# GitHub account audit — lowelltwong-alt

Date: 2026-07-27 · 33 repositories (16 public, 17 private), 2 already archived.

## What this session could and could not do

This session's credentials are **read-broad, write-narrow**:

| Capability | Scope |
| --- | --- |
| Repo/issue/PR search (GitHub API) | Whole account, public + private |
| `git clone` / `ls-remote` | All 16 **public** repos |
| `git clone` of private repos | Blocked (auth refused) |
| Branch deletion (`git push --delete`) | **Blocked everywhere** — HTTP 403 at the proxy, including `orphan-radar` |
| Repo archiving | Not available |

So **no branches were deleted and no repos were archived.** The analysis below is
complete for the 16 public repos; the two scripts in `scripts/` reproduce and
apply it — including for the 17 private repos — when run with your own `gh` login.

```bash
gh auth login                                   # needs `repo` scope
./scripts/maintenance/gh_branch_cleanup.sh                  # dry run across every repo
./scripts/maintenance/gh_branch_cleanup.sh --apply          # delete merged branches
./scripts/maintenance/gh_archive_plan.sh                    # dry run, tier-1 archives
./scripts/maintenance/gh_archive_plan.sh --apply            # archive them
```

The cleanup script re-derives merge status live rather than trusting the table
below, and never touches the default branch, protected branches, or a branch
with an open PR.

## Branch cleanup

Across the 16 public repos: **92 branches, 76 non-default. 30 are merged and
safe to delete; 46 are unmerged.**

Merge status was determined two ways — ancestry (`merge-base --is-ancestor`)
catches ordinary merges; a merge-tree identity check catches squash merges,
where the branch tip never becomes an ancestor of `main`.

### The 30 merged branches (delete these)

