#!/usr/bin/env python3
"""Deltas, Q Proofs and drop-image text for therubberduck.net (add-on to tools/seo-build.py).

Run from the repo root AFTER tools/seo-build.py (it patches pages that script writes):
    python3 tools/seo-deltas-build.py

Idempotent. What it does:
  1. /deltas/            hub: what a delta is, a 12-month calendar of every date that has drops,
                         and The Rubber Duck's #delta posts from the X archive.
  2. /deltas/MM-DD/      one page per calendar date: every drop posted on that date, grouped by year.
  3. /q-proofs/          what a Q proof is, every drop signed Q+, the Book of Q Proofs PDFs,
                         and The Rubber Duck's #Qproof posts.
  4. /drops/N/           adds the drop's images with real alt text and a visible caption
                         (from data/drop-image-text.json), ImageObject JSON-LD, and links to the
                         date's delta page and, for Q+ drops, to /q-proofs/. Marked blocks only.
  5. /drops/             adds one line linking the two new sections (marked block).
  6. sitemaps/deltas.xml (new) + sitemap.xml index entry; image entries on drop URLs in sitemaps/drops.xml.
Rollback: git revert the commit, or delete /deltas/ /q-proofs/ and re-run tools/seo-build.py --only drops.
"""
import importlib.util, json, os, re, glob, datetime, html
from collections import OrderedDict, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('seob', os.path.join(HERE, 'seo-build.py'))
S = importlib.util.module_from_spec(spec); spec.loader.exec_module(S)   # chdirs to repo root; main() not run
E, SITE, ET, page, clip, ld_script = S.E, S.SITE, S.ET, S.page, S.clip, S.ld_script
PWA_HEAD, og_size = S.PWA_HEAD, S.og_size
TODAY = S.TODAY

LEDGER_DELTA = '/ledger.html?delta=today'
DX_CSS = '<link rel="stylesheet" href="/assets/seo/dx.css?v=1">\n'
RE_CSS = re.compile(r'<link rel="stylesheet" href="/assets/seo/dx\.css[^"]*">\n')
IMG_BASE = 'https://memes.therubberduck.net/drops/img/'
MISSING_IMAGES = set()   # keys listed in data/drop-images.js but not on R2 (404); 1001_1 uploaded 2026-10-30

# ---------------------------------------------------------------- data
src = open('data/drops.js', encoding='utf-8').read()
DROPS = []
for n, ts, site, board, link, text in json.loads(src[src.index('['):src.rindex(']') + 1]):
    DROPS.append({'n': n, 'dt': datetime.datetime.fromtimestamp(ts, ET), 'text': text or ''})
DROPS.sort(key=lambda d: d['n'])
BYN = {d['n']: d for d in DROPS}

isrc = open('data/drop-images.js', encoding='utf-8').read()
IMGS = json.loads(re.sub(r'([{,])(\w+):', r'\1"\2":', isrc[isrc.index('{'):isrc.rindex('}') + 1]))['d']
ITEXT = json.load(open('data/drop-image-text.json', encoding='utf-8'))

def plain(t):
    t = re.sub(r'https?://\s?\S+', '', t or '')
    t = re.sub(r'>>\d+', '', t)
    return re.sub(r'\s+', ' ', t).strip()

def is_qplus(t):
    # signed Q+ (also "(((Q+)))" and "Q 0 = Q+"); drop 2567 only contains a "Q+" inside other text
    return bool(re.search(r'(^|[\s(])Q\+(?=$|[\s)])', t or '', re.M))
QPLUS = [d for d in DROPS if is_qplus(d['text']) and d['n'] != 2567]

# X archive posts by The Rubber Duck that are on the month pages (anchor exists)
_anchor_cache = {}
def x_anchor(p):
    mk = p['c'][:7]
    f = 'x/archive/%s/index.html' % mk
    if f not in _anchor_cache:
        _anchor_cache[f] = open(f, encoding='utf-8').read() if os.path.exists(f) else ''
    return ('/x/archive/%s/#p%s' % (mk, p['i'])) if ('id="p%s"' % p['i']) in _anchor_cache[f] else None

