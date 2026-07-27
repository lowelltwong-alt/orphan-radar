# Tier-2 archive decisions — premortem and red team

Companion to `github-audit-2026-07-27.md`, which left four decisions open.
Each is resolved below with evidence, a premortem, a red team against my own
recommendation, rollback criteria, and a confidence level.

**Rollback for every recommendation here:** `gh repo unarchive lowelltwong-alt/<name>`.
Archiving is reversible and lossless — issues, PRs, stars, and history survive, the
repo stays cloneable, and the only effects are a read-only period and an "Archived"
badge. Nothing below deletes anything.

## Correction to the audit

The audit listed `LawFirm-os-talent-intelligence` as the archive candidate in the
talent pair. The evidence says the opposite — it is the survivor. Corrected below.

## Finding that reframes three of the four

Four repos (`airca-fractal-decision-architecture`, `fmg-fractal-capability-ontology`,
`lowelltwong-alt`, `noesis-atlas`) all show last activity on or near 2026-06-03. That
is not four projects stopping at once. Their final commits are:

- airca — `docs(integrations): add Shannon information theory and decision capacity (#2)`
- lowelltwong-alt — `docs(ai): add Shannon information theory for AI governance (#1)`
- noesis-atlas — `docs(architecture): harden Shannon note (F2 + F3) (#2)`
- fmg — `docs: add Shannon information-theory capability-routing note (#44)`

