# Orphan Radar

Orphan Radar is a **local-first knowledge-graph maintenance engine**.

It scans a folder of Markdown/text notes, detects hard and weak orphan notes, assigns them to likely graph communities, ranks candidate target notes, detects bridge candidates, and writes a human-reviewable report.

It does **not** send note content to external services. It does **not** call LLMs. It does **not** mutate source files. The current implementation is classical: NetworkX graph structure plus scikit-learn TF-IDF.

## Core loop

1. Scan notes.
2. Build a local graph from existing links.
3. Build a TF-IDF similarity layer.
4. Detect hard and weak orphan notes.
5. Route each orphan to likely communities.
6. Rank specific candidate targets inside those communities.
7. Penalize generic hubs without punishing specific authority nodes.
8. Detect bridge candidates between weakly connected communities.
9. Generate evidence packets and a review report.
10. Verify source files were not modified.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
orphan-radar scan --src ./examples/demo_notes --out ./radar_output
```

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
orphan-radar scan --src .\examples\demo_notes --out .\radar_output
```

## CLI

```bash
orphan-radar scan --src ./examples/demo_notes --out ./radar_output
orphan-radar status --src ./examples/demo_notes
orphan-radar eval --src ./examples/demo_notes --out ./radar_eval
orphan-radar lineage
```

## Outputs

A scan writes:

```text
radar_output/
  graph.json
  communities.json
  orphan_notes.jsonl
  candidate_edges.jsonl
  bridge_candidates.jsonl
  evidence_packets.jsonl
  review_report.md
  run_summary.json
```

## Current limits

- Supports `.md` and `.txt` files.
- Uses local TF-IDF, not semantic embeddings.
- Does not auto-apply links.
- Does not mutate source notes.
- Quantum algorithms are not implemented. See `docs/QUANTUM_ROADMAP.md` for a sober future-research framing.

## Lineage note

Orphan Radar is a small practical descendant of three ideas: PageRank-style graph authority, Shannon-style uncertainty reduction, and human-reviewed knowledge curation. Hubs can route attention, but specific evidence-backed links reduce uncertainty. See `docs/LINEAGE.md`.
