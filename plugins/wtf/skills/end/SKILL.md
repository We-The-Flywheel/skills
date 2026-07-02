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

> **Note:** This skill orchestrates a few optional helpers (a commit-workflow skill
> such as `/go-live` or `/commit-push`, a learnings step, a memory-consolidation step,
> a session-handoff/recall file). "The commit skill" below means whichever of those is
> installed. Where one isn't, fall back to the plain-git or inline equivalent described
> at each step — the skill never hard-depends on tooling you don't have. Never reference
> a skill that isn't in your available-skills list.

## Arguments

$ARGUMENTS

## Pre-Computed Context

**Branch:** $(git branch --show-current 2>/dev/null || echo "detached")
**Status:** $(git status --short 2>/dev/null | head -15)
**Unpushed:** $(git log --oneline @{upstream}..HEAD 2>/dev/null || echo "none")
**Last commit:** $(git log -1 --format="%h %s (%ar)" 2>/dev/null || echo "none")

- `manual` - Use interactive prompts for commits (old behavior)
- `skip-map` - Don't update PROJECT_MAP.md or CLAUDE.md (also skips handoff/decisions/learnings)
- `skip-cleanup` - Skip temp file cleanup AND local server shutdown
- `keep-servers` - Run cleanup but leave local dev servers running
- `force` - Exit immediately without processing (shows summary only)

**Default behavior (no arguments):**
- Shut down local dev servers this session started (silent)
- Auto-remove .DS_Store (macOS) and .bak files (silent)
- Distill the conversation → `.session-handoff.md`, `DECISIONS.md`, and codified learnings
- Generate/update PROJECT_MAP.md + essential CLAUDE.md context
- Auto-commit everything via the commit skill (docs included), auto-push

**Step order matters:** all file-writing steps (4–8) run BEFORE the commit (Step 9) so handoff, decisions, learnings, and project-map updates ride along in the same commit instead of leaving a dirty tree behind.

## Workflow

### 1. Parse Arguments and Detect Environment

```bash
OS=$(uname -s)
IS_GIT=$(git rev-parse --git-dir 2>/dev/null && echo "yes" || echo "no")
IS_MERGE=$(git status 2>/dev/null | grep -q "merge" && echo "yes" || echo "no")
IS_DETACHED=$(git symbolic-ref -q HEAD || echo "detached")
```

**If `force` argument:** skip all processing, jump directly to the session summary (Step 12), exit immediately.

**If merge in progress or detached HEAD:** warn the user, skip auto-commit operations, suggest completing the merge or creating a branch first.

### 2. Outstanding Work Gate

Before any cleanup or wrap-up, check for outstanding work. If found, **STOP** and inform the user — do not proceed to cleanup, commits, or summary. (Skipped in `force` mode.)

**Checks:**

1. **Active tasks** — query TaskList for tasks with status `in_progress` or `todo`; list them if any
2. **Uncommitted changes** — from pre-computed context (`git status --short`): unstaged modifications or untracked files that look intentional (not temp files)
3. **Stashed changes** — `git stash list 2>/dev/null | head -5`
4. **Open TODOs from this session** — `git diff HEAD 2>/dev/null | grep "^+" | grep -iE "TODO|FIXME|HACK|XXX" | head -10`

**If any outstanding work is found, display:**

```
═══════════════════════════════════
    OUTSTANDING WORK DETECTED
═══════════════════════════════════

⚠️  Cannot wrap up — the following work is still pending:

[List whichever apply: 📋 Active tasks / 📝 Uncommitted changes / 📦 Stashed changes / 🔖 New TODOs in uncommitted code]

─────────────────────────────────

Options:
  1. Go back and finish the work
  2. Continue with /end anyway (will auto-commit what's there)
  3. Run /end force (skip all processing, just show summary)

Choose: [1/2/3]
```

**Handle user choice:** 1 = stop /end entirely; 2 = proceed with the normal workflow (Step 3 onwards); 3 = jump to Step 12 (summary only).

**If NO outstanding work found:** proceed silently to Step 3.

### 3. Cleanup

Skip this entire step if `skip-cleanup` argument provided.

**3a. Silent auto-remove (no confirmation):**

```bash
# .DS_Store (macOS only) and .bak files (all platforms)
find . \( -name ".DS_Store" -o -name "*.bak" \) -type f \
  -not -path "./.git/*" -not -path "./node_modules/*" -not -path "./.venv/*" \
  -print -delete 2>/dev/null
```

Show: "Cleaned N .DS_Store / .bak files" (if N > 0).

**3b. Stop servers THIS session started (silent, automatic).**

