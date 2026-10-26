#!/usr/bin/env python3
"""Video Room share pages: writes videos/share/<id>.html for every feature in the Video Room.

Ids and titles come from the same two sources the room uses:
  - the ALL list inside videos.html (Rumble features + reposts)
  - data/video-room-local.json (file-hosted local-archive reels)

Each page is a tiny static page with og/twitter tags (tease only: title + 'Video Room · The Rubber Duck',
plus running time) and the feature's poster as the preview image. Humans are sent on to
/videos.html?<utm...>#v=<id>; the room then shows that feature on the big screen. No page ever
references the video file itself, so a link preview never loads a video.

Usage:
  python3 tools/video-share-build.py                    # poster/thumbnail as the preview image (default)
  python3 tools/video-share-build.py --cards-base URL   # use URL/<id>.jpg (1200x630 cards, e.g. after an R2 upload)
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


def preview_img(v, cards_base):
    if cards_base:
        return cards_base.rstrip('/') + '/' + v['id'] + '.jpg'
    th = (v.get('th') or '').strip()
    if not th.startswith('http') or 'intermission-card' in th:
        return FALLBACK_IMG
    return th


def page(v, img, meta):
    e = lambda s: html.escape(s, quote=True)
    vid, t = v['id'], re.sub(r'\s+', ' ', v['t']).strip()
    title = t + ' \u00b7 Video Room \u00b7 The Rubber Duck'
    bits = []
    if v.get('dur'):
        bits.append('Running time ' + v['dur'])
    bits.append('Free in the Video Room at therubberduck.net')
    desc = ' \u00b7 '.join(bits)
    url = SITE + '/videos/share/' + vid + '.html'
    dest = '/videos.html#v=' + vid
    size = ''
    m = meta.get(img)
    if m and m.get('w'):
        size = ('<meta property="og:image:width" content="%d">\n<meta property="og:image:height" content="%d">\n'
                % (m['w'], m['h']))
    alt = ('Poster frame from ' + t + ', in The Rubber Duck Video Room') if img != FALLBACK_IMG else 'The Rubber Duck Video Room'
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>{e(title)}</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex, follow">
<link rel="canonical" href="{url}">
<meta name="description" content="{e(desc)}">
<meta property="og:type" content="website">
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
<link rel="icon" href="/favicon-duck-white.ico" sizes="any">
<meta http-equiv="refresh" content="0; url={dest}">
<script>location.replace("/videos.html"+location.search+"#v={vid}");</script>
<style>body{{margin:0;background:#04060d;color:#f3e6c8;font:16px/1.5 system-ui,sans-serif;display:grid;place-items:center;min-height:100vh;text-align:center;padding:0 20px}}a{{color:#ffc864}}</style>
</head><body><p>Opening {e(t)} in <a href="{dest}">the Video Room</a>.</p></body></html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cards-base', default='')
    ap.add_argument('--img-meta', default='')
    a = ap.parse_args()
    meta = json.load(open(a.img_meta)) if a.img_meta else {}
    feats, nr, nl, dups = load_features()
    outdir = os.path.join(ROOT, 'videos', 'share')
    os.makedirs(outdir, exist_ok=True)
    keep = set()
    for v in feats:
        fn = v['id'] + '.html'
        keep.add(fn)
        with open(os.path.join(outdir, fn), 'w', encoding='utf-8') as f:
            f.write(page(v, preview_img(v, a.cards_base), meta))
    stale = [f for f in os.listdir(outdir) if f.endswith('.html') and f not in keep]
    for f in stale:
        os.remove(os.path.join(outdir, f))
    print('wrote %d share pages (%d Rumble list entries incl. reposts, %d local archive; %d ids listed twice: %s); removed %d stale'
          % (len(feats), nr, nl, len(dups), ', '.join(dups), len(stale)))


if __name__ == '__main__':
    main()
