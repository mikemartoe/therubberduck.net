"""Premium line, COMING SOON (preview branch premium-hats, Oct 25 2026; not live until Mike approves screenshots).
Two lines, no prices and no buy buttons: they are announced, not sold.
  /shop/premium-wool-cap/     wool baseball cap, chrome duck embroidered front centre, red pill embroidered on the bill
  /shop/premium-leather-hat/  leather baseball cap, same embroidery
Also writes the "Coming Soon" section of merch.html between <!-- premium:begin --> and <!-- premium:end -->.
Images: /store-img/premium/<slug>_<color>.{jpg,webp}, 720x1280 mockups (real duck and pill art composited, not redrawn).
Used by tools/seo-build.py (build_soon). Items here never get Product/Offer JSON-LD because there is no price yet."""
import html, re
E = lambda s: html.escape(str(s), quote=True)

LINES = [
    {'slug': 'premium-wool-cap', 'name': 'Premium Wool Cap', 'kind': 'Wool cap', 'short': 'Wool',
     'made': 'Wool baseball cap, structured six-panel crown',
     'tagline': 'Real wool, felted and dense, with the chrome duck embroidered in raised thread.',
     'colors': [('navy', 'Deep Navy', '#1e2740'), ('black', 'Black', '#121212'), ('charcoal', 'Charcoal', '#3b3b3d'),
                ('ivory', 'Natural Cream', '#d9ccb0'), ('burgundy', 'Burgundy', '#5e1620')]},
    {'slug': 'premium-leather-hat', 'name': 'Premium Leather Hat', 'kind': 'Leather hat', 'short': 'Leather',
     'made': 'Leather baseball cap, six-panel crown and bill',
     'tagline': 'Full leather, top-stitched, with the chrome duck and the red pill embroidered the same way.',
     'colors': [('black', 'Black', '#151313'), ('cognac', 'Cognac', '#7a3f1d'), ('tan', 'Saddle Tan', '#b88a55')]},
]
BIO = lambda ln: [('Made', ln['made']), ('Front', 'Chrome duck, embroidered'), ('Bill', 'Red pill, embroidered'),
                  ('Colors', ', '.join(c[1] for c in ln['colors'])), ('Price', 'Announced at launch'), ('Status', 'Coming soon')]

def img(slug, key, ext='jpg'):
    return '/store-img/premium/%s_%s.%s' % (slug, key, ext)

SWAP_JS = ('<script>(function(){document.querySelectorAll("[data-soon]").forEach(function(x){var s=x.getAttribute("data-soon"),k=x.getAttribute("data-kind"),'
           'img=x.querySelector("img.ps-img"),src=x.querySelector("source.ps-src"),nm=x.querySelector(".ps-cn"),bs=x.querySelectorAll(".ps-sw");'
           'bs.forEach(function(b){b.addEventListener("click",function(){var c=b.getAttribute("data-c"),l=b.getAttribute("data-l"),p="/store-img/premium/"+s+"_"+c;'
           'bs.forEach(function(o){o.setAttribute("aria-pressed",String(o===b));});src.srcset=p+".webp";img.src=p+".jpg";img.alt=k+", "+l+", mockup, coming soon";if(nm)nm.textContent=l;});});});})();</script>')

def swatches(ln, cls='ps-sw'):
    return ''.join('<button type="button" class="%s" data-c="%s" data-l="%s" aria-pressed="%s" aria-label="%s" title="%s" style="--sw:%s"><i></i><span>%s</span></button>'
                   % (cls, k, E(l), 'true' if i == 0 else 'false', E(l), E(l), sw, E(l)) for i, (k, l, sw) in enumerate(ln['colors']))

