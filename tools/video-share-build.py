#!/usr/bin/env python3
"""Video Room share pages: writes videos/share/<id>.html for every feature in the Video Room.

Ids and titles come from the same two sources the room uses:
  - the ALL list inside videos.html (Rumble features + reposts)
  - data/video-room-local.json (file-hosted local-archive reels)

Each page is a real preview page (2026-10-30, preview for Mike): the poster frame (tap to play it in the room),
title, date and running time, the feature's own notes (filename guesses are never shown), Watch in the Video Room,
the compact share row (assets/trd/share.js, same as under each drop), and three more features. og/twitter tags use the
feature's 1200x630 card (tools/video-cards/render_video_cards.py, R2 video-room/og/<id>.jpg). No page ever
references the video file itself in a tag a link preview loads. Writes sitemaps/video-share.xml and its
sitemap.xml index entry.

Usage:
  python3 tools/video-share-build.py                    # 1200x630 cards on R2 as the preview image (default)
  python3 tools/video-share-build.py --cards-base URL   # cards from another base URL/<id>.jpg
  python3 tools/video-share-build.py --poster           # poster/thumbnail as the preview image
  python3 tools/video-share-build.py --img-meta FILE    # JSON {url:{w,h}} to emit og:image:width/height
"""
import argparse, html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://therubberduck.net'
FALLBACK_IMG = SITE + '/images/brand/trd-share-2026.jpg'   # 1200x630 brand card, for reels with no real poster
ID_RE = re.compile(r'^[a-z0-9]+$', re.I)                     # the room's #v= parser only accepts these


