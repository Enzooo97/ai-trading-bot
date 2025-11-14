# Trading Bot Setup Guide

Complete step-by-step guide to get your aggressive scalping bot running.

## Prerequisites

- Python 3.10 or higher
- Alpaca Premium account (recommended for better data)
- Anthropic or OpenAI API key (for LLM analysis)
- Windows/Linux/Mac OS

## Step 1: Alpaca Setup

### Create Alpaca Account

1. Visit [alpaca.markets](https://alpaca.markets)
2. Sign up for a paper trading account (free)
3. Optionally upgrade to premium for better data feeds

### Get API Keys

1. Log into Alpaca dashboard
2. Navigate to "API Keys" section
3. Generate new API keys
4. **Save both API Key and Secret Key** securely

## Step 2: LLM API Setup

Choose one or both:

### Option A: Anthropic Claude

1. Visit [console.anthropic.com](https://console.anthropic.com)
2. Create account and add payment method
3. Generate API key from dashboard
4. Copy API key

### Option B: OpenAI GPT

1. Visit [platform.openai.com](https://platform.openai.com)
2. Create account and add payment method
3. Generate API key from API keys section
4. Copy API key

## Step 3: Install Python Environment

### Windows

```powershell
# Check Python version
python --version  # Should be 3.10+

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip
```

### Linux/Mac

```bash
# Check Python version
python3 --version  # Should be 3.10+

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

## Step 4: Install Dependencies

### Install TA-Lib (Technical Analysis Library)

#### Windows
```powershell
# Download TA-Lib wheel from:
# https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
# Choose appropriate version for your Python

# Install wheel
pip install TA_Lib‑0.4.XX‑cpXX‑cpXX‑win_amd64.whl
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install ta-lib
sudo apt-get install python3-dev

pip install TA-Lib
```

#### Mac
```bash
brew install ta-lib

pip install TA-Lib
```

### Install Python Packages

```bash
# Install all required packages
pip install -r requirements.txt

# Verify installation
python -c "import alpaca; import anthropic; import pandas_ta; print('All packages installed!')"
```

## Step 5: Configure Environment

### Create .env File

```bash
# Copy example file
cp .env.example .env

# Edit with your favorite editor
nano .env
# or
code .env
```

### Required Configuration

```bash
# Alpaca (REQUIRED)
ALPACA_API_KEY=YOUR_ALPACA_API_KEY_HERE
ALPACA_SECRET_KEY=YOUR_ALPACA_SECRET_KEY_HERE
ALPACA_BASE_URL=https://paper-api.alpaca.markets  # Paper trading

# LLM - Choose one (REQUIRED for LLM features)
ANTHROPIC_API_KEY=YOUR_ANTHROPIC_KEY_HERE
# OR
OPENAI_API_KEY=YOUR_OPENAI_KEY_HERE

# Database (Optional - defaults to SQLite)
DATABASE_URL=sqlite:///./trading_bot.db

# Trading Configuration (Optional - has defaults)
MAX_POSITION_SIZE_PCT=0.15
MAX_LEVERAGE=4.0
DAILY_PROFIT_TARGET=0.05
MAX_DAILY_LOSS=-0.03
```

### Optional: Advanced Configuration

```bash
# Risk Management
STOP_LOSS_PCT=0.02
TAKE_PROFIT_PCT=0.04
TRAILING_STOP_PCT=0.015
MAX_CONCURRENT_POSITIONS=10

# Schedule (London time)
TRADING_START_TIME=14:25
TRADING_END_TIME=21:05
TIMEZONE=Europe/London

# Strategy Parameters
RSI_OVERSOLD=30
RSI_OVERBOUGHT=70
BOLLINGER_PERIOD=20
```

## Step 6: Initialize Database

```bash
# Initialize database tables
python -c "from src.database import init_database; init_database()"
```

## Step 7: Test Configuration

### Verify Alpaca Connection

```python
# test_alpaca.py
from src.config import settings
from src.data_pipeline import alpaca_client

# Get account info
account = alpaca_client.get_account()
print(f"Account Status: OK")
print(f"Equity: ${account['equity']}")
print(f"Buying Power: ${account['buying_power']}")
```

Run:
```bash
python test_alpaca.py
```

### Verify LLM Connection

```python
# test_llm.py
from src.config import settings

if settings.anthropic_api_key:
    import anthropic
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print("Anthropic API: OK")

if settings.openai_api_key:
    import openai
    openai.api_key = settings.openai_api_key
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo-preview",
        messages=[{"role": "user", "content": "Hello!"}],
        max_tokens=100
    )
    print("OpenAI API: OK")
```

Run:
```bash
python test_llm.py
```

## Step 8: First Run (Dry Run)

### Test Bot Without Trading

```python
# Edit src/trading_bot.py temporarily
# Change line in _scan_opportunities():
# symbols_to_scan = settings.symbol_universe[:1]  # Only scan 1 symbol

# Run bot
python main.py
```

**Watch for:**
- ✅ "Trading bot initialized successfully"
- ✅ "LLM analyzer initialized"
- ✅ "Trading schedule configured"
- ✅ No error messages

Press `Ctrl+C` to stop.

## Step 9: Monitor First Trading Session

### Option 1: Manual Start (Testing)

```python
# In main.py or trading_bot.py, you can force start immediately
# For testing, temporarily modify start_trading() to run immediately
```

### Option 2: Wait for Scheduled Start

The bot will automatically start at 14:25 London time.

### Watch the Logs

```bash
# In real-time
tail -f logs/trading_bot_YYYYMMDD.log

# Or watch console output
python main.py
```

**Expected Output:**
```
2025-01-13 14:25:00 - Starting trading session...
2025-01-13 14:25:01 - Starting equity: $100000.00
2025-01-13 14:25:05 - Scanning 20 symbols for opportunities...
2025-01-13 14:26:12 - AAPL: buy (strength: 0.85) - Momentum breakout
2025-01-13 14:26:15 - LLM analysis: Recommendation=buy, Confidence=0.92
2025-01-13 14:26:20 - Order executed: BUY 50 AAPL @ $182.50
```

## Step 10: Monitoring & Management

### View Active Positions

```python
# check_positions.py
from src.database import db
from src.database.models import Position, PositionStatus

with db.session_scope() as session:
    positions = session.query(Position).filter(
        Position.status == PositionStatus.OPEN
    ).all()

    for p in positions:
        print(f"{p.symbol}: {p.quantity} @ ${p.entry_price}")
        print(f"  P&L: ${p.pnl or 0:.2f}")
```

### View Session Performance

```python
# check_performance.py
from src.database import db
from src.database.models import TradingSession

with db.session_scope() as session:
    sessions = session.query(TradingSession).order_by(
        TradingSession.session_date.desc()
    ).limit(5).all()

    for s in sessions:
        print(f"{s.session_date}: ${s.pnl or 0:.2f} ({(s.pnl_pct or 0)*100:.2f}%)")
        print(f"  Trades: {s.total_trades} (W:{s.winning_trades} L:{s.losing_trades})")
```

### Emergency Stop

If you need to stop trading immediately:

```python
# emergency_stop.py
from src.data_pipeline import alpaca_client

# Close all positions
alpaca_client.close_all_positions()
print("All positions closed!")
```

Or simply press `Ctrl+C` when running `main.py`.

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'src'"

**Solution:**
```bash
# Make sure you're in the project root directory
cd Trading_Bot_ModerateScalping_Mk1

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
```

### Issue: "TA_Lib not found"

**Solution:**
Use pandas-ta instead (already in requirements):
```python
# pandas_ta is a pure Python alternative to TA-Lib
# It's already integrated in the strategies
```

### Issue: "Database locked"

**Solution:**
```bash
# Close all Python processes
# Delete database file
rm trading_bot.db

# Reinitialize
python -c "from src.database import init_database; init_database()"
```

### Issue: "API rate limit exceeded"

**Solution:**
```python
# In src/trading_bot.py, increase sleep time:
time.sleep(120)  # Change from 60 to 120 seconds
```

### Issue: Bot not trading

**Check:**
1. Is it within trading hours (14:25-21:05 London time)?
2. Are there signals being generated? (Check logs)
3. Is daily loss limit reached?
4. Are max positions reached?

## Going Live

### Before Live Trading

- [ ] Test with paper trading for at least 1 week
- [ ] Review all trades and performance
- [ ] Understand all risk parameters
- [ ] Set appropriate position sizes
- [ ] Have emergency stop procedures ready
- [ ] Start with small capital

### Switch to Live Trading

```bash
# In .env, change:
ALPACA_BASE_URL=https://api.alpaca.markets

# Reduce position sizes initially
MAX_POSITION_SIZE_PCT=0.05  # Start with 5% instead of 15%
```

### Best Practices

1. **Start Small**: Use 5-10% of intended capital first
2. **Monitor Closely**: Watch first week of live trading
3. **Review Daily**: Check session summaries every day
4. **Adjust Gradually**: Increase sizes slowly if profitable
5. **Set Alerts**: Monitor for unusual behavior
6. **Keep Records**: Export and backup database regularly

## Support & Resources

- **Logs**: Check `logs/` directory for detailed logs
- **Database**: Query `trading_bot.db` for historical data
- **Configuration**: Edit `.env` for parameter changes
- **Alpaca Docs**: [alpaca.markets/docs](https://alpaca.markets/docs)
- **Anthropic Docs**: [docs.anthropic.com](https://docs.anthropic.com)

---

**Ready to Trade!** 🚀

Remember: Start with paper trading, test thoroughly, and never risk more than you can afford to lose.
