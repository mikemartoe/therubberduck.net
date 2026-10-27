"""Demo media (video + photo per color) shown under a shop listing's facts, in an "In the box" section.
One color tab row per listing; tapping a color swaps the video and photo. Muted autoplay loop, Sound button.
Files: /store-img/demo/<slug>_<color>_demo.{mp4,jpg,webp} (720x1280, 8 s).
Used by tools/seo-build.py build_shop(); keep markup self-contained (archive.css is shared by every archive page)."""
import html, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import umbrella_lineup as U

def _and(xs):
    xs = list(xs)
    return ', '.join(xs[:-1]) + ' and ' + xs[-1] if len(xs) > 1 else xs[0]

# The six demo colors (Mike, Oct 25 2026: show the full color set; colors are being added to the lineup).
COLORS = [
    ('black', 'Black', '#111111'),
    ('white', 'White', '#f3f2ee'),
    ('tiffany', 'Tiffany Blue', '#81d8d0'),
    ('hotpink', 'Hot Pink', '#ff2a8a'),
    ('navy', 'Navy', '#1d2b4f'),
    ('gold', 'Gold', '#c9a43a'),
]

# Signed listings: the signature in the demo is the real one from a signed hat photo (No. 11 of 500), composited, never redrawn.
_FRONT = 'The demo shows the front; your hat is signed and numbered by hand under the brim. '
_SIG = 'The signature under the brim in the demo is taken from a real signed hat (No. 11 of 500); yours carries its own hand-written number. '

def _posters(base_slug, own):
    """Poster per color: signed demo videos open on the same unsigned frame as the base listing's demo,
    so they use that listing's photo as poster; colors in `own` open on the signed photo itself."""
    return {c[0]: None if c[0] in own else '/store-img/demo/%s_%s_demo' % (base_slug, c[0]) for c in COLORS}

# slug -> (what the demo shows, extra caption sentence or '', list of color keys that have media[, {color: poster base or None}])
DEMO_MEDIA = {
    'duck-trucker-hat': ('Trucker hat', '', [c[0] for c in COLORS]),
    'duck-dad-hat': ('Dad hat', '', [c[0] for c in COLORS]),
    # Oct 26 2026 (Mike): the signed hats show the FRONT only. The old signed demos (store-img/demo/signed-*_demo.*, a hat held up
    # to show the brim) are no longer used anywhere; the signed listings play the regular hat's front demo instead (MEDIA_SLUG).
    'signed-dad-hat': ('Dad hat', _FRONT, [c[0] for c in COLORS]),
    'signed-trucker-hat': ('Trucker hat', _FRONT, [c[0] for c in COLORS]),
}
MEDIA_SLUG = {'signed-dad-hat': 'duck-dad-hat', 'signed-trucker-hat': 'duck-trucker-hat'}

# The small signed-brim preview (a real signed hat, No. 11 of 500) on the signed hat listings: a secondary tile, never the main photo.
SIG_PREVIEW = set()  # back-of-hat renderings removed on Mike's order; never re-add
def sig_preview(slug):
    if slug not in SIG_PREVIEW:
        return ''
    return ('<style>.sigp{display:flex;align-items:center;gap:12px;margin:4px 0 14px;max-width:420px}'
            '.sigp picture{flex:0 0 auto}.sigp img{display:block;width:112px;height:112px;object-fit:cover;border-radius:8px;border:1px solid var(--gold,#c9a43a);box-shadow:0 2px 10px rgba(0,0,0,.35)}'
            '.sigp figcaption{color:var(--muted);font-size:14px;line-height:1.4}</style>'
            '<figure class="sigp"><picture><source srcset="/store-img/signed-brim-11of500.webp" type="image/webp">'
            '<img src="/store-img/signed-brim-11of500.jpg" alt="The brim of a signed hat, marked 11/500 TRD" width="480" height="480" loading="lazy" decoding="async"></picture>'
            '<figcaption>Signed and numbered under the brim, out of 500. Shown: No. 11; yours carries its own number.</figcaption></figure>')

