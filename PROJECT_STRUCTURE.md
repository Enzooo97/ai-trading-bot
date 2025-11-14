# Project Structure

Complete overview of the trading bot architecture and file organization.

## Directory Structure

```
Trading_Bot_ModerateScalping_Mk1/
├── src/                          # Source code
│   ├── config/                   # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py           # Pydantic settings with validation
│   │
│   ├── database/                 # Database layer
│   │   ├── __init__.py
│   │   ├── database.py           # SQLAlchemy connection & sessions
│   │   └── models.py             # ORM models (Position, Order, etc.)
│   │
│   ├── data_pipeline/            # Market data integration
│   │   ├── __init__.py
│   │   └── alpaca_client.py      # Alpaca API wrapper
│   │
│   ├── strategies/               # Trading strategies
│   │   ├── __init__.py
│   │   ├── base_strategy.py      # Abstract base class
│   │   ├── momentum_breakout_strategy.py
│   │   └── mean_reversion_strategy.py
│   │
│   ├── risk_management/          # Risk control
│   │   ├── __init__.py
│   │   └── risk_manager.py       # Position sizing, stop loss, limits
│   │
│   ├── order_execution/          # Order management
│   │   ├── __init__.py
│   │   └── order_executor.py     # Order placement & tracking
│   │
│   ├── llm_integration/          # AI analysis
│   │   ├── __init__.py
│   │   └── llm_analyzer.py       # Claude/GPT integration
│   │
│   ├── utils/                    # Utilities
│   │   ├── __init__.py
│   │   ├── logger.py             # Logging configuration
│   │   └── scheduler.py          # Trading schedule automation
│   │
│   ├── __init__.py
│   └── trading_bot.py            # Main bot orchestrator
│
├── logs/                         # Log files (generated)
├── data/                         # Market data cache (optional)
├── tests/                        # Unit tests (TODO)
│
├── main.py                       # Entry point
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
├── .env                          # Your configuration (gitignored)
├── .gitignore                    # Git ignore rules
│
├── README.md                     # Main documentation
├── SETUP_GUIDE.md                # Step-by-step setup
├── QUICK_REFERENCE.md            # Daily operations guide
├── PROJECT_STRUCTURE.md          # This file
└── trading_bot.db                # SQLite database (generated)
```

## Core Components

### 1. Configuration System ([src/config/](src/config/))

**Purpose**: Centralized settings management

**Key Features**:
- Environment variable loading
- Validation with Pydantic
- Type safety
- Default values

**Key Files**:
- [settings.py](src/config/settings.py:1): Settings class with validation

**Usage**:
```python
from src.config import settings

max_leverage = settings.max_leverage
trading_start = settings.get_trading_start_time()
```

---

### 2. Database Layer ([src/database/](src/database/))

**Purpose**: Persistent storage for all trading data

**Key Features**:
- SQLAlchemy ORM
- Automatic migrations (Alembic ready)
- Transaction management
- Dependency injection pattern

**Data Models**:
- `TradingSession`: Daily session tracking
- `Position`: Trade positions with full lifecycle
- `Order`: Order execution details
- `MarketData`: Historical price data
- `LLMAnalysis`: AI decision logs
- `StrategyPerformance`: Strategy metrics
- `BacktestRun`: Backtest results

**Key Files**:
- [models.py](src/database/models.py:1): All ORM models
- [database.py](src/database/database.py:1): Connection management

**Usage**:
```python
from src.database import db, Position

with db.session_scope() as session:
    positions = session.query(Position).filter(
        Position.status == PositionStatus.OPEN
    ).all()
```

---

### 3. Data Pipeline ([src/data_pipeline/](src/data_pipeline/))

**Purpose**: Real-time and historical market data

**Key Features**:
- Alpaca Premium integration
- Multiple timeframes (1min, 5min, 15min, etc.)
- Real-time quotes and bars
- Position management
- Order execution

**Key Files**:
- [alpaca_client.py](src/data_pipeline/alpaca_client.py:1): Unified Alpaca interface

**Usage**:
```python
from src.data_pipeline import alpaca_client

# Get bars
bars = alpaca_client.get_bars(['AAPL'], timeframe='5Min', limit=100)

# Get account
account = alpaca_client.get_account()

# Submit order
order = alpaca_client.submit_market_order('AAPL', qty=10, side='buy')
```

