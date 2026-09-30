import json, math, sys
from playwright.sync_api import sync_playwright

FOLD_W, FOLD_H, CELL = 1440, 900, 6

JS = """() => {
  const isContent = (el) => {
    if (el.children.length === 0) {
      const t = (el.textContent || '').trim();
      if (t.length > 0) return true;
    }
    const tag = el.tagName.toLowerCase();
    if (['img','svg','video','canvas','picture','iframe','input','button','textarea','select'].includes(tag)) return true;
    const cs = getComputedStyle(el);
    if (cs.backgroundImage && cs.backgroundImage !== 'none') return true;
    return false;
  };
  const boxes = [];
  document.querySelectorAll('body *').forEach(el => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) return;
    if (cs.position === 'fixed') return;
    if (!isContent(el)) return;
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) return;
    boxes.push([r.left + scrollX, r.top + scrollY, r.width, r.height]);
  });
  // top-level sections: direct children of main/body that are block-level and tall enough
  const host = document.querySelector('main') || document.body;
  const sections = [];
  Array.from(host.children).forEach(el => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none') return;
    const r = el.getBoundingClientRect();
    if (r.height < 80) return;
    sections.push([r.left + scrollX, r.top + scrollY, r.width, r.height]);
  });
  return {boxes, sections, docH: document.documentElement.scrollHeight};
}"""

def grid_cover(boxes, ox, oy, w, h, cell=CELL):
    cols = max(1, int(w // cell)); rows = max(1, int(h // cell))
    g = [bytearray(cols) for _ in range(rows)]
    for (bx, by, bw, bh) in boxes:
        x0 = max(0, int((bx - ox) // cell)); x1 = min(cols, int(math.ceil((bx - ox + bw) / cell)))
        y0 = max(0, int((by - oy) // cell)); y1 = min(rows, int(math.ceil((by - oy + bh) / cell)))
        if x1 <= 0 or y1 <= 0 or x0 >= cols or y0 >= rows: continue
        for y in range(max(0, y0), y1):
            row = g[y]
            for x in range(max(0, x0), x1): row[x] = 1
    return g, cols, rows

def fill_fraction(g, cols, rows):
    filled = sum(sum(r) for r in g)
    return filled / float(cols * rows)

def largest_empty_rect(g, cols, rows):
    """Largest all-zero axis-aligned rectangle, as a fraction of the grid."""
    best = 0; heights = [0]*cols
    for y in range(rows):
        row = g[y]
        for x in range(cols):
            heights[x] = 0 if row[x] else heights[x] + 1
        stack = []
        for x in range(cols + 1):
            hh = heights[x] if x < cols else 0
            start = x
            while stack and stack[-1][1] > hh:
                sx, sh = stack.pop()
                best = max(best, sh * (x - sx)); start = sx
            stack.append((start, hh))
    return best / float(cols * rows)

def measure(pw, url):
    b = pw.chromium.launch()
    try:
        pg = b.new_page(viewport={"width": FOLD_W, "height": FOLD_H})
        pg.goto(url, wait_until="networkidle", timeout=45000)
        pg.wait_for_timeout(1800)
        d = pg.evaluate(JS)
        boxes, sections = d["boxes"], d["sections"]
        # 1. above-fold fill
        fold_boxes = [bx for bx in boxes if bx[1] < FOLD_H]
        g, c, r = grid_cover(fold_boxes, 0, 0, FOLD_W, FOLD_H)
        fold_fill = fill_fraction(g, c, r)
        fold_dead = largest_empty_rect(g, c, r)
        # 2. worst dead region across sections
        worst = 0.0; worst_i = -1
        for i, (sx, sy, sw, sh) in enumerate(sections):
            if sh < 120 or sw < 200: continue
            sb = [bb for bb in boxes if bb[1] + bb[3] > sy and bb[1] < sy + sh]
            sg, sc, sr = grid_cover(sb, sx, sy, sw, min(sh, 4000), cell=8)
            v = largest_empty_rect(sg, sc, sr)
            if v > worst: worst, worst_i = v, i
        # 3. section height variance
        hs = [s[3] for s in sections if s[3] >= 120]
        cv = (statistics_stdev(hs) / (sum(hs)/len(hs))) if len(hs) > 1 else 0.0
        return dict(url=url, fold_fill=round(fold_fill,3), fold_dead=round(fold_dead,3),
                    worst_section_dead=round(worst,3), worst_section_index=worst_i,
                    sections=len(hs), section_cv=round(cv,3), doc_h=d["docH"])
    finally:
        b.close()

def statistics_stdev(xs):
    m = sum(xs)/len(xs)
    return math.sqrt(sum((x-m)**2 for x in xs)/(len(xs)-1))

URLS = json.load(open(sys.argv[1]))
out = []
with sync_playwright() as pw:
    for u in URLS:
        try:
            res = measure(pw, u); out.append(res)
            print(f"OK   {u}  fill={res['fold_fill']} folddead={res['fold_dead']} secdead={res['worst_section_dead']} cv={res['section_cv']} n={res['sections']}", flush=True)
        except Exception as e:
            out.append(dict(url=u, error=str(e)[:120]))
            print(f"FAIL {u}  {str(e)[:100]}", flush=True)
json.dump(out, open('/tmp/calib-results.json','w'), indent=1)
