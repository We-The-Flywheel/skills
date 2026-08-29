---
name: autopilot
description: |
  High-autonomy execution mode — the deliberate opposite of the default cautious,
  escalate-often posture. Decomposes a goal into a task graph, runs a loop
  (built on the ralph-wiggum plugin's Stop-hook mechanism) that dispatches one
  scoped subagent per graph node until the goal is met, and logs every
  independent decision to a structured, append-only file for human review
  afterward. Includes autonomous infrastructure setup for NEW/additive
  resources. Use when the user says "autopilot", "mission mode", "run this
  autonomously", "run to completion", "don't stop to ask me", "keep going
  until it works", or wants a long, low-supervision build session. Has a very
  high bar before interrupting the human — only genuinely irreversible,
  unresolvable decisions escalate; everything else gets a defensible default,
  logged, and the run continues. Aliased as "mission".
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
  - Skill
department: engineering
---

# Autopilot

**Prerequisite:** this skill drives the `/ralph-loop` command (Stop-hook based loop,
stable prompt fed back until a completion promise or max-iterations) rather than
reimplementing it. That command ships in the internal `ralph-wiggum` plugin, not in this
marketplace. If `/ralph-loop` isn't available in your install, either add an equivalent
Stop-hook loop yourself (see the Ralph Wiggum technique — Geoffrey Huntley, 2025) or ask
before assuming this skill can run end-to-end.

The opposite of this fleet's default posture. Default behavior escalates early and often
(see the global `CLAUDE.md` "Escalation Protocol" and "Path-of-Least-Resistance Guard").
Autopilot inverts the threshold: pick a defensible default, log the reasoning, keep going.
It does not remove the hard-gate list below — it changes what counts as "ambiguous enough
to stop for."

Prior art this builds on (don't re-derive, read these if you need the mechanics):
Factory AI's "Missions" (milestones → features, fresh-context worker per feature, a
distinct validator role, structured decision logging via OpenTelemetry) and the Ralph
Wiggum technique (stable prompt fed back on Stop, filesystem/git as memory instead of
conversation history). This skill adds a task graph and a decision log on top of the
loop primitive this repo already has in `plugins/ralph-wiggum/` — it does not reimplement
the loop.

## Step 0 — Scope negotiation (once, up front, before looping)

**First check for a crashed or interrupted prior run**: if `.claude/autopilot-graph.local.json`
already exists and no `<promise>` ever fired for it (the ralph-loop state file
`.claude/ralph-loop.local.md` is gone but the graph has non-`validated` nodes), this is a
resumption, not a fresh start. Tell the human what you found (node counts by status, last
decision-log entry) and confirm whether to resume or discard and restart. Don't silently
pick either.

For a genuinely fresh run, ask the human exactly once, before starting the loop, for
whatever isn't already clear:
- The goal and what "done" looks like (the exit criteria in Step 4 need a concrete target).
- Any additions to the hard-gate list below specific to this task (e.g. "don't touch the
  billing table" or "staging only, never prod").
- A sane `--max-iterations` ceiling as a safety valve (default to 300 if the user has no
  opinion — this bounds runaway loops, not the ambition of the task).

Do not ask again after this. Factory's Missions do scoping up front and then run
unattended — mirror that. Anything else that comes up mid-run either gets resolved
autonomously (Step 3) or hits the hard-gate list (Step 2) — there is no third category of
"check in with the human for a status update."

## Step 1 — Initialize state (four files, all `.local` so they don't get committed by accident unless the user wants the log kept)

Before creating anything, write `.claude/autopilot.lock` containing the start timestamp
and a one-line goal summary. Its presence means a run is active in this directory — if
you find one already there and it's not the crash-resumption case above, stop and tell
the human two autopilot runs would collide here rather than starting a second one.
Remove the lock file as the very last action when the loop ends (success or escalation).

All writes to the JSON/JSONL state files below must be atomic: write to a temp file in
the same directory, then rename over the target. A crash mid-write must never leave a
half-written graph or log — that's how resumption (above) stays trustworthy.

Create in the project root:

**`.claude/autopilot-goal.local.md`** — the confirmed goal, exit criteria, any
task-specific hard-gate additions from Step 0, and a running `## Resources created this
run` list. Every time a node creates something that didn't exist before (a service, a
DNS record, a file, a branch), append it here immediately. This list is the literal
definition of "new" for the infra hard-gate in Step 2 — if it's not on this list, treat it
as pre-existing and gated, even if it looks like something you'd expect to be new.

**`.claude/autopilot-graph.local.json`** — the task graph:
```json
{
  "goal": "...",
  "nodes": [
    {"id": "n1", "title": "...", "depends_on": [], "status": "pending", "attempt_count": 0, "validation": "..."},
    {"id": "n2", "title": "...", "depends_on": ["n1"], "status": "pending", "attempt_count": 0, "validation": "..."}
  ]
}
```
`status` is one of `pending`, `in_progress`, `validated`, or `blocked` (3 failed attempts —
see Step 3's watchdog clause; a `blocked` node needs a human, not a 4th retry). Break the
goal into nodes the size of "one subagent dispatch" — a node should be independently
verifiable, not a whole feature. Milestones are just nodes whose children all depend on
them; you don't need a separate milestone concept, dependency edges are enough.

**`.claude/autopilot-decisions.local.jsonl`** — empty file, one JSON object per line,
append-only, never edited or rewritten. This is the artifact a human reviews afterward —
treat every line as permanent once written.

## Step 2 — The hard-gate list (always escalates, autonomy setting doesn't matter)

These are the same category the global Escalation Protocol already names, restated here
because this skill's whole point is inverting the threshold everywhere else:

- Spending money, creating billing/payment configuration, or any financial transaction.
- Creating credentials, API keys, secrets, or accounts under someone's identity.
- Deleting or destructively modifying production data, or any `DROP`/`TRUNCATE`/bulk
  delete against a database that isn't a disposable dev/test instance you created this run.
- Auth/authorization logic, session handling, token management, encryption/permissions.
- **Infrastructure: additive is autonomous, destructive or conflicting is not.** Standing
  up a new service, a new DNS record for a new hostname, a new vhost, a new systemd unit —
  proceed. Modifying or removing an EXISTING production resource, or any resource you
  didn't create this run — stop. (This is not hypothetical: an earlier session hit exactly
  this when a target hostname turned out to already be serving a different production app;
  the correct move was to stop and report the conflict, not guess past it. Do the same.)
- `git push --force`, `git reset --hard` on a shared/published branch, deleting branches
  you didn't create this run.
- Publishing content, sending messages, or taking any action visible to third parties
  under the user's identity or the organization's identity (emails, social posts, PRs on
  repos you don't own, Slack/Discord messages to real humans).
- Anything the user added in Step 0.

Hitting one of these: stop the loop (see "Ending the loop" below), write the specific
blocker and the decision you'd otherwise make, and wait for a real human turn. Do not
paraphrase this as "checking in" — it's a hard stop, not a status update.

## Step 3 — The loop body (this is what gets fed back on every Stop-hook iteration)

Start the loop via the existing `/ralph-loop` command from `plugins/ralph-wiggum/`
(already installed, already wired to the Stop hook — do not build a second hook
mechanism). The PROMPT argument is the fixed instruction below; `--completion-promise`
is `"AUTOPILOT RUN ENDED"` — note this promise means "the run has ended," not
"the run succeeded." Success and escalation both end the loop the same way; the
distinguishing content is in the final message, not in which promise fired. That keeps
this honest under the ralph-loop's own "don't lie to exit" rule: the run genuinely has
ended either way.

```
/ralph-loop <the instruction block below, as one prompt> --completion-promise "AUTOPILOT RUN ENDED" --max-iterations <N from Step 0>
```

Instruction block (this is what iterates):

> Read `.claude/autopilot-goal.local.md`, `.claude/autopilot-graph.local.json`, and
> `.claude/autopilot-decisions.local.jsonl`.
>
> If any hard-gate item (see the autopilot skill's Step 2 list) blocks the next node:
> write the blocker and the decision you'd otherwise make as your response text, then
> output `<promise>AUTOPILOT RUN ENDED</promise>`. Do not guess past a hard-gate item.
>
> Otherwise, pick the next node with status `pending` whose `depends_on` are all
> `validated`. If none exists and unvalidated/in-progress nodes remain, work on one of
> those. If all nodes are `validated`, go to the finalize step below.
>
> For the chosen node: dispatch a subagent (Agent tool) scoped to only the tools that
> node needs — do not hand a single-file-edit node full Bash+infra access, do not hand
> an infra node write access to unrelated app code. Give it the node's title, the
> relevant slice of the goal, and enough surrounding context to work without re-deriving
> the whole graph. Mark the node `in_progress` before dispatch.
>
> When the subagent reports back: run the node's validation (tests, a smoke check, a
> curl, whatever "verified" means for that node — write it into the node's `validation`
> field when you create the node, don't invent verification standards ad hoc per node).
> If it passes, mark the node `validated`. If it fails, increment the node's
> `attempt_count` (start every node at 0) and either retry with adjusted instructions or
> split it into smaller nodes — append a decision-log entry either way explaining what
> failed and what you changed. **This is the loop's watchdog: a node that hits 3 failed
> attempts is not retried a 4th time.** Mark it `blocked`, log why, and treat it as a
> hard-gate hit for the orchestrator — this is the "cannot be resolved by trying" case
> Step 2 already covers, not a new escalation path. Retrying the same failing approach a
> 4th time burns iterations without changing the outcome; a human unblocking it beats an
> infinite loop of near-identical attempts.
>
> For every non-trivial choice made this iteration (which approach, which library, how
> to resolve an ambiguity, which of two reasonable defaults you picked, why a node was
> split or retried) append exactly one line to
> `.claude/autopilot-decisions.local.jsonl`:
> `{"timestamp": "<ISO8601>", "node": "<node id or 'orchestrator'>", "decision": "<one-line summary>", "reasoning": "<why>", "alternatives_considered": ["..."], "reversibility": "reversible|irreversible", "action_taken": "<what actually happened>"}`
> Trivial mechanical steps (reading a file, running a test) don't need a log line — this
> is a decision log, not an activity log.
>
> Commit any files the node produced with a small, scoped commit message before moving
> to the next node — Ralph-style atomic commits, so a bad node can be reverted without
> losing earlier progress.
>
> If `.claude/autopilot-decisions.local.jsonl` has grown past ~150 lines, roll it so it
> doesn't eat the context budget of every future iteration: move the file as-is to
> `.claude/autopilot-decisions.archive-<N>.local.jsonl` (never delete or summarize-over
> the raw lines — the archive is still the full audit trail, just not the active file),
> start a fresh empty `.claude/autopilot-decisions.local.jsonl`, and add one line to
> `.claude/autopilot-goal.local.md` noting the archive file exists and roughly what it
> covers. A human reviewing later reads all archive files plus the active one, in order.
>
> **Finalize step** (all nodes validated): write a closing summary to
> `.claude/autopilot-decisions.local.jsonl` (one final entry, `node: "orchestrator"`,
> summarizing node count, decision count, and the working deliverable), then output
> `<promise>AUTOPILOT RUN ENDED</promise>`.

## Step 4 — Exit criteria (dual — both required)

1. The graph's terminal nodes are all `validated` against their own stated validation
   check — a working deliverable, not just code that was written.
2. The decision log is finalized (closing entry present) and human-readable.

Declaring done on code alone, without the log, is not done. The log is the point of this
skill — it's what lets a human trust a long unattended run after the fact instead of
re-reviewing every file from scratch.

## Ending the loop

Whether by success or by hard-gate escalation, the `<promise>AUTOPILOT RUN ENDED</promise>`
tag ends it (same mechanism as `/cancel-ralph`, which also just removes
`.claude/ralph-loop.local.md` if you need to abort manually mid-run). Remove
`.claude/autopilot.lock` as the last action before the promise fires — a leftover lock
file is what would make the crash-resumption check in Step 0 misfire on the next run.
After it ends, report to the human: node count, validated count, decision count, whether
this was a clean finish or an escalation, and the path to the decision log (plus any
archive files from log rolling).
