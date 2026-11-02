#!/usr/bin/env python3
"""Build one small share page per meme so links shared to X, Facebook and Reddit
show that meme's own preview card.

Reads memes/data/memes.json and writes:
  memes/share/<id>.html   OG/Twitter tags + redirect to memes.html#<id> (noindex)
  memes/card/<id>.jpg     1200x630 letterboxed preview, only for memes whose shape
                          would be cropped badly in a 1.91:1 card (portrait, square,
                          very wide). Other memes use their own image on R2.

v2 (2026-11-02, PREVIEW): EVERY meme now gets its own exactly-1200x630 card, memes/card2/<id>.jpg on R2
(memes.therubberduck.net), the meme letterboxed on the Meme Dump brown with a 24 px safe margin. Before, memes whose
shape was 1.3-2.4:1 linked their raw image (any size/shape, up to MBs); X, Facebook and iMessage then cover-cropped it
into their fixed ~1.91:1 frame (top/bottom or sides lost) and had to fetch and resize a big file for the preview.
Cards are written to .work/r2/memes/card2/ (gitignored) for the R2 upload; nothing is added to the GitHub repo.
Gate: python3 tools/share-card-audit.py memes --pages . --img-map https://memes.therubberduck.net/=.work/r2/ --csv ...

Run after tools/memes-intake.py:  python tools/meme-share-build.py
Re-running is safe: unchanged cards are skipped and pages for removed memes are deleted.
"""
import html, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://therubberduck.net'
MEDIA = 'https://memes.therubberduck.net/'
SHARE_DIR = os.path.join(ROOT, 'memes', 'share')
CARD_DIR = os.path.join(ROOT, '.work', 'r2', 'memes', 'card2')   # -> R2 memes/card2/
CARD_URL = MEDIA + 'memes/card2/'
SAFE_W, SAFE_H = 1152, 582        # meme area inside the card: >= 24 px from every edge (safe after a 2:1 crop)
SRC_ROOTS = [ROOT, os.path.join(os.path.dirname(ROOT), 'trd-site')]   # memes/web/ is gitignored: use any checkout that has it
CARD_W, CARD_H = 1200, 630
OK_MIN, OK_MAX = 1.3, 2.4          # aspect ratios that crop acceptably in a large card
MAX_BYTES = 5 * 1024 * 1024        # X card image limit
CT = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'gif': 'image/gif', 'webp': 'image/webp'}


def esc(s):
    return html.escape(s or '', quote=True)


def media_url(p):
    return p if p.startswith('http') else MEDIA + p.lstrip('/')


def _video_frame(video):
    """brightest of ~32 frames spread over the clip (posters that are a black first frame give a blank card)"""
    import subprocess, tempfile
    from PIL import Image, ImageStat
    try:
        dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', video],
                                   capture_output=True, text=True).stdout.strip() or 0)
    except ValueError:
        dur = 0
    times = sorted({round(dur * k / 32, 2) for k in range(1, 32)} | {0.5, 1, 2, 3}) if dur else [0.5, 1, 2, 3, 5, 8]
    best, best_m = None, -1
    for t in times:
        if dur and t >= dur: continue
        with tempfile.NamedTemporaryFile(suffix='.jpg') as f:
            r = subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', video, '-frames:v', '1', f.name], capture_output=True)
            if r.returncode or not os.path.getsize(f.name): continue
            im = Image.open(f.name).convert('RGB'); im.load()
            m = ImageStat.Stat(im.convert('L')).mean[0]
            if m > best_m: best, best_m = im, m
    return best if best is not None and best.convert('L').getextrema()[1] > 40 else None


def make_card(src, dst, video=None):
    from PIL import Image
    im = Image.open(src)
    try:
        im.seek(0)
    except Exception:
        pass
    if im.mode in ('RGBA', 'LA', 'P', 'PA'):          # transparent PNG/GIF: flatten on white (on the brown it went black)
        im = im.convert('RGBA'); white = Image.new('RGBA', im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(white, im)
    im = im.convert('RGB')
    if video and im.convert('L').getextrema()[1] <= 40:   # black poster frame -> use a visible frame of the clip
        im = _video_frame(video) or im
    bg = Image.new('RGB', (CARD_W, CARD_H), (20, 14, 9))
    s = min(SAFE_W / im.width, SAFE_H / im.height)
    nw, nh = max(1, int(im.width * s)), max(1, int(im.height * s))
    bg.paste(im.resize((nw, nh), Image.LANCZOS), ((CARD_W - nw) // 2, (CARD_H - nh) // 2))
    bg.save(dst, 'JPEG', quality=82, optimize=True, progressive=True)


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
<script>location.replace("/memes.html"+location.search+{hashjs});</script>
<style>body{{margin:0;background:#140e09;color:#f6e3b4;font:16px/1.5 system-ui,sans-serif;display:grid;place-items:center;min-height:100vh}}a{{color:#e3a82b}}</style>
</head><body><p>Opening the meme in <a href="{dest}">The Meme Dump</a>.</p></body></html>
'''.format(t=esc(t_full), d=esc(desc), u=esc(url), i=esc(img), ct=ctype, w=w, h=h, a=esc(alt),
           dest=esc(dest), hashjs=json.dumps('#' + mid))


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
            dst = os.path.join(CARD_DIR, mid + '.jpg')
            make_card(os.path.join(ROOT, 'images', 'brand', 'trd-share-2026.jpg'), dst)
            new_man[mid] = 'site-card'; cards.add(mid + '.jpg')
            out = page(it, CARD_URL + mid + '.jpg', 1200, 630, 'image/jpeg')
            open(os.path.join(SHARE_DIR, mid + '.html'), 'w', encoding='utf-8').write(out)
            pages.add(mid + '.html')
            continue
        w, h = it.get('width') or 0, it.get('height') or 0
        if it.get('kind') == 'video':
            local = next((os.path.join(r, src) for r in SRC_ROOTS if os.path.exists(os.path.join(r, src))), os.path.join(ROOT, src))
            if os.path.exists(local):
                from PIL import Image
                w, h = Image.open(local).size
        ext = src.rsplit('.', 1)[-1].lower()
        ar = (w / h) if h else 0
        bytes_ = it.get('bytes') or 0 if it.get('kind') != 'video' else 0
        need_card = True                 # v2: every meme gets an exact 1200x630 card (was: only outside OK_MIN..OK_MAX)
        local = next((os.path.join(r, src) for r in SRC_ROOTS if os.path.exists(os.path.join(r, src))), os.path.join(ROOT, src))
        if need_card and os.path.exists(local):
            dst = os.path.join(CARD_DIR, mid + '.jpg')
            key = (it.get('sha256') or str(os.path.getmtime(local))) + ':v2b'
            if man.get(mid) != key or not os.path.exists(dst):
                vid = None
                if it.get('kind') == 'video':
                    vid = next((os.path.join(r, it['file']) for r in SRC_ROOTS if it.get('file') and os.path.exists(os.path.join(r, it['file']))), None)
                make_card(local, dst, vid)
                made += 1
            new_man[mid] = key
            cards.add(mid + '.jpg')
            img, w, h, ctype = CARD_URL + mid + '.jpg', CARD_W, CARD_H, 'image/jpeg'
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