---

### 4. Trading Strategies ([src/strategies/](src/strategies/))

**Purpose**: Generate trading signals from market data

**Architecture**:
- Abstract base class defines interface
- Each strategy inherits from base
- Strategies calculate indicators
- Return Signal objects with strength rating

**Strategies**:

1. **Momentum Breakout** ([momentum_breakout_strategy.py](src/strategies/momentum_breakout_strategy.py:1))
   - Rides strong trends with volume
   - Entry: RSI > 60, MACD crossover, high volume
   - Exit: 3% profit or 1.5% loss
   - Best for: Volatile, trending markets

2. **Mean Reversion** ([mean_reversion_strategy.py](src/strategies/mean_reversion_strategy.py:1))
   - Exploits oversold/overbought extremes
   - Entry: RSI < 30 or > 70, Bollinger extremes
   - Exit: Return to mean or 2.5% profit
   - Best for: Range-bound markets

**Adding New Strategy**:
```python
from src.strategies.base_strategy import BaseStrategy, Signal

class MyStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("MyStrategy")

    def calculate_indicators(self, data):
        # Add indicators to DataFrame
        return data

    def analyze(self, symbol, data, account_info, positions):
        # Generate signal
        return Signal("buy", 0.8, "My reason")
```

---

### 5. Risk Management ([src/risk_management/](src/risk_management/))

**Purpose**: Protect capital with intelligent risk controls

**Key Features**:
- Position sizing based on equity and signal strength
- Automatic stop loss calculation
- Take profit targeting
- Trailing stops
- Daily loss limits
- Leverage restrictions
- Max position limits

**Key Files**:
- [risk_manager.py](src/risk_management/risk_manager.py:1): RiskManager class

**Safety Rules**:
- Max 15% per position
- Max 10 concurrent positions
- Max 4x leverage (high confidence only)
- 1.5-2% stop loss per trade
- -3% daily loss limit (auto-shutdown)
- 48 hour max hold time

**Usage**:
```python
from src.risk_management import RiskManager

risk_mgr = RiskManager(session)

# Calculate position size
qty, leverage = risk_mgr.calculate_position_size(
    symbol='AAPL',
    current_price=Decimal('180.00'),
    account_equity=Decimal('100000'),
    signal_strength=0.85,
    use_leverage=True
)

# Check if should close
should_close, reason = risk_mgr.should_close_position(
    position, current_price
)
```

---

### 6. Order Execution ([src/order_execution/](src/order_execution/))

**Purpose**: Execute trades with smart routing

**Key Features**:
- Bracket orders (entry + stop + target)
- Order tracking in database
- Position lifecycle management
- Automatic position updates
- Stale order cancellation

**Key Files**:
- [order_executor.py](src/order_execution/order_executor.py:1): OrderExecutor class

**Usage**:
```python
from src.order_execution import OrderExecutor

executor = OrderExecutor(session)

# Execute signal
position = executor.execute_signal(
    symbol='AAPL',
    signal=signal,
    account_info=account,
    current_session=session_obj,
    use_leverage=True
)

# Close position
executor.close_position(
    position=position,
    reason="Take profit hit",
    current_session=session_obj
)

# Update all positions
executor.update_positions(current_session)
```

---

### 7. LLM Integration ([src/llm_integration/](src/llm_integration/))

**Purpose**: AI-enhanced decision making

**Key Features**:
- Claude or GPT-4 integration
- Market condition analysis
- Trade validation
- Confidence scoring
- Decision logging

**Key Files**:
- [llm_analyzer.py](src/llm_integration/llm_analyzer.py:1): LLMAnalyzer class

**Usage**:
```python
from src.llm_integration import LLMAnalyzer

llm = LLMAnalyzer(session)

# Analyze market
analysis = llm.analyze_market_conditions(
    symbol='AAPL',
    market_data=market_data,
    technical_indicators=indicators,
    signal=signal
)

# Validate entry
should_enter, reason, confidence = llm.validate_entry(
    symbol='AAPL',
    signal=signal,
    market_data=market_data,
    account_info=account
)
```

---

### 8. Utilities ([src/utils/](src/utils/))

**Purpose**: Supporting functionality

**Components**:

1. **Logger** ([logger.py](src/utils/logger.py:1))
   - JSON structured logging
   - File + console output
   - Daily log rotation
   - Error tracking