# ---------------------------------------------------------------- merch.html section
MERCH_CSS = '''<style>
/* ============ premium line: coming soon ============ */
.vault{margin:34px 0 0;position:relative;background:radial-gradient(120% 90% at 50% 0%,#1d1710 0%,#0b0907 60%,#050404 100%);border:1px solid #6d5426;border-radius:14px;
  padding:30px 28px 30px;box-shadow:0 0 0 6px #0b0907,0 0 0 7px #8a6420,0 24px 50px rgba(0,0,0,.65);overflow:hidden}
.vault::before{content:"";position:absolute;inset:0;background-image:var(--noise);opacity:.18;pointer-events:none}
.vault .vh{position:relative;text-align:center;margin:0 auto 22px;max-width:720px}
.vault .vk{margin:0;font-family:var(--mono);font-weight:700;font-size:.82rem;letter-spacing:.42em;text-transform:uppercase;color:var(--gold2)}
.vault h2{margin:8px 0 0;font-family:Georgia,'Times New Roman',serif;font-weight:400;font-size:clamp(2rem,4.4vw,3.2rem);line-height:1.05;letter-spacing:.04em;
  background:linear-gradient(180deg,var(--gold1) 0%,var(--gold2) 55%,var(--gold3) 100%);-webkit-background-clip:text;background-clip:text;color:transparent}
.vault .vrule{display:block;width:120px;height:1px;margin:14px auto;background:linear-gradient(90deg,transparent,var(--gold2),transparent)}
.vault .vp{margin:0;color:#d8ccb2;font-size:1.02rem;line-height:1.5;text-wrap:balance}
.vgrid{position:relative;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:26px}
.soon{position:relative;background:linear-gradient(180deg,#14100b,#0c0a08);border:1px solid #3e3019;border-radius:10px;padding:14px 14px 18px;display:flex;flex-direction:column;gap:12px}
.soon .ph{position:relative;border-radius:6px;overflow:hidden;border:1px solid #4a3a1c;background:#111;aspect-ratio:9/16;max-height:620px}
.soon .ph img{display:block;width:100%;height:100%;object-fit:cover;object-position:50% 42%}
.soon .badge{position:absolute;top:12px;left:12px;font-family:var(--mono);font-weight:700;font-size:.78rem;letter-spacing:.28em;text-transform:uppercase;color:#120d05;
  background:linear-gradient(180deg,var(--gold1),var(--gold2));padding:7px 11px 6px;border-radius:3px;box-shadow:0 2px 10px rgba(0,0,0,.5)}
.soon .ttl{display:flex;align-items:baseline;justify-content:space-between;gap:10px;flex-wrap:wrap}
.soon h3{margin:0;font-family:Georgia,'Times New Roman',serif;font-weight:400;font-size:1.55rem;letter-spacing:.03em;color:var(--gold1)}
.soon .st{font-family:var(--mono);font-weight:700;font-size:.8rem;letter-spacing:.24em;text-transform:uppercase;color:var(--gold2);border:1px solid #6d5426;padding:4px 8px 3px;border-radius:3px}
.soon .tl{margin:0;color:#d8ccb2;font-size:.98rem;line-height:1.45}
.soon .cl{font-family:var(--mono);font-size:.85rem;color:#b9a985;letter-spacing:.06em}
.soon .cl b{color:#efe4c6;font-weight:700}
.ps-sws{display:flex;flex-wrap:wrap;gap:8px}
.ps-sw{display:inline-flex;align-items:center;gap:7px;min-height:38px;padding:7px 12px 7px 8px;border-radius:999px;border:1px solid #4a3a1c;background:transparent;color:#efe4c6;font:600 13px/1 var(--body);cursor:pointer}
.ps-sw i{width:18px;height:18px;border-radius:50%;background:var(--sw);box-shadow:inset 0 0 0 1px rgba(255,255,255,.25)}
.ps-sw[aria-pressed="true"]{border-color:var(--gold2);box-shadow:0 0 0 1px var(--gold2) inset}
.soon .more{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;margin-top:2px}
.soon .more a{color:var(--gold1);font-weight:700;text-decoration:none;border-bottom:1px solid #6d5426;padding-bottom:2px}
.soon .more span{color:#8f826a;font-size:.88rem}
@media(max-width:760px){.vault{padding:22px 14px 22px}.vgrid{grid-template-columns:1fr;gap:20px}.soon .ph{max-height:none}}
</style>'''

