#!/usr/bin/env python3
"""
LLM Enhancement Comparison Backtest.

Compares Momentum Breakout strategy performance:
1. Base strategy (no LLM)
2. LLM-enhanced strategy (with market regime + trade scoring)

This shows the actual impact of LLM integration on strategy performance.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils import setup_logging
from src.backtesting import BacktestEngine
from src.strategies.momentum_breakout_strategy import MomentumBreakoutStrategy
from src.strategies.momentum_breakout_llm import MomentumBreakoutLLM

import logging
logger = logging.getLogger(__name__)


def print_metrics(strategy_name: str, metrics, detailed=True):
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

    if detailed:
        print("\nTRADE CHARACTERISTICS:")
        print(f"  Avg Hold Time:       {metrics.avg_hold_duration_minutes:>8.1f} minutes")
        print(f"  Max Consecutive Wins: {metrics.max_consecutive_wins:>7}")
        print(f"  Max Consecutive Loss: {metrics.max_consecutive_losses:>7}")

        print("\nDAILY STATS:")
        print(f"  Best Day:            {metrics.best_day_pct*100:>8.2f}%")
        print(f"  Worst Day:           {metrics.worst_day_pct*100:>8.2f}%")

    print(f"{'='*70}\n")


def run_comparison_backtest(
    symbols: list = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA'],
    days: int = 180,
):
    """Run comparison backtest between base and LLM strategies."""

    setup_logging()

    print("\n" + "="*70)
    print("LLM ENHANCEMENT COMPARISON BACKTEST")
    print("="*70)

    # Date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    print(f"\nTest Configuration:")
    print(f"  Symbols:        {', '.join(symbols)}")
    print(f"  Period:         {start_date.date()} to {end_date.date()} ({days} days)")
    print(f"  Timeframe:      5Min")
    print(f"  Initial Capital: $100,000")
    print(f"  LLM Model:      Claude 3 Haiku")
    print(f"  Score Threshold: 70/100")

    # Test 1: Base Momentum Breakout (no LLM)
    print(f"\n{'='*70}")
    print("TEST 1: BASE MOMENTUM BREAKOUT (No LLM)")
    print(f"{'='*70}")
    print("Running backtest... (this may take 5-10 minutes)")

    strategy_base = MomentumBreakoutStrategy()
    engine_base = BacktestEngine(initial_capital=100000.0)

    metrics_base, trades_base, equity_base = engine_base.run_backtest(
        strategy=strategy_base,
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        timeframe="5Min",
    )

    print_metrics("Momentum Breakout (Base)", metrics_base, detailed=True)

    # Sample trades
    if trades_base:
        print("Sample Trades (First 5):")
        print("-" * 70)
        for trade in trades_base[:5]:
            print(f"  {trade.exit_time.strftime('%Y-%m-%d %H:%M')} | "
                  f"{trade.symbol:6} | {trade.side:4} | "
                  f"P&L: ${trade.pnl:+8.2f} ({trade.pnl_pct*100:+6.2f}%) | "
                  f"{trade.hold_duration_minutes:.0f}min")

    # Test 2: LLM-Enhanced Momentum Breakout
    print(f"\n\n{'='*70}")
    print("TEST 2: LLM-ENHANCED MOMENTUM BREAKOUT")
    print(f"{'='*70}")
    print("Running backtest with LLM filtering...")
    print("NOTE: This will be slower due to LLM API calls (caching helps)")
    print("      Expect ~2 seconds per signal evaluation")

    strategy_llm = MomentumBreakoutLLM(use_llm=True, llm_score_threshold=70)
    engine_llm = BacktestEngine(initial_capital=100000.0)

    metrics_llm, trades_llm, equity_llm = engine_llm.run_backtest(
        strategy=strategy_llm,
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        timeframe="5Min",
    )

    print_metrics("Momentum Breakout (LLM-Enhanced)", metrics_llm, detailed=True)

    # Sample trades
    if trades_llm:
        print("Sample Trades (First 5):")
        print("-" * 70)
        for trade in trades_llm[:5]:
            print(f"  {trade.exit_time.strftime('%Y-%m-%d %H:%M')} | "
                  f"{trade.symbol:6} | {trade.side:4} | "
                  f"P&L: ${trade.pnl:+8.2f} ({trade.pnl_pct*100:+6.2f}%) | "
                  f"{trade.hold_duration_minutes:.0f}min")

    # Comparison Summary
    print(f"\n\n{'='*70}")
    print("COMPARISON SUMMARY")
    print(f"{'='*70}\n")

    # Calculate improvements
    return_improvement = ((metrics_llm.total_return_pct - metrics_base.total_return_pct) /
                          abs(metrics_base.total_return_pct) * 100 if metrics_base.total_return_pct != 0 else 0)

    win_rate_change = (metrics_llm.win_rate - metrics_base.win_rate) * 100

    trades_filtered = metrics_base.total_trades - metrics_llm.total_trades
    filter_rate = (trades_filtered / metrics_base.total_trades * 100) if metrics_base.total_trades > 0 else 0

    sharpe_improvement = metrics_llm.sharpe_ratio - metrics_base.sharpe_ratio

    print("Performance Comparison:")
    print(f"{'Metric':<30} {'Base':>15} {'LLM':>15} {'Change':>15}")
    print("-" * 75)
    print(f"{'Total Return':<30} {metrics_base.total_return_pct*100:>14.2f}% {metrics_llm.total_return_pct*100:>14.2f}% {return_improvement:>14.1f}%")
    print(f"{'Annualized Return':<30} {metrics_base.annualized_return_pct*100:>14.2f}% {metrics_llm.annualized_return_pct*100:>14.2f}%")
    print(f"{'Win Rate':<30} {metrics_base.win_rate*100:>14.1f}% {metrics_llm.win_rate*100:>14.1f}% {win_rate_change:>+14.1f}%")
    print(f"{'Total Trades':<30} {metrics_base.total_trades:>15} {metrics_llm.total_trades:>15} {-trades_filtered:>15}")
    print(f"{'Sharpe Ratio':<30} {metrics_base.sharpe_ratio:>15.2f} {metrics_llm.sharpe_ratio:>15.2f} {sharpe_improvement:>+15.2f}")
    print(f"{'Max Drawdown':<30} {metrics_base.max_drawdown_pct*100:>14.2f}% {metrics_llm.max_drawdown_pct*100:>14.2f}%")
    print(f"{'Profit Factor':<30} {metrics_base.profit_factor:>15.2f} {metrics_llm.profit_factor:>15.2f}")

    print(f"\n{'='*75}")

    print("\nKey Insights:")
    print(f"  • LLM filtered {trades_filtered} trades ({filter_rate:.1f}% of signals)")
    print(f"  • Return improvement: {return_improvement:+.1f}%")
    print(f"  • Win rate change: {win_rate_change:+.1f} percentage points")
    print(f"  • Sharpe ratio change: {sharpe_improvement:+.2f}")

    if return_improvement > 10:
        print("\n  [+] LLM significantly improved performance!")
    elif return_improvement > 0:
        print("\n  [+] LLM moderately improved performance")
    else:
        print("\n  [-] LLM did not improve performance (may need tuning)")

    print(f"\n{'='*70}")
    print("Backtest Complete!")
    print(f"{'='*70}\n")

    return {
        'base': {'metrics': metrics_base, 'trades': trades_base},
        'llm': {'metrics': metrics_llm, 'trades': trades_llm},
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compare LLM-enhanced vs base strategy")
    parser.add_argument('--days', type=int, default=90, help='Days to backtest (default: 90)')
    parser.add_argument('--symbols', nargs='+', default=['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA'],
                       help='Symbols to test')

    args = parser.parse_args()

    results = run_comparison_backtest(symbols=args.symbols, days=args.days)
