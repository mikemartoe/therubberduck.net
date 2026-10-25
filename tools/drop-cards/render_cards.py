#!/usr/bin/env python3
"""Q-drop share cards (approved v4 layout, 2026-10-25) for the share feature.

Replica of the original post (name, trip, ID, Eastern date/time, post No.), no board banner,
wide Unicode spaces shown as ordinary spaces IN THE IMAGE ONLY (data/drops.js is never changed),
caption under the post box: "Q drop #N · site /board/ · [duck] therubberduck.net".
Duck = images/brand/duck-hero-soft.png (transparent background, no fill, no circle).

Outputs (default OUT = <repo>/.work/drop-cards, git-ignored; upload to R2 trd-memes under drops/):
  card/N.png  full drop, 1200 px wide, any height (never truncated)          -> what gets shared/saved
  og/N.jpg    1200x630 link-preview image (short: centred; long: top crop + caption)
  ig/N.png    1080x1350 phone/Instagram top crop, ONLY for long drops (caption only, no extra line)
Every render asserts the rendered post text == drops.js text (wide spaces normalised).

Usage:  python3 tools/drop-cards/render_cards.py 1 134 225          # some drops
        python3 tools/drop-cards/render_cards.py --all [--from N]     # all 4,966 (resumable)
        python3 tools/drop-cards/render_cards.py --out DIR ...
"""
import json, re, sys, html, os, base64, io, time
from datetime import datetime
from zoneinfo import ZoneInfo
from PIL import Image
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DUCK_SRC = os.path.join(ROOT, "images/brand/duck-hero-soft.png")
_DUCK = Image.open(DUCK_SRC).convert("RGBA")
_DUCK = _DUCK.crop(_DUCK.getbbox())
DUCK_AR = _DUCK.width / _DUCK.height
def duck_uri(px_h):
    im = _DUCK.resize((max(1, round(px_h * DUCK_AR)), px_h), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, "PNG"); return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()
SITE = {"4chan": "4chan", "8chan": "8chan", "8kun": "8kun"}
def caption_html(n, scale, css_px=16, font_pt=9.5):
    num, _, site, board = DROPS[n][:4]
    w = round(css_px * DUCK_AR, 2)
    return (f'<div class="cap"><span>Q drop #{num}</span><span class="dot">&middot;</span>'
            f'<span>{SITE[site]} /{esc(board.strip("/"))}/</span><span class="dot">&middot;</span>'
            f'<span class="site"><img class="duck" width="{w}" height="{css_px}" src="{duck_uri(round(css_px*scale))}" alt="">therubberduck.net</span></div>')
CAP_CSS = """.cap{clear:both;display:flex;justify-content:center;align-items:center;gap:0;margin:10px auto 2px;padding:7px 0 1px;
 border-top:1px solid #B7C5D9;font:%(pt)spt arial,"Liberation Sans",sans-serif;color:#34345C;line-height:1;white-space:nowrap}
.cap .dot{margin:0 .6em;color:#7d84a8}.cap .site{display:inline-flex;align-items:center;font-weight:bold}
.cap .duck{display:block;margin-right:.35em}"""
WIDE = re.compile("[\u2000-\u200A\u3000]")
norm = lambda s: WIDE.sub(" ", s)
ET = ZoneInfo("America/New_York")
raw = open(os.path.join(ROOT, "data/drops.js"), encoding="utf-8").read().strip()
DROPS = {d[0]: d for d in json.loads(raw[raw.index("["):raw.rstrip(";").rindex("]") + 1])}
HDR = {r["drop"]: r for r in json.load(open(os.path.join(HERE, "header-table.json")))}
b64 = lambda p, t: f"data:{t};base64," + base64.b64encode(open(os.path.join(HERE, "assets", p), "rb").read()).decode()
FADE = b64("fade-blue.png", "image/png")
FLAG = {"US": b64("flag-us.gif", "image/gif")}
COUNTRY = {"US": "United States"}
esc = lambda s: html.escape(s, quote=False)

def id_color(s):  # 4chan extension.js IDColor.compute / $.hash, 32-bit JS int semantics
    h = 0
    for ch in s:
        h = ((h << 5) - h + ord(ch)) & 0xFFFFFFFF
    if h & 0x80000000: h -= 1 << 32
    r, g, b = (h >> 24) & 255, (h >> 16) & 255, (h >> 8) & 255
    return r, g, b, ("black" if .299 * r + .587 * g + .114 * b > 125 else "white")

