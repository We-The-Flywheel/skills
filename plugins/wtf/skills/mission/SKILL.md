---
name: mission
description: |
  Multi-agent build mode for long, low-supervision work. An orchestrator plans
  with the human, writes a validation contract (countable assertions that
  define done) before any code, and splits the work into milestones and
  features. Fresh-context workers build one feature at a time; separate
  validators (scrutiny: lint, types, tests, code review; user-testing: drive
  the real app like a QA engineer) check each milestone against the contract.
  Unsatisfied assertions become follow-up features. Every role transition
  leaves a structured handoff on disk. Use when the user says "mission",
  "mission mode", "run this autonomously", "run to completion", "multi-day
  build", "autopilot", or wants a large feature built end to end with the
  human only at the start and the end. Replaces the former autopilot skill.
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

# Mission

A mission is a long build run by three kinds of agent that never grade their own work.
You, in the main session, are the **orchestrator**. You plan, delegate, and keep the
books. **Workers** build. **Validators** check. The human sets the objective and the
architecture at the start, answers only irreversible questions in the middle, and
reviews at the end.

Inspired by Factory AI's Missions, as described by Luke Alvoeiro in "The Multi-Agent
Architecture That Actually Ships" (AI Engineer). This is an independent adaptation to
Claude Code primitives, not Factory's implementation.

## Vocabulary

- **Delegation**: the orchestrator hands one scoped piece of work to one agent. The only
  way work moves.
- **Creator-verifier**: whoever wrote the code never decides whether it is done. A
  validator with no stake in the implementation does.
- **Direct communication**: agents talking to each other peer to peer. **Avoided.**
  Workers and validators never message each other; everything flows through the
  orchestrator and the files in `.mission/`.
- **Negotiation**: settling a shared resource or architectural choice. The orchestrator
  decides, records it in the decision log, and the decision binds every later agent.
- **Broadcast**: constraints every agent must see. Here that is the contract, the
  architecture notes, and the decision log, which every dispatch prompt points to.
- **Validation contract**: the list of countable assertions that define done, written
  before implementation and independent of it.
- **Structured handoff**: the fixed-format report every agent writes when it finishes.

## State on disk

Everything lives in `.mission/` at the project root. Files, not conversation, are the
memory: a compacted or restarted orchestrator rebuilds itself from them.

```
.mission/
  brief.md          objective, scope, architecture decisions, human-added hard gates
  contract.md       validation contract (assertions + status)
  plan.md           milestones -> features, each feature mapped to assertion ids
  decisions.jsonl   append-only decision log
  handoffs/         one file per agent run: <NNN>-<role>-<feature-or-milestone>.md
  lock              present while a mission is active
```

Ask the human whether `.mission/` should be committed (a reviewable audit trail) or
gitignored. Default: commit it.

If `.mission/lock` already exists, this is a resumption or a collision. Read `plan.md`,
the contract, and the newest handoff, tell the human what state you found, and ask
whether to resume or restart. Do not pick silently.

## Phase 1: Plan with the human (orchestrator)

This is the one long conversation. Spend it well.

1. Read the codebase enough to ask good questions. Parallel read-only exploration
   subagents are fine here.
2. Ask clarifying questions until the objective, scope, non-goals, and architecture
   decisions (stack, data model, service boundaries, anything costly to reverse) are
   settled. Record them in `brief.md`. Ask the human for task-specific hard gates too
   ("never touch the billing tables", "staging only").
3. Write `contract.md` **before any code exists**. Each assertion is observable and
   countable, phrased as behavior, not implementation:

   ```
   ## Milestone M1: accounts
   - [ ] A1  POST /signup with a new email returns 201 and the user can log in
   - [ ] A2  Signing up twice with the same email returns 409, no second row
   - [ ] A3  The login form shows an inline error on a wrong password (UI)
   ```

   Tag assertions that need a real UI or browser with `(UI)`: those go to the
   user-testing validator. Aim for coverage, not elegance. A large feature has dozens
   to hundreds of assertions.
4. Write `plan.md`: milestones in order, features inside each, and for every feature the
   assertion ids it is meant to satisfy. Every assertion must be owned by at least one
   feature. Size a feature so one worker can finish it in one clean context.
5. Show the human the brief, contract, and plan. This is the approval gate. After it,
   the mission runs without status check-ins.

## Phase 2: Execute (serial)

**One writer at a time.** Only one worker or validator runs at any moment, because
parallel writers step on each other, duplicate work, and make conflicting design
choices. Parallelize only read-only work: search, research, and code review fan-out
inside a validator.

For each feature in `plan.md`, in order:

