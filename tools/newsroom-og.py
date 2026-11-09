#!/usr/bin/env python3
"""DUCK SAUCE per-story OG cards (1200x630 JPG) for The Rubber Duck Newsroom.

Uses Mike's six battlefield theme photos + Steelfish/Courier plate.
Writes images/newsroom/og/<slug>.jpg. Does not touch newsroom.jpg or HTML.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
import json, os, random, datetime, textwrap
from pathlib import Path

ROOT = str(Path(__file__).resolve().parents[1])
SRC = os.path.join(ROOT, 'images/newsroom/ducksauce-src')
OUT = os.path.join(ROOT, 'images/newsroom/og')
FONTS = os.path.join(ROOT, 'assets/trd/fonts')
W, H = 1200, 630

THEME = [
    '05-gi-capture-major-base.png',
    '04-vietnam-home-safe.png',
    '03-kosovo-4000.png',
    '06-accuse-portrait.png',
    '02-iraq-baghdad.png',
    '01-desert-deployment.png',
]
_theme_imgs = None

def theme_imgs():
    global _theme_imgs
    if _theme_imgs is None:
        missing = [f for f in THEME if not os.path.exists(os.path.join(SRC, f))]
        if missing:
            raise SystemExit('Missing theme photos in %s: %s (Mike\'s six; not shipped live)' % (SRC, ', '.join(missing)))
        _theme_imgs = [Image.open(os.path.join(SRC, f)).convert('RGB') for f in THEME]
    return _theme_imgs

steel_path = os.path.join(FONTS, 'Steelfish-Bd.otf')
courier_path = os.path.join(FONTS, 'CourierPrime-Bold.ttf')

def sand_bg(seed):
    random.seed(seed)
    base = Image.new('RGB', (W, H), (42, 36, 24))
    nz = Image.effect_noise((W // 3, H // 3), 46).resize((W, H), Image.Resampling.BILINEAR)
    nz = ImageOps.colorize(nz.convert('L'), (28, 24, 16), (80, 68, 42))
    bg = Image.blend(base, nz, 0.55).convert('RGBA')
    d = ImageDraw.Draw(bg)
    for y in range(0, H, 26):
        shade = 20 + (y // 26) % 3 * 4
        d.rectangle((0, y, W, y + 2), fill=(shade, shade - 4, shade - 10, 255))
    return bg

def framed(im, max_w, max_h, border=9, tone=0.98):
    im = im.copy()
    im.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    im = ImageEnhance.Color(im).enhance(0.94)
    im = ImageEnhance.Contrast(im).enhance(1.12)
    im = ImageEnhance.Brightness(im).enhance(tone)
    bw, bh = im.size
    pad = border
    card = Image.new('RGBA', (bw + pad * 2 + 6, bh + pad * 2 + 10), (0, 0, 0, 0))
    sh = Image.new('RGBA', card.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle((5, 8, card.width - 1, card.height - 1), fill=(0, 0, 0, 170))
    sh = sh.filter(ImageFilter.GaussianBlur(9))
    card.alpha_composite(sh)
    paper = Image.new('RGB', (bw + pad * 2, bh + pad * 2), (222, 208, 170))
    card.paste(paper, (0, 0))
    card.paste(im, (pad, pad))
    d = ImageDraw.Draw(card)
    d.rectangle((pad - 1, pad - 1, pad + bw, pad + bh), outline=(55, 48, 28, 220), width=2)
    cx = card.width // 2 - 3
    d.ellipse((cx - 6, 2, cx + 6, 14), fill=(130, 32, 24, 255))
    return card

def place(canvas, card, cx, cy, angle):
    r = card.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
    canvas.alpha_composite(r, (int(cx - r.width / 2), int(cy - r.height / 2)))

def layout_for(seed):
    random.seed(seed)
    # six positions around edges; shuffle order of theme photos
    order = list(range(6))
    random.shuffle(order)
    slots = [
        (0.14, 0.18, 400, 300, -5.0),
        (0.86, 0.18, 420, 320, 4.0),
        (0.90, 0.72, 380, 300, -2.5),
        (0.10, 0.70, 220, 380, 7.0),
        (0.40, 0.90, 380, 360, -3.0),
        (0.72, 0.90, 360, 280, 2.5),
    ]
    # jitter
    out = []
    for i, (cx, cy, mw, mh, ang) in enumerate(slots):
        out.append((
            order[i],
            cx + random.uniform(-0.03, 0.03),
            cy + random.uniform(-0.03, 0.03),
            int(mw * random.uniform(0.92, 1.08)),
            int(mh * random.uniform(0.92, 1.08)),
            ang + random.uniform(-1.5, 1.5),
        ))
    return out

def fdate(d):
    y, m, dd = map(int, d.split('-'))
    return datetime.date(y, m, dd).strftime('%b ').upper() + f'{dd}, {y}'

def wrap_title(draw, title, font, max_w, max_lines=5):
    # binary-search font size then wrap by words measuring width
    words = title.split()
    lines = []
    cur = ''
    for w in words:
        trial = (cur + ' ' + w).strip()
        bb = draw.textbbox((0, 0), trial, font=font)
        if bb[2] - bb[0] <= max_w:
            cur = trial
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip('.,;:') + '…'
    return lines

def fit_title(draw, title, max_w, max_h, start=72, lo=28):
    size = start
    while size >= lo:
        font = ImageFont.truetype(steel_path, size)
        lines = wrap_title(draw, title, font, max_w)
        # measure total height
        total = 0
        widths = []
        for ln in lines:
            bb = draw.textbbox((0, 0), ln, font=font)
            widths.append(bb[2] - bb[0])
            total += bb[3] - bb[1] + int(size * 0.12)
        if total <= max_h and max(widths) <= max_w:
            return font, lines, size
        size -= 2
    font = ImageFont.truetype(steel_path, lo)
    return font, wrap_title(draw, title, font, max_w), lo

def make_card(job, seed):
    slug = job['slug']
    title = job['title']  # exact
    kind = job['kind']
    label = 'ARTICLE' if kind == 'article' else ('THREAD' if 'thread' in slug else 'COMMENTARY')
    if slug.startswith('epstein-dentist'):
        label = 'REPUBLISHED'
    words = job.get('words')
    date = fdate(job['date'])
    meta = f"{label}  ·  {date}"
    if words:
        meta += f"  ·  {words:,} WORDS"

    bg = sand_bg(seed)
    for idx, cx, cy, mw, mh, ang in layout_for(seed):
        place(bg, framed(theme_imgs()[idx], mw, mh), int(cx * W), int(cy * H), ang)
    bg = Image.alpha_composite(bg, Image.new('RGBA', (W, H), (8, 7, 5, 105)))
    canvas = bg.convert('RGB')

    # plate — leave room on right for optional story image pin
    has_img = bool(job.get('img'))
    pw = 780 if has_img else 900
    ph = 470
    plate = Image.new('RGB', (pw, ph), (214, 198, 158))
    noise = Image.effect_noise((pw, ph), 10).convert('RGB')
    plate = Image.blend(plate, noise, 0.06)
    grad = Image.new('L', (1, ph))
    for y in range(ph):
        grad.putpixel((0, y), int(255 - y * 18 / ph))
    warm = ImageOps.colorize(grad.resize((pw, ph)), (200, 180, 130), (230, 216, 180))
    plate = Image.blend(plate, warm, 0.35)
    pd = ImageDraw.Draw(plate)
    pd.rectangle((0, 0, pw - 1, ph - 1), outline=(42, 38, 28), width=3)
    pd.rectangle((5, 5, pw - 6, ph - 6), outline=(74, 90, 50), width=1)

    def rivet(x, y):
        pd.ellipse((x - 10, y - 10, x + 10, y + 10), fill=(90, 90, 90))
        pd.ellipse((x - 7, y - 7, x + 7, y + 7), fill=(185, 185, 185))
        pd.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(55, 55, 55))
    rivet(24, ph // 2)
    rivet(pw - 24, ph // 2)

    olive = (38, 48, 28)
    ink2 = (70, 62, 48)
    red = (140, 28, 22)
    courier = ImageFont.truetype(courier_path, 16)
    courier_sm = ImageFont.truetype(courier_path, 15)

    header = 'DUCK SAUCE · THE RUBBER DUCK NEWSROOM'
    hb = pd.textbbox((0, 0), header, font=courier)
    pd.text(((pw - (hb[2] - hb[0])) / 2, 22), header, font=courier, fill=olive)
    pd.line((60, 48, pw - 60, 48), fill=(46, 42, 31), width=1)

    # title area
    max_w = pw - 100
    max_h = 250
    # use temp draw measure
    font, lines, size = fit_title(pd, title, max_w, max_h, start=68 if len(title) < 50 else 56)
    # vertical center title block in middle of plate
    line_h = int(size * 1.05)
    block_h = line_h * len(lines)
    y0 = 70 + max(0, (250 - block_h) // 2)
    for i, ln in enumerate(lines):
        bb = pd.textbbox((0, 0), ln, font=font)
        tw = bb[2] - bb[0]
        pd.text(((pw - tw) / 2, y0 + i * line_h), ln, font=font, fill=olive)

    pd.line((70, 340, pw - 70, 340), fill=(46, 42, 31), width=2)
    pd.line((70, 345, pw - 70, 345), fill=(46, 42, 31), width=2)
    mb = pd.textbbox((0, 0), meta, font=courier_sm)
    pd.text(((pw - (mb[2] - mb[0])) / 2, 358), meta, font=courier_sm, fill=ink2)

    # stamp + domain
    stamp = 'CLASSIFIED // FOR PUBLIC RELEASE'
    sb = pd.textbbox((0, 0), stamp, font=courier_sm)
    sw, sh = sb[2] - sb[0] + 22, sb[3] - sb[1] + 12
    st = Image.new('RGBA', (sw + 20, sh + 20), (0, 0, 0, 0))
    sd = ImageDraw.Draw(st)
    sd.rectangle((4, 4, sw + 4, sh + 4), outline=(*red, 255), width=3)
    sd.text((15, 9), stamp, font=courier_sm, fill=(*red, 255))
    st = st.rotate(-2.5, expand=True, resample=Image.Resampling.BICUBIC)
    plate_rgba = plate.convert('RGBA')
    plate_rgba.alpha_composite(st, (50, 392))
    pd3 = ImageDraw.Draw(plate_rgba)
    dom = 'THERUBBERDUCK.NET'
    db = pd3.textbbox((0, 0), dom, font=courier)
    pd3.text((pw - 70 - (db[2] - db[0]), 415), dom, font=courier, fill=olive)

    # optional story image as pinned print on the right
    final = canvas.convert('RGBA')
    if has_img:
        ip = os.path.join(ROOT, job['img'].lstrip('/'))
        if os.path.exists(ip):
            sim = Image.open(ip).convert('RGB')
            scard = framed(sim, 340, 420, border=10, tone=1.0)
            scard = scard.rotate(3.5, expand=True, resample=Image.Resampling.BICUBIC)
            sx = W - scard.width - 36
            sy = (H - scard.height) // 2
            # shadow
            shad = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(shad).rectangle((sx + 8, sy + 12, sx + scard.width, sy + scard.height), fill=(0, 0, 0, 150))
            shad = shad.filter(ImageFilter.GaussianBlur(12))
            final = Image.alpha_composite(final, shad)
            final.alpha_composite(scard, (sx, sy))
            px = 40
        else:
            px = (W - pw) // 2
    else:
        px = (W - pw) // 2
    py = (H - ph) // 2 - 4
    shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rectangle((px + 8, py + 12, px + pw + 8, py + ph + 12), fill=(0, 0, 0, 160))
    shadow = shadow.filter(ImageFilter.GaussianBlur(16))
    final = Image.alpha_composite(final, shadow)
    final.alpha_composite(plate_rgba, (px, py))

    out = final.convert('RGB')
    path = os.path.join(OUT, slug + '.jpg')
    out.save(path, 'JPEG', quality=82, optimize=True, progressive=True)
    sz = os.path.getsize(path)
    if sz > 200_000:
        for q in (78, 74, 70, 66):
            out.save(path, 'JPEG', quality=q, optimize=True, progressive=True)
            sz = os.path.getsize(path)
            if sz <= 200_000:
                break
    print(f'{slug}: {sz/1024:.1f}KB title_size={size} lines={len(lines)}')
    return path

def load_jobs(path=None):
    if path is None:
        path = str(Path(ROOT) / 'tools' / 'ds-og-jobs.json')
    with open(path) as f:
        return json.load(f)

def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description='Build DUCK SAUCE newsroom OG cards')
    ap.add_argument('slug', nargs='*', help='Limit to these slug(s); default: all in jobs file')
    ap.add_argument('--jobs', default=None, help='Jobs JSON path (default: tools/ds-og-jobs.json)')
    args = ap.parse_args(argv)
    jobs = load_jobs(args.jobs)
    if args.slug:
        want = set(args.slug)
        jobs = [j for j in jobs if j['slug'] in want]
        missing = want - {j['slug'] for j in jobs}
        if missing:
            raise SystemExit('unknown slug(s): ' + ', '.join(sorted(missing)))
    for i, job in enumerate(jobs):
        # stable seed by slug so re-running one card matches full-batch look
        seed = 100 + sorted(j['slug'] for j in load_jobs(args.jobs)).index(job['slug']) * 17
        make_card(job, seed=seed)
    print('done', len(jobs))

if __name__ == '__main__':
    main()
