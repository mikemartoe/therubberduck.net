#!/usr/bin/env python3
import argparse, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path('/workspace/trd-site')
TRACKS = ROOT / 'data/album/tracks.json'
OUT_DIR = ROOT / 'images/album/og'

W, H = 1200, 630

def font(name, size):
    return ImageFont.truetype(str(ROOT / 'fonts' / name), size)

def wrap_lines(draw, text, fnt, max_w):
    words = text.split()
    lines = []
    cur = ''
    for w in words:
        cand = (cur + ' ' + w).strip()
        if draw.textbbox((0, 0), cand, font=fnt)[2] <= max_w:
            cur = cand
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def render_card(track, cover_img, avatar_img, out_path):
    # Blurred dark crimson-black backdrop from the cover art
    bg = cover_img.resize((W, W), Image.Resampling.LANCZOS).crop((0, (W - H)//2, W, (W - H)//2 + H))
    bg = bg.filter(ImageFilter.GaussianBlur(28)).convert('RGBA')
    shade = Image.new('RGBA', (W, H), (5, 5, 5, 212))
    canvas = Image.alpha_composite(bg, shade)

    # Subtle crimson radial wash on left
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for r, a in [(380, 42), (280, 36), (180, 28)]:
        gd.ellipse((280 - r, 315 - r, 280 + r, 315 + r), fill=(225, 6, 0, a))
    glow = glow.filter(ImageFilter.GaussianBlur(40))
    canvas = Image.alpha_composite(canvas, glow)

    d = ImageDraw.Draw(canvas)
    # Top crimson accent bar
    d.rectangle((0, 0, W, 6), fill=(225, 6, 0, 255))

    # Left square cover art (460x460)
    art_size = 456
    art_x, art_y = 64, (H - art_size) // 2
    # Shadow
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle(
        (art_x - 4, art_y + 8, art_x + art_size + 4, art_y + art_size + 14),
        radius=16, fill=(0, 0, 0, 170)
    )
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    canvas = Image.alpha_composite(canvas, sh)

    art = cover_img.resize((art_size, art_size), Image.Resampling.LANCZOS).convert('RGBA')
    mask = Image.new('L', (art_size, art_size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, art_size, art_size), radius=12, fill=255)
    canvas.paste(art, (art_x, art_y), mask)

    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle((art_x, art_y, art_x + art_size, art_y + art_size), radius=12, outline=(72, 22, 22, 255), width=2)

    # Right column
    rx = art_x + art_size + 52
    rw = W - rx - 64

    f_kicker = font('JetBrainsMono.ttf', 19)
    f_album = font('Roboto-Bold.ttf', 24)
    f_meta = font('Roboto-Regular.ttf', 22)
    f_foot = font('Roboto-Bold.ttf', 20)
    f_pill = font('Roboto-Bold.ttf', 17)

    # Kicker badge
    kicker = f"track {track['n']:02d} of 22  ·  the red pill room"
    kb = d.textbbox((0, 0), kicker, font=f_kicker)
    kw = (kb[2] - kb[0]) + 28
    d.rounded_rectangle((rx, 96, rx + kw, 134), radius=6, fill=(26, 8, 8, 255), outline=(225, 6, 0, 200), width=1)
    d.text((rx + 14, 104), kicker, font=f_kicker, fill=(255, 59, 65, 255))

    # Song title (Steelfish Bd / fallback sizing)
    title = track['title']
    title_size = 94
    while title_size >= 52:
        f_title = font('Steelfish Bd.otf', title_size)
        tlines = wrap_lines(d, title, f_title, rw)
        if len(tlines) <= 2 and all(d.textbbox((0, 0), ln, font=f_title)[2] <= rw for ln in tlines):
            break
        title_size -= 6

    ty = 166
    lh = int(title_size * 1.02)
    for ln in tlines:
        d.text((rx, ty), ln, font=f_title, fill=(255, 255, 255, 255))
        ty += lh

    # Artist & Album line
    d.text((rx, ty + 14), "The Rubber Duck™  ·  The Red Pill Album", font=f_album, fill=(228, 228, 228, 255))
    d.text((rx, ty + 50), f"{track['len']}  ·  synced lyrics & player", font=f_meta, fill=(185, 185, 185, 255))

    # CTA pill
    pill_y = max(ty + 94, 362)
    pill_txt = "listen + read lyrics"
    pb = d.textbbox((0, 0), pill_txt, font=f_pill)
    pw = (pb[2] - pb[0]) + 34
    d.rounded_rectangle((rx, pill_y, rx + pw, pill_y + 40), radius=20, fill=(225, 6, 0, 255))
    d.text((rx + 17, pill_y + 10), pill_txt, font=f_pill, fill=(255, 255, 255, 255))

    # Footer separator + unaltered avatar + site URL
    fy = 516
    d.line((rx, fy - 18, W - 64, fy - 18), fill=(42, 18, 18, 255), width=2)
    av_sz = 46
    av = avatar_img.resize((av_sz, av_sz), Image.Resampling.LANCZOS).convert('RGBA')
    av_mask = Image.new('L', (av_sz, av_sz), 0)
    ImageDraw.Draw(av_mask).ellipse((0, 0, av_sz, av_sz), fill=255)
    canvas.paste(av, (rx, fy), av_mask)
    d.ellipse((rx, fy, rx + av_sz, fy + av_sz), outline=(225, 6, 0, 255), width=2)

    d.text((rx + av_sz + 14, fy + 2), "therubberduck.net/album/enjoy-the-show/" if track['n'] == 4 else f"therubberduck.net/album/{track['slug']}/", font=f_foot, fill=(255, 255, 255, 255))
    d.text((rx + av_sz + 14, fy + 26), "free in the red pill room", font=font('Roboto-Regular.ttf', 16), fill=(185, 185, 185, 255))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert('RGB').save(out_path, 'JPEG', quality=92, optimize=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--track', type=int, help='Track number to render (default: all with shareUrl)')
    args = ap.parse_args()
    data = json.loads(TRACKS.read_text())
    cover = Image.open(ROOT / 'images/opt/album-cover-card.jpg')
    avatar = Image.open(ROOT / 'images/duck-avatar.jpg')
    for tr in data['tracks']:
        if args.track and tr['n'] != args.track:
            continue
        if not args.track and not tr.get('shareUrl'):
            continue
        out = OUT_DIR / f"{tr['fileId']}.jpg"
        render_card(tr, cover, avatar, out)
        print('Rendered', out)

if __name__ == '__main__':
    main()
