#!/usr/bin/env python3
"""Right-sized link-preview cards (og/N.jpg replacement), prepared 2026-10-26, NOT deployed.

Mike's reference (Q drop #1): the post cropped tight to its content. Header row (name, trip, ID, flag, date, No.)
on ONE line across the top, the post text below at a natural readable size filling the card width, a small even
margin all round, no empty band, then the thin caption strip "Q drop #N · site /board/ · [duck] therubberduck.net".
The image height is set by the content (not forced to 1200x630).

How: the same replica HTML as render_cards.py (same text check against data/drops.js) with
  - the ">>" side arrows column removed and the post box spanning the full width,
  - the same small margin (20 px in the output image) on every side and between box, caption line and caption,
  - OP posts (posted file-first) get the header row on top and the file under it,
  - the header kept on one line (white-space:nowrap, verified: never overflows),
  - CSS width W = the width the header row needs, at least W_MIN (so a short 8chan header does not
    blow the text up to a silly size), and the page rendered at pixel ratio 1200/W -> 1200 px wide output.
    Zoom is uniform and vector (Chrome re-renders the text at that ratio): never stretched, never resampled.
    The duck is rasterised from the source PNG at the final pixel size, aspect kept.
  - 2-4 attached files (105 drops) sit side by side in a row (file names ellipsised) instead of stacked.
  - Height = content. If the content would be taller than H_CAP (1.91:1 at 1200 wide), the post text is cut
    after the last WHOLE line that fits (no half-cut letters), that last line fades out, and the box bottom
    edge and caption strip follow as normal.

Usage:
  python3 tools/drop-cards/rightsize.py --out DIR 1 3709 ...    # DIR/after/N.jpg + DIR/report.json
  python3 tools/drop-cards/rightsize.py --out DIR --all          # all 4,966
  python3 tools/drop-cards/rightsize.py --measure --out DIR      # no images: sizes for every drop -> DIR/measure.json
Upload is a separate manual step; this script never uploads. og:image:height in tools/drop-share-build.py is 630
today and would have to come from report.json (per drop) if these are deployed.
"""
import io, os, sys, json, math, time
from PIL import Image
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_cards as rc

W_OUT = 1200
W_MIN = 460      # narrowest CSS width -> max zoom 600/460 = 1.30x the live replica (pixel ratio 2.61)
W_HARD = 900     # header needs even more than this -> let it wrap (reported as hdr_wrap)
W_FIT = 640      # a post too tall for H_CAP at its header width is widened (smaller zoom) up to this (zoom 0.94 of the live
                 # replica), so it shows WHOLE; only if it still does not fit is the text cut (at the header-fit zoom)
H_CAP = 630      # max output height (1200x630 = 1.91:1, the og standard)
M_OUT = 20       # even outer margin in output px (CSS px = M_OUT / pixel ratio)
MR = 34          # right margin of the post text inside the box (4chan native 40)

EXTRA = """<style>
html,body{margin:0 !important}
body{width:auto !important;padding:%(m)spx !important;background:#EEF2FF !important}
blockquote.postMessage{margin-right:%(mr)dpx !important}
div.post div.body{margin-right:%(m)spx}
div.sideArrows{display:none !important}
div.postContainer{display:block}
div.post.reply{display:block !important;max-width:none !important;margin:0 !important}
div.post.op{margin:0 !important}
div.thread{margin:0}
.postInfo,p.intro{white-space:nowrap}
p.intro{margin-top:.3em}
.cap{margin:%(m)spx 0 0 !important;padding:%(m)spx 0 0 !important}
/* 2-4 files: side by side in a row as on the board (names ellipsised), not stacked */
:has(> .file + .file) > .file{display:inline-block;vertical-align:top;width:145px}
:has(> .file + .file) > .file p.fileinfo{margin-left:20px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
:has(> .file + .file) > .file .thumbph{margin-right:0}
.post.op > .postInfo + .file{margin-top:.4em}
.pre.cut{overflow:hidden;position:relative}
.pre.cut .fade{position:absolute;left:0;right:0;pointer-events:none}
</style>"""

