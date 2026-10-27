"""Write the Trucker Hat special-order colors (tools/umbrella_lineup.py TRUCKER) into merch.html. Safe to rerun.
Keeps the four Printful two-tones as they are and adds White, Navy, Gold, Tiffany Blue and Hot Pink as special orders
(swatch + picker option with data-special="1", the 7-day note, the special link on the Buy button), like the Duck Dad Hat card.
Also gives the two unsigned hat cards data-sp-shipamt (special-order shipping) so the card's Ship price follows the color.
Usage, from the repo root:  python3 tools/apply_trucker_lineup.py   then   python3 tools/build_shop_only.py"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import umbrella_lineup as U
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
h = open('merch.html', encoding='utf-8').read()
SW = {c: sw for c, _, sw in U.LINEUP}
KEY = {c: k for c, k, _ in U.LINEUP}
for slug, spec in U.TRUCKER.items():
    m = re.search(r'<article class="item[^"]*" data-slug="%s".*?</article>' % slug, h, re.S)
    b = m.group(0)
    if 'data-sp-ship=' not in b:
        b = b.replace('data-slug="%s"' % slug, 'data-slug="%s" data-sp-ship="%s" data-sp-shipin="%s"' % (slug, U.SHIP_SPECIAL, U.SHIPIN_SPECIAL_UNSIGNED), 1)
    if 'data-special="1"' not in b:
        btns = ''.join('<button type="button" class="sw" data-color="%s" data-img="%s" data-special="1" aria-label="%s (special order)" aria-pressed="false" '
                       'title="%s (special order)" style="--sa:%s;--sb:#fff"></button>' % (c, spec['img'] % KEY[c], c, c, SW[c]) for c in spec['special'])
        b = re.sub(r'(<div class="sws" role="group" aria-label="Color">.*?)(</div><select class="csel")', lambda x: x.group(1) + btns + x.group(2), b, count=1, flags=re.S)
        opts = '<optgroup label="Special order, up to 7 extra days">%s</optgroup>' % ''.join(
            '<option value="%s" data-img="%s" data-special="1">%s</option>' % (c, spec['img'] % KEY[c], c) for c in spec['special'])
        b = b.replace('</select></div>', opts + '</select></div>', 1)
    n = len(re.findall(r'class="sw( on)?"', b))
    b = re.sub(r'(<td>One</td><td>)\d+(</td>)', r'\g<1>%d\2' % n, b, count=1)
    b = b.replace('<td>3-8 days</td>', '<td class="shipin">3-8 days</td>', 1)
    if 'class="sp-note"' not in b:
        b = b.replace('\n      <a class="buy"', '\n      <p class="sp-note" role="note" hidden>%s</p>\n      <a class="buy"' % U.NOTE_UNSIGNED, 1)
    if 'data-special-base' not in b:
        b = re.sub(r'(<a class="buy" href="[^"]+" data-base="[^"]+")', r'\1 data-special-base="%s"' % spec['special_link'], b, count=1)
    h = h.replace(m.group(0), b)
    # the "On the rack" tile on the store page
    h = re.sub(r'(<a class="hr-t" href="/shop/%s/">.*?<em>)\d+ colors(</em>)' % slug, r'\g<1>%d colors\2' % n, h, count=1, flags=re.S)
# special-order shipping on the card's Ship price (unsigned hats: $4.75 regular, $4.95 special order)
for slug in ('duck-dad-hat', 'duck-trucker-hat'):
    amt = U.SPECIAL_SHIP[slug]
    if not re.search(r'data-slug="%s"[^>]*data-sp-shipamt' % slug, h):
        h = h.replace('data-slug="%s" ' % slug, 'data-slug="%s" data-sp-shipamt="$%s" ' % (slug, amt), 1)
js_old = "      var si=card.querySelector('.tag .shipin');"
js_new = ("      var sa=card.querySelector('.tag .line tbody td:nth-child(2)');if(sa&&card.hasAttribute('data-sp-shipamt')){if(!sa._t)sa._t=sa.textContent;sa.textContent=special?card.getAttribute('data-sp-shipamt'):sa._t}\n")
if js_new not in h:
    assert h.count(js_old) == 1
    h = h.replace(js_old, js_new + js_old, 1)
open('merch.html', 'w', encoding='utf-8').write(h)
print('merch.html: trucker special colors written')
