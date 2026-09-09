import numpy as np
import pytest

from dialtone import settle, stream

# partial sequences are (t, text); the last entry is the final transcript


def test_prefix_grid_is_step_half_from_one_and_ends_on_the_full_duration():
    assert stream.prefix_grid(3.2) == [1.0, 1.5, 2.0, 2.5, 3.0, 3.2]
    assert stream.prefix_grid(0.7) == [0.7]
    assert stream.prefix_grid(1.02) == [1.02]
    assert stream.prefix_grid(1.6) == [1.0, 1.6]  # 1.5 is within eps of the end
    assert stream.prefix_grid(2.0) == [1.0, 1.5, 2.0]


def test_stable_time_is_the_first_prefix_after_which_a_word_never_changes():
    p = [(1.0, "he"), (1.5, "he hoped"), (2.0, "he hoped their"), (2.5, "he hoped there would")]
    assert settle.stable_times(p, p[-1][1]) == [1.0, 1.5, 2.5, 2.5]


def test_a_leading_insertion_does_not_reset_every_later_word():
    p = [(1.5, "he hoped there"), (2.0, "and he hoped there"), (2.5, "and he hoped there")]
    # positional comparison would give 2.0 for all four; alignment keeps the survivors at 1.5
    assert settle.stable_times(p, p[-1][1]) == [2.0, 1.5, 1.5, 1.5]


def test_stable_time_survives_a_hallucinated_partial():
    final = "he hoped there would be stew"
    junk = final + " thank you" * 200
    p = [(1.0, "he hoped"), (1.5, junk), (2.0, "he hoped there would"), (2.5, final)]
    # the junk partial still *contains* the real words, so "there would" legitimately count
    # as emitted at 1.5; what must not happen is the 200 extra words resetting "he hoped"
    assert settle.stable_times(p, final) == [1.0, 1.0, 1.5, 1.5, 2.5, 2.5]
    without_junk = [(1.0, "he hoped"), (2.0, "he hoped there would"), (2.5, final)]
    assert settle.stable_times(without_junk, final)[:2] == settle.stable_times(p, final)[:2]


def test_emission_lag_uses_the_reference_word_the_final_word_aligned_to():
    final = ref = "he hoped there would"
    lags = settle.emission_lags(final, ref, [0.4, 0.9, 1.4, 2.1], [1.0, 1.5, 2.5, 2.5])
    assert lags == pytest.approx([0.6, 0.6, 1.1, 0.4])
    assert float(np.median(lags)) == pytest.approx(0.6)


def test_emission_lag_is_none_for_final_words_with_no_reference_hit():
    lags = settle.emission_lags("he hoped their", "he hoped there", [0.4, 0.9, 1.4], [1.0, 1.5, 2.0])
    assert lags == [pytest.approx(0.6), pytest.approx(0.6), None]


def test_revisions_ignore_pure_trailing_appends():
    assert settle.revisions([(1.0, "he"), (1.5, "he hoped"), (2.0, "he hoped there")]) == 0


def test_revisions_count_a_rewritten_word():
    assert settle.revisions([(1.0, "he hoped their"), (1.5, "he hoped there would")]) == 1


def test_revisions_count_a_dropped_word_and_an_interior_insertion():
    assert settle.revisions([(1.0, "he hoped there"), (1.5, "he there")]) == 1
    assert settle.revisions([(1.0, "he there"), (1.5, "he hoped there")]) == 1


def test_unstable_tail_counts_only_trailing_non_surviving_words():
    final = "he hoped there would be stew"
    assert settle.unstable_tail([(1.0, "he hoped their soup"), (2.0, final)], final) == [2]
    assert settle.unstable_tail([(1.0, "he hopped there would be stew"), (2.0, final)], final) == [0]
    assert settle.unstable_tail([(1.0, ""), (2.0, final)], final) == [0]


def test_unstable_tail_counts_a_hallucinated_overlong_partial():
    final = "he hoped"
    assert settle.unstable_tail([(1.0, "he hoped thank you thank you"), (2.0, final)], final) == [4]


def test_agreement_point_is_the_last_change():
    final = "he hoped there"
    p = [(1.0, "he"), (1.5, "he hoped"), (2.0, "he hoped their"), (2.5, final), (3.0, final)]
    assert settle.agreement_point(p, final) == 2.5


def test_agreement_point_when_a_late_partial_regresses():
    final = "he hoped there"
    p = [(1.5, final), (2.0, "he hoped"), (2.5, final), (3.0, final)]
    assert settle.agreement_point(p, final) == 2.5


def test_empty_partials_are_handled():
    p = [(1.0, ""), (1.5, ""), (2.0, "")]
    assert settle.stable_times(p, "") == []
    assert settle.revisions(p) == 0
    assert settle.unstable_tail(p, "") == [0, 0]
    assert settle.agreement_point(p, "") == 1.0
    assert settle.emission_lags("", "he", [0.5], []) == []


