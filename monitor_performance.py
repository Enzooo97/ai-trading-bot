#!/usr/bin/env python3
"""
Paper Trading Performance Monitor

Real-time monitoring dashboard for tracking bot performance during the 30-day
paper trading evaluation period.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import time
from decimal import Decimal

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.data_pipeline import alpaca_client
import config_paper_trading as config


def clear_screen():
    """Clear terminal screen."""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


def get_portfolio_performance():
    """Get current portfolio performance metrics."""
    try:
        account = alpaca_client.get_account()
        positions = alpaca_client.get_positions()

        equity = float(account['equity'])
        cash = float(account['cash'])
        buying_power = float(account['buying_power'])

        # Calculate performance
        total_return = equity - config.INITIAL_CAPITAL
        total_return_pct = (total_return / config.INITIAL_CAPITAL) * 100

        # Position details
        total_market_value = sum(float(p['market_value']) for p in positions)
        total_unrealized_pl = sum(float(p['unrealized_pl']) for p in positions)

        return {
            'equity': equity,
            'cash': cash,
            'buying_power': buying_power,
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'num_positions': len(positions),
            'total_market_value': total_market_value,
            'total_unrealized_pl': total_unrealized_pl,
            'positions': positions
        }
    except Exception as e:
        return {'error': str(e)}


def display_dashboard():
    """Display real-time performance dashboard."""
    perf = get_portfolio_performance()

    if 'error' in perf:
        print(f"[ERROR] Failed to fetch data: {perf['error']}")
        return

    clear_screen()

    print("="*80)
    print("PAPER TRADING PERFORMANCE MONITOR")
    print("="*80)
    print(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # Account Summary
    print("\nACCOUNT SUMMARY:")
    print(f"  Starting Capital:    £{config.INITIAL_CAPITAL:>12,.2f}")
    print(f"  Current Equity:      £{perf['equity']:>12,.2f}")
    print(f"  Cash Available:      £{perf['cash']:>12,.2f}")
    print(f"  Buying Power:        £{perf['buying_power']:>12,.2f}")

    # Performance
    return_color = "+" if perf['total_return'] >= 0 else ""
    print(f"\nPERFORMANCE:")
    print(f"  Total Return:        £{return_color}{perf['total_return']:>12,.2f} ({return_color}{perf['total_return_pct']:.2f}%)")
    print(f"  Unrealized P&L:      £{perf['total_unrealized_pl']:>12,.2f}")

    # Progress to targets
    monthly_progress = (perf['total_return'] / config.MONTHLY_TARGET_DOLLARS) * 100
    annual_progress = (perf['total_return_pct'] / config.ANNUAL_TARGET_PCT) / 100 * 100

    print(f"\nTARGET PROGRESS:")
    print(f"  Monthly Target:      £{config.MONTHLY_TARGET_DOLLARS:.2f} ({monthly_progress:.1f}% achieved)")
    print(f"  Annual Target:       {config.ANNUAL_TARGET_PCT*100:.0f}% ({annual_progress:.1f}% achieved)")

    # Risk Status
    daily_loss_remaining = config.MAX_DAILY_LOSS_DOLLARS + perf['total_return']
    account_buffer = perf['equity'] - config.MIN_ACCOUNT_BALANCE

    print(f"\nRISK STATUS:")
    print(f"  Daily Loss Limit:    £{config.MAX_DAILY_LOSS_DOLLARS:.2f} (£{daily_loss_remaining:.2f} remaining)")
    print(f"  Min Balance:         £{config.MIN_ACCOUNT_BALANCE:.2f} (£{account_buffer:.2f} buffer)")
    print(f"  Position Limit:      {config.MAX_CONCURRENT_POSITIONS} ({perf['num_positions']} used)")

    # Positions
    print(f"\nOPEN POSITIONS ({perf['num_positions']}):")
    if perf['num_positions'] == 0:
        print("  No open positions")
    else:
        print(f"  {'Symbol':<8} {'Qty':>6} {'Entry':>10} {'Current':>10} {'P&L':>10} {'P&L%':>8}")
        print("  " + "-"*66)
        for pos in perf['positions']:
            symbol = pos['symbol']
            qty = int(pos['quantity'])
            entry_price = float(pos['avg_entry_price'])
            current_price = float(pos['current_price'])
            unrealized_pl = float(pos['unrealized_pl'])
            unrealized_plpc = float(pos['unrealized_plpc']) * 100

            pl_sign = "+" if unrealized_pl >= 0 else ""
            print(f"  {symbol:<8} {qty:>6} £{entry_price:>9.2f} £{current_price:>9.2f} £{pl_sign}{unrealized_pl:>9.2f} {pl_sign}{unrealized_plpc:>7.2f}%")

    # Health Check
    print(f"\nHEALTH CHECK:")
    warnings = []

    if perf['total_return'] < -config.MAX_DAILY_LOSS_DOLLARS:
        warnings.append("  [!] Daily loss limit exceeded!")

    if perf['equity'] < config.MIN_ACCOUNT_BALANCE:
        warnings.append("  [!] Account below minimum balance!")

    if perf['num_positions'] >= config.MAX_CONCURRENT_POSITIONS:
        warnings.append("  [!] Maximum positions reached")

    if not warnings:
        print("  [OK] All systems normal")
    else:
        for warning in warnings:
            print(warning)

    # Recommendations
    print(f"\nRECOMMENDATIONS:")
    if perf['total_return_pct'] < -2:
        print("  - Review recent trades for pattern of losses")
        print("  - Consider reducing position sizes")
    elif perf['total_return_pct'] > 2:
        print("  - Performance above target - well done!")
        print("  - Consider taking profits if near daily target")
    else:
        print("  - Performance within expected range")
        print("  - Continue monitoring and following strategy")

    print("\n" + "="*80)
    print("Press Ctrl+C to exit | Refreshing every 60 seconds")
    print("="*80)


def monitor_live(refresh_seconds=60):
    """Run live monitoring dashboard."""
    try:
        while True:
            display_dashboard()
            time.sleep(refresh_seconds)
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")


def show_daily_summary():
    """Show end-of-day summary report."""
    perf = get_portfolio_performance()

    if 'error' in perf:
        print(f"[ERROR] Failed to fetch data: {perf['error']}")
        return

    print("="*80)
    print("DAILY SUMMARY REPORT")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    print("="*80)

    print(f"\nACCOUNT:")
    print(f"  Equity:              £{perf['equity']:,.2f}")
    print(f"  Cash:                £{perf['cash']:,.2f}")
    print(f"  Total Return:        £{perf['total_return']:,.2f} ({perf['total_return_pct']:+.2f}%)")

    print(f"\nPOSITIONS:")
    print(f"  Open Positions:      {perf['num_positions']}")
    print(f"  Market Value:        £{perf['total_market_value']:,.2f}")
    print(f"  Unrealized P&L:      £{perf['total_unrealized_pl']:,.2f}")

    print(f"\nTARGETS:")
    print(f"  Monthly Target:      £{config.MONTHLY_TARGET_DOLLARS:.2f} ({(perf['total_return']/config.MONTHLY_TARGET_DOLLARS)*100:.1f}%)")
    print(f"  Annual Target:       {config.ANNUAL_TARGET_PCT*100:.0f}% ({perf['total_return_pct']/config.ANNUAL_TARGET_PCT/100*100:.1f}%)")

    print(f"\nNEXT STEPS:")
    if perf['total_return_pct'] < -1:
        print("  - Review why trades are losing")
        print("  - Check if market conditions changed")
        print("  - Consider reducing risk temporarily")
    elif perf['total_return_pct'] > config.DAILY_PROFIT_TARGET_PCT * 100:
        print("  - Daily target achieved!")
        print("  - Consider stopping trading for today")
        print("  - Review what worked well")
    else:
        print("  - Performance on track")
        print("  - Continue monitoring tomorrow")

    print("="*80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Monitor paper trading performance")
    parser.add_argument('--live', action='store_true', help='Live monitoring dashboard')
    parser.add_argument('--summary', action='store_true', help='Show daily summary')
    parser.add_argument('--refresh', type=int, default=60, help='Refresh interval (seconds)')

    args = parser.parse_args()

    if args.summary:
        show_daily_summary()
    elif args.live:
        monitor_live(refresh_seconds=args.refresh)
    else:
        # Default: show current status
        display_dashboard()
