"""Forced alignment: when was each reference word actually spoken?

The settle metrics need the true end time of every reference word, independent of
the speech-to-text models under test. That comes from *forced alignment* of the
reference transcript to the clean audio - the aligner is told the words and only has
to place them in time. Computed once per utterance and cached under
`data/alignments/`; every model and condition reuses it.

Aligner: Qwen3-ForcedAligner-0.6B, native in transformers (token classification over
80 ms segments). Loaded through `models._load_checked`: a token-classification head
with random weights would produce smooth, monotone, *meaningless* timestamps, and
transformers only warns about missing weights - so the guard is the whole defence.

`word_end_times` bridges the aligner's words (the original reference tokens) to the
tokens jiwer scores (the *normalised* reference), which can split ("million'd" ->
"1000000 would") or merge ("twenty five" -> "25").
"""

from __future__ import annotations

import json
import platform
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

import jiwer
import numpy as np

from . import run as _run  # noqa: F401  (allocator env before torch)
import torch
from tqdm import tqdm

from . import __version__, data, models

QWEN_ALIGNER = "Qwen/Qwen3-ForcedAligner-0.6B-hf"
ALIGNER_NAME = "qwen3-forced-aligner-0.6b"


@dataclass(frozen=True)
class Word:
    text: str
    start: float
    end: float


class QwenAligner:
    backend = "transformers"
    name = ALIGNER_NAME
    max_batch_items = 8
    max_batch_seconds = 120.0
    language = "English"

    def __init__(self, model: str = QWEN_ALIGNER, dtype: str = "auto", device: str | None = None):
        from transformers import AutoProcessor, Qwen3ASRForTokenClassification
        from transformers.models.qwen3_asr.feature_extraction_qwen3_asr import Qwen3ASRFeatureExtractor

        self.model_id = model
        self.device = models._device(device)
        self.dtype = models._dtype(dtype, "bf16", self.device)
        self.processor = AutoProcessor.from_pretrained(model)
        if not isinstance(self.processor.feature_extractor, Qwen3ASRFeatureExtractor):
            self.processor.feature_extractor = Qwen3ASRFeatureExtractor.from_pretrained(model)
        self.model = models._load_checked(Qwen3ASRForTokenClassification, model, dtype=self.dtype).to(self.device).eval()
        self.timestamp_token_id = self.model.config.timestamp_token_id

    def split(self, text: str) -> list[str]:
        return self.processor.split_words_for_alignment(text, self.language)

    @torch.inference_mode()
    def align(self, audios: list[np.ndarray], texts: list[str]) -> list[list[Word]]:
        inputs, word_lists = self.processor.prepare_forced_aligner_inputs(
            list(audios), list(texts), language=self.language, padding=True, return_tensors="pt"
        )
        inputs = inputs.to(self.device)
        if "input_features" in inputs:
            inputs["input_features"] = inputs["input_features"].to(self.dtype)
        logits = self.model(**inputs).logits
        out = self.processor.decode_forced_alignment(
            logits, inputs["input_ids"], word_lists, timestamp_token_id=self.timestamp_token_id
        )
        return [[Word(w["text"], float(w["start_time"]), float(w["end_time"])) for w in words] for words in out]

    def info(self) -> dict:
        return {"class": type(self.model).__name__, "language": self.language, "segment_ms": 80}


def check(words: list[Word], n_expected: int, audio_s: float) -> bool:
    """Non-empty, one per expected word, monotone, and inside the clip."""
    if not words or len(words) != n_expected:
        return False
    if any(w.end < w.start for w in words):
        return False
    if any(b.start < a.start for a, b in zip(words, words[1:])):
        return False
    return words[-1].end <= audio_s + 0.5


def proportional(text: str, duration: float) -> list[Word]:
    """Last resort: spread the duration over the characters. Labelled wherever it is used."""
    src = text.split()
    total = sum(len(w) + 1 for w in src)
    out, pos = [], 0
    for w in src:
        start = duration * pos / total
        pos += len(w) + 1
        out.append(Word(w, round(start, 3), round(duration * pos / total, 3)))
    return out


def cache_path(out: Path, name: str = ALIGNER_NAME) -> Path:
    return out / f"{name}.jsonl"


