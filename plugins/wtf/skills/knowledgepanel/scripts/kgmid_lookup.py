#!/usr/bin/env python3
"""Look up an entity's KGMID, confidence and associated URL.

Two independent sources, because they answer different questions:

  kg    Google Knowledge Graph Search API. What Google's *graph* holds.
        Free, ~100k calls/day. Needs GOOGLE_API_KEY.
  serp  DataForSEO SERP `knowledge_graph` item. What Google actually
        *renders* in the panel. Paid per call, so opt-in only.

Disagreement between the two is itself a finding: the graph can hold an
entity Google declines to render a panel for, and a rendered panel can
show facts sourced from outside the graph.

Usage:
  kgmid_lookup.py "Jason Barnard"
  kgmid_lookup.py "Jason Barnard" --url https://kalicube.com/about/
  kgmid_lookup.py "Acme Corp" --source both --yes
  kgmid_lookup.py "Acme Corp" --json
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

KG_ENDPOINT = "https://kgsearch.googleapis.com/v1/entities:search"
DFS_ENDPOINT = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"
DFS_ACCOUNT = "https://api.dataforseo.com/v3/appendix/user_data"

# The GCP project that owns GOOGLE_API_KEY. Used to print an actionable
# remediation instead of a bare 403.
KG_PROJECT = os.environ.get("GCP_PROJECT", "<your-gcp-project>")

# DataForSEO live/advanced list price. Printed as an estimate before spending.
DFS_EST_COST = 0.002

ENV_FILE = os.path.expanduser("~/.env.shared")


def load_env():
    """Merge ~/.env.shared into os.environ without clobbering what's set.

    Existing process env wins, matching load_dotenv() default semantics.
    """
    if not os.path.exists(ENV_FILE):
        return
    with open(ENV_FILE, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.replace("export ", "").strip()
            val = val.strip().strip('"').strip("'")
            os.environ.setdefault(key, val)


def http_json(url, data=None, headers=None, timeout=30):
    """Return (status, parsed_body_or_raw_text). Never raises on HTTP error."""
    req = urllib.request.Request(url, data=data, headers=headers or {})
    if data is not None:
        req.get_method = lambda: "POST"
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
            status = resp.status
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        status = exc.code
    except (urllib.error.URLError, OSError) as exc:
        return 0, {"_transport_error": str(exc)}
    try:
        return status, json.loads(raw)
    except json.JSONDecodeError:
        return status, {"_raw": raw[:2000]}


# ---------------------------------------------------------------- kg source

def lookup_kg(query, limit=5):
    """Google Knowledge Graph Search API. Returns a result dict."""
    # GOOGLE_KG_API_KEY first: on this fleet GOOGLE_API_KEY and GEMINI_API_KEY
    # are the SAME key, restricted to generativelanguage.googleapis.com, so
    # they return API_KEY_SERVICE_BLOCKED here no matter how many times the
    # service is enabled. A dedicated kgsearch-scoped key is the fix.
    key = (os.environ.get("GOOGLE_KG_API_KEY")
           or os.environ.get("GOOGLE_API_KEY")
           or os.environ.get("GEMINI_API_KEY"))
    if not key:
        return {
            "source": "kg",
            "ok": False,
            "blocker": "GOOGLE_API_KEY not set. Export it, or add it to "
                       "~/.env.shared / your secret store.",
            "entities": [],
        }

    qs = urllib.parse.urlencode(
        {"query": query, "limit": limit, "indent": "true", "key": key}
    )
    status, body = http_json(f"{KG_ENDPOINT}?{qs}")

    if status == 0:
        return {"source": "kg", "ok": False,
                "blocker": f"transport error: {body.get('_transport_error')}",
                "entities": []}

    if status == 403:
        reason = ""
        try:
            reason = body["error"]["details"][0]["metadata"].get("reason", "")
        except (KeyError, IndexError, TypeError):
            reason = str(body.get("error", {}).get("status", ""))
        if "SERVICE_BLOCKED" in reason or "API_KEY_SERVICE_BLOCKED" in str(body):
            # This is the important branch. The credential is fine; the API is
            # simply not enabled on the project. Reporting "no key" here would
            # send someone hunting for a credential that already works.
            return {
                "source": "kg",
                "ok": False,
                "blocker": (
                    "The API key is VALID but cannot reach kgsearch. Two "
                    "separate causes, check BOTH:\n"
                    "    1. the service is not enabled on the project\n"
                    "    2. the key has an API restriction that excludes "
                    "kgsearch (most common)\n"
                    f"    Fix:  gcloud services enable kgsearch.googleapis.com "
                    f"--project={KG_PROJECT}\n"
                    "    Or:   https://console.cloud.google.com/apis/library/"
                    f"kgsearch.googleapis.com?project={KG_PROJECT}\n"
                    "    Restriction fix: create a dedicated key --\n"
                    "      gcloud services api-keys create "
                    f"--project={KG_PROJECT} \\\n"
                    "        --display-name='Knowledge Graph Search' \\\n"
                    "        --api-target=service=kgsearch.googleapis.com\n"
                    "    then export it as GOOGLE_KG_API_KEY."
                ),
                "entities": [],
            }
        return {"source": "kg", "ok": False,
                "blocker": f"403 {reason or 'permission denied'}",
                "entities": []}

    if status != 200:
        msg = body.get("error", {}).get("message", str(body)[:300])
        return {"source": "kg", "ok": False,
                "blocker": f"HTTP {status}: {msg}", "entities": []}

    entities = []
    for item in body.get("itemListElement", []):
        node = item.get("result", {})
        # The KG @id looks like "kg:/g/11abc..." — the KGMID is the tail.
        raw_id = node.get("@id", "")
        kgmid = raw_id[3:] if raw_id.startswith("kg:") else raw_id
        entities.append({
            "kgmid": kgmid,
            "name": node.get("name"),
            "types": [t for t in node.get("@type", []) if t != "Thing"],
            "score": item.get("resultScore"),
            "description": node.get("description"),
            "url": node.get("url"),
            "detailed_url": (node.get("detailedDescription") or {}).get("url"),
            "image": (node.get("image") or {}).get("contentUrl"),
        })
    return {"source": "kg", "ok": True, "blocker": None, "entities": entities}


# -------------------------------------------------------------- serp source

def dfs_auth():
    user = os.environ.get("DATAFORSEO_USERNAME")
    pwd = os.environ.get("DATAFORSEO_PASSWORD")
    if not (user and pwd):
        return None
    import base64
    token = base64.b64encode(f"{user}:{pwd}".encode()).decode()
    return {"Authorization": f"Basic {token}",
            "Content-Type": "application/json"}


def dfs_balance(headers):
    status, body = http_json(DFS_ACCOUNT, headers=headers)
    if status != 200:
        return None
    try:
        return body["tasks"][0]["result"][0]["money"]["balance"]
    except (KeyError, IndexError, TypeError):
        return None


def lookup_serp(query, location="United States", assume_yes=False):
    """DataForSEO SERP, filtered to the knowledge_graph item type."""
    headers = dfs_auth()
    if not headers:
        return {"source": "serp", "ok": False,
                "blocker": "DATAFORSEO_USERNAME/PASSWORD not set in ~/.env.shared.",
                "entities": []}

    balance = dfs_balance(headers)
    bal_str = f"${balance:.2f}" if balance is not None else "unknown"
    sys.stderr.write(
        f"  serp: paid call. est ~${DFS_EST_COST:.4f}, balance {bal_str}\n"
    )
    if not assume_yes:
        if not sys.stdin.isatty():
            return {"source": "serp", "ok": False,
                    "blocker": "paid call declined (non-interactive, no --yes).",
                    "entities": []}
        try:
            if input("  spend it? [y/N] ").strip().lower() not in ("y", "yes"):
                return {"source": "serp", "ok": False,
                        "blocker": "paid call declined by user.", "entities": []}
        except (EOFError, KeyboardInterrupt):
            return {"source": "serp", "ok": False,
                    "blocker": "paid call declined.", "entities": []}

    payload = json.dumps([{
        "keyword": query,
        "location_name": location,
        "language_code": "en",
        "device": "desktop",
    }]).encode()
    status, body = http_json(DFS_ENDPOINT, data=payload, headers=headers, timeout=90)

    if status != 200:
        return {"source": "serp", "ok": False,
                "blocker": f"HTTP {status}: {str(body)[:300]}", "entities": []}

    try:
        items = body["tasks"][0]["result"][0]["items"] or []
    except (KeyError, IndexError, TypeError):
        return {"source": "serp", "ok": False,
                "blocker": f"unexpected response shape: {str(body)[:300]}",
                "entities": []}

    entities = []
    for item in items:
        if item.get("type") != "knowledge_graph":
            continue
        entities.append({
            "kgmid": None,
            "name": item.get("title"),
            "types": [item.get("subtitle")] if item.get("subtitle") else [],
            "score": None,
            "description": item.get("description"),
            "url": item.get("url"),
            "detailed_url": None,
            "image": item.get("image_url"),
        })
    return {"source": "serp", "ok": True, "blocker": None, "entities": entities}


# ------------------------------------------------------------------ output

def norm(u):
    """Compare URLs ignoring scheme, www and trailing slash."""
    if not u:
        return ""
    u = re.sub(r"^https?://", "", u.strip().lower())
    u = re.sub(r"^www\.", "", u)
    return u.rstrip("/")


def report(query, results, entity_home):
    print(f"\nKGMID LOOKUP — {query}")
    if entity_home:
        print(f"  Entity Home: {entity_home}")
    print()

    verdict_lines = []

    for res in results:
        label = {"kg": "Google Knowledge Graph API",
                 "serp": "Google SERP panel (DataForSEO)"}[res["source"]]
        print(f"  [{res['source']}] {label}")

        if not res["ok"]:
            print(f"      BLOCKED — {res['blocker']}")
            print()
            verdict_lines.append(f"{res['source']}: blocked")
            continue

        if not res["entities"]:
            print("      NOT FOUND — Google's graph holds no entity for this "
                  "query.")
            print("      This is the expected answer before a panel exists. "
                  "It is a finding, not an error.")
            print()
            verdict_lines.append(f"{res['source']}: not found")
            continue

        for i, e in enumerate(res["entities"], 1):
            print(f"      {i}. {e['name']}")
            if e["kgmid"]:
                print(f"         KGMID:       {e['kgmid']}")
            if e["score"] is not None:
                print(f"         resultScore: {e['score']}")
            if e["types"]:
                print(f"         types:       {', '.join(t for t in e['types'] if t)}")
            if e["description"]:
                print(f"         description: {e['description']}")
            if e["url"]:
                print(f"         url:         {e['url']}")
            elif res["source"] == "kg":
                print("         url:         (none — Google holds no URL for "
                      "this entity)")
            if e["detailed_url"]:
                print(f"         detailed:    {e['detailed_url']}")
            print()

        verdict_lines.append(f"{res['source']}: {len(res['entities'])} found")

        # The diagnostic that matters most: does Google point at the Entity Home?
        if entity_home:
            top = res["entities"][0]
            if not top.get("url"):
                print(f"      ENTITY HOME: Google holds no url for the top "
                      f"result. Nothing to reconcile against — the "
                      f"corroboration loop has not landed yet.\n")
            elif norm(top["url"]) == norm(entity_home):
                print("      ENTITY HOME: MATCH — Google's url is your Entity "
                      "Home. The loop is closed.\n")
            else:
                print(f"      ENTITY HOME: MISMATCH\n"
                      f"          Google holds: {top['url']}\n"
                      f"          You claim:    {entity_home}\n"
                      f"          More schema will not fix this. External "
                      f"profiles are pointing somewhere else.\n")

    print("VERDICT: " + " | ".join(verdict_lines))


def main():
    ap = argparse.ArgumentParser(
        description="Look up an entity's KGMID, confidence and URL.")
    ap.add_argument("query", help="entity name, exactly as written everywhere else")
    ap.add_argument("--url", dest="entity_home",
                    help="the Entity Home URL you expect Google to hold")
    ap.add_argument("--source", choices=["kg", "serp", "both"], default="kg",
                    help="kg (free, default), serp (paid), or both")
    ap.add_argument("--location", default="United States",
                    help="SERP location name (serp source only)")
    ap.add_argument("--limit", type=int, default=5,
                    help="max KG results (default 5)")
    ap.add_argument("--yes", action="store_true",
                    help="skip the confirmation prompt for paid serp calls")
    ap.add_argument("--json", action="store_true",
                    help="emit raw JSON instead of the report")
    args = ap.parse_args()

    load_env()

    results = []
    if args.source in ("kg", "both"):
        results.append(lookup_kg(args.query, args.limit))
    if args.source in ("serp", "both"):
        results.append(lookup_serp(args.query, args.location, args.yes))

    if args.json:
        print(json.dumps({"query": args.query,
                          "entity_home": args.entity_home,
                          "results": results}, indent=2))
    else:
        report(args.query, results, args.entity_home)

    # Exit non-zero only on transport/auth failure. "Not found" is the
    # expected pre-panel answer and must not read as a broken tool.
    return 1 if all(not r["ok"] for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
