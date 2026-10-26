#!/usr/bin/env python3
"""Short-drop link previews without the empty band (prepared 2026-10-26, NOT deployed).

render_cards.py centres a short drop (full card <= 630 px tall at 1200 wide) on a 1200x630 board-colour
canvas, which leaves an empty band above (and below) the post. This renders the same full card
(post + caption, text checked against data/drops.js) at a narrower CSS width and a higher pixel ratio so the
1200-wide image is as close to 630 tall as possible: the post is enlarged to fill the frame, never stretched
(uniform scale; lines may wrap differently, the text is identical). Max enlargement MAX_ZOOM.
Medium and long drops already use a top crop with no band and are not touched.

Usage:
  python3 tools/drop-cards/fill_short.py --out DIR 1 3709 ...        # writes DIR/before/N.jpg, DIR/after/N.jpg
  python3 tools/drop-cards/fill_short.py --out DIR --all              # every short drop (after/ only)
  --allow-wrap   keep zooming even if the header line (name/date/No.) wraps (variant B)
Upload is a separate, manual step (see README in the report folder); this script never uploads.
"""
import io, os, sys, json
from PIL import Image
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_cards as rc

MAX_ZOOM = 1.6          # at most 1.6x the 600-css-px replica (scale 2 -> 3.2)
W_FULL, H_OG = 1200, 630
PAD = 18                # breathing room kept above and below the card in the 1200x630 frame

HDR_H = "()=>{var e=document.querySelector('.postInfo,p.intro');return e?e.getBoundingClientRect().height:0}"

def shot(pg, n, css_w, with_hdr=False):
    pg.set_viewport_size({"width": css_w, "height": 40})
    pg.set_content(rc.page(n, width=css_w, scale=W_FULL / css_w)); pg.wait_for_timeout(60); rc.check(pg, n)
    im = Image.open(io.BytesIO(pg.screenshot(full_page=True))).convert("RGB")
    return (im, pg.evaluate(HDR_H)) if with_hdr else im

def before(pg, n):
    im = shot(pg, n, 600)
    if im.height > H_OG: return None, im.height
    can = Image.new("RGB", (W_FULL, H_OG), rc.BG); can.paste(im, (0, (H_OG - im.height) // 2)); return can, im.height

def after(br, n, allow_wrap=False):
    """largest zoom whose card still fits 630 - 2*PAD and whose header line (name, date, No.) still sits on
    one line as posted. Each width needs its own page (pixel ratio is per page)."""
    best = None; hdr0 = None
    lo_w = int(600 / MAX_ZOOM)
    for css_w in range(600, lo_w - 1, -10):
        pg = br.new_page(viewport={"width": css_w, "height": 40}, device_scale_factor=W_FULL / css_w)
        try: im, hh = shot(pg, n, css_w, True)
        finally: pg.close()
        if hdr0 is None: hdr0 = hh
        if hh > hdr0 + 2 and not allow_wrap: break    # header would wrap: stop zooming
        if im.width != W_FULL: im = im.resize((W_FULL, round(im.height * W_FULL / im.width)), Image.LANCZOS)  # rounding only (<=1px)
        if im.height <= H_OG - 2 * PAD: best = (css_w, im)
        else: break
    if best is None: return None, None
    css_w, im = best
    can = Image.new("RGB", (W_FULL, H_OG), rc.BG); can.paste(im, (0, (H_OG - im.height) // 2))
    return can, css_w

def main(nums, out, want_before=True, allow_wrap=False):
    for d in ("before", "after"): os.makedirs(os.path.join(out, d), exist_ok=True)
    rep = {}
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 600, "height": 40}, device_scale_factor=2)
        for n in nums:
            b, h600 = before(pg, n)
            kind = "short" if b is not None else ("long" if h600 > rc.LONG_H else "medium")
            r = {"kind": kind, "card_h_1200": h600}
            if b is not None:
                if want_before: b.save(os.path.join(out, "before", f"{n}.jpg"), "JPEG", quality=86, optimize=True, progressive=True)
                a, css_w = after(br, n, allow_wrap)
                if a is not None:
                    a.save(os.path.join(out, "after", f"{n}.jpg"), "JPEG", quality=86, optimize=True, progressive=True)
                    r.update(css_w=css_w, zoom=round(600 / css_w, 2))
            rep[n] = r; print(n, r, flush=True)
        br.close()
    json.dump(rep, open(os.path.join(out, "fill_report.json"), "w"), indent=1)

if __name__ == "__main__":
    a = sys.argv[1:]; out = os.path.join(rc.ROOT, ".work", "drop-cards-fill")
    if "--out" in a: i = a.index("--out"); out = a[i + 1]; del a[i:i + 2]
    wrap = "--allow-wrap" in a
    if wrap: a.remove("--allow-wrap")
    if "--all" in a: main(sorted(rc.DROPS), out, want_before=False, allow_wrap=wrap)
    else: main([int(x) for x in a], out, allow_wrap=wrap)
