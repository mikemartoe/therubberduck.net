"""Premium line, COMING SOON (refresh: branch hat-lines-coming-soon, Oct 26 2026; not live until Mike approves the screenshots).
Two lines, no prices and no buy buttons: they are announced, not sold.
  /shop/premium-wool-cap/     wool-blend cap, chrome duck embroidered front center (pill on the bill in mockups is artwork only)
  /shop/premium-leather-hat/  leather cap, chrome duck front; leather type/maker/price confirmed at launch (no Printful leather cap exists)
Also writes the "Coming Soon" section of merch.html between <!-- premium:begin --> and <!-- premium:end -->.
Images: /store-img/premium/<slug>_<color>.{jpg,webp} 1024x1024 studio mockups on dark surfaces, plus -512 copies for thumbnails.
The real duck and pill art is composited (uniform scale and rotation only, never redrawn or stretched); see
/workspace/trd-reports/hat-lines-2026-10-26/tools/compose_lux.py. Used by tools/seo-build.py (build_soon).
Items here never get Product/Offer JSON-LD because there is no price yet."""
import html, re
E = lambda s: html.escape(str(s), quote=True)

LINES = [
    {'slug': 'premium-wool-cap', 'name': 'Premium Wool Cap', 'kind': 'Wool cap', 'short': 'Wool',
     'cap': 'Concept mockup. The finished cap carries the embroidered chrome duck on the front; the pill shown on the bill is artwork only.',
     'desc': 'Premium Wool Cap from The Rubber Duck, coming soon: a wool-blend cap with the chrome duck embroidered on the front. Planned colors: Deep Navy, Black, Charcoal, Natural Cream, Burgundy. Not on sale yet; materials and price confirmed at launch.',
     'made': 'Wool blend, structured crown',
     'tagline': 'A structured wool-blend cap with the chrome duck embroidered on the front.',
     'lede': 'A structured six-panel cap in a wool blend, with the chrome duck embroidered front and center. Raised (3D puff) stitching is the plan. The exact blend, the final colors and the price are confirmed at launch.',
     'colors': [('navy', 'Deep Navy', '#1e2740'), ('black', 'Black', '#121212'), ('charcoal', 'Charcoal', '#46464a'),
                ('ivory', 'Natural Cream', '#d9ccb0'), ('burgundy', 'Burgundy', '#5e1620')]},
    {'slug': 'premium-leather-hat', 'name': 'Premium Leather Hat', 'kind': 'Leather hat', 'short': 'Leather',
     'cap': 'Concept mockup. The finished cap carries the chrome duck on the front; the pill shown on the bill is artwork only.', 'front': 'Chrome duck',
     'desc': 'Premium Leather Hat from The Rubber Duck, coming soon: a leather cap with the chrome duck on the front. Planned colors: Black, Cognac, Saddle Tan. Not on sale yet; materials and price confirmed at launch.',
     'made': 'Leather (type confirmed at launch)',
     'tagline': 'A leather cap with the chrome duck on the front. The leather, the stitching and the price are confirmed at launch.',
     'lede': 'A leather baseball cap with the chrome duck front and center. We are still choosing the maker, so the type of leather, how the duck is applied and the price will be confirmed here before launch. Black, Cognac and Saddle Tan are the planned colors.',
     'colors': [('black', 'Black', '#151313'), ('cognac', 'Cognac', '#7a3f1d'), ('tan', 'Saddle Tan', '#b88a55')]},
]
BIO = lambda ln: [('Made of', ln['made']), ('Front', ln.get('front', 'Chrome duck, embroidered')),
                  ('Price', 'Announced at launch'), ('Status', 'Coming soon')]
PROMISE = ('If it&rsquo;s listed here, it&rsquo;s ours to deliver, and that will hold for this line too. It isn&rsquo;t on sale yet. '
           'When it launches, every cap is made for your order and ships in our standard time. If anything ever holds up yours, it may '
           'take up to 7 extra days, and if we can&rsquo;t fill it, every penny comes back to you.')

