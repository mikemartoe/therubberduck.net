#!/usr/bin/env python3
"""Build DUCK SAUCE battlefield collage WebPs from Mike's six soldier+Stars-and-Stripes photos.

Default photo dir: images/newsroom/ducksauce-src/ (not shipped on the live site).
Override with --src. Writes collage-desktop.webp + collage-mobile.webp under --out.
"""
from __future__ import annotations
import argparse, os, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ORDER = [
    "01-desert-deployment.png",
    "02-iraq-baghdad.png",
    "03-kosovo-4000.png",
    "04-vietnam-home-safe.png",
    "05-gi-capture-major-base.png",
    "06-accuse-portrait.png",
]

def sand_bg(W, H, seed):
    random.seed(seed)
    base = Image.new("RGB", (W, H), (42, 36, 24))
    nz = Image.effect_noise((W // 3, H // 3), 48).resize((W, H), Image.Resampling.BILINEAR)
    nz = ImageOps.colorize(nz.convert("L"), (28, 24, 16), (78, 68, 42))
    bg = Image.blend(base, nz, 0.55)
    d = ImageDraw.Draw(bg)
    for y in range(0, H, 28):
        shade = 18 + (y // 28) % 3 * 4
        d.rectangle((0, y, W, y + 2), fill=(shade, shade - 4, shade - 10))
    return bg.convert("RGBA")

def framed(im, max_w, max_h, border=14, tone=0.92):
    im = im.copy()
    im.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    im = ImageEnhance.Color(im).enhance(0.88)
    im = ImageEnhance.Contrast(im).enhance(1.08)
    im = ImageEnhance.Brightness(im).enhance(tone)
    bw, bh = im.size
    pad = border
    card = Image.new("RGBA", (bw + pad * 2 + 6, bh + pad * 2 + 10), (0, 0, 0, 0))
    sh = Image.new("RGBA", card.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle((5, 8, card.width - 1, card.height - 1), fill=(0, 0, 0, 170))
    sh = sh.filter(ImageFilter.GaussianBlur(9))
    card.alpha_composite(sh)
    paper = Image.new("RGB", (bw + pad * 2, bh + pad * 2), (222, 208, 170))
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

def darken(im, amount=0.5):
    return Image.alpha_composite(im, Image.new("RGBA", im.size, (8, 7, 5, int(255 * amount))))

def build(srcs, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    # desktop
    random.seed(7)
    W, H = 1920, 1080
    bg = sand_bg(W, H, 7)
    layout = [
        (0, 0.22, 0.28, 980, 700, -6.5),
        (5, 0.72, 0.26, 1000, 720, 5.0),
        (2, 0.48, 0.52, 900, 680, -2.0),
        (1, 0.18, 0.72, 720, 900, 7.0),
        (3, 0.55, 0.82, 980, 680, -4.5),
        (4, 0.85, 0.70, 860, 620, 3.5),
    ]
    for idx, cx, cy, mw, mh, ang in layout:
        place(bg, framed(srcs[idx], mw, mh, border=16, tone=0.9), int(cx * W), int(cy * H), ang)
    out = ImageEnhance.Color(darken(bg, 0.52).convert("RGB"),).enhance(0.92) if False else ImageEnhance.Color(darken(bg, 0.52).convert("RGB")).enhance(0.92)
    path = out_dir / "collage-desktop.webp"
    out.save(path, "WEBP", quality=74, method=6)
    print("desktop", out.size, path.stat().st_size // 1024, "KB")
    # mobile
    random.seed(99)
    W, H = 1080, 2200
    bg = sand_bg(W, H, 99)
    layout = [
        (0, 0.50, 0.14, 980, 700, -3.0),
        (5, 0.48, 0.32, 980, 720, 4.0),
        (2, 0.52, 0.48, 960, 700, -5.0),
        (1, 0.35, 0.64, 700, 900, 6.0),
        (3, 0.58, 0.78, 980, 680, -3.5),
        (4, 0.45, 0.92, 960, 650, 2.5),
    ]
    for idx, cx, cy, mw, mh, ang in layout:
        place(bg, framed(srcs[idx], mw, mh, border=14, tone=0.9), int(cx * W), int(cy * H), ang)
    out = darken(bg, 0.54).convert("RGB")
    path = out_dir / "collage-mobile.webp"
    out.save(path, "WEBP", quality=74, method=6)
    print("mobile", out.size, path.stat().st_size // 1024, "KB")

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=Path, default=ROOT / "images/newsroom/ducksauce-src")
    ap.add_argument("--out", type=Path, default=ROOT / "images/newsroom")
    args = ap.parse_args(argv)
    srcs = [Image.open(args.src / f).convert("RGB") for f in ORDER]
    build(srcs, args.out)

if __name__ == "__main__":
    main()