# OP posts are posted file-first; in the preview the header row goes on top, the file(s) right under it
OP_HDR_FIRST = """<script>for(const op of document.querySelectorAll('.post.op')){const i=op.querySelector('.postInfo,p.intro');
const fs=[...(op.closest('.thread')||op).querySelectorAll('.file')];if(!i||!fs.length)continue;let a=i;for(const f of fs){a.after(f);a=f}}</script>"""

def html_for(n, css_w, scale, m_for=None):
    h = rc.page(n, width=css_w, footer=True, scale=scale)
    m = round(M_OUT * (m_for or css_w) / W_OUT, 2)          # same ~20 px margin in the 1200-wide image whatever the zoom
    return h.replace("</head>", (EXTRA % {"m": m, "mr": MR}) + "</head>", 1).replace("</body>", OP_HDR_FIRST + "</body>", 1)

JS_HDR = """()=>{const e=document.querySelector('.postInfo,p.intro');const r=document.createRange();r.selectNodeContents(e);
const a=r.getBoundingClientRect(), b=e.getBoundingClientRect();
return {need: a.right + (document.documentElement.clientWidth - b.right), over: e.scrollWidth - e.clientWidth, h: b.height}}"""

# whole-line bottoms of the post text (CSS px, relative to .pre top)
JS_LINES = """()=>{const p=document.querySelector('.pre');const top=p.getBoundingClientRect().top;const r=document.createRange();
r.selectNodeContents(p);const bs=new Set();for(const q of r.getClientRects()){if(q.height>0)bs.add(Math.round((q.bottom-top)*100)/100)}
return [...bs].sort((x,y)=>x-y)}"""

JS_CUT = """([hpx,lh])=>{const p=document.querySelector('.pre');p.classList.add('cut');p.style.height=hpx+'px';
let e=p, bg='';while(e){bg=getComputedStyle(e).backgroundColor;if(/^rgb[(]/.test(bg))break;e=e.parentElement}
if(!e)bg='rgb(238, 242, 255)';const f=p.querySelector('.fade')||document.createElement('span');f.className='fade';
f.style.top=(hpx-lh)+'px';f.style.height=lh+'px';f.style.background='linear-gradient('+bg.replace('rgb(','rgba(').replace(')',', 0)')+','+bg.replace('rgb(','rgba(').replace(')',', .88)')+')';
p.appendChild(f);return document.documentElement.scrollHeight}"""

def pick_width(pg, n):
    pg.set_viewport_size({"width": W_HARD, "height": 100})
    need = W_MIN
    for _ in range(3):                                 # margin depends on the final width: converge (2 rounds suffice)
        pg.set_content(html_for(n, W_HARD, 2, m_for=need)); rc.check(pg, n)
        need = math.ceil(pg.evaluate(JS_HDR)["need"]) + 2
    return need, min(max(need, W_MIN), W_HARD)

def fit_width(pg, n, css_w, w_max=W_FIT):
    """smallest W in [css_w, max(css_w, w_max)] at which the whole card fits H_CAP; None if none does"""
    for w in list(range(css_w, max(css_w, w_max), 4)) + [max(css_w, w_max)]:
        pg.set_viewport_size({"width": w, "height": 100}); pg.set_content(html_for(n, w, W_OUT / w))
        if pg.evaluate("document.documentElement.scrollHeight") * W_OUT / w <= H_CAP + 0.5: return w
    return None

