#!/usr/bin/env bash
# Vendor-sync: keep track of skills copied in from third-party repos.
#
# Manifest-driven, not git subtree/submodule (submodules are already
# forbidden by CONTRIBUTING.md; subtree merges upstream history wholesale,
# which fights scrub-check and can't cleanly cherry-pick one skill directory
# out of a larger upstream repo). This script only reports and stages --
# it never commits or pushes on its own. See vendor.json for the manifest
# schema and DECISIONS.md / the vendor-sync plan for the full design.
#
# Usage:
#   scripts/vendor-sync.sh [check]                        (default)
#   scripts/vendor-sync.sh pull <skill-name>
#   scripts/vendor-sync.sh adopt <source-id> <upstream-path> <skill-name>

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
# shellcheck source=lib/vendor-common.sh
source "$REPO_ROOT/scripts/lib/vendor-common.sh"

VENDOR_JSON="$REPO_ROOT/vendor.json"
SKILLS_DIR="$REPO_ROOT/plugins/wtf/skills"

if ! command -v jq >/dev/null 2>&1; then
  echo "❌ jq is required (brew install jq)." >&2
  exit 1
fi

# ---------------------------------------------------------------- check ---

cmd_check() {
  local scratch
  scratch="$(mktemp -d)"
  trap 'rm -rf "$scratch"' EXIT

  local total=0 drifted=0 license_drift_count=0

  echo "== vendor-sync check -- $(date +%Y-%m-%d) =="
  echo

  local src
  for src in $(jq -r '.sources | keys[]' "$VENDOR_JSON"); do
    local repo_url expected_hash gitdir head_sha
    repo_url=$(vendor_source_field "$VENDOR_JSON" "$src" repo)
    expected_hash=$(vendor_source_field "$VENDOR_JSON" "$src" license_file_hash)
    gitdir="$scratch/$src"

    echo "-- source: $src ($repo_url)"

    if ! head_sha=$(vendor_fetch_ref "$repo_url" "HEAD" "$gitdir" 2>/dev/null); then
      echo "   !! failed to fetch $repo_url -- skipping this source"
      echo
      continue
    fi
    echo "   upstream HEAD: $head_sha"

    local actual_hash
    if actual_hash=$(vendor_file_hash_at "$gitdir" "$head_sha" "LICENSE" 2>/dev/null) && [ -n "$actual_hash" ]; then
      if [ "$actual_hash" != "$expected_hash" ]; then
        echo "   !!!!!! LICENSE DRIFT for $src !!!!!!"
        echo "       recorded: $expected_hash"
        echo "       actual:   $actual_hash"
        license_drift_count=$((license_drift_count + 1))
      else
        echo "   license OK (sha256 matches vendor.json)"
      fi
    else
      echo "   ?? could not read LICENSE at upstream HEAD -- skipping license check for this source"
    fi

    local name
    for name in $(jq -r --arg s "$src" '.skills[] | select(.source == $s) | .name' "$VENDOR_JSON"); do
      total=$((total + 1))
      local pinned upath
      pinned=$(vendor_skill_field "$VENDOR_JSON" "$name" pinned_sha)
      upath=$(vendor_skill_field "$VENDOR_JSON" "$name" upstream_path)

      if [ -z "$(vendor_path_type "$gitdir" "$head_sha" "$upath")" ]; then
        echo "   [$name] path_missing: '$upath' not found at upstream HEAD"
        continue
      fi

      if ! vendor_fetch_ref "$repo_url" "$pinned" "$gitdir" >/dev/null 2>&1; then
        echo "   [$name] could not fetch pinned_sha $pinned -- cannot diff (force-pushed upstream?)"
        continue
      fi

      local diffstat
      diffstat=$(vendor_diff_stat "$gitdir" "$pinned" "$head_sha" "$upath")
      if [ -n "$diffstat" ]; then
        drifted=$((drifted + 1))
        echo "   [$name] upstream changes since pinned $pinned:"
        echo "$diffstat" | sed 's/^/       /'
      else
        echo "   [$name] clean (matches pinned $pinned)"
      fi
    done
    echo
  done

  echo "== summary =="
  echo "$drifted/$total vendored skills have upstream changes; $license_drift_count sources have license drift."
  exit 0
}

# ----------------------------------------------------------------- pull ---

