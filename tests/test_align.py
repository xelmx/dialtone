import pytest

from dialtone import align


def test_proportional_covers_the_whole_duration_and_is_monotone():
    w = align.proportional("HE HOPED THERE", 3.0)
    assert [x.text for x in w] == ["HE", "HOPED", "THERE"]
    assert w[0].start == 0.0 and w[-1].end == pytest.approx(3.0)
    assert all(a.end <= b.start + 1e-9 for a, b in zip(w, w[1:]))


def test_check_flags_bad_alignments():
    good = [align.Word("A", 0.0, 0.5), align.Word("B", 0.5, 1.0)]
    assert align.check(good, 2, 1.2)
    assert not align.check(good, 3, 1.2)  # wrong count
    assert not align.check([align.Word("A", 0.6, 0.5)], 1, 1.0)  # end before start
    assert not align.check([align.Word("A", 0.5, 1.0), align.Word("B", 0.2, 0.6)], 2, 1.2)  # B starts before A
    assert not align.check(good, 2, 0.3)  # past the end of the clip


def _words(ends):
    return [align.Word(f"w{i}", (ends[i - 1] if i else 0.0), e) for i, e in enumerate(ends)]


def test_word_end_times_is_identity_when_the_normaliser_keeps_tokens():
    assert align.word_end_times("HE HOPED THERE", _words([0.4, 0.9, 1.4]), str.lower) == [0.4, 0.9, 1.4]


def test_word_end_times_survive_a_splitting_normaliser():
    norm = lambda s: s.lower().replace("million'd", "1000000 would")  # noqa: E731
    ends = align.word_end_times("A MILLION'D B", _words([1.0, 2.0, 3.0]), norm)
    assert ends == [1.0, 2.0, 2.0, 3.0]  # both new tokens inherit the source word's end


def test_word_end_times_survive_a_merging_normaliser():
    norm = lambda s: s.lower().replace("twenty five", "25")  # noqa: E731
    ends = align.word_end_times("TWENTY FIVE CATS", _words([1.0, 2.0, 3.0]), norm)
    assert ends == [2.0, 3.0]  # "25" ends when FIVE ends; still monotone


def test_word_end_times_returns_one_value_per_normalised_token_even_if_the_aligner_split_differently():
    ends = align.word_end_times("HE HOPED THERE WOULD", _words([0.5, 1.5]), str.lower)  # aligner gave 2 words for 4
    assert len(ends) == 4 and ends == sorted(ends)
    assert align.word_end_times("", _words([0.5]), str.lower) == []
