# logos-scripture-graph branch triage — 2026-07-27

Owner guidance applied: **this repo is very important, and recent branches
outrank stale ones.** Accordingly: nothing here recommends bare deletion.
Every retirement goes through a tag first (zero-loss), the newest branches
lead the keep/land list, and anything ambiguous is marked *owner decides*.

Method: for each of the 21 non-default branches, every commit not on `main`
was compared by **patch-id** (catches rebase/squash-equivalent landings that
ancestry checks miss), then the surviving branches were diffed three-dot
against `main` to measure exactly what merging would add. Cross-branch
containment was checked the same way.

## Headline numbers

| Class | Branches | Meaning |
| --- | --- | --- |
| Zero unique content | 7 | every commit already in `main` by patch-id — retire-safe |
| Duplicate tree | 1 | `t483` and `t484` point at **byte-identical trees** — one name is redundant |
| Unlanded real work | 13 | ~21,600 insertions not on `main`, incl. two task IDs with **zero** presence in `main` |

The surprise: this repo's branch pile is not mostly junk. It is mostly
**unlanded work**, and the newest branches carry the most substance — the
recency rule and the evidence point the same way.

## Safety net first (run before anything else)

Tags make every branch tip permanently reachable, so later deletions can
never lose anything:

```bash
git clone https://github.com/lowelltwong-alt/logos-scripture-graph
cd logos-scripture-graph
for b in $(git for-each-ref --format='%(refname:short)' refs/remotes/origin \
           | grep -v 'origin/main\|origin/HEAD'); do
  git tag "archive/2026-07-27/${b#origin/}" "$b"
done
git push origin --tags
```

## Tier A — retire now (7 branches, zero loss)

Every commit on each of these is patch-identical to a commit already on
`main` (they were rebased or squashed in, then the branch pointer was left
behind). Deleting the pointer loses nothing; the tag from the safety net
keeps even the pointer recoverable.

| Branch | Last commit | Landed as |
| --- | --- | --- |
| `codex/t497-fable-architecture-owner-decisions` | 07-13 | in `main` |
| `codex/t495-doctrine-genealogy-governance-handoff` | 07-12 | in `main` |
| `codex/t494-theological-edge-taxonomy-research` | 07-12 | in `main` |
| `codex/t493-patristics-boundary-intake-plan` | 07-12 | in `main` |
| `codex/t485-postmerge-scope-repair` | 07-11 | in `main` |
| `codex/transport-spool-cutover` | 07-11 | in `main` |
| `cursor/src-pilot-a-t469-wave0` | 07-11 | in `main` |

```bash
for b in codex/t497-fable-architecture-owner-decisions \
         codex/t495-doctrine-genealogy-governance-handoff \
         codex/t494-theological-edge-taxonomy-research \
         codex/t493-patristics-boundary-intake-plan \
         codex/t485-postmerge-scope-repair \
         codex/transport-spool-cutover \
         cursor/src-pilot-a-t469-wave0; do
  git push origin --delete "$b"
done
```

## The duplicate — `t483` ≡ `t484`

