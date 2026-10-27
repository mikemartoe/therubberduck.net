"""Unsigned Trucker Hat special-order photos (Oct 26 2026, umbrella policy): White, Navy, Gold, Tiffany Blue, Hot Pink.
Printful has no such Richardson 112 blank, so these are made exactly like the signed trucker fronts
(tools/make_signed_hat_front_photos.py, same recolor code copied below): the real Printful Heather Grey/White mockup with only
the front crown and bill fabric re-tinted to match the dad-hat photo of the same color. NO red pill (the pill on the bill is
the signed design). New files only: store-img/duck-trucker-hat-sp_<c>.{jpg,webp}; nothing existing is changed.
Usage, from the repo root:  python3 tools/make_trucker_special_photos.py"""
import os, sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as nd
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'store-img')
OUT = D
L = lambda f: np.asarray(Image.open(os.path.join(D, f)).convert('RGB')).astype(float)
A = L('duck-trucker-hat_heather-grey-white.jpg'); B = L('duck-trucker-hat_black-white.jpg')
lum = lambda x: x @ [0.299, 0.587, 0.114]
diff = np.abs(A - B).sum(2); la = lum(A)
F = nd.binary_fill_holes(nd.binary_closing(diff > 150, iterations=3))
F = F & ((diff > 90) | (la > nd.uniform_filter(la, 9) + 10))   # stitches (bright on both) stay in, to be re-tinted tonal
# the duck: keep only heather-grey-looking fabric inside its box, everything else (all threads) stays real
box = np.zeros(F.shape, bool); box[280:500, 270:540] = True
r, g, b = A[..., 0], A[..., 1], A[..., 2]; la = lum(A)
heather = (np.abs(r - g) < 12) & (np.abs(b - r) < 14) & (la > 105) & (la < 225)
emb = box & ~heather
emb = nd.binary_opening(emb, iterations=1)
lab, n = nd.label(emb); sz = nd.sum(emb, lab, range(1, n + 1)); emb = np.isin(lab, 1 + np.where(sz > 150)[0])
sil = nd.binary_fill_holes(nd.binary_closing(emb, iterations=4))   # the whole duck silhouette
emb = nd.binary_fill_holes(nd.binary_closing(emb, iterations=1))     # threads + fully enclosed gaps stay real; open notches are fabric
F = F & ~emb
lab, n = nd.label(F); s = nd.sum(F, lab, range(1, n + 1)); F = np.isin(lab, 1 + np.where(s > 40)[0])
# shading: heather speckle smoothed away (normalized blur inside the fabric), folds and light kept
Fm = F.astype(float)
def nblur(x, sg): return nd.gaussian_filter(x * Fm, sg) / np.maximum(nd.gaussian_filter(Fm, sg), 1e-3)
# low-frequency light from the grey mockup (big blur kills the heather mottling), fine seams/weave from the black mockup
# (solid twill, no heather), and the bill's contrast stitching from the grey mockup as tonal (lighter) thread.
ref = np.median(la[F])
low = nblur(la, 7.0) / ref
lb = lum(B); detB = np.clip(nblur(lb, 0.6) / np.maximum(nblur(lb, 4.0), 8), 0.55, 1.6) ** 0.55
band = nd.gaussian_filter(nd.binary_dilation(sil, iterations=7).astype(float), 2)   # the black mockup's duck has a light outline: no weave detail from it there
detB = detB * (1 - band) + band
stitch = np.clip(la - nblur(la, 3.0) - 14, 0, 80) / ref
S = low * detB
tex = stitch
REG = (slice(170, 260), slice(200, 300))              # left front panel, same spot on both hats
dadS = {'white': 'duck-dad-hat_white_product.jpg', 'navy': 'duck-dad-hat_navy_product.jpg', 'gold': 'duck-dad-hat_gold_product.jpg',
        'tiffany': 'duck-dad-hat_tiffany_product.jpg', 'hotpink': 'duck-dad-hat_hotpink_product.jpg'}
TRK = {'black': B}
m = np.asarray(Image.fromarray((F * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(0.7))).astype(float)[..., None] / 255
for k, f in dadS.items():
    dad = L(f); want = np.median(dad[REG].reshape(-1, 3), 0)
    sreg = np.median(S[REG][F[REG]])
    tgt = want / sreg
    rec = np.clip(tgt[None, None] * S[..., None] + 255 * 0.55 * tex[..., None] * (1 - tgt[None, None] / 290), 0, 255)
    out = A * (1 - m) + rec * m
    TRK[k] = out
    print(k, want.round(), tgt.round())

for c in ('white', 'navy', 'gold', 'tiffany', 'hotpink'):
    im = Image.fromarray(np.clip(TRK[c], 0, 255).round().astype('uint8'))
    f = os.path.join(OUT, 'duck-trucker-hat-sp_%s' % c)
    im.save(f + '.jpg', quality=90, optimize=True, progressive=True); im.save(f + '.webp', quality=84, method=6)
    print('wrote', f)