# ---------------------------------------------------------------- signature example, on every signed listing (Oct 26 2026, Mike)
# Mike's own photo of a real signed hat (white marker "11/500 -TRD" under a navy brim): shown ONLY as an example of what the hand-written
# number and signature look like; the copy says so and never promises a number. Files: store-img/signature-example-11-500_{592,360}.{jpg,webp}
# (592 = Mike's photo, pixels untouched, metadata stripped; 360 = downscale). This is a real photo, not one of the back-of-hat renderings
# Mike had removed (SIG_PREVIEW above stays empty).
SIG_EXAMPLE = {
    'signed-dad-hat': ('Your hat is signed and numbered by hand under the brim, out of 500.',),
    'signed-trucker-hat': ('Your hat is signed and numbered by hand under the brim, out of 500.',),
    'signed-tee': ('Your tee is signed and numbered by hand too, out of 500. The photo shows the signature on a hat, as an example of the hand.',),
}
SIG_CSS = ('<style>.sigx{display:grid;grid-template-columns:minmax(0,296px) minmax(0,1fr);gap:24px;align-items:center;margin:20px 0 22px;padding:16px;'
           'border:1px solid var(--gold);border-radius:8px;background:linear-gradient(135deg,rgba(201,164,58,.10),rgba(0,0,0,0) 55%);'
           'box-shadow:inset 0 0 0 3px rgba(0,0,0,.25),inset 0 0 0 4px rgba(200,155,60,.45)}'
           '.sigx-f{margin:0}.sigx-p{display:block;aspect-ratio:592/584;border:1px solid var(--gold);border-radius:6px;overflow:hidden;background:#1a1c22;'
           'box-shadow:0 6px 18px rgba(0,0,0,.45)}.sigx-p img{display:block;width:100%;height:100%;object-fit:cover}'
           '.sigx-k{margin:0 0 8px;font-size:13px;letter-spacing:.24em;text-transform:uppercase;color:var(--gold)}'
           '.sigx-t{margin:0 0 10px;font-size:1.22rem;line-height:1.35;color:var(--ink)}.sigx-t b{color:var(--gold)}'
           '.sigx-d{margin:0;line-height:1.5;color:var(--muted)}.sigx-d+.sigx-d{margin-top:8px}'
           '@media(max-width:640px){.sigx{grid-template-columns:1fr;gap:14px;padding:12px}.sigx-t{font-size:1.1rem}}</style>')

def sig_example_block(slug):
    e = SIG_EXAMPLE.get(slug)
    if not e:
        return ''
    b = '/store-img/signature-example-11-500'
    return (SIG_CSS + '<section class="sigx" aria-labelledby="sx-%s">'
            '<figure class="sigx-f"><span class="sigx-p"><picture><source type="image/webp" srcset="%s_360.webp 360w, %s_592.webp 592w" sizes="(max-width: 640px) calc(100vw - 62px), 296px">'
            '<img src="%s_592.jpg" srcset="%s_360.jpg 360w, %s_592.jpg 592w" sizes="(max-width: 640px) calc(100vw - 62px), 296px" '
            'alt="Example of the hand-written number and signature: 11/500 -TRD in white marker under the brim of a navy hat" width="592" height="584" loading="lazy" decoding="async"></picture></span></figure>'
            '<div><h2 class="sigx-k" id="sx-%s">Signed and numbered by hand</h2>'
            '<p class="sigx-t"><b>Example:</b> your number and signature are written by hand, like this.</p>'
            '<p class="sigx-d">%s</p>'
            '<p class="sigx-d">Shown: No. 11 of 500, under the brim of a navy hat. It is an example only; yours carries its own hand-written number.</p></div></section>'
            % (slug, b, b, b, b, b, slug, e[0]))

def _figs(slug, kind, key, label, poster=None):
    b = '/store-img/demo/%s_%s_demo' % (slug, key)
    pb = poster or b
    a = html.escape('%s, %s, lifted above the TRD box' % (kind, label))
    return ('<figure class="dm"><div class="dm-v"><video src="%s.mp4" poster="%s.jpg" width="720" height="1280" muted loop playsinline autoplay preload="metadata" aria-label="%s"></video>'
            '<button type="button" class="dm-snd" aria-pressed="false" aria-label="Turn sound on">Sound on</button></div>'
            '<figcaption><span class="dm-c">%s</span></figcaption></figure>') % (b, pb, a, label)

