"""Demo media (video + photo per color) shown under a shop listing's facts, in an "In the box" section.
One color tab row per listing; tapping a color swaps the video and photo. Muted autoplay loop, Sound button.
Files: /store-img/demo/<slug>_<color>_demo.{mp4,jpg,webp} (720x1280, 8 s).
Used by tools/seo-build.py build_shop(); keep markup self-contained (archive.css is shared by every archive page)."""
import html, os, sys
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

def _figs(slug, kind, key, label, poster=None):
    b = '/store-img/demo/%s_%s_demo' % (slug, key)
    pb = poster or b
    a = html.escape('%s, %s, lifted above the TRD box' % (kind, label))
    return ('<figure class="dm"><div class="dm-v"><video src="%s.mp4" poster="%s.jpg" width="720" height="1280" muted loop playsinline autoplay preload="metadata" aria-label="%s"></video>'
            '<button type="button" class="dm-snd" aria-pressed="false" aria-label="Turn sound on">Sound on</button></div>'
            '<figcaption><span class="dm-c">%s</span> &middot; video</figcaption></figure>'
            '<figure class="dm"><picture><source srcset="%s.webp" type="image/webp"><img src="%s.jpg" alt="%s" width="720" height="1280" loading="lazy" decoding="async"></picture>'
            '<figcaption><span class="dm-c">%s</span> &middot; photo</figcaption></figure>') % (b, pb, a, label, b, b, a, label)

def demo_block(slug):
    entry = DEMO_MEDIA.get(slug)
    if not entry:
        return ''
    kind, extra, keys = entry[:3]
    posters = entry[3] if len(entry) > 3 else {}
    cols = [c for c in COLORS if c[0] in keys]
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
           '.dms{display:flex;flex-wrap:wrap;gap:14px}.dm{margin:0;flex:1 1 220px;max-width:300px}'
           '.dm video,.dm img{display:block;width:100%;height:auto;aspect-ratio:9/16;object-fit:cover;border-radius:6px;border:1px solid var(--line);background:#111}'
           '.dm-v{position:relative}.dm-snd{position:absolute;right:8px;bottom:8px;font:700 13px/1 system-ui,sans-serif;color:#140e05;background:var(--gold);border:0;border-radius:999px;padding:8px 12px;cursor:pointer;opacity:.92}'
           '.dm-snd[aria-pressed="true"]{background:var(--ink)}.dm figcaption{color:var(--muted);font-size:13px;margin-top:6px}'
           '@media(max-width:640px){.dms{gap:10px}.dm{flex-basis:calc(50% - 5px)}}</style>')
    js = ('<script>(function(){var rm=window.matchMedia&&matchMedia("(prefers-reduced-motion: reduce)").matches;'
          'document.querySelectorAll(".dmx").forEach(function(x){var s=x.getAttribute("data-slug"),v=x.querySelector("video"),b=x.querySelector(".dm-snd"),'
          'src=x.querySelector("source"),img=x.querySelector("img"),tabs=x.querySelectorAll(".dm-t");'
          'if(rm){v.removeAttribute("autoplay");v.pause();}'
          'function setb(){b.setAttribute("aria-pressed",String(!v.muted));b.setAttribute("aria-label",v.muted?"Turn sound on":"Mute");b.textContent=v.muted?"Sound on":"Mute";}'
          'b.addEventListener("click",function(){v.muted=!v.muted;if(!v.muted){document.querySelectorAll(".dmx video").forEach(function(o){if(o!==v)o.muted=true;});v.play();}setb();});'
          'tabs.forEach(function(t){t.addEventListener("click",function(){if(t.getAttribute("aria-selected")==="true")return;'
          'tabs.forEach(function(o){o.setAttribute("aria-selected",String(o===t));});'
          'var c=t.getAttribute("data-c"),l=t.getAttribute("data-l"),p="/store-img/demo/"+s+"_"+c+"_demo",a=x.getAttribute("data-kind")+", "+l+", lifted above the TRD box";'
          'v.poster=t.getAttribute("data-p")||p+".jpg";v.src=p+".mp4";v.setAttribute("aria-label",a);src.srcset=p+".webp";img.src=p+".jpg";img.alt=a;'
          'x.querySelectorAll(".dm-c").forEach(function(e){e.textContent=l;});if(!rm||!v.muted)v.play().catch(function(){});});});});})();</script>')
    # Signed listings sell the full six-color lineup (some as special orders, tools/umbrella_lineup.py); the unsigned hats don't yet.
    sp = (U.SIGNED.get(slug) or {}).get('special')
    if sp:
        avail = 'Every color shown can be ordered; %s %s special orders (up to 7 extra days). ' % (html.escape(_and(sp)), 'is a' if len(sp) == 1 else 'are')
    else:
        avail = 'New colors are being added to the lineup; the colors you can order today are listed above. '
    cap = ('<p class="meta">The demo shows the %s in each color: %s. %s%s'
           'Demo music from The Red Pill Album (&ldquo;The Storm Is Upon Us&rdquo;).</p>') % (kind.lower(), html.escape(names_txt), extra, avail)
    return ('<h2>In the box</h2>' + css +
            '<div class="dmx" data-slug="%s" data-kind="%s"><div class="dm-tabs" role="tablist" aria-label="Demo color">%s</div><div class="dms">%s</div>%s</div>'
            % (ms, html.escape(kind), tabs, _figs(ms, kind, k0, l0, posters.get(k0)), cap) + js)

