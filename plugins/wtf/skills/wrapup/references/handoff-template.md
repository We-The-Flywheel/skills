# Step 4: session handoff template

Moved verbatim from `SKILL.md`; read at the step that points here.

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
