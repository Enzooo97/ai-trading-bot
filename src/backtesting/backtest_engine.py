"""
Comprehensive backtesting engine for strategy validation.
Tests strategies on historical data to optimize parameters.
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import logging
import pandas as pd
import numpy as np
from dataclasses import dataclass
from sqlalchemy.orm import Session

from src.config import settings
from src.data_pipeline import alpaca_client
from src.strategies.base_strategy import BaseStrategy, Signal
from src.database import db, BacktestRun

logger = logging.getLogger(__name__)


@dataclass
class BacktestTrade:
    """Individual backtest trade record."""
    entry_time: datetime
    exit_time: datetime
    symbol: str
    side: str  # 'buy' or 'sell'
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_pct: float
    strategy_name: str
    entry_reason: str
    exit_reason: str
    hold_duration_minutes: float


@dataclass
class BacktestMetrics:
    """Backt testing performance metrics."""
    # Returns
    total_return_pct: float
    annualized_return_pct: float

    # Trades
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float

    # Profitability
    avg_win: float
    avg_loss: float
    profit_factor: float
    avg_trade_pnl: float

    # Risk metrics
    max_drawdown_pct: float
    sharpe_ratio: float
    sortino_ratio: float

    # Trade characteristics
    avg_hold_duration_minutes: float
    max_consecutive_losses: int
    max_consecutive_wins: int

    # Daily stats
    avg_trades_per_day: float
    best_day_pct: float
    worst_day_pct: float


class BacktestEngine:
    """
    Backtesting engine for strategy validation and optimization.

    Simulates trading with realistic conditions:
    - Commission costs
    - Slippage estimation
    - Position sizing
    - Risk management
    """

    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_per_trade: float = 0.0,  # Alpaca has $0 commissions
        slippage_bps: float = 2.0,  # 2 basis points slippage estimate
    ):
        """
        Initialize backtesting engine.

        Args:
            initial_capital: Starting capital
            commission_per_trade: Commission per trade (Alpaca = $0)
            slippage_bps: Slippage in basis points (0.01% = 1bp)
        """
        self.initial_capital = initial_capital
        self.commission = commission_per_trade
        self.slippage_bps = slippage_bps

    def run_backtest(
        self,
        strategy: BaseStrategy,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "5Min",
    ) -> Tuple[BacktestMetrics, List[BacktestTrade], pd.DataFrame]:
        """
        Run backtest for a strategy on historical data.

        Args:
            strategy: Strategy to test
            symbols: List of symbols to trade
            start_date: Backtest start date
            end_date: Backtest end date
            timeframe: Bar timeframe (1Min, 5Min, 15Min)

        Returns:
            Tuple of (metrics, trades, equity_curve)
        """
        try:
            logger.info(
                f"Starting backtest: {strategy.name} on {len(symbols)} symbols "
                f"from {start_date.date()} to {end_date.date()}"
            )

            # Initialize tracking
            trades: List[BacktestTrade] = []
            equity_curve = []
            current_capital = self.initial_capital
            open_position = None

            # Get historical data for each symbol
            for symbol in symbols:
                logger.info(f"Testing {symbol}...")

                # Get bars
                bars_dict = alpaca_client.get_bars(
                    symbols=[symbol],
                    timeframe=timeframe,
                    start=start_date,
                    end=end_date,
                )

                if symbol not in bars_dict or bars_dict[symbol].empty:
                    logger.warning(f"No data for {symbol}, skipping")
                    continue

                bars = bars_dict[symbol]

                # Simulate trading on each bar
                for i in range(strategy.get_required_bars(), len(bars)):
                    current_bar = bars.iloc[i]
                    current_time = current_bar.name
                    current_price = current_bar['close']

                    # Get historical data window
                    hist_data = bars.iloc[:i+1]

                    # Check exit conditions if position open
                    if open_position:
                        signal = strategy.analyze(
                            symbol=symbol,
                            data=hist_data,
                            account_info={'equity': Decimal(str(current_capital))},
                            current_positions=[{
                                'symbol': symbol,
                                'side': open_position['side'],
                                'avg_entry_price': open_position['entry_price'],
                            }],
                        )

                        # Close position on signal or max hold time
                        hold_duration = (current_time - open_position['entry_time']).total_seconds() / 60
                        should_close = (
                            signal.action == "close" or
                            hold_duration > settings.max_position_hold_hours * 60
                        )

                        if should_close:
                            # Close position
                            exit_price = self._get_exit_price(current_price, open_position['side'])

                            # Calculate P&L
                            if open_position['side'] == 'buy':
                                pnl = (exit_price - open_position['entry_price']) * open_position['quantity']
                            else:
                                pnl = (open_position['entry_price'] - exit_price) * open_position['quantity']

                            pnl -= self.commission  # Subtract commission
                            pnl_pct = pnl / (open_position['entry_price'] * open_position['quantity'])

                            # Record trade
                            trade = BacktestTrade(
                                entry_time=open_position['entry_time'],
                                exit_time=current_time,
                                symbol=symbol,
                                side=open_position['side'],
                                entry_price=open_position['entry_price'],
                                exit_price=exit_price,
                                quantity=open_position['quantity'],
                                pnl=pnl,
                                pnl_pct=pnl_pct,
                                strategy_name=strategy.name,
                                entry_reason=open_position['entry_reason'],
                                exit_reason=signal.reason if signal.action == "close" else "max_hold_time",
                                hold_duration_minutes=hold_duration,
                            )
                            trades.append(trade)

                            # Update capital
                            current_capital += pnl
                            equity_curve.append({
                                'timestamp': current_time,
                                'equity': current_capital,
                                'trade_pnl': pnl,
                            })

                            logger.debug(
                                f"Closed {symbol}: ${pnl:+.2f} ({pnl_pct*100:+.2f}%) "
                                f"- {trade.exit_reason}"
                            )

                            open_position = None

                    # Check entry conditions if no position
                    if not open_position:
                        signal = strategy.analyze(
                            symbol=symbol,
                            data=hist_data,
                            account_info={'equity': Decimal(str(current_capital))},
                            current_positions=[],
                        )

                        if signal.action in ["buy", "sell"] and signal.strength >= 0.7:
                            # Calculate position size (simplified)
                            position_size_dollars = current_capital * settings.max_position_size_pct
                            entry_price = self._get_entry_price(current_price, signal.action)
                            quantity = position_size_dollars / entry_price

                            # Open position
                            open_position = {
                                'entry_time': current_time,
                                'side': signal.action,
                                'entry_price': entry_price,
                                'quantity': quantity,
                                'entry_reason': signal.reason,
                            }

                            logger.debug(
                                f"Opened {signal.action} {symbol} @ ${entry_price:.2f} "
                                f"qty={quantity:.2f} - {signal.reason}"
                            )

            # Close any open position at end
            if open_position:
                last_bar = bars.iloc[-1]
                exit_price = self._get_exit_price(last_bar['close'], open_position['side'])

                if open_position['side'] == 'buy':
                    pnl = (exit_price - open_position['entry_price']) * open_position['quantity']
                else:
                    pnl = (open_position['entry_price'] - exit_price) * open_position['quantity']

                pnl -= self.commission
                pnl_pct = pnl / (open_position['entry_price'] * open_position['quantity'])

                trade = BacktestTrade(
                    entry_time=open_position['entry_time'],
                    exit_time=last_bar.name,
                    symbol=symbol,
                    side=open_position['side'],
                    entry_price=open_position['entry_price'],
                    exit_price=exit_price,
                    quantity=open_position['quantity'],
                    pnl=pnl,
                    pnl_pct=pnl_pct,
                    strategy_name=strategy.name,
                    entry_reason=open_position['entry_reason'],
                    exit_reason="backtest_end",
                    hold_duration_minutes=(last_bar.name - open_position['entry_time']).total_seconds() / 60,
                )
                trades.append(trade)
                current_capital += pnl

            # Convert equity curve to DataFrame
            equity_df = pd.DataFrame(equity_curve)
            if not equity_df.empty:
                equity_df.set_index('timestamp', inplace=True)

            # Calculate metrics
            metrics = self._calculate_metrics(trades, equity_df, start_date, end_date)

            logger.info(
                f"Backtest complete: {len(trades)} trades, "
                f"{metrics.win_rate*100:.1f}% win rate, "
                f"{metrics.total_return_pct*100:+.2f}% return"
            )

            return metrics, trades, equity_df

        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            raise

    def _get_entry_price(self, current_price: float, side: str) -> float:
        """Calculate entry price with slippage."""
        slippage = current_price * (self.slippage_bps / 10000.0)

        if side == "buy":
            return current_price + slippage  # Pay slippage on buy
        else:
            return current_price - slippage  # Pay slippage on short

    def _get_exit_price(self, current_price: float, side: str) -> float:
        """Calculate exit price with slippage."""
        slippage = current_price * (self.slippage_bps / 10000.0)

        if side == "buy":
            return current_price - slippage  # Pay slippage on sell
        else:
            return current_price + slippage  # Pay slippage on cover

    def _calculate_metrics(
        self,
        trades: List[BacktestTrade],
        equity_curve: pd.DataFrame,
        start_date: datetime,
        end_date: datetime,
    ) -> BacktestMetrics:
        """Calculate comprehensive backtest metrics."""
        if not trades:
            return self._empty_metrics()

        # Basic stats
        total_trades = len(trades)
        wins = [t for t in trades if t.pnl > 0]
        losses = [t for t in trades if t.pnl <= 0]
        winning_trades = len(wins)
        losing_trades = len(losses)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        # P&L stats
        total_pnl = sum(t.pnl for t in trades)
        total_return_pct = total_pnl / self.initial_capital

        # Annualize return
        days = (end_date - start_date).days
        years = days / 365.25
        annualized_return_pct = ((1 + total_return_pct) ** (1 / years) - 1) if years > 0 else 0

        # Win/Loss stats
        avg_win = np.mean([t.pnl for t in wins]) if wins else 0
        avg_loss = np.mean([t.pnl for t in losses]) if losses else 0
        profit_factor = abs(sum(t.pnl for t in wins) / sum(t.pnl for t in losses)) if losses and sum(t.pnl for t in losses) != 0 else float('inf')
        avg_trade_pnl = total_pnl / total_trades

        # Hold duration
        avg_hold_duration = np.mean([t.hold_duration_minutes for t in trades])

        # Consecutive wins/losses
        max_consecutive_wins = self._max_consecutive(trades, lambda t: t.pnl > 0)
        max_consecutive_losses = self._max_consecutive(trades, lambda t: t.pnl <= 0)

        # Daily stats
        trades_per_day = total_trades / days if days > 0 else 0

        # Drawdown and risk metrics
        max_drawdown_pct = self._calculate_max_drawdown(equity_curve)
        sharpe_ratio = self._calculate_sharpe_ratio(trades, total_return_pct, years)
        sortino_ratio = self._calculate_sortino_ratio(trades, total_return_pct, years)

        # Daily P&L stats
        daily_pnl = pd.DataFrame([{
            'date': t.exit_time.date(),
            'pnl': t.pnl
        } for t in trades]).groupby('date')['pnl'].sum()

        best_day_pct = (daily_pnl.max() / self.initial_capital) if not daily_pnl.empty else 0
        worst_day_pct = (daily_pnl.min() / self.initial_capital) if not daily_pnl.empty else 0

        return BacktestMetrics(
            total_return_pct=total_return_pct,
            annualized_return_pct=annualized_return_pct,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            avg_trade_pnl=avg_trade_pnl,
            max_drawdown_pct=max_drawdown_pct,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            avg_hold_duration_minutes=avg_hold_duration,
            max_consecutive_losses=max_consecutive_losses,
            max_consecutive_wins=max_consecutive_wins,
            avg_trades_per_day=trades_per_day,
            best_day_pct=best_day_pct,
            worst_day_pct=worst_day_pct,
        )

    def _empty_metrics(self) -> BacktestMetrics:
        """Return empty metrics when no trades."""
        return BacktestMetrics(
            total_return_pct=0, annualized_return_pct=0,
            total_trades=0, winning_trades=0, losing_trades=0, win_rate=0,
            avg_win=0, avg_loss=0, profit_factor=0, avg_trade_pnl=0,
            max_drawdown_pct=0, sharpe_ratio=0, sortino_ratio=0,
            avg_hold_duration_minutes=0, max_consecutive_losses=0,
            max_consecutive_wins=0, avg_trades_per_day=0,
            best_day_pct=0, worst_day_pct=0,
        )

    def _max_consecutive(self, trades: List[BacktestTrade], condition) -> int:
        """Calculate maximum consecutive trades meeting condition."""
        max_count = 0
        current_count = 0

        for trade in trades:
            if condition(trade):
                current_count += 1
                max_count = max(max_count, current_count)
            else:
                current_count = 0

        return max_count

    def _calculate_max_drawdown(self, equity_curve: pd.DataFrame) -> float:
        """Calculate maximum drawdown percentage."""
        if equity_curve.empty:
            return 0.0

        equity = equity_curve['equity']
        peak = equity.expanding().max()
        drawdown = (equity - peak) / peak

        return abs(drawdown.min())

    def _calculate_sharpe_ratio(self, trades: List[BacktestTrade], total_return: float, years: float) -> float:
        """Calculate Sharpe ratio (risk-adjusted return)."""
        if not trades or years == 0:
            return 0.0

        returns = [t.pnl_pct for t in trades]
        mean_return = np.mean(returns)
        std_return = np.std(returns)

        if std_return == 0:
            return 0.0

        # Annualized Sharpe (assuming 252 trading days)
        sharpe = (mean_return / std_return) * np.sqrt(252)

        return sharpe

    def _calculate_sortino_ratio(self, trades: List[BacktestTrade], total_return: float, years: float) -> float:
        """Calculate Sortino ratio (downside risk-adjusted return)."""
        if not trades or years == 0:
            return 0.0

        returns = [t.pnl_pct for t in trades]
        mean_return = np.mean(returns)

        # Only consider negative returns for downside deviation
        downside_returns = [r for r in returns if r < 0]

        if not downside_returns:
            return float('inf')

        downside_std = np.std(downside_returns)

        if downside_std == 0:
            return 0.0

        # Annualized Sortino
        sortino = (mean_return / downside_std) * np.sqrt(252)

        return sortino