| Repo | Branch | How merged | SHA |
| --- | --- | --- | --- |
| logos-scripture-graph | `codex/t465-multi-model-reconciliation-gate` | ancestor | `f0cec96a` |
| logos-scripture-graph | `codex/t468-owner-chunking-decisions` | ancestor | `50b922bb` |
| logos-scripture-graph | `codex/t474-usfm-marker-anchor-repair` | ancestor | `2ea6db7b` |
| logos-scripture-graph | `codex/t475-shadow-refreeze-t519` | ancestor | `ac7263a2` |
| logos-scripture-graph | `codex/t511-generated-sidecar-lifecycle` | ancestor | `82cb454b` |
| logos-scripture-graph | `codex/t513-portable-ocr-research` | ancestor | `25a71f3e` |
| logos-scripture-graph | `codex/t518-codex-pointer-registry` | ancestor | `b90bf0d1` |
| logos-scripture-graph | `cursor/t477-canonical-regen-baseline-reset` | ancestor | `9dce299b` |
| LawFirm-os-orchestrator | `docs/ai-strategy-decision-bottleneck` | ancestor | `a064319b` |
| LawFirm-os-orchestrator | `docs/record-agent-hostile-control-milestone` | ancestor | `66d9008f` |
| LawFirm-os-orchestrator | `feature/legal-knowledge-runtime-adapter` | ancestor | `951b45d9` |
| LawFirm-os-orchestrator | `fix/prompt-integrity-lf-normalization` | ancestor | `e7c3ba85` |
| LawFirm-os-orchestrator | `phase2/pr09-pr12-compute-intelligence-seeds` | ancestor | `675ce3cf` |
| LawFirm-os-semantic-substrate | `docs/ai-strategy-decision-bottleneck` | ancestor | `ea8ff603` |
| LawFirm-os-semantic-substrate | `feature/legal-knowledge-runtime-contracts` | ancestor | `a9448306` |
| LawFirm-os-semantic-substrate | `phase2/pr01-control-plane-schemas-policies` | ancestor | `d2ac7f50` |
| LawFirm-os-skills-registry | `feat/skills-registry-v2-security-hardened` | ancestor | `6d583323` |
| LawFirm-os-skills-registry | `feature/legal-knowledge-skills` | ancestor | `2d4bd25d` |
| LawFirm-os-skills-registry | `refresh/agent-hostile-contract-lock` | ancestor | `a1b93064` |
| LawFirm-os-exceptions-lake-runtime | `feature/legal-knowledge-events` | ancestor | `c8638e43` |
| LawFirm-os-exceptions-lake-runtime | `orchestrator-handoff-boundary` | ancestor | `f786aeed` |
| law-firm-digital-twin | `agent/g0-g2-prototype` | ancestor | `b37f16a9` |
| law-firm-digital-twin | `codex/c023-source-lineage` | ancestor | `b263d13a` |
| logos-boundary-literature | `codex/t003-codex-pointer-registry` | ancestor | `b6a8d600` |
| logos-boundary-literature | `codex/llos-v1-boundary-index` | **squash** | `97320f6d` |
| logos-doctrine-genealogy | `codex/llos-v1-doctrine-index` | **squash** | `ab4419df` |
| logos-governance-architecture | `codex/llos-v1-governance` | **squash** | `14a500bd` |
| orphan-radar | `codex/dad-wave2-pointer` | **squash** (PR #5) | `9ac34a1d` |
| airca-fractal-decision-architecture | `feat/make-airca-usable` | ancestor | `728f60b0` |
| lairca-logos-grounded-theological-model | `logos-roadmap-build-from-scratch` | ancestor | `84bb0478` |

`lairca-...` is already archived, so its branch can only be deleted after an
`unarchive`. Skip it unless you want the tidiness.

To restore any of these: `git push origin <sha>:refs/heads/<branch>`.

### The 46 unmerged branches

Only **11 have an open PR**. The other **35 are abandoned work with no open PR** —
that is the actual mess, and none of it is safe to bulk-delete.

**`logos-scripture-graph` — 21 unmerged branches, zero open PRs.** This is the
worst concentration in the account. Most are `codex/t4xx-*` task branches from
2026-07-05 → 2026-07-20, each 40–114 commits behind `main`:

`codex/t451-bible-edge-taxonomy-deepening`, `codex/t479-leipzig-sinaiticus-acquisition`,
`codex/t482-sinaiticus-rights-decision`, `codex/t483-restricted-source-catalog`,
`codex/t484-predownload-readiness`, `codex/t485-postmerge-scope-repair`,
`codex/t492-theological-research-foundation`, `codex/t493-patristics-boundary-intake-plan`,
`codex/t494-theological-edge-taxonomy-research`, `codex/t495-doctrine-genealogy-governance-handoff`,
`codex/t497-fable-architecture-owner-decisions`, `codex/t498-changed-path-engine`,
`codex/t500-scripture-first-biblical-chunking-family`, `codex/t514-external-root-approval`,
`codex/llos-v1-scripture-adapter`, `codex/transport-spool-cutover`,
`cursor/src-pilot-a-t469-wave0`, `preserve/t470-t478-nas-scholarship-mirror`,
`preserve/t516-csntm-rights-gated-campaign`, `roster/2026-07`

The two `preserve/*` branches look intentionally retained — check before touching.

**`logos-governance-architecture` — 9 unmerged, zero open PRs.** `benchmark-question-corpus-foundation`
is 138 commits behind and last touched 2026-04-08; it is almost certainly dead.
The rest are `codex/*` gates from late June.

**The 5 public `LawFirm-os-*` repos share the same three stale branches**, a
fan-out that was never finished:

| Branch | Repos | Open PR? |
| --- | --- | --- |
| `codex/dad-wave1-pointer` | all 5 | yes — 5 open draft PRs |
| `codex/ci-manifest-refresh` | 4 (substrate uses `codex/semantic-ci-exclusions`) | yes — 5 open draft PRs |
| `codex/lawfirm-governance-map-gate` | all 5 | **no — PRs #7/#12/#6/#9/#7 were closed unmerged** |

`codex/lawfirm-governance-map-gate` ×5 is the cleanest sweep available: five
branches, closed PRs, nothing depending on them.

## Open issues and PRs

**13 open issues, 15 open PRs.** 13 of the 15 PRs are stale drafts.

### The stale draft-PR cluster (11 PRs, all opened 2026-07-01, 26 days old)

The same two `codex` changes were fanned out across five repos and none landed:

| PR | Repo |
| --- | --- |
| #9 / #10 | LawFirm-os-skills-registry |
| #17 / #18 | LawFirm-os-orchestrator |
| #9 / #10 | LawFirm-os-legal-knowledge-runtime |
| #13 / #14 | LawFirm-os-semantic-substrate |
| #10 / #11 | LawFirm-os-exceptions-lake-runtime |
| #35 | LawFirm-os-talent-intelligence (private) |

These are a batch decision, not eleven decisions: either finish the DAD Wave 1 +
CI manifest rollout, or close all eleven and delete the branches. Leaving them
open is the current state and it is costing you the signal.

Note `orphan-radar` already completed this rollout as **Wave 2** (PR #5, merged
2026-07-14), which suggests the Wave 1 fan-out was superseded rather than
abandoned — worth confirming before you close them.

### Other open PRs (recent, likely genuine)

- `LawFirm-os-semantic-substrate` #17 — synthetic adversity registry (17d)
- `world-maker-contracts` #1, `world-maker` #1 — the Fable split (5d, 4d)
- `Digital-Assett-Directory` #87 — DAD preflight rating calibration (5d)

### Open issues

Four are 75 days old and predate most of the current architecture:

- `LawFirm-os-semantic-substrate` #1 — seed contract authority bundle
- `LawFirm-os-exceptions-lake-runtime` #1 — validate-only handoff
- `LawFirm-os-orchestrator` #3 — classify-exception MVP
- `LawFirm-os-skills-registry` #2 — *title is just a URL to its own repo; this is malformed, close it*

Four more in `kirsten-dissertation-knowledge-graph` (#4–#7, 62d) are all
"Cursor task: …" — agent scratch tickets that were never closed out.

`logos-governance-architecture` has two "Monthly Architecture Alignment Review"
issues open at once (#50 for June, #69 for July). June's should be closed.

`logos-doctrine-genealogy` #4 — "Owner decision needed: data-readiness lane
selection" — is a genuine blocker gating that repo's tier-2 archive decision.

## Archive recommendations

Archiving is reversible (`gh repo unarchive`) and keeps the repo visible and
cloneable — it only makes it read-only. Cheap to do, easy to undo.

### Tier 1 — archive now (6 repos)

| Repo | Vis | Idle | Why |
| --- | --- | --- | --- |
| `exceptions-lake-runtime` | private | 87d | Superseded by public `LawFirm-os-exceptions-lake-runtime` (48 commits, active). Clear predecessor. |
| `obsidian-foundry-vault` | private | 68d | 10 KB. Created and last pushed the same day — never developed past scaffold. |
| `Bi-Test` | private | 41d | Declares itself a test repo. |
| `All-Law-Firm-Talent-Intel` | private | 34d | Oldest of three overlapping talent repos. |
| `lowell-career-os` | private | 54d | 23 KB personal scratch. |
| `noesis-atlas` | public | 59d | 6 commits over 3 days in May, nothing since. Public scaffold. |

### Tier 2 — decide first (4 repos)

- **`LawFirm-os-talent-intelligence` vs `LawFirm-Talent-Intel-ATS`** — two live
  private talent repos, last pushed a day apart (07-01, 07-02). Keep one, archive
  the other. `-talent-intelligence` also holds stale draft PR #35.
- **`fmg-fractal-capability-ontology`** — 793 KB, dormant 54d, described as the
  "canonical rebuilt repository". Archive unless the FMG line is resuming.
- **`airca-fractal-decision-architecture`** — 110 commits, 2 stars, dormant 54d.
  Real public work that `logos-governance-architecture` still references by topic.
  Archive only if the AIRCA line is genuinely finished; otherwise leave it.
- **`logos-doctrine-genealogy`** — self-described "scaffold-only until governed
  data gates exist". Resolve open issue #4 first, then build it or archive it.

### Do not archive

**`lowelltwong-alt`** — this is your GitHub profile README repo. It is dormant
(54d) and looks archivable, but archiving it greys out the header on your public
profile page.

### Already archived (2)

`logos-governed-core`, `lairca-logos-grounded-theological-model`

### Active — keep (21)

`Digital-Assett-Directory`, `Albert-Trial-Simulation-System`, `LawFirm-os-intake`,
`dad-journal`, `Albert-Simulation-Core-Private`, `claude-legal-audit-lab`,
`world-maker`, `world-maker-contracts`, `law-firm-digital-twin`,
`logos-scripture-graph`, `logos-boundary-literature`, `logos-governance-architecture`,
`orphan-radar`, `kirsten-dissertation-knowledge-graph`, and the five public
`LawFirm-os-*` repos.

## Suggested order

1. Run `gh_branch_cleanup.sh --apply` — clears 30 merged branches, plus whatever
   it finds in the 17 private repos this session could not read.
2. Decide the DAD Wave 1 / CI-manifest cluster as one batch (11 draft PRs).
3. Delete `codex/lawfirm-governance-map-gate` ×5 — closed PRs, nothing pending.
4. Triage `logos-scripture-graph`'s 21 orphaned branches. Check the two
   `preserve/*` ones first.
5. Run `gh_archive_plan.sh --apply` for tier 1.
6. Close the four 75-day issues and `logos-governance-architecture` #50.

## Notes

- Branch counts and merge status are for the 16 public repos only. The private
  repos were not clonable from this session; the scripts cover them.
- `MERGED_SQUASH` is inferred from merge-tree identity: merging the branch into
  `main` produces exactly `main`'s tree, so it contributes nothing. A branch
  whose changes were merged and then fully reverted would also match — none of
  the four here look like that, and the cleanup script independently confirms
  via the GitHub PR API before deleting.
- The `AGENTS.md` DAD preflight/postflight contract could not be honored: the
  `asset-dir` CLI is not installed in this container and the hub path is a local
  Windows path. No preflight or postflight was recorded for this session.
