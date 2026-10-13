# Manual Mode

Moved verbatim from `SKILL.md`; read at the step that points here.

## Manual Mode (Escape Hatch)

`/wrapup manual` restores interactive behavior:
- Step 3: still auto-remove .DS_Store/.bak, but announce counts; ask before shutting down any dev server
- Step 9: ask "Commit these changes?" instead of auto-committing
- Step 10: ask "Push commits?" instead of auto-pushing
- Step 10b: ask "Merge [branch] into [base]?" instead of auto-merging
- Steps 10c–10d: ask before deployment and branch/worktree removal; run read-only verification regardless
- Step 7: ask "Update PROJECT_MAP.md?" instead of auto-generating

All other steps work the same as default mode.