1. **Delegate to a worker** with the Agent tool. The prompt contains: the feature, its
   assertion ids with their text, the paths to `brief.md` and `decisions.jsonl` (the
   broadcast), the previous handoff if it touches this area, and the handoff format
   below. Give it only the tools the feature needs. The worker starts from a clean
   context; do not paste the conversation history into it.
2. The worker implements, runs the relevant tests, commits with a scoped message, and
   writes its handoff to `.mission/handoffs/`.
3. Read the handoff. If it reports undone work or a discovered issue, decide: fold it
   into the next feature, add a new feature, or log it and move on. Record the choice in
   `decisions.jsonl`.

When every feature in a milestone has a handoff, validate the milestone.

## Phase 3: Validate each milestone (creator-verifier)

Run the two validators one after the other. Neither may be the agent that wrote the
code, and neither fixes anything: they report.

**Scrutiny validator.** Runs lint, type checks, and the full test suite and records the
exit code of each. Spawns read-only code-review subagents in parallel over the
milestone's diff (correctness, security, consistency with `brief.md`). Checks each
non-UI assertion against the running code and marks it satisfied or unsatisfied with
evidence.

**User-testing validator.** Starts the app and drives it the way a QA engineer would: a
browser automation tool, computer use, or curl for APIs. Exercises every `(UI)`
assertion plus the obvious unhappy paths around it (empty input, wrong password, reload
mid-flow). Records what it did and what it saw, with screenshots or response bodies
where it can.

Both write a structured handoff. Then the orchestrator updates `contract.md`:

```
- [x] A1  ... (satisfied: handoffs/014-scrutiny-M1.md)
- [ ] A3  ... (UNSATISFIED: error renders below the fold, handoffs/015-usertest-M1.md)
```

**Every unsatisfied assertion becomes a targeted follow-up feature** in `plan.md`,
scoped to exactly that assertion and the evidence of failure. Run those features
(Phase 2), then re-validate only the affected assertions. A milestone is closed when all
of its assertions are satisfied. Then move to the next milestone.

Watchdog: an assertion that stays unsatisfied after three follow-up rounds is not
retried a fourth time. Mark it `BLOCKED` in the contract, log why, and treat it as an
escalation.

## Structured handoff format

Every worker and validator ends by writing this file, and the orchestrator reads it
before the next delegation:

```markdown
# Handoff 014: scrutiny, milestone M1
## Completed
- what was done, with commit shas
## Not done
- what was skipped or left partial, and why
## Commands run
- `npm run lint` -> exit 0
- `npm test` -> exit 1 (2 failures, see below)
## Discovered issues
- anything found outside the assigned scope
## Assertions
- A1 satisfied (evidence), A3 unsatisfied (evidence)   # validators only
## Procedure adherence
- did it follow the brief and the handoff format; any deviation and why
```

"Commands run" with real exit codes is not optional. A handoff that claims tests pass
without the command and its exit code is treated as unverified.

## Decision log

One JSON object per line in `decisions.jsonl`, append-only, never rewritten:

```json
{"ts":"<ISO8601>","by":"orchestrator|worker|validator","feature":"F7","decision":"...","why":"...","alternatives":["..."],"reversible":true}
```

Log real choices (approach, library, how an ambiguity was resolved, why a feature was
split or added), not activity. The human reads this afterward to trust the run without
re-reading every diff.

## Escalation: when the human is interrupted

Mid-mission, pick a defensible default, log it, and continue. Stop and ask only for an
**irreversible** decision or a hard gate:

- spending money or creating billing configuration
- creating credentials, keys, or accounts under someone's identity
- destructive changes to data or infrastructure you did not create in this mission
- auth, permissions, or encryption logic not settled in `brief.md`
- force-pushing, rewriting published history, deleting branches you did not create
- anything visible to third parties: publishing, sending messages, opening PRs on
  others' repos
- an architecture change that contradicts `brief.md`
- a `BLOCKED` assertion
- any gate the human added in Phase 1

When you stop, write the blocker, the decision you would make, and its evidence, then
wait. Do not guess past it.

## Phase 4: Finish

The mission is done when every assertion in `contract.md` is satisfied (or explicitly
`BLOCKED` and escalated) and a final full scrutiny run passes. Append a closing entry to
`decisions.jsonl`, remove `.mission/lock`, and give the human the review packet:

- assertions satisfied / blocked / total
- milestones, features, and follow-up features run
- the final scrutiny exit codes and the user-testing evidence
- the three to five decisions most worth a second look, with log line references

The human's final review is part of the process, not a courtesy.
