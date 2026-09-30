#!/usr/bin/env python3
"""Tier B of the /visual-qa rubric — geometry, measured in a real browser.

Tier A reads served HTML. Whitespace, alignment, sparse layouts, and spacing
that drifts off the scale do not exist in HTML. They are emergent at layout
time, in a browser, at a viewport, with real content. This is the tier that
can see them.

The rule that makes these checks able to FAIL: measure the layout tree, never
judge the picture. Every check resolves to a number and a threshold, and every
failure carries the measured value, the expected value, and a selector.

Piggybacks on the same .visual-qa/urls.json the capture pass already uses.
"""
import argparse, json, os, statistics, sys
from collections import defaultdict

from playwright.sync_api import sync_playwright

# --------------------------------------------------------------- measure ----
MEASURE_JS = r"""() => {
  const vis = (el) => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  const sig = (el) => el.tagName + '.' + Array.from(el.classList).sort().join('.');
  const out = { rows: [], repeats: {}, spacing: [], clipped: [], overlaps: 0,
                container: null, nav: null, footer: null, docW: 0, innerW: 0,
                tapSmall: [], imgs: 0 };

  out.docW = document.documentElement.scrollWidth;
  out.innerW = window.innerWidth;

  // --- sibling rows: >=3 same-signature children sharing a row -------------
  document.querySelectorAll('body *').forEach(parent => {
    const kids = Array.from(parent.children).filter(vis);
    if (kids.length < 3) return;
    const bySig = {};
    kids.forEach(k => { (bySig[sig(k)] = bySig[sig(k)] || []).push(k); });
    Object.entries(bySig).forEach(([s, els]) => {
      if (els.length < 3) return;
      const boxes = els.map(e => e.getBoundingClientRect());
      const top = boxes[0].top;
      if (!boxes.every(b => Math.abs(b.top - top) < 4)) return;   // one visual row only
      out.rows.push({ sig: s, n: els.length,
        lefts: boxes.map(b => +b.left.toFixed(2)),
        tops: boxes.map(b => +b.top.toFixed(2)),
        heights: boxes.map(b => +b.height.toFixed(2)) });
    });
  });

  // --- repeated components: identical computed padding ---------------------
  const groups = {};
  document.querySelectorAll('body *').forEach(el => {
    if (!el.classList.length || !vis(el)) return;
    (groups[sig(el)] = groups[sig(el)] || []).push(el);
  });
  Object.entries(groups).forEach(([s, els]) => {
    if (els.length < 3) return;
    const pads = els.map(e => {
      const c = getComputedStyle(e);
      return [c.paddingTop, c.paddingRight, c.paddingBottom, c.paddingLeft].join(' ');
    });
    const uniq = Array.from(new Set(pads));
    if (uniq.length > 1) out.repeats[s] = { n: els.length, variants: uniq.slice(0, 4) };
  });

  // --- every non-zero spacing value actually computed ----------------------
  const seen = {};
  document.querySelectorAll('body *').forEach(el => {
    if (!vis(el)) return;
    const c = getComputedStyle(el);
    ['marginTop','marginBottom','marginLeft','marginRight',
     'paddingTop','paddingBottom','paddingLeft','paddingRight','gap',
     'rowGap','columnGap'].forEach(p => {
      const v = c[p];
      if (!v || !v.endsWith('px')) return;
      const n = Math.abs(parseFloat(v));
      if (!n) return;
      seen[n] = (seen[n] || 0) + 1;
    });
  });
  out.spacing = Object.entries(seen).map(([v, n]) => [+v, n]);

  // --- text clipped by its own box ----------------------------------------
  const HIDDEN = /sr-only|visually-hidden|screen-?reader|a11y-hidden/i;
  document.querySelectorAll('h1,h2,h3,h4,p,li,a,span,button,td,th,figcaption,label')
    .forEach(el => {
      if (!vis(el) || !el.textContent.trim()) return;
      if (el.children.length) return;
      const c = getComputedStyle(el);
      // Deliberate overflow, in every form it ships in.
      if (['auto','scroll','hidden'].includes(c.overflowX) && c.textOverflow === 'ellipsis') return;
      if (c.overflow === 'auto' || c.overflow === 'scroll') return;
      if (c.overflowX === 'auto' || c.overflowY === 'auto') return;
      if (c.textOverflow === 'ellipsis') return;
      // Visually-hidden helpers are SUPPOSED to be clipped: they are how the
      // accessible name gets to a screen reader. Flagging them is noise.
      if (HIDDEN.test(el.className || '')) return;
      if (c.clipPath && c.clipPath !== 'none') return;
      if (c.position === 'absolute' && (el.clientWidth <= 1 || el.clientHeight <= 1)) return;
      // Inline boxes report scrollHeight against the line box, so a descender
      // or a line-height rounding shows as 1-3px of phantom overflow.
      if (c.display === 'inline') return;
      const overW = el.scrollWidth - el.clientWidth;
      const overH = el.scrollHeight - el.clientHeight;
      if (overW > 4 || overH > 4) {
        out.clipped.push({ sel: sig(el), overW, overH,
                           text: el.textContent.trim().slice(0, 44) });
      }
    });

  // --- container width + chrome fingerprints ------------------------------
  const main = document.querySelector('main') || document.body;
  const kids = Array.from(main.children).filter(vis);
  if (kids.length) {
    const widths = kids.map(k => {
      const inner = Array.from(k.querySelectorAll(':scope > *')).filter(vis);
      const t = inner.length ? inner[0] : k;
      return Math.round(t.getBoundingClientRect().width);
    });
    out.container = widths.sort((a, b) =>
      widths.filter(v => v === b).length - widths.filter(v => v === a).length)[0];
  }
  // Structural fingerprint: tag skeleton only, no text and no active-state
  // classes. Comparing innerHTML across locales just detects translation, and
  // every multilingual site fails for the wrong reason.
  const strip = (el) => {
    if (!el) return null;
    const parts = [];
    const walk = (n, depth) => {
      if (depth > 6) return;
      Array.from(n.children).forEach(c => {
        const cls = Array.from(c.classList)
          .filter(x => !/active|current|selected|open/i.test(x)).sort().join('.');
        parts.push(depth + ':' + c.tagName + (cls ? '.' + cls : ''));
        walk(c, depth + 1);
      });
    };
    walk(el, 0);
    return parts.join('|');
  };
  out.nav = strip(document.querySelector('header nav, nav'));
  out.footer = strip(document.querySelector('footer'));

  // --- tap targets --------------------------------------------------------
  document.querySelectorAll('a,button,[role="button"],input,select').forEach(el => {
    if (!vis(el)) return;
    const r = el.getBoundingClientRect();
    if (r.width < 44 || r.height < 44)
      out.tapSmall.push({ sel: sig(el), w: Math.round(r.width), h: Math.round(r.height) });
  });
  out.imgs = document.images.length;
  return out;
}"""


