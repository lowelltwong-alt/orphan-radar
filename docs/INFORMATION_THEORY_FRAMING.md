# Information-theory framing

Orphan Radar treats a candidate link as useful when it reduces uncertainty
about where a note belongs in the local knowledge graph. Generic hubs may
route attention, but they often reduce little uncertainty. Specific,
evidence-backed links are preferred because they make the graph more
informative while leaving final promotion to a human reviewer.

This is consistent with the lineage note: *Hubs route attention. Specific
links reduce uncertainty. Review keeps the graph honest.*

## What is implemented

`src/orphan_radar/rank/information_gain.py` adds a Shannon-style
entropy-reduction signal to the candidate ranker. For each candidate link:

1. The community router already produces a per-community score vector for the
   orphan note. We treat these as a local routing distribution by passing them
   through a temperature-scaled softmax. They are **not** calibrated
   probabilities; they are a ranking distribution.
2. We compute Shannon entropy *H_before* over that distribution in bits.
3. We simulate a small bounded boost (`information_gain_boost * pre_signal`)
   applied to the candidate's target community.
4. We recompute entropy *H_after*.
5. The normalized information gain is
   `clamp((H_before - H_after) / log2(k))` where `k` is the number of routed
   communities. Negative gains (entropy increases) are clamped to zero so a
   misleading candidate cannot be rewarded by this feature.

The feature enters `score_candidate` as one additive term, multiplied by the
configurable weight `settings.information_gain` (default 0.08). It does not
replace any existing signal.

## What is deliberately not claimed

- The metric does not measure truth. It measures whether a candidate link
  reduces the routing ambiguity of where the orphan note belongs.
- Community scores are not probability estimates of community membership in
  any rigorous sense. They are a weighted similarity combination from
  `community_router.score_note_to_communities`. The softmax is a convenience
  for entropy, not a claim about calibration.
- The simulated boost is a heuristic. Its magnitude (`information_gain_boost`)
  is a knob, not a derived constant.

## Why the existing signals are still required

- Hub penalty still applies. A generic hub that happens to point at the
  dominant community gets a low net score even if its raw entropy reduction
  is large, because `hub_penalty * hub.hub_penalty` is subtracted.
- The quality gate (`passes_quality_gate`) still requires shared terms, shared
  tags, or folder proximity. Information gain alone cannot push a candidate
  through to the review queue.
- The pre-information signal that feeds the simulated boost uses
  title/content/tags/folder/specificity. It does not use the final candidate
  score, so the ranker does not self-reinforce.

## Recommended acceptance rule

Treat tuned weights with skepticism. The link-reconstruction calibrator
performs a random search and adds another degree of freedom by including
`information_gain`. Adopt a tuned weight vector only if recall@k and MRR
improve across more than one holdout seed, and only if the candidate evidence
remains readable to a human reviewer.

## Where Shannon ends

Source coding, channel capacity, and Shannon-Hartley are not implemented and
are not part of the ranker. They are useful as a way to talk about
governance and review attention (humans have finite review capacity, so
queue the highest expected information-gain items first), but the math in
this repository deliberately stops at entropy of a local routing
distribution.
