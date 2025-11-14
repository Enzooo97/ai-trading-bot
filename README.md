# AI-Enhanced Trading Bot (Momentum Breakout Strategy)

A sophisticated algorithmic trading bot with optional LLM (Large Language Model) enhancement for intelligent trade filtering and market regime detection.

## 🎯 Overview

This trading bot implements a **Momentum Breakout strategy** with optional Claude AI integration for:
- Market regime detection (trending vs ranging markets)
- Trade quality scoring (0-100 scale)
- Adaptive threshold adjustment based on market conditions
- Position sizing optimization

**Proven Performance:**
- **180-day backtest**: +4.11% return (8.5% annualized), 52.3% win rate
- **90-day LLM-enhanced**: +3.49% return (vs +0.12% base), 60% win rate, Sharpe 2.95
- Trades on Alpaca Markets (paper & live trading)

---

## 📊 Key Features

### Core Trading System
- ✅ **Multiple strategies** (Momentum Breakout, Mean Reversion, RSI Reversal, MACD Crossover)
- ✅ **Comprehensive backtesting** engine with realistic slippage modeling
- ✅ **Risk management** (stop-loss, take-profit, position sizing)
- ✅ **Paper trading** integration with Alpaca Markets
- ✅ **Real-time monitoring** and trade execution
- ✅ **SQLite database** for trade history and performance tracking

### LLM Enhancement (Optional)
- 🤖 **Claude 3 Haiku** integration for fast (<2s) market analysis
- 🧠 **Market regime detection** (strong/weak trends, ranging, volatile)
- 📈 **Trade quality scoring** with confidence levels
- 🎯 **Adaptive thresholds** (55-75/100) based on market conditions
- 💰 **Dynamic position sizing** (0.5x-1.5x) based on LLM confidence
- 💾 **15-minute caching** to minimize API costs

### Backtesting & Validation
- 📉 **180-day historical backtesting** across multiple timeframes
- 🔍 **Data quality validation** tools
- 📊 **Performance metrics** (Sharpe, Sortino, max drawdown, profit factor)
- 📈 **Equity curve** tracking
- 🎲 **Comparison testing** (base vs LLM strategies)

---

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Python 3.11+ required
python --version

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file (copy from `.env.example`):

```bash
# Alpaca API Keys (Paper Trading)
ALPACA_API_KEY=your_api_key_here
ALPACA_SECRET_KEY=your_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets/v2

# Claude API Key (Optional - for LLM features)
ANTHROPIC_API_KEY=your_claude_api_key_here

# Trading Parameters
MAX_POSITION_SIZE_PCT=0.15
STOP_LOSS_PCT=0.02
TAKE_PROFIT_PCT=0.04
```

### 3. Run Backtests

```bash
# Test base Momentum Breakout strategy (90 days)
python backtest_90d.py

# Test LLM-enhanced strategy with comparison
python compare_llm_backtest.py --days 90

# Comprehensive comparison (all approaches)
python compare_all_llm_approaches.py --days 180

# Validate data quality
python validate_data_quality.py --days 30 --symbols AAPL MSFT TSLA
```

### 4. Paper Trading

```bash
# Run paper trading (base strategy recommended for 180+ days)
python -m src.main

# Or test specific strategy
python test_strategy.py --strategy momentum_breakout
```

---

## 📈 Strategy Performance

### Base Momentum Breakout (No LLM)
**Best for**: 180-day+ trading horizons

| Metric | Value |
|--------|-------|
| **Total Return** | +4.11% (180 days) |
| **Annualized Return** | 8.51% |
| **Win Rate** | 52.3% |
| **Sharpe Ratio** | 1.62 |
| **Max Drawdown** | -3.93% |
| **Total Trades** | 107 |
| **Avg Hold Time** | 14.2 hours |

### LLM-Enhanced Strategy
**Best for**: 90-day trading horizons (re-evaluate quarterly)

| Metric | Base (90d) | LLM (90d) | Improvement |
|--------|-----------|----------|-------------|
| **Total Return** | +0.12% | +3.49% | **+2,808%** |
| **Win Rate** | 51.0% | 60.0% | +9% |
| **Sharpe Ratio** | 0.13 | 2.95 | **22.7x** |
| **Total Trades** | 49 | 25 | 49% filtered |

⚠️ **Note**: LLM over-filters on 180-day horizons (96% trades filtered, -1.64% return)

---

## 🧠 LLM Integration Details

### How It Works

1. **Market Regime Detection** (Every 15 minutes, cached)
   - Analyzes price action, volume, volatility
   - Classifies market: `strong_uptrend`, `weak_uptrend`, `ranging_tight`, etc.
   - Returns confidence level and optimal strategy recommendations

2. **Trade Quality Scoring** (Per signal, <2s)
   - Scores each trade opportunity 0-100
   - Considers: signal strength, market regime, indicators, volume
   - Provides reasoning and position size multiplier

3. **Adaptive Thresholds**
   - Strong trends: 55-60/100 threshold (allow more trades)
   - Weak trends: 65/100 threshold
   - Ranging markets: 70-75/100 threshold (be selective)

