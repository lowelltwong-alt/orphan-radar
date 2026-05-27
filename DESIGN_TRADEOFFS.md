# Design Tradeoffs

## Why classical first?

NetworkX and scikit-learn are sufficient to test the product hypothesis. Quantum algorithms, LLMs, and cloud embeddings would add complexity before the local workflow is proven.

## Why no silent mutation?

Automatic link insertion can pollute a knowledge graph. Orphan Radar writes review artifacts only.

## Why two-pass routing?

Flat global ranking over-connects orphans to generic hubs. Orphan Radar first routes an orphan to likely communities, then ranks specific candidates inside those communities.

## Why a calibration harness?

Hardcoded scoring weights are only useful if there is a proxy evaluation path. Link reconstruction provides that path without requiring labeled data.
