import numpy as np

from dialtone import g711


def test_silence_is_0xff_and_back():
    assert g711.encode(np.array([0], dtype=np.int16))[0] == 0xFF
    assert g711.decode(np.array([0xFF], dtype=np.uint8))[0] == 0


def test_extremes_match_the_g711_table():
    assert g711.decode(np.array([0x00], dtype=np.uint8))[0] == -32124
    assert g711.decode(np.array([0x80], dtype=np.uint8))[0] == 32124


def test_roundtrip_is_monotonic_over_the_full_int16_range():
    x = np.arange(-32768, 32768, dtype=np.int16)
    y = g711.decode(g711.encode(x)).astype(np.int32)
    assert np.all(np.diff(y) >= 0)


def test_every_code_decodes_to_a_distinct_level():
    codes = np.arange(256, dtype=np.uint8)
    levels = g711.decode(codes)
    assert len(set(levels.tolist())) == 255  # 0x7F and 0xFF both mean zero


def test_sine_roundtrip_snr_is_in_the_mu_law_range():
    t = np.arange(8000) / 8000
    x = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    y = g711.roundtrip(x)
    snr = 10 * np.log10((x**2).sum() / ((x - y) ** 2).sum())
    assert 30 < snr < 45, snr