def body(text, site):
    out = []
    for line in text.split("\n"):
        parts = re.split(r"(>>\d+)", line)
        if re.match(r"^>(?!>\d)", line):           # greentext line
            out.append(f'<span class="quote">{esc(line)}</span>')
        else:
            s = "".join(f'<a class="quotelink">&gt;&gt;{p[2:]}</a>' if re.fullmatch(r">>\d+", p) else
                        (re.sub(r"(https?://[^\s<]+)", r'<a class="url">\1</a>', esc(p)) if site != "4chan" else esc(p))
                        for p in parts)
            out.append(s)
    return "\n".join(out)

CSS_4CH = f"""*{{box-sizing:content-box}}html{{margin:0}}
body{{width:%WIDTH%px;margin:0;padding-top:8px !important;padding:0 5px;background:#EEF2FF url({FADE}) top center repeat-x;color:#000;font-family:arial,helvetica,"Liberation Sans",sans-serif;font-size:10pt}}
div.boardBanner{{text-align:center;clear:both;color:#AF0A0F}}
div.boardTitle{{font-family:Tahoma,"DejaVu Sans",sans-serif;font-size:28px;font-weight:bold;letter-spacing:-2px;margin-top:0}}
hr{{border:none;border-top:1px solid #B7C5D9;height:0}}
div.sideArrows{{color:#B7C5D9;float:left;margin:0 2px 0 2px}}
div.reply{{background-color:#D6DAF0;border:1px solid #B7C5D9;border-left:none;border-top:none;display:table;padding:2px}}
div.op{{display:block}}
div.postInfo{{display:block}}
input[type=checkbox]{{margin:3px 3px 3px 4px;vertical-align:middle;width:13px;height:13px}}
span.nameBlock{{display:inline-block}}
span.name{{color:#117743;font-weight:bold}}
span.postertrip{{color:#117743;font-weight:normal}}
span.subject{{color:#0F0C5D;font-weight:bold}}
.posteruid .hand{{padding:0 5px;border-radius:6px;font-size:.8em}}
.flag{{display:inline-block;width:16px;height:11px;position:relative;top:1px}}
span.postNum a{{text-decoration:none;color:#000}}
blockquote.postMessage{{display:block;margin:13px 40px;white-space:pre-wrap;overflow-wrap:anywhere}}
blockquote > span.quote{{color:#789922}}
a.quotelink{{color:#D00;text-decoration:underline}}
.fileText{{margin-left:20px}}.fileText a{{text-decoration:underline;color:#34345C}}
.thumbph{{display:inline-block;margin:3px 20px 5px 20px;background:#c9cde6;border:1px dashed #8a93b8;color:#4b5375;font-size:8pt;text-align:center}}
.foot{{clear:both;margin-top:8px;color:#5a5a7a;font-size:8pt;text-align:right}}.foot b{{color:#34345C}}"""

CSS_VICHAN = f"""*{{box-sizing:content-box}}html{{margin:0}}
body{{width:%WIDTH%px;background:#EEF2FF url({FADE}) repeat-x 50% 0%;color:black;font-family:arial,helvetica,"Liberation Sans",sans-serif;font-size:10pt;margin:0 4px;padding:8px 4px 4px}}
h1{{font-family:tahoma,"DejaVu Sans",sans-serif;letter-spacing:-2px;font-size:20pt;margin:0;color:#AF0A0F;text-align:center}}
hr{{border:none;border-top:1px solid #B7C5D9;height:0;margin:8px 0}}
div.post.reply{{background:#D6DAF0;margin:.2em 4px;padding:.5em .3em .5em .6em;border-width:1px;border-style:none solid solid none;border-color:#B7C5D9;display:inline-block;max-width:94%}}
div.post.op{{margin-right:20px;margin-bottom:5px}}
.intro{{margin:.5em 0;padding:0 0 .2em}}
input[type=checkbox]{{margin:0 3px 0 0;vertical-align:middle;width:13px;height:13px}}
.intro span.subject{{color:#0F0C5D;font-weight:bold}}
.intro span.name{{color:#117743;font-weight:bold}}
span.trip{{color:#228854}}
.intro a{{margin-left:5px;color:inherit;text-decoration:none}}.intro a.post_no{{margin:0}}
.poster_id{{white-space:nowrap}}.poster_id::before{{content:" ID: "}}
div.post div.body{{word-wrap:break-word;white-space:pre-wrap;overflow-wrap:anywhere}}
div.post.reply div.body{{margin-left:1.8em}}
div.post.reply div.body a{{color:#D00}}
.quote{{color:#789922}}
a.quotelink,a.url{{text-decoration:underline}}
p.fileinfo{{display:block;margin:0 0 0 20px}}
.thumbph{{display:inline-block;margin:5px 20px 10px 20px;background:#c9cde6;border:1px dashed #8a93b8;color:#4b5375;font-size:8pt;text-align:center}}
.foot{{clear:both;margin-top:8px;color:#5a5a7a;font-size:8pt;text-align:right}}.foot b{{color:#34345C}}"""

