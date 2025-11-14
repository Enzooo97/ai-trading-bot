"""
LLM integration for advanced market analysis and decision support.
Uses Claude or GPT for contextual analysis and trade validation.
"""
from typing import Dict, Optional, List, Tuple
from datetime import datetime
import json
import logging
from decimal import Decimal
import anthropic
import openai
from sqlalchemy.orm import Session
from src.config import settings
from src.database.models import LLMAnalysis
from src.strategies.base_strategy import Signal

logger = logging.getLogger(__name__)


class LLMAnalyzer:
    """
    LLM-powered market analyzer for enhanced decision making.
    Provides contextual analysis beyond technical indicators.
    """

    def __init__(self, session: Session):
        """
        Initialize LLM analyzer.

        Args:
            session: Database session for logging analyses
        """
        self.session = session
        self.provider = settings.llm_provider

        # Initialize appropriate client
        if self.provider == "anthropic":
            self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            self.model = settings.llm_model
        elif self.provider == "openai":
            openai.api_key = settings.openai_api_key
            self.client = openai
            self.model = settings.llm_model or "gpt-4-turbo-preview"
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

        logger.info(f"LLM Analyzer initialized with {self.provider}")

    def analyze_market_conditions(
        self,
        symbol: str,
        market_data: Dict,
        technical_indicators: Dict,
        signal: Signal,
    ) -> Dict:
        """
        Get LLM analysis of market conditions and trade signal.

        Args:
            symbol: Stock symbol
            market_data: Current market data (price, volume, etc.)
            technical_indicators: Technical indicator values
            signal: Trading signal from strategy

        Returns:
            Dictionary with LLM analysis and recommendations
        """
        try:
            start_time = datetime.utcnow()

            # Build prompt
            prompt = self._build_analysis_prompt(
                symbol, market_data, technical_indicators, signal
            )

            # Get LLM response
            response = self._query_llm(prompt)

            # Parse response
            analysis = self._parse_llm_response(response)

            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Log to database
            self._log_analysis(
                symbol=symbol,
                analysis_type="market_analysis",
                prompt=prompt,
                response=response,
                market_context=json.dumps(market_data),
                action_taken=signal.action,
                processing_time_ms=int(processing_time),
            )

            logger.info(f"LLM analysis for {symbol}: {analysis.get('recommendation', 'N/A')}")

            return analysis

        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}")
            return {
                "recommendation": "hold",
                "confidence": 0.0,
                "reasoning": f"LLM analysis failed: {str(e)}",
                "risk_assessment": "unknown",
            }

    def validate_entry(
        self,
        symbol: str,
        signal: Signal,
        market_data: Dict,
        account_info: Dict,
    ) -> Tuple[bool, str, float]:
        """
        Validate trade entry using LLM reasoning.

        Args:
            symbol: Stock symbol
            signal: Trading signal
            market_data: Market data
            account_info: Account information

        Returns:
            Tuple of (should_enter, reason, confidence)
        """
        try:
            prompt = self._build_validation_prompt(symbol, signal, market_data, account_info)
            response = self._query_llm(prompt)
            analysis = self._parse_llm_response(response)

            # Log validation
            self._log_analysis(
                symbol=symbol,
                analysis_type="entry_decision",
                prompt=prompt,
                response=response,
                market_context=json.dumps(market_data),
                action_taken=signal.action,
            )

            should_enter = analysis.get("recommendation", "hold").lower() in ["buy", "sell"]
            reason = analysis.get("reasoning", "No clear reason provided")
            confidence = analysis.get("confidence", 0.5)

            return should_enter, reason, confidence

        except Exception as e:
            logger.error(f"Error validating entry: {e}")
            return False, f"Validation error: {e}", 0.0

    def _build_analysis_prompt(
        self,
        symbol: str,
        market_data: Dict,
        indicators: Dict,
        signal: Signal,
    ) -> str:
        """Build analysis prompt for LLM."""
        return f"""You are an expert day trader analyzing market conditions for aggressive scalping.

Symbol: {symbol}
Current Price: ${market_data.get('current_price', 'N/A')}
Signal: {signal.action.upper()} (strength: {signal.strength:.2f})
Signal Reason: {signal.reason}

Market Data:
- Volume: {market_data.get('volume', 'N/A')} (Avg: {market_data.get('avg_volume', 'N/A')})
- Volume Ratio: {market_data.get('volume_ratio', 'N/A'):.2f}x
- Volatility (ATR%): {market_data.get('atr_pct', 'N/A'):.2f}%
- Spread: Bid ${market_data.get('bid', 'N/A')} / Ask ${market_data.get('ask', 'N/A')}

Technical Indicators:
- RSI: {indicators.get('rsi', 'N/A'):.1f}
- MACD: {indicators.get('macd', 'N/A')}
- Trend: {indicators.get('trend', 'N/A')}
- Support: ${indicators.get('support', 'N/A')}
- Resistance: ${indicators.get('resistance', 'N/A')}

Trading Context:
- This is aggressive day trading with 2-4 hour hold times
- Target: 3-5% profit per trade
- Stop loss: 1.5-2%
- Can use up to 4x leverage if conditions are excellent

Analyze:
1. Is this signal valid given current market conditions?
2. What are the key risks and opportunities?
3. Should we take this trade? (buy/sell/hold)
4. Confidence level (0.0 to 1.0)
5. Risk assessment (low/medium/high)

Respond in JSON format:
{{
    "recommendation": "buy|sell|hold",
    "confidence": 0.0-1.0,
    "reasoning": "concise explanation",
    "risk_assessment": "low|medium|high",
    "key_factors": ["factor1", "factor2", ...],
    "suggested_position_size": "percentage of normal size (0.5 = half, 1.0 = normal, 1.5 = larger)"
}}"""

    def _build_validation_prompt(
        self,
        symbol: str,
        signal: Signal,
        market_data: Dict,
        account_info: Dict,
    ) -> str:
        """Build validation prompt."""
        return f"""Validate this trade entry for aggressive scalping:

Symbol: {symbol}
Proposed Action: {signal.action.upper()}
Signal Strength: {signal.strength:.2f}
Reason: {signal.reason}

Current Price: ${market_data.get('current_price', 'N/A')}
Account Equity: ${account_info.get('equity', 'N/A')}
Open Positions: {account_info.get('open_positions', 0)}

Market Context:
- Volume activity: {market_data.get('volume_ratio', 1.0):.1f}x average
- Volatility: {market_data.get('atr_pct', 0):.2f}%
- Market hours: {market_data.get('market_hours', 'unknown')}

Should we enter this trade?
- Consider: timing, market conditions, risk/reward, current exposure
- This is for scalping (quick in/out, 2-4 hours max)
- Need high probability setups only

Respond in JSON:
{{
    "recommendation": "buy|sell|hold",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}"""

    def _query_llm(self, prompt: str) -> str:
        """Query the configured LLM."""
        try:
            if self.provider == "anthropic":
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    temperature=0.3,  # Lower temperature for consistency
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return message.content[0].text

            elif self.provider == "openai":
                response = self.client.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert day trader."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1024,
                )
                return response.choices[0].message.content

        except Exception as e:
            logger.error(f"LLM query error: {e}")
            raise

    def _parse_llm_response(self, response: str) -> Dict:
        """Parse LLM JSON response."""
        try:
            # Try to extract JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1

            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                # Fallback if no JSON found
                return {
                    "recommendation": "hold",
                    "confidence": 0.5,
                    "reasoning": response[:200],  # First 200 chars
                    "risk_assessment": "medium",
                }

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM JSON: {e}")
            return {
                "recommendation": "hold",
                "confidence": 0.5,
                "reasoning": "Failed to parse LLM response",
                "risk_assessment": "high",
            }

    def _log_analysis(
        self,
        symbol: str,
        analysis_type: str,
        prompt: str,
        response: str,
        market_context: Optional[str] = None,
        action_taken: Optional[str] = None,
        processing_time_ms: Optional[int] = None,
    ):
        """Log LLM analysis to database."""
        try:
            analysis = LLMAnalysis(
                timestamp=datetime.utcnow(),
                symbol=symbol,
                analysis_type=analysis_type,
                prompt=prompt,
                llm_provider=self.provider,
                llm_model=self.model,
                response=response,
                market_context=market_context,
                action_taken=action_taken,
                processing_time_ms=processing_time_ms,
            )
            self.session.add(analysis)
            self.session.commit()

        except Exception as e:
            logger.error(f"Error logging LLM analysis: {e}")
            self.session.rollback()
