# OrphanRank v0.2

OrphanRank v0.2 detects hard and weak orphan notes, assigns them to likely graph communities, ranks candidate targets inside those communities, distinguishes generic hubs from authoritative specific nodes, detects bridge candidates between weakly connected communities, and generates a review queue that balances quick wins, uncertain high-impact edges, and structural bridge opportunities.

## Core corrections

- Degree-only hub penalty is wrong.
- Flat global ranking is wrong.
- Hardcoded weights need evaluation. *(Implemented: `eval/link_reconstruction.py` hides a
  holdout of existing links, re-runs the ranker, and reports recall@k / MRR; `--calibrate`
  random-searches the weight vector against that proxy.)*
- Hard orphans and weak orphans need separate tracks.
- Bridge candidates are overlays, not exclusive orphan classes.
- No-source-mutation must be enforced, not merely promised.
