---
name: website-build
description: |
  Scope a new marketing, brand, or portfolio website through Audience, Structure,
  Copy and Design before building. Produces a reference brief, then hands off to
  riff and moodboard for approved design. For editorial publication scaffolding,
  prefer the installed site-scaffold capability when available. Not for existing
  site tweaks or single-page edits.
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
uses:
  - skill: moodboard
    relation: delegates
    why: Approved design direction is locked through moodboard
  - skill: humanizer
    relation: requires
    why: drafted copy must be de-AI'd
department: design
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

- For editorial publications needing domain onboarding, repository/template setup,
  taxonomy and charter, route to the installed `site-scaffold` capability when
  available. Keep this brief as input. That scaffold is specialized; marketing,
  brand and portfolio briefs still belong here.
- For an unproven product claim, use an installed disposable POC workflow first.
  Record its finding; discard its code. A POC is not a production-site shortcut.
- For approved new design, use `wtf:riff` for distinct rendered directions, pick
  one, then use `wtf:moodboard` to lock it. Build through the installed production
  UI workflow using the project's design system and review gates.
- Copy uses `wtf:humanizer`; public pages use `wtf:content-gate` when installed.
  A brief, scaffold or preview does not authorize launch or deployment.