def load_features():
    src = open(os.path.join(ROOT, 'videos.html'), encoding='utf-8').read()
    m = re.search(r'const ALL = (\[.*?\]);\n', src)
    if not m:
        sys.exit('ALL list not found in videos.html')
    rumble = json.loads(m.group(1))
    local = json.load(open(os.path.join(ROOT, 'data', 'video-room-local.json'), encoding='utf-8'))
    # Double features (one card playing several files back to back): the card's id and the old per-file ids
    # all share the double feature's own title and total running time, as the room shows them.
    dfs = {}
    blk = re.search(r'const DOUBLE_FEATURES = \[(.*?)\n\];', src, re.S)
    for d in re.finditer(r"\{id: '(\w+)', t: '([^']+)'.*?reels: \[(.*?)\]\}", blk.group(1) if blk else '', re.S):
        secs = sum(float(x) for x in re.findall(r'secs: ([\d.]+)', d.group(3)))
        t = int(round(secs)); dur = '%d:%02d:%02d' % (t // 3600, t % 3600 // 60, t % 60) if t >= 3600 else '%d:%02d' % (t // 60, t % 60)
        for rid in re.findall(r"id: '(\w+)'", d.group(3)):
            dfs[rid] = {'t': d.group(2), 'dur': dur if secs else None}
    local = [dict(v, t=dfs[v['id']]['t'], dur=dfs[v['id']]['dur'] or v.get('dur')) if v['id'] in dfs else v for v in local]
    out, seen, dups = [], set(), []
    for v in rumble + local:
        if v['id'] in seen:      # same Rumble video listed as a feature and as a repost: one page (same id, same title)
            dups.append(v['id'])
            continue
        if not ID_RE.match(v['id']):
            sys.exit('id the room cannot deep-link: ' + v['id'])
        seen.add(v['id'])
        out.append(v)
    return out, len(rumble), len(local), dups


CARDS_BASE = 'https://memes.therubberduck.net/video-room/og'   # 1200x630 cards (tools/video-cards/render_video_cards.py)
ET = None


def preview_img(v, cards_base):
    if cards_base:
        return cards_base.rstrip('/') + '/' + v['id'] + '.jpg'
    th = (v.get('th') or '').strip()
    if not th.startswith('http') or 'intermission-card' in th:
        return FALLBACK_IMG
    return th


def poster(v):
    th = (v.get('th') or '').strip()
    if not th or 'intermission-card' in th:
        return '/assets/trd/clips/intermission-card.jpg'
    return th


def clip(s, n):
    s = re.sub(r'\s+', ' ', str(s or '')).strip()
    if len(s) <= n:
        return s
    return s[:n - 1].rsplit(' ', 1)[0].rstrip(' ,.;:-') + '\u2026'


def notes(v):
    """The feature's own notes, unless they are the archive's filename guesses (not public text)."""
    d = (v.get('desc') or '').strip()
    if not d or d.startswith('From filename'):
        return ''
    return d


def when(v):
    if v.get('source') == 'local' or not v.get('ts'):
        return ''
    import datetime
    from zoneinfo import ZoneInfo
    return datetime.datetime.fromtimestamp(int(v['ts']), ZoneInfo('America/New_York')).strftime('%B %-d, %Y')


def iso_dur(s):
    p = [int(x) for x in re.findall(r'\d+', s or '')]
    if not p:
        return None
    while len(p) < 3:
        p.insert(0, 0)
    h, m, sec = p[-3:]
    return 'PT%dH%dM%dS' % (h, m, sec) if h else 'PT%dM%dS' % (m, sec)


CSS = """@font-face{font-family:'Oswald';src:url('/assets/trd/fonts/Oswald-VariableFont_wght.woff2') format('woff2');font-weight:200 700;font-display:swap}
:root{--night:#04060d;--cream:#f3e6c8;--amber:#ffc864;--bulb:#ffe2a0;--red:#c8321f;--neon:#ff5b45;
--border:rgba(255,200,100,.45);--surface-1:rgba(20,10,6,.6);--text:var(--bulb);--accent:var(--amber);--muted:#cbb994;--font-body:'Oswald',sans-serif}
*{box-sizing:border-box}
html{background:#04060d}
body{margin:0;background:#04060d radial-gradient(ellipse at 50% 0,#1b1430 0,#04060d 900px) no-repeat;min-height:100vh;color:var(--cream);font:17px/1.55 system-ui,-apple-system,'Segoe UI',sans-serif}
a{color:var(--amber)}
.top,.vp,.more,.foot{max-width:1160px;margin:0 auto;padding:0 24px}
.top{display:flex;justify-content:space-between;align-items:center;gap:16px;padding-top:18px;padding-bottom:18px;font-family:'Oswald',sans-serif;text-transform:uppercase;letter-spacing:.16em;font-size:15px}
.top a{text-decoration:none;color:var(--bulb)}.top b{font-weight:600}
.vp{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(0,1fr);gap:34px;align-items:center;padding-top:10px;padding-bottom:34px}
.poster{position:relative;display:block;aspect-ratio:16/9;border-radius:8px;overflow:hidden;background:#000;box-shadow:0 0 0 3px var(--amber),0 18px 40px rgba(0,0,0,.6)}
.poster img{width:100%;height:100%;object-fit:cover;display:block}
.play{position:absolute;left:50%;top:50%;width:84px;height:84px;margin:-42px 0 0 -42px;border-radius:50%;background:rgba(4,6,13,.72);box-shadow:0 0 0 3px var(--bulb);transition:transform .15s}
.play:after{content:"";position:absolute;left:33px;top:24px;border-left:30px solid var(--bulb);border-top:18px solid transparent;border-bottom:18px solid transparent}
.poster:hover .play,.poster:focus-visible .play{transform:scale(1.08)}
.dur{position:absolute;right:10px;bottom:10px;background:rgba(0,0,0,.85);color:var(--bulb);font:600 17px/1 'Oswald',sans-serif;padding:6px 10px;border-radius:3px;letter-spacing:.04em}
.kick{margin:0 0 8px;font:700 15px/1.2 'Oswald',sans-serif;letter-spacing:.22em;text-transform:uppercase;color:var(--neon)}
h1{margin:0 0 10px;font:600 clamp(30px,3.4vw,44px)/1.12 'Oswald',sans-serif;color:var(--cream)}
.meta{margin:0 0 14px;font:500 16px/1.3 'Oswald',sans-serif;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.desc{margin:0 0 20px;font-size:17px;color:#e8dcc0}
.acts{display:flex;flex-wrap:wrap;gap:10px;margin:0 0 6px}
.btn{display:inline-flex;align-items:center;justify-content:center;min-height:46px;padding:0 16px;border-radius:4px;background:var(--amber);color:#1c130c;text-decoration:none;font:600 16px/1 'Oswald',sans-serif;letter-spacing:.08em;flex:1 1 auto;white-space:nowrap;text-transform:uppercase}
.btn.alt{background:none;color:var(--bulb);box-shadow:inset 0 0 0 2px var(--border)}
.btn:hover,.btn:focus-visible{filter:brightness(1.08)}
.shr.shr-compact{margin-top:16px}
.more{padding-bottom:34px}
.more h2{margin:0 0 16px;font:700 16px/1.2 'Oswald',sans-serif;letter-spacing:.22em;text-transform:uppercase;color:var(--bulb);border-top:2px dashed rgba(255,200,100,.35);padding-top:22px}
.more ul{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px}
.more a{display:block;text-decoration:none;color:var(--cream)}
.more .th{position:relative;display:block;aspect-ratio:16/9;border-radius:5px;overflow:hidden;background:#000;box-shadow:0 0 0 2px rgba(255,200,100,.5)}
.more img{width:100%;height:100%;object-fit:cover;display:block}
.more .th i{position:absolute;right:6px;bottom:6px;background:rgba(0,0,0,.85);color:var(--bulb);font:600 13px/1 'Oswald',sans-serif;font-style:normal;padding:4px 7px;border-radius:3px}
.more b{display:block;margin-top:9px;font:600 18px/1.25 'Oswald',sans-serif;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.foot{padding-bottom:30px;text-align:center;color:var(--muted);font:500 14px/1.6 'Oswald',sans-serif;letter-spacing:.12em;text-transform:uppercase}
.foot a{color:var(--bulb);text-decoration:none}
@media (max-width:820px){
.vp{grid-template-columns:minmax(0,1fr);gap:20px}
.top,.vp,.more,.foot{padding-left:16px;padding-right:16px}
.top{font-size:13px;letter-spacing:.12em}
.more ul{grid-template-columns:minmax(0,1fr);gap:14px}
.more a{display:grid;grid-template-columns:44% 1fr;gap:12px;align-items:center}
.more b{margin:0;font-size:17px;-webkit-line-clamp:3}
.shr.shr-compact{justify-content:space-between}
}"""


def page(v, img, meta, others):
    e = lambda s: html.escape(s, quote=True)
    vid, t = v['id'], re.sub(r'\s+', ' ', v['t']).strip()
    title = t + ' \u00b7 Video Room \u00b7 The Rubber Duck'
    n = notes(v)
    date = when(v)
    bits = [b for b in [date, ('Running time ' + v['dur']) if v.get('dur') else ''] if b]
    lead = ' \u00b7 '.join(bits)
    desc = clip(n, 200) if n else ((lead + '. ') if lead else '') + 'Free to watch in the Video Room at therubberduck.net.'
    shown = clip(n, 420) if n else ('Free to watch in The Rubber Duck Video Room. Tap the poster to play it on the big screen.')
    url = SITE + '/videos/share/' + vid + '.html'
    room = '/videos.html#v=' + vid
    m = meta.get(img)
    w, h = (m['w'], m['h']) if m and m.get('w') else ((1200, 630) if '/video-room/og/' in img else (0, 0))
    size = ('<meta property="og:image:width" content="%d">\n<meta property="og:image:height" content="%d">\n' % (w, h)) if w else ''
    alt = 'Video Room card for ' + t + ': poster frame, title and running time'
    kick = 'Livestream' if v.get('live') else 'Now showing'
    src = v.get('u') or ''
    alt_btn = ('<a class="btn alt" href="%s" target="_blank" rel="noopener">Watch on Rumble</a>' % e(src)) if 'rumble.com' in src else ''
    ld = {'@context': 'https://schema.org', '@type': 'VideoObject', 'name': t, 'description': n or desc, 'url': url,
          'thumbnailUrl': [img, poster(v) if poster(v).startswith('http') else SITE + poster(v)],
          'isAccessibleForFree': True, 'publisher': {'@type': 'Organization', 'name': 'The Rubber Duck', 'url': SITE + '/'}}
    if v.get('ts'):
        import datetime
        ld['uploadDate'] = datetime.datetime.fromtimestamp(int(v['ts']), datetime.timezone.utc).isoformat()
    if v.get('e'):
        ld['embedUrl'] = v['e']
    if v.get('mediaUrl'):
        ld['contentUrl'] = v['mediaUrl']
    if iso_dur(v.get('dur')):
        ld['duration'] = iso_dur(v.get('dur'))
    more = ''.join('<li><a href="/videos/share/%s.html"><span class="th"><img src="%s" alt="" decoding="async">%s</span><b>%s</b></a></li>'
                   % (o['id'], e(poster(o)), ('<i>%s</i>' % e(o['dur'])) if o.get('dur') else '', e(re.sub(r'\s+', ' ', o['t']).strip())) for o in others)
    share = ('{kind:"video",id:%s,page:%s,text:%s,fileName:%s,compact:true,only:["x","truth","fb","email","sms","link"],groupLabel:%s}'
             % (json.dumps(vid), json.dumps(url), json.dumps(t + ' \u00b7 Video Room \u00b7 The Rubber Duck'), json.dumps('trd-video-' + vid + '.jpg'), json.dumps('Share ' + t)))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>{e(title)}</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="index, follow, max-image-preview:large">
<link rel="canonical" href="{url}">
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="#04060d">
<meta property="og:type" content="video.other">
<meta property="og:site_name" content="The Rubber Duck&trade;">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{e(img)}">
<meta property="og:image:secure_url" content="{e(img)}">
<meta property="og:image:type" content="image/jpeg">
{size}<meta property="og:image:alt" content="{e(alt)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@TheRubberDuck79">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{e(img)}">
<meta name="twitter:image:alt" content="{e(alt)}">
<link rel="icon" href="/favicon-duck-white.ico" sizes="any"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="stylesheet" href="/assets/trd/share.css?v=20261030c" data-trd-keep>
<style>{CSS}</style>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False).replace('</', '<\\/')}</script>
<script data-goatcounter="https://therubberduck.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
<script src="/assets/trd/track.js" data-trd-keep></script>
</head><body>
<header class="top"><a href="/"><b>The Rubber Duck&trade;</b></a><a href="/videos.html">Video Room</a></header>
<main>
<article class="vp">
<a class="poster" href="{room}" aria-label="Play {e(t)} in the Video Room"><img src="{e(poster(v))}" alt="Poster frame from {e(t)}" width="1280" height="720" decoding="async"><span class="play"></span>{('<span class="dur">' + e(v['dur']) + '</span>') if v.get('dur') else ''}</a>
<div class="info">
<p class="kick">{kick}</p>
<h1>{e(t)}</h1>
{('<p class="meta">' + e(lead) + '</p>') if lead else ''}
<p class="desc">{e(shown)}</p>
<div class="acts"><a class="btn" href="{room}">Watch in the Video Room</a>{alt_btn}</div>
<div id="shr"></div>
</div>
</article>
<section class="more" aria-labelledby="mh"><h2 id="mh">More in the Video Room</h2><ul>{more}</ul></section>
</main>
<footer class="foot"><a href="/">therubberduck.net</a> &middot; <a href="/videos.html">Video Room</a> &middot; <a href="https://x.com/TheRubberDuck79" rel="me">@TheRubberDuck79</a></footer>
<script src="/assets/trd/share.js?v=20261030c" data-trd-keep></script>
<script>if(window.trdShare)document.getElementById('shr').appendChild(trdShare.build({share}));</script>
</body></html>
"""


def sitemap(feats):
    import datetime
    lm = datetime.date.today().isoformat()
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
    for v in feats:
        img = html.escape(CARDS_BASE + '/' + v['id'] + '.jpg')
        out.append('  <url><loc>%s/videos/share/%s.html</loc><lastmod>%s</lastmod><image:image><image:loc>%s</image:loc></image:image></url>' % (SITE, v['id'], lm, img))
    open(os.path.join(ROOT, 'sitemaps', 'video-share.xml'), 'w', encoding='utf-8').write('\n'.join(out + ['</urlset>\n']))
    p = os.path.join(ROOT, 'sitemap.xml')
    idx = open(p, encoding='utf-8').read()
    idx = re.sub(r'\n  <sitemap><loc>[^<]*/sitemaps/video-share\.xml</loc>.*?</sitemap>', '', idx)
    idx = idx.replace('</sitemapindex>', '  <sitemap><loc>%s/sitemaps/video-share.xml</loc><lastmod>%s</lastmod></sitemap>\n</sitemapindex>' % (SITE, lm))
    open(p, 'w', encoding='utf-8').write(idx)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cards-base', default=CARDS_BASE)
    ap.add_argument('--poster', action='store_true', help='use the poster frame instead of the 1200x630 card')
    ap.add_argument('--img-meta', default='')
    a = ap.parse_args()
    meta = json.load(open(a.img_meta)) if a.img_meta else {}
    feats, nr, nl, dups = load_features()
    outdir = os.path.join(ROOT, 'videos', 'share')
    os.makedirs(outdir, exist_ok=True)
    keep = set()
    base = '' if a.poster else a.cards_base
    for i, v in enumerate(feats):
        fn = v['id'] + '.html'
        keep.add(fn)
        others = [feats[(i + k) % len(feats)] for k in (1, 2, 3)]
        with open(os.path.join(outdir, fn), 'w', encoding='utf-8') as f:
            f.write(page(v, preview_img(v, base), meta, others))
    sitemap(feats)
    stale = [f for f in os.listdir(outdir) if f.endswith('.html') and f not in keep]
    for f in stale:
        os.remove(os.path.join(outdir, f))
    print('wrote %d share pages (%d Rumble list entries incl. reposts, %d local archive; %d ids listed twice: %s); removed %d stale'
          % (len(feats), nr, nl, len(dups), ', '.join(dups), len(stale)))


if __name__ == '__main__':
    main()
