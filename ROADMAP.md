# Roadmap

## v0.1 — done

- Local scan for `.md` / `.txt` notes.
- OrphanRank v0.2 classical pipeline.
- Source mutation protection.
- Markdown review report.
- Link-reconstruction eval with recall@k / MRR and optional weight calibration.
- Code-aware parsing (links/tags ignored inside fenced and inline code).
- Validated configuration (range checks + unknown-key warnings).
- CI: ruff, mypy, and pytest on every push.

## v0.1.1 — done (2026-06-03)

- **Shannon information-gain signal in candidate ranking** (PR #1). Bounded,
  numerically-stable entropy-reduction metric; default weight `0.08`,
  temperature `0.25`, boost `0.35`. Guarded against NaN/Inf. Added four
  metrics keys to `CandidateEdge` and `EvidencePacket`.
- **Behavior test + CHANGELOG** (PR #2). Corpus-level assertion that the
  feature does not break reconstruction; math-invariant tests.
- **Sensitivity sweep + multi-seed calibration study** (PR #3). LOO on/off,
  72-point grid, 30-seed random holdout, 10-seed calibration stability. On
  the demo corpus the feature is inert at defaults. See
  `docs/INFORMATION_GAIN_SENSITIVITY.md` and
  `scripts/sweep_information_gain.py`.
- **Red-team review** completed; all follow-ups (F1–F8, F14) resolved. See
  `docs/REDTEAM_INFORMATION_GAIN.md` and `HANDOFF.md`.

## Next — validate on a real corpus

- **Run `scripts/sweep_information_gain.py --src /path/to/vault`** against a
  multi-hundred-note corpus. The demo corpus (8 notes, 7 edges) is too small
  to detect a real effect.
- If the feature shows recall@5 lift: update defaults in `core/settings.py`
  and document the evidence.
- If the feature remains inert: consider removing it to reduce complexity.

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
