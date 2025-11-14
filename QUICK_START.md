# Quick Start Guide

## Python 3.11 Detected!

Good news: Python 3.11 is already installed on your system at:
- Location: `py -3.11` (via Python launcher)
- Version: Python 3.11 (64-bit)

## Step 1: Run the Automated Setup

Open PowerShell in this project directory and run:

```powershell
.\setup_python311.ps1
```

This will:
- Create Python 3.11 virtual environment in `venv/` folder
- Activate the virtual environment
- Upgrade pip to latest version
- Install all dependencies from requirements.txt
- Test all critical imports
- Show you next steps

**If you get a script execution error**, run this first:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Step 2: Add Your Alpaca API Keys

After the setup completes, open [.env](.env) and replace:

```bash
ALPACA_API_KEY=your_api_key_here
ALPACA_SECRET_KEY=your_secret_key_here
```

With your actual Alpaca API keys from [alpaca.markets](https://alpaca.markets).

## Step 3: Run Your First Backtest

Activate the virtual environment:
```powershell
.\venv\Scripts\activate
```

Run a comprehensive backtest:
```bash
python run_backtest.py --strategy all --symbols AAPL MSFT GOOGL TSLA NVDA --days 30
```

This will test all 5 strategies and show you which performs best.

## Expected Timeline

- **Setup (Step 1)**: 5-10 minutes (automated)
- **API Keys (Step 2)**: 2-3 minutes
- **First Backtest (Step 3)**: 3-5 minutes
- **Total**: ~15 minutes to your first results

## What Happens Next

After your first backtest, you'll see:
- Win rates for each strategy (target: >55%)
- Total returns and annualized returns
- Sharpe ratios (target: >1.0)
- Maximum drawdowns (target: <12%)
- Trade frequency and profit factors

Based on these metrics, you can:
1. Choose the top 2-3 performing strategies
2. Run extended backtests (60-90 days)
3. Optimize parameters
4. Start paper trading

## Need Help?

Check these guides:
- [NEXT_STEPS.md](NEXT_STEPS.md) - Detailed workflow and troubleshooting
- [BACKTESTING_GUIDE.md](BACKTESTING_GUIDE.md) - How to interpret results
- [SCALPING_RESEARCH.md](SCALPING_RESEARCH.md) - Strategy details

## Ready to Go!

Your trading bot has:
- 5 professional strategies (research-backed)
- Comprehensive backtesting engine
- Risk management system
- LLM integration (optional)
- Automated scheduling
- Full documentation

Just run the setup script and you're ready to start testing!