def demo_block(slug):
    entry = DEMO_MEDIA.get(slug)
    if not entry:
        return ''
    kind, extra, keys = entry[:3]
    posters = entry[3] if len(entry) > 3 else {}
    lab = (U.TRUCKER.get(slug) or {}).get('demo_label', {})   # e.g. the trucker's black demo IS the Black / White hat
    cols = [(k, lab.get(k, l), sw) for k, l, sw in COLORS if k in keys]
    names = [c[1] for c in cols]
    names_txt = ', '.join(names[:-1]) + ' and ' + names[-1] if len(names) > 1 else names[0]
    tabs = ''.join('<button type="button" role="tab" class="dm-t" data-c="%s" data-l="%s"%s aria-selected="%s" style="--sw:%s"><i></i>%s</button>'
                   % (k, html.escape(l), (' data-p="%s.jpg"' % posters[k]) if posters.get(k) else '', 'true' if i == 0 else 'false', sw, html.escape(l))
                   for i, (k, l, sw) in enumerate(cols))
    k0, l0, _ = cols[0]
    ms = MEDIA_SLUG.get(slug, slug)   # whose demo files to play
    css = ('<style>.dmx{margin:6px 0 10px}.dm-tabs{display:flex;gap:8px;overflow-x:auto;padding:2px 2px 10px;scrollbar-width:thin;-webkit-overflow-scrolling:touch}'
           '.dm-t{flex:0 0 auto;display:inline-flex;align-items:center;gap:7px;font:600 14px/1 system-ui,sans-serif;color:var(--ink);background:transparent;border:1px solid var(--line);border-radius:999px;padding:9px 13px 9px 9px;cursor:pointer;min-height:40px}'
           '.dm-t i{width:18px;height:18px;border-radius:50%;background:var(--sw);box-shadow:inset 0 0 0 1px rgba(128,128,128,.55)}'
           '.dm-t[aria-selected="true"]{border-color:var(--gold);box-shadow:0 0 0 1px var(--gold) inset}'
           '.dms{display:flex;flex-wrap:wrap;gap:14px}.dm{margin:0;flex:1 1 220px;max-width:340px}'
           '.dm video,.dm img{display:block;width:100%;height:auto;aspect-ratio:9/16;object-fit:cover;border-radius:6px;border:1px solid var(--line);background:#111}'
           '.dm-v{position:relative}.dm-snd{position:absolute;right:8px;bottom:8px;font:700 13px/1 system-ui,sans-serif;color:#140e05;background:var(--gold);border:0;border-radius:999px;padding:8px 12px;cursor:pointer;opacity:.92}'
           '.dm-snd[aria-pressed="true"]{background:var(--ink)}.dm figcaption{color:var(--muted);font-size:13px;margin-top:6px}'
           '@media(max-width:640px){.dms{gap:10px}.dm{flex-basis:calc(50% - 5px)}}</style>')
    js = ('<script>(function(){var rm=window.matchMedia&&matchMedia("(prefers-reduced-motion: reduce)").matches;'
          'document.querySelectorAll(".dmx").forEach(function(x){var s=x.getAttribute("data-slug"),v=x.querySelector("video"),b=x.querySelector(".dm-snd"),'
          'tabs=x.querySelectorAll(".dm-t");'
          'if(rm){v.removeAttribute("autoplay");v.pause();}'
          'function setb(){b.setAttribute("aria-pressed",String(!v.muted));b.setAttribute("aria-label",v.muted?"Turn sound on":"Mute");b.textContent=v.muted?"Sound on":"Mute";}'
          'b.addEventListener("click",function(){v.muted=!v.muted;if(!v.muted){document.querySelectorAll(".dmx video").forEach(function(o){if(o!==v)o.muted=true;});v.play();}setb();});'
          'tabs.forEach(function(t){t.addEventListener("click",function(){if(t.getAttribute("aria-selected")==="true")return;'
          'tabs.forEach(function(o){o.setAttribute("aria-selected",String(o===t));});'
          'var c=t.getAttribute("data-c"),l=t.getAttribute("data-l"),p="/store-img/demo/"+s+"_"+c+"_demo",a=x.getAttribute("data-kind")+", "+l+", lifted above the TRD box";'
          'v.poster=t.getAttribute("data-p")||p+".jpg";v.src=p+".mp4";v.setAttribute("aria-label",a);'
          'x.querySelectorAll(".dm-c").forEach(function(e){e.textContent=l;});if(x._pick)x._pick(c);if(!rm||!v.muted)v.play().catch(function(){});});});});})();</script>')
    # Signed listings sell the full six-color lineup (some as special orders, tools/umbrella_lineup.py); the unsigned hats don't yet.
    # Every color in the demo can be ordered (Oct 26 2026, hat colors): the special-order ones per tools/umbrella_lineup.py.
    sp = (U.SIGNED.get(slug) or U.UNSIGNED.get(slug) or U.TRUCKER.get(slug) or {}).get('special')
    if sp:
        avail = 'Every color shown can be ordered above; %s %s special orders (up to 7 extra days). ' % (html.escape(_and(sp)), 'is a' if len(sp) == 1 else 'are')
        if lab.get('black'):
            avail = 'Black is the %s (black front, white mesh). ' % html.escape(lab['black']) + avail
    else:
        avail = 'The colors you can order are listed above. '
    cap = ('<p class="meta">The demo shows the %s in each color: %s. %s%s'
           'Demo music from The Red Pill Album (&ldquo;The Storm Is Upon Us&rdquo;).</p>') % (kind.lower(), html.escape(names_txt), extra, avail)
    return ('<h2>In the box</h2>' + css +
            '<div class="dmx" data-slug="%s" data-kind="%s"><div class="dm-tabs" role="tablist" aria-label="Demo color">%s</div><div class="dms">%s</div>%s</div>'
            % (ms, html.escape(kind), tabs, _figs(ms, kind, k0, l0, posters.get(k0)), cap) + js)

