"""Cross-sectional stock selection from a factor table."""

from __future__ import annotations

import pandas as pd

from alphalab.factors import Factor


def select_stocks(
    factor_table: pd.DataFrame, factors: list[Factor], top_n: int
) -> list[str]:
    """Pick the `top_n` tickers with the best equal-weighted factor ranks.

    Each factor is ranked so that rank 1 is best (direction taken from
    `higher_is_better`); tickers missing a factor value are ranked last for
    that factor rather than dropped, so a stock with strong momentum but no
    meaningful P/E can still be selected. The composite score is the mean
    rank across factors.
    """
    ranks = pd.DataFrame(index=factor_table.index)
    for factor in factors:
        ranks[factor.name] = factor_table[factor.name].rank(
            ascending=not factor.higher_is_better, na_option="bottom"
        )
    composite = ranks.mean(axis=1)
    return composite.nsmallest(min(top_n, len(composite))).index.tolist()
