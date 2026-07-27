# Open PR and issue triage — 2026-07-27

Resolves the last two items from `github-audit-2026-07-27.md`: the 11-PR
"stale draft cluster" and the 13 open issues.

Method: for every PR, the **true merge result** was computed with
`git merge-tree --write-tree main <branch>` and diffed against `main`. A
plain two-dot `git diff main <branch>` is misleading here — it shows the
branch tip missing everything `main` gained since the merge-base, which
reads as thousands of deletions that a merge would never perform. Every
"deletes N lines" instinct about these branches is an artifact of that.

**All 11 PRs merge cleanly. None conflict.** The question is not *can* they
merge but *should* they.

## The cluster splits in two, with opposite answers

The audit treated the 11 PRs as one batch. They are two batches with
different verdicts.

### Group A — DAD Wave 1: close all five, do not merge

| PR | Repo |
| --- | --- |
| #9 | LawFirm-os-skills-registry |
| #17 | LawFirm-os-orchestrator |
| #9 | LawFirm-os-legal-knowledge-runtime |
| #13 | LawFirm-os-semantic-substrate |
| #10 | LawFirm-os-exceptions-lake-runtime |

Each merges cleanly and additively: **+71 lines, 5 files, zero deletions**,
identical across all five repos. Safe — and superseded.

**The timeline is decisive.** The Wave 1 branch tip is **2026-06-30**. On
**2026-07-08**, `main` in every one of these repos gained a materially more
advanced DAD integration via "Add DAD transport surface v1 contract". `main`
already has:

- `.digital-asset/dad-integration.json` — richer than anything Wave 1 adds,
  carrying `approved_dad_managed_paths`, `agent_runtime_policy`, and
  `vendor_lock_in_prohibited`
- the full `.digital-asset/` tree — `assets/`, `key-values/`,
  `governance-map.yaml`, `data-map.yaml`, `skills/checkout.json`,
  `context-map.json`
- `.githooks/pre-push` that **actively enforces** postflight by invoking
  `enforce_postflight.py` against the hub

Wave 1 would add `.digital-asset-directory.yml` declaring:

```yaml
enforcement: advisory_no_hooks
hooks_enabled: false
rollout:
  wave: 1
```

That is not merely redundant — it **contradicts the enforcing hooks already
installed on `main`**, writing a config that says hooks are off into repos
whose hooks are on and blocking pushes.

For contrast, `orphan-radar` completed **Wave 2** (PR #5, merged 07-14) with
`enforcement: pre_push` and a `load_bearing_decision_review` block gating
high-risk decisions on human review. Wave 1 has neither.

**Close all five as superseded.** If a `.digital-asset-directory.yml` is
still wanted in these repos, generate it fresh at Wave 2 schema — do not
resurrect a Wave 1 branch.

```bash
gh pr close 9  --repo lowelltwong-alt/LawFirm-os-skills-registry         --comment "Superseded by the DAD transport surface v1 work on main (2026-07-08). Wave 1 declares hooks_enabled: false against main's enforcing pre-push hook."
gh pr close 17 --repo lowelltwong-alt/LawFirm-os-orchestrator            --comment "Superseded by the DAD transport surface v1 work on main (2026-07-08)."
gh pr close 9  --repo lowelltwong-alt/LawFirm-os-legal-knowledge-runtime --comment "Superseded by the DAD transport surface v1 work on main (2026-07-08)."
gh pr close 13 --repo lowelltwong-alt/LawFirm-os-semantic-substrate      --comment "Superseded by the DAD transport surface v1 work on main (2026-07-08)."
gh pr close 10 --repo lowelltwong-alt/LawFirm-os-exceptions-lake-runtime --comment "Superseded by the DAD transport surface v1 work on main (2026-07-08)."
```

### Group B — CI manifest refresh: merge these, then regenerate

| PR | Repo | Merge adds |
| --- | --- | --- |
| #10 | LawFirm-os-skills-registry | manifest +130/−84, `contracts.lock.json` |
| #18 | LawFirm-os-orchestrator | manifest **+850/−336** |
| #10 | LawFirm-os-legal-knowledge-runtime | manifest +114/−108 |
| #11 | LawFirm-os-exceptions-lake-runtime | manifest +379/−118 |
| #14 | LawFirm-os-semantic-substrate | manifest, **plus validators and a 60-line test** |

Opposite situation from Group A — here the **branch is newer than `main`**:

| Repo | manifest on `main` | manifest on branch |
| --- | --- | --- |
| skills-registry | 2026-06-29 | 2026-07-01 |
| orchestrator | 2026-06-30 | 2026-07-01 |
| legal-knowledge-runtime | 2026-06-29 | 2026-07-01 |
| exceptions-lake-runtime | 2026-06-30 | 2026-07-01 |
| semantic-substrate | 2026-06-29 | 2026-07-01 |

Merging is a strict improvement over the current state. **But it does not
finish the job:** `main` moved to 2026-07-08 while `ci-test-manifest.json`
has not been regenerated since 06-30, so even post-merge the manifest lags
`main` by roughly a week of commits.

Recommended order: merge **#14 first** (it carries validator changes and
tests, not just a regenerated artifact), then the other four, then
regenerate all five manifests against current `main` and commit the result.

