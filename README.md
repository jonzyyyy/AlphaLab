# AlphaLab

A small, self-contained quantitative research project: a cross-sectional
**value + momentum** strategy on the S&P 500, backtested point-in-time and
benchmarked against SPY. Everything runs locally on a laptop — the default
run makes two batch price downloads, caches them to disk (~0.5 MB), and
completes in seconds.

## Strategy

1. **Universe** — the largest S&P 500 names by market cap (default 100).
2. **Factors**, evaluated at each rebalance date using only data up to that date:
   - *Value*: trailing P/E = price as of the rebalance date ÷ trailing-12-month EPS (lower is better). Negative-earnings names are excluded from the value ranking.
   - *Momentum*: trailing 126-trading-day (~6 month) return (higher is better).
3. **Selection** — stocks are ranked on each factor, ranks are averaged, and the top 5 composite names are held equal-weight.
4. **Rebalancing** — quarterly.
5. **Evaluation** — the last 30% of the sample is an out-of-sample test window; strategy and SPY returns are measured over the same dates and summarized by one shared metrics function (total/annualized return, volatility, Sharpe).

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Three entry points, all driving the same `alphalab` package:

```bash
python -m alphalab                 # headless run: holdings + metrics table
streamlit run app.py               # interactive dashboard at localhost:8501
```

For the step-by-step walkthrough, open `notebooks/research.ipynb` in VS Code
(or any Jupyter frontend) and select the `.venv` kernel.

Useful flags: `python -m alphalab --universe-size 50 --years 3 --top-n 10`.

## Project layout

```
src/alphalab/
├── config.py      # Settings dataclass + data paths
├── data.py        # universe, EPS, and price loading with on-disk caches
├── factors.py     # Factor interface, Momentum, Value
├── selection.py   # rank-based composite selection
├── metrics.py     # the single shared performance-metrics function
├── backtest.py    # quarterly point-in-time backtest
├── pipeline.py    # end-to-end orchestration (CLI/notebook/app all use this)
└── plotting.py    # matplotlib chart
app.py             # Streamlit UI (UI only — no strategy logic)
notebooks/research.ipynb
data/              # committed snapshots + gitignored price cache
archive/           # original Colab notebooks kept for reference
```

## Data and caching

- `data/sp500_market_caps.csv` and `data/fundamentals.csv` are committed
  snapshots, so a fresh clone never fires per-ticker requests. Rebuilding
  them (`python -m alphalab --refresh`) makes one yfinance `.info` request
  per ticker (~500 for the full universe) and takes several minutes — it is
  deliberately opt-in.
- Prices are fetched in a single batch `yf.download` and cached as parquet
  in `data/cache/`, keyed by ticker set and date range. Reruns are fully
  offline. Delete `data/cache/` at any time to reclaim space or force fresh
  data; a default run recreates ~0.5 MB.
- To shrink the footprint further, lower `universe_size` or `data_years` in
  `Settings` (or the CLI flags / app sidebar).

## Methodology notes and known limitations

Stated up front because they matter for interpreting the results:

- **Survivorship bias.** The universe is *today's* S&P 500 membership applied
  historically. Companies that left the index are absent, which flatters
  returns.
- **Frozen EPS in the value factor.** P/E at each rebalance uses the price as
  of that date (point-in-time) but a *current* trailing-12-month EPS snapshot.
  Truly point-in-time EPS was evaluated and rejected: yfinance only exposes
  ~4–5 quarters of income statements, which cannot reconstruct TTM EPS at the
  earlier rebalance dates, and interpolating it would be false precision. The
  residual bias is that EPS is "known" at most a few quarters early. (The
  original Colab version used *today's price and EPS* at every historical
  date, which invalidated the backtest entirely; that is fixed.)
- **No transaction costs or slippage.** Quarterly turnover on a 5-stock book
  is modest, but costs are not modeled.
- **Single train/test split.** One out-of-sample window; results are
  period-sensitive. The train window is used only as factor lookback history —
  no parameters are fitted to it.

## Roadmap

- Max drawdown and turnover in the metrics table
- Simple transaction-cost model
- Walk-forward evaluation instead of a single split
- Point-in-time universe membership
- Unit tests for metrics and selection
