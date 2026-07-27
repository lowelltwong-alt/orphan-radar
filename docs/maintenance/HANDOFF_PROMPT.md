# Handoff prompt — finish the 2026-07-27 account cleanup

Everything below the line is a self-contained prompt. Paste it into a fresh
Claude Code session (or any capable agent with `gh` access) to execute the
remaining work.

**Why a handoff exists:** the session that produced the analysis had
read-broad/write-narrow credentials — it could read every public repo but was
scoped to write only `lowelltwong-alt/orphan-radar`. Branch deletion, repo
archiving, and cross-repo PR/issue operations all returned 403 or
"repository is not configured for this session". The analysis is complete and
merged; only execution remains.

**Before pasting:** the new session needs write access to these repos.
`orphan-radar` alone is not enough.

| Repo | Needed for |
| --- | --- |
| `LawFirm-os-semantic-substrate` | 2 merges, 1 close, 1 issue review |
| `LawFirm-os-orchestrator` | 1 merge, 1 close, 1 issue review |
| `LawFirm-os-skills-registry` | 1 merge, 1 close, 1 issue close |
| `LawFirm-os-legal-knowledge-runtime` | 1 merge, 1 close |
| `LawFirm-os-exceptions-lake-runtime` | 1 merge, 1 close, 1 issue review |
| `logos-scripture-graph` | tag + retire 7 branches, land up to 13 |
| `logos-governance-architecture` | 1 issue close |
| `logos-doctrine-genealogy` | 1 owner decision to record |
| `kirsten-dissertation-knowledge-graph` | 4 issue closes |
| `LawFirm-Talent-Intel-ATS` + `LawFirm-os-talent-intelligence` | archive precondition check |
| `fmg-fractal-capability-ontology` | archive (owner already approved) |

---

## PROMPT — copy from here

You are finishing a GitHub account cleanup for `lowelltwong-alt`. The analysis
is already done and merged to `main` in the `orphan-radar` repo. **Read these
four documents first — they contain the evidence, the reasoning, and the
rollback criteria for every action below:**

- `docs/maintenance/github-audit-2026-07-27.md` — the 33-repo audit
- `docs/maintenance/github-archive-decisions-2026-07-27.md` — archive calls with premortem/red team
- `docs/maintenance/github-open-pr-and-issue-triage-2026-07-27.md` — PR and issue verdicts
- `docs/maintenance/logos-scripture-graph-branch-triage-2026-07-27.md` — per-branch triage

Do not re-derive the analysis. Do verify state before each destructive step —
these findings are from 2026-07-27 and the account may have moved.

### Governing rule

> `main` is canon. A branch lands only if it carries the newest version of what
> it touches. Older than `main` → close. Newer than `main` → merge.

### Task 1 — Merge 6 PRs

All are **drafts**, so `gh pr merge` alone will refuse. Mark ready first.

Merge #14 **first and on its own** — it carries validator changes and a 60-line
test, not just a regenerated artifact, so it deserves a real review. The other
four change only generated files (`ci-test-manifest.json`, `contracts.lock.json`),
merge cleanly, and no GitHub workflow in any of those repos consumes the
manifest, so nothing turns red on merge day.

```bash
gh pr ready 14 --repo lowelltwong-alt/LawFirm-os-semantic-substrate
gh pr merge 14 --repo lowelltwong-alt/LawFirm-os-semantic-substrate --squash

gh pr ready 18 --repo lowelltwong-alt/LawFirm-os-orchestrator            && gh pr merge 18 --repo lowelltwong-alt/LawFirm-os-orchestrator --squash
gh pr ready 10 --repo lowelltwong-alt/LawFirm-os-skills-registry         && gh pr merge 10 --repo lowelltwong-alt/LawFirm-os-skills-registry --squash
gh pr ready 10 --repo lowelltwong-alt/LawFirm-os-legal-knowledge-runtime && gh pr merge 10 --repo lowelltwong-alt/LawFirm-os-legal-knowledge-runtime --squash
gh pr ready 11 --repo lowelltwong-alt/LawFirm-os-exceptions-lake-runtime && gh pr merge 11 --repo lowelltwong-alt/LawFirm-os-exceptions-lake-runtime --squash
```

Then **review and land** `LawFirm-os-semantic-substrate` #17 — +1,227 lines of
real feature work (adversity-class registry schema, 265-line validator,
141-line test suite). Not part of the stale cluster; give it a proper read.

### Task 2 — Close 5 superseded PRs

