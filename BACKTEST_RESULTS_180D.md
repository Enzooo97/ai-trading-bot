# Comprehensive 180-Day Backtest Results

**Test Period**: May 17, 2025 - November 13, 2025 (180 days)
**Symbols**: AAPL, MSFT, GOOGL, TSLA, NVDA
**Initial Capital**: $100,000
**Strategies Tested**: VWAP, EMA Crossover, Stochastic RSI, Momentum Breakout, Mean Reversion

## Test Matrix

**All timeframes tested with 5Min bars (data resolution limitation)**

| Timeframe Label | Best Strategy | Return | Win Rate | Trades | Sharpe | Max DD |
|-----------------|---------------|--------|----------|--------|--------|--------|
| 1 Min | Momentum Breakout | +4.11% | 52.3% | 107 | 1.62 | 3.93% |
| 5 Min | Momentum Breakout | +4.11% | 52.3% | 107 | 1.62 | 3.93% |
| 15 Min | Momentum Breakout | +4.11% | 52.3% | 107 | 1.62 | 3.93% |
| 30 Min | Momentum Breakout | +4.11% | 52.3% | 107 | 1.62 | 3.93% |

**Note**: All results identical - backtesting used 5Min bars regardless of timeframe parameter. Different timeframes would require different data resolution from Alpaca.

## Detailed Strategy Results (180 Days, 5Min Bars)

| Strategy | Return | Ann. Return | Win Rate | Trades | Sharpe | Max DD | Avg Trade |
|----------|--------|-------------|----------|--------|--------|--------|-----------|
| **Momentum Breakout** | **+4.11%** | **+8.51%** | **52.3%** | **107** | **1.62** | **3.93%** | **$38.37** |
| Stochastic RSI | -0.39% | -0.79% | 54.6% | 141 | -0.38 | 1.14% | -$2.78 |
| VWAP Anchored | -0.42% | -0.86% | 46.3% | 41 | -1.77 | 1.05% | -$10.32 |
| EMA Crossover | -1.55% | -3.12% | 47.4% | 274 | -0.69 | 2.55% | -$5.65 |
| Mean Reversion | -2.49% | -4.98% | 42.4% | 33 | -3.59 | 3.73% | -$75.48 |

## Key Findings

### 1. **Winner: Momentum Breakout Strategy**
- **Only profitable strategy** over 180 days
- 8.51% annualized return (4.11% in 180 days)
- Excellent risk-adjusted returns (1.62 Sharpe, 3.96 Sortino)
- Good risk/reward: $362 avg win vs $317 avg loss
- **Critical Issue**: Avg hold time = 851 minutes (~14 hours) - This is NOT scalping, it's swing trading!

### 2. **All Scalping Strategies Failed**
- VWAP, EMA, Stochastic RSI all showed negative returns
- Even with 54.6% win rate, Stochastic RSI lost money (poor R:R ratio)
- Too many trades with poor risk/reward ratios

### 3. **Path to 1-2% Daily Returns**

**Current Performance**: 4.11% / 180 days = 0.023% per day (far from 1-2% target)

**What's needed**:
- **40-85x improvement** in daily returns
- This is extremely challenging and likely unrealistic for consistent scalping
- 1% daily = 252% annually (compounded = 1,150%+ annually!)
- 2% daily = 504% annually (compounded = 137,000%+ annually!)

### 4. **Recommendations**

**Short-term (Use what works)**:
1. Deploy Momentum Breakout as-is
2. Accept it's a swing strategy (14hr holds), not scalping
3. Target realistic 8-15% annual returns
4. Use LLM for:
   - Market regime detection (trending vs ranging)
   - Entry quality scoring
   - Position sizing optimization

**Medium-term (Improve existing)**:
1. Optimize Momentum Breakout for shorter holds
2. Add market regime filters (ADX > 25 for trends)
3. Improve R:R ratios on other strategies:
   - Increase profit targets to 2x stop loss
   - Tighten entry criteria (fewer, better trades)
4. Test on higher volatility periods only

**Long-term (Reality check)**:
- **1-2% daily is not realistic for algorithmic trading**
- Professional quant funds target 15-30% annually
- Scalping typically yields 0.05-0.2% per day on good days
- Your bot would need to be in top 0.1% of all trading bots globally

## LLM Integration Strategy for Your Goals

### Current State
- You have Claude API key configured
- LLM can analyze market conditions, optimize parameters, validate trades
- **But**: LLM cannot magically create 1-2% daily returns from strategies that fundamentally don't perform

### How LLM Can Help (Realistically)

**1. Market Regime Detection** (Run every 15 min)
```
- Identify if market is: Trending Up, Trending Down, Ranging, High Volatility
- Enable/disable strategies based on regime
- Example: Only run Momentum Breakout during strong trends (ADX > 25)
```

**2. Trade Quality Scoring** (Run before each trade)
```
- Score each signal 0-100 based on:
  * Multiple timeframe confirmation
  * Volume profile
  * Recent win/loss patterns
  * Market regime alignment
- Only execute trades scoring > 70
```

**3. Dynamic Parameter Optimization** (Run daily after market close)
```
- Analyze day's trades
- Suggest parameter adjustments:
  * "Increase stop loss from 0.25% to 0.3% - recent losses due to tight stops"
  * "VWAP working better in first 2 hours - adjust trading window"
- Test suggestions in next day's trading
```

**4. Position Sizing Optimization** (Real-time)
```
- Adjust position size based on:
  * Recent win streak/loss streak
  * Current drawdown
  * Signal confidence score
  * Account balance
```

### What LLM CANNOT Do
- Predict future price movements with certainty
- Generate alpha (excess returns) consistently
- Turn losing strategies into 1-2% daily gainers
- Replace fundamental strategy improvements

### Realistic Expectations with LLM
- **Without LLM**: 8.5% annual (Momentum Breakout)
- **With LLM**: 12-18% annual (optimistic)
  - +30-50% improvement through:
    * Better trade filtering (fewer losing trades)
    * Optimized position sizing
    * Market regime awareness

---

**Started**: 2025-11-13 18:10
**Completed**: 2025-11-13 19:38 (1 hour 28 minutes)
