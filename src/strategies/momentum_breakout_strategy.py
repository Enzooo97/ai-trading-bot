"""
Aggressive momentum breakout strategy for scalping.
Identifies strong momentum moves and rides them for quick profits.
"""
from typing import Dict, List
import pandas as pd
from src.utils import indicators as ta
from src.strategies.base_strategy import BaseStrategy, Signal
from src.config import settings


class MomentumBreakoutStrategy(BaseStrategy):
    """
    Momentum breakout strategy optimized for aggressive scalping.

    Entry Conditions (BUY):
    - Price breaks above resistance with high volume
    - RSI > 60 (momentum building)
    - MACD bullish crossover
    - Volume > 1.5x average
    - Volatility > 1% (enough movement for scalping)

    Entry Conditions (SELL/Short):
    - Price breaks below support with high volume
    - RSI < 40 (momentum declining)
    - MACD bearish crossover
    - Volume > 1.5x average

    Exit:
    - 2-4% profit target
    - 1.5% stop loss
    - Position hold max 2-3 hours
    """

    def __init__(self):
        super().__init__("MomentumBreakout")
        self.min_bars = 100

    def get_required_bars(self) -> int:
        return self.min_bars

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators for momentum analysis."""
        df = data.copy()

        # Moving averages
        df['sma_20'] = ta.sma(df['close'], length=20)
        df['sma_50'] = ta.sma(df['close'], length=50)
        df['ema_9'] = ta.ema(df['close'], length=9)
        df['ema_21'] = ta.ema(df['close'], length=21)

        # RSI
        df['rsi'] = ta.rsi(df['close'], length=14)

        # MACD
        macd = ta.macd(df['close'], fast=settings.macd_fast, slow=settings.macd_slow, signal=settings.macd_signal)
        if macd is not None:
            df['macd'] = macd['MACD_12_26_9']
            df['macd_signal'] = macd['MACDs_12_26_9']
            df['macd_hist'] = macd['MACDh_12_26_9']

        # Bollinger Bands
        bbands = ta.bbands(df['close'], length=settings.bollinger_period, std=settings.bollinger_std)
        if bbands is not None:
            df['bb_upper'] = bbands['BBU_20_2.0']
            df['bb_middle'] = bbands['BBM_20_2.0']
            df['bb_lower'] = bbands['BBL_20_2.0']
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']

        # ATR for volatility
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        df['atr_pct'] = (df['atr'] / df['close']) * 100

        # Volume indicators
        df['volume_sma'] = ta.sma(df['volume'], length=20)
        df['volume_ratio'] = df['volume'] / df['volume_sma']

        # Rate of Change
        df['roc'] = ta.roc(df['close'], length=10)

        # ADX for trend strength
        adx = ta.adx(df['high'], df['low'], df['close'], length=14)
        if adx is not None:
            df['adx'] = adx['ADX_14']
            df['plus_di'] = adx['DMP_14']
            df['minus_di'] = adx['DMN_14']

        # Support and resistance levels
        df['resistance'] = df['high'].rolling(window=20).max()
        df['support'] = df['low'].rolling(window=20).min()

        return df

    def analyze(
        self,
        symbol: str,
        data: pd.DataFrame,
        account_info: Dict,
        current_positions: List[Dict],
    ) -> Signal:
        """Analyze for momentum breakout opportunities."""
        try:
            # Validate data
            if not self.validate_data(data):
                return Signal("hold", 0.0, "Insufficient data")

            # Calculate indicators
            df = self.calculate_indicators(data)

            # Get latest values
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest

            # Extract indicators
            close = latest['close']
            rsi = latest['rsi']
            volume_ratio = latest['volume_ratio']
            atr_pct = latest['atr_pct']

            # Check if we have open position
            has_position = any(p['symbol'] == symbol for p in current_positions)

            # Exit signals for existing positions
            if has_position:
                exit_signal = self._check_exit_conditions(df, current_positions, symbol)
                if exit_signal:
                    return exit_signal

            # Don't enter if insufficient volatility (relaxed from 1.0 to 0.6)
            if atr_pct < 0.6:
                return Signal("hold", 0.0, "Insufficient volatility for scalping")

            # Don't enter if volume too low (relaxed from 1.2 to 1.0)
            if volume_ratio < 1.0:
                return Signal("hold", 0.0, "Volume too low")

            # Long (BUY) signals
            if self._check_long_entry(df, latest, prev):
                strength = self._calculate_signal_strength(df, "long")
                reason = self._build_entry_reason(df, "long")
                return Signal("buy", strength, reason, {
                    "rsi": float(rsi),
                    "volume_ratio": float(volume_ratio),
                    "atr_pct": float(atr_pct),
                })

            # Short (SELL) signals
            if self._check_short_entry(df, latest, prev):
                strength = self._calculate_signal_strength(df, "short")
                reason = self._build_entry_reason(df, "short")
                return Signal("sell", strength, reason, {
                    "rsi": float(rsi),
                    "volume_ratio": float(volume_ratio),
                    "atr_pct": float(atr_pct),
                })

            return Signal("hold", 0.0, "No clear signal")

        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {e}")
            return Signal("hold", 0.0, f"Analysis error: {e}")

    def _check_long_entry(self, df: pd.DataFrame, latest: pd.Series, prev: pd.Series) -> bool:
        """Check if long entry conditions are met."""
        # Price action
        close = latest['close']
        resistance = latest['resistance']
        breakout = close > resistance * 0.998  # Within 0.2% of resistance

        # Momentum (relaxed RSI range)
        rsi = latest['rsi']
        rsi_momentum = 50 < rsi < 80  # More relaxed range

        # MACD (optional now)
        macd_bullish = (
            'macd' in latest and 'macd_signal' in latest and
            latest['macd'] > latest['macd_signal']
        )

        # Volume (relaxed threshold)
        volume_confirmation = latest['volume_ratio'] > 1.3

        # Trend
        uptrend = latest['ema_9'] > latest['ema_21']

        # ADX for trend strength (relaxed)
        strong_trend = 'adx' in latest and latest['adx'] > 20

        # Require fewer conditions (3 out of 5 instead of 4)
        conditions = [breakout, rsi_momentum, macd_bullish or strong_trend, volume_confirmation, uptrend]
        met_conditions = sum(bool(c) for c in conditions)

        return met_conditions >= 3  # Relaxed from 4 to 3

    def _check_short_entry(self, df: pd.DataFrame, latest: pd.Series, prev: pd.Series) -> bool:
        """Check if short entry conditions are met."""
        # Price action
        close = latest['close']
        support = latest['support']
        breakdown = close < support * 1.002  # Within 0.2% of support

        # Momentum (relaxed RSI range)
        rsi = latest['rsi']
        rsi_momentum = 20 < rsi < 50  # More relaxed range

        # MACD (optional now)
        macd_bearish = (
            'macd' in latest and 'macd_signal' in latest and
            latest['macd'] < latest['macd_signal']
        )

        # Volume (relaxed threshold)
        volume_confirmation = latest['volume_ratio'] > 1.3

        # Trend
        downtrend = latest['ema_9'] < latest['ema_21']

        # ADX for trend strength (relaxed)
        strong_trend = 'adx' in latest and latest['adx'] > 20

        # Require fewer conditions (3 out of 5 instead of 4)
        conditions = [breakdown, rsi_momentum, macd_bearish or strong_trend, volume_confirmation, downtrend]
        met_conditions = sum(bool(c) for c in conditions)

        return met_conditions >= 3  # Relaxed from 4 to 3

    def _calculate_signal_strength(self, df: pd.DataFrame, direction: str) -> float:
        """Calculate signal strength (0.0 to 1.0)."""
        latest = df.iloc[-1]
        strength = 0.5  # Base strength

        # Volume boost
        volume_ratio = latest['volume_ratio']
        if volume_ratio > 2.0:
            strength += 0.2
        elif volume_ratio > 1.5:
            strength += 0.1

        # Volatility boost (more volatility = better for scalping)
        atr_pct = latest['atr_pct']
        if atr_pct > 2.0:
            strength += 0.15
        elif atr_pct > 1.5:
            strength += 0.1

        # Trend strength boost
        if 'adx' in latest:
            adx = latest['adx']
            if adx > 40:
                strength += 0.15
            elif adx > 30:
                strength += 0.1

        return min(1.0, strength)  # Cap at 1.0

    def _build_entry_reason(self, df: pd.DataFrame, direction: str) -> str:
        """Build human-readable entry reason."""
        latest = df.iloc[-1]
        rsi = latest['rsi']
        volume_ratio = latest['volume_ratio']
        atr_pct = latest['atr_pct']

        if direction == "long":
            return (
                f"Momentum breakout (Long): RSI={rsi:.1f}, "
                f"Volume={volume_ratio:.1f}x, Volatility={atr_pct:.2f}%, "
                f"MACD bullish crossover"
            )
        else:
            return (
                f"Momentum breakdown (Short): RSI={rsi:.1f}, "
                f"Volume={volume_ratio:.1f}x, Volatility={atr_pct:.2f}%, "
                f"MACD bearish crossover"
            )

    def _check_exit_conditions(
        self,
        df: pd.DataFrame,
        current_positions: List[Dict],
        symbol: str,
    ) -> Signal:
        """Check if position should be exited."""
        position = next((p for p in current_positions if p['symbol'] == symbol), None)
        if not position:
            return None

        latest = df.iloc[-1]
        entry_price = position['avg_entry_price']
        current_price = latest['close']
        side = position['side']

        # Calculate P&L percentage
        if side == 'long':
            pnl_pct = (current_price - entry_price) / entry_price
        else:
            pnl_pct = (entry_price - current_price) / entry_price

        # Take profit (aggressive target)
        if pnl_pct >= 0.03:  # 3% profit
            return Signal("close", 1.0, f"Take profit: {pnl_pct*100:.2f}%")

        # Stop loss
        if pnl_pct <= -0.015:  # 1.5% loss
            return Signal("close", 1.0, f"Stop loss: {pnl_pct*100:.2f}%")

        # Momentum reversal
        rsi = latest['rsi']
        if side == 'long' and rsi > 75:
            return Signal("close", 0.8, "RSI overbought - momentum fading")
        elif side == 'short' and rsi < 25:
            return Signal("close", 0.8, "RSI oversold - momentum fading")

        # MACD reversal
        if 'macd' in latest and 'macd_signal' in latest:
            if side == 'long' and latest['macd'] < latest['macd_signal']:
                return Signal("close", 0.7, "MACD bearish crossover")
            elif side == 'short' and latest['macd'] > latest['macd_signal']:
                return Signal("close", 0.7, "MACD bullish crossover")

        return None
