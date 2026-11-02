#!/usr/bin/env python3
"""Share-card regression gate (prepared 2026-11-02). Audits EVERY link-preview card a share page points at.

    python3 tools/share-card-audit.py drops  --pages ROOT|URL [--img-map URLPREFIX=DIR] [--layout cards-v4.json] [--jobs 6] --csv OUT.csv
    python3 tools/share-card-audit.py memes  --pages ROOT|URL [--img-map URLPREFIX=DIR] --csv OUT.csv

--pages: a local checkout (reads drops/share/N.html, memes/share/*.html) or the live site base URL
         (https://therubberduck.net -> fetches every share page, then every og:image, as Twitterbot would).
--img-map: read og:image URLs that start with URLPREFIX from a local directory instead (preview, before upload).
Per card, pass/fail:
  fetch  - 200, image/* content type, no redirect, < 5 MB (X limit), og:image == twitter:image, summary_large_image
  meta   - og:image:width/height present and equal to the real pixel size
  dims   - X/Facebook/iMessage show link cards in a fixed ~1.91:1 frame (X web 2:1-ish) and cover-crop anything else:
           pass when 1.89 <= w/h <= 1.92 and w >= 1200 (so X/FB crop <= 1 %)
  safe   - simulate the crop X applies (1.91:1 and 2:1, landscape centre-cropped, portrait top-anchored); every
           non-background pixel (text, image, logo/caption) must stay inside the crop with a 1 % inset
  text   - drops only: re-render the FULL drop at the card's layout (css width, columns, zoom from --layout) without
           any cut; the card's content height must be >= the full layout height (12 px tolerance) -> no hidden lines
Writes one CSV row per card plus a summary (stdout and OUT.summary.json). Exit code 1 when anything fails.
"""
import csv, io, json, os, re, sys, time, argparse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageChops

UA = "Twitterbot/1.0"
TOL = 10   # px: painted card content may be at most this much shorter than the full layout (a hidden line is >= 19 px)
HERE = os.path.dirname(os.path.abspath(__file__))
META = lambda s, k: (re.search(r'<meta (?:property|name)="%s" content="([^"]*)"' % re.escape(k), s) or [None, None])[1]

def get(url, head_only=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method="HEAD" if head_only else "GET")
    class NoRedir(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k): return None
    op = urllib.request.build_opener(NoRedir)
    for t in range(3):
        try:
            r = op.open(req, timeout=30); return r.status, dict(r.headers), (b"" if head_only else r.read())
        except urllib.error.HTTPError as e: return e.code, dict(e.headers or {}), b""
        except Exception as e:
            if t == 2: return 0, {}, str(e).encode()
            time.sleep(1 + t)

def load_page(pages, rel):
    if pages.startswith("http"): st, h, b = get(pages.rstrip("/") + "/" + rel); return b.decode("utf-8", "replace") if st == 200 else None
    p = os.path.join(pages, rel); return open(p, encoding="utf-8").read() if os.path.exists(p) else None

def load_img(url, maps):
    for pre, d in maps:
        if url.startswith(pre):
            p = os.path.join(d, url[len(pre):])
            if not os.path.exists(p): return 404, "", b""
            ext = p.rsplit(".", 1)[-1].lower()
            return 200, {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif", "webp": "image/webp"}.get(ext, "?"), open(p, "rb").read()
    st, h, b = get(url); h = {k.lower(): v for k, v in h.items()}
    return st, h.get("content-type", ""), b

def bg_bbox(im):
    """bbox of everything that differs from the card background (colour of the corner pixels)"""
    im = im.convert("RGB"); w, h = im.size
    corners = [im.getpixel(p) for p in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]]
    bg = tuple(sorted(c[i] for c in corners)[1] for i in range(3))   # robust to JPEG noise
    near = sum(1 for c in corners if max(abs(c[i] - bg[i]) for i in range(3)) <= 10)
    diff = ImageChops.difference(im, Image.new("RGB", im.size, bg)).convert("L").point(lambda v: 255 if v > 24 else 0)
    return diff.getbbox(), bg, near

def crop_frame(w, h, ar):
    """visible rect when a platform cover-fits a w x h image into an ar:1 frame (landscape centre, portrait top)"""
    if w / h > ar: vw = h * ar; x0 = (w - vw) / 2; return (x0, 0, x0 + vw, h)
    vh = w / ar
    return (0, 0, w, vh) if h > w else (0, (h - vh) / 2, w, (h - vh) / 2 + vh)

