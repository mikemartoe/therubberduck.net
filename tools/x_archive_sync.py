#!/usr/bin/env python3
"""Nightly incremental sync of the X archive (x/) with new @TheRubberDuck79 posts.

Run from the repo root. Three steps:

  1. python3 tools/x_archive_sync.py plan
     Prints the last archived post id and the exact arguments for the fetch. The fetch is done by Grok Bot
     with its built-in X tool (namespace `x`, tool `get_users_posts`), one page of up to 25 posts per call,
     following meta.next_token until it is absent. Each raw response is saved as a .json file in one folder
     (any wrapper text around the JSON is ignored). No keys or tokens are used or stored by this script.

  2. python3 tools/x_archive_sync.py apply --drop <folder>
     Adds every post in the folder that is newer than the archive and not already in it (by post id):
     month shards (x/data/p), search postings (x/data/t), meta.json (count, months, ids, times, flags),
     facets.json, the per-year downloads (x/data/dl), the affected month pages under x/archive/ and the
     month index (keeping hand fixes such as Wayback links), sitemaps/x.xml, sitemaps/all-urls.txt, the
     sitemap index, and the post count / date range text in x/index.html and assets/search/site-index.json.
     Text is kept exactly as posted, except Wikipedia links, which become plain "(ref: Topic)" (Duck's rule).
     Re-running with the same folder adds nothing (idempotent).

  3. python3 tools/x_archive_sync.py verify
     Integrity checks: counts agree everywhere, no duplicate ids, time order, every shard parses, the
     newest post is findable in search, month pages exist for every month with posts. Exit code 1 on failure.
"""
import argparse, collections, csv, datetime, glob, gzip, html, importlib.util, io, json, os, re, sys, unicodedata, urllib.parse
from urllib.parse import urlsplit

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(ROOT)
D = 'x/data/'
HANDLE = 'TheRubberDuck79'
MYID = '1254803542914850816'
SITE = 'https://therubberduck.net'
TODAY = datetime.date.today().isoformat()
FETCH = {
    'id': MYID, 'max_results': 100,
    'post.fields': 'id,text,created_at,lang,public_metrics,entities,referenced_tweets,in_reply_to_user_id,conversation_id,attachments,note_tweet,author_id',
    'expansions': 'attachments.media_keys,referenced_tweets.id,referenced_tweets.id.author_id,in_reply_to_user_id,referenced_tweets.id.attachments.media_keys',
    'media.fields': 'media_key,type,url,preview_image_url,variants', 'user.fields': 'id,username'}

# ---------------------------------------------------------------- shared with tools/x-archive-build.py
B36 = '0123456789abcdefghijklmnopqrstuvwxyz'
def b36(n):
    s = ''
    while True:
        n, r = divmod(n, 36); s = B36[r] + s
        if not n: return s
SLD = {'co.uk', 'com.au', 'co.jp', 'co.nz', 'org.uk', 'com.br', 'co.za', 'co.in', 'gov.uk', 'ac.uk'}
def hosts(u):
    try: h = (urlsplit(u).hostname or '').lower()
    except Exception: return []
    if not h: return []
    if h.startswith('www.'): h = h[4:]
    out = {h}; parts = h.split('.')
    if len(parts) > 2:
        out.add('.'.join(parts[-3:]) if '.'.join(parts[-2:]) in SLD else '.'.join(parts[-2:]))
    return sorted(out)
WORD = re.compile(r'[^\W]+', re.U)
def norm(s):
    s = unicodedata.normalize('NFKD', s.lower())
    return ''.join(ch for ch in s if not unicodedata.combining(ch))
def toks(s): return set(WORD.findall(norm(s)))
def skey(t):
    c = t[0]
    if c == '~': return 'd'
    cls = {'#': 'h', '@': 'm'}.get(c)
    if cls: t = t[1:]
    else: cls = 'w'
    k = ''.join(ch if ch in B36 else '_' for ch in t[:2])
    if cls != 'w': k = k[:1]
    return cls + k
MT = {'photo': 'p', 'video': 'v', 'animated_gif': 'g'}