# ---------------------------------------------------------------- listing gallery: one main photo per color with color tabs
# Red Pill Tee: Mike's front + back mock (Oct 26 2026) in six colors, landscape 1600x982 (+900 w), made by tools/make_tee_mock_images.py.
# Shown as the listing's main photo, full width above the facts; the frame has the photo's own aspect ratio, so nothing is cropped or letterboxed.
# Signed Duck Tee (Oct 26 2026, branch shirts-audit): same print front + back, so it reuses the same approved mock files; the caption says the
# signature is added by hand (the mock shows the print only). The colors you can order are still the ones in merch.html.
GALLERY_COLORS = [
    ('black', 'Black', '#141414'),
    ('white', 'White', '#f3f2ee'),
    ('navy', 'Navy', '#1f2a44'),
    ('gold', 'Gold', '#d9a50a'),
    ('tiffany', 'Tiffany Blue', '#81d8d0'),
    ('hotpink', 'Hot Pink', '#dd1e78'),
]
# Oct 26 2026 (Mike): all six colors are sold. Tiffany Blue and Hot Pink are SPECIAL ORDERS under the umbrella rule (tools/umbrella_lineup.py:
# standard time plus up to 7 extra days; card authorized, not charged, until we confirm the order; hold released / every penny refunded
# if it can't be made within those 7 days) on their own Stripe links (merch.html size options carry data-special-link). Keep in step with merch.html.
SPECIAL_COLORS = {'tiffany', 'hotpink'}
SPECIAL_NOTE = ('Tiffany Blue and Hot Pink are special orders: they ship in the standard time, plus up to 7 extra days. Your card is only authorized, '
                'not charged, until we confirm your order. If we can&rsquo;t fill it within those 7 days, the hold is released at once and you pay nothing. '
                'You&rsquo;ll be asked to agree at checkout.')
# slug -> (product name for alt text, file stem under /store-img/demo/, width, height)
GALLERY = {
    'duck-tee': ('Red Pill Tee', 'duck-tee', 1600, 982),
    'signed-tee': ('Signed Duck Tee', 'duck-tee', 1600, 982),
}
# extra caption text per listing
GALLERY_NOTE = {'signed-tee': ' Print shown; yours is signed and numbered by hand.'}

def _galt(name, label):
    return '%s in %s, front and back' % (name, label)

def gallery_images(slug):
    """[(url, alt)] for every gallery color, first color first; [] if the listing has no gallery."""
    g = GALLERY.get(slug)
    if not g:
        return []
    return [('/store-img/demo/%s_%s_mock.jpg' % (g[1], k), _galt(g[0], l)) for k, l, _ in GALLERY_COLORS]

def gallery_block(slug):
    g = GALLERY.get(slug)
    if not g:
        return ''
    name, stem, w, h = g
    k0, l0, _ = GALLERY_COLORS[0]
    b = '/store-img/demo/%s_%s_mock' % (stem, k0)
    sizes = '(max-width: 960px) calc(100vw - 36px), 924px'
    tabs = ''.join('<button type="button" role="tab" class="tg-t" data-c="%s" data-l="%s" aria-selected="%s" aria-controls="tg-%s" style="--sw:%s"><i></i>%s</button>'
                   % (k, html.escape(l), 'true' if i == 0 else 'false', stem, sw, html.escape(l)) for i, (k, l, sw) in enumerate(GALLERY_COLORS))
    names = [c[1] for c in GALLERY_COLORS]
    css = ('<style>.tg{margin:4px 0 18px}.tg-f{margin:0}.tg-p{display:block;position:relative;aspect-ratio:%d/%d;background:#666;border:1px solid var(--line);border-radius:8px;overflow:hidden}'
           '.tg-p img{display:block;width:100%%;height:100%%;object-fit:contain}'
           '.tg-tabs{display:flex;flex-wrap:wrap;gap:8px;padding:2px 2px 10px}'
           '.tg-t{flex:0 0 auto;display:inline-flex;align-items:center;gap:7px;font:600 14px/1 system-ui,sans-serif;color:var(--ink);background:transparent;border:1px solid var(--line);border-radius:999px;padding:9px 13px 9px 9px;cursor:pointer;min-height:40px}'
           '.tg-t i{width:18px;height:18px;border-radius:50%%;background:var(--sw);box-shadow:inset 0 0 0 1px rgba(128,128,128,.55)}'
           '.tg-t[aria-selected="true"]{border-color:var(--gold);box-shadow:0 0 0 1px var(--gold) inset}'
           '.tg figcaption{color:var(--muted);font-size:13px;margin-top:6px}.doc.tg-doc{grid-template-columns:1fr}</style>') % (w, h)
    pic = ('<div class="tg-p" id="tg-%s" role="tabpanel"><picture><source type="image/webp" srcset="%s-900.webp 900w, %s.webp %dw" sizes="%s">'
           '<img src="%s.jpg" srcset="%s-900.jpg 900w, %s.jpg %dw" sizes="%s" alt="%s" width="%d" height="%d" decoding="async" fetchpriority="high"></picture></div>'
           % (stem, b, b, w, sizes, b, b, b, w, sizes, html.escape(_galt(name, l0)), w, h))
    js = ('<script>(function(){document.querySelectorAll(".tg").forEach(function(x){var st=x.getAttribute("data-stem"),nm=x.getAttribute("data-name"),w=x.getAttribute("data-w"),'
          'src=x.querySelector("source"),img=x.querySelector("img"),cap=x.querySelector(".tg-c"),tabs=x.querySelectorAll(".tg-t");'
          'function base(t){return "/store-img/demo/"+st+"_"+t.getAttribute("data-c")+"_mock";}'
          'function ss(p,e){return p+"-900."+e+" 900w, "+p+"."+e+" "+w+"w";}'
          'tabs.forEach(function(t){function pre(){if(t._p)return;t._p=1;var i=new Image();i.sizes=img.sizes;i.srcset=ss(base(t),"webp");}'
          't.addEventListener("pointerenter",pre);t.addEventListener("focus",pre);t.addEventListener("touchstart",pre,{passive:true});'
          't.addEventListener("click",function(){if(t.getAttribute("aria-selected")==="true")return;tabs.forEach(function(o){o.setAttribute("aria-selected",String(o===t));});'
          'var p=base(t),l=t.getAttribute("data-l"),n=++x._n,i=new Image();cap.textContent=l;'
          # decode the new photo first, then swap, so the frame never shows an empty gray box while it loads
          'if(x._pick)x._pick(t.getAttribute("data-c"),l);'
          'function sw(){if(n!==x._n)return;src.srcset=ss(p,"webp");img.srcset=ss(p,"jpg");img.src=p+".jpg";img.alt=nm+" in "+l+", front and back";}'
          'i.sizes=img.sizes;i.srcset=ss(p,(img.currentSrc||"").slice(-5)===".webp"?"webp":"jpg");(i.decode?i.decode():Promise.reject()).then(sw,sw);});});x._n=0;});})();</script>')
    return (css + '<div class="tg" data-stem="%s" data-name="%s" data-w="%d">'
            '<div class="tg-tabs" role="tablist" aria-label="Tee color">%s</div>'
            '<figure class="tg-f">%s<figcaption><span class="tg-c">%s</span> &middot; front (left) and back (right). Sold in %s; '
            'Tiffany Blue and Hot Pink are special orders (up to 7 extra days).%s</figcaption></figure></div>'
            % (stem, html.escape(name), w, tabs, pic, html.escape(l0), html.escape(', '.join(names[:-1]) + ' and ' + names[-1]), GALLERY_NOTE.get(slug, ''))) + js

