#!/usr/bin/env python3
"""
Paper Trading Configuration for £3,000 Capital

Optimized settings for realistic capital deployment with conservative risk management.
"""

# CAPITAL CONFIGURATION
INITIAL_CAPITAL = 3000.00  # £3,000 realistic trading capital
CURRENCY = "USD"  # Alpaca uses USD, but equivalent to £3,000

# POSITION SIZING (Conservative for small account)
MAX_POSITION_SIZE_PCT = 0.10          # Max 10% per position (£300 per trade)
MAX_POSITION_SIZE_DOLLARS = 300.00    # Hard cap at £300 per position
MIN_POSITION_SIZE_DOLLARS = 50.00     # Minimum £50 per position
MAX_CONCURRENT_POSITIONS = 3          # Max 3 positions (30% total exposure)

# RISK MANAGEMENT (Conservative for small account)
STOP_LOSS_PCT = 0.02                  # 2% stop loss (£6 max loss per trade)
TAKE_PROFIT_PCT = 0.04                # 4% take profit (£12 target per trade)
TRAILING_STOP_PCT = 0.015             # 1.5% trailing stop

# DAILY LIMITS (Protect capital)
MAX_DAILY_LOSS_PCT = 0.03             # Stop trading if -3% daily loss (-£90)
MAX_DAILY_LOSS_DOLLARS = 90.00        # Hard cap: -£90 max loss per day
DAILY_PROFIT_TARGET_PCT = 0.02        # 2% daily target (£60) - optional stop
DAILY_PROFIT_TARGET_DOLLARS = 60.00   # £60 daily target

# STRATEGY SELECTION
USE_BASE_STRATEGY = True              # Use base Momentum Breakout (NO LLM)
USE_LLM_ENHANCEMENT = False           # Disable LLM for 180+ day consistency

# TRADING SCHEDULE (London Time)
TRADING_START_TIME = "14:25"          # 9:25 AM ET (5 min before market open)
TRADING_END_TIME = "20:55"            # 3:55 PM ET (5 min before market close)
TIMEZONE = "Europe/London"

# SYMBOL UNIVERSE (Blue chip stocks for conservative trading)
SYMBOLS = [
    "AAPL",   # Apple - high liquidity
    "MSFT",   # Microsoft - high liquidity
    "GOOGL",  # Google - tested in backtests
    "TSLA",   # Tesla - higher volatility but tested
    "NVDA",   # Nvidia - tested in backtests
]

# TECHNICAL INDICATORS (Momentum Breakout parameters)
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

ATR_PERIOD = 14
ATR_PCT_THRESHOLD = 0.015            # 1.5% volatility minimum

VOLUME_THRESHOLD = 1.5               # Volume must be 1.5x average
MIN_VOLUME_ABSOLUTE = 500000         # Minimum 500k daily volume

# MONITORING & ALERTS
ENABLE_PERFORMANCE_LOGGING = True
LOG_LEVEL = "INFO"
PERFORMANCE_CHECK_INTERVAL_MINUTES = 60  # Check performance every hour

# SAFETY FEATURES
ENABLE_DAILY_LOSS_LIMIT = True       # Auto-stop on daily loss limit
ENABLE_POSITION_LIMITS = True        # Enforce max positions
ENABLE_ACCOUNT_PROTECTION = True     # Don't trade if account < £2,700 (10% loss)
MIN_ACCOUNT_BALANCE = 2700.00        # Stop trading if equity falls below this

# REALISTIC TARGETS (Monthly, not daily!)
MONTHLY_TARGET_PCT = 0.015           # 1.5% monthly target (realistic)
MONTHLY_TARGET_DOLLARS = 45.00       # £45 per month
ANNUAL_TARGET_PCT = 0.12             # 12% annual target (with base strategy)

# BACKTESTING VALIDATION
BACKTEST_PROVEN_RETURN_180D = 0.0411  # +4.11% over 180 days
BACKTEST_WIN_RATE = 0.523             # 52.3% win rate
BACKTEST_SHARPE_RATIO = 1.62          # Sharpe ratio 1.62

print(f"""
{'='*70}
PAPER TRADING CONFIGURATION SUMMARY
{'='*70}

CAPITAL:
  Starting Capital:    £{INITIAL_CAPITAL:,.2f}
  Max Per Position:    £{MAX_POSITION_SIZE_DOLLARS:,.2f} ({MAX_POSITION_SIZE_PCT*100:.0f}%)
  Max Positions:       {MAX_CONCURRENT_POSITIONS}
  Total Max Exposure:  £{MAX_POSITION_SIZE_DOLLARS * MAX_CONCURRENT_POSITIONS:,.2f}

RISK MANAGEMENT:
  Stop Loss:           {STOP_LOSS_PCT*100:.1f}% (£{INITIAL_CAPITAL * STOP_LOSS_PCT:.2f} per trade)
  Take Profit:         {TAKE_PROFIT_PCT*100:.1f}% (£{INITIAL_CAPITAL * TAKE_PROFIT_PCT:.2f} per trade)
  Daily Loss Limit:    -{MAX_DAILY_LOSS_DOLLARS:.0f} ({MAX_DAILY_LOSS_PCT*100:.0f}%)
  Min Account Balance: £{MIN_ACCOUNT_BALANCE:,.2f}

STRATEGY:
  Type:                Momentum Breakout (Base - NO LLM)
  Reason:              Proven +4.11% over 180 days
  Win Rate:            52.3% (from backtests)
  Sharpe Ratio:        1.62

TARGETS (REALISTIC):
  Daily Target:        £{DAILY_PROFIT_TARGET_DOLLARS:.2f} ({DAILY_PROFIT_TARGET_PCT*100:.1f}%)
  Monthly Target:      £{MONTHLY_TARGET_DOLLARS:.2f} ({MONTHLY_TARGET_PCT*100:.1f}%)
  Annual Target:       £{INITIAL_CAPITAL * ANNUAL_TARGET_PCT:.2f} ({ANNUAL_TARGET_PCT*100:.0f}%)

SYMBOLS:
  Trading Universe:    {', '.join(SYMBOLS)}
  Count:               {len(SYMBOLS)} stocks

SCHEDULE:
  Trading Hours:       {TRADING_START_TIME} - {TRADING_END_TIME} {TIMEZONE}
  Market Hours:        9:30 AM - 4:00 PM ET

SAFETY:
  Daily Loss Limit:    {'ENABLED' if ENABLE_DAILY_LOSS_LIMIT else 'DISABLED'}
  Position Limits:     {'ENABLED' if ENABLE_POSITION_LIMITS else 'DISABLED'}
  Account Protection:  {'ENABLED' if ENABLE_ACCOUNT_PROTECTION else 'DISABLED'}

{'='*70}

IMPORTANT REMINDERS:
  1. This is PAPER TRADING - no real money at risk
  2. Monitor for 30 days before considering live trading
  3. Target 1.5% MONTHLY, not daily!
  4. Base strategy (no LLM) is recommended for consistency
  5. Check performance daily at end of trading session

{'='*70}
""")
