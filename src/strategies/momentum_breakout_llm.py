"""
LLM-Enhanced Momentum Breakout Strategy.

This strategy combines the profitable Momentum Breakout logic with:
1. Market Regime Filtering (only trade in favorable conditions)
2. Trade Quality Scoring (skip low-quality setups)
3. Dynamic Position Sizing (adjust based on confidence)

Expected improvement: 8.5% -> 12-18% annual returns
"""
from typing import Dict, List, Optional
import pandas as pd
from src.strategies.base_strategy import BaseStrategy, Signal
from src.utils import indicators as ta
from src.llm_integration.enhanced_llm_service import EnhancedLLMService, MarketRegime
import logging

logger = logging.getLogger(__name__)


class MomentumBreakoutLLM(BaseStrategy):
    """
    LLM-Enhanced Momentum Breakout Strategy.

    Base Strategy Performance (180 days):
    - Return: +4.11% (8.51% annualized)
    - Sharpe: 1.62
    - Win Rate: 52.3%

    LLM Enhancements:
    1. Market regime filtering (only trade in trending markets)
    2. Trade quality scoring (skip scores < 70)
    3. Position sizing optimization (0.5x to 1.5x based on confidence)

    Target Performance:
    - Return: 12-18% annualized
    - Sharpe: >2.0
    - Win Rate: 55-60%
    """

    def __init__(self, use_llm: bool = True, llm_score_threshold: int = 70):
        """
        Initialize LLM-enhanced momentum strategy.

        Args:
            use_llm: Enable LLM filtering (set False to test base strategy)
            llm_score_threshold: Minimum score to execute trade (0-100)
        """
        super().__init__("Momentum_Breakout_LLM")
        self.min_bars = 100  # Need more history for regime detection
        self.use_llm = use_llm
        self.llm_score_threshold = llm_score_threshold

        # Initialize LLM service if enabled
        self.llm_service = EnhancedLLMService() if use_llm else None

        # Statistics tracking
        self.llm_filtered_count = 0
        self.llm_approved_count = 0
        self.regime_filtered_count = 0

        logger.info(f"Momentum Breakout LLM initialized (LLM: {use_llm}, threshold: {llm_score_threshold})")

    def get_required_bars(self) -> int:
        return self.min_bars

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate indicators for momentum breakout + regime detection."""
        df = data.copy()

        # Core momentum indicators
        df['rsi'] = ta.rsi(df['close'], length=14)
        df['roc'] = ta.roc(df['close'], length=10)

        # Moving averages for trend
        df['ema_20'] = ta.ema(df['close'], length=20)
        df['ema_50'] = ta.ema(df['close'], length=50)
        df['sma_200'] = ta.sma(df['close'], length=200)

        # Volume
        df['volume_sma'] = ta.sma(df['volume'], length=20)
        df['volume_ratio'] = df['volume'] / df['volume_sma']

        # Volatility
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        df['atr_pct'] = (df['atr'] / df['close']) * 100

        # Trend strength (ADX)
        adx_result = ta.adx(df['high'], df['low'], df['close'], length=14)
        if adx_result is not None and isinstance(adx_result, pd.DataFrame):
            df['adx'] = adx_result[f'ADX_14'] if f'ADX_14' in adx_result.columns else adx_result.iloc[:, 0]
        else:
            df['adx'] = 0

        # MACD for momentum confirmation
        macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
        if macd is not None:
            df['macd'] = macd['MACD_12_26_9']
            df['macd_signal'] = macd['MACDs_12_26_9']
            df['macd_hist'] = macd['MACDh_12_26_9']

        # Bollinger Bands for breakout detection
        df['bb_upper'] = df['close'].rolling(20).mean() + 2 * df['close'].rolling(20).std()
        df['bb_lower'] = df['close'].rolling(20).mean() - 2 * df['close'].rolling(20).std()
        df['bb_middle'] = df['close'].rolling(20).mean()

        # Price relative to key levels
        df['above_ema20'] = df['close'] > df['ema_20']
        df['above_ema50'] = df['close'] > df['ema_50']
        df['above_sma200'] = df['close'] > df['sma_200']

        return df

    def analyze(
        self,
        symbol: str,
        data: pd.DataFrame,
        account_info: Dict,
        current_positions: List[Dict],
    ) -> Signal:
        """Analyze for momentum breakout with LLM enhancement."""
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

            # Step 1: LLM Market Regime Check (if enabled)
            regime_result = None
            adaptive_threshold = self.llm_score_threshold  # Default to static threshold

            if self.use_llm and self.llm_service:
                regime_result = self.llm_service.detect_market_regime(symbol, df)

                # Get adaptive threshold based on regime strength
                adaptive_threshold = self.llm_service.get_adaptive_threshold(
                    regime=regime_result['regime'],
                    confidence=regime_result['confidence']
                )

                # Only trade if regime is favorable for momentum
                if not regime_result.get('optimal_for_momentum', False):
                    self.regime_filtered_count += 1
                    logger.debug(f"Regime filter: {symbol} not optimal for momentum ({regime_result['regime']})")
                    return Signal("hold", 0.0, f"Unfavorable regime: {regime_result['regime']}")

            # Step 2: Generate base signal (original momentum logic)
            base_signal = self._generate_base_signal(df, latest, prev)

            if base_signal.action == "hold":
                return base_signal

            # Step 3: LLM Trade Quality Scoring (if enabled)
            if self.use_llm and self.llm_service and base_signal.action != "hold":
                # Prepare data for LLM
                market_data = {
                    'close': float(latest['close']),
                    'volume_ratio': float(latest['volume_ratio']),
                    'atr_pct': float(latest['atr_pct'])
                }

                indicators = {
                    'rsi': float(latest['rsi']),
                    'adx': float(latest.get('adx', 0)),
                    'macd': float(latest.get('macd', 0))
                }

                # Score trade quality
                score_result = self.llm_service.score_trade_quality(
                    symbol=symbol,
                    signal_action=base_signal.action,
                    signal_reason=base_signal.reason,
                    signal_strength=base_signal.strength,
                    market_data=market_data,
                    indicators=indicators
                )

                # Check if trade passes quality threshold (using adaptive threshold)
                if score_result['score'] < adaptive_threshold:
                    self.llm_filtered_count += 1
                    logger.info(f"LLM filtered: {symbol} {base_signal.action} (score: {score_result['score']}/{adaptive_threshold})")
                    return Signal("hold", 0.0, f"LLM score too low: {score_result['score']}/{adaptive_threshold} - {score_result['reasoning']}")

                # Trade approved!
                self.llm_approved_count += 1

                # Adjust position size based on LLM recommendation
                adjusted_strength = base_signal.strength * score_result.get('position_size_multiplier', 1.0)

                # Add LLM insights to signal metadata
                metadata = base_signal.metadata or {}
                metadata['llm_score'] = score_result['score']
                metadata['llm_reasoning'] = score_result['reasoning']
                metadata['llm_confidence'] = score_result['confidence']
                metadata['position_multiplier'] = score_result.get('position_size_multiplier', 1.0)
                metadata['adaptive_threshold'] = adaptive_threshold
                if regime_result:
                    metadata['market_regime'] = regime_result['regime']
                    metadata['regime_confidence'] = regime_result['confidence']

                logger.info(f"LLM approved: {symbol} {base_signal.action} (score: {score_result['score']}/{adaptive_threshold}, regime: {regime_result['regime'] if regime_result else 'N/A'}, mult: {score_result.get('position_size_multiplier', 1.0):.2f}x)")

                return Signal(
                    action=base_signal.action,
                    strength=min(1.0, adjusted_strength),  # Cap at 1.0
                    reason=f"{base_signal.reason} | LLM: {score_result['reasoning'][:50]}",
                    metadata=metadata
                )

            # Return base signal if LLM disabled
            return base_signal

        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {e}")
            return Signal("hold", 0.0, f"Analysis error: {e}")

    def _generate_base_signal(self, df: pd.DataFrame, latest: pd.Series, prev: pd.Series) -> Signal:
        """Generate base momentum breakout signal (original logic)."""
        # Minimum volatility
        if latest['atr_pct'] < 0.6:
            return Signal("hold", 0.0, "Insufficient volatility")

        # Volume confirmation
        if latest['volume_ratio'] < 1.0:
            return Signal("hold", 0.0, "Volume too low")

        # Check for bullish breakout
        if self._check_bullish_breakout(df, latest, prev):
            strength = self._calculate_signal_strength(df, "long")
            reason = f"Momentum Breakout Long: RSI={latest['rsi']:.1f}, Vol={latest['volume_ratio']:.1f}x"
            return Signal("buy", strength, reason, {
                'rsi': float(latest['rsi']),
                'volume_ratio': float(latest['volume_ratio']),
                'atr_pct': float(latest['atr_pct'])
            })

        # Check for bearish breakout
        if self._check_bearish_breakout(df, latest, prev):
            strength = self._calculate_signal_strength(df, "short")
            reason = f"Momentum Breakout Short: RSI={latest['rsi']:.1f}, Vol={latest['volume_ratio']:.1f}x"
            return Signal("sell", strength, reason, {
                'rsi': float(latest['rsi']),
                'volume_ratio': float(latest['volume_ratio']),
                'atr_pct': float(latest['atr_pct'])
            })

        return Signal("hold", 0.0, "No momentum breakout")

    def _check_bullish_breakout(self, df: pd.DataFrame, latest: pd.Series, prev: pd.Series) -> bool:
        """Check for bullish momentum breakout."""
        # Price breakout above Bollinger upper band or recent high
        breakout = (latest['close'] > latest['bb_upper'] or
                   latest['close'] > df['high'].rolling(20).max().iloc[-2])

        # Momentum indicators
        rsi_momentum = 50 < latest['rsi'] < 80
        macd_bullish = latest.get('macd', 0) > latest.get('macd_signal', 0)

        # Trend confirmation
        uptrend = (latest['ema_20'] > latest['ema_50'] and
                  latest['close'] > latest['ema_20'])

        # Strong trend (ADX)
        strong_trend = latest.get('adx', 0) > 20

        # Volume surge
        volume_confirmation = latest['volume_ratio'] > 1.3

        # Require most conditions
        conditions = [breakout, rsi_momentum, macd_bullish or strong_trend, volume_confirmation, uptrend]
        return sum(bool(c) for c in conditions) >= 3

    def _check_bearish_breakout(self, df: pd.DataFrame, latest: pd.Series, prev: pd.Series) -> bool:
        """Check for bearish momentum breakout."""
        # Price breakdown below Bollinger lower band or recent low
        breakout = (latest['close'] < latest['bb_lower'] or
                   latest['close'] < df['low'].rolling(20).min().iloc[-2])

        # Momentum indicators
        rsi_momentum = 20 < latest['rsi'] < 50
        macd_bearish = latest.get('macd', 0) < latest.get('macd_signal', 0)

        # Trend confirmation
        downtrend = (latest['ema_20'] < latest['ema_50'] and
                    latest['close'] < latest['ema_20'])

        # Strong trend (ADX)
        strong_trend = latest.get('adx', 0) > 20

        # Volume surge
        volume_confirmation = latest['volume_ratio'] > 1.3

        # Require most conditions
        conditions = [breakout, rsi_momentum, macd_bearish or strong_trend, volume_confirmation, downtrend]
        return sum(bool(c) for c in conditions) >= 3

    def _calculate_signal_strength(self, df: pd.DataFrame, direction: str) -> float:
        """Calculate signal strength."""
        latest = df.iloc[-1]
        strength = 0.6  # Base

        # ADX strength
        adx = latest.get('adx', 0)
        if adx > 30:
            strength += 0.2
        elif adx > 20:
            strength += 0.1

        # Volume confirmation
        if latest['volume_ratio'] > 2.0:
            strength += 0.15
        elif latest['volume_ratio'] > 1.5:
            strength += 0.1

        # RSI positioning
        rsi = latest['rsi']
        if direction == "long" and 55 < rsi < 70:
            strength += 0.1
        elif direction == "short" and 30 < rsi < 45:
            strength += 0.1

        return min(1.0, strength)

    def _check_exit_conditions(
        self,
        df: pd.DataFrame,
        current_positions: List[Dict],
        symbol: str,
    ) -> Optional[Signal]:
        """Check exit conditions for open positions."""
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

        # Profit targets (same as original)
        if pnl_pct >= 0.05:  # 5% profit target
            return Signal("close", 1.0, f"Profit target: {pnl_pct*100:.2f}%")

        # Stop loss
        if pnl_pct <= -0.02:  # 2% stop loss
            return Signal("close", 1.0, f"Stop loss: {pnl_pct*100:.2f}%")

        # Momentum reversal
        if side == 'long':
            if latest['close'] < latest['ema_20']:
                return Signal("close", 0.9, "Below EMA20 - momentum lost")
        elif side == 'short':
            if latest['close'] > latest['ema_20']:
                return Signal("close", 0.9, "Above EMA20 - momentum lost")

        return None

    def get_llm_statistics(self) -> Dict:
        """Get LLM filtering statistics."""
        total_signals = self.llm_approved_count + self.llm_filtered_count
        if total_signals == 0:
            return {'enabled': self.use_llm, 'no_signals': True}

        return {
            'enabled': self.use_llm,
            'total_base_signals': total_signals,
            'llm_approved': self.llm_approved_count,
            'llm_filtered': self.llm_filtered_count,
            'regime_filtered': self.regime_filtered_count,
            'approval_rate': f"{self.llm_approved_count / total_signals * 100:.1f}%",
            'llm_performance': self.llm_service.get_performance_stats() if self.llm_service else {}
        }
