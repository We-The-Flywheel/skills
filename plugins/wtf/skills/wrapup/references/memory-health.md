# Step 6: memory health check

Moved verbatim from `SKILL.md`; read at the step that points here.

**After learnings are codified, check memory health** (skip if the project has no memory store). Memories accumulate forever unless pruned. The trigger is a *judgment*, not a raw count:

```bash
# NOTE: pwd's leading "/" already becomes the leading "-" via sed — do NOT add an
# extra "-" prefix (that produces a double-dash dir that doesn't exist on disk).
MEM_DIR="$HOME/.claude/projects/$(pwd | sed 's|/|-|g')/memory"
MEM_COUNT=$(find "$MEM_DIR" -maxdepth 1 -name '*.md' -not -name 'MEMORY.md' 2>/dev/null | wc -l | tr -d ' ')
MEM_RECENT=$(find "$MEM_DIR" -maxdepth 1 -name '*.md' -not -name 'MEMORY.md' -mtime -7 2>/dev/null | wc -l | tr -d ' ')
if [ -f "$MEM_DIR/.last-consolidated" ]; then
  LAST=$(cat "$MEM_DIR/.last-consolidated")
  DAYS_SINCE=$(( ( $(date +%s) - $(date -j -f %Y-%m-%dT%H:%M:%SZ "$LAST" +%s 2>/dev/null || date -d "$LAST" +%s 2>/dev/null || echo 0) ) / 86400 ))
else
  DAYS_SINCE="never"
fi
```

Apply this judgment (treat `never` as "long overdue"):

| Situation | Action |
|-----------|--------|
| `MEM_COUNT` < 15 | Skip silently — too little to consolidate |
| Consolidated in the last ~3 days (`DAYS_SINCE` ≤ 3) | Skip silently — even at high count |
| 15–25 entries, some recent churn, not consolidated recently | Inline note: "ℹ️ Memory has $MEM_COUNT entries ($MEM_RECENT added this week, last consolidated ${DAYS_SINCE}d ago) — consider consolidating soon" |
| > 25 entries AND (`DAYS_SINCE` ≥ 7 or `never`) | Inline note + consolidate now (use a `/memory-consolidate`-style skill if you have one, else do it inline: ground claims against the codebase, prune stale entries, deduplicate) |

If borderline (high count but consolidated 4–6 days ago, little churn), prefer the note over auto-running. This pairs with the learnings dedup gate: that prevents new duplicates at write time, this prunes accumulated decay at session end.
