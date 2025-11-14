# Trading Bot Quick Reference

Quick commands and tips for daily operation.

## Daily Operations

### Start Bot
```bash
# Activate environment
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Run bot
python main.py
```

Bot automatically trades 14:25-21:05 London time.

### Stop Bot
Press `Ctrl+C` or wait until 21:05 (automatic stop)

### Emergency Stop
```python
python -c "from src.data_pipeline import alpaca_client; alpaca_client.close_all_positions()"
```

## Monitoring

### View Logs
```bash
# Real-time
tail -f logs/trading_bot_20250113.log

# Latest errors
grep ERROR logs/trading_bot_20250113.log
```

### Check Performance
```python
# Quick check
python -c "
from src.database import db
from src.database.models import TradingSession

with db.session_scope() as session:
    s = session.query(TradingSession).filter(
        TradingSession.is_active == True
    ).first()
    if s:
        print(f'P&L: ${s.pnl or 0:.2f} ({(s.pnl_pct or 0)*100:.2f}%)')
        print(f'Trades: {s.total_trades} (W:{s.winning_trades}/L:{s.losing_trades})')
"
```

### Check Positions
```python
python -c "
from src.data_pipeline import alpaca_client
positions = alpaca_client.get_positions()
for p in positions:
    print(f\"{p['symbol']}: {p['quantity']} @ ${p['avg_entry_price']} (P&L: ${p['unrealized_pl']})\")
"
```

## Configuration Quick Edits

Edit `.env` file:

```bash
# More aggressive (higher risk)
MAX_POSITION_SIZE_PCT=0.20
MAX_LEVERAGE=4.0
STOP_LOSS_PCT=0.025

# More conservative (lower risk)
MAX_POSITION_SIZE_PCT=0.10
MAX_LEVERAGE=2.0
STOP_LOSS_PCT=0.015
```

Restart bot for changes to take effect.

## Common Issues

### Bot Not Trading

**Check:**
```python
python -c "
from src.utils.scheduler import TradingScheduler
from src.config import settings
from datetime import datetime

# Check if in trading hours
tz = settings.get_timezone()
now = datetime.now(tz)
start = settings.get_trading_start_time()
stop = settings.get_trading_end_time()
print(f'Current time: {now.time()}')
print(f'Trading hours: {start} - {stop}')
print(f'In hours: {start <= now.time() <= stop}')
"
```

### Check Account Status
```python
python -c "
from src.data_pipeline import alpaca_client
account = alpaca_client.get_account()
print(f'Equity: ${account[\"equity\"]}')
print(f'Buying Power: ${account[\"buying_power\"]}')
print(f'Trading Blocked: {account[\"trading_blocked\"]}')
"
```

### Reset Daily Limits
If bot stopped due to limits, reset by:
1. Wait for next day
2. Or manually adjust in database (advanced)

## Performance Targets

- **Daily Goal**: +5% profit
- **Stop Loss**: -3% max daily loss
- **Win Rate**: Target >55%
- **Profit Factor**: Target >1.5
- **Max Drawdown**: <10%

## Risk Limits

- Max 10 positions simultaneously
- Max 15% of capital per position
- Max 4x leverage (high confidence only)
- Max 48 hours per position
- 1.5-2% stop loss per trade

## Key Files

- `.env` - Configuration
- `logs/trading_bot_YYYYMMDD.log` - Daily logs
- `trading_bot.db` - Trading history
- `main.py` - Bot entry point
- `README.md` - Full documentation
- `SETUP_GUIDE.md` - Setup instructions

## Useful Commands

### Backup Database
```bash
cp trading_bot.db trading_bot_backup_$(date +%Y%m%d).db
```

### View Recent Trades
```python
python -c "
from src.database import db
from src.database.models import Position
from datetime import datetime, timedelta

with db.session_scope() as session:
    recent = session.query(Position).filter(
        Position.entry_time >= datetime.utcnow() - timedelta(days=1)
    ).all()

    for p in recent:
        pnl = p.pnl or 0
        status = p.status.value
        print(f'{p.symbol}: {status} - P&L: ${pnl:.2f}')
"
```

### Calculate Today's P&L
```python
python -c "
from src.database import db
from src.database.models import Position
from datetime import datetime

with db.session_scope() as session:
    today = session.query(Position).filter(
        Position.entry_time >= datetime.utcnow().date()
    ).all()

    total_pnl = sum(p.pnl or 0 for p in today)
    print(f'Today P&L: ${total_pnl:.2f}')
"
```

## Safety Checklist

- [ ] Using paper trading initially
- [ ] API keys properly configured
- [ ] Daily loss limits set
- [ ] Position size limits appropriate
- [ ] Monitoring logs actively
- [ ] Emergency stop procedure known
- [ ] Backup of configuration saved

## Contact

For issues:
1. Check logs in `logs/` directory
2. Review database for trade history
3. Verify `.env` configuration
4. Test API connections

---

**Trade Smart, Trade Safe** 📊
