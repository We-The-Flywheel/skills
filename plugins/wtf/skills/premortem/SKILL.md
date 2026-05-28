---
name: premortem
description: |
  Run a pre-mortem on a plan or decision before committing to it. Imagine it's
  months in the future and the plan has already failed, then work backward to find
  exactly why. Use when the user says "premortem", "premortem this", "pre-mortem",
  "stress-test this plan", "how could this fail", "red-team this decision", "what am
  I missing", or is about to commit to something costly — a launch, hire, pricing
  change, partnership, fundraise, rebrand, big purchase, or career/personal move.
  Spawns one investigator per failure mode in parallel, then synthesizes the findings
  into the most likely failure, the most dangerous one, the biggest hidden assumption,
  a revised plan, and a pre-commit checklist.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write
  - Task
  - AskUserQuestion
---

# Premortem: find out how the plan dies before you live it

You run a **premortem** — Gary Klein's decision technique, which Kahneman called the
single most valuable one he knew. Researchers call the underlying effect *prospective
hindsight*: people are markedly better at naming why something failed when they assume
it *already* has, versus asking the open-ended "what could go wrong?"

Your default mode is helpful and optimistic. This skill deliberately suspends that. For
the duration of a premortem you are not a cheerleader — you are the person in six months
explaining, with the benefit of hindsight, exactly how this plan fell apart. Be specific,
be honest, and do not soften.

## Step 1 — Gather context (don't ask for a brief you can infer)

First mine what you already have:
- The current conversation — the plan is often already described above.
- The workspace — `Read`/`Grep`/`Glob` for `PLAN.md`, `SPEC.md`, `README`, memory/notes,
  or anything the user referenced.

You need four things to run a useful premortem:
1. **The plan** — what's being committed to, in a sentence or two.
2. **The stakes** — what success looks like, and what being wrong costs (time, money, trust).
3. **The horizon** — when "did it work?" gets answered (launch date, 90 days, end of quarter).
4. **The constraints** — who's involved, budget, deadlines, dependencies.

If the conversation already gives you enough, **just run** — don't interrogate the user.
If something essential is missing, use `AskUserQuestion` to ask **one focused question at
a time** until you can run a real premortem. Never ask for things you can reasonably infer.

## Step 2 — Set the frame and generate the failure modes

Adopt the frame explicitly: *"It is [horizon] from now. This plan failed. Here is why."*

Then list **every genuine reason it could have died** — specific to *this* plan, not a
generic risk catalogue. Let the count be whatever is real: it might be 4, it might be 9.
Do not pad to a round number, and do not merge distinct failures to look tidy. Each failure
mode should be a one-line, concrete cause (e.g. "the partner goes quiet by month 3 and you
carry 80% of the work" — not "execution risk").

## Step 3 — Spawn one investigator per failure mode, in parallel

This is what makes a premortem more than a checklist. For **each** failure mode, spawn a
sub-agent with the `Task` tool. **Launch them all in a single message** (multiple `Task`
calls at once) so they run concurrently. Use a general-purpose agent; `model: "sonnet"` is
a good default for depth-vs-cost.

Give each agent the full plan context **plus its one assigned failure mode**, and ask it to
return a tight case study (≤200 words):

```
You are running one branch of a premortem. Context: <plan, stakes, horizon, constraints>.

It is <horizon> from now and the plan failed. The specific cause you are investigating:
"<this failure mode>".

Write a short, concrete case study of how this failure actually played out over time —
month by month if useful. Then state, clearly labelled:
- THE UNDERLYING ASSUMPTION this failure exposes (the thing the plan quietly bet on).
- THE EARLIEST WARNING SIGN — an observable signal the user would actually see, with a
  threshold where possible (e.g. "more than 3 unanswered messages in a week").
- A LEADING INDICATOR to track from day one.
Be specific to this plan. No generic risk language. Do not spawn further sub-agents.
```

(Depth limit: sub-agents cannot spawn their own sub-agents — you do all the dispatching.)

## Step 4 — Synthesize

Once the investigators report back, pull everything together:

- **Most likely failure** — the one to address first.
- **Most dangerous failure** — the one worth insuring against even if less likely (high cost
  × plausible). Call out when "most likely" and "most dangerous" differ — that gap is the
  insight.
- **The single biggest hidden assumption** — the load-bearing belief that, if wrong, takes
  the whole plan with it. Name the one the user would never have written down themselves.
- **Revised plan** — concrete changes, each mapped to the specific failure mode it defuses.
- **Pre-commit checklist** — 3–5 things to verify *before* committing, each phrased as a
  check with a clear pass/fail.

## Step 5 — Deliver

Write a markdown report to the workspace at `premortem-<slug>-<YYYY-MM-DD>.md` containing:
the frame, the failure modes, each investigator's case study, and the full synthesis — so
the user can dig back into any single branch's reasoning later. Then give a concise summary
in chat led by the most dangerous failure and the hidden assumption.

If the user explicitly wants a visual artifact, additionally render a self-contained HTML
version (`premortem-<slug>-<YYYY-MM-DD>.html`) — plain inline CSS, no build step or
dependencies. Markdown is always the default deliverable.

## Guardrails

- **Specific, not generic.** "Audience trust doesn't transfer to the joint product" beats
  "marketing risk." If a failure mode reads like it could apply to any plan, sharpen it.
- **Observable warning signs.** Every failure needs a signal the user could actually notice
  early, ideally with a threshold — that's what makes a premortem actionable.
- **Don't flip back to cheerleading** in the synthesis. The revised plan can be encouraging;
  the diagnosis must stay honest.
- **Thin context → ask first.** A premortem on a vague plan produces vague failures. If you
  can't name the stakes and horizon, ask before running.
