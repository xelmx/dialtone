import numpy as np

from dialtone import degrade

SR = degrade.SR_MODEL


def _band_energy(x, lo, hi):
    spec = np.abs(np.fft.rfft(x)) ** 2
    f = np.fft.rfftfreq(len(x), 1 / SR)
    return spec[(f >= lo) & (f < hi)].sum()


def test_profiles_preserve_length_and_rate():
    x = np.random.default_rng(0).standard_normal(SR * 2).astype(np.float32) * 0.1
    for p in degrade.PROFILES:
        y = degrade.apply(x, p)
        assert y.shape == x.shape, p
        assert y.dtype == np.float32


def test_g711u_removes_everything_above_4khz():
    x = np.random.default_rng(1).standard_normal(SR * 2).astype(np.float32) * 0.1
    y = degrade.apply(x, "g711u")
    ratio = _band_energy(y, 4500, 8000) / _band_energy(x, 4500, 8000)
    assert ratio < 1e-3, ratio  # >30 dB down


def test_pots_also_cuts_below_300_and_above_3400():
    x = np.random.default_rng(2).standard_normal(SR * 4).astype(np.float32) * 0.1
    y = degrade.apply(x, "pots")
    low = _band_energy(y, 0, 150) / _band_energy(x, 0, 150)
    high = _band_energy(y, 3800, 4000) / _band_energy(x, 3800, 4000)
    mid = _band_energy(y, 800, 2500) / _band_energy(x, 800, 2500)
    assert low < 0.05 and high < 0.2, (low, high)
    assert mid > 0.5, mid  # the speech band survives


def test_describe_lists_the_exact_chain():
    d = degrade.describe("pots")
    assert [s["name"] for s in d["steps"]] == ["narrowband", "bandpass", "mulaw", "wideband"]