# ---------------------------------------------------------------- Q tier (same rules as the original export build)
STRONG = [('Q', r'(?<![\w$])Q(?![\w\'’])'), ('Q+', r'(?<!\w)Q\+'), ('Qanon', r'q[\s-]?anon'), ('WWG1WGA', r'wwg1wga'),
          ('Q post', r'\bq[\s-]?posts?\b'), ('Q drop', r'\bq[\s-]?drops?\b'), ('qanon.pub', r'qanon\.pub'), ('qagg', r'qagg'),
          ('qalerts', r'qalerts'), ('qmap', r'qmap'), ('8kun', r'8kun'), ('8ch', r'8ch(?:an)?\b'), ('Trust the plan', r'trust\s*the\s*plan'),
          ('Great Awakening', r'great\s*awakening'), ('Dark to Light', r'dark\s*to\s*light'), ('Digital soldiers', r'digital\s*soldiers?')]
BROAD = [('drop', r'\bdrops?\b'), ('anon', r'\banons?\b'), ('POTUS', r'\bpotus\b'), ('Patriots', r'\bpatriots?\b'),
         ('Storm', r'\bstorm\b'), ('Durham', r'\bdurham\b'), ('Comey', r'\bcomey\b'), ('Clinton', r'\bclintons?\b')]
QTAG = re.compile(r'^(q|qanon\w*|q\w*army|wwg1wga\w*|\w*wwg1wga|trusttheplan|thegreatawakening|greatawakening|thestorm\w*|stormiscoming|darktolight|digitalsoldiers?|qproof\w*|qsentme|qdrops?|qpost\w*|qarmy|thestormishere|qresearch|followthewhiterabbit|enjoytheshow|nothingcanstopwhatiscoming)$', re.I)
def q_tier(r):
    hay = r['full_text_expanded'] + ' ' + ' '.join(r['urls'])
    s = [n for n, p in STRONG if re.search(p, hay, 0 if n in ('Q', 'Q+') else re.I)]
    tags = [h for h in r['hashtags'] if QTAG.match(h)]
    b = [n for n, p in BROAD if re.search(p, hay, re.I)]
    return 1 if (s or tags) else (2 if b else 0)

# ---------------------------------------------------------------- Wikipedia rule (same regex as tools/strip_wikipedia.py)
WIKI = re.compile(r'https?://\s?(?:[a-z]{2}\.)?(?:m\.)?wikipedia\.org/wiki/([^\s"<>\\)\]]+)')
def _topic(m):
    t = m.group(1).split('#')[0]
    t = html.unescape(urllib.parse.unquote(t)).replace('_', ' ').strip()
    return '(ref: ' + html.escape(t, quote=False) + ')'
def nowiki(v):
    if isinstance(v, str): return WIKI.sub(_topic, v)
    if isinstance(v, list): return [nowiki(x) for x in v]
    if isinstance(v, dict): return {k: nowiki(x) for k, x in v.items()}
    return v

# ---------------------------------------------------------------- reading the fetched pages
def load_page(path):
    s = open(path, encoding='utf-8').read()
    i = s.find('{"')
    if i < 0: return None
    return json.JSONDecoder().raw_decode(s[i:])[0]

STATUS_RE = re.compile(r'https?://(?:www\.|mobile\.)?(?:twitter|x)\.com/(\w+)/status(?:es)?/(\d+)', re.I)
def xurl(u):
    # the X export writes status links as https://x.com/...; the API still expands some to twitter.com
    return re.sub(r'^https?://(?:www\.|mobile\.)?twitter\.com/', 'https://x.com/', u) if u and STATUS_RE.match(u) else u

