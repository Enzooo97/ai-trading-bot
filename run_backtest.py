#!/usr/bin/env python3
"""
Backtest runner script.
Tests trading strategies on historical data and generates performance reports.

Usage:
    python run_backtest.py --strategy VWAP --symbols AAPL MSFT --days 30
    python run_backtest.py --strategy all --days 90
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils import setup_logging
from src.backtesting import BacktestEngine
from src.strategies import (
    VWAPStrategy, EMATripleCrossoverStrategy, StochasticRSIStrategy,
    MomentumBreakoutStrategy, MeanReversionStrategy
)

import logging
logger = logging.getLogger(__name__)


def run_single_backtest(
    strategy_class,
    symbols: list,
    days: int,
    timeframe: str = "5Min",
):
    """Run backtest for a single strategy."""
    # Initialize
    strategy = strategy_class()
    engine = BacktestEngine(initial_capital=100000.0)

    # Date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    print(f"\n{'='*70}")
    print(f"BACKTESTING: {strategy.name}")
    print(f"{'='*70}")
    print(f"Symbols: {', '.join(symbols)}")
    print(f"Period: {start_date.date()} to {end_date.date()} ({days} days)")
    print(f"Timeframe: {timeframe}")
    print(f"Initial Capital: $100,000")
    print(f"{'='*70}\n")

    # Run backtest
    metrics, trades, equity_curve = engine.run_backtest(
        strategy=strategy,
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        timeframe=timeframe,
    )

    # Print results
    print_metrics(strategy.name, metrics)

    # Print sample trades
    if trades:
        print("\nSample Trades (First 5):")
        print("-" * 70)
        for trade in trades[:5]:
            print(f"  {trade.exit_time.strftime('%Y-%m-%d %H:%M')} | "
                  f"{trade.symbol:6} | {trade.side:4} | "
                  f"P&L: ${trade.pnl:+8.2f} ({trade.pnl_pct*100:+6.2f}%) | "
                  f"{trade.hold_duration_minutes:.0f}min")

    return metrics, trades, equity_curve


def print_metrics(strategy_name: str, metrics):
    """Print formatted backtest metrics."""
    print(f"\n{'='*70}")
    print(f"RESULTS: {strategy_name}")
    print(f"{'='*70}")

    print("\nRETURNS:")
    print(f"  Total Return:        {metrics.total_return_pct*100:>8.2f}%")
    print(f"  Annualized Return:   {metrics.annualized_return_pct*100:>8.2f}%")

    print("\nTRADES:")
    print(f"  Total Trades:        {metrics.total_trades:>8}")
    print(f"  Winning Trades:      {metrics.winning_trades:>8} ({metrics.win_rate*100:.1f}%)")
    print(f"  Losing Trades:       {metrics.losing_trades:>8}")
    print(f"  Avg Trades/Day:      {metrics.avg_trades_per_day:>8.1f}")

    print("\nPROFITABILITY:")
    print(f"  Avg Win:            ${metrics.avg_win:>8.2f}")
    print(f"  Avg Loss:           ${metrics.avg_loss:>8.2f}")
    print(f"  Profit Factor:       {metrics.profit_factor:>8.2f}")
    print(f"  Avg Trade P&L:      ${metrics.avg_trade_pnl:>8.2f}")

    print("\nRISK METRICS:")
    print(f"  Max Drawdown:        {metrics.max_drawdown_pct*100:>8.2f}%")
    print(f"  Sharpe Ratio:        {metrics.sharpe_ratio:>8.2f}")
    print(f"  Sortino Ratio:       {metrics.sortino_ratio:>8.2f}")

    print("\nTRADE CHARACTERISTICS:")
    print(f"  Avg Hold Time:       {metrics.avg_hold_duration_minutes:>8.1f} minutes")
    print(f"  Max Consecutive Wins: {metrics.max_consecutive_wins:>7}")
    print(f"  Max Consecutive Loss: {metrics.max_consecutive_losses:>7}")

    print("\nDAILY STATS:")
    print(f"  Best Day:            {metrics.best_day_pct*100:>8.2f}%")
    print(f"  Worst Day:           {metrics.worst_day_pct*100:>8.2f}%")

    print(f"{'='*70}\n")


def run_all_strategies(symbols: list, days: int):
    """Run backtests for all strategies and compare."""
    strategies = [
        VWAPStrategy,
        EMATripleCrossoverStrategy,
        StochasticRSIStrategy,
        MomentumBreakoutStrategy,
        MeanReversionStrategy,
    ]

    results = []

    for strategy_class in strategies:
        metrics, trades, equity_curve = run_single_backtest(
            strategy_class, symbols, days
        )
        results.append({
            'strategy': strategy_class().name,
            'metrics': metrics,
        })

    # Print comparison
    print("\n" + "="*90)
    print("STRATEGY COMPARISON")
    print("="*90)
    print(f"{'Strategy':<30} {'Return':>10} {'Win Rate':>10} {'Trades':>8} {'Sharpe':>8} {'Max DD':>10}")
    print("-"*90)

    for result in results:
        m = result['metrics']
        print(f"{result['strategy']:<30} "
              f"{m.total_return_pct*100:>9.2f}% "
              f"{m.win_rate*100:>9.1f}% "
              f"{m.total_trades:>8} "
              f"{m.sharpe_ratio:>8.2f} "
              f"{m.max_drawdown_pct*100:>9.2f}%")

    print("="*90 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Backtest trading strategies")

    parser.add_argument(
        '--strategy',
        type=str,
        default='all',
        choices=['all', 'vwap', 'ema', 'stochastic', 'momentum', 'meanrev'],
        help='Strategy to test'
    )

    parser.add_argument(
        '--symbols',
        nargs='+',
        default=['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA'],
        help='Symbols to trade'
    )

    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days to backtest'
    )

    parser.add_argument(
        '--timeframe',
        type=str,
        default='5Min',
        choices=['1Min', '5Min', '15Min', '30Min', '1Hour'],
        help='Bar timeframe'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging()

    print("\n" + "="*70)
    print("TRADING STRATEGY BACKTESTING SYSTEM")
    print("="*70)

    # Strategy mapping
    strategy_map = {
        'vwap': VWAPStrategy,
        'ema': EMATripleCrossoverStrategy,
        'stochastic': StochasticRSIStrategy,
        'momentum': MomentumBreakoutStrategy,
        'meanrev': MeanReversionStrategy,
    }

    # Run backtest
    if args.strategy == 'all':
        run_all_strategies(args.symbols, args.days)
    else:
        strategy_class = strategy_map[args.strategy]
        run_single_backtest(strategy_class, args.symbols, args.days, args.timeframe)

    print("\n[COMPLETE] Backtesting complete!\n")


if __name__ == "__main__":
    main()
