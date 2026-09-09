import json

import numpy as np

from dialtone import degrade, run, stream

SR = degrade.SR_MODEL


def test_done_key_generalisation_keeps_the_old_behaviour(tmp_path):
    p = tmp_path / "x.jsonl"
    p.write_text(json.dumps({"id": "a", "t": 1.0}) + "\n" + json.dumps({"id": "a", "t": 1.5}) + "\n", encoding="utf-8")
    assert run._done(p) == {"a"}
    assert run._done(p, key=lambda r: (r["id"], r["t"])) == {("a", 1.0), ("a", 1.5)}
    assert run._done(tmp_path / "missing.jsonl") == set()


def test_prefix_batches_respect_both_caps_and_go_longest_first():
    ts = stream.prefix_grid(30.0)  # 1.0 .. 29.5, 30.0 -> 60 prefixes, ~930 s of audio
    batches = list(stream.prefix_batches(ts, max_items=8, max_seconds=80.0))
    assert sorted(t for b in batches for t in b) == sorted(ts)
    assert all(len(b) <= 8 and sum(b) <= 80.0 + 1e-9 for b in batches)
    assert batches[0][0] == 30.0  # the biggest prefix is attempted first


def test_prefix_slices_come_from_one_degraded_signal():
    x = (0.1 * np.random.default_rng(0).standard_normal(SR * 3)).astype(np.float32)
    y = degrade.apply(x, "pink10")
    one_second_from_full = y[:SR]
    one_second_alone = degrade.apply(x[:SR], "pink10")
    assert np.array_equal(one_second_from_full, y[:SR])
    assert not np.array_equal(one_second_from_full, one_second_alone)  # different seed and SNR base