def to_record(t, inc):
    """API v2 post -> one record in the same shape as the X export index (x-archive-2026-09/index.jsonl)."""
    tid = t['id']
    raw = html.unescape(t['text'])
    refs = {r['type']: r['id'] for r in t.get('referenced_tweets', [])}
    note = t.get('note_tweet')
    ent = t.get('entities', {}) or {}
    if note:
        lead = re.match(r'^((?:@\w+\s+)+)', raw)
        prefix = lead.group(1) if lead and not note['text'].startswith('@') else ''
        full = prefix + note['text']; text_source = 'note-tweet'
    else:
        full = raw; text_source = 'tweets'
    urls, url_map, media_link = [], {}, {}
    for u in ent.get('urls', []):
        e = xurl(u.get('expanded_url') or u.get('url'))
        url_map[u.get('url')] = e
        if u.get('media_key'): media_link[u['media_key']] = (e, u.get('url'))
        else: urls.append(e)
    nent = (note or {}).get('entities', {}) or {}
    for u in nent.get('urls', []):
        e = xurl(u.get('expanded_url') or u.get('url'))
        url_map[u.get('url')] = e
        if u.get('media_key'): media_link.setdefault(u['media_key'], (e, u.get('url')))
        elif e not in urls: urls.append(e)
    is_rt = t['text'].startswith('RT @')
    mo = re.match(r'RT @(\w+):', t['text'])
    rt_of = mo.group(1) if is_rt and mo else None
    # media: the post's own attachments; for a repost with none, the reposted post's attachments
    mkeys = (t.get('attachments') or {}).get('media_keys') or []
    if not mkeys and 'retweeted' in refs:
        mkeys = (inc['tweets'].get(refs['retweeted'], {}).get('attachments') or {}).get('media_keys') or []
    media = []
    for k in mkeys:
        m = inc['media'].get(k)
        if not m: continue
        vurl = vbr = None
        mp4 = [v for v in m.get('variants', []) if v.get('content_type') == 'video/mp4']
        if mp4:
            best = max(mp4, key=lambda v: int(v.get('bit_rate', 0) or 0))
            vurl = best['url']; vbr = int(best.get('bit_rate', 0) or 0)
        exp, tco = media_link.get(k, (None, None))
        media.append({'type': m['type'], 'media_url_https': m.get('url') or m.get('preview_image_url'),
                      'video_url': vurl, 'video_bitrate': vbr, 'expanded_url': exp, 'tco_url': tco,
                      'archive_media_path': None})
    full_expanded = re.sub(r'https://t\.co/\w+', lambda mo: url_map.get(mo.group(0)) or mo.group(0), full)
    hashtags, mentions = [], []
    for e in (ent, nent):
        for h in e.get('hashtags', []):
            if h.get('tag') and h['tag'] not in hashtags: hashtags.append(h['tag'])
        for u in e.get('mentions', []):
            if u.get('username') and u['username'] not in mentions: mentions.append(u['username'])
    rep_uid = t.get('in_reply_to_user_id')
    rep_sid = refs.get('replied_to')
    is_reply = (not is_rt) and bool(rep_sid or rep_uid)
    rep_name = None
    if is_reply:
        if rep_uid and rep_uid in inc['users']: rep_name = inc['users'][rep_uid]
        elif rep_sid and inc['tweets'].get(rep_sid, {}).get('author_id') in inc['users']:
            rep_name = inc['users'][inc['tweets'][rep_sid]['author_id']]
    quoted = None
    if not is_rt:
        for u in urls:
            m2 = STATUS_RE.match(u or '')
            if m2 and m2.group(2) != tid: quoted = u; break
        if not quoted and 'quoted' in refs:
            qa = inc['tweets'].get(refs['quoted'], {}).get('author_id')
            quoted = 'https://x.com/%s/status/%s' % (inc['users'].get(qa, 'i/web'), refs['quoted'])
            urls.append(quoted)
    pm = t.get('public_metrics', {}) or {}
    return {
        'id': tid, 'created_at': t['created_at'][:19] + 'Z',
        'tweet_url': 'https://x.com/%s/status/%s' % (HANDLE, tid),
        'type': 'retweet' if is_rt else ('reply' if is_reply else 'original'),
        'is_reply': is_reply, 'is_retweet': is_rt, 'is_quote': bool(quoted),
        'is_self_thread': is_reply and rep_uid == MYID,
        'in_reply_to_screen_name': rep_name if is_reply else None,
        'in_reply_to_user_id': rep_uid if is_reply else None,
        'in_reply_to_status_id': rep_sid if is_reply else None,
        'in_reply_to_url': ('https://x.com/%s/status/%s' % (rep_name or 'i/web', rep_sid)) if (is_reply and rep_sid) else None,
        'retweet_of_screen_name': rt_of, 'quoted_tweet_url': quoted,
        'full_text': full, 'full_text_expanded': full_expanded, 'text_source': text_source,
        'urls': urls, 'media': media, 'hashtags': hashtags, 'user_mentions': mentions,
        # a repost's counts on X belong to the original post; the export records 0 for reposts
        'favorite_count': 0 if is_rt else int(pm.get('like_count', 0) or 0),
        'retweet_count': 0 if is_rt else int(pm.get('retweet_count', 0) or 0),
        'lang': t.get('lang'),
    }

