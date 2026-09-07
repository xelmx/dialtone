"""Look past the headline number: which utterances moved, and why.

WER is a pooled count. It cannot tell "the phone line broke 11 sentences"
from "the phone line reshuffled which words were wrong". This module can.

For each results directory it reports, per condition, how many utterances got
a *different* transcript than on clean audio, how many have any error, and
how many went from fully correct on clean to wrong. Across several
directories it lists the utterances every model gets wrong on clean audio -
those are reference/normaliser problems, not model problems, and they set
the floor under which WER differences are meaningless.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import normalize


def _load(out: Path, norm) -> dict[str, dict[str, dict]]:
    """condition -> id -> {ref, hyp} (normalised)."""
    by_cond: dict[str, dict[str, dict]] = {}
    for f in sorted(out.glob("*.jsonl")):
        recs = {}
        for l in f.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                recs[r["id"]] = {"ref": norm(r["ref"]), "hyp": norm(r["hyp"])}
        by_cond[f.stem] = recs
    return by_cond


def churn(by_cond: dict[str, dict[str, dict]]) -> dict[str, dict]:
    clean = by_cond.get("clean", {})
    ids = [i for i in clean]
    rows = {}
    for cond, recs in by_cond.items():
        common = [i for i in ids if i in recs]
        rows[cond] = {
            "n": len(common),
            "changed_vs_clean": sum(recs[i]["hyp"] != clean[i]["hyp"] for i in common),
            "with_errors": sum(recs[i]["hyp"] != recs[i]["ref"] for i in common),
            "right_to_wrong": sum(clean[i]["hyp"] == clean[i]["ref"] and recs[i]["hyp"] != recs[i]["ref"] for i in common),
            "wrong_to_right": sum(clean[i]["hyp"] != clean[i]["ref"] and recs[i]["hyp"] == recs[i]["ref"] for i in common),
        }
    return rows


def right_to_wrong(by_cond, cond: str, k: int = 8) -> list[tuple[str, str, str]]:
    clean, recs = by_cond["clean"], by_cond[cond]
    out = []
    for i in clean:
        if i in recs and clean[i]["hyp"] == clean[i]["ref"] and recs[i]["hyp"] != recs[i]["ref"]:
            out.append((i, recs[i]["ref"], recs[i]["hyp"]))
            if len(out) >= k:
                break
    return out


def shared_clean_errors(loaded: dict[str, dict]) -> list[str]:
    """ids every model gets wrong on clean audio."""
    sets = [{i for i, r in d["clean"].items() if r["hyp"] != r["ref"]} for d in loaded.values() if "clean" in d]
    return sorted(set.intersection(*sets)) if sets else []


def report(dirs: list[Path], normalizer: str = "whisper_en", worst: str | None = None, k: int = 8) -> str:
    norm = normalize.get(normalizer)
    loaded = {d.name: _load(d, norm) for d in dirs}
    lines = [f"normaliser: `{normalizer}`", ""]

    lines += ["| model | condition | n | changed vs clean | with errors | right→wrong | wrong→right |", "|---|---|---:|---:|---:|---:|---:|"]
    for name, by_cond in loaded.items():
        for cond, r in churn(by_cond).items():
            lines.append(f"| {name} | {cond} | {r['n']} | {r['changed_vs_clean']} | {r['with_errors']} | {r['right_to_wrong']} | {r['wrong_to_right']} |")

    if len(loaded) > 1:
        shared = shared_clean_errors(loaded)
        n = min(len(d["clean"]) for d in loaded.values())
        lines += ["", f"**Utterances every model gets wrong on clean audio: {len(shared)} of {n}** ({len(shared) / n * 100:.1f}%) — reference/normaliser artefacts, the floor under the numbers."]
        first = next(iter(loaded.values()))
        for i in shared[:5]:
            lines.append(f"- `{i}` ref: {first['clean'][i]['ref'][:120]}")

    for name, by_cond in loaded.items():
        conds = [c for c in by_cond if c != "clean"]
        if not conds:
            continue
        w = worst or max(conds, key=lambda c: churn(by_cond)[c]["right_to_wrong"])
        ex = right_to_wrong(by_cond, w, k)
        lines += ["", f"**{name} — correct on clean, wrong on `{w}` ({len(ex)} shown)**"]
        for i, ref, hyp in ex:
            lines += [f"- `{i}`", f"  - ref: {ref[:140]}", f"  - {w}: {hyp[:140]}"]
    return "\n".join(lines) + "\n"
