"""Model adapters.

One class per model family. Each turns a list of 16 kHz float32 arrays into a
list of transcripts, and reports exactly what it loaded (class, dtype, device,
decoding settings) so the run record can't drift from what actually ran.

Adding a model = one class here plus one line in `load`.

dtype policy when `--dtype auto`: follow each model card. Whisper fp16 (its
usual serving precision), Parakeet fp32 (a conformer transducer; keep the
numerics boring until fp16 is shown not to move accuracy), Qwen3-ASR bf16 (the
card's recommendation). Everything is fp32 on CPU.
"""

from __future__ import annotations

import re

import numpy as np
import torch

SR = 16_000

_DTYPES = {"fp16": torch.float16, "bf16": torch.bfloat16, "fp32": torch.float32}


def _device(device: str | None) -> str:
    return device or ("cuda:0" if torch.cuda.is_available() else "cpu")


def _dtype(requested: str, default: str, device: str) -> torch.dtype:
    if not device.startswith("cuda"):
        return torch.float32
    return _DTYPES[default if requested == "auto" else requested]


def _model_type(model: str) -> str:
    from transformers import AutoConfig

    return AutoConfig.from_pretrained(model).model_type


def _load_checked(cls, model: str, **kw):
    """from_pretrained, but refuse a checkpoint whose weights don't fully map.

    transformers only *warns* when weights are missing and initialises them at
    random. For a benchmark that is the worst possible failure: the run
    completes and produces confident nonsense. (The original Qwen/Qwen3-ASR-*
    checkpoints do exactly this against the native class - use the `-hf` ones.)
    """
    m, info = cls.from_pretrained(model, output_loading_info=True, **kw)
    missing = sorted(info.get("missing_keys") or [])
    if missing:
        raise SystemExit(
            f"{model}: {len(missing)} weights missing from checkpoint (e.g. {missing[0]}); "
            "refusing to run a partially random model"
        )
    return m


class WhisperHF:
    backend = "transformers.pipeline"
    # The chunked pipeline holds overlapping 30 s windows for every input in the
    # batch. On an 8 GB card, ~150 s of audio per call thrashes the allocator and
    # then dies with a raw CUDA OOM that no retry can recover from; ~80 s is safe.
    max_batch_seconds = 80.0
    # Whisper pads every input to a 30 s window, so its memory cost is per
    # *item*, not per audio second. A seconds budget alone lets a batch of short
    # clips balloon to 14+ windows; cap the count too.
    max_batch_items = 8

    def __init__(self, model: str, dtype: str = "auto", device: str | None = None):
        from transformers import pipeline

        self.device = _device(device)
        self.dtype = _dtype(dtype, "fp16", self.device)
        self.generate_kwargs = {"language": "en", "task": "transcribe"}
        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=model,
            torch_dtype=self.dtype,
            device=self.device,
            chunk_length_s=30,
        )

    @torch.inference_mode()
    def transcribe(self, audios: list[np.ndarray]) -> list[str]:
        outs = self.pipe(
            [{"raw": a, "sampling_rate": SR} for a in audios],
            batch_size=len(audios),
            generate_kwargs=self.generate_kwargs,
        )
        return [o["text"] for o in outs]

    def info(self) -> dict:
        return {"class": "WhisperForConditionalGeneration", "chunk_length_s": 30, "generate_kwargs": self.generate_kwargs}