def merch_section():
    cards = []
    for ln in LINES:
        k0, l0, _ = ln['colors'][0]
        cards.append(
            '<article class="soon" data-soon="%s" data-kind="%s" aria-label="%s, coming soon">'
            '<div class="ph"><picture><source class="ps-src" srcset="%s" type="image/webp"><img class="ps-img" src="%s" alt="%s, %s, mockup, coming soon" width="720" height="1280" loading="lazy" decoding="async"></picture>'
            '<span class="badge">Coming Soon</span></div>'
            '<div class="ttl"><h3>%s</h3><span class="st">Coming Soon</span></div>'
            '<p class="tl">%s</p>'
            '<p class="cl">Color <b class="ps-cn">%s</b></p><div class="ps-sws" role="group" aria-label="Color">%s</div>'
            '<p class="more"><a href="/shop/%s/">See the %s line</a><span>Not on sale yet. Price announced at launch.</span></p>'
            '</article>' % (ln['slug'], E(ln['name']), E(ln['name']), img(ln['slug'], k0, 'webp'), img(ln['slug'], k0), E(ln['name']), E(l0),
                            E(ln['name']), E(ln['tagline']), E(l0), swatches(ln), ln['slug'], E(ln['short'].lower())))
    return ('<!-- premium:begin -->\n' + MERCH_CSS +
            '\n  <section class="vault" aria-labelledby="vault-title">\n    <header class="vh"><p class="vk">The Premium Line</p>'
            '<h2 id="vault-title">Coming Soon</h2><span class="vrule" aria-hidden="true"></span>'
            '<p class="vp">Real wool and real leather caps, embroidered the same way as the hats you know: the chrome duck front and centre, the red pill on the bill. Not on sale yet.</p></header>\n'
            '    <div class="vgrid">' + ''.join(cards) + '</div>\n  </section>\n' + SWAP_JS + '\n<!-- premium:end -->')

def update_merch(path='merch.html'):
    h = open(path, encoding='utf-8').read()
    sec = merch_section()
    if '<!-- premium:begin -->' in h:
        h2 = re.sub(r'<!-- premium:begin -->.*?<!-- premium:end -->', lambda m: sec, h, flags=re.S)
    else:  # first run: right after the shop sign, before the Glass Case
        anchor = '  <section class="case" aria-labelledby="signed-title">'
        assert anchor in h
        h2 = h.replace(anchor, sec + '\n\n' + anchor, 1)
    if h2 != h:
        open(path, 'w', encoding='utf-8').write(h2)

# ---------------------------------------------------------------- /shop/<slug>/ pages
PAGE_CSS = ('<style>.soonpg .badge{display:inline-block;font:700 12px/1 ui-monospace,Menlo,monospace;letter-spacing:.28em;text-transform:uppercase;color:#120d05;'
            'background:linear-gradient(180deg,#f6e3a1,#c89b3c);padding:7px 10px 6px;border-radius:3px;margin:0 0 10px}'
            '.soonpg .doc{grid-template-columns:minmax(0,340px) 1fr}.soonpg .doc img.prod{aspect-ratio:9/16;object-fit:cover;width:100%;max-width:340px}'
            '.ps-sws{display:flex;flex-wrap:wrap;gap:8px;margin:4px 0 6px}.ps-sw{display:inline-flex;align-items:center;gap:7px;min-height:40px;padding:8px 12px 8px 8px;border-radius:999px;'
            'border:1px solid var(--line);background:transparent;color:var(--ink);font:600 14px/1 system-ui,sans-serif;cursor:pointer}'
            '.ps-sw i{width:18px;height:18px;border-radius:50%;background:var(--sw);box-shadow:inset 0 0 0 1px rgba(128,128,128,.55)}'
            '.ps-sw[aria-pressed="true"]{border-color:var(--gold);box-shadow:0 0 0 1px var(--gold) inset}'
            '.soon-note{background:#16120c;border:1px solid #4a3716;border-radius:8px;padding:12px 14px;color:#e8dcc0;margin:14px 0}'
            '.pgal{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px;margin:8px 0 6px}.pgal figure{margin:0}'
            '.pgal img{display:block;width:100%;height:auto;aspect-ratio:9/16;object-fit:cover;border-radius:6px;border:1px solid var(--line);background:#111}'
            '.pgal figcaption{color:var(--muted);font-size:13px;margin-top:5px}'
            '@media(max-width:640px){.soonpg .doc{grid-template-columns:1fr}.soonpg .doc img.prod{max-width:100%}.pgal{grid-template-columns:repeat(2,1fr)}}</style>')