XPOSTS = []
for f in sorted(glob.glob('x/data/p/*.json')):
    for p in json.load(open(f, encoding='utf-8')):
        if p.get('y') not in ('o', 'q'): continue
        t = p.get('x', '')
        tags = {'delta': bool(re.search(r'#delta\b', t, re.I)), 'proof': bool(re.search(r'#q ?proofs?\b|\bq ?proofs?\b', t, re.I))}
        if not (tags['delta'] or tags['proof']): continue
        a = x_anchor(p)
        if not a: continue
        dt = datetime.datetime.fromisoformat(p['c'].replace('Z', '+00:00')).astimezone(ET)
        XPOSTS.append({'id': p['i'], 'dt': dt, 'text': t, 'href': a, **tags})
XPOSTS.sort(key=lambda p: p['dt'], reverse=True)

EMOJI = re.compile('[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u200D\u20E3]')
def xpost_li(p):
    body = re.sub(r'\s+', ' ', EMOJI.sub('', plain(p['text']))).strip()
    body = clip(body, 220) if body else 'Image post'
    return ('<li><a href="%s"><time datetime="%s">%s</time></a> <span class="dx-q">%s</span></li>'
            % (p['href'], p['dt'].isoformat(), p['dt'].strftime('%B %-d, %Y'), E(body)))

# ---------------------------------------------------------------- shared copy
DEF_HTML = ('<dl class="dx-def">'
            '<dt>Drop</dt><dd>A post by the Q team.</dd>'
            '<dt>Delta</dt><dd>A drop&rsquo;s anniversary. Each day, anons read the drops posted on the same date in past years, 2017 to 2022, to see how they read today.</dd>'
            '<dt>Delta proof</dt><dd>A delta becomes a proof when the past drop proves true on its anniversary date.</dd>'
            '<dt>Q proof</dt><dd>A Q drop confirmed publicly by Donald Trump. Drops signed Q+ are attributed to President Trump.</dd>'
            '</dl>')

def mmdd_key(dt): return dt.strftime('%m-%d')
def mmdd_name(k): return datetime.date(2020, int(k[:2]), int(k[3:])).strftime('%B %-d')   # 2020 is a leap year

BYDAY = OrderedDict()
for d in sorted(DROPS, key=lambda d: (mmdd_key(d['dt']), d['dt'])):
    BYDAY.setdefault(mmdd_key(d['dt']), []).append(d)
DAYS = sorted(BYDAY)
YEARS = sorted({d['dt'].year for d in DROPS})
XBYDAY = defaultdict(list)
for p in XPOSTS:
    if p['delta']:
        # "tomorrow's #delta" posts belong to the next date, "yesterday's" to the previous one
        shift = 1 if re.search(r"tomorrow", p['text'], re.I) else (-1 if re.search(r"yesterday", p['text'], re.I) else 0)
        XBYDAY[mmdd_key(p['dt'] + datetime.timedelta(days=shift))].append(p)

SM = []   # (path, lastmod)
LM = S.git_date('data/drops.js')

def img_only(d):
    im = images_for(d['n'])
    return ('Image: ' + im[0][1]) if im else 'Image or link only.'

def drop_row(d):
    ex = plain(d['text'])
    ex = clip(ex, 200) if ex else clip(img_only(d), 200)
    nimg = len([i for i in IMGS.get(str(d['n']), []) if i['src'][:-5] not in MISSING_IMAGES])
    extra = (' &middot; %d image%s' % (nimg, '' if nimg == 1 else 's')) if nimg else ''
    return ('<li><a href="/drops/%d/">Q drop #%d</a> <span class="n"><time datetime="%s">%s</time>%s</span><span class="dx-q">%s</span></li>'
            % (d['n'], d['n'], d['dt'].isoformat(), d['dt'].strftime('%-I:%M %p ET'), extra, E(ex)))

