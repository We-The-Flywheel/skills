#!/usr/bin/env bash
# Clone-based install (alternative to the plugin marketplace).
# Copies each skill into ~/.claude/skills/ with a `wtf-` prefix so they never
# clash with same-named skills you may already have. Skips anything already
# installed. The plugin marketplace is the recommended path — see README.md.

set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/plugins/wtf/skills"
DEST_ROOT="$HOME/.claude/skills"

SKILLS=(humanizer multi-llm-deliberation visual-qa premortem end idiocy-check release-gate content-gate moodboard website-build)

mkdir -p "$DEST_ROOT"

for skill in "${SKILLS[@]}"; do
  src="$SRC_DIR/$skill"
  dest="$DEST_ROOT/wtf-$skill"

  if [ ! -d "$src" ]; then
    echo "⚠️  source missing, skipping: $src"
    continue
  fi
  if [ -e "$dest" ]; then
    echo "↷  skip (already installed): wtf-$skill"
    continue
  fi

  cp -R "$src" "$dest"

  # Make the prefixed name real: rewrite the first `name:` line in SKILL.md.
  skfile="$dest/SKILL.md"
  if [ -f "$skfile" ]; then
    awk -v n="wtf-$skill" '
      BEGIN { done = 0 }
      /^name:/ && !done { print "name: " n; done = 1; next }
      { print }
    ' "$skfile" > "$skfile.tmp" && mv "$skfile.tmp" "$skfile"
  fi

  echo "✓ installed: wtf-$skill"
done

echo
echo "Done. Restart Claude Code (fresh terminal window) to pick up new skills."
echo "Invoke them as /wtf-humanizer, /wtf-multi-llm-deliberation, /wtf-visual-qa, /wtf-premortem."