**Unverified:** whether these repos' CI currently passes. They are outside
this session's GitHub API scope, so I could not read their Actions status.
If a validator gates on manifest freshness, `main` may be failing right now —
which would make Group B urgent rather than merely tidy. Check before you
schedule it.

### Not part of the cluster at all

**`LawFirm-os-semantic-substrate` #17** — `codex/fable-chw-substrate`,
17 days old, **+1,227 lines**: an adversity-class registry schema (243
lines), its validator (265 lines), a 141-line test suite, and AI-front-door
integrity tests. This is real feature work that the audit mis-binned as part
of the stale cluster. **Land it.**

**`LawFirm-os-talent-intelligence` #35** — private, unreadable from this
session. Its title matches the Wave 1 pattern exactly, so it is *probably*
the same supersession, but I could not verify it and am not recommending a
close on a guess. Check whether that repo's `main` also received the
2026-07-08 transport-surface work; if yes, close for the same reason.

## Issue triage — 13 open

### Answer this one first

**`logos-doctrine-genealogy` #4 — "Owner decision needed: data-readiness
lane selection"** (20 days). This is the gate holding the repo the archive
decisions said to keep. The issue carries its own recommendation:
DR-OPTION-A for implementation readiness, DR-OPTION-B if source
contamination is the pressing worry.

**DR-OPTION-A is the consistent choice.** The repo's own
`GOVERNANCE_DEPENDENCY_MAP_MIRROR.yaml` sets `authorizes_source_imports:
false`, so Option B's source-intake docket runs against the authority the
repo has declared for itself. Option A — governance schema mirror only —
is exactly the mirror-with-validators role it is registered for. The issue
already contains a ready-to-paste owner prompt for it.

### Close

| Repo | # | Age | Why |
| --- | --- | --- | --- |
| LawFirm-os-skills-registry | 2 | 75d | **Malformed** — the title is a bare URL to its own repo. Close as `not_planned` |
| logos-governance-architecture | 50 | 56d | June's monthly alignment review, superseded by #69 for July |
| kirsten-dissertation-knowledge-graph | 4, 5, 6, 7 | 62d | Four "Cursor task: …" agent scratch tickets, never closed out |

```bash
gh issue close 2 --repo lowelltwong-alt/LawFirm-os-skills-registry --reason not_planned \
  --comment "Malformed issue - title is a bare URL to this repository. Closing as part of the 2026-07-27 account cleanup."
gh issue close 50 --repo lowelltwong-alt/logos-governance-architecture --reason completed \
  --comment "June alignment review superseded by #69 (July)."
for n in 4 5 6 7; do
  gh issue close $n --repo lowelltwong-alt/kirsten-dissertation-knowledge-graph --reason not_planned \
    --comment "Stale Cursor agent task from 2026-05-26. Closing as part of the 2026-07-27 account cleanup."
done
```

### Review, do not bulk-close

Three issues from 2026-05-13 (75 days) predate most of the current
architecture but describe real intent, not scratch work:

- `LawFirm-os-semantic-substrate` #1 — seed contract authority bundle
- `LawFirm-os-exceptions-lake-runtime` #1 — validate-only handoff for
  orchestrator evidence packets
- `LawFirm-os-orchestrator` #3 — local-first classify-exception MVP

Each is either already delivered under a different name or still wanted. A
minute apiece to decide; do not batch-close them with the scratch tickets.

### Keep

`logos-governance-architecture` #54 and `logos-scripture-graph` #7 are a
linked governance-parent / data-plane-child pair, both active. #69 is the
current month's review.

## Net effect

| Action | Count |
| --- | --- |
| PRs to close (superseded) | 5 |
| PRs to merge | 5 + 1 feature |
| PRs needing a private-repo check | 1 |
| Issues to close | 6 |
| Issues to review individually | 3 |
| Issues to answer | 1 (`logos-doctrine-genealogy` #4) |

Open PRs go 15 → 4. Open issues go 13 → 6.
