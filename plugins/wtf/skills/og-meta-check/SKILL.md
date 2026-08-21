---
name: og-meta-check
description: |
  Check that a page emits the full Open Graph + Twitter Card meta-tag set —
  the tags that control link-preview cards on iMessage, Slack, WhatsApp, X,
  and LinkedIn. Use when the user says "check og tags", "check meta tags",
  "social preview check", "twitter card check", "check open graph", or wants
  a standalone pass/fail on a page's share-preview tags without running a
  full content gate. Emits a PASS/FAIL verdict with the missing-tag list.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - WebFetch
---

# OG meta check: Open Graph + Twitter Card verification

You are a **gatekeeper, not an editor**. This check resolves to **PASS** or
**FAIL** with evidence — the rendered `<head>` tags or a grep hit against the
built HTML. If it fails, stop and tell the user:

> "OG meta gate incomplete. Page `<path>` is missing: [list of missing tags]. Add them to the shared layout before publishing."

**Applies to:** every routable page in every project that ships HTML —
landing pages, blog posts, product pages, marketing sites, dashboards with
public share routes.

**Does NOT apply to:** API-only services, internal admin panels with no
public sharing, redirect-only pages.

---

## Why this matters

Without a full, correct Open Graph + Twitter Card tag set, link previews on
iMessage, Slack, WhatsApp, X, and LinkedIn collapse to a bare URL — a silent
visibility tax on everything you ship. This is a narrow, mechanical check:
one shared layout should render all the tags below from props, and this
skill verifies the built output actually has them.

## Required tags (the full set, no exceptions)

Rendered from **one shared layout** (pages pass props) — never hand-pasted
per page:

```html
<!-- Core -->
<title>{title}</title>
<meta name="description" content="{description}" />
<link rel="canonical" href="{absoluteCanonicalUrl}" />

<!-- Open Graph -->
<meta property="og:site_name" content="{brand}" />
<meta property="og:type" content="{ogType}" />              <!-- website | article | profile -->
<meta property="og:title" content="{title}" />
<meta property="og:description" content="{description}" />
<meta property="og:url" content="{absoluteCanonicalUrl}" />
<meta property="og:locale" content="en_US" />               <!-- match site language -->
<meta property="og:image" content="{absoluteImageUrl}" />
<meta property="og:image:secure_url" content="{absoluteImageUrl}" />
<meta property="og:image:type" content="image/jpeg" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="624" />            <!-- or 630 if the project uses standard OG -->
<meta property="og:image:alt" content="{imageAlt}" />

<!-- Twitter / X -->
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{title}" />
<meta name="twitter:description" content="{description}" />
<meta name="twitter:image" content="{absoluteImageUrl}" />
<meta name="twitter:image:alt" content="{imageAlt}" />
<meta name="twitter:site" content="@handle" />               <!-- if the brand has one -->
```

## Hard rules

| Rule | Why |
|---|---|
| URLs in `og:url`, `og:image`, `og:image:secure_url`, `twitter:image`, `canonical` MUST be **absolute** (`https://domain/path`), not relative | Scrapers do not resolve relative URLs and silently drop the preview |
| `og:image` MUST be **JPEG**, served over HTTPS, **≥ 1200×624** (1200×630 acceptable), **< 5 MB**, ideally < 300 KB | LinkedIn rejects PNG transparency; X rejects > 5 MB; large files block sharing on slow networks |
| `og:title` should be **≤ 70 chars**; `og:description` **≤ 200 chars** (target 150) | Truncation in preview cards looks unfinished |
| Every page MUST have an `og:image` — fall back to a sitewide default (`/img/og/default.jpg`) if no per-page hero exists | Bare URL previews look broken; a default image is always better than none |
| `twitter:card` MUST be `summary_large_image` unless the image is truly square small | Default `summary` produces a tiny thumbnail that buries the image |
| `og:image:alt` MUST be present and descriptive | Screen readers and accessibility audits flag missing alt; some scrapers use it |
| **One layout component renders all of these**; pages pass props | Per-page hand-rolled tags drift, develop typos, and miss new requirements |

## Verification (run before declaring done)

```bash
# 1. Build the site
npm run build

# 2. Confirm tags rendered on every page
for f in dist/**/*.html dist/*.html; do
  echo "== $f =="
  grep -oE '<(meta|link)[^>]*(og:|twitter:|canonical)[^>]*>' "$f" | wc -l
done
# Expect ≥ 18 matches per page (15 OG + 5 Twitter + canonical, give or take).

# 3. Validate with external scrapers (after deploy)
#    https://www.opengraph.xyz/url/<encoded-url>
#    https://cards-dev.twitter.com/validator
#    https://www.linkedin.com/post-inspector/
```

## Report

```
OG META CHECK — <page/URL>
 Tags found:    N / ~18 expected
 Missing:       [list, or "none"]
 Hard-rule violations: [list, or "none"]

VERDICT: PASS / FAIL — <what's missing, if FAIL>
```

Any FAIL → stop and tell the user what's missing. Never soften a FAIL into a
recommendation.

> This is Step 5 of `wtf:content-gate`, extracted so it can run standalone.
> `content-gate` delegates to this skill for its own Step 5 check.