class ParakeetHF:
    backend = "transformers"

    def __init__(self, model: str, dtype: str = "auto", device: str | None = None):
        from transformers import AutoModelForCTC, AutoModelForTDT, AutoProcessor

        self.device = _device(device)
        self.dtype = _dtype(dtype, "fp32", self.device)
        self.tdt = _model_type(model) == "parakeet_tdt"
        cls = AutoModelForTDT if self.tdt else AutoModelForCTC
        self.processor = AutoProcessor.from_pretrained(model)
        self.model = _load_checked(cls, model, dtype=self.dtype).to(self.device).eval()

    @torch.inference_mode()
    def transcribe(self, audios: list[np.ndarray]) -> list[str]:
        inputs = self.processor(list(audios), sampling_rate=SR, return_tensors="pt")
        inputs = {
            k: (v.to(self.device, self.dtype) if v.is_floating_point() else v.to(self.device))
            for k, v in inputs.items()
        }
        if self.tdt:
            seqs = self.model.generate(**inputs, return_dict_in_generate=True).sequences
        else:
            seqs = self.model(**inputs).logits.argmax(-1)
        return self.processor.batch_decode(seqs, skip_special_tokens=True)

    def info(self) -> dict:
        return {"class": type(self.model).__name__, "decoding": "greedy"}


class Qwen3ASRHF:
    backend = "transformers"

    # The model answers "language <X><asr_text>..." (or a "language: X\ntext:" variant);
    # we want only the words.
    _LANG_PREFIX = re.compile(r"^\s*language\s*:?\s*[A-Za-z-]+\s*(?:<asr_text>|\btext\s*:|\n)\s*", re.I)

    def __init__(self, model: str, dtype: str = "auto", device: str | None = None, max_new_tokens: int = 256):
        from transformers import AutoProcessor, Qwen3ASRForConditionalGeneration

        self.device = _device(device)
        self.dtype = _dtype(dtype, "bf16", self.device)
        self.max_new_tokens = max_new_tokens
        self.processor = AutoProcessor.from_pretrained(model)
        # The original Qwen/Qwen3-ASR-* checkpoints name WhisperFeatureExtractor in
        # preprocessor_config.json (for Qwen's own `qwen-asr` package). The native
        # transformers model needs Qwen3ASRFeatureExtractor, which pads the mel axis
        # to a multiple of 2*n_window; without it the encoder rejects most batches.
        from transformers.models.qwen3_asr.feature_extraction_qwen3_asr import Qwen3ASRFeatureExtractor

        if not isinstance(self.processor.feature_extractor, Qwen3ASRFeatureExtractor):
            self.processor.feature_extractor = Qwen3ASRFeatureExtractor.from_pretrained(model)
        self.processor.tokenizer.padding_side = "left"  # batched generation needs left padding
        self.model = _load_checked(Qwen3ASRForConditionalGeneration, model, dtype=self.dtype).to(self.device).eval()
        conv = [{"role": "user", "content": [{"type": "audio"}]}]
        self.prompt = self.processor.apply_chat_template(conv, add_generation_prompt=True, tokenize=False)

    @torch.inference_mode()
    def transcribe(self, audios: list[np.ndarray]) -> list[str]:
        inputs = self.processor(
            text=[self.prompt] * len(audios),
            audio=list(audios),
            sampling_rate=SR,
            padding=True,
            return_tensors="pt",
        ).to(self.device)
        if "input_features" in inputs:
            inputs["input_features"] = inputs["input_features"].to(self.dtype)
        out = self.model.generate(**inputs, max_new_tokens=self.max_new_tokens, do_sample=False)
        gen = out[:, inputs["input_ids"].shape[1] :]
        raw = self.processor.batch_decode(gen, skip_special_tokens=True)
        return [self._LANG_PREFIX.sub("", t, count=1).strip() for t in raw]

    def info(self) -> dict:
        return {
            "class": type(self.model).__name__,
            "decoding": "greedy",
            "max_new_tokens": self.max_new_tokens,
            "prompt": self.prompt,
            "language": "auto-detected; prefix stripped",
        }


def load(model: str, dtype: str = "auto", device: str | None = None):
    mt = _model_type(model)
    if mt == "whisper":
        return WhisperHF(model, dtype, device)
    if mt in ("parakeet_tdt", "parakeet_ctc"):
        return ParakeetHF(model, dtype, device)
    if mt == "qwen3_asr":
        return Qwen3ASRHF(model, dtype, device)
    raise SystemExit(f"no adapter for model_type {mt!r} ({model})")
