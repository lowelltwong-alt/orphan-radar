# Changelog

All notable changes to this project will be documented in this file.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions are not yet tagged.

## Unreleased

### Fixed

- **CI no longer breaks when a linter releases.** The lint rule set is now
  declared explicitly (`[tool.ruff.lint] select = ["E4", "E7", "E9", "F"]`)
  instead of inheriting ruff's defaults, which widened in a newer release and
  turned CI red on an unchanged tree. Upper bounds added to `ruff` and `mypy`.
- **mypy no longer parses third-party stubs targeting a newer Python.**
  numpy 2.5 ships PEP 695 `type` statements in its stubs; with
  `python_version = "3.11"` mypy rejected them. Stubs for
  numpy/scipy/sklearn/networkx are now skipped via a scoped override plus
  `follow_imports_for_stubs`; first-party cross-module checking is unaffected.

### Added

- **Shannon-style information-gain signal in candidate ranking.** A bounded,
  numerically-stable entropy-reduction metric over the orphan note's community
  routing distribution. Implemented as one additive term in
  `score_candidate` alongside the existing signals; default weight `0.08`,
  default `entropy_temperature` `0.25`, default `information_gain_boost`
  `0.35`. Negative gains are clamped to zero; non-finite inputs are guarded.
  See `docs/INFORMATION_THEORY_FRAMING.md` for scope and non-claims, and
  `docs/REDTEAM_INFORMATION_GAIN.md` for attacks/mitigations.
- **Entropy fields in candidate metrics and evidence packets.** The
  `metrics` dict on `CandidateEdge` and `EvidencePacket` now carries four
  additional keys: `information_gain`, `community_entropy_before`,
  `community_entropy_after`, `candidate_entropy_boost`. These additions are
  **additive** — no existing key has been removed or renamed. Downstream
  JSONL consumers that ignore unknown keys are unaffected.
- **Behavior test for information-gain ranking.** `tests/test_information_gain.py`
  now includes a corpus-level assertion that the feature does not break a
  reconstruction the ranker can already solve. This complements the existing
  math-invariant tests (entropy reduction, NaN/Inf safety, normalization).
- **`information_gain` added to the calibration weight vector** in
  `eval.link_reconstruction.WEIGHT_FIELDS`. The random-search calibrator
  now searches over the new weight alongside the existing eight.

### Notes for consumers

- The new metrics keys appear in `candidate_edges.jsonl` and
  `evidence_packets.jsonl` outputs. They are not present in scans produced
  before this change.
- Hyperparameters (`entropy_temperature`, `information_gain_boost`,
  `information_gain` weight) are heuristic defaults. They have **not** been
  calibrated against a real corpus; treat them as starting points and
  validate per-corpus with the link-reconstruction eval before relying on
  any tuned vector.
- Calibration's `improved: true` on small corpora (single-edge holdouts)
  is single-seed noise. A sensitivity sweep + multi-seed study now
  documents this empirically: see `docs/INFORMATION_GAIN_SENSITIVITY.md`
  and `scripts/sweep_information_gain.py`. On the demo corpus the feature is
  **inert at defaults** (identical reconstruction on/off, 30/30 seeds tied)
  and only ever *degrades* MRR when over-weighted, so keep the weight low and
  do not adopt calibrated weights from a corpus this small.

### Internal

- Threaded `community_scores` from `pipeline.run_scan` and
  `eval.link_reconstruction._rank_of_target` into `score_candidate`.
- Added `src/orphan_radar/rank/information_gain.py` (new module).
