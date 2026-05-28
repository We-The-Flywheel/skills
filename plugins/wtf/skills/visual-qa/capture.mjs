#!/usr/bin/env node
// visual-qa: capture full-page screenshots at desktop/tablet/mobile.
//
// Usage:
//   node capture.mjs --config <urls.json> --out <dir> [--env local|production] [--only <layout-id>] [--locales en,de] [--force]
//
// Default --env is `local` (the whole point: catch issues before they hit prod).

import fs from 'node:fs';
import path from 'node:path';

let chromium;
try {
  ({ chromium } = await import('playwright'));
} catch {
  const here = path.dirname(new URL(import.meta.url).pathname);
  console.error(`Playwright not installed. Run: bash ${path.join(here, 'setup.sh')}`);
  process.exit(5);
}

const VIEWPORTS = [
  { id: 'desktop', width: 1280, height: 800, deviceScaleFactor: 1 },
  { id: 'tablet',  width: 768,  height: 1024, deviceScaleFactor: 2 },
  { id: 'mobile',  width: 390,  height: 844, deviceScaleFactor: 3, isMobile: true, hasTouch: true }
];

function parseArgs(argv) {
  const args = { env: 'local', force: false };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--config') args.config = argv[++i];
    else if (a === '--out') args.out = argv[++i];
    else if (a === '--only') args.only = argv[++i];
    else if (a === '--locales') args.localesFilter = argv[++i].split(',').map(s => s.trim()).filter(Boolean);
    else if (a === '--env') args.env = argv[++i];
    else if (a === '--force') args.force = true;
  }
  if (!args.config || !args.out) {
    console.error('Usage: capture.mjs --config <urls.json> --out <dir> [--env local|production] [--only <id>] [--locales en,de] [--force]');
    process.exit(2);
  }
  return args;
}

function slug(s) {
  return s
    .replace(/^https?:\/\//, '')
    .replace(/\/$/, '')
    .replace(/[^a-z0-9]+/gi, '-')
    .replace(/^-|-$/g, '')
    .toLowerCase();
}

// Expand a layout's `samples` into concrete URLs.
// Each sample is a string (path) or { path, locale?, waitForSelector?, extraDelayMs? }.
// Locale is auto-derived from the first path segment if not given.
function expandLayout(layout, config, baseUrl, localesFilter) {
  const known = new Set(config.locales || ['en']);
  const samples = Array.isArray(layout.samples) ? layout.samples : [];
  const out = [];
  for (const raw of samples) {
    const s = typeof raw === 'string' ? { path: raw } : { ...raw };
    if (!s.locale) {
      const seg = (s.path || '').split('/').filter(Boolean)[0];
      s.locale = known.has(seg) ? seg : (config.defaultLocale || 'en');
    }
    if (localesFilter && !localesFilter.includes(s.locale)) continue;
    s.url = baseUrl.replace(/\/$/, '') + s.path;
    out.push(s);
  }
  return out;
}

async function autoScroll(page) {
  await page.evaluate(async () => {
    await new Promise((resolve) => {
      let total = 0;
      const step = 400;
      const timer = setInterval(() => {
        window.scrollBy(0, step);
        total += step;
        if (total >= document.body.scrollHeight) {
          clearInterval(timer);
          window.scrollTo(0, 0);
          setTimeout(resolve, 200);
        }
      }, 80);
    });
  });
}

async function captureOne(browser, sample, viewport, outFile) {
  const context = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
    deviceScaleFactor: viewport.deviceScaleFactor,
    isMobile: !!viewport.isMobile,
    hasTouch: !!viewport.hasTouch,
    userAgent: viewport.isMobile
      ? 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
      : undefined
  });
  const page = await context.newPage();
  try {
    const resp = await page.goto(sample.url, { waitUntil: 'domcontentloaded', timeout: 45000 });
    if (resp && resp.status() >= 400) {
      throw new Error(`HTTP ${resp.status()}`);
    }
    try { await page.waitForLoadState('networkidle', { timeout: 15000 }); } catch {}
    await autoScroll(page);
    try { await page.waitForLoadState('networkidle', { timeout: 10000 }); } catch {}
    try { await page.evaluate(() => document.fonts && document.fonts.ready); } catch {}
    if (sample.waitForSelector) {
      try { await page.waitForSelector(sample.waitForSelector, { timeout: 10000 }); } catch {}
    }
    if (sample.extraDelayMs) {
      await page.waitForTimeout(sample.extraDelayMs);
    }
    fs.mkdirSync(path.dirname(outFile), { recursive: true });
    await page.screenshot({ path: outFile, fullPage: true });
    return { ok: true };
  } catch (err) {
    return { ok: false, error: err.message };
  } finally {
    await context.close();
  }
}

