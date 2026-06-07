---
name: content-gate
description: |
  Nine-step pre-publish gate for web content — blog posts, landing pages, SEO
  articles, product pages, anything destined for a public URL. Checks drafting
  quality, fact-checking, de-AI-ing, hero/OG image, full OG/Twitter meta tags,
  FAQ + FAQPage JSON-LD, schema + E-E-A-T signals, analytics coverage, and
  AI-citation/zero-click readiness (self-contained answer above the fold).
  Use before publishing any web content, when the user says "content gate",
  "run the content gate", "is this ready to publish", or "can this page go
  live". Emits a per-step PASS/FAIL report card; any FAIL blocks publish and
  names exactly what is missing. NOT a style review — it gates on evidence.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - WebFetch
  - AskUserQuestion
---

# Content gate: nine checks before anything goes public

You are a **gatekeeper, not an editor**. Every step below resolves to **PASS**
or **FAIL** with evidence — a rendered tag, a file path, a screenshot, a grep
hit. If any step fails, you stop and tell the user:

> "Content gate incomplete. Missing: [step(s)]. Complete these before publishing."

**Applies to:** blog posts, landing pages, product descriptions, SEO articles,
guides — any content destined for a public URL.

**Does NOT apply to:** commit messages, internal docs, READMEs, code comments,
one-liner UI labels.

Run the steps **in order** — early steps (drafting, fact-check) change the text
that later steps (meta tags, FAQ, schema) depend on.

---

## Step 0 — Scope

Before checking anything, establish:

1. **Which file(s)/page(s)** are being published, and the **routed URL** for
   each (map source path → URL using the framework's routing — don't assume).
2. **Page type** (article, landing page, product page, …) — it determines which
   schemas Step 7 requires and which exemptions apply.
3. **Exempt pages** in scope: homepages (`/`, `/<lang>/`), redirect/alias pages,
   paginated leaves (page 2+), and search-result pages skip Step 6 (FAQ); pure
   tool/calculator pages relax parts of Step 9. Note exemptions in the report —
   never silently skip.

