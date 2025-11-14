# Paper Trading Deployment Guide

Complete guide for deploying the trading bot to paper trading with £3,000 capital.

---

## ✅ Pre-Deployment Checklist

### 1. Account Verification
- [x] Alpaca paper trading account created
- [x] Account funded with $3,000 (£3,000 equivalent)
- [x] API keys configured in `.env` file
- [x] Account connectivity tested

### 2. Configuration Review
- [x] Capital: £3,000
- [x] Max position size: £300 (10%)
- [x] Max positions: 3
- [x] Stop loss: 2%
- [x] Take profit: 4%
- [x] Daily loss limit: -£90 (3%)

### 3. Strategy Selection
- [x] **Base Momentum Breakout** (NO LLM)
- [ ] LLM-Enhanced (not recommended for 180+ days)

**Why Base Strategy?**
- Proven +4.11% over 180 days
- More consistent long-term performance
- No LLM API costs
- 52.3% win rate, Sharpe 1.62

---

## 🚀 Deployment Steps

### Step 1: Verify Configuration

```bash
# Display paper trading configuration
python config_paper_trading.py
```

**Expected Output:**
```
PAPER TRADING CONFIGURATION SUMMARY
======================================================================
CAPITAL:
  Starting Capital:    £3,000.00
  Max Per Position:    £300.00 (10%)
  Max Positions:       3

STRATEGY:
  Type:                Momentum Breakout (Base - NO LLM)
  Proven Return:       +4.11% (180 days)
```

### Step 2: Check Account Status

```bash
# Verify account connectivity and balance
python monitor_performance.py
```

**Expected Output:**
```
ACCOUNT SUMMARY:
  Starting Capital:    £3,000.00
  Current Equity:      £3,000.00
  Cash Available:      £3,000.00
  Buying Power:        £6,000.00
```

✅ **Confirm equity = £3,000 before proceeding!**

### Step 3: Deploy to Paper Trading

```bash
# Start paper trading bot
python deploy_paper_trading.py
```

**What happens:**
1. Bot displays configuration summary
2. Asks for confirmation
3. Connects to Alpaca
4. Starts scanning every 60 seconds
5. Executes trades based on Momentum Breakout signals

**Console Output:**
```
======================================================================
PAPER TRADING BOT - STARTING
======================================================================

Account Status:
  Equity:        £3,000.00
  Cash:          £3,000.00

Strategy:        MomentumBreakout
Symbols:         AAPL, MSFT, GOOGL, TSLA, NVDA
Trading Hours:   14:25 - 20:55 Europe/London

Bot is running... Press Ctrl+C to stop
======================================================================
```

### Step 4: Monitor Performance

**Option A: Live Dashboard (recommended)**
```bash
# Run in separate terminal
python monitor_performance.py --live
```

Refreshes every 60 seconds with:
- Current equity and P&L
- Open positions
- Target progress
- Risk status

**Option B: Daily Summary**
```bash
# Check end-of-day performance
python monitor_performance.py --summary
```

---

## 📊 30-Day Monitoring Plan

### Week 1: Initial Observation
**Goals:**
- Verify bot executes trades correctly
- Confirm risk management works (stop losses, position limits)
- Check for any errors or crashes

**Daily Tasks:**
- [ ] Check bot is running (morning and evening)
- [ ] Review any trades executed
- [ ] Monitor P&L (expect small +/- movements)
- [ ] Check logs for errors

**Expected Performance:** -2% to +2%

### Week 2: Pattern Analysis
**Goals:**
- Understand trade frequency (expect ~1-2 trades/week)
- Analyze win/loss patterns
- Verify strategy is following backtest behavior

**Daily Tasks:**
- [ ] Log trade details (entry, exit, reason)
- [ ] Compare to backtest expectations
- [ ] Note market conditions

**Expected Performance:** -1% to +3%

### Week 3: Risk Assessment
**Goals:**
- Confirm max drawdown stays within limits
- Test daily loss limits (if triggered)
- Evaluate position sizing

**Daily Tasks:**
- [ ] Check max drawdown
- [ ] Review largest losing trade
- [ ] Assess if position sizes are appropriate

**Expected Performance:** 0% to +4%

### Week 4: Decision Point
**Goals:**
- Determine if live trading is viable
- Calculate actual vs expected performance
- Make go/no-go decision

**End of Month Review:**
- [ ] Total return: ____% (target: +1.5%)
- [ ] Win rate: ____% (target: ~52%)
- [ ] Max drawdown: ____% (target: <5%)
- [ ] Number of trades: ____
- [ ] Any major issues? Yes / No

---

## 🎯 Realistic Expectations

### Monthly Performance Targets

| Metric | Conservative | Base Case | Optimistic |
|--------|-------------|-----------|------------|
| **Monthly Return** | +0.5% | +1.5% | +2.5% |
| **Monthly P&L** | +£15 | +£45 | +£75 |
| **Win Rate** | 50% | 52% | 55% |
| **Max Drawdown** | -5% | -4% | -3% |

### What to Expect

**First Week:**
- 0-3 trades total
- Likely small movements (+/- £50)
- Getting used to bot behavior

**First Month:**
- 4-12 trades total
- Target: +£45 (+1.5%)
- Learn strategy patterns

**First 3 Months:**
- 15-35 trades total
- Target: +£135 (+4.5% total)
- Decide on live trading

