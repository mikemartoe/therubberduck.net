/* The Rubber Duck X archive: static search over sharded JSON in /x/data/ */
'use strict';
const D = '/x/data/';
const ME = 'TheRubberDuck79';
const cache = {};
function getJSON(u){ return cache[u] || (cache[u] = fetch(u).then(r => { if(!r.ok) throw new Error(u + ' ' + r.status); return r.json(); })); }
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmtN = n => n.toLocaleString('en-US');

/* ---------- meta ---------- */
let META = null;
async function meta(){
  if(META) return META;
  const m = await getJSON(D + 'meta.json');
  const n = m.n, ts = new Float64Array(n), fl = new Int32Array(m.fl);
  let t = 0; for(let i = 0; i < n; i++){ t += m.ts[i]; ts[i] = t; }
  const byId = new Map(); m.ids.forEach((id, i) => byId.set(id, i));
  const mStart = m.months.map(x => x[1]);
  META = {n, ids: m.ids, ts, fl, byId, months: m.months.map(x => x[0]), mStart, shards: new Set(m.shards)};
  return META;
}
function monthOf(i){ const s = META.mStart; let lo = 0, hi = s.length - 1; while(lo < hi){ const mid = (lo + hi + 1) >> 1; if(s[mid] <= i) lo = mid; else hi = mid - 1; } return lo; }
async function postAt(i){ const mi = monthOf(i); const arr = await getJSON(D + 'p/' + META.months[mi] + '.json'); return arr[i - META.mStart[mi]]; }

/* ---------- tokenising (mirrors the Python build) ---------- */
const norm = s => s.toLowerCase().normalize('NFKD').replace(/\p{M}/gu, '');
const words = s => norm(s).match(/[\p{L}\p{N}_]+/gu) || [];
const B36 = '0123456789abcdefghijklmnopqrstuvwxyz';
function shardKey(t){
  const c = t[0]; if(c === '~') return 'd';
  let cls = 'w'; if(c === '#'){ cls = 'h'; t = t.slice(1); } else if(c === '@'){ cls = 'm'; t = t.slice(1); }
  let k = ''; for(const ch of t.slice(0, 2)) k += B36.includes(ch) ? ch : '_';
  if(cls !== 'w') k = k.slice(0, 1);
  return cls + k;
}
function decode(s){ const p = s.split('.'), out = new Int32Array(p.length); let prev = -1; for(let i = 0; i < p.length; i++){ prev += parseInt(p[i], 36) + 1; out[i] = prev; } return out; }
async function shard(k){ if(!META.shards.has(k)) return {}; return getJSON(D + 't/' + k + '.json'); }
async function postings(term, prefix){
  const sh = await shard(shardKey(term));
  if(!prefix){ const s = sh[term]; return s ? decode(s) : new Int32Array(0); }
  const set = new Set(); for(const k in sh) if(k.startsWith(term)) for(const x of decode(sh[k])) set.add(x);
  return Int32Array.from([...set].sort((a, b) => a - b));
}
function inter(a, b){ const o = []; let i = 0, j = 0; while(i < a.length && j < b.length){ if(a[i] < b[j]) i++; else if(a[i] > b[j]) j++; else { o.push(a[i]); i++; j++; } } return Int32Array.from(o); }
function minus(a, b){ const s = new Set(b); return a.filter(x => !s.has(x)); }

