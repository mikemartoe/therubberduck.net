#!/usr/bin/env python3
"""Ping IndexNow for therubberduck.net.

The key file lives at the site root as {key}.txt and is public by design.
No API secret is required. On a GitHub Actions push, this script submits
URLs for HTML (and sitemap) files changed in the push. Pass --sitemap to
submit every URL in the sitemap index, in batches.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

SITE = "https://therubberduck.net"
HOST = "therubberduck.net"
ENDPOINT = "https://api.indexnow.org/indexnow"
BATCH = 10000
ROOT = Path(__file__).resolve().parents[1]


def find_key() -> tuple[str, Path]:
    keys = []
    for p in ROOT.glob("*.txt"):
        if p.name in {".dump-ingest-status.json"}:
            continue
        text = p.read_text(encoding="utf-8").strip()
        if text and p.stem == text and 8 <= len(text) <= 128 and all(
            c.isalnum() or c in "-_" for c in text
        ):
            # typical IndexNow key file: filename is {key}.txt and body is the key
            if p.name == text + ".txt":
                keys.append((text, p))
    if not keys:
        sys.exit("No IndexNow key file found at repo root ({key}.txt).")
    if len(keys) > 1:
        sys.exit("Multiple IndexNow key files found: " + ", ".join(k[1].name for k in keys))
    return keys[0]


def to_url(path: str) -> str | None:
    path = path.replace("\\", "/").lstrip("./")
    if path.endswith(".html"):
        if path in {"offline.html", "404.html"}:
            return None
        if path == "index.html":
            return SITE + "/"
        if path.endswith("/index.html"):
            return SITE + "/" + path[: -len("index.html")]
        return SITE + "/" + path
    if path == "sitemap.xml" or path.startswith("sitemaps/"):
        return SITE + "/" + path
    return None


def changed_urls(base: str, head: str) -> list[str]:
    import subprocess

    out = subprocess.check_output(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", base, head],
        cwd=ROOT,
        text=True,
    )
    urls = []
    for line in out.splitlines():
        u = to_url(line.strip())
        if u:
            urls.append(u)
    return sorted(set(urls))


def sitemap_urls() -> list[str]:
    import re

    index = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    locs = re.findall(r"<loc>([^<]+)</loc>", index)
    urls: list[str] = []
    for loc in locs:
        name = loc.split("/sitemaps/")[-1] if "/sitemaps/" in loc else None
        if loc.rstrip("/").endswith("sitemap.xml"):
            # already the index; skip its own loc if present
            continue
        path = ROOT / "sitemaps" / name if name else None
        if not path or not path.exists():
            # try relative from site path
            rel = loc.replace(SITE + "/", "")
            path = ROOT / rel
        if not path.exists():
            print("missing sitemap", loc, file=sys.stderr)
            continue
        text = path.read_text(encoding="utf-8")
        urls.extend(re.findall(r"<loc>([^<]+)</loc>", text))
    # unique, keep order
    seen = set()
    out = []
    for u in urls:
        if u not in seen and u.startswith(SITE):
            seen.add(u)
            out.append(u)
    return out


def post(key: str, urls: list[str]) -> tuple[int, str]:
    body = json.dumps(
        {"host": HOST, "key": key, "keyLocation": f"{SITE}/{key}.txt", "urlList": urls}
    ).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            return res.status, res.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sitemap", action="store_true", help="Submit every URL in the sitemap index")
    ap.add_argument("--base", default="", help="git base SHA (default: previous commit)")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    key, keypath = find_key()
    print("key file:", keypath.name)

    if args.sitemap:
        urls = sitemap_urls()
    else:
        base = args.base
        if not base:
            import subprocess

            try:
                base = subprocess.check_output(
                    ["git", "rev-parse", "HEAD~1"], cwd=ROOT, text=True
                ).strip()
            except Exception:
                print("No previous commit; nothing to diff. Use --sitemap for a full submit.")
                return 0
        urls = changed_urls(base, args.head)

    if not urls:
        print("No URLs to submit.")
        return 0
    print(f"{len(urls)} URL(s) to submit")
    ok = True
    for i in range(0, len(urls), BATCH):
        batch = urls[i : i + BATCH]
        print(f"batch {i // BATCH + 1}: {len(batch)} URLs")
        if args.dry_run:
            print("dry-run, first 5:", batch[:5])
            continue
        status, body = post(key, batch)
        print("IndexNow response:", status, body[:300])
        if status not in (200, 202):
            ok = False
        if i + BATCH < len(urls):
            time.sleep(1)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
