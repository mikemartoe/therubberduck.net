#!/usr/bin/env python3
"""DUCK SAUCE feeds: RSS 2.0 + Google News sitemap (PREVIEW, not wired into main yet).

  python3 tools/newsroom-feeds.py            # writes newsroom/feed.xml and sitemaps/news.xml
  python3 tools/newsroom-feeds.py --now 2026-11-24T12:00:00-05:00   # test the 48h window

Reads the JSON-LD in newsroom/<slug>/index.html (headline, datePublished,
dateModified, image, @type) and the page's meta description.
- feed.xml: newest 50 stories, all kinds (articles + commentary), full permalinks.
- news.xml: only Article/NewsArticle/OpinionNewsArticle published in the last
  48 hours (Google: "articles that were created in the last two days").
  An empty urlset is fine (Search Console shows a harmless warning).
Author and publisher are always "The Rubber Duck". No personal names, ever.
"""
import argparse, datetime as dt, glob, html, json, os, re
from email.utils import format_datetime
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://therubberduck.net'
PUB = 'The Rubber Duck'
ET = dt.timezone(dt.timedelta(hours=-5))  # date-only legacy stories: treat as midnight ET
NEWS_TYPES = {'NewsArticle', 'Article', 'OpinionNewsArticle', 'ReportageNewsArticle', 'AnalysisNewsArticle'}

def parse_date(s):
    if not s: return None
    if len(s) == 10: return dt.datetime.fromisoformat(s).replace(tzinfo=ET)
    d = dt.datetime.fromisoformat(s.replace('Z', '+00:00'))
    return d if d.tzinfo else d.replace(tzinfo=ET)

def stories():
    out = []
    for f in glob.glob(os.path.join(ROOT, 'newsroom', '*', 'index.html')):
        s = open(f, encoding='utf-8').read()
        if re.search(r'<meta name="robots" content="[^"]*noindex', s): continue
        m = re.search(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
        if not m: continue
        graph = json.loads(m.group(1)).get('@graph', [])
        art = next((x for x in graph if x.get('@type') not in ('Organization', 'BreadcrumbList', 'Person', 'WebSite')), None)
        if not art or not art.get('datePublished'): continue
        slug = os.path.basename(os.path.dirname(f))
        desc = re.search(r'<meta name="description" content="([^"]*)"', s)
        img = art.get('image'); img = img[0] if isinstance(img, list) else img
        if isinstance(img, dict): img = img.get('url')
        out.append(dict(
            slug=slug, type=art['@type'], title=html.unescape(art.get('headline', slug)),
            url=f'{SITE}/newsroom/{slug}/', desc=html.unescape(desc.group(1)) if desc else '',
            pub=parse_date(art['datePublished']), mod=parse_date(art.get('dateModified') or art['datePublished']),
            img=img, lang=art.get('inLanguage', 'en')))
    out.sort(key=lambda x: x['pub'], reverse=True)
    return out

def rss(items):
    now = items[0]['mod'] if items else dt.datetime.now(ET)
    rows = []
    for it in items[:50]:
        enc = ''
        if it['img'] and it['img'].startswith(SITE):
            local = os.path.join(ROOT, it['img'][len(SITE):].split('?')[0].lstrip('/'))
            if os.path.isfile(local):
                mime = 'image/webp' if local.endswith('.webp') else 'image/png' if local.endswith('.png') else 'image/jpeg'
                enc = f'\n      <enclosure url="{escape(it["img"])}" type="{mime}" length="{os.path.getsize(local)}"/>'
        rows.append(f'''    <item>
      <title>{escape(it["title"])}</title>
      <link>{it["url"]}</link>
      <guid isPermaLink="true">{it["url"]}</guid>
      <pubDate>{format_datetime(it["pub"])}</pubDate>
      <dc:creator>{PUB}</dc:creator>
      <category>{"commentary" if it["type"] == "SocialMediaPosting" or it["type"] == "OpinionNewsArticle" else "news"}</category>
      <description>{escape(it["desc"])}</description>{enc}
    </item>''')
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel>
    <title>DUCK SAUCE | The Rubber Duck</title>
    <link>{SITE}/newsroom.html</link>
    <atom:link href="{SITE}/newsroom/feed.xml" rel="self" type="application/rss+xml"/>
    <description>original news, commentary and dispatches by the rubber duck. free to read, always.</description>
    <language>en-us</language>
    <lastBuildDate>{format_datetime(now)}</lastBuildDate>
    <image><url>{SITE}/favicon-192.png</url><title>DUCK SAUCE | The Rubber Duck</title><link>{SITE}/newsroom.html</link></image>
{chr(10).join(rows)}
  </channel>
</rss>
'''

def news_sitemap(items, now):
    cutoff = now - dt.timedelta(hours=48)
    rows = []
    for it in items:
        if it['type'] not in NEWS_TYPES or it['pub'] < cutoff or it['pub'] > now: continue
        rows.append(f'''  <url>
    <loc>{it["url"]}</loc>
    <news:news>
      <news:publication><news:name>{PUB}</news:name><news:language>{it["lang"][:2]}</news:language></news:publication>
      <news:publication_date>{it["pub"].isoformat()}</news:publication_date>
      <news:title>{escape(it["title"])}</news:title>
    </news:news>
  </url>''')
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
            '        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n' + '\n'.join(rows) + ('\n' if rows else '') + '</urlset>\n'), len(rows)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--now'); ap.add_argument('--dry', action='store_true')
    a = ap.parse_args()
    now = dt.datetime.fromisoformat(a.now) if a.now else dt.datetime.now(dt.timezone.utc)
    items = stories()
    feed = rss(items); sm, n = news_sitemap(items, now)
    if not a.dry:
        open(os.path.join(ROOT, 'newsroom', 'feed.xml'), 'w', encoding='utf-8').write(feed)
        open(os.path.join(ROOT, 'sitemaps', 'news.xml'), 'w', encoding='utf-8').write(sm)
    print(f'feed: {min(len(items),50)} items | news sitemap: {n} urls in the 48h window ending {now.isoformat()}')
    # Keep the article-end "support the mission" block in place on every story.
    import importlib.util
    support = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'newsroom-support.py')
    spec = importlib.util.spec_from_file_location('newsroom_support', support)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    rows = mod.apply(dry=a.dry)
    nchg = sum(1 for *_, c in rows if c)
    print(f'support block: {"dry, would update" if a.dry else "updated"} {nchg} of {len(rows)} articles')