# ---------------------------------------------------------------- 1. day pages
def build_days():
    for i, k in enumerate(DAYS):
        ds = BYDAY[k]; name = mmdd_name(k)
        yrs = OrderedDict()
        for d in ds: yrs.setdefault(d['dt'].year, []).append(d)
        yspan = ('%d' % min(yrs)) if len(yrs) == 1 else '%d to %d' % (min(yrs), max(yrs))
        title = 'Q Drop Deltas for %s: Every Drop Posted on This Date' % name
        desc = clip('Q drop deltas for %s: all %d Q drop%s posted on %s, %s, grouped by year with full text links. Read what was posted on this date and how it reads today.'
                    % (name, len(ds), '' if len(ds) == 1 else 's', name, yspan))
        prev_k = DAYS[i - 1]; next_k = DAYS[(i + 1) % len(DAYS)]
        pn = ('<nav class="pn"><a rel="prev" href="/deltas/%s/">&lsaquo; %s</a><a href="/deltas/">All dates</a><a rel="next" href="/deltas/%s/">%s &rsaquo;</a></nav>'
              % (prev_k, mmdd_name(prev_k), next_k, mmdd_name(next_k)))
        groups = ''.join('<section class="dx-year"><h2 id="y%d">%s, %d <span class="n">%d drop%s</span></h2><ol class="dx-list">%s</ol></section>'
                         % (y, name, y, len(v), '' if len(v) == 1 else 's', ''.join(drop_row(d) for d in v)) for y, v in yrs.items())
        jump = ' &middot; '.join('<a href="#y%d">%d</a>' % (y, y) for y in yrs)
        xp = XBYDAY.get(k, [])
        xs = ('<section class="dx-x"><h2>The Rubber Duck&rsquo;s #delta posts for %s</h2><ul class="dx-xl%s">%s</ul></section>' % (name, ' one' if len(xp[:12]) < 4 else '', ''.join(xpost_li(p) for p in xp[:12]))) if xp else ''
        body = ('<h1>Q Drop Deltas for %s</h1>' % name +
                '<p class="lede">%d drop%s posted on %s, %s. A delta is a drop&rsquo;s anniversary: read what was posted on this date in past years and see how it reads today. '
                'To see today&rsquo;s deltas as they happen, open <a href="%s">Deltas in The Drop Ledger</a>.</p>' % (len(ds), '' if len(ds) == 1 else 's', name, yspan, LEDGER_DELTA) +
                '<p class="dx-jump">Jump to %s</p>' % jump + pn + groups + xs +
                '<p class="dx-more">When a past drop proves true on its anniversary, it is a delta proof. See <a href="/q-proofs/">Q Proofs</a> for drops confirmed by President Trump.</p>' + pn)
        items = [{'@type': 'ListItem', 'position': j + 1, 'url': SITE + '/drops/%d/' % d['n'], 'name': 'Q drop #%d, %s' % (d['n'], d['dt'].strftime('%B %-d, %Y'))} for j, d in enumerate(ds)]
        g = [{'@type': 'CollectionPage', '@id': SITE + '/deltas/%s/#c' % k, 'name': title, 'url': SITE + '/deltas/%s/' % k, 'isPartOf': {'@id': SITE + '/deltas/#hub'},
              'about': 'Q drops posted on %s' % name, 'mainEntity': {'@type': 'ItemList', 'numberOfItems': len(ds), 'itemListElement': items}}]
        S.write('deltas/%s/index.html' % k, page('/deltas/%s/' % k, title, desc, body, g,
                [('Home', '/'), ('Q Drops', '/drops/'), ('Deltas', '/deltas/'), (name, '/deltas/%s/' % k)], og_desc='Q drop deltas for %s: %d drops posted on this date.' % (name, len(ds)), extra_head=DX_CSS))
        SM.append(('/deltas/%s/' % k, LM))
    return len(DAYS)