# ---------------------------------------------------------------- listing gallery: one main photo per color with color tabs
# Red Pill Tee: Mike's front + back mock (Oct 26 2026) in six colors, landscape 1600x982 (+900 w), made by tools/make_tee_mock_images.py.
# Shown as the listing's main photo, full width above the facts; the frame has the photo's own aspect ratio, so nothing is cropped or letterboxed.
# Not used on signed-tee (the mock has no signature). The colors you can order are still the ones in merch.html.
GALLERY_COLORS = [
    ('black', 'Black', '#141414'),
    ('white', 'White', '#f3f2ee'),
    ('navy', 'Navy', '#1f2a44'),
    ('gold', 'Gold', '#d9a50a'),
    ('tiffany', 'Tiffany Blue', '#81d8d0'),
    ('hotpink', 'Hot Pink', '#dd1e78'),
]
# Oct 26 2026 (Mike): all six colors are sold. Tiffany Blue and Hot Pink are SPECIAL ORDERS under the umbrella rule (tools/umbrella_lineup.py:
# up to 7 extra days to source and make it; card authorized, not charged, until the maker confirms; hold released / every penny refunded
# if it can't be made within those 7 days) on their own Stripe links (merch.html size options carry data-special-link). Keep in step with merch.html.
SPECIAL_COLORS = {'tiffany', 'hotpink'}
SPECIAL_NOTE = ('Tiffany Blue and Hot Pink are special orders: we take up to 7 extra days to source and make yours. Your card is only authorized, '
                'not charged, until a maker confirms it. If we can&rsquo;t make it within those 7 days, the hold is released at once and you pay nothing. '
                'You&rsquo;ll be asked to agree at checkout.')
# slug -> (product name for alt text, file stem under /store-img/demo/, width, height)
GALLERY = {
    'duck-tee': ('Red Pill Tee', 'duck-tee', 1600, 982),
}

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
            'Tiffany Blue and Hot Pink are special orders (up to 7 extra days).</figcaption></figure></div>'
            % (stem, html.escape(name), w, tabs, pic, html.escape(l0), html.escape(', '.join(names[:-1]) + ' and ' + names[-1]))) + js

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
            colors=html.escape(_and(special_colors)), verb='is a' if len(special_colors) == 1 else 'are',
            signed=', then it&rsquo;s signed and numbered by hand' if signed else '',
            total='3 to 4 weeks' if signed else '2 to 3 weeks')
        lead = ('If it&rsquo;s listed here, it&rsquo;s ours to deliver. Every other color ships on the normal schedule above.')
    else:
        sp = ''
        lead = ('If it&rsquo;s listed here, it&rsquo;s ours to deliver. Every piece is made for your order. If anything ever stops us making yours, '
                'we take up to 7 extra days to source it, and if we can&rsquo;t, every penny comes back to you.')
    return (PROMISE_CSS + '<section class="trd-promise" aria-labelledby="pr-%s"><h2 id="pr-%s">%s</h2><p>%s</p>%s</section>'
            % (slug, slug, U.PROMISE_TITLE, lead, sp))
