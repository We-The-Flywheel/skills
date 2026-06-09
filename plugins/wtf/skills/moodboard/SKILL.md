---
name: moodboard
description: |
  Reusable moodboard methodology for a website build — turn visual references
  (and anti-references) into locked design decisions: background treatment,
  type category, accent approach, navigation scale, interaction patterns, and a
  list of anti-patterns to avoid. Includes an in-context type explorer (render
  the real wordmark in 8–12 fonts on the actual brand background, all in one
  scroll). Use when the user says "build a moodboard", "moodboard process", "do
  design research", "collect references", "pick fonts", or "type explorer", or
  is starting the design phase of a site build. NOT a code generator — it
  produces documented design decisions, not pages.
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash
  - AskUserQuestion
  - Skill
  - WebFetch
---

# Moodboard: references → locked design decisions

A moodboard here is **research, not decoration**. The output is not a pretty
collage — it's a set of *locked, traceable* design decisions: background
treatment, type category, accent approach, interaction patterns, and what to
avoid. Every decision should trace back to a specific finding, and feed directly
into your design tokens and design doc.

Work the eight steps **in order** — the early steps gather honest signal, and
analysis applied too early contaminates it. Steps 1, 3, and 4 need the client's
input: use `AskUserQuestion` rather than guessing.

---

## Step 1 — Human references first

Ask the client for 2–4 sites they personally like. No criteria, no structure —
just sites they're drawn to.

**Why:** the purest signal you'll get. They reveal aesthetic instinct before
analysis contaminates it. These become the anchor; everything else is measured
against them.

## Step 2 — Scope the research direction

Don't look for direct competitors or peers. Look **adjacent** — well-funded,
design-forward organizations whose websites are worth referencing, regardless of
business-model similarity.

**Why:** direct peers are often poorly designed. The question is "who makes
beautiful websites in this general sphere," not "who does what we do."

## Step 3 — Generate a candidate list

Brainstorm 10–15 candidate sites from knowledge. Present the list to the client
**before** opening anything, so they can flag what they already know and dislike.
Avoids wasted research.

## Step 4 — Open everything for a vibe-check

Open all candidates at once. Let the client browse with no structure or scoring —
first impressions only. Get the gut response first, then apply structure.

## Step 5 — Structured feedback via spreadsheet

Create a CSV: Site / URL / What They Are / Vibe (1–10) / What We Like / What We
Don't Like / Relevant? / Notes. Share it (e.g. upload to a shared drive) so the
client fills it in directly. This is the bridge from gut reaction to documentable
decisions.

## Step 6 — Screenshots into the moodboard folder

Client captures screenshots of standouts into `moodboard/`, organized into two
subfolders:

- `moodboard/` — positive and mixed references. *Mixed* = something to take AND
  something to leave; the CSV captures which.
- `moodboard/anti-ref/` — things to explicitly **not** emulate.

**Anti-refs matter as much as positive refs** — they define the edges just as
clearly. Traditional moodboards skip them; don't.

## Step 7 — Analysis

Read the populated CSV and the screenshots together. Extract:

- recurring patterns in what works
- recurring patterns in what fails
- the specific decisions those patterns suggest (background approach, type
  weight, accent usage, nav size, interaction style)
- a **"sweet spot" description** — what this site should feel like, from evidence

Write the findings into the project's design brief. Every decision from here
should be traceable to a moodboard finding.

## Step 8 — Type exploration (in context)

Once the type category is settled (serif vs. sans, weight range, feel), evaluate
fonts **in context** before committing them to tokens.

**The tool:** a single self-contained HTML file that renders the actual wordmark
in 8–12 candidates simultaneously — same background, same accent, same real copy
— so all options compare directly in one scroll. Beats Google Fonts / design-tool
specimen sheets because the human reacts to fonts *in situ*, not in abstraction,
with no tooling to set up.

**Run three explorers in sequence** (each disposable once decided):
1. Display / wordmark candidates — pick the headline font
2. Body-copy pairings — with the wordmark locked, judge paragraph readability
3. Logline / sub-headline — with wordmark + body locked, judge the middle tier

**This skill can scaffold the HTML on request:** load each candidate's web-font
`<link>`, the real wordmark/logline/body copy (never lorem), and the locked
background + accent as CSS variables; render one labelled row per candidate.

---

## Output

By the end you should have locked decisions on: background approach, type
category and weight range, accent approach (one vs. two; saturated vs. muted),
navigation scale, interaction patterns to adopt or avoid, a documented "sweet
spot" description, and a list of anti-patterns to screen against.

These feed your design tokens (e.g. a `tokens.json` in the W3C DTCG format) and a
plain-language design doc, then into whatever design-system or citation gate you
enforce at code time.

> **Companion:** if you're scaffolding the whole build (not just the design
> phase), `wtf:website-build` runs the four-pillars framework (Audience →
> Structure → Copy → Design) and calls this skill for the Design pillar. For
> de-AI-ing the copy, `wtf:humanizer`; before publishing public pages,
> `wtf:content-gate` (each used if installed).
