#!/usr/bin/env python3
"""
Trading Bot - Aggressive Daily Scalping with LLM Integration

Main entry point for the trading bot.
Runs automated trading from 14:25 to 21:05 London time.

Target: 5%+ daily profit through aggressive scalping.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.trading_bot import main

if __name__ == "__main__":
    main()
