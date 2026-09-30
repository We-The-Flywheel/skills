---
name: screamingfrog-check
description: >-
  Headless Screaming Frog crawl for SEO and technical issues with a prioritized fix plan. Use when the user says crawl, audit site, check site health, Screaming Frog, or needs a full-site technical SEO review.
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
department: seo
---

# /screamingfrog-check — Site Crawl & Technical Audit

**Local overlay.** If `~/.local/share/flywheel/house/screamingfrog-check.md` exists, read it before starting and apply it on top of this skill: it holds an organisation's own rules, tools and paths for this workflow. Where the two conflict, the overlay wins. No overlay, no change.

Full-site crawl using Screaming Frog headless CLI. Produces a prioritized issue report with fix plan.

## User-invocable
When the user types `/screamingfrog-check <url>`, run this skill.

## Arguments
- `/screamingfrog-check https://example.com` — crawl a single site
- `/screamingfrog-check https://example.com --pages 50` — limit crawl depth

## Instructions

### Step 1: Determine Crawl Mode

**Crawl (default):** Uses Screaming Frog headless for comprehensive crawl. Spot-check pages manually with playwright if needed.

### Step 2: Full Crawl with Screaming Frog

```bash
SF="/Applications/Screaming Frog SEO Spider.app/Contents/MacOS/ScreamingFrogSEOSpiderLauncher"
OUTPUT="/tmp/crawl-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUTPUT"

# Run headless crawl with standard exports
"$SF" \
  --crawl <URL> \
  --headless \
  --output-folder "$OUTPUT" \
  --export-tabs "Internal:All,Response Codes:Client Error (4xx),Response Codes:Server Error (5xx),Page Titles:Missing,Page Titles:Duplicate,Page Titles:Over 60 Characters,Page Titles:Below 30 Characters,Meta Description:Missing,Meta Description:Duplicate,Meta Description:Over 155 Characters,Meta Description:Below 70 Characters,H1:Missing,H1:Duplicate,Images:Missing Alt Text,Images:Over 100 KB,Canonicals:Non-Indexable Canonical" \
  --bulk-export "All Inlinks,All Outlinks,Redirect Chains" \
  --save-report "Crawl Overview,Redirect & Canonical Chains,Orphan Pages" \
  --create-sitemap
```

If `--pages N` specified, add `--max-crawl-depth` or use a config file with URL limit.

Filter thresholds (`Over 60 Characters`, `Over 100 KB`, etc.) are literal names with the
configured number substituted in — see Step 2c before assuming a different number works.

**If Screaming Frog is not installed or fails:** Fall back to quick crawl mode automatically.

### Step 2b: Running on a remote host (long crawls)

On Linux, the CLI binary is `screamingfrogseospider` (installed via the vendor's
`.rpm`/`.deb`). Headless works with **no X server** (no Xvfb needed, no `DISPLAY`).
Run it on a server when the crawl is long-running or should survive the laptop closing:

```bash
ssh your-crawl-host 'O=/tmp/crawl-$(date +%Y%m%d-%H%M%S); mkdir -p $O; \
  screamingfrogseospider --crawl <URL> --headless --output-folder $O \
  --export-tabs "Internal:All" --save-report "Crawl Overview" --create-sitemap --overwrite'
```

The licence file lives at `~/.ScreamingFrogSEOSpider/licence.txt` on each machine that
runs it — a fixed-term licence needs renewing there before it expires.

**Unlicensed / expired-licence behaviour (verified 2026-07-31):**
headless CLI crawling still runs fine with `Licence Status: Missing` — `--crawl`,
`--export-tabs`, `--save-report`, `--bulk-export` and `--create-sitemap` all work. Limits:

- Crawl caps at **500 URLs** (silently — it just stops; check the "crawled N urls" log line).
- **`--config` fails hard**: `Could not locate licence file … licence.txt` and exit 1. So the
  `--pages N` config-file path above is licence-only; unlicensed, use `--crawl-list` or
  post-filter the CSV instead.
- API integrations (`--use-google-search-console`, `--use-pagespeed`, …) and custom
  extraction are licensed features.

If a crawl comes back at exactly 500 URLs or `--config` errors, check the licence before
debugging the crawl.


### Step 2c: CLI gotchas that abort the run (verified 2026-07-31, SF 23.3)

**SF validates every export name BEFORE crawling and exits `FATAL` on the first bad one** — you
lose the whole run, not just that export. On a long crawl, validate names against a throwaway
`--crawl https://example.com` first.

- **Filter names are literal, with a placeholder `X`** — `Page Titles:Over X Characters`, not
  `Over 60 Characters`. Same for `Below X Characters`, `Over X Pixels`, `Images:Over X KB`,
  `Images:Alt Text Over X Characters`. SF substitutes the configured threshold into the *output
  filename* (`page_titles_over_60_characters.csv`), which is what misleads you into passing the
  resolved name back in.
