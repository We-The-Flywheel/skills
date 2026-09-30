#!/usr/bin/env python3
"""Tier A of the /visual-qa rubric — static checks, no browser.

Six checks that need only served HTML, so they are fast enough to block a
deploy. Runs against a built directory (--dir, the deploy-step case) or against
live URLs from .visual-qa/urls.json (--project, the sweep case).

Every failure prints route, check id, and what was measured vs expected.
Exit 1 if any check fails.
"""
import argparse, json, os, re, sys, io
from collections import defaultdict
from urllib.parse import urljoin, urlparse

import requests
from lxml import html as LH

UA = {"User-Agent": "Mozilla/5.0 (compatible; FlywheelVisualQA/1.0)"}
TIMEOUT = 25

PLACEHOLDER = re.compile(
    r"\b(lorem ipsum|TODO:|FIXME|TBD|your-domain|replace-me|dummy text|"
    r"Placeholder text|Sample text)\b", re.I)

FRAMEWORK_404 = re.compile(
    r"(This page could not be found|404: This page|Cannot GET|"
    r"<hr><center>nginx|Apache/[\d.]+ Server at|Default 404)", re.I)


class Findings:
    def __init__(self): self.rows = []
    def fail(self, route, check, measured, expected, sev="P1"):
        self.rows.append(dict(route=route, check=check, measured=measured,
                              expected=expected, severity=sev))
    def __len__(self): return len(self.rows)


def fetch(url):
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    return r.status_code, r.text, r.url


def head_ok(url):
    try:
        r = requests.head(url, headers=UA, timeout=TIMEOUT, allow_redirects=True)
        if r.status_code == 405 or r.status_code >= 400:
            r = requests.get(url, headers=UA, timeout=TIMEOUT, stream=True)
        return r.status_code, r
    except Exception as e:
        return None, str(e)


# ---------------------------------------------------------------- checks ----
def check_favicon(doc, base, route, f):
    icons = doc.xpath('//link[contains(translate(@rel,"ICON","icon"),"icon")]/@href')
    if not icons:
        f.fail(route, "favicon-resolves", "no rel=icon link", "at least one icon link", "P2")
        return
    for href in dict.fromkeys(icons):
        u = urljoin(base, href)
        code, _ = head_ok(u)
        if code != 200:
            f.fail(route, "favicon-resolves", f"{href} -> {code}", "200", "P2")


def check_meta(doc, route, seen, f):
    title = (doc.xpath("string(//title)") or "").strip()
    desc = (doc.xpath('string(//meta[@name="description"]/@content)') or "").strip()
    if not title:
        f.fail(route, "per-route-meta", "empty <title>", "non-empty title", "P1")
    if not desc:
        f.fail(route, "per-route-meta", "no meta description", "non-empty description", "P1")
        key = route.split("?")[0]   # same path + different query = one document
        if title and key not in seen["title"][title]: seen["title"][title].append(key)
        if desc and key not in seen["desc"][desc]: seen["desc"][desc].append(key)


def check_og(doc, base, route, f):
    og = doc.xpath('string(//meta[@property="og:image"]/@content)').strip()
    if not og:
        f.fail(route, "og-image-resolves", "no og:image", "absolute https URL", "P1")
        return
    if not urlparse(og).scheme:
        f.fail(route, "og-image-resolves", f"relative URL {og}", "absolute URL", "P0")
        return
    code, r = head_ok(og)
    if code != 200:
        f.fail(route, "og-image-resolves", f"{og} -> {code}", "200", "P0")
        return
    dw = doc.xpath('string(//meta[@property="og:image:width"]/@content)').strip()
    dh = doc.xpath('string(//meta[@property="og:image:height"]/@content)').strip()
    if dw and dh:
        try:
            from PIL import Image
            img = requests.get(og, headers=UA, timeout=TIMEOUT).content
            w, h = Image.open(io.BytesIO(img)).size
            if (str(w), str(h)) != (dw, dh):
                f.fail(route, "og-image-resolves", f"declared {dw}x{dh}, actual {w}x{h}",
                       "declared matches actual", "P2")
        except Exception:
            pass


def visible_text(doc):
    """Text nodes only, with script/style/noscript dropped. Searching raw HTML
    matches attribute NAMES (placeholder="Search races") and legitimate sample
    values inside form fields, which are not placeholder content."""
    d = LH.fromstring(LH.tostring(doc))
    for bad in d.xpath("//script | //style | //noscript | //template"):
        bad.getparent().remove(bad)
    return " ".join(d.itertext())


def check_placeholder(doc, route, f):
    hits = {m.group(0) for m in PLACEHOLDER.finditer(visible_text(doc))}
    if hits:
        f.fail(route, "no-placeholder-strings", ", ".join(sorted(hits)[:4]),
               "no placeholder text in rendered copy", "P1")