def read_drop(folder):
    posts = {}; files = sorted(glob.glob(os.path.join(folder, '*.json')))
    for f in files:
        j = load_page(f)
        if not j: continue
        inc = {'media': {m['media_key']: m for m in j.get('includes', {}).get('media', [])},
               'tweets': {x['id']: x for x in j.get('includes', {}).get('tweets', [])},
               'users': {u['id']: u['username'] for u in j.get('includes', {}).get('users', [])}}
        for t in j.get('data', []) or []:
            if t.get('author_id', MYID) != MYID: continue
            if t['id'] not in posts: posts[t['id']] = to_record(t, inc)
    return files, list(posts.values())

# ---------------------------------------------------------------- helpers for the site files
def jload(p): return json.load(open(p, encoding='utf-8'))
def jdump(o, p, ascii=False):
    s = json.dumps(o, ensure_ascii=ascii, separators=(',', ':'))
    with open(p, 'w', encoding='utf-8') as f: f.write(s)
def unix(c): return int(datetime.datetime.strptime(c, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc).timestamp())
def decode_last(enc):
    i = -1
    for x in enc.split('.'): i += int(x, 36) + 1
    return i
def month_name(mk): return datetime.date(int(mk[:4]), int(mk[5:7]), 1).strftime('%B %Y')

def short(p, q):
    r = {'i': p['id'], 'c': p['created_at'], 'y': {'original': 'o', 'reply': 'r', 'retweet': 't'}[p['type']], 'x': p['full_text_expanded']}
    if p['tweet_url'] != 'https://x.com/%s/status/%s' % (HANDLE, p['id']): r['tu'] = p['tweet_url']
    if p['is_quote']: r['qt'] = 1
    if p['is_self_thread']: r['st'] = 1
    if p['in_reply_to_screen_name']: r['rn'] = p['in_reply_to_screen_name']
    if p['in_reply_to_status_id']: r['ri'] = p['in_reply_to_status_id']
    if p['in_reply_to_url'] and p['in_reply_to_url'] != 'https://x.com/%s/status/%s' % (p['in_reply_to_screen_name'], p['in_reply_to_status_id']): r['ru'] = p['in_reply_to_url']
    if p['retweet_of_screen_name']: r['rt'] = p['retweet_of_screen_name']
    if p['quoted_tweet_url']: r['qu'] = p['quoted_tweet_url']
    if p['media']:
        r['m'] = [[MT[m['type']], m['media_url_https']] + ([m['video_url']] if m.get('video_url') else []) for m in p['media']]
    for k, s in (('h', 'hashtags'), ('mn', 'user_mentions'), ('u', 'urls')):
        if p[s]: r[k] = p[s]
    if p['favorite_count']: r['f'] = int(p['favorite_count'])
    if p['retweet_count']: r['r'] = int(p['retweet_count'])
    if p['lang']: r['l'] = p['lang']
    if p['text_source'] != 'tweets': r['s'] = p['text_source']
    if q: r['q'] = q
    return r

def flags(p, q):
    f = {'original': 0, 'reply': 1, 'retweet': 2}[p['type']]
    if p['is_quote']: f |= 4
    if p['is_self_thread']: f |= 8
    mt = {m['type'] for m in p['media']}
    if 'photo' in mt: f |= 16
    if 'video' in mt: f |= 32
    if 'animated_gif' in mt: f |= 64
    if q == 1: f |= 128
    if q == 2: f |= 256
    if p['urls']: f |= 512
    return f

def terms_of(p):
    terms = toks(p['full_text_expanded'])
    for h in {x.lower() for x in p['hashtags']}: terms.add('#' + norm(h))
    for h in {x.lower() for x in p['user_mentions']}: terms.add('@' + h)
    for u in p['urls'] + ([p['quoted_tweet_url']] if p['quoted_tweet_url'] else []):
        for d in hosts(u): terms.add('~' + d)
    return terms

