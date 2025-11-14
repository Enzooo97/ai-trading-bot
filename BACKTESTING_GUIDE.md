# Backtesting Guide

## Overview

Your trading bot now includes a comprehensive backtesting engine to validate and optimize strategies before live trading.

## Quick Start

### Run Backtest for All Strategies

```bash
python run_backtest.py --strategy all --symbols AAPL MSFT GOOGL --days 30
```

### Run Backtest for Specific Strategy

```bash
# VWAP strategy
python run_backtest.py --strategy vwap --symbols SPY QQQ --days 60

# EMA Crossover strategy
python run_backtest.py --strategy ema --symbols TSLA NVDA AMD --days 90

# Stochastic RSI strategy
python run_backtest.py --strategy stochastic --symbols AAPL MSFT --days 30
```

### Custom Timeframe

```bash
# 1-minute bars (ultra-fast scalping)
python run_backtest.py --strategy vwap --timeframe 1Min --days 7

# 15-minute bars (micro-swing)
python run_backtest.py --strategy ema --timeframe 15Min --days 60
```

## Available Strategies

| Strategy Code | Name | Best For |
|--------------|------|----------|
| `vwap` | VWAP Anchored | Institutional flow, trending days |
| `ema` | EMA Triple Crossover (5/9/21) | Fast momentum, trending markets |
| `stochastic` | Stochastic RSI Combo | Range-bound, mean reversion |
| `momentum` | Momentum Breakout | Strong trends, breakouts |
| `meanrev` | Mean Reversion | Oversold/overbought reversals |

## Understanding Results

### Key Metrics Explained

**Returns**:
- **Total Return**: Overall profit/loss percentage
- **Annualized Return**: Projected annual return rate

**Trades**:
- **Win Rate**: Percentage of winning trades (target: >55%)
- **Avg Trades/Day**: Number of trades per day

**Profitability**:
- **Profit Factor**: Gross profit / Gross loss (target: >1.5)
- **Avg Win/Loss**: Average profit vs average loss

**Risk**:
- **Max Drawdown**: Largest peak-to-trough decline (keep <10%)
- **Sharpe Ratio**: Risk-adjusted return (>1.0 good, >2.0 excellent)
- **Sortino Ratio**: Downside risk-adjusted return

### Example Output

```
==================================================================
RESULTS: VWAP_Anchored
==================================================================

📊 RETURNS:
  Total Return:             +8.45%
  Annualized Return:       +112.34%

📈 TRADES:
  Total Trades:                 45
  Winning Trades:               28 (62.2%)
  Losing Trades:                17
  Avg Trades/Day:              1.5

💰 PROFITABILITY:
  Avg Win:              $   287.50
  Avg Loss:             $  -142.30
  Profit Factor:             2.35
  Avg Trade P&L:        $   187.78

⚠️  RISK METRICS:
  Max Drawdown:             -4.25%
  Sharpe Ratio:              2.18
  Sortino Ratio:             3.45

⏱️  TRADE CHARACTERISTICS:
  Avg Hold Time:            18.5 minutes
  Max Consecutive Wins:         5
  Max Consecutive Loss:         3

📅 DAILY STATS:
  Best Day:                 +2.45%
  Worst Day:                -1.12%
```

## Interpreting Results

### Excellent Strategy
- ✅ Win rate > 58%
- ✅ Profit factor > 2.0
- ✅ Sharpe ratio > 1.5
- ✅ Max drawdown < 8%
- ✅ Annualized return > 50%

### Good Strategy
- ✅ Win rate > 55%
- ✅ Profit factor > 1.5
- ✅ Sharpe ratio > 1.0
- ✅ Max drawdown < 12%
- ✅ Annualized return > 30%

### Needs Optimization
- ⚠️ Win rate < 52%
- ⚠️ Profit factor < 1.3
- ⚠️ Sharpe ratio < 0.8
- ⚠️ Max drawdown > 15%

### Red Flags
- 🚫 Win rate < 48%
- 🚫 Profit factor < 1.0
- 🚫 Max drawdown > 20%
- 🚫 Negative Sharpe ratio

## Backtest Validation Workflow

### 1. Initial Test (30 days)

```bash
python run_backtest.py --strategy all --days 30
```

**Purpose**: Quick validation of all strategies
**Decision**: Choose top 2-3 performers

### 2. Extended Test (90 days)

```bash
python run_backtest.py --strategy vwap --days 90
python run_backtest.py --strategy ema --days 90
```

**Purpose**: Validate consistency over longer period
**Decision**: Confirm strategies work in different market conditions

### 3. Symbol Specific Test

```bash
# Test high volatility stocks
python run_backtest.py --strategy vwap --symbols TSLA NVDA AMD --days 60

# Test stable stocks
python run_backtest.py --strategy meanrev --symbols AAPL MSFT GOOGL --days 60

# Test ETFs
python run_backtest.py --strategy ema --symbols SPY QQQ IWM --days 60
```

**Purpose**: Find which strategies work best for which assets
**Decision**: Strategy-symbol matching

### 4. Timeframe Optimization

```bash
# 1-minute (aggressive)
python run_backtest.py --strategy vwap --timeframe 1Min --days 7

# 5-minute (optimal)
python run_backtest.py --strategy vwap --timeframe 5Min --days 30

# 15-minute (conservative)
python run_backtest.py --strategy vwap --timeframe 15Min --days 60
```

**Purpose**: Find optimal timeframe per strategy
**Decision**: Balance speed vs accuracy

## Advanced Analysis

### Compare Strategies

