#!/usr/bin/env python3
"""
Paper Trading Deployment Script

Runs the trading bot in paper trading mode with £3,000 capital configuration.
Uses base Momentum Breakout strategy (NO LLM) for consistent 180+ day performance.
"""
import sys
from pathlib import Path
from datetime import datetime
import time
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils import setup_logging
from src.data_pipeline import alpaca_client
from src.strategies.momentum_breakout_strategy import MomentumBreakoutStrategy
from src.risk_management import RiskManager
from src.order_execution import OrderExecutor
from src.database import db, TradingSession
import config_paper_trading as config

import logging
logger = logging.getLogger(__name__)


class PaperTradingBot:
    """Paper trading bot with conservative risk management for £3,000 capital."""

    def __init__(self):
        """Initialize paper trading bot."""
        self.strategy = MomentumBreakoutStrategy()
        self.risk_manager = RiskManager(
            max_position_size_pct=config.MAX_POSITION_SIZE_PCT,
            max_positions=config.MAX_CONCURRENT_POSITIONS,
            stop_loss_pct=config.STOP_LOSS_PCT,
            take_profit_pct=config.TAKE_PROFIT_PCT,
        )
        self.order_executor = OrderExecutor()

        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.session_start_equity = 0.0
        self.is_trading_day_stopped = False

        logger.info("Paper Trading Bot initialized")
        logger.info(f"Strategy: {self.strategy.name}")
        logger.info(f"Capital: £{config.INITIAL_CAPITAL:,.2f}")
        logger.info(f"Max position size: £{config.MAX_POSITION_SIZE_DOLLARS:,.2f}")

    def check_account_health(self) -> bool:
        """Check if account is healthy enough to continue trading."""
        try:
            account = alpaca_client.get_account()
            equity = float(account['equity'])

            # Check minimum balance
            if equity < config.MIN_ACCOUNT_BALANCE:
                logger.error(f"Account equity (£{equity:.2f}) below minimum (£{config.MIN_ACCOUNT_BALANCE:.2f})")
                logger.error("STOPPING TRADING - Account protection triggered")
                return False

            # Check daily loss limit
            daily_loss = equity - self.session_start_equity
            daily_loss_pct = (daily_loss / self.session_start_equity) if self.session_start_equity > 0 else 0

            if config.ENABLE_DAILY_LOSS_LIMIT:
                if daily_loss < -config.MAX_DAILY_LOSS_DOLLARS:
                    logger.warning(f"Daily loss limit hit: -£{abs(daily_loss):.2f}")
                    logger.warning("STOPPING TRADING for today")
                    self.is_trading_day_stopped = True
                    return False

                if daily_loss_pct < -config.MAX_DAILY_LOSS_PCT:
                    logger.warning(f"Daily loss % limit hit: {daily_loss_pct*100:.2f}%")
                    logger.warning("STOPPING TRADING for today")
                    self.is_trading_day_stopped = True
                    return False

            # Check daily profit target (optional stop)
            if daily_loss > config.DAILY_PROFIT_TARGET_DOLLARS:
                logger.info(f"Daily profit target reached: +£{daily_loss:.2f}")
                logger.info("Consider stopping for the day (target achieved)")

            return True

        except Exception as e:
            logger.error(f"Error checking account health: {e}")
            return False

    def scan_and_trade(self):
        """Scan symbols and execute trades based on strategy signals."""
        if self.is_trading_day_stopped:
            logger.debug("Trading stopped for the day - skipping scan")
            return

        try:
            # Get account info
            account = alpaca_client.get_account()
            current_positions = alpaca_client.get_positions()

            # Check position limit
            if len(current_positions) >= config.MAX_CONCURRENT_POSITIONS:
                logger.debug(f"Max positions ({config.MAX_CONCURRENT_POSITIONS}) reached - no new entries")
                return

            # Scan each symbol
            for symbol in config.SYMBOLS:
                try:
                    # Get market data
                    bars = alpaca_client.get_bars(
                        symbols=[symbol],
                        timeframe="5Min",
                        limit=100
                    )

                    if symbol not in bars or bars[symbol].empty:
                        logger.debug(f"No data for {symbol}")
                        continue

                    # Analyze with strategy
                    signal = self.strategy.analyze(
                        symbol=symbol,
                        data=bars[symbol],
                        account_info=account,
                        current_positions=current_positions
                    )

                    if signal.action == "hold":
                        continue

                    # Calculate position size
                    position_size = self.risk_manager.calculate_position_size(
                        capital=float(account['buying_power']),
                        signal_strength=signal.strength,
                        current_price=float(bars[symbol]['close'].iloc[-1])
                    )

                    # Enforce hard caps
                    max_shares = int(config.MAX_POSITION_SIZE_DOLLARS / float(bars[symbol]['close'].iloc[-1]))
                    min_shares = int(config.MIN_POSITION_SIZE_DOLLARS / float(bars[symbol]['close'].iloc[-1]))

                    position_size = max(min_shares, min(position_size, max_shares))

                    if position_size < min_shares:
                        logger.debug(f"Position size too small for {symbol}")
                        continue

                    # Execute trade
                    logger.info(f"SIGNAL: {signal.action.upper()} {symbol} ({position_size} shares)")
                    logger.info(f"Reason: {signal.reason}")

                    order = self.order_executor.place_market_order(
                        symbol=symbol,
                        side=signal.action,
                        qty=position_size,
                        stop_loss_pct=config.STOP_LOSS_PCT,
                        take_profit_pct=config.TAKE_PROFIT_PCT
                    )

                    if order:
                        self.daily_trades += 1
                        logger.info(f"Order placed: {order['id']}")
                    else:
                        logger.warning(f"Order failed for {symbol}")

                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error in scan_and_trade: {e}")

    def monitor_positions(self):
        """Monitor and manage open positions."""
        try:
            positions = alpaca_client.get_positions()

            for position in positions:
                symbol = position['symbol']
                unrealized_pl = float(position['unrealized_pl'])
                unrealized_plpc = float(position['unrealized_plpc'])

                logger.debug(f"{symbol}: P&L £{unrealized_pl:.2f} ({unrealized_plpc*100:.2f}%)")

                # Check if we should close position
                # (stop loss and take profit are handled by Alpaca bracket orders)

        except Exception as e:
            logger.error(f"Error monitoring positions: {e}")

    def log_daily_summary(self):
        """Log daily performance summary."""
        try:
            account = alpaca_client.get_account()
            equity = float(account['equity'])
            daily_pnl = equity - self.session_start_equity
            daily_pnl_pct = (daily_pnl / self.session_start_equity * 100) if self.session_start_equity > 0 else 0

            logger.info("="*70)
            logger.info("DAILY SUMMARY")
            logger.info("="*70)
            logger.info(f"Starting Equity:  £{self.session_start_equity:,.2f}")
            logger.info(f"Ending Equity:    £{equity:,.2f}")
            logger.info(f"Daily P&L:        £{daily_pnl:+.2f} ({daily_pnl_pct:+.2f}%)")
            logger.info(f"Trades Executed:  {self.daily_trades}")
            logger.info(f"Target (daily):   £{config.DAILY_PROFIT_TARGET_DOLLARS:.2f}")
            logger.info(f"Target (monthly): £{config.MONTHLY_TARGET_DOLLARS:.2f}")
            logger.info("="*70)

        except Exception as e:
            logger.error(f"Error logging daily summary: {e}")

    def run(self):
        """Run paper trading bot."""
        setup_logging()

        print("\n" + "="*70)
        print("PAPER TRADING BOT - STARTING")
        print("="*70)

        # Verify account
        try:
            account = alpaca_client.get_account()
            equity = float(account['equity'])
            cash = float(account['cash'])

            print(f"\nAccount Status:")
            print(f"  Equity:        £{equity:,.2f}")
            print(f"  Cash:          £{cash:,.2f}")
            print(f"  Buying Power:  £{float(account['buying_power']):,.2f}")
            print(f"  PDT:           {account.get('pattern_day_trader', False)}")

            self.session_start_equity = equity

            if equity < config.MIN_ACCOUNT_BALANCE:
                print(f"\n[ERROR] Account equity (£{equity:.2f}) below minimum (£{config.MIN_ACCOUNT_BALANCE:.2f})")
                print("Cannot start trading - account protection")
                return

        except Exception as e:
            print(f"\n[ERROR] Failed to connect to Alpaca: {e}")
            logger.error(f"Failed to connect to Alpaca: {e}")
            return

        print(f"\nStrategy:        {self.strategy.name}")
        print(f"Symbols:         {', '.join(config.SYMBOLS)}")
        print(f"Trading Hours:   {config.TRADING_START_TIME} - {config.TRADING_END_TIME} {config.TIMEZONE}")
        print(f"Scan Interval:   60 seconds")
        print("\n" + "="*70)
        print("Bot is running... Press Ctrl+C to stop")
        print("="*70 + "\n")

        logger.info("Paper trading bot started")

        try:
            iteration = 0
            while True:
                iteration += 1

                # Check account health
                if not self.check_account_health():
                    logger.error("Account health check failed - stopping bot")
                    break

                # Scan and trade
                logger.info(f"Scan #{iteration}")
                self.scan_and_trade()

                # Monitor positions
                self.monitor_positions()

                # Log performance every hour
                if iteration % 60 == 0:
                    self.log_daily_summary()

                # Wait for next scan
                time.sleep(60)  # Scan every 60 seconds

        except KeyboardInterrupt:
            print("\n\nBot stopped by user")
            logger.info("Bot stopped by user")
            self.log_daily_summary()

        except Exception as e:
            print(f"\n[ERROR] Bot crashed: {e}")
            logger.error(f"Bot crashed: {e}", exc_info=True)
            self.log_daily_summary()


if __name__ == "__main__":
    # Display configuration
    import config_paper_trading
    # (config prints its summary on import)

    # Confirm before starting
    print("\nReady to start paper trading?")
    print("  - Base Momentum Breakout strategy (NO LLM)")
    print("  - £3,000 capital")
    print("  - Conservative risk management")
    print("  - 30-day monitoring recommended")
    print("\nPress Enter to continue, or Ctrl+C to cancel...")

    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled by user")
        sys.exit(0)

    # Run bot
    bot = PaperTradingBot()
    bot.run()