The DAD Wave 1 fan-out. Branch tips are 2026-06-30; on 2026-07-08 every one of
these repos' `main` gained a **more advanced** DAD integration
(`dad-integration.json`, the full `.digital-asset/` tree, and a `pre-push` hook
that actively enforces postflight). Wave 1 would write
`enforcement: advisory_no_hooks` / `hooks_enabled: false` into repos whose hooks
are live. **These now conflict** on `AGENTS.md`, `CLAUDE.md`, and the mail
README — `main` holds the newer governance block in exactly the region Wave 1
targets. Superseded *and* conflicting.

```bash
MSG="Superseded by the 2026-07-08 DAD transport surface v1 on main; merge now conflicts on AGENTS.md/CLAUDE.md/mail README, with main holding the newer governance block. If a .digital-asset-directory.yml is still wanted, generate it fresh at Wave 2 schema (enforcement: pre_push, load_bearing_decision_review)."
gh pr close 9  --repo lowelltwong-alt/LawFirm-os-skills-registry         --comment "$MSG"
gh pr close 17 --repo lowelltwong-alt/LawFirm-os-orchestrator            --comment "$MSG"
gh pr close 9  --repo lowelltwong-alt/LawFirm-os-legal-knowledge-runtime --comment "$MSG"
gh pr close 13 --repo lowelltwong-alt/LawFirm-os-semantic-substrate      --comment "$MSG"
gh pr close 10 --repo lowelltwong-alt/LawFirm-os-exceptions-lake-runtime --comment "$MSG"
```

**Also check `LawFirm-os-talent-intelligence` #35.** Private, unreadable from
the prior session. Its title matches Wave 1 exactly. Verify whether that repo's
`main` also received the 2026-07-08 transport-surface work; if yes, close for
the same reason. Do not close on the title match alone.

### Task 3 — Close 6 issues, review 3, answer 1

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

**Review individually — do NOT bulk-close.** These three are 75 days old but
describe real intent, not scratch work. Each is either already delivered under
another name or still wanted:

- `LawFirm-os-semantic-substrate` #1 — seed contract authority bundle
- `LawFirm-os-exceptions-lake-runtime` #1 — validate-only handoff for orchestrator evidence packets
- `LawFirm-os-orchestrator` #3 — local-first classify-exception MVP

**Answer `logos-doctrine-genealogy` #4** — "Owner decision needed:
data-readiness lane selection". This gates a repo the audit decided to keep.
The recommendation is **DR-OPTION-A** (governance schema mirror only), because
the repo's own `GOVERNANCE_DEPENDENCY_MAP_MIRROR.yaml` sets
`authorizes_source_imports: false`, which rules out Option B's source-intake
docket by the repo's own declared authority. The issue already contains a
ready-to-paste owner prompt for Option A. **This is an owner decision — confirm
with the human before posting it.**

### Task 4 — Delete ~30 merged branches account-wide

Use the script on `main` in `orphan-radar`. It re-derives merge status live
rather than trusting the audit table, paginates the open-PR inventory and fails
closed if it cannot fetch it, skips default/protected/open-PR branches, prints a
repo-explicit restore command for every deletion, and exits nonzero on any
failure.

```bash
cd orphan-radar
./scripts/maintenance/gh_branch_cleanup.sh            # DRY RUN — read the plan
./scripts/maintenance/gh_branch_cleanup.sh --apply
```

Run this **after** Tasks 1–2, so branches freed by the merges and closes are
swept in the same pass. It also covers the 17 private repos the prior session
could not read.

### Task 5 — `logos-scripture-graph`, carefully

**The owner has flagged this repo as very important, and stated that recent
branches outrank stale ones. Nothing here is a bare deletion.**

First, make every branch tip permanently recoverable:

```bash
git clone https://github.com/lowelltwong-alt/logos-scripture-graph
cd logos-scripture-graph
for b in $(git for-each-ref --format='%(refname:short)' refs/remotes/origin \
           | grep -v 'origin/main\|origin/HEAD'); do
  git tag "archive/2026-07-27/${b#origin/}" "$b"
done
git push origin --tags
```

Then retire the 7 branches whose every commit is already in `main` by patch-id
(rebase/squash landings that left stale pointers — zero content loss):

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

