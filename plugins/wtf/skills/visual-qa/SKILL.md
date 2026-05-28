---
name: visual-qa
description: Capture top-to-bottom full-page screenshots of real pages at desktop/tablet/mobile viewports, grouped by page-layout, and render them into one tabbed HTML gallery for visual review. Use when user says "visual qa", "screenshot gallery", "full-page audit", "review the site visually", or wants a single artifact to scan every layout at every breakpoint after a UI change or deploy.
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
---

# /visual-qa — Full-Page Visual Review Gallery

Batched Playwright capture + single tabbed HTML gallery. The artifact you open after a UI change to scan every layout at every breakpoint without re-running anything.

## When to use

Reach for `/visual-qa` when you have a **set** of URLs grouped by layout and want
full-page captures at every breakpoint collected into one persistent HTML gallery — the
artifact you open after a UI change or deploy to scan every layout without re-running
anything. For a quick one-off look at a single URL, a plain screenshot tool is lighter
weight; for a code-level audit (accessibility, design tokens) or an SEO crawl, use a tool
built for that — `/visual-qa` is about reviewing rendered pixels.

## User-invocable

`/visual-qa <project-path>` — reads `<project-path>/.visual-qa/urls.json`, writes PNGs + `gallery.html` into `<project-path>/.visual-qa/out/`.

Example:
```
/visual-qa ~/projects/mysite
```

## Arguments

- `<project-path>` — repo root containing `.visual-qa/urls.json`
- `--out <dir>` — override output dir (default `<project-path>/.visual-qa/out`)
- `--env local|production` — which `baseUrls.<env>` to prepend to each sample path (default **local**)
- `--only <layout-id>` — capture just one layout
- `--locales en,de` — filter to a subset of locales declared in config
- `--force` — re-capture even if PNGs are fresh (default: skip if PNG mtime > urls.json mtime)

## Config: `.visual-qa/urls.json`

Paths only (no host) so the same config runs against `localhost` and production unchanged. Locale is auto-derived from the first path segment if it matches one of `locales`.

```json
{
  "title": "My Site",
  "baseUrls": { "local": "http://localhost:3000", "production": "https://example.com" },
  "locales": ["en", "de", "es", "fr", "br", "id"],
  "defaultLocale": "en",
  "layouts": [
    {
      "id": "hub",
      "label": "Hub / Hub-and-Spoke",
      "samples": [
        "/en/chief-ai-officer/",
        "/de/chief-ai-officer/",
        "/fr/chief-ai-officer/",
        { "path": "/en/ask-ctaio/", "extraDelayMs": 2000 }
      ]
    }
  ]
}
```

**i18n rule:** every layout SHOULD include at least one sample per supported locale (when that layout exists in the locale). Slugs translate per locale in many sites (e.g. `/en/salary/` → `/de/gehalt/` → `/fr/salaire/`) so use explicit per-locale paths rather than templates. 404s during capture are reported and surface as "No screenshot" tiles in the gallery — useful gap signal.

**Per-sample escape hatches** (object form): `waitForSelector`, `extraDelayMs`, `locale` (override auto-detection).

## Instructions

### Step 0: First-run bootstrap

On a fresh machine, install dependencies once:
```bash
bash <skill-dir>/setup.sh
```

`<skill-dir>` is wherever this skill is installed — `~/.claude/skills/wtf-visual-qa/`
if you used `install.sh`, or the plugin's `skills/visual-qa/` directory if you
installed via the marketplace. `capture.mjs` exits with a clear hint if Playwright
isn't installed, so you'll know.

### Step 1: Validate

1. Confirm `<project-path>/.visual-qa/urls.json` exists. **If it does NOT exist**, run scaffold:
   ```bash
   node <skill-dir>/scaffold.mjs <project-path>
   ```
   Scaffold detects: framework (Astro / Next.js), dev port + production URL from `astro.config.*`, locales + `defaultLocale`, and groups pages under `src/pages/` into templates (max 3 samples per template, prioritizing the default locale). Writes `<project-path>/.visual-qa/urls.json`. **Review the generated config before capturing** — sample selection is heuristic; you may want to swap in more representative URLs per template, or drop noisy templates.
   ```bash
   # If a config already exists and you want to regenerate:
   node <skill-dir>/scaffold.mjs <project-path> --force
   ```

### Step 2: Capture

```bash
node <skill-dir>/capture.mjs \
  --config <project-path>/.visual-qa/urls.json \
  --out <project-path>/.visual-qa/out \
  --env local           # or --env production
```

If `--env local` and the dev server isn't reachable, capture exits non-zero with a hint to start the dev server (or pass `--env production`).

The script:
- Launches Chromium headless
- For each layout × sample × viewport (desktop 1280×800, tablet 768×1024, mobile 390×844):
  - `goto(url, { waitUntil: 'networkidle' })`
  - `autoScroll` to trigger lazy-load
  - Wait for `document.fonts.ready`
  - `screenshot({ fullPage: true })`
- Writes to `out/<layout-id>/<url-slug>/<viewport>.png`
- Skips files already fresh relative to `urls.json` mtime unless `--force`

### Step 3: Render

```bash
node <skill-dir>/render.mjs \
  --config <project-path>/.visual-qa/urls.json \
  --out <project-path>/.visual-qa/out
```

Emits `out/gallery.html` with:
- Sticky tab bar `[Desktop] [Tablet] [Mobile]` (CSS-only radio, no JS framework)
- Layout sections per tab, sample columns side-by-side
- `<img loading="lazy">` for snappy open
- Click-to-zoom opens raw PNG in new tab

### Step 4: Report

Print to user:
- Total PNGs written / skipped
- Path to `gallery.html`
- `open <gallery.html>` invitation

## Tradeoffs / known limits

- Authenticated pages: not handled in v1. Public URLs only.
- JS-heavy pages (chat surfaces, calculators): may need per-URL `waitForSelector` overrides in `urls.json`.
- File size: 50+ full-page PNGs at desktop width can be 30-60 MB total. Gallery uses lazy-load so open time is fine; committing to git is not.
- `.visual-qa/out/` should be gitignored; keep only `urls.json` (and optionally a recent `gallery.html` if useful for PR review).
