"""Project paths and run settings.

Everything configurable lives in the `Settings` dataclass so the CLI, the
research notebook, and the Streamlit app all run the exact same pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# src/alphalab/config.py -> repo root, independent of the current working directory
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
PRICE_CACHE_DIR = DATA_DIR / "cache"
MARKET_CAP_CACHE = DATA_DIR / "sp500_market_caps.csv"
FUNDAMENTALS_CACHE = DATA_DIR / "fundamentals.csv"


@dataclass(frozen=True)
class Settings:
    """Parameters for a single research run."""

    data_years: int = 2
    split_ratio: float = 0.7
    top_n_stocks: int = 5
    universe_size: int = 100
    benchmark_ticker: str = "SPY"
    starting_amount: float = 10_000.0
    rebalance_freq: str = "QS"
    momentum_lookback_days: int = 126
    risk_free_rate: float = 0.0
    trading_days_per_year: int = 252

    def __post_init__(self) -> None:
        if not 0 < self.split_ratio < 1:
            raise ValueError(f"split_ratio must be in (0, 1), got {self.split_ratio}")
        if self.top_n_stocks < 1:
            raise ValueError("top_n_stocks must be at least 1")
        if self.universe_size < self.top_n_stocks:
            raise ValueError("universe_size must be at least top_n_stocks")