def order_block(slug, sizes):
    """Red Pill Tee listing: color (follows the gallery tabs) + size + Buy, wired per color. sizes = [(size, link, cents, special_link)]."""
    if slug not in GALLERY or not sizes:
        return ''
    k0, l0, _ = GALLERY_COLORS[0]
    copts = ''.join('<option value="%s"%s>%s%s</option>' % (k, ' data-special="1"' if k in SPECIAL_COLORS else '', html.escape(l), ' (special order)' if k in SPECIAL_COLORS else '')
                    for k, l, _ in GALLERY_COLORS)
    def dol(c):
        return '$' + ('%.2f' % (c / 100)).rstrip('0').rstrip('.')
    sopts = ''.join('<option value="%s" data-link="%s" data-special-link="%s" data-price="%d"%s>%s %s</option>' % (
        html.escape(z), html.escape(l), html.escape(sl or ''), c, ' selected' if z == 'L' else '', html.escape(z), dol(c)) for z, l, c, sl in sizes)
    l_default = next((l for z, l, c, sl in sizes if z == 'L'), sizes[0][1])
    css = ('<style>.tg-o{display:flex;flex-wrap:wrap;align-items:flex-end;gap:10px 14px;margin:6px 0 14px}.tg-o label{display:flex;flex-direction:column;gap:4px;font:600 13px/1.2 system-ui,sans-serif;color:var(--muted)}'
           '.tg-o select{font:16px system-ui,sans-serif;padding:9px 10px;border:1px solid var(--line);border-radius:8px;background:#fff;color:#111;min-width:9em}'
           '.tg-o .btn{margin:0}.tg-n{flex-basis:100%;margin:0;padding:9px 12px;border:2px solid #c8202b;border-radius:8px;background:#fff4d6;color:#2a1a0a;font-size:14px;line-height:1.35}'
           '.tg-n b{color:#c8202b}.tg-n[hidden]{display:none}</style>')
    js = ('<script>(function(){var o=document.querySelector(".tg-o");if(!o)return;var c=o.querySelector(".tg-oc"),z=o.querySelector(".tg-oz"),b=o.querySelector(".tg-ob"),n=o.querySelector(".tg-n"),'
          'g=document.querySelector(".tg");'
          'function sl(s){return String(s).toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"")}'
          'function sync(){var co=c.options[c.selectedIndex],so=z.options[z.selectedIndex],sp=co.hasAttribute("data-special"),'
          'l=(sp&&so.getAttribute("data-special-link"))||so.getAttribute("data-link");n.hidden=!sp;'
          'b.href=l+"?client_reference_id="+encodeURIComponent(["%s",sl(co.textContent.replace(" (special order)","")),sl(z.value)].join("_"));}'
          'c.addEventListener("change",function(){var t=g&&g.querySelector(\'.tg-t[data-c="\'+c.value+\'"]\');if(t&&t.getAttribute("aria-selected")!=="true")t.click();sync();});'
          'z.addEventListener("change",sync);if(g)g._pick=function(k){if(c.value!==k){c.value=k;}sync();};sync();})();</script>') % slug
    return (css + '<div class="tg-o" aria-label="Order this tee"><label>Color<select class="tg-oc">%s</select></label>'
            '<label>Size<select class="tg-oz">%s</select></label><a class="btn tg-ob" href="%s" rel="noopener">Buy now through Stripe</a>'
            '<p class="tg-n" role="note" hidden><b>SPECIAL ORDER</b> %s</p></div>' % (copts, sopts, html.escape(l_default), SPECIAL_NOTE)) + js

