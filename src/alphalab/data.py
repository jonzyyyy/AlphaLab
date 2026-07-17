"""Data access layer: ticker universe, fundamentals, and price history.

Design goals for running on a laptop:
- The default path never makes per-ticker network calls. The universe and
  EPS snapshots are read from committed CSVs, and prices come from a single
  batch `yf.download` that is cached to parquet on disk.
- Expensive refreshes (hundreds of yfinance `.info` requests) only happen
  when `refresh=True` is passed explicitly.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import date

import pandas as pd
import yfinance as yf

from alphalab.config import (
    FUNDAMENTALS_CACHE,
    MARKET_CAP_CACHE,
    PRICE_CACHE_DIR,
)

logger = logging.getLogger(__name__)


def load_universe(refresh: bool = False) -> pd.DataFrame:
    """Return the S&P 500 universe sorted by market cap (largest first).

    Columns: Ticker, MarketCap, CompanyName. Reads the committed snapshot by
    default; `refresh=True` rebuilds it from yfinance (one `.info` request
    per ticker, ~500 requests, several minutes).
    """
    if not refresh and MARKET_CAP_CACHE.exists():
        return pd.read_csv(MARKET_CAP_CACHE)
    if not refresh:
        raise FileNotFoundError(
            f"Universe snapshot not found at {MARKET_CAP_CACHE}. "
            "Run with refresh=True (CLI: --refresh) to rebuild it — note this "
            "makes one yfinance request per S&P 500 ticker."
        )

    from pytickersymbols import PyTickerSymbols

    tickers = sorted(set(PyTickerSymbols().get_sp_500_nyc_yahoo_tickers()))
    logger.warning("Rebuilding universe snapshot: ~%d yfinance .info requests", len(tickers))

    rows = []
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info
        except Exception as exc:  # yfinance raises a mix of network/JSON errors
            logger.warning("Skipping %s: %s", ticker, exc)
            continue
        market_cap = info.get("marketCap")
        if market_cap:
            rows.append(
                {
                    "Ticker": ticker,
                    "MarketCap": market_cap,
                    "CompanyName": info.get("longName", ticker),
                }
            )

    universe = (
        pd.DataFrame(rows)
        .drop_duplicates(subset="CompanyName")  # dual share classes (GOOG/GOOGL etc.)
        .sort_values("MarketCap", ascending=False)
        .reset_index(drop=True)
    )
    MARKET_CAP_CACHE.parent.mkdir(parents=True, exist_ok=True)
    universe.to_csv(MARKET_CAP_CACHE, index=False)
    return universe


def load_fundamentals(tickers: list[str], refresh: bool = False) -> pd.Series:
    """Return trailing-twelve-month EPS for each ticker as a Series.

    Values come from a committed CSV snapshot; only tickers missing from the
    snapshot are fetched (one `.info` request each) and appended. Tickers
    with no EPS available are NaN.
    """
    if FUNDAMENTALS_CACHE.exists():
        cached = pd.read_csv(FUNDAMENTALS_CACHE, index_col="Ticker")["TrailingEPS"]
    else:
        cached = pd.Series(dtype=float, name="TrailingEPS")

    missing = tickers if refresh else [t for t in tickers if t not in cached.index]
    if missing:
        logger.info("Fetching trailing EPS for %d tickers", len(missing))
        fetched = {}
        for ticker in missing:
            try:
                info = yf.Ticker(ticker).info
                fetched[ticker] = info.get("trailingEps", float("nan"))
            except Exception as exc:
                logger.warning("No EPS for %s: %s", ticker, exc)
                fetched[ticker] = float("nan")
        fetched_series = pd.Series(fetched, name="TrailingEPS", dtype=float)
        cached = pd.concat([cached.drop(fetched_series.index, errors="ignore"), fetched_series])
        FUNDAMENTALS_CACHE.parent.mkdir(parents=True, exist_ok=True)
        cached.rename_axis("Ticker").to_csv(FUNDAMENTALS_CACHE)

    return cached.reindex(tickers)


def load_prices(
    tickers: list[str], start: date, end: date, refresh: bool = False
) -> pd.DataFrame:
    """Return daily close prices (auto-adjusted) as a DataFrame of date x ticker.

    Downloads happen in one batch request and are cached to parquet keyed by
    the ticker set and date range, so repeat runs are fully offline.
    """
    key = hashlib.sha1(",".join(sorted(tickers)).encode()).hexdigest()[:8]
    cache_file = (
        PRICE_CACHE_DIR
        / f"prices_{start:%Y%m%d}_{end:%Y%m%d}_{len(tickers)}t_{key}.parquet"
    )
    if not refresh and cache_file.exists():
        return pd.read_parquet(cache_file)

    raw = yf.download(
        tickers,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
        group_by="column",
    )
    close = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw[["Close"]]
    if not isinstance(raw.columns, pd.MultiIndex):
        close = close.rename(columns={"Close": tickers[0]})
    close = close.dropna(axis=1, how="all").sort_index()
    if close.empty:
        raise RuntimeError(
            f"No price data returned for {len(tickers)} tickers between {start} and {end}"
        )

    PRICE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    close.to_parquet(cache_file)
    return close


def load_benchmark(ticker: str, start: date, end: date, refresh: bool = False) -> pd.Series:
    """Return the benchmark's daily close prices as a Series."""
    prices = load_prices([ticker], start, end, refresh=refresh)
    return prices[ticker]


def train_test_split_index(
    index: pd.DatetimeIndex, split_ratio: float
) -> tuple[pd.DatetimeIndex, pd.DatetimeIndex]:
    """Split a date index into train/test segments by position."""
    split_at = int(len(index) * split_ratio)
    if split_at == 0 or split_at == len(index):
        raise ValueError(
            f"split_ratio={split_ratio} leaves an empty train or test set "
            f"for {len(index)} rows"
        )
    return index[:split_at], index[split_at:]
