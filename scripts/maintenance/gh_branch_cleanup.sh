#!/usr/bin/env bash
# Delete merged branches across every repo owned by $OWNER.
#
# Safe by default: prints the plan and changes nothing until you pass --apply.
#
#   ./scripts/maintenance/gh_branch_cleanup.sh              # dry run, all repos
#   ./scripts/maintenance/gh_branch_cleanup.sh --apply      # actually delete
#   ./scripts/maintenance/gh_branch_cleanup.sh --repo orphan-radar --apply
#
# Requires: gh (authenticated with `repo` scope), jq.
#
# A branch is deleted only when GitHub itself reports it as fully contained in
# the default branch:
#   * compare status "identical" or "behind"  -> ancestor merge / fast-forward
#   * an associated pull request in state MERGED -> squash or rebase merge
# Anything else is left alone and reported as UNMERGED.
#
# The default branch, protected branches, and any branch with an OPEN pull
# request are never deleted.

set -uo pipefail

OWNER="${OWNER:-lowelltwong-alt}"
APPLY=0
ONLY_REPO=""

while [ $# -gt 0 ]; do
  case "$1" in
    --apply) APPLY=1 ;;
    --repo) ONLY_REPO="${2:?--repo needs a name}"; shift ;;
    --owner) OWNER="${2:?--owner needs a name}"; shift ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done

command -v gh >/dev/null || { echo "gh CLI not found" >&2; exit 1; }
command -v jq >/dev/null || { echo "jq not found" >&2; exit 1; }

[ "$APPLY" -eq 1 ] || echo "== DRY RUN == (re-run with --apply to delete)"
echo

deleted=0; kept=0; skipped=0; failed=0; skipped_repos=0

if [ -n "$ONLY_REPO" ]; then
  repos="$ONLY_REPO"
else
  repos=$(gh repo list "$OWNER" --limit 500 --no-archived \
            --json name --jq '.[].name' | sort)
fi

for repo in $repos; do
  meta=$(gh api "repos/$OWNER/$repo" 2>/dev/null) || { echo "!! cannot read $repo"; continue; }
  default=$(jq -r .default_branch <<<"$meta")

  # Branch names that currently have an OPEN PR -- never touch these.
  # Paginated, and fail closed: if this inventory cannot be fetched in full,
  # skip the entire repository rather than risk deleting an open-PR branch
  # that a partial or empty listing failed to protect.
  if ! open_heads=$(gh api "repos/$OWNER/$repo/pulls?state=open&per_page=100" \
                      --paginate --jq '.[].head.ref' 2>/dev/null | sort -u); then
    echo "!! cannot list open PRs for $repo -- skipping repo (fail closed)"
    skipped_repos=$((skipped_repos+1)); continue
  fi

  branches=$(gh api "repos/$OWNER/$repo/branches?per_page=100" --paginate \
               --jq '.[] | select(.protected|not) | .name' 2>/dev/null)

  header_shown=0
  for br in $branches; do
    [ "$br" = "$default" ] && continue
    if grep -qxF "$br" <<<"$open_heads"; then
      skipped=$((skipped+1)); continue
    fi

    sha=$(gh api "repos/$OWNER/$repo/git/ref/heads/$br" --jq .object.sha 2>/dev/null) || continue

    status=$(gh api "repos/$OWNER/$repo/compare/$default...$sha" --jq .status 2>/dev/null)
    reason=""
    case "$status" in
      identical|behind) reason="ancestor of $default" ;;
      *)
        # Squash/rebase merges leave the branch "diverged"; trust a MERGED PR.
        merged_pr=$(gh api "repos/$OWNER/$repo/commits/$sha/pulls" \
                      --jq '[.[] | select(.state=="closed" and .merged_at!=null) | .number] | first' \
                      2>/dev/null)
        [ -n "$merged_pr" ] && [ "$merged_pr" != "null" ] && reason="squash/rebase-merged via PR #$merged_pr"
        ;;
    esac

    if [ -z "$reason" ]; then
      kept=$((kept+1)); continue
    fi

    if [ "$header_shown" -eq 0 ]; then echo "### $repo (default: $default)"; header_shown=1; fi
    printf '  %-52s %s  [%s]\n' "$br" "${sha:0:8}" "$reason"

    if [ "$APPLY" -eq 1 ]; then
      if gh api -X DELETE "repos/$OWNER/$repo/git/refs/heads/$br" >/dev/null 2>&1; then
        # Restore via the create-ref API: works from any directory, names the
        # repo explicitly, and needs no local copy of the commit.
        echo "      deleted (restore: gh api -X POST repos/$OWNER/$repo/git/refs -f ref=refs/heads/$br -f sha=$sha)"
        deleted=$((deleted+1))
      else
        echo "      FAILED to delete"
        failed=$((failed+1))
      fi
    else
      deleted=$((deleted+1))
    fi
  done
  [ "$header_shown" -eq 1 ] && echo
done

echo "-----"
if [ "$APPLY" -eq 1 ]; then echo "deleted:        $deleted"; else echo "would delete:   $deleted"; fi
echo "left (unmerged): $kept"
echo "skipped (open PR): $skipped"
[ "$skipped_repos" -gt 0 ] && echo "repos skipped (PR inventory unavailable): $skipped_repos"
if [ "$failed" -gt 0 ] || [ "$skipped_repos" -gt 0 ]; then
  echo "INCOMPLETE: $failed deletion(s) failed, $skipped_repos repo(s) skipped -- rerun after fixing"
  exit 1
fi
