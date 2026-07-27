#!/usr/bin/env bash
# Apply the archive recommendations from docs/maintenance/github-audit-2026-07-27.md.
#
#   ./scripts/maintenance/gh_archive_plan.sh            # dry run, show what would change
#   ./scripts/maintenance/gh_archive_plan.sh --apply    # archive the tier-1 repos
#   ./scripts/maintenance/gh_archive_plan.sh --tier 2 --apply
#
# Archiving is reversible: `gh repo unarchive OWNER/NAME` restores write access.
# An archived repo stays visible and cloneable; it just becomes read-only.
#
# Tier 2 is deliberately NOT run by default -- each entry needs an owner
# decision first (see the audit doc). Nothing here deletes a repository.

set -uo pipefail

OWNER="${OWNER:-lowelltwong-alt}"
APPLY=0
TIER=1

while [ $# -gt 0 ]; do
  case "$1" in
    --apply) APPLY=1 ;;
    --tier) TIER="${2:?--tier needs 1 or 2}"; shift ;;
    --owner) OWNER="${2:?--owner needs a name}"; shift ;;
    -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done

command -v gh >/dev/null || { echo "gh CLI not found" >&2; exit 1; }

# Tier 1 -- superseded, abandoned, or scratch. Safe to archive now.
TIER1="
exceptions-lake-runtime|superseded by LawFirm-os-exceptions-lake-runtime; idle 87d
obsidian-foundry-vault|10 KB stub, first and last push same day; idle 68d
Bi-Test|scratch/test repo; idle 41d
All-Law-Firm-Talent-Intel|superseded by the two newer talent repos; idle 34d
lowell-career-os|23 KB personal scratch; idle 54d
noesis-atlas|6-commit public scaffold, no development since; idle 59d
fmg-fractal-capability-ontology|private; vocabulary superseded by semantic-substrate + logos-governance-architecture; owner approved retirement 2026-07-27
"

# Tier 2 -- resolved in docs/maintenance/github-archive-decisions-2026-07-27.md.
# Remaining entry has a PRECONDITION. Do not batch it with tier 1.
#   KEEP (removed from this list): LawFirm-os-talent-intelligence,
#   airca-fractal-decision-architecture, logos-doctrine-genealogy
#   MOVED to tier 1: fmg-fractal-capability-ontology (owner approved 2026-07-27)
TIER2="
LawFirm-Talent-Intel-ATS|0 PRs, 25-minute lifespan -- PRECONDITION: diff its tree against LawFirm-os-talent-intelligence first
"

case "$TIER" in
  1) LIST="$TIER1" ;;
  2) LIST="$TIER2" ;;
  *) echo "--tier must be 1 or 2" >&2; exit 2 ;;
esac

[ "$APPLY" -eq 1 ] || echo "== DRY RUN == (re-run with --apply)"
echo "Tier $TIER archive plan for $OWNER:"
echo

n=0; ok=0; failed=0
while IFS='|' read -r name why; do
  [ -z "$name" ] && continue
  state=$(gh api "repos/$OWNER/$name" --jq 'if .archived then "already-archived" else "active" end' 2>/dev/null) \
    || { printf '  %-42s !! cannot read\n' "$name"; failed=$((failed+1)); continue; }

  if [ "$state" = "already-archived" ]; then
    printf '  %-42s already archived, skipping\n' "$name"
    continue
  fi

  printf '  %-42s %s\n' "$name" "$why"
  n=$((n+1))

  if [ "$APPLY" -eq 1 ]; then
    if gh repo archive "$OWNER/$name" --yes >/dev/null 2>&1; then
      echo "      archived (undo: gh repo unarchive $OWNER/$name)"
      ok=$((ok+1))
    else
      echo "      FAILED to archive"
      failed=$((failed+1))
    fi
  fi
done <<<"$LIST"

echo
if [ "$APPLY" -eq 1 ]; then
  echo "archived: $ok of $n planned"
else
  echo "would archive: $n"
fi
if [ "$failed" -gt 0 ]; then
  echo "INCOMPLETE: $failed repo(s) failed or unreadable -- rerun after fixing auth/rate limits"
  exit 1
fi

# Never archive: lowelltwong-alt -- that is the GitHub profile README repo.
# Archiving it greys out the profile header on your public profile page.
