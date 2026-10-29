#!/usr/bin/env python3
"""Build the header search index for therubberduck.net.

Writes /assets/search/site-index.json: one small row per page in the archive
(rooms, Q drops, PDFs, videos, recordings, store items, the book and every meme).
X posts are searched by the X Archive's own static index (/x/data/), so the
header links straight into it with the query filled in.

Run from the repo root after adding pages:  python3 tools/site-search-build.py
"""
import html, json, os, re, glob, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
TYPES = ['Room', 'Q drop', 'PDF', 'Video', 'Recording', 'Collectible', 'Book', 'Meme']
rows = []
def clean(s, n=None):
    s = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s or ''))).strip()
    if n and len(s) > n: s = s[:n].rsplit(' ', 1)[0] + '…'
    return s
def page(path):
    s = open(path, encoding='utf-8', errors='replace').read()
    t = re.search(r'<title>(.*?)</title>', s, re.S)
    d = re.search(r'<meta name="description" content="(.*?)"', s, re.S)
    t = clean(t.group(1)) if t else ''
    t = re.sub(r'\s*\|\s*(The Rubber Duck™|The Rubber Duck&trade;|TRD Collectibles).*$', '', t)
    return t, clean(d.group(1), 220) if d else ''
ROOMS = [('index.html', '/', 'Home'), ('videos.html', '/videos.html', 'Private Theater (videos)'),
         ('listening-room.html', '/listening-room.html', 'The Listening Room (recordings)'),
         ('pdfs.html', '/pdfs.html', 'SCIF Reading Room (PDFs)'), ('ledger.html', '/ledger.html', 'The Drop Ledger (every Q drop)'),
         ('memes.html', '/memes.html', 'The Meme Dump'), ('x/index.html', '/x/', 'X Archive'),
         ('album.html', '/album.html', 'The Red Pill Album'), ('merch.html', '/merch.html', 'TRD Collectibles (store)'),
         ('sponsor.html', '/sponsor.html', 'Sponsor the Site'), ('Qdrops/index.html', '/Qdrops/', 'Q drops by month')]
FROZEN = {'ledger.html': 'Every Q drop, dated and searchable.',      # frozen pages: never opened by this script
          'album.html': 'The Red Pill Album by The Rubber Duck: 22 tracks, play it right here.'}
for f, u, name in ROOMS:
    if f in FROZEN: rows.append([0, name, u, FROZEN[f]])
    elif os.path.exists(f):
        t, d = page(f); rows.append([0, name, u, d])
def section(folder, ti):
    for f in sorted(glob.glob(folder + '/*/index.html')):
        t, d = page(f); rows.append([ti, t, '/' + os.path.dirname(f) + '/', d])
def num(f):
    m = re.search(r'/(\d+)/index\.html$', f); return int(m.group(1)) if m else 0
for f in sorted(glob.glob('drops/*/index.html'), key=num):
    if not num(f): continue
    t, d = page(f); rows.append([1, re.sub(r':\s*Full Text$', '', t), '/' + os.path.dirname(f) + '/', d])
section('library', 2); section('watch', 3); section('listen', 4); section('shop', 5); section('book', 6)
m = json.load(open('memes/data/memes.json', encoding='utf-8'))
for it in m['items']:
    tags = ' '.join(x for x in (it.get('topics') or []) if x != 'text-in-image')
    rows.append([7, it.get('title') or it['id'], '/memes/share/' + it['id'] + '.html', tags])
meta = json.load(open('x/data/meta.json'))
out = {'v': 1, 'built': datetime.date.today().isoformat(), 'types': TYPES, 'xPosts': meta['n'], 'rows': rows}
os.makedirs('assets/search', exist_ok=True)
with open('assets/search/site-index.json', 'w', encoding='utf-8') as fh:
    json.dump(out, fh, ensure_ascii=False, separators=(',', ':'))
print(len(rows), 'rows;', os.path.getsize('assets/search/site-index.json') // 1024, 'KB;', meta['n'], 'X posts via /x/')