def check_image(st, ctype, body, ow, oh):
    r = {"http": st, "ctype": ctype, "bytes": len(body), "w": "", "h": "", "aspect": "", "x_lost_pct": "",
         "fetch_ok": False, "meta_ok": False, "dims_ok": False, "safe_ok": False, "bbox": ""}
    if st != 200 or not body: return r, None
    try: im = Image.open(io.BytesIO(body)); im.load()
    except Exception as e: r["ctype"] += " UNDECODABLE"; return r, None
    w, h = im.size; r.update(w=w, h=h, aspect=round(w / h, 3))
    r["fetch_ok"] = ctype.startswith("image/") and len(body) < 5_000_000
    r["meta_ok"] = str(w) == str(ow) and str(h) == str(oh)
    r["dims_ok"] = 1.89 <= w / h <= 1.92 and w >= 1200
    bb, bg, nbg = bg_bbox(im); r["bbox"] = "%s,%s,%s,%s" % bb if bb else ""
    lost, ok = 0.0, True
    for ar in (1.91, 2.0):
        fx0, fy0, fx1, fy1 = crop_frame(w, h, ar)
        lost = max(lost, 1 - (fx1 - fx0) * (fy1 - fy0) / (w * h))
        ix, iy = (fx1 - fx0) * 0.01, (fy1 - fy0) * 0.01
        box = bb if (bb and nbg >= 3) else (0, 0, w, h)          # no uniform border -> the whole image is content
        if not (box[0] >= fx0 + ix - 0.5 and box[1] >= fy0 + iy - 0.5 and box[2] <= fx1 - ix + 0.5 and box[3] <= fy1 - iy + 0.5):
            ok = False
    r["x_lost_pct"] = round(100 * lost, 1); r["safe_ok"] = ok
    return r, im

# ---------- drops: full-layout re-render ----------
class Layout:
    def __init__(self, spec):
        sys.path.insert(0, os.path.join(HERE, "drop-cards"))
        import rightsize as rs; self.rs = rs; self.spec = spec; self.pw = self.br = None
    def page(self):
        if self.br is None:
            from playwright.sync_api import sync_playwright
            self.pw = sync_playwright().start(); self.br = self.pw.chromium.launch(); self.pg = self.br.new_page()
        return self.pg
    def full_h(self, n):
        s = self.spec.get(str(n))
        if not s or "css_w" not in s: return None
        css_w, cols, wout = s["css_w"], s.get("cols", 1), s.get("w_content", 1200)
        html = self.rs.html_for(n, css_w, wout / css_w)
        if cols > 1: html = html.replace("</head>", "<style>.pre{column-count:%d;column-gap:24px;orphans:2;widows:2}</style></head>" % cols, 1)
        pg = self.page(); pg.set_viewport_size({"width": css_w, "height": 100}); pg.set_content(html)
        # height of the painted content (union of all element boxes), in card pixels
        hh = pg.evaluate("""()=>{let t=1e9,b=-1e9;for(const e of document.body.querySelectorAll('*')){const r=e.getBoundingClientRect();
            if(r.width>0&&r.height>0&&getComputedStyle(e).visibility!=='hidden'){t=Math.min(t,r.top);b=Math.max(b,r.bottom);}}return b-t;}""")
        return hh * wout / css_w
    def close(self):
        if self.br: self.br.close(); self.pw.stop()

def audit_drop(args, maps, n, lay):
    rel = "drops/share/%d.html" % n; s = load_page(args.pages, rel)
    row = {"id": n, "page": rel}
    if s is None: row.update(page_ok=False); return row
    img = META(s, "og:image"); row.update(og_image=img, page_ok=True)
    ok_meta = img and img == META(s, "twitter:image") and META(s, "twitter:card") == "summary_large_image"
    st, ct, body = load_img(img, maps)
    r, im = check_image(st, ct, body, META(s, "og:image:width"), META(s, "og:image:height"))
    r["fetch_ok"] = bool(r["fetch_ok"] and ok_meta); row.update(r)
    row["text_ok"], row["full_h"], row["content_h"] = False, "", ""
    if im is not None and lay is not None:
        fh = lay.full_h(n); bb = r["bbox"]
        if fh is not None and bb:
            y0, y1 = int(bb.split(",")[1]), int(bb.split(",")[3])
            ch = y1 - y0 + 2 * 20                          # rightsize keeps a 20 px margin round the content
            row.update(full_h=round(fh), content_h=ch, text_ok=fh <= ch + 12 + 20)  # +20: caption line leading
    return row

