"""Factor definitions.

Every factor implements `compute(prices, as_of)` and may only use price data
up to and including `as_of` — this is what keeps the backtest point-in-time.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
import pandas as pd


class Factor(ABC):
    """A cross-sectional scoring rule evaluated at a single date."""

    name: str
    higher_is_better: bool

    @abstractmethod
    def compute(self, prices: pd.DataFrame, as_of: pd.Timestamp) -> pd.Series:
        """Return one score per ticker using only data up to `as_of`."""


class Momentum(Factor):
    """Trailing price return over a fixed lookback window (default ~6 months)."""

    higher_is_better = True

    def __init__(self, lookback_days: int = 126):
        self.lookback_days = lookback_days
        self.name = f"momentum_{lookback_days}d"

    def compute(self, prices: pd.DataFrame, as_of: pd.Timestamp) -> pd.Series:
        window = prices.loc[:as_of]
        if len(window) <= self.lookback_days:
            return pd.Series(np.nan, index=prices.columns, name=self.name)
        current = window.iloc[-1]
        past = window.iloc[-1 - self.lookback_days]
        return (current / past - 1).rename(self.name)


class Value(Factor):
    """Trailing P/E: price as of the rebalance date over trailing-12m EPS.

    The price side is point-in-time; EPS is a single snapshot fetched once
    (see README for why yfinance cannot supply historical TTM EPS). Tickers
    with zero or negative earnings get NaN so they are excluded from the
    value ranking rather than rewarded for a meaningless ratio.
    """

    name = "trailing_pe"
    higher_is_better = False

    def __init__(self, eps_ttm: pd.Series):
        self.eps_ttm = eps_ttm.where(eps_ttm > 0)

    def compute(self, prices: pd.DataFrame, as_of: pd.Timestamp) -> pd.Series:
        last_price = prices.loc[:as_of].iloc[-1]
        return (last_price / self.eps_ttm.reindex(prices.columns)).rename(self.name)


def compute_factor_table(
    prices: pd.DataFrame, as_of: pd.Timestamp, factors: list[Factor]
) -> pd.DataFrame:
    """Evaluate all factors at one date; rows are tickers, columns are factors.

    Tickers where every factor is NaN (e.g. no price history yet) are dropped.
    """
    table = pd.concat([f.compute(prices, as_of) for f in factors], axis=1)
    return table.dropna(how="all")
