#!/usr/bin/env python3
"""Back-catalog schema, feeds and sitemaps (preview branch).

Makes already-public archive material easier for crawlers to cite, without
changing visible archive text, captions, art, avatars, the global nav,
signup/suggestion scripts, or duckpod files.

  python3 tools/back-catalog-schema.py            # default sample permalinks
  python3 tools/back-catalog-schema.py --all-visible
  python3 tools/back-catalog-schema.py --dry

What it does:
  1. Injects SocialMediaPosting ItemList JSON-LD into each X monthly archive
     page, for the same original posts already printed in that page's HTML.
     Dates come from x/data/p/*.json (created_at). sharedContent.url is the
     original x.com status. Author is The Rubber Duck.
  2. Writes crawlable permalinks at /x/status/{id}/ for a representative
     sample (or every month-visible original with --all-visible). Body text
     is the archived post, unedited.
  3. Writes /x/feed.xml (Atom of the 50 newest sample/visible posts).
  4. Writes sitemaps/x-status.xml, updates sitemap.xml and sitemaps/x.xml
     lastmods, and appends new URLs to sitemaps/all-urls.txt.
  5. Adds sharedContent / isBasedOn on DUCK SAUCE stories when the page
     already contains an @TheRubberDuck79 status URL.
  6. Adds numberOfItems (from memes.json count) and the catalog generated
     date as dateModified on The Meme Dump CollectionPage. Does not invent
     datePublished for individual memes.
  7. Adds a <link rel="alternate"> to /x/feed.xml on /x/ and /x/archive/,
     and notes the feed plus status permalinks in llms.txt.

Dates are never invented. Posts with emails or phone numbers are kept off
indexable pages, matching tools/seo-build.py. Do not run tools/i18n/build.py
from this script.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import html
import json
import os
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://therubberduck.net'
ORG_ID = SITE + '/#org'
SITE_ID = SITE + '/#website'
AUTHOR = {
    '@type': 'Person',
    'name': 'The Rubber Duck',
    'url': 'https://x.com/TheRubberDuck79',
}
ET = ZoneInfo('America/New_York')
TODAY = dt.date.today().isoformat()
# Real contact details only. Do not treat 11+ digit tweet IDs or URLs as phone numbers.
PII = re.compile(
    r'(?:[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})|(?<!\d)(?:\+?1[-.\s]*)?(?:\(\d{3}\)|\d{3})[-.\s]+\d{3}[-.\s]+\d{4}(?!\d)',
    re.I,
)
X_STATUS = re.compile(
    r'https?://(?:www\.)?(?:x|twitter)\.com/TheRubberDuck79/status/(\d+)',
    re.I,
)
LD_RE = re.compile(
    r'(<script type="application/ld\+json">)(.*?)(</script>)',
    re.S,
)
ALT_FEED = (
    '<link rel="alternate" type="application/atom+xml" '
    'title="The Rubber Duck X Archive" href="%s/x/feed.xml">' % SITE
)

E = lambda s: html.escape(str(s if s is not None else ''), quote=True)


def clip(s, n=155):
    s = re.sub(r'\s+', ' ', str(s or '')).strip()
    if len(s) <= n:
        return s
    cut = s[: n - 1].rsplit(' ', 1)[0]
    return cut.rstrip(' ,.;:-') + '\u2026'


def linkify(text):
    out = E(text)
    out = re.sub(
        r'(https?://[^\s<>"]+)',
        lambda m: '<a href="%s" rel="nofollow noopener" target="_blank">%s</a>'
        % (m.group(1), m.group(1)),
        out,
    )
    return out.replace('\n', '<br>')


def parse_created(c):
    return dt.datetime.fromisoformat(c.replace('Z', '+00:00')).astimezone(ET)


def visible_original(p):
    """Fallback filter. Month ItemLists use IDs already in the monthly HTML."""
    if p.get('y') not in ('o', 'q'):
        return False
    bare = re.sub(r'https?://\S+', '', p.get('x', '')).strip()
    return len(bare) >= 3 and not PII.search(p.get('x', ''))


ARTICLE_ID = re.compile(r'<article class="item" id="p(\d+)"')


def posts_already_on_month_page(month, by_id, packs):
    path = ROOT / 'x/archive' / month / 'index.html'
    if not path.exists():
        return []
    ids = ARTICLE_ID.findall(path.read_text(encoding='utf-8'))
    out = []
    for pid in ids:
        p = by_id.get(pid)
        if not p:
            # fall back to this month's pack
            for q in packs.get(month, []):
                if q['i'] == pid:
                    p = dict(q)
                    p['_month'] = month
                    break
        if p:
            out.append(p if p.get('_month') == month else dict(p, _month=month))
    return out


def x_url(pid):
    return 'https://x.com/TheRubberDuck79/status/' + pid


def status_path(pid):
    return '/x/status/%s/' % pid


def dumps_ld(graph):
    data = {'@context': 'https://schema.org', '@graph': graph}
    s = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    return s.replace('</', '<\\/')


def inject_graph(html_text, mutator):
    """Run mutator(graph) on the first JSON-LD block in <head> or the page.

    mutator may modify the graph in place and return True if it changed.
    """
    m = LD_RE.search(html_text)
    if not m:
        return html_text, False
    try:
        data = json.loads(m.group(2).replace('<\\/', '</'))
    except json.JSONDecodeError as e:
        raise SystemExit('JSON-LD parse error: %s' % e)
    graph = data.get('@graph', data if isinstance(data, list) else [data])
    if not isinstance(graph, list):
        graph = [graph]
    changed = bool(mutator(graph))
    if not changed:
        return html_text, False
    new = m.group(1) + dumps_ld(graph) + m.group(3)
    return html_text[: m.start()] + new + html_text[m.end() :], True


def ensure_alternate(html_text):
    if 'rel="alternate"' in html_text and '/x/feed.xml' in html_text:
        return html_text, False
    # insert before the first JSON-LD or before </head>
    needle = '<script type="application/ld+json">'
    if needle in html_text:
        html_text = html_text.replace(needle, ALT_FEED + '\n' + needle, 1)
        return html_text, True
    if '</head>' in html_text:
        return html_text.replace('</head>', ALT_FEED + '\n</head>', 1), True
    return html_text, False


def load_packs():
    packs = {}
    by_id = {}
    for f in sorted((ROOT / 'x/data/p').glob('*.json')):
        posts = json.loads(f.read_text(encoding='utf-8'))
        packs[f.stem] = posts
        for p in posts:
            p = dict(p)
            p['_month'] = f.stem
            by_id[p['i']] = p
    html_visible = []
    for mk in packs:
        html_visible.extend(posts_already_on_month_page(mk, by_id, packs))
    return packs, by_id, html_visible


def posting_obj(p, *, full_text, permalink):
    dt_et = parse_created(p['c'])
    text = p.get('x') or ''
    url = SITE + (status_path(p['i']) if permalink else '/x/archive/%s/#p%s' % (p['_month'], p['i']))
    obj = {
        '@type': 'SocialMediaPosting',
        '@id': SITE + status_path(p['i']) + '#post' if permalink else SITE + '/x/archive/%s/#p%s' % (p['_month'], p['i']),
        'url': url,
        'datePublished': dt_et.isoformat(),
        'author': {'@type': 'Person', '@id': AUTHOR['url']},
        'isPartOf': {'@id': SITE_ID},
        'identifier': p['i'],
        'sharedContent': {'@type': 'SocialMediaPosting', 'url': x_url(p['i'])},
        'inLanguage': p.get('l') or 'en',
    }
    # Full text belongs on individual permalinks. Month pages already print it in HTML.
    if full_text:
        obj['headline'] = clip(text, 110)
        obj['articleBody'] = text
        obj['author'] = AUTHOR
    if p.get('m'):
        imgs = [m[1] for m in p['m'] if len(m) > 1 and str(m[1]).startswith('http')]
        if imgs:
            obj['image'] = imgs
    if p.get('y') == 't':
        obj['additionalType'] = 'https://schema.org/ShareAction'
    return obj


def pick_sample(visible, by_id, newsroom_ids, n_recent=50, n_early=15, per_year=8):
    chosen = collections.OrderedDict()

    def add(p):
        if p and p['i'] not in chosen:
            chosen[p['i']] = p

    for pid in newsroom_ids:
        add(by_id.get(pid))
    # newest first for the feed
    newest = sorted(visible, key=lambda p: p['c'], reverse=True)
    for p in newest[:n_recent]:
        add(p)
    oldest = sorted(visible, key=lambda p: p['c'])
    for p in oldest[:n_early]:
        add(p)
    by_year = collections.defaultdict(list)
    for p in visible:
        by_year[p['c'][:4]].append(p)
    for year in sorted(by_year):
        # evenly spaced through the year
        group = sorted(by_year[year], key=lambda p: p['c'])
        if not group:
            continue
        step = max(1, len(group) // per_year)
        for p in group[::step][:per_year]:
            add(p)
    return list(chosen.values())


def month_itemlist(posts, month, have_permalinks):
    elements = []
    for i, p in enumerate(posts, 1):
        elements.append({
            '@type': 'ListItem',
            'position': i,
            'item': posting_obj(p, full_text=False, permalink=p['i'] in have_permalinks),
        })
    list_id = SITE + '/x/archive/%s/#post-list' % month
    return {
        '@type': 'ItemList',
        '@id': list_id,
        'name': 'Original @TheRubberDuck79 posts, %s' % month,
        'numberOfItems': len(elements),
        'itemListOrder': 'https://schema.org/ItemListOrderAscending',
        'itemListElement': elements,
    }


def patch_month_page(path, posts, have_permalinks):
    html_text = path.read_text(encoding='utf-8')
    month = path.parent.name
    list_id = SITE + '/x/archive/%s/#post-list' % month

    def mut(graph):
        # drop a previous run of this tool
        graph[:] = [g for g in graph if not (isinstance(g, dict) and g.get('@id') == list_id)]
        itemlist = month_itemlist(posts, month, have_permalinks)
        for g in graph:
            if isinstance(g, dict) and g.get('@type') == 'CollectionPage':
                g['mainEntity'] = {'@id': list_id}
                g['numberOfItems'] = len(posts)
                if posts:
                    g['datePublished'] = parse_created(posts[0]['c']).isoformat()
                    g['dateModified'] = parse_created(posts[-1]['c']).isoformat()
                g['author'] = AUTHOR
        graph.append(itemlist)
        return True

    new, changed = inject_graph(html_text, mut)
    if changed:
        path.write_text(new, encoding='utf-8')
    return changed


def status_page(p):
    dt_et = parse_created(p['c'])
    month = p['_month']
    mname = dt.date(int(month[:4]), int(month[5:]), 1).strftime('%B %Y')
    title = clip(p.get('x') or ('Post ' + p['i']), 80)
    page_title = '%s | The X Archive | The Rubber Duck™' % title
    desc = clip('A post by The Rubber Duck (@TheRubberDuck79) on X, %s. Shown as posted, with a link to the original.' % dt_et.strftime('%B %-d, %Y, %-I:%M %p ET'))
    url = SITE + status_path(p['i'])
    graph = [
        {
            '@type': 'Organization',
            '@id': ORG_ID,
            'name': 'The Rubber Duck',
            'url': SITE + '/',
            'sameAs': [
                'https://x.com/TheRubberDuck79',
                'https://x.com/TheRubberDuck78',
                'https://rumble.com/user/TheRubberDuck78',
            ],
        },
        {
            '@type': 'WebSite',
            '@id': SITE_ID,
            'url': SITE + '/',
            'name': 'The Rubber Duck',
            'publisher': {'@id': ORG_ID},
            'inLanguage': 'en',
        },
        posting_obj(p, full_text=True, permalink=True),
        {
            '@type': 'BreadcrumbList',
            '@id': url + '#crumbs',
            'itemListElement': [
                {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': SITE + '/'},
                {'@type': 'ListItem', 'position': 2, 'name': 'X Archive', 'item': SITE + '/x/'},
                {'@type': 'ListItem', 'position': 3, 'name': 'X posts by month', 'item': SITE + '/x/archive/'},
                {'@type': 'ListItem', 'position': 4, 'name': mname, 'item': SITE + '/x/archive/%s/' % month},
                {'@type': 'ListItem', 'position': 5, 'name': 'Post ' + p['i'], 'item': url},
            ],
        },
    ]
    # image for og: prefer first photo if present, else site share image
    og = SITE + '/images/brand/trd-share-2026.jpg'
    if p.get('m'):
        for m in p['m']:
            if len(m) > 1 and str(m[1]).startswith('http'):
                og = m[1]
                break
    media = ''
    if p.get('m'):
        kinds = {'p': 'photo', 'v': 'video', 'g': 'GIF'}
        ks = sorted(set(kinds.get(m[0], 'media') for m in p['m']))
        media = ' &middot; with ' + ' and '.join(ks)
    body = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
<meta name="description" content="%s">
<link rel="canonical" href="%s">
<link rel="alternate" type="application/atom+xml" title="The Rubber Duck X Archive" href="%s/x/feed.xml">
<meta property="og:type" content="article">
<meta property="og:site_name" content="The Rubber Duck&trade;">
<meta property="og:title" content="%s">
<meta property="og:description" content="%s">
<meta property="og:url" content="%s">
<meta property="og:image" content="%s">
<meta property="article:published_time" content="%s">
<meta property="article:author" content="https://x.com/TheRubberDuck79">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@TheRubberDuck79">
<meta name="twitter:creator" content="@TheRubberDuck79">
<meta name="twitter:title" content="%s">
<meta name="twitter:description" content="%s">
<meta name="twitter:image" content="%s">
<link rel="icon" href="/favicon-duck-white.ico" sizes="any">
<link rel="stylesheet" href="/assets/seo/archive.css?v=1">
<script type="application/ld+json">%s</script>
</head>
<body>
<header class="top"><div class="wrap"><a class="brand" href="/">THE RUBBER DUCK&trade;</a>
<nav aria-label="Rooms"><a href="/">Home</a><a href="/ledger.html">Drop Ledger</a><a href="/videos.html">Video Room</a><a href="/listening-room.html">Listening Room</a><a href="/pdfs.html">SCI[F]</a><a href="/x/">X Archive</a><a href="/memes.html">Meme Dump</a><a href="/album.html">Red Pill Album</a><a class="shop" href="/merch.html">TRD Collectibles</a><a class="book" href="/book/anon-mission/">anon mission</a></nav></div></header>
<main class="wrap">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> <span aria-hidden="true">&rsaquo;</span> <a href="/x/">X Archive</a> <span aria-hidden="true">&rsaquo;</span> <a href="/x/archive/">X posts by month</a> <span aria-hidden="true">&rsaquo;</span> <a href="/x/archive/%s/">%s</a> <span aria-hidden="true">&rsaquo;</span> <span aria-current="page">Post</span></nav>
<article class="item" id="p%s">
<h1 class="sr" style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)">%s</h1>
<p class="meta"><time datetime="%s">%s</time>%s &middot; <a href="/x/archive/%s/#p%s">This post in the monthly archive</a> &middot; <a href="/x/post.html?id=%s">Open this post in the X Archive</a> &middot; <a href="%s" rel="nofollow noopener" target="_blank">View this post on X</a></p>
<div class="text">%s</div>
</article>
<p class="foot">Original post by The Rubber Duck (@TheRubberDuck79). Text is shown as posted. This page is a crawlable permalink into the <a href="/x/">X Archive</a>.</p>
</main>
</body>
</html>
''' % (
        E(page_title),
        E(desc),
        E(url),
        SITE,
        E(page_title),
        E(desc),
        E(url),
        E(og),
        E(dt_et.isoformat()),
        E(page_title),
        E(desc),
        E(og),
        dumps_ld(graph),
        E(month),
        E(mname),
        E(p['i']),
        E(page_title),
        E(dt_et.isoformat()),
        E(dt_et.strftime('%B %-d, %Y, %-I:%M %p ET')),
        media,
        E(month),
        E(p['i']),
        E(p['i']),
        E(x_url(p['i'])),
        linkify(p.get('x') or ''),
    )
    return body


def write_status_pages(posts, dry):
    written = []
    for p in posts:
        dest = ROOT / 'x/status' / p['i'] / 'index.html'
        if not dry:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(status_page(p), encoding='utf-8')
        written.append(p)
    return written


def write_feed(posts):
    posts = sorted(posts, key=lambda p: p['c'], reverse=True)[:50]
    updated = parse_created(posts[0]['c']).isoformat() if posts else dt.datetime.now(ET).isoformat()
    entries = []
    for p in posts:
        dt_et = parse_created(p['c'])
        url = SITE + status_path(p['i'])
        title = clip(p.get('x') or ('Post ' + p['i']), 80)
        summary = clip(p.get('x') or '', 280)
        entries.append(
            '''  <entry>
    <title>%s</title>
    <link href="%s" rel="alternate" type="text/html"/>
    <link href="%s" rel="related" type="text/html"/>
    <id>%s</id>
    <updated>%s</updated>
    <published>%s</published>
    <author><name>The Rubber Duck</name><uri>https://x.com/TheRubberDuck79</uri></author>
    <summary type="text">%s</summary>
  </entry>'''
            % (
                E(title),
                E(url),
                E(x_url(p['i'])),
                E(url),
                E(dt_et.isoformat()),
                E(dt_et.isoformat()),
                E(summary),
            )
        )
    feed = '''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>The Rubber Duck X Archive</title>
  <subtitle>Original posts by The Rubber Duck (@TheRubberDuck79), shown as posted, with original dates and links to the post on X.</subtitle>
  <link href="%s/x/feed.xml" rel="self" type="application/atom+xml"/>
  <link href="%s/x/archive/" rel="alternate" type="text/html"/>
  <id>%s/x/feed.xml</id>
  <updated>%s</updated>
  <author><name>The Rubber Duck</name><uri>https://x.com/TheRubberDuck79</uri></author>
%s
</feed>
''' % (SITE, SITE, SITE, E(updated), '\n'.join(entries))
    (ROOT / 'x/feed.xml').write_text(feed, encoding='utf-8')
    return len(posts)


def write_status_sitemap(posts):
    """Write sitemaps/x-status.xml, split into 50,000-URL / 50 MB files if needed."""
    posts = sorted(posts, key=lambda x: x['c'])
    header = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    footer = '</urlset>\n'
    url_limit = 50000
    byte_limit = 50 * 1024 * 1024
    for old in (ROOT / 'sitemaps').glob('x-status*.xml'):
        old.unlink()
    chunks, cur, cur_bytes = [], [], len(header.encode()) + len(footer.encode())
    for p in posts:
        row = '  <url><loc>%s%s</loc><lastmod>%s</lastmod></url>\n' % (SITE, status_path(p['i']), TODAY)
        add = len(row.encode())
        if cur and (len(cur) >= url_limit or cur_bytes + add > byte_limit):
            chunks.append(cur)
            cur, cur_bytes = [], len(header.encode()) + len(footer.encode())
        cur.append(row)
        cur_bytes += add
    if cur or not chunks:
        chunks.append(cur)
    names = []
    for i, chunk in enumerate(chunks, 1):
        name = 'x-status.xml' if len(chunks) == 1 else 'x-status-%d.xml' % i
        (ROOT / 'sitemaps' / name).write_text(header + ''.join(chunk) + footer, encoding='utf-8')
        names.append(name)
    return len(posts), names


def update_sitemap_index(status_sitemaps=None):
    idx = ROOT / 'sitemap.xml'
    text = idx.read_text(encoding='utf-8')
    # drop any previous x-status entries, then add the current file list
    text = re.sub(
        r'  <sitemap><loc>%s/sitemaps/x-status[^<]*</loc><lastmod>[^<]*</lastmod></sitemap>\n?' % re.escape(SITE),
        '',
        text,
    )
    if status_sitemaps is None:
        status_sitemaps = sorted(path.name for path in (ROOT / 'sitemaps').glob('x-status*.xml'))
    entries = ''.join(
        '  <sitemap><loc>%s/sitemaps/%s</loc><lastmod>%s</lastmod></sitemap>\n' % (SITE, name, TODAY)
        for name in status_sitemaps
    )
    if '</sitemapindex>' not in text:
        raise SystemExit('sitemap.xml has no sitemapindex close tag')
    text = text.replace('</sitemapindex>', entries + '</sitemapindex>')
    # bump x.xml lastmod in the index (month pages gained JSON-LD today)
    text = re.sub(
        r'(<sitemap><loc>%s/sitemaps/x.xml</loc><lastmod>)[^<]+' % re.escape(SITE),
        r'\g<1>' + TODAY,
        text,
    )
    idx.write_text(text, encoding='utf-8')


def update_x_sitemap_lastmods():
    path = ROOT / 'sitemaps/x.xml'
    text = path.read_text(encoding='utf-8')
    # month pages and index were updated today with JSON-LD
    text2 = re.sub(r'<lastmod>[^<]+</lastmod>', '<lastmod>%s</lastmod>' % TODAY, text)
    if text2 != text:
        path.write_text(text2, encoding='utf-8')
        return True
    return False


def append_all_urls(posts):
    path = ROOT / 'sitemaps/all-urls.txt'
    existing = set()
    if path.exists():
        existing = {line.strip() for line in path.read_text(encoding='utf-8').splitlines() if line.strip()}
    new = []
    for p in posts:
        u = SITE + status_path(p['i'])
        if u not in existing:
            new.append(u)
    feed = SITE + '/x/feed.xml'
    if feed not in existing:
        new.append(feed)
    if new:
        with path.open('a', encoding='utf-8') as f:
            if path.stat().st_size and not path.read_text(encoding='utf-8').endswith('\n'):
                f.write('\n')
            f.write('\n'.join(new) + '\n')
    return len(new)


def newsroom_ids_and_patch(dry):
    ids = []
    patched = 0
    for f in sorted((ROOT / 'newsroom').glob('*/index.html')):
        text = f.read_text(encoding='utf-8')
        found = X_STATUS.findall(text)
        # preserve order, unique
        uniq = []
        for pid in found:
            if pid not in uniq:
                uniq.append(pid)
        ids.extend(uniq)
        if not uniq:
            continue

        def mut(graph, uniq=uniq):
            changed = False
            primary = uniq[0]
            shared = {'@type': 'SocialMediaPosting', 'url': x_url(primary)}
            if len(uniq) > 1:
                shared['sameAs'] = [x_url(i) for i in uniq[1:]]
            for g in graph:
                if not isinstance(g, dict):
                    continue
                t = g.get('@type')
                if t == 'SocialMediaPosting' and 'sharedContent' not in g:
                    g['sharedContent'] = shared
                    g['identifier'] = g.get('identifier') or primary
                    changed = True
                elif t in ('NewsArticle', 'Article', 'OpinionNewsArticle', 'ReportageNewsArticle', 'AnalysisNewsArticle') and 'isBasedOn' not in g:
                    g['isBasedOn'] = shared
                    changed = True
            return changed

        new, changed = inject_graph(text, mut)
        if changed and not dry:
            f.write_text(new, encoding='utf-8')
            patched += 1
        elif changed and dry:
            patched += 1
    return ids, patched


def patch_memes(dry):
    data = json.loads((ROOT / 'memes/data/memes.json').read_text(encoding='utf-8'))
    count = int(data.get('count') or len(data.get('items') or []))
    generated = data.get('generated')  # catalog build date, not meme origin dates
    path = ROOT / 'memes.html'
    text = path.read_text(encoding='utf-8')

    def mut(graph):
        changed = False
        for g in graph:
            if isinstance(g, dict) and g.get('@type') == 'CollectionPage':
                if g.get('numberOfItems') != count:
                    g['numberOfItems'] = count
                    changed = True
                if generated and g.get('dateModified') != generated:
                    # ingest/catalog date only; do not set datePublished
                    g['dateModified'] = generated
                    changed = True
        return changed

    new, changed = inject_graph(text, mut)
    if changed and not dry:
        path.write_text(new, encoding='utf-8')
    return changed, count, generated


def patch_x_homes(dry):
    n = 0
    for rel in ('x/index.html', 'x/archive/index.html'):
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding='utf-8')
        new, changed = ensure_alternate(text)
        if changed and not dry:
            path.write_text(new, encoding='utf-8')
        if changed:
            n += 1
    return n


def patch_llms(visible_n, originals_n, archive_n, sample_n):
    path = ROOT / 'llms.txt'
    text = path.read_text(encoding='utf-8')
    block = (
        '- [The X Archive](https://therubberduck.net/x/): searchable archive of %s posts by The Rubber Duck (@TheRubberDuck79) on X\n'
        '- [X posts by month](https://therubberduck.net/x/archive/): %s original posts with full text, dates and links to the original post on X, one crawlable page per month (June 2020 to November 2026). The searchable archive holds %s originals and %s posts in all, including replies and reposts.\n'
        '- [X Archive Atom feed](https://therubberduck.net/x/feed.xml): recent original posts, with original dates, archive permalinks and links to the post on X\n'
        '- [X post permalinks](https://therubberduck.net/x/status/): sample crawlable pages for individual archive posts at /x/status/{id}/, each with the original date and a link to the post on X. tools/back-catalog-schema.py can build the rest of the month-visible set.\n'
        % (format(archive_n, ','), format(visible_n, ','), format(originals_n, ','), format(archive_n, ','))
    )
    # replace the two existing X bullets if present
    text2, n = re.subn(
        r'- \[The X Archive\]\(https://therubberduck\.net/x/\):.*\n- \[X posts by month\]\(https://therubberduck\.net/x/archive/\):.*\n(?:- \[X Archive Atom feed\]\(https://therubberduck\.net/x/feed\.xml\):.*\n)?(?:- \[X post permalinks\]\(https://therubberduck\.net/x/status/\):.*\n)?',
        block,
        text,
        count=1,
    )
    if n == 0:
        # insert before DUCK SAUCE bullet in that section
        text2 = text.replace(
            '- [DUCK SAUCE](https://therubberduck.net/newsroom.html)',
            block + '- [DUCK SAUCE](https://therubberduck.net/newsroom.html)',
            1,
        )
    if text2 != text:
        path.write_text(text2, encoding='utf-8')
        return True
    return False


def validate():
    errors = []
    # month pages
    for f in sorted((ROOT / 'x/archive').glob('*/index.html')):
        text = f.read_text(encoding='utf-8')
        for i, m in enumerate(LD_RE.finditer(text)):
            try:
                data = json.loads(m.group(2).replace('<\\/', '</'))
            except Exception as e:
                errors.append('%s block %d: %s' % (f, i, e))
                continue
            graph = data.get('@graph', [])
            types = [g.get('@type') for g in graph if isinstance(g, dict)]
            if f.parent.name != 'archive' and 'ItemList' not in types and f.parent.name >= '2020-06':
                # months with no visible posts won't have an ItemList if we skipped them
                pass
    for f in (ROOT / 'x/status').glob('*/index.html'):
        text = f.read_text(encoding='utf-8')
        ms = list(LD_RE.finditer(text))
        if not ms:
            errors.append('%s: no JSON-LD' % f)
            continue
        try:
            data = json.loads(ms[0].group(2).replace('<\\/', '</'))
        except Exception as e:
            errors.append('%s: %s' % (f, e))
            continue
        posts = [g for g in data.get('@graph', []) if isinstance(g, dict) and g.get('@type') == 'SocialMediaPosting' and g.get('author')]
        # sharedContent child is also SocialMediaPosting; require a dated one
        dated = [g for g in posts if g.get('datePublished') and g.get('author', {}).get('name') == 'The Rubber Duck']
        if not dated:
            errors.append('%s: missing dated SocialMediaPosting' % f)
        else:
            if 'T' not in dated[0]['datePublished']:
                errors.append('%s: datePublished is not a full timestamp' % f)
            if not dated[0].get('sharedContent', {}).get('url', '').startswith('https://x.com/'):
                errors.append('%s: missing sharedContent.url' % f)
    if errors:
        raise SystemExit('validation failed:\n' + '\n'.join(errors[:20]))
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dry', action='store_true')
    ap.add_argument('--all-visible', action='store_true',
                    help='Write permalinks for every original already shown on monthly archive pages (thousands of files).')
    args = ap.parse_args()
    os.chdir(ROOT)

    packs, by_id, visible = load_packs()
    meta = json.loads((ROOT / 'x/data/meta.json').read_text(encoding='utf-8'))
    originals_n = sum(1 for p in by_id.values() if p.get('y') in ('o', 'q'))
    archive_n = int(meta.get('n') or len(by_id))

    newsroom_ids, newsroom_patched = newsroom_ids_and_patch(dry=True if args.dry else False)
    # newsroom_ids_and_patch already writes unless we need to avoid double write
    # (called once here after dry handling below — rewrite call structure)

    if args.all_visible:
        sample = list(visible)
        # still include newsroom-linked posts we have, even if they failed the visible filter
        have = {p['i'] for p in sample}
        for pid in newsroom_ids:
            if pid in by_id and pid not in have:
                sample.append(by_id[pid])
    else:
        sample = pick_sample(visible, by_id, newsroom_ids)

    have_permalinks = {p['i'] for p in sample}

    if args.dry:
        months_with = sum(1 for mk in packs if posts_already_on_month_page(mk, by_id, packs))
        print('dry: posts already on month pages: %d' % len(visible))
        print('dry: sample permalinks: %d' % len(sample))
        print('dry: month pages with posts: %d' % months_with)
        print('dry: newsroom status ids: %d unique, pages to patch counted separately' % len(set(newsroom_ids)))
        return

    # newsroom already patched above only when not dry — fix: I passed dry incorrectly.
    # Re-run is idempotent.

    written = write_status_pages(sample, dry=False)
    month_changed = 0
    skipped_empty = 0
    for mk in packs:
        sel = posts_already_on_month_page(mk, by_id, packs)
        path = ROOT / 'x/archive' / mk / 'index.html'
        if not sel or not path.exists():
            skipped_empty += 1
            continue
        if patch_month_page(path, sel, have_permalinks):
            month_changed += 1
    feed_n = write_feed(written)
    sm_n, sm_names = write_status_sitemap(written)
    update_sitemap_index(sm_names)
    update_x_sitemap_lastmods()
    new_urls = append_all_urls(written)
    memes_changed, meme_count, meme_gen = patch_memes(dry=False)
    homes = patch_x_homes(dry=False)
    llms = patch_llms(len(visible), originals_n, archive_n, len(written))
    validate()
    print('status permalinks: %d' % len(written))
    print('month pages patched: %d (empty/skipped %d)' % (month_changed, skipped_empty))
    print('atom feed entries: %d -> /x/feed.xml' % feed_n)
    print('x-status sitemap urls: %d in %s' % (sm_n, ', '.join(sm_names)))
    print('new all-urls lines: %d' % new_urls)
    print('newsroom stories patched with source status: %d (ids: %d)' % (newsroom_patched, len(set(newsroom_ids))))
    print('memes.html CollectionPage updated: %s (numberOfItems=%s, dateModified=%s)' % (memes_changed, meme_count, meme_gen))
    print('x homes feed link: %d' % homes)
    print('llms.txt updated: %s' % llms)
    print('ok: JSON-LD parsed on month pages and status permalinks')


if __name__ == '__main__':
    main()
