# Handoff — Information-Gain Feature Integration

Date: 2026-06-03

## What was done

Four work items from the red-team review were executed in a single session:

### 1. F4 — Cross-linked the Semantic Substrate's two Shannon notes

**Repo:** `LawFirm-os-semantic-substrate`
**PR:** #8 (squash-merged, verified)

The substrate had two Shannon concept notes that looked like duplicates but
serve distinct purposes:

- `governance/SHANNON_INFORMATION_THEORY_CROSSWALK.md` — metrics-discipline
  angle: which entropy-style metrics are allowed, with caveats and forbidden
  uses.
- `docs/architecture/SHANNON_INFORMATION_THEORY_AND_SEMANTIC_AUTHORITY.md` —
  substrate-internal angle: why the control plane sits upstream of runtimes,
  data-processing inequality formalizes the mutation boundary.

Action: added reciprocal `Companion note:` links in both files with a
one-sentence scope distinction. No merge, no content changes.

### 2. FMG — Tailored Shannon concept note

**Repo:** `fmg-fractal-capability-ontology`
**PR:** #44 (squash-merged, verified)

New file: `docs/architecture/SHANNON_INFORMATION_THEORY_AND_CAPABILITY_ROUTING.md`

Tailored to FMG's control-plane / mutation-boundary identity. The
data-processing inequality formalizes the
`exception-event -> pressure-vector -> adaptation-proposal -> promotion-decision`
chain. Follows the standard concept-note pattern (YAML frontmatter,
BLUF, Boundary, Real math used, Non-goals).

### 3. Kirsten — Tailored Shannon concept note

**Repo:** `kirsten-dissertation-knowledge-graph`
**PR:** #9 (squash-merged, verified)

New file: `SHANNON_INFORMATION_THEORY_AND_CITATION_INTEGRITY.md` (top-level,
matching repo convention).

Tailored to citation/provenance/source-integrity: "polish is not provenance,"
anchors and page references as structured redundancy, cascade sensitivity as a
Lyapunov-style analogy (not claim). Boundary section blocks the note from
asserting legal correctness.

### 4. F7/F8 — Sensitivity sweep + multi-seed calibration (orphan-radar)

**Repo:** `orphan-radar`
**PR:** #3 (squash-merged, verified)

Three files landed:

| File | Purpose |
|---|---|
| `scripts/sweep_information_gain.py` | Reproducible evidence-gathering harness: LOO on/off, 72-point sensitivity grid, 30-seed random holdout, 10-seed calibration stability |
| `docs/INFORMATION_GAIN_SENSITIVITY.md` | Write-up of results, safe ranges, honest limitations |
| `CHANGELOG.md` | Updated consumer notes with empirical findings |

**Key findings on `examples/demo_notes` (8 notes, 7 eligible edges):**

- Feature is **inert at defaults** — LOO reconstruction identical on vs. off;
  30/30 random-holdout seeds tied.
- recall@5 invariant (0.857) across the entire 72-point hyperparameter grid.
- MRR only ever moves **downward**, only at aggressive settings
  (`information_gain >= 0.16` with `boost = 1.0`).
- Calibration "best" weight scatters ~50x across seeds — pure noise on 7 edges.

### F14 — Decision: KEEP the feature

No code change. The information-gain feature is non-regressive at sane defaults,
fully guarded (NaN/Inf, clamp-to-zero), and defaulted low. Its plausible upside
is on larger corpora where community routing is actually ambiguous. Documented in
`docs/INFORMATION_GAIN_SENSITIVITY.md` and `CHANGELOG.md`.

---

## What was NOT done

- No weight tuning against the demo corpus (explicitly avoided — calibration is
  noise at this scale).
- No changes to ranking logic, default weights, or pipeline behavior.
- No new dependencies added.
- No changes to any repo's CI configuration.

---

## Immediate next steps (for the next contributor)

1. **Run the sweep on a real vault.** The demo corpus is too small to detect a
   real effect. Point `scripts/sweep_information_gain.py --src /path/to/vault`
   at a multi-hundred-note corpus and re-evaluate:
   - Does the feature produce any recall@5 lift?
   - At what weight/temperature/boost settings?
   - Is the calibrated weight stable across seeds?

2. **If the feature shows lift on a real corpus:** update defaults in
   `core/settings.py` and document the evidence in
   `docs/INFORMATION_GAIN_SENSITIVITY.md`.

3. **If the feature remains inert on real corpora:** consider removing it to
   reduce complexity (it adds one module, four metrics keys, and three
   hyperparameters for zero measured benefit).

---

## Open items from the broader roadmap

These are inherited from `ROADMAP.md` and the red-team, not from this session:

- Scale beyond ~10k notes (O(N^2) similarity matrix).
- Obsidian adapter.
- VS Code adapter.
- Local embedding backend.
- Tighten mypy toward `strict = true`.

---

## Repo locations

| Repo | Local path |
|---|---|
| orphan-radar | `02_Other_Git_Projects/orphan_radar/orphan-radar/` |
| LawFirm-os-semantic-substrate | `00_LawFirm_OS/LawFirm-os-semantic-substrate/` |
| fmg-fractal-capability-ontology | `02_Other_Git_Projects/fmg-fractal-capability-ontology/` |
| kirsten-dissertation-knowledge-graph | `02_Other_Git_Projects/kirsten-dissertation-knowledge-graph/` |

---

## Constraints carried forward

- Documentation-only unless code changes explicitly approved.
- Do not publish private/concept repo names in public repos.
- Use real math only — no pseudo-math.
- Shannon, entropy, chaos, Kant, Spinoza, Logos are **not** sources of
  legal, theological, or governance authority.
- Per-repo feature branches; squash-merge via `gh pr merge --squash --delete-branch`.
- Stage only specific files (avoid linter contamination).
