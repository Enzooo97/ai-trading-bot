"""
Logging configuration with structured JSON logging.
Provides comprehensive logging for all bot activities.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from pythonjsonlogger import jsonlogger
from src.config import settings


def setup_logging():
    """Configure logging for the trading bot."""
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Create log filename with date
    log_date = datetime.now().strftime("%Y%m%d")
    log_file = log_dir / f"{settings.log_file.replace('.log', '')}_{log_date}.log"

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler with formatted output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)

    # File handler with JSON logging
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    json_formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d'
    )
    file_handler.setFormatter(json_formatter)

    # Add handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Suppress noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('alpaca').setLevel(logging.INFO)
    logging.getLogger('anthropic').setLevel(logging.INFO)
    logging.getLogger('openai').setLevel(logging.INFO)

    logging.info("Logging configured successfully")
    logging.info(f"Log file: {log_file}")
