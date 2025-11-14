"""
Database models for trading bot.
Stores all trading data, positions, orders, market data, and backtesting results.
"""
from datetime import datetime
from typing import Optional
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text,
    ForeignKey, Index, Numeric, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class OrderSide(enum.Enum):
    """Order side enum."""
    BUY = "buy"
    SELL = "sell"


class OrderType(enum.Enum):
    """Order type enum."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class OrderStatus(enum.Enum):
    """Order status enum."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    FAILED = "failed"


class PositionStatus(enum.Enum):
    """Position status enum."""
    OPEN = "open"
    CLOSED = "closed"
    STOPPED_OUT = "stopped_out"
    PROFIT_TAKEN = "profit_taken"


class TradingSession(Base):
    """Trading session tracking."""
    __tablename__ = "trading_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_date = Column(DateTime, nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    starting_equity = Column(Numeric(precision=15, scale=2), nullable=False)
    ending_equity = Column(Numeric(precision=15, scale=2), nullable=True)
    pnl = Column(Numeric(precision=15, scale=2), nullable=True)
    pnl_pct = Column(Float, nullable=True)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    max_drawdown = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    positions = relationship("Position", back_populates="session", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_session_date_active", "session_date", "is_active"),
    )


class Position(Base):
    """Position tracking with full lifecycle management."""
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("trading_sessions.id"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(SQLEnum(OrderSide), nullable=False)
    status = Column(SQLEnum(PositionStatus), nullable=False, default=PositionStatus.OPEN, index=True)

    # Entry details
    entry_price = Column(Numeric(precision=15, scale=4), nullable=False)
    entry_time = Column(DateTime, nullable=False, index=True)
    quantity = Column(Numeric(precision=15, scale=4), nullable=False)
    leverage = Column(Float, default=1.0)
    entry_order_id = Column(String(100), nullable=True)

    # Exit details
    exit_price = Column(Numeric(precision=15, scale=4), nullable=True)
    exit_time = Column(DateTime, nullable=True)
    exit_order_id = Column(String(100), nullable=True)

    # Risk management
    stop_loss_price = Column(Numeric(precision=15, scale=4), nullable=True)
    take_profit_price = Column(Numeric(precision=15, scale=4), nullable=True)
    trailing_stop_pct = Column(Float, nullable=True)
    highest_price = Column(Numeric(precision=15, scale=4), nullable=True)  # For trailing stop
    lowest_price = Column(Numeric(precision=15, scale=4), nullable=True)

    # Performance metrics
    pnl = Column(Numeric(precision=15, scale=2), nullable=True)
    pnl_pct = Column(Float, nullable=True)
    commission = Column(Numeric(precision=15, scale=4), default=0)

    # Strategy information
    strategy_name = Column(String(100), nullable=True, index=True)
    entry_reason = Column(Text, nullable=True)
    exit_reason = Column(Text, nullable=True)
    llm_analysis = Column(Text, nullable=True)  # LLM decision reasoning

    # Metadata
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    session = relationship("TradingSession", back_populates="positions")
    orders = relationship("Order", back_populates="position", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_symbol_status", "symbol", "status"),
        Index("idx_entry_time", "entry_time"),
    )


class Order(Base):
    """Order tracking with complete execution details."""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("trading_sessions.id"), nullable=False, index=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=True, index=True)

    # Order details
    alpaca_order_id = Column(String(100), unique=True, nullable=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(SQLEnum(OrderSide), nullable=False)
    order_type = Column(SQLEnum(OrderType), nullable=False)
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING, index=True)

    # Quantity and pricing
    quantity = Column(Numeric(precision=15, scale=4), nullable=False)
    filled_quantity = Column(Numeric(precision=15, scale=4), default=0)
    limit_price = Column(Numeric(precision=15, scale=4), nullable=True)
    stop_price = Column(Numeric(precision=15, scale=4), nullable=True)
    filled_avg_price = Column(Numeric(precision=15, scale=4), nullable=True)

    # Timing
    submitted_at = Column(DateTime, nullable=True)
    filled_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)

    # Execution details
    commission = Column(Numeric(precision=15, scale=4), default=0)
    slippage = Column(Numeric(precision=15, scale=4), nullable=True)

    # Context
    reason = Column(Text, nullable=True)  # Why order was placed
    error_message = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    session = relationship("TradingSession", back_populates="orders")
    position = relationship("Position", back_populates="orders")

    __table_args__ = (
        Index("idx_symbol_status", "symbol", "status"),
        Index("idx_created_at", "created_at"),
    )


class MarketData(Base):
    """Market data storage for backtesting and analysis."""
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)  # 1min, 5min, 15min, 1hour, 1day

    # OHLCV data
    open = Column(Numeric(precision=15, scale=4), nullable=False)
    high = Column(Numeric(precision=15, scale=4), nullable=False)
    low = Column(Numeric(precision=15, scale=4), nullable=False)
    close = Column(Numeric(precision=15, scale=4), nullable=False)
    volume = Column(Numeric(precision=20, scale=2), nullable=False)

    # Additional metrics
    vwap = Column(Numeric(precision=15, scale=4), nullable=True)
    trade_count = Column(Integer, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_symbol_timestamp_timeframe", "symbol", "timestamp", "timeframe", unique=True),
    )


class StrategyPerformance(Base):
    """Strategy performance tracking."""
    __tablename__ = "strategy_performance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_name = Column(String(100), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)

    # Performance metrics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, nullable=True)
    avg_win = Column(Numeric(precision=15, scale=2), nullable=True)
    avg_loss = Column(Numeric(precision=15, scale=2), nullable=True)
    profit_factor = Column(Float, nullable=True)
    total_pnl = Column(Numeric(precision=15, scale=2), nullable=True)
    max_drawdown = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_strategy_date", "strategy_name", "date"),
    )


class LLMAnalysis(Base):
    """LLM analysis and decision logging."""
    __tablename__ = "llm_analysis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    analysis_type = Column(String(50), nullable=False)  # market_analysis, entry_decision, exit_decision

    # Input context
    prompt = Column(Text, nullable=False)
    market_context = Column(Text, nullable=True)  # JSON serialized market data

    # LLM response
    llm_provider = Column(String(20), nullable=False)
    llm_model = Column(String(50), nullable=False)
    response = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=True)

    # Action taken
    action_taken = Column(String(50), nullable=True)  # buy, sell, hold, close
    position_id = Column(Integer, nullable=True)

    # Metadata
    processing_time_ms = Column(Integer, nullable=True)
    token_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_symbol_timestamp", "symbol", "timestamp"),
        Index("idx_analysis_type", "analysis_type"),
    )


class BacktestRun(Base):
    """Backtesting results storage."""
    __tablename__ = "backtest_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_name = Column(String(200), nullable=False)
    strategy_name = Column(String(100), nullable=False, index=True)

    # Backtest parameters
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Numeric(precision=15, scale=2), nullable=False)
    symbols = Column(Text, nullable=False)  # JSON serialized list
    parameters = Column(Text, nullable=True)  # JSON serialized strategy parameters

    # Results
    final_equity = Column(Numeric(precision=15, scale=2), nullable=True)
    total_return = Column(Float, nullable=True)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, nullable=True)
    profit_factor = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    avg_trade_duration_hours = Column(Float, nullable=True)

    # Metadata
    execution_time_seconds = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_strategy_created", "strategy_name", "created_at"),
    )
