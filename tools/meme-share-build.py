#!/usr/bin/env python3
"""Build one small share page per meme so links shared to X, Facebook and Reddit
show that meme's own preview card.

Reads memes/data/memes.json and writes:
  memes/share/<id>.html   OG/Twitter tags + redirect to memes.html#<id> (noindex)
  memes/card/<id>.jpg     1200x630 letterboxed preview, only for memes whose shape
                          would be cropped badly in a 1.91:1 card (portrait, square,
                          very wide). Other memes use their own image on R2.

Run after tools/memes-intake.py:  python tools/meme-share-build.py
Re-running is safe: unchanged cards are skipped and pages for removed memes are deleted.
"""
import html, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://therubberduck.net'
MEDIA = 'https://memes.therubberduck.net/'
SHARE_DIR = os.path.join(ROOT, 'memes', 'share')
CARD_DIR = os.path.join(ROOT, 'memes', 'card')
CARD_W, CARD_H = 1200, 630
OK_MIN, OK_MAX = 1.3, 2.4          # aspect ratios that crop acceptably in a large card
MAX_BYTES = 5 * 1024 * 1024        # X card image limit
CT = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'gif': 'image/gif', 'webp': 'image/webp'}


def esc(s):
    return html.escape(s or '', quote=True)


def media_url(p):
    return p if p.startswith('http') else MEDIA + p.lstrip('/')


def make_card(src, dst):
    from PIL import Image
    im = Image.open(src)
    try:
        im.seek(0)
    except Exception:
        pass
    im = im.convert('RGB')
    bg = Image.new('RGB', (CARD_W, CARD_H), (20, 14, 9))
    s = min(CARD_W / im.width, CARD_H / im.height)
    nw, nh = max(1, int(im.width * s)), max(1, int(im.height * s))
    bg.paste(im.resize((nw, nh), Image.LANCZOS), ((CARD_W - nw) // 2, (CARD_H - nh) // 2))
    bg.save(dst, 'JPEG', quality=72, optimize=True, progressive=True)


def page(it, img, w, h, ctype):
    mid = it['id']
    title = (it.get('title') or mid).strip()
    topics = [t for t in (it.get('topics') or [])][:4]
    kind = 'clip' if it.get('kind') == 'video' else ('GIF' if it.get('ext') == 'gif' else 'meme')
    t_full = '%s | The Meme Dump | The Rubber Duck\u2122' % title
    desc = 'A %s from The Rubber Duck\'s Meme Dump%s. Open it, download it or share it at therubberduck.net.' % (
        kind, (': ' + ', '.join(topics)) if topics else '')
    url = '%s/memes/share/%s.html' % (SITE, mid)
    dest = '/memes.html#' + mid
    alt = '%s, from The Rubber Duck Meme Dump' % title
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
<meta property="og:image:width" content="{w}">
<meta property="og:image:height" content="{h}">
<meta property="og:image:alt" content="{a}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@TheRubberDuck79">
<meta name="twitter:title" content="{t}">
<meta name="twitter:description" content="{d}">
<meta name="twitter:image" content="{i}">
<meta name="twitter:image:alt" content="{a}">
<meta http-equiv="refresh" content="0; url={dest}">
<script>location.replace({destjs});</script>
<style>body{{margin:0;background:#140e09;color:#f6e3b4;font:16px/1.5 system-ui,sans-serif;display:grid;place-items:center;min-height:100vh}}a{{color:#e3a82b}}</style>
</head><body><p>Opening the meme in <a href="{dest}">The Meme Dump</a>.</p></body></html>
'''.format(t=esc(t_full), d=esc(desc), u=esc(url), i=esc(img), ct=ctype, w=w, h=h, a=esc(alt),
           dest=esc(dest), destjs=json.dumps(dest))


def main():
    data = json.load(open(os.path.join(ROOT, 'memes', 'data', 'memes.json'), encoding='utf-8'))
    items = data['items'] if isinstance(data, dict) else data
    os.makedirs(SHARE_DIR, exist_ok=True)
    os.makedirs(CARD_DIR, exist_ok=True)
    man_path = os.path.join(CARD_DIR, '_cards.json')
    man = json.load(open(man_path)) if os.path.exists(man_path) else {}
    new_man, pages, cards, made, warn = {}, set(), set(), 0, []
    for it in items:
        mid = it['id']
        src = it.get('poster') if it.get('kind') == 'video' else it.get('file')
        if not src:
            warn.append(mid + ': no image or poster, using the site card')
            out = page(it, SITE + '/images/brand/trd-share-2026.jpg', 1200, 630, 'image/jpeg')
            open(os.path.join(SHARE_DIR, mid + '.html'), 'w', encoding='utf-8').write(out)
            pages.add(mid + '.html')
            continue
        w, h = it.get('width') or 0, it.get('height') or 0
        if it.get('kind') == 'video':
            local = os.path.join(ROOT, src)
            if os.path.exists(local):
                from PIL import Image
                w, h = Image.open(local).size
        ext = src.rsplit('.', 1)[-1].lower()
        ar = (w / h) if h else 0
        bytes_ = it.get('bytes') or 0 if it.get('kind') != 'video' else 0
        need_card = not (OK_MIN <= ar <= OK_MAX) or ext not in CT or bytes_ > MAX_BYTES
        local = os.path.join(ROOT, src)
        if need_card and os.path.exists(local):
            dst = os.path.join(CARD_DIR, mid + '.jpg')
            key = it.get('sha256') or str(os.path.getmtime(local))
            if man.get(mid) != key or not os.path.exists(dst):
                make_card(local, dst)
                made += 1
            new_man[mid] = key
            cards.add(mid + '.jpg')
            img, w, h, ctype = '%s/memes/card/%s.jpg' % (SITE, mid), CARD_W, CARD_H, 'image/jpeg'
        else:
            if need_card:
                warn.append(mid + ': no local file for a card, using the original')
            img, ctype = media_url(src), CT.get(ext, 'image/jpeg')
        p = mid + '.html'
        out = page(it, img, w, h, ctype)
        fp = os.path.join(SHARE_DIR, p)
        if not os.path.exists(fp) or open(fp, encoding='utf-8').read() != out:
            open(fp, 'w', encoding='utf-8').write(out)
        pages.add(p)
    for f in os.listdir(SHARE_DIR):
        if f.endswith('.html') and f not in pages:
            os.remove(os.path.join(SHARE_DIR, f))
    for f in os.listdir(CARD_DIR):
        if f.endswith('.jpg') and f not in cards:
            os.remove(os.path.join(CARD_DIR, f))
    json.dump(new_man, open(man_path, 'w'), indent=0, sort_keys=True)
    print('share pages: %d  cards: %d (%d rebuilt)' % (len(pages), len(cards), made))
    for w_ in warn:
        print('note:', w_)


if __name__ == '__main__':
    sys.exit(main())
