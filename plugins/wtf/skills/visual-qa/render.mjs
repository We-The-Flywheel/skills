#!/usr/bin/env node
// visual-qa: render captured PNGs into a tabbed HTML gallery with
// an action-chip "fix request" builder that emits a clipboard-ready prompt.
//
// Usage:
//   node render.mjs --config <urls.json> --out <output-dir>

import fs from 'node:fs';
import path from 'node:path';

const SKILL_DIR = path.dirname(new URL(import.meta.url).pathname);

const VIEWPORTS = [
  { id: 'desktop', label: 'Desktop · 1280×800', cardWidth: 640 },
  { id: 'tablet',  label: 'Tablet · 768×1024',   cardWidth: 384 },
  { id: 'mobile',  label: 'Mobile · 390×844',    cardWidth: 260 }
];

// Universal action set — same across every card. Add new ones here.
const ACTIONS = [
  { id: 'polish',    label: 'Visual polish' },
  { id: 'padding',   label: 'Better padding & spacing' },
  { id: 'whitespace',label: 'Less white space' },
  { id: 'contrast',  label: 'Improve font contrast' },
  { id: 'content',   label: 'Content issues' },
  { id: 'ai-images', label: 'Flag AI images' }
];

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--config') args.config = argv[++i];
    else if (a === '--out') args.out = argv[++i];
  }
  if (!args.config || !args.out) {
    console.error('Usage: render.mjs --config <urls.json> --out <dir>');
    process.exit(2);
  }
  return args;
}