def build_soon(page, write, add_sm, site, lastmod):
    for ln in LINES:
        url = '/shop/%s/' % ln['slug']
        k0, l0, _ = ln['colors'][0]
        cols = ', '.join(c[1] for c in ln['colors'])
        title = '%s, Coming Soon | TRD Collectibles' % ln['name']
        desc = '%s from The Rubber Duck, coming soon: the chrome duck embroidered on the front, the red pill embroidered on the bill. Colors: %s. Not on sale yet; price announced at launch.' % (ln['name'], cols)
        facts = '<dl class="facts">%s</dl>' % ''.join('<dt>%s</dt><dd>%s</dd>' % (E(a), E(b)) for a, b in BIO(ln))
        others = [o for o in LINES if o is not ln][0]
        gal = ''.join('<figure><picture><source srcset="%s" type="image/webp"><img src="%s" alt="%s, %s, mockup" width="720" height="1280" loading="lazy" decoding="async"></picture><figcaption>%s</figcaption></figure>'
                      % (img(ln['slug'], k, 'webp'), img(ln['slug'], k), E(ln['name']), E(l), E(l)) for k, l, _ in ln['colors'])
        body = (PAGE_CSS + '<div class="soonpg" data-soon="%s" data-kind="%s"><p class="badge">Coming Soon</p><h1>%s</h1>'
                '<div class="doc"><picture><source class="ps-src" srcset="%s" type="image/webp"><img class="prod ps-img" src="%s" alt="%s, %s, mockup, coming soon" width="720" height="1280" decoding="async"></picture><div>'
                '<p class="lede">%s</p>'
                '<p class="meta">Color: <b class="ps-cn">%s</b></p><div class="ps-sws" role="group" aria-label="Color">%s</div>'
                '%s'
                '<p class="soon-note"><b>Coming soon.</b> This line is not on sale yet, so there is no checkout here. The price is announced at launch.</p>'
                '<p class="cta"><a class="btn" href="/merch.html">Shop what is available now</a> <a href="/shop/%s/">See the %s</a></p>'
                '</div></div>'
                '<h2>Every color</h2><div class="pgal">%s</div>'
                '<p class="meta">Mockups: the real duck and red pill artwork, shown on the cap held above the TRD box. Final product photos come with the launch.</p></div>'
                % (ln['slug'], E(ln['name']), E(ln['name']), img(ln['slug'], k0, 'webp'), img(ln['slug'], k0), E(ln['name']), E(l0),
                   E(ln['tagline']), E(l0), swatches(ln), facts, others['slug'], E(others['name']), gal)) + SWAP_JS
        graph = [{'@type': 'ImageGallery', 'name': ln['name'] + ' mockups', 'image': [site + img(ln['slug'], k) for k, _, _ in ln['colors']]}]
        write('shop/%s/index.html' % ln['slug'], page(url, title, desc, body, graph,
              [('Home', '/'), ('TRD Collectibles', '/merch.html'), (ln['name'], url)], og_image=site + img(ln['slug'], k0)))
        add_sm('shop', url, lastmod, images=[(site + img(ln['slug'], k), '%s, %s' % (ln['name'], l)) for k, l, _ in ln['colors']])
    update_merch()
