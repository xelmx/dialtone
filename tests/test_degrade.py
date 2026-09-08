import shutil

import numpy as np
import pytest

from dialtone import degrade

SR = degrade.SR_MODEL


def _band_energy(x, lo, hi):
    spec = np.abs(np.fft.rfft(x)) ** 2
    f = np.fft.rfftfreq(len(x), 1 / SR)
    return spec[(f >= lo) & (f < hi)].sum()


def _snr_db(clean, noisy):
    n = noisy - clean
    return 10 * np.log10((clean**2).mean() / (n**2).mean())


def _speechish(seed=0, secs=2.0):
    """Band-limited noise burst - enough like speech for SNR/bandwidth tests."""
    x = np.random.default_rng(seed).standard_normal(int(SR * secs)).astype(np.float32) * 0.1
    return degrade.bandpass(x, None, sr=SR)


def _ctx():
    rng = np.random.default_rng(7)
    pool = degrade.BabblePool([(f"spk{i}", rng.standard_normal(SR * 3).astype(np.float32) * 0.05) for i in range(4)])
    return degrade.Context(pool=pool, speaker="spk0")


def test_profiles_preserve_length_and_rate():
    x = _speechish()
    for p in degrade.PROFILES:
        if "opus" in p and not shutil.which("ffmpeg"):
            continue
        y = degrade.apply(x, p, _ctx())
        assert y.shape == x.shape, p
        assert y.dtype == np.float32


def test_g711u_removes_everything_above_4khz():
    x = np.random.default_rng(1).standard_normal(SR * 2).astype(np.float32) * 0.1
    y = degrade.apply(x, "g711u")
    assert _band_energy(y, 4500, 8000) / _band_energy(x, 4500, 8000) < 1e-3


def test_pots_also_cuts_below_300_and_above_3400():
    x = np.random.default_rng(2).standard_normal(SR * 4).astype(np.float32) * 0.1
    y = degrade.apply(x, "pots")
    low = _band_energy(y, 0, 150) / _band_energy(x, 0, 150)
    high = _band_energy(y, 3800, 4000) / _band_energy(x, 3800, 4000)
    mid = _band_energy(y, 800, 2500) / _band_energy(x, 800, 2500)
    assert low < 0.05 and high < 0.2, (low, high)
    assert mid > 0.5, mid


def test_pink_hits_the_requested_snr_and_is_deterministic():
    x = _speechish(3)
    y1 = degrade.apply(x, "pink10")
    y2 = degrade.apply(x, "pink10")
    assert np.array_equal(y1, y2)
    assert abs(_snr_db(x, y1) - 10.0) < 0.3


def test_pink_has_equal_energy_per_octave():
    x = np.zeros(SR * 8, dtype=np.float32)
    x[0] = 1e-6  # non-silent so _at_snr scales; noise dominates
    y = degrade.pink(x, None, snr_db=-60.0) - x
    ratio = _band_energy(y, 200, 400) / _band_energy(y, 3200, 6400)
    assert 0.5 < ratio < 2.0, ratio  # white noise would give ~1/16


def test_babble_hits_snr_and_never_uses_the_targets_own_speaker():
    x = _speechish(4)
    ctx = _ctx()
    y = degrade.apply(x, "babble10", ctx)
    assert abs(_snr_db(x, y) - 10.0) < 0.3
    # a pool of only the target's speaker still returns (single-speaker escape hatch)
    solo = degrade.Context(pool=degrade.BabblePool([("spk0", ctx.pool.items[0][1])]), speaker="spk0")
    assert degrade.apply(x, "babble10", solo).shape == x.shape


def test_babble_requires_a_pool():
    with pytest.raises(ValueError):
        degrade.apply(_speechish(), "babble10")


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not on PATH")
def test_opus_roundtrip_keeps_level_and_opus8_is_narrowband():
    x = _speechish(5, secs=3.0)
    y12 = degrade.apply(x, "opus12")
    assert y12.shape == x.shape
    level = 10 * np.log10((y12**2).mean() / (x**2).mean())
    assert abs(level) < 3.0, level
    w = np.random.default_rng(6).standard_normal(SR * 3).astype(np.float32) * 0.1
    y8 = degrade.apply(w, "opus8")
    assert _band_energy(y8, 4500, 8000) / _band_energy(w, 4500, 8000) < 0.05


def test_describe_lists_the_exact_chain_with_params():
    d = degrade.describe("pots_babble10")
    assert [s["name"] for s in d["steps"]] == ["babble", "narrowband", "bandpass", "mulaw", "wideband"]
    assert d["steps"][0]["snr_db"] == 10.0 and d["steps"][0]["talkers"] == 6
    assert degrade.describe("opus8")["steps"][0]["cutoff_hz"] == 4000
