from __future__ import annotations

from dataclasses import dataclass
from math import exp, isfinite, log2


@dataclass(frozen=True)
class InformationGainMetrics:
    """Entropy-reduction signal for a proposed candidate link.

    Values are deliberately normalized and bounded so the metric can be safely
    used as one additive ranker feature rather than as a hard truth claim.
    """

    entropy_before: float = 0.0
    entropy_after: float = 0.0
    information_gain: float = 0.0
    candidate_boost: float = 0.0


def _finite_float(value: float, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if isfinite(number) else default


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    value = _finite_float(value, default=low)
    return max(low, min(high, value))


def _clean_scores(scores: dict[int, float]) -> dict[int, float]:
    cleaned: dict[int, float] = {}
    for cid, raw in scores.items():
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if isfinite(value):
            cleaned[int(cid)] = value
    return cleaned


def softmax_probabilities(scores: dict[int, float], temperature: float) -> dict[int, float]:
    """Convert arbitrary community scores into pseudo-probabilities.

    The community router's scores are not calibrated probabilities. This helper
    treats them only as a local ranking distribution so entropy can measure
    assignment ambiguity. The implementation subtracts the maximum scaled score
    before exponentiating for numerical stability.
    """

    cleaned = _clean_scores(scores)
    if not cleaned:
        return {}

    temperature = max(_finite_float(temperature, default=1.0), 1e-9)
    scaled = {cid: value / temperature for cid, value in cleaned.items()}
    max_scaled = max(scaled.values())
    exp_values = {cid: exp(value - max_scaled) for cid, value in scaled.items()}
    denom = sum(exp_values.values())
    if denom <= 0.0 or not isfinite(denom):
        uniform = 1.0 / len(exp_values)
        return {cid: uniform for cid in exp_values}
    return {cid: value / denom for cid, value in exp_values.items()}


def entropy_from_scores(scores: dict[int, float], temperature: float) -> float:
    """Return Shannon entropy in bits for softmaxed community scores."""

    probabilities = softmax_probabilities(scores, temperature)
    entropy = 0.0
    for probability in probabilities.values():
        if probability > 0.0:
            entropy -= probability * log2(probability)
    return max(0.0, entropy)


def candidate_information_gain(
    community_scores: dict[int, float] | None,
    target_community_id: int | None,
    candidate_signal: float,
    temperature: float,
    boost: float,
) -> InformationGainMetrics:
    """Estimate how much a candidate link reduces routing uncertainty.

    The candidate does not mutate the graph. It simulates a small bounded boost
    to the target community, recomputes entropy, and reports normalized entropy
    reduction. Negative reductions are clamped to zero so ambiguous or misleading
    boosts cannot increase a candidate's score through this feature.
    """

    if target_community_id is None or not community_scores:
        return InformationGainMetrics()

    scores = _clean_scores(community_scores)
    if target_community_id not in scores or len(scores) <= 1:
        return InformationGainMetrics()

    signal = _clamp(candidate_signal)
    applied_boost = signal * max(_finite_float(boost), 0.0)
    entropy_before = entropy_from_scores(scores, temperature)

    if applied_boost <= 0.0:
        return InformationGainMetrics(
            entropy_before=entropy_before,
            entropy_after=entropy_before,
            information_gain=0.0,
            candidate_boost=0.0,
        )

    boosted_scores = dict(scores)
    boosted_scores[target_community_id] = boosted_scores[target_community_id] + applied_boost
    entropy_after = entropy_from_scores(boosted_scores, temperature)

    max_entropy = log2(len(scores))
    raw_gain = max(0.0, entropy_before - entropy_after)
    normalized_gain = _clamp(raw_gain / max_entropy) if max_entropy > 0.0 else 0.0

    return InformationGainMetrics(
        entropy_before=entropy_before,
        entropy_after=entropy_after,
        information_gain=normalized_gain,
        candidate_boost=applied_boost,
    )