# ---------------------------------------------------------------- the TRD Promise (umbrella special-order rule), on every listing
PROMISE_CSS = ('<style>.trd-promise{margin:18px 0 22px;padding:14px 18px 15px;border:1px solid var(--gold);border-radius:8px;'
               'box-shadow:inset 0 0 0 3px rgba(0,0,0,.25),inset 0 0 0 4px rgba(200,155,60,.45)}'
               '.trd-promise h2{margin:0 0 6px;font-size:13px;letter-spacing:.24em;text-transform:uppercase;color:var(--gold)}'
               '.trd-promise p{margin:0;line-height:1.5}.trd-promise p+p{margin-top:8px}</style>')

def promise_block(slug, special_colors, signed, has_gallery=False):
    """The promise on a listing page. Listings with special-order colors also spell out the special-order terms."""
    if special_colors:
        sp = '<p><b>Special order.</b> %s</p>' % U.LISTING_SPECIAL.format(
            colors=html.escape(_and(special_colors)), verb='is a special order' if len(special_colors) == 1 else 'are special orders',
            signed=' (signed and numbered by hand)' if signed else '',
            std=U.STD_SHIP_SIGNED if signed else U.STD_SHIP_UNSIGNED)
        lead = ('If it&rsquo;s listed here, it&rsquo;s ours to deliver. Every other color ships on the normal schedule above.')
    else:
        sp = ''
        lead = ('If it&rsquo;s listed here, it&rsquo;s ours to deliver. Every piece is made for your order and ships in our standard time. If anything '
                'ever holds up yours, it may take up to 7 extra days, and if we can&rsquo;t fill it, every penny comes back to you.')
    return (PROMISE_CSS + '<section class="trd-promise" aria-labelledby="pr-%s"><h2 id="pr-%s">%s</h2><p>%s</p>%s</section>'
            % (slug, slug, U.PROMISE_TITLE, lead, sp))

# ---------------------------------------------------------------- hat listings: buy any color shown, on the right link (Oct 26 2026)
# Every color on a hat card in merch.html is buyable from the listing itself: regular colors on the regular Stripe link, special-order
# colors (data-special="1", tools/umbrella_lineup.py) on the hat's special-order link (card hold, consent at checkout). The client_reference_id
# is <slug>_<color>_one-size, exactly what the store card sends. Picking a color swaps the listing photo (the card's own photo for that
# color) and the demo video tab when the demo has that color; picking a demo tab picks the color here.
HAT_SLUGS = ('duck-dad-hat', 'duck-trucker-hat', 'signed-dad-hat', 'signed-trucker-hat')

def _demo_key(slug, label):
    lab = (U.TRUCKER.get(slug) or {}).get('demo_label', {})
    for k, l, _ in COLORS:
        if lab.get(k, l) == label:
            return k
    return ''

