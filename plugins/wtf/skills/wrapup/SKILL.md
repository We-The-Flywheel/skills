---
name: wrapup
description: |
  Wrap up a coding session: stop session dev servers, clean temp files, commit and push work, land and verify deploy/branch cleanup, refresh PROJECT_MAP.md and AGENTS.md. Use for "wrapup", "wrap up", "end the session", "finish up". Args: manual, skip-map, skip-cleanup, keep-servers, force.
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

**3c-3e.** Read `references/cleanup-detail.md`: detect other listening dev servers, other temp files, and session `/tmp` scratch. Confirm before killing or deleting anything this session did not start or write (default NO). Never kill non-dev-server processes; local-only.

### 4. Conversation Distill & Handoff

Skip if session was trivial (single Q/A, no code changes), or `force`/`skip-map` provided.

Re-read the conversation from the beginning and extract value that didn't make it into commits or files — implicit standards, decisions, loose threads.

Read `references/distill-signals.md` for the signal-to-action table and the memory rules (non-obvious and reusable only; name the root cause; proved vs. suggested; update in place). If nothing is worth capturing, skip silently.
**Write `.session-handoff.md` in the project root.** Read `references/handoff-template.md` and fill it in (overwritten each session; add to `.gitignore` if absent).

### 5. Harvest Decisions (Durable Decision Log)

Skip if session was trivial, or `force`/`skip-map` provided.

Read `references/decisions-harvest.md` (what to promote from the handoff `## Decisions made` buffer, and the 5a filter for what qualifies). Log an entry only for a real fork with lasting rationale and a rejected alternative; otherwise skip silently.

**5b-5c. Dedup gate and entry format.** Read `references/decisions-template.md`: grep the existing log first (skip identical, supersede reversed, append new), then write the entry in the template format. `DECISIONS.md` is committed, append-only, newest-on-top.

### 6. Codify Learnings

Skip if session was trivial, or `force`/`skip-map` provided.

Codify the session's learnings: read `references/learnings.md` (use a `/learnings`-style skill if installed, else do the same work inline, with a dedup check so entries are updated, not duplicated).

**After learnings are codified, check memory health** (skip if the project has no memory store). Read `references/memory-health.md` for the check script and the consolidate-or-skip judgment table.

### 7. Generate PROJECT_MAP.md + AGENTS.md Context

Skip if `skip-map` argument provided.

Generates/updates TWO files: **PROJECT_MAP.md** (comprehensive, 200 lines max) and the project instruction file (essential ~20-line context, token-efficient): `AGENTS.md` if the repo has one, otherwise `CLAUDE.md`.

#### 7a. Gather Context

Read `references/gather-context.md` and run the commands there.

#### 7b. Generate PROJECT_MAP.md

Read `references/project-map-templates.md` (section 7b) and fill in the structure. Update rules if PROJECT_MAP.md exists: preserve the "Notes" section entirely; update Last Updated, Recent Session Work, Tech Stack (if deps changed), Directory Structure (if new dirs), Top 5 Files (if critical files changed); keep other sections unless significant changes detected. Fallback if generation fails: basic template (project name, timestamp, tech stack, directory listing, note that full generation failed).

#### 7c. Update AGENTS.md (or CLAUDE.md) with Essential Context

Critical for token efficiency — new sessions get essential info immediately.

If `AGENTS.md` (or, failing that, `CLAUDE.md`) exists: extract essentials from PROJECT_MAP.md (1-sentence purpose, top 3-5 directories, top 3-5 files, 1-3 quick-start commands). If a `## Project Map` section exists, replace its content (Edit tool, between the heading and the next `##`); otherwise add the section after `## Tech Stack` (or near the top). Keep to 20 lines max. Show: "✅ Updated/Added Project Map section in AGENTS.md" (name the file actually edited).

Read `references/project-map-templates.md` (section 7c format) for the exact block. Keep to 20 lines max.

If neither exists: note "No AGENTS.md or CLAUDE.md found - PROJECT_MAP.md created as standalone" and skip.

### 8. Session Metrics (Structured Log)

Skip entirely if session was trivial (no commits, no code changes).

Read `references/session-metrics.md` and append one JSONL entry to `.session-metrics.jsonl` (append-only, gitignored).

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

On any failure or unusual state (not a git repo, merge in progress, detached HEAD, failed commit/push/merge/deploy/cleanup, failed doc generation, failed `find`/`lsof`), read `references/error-handling.md` and follow the matching rule.

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

When the `manual` argument is given, read `references/manual-mode.md` first and apply it; all other steps work as in default mode.
