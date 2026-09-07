"""ITU-T G.711 mu-law, implemented the way the spec says.

Reference algorithm: Sun Microsystems' public-domain g711.c, which is what
every telephony stack ultimately traces back to. Vectorised with numpy and
written out step by step (no library call hiding a lookup table) so the whole
codec is reviewable in one screen.

Both directions work in the 16-bit PCM domain: `encode` takes int16 samples,
`decode` returns int16 samples.
"""

from __future__ import annotations

import numpy as np

BIAS = 0x84  # 132: added before segment search so small signals get fine steps
CLIP = 8159  # magnitude ceiling in the >>2 (14-bit) domain; 32635 in 16-bit terms
_SEG_END = np.array(
    [0x3F, 0x7F, 0xFF, 0x1FF, 0x3FF, 0x7FF, 0xFFF, 0x1FFF], dtype=np.int32
)


def encode(pcm16: np.ndarray) -> np.ndarray:
    """int16 PCM -> uint8 mu-law bytes (one byte per sample)."""
    x = pcm16.astype(np.int32) >> 2  # 16-bit -> 14-bit, arithmetic shift keeps sign
    neg = x < 0
    mag = np.where(neg, -x, x)
    mag = np.minimum(mag, CLIP) + (BIAS >> 2)
    seg = np.searchsorted(_SEG_END, mag)  # first segment whose end >= magnitude
    mantissa = (mag >> (seg + 1)) & 0x0F
    uval = (seg << 4) | mantissa
    uval = np.where(seg >= 8, 0x7F, uval)  # out of range -> max code
    mask = np.where(neg, 0x7F, 0xFF)  # sign bit lives in the inverted top bit
    return (uval ^ mask).astype(np.uint8)


def decode(ulaw: np.ndarray) -> np.ndarray:
    """uint8 mu-law bytes -> int16 PCM."""
    u = (~ulaw.astype(np.int32)) & 0xFF
    t = ((u & 0x0F) << 3) + BIAS
    t = t << ((u & 0x70) >> 4)
    out = np.where(u & 0x80, BIAS - t, t - BIAS)
    return out.astype(np.int16)


def roundtrip(x: np.ndarray) -> np.ndarray:
    """float32 in [-1, 1] -> through the codec -> float32. What the far end hears."""
    pcm = np.clip(np.round(x * 32767.0), -32768, 32767).astype(np.int16)
    return decode(encode(pcm)).astype(np.float32) / 32768.0