Dev sessions routinely leave background servers running — `npm run dev`, `hugo server`, `vite`, `next dev`, etc. — holding ports and serving stale builds into the next session's QA. If you launched any background processes this session via `run_in_background`, terminate them now using the background-shell IDs the harness is tracking; do not blanket-kill by name. Show: "Stopped N local server(s) started this session" (if N > 0). Skip if `keep-servers`.

**3c. Detect other listening dev servers (confirm before killing).** Skip if `keep-servers`.

```bash
lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null \
  | grep -iE 'node|bun|vite|next|hugo|astro|deno|python|php|ruby|rails|webpack' \
  | awk '{print $1, $2, $9}' | sort -u
```

If any are found that this session did NOT start: list them (process, PID, port) and ask "Shut down these dev servers too?" (y/N). Default **NO** — never auto-kill a server this session didn't start.

**Safety:** never kill non-dev-server processes (databases, system services, editors/IDEs, the Claude Code process itself). Local-only — never `ssh` to a server and stop remote/production services here. If detection is ambiguous, list and ask.

**3d. Other temp files (confirm before deleting):**

```bash
find . -type f \( -name "*.tmp" -o -name "*.swp" -o -name "*~" -o -name "*.orig" \) \
  -not -path "./.git/*" -not -path "./node_modules/*" -not -path "./.venv/*" 2>/dev/null
find . -type d \( -name ".pytest_cache" -o -name ".ruff_cache" \) \
  -not -path "./.git/*" -not -path "./node_modules/*" -not -path "./.venv/*" 2>/dev/null
```

Python cache (`*.pyc`, `__pycache__`, `.mypy_cache`) is excluded — it regenerates. If found: list clearly, ask "Remove these temporary files?" (y/N), default NO.

**3e. Session `/tmp` scratch artifacts:** if this session wrote scratch files to the system temp dir (screenshots, capture prefixes, image-staging dirs), list and remove them with the same y/N confirmation. Only target paths this session actually wrote — never blanket-delete `/tmp`.

### 4. Conversation Distill & Handoff

Skip if session was trivial (single Q/A, no code changes), or `force`/`skip-map` provided.

Re-read the conversation from the beginning and extract value that didn't make it into commits or files — implicit standards, decisions, loose threads.

**Scan for these signal types:**

| Signal | Action |
|--------|--------|
| User corrections to your approach | Save as a feedback memory (if a memory store exists) |
| Design decisions with rationale | Note in handoff file |
| Unfinished threads ("we should also check X" — never did) | Note in handoff file as TODO |
| User preferences expressed in passing | Save as a user memory (if a memory store exists) |
| Discoveries about system behavior | Note in handoff file |
| Root cause analyses worth preserving | Note in handoff file |
| Escalations that saved time or prevented mistakes | Note in handoff `## Escalation outcomes` |
| Escalations that should have happened but didn't (caught late) | Note in handoff + save as a feedback memory |
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
- [This section is the **staging buffer** for the durable decision log: Step 5 promotes the lasting "we chose X over Y, because…" entries from here into committed `DECISIONS.md`. Capture rationale and the rejected alternative even for decisions you'll log durably — this buffer is overwritten next session.]

## Escalation outcomes
- [What was escalated and whether it was the right call; anything caught late. Omit if none.]

## Agent outcomes
- [Agents spawned, what they produced, pass/fail/block; retry patterns. Omit if none.]

## QC findings
- [Issues caught by review; false positives that wasted time. Omit if no QC ran.]

## Sweep candidates
- [Papercuts, tech debt, or quick wins noticed but not addressed. Omit if none.]

## Next steps
- [Suggested continuation points, ordered by priority]
```

**Note:** `.session-handoff.md` is overwritten each session (not appended). Add to `.gitignore` if not already there. A recall/catchup step (if you have one) surfaces it at the start of the next session.

### 5. Harvest Decisions (Durable Decision Log)

Skip if session was trivial, or `force`/`skip-map` provided.

Promote the **durable** decisions from the ephemeral `## Decisions made` staging buffer (Step 4) into a committed, append-only `DECISIONS.md` at the repo root. This is the immutable "why" tier: `.session-handoff.md` is gone next session, `PROJECT_MAP.md` is a regenerated snapshot, `CHANGELOG.md` records *what* shipped — `DECISIONS.md` is the only durable record of *why we chose X over Y*, and what a future session reads instead of re-litigating a settled choice.

Runs **before** the learnings step (Step 6) and PROJECT_MAP (Step 7) so Architecture Highlights can derive from a freshly-written log, and **before** the commit (Step 9) so the file ships in this session's commit.

**5a. Filter — what qualifies.** Log an entry **only** when all hold:
- It resolved a real fork (architecture, tooling, schema, data model, process, API contract, "X over Y").
- It has lasting rationale — a future session could otherwise reasonably re-debate it.
- There was a rejected alternative worth recording.

Do **not** log: implementation mechanics or routine bug fixes (commits/`CHANGELOG.md`), reusable patterns or gotchas (the learnings step, Step 6), or ephemeral task choices. If nothing qualifies, skip silently — never force an entry.

**5b. Dedup gate (required before writing).** For each candidate, grep the existing log for its key noun/concept first:

```bash
# Example candidate: "use a single append-only DECISIONS.md, not per-file ADRs"
grep -in "DECISIONS\.md\|per-file ADR\|decision log" DECISIONS.md 2>/dev/null
```

| Result | Action |
|--------|--------|
| Identical decision already logged | **Skip** — report "already logged: DECISIONS.md:<line>" |
| Prior decision now reversed/changed by this session | **Supersede** — append a new entry AND flip the old entry's `**Status:**` to `superseded by [<this entry's date+title>]` (the only permitted edit to history) |
| Genuinely new decision | **Append** a new entry at the top (newest-on-top) |

**5c. Write the entry.** Create `DECISIONS.md` if absent (newest-on-top, append-only). Each entry, ~6 lines:

```markdown
## YYYY-MM-DD — <decision title>
**Status:** accepted
**Context:** <the forcing question — what made this a real choice>
**Decision:** <what we chose>
**Alternatives:** <what we rejected, and the one-line why>
**Consequences:** <what this locks in or costs later>   ← optional, omit if obvious
```

**Rules:** append-only (sole exception: flipping a `**Status:**` line when superseding); newest entry at the top under `# Decisions`; keep entries tight — this is not a design doc. `DECISIONS.md` is **committed** (tracked) — never `.gitignore` it. Report: "📋 Logged N decision(s) to DECISIONS.md" (or skip silently).

