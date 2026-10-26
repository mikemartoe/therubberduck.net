#!/usr/bin/env python3
"""SEO build for therubberduck.net.

Run from the repo root:  python3 tools/seo-build.py

What it does (idempotent, safe to re-run after any data change):
  1. Generates static, crawlable HTML pages from the data the rooms already use:
       /drops/            Q drops: index, one page per month, one page per drop
       /x/archive/        X archive: index and one page per month (original posts and quotes)
       /library/          SCIF Reading Room: index and one page per PDF
       /watch/            Video Room: index and one page per video (VideoObject)
       /listen/           Listening Room: index and one page per volume
       /shop/<slug>/      one page per TRD Collectibles item (Product, real prices)
                          plus coming-soon pages from tools/premium_soon.py (no prices, no checkout)
       /book/anon-mission/  the book (Book + Product, real Gumroad price)
  2. Injects JSON-LD and invisible head tags into the existing room pages, between
     <!-- seo:begin --> and <!-- seo:end --> markers (nothing in <body> is touched).
  3. Writes sitemap.xml (a sitemap index) plus /sitemaps/*.xml, and robots.txt.
The rooms themselves are not changed visually; the new pages are separate URLs.
"""
import html, json, os, re, subprocess, sys, datetime
from zoneinfo import ZoneInfo
from collections import OrderedDict, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(ROOT)
SITE = 'https://therubberduck.net'
ET = ZoneInfo('America/New_York')
TODAY = datetime.date.today().isoformat()
BRAND = 'The Rubber Duck\u2122'
SHARE = SITE + '/images/brand/trd-share-2026.jpg'
GUMROAD = 'https://rubberduck41.gumroad.com/l/ttmhx'
BOOK_PRICE = '19.99'
SAME_AS = [
    'https://x.com/TheRubberDuck79',
    'https://x.com/TheRubberDuck78',
    'https://rumble.com/user/TheRubberDuck78',
    'https://rubberduck41.gumroad.com/',
    'https://open.spotify.com/album/2zxmpLk7jYsvoEUAKTWbH4',
    'https://music.apple.com/us/album/the-red-pill-album/1896233683',
]
ORG_ID = SITE + '/#org'
SITE_ID = SITE + '/#website'
E = lambda s: html.escape(str(s if s is not None else ''), quote=True)

def write(path, text):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    old = open(path, encoding='utf-8').read() if os.path.exists(path) else None
    if old != text:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)

def clip(s, n=155):
    s = re.sub(r'\s+', ' ', str(s or '')).strip()
    if len(s) <= n: return s
    cut = s[:n - 1].rsplit(' ', 1)[0]
    return cut.rstrip(' ,.;:-') + '\u2026'

def linkify(text):
    out = E(text)
    out = re.sub(r'(https?://[^\s<>"]+)', lambda m: '<a href="%s" rel="nofollow noopener" target="_blank">%s</a>' % (m.group(1), m.group(1)), out)
    return out.replace('\n', '<br>')

def iso_dur(s):
    p = [int(x) for x in re.findall(r'\d+', s or '')]
    if not p: return None
    while len(p) < 3: p.insert(0, 0)
    h, m, sec = p[-3:]
    return 'PT%dH%dM%dS' % (h, m, sec) if h else 'PT%dM%dS' % (m, sec)

def ts_iso(ts):
    return datetime.datetime.fromtimestamp(int(ts), ET).isoformat()

def git_date(path):
    try:
        d = subprocess.check_output(['git', 'log', '-1', '--format=%cs', '--', path], text=True).strip()
        return d or TODAY
    except Exception:
        return TODAY

# ---------------------------------------------------------------- JSON-LD helpers
def org():
    return {'@type': 'Organization', '@id': ORG_ID, 'name': 'The Rubber Duck', 'alternateName': ['TRD', 'The Rubber Duck\u2122', 'TRD Collectibles'],
            'url': SITE + '/', 'logo': {'@type': 'ImageObject', 'url': SITE + '/favicon-192.png', 'width': 192, 'height': 192},
            'image': SHARE, 'description': 'An open archive of Trump and Q-era research: every Q drop, videos, X Spaces, PDFs, memes and the X archive, plus TRD Collectibles and the book anon mission.',
            'sameAs': SAME_AS}

def website():
    return {'@type': 'WebSite', '@id': SITE_ID, 'url': SITE + '/', 'name': 'The Rubber Duck', 'alternateName': ['TRD', 'therubberduck.net'],
            'publisher': {'@id': ORG_ID}, 'inLanguage': 'en',
            'potentialAction': {'@type': 'SearchAction', 'target': {'@type': 'EntryPoint', 'urlTemplate': SITE + '/ledger.html?q={search_term_string}'},
                                'query-input': 'required name=search_term_string'}}

