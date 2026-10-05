---
name: wrapup
description: |
  Wrap up a coding session cleanly: shut down local dev servers, remove temp/backup
  files, commit and push session work, verify merge/deployment and branch/worktree cleanup, and refresh project docs (PROJECT_MAP.md +
  AGENTS.md or CLAUDE.md). Use when the user says "wrapup", "/wrapup", "wrap up", "end the session",
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
department: ops
---

End-of-session cleanup and verification with intelligent automation. Ensures work is properly saved and documented before exiting.

**Local overlay.** If `~/.local/share/flywheel/house/wrapup.md` exists, read it before starting and apply it on top of this skill: it holds an organisation's own closure checks, tools and documentation rules for this workflow. Where the two conflict, the overlay wins. No overlay, no change.

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
**Unpushed:** $(git log --oneline @{upstream}..HEAD 2>/dev/null || echo "UNKNOWN — inspect upstream and remote")
**Last commit:** $(git log -1 --format="%h %s (%ar)" 2>/dev/null || echo "none")

- `manual` - Use interactive prompts for commits (old behavior)
- `skip-map` - Don't update PROJECT_MAP.md or AGENTS.md/CLAUDE.md (also skips handoff/decisions/learnings)
- `skip-cleanup` - Skip temp file cleanup AND local server shutdown
- `keep-servers` - Run cleanup but leave local dev servers running
- `force` - Exit immediately without processing (shows summary only)

**Default behavior (no arguments):**
- Shut down local dev servers this session started (silent)
- Auto-remove .DS_Store (macOS) and .bak files (silent)
- Distill the conversation → `.session-handoff.md`, `DECISIONS.md`, and codified learnings
- Generate/update PROJECT_MAP.md + essential AGENTS.md (or CLAUDE.md) context
- Commit all authorized session work (docs included), push, land it in `origin/main` unless explicitly directed elsewhere, and verify the applicable deployment
- Verify merged topic branches are absent locally and remotely, and remove completed temporary worktrees; preserve active or unrelated work

**Step order matters:** file-writing steps run before the final commit. After Steps 9–11, repeat the scoped commit/push/merge/deploy checks if closure produced more tracked changes. `skip-map`, `skip-cleanup`, and `keep-servers` do not skip delivery or branch/worktree verification. `force` is a summary-only exit, never verified completion.

## Workflow

### 1. Parse Arguments and Detect Environment

```bash
OS=$(uname -s)
IS_GIT=$(git rev-parse --git-dir 2>/dev/null && echo "yes" || echo "no")
IS_MERGE=$(git status 2>/dev/null | grep -q "merge" && echo "yes" || echo "no")
IS_DETACHED=$(git symbolic-ref -q HEAD || echo "detached")
```

**If `force` argument:** skip all processing, jump directly to the session summary (Step 12), exit immediately.

**Resolve delivery context before using it:** default to `REMOTE=origin` and `BASE_BRANCH=main`; use a different remote/branch only when the user or project explicitly directs it. Record the deployment target and documented workflow separately: a Git ref is not a deployment target. Verify the remote and base ref exist; absence is a blocker, not permission to guess. Record the current branch, session commits, PRs, and every temporary worktree created or used in this session, including detached and already-removed paths.

**Shared checkout:** inspect Git status, staged paths, registered worktrees, and active sessions before changing Git state. Do not switch, pull, rebase, reset, stash, or remove a checkout used by another session. Do not create a worktree or clone just to wrap up. Use an existing safe checkout or report the exact blocked action.

**If merge in progress or detached HEAD:** preserve the work and diagnose ownership before changing state. Read-only delivery and cleanup audits still run; skipped writes remain incomplete.

### 2. Reconcile Outstanding Work

Inspect active session tasks, `git status --short`, staged paths, `git stash list`, and unresolved TODOs introduced by this session. Use available task tooling, not an assumed tool name. Intentional uncommitted session changes are input to Step 9, not a reason to ask whether to continue.

Finish authorized work and affected checks before shipping. Preserve other sessions' files, commits and stashes; do not stage them to manufacture a clean tree. Inspect the full diff to establish ownership. If a file or hunk has mixed ownership, isolate only the reviewed session change without reverting other edits. Ask only when ownership or a consequential unfinished decision cannot be resolved. Continue independent checks while that question is pending.