/* query: words AND, "exact phrase", -exclude, word* prefix, #tag, @user */
function parseQuery(q){
  const out = {terms: [], phrases: [], not: []};
  const re = /(-?)"([^"]*)"|(\S+)/g; let m;
  while((m = re.exec(q))){
    const neg = m[1] === '-' || (m[3] && m[3][0] === '-' && m[3].length > 1);
    let raw = m[2] !== undefined ? m[2] : (m[3][0] === '-' ? m[3].slice(1) : m[3]);
    const quoted = m[2] !== undefined;
    if(!quoted && /^[#@][\p{L}\p{N}_]+$/u.test(raw)){ (neg ? out.not : out.terms).push({t: raw[0] + norm(raw.slice(1)), p: false}); continue; }
    const pre = !quoted && raw.endsWith('*'); if(pre) raw = raw.slice(0, -1);
    const w = words(raw); if(!w.length) continue;
    if(neg){ if(w.length === 1) out.not.push({t: w[0], p: pre}); else out.notPhrase = (out.notPhrase || []).concat([w]); continue; }
    w.forEach((x, i) => out.terms.push({t: x, p: pre && i === w.length - 1 && x.length >= 2}));
    if(w.length > 1) out.phrases.push(w);
  }
  return out;
}
const flat = t => ' ' + words(t).join(' ') + ' ';

/* ---------- search ---------- */
const TYPES = {all: null, original: f => (f & 3) === 0, reply: f => (f & 3) === 1, retweet: f => (f & 3) === 2, quote: f => (f & 4) !== 0, thread: f => (f & 8) !== 0};
const MEDIA = {any: null, media: f => (f & 112) !== 0, photo: f => (f & 16) !== 0, video: f => (f & 32) !== 0, gif: f => (f & 64) !== 0, none: f => (f & 112) === 0, links: f => (f & 512) !== 0};
const QF = {all: null, q: f => (f & 384) !== 0, strong: f => (f & 128) !== 0, broad: f => (f & 256) !== 0, not: f => (f & 384) === 0};
function dayTs(s, end){ if(!s) return null; const t = Date.parse(s + 'T00:00:00Z') / 1000; return isNaN(t) ? null : t + (end ? 86400 : 0); }

async function search(st, progress){
  await meta();
  const pq = parseQuery(st.q || '');
  const must = pq.terms.slice();
  if(st.h) must.push({t: '#' + norm(st.h.replace(/^#/, '').trim()), p: false});
  if(st.m) must.push({t: '@' + norm(st.m.replace(/^@/, '').trim()), p: false});
  if(st.d) must.push({t: '~' + st.d.trim().toLowerCase().replace(/^https?:\/\//, '').replace(/^www\./, '').replace(/\/.*$/, ''), p: false});
  let cand = null;
  if(must.length){
    const lists = await Promise.all(must.map(x => postings(x.t, x.p)));
    lists.sort((a, b) => a.length - b.length);
    cand = lists[0]; for(let i = 1; i < lists.length && cand.length; i++) cand = inter(cand, lists[i]);
  }
  if(pq.not.length){ const lists = await Promise.all(pq.not.map(x => postings(x.t, x.p))); if(!cand) cand = Int32Array.from({length: META.n}, (_, i) => i); for(const l of lists) cand = minus(cand, l); }
  let from = dayTs(st.from, false), to = dayTs(st.to, true);
  if(st.y){ const yf = Date.UTC(+st.y, 0, 1) / 1000, yt = Date.UTC(+st.y + 1, 0, 1) / 1000; from = from == null ? yf : Math.max(from, yf); to = to == null ? yt : Math.min(to, yt); }
  const ft = TYPES[st.type || 'all'], fm = MEDIA[st.media || 'any'], fq = QF[st.qr || 'all'];
  const res = [], ts = META.ts, fl = META.fl;
  const test = i => !((from != null && ts[i] < from) || (to != null && ts[i] >= to) || (ft && !ft(fl[i])) || (fm && !fm(fl[i])) || (fq && !fq(fl[i])));
  if(cand){ for(const i of cand) if(test(i)) res.push(i); }
  else for(let i = 0; i < META.n; i++) if(test(i)) res.push(i);
  let out = res;
  if(pq.phrases.length || pq.notPhrase){
    const months = [...new Set(res.map(monthOf))];
    let done = 0;
    await Promise.all(months.map(mi => getJSON(D + 'p/' + META.months[mi] + '.json').then(() => progress && progress(++done, months.length))));
    const ph = pq.phrases.map(w => ' ' + w.join(' ') + ' '), nph = (pq.notPhrase || []).map(w => ' ' + w.join(' ') + ' ');
    out = [];
    for(const i of res){ const p = await postAt(i); const f = flat(p.x); if(ph.every(x => f.includes(x)) && !nph.some(x => f.includes(x))) out.push(i); }
  }
  if(st.sort === 'old') return out;
  return out.reverse();
}

/* ---------- rendering ---------- */
const purl = id => '/x/post.html?id=' + id;
const xurl = p => p.tu || ('https://x.com/' + ME + '/status/' + p.i);
const KIND = {o: 'Post', r: 'Reply', t: 'Repost'};
function fmtDate(c){ return c.replace('T', ' ').replace('Z', ' UTC'); }
function linkText(text){
  const parts = text.split(/(https?:\/\/[^\s]+)/g); let h = '';
  parts.forEach((s, i) => {
    if(i % 2){ const m = s.match(/^(.*?)([.,;:!?)\]"'\u2026]*)$/s); const u = m[1], tail = m[2]; h += '<a href="' + esc(u) + '" rel="noopener nofollow" target="_blank">' + esc(u) + '</a>' + esc(tail); }
    else h += esc(s).replace(/(^|[^\w&])@(\w{1,15})/g, '$1<a href="https://x.com/$2" rel="noopener nofollow" target="_blank">@$2</a>')
                     .replace(/(^|[^\w&\/])#([\p{L}\p{N}_]+)/gu, '$1<a href="/x/?h=$2">#$2</a>');
  });
  return h;
}
const ownId = u => { const m = /^https?:\/\/(?:mobile\.)?(?:x|twitter)\.com\/therubberduck79\/status\/(\d+)/i.exec(u || ''); return m ? m[1] : null; };
function ctxLinks(p){
  const c = [];
  if(p.y === 'r' || p.ri || p.rn){
    const ru = p.ru || (p.ri ? 'https://x.com/' + p.rn + '/status/' + p.ri : null);
    let s = 'Replying to <a href="https://x.com/' + esc(p.rn || '') + '" target="_blank" rel="noopener">@' + esc(p.rn || 'unknown') + '</a>';
    if(ru) s += ' | <a href="' + esc(ru) + '" target="_blank" rel="noopener">parent post on X</a>';
    if(p.ri && p.rn && p.rn.toLowerCase() === ME.toLowerCase()) s += ' | <a href="' + purl(p.ri) + '">parent in archive</a>';
    if(!p.ri) s += ' (parent post id not in the data)';
    c.push(s);
  }
  if(p.rt) c.push('Repost of <a href="https://x.com/' + esc(p.rt) + '" target="_blank" rel="noopener">@' + esc(p.rt) + '</a>');
  if(p.qu){ const o = ownId(p.qu); c.push('Quoting <a href="' + esc(p.qu) + '" target="_blank" rel="noopener">' + esc(p.qu) + '</a>' + (o ? ' | <a href="' + purl(o) + '">quoted post in archive</a>' : '')); }
  if(p.st) c.push('Part of a self-thread');
  if(p.k) c.push(p.k.length + ' repl' + (p.k.length > 1 ? 'ies' : 'y') + ' in archive: ' + p.k.map(k => '<a href="' + purl(k) + '">' + k + '</a>').join(', '));
  return c.map(s => '<p class="ctx">' + s + '</p>').join('');
}
function mediaHtml(p){
  if(!p.m) return '';
  const xu = esc(xurl(p));
  const items = p.m.map(([t, u, v]) => {
    const thumb = esc(u + (u.includes('?') ? '' : '?name=small'));
    if(t === 'p') return '<a class="mi" href="' + esc(u + '?name=orig') + '" target="_blank" rel="noopener" data-x="' + xu + '"><img loading="lazy" src="' + thumb + '" alt="photo"></a>';
    const lab = t === 'g' ? 'GIF' : 'Video';
    return '<div class="mi" data-x="' + xu + '"><img loading="lazy" src="' + thumb + '" alt="' + lab + ' thumbnail">' +
      (v ? '<button class="play" type="button" data-v="' + esc(v) + '" data-g="' + (t === 'g' ? 1 : '') + '" aria-label="Play ' + lab + '"></button>'
         : '<a class="play" href="' + xu + '" target="_blank" rel="noopener" aria-label="Play on X"></a>') +
      '<span class="mt">' + lab + '</span></div>';
  }).join('');
  return '<div class="med' + (p.m.length === 1 ? ' one' : '') + '">' + items + '</div>';
}
function postHtml(p, opts = {}){
  const kind = p.qt && p.y !== 't' ? (p.y === 'r' ? 'Reply + Quote' : 'Quote') : KIND[p.y];
  let h = '<article class="post' + (opts.hi ? ' hi' : '') + '" id="p' + p.i + '">';
  h += '<div class="ph"><span class="kind">' + kind + '</span><span class="nm">The Rubber Duck</span><span>@' + ME + '</span><time datetime="' + p.c + '">' + fmtDate(p.c) + '</time>' +
       '<span class="no"><a href="' + purl(p.i) + '">No.' + p.i + '</a> | <a href="' + esc(xurl(p)) + '" target="_blank" rel="noopener">View on X</a></span></div>';
  h += ctxLinks(p);
  h += '<div class="tx">' + linkText(p.x) + '</div>';
  h += mediaHtml(p);
  if(opts.full){
    const L = (p.u || []).map(u => '<li><a href="' + esc(u) + '" target="_blank" rel="noopener nofollow">' + esc(u) + '</a></li>');
    (p.m || []).forEach(m => { L.push('<li>' + (m[0] === 'p' ? 'photo' : m[0] === 'g' ? 'gif' : 'video') + ': <a href="' + esc(m[1]) + '" target="_blank" rel="noopener">' + esc(m[1]) + '</a>' + (m[2] ? ' | file: <a href="' + esc(m[2]) + '" target="_blank" rel="noopener">' + esc(m[2]) + '</a>' : '') + '</li>'); });
    if(L.length) h += '<ul class="links">' + L.join('') + '</ul>';
  }
  h += '<div class="pf"><span>' + fmtN(p.f || 0) + ' likes</span><span>' + fmtN(p.r || 0) + ' reposts</span>' + (p.l ? '<span>lang: ' + esc(p.l) + '</span>' : '') +
       (p.s ? '<span>long post</span>' : '') + (p.q === 1 ? '<span class="tag">Q-related</span>' : p.q === 2 ? '<span class="tag b">Q-related (broad)</span>' : '') + '</div>';
  return h + '</article>';
}
/* media fallbacks: never a broken icon */
function failBox(el){
  const box = el.closest('.mi'); if(!box || box.dataset.failed) return; box.dataset.failed = 1;
  const a = document.createElement('a'); a.className = 'mfail'; a.href = box.dataset.x; a.target = '_blank'; a.rel = 'noopener'; a.textContent = 'Media on X';
  box.replaceWith(a);
}
document.addEventListener('error', e => { const t = e.target; if(t && t.tagName === 'IMG' && t.closest && t.closest('.mi')) failBox(t); }, true);
document.addEventListener('click', e => {
  const b = e.target.closest && e.target.closest('button.play'); if(!b) return;
  const box = b.closest('.mi'), img = box.querySelector('img'), keep = box.innerHTML;
  const v = document.createElement('video'); v.controls = true; v.autoplay = true; v.playsInline = true; if(b.dataset.g){ v.loop = true; v.muted = true; }
  if(img) v.poster = img.src; v.src = b.dataset.v;
  /* if the video file will not play here, go back to the thumbnail with a play badge that opens the post on X */
  v.addEventListener('error', () => {
    box.innerHTML = keep;
    const old = box.querySelector('button.play'), a = document.createElement('a');
    a.className = 'play'; a.href = box.dataset.x; a.target = '_blank'; a.rel = 'noopener'; a.setAttribute('aria-label', 'Play on X'); a.title = 'Play on X';
    old.replaceWith(a);
  });
  box.innerHTML = ''; box.appendChild(v);
});
