# Scalping Strategy Research Summary

Research conducted: January 2025
Sources: Multiple trading platforms and strategy guides (2024-2025)

## Key Findings

### Best Scalping Timeframes
- **1-minute charts**: Ultra-fast scalping (10-30 trades per day)
- **5-minute charts**: OPTIMAL for scalping (balance of speed and accuracy)
- **15-minute charts**: Micro-swing trades (fewer but higher quality setups)

### Most Profitable Indicators for Scalping

#### Tier 1 (Essential)
1. **VWAP** - Institutional anchor point, shows fair value
2. **EMA (5, 9, 21)** - Fast crossovers for momentum
3. **RSI (7-9 period)** - Shortened for faster signals
4. **Volume Profile** - Key support/resistance levels

#### Tier 2 (Highly Effective)
5. **Stochastic (5,3,3)** - Overbought/oversold on steroids
6. **Bollinger Bands (20,2)** - Volatility and mean reversion
7. **ATR** - Position sizing and stop placement
8. **MACD (5,13,3)** - Faster than standard settings

#### Tier 3 (Supporting)
9. **CPR (Central Pivot Range)** - Intraday support/resistance
10. **Parabolic SAR** - Trend following and trailing stops

### Optimal Parameter Settings (Research-Backed)

| Indicator | Scalping Settings | Standard Settings | Rationale |
|-----------|------------------|-------------------|-----------|
| RSI | 7-9 period | 14 period | Faster response to price changes |
| RSI Levels | 20/80 or 25/75 | 30/70 | Tighter for more signals |
| MACD | (5, 13, 3) | (12, 26, 9) | Reduce lag for scalping |
| Bollinger | (20, 2) on 5min | (20, 2) | Standard works well |
| Stochastic | (5, 3, 3) | (14, 3, 3) | More sensitive |
| EMA Fast | 5 or 9 | 12 | Quick crossovers |
| EMA Slow | 21 or 26 | 26 | Balance speed/noise |
| ATR | 14 period | 14 period | Standard is optimal |

### Top 5 Proven Scalping Strategies

#### 1. VWAP Anchored Strategy ⭐⭐⭐⭐⭐
**Best for**: Trending days, institutional flow
**Timeframe**: 5-minute
**Win Rate**: 60-65%

**Rules**:
- Long when price dips to VWAP from above (buying support)
- Short when price rallies to VWAP from below (selling resistance)
- Confirm with volume spike (>1.5x average)
- Exit at 0.3-0.5% profit or return to VWAP
- Stop: 0.2% beyond VWAP

**Indicators**:
- VWAP (daily reset)
- Volume (20 SMA)
- 9 EMA for trend confirmation

#### 2. EMA Triple Crossover (5/9/21) ⭐⭐⭐⭐⭐
**Best for**: Momentum trading, trending markets
**Timeframe**: 5-minute
**Win Rate**: 55-62%

**Rules**:
- Long: 5 EMA crosses above 9 EMA, both above 21 EMA
- Short: 5 EMA crosses below 9 EMA, both below 21 EMA
- Volume must be >1.3x average
- Exit when 5 EMA crosses back through 9 EMA
- Target: 0.4-0.6%, Stop: 0.2%

**Indicators**:
- EMA 5, 9, 21
- Volume confirmation
- Optional: RSI > 50 for longs, < 50 for shorts

#### 3. Stochastic RSI Combo ⭐⭐⭐⭐
**Best for**: Range-bound markets, reversals
**Timeframe**: 5-minute or 15-minute
**Win Rate**: 58-63%

**Rules**:
- Long: RSI(7) < 25 AND Stochastic(5,3,3) < 20
- Short: RSI(7) > 75 AND Stochastic(5,3,3) > 80
- Both must turn up/down (divergence fading)
- Exit when RSI returns to 50 or Stochastic crosses 50
- Target: 0.5-0.8%, Stop: 0.25%

**Indicators**:
- RSI (7 period, levels: 25/75)
- Stochastic (5, 3, 3, levels: 20/80)
- Bollinger Bands optional for entry confirmation

#### 4. Bollinger Band Squeeze ⭐⭐⭐⭐
**Best for**: Volatility breakouts
**Timeframe**: 5-minute
**Win Rate**: 52-58%

**Rules**:
- Wait for BB width to compress < 2% of price
- Enter on breakout above upper band (long) or below lower (short)
- Volume must surge (>2x average)
- Exit at 2x ATR or when price returns inside bands
- Target: 0.6-1.0%, Stop: 0.3%

**Indicators**:
- Bollinger Bands (20, 2)
- ATR (14) for targets
- Volume
- RSI to avoid false breakouts in overbought/oversold

#### 5. Parabolic SAR + EMA Trend ⭐⭐⭐⭐
**Best for**: Strong trending days
**Timeframe**: 5-minute or 15-minute
**Win Rate**: 57-62%

