"""Text normalisation before comparing reference to hypothesis.

This is a judgment call that moves the numbers, so it is a named choice:

basic       lowercase, drop punctuation except apostrophes, collapse spaces.
            Transparent, but "25" vs "twenty five" counts as two errors.
whisper_en  OpenAI's English normaliser (spelled-out numbers, British/American
            spelling, contractions, filler words). Applied to *every* model's
            output, this is what the Open ASR Leaderboard uses, so results are
            comparable to published numbers. Slightly favours Whisper because
            it was written alongside it, and it mangles archaic text
            ("million'd" -> "1000000 would").

The spelling map it needs is vendored in `assets/` (MIT, from openai/whisper)
so scoring does not depend on having any model on disk.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path

_NOT_WORD = re.compile(r"[^\w\s']", re.UNICODE)
_SPELLING = Path(__file__).parent / "assets" / "whisper_english_normalizer.json"


def basic(text: str) -> str:
    text = _NOT_WORD.sub(" ", text.lower())
    return " ".join(text.split())


def whisper_en() -> Callable[[str], str]:
    from transformers.models.whisper.english_normalizer import EnglishTextNormalizer

    return EnglishTextNormalizer(json.loads(_SPELLING.read_text(encoding="utf-8")))


def get(name: str) -> Callable[[str], str]:
    if name == "basic":
        return basic
    if name == "whisper_en":
        return whisper_en()
    raise KeyError(f"unknown normaliser {name!r}")