# Runs scrub-check.sh against the *whole repo* with the candidate files
# already copied into the real target path (scrub-check.sh only supports
# whole-repo scans, confirmed by reading it -- no path-scoping flag). On
# failure this reverts the target path with `git checkout --`, so nothing
# is left changed in the working tree. Only safe to call when the target
# path had no pre-existing uncommitted changes (checked by the caller).
_scrub_or_revert() {
  local target="$1"
  echo "-- running scrub-check.sh against the whole repo --"
  if "$REPO_ROOT/scripts/scrub-check.sh"; then
    return 0
  else
    echo "❌ scrub-check FAILED -- reverting $target"
    git -C "$REPO_ROOT" checkout -- "$target" 2>/dev/null || true
    return 1
  fi
}

cmd_pull() {
  local name="${1:-}"
  if [ -z "$name" ]; then
    echo "Usage: vendor-sync.sh pull <skill-name>" >&2
    exit 1
  fi

  if [ -z "$(jq -r --arg n "$name" '.skills[] | select(.name == $n) | .name' "$VENDOR_JSON")" ]; then
    echo "❌ '$name' is not in vendor.json's skills list." >&2
    exit 1
  fi

  local source pinned upath local_mods
  source=$(vendor_skill_field "$VENDOR_JSON" "$name" source)
  pinned=$(vendor_skill_field "$VENDOR_JSON" "$name" pinned_sha)
  upath=$(vendor_skill_field "$VENDOR_JSON" "$name" upstream_path)
  local_mods=$(vendor_skill_field "$VENDOR_JSON" "$name" local_modifications)

  local repo_url
  repo_url=$(vendor_source_field "$VENDOR_JSON" "$source" repo)

  local scratch gitdir
  scratch="$(mktemp -d)"
  trap 'rm -rf "$scratch"' EXIT
  gitdir="$scratch/src"

  local head_sha
  head_sha=$(vendor_fetch_ref "$repo_url" "HEAD" "$gitdir") || { echo "❌ could not fetch $repo_url"; exit 1; }
  echo "upstream HEAD for $source: $head_sha"

  if [ -z "$(vendor_path_type "$gitdir" "$head_sha" "$upath")" ]; then
    echo "❌ path_missing: '$upath' no longer exists at upstream HEAD -- nothing pulled."
    exit 1
  fi

  vendor_fetch_ref "$repo_url" "$pinned" "$gitdir" >/dev/null 2>&1 || {
    echo "❌ could not fetch pinned_sha $pinned -- cannot compute the upstream delta."
    exit 1
  }

  if [ "$local_mods" = "true" ]; then
    echo "'$name' has local_modifications: true -- refusing to blind-copy."
    echo "Manual merge required. Upstream delta since pinned $pinned:"
    echo
    vendor_diff_full "$gitdir" "$pinned" "$head_sha" "$upath"
    echo
    echo "Apply the parts you want by hand into plugins/wtf/skills/$name/,"
    echo "then update pinned_sha/last_synced in vendor.json yourself."
    exit 0
  fi

  local target="plugins/wtf/skills/$name"
  if [ ! -d "$REPO_ROOT/$target" ]; then
    echo "❌ $target does not exist locally -- use 'adopt' for first-time imports." >&2
    exit 1
  fi
  if [ -n "$(git -C "$REPO_ROOT" status --porcelain -- "$target")" ]; then
    echo "❌ $target has uncommitted changes -- commit or stash them first (pull's rollback path uses 'git checkout --' on failure, which would discard them)." >&2
    exit 1
  fi

  echo "-- copying $source:$upath @ $head_sha into $target --"
  vendor_extract_path "$gitdir" "$head_sha" "$upath" "$scratch/extracted"
  cp -R "$scratch/extracted/." "$REPO_ROOT/$target/"

  if ! _scrub_or_revert "$target"; then
    exit 1
  fi

  local today
  today=$(date +%Y-%m-%d)
  local tmp
  tmp="$(mktemp)"
  jq --arg n "$name" --arg sha "$head_sha" --arg d "$today" \
    '(.skills[] | select(.name == $n) | .pinned_sha) = $sha
     | (.skills[] | select(.name == $n) | .last_synced) = $d' \
    "$VENDOR_JSON" > "$tmp" && mv "$tmp" "$VENDOR_JSON"

  echo "✅ pulled '$name' -- pinned_sha updated to $head_sha ($today)."
  echo "Now run: review diff && bump version (plugin.json + marketplace.json + README)."
}