def img(slug, key, ext='jpg', small=False):
    return '/store-img/premium/%s_%s%s.%s' % (slug, key, '-512' if small else '', ext)

# swatches / gallery tiles swap the main photo and the color name
SWAP_JS = ('<script>(function(){document.querySelectorAll("[data-soon]").forEach(function(x){var s=x.getAttribute("data-soon"),k=x.getAttribute("data-kind"),'
           'img=x.querySelector("img.ps-img"),src=x.querySelector("source.ps-src"),nm=x.querySelector(".ps-cn"),bs=x.querySelectorAll(".ps-sw"),ts=x.querySelectorAll(".ps-t");'
           'function pick(c,l){var p="/store-img/premium/"+s+"_"+c;bs.forEach(function(o){o.setAttribute("aria-pressed",String(o.getAttribute("data-c")===c));});'
           'ts.forEach(function(o){o.setAttribute("aria-pressed",String(o.getAttribute("data-c")===c));});'
           'src.srcset=p+".webp";img.src=p+".jpg";img.alt=k+", "+l+", mockup, coming soon";if(nm)nm.textContent=l;}'
           'bs.forEach(function(b){b.addEventListener("click",function(){pick(b.getAttribute("data-c"),b.getAttribute("data-l"));});});'
           'ts.forEach(function(b){b.addEventListener("click",function(){pick(b.getAttribute("data-c"),b.getAttribute("data-l"));'
           'var m=x.querySelector(".lx-main");if(m&&m.getBoundingClientRect().top<0)m.scrollIntoView({behavior:"smooth",block:"start"});});});});})();</script>')

def swatches(ln):
    return ''.join('<button type="button" class="ps-sw" data-c="%s" data-l="%s" aria-pressed="%s" aria-label="%s" title="%s" style="--sw:%s"></button>'
                   % (k, E(l), 'true' if i == 0 else 'false', E(l), E(l), sw) for i, (k, l, sw) in enumerate(ln['colors']))