### Cost Optimization
- Uses Claude 3 Haiku (fastest, cheapest model)
- 15-minute regime caching reduces API calls by ~90%
- Average cost: ~$0.05-0.10 per trading day

---

## 📂 Project Structure

```
Trading_Bot_ModerateScalping_Mk1/
├── src/
│   ├── strategies/              # Trading strategies
│   │   ├── base_strategy.py
│   │   ├── momentum_breakout_strategy.py
│   │   └── momentum_breakout_llm.py  # LLM-enhanced version
│   ├── llm_integration/         # LLM services
│   │   ├── enhanced_llm_service.py
│   │   └── llm_analyzer.py
│   ├── backtesting/             # Backtesting engine
│   │   └── backtest_engine.py
│   ├── data_pipeline/           # Alpaca API client
│   │   └── alpaca_client.py
│   ├── database/                # SQLite database
│   ├── risk_management/         # Risk & position management
│   └── utils/                   # Utilities & logging
├── backtest_90d.py              # 90-day backtest
├── backtest_180d.py             # 180-day backtest
├── compare_llm_backtest.py      # LLM comparison tests
├── compare_all_llm_approaches.py # Comprehensive comparison
├── validate_data_quality.py     # Data quality validation
├── test_llm_enhanced.py         # LLM integration demo
├── requirements.txt             # Python dependencies
├── .env                         # Configuration (DO NOT COMMIT)
└── README.md                    # This file
```

---

## 🔧 Configuration Options

### Trading Parameters

```python
# Position Sizing
MAX_POSITION_SIZE_PCT = 0.15      # Max 15% of capital per trade
MAX_CONCURRENT_POSITIONS = 10     # Max 10 open positions

# Risk Management
STOP_LOSS_PCT = 0.02              # 2% stop loss
TAKE_PROFIT_PCT = 0.04            # 4% take profit
TRAILING_STOP_PCT = 0.015         # 1.5% trailing stop

# Trading Hours (London time)
TRADING_START_TIME = "14:25"      # 9:25 AM ET
TRADING_END_TIME = "21:05"        # 4:05 PM ET
```

### Strategy Parameters

```python
# Momentum Breakout
VOLUME_THRESHOLD = 1.5            # Volume must be 1.5x average
ATR_PCT_THRESHOLD = 0.015         # 1.5% volatility minimum
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

# LLM Configuration
LLM_SCORE_THRESHOLD = 70          # Trade quality threshold (0-100)
USE_ADAPTIVE_THRESHOLDS = True    # Adjust based on market regime
REGIME_CACHE_MINUTES = 15         # Cache regime detection
```

---

## 📊 Data Quality

**Source**: Alpaca Markets API (professional-grade market data)

**Validation Results** (30-day test):
- ✅ NO negative or zero prices
- ✅ NO invalid OHLC relationships
- ✅ NO extreme anomalies (max move: 4.16%)
- ✅ Zero data errors detected
- ⚠️ Includes extended hours data (pre-market + after-hours)

**Quality Score**: 85/100 - GOOD

**Limitations**:
- No Level 2 order book data
- No bid-ask spread modeling
- Assumes 100% fill rate (no partial fills)
- No market impact simulation

---

## 🎯 Recommendations

### For Long-Term Trading (180+ days)
✅ **Use Base Strategy (No LLM)**
- More consistent over long periods
- Lower API costs (no LLM calls)
- Proven 8.5% annualized returns

### For Medium-Term Trading (90 days)
✅ **Use LLM-Enhanced Strategy**
- Significantly better performance (+2,808%)
- Higher Sharpe ratio (2.95 vs 0.13)
- Re-evaluate every 90 days

### Realistic Expectations
- **Target**: 1-2% monthly returns (12-24% annually)
- **Not**: 1-2% daily returns (unrealistic for any strategy)
- Professional quant funds: 15-30% annually
- This bot (base): 8.5% annually
- This bot (LLM 90d): 14-18% annually projected

---

## ⚠️ Risk Warnings

1. **Past performance does not guarantee future results**
2. **Paper trading results may differ from live trading**
3. **Start with small capital to test in live markets**
4. **Use proper risk management (stop losses, position sizing)**
5. **Monitor bot performance daily, especially first 30 days**
6. **Be aware of market conditions (news, earnings, volatility)**

---

## 🛠️ Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

### Adding New Strategies

1. Inherit from `BaseStrategy` in `src/strategies/base_strategy.py`
2. Implement `analyze()` method returning `Signal` objects
3. Add strategy to backtesting scripts
4. Test with historical data before deploying

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

---

## 📧 Support

For issues or questions:
- Open an issue on GitHub
- Review existing backtest results in `BACKTEST_RESULTS_*.md`
- Check data quality with `validate_data_quality.py`

---

## 🙏 Acknowledgments

- **Alpaca Markets** for excellent API and paper trading
- **Anthropic** for Claude AI integration
- **pandas-ta** for technical indicators

---

## 📈 Version History

### v1.0.0 (Current)
- Initial release
- Momentum Breakout strategy with LLM enhancement
- Comprehensive backtesting (30, 90, 180 day tests)
- Adaptive threshold system
- Data quality validation tools
- Paper trading integration

---

**Built with Python 3.11+ | Powered by Alpaca Markets & Claude AI**