# ---------------------------------------------------------------- 2. hub
def build_hub():
    months = ''
    for m in range(1, 13):
        cells = ''
        ndays = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]
        for dd in range(1, ndays + 1):
            k = '%02d-%02d' % (m, dd)
            if k in BYDAY:
                c = len(BYDAY[k])
                cells += '<a href="/deltas/%s/" title="%s: %d drop%s" aria-label="%s, %d drop%s">%d</a>' % (k, mmdd_name(k), c, '' if c == 1 else 's', mmdd_name(k), c, '' if c == 1 else 's', dd)
            else:
                cells += '<span title="No drops on %s">%d</span>' % (mmdd_name(k), dd)
        months += '<section class="dx-month"><h3>%s</h3><div class="dx-days">%s</div></section>' % (datetime.date(2020, m, 1).strftime('%B'), cells)
    busiest = sorted(DAYS, key=lambda k: -len(BYDAY[k]))[:8]
    dp = [p for p in XPOSTS if p['delta']]
    title = 'Q Drop Deltas: Drops Posted on This Day, 2017 to 2022'
    desc = clip('Q drop deltas, day by day: every Q drop posted on each calendar date from %d to %d, on %d date pages. What a delta is, delta proofs, and today\'s deltas in The Drop Ledger.'
                % (YEARS[0], YEARS[-1], len(DAYS)))
    body = ('<h1>Q Drop Deltas</h1>'
            '<p class="lede">Every Q drop, sorted by the calendar date it was posted. Each date below opens a page with all the drops posted on that day from %d to %d, grouped by year, so you can read them on their anniversary. '
            'For today, yesterday and tomorrow in one click, open <a href="%s">Deltas in The Drop Ledger</a>.</p>' % (YEARS[0], YEARS[-1], LEDGER_DELTA) +
            DEF_HTML +
            '<h2>Pick a date</h2><p class="dx-note">%d dates have drops. Dates in gray have none.</p><div class="dx-cal">%s</div>' % (len(DAYS), months) +
            '<h2>Dates with the most drops</h2><ul class="months">%s</ul>' % ''.join('<li><a href="/deltas/%s/">%s</a> <span class="n">%d drops</span></li>' % (k, mmdd_name(k), len(BYDAY[k])) for k in busiest) +
            (('<h2>Recent #delta posts by The Rubber Duck</h2><ul class="dx-xl">%s</ul><p class="dx-more">More in <a href="/x/archive/">the X archive by month</a>.</p>' % ''.join(xpost_li(p) for p in dp[:16])) if dp else '') +
            '<p class="dx-more">See also <a href="/q-proofs/">Q Proofs</a>, drops confirmed by President Trump, and <a href="/drops/">every Q drop by month</a>.</p>'
            '<p class="dx-more">Get the daily Deltas digest on your phone: <a href="/alerts/">turn on alerts</a>.</p>')
    g = [{'@type': 'CollectionPage', '@id': SITE + '/deltas/#hub', 'name': title, 'url': SITE + '/deltas/', 'description': desc,
          'about': [{'@type': 'DefinedTerm', 'name': 'Delta', 'description': 'A Q drop\u2019s anniversary: the drops posted on the same calendar date in past years, read again to see their relevance today.'},
                    {'@type': 'DefinedTerm', 'name': 'Delta proof', 'description': 'A delta whose past drop proves true on its anniversary date.'}],
          'hasPart': [{'@type': 'CollectionPage', 'url': SITE + '/deltas/%s/' % k, 'name': 'Q drop deltas for %s' % mmdd_name(k)} for k in DAYS]}]
    S.write('deltas/index.html', page('/deltas/', title, desc, body, g, [('Home', '/'), ('Q Drops', '/drops/'), ('Deltas', '/deltas/')],
                                     og_image=SITE + '/images/brand/social-deltas-20261030.png',
                                     extra_head=og_size('Deltas: Q drop anniversaries, year by year. The Rubber Duck.') + DX_CSS + PWA_HEAD))
    SM.insert(0, ('/deltas/', TODAY))

