"""Square store-card photos for the three signed listings in the new six-color lineup (Oct 26 2026, branch umbrella-special-orders).
Signed tee: the Red Pill Tee front photo (store-img/demo/duck-tee_<c>_front.jpg, 800x1300), padded onto its own gray studio backdrop.
Signed hats: a square crop of the signed demo still (store-img/demo/signed-<hat>_<c>_demo.jpg, 720x1280) around the hat, the real
No. 11/500 signature under the brim and the TRD box. Output: store-img/signed-<item>_<c>.{jpg,webp}, 800x800."""
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
    for hat in ('signed-dad-hat', 'signed-trucker-hat'):
        h = Image.open(os.path.join(D, 'demo', '%s_%s_demo.jpg' % (hat, c))).convert('RGB')
        save(h.crop((0, 165, 720, 885)), '%s_%s' % (hat, c))
print('ok')
