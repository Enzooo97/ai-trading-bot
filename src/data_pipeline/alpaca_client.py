"""
Alpaca API client for trading and market data.
Handles connection, authentication, and provides clean interface for data access.
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import logging
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.live import StockDataStream
from alpaca.data.requests import (
    StockBarsRequest,
    StockLatestBarRequest,
    StockLatestQuoteRequest,
    StockSnapshotRequest
)
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.trading.requests import (
    MarketOrderRequest,
    LimitOrderRequest,
    StopLossRequest,
    TakeProfitRequest,
    GetOrdersRequest
)
from alpaca.trading.enums import OrderSide as AlpacaOrderSide, TimeInForce, OrderClass
from src.config import settings
import pandas as pd

logger = logging.getLogger(__name__)


class AlpacaClient:
    """
    Alpaca API client wrapper.
    Provides unified interface for trading and market data operations.
    """

    def __init__(self):
        """Initialize Alpaca clients."""
        self.trading_client = TradingClient(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_secret_key,
            paper=settings.alpaca_base_url.startswith("https://paper"),
        )

        self.data_client = StockHistoricalDataClient(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_secret_key,
        )

        self.stream_client = None  # Initialize when needed
        logger.info("Alpaca clients initialized successfully")

    def get_account(self) -> Dict:
        """
        Get account information.

        Returns:
            Dict containing account details (equity, buying_power, etc.)
        """
        try:
            account = self.trading_client.get_account()
            return {
                "equity": Decimal(str(account.equity)),
                "cash": Decimal(str(account.cash)),
                "buying_power": Decimal(str(account.buying_power)),
                "portfolio_value": Decimal(str(account.portfolio_value)),
                "long_market_value": Decimal(str(account.long_market_value)),
                "short_market_value": Decimal(str(account.short_market_value)),
                "daytrading_buying_power": Decimal(str(account.daytrading_buying_power)),
                "multiplier": Decimal(str(account.multiplier)),
                "pattern_day_trader": account.pattern_day_trader,
                "trading_blocked": account.trading_blocked,
                "transfers_blocked": account.transfers_blocked,
                "account_blocked": account.account_blocked,
            }
        except Exception as e:
            logger.error(f"Error fetching account info: {e}")
            raise

    def get_positions(self) -> List[Dict]:
        """
        Get all open positions.

        Returns:
            List of position dictionaries
        """
        try:
            positions = self.trading_client.get_all_positions()
            return [
                {
                    "symbol": pos.symbol,
                    "quantity": Decimal(str(pos.qty)),
                    "market_value": Decimal(str(pos.market_value)),
                    "avg_entry_price": Decimal(str(pos.avg_entry_price)),
                    "current_price": Decimal(str(pos.current_price)),
                    "unrealized_pl": Decimal(str(pos.unrealized_pl)),
                    "unrealized_plpc": Decimal(str(pos.unrealized_plpc)),
                    "side": pos.side,
                }
                for pos in positions
            ]
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            raise

    def get_position(self, symbol: str) -> Optional[Dict]:
        """
        Get specific position.

        Args:
            symbol: Stock symbol

        Returns:
            Position dictionary or None if not found
        """
        try:
            pos = self.trading_client.get_open_position(symbol)
            return {
                "symbol": pos.symbol,
                "quantity": Decimal(str(pos.qty)),
                "market_value": Decimal(str(pos.market_value)),
                "avg_entry_price": Decimal(str(pos.avg_entry_price)),
                "current_price": Decimal(str(pos.current_price)),
                "unrealized_pl": Decimal(str(pos.unrealized_pl)),
                "unrealized_plpc": Decimal(str(pos.unrealized_plpc)),
                "side": pos.side,
            }
        except Exception as e:
            logger.debug(f"No position found for {symbol}: {e}")
            return None

    def get_bars(
        self,
        symbols: List[str],
        timeframe: str = "1Min",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, pd.DataFrame]:
        """
        Get historical bars for symbols.

        Args:
            symbols: List of symbols
            timeframe: Bar timeframe (1Min, 5Min, 15Min, 1Hour, 1Day)
            start: Start datetime
            end: End datetime
            limit: Maximum number of bars

        Returns:
            Dictionary mapping symbols to DataFrames with OHLCV data
        """
        try:
            # Parse timeframe
            tf_map = {
                "1Min": TimeFrame(1, TimeFrameUnit.Minute),
                "5Min": TimeFrame(5, TimeFrameUnit.Minute),
                "15Min": TimeFrame(15, TimeFrameUnit.Minute),
                "30Min": TimeFrame(30, TimeFrameUnit.Minute),
                "1Hour": TimeFrame(1, TimeFrameUnit.Hour),
                "1Day": TimeFrame(1, TimeFrameUnit.Day),
            }
            tf = tf_map.get(timeframe, TimeFrame(1, TimeFrameUnit.Minute))

            # Default to last 100 bars if no time range specified
            if not start and not end and not limit:
                limit = 100
                end = datetime.now()

            request = StockBarsRequest(
                symbol_or_symbols=symbols,
                timeframe=tf,
                start=start,
                end=end,
                limit=limit,
            )

            bars = self.data_client.get_stock_bars(request)

            # Convert to DataFrames
            result = {}
            for symbol in symbols:
                if symbol in bars.data:
                    df = pd.DataFrame([
                        {
                            "timestamp": bar.timestamp,
                            "open": float(bar.open),
                            "high": float(bar.high),
                            "low": float(bar.low),
                            "close": float(bar.close),
                            "volume": int(bar.volume),
                            "vwap": float(bar.vwap) if hasattr(bar, 'vwap') and bar.vwap else None,
                            "trade_count": bar.trade_count if hasattr(bar, 'trade_count') else None,
                        }
                        for bar in bars.data[symbol]
                    ])
                    df.set_index("timestamp", inplace=True)
                    result[symbol] = df
                else:
                    logger.warning(f"No bars returned for {symbol}")
                    result[symbol] = pd.DataFrame()

            return result

        except Exception as e:
            logger.error(f"Error fetching bars: {e}")
            raise

    def get_latest_bar(self, symbol: str) -> Optional[Dict]:
        """
        Get latest bar for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Dictionary with OHLCV data
        """
        try:
            request = StockLatestBarRequest(symbol_or_symbols=symbol)
            bars = self.data_client.get_stock_latest_bar(request)

            if symbol in bars:
                bar = bars[symbol]
                return {
                    "symbol": symbol,
                    "timestamp": bar.timestamp,
                    "open": Decimal(str(bar.open)),
                    "high": Decimal(str(bar.high)),
                    "low": Decimal(str(bar.low)),
                    "close": Decimal(str(bar.close)),
                    "volume": int(bar.volume),
                    "vwap": Decimal(str(bar.vwap)) if hasattr(bar, 'vwap') and bar.vwap else None,
                }
            return None

        except Exception as e:
            logger.error(f"Error fetching latest bar for {symbol}: {e}")
            raise

    def get_latest_quote(self, symbol: str) -> Optional[Dict]:
        """
        Get latest quote (bid/ask) for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Dictionary with bid/ask data
        """
        try:
            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quotes = self.data_client.get_stock_latest_quote(request)

            if symbol in quotes:
                quote = quotes[symbol]
                return {
                    "symbol": symbol,
                    "timestamp": quote.timestamp,
                    "bid_price": Decimal(str(quote.bid_price)),
                    "bid_size": int(quote.bid_size),
                    "ask_price": Decimal(str(quote.ask_price)),
                    "ask_size": int(quote.ask_size),
                }
            return None

        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")
            raise

    def get_snapshot(self, symbol: str) -> Optional[Dict]:
        """
        Get market snapshot (latest bar + quote).

        Args:
            symbol: Stock symbol

        Returns:
            Dictionary with comprehensive market data
        """
        try:
            request = StockSnapshotRequest(symbol_or_symbols=symbol)
            snapshots = self.data_client.get_stock_snapshot(request)

            if symbol in snapshots:
                snap = snapshots[symbol]
                return {
                    "symbol": symbol,
                    "latest_bar": {
                        "timestamp": snap.latest_trade.timestamp if snap.latest_trade else None,
                        "price": Decimal(str(snap.latest_trade.price)) if snap.latest_trade else None,
                    },
                    "latest_quote": {
                        "timestamp": snap.latest_quote.timestamp if snap.latest_quote else None,
                        "bid_price": Decimal(str(snap.latest_quote.bid_price)) if snap.latest_quote else None,
                        "ask_price": Decimal(str(snap.latest_quote.ask_price)) if snap.latest_quote else None,
                    },
                    "prev_daily_bar": {
                        "close": Decimal(str(snap.previous_daily_bar.close)) if snap.previous_daily_bar else None,
                    },
                }
            return None

        except Exception as e:
            logger.error(f"Error fetching snapshot for {symbol}: {e}")
            raise

    def submit_market_order(
        self,
        symbol: str,
        qty: Decimal,
        side: str,
        time_in_force: str = "day",
    ) -> Dict:
        """
        Submit a market order.

        Args:
            symbol: Stock symbol
            qty: Quantity to trade
            side: 'buy' or 'sell'
            time_in_force: Order duration ('day', 'gtc', 'ioc', 'fok')

        Returns:
            Order dictionary
        """
        try:
            side_enum = AlpacaOrderSide.BUY if side.lower() == "buy" else AlpacaOrderSide.SELL
            tif_map = {
                "day": TimeInForce.DAY,
                "gtc": TimeInForce.GTC,
                "ioc": TimeInForce.IOC,
                "fok": TimeInForce.FOK,
            }

            request = MarketOrderRequest(
                symbol=symbol,
                qty=float(qty),
                side=side_enum,
                time_in_force=tif_map.get(time_in_force.lower(), TimeInForce.DAY),
            )

            order = self.trading_client.submit_order(request)
            logger.info(f"Market order submitted: {side} {qty} {symbol}")

            return self._format_order(order)

        except Exception as e:
            logger.error(f"Error submitting market order: {e}")
            raise

    def submit_bracket_order(
        self,
        symbol: str,
        qty: Decimal,
        side: str,
        stop_loss_price: Optional[Decimal] = None,
        take_profit_price: Optional[Decimal] = None,
    ) -> Dict:
        """
        Submit a bracket order with stop loss and take profit.

        Args:
            symbol: Stock symbol
            qty: Quantity to trade
            side: 'buy' or 'sell'
            stop_loss_price: Stop loss price
            take_profit_price: Take profit price

        Returns:
            Order dictionary
        """
        try:
            side_enum = AlpacaOrderSide.BUY if side.lower() == "buy" else AlpacaOrderSide.SELL

            # Build order legs
            order_data = {
                "symbol": symbol,
                "qty": float(qty),
                "side": side_enum,
                "time_in_force": TimeInForce.DAY,
                "order_class": OrderClass.BRACKET,
            }

            if stop_loss_price:
                order_data["stop_loss"] = StopLossRequest(stop_price=float(stop_loss_price))

            if take_profit_price:
                order_data["take_profit"] = TakeProfitRequest(limit_price=float(take_profit_price))

            request = MarketOrderRequest(**order_data)
            order = self.trading_client.submit_order(request)
            logger.info(f"Bracket order submitted: {side} {qty} {symbol}")

            return self._format_order(order)

        except Exception as e:
            logger.error(f"Error submitting bracket order: {e}")
            raise

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.

        Args:
            order_id: Alpaca order ID

        Returns:
            True if successful
        """
        try:
            self.trading_client.cancel_order_by_id(order_id)
            logger.info(f"Order cancelled: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False

    def close_position(self, symbol: str) -> bool:
        """
        Close a position completely.

        Args:
            symbol: Stock symbol

        Returns:
            True if successful
        """
        try:
            self.trading_client.close_position(symbol)
            logger.info(f"Position closed: {symbol}")
            return True
        except Exception as e:
            logger.error(f"Error closing position {symbol}: {e}")
            return False

    def close_all_positions(self) -> bool:
        """
        Close all open positions.

        Returns:
            True if successful
        """
        try:
            self.trading_client.close_all_positions(cancel_orders=True)
            logger.info("All positions closed")
            return True
        except Exception as e:
            logger.error(f"Error closing all positions: {e}")
            return False

    def _format_order(self, order) -> Dict:
        """Format Alpaca order object to dictionary."""
        return {
            "id": order.id,
            "symbol": order.symbol,
            "qty": Decimal(str(order.qty)),
            "filled_qty": Decimal(str(order.filled_qty)),
            "side": order.side.value,
            "type": order.type.value,
            "status": order.status.value,
            "limit_price": Decimal(str(order.limit_price)) if order.limit_price else None,
            "stop_price": Decimal(str(order.stop_price)) if order.stop_price else None,
            "filled_avg_price": Decimal(str(order.filled_avg_price)) if order.filled_avg_price else None,
            "submitted_at": order.submitted_at,
            "filled_at": order.filled_at,
        }


# Global client instance
alpaca_client = AlpacaClient()