def render(br, n, css_w):
    s = W_OUT / css_w
    pg = br.new_page(viewport={"width": css_w, "height": 100}, device_scale_factor=s)
    try:
        pg.set_content(html_for(n, css_w, s)); pg.wait_for_timeout(60); rc.check(pg, n)
        hd = pg.evaluate(JS_HDR)
        full_h = pg.evaluate("document.documentElement.scrollHeight")
        cut = None
        if full_h * s > H_CAP + 0.5:
            lines = pg.evaluate(JS_LINES)
            pre_h = pg.evaluate("document.querySelector('.pre').getBoundingClientRect().height")
            chrome = full_h - pre_h                     # everything that is not the post text
            room = H_CAP / s - chrome
            fit = [b for b in lines if b <= room + 0.01]
            if not fit: raise RuntimeError(f"#{n}: no whole line fits under {H_CAP}px")
            lh = (lines[1] - lines[0]) if len(lines) > 1 else lines[0]
            hpx = fit[-1]
            got = pg.evaluate(JS_CUT, [hpx, min(lh, hpx)])
            while got * s > H_CAP + 0.5 and len(fit) > 1:   # safety: shave a line if rounding pushed it over
                fit.pop(); hpx = fit[-1]; got = pg.evaluate(JS_CUT, [hpx, min(lh, hpx)])
            cut = {"lines_shown": len(fit), "lines_total": len(lines)}
            rc.check(pg, n)                            # full text still in the DOM (only visually clipped)
        png = pg.screenshot(full_page=True)
    finally:
        pg.close()
    im = Image.open(io.BytesIO(png)).convert("RGB")
    if im.width != W_OUT:                              # sub-pixel rounding only: pad/crop 1 px, never resample
        can = Image.new("RGB", (W_OUT, im.height), rc.BG); can.paste(im.crop((0, 0, min(W_OUT, im.width), im.height)), (0, 0)); im = can
    if im.height > H_CAP: im = im.crop((0, 0, W_OUT, H_CAP))
    return im, {"hdr_over": hd["over"], "hdr_h": round(hd["h"], 1), "cut": cut}

def main(nums, out, measure=False):
    os.makedirs(os.path.join(out, "after"), exist_ok=True)
    rp = os.path.join(out, "measure.json" if measure else "report.json")
    rep = json.load(open(rp)) if (measure and os.path.exists(rp)) else {}
    t0 = time.time()
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page()
        for i, n in enumerate(nums):
            if measure and str(n) in rep: continue
            try:
                need, css_w = pick_width(pg, n)
                w_fit = fit_width(pg, n, css_w)
                if w_fit is not None: css_w = w_fit
                r = {"hdr_need": need, "css_w": css_w, "zoom": round(600 / css_w, 3), "hdr_wrap": need > W_HARD,
                     "fits_whole": w_fit is not None}
                if measure:
                    pg.set_viewport_size({"width": css_w, "height": 100}); pg.set_content(html_for(n, css_w, 2))
                    r["h_out"] = min(H_CAP, round(pg.evaluate("document.documentElement.scrollHeight") * W_OUT / css_w))
                else:
                    try: im, info = render(br, n, css_w)
                    except RuntimeError:            # header + file thumbnails leave no room for a text line at this
                        im = None                   # zoom: step wider (smaller) only until some lines fit (keeps text big;
                        for w in range(max(css_w, W_FIT), W_HARD + 1, 20):   # the rest is cut + faded as usual)
                            try: im, info = render(br, n, w); css_w = w; break
                            except RuntimeError: continue
                        if im is None: raise
                        r.update(css_w=css_w, zoom=round(600 / css_w, 3), fits_whole=info["cut"] is None)
                    r.update(info, w=im.width, h=im.height)
                    im.save(os.path.join(out, "after", f"{n}.jpg"), "JPEG", quality=88, optimize=True, progressive=True)
            except Exception as e:
                r = {"error": str(e)}
            rep[str(n)] = r
            if not measure: print(n, r, flush=True)
            elif i % 250 == 0: print(f"{i+1}/{len(nums)} {time.time()-t0:.0f}s", flush=True); json.dump(rep, open(rp, "w"))
        br.close()
    json.dump(rep, open(rp, "w"), indent=None if measure else 1)

if __name__ == "__main__":
    a = sys.argv[1:]; out = os.path.join(rc.ROOT, ".work", "drop-cards-rightsized")
    if "--out" in a: i = a.index("--out"); out = a[i + 1]; del a[i:i + 2]
    measure = "--measure" in a
    if measure: a.remove("--measure")
    nums = sorted(rc.DROPS) if ("--all" in a or (measure and not [x for x in a if x.isdigit()])) else [int(x) for x in a if x.isdigit()]
    main(nums, out, measure)
