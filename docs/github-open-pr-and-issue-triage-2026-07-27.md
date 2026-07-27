# Open PR and issue triage — 2026-07-27

Resolves the last two items from `github-audit-2026-07-27.md`: the 11-PR
"stale draft cluster" and the 13 open issues. Revised after a red-team pass
that overturned one of this document's own claims — see the correction
below before trusting any earlier copy.

## Correction (red team, self-inflicted)

An earlier revision said "all 11 PRs merge cleanly; none conflict." **That
was wrong.** The check captured `merge-tree --write-tree`'s output tree but
not its exit code — and on conflict, merge-tree still writes a tree, with
conflict markers embedded in the files. Re-run with exit codes:

- **All five DAD Wave 1 PRs CONFLICT**, identically, on `AGENTS.md`,
  `CLAUDE.md`, and `.digital-asset/mail/README.md`.
- All five CI-manifest PRs are genuinely clean.
- `semantic-substrate` #17 (`fable-chw-substrate`) is genuinely clean.

The conflict content is itself evidence: inside `AGENTS.md`, `main`'s side
of the conflict is a **newer** DAD governance block ("Digital Asset
Directory enrollment contract", enrollment IDs, preflight trace IDs) sitting
exactly where Wave 1 wants to write its **older** block ("learning and mail
pointer", `Wave: 1`, "Hooks are not enabled by this Wave 1 install"). The
branches aren't just stale — merging them would ask a human to hand-resolve
a newer contract against its own predecessor.

## The decision, unified

The owner flagged the two-verdict outcome (close five, merge five) as a
mess. It isn't two rules — it's one rule applied to branches on opposite
sides of `main` in time:

> **`main` is canon. A branch lands only if it carries the newest version
> of what it touches. Older-than-main → close. Newer-than-main → land.**

| | DAD Wave 1 (5 PRs) | CI manifest (5 PRs) |
| --- | --- | --- |
| Branch content dated | 2026-06-30 | 2026-07-01 |
| `main`'s version dated | **2026-07-08** (transport surface v1) | 2026-06-29/30 |
| Branch vs `main` | older | **newer** |
| Merge result | conflicts (3 files × 5 repos) | clean |
| Verdict | **CLOSE** | **MERGE** |

### Premortem — how each verdict fails, and the mitigation

**Closing Wave 1 was wrong if…** the DAD hub tooling specifically requires
a `.digital-asset-directory.yml` pointer file, which these five repos lack
(`orphan-radar`'s Wave 2 has one; the LawFirm-os five instead carry the
07-08 `dad-integration.json`). The hub is a local Windows directory this
session cannot inspect, so this is unverifiable from here. *Mitigation:*
if the yml is needed, generate it fresh at Wave 2 schema
(`enforcement: pre_push`, `load_bearing_decision_review`) — a small task —
rather than resurrecting a branch that writes `hooks_enabled: false` into
repos whose `pre-push` hook is live and enforcing. Closing a PR also
deletes nothing: the branches and their content remain until the branch
cleanup runs, and the closed PRs preserve the diffs forever.

**Merging the manifests was wrong if…** `ci-test-manifest.json` is a
generated artifact whose 07-01 snapshot embeds test lists that drifted
again by 07-08 — merging would then install a manifest that is newer than
`main`'s but still stale, and local tooling that trusts it could misreport.
*Two findings bound this risk.* First, **no GitHub workflow in any of the
five repos references the manifest** (verified across every workflow file
on every `main`) — it feeds local tooling, so nothing turns red on merge
day. Second, no generator script exists in any of the repos, so
"regenerate instead of merging" is not an available command — these codex
branches *are* the regeneration, and the only one there is. Merging the
newest available snapshot, then regenerating when the tooling that produces
it next runs, strictly dominates both alternatives (close-and-keep-06-29,
or hand-edit).

### Red team — strongest case against each verdict

*Against closing Wave 1:* "The five repos never got a Wave 2 install —
orphan-radar did. You're closing the only DAD-pointer work these repos
have." Answer: they got something newer than Wave 1 — the 07-08 transport
surface (`dad-integration.json`, enforcing hooks, managed-path allowlist),
which is why the merge conflicts. The gap, if any, is a missing *yml
format*, not missing *DAD integration* — and the premortem mitigation
covers it.

*Against merging the manifests:* "You're batch-merging five drafts nobody
reviewed." Answer: four of the five change exactly two generated files
(`ci-test-manifest.json`, `contracts.lock.json`) with clean merges and no
CI consumer; blast radius is local tooling accuracy, which the merge
*improves* from a 06-29 snapshot to a 07-01 one. The fifth (#14) touches
validators and adds a 60-line test — it gets individual review, merged
first, not batched.

### Rollback criteria

- Wave 1 closes: reopen the PR (one click); branches untouched until the
  separate cleanup pass, which tags before deleting.
- Manifest merges: each is a 1–2 file merge commit; `git revert -m 1` on
  any repo independently restores its 06-29 state.
- Trigger for rollback: DAD hub preflight/postflight starts erroring on the
  five repos (Wave 1 case), or local test tooling misreports against the
  merged manifest (Group B case).

## Execution order

```bash
# 1. Merge semantic-substrate #14 after a normal review (validators + test, not just data)
gh pr ready 14 --repo lowelltwong-alt/LawFirm-os-semantic-substrate
gh pr merge 14 --repo lowelltwong-alt/LawFirm-os-semantic-substrate --squash

# 2. Merge the four pure manifest refreshes
gh pr ready 18 --repo lowelltwong-alt/LawFirm-os-orchestrator            && gh pr merge 18 --repo lowelltwong-alt/LawFirm-os-orchestrator --squash
gh pr ready 10 --repo lowelltwong-alt/LawFirm-os-skills-registry         && gh pr merge 10 --repo lowelltwong-alt/LawFirm-os-skills-registry --squash
gh pr ready 10 --repo lowelltwong-alt/LawFirm-os-legal-knowledge-runtime && gh pr merge 10 --repo lowelltwong-alt/LawFirm-os-legal-knowledge-runtime --squash
gh pr ready 11 --repo lowelltwong-alt/LawFirm-os-exceptions-lake-runtime && gh pr merge 11 --repo lowelltwong-alt/LawFirm-os-exceptions-lake-runtime --squash

# 3. Close the five Wave 1 PRs as superseded-and-conflicting
gh pr close 9  --repo lowelltwong-alt/LawFirm-os-skills-registry         --comment "Superseded by the 2026-07-08 DAD transport surface v1 on main; merge now conflicts on AGENTS.md/CLAUDE.md/mail README, with main holding the newer governance block. If a .digital-asset-directory.yml is still wanted, generate it fresh at Wave 2 schema."
gh pr close 17 --repo lowelltwong-alt/LawFirm-os-orchestrator            --comment "Superseded by the 2026-07-08 DAD transport surface v1 on main; merge conflicts with the newer governance block."
gh pr close 9  --repo lowelltwong-alt/LawFirm-os-legal-knowledge-runtime --comment "Superseded by the 2026-07-08 DAD transport surface v1 on main; merge conflicts with the newer governance block."
gh pr close 13 --repo lowelltwong-alt/LawFirm-os-semantic-substrate      --comment "Superseded by the 2026-07-08 DAD transport surface v1 on main; merge conflicts with the newer governance block."
gh pr close 10 --repo lowelltwong-alt/LawFirm-os-exceptions-lake-runtime --comment "Superseded by the 2026-07-08 DAD transport surface v1 on main; merge conflicts with the newer governance block."

# 4. Review and land the real feature work
gh pr ready 17 --repo lowelltwong-alt/LawFirm-os-semantic-substrate   # +1,227 lines: adversity-class registry + validator + tests

# 5. Then re-run the branch cleanup script -- the closed PRs' branches become
#    deletable on its next pass (it skips open-PR branches only).
```

**`LawFirm-os-talent-intelligence` #35** (private, unreadable here): title
matches Wave 1 exactly. Verify its `main` also received the 07-08 transport
surface; if yes, close for the same reason. Not recommending action on a
guess.

## Issue triage — 13 open

### Answer this one first

**`logos-doctrine-genealogy` #4 — "Owner decision needed: data-readiness
lane selection"** (20 days). This gates the repo the archive decisions kept.
**DR-OPTION-A** is the consistent choice: the repo's own
`GOVERNANCE_DEPENDENCY_MAP_MIRROR.yaml` sets
`authorizes_source_imports: false`, which rules out Option B's source-intake
docket by the repo's own declared authority. The issue already contains a
ready-to-paste owner prompt for Option A.

### Close (6)

| Repo | # | Age | Why |
| --- | --- | --- | --- |
| LawFirm-os-skills-registry | 2 | 75d | Malformed — title is a bare URL to its own repo |
| logos-governance-architecture | 50 | 56d | June's monthly review, superseded by #69 |
| kirsten-dissertation-knowledge-graph | 4–7 | 62d | Four "Cursor task:" agent scratch tickets |

```bash
gh issue close 2 --repo lowelltwong-alt/LawFirm-os-skills-registry --reason not_planned \
  --comment "Malformed issue - title is a bare URL to this repository. 2026-07-27 cleanup."
gh issue close 50 --repo lowelltwong-alt/logos-governance-architecture --reason completed \
  --comment "June alignment review superseded by #69 (July)."
for n in 4 5 6 7; do
  gh issue close $n --repo lowelltwong-alt/kirsten-dissertation-knowledge-graph --reason not_planned \
    --comment "Stale Cursor agent task from 2026-05-26. 2026-07-27 cleanup."
done
```

### Review individually (3) — real intent, not scratch

- `LawFirm-os-semantic-substrate` #1 — seed contract authority bundle (75d)
- `LawFirm-os-exceptions-lake-runtime` #1 — validate-only handoff (75d)
- `LawFirm-os-orchestrator` #3 — classify-exception MVP (75d)

Each is either delivered under another name or still wanted; a minute
apiece, not a batch close.

### Keep (4)

`logos-governance-architecture` #54 + `logos-scripture-graph` #7 (linked
parent/child pair), #69 (current month), `logos-doctrine-genealogy` #4
until answered.

## Net effect

Open PRs 15 → 4 · Open issues 13 → 6.
