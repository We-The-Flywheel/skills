---
name: end
description: |
  Wrap up a coding session cleanly: shut down local dev servers, remove temp/backup
  files, commit and push outstanding work, and refresh project docs (PROJECT_MAP.md +
  CLAUDE.md). Use when the user says "end", "/end", "wrap up", "end the session",
  "finish up", "we're done for today", or wants a safe shutdown that saves work,
  frees ports, and leaves the repo and working tree in a clean, documented state.
  Accepts optional args: manual (interactive prompts), skip-map (don't touch docs),
  skip-cleanup (no temp/server cleanup), keep-servers (cleanup but leave servers up),
  force (summary only, no processing).
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

End-of-session cleanup and verification with intelligent automation. Ensures work is properly saved and documented before exiting.

> **Note:** This skill orchestrates a few optional helpers (a `/ship`-style commit
> workflow, a learnings/memory step, a session-handoff file). Where one isn't
> installed, fall back to the plain-git equivalent described inline — the skill never
> hard-depends on tooling you don't have.

## Arguments

$ARGUMENTS

## Pre-Computed Context

**Branch:** $(git branch --show-current 2>/dev/null || echo "detached")
**Status:** $(git status --short 2>/dev/null | head -15)
**Unpushed:** $(git log --oneline @{upstream}..HEAD 2>/dev/null || echo "none")
**Last commit:** $(git log -1 --format="%h %s (%ar)" 2>/dev/null || echo "none")

- `manual` - Use interactive prompts for commits (old behavior)
- `skip-map` - Don't update PROJECT_MAP.md or CLAUDE.md
- `skip-cleanup` - Skip temp file cleanup AND local server shutdown
- `keep-servers` - Run cleanup but leave local dev servers running
- `force` - Exit immediately without processing (shows summary only)

**Default behavior (no arguments):**
- Shut down local dev servers this session started (silent)
- Auto-remove .DS_Store on macOS (silent)
- Auto-remove .bak backup files on all platforms (silent)
- Auto-commit via /ship skill
- Auto-push to remote
- Generate/update PROJECT_MAP.md (comprehensive details)
- Update CLAUDE.md with essential 20-line context

## Workflow

### 1. **Parse Arguments and Detect Environment**

Check arguments provided and detect the current environment:

```bash
# Detect OS
OS=$(uname -s)

# Detect git repo
IS_GIT=$(git rev-parse --git-dir 2>/dev/null && echo "yes" || echo "no")

# Detect merge in progress
IS_MERGE=$(git status 2>/dev/null | grep -q "merge" && echo "yes" || echo "no")

# Detect detached HEAD
IS_DETACHED=$(git symbolic-ref -q HEAD || echo "detached")
```

**If `force` argument:**
- Skip all processing
- Jump directly to session summary (Step 8)
- Exit immediately

**If merge in progress or detached HEAD:**
- Warn user about state
- Skip auto-commit operations
- Suggest completing merge or creating branch first

### 1b. **Outstanding Work Gate**

Before any cleanup or wrap-up, check for outstanding work. If found, **STOP** and inform the user — do not proceed to cleanup, commits, or summary.

Skip this gate if `force` argument was provided.

**Checks to perform:**

1. **Active tasks** — query TaskList for any tasks with status `in_progress` or `todo`:
   - If active tasks exist, list them with their status

2. **Uncommitted changes** — already collected in pre-computed context (`git status --short`):
   - Unstaged modifications or untracked files that look intentional (not temp files)

3. **Stashed changes** — work the user may have forgotten:
   ```bash
   git stash list 2>/dev/null | head -5
   ```

4. **Open TODOs from this session** — scan for `TODO` or `FIXME` added in uncommitted changes:
   ```bash
   git diff HEAD 2>/dev/null | grep "^+" | grep -iE "TODO|FIXME|HACK|XXX" | head -10
   ```

**If any outstanding work is found, display:**

```
═══════════════════════════════════
    OUTSTANDING WORK DETECTED
═══════════════════════════════════

⚠️  Cannot wrap up — the following work is still pending:

[If active tasks:]
📋 Active tasks:
  - [task name] (in_progress)
  - [task name] (todo)

[If uncommitted changes:]
📝 Uncommitted changes:
  M  src/auth/middleware.ts
  ??  src/utils/newHelper.ts

[If stashed changes:]
📦 Stashed changes:
  stash@{0}: WIP on main: abc123 last commit message

[If TODOs in diff:]
🔖 New TODOs in uncommitted code:
  + // TODO: handle edge case for expired tokens
  + // FIXME: race condition in queue drain

─────────────────────────────────

Options:
  1. Go back and finish the work
  2. Continue with /end anyway (will auto-commit what's there)
  3. Run /end force (skip all processing, just show summary)

Choose: [1/2/3]
```

**Handle user choice:**
- **1**: Stop the /end command entirely. User returns to normal session.
- **2**: Proceed with the normal /end workflow (Step 2 onwards).
- **3**: Jump to Step 8 (session summary only).

**If NO outstanding work found:** Proceed silently to Step 2.

### 2. **Silent Cleanup (Auto-Remove Files)**

Unless `skip-cleanup` argument provided, auto-remove these files without prompting:

**macOS .DS_Store:**
```bash
# Auto-remove .DS_Store without prompting (macOS only)
find . -name ".DS_Store" -type f \
  -not -path "./.git/*" \
  -not -path "./node_modules/*" \
  -not -path "./.venv/*" \
  -print -delete 2>/dev/null | wc -l
```

Show: "Cleaned N .DS_Store files" (if N > 0, macOS only)

**Backup files (.bak):**
```bash
# Auto-remove .bak files without prompting (all platforms)
find . -name "*.bak" -type f \
  -not -path "./.git/*" \
  -not -path "./node_modules/*" \
  -not -path "./.venv/*" \
  -print -delete 2>/dev/null | wc -l
```

Show: "Cleaned N .bak files" (if N > 0)

This is **automatic and silent** - no user confirmation needed for .DS_Store (macOS) or .bak files.

### 2.5. **Local Server Shutdown**

Skip this step if `skip-cleanup` or `keep-servers` argument provided.

Dev sessions routinely leave background servers running — `npm run dev`, `hugo server`, `astro dev`, `vite`, `next dev`, `python -m http.server`, `php -S`, etc. — bound to local ports (3000, 5100, 8300, 1313, 4321, …). Left running after the session, they hold ports, burn CPU/battery, and serve stale builds into the next session's QA. Shut them down before wrapping up.

**2.5a. Stop servers THIS session started (silent, automatic).**

If you launched any background processes during this session via `run_in_background` (dev servers, watchers, `browse` daemon spawned for QA), terminate them now. These are unambiguously session-scoped — kill them without prompting. Use the background-shell IDs the harness is tracking; do not blanket-kill by name.

Show: "Stopped N local server(s) started this session" (if N > 0).

**2.5b. Detect other listening dev servers (confirm before killing).**

Scan for dev servers that are still listening but were **not** started by this session — they may belong to another session or to deliberate long-running work:

```bash
# macOS / Linux: list listeners on common dev ports owned by dev-server processes
lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null \
  | grep -iE 'node|bun|vite|next|hugo|astro|deno|python|php|ruby|rails|webpack' \
  | awk '{print $1, $2, $9}' | sort -u
```

**If any are found that this session did NOT start:**
- List them clearly (process, PID, port)
- Ask: "Shut down these dev servers too?" (y/N)
- Default is **NO** — only kill if the user explicitly confirms
- Never auto-kill a server this session didn't start

**Safety:**
- **Never** kill non-dev-server processes (databases, system services, the user's editor/IDE, the Claude Code process itself).
- **Never** touch production services on remote hosts — this step is local-only. Do not SSH into a remote/production host and stop services here.
- If detection is ambiguous, list and ask rather than guess.

### 3. **Temp File Cleanup (Other Files)**

Unless `skip-cleanup` argument provided, find other temp files:

```bash
# Find temp files (excludes .DS_Store and .bak which are auto-removed in Step 2)
find . -type f \( \
  -name "*.tmp" -o \
  -name "*.swp" -o \
  -name "*~" -o \
  -name "*.orig" \
\) -not -path "./.git/*" -not -path "./node_modules/*" -not -path "./.venv/*" 2>/dev/null

# Find temp directories (excluding Python cache which auto-regenerates)
find . -type d \( \
  -name ".pytest_cache" -o \
  -name ".ruff_cache" \
\) -not -path "./.git/*" -not -path "./node_modules/*" -not -path "./.venv/*" 2>/dev/null
```

**Python cache files (`*.pyc`, `__pycache__`, `.mypy_cache`) are automatically excluded** - they're regenerated during execution.

**If temp files/dirs found:**
- List them clearly
- Ask: "Remove these temporary files?" (y/N)
- Default is NO - only delete if user explicitly confirms
- Never delete without confirmation

**Session `/tmp` scratch artifacts:**
Sessions commonly write scratch files to the system temp dir — screenshots (`/tmp/*.png`), responsive-shot prefixes, `browse` captures, OG-image staging (`/tmp/og-gen-*`). If you created any such files **during this session**, list and remove them (same y/N confirmation as above). Only target paths this session actually wrote — never blanket-delete `/tmp`, and never touch temp files you can't attribute to this session (other processes and sessions use `/tmp` too).

### 4. **Auto-Commit Workflow**

Skip this step if:
- `manual` mode is enabled (go to interactive prompts instead)
- IS_GIT = "no"
- IS_MERGE = "yes"
- IS_DETACHED = "detached"

**Check for uncommitted changes:**
```bash
git status --short
```

**If uncommitted changes exist:**

1. Announce: "Uncommitted changes detected - committing..."

2. Commit the changes:
   - If you have a `/ship`-style commit skill, invoke it (it analyzes changes, updates a CHANGELOG if present, and writes the message).
   - Otherwise, stage everything and create a single well-described commit (`git add -A && git commit`) whose message summarizes the actual diff. Update the CHANGELOG yourself if the project keeps one.

3. Monitor for success/failure

**Mixed commits are fine:** The working tree may contain changes from prior sessions, manual edits, or work-in-progress that predates this conversation. Do **not** try to separate "session work" from "pre-existing work", and do **not** stash, revert, or skip files just because you didn't touch them this session. Commit everything that's staged/unstaged as a single coherent set — `/ship` writes a commit message that describes the actual diff, regardless of when the changes were made. If the diff spans clearly unrelated concerns, `/ship` may split into multiple commits on its own; otherwise one mixed commit is the correct outcome.

**If /ship fails:**
```
❌ Commit workflow failed: [error message]

Options:
1. Fix manually (session stays open)
2. Skip commit (continue with other cleanup)
3. Abort /end command

Choose: [1/2/3]
```

Handle user choice:
- 1: Keep session open, don't proceed
- 2: Continue to next step without committing
- 3: Exit /end command immediately

**Manual mode behavior:**
If `manual` argument provided, ask instead: "Commit these changes?" (Y/n)
- If yes, invoke /ship skill
- If no, warn that changes will persist uncommitted

### 5. **Auto-Push**

Skip this step if:
- `manual` mode is enabled (go to interactive prompts instead)
- IS_GIT = "no"
- Previous commit step failed and user chose to skip

**Check for unpushed commits:**
```bash
UNPUSHED=$(git log --oneline @{upstream}..HEAD 2>/dev/null)
```

**If unpushed commits exist:**

1. Announce: "Pushing commits to remote..."

2. Attempt push:
```bash
git push 2>&1
```

**If push fails:**
```
❌ Push failed: [error details]

Common causes:
- Network issue
- Remote has changes (try: git pull --rebase)
- Permission issue (check SSH keys)

Options:
1. Retry push
2. Skip push (commits stay local)
3. Abort /end

Choose: [1/2/3]
```

**Manual mode behavior:**
If `manual` argument provided:
- Ask: "Push commits?" (Y/n)

### 6. **Generate PROJECT_MAP.md**

Skip this step if `skip-map` argument provided.

This step generates/updates TWO files:
1. **PROJECT_MAP.md** - Comprehensive detailed documentation (200 lines max)
2. **CLAUDE.md** - Essential 20-line context (token-efficient)

#### 6a. Gather Context

Collect information about the project:

```bash
# Directory structure
ls -la
find . -maxdepth 2 -type d 2>/dev/null | head -30

# Git activity (last 20 commits)
git log --oneline -20 2>/dev/null

# Files changed in recent commits
git diff --name-status HEAD~5..HEAD 2>/dev/null

# Tech stack detection
cat package.json 2>/dev/null | head -50
cat pyproject.toml 2>/dev/null | head -50
cat requirements.txt 2>/dev/null | head -50
cat Cargo.toml 2>/dev/null | head -30
cat go.mod 2>/dev/null | head -30
cat composer.json 2>/dev/null | head -30

# Existing documentation
cat CLAUDE.md 2>/dev/null | head -100
cat README.md 2>/dev/null | head -100

# Check if PROJECT_MAP.md already exists
cat PROJECT_MAP.md 2>/dev/null
```

#### 6b. Generate PROJECT_MAP.md (Comprehensive Details)

Generate a comprehensive PROJECT_MAP.md file with this structure:

```markdown
# Project Map

**Last Updated:** YYYY-MM-DD (auto-generated by /end)
**Project:** [directory name]

---

## ⚡ Quick Reference (Start Here)

**What:** [1-2 sentence description of what this project does]
**Tech:** [Primary language + framework]
**Start:** `[main command to start dev environment]`

**Top 5 Files to Know:**
1. `file1` - [1-line description]
2. `file2` - [1-line description]
3. `file3` - [1-line description]
4. `file4` - [1-line description]
5. `file5` - [1-line description]

---

## Tech Stack

- **Language:** [detected from files]
- **Framework:** [detected from package.json, etc.]
- **Database:** [if applicable]
- **Key Dependencies:** [top 3-5 most important packages]

## Directory Structure

```
project/
├── dir1/          - [purpose inferred from contents]
├── dir2/          - [purpose]
│   ├── subdir/    - [purpose]
├── dir3/          - [purpose]
└── config/        - [purpose]
```

## Critical Files

**Configuration:**
- `file1` - [what it configures]
- `file2` - [purpose]

**Core Logic:**
- `file3` - [what it does]
- `file4` - [purpose]
- `file5` - [purpose]

**Deployment:**
- `file6` - [deployment script/config]
- `file7` - [infrastructure]

## Recent Session Work

[Generated from git log of commits from this session - list 3-5 most recent commits with short descriptions]

Example:
- 2026-01-23: Added authentication middleware (abc123)
- 2026-01-23: Fixed race condition in payment processing (def456)
- 2026-01-23: Updated API documentation (ghi789)

## Quick Start Commands

```bash
# Development
[commands to start dev environment - from package.json scripts, README, or CLAUDE.md]

# Testing
[test commands if applicable]

# Deployment
[if CLAUDE.md has deployment info, reference it; otherwise show basic deploy command]
```

## Architecture Highlights

[Key architectural decisions or patterns detected in the codebase]
- [Decision 1 with rationale]
- [Decision 2 with rationale]
- [Notable pattern or design choice]

## External Integrations

[If any external APIs, services, or databases are detected]
- **[Service Name]** - [purpose, auth method if visible]
- **[Database]** - [connection details from CLAUDE.md if present]

## Notes

[Preserve any manual notes that were in previous version of PROJECT_MAP.md]

[This section is for human-added context that should survive regeneration]

---

*Auto-generated by Claude Code's /end command. For deployment details and environment-specific instructions, see CLAUDE.md.*
```

**Update behavior if PROJECT_MAP.md already exists:**
- Preserve the "Notes" section entirely (manual edits)
- Update "Last Updated" timestamp
- Update "Recent Session Work" with current session commits
- Update "Tech Stack" if dependencies changed
- Refresh "Directory Structure" if new directories added
- Update "Top 5 Files" in Quick Reference if critical files changed
- Keep other sections unless significant changes detected

**Fallback if generation fails:**
Use a basic template with just:
- Project name
- Last updated timestamp
- Tech stack from files
- Directory listing
- Note that full generation failed

#### 6c. Update CLAUDE.md with Essential Context

This is **critical for token efficiency** - new agent sessions get essential info immediately.

**Check if CLAUDE.md exists:**
```bash
test -f CLAUDE.md
```

**If CLAUDE.md exists:**

1. Extract essentials from PROJECT_MAP.md:
   - 1-sentence purpose from Quick Reference
   - Top 3-5 key directories with purposes
   - Top 3-5 main files with purposes
   - 1-3 quick start commands

2. Check if "## Project Map" section exists:
```bash
grep -q "## Project Map" CLAUDE.md
```

3. If section exists:
   - Use Edit tool to replace content between "## Project Map" and next "##" heading
   - Keep to 20 lines max (excluding markdown formatting)
   - Show: "✅ Updated Project Map section in CLAUDE.md (20 lines)"

4. If section doesn't exist:
   - Use Edit tool to add section after "## Tech Stack" (or near top if no Tech Stack)
   - Show: "✅ Added Project Map section to CLAUDE.md (20 lines)"

**Essential context format for CLAUDE.md:**

```markdown
## Project Map

**Purpose:** [1 sentence - extracted from PROJECT_MAP.md Quick Reference]

**Key Directories:**
- `dir1/` - [purpose]
- `dir2/` - [purpose]
- `dir3/` - [purpose]

**Main Files:**
- `path/to/file1` - [purpose]
- `path/to/file2` - [purpose]
- `path/to/file3` - [purpose]

**Quick Start:**
```bash
[1-3 essential commands extracted from PROJECT_MAP.md]
```

**Full Details:** See [PROJECT_MAP.md](PROJECT_MAP.md) for architecture notes, integration points, and comprehensive structure.
```

**If CLAUDE.md doesn't exist:**
- Show note: "No CLAUDE.md found - PROJECT_MAP.md created as standalone"
- Skip CLAUDE.md update

**Benefits of this two-tier approach:**
- CLAUDE.md: ~20 lines of essential context (always loaded, minimal tokens)
- PROJECT_MAP.md: Comprehensive details (loaded only when needed)
- New agents get critical info immediately without token waste
- Deep details available when required

### 7. **CHANGELOG.MD Audit**

Check if CHANGELOG.MD exists and appears current:

```bash
# Compare last commit date vs CHANGELOG modification
git log -1 --format="%h %s" 2>/dev/null
head -20 CHANGELOG.MD 2>/dev/null
```

**If CHANGELOG.MD doesn't exist or looks stale:**
- Show informational note: "ℹ️  CHANGELOG.MD may need updating for recent changes"
- This is informational only - don't block or prompt

**Skip this check if:**
- Not a git repo
- /ship was run in step 4 (it updates CHANGELOG.MD automatically)

### 7b. **Conversation Distill & Handoff**

Re-read the conversation from the beginning and extract value that didn't make it into commits or files. This captures the epistemic side of the session — implicit standards, decisions, and loose threads.

**Scan the conversation for these signal types:**

| Signal | Action |
|--------|--------|
| User corrections to your approach | Save as feedback memory (`/memory`) |
| Design decisions with rationale | Note in handoff file |
| Unfinished threads ("we should also check X" — never did) | Note in handoff file as TODO |
| User preferences expressed in passing | Save as user memory (`/memory`) |
| Discoveries about system behavior | Note in handoff file |
| Root cause analyses worth preserving | Note in handoff file |
| Escalations that saved time or prevented mistakes | Note in handoff `## Escalation outcomes` |
| Escalations that should have happened but didn't (caught late) | Note in handoff + save as feedback memory |
| Agent outcomes (which agents succeeded, failed, or were blocked) | Note in handoff `## Agent outcomes` |
| QC review findings (from post-wave review or /code-review) | Note in handoff `## QC findings` |
| Papercuts noticed but not fixed | Note in handoff `## Sweep candidates` |

**Rules:**
- Only save memories for signals that are **non-obvious and reusable across sessions**
- Don't save memories for things already in CLAUDE.md, code, or git history
- Don't save memories for ephemeral task context
- If nothing worth capturing, skip silently — don't force it

**Write `.session-handoff.md` in the project root:**

```markdown
# Session Handoff

**Date:** YYYY-MM-DD HH:MM (timezone)
**Branch:** [current branch]
**Last commit:** [hash] [message]

## What was done
- [Bullet list of completed work from this session]

## What's in progress
- [Anything started but not finished, with current state]

## Unfinished threads
- [Things discussed but not acted on — "we should also..." moments]

## Decisions made
- [Key decisions with rationale — especially non-obvious ones]

## Escalation outcomes
- [What was escalated to the user and whether it was the right call]
- [Anything that should have been escalated but wasn't — caught late]
- [Omit this section if no escalations occurred]

## Agent outcomes
- [Which agents were spawned, what they produced, pass/fail/block]
- [Any agent that consistently failed or needed retry — pattern worth noting]
- [Omit this section if no agents were spawned]

## QC findings
- [Issues caught by post-wave review, /code-review, or /gstack-review]
- [False positives that wasted time]
- [Omit this section if no QC ran]

## Sweep candidates
- [Papercuts, tech debt, or quick wins noticed but not addressed]
- [Good input for a future /sweep run]
- [Omit this section if none noticed]

## Next steps
- [Suggested continuation points, ordered by priority]
```

**Skip handoff if:**
- Session was trivial (single question/answer, no code changes)
- `force` argument was provided
- `skip-map` argument was provided

**Note:** `.session-handoff.md` is overwritten each session (not appended). Add to `.gitignore` if not already there. The `/catchup` command already reads this file.

### 7b.5. **Codify Learnings**

Skip this step if:
- Session was trivial (no commits, no code changes)
- `force` argument was provided
- `skip-map` argument was provided

Codify the session's learnings. If you have a `/learnings`-style skill, invoke it; otherwise do the same work inline. This closes the knowledge loop — patterns, gotchas, and reusable workflows discovered this session get written into the right file (project `CLAUDE.md`, `PROJECT_MAP.md`, or a rules file) so they compound across sessions rather than evaporating.

The process: identify what was learned, categorize by scope, write it down (with a dedup check against existing entries so you update rather than duplicate), and report what was captured and where.

**Then, if the project keeps a memory store, check its health.** Memories accumulate forever unless pruned. Count files in the project memory dir (skip this if no such dir exists):

```bash
MEM_DIR="$HOME/.claude/projects/-$(pwd | sed 's|/|-|g')/memory"
MEM_COUNT=$(find "$MEM_DIR" -maxdepth 1 -name '*.md' -not -name 'MEMORY.md' 2>/dev/null | wc -l | tr -d ' ')
```

Apply this threshold:

| Count | Action |
|-------|--------|
| < 15 | Skip silently |
| 15–25 | Inline note: "ℹ️ Memory has $MEM_COUNT entries — consider consolidating soon" |
| > 25 | Inline note + consolidate now: ground claims against the codebase, prune stale entries, deduplicate (use a `/memory-consolidate`-style skill if you have one) |

This pairs with the dedup check in the learnings step: that prevents new duplicates at
write time, this prunes accumulated decay at session end.

### 7c. **Session Metrics (Structured Log)**

Append a structured JSONL entry to `.session-metrics.jsonl` in the project root. This enables `/retro` and future analysis to detect patterns across sessions — which agent types succeed, what escalation patterns recur, where QC catches real issues vs false positives.

**Collect from the conversation:**

```bash
# Git metrics for this session
COMMITS=$(git log --oneline --since="$(date -v-4H +%Y-%m-%dT%H:%M:%S 2>/dev/null || date -d '4 hours ago' +%Y-%m-%dT%H:%M:%S 2>/dev/null)" 2>/dev/null | wc -l | tr -d ' ')
FILES_CHANGED=$(git diff --name-only HEAD~${COMMITS}..HEAD 2>/dev/null | wc -l | tr -d ' ')
```

**Build and append the metrics entry:**

```json
{
  "date": "YYYY-MM-DDTHH:MM:SS",
  "branch": "[current branch]",
  "duration_min": "[estimated from first to last commit, or conversation length]",
  "commits": "[N]",
  "files_changed": "[N]",
  "agents_spawned": [
    {"type": "code-reviewer", "outcome": "pass", "model": "sonnet"},
    {"type": "debugger", "outcome": "completed", "model": "sonnet"}
  ],
  "escalations": {
    "count": "[N]",
    "categories": ["auth", "schema"],
    "correct": "[N that were the right call]",
    "missed": "[N that should have escalated but didn't]"
  },
  "qc_verdicts": {
    "pass": "[N]",
    "flag": "[N]",
    "block": "[N]"
  },
  "sweep_candidates": "[N papercuts noticed]",
  "skills_used": ["ship", "debug", "code-review"],
  "model": "[primary model used]"
}
```

```bash
# Append (never overwrite)
echo '{...}' >> .session-metrics.jsonl
```

**Rules:**
- Append-only — never overwrite or truncate the file
- Add `.session-metrics.jsonl` to `.gitignore` if not already there (local analytics, not committed)
- If no agents were spawned and no escalations occurred, still log the basic metrics (commits, files, duration, skills) — the absence of agent usage is itself a data point
- Skip entirely if session was trivial (no commits, no code changes)
- `/retro` should read this file when analyzing weekly patterns

### 8. **Session Summary**

First, detect if on a non-main branch:

```bash
CURRENT_BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || echo "detached")
MAIN_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
IS_FEATURE_BRANCH="no"

if [ "$CURRENT_BRANCH" != "$MAIN_BRANCH" ] && [ "$CURRENT_BRANCH" != "detached" ]; then
  IS_FEATURE_BRANCH="yes"
fi
```

Display final summary based on what actually executed:

```
═══════════════════════════════════
       SESSION COMPLETE
═══════════════════════════════════

[Conditional lines based on what ran:]

✅ Stopped 2 local server(s) (port 1313, 5100)
✅ Cleaned 3 .DS_Store files (macOS)
✅ Removed 5 temporary files
✅ Changes committed via /ship
✅ Pushed to remote: origin/main
✅ PROJECT_MAP.md updated (comprehensive details)
✅ CLAUDE.md updated (essential context: 20 lines)

─────────────────────────────────

Repository Status:
  Branch:      main
  Last commit: a1b2c3d Fix authentication bug
  Status:      Working tree clean

[If IS_FEATURE_BRANCH = "yes":]
🌿 FEATURE BRANCH SESSION
──────────────────────────────────
You are ending this session on branch: [branch-name]

[If unpushed commits exist:]
⚠️  This branch has [N] unpushed commit(s)
   Work is saved locally but not on remote

[If working tree is dirty:]
⚠️  This branch has uncommitted changes
   Changes are only in your working directory

[If branch has both unpushed and uncommitted:]
⚠️  This branch has uncommitted changes AND [N] unpushed commits
   Work is saved locally but not on remote

To resume this work:
  1. git checkout [branch-name]
  2. Continue development
  3. When ready: git push (if not already pushed)
  4. Create PR: gh pr create or use /pr

──────────────────────────────────

[If warnings exist:]
⚠️  Warnings:
  - CHANGELOG.MD may be stale
  - 2 stashed changes pending

─────────────────────────────────

[1-2 sentence accomplishment summary of session work]

You can now /exit if all work is done and there is nothing more to clarify.
```

**Adapt checkmarks dynamically:**
- Show ✅ only for operations that succeeded
- Show ❌ for operations that failed
- Omit lines for operations that were skipped
- If `manual` mode: note "(manual mode)" in summary
- If `force` mode: show minimal summary only

**Example variations:**

*Nothing to do:*
```
═══════════════════════════════════
       SESSION COMPLETE
═══════════════════════════════════

✅ No temporary files found
✅ Working tree clean
✅ All commits pushed

No changes made this session.

You can now /exit if all work is done and there is nothing more to clarify.
```

*Errors occurred:*
```
═══════════════════════════════════
       SESSION COMPLETE
═══════════════════════════════════

❌ Push failed: remote has newer commits
✅ PROJECT_MAP.md updated

─────────────────────────────────

Repository Status:
  Branch:      feature/auth
  Last commit: a1b2c3d Fix authentication bug
  Status:      3 commits ahead of origin

🌿 FEATURE BRANCH SESSION
──────────────────────────────────
You are ending this session on branch: feature/auth

⚠️  This branch has 3 unpushed commit(s)
   Work is saved locally but not on remote

To resume this work:
  1. git checkout feature/auth
  2. Resolve push conflict: git pull --rebase
  3. Push changes: git push
  4. Create PR: gh pr create or use /pr

──────────────────────────────────

Resolve the push conflict before continuing.

You can now /exit if all work is done and there is nothing more to clarify.
```

*Feature branch with uncommitted changes:*
```
═══════════════════════════════════
       SESSION COMPLETE
═══════════════════════════════════

✅ No temporary files found
✅ PROJECT_MAP.md updated

─────────────────────────────────

Repository Status:
  Branch:      feature/new-ui
  Last commit: b4c5d6e Update button styles
  Status:      Working tree has 2 modified files

🌿 FEATURE BRANCH SESSION
──────────────────────────────────
You are ending this session on branch: feature/new-ui

⚠️  This branch has uncommitted changes
   Changes are only in your working directory

Modified files:
  - src/components/Header.tsx
  - src/styles/theme.css

To resume this work:
  1. git checkout feature/new-ui
  2. Review changes: git status
  3. Commit when ready: /ship
  4. Create PR: gh pr create or use /pr

──────────────────────────────────

You can now /exit if all work is done and there is nothing more to clarify.
```

## Force Mode

If `force` argument provided:
- Skip all steps 1-7
- Show minimal summary:
  - Current branch
  - Last commit
  - Working tree status
- Exit immediately without any prompts or processing

## Error Handling

- **Not a git repo**: Skip all git operations, still do cleanup and PROJECT_MAP.md (if applicable)
- **Merge in progress**: Warn user, skip auto-commit, suggest: "Complete merge first with: git merge --continue"
- **Detached HEAD**: Warn user, skip auto-commit, suggest: "Create branch with: git checkout -b <branch-name>"
- **Ship fails**: Show error, offer retry/skip/abort options, wait for user choice
- **Push fails**: Show error with common causes, offer retry/skip/abort
- **PROJECT_MAP.md generation fails**: Use basic fallback template with directory listing and tech stack
- **CLAUDE.md update fails**: Show warning, PROJECT_MAP.md still created successfully
- **CHANGELOG.MD missing**: Show informational note only (non-blocking)
- **Find command fails**: Skip cleanup, show warning, proceed to next step
- **Not on macOS**: Skip .DS_Store cleanup silently
- **`lsof` unavailable or server kill fails**: Show warning, skip server detection, proceed to next step — never block exit on a failed shutdown

## Safety Rules

- **NEVER auto-delete files without confirmation** (exceptions: .DS_Store on macOS, .bak files on all platforms)
- **Server shutdown is local-only** - auto-kill only servers THIS session started; confirm before killing any other dev server; never touch databases, system services, IDEs, the Claude Code process, or remote/production services
- **NEVER force-commit** - always use /ship skill which does proper analysis
- **NEVER push if remote has commits we don't have** - check first
- **OK to commit pre-existing uncommitted work** - the working tree at session-end may include changes you didn't make this session; commit them anyway rather than leaving the tree dirty
- **NEVER block exit** - all warnings are informational, user can always exit
- **Always show what will be deleted** before deleting (except .DS_Store on macOS and .bak files)
- **Always give user options** if auto-operations fail (retry/skip/abort)
- **Always preserve manual edits** in PROJECT_MAP.md "Notes" section during updates
- **Never modify PROJECT_MAP.md structure** if user has customized it - only update specific sections
- **Always verify git state** before auto-operations (check for merge, detached HEAD, etc.)

## Manual Mode (Escape Hatch)

When user runs `/end manual`, restore old interactive behavior:

**Changes in manual mode:**
- Step 2: Still auto-remove .DS_Store (macOS) and .bak files, but announce counts
- Step 2.5: Ask "Shut down local dev servers?" instead of auto-stopping session-started servers
- Step 4: Ask "Commit these changes?" instead of auto-running /ship
- Step 5: Ask "Push commits?" instead of auto-pushing
- Step 6: Ask "Update PROJECT_MAP.md?" instead of auto-generating

This preserves the old workflow for users who want fine-grained control.

All other steps (temp file cleanup, CHANGELOG audit, summary) work the same as default mode.
