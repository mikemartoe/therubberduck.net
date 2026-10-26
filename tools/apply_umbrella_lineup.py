"""Write tools/umbrella_lineup.py into merch.html: the six-color lineup on the three signed cards (Pink and Light Blue retired),
special-order colors wired to their own (manual-capture) checkout links, the TRD Promise plate under the shop sign, and the
7-day special-order wording on every card that has special colors. Safe to rerun. Usage: python3 tools/apply_umbrella_lineup.py"""
import html, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import umbrella_lineup as U
F = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'merch.html')
h = open(F, encoding='utf-8').read()
E = html.escape

def card(slug):
    m = re.search(r'<article class="item[^"]*" data-slug="%s"[^>]*>.*?</article>' % re.escape(slug), h, re.S)
    assert m, slug
    return m

def color_opt(slug, spec, img_fmt=None):
    sp = set(spec['special'])
    sws, opts, sopts = [], [], []
    for i, (label, key, sw) in enumerate(U.LINEUP):
        img = (img_fmt % key) if img_fmt else '%s_%s' % (slug, key)
        s = label in sp
        t = label + (' (special order)' if s else '')
        sws.append('<button type="button" class="sw%s" data-color="%s" data-img="%s"%s aria-label="%s" aria-pressed="%s" title="%s" style="--sa:%s;--sb:%s"></button>'
                   % (' on' if i == 0 else '', E(label), img, ' data-special="1"' if s else '', E(t), 'true' if i == 0 else 'false', E(t), sw, sw))
        (sopts if s else opts).append('<option value="%s" data-img="%s"%s>%s</option>' % (E(label), img, ' data-special="1"' if s else '', E(label)))
    if sopts:
        opts.append('<optgroup label="Special order, up to 7 extra days">%s</optgroup>' % ''.join(sopts))
    return ('<div class="opt"><span class="lbl">Color <b class="cname">%s</b></span><div class="sws" role="group" aria-label="Color">%s</div>'
            '<select class="csel" aria-label="Color">%s</select></div>' % (E(U.LINEUP[0][0]), ''.join(sws), ''.join(opts)))

for slug, spec in U.SIGNED.items():
    m = card(slug); b = m.group(0)
    k0 = U.LINEUP[0]
    # article: special ship wording for the card script
    b = re.sub(r'(<article class="item signed" data-slug="%s")(?: data-sp-ship="[^"]*" data-sp-shipin="[^"]*")?' % slug,
               r'\1 data-sp-ship="%s" data-sp-shipin="%s"' % (U.SHIP_SPECIAL, U.SHIPIN_SPECIAL_SIGNED), b, count=1)
    # front photo: the lineup's first color, square signed-card photo
    b = re.sub(r'<div class="photo"><picture><source srcset="[^"]+" type="image/webp"><img src="[^"]+" alt="[^"]*"',
               '<div class="photo"><picture><source srcset="store-img/%s_%s.webp" type="image/webp"><img src="store-img/%s_%s.jpg" alt="%s - %s"'
               % (slug, k0[1], slug, k0[1], E(re.search(r'<span class="nm">(.*?)</span>', b).group(1)), k0[0]), b, count=1)
    b = b.replace('<td>2-3 wks</td></tr>', '<td class="shipin">2-3 wks</td></tr>', 1)
    # colors count on the back
    b = re.sub(r'(<td>(?:One|S-3XL)</td><td>)\d+(</td>)', r'\g<1>%d\2' % len(U.LINEUP), b, count=1)
    # color picker
    b = re.sub(r'<div class="opt"><span class="lbl">Color .*?</select></div>', lambda _: color_opt(slug, spec), b, count=1, flags=re.S)
    # special links
    if 'special_links' in spec:
        def so(mm):
            z = mm.group(1)
            return '%s data-special-link="%s"' % (re.sub(r' data-special-link="[^"]*"', '', mm.group(0)), spec['special_links'][z])
        b = re.sub(r'<option value="([^"]+)" data-link="[^"]+" data-price="\d+"(?: data-special-link="[^"]*")?', so, b)
    else:
        b = re.sub(r'(<a class="buy" href="[^"]+" data-base="[^"]+")(?: data-special-base="[^"]*")?', r'\1 data-special-base="%s"' % spec['special_link'], b, count=1)
    # the special-order note above the Buy button
    b = re.sub(r'\s*<p class="sp-note"[^>]*>.*?</p>', '', b, flags=re.S)
    b = b.replace('\n      <a class="buy"', '\n      <p class="sp-note" role="note" hidden>%s</p>\n      <a class="buy"' % U.NOTE_SIGNED, 1)
    h = h[:m.start()] + b + h[m.end():]

