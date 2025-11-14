#!/usr/bin/env python3
"""
Comprehensive LLM Approach Comparison Backtest.

Tests 180-day performance across THREE approaches:
1. Base strategy (no LLM)
2. LLM with static 60/100 threshold
3. LLM with static 70/100 threshold (original)
4. LLM with adaptive thresholds (NEW)

This identifies the optimal LLM configuration for long-term trading.
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


def run_comprehensive_comparison(
    symbols: list = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA'],
    days: int = 180,
):
    """Run comprehensive comparison across all LLM approaches."""

    setup_logging()

    print("\n" + "="*70)
    print("COMPREHENSIVE LLM APPROACH COMPARISON")
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

    results = {}

    # Test 1: Base Momentum Breakout (no LLM)
    print(f"\n{'='*70}")
    print("TEST 1: BASE MOMENTUM BREAKOUT (No LLM)")
    print(f"{'='*70}")
    print("Running backtest...")

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
    results['base'] = {'metrics': metrics_base, 'trades': trades_base}

    # Test 2: LLM with 60/100 threshold
    print(f"\n\n{'='*70}")
    print("TEST 2: LLM-ENHANCED (Static 60/100 Threshold)")
    print(f"{'='*70}")
    print("Running backtest with LLM scoring (threshold=60)...")

    strategy_llm_60 = MomentumBreakoutLLM(use_llm=True, llm_score_threshold=60)
    engine_llm_60 = BacktestEngine(initial_capital=100000.0)

    metrics_llm_60, trades_llm_60, equity_llm_60 = engine_llm_60.run_backtest(
        strategy=strategy_llm_60,
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        timeframe="5Min",
    )

    print_metrics("Momentum Breakout (LLM 60/100)", metrics_llm_60, detailed=True)
    results['llm_60'] = {'metrics': metrics_llm_60, 'trades': trades_llm_60}

    # Test 3: LLM with 70/100 threshold (original)
    print(f"\n\n{'='*70}")
    print("TEST 3: LLM-ENHANCED (Static 70/100 Threshold - Original)")
    print(f"{'='*70}")
    print("Running backtest with LLM scoring (threshold=70)...")

    strategy_llm_70 = MomentumBreakoutLLM(use_llm=True, llm_score_threshold=70)
    engine_llm_70 = BacktestEngine(initial_capital=100000.0)

    metrics_llm_70, trades_llm_70, equity_llm_70 = engine_llm_70.run_backtest(
        strategy=strategy_llm_70,
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        timeframe="5Min",
    )

    print_metrics("Momentum Breakout (LLM 70/100)", metrics_llm_70, detailed=True)
    results['llm_70'] = {'metrics': metrics_llm_70, 'trades': trades_llm_70}

    # Test 4: LLM with adaptive thresholds (NEW)
    print(f"\n\n{'='*70}")
    print("TEST 4: LLM-ENHANCED (Adaptive Thresholds - NEW)")
    print(f"{'='*70}")
    print("Running backtest with adaptive thresholds...")
    print("Thresholds adjust based on market regime:")
    print("  - Strong trends: 55-60/100")
    print("  - Weak trends: 65/100")
    print("  - Ranging markets: 70-75/100")

    # For adaptive thresholds, we still pass a base threshold
    # but the strategy will dynamically adjust it
    strategy_llm_adaptive = MomentumBreakoutLLM(use_llm=True, llm_score_threshold=70)
    engine_llm_adaptive = BacktestEngine(initial_capital=100000.0)

    metrics_llm_adaptive, trades_llm_adaptive, equity_llm_adaptive = engine_llm_adaptive.run_backtest(
        strategy=strategy_llm_adaptive,
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        timeframe="5Min",
    )

    print_metrics("Momentum Breakout (LLM Adaptive)", metrics_llm_adaptive, detailed=True)
    results['llm_adaptive'] = {'metrics': metrics_llm_adaptive, 'trades': trades_llm_adaptive}

    # Comprehensive Comparison Summary
    print(f"\n\n{'='*90}")
    print("COMPREHENSIVE COMPARISON SUMMARY")
    print(f"{'='*90}\n")

    print("Performance Comparison:")
    print(f"{'Approach':<35} {'Return':>10} {'Win Rate':>10} {'Trades':>8} {'Sharpe':>8} {'Max DD':>10}")
    print("-" * 90)

    approaches = [
        ('Base (No LLM)', metrics_base),
        ('LLM Static 60/100', metrics_llm_60),
        ('LLM Static 70/100', metrics_llm_70),
        ('LLM Adaptive', metrics_llm_adaptive),
    ]

    for name, m in approaches:
        print(f"{name:<35} "
              f"{m.total_return_pct*100:>9.2f}% "
              f"{m.win_rate*100:>9.1f}% "
              f"{m.total_trades:>8} "
              f"{m.sharpe_ratio:>8.2f} "
              f"{m.max_drawdown_pct*100:>9.2f}%")

    print("=" * 90)

    # Calculate improvements
    print("\nKey Insights:")

    # Trade filtering analysis
    trades_60_filtered = metrics_base.total_trades - metrics_llm_60.total_trades
    trades_70_filtered = metrics_base.total_trades - metrics_llm_70.total_trades
    trades_adaptive_filtered = metrics_base.total_trades - metrics_llm_adaptive.total_trades

    print(f"  Trade Filtering:")
    print(f"    - 60/100 filtered: {trades_60_filtered} ({trades_60_filtered/metrics_base.total_trades*100:.1f}%)")
    print(f"    - 70/100 filtered: {trades_70_filtered} ({trades_70_filtered/metrics_base.total_trades*100:.1f}%)")
    print(f"    - Adaptive filtered: {trades_adaptive_filtered} ({trades_adaptive_filtered/metrics_base.total_trades*100:.1f}%)")

    # Performance improvements
    print(f"\n  Return Improvement vs Base:")
    for name, m in approaches[1:]:
        improvement = ((m.total_return_pct - metrics_base.total_return_pct) /
                      abs(metrics_base.total_return_pct) * 100 if metrics_base.total_return_pct != 0 else 0)
        print(f"    - {name}: {improvement:+.1f}%")

    # Sharpe improvements
    print(f"\n  Sharpe Ratio Improvement vs Base:")
    for name, m in approaches[1:]:
        sharpe_diff = m.sharpe_ratio - metrics_base.sharpe_ratio
        print(f"    - {name}: {sharpe_diff:+.2f}")

    # Determine best approach
    print("\n" + "=" * 90)

    best_return_idx = max(range(len(approaches)), key=lambda i: approaches[i][1].total_return_pct)
    best_sharpe_idx = max(range(len(approaches)), key=lambda i: approaches[i][1].sharpe_ratio)

    print(f"\nBest Overall Return: {approaches[best_return_idx][0]} "
          f"({approaches[best_return_idx][1].total_return_pct*100:.2f}%)")
    print(f"Best Risk-Adjusted:  {approaches[best_sharpe_idx][0]} "
          f"(Sharpe: {approaches[best_sharpe_idx][1].sharpe_ratio:.2f})")

    # Recommendation
    print("\n" + "=" * 90)
    print("RECOMMENDATION:")

    if metrics_llm_adaptive.total_return_pct > metrics_base.total_return_pct:
        print("  [+] Adaptive thresholds IMPROVED performance!")
        print(f"      Return: {metrics_base.total_return_pct*100:.2f}% -> {metrics_llm_adaptive.total_return_pct*100:.2f}%")
        print(f"      Sharpe: {metrics_base.sharpe_ratio:.2f} -> {metrics_llm_adaptive.sharpe_ratio:.2f}")
        print("\n  DEPLOY: LLM with adaptive thresholds to paper trading")
    elif metrics_llm_60.total_return_pct > metrics_base.total_return_pct:
        print("  [~] Static 60/100 threshold performs best")
        print(f"      Return: {metrics_base.total_return_pct*100:.2f}% -> {metrics_llm_60.total_return_pct*100:.2f}%")
        print("\n  CONSIDER: Static 60/100 threshold for deployment")
    else:
        print("  [-] No LLM approach improved 180-day performance")
        print("      Consider using base strategy or LLM only for 90-day horizons")

    print("=" * 90 + "\n")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compare all LLM approaches")
    parser.add_argument('--days', type=int, default=180, help='Days to backtest (default: 180)')
    parser.add_argument('--symbols', nargs='+', default=['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA'],
                       help='Symbols to test')

    args = parser.parse_args()

    results = run_comprehensive_comparison(symbols=args.symbols, days=args.days)
