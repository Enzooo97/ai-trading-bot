"""
Main trading bot orchestrator.
Coordinates all components: strategies, risk management, order execution, LLM analysis.
"""
import logging
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
import pandas as pd

from src.config import settings
from src.database import db, TradingSession, Position, PositionStatus
from src.data_pipeline import alpaca_client
from src.strategies import (
    MomentumBreakoutStrategy, MeanReversionStrategy,
    VWAPStrategy, EMATripleCrossoverStrategy, StochasticRSIStrategy,
    Signal
)
from src.risk_management import RiskManager
from src.order_execution import OrderExecutor
from src.llm_integration import LLMAnalyzer
from src.utils import setup_logging, TradingScheduler

logger = logging.getLogger(__name__)


class TradingBot:
    """
    Main trading bot that orchestrates all trading activities.
    Implements aggressive scalping strategy with LLM-enhanced decision making.
    """

    def __init__(self):
        """Initialize trading bot."""
        self.session: Optional[Session] = None
        self.current_session: Optional[TradingSession] = None
        self.strategies = []
        self.risk_manager: Optional[RiskManager] = None
        self.order_executor: Optional[OrderExecutor] = None
        self.llm_analyzer: Optional[LLMAnalyzer] = None
        self.scheduler: Optional[TradingScheduler] = None
        self.is_running = False
        self.use_llm = True  # Enable/disable LLM analysis

    def initialize(self):
        """Initialize all bot components."""
        try:
            logger.info("Initializing trading bot...")

            # Setup database
            db.create_tables()

            # Get database session
            self.session = db.get_session()

            # Initialize components
            self.risk_manager = RiskManager(self.session)
            self.order_executor = OrderExecutor(self.session)

            # Initialize LLM analyzer (if API keys provided)
            if settings.anthropic_api_key or settings.openai_api_key:
                self.llm_analyzer = LLMAnalyzer(self.session)
                logger.info("LLM analyzer initialized")
            else:
                logger.warning("No LLM API keys provided - LLM analysis disabled")
                self.use_llm = False

            # Initialize strategies (research-optimized for aggressive scalping)
            self.strategies = [
                VWAPStrategy(),                    # Institutional anchor (60-65% win rate)
                EMATripleCrossoverStrategy(),      # Fast momentum (55-62% win rate)
                MomentumBreakoutStrategy(),        # Trend continuation (existing)
                StochasticRSIStrategy(),           # Extreme reversals (58-63% win rate)
                MeanReversionStrategy(),           # Mean reversion (existing)
            ]
            logger.info(f"Loaded {len(self.strategies)} trading strategies (research-optimized)")

            # Initialize scheduler
            self.scheduler = TradingScheduler(
                start_callback=self.start_trading,
                stop_callback=self.stop_trading,
            )
            self.scheduler.setup_schedule()

            logger.info("Trading bot initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing bot: {e}")
            raise

    def start(self):
        """Start the trading bot with scheduler."""
        try:
            logger.info("=" * 60)
            logger.info("TRADING BOT STARTING")
            logger.info("=" * 60)

            # Initialize if not already done
            if not self.session:
                self.initialize()

            # Start scheduler
            self.scheduler.start()

            # Log schedule info
            schedule_info = self.scheduler.get_next_run_times()
            logger.info(f"Next trading session start: {schedule_info.get('next_start')}")
            logger.info(f"Next trading session stop: {schedule_info.get('next_stop')}")

            logger.info("Bot is running - press Ctrl+C to stop")

            # Keep running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Shutdown signal received")
                self.shutdown()

        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise

    def start_trading(self):
        """Start active trading session."""
        try:
            logger.info("Starting trading session...")

            # Get account info
            account_info = alpaca_client.get_account()
            starting_equity = account_info['equity']

            logger.info(f"Starting equity: ${starting_equity}")

            # Create trading session
            self.current_session = TradingSession(
                session_date=datetime.utcnow().date(),
                start_time=datetime.utcnow(),
                starting_equity=starting_equity,
                is_active=True,
            )
            self.session.add(self.current_session)
            self.session.commit()

            self.is_running = True

            # Start trading loop
            self._trading_loop()

        except Exception as e:
            logger.error(f"Error starting trading: {e}")
            self.is_running = False

    def stop_trading(self):
        """Stop active trading session."""
        try:
            logger.info("Stopping trading session...")

            self.is_running = False

            if self.current_session:
                # Close all open positions
                self._close_all_positions("Trading session ended")

                # Get final account info
                account_info = alpaca_client.get_account()
                ending_equity = account_info['equity']

                # Update session
                self.current_session.end_time = datetime.utcnow()
                self.current_session.ending_equity = ending_equity
                self.current_session.pnl = ending_equity - self.current_session.starting_equity
                self.current_session.pnl_pct = float(
                    self.current_session.pnl / self.current_session.starting_equity
                )
                self.current_session.is_active = False

                self.session.commit()

                # Log session results
                self._log_session_summary()

            logger.info("Trading session stopped")

        except Exception as e:
            logger.error(f"Error stopping trading: {e}")

    def _trading_loop(self):
        """Main trading loop - runs continuously during trading hours."""
        logger.info("Entering main trading loop...")

        iteration = 0
        while self.is_running:
            try:
                iteration += 1
                logger.debug(f"Trading loop iteration {iteration}")

                # Update existing positions
                self.order_executor.update_positions(self.current_session)

                # Check daily profit/loss limits
                if self._check_daily_limits():
                    logger.warning("Daily limits reached - stopping trading")
                    self.stop_trading()
                    break

                # Scan for new opportunities
                self._scan_opportunities()

                # Wait before next iteration (1 minute for scalping)
                time.sleep(60)

            except KeyboardInterrupt:
                logger.info("Trading loop interrupted")
                break
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                time.sleep(10)  # Brief pause on error

        logger.info("Exiting trading loop")

    def _scan_opportunities(self):
        """Scan symbols for trading opportunities."""
        try:
            # Get current account info
            account_info = alpaca_client.get_account()

            # Get current positions
            current_positions = alpaca_client.get_positions()

            # Sample of symbols to scan (rotate through universe)
            # In production, you'd scan all symbols or use a more sophisticated selection
            symbols_to_scan = settings.symbol_universe[:20]  # Top 20 for quick scanning

            logger.info(f"Scanning {len(symbols_to_scan)} symbols for opportunities...")

            for symbol in symbols_to_scan:
                try:
                    self._analyze_symbol(symbol, account_info, current_positions)
                except Exception as e:
                    logger.error(f"Error analyzing {symbol}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error scanning opportunities: {e}")

    def _analyze_symbol(
        self,
        symbol: str,
        account_info: Dict,
        current_positions: List[Dict],
    ):
        """Analyze a single symbol and execute trades if signals are strong."""
        try:
            # Check if already have position
            has_position = any(p['symbol'] == symbol for p in current_positions)

            # Get historical data (5-minute bars for scalping)
            bars_data = alpaca_client.get_bars(
                symbols=[symbol],
                timeframe="5Min",
                limit=100,
            )

            if symbol not in bars_data or bars_data[symbol].empty:
                return

            data = bars_data[symbol]

            # Run all strategies
            signals = []
            for strategy in self.strategies:
                signal = strategy.analyze(
                    symbol=symbol,
                    data=data,
                    account_info=account_info,
                    current_positions=current_positions,
                )
                signal.metadata['strategy_name'] = strategy.name
                signals.append(signal)

            # Get strongest signal
            best_signal = max(signals, key=lambda s: s.strength)

            # Log signal
            logger.debug(
                f"{symbol}: {best_signal.action} "
                f"(strength: {best_signal.strength:.2f}) - {best_signal.reason}"
            )

            # Only proceed with strong signals
            if best_signal.strength < 0.7:
                return

            # For entry signals, validate with LLM if enabled
            if best_signal.action in ["buy", "sell"] and not has_position:
                if self.use_llm and self.llm_analyzer:
                    # Get latest market data
                    latest_bar = alpaca_client.get_latest_bar(symbol)
                    latest_quote = alpaca_client.get_latest_quote(symbol)

                    market_data = {
                        "symbol": symbol,
                        "current_price": float(latest_bar['close']),
                        "volume": int(latest_bar['volume']),
                        "bid": float(latest_quote['bid_price']),
                        "ask": float(latest_quote['ask_price']),
                    }

                    # Get LLM validation
                    should_enter, llm_reason, llm_confidence = self.llm_analyzer.validate_entry(
                        symbol=symbol,
                        signal=best_signal,
                        market_data=market_data,
                        account_info=account_info,
                    )

                    if not should_enter:
                        logger.info(f"LLM rejected {symbol} entry: {llm_reason}")
                        return

                    # Adjust signal strength based on LLM confidence
                    best_signal.strength = (best_signal.strength + llm_confidence) / 2

                # Execute trade
                logger.info(f"Executing {best_signal.action.upper()} for {symbol}")

                # Determine if leverage should be used (only for very strong signals)
                use_leverage = best_signal.strength > 0.85

                position = self.order_executor.execute_signal(
                    symbol=symbol,
                    signal=best_signal,
                    account_info=account_info,
                    current_session=self.current_session,
                    use_leverage=use_leverage,
                )

                if position:
                    logger.info(f"Position opened successfully for {symbol}")
                else:
                    logger.warning(f"Failed to open position for {symbol}")

            # For close signals
            elif best_signal.action == "close" and has_position:
                position = self.session.query(Position).filter(
                    Position.symbol == symbol,
                    Position.status == PositionStatus.OPEN,
                ).first()

                if position:
                    logger.info(f"Closing position for {symbol}: {best_signal.reason}")
                    self.order_executor.close_position(
                        position=position,
                        reason=best_signal.reason,
                        current_session=self.current_session,
                    )

        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")

    def _check_daily_limits(self) -> bool:
        """Check if daily profit/loss limits are reached."""
        if not self.current_session:
            return False

        # Check profit target
        if self.current_session.pnl_pct and self.current_session.pnl_pct >= settings.daily_profit_target:
            logger.info(
                f"Daily profit target reached: "
                f"{self.current_session.pnl_pct*100:.2f}% >= "
                f"{settings.daily_profit_target*100:.2f}%"
            )
            return True

        # Check loss limit
        if self.current_session.pnl_pct and self.current_session.pnl_pct <= settings.max_daily_loss:
            logger.warning(
                f"Daily loss limit reached: "
                f"{self.current_session.pnl_pct*100:.2f}% <= "
                f"{settings.max_daily_loss*100:.2f}%"
            )
            return True

        return False

    def _close_all_positions(self, reason: str):
        """Close all open positions."""
        try:
            open_positions = self.session.query(Position).filter(
                Position.status == PositionStatus.OPEN
            ).all()

            logger.info(f"Closing {len(open_positions)} open positions...")

            for position in open_positions:
                self.order_executor.close_position(
                    position=position,
                    reason=reason,
                    current_session=self.current_session,
                )

            # Also close via Alpaca to ensure cleanup
            alpaca_client.close_all_positions()

        except Exception as e:
            logger.error(f"Error closing all positions: {e}")

    def _log_session_summary(self):
        """Log trading session summary."""
        if not self.current_session:
            return

        logger.info("=" * 60)
        logger.info("TRADING SESSION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Start Time: {self.current_session.start_time}")
        logger.info(f"End Time: {self.current_session.end_time}")
        logger.info(f"Starting Equity: ${self.current_session.starting_equity:,.2f}")
        logger.info(f"Ending Equity: ${self.current_session.ending_equity:,.2f}")
        logger.info(f"P&L: ${self.current_session.pnl:,.2f} ({self.current_session.pnl_pct*100:.2f}%)")
        logger.info(f"Total Trades: {self.current_session.total_trades}")
        logger.info(f"Winning Trades: {self.current_session.winning_trades}")
        logger.info(f"Losing Trades: {self.current_session.losing_trades}")

        if self.current_session.total_trades > 0:
            win_rate = self.current_session.winning_trades / self.current_session.total_trades
            logger.info(f"Win Rate: {win_rate*100:.1f}%")

        logger.info("=" * 60)

    def shutdown(self):
        """Gracefully shutdown the bot."""
        try:
            logger.info("Shutting down trading bot...")

            # Stop trading if active
            if self.is_running:
                self.stop_trading()

            # Stop scheduler
            if self.scheduler:
                self.scheduler.stop()

            # Close database session
            if self.session:
                self.session.close()

            logger.info("Bot shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


def main():
    """Main entry point."""
    # Setup logging
    setup_logging()

    # Create and start bot
    bot = TradingBot()
    bot.start()


if __name__ == "__main__":
    main()