---

## ⚠️ Safety Protocols

### Automatic Stops (Built-in)

1. **Daily Loss Limit**: -£90 (3%)
   - Bot stops trading for the day
   - Resumes next trading day

2. **Account Protection**: £2,700 minimum
   - Bot stops if equity drops below this
   - Manual intervention required

3. **Position Limits**: Max 3 positions
   - Prevents over-exposure
   - Enforced before each trade

### Manual Interventions

**Stop trading immediately if:**
- [ ] Equity drops below £2,800 (-7%)
- [ ] 5 consecutive losing trades
- [ ] Bot shows errors or crashes repeatedly
- [ ] Market conditions change dramatically (news, volatility)

**Review strategy if:**
- [ ] Win rate drops below 45%
- [ ] Average loss > £20 per trade
- [ ] Trades executing at wrong times
- [ ] Performance significantly worse than backtest

---

## 🔧 Troubleshooting

### Bot Won't Start
```bash
# Check API connection
python -c "from src.data_pipeline import alpaca_client; print(alpaca_client.get_account())"
```

**Common issues:**
- API keys incorrect in `.env`
- Network connectivity
- Alpaca API down (check status.alpaca.markets)

### No Trades Executing
**Possible reasons:**
- Market hours (only trades 14:25-20:55 London time)
- No signals meeting criteria (normal - strategy is selective)
- Position limit reached (max 3)
- Daily loss limit hit

**Check:** Run backtest to confirm strategy still generates signals

### Performance Worse Than Backtest
**Normal** - Backtesting can't simulate:
- Execution slippage (real orders may fill at slightly worse prices)
- Market impact (large orders moving price)
- Partial fills (orders not fully executed)
- Live market volatility

**Acceptable deviation:** ±2% from backtest over 30 days

---

## 📈 Decision Tree: After 30 Days

### Scenario 1: Performance On Target (+1% to +3%)
✅ **Action:** Consider live trading with small capital
- Start with £500-£1,000 live
- Same configuration as paper
- Monitor for another 30 days

### Scenario 2: Performance Below Target (-1% to +1%)
⚠️ **Action:** Continue paper trading for another 30 days
- Review trades to understand why
- Check if market conditions were unusual
- Consider adjusting risk parameters

### Scenario 3: Significant Loss (< -3%)
❌ **Action:** STOP and re-evaluate
- Detailed review of all trades
- Check if strategy logic is correct
- Consider re-backtesting with recent data
- May need strategy adjustments

### Scenario 4: Exceptional Performance (> +5%)
🎉 **Action:** Proceed cautiously
- Performance may not be sustainable
- Could be lucky market conditions
- Start live with £1,000 and monitor closely

---

## 📝 Daily Checklist

### Morning (Before Market Open - 9:00 AM ET / 2:00 PM London)
- [ ] Check bot is running (`python monitor_performance.py`)
- [ ] Review overnight market news
- [ ] Check for any pending orders
- [ ] Verify account balance

### Evening (After Market Close - 4:30 PM ET / 9:30 PM London)
- [ ] Run daily summary (`python monitor_performance.py --summary`)
- [ ] Review any trades executed
- [ ] Log performance in spreadsheet
- [ ] Check for any errors in logs

### Weekly Review (Friday Evening)
- [ ] Calculate week's performance
- [ ] Review all trades
- [ ] Update performance spreadsheet
- [ ] Note any patterns or issues

---

## 💾 Performance Tracking

Create a spreadsheet to track:

| Date | Starting Equity | Ending Equity | Daily P&L | Daily % | Trades | Win Rate | Notes |
|------|----------------|---------------|-----------|---------|--------|----------|-------|
| Week 1 |
| Week 2 |
| Week 3 |
| Week 4 |
| **Month Total** |

---

## 🚦 Go-Live Decision Criteria

### Minimum Requirements (ALL must be met)

- [ ] **30+ days paper trading** completed
- [ ] **Positive returns** (+1% minimum)
- [ ] **Win rate** ≥ 50%
- [ ] **Max drawdown** < 5%
- [ ] **No major errors** or crashes
- [ ] **Understand** how strategy works
- [ ] **Capital available** for live trading (£1,000 minimum)
- [ ] **Risk tolerance** confirmed (can afford to lose 100%)

### Recommended Criteria

- [ ] **2-3 months** paper trading (not just 30 days)
- [ ] **+3% cumulative** return
- [ ] **52%+ win rate**
- [ ] **Consistent** performance (not one lucky month)
- [ ] **Tested** in different market conditions

---

## 📞 Support & Resources

### Documentation
- [README.md](README.md) - Main documentation
- [BACKTEST_RESULTS_180D.md](BACKTEST_RESULTS_180D.md) - Historical performance
- [config_paper_trading.py](config_paper_trading.py) - Configuration reference

### Commands
```bash
# Start bot
python deploy_paper_trading.py

# Monitor live
python monitor_performance.py --live

# Daily summary
python monitor_performance.py --summary

# Check configuration
python config_paper_trading.py
```

### Logs
- Location: `logs/trading_bot_YYYYMMDD.log`
- Format: JSON (searchable)
- Includes: All trades, decisions, errors

---

**Remember:** Paper trading is a TEST, not a guarantee. Always start small with live capital and never risk more than you can afford to lose.

**Good luck! 🚀**
