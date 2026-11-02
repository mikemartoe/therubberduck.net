#!/usr/bin/env python3
"""Fixed-frame link-preview cards v4 (prepared 2026-11-02, PREVIEW, not deployed): drops/v4/og/N.jpg on R2.

Why: the v3 og2 cards (rightsize.py) were 1200 wide with a height set by the content (274-630 px), and long drops were
cut at 630 px with a fade. X (summary_large_image), Facebook and iMessage show a link card in a FIXED ~1.91:1 frame
and cover-crop whatever they get: a short card (e.g. #54, 1200x363 = 3.3:1) loses its left and right sides, a long drop
(e.g. #48) was already cut by us before X ever saw it.

v4 card = exactly 1200x630 (1.905:1, the og standard; X/Facebook crop <= 1 px per edge, a 2:1 frame crops 15 px top
and bottom). The same replica card as v3 (rightsize.html_for: header 'Q drop #N  Month D, YYYY', post box, real
attached image(s), caption '[duck] therubberduck.net'; no board credit) is rendered into a content area of
W_C x H_C (1120 x 590) and centred on the board colour, so every pixel of text, image and caption sits >= 40 px from
the left/right edge and >= 20 px from the top/bottom edge (safe after a 1.91:1 or 2:1 crop).

Fitting ladder (largest text that shows the WHOLE drop wins; text is never resampled, Chrome re-renders at the zoom):
  1. one column, CSS width from the header width up to W_FIT (640)            -> same look as the v3 cards
  2. two balanced text columns inside the post box, or one column, CSS width up to W_READ (760; body text about
     21 px in the 1200 px image, the readable floor for a phone-size link card)
  3. still too long (172 drops): 2-4 columns, CSS width up to W_MAX -> the WHOLE drop, smaller text (text_px in report)
  4. never used so far: cut after the last whole line with a fade (as v3); the audit gate fails such a card.
Every render asserts the rendered post text == data/drops.js text (render_cards.check).

Usage: python3 tools/drop-cards/fitcard.py --out DIR [--all | N N ...]   -> DIR/og/N.jpg + DIR/report.json
Uploads nothing.
"""
import io, os, sys, json, time
from PIL import Image
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_cards as rc
import rightsize as rs

CW, CH = 1200, 630          # final card
W_C, H_C = 1120, 590        # content area (centred): 40 px side, 20 px top/bottom gutter outside rightsize's own 20 px margin
W_READ = 760                # readable floor: 13.33 CSS px body * 1120/760 = 19.6 px ... see report 'text_px'
COLS_CSS = "<style>.pre{column-count:%d;column-gap:24px;orphans:2;widows:2}</style>"
W_MAX = 2400                # step 3 (very long drops): 2-4 columns, CSS width up to this -> whole drop, smaller text
rs.W_OUT, rs.H_CAP = W_C, H_C
_html_for = rs.html_for
STATE = {"cols": 1}
def html_for(n, css_w, scale, m_for=None):
    h = _html_for(n, css_w, scale, m_for)
    return h.replace("</head>", COLS_CSS % STATE["cols"] + "</head>", 1) if STATE["cols"] > 1 else h
rs.html_for = html_for

def content_h(pg, n, w, cols):
    STATE["cols"] = cols
    pg.set_viewport_size({"width": w, "height": 100}); pg.set_content(html_for(n, w, W_C / w))
    return pg.evaluate("document.documentElement.scrollHeight") * W_C / w

def smallest_fit(pg, n, lo, hi, cols):
    """smallest CSS width in [lo, hi] (step 4) at which the whole card fits H_C; None if even hi does not"""
    if content_h(pg, n, hi, cols) > H_C + 0.5: return None
    if content_h(pg, n, lo, cols) <= H_C + 0.5: return lo
    while hi - lo > 4:
        mid = (lo + hi) // 2
        if content_h(pg, n, mid, cols) <= H_C + 0.5: hi = mid
        else: lo = mid
    return hi

def plan(pg, n):
    need, css0 = rs.pick_width(pg, n)
    STATE["cols"] = 1
    f1 = rs.fit_width(pg, n, css0)                       # step 1 (unchanged v3 rule, in the new content area)
    if f1 is not None: return {"css_w": f1, "cols": 1, "step": 1, "hdr_need": need}
    cand = []
    w2 = smallest_fit(pg, n, css0, max(css0, W_READ), 2)
    if w2: cand.append((w2, 1, 2))                         # (width, tie-break: prefer 1 col, cols)
    w1 = smallest_fit(pg, n, max(css0, rs.W_FIT), max(css0, W_READ), 1)
    if w1: cand.append((w1, 0, 1))
    if cand:
        w, _, c = min(cand); return {"css_w": w, "cols": c, "step": 2, "hdr_need": need}
    cand = []
    for c in (2, 3, 4):                                    # step 3: whole drop in more columns, smaller text
        w = smallest_fit(pg, n, max(css0, W_READ), W_MAX, c)
        if w: cand.append((w, c))
    if cand:
        w, c = min(cand); return {"css_w": w, "cols": c, "step": 3, "hdr_need": need}
    return {"css_w": css0, "cols": 1, "step": 4, "hdr_need": need}

def card(br, n, p):
    STATE["cols"] = p["cols"]; css_w = p["css_w"]
    try: im, info = rs.render(br, n, css_w)
    except RuntimeError:                                 # header + thumbnails leave no room for a line: step wider
        im = None
        for w in range(max(css_w, rs.W_FIT), rs.W_HARD + 1, 20):
            try: im, info = rs.render(br, n, w); p["css_w"] = w; break
            except RuntimeError: continue
        if im is None: raise
    can = Image.new("RGB", (CW, CH), rc.BG)
    can.paste(im, ((CW - im.width) // 2, (CH - im.height) // 2))
    p.update(cut=info["cut"], content_w=im.width, content_h=im.height, w=CW, h=CH,
             text_px=round(13.333 * W_C / p["css_w"], 1))
    return can

def main(nums, out):
    os.makedirs(os.path.join(out, "og"), exist_ok=True)
    rp = os.path.join(out, "report.json"); rep = json.load(open(rp)) if os.path.exists(rp) else {}
    t0 = time.time()
    with sync_playwright() as pw:
        br = pw.chromium.launch(); pg = br.new_page()
        for i, n in enumerate(nums):
            if str(n) in rep and "error" not in rep[str(n)] and os.path.exists(os.path.join(out, "og", f"{n}.jpg")): continue
            try:
                p = plan(pg, n); im = card(br, n, p)
                im.save(os.path.join(out, "og", f"{n}.jpg"), "JPEG", quality=88, optimize=True, progressive=True)
            except Exception as e:
                p = {"error": str(e)}
            rep[str(n)] = p
            if i % 100 == 0 or i == len(nums) - 1:
                json.dump(rep, open(rp, "w")); print(f"{i+1}/{len(nums)} #{n} {p} {time.time()-t0:.0f}s", flush=True)
        br.close()
    json.dump(rep, open(rp, "w"), indent=0, sort_keys=True)

if __name__ == "__main__":
    a = sys.argv[1:]; out = os.path.join(rc.ROOT, ".work", "drops-v4")
    if "--out" in a: i = a.index("--out"); out = a[i + 1]; del a[i:i + 2]
    nums = sorted(rc.DROPS) if "--all" in a else [int(x) for x in a]
    main(nums, out)
