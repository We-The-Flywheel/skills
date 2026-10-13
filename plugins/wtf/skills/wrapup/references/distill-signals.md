# Step 4: signal types and memory rules

Moved verbatim from `SKILL.md`; read at the step that points here.

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