# Unsigned listings moved to the lineup (Duck Dad Hat): color picker, special link, special note and ship wording
for slug, spec in U.UNSIGNED.items():
    m = card(slug); b = m.group(0)
    b = re.sub(r'(<article class="item counter" data-slug="%s")(?: data-sp-ship="[^"]*" data-sp-shipin="[^"]*")?' % slug,
               r'\1 data-sp-ship="%s" data-sp-shipin="%s"' % (U.SHIP_SPECIAL, U.SHIPIN_SPECIAL_UNSIGNED), b, count=1)
    b = b.replace('<td>3-8 days</td></tr>', '<td class="shipin">3-8 days</td></tr>', 1)
    b = re.sub(r'(<td>(?:One|S-3XL)</td><td>)\d+(</td>)', r'\g<1>%d\2' % len(U.LINEUP), b, count=1)
    b = re.sub(r'<div class="opt"><span class="lbl">Color .*?</select></div>', lambda _: color_opt(slug, spec, spec['img']), b, count=1, flags=re.S)
    b = re.sub(r'(<a class="buy" href="[^"]+" data-base="[^"]+")(?: data-special-base="[^"]*")?', r'\1 data-special-base="%s"' % spec['special_link'], b, count=1)
    b = re.sub(r'\s*<p class="sp-note"[^>]*>.*?</p>', '', b, flags=re.S)
    b = b.replace('\n      <a class="buy"', '\n      <p class="sp-note" role="note" hidden>%s</p>\n      <a class="buy"' % U.NOTE_UNSIGNED, 1)
    h = h[:m.start()] + b + h[m.end():]

# Red Pill Tee: same 7-day wording (its special links already exist in Stripe)
m = card('duck-tee'); b = m.group(0)
b = re.sub(r'(<article class="item counter" data-slug="duck-tee")(?: data-sp-ship="[^"]*" data-sp-shipin="[^"]*")?',
           r'\1 data-sp-ship="%s" data-sp-shipin="%s"' % (U.SHIP_SPECIAL, U.SHIPIN_SPECIAL_UNSIGNED), b, count=1)
b = re.sub(r'<p class="sp-note" role="note" hidden>.*?</p>', '<p class="sp-note" role="note" hidden>%s</p>' % U.NOTE_UNSIGNED, b, count=1, flags=re.S)
b = re.sub(r'<div class="fact"><p><b>Duck Fact:</b> Tiffany Blue and Hot Pink are special orders:[^<]*</p></div>',
           '<div class="fact"><p><b>Duck Fact:</b> Tiffany Blue and Hot Pink are special orders: up to 7 extra days, card authorized, not charged, until the maker confirms.</p></div>', b, count=1)
h = h[:m.start()] + b + h[m.end():]

# The TRD Promise plate under the shop sign's plaques (same width as the plaques row, centered)
plate = ('<!-- promise:begin -->\n    <div class="promise" id="promise" role="note" aria-label="%s"><p class="pr-k"><span>%s</span></p><p class="pr-t">%s</p></div>\n<!-- promise:end -->'
         % (U.PROMISE_TITLE, U.PROMISE_TITLE, U.PROMISE_TEXT))
h = re.sub(r'[ \t]*<!-- promise:begin -->.*?<!-- promise:end -->\n', '', h, flags=re.S)
assert '    </ul>\n    <span class="neon"' in h
h = h.replace('    </ul>\n    <span class="neon"', '    </ul>\n    ' + plate.lstrip() + '\n    <span class="neon"', 1)

