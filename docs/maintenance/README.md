# Maintenance records

Account-level GitHub maintenance artifacts, kept separate from Orphan Radar's
product documentation (which lives one level up in `docs/`).

These records were produced during the 2026-07-27 account cleanup and are kept
for provenance: what was decided, on what evidence, and how to undo it.

| Document | Contents |
| --- | --- |
| [`github-audit-2026-07-27.md`](github-audit-2026-07-27.md) | Full account audit: 33 repos, branch merge-state analysis, open-PR/issue inventory, archive tiers |
| [`github-archive-decisions-2026-07-27.md`](github-archive-decisions-2026-07-27.md) | The four contested archive decisions, each with premortem, red team, rollback criteria, and confidence |
| [`github-open-pr-and-issue-triage-2026-07-27.md`](github-open-pr-and-issue-triage-2026-07-27.md) | Verdicts on all 15 open PRs and 13 open issues, unified under a single rule after a red-team pass |
| [`logos-scripture-graph-branch-triage-2026-07-27.md`](logos-scripture-graph-branch-triage-2026-07-27.md) | Per-branch triage of all 21 non-default branches in `logos-scripture-graph`, patch-id evidence, zero-loss retirement plan |
| [`HANDOFF_PROMPT.md`](HANDOFF_PROMPT.md) | Dated read-only handoff for the July records; requires a fresh, permission-gated portfolio docket before any action. |

The operational utilities live in [`scripts/maintenance/`](../../scripts/maintenance/):

- `gh_branch_cleanup.sh` — deletes merged branches account-wide (dry-run by default)
- `gh_archive_plan.sh` — applies the archive tiers (dry-run by default)

Both require an authenticated `gh` CLI and re-derive state live rather than
trusting the documents above. Their presence does not grant authority for an
external mutation; use the current repository and portfolio governance gates.