A known failure, explicit pause, unresolved conflict, or missing authorization blocks the affected operation. Record its exact reason and next action; never turn a skipped operation into completion. Ordinary commit/push/merge/deploy steps already authorized by the task do not require another confirmation.

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
- **Name the root cause, not the symptom.** For anything that took multiple attempts, ask what single upstream fix (a question asked earlier, a different check, a different verification method) would have prevented the whole chain — and save *that*, as a concrete rule ("grep the literal hostname, not just client construction"), never a sentiment ("be more careful").
- **Proved vs. suggested.** Before writing a lesson, ask whether this session *proved* it (the same failure recurred, the root cause was confirmed against real evidence, or a fix was verified) or only *suggested* it (happened once, plausible, unconfirmed). Proved → save as a firm rule. Suggested → either hold it out of memory and name it in the session summary as a watch-item pending a second occurrence, or save it with the uncertainty stated in the entry ("seen once, not yet confirmed as a pattern"). Never write a single-occurrence guess as an unqualified rule.
- **Update in place.** Read the memory index before writing. If an existing entry already covers the topic, append a dated addendum to that file in its existing structure instead of creating a near-duplicate.

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

Promote the **durable** decisions from the ephemeral `## Decisions made` staging buffer (Step 4) into a committed, append-only `DECISIONS.md` at the repo root. If a hook records decisions automatically (for example an `## Decisions made (auto-captured)` block that a PreCompact/SessionEnd hook writes into `.session-handoff.md`, possibly from earlier sessions that never ran `/wrapup`), read that block too, and keep it when Step 4 rewrites the file. This is the immutable "why" tier: `.session-handoff.md` is gone next session, `PROJECT_MAP.md` is a regenerated snapshot, `CHANGELOG.md` records *what* shipped — `DECISIONS.md` is the only durable record of *why we chose X over Y*, and what a future session reads instead of re-litigating a settled choice.

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

Codify the session's learnings. If you have a `/learnings`-style skill, invoke it; otherwise do the same work inline. This closes the knowledge loop — patterns, gotchas, and reusable workflows discovered this session get written into the right file (project `AGENTS.md`/`CLAUDE.md`, `PROJECT_MAP.md`, or a rules file) so they compound across sessions rather than evaporating. The process: identify what was learned, categorize by scope, write it down with a dedup check against existing entries (so you update rather than duplicate), and report what was captured and where.

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

### 7. Generate PROJECT_MAP.md + AGENTS.md Context

Skip if `skip-map` argument provided.

Generates/updates TWO files: **PROJECT_MAP.md** (comprehensive, 200 lines max) and the project instruction file (essential ~20-line context, token-efficient): `AGENTS.md` if the repo has one, otherwise `CLAUDE.md`.

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
head -100 AGENTS.md CLAUDE.md README.md 2>/dev/null
cat PROJECT_MAP.md 2>/dev/null
```

#### 7b. Generate PROJECT_MAP.md

Structure:

```markdown
# Project Map

**Last Updated:** YYYY-MM-DD (auto-generated by /wrapup)
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

*Auto-generated by Claude Code's /wrapup command. For deployment details, see CLAUDE.md.*
```

**Update behavior if PROJECT_MAP.md already exists:** preserve the "Notes" section entirely; update Last Updated, Recent Session Work, Tech Stack (if deps changed), Directory Structure (if new dirs), Top 5 Files (if critical files changed); keep other sections unless significant changes detected.

**Fallback if generation fails:** basic template — project name, timestamp, tech stack, directory listing, note that full generation failed.

#### 7c. Update AGENTS.md (or CLAUDE.md) with Essential Context

Critical for token efficiency — new sessions get essential info immediately.

If `AGENTS.md` (or, failing that, `CLAUDE.md`) exists: extract essentials from PROJECT_MAP.md (1-sentence purpose, top 3-5 directories, top 3-5 files, 1-3 quick-start commands). If a `## Project Map` section exists, replace its content (Edit tool, between the heading and the next `##`); otherwise add the section after `## Tech Stack` (or near the top). Keep to 20 lines max. Show: "✅ Updated/Added Project Map section in AGENTS.md" (name the file actually edited).

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

If neither exists: note "No AGENTS.md or CLAUDE.md found - PROJECT_MAP.md created as standalone" and skip.

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

### 9. Commit All Authorized Session Work

For Git repositories, inspect `git status --short`, the full session diff and `git diff --cached --name-only`. Complete affected checks and required changelog updates. Commit all intended session changes, including closure docs, using explicit paths or hunks; verify the staged list before every commit. A commit helper must obey the same scope. Preserve unrelated work and report it separately. Never use blanket `git add -A` in a shared checkout.

In `manual` mode ask before committing. For an owned failure, diagnose and fix within scope, then retry; do not ask a routine retry/skip/abort question. A declined, failed, or blocked commit is `INCOMPLETE`. If detached or mid-merge, resolve safely under Step 1 before writing; do not silently skip and call the session complete.

### 10. Push and Verify the Destination

Do not infer push success from an empty `git log @{upstream}..HEAD`: a missing upstream or failed command is `UNKNOWN`. Fetch the selected remote and inspect the explicit destination refs. For a new topic branch, push explicitly and set tracking (`git push -u "$REMOTE" "$CURRENT_BRANCH"`). Direct-to-base work follows the project's PR policy. In `manual` mode ask before pushing.

