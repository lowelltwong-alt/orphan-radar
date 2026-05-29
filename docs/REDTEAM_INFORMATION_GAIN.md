# Information-gain integration: red-team notes

## Scope

This integration adds a Shannon-style entropy-reduction signal to candidate
link ranking. It does **not** treat model output or graph structure as truth.
It treats community routing scores as a local ambiguity distribution and
rewards candidate links only when a bounded simulation reduces that
ambiguity.

## What changed

- Added `src/orphan_radar/rank/information_gain.py` (new module).
- Added `information_gain`, `entropy_temperature`, and `information_gain_boost`
  fields to `RadarSettings` with `_BOUNDS` validation.
- Threaded `community_scores` from `pipeline.run_scan` and
  `eval.link_reconstruction._rank_of_target` into `score_candidate`.
- Added `information_gain` to `eval.link_reconstruction.WEIGHT_FIELDS`,
  bringing it into the random-search calibrator.
- Added the new metric and entropy fields to candidate `metrics` and to
  evidence packets, plus a human-readable reason
  ("link reduces community assignment uncertainty").
- Added `tests/test_information_gain.py` with 13 unit cases covering
  entropy reduction, missing/single community, negative/entropy-increasing
  clamps, numerical stability, non-finite inputs, uniform distributions,
  monotone-with-boost, normalization, negative inputs, zero temperature,
  and empty scores.
- Added `docs/INFORMATION_THEORY_FRAMING.md` explaining what the feature
  does and does not claim.

## Verification performed

- `python -m py_compile` on all touched files: passed.
- `pytest tests/` (the full repo suite, 29 tests including the 13 new ones):
  all passed.
- `orphan-radar scan --src ./examples/demo_notes --out ...`: completed,
  source files unmutated, evidence packets contain the new entropy fields,
  and the reason text fires on candidates where normalized gain > 0.05.
- `orphan-radar eval --src ./examples/demo_notes --out ...` before and
  after the integration: identical link-reconstruction numbers on the
  8-note demo corpus (recall@5=0.0, MRR=0.1667). The new feature does not
  silently regress eval on this corpus; the corpus is too small to show
  signal.
- `orphan-radar eval --calibrate --trials 40`: calibrator successfully
  searches over the new weight. Reported `improved: true` with a different
  vector, but on a corpus with `eligible_edges=7` and `hidden_edges=1` this
  is a one-trial fluctuation, not durable evidence.
- 20,000-case randomized fuzz over score / target / signal / temperature /
  boost cases (including NaN, Inf, negative inputs, zero temperature, single
  community, missing target): no invariant violations. The invariants
  checked are: all metrics finite; `information_gain ∈ [0, 1]`;
  `entropy_before ∈ [0, log2(k)]`; if `information_gain > 0` then
  `entropy_after ≤ entropy_before`; softmax probabilities sum to 1.

## Red-team findings and mitigations

### 1. Pseudo-probability risk

**Attack:** Community scores are not calibrated probabilities. Softmax
entropy can look precise while only describing a routing heuristic.

**Mitigation:** Named and exposed as `information_gain`, but implemented as
a bounded additive feature with default weight 0.08. It does not replace
content similarity, tags, folder signal, authority, specificity, hub
penalty, or human review. Documentation in
`docs/INFORMATION_THEORY_FRAMING.md` explicitly says the metric is a
ranking heuristic, not a probability estimate.

**Residual risk:** `entropy_temperature` and `information_gain_boost`
require empirical calibration per corpus. Defaults (0.25 and 0.35) were
chosen for community scores that sit in roughly the [0, 1] range produced
by `community_router.score_note_to_communities`.

### 2. Circular scoring risk

**Attack:** If information gain were a function of the final candidate
score, the ranker would self-reinforce.

**Mitigation:** The simulated boost uses a separate `pre_information_signal`
built from title / content / tag / folder / specificity. It does not use
the final `raw_score`.

**Residual risk:** The pre-signal still includes 10 % specificity, which
comes from hub metrics. That coupling is small but should be watched
during calibration.

### 3. Hub gaming risk

**Attack:** Generic hubs may reduce routing uncertainty by pointing at the
dominant community even when they are weak links.

**Mitigation:** The final score still subtracts `hub_penalty *
hub.hub_penalty`. The quality gate still requires shared terms / tags /
folder evidence. `information_gain` has the lowest default weight in the
additive vector.

**Residual risk:** In corpora with one very dominant community, a small
but nonzero gain may still lift weak candidates above the
`min_candidate_score` boundary. Keep the default weight low and validate
with link reconstruction before adopting tuned weights.

### 4. Entropy-increase risk

**Attack:** Boosting a low-probability target can increase ambiguity.

**Mitigation:** Negative gain is clamped to zero in
`candidate_information_gain` and re-checked in the fuzz harness
(`information_gain > 0 ⇒ entropy_after ≤ entropy_before`). It cannot
increase the score.

**Residual risk:** Zero gain still leaves the candidate ranked by existing
signals.

### 5. Numerical instability risk

**Attack:** Extreme scores, zero temperature, NaN, or Infinity could
produce overflow or invalid metrics.

**Mitigation:** Scores are cleaned for finiteness; softmax subtracts the
maximum scaled value before exponentiating; temperature is lower-bounded
at 1e-9; non-finite signal and boost become zero; tests cover extreme
cases; 20k fuzz cases pass.

**Residual risk:** Very large community counts add linear CPU cost. The
default routes the top-3 communities per orphan so this is bounded in
practice.

### 6. Calibration overfit risk

**Attack:** Adding another weight field gives the random search another
degree of freedom and can overfit a small holdout.

**Mitigation:** The field is added because it is a real additive term.
Adoption of tuned weights is left to a human gated on multi-seed
improvement. The `INFORMATION_THEORY_FRAMING.md` doc explicitly says so.

**Residual risk:** On `examples/demo_notes` the calibrator reports
`improved: true` based on a single held-out edge. That is not durable
evidence. Recommend running calibration on a real corpus with multiple
seeds before treating any tuned vector as canonical.

### 7. Review-explanation risk

**Attack:** "Information gain" language could imply truth rather than
routing clarity.

**Mitigation:** The evidence reason reads
`link reduces community assignment uncertainty`, not `link is true`. The
metric appears alongside the existing entropy fields so a reviewer can
see what reduction was simulated.

**Residual risk:** None we can fix in code. Reviewers must read the
framing doc to understand what the metric does and does not mean.

### 8. Backwards-compatibility risk

**Attack:** Existing callers of `score_candidate` would break if they
already pass positional arguments past `rank`.

**Mitigation:** `community_scores` is added as the last parameter and
defaults to `None`. All callers in the repo were updated to pass
`community_scores=...` explicitly. With `community_scores=None` the new
feature contributes exactly zero to the score, so the function is a
strict superset of its previous behaviour.

## Acceptance gate

Adopt the integration as-is. Treat any specific weight vector produced by
`--calibrate` as a hypothesis. Re-run calibration across multiple holdout
seeds and a representative corpus before promoting tuned weights into
`configs/default_weights.json`.