If a dev server is needed for verification, start it (or confirm it's running)
and **fetch the actual URL to confirm the H1/title matches the source file**
before grepping anything. A passing check on the wrong page is worse than a
failing one on the right page.

---

## Step 1 — Draft with your strongest model, in the property's voice

- Content should be written (or heavily edited) by the **strongest writing
  model available** — weaker/faster models produce measurably flatter prose.
- If the repo carries a **`VOICE.md`** voice profile, load the **nearest** one
  (walk up from the content file's directory to the repo root; more specific
  files override, omitted sections cascade upward) and draft in that voice.
  Use its example paragraphs as few-shot anchors and its experience claims to
  ground the byline (feeds Step 7).
- No `VOICE.md`? Proceed generically — but flag it as a recommendation in the
  report.

**PASS:** draft exists, voice profile loaded (or its absence noted).

## Step 2 — Fact-check every verifiable claim

Hallucinated dates, stats, names, and prices are the fastest way to torch a
property's credibility.

1. Extract **atomic verifiable claims** from the draft: dates, statistics,
   names, prices, rights/licensing assertions, version numbers. Opinions and
   hedged statements are out of scope.
2. Split claims into **stable** (historical facts) vs **volatile** (prices,
   "current" anything, recent events).
3. If `wtf:multi-llm-deliberation` is installed, run its **Content Truth-Check
   Mode** — cross-model disagreement is a hallucination flag. Otherwise verify
   in-session.
4. **Web-verify all volatile or disputed claims yourself** (WebFetch/search).
   Model consensus is never ground truth for volatile facts — only retrieval is.
5. Apply **surgical, voice-preserving fixes**. Keep a claim table (claim →
   verdict → source) for the report.

**PASS:** every volatile/disputed claim verified against a live source; fixes
applied.

## Step 3 — Remove AI tells

Run a de-AI pass on the final draft: em-dash overuse, rule-of-three patterns,
inflated symbolism ("stands as a testament"), vague attributions ("experts
say"), negative parallelisms, AI vocabulary ("delve", "tapestry", "crucial").

If `wtf:humanizer` is installed, use it — it also re-applies the `VOICE.md`
lexicon on top of the generic pass. Otherwise do a manual pass against those
patterns.

**PASS:** de-AI pass completed *after* the last substantive edit (re-run it if
Step 2 fixes changed the text).

## Step 4 — Hero / OG image

Every page needs a share image. Pages without one collapse to bare-URL previews
on iMessage/Slack/WhatsApp/X/LinkedIn — a silent visibility tax.

- **Size:** 1200×624 (or 1200×630) **JPEG**, < 5 MB (ideally < 300 KB), saved
  in the repo (e.g. `public/img/og/<slug>.jpg`) and referenced from the page's
  meta.
- **Brand-match:** look at an existing OG image from the same site first and
  match its palette/composition. Don't generate in a vacuum.
- If using a diffusion model (FLUX, SDXL, …) to generate it, include in the
  prompt: *"CRITICAL: NO TEXT WHATSOEVER, no labels, no words, no letters, no
  numbers visible on any object."* — these models render garbled text on
  anything resembling UI.
- Convert PNG output to JPEG (`sips -s format jpeg` on macOS, or ImageMagick).
- A sitewide default (`/img/og/default.jpg`) is the floor — a default image
  always beats none.

**PASS:** image exists at the referenced path, correct dimensions/format,
visually consistent with the site, no garbled generated text.

## Step 5 — Full OG / Twitter meta-tag set

Rendered from **one shared layout** (pages pass props) — never hand-pasted
per page. Required on every page:

```html
<title>…</title>
<meta name="description" content="…" />
<link rel="canonical" href="{absolute URL}" />

<meta property="og:site_name" content="…" />
<meta property="og:type" content="website|article|profile" />
<meta property="og:title" content="…" />              <!-- ≤ 70 chars -->
<meta property="og:description" content="…" />        <!-- ≤ 200 chars -->
<meta property="og:url" content="{absolute URL}" />
<meta property="og:locale" content="…" />
<meta property="og:image" content="{absolute URL}" />
<meta property="og:image:secure_url" content="{absolute URL}" />
<meta property="og:image:type" content="image/jpeg" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="624" />
<meta property="og:image:alt" content="…" />

<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="…" />
<meta name="twitter:description" content="…" />
<meta name="twitter:image" content="{absolute URL}" />
<meta name="twitter:image:alt" content="…" />
```

**Hard rules:** all URLs **absolute** (scrapers don't resolve relative paths —
they silently drop the preview); `twitter:card` must be `summary_large_image`;
`og:image:alt` present and descriptive.

**Verify:**

```bash
# after build — expect ~18+ matches per page (OG + Twitter + canonical)
grep -oE '<(meta|link)[^>]*(og:|twitter:|canonical)[^>]*>' dist/path/index.html | wc -l
```

## Step 6 — FAQ block + FAQPage JSON-LD

Every standalone content page renders a **visible FAQ section AND** emits a
`FAQPage` JSON-LD block — both from **one shared partial**, citing the **same**
Q/A text. (JSON-LD without the visible block is a Google policy violation;
visible block without JSON-LD forfeits the rich result.)

- **3–6 Q/A pairs**, each answer 2–4 sentences of substantive prose.
- Questions are **real follow-ups** a reader would ask — not keyword
  re-phrasings of the H1.
- **Server-side rendered** — crawler-invisible client-JS FAQs don't count.
- Per-page FAQs by default; identical FAQs on every page get deduped to zero
  rich results.
- **Exempt:** homepages, redirect/alias pages, paginated leaves, search-result
  pages, email-only URLs. Per-page opt-out (`faq: false` frontmatter or
  explicit user instruction) is allowed but must be deliberate.

**Verify:**

```bash
total=$(find dist -name "*.html" | wc -l)
withfaq=$(grep -rl "FAQPage" dist/ | wc -l)
echo "FAQ coverage: $withfaq / $total"   # every miss must be an exempt page
```

## Step 7 — Schema + E-E-A-T completeness

**Part A — content-type-appropriate JSON-LD** (multiple schemas per page is
normal; render server-side; must validate in Google's Rich Results Test):

| Page type | Required schemas |
|---|---|
| All pages | `WebSite` (sitewide) + `BreadcrumbList` |
| Article / blog post | `Article` (`author`, `datePublished`, `dateModified`, `image`, `headline`) |
| Product page | `Product` with `Offer` (price, currency, availability) |
| Person / about | `Person` or `ProfilePage` with `sameAs` |
| How-to | `HowTo` with `HowToStep` |
| Generic landing | `WebPage` |

`dateModified` reflects **real** content updates — never build timestamps.
Schema claims must match visible page content.

**Part B — visible E-E-A-T signals:**

- **Author byline** — a real, named person (not "Staff" / "Editorial Team" /
  "AI"), linking to a bio page with `Person` JSON-LD and `sameAs`.
- **Author bio snippet** with topic-relevant credentials. Only **factually
  true** experience — never invent credentials.
- **Visible published + updated dates.**
- **≥2 external citations** to authoritative sources on factual content — zero
  outbound links is a strong AI-content signal.
- **Experience markers** where true ("I tested", "we measured").
- **Editorial transparency** — about/contact reachable from the page.

**Exempt from byline/bio:** tool pages, calculators, legal pages, genuinely
organizational announcements (dates + transparency still required).

## Step 8 — Analytics tag present

Every routable page emits the site's analytics tag (GA4 or equivalent) from a
**shared layout/partial** — never pasted per page.

- The measurement ID must be **this site's** ID, resolved from your config /
  secret store — not a placeholder (`G-XXXXXXXXXX`) and not another site's.
- Static in the HTML `<head>` — late client-JS injection misses early
  pageviews.

**Verify:**

```bash
EXPECTED="G-YOURSITEID"
grep -rl "gtag/js?id=$EXPECTED" dist/ | wc -l        # vs total page count
grep -rho 'gtag/js?id=G-[A-Z0-9]*' dist/ | sort -u   # ONLY the expected ID
```

After deploy, confirm a live hit in the analytics realtime view.

## Step 9 — AI-citation & zero-click readiness

AI engines (ChatGPT, Perplexity, Google AI Overviews) and click-behavior
ranking reward signals **orthogonal to classic SEO** — backlinks and keyword
density do **not** earn citations. And **~60% of searches now end with no
click at all**: readers form their decision across AI answers, Reddit threads,
and review aggregators *before* they ever visit. The extractable above-fold
answer is frequently the **only** impression the page makes.

| # | Check | Pass criterion |
|---|---|---|
| 9.1 | **Freshness** (top citation factor) | Visible `Updated: YYYY-MM-DD` + `dateModified` reflecting a real change — never a build-stamp |
| 9.2 | **Structured formatting** | Descriptive H2/H3 every ~200–300 words, lists, comparison tables, a TL;DR near the top. No wall-of-text |
| 9.3 | **Clear, direct language** | Core claims stated plainly; no hedging preamble before the answer |
| 9.4 | **Self-contained direct answer above the fold** — *the headline check* | The page's core question answered in the first screen (~600px): **2–4 declarative sentences that name the entity and state the answer, quotable verbatim by an AI engine with zero surrounding context**. Don't bury the lede; don't make the answer depend on text below it |
| 9.5 | **Titles & meta for clicks** | Specific, benefit-led, curiosity-closing — not exact-match keyword repetition |
| 9.6 | **Friction-free first 30 s** | No interstitials, pop-ups, content-blocking cookie walls, or layout-shifting modals |
| 9.7 | **Internal links** | ≥2 contextual internal links placed to extend the session |
| 9.8 | **Source-category fit** | The page reads as the *type* of source AI engines cite for this query class — an authoritative editorial answer, not a thin landing page |

**Verify 9.4 properly:** render the page at ~1280×800 **without scrolling**
(screenshot it) and read the visible block in isolation. If it can't be quoted
verbatim as the answer — zero-click test — it fails.

For pure tool/calculator pages: 9.4–9.6 still apply; 9.1–9.3 and 9.8 are
relaxed.

---

## Gate artifacts must be committed

Everything the gate produces is part of the page: OG images, generated content
pages, FAQ partials, JSON-LD fragments. None of it may be gitignored or left
uncommitted.

```bash
git check-ignore public/img/og/<slug>.jpg <generated-page-path> 2>/dev/null \
  && echo "BLOCKED: a gate artifact is gitignored" || echo "ok"
git status --porcelain public/img/og/ <generated-content-dir>
```

If a broad `.gitignore` rule (`*.jpg`, `public/img/`) would swallow an
artifact, add a negation (`!public/img/og/`). Only ephemeral build caches
(`dist/`, `.astro/`) stay ignored.

---

## Report card

End every run with:

```
CONTENT GATE — <page/URL>
 1 Draft + voice        PASS/FAIL  <evidence or what's missing>
 2 Fact-check           PASS/FAIL  <N claims verified, M fixed>
 3 De-AI pass           PASS/FAIL
 4 Hero/OG image        PASS/FAIL  <path, dimensions>
 5 OG/Twitter meta      PASS/FAIL  <tag count or missing tags>
 6 FAQ + JSON-LD        PASS/FAIL/EXEMPT
 7 Schema + E-E-A-T     PASS/FAIL  <schemas found; missing signals>
 8 Analytics            PASS/FAIL  <ID verified>
 9 AI-citation          PASS/FAIL  <failed sub-checks>
 — Artifacts committed  PASS/FAIL

VERDICT: READY TO PUBLISH / BLOCKED — missing: <list>
```

Any FAIL → stop and tell the user what's missing. Never soften a FAIL into a
recommendation, and never declare "ready to publish" with an unverified step.
