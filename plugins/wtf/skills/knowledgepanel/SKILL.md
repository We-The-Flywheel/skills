---
name: knowledgepanel
description: |
  Audit and build Google Knowledge Panel / entity setup for a person or
  brand — Entity Home, JSON-LD identity node, sameAs corroboration loop,
  KGMID lookup, and entity-optimized copy. Use when the user says
  "knowledge panel", "entity SEO", "entity home", "KGMID", "knowledge
  graph", "why doesn't Google know who I am", "Google shows the wrong
  person", "Google thinks I'm someone else", or is setting up the identity
  layer for a brand or personal site. Emits a PASS/FAIL report card with
  evidence. NOT a ranking or on-page SEO review — this is about the entity
  the pages are about, not the pages.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - WebFetch
  - AskUserQuestion
uses:
  - skill: humanizer
    relation: delegates
    why: copy mode output goes through the de-AI pass before it is shown
  - skill: og-meta-check
    relation: requires
    why: entity pages are still web pages and need the meta-tag set
department: seo
---

# Knowledge panel / entity setup

You are an **auditor, not a biographer**. Never invent a fact about a
person or company: no dates of birth, no registration numbers, no
headcounts, no awards. A missing fact is a finding to report, not a gap to
fill.

**Read `references/entity-method.md` (next to this file) now and execute
it.** It owns the Entity Home rule, the corroboration loop, the schema
table, the copywriting rules, the tools, the sequencing, and the 14-row
report card. Do not paraphrase it from memory.

## Modes

Invoked as `/wtf:knowledgepanel [mode] [target]`. Default is `audit`.

| Mode | Does |
|---|---|
| `audit` | Read-only report card against the 14-row checklist. Never edits. |
| `copy` | Writes the 150-word executive summary and modular blocks to the method's Step 4 rules. |
| `kgmid` | Runs the lookup script below. |
| `fix` | Applies the audit's findings. **Only after an audit has run** — never fix what you have not measured. |

`copy` and `fix` both run `audit` first. They need to know what is missing.

## Wiring

**Audit the built output, not the source templates.** Build first
(`npm run build` or equivalent) and read the rendered HTML, or `WebFetch`
the live URL. What ships is what counts. Find where the schema is
generated before editing: page-inline, a shared schema builder module, or
a layout template prop are all common.

**Corroboration loop check.** Fetch each `sameAs` target and grep for the
Entity Home URL. Two hosts always bot-block automated requests and must be
reported `MANUAL`, never `FAIL`:

| Host | Returns | Meaning |
|---|---|---|
| `linkedin.com` | `999` | Bot-block. Profile probably fine. |
| `crunchbase.com` | `403` | Bot-block. Profile probably fine. |

Scoring those as failures creates a false negative that never clears.

**KGMID lookup:**

```bash
python3 scripts/kgmid_lookup.py "<entity name>" --url <entity-home-url> \
  [--source kg|serp|both] [--json]
```

Credentials are read from the environment, or from `~/.env.shared` if
present:

| Source | Needs | Cost |
|---|---|---|
| `kg` (default) | `GOOGLE_API_KEY` | Free, ~100k calls/day |
| `serp` | `DATAFORSEO_USERNAME` + `DATAFORSEO_PASSWORD` | Paid per call, prompts before spending |

`--source kg` is free, so always run it. Reach for `serp` only when the KG
API and the rendered panel disagree, or the KG API returns nothing but a
panel visibly exists.

If the script reports that `kgsearch.googleapis.com` is not enabled, that
is **not a missing credential** — the key is valid and the API is simply
off for that Google Cloud project. Surface the `gcloud services enable`
line the script prints and let the user decide. Enabling an API is an
infra change, not yours to make. Set `GCP_PROJECT` so the message names
the right project.

**Copy mode.** Draft in-session. Load the nearest `VOICE.md` if the repo
has one, then run the draft through `humanizer` before showing it. Output
the 150-word summary plus per-platform variants (Crunchbase, LinkedIn, X)
as copy-pasteable blocks, each with its word count stated.

**Fix mode.** Merge into the existing entity node. Never append a second
`<script>` for an entity that already has one: two unlinked nodes is the
exact split this skill exists to catch. Preserve any existing `@id`
verbatim, because changing one orphans every piece of corroboration built
against it.

## Output

Emit the 14-row report card from the method file, then:

```
VERDICT: <n> failing — <structural blockers first, if any>
```

Rows 1, 5 and 6 (Entity Home exists, stable `@id`, `url` → Entity Home)
are structural. A FAIL on any of them makes the rest moot, so say that
rather than handing back fourteen equal-weight items:

> "Entity setup incomplete. `<entity>` fails: [rows]. Entity Home and a
> stable `@id` have to be right before corroboration is worth building —
> fix these first, or the external profile work is wasted."

Never soften a structural FAIL into a recommendation. Never report an
entity as correctly set up on schema alone: the corroboration loop and the
`url` Google actually holds are what decide it.

## Don't

- Don't invent facts to fill a schema property.
- Don't treat a homepage `#about` anchor as an Entity Home.
- Don't change an existing `@id`, ever.
- Don't add a second entity node instead of merging.
- Don't score a LinkedIn `999` or Crunchbase `403` as a broken link.
- Don't promise a timeline. Corroboration accumulates over weeks to months.
- Don't spend on `--source serp` without saying what it costs first.

> Background and worked explanation: https://docs.tfw.bz/knowledgepanel