`codex/t483-restricted-source-catalog` and `codex/t484-predownload-readiness`
point at **byte-identical trees**. Keep `t484` (fuller task scope, includes PR
#173's readiness commit); retire the `t483` name.

**13 branches carry ~21,600 unlanded insertions. Do not delete any of them.**
Land them smallest-first so PRs stay reviewable — full table and rationale in
the triage doc. Expect small conflicts in append-only ledger files
(`.ai/control/handoff_ledger.jsonl`, `PROJECT_STATUS.md`); resolve by keeping
both sides.

1. `codex/t482-sinaiticus-rights-decision` (+147) — rights/permission records that currently exist only on a branch
2. `codex/t484-predownload-readiness` (+362)
3. `codex/llos-v1-scripture-adapter` (+458) — **the one repo missing from an already-shipped four-repo LLOS v1 rollout**; the siblings all landed
4. `codex/t514-external-root-approval` (+471)
5. `codex/t492-theological-research-foundation` (+601)
6. `codex/t498-changed-path-engine` (+1,126) — 437-line engine, 355-line test suite
7. `codex/t479-leipzig-sinaiticus-acquisition` (+2,862) — 753-line IIIF engine, tests, 402-line rights ledger, three review rounds
8. `codex/t500-scripture-first-biblical-chunking-family` (+6,681) — biggest unlanded item; review properly

Leave `preserve/t470-t478-nas-scholarship-mirror` and
`preserve/t516-csntm-rights-gated-campaign` alone — the `preserve/` prefix is
deliberate. `codex/t451-bible-edge-taxonomy-deepening` (+2,056, a complete
923-line edge-taxonomy catalog with **zero presence in `main`**) and
`roster/2026-07` are **owner decisions** — land or tag-retire deliberately, do
not leave them in limbo.

⚠️ Before merging `t500` or `t451`, have a human confirm `main` has not
semantically re-done that work under a different task ID. The prior session
verified what is *on* the branches, not that `main` lacks an equivalent.

### Task 6 — Archive 7 repos

Reversible (`gh repo unarchive`); archived repos stay visible and cloneable,
just read-only.

```bash
cd orphan-radar
./scripts/maintenance/gh_archive_plan.sh            # DRY RUN
./scripts/maintenance/gh_archive_plan.sh --apply    # tier 1, 7 repos
```

Tier 1: `exceptions-lake-runtime`, `obsidian-foundry-vault`, `Bi-Test`,
`All-Law-Firm-Talent-Intel`, `lowell-career-os`, `noesis-atlas`,
`fmg-fractal-capability-ontology` (owner-approved 2026-07-27).

**`LawFirm-Talent-Intel-ATS` is gated on a precondition.** It has 0 PRs and a
25-minute total lifespan (created 07-02 05:05, last push 05:30), which reads as
abandoned — but 1,316 KB arriving in 25 minutes is also exactly what a bulk
import of locally-developed work looks like. **Before archiving, diff its tree
against `LawFirm-os-talent-intelligence`.** If ATS contains top-level
directories the other lacks, stop and reassess. Then:

```bash
./scripts/maintenance/gh_archive_plan.sh --tier 2 --apply
```

**Do NOT archive** `lowelltwong-alt` — it is the profile README repo; archiving
greys out the header on the public GitHub profile. **Keep**
`LawFirm-os-talent-intelligence` (35 PRs, 77 passing tests — it is the survivor
of the talent trio), `airca-fractal-decision-architecture` (the only repo with
an external audience: `CITATION.cff`, public promotion, non-owner stars — add a
README status line instead), and `logos-doctrine-genealogy` (a formally
registered governance child; archiving breaks a mirror its parent requires be
kept fresh).

### Task 7 — Cosmetic

Fix the repo topic typo on `orphan-radar`: **`link-perdiction` →
`link-prediction`**. Settings → topics, or:

```bash
gh repo edit lowelltwong-alt/orphan-radar --remove-topic link-perdiction --add-topic link-prediction
```

### Guardrails

- **Never delete an unmerged branch.** Tag first, always.
- **Verify before destroying.** Re-check state; this analysis is from 2026-07-27.
- **Do not bulk-close the three 75-day issues** — they are real intent.
- **`logos-scripture-graph` is the owner's most important repo.** Recent
  branches outrank stale ones. Preserve everything.
- Owner decisions (`logos-doctrine-genealogy` #4, `t451`, `roster/2026-07`,
  the ATS archive) need human confirmation, not agent judgment.

### Definition of done

Open PRs 15 → 4 (or fewer). Open issues 13 → 6. ~37 branches retired with tags.
7–8 repos archived. `logos-scripture-graph` either landed or tagged, nothing
lost. Report exact outcomes — including anything skipped and why.

## PROMPT — copy to here
