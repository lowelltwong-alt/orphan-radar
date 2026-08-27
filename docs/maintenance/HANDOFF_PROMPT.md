# Historical account-maintenance decision handoff — 2026-07-27

## Status and scope

This is a dated, read-only handoff for the four July 2026 maintenance records
listed below. They preserve historical audit evidence, reasoning, and rollback
considerations. Their repository counts, branch state, pull-request and issue
verdicts, archive recommendations, and ownership assumptions are stale and
non-authorizing.

- `github-audit-2026-07-27.md`
- `github-archive-decisions-2026-07-27.md`
- `github-open-pr-and-issue-triage-2026-07-27.md`
- `logos-scripture-graph-branch-triage-2026-07-27.md`

Do not treat those records as a command list, current inventory, approval, or
substitute for independent review. Do not skip current-state discovery because
a historical record appears decisive.

## Required fresh process

Any current pull-request portfolio work must begin with a fresh, read-only
inventory through the existing `cross-repo-pr-queue`, then route each pull
request through `pr-lifecycle-router` and an independent
`pr-review-merge-gate`. Do not create a second queue from this handoff.

For each pull request, record its current repository, number, base and head
SHA, draft and review state, required checks, branch protection, dependencies,
and verification time. PROCESS and MERGE authority are separate, immutable,
per-pull-request records; a changed SHA, base, checks, reviews, protection, or
dependency state invalidates them. A historical recommendation never grants
authority to mark ready, merge, close, update, or otherwise mutate a pull
request.

Repository archival, branch retirement, issue closure, topic changes, and any
other external mutation likewise require fresh state, an exact target set,
explicit human authority, and a recorded rollback or recovery path. A failed
or incomplete inventory is a stop condition, not permission to rely on the
July records.

## Historical zero-loss review criteria

Use the following only as review criteria while building a fresh, authorized
decision record:

- Never retire an unmerged branch.
- Before an authorized branch retirement, confirm recoverability, the exact
  remote reference, and a tested restoration path.
- Treat protected repositories and deliberately preserved branches as
  non-routine decisions requiring their current owner and policy gates.
- Do not bulk-close issues merely because they are old; review stated intent
  and current delivery evidence independently.
- Treat archive recommendations as reversible only after current dependency,
  visibility, ownership, and open-work checks have passed.

## Handoff outcome

The four July records remain available for provenance and comparison. They do
not authorize execution. The next actor should create a fresh, permission-gated
portfolio docket and report unknowns or conflicting evidence to the human
owner before any mutation.