Read back the remote branch SHA with `git ls-remote --heads "$REMOTE" "refs/heads/$CURRENT_BRANCH"` and compare it to the intended local commit. Investigate mismatches; a successful command alone is not proof. If a push helper already landed the PR and removed the branch, verify the merge and base instead; do not recreate the merged branch. Fix safe failures within scope; never force-push, or rebase/pull a shared active checkout to bypass a rejection.

### 10b. Land Session Work in the Base Branch

The destination is `$REMOTE/$BASE_BRANCH`, normally `origin/main`, unless explicitly directed otherwise. For each session topic branch that still needs landing:

1. Identify the PR by repository and branch. Inspect state, base, exact head, required checks and explicit holds. Run the project's review/merge gate and resolve real findings within scope. An advisory review is not a new approval requirement; required checks, conflicts, ownership boundaries and explicit pauses still apply.
2. When authorized and checks pass, merge the exact reviewed head. With GitHub, use the project's merge method and `gh pr merge <PR> --match-head-commit <reviewed-sha>` (add `--squash` when that is the project convention). Record the pre-merge head and resulting merge SHA. Read the PR state back even if the CLI reports a local checkout error: the server merge may have succeeded. `--delete-branch` is only an attempt; Step 10d verifies cleanup.
3. Without a PR service, use the documented local merge workflow only in an idle, clean checkout. Update the base with a fast-forward, merge the reviewed topic, push the base, and read it back. Never switch another session's checkout.
4. Fetch and verify the merge/result commit is contained in the selected remote base. For squash/rebase merges, use the PR's recorded head and merge metadata; topic-commit ancestry alone is insufficient. An open PR or a pushed topic branch is not a landed result.

Already on base, no new commits, or merged earlier in the session? Verify the existing result and continue through deployment and cleanup. These conditions do not skip closure checks. Follow-up changes after a merge use a new branch and PR, never the merged branch. In `manual` mode ask before merging.

### 10c. Deploy and Verify What Is Running

Use the project's documented deployment/release path and the session's authorization. Deploy the landed revision to every applicable target, including package/plugin installations or configuration consumers when this is not an application. Honor explicit `local only`, `do not deploy`, or alternate-target instructions; report them as user-directed skips. If the path, target, or necessary authorization is missing, report a blocker rather than inventing one.

Record the intended revision or artifact, command result, and live readback for each target. Verify the deployed SHA/version or artifact contents and the affected behavior using appropriate runtime, HTTP or browser checks. A green health endpoint, a merged PR, or a successful deploy command alone does not prove the new revision is live. CI deployment must finish successfully and be checked at its target. Report a restart/reload still needed to activate an installed plugin.

Use `N/A` only when there is no applicable deployable artifact, with a reason (for example, internal documentation only). A repository without a known deploy path is not automatically `N/A`. A failed or stale deployment remains `INCOMPLETE` and does not prevent safe cleanup of independently verified merged work.

### 10d. Verify Merged Branch and Worktree Cleanup

Run even when no merge happened during wrap-up, the current checkout is on base, or `skip-cleanup` was passed. That flag skips temp/server cleanup only.

**Inventory the repository, not just the current branch.** Refresh remote refs, list local/remote topic branches and `git worktree list --porcelain`, and inspect merged PRs plus branches merged directly into the selected base. Include every branch naming scheme (`feature/`, `fix/`, `chore/`, `release/`, bot branches, and unprefixed names). Protect the default/base branch and other documented long-lived branches. Limit mutations to this repository and authorized related checkouts, not a fleet-wide sweep.

For each candidate, record the branch, current local and remote tip, merged PR/result, associated worktree paths, and ownership/activity:

- **Prove all current work is landed.** Direct merge ancestry can establish this. For a squash/rebase merge, verify the PR is merged into the intended base and its recorded head matches the candidate tip; verify the merge result is in the base. Check local and remote tips separately. New commits after the merge, an open PR reusing the branch name, or ambiguous evidence means keep it and report why. `git branch --merged` alone misses squash merges; a `[gone]` upstream or an old merged PR alone proves nothing about today's tip.
- **Remove completed temporary worktrees first.** Account for every worktree created during the session, including detached worktrees, plus inactive worktrees attached to verified merged branches. Inspect tracked, untracked and ignored files for unique local data, and confirm no other session/process is using the path. Move this session out to an existing safe checkout before removal. Use `git worktree remove <path>` only after wanted work/data is committed, pushed, or preserved through an authorized archival path. Never force-remove a dirty/active worktree or use `rm -rf` to bypass Git. Preserve the primary/shared checkout and intentional persistent checkouts.
- **Delete the verified topic branch locally and remotely.** Require exclusive branch ownership through deletion; if another writer may move the ref, retain it until coordination or an authorized atomic expected-tip deletion is available. Recheck tips and ownership immediately before deletion. Use `git push "$REMOTE" --delete <branch>` if the remote branch remains, then `git branch -d <branch>`. After a squash merge, `-D` is allowed only when the exact current local tip was independently proven merged and no worktree/session holds it. Never blanket-delete branches from a list of names or delete an active session's branch.
- **Read back every deletion.** `git ls-remote --heads "$REMOTE" "refs/heads/<branch>"` must succeed with no matching ref; `git show-ref --verify --quiet "refs/heads/<branch>"` must return the missing-ref status. Confirm each removed worktree is absent from both `git worktree list --porcelain` and the filesystem. If registrations are stale, inspect a prune dry run before pruning; pruning registrations is not directory removal. Distinguish network/command errors from absence.

