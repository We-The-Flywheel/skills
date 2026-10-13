# Step 5: decision dedup and entry template

Moved verbatim from `SKILL.md`; read at the step that points here.

**5b. Dedup gate (required before writing).** For each candidate, grep the existing log for its key noun/concept first:

```bash
# Example candidate: "use a single append-only DECISIONS.md, not per-file ADRs"
grep -in "DECISIONS\.md\|per-file ADR\|decision log" DECISIONS.md 2>/dev/null
```

| Result | Action |
|--------|--------|
| Identical decision already logged | **Skip** — report "already logged: DECISIONS.md:<line>" |
| Prior decision now reversed/changed by this session | **Supersede** — append a new entry AND flip the old entry's `**Status:**` to `superseded by [<this entry's date+title>]` (the only permitted edit to history) |
| Genuinely new decision | **Append** a new entry at the top (newest-on-top) |

**5c. Write the entry.** Create `DECISIONS.md` if absent (newest-on-top, append-only). Each entry, ~6 lines:

```markdown
## YYYY-MM-DD — <decision title>
**Status:** accepted
**Context:** <the forcing question — what made this a real choice>
**Decision:** <what we chose>
**Alternatives:** <what we rejected, and the one-line why>
**Consequences:** <what this locks in or costs later>   ← optional, omit if obvious
```

**Rules:** append-only (sole exception: flipping a `**Status:**` line when superseding); newest entry at the top under `# Decisions`; keep entries tight — this is not a design doc. `DECISIONS.md` is **committed** (tracked) — never `.gitignore` it. Report: "📋 Logged N decision(s) to DECISIONS.md" (or skip silently).
