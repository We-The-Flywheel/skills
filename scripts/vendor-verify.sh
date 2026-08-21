#!/usr/bin/env bash
# CI drift guard: fails the build if a manifest-tracked skill's local files
# no longer match what upstream looked like at its pinned_sha, unless the
# skill is flagged local_modifications: true. Catches someone hand-editing
# a vendored skill without going through vendor-sync.sh (or without setting
# the flag to say so intentionally).
#
# Unlike `vendor-sync.sh check` (which diffs pinned_sha..upstream-HEAD, i.e.
# "is there a newer version upstream?"), this diffs local-files..pinned_sha
# (i.e. "does our copy still match what we last pulled?"). Shares fetch/diff
# plumbing with vendor-sync.sh via scripts/lib/vendor-common.sh.
#
# Usage: scripts/vendor-verify.sh
# Exit 0: no unflagged drift. Exit 1: drift found (or a hard error).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
# shellcheck source=lib/vendor-common.sh
source "$REPO_ROOT/scripts/lib/vendor-common.sh"

VENDOR_JSON="$REPO_ROOT/vendor.json"

if ! command -v jq >/dev/null 2>&1; then
  echo "❌ jq is required (brew install jq)." >&2
  exit 1
fi

scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT

drift_found=0

echo "== vendor-verify -- $(date +%Y-%m-%d) =="
echo

for name in $(jq -r '.skills[].name' "$VENDOR_JSON"); do
  local_mods=$(vendor_skill_field "$VENDOR_JSON" "$name" local_modifications)
  if [ "$local_mods" = "true" ]; then
    echo "[$name] skipped (local_modifications: true)"
    continue
  fi

  source=$(vendor_skill_field "$VENDOR_JSON" "$name" source)
  pinned=$(vendor_skill_field "$VENDOR_JSON" "$name" pinned_sha)
  upath=$(vendor_skill_field "$VENDOR_JSON" "$name" upstream_path)
  repo_url=$(vendor_source_field "$VENDOR_JSON" "$source" repo)
  gitdir="$scratch/$source"

  if ! vendor_fetch_ref "$repo_url" "$pinned" "$gitdir" >/dev/null 2>&1; then
    echo "[$name] ❌ could not fetch pinned_sha $pinned from $repo_url -- treating as failure"
    drift_found=1
    continue
  fi

  pinned_copy="$scratch/pinned-$name"
  if ! vendor_extract_path "$gitdir" "$pinned" "$upath" "$pinned_copy"; then
    echo "[$name] ❌ could not extract '$upath' at pinned $pinned -- treating as failure"
    drift_found=1
    continue
  fi

  # Compare each file that upstream had at the pin against the local copy.
  # We only check files that exist in the pinned upstream snapshot -- local
  # files with no upstream counterpart (README.md alongside a vendored
  # SKILL.md, say) are out of scope for this pin and intentionally ignored.
  local_dir="$REPO_ROOT/plugins/wtf/skills/$name"
  mismatch=""
  while IFS= read -r -d '' f; do
    rel="${f#"$pinned_copy"/}"
    if [ ! -f "$local_dir/$rel" ] || ! diff -q "$f" "$local_dir/$rel" >/dev/null 2>&1; then
      mismatch="$mismatch $rel"
    fi
  done < <(find "$pinned_copy" -type f -print0)

  if [ -n "$mismatch" ]; then
    echo "[$name] ❌ DRIFT: local files differ from upstream at pinned $pinned, and local_modifications is not true:"
    for rel in $mismatch; do
      echo "       $rel"
    done
    drift_found=1
  else
    echo "[$name] OK (matches pinned $pinned)"
  fi
done

echo
if [ "$drift_found" -ne 0 ]; then
  echo "❌ vendor-verify FAILED -- unflagged drift found. Either re-run"
  echo "   'vendor-sync.sh pull <skill>' to re-pin, or set local_modifications:"
  echo "   true in vendor.json if the change was intentional."
  exit 1
fi

echo "✅ vendor-verify passed -- no unflagged drift."
exit 0