# ---------------------------------------------------------------- merch.html section
MERCH_CSS = '''<style>
/* ============ premium line: coming soon ============ */
.vault{margin:34px 0 0;position:relative;background:radial-gradient(120% 90% at 50% 0%,#1d1710 0%,#0b0907 60%,#050404 100%);border:1px solid #6d5426;border-radius:14px;
  padding:30px 28px 30px;box-shadow:0 0 0 6px #0b0907,0 0 0 7px #8a6420,0 24px 50px rgba(0,0,0,.65);overflow:hidden}
.vault::before{content:"";position:absolute;inset:0;background-image:var(--noise);opacity:.18;pointer-events:none}
.vault .vh{position:relative;text-align:center;margin:0 auto 24px;max-width:760px}
.vault .vk{margin:0;font-family:var(--mono);font-weight:700;font-size:.86rem;letter-spacing:.42em;text-transform:uppercase;color:var(--gold2)}
.vault h2{margin:8px 0 0;font-family:Georgia,'Times New Roman',serif;font-weight:400;font-size:clamp(2.2rem,4.6vw,3.4rem);line-height:1.05;letter-spacing:.04em;
  background:linear-gradient(180deg,var(--gold1) 0%,var(--gold2) 55%,var(--gold3) 100%);-webkit-background-clip:text;background-clip:text;color:transparent}
.vault .vrule{display:block;width:140px;height:1px;margin:14px auto;background:linear-gradient(90deg,transparent,var(--gold2),transparent)}
.vault .vp{margin:0;color:#e2d6bb;font-size:1.12rem;line-height:1.55;text-wrap:balance}
.vgrid{position:relative;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:26px;align-items:stretch}
.soon{position:relative;background:linear-gradient(180deg,#14100b,#0c0a08);border:1px solid #3e3019;border-radius:10px;padding:14px 14px 18px;display:flex;flex-direction:column;gap:12px}
.soon .ph{position:relative;border-radius:6px;overflow:hidden;border:1px solid #4a3a1c;background:#0a0807;aspect-ratio:1/1}
.soon .ph img{display:block;width:100%;height:100%;object-fit:cover}
.soon .badge{position:absolute;top:12px;left:12px;font-family:var(--mono);font-weight:700;font-size:.78rem;letter-spacing:.28em;text-transform:uppercase;color:#120d05;
  background:linear-gradient(180deg,var(--gold1),var(--gold2));padding:7px 11px 6px;border-radius:3px;box-shadow:0 2px 10px rgba(0,0,0,.5)}
.soon h3{margin:2px 0 0;font-family:Georgia,'Times New Roman',serif;font-weight:400;font-size:1.75rem;letter-spacing:.03em;color:var(--gold1);text-align:center}
.soon .tl{margin:0;color:#e2d6bb;font-size:1.06rem;line-height:1.5;text-align:center;text-wrap:balance}
.soon .crow{display:flex;align-items:center;justify-content:center;gap:14px;flex-wrap:wrap}
.soon .cl{margin:0;font-family:var(--mono);font-size:.9rem;color:#b9a985;letter-spacing:.06em}
.soon .cl b{color:#efe4c6;font-weight:700}
.ps-sws{display:flex;flex-wrap:wrap;gap:10px;justify-content:center}
.ps-sw{width:30px;height:30px;padding:0;border-radius:50%;border:1px solid #4a3a1c;background:var(--sw);cursor:pointer;
  box-shadow:inset 0 0 0 2px #0c0a08,inset 0 0 0 3px rgba(255,255,255,.18)}
.ps-sw[aria-pressed="true"]{border-color:var(--gold1);box-shadow:inset 0 0 0 2px #0c0a08,0 0 0 2px var(--gold2)}
.soon .more{display:flex;flex-direction:column;align-items:center;gap:6px;margin:auto 0 0;padding-top:4px;text-align:center}
.soon .more a{color:var(--gold1);font-weight:700;font-size:1.05rem;text-decoration:none;border-bottom:1px solid #6d5426;padding-bottom:2px}
.soon .more span{color:#9d8f74;font-size:.92rem}
@media(max-width:760px){.vault{padding:22px 14px 22px}.vgrid{grid-template-columns:1fr;gap:20px}.vault .vp{font-size:1.02rem}}
</style>'''