# ---------------------------------------------------------------- 3. q proofs
def build_proofs():
    rows = ''.join(drop_row_full(d) for d in QPLUS)
    pdfs = [('book-of-q-proofs-v1-5', 'Book of Q Proofs, version 1.5')] + [('book-of-q-proofs-v1-5-%s' % s, 'Book of Q Proofs, version 1.5, edition %s' % s) for s in ('2', '29', '30', '31')]
    pdfs = [(s, t) for s, t in pdfs if os.path.exists('library/%s/index.html' % s)]
    pp = [p for p in XPOSTS if p['proof']]
    ctx = [(225, 'Trump&rsquo;s &ldquo;calm before the storm&rdquo; remark of October 5, 2017, set beside the drop'), (4948, 'context and sources set beside the drop')]
    ctx = [(n, t) for n, t in ctx if os.path.exists('tools/witness-blocks/%d.html' % n)]
    title = 'Q Proofs: Q Drops Confirmed by Donald Trump, and Q+ Drops'
    desc = clip('Q proofs: Q drops confirmed publicly by Donald Trump. All %d drops signed Q+, with full text links, the Book of Q Proofs PDFs, and delta proofs from The Rubber Duck.' % len(QPLUS))
    body = ('<h1>Q Proofs</h1>'
            '<p class="lede">A Q proof is a Q drop confirmed publicly by Donald Trump. '
            'Drops signed Q+ are attributed to President Trump himself. A delta proof is a drop that proves true on its anniversary date; see <a href="/deltas/">Deltas</a>.</p>' + DEF_HTML +
            '<h2>Drops signed Q+</h2><p class="dx-note">%d drops carry the Q+ signature, oldest first.</p><ol class="dx-list">%s</ol>' % (len(QPLUS), rows) +
            (('<h2>Drops shown with their public record</h2><ul class="links">%s</ul>' % ''.join('<li><a href="/drops/%d/">Q drop #%d</a>: %s</li>' % (n, n, t) for n, t in ctx)) if ctx else '') +
            (('<h2>The Book of Q Proofs</h2><p>Proof collections in the SCIF Reading Room, each with its own page and PDF.</p><ul class="links">%s</ul>' % ''.join('<li><a href="/library/%s/">%s</a></li>' % (s, t) for s, t in pdfs)) if pdfs else '') +
            (('<h2>Q proofs posted by The Rubber Duck</h2><ul class="dx-xl">%s</ul><p class="dx-more">More in <a href="/x/archive/">the X archive by month</a>.</p>' % ''.join(xpost_li(p) for p in pp[:25])) if pp else '') +
            '<p class="dx-more">Search every drop in <a href="/ledger.html">The Drop Ledger</a>, or browse <a href="/drops/">every Q drop by month</a>.</p>')
    items = [{'@type': 'ListItem', 'position': j + 1, 'url': SITE + '/drops/%d/' % d['n'], 'name': 'Q drop #%d, signed Q+' % d['n']} for j, d in enumerate(QPLUS)]
    g = [{'@type': 'CollectionPage', '@id': SITE + '/q-proofs/#c', 'name': title, 'url': SITE + '/q-proofs/', 'description': desc,
          'about': [{'@type': 'DefinedTerm', 'name': 'Q proof', 'description': 'A Q drop confirmed publicly by Donald Trump.'},
                    {'@type': 'DefinedTerm', 'name': 'Q+', 'description': 'The signature on drops attributed to President Trump.'},
                    {'@type': 'Person', 'name': 'Donald J. Trump'}],
          'mainEntity': {'@type': 'ItemList', 'name': 'Q drops signed Q+', 'numberOfItems': len(QPLUS), 'itemListElement': items}}]
    S.write('q-proofs/index.html', page('/q-proofs/', title, desc, body, g, [('Home', '/'), ('Q Drops', '/drops/'), ('Q Proofs', '/q-proofs/')],
                                      og_image=SITE + '/images/brand/social-q-proofs-20261030.png',
                                      extra_head=og_size('Q Proofs: explore the drops and public record. The Rubber Duck.') + DX_CSS + PWA_HEAD))
    SM.insert(1, ('/q-proofs/', TODAY))

