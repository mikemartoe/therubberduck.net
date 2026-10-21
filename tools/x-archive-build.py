import json, csv, re, os, gzip, shutil, collections, unicodedata
from urllib.parse import urlsplit
SRC='/workspace/therubberduck/x-archive-2026-09/'
OUT='/workspace/trd-site/x/data/'
shutil.rmtree(OUT, ignore_errors=True)
for d in ('p','t','dl'): os.makedirs(OUT+d)
B36='0123456789abcdefghijklmnopqrstuvwxyz'
def b36(n):
    s=''
    while True:
        n,r=divmod(n,36); s=B36[r]+s
        if not n: return s
qt={}
for r in csv.DictReader(open(SRC+'q-related.csv',encoding='utf-8')):
    qt[r['id']]=1 if r['tier']=='strong' else 2
posts=[json.loads(l) for l in open(SRC+'index.jsonl',encoding='utf-8')]
assert len(posts)==61225 and len({p['id'] for p in posts})==61225
posts.sort(key=lambda p:(p['created_at'],int(p['id'])))
ids={p['id']:i for i,p in enumerate(posts)}
kids=collections.defaultdict(list)
for p in posts:
    if p['in_reply_to_status_id'] in ids: kids[p['in_reply_to_status_id']].append(p['id'])
SLD={'co.uk','com.au','co.jp','co.nz','org.uk','com.br','co.za','co.in','gov.uk','ac.uk'}
def hosts(u):
    try: h=(urlsplit(u).hostname or '').lower()
    except Exception: return []
    if not h: return []
    if h.startswith('www.'): h=h[4:]
    out={h}; parts=h.split('.')
    if len(parts)>2:
        base='.'.join(parts[-3:]) if '.'.join(parts[-2:]) in SLD else '.'.join(parts[-2:])
        out.add(base)
    return sorted(out)
WORD=re.compile(r'[^\W]+',re.U)
def norm(s):
    s=unicodedata.normalize('NFKD',s.lower())
    return ''.join(ch for ch in s if not unicodedata.combining(ch))
