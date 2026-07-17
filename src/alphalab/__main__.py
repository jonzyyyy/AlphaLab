"""Headless entry point: `python -m alphalab`."""

from __future__ import annotations

import argparse
import logging

from alphalab.config import Settings
from alphalab.pipeline import holdings_frame, run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m alphalab",
        description="Run the value+momentum backtest against SPY.",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Re-download universe, fundamentals, and prices "
        "(universe refresh makes ~500 yfinance requests)",
    )
    parser.add_argument("--universe-size", type=int, default=None)
    parser.add_argument("--years", type=int, default=None)
    parser.add_argument("--top-n", type=int, default=None)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    overrides = {
        key: value
        for key, value in {
            "universe_size": args.universe_size,
            "data_years": args.years,
            "top_n_stocks": args.top_n,
        }.items()
        if value is not None
    }
    settings = Settings(**overrides)

    output = run_pipeline(settings, refresh=args.refresh)

    print("\nHoldings per rebalance date:")
    print(holdings_frame(output["result"]).to_string())
    print("\nPerformance over the test period:")
    print(output["metrics"].round(4).to_string())


if __name__ == "__main__":
    main()
