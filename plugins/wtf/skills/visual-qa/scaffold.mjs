#!/usr/bin/env node
// visual-qa: scaffold .visual-qa/urls.json by inspecting an Astro project.
//
// Detects:
//   - dev port + production "site" URL from astro.config.mjs
//   - locales list (+ defaultLocale) from astro.config.mjs
//   - templates by grouping pages under src/pages/<locale?>/ by structure
//   - samples (max 3 per template), prioritizing the default locale
//
// Usage:
//   node scaffold.mjs <project-path> [--force] [--out <urls.json>]

import fs from 'node:fs';
import path from 'node:path';

const SKILL_DIR = path.dirname(new URL(import.meta.url).pathname);

function parseArgs(argv) {
  const args = { force: false };
  const rest = [];
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--force') args.force = true;
    else if (a === '--out') args.out = argv[++i];
    else rest.push(a);
  }
  args.projectPath = rest[0];
  if (!args.projectPath) {
    console.error('Usage: scaffold.mjs <project-path> [--force] [--out <urls.json>]');
    process.exit(2);
  }
  return args;
}

function readIfExists(p) {
  try { return fs.readFileSync(p, 'utf8'); } catch { return null; }
}

function extractFirst(text, regex) {
  if (!text) return null;
  const m = text.match(regex);
  return m ? m[1] : null;
}

function detectFramework(root) {
  if (fs.existsSync(path.join(root, 'astro.config.mjs')) || fs.existsSync(path.join(root, 'astro.config.ts'))) return 'astro';
  if (fs.existsSync(path.join(root, 'next.config.js')) || fs.existsSync(path.join(root, 'next.config.mjs'))) return 'nextjs';
  return null;
}

