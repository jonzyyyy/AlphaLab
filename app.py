"""Streamlit dashboard for the AlphaLab value + momentum strategy.

Run locally with:  streamlit run app.py
All strategy logic lives in the `alphalab` package; this file is UI only.
"""

from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from alphalab import (
    Momentum,
    Settings,
    Value,
    holdings_frame,
    load_fundamentals,
    load_prices,
    load_universe,
    metrics_table,
    run_backtest,
    train_test_split_index,
)

st.set_page_config(page_title="AlphaLab", page_icon="📈", layout="wide")

st.title("AlphaLab — Value + Momentum Factor Strategy")
st.caption(
    "Ranks the largest S&P 500 names on trailing P/E and 6-month momentum, "
    "holds the top composite picks equal-weight, rebalances quarterly, and "
    "compares the out-of-sample result against SPY."
)

with st.sidebar:
    st.header("Parameters")
    universe_size = st.slider("Universe size (largest by market cap)", 20, 150, 50, step=10)
    top_n = st.slider("Stocks held", 3, 20, 5)
    data_years = st.slider("Years of history", 1, 5, 2)
    split_ratio = st.slider("Train fraction", 0.5, 0.9, 0.7, step=0.05)
    starting_amount = st.number_input(
        "Starting amount ($)", min_value=1_000, value=10_000, step=1_000
    )
    st.divider()
    refresh = st.checkbox(
        "Force re-download",
        help="Ignore the on-disk price/EPS caches for this run.",
    )


@st.cache_data(show_spinner="Loading universe…")
def cached_universe(refresh: bool) -> pd.DataFrame:
    return load_universe(refresh=refresh)


@st.cache_data(show_spinner="Downloading prices…")
def cached_prices(tickers: tuple[str, ...], start: date, end: date, refresh: bool):
    return load_prices(list(tickers), start, end, refresh=refresh)


@st.cache_data(show_spinner="Loading fundamentals…")
def cached_fundamentals(tickers: tuple[str, ...], refresh: bool) -> pd.Series:
    return load_fundamentals(list(tickers), refresh=refresh)


settings = Settings(
    universe_size=universe_size,
    top_n_stocks=top_n,
    data_years=data_years,
    split_ratio=split_ratio,
    starting_amount=float(starting_amount),
)
end = date.today()
start = end - timedelta(days=settings.data_years * 365)

universe = cached_universe(refresh)
tickers = tuple(universe["Ticker"].head(settings.universe_size))
prices = cached_prices(tickers, start, end, refresh)
train_index, test_index = train_test_split_index(prices.index, settings.split_ratio)

eps = cached_fundamentals(tuple(prices.columns), refresh)
factors = [Value(eps), Momentum(settings.momentum_lookback_days)]

result = run_backtest(
    prices, factors, settings.top_n_stocks, test_index, settings.rebalance_freq
)
benchmark_prices = cached_prices(
    (settings.benchmark_ticker,), start, end, refresh
)[settings.benchmark_ticker]
benchmark_returns = (
    benchmark_prices.pct_change().reindex(result.daily_returns.index).dropna()
)
benchmark_cum = (1 + benchmark_returns).cumprod()

metrics = metrics_table(
    {"Strategy": result.daily_returns, settings.benchmark_ticker: benchmark_returns},
    trading_days_per_year=settings.trading_days_per_year,
)

st.subheader(
    f"Out-of-sample test: {test_index[0].date()} to {test_index[-1].date()}"
)

strategy = metrics["Strategy"]
benchmark = metrics[settings.benchmark_ticker]
cols = st.columns(4)
cols[0].metric(
    "Total return",
    f"{strategy['total_return']:.1%}",
    f"{strategy['total_return'] - benchmark['total_return']:.1%} vs SPY",
)
cols[1].metric("Annualized return", f"{strategy['annualized_return']:.1%}")
cols[2].metric("Annualized volatility", f"{strategy['annualized_vol']:.1%}")
cols[3].metric("Sharpe ratio", f"{strategy['sharpe_ratio']:.2f}")

fig = go.Figure()
fig.add_scatter(
    x=result.cum_returns.index,
    y=result.cum_returns * settings.starting_amount,
    name="Strategy",
)
fig.add_scatter(
    x=benchmark_cum.index,
    y=benchmark_cum * settings.starting_amount,
    name=settings.benchmark_ticker,
)
fig.update_layout(
    title=f"Growth of ${settings.starting_amount:,.0f}",
    yaxis_title="Portfolio value ($)",
    legend=dict(orientation="h", y=1.02, yanchor="bottom"),
    margin=dict(t=80),
)
st.plotly_chart(fig, width="stretch")

left, right = st.columns(2)
with left:
    st.subheader("Holdings per rebalance")
    st.dataframe(holdings_frame(result), width="stretch")
with right:
    st.subheader("Metrics")
    st.dataframe(metrics.round(4), width="stretch")

st.caption(
    "Known limitations: today's index membership applied historically "
    "(survivorship bias), EPS frozen at the latest trailing-twelve-month "
    "snapshot, no transaction costs. See the README for details."
)