def crumbs(items):
    return {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': SITE + u} for i, (n, u) in enumerate(items)]}

def ld_script(graph):
    data = {'@context': 'https://schema.org', '@graph': graph}
    s = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    s = s.replace('</', '<\\/')
    return '<script type="application/ld+json">' + s + '</script>'

def book_ld():
    return {'@type': ['Book', 'Product'], '@id': SITE + '/book/anon-mission/#book', 'name': 'anon mission, Volume 1',
            'alternateName': 'anon mission or all you need to know about q - and how they made you afraid to ask',
            'description': 'anon mission or all you need to know about q - and how they made you afraid to ask. A polished, printable PDF by The Rubber Duck.',
            'author': {'@id': ORG_ID}, 'publisher': {'@id': ORG_ID}, 'brand': {'@type': 'Brand', 'name': 'The Rubber Duck'},
            'bookFormat': 'https://schema.org/EBook', 'inLanguage': 'en', 'url': SITE + '/book/anon-mission/',
            'image': SITE + '/assets/trd/img/anon-mission-book-face@2x.webp', 'sameAs': GUMROAD,
            'offers': {'@type': 'Offer', 'url': GUMROAD, 'price': BOOK_PRICE, 'priceCurrency': 'USD', 'availability': 'https://schema.org/InStock',
                       'seller': {'@id': ORG_ID}}}

# ---------------------------------------------------------------- page shell for generated pages
CSS_HREF = '/assets/seo/archive.css?v=1'
NAV = [('/', 'Home'), ('/ledger.html', 'Drop Ledger'), ('/videos.html', 'Video Room'), ('/listening-room.html', 'Listening Room'),
       ('/pdfs.html', 'SCIF Reading Room'), ('/x/', 'X Archive'), ('/memes.html', 'Meme Dump'), ('/album.html', 'Red Pill Album')]

DROP_OG = 'https://memes.therubberduck.net/drops/og2/%d.jpg'   # right-sized share cards on R2 (tools/drop-cards/rightsize.py); old 1200x630 in drops/og/


def page(path, title, desc, body, graph, crumb_items, og_image=SHARE, og_type='website', extra_head='', og_desc=None, robots='index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1'):
    url = SITE + path
    full_title = title if title.endswith(BRAND) else title + ' | ' + BRAND
    graph = [{'@type': 'Organization', '@id': ORG_ID, 'name': 'The Rubber Duck', 'url': SITE + '/', 'sameAs': SAME_AS[:3]}, {'@type': 'WebPage', '@id': url + '#page', 'url': url, 'name': full_title, 'description': desc,
                                 'isPartOf': {'@id': SITE_ID}, 'publisher': {'@id': ORG_ID}, 'inLanguage': 'en',
                                 'breadcrumb': {'@id': url + '#crumbs'}}] + graph
    bc = crumbs(crumb_items); bc['@id'] = url + '#crumbs'; graph.append(bc)
    nav = ''.join('<a href="%s">%s</a>' % (u, E(n)) for u, n in NAV)
    crumb_html = ' <span aria-hidden="true">&rsaquo;</span> '.join(
        ('<a href="%s">%s</a>' % (u, E(n)) if i < len(crumb_items) - 1 else '<span aria-current="page">%s</span>' % E(n))
        for i, (n, u) in enumerate(crumb_items))
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(full_title)}</title>
<meta name="description" content="{E(desc)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{url}">
<meta name="theme-color" content="#0d0b08">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{E(BRAND)}">
<meta property="og:title" content="{E(full_title)}">
<meta property="og:description" content="{E(og_desc or desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{og_image}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@TheRubberDuck79">
<meta name="twitter:title" content="{E(full_title)}">
<meta name="twitter:description" content="{E(og_desc or desc)}">
<meta name="twitter:image" content="{og_image}">
<link rel="icon" href="/favicon-duck-white.ico" sizes="any"><link rel="icon" type="image/png" sizes="32x32" href="/favicon-duck-white-32.png"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="stylesheet" href="{CSS_HREF}">
{extra_head}{ld_script(graph)}
<script data-goatcounter="https://therubberduck.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
</head>
<body>
<header class="top"><div class="wrap"><a class="brand" href="/">THE RUBBER DUCK&trade;</a>
<nav aria-label="Rooms">{nav}<a class="shop" href="/merch.html">TRD Collectibles</a><a class="book" href="/book/anon-mission/">anon mission</a></nav></div></header>
<main class="wrap">
<nav class="crumbs" aria-label="Breadcrumb">{crumb_html}</nav>
{body}
</main>
<aside class="wrap support" aria-label="Support the archive">
<p><b>The archive stays free.</b> Keep it running: pick up a signed cap or tee at <a href="/merch.html">TRD Collectibles</a>, or get the book <a href="/book/anon-mission/">anon mission, Volume 1</a> ($19.99 on Gumroad).</p>
</aside>
<footer class="wrap foot"><p>{E(BRAND)} &middot; <a href="/">therubberduck.net</a> &middot; <a href="https://x.com/TheRubberDuck79" rel="me">@TheRubberDuck79</a> &middot; <a href="https://x.com/TheRubberDuck78" rel="me">@TheRubberDuck78</a> &middot; <a href="https://rumble.com/user/TheRubberDuck78" rel="me">Rumble</a> &middot; <a href="/drops/">Q drops by month</a> &middot; <a href="/x/archive/">X posts by month</a> &middot; <a href="/library/">PDF library</a> &middot; <a href="/watch/">Videos</a> &middot; <a href="/listen/">Spaces and shows</a></p></footer>
</body>
</html>
'''

SITEMAPS = defaultdict(list)   # name -> [(loc, lastmod, images[], videos[])]
def add_sm(name, path, lastmod=TODAY, images=None, videos=None):
    SITEMAPS[name].append((SITE + path, lastmod, images or [], videos or []))

# ---------------------------------------------------------------- 1. Q drops
def build_drops():
    src = open('data/drops.js', encoding='utf-8').read()
    arr = json.loads(src[src.index('['):src.rindex(']') + 1])
    drops = []
    for n, ts, site, board, link, text in arr:
        dt = datetime.datetime.fromtimestamp(ts, ET)
        drops.append({'n': n, 'ts': ts, 'dt': dt, 'site': site, 'board': board, 'link': link, 'text': text or ''})
    drops.sort(key=lambda d: d['n'])
    months = OrderedDict()
    for d in drops:
        months.setdefault(d['dt'].strftime('%Y-%m'), []).append(d)
    mkeys = list(months)
    lm = git_date('data/drops.js')

    def drop_card(d, own_link=True):
        h = ('<h2 id="drop-%d"><a href="/drops/%d/">Q drop #%d</a></h2>' % (d['n'], d['n'], d['n'])) if own_link else ''
        meta = '<p class="meta"><time datetime="%s">%s</time> &middot; %s %s</p>' % (d['dt'].isoformat(), d['dt'].strftime('%B %-d, %Y, %-I:%M %p ET'), E(d['site']), E(d['board']))
        return '<article class="item">%s%s<div class="text">%s</div></article>' % (h, meta, linkify(d['text']) or '<em>(image or link only)</em>')

    # per drop
    for i, d in enumerate(drops):
        n = d['n']; mk = d['dt'].strftime('%Y-%m'); mname = d['dt'].strftime('%B %Y')
        first = re.sub(r'\s+', ' ', re.sub(r'https?://\s?\S+', '', d['text'])).strip()
        title = 'Q Drop #%d, %s: Full Text' % (n, d['dt'].strftime('%B %-d, %Y'))
        desc = clip('Q drop #%d, posted %s on %s %s. %s' % (n, d['dt'].strftime('%B %-d, %Y'), d['site'], d['board'], ('"' + clip(first, 110) + '"') if first else 'Full text, date and the original source.'))
        prev = drops[i - 1] if i else None; nxt = drops[i + 1] if i + 1 < len(drops) else None
        pn = '<nav class="pn">%s%s</nav>' % (
            ('<a rel="prev" href="/drops/%d/">&lsaquo; Q drop #%d</a>' % (prev['n'], prev['n'])) if prev else '<span></span>',
            ('<a rel="next" href="/drops/%d/">Q drop #%d &rsaquo;</a>' % (nxt['n'], nxt['n'])) if nxt else '<span></span>')
        body = ('<h1>Q Drop #%d</h1>' % n + drop_card(d, own_link=False) +
                '<ul class="links"><li><a href="/ledger.html#drop-%d">Open #%d in The Drop Ledger</a></li>' % (n, n) +
                '<li><a href="https://qalerts.app/?n=%d" rel="nofollow noopener" target="_blank">See #%d on qalerts.app</a></li>' % (n, n) +
                ('<li><a href="%s" rel="nofollow noopener" target="_blank">Original board archive</a></li>' % E(d['link']) if d['link'] else '') +
                '<li><a href="/drops/%s/">All Q drops from %s</a></li></ul>' % (mk, mname) + pn)
        g = [{'@type': 'CreativeWork', '@id': SITE + '/drops/%d/#drop' % n, 'name': 'Q drop #%d' % n, 'text': d['text'][:5000],
              'dateCreated': d['dt'].isoformat(), 'datePublished': d['dt'].isoformat(), 'author': {'@type': 'Person', 'name': 'Q'},
              'isPartOf': {'@id': SITE + '/drops/#archive'}, 'url': SITE + '/drops/%d/' % n}]
        write('drops/%d/index.html' % n, page('/drops/%d/' % n, title, desc, body, g,
              [('Home', '/'), ('Q Drops', '/drops/'), (mname, '/drops/%s/' % mk), ('#%d' % n, '/drops/%d/' % n)], og_type='article',
              og_desc='Q drop #%d \u00b7 %s \u00b7 %s /%s/' % (n, d['dt'].strftime('%B %-d, %Y'), d['site'], d['board'].strip('/')),   # tease only
              og_image=DROP_OG % n))
        add_sm('drops', '/drops/%d/' % n, lm)

    # per month
    for j, mk in enumerate(mkeys):
        ds = months[mk]; mname = ds[0]['dt'].strftime('%B %Y')
        title = 'Q Drops, %s: #%d to #%d, Full Text' % (mname, ds[0]['n'], ds[-1]['n'])
        desc = clip('All %d Q drops posted in %s (#%d to #%d), in order, with full text, dates, boards and a link to each original source.' % (len(ds), mname, ds[0]['n'], ds[-1]['n']))
        pn = '<nav class="pn">%s%s</nav>' % (
            ('<a rel="prev" href="/drops/%s/">&lsaquo; %s</a>' % (mkeys[j - 1], months[mkeys[j - 1]][0]['dt'].strftime('%B %Y'))) if j else '<span></span>',
            ('<a rel="next" href="/drops/%s/">%s &rsaquo;</a>' % (mkeys[j + 1], months[mkeys[j + 1]][0]['dt'].strftime('%B %Y'))) if j + 1 < len(mkeys) else '<span></span>')
        body = ('<h1>Q Drops, %s</h1><p class="lede">%d drops, #%d to #%d, as originally posted. Search them all in <a href="/ledger.html">The Drop Ledger</a>.</p>' % (mname, len(ds), ds[0]['n'], ds[-1]['n'])
                + pn + ''.join(drop_card(d) for d in ds) + pn)
        g = [{'@type': 'CollectionPage', '@id': SITE + '/drops/%s/#c' % mk, 'name': title, 'url': SITE + '/drops/%s/' % mk, 'isPartOf': {'@id': SITE + '/drops/#archive'}}]
        write('drops/%s/index.html' % mk, page('/drops/%s/' % mk, title, desc, body, g, [('Home', '/'), ('Q Drops', '/drops/'), (mname, '/drops/%s/' % mk)]))
        add_sm('drops', '/drops/%s/' % mk, lm)

    # index
    rows = ''.join('<li><a href="/drops/%s/">%s</a> <span class="n">%d drops &middot; #%d&ndash;#%d</span></li>' % (mk, months[mk][0]['dt'].strftime('%B %Y'), len(months[mk]), months[mk][0]['n'], months[mk][-1]['n']) for mk in mkeys)
    title = 'Every Q Drop by Month: #1 to #%d, Full Text Archive' % drops[-1]['n']
    desc = clip('All %s numbered Q drops, %s to %s, by month and by number, with full text, dates and original sources. From The Rubber Duck.' % (format(len(drops), ','), drops[0]['dt'].strftime('%B %Y'), drops[-1]['dt'].strftime('%B %Y')))
    global DROP_RANGE
    DROP_RANGE = (drops[0]['dt'], drops[-1]['dt'])
    body = ('<h1>Every Q Drop, by Month</h1><p class="lede">All %s numbered drops, #1 to #%d, as originally posted. Each month has its own page, and every drop has its own page. For search and filters, open <a href="/ledger.html">The Drop Ledger</a>; for how a drop was worked, read <a href="/process.html">The Process</a>.</p>' % (format(len(drops), ','), drops[-1]['n'])
            + '<ul class="months">' + rows + '</ul>'
            + '<h2>Jump to a drop</h2><p class="jump">' + ' '.join('<a href="/drops/%d/">#%d</a>' % (k, k) for k in [1, 2, 3, 4, 34, 100, 500, 1000, 1061, 1500, 2000, 2500, 3000, 3500, 4000, 4500, drops[-1]['n']] if k <= drops[-1]['n']) + '</p>')
    g = [{'@type': 'CollectionPage', '@id': SITE + '/drops/#archive', 'name': 'Every Q drop, #1 to #%d' % drops[-1]['n'], 'url': SITE + '/drops/', 'about': 'Q drops'}]
    write('drops/index.html', page('/drops/', title, desc, body, g, [('Home', '/'), ('Q Drops', '/drops/')]))
    add_sm('drops', '/drops/', lm)
    return len(drops), len(mkeys)

# ---------------------------------------------------------------- 2. X archive months
def build_x():
    meta = json.load(open('x/data/meta.json', encoding='utf-8'))
    months = [m[0] for m in meta['months']]
    counts = {}
    lm = meta.get('built', TODAY)
    keep_months = []
    for mk in months:
        posts = json.load(open('x/data/p/%s.json' % mk, encoding='utf-8'))
        # Skip posts that carry third-party contact details (emails / phone numbers): keep private details off indexable pages.
        sel = [p for p in posts if p.get('y') in ('o', 'q') and len(re.sub(r'https?://\S+', '', p.get('x', '')).strip()) >= 3 and not PII.search(p.get('x', ''))]
        if not sel: continue
        keep_months.append((mk, sel))
    for j, (mk, sel) in enumerate(keep_months):
        d0 = datetime.date(int(mk[:4]), int(mk[5:]), 1); mname = d0.strftime('%B %Y')
        counts[mk] = len(sel)
        items = []
        for p in sel:
            dt = datetime.datetime.fromisoformat(p['c'].replace('Z', '+00:00')).astimezone(ET)
            media = ''
            if p.get('m'):
                kinds = {'p': 'photo', 'v': 'video', 'g': 'GIF'}
                ks = sorted(set(kinds.get(m[0], 'media') for m in p['m']))
                media = ' &middot; with ' + ' and '.join(ks)
            items.append('<article class="item" id="p%s"><p class="meta"><time datetime="%s">%s</time>%s%s &middot; <a href="/x/post.html?id=%s">Open post</a> &middot; <a href="https://x.com/TheRubberDuck79/status/%s" rel="nofollow noopener" target="_blank">On X</a></p><div class="text">%s</div></article>'
                         % (p['i'], dt.isoformat(), dt.strftime('%B %-d, %Y, %-I:%M %p ET'), ' &middot; quote post' if p['y'] == 'q' else '', media, p['i'], p['i'], linkify(p['x'])))
        pn = '<nav class="pn">%s%s</nav>' % (
            ('<a rel="prev" href="/x/archive/%s/">&lsaquo; %s</a>' % (keep_months[j - 1][0], datetime.date(int(keep_months[j - 1][0][:4]), int(keep_months[j - 1][0][5:]), 1).strftime('%B %Y'))) if j else '<span></span>',
            ('<a rel="next" href="/x/archive/%s/">%s &rsaquo;</a>' % (keep_months[j + 1][0], datetime.date(int(keep_months[j + 1][0][:4]), int(keep_months[j + 1][0][5:]), 1).strftime('%B %Y'))) if j + 1 < len(keep_months) else '<span></span>')
        title = '@TheRubberDuck79 Posts, %s: X Archive' % mname
        first = clip(re.sub(r'https?://\S+', '', sel[0]['x']), 80)
        desc = clip('%d original posts by The Rubber Duck (@TheRubberDuck79) on X in %s, with full text and dates. First: "%s"' % (len(sel), mname, first))
        body = ('<h1>@TheRubberDuck79 on X, %s</h1><p class="lede">%d original posts and quote posts from %s, oldest first. Replies and reposts are in the full, searchable <a href="/x/">X Archive</a>.</p>' % (mname, len(sel), mname)
                + pn + ''.join(items) + pn)
        g = [{'@type': 'CollectionPage', 'name': title, 'url': SITE + '/x/archive/%s/' % mk, 'about': {'@id': ORG_ID}, 'author': {'@id': ORG_ID}}]
        write('x/archive/%s/index.html' % mk, page('/x/archive/%s/' % mk, title, desc, body, g, [('Home', '/'), ('X Archive', '/x/'), ('By month', '/x/archive/'), (mname, '/x/archive/%s/' % mk)]))
        add_sm('x', '/x/archive/%s/' % mk, lm)
    rows = ''.join('<li><a href="/x/archive/%s/">%s</a> <span class="n">%s posts</span></li>' % (mk, datetime.date(int(mk[:4]), int(mk[5:]), 1).strftime('%B %Y'), format(counts[mk], ',')) for mk, _ in keep_months)
    total = sum(counts.values())
    title = 'The X Archive by Month: Every @TheRubberDuck79 Post'
    desc = clip('Every original post by The Rubber Duck (@TheRubberDuck79) on X, %s to %s, by month with full text. %s posts in all, out of %s in the searchable archive.' % (
        datetime.date(int(keep_months[0][0][:4]), int(keep_months[0][0][5:]), 1).strftime('%B %Y'), datetime.date(int(keep_months[-1][0][:4]), int(keep_months[-1][0][5:]), 1).strftime('%B %Y'), format(total, ','), format(meta['n'], ',')))
    body = '<h1>The X Archive, by Month</h1><p class="lede">%s original posts and quote posts by @TheRubberDuck79, one page per month. Search all %s posts, including replies and reposts, in <a href="/x/">The X Archive</a>.</p><ul class="months">%s</ul>' % (format(total, ','), format(meta['n'], ','), rows)
    write('x/archive/index.html', page('/x/archive/', title, desc, body, [], [('Home', '/'), ('X Archive', '/x/'), ('By month', '/x/archive/')]))
    add_sm('x', '/x/archive/', lm)
    return total, len(keep_months)

# ---------------------------------------------------------------- 3. SCIF library
def slugify(s):
    s = re.sub(r'\.pdf$', '', s, flags=re.I)
    s = re.sub(r'[^a-zA-Z0-9]+', '-', s).strip('-').lower()
    return s[:80].strip('-') or 'doc'

def build_library():
    h = open('pdfs.html', encoding='utf-8').read()
    docs = json.loads(re.search(r'var DOCS = (\[.*?\]);\n', h, re.S).group(1))
    lm = git_date('pdfs.html')
    used = set(); topics = OrderedDict()
    for d in docs:
        s = slugify(d.get('title') or d['name'])
        base = s; k = 2
        while s in used: s = '%s-%d' % (base, k); k += 1
        used.add(s); d['slug'] = s
        topics.setdefault(d.get('topic') or 'Other', []).append(d)
    for d in docs:
        url = '/library/%s/' % d['slug']
        # Some DOCS entries are already %-encoded and a few are full https URLs (media host).
        # Full URLs are used as is; everything else is decoded once, then encoded once.
        if re.match(r'https?://', d['file']):
            pdf_q = pdf_abs = d['file']
        else:
            pdf = '/' + __import__('urllib.parse').parse.unquote(d['file']).lstrip('/')
            pdf_q = '/'.join(__import__('urllib.parse').parse.quote(x) for x in pdf.split('/'))
            pdf_abs = SITE + pdf_q
        thumb = ('/' + d['thumb'].lstrip('/')) if d.get('thumb') else ''
        thumb_q = '/'.join(__import__('urllib.parse').parse.quote(x) for x in thumb.split('/')) if thumb else ''
        size = ('%d KB' % max(1, round(d['bytes'] / 1024))) if d['mb'] < 0.1 else '%.1f MB' % d['mb']
        title = '%s (PDF)' % d['title']
        desc = clip('%s %s Free to read or download: %s pages, %s.' % (d['title'] + '.', d.get('desc', ''), d.get('pages', '?'), size), 158)
        img = '<img class="thumb" src="%s" alt="First page of %s" width="240" height="310" loading="lazy" decoding="async">' % (thumb_q, E(d['title'])) if thumb else ''
        body = ('<h1>%s</h1><div class="doc">%s<div><p class="lede">%s</p><dl class="facts"><dt>Topic</dt><dd>%s</dd><dt>Pages</dt><dd>%s</dd><dt>Size</dt><dd>%s</dd><dt>File</dt><dd>%s</dd><dt>Catalog no.</dt><dd>%s</dd></dl>'
                '<p class="cta"><a class="btn" href="%s">Read or download the PDF</a> <a href="/pdfs.html">Open the SCIF Reading Room</a></p></div></div>'
                % (E(d['title']), img, E(d.get('desc', '')), E(d.get('topic', '')), E(d.get('pages', '')), size, E(d['name']), E(d['id']), pdf_q))
        rel = [x for x in topics[d.get('topic') or 'Other'] if x is not d][:12]
        if rel:
            body += '<h2>More on %s</h2><ul class="list">%s</ul>' % (E(d.get('topic')), ''.join('<li><a href="/library/%s/">%s</a></li>' % (x['slug'], E(x['title'])) for x in rel))
        g = [{'@type': 'DigitalDocument', 'name': d['title'], 'description': d.get('desc', ''), 'url': SITE + url, 'encodingFormat': 'application/pdf',
              'numberOfPages': d.get('pages'), 'contentSize': size, 'about': d.get('topic'), 'isAccessibleForFree': True,
              'associatedMedia': {'@type': 'MediaObject', 'contentUrl': pdf_abs, 'encodingFormat': 'application/pdf'},
              **({'thumbnailUrl': SITE + thumb_q, 'image': SITE + thumb_q} if thumb else {})}]
        write('library/%s/index.html' % d['slug'], page(url, title, desc, body, g, [('Home', '/'), ('SCIF Reading Room', '/pdfs.html'), ('Library', '/library/'), (d['title'], url)],
              og_image=(SITE + thumb_q) if thumb else SHARE))
        add_sm('library', url, lm, images=[(SITE + thumb_q, d['title'])] if thumb else [])
    secs = ''.join('<h2>%s</h2><ul class="list">%s</ul>' % (E(t), ''.join('<li><a href="/library/%s/">%s</a> <span class="n">%s pages</span></li>' % (d['slug'], E(d['title']), d.get('pages', '?')) for d in ds)) for t, ds in topics.items())
    title = 'The SCIF Reading Room Library: %d Free PDFs' % len(docs)
    desc = clip('%d public documents and books to read or download free: PSYOP doctrine, Q drops, the Epstein files and more, grouped by topic, each with a summary.' % len(docs))
    body = '<h1>The SCIF Reading Room Library</h1><p class="lede">%d documents, grouped by topic. Each has its own page with a summary. Search and read them all in <a href="/pdfs.html">The SCIF Reading Room</a>.</p>%s' % (len(docs), secs)
    write('library/index.html', page('/library/', title, desc, body, [], [('Home', '/'), ('SCIF Reading Room', '/pdfs.html'), ('Library', '/library/')]))
    add_sm('library', '/library/', lm)
    return len(docs)

# ---------------------------------------------------------------- 4. videos
def video_ld(v, url, desc):
    o = {'@type': 'VideoObject', '@id': SITE + url + '#video', 'name': v['t'], 'description': clip(desc, 2000) or v['t'],
         'thumbnailUrl': [v['th'] if v['th'].startswith('http') else SITE + v['th']], 'uploadDate': ts_iso(v['ts']),
         'publisher': {'@id': ORG_ID}, 'url': SITE + url}
    if v.get('e'): o['embedUrl'] = v['e']
    if v.get('mediaUrl'): o['contentUrl'] = v['mediaUrl']
    dur = iso_dur(v.get('dur') or v.get('len'))
    if dur: o['duration'] = dur
    if isinstance(v.get('vn'), int) and v['vn'] > 0:
        o['interactionStatistic'] = {'@type': 'InteractionCounter', 'interactionType': {'@type': 'WatchAction'}, 'userInteractionCount': v['vn']}
    return o

def build_videos():
    h = open('videos.html', encoding='utf-8').read()
    allv = json.loads(re.search(r'const ALL = (\[.*?\]);\n', h, re.S).group(1))
    # The local-archive features (data/video-room-local.json) are left out on purpose: they have
    # placeholder dates, a generic poster and filename-based notes, and many are third-party films.
    vids = [v for v in allv if not v.get('rp')]
    seen = set(); out = []
    for v in vids:
        if v['id'] in seen: continue
        seen.add(v['id']); out.append(v)
    lm = git_date('videos.html')
    out.sort(key=lambda v: -int(v.get('ts') or 0))
    for v in out:
        url = '/watch/%s/' % v['id']
        desc_full = v.get('desc') or v['t']
        when = (datetime.datetime.fromtimestamp(int(v['ts']), ET).strftime('%B %-d, %Y') if v.get('source') != 'local' else '')
        title = '%s%s' % (v['t'], ' (Video)' if not v.get('live') else ' (Livestream)')
        desc = clip('%s%s' % ((v['t'] + ': ') if not desc_full.startswith(v['t']) else '', desc_full))
        th = v['th'] if v['th'].startswith('http') else SITE + v['th']
        if v.get('e'):
            player = '<div class="player"><iframe src="%s" title="%s" allowfullscreen allow="autoplay; fullscreen; picture-in-picture" referrerpolicy="strict-origin-when-cross-origin"></iframe></div>' % (E(v['e']), E(v['t']))
        elif v.get('mediaUrl'):
            player = '<div class="player"><video controls preload="none" poster="%s" src="%s"></video></div>' % (E(th), E(v['mediaUrl']))
        else:
            player = ''
        facts = '<p class="meta">%s%s%s</p>' % ((when + ' &middot; ') if when else '', ('Length ' + E(v['dur'])) if v.get('dur') else '', (' &middot; ' + E(v['v']) + ' views on Rumble') if v.get('v') else '')
        links = '<ul class="links"><li><a href="/videos.html#v=%s">Watch at The Rubber Duck Drive-In</a></li>%s</ul>' % (E(v['id']), ('<li><a href="%s" rel="noopener" target="_blank">Watch on Rumble</a></li>' % E(v['u'])) if 'rumble.com' in (v.get('u') or '') else '')
        body = '<h1>%s</h1>%s%s<div class="text">%s</div>%s' % (E(v['t']), player, facts, linkify(desc_full), links)
        write('watch/%s/index.html' % v['id'], page(url, title, desc, body, [video_ld(v, url, desc_full)], [('Home', '/'), ('Video Room', '/videos.html'), ('All videos', '/watch/'), (clip(v['t'], 60), url)],
              og_image=th, og_type='video.other'))
        vid_sm = {'thumb': th, 'title': v['t'], 'desc': clip(desc_full, 2000) or v['t'], 'player': v.get('e') or '', 'content': v.get('mediaUrl') or '',
                  'dur': None, 'date': ts_iso(v['ts'])}
        add_sm('media', url, lm, videos=[vid_sm] if (vid_sm['player'] or vid_sm['content']) else [])
    rows = ''.join('<li><a href="/watch/%s/">%s</a> <span class="n">%s%s</span></li>' % (v['id'], E(v['t']), E(v.get('dur', '')), (' &middot; ' + datetime.datetime.fromtimestamp(int(v['ts']), ET).strftime('%b %-d, %Y')) if v.get('source') != 'local' else '') for v in out)
    title = 'Videos and Livestreams: All %d Features' % len(out)
    desc = clip('Every video and livestream in The Rubber Duck Drive-In: %d features, each with its own page, a summary, the player and a link to Rumble.' % len(out))
    body = '<h1>All Videos and Livestreams</h1><p class="lede">%d features, newest first. Watch them the fun way at <a href="/videos.html">The Rubber Duck Drive-In</a>.</p><ul class="list">%s</ul>' % (len(out), rows)
    write('watch/index.html', page('/watch/', title, desc, body, [], [('Home', '/'), ('Video Room', '/videos.html'), ('All videos', '/watch/')], og_image=SITE + '/assets/trd/img/share-videos.jpg'))
    add_sm('media', '/watch/', lm)
    return len(out)

def build_listen():
    h = open('listening-room.html', encoding='utf-8').read()
    D = json.loads(re.search(r'const DATA = (\{.*?\});\n', h, re.S).group(1))
    SER = {s['k']: s['name'] for s in D['series']}
    lm = git_date('listening-room.html')
    vols = []; seen = set()
    for v in D['vols']:
        if v['id'] in seen: continue
        seen.add(v['id']); vols.append(v)
    for v in vols:
        url = '/listen/%s/' % v['id']
        mn = v.get('min') or {}
        summ = mn.get('sum') or v.get('sum') or ''
        title = '%s, %s' % (v['t'], v.get('ds') or v.get('d'))
        desc = clip('%s (%s, %s). %s' % (v['t'], v.get('d'), 'Rumble' if v['src'] == 'rumble' else 'X Space', summ))
        player = ''
        if v.get('embed'):
            player = '<div class="player"><iframe src="%s" title="%s" allowfullscreen allow="autoplay; fullscreen; picture-in-picture" referrerpolicy="strict-origin-when-cross-origin"></iframe></div>' % (E(v['embed']), E(v['t']))
        facts = '<dl class="facts"><dt>Date</dt><dd>%s</dd><dt>Series</dt><dd>%s</dd><dt>Source</dt><dd>%s</dd>%s%s%s</dl>' % (
            E(v.get('d')), E(SER.get(v.get('ser'), '')), 'Rumble' if v['src'] == 'rumble' else 'X Space', ('<dt>Length</dt><dd>%s</dd>' % E(v['lenl'])) if v.get('len') else '',
            ('<dt>Host</dt><dd>%s</dd>' % E(v['host'])) if v.get('host') else '', ('<dt>Topics</dt><dd>%s</dd>' % E(', '.join(v.get('topics') or []))) if v.get('topics') else '')
        mins = ''
        if mn.get('tops'):
            mins = '<h2>Minutes</h2>' + (('<p class="meta">%s</p>' % E(mn['att'])) if mn.get('att') else '') + '<ol class="minutes">' + ''.join(
                '<li><b>%s %s</b><p>%s</p></li>' % (E(t.get('at', '')), E(t.get('t', '')), E(t.get('x', ''))) for t in mn['tops']) + '</ol>'
            if mn.get('closing'): mins += '<p>%s</p>' % E(mn['closing'])
            if v.get('note'): mins += '<p class="meta">%s</p>' % E(v['note'])
        links = '<ul class="links"><li><a href="/listening-room.html#vol=%s">Take it down from the shelf in The Listening Room</a></li><li><a href="%s" rel="noopener" target="_blank">%s</a></li></ul>' % (
            E(v['id']), E(v['url']), 'Listen on Rumble' if v['src'] == 'rumble' else 'Open the Space on X')
        body = '<h1>%s</h1><p class="meta">%s</p>%s<p class="lede">%s</p>%s%s%s' % (E(v['t']), E(v.get('orig', '')), player, E(summ), facts, mins, links)
        g = []
        if v['src'] == 'rumble' and v.get('embed') and v.get('th'):
            vv = {'t': v['t'], 'e': v['embed'], 'th': v['th'], 'ts': v['ts'], 'len': v.get('len'), 'vn': int(v['views']) if str(v.get('views', '')).isdigit() else 0}
            g.append(video_ld(vv, url, summ))
        else:
            g.append({'@type': 'CreativeWork', 'name': v['t'], 'description': summ, 'dateCreated': ts_iso(v['ts']), 'url': SITE + url, 'sameAs': v['url'], 'author': {'@id': ORG_ID}})
        th = v['th'] if v.get('th') else SITE + '/assets/trd/img/share-listening.jpg'
        write('listen/%s/index.html' % v['id'], page(url, title, desc, body, g, [('Home', '/'), ('Listening Room', '/listening-room.html'), ('All volumes', '/listen/'), (clip(title, 60), url)],
              og_image=th, og_type='video.other' if v['src'] == 'rumble' else 'article'))
        vids = []
        if v['src'] == 'rumble' and v.get('embed') and v.get('th'):
            vids = [{'thumb': v['th'], 'title': v['t'], 'desc': clip(summ, 2000) or v['t'], 'player': v['embed'], 'content': '', 'date': ts_iso(v['ts'])}]
        add_sm('media', url, lm, videos=vids)
    by = OrderedDict((k, []) for k in SER)
    for v in vols: by.setdefault(v.get('ser'), []).append(v)
    secs = ''.join('<h2>%s</h2><ul class="list">%s</ul>' % (E(SER.get(k, k)), ''.join('<li><a href="/listen/%s/">%s</a> <span class="n">%s &middot; %s</span></li>' % (v['id'], E(v['t']), E(v.get('ds', '')), 'Rumble' if v['src'] == 'rumble' else 'X Space') for v in vs)) for k, vs in by.items() if vs)
    title = 'X Spaces and Shows: All %d Listening Room Volumes' % len(vols)
    desc = clip('Every X Space and Rumble show with The Rubber Duck in The Listening Room: %d volumes by series, each with a written summary and minutes.' % len(vols))
    body = '<h1>X Spaces and Shows</h1><p class="lede">%d conversations, shelved by series. Each has its own page with a summary. Listen the fun way in <a href="/listening-room.html">The Listening Room</a>.</p>%s' % (len(vols), secs)
    write('listen/index.html', page('/listen/', title, desc, body, [], [('Home', '/'), ('Listening Room', '/listening-room.html'), ('All volumes', '/listen/')], og_image=SITE + '/assets/trd/img/share-listening.jpg'))
    add_sm('media', '/listen/', lm)
    return len(vols)

# ---------------------------------------------------------------- 5. merch
def parse_merch():
    h = open('merch.html', encoding='utf-8').read()
    items = []
    for m in re.finditer(r'<article class="item([^"]*)" data-slug="([^"]+)"[^>]*>(.*?)</article>', h, re.S):
        cls, slug, b = m.group(1), m.group(2), m.group(3)
        g = lambda p: (re.search(p, b, re.S).group(1).strip() if re.search(p, b, re.S) else '')
        name = html.unescape(re.sub('<[^>]+>', '', g(r'<span class="nm">(.*?)</span>')))
        price = g(r'class="amt">\$([0-9.]+)')
        ship = g(r'<td class="amt">\$[0-9.]+</td><td>\$([0-9.]+)</td>')
        img = g(r'<img src="([^"]+)"')
        alt = html.unescape(g(r'<img src="[^"]+" alt="([^"]*)"'))
        buy = g(r'<a class="buy" href="([^"]+)"')
        bio = [(html.unescape(re.sub('<[^>]+>', '', a)), html.unescape(re.sub('<[^>]+>', '', c))) for a, c in re.findall(r'<li><b>(.*?)</b><span>(.*?)</span></li>', g(r'<ul class="bio">(.*?)</ul>'))]
        shipin = html.unescape(g(r'<p class="bk-ship">(.*?)</p>'))
        colors = [html.unescape(c) for c in re.findall(r'<option value="([^"]+)" data-img=', b)]
        # special-order colors (umbrella rule, tools/umbrella_lineup.py): <option ... data-special="1"> in the card's color picker
        special_colors = [html.unescape(c) for c, a in re.findall(r'<option value="([^"]+)" data-img=("[^>]*)>', b) if 'data-special="1"' in a]
        sizes = [(a, l, int(p)) for a, l, p in re.findall(r'<option value="([^"]+)" data-link="([^"]+)" data-price="(\d+)"', b)]
        special = dict(re.findall(r'<option value="([^"]+)" data-link="[^"]+" data-price="\d+" data-special-link="([^"]+)"', b))
        # the fixed SIZE (the card's "Size" line), not the first fixed line (which is the color on one-color items: mug "White")
        fix = html.unescape(re.sub('<[^>]+>', '', g(r'<span class="lbl">Size</span>\s*<p class="fix">(.*?)</p>')))
        items.append({'slug': slug, 'signed': 'signed' in cls, 'name': name, 'price': price, 'ship': ship, 'img': img, 'alt': alt, 'buy': buy,
                      'bio': bio, 'shipin': shipin, 'colors': colors, 'sizes': sizes, 'fix': fix, 'special': special,
                      'special_colors': special_colors})
    return items

def card_photo(src):
    """A store card image made only to fill the card frame (store-img/demo/*_card.jpg, the Red Pill Tee) -> the photo itself (*_mock.jpg)."""
    return re.sub(r'(store-img/demo/[^"]+)_(card|front)\.jpg$', r'\1_mock.jpg', src)

def product_ld(it, url):
    desc = '%s from TRD Collectibles by The Rubber Duck. %s.' % (it['name'], '; '.join('%s: %s' % b for b in it['bio']))
    if it['signed']: desc += ' Hand-signed and numbered out of 500.'
    ship = {'@type': 'OfferShippingDetails', 'shippingRate': {'@type': 'MonetaryAmount', 'value': it['ship'], 'currency': 'USD'},
            'shippingDestination': {'@type': 'DefinedRegion', 'addressCountry': 'US'}} if it['ship'] else None
    def offer(price, link, name=None):
        o = {'@type': 'Offer', 'url': link or (SITE + url), 'price': price, 'priceCurrency': 'USD', 'availability': 'https://schema.org/MadeToOrder',
             'itemCondition': 'https://schema.org/NewCondition', 'seller': {'@id': ORG_ID}}
        if name: o['name'] = name
        if ship: o['shippingDetails'] = ship
        return o
    if it['sizes']:
        offers = [offer('%.2f' % (p / 100), l, 'Size ' + s) for s, l, p in it['sizes']]
    else:
        offers = offer('%.2f' % float(it['price']), it['buy'])
    imgs = [SITE + '/' + card_photo(it['img']).lstrip('/')]
    return {'@type': 'Product', '@id': SITE + url + '#product', 'name': it['name'], 'description': desc, 'sku': 'TRD-' + it['slug'],
            'image': imgs, 'brand': {'@type': 'Brand', 'name': 'The Rubber Duck'}, 'url': SITE + url, 'offers': offers,
            **({'color': ', '.join(it['colors'])} if it['colors'] else {})}

def build_shop():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from shop_demo_media import demo_block, gallery_block, gallery_images, order_block, promise_block
    items = parse_merch()
    lm = git_date('merch.html')
    for it in items:
        url = '/shop/%s/' % it['slug']
        img = '/' + it['img'].lstrip('/')
        webp = re.sub(r'\.jpg$', '.webp', img)
        price_txt = '$' + it['price'] + (' and up' if it['sizes'] and len(set(p for _, _, p in it['sizes'])) > 1 else '')
        title = '%s, %s | TRD Collectibles' % (it['name'], price_txt)
        desc = clip('%s from The Rubber Duck, %s plus $%s US shipping. %s%s Made to order. %s.' % (it['name'], price_txt, it['ship'],
                    '; '.join('%s: %s' % b for b in it['bio'][:3]) + '.', ' Hand-signed and numbered out of 500.' if it['signed'] else '', it['shipin'] or 'Ships in 3 to 8 business days'))
        sizes = ''
        bio = it['bio']
        if it['sizes']:   # the per-size price row replaces the card's own "Sizes" line (no duplicate Sizes row)
            bio = [(x, y) for x, y in bio if x not in ('Size', 'Sizes')]
            sizes = '<dt>Sizes</dt><dd>%s</dd>' % ', '.join('%s $%s' % (s, ('%.2f' % (p / 100)).rstrip('0').rstrip('.')) for s, _, p in it['sizes'])
        elif it['fix'] and not any(x in ('Size', 'Sizes', 'Fit', 'Fits') for x, _ in bio):
            sizes = '<dt>Size</dt><dd>%s</dd>' % E(it['fix'])
        facts = '<dl class="facts"><dt>Price</dt><dd>%s</dd><dt>US shipping</dt><dd>$%s</dd>%s%s%s</dl>' % (
            E(price_txt), E(it['ship']), ''.join('<dt>%s</dt><dd>%s</dd>' % (E(a), E(c)) for a, c in bio), sizes,
            (('<dt>Colors</dt><dd>%s</dd>' % E(', '.join(c for c in it['colors'] if c not in it['special_colors']))) +
             ('<dt>Special order</dt><dd>%s (up to 7 extra days)</dd>' % E(', '.join(it['special_colors'])) if it['special_colors'] else '')) if it['colors'] else '')
        # Listings with a color gallery (tools/shop_demo_media.py GALLERY) show it full width as the main photo, in place of the square store photo.
        gal, gimgs = gallery_block(it['slug']), gallery_images(it['slug'])
        order = order_block(it['slug'], [(z, l, c, it['special'].get(z)) for z, l, c in it['sizes']]) if gal else ''
        pic = ('<picture><source srcset="%s" type="image/webp"><img class="prod" src="%s" alt="%s" width="800" height="800" decoding="async"></picture>'
               % (E(webp), E(img), E(it['alt'] or it['name']))) if not gal else ''
        body = ('<h1>%s</h1>%s<div class="doc%s">%s<div>'
                '<p class="lede">%s%s</p>%s%s'
                '<p class="meta">%s. Made to order and paid securely through Stripe. Every order helps keep therubberduck.net free.</p></div></div>'
                % (E(it['name']), gal, ' tg-doc' if gal else '', pic, E(it['name']), ', signed and numbered by hand out of 500.' if it['signed'] else ' from TRD Collectibles.',
                   facts, order or '<p class="cta"><a class="btn" href="/merch.html">Choose color and size in the store</a> <a href="%s" rel="noopener">Buy now through Stripe</a></p>' % E(it['buy']),
                   E(it['shipin'] or 'Ships in 3 to 8 business days')))
        # the umbrella special-order promise, on every listing (tools/umbrella_lineup.py)
        body += promise_block(it['slug'], it['special_colors'], it['signed'], bool(gal))
        body += demo_block(it['slug'])
        others = [o for o in items if o is not it]
        body += '<h2>More from TRD Collectibles</h2><ul class="list">%s</ul>' % ''.join('<li><a href="/shop/%s/">%s</a> <span class="n">$%s</span></li>' % (o['slug'], E(o['name']), o['price']) for o in others)
        ld = product_ld(it, url)
        if gimgs:
            ld['image'] = [SITE + u for u, _ in gimgs] + [u for u in ld['image'] if u not in [SITE + g for g, _ in gimgs]]
        og = SITE + (gimgs[0][0] if gimgs else img)
        write('shop/%s/index.html' % it['slug'], page(url, title, desc, body, [ld],
              [('Home', '/'), ('TRD Collectibles', '/merch.html'), (it['name'], url)], og_image=og, og_type='product'))
        add_sm('shop', url, lm, images=[(SITE + u, a) for u, a in gimgs] or [(SITE + img, it['name'])])
    return items

def build_soon():
    # Premium line, coming soon: pages + merch.html section, no prices or checkout (tools/premium_soon.py)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from premium_soon import build_soon as _bs
    _bs(page, write, add_sm, SITE, git_date('tools/premium_soon.py'))

def build_book():
    url = '/book/anon-mission/'
    title = 'anon mission, Volume 1: All You Need to Know About Q ($19.99 PDF)'
    desc = 'anon mission or all you need to know about q - and how they made you afraid to ask. Volume 1 of the book by The Rubber Duck, a polished printable PDF, $19.99 on Gumroad.'
    body = ('<h1>anon mission, Volume 1</h1><div class="doc"><picture><img class="prod" src="/assets/trd/img/anon-mission-book-face@2x.webp" alt="The cover of anon mission, Volume 1, by The Rubber Duck" width="560" height="872" decoding="async"></picture><div>'
            '<p class="lede"><b>anon mission</b> or <i>all you need to know about q - and how they made you afraid to ask</i>. A polished, printable PDF by The Rubber Duck.</p>'
            '<dl class="facts"><dt>Price</dt><dd>$19.99</dd><dt>Format</dt><dd>PDF, printable</dd><dt>Author</dt><dd>The Rubber Duck</dd><dt>Sold through</dt><dd>Gumroad</dd></dl>'
            '<p class="cta"><a class="btn" href="%s" rel="noopener">Get your copy on Gumroad, $19.99</a></p>'
            '<p>Want the background first? Read every drop in <a href="/ledger.html">The Drop Ledger</a> or <a href="/drops/">by month</a>, see <a href="/process.html">how a drop was worked</a>, and browse the <a href="/library/">SCIF Reading Room library</a>.</p></div></div>') % GUMROAD
    write('book/anon-mission/index.html', page(url, title, desc, body, [book_ld()], [('Home', '/'), ('anon mission, Volume 1', url)],
          og_image=SITE + '/assets/trd/img/anon-mission-book-face@2x.webp', og_type='book'))
    add_sm('shop', url, TODAY, images=[(SITE + '/assets/trd/img/anon-mission-book-face@2x.webp', 'anon mission, Volume 1')])

# ---------------------------------------------------------------- 6. existing room pages: head only
ROOMS = OrderedDict([
    ('index.html', {'path': '/', 'title': 'The Rubber Duck&trade; | Q Drops Archive, Videos, X Spaces, Merch and Books',
                    'desc': 'Welcome, curious minds. The Rubber Duck\'s open archive of the Q era: every Q drop, videos, X Spaces, PDFs, memes and 61,225 X posts, plus TRD Collectibles and the book anon mission.',
                    'crumbs': [('Home', '/')], 'img': None}),
    ('ledger.html', {'path': '/ledger.html', 'title': None, 'desc': None, 'crumbs': [('Home', '/'), ('The Drop Ledger', '/ledger.html')], 'img': None}),
    ('Qdrops/index.html', {'path': '/Qdrops/', 'title': None, 'desc': None, 'crumbs': [('Home', '/'), ('Q Drop Archive', '/Qdrops/')], 'img': None}),
    ('videos.html', {'path': '/videos.html', 'title': 'Videos and Livestreams | The Rubber Duck&trade; Drive-In on Rumble', 'desc': None,
                     'crumbs': [('Home', '/'), ('Video Room', '/videos.html')], 'img': '/assets/trd/img/share-videos.jpg'}),
    ('listening-room.html', {'path': '/listening-room.html', 'title': None, 'desc': None, 'crumbs': [('Home', '/'), ('Listening Room', '/listening-room.html')], 'img': '/assets/trd/img/share-listening.jpg'}),
    ('memes.html', {'path': '/memes.html', 'title': None, 'desc': None, 'crumbs': [('Home', '/'), ('The Meme Dump', '/memes.html')], 'img': None}),
    ('pdfs.html', {'path': '/pdfs.html', 'title': 'The SCIF Reading Room | Free PDF Library on Q, PSYOP and Epstein | The Rubber Duck&trade;', 'desc': None,
                   'crumbs': [('Home', '/'), ('SCIF Reading Room', '/pdfs.html')], 'img': None}),
    ('x/index.html', {'path': '/x/', 'title': 'The X Archive: Every @TheRubberDuck79 Post | The Rubber Duck&trade;', 'desc': None, 'crumbs': [('Home', '/'), ('X Archive', '/x/')], 'img': None}),
    ('album.html', {'path': '/album.html', 'title': None, 'desc': None, 'crumbs': [('Home', '/'), ('The Red Pill Album', '/album.html')], 'img': None}),
    ('merch.html', {'path': '/merch.html', 'title': 'TRD Collectibles | Signed Caps, Tees and Merch | The Rubber Duck&trade;',
                    'desc': 'The Rubber Duck merch store: caps, tees, mugs, patches and stickers from $5, plus signed caps and tees numbered by hand out of 500. Every order keeps the site free.',
                    'crumbs': [('Home', '/'), ('TRD Collectibles', '/merch.html')], 'img': None}),
    ('process.html', {'path': '/process.html', 'title': None, 'desc': None, 'crumbs': [('Home', '/'), ('The Process', '/process.html')], 'img': None}),
])
PRECONNECT = {
    '*': ['https://therubberduck.goatcounter.com', 'https://gc.zgo.at'],
    'videos.html': ['https://hugh.cdn.rumble.cloud', 'https://rumble.com'],
    'listening-room.html': ['https://hugh.cdn.rumble.cloud'],
    'memes.html': ['https://memes.therubberduck.net'],
    'x/index.html': ['https://pbs.twimg.com'],
}
IMG_ALT = {'/assets/trd/img/share-videos.jpg': 'The Rubber Duck Drive-In: a lit Now Showing marquee reading Videos and Livestreams above the screen, under a night sky with a full moon.',
           '/assets/trd/img/share-listening.jpg': 'The Listening Room: an open book on the reading desk under a green lamp, above a shelf of numbered leather volumes.'}
# Lossless WebP twins of the heaviest PNGs (pixel-identical), and the exact src strings to point at them.
WEBP_SWAPS = {
    'Qdrops/index.html': [('"../images/hero.png"', '"../images/hero.webp"'), ('"../images/drop-index.png"', '"../images/drop-index.webp"'), ('"../images/reading-room.png"', '"../images/reading-room.webp"')],
    'ledger.html': [('"images/hero.png"', '"images/hero.webp"'), ('"images/reading-room.png"', '"images/reading-room.webp"')],
}
PII = re.compile(r'[\w.+-]+@[\w-]+\.[a-z]{2,}|\(?\b\d{3}\)?[ .-]?\d{3}[ .-]\d{4}\b', re.I)
def ensure_webp():
    from PIL import Image
    for f in ['images/hero.png', 'images/drop-index.png', 'images/reading-room.png']:
        w = f[:-4] + '.webp'
        if not os.path.exists(w):
            Image.open(f).save(w, 'WEBP', lossless=True, quality=100, method=6, exact=True)
        a, b = Image.open(f).convert('RGBA'), Image.open(w).convert('RGBA')
        assert a.tobytes() == b.tobytes(), 'webp not pixel-identical: ' + w
ROBOTS_META = '<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">'

def set_tag(h, pattern, new):
    return re.sub(pattern, lambda m: new, h, count=1, flags=re.I)

def room_extra(f, info, merch_items):
    url = SITE + info['path']
    g = []
    if f == 'index.html':
        g.append(book_ld())
        g.append({'@type': 'ItemList', 'name': 'Rooms at The Rubber Duck', 'itemListElement': [
            {'@type': 'SiteNavigationElement', 'position': i + 1, 'name': n, 'url': SITE + u} for i, (u, n) in enumerate([
                ('/videos.html', 'Video Room'), ('/listening-room.html', 'Listening Room'), ('/ledger.html', 'The Drop Ledger'), ('/memes.html', 'The Meme Dump'),
                ('/pdfs.html', 'The SCIF Reading Room'), ('/x/', 'Twitter / X Archive'), ('/album.html', 'Red Pill Album'), ('/merch.html', 'TRD Collectibles')])]})
    if f == 'merch.html':
        g.append({'@type': 'OnlineStore', '@id': SITE + '/merch.html#store', 'name': 'TRD Collectibles', 'url': url, 'parentOrganization': {'@id': ORG_ID}, 'brand': {'@type': 'Brand', 'name': 'The Rubber Duck'}})
        g.append({'@type': 'ItemList', 'name': 'TRD Collectibles', 'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'item': product_ld(it, '/shop/%s/' % it['slug'])} for i, it in enumerate(merch_items)]})
    if f == 'album.html':
        src = open('assets/trd/duckpod.js', encoding='utf-8').read()
        tracks = re.findall(r"\['(\d\d-[^']+)', '([^']+)', '(\d+:\d+)'\]", src)
        g.append({'@type': 'MusicAlbum', '@id': url + '#album', 'name': 'The Red Pill Album', 'byArtist': {'@type': 'MusicGroup', 'name': 'The Rubber Duck', 'sameAs': SAME_AS[:3]},
                  'datePublished': '2026-04-30', 'numTracks': len(tracks), 'image': SITE + '/images/opt/album-cover-card.jpg', 'url': url,
                  'sameAs': ['https://open.spotify.com/album/2zxmpLk7jYsvoEUAKTWbH4', 'https://music.apple.com/us/album/the-red-pill-album/1896233683'],
                  'track': [{'@type': 'MusicRecording', 'position': i + 1, 'name': html.unescape(t), 'duration': iso_dur(d), 'url': SITE + '/audio/' + s + '.mp3'} for i, (s, t, d) in enumerate(tracks)]})
    if f in ('ledger.html', 'Qdrops/index.html'):
        g.append({'@type': 'Dataset', 'name': 'The Drop Ledger: every numbered Q drop, #1 to #4,966', 'description': 'Every numbered Q drop from %s to %s, in order, with dates, boards, full text and a link to each original source.' % (DROP_RANGE[0].strftime('%B %Y'), DROP_RANGE[1].strftime('%B %Y')),
                  'url': SITE + '/drops/', 'creator': {'@id': ORG_ID}, 'isAccessibleForFree': True, 'temporalCoverage': '%s/%s' % (DROP_RANGE[0].date().isoformat(), DROP_RANGE[1].date().isoformat()),
                  'distribution': {'@type': 'DataDownload', 'encodingFormat': 'application/javascript', 'contentUrl': SITE + '/data/drops.js'}})
    return g

def build_rooms(merch_items):
    for f, info in ROOMS.items():
        h = open(f, encoding='utf-8').read()
        h = re.sub(r'<!-- seo:begin -->.*?<!-- seo:end -->\n', '', h, flags=re.S)
        if info['title']:
            h = set_tag(h, r'<title>[^<]*</title>', '<title>%s</title>' % info['title'])
            h = set_tag(h, r'<meta property="og:title" content="[^"]*">', '<meta property="og:title" content="%s">' % info['title'])
            h = set_tag(h, r'<meta name="twitter:title" content="[^"]*">', '<meta name="twitter:title" content="%s">' % info['title'])
        if info['desc']:
            d = E(info['desc'])
            for p, t in [(r'<meta name="description" content="[^"]*">', '<meta name="description" content="%s">'),
                         (r'<meta property="og:description" content="[^"]*">', '<meta property="og:description" content="%s">'),
                         (r'<meta name="twitter:description" content="[^"]*">', '<meta name="twitter:description" content="%s">')]:
                h = set_tag(h, p, t % d)
        if info['img']:
            h = re.sub(r'(<meta property="og:image" content=")[^"]*(">)', r'\g<1>' + SITE + info['img'] + r'\2', h, count=1)
            h = re.sub(r'(<meta name="twitter:image" content=")[^"]*(">)', r'\g<1>' + SITE + info['img'] + r'\2', h, count=1)
            if info['img'] in IMG_ALT:
                h = re.sub(r'(<meta property="og:image:alt" content=")[^"]*(">)', lambda m: m.group(1) + E(IMG_ALT[info['img']]) + m.group(2), h, count=1)
                h = re.sub(r'(<meta name="twitter:image:alt" content=")[^"]*(">)', lambda m: m.group(1) + E(IMG_ALT[info['img']]) + m.group(2), h, count=1)
        for a, b in WEBP_SWAPS.get(f, []):
            h = h.replace(a, b)
        title = html.unescape(re.search(r'<title>([^<]*)</title>', h).group(1))
        desc = html.unescape((re.search(r'<meta name="description" content="([^"]*)"', h) or re.search(r'()', '')).group(1))
        url = SITE + info['path']
        bc = crumbs(info['crumbs']); bc['@id'] = url + '#crumbs'
        ptype = 'CollectionPage' if f not in ('index.html', 'process.html') else ('WebPage' if f == 'index.html' else 'Article')
        wp = {'@type': ptype, '@id': url + '#page', 'url': url, 'name': title, 'description': desc, 'isPartOf': {'@id': SITE_ID}, 'publisher': {'@id': ORG_ID},
              'inLanguage': 'en', 'breadcrumb': {'@id': url + '#crumbs'}}
        if f == 'process.html': wp.update({'headline': title[:110], 'author': {'@id': ORG_ID}, 'image': SHARE})
        if f == 'index.html': wp['about'] = {'@id': ORG_ID}
        graph = [org(), website(), wp, bc] + room_extra(f, info, merch_items)
        pcs = ''.join('<link rel="preconnect" href="%s" crossorigin>\n' % o for o in PRECONNECT['*'] + PRECONNECT.get(f, []) if ('href="%s"' % o) not in h)
        block = '<!-- seo:begin -->\n' + pcs + ('' if re.search(r'<meta name="robots"', h) else ROBOTS_META + '\n') + \
                ('' if re.search(r'twitter:image', h) else '<meta name="twitter:image" content="%s">\n' % (re.search(r'<meta property="og:image" content="([^"]*)"', h).group(1))) + \
                ld_script(graph) + '\n<!-- seo:end -->'
        h = h.replace('</head>', block + '\n</head>', 1)
        write(f, h)

# ---------------------------------------------------------------- 7. sitemaps + robots
def build_sitemaps():
    rooms = [('/', 'index.html'), ('/merch.html', 'merch.html'), ('/book/anon-mission/', None), ('/ledger.html', 'ledger.html'), ('/Qdrops/', 'Qdrops/index.html'),
             ('/videos.html', 'videos.html'), ('/listening-room.html', 'listening-room.html'), ('/memes.html', 'memes.html'), ('/pdfs.html', 'pdfs.html'),
             ('/x/', 'x/index.html'), ('/album.html', 'album.html'), ('/process.html', 'process.html')]
    pages = []
    for p, f in rooms:
        if f is None: continue
        imgs = []
        if f == 'merch.html':
            imgs = [(SITE + '/' + (card_photo(x) if '/demo/' in x else 'store-img/' + os.path.basename(x)), None) for x in sorted(set(re.findall(r'src="(store-img/[^"]+\.jpg)"', open(f).read())))]
        if f == 'album.html':
            imgs = [(SITE + '/images/opt/album-cover-card.jpg', 'The Red Pill Album cover')]
        pages.append((SITE + p, git_date(f), imgs, []))
    SITEMAPS['pages'] = pages + SITEMAPS.get('pages', [])
    os.makedirs('sitemaps', exist_ok=True)
    names = []
    for name in ['pages', 'shop', 'drops', 'media', 'library', 'x']:
        urls = SITEMAPS.get(name) or []
        if not urls: continue
        out = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1" xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">']
        for loc, lm, imgs, vids in urls:
            s = '  <url><loc>%s</loc><lastmod>%s</lastmod>' % (E(loc), lm)
            for u, _t in imgs:
                s += '<image:image><image:loc>%s</image:loc></image:image>' % E(u)
            for v in vids:
                s += ('<video:video><video:thumbnail_loc>%s</video:thumbnail_loc><video:title>%s</video:title><video:description>%s</video:description>%s%s<video:publication_date>%s</video:publication_date></video:video>'
                      % (E(v['thumb']), E(v['title'][:100]), E(v['desc'][:2048]), ('<video:content_loc>%s</video:content_loc>' % E(v['content'])) if v.get('content') else '',
                         ('<video:player_loc>%s</video:player_loc>' % E(v['player'])) if v.get('player') else '', v['date']))
            out.append(s + '</url>')
        out.append('</urlset>\n')
        write('sitemaps/%s.xml' % name, '\n'.join(out))
        names.append(name)
    idx = ['<?xml version="1.0" encoding="UTF-8"?>', '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for n in names:
        lm = max(u[1] for u in SITEMAPS[n])
        idx.append('  <sitemap><loc>%s/sitemaps/%s.xml</loc><lastmod>%s</lastmod></sitemap>' % (SITE, n, lm))
    idx.append('</sitemapindex>\n')
    write('sitemap.xml', '\n'.join(idx))
    write('robots.txt', 'User-agent: *\nAllow: /\nDisallow: /tools/\nDisallow: /workers/\n\nSitemap: %s/sitemap.xml\n' % SITE)
    allurls = [u[0] for n in names for u in SITEMAPS[n]]
    write('sitemaps/all-urls.txt', '\n'.join(allurls) + '\n')
    return {n: len(SITEMAPS[n]) for n in names}

if __name__ == '__main__':
    stats = {}
    stats['drops'] = build_drops()
    stats['x'] = build_x()
    stats['library'] = build_library()
    stats['watch'] = build_videos()
    stats['listen'] = build_listen()
    items = build_shop(); stats['shop'] = len(items)
    build_soon()
    build_book()
    ensure_webp()
    build_rooms(items)
    stats['sitemaps'] = build_sitemaps()
    print(json.dumps(stats, indent=1))