### 6. Codify Learnings

Skip if session was trivial, or `force`/`skip-map` provided.

Codify the session's learnings. If you have a `/learnings`-style skill, invoke it; otherwise do the same work inline. This closes the knowledge loop — patterns, gotchas, and reusable workflows discovered this session get written into the right file (project `CLAUDE.md`, `PROJECT_MAP.md`, or a rules file) so they compound across sessions rather than evaporating. The process: identify what was learned, categorize by scope, write it down with a dedup check against existing entries (so you update rather than duplicate), and report what was captured and where.

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

### 7. Generate PROJECT_MAP.md + CLAUDE.md Context

Skip if `skip-map` argument provided.

Generates/updates TWO files: **PROJECT_MAP.md** (comprehensive, 200 lines max) and **CLAUDE.md** (essential ~20-line context, token-efficient).

#### 7a. Gather Context

```bash
ls -la
find . -maxdepth 2 -type d 2>/dev/null | head -30
git log --oneline -20 2>/dev/null
git diff --name-status HEAD~5..HEAD 2>/dev/null
# Tech stack detection (whichever exist)
head -50 package.json pyproject.toml requirements.txt 2>/dev/null
head -30 Cargo.toml go.mod composer.json 2>/dev/null
# Existing documentation
head -100 CLAUDE.md README.md 2>/dev/null
cat PROJECT_MAP.md 2>/dev/null
```

#### 7b. Generate PROJECT_MAP.md

Structure:

```markdown
# Project Map

**Last Updated:** YYYY-MM-DD (auto-generated by /end)
**Project:** [directory name]

---

## ⚡ Quick Reference (Start Here)

**What:** [1-2 sentence description]
**Tech:** [Primary language + framework]
**Start:** `[main command to start dev environment]`

**Top 5 Files to Know:**
1-5. `file` - [1-line description each]

---

## Tech Stack
[Language / Framework / Database / Key Dependencies — detected from files]

## Directory Structure
[Tree with 1-line purpose per directory]

## Critical Files
[Configuration / Core Logic / Deployment — grouped, 1-line purpose each]

## Recent Session Work
[3-5 most recent commits with short descriptions, dated]

## Quick Start Commands
[Development / Testing / Deployment commands from package.json scripts, README, or CLAUDE.md]

## Architecture Highlights
[Key architectural decisions or patterns — derive from DECISIONS.md where entries exist]

## External Integrations
[External APIs, services, databases — purpose + auth method if visible]

## Notes
[Preserve any manual notes from the previous version — human-added context that survives regeneration]

---

*Auto-generated by Claude Code's /end command. For deployment details, see CLAUDE.md.*
```

