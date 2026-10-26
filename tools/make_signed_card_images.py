"""Square store-card photos for the three signed listings in the new six-color lineup (Oct 26 2026, branch umbrella-special-orders).
Signed tee: the Red Pill Tee front photo (store-img/demo/duck-tee_<c>_front.jpg, 800x1300), padded onto its own gray studio backdrop.
Signed hats: NOT built here any more (Oct 26 2026, Mike: front views only). The old crop of the signed demo still showed a malformed
held-up hat; the hat cards are now the approved front product photos, see tools/make_signed_hat_front_photos.py.
Output: store-img/signed-tee_<c>.{jpg,webp}, 800x800."""
from PIL import Image
import os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'store-img')
COLORS = ['black', 'white', 'navy', 'gold', 'tiffany', 'hotpink']
def save(im, stem):
    im = im.resize((800, 800), Image.LANCZOS)
    im.save(os.path.join(D, stem + '.jpg'), quality=86, optimize=True, progressive=True)
    im.save(os.path.join(D, stem + '.webp'), quality=82, method=6)
for c in COLORS:
    t = Image.open(os.path.join(D, 'demo', 'duck-tee_%s_front.jpg' % c)).convert('RGB')
    top, bot = 190, 1130                       # the shirt and its shadow
    crop = t.crop((0, top, 800, bot)); s = bot - top
    sq = Image.new('RGB', (s, s))
    for y in range(s):                         # the backdrop is a vertical gradient: extend each row's edge colors
        l, r = crop.getpixel((2, y)), crop.getpixel((797, y))
        sq.paste(l, (0, y, (s - 800) // 2, y + 1)); sq.paste(r, ((s - 800) // 2 + 800, y, s, y + 1))
    sq.paste(crop, ((s - 800) // 2, 0))
    save(sq, 'signed-tee_%s' % c)
print('ok')