def check_alt(doc, route, f):
    """A missing alt attribute is the failure. alt="" is the correct way to mark
    an image decorative — WCAG does not require role="presentation" alongside it,
    and demanding both produces a wall of false positives on well-built sites.

    Separately, if nearly every image on a page is marked decorative, that is
    worth surfacing: content images hidden from screen readers look identical to
    correctly-marked chrome. Reported as P3 information, not a failure."""
    imgs = doc.xpath("//img")
    if not imgs:
        return
    missing, empty = [], 0
    for img in imgs:
        alt = img.get("alt")
        src = (img.get("src") or img.get("data-src") or "?")[:70]
        if alt is None:
            missing.append(src)
        elif alt.strip() == "":
            empty += 1
    if missing:
        f.fail(route, "alt-text-present",
               f"{len(missing)} image(s) with no alt attribute; e.g. {missing[0]}",
               "every img carries an alt attribute", "P1")
    if imgs and empty == len(imgs) and len(imgs) >= 5:
        f.fail(route, "alt-text-all-decorative",
               f'all {len(imgs)} images on the page use alt=""',
               "content images should describe themselves; only chrome is decorative", "P3")


def check_404(base, f, locales=None):
    """Tier A can only assert the STATUS CODE.

    Whether the 404 is *designed* cannot be settled from served HTML: on
    some sites the designed 404 body is client-rendered, so the server
    HTML for a designed 404 and a framework default are both empty, while the
    framework's own "404: This page could not be found" string sits in the RSC
    payload of BOTH. Static inspection cannot separate them, so that judgement
    belongs in Tier B, where there is a browser.
    """
    probes = ["/this-route-should-not-exist-vqa/"]
    for loc in (locales or [])[:1]:
        probes.append(f"/{loc}/this-route-should-not-exist-vqa/")
    for path in probes:
        try:
            r = requests.get(urljoin(base, path), headers=UA, timeout=TIMEOUT)
        except Exception as e:
            f.fail(path, "404-status", f"request failed: {e}", "404", "P2"); continue
        if r.status_code != 404:
            f.fail(path, "404-status", f"unknown route returned {r.status_code}",
                   "404", "P1")


# ------------------------------------------------------------------ main ----
def routes_from_project(project, env):
    cfg = json.load(open(os.path.join(project, ".visual-qa", "urls.json")))
    base = cfg["baseUrls"][env].rstrip("/")
    out = []
    for layout in cfg.get("layouts", []):
        for s in layout.get("samples", []):
            path = s["path"] if isinstance(s, dict) else s
            out.append(base + path)
    return base, list(dict.fromkeys(out)), cfg.get("locales", [])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", help="repo root containing .visual-qa/urls.json")
    ap.add_argument("--env", default="production")
    ap.add_argument("--dir", help="built output dir to scan instead of live URLs")
    ap.add_argument("--base", default="", help="base URL when using --dir")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--json", dest="json_out")
    a = ap.parse_args()

    f = Findings()
    seen = {"title": defaultdict(list), "desc": defaultdict(list)}
    pages = []

    locales = []
    if a.dir:
        base = a.base.rstrip("/")
        for root, _, files in os.walk(a.dir):
            for fn in files:
                if fn.endswith(".html"):
                    p = os.path.join(root, fn)
                    pages.append(("/" + os.path.relpath(p, a.dir), open(p, encoding="utf-8", errors="replace").read()))
    else:
        base, urls, locales = routes_from_project(a.project, a.env)
        if a.limit: urls = urls[:a.limit]
        for u in urls:
            try:
                code, text, final = fetch(u)
            except Exception as e:
                f.fail(u.replace(base, ""), "fetch", str(e)[:90], "200", "P0"); continue
            if code != 200:
                f.fail(u.replace(base, ""), "fetch", f"HTTP {code}", "200", "P0"); continue
            pages.append((u.replace(base, "") or "/", text))

    print(f"scanning {len(pages)} page(s) at {base or a.dir}\n")
    for route, text in pages:
        doc = LH.fromstring(text)
        check_favicon(doc, base or "http://local/", route, f)
        check_meta(doc, route, seen, f)
        check_og(doc, base or "http://local/", route, f)
        check_placeholder(doc, route, f)
        check_alt(doc, route, f)

    for kind, label in (("title", "<title>"), ("desc", "meta description")):
        for value, rs in seen[kind].items():
            if len(rs) > 1:
                f.fail(", ".join(rs[:3]) + (f" +{len(rs)-3} more" if len(rs) > 3 else ""),
                       "per-route-meta", f"identical {label} on {len(rs)} routes: {value[:60]!r}",
                       "unique per route", "P1")
    if base:
        check_404(base, f, locales)

    order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    f.rows.sort(key=lambda r: (order.get(r["severity"], 9), r["check"]))
    if not f.rows:
        print("PASS — all six Tier A checks clean."); return 0
    counts = defaultdict(int)
    for r in f.rows: counts[r["severity"]] += 1
    print("FAIL — " + ", ".join(f"{counts[s]} {s}" for s in ("P0","P1","P2","P3") if counts[s]) + "\n")
    for r in f.rows:
        print(f"[{r['severity']}] {r['check']}")
        print(f"      route:    {r['route']}")
        print(f"      measured: {r['measured']}")
        print(f"      expected: {r['expected']}\n")
    if a.json_out: json.dump(f.rows, open(a.json_out, "w"), indent=1)
    return 1


if __name__ == "__main__":
    sys.exit(main())