- **A bad filter prints the valid list** — `Unknown filter 'X' for tab 'Y'. Available filters: …`.
  Cheapest way to discover real names: pass a deliberately wrong one and read the error.
- **`--timestamped-output=false` is not valid** (`FATAL - Unrecognized option`). The flag takes no
  `=value` form; with `--output-folder` set, exports land directly in that folder anyway.
- **Names that look obvious but don't exist:** `Redirect Chains` and `Non-Indexable URLs` as
  `--save-report` (use `Redirect & Canonical Chains`); `Images:Missing Alt Text Inlinks` as
  `--bulk-export`; `Validation:Missing <html>/<head>/<body> Element`;
  `Validation:High Internal/External Outlinks`; `URL:Over 115 Characters`.
- **Images on a CDN are `External`, not `Internal`.** Webflow/Shopify-style sites serve images
  from another host, so `Internal:Images` comes back empty and `internal_all.csv` is HTML-only.
  Image data is in `external_all.csv` and the `Images:*` tabs.

### Step 2d: Crawling a site that is `Disallow: /` (staging previews)

SF respects `robots.txt` by default and there is **no CLI flag** to override it — the setting
lives in the crawl config, which is a Java-serialized blob you can't hand-author. Symptom:
`crawled 1 urls` and a single-row `internal_all.csv`.

**Webflow blanket-applies `robots.txt: Disallow: /` to every `*.webflow.io` staging domain.**
That is a platform default, not a targeted exclusion — but confirm you're authorised to crawl the
site before overriding it, and never do this to a third party's production domain.

Get a base config without touching the GUI: SF writes one after every run. Then byte-patch the
enum — the string is length-prefixed, and Java handles the size change fine because references
are handle-indexed, not offset-based:

```bash
# 1. Run any crawl once, then grab the config SF just wrote
SRC=$(ls -t ~/.ScreamingFrogSEOSpider/ProjectInstanceData/*/serialised_data/spiderconfig | head -1)

# 2. Flip RobotsTxtMode RESPECT -> IGNORE
python3 -c "
d=open('$SRC','rb').read()
assert d.count(b'\x00\x07RESPECT')==1
open('ignore-robots.seospiderconfig','wb').write(d.replace(b'\x00\x07RESPECT', b'\x00\x06IGNORE'))"

# 3. Use it
"$SF" --crawl <URL> --headless --config "$PWD/ignore-robots.seospiderconfig" ...
```

SF echoes `mRobotsTxtMode=IGNORE` in the startup log — check for it. Note `--config` requires a
valid licence (see the note above).

