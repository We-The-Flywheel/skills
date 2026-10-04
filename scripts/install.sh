#!/usr/bin/env bash
# Clone-based install (alternative to the plugin marketplace).
# Copies each skill into ~/.claude/skills/ with a `wtf-` prefix so they never
# clash with same-named skills you may already have. Skips anything already
# installed. The plugin marketplace is the recommended path — see README.md.

set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/plugins/wtf/skills"
DEST_ROOT="$HOME/.claude/skills"

SKILLS=(humanizer mission multi-llm visual-qa premortem wrapup end idiocy-check release-gate content-gate og-meta-check moodboard website-build riff grilling skill-test verify-claim review-feedback knowledgepanel improve-codebase-architecture codebase-design tdd domain-modeling axi debug memory-consolidate sop lavish screamingfrog-check video-analyze video-use)

# Skills moved to archive/: archive copies left by earlier installs.
RETIRED=(pangram ultrahumanizer longterm)

mkdir -p "$DEST_ROOT"

for skill in "${RETIRED[@]}"; do
  if [ -d "$DEST_ROOT/wtf-$skill" ]; then
    archive_root="$HOME/.claude/skills-disabled"
    mkdir -p "$archive_root"
    mv "$DEST_ROOT/wtf-$skill" "$archive_root/wtf-$skill-$(date +%s)-$$"
    echo "✗  archived retired skill: wtf-$skill"
  fi
done

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
echo "Invoke them as /wtf-humanizer, /wtf-multi-llm, /wtf-visual-qa, /wtf-premortem."
