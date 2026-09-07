"""Turn a clean 16 kHz recording into what a phone line would deliver.

Every profile is a named, ordered list of steps. The list is written into the
run record so a result can never be separated from the exact chain that
produced it.

Steps
-----
narrowband  16 kHz -> 8 kHz. `resample_poly` applies a Kaiser-windowed FIR
            low-pass *before* decimating, so nothing above 4 kHz folds back
            into the band. Downsampling without this filter is the classic
            mistake and it corrupts every result downstream.
bandpass    300-3400 Hz, 4th-order Butterworth, applied causally (`sosfilt`,
            not `sosfiltfilt`) because real line equipment is causal. This is
            the traditional analogue telephone channel.
mulaw       G.711 mu-law encode -> decode. 8-bit companded PCM, the codec
            carriers and Twilio hand you.
wideband    8 kHz -> 16 kHz, because the STT model expects 16 kHz input. Done
            here explicitly so the model's own loader can't silently pick a
            different resampler.
"""

from __future__ import annotations

import numpy as np
from scipy.signal import butter, resample_poly, sosfilt

from . import g711

SR_MODEL = 16_000
SR_PHONE = 8_000

PROFILES: dict[str, list[str]] = {
    "clean": [],
    "g711u": ["narrowband", "mulaw", "wideband"],
    "pots": ["narrowband", "bandpass", "mulaw", "wideband"],
}

PARAMS = {
    "narrowband": {
        "from_hz": SR_MODEL,
        "to_hz": SR_PHONE,
        "method": "scipy.signal.resample_poly (Kaiser FIR anti-alias)",
    },
    "bandpass": {"lo_hz": 300.0, "hi_hz": 3400.0, "order": 4, "type": "butterworth, causal sosfilt"},
    "mulaw": {"codec": "ITU-T G.711 mu-law, Sun g711.c algorithm"},
    "wideband": {"from_hz": SR_PHONE, "to_hz": SR_MODEL, "method": "scipy.signal.resample_poly"},
}


def narrowband(x: np.ndarray) -> np.ndarray:
    return resample_poly(x, 1, 2).astype(np.float32)


def wideband(x: np.ndarray) -> np.ndarray:
    return resample_poly(x, 2, 1).astype(np.float32)


def bandpass(x: np.ndarray, sr: int = SR_PHONE) -> np.ndarray:
    p = PARAMS["bandpass"]
    sos = butter(p["order"], [p["lo_hz"], p["hi_hz"]], btype="bandpass", fs=sr, output="sos")
    return sosfilt(sos, x).astype(np.float32)


def mulaw(x: np.ndarray) -> np.ndarray:
    return g711.roundtrip(x)


_STEPS = {
    "narrowband": narrowband,
    "bandpass": bandpass,
    "mulaw": mulaw,
    "wideband": wideband,
}


def apply(x: np.ndarray, profile: str) -> np.ndarray:
    """Run a 16 kHz float32 signal through a named profile; returns 16 kHz float32."""
    if profile not in PROFILES:
        raise KeyError(f"unknown profile {profile!r}; choose from {sorted(PROFILES)}")
    for step in PROFILES[profile]:
        x = _STEPS[step](x)
    return x


def describe(profile: str) -> dict:
    """The exact chain, for the run record."""
    return {"profile": profile, "steps": [{"name": s, **PARAMS[s]} for s in PROFILES[profile]]}
