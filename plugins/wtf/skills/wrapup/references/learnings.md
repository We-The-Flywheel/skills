# Step 6: codify learnings

Moved verbatim from `SKILL.md`; read at the step that points here.

Codify the session's learnings. If you have a `/learnings`-style skill, invoke it; otherwise do the same work inline. This closes the knowledge loop — patterns, gotchas, and reusable workflows discovered this session get written into the right file (project `AGENTS.md`/`CLAUDE.md`, `PROJECT_MAP.md`, or a rules file) so they compound across sessions rather than evaporating. The process: identify what was learned, categorize by scope, write it down with a dedup check against existing entries (so you update rather than duplicate), and report what was captured and where.

**Review interactions and mistakes explicitly.** Re-read user corrections, clarifications and repeated requests, failed commands and checks, wrong assumptions, unnecessary retries, and approaches that needed rework. Include errors you caught yourself and successful recoveries. Distinguish an explicit user preference from an inference; do not turn a one-off request into a universal rule.

For each reusable lesson, record the trigger, what went wrong and why, the better first action, and the evidence or check that confirms it works. Write an actionable prevention rule, not just "be more careful" or a transcript. If the cause or fix is unverified, label it as a hypothesis with the next check; do not preserve it as established guidance.

Search existing guidance first and update the smallest relevant source: project-specific lessons in the project's rules, reusable workflow corrections in the owning skill, and personal preferences in an authorized memory store. Keep instruction files concise indexes and link to details. Ensure the lesson is reachable through instructions future sessions actually read; an overwritten handoff alone is not durable learning. Preserve secrets and private interaction details outside shared/public skills.

Respect the runtime's memory-write policy and skill-edit/release boundaries. This step does not grant permission to edit protected memory or publish a skill. If persistence is unavailable, report the lesson and exact blocked destination without claiming it was saved. When writing is authorized, read back the saved change and report its path and verification state. If review finds no reusable lesson, say so briefly; do not invent one.

Example: after a command fails because an option is unsupported, consult the installed command's help before retrying; save the supported invocation and a help/version check so the next session starts with it.