# ---------------------------------------------------------------- adopt ---

cmd_adopt() {
  local source="${1:-}" upath="${2:-}" name="${3:-}"
  if [ -z "$source" ] || [ -z "$upath" ] || [ -z "$name" ]; then
    echo "Usage: vendor-sync.sh adopt <source-id> <upstream-path> <skill-name>" >&2
    exit 1
  fi

  if [ -z "$(jq -r --arg s "$source" '.sources[$s] // empty' "$VENDOR_JSON")" ]; then
    echo "❌ source '$source' is not in vendor.json's sources map. Add it first." >&2
    exit 1
  fi
  if [ -n "$(jq -r --arg n "$name" '.skills[] | select(.name == $n) | .name' "$VENDOR_JSON")" ]; then
    echo "❌ '$name' is already in vendor.json -- use 'pull' instead." >&2
    exit 1
  fi
  local target="plugins/wtf/skills/$name"
  if [ -e "$REPO_ROOT/$target" ]; then
    echo "❌ $target already exists -- pick a different name or use 'pull'." >&2
    exit 1
  fi

  local repo_url
  repo_url=$(vendor_source_field "$VENDOR_JSON" "$source" repo)

  local scratch gitdir
  scratch="$(mktemp -d)"
  trap 'rm -rf "$scratch"' EXIT
  gitdir="$scratch/src"

  local head_sha
  head_sha=$(vendor_fetch_ref "$repo_url" "HEAD" "$gitdir") || { echo "❌ could not fetch $repo_url"; exit 1; }
  echo "upstream HEAD for $source: $head_sha"

  if [ -z "$(vendor_path_type "$gitdir" "$head_sha" "$upath")" ]; then
    echo "❌ path_missing: '$upath' does not exist at upstream HEAD -- nothing adopted."
    exit 1
  fi

  echo "-- copying $source:$upath @ $head_sha into $target (new) --"
  mkdir -p "$REPO_ROOT/$target"
  vendor_extract_path "$gitdir" "$head_sha" "$upath" "$scratch/extracted"
  cp -R "$scratch/extracted/." "$REPO_ROOT/$target/"

  echo "-- running scrub-check.sh against the whole repo --"
  if ! "$REPO_ROOT/scripts/scrub-check.sh"; then
    echo "❌ scrub-check FAILED -- removing untracked $target"
    rm -rf "${REPO_ROOT:?}/$target"
    exit 1
  fi

  local today
  today=$(date +%Y-%m-%d)
  local tmp
  tmp="$(mktemp)"
  jq --arg n "$name" --arg s "$source" --arg up "$upath" --arg sha "$head_sha" --arg d "$today" \
    '.skills += [{
       "name": $n, "source": $s, "upstream_path": $up,
       "pinned_sha": $sha, "last_synced": $d, "local_modifications": false
     }]' \
    "$VENDOR_JSON" > "$tmp" && mv "$tmp" "$VENDOR_JSON"

  {
    echo
    echo "-------------------------------------------------------------------------------"
    echo "skills/$name"
    echo "-------------------------------------------------------------------------------"
    echo "Derived from \"$upath\" in $repo_url (pinned at $head_sha)."
    echo "  Source:  $repo_url"
    echo "  License: $(vendor_source_field "$VENDOR_JSON" "$source" license)"
  } >> "$REPO_ROOT/NOTICE"

  echo "✅ adopted '$name' from $source:$upath -- vendor.json and NOTICE updated."
  echo
  echo "Now: add to README.md skill table, add '$name' to scripts/install.sh SKILLS array,"
  echo "bump version in plugins/wtf/.claude-plugin/plugin.json and .claude-plugin/marketplace.json,"
  echo "then commit."
}

# ----------------------------------------------------------------- main ---

cmd="${1:-check}"
case "$cmd" in
  check)
    cmd_check
    ;;
  pull)
    shift
    cmd_pull "$@"
    ;;
  adopt)
    shift
    cmd_adopt "$@"
    ;;
  *)
    echo "Usage: $(basename "$0") [check|pull <skill-name>|adopt <source-id> <upstream-path> <skill-name>]" >&2
    exit 1
    ;;
esac
