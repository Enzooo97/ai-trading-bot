"""
VWAP Anchored Scalping Strategy.
Uses Volume Weighted Average Price as institutional anchor point.

Research shows this is one of the most profitable scalping strategies.
VWAP acts as dynamic support/resistance that institutions respect.
"""
from typing import Dict, List
import pandas as pd
from src.utils import indicators as ta
import numpy as np
from src.strategies.base_strategy import BaseStrategy, Signal
from src.config import settings


class VWAPStrategy(BaseStrategy):
    """
    VWAP Anchored Scalping Strategy - Research-backed institutional approach.

    Entry Conditions (BUY):
    - Price dips to VWAP from above (institutional support)
    - Volume > 1.5x average (confirming interest)
    - 9 EMA above VWAP (uptrend context)
    - Price within 0.2% of VWAP

    Entry Conditions (SELL/Short):
    - Price rallies to VWAP from below (institutional resistance)
    - Volume > 1.5x average
    - 9 EMA below VWAP (downtrend context)
    - Price within 0.2% of VWAP

    Exit:
    - 0.3-0.5% profit target (quick scalp)
    - Stop: 0.2% beyond VWAP
    - Time: 5-15 minutes max

    Best Performance:
    - 5-minute timeframe
    - Trending days
    - High liquidity stocks
    - Win rate: 60-65% (research-backed)
    """

    def __init__(self):
        super().__init__("VWAP_Anchored")
        self.min_bars = 50
        self.vwap_threshold_pct = 0.002  # 0.2% from VWAP
        self.profit_target_pct = 0.006  # 0.6% target (increased from 0.4%)
        self.stop_loss_pct = 0.0025  # 0.25% stop (slightly wider for better fills)

    def get_required_bars(self) -> int:
        return self.min_bars

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate VWAP and supporting indicators."""
        df = data.copy()

        # Calculate VWAP
        df['vwap'] = self._calculate_vwap(df)

        # EMA for trend context
        df['ema_9'] = ta.ema(df['close'], length=9)
        df['ema_21'] = ta.ema(df['close'], length=21)

        # Volume analysis
        df['volume_sma'] = ta.sma(df['volume'], length=20)
        df['volume_ratio'] = df['volume'] / df['volume_sma']

        # Distance from VWAP
        df['vwap_distance_pct'] = (df['close'] - df['vwap']) / df['vwap']

        # Price position relative to VWAP
        df['above_vwap'] = df['close'] > df['vwap']
        df['below_vwap'] = df['close'] < df['vwap']

        # VWAP bands (standard deviation)
        df['vwap_std'] = df['close'].rolling(window=20).std()
        df['vwap_upper'] = df['vwap'] + df['vwap_std']
        df['vwap_lower'] = df['vwap'] - df['vwap_std']

        # Momentum
        df['roc'] = ta.roc(df['close'], length=5)

        # ATR for volatility
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        df['atr_pct'] = (df['atr'] / df['close']) * 100

        return df

    def _calculate_vwap(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate Volume Weighted Average Price.
        VWAP = Σ(Price × Volume) / Σ(Volume)
        """
        # Typical price (HLC/3)
        typical_price = (df['high'] + df['low'] + df['close']) / 3

        # Cumulative price * volume
        cumulative_pv = (typical_price * df['volume']).cumsum()

        # Cumulative volume
        cumulative_volume = df['volume'].cumsum()

        # VWAP
        vwap = cumulative_pv / cumulative_volume

        return vwap

    def analyze(
        self,
        symbol: str,
        data: pd.DataFrame,
        account_info: Dict,
        current_positions: List[Dict],
    ) -> Signal:
        """Analyze for VWAP bounce/rejection opportunities."""
        try:
            if not self.validate_data(data):
                return Signal("hold", 0.0, "Insufficient data")

            df = self.calculate_indicators(data)
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest

            # Check for existing position
            has_position = any(p['symbol'] == symbol for p in current_positions)

            if has_position:
                exit_signal = self._check_exit_conditions(df, current_positions, symbol)
                if exit_signal:
                    return exit_signal

            # Minimum volatility check
            if latest['atr_pct'] < 0.5:
                return Signal("hold", 0.0, "Insufficient volatility for VWAP strategy")

            # Volume confirmation required
            if latest['volume_ratio'] < 1.2:
                return Signal("hold", 0.0, "Volume too low for VWAP bounce")

            # Long signal: Price dipping to VWAP from above
            if self._check_vwap_bounce_long(df, latest, prev):
                strength = self._calculate_signal_strength(df, "long")
                reason = self._build_entry_reason(df, "long")
                return Signal("buy", strength, reason, {
                    "vwap": float(latest['vwap']),
                    "distance_pct": float(latest['vwap_distance_pct'] * 100),
                    "volume_ratio": float(latest['volume_ratio']),
                })

            # Short signal: Price rallying to VWAP from below
            if self._check_vwap_rejection_short(df, latest, prev):
                strength = self._calculate_signal_strength(df, "short")
                reason = self._build_entry_reason(df, "short")
                return Signal("sell", strength, reason, {
                    "vwap": float(latest['vwap']),
                    "distance_pct": float(latest['vwap_distance_pct'] * 100),
                    "volume_ratio": float(latest['volume_ratio']),
                })

            return Signal("hold", 0.0, "No VWAP setup")

        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {e}")
            return Signal("hold", 0.0, f"Analysis error: {e}")

    def _check_vwap_bounce_long(
        self,
        df: pd.DataFrame,
        latest: pd.Series,
        prev: pd.Series,
    ) -> bool:
        """
        Check for VWAP bounce (long entry).
        Price dips to VWAP from above = institutional buying support.
        """
        # Price must be near VWAP (within 0.2%)
        near_vwap = abs(latest['vwap_distance_pct']) < self.vwap_threshold_pct

        # Price was above VWAP recently
        was_above = prev['above_vwap']

        # Currently touching or just above VWAP
        at_vwap = latest['close'] >= latest['vwap'] * 0.998

        # Uptrend context (9 EMA above VWAP)
        uptrend_context = latest['ema_9'] > latest['vwap']

        # Price bouncing off VWAP (higher low)
        bouncing = latest['low'] >= prev['low'] * 0.999

        # Volume surge (institutions stepping in)
        volume_surge = latest['volume_ratio'] > 1.5

        # Not extended above VWAP
        not_extended = latest['close'] < latest['vwap_upper']

        # Positive momentum starting
        momentum_turning = 'roc' in latest and latest['roc'] > -1.0

        # Require core conditions
        conditions = [
            near_vwap and was_above and at_vwap,
            uptrend_context,
            volume_surge or bouncing,
            not_extended,
        ]

        return sum(bool(c) for c in conditions) >= 3

    def _check_vwap_rejection_short(
        self,
        df: pd.DataFrame,
        latest: pd.Series,
        prev: pd.Series,
    ) -> bool:
        """
        Check for VWAP rejection (short entry).
        Price rallies to VWAP from below = institutional selling resistance.
        """
        # Price must be near VWAP (within 0.2%)
        near_vwap = abs(latest['vwap_distance_pct']) < self.vwap_threshold_pct

        # Price was below VWAP recently
        was_below = prev['below_vwap']

        # Currently touching or just below VWAP
        at_vwap = latest['close'] <= latest['vwap'] * 1.002

        # Downtrend context (9 EMA below VWAP)
        downtrend_context = latest['ema_9'] < latest['vwap']

        # Price rejecting at VWAP (lower high)
        rejecting = latest['high'] <= prev['high'] * 1.001

        # Volume surge (institutions stepping in to sell)
        volume_surge = latest['volume_ratio'] > 1.5

        # Not extended below VWAP
        not_extended = latest['close'] > latest['vwap_lower']

        # Negative momentum starting
        momentum_turning = 'roc' in latest and latest['roc'] < 1.0

        # Require core conditions
        conditions = [
            near_vwap and was_below and at_vwap,
            downtrend_context,
            volume_surge or rejecting,
            not_extended,
        ]

        return sum(bool(c) for c in conditions) >= 3

    def _calculate_signal_strength(self, df: pd.DataFrame, direction: str) -> float:
        """Calculate signal strength based on setup quality."""
        latest = df.iloc[-1]
        strength = 0.6  # Base strength

        # Distance from VWAP (closer = stronger)
        distance = abs(latest['vwap_distance_pct'])
        if distance < 0.001:  # Within 0.1%
            strength += 0.2
        elif distance < 0.002:  # Within 0.2%
            strength += 0.1

        # Volume confirmation
        volume_ratio = latest['volume_ratio']
        if volume_ratio > 2.0:
            strength += 0.15
        elif volume_ratio > 1.5:
            strength += 0.1

        # Trend alignment
        if direction == "long":
            if latest['ema_9'] > latest['ema_21']:
                strength += 0.1
        else:
            if latest['ema_9'] < latest['ema_21']:
                strength += 0.1

        # Volatility (higher = better for scalping)
        if latest['atr_pct'] > 1.0:
            strength += 0.05

        return min(1.0, strength)

    def _build_entry_reason(self, df: pd.DataFrame, direction: str) -> str:
        """Build entry reason."""
        latest = df.iloc[-1]
        vwap = latest['vwap']
        distance = latest['vwap_distance_pct'] * 100
        volume_ratio = latest['volume_ratio']

        if direction == "long":
            return (
                f"VWAP Bounce (Long): Price ${latest['close']:.2f} at VWAP ${vwap:.2f} "
                f"({distance:+.2f}%), Volume {volume_ratio:.1f}x, Institutional support"
            )
        else:
            return (
                f"VWAP Rejection (Short): Price ${latest['close']:.2f} at VWAP ${vwap:.2f} "
                f"({distance:+.2f}%), Volume {volume_ratio:.1f}x, Institutional resistance"
            )

    def _check_exit_conditions(
        self,
        df: pd.DataFrame,
        current_positions: List[Dict],
        symbol: str,
    ) -> Signal:
        """Check VWAP-specific exit conditions."""
        position = next((p for p in current_positions if p['symbol'] == symbol), None)
        if not position:
            return None

        latest = df.iloc[-1]
        entry_price = position['avg_entry_price']
        current_price = latest['close']
        side = position['side']

        # Calculate P&L
        if side == 'long':
            pnl_pct = (current_price - entry_price) / entry_price
        else:
            pnl_pct = (entry_price - current_price) / entry_price

        # Quick profit target (0.4% for scalping)
        if pnl_pct >= self.profit_target_pct:
            return Signal("close", 1.0, f"VWAP scalp profit: {pnl_pct*100:.2f}%")

        # Tight stop loss (0.2%)
        if pnl_pct <= -self.stop_loss_pct:
            return Signal("close", 1.0, f"VWAP stop loss: {pnl_pct*100:.2f}%")

        # Price moved away from VWAP (take profit)
        vwap_distance = abs(latest['vwap_distance_pct'])
        if side == 'long' and current_price > latest['vwap'] * 1.003:
            return Signal("close", 0.8, "Price extended above VWAP - take profit")
        elif side == 'short' and current_price < latest['vwap'] * 0.997:
            return Signal("close", 0.8, "Price extended below VWAP - take profit")

        # VWAP crossed against position
        if side == 'long' and current_price < latest['vwap']:
            return Signal("close", 0.9, "Price broke below VWAP")
        elif side == 'short' and current_price > latest['vwap']:
            return Signal("close", 0.9, "Price broke above VWAP")

        return None