def toks(s): return set(WORD.findall(norm(s)))
MT={'photo':'p','video':'v','animated_gif':'g'}
postings=collections.defaultdict(list)
months=[]; shard=[]; cur=None
fl=[]; ts=[]; idl=[]
fac={'h':collections.Counter(),'m':collections.Counter(),'d':collections.Counter()}
hcase={}
import datetime
for i,p in enumerate(posts):
    mo=p['created_at'][:7]
    if mo!=cur:
        if shard: json.dump(shard,open(f'{OUT}p/{cur}.json','w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
        cur=mo; shard=[]; months.append([mo,i])
    r={'i':p['id'],'c':p['created_at'],'y':{'original':'o','reply':'r','retweet':'t'}[p['type']],'x':p['full_text_expanded']}
    if p['tweet_url']!='https://x.com/TheRubberDuck79/status/'+p['id']: r['tu']=p['tweet_url']
    if p['is_quote']: r['qt']=1
    if p['is_self_thread']: r['st']=1
    if p['in_reply_to_screen_name']: r['rn']=p['in_reply_to_screen_name']
    if p['in_reply_to_status_id']: r['ri']=p['in_reply_to_status_id']
    if p['in_reply_to_url'] and p['in_reply_to_url']!=f"https://x.com/{p['in_reply_to_screen_name']}/status/{p['in_reply_to_status_id']}": r['ru']=p['in_reply_to_url']
    if p['retweet_of_screen_name']: r['rt']=p['retweet_of_screen_name']
    if p['quoted_tweet_url']: r['qu']=p['quoted_tweet_url']
    if p['media']:
        ms=[]
        for m in p['media']:
            e=[MT[m['type']],m['media_url_https']]
            if m.get('video_url'): e.append(m['video_url'])
            ms.append(e)
        r['m']=ms
    for k,s in (('h','hashtags'),('mn','user_mentions'),('u','urls')):
        if p[s]: r[k]=p[s]
    if p['favorite_count']: r['f']=int(p['favorite_count'])
    if p['retweet_count']: r['r']=int(p['retweet_count'])
    if p['lang']: r['l']=p['lang']
    if p['text_source']!='tweets': r['s']=p['text_source']
    q=qt.get(p['id'],0)
    if q: r['q']=q
    if p['id'] in kids: r['k']=kids[p['id']]
    shard.append(r)
    # meta
    f={'original':0,'reply':1,'retweet':2}[p['type']]
    if p['is_quote']: f|=4
    if p['is_self_thread']: f|=8
    mt={m['type'] for m in p['media']}
    if 'photo' in mt: f|=16
    if 'video' in mt: f|=32
    if 'animated_gif' in mt: f|=64
    if q==1: f|=128
    if q==2: f|=256
    if p['urls']: f|=512
    fl.append(f); idl.append(p['id'])
    ts.append(int(datetime.datetime.strptime(p['created_at'],'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc).timestamp()))
    terms=toks(p['full_text_expanded'])
    for h in {x.lower() for x in p['hashtags']}:
        terms.add('#'+norm(h)); fac['h'][norm(h)]+=1
    for h in {x.lower() for x in p['user_mentions']}:
        terms.add('@'+h); fac['m'][h]+=1
    ds=set()
    for u in p['urls']+([p['quoted_tweet_url']] if p['quoted_tweet_url'] else []):
        ds.update(hosts(u))
    for d in ds: terms.add('~'+d); fac['d'][d]+=1
    for t in terms: postings[t].append(i)
json.dump(shard,open(f'{OUT}p/{cur}.json','w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
def skey(t):
    c=t[0]
    if c=='~': return 'd'
    cls={'#':'h','@':'m'}.get(c)
    if cls: t=t[1:]
    else: cls='w'
    k=''.join(ch if ch in B36 else '_' for ch in t[:2])
    if cls!='w': k=k[:1]
    return cls+k
sh=collections.defaultdict(dict)
for t,pl in postings.items():
    prev=-1; enc=[]
    for x in pl: enc.append(b36(x-prev-1)); prev=x
    sh[skey(t)][t]='.'.join(enc)
for k,v in sh.items():
    json.dump(v,open(f'{OUT}t/{k}.json','w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
# meta: ids delta base36, ts delta
dts=[ts[0]]+[ts[i]-ts[i-1] for i in range(1,len(ts))]
meta={'n':len(posts),'built':'2026-10-21','months':months,'ids':idl,'ts':dts,'fl':fl,'shards':sorted(sh.keys())}
json.dump(meta,open(OUT+'meta.json','w'),separators=(',',':'))
facets={k:[[a,b] for a,b in v.most_common() if b>=2][:3000] for k,v in fac.items()}
facets['counts']={k:len(v) for k,v in fac.items()}
json.dump(facets,open(OUT+'facets.json','w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
# downloads per year
DROP=('local_file','local_status')
cols=['id','created_at','tweet_url','type','is_reply','is_retweet','is_quote','is_self_thread','q_tier','in_reply_to_screen_name','in_reply_to_user_id','in_reply_to_status_id','in_reply_to_url','retweet_of_screen_name','quoted_tweet_url','full_text','full_text_expanded','text_source','urls','media_types','media_urls','video_urls','media_expanded_urls','hashtags','user_mentions','favorite_count','retweet_count','lang']
byy=collections.defaultdict(list)
for p in posts: byy[p['created_at'][:4]].append(p)
dl=[]
for y,ps in sorted(byy.items()):
    with gzip.open(f'{OUT}dl/posts-{y}.jsonl.gz','wt',encoding='utf-8',compresslevel=9) as g:
        for p in ps:
            o={k:v for k,v in p.items() if k!='source_file'}
            o['media']=[{k:v for k,v in m.items() if k not in DROP} for m in p['media']]
            o['q_tier']={1:'strong',2:'broad'}.get(qt.get(p['id']),None)
            g.write(json.dumps(o,ensure_ascii=False)+'\n')
    with gzip.open(f'{OUT}dl/posts-{y}.csv.gz','wt',encoding='utf-8',newline='',compresslevel=9) as g:
        w=csv.writer(g); w.writerow(cols)
        for p in ps:
            o=dict(p); o['q_tier']={1:'strong',2:'broad'}.get(qt.get(p['id']),'')
            J=lambda L:' | '.join(L)
            o['media_types']=J(m['type'] for m in p['media']); o['media_urls']=J(m['media_url_https'] for m in p['media'])
            o['video_urls']=J(m['video_url'] or '' for m in p['media']) if any(m['video_url'] for m in p['media']) else ''
            o['media_expanded_urls']=J(m['expanded_url'] or '' for m in p['media'])
            for k in ('urls','hashtags','user_mentions'): o[k]=J(p[k])
            w.writerow(['' if o.get(c) is None else o.get(c) for c in cols])
    dl.append([y,len(ps),os.path.getsize(f'{OUT}dl/posts-{y}.jsonl.gz'),os.path.getsize(f'{OUT}dl/posts-{y}.csv.gz')])
json.dump(dl,open(OUT+'dl/files.json','w'))
print('posts',len(posts),'months',len(months),'termshards',len(sh),'terms',len(postings)); print(dl)
