---
name: riff
description: |
  Divergent design ideation — generate 3–5 deliberately far-apart, fully-rendered
  design directions for a UI surface (hero, landing page, dashboard shell,
  component) and present them in ONE side-by-side local compare artifact, ending
  with a pick-and-lock step that hands the winner to wtf:moodboard. Use when the
  user says "riff", "riff on this", "show me directions", "give me a few
  options", "surprise me", "explore some designs", "what could this look like",
  or is starting design work with no design system chosen yet. Deliberately
  ignores any existing DESIGN.md / tokens.json — this is the gate-exempt
  Diverge stage of the design lifecycle (design.tfw.bz#lifecycle). NOT for
  on-brand work in a repo that already has a locked design system, reference
  research (wtf:moodboard), or polish passes on an existing design.
user-invocable: true
argument-hint: "[surface to riff on] [--n 3..5] [--include <aesthetic>]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - AskUserQuestion
  - Skill
  - WebFetch
uses:
  - skill: moodboard
    relation: delegates
    why: winning direction hands off to moodboard for tokens.json/DESIGN.md
department: design
---

# Riff — divergent design ideation

You are running the **Diverge** stage of the design lifecycle
(**Diverge → Lock → Enforce → Judge**, documented at
<https://design.tfw.bz/#lifecycle>). The deliverable is an *option space*: 3–5
genuinely far-apart, fully-rendered directions the human can compare in a
browser and pick from. You generate; the human judges; `wtf:moodboard` locks
the winner into design decisions; whatever design-system enforcement your repo
uses takes over from there.

## Hard rules

1. **Gate-exempt, not craft-exempt.** Do NOT load `design/DESIGN.md`,
   `design/tokens.json`, or any brand stylesheet — escaping the existing
   system's gravity is the point. But AI-slop is still slop, and it applies to
   every direction. If the repo ships an anti-slop baseline of its own, read it
   before building. Otherwise these are the floor, in ANY direction: no
   purple-pink (or violet-fuchsia) gradients · no Inter/Roboto/Arial as a
   default · no Space Grotesk as the reflex "designed" font · no
   `bg-clip-text` gradient headings · no blinking `animate-pulse` status dots
   unconnected to live data · no backdrop-blur glassmorphism as decoration ·
   no `border-l-4` side-stripe callouts · no indigo-500/600 default CTA · no
   three-identical-cards feature row · no "AI-powered" in the copy.
2. **Forced diversity.** No two directions from the same aesthetic family
   (list below). If two of your candidate directions could be described with
   the same three adjectives, throw one out and pull from a different family.
3. **Real code, real copy.** Every direction is a standalone, self-contained
   HTML file with actual content — the user's real copy and assets when they
   exist, honest placeholders when they don't. Never lorem ipsum, never
   wireframes, never "imagine a hero image here".
4. **One local compare artifact.** Output is a local file on disk, opened in
   the user's browser — not a hosted artifact. It must work from `file://`
   with no server: self-contained, assets inline or referenced by local path.
5. **Vary across invocations.** If you riffed for this user before, don't
   reuse the same family lineup. Two riffs should never rhyme.

## Step 1 — Brief (2 minutes, not 20)

Gather the minimum needed to make each direction *about this product*:

- **Surface**: what exactly is being riffed (hero, full landing, dashboard
  shell, pricing page, component)?
- **Audience + job**: who sees it and what should they feel/do? If the repo
  has a `PRODUCT.md`, read it for audience/tone — its *content* context is
  welcome; its design references are not binding here.
- **Raw material**: real copy (headline, value prop), real assets (logo,
  product shots, photography). Ask for what's missing — front-loading real
  assets is the single highest-leverage input (field note on design.tfw.bz).
- **Hard constraints only**: framework, must-keep elements, legal copy.
  Aesthetic preferences are NOT collected here — that's what the directions
  are for.

Batch all questions into one `AskUserQuestion` call. If the user gave enough
in the invocation, skip straight to Step 2.

## Step 2 — Direction selection (before any code)

Pick **N directions (default 4, range 3–5)** from far-apart families. For each,
write a **one-line thesis** naming what makes it unforgettable — e.g. *"The
headline IS the interface: 12rem variable-font type that responds to scroll
velocity."* If you can't write a sharp thesis, the direction is filler; replace
it.

Composition rules:

- Each direction from a **different family** (appendix below).
- **At least one wildcard**: something the user wouldn't have asked for —
  kinetic typography, an unexpected interaction model, a medium borrowed from
  print/film/hardware. Surprise is a feature, not a risk.
- Vary the **theme axis** too: don't ship four dark pages. Derive each
  direction's light/dark from its own physical-scene sentence (write one line of
  who uses it, where, under what ambient light), not from a default.
- Honor `--include <aesthetic>` by making one direction interpret that
  request; the rest still diverge.

State the N theses to the user in one short list as you start building — no
approval gate, just visibility.

## Step 3 — Build each direction

Each direction is `direction-<n>.html`: standalone, self-contained (inline
CSS/JS, Google Fonts links allowed, assets referenced by absolute path or
embedded). Craft bar per direction — applied per-direction rather
than per-system:

- **Typography**: distinctive, characterful pairing per direction; never the
  same display font in two directions; hierarchy through scale + weight
  (≥1.25 ratio).
- **Color**: commit. Pick a color strategy (restrained / committed / full
  palette / drenched) per direction and execute it; tinted neutrals, no pure
  `#000`/`#fff`.
- **Motion**: one orchestrated moment per direction (staggered load reveal,
  scroll-trigger, hover surprise) beats scattered micro-interactions.
  CSS-only where possible.
- **Composition**: at least one direction breaks the grid (asymmetry,
  overlap, diagonal flow); at least one uses restraint as its statement.
- **Complexity matches vision**: maximalist directions need elaborate code;
  minimal directions need precision. A timid maximalist page is worse than
  either.

## Step 4 — The compare artifact

Assemble everything in one folder — `<reports-dir>/riff-<slug>-<YYYY-MM-DD>/`,
where `<reports-dir>` is wherever this project keeps local review artifacts
(`~/reports/` is a fine default; create it if missing):

```
riff-<slug>-<date>/
├── index.html          ← compare shell (the thing you open)
├── direction-1.html
├── direction-2.html
├── …
└── LOCKED-DIRECTION.md ← written in Step 5
```

The `index.html` shell:

- **Tabs** (one per direction) labelled with family name + thesis line.
- Directions embedded via `<iframe src="direction-n.html">` — sibling-file
  iframes work from disk; don't inline via srcdoc.
- **Viewport toggle**: buttons for 390 / 768 / 1440 px that resize the iframe.
- A footer note: *"Diverge stage — gate-exempt. Winner locks via moodboard."*
- Keep the shell chrome neutral (system font, near-white) so it never competes
  with the directions it frames.

Then open `riff-<slug>-<date>/index.html` in the browser (`open` on macOS,
`xdg-open` on Linux) and tell the user what
they're looking at in one sentence per direction.

## Step 5 — Pick and lock

Ask which direction wins via `AskUserQuestion` (one option per direction,
labels = family names). Merges are first-class: "2, but with 4's typography"
→ build the merged variant as `direction-final.html`, add it to the shell,
confirm.

On a pick, write `LOCKED-DIRECTION.md` into the riff folder:

- The winning thesis + family.
- The concrete decisions the winner embodies: background treatment, type
  pairing (exact font names), color strategy + key values, navigation scale,
  the signature interaction, and **anti-decisions** (what the rejected
  directions prove the user doesn't want — these become do-nots).

Then hand off: **suggest `wtf:moodboard` with `LOCKED-DIRECTION.md` as input** —
it converts the locked decisions into design tokens + a design doc, and from
that point your repo's design-system enforcement owns the project. Riff's job ends at
the handoff; never generate production components from a riff directly.

If the user picks nothing ("none of these"), treat it as signal: ask which
direction came *closest* and what repelled them about the rest, then re-riff
with fresh families — the rejected families are now anti-references.

## Appendix — aesthetic families (pick far apart)

Brutalist/raw · editorial/magazine serif · Swiss/international grid ·
retro-futurist/terminal · organic/hand-drawn · luxury/refined minimal ·
maximalist collage · art-deco/geometric · industrial/utilitarian ·
soft/pastel toy-like · kinetic-type-led · photography-led drenched ·
data-dense hacker · vintage print (risograph/newsprint) · neo-memphis playful.

The list is a starter, not a cage — invent families when the product calls
for one. What's non-negotiable is the *distance between* the ones you pick.