Keep an explicit list of retained branches/worktrees with owner, reason and next action. A blocked session-owned worktree or merged-branch deletion keeps closure `INCOMPLETE`; an unrelated active or documented persistent checkout is a reported exclusion, not something to destroy. Do not claim cleanup from `gh pr merge --delete-branch`, auto-delete settings, a clean current checkout, or removal of only the worktree.

### 11. CHANGELOG.md Audit

Skip if not a git repo, or if the commit skill ran in Step 9 (it updates `CHANGELOG.md` automatically).

```bash
git log -1 --format="%h %s" 2>/dev/null
head -20 CHANGELOG.md 2>/dev/null
```

If `CHANGELOG.md` doesn't exist or looks stale: show informational note "ℹ️  CHANGELOG.md may need updating for recent changes" — informational only, don't block or prompt.

### 12. Verify Closure and Report

Rerun status, staged-path and remote checks after the last file write. Commit/push/land any new intended tracked changes and redeploy if they affect the shipped artifact. Keep local ignored handoff files and unrelated work explicit. Recheck the recorded branch/worktree removals.

Report each field, per repository and deployment target when multiple are involved:

```text
Session: COMPLETE | INCOMPLETE | USER-DIRECTED SKIP
Destination: origin/main (or explicit override)
Committed: PASS | INCOMPLETE — session commit(s), remaining owned paths
Pushed/landed: PASS | INCOMPLETE — remote base SHA, PR/merge evidence
Deployed: PASS | INCOMPLETE | N/A | USER-DIRECTED SKIP — target, revision, live check/reason
Branches: PASS | INCOMPLETE | N/A — local and remote absence checks; retained refs and reasons
Worktrees: PASS | INCOMPLETE | N/A — removed paths, registration + filesystem checks; retained paths and reasons
Other work preserved: owners/paths, or none
Documentation/cleanup: operations actually completed
Remaining actions: exact blockers and next steps, or none
```

`INCOMPLETE` takes precedence over `USER-DIRECTED SKIP` whenever an independent required check fails or remains unresolved. `COMPLETE` requires every applicable delivery and cleanup check to pass. `N/A` requires evidence that the step does not apply, not missing evidence. Never say the whole checkout is clean if unrelated changes remain. Any user-directed skip must be visible; do not silently turn it into PASS. The user can exit with unresolved work, but closure remains incomplete. In `force` mode show current Git state and `USER-DIRECTED SKIP — delivery and cleanup not verified`, without claiming completion.

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

## Safety Rules

- **File deletion follows task authorization** — temp-file confirmation rules are in Step 3; verified merged-branch and completed-worktree cleanup follows Step 10d
- **Server shutdown is local-only** — auto-kill only servers THIS session started; confirm for anything else; never touch databases, system services, IDEs, the Claude Code process, or remote/production services
- **NEVER force-commit** — always analyze the diff and write a message that describes it (commit skill or plain git)
- **NEVER push if remote has commits we don't have** — check first
- **Preserve unrelated and active work** — commit all authorized session work, not every file in a shared checkout
- **Never prevent the user from exiting** — report incomplete delivery or cleanup honestly; exit is not completion
- **Always identify deletion targets** before deleting (except the two silent-delete exceptions); verify absence afterward
- **Always preserve manual edits** in PROJECT_MAP.md "Notes"; never restructure a user-customized PROJECT_MAP.md — only update specific sections
- **Always verify git state** before auto-operations (merge, detached HEAD, etc.)

## Manual Mode (Escape Hatch)

`/wrapup manual` restores interactive behavior:
- Step 3: still auto-remove .DS_Store/.bak, but announce counts; ask before shutting down any dev server
- Step 9: ask "Commit these changes?" instead of auto-committing
- Step 10: ask "Push commits?" instead of auto-pushing
- Step 10b: ask "Merge [branch] into [base]?" instead of auto-merging
- Steps 10c–10d: ask before deployment and branch/worktree removal; run read-only verification regardless
- Step 7: ask "Update PROJECT_MAP.md?" instead of auto-generating

All other steps work the same as default mode.
