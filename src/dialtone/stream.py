"""Simulated streaming: transcribe growing prefixes of every utterance. Resumable.

A phone agent hears audio a slice at a time. To measure how a model's transcript
*settles*, each utterance is fed as prefixes `y[:1.0 s], y[:1.5 s], ..., y[:T]` and
every prefix is transcribed independently by the ordinary batch adapter. No state is
carried between prefixes and no streaming decoder is involved, so this is an upper
bound on partial quality (each prefix sees everything heard so far) and a gross upper
bound on cost (the corpus is re-decoded ~11x). It answers: how much does an offline
model's answer churn as audio arrives?

Order of operations, per utterance and condition - non-negotiable:
  1. degrade the FULL clip once (`degrade.apply`), because noise is seeded from the
     clip's bytes and the SNR is a whole-clip quantity;
  2. slice that one degraded signal into prefixes.
Degrading each prefix separately would give every prefix a different noise
realisation and level, and the settle metrics would be measuring that instead of the
model.

Resumability is per (utterance, prefix length). The prefix grid is a pure function
of the clip's duration, so a restart can never produce a different set of prefixes.
"""

from __future__ import annotations

import json
import platform
import time
from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path

from . import run as _run  # noqa: F401  (sets PYTORCH_CUDA_ALLOC_CONF before torch loads)
import torch
from tqdm import tqdm

from . import __version__, data, degrade, models

FIRST = 1.0  # seconds; must keep first*SR >= Qwen3-ASR's min_length (8000 samples)
STEP = 0.5
EPS = 0.1  # a prefix closer than this to the full clip is not worth decoding twice


def prefix_grid(dur: float, first: float = FIRST, step: float = STEP, eps: float = EPS) -> list[float]:
    """[first, first+step, ...] while t < dur - eps, then the full duration.

    prefix_grid(3.2) -> [1.0, 1.5, 2.0, 2.5, 3.0, 3.2]
    prefix_grid(1.6) -> [1.0, 1.6]      (1.5 is within eps of the end)
    prefix_grid(0.7) -> [0.7]           (shorter than the first prefix: one point)
    """
    grid: list[float] = []
    k = 0
    while True:
        t = round(first + k * step, 3)
        if t >= dur - eps:
            break
        grid.append(t)
        k += 1
    grid.append(round(dur, 3))
    return grid


def prefix_batches(ts: list[float], max_items: int, max_seconds: float) -> Iterator[list[float]]:
    """Batches of prefix lengths for ONE utterance, longest first, under both caps."""
    yield from _run._batches(ts, {t: t for t in ts}, max_items, max_seconds)


def run(
    model: str,
    manifest: Path,
    conditions: list[str],
    out: Path,
    data_dir: Path,
    first: float = FIRST,
    step: float = STEP,
    batch_size: int = 16,
    max_batch_seconds: float = 160.0,
    dtype: str = "auto",
    device: str | None = None,
    limit: int | None = None,
) -> None:
    if first * data.SR < 8000:
        raise SystemExit("--first must be >= 0.5 s: Qwen3-ASR zero-pads anything shorter, which would be benchmarked as audio")
    root = data.fetch(data_dir)
    utts = data.index(root)
    ids = data.read_manifest(manifest)
    if limit:
        ids = ids[:limit]
    missing = [i for i in ids if i not in utts]
    if missing:
        raise SystemExit(f"{len(missing)} manifest ids not found in {root}: {missing[:3]}...")
    dur = {i: round(data.duration(utts[i]["path"]), 3) for i in ids}
    grids = {i: prefix_grid(dur[i], first, step) for i in ids}

    out.mkdir(parents=True, exist_ok=True)
    key = lambda r: (r["id"], r["t"])  # noqa: E731
    pending: dict[str, dict[str, list[float]]] = {}
    for cond in conditions:
        done = _run._done(out / f"{cond}.jsonl", key)
        todo: dict[str, list[float]] = defaultdict(list)
        for i in ids:
            for t in grids[i]:
                if (i, t) not in done:
                    todo[i].append(t)
        pending[cond] = dict(todo)
    if not any(pending.values()):
        print(f"all conditions already complete for {len(ids)} utterances; nothing to load")
        return

    m = models.load(model, dtype=dtype, device=device)
    max_batch_seconds = min(max_batch_seconds, getattr(m, "max_batch_seconds", max_batch_seconds))
    batch_size = min(batch_size, getattr(m, "max_batch_items", batch_size))
    pool = degrade.BabblePool.from_index(utts) if degrade.needs_pool(conditions) else None

    import transformers

    n_prefixes = sum(len(g) for g in grids.values())
    record = {
        "dialtone": __version__,
        "kind": "stream",
        "model": model,
        "backend": m.backend,
        "adapter": m.info(),
        "dtype": str(m.dtype).replace("torch.", ""),
        "device": m.device,
        "gpu": torch.cuda.get_device_name(0) if m.device.startswith("cuda") else None,
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "python": platform.python_version(),
        "manifest": str(manifest),
        "manifest_header": manifest.read_text(encoding="utf-8").splitlines()[0],
        "n": len(ids),
        "audio_s": round(sum(dur.values()), 1),
        "prefixes": {
            "first": first,
            "step": step,
            "eps": EPS,
            "n_prefixes": n_prefixes,
            "prefix_audio_s": round(sum(sum(g) for g in grids.values()), 1),
        },
        "batching": {
            "max_items": batch_size,
            "max_seconds": max_batch_seconds,
            "order": "one utterance per batch group, longest prefix first",
        },
        "conditions": {c: degrade.describe(c) for c in conditions},
        "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    (out / "stream.json").write_text(json.dumps(record, indent=2), encoding="utf-8", newline="\n")

    for cond in conditions:
        todo = pending[cond]
        path = out / f"{cond}.jsonl"
        if not todo:
            print(f"[{cond}] already complete ({n_prefixes} prefixes)")
            continue
        n_todo = sum(len(v) for v in todo.values())
        print(f"[{cond}] {n_todo} prefixes to do over {len(todo)} utterances, {n_prefixes - n_todo} already done")
        with path.open("a", encoding="utf-8", newline="\n") as fh:
            for uid in tqdm(list(todo), desc=cond, unit="utt"):
                y = degrade.apply(
                    data.load_audio(utts[uid]["path"]), cond, degrade.Context(pool=pool, speaker=utts[uid]["speaker"])
                )
                final_t = grids[uid][-1]
                for batch_ts in prefix_batches(todo[uid], batch_size, max_batch_seconds):
                    audios = [y if t == final_t else y[: int(round(t * data.SR))] for t in batch_ts]
                    t0 = time.perf_counter()
                    hyps = _run._transcribe(m, audios)
                    dt = time.perf_counter() - t0
                    for t, a, h in zip(batch_ts, audios, hyps):
                        row = {
                            "id": uid,
                            "condition": cond,
                            "t": t,
                            "final": t == final_t,
                            "ref": utts[uid]["text"],
                            "hyp": h,
                            "audio_s": round(len(a) / data.SR, 3),
                            "compute_s": round(dt / len(batch_ts), 4),
                            "batch_n": len(batch_ts),
                        }
                        fh.write(json.dumps(row) + "\n")
                    fh.flush()
                    if m.device.startswith("cuda"):
                        torch.cuda.empty_cache()