**Rules**:
- Long: SAR flips below price AND 21 EMA rising
- Short: SAR flips above price AND 21 EMA falling
- Hold until SAR flips again
- Trail stop with SAR dots
- Target: 0.5-1.2%, Stop: SAR flip

**Indicators**:
- Parabolic SAR (default: 0.02, 0.2)
- EMA 21 for trend filter
- Volume confirmation

### Advanced Concepts

#### Order Flow (Institutional Level)
- Level 2 market depth analysis
- Tape reading for large orders
- Footprint charts
- **Note**: Requires specialized platforms (Bookmap, ATAS)
- Not easily implemented via Alpaca API

#### Volume Profile
- Point of Control (POC): Highest volume price level
- Value Area: 70% of volume distribution
- High/Low Volume Nodes as support/resistance
- **Implementation**: Calculate from historical data

### Risk Management for Scalping

#### Position Sizing
- Max 2-3% risk per trade
- 10-20 positions per day maximum
- Never risk more than 6% total simultaneously

#### Stop Losses
- **ATR-based**: 1.5x ATR (tight but accounts for volatility)
- **Fixed**: 0.15-0.25% for scalping
- **Time-based**: Exit after 15-30 minutes if no movement

#### Profit Targets
- **Quick scalps**: 0.3-0.5% (30-60 seconds)
- **Standard**: 0.5-0.8% (2-5 minutes)
- **Runners**: 1.0-2.0% (10-30 minutes)
- Risk/Reward minimum: 2:1

### Best Practice Combinations

#### Aggressive Scalping (15-30 trades/day)
- VWAP + Volume
- 1-5 minute timeframe
- 0.3-0.5% targets
- Very tight stops (0.15%)

#### Moderate Scalping (8-15 trades/day)
- EMA Crossover + RSI
- 5-minute timeframe
- 0.5-0.8% targets
- Standard stops (0.2-0.25%)

#### Conservative Micro-Swing (5-10 trades/day)
- Stochastic RSI + Bollinger
- 15-minute timeframe
- 0.8-1.5% targets
- Wider stops (0.3-0.4%)

### Market Conditions

#### Best Times for Scalping
- **9:30-11:00 AM EST**: Market open volatility
- **2:00-4:00 PM EST**: Afternoon momentum
- **Avoid**: 11:30-1:30 PM (lunch lull)

#### Best Assets
- High liquidity (>5M daily volume)
- Tight spreads (<0.05%)
- High volatility (>1% ATR)
- Examples: SPY, QQQ, AAPL, TSLA, NVDA

### Technology Requirements

#### Execution Speed
- Scalping requires <100ms execution
- Co-located servers ideal
- Alpaca Premium for best fills

#### Data Quality
- Real-time Level 1 minimum
- 1-second or tick data preferred
- Level 2 for advanced strategies

## Implementation Priorities

### Phase 1: Core Strategies (Implement Now)
1. ✅ Momentum Breakout (already implemented)
2. ✅ Mean Reversion (already implemented)
3. 🔄 VWAP Anchored Strategy
4. 🔄 EMA Triple Crossover (5/9/21)
5. 🔄 Stochastic RSI Combo

### Phase 2: Advanced Strategies (After Backtesting)
6. Bollinger Band Squeeze
7. Parabolic SAR Trend
8. Volume Profile Strategy
9. CPR Strategy

### Phase 3: Optimization (After Live Testing)
- Walk-forward analysis
- Parameter optimization per symbol
- Adaptive strategies
- Machine learning enhancements

## Recommended Backtesting Approach

### Data Requirements
- 6-12 months historical data
- 5-minute bars minimum
- Include: OHLCV, spreads, slippage

### Metrics to Track
- Win rate
- Profit factor
- Sharpe ratio
- Max drawdown
- Average trade duration
- Trades per day
- Commission impact

### Validation
1. In-sample optimization (60% data)
2. Out-of-sample testing (20% data)
3. Walk-forward validation (20% data)
4. Paper trading (1 week)
5. Small live capital (1 week)
6. Full deployment

## Key Takeaways

✅ **5-minute timeframe is optimal** for balancing speed and accuracy
✅ **VWAP is the king indicator** for institutional-grade scalping
✅ **EMA crossovers (5/9/21) are highly effective** for momentum
✅ **RSI and Stochastic work better with shorter periods** (7-9 vs 14)
✅ **Volume confirmation is crucial** (>1.3-1.5x average)
✅ **Tight stops (0.15-0.25%)** with 2:1 risk/reward minimum
✅ **10-20 trades per day** is realistic and profitable
✅ **Avoid choppy mid-day hours** (11:30 AM - 1:30 PM EST)

## Next Steps

1. Implement top 3 new strategies
2. Create comprehensive backtesting engine
3. Test on 6 months historical data
4. Optimize parameters per strategy
5. Combine strategies with voting system
6. Live test with paper trading
7. Deploy with small capital

---

**Research Sources**: TradingView, LiteFinance, Elearnmarkets, IG, Bookmap, ATAS, QuantifiedStrategies (2024-2025)