**Update behavior if PROJECT_MAP.md already exists:** preserve the "Notes" section entirely; update Last Updated, Recent Session Work, Tech Stack (if deps changed), Directory Structure (if new dirs), Top 5 Files (if critical files changed); keep other sections unless significant changes detected.

**Fallback if generation fails:** basic template — project name, timestamp, tech stack, directory listing, note that full generation failed.

#### 7c. Update CLAUDE.md with Essential Context

Critical for token efficiency — new sessions get essential info immediately.

If `CLAUDE.md` exists: extract essentials from PROJECT_MAP.md (1-sentence purpose, top 3-5 directories, top 3-5 files, 1-3 quick-start commands). If a `## Project Map` section exists, replace its content (Edit tool, between the heading and the next `##`); otherwise add the section after `## Tech Stack` (or near the top). Keep to 20 lines max. Show: "✅ Updated/Added Project Map section in CLAUDE.md".

Format:

```markdown
## Project Map

**Purpose:** [1 sentence]

**Key Directories:**
- `dir/` - [purpose]  (×3)

**Main Files:**
- `path/file` - [purpose]  (×3)

**Quick Start:**
```bash
[1-3 essential commands]
```

**Full Details:** See [PROJECT_MAP.md](PROJECT_MAP.md).
```

If `CLAUDE.md` doesn't exist: note "No CLAUDE.md found - PROJECT_MAP.md created as standalone" and skip.

### 8. Session Metrics (Structured Log)

Skip entirely if session was trivial (no commits, no code changes).

Append a structured JSONL entry to `.session-metrics.jsonl` in the project root — input for periodic retrospectives and cross-session pattern analysis (which agent types succeed, what escalation patterns recur, where QC catches real issues vs false positives).

```json
{
  "date": "YYYY-MM-DDTHH:MM:SS",
  "branch": "[current branch]",
  "duration_min": "[estimated from first to last commit, or conversation length]",
  "commits": "[N this session]",
  "files_changed": "[N]",
  "agents_spawned": [{"type": "code-reviewer", "outcome": "pass", "model": "sonnet"}],
  "escalations": {"count": 0, "categories": [], "correct": 0, "missed": 0},
  "qc_verdicts": {"pass": 0, "flag": 0, "block": 0},
  "sweep_candidates": 0,
  "skills_used": ["go-live", "debug"],
  "model": "[primary model used]"
}
```

```bash
echo '{...}' >> .session-metrics.jsonl
```

**Rules:** append-only — never overwrite or truncate; add `.session-metrics.jsonl` to `.gitignore` if not already there (local analytics, not committed); if no agents/escalations occurred, still log the basic metrics — absence is itself a data point.

### 9. Auto-Commit (via the commit skill)

Skip this step if: `manual` mode (interactive prompt instead), IS_GIT = "no", IS_MERGE = "yes", or IS_DETACHED = "detached".

**Check for uncommitted changes:** `git status --short`

**If uncommitted changes exist:**

1. Announce: "Uncommitted changes detected - committing..."
2. Commit the changes:
   - If you have a commit skill installed (e.g. `/go-live`, `/commit-push`), invoke it — it analyzes changes, updates a `CHANGELOG.md` if present, and writes the message. Prefer a commit-only mode (no server deploy / cache purge) if the skill offers one.
   - Otherwise, stage everything and create a single well-described commit (`git add -A && git commit`) whose message summarizes the actual diff. Update the `CHANGELOG.md` yourself if the project keeps one.
3. Monitor for success/failure.

**Mixed commits are fine:** the working tree may contain changes from prior sessions, manual edits, or pre-existing WIP. Do **not** try to separate "session work" from "pre-existing work", and do **not** stash, revert, or skip files you didn't touch this session. Commit everything as a single coherent set — write a message describing the actual diff. If the diff spans clearly unrelated concerns, split into multiple commits; otherwise one mixed commit is correct.

**If the commit step fails:**

```
❌ Commit workflow failed: [error message]

Options:
1. Fix manually (session stays open)
2. Skip commit (continue with other cleanup)
3. Abort /end command

Choose: [1/2/3]
```

**Manual mode:** ask "Commit these changes?" (Y/n); if yes, run the commit step (commit skill if installed, else plain git); if no, warn that changes persist uncommitted.

### 10. Auto-Push

Skip if: `manual` mode (ask "Push commits?" instead), IS_GIT = "no", or the commit step failed and user chose to skip. (A commit skill often pushes already — this step catches commits it left behind.)

```bash
UNPUSHED=$(git log --oneline @{upstream}..HEAD 2>/dev/null)
```

If unpushed commits exist: announce "Pushing commits to remote..." and `git push 2>&1`.