HAT_CSS = ('<style>.doc.ho-doc{grid-template-columns:minmax(0,400px) 1fr;gap:28px}.ho-doc img.prod{width:100%;max-width:400px;background:#efece4}'
           '.ho{margin:16px 0 14px;padding:16px 18px 14px;border:1px solid var(--gold);border-radius:10px;'
           'background:linear-gradient(160deg,rgba(227,168,43,.09),rgba(0,0,0,0) 60%);box-shadow:inset 0 0 0 3px rgba(0,0,0,.25),inset 0 0 0 4px rgba(200,155,60,.4)}'
           '.ho-k{margin:0 0 4px;font-size:13px;letter-spacing:.24em;text-transform:uppercase;color:var(--gold)}'
           '.ho-sel{margin:0 0 10px;font-size:1.15rem}.ho-sel b{color:var(--ink)}'
           '.ho-tag{display:inline-block;margin-left:8px;padding:3px 8px;border-radius:999px;background:#c8202b;color:#fff;font:700 11px/1.2 system-ui,sans-serif;letter-spacing:.08em;text-transform:uppercase;vertical-align:2px}'
           '.ho-tag[hidden]{display:none}.ho-g{margin:0 0 10px}.ho-gl{display:block;margin:0 0 6px;color:var(--muted);font-size:13px}'
           '.ho-sw{display:flex;flex-wrap:wrap;gap:8px}'
           '.ho-c{display:inline-flex;align-items:center;gap:8px;font:600 14px/1 system-ui,sans-serif;color:var(--ink);background:rgba(0,0,0,.18);border:1px solid var(--line);'
           'border-radius:999px;padding:8px 13px 8px 8px;min-height:40px;cursor:pointer}'
           '.ho-c i{width:20px;height:20px;border-radius:50%;background:linear-gradient(135deg,var(--sa) 50%,var(--sb) 50%);box-shadow:inset 0 0 0 1px rgba(128,128,128,.6)}'
           '.ho-c:hover{border-color:#8a6a2a}.ho-c[aria-checked="true"]{border-color:var(--gold);box-shadow:0 0 0 1px var(--gold) inset;background:rgba(227,168,43,.12)}'
           '.ho-c:focus-visible{outline:2px solid var(--gold);outline-offset:2px}'
           '.ho-buy{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:10px 16px;margin:14px 0 0;padding-top:12px;border-top:1px solid var(--line)}'
           '.ho-p{margin:0;line-height:1.3}.ho-amt{font-size:1.5rem;font-weight:800;color:var(--ink)}.ho-sh{color:var(--muted);font-size:14px}'
           '.ho-t{display:block;color:var(--muted);font-size:13px}.ho .btn{margin:0;padding:12px 20px;font-size:1rem}'
           '.ho-n{margin:12px 0 0;padding:9px 12px;border:2px solid #c8202b;border-radius:8px;background:#fff4d6;color:#2a1a0a;font-size:14px;line-height:1.4}'
           '.ho-n b{color:#c8202b}.ho-n[hidden]{display:none}.ho-w{margin:10px 0 0;color:var(--muted);font-size:13px}.ho-w a{color:var(--muted)}'
           '@media(max-width:640px){.doc.ho-doc{grid-template-columns:1fr;gap:14px}.ho-doc img.prod{max-width:100%}.ho{padding:14px 12px 12px}'
           '.ho-buy{flex-direction:column;align-items:stretch}.ho .btn{text-align:center}}</style>')