function detectAstroConfig(root) {
  const candidates = ['astro.config.mjs', 'astro.config.ts', 'astro.config.js'];
  let text = null;
  for (const c of candidates) {
    text = readIfExists(path.join(root, c));
    if (text) break;
  }
  if (!text) return {};
  const port = parseInt(extractFirst(text, /port:\s*(\d+)/) || '0', 10) || 4321;
  const site = extractFirst(text, /site:\s*['"]([^'"]+)['"]/);
  const localesMatch = text.match(/locales:\s*\[([\s\S]*?)\]/);
  const locales = localesMatch
    ? Array.from(localesMatch[1].matchAll(/['"]([a-z]{2,3}(?:-[A-Z]{2})?)['"]/g)).map(m => m[1])
    : [];
  const defaultLocale = extractFirst(text, /defaultLocale:\s*['"]([^'"]+)['"]/);
  const prefixDefault = !/prefixDefaultLocale:\s*false/.test(text);
  return { port, site, locales, defaultLocale, prefixDefaultLocale: prefixDefault };
}

function detectNextConfig(root) {
  return { port: 3000, locales: [], prefixDefaultLocale: false };
}

function walkPages(pagesDir) {
  const out = [];
  function walk(dir, rel) {
    let entries;
    try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
    for (const e of entries) {
      const full = path.join(dir, e.name);
      const r = path.join(rel, e.name);
      if (e.isDirectory()) walk(full, r);
      else if (e.isFile() && /\.(astro|mdx?|tsx?)$/.test(e.name) && !e.name.startsWith('_')) {
        out.push(r);
      }
    }
  }
  walk(pagesDir, '');
  return out;
}

// Convert a file path under src/pages/ into a URL path.
//   en/index.astro          -> /en/        (or / if prefixDefault=false and en is default)
//   en/foo.astro            -> /en/foo/
//   en/bar/index.astro      -> /en/bar/
//   en/bar/baz.astro        -> /en/bar/baz/
//   404.astro               -> /404/       (skipped)
//   [slug].astro            -> dynamic, skipped
function fileToUrlPath(relFile, defaultLocale, prefixDefault) {
  // Skip dynamic routes (require runtime data).
  if (/\[.+?\]/.test(relFile)) return null;
  let p = '/' + relFile.replace(/\\/g, '/').replace(/\.(astro|mdx?|tsx?)$/, '');
  p = p.replace(/\/index$/, '/');
  if (!p.endsWith('/')) p += '/';
  // If en is default and prefixDefaultLocale=false, /en/foo/ → /foo/
  if (!prefixDefault && defaultLocale && p.startsWith('/' + defaultLocale + '/')) {
    p = p.replace(new RegExp('^/' + defaultLocale + '/'), '/');
    if (p === '') p = '/';
  }
  return p;
}

// Group a list of URL paths into templates by structure.
// Heuristics:
//   /                        -> template "home"
//   /<locale>/               -> template "home"
//   /<seg>/                  -> template "<seg>" (single-page top-level)
//   /<seg>/<x>/              -> template "<seg>-detail" (sub-pages under section)
//   /<locale>/<seg>/         -> template "<seg>" (treat locale as transparent)
//   /<locale>/<seg>/<x>/     -> template "<seg>-detail"
function groupTemplates(urlPaths, locales) {
  const localeSet = new Set(locales);
  function classify(p) {
    const segs = p.split('/').filter(Boolean);
    // Strip leading locale if present
    if (segs.length > 0 && localeSet.has(segs[0])) segs.shift();
    if (segs.length === 0) return { id: 'home', label: 'Home' };
    if (segs.length === 1) {
      const s = segs[0];
      // Conventional names get nicer labels
      const label = s.replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
      return { id: s, label };
    }
    // Multi-segment: bucket by first segment + treat as "<seg>-detail"
    const root = segs[0];
    const label = root.replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) + ' — Detail';
    return { id: root + '-detail', label };
  }
  const groups = new Map(); // id -> { label, paths: [] }
  for (const p of urlPaths) {
    const { id, label } = classify(p);
    if (!groups.has(id)) groups.set(id, { id, label, paths: [] });
    groups.get(id).paths.push(p);
  }
  return Array.from(groups.values());
}

function pathLocale(p, locales) {
  const seg = p.split('/').filter(Boolean)[0];
  return locales.includes(seg) ? seg : null;
}

function sampleTemplate(group, defaultLocale, locales, maxPerLocale = 3) {
  // Sort: defaultLocale first, then by path length (shorter = more representative), max 3.
  const byLocale = new Map(); // locale -> paths
  for (const p of group.paths) {
    const loc = pathLocale(p, locales) || defaultLocale || 'en';
    if (!byLocale.has(loc)) byLocale.set(loc, []);
    byLocale.get(loc).push(p);
  }
  const samples = [];
  // Prefer up to 3 from default locale (shortest paths first), then 1 each from other locales.
  const def = defaultLocale || 'en';
  if (byLocale.has(def)) {
    byLocale.get(def).sort((a, b) => a.length - b.length).slice(0, maxPerLocale).forEach(p => samples.push(p));
  }
  for (const [loc, paths] of byLocale.entries()) {
    if (loc === def) continue;
    paths.sort((a, b) => a.length - b.length).slice(0, 1).forEach(p => samples.push(p));
  }
  return samples;
}

function buildConfig(root) {
  const framework = detectFramework(root);
  if (!framework) throw new Error('Could not detect framework (looked for astro.config.* / next.config.*)');

  const cfg = framework === 'astro' ? detectAstroConfig(root) : detectNextConfig(root);
  const pagesDir = framework === 'astro'
    ? path.join(root, 'src/pages')
    : path.join(root, 'src/pages'); // Next.js also typical
  if (!fs.existsSync(pagesDir)) throw new Error('No pages dir at ' + pagesDir);

  const files = walkPages(pagesDir);
  if (files.length === 0) throw new Error('No page files found under ' + pagesDir);

  const locales = cfg.locales && cfg.locales.length ? cfg.locales : ['en'];
  const defaultLocale = cfg.defaultLocale || locales[0] || 'en';
  const prefixDefault = cfg.prefixDefaultLocale !== false;

  const urlPaths = files
    .map(f => fileToUrlPath(f, defaultLocale, prefixDefault))
    .filter(Boolean)
    // Drop 404 / error pages
    .filter(p => !/(^|\/)404\//.test(p))
    // Drop very long sample paths (likely dynamic-generated detail with non-representative slugs we lucked into)
    .sort();

  const groups = groupTemplates(urlPaths, locales);

  // Build layouts, sample each, sorted by sample count descending so most-prominent templates come first.
  const layouts = groups
    .map(g => ({ id: g.id, label: g.label, samples: sampleTemplate(g, defaultLocale, locales) }))
    .filter(l => l.samples.length > 0)
    .sort((a, b) => b.samples.length - a.samples.length);

  const baseUrls = { local: `http://localhost:${cfg.port}` };
  if (cfg.site) baseUrls.production = cfg.site.replace(/\/$/, '');

  return {
    title: path.basename(root),
    baseUrls,
    locales,
    defaultLocale,
    layouts
  };
}

function main() {
  const args = parseArgs(process.argv);
  const root = path.resolve(args.projectPath);
  if (!fs.existsSync(root)) {
    console.error('Project path does not exist: ' + root);
    process.exit(3);
  }
  const outFile = args.out
    ? path.resolve(args.out)
    : path.join(root, '.visual-qa', 'urls.json');

  if (fs.existsSync(outFile) && !args.force) {
    console.error('Refusing to overwrite existing: ' + outFile);
    console.error('Pass --force to overwrite, or remove it first.');
    process.exit(4);
  }

  const config = buildConfig(root);
  fs.mkdirSync(path.dirname(outFile), { recursive: true });
  fs.writeFileSync(outFile, JSON.stringify(config, null, 2) + '\n');

  const totalSamples = config.layouts.reduce((s, l) => s + l.samples.length, 0);
  console.log(`✓ Wrote: ${outFile}`);
  console.log(`  Framework: ${detectFramework(root)}`);
  console.log(`  Templates: ${config.layouts.length}`);
  console.log(`  Locales:   ${config.locales.join(', ')} (default: ${config.defaultLocale})`);
  console.log(`  Samples:   ${totalSamples}`);
  console.log(`  Base URL:  ${config.baseUrls.local}${config.baseUrls.production ? ' · ' + config.baseUrls.production : ''}`);
  console.log('');
  console.log('Next steps:');
  console.log(`  1. Review/edit ${outFile}`);
  console.log(`  2. Run: node ${SKILL_DIR}/capture.mjs --config ${outFile} --out ${path.dirname(outFile)}/out`);
  console.log(`  3. Run: node ${SKILL_DIR}/render.mjs --config ${outFile} --out ${path.dirname(outFile)}/out`);
}

main();
