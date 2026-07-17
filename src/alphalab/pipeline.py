"""End-to-end research pipeline shared by the CLI, notebook, and Streamlit app."""

from __future__ import annotations

import logging
from datetime import date, timedelta

import pandas as pd

from alphalab.backtest import BacktestResult, run_backtest
from alphalab.config import Settings
from alphalab.data import (
    load_benchmark,
    load_fundamentals,
    load_prices,
    load_universe,
    train_test_split_index,
)
from alphalab.factors import Momentum, Value
from alphalab.metrics import metrics_table

logger = logging.getLogger(__name__)


def run_pipeline(settings: Settings = Settings(), refresh: bool = False) -> dict:
    """Run universe -> prices -> factors -> backtest -> benchmark comparison.

    Returns a dict with the backtest result, benchmark returns, the metrics
    comparison table, and the intermediate data for inspection.
    """
    end = date.today()
    start = end - timedelta(days=settings.data_years * 365)

    universe = load_universe(refresh=refresh)
    tickers = universe["Ticker"].head(settings.universe_size).tolist()

    prices = load_prices(tickers, start, end, refresh=refresh)
    train_index, test_index = train_test_split_index(prices.index, settings.split_ratio)
    logger.info(
        "Train %s to %s, test %s to %s",
        train_index[0].date(), train_index[-1].date(),
        test_index[0].date(), test_index[-1].date(),
    )

    eps = load_fundamentals(list(prices.columns), refresh=refresh)
    factors = [Value(eps), Momentum(settings.momentum_lookback_days)]

    result: BacktestResult = run_backtest(
        prices, factors, settings.top_n_stocks, test_index, settings.rebalance_freq
    )

    benchmark_prices = load_benchmark(settings.benchmark_ticker, start, end, refresh=refresh)
    # Same dates as the strategy so the metrics share a denominator
    benchmark_returns = (
        benchmark_prices.pct_change().reindex(result.daily_returns.index).dropna()
    )

    metrics = metrics_table(
        {"Strategy": result.daily_returns, settings.benchmark_ticker: benchmark_returns},
        trading_days_per_year=settings.trading_days_per_year,
        risk_free_rate=settings.risk_free_rate,
    )

    return {
        "settings": settings,
        "universe": universe,
        "prices": prices,
        "train_index": train_index,
        "test_index": test_index,
        "factors": factors,
        "result": result,
        "benchmark_returns": benchmark_returns,
        "benchmark_cum_returns": (1 + benchmark_returns).cumprod(),
        "metrics": metrics,
    }


def holdings_frame(result: BacktestResult) -> pd.DataFrame:
    """Holdings per rebalance date as a display-friendly DataFrame."""
    return pd.DataFrame(
        {d.date(): pd.Series(tickers) for d, tickers in result.holdings.items()}
    ).T.rename(columns=lambda i: f"#{i + 1}")