**If push fails:**

```
❌ Push failed: [error details]

Common causes: network issue · remote has changes (try: git pull --rebase) · permission issue (check SSH keys)

Options:
1. Retry push
2. Skip push (commits stay local)
3. Abort /end

Choose: [1/2/3]
```

### 11. CHANGELOG.md Audit

Skip if not a git repo, or if the commit skill ran in Step 9 (it updates `CHANGELOG.md` automatically).

```bash
git log -1 --format="%h %s" 2>/dev/null
head -20 CHANGELOG.md 2>/dev/null
```

If `CHANGELOG.md` doesn't exist or looks stale: show informational note "ℹ️  CHANGELOG.md may need updating for recent changes" — informational only, don't block or prompt.

### 12. Session Summary

Detect branch context first:

```bash
CURRENT_BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || echo "detached")
MAIN_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
IS_FEATURE_BRANCH=$([ "$CURRENT_BRANCH" != "$MAIN_BRANCH" ] && [ "$CURRENT_BRANCH" != "detached" ] && echo yes || echo no)
```

Display a final summary of what actually executed:

```
═══════════════════════════════════
       SESSION COMPLETE
═══════════════════════════════════

[Conditional lines — only for operations that ran:]
✅ Stopped 2 local server(s) (port 1313, 5100)
✅ Cleaned 3 .DS_Store files
✅ Handoff written (.session-handoff.md); 1 decision logged to DECISIONS.md
✅ PROJECT_MAP.md + CLAUDE.md updated
✅ Changes committed
✅ Pushed to remote: origin/main

─────────────────────────────────

Repository Status:
  Branch:      main
  Last commit: a1b2c3d Fix authentication bug
  Status:      Working tree clean

[If IS_FEATURE_BRANCH = "yes":]
🌿 FEATURE BRANCH SESSION — ending on branch: [branch-name]
[⚠️ note unpushed commits and/or uncommitted changes if any]
To resume: git checkout [branch-name] → continue → git push → open a PR (gh pr create)

[If warnings exist:]
⚠️  Warnings:
  - CHANGELOG.md may be stale
  - 2 stashed changes pending

─────────────────────────────────

[1-2 sentence accomplishment summary of session work]

You can now /exit if all work is done and there is nothing more to clarify.
```

**Adapt dynamically:** show ✅ only for operations that succeeded, ❌ for failures, omit skipped operations. Note "(manual mode)" if applicable. In `force` mode show only branch, last commit, and working-tree status.

## Error Handling

- **Not a git repo**: skip all git operations; still do cleanup and PROJECT_MAP.md
- **Merge in progress**: warn, skip auto-commit, suggest `git merge --continue`
- **Detached HEAD**: warn, skip auto-commit, suggest `git checkout -b <branch-name>`
- **Commit or push fails**: show error, offer retry/skip/abort, wait for user choice
- **PROJECT_MAP.md generation fails**: use basic fallback template
- **CLAUDE.md update fails**: warn; PROJECT_MAP.md still created
- **CHANGELOG.md missing**: informational note only (non-blocking)
- **Find command fails**: skip cleanup, warn, proceed
- **Not on macOS**: skip .DS_Store cleanup silently
- **`lsof` unavailable or server kill fails**: warn, skip server detection, proceed — never block exit on a failed shutdown

## Safety Rules

- **NEVER auto-delete files without confirmation** (exceptions: .DS_Store on macOS, .bak files)
- **Server shutdown is local-only** — auto-kill only servers THIS session started; confirm for anything else; never touch databases, system services, IDEs, the Claude Code process, or remote/production services
- **NEVER force-commit** — always analyze the diff and write a message that describes it (commit skill or plain git)
- **NEVER push if remote has commits we don't have** — check first
- **OK to commit pre-existing uncommitted work** — commit it rather than leaving the tree dirty
- **NEVER block exit** — all warnings are informational
- **Always show what will be deleted** before deleting (except the two silent-delete exceptions)
- **Always preserve manual edits** in PROJECT_MAP.md "Notes"; never restructure a user-customized PROJECT_MAP.md — only update specific sections
- **Always verify git state** before auto-operations (merge, detached HEAD, etc.)

## Manual Mode (Escape Hatch)

`/end manual` restores interactive behavior:
- Step 3: still auto-remove .DS_Store/.bak, but announce counts; ask before shutting down any dev server
- Step 9: ask "Commit these changes?" instead of auto-committing
- Step 10: ask "Push commits?" instead of auto-pushing
- Step 7: ask "Update PROJECT_MAP.md?" instead of auto-generating

All other steps work the same as default mode.
