"""
Risk management system for position sizing, stop losses, and portfolio risk.
Ensures aggressive trading stays within acceptable risk parameters.
"""
from typing import Dict, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from src.config import settings
from src.database.models import Position, TradingSession, PositionStatus

logger = logging.getLogger(__name__)


class RiskManager:
    """
    Manages all risk-related decisions and calculations.
    Prevents over-leverage, excessive losses, and poor position sizing.
    """

    def __init__(self, session: Session):
        """
        Initialize risk manager.

        Args:
            session: Database session (dependency injection)
        """
        self.session = session

    def calculate_position_size(
        self,
        symbol: str,
        current_price: Decimal,
        account_equity: Decimal,
        signal_strength: float = 1.0,
        use_leverage: bool = False,
    ) -> Tuple[Decimal, float]:
        """
        Calculate position size based on risk parameters and signal strength.

        Args:
            symbol: Stock symbol
            current_price: Current market price
            account_equity: Total account equity
            signal_strength: Signal confidence (0.0 to 1.0)
            use_leverage: Whether to apply leverage

        Returns:
            Tuple of (quantity, leverage_used)
        """
        try:
            # Base position size as percentage of equity
            base_size = account_equity * Decimal(str(settings.max_position_size_pct))

            # Adjust for signal strength
            adjusted_size = base_size * Decimal(str(signal_strength))

            # Apply leverage if conditions are met
            leverage = 1.0
            if use_leverage and self._can_use_leverage(account_equity):
                leverage = min(settings.max_leverage, 1.0 + signal_strength * (settings.max_leverage - 1.0))
                adjusted_size *= Decimal(str(leverage))

            # Calculate quantity
            quantity = adjusted_size / current_price

            # Round down to avoid exceeding buying power
            quantity = quantity.quantize(Decimal("0.01"))

            logger.info(
                f"Position sizing for {symbol}: "
                f"price=${current_price}, "
                f"equity=${account_equity}, "
                f"signal={signal_strength:.2f}, "
                f"leverage={leverage:.2f}x, "
                f"qty={quantity}"
            )

            return quantity, leverage

        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            raise

    def calculate_stop_loss(
        self,
        entry_price: Decimal,
        side: str,
        volatility: Optional[float] = None,
    ) -> Decimal:
        """
        Calculate stop loss price based on entry price and volatility.

        Args:
            entry_price: Entry price
            side: 'buy' or 'sell'
            volatility: Optional volatility adjustment (0.0 to 1.0)

        Returns:
            Stop loss price
        """
        # Base stop loss percentage
        stop_pct = Decimal(str(settings.stop_loss_pct))

        # Adjust for volatility if provided
        if volatility:
            # Higher volatility = wider stop
            stop_pct *= Decimal(str(1.0 + volatility * 0.5))

        if side.lower() == "buy":
            # Long position: stop below entry
            stop_price = entry_price * (Decimal("1.0") - stop_pct)
        else:
            # Short position: stop above entry
            stop_price = entry_price * (Decimal("1.0") + stop_pct)

        return stop_price.quantize(Decimal("0.01"))

    def calculate_take_profit(
        self,
        entry_price: Decimal,
        side: str,
        risk_reward_ratio: float = 2.0,
    ) -> Decimal:
        """
        Calculate take profit price based on entry and risk/reward ratio.

        Args:
            entry_price: Entry price
            side: 'buy' or 'sell'
            risk_reward_ratio: Target risk/reward ratio

        Returns:
            Take profit price
        """
        # Base take profit percentage
        take_profit_pct = Decimal(str(settings.take_profit_pct))

        # Adjust for risk/reward ratio
        take_profit_pct *= Decimal(str(risk_reward_ratio))

        if side.lower() == "buy":
            # Long position: take profit above entry
            tp_price = entry_price * (Decimal("1.0") + take_profit_pct)
        else:
            # Short position: take profit below entry
            tp_price = entry_price * (Decimal("1.0") - take_profit_pct)

        return tp_price.quantize(Decimal("0.01"))

    def should_close_position(
        self,
        position: Position,
        current_price: Decimal,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if position should be closed based on risk rules.

        Args:
            position: Position object
            current_price: Current market price

        Returns:
            Tuple of (should_close, reason)
        """
        # Check stop loss
        if position.stop_loss_price:
            if position.side.value == "buy" and current_price <= position.stop_loss_price:
                return True, "stop_loss_hit"
            elif position.side.value == "sell" and current_price >= position.stop_loss_price:
                return True, "stop_loss_hit"

        # Check take profit
        if position.take_profit_price:
            if position.side.value == "buy" and current_price >= position.take_profit_price:
                return True, "take_profit_hit"
            elif position.side.value == "sell" and current_price <= position.take_profit_price:
                return True, "take_profit_hit"

        # Check trailing stop
        if position.trailing_stop_pct:
            should_close, reason = self._check_trailing_stop(position, current_price)
            if should_close:
                return True, reason

        # Check max hold time
        if position.entry_time:
            hold_hours = (datetime.utcnow() - position.entry_time).total_seconds() / 3600
            if hold_hours >= settings.max_position_hold_hours:
                return True, "max_hold_time_exceeded"

        return False, None

    def _check_trailing_stop(
        self,
        position: Position,
        current_price: Decimal,
    ) -> Tuple[bool, Optional[str]]:
        """Check if trailing stop should trigger."""
        if not position.trailing_stop_pct:
            return False, None

        trailing_pct = Decimal(str(position.trailing_stop_pct))

        if position.side.value == "buy":
            # Long position: track highest price
            if position.highest_price is None or current_price > position.highest_price:
                # Update highest price
                position.highest_price = current_price
                self.session.commit()

            # Check if price dropped enough from highest
            if position.highest_price:
                stop_price = position.highest_price * (Decimal("1.0") - trailing_pct)
                if current_price <= stop_price:
                    return True, "trailing_stop_hit"

        else:
            # Short position: track lowest price
            if position.lowest_price is None or current_price < position.lowest_price:
                # Update lowest price
                position.lowest_price = current_price
                self.session.commit()

            # Check if price rose enough from lowest
            if position.lowest_price:
                stop_price = position.lowest_price * (Decimal("1.0") + trailing_pct)
                if current_price >= stop_price:
                    return True, "trailing_stop_hit"

        return False, None

    def can_open_new_position(
        self,
        account_equity: Decimal,
        current_session: Optional[TradingSession] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if bot can open a new position based on risk limits.

        Args:
            account_equity: Current account equity
            current_session: Current trading session

        Returns:
            Tuple of (can_open, reason_if_not)
        """
        # Check max concurrent positions
        open_positions = self.session.query(Position).filter(
            Position.status == PositionStatus.OPEN
        ).count()

        if open_positions >= settings.max_concurrent_positions:
            return False, "max_concurrent_positions_reached"

        # Check daily loss limit
        if current_session:
            if current_session.pnl_pct and current_session.pnl_pct <= settings.max_daily_loss:
                return False, "daily_loss_limit_reached"

            # Check if daily profit target already hit
            if current_session.pnl_pct and current_session.pnl_pct >= settings.daily_profit_target:
                logger.info("Daily profit target reached - could stop trading or continue conservatively")
                # Still allow trading but could implement conservative mode here

        return True, None

    def _can_use_leverage(self, account_equity: Decimal) -> bool:
        """
        Determine if leverage should be used based on account health.

        Args:
            account_equity: Current account equity

        Returns:
            True if leverage can be used
        """
        # Check if account has enough equity for leveraged trading
        min_equity_for_leverage = Decimal("10000.0")  # $10k minimum

        if account_equity < min_equity_for_leverage:
            return False

        # Check current session performance
        current_session = self.session.query(TradingSession).filter(
            TradingSession.is_active == True
        ).first()

        if current_session:
            # Don't use leverage if session is losing
            if current_session.pnl_pct and current_session.pnl_pct < 0:
                return False

            # Don't use leverage if too many losing trades
            if current_session.total_trades > 0:
                win_rate = current_session.winning_trades / current_session.total_trades
                if win_rate < 0.5:
                    return False

        return True

    def calculate_portfolio_risk(self) -> Dict:
        """
        Calculate overall portfolio risk metrics.

        Returns:
            Dictionary with risk metrics
        """
        try:
            open_positions = self.session.query(Position).filter(
                Position.status == PositionStatus.OPEN
            ).all()

            total_exposure = sum(
                float(pos.quantity * pos.entry_price * pos.leverage)
                for pos in open_positions
            )

            total_risk = sum(
                float(abs(pos.entry_price - pos.stop_loss_price) * pos.quantity)
                for pos in open_positions
                if pos.stop_loss_price
            )

            return {
                "open_positions": len(open_positions),
                "total_exposure": total_exposure,
                "total_risk": total_risk,
                "avg_leverage": sum(pos.leverage for pos in open_positions) / len(open_positions)
                if open_positions else 0,
            }

        except Exception as e:
            logger.error(f"Error calculating portfolio risk: {e}")
            return {}

    def validate_trade_parameters(
        self,
        symbol: str,
        quantity: Decimal,
        price: Decimal,
        side: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate trade parameters before execution.

        Args:
            symbol: Stock symbol
            quantity: Order quantity
            price: Order price
            side: Order side

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check quantity is positive
        if quantity <= 0:
            return False, "Quantity must be positive"

        # Check price is positive
        if price <= 0:
            return False, "Price must be positive"

        # Check side is valid
        if side.lower() not in ["buy", "sell"]:
            return False, "Side must be 'buy' or 'sell'"

        # Check symbol is in universe
        if symbol not in settings.symbol_universe:
            logger.warning(f"Symbol {symbol} not in configured universe")

        # Check minimum position value
        min_position_value = Decimal("100.0")  # $100 minimum
        position_value = quantity * price
        if position_value < min_position_value:
            return False, f"Position value too small: ${position_value} < ${min_position_value}"

        return True, None
