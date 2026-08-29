---
name: mission
description: |
  Alias of the autopilot skill (renamed candidate during design, kept as an
  alias since "mission" echoes Factory AI's "Mission Mode" which inspired
  it). Use when the user says "mission mode", "mission", or any of the
  autopilot triggers — high-autonomy execution with a task graph, scoped
  subagent dispatch per node, and a structured decision log for human
  review. See the autopilot skill for the full instructions; this file only
  exists because Claude Code skill aliasing requires a real directory, not a
  symlink or frontmatter alias field (both are silently inert).
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

# Mission (alias of autopilot)

This is an alias. Follow `skills/autopilot/SKILL.md` in full — same steps, same hard-gate
list, same loop mechanics, same decision-log format. Nothing in this file overrides or
adds to that skill; it exists only so "mission" resolves as a skill name.