This was one cross-cutting documentation sweep applied to the whole portfolio
(`orphan-radar` PR #1, 2026-05-29, is the same thread). **The 06-03 timestamp
overstates how alive these repos are.** Real last substantive work:

| Repo | Last push | Last *substantive* work |
| --- | --- | --- |
| airca | 2026-06-03 | 2026-05-07 (PR #1), core work 2026-04-10 |
| noesis-atlas | 2026-05-29 | 2026-05-27 |
| fmg | 2026-06-03 | before 2026-06-03 |

## 1. Talent repos — keep `LawFirm-os-talent-intelligence`

**Recommendation: keep `LawFirm-os-talent-intelligence`. Archive `LawFirm-Talent-Intel-ATS`
and `All-Law-Firm-Talent-Intel`.**

| Repo | PRs | Size | Lifespan | Signal |
| --- | --- | --- | --- | --- |
| `LawFirm-os-talent-intelligence` | **35** | 949 KB | 06-18 → 07-01 | 77 passing tests, `src/` layout, `LawFirm-os-*` family prefix |
| `LawFirm-Talent-Intel-ATS` | **0** | 1316 KB | 07-02 05:05 → 05:30 | **25 minutes total, then nothing** |
| `All-Law-Firm-Talent-Intel` | **0** | 4336 KB | 06-16 → 06-23 | no detected language — data, not code |

`-talent-intelligence` is the only one with a development history. Its PR #35 body
records `77 passed` against a real source layout. ATS existed for 25 minutes.

**Premortem — six months on, archiving ATS was wrong.** ATS was a deliberate
greenfield restart carrying an applicant-tracking integration that
`-talent-intelligence` never had, and the 25-minute window was a bulk import of
work developed locally for weeks. 1316 KB arriving in 25 minutes with no PRs is
genuinely consistent with that. **This is the one real risk in this document.**

**Mitigation (do this before executing):** diff the two trees. If ATS's `main`
contains top-level directories absent from `-talent-intelligence`, stop and
reassess. Two minutes of work; I could not do it because both repos are private
and unreadable from this session.

**Premortem — archiving `All-Law-Firm-Talent-Intel` was wrong.** It is 4.3 MB of
data that the other repos consume as a corpus. Archiving does not break reads —
archived repos still clone — and nothing has written to it since 06-23. Low risk.

**Red team.** *"PR count is a bad proxy; this owner pushes straight to main."*
True — the profile repo shows `Add files via upload` direct commits, so 0 PRs is
not 0 work. But ATS's entire existence was 25 minutes; even direct-push work
outlasts that unless it is an import. *"The `LawFirm-os-*` prefix is weak
evidence."* Fair on its own; it is corroborating, not load-bearing. *"You cannot
read any of the three."* Correct, and it is the honest limit here.

**Confidence:** high on `All-Law-Firm-Talent-Intel`, **medium on ATS** — gated on
the tree diff.

## 2. `fmg-fractal-capability-ontology` — archive, after one check

**Recommendation: archive, conditional on a supersession check.**

44 PRs and real ontology work — AUTHORITY_MAP, control plane, capability router,
trust zones, `canon_status`. Not a scratch repo. But its final PR was the Shannon
docs sweep, so substantive work stopped before 2026-06-03, and its whole
vocabulary now lives in two active families: `LawFirm-os-semantic-substrate`
(control plane, governance) and `logos-governance-architecture` (authority map,
registry, trust zone, canon status). It reads as the conceptual ancestor of both.

**Check before executing:** confirm its core ontology terms exist in one of those
two repos. If they do, archive with a forwarding line in the README. If they do
not, this is an orphaned asset that should be revived or explicitly retired —
not quietly archived.

**Premortem.** It held the only copy of a capability taxonomy the LawFirm-os
control plane assumed but never re-encoded. Someone needs the capability-router
spec and finds a read-only repo. Direct cost is near zero — unarchive. The real
cost is subtler: if future agent preflight skips archived repos, that taxonomy
silently drops out of context for every later decision.

**Red team.** *"You are recommending archiving a 44-PR repo you have never
read."* Correct, and this is the weakest recommendation in this document. The
supersession claim rests on vocabulary overlap visible only through PR titles and
bodies. That is suggestive, not proof. *"Dormancy is not supersession."* Agreed —
which is why the check is a precondition rather than a nicety.

**Confidence: medium-low.** Do not execute this one blind.

**Owner decision 2026-07-27: retire it.** The owner approved archiving without
the supersession check; that decision supersedes the precondition above. The
repo is private, so archiving has no public-facing effect. Moved to tier 1 in
`gh_archive_plan.sh`. Rollback remains one command:
`gh repo unarchive lowelltwong-alt/fmg-fractal-capability-ontology`.

## 3. `airca-fractal-decision-architecture` — do not archive

**Recommendation: keep. Add a status line to the README instead.** This reverses
the audit's lean.

This is the only repo in the account with an **external audience**:

- `CITATION.cff` — v0.1.0, released 2026-03-27, explicitly inviting citation
- `reddit-post-v1.md` — it was publicly promoted
- 2 stars, 2 watchers — the only non-owner attention in the account
- a working Python package, CLI, SHACL validation, schemas, and applied pilots
- a `ROADMAP.md` with real exit criteria

It is also **not coupled to Logos governance**. It is absent from
`LOGOS_REPO_REGISTRY.yaml`; the `airca` hits inside `logos-governance-architecture`
are `docs/lairca/**`, which inventory entry LCOI-009 marks
`disposition: retain_as_governance_architecture` — retained *there*, not here. The
2026-04-05 commits ("Clarify AIRCA secular-business scope and direct doctrinal
adaptation to Logos project") record a deliberate split. Archiving it breaks
nothing technical.

The case rests on signal, not dependencies. Archiving broadcasts "abandoned" to
people who cited or starred it, and this is a dormant-but-*complete* artifact,
not an abandoned scaffold. A README status line — "v0.1.0, stable, not under
active development" — buys the same honesty at none of the cost.

**Premortem — keeping it was wrong.** It sits another year, someone opens an
issue expecting support, it reads as stale. Cost: one unanswered issue.

**Premortem — archiving it was wrong.** A citer reads "Archived" as retracted;
the CITATION invitation becomes awkward; and the single strongest piece of public
work in the account is greyed out precisely when it would be useful to point an
employer or collaborator at it. Higher cost, and harder to notice.

**Red team.** *"Two stars is not an audience."* Possibly self-star plus a bot. But
`CITATION.cff` and a Reddit post are a stated *intent* to have an audience, and
nothing has revoked it. *"You are just reluctant to archive public repos."* Checked:
`noesis-atlas` is public and I still recommend archiving it — 6 commits, no
citation, no package, no promotion. The distinction is external-facing artifact
versus public scaffold, not public versus private.

**Note:** `feat/make-airca-usable` is on the merged-branch delete list *and* is a
trigger branch in `.github/workflows/airca-publish.yml`. Deleting it is safe —
`main` is also a trigger — but drop the stale reference from the workflow.

**Confidence: high.**

## 4. `logos-doctrine-genealogy` — do not archive, not a close call

**Recommendation: remove from the archive list entirely. Answer issue #4.**

It is a **formally registered child** of `logos-governance-architecture`:

- registration issue #83, with a recorded owner acceptance comment
- decision record `FABLE-D1-D10-2026-07-06`
- `UPSTREAM_GOVERNANCE_CONTRACT.md` and `GOVERNANCE_DEPENDENCY_MAP_MIRROR.yaml`,
  both `lifecycle_status: active`, `trust_zone: active_scaffold`
- referenced from the parent in `LOGOS_REPO_REGISTRY.yaml`/`.md`,
  `CROSS_REPO_REFERENCE_MANIFEST.yaml`, `GOVERNANCE_DEPENDENCY_MAP.yaml`,
  `REPOSITORY_LINK_CONTRACTS.md`, `LLOS_ROUTE_REGISTRY.yaml`, and
  `FUTURE_FIVE_REPO_ARCHITECTURE.md`
- the parent holds the source `schemas/doctrine_genealogy/*` that this repo mirrors
- 12 validator scripts including `validate_mirror_freshness.py`, with CI

The parent's own registry policy states
`child_repos_must_validate_governance_dependency_map_mirror: true` and
`relationship_change_updates_registry_first_or_same_pr: true`.

It is not dormant — 16 days idle, the newest of the four. It is **gated**, waiting
on owner decision issue #4, "data-readiness lane selection", which picks one of
DR-OPTION-A/B/C/D from `docs/roadmap/data-readiness-decision-packet.md`. The
action is to answer that issue, not to archive the repo.

**Premortem.** Archiving freezes a mirror the parent requires be kept fresh;
`validate_mirror_freshness.py` and the parent's child-mirror gate go red; and
un-archiving cleanly means re-running the registration flow, because the
relationship change never went through the registry as policy requires.
Self-inflicted and moderate.

**Red team.** *"8 commits is nothing — you are over-weighting ceremony."* Commit
count is the wrong metric for a governance mirror: it is 40+ files of schemas,
validators, and contracts, plus CI, in those 8 commits. *"Maybe the whole child-repo
scheme is over-engineered and should collapse."* Genuinely possible — but that is a
far bigger decision than archiving one repo, and by the parent's own policy it
routes through the registry, not through a cleanup sweep.

**Confidence: high.**

## Summary

| # | Repo | Recommendation | Confidence |
| --- | --- | --- | --- |
| 1 | `LawFirm-os-talent-intelligence` | **keep** — the survivor | high |
| 1 | `LawFirm-Talent-Intel-ATS` | archive — *diff trees first* | medium |
| 1 | `All-Law-Firm-Talent-Intel` | archive | high |
| 2 | `fmg-fractal-capability-ontology` | archive — *check supersession first* | medium-low |
| 3 | `airca-fractal-decision-architecture` | **keep** + README status line | high |
| 4 | `logos-doctrine-genealogy` | **keep** — answer issue #4 | high |

Net: tier 1 is now 7 repos (fmg moved in by owner decision 2026-07-27);
`LawFirm-Talent-Intel-ATS` remains gated on its tree diff, for **8 total
archives**, and three keeps are confirmed.

**Fresh-eyes review flag:** the two medium-confidence calls (ATS, fmg) rest
entirely on metadata for repos this session could not read. Both carry a
precondition. Do not batch them with the high-confidence archives.