def hat_order_block(slug, it):
    """it = parse_merch() item (needs swatches, special_base, price, ship, signed, shipin, name)."""
    sw = it.get('swatches') or []
    if slug not in HAT_SLUGS or not sw:
        return ''
    signed = it['signed']
    sp_ship = U.SPECIAL_SHIP.get(slug, it['ship'])
    def pill(s, first):
        lab, img, spc, sa, sb = s
        return ('<button type="button" role="radio" class="ho-c" aria-checked="%s" data-l="%s" data-img="%s" data-d="%s"%s style="--sa:%s;--sb:%s"><i></i>%s</button>'
                % ('true' if first else 'false', html.escape(lab), html.escape(img), _demo_key(slug, lab), ' data-sp="1"' if spc else '', sa, sb, html.escape(lab)))
    std = [s for s in sw if not s[2]]; spc = [s for s in sw if s[2]]
    groups = '<div class="ho-g"><span class="ho-gl">%s</span><div class="ho-sw" role="radiogroup" aria-label="Regular colors">%s</div></div>' % (
        'Regular colors &middot; ships in %s' % (U.STD_SHIP_SIGNED if signed else U.STD_SHIP_UNSIGNED), ''.join(pill(s, i == 0) for i, s in enumerate(std)))
    if spc:
        if not it.get('special_base'):
            raise SystemExit('hat listing %s has special colors but no data-special-base link' % slug)
        groups += ('<div class="ho-g"><span class="ho-gl">Special order &middot; ships in %s, plus up to 7 extra days</span>'
                   '<div class="ho-sw" role="radiogroup" aria-label="Special-order colors">%s</div></div>') % (
            U.STD_SHIP_SIGNED if signed else U.STD_SHIP_UNSIGNED, ''.join(pill(s, False) for s in spc))
    note = ('<b>SPECIAL ORDER</b> <span class="ho-nc"></span> is a special order: it ships in %s%s, plus up to 7 extra days. '
            'Your card is only authorized, not charged, until we confirm your order. If we can&rsquo;t fill it within those 7 days, the hold is released '
            'at once and you pay nothing. You&rsquo;ll be asked to agree at checkout.') % (
        U.STD_SHIP_SIGNED if signed else U.STD_SHIP_UNSIGNED, ' (signed and numbered by hand)' if signed else '')
    label = 'Buy the signed one through Stripe' if signed else 'Buy now through Stripe'
    # runs after the page is parsed: the demo block (.dmx) comes after this block in the page
    js = ('<script>(function(){function init(){document.querySelectorAll(".ho").forEach(function(o){var s=o.getAttribute("data-slug"),nm=o.getAttribute("data-name"),'
          'b=o.querySelector(".ho-b"),cn=o.querySelector(".ho-cn"),tg=o.querySelector(".ho-tag"),n=o.querySelector(".ho-n"),nc=o.querySelector(".ho-nc"),'
          'sh=o.querySelector(".ho-sh"),tt=o.querySelector(".ho-t"),w=o.querySelector(".ho-wt"),ps=o.querySelectorAll(".ho-c"),'
          'pr=parseFloat(o.getAttribute("data-price")),im=document.querySelector(".ho-doc img.prod"),so=im&&im.parentNode.querySelector("source"),x=document.querySelector(".dmx");'
          'function sl(v){return String(v).toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"")}'
          'function m(v){return "$"+(v%1?v.toFixed(2):String(v))}'
          'function pick(p,fd){ps.forEach(function(q){q.setAttribute("aria-checked",String(q===p))});var l=p.getAttribute("data-l"),sp=p.hasAttribute("data-sp"),'
          'k=p.getAttribute("data-img"),d=p.getAttribute("data-d"),h=parseFloat(o.getAttribute(sp?"data-sp-ship":"data-ship")),'
          'lk=o.getAttribute(sp?"data-sp-base":"data-base");'
          'b.href=lk+"?client_reference_id="+encodeURIComponent([s,sl(l),"one-size"].join("_"));b.setAttribute("data-link",lk);'
          'cn.textContent=l;nc.textContent=l;tg.hidden=!sp;n.hidden=!sp;sh.textContent="+ "+m(h)+" US shipping"+(sp?" (special order)":"");'
          'tt.textContent="Total "+m(Math.round((pr+h)*100)/100)+" with shipping";w.textContent=o.getAttribute(sp?"data-sp-when":"data-when");'
          'if(im&&k){so.srcset="/store-img/"+k+".webp";im.src="/store-img/"+k+".jpg";im.alt=nm+" - "+l}'
          'if(!fd&&d&&x){var t=x.querySelector(\'.dm-t[data-c="\'+d+\'"]\');if(t&&t.getAttribute("aria-selected")!=="true")t.click();}}'
          'ps.forEach(function(p){p.addEventListener("click",function(){pick(p)});p.addEventListener("keydown",function(e){var a=[].slice.call(ps),i=a.indexOf(p),j=-1;'
          'if(e.key==="ArrowRight"||e.key==="ArrowDown")j=(i+1)%a.length;if(e.key==="ArrowLeft"||e.key==="ArrowUp")j=(i-1+a.length)%a.length;if(j>=0){e.preventDefault();a[j].focus();pick(a[j]);}})});'
          'if(x)x._pick=function(c){var p=o.querySelector(\'.ho-c[data-d="\'+c+\'"]\');if(p&&p.getAttribute("aria-checked")!=="true")pick(p,1)};'
          'pick(o.querySelector(\'.ho-c[aria-checked="true"]\')||ps[0],1);});}'
          'if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);else init();})();</script>')
    first = (std or spc)[0]
    tot = float(it['price']) + float(it['ship'])
    return (HAT_CSS + '<section class="ho" aria-labelledby="ho-%s" data-slug="%s" data-name="%s" data-price="%s" data-ship="%s" data-sp-ship="%s" '
            'data-base="%s" data-sp-base="%s" data-when="%s" data-sp-when="%s">'
            '<h2 class="ho-k" id="ho-%s">Choose your color</h2>'
            '<p class="ho-sel">Color: <b class="ho-cn">%s</b><span class="ho-tag" hidden>Special order</span></p>%s'
            '<div class="ho-buy"><p class="ho-p"><span class="ho-amt">$%s</span> <span class="ho-sh">+ $%s US shipping</span><span class="ho-t">Total $%s with shipping</span></p>'
            '<a class="btn ho-b" href="%s?client_reference_id=%s" rel="noopener">%s</a></div>'
            '<p class="ho-n" role="note" hidden>%s</p>'
            '<p class="ho-w"><span class="ho-wt">%s</span> &middot; One size, %s. <a href="/merch.html">See it in the store</a></p></section>'
            % (slug, slug, html.escape(it['name']), it['price'], it['ship'], sp_ship, html.escape(it['buy']), html.escape(it.get('special_base') or it['buy']),
               'Ships in ' + (U.STD_SHIP_SIGNED if signed else U.STD_SHIP_UNSIGNED), U.special_when(signed),
               slug, html.escape(first[0]), groups, it['price'], it['ship'], ('%.2f' % tot), html.escape(it['buy']),
               '%s_%s_one-size' % (slug, re.sub(r'[^a-z0-9]+', '-', first[0].lower()).strip('-')), label, note,
               'Ships in ' + (U.STD_SHIP_SIGNED if signed else U.STD_SHIP_UNSIGNED), 'snapback' if 'trucker' in slug else 'adjustable')) + js