class Findings:
    def __init__(self): self.rows = []
    def fail(self, route, vp, check, measured, expected, sev="P2", sel=""):
        self.rows.append(dict(route=route, viewport=vp, check=check, selector=sel,
                              measured=measured, expected=expected, severity=sev))


def token_scale(project):
    """Read the project's own spacing scale so this needs no configuration."""
    for p in ("design/tokens.json", "tokens.json"):
        fp = os.path.join(project, p)
        if not os.path.exists(fp): continue
        try: data = json.load(open(fp))
        except Exception: continue
        vals = set()
        def walk(n):
            if isinstance(n, dict):
                v = n.get("$value")
                if isinstance(v, str) and v.endswith(("px", "rem")):
                    try:
                        num = float(v[:-3] if v.endswith("rem") else v[:-2])
                        vals.add(round(num * 16, 2) if v.endswith("rem") else round(num, 2))
                    except ValueError: pass
                for x in n.values(): walk(x)
            elif isinstance(n, list):
                for x in n: walk(x)
        walk(data)
        if vals: return sorted(vals), p
    return None, None


def check_page(route, vp, d, f, scale):
    # 1 row alignment. Items sitting side by side in a row are SUPPOSED to have
    #   different left and right edges — that is what a row is. What must line up
    #   is their top edge and, for anything card-shaped, their height. An item
    #   3px taller than its neighbours is the misalignment a human notices.
    for row in d["rows"]:
        tops = row["tops"]
        spread = max(tops) - min(tops)
        if spread > 1.0:
            f.fail(route, vp, "row-top-alignment",
                   f"{row['n']} siblings in one row, top edges span {spread:.2f}px",
                   "within 1px", "P2", row["sig"])
        hs = row["heights"]
        hspread = max(hs) - min(hs)
        if hspread > 1.0 and min(hs) > 24:
            f.fail(route, vp, "row-height-consistency",
                   f"{row['n']} siblings in one row, heights span {hspread:.2f}px "
                   f"({min(hs):.0f}..{max(hs):.0f})",
                   "equal height across the row", "P2", row["sig"])
    # 2 repeated component padding
    for sig, info in list(d["repeats"].items())[:6]:
        f.fail(route, vp, "repeated-component-padding",
               f"{info['n']} instances with {len(info['variants'])} different paddings: "
               + " | ".join(info["variants"][:2]),
               "identical padding on every instance", "P2", sig)
    # 3 spacing scale conformance
    if scale:
        off = [(v, n) for v, n in d["spacing"]
               if not any(abs(v - s) <= 0.5 for s in scale)]
        off.sort(key=lambda t: -t[1])
        if off:
            total = sum(n for _, n in d["spacing"]) or 1
            bad = sum(n for _, n in off)
            f.fail(route, vp, "spacing-scale-conformance",
                   f"{bad}/{total} spacing values off-scale ({100*bad/total:.0f}%); "
                   f"worst: {', '.join(f'{v}px x{n}' for v, n in off[:4])}",
                   "every value in the project spacing scale", "P2")
    # 4 text clipping
    for c in d["clipped"][:5]:
        f.fail(route, vp, "no-text-clipping",
               f"overflow {c['overW']}x{c['overH']}px: {c['text']!r}",
               "text fits its box, or has an ellipsis affordance", "P1", c["sel"])
    # 5 horizontal scroll
    if d["docW"] > d["innerW"] + 1:
        f.fail(route, vp, "no-horizontal-scroll",
               f"document {d['docW']}px wide in a {d['innerW']}px viewport",
               "no overflow", "P1")
    # 6 tap targets (mobile only)
    if vp == "mobile" and d["tapSmall"]:
        worst = sorted(d["tapSmall"], key=lambda t: t["w"] * t["h"])[:3]
        f.fail(route, vp, "tap-target-size",
               f"{len(d['tapSmall'])} target(s) under 44x44; smallest "
               + ", ".join(f"{t['w']}x{t['h']}" for t in worst),
               "44x44 minimum", "P2", worst[0]["sel"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--env", default="production")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--viewports", default="desktop,mobile")
    ap.add_argument("--json", dest="json_out")
    a = ap.parse_args()

    cfg = json.load(open(os.path.join(a.project, ".visual-qa", "urls.json")))
    base = cfg["baseUrls"][a.env].rstrip("/")
    urls = []
    for layout in cfg.get("layouts", []):
        for s in layout.get("samples", []):
            urls.append(base + (s["path"] if isinstance(s, dict) else s))
    urls = list(dict.fromkeys(urls))
    if a.limit: urls = urls[:a.limit]

    scale, scale_src = token_scale(a.project)
    print(f"scanning {len(urls)} route(s) at {base}")
    print(f"spacing scale: {'%d values from %s' % (len(scale), scale_src) if scale else 'NOT FOUND — spacing-scale-conformance skipped'}\n")

    VPS = {"desktop": {"width": 1440, "height": 900},
           "mobile":  {"width": 390, "height": 844}}
    want = [v.strip() for v in a.viewports.split(",")]
    f = Findings()
    chrome = defaultdict(dict)

    with sync_playwright() as p:
        b = p.chromium.launch()
        for vp in want:
            page = b.new_page(viewport=VPS[vp])
            for u in urls:
                route = u.replace(base, "") or "/"
                try:
                    page.goto(u, wait_until="networkidle", timeout=45000)
                    page.wait_for_timeout(1200)
                    d = page.evaluate(MEASURE_JS)
                except Exception as e:
                    f.fail(route, vp, "load", str(e)[:90], "page loads", "P0"); continue
                check_page(route, vp, d, f, scale)
                chrome[vp][route] = (d["nav"], d["footer"], d["container"])
            page.close()
        b.close()

    # cross-route parity, desktop only
    for vp, routes in chrome.items():
        if vp != "desktop": continue
        for idx, label in ((0, "nav"), (1, "footer")):
            seen = defaultdict(list)
            for route, tup in routes.items():
                if tup[idx]: seen[tup[idx]].append(route)
            if len(seen) > 1:
                groups = sorted(seen.values(), key=len, reverse=True)
                f.fail(", ".join(groups[1][:3]), vp, "nav-footer-parity",
                       f"{len(seen)} different {label} markups across {len(routes)} routes",
                       f"identical {label} on every route", "P2")
        widths = defaultdict(list)
        for route, tup in routes.items():
            if tup[2]: widths[tup[2]].append(route)
        if len(widths) > 3:
            f.fail(", ".join(sorted(widths, key=lambda w: -len(widths[w]))[3:][:3] and
                             [r for w in sorted(widths, key=lambda w: -len(widths[w]))[3:]
                              for r in widths[w]][:3]),
                   vp, "container-width-parity",
                   f"{len(widths)} distinct content widths: {sorted(widths)}",
                   "3 or fewer sitewide", "P2")

    order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    f.rows.sort(key=lambda r: (order.get(r["severity"], 9), r["check"]))
    if not f.rows:
        print("PASS — Tier B clean."); return 0
    counts = defaultdict(int)
    for r in f.rows: counts[r["severity"]] += 1
    print("FAIL — " + ", ".join(f"{counts[s]} {s}" for s in ("P0","P1","P2","P3") if counts[s]) + "\n")
    for r in f.rows[:40]:
        print(f"[{r['severity']}] {r['check']}  ({r['viewport']})")
        print(f"      route:    {r['route']}")
        if r["selector"]: print(f"      selector: {r['selector'][:100]}")
        print(f"      measured: {r['measured']}")
        print(f"      expected: {r['expected']}\n")
    if len(f.rows) > 40: print(f"... and {len(f.rows)-40} more")
    if a.json_out: json.dump(f.rows, open(a.json_out, "w"), indent=1)
    return 1


if __name__ == "__main__":
    sys.exit(main())