def test_single_prefix_utterance_yields_zero_revisions_and_zero_tail():
    rows = [{"id": "u", "t": 0.7, "final": True, "ref": "HI", "hyp": "hi", "audio_s": 0.7, "compute_s": 0.01}]
    m = settle.per_utterance(rows, [0.6], str.lower)
    assert m["edits"] == 0 and m["tail_n"] == 0 and m["n_prefixes"] == 1
    assert m["lags"] == [pytest.approx(0.1)]
    assert m["agree_before_end"] == 0.0


def _rows(uid, partials, ref, compute=0.01):
    return [
        {"id": uid, "t": t, "final": i == len(partials) - 1, "ref": ref, "hyp": h, "audio_s": t, "compute_s": compute}
        for i, (t, h) in enumerate(partials)
    ]


def test_per_utterance_pools_everything_needed_for_aggregation():
    p = [(1.0, "he"), (1.5, "he hoped"), (2.0, "he hoped their"), (2.5, "he hoped there would")]
    m = settle.per_utterance(_rows("u", p, "HE HOPED THERE WOULD"), [0.4, 0.9, 1.4, 2.1], str.lower)
    assert m["n_final_words"] == 4 and m["edits"] == 1 and m["tail_sum"] == 1 and m["tail_n"] == 3
    assert m["agree_before_end"] == 0.0 and m["audio_s"] == pytest.approx(7.0) and m["compute_s"] == pytest.approx(0.04)


def test_revision_rate_is_pooled_per_hundred_final_words():
    a = settle.per_utterance(_rows("a", [(1.0, "x y"), (1.5, "x z")], "X Z"), [0.5, 1.0], str.lower)  # 1 edit, 2 words
    b = settle.per_utterance(_rows("b", [(1.0, "p"), (1.5, "p q")], "P Q"), [0.5, 1.0], str.lower)  # 0 edits, 2 words
    agg = settle.aggregate([a, b], n_boot=10)
    assert agg["revisions_per_100"] == pytest.approx(25.0)
    assert agg["audio_expansion"] == pytest.approx(5.0 / 3.0)


def test_exploded_partials_are_counted_and_the_median_revision_rate_ignores_them():
    loop = "a little bit of " * 40  # a decoding loop: 160 words on a 3-word utterance
    boom = settle.per_utterance(_rows("boom", [(1.0, loop), (1.5, "he hoped there")], "HE HOPED THERE"), [0.4, 0.9, 1.4], str.lower)
    calm = [settle.per_utterance(_rows(f"c{i}", [(1.0, "he"), (1.5, "he hoped there")], "HE HOPED THERE"), [0.4, 0.9, 1.4], str.lower) for i in range(4)]
    assert boom["exploded_partials"] == 1 and calm[0]["exploded_partials"] == 0
    assert boom["max_partial_words"] == 160
    agg = settle.aggregate([boom, *calm], n_boot=10)
    assert agg["exploded_partials"] == 1
    assert agg["revisions_per_100"] > 1000  # pooled is dominated by the loop...
    assert agg["revisions_per_100_median"] == 0.0  # ...the typical utterance is not


def test_bootstrap_is_degenerate_when_every_utterance_is_identical():
    p = [(1.0, "he"), (1.5, "he hoped"), (2.0, "he hoped there")]
    per = [settle.per_utterance(_rows(f"u{i}", p, "HE HOPED THERE"), [0.4, 0.9, 1.4], str.lower) for i in range(20)]
    agg = settle.aggregate(per, n_boot=50)
    lo, hi = agg["lag_median_ms_ci95"]
    assert lo == hi == agg["lag_median_ms"] == pytest.approx(600.0)


def test_paired_delta_excludes_zero_when_every_utterance_got_slower():
    fast = [(1.0, "he"), (1.5, "he hoped"), (2.0, "he hoped there")]
    slow = [(1.0, ""), (1.5, "he"), (2.0, "he hoped there")]
    base = [settle.per_utterance(_rows(f"u{i}", fast, "HE HOPED THERE"), [0.4, 0.9, 1.4], str.lower) for i in range(30)]
    other = [settle.per_utterance(_rows(f"u{i}", slow, "HE HOPED THERE"), [0.4, 0.9, 1.4], str.lower) for i in range(30)]
    d = settle.paired_delta(base, other, n_boot=50)
    assert d["lag_median_ms"] > 0 and d["lag_median_ms_ci95"][0] > 0


def test_group_rows_rejects_an_incomplete_grid():
    good = _rows("g", [(1.0, "a"), (1.5, "a b"), (1.8, "a b c")], "A B C")
    bad = _rows("b", [(1.0, "a"), (1.8, "a b c")], "A B C")  # missing t=1.5
    unfinished = _rows("u", [(1.0, "a"), (1.5, "a b")], "A B C")
    for r in unfinished:
        r["final"] = False
    ok, dropped = settle.group_rows(good + bad + unfinished, 1.0, 0.5, 0.1)
    assert list(ok) == ["g"] and sorted(dropped) == ["b", "u"]
