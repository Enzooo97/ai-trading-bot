"""
Base strategy class that all trading strategies inherit from.
Provides common interface and utility methods.
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple, List
from decimal import Decimal
from datetime import datetime
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class Signal:
    """Trading signal with strength and metadata."""

    def __init__(
        self,
        action: str,  # 'buy', 'sell', 'hold', 'close'
        strength: float,  # 0.0 to 1.0
        reason: str,
        metadata: Optional[Dict] = None,
    ):
        """
        Initialize trading signal.

        Args:
            action: Trading action to take
            strength: Signal confidence (0.0 = weak, 1.0 = strong)
            reason: Human-readable reason for signal
            metadata: Additional context data
        """
        self.action = action.lower()
        self.strength = max(0.0, min(1.0, strength))  # Clamp to 0-1
        self.reason = reason
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()

    def __repr__(self):
        return f"Signal(action={self.action}, strength={self.strength:.2f}, reason={self.reason})"


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    Implements common functionality and defines required interface.
    """

    def __init__(self, name: str):
        """
        Initialize strategy.

        Args:
            name: Strategy name
        """
        self.name = name
        self.logger = logging.getLogger(f"strategy.{name}")

    @abstractmethod
    def analyze(
        self,
        symbol: str,
        data: pd.DataFrame,
        account_info: Dict,
        current_positions: List[Dict],
    ) -> Signal:
        """
        Analyze market data and generate trading signal.

        Args:
            symbol: Stock symbol
            data: Historical OHLCV data with indicators
            account_info: Current account information
            current_positions: List of current open positions

        Returns:
            Signal object with action and strength
        """
        pass

    @abstractmethod
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators for strategy.

        Args:
            data: OHLCV DataFrame

        Returns:
            DataFrame with added indicator columns
        """
        pass

    def get_required_bars(self) -> int:
        """
        Get minimum number of historical bars needed.

        Returns:
            Number of bars required
        """
        return 100  # Default to 100 bars

    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate that data is sufficient for analysis.

        Args:
            data: OHLCV DataFrame

        Returns:
            True if data is valid
        """
        if data is None or data.empty:
            self.logger.warning("Data is empty")
            return False

        if len(data) < self.get_required_bars():
            self.logger.warning(
                f"Insufficient data: {len(data)} bars, need {self.get_required_bars()}"
            )
            return False

        required_columns = ["open", "high", "low", "close", "volume"]
        missing = [col for col in required_columns if col not in data.columns]
        if missing:
            self.logger.error(f"Missing required columns: {missing}")
            return False

        return True

    def calculate_volatility(self, data: pd.DataFrame, period: int = 20) -> float:
        """
        Calculate price volatility (standard deviation of returns).

        Args:
            data: OHLCV DataFrame
            period: Lookback period

        Returns:
            Volatility as decimal (e.g., 0.02 = 2%)
        """
        if len(data) < period:
            return 0.02  # Default 2% volatility

        returns = data['close'].pct_change().dropna()
        return float(returns.tail(period).std())

    def is_trending(
        self,
        data: pd.DataFrame,
        threshold: float = 0.6,
    ) -> Tuple[bool, str]:
        """
        Determine if market is trending or ranging.

        Args:
            data: OHLCV DataFrame with indicators
            threshold: ADX threshold for trending market

        Returns:
            Tuple of (is_trending, direction)
        """
        # Use ADX if available
        if 'adx' in data.columns:
            adx = data['adx'].iloc[-1]
            if adx > threshold * 100:  # ADX typically 0-100
                # Check trend direction using +DI and -DI
                if 'plus_di' in data.columns and 'minus_di' in data.columns:
                    if data['plus_di'].iloc[-1] > data['minus_di'].iloc[-1]:
                        return True, 'up'
                    else:
                        return True, 'down'
                return True, 'unknown'

        # Fallback: use moving average slope
        if 'sma_20' in data.columns:
            ma = data['sma_20'].tail(10)
            slope = (ma.iloc[-1] - ma.iloc[0]) / ma.iloc[0]
            if abs(slope) > 0.01:  # 1% change
                direction = 'up' if slope > 0 else 'down'
                return True, direction

        return False, 'ranging'

    def calculate_volume_profile(self, data: pd.DataFrame) -> Dict:
        """
        Calculate volume metrics.

        Args:
            data: OHLCV DataFrame

        Returns:
            Dictionary with volume metrics
        """
        if len(data) < 20:
            return {"avg_volume": 0, "volume_ratio": 1.0}

        avg_volume = data['volume'].tail(20).mean()
        current_volume = data['volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

        return {
            "avg_volume": float(avg_volume),
            "current_volume": float(current_volume),
            "volume_ratio": float(volume_ratio),
            "is_high_volume": volume_ratio > 1.5,
        }

    def __repr__(self):
        return f"Strategy({self.name})"
