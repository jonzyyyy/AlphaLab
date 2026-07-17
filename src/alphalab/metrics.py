"""Performance metrics.

This is the only module that annualizes anything: the strategy and the
benchmark are both pushed through `compute_metrics` over the same date
index, so their Sharpe ratios and annualized figures are directly
comparable.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def compute_metrics(
    daily_returns: pd.Series,
    trading_days_per_year: int = 252,
    risk_free_rate: float = 0.0,
) -> dict[str, float]:
    """Summarize a daily return series.

    Returns total return, annualized return/volatility, Sharpe ratio, and the
    number of observations used (handy for confirming that two series were
    measured over the same window).
    """
    returns = daily_returns.dropna()
    n = len(returns)
    if n < 2:
        return {
            "total_return": np.nan,
            "annualized_return": np.nan,
            "annualized_vol": np.nan,
            "sharpe_ratio": np.nan,
            "n_days": n,
        }

    total_return = (1 + returns).prod() - 1
    annualized_return = (1 + total_return) ** (trading_days_per_year / n) - 1
    annualized_vol = returns.std(ddof=1) * np.sqrt(trading_days_per_year)
    sharpe = (
        (annualized_return - risk_free_rate) / annualized_vol
        if annualized_vol > 0
        else np.nan
    )
    return {
        "total_return": total_return,
        "annualized_return": annualized_return,
        "annualized_vol": annualized_vol,
        "sharpe_ratio": sharpe,
        "n_days": n,
    }


def metrics_table(named_returns: dict[str, pd.Series], **kwargs) -> pd.DataFrame:
    """Build a comparison table (one column per return series)."""
    return pd.DataFrame(
        {name: compute_metrics(returns, **kwargs) for name, returns in named_returns.items()}
    )