def merch_section():
    cards = []
    for ln in LINES:
        k0, l0, _ = ln['colors'][0]
        cards.append(
            '<article class="soon" data-soon="%s" data-kind="%s" aria-label="%s, coming soon">'
            '<div class="ph"><picture><source class="ps-src" srcset="%s" type="image/webp"><img class="ps-img" src="%s" alt="%s, %s, mockup, coming soon" width="1024" height="1024" loading="lazy" decoding="async"></picture>'
            '<span class="badge">Coming Soon</span></div>'
            '<h3>%s</h3>'
            '<p class="tl">%s</p>'
            '<div class="crow"><p class="cl">Color <b class="ps-cn">%s</b></p><div class="ps-sws" role="group" aria-label="Color">%s</div></div>'
            '<p class="more"><a href="/shop/%s/">See the %s line</a><span>Not on sale yet. Price announced at launch.</span></p>'
            '</article>' % (ln['slug'], E(ln['name']), E(ln['name']), img(ln['slug'], k0, 'webp'), img(ln['slug'], k0), E(ln['name']), E(l0),
                            E(ln['name']), E(ln['tagline']), E(l0), swatches(ln), ln['slug'], E(ln['short'].lower())))
    return ('<!-- premium:begin -->\n' + MERCH_CSS +
            '\n  <section class="vault" aria-labelledby="vault-title">\n    <header class="vh"><p class="vk">The Premium Line</p>'
            '<h2 id="vault-title">Coming Soon</h2><span class="vrule" aria-hidden="true"></span>'
            '<p class="vp">Wool-blend and leather caps with the chrome duck front and center. Concept mockups; not on sale yet.</p></header>\n'
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
PAGE_CSS = '''<style>
.lx{--g1:#f6e3a1;--g2:#c89b3c;--g3:#8a6420;--hair:#5a4521}
.lx-h{text-align:center;margin:18px auto 24px;max-width:800px}
.lx-sub{margin:16px auto 0;max-width:740px;font-size:19px;line-height:1.6;color:#e8dcc0;text-wrap:balance}
.lx-k{margin:0;font:700 12px/1 ui-monospace,Menlo,monospace;letter-spacing:.42em;text-transform:uppercase;color:var(--g2)}
.lx-h h1{margin:12px 0 0;font-family:Georgia,'Times New Roman',serif;font-weight:400;font-size:clamp(34px,5.2vw,54px);line-height:1.05;letter-spacing:.03em;
  background:linear-gradient(180deg,var(--g1) 0%,var(--g2) 60%,var(--g3) 100%);-webkit-background-clip:text;background-clip:text;color:transparent}
.lx-rule{display:block;width:150px;height:1px;margin:14px auto;background:linear-gradient(90deg,transparent,var(--g2),transparent)}
.lx-badge{display:inline-block;font:700 12px/1 ui-monospace,Menlo,monospace;letter-spacing:.3em;text-transform:uppercase;color:#120d05;
  background:linear-gradient(180deg,var(--g1),var(--g2));padding:8px 12px 7px;border-radius:3px}
.lx-hero{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr);gap:24px;align-items:stretch}
.lx-main{position:relative;margin:0;border-radius:10px;overflow:hidden;border:1px solid var(--hair);background:#0a0807;box-shadow:0 18px 40px rgba(0,0,0,.55)}
.lx-main::before{content:"";display:block;padding-top:100%}
.lx-main picture,.lx-main img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:50% 45%;display:block}
.lx-panel{display:flex;flex-direction:column;justify-content:space-between;gap:18px;padding:26px 28px;border-radius:10px;border:1px solid var(--hair);
  background:radial-gradient(130% 90% at 50% 0%,#1d1710 0%,#0f0c09 65%,#0a0807 100%);box-shadow:inset 0 0 0 4px #0a0807,inset 0 0 0 5px rgba(200,155,60,.35)}
.lx-panel .facts{grid-template-columns:max-content 1fr;gap:13px 20px;margin:0;font-size:18px;line-height:1.4;padding:0 0 20px;border-bottom:1px solid #3a2d17}
.lx-panel .facts dt{color:#b9a985;font:600 12.5px/2 ui-monospace,Menlo,monospace;letter-spacing:.18em;text-transform:uppercase}
.lx-panel .facts dd{color:#f3ead6}
.lx-cl{margin:0 0 12px;font:600 13.5px/1 ui-monospace,Menlo,monospace;letter-spacing:.18em;text-transform:uppercase;color:#b9a985}
.lx-cl b{color:#f3ead6;letter-spacing:.08em}
.ps-sws{display:flex;flex-wrap:wrap;gap:12px}
.ps-sw{width:36px;height:36px;padding:0;border-radius:50%;border:1px solid #5a4521;background:var(--sw);cursor:pointer;
  box-shadow:inset 0 0 0 2px #0c0a08,inset 0 0 0 3px rgba(255,255,255,.18)}
.ps-sw[aria-pressed="true"]{border-color:var(--g1);box-shadow:inset 0 0 0 2px #0c0a08,0 0 0 2px var(--g2)}
.lx-note{margin:0;padding-top:20px;border-top:1px solid #3a2d17;font-size:17.5px;line-height:1.55;color:#e8dcc0}
.lx-note b{color:var(--g1);font-weight:700}
.lx-sec{margin:34px 0 0}
.lx-sec h2{margin:0 0 14px;text-align:center;font-family:Georgia,'Times New Roman',serif;font-weight:400;font-size:28px;letter-spacing:.04em;color:var(--g1)}
.lx-gal{display:grid;grid-template-columns:repeat(var(--n),minmax(0,1fr));gap:14px}
.ps-t{display:block;margin:0;padding:0;border:0;background:none;color:inherit;font:inherit;cursor:pointer;text-align:center}
.ps-t img{display:block;width:100%;height:auto;aspect-ratio:1/1;object-fit:cover;border-radius:8px;border:1px solid var(--hair);background:#0a0807}
.ps-t[aria-pressed="true"] img{border-color:var(--g2);box-shadow:0 0 0 1px var(--g2)}
.ps-t span{display:block;margin-top:8px;font:600 12.5px/1.2 ui-monospace,Menlo,monospace;letter-spacing:.16em;text-transform:uppercase;color:#cdbf9f}
.lx .trd-promise{margin:34px 0 0;padding:20px 26px 21px;text-align:center;border:1px solid var(--g2);border-radius:10px;
  background:radial-gradient(120% 120% at 50% 0%,#1a140c 0%,#0e0b08 70%);box-shadow:inset 0 0 0 4px #0a0807,inset 0 0 0 5px rgba(200,155,60,.45)}
.lx .trd-promise h2{margin:0 0 8px;font:700 14px/1.2 ui-monospace,Menlo,monospace;letter-spacing:.32em;text-transform:uppercase;color:var(--g2)}
.lx .trd-promise p{margin:0 auto;max-width:760px;font-size:18px;line-height:1.6;color:#efe4c6;text-wrap:balance}
.lx-next{margin:34px 0 4px;display:grid;grid-template-columns:210px minmax(0,1fr);gap:26px;align-items:stretch;padding:16px;border-radius:10px;border:1px solid var(--hair);background:#100d09}
.lx-next img{display:block;width:100%;height:100%;aspect-ratio:1/1;object-fit:cover;border-radius:7px;border:1px solid var(--hair)}
.lx-next div{display:flex;flex-direction:column;justify-content:center;gap:10px}
.lx-next .lx-k{letter-spacing:.32em}
.lx-next h3{margin:0;font-family:Georgia,'Times New Roman',serif;font-weight:400;font-size:32px;color:var(--g1)}
.lx-next p{margin:0;font-size:18.5px;line-height:1.5;color:#e2d6bb}
.lx-next .cta{margin:4px 0 0}
@media(max-width:700px){.lx-h{margin-top:14px}.lx-sub{font-size:17px}.lx-hero{grid-template-columns:1fr;gap:16px}.lx-panel{padding:20px 18px}.lx-panel .facts{font-size:16.5px;gap:10px 16px}.lx-note{font-size:16.5px}
  .lx-gal{grid-template-columns:repeat(6,minmax(0,1fr));gap:10px}.lx-gal .ps-t{grid-column:span 2}.lx-gal[data-n="5"] .ps-t:nth-child(n+4){grid-column:span 3}
  .lx-gal[data-n="2"] .ps-t,.lx-gal[data-n="4"] .ps-t{grid-column:span 3}.ps-t span{font-size:11px;letter-spacing:.1em}
  .lx .trd-promise{padding:16px 16px 17px}.lx .trd-promise p{font-size:16.5px}
  .lx-next{grid-template-columns:1fr;gap:14px;padding:12px}.lx-next img{aspect-ratio:16/10;height:auto;object-position:50% 50%}.lx-next div{align-items:center;text-align:center;padding:0 6px 6px}
  .lx-next h3{font-size:25px}.lx-next p{font-size:16px}.lx-next .cta{justify-content:center}}
</style>'''

def build_soon(page, write, add_sm, site, lastmod):
    for ln in LINES:
        url = '/shop/%s/' % ln['slug']
        k0, l0, _ = ln['colors'][0]
        cols = ', '.join(c[1] for c in ln['colors'])
        title = '%s, Coming Soon | TRD Collectibles' % ln['name']
        desc = ln['desc']
        facts = '<dl class="facts">%s</dl>' % ''.join('<dt>%s</dt><dd>%s</dd>' % (E(a), E(b)) for a, b in BIO(ln))
        other = [o for o in LINES if o is not ln][0]
        n = len(ln['colors'])
        gal = ''.join('<button type="button" class="ps-t" data-c="%s" data-l="%s" aria-pressed="%s" aria-label="Show %s">'
                      '<picture><source srcset="%s" type="image/webp"><img src="%s" alt="%s, %s, mockup" width="512" height="512" loading="lazy" decoding="async"></picture><span>%s</span></button>'
                      % (k, E(l), 'true' if i == 0 else 'false', E(l), img(ln['slug'], k, 'webp', True), img(ln['slug'], k, 'jpg', True), E(ln['name']), E(l), E(l))
                      for i, (k, l, _) in enumerate(ln['colors']))
        ok0, ol0, _ = other['colors'][0]
        body = (PAGE_CSS + '<div class="lx" data-soon="%s" data-kind="%s">'
                '<header class="lx-h"><p class="lx-k">The Premium Line</p><h1>%s</h1><span class="lx-rule" aria-hidden="true"></span><span class="lx-badge">Coming Soon</span><p class="lx-sub">%s</p></header>'
                '<div class="lx-hero"><figure class="lx-main"><picture><source class="ps-src" srcset="%s" type="image/webp">'
                '<img class="ps-img" src="%s" alt="%s, %s, mockup, coming soon" width="1024" height="1024" decoding="async"></picture>'
                '<figcaption class="lx-cap" style="font-size:.8rem;opacity:.75;margin-top:.5rem;text-align:center">%s</figcaption></figure>'
                '<div class="lx-panel">%s'
                '<div><p class="lx-cl">Color <b class="ps-cn">%s</b></p><div class="ps-sws" role="group" aria-label="Color">%s</div></div>'
                '<p class="lx-note"><b>Coming soon.</b> This line is not on sale yet, so there is no checkout here. The price is announced at launch.</p></div></div>'
                '<section class="lx-sec" aria-labelledby="ec-%s"><h2 id="ec-%s">Every Color</h2><div class="lx-gal" data-n="%d" style="--n:%d">%s</div></section>'
                '<section class="trd-promise" aria-labelledby="pr-%s"><h2 id="pr-%s">The TRD Promise</h2><p>%s</p></section>'
                '<aside class="lx-next" aria-label="Also coming soon"><picture><source srcset="%s" type="image/webp"><img src="%s" alt="%s, %s, mockup" width="512" height="512" loading="lazy" decoding="async"></picture>'
                '<div><p class="lx-k">Also coming soon</p><h3>%s</h3><p>%s</p><p class="cta"><a class="btn" href="/merch.html">Shop what&rsquo;s available now</a> <a href="/shop/%s/">See the %s</a></p></div></aside>'
                '</div>'
                % (ln['slug'], E(ln['name']), E(ln['name']), E(ln['lede']), img(ln['slug'], k0, 'webp'), img(ln['slug'], k0), E(ln['name']), E(l0), ln['cap'],
                   facts, E(l0), swatches(ln), ln['slug'], ln['slug'], n, n, gal, ln['slug'], ln['slug'], PROMISE,
                   img(other['slug'], ok0, 'webp', True), img(other['slug'], ok0, 'jpg', True), E(other['name']), E(ol0),
                   E(other['name']), E(other['tagline']), other['slug'], E(other['name']))) + SWAP_JS
        graph = [{'@type': 'ImageGallery', 'name': ln['name'] + ' mockups', 'image': [site + img(ln['slug'], k) for k, _, _ in ln['colors']]}]
        write('shop/%s/index.html' % ln['slug'], page(url, title, desc, body, graph,
              [('Home', '/'), ('TRD Collectibles', '/merch.html'), (ln['name'], url)], og_image=site + img(ln['slug'], k0)))
        add_sm('shop', url, lastmod, images=[(site + img(ln['slug'], k), '%s, %s' % (ln['name'], l)) for k, l, _ in ln['colors']])
    update_merch()
