"""Summarise result directories: one table per model, two tables across models."""

from __future__ import annotations

import json
from pathlib import Path

from . import degrade, normalize, score


def _rows(f: Path, norm) -> dict[str, dict]:
    """utterance id -> per-utterance error counts, plus audio/compute seconds."""
    out = {}
    for l in f.read_text(encoding="utf-8").splitlines():
        if not l.strip():
            continue
        r = json.loads(l)
        (per,) = score.per_utterance([norm(r["ref"])], [norm(r["hyp"])])
        out[r["id"]] = {**per, "audio_s": r["audio_s"], "compute_s": r["compute_s"]}
    return out


def summarize(out: Path, normalizer: str = "whisper_en") -> dict:
    record = json.loads((out / "run.json").read_text(encoding="utf-8"))
    norm = normalize.get(normalizer)

    per_cond = {f.stem: _rows(f, norm) for f in sorted(out.glob("*.jsonl"))}
    clean = per_cond.get("clean")

    rows: dict[str, dict] = {}
    for cond, by_id in per_cond.items():
        per = list(by_id.values())
        p = score.pooled(per)
        lo, hi = score.bootstrap_ci(per)
        audio = sum(r["audio_s"] for r in per)
        compute = sum(r["compute_s"] for r in per)
        row = {
            **p,
            "ci95": [lo, hi],
            "utterances": len(per),
            "audio_s": audio,
            "compute_s": compute,
            "rtf": compute / audio if audio else None,
            "gap_abs": None,
            "gap_rel": None,
            "gap_ci95": None,
        }
        if clean and cond != "clean":
            ids = [i for i in by_id if i in clean]  # paired on the same utterances
            base = [clean[i] for i in ids]
            other = [by_id[i] for i in ids]
            wc, wo = score.pooled(base)["wer"], score.pooled(other)["wer"]
            row["gap_abs"] = wo - wc
            row["gap_rel"] = (wo / wc - 1) if wc else None
            row["gap_ci95"] = list(score.bootstrap_gap_ci(base, other))
        rows[cond] = row

    summary = {
        "name": out.name,
        "model": record["model"],
        "dtype": record.get("dtype"),
        "normalizer": normalizer,
        "n": record["n"],
        "conditions": rows,
    }
    (out / f"summary.{normalizer}.json").write_text(json.dumps(summary, indent=2), encoding="utf-8", newline="\n")
    (out / f"summary.{normalizer}.md").write_text(as_markdown(summary), encoding="utf-8", newline="\n")
    return summary


def _order(conds) -> list[str]:
    """clean first, then the chain order profiles are defined in, then anything unknown."""
    known = [c for c in degrade.PROFILES if c in conds]
    return known + sorted(c for c in conds if c not in degrade.PROFILES)


def _gap(r: dict) -> str:
    """'+0.25 pp [+0.12, +0.38]' - the paired interval is the part that matters."""
    if r.get("gap_abs") is None:
        return "—"
    s = f"{r['gap_abs'] * 100:+.2f} pp"
    if r.get("gap_ci95"):
        lo, hi = r["gap_ci95"]
        s += f" [{lo * 100:+.2f}, {hi * 100:+.2f}]"
    return s


def as_markdown(s: dict) -> str:
    lines = [
        f"model: `{s['model']}`  dtype: `{s.get('dtype')}`  normaliser: `{s['normalizer']}`  n = {s['n']} utterances",
        "",
        "| condition | WER | 95% CI | gap vs clean, paired 95% CI | S / D / I | ref words | RTF |",
        "|---|---:|:---:|---:|:---:|---:|---:|",
    ]
    for cond in _order(s["conditions"]):
        r = s["conditions"][cond]
        rtf = "—" if r["rtf"] is None else f"{r['rtf']:.3f}"
        lines.append(
            f"| {cond} | {r['wer'] * 100:.2f}% | {r['ci95'][0] * 100:.2f}–{r['ci95'][1] * 100:.2f} | {_gap(r)} "
            f"| {r['S']} / {r['D']} / {r['I']} | {r['N']} | {rtf} |"
        )
    return "\n".join(lines) + "\n"


def compare(dirs: list[Path], normalizer: str = "whisper_en") -> tuple[dict, str]:
    """Two tables: WER per condition, then the paired gap vs clean per condition."""
    summaries = {d.name: summarize(d, normalizer) for d in dirs}
    conds = _order({c for s in summaries.values() for c in s["conditions"]})
    n = next(iter(summaries.values()))["n"]

    def cell(s, c):
        r = s["conditions"].get(c)
        return "—" if r is None else f"{r['wer'] * 100:.2f}%"

    def rtf(s):
        rc = s["conditions"].get("clean", {}).get("rtf")
        return "—" if rc is None else f"{rc:.3f}"

    lines = [f"normaliser: `{normalizer}`  n = {n} utterances", "", "**WER by condition**", ""]
    lines.append("| model | " + " | ".join(conds) + " | RTF (clean) |")
    lines.append("|---|" + "---:|" * len(conds) + "---:|")
    for name, s in summaries.items():
        lines.append(f"| {name} (`{s.get('dtype')}`) | " + " | ".join(cell(s, c) for c in conds) + f" | {rtf(s)} |")

    gaps = [c for c in conds if c != "clean"]
    lines += ["", "**Gap vs clean, percentage points, paired bootstrap 95% CI** (an interval that excludes 0 means the condition really moved the model)", ""]
    lines.append("| model | " + " | ".join(gaps) + " |")
    lines.append("|---|" + "---:|" * len(gaps))
    for name, s in summaries.items():
        cells = [("—" if s["conditions"].get(c) is None else _gap(s["conditions"][c])) for c in gaps]
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    return summaries, "\n".join(lines) + "\n"
