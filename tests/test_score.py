from dialtone import score


def _rows(errs, n=10):
    return [{"S": e, "D": 0, "I": 0, "N": n} for e in errs]


def test_pooled_wer_is_errors_over_reference_words():
    p = score.pooled(_rows([1, 0, 2], n=10))
    assert p["wer"] == 3 / 30


def test_paired_gap_ci_is_zero_when_conditions_are_identical():
    base = _rows([1, 0, 2, 0, 1] * 20)
    lo, hi = score.bootstrap_gap_ci(base, base)
    assert lo == 0.0 and hi == 0.0


def test_paired_gap_ci_excludes_zero_when_every_utterance_got_worse():
    base = _rows([1, 0, 2, 0, 1] * 20)
    worse = _rows([2, 1, 3, 1, 2] * 20)  # +1 error on every utterance
    lo, hi = score.bootstrap_gap_ci(base, worse)
    assert lo > 0 and hi > 0
    assert abs((lo + hi) / 2 - 0.1) < 0.01  # +1 error per 10 words = +10 pp


def test_paired_gap_ci_straddles_zero_when_changes_cancel():
    base = _rows([1, 1] * 50)
    mixed = _rows([2, 0] * 50)  # half worse, half better, same total
    lo, hi = score.bootstrap_gap_ci(base, mixed)
    assert lo < 0 < hi
