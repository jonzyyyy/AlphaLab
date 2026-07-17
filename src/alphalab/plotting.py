"""Matplotlib charts for the notebook and CLI."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd


def plot_cumulative_returns(
    strategy_cum: pd.Series,
    benchmark_cum: pd.Series,
    starting_amount: float = 10_000.0,
    benchmark_label: str = "SPY",
) -> plt.Figure:
    """Plot portfolio value over the test period, strategy vs benchmark."""
    fig, ax = plt.subplots(figsize=(10, 5))
    (strategy_cum * starting_amount).plot(ax=ax, label="Strategy", linewidth=1.8)
    (benchmark_cum * starting_amount).plot(
        ax=ax, label=benchmark_label, linewidth=1.8, alpha=0.85
    )
    ax.set_title(f"Growth of ${starting_amount:,.0f} over the test period")
    ax.set_ylabel("Portfolio value ($)")
    ax.set_xlabel("")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig
