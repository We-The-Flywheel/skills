---
name: longterm
aliases: [right-approach, do-it-right]
description: Use when several approaches are on the table and you want the one that's correct for the long term, not the fastest to ship. Triggers on "/longterm", "take the right long-term approach", "do it the right way even if it takes longer", "pick the durable option", "no shortcuts". Picks and proceeds with the option that ages best, accepting more time/effort now.
---

# Long-Term Approach

Pick and execute the option that is **correct for the long term** — the one a senior engineer would still be glad to live with in a year — even when it costs more time or effort now. Bias hard against shortcuts, patches over bad foundations, and "good enough for today."

**Announce at start:** "Using the longterm skill — optimizing for the durable approach, not the fastest."

## Decision rule

When multiple options exist, score each against these, in order:

1. **Correctness & root cause** — fixes the actual problem, not a symptom. No suppressing errors, no patching over a bad foundation. (Counters LLM commitment bias: if today's foundation is wrong, scrap it and do the elegant thing.)
2. **Maintainability** — the next person (or you in 6 months) understands and extends it without archaeology. Clear names, obvious control flow, fits existing patterns.
3. **Robustness** — handles edge cases, failure modes, and realistic scale, not just the happy path.
4. **Reversibility & blast radius** — avoids one-way doors and hidden coupling; easy to change later.
5. **Total cost over time** — accepts more work now to avoid compounding debt, rework, and on-call pain later.

**Explicitly deprioritize:** speed-to-ship, fewest lines changed, "we can clean it up later," and avoiding unfamiliar-but-correct patterns.

Do **not** confuse "long-term" with "over-engineered." The durable choice is still the *simplest* one that satisfies the rule above — don't add abstractions, config, or generality the problem doesn't have. If a senior engineer would call it overcomplicated, it's the wrong long-term choice too.

## Procedure

1. **Lay out the real options** — 2–4 genuine candidates, not strawmen. One line each.
2. **Name the tradeoff** — for each, the cost now vs. the cost later. Be honest about what taking the right path actually costs (time, unfamiliar tooling, bigger diff).
3. **Pick** — apply the decision rule. State the choice and the one-sentence why.
4. **Flag if it crosses an escalation line** — if the durable choice touches auth, schema/data migrations, billing, infra/DNS/SSL, security, or external API contracts, **stop and confirm** before proceeding (per global Escalation Protocol). Otherwise proceed autonomously.
5. **Proceed** — implement the chosen approach fully. Don't half-build it and leave a TODO that recreates the shortcut you just rejected.
6. **Verify** — tests / build / runtime evidence, per the project's verification norms. The last 1% is where shortcuts hide.

## When NOT to use this

- Throwaway scripts, spikes, and prototypes explicitly meant to be discarded — there, fastest-that-works is correct.
- Genuine emergencies (prod down) where a stopgap now + the durable fix logged as a follow-up is the right sequence. Say so explicitly and capture the follow-up.

## Output shape

Keep it tight:

```
Options:
  A — <one line>   (now: cheap / later: expensive)
  B — <one line>   (now: more work / later: cheap)  ← choosing
  C — <one line>   ...

Choosing B: <one-sentence why, per decision rule>.
[Escalation: <only if a line is crossed>]
```

Then build it.
