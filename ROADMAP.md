# Roadmap

## v0.1

- Local scan for `.md` / `.txt` notes.
- OrphanRank v0.2 classical pipeline.
- Source mutation protection.
- Markdown review report.
- Link-reconstruction eval with recall@k / MRR and optional weight calibration.
- Code-aware parsing (links/tags ignored inside fenced and inline code).
- Validated configuration (range checks + unknown-key warnings).
- CI: ruff, mypy, and pytest on every push.

## Later

- **Scale beyond ~10k notes.** The current similarity stage builds a dense all-pairs
  cosine matrix in `build_hybrid_graph` (O(N²) memory) and holds full note bodies in
  RAM. For large vaults, replace all-pairs cosine with a top-k nearest-neighbour pass
  (e.g. `sklearn.neighbors`), bound the vectorizer (`max_features`, `min_df=2`), and
  stream note bodies rather than retaining them.
- Tighten mypy toward `strict = true`, module by module.
- Obsidian adapter.
- VS Code adapter.
- Local embedding backend.
- Better bridge-node labeling.
- All-pairs cross-community bridge detection as an optional deeper pass.
- Optional UI.
- Sober quantum research module only after large-scale classical baselines exist.