2. **Scheduler** ([scheduler.py](src/utils/scheduler.py:1))
   - Timezone-aware scheduling
   - Automatic start/stop (14:25-21:05 London)
   - APScheduler integration

---

### 9. Main Orchestrator ([src/trading_bot.py](src/trading_bot.py:1))

**Purpose**: Coordinate all components

**Responsibilities**:
- Initialize all systems
- Manage trading sessions
- Main trading loop
- Scan for opportunities
- Execute trades
- Monitor positions
- Handle shutdown

**Flow**:
```
Initialize → Start Scheduler → Wait for Trading Hours
    ↓
Start Trading Session → Get Account Info → Create Session
    ↓
Trading Loop:
    - Update positions
    - Check daily limits
    - Scan symbols
    - Generate signals
    - Validate with LLM
    - Execute trades
    - Sleep 60s
    - Repeat
    ↓
Stop Trading → Close Positions → Log Summary
```

---

## Data Flow

### Trade Entry Flow

```
Market Data → Strategy Analysis → Signal
    ↓
LLM Validation → Enhanced Signal
    ↓
Risk Manager → Position Size + Stop/Target
    ↓
Order Executor → Submit to Alpaca
    ↓
Database → Record Position + Order
    ↓
Logs → Track Decision Process
```

### Position Monitoring Flow

```
Main Loop (every 60s)
    ↓
Get Current Prices → For Each Open Position
    ↓
Risk Manager → Check Exit Conditions
    ↓
Should Close? → Yes: Order Executor → Close Position
    ↓                 ↓
    No              Update Database with P&L
    Continue
```

## Key Design Principles

### 1. Dependency Injection
Services receive dependencies rather than creating them:
```python
class OrderExecutor:
    def __init__(self, session: Session):
        self.session = session
        self.risk_manager = RiskManager(session)
```

### 2. Separation of Concerns
Each module has single responsibility:
- Strategies: Generate signals
- Risk Manager: Control risk
- Order Executor: Execute orders
- Database: Persist data

### 3. Validate at Boundaries
Input validation at system boundaries:
- Settings: Pydantic validation
- API responses: Type checking
- Database: Constraints and validators

### 4. Fail Fast
Errors caught early with clear messages:
- Configuration validation on startup
- Database constraints
- Type hints throughout

### 5. Logging Everything
Comprehensive audit trail:
- All trades logged
- All decisions logged
- LLM analysis logged
- Errors logged with context

## Database Schema

### Core Tables

**trading_sessions**
- Tracks daily trading sessions
- Starting/ending equity
- P&L and statistics
- Win/loss counts

**positions**
- Individual trades
- Entry/exit details
- Stop loss and take profit
- Strategy and reasoning

**orders**
- Order execution details
- Alpaca order IDs
- Fill prices and quantities
- Commissions and slippage

**llm_analysis**
- LLM decision logs
- Prompts and responses
- Confidence scores
- Actions taken

**market_data**
- Historical OHLCV data
- For backtesting
- Multiple timeframes

## Testing Strategy

### Manual Testing
1. Paper trading validation
2. Monitor for 1 week minimum
3. Review all decisions
4. Verify risk controls

### Future: Automated Testing
- Unit tests for strategies
- Integration tests for order flow
- Backtesting on historical data
- Performance regression tests

## Performance Optimization

### Current Optimizations
- Database connection pooling
- Efficient SQL queries with indexes
- Batch processing where possible
- Caching of market data

### Future Optimizations
- Parallel strategy evaluation
- Async API calls
- Redis caching
- Database partitioning

## Security Considerations

### API Keys
- Stored in `.env` (gitignored)
- Never committed to version control
- Separate keys for paper/live

### Database
- Local SQLite for development
- PostgreSQL for production
- Regular backups
- No sensitive data in logs

### Risk Controls
- Multiple safety limits
- Automatic shutdowns
- Manual emergency stop
- Position size caps

---

## Getting Started

1. Read [SETUP_GUIDE.md](SETUP_GUIDE.md) for installation
2. Read [README.md](README.md) for overview
3. Use [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for daily ops
4. Refer to this file for architecture details

## Support

For detailed information on specific components, see inline documentation in source files. All major classes and functions include comprehensive docstrings.