def drop_row_full(d):
    ex = plain(d['text']); ex = clip(ex, 220) if ex else clip(img_only(d), 220)
    return ('<li><a href="/drops/%d/">Q drop #%d</a> <span class="n"><time datetime="%s">%s</time> &middot; <a href="/deltas/%s/">delta</a></span><span class="dx-q">%s</span></li>'
            % (d['n'], d['n'], d['dt'].isoformat(), d['dt'].strftime('%B %-d, %Y'), mmdd_key(d['dt']), E(ex)))

# ---------------------------------------------------------------- 4. drop pages
RE_FIG = re.compile(r'<!-- seo-img:begin -->.*?<!-- seo-img:end -->', re.S)
RE_XL = re.compile(r'<li class="xl">.*?</li>', re.S)
RE_LD = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)

def images_for(n):
    out = []
    for i in IMGS.get(str(n), []):
        key = i['src'][:-5]
        if key in MISSING_IMAGES: continue
        t = ITEXT.get(key)
        if not t: continue
        # an entry is either one string (alt text = caption) or {"alt": ..., "caption": ...}
        alt, cap = (t.get('alt', ''), t.get('caption') or t.get('alt', '')) if isinstance(t, dict) else (t, t)
        if not alt: continue
        out.append((i, alt, cap))
    return out

def patch_drops():
    with_img = 0; nimg = 0; sm_imgs = {}
    for d in DROPS:
        n = d['n']; f = 'drops/%d/index.html' % n
        if not os.path.exists(f): continue
        h0 = open(f, encoding='utf-8').read()
        h = RE_FIG.sub('', h0); h = RE_XL.sub('', h); h = RE_CSS.sub('', h)
        imgs = images_for(n)
        if imgs:
            with_img += 1; nimg += len(imgs)
            figs = ''
            for j, (i, t, cap) in enumerate(imgs):
                full = IMG_BASE + i['src']; sm = IMG_BASE + i.get('sm', i['src'])
                w, hh = i.get('sw') or i['w'], i.get('sh') or i['h']
                srcset = (' srcset="%s %dw, %s %dw" sizes="(max-width:640px) 100vw, 460px"' % (E(sm), w, E(full), i['w'])) if i['w'] > w else ''
                figs += ('<figure class="dimg"><a href="%s" target="_blank" rel="noopener"><img src="%s"%s width="%d" height="%d" alt="%s" loading="%s" decoding="async"></a>'
                         '<figcaption>%s</figcaption></figure>' % (E(full), E(sm), srcset, w, hh, E(t), 'eager' if j == 0 else 'lazy', E(cap)))
            label = 'Image attached to this drop' if len(imgs) == 1 else '%d images attached to this drop' % len(imgs)
            c = len(imgs); cols = 'one' if c == 1 else ('c2' if c in (2, 4, 8) else 'c3')
            block = '<!-- seo-img:begin --><section class="dimgs %s" aria-label="%s"><h2 class="dimgs-h">%s</h2>%s</section><!-- seo-img:end -->' % (cols, label, label, figs)
            h = h.replace('</article>', '</article>' + block, 1)
            h = h.replace('<link rel="stylesheet" href="%s">\n' % S.CSS_HREF, '<link rel="stylesheet" href="%s">\n' % S.CSS_HREF + DX_CSS, 1)
            sm_imgs[n] = [IMG_BASE + i['src'] for i, _, _ in imgs]
        k = mmdd_key(d['dt'])
        xl = '<li class="xl"><a href="/deltas/%s/">Q drop deltas for %s: every drop posted on this date</a></li>' % (k, mmdd_name(k))
        if d in QPLUS:
            xl += '<li class="xl"><a href="/q-proofs/">Q Proofs: this drop is signed Q+</a></li>'
        h = h.replace('<ul class="links">', '<ul class="links">' + xl, 1)
        # JSON-LD: add/refresh images on the CreativeWork
        m = RE_LD.search(h)
        if m:
            data = json.loads(m.group(1).replace('<\\/', '</'))
            for node in data['@graph']:
                if node.get('@id', '').endswith('/drops/%d/#drop' % n):
                    node.pop('image', None)
                    if imgs:
                        node['image'] = [{'@type': 'ImageObject', 'contentUrl': IMG_BASE + i['src'], 'url': IMG_BASE + i['src'], 'width': i['w'], 'height': i['h'],
                                          'thumbnailUrl': IMG_BASE + i.get('sm', i['src']), 'caption': cap, 'description': t} for i, t, cap in imgs]
            s = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
            h = h[:m.start(1)] + s + h[m.end(1):]
        if h != h0:
            open(f, 'w', encoding='utf-8').write(h)
    return with_img, nimg, sm_imgs

