"""AlphaLab: factor-based equity strategy research."""

from alphalab.backtest import BacktestResult, rebalance_schedule, run_backtest
from alphalab.config import Settings
from alphalab.data import (
    load_benchmark,
    load_fundamentals,
    load_prices,
    load_universe,
    train_test_split_index,
)
from alphalab.factors import Factor, Momentum, Value, compute_factor_table
from alphalab.metrics import compute_metrics, metrics_table
from alphalab.pipeline import holdings_frame, run_pipeline
from alphalab.plotting import plot_cumulative_returns
from alphalab.selection import select_stocks

__version__ = "0.1.0"

__all__ = [
    "BacktestResult",
    "Factor",
    "Momentum",
    "Settings",
    "Value",
    "compute_factor_table",
    "compute_metrics",
    "holdings_frame",
    "load_benchmark",
    "load_fundamentals",
    "load_prices",
    "load_universe",
    "metrics_table",
    "plot_cumulative_returns",
    "rebalance_schedule",
    "run_backtest",
    "run_pipeline",
    "select_stocks",
    "train_test_split_index",
]
