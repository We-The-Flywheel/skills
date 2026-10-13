# Step 5: harvest decisions, intro and filter (5a)

Moved verbatim from `SKILL.md`; read at the step that points here.

Promote the **durable** decisions from the ephemeral `## Decisions made` staging buffer (Step 4) into a committed, append-only `DECISIONS.md` at the repo root. If a hook records decisions automatically (for example an `## Decisions made (auto-captured)` block that a PreCompact/SessionEnd hook writes into `.session-handoff.md`, possibly from earlier sessions that never ran `/wrapup`), read that block too, and keep it when Step 4 rewrites the file. This is the immutable "why" tier: `.session-handoff.md` is gone next session, `PROJECT_MAP.md` is a regenerated snapshot, `CHANGELOG.md` records *what* shipped — `DECISIONS.md` is the only durable record of *why we chose X over Y*, and what a future session reads instead of re-litigating a settled choice.

Runs **before** the learnings step (Step 6) and PROJECT_MAP (Step 7) so Architecture Highlights can derive from a freshly-written log, and **before** the commit (Step 9) so the file ships in this session's commit.

**5a. Filter — what qualifies.** Log an entry **only** when all hold:
- It resolved a real fork (architecture, tooling, schema, data model, process, API contract, "X over Y").
- It has lasting rationale — a future session could otherwise reasonably re-debate it.
- There was a rejected alternative worth recording.

Do **not** log: implementation mechanics or routine bug fixes (commits/`CHANGELOG.md`), reusable patterns or gotchas (the learnings step, Step 6), or ephemeral task choices. If nothing qualifies, skip silently — never force an entry.