def audit_meme(args, maps, rel):
    s = load_page(args.pages, rel); row = {"id": rel.split("/")[-1][:-5], "page": rel}
    if s is None: row.update(page_ok=False); return row
    img = META(s, "og:image"); row.update(og_image=img, page_ok=True)
    ok_meta = img and img == META(s, "twitter:image") and META(s, "twitter:card") == "summary_large_image"
    st, ct, body = load_img(img, maps)
    r, _ = check_image(st, ct, body, META(s, "og:image:width"), META(s, "og:image:height"))
    r["fetch_ok"] = bool(r["fetch_ok"] and ok_meta); row.update(r); row["text_ok"] = "n/a"
    return row

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("kind", choices=["drops", "memes"])
    ap.add_argument("--pages", required=True); ap.add_argument("--img-map", action="append", default=[])
    ap.add_argument("--layout"); ap.add_argument("--csv", required=True); ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--only", help="comma list of ids/numbers")
    args = ap.parse_args()
    maps = [tuple(m.split("=", 1)) for m in args.img_map]
    rows = []
    if args.kind == "drops":
        sys.path.insert(0, os.path.join(HERE, "drop-cards")); import render_cards as rc
        nums = [int(x) for x in args.only.split(",")] if args.only else sorted(rc.DROPS)
        spec = json.load(open(args.layout)) if args.layout else None
        if spec and "drops" in spec: spec = spec["drops"]
        lay = Layout(spec) if spec else None
        # images in threads, layout (Chromium) in this thread
        with ThreadPoolExecutor(args.jobs) as ex:
            futs = [ex.submit(audit_drop, args, maps, n, None) for n in nums]
            for n, f in zip(nums, futs):
                row = f.result()
                if lay is not None and row.get("bbox"):
                    fh = lay.full_h(n); y0, y1 = int(row["bbox"].split(",")[1]), int(row["bbox"].split(",")[3])
                    if fh is not None:
                        ch = y1 - y0; row.update(full_h=round(fh), content_h=ch, text_ok=fh <= ch + TOL)
                rows.append(row)
                if len(rows) % 250 == 0: print(len(rows), "/", len(nums), flush=True)
        if lay: lay.close()
    else:
        if args.only: rels = ["memes/share/%s.html" % x for x in args.only.split(",")]
        elif args.pages.startswith("http"):
            rels = ["memes/share/%s.html" % i["id"] for i in json.loads(get(args.pages.rstrip("/") + "/memes/data/memes.json")[2])["items"]]
        else: rels = sorted("memes/share/" + f for f in os.listdir(os.path.join(args.pages, "memes/share")) if f.endswith(".html"))
        with ThreadPoolExecutor(args.jobs) as ex:
            for i, row in enumerate(ex.map(lambda r: audit_meme(args, maps, r), rels)):
                rows.append(row)
                if (i + 1) % 500 == 0: print(i + 1, "/", len(rels), flush=True)
    checks = ["page_ok", "fetch_ok", "meta_ok", "dims_ok", "safe_ok", "text_ok"]
    for r in rows:
        r["pass"] = all(r.get(c) in (True, "n/a") for c in checks if not (c == "text_ok" and args.kind == "drops" and not args.layout))
    cols = ["id", "page", "og_image", "http", "ctype", "bytes", "w", "h", "aspect", "x_lost_pct", "bbox", "full_h", "content_h"] + checks + ["pass"]
    with open(args.csv, "w", newline="") as f:
        wr = csv.DictWriter(f, cols, extrasaction="ignore"); wr.writeheader(); wr.writerows(rows)
    summ = {"kind": args.kind, "pages": args.pages, "total": len(rows), "pass": sum(r["pass"] for r in rows)}
    for c in checks: summ[c + "_fail"] = sum(1 for r in rows if r.get(c) is False)
    summ["fail"] = summ["total"] - summ["pass"]
    json.dump(summ, open(args.csv.rsplit(".", 1)[0] + ".summary.json", "w"), indent=1); print(json.dumps(summ))
    sys.exit(0 if summ["fail"] == 0 else 1)

if __name__ == "__main__":
    main()
