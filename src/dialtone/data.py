"""LibriSpeech test-clean: fetch, index, and pin a reproducible subset.

Why this set: it is free (CC BY 4.0), small (~350 MB, 5.4 h, 2620 utterances,
40 speakers), and every recording ships with the exact words spoken. That
answer key is what makes speech-to-text scoreable at all.
"""

from __future__ import annotations

import random
import tarfile
import urllib.request
from pathlib import Path

import numpy as np
import soundfile as sf
from tqdm import tqdm

SUBSET = "test-clean"
URL = f"https://www.openslr.org/resources/12/{SUBSET}.tar.gz"
SR = 16_000


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(url) as r, tmp.open("wb") as f, tqdm(
        total=int(r.headers.get("Content-Length", 0)), unit="B", unit_scale=True, desc=dest.name
    ) as bar:
        while chunk := r.read(1 << 20):
            f.write(chunk)
            bar.update(len(chunk))
    tmp.replace(dest)


def fetch(data_dir: Path) -> Path:
    """Ensure LibriSpeech/test-clean is extracted under data_dir; return its root."""
    root = data_dir / "LibriSpeech" / SUBSET
    if root.exists():
        return root
    tgz = data_dir / f"{SUBSET}.tar.gz"
    if not tgz.exists():
        _download(URL, tgz)
    with tarfile.open(tgz) as t:
        t.extractall(data_dir, filter="data")
    return root


def index(root: Path) -> dict[str, dict]:
    """utterance id -> {id, speaker, chapter, text, path}."""
    utts: dict[str, dict] = {}
    for trans in sorted(root.rglob("*.trans.txt")):
        for line in trans.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            uid, text = line.split(" ", 1)
            spk, chap, _ = uid.split("-")
            utts[uid] = {
                "id": uid,
                "speaker": spk,
                "chapter": chap,
                "text": text,
                "path": str(trans.parent / f"{uid}.flac"),
            }
    return utts


def make_manifest(utts: dict[str, dict], n: int, seed: int, out: Path) -> list[str]:
    """Seeded sample of n ids, written sorted with its provenance in a header line.

    Commit the file. Never regenerate it with a different seed once results exist.
    """
    ids = sorted(utts)
    picked = sorted(random.Random(seed).sample(ids, n))
    out.parent.mkdir(parents=True, exist_ok=True)
    header = f"# source=librispeech/{SUBSET} n={n} seed={seed} pool={len(ids)}\n"
    out.write_text(header + "\n".join(picked) + "\n", encoding="utf-8", newline="\n")
    return picked


def read_manifest(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [l.strip() for l in lines if l.strip() and not l.startswith("#")]


def duration(path: str | Path) -> float:
    """Seconds, from the header only - no decode."""
    return sf.info(str(path)).duration


def load_audio(path: str | Path) -> np.ndarray:
    """float32 mono at 16 kHz. Refuses anything else rather than resampling quietly."""
    x, sr = sf.read(str(path), dtype="float32", always_2d=False)
    if sr != SR:
        raise ValueError(f"{path}: expected {SR} Hz, got {sr}")
    if x.ndim > 1:
        x = x.mean(axis=1)
    return x