function isFresh(outFile, configMtime) {
  try {
    const st = fs.statSync(outFile);
    return st.mtimeMs > configMtime;
  } catch {
    return false;
  }
}

async function reachable(url) {
  try {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 3000);
    const resp = await fetch(url, { signal: ctrl.signal });
    clearTimeout(t);
    return resp.status < 500;
  } catch {
    return false;
  }
}

async function main() {
  const args = parseArgs(process.argv);
  const configPath = path.resolve(args.config);
  const outDir = path.resolve(args.out);

  const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  const configMtime = fs.statSync(configPath).mtimeMs;

  const baseUrls = config.baseUrls || {};
  const baseUrl = baseUrls[args.env];
  if (!baseUrl) {
    console.error(`No baseUrls.${args.env} in config. Available: ${Object.keys(baseUrls).join(', ') || '(none)'}`);
    process.exit(3);
  }

  if (!(await reachable(baseUrl))) {
    console.error(`Base URL not reachable: ${baseUrl}`);
    if (args.env === 'local') {
      console.error(`Start the dev server first (e.g., \`npm run dev\` in the project), or run with --env production.`);
    }
    process.exit(4);
  }

  const layouts = args.only
    ? config.layouts.filter(l => l.id === args.only)
    : config.layouts;

  if (layouts.length === 0) {
    console.error(`No layouts matched (only=${args.only})`);
    process.exit(3);
  }

  fs.mkdirSync(outDir, { recursive: true });

  // Persist resolved environment + base URL for the renderer.
  fs.writeFileSync(
    path.join(outDir, '_meta.json'),
    JSON.stringify({ env: args.env, baseUrl, capturedAt: new Date().toISOString() }, null, 2)
  );

  const browser = await chromium.launch({ headless: true });
  let captured = 0, skipped = 0, failed = 0;
  const failures = [];

  for (const layout of layouts) {
    const samples = expandLayout(layout, config, baseUrl, args.localesFilter);
    for (const sample of samples) {
      const sampleSlug = slug(sample.path);
      for (const vp of VIEWPORTS) {
        const outFile = path.join(outDir, layout.id, sample.locale, sampleSlug, `${vp.id}.png`);
        if (!args.force && isFresh(outFile, configMtime)) {
          skipped++;
          continue;
        }
        process.stdout.write(`[${layout.id}/${sample.locale}] ${vp.id.padEnd(7)} ${sample.url}\n`);
        const result = await captureOne(browser, sample, vp, outFile);
        if (result.ok) captured++;
        else { failed++; failures.push({ url: sample.url, viewport: vp.id, error: result.error }); }
      }
    }
  }

  await browser.close();

  console.log('---');
  console.log(`Env: ${args.env}  Base: ${baseUrl}`);
  console.log(`Captured: ${captured}  Skipped (fresh): ${skipped}  Failed: ${failed}`);
  if (failures.length) {
    console.log('Failures:');
    for (const f of failures) console.log(`  ${f.viewport}  ${f.url}  --  ${f.error}`);
  }
  console.log(`Output: ${outDir}`);
  process.exit(failed > 0 ? 1 : 0);
}

main().catch(err => { console.error(err); process.exit(1); });