# ---------------------------------------------------------------- month pages via tools/seo-build.py (captured, not written)
def seo_module():
    spec = importlib.util.spec_from_file_location('seo_build', os.path.join(ROOT, 'tools', 'seo-build.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def render_x(seo):
    out = {}
    seo.write = lambda path, text: out.__setitem__(path, text)
    seo.SITEMAPS.clear(); seo.build_x()
    return out
HREF = re.compile(r'href="([^"]*)"')
def hand_fixes(generated, committed):
    """Map of href changes made by hand after generation (e.g. dead links -> Wayback). None if anything else differs."""
    a, b = HREF.findall(generated), HREF.findall(committed)
    if len(a) != len(b): return None
    fx = {x: y for x, y in zip(a, b) if x != y}
    redo = HREF.sub(lambda m: 'href="%s"' % fx.get(m.group(1), m.group(1)), generated)
    return fx if redo == committed else None

# ---------------------------------------------------------------- apply
def apply(drop, dry=False):
    meta = jload(D + 'meta.json')
    n0 = meta['n']; have = set(meta['ids'])
    ts_abs = []; acc = 0
    for v in meta['ts']: acc += v; ts_abs.append(acc)
    files, recs = read_drop(drop)
    new = [p for p in recs if p['id'] not in have]
    last_c = datetime.datetime.fromtimestamp(ts_abs[-1], datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    last_key = (last_c, int(meta['ids'][-1]))
    older = [p for p in new if (p['created_at'], int(p['id'])) <= last_key]
    if older:
        print('WARNING: %d fetched post(s) are older than the newest archived post and are not in the archive; '
              'they are skipped (adding them would renumber the search index): %s' % (len(older), ', '.join(p['id'] for p in older[:10])))
    new = sorted([p for p in new if (p['created_at'], int(p['id'])) > last_key], key=lambda p: (p['created_at'], int(p['id'])))
    rep = {'files': len(files), 'fetched': len(recs), 'already_in_archive': len(recs) - len(new) - len(older), 'skipped_older': len(older), 'added': len(new)}
    if not new:
        rep['n'] = n0; print(json.dumps(rep)); return rep
    if dry:
        rep['would_be_n'] = n0 + len(new); print(json.dumps(rep)); return rep

    seo = seo_module()
    before = render_x(seo)                                   # pages as the generator makes them from today's data
    old_meta_end = month_name(last_c[:7])

    # 1. month shards + reply children
    shards = {}
    def shard(mk):
        if mk not in shards:
            shards[mk] = jload(D + 'p/%s.json' % mk) if os.path.exists(D + 'p/%s.json' % mk) else []
        return shards[mk]
    month_start = [(m, s) for m, s in meta['months']]
    def month_of(i):
        mk = None
        for m, s in month_start:
            if s <= i: mk = m
            else: break
        return mk
    idx = {pid: i for i, pid in enumerate(meta['ids'])}
    postings = collections.defaultdict(list)
    touched_months = set()
    for p in new:
        p_clean = nowiki(p)                                   # Duck's no-Wikipedia rule, applied to everything shown
        q = q_tier(p)
        i = meta['n']; mk = p['created_at'][:7]
        if not meta['months'] or meta['months'][-1][0] != mk:
            meta['months'].append([mk, i]); month_start.append((mk, i))
        shard(mk).append(short(p_clean, q)); touched_months.add(mk)
        meta['ids'].append(p['id']); meta['ts'].append(unix(p['created_at']) - ts_abs[-1]); ts_abs.append(unix(p['created_at']))
        meta['fl'].append(flags(p, q)); meta['n'] += 1; idx[p['id']] = i
        parent = p['in_reply_to_status_id']
        if parent and parent in idx:
            pm = month_of(idx[parent]); rows = shard(pm)
            for r in rows:
                if r['i'] == parent:
                    if p['id'] not in r.get('k', []): r.setdefault('k', []).append(p['id']); touched_months.add(pm)
                    break
        for t in terms_of(p_clean): postings[t].append(i)
        p['_q'] = q; p['_clean'] = p_clean
    for mk in touched_months: jdump(shards[mk], D + 'p/%s.json' % mk)

    # 2. search postings (indices only grow, so new ones append to the end of each list)
    byshard = collections.defaultdict(dict)
    for t, pl in postings.items(): byshard[skey(t)][t] = pl
    for k, terms in byshard.items():
        path = D + 't/%s.json' % k
        sh = jload(path) if os.path.exists(path) else {}
        for t, pl in terms.items():
            prev = decode_last(sh[t]) if t in sh else -1
            enc = []
            for x in pl: enc.append(b36(x - prev - 1)); prev = x
            sh[t] = (sh[t] + '.' if t in sh else '') + '.'.join(enc)
        jdump(sh, path)
    meta['shards'] = sorted(set(meta['shards']) | set(byshard))
    meta['synced'] = TODAY
    jdump(meta, D + 'meta.json', ascii=True)

    # 3. facets: totals from the postings; ties keep their current order
    fac = jload(D + 'facets.json')
    tot = {'h': {}, 'm': {}, 'd': {}}
    for f in glob.glob(D + 't/*.json'):
        for t, v in jload(f).items():
            c = {'#': 'h', '@': 'm', '~': 'd'}.get(t[0])
            if c: tot[c][t[1:]] = v.count('.') + 1
    for c in 'hmd':
        order = [a for a, _ in fac[c]]; seen = set(order)
        order += [a for a, _ in sorted(tot[c].items(), key=lambda kv: -kv[1]) if a not in seen]
        rows = [[a, tot[c].get(a, 0)] for a in order]
        rows.sort(key=lambda r: -r[1])                      # stable sort
        fac[c] = [r for r in rows if r[1] >= 2][:3000]
        fac['counts'][c] = len(tot[c])
    jdump(fac, D + 'facets.json')

    # 4. downloads per year (append; existing lines kept byte for byte)
    cols = ['id','created_at','tweet_url','type','is_reply','is_retweet','is_quote','is_self_thread','q_tier','in_reply_to_screen_name','in_reply_to_user_id','in_reply_to_status_id','in_reply_to_url','retweet_of_screen_name','quoted_tweet_url','full_text','full_text_expanded','text_source','urls','media_types','media_urls','video_urls','media_expanded_urls','hashtags','user_mentions','favorite_count','retweet_count','lang']
    files_json = jload(D + 'dl/files.json'); fj = {r[0]: r for r in files_json}
    byy = collections.defaultdict(list)
    for p in new: byy[p['created_at'][:4]].append(p)
    for y, ps in byy.items():
        jp, cp = D + 'dl/posts-%s.jsonl.gz' % y, D + 'dl/posts-%s.csv.gz' % y
        old_lines = gzip.open(jp, 'rt', encoding='utf-8').read() if os.path.exists(jp) else ''
        old_ids = set(re.findall(r'^\{"id": "(\d+)"', old_lines, re.M))
        ps = [p for p in ps if p['id'] not in old_ids]
        old_csv = gzip.open(cp, 'rt', encoding='utf-8', newline='').read() if os.path.exists(cp) else ''
        buf = io.StringIO(); w = csv.writer(buf)
        if not old_csv: w.writerow(cols)
        add = ''
        J = lambda L: ' | '.join(L)
        for p in ps:
            c = p['_clean']; o = {k: v for k, v in c.items() if not k.startswith('_')}
            o['q_tier'] = {1: 'strong', 2: 'broad'}.get(p['_q'])
            add += json.dumps(o, ensure_ascii=False) + '\n'
            o = dict(o); o['q_tier'] = o['q_tier'] or ''
            m = c['media']
            o['media_types'] = J(x['type'] for x in m); o['media_urls'] = J(x['media_url_https'] for x in m)
            o['video_urls'] = J(x['video_url'] or '' for x in m) if any(x['video_url'] for x in m) else ''
            o['media_expanded_urls'] = J(x['expanded_url'] or '' for x in m)
            for k in ('urls', 'hashtags', 'user_mentions'): o[k] = J(c[k])
            w.writerow(['' if o.get(k) is None else o.get(k) for k in cols])
        with gzip.open(jp, 'wt', encoding='utf-8', compresslevel=9) as g: g.write(old_lines + add)
        with gzip.open(cp, 'wt', encoding='utf-8', newline='', compresslevel=9) as g: g.write(old_csv + buf.getvalue())
        cnt = (fj[y][1] if y in fj else 0) + len(ps)
        row = [y, cnt, os.path.getsize(jp), os.path.getsize(cp)]
        if y in fj: fj[y][:] = row
        else: files_json.append(row)
    files_json.sort(key=lambda r: r[0])
    with open(D + 'dl/files.json', 'w') as f: json.dump(files_json, f)

    # 5. month pages + month index (only the pages whose content changed; hand fixes carried over)
    after = render_x(seo)
    changed_pages = []
    for path, text in sorted(after.items()):
        if before.get(path) == text: continue
        if os.path.exists(path):
            cur = open(path, encoding='utf-8').read()
            fx = {} if before.get(path) == cur else hand_fixes(before.get(path, ''), cur)
            if fx is None:
                raise SystemExit('STOP: %s was edited by hand in a way this script cannot carry over. Nothing else in it was changed; '
                                 'data files are already updated, so fix the page by hand or run git checkout to undo.' % path)
            text = HREF.sub(lambda m: 'href="%s"' % fx.get(m.group(1), m.group(1)), text)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f: f.write(text)
        changed_pages.append(path)

    # 6. sitemaps
    month_urls = [SITE + '/' + p[:-len('index.html')] for p in sorted(after) if re.match(r'x/archive/\d{4}-\d{2}/index\.html$', p)]
    changed_urls = {SITE + '/' + p[:-len('index.html')] for p in changed_pages}
    sm = open('sitemaps/x.xml', encoding='utf-8').read()
    for u in month_urls:
        if '<loc>%s</loc>' % u not in sm:
            sm = sm.replace('  <url><loc>%s/x/archive/</loc>' % SITE, '  <url><loc>%s</loc><lastmod>%s</lastmod></url>\n  <url><loc>%s/x/archive/</loc>' % (u, TODAY, SITE))
    for u in changed_urls:
        sm = re.sub(r'(<url><loc>%s</loc><lastmod>)[^<]*' % re.escape(u), r'\g<1>' + TODAY, sm)
    open('sitemaps/x.xml', 'w', encoding='utf-8').write(sm)
    au = open('sitemaps/all-urls.txt', encoding='utf-8').read()
    for u in month_urls:
        if '\n' + u + '\n' not in au:
            au = au.replace('\n%s/x/archive/\n' % SITE, '\n%s\n%s/x/archive/\n' % (u, SITE))
    open('sitemaps/all-urls.txt', 'w', encoding='utf-8').write(au)

    # 7. count and date range text outside x/data
    new_end = month_name(new[-1]['created_at'][:7])
    first = month_name(datetime.datetime.fromtimestamp(ts_abs[0], datetime.timezone.utc).strftime('%Y-%m'))
    xi_changed = False
    import subprocess
    footers = subprocess.run(['git', 'grep', '-l', '-F', '%s X posts' % format(n0, ','), '--', '*.html', ':!x/archive/*'],
                             capture_output=True, text=True).stdout.split()
    for f in sorted(set(['x/index.html', 'assets/search/site-index.json'] + footers)):
        s = open(f, encoding='utf-8').read(); o = s
        s = s.replace('%s to %s' % (first, old_meta_end), '%s to %s' % (first, new_end))
        s = s.replace('%s X posts' % format(n0, ','), '%s X posts' % format(meta['n'], ','))
        s = s.replace('"xPosts":%d' % n0, '"xPosts":%d' % meta['n'])
        if s != o:
            open(f, 'w', encoding='utf-8').write(s)
            if f == 'x/index.html': xi_changed = True
    si = open('sitemap.xml', encoding='utf-8').read()
    si = re.sub(r'(<loc>%s/sitemaps/x\.xml</loc><lastmod>)[^<]*' % re.escape(SITE), r'\g<1>' + TODAY, si)
    if xi_changed:
        pg = open('sitemaps/pages.xml', encoding='utf-8').read()
        pg2 = re.sub(r'(<loc>%s/x/</loc><lastmod>)[^<]*' % re.escape(SITE), r'\g<1>' + TODAY, pg)
        if pg2 != pg:
            open('sitemaps/pages.xml', 'w', encoding='utf-8').write(pg2)
            si = re.sub(r'(<loc>%s/sitemaps/pages\.xml</loc><lastmod>)[^<]*' % re.escape(SITE), r'\g<1>' + TODAY, si)
    open('sitemap.xml', 'w', encoding='utf-8').write(si)

    rep.update({'n_before': n0, 'n': meta['n'], 'first_new': [new[0]['id'], new[0]['created_at']], 'last_new': [new[-1]['id'], new[-1]['created_at']],
                'months_touched': sorted(touched_months), 'pages_written': changed_pages,
                'by_type': dict(collections.Counter(p['type'] for p in new)), 'q': dict(collections.Counter(p['_q'] for p in new))})
    print(json.dumps(rep, indent=1))
    return rep

# ---------------------------------------------------------------- verify
def verify():
    errs = []
    meta = jload(D + 'meta.json'); n = meta['n']
    for k in ('ids', 'ts', 'fl'):
        if len(meta[k]) != n: errs.append('meta.%s has %d entries, n=%d' % (k, len(meta[k]), n))
    if len(set(meta['ids'])) != len(meta['ids']): errs.append('duplicate ids in meta')
    if any(v < 0 for v in meta['ts'][1:]): errs.append('times not in order')
    tot = 0; seen = set()
    for j, (mk, s) in enumerate(meta['months']):
        rows = jload(D + 'p/%s.json' % mk)
        e = meta['months'][j + 1][1] if j + 1 < len(meta['months']) else n
        if len(rows) != e - s: errs.append('%s: %d rows, months says %d' % (mk, len(rows), e - s))
        for i, r in enumerate(rows):
            if r['i'] != meta['ids'][s + i]: errs.append('%s row %d id mismatch' % (mk, i)); break
            if r['c'][:7] != mk: errs.append('%s row %d in wrong month' % (mk, i)); break
            seen.add(r['i'])
        tot += len(rows)
    if tot != n or len(seen) != n: errs.append('shards hold %d rows / %d unique, n=%d' % (tot, len(seen), n))
    for k in meta['shards']:
        if not os.path.exists(D + 't/%s.json' % k): errs.append('missing term shard ' + k)
    # newest post findable: every word of it must list its index
    last = jload(D + 'p/%s.json' % meta['months'][-1][0])[-1]
    words = sorted(toks(last['x']), key=len, reverse=True)[:5]
    for w in words:
        sh = jload(D + 't/%s.json' % skey(w))
        if w not in sh or decode_last(sh[w]) != n - 1: errs.append('search term %r does not find the newest post' % w)
    files = jload(D + 'dl/files.json')
    if sum(r[1] for r in files) != n: errs.append('dl/files.json counts %d, n=%d' % (sum(r[1] for r in files), n))
    for mk, _ in meta['months']:
        rows = jload(D + 'p/%s.json' % mk)
        if any(r['y'] == 'o' for r in rows) and not os.path.exists('x/archive/%s/index.html' % mk):
            errs.append('no month page for ' + mk)
    s = open('assets/search/site-index.json', encoding='utf-8').read()
    if '"xPosts":%d' % n not in s: errs.append('site-index.json xPosts is not %d' % n)
    import subprocess
    stale = [l for l in subprocess.run(['git', 'grep', '-n', '-E', r'memes and [0-9,]+ X posts', '--', '*.html'], capture_output=True, text=True).stdout.splitlines()
             if 'memes and %s X posts' % format(n, ',') not in l]
    if stale: errs.append('footer count not %s in: %s' % (format(n, ','), ', '.join(l.split(':')[0] for l in stale)))
    for f in glob.glob(D + 'p/*.json'):
        if 'wikipedia.org/wiki' in open(f, encoding='utf-8').read(): errs.append('Wikipedia link in ' + f)
    end = datetime.datetime.fromtimestamp(sum(meta['ts']), datetime.timezone.utc)
    print(json.dumps({'n': n, 'months': len(meta['months']), 'newest': [meta['ids'][-1], end.strftime('%Y-%m-%d %H:%M:%S UTC')],
                      'checked_words': words, 'errors': errs}, indent=1, ensure_ascii=False))
    return not errs

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    sp.add_parser('plan')
    a = sp.add_parser('apply'); a.add_argument('--drop', required=True); a.add_argument('--dry-run', action='store_true')
    sp.add_parser('verify')
    o = ap.parse_args()
    if o.cmd == 'plan':
        meta = jload(D + 'meta.json')
        print(json.dumps({'since_id': meta['ids'][-1], 'n': meta['n'], 'tool': 'x.get_users_posts (Grok Bot built-in X tool)',
                          'arguments': dict(FETCH, since_id=meta['ids'][-1]),
                          'paging': 'repeat with "pagination_token": <meta.next_token> until next_token is absent; save each response as NNN.json in one folder'}, indent=1))
    elif o.cmd == 'apply':
        apply(o.drop, o.dry_run)
    else:
        sys.exit(0 if verify() else 1)
