---
name: grilling
description: >-
  Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to
  stress-test their thinking, or uses any 'grill' trigger phrases. Also collects the open
  questions and pending decisions already in the thread and asks them: use when the user says
  /questions, "what's open", "ask me the open questions", "repeat the open questions", or
  "what do you need from me".
department: engineering
---

Two modes, one method:

- **Grill** (default): interview the user about a plan until you share one understanding of it.
- **Open questions**: when the user asks what is open or what you need from them, skip the
  interview. Collect what is already waiting on them (see "Open questions mode" below), treat
  those items as the frontier, and ask them the same way.

Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the whole frontier in one round: number each question and give your recommended answer. Then wait for the user's answers before the next round.

Format a round like so:

```
❓ **Q1** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>

---

❓ **Q2** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>
```

Each round the user answers reshapes the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one.

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), dispatch a sub-agent to find it; don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for the sub-agent to report; ask the rest of the frontier now. The _decisions_ are the user's: put each to them and wait.

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you have reached a shared understanding.

## Asking with a picker

If the harness has an interactive question tool (Claude Code's `AskUserQuestion`), ask each
choice-shaped question through it instead of the markdown format, so the user answers by
clicking:

| Kind of question | How to ask |
|---|---|
| Choice between named options | multiple choice, 2 to 4 options |
| Yes/no approval (merge, spend, deploy, go) | multiple choice: approve, not now, plus one real alternative if one exists |
| Number or amount | 2 to 3 concrete values; the tool's "Other" covers the rest |
| Genuinely open ("what should the headline be") | markdown format above, after the picker |

- Put your recommended answer first and add "(Recommended)" to its label. Each option's
  description says what happens if it is picked, in one line.
- The tool takes up to 4 questions per call. A bigger frontier goes in batches of 4, most
  blocking first; say "batch 1 of 3" before each call.
- Headers are 12 characters or fewer; use the question's code (`Q3`).
- Use `multiSelect` only when the options are not mutually exclusive.

Without such a tool, use the markdown format.

## Open questions mode

Scan, newest first:

- this conversation: items coded `Q<n>`, `D<n>`, `O<n>`, `F<n>` or `R<n>` that wait on the user, or
  marked "decision needed", "approve", "your call" or "choose one", plus PRs held for a human;
- the repo's session handoff file (`.session-handoff.md`), under "Open questions", if one exists;
- any design doc's "Open decisions" table touched this session.

Drop anything already answered in the thread. Keep each item's original code (`Q17`) so the
answers map back. Never ask what you can settle from the code, the docs or a sensible default:
state the default in one line instead.

## Recording answers

After each round:

- restate each decision in one line (`Q17: reword O6`);
- an answer approves exactly that item, nothing broader;
- when the repo keeps them, update "Open questions" in the session handoff file and add settled
  choices to `DECISIONS.md`;
- list anything still open, with its code.
