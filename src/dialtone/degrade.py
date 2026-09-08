"""Turn a clean 16 kHz recording into what a phone line (and a room) would deliver.

Every profile is a named, ordered list of `(step, params)`. The list is written
into the run record so a result can never be separated from the exact chain
that produced it. Noise is added first (at the microphone), then the line.

Line steps
----------
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
opus        Opus encode -> decode through ffmpeg/libopus in `voip` mode, the
            codec every WebRTC and most VoIP stacks use. `kbps` sets the
            bitrate; `cutoff_hz=4000` forces narrowband. Output is aligned
            back to the input length.

Noise steps (SNR in dB over the whole clip, RMS-based)
------------
pink        1/f noise, the stationary control case. Seeded from the audio
            bytes, so the same clip always gets the same noise.
babble      `talkers` other utterances from the corpus, never the target's own
            speaker, summed and scaled. Speech-shaped, the thing that actually
            confuses recognisers. Needs a `Context` with a `BabblePool`.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import zlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.signal import butter, resample_poly, sosfilt

from . import g711

SR_MODEL = 16_000
SR_PHONE = 8_000

_LINE_POTS = [("narrowband", {}), ("bandpass", {}), ("mulaw", {}), ("wideband", {})]

PROFILES: dict[str, list[tuple[str, dict]]] = {
    "clean": [],
    "g711u": [("narrowband", {}), ("mulaw", {}), ("wideband", {})],
    "pots": list(_LINE_POTS),
    "pink10": [("pink", {"snr_db": 10.0})],
    "babble10": [("babble", {"snr_db": 10.0, "talkers": 6})],
    "pots_babble10": [("babble", {"snr_db": 10.0, "talkers": 6}), *_LINE_POTS],
    "opus12": [("opus", {"kbps": 12, "cutoff_hz": None})],
    "opus8": [("opus", {"kbps": 8, "cutoff_hz": 4000})],
}

NOTES = {
    "narrowband": {"from_hz": SR_MODEL, "to_hz": SR_PHONE, "method": "scipy.signal.resample_poly (Kaiser FIR anti-alias)"},
    "bandpass": {"lo_hz": 300.0, "hi_hz": 3400.0, "order": 4, "type": "butterworth, causal sosfilt"},
    "mulaw": {"codec": "ITU-T G.711 mu-law, Sun g711.c algorithm"},
    "wideband": {"from_hz": SR_PHONE, "to_hz": SR_MODEL, "method": "scipy.signal.resample_poly"},
    "opus": {"codec": "libopus via ffmpeg, application=voip, vbr=on, decoded at 16 kHz"},
    "pink": {"spectrum": "1/f (equal energy per octave)", "seed": "crc32 of the audio bytes"},
    "babble": {"source": "other-speaker utterances from the same corpus", "seed": "crc32 of the audio bytes"},
}


class BabblePool:
    """Other people's speech to mix in. Items are (speaker, path) or (speaker, array)."""

    def __init__(self, items: list[tuple[str, str | np.ndarray]]):
        if not items:
            raise ValueError("empty babble pool")
        self.items = items

    @classmethod
    def from_index(cls, utts: dict[str, dict]) -> BabblePool:
        return cls([(u["speaker"], u["path"]) for u in utts.values()])

    def _load(self, src) -> np.ndarray:
        if isinstance(src, np.ndarray):
            return src
        from . import data

        return data.load_audio(src)

    def mix(self, rng: np.random.Generator, talkers: int, exclude_speaker: str | None, length: int) -> np.ndarray:
        out = np.zeros(length, dtype=np.float32)
        got = 0
        while got < talkers:
            spk, src = self.items[int(rng.integers(len(self.items)))]
            if spk == exclude_speaker and len({s for s, _ in self.items}) > 1:
                continue
            y = self._load(src)
            if len(y) < length:
                y = np.tile(y, length // len(y) + 1)
            start = int(rng.integers(0, len(y) - length + 1))
            out += y[start : start + length]
            got += 1
        return out


@dataclass
class Context:
    """What some steps need beyond the audio: a babble pool, and the target's speaker."""

    pool: BabblePool | None = None
    speaker: str | None = None


def _seed(x: np.ndarray, salt: str) -> int:
    return zlib.crc32(x.tobytes()) ^ zlib.crc32(salt.encode())


def _at_snr(x: np.ndarray, noise: np.ndarray, snr_db: float) -> np.ndarray:
    ps = float(np.mean(x.astype(np.float64) ** 2))
    pn = float(np.mean(noise.astype(np.float64) ** 2))
    if ps == 0.0 or pn == 0.0:
        return x
    scale = np.sqrt(ps / (pn * 10 ** (snr_db / 10)))
    return (x + noise * scale).astype(np.float32)


# --- line -------------------------------------------------------------------


def narrowband(x: np.ndarray, ctx: Context) -> np.ndarray:
    return resample_poly(x, 1, 2).astype(np.float32)


def wideband(x: np.ndarray, ctx: Context) -> np.ndarray:
    return resample_poly(x, 2, 1).astype(np.float32)


def bandpass(x: np.ndarray, ctx: Context, sr: int = SR_PHONE) -> np.ndarray:
    p = NOTES["bandpass"]
    sos = butter(p["order"], [p["lo_hz"], p["hi_hz"]], btype="bandpass", fs=sr, output="sos")
    return sosfilt(sos, x).astype(np.float32)


def mulaw(x: np.ndarray, ctx: Context) -> np.ndarray:
    return g711.roundtrip(x)


def ffmpeg_path() -> str:
    ff = shutil.which("ffmpeg")
    if not ff:
        raise SystemExit("opus steps need ffmpeg with libopus on PATH (e.g. `winget install Gyan.FFmpeg`)")
    return ff


def opus(x: np.ndarray, ctx: Context, kbps: int, cutoff_hz: int | None = None, application: str = "voip") -> np.ndarray:
    ff = ffmpeg_path()
    pcm = np.clip(np.round(x * 32767.0), -32768, 32767).astype(np.int16).tobytes()
    with tempfile.TemporaryDirectory() as d:
        enc = Path(d) / "a.opus"
        cmd = [ff, "-hide_banner", "-loglevel", "error", "-f", "s16le", "-ar", str(SR_MODEL), "-ac", "1", "-i", "pipe:0",
               "-c:a", "libopus", "-b:a", f"{kbps}k", "-application", application, "-vbr", "on"]
        if cutoff_hz:
            cmd += ["-cutoff", str(cutoff_hz)]
        subprocess.run(cmd + ["-y", str(enc)], input=pcm, check=True, capture_output=True)
        dec = subprocess.run(
            [ff, "-hide_banner", "-loglevel", "error", "-i", str(enc), "-ar", str(SR_MODEL), "-ac", "1", "-f", "s16le", "pipe:1"],
            check=True, capture_output=True,
        ).stdout
    y = np.frombuffer(dec, dtype=np.int16).astype(np.float32) / 32768.0
    if len(y) < len(x):
        y = np.pad(y, (0, len(x) - len(y)))
    return y[: len(x)]


# --- noise ------------------------------------------------------------------


def pink(x: np.ndarray, ctx: Context, snr_db: float) -> np.ndarray:
    rng = np.random.default_rng(_seed(x, "pink"))
    white = rng.standard_normal(len(x))
    spec = np.fft.rfft(white)
    f = np.fft.rfftfreq(len(x), 1 / SR_MODEL)
    spec[1:] /= np.sqrt(f[1:])  # power ~ 1/f
    spec[0] = 0.0
    noise = np.fft.irfft(spec, n=len(x)).astype(np.float32)
    return _at_snr(x, noise, snr_db)


def babble(x: np.ndarray, ctx: Context, snr_db: float, talkers: int) -> np.ndarray:
    if ctx is None or ctx.pool is None:
        raise ValueError("babble needs a Context with a BabblePool")
    rng = np.random.default_rng(_seed(x, "babble"))
    noise = ctx.pool.mix(rng, talkers, ctx.speaker, len(x))
    return _at_snr(x, noise, snr_db)


_STEPS = {
    "narrowband": narrowband,
    "bandpass": bandpass,
    "mulaw": mulaw,
    "wideband": wideband,
    "opus": opus,
    "pink": pink,
    "babble": babble,
}


def apply(x: np.ndarray, profile: str, ctx: Context | None = None) -> np.ndarray:
    """Run a 16 kHz float32 signal through a named profile; returns 16 kHz float32."""
    if profile not in PROFILES:
        raise KeyError(f"unknown profile {profile!r}; choose from {sorted(PROFILES)}")
    for step, params in PROFILES[profile]:
        x = _STEPS[step](x, ctx, **params)
    return x


def needs_pool(profiles: list[str]) -> bool:
    return any(step == "babble" for p in profiles for step, _ in PROFILES[p])


def describe(profile: str) -> dict:
    """The exact chain, for the run record."""
    return {"profile": profile, "steps": [{"name": s, **params, **NOTES.get(s, {})} for s, params in PROFILES[profile]]}
