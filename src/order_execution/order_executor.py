"""
Order execution system with smart routing and risk management.
Handles order placement, tracking, and position management.
"""
from typing import Dict, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from src.config import settings
from src.data_pipeline import alpaca_client
from src.database.models import (
    Order, Position, TradingSession,
    OrderSide, OrderType, OrderStatus, PositionStatus
)
from src.risk_management import RiskManager
from src.strategies.base_strategy import Signal

logger = logging.getLogger(__name__)


class OrderExecutor:
    """
    Manages order execution with intelligent routing and tracking.
    Ensures orders comply with risk management rules.
    """

    def __init__(self, session: Session):
        """
        Initialize order executor.

        Args:
            session: Database session (dependency injection)
        """
        self.session = session
        self.risk_manager = RiskManager(session)
        self.alpaca = alpaca_client

    def execute_signal(
        self,
        symbol: str,
        signal: Signal,
        account_info: Dict,
        current_session: TradingSession,
        use_leverage: bool = False,
    ) -> Optional[Position]:
        """
        Execute trading signal with full risk management.

        Args:
            symbol: Stock symbol
            signal: Trading signal
            account_info: Account information
            current_session: Current trading session
            use_leverage: Whether to use leverage

        Returns:
            Position object if successful, None otherwise
        """
        try:
            # Validate signal
            if signal.action not in ["buy", "sell"]:
                logger.info(f"Skipping non-entry signal: {signal.action}")
                return None

            # Check if can open new position
            can_open, reason = self.risk_manager.can_open_new_position(
                account_equity=account_info['equity'],
                current_session=current_session,
            )

            if not can_open:
                logger.warning(f"Cannot open position for {symbol}: {reason}")
                return None

            # Get current price
            latest_bar = self.alpaca.get_latest_bar(symbol)
            if not latest_bar:
                logger.error(f"Failed to get price for {symbol}")
                return None

            current_price = latest_bar['close']

            # Calculate position size
            quantity, leverage = self.risk_manager.calculate_position_size(
                symbol=symbol,
                current_price=current_price,
                account_equity=account_info['equity'],
                signal_strength=signal.strength,
                use_leverage=use_leverage,
            )

            if quantity <= 0:
                logger.warning(f"Invalid quantity calculated: {quantity}")
                return None

            # Validate trade parameters
            is_valid, error = self.risk_manager.validate_trade_parameters(
                symbol=symbol,
                quantity=quantity,
                price=current_price,
                side=signal.action,
            )

            if not is_valid:
                logger.error(f"Invalid trade parameters: {error}")
                return None

            # Calculate risk management prices
            stop_loss = self.risk_manager.calculate_stop_loss(
                entry_price=current_price,
                side=signal.action,
            )

            take_profit = self.risk_manager.calculate_take_profit(
                entry_price=current_price,
                side=signal.action,
                risk_reward_ratio=2.0,
            )

            # Submit bracket order (entry + stop loss + take profit)
            order_result = self.alpaca.submit_bracket_order(
                symbol=symbol,
                qty=quantity,
                side=signal.action,
                stop_loss_price=stop_loss,
                take_profit_price=take_profit,
            )

            # Create position record
            position = Position(
                session_id=current_session.id,
                symbol=symbol,
                side=OrderSide.BUY if signal.action == "buy" else OrderSide.SELL,
                status=PositionStatus.OPEN,
                entry_price=current_price,
                entry_time=datetime.utcnow(),
                quantity=quantity,
                leverage=leverage,
                entry_order_id=order_result['id'],
                stop_loss_price=stop_loss,
                take_profit_price=take_profit,
                trailing_stop_pct=settings.trailing_stop_pct,
                strategy_name=signal.metadata.get('strategy_name', 'Unknown'),
                entry_reason=signal.reason,
            )

            self.session.add(position)

            # Create order record
            order = Order(
                session_id=current_session.id,
                alpaca_order_id=order_result['id'],
                symbol=symbol,
                side=OrderSide.BUY if signal.action == "buy" else OrderSide.SELL,
                order_type=OrderType.MARKET,
                status=OrderStatus.SUBMITTED,
                quantity=quantity,
                submitted_at=datetime.utcnow(),
                reason=signal.reason,
            )

            self.session.add(order)
            self.session.commit()

            logger.info(
                f"Order executed: {signal.action.upper()} {quantity} {symbol} @ ${current_price} "
                f"(leverage: {leverage:.2f}x, SL: ${stop_loss}, TP: ${take_profit})"
            )

            return position

        except Exception as e:
            logger.error(f"Error executing signal for {symbol}: {e}")
            self.session.rollback()
            return None

    def close_position(
        self,
        position: Position,
        reason: str,
        current_session: TradingSession,
    ) -> bool:
        """
        Close an open position.

        Args:
            position: Position to close
            reason: Reason for closing
            current_session: Current trading session

        Returns:
            True if successful
        """
        try:
            # Close position via Alpaca
            success = self.alpaca.close_position(position.symbol)

            if not success:
                logger.error(f"Failed to close position {position.symbol}")
                return False

            # Get fill price
            latest_bar = self.alpaca.get_latest_bar(position.symbol)
            exit_price = latest_bar['close'] if latest_bar else position.entry_price

            # Calculate P&L
            if position.side == OrderSide.BUY:
                pnl = (exit_price - position.entry_price) * position.quantity
                pnl_pct = float((exit_price - position.entry_price) / position.entry_price)
            else:
                pnl = (position.entry_price - exit_price) * position.quantity
                pnl_pct = float((position.entry_price - exit_price) / position.entry_price)

            # Update position
            position.status = PositionStatus.CLOSED
            position.exit_price = exit_price
            position.exit_time = datetime.utcnow()
            position.exit_reason = reason
            position.pnl = pnl
            position.pnl_pct = pnl_pct

            # Create exit order record
            exit_order = Order(
                session_id=current_session.id,
                position_id=position.id,
                symbol=position.symbol,
                side=OrderSide.SELL if position.side == OrderSide.BUY else OrderSide.BUY,
                order_type=OrderType.MARKET,
                status=OrderStatus.FILLED,
                quantity=position.quantity,
                filled_quantity=position.quantity,
                filled_avg_price=exit_price,
                submitted_at=datetime.utcnow(),
                filled_at=datetime.utcnow(),
                reason=reason,
            )

            self.session.add(exit_order)

            # Update session stats
            self._update_session_stats(current_session, position)

            self.session.commit()

            logger.info(
                f"Position closed: {position.symbol} @ ${exit_price} "
                f"(P&L: ${pnl:.2f}, {pnl_pct*100:.2f}%) - {reason}"
            )

            return True

        except Exception as e:
            logger.error(f"Error closing position {position.symbol}: {e}")
            self.session.rollback()
            return False

    def update_positions(self, current_session: TradingSession):
        """
        Update all open positions and check exit conditions.

        Args:
            current_session: Current trading session
        """
        try:
            # Get all open positions
            open_positions = self.session.query(Position).filter(
                Position.status == PositionStatus.OPEN,
                Position.session_id == current_session.id,
            ).all()

            for position in open_positions:
                try:
                    # Get current price
                    latest_bar = self.alpaca.get_latest_bar(position.symbol)
                    if not latest_bar:
                        logger.warning(f"Could not get price for {position.symbol}")
                        continue

                    current_price = latest_bar['close']

                    # Check if position should be closed
                    should_close, reason = self.risk_manager.should_close_position(
                        position=position,
                        current_price=current_price,
                    )

                    if should_close:
                        logger.info(f"Closing {position.symbol}: {reason}")
                        self.close_position(position, reason, current_session)

                except Exception as e:
                    logger.error(f"Error updating position {position.symbol}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error updating positions: {e}")

    def cancel_stale_orders(self, max_age_minutes: int = 30):
        """
        Cancel orders that have been pending too long.

        Args:
            max_age_minutes: Maximum age for pending orders
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)

            stale_orders = self.session.query(Order).filter(
                Order.status.in_([OrderStatus.PENDING, OrderStatus.SUBMITTED]),
                Order.created_at < cutoff_time,
            ).all()

            for order in stale_orders:
                if order.alpaca_order_id:
                    self.alpaca.cancel_order(order.alpaca_order_id)

                order.status = OrderStatus.CANCELLED
                order.cancelled_at = datetime.utcnow()
                order.error_message = "Cancelled due to age"

            if stale_orders:
                self.session.commit()
                logger.info(f"Cancelled {len(stale_orders)} stale orders")

        except Exception as e:
            logger.error(f"Error cancelling stale orders: {e}")
            self.session.rollback()

    def _update_session_stats(self, session: TradingSession, position: Position):
        """Update trading session statistics."""
        session.total_trades += 1

        if position.pnl > 0:
            session.winning_trades += 1
        elif position.pnl < 0:
            session.losing_trades += 1

        # Update session P&L
        if session.pnl is None:
            session.pnl = position.pnl
        else:
            session.pnl += position.pnl

        # Calculate P&L percentage
        if session.starting_equity:
            session.pnl_pct = float(session.pnl / session.starting_equity)

    def get_order_status(self, order_id: str) -> Optional[Dict]:
        """
        Get order status from Alpaca.

        Args:
            order_id: Alpaca order ID

        Returns:
            Order status dictionary
        """
        try:
            # In production, query Alpaca API for order status
            # For now, return basic info
            order = self.session.query(Order).filter(
                Order.alpaca_order_id == order_id
            ).first()

            if order:
                return {
                    "id": order.alpaca_order_id,
                    "symbol": order.symbol,
                    "status": order.status.value,
                    "filled_qty": float(order.filled_quantity) if order.filled_quantity else 0,
                }

            return None

        except Exception as e:
            logger.error(f"Error getting order status: {e}")
            return None
