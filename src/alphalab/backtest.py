"""Point-in-time backtest: rank, hold, rebalance.

At each rebalance date the portfolio is rebuilt from factor scores computed
using only prices up to that date, then held equal-weight until the next
rebalance. Returns are accumulated strictly within the test window.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from alphalab.factors import Factor, compute_factor_table
from alphalab.selection import select_stocks


@dataclass
class BacktestResult:
    daily_returns: pd.Series
    cum_returns: pd.Series  # growth of 1.0 over the test period
    holdings: dict[pd.Timestamp, list[str]]  # rebalance date -> tickers held


def rebalance_schedule(test_index: pd.DatetimeIndex, freq: str = "QS") -> pd.DatetimeIndex:
    """Rebalance dates within the test window, always including its first day."""
    dates = pd.date_range(test_index[0], test_index[-1], freq=freq)
    if len(dates) == 0 or dates[0] != test_index[0]:
        dates = dates.insert(0, test_index[0])
    return dates


def period_returns(
    prices: pd.DataFrame,
    tickers: list[str],
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.Series:
    """Equal-weight daily returns for `tickers` over trading days in [start, end].

    The price slice starts one trading day before `start` purely to seed
    pct_change, so the first day of the period gets its true return instead
    of the 0 that a naive fillna would give it.
    """
    window = prices.loc[:end, tickers]
    seed_position = max(window.index.searchsorted(start) - 1, 0)
    returns = window.iloc[seed_position:].pct_change().iloc[1:]
    returns = returns.loc[returns.index >= start]
    # mean(axis=1) skips NaN, so a ticker with a missing price implicitly has
    # its weight redistributed across the rest for that day
    return returns.mean(axis=1)


def run_backtest(
    prices: pd.DataFrame,
    factors: list[Factor],
    top_n: int,
    test_index: pd.DatetimeIndex,
    freq: str = "QS",
) -> BacktestResult:
    """Run the quarterly-rebalanced strategy over the test window."""
    schedule = rebalance_schedule(test_index, freq)
    holdings: dict[pd.Timestamp, list[str]] = {}
    all_returns: list[pd.Series] = []

    for i, rebalance_date in enumerate(schedule):
        table = compute_factor_table(prices, rebalance_date, factors)
        selected = select_stocks(table, factors, top_n)
        holdings[rebalance_date] = selected

        period_end = (
            schedule[i + 1] - pd.Timedelta(days=1)
            if i + 1 < len(schedule)
            else test_index[-1]
        )
        all_returns.append(period_returns(prices, selected, rebalance_date, period_end))

    daily_returns = pd.concat(all_returns).reindex(test_index).dropna()
    cum_returns = (1 + daily_returns).cumprod()
    return BacktestResult(daily_returns=daily_returns, cum_returns=cum_returns, holdings=holdings)