`codex/t483-restricted-source-catalog` and `codex/t484-predownload-readiness`
resolve to **the same tree** (`git rev-parse <branch>^{tree}` matches).
Whatever you decide for one applies to both; keep the `t484` name (the more
complete task scope, and it includes PR #173's readiness commit) and retire
the `t483` name after tagging.

## Tier B — unlanded work, newest first (owner's recency rule)

None of these should be deleted. The decision per branch is **land it**
(open a PR / merge) or **tag-and-retire** (accept the work is not wanted,
keep it reachable via tag). My recommendation per row:

| Branch | Last | Adds vs `main` | What it is | Recommendation |
| --- | --- | --- | --- | --- |
| `preserve/t470-t478-nas-scholarship-mirror` | 07-20 | 82 files, +5,897 | NAS scholarship mirror records; named `preserve/` on purpose | **Keep as-is** — explicit archival intent |
| `preserve/t516-csntm-rights-gated-campaign` | 07-20 | 10 files, +723 | CSNTM rights-gated campaign: task, handoff, roadmap. **T516 has zero files in `main`** | **Keep as-is**, or land if the campaign is live |
| `codex/t479-leipzig-sinaiticus-acquisition` | 07-18 | 22 files, +2,862 | Leipzig Sinaiticus IIIF acquisition: 753-line engine, PowerShell adapter, witness specs, 103-line test file, 402-line rights ledger | **Land.** Working code + rights records, 3 review rounds on the branch |
| `codex/t514-external-root-approval` | 07-18 | 15 files, +471 | External-asset-root + pre-download validators with tests | **Land** — small, tested, validator-plane |
| `codex/t500-scripture-first-biblical-chunking-family` | 07-15 | 93 files, +6,681 | The chunking-family schema set: packets, releases, fixtures, 206-line test | **Land or decide** — biggest single unlanded item in the repo |
| `codex/t498-changed-path-engine` | 07-13 | 13 files, +1,126 | 437-line `changed_paths.py`, JSON schema, 355-line test suite, golden fixtures | **Land** — engine + tests, self-contained |
| `codex/t492-theological-research-foundation` | 07-12 | 13 files, +601 | Research-foundation validator + tests + roadmap doc | **Land** — small, tested |
| `codex/llos-v1-scripture-adapter` | 07-11 | 13 files, +458 | Scripture-side LLOS v1 adapter + 199-line validator. Note: the LLOS v1 branches in `logos-governance-architecture`, `logos-boundary-literature`, and `logos-doctrine-genealogy` all **landed** (squash-merged) — this is the **missing repo** in that cross-repo rollout | **Land** — completes an already-shipped rollout |
| `codex/t484-predownload-readiness` (≡ t483) | 07-11 | 11 files, +362 | Wave-4 restricted-source catalog + W1–W4 readiness (incl. PR #173 commit) | **Land**; retire the `t483` name |
| `codex/t482-sinaiticus-rights-decision` | 07-11 | 6 files, +147 | Sinaiticus rights decision, permission queue (Vatican/Israel/CSNTM routes) | **Land** — rights/permission records should not live only on a branch |
| `codex/t451-bible-edge-taxonomy-deepening` | 07-05 | 16 files, +2,056 | 923-line Bible edge candidate-type catalog + validators + tests. **T451 has zero files in `main`** | **Owner decides.** Oldest codex branch (recency rule says lower priority), but it is a complete, tested catalog absent from `main` — land it or tag-retire it deliberately, don't leave it in limbo |
| `roster/2026-07` | 07-04 | 2 files, +110 | July 2026 model-roster review doc | **Owner decides** — land as historical record before the month closes, or tag-retire |

### Suggested landing order

Small-and-tested first, big-decision last:

1. `t482` (+147) → 2. `t484` (+362) → 3. `llos-v1-scripture-adapter` (+458)
→ 4. `t514` (+471) → 5. `t492` (+601) → 6. `t498` (+1,126)
→ 7. `t479` (+2,862) → 8. `t500` (+6,681, review properly)
→ then decide `t451` and `roster/2026-07`.

Each branch is only 1–6 commits ahead, so PRs will be clean; expect small
conflicts in shared ledger files (`.ai/control/handoff_ledger.jsonl`,
`PROJECT_STATUS.md`) since `main` moved 36–128 commits past these
merge-bases — the JSONL ledgers are append-only, so conflicts resolve by
keeping both sides.

```bash
# open a PR per land-candidate (repeat per branch)
gh pr create --repo lowelltwong-alt/logos-scripture-graph \
  --base main --head codex/t482-sinaiticus-rights-decision \
  --title "Land T482: Sinaiticus rights decision and permission routes" \
  --body "Landing unmerged branch work identified in the 2026-07-27 triage."
```

## What was NOT checked

- Whether `main`'s later commits *semantically* supersede any branch (e.g.
  if a task was re-done differently on `main` under another ID). `main`
  carries partial artifacts (ledger/status entries) for most of these task
  IDs, which reads as "task registered, work unlanded" — but a human who
  knows the roadmap should confirm for `t500` and `t451` before merging.
- The two `preserve/*` branches' contents were inventoried but their
  retention policy is taken at face value from the naming convention.
