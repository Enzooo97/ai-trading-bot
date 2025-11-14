"""
Mean reversion scalping strategy.
Exploits short-term oversold/overbought conditions for quick profits.
"""
from typing import Dict, List
import pandas as pd
from src.utils import indicators as ta
from src.strategies.base_strategy import BaseStrategy, Signal
from src.config import settings


class MeanReversionStrategy(BaseStrategy):
    """
    Mean reversion strategy for aggressive scalping.

    Entry Conditions (BUY):
    - RSI < 30 (oversold)
    - Price near lower Bollinger Band
    - Volume spike (capitulation)
    - No strong downtrend

    Entry Conditions (SELL/Short):
    - RSI > 70 (overbought)
    - Price near upper Bollinger Band
    - Volume spike (exhaustion)
    - No strong uptrend

    Exit:
    - Price returns to mean (middle BB)
    - 2-3% profit target
    - 1.5% stop loss
    """

    def __init__(self):
        super().__init__("MeanReversion")
        self.min_bars = 100

    def get_required_bars(self) -> int:
        return self.min_bars

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate mean reversion indicators."""
        df = data.copy()

        # RSI
        df['rsi'] = ta.rsi(df['close'], length=14)
        df['rsi_fast'] = ta.rsi(df['close'], length=7)

        # Bollinger Bands
        bbands = ta.bbands(df['close'], length=20, std=2.0)
        if bbands is not None:
            df['bb_upper'] = bbands['BBU_20_2.0']
            df['bb_middle'] = bbands['BBM_20_2.0']
            df['bb_lower'] = bbands['BBL_20_2.0']
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
            df['bb_pct'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

        # Stochastic
        stoch = ta.stoch(df['high'], df['low'], df['close'], k=14, d=3)
        if stoch is not None:
            df['stoch_k'] = stoch['STOCHk_14_3_3']
            df['stoch_d'] = stoch['STOCHd_14_3_3']

        # Moving averages for trend context
        df['sma_20'] = ta.sma(df['close'], length=20)
        df['sma_50'] = ta.sma(df['close'], length=50)

        # Volume
        df['volume_sma'] = ta.sma(df['volume'], length=20)
        df['volume_ratio'] = df['volume'] / df['volume_sma']

        # ATR
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        df['atr_pct'] = (df['atr'] / df['close']) * 100

        # Z-score (distance from mean in standard deviations)
        df['price_zscore'] = (df['close'] - df['sma_20']) / df['close'].rolling(20).std()

        return df

    def analyze(
        self,
        symbol: str,
        data: pd.DataFrame,
        account_info: Dict,
        current_positions: List[Dict],
    ) -> Signal:
        """Analyze for mean reversion opportunities."""
        try:
            if not self.validate_data(data):
                return Signal("hold", 0.0, "Insufficient data")

            df = self.calculate_indicators(data)
            latest = df.iloc[-1]

            # Check for existing position
            has_position = any(p['symbol'] == symbol for p in current_positions)

            if has_position:
                exit_signal = self._check_exit_conditions(df, current_positions, symbol)
                if exit_signal:
                    return exit_signal

            # Check minimum volatility
            if latest['atr_pct'] < 0.8:
                return Signal("hold", 0.0, "Insufficient volatility")

            # Long entry conditions (oversold)
            if self._check_oversold_entry(df, latest):
                strength = self._calculate_signal_strength(df, "long")
                reason = self._build_entry_reason(df, "long")
                return Signal("buy", strength, reason, {
                    "rsi": float(latest['rsi']),
                    "bb_pct": float(latest['bb_pct']),
                    "stoch_k": float(latest.get('stoch_k', 0)),
                })

            # Short entry conditions (overbought)
            if self._check_overbought_entry(df, latest):
                strength = self._calculate_signal_strength(df, "short")
                reason = self._build_entry_reason(df, "short")
                return Signal("sell", strength, reason, {
                    "rsi": float(latest['rsi']),
                    "bb_pct": float(latest['bb_pct']),
                    "stoch_k": float(latest.get('stoch_k', 0)),
                })

            return Signal("hold", 0.0, "No mean reversion signal")

        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {e}")
            return Signal("hold", 0.0, f"Analysis error: {e}")

    def _check_oversold_entry(self, df: pd.DataFrame, latest: pd.Series) -> bool:
        """Check for oversold entry conditions."""
        # RSI oversold
        rsi_oversold = latest['rsi'] < 30 and latest['rsi_fast'] < 35

        # Near lower Bollinger Band
        bb_oversold = 'bb_pct' in latest and latest['bb_pct'] < 0.2

        # Volume spike (selling climax)
        volume_spike = latest['volume_ratio'] > 1.3

        # Not in strong downtrend
        not_strong_downtrend = latest['close'] > latest['sma_50'] * 0.95

        # Stochastic confirmation
        stoch_oversold = 'stoch_k' in latest and latest['stoch_k'] < 20

        # Price below mean (Z-score)
        price_below_mean = 'price_zscore' in latest and latest['price_zscore'] < -1.5

        conditions = [
            rsi_oversold,
            bb_oversold,
            volume_spike,
            not_strong_downtrend,
            stoch_oversold or price_below_mean
        ]

        return sum(bool(c) for c in conditions) >= 4

    def _check_overbought_entry(self, df: pd.DataFrame, latest: pd.Series) -> bool:
        """Check for overbought entry conditions."""
        # RSI overbought
        rsi_overbought = latest['rsi'] > 70 and latest['rsi_fast'] > 65

        # Near upper Bollinger Band
        bb_overbought = 'bb_pct' in latest and latest['bb_pct'] > 0.8

        # Volume spike (buying exhaustion)
        volume_spike = latest['volume_ratio'] > 1.3

        # Not in strong uptrend
        not_strong_uptrend = latest['close'] < latest['sma_50'] * 1.05

        # Stochastic confirmation
        stoch_overbought = 'stoch_k' in latest and latest['stoch_k'] > 80

        # Price above mean (Z-score)
        price_above_mean = 'price_zscore' in latest and latest['price_zscore'] > 1.5

        conditions = [
            rsi_overbought,
            bb_overbought,
            volume_spike,
            not_strong_uptrend,
            stoch_overbought or price_above_mean
        ]

        return sum(bool(c) for c in conditions) >= 4

    def _calculate_signal_strength(self, df: pd.DataFrame, direction: str) -> float:
        """Calculate signal strength."""
        latest = df.iloc[-1]
        strength = 0.5

        # RSI extremes
        rsi = latest['rsi']
        if direction == "long":
            if rsi < 25:
                strength += 0.2
            elif rsi < 30:
                strength += 0.1
        else:
            if rsi > 75:
                strength += 0.2
            elif rsi > 70:
                strength += 0.1

        # Bollinger Band position
        if 'bb_pct' in latest:
            bb_pct = latest['bb_pct']
            if direction == "long" and bb_pct < 0.1:
                strength += 0.15
            elif direction == "short" and bb_pct > 0.9:
                strength += 0.15

        # Volume confirmation
        if latest['volume_ratio'] > 1.5:
            strength += 0.15

        return min(1.0, strength)

    def _build_entry_reason(self, df: pd.DataFrame, direction: str) -> str:
        """Build entry reason."""
        latest = df.iloc[-1]
        rsi = latest['rsi']
        bb_pct = latest.get('bb_pct', 0)
        volume_ratio = latest['volume_ratio']

        if direction == "long":
            return (
                f"Oversold mean reversion (Long): RSI={rsi:.1f}, "
                f"BB%={bb_pct*100:.1f}, Volume={volume_ratio:.1f}x"
            )
        else:
            return (
                f"Overbought mean reversion (Short): RSI={rsi:.1f}, "
                f"BB%={bb_pct*100:.1f}, Volume={volume_ratio:.1f}x"
            )

    def _check_exit_conditions(
        self,
        df: pd.DataFrame,
        current_positions: List[Dict],
        symbol: str,
    ) -> Signal:
        """Check exit conditions."""
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

        # Quick profit target (mean reversion is fast)
        if pnl_pct >= 0.025:  # 2.5% profit
            return Signal("close", 1.0, f"Take profit: {pnl_pct*100:.2f}%")

        # Stop loss
        if pnl_pct <= -0.015:  # 1.5% loss
            return Signal("close", 1.0, f"Stop loss: {pnl_pct*100:.2f}%")

        # Price returned to mean
        if 'bb_pct' in latest:
            bb_pct = latest['bb_pct']
            if side == 'long' and bb_pct > 0.5:
                return Signal("close", 0.8, "Price returned to mean")
            elif side == 'short' and bb_pct < 0.5:
                return Signal("close", 0.8, "Price returned to mean")

        # RSI normalization
        rsi = latest['rsi']
        if side == 'long' and rsi > 50:
            return Signal("close", 0.6, "RSI normalized")
        elif side == 'short' and rsi < 50:
            return Signal("close", 0.6, "RSI normalized")

        return None
