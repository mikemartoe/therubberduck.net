#!/usr/bin/env python3
"""Build the static share pages for Ledger Photos (same pattern as tools/meme-share-build.py).

Writes drops/photo/<n>_<i>.html: OG/Twitter tags with the actual drop photo on R2
(https://memes.therubberduck.net/drops/img/…), noindex; humans are sent on to
/ledger.html?view=photos&img=<n>_<i> with the utm query kept.

Usage: python3 tools/photo-share-build.py
"""
import html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://therubberduck.net'
OUT = os.path.join(ROOT, 'drops', 'photo')
esc = lambda s: html.escape(s or '', quote=True)


def load_js_obj(path, marker=None):
    t = open(path, encoding='utf-8').read()
    if marker and marker in t:
        t = t[t.index(marker) + len(marker):]
    t = t[t.index('{'):t.rstrip().rstrip(';').rindex('}') + 1]
    t = re.sub(r'([{,])([A-Za-z_]\w*|\d+):', r'\1"\2":', t)
    return json.loads(t)


def text_of(tx, mid):
    v = tx.get(mid)
    if v is None:
        return ''
    if isinstance(v, dict):
        return (v.get('alt') or v.get('caption') or '').strip()
    return str(v).strip()


def page(mid, im, base, cap):
    n, i = mid.split('_', 1)
    img = base + im['src']
    w, h = int(im.get('w') or 0), int(im.get('h') or 0)
    ext = (im.get('src') or 'x.webp').rsplit('.', 1)[-1].lower()
    ctype = {'webp': 'image/webp', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
             'png': 'image/png', 'gif': 'image/gif'}.get(ext, 'image/webp')
    title = 'Photo from Q drop #%s | The Drop Ledger | The Rubber Duck™' % n
    if cap:
        desc = cap if len(cap) < 220 else cap[:217].rsplit(' ', 1)[0] + '…'
    else:
        desc = 'A photo from Q drop #%s in The Drop Ledger at The Rubber Duck.' % n
    alt = cap or ('Photo from Q drop #%s' % n)
    dest = '/ledger.html?view=photos&img=%s' % mid
    url = SITE + '/drops/photo/' + mid + '.html'
    dims = ''
    if w and h:
        dims = '<meta property="og:image:width" content="%d">\n<meta property="og:image:height" content="%d">\n' % (w, h)
    return '''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>{t}</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex, follow">
<meta name="description" content="{d}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="The Rubber Duck&trade;">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:url" content="{u}">
<meta property="og:image" content="{i}">
<meta property="og:image:secure_url" content="{i}">
<meta property="og:image:type" content="{ct}">
{dims}<meta property="og:image:alt" content="{a}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@TheRubberDuck79">
<meta name="twitter:title" content="{t}">
<meta name="twitter:description" content="{d}">
<meta name="twitter:image" content="{i}">
<meta name="twitter:image:alt" content="{a}">
<meta http-equiv="refresh" content="0; url={dest}">
<script>location.replace({destjs}+location.search.replace(/^\\?/,"&"));</script>
<style>body{{margin:0;background:#140e09;color:#f6e3b4;font:16px/1.5 system-ui,sans-serif;display:grid;place-items:center;min-height:100vh}}a{{color:#e3a82b}}</style>
</head><body><p>Opening the photo in <a href="{dest}">The Drop Ledger</a>.</p></body></html>
'''.format(t=esc(title), d=esc(desc), u=esc(url), i=esc(img), ct=esc(ctype),
           dims=dims, a=esc(alt), dest=esc(dest), destjs=json.dumps(dest))


def main():
    imgs = load_js_obj(os.path.join(ROOT, 'data', 'drop-images.js'))
    base = imgs.get('base') or 'https://memes.therubberduck.net/drops/img/'
    d = {str(k): v for k, v in imgs['d'].items()}
    tx_path = os.path.join(ROOT, 'data', 'drop-image-text.js')
    tx = {}
    if os.path.exists(tx_path):
        raw = load_js_obj(tx_path)
        tx = {str(k): v for k, v in raw.items()}
    os.makedirs(OUT, exist_ok=True)
    pages, wrote = set(), 0
    for n, arr in d.items():
        for i, im in enumerate(arr, 1):
            mid = '%s_%d' % (n, i)
            out = page(mid, im, base, text_of(tx, mid))
            fp = os.path.join(OUT, mid + '.html')
            if not os.path.exists(fp) or open(fp, encoding='utf-8').read() != out:
                open(fp, 'w', encoding='utf-8').write(out)
                wrote += 1
            pages.add(mid + '.html')
    removed = 0
    for f in os.listdir(OUT):
        if f.endswith('.html') and f not in pages:
            os.remove(os.path.join(OUT, f))
            removed += 1
    print('photo share pages: %d  wrote: %d  removed: %d' % (len(pages), wrote, removed))


if __name__ == '__main__':
    sys.exit(main())
