from orphan_radar.rank.information_gain import (
    candidate_information_gain,
    entropy_from_scores,
    softmax_probabilities,
)


def test_candidate_information_gain_reduces_ambiguous_community_entropy():
    community_scores = {1: 0.40, 2: 0.39, 3: 0.38}

    result = candidate_information_gain(
        community_scores=community_scores,
        target_community_id=1,
        candidate_signal=1.0,
        temperature=0.25,
        boost=0.35,
    )

    assert result.entropy_before > result.entropy_after
    assert 0.0 < result.information_gain <= 1.0
    assert result.candidate_boost == 0.35


def test_candidate_information_gain_is_zero_for_missing_or_single_community():
    missing = candidate_information_gain(
        community_scores={1: 0.4, 2: 0.3},
        target_community_id=3,
        candidate_signal=1.0,
        temperature=0.25,
        boost=0.35,
    )
    single = candidate_information_gain(
        community_scores={1: 0.4},
        target_community_id=1,
        candidate_signal=1.0,
        temperature=0.25,
        boost=0.35,
    )

    assert missing.information_gain == 0.0
    assert single.information_gain == 0.0


def test_candidate_information_gain_clamps_negative_or_entropy_increasing_cases():
    result = candidate_information_gain(
        community_scores={1: 0.90, 2: 0.10},
        target_community_id=2,
        candidate_signal=0.20,
        temperature=0.25,
        boost=0.10,
    )

    assert result.information_gain == 0.0
    assert result.entropy_after >= result.entropy_before


def test_softmax_is_numerically_stable_for_extreme_scores():
    probabilities = softmax_probabilities({1: 1000000.0, 2: 999999.0}, temperature=1e-9)

    assert set(probabilities) == {1, 2}
    assert abs(sum(probabilities.values()) - 1.0) < 1e-12
    assert probabilities[1] > probabilities[2]


def test_entropy_from_scores_ignores_non_finite_scores():
    entropy = entropy_from_scores({1: 0.5, 2: float('nan'), 3: 0.5}, temperature=0.25)

    assert entropy > 0.0


def test_candidate_information_gain_handles_non_finite_parameters():
    result = candidate_information_gain(
        community_scores={1: 0.5, 2: 0.49},
        target_community_id=1,
        candidate_signal=float('nan'),
        temperature=float('nan'),
        boost=float('nan'),
    )

    assert result.information_gain == 0.0
    assert result.candidate_boost == 0.0


def test_softmax_is_uniform_for_equal_scores():
    probabilities = softmax_probabilities({1: 0.3, 2: 0.3, 3: 0.3}, temperature=0.25)
    assert set(probabilities) == {1, 2, 3}
    for cid in probabilities:
        assert abs(probabilities[cid] - (1.0 / 3.0)) < 1e-12


def test_entropy_is_maximal_when_uniform():
    """Three equally weighted communities should produce ~log2(3) bits."""
    from math import log2
    entropy = entropy_from_scores({1: 0.0, 2: 0.0, 3: 0.0}, temperature=0.25)
    assert abs(entropy - log2(3)) < 1e-9


def test_information_gain_grows_with_boost_magnitude():
    """A larger boost in an ambiguous distribution should reduce entropy more."""
    small = candidate_information_gain(
        community_scores={1: 0.4, 2: 0.39, 3: 0.38},
        target_community_id=1,
        candidate_signal=1.0,
        temperature=0.25,
        boost=0.05,
    )
    big = candidate_information_gain(
        community_scores={1: 0.4, 2: 0.39, 3: 0.38},
        target_community_id=1,
        candidate_signal=1.0,
        temperature=0.25,
        boost=0.50,
    )
    assert big.information_gain >= small.information_gain


def test_normalized_information_gain_is_in_unit_interval():
    """Even with an extreme boost, normalized gain must not exceed 1.0."""
    result = candidate_information_gain(
        community_scores={1: 1e-9, 2: 1e-9, 3: 1e-9},
        target_community_id=1,
        candidate_signal=1.0,
        temperature=0.25,
        boost=5.0,
    )
    assert 0.0 <= result.information_gain <= 1.0


def test_negative_boost_or_signal_yields_zero_gain():
    """Negative inputs should not be able to produce positive gain."""
    neg_boost = candidate_information_gain(
        community_scores={1: 0.4, 2: 0.39, 3: 0.38},
        target_community_id=1,
        candidate_signal=1.0,
        temperature=0.25,
        boost=-1.0,
    )
    neg_signal = candidate_information_gain(
        community_scores={1: 0.4, 2: 0.39, 3: 0.38},
        target_community_id=1,
        candidate_signal=-1.0,
        temperature=0.25,
        boost=0.35,
    )
    assert neg_boost.information_gain == 0.0
    assert neg_signal.information_gain == 0.0


def test_zero_temperature_does_not_explode():
    """Pathological zero temperature should fall back to a finite result."""
    probabilities = softmax_probabilities({1: 0.4, 2: 0.3}, temperature=0.0)
    assert set(probabilities) == {1, 2}
    assert abs(sum(probabilities.values()) - 1.0) < 1e-9


def test_empty_scores_returns_zero_metrics():
    result = candidate_information_gain(
        community_scores={},
        target_community_id=1,
        candidate_signal=1.0,
        temperature=0.25,
        boost=0.35,
    )
    assert result.entropy_before == 0.0
    assert result.entropy_after == 0.0
    assert result.information_gain == 0.0
    assert result.candidate_boost == 0.0