css = ('<style id="umbrella-css">\n'
       '.promise{position:relative;max-width:1040px;margin:18px auto 0;padding:14px 22px 15px;text-align:center;border-radius:10px;'
       'background:linear-gradient(180deg,#1d140a,#120c06);border:1px solid var(--gold2);box-shadow:inset 0 0 0 4px #120c06,inset 0 0 0 5px rgba(200,155,60,.55),0 6px 14px rgba(0,0,0,.45)}\n'
       '.pr-k{margin:0 0 6px;display:flex;align-items:center;justify-content:center;gap:14px;font-family:var(--mono);font-weight:700;font-size:.86rem;letter-spacing:.3em;text-transform:uppercase;color:var(--gold1)}\n'
       '.pr-k::before,.pr-k::after{content:"";flex:0 1 90px;height:1px;background:linear-gradient(90deg,transparent,var(--gold2))}.pr-k::after{transform:scaleX(-1)}\n'
       '.pr-t{margin:0 auto;max-width:860px;color:#efe4c6;font-size:1.02rem;line-height:1.5;text-wrap:balance}\n'
       '.item[data-slug="signed-tee"] .photo{background:#5c5b5c}\n'
       '.signed .photo>picture img{object-fit:cover}\n'
       '.item[data-slug="signed-dad-hat"] .auto,.item[data-slug="signed-trucker-hat"] .auto{display:none}\n'
       '.buy.pending{opacity:.55;cursor:not-allowed;filter:grayscale(.4)}\n'
       '@media (max-width:699px){.promise{margin-top:12px;padding:11px 12px 12px}.pr-k{font-size:.74rem;letter-spacing:.2em;gap:8px}.pr-k span{white-space:nowrap}.pr-t{font-size:.9rem;line-height:1.42}}\n'
       '</style>\n')
h = re.sub(r'<style id="umbrella-css">.*?</style>\n', '', h, flags=re.S)
h = h.replace('  <section class="case"', css + '  <section class="case"', 1)

# Card script: special links for one-size items (data-special-base), per-card special ship wording, pending links can't be clicked
old_js = re.search(r"    function sync\(\)\{.*?\n    \}\n", h, re.S).group(0)
new_js = ("    function sync(){\n"
          "      var link=(special&&buy.getAttribute('data-special-base'))||buy.getAttribute('data-base');\n"
          "      if(size){var o=size.options[size.selectedIndex];link=(special&&o.getAttribute('data-special-link'))||o.getAttribute('data-link');amts.forEach(function(a){a.textContent=money(o.getAttribute('data-price'))})}\n"
          "      var ref=[s];if(color)ref.push(slug(color));if(size)ref.push(slug(size.value));else if(color)ref.push('one-size');\n"
          "      /* a special-order link that isn't live in Stripe yet (tools/umbrella_lineup.py) can't be clicked */\n"
          "      var pend=link.indexOf('/PENDING-')>=0;if(!buy._t)buy._t=buy.textContent;buy.classList.toggle('pending',pend);\n"
          "      if(pend){buy.removeAttribute('href');buy.setAttribute('aria-disabled','true');buy.textContent='Link not live yet'}\n"
          "      else{buy.removeAttribute('aria-disabled');buy.textContent=buy._t;buy.href=link+(link.indexOf('?')<0?'?':'&')+'client_reference_id='+encodeURIComponent(ref.join('_'))}\n"
          "    }\n")
h = h.replace(old_js, new_js, 1)
h = re.sub(r"var bs=card\.querySelector\('\.bk-ship'\);if\(bs(?:&&card\.querySelector\('\.bk-pic'\))?\)\{if\(!bs\._t\)bs\._t=bs\.textContent;bs\.textContent=special\?'[^']*':bs\._t\}",
           "var bs=card.querySelector('.bk-ship');if(bs&&card.hasAttribute('data-sp-ship')){if(!bs._t)bs._t=bs.textContent;bs.textContent=special?card.getAttribute('data-sp-ship'):bs._t}", h, count=1)
h = re.sub(r"var si=card\.querySelector\('\.tag \.shipin'\);if\(si\)\{if\(!si\._t\)si\._t=si\.textContent;si\.textContent=special\?'[^']*':si\._t\}",
           "var si=card.querySelector('.tag .shipin');if(si&&card.hasAttribute('data-sp-shipin')){if(!si._t)si._t=si.textContent;si.textContent=special?card.getAttribute('data-sp-shipin'):si._t}", h, count=1)
open(F, 'w', encoding='utf-8').write(h)
print('merch.html updated')
