---
name: memory-consolidate
description: Review and consolidate memory files — remove stale entries, merge duplicates, verify code claims still hold. Inspired by Claude Code's internal autoDream pattern.
department: ops
---

# Memory Consolidation

Review all memory files across projects, verify code-specific claims still hold, remove stale entries, merge duplicates. Keeps memory healthy so future sessions get accurate context.

## When to Use

- Manually when memory feels stale or cluttered
- After `/compact` if >30 days since last consolidation
- When memory file count exceeds 20 entries across a project
- Weekly via cron as safety net

## Process

### 1. Scan Memory Files

Find all memory directories and their files:

```bash
find ~/.claude/projects/*/memory -name "*.md" -not -name "MEMORY.md" 2>/dev/null
```

For each project's memory directory, read every `.md` file (excluding MEMORY.md index).

### 2. Grounding Checks

For each memory file, verify code-specific claims:

- **File paths**: If memory references a file path, run `test -f <path>`. If gone, flag as stale.
- **Function/class names**: If memory claims a function exists, `grep -r "function_name" <project>`. If not found, flag.
- **Config flags/env vars**: If memory references an env var, `grep <VAR> ~/.env.shared` (or wherever you keep shared env vars). If missing, flag.
- **Tool/binary references**: If memory says a tool is installed, `which <tool>`. If missing, flag.

### 2b. Evidence-Qualifier Check

An entry that generalizes a single occurrence into an unqualified rule is worse than no entry — future sessions act on it as settled fact. For each memory whose body states a rule:

- Does it trace to a real, specific event, or is it a generic best practice restated? Generic → remove.
- Was the rule **proved** (the failure recurred, the root cause was confirmed against real evidence, or the fix was verified) or only **suggested** (one occurrence, plausible, unconfirmed)? A suggested rule stated unqualified gets edited in place to say so plainly ("seen once, not yet confirmed as a pattern") rather than deleted.
- Does it name a root cause, or only a symptom? Symptom-only entries are weak; if the session that produced it is gone, keep it but note the gap.

### 3. Staleness Check

Flag entries where:
- File's `mtime` is >30 days old AND contains code-specific claims
- The `description` references something that no longer exists
- The content contradicts another memory file of the same type

### 4. Merge Duplicates

Within each project:
- Find memories with overlapping `description` fields (>70% word overlap)
- Merge into single file, keeping the most recent/specific content
- Update the `name` and `description` to reflect merged scope

### 5. Update Index

For each project where changes were made:
- Re-read MEMORY.md
- Remove lines pointing to deleted files
- Add lines for any new merged files
- Keep each entry under 150 characters

### 5b. Skill Candidates (M7)

While reading, note procedures (multi-step, repeatable, with a clear trigger) that appear in
3 or more memory files, across projects. For each, write a draft to
`skills-proposed/<kebab-name>/SKILL.md` (pick a stable location outside any live `skills/`
directory) with frontmatter
`name`, `description`, `status: proposed`, `evidence: N`, `proposed: <date>`, and a body of
numbered steps with the exact commands and paths the memories cite. Overwrite an existing draft
only if the new evidence count is higher. Never write under `skills/` (it registers live) and
never include secrets. Max 2 drafts per run; none is the normal result. The monthly review in
`skills-proposed/README.txt` accepts or deletes them.

### 6. Report

Output a brief consolidation report:

```
MEMORY CONSOLIDATION REPORT
  Project: /path/to/project
  Scanned: N memory files
  Stale (removed): X entries
  Merged: Y pairs → Z files
  Verified OK: W entries
  Skill drafts: K written to skills-proposed/
  Action taken: [list of changes]
```

**Then stamp a last-run marker** in each consolidated project's memory dir so other tools
(e.g. `/end`'s memory-health check) can judge whether a consolidation is *due* rather than
guessing from file count alone:

```bash
# Write per-project marker after consolidating that project (use the dir you scanned in Step 1)
date -u +%Y-%m-%dT%H:%M:%SZ > "<memory_dir>/.last-consolidated"
```

Write the marker even in `--dry-run`? No — only stamp it when changes were actually made (or
verified clean in a real run), never on `--dry-run`. The marker is local bookkeeping; add
`.last-consolidated` to `.gitignore` if the memory dir is tracked (it usually isn't).

## Flags

- `--auto`: Run without interactive confirmation (for cron)
- `--dry-run`: Report only, don't modify files
- `--project <path>`: Consolidate only one project's memories

## Guidelines

- Never delete a memory without checking — false negatives waste more time than false positives
- When merging, keep the more specific entry's content and the more recent entry's metadata
- If a memory's claims can't be verified (e.g., references external system), keep it but note uncertainty
- Run with `--dry-run` first if unsure