function slug(s) {
  return s.replace(/^https?:\/\//, '').replace(/\/$/, '')
    .replace(/[^a-z0-9]+/gi, '-').replace(/^-|-$/g, '').toLowerCase();
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

function expandLayout(layout, config) {
  const known = new Set(config.locales || ['en']);
  const samples = Array.isArray(layout.samples) ? layout.samples : [];
  const out = [];
  for (const raw of samples) {
    const s = typeof raw === 'string' ? { path: raw } : { ...raw };
    if (!s.locale) {
      const seg = (s.path || '').split('/').filter(Boolean)[0];
      s.locale = known.has(seg) ? seg : (config.defaultLocale || 'en');
    }
    out.push(s);
  }
  return out;
}

function renderCard(layout, sample, viewport, outDir) {
  const sampleSlug = slug(sample.path);
  const relPath = `${layout.id}/${sample.locale}/${sampleSlug}/${viewport.id}.png`;
  const absPath = path.join(outDir, relPath);
  const exists = fs.existsSync(absPath);
  // Deterministic card id used for state lookup in clipboard JS.
  const cardId = `${layout.id}__${sample.locale}__${sampleSlug}`;

  // Encode card metadata as data-attributes so the JS doesn't need a parallel data dump.
  const dataAttrs = [
    `data-card-id="${escapeHtml(cardId)}"`,
    `data-layout-id="${escapeHtml(layout.id)}"`,
    `data-layout-label="${escapeHtml(layout.label || layout.id)}"`,
    `data-locale="${escapeHtml(sample.locale)}"`,
    `data-path="${escapeHtml(sample.path)}"`
  ].join(' ');

  let html = `<div class="sample-card" ${dataAttrs}>`;
  html += `<div class="sample-header">`;
  html += `<span class="locale">${escapeHtml(sample.locale)}</span>`;
  html += `<span class="path-small">${escapeHtml(sample.path)}</span>`;
  html += `<span class="card-state" aria-hidden="true"></span>`;
  html += `</div>`;
  if (exists) {
    html += `<a class="zoom" href="${escapeHtml(relPath)}" target="_blank" rel="noopener">`;
    html += `<img loading="lazy" src="${escapeHtml(relPath)}" alt="${escapeHtml(sample.path)} (${viewport.id})">`;
    html += `</a>`;
  } else {
    html += `<div class="missing">No screenshot · capture may have failed (HTTP 404 etc.)</div>`;
  }
  html += `<div class="card-footer"><span class="card-hint">Click image for per-page custom note</span></div>`;
  html += `</div>`;
  return html;
}

function renderTabPanel(viewport, config, outDir) {
  let html = `<div class="tab-panel" id="panel-${viewport.id}">`;
  for (const layout of config.layouts) {
    const samples = expandLayout(layout, config);
    const locales = new Set(samples.map(s => s.locale));
    const tplChips = ACTIONS.map(a =>
      `<button type="button" class="chip tpl-chip" data-tpl-action="${a.id}">${escapeHtml(a.label)}</button>`
    ).join('');
    html += `<section class="layout" data-layout-id="${escapeHtml(layout.id)}">`;
    html += `<h2><span class="tpl-name">${escapeHtml(layout.label || layout.id)}</span> <span class="tpl-id-h2">${escapeHtml(layout.id)}</span> <span class="badge muted">${samples.length} sample${samples.length === 1 ? '' : 's'} · ${locales.size} locale${locales.size === 1 ? '' : 's'}</span></h2>`;
    html += `<div class="tpl-cta" data-layout-id="${escapeHtml(layout.id)}">`;
    html += `<div class="tpl-cta-label">Apply to all <strong>${samples.length}</strong> screenshot${samples.length === 1 ? '' : 's'} of this template ↓</div>`;
    html += `<div class="chips">${tplChips}</div>`;
    html += `</div>`;
    html += `<div class="sample-grid">`;
    for (const s of samples) html += renderCard(layout, s, viewport, outDir);
    html += `</div></section>`;
  }
  html += `</div>`;
  return html;
}

function renderHTML(config, outDir, meta) {
  const radios = VIEWPORTS.map((vp, i) =>
    `<input type="radio" name="tab" id="tab-${vp.id}" ${i === 0 ? 'checked' : ''}>`
  ).join('\n');
  const labels = VIEWPORTS.map(vp =>
    `<label class="tab-label" for="tab-${vp.id}">${escapeHtml(vp.label)}</label>`
  ).join('\n');
  const panels = VIEWPORTS.map(vp => renderTabPanel(vp, config, outDir)).join('\n');

  const widthCss = VIEWPORTS.map(vp =>
    `#panel-${vp.id} .sample-grid { grid-template-columns: repeat(auto-fit, minmax(${vp.cardWidth}px, ${vp.cardWidth}px)); }`
  ).join('\n  ');

  // Inline manifest of templates for the "verify all templates captured" sanity check at top.
  const templateManifest = config.layouts.map(l => ({
    id: l.id, label: l.label || l.id, samples: (l.samples || []).length
  }));

  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Visual QA — ${escapeHtml(meta.title || 'Gallery')}</title>
<style>
  :root {
    --bg: #0b0b0d; --panel: #14141a; --border: #25252e;
    --text: #e6e6ea; --muted: #8b8b95; --accent: #f47921; --accent-on: #000;
  }
  * { box-sizing: border-box; }
  html, body { background: var(--bg); color: var(--text); margin: 0; font: 14px/1.4 -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
  header.top { position: sticky; top: 0; z-index: 20; background: rgba(11,11,13,0.95); backdrop-filter: blur(10px); border-bottom: 1px solid var(--border); padding: 14px 24px; }
  header.top h1 { margin: 0 0 4px; font-size: 16px; font-weight: 600; }
  header.top .meta { color: var(--muted); font-size: 12px; }
  .tabs { display: flex; gap: 4px; margin-top: 12px; }
  input[type="radio"][name="tab"] { display: none; }
  .tab-label { padding: 8px 16px; border: 1px solid var(--border); border-radius: 6px; cursor: pointer; color: var(--muted); user-select: none; font-size: 13px; }
  .tab-label:hover { color: var(--text); }
  .tab-panel { display: none; padding: 24px; }
  ${widthCss}
  #tab-desktop:checked ~ main #panel-desktop,
  #tab-tablet:checked  ~ main #panel-tablet,
  #tab-mobile:checked  ~ main #panel-mobile { display: block; }
  #tab-desktop:checked ~ header .tabs label[for="tab-desktop"],
  #tab-tablet:checked  ~ header .tabs label[for="tab-tablet"],
  #tab-mobile:checked  ~ header .tabs label[for="tab-mobile"] { color: var(--accent); border-color: var(--accent); }

  /* Top toolbar */
  .toolbar { display: flex; align-items: center; gap: 10px; margin-top: 14px; flex-wrap: wrap; }
  .toolbar button.primary { background: var(--accent); color: var(--accent-on); border: 0; padding: 9px 16px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 13px; }
  .toolbar button.primary:hover { filter: brightness(1.1); }
  .toolbar button.ghost { background: transparent; color: var(--muted); border: 1px solid var(--border); padding: 8px 14px; border-radius: 6px; cursor: pointer; font-size: 12px; }
  .toolbar button.ghost:hover { color: var(--text); border-color: var(--accent); }
  .toolbar .selection-count { color: var(--muted); font-size: 12px; }
  .toolbar .selection-count strong { color: var(--text); }
  .toolbar .toast { color: #5ad17f; font-size: 12px; opacity: 0; transition: opacity 0.2s; }
  .toolbar .toast.show { opacity: 1; }
  textarea.general-feedback { width: 100%; margin-top: 10px; background: var(--panel); color: var(--text); border: 1px solid var(--border); border-radius: 6px; padding: 10px 12px; font-size: 13px; font-family: inherit; resize: vertical; min-height: 44px; }
  textarea.general-feedback:focus { outline: none; border-color: var(--accent); }
  textarea.general-feedback.has-text { border-color: var(--accent); background: linear-gradient(180deg, rgba(244,121,33,0.06), rgba(244,121,33,0.02)); }

  /* Template manifest in header */
  details.manifest { margin-top: 10px; font-size: 12px; }
  details.manifest summary { cursor: pointer; color: var(--muted); user-select: none; }
  details.manifest summary:hover { color: var(--text); }
  details.manifest .template-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 6px 16px; margin-top: 10px; padding: 12px; border: 1px solid var(--border); border-radius: 6px; background: var(--panel); }
  details.manifest .template-list .row { display: flex; align-items: center; gap: 8px; }
  details.manifest .template-list .row .id { color: var(--accent); font-family: ui-monospace, Menlo, monospace; font-size: 11px; }
  details.manifest .template-list .row .lbl { color: var(--text); }
  details.manifest .template-list .row .cnt { color: var(--muted); font-size: 11px; margin-left: auto; }

  /* Layout sections */
  .layout { margin: 0 0 56px; }
  .layout h2 { font-size: 18px; margin: 0 0 16px; padding-bottom: 8px; border-bottom: 1px solid var(--border); display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; }
  .tpl-name { color: var(--text); }
  .tpl-id-h2 { color: var(--accent); font-family: ui-monospace, Menlo, monospace; font-size: 12px; font-weight: 500; }
  .badge.muted { background: var(--border); color: var(--muted); font-size: 11px; padding: 2px 8px; border-radius: 999px; font-weight: 400; }

  /* Template-level CTA — visually owns the screenshots below */
  .tpl-cta { background: linear-gradient(180deg, rgba(244,121,33,0.10), rgba(244,121,33,0.02)); border: 1px solid rgba(244,121,33,0.35); border-bottom: 0; border-radius: 8px 8px 0 0; padding: 12px 14px; margin-bottom: -1px; position: relative; }
  .tpl-cta::after { content: ''; position: absolute; left: 24px; right: 24px; bottom: -1px; height: 2px; background: var(--accent); opacity: 0.6; }
  .tpl-cta.has-selection { background: linear-gradient(180deg, rgba(244,121,33,0.22), rgba(244,121,33,0.06)); border-color: var(--accent); }
  .tpl-cta-label { color: var(--muted); font-size: 11px; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.4px; }
  .tpl-cta-label strong { color: var(--accent); }
  .tpl-cta.has-selection .tpl-cta-label { color: var(--text); }

  /* Sample grid — visually connected to the CTA above via an accent rail on the left */
  .sample-grid { display: grid; gap: 16px; justify-content: start; padding: 16px; border: 1px solid rgba(244,121,33,0.35); border-top: 0; border-radius: 0 0 8px 8px; background: rgba(244,121,33,0.02); }

  /* Sample card */
  .sample-card { background: var(--panel); border: 1px solid var(--border); border-radius: 6px; overflow: hidden; transition: border-color 0.15s, box-shadow 0.15s; cursor: zoom-in; position: relative; }
  .sample-card.has-selection { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent) inset; }
  .sample-header { padding: 8px 10px; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 8px; font-size: 11px; }
  .locale { background: var(--accent); color: var(--accent-on); padding: 1px 6px; border-radius: 3px; font-weight: 700; text-transform: uppercase; font-size: 10px; letter-spacing: 0.5px; flex-shrink: 0; }
  .path-small { color: var(--muted); font-family: ui-monospace, Menlo, monospace; word-break: break-all; flex: 1 1 auto; min-width: 0; }
  .card-state { width: 8px; height: 8px; border-radius: 50%; background: transparent; border: 1px solid var(--border); flex-shrink: 0; transition: all 0.15s; }
  .sample-card.has-selection .card-state { background: var(--accent); border-color: var(--accent); box-shadow: 0 0 6px var(--accent); }
  .zoom { display: block; background: #000; }
  .zoom img { display: block; width: 100%; height: auto; }
  .missing { padding: 24px; color: var(--muted); text-align: center; font-style: italic; font-size: 12px; }
  .card-footer { padding: 6px 10px; border-top: 1px solid var(--border); }
  .card-hint { color: var(--muted); font-size: 10px; }
  .sample-card.has-selection .card-hint { color: var(--accent); }

  /* Action chips (used in template CTA + modal) */
  .chips { display: flex; flex-wrap: wrap; gap: 6px; }
  .chip { background: transparent; color: var(--muted); border: 1px solid var(--border); border-radius: 999px; padding: 5px 12px; font-size: 12px; cursor: pointer; transition: all 0.1s; font-family: inherit; }
  .chip:hover { color: var(--text); border-color: var(--muted); }
  .chip.on { background: var(--accent); color: var(--accent-on); border-color: var(--accent); font-weight: 600; }
  .chip.partial { background: rgba(244,121,33,0.20); color: var(--accent); border-color: var(--accent); font-weight: 600; }
  input.note { width: 100%; background: transparent; color: var(--text); border: 1px solid var(--border); border-radius: 4px; padding: 8px 10px; font-size: 13px; font-family: inherit; }
  input.note:focus { outline: none; border-color: var(--accent); }
  input.note.has-text { border-color: var(--accent); }

  footer { padding: 24px; color: var(--muted); font-size: 12px; border-top: 1px solid var(--border); text-align: center; }

  /* Modal */
  .modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.92); z-index: 100; display: none; align-items: flex-start; justify-content: center; overflow: auto; padding: 24px; }
  .modal-overlay.open { display: flex; }
  .modal-inner { display: flex; flex-direction: column; gap: 12px; max-width: none; min-width: 320px; }
  .modal-toolbar { position: sticky; top: 0; display: flex; align-items: center; gap: 10px; padding: 10px 14px; background: rgba(11,11,13,0.95); backdrop-filter: blur(8px); border: 1px solid var(--border); border-radius: 6px; z-index: 1; flex-wrap: wrap; }
  .modal-toolbar .tpl { color: var(--text); font-weight: 600; font-size: 12px; }
  .modal-toolbar .tpl-id { color: var(--accent); font-family: ui-monospace, Menlo, monospace; font-size: 11px; }
  .modal-toolbar .locale { background: var(--accent); color: var(--accent-on); padding: 1px 6px; border-radius: 3px; font-weight: 700; text-transform: uppercase; font-size: 10px; }
  .modal-toolbar .path-small { color: var(--muted); font-family: ui-monospace, Menlo, monospace; font-size: 11px; word-break: break-all; }
  .modal-toolbar .close { margin-left: auto; background: transparent; border: 1px solid var(--border); color: var(--muted); padding: 4px 10px; border-radius: 4px; cursor: pointer; font-size: 12px; }
  .modal-toolbar .close:hover { color: var(--text); border-color: var(--accent); }
  .modal-toolbar .hint { color: var(--muted); font-size: 11px; }
  .modal-img-frame { background: #000; border: 1px solid var(--border); border-radius: 6px; overflow: hidden; cursor: zoom-out; }
  .modal-img-frame img { display: block; height: auto; }   /* width set inline to natural width */
  .modal-controls { display: flex; flex-direction: column; gap: 8px; padding: 12px 14px; background: var(--panel); border: 1px solid var(--border); border-radius: 6px; }
  .modal-controls .chips { display: flex; flex-wrap: wrap; gap: 6px; }
  .modal-controls input.note { width: 100%; }
  .modal-controls .force-row { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--muted); }
  .modal-controls .force-row input { accent-color: var(--accent); }
</style>
</head>
<body>
${radios}
<header class="top">
  <h1>Visual QA — ${escapeHtml(meta.title || 'Gallery')}</h1>
  <div class="meta">${escapeHtml(meta.subtitle || '')}</div>
  <div class="tabs">${labels}</div>
  <div class="toolbar">
    <button type="button" class="primary" id="copyBtn">Copy fix request to clipboard</button>
    <button type="button" class="ghost" id="clearBtn">Clear all</button>
    <span class="selection-count" id="selCount"><strong>0</strong> pages · <strong>0</strong> actions selected</span>
    <span class="toast" id="toast">Copied ✓</span>
  </div>
  <textarea class="general-feedback" id="generalFeedback" rows="2" placeholder="General feedback for the whole site (optional) — applies on top of any per-template / per-page selections…"></textarea>
  <details class="manifest">
    <summary>Templates in this gallery (${templateManifest.length}) — verify coverage</summary>
    <div class="template-list">
      ${templateManifest.map(t =>
        `<div class="row"><span class="id">${escapeHtml(t.id)}</span><span class="lbl">${escapeHtml(t.label)}</span><span class="cnt">${t.samples} sample${t.samples === 1 ? '' : 's'}</span></div>`
      ).join('')}
    </div>
  </details>
</header>
<main>
${panels}
</main>
<footer>Generated ${new Date().toISOString()}${meta.envLine ? ' · ' + escapeHtml(meta.envLine) : ''} · click any screenshot to open it at its captured device-pixel width · ESC or click image to close</footer>

<div class="modal-overlay" id="modal" role="dialog" aria-modal="true" aria-hidden="true">
  <div class="modal-inner" id="modalInner">
    <div class="modal-toolbar">
      <span class="tpl" id="mTpl"></span>
      <span class="tpl-id" id="mTplId"></span>
      <span class="locale" id="mLocale"></span>
      <span class="path-small" id="mPath"></span>
      <span class="hint">Dictation lands in the note box below</span>
      <button type="button" class="close" id="mClose">Close (Esc)</button>
    </div>
    <div class="modal-img-frame" id="mFrame"><img id="mImg" alt=""></div>
    <div class="modal-controls">
      <div class="chips" id="mChips"></div>
      <input type="text" class="note" id="mNote" placeholder="Custom note for this page — start dictating now…">
      <label class="force-row"><input type="radio" name="mForce" id="mForce"> Force this note as a per-page custom instruction</label>
    </div>
  </div>
</div>

<script>
(function () {
  const SITE_TITLE = ${JSON.stringify(meta.title || 'site')};
  const BASE_URL = ${JSON.stringify(meta.baseUrl || '')};
  const ENV = ${JSON.stringify(meta.env || '')};
  const ACTION_LABELS = ${JSON.stringify(Object.fromEntries(ACTIONS.map(a => [a.id, a.label])))};

  // Card state shared across all 3 tabs (same card-id in each panel mirrors the same selection).
  const state = new Map(); // cardId -> { layoutId, layoutLabel, locale, path, actions: Set, note: string }
  let generalFeedback = '';

  function getActiveViewport() {
    const r = document.querySelector('input[name="tab"]:checked');
    return r ? r.id.replace('tab-', '') : 'desktop';
  }

  function ensureEntry(card) {
    const id = card.dataset.cardId;
    let e = state.get(id);
    if (!e) {
      e = {
        layoutId: card.dataset.layoutId,
        layoutLabel: card.dataset.layoutLabel,
        locale: card.dataset.locale,
        path: card.dataset.path,
        actions: new Set(),
        note: ''
      };
      state.set(id, e);
    }
    return e;
  }

  function syncCardClasses(card) {
    const id = card.dataset.cardId;
    const e = state.get(id);
    const hasSel = e && (e.actions.size > 0 || e.note.trim().length > 0);
    // Apply to ALL cards with this id across tab panels.
    document.querySelectorAll('[data-card-id="' + CSS.escape(id) + '"]').forEach(c => {
      c.classList.toggle('has-selection', !!hasSel);
      // Sync chip states.
      c.querySelectorAll('.chip').forEach(chip => {
        chip.classList.toggle('on', e && e.actions.has(chip.dataset.action));
      });
      // Sync notes.
      const n = c.querySelector('.note');
      if (n && e) {
        if (document.activeElement !== n) n.value = e.note;
        n.classList.toggle('has-text', e.note.trim().length > 0);
      }
    });
  }

  function updateCount() {
    let pages = 0, actions = 0;
    for (const e of state.values()) {
      const has = e.actions.size > 0 || e.note.trim().length > 0;
      if (has) pages++;
      actions += e.actions.size + (e.note.trim().length > 0 ? 1 : 0);
    }
    const el = document.getElementById('selCount');
    const fb = generalFeedback.trim().length > 0 ? ' · <strong>+ general feedback</strong>' : '';
    el.innerHTML = '<strong>' + pages + '</strong> page' + (pages === 1 ? '' : 's') + ' · <strong>' + actions + '</strong> action' + (actions === 1 ? '' : 's') + ' selected' + fb;
  }

  const fbEl = document.getElementById('generalFeedback');
  fbEl.addEventListener('input', () => {
    generalFeedback = fbEl.value;
    fbEl.classList.toggle('has-text', generalFeedback.trim().length > 0);
    updateCount();
  });

  /* ---------- Template-level CTAs ---------- */
  function syncTemplateChips(layoutId) {
    // For each chip in every panel's template CTA matching this layout,
    // reflect on/off/partial based on the union of samples' state.
    const cards = Array.from(document.querySelectorAll('#panel-' + getActiveViewport() + ' [data-layout-id="' + CSS.escape(layoutId) + '"] .sample-card'));
    const total = cards.length;
    document.querySelectorAll('.tpl-cta[data-layout-id="' + CSS.escape(layoutId) + '"]').forEach(cta => {
      let anySelected = false;
      cta.querySelectorAll('.tpl-chip').forEach(chip => {
        const action = chip.dataset.tplAction;
        let onCount = 0;
        for (const c of cards) {
          const e = state.get(c.dataset.cardId);
          if (e && e.actions.has(action)) onCount++;
        }
        chip.classList.remove('on', 'partial');
        if (total > 0 && onCount === total) chip.classList.add('on');
        else if (onCount > 0) chip.classList.add('partial');
        if (onCount > 0) anySelected = true;
      });
      cta.classList.toggle('has-selection', anySelected);
    });
  }

  function syncAllTemplateChips() {
    document.querySelectorAll('.tpl-cta').forEach(cta => syncTemplateChips(cta.dataset.layoutId));
  }

  document.addEventListener('click', (ev) => {
    // Template-level chip — toggle action across every sample in the active panel for this layout.
    const tplChip = ev.target.closest('.tpl-chip');
    if (tplChip) {
      const layoutId = tplChip.closest('.tpl-cta').dataset.layoutId;
      const action = tplChip.dataset.tplAction;
      const cards = Array.from(document.querySelectorAll('#panel-' + getActiveViewport() + ' [data-layout-id="' + CSS.escape(layoutId) + '"] .sample-card'));
      // Determine intent: if all currently have it, turn all off; otherwise turn all on.
      const allOn = cards.length > 0 && cards.every(c => {
        const e = state.get(c.dataset.cardId);
        return e && e.actions.has(action);
      });
      for (const card of cards) {
        const e = ensureEntry(card);
        if (allOn) e.actions.delete(action);
        else e.actions.add(action);
        syncCardClasses(card);
      }
      syncTemplateChips(layoutId);
      updateCount();
      return;
    }
    // Card-level chip (only present in modal now, handled in renderModalChips).
    const chip = ev.target.closest('.chip:not(.tpl-chip)');
    if (chip) {
      const card = chip.closest('.sample-card');
      if (!card) return;
      const e = ensureEntry(card);
      const action = chip.dataset.action;
      if (e.actions.has(action)) e.actions.delete(action);
      else e.actions.add(action);
      syncCardClasses(card);
      syncTemplateChips(card.dataset.layoutId);
      updateCount();
    }
  });

  document.addEventListener('input', (ev) => {
    const n = ev.target.closest('input.note');
    if (!n) return;
    const card = n.closest('.sample-card');
    if (!card) return;
    const e = ensureEntry(card);
    e.note = n.value;
    n.classList.toggle('has-text', e.note.trim().length > 0);
    // Mirror to other tabs' copies (without overwriting the focused one).
    syncCardClasses(card);
    updateCount();
  });

  /* ---------- Modal ---------- */
  const modal = document.getElementById('modal');
  const mImg = document.getElementById('mImg');
  const mFrame = document.getElementById('mFrame');
  const mNote = document.getElementById('mNote');
  const mForce = document.getElementById('mForce');
  const mChips = document.getElementById('mChips');
  const mTpl = document.getElementById('mTpl');
  const mTplId = document.getElementById('mTplId');
  const mLocale = document.getElementById('mLocale');
  const mPath = document.getElementById('mPath');
  let modalCardId = null;

  function renderModalChips(cardId) {
    const e = state.get(cardId);
    mChips.innerHTML = '';
    Object.entries(ACTION_LABELS).forEach(([id, label]) => {
      const b = document.createElement('button');
      b.type = 'button'; b.className = 'chip'; b.dataset.action = id; b.textContent = label;
      if (e && e.actions.has(id)) b.classList.add('on');
      b.addEventListener('click', () => {
        const card = document.querySelector('[data-card-id="' + CSS.escape(cardId) + '"]');
        if (!card) return;
        const en = ensureEntry(card);
        if (en.actions.has(id)) en.actions.delete(id); else en.actions.add(id);
        syncCardClasses(card);
        syncTemplateChips(card.dataset.layoutId);
        renderModalChips(cardId);
        updateCount();
      });
      mChips.appendChild(b);
    });
  }

  function openModal(card, imgSrc) {
    modalCardId = card.dataset.cardId;
    const e = ensureEntry(card);
    mTpl.textContent = card.dataset.layoutLabel;
    mTplId.textContent = card.dataset.layoutId;
    mLocale.textContent = card.dataset.locale;
    mPath.textContent = card.dataset.path;
    mImg.src = imgSrc;
    mImg.alt = card.dataset.path;
    // After load we know natural pixel dimensions; show at natural width.
    mImg.onload = () => {
      mImg.style.width = mImg.naturalWidth + 'px';
    };
    mNote.value = e.note;
    mForce.checked = e.note.trim().length > 0;
    renderModalChips(modalCardId);
    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');
    // Focus note input so dictation (Wispr Flow, OS dictation) lands there immediately.
    setTimeout(() => mNote.focus(), 50);
  }

  function closeModal() {
    modal.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
    mImg.removeAttribute('src');
    mImg.style.width = '';
    modalCardId = null;
  }

  // Intercept zoom-link clicks → modal (preserves right-click → "open in new tab" via the href).
  document.addEventListener('click', (ev) => {
    const a = ev.target.closest('a.zoom');
    if (!a) return;
    // Allow modifier-clicks to fall through to the browser (cmd-click new tab etc.)
    if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey || ev.button !== 0) return;
    ev.preventDefault();
    const card = a.closest('.sample-card');
    if (!card) return;
    openModal(card, a.getAttribute('href'));
  });

  // Click on the image / frame closes the modal.
  mFrame.addEventListener('click', closeModal);
  document.getElementById('mClose').addEventListener('click', closeModal);
  modal.addEventListener('click', (ev) => {
    // Clicking the dark overlay (not the inner) closes too.
    if (ev.target === modal) closeModal();
  });
  document.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape' && modal.classList.contains('open')) closeModal();
  });

  // Note input inside the modal mirrors back into card state.
  mNote.addEventListener('input', () => {
    if (!modalCardId) return;
    const card = document.querySelector('[data-card-id="' + CSS.escape(modalCardId) + '"]');
    if (!card) return;
    const e = ensureEntry(card);
    e.note = mNote.value;
    mForce.checked = e.note.trim().length > 0;
    syncCardClasses(card);
    updateCount();
  });

  // Manual toggle of the "force" radio: clearing it clears the note text too.
  mForce.addEventListener('click', () => {
    if (!modalCardId) return;
    const card = document.querySelector('[data-card-id="' + CSS.escape(modalCardId) + '"]');
    if (!card) return;
    const e = ensureEntry(card);
    if (!mForce.checked) {
      e.note = '';
      mNote.value = '';
      syncCardClasses(card);
      updateCount();
    } else {
      // checked manually with no text — just focus note so dictation starts now.
      mNote.focus();
    }
  });

  document.getElementById('clearBtn').addEventListener('click', () => {
    state.clear();
    document.querySelectorAll('.sample-card').forEach(c => c.classList.remove('has-selection'));
    document.querySelectorAll('.chip').forEach(ch => ch.classList.remove('on', 'partial'));
    document.querySelectorAll('.tpl-cta').forEach(c => c.classList.remove('has-selection'));
    generalFeedback = '';
    fbEl.value = '';
    fbEl.classList.remove('has-text');
    updateCount();
  });

  function buildPrompt() {
    const viewport = getActiveViewport();
    const lines = [];
    lines.push('# Visual QA — apply selected fixes');
    lines.push('');
    lines.push('Site: ' + SITE_TITLE);
    if (BASE_URL) lines.push('Base URL: ' + BASE_URL + ' (env: ' + ENV + ')');
    lines.push('Viewing tab: ' + viewport);
    lines.push('');

    if (generalFeedback.trim().length > 0) {
      lines.push('## General feedback (applies site-wide)');
      lines.push('');
      lines.push(generalFeedback.trim());
      lines.push('');
    }

    lines.push('Selected pages:');
    lines.push('');

    // Group entries by layout for clarity.
    const byLayout = new Map();
    for (const [id, e] of state.entries()) {
      if (e.actions.size === 0 && e.note.trim().length === 0) continue;
      if (!byLayout.has(e.layoutId)) byLayout.set(e.layoutId, { label: e.layoutLabel, entries: [] });
      byLayout.get(e.layoutId).entries.push(e);
    }

    if (byLayout.size === 0 && generalFeedback.trim().length === 0) return null;

    for (const [layoutId, group] of byLayout.entries()) {
      lines.push('## ' + group.label + ' [' + layoutId + ']');
      for (const e of group.entries) {
        lines.push('');
        lines.push('- **' + e.path + '** (' + e.locale + ')');
        if (e.actions.size > 0) {
          const labels = Array.from(e.actions).map(a => ACTION_LABELS[a] || a);
          lines.push('  - Actions: ' + labels.join(', '));
        }
        if (e.note.trim().length > 0) {
          lines.push('  - Note: ' + e.note.trim());
        }
      }
      lines.push('');
    }

    lines.push('---');
    lines.push('');
    lines.push('## Before you start');
    lines.push('Ask clarifying questions for anything ambiguous before making changes.');
    lines.push('Current-state screenshots live in \`.visual-qa/out/<layout>/<locale>/<slug>/<viewport>.png\`.');
    lines.push('');
    lines.push('## After you finish — MANDATORY validation');
    lines.push('1. Re-run the visual-qa capture against \`' + BASE_URL + '\` (env: ' + ENV + ') so fresh PNGs replace the ones above.');
    lines.push('   \`\`\`');
    lines.push('   node ' + SKILL_DIR + '/capture.mjs \\\\');
    lines.push('     --config .visual-qa/urls.json --out .visual-qa/out --env ' + ENV + ' --force');
    lines.push('   \`\`\`');
    lines.push('2. For every affected page, look at the new PNGs at **all three viewports** (desktop, tablet, mobile). Use the \`Read\` tool on each PNG — actually inspect the pixels, do not trust that the code change worked.');
    lines.push('3. If anything looks wrong (regression, overflow, broken layout, contrast still poor, padding still off) — fix it and re-validate. Iterate until every affected viewport looks correct.');
    lines.push('4. Only report back "done" once **all three viewports for every affected page** look good. State explicitly: which pages you re-captured, which viewports you reviewed, and what you confirmed visually.');
    return lines.join('\\n');
  }

  document.getElementById('copyBtn').addEventListener('click', async () => {
    const text = buildPrompt();
    if (!text) {
      const t = document.getElementById('toast');
      t.textContent = 'Nothing selected';
      t.style.color = '#d97a5a';
      t.classList.add('show');
      setTimeout(() => { t.classList.remove('show'); t.style.color = ''; t.textContent = 'Copied ✓'; }, 1600);
      return;
    }
    try {
      await navigator.clipboard.writeText(text);
      const t = document.getElementById('toast');
      t.classList.add('show');
      setTimeout(() => t.classList.remove('show'), 1600);
    } catch (err) {
      // Fallback: open a window with the text for manual copy.
      const w = window.open('', '_blank');
      w.document.body.style.background = '#0b0b0d';
      w.document.body.style.color = '#e6e6ea';
      w.document.body.innerHTML = '<pre style="white-space:pre-wrap;padding:20px;font-family:ui-monospace,Menlo,monospace">' +
        text.replace(/&/g, '&amp;').replace(/</g, '&lt;') + '</pre>';
    }
  });

  document.querySelectorAll('input[name="tab"]').forEach(r => r.addEventListener('change', syncAllTemplateChips));

  updateCount();
  syncAllTemplateChips();
})();
</script>
</body>
</html>`;
}

function main() {
  const args = parseArgs(process.argv);
  const config = JSON.parse(fs.readFileSync(path.resolve(args.config), 'utf8'));
  const outDir = path.resolve(args.out);

  let envLine = '', baseUrl = '', env = '';
  try {
    const m = JSON.parse(fs.readFileSync(path.join(outDir, '_meta.json'), 'utf8'));
    env = m.env; baseUrl = m.baseUrl;
    envLine = `env: ${m.env} (${m.baseUrl})`;
  } catch {}

  let totalSamples = 0;
  for (const layout of config.layouts) totalSamples += expandLayout(layout, config).length;
  const meta = {
    title: config.title || 'Gallery',
    subtitle: `${config.layouts.length} templates · ${(config.locales || ['en']).length} locales · ${totalSamples} sample URLs · 3 viewports`,
    envLine, baseUrl, env
  };
  const html = renderHTML(config, outDir, meta);
  const outFile = path.join(outDir, 'gallery.html');
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(outFile, html);
  console.log(`Wrote: ${outFile}`);
}

main();
