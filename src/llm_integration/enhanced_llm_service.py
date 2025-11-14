"""
Enhanced LLM Service for Market Regime Detection and Trade Quality Scoring.

This module provides:
1. Market Regime Detection (every 15 minutes)
2. Trade Quality Scoring (before each trade)
3. Dynamic Parameter Optimization (daily)
4. Position Sizing Recommendations (real-time)

Designed specifically to improve Momentum Breakout strategy from 8.5% to 12-18% annual returns.
"""
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
import anthropic
import pandas as pd
from src.config import settings

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime classifications."""
    STRONG_UPTREND = "strong_uptrend"
    WEAK_UPTREND = "weak_uptrend"
    STRONG_DOWNTREND = "strong_downtrend"
    WEAK_DOWNTREND = "weak_downtrend"
    RANGING_TIGHT = "ranging_tight"
    RANGING_WIDE = "ranging_wide"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"


class EnhancedLLMService:
    """
    Enhanced LLM service for intelligent trading decisions.

    Key Features:
    - Market regime detection with caching (updates every 15 min)
    - Trade quality scoring (0-100 scale)
    - Fast responses (<2 seconds for trade scoring)
    - Conservative by default (helps avoid bad trades)
    """

    def __init__(self):
        """Initialize enhanced LLM service."""
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-3-haiku-20240307"  # Fast, cost-effective model for trading

        # Cache for market regime (updates every 15 min)
        self.regime_cache: Dict[str, Dict] = {}
        self.regime_cache_expiry = timedelta(minutes=15)

        # Performance tracking
        self.total_calls = 0
        self.total_time_ms = 0

        logger.info(f"Enhanced LLM Service initialized with {self.model}")

    def detect_market_regime(
        self,
        symbol: str,
        market_data: pd.DataFrame,
        force_refresh: bool = False
    ) -> Dict:
        """
        Detect current market regime for a symbol.

        Uses cached result if less than 15 minutes old.

        Args:
            symbol: Stock symbol
            market_data: DataFrame with OHLCV + indicators (last 100 bars minimum)
            force_refresh: Force new LLM call even if cached

        Returns:
            Dict with:
                - regime: MarketRegime enum
                - confidence: 0.0-1.0
                - reasoning: str
                - key_characteristics: List[str]
                - recommended_strategies: List[str]
                - optimal_for_momentum: bool
        """
        # Check cache
        if not force_refresh and symbol in self.regime_cache:
            cache_entry = self.regime_cache[symbol]
            age = datetime.now() - cache_entry['timestamp']
            if age < self.regime_cache_expiry:
                logger.debug(f"Using cached regime for {symbol} (age: {age.seconds}s)")
                return cache_entry['result']

        try:
            start_time = datetime.now()

            # Build regime detection prompt
            prompt = self._build_regime_prompt(symbol, market_data)

            # Query LLM
            response = self._query_llm_fast(prompt, max_tokens=512)

            # Parse response
            result = self._parse_regime_response(response)

            # Add metadata
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            result['processing_time_ms'] = int(processing_time)
            result['timestamp'] = datetime.now()

            # Update cache
            self.regime_cache[symbol] = {
                'timestamp': datetime.now(),
                'result': result
            }

            # Track performance
            self.total_calls += 1
            self.total_time_ms += processing_time

            logger.info(f"Regime for {symbol}: {result['regime']} (conf: {result['confidence']:.2f}, {processing_time:.0f}ms)")

            return result

        except Exception as e:
            logger.error(f"Error detecting market regime for {symbol}: {e}")
            # Return conservative fallback
            return {
                'regime': MarketRegime.RANGING_TIGHT.value,
                'confidence': 0.0,
                'reasoning': f"Error: {str(e)}",
                'key_characteristics': [],
                'recommended_strategies': [],
                'optimal_for_momentum': False,
                'processing_time_ms': 0,
                'timestamp': datetime.now()
            }

    def get_adaptive_threshold(self, regime: str, confidence: float) -> int:
        """
        Get adaptive LLM score threshold based on market regime strength.

        Strong trending markets get lower thresholds (allow more trades).
        Weak/ranging markets get higher thresholds (be more selective).

        Args:
            regime: Market regime classification
            confidence: LLM's confidence in the regime (0.0-1.0)

        Returns:
            Recommended score threshold (0-100)
        """
        # Strong trending regimes - lower threshold (55-60)
        if regime in ["strong_uptrend", "strong_downtrend"]:
            if confidence >= 0.8:
                return 55  # Very confident strong trend
            else:
                return 60  # Moderately confident strong trend

        # Weak trending regimes - medium threshold (65)
        elif regime in ["weak_uptrend", "weak_downtrend"]:
            return 65

        # Ranging markets - higher threshold (70-75)
        elif regime in ["ranging_tight", "ranging_wide"]:
            if regime == "ranging_tight":
                return 75  # Very selective in tight ranges
            else:
                return 70  # Somewhat selective in wide ranges

        # High volatility - be selective (70)
        elif regime == "high_volatility":
            return 70

        # Low volatility - very selective (75)
        elif regime == "low_volatility":
            return 75

        # Default: conservative
        return 70

    def score_trade_quality(
        self,
        symbol: str,
        signal_action: str,
        signal_reason: str,
        signal_strength: float,
        market_data: Dict,
        indicators: Dict,
        recent_trades: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Score trade quality from 0-100.

        Fast scoring (<2 seconds) to validate trades before execution.
        Only trades scoring >70 should be executed.

        Args:
            symbol: Stock symbol
            signal_action: "buy", "sell", or "hold"
            signal_reason: Why the signal was generated
            signal_strength: Strategy's confidence (0.0-1.0)
            market_data: Current market state
            indicators: Technical indicator values
            recent_trades: Recent trade history for this symbol

        Returns:
            Dict with:
                - score: 0-100 (0=terrible, 100=excellent)
                - confidence: 0.0-1.0 (LLM's confidence in the score)
                - reasoning: Brief explanation
                - risk_factors: List[str]
                - opportunity_factors: List[str]
                - recommended_action: "execute", "skip", "reduce_size"
                - position_size_multiplier: 0.5-2.0 (adjust position size)
        """
        try:
            start_time = datetime.now()

            # Build scoring prompt
            prompt = self._build_scoring_prompt(
                symbol, signal_action, signal_reason, signal_strength,
                market_data, indicators, recent_trades
            )

            # Query LLM (fast mode)
            response = self._query_llm_fast(prompt, max_tokens=400)

            # Parse response
            result = self._parse_scoring_response(response)

            # Add metadata
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            result['processing_time_ms'] = int(processing_time)

            # Determine recommendation
            score = result['score']
            if score >= 70:
                result['recommended_action'] = 'execute'
                result['position_size_multiplier'] = 1.0  # Normal size
            elif score >= 50:
                result['recommended_action'] = 'reduce_size'
                result['position_size_multiplier'] = 0.5
            else:
                result['recommended_action'] = 'skip'
                result['position_size_multiplier'] = 0.0

            logger.info(f"Trade quality for {symbol} {signal_action}: {score}/100 - {result['recommended_action']} ({processing_time:.0f}ms)")

            return result

        except Exception as e:
            logger.error(f"Error scoring trade quality: {e}")
            # Conservative fallback - reject trade
            return {
                'score': 30,
                'confidence': 0.0,
                'reasoning': f"Scoring error: {str(e)}",
                'risk_factors': ['LLM error'],
                'opportunity_factors': [],
                'recommended_action': 'skip',
                'position_size_multiplier': 0.0,
                'processing_time_ms': 0
            }

    def _build_regime_prompt(self, symbol: str, market_data: pd.DataFrame) -> str:
        """Build market regime detection prompt."""
        # Get last 100 bars
        recent = market_data.tail(100)

        # Calculate key metrics
        latest = recent.iloc[-1]
        price_change_20d = ((latest['close'] - recent.iloc[-20]['close']) / recent.iloc[-20]['close'] * 100)
        volatility_20d = recent['close'].pct_change().tail(20).std() * 100

        # Get ADX if available
        adx = latest.get('adx', 0)
        adx_str = f"{adx:.1f}" if isinstance(adx, (int, float)) else "N/A"

        # Get volume ratio
        vol_ratio = latest.get('volume_ratio', 1.0)
        vol_str = f"{vol_ratio:.2f}" if isinstance(vol_ratio, (int, float)) else "N/A"

        # Get recent price action
        price_range = f"${recent['low'].min():.2f} - ${recent['high'].max():.2f}"

        # Format RSI and MACD safely
        rsi_value = latest.get('rsi', 50)
        rsi_str = f"{rsi_value:.1f}" if isinstance(rsi_value, (int, float)) else "50.0"

        macd_value = latest.get('macd', 0)
        macd_str = f"{macd_value:.2f}" if isinstance(macd_value, (int, float)) else "0.00"

        ema_5 = latest.get('ema_5', 0)
        ema_21 = latest.get('ema_21', 0)
        ema_align = 'Bullish' if ema_5 > ema_21 else 'Bearish'

        return f"""Analyze the market regime for {symbol} for momentum breakout trading.

Recent Price Action (last 100 bars):
- Current: ${latest['close']:.2f}
- 20-bar change: {price_change_20d:+.2f}%
- 20-bar volatility: {volatility_20d:.2f}%
- ADX (trend strength): {adx_str}
- Range: {price_range}
- Volume ratio: {vol_str}x

Technical Context:
- RSI: {rsi_str}
- EMA alignment: {ema_align}
- MACD: {macd_str}

Classify the current market regime and determine if it's optimal for momentum breakout trading.

Momentum breakout works best in:
- Strong trending markets (ADX > 25)
- Clear directional moves
- High volume confirmation

Responds in JSON:
{{
    "regime": "strong_uptrend|weak_uptrend|strong_downtrend|weak_downtrend|ranging_tight|ranging_wide|high_volatility|low_volatility",
    "confidence": 0.0-1.0,
    "reasoning": "brief 1-sentence explanation",
    "key_characteristics": ["char1", "char2"],
    "optimal_for_momentum": true/false
}}"""

    def _build_scoring_prompt(
        self,
        symbol: str,
        action: str,
        reason: str,
        strength: float,
        market_data: Dict,
        indicators: Dict,
        recent_trades: Optional[List[Dict]]
    ) -> str:
        """Build trade quality scoring prompt."""
        # Format recent trades
        trade_summary = "None"
        if recent_trades:
            wins = sum(1 for t in recent_trades if t.get('pnl', 0) > 0)
            total = len(recent_trades)
            win_rate = wins / total * 100 if total > 0 else 0
            trade_summary = f"{wins}/{total} wins ({win_rate:.0f}% win rate)"

        return f"""Score this trade setup for {symbol} (0-100 scale).

Proposed Trade:
- Action: {action.upper()}
- Reason: {reason}
- Strategy Confidence: {strength:.2f}

Current Market:
- Price: ${market_data.get('close', 'N/A')}
- Volume: {market_data.get('volume_ratio', 1.0):.1f}x average
- Volatility: {market_data.get('atr_pct', 0):.2f}%
- RSI: {indicators.get('rsi', 50):.1f}
- Trend: {'Up' if indicators.get('adx', 0) > 25 else 'Weak/Ranging'}

Recent Performance:
- Last 5 trades on {symbol}: {trade_summary}

Score this trade 0-100 where:
- 90-100: Exceptional setup, high confidence
- 70-89: Good setup, execute
- 50-69: Marginal, reduce position
- 0-49: Poor setup, skip

Respond in JSON:
{{
    "score": 0-100,
    "confidence": 0.0-1.0,
    "reasoning": "1-sentence explanation",
    "risk_factors": ["factor1", "factor2"],
    "opportunity_factors": ["factor1", "factor2"]
}}"""

    def _query_llm_fast(self, prompt: str, max_tokens: int = 512) -> str:
        """Fast LLM query optimized for low latency."""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.1,  # Very low for consistency and speed
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text

        except Exception as e:
            logger.error(f"LLM query error: {e}")
            raise

    def _parse_regime_response(self, response: str) -> Dict:
        """Parse market regime response."""
        try:
            # Extract JSON
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(response[start:end])

                # Ensure all required fields
                return {
                    'regime': data.get('regime', 'ranging_tight'),
                    'confidence': float(data.get('confidence', 0.5)),
                    'reasoning': data.get('reasoning', 'No reasoning provided'),
                    'key_characteristics': data.get('key_characteristics', []),
                    'recommended_strategies': data.get('recommended_strategies', []),
                    'optimal_for_momentum': bool(data.get('optimal_for_momentum', False))
                }
            else:
                raise ValueError("No JSON found in response")

        except Exception as e:
            logger.warning(f"Failed to parse regime response: {e}")
            return {
                'regime': 'ranging_tight',
                'confidence': 0.0,
                'reasoning': 'Parse error',
                'key_characteristics': [],
                'recommended_strategies': [],
                'optimal_for_momentum': False
            }

    def _parse_scoring_response(self, response: str) -> Dict:
        """Parse trade scoring response."""
        try:
            # Extract JSON
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(response[start:end])

                return {
                    'score': int(data.get('score', 30)),
                    'confidence': float(data.get('confidence', 0.5)),
                    'reasoning': data.get('reasoning', 'No reasoning provided'),
                    'risk_factors': data.get('risk_factors', []),
                    'opportunity_factors': data.get('opportunity_factors', [])
                }
            else:
                raise ValueError("No JSON found in response")

        except Exception as e:
            logger.warning(f"Failed to parse scoring response: {e}")
            return {
                'score': 30,  # Conservative default
                'confidence': 0.0,
                'reasoning': 'Parse error',
                'risk_factors': ['Parse error'],
                'opportunity_factors': []
            }

    def get_performance_stats(self) -> Dict:
        """Get LLM service performance statistics."""
        avg_time = self.total_time_ms / self.total_calls if self.total_calls > 0 else 0
        return {
            'total_calls': self.total_calls,
            'total_time_ms': int(self.total_time_ms),
            'avg_time_ms': int(avg_time),
            'cached_regimes': len(self.regime_cache)
        }
