"""Settle metrics: how fast does a transcript stop changing as audio arrives?

Input: for one utterance, the partial transcripts H_t at each prefix length t, the
final H_T, the reference, and the true end time of every reference word.

All comparisons are alignment-based (jiwer), never positional. If H_2.0 = "he hoped
there" and H_2.5 = "and he hoped there would", positional comparison says every word
changed; the alignment absorbs "and" as one insertion and keeps the rest equal -
which is what someone watching the caption actually experiences. The same property
means a hallucinated 200-word partial only costs the words it genuinely displaced.

Metrics
-------
stable time   s_i: smallest prefix length from which final word i is present (aligned
              equal) in every later partial. When the model committed to the word.
emission lag  s_i - end_r for final words that are hits against reference word r.
              Only hits: a word the model never got right has no reference time.
              Negative lags are kept (a model can commit before the word ends).
revisions     word edits between consecutive partials, excluding a pure trailing
              append. Per 100 final words. How often the model takes back its words.
unstable tail trailing words of a partial that do not survive to the final. How many
              words behind the cursor can't be trusted yet.
agreement     smallest t from which H_t == H_T for good, as seconds before the end.
compute       total model time over all prefixes / T; prefix audio / T (~11.5).
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import jiwer
import numpy as np

from . import align as _align
from . import normalize, report, stream


@dataclass(frozen=True)
class Chunk:
    type: str
    rs: int
    re: int
    hs: int
    he: int


def tokens(s: str) -> list[str]:
    return s.split()


def chunks(ref: str, hyp: str) -> list[Chunk]:
    """jiwer word alignment, with the empty cases handled explicitly."""
    r, h = tokens(ref), tokens(hyp)
    if not r and not h:
        return []
    if not r:
        return [Chunk("insert", 0, 0, 0, len(h))]
    if not h:
        return [Chunk("delete", 0, len(r), 0, 0)]
    o = jiwer.process_words(" ".join(r), " ".join(h))
    return [Chunk(c.type, c.ref_start_idx, c.ref_end_idx, c.hyp_start_idx, c.hyp_end_idx) for c in o.alignments[0]]


def equal_ref_indices(ref: str, hyp: str) -> set[int]:
    return {r for c in chunks(ref, hyp) if c.type == "equal" for r in range(c.rs, c.re)}


def equal_hyp_indices(ref: str, hyp: str) -> set[int]:
    return {h for c in chunks(ref, hyp) if c.type == "equal" for h in range(c.hs, c.he)}


def equal_map(ref: str, hyp: str) -> dict[int, int]:
    """reference index -> hypothesis index, equal chunks only."""
    return {c.rs + k: c.hs + k for c in chunks(ref, hyp) if c.type == "equal" for k in range(c.re - c.rs)}


# --- per-utterance metrics -----------------------------------------------------------


def stable_times(partials: list[tuple[float, str]], final: str) -> list[float]:
    """partials ascending by t, last is (T, final). One time per final word."""
    n = len(tokens(final))
    T = partials[-1][0]
    s = [T] * n
    alive = set(range(n))
    for t, h in reversed(partials[:-1]):
        alive &= equal_ref_indices(final, h)
        for i in alive:
            s[i] = t
    return s


def emission_lags(final: str, ref: str, ends: list[float | None], stable: list[float]) -> list[float | None]:
    lags: list[float | None] = [None] * len(stable)
    for r, i in equal_map(ref, final).items():
        if r < len(ends) and ends[r] is not None:
            lags[i] = stable[i] - ends[r]
    return lags


def edits_allowing_append(a: list[str], b: list[str]) -> int:
    """Fewest word edits turning a into b when appending at the end of b is free.

    Standard edit-distance DP; the answer is the minimum over every prefix of b, so
    words that merely arrived at the end cost nothing while anything taken back or
    rewritten counts. Independent of how an aligner breaks ties between equal-cost
    paths (jiwer, for "their" -> "there would", chooses insert+substitute, which would
    otherwise be counted as two revisions instead of one).
    """
    prev = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        cur = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] != b[j - 1]))
        prev = cur
    return min(prev)


def revisions(partials: list[tuple[float, str]]) -> int:
    return sum(edits_allowing_append(tokens(h0), tokens(h1)) for (_, h0), (_, h1) in zip(partials, partials[1:]))


def unstable_tail(partials: list[tuple[float, str]], final: str) -> list[int]:
    out = []
    for _, h in partials[:-1]:
        toks = tokens(h)
        if not toks:
            out.append(0)
            continue
        eq = equal_hyp_indices(final, h)
        n = 0
        for j in range(len(toks) - 1, -1, -1):
            if j in eq:
                break
            n += 1
        out.append(n)
    return out


def agreement_point(partials: list[tuple[float, str]], final: str) -> float:
    ft = tokens(final)
    t_agree = partials[-1][0]
    for t, h in reversed(partials):
        if tokens(h) == ft:
            t_agree = t
        else:
            break
    return t_agree


def per_utterance(rows: list[dict], ends: list[float | None], norm: Callable[[str], str]) -> dict:
    rows = sorted(rows, key=lambda r: r["t"])
    partials = [(r["t"], norm(r["hyp"])) for r in rows]
    final = partials[-1][1]
    ref = norm(rows[-1]["ref"])
    T = rows[-1]["audio_s"]
    stable = stable_times(partials, final)
    lags = emission_lags(final, ref, ends, stable)
    tails = unstable_tail(partials, final)
    agree_t = agreement_point(partials, final)
    n_final = len(tokens(final))
    edits = revisions(partials)
    return {
        "id": rows[-1]["id"],
        "T": T,
        "n_final_words": n_final,
        "n_ref_words": len(tokens(ref)),
        "n_prefixes": len(rows),
        "stable": stable,
        "lags": lags,
        "edits": edits,
        "rev_rate": (edits / n_final * 100) if n_final else None,
        "tail_sum": sum(tails),
        "tail_n": len(tails),
        "agree_t": agree_t,
        "agree_before_end": round(T - agree_t, 3),
        "compute_s": sum(r["compute_s"] for r in rows),
        "audio_s": sum(r["audio_s"] for r in rows),
        "empty_partials": sum(1 for _, h in partials[:-1] if not tokens(h)),
        # a decoding loop: a partial far longer than the utterance could possibly be
        "exploded_partials": sum(1 for _, h in partials[:-1] if len(tokens(h)) > 2 * n_final + 5),
        "max_partial_words": max(len(tokens(h)) for _, h in partials),
    }


def group_rows(rows: list[dict], first: float, step: float, eps: float) -> tuple[dict[str, list[dict]], list[str]]:
    """Rows by utterance; utterances whose prefix grid is incomplete are dropped, and named."""
    by: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by[r["id"]].append(r)
    ok, dropped = {}, []
    for uid, rs in by.items():
        rs.sort(key=lambda r: r["t"])
        fin = [r for r in rs if r.get("final")]
        if not fin:
            dropped.append(uid)
            continue
        expected = stream.prefix_grid(fin[-1]["audio_s"], first, step, eps)
        got = [r["t"] for r in rs]
        if len(got) != len(expected) or any(abs(a - b) > 1e-3 for a, b in zip(got, expected)):
            dropped.append(uid)
            continue
        ok[uid] = rs
    return ok, dropped


# --- aggregation with utterance-level bootstrap ------------------------------------------


def _idx(n: int, n_boot: int = 1000, seed: int = 0) -> np.ndarray:
    return np.random.default_rng(seed).integers(0, n, size=(n_boot, n))


def ratio_draws(num: np.ndarray, den: np.ndarray, idx: np.ndarray) -> np.ndarray:
    d = den[idx].sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        return num[idx].sum(axis=1) / d


def quantile_draws(per_utt: list[np.ndarray], q: float, idx: np.ndarray) -> np.ndarray:
    """Weighted quantile of the pooled values under each utterance resample."""
    lens = np.array([len(a) for a in per_utt])
    if lens.sum() == 0:
        return np.full(len(idx), np.nan)
    vals = np.concatenate([a for a in per_utt if len(a)])
    owner = np.repeat(np.arange(len(per_utt)), lens)
    order = np.argsort(vals, kind="stable")
    vals, owner = vals[order], owner[order]
    out = np.empty(len(idx))
    for b, row in enumerate(idx):
        w = np.bincount(row, minlength=len(per_utt))[owner]
        cw = np.cumsum(w)
        if cw[-1] == 0:
            out[b] = np.nan
            continue
        out[b] = vals[np.searchsorted(cw, q * cw[-1], side="left")]
    return out


def _ci(draws: np.ndarray) -> list[float]:
    d = draws[~np.isnan(draws)]
    if len(d) == 0:
        return [float("nan"), float("nan")]
    lo, hi = np.percentile(d, [2.5, 97.5])
    return [float(lo), float(hi)]


def _arrays(per: list[dict]) -> dict[str, np.ndarray | list[np.ndarray]]:
    f = lambda k: np.array([p[k] for p in per], dtype=np.float64)  # noqa: E731
    return {
        "lags": [np.array([x for x in p["lags"] if x is not None], dtype=np.float64) for p in per],
        "n_lags": np.array([sum(x is not None for x in p["lags"]) for p in per], dtype=np.float64),
        "rev_rate": [np.array([p["rev_rate"]] if p["rev_rate"] is not None else [], dtype=np.float64) for p in per],
        "n_final": f("n_final_words"),
        "edits": f("edits"),
        "tail_sum": f("tail_sum"),
        "tail_n": f("tail_n"),
        "agree": f("agree_before_end"),
        "ones": np.ones(len(per)),
        "T": f("T"),
        "compute": f("compute_s"),
        "audio": f("audio_s"),
    }


STATS = {  # name -> (kind, numerator key, denominator key | quantile)
    "lag_median_ms": ("q", "lags", 0.5),
    "lag_p90_ms": ("q", "lags", 0.9),
    "revisions_per_100": ("r", "edits", "n_final"),  # pooled: honest, but a few decoding loops dominate it
    "revisions_per_100_median": ("q", "rev_rate", 0.5),  # per-utterance median: what a typical utterance sees
    "unstable_tail": ("r", "tail_sum", "tail_n"),
    "agree_before_end_s": ("r", "agree", "ones"),
    "agree_frac": ("r", "agree", "T"),
    "stream_rtf": ("r", "compute", "T"),
    "audio_expansion": ("r", "audio", "T"),
    "lag_defined_frac": ("r", "n_lags", "n_final"),
}
_SCALE = {"lag_median_ms": 1000.0, "lag_p90_ms": 1000.0, "revisions_per_100": 100.0}


def _draws(a: dict, name: str, idx: np.ndarray) -> np.ndarray:
    kind, num, den = STATS[name]
    d = quantile_draws(a[num], den, idx) if kind == "q" else ratio_draws(a[num], a[den], idx)
    return d * _SCALE.get(name, 1.0)


def aggregate(per: list[dict], n_boot: int = 1000, seed: int = 0) -> dict:
    a = _arrays(per)
    idx = _idx(len(per), n_boot, seed)
    point = np.arange(len(per))[None, :]
    out = {"n": len(per)}
    for name in STATS:
        out[name] = float(_draws(a, name, point)[0])
        out[name + "_ci95"] = _ci(_draws(a, name, idx))
    out["empty_partials"] = int(sum(p["empty_partials"] for p in per))
    out["exploded_partials"] = int(sum(p["exploded_partials"] for p in per))
    out["max_partial_words"] = int(max(p["max_partial_words"] for p in per))
    out["n_empty_final"] = int(sum(1 for p in per if p["n_final_words"] == 0))
    return out


DELTA_STATS = ["lag_median_ms", "lag_p90_ms", "revisions_per_100", "revisions_per_100_median", "unstable_tail", "agree_before_end_s"]


def paired_delta(base: list[dict], other: list[dict], n_boot: int = 1000, seed: int = 0) -> dict:
    """other - base on the same utterances, same resample; keys are per-utterance ids."""
    bi = {p["id"]: p for p in base}
    oi = {p["id"]: p for p in other}
    ids = [i for i in bi if i in oi]
    b, o = _arrays([bi[i] for i in ids]), _arrays([oi[i] for i in ids])
    idx = _idx(len(ids), n_boot, seed)
    point = np.arange(len(ids))[None, :]
    out = {"n": len(ids)}
    for name in DELTA_STATS:
        out[name] = float(_draws(o, name, point)[0] - _draws(b, name, point)[0])
        out[name + "_ci95"] = _ci(_draws(o, name, idx) - _draws(b, name, idx))
    return out


# --- summaries -----------------------------------------------------------------------------


def summarize(out: Path, alignments: Path | None, normalizer: str = "whisper_en") -> dict:
    record = json.loads((out / "stream.json").read_text(encoding="utf-8"))
    p = record["prefixes"]
    norm = normalize.get(normalizer)
    al = _align.load(alignments) if alignments and Path(alignments).exists() else {}
    conds: dict[str, dict] = {}
    per_all: dict[str, list[dict]] = {}
    notes = []
    for f in sorted(out.glob("*.jsonl")):
        rows = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
        groups, dropped = group_rows(rows, p["first"], p["step"], p.get("eps", stream.EPS))
        if dropped:
            notes.append(f"{f.stem}: dropped {len(dropped)} utterances with an incomplete prefix grid")
        per = []
        n_prop = n_suspect = 0
        for uid, rs in groups.items():
            ref = rs[-1]["ref"]
            row = al.get(uid)
            if row is None:
                words = _align.proportional(ref, rs[-1]["audio_s"])
                n_prop += 1
            else:
                words = row["words"]
                n_suspect += bool(row.get("suspect"))
            per.append(per_utterance(rs, _align.word_end_times(ref, words, norm), norm))
        if n_prop:
            notes.append(f"{f.stem}: {n_prop} utterances had NO forced alignment - proportional timing used; lag numbers are indicative only")
        if n_suspect:
            notes.append(f"{f.stem}: {n_suspect} utterances use alignments flagged suspect")
        conds[f.stem] = aggregate(per)
        per_all[f.stem] = per
    deltas = {}
    if "clean" in per_all:
        for c, per in per_all.items():
            if c != "clean":
                deltas[c] = paired_delta(per_all["clean"], per)
    summary = {
        "name": out.name,
        "model": record["model"],
        "dtype": record.get("dtype"),
        "normalizer": normalizer,
        "prefixes": p,
        "aligner": next(iter(al.values()))["aligner"] if al else "proportional",
        "notes": notes,
        "conditions": conds,
        "deltas_vs_clean": deltas,
    }
    (out / f"settle.{normalizer}.json").write_text(json.dumps(summary, indent=2), encoding="utf-8", newline="\n")
    (out / f"settle.{normalizer}.md").write_text(as_markdown({out.name: summary}), encoding="utf-8", newline="\n")
    for n in notes:
        print("NOTE:", n)
    return summary


def _fmt(v: float, ci: list[float], digits: int = 0, unit: str = "") -> str:
    if v != v:
        return "—"
    return f"{v:.{digits}f}{unit} [{ci[0]:.{digits}f}, {ci[1]:.{digits}f}]"


def _fmt_delta(v: float, ci: list[float], digits: int = 0) -> str:
    if v != v:
        return "—"
    return f"{v:+.{digits}f} [{ci[0]:+.{digits}f}, {ci[1]:+.{digits}f}]"


def as_markdown(summaries: dict[str, dict]) -> str:
    first = next(iter(summaries.values()))
    p = first["prefixes"]
    lines = [
        f"normaliser: `{first['normalizer']}`  prefixes: first {p['first']} s, step {p['step']} s  aligner: `{first['aligner']}`",
        "",
        "**Settle metrics** (95% bootstrap CI over utterances; lags quantised by the step, read differences not absolutes)",
        "",
        "| model | condition | n | median lag | p90 lag | lag defined | revisions /100 (pooled) | revisions /100 (median utt) | unstable tail | agree before end | stream RTF | ×audio | empty partials | exploded partials | max partial words |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, s in summaries.items():
        for cond in report._order(s["conditions"]):
            c = s["conditions"][cond]
            lines.append(
                f"| {name} | {cond} | {c['n']} | {_fmt(c['lag_median_ms'], c['lag_median_ms_ci95'], 0, ' ms')} "
                f"| {_fmt(c['lag_p90_ms'], c['lag_p90_ms_ci95'], 0, ' ms')} | {c['lag_defined_frac'] * 100:.0f}% "
                f"| {_fmt(c['revisions_per_100'], c['revisions_per_100_ci95'], 1)} | {_fmt(c['revisions_per_100_median'], c['revisions_per_100_median_ci95'], 1)} "
                f"| {_fmt(c['unstable_tail'], c['unstable_tail_ci95'], 2)} "
                f"| {_fmt(c['agree_before_end_s'], c['agree_before_end_s_ci95'], 2, ' s')} | {c['stream_rtf']:.3f} | {c['audio_expansion']:.1f} "
                f"| {c['empty_partials']} | {c['exploded_partials']} | {c['max_partial_words']} |"
            )
    if any(s["deltas_vs_clean"] for s in summaries.values()):
        lines += [
            "",
            "**Change vs clean, same utterances, paired 95% CI** (an interval that excludes 0 means the condition really changed how the model settles)",
            "",
            "| model | condition | Δ median lag | Δ p90 lag | Δ revisions /100 (pooled) | Δ revisions /100 (median utt) | Δ unstable tail | Δ agree before end |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
        for name, s in summaries.items():
            for cond, d in s["deltas_vs_clean"].items():
                lines.append(
                    f"| {name} | {cond} | {_fmt_delta(d['lag_median_ms'], d['lag_median_ms_ci95'])} ms | {_fmt_delta(d['lag_p90_ms'], d['lag_p90_ms_ci95'])} ms "
                    f"| {_fmt_delta(d['revisions_per_100'], d['revisions_per_100_ci95'], 1)} | {_fmt_delta(d['revisions_per_100_median'], d['revisions_per_100_median_ci95'], 1)} "
                    f"| {_fmt_delta(d['unstable_tail'], d['unstable_tail_ci95'], 2)} "
                    f"| {_fmt_delta(d['agree_before_end_s'], d['agree_before_end_s_ci95'], 2)} s |"
                )
    notes = [n for s in summaries.values() for n in s["notes"]]
    if notes:
        lines += ["", *[f"- NOTE: {n}" for n in notes]]
    return "\n".join(lines) + "\n"


def compare(dirs: list[Path], alignments: Path | None, normalizer: str = "whisper_en") -> tuple[dict, str]:
    summaries = {d.name: summarize(d, alignments, normalizer) for d in dirs}
    return summaries, as_markdown(summaries)
