"""
Configuration management using Pydantic Settings.
Validates and manages all bot configuration from environment variables.
"""
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from datetime import time
import pytz


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Alpaca Configuration
    alpaca_api_key: str = Field(..., description="Alpaca API key")
    alpaca_secret_key: str = Field(..., description="Alpaca secret key")
    alpaca_base_url: str = Field(
        default="https://paper-api.alpaca.markets",
        description="Alpaca API base URL"
    )

    # LLM Configuration
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    llm_provider: str = Field(default="anthropic", description="LLM provider (anthropic or openai)")
    llm_model: str = Field(default="claude-sonnet-4-5-20250929", description="LLM model name")

    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./trading_bot.db",
        description="Database connection URL"
    )

    # Trading Configuration
    max_position_size_pct: float = Field(
        default=0.15,
        ge=0.01,
        le=0.5,
        description="Maximum position size as percentage of portfolio"
    )
    max_leverage: float = Field(
        default=4.0,
        ge=1.0,
        le=4.0,
        description="Maximum leverage multiplier"
    )
    daily_profit_target: float = Field(
        default=0.05,
        ge=0.01,
        description="Daily profit target (5% = 0.05)"
    )
    max_daily_loss: float = Field(
        default=-0.03,
        le=0.0,
        description="Maximum daily loss before stopping (negative value)"
    )
    max_position_hold_hours: int = Field(
        default=48,
        ge=1,
        description="Maximum hours to hold a position"
    )

    # Trading Schedule
    trading_start_time: str = Field(default="14:25", description="Trading start time HH:MM")
    trading_end_time: str = Field(default="21:05", description="Trading end time HH:MM")
    timezone: str = Field(default="Europe/London", description="Timezone for trading schedule")

    # Risk Management
    stop_loss_pct: float = Field(
        default=0.02,
        ge=0.005,
        le=0.1,
        description="Stop loss percentage per position"
    )
    take_profit_pct: float = Field(
        default=0.04,
        ge=0.01,
        le=0.2,
        description="Take profit percentage per position"
    )
    trailing_stop_pct: float = Field(
        default=0.015,
        ge=0.005,
        le=0.05,
        description="Trailing stop percentage"
    )
    max_concurrent_positions: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum concurrent positions"
    )
    min_volume_threshold: int = Field(
        default=1000000,
        ge=10000,
        description="Minimum daily volume for tradeable symbols"
    )

    # Strategy Parameters
    rsi_oversold: int = Field(default=30, ge=10, le=40)
    rsi_overbought: int = Field(default=70, ge=60, le=90)
    macd_fast: int = Field(default=12, ge=5, le=20)
    macd_slow: int = Field(default=26, ge=20, le=40)
    macd_signal: int = Field(default=9, ge=5, le=15)
    bollinger_period: int = Field(default=20, ge=10, le=50)
    bollinger_std: float = Field(default=2.0, ge=1.0, le=3.0)

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(default="trading_bot.log", description="Log file name")

    # Symbol Configuration
    symbol_universe: List[str] = Field(
        default_factory=lambda: [
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AMD", "NFLX", "ADBE",
            "CRM", "ORCL", "INTC", "CSCO", "AVGO", "TXN", "QCOM", "AMAT", "MU", "LRCX",
            "SPY", "QQQ", "IWM", "DIA", "XLF", "XLE", "XLK", "XLV", "XLI", "XLP",
            "JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "SCHW", "AXP", "V",
            "MA", "PYPL", "SQ", "COIN", "HOOD", "SOFI", "ABNB", "UBER", "LYFT", "DASH",
            "BA", "CAT", "DE", "GE", "HON", "LMT", "RTX", "UNP", "UPS", "FDX",
            "CVX", "XOM", "SLB", "COP", "EOG", "OXY", "HAL", "PSX", "VLO", "MPC",
            "DIS", "CMCSA", "T", "VZ", "TMUS", "CHTR", "NKE", "SBUX", "MCD", "CMG",
            "PFE", "JNJ", "UNH", "ABBV", "LLY", "MRK", "TMO", "ABT", "DHR", "BMY",
            "SHOP", "SQ", "SNOW", "DDOG", "CRWD", "ZS", "NET"
        ],
        description="Universe of tradeable symbols"
    )

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        """Validate timezone string."""
        try:
            pytz.timezone(v)
            return v
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"Invalid timezone: {v}")

    @field_validator("trading_start_time", "trading_end_time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """Validate time format HH:MM."""
        try:
            parts = v.split(":")
            if len(parts) != 2:
                raise ValueError
            hours, minutes = int(parts[0]), int(parts[1])
            if not (0 <= hours < 24 and 0 <= minutes < 60):
                raise ValueError
            return v
        except (ValueError, IndexError):
            raise ValueError(f"Invalid time format: {v}. Expected HH:MM")

    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        """Validate LLM provider."""
        if v.lower() not in ["anthropic", "openai"]:
            raise ValueError(f"Invalid LLM provider: {v}. Must be 'anthropic' or 'openai'")
        return v.lower()

    def get_trading_start_time(self) -> time:
        """Get trading start time as datetime.time object."""
        hours, minutes = map(int, self.trading_start_time.split(":"))
        return time(hour=hours, minute=minutes)

    def get_trading_end_time(self) -> time:
        """Get trading end time as datetime.time object."""
        hours, minutes = map(int, self.trading_end_time.split(":"))
        return time(hour=hours, minute=minutes)

    def get_timezone(self) -> pytz.timezone:
        """Get timezone object."""
        return pytz.timezone(self.timezone)


# Global settings instance
settings = Settings()
