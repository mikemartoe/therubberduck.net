#!/usr/bin/env python3
"""Keep /live.json (the ON AIR sign) in sync.

  python3 tools/update-live-json.py                 # set latestArticle = newest newsroom/<slug>/ story
  python3 tools/update-live-json.py --live https://x.com/i/broadcasts/XXXX --label "LIVE FROM THE BEACH"
  python3 tools/update-live-json.py --off           # end the broadcast (keeps latestArticle)

Newest story = the highest schema.org datePublished among newsroom/*/index.html
(ties broken by file mtime). Run it as the last step of every DUCK SAUCE publish.
"""
import argparse, glob, html, json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE = os.path.join(ROOT, 'live.json')

def newest():
    best = None
    for f in glob.glob(os.path.join(ROOT, 'newsroom', '*', 'index.html')):
        s = open(f, encoding='utf-8').read()
        m = re.search(r'"headline":\s*"((?:[^"\\]|\\.)*)",\s*"datePublished":\s*"([^"]+)"', s)
        if not m: continue
        slug = os.path.basename(os.path.dirname(f))
        title = json.loads('"' + m.group(1) + '"')
        key = (m.group(2), os.path.getmtime(f))
        if best is None or key > best[0]:
            best = (key, {'slug': slug, 'title': html.unescape(title), 'url': '/newsroom/%s/' % slug, 'publishedAt': m.group(2)})
    return best and best[1]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--live'); ap.add_argument('--label', default=''); ap.add_argument('--off', action='store_true')
    ap.add_argument('--published-at', help='override latestArticle.publishedAt (ISO, e.g. 2026-11-09T18:00:00-05:00)')
    a = ap.parse_args()
    d = json.load(open(LIVE)) if os.path.exists(LIVE) else {}
    d.setdefault('live', False); d.setdefault('liveUrl', ''); d.setdefault('liveLabel', '')
    n = newest()
    if n:
        if a.published_at: n['publishedAt'] = a.published_at
        d['latestArticle'] = n
    if a.live: d.update(live=True, liveUrl=a.live, liveLabel=a.label)
    if a.off: d.update(live=False, liveUrl='', liveLabel='')
    out = {'live': d['live'], 'liveUrl': d['liveUrl'], 'liveLabel': d['liveLabel'], 'latestArticle': d.get('latestArticle', {})}
    open(LIVE, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
