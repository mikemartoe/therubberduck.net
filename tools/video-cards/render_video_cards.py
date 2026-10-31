#!/usr/bin/env python3
"""Video Room share cards: one 1200x630 link-preview image per Video Room feature (2026-10-30, preview).

Same family as the Q-drop cards (tools/drop-cards/render_cards.py): the video's own poster frame large on the left
with a play mark and its running time, the title sized to fill the right column, the duck + therubberduck.net
underneath. No board names, no credits, no emojis.

Features come from tools/video-share-build.py (the same list the room and the share pages use).
Output (default OUT = <repo>/.work/video-cards, git-ignored): <id>.jpg  -> upload to R2 trd-memes under
video-room/og/<id>.jpg (served at https://memes.therubberduck.net/video-room/og/<id>.jpg).

Usage:  python3 tools/video-cards/render_video_cards.py            # all features
        python3 tools/video-cards/render_video_cards.py v416nbw ...  # some
        python3 tools/video-cards/render_video_cards.py --out DIR
"""
import base64, html, importlib.util, os, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
spec = importlib.util.spec_from_file_location('vsb', os.path.join(ROOT, 'tools', 'video-share-build.py'))
vsb = importlib.util.module_from_spec(spec); spec.loader.exec_module(vsb)


def b64(path, mime):
    return 'data:%s;base64,%s' % (mime, base64.b64encode(open(path, 'rb').read()).decode())


FONT = b64(os.path.join(ROOT, 'assets/trd/fonts/Oswald-VariableFont_wght.ttf'), 'font/ttf')
DUCK = b64(os.path.join(ROOT, 'images/brand/duck-hero-soft.png'), 'image/png')
INTERMISSION = b64(os.path.join(ROOT, 'assets/trd/clips/intermission-card.jpg'), 'image/jpeg')


def poster(v):
    th = (v.get('th') or '').strip()
    if not th.startswith('http') or 'intermission-card' in th:
        return INTERMISSION
    return th


def card_html(v):
    e = lambda s: html.escape(s, quote=True)
    t = ' '.join(v['t'].split())
    dur = v.get('dur') or ''
    kind = 'Livestream' if v.get('live') else ('Double feature' if v.get('reels') else 'Now showing')
    img = poster(v)
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:'Oswald';src:url('{FONT}') format('truetype');font-weight:200 700}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:1200px;height:630px;overflow:hidden;background:#04060d}}
.bg{{position:absolute;inset:-40px;background:url('{img}') center/cover;filter:blur(36px) brightness(.32) saturate(1.2)}}
.card{{position:absolute;inset:0;display:grid;grid-template-columns:784px 1fr;gap:34px;padding:36px;font-family:'Oswald',sans-serif;color:#f3e6c8}}
.left{{display:grid;grid-template-rows:441px 1fr;gap:22px}}
.thumb{{position:relative;border-radius:8px;overflow:hidden;background:#000;box-shadow:0 0 0 3px #ffc864,0 18px 40px rgba(0,0,0,.6)}}
.thumb img{{width:100%;height:100%;object-fit:cover;display:block}}
.play{{position:absolute;left:50%;top:50%;width:118px;height:118px;margin:-59px 0 0 -59px;border-radius:50%;background:rgba(4,6,13,.72);box-shadow:0 0 0 4px #ffe2a0}}
.play:after{{content:"";position:absolute;left:46px;top:33px;border-left:42px solid #ffe2a0;border-top:26px solid transparent;border-bottom:26px solid transparent}}
.dur{{position:absolute;right:14px;bottom:14px;background:rgba(0,0,0,.85);color:#ffe2a0;font-weight:600;font-size:30px;line-height:1;padding:8px 14px 9px;border-radius:4px;letter-spacing:.04em}}
.brand{{display:flex;align-items:center;gap:18px}}
.brand img{{height:96px;width:auto}}
.brand b{{font-weight:600;font-size:52px;letter-spacing:.02em;color:#ffe2a0;line-height:1}}
.right{{display:grid;grid-template-rows:auto minmax(0,1fr) auto;gap:18px;min-width:0;min-height:0;height:558px}}
.kick{{font-weight:700;font-size:26px;letter-spacing:.2em;text-transform:uppercase;color:#ff5b45;line-height:1.1;border-bottom:3px solid rgba(255,200,100,.55);padding-bottom:14px}}
.tbox{{position:relative;min-height:0;overflow:hidden;display:flex;align-items:center}}
.title{{font-weight:600;line-height:1.12;color:#f3e6c8;overflow-wrap:normal;hyphens:none;width:100%}}
.foot{{font-weight:500;font-size:26px;letter-spacing:.12em;text-transform:uppercase;color:#ffc864;line-height:1.2;border-top:3px solid rgba(255,200,100,.55);padding-top:14px}}
</style></head><body><div class="bg"></div><div class="card">
<div class="left"><div class="thumb"><img id="im" src="{e(img)}" alt=""><span class="play"></span>{('<span class="dur">' + e(dur) + '</span>') if dur else ''}</div>
<div class="brand"><img src="{DUCK}" alt=""><b>therubberduck.net</b></div></div>
<div class="right"><div class="kick">{e(kind)}</div><div class="tbox" id="tb"><div class="title" id="tt">{e(t)}</div></div><div class="foot">Free in the<br>Video Room</div></div>
</div><script>
(function(){{var tb=document.getElementById('tb'),tt=document.getElementById('tt'),lo=24,hi=84;
while(hi-lo>1){{var m=(lo+hi)>>1;tt.style.fontSize=m+'px';(tt.scrollHeight<=tb.clientHeight&&tt.scrollWidth<=tt.clientWidth+1)?lo=m:hi=m;}}
tt.style.fontSize=lo+'px';}})();
</script></body></html>"""


def main():
    args = sys.argv[1:]
    out = os.path.join(ROOT, '.work', 'video-cards')
    if '--out' in args:
        i = args.index('--out'); out = args[i + 1]; del args[i:i + 2]
    os.makedirs(out, exist_ok=True)
    feats = vsb.load_features()[0]
    if args:
        feats = [v for v in feats if v['id'] in args]
    bad = []
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={'width': 1200, 'height': 630})
        for n, v in enumerate(feats, 1):
            pg.set_content(card_html(v), wait_until='load', timeout=60000)
            pg.evaluate('document.fonts.ready')
            ok = pg.evaluate("(()=>{const i=document.getElementById('im');return i.complete&&i.naturalWidth>0})()")
            if not ok:   # poster did not load: use the room's intermission card rather than a black box
                pg.set_content(card_html(dict(v, th='')), wait_until='load'); bad.append(v['id'])
            pg.screenshot(path=os.path.join(out, v['id'] + '.jpg'), type='jpeg', quality=86)
            if n % 25 == 0:
                print(n, 'cards', flush=True)
        br.close()
    print('rendered %d cards to %s; poster missing (intermission card used): %s' % (len(feats), out, ', '.join(bad) or 'none'))


if __name__ == '__main__':
    main()