The same file exposes other defaults worth knowing are **off**: `mExtractJsonLd`,
`mExtractMicrodata`, `mSchemaDotOrgValidation`, `mExtractHttpHeader`, `mExtractImgSrcSet`. Patching
those booleans is far more fragile than the enum (they're positional in the field-data block) — if
you need schema, OG tags, caching headers or image byte weights, write a small companion crawler
instead that pairs with SF and cross-validates against it.

### Step 3: Extended Checks (schema, OG tags, robots/sitemap health, accessibility)

The default export tabs above do **not** cover these — they need extra steps or a licensed
config. Run all of them; each maps to a checklist item this skill is scored against.

**3a. Structured data (schema.org / JSON-LD / microdata)**
`mExtractJsonLd`, `mExtractMicrodata`, and `mSchemaDotOrgValidation` are OFF by default in SF's
config (see Step 2d's `spiderconfig` byte-patch technique) and licensed validation needs
`--config`. Cheapest reliable path: pull rendered HTML for a representative page sample
(homepage, top-3 landing pages, one article/product template) and grep for `<script
type="application/ld+json">` blocks, then validate each with Google's Rich Results Test
(`https://search.google.com/test/rich-results`) or schema.org's validator. Flag: missing
JSON-LD on templates that should have it (Article, Product, FAQPage, Organization, BreadcrumbList),
and any block that fails validation.

**3b. Open Graph / Twitter Card tags**
Also not in any SF export tab. For the same page sample as 3a, grep rendered `<head>` for
`og:title`, `og:description`, `og:image` (+ width/height/alt), `og:url`, `og:type`,
`twitter:card`, `twitter:title`, `twitter:description`, `twitter:image`. Cross-check against
the full required tag set, or just run `wtf:og-meta-check <url>` per page and fold its
PASS/FAIL into this report's OG section.

**3c. robots.txt and sitemap health**
`--create-sitemap` generates a *new* sitemap from the crawl — it does not validate the site's
*existing* one. Check both explicitly:
```bash
curl -s <URL>/robots.txt          # exists, returns 200, not blanket Disallow: / on prod
curl -s <URL>/sitemap.xml | head  # exists, valid XML, <lastmod> present
```
Then diff sitemap URLs against the crawl's `internal_all.csv`: entries in the sitemap that 4xx/5xx
or redirect are stale; internal pages missing from the sitemap may be intentionally excluded or
an oversight — call out both.

**3d. Accessibility**
`Images:Missing Alt Text` only covers one WCAG criterion. For a real pass, run a design/accessibility QA pass
or an axe-core scan (`npx @axe-core/cli <url>`) against the same page sample as 3a — covers
color contrast, landmark regions, form labels, focus order, and ARIA misuse that SF can't see.

**3e. Duplicate meta descriptions and title/meta length**
Covered by the `--export-tabs` additions above (`Meta Description:Duplicate`, `Over/Below X
Characters` filters) — just make sure Step 4 actually reads those CSVs, not just the presence/
absence ones.

**3f. Image weight / web optimization**
Covered by `Images:Over 100 KB` above (adjust threshold per site). Note Step 2c's CDN caveat:
images served off-host land in `external_all.csv`, not `internal_all.csv`.

**3g. URL slug / title / H1 SEO quality (not just presence)**
SF confirms titles/H1s *exist* and aren't duplicated — it doesn't judge whether they're good SEO
copy (keyword relevance, readability, slug structure). Flag this as a manual/LLM-assisted review
step in the report, not an automated SF check: sample 10-15 URLs and assess slug clarity,
keyword-to-intent match, and title/H1 alignment.

**3h. Performance**
SF's headless crawl does not populate real TTFB/DOM-ready/load timing by default — that requires
either the licensed PageSpeed Insights integration (`--use-pagespeed`, licensed) or a separate
pass (Lighthouse CLI or Playwright timing). Don't claim performance numbers
in the report unless one of those actually ran; if none ran, mark the Performance section
"not measured this run" rather than leaving stale placeholder text.

### Step 4: Parse Screaming Frog Output

Read the exported CSV/TSV files from `$OUTPUT/`:

```bash
# Key files to parse
ls "$OUTPUT"/*.csv "$OUTPUT"/*.xlsx 2>/dev/null
```

Extract and categorize issues:

| Category | Source File | What to Extract |
|---|---|---|
| Broken links (4xx) | Client Error (4xx).csv | URL, status code, inlink count |
| Server errors (5xx) | Server Error (5xx).csv | URL, status code |
| Missing titles | Page Titles Missing.csv | URLs without title tags |
| Duplicate titles | Page Titles Duplicate.csv | URLs sharing same title |
| Missing meta descriptions | Meta Description Missing.csv | URLs |
| Duplicate meta descriptions | Meta Description Duplicate.csv | URLs sharing same description |
| Title/meta length issues | Page Titles Over/Below X Characters.csv, Meta Description Over/Below X Characters.csv | URLs outside best-practice length |
| Missing H1 | H1 Missing.csv | URLs |
| Missing alt text | Images Missing Alt Text.csv | Image URLs, page URLs |
| Oversized images | Images Over X KB.csv | Image URLs, page URLs, size |
| Redirect chains | Redirect Chains.csv | Chain length, URLs |
| Orphan pages | Orphan Pages.csv | URLs not linked internally |
| Non-indexable canonicals | Non-Indexable Canonical.csv | URLs with bad canonicals |
| Structured data | manual (Step 3a) | Missing/invalid JSON-LD per template |
| OG/Twitter tags | manual or `/og-meta-check` (Step 3b) | Missing tags per page |
| robots.txt / sitemap health | manual (Step 3c) | Blocking rules, stale/missing sitemap entries |
| Accessibility | axe-core or an equivalent audit tool (Step 3d) | WCAG violations beyond alt text |
| URL/title/H1 SEO quality | manual/LLM review (Step 3g) | Weak slugs, keyword mismatch |
| Performance | Lighthouse or an equivalent tool (Step 3h) | TTFB, DOM ready, load — only if actually run |

### Step 5: Spot-Check with Browse

After parsing Screaming Frog data, optionally use a playwright script to spot-check top issues visually.


### Step 6: Generate Report

Output the report directly to the conversation in this format:

```markdown
## Site Crawl Report: <domain>
**Date:** <date> | **Pages crawled:** N | **Tool:** Screaming Frog

### Summary
| Metric | Value |
|---|---|
| Total pages | N |
| Healthy pages | N (X%) |
| Pages with issues | N (X%) |
| Broken links (4xx) | N |
| Server errors (5xx) | N |
| Missing titles | N |
| Duplicate titles | N |
| Missing meta descriptions | N |
| Duplicate meta descriptions | N |
| Title/meta description length issues | N |
| Missing H1 | N |
| Images missing alt text | N |
| Oversized images (over threshold) | N |
| Redirect chains | N |
| Orphan pages | N |
| Non-indexable canonicals | N |
| Pages missing/invalid structured data | N (of M sampled) |
| Pages missing OG/Twitter tags | N (of M sampled) |
| robots.txt / sitemap issues | N (list) |
| Accessibility violations (beyond alt text) | N (of M sampled) — "not measured" if Step 3d skipped |
| Avg page load (TTFB) | Nms — "not measured" if Step 3h skipped |
| JS console errors | N |

### Critical Issues (fix immediately)
1. **[issue]** — [N pages affected] — [specific URLs]
   **Fix:** [concrete action]

### Important Issues (fix this week)
...

### Minor Issues (backlog)
...

### Structured Data & Social Meta (Step 3a/3b)
- Templates checked: [list]
- Missing/invalid JSON-LD: [list, or "none"]
- Missing OG/Twitter tags: [list, or "none"]

### robots.txt / Sitemap Health (Step 3c)
- robots.txt: [status, blocking rules if any]
- sitemap.xml: [status, stale/missing entries]

### Accessibility (Step 3d)
- [Summary of axe-core or equivalent audit findings, or "not measured this run"]

### URL / Title / H1 SEO Quality (Step 3g)
- [Manual review notes on the sampled URLs, or "not reviewed this run"]

### Performance Snapshot (Step 3h)
- Homepage TTFB: Nms, or "not measured this run"
- DOM ready: Nms
- Full load: Nms
- Console errors: [list or "none"]

### Screenshots
Screenshots saved to /tmp/crawl-responsive-*.png
```

### Step 7: Generate Fix Plan

After the report, create a prioritized fix plan:

```markdown
## Fix Plan: <domain>

### Priority 1: Broken Links (estimated: Xh)
- [ ] Fix N broken internal links [list top 5 URLs]
- [ ] Fix N broken external links or remove references
- [ ] Set up redirect for moved pages

### Priority 2: Missing SEO Elements (estimated: Xh)
- [ ] Add title tags to N pages [list]
- [ ] Add meta descriptions to N pages [list]
- [ ] Add H1 tags to N pages [list]

### Priority 3: Redirect Chains (estimated: Xh)
- [ ] Shorten N redirect chains to single hop

### Priority 4: Images (estimated: Xh)
- [ ] Add alt text to N images
- [ ] Compress/resize N oversized images

### Priority 5: Orphan Pages (estimated: Xh)
- [ ] Link or remove N orphan pages

### Priority 6: Structured Data & Social Meta (estimated: Xh)
- [ ] Add/fix JSON-LD on N templates [list]
- [ ] Add missing OG/Twitter tags to N pages [list]

### Priority 7: robots.txt / Sitemap (estimated: Xh)
- [ ] Fix N blocking robots.txt rules
- [ ] Remove/update N stale sitemap entries

### Priority 8: Accessibility (estimated: Xh)
- [ ] Fix N WCAG violations [list, from axe-core or an equivalent audit tool]

### Priority 9: SEO Copy Quality (estimated: Xh)
- [ ] Rewrite N weak titles/H1s/slugs [list]
```

### Step 8: Save Results

```bash
# Save Screaming Frog output location
echo "Crawl data saved to: $OUTPUT"

# Optionally save report as markdown
# Only if user requests it
```

## Important Rules

- Screaming Frog is the primary tool. Install via `brew install screamingfrogseospider`.
- Report issues by severity (critical > important > minor)
- Fix plan must have concrete actions, not vague "improve SEO"
- Include time estimates in fix plan
- Screenshots go to /tmp, not project directories
- Don't modify the site — this is read-only audit
- If the site requires auth, ask the user for credentials before crawling
- Step 3 (schema, OG tags, robots/sitemap health, accessibility, image weight, meta length/dupes,
  URL/title/H1 quality, performance) is **mandatory**, not optional — SF's default exports alone
  don't satisfy a full technical SEO audit. If a Step 3 sub-check is skipped (no time, no
  Lighthouse available, etc.), say so explicitly in the report ("not measured this run") instead
  of omitting the section or leaving stale placeholder numbers.

## Screaming Frog Reference

**Binary:** `/Applications/Screaming Frog SEO Spider.app/Contents/MacOS/ScreamingFrogSEOSpiderLauncher`
**Key flags:** `--headless`, `--crawl <url>`, `--output-folder <dir>`, `--export-tabs`, `--bulk-export`, `--save-report`, `--create-sitemap`
**Config files:** Can supply custom crawl configs with `--config <path>`