# ---------------------------------------------------------------- 5. /drops/ index line
def patch_index():
    f = 'drops/index.html'; h0 = open(f, encoding='utf-8').read()
    h = re.sub(r'<!-- seo-dx:begin -->.*?<!-- seo-dx:end -->', '', h0, flags=re.S); h = RE_CSS.sub('', h)
    h = h.replace('<link rel="stylesheet" href="%s">\n' % S.CSS_HREF, '<link rel="stylesheet" href="%s">\n' % S.CSS_HREF + DX_CSS, 1)
    line = ('<!-- seo-dx:begin --><p class="dx-more">Read the drops by calendar date in <a href="/deltas/">Q Drop Deltas</a>, every drop posted on each day of the year, '
            'and see the drops confirmed by President Trump in <a href="/q-proofs/">Q Proofs</a>.</p><!-- seo-dx:end -->')
    h = h.replace('</p><ul class="months">', '</p>' + line + '<ul class="months">', 1)
    if h != h0: open(f, 'w', encoding='utf-8').write(h)

# ---------------------------------------------------------------- 6. sitemaps
def sitemaps(sm_imgs):
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    out += ['  <url><loc>%s%s</loc><lastmod>%s</lastmod></url>' % (SITE, p, lm) for p, lm in SM]
    S.write('sitemaps/deltas.xml', '\n'.join(out + ['</urlset>\n']))
    idx = open('sitemap.xml', encoding='utf-8').read()
    idx = re.sub(r'\n  <sitemap><loc>[^<]*/sitemaps/deltas\.xml</loc>.*?</sitemap>', '', idx)
    idx = idx.replace('</sitemapindex>', '  <sitemap><loc>%s/sitemaps/deltas.xml</loc><lastmod>%s</lastmod></sitemap>\n</sitemapindex>' % (SITE, max(lm for _, lm in SM)))
    S.write('sitemap.xml', idx)
    lines = open('sitemaps/drops.xml', encoding='utf-8').read().split('\n')
    res = []
    for ln in lines:
        m = re.match(r'  <url><loc>%s/drops/(\d+)/</loc><lastmod>([^<]+)</lastmod>' % re.escape(SITE), ln)
        if m:
            n = int(m.group(1))
            ln = '  <url><loc>%s/drops/%d/</loc><lastmod>%s</lastmod>%s</url>' % (SITE, n, m.group(2), ''.join('<image:image><image:loc>%s</image:loc></image:image>' % E(u) for u in sm_imgs.get(n, [])))
        res.append(ln)
    S.write('sitemaps/drops.xml', '\n'.join(res))
    allu = 'sitemaps/all-urls.txt'
    if os.path.exists(allu):
        u = [x for x in open(allu).read().split('\n') if x and '/deltas/' not in x and '/q-proofs/' not in x]
        S.write(allu, '\n'.join(u + [SITE + p for p, _ in SM]) + '\n')

if __name__ == '__main__':
    S.write_pwa_data([[d['n'], int(d['dt'].timestamp())] for d in DROPS])
    nd = build_days(); build_hub(); build_proofs()
    wi, ni, smi = patch_drops(); patch_index(); sitemaps(smi)
    print('deltas day pages: %d, hub: 1, q-proofs: 1 (Q+ drops: %d), x posts linked: %d' % (nd, len(QPLUS), len(XPOSTS)))
    print('drop pages with image text: %d (%d images)' % (wi, ni))