```bash
python run_backtest.py --strategy all --symbols AAPL MSFT GOOGL TSLA NVDA --days 60
```

Look at the comparison table:
- Highest return
- Best win rate
- Best Sharpe ratio
- Lowest drawdown

### Walk-Forward Analysis (Manual)

1. **Train period**: 60 days
   ```bash
   python run_backtest.py --strategy vwap --days 60
   ```

2. **Test period**: Next 30 days
   ```bash
   python run_backtest.py --strategy vwap --days 30
   ```

3. **Compare**: Do results hold up?

### Monte Carlo Simulation (Future)

- Run 1000+ variations
- Randomize entry/exit timing
- Test parameter sensitivity
- Calculate probability of success

## Optimization Tips

### If Win Rate Too Low (<50%)

**Try**:
- Increase minimum signal strength threshold
- Add more filters (volume, trend)
- Tighten entry conditions
- Use LLM validation

### If Profit Factor Too Low (<1.5)

**Try**:
- Widen profit targets
- Tighten stop losses
- Hold winners longer
- Cut losers faster

### If Max Drawdown Too High (>12%)

**Try**:
- Reduce position sizes
- Lower leverage
- Add daily loss limits
- Diversify across more symbols

### If Too Few Trades (<0.5/day)

**Try**:
- Lower signal strength threshold
- Reduce entry requirements
- Add more symbols
- Use faster timeframe

### If Too Many Trades (>5/day)

**Try**:
- Increase signal strength threshold
- Add more filters
- Use slower timeframe
- Focus on best setups only

## Real-World Considerations

### Backtesting Limitations

1. **Slippage**: Backtest assumes 2bp slippage (may be higher in reality)
2. **Commissions**: Alpaca has $0 commissions (backtest reflects this)
3. **Market Impact**: Doesn't account for large orders moving the market
4. **Liquidity**: Assumes unlimited liquidity (not true for all stocks)
5. **Data Quality**: Historical data may have gaps or errors

### Adjustments for Live Trading

After backtesting, reduce expectations:
- **Win Rate**: Reduce by 3-5%
- **Profit Factor**: Reduce by 0.2-0.3
- **Return**: Reduce by 10-20%
- **Max Drawdown**: Increase by 20-30%

**Example**:
- Backtest: 60% win rate, 8% return
- Live expectation: 55% win rate, 6-7% return

## Strategy Selection Criteria

### For Trending Markets
1. VWAP Anchored (institutional flow)
2. EMA Triple Crossover (momentum)
3. Momentum Breakout (trend continuation)

### For Range-Bound Markets
1. Stochastic RSI (extreme reversals)
2. Mean Reversion (oversold/overbought)
3. Bollinger Band strategies

### For Mixed Conditions
- Use all strategies
- Let each find its opportunities
- Diversification reduces risk

## Next Steps After Backtesting

### 1. Choose Top Strategies

Based on results, select 2-3 best performers:
```python
# In src/trading_bot.py
self.strategies = [
    VWAPStrategy(),           # If ranked #1
    EMATripleCrossoverStrategy(),  # If ranked #2
    StochasticRSIStrategy(),  # If ranked #3
]
```

### 2. Optimize Parameters

Fine-tune strategy parameters:
```python
# Example: Adjust RSI levels
RSI_OVERSOLD=25  # From 30
RSI_OVERBOUGHT=75  # From 70
```

### 3. Paper Trading

Run bot on paper account for 1 week:
```bash
python main.py
```

Monitor:
- Does it match backtest results?
- Any unexpected behavior?
- Strategy win rates holding up?

### 4. Go Live (Small Capital)

Start with 10-20% of intended capital:
```bash
# In .env
MAX_POSITION_SIZE_PCT=0.05  # 5% per position (conservative)
MAX_LEVERAGE=2.0  # Half leverage initially
```

### 5. Scale Up Gradually

If profitable after 1 week:
- Increase capital by 20%
- Monitor for 3 more days
- Repeat until at full capital

## Troubleshooting

### Backtest Won't Run

```bash
# Check API keys
python -c "from src.config import settings; print(settings.alpaca_api_key)"

# Test Alpaca connection
python -c "from src.data_pipeline import alpaca_client; print(alpaca_client.get_account())"
```

### No Trades Generated

- Check date range (need enough data)
- Try different symbols
- Lower signal strength threshold
- Check timeframe availability

### Poor Results on All Strategies

- Market conditions may not suit strategies
- Try different time period
- Test on more liquid symbols
- Adjust parameters

## Performance Benchmarks

### Research-Backed Targets

| Strategy | Win Rate | Profit Factor | Max DD | Daily Trades |
|----------|----------|---------------|--------|--------------|
| VWAP | 60-65% | 2.0-2.5 | 5-8% | 1-3 |
| EMA Crossover | 55-62% | 1.8-2.3 | 6-10% | 2-4 |
| Stochastic RSI | 58-63% | 2.1-2.6 | 5-9% | 1-2 |
| Momentum | 52-58% | 1.6-2.1 | 8-12% | 2-5 |
| Mean Reversion | 55-60% | 1.7-2.2 | 6-11% | 1-3 |

If your backtests match these ranges, strategies are working correctly!

## Conclusion

Backtesting is crucial for:
- ✅ Validating strategies before risking real money
- ✅ Optimizing parameters for best performance
- ✅ Understanding risk/reward profiles
- ✅ Building confidence in your system

**Remember**: Past performance doesn't guarantee future results, but it's the best tool we have for strategy validation.

---

**Happy Backtesting!** 📊📈
