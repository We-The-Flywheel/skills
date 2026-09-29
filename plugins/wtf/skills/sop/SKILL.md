---
name: sop
aliases: [sop-create, sop-review]
description: >-
  Create, edit, or review Standard Operating Procedures with one consistent structure across projects. Use on create an SOP, review this SOP, write a procedure for, or any operational-procedure request.
department: content
---

# SOP Management

Create, edit, and review Standard Operating Procedures with a consistent structure across all projects.

**Announce at start:** "Using the SOP skill to [create | edit | review] this procedure."

## Detect Mode

Determine the mode from the user's request:

| Mode | Trigger | Action |
|------|---------|--------|
| **Create** | "create/write an SOP for...", new procedure needed | Generate from template |
| **Edit** | "update/fix/align this SOP", existing file referenced | Restructure to match template |
| **Review** | "review this SOP", "/sop review", quality check | Audit against checklist |

## Standard SOP Structure

Every SOP MUST follow this structure. No exceptions.

```markdown
---
name: sop-name-in-kebab-case
type: sop
version: "1.0"
owner: <person or team>
last_validated: YYYY-MM-DD
frequency: <daily | weekly | monthly | quarterly | on-demand | on-trigger>
---

# SOP: [Title]

> One-line summary of what this procedure achieves and why it matters.

**Scope:** Who/what this applies to
**Trigger:** When to execute this SOP (event, schedule, or condition)
**Prerequisites:** What must be true before starting

---

## Phase 1: [Name]

### Step 1.1: [Action verb + object]

[Clear instructions. One action per step.]

### Step 1.2: [Action verb + object]

[Instructions with commands, screenshots, or examples as needed.]

---

## Phase N: Verify

Every SOP ends with verification.

### Success Criteria

- [ ] Criterion 1 (measurable)
- [ ] Criterion 2 (observable)
- [ ] Criterion 3 (testable)

### Rollback

What to do if verification fails. How to undo.

---

## References

- [Source 1](url) - why it's relevant
- [Source 2](url) - why it's relevant
```

## Rules

### Naming
- File: `SOP-<kebab-case-name>.md`
- Location: `docs/sops/` in the relevant project (create directory if needed)
- Title: Always prefixed with `SOP:` in the H1

### Content
- **Action-oriented steps** - every step starts with a verb ("Run", "Check", "Update", "Verify")
- **One action per step** - if a step has "and", split it
- **Commands over descriptions** - show the exact command, not "run the deployment script"
- **Phase-based** - group related steps into phases (detect, diagnose, fix, verify)
- **Always end with verification** - the last phase is always "Verify" with checkable success criteria
- **Include rollback** - what to do when it goes wrong

### Metadata
- `version` - increment on significant changes (1.0, 1.1, 2.0)
- `owner` - who maintains this SOP (person, not "the team")
- `last_validated` - date someone last confirmed it works end-to-end
- `frequency` - how often this runs, or "on-trigger" for event-driven

## Create Mode

1. Ask the user for the topic if not provided
2. Research existing procedures in the project (grep for related files, check `docs/`)
3. Generate the SOP using the template above
4. Save to `docs/sops/SOP-<name>.md` in the relevant project
5. If there's an existing informal procedure, incorporate its content

**Quality gates before saving:**
- [ ] Every step starts with a verb
- [ ] No step contains "and" joining two actions
- [ ] Commands are exact (copy-pasteable)
- [ ] Success criteria are measurable
- [ ] Rollback section exists
- [ ] Frontmatter is complete

## Edit Mode

1. Read the existing SOP file
2. Map its content to the standard structure:
   - Extract metadata into YAML frontmatter
   - Identify phases and steps
   - Ensure title has `SOP:` prefix
   - Add missing sections (verify, rollback, references)
   - Rewrite steps to start with verbs
3. Present a diff summary to the user before writing
4. Preserve all original content - restructure, don't delete

## Review Mode

Audit the SOP against this checklist and report findings:

### Structure Checklist
- [ ] Has YAML frontmatter with all required fields (name, type, version, owner, last_validated, frequency)
- [ ] H1 title starts with `SOP:`
- [ ] Has one-line summary blockquote
- [ ] Has Scope, Trigger, Prerequisites
- [ ] Organized into numbered phases
- [ ] Steps use `### Step N.N: [Verb + object]` format
- [ ] Final phase is "Verify" with success criteria
- [ ] Has rollback section
- [ ] Has references section

### Content Checklist
- [ ] Every step starts with an action verb
- [ ] No compound steps (no "and" joining two actions)
- [ ] Commands are exact and copy-pasteable
- [ ] Success criteria are measurable/observable
- [ ] No ambiguous language ("should", "might", "consider")
- [ ] Owner field has a specific person
- [ ] `last_validated` is within the last 90 days

### Report Format

```
## SOP Review: [filename]

**Score:** X/16 checks passing
**Status:** [PASS | NEEDS WORK | RESTRUCTURE]

### Passing
- [x] ...

### Failing
- [ ] ... — [specific fix needed]

### Recommendations
1. ...
```

**Thresholds:**
- 14-16: PASS
- 10-13: NEEDS WORK (minor fixes)
- 0-9: RESTRUCTURE (apply edit mode)
