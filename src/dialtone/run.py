"""Run one model over the manifest under each condition. Resumable.

Every utterance's result is appended to results/<run>/<condition>.jsonl as
soon as its batch finishes; on restart, ids already present are skipped. A
crash costs at most one batch.

Batches are formed by total audio seconds, longest utterances first, rather
than by a fixed count: sixteen 30-second clips and sixteen 3-second clips are
very different amounts of GPU memory, and the fixed-count version fell over
on an 8 GB card partway through LibriSpeech. If a batch still fails for lack
of GPU capacity, it is retried one utterance at a time.
"""

from __future__ import annotations

import json
import os
import platform
import time
from collections.abc import Iterator
from pathlib import Path

# Batches change shape constantly (longest-first, then many short clips). The
# default caching allocator fragments under that and eventually fails with a
# raw CUDA OOM even though plenty of memory is free. Expandable segments fix
# it; must be set before torch initialises CUDA.
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

import torch  # noqa: E402
from tqdm import tqdm

from . import __version__, data, degrade, models


def _done(path: Path, key=lambda r: r["id"]) -> set:
    """Keys of rows already written to a jsonl (default: utterance id)."""
    if not path.exists():
        return set()
    lines = path.read_text(encoding="utf-8").splitlines()
    return {key(json.loads(l)) for l in lines if l.strip()}


def _batches(ids: list[str], dur: dict[str, float], max_items: int, max_seconds: float) -> Iterator[list[str]]:
    batch: list[str] = []
    secs = 0.0
    for i in sorted(ids, key=lambda i: -dur[i]):
        if batch and (len(batch) >= max_items or secs + dur[i] > max_seconds):
            yield batch
            batch, secs = [], 0.0
        batch.append(i)
        secs += dur[i]
    if batch:
        yield batch


def _capacity_error(e: Exception) -> bool:
    s = str(e).lower()
    return isinstance(e, torch.cuda.OutOfMemoryError) or "out of memory" in s or "unable to find an engine" in s


def _transcribe(m, audios: list) -> list[str]:
    try:
        return m.transcribe(audios)
    except RuntimeError as e:
        if len(audios) == 1 or not _capacity_error(e):
            raise
        torch.cuda.empty_cache()
        return [h for a in audios for h in _transcribe(m, [a])]


def run(
    model: str,
    manifest: Path,
    conditions: list[str],
    out: Path,
    data_dir: Path,
    batch_size: int = 16,
    max_batch_seconds: float = 160.0,
    dtype: str = "auto",
    device: str | None = None,
    limit: int | None = None,
) -> None:
    root = data.fetch(data_dir)
    utts = data.index(root)
    ids = data.read_manifest(manifest)
    if limit:
        ids = ids[:limit]
    missing = [i for i in ids if i not in utts]
    if missing:
        raise SystemExit(f"{len(missing)} manifest ids not found in {root}: {missing[:3]}...")
    dur = {i: data.duration(utts[i]["path"]) for i in ids}

    out.mkdir(parents=True, exist_ok=True)
    pending = [c for c in conditions if any(i not in _done(out / f"{c}.jsonl") for i in ids)]
    if not pending:
        print(f"all conditions already complete for {len(ids)} utterances; nothing to load")
        return
    m = models.load(model, dtype=dtype, device=device)
    pool = degrade.BabblePool.from_index(utts) if degrade.needs_pool(pending) else None
    # An adapter may know its own memory ceilings; never exceed them.
    max_batch_seconds = min(max_batch_seconds, getattr(m, "max_batch_seconds", max_batch_seconds))
    batch_size = min(batch_size, getattr(m, "max_batch_items", batch_size))

    import transformers

    record = {
        "dialtone": __version__,
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
        "batching": {"max_items": batch_size, "max_seconds": max_batch_seconds, "order": "longest first"},
        "conditions": {c: degrade.describe(c) for c in conditions},
        "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    (out / "run.json").write_text(json.dumps(record, indent=2), encoding="utf-8", newline="\n")

    for cond in conditions:
        path = out / f"{cond}.jsonl"
        todo = [i for i in ids if i not in _done(path)]
        if not todo:
            print(f"[{cond}] already complete ({len(ids)} utterances)")
            continue
        print(f"[{cond}] {len(todo)} to do, {len(ids) - len(todo)} already done")
        batches = list(_batches(todo, dur, batch_size, max_batch_seconds))
        with path.open("a", encoding="utf-8", newline="\n") as fh:
            for batch in tqdm(batches, desc=cond, unit="batch"):
                audios = [
                    degrade.apply(
                        data.load_audio(utts[i]["path"]), cond, degrade.Context(pool=pool, speaker=utts[i]["speaker"])
                    )
                    for i in batch
                ]
                t0 = time.perf_counter()
                hyps = _transcribe(m, audios)
                dt = time.perf_counter() - t0
                for i, a, h in zip(batch, audios, hyps):
                    row = {
                        "id": i,
                        "condition": cond,
                        "ref": utts[i]["text"],
                        "hyp": h,
                        "audio_s": round(len(a) / data.SR, 3),
                        "compute_s": round(dt / len(batch), 4),
                    }
                    fh.write(json.dumps(row) + "\n")
                fh.flush()
                if m.device.startswith("cuda"):
                    torch.cuda.empty_cache()  # shapes differ batch to batch; don't let the cache grow
