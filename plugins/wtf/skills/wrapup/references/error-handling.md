# Error Handling

Moved verbatim from `SKILL.md`; read at the step that points here.

## Error Handling

- **Not a git repo**: skip all git operations; still do cleanup and PROJECT_MAP.md
- **Merge in progress**: apply Step 1 ownership checks; report the affected delivery as incomplete until resolved
- **Detached HEAD**: apply Step 1 ownership checks; preserve commits and report any unresolved delivery
- **Commit, push, merge, deploy or cleanup fails**: fix within scope; otherwise report the exact blocker and mark closure incomplete
- **PROJECT_MAP.md generation fails**: use basic fallback template
- **CLAUDE.md update fails**: warn; PROJECT_MAP.md still created
- **CHANGELOG.md missing**: informational note only (non-blocking)
- **Find command fails**: skip cleanup, warn, proceed
- **Not on macOS**: skip .DS_Store cleanup silently
- **`lsof` unavailable or server kill fails**: warn, skip server detection, proceed — never block exit on a failed shutdown
