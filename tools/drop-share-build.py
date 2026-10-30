#!/usr/bin/env python3
"""Build the static share pages for Q drops (same pattern as tools/meme-share-build.py).

Reads data/drops.js and the card manifest written by tools/drop-cards/render_cards.py and writes:
  drops/share/<N>.html  OG/Twitter tags (preview = R2 drops/og2/N.jpg: right-sized card, 1200 wide, height per
                        drop from tools/drop-cards/og2-sizes.json; old 1200x630 drops/og/ kept in R2 for rollback), canonical /drops/N/,
                        noindex; humans are sent on to /ledger.html#drop-N with the utm query kept.
  data/drop-cards.js    {base, long:[...], v2base, v2:[...]}: which drops have a 1080x1350 ig/ crop, and which drops'
                        images live under the v2/ prefix (cards with the real attached images, 2026-10-27).
Drops listed in tools/drop-cards/cards-v2.json (written by tools/drop-cards/cards_v2.py) use R2 drops/v2/{card,og,og2,ig}/
(new keys, so the immutable 1-year cache on the old keys does not matter); their og:image:height and long flag come from it.
Only drops present in the manifest get a page, so a page never points at an image not yet uploaded.

Usage: python3 tools/drop-share-build.py [--manifest .work/drop-cards/manifest.json]
"""
import html, json, os, sys
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://therubberduck.net'
MEDIA = 'https://memes.therubberduck.net/drops/'
OUT = os.path.join(ROOT, 'drops', 'share')
ET = ZoneInfo('America/New_York')
OG_DIR = 'og2'   # right-sized previews (tools/drop-cards/rightsize.py, 2026-10-26); 'og' = the old 1200x630 ones
_SZ = os.path.join(ROOT, 'tools', 'drop-cards', 'og2-sizes.json')
OG_H = {int(k): v for k, v in json.load(open(_SZ)).items()} if os.path.exists(_SZ) else {}
_V2 = os.path.join(ROOT, 'tools', 'drop-cards', 'cards-v2.json')
V2 = json.load(open(_V2)) if os.path.exists(_V2) else {'prefix': 'v2/', 'drops': {}}
V2D = {int(k): v for k, v in V2['drops'].items()}
esc = lambda s: html.escape(s or '', quote=True)


def tease(n, dt, site, board):
    return 'Q drop #%d \u00b7 %s' % (n, dt.strftime('%B %-d, %Y'))   # no board credit (Mike, 2026-10-30)


def page(d):
    n, ts, site, board, _url, text = d
    dt = datetime.fromtimestamp(ts, ET)
    when = dt.strftime('%B %-d, %Y')
    title = 'Q Drop #%d, %s | The Drop Ledger | The Rubber Duck\u2122' % (n, when)
    desc = tease(n, dt, site, board)   # tease only (Mike, 2026-10-25): no drop text in previews
    img = MEDIA + (V2['prefix'] if n in V2D else '') + '%s/%d.jpg' % (OG_DIR, n)
    alt = 'Q drop #%d as originally posted, %s' % (n, when)   # no board credit (Mike, 2026-10-30)
    dest = '/ledger.html#drop-%d' % n
    return '''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>{t}</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex, follow">
<link rel="canonical" href="{canon}">
<meta name="description" content="{d}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="The Rubber Duck&trade;">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:url" content="{u}">
<meta property="og:image" content="{i}">
<meta property="og:image:secure_url" content="{i}">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="{h}">
<meta property="og:image:alt" content="{a}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@TheRubberDuck79">
<meta name="twitter:title" content="{t}">
<meta name="twitter:description" content="{d}">
<meta name="twitter:image" content="{i}">
<meta name="twitter:image:alt" content="{a}">
<link rel="icon" href="/favicon-duck-white.ico" sizes="any">
<meta http-equiv="refresh" content="0; url={dest}">
<script>location.replace("/ledger.html"+location.search+"#drop-{n}");</script>
<style>body{{margin:0;background:#040705;color:#C8F5D2;font:16px/1.5 system-ui,sans-serif;display:grid;place-items:center;min-height:100vh}}a{{color:#00FF41}}</style>
</head><body><p>Opening Q drop #{n} in <a href="{dest}">The Drop Ledger</a>.</p></body></html>
'''.format(t=esc(title), d=esc(desc), u=esc('%s/drops/share/%d.html' % (SITE, n)), canon=esc('%s/drops/%d/' % (SITE, n)),
           i=esc(img), a=esc(alt), dest=esc(dest), n=n, h=V2D[n]['og2_h'] if n in V2D else OG_H.get(n, 630))


def drop_cards_js(ns, man):
    longs = [n for n in ns if (V2D[n]['long'] if n in V2D else man[str(n)]['long'])]
    v2 = sorted(n for n in V2D if n in set(ns))
    return ('/* written by tools/drop-share-build.py: drop share images on R2 (trd-memes, drops/ prefix; drops in v2 use drops/v2/) */\n'
            'window.TRD_DROP_CARDS={base:%s,long:%s,v2base:%s,v2:%s};\n' % (json.dumps(MEDIA), json.dumps(longs, separators=(',', ':')),
            json.dumps(MEDIA + V2['prefix']), json.dumps(v2, separators=(',', ':'))))


def main():
    a = sys.argv[1:]
    mp = a[a.index('--manifest') + 1] if '--manifest' in a else os.path.join(ROOT, '.work', 'drop-cards', 'manifest.json')
    man = json.load(open(mp))
    raw = open(os.path.join(ROOT, 'data', 'drops.js'), encoding='utf-8').read().strip()
    drops = {d[0]: d for d in json.loads(raw[raw.index('['):raw.rstrip(';').rindex(']') + 1])}
    os.makedirs(OUT, exist_ok=True)
    ns = sorted(int(k) for k in man if int(k) in drops)
    for n in ns:
        open(os.path.join(OUT, '%d.html' % n), 'w', encoding='utf-8').write(page(drops[n]))
    open(os.path.join(ROOT, 'data', 'drop-cards.js'), 'w').write(drop_cards_js(ns, man))
    print('share pages: %d  long (ig crop): %d' % (len(ns), len(longs)))


if __name__ == '__main__':
    sys.exit(main())