def files_html(h, site):
    if not h["files"]: return ""
    out = []
    for f in h["files"].split("; "):
        out.append(f'<div class="file"><{"div class=fileText" if site=="4chan" else "p class=fileinfo"}>File: {esc(f)}</{"div" if site=="4chan" else "p"}>'
                   f'<span class="thumbph" style="width:125px;height:125px;line-height:125px">image</span></div>')
    return "".join(out)

def page(n, width=600, footer=True, scale=2):
    num, ts, site, board, url, text = DROPS[n]; h = HDR[n]; text = norm(text)
    b = board.strip("/"); t = datetime.fromtimestamp(ts, ET)
    if site == "4chan":
        uid = ""
        if h["poster_id"]:
            r, g, bb, fg = id_color(h["poster_id"])
            uid = f' <span class="posteruid">(ID: <span class="hand" style="background-color:rgb({r},{g},{bb});color:{fg}">{esc(h["poster_id"])}</span>)</span>'
        flag = f' <img class="flag" title="{COUNTRY.get(h["country"], h["country"])}" src="{FLAG[h["country"]]}">' if h["country"] in FLAG else ""
        subj = f'<span class="subject">{esc(h["subject"])}</span> ' if h["subject"] else '<span class="subject"></span> '
        trip = f' <span class="postertrip">{esc(h["trip"])}</span>' if h["trip"] else ""
        info = (f'<div class="postInfo"><input type="checkbox"> {subj}<span class="nameBlock"><span class="name">{esc(h["name"])}</span>'
                f'{trip}{uid}{flag} </span> <span class="dateTime">{t.strftime("%m/%d/%y(%a)%H:%M:%S")}</span> '
                f'<span class="postNum"><a>No.</a><a>{esc(h["post_no"])}</a></span></div>')
        msg = f'<blockquote class="postMessage pre">{body(text, site)}</blockquote>'
        title = h["board_title"] or f"/{b}/"
        if h["op"]:
            post = f'<div class="post op">{files_html(h, site)}{info}{msg}</div>'
        else:
            post = f'<div class="postContainer"><div class="sideArrows">&gt;&gt;</div><div class="post reply">{info}{files_html(h, site)}{msg}</div></div>'
        top = ''
        css = CSS_4CH
    else:
        subj = f'<span class="subject">{esc(h["subject"])}</span> ' if h["subject"] else ""
        trip = f' <span class="trip">{esc(h["trip"])}</span>' if h["trip"] else ""
        pid = f' <span class="poster_id">{esc(h["poster_id"])}</span>' if h["poster_id"] else ""
        info = (f'<p class="intro"><input type="checkbox"> <label>{subj}<span class="name">{esc(h["name"])}</span>{trip}&nbsp; '
                f'<time>{t.strftime("%m/%d/%y (%a) %H:%M:%S")}</time></label>{pid}&nbsp;<a class="post_no">No.</a><a class="post_no">{esc(h["post_no"])}</a></p>')
        msg = f'<div class="body pre">{body(text, site)}</div>'
        if h["op"]:
            post = f'<div class="thread">{files_html(h, site)}<div class="post op">{info}{msg}</div></div>'
        else:
            post = f'<div class="post reply">{info}{files_html(h, site)}{msg}</div>'
        top = ''
        css = CSS_VICHAN
    foot = caption_html(n, scale) if footer else ""
    css = css + CAP_CSS % {"pt": 9.5}
    return f'<!doctype html><html><head><meta charset="utf-8"><style>{css.replace("%WIDTH%", str(width - 10 if site=="4chan" else width - 16))}</style></head><body>{top}{post}{foot}</body></html>'

def check(pg, n):
    got = pg.eval_on_selector(".pre", "e=>e.innerText")
    assert got == norm(DROPS[n][5]), f"text mismatch on drop {n}"

BAR = """<div class="bar" style="position:fixed;left:0;right:0;bottom:0;height:%(h)dpx;z-index:9;box-sizing:border-box;
background:linear-gradient(rgba(238,242,255,0),#EEF2FF 55%%);display:flex;flex-direction:column;justify-content:flex-end;align-items:center;padding-bottom:%(pb)dpx">%(cap)s</div>"""
BG = (238, 242, 255)
LONG_H = 1500          # a 1200-wide card taller than this is "long" (taller than 4:5) -> gets an ig/ crop

