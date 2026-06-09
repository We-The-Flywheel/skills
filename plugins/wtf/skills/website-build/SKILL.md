---
name: website-build
description: |
  Reference-first website build using a four-pillars framework — Audience →
  Structure → Copy → Design — collecting and documenting inputs before building
  anything. Use when the user says "build a website", "new site build", "start a
  website project", "website template", "scope a site", or is kicking off a
  marketing, brand, or portfolio site from scratch. Produces a populated brief
  (the four pillars) and hands the Design pillar to the moodboard process. NOT
  for single-page tweaks or existing-site edits.
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

# Website build: four pillars, reference-first

Scope the site **reference-first** — collect and organize inputs for all four
pillars *before* building anything. The output of this phase is a populated
brief, not pages. Fill what's known; leave the rest blank. **Blanks are the
to-do list** — they tell you what to collect next.

Create a live brief (e.g. `REFERENCE.md`) with the four pillars below, plus
`moodboard/` and `moodboard/anti-ref/` folders. Fill the pillars interactively —
use `AskUserQuestion` for the human-input pieces (references, voice, audience).
Flag every unresolved decision with ⚠️ and who owns sign-off; never fill a gap
with a silent assumption. Keep a running build log (decisions, findings,
reversals) **separate** from the brief so the brief stays clean.

---

## Step 0 — The clarity paragraph (gate)

One paragraph, plain language, child-readable, no jargon: what this is and who
it's for. **Gate:** if it can't be written yet, that's the first problem to
solve — don't build on an unclear premise.

## 1. Audience

Who it's for, in plain terms. A single qualifying **filter** beats a
profession/demographic list — it's more durable and less likely to carry hidden
bias. State what they need *from the site*.

## 2. Structure

What pages, and what lives on each. Run every candidate page through the **four
visitor jobs**: *understand what this is / believe it works / know if it's for
them / get in.* Anything that serves none of those doesn't get a page.

Keep an **accountability map**: for each thing you cut from the nav, record where
it went and why — folded into another page, moved to the footer, cut until
content exists, post-launch. A cut you can't account for is one you'll
second-guess later. Reference design-forward sites for structural minimalism.

## 3. Copy

Brand name, loglines, brand voice, and an explicit **language-to-use /
language-to-avoid** list. Loglines should provoke, not merely describe. When the
copy is drafted, de-AI it with `wtf:humanizer`; for anything going to a public
URL, gate it with `wtf:content-gate` (each if installed).

## 4. Design

Hand the Design pillar to the **moodboard process** (`wtf:moodboard` if
installed, otherwise run it inline): it turns references + anti-refs into locked
decisions — background, type, accent, nav scale, interaction patterns — and an
in-context type explorer. Those feed your design tokens and design doc, then
whatever design-system or citation gate you enforce at code time.

---

## Build approach (after the brief is filled)

- **POC, not comps.** Build 3–5 real working homepage directions in code, deploy
  to a preview URL, pick one. The chosen POC becomes the production site — no
  design-tool-to-build translation step.
- **Hand-offs:** Design → `wtf:moodboard` · de-AI copy → `wtf:humanizer` ·
  public-page gate → `wtf:content-gate` (each used if installed).