def build(
    manifest: Path,
    data_dir: Path,
    out: Path = Path("data/alignments"),
    model: str = QWEN_ALIGNER,
    dtype: str = "auto",
    device: str | None = None,
    limit: int | None = None,
    show: int = 0,
) -> Path:
    root = data.fetch(data_dir)
    utts = data.index(root)
    ids = data.read_manifest(manifest)
    if limit:
        ids = ids[:limit]
    dur = {i: data.duration(utts[i]["path"]) for i in ids}
    out.mkdir(parents=True, exist_ok=True)
    path = cache_path(out)
    todo = [i for i in ids if i not in _run._done(path)]
    if not todo:
        print(f"alignments complete for {len(ids)} utterances: {path}")
        return path

    al = QwenAligner(model, dtype, device)
    import transformers

    record = {
        "dialtone": __version__,
        "kind": "align",
        "aligner": al.name,
        "model": model,
        "info": al.info(),
        "dtype": str(al.dtype).replace("torch.", ""),
        "device": al.device,
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "python": platform.python_version(),
        "manifest": str(manifest),
        "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    path.with_suffix(".json").write_text(json.dumps(record, indent=2), encoding="utf-8", newline="\n")

    suspect = shown = 0
    batches = list(_run._batches(todo, dur, al.max_batch_items, al.max_batch_seconds))
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        for batch in tqdm(batches, desc="align", unit="batch"):
            audios = [data.load_audio(utts[i]["path"]) for i in batch]
            texts = [utts[i]["text"] for i in batch]
            try:
                words = al.align(audios, texts)
            except RuntimeError as e:
                if not _run._capacity_error(e):
                    raise
                torch.cuda.empty_cache()
                words = [al.align([a], [t])[0] for a, t in zip(audios, texts)]
            for i, a, t, w in zip(batch, audios, texts, words):
                secs = len(a) / data.SR
                ok = check(w, len(al.split(t)), secs)
                if not ok:  # once more on its own before calling it suspect
                    w = al.align([a], [t])[0]
                    ok = check(w, len(al.split(t)), secs)
                    suspect += not ok
                row = {"id": i, "aligner": al.name, "model": model, "audio_s": round(secs, 3), "words": [asdict(x) for x in w], "suspect": not ok}
                fh.write(json.dumps(row) + "\n")
                if shown < show:
                    shown += 1
                    print(f"{i}  ({secs:.2f} s){'  SUSPECT' if not ok else ''}")
                    print("   " + "  ".join(f"{x.text}[{x.start:.2f}-{x.end:.2f}]" for x in w))
            fh.flush()
    print(f"aligned {len(todo)} utterances -> {path}  ({suspect} suspect)")
    return path


def load(path: Path) -> dict[str, dict]:
    """utterance id -> cache row, `words` as Word objects."""
    rows = {}
    for l in path.read_text(encoding="utf-8").splitlines():
        if l.strip():
            r = json.loads(l)
            r["words"] = [Word(**w) for w in r["words"]]
            rows[r["id"]] = r
    return rows


def _tokens(s: str) -> list[str]:
    return s.split()


def word_end_times(ref_text: str, words: list[Word], norm: Callable[[str], str]) -> list[float | None]:
    """End time for every token of the NORMALISED reference, from the aligner's words.

    Normalise each reference word on its own to learn which normalised tokens each
    source word produces; reconcile that against the normaliser applied to the whole
    string (which can differ, e.g. merge "twenty five" -> "25") by alignment. A token
    produced by several source words gets the latest of their end times, so the
    result is monotone non-decreasing.
    """
    src = ref_text.split()
    true = _tokens(norm(ref_text))
    if not true:
        return []
    if len(words) == len(src):
        ends_src = [w.end for w in words]
    else:  # aligner split the text differently: nearest-position fallback
        ends_src = [words[min(int(j * len(words) / len(src)), len(words) - 1)].end for j in range(len(src))] if words else [None] * len(src)
    flat: list[str] = []
    origin: list[int] = []
    for j, w in enumerate(src):
        for tok in _tokens(norm(w)):
            flat.append(tok)
            origin.append(j)
    if flat == true:
        return [ends_src[o] for o in origin]

    out: list[float | None] = [None] * len(true)
    if flat:
        chunks = jiwer.process_words(" ".join(true), " ".join(flat)).alignments[0]
        for c in chunks:
            hyp_ends = [ends_src[origin[h]] for h in range(c.hyp_start_idx, c.hyp_end_idx)]
            hyp_ends = [e for e in hyp_ends if e is not None]
            if c.type == "equal":
                for k, r in enumerate(range(c.ref_start_idx, c.ref_end_idx)):
                    e = ends_src[origin[c.hyp_start_idx + k]]
                    out[r] = e
            elif c.type == "substitute":
                for r in range(c.ref_start_idx, c.ref_end_idx):
                    out[r] = max(hyp_ends) if hyp_ends else None
            elif c.type == "insert" and hyp_ends and c.ref_start_idx > 0:
                # source words folded into the preceding token: it ends when they end
                prev = out[c.ref_start_idx - 1]
                out[c.ref_start_idx - 1] = max([e for e in [prev, *hyp_ends] if e is not None])
    last = None
    for r in range(len(out)):
        if out[r] is None:
            out[r] = last
        else:
            last = out[r]
    first = next((v for v in out if v is not None), None)
    return [v if v is not None else first for v in out]