def crop_shot(br, n, css_w, css_h, scale, bar_h, cap_px, cap_pt, path, fmt):
    pg = br.new_page(viewport={"width": css_w, "height": css_h}, device_scale_factor=scale)
    pg.set_content(page(n, width=css_w, footer=False)); pg.wait_for_timeout(80); check(pg, n)
    cap = caption_html(n, scale, css_px=cap_px).replace('class="cap"', f'class="cap" style="border-top:none;margin:0;padding:0;font-size:{cap_pt}pt"')
    pg.evaluate("h=>document.body.insertAdjacentHTML('beforeend',h)", BAR % {"h": bar_h, "pb": round(30/scale), "cap": cap})
    png = pg.screenshot(full_page=False); pg.close()
    im = Image.open(io.BytesIO(png)).convert("RGB")
    if fmt == "jpg": im.save(path, "JPEG", quality=86, optimize=True, progressive=True)
    else: im.save(path, "PNG", optimize=True)

def main(nums, out, shard=None):
    for d in ("card", "og", "ig"): os.makedirs(os.path.join(out, d), exist_ok=True)
    man_p = os.path.join(out, "manifest.json" if shard is None else f"manifest.shard{shard}.json")
    err_p = os.path.join(out, "errors.txt" if shard is None else f"errors.shard{shard}.txt")
    man = json.load(open(man_p)) if os.path.exists(man_p) else {}
    t0 = time.time()
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 600, "height": 40}, device_scale_factor=2)
        for i, n in enumerate(nums):
            if str(n) in man and os.path.exists(os.path.join(out, "card", f"{n}.png")): continue   # resumable
            try:
                pg.set_content(page(n)); pg.wait_for_timeout(60); check(pg, n)
            except Exception as e:      # log and carry on; a drop with no image gets no share page
                open(err_p, "a").write(f"{n}\t{e}\n"); print(f"ERROR #{n}: {e}", flush=True); continue
            cp = os.path.join(out, "card", f"{n}.png")
            Image.open(io.BytesIO(pg.screenshot(full_page=True))).save(cp, "PNG", optimize=True)
            w, h = Image.open(cp).size
            long_ = h > LONG_H
            op = os.path.join(out, "og", f"{n}.jpg")
            if h <= 630:      # short: centre the whole card on the board colour
                can = Image.new("RGB", (1200, 630), BG); can.paste(Image.open(cp).convert("RGB"), (0, (630 - h) // 2))
                can.save(op, "JPEG", quality=86, optimize=True, progressive=True)
            try:
              if h > 630:     # tall: top of the post, faded into the caption
                crop_shot(br, n, 600, 315, 2, 70, 14, 8.5, op, "jpg")
              if long_:
                crop_shot(br, n, 540, 675, 2, 90, 14, 8.5, os.path.join(out, "ig", f"{n}.png"), "png")
            except Exception as e:
                open(err_p, "a").write(f"{n}\t{e}\n"); print(f"ERROR #{n}: {e}", flush=True); continue
            man[str(n)] = {"w": w, "h": h, "long": long_, "card_bytes": os.path.getsize(cp), "og_bytes": os.path.getsize(op),
                           "ig_bytes": os.path.getsize(os.path.join(out, "ig", f"{n}.png")) if long_ else 0}
            if i % 50 == 0 or i == len(nums) - 1:
                json.dump(man, open(man_p, "w"), indent=0, sort_keys=True)
                print(f"{i+1}/{len(nums)} #{n} {w}x{h}{' long' if long_ else ''}  {time.time()-t0:.0f}s", flush=True)
        json.dump(man, open(man_p, "w"), indent=0, sort_keys=True)
        print(f"done {len(man)} in manifest  {time.time()-t0:.0f}s", flush=True)
        br.close()

if __name__ == "__main__":
    a = sys.argv[1:]; out = os.path.join(ROOT, ".work", "drop-cards")
    if "--out" in a: i = a.index("--out"); out = a[i + 1]; del a[i:i + 2]
    shard = None
    if "--shard" in a: i = a.index("--shard"); k, K = map(int, a[i + 1].split("/")); shard = k; del a[i:i + 2]
    if "--all" in a:
        frm = int(a[a.index("--from") + 1]) if "--from" in a else 1
        nums = sorted(k for k in DROPS if k >= frm)
    else:
        nums = [int(x) for x in a] or [1, 134, 225, 513, 668, 4953, 4966, 520, 3709]
    if shard is not None: nums = nums[k::K]
    main(nums, out, shard)
