"""Word error rate with an honest uncertainty band.

WER = (substitutions + deletions + insertions) / reference words, pooled over
the whole set. The bootstrap resamples *utterances* (not words) 1000 times to
give a 95% interval, because utterances are the independent unit here.
"""

from __future__ import annotations

import jiwer
import numpy as np


def per_utterance(refs: list[str], hyps: list[str]) -> list[dict]:
    rows = []
    for r, h in zip(refs, hyps):
        o = jiwer.process_words(r, h)
        rows.append({"S": o.substitutions, "D": o.deletions, "I": o.insertions, "N": len(r.split())})
    return rows


def pooled(rows: list[dict]) -> dict:
    S = sum(r["S"] for r in rows)
    D = sum(r["D"] for r in rows)
    I = sum(r["I"] for r in rows)
    N = sum(r["N"] for r in rows)
    return {"S": S, "D": D, "I": I, "N": N, "wer": (S + D + I) / N if N else float("nan")}


def bootstrap_ci(rows: list[dict], n_boot: int = 1000, seed: int = 0) -> tuple[float, float]:
    err = np.array([r["S"] + r["D"] + r["I"] for r in rows], dtype=np.float64)
    n = np.array([r["N"] for r in rows], dtype=np.float64)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(rows), size=(n_boot, len(rows)))
    w = err[idx].sum(axis=1) / n[idx].sum(axis=1)
    lo, hi = np.percentile(w, [2.5, 97.5])
    return float(lo), float(hi)


def bootstrap_gap_ci(
    base: list[dict], other: list[dict], n_boot: int = 1000, seed: int = 0
) -> tuple[float, float]:
    """95% CI of WER(other) - WER(base) for the *same* utterances, paired.

    Two conditions of one model are scored on identical utterances, so their
    difference should be resampled jointly: draw a set of utterances, score
    both conditions on that set, take the difference. This is much tighter
    than comparing two independent intervals and is the right test for
    "did the phone line hurt this model".
    `base[i]` and `other[i]` must be the same utterance.
    """
    if len(base) != len(other):
        raise ValueError("paired bootstrap needs aligned rows")
    eb = np.array([r["S"] + r["D"] + r["I"] for r in base], dtype=np.float64)
    eo = np.array([r["S"] + r["D"] + r["I"] for r in other], dtype=np.float64)
    n = np.array([r["N"] for r in base], dtype=np.float64)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(base), size=(n_boot, len(base)))
    tot = n[idx].sum(axis=1)
    gap = eo[idx].sum(axis=1) / tot - eb[idx].sum(axis=1) / tot
    lo, hi = np.percentile(gap, [2.5, 97.5])
    return float(lo), float(hi)
