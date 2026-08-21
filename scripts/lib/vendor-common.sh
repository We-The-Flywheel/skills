#!/usr/bin/env bash
# Shared helpers for scripts/vendor-sync.sh and scripts/vendor-verify.sh.
# Source this file; it is not meant to be executed directly.
#
# Conventions:
#   - all functions read/write a scratch git dir per source (a real .git dir
#     with no working tree checkout, populated via shallow fetches of
#     specific refs -- HEAD and/or a pinned SHA), so pinned_sha..HEAD diffs
#     work without a full clone or shared ancestry.
#   - all functions take vendor.json's path explicitly rather than assuming
#     a global, so both callers can pass their own resolved path.

vendor_sha256() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    shasum -a 256 "$1" | awk '{print $1}'
  fi
}

# vendor_fetch_ref <repo-url> <ref> <scratch-gitdir>
# Shallow-fetches <ref> (a full 40-char SHA, or "HEAD" for the default
# branch) from <repo-url> into <scratch-gitdir>, creating/reusing a bare-ish
# git dir there. Objects from earlier fetches into the same dir are kept, so
# calling this twice with two different refs against the same dir leaves
# both commits available for diffing even though neither is an ancestor of
# the other's fetch. Prints the resolved SHA on success; returns non-zero
# and prints nothing on fetch failure (e.g. ref no longer reachable after an
# upstream force-push, or a short SHA -- GitHub only allows fetch-by-SHA for
# full 40-char SHAs).
vendor_fetch_ref() {
  local repo_url="$1" ref="$2" gitdir="$3"
  if [ ! -d "$gitdir/.git" ]; then
    mkdir -p "$gitdir"
    git -C "$gitdir" init -q
    git -C "$gitdir" remote add origin "$repo_url"
  fi
  git -C "$gitdir" fetch -q --depth 1 origin "$ref" || return 1
  git -C "$gitdir" rev-parse FETCH_HEAD
}

# vendor_path_type <gitdir> <sha> <path>
# Prints "blob", "tree", or nothing (path missing at that sha).
vendor_path_type() {
  git -C "$1" cat-file -t "$2:$3" 2>/dev/null
}

# vendor_diff_stat <gitdir> <sha_a> <sha_b> <path>
vendor_diff_stat() {
  git -C "$1" diff --stat "$2" "$3" -- "$4" 2>/dev/null
}

# vendor_diff_full <gitdir> <sha_a> <sha_b> <path>
vendor_diff_full() {
  git -C "$1" diff "$2" "$3" -- "$4" 2>/dev/null
}

# vendor_file_hash_at <gitdir> <sha> <path>
# Hashes a single blob's content at <sha>:<path>. Prints nothing (and
# returns non-zero) if the path isn't a blob at that sha.
vendor_file_hash_at() {
  local gitdir="$1" sha="$2" path="$3"
  local type
  type=$(vendor_path_type "$gitdir" "$sha" "$path") || return 1
  [ "$type" = "blob" ] || return 1
  git -C "$gitdir" show "$sha:$path" | { command -v sha256sum >/dev/null 2>&1 && sha256sum || shasum -a 256; } | awk '{print $1}'
}

# vendor_extract_path <gitdir> <sha> <path> <dest_dir>
# Extracts the blob or tree at <sha>:<path> into <dest_dir>, normalized so
# the caller never has to think about the upstream path prefix:
#   - a file path yields <dest_dir>/<basename-of-path>
#   - a directory path yields its *contents* directly under <dest_dir>
#     (not nested under the upstream path)
# Best-effort for deeply-nested directory paths (flattens by removing the
# first path segment of the archived tree) -- fine for the flat/one-level
# upstream layouts this repo has vendored from so far; revisit if a future
# adoption needs a deeper upstream_path.
vendor_extract_path() {
  local gitdir="$1" sha="$2" path="$3" dest="$4"
  mkdir -p "$dest"
  local type
  type=$(vendor_path_type "$gitdir" "$sha" "$path") || return 1
  if [ "$type" = "blob" ]; then
    git -C "$gitdir" show "$sha:$path" > "$dest/$(basename "$path")"
  elif [ "$type" = "tree" ]; then
    git -C "$gitdir" archive "$sha" -- "$path" | tar -x -C "$dest"
    if [ -d "$dest/$path" ]; then
      local top="${path%%/*}"
      ( cd "$dest/$path" && tar -cf - . ) | tar -xf - -C "$dest"
      rm -rf "${dest:?}/${top}"
    fi
  else
    return 1
  fi
}

# vendor_skill_field <vendor.json> <skill-name> <field>
vendor_skill_field() {
  jq -r --arg n "$2" --arg f "$3" '.skills[] | select(.name == $n) | .[$f] // empty' "$1"
}

# vendor_source_field <vendor.json> <source-id> <field>
vendor_source_field() {
  jq -r --arg s "$2" --arg f "$3" '.sources[$s][$f] // empty' "$1"
}
