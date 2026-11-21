const R2_PDF = 'https://memes.therubberduck.net/eo-library/pdfs/eo-';
/* President Donald J. Trump Executive Order Library — search, shelves, open binder. */
import * as pdfjsLib from '/eo-library/vendor/pdfjs/pdf.min.mjs';
pdfjsLib.GlobalWorkerOptions.workerSrc = '/eo-library/vendor/pdfjs/pdf.worker.min.mjs';

const YELLOW_PROMPTS = [
  'Search the Executive Orders',
  '13818',
  'Magnitsky',
  'January 20, 2025',
  'cartels',
  'what about election interference?',
  'JFK records',
  'Schedule F',
  'border wall',
  'who signed the energy emergency?',
  '14438',
  'human trafficking',
  'tariffs',
  'October 22, 2026',
  'TikTok',
  'why were the JFK files released?',
  'sanctuary cities',
  'Iran',
  'birthright',
  'has a Q connection'
];

const SYN = {
  magnitsky: ['magnitsky', 'human rights abuse', 'global magnitsky'],
  hillary: ['hillary', 'hrc', 'clinton'],
  obamacare: ['obamacare', 'affordable care', 'aca', 'patient protection'],
  cartels: ['cartel', 'cartels', 'foreign terrorist organization', 'fto', 'ms-13', 'ms13'],
  jfk: ['jfk', 'john f kennedy', 'john f. kennedy', 'kennedy assassination', 'jfk records'],
  tiktok: ['tiktok', 'bytedance', 'musical.ly'],
  election: ['election interference', 'foreign interference', 'election integrity'],
  wall: ['border wall', 'build the wall', 'southern border'],
  sanctuary: ['sanctuary', 'sanctuary cities', 'sanctuary jurisdictions'],
  trafficking: ['human trafficking', 'sex trafficking', 'traffick'],
  china: ['china', 'chinese', 'ccp', "people's republic"],
  iran: ['iran', 'iranian', 'jcpoa']
};

const STOP = new Set('the a an of and to in is on for at by as or if be it its this that those these with from into upon over under within without than then also such any all each every other another both not no nor but so shall may must will would can could should have has had having been being was were are am do does did doing who what when where why how which whom whose did does was were is are i we you they whats'.split(' '));
const QSTART = /^(who|what|when|where|why|how|which|did|does|do|is|are|was|were|can|could|should|would|will)\b/i;

const TAG_LABEL = {
  cartels:'Cartels', immigration:'Immigration', election:'Elections', sanctions:'Sanctions',
  china:'China', iran:'Iran', israel:'Israel', energy:'Energy', trade:'Trade',
  healthcare:'Healthcare', military:'Military', intelligence:'Intelligence',
  'civil-service':'Civil service', trafficking:'Trafficking', justice:'Justice',
  education:'Education', environment:'Environment', economy:'Economy', covid:'COVID',
  records:'Records', 'human-rights':'Human rights', terrorism:'Terrorism',
  'foreign-policy':'Foreign policy', housing:'Housing', tech:'Technology',
  crime:'Crime', regulatory:'Regulation', emergency:'Emergency'
};

const $ = (id) => document.getElementById(id);
const EOS = Array.isArray(window.TRD_EOS) ? window.TRD_EOS : [];
const META = window.TRD_EO_META || {};
const BYN = new Map(EOS.map((r) => [r.n, r]));
let TEXTS = null;
let textsLoading = null;
let state = { q:'', term:'', year:'', status:'', tag:'', from:'', to:'', num:'', hasQ:false };
let pdfDoc = null, pdfPage = 1, openN = null;

function esc(s){ return String(s||'').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function fold(s){
  s = String(s||'').toLowerCase();
  if (s.normalize) s = s.normalize('NFD').replace(/[\u0300-\u036f]/g,'');
  return s.replace(/[\u2018\u2019]/g,"'").replace(/[\u2013\u2014]/g,'-');
}
function toks(s){ return fold(s).replace(/'/g,'').match(/[a-z0-9]+/g) || []; }
function fmtNum(n){ return Number(n).toLocaleString('en-US'); }

function cleanQuestion(q){
  let s = String(q||'').trim();
  s = s.replace(/\?+\s*$/,'');
  const words = toks(s);
  const kept = words.filter((w,i) => {
    if (STOP.has(w) && words.length>1) return false;
    if (i===0 && QSTART.test(w) && words.length>1) return false;
    return true;
  });
  return kept;
}

function alts(w){
  const a = new Set([w]);
  Object.values(SYN).forEach((list) => {
    if (list.some((x) => fold(x)===w || toks(x).includes(w))) list.forEach((x) => toks(x).forEach((t)=>a.add(t)));
  });
  return [...a];
}

function dist(a,b){
  if (a===b) return 0;
  if (Math.abs(a.length-b.length)>1) return 2;
  // levenshtein capped at 2
  const m=[];
  for(let i=0;i<=a.length;i++){ m[i]=[i]; }
  for(let j=0;j<=b.length;j++) m[0][j]=j;
  for(let i=1;i<=a.length;i++){
    for(let j=1;j<=b.length;j++){
      const c=a[i-1]===b[j-1]?0:1;
      m[i][j]=Math.min(m[i-1][j]+1,m[i][j-1]+1,m[i-1][j-1]+c);
    }
  }
  return m[a.length][b.length];
}

function hayFor(r){
  const extra = TEXTS && TEXTS[r.n] ? TEXTS[r.n] : (TEXTS && TEXTS[String(r.n)] ? TEXTS[String(r.n)] : '');
  return fold([r.n, r.title, r.summary, r.dateLabel, r.citation, r.statusNote, (r.tags||[]).join(' '), extra].join(' '));
}

function highlight(htmlSafeText, terms){
  // htmlSafeText is already escaped
  if (!terms || !terms.length) return htmlSafeText;
  const rx = new RegExp('('+terms.map((t)=>t.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')).filter((t)=>t.length>1).join('|')+')','ig');
  if (rx.source === '()') return htmlSafeText;
  return htmlSafeText.replace(rx, '<mark>$1</mark>');
}

function loadTexts(){
  if (TEXTS || textsLoading) return textsLoading || Promise.resolve(TEXTS);
  textsLoading = new Promise((resolve) => {
    const s = document.createElement('script');
    s.src = '/eo-library/data/eo-texts.js';
    s.onload = () => { TEXTS = window.TRD_EO_TEXTS || {}; resolve(TEXTS); };
    s.onerror = () => { TEXTS = {}; resolve(TEXTS); };
    document.head.appendChild(s);
  });
  return textsLoading;
}

function applyFilters(rows){
  return rows.filter((r) => {
    if (state.term && String(r.term) !== state.term) return false;
    if (state.year && String(r.year) !== state.year) return false;
    if (state.status && r.status !== state.status) return false;
    if (state.tag && !(r.tags||[]).includes(state.tag)) return false;
    if (state.hasQ && !(r.q && r.q.length)) return false;
    if (state.from && r.date < state.from) return false;
    if (state.to && r.date > state.to) return false;
    if (state.num) {
      const n = state.num.replace(/\D/g,'');
      if (n && !String(r.n).includes(n) && String(r.n)!==n) return false;
    }
    return true;
  });
}

function search(raw){
  const typed = String(raw||'').trim();
  let pool = applyFilters(EOS);
  const info = { rows: pool, label:'', note:'', hl:[], kind:'all' };
  if (!typed) {
    info.label = pool.length===EOS.length ? (fmtNum(pool.length)+' executive orders') : (fmtNum(pool.length)+' orders in the current filters');
    return info;
  }
  // EO number only
  if (/^#?\d{4,5}$/.test(typed)) {
    const n = +typed.replace('#','');
    const hit = pool.filter((r)=>r.n===n);
    if (hit.length){ info.rows=hit; info.kind='number'; info.label='Executive Order '+fmtNum(n); info.hl=[String(n)]; return info; }
  }
  const words = (looksQ(typed) ? cleanQuestion(typed) : toks(typed)).filter(Boolean);
  if (!words.length){ info.label='No searchable terms in that question.'; info.rows=[]; return info; }
  info.hl = words.slice();
  const phrase = fold(typed).replace(/\?+/g,'').trim();
  if (phrase.length>=6 && phrase.indexOf(' ')>=0){
    const ph = pool.filter((r)=>hayFor(r).indexOf(phrase)>=0);
    if (ph.length){
      info.rows = rank(ph, words);
      info.kind = 'phrase';
      info.label = fmtNum(ph.length)+' order'+(ph.length===1?'':'s')+' containing “'+typed.replace(/\?+$/,'')+'”';
      return info;
    }
  }
  const groups = words.map(alts);
  function andMatch(r){
    const h = hayFor(r);
    const ht = toks(h);
    return groups.every((g) => g.some((w) => {
      if (h.indexOf(w)>=0) return true;
      if (w.length>=5) return ht.some((t)=>t.length>=5 && dist(t,w)===1);
      return false;
    }));
  }
  let and = pool.filter(andMatch);
  if (and.length){
    info.rows = rank(and, words);
    info.kind = 'and';
    info.label = fmtNum(and.length)+' order'+(and.length===1?'':'s')+' matching “'+typed+'”';
    return info;
  }
  // OR fallback
  function orScore(r){
    const h = hayFor(r);
    let n=0; groups.forEach((g)=>{ if(g.some((w)=>h.indexOf(w)>=0)) n++; });
    return n;
  }
  const or = pool.map((r)=>({r,s:orScore(r)})).filter((x)=>x.s>0).sort((a,b)=>b.s-a.s || b.r.date.localeCompare(a.r.date) || b.r.n-a.r.n).map((x)=>x.r);
  info.rows = or;
  info.kind = 'or';
  info.note = 'No order uses every term, so these are ranked by how many terms they match.';
  info.label = or.length ? (fmtNum(or.length)+' order'+(or.length===1?'':'s')+' matching any of those terms') : ('No executive order uses “'+typed+'”.');
  return info;
}

function looksQ(q){ return /\?\s*$/.test(q) || QSTART.test(q); }
function rank(rows, words){
  return rows.slice().sort((a,b)=>{
    const sa = score(a,words), sb=score(b,words);
    return sb-sa || b.date.localeCompare(a.date) || b.n-a.n;
  });
}
function score(r, words){
  const title = fold(r.title+' '+r.n);
  let s=0;
  words.forEach((w)=>{
    if (String(r.n).includes(w)) s+=50;
    if (title.indexOf(w)>=0) s+=12;
    if (fold(r.summary).indexOf(w)>=0) s+=4;
  });
  if (r.q && r.q.length) s+=2;
  return s;
}

function setStats(){
  const m = META;
  const el = $('eolStats'); if(!el) return;
  el.querySelector('[data-stat="count"]').textContent = fmtNum(m.count || EOS.length);
  el.querySelector('[data-stat="first"]').textContent = fmtNum(m.firstTerm || EOS.filter(r=>r.term===1).length);
  el.querySelector('[data-stat="second"]').textContent = fmtNum(m.secondTerm || EOS.filter(r=>r.term===2).length);
  el.querySelector('[data-stat="q"]').textContent = fmtNum(m.withQ || EOS.filter(r=>r.q&&r.q.length).length);
}

function chipYears(){
  const years = [...new Set(EOS.map((r)=>r.year))].sort((a,b)=>b-a);
  const host = $('eolYears');
  host.innerHTML = '<button type="button" class="is-on" data-val="">All</button>' + years.map((y)=>'<button type="button" data-val="'+y+'">'+y+'</button>').join('');
  const tags = {};
  EOS.forEach((r)=>(r.tags||[]).forEach((t)=>{ tags[t]=(tags[t]||0)+1; }));
  const order = Object.keys(tags).sort((a,b)=>tags[b]-tags[a]);
  $('eolTags').innerHTML = '<button type="button" class="is-on" data-val="">All</button>' + order.map((t)=>'<button type="button" data-val="'+esc(t)+'">'+esc(TAG_LABEL[t]||t)+'</button>').join('');
}

function binderCard(r, hl){
  const badges = [];
  if (r.q && r.q.length) badges.push('<span class="binder-badge q">Q</span>');
  if (r.status==='revoked') badges.push('<span class="binder-badge">Revoked</span>');
  else if (r.status==='amended') badges.push('<span class="binder-badge">Amended</span>');
  else if (r.status==='superseded') badges.push('<span class="binder-badge">Superseded</span>');
  return '<button type="button" class="binder" id="eo-'+r.n+'" data-eo="'+r.n+'" aria-label="Open Executive Order '+r.n+', '+esc(r.title)+'">'+
    '<span class="binder-cover">'+
      '<span class="binder-badges">'+badges.join('')+'</span>'+
      '<img class="binder-seal" src="/eo-library/img/presidential-seal.svg" width="58" height="58" alt="">'+
      '<span class="binder-k">Executive Order</span>'+
      '<span class="binder-num">'+highlight(esc(String(r.n)), hl)+'</span>'+
      '<span class="binder-title">'+highlight(esc(r.title), hl)+'</span>'+
      '<span class="binder-date">'+esc(r.dateLabel)+'</span>'+
      '<span class="binder-sign">Donald J. Trump</span>'+
    '</span></button>';
}

function render(){
  const info = search(state.q);
  const rows = info.rows;
  const count = $('eolCount');
  count.innerHTML = esc(info.label) + (info.note ? ' <span>'+esc(info.note)+'</span>' : '');
  const host = $('eolShelves');
  const empty = $('eolEmpty');
  if (!rows.length){
    host.innerHTML='';
    empty.hidden=false;
    return;
  }
  empty.hidden=true;
  // group by term+year, newest first (rows already date-sorted from EOS except search ranks)
  const groups = [];
  const map = new Map();
  rows.forEach((r)=>{
    const key = r.term+'-'+r.year;
    if (!map.has(key)){
      const g = { term:r.term, year:r.year, rows:[] };
      map.set(key,g); groups.push(g);
    }
    map.get(key).rows.push(r);
  });
  groups.sort((a,b)=> b.year-a.year || b.term-a.term);
  host.innerHTML = groups.map((g)=>{
    const label = (g.term===2?'Second term':'First term')+' · '+g.year;
    return '<section class="eol-shelf" data-year="'+g.year+'">'+
      '<div class="eol-year"><h2>'+label+'</h2><p>'+g.rows.length+' order'+(g.rows.length===1?'':'s')+'</p><span class="eol-year-rule"></span></div>'+
      '<div class="eol-grid">'+g.rows.map((r)=>binderCard(r, info.hl)).join('')+'</div></section>';
  }).join('');
}

function syncUrl(){
  const u = new URL(location.href);
  const p = u.searchParams;
  if (state.q) p.set('q', state.q); else p.delete('q');
  ['term','year','status','tag','from','to'].forEach((k)=>{
    if (state[k]) p.set(k, state[k]); else p.delete(k);
  });
  if (state.hasQ) p.set('qconn','1'); else p.delete('qconn');
  if (state.num) p.set('n', state.num); else p.delete('n');
  const hash = openN ? ('eo-'+openN) : (u.hash||'').replace(/^#/,'');
  history.replaceState(null,'', u.pathname + (p.toString()?('?'+p.toString()):'') + (hash?('#'+hash):''));
}

function readUrl(){
  const u = new URL(location.href);
  const p = u.searchParams;
  state.q = p.get('q')||'';
  state.term = p.get('term')||'';
  state.year = p.get('year')||'';
  state.status = p.get('status')||'';
  state.tag = p.get('tag')||'';
  state.from = p.get('from')||'';
  state.to = p.get('to')||'';
  state.num = p.get('n')||'';
  state.hasQ = p.get('qconn')==='1';
  $('eolQ').value = state.q;
  $('eolFrom').value = state.from;
  $('eolTo').value = state.to;
  $('eolNum').value = state.num;
  $('eolHasQ').checked = state.hasQ;
  $('eolClear').hidden = !state.q;
  document.querySelectorAll('[data-filter]').forEach((group)=>{
    const key = group.getAttribute('data-filter');
    group.querySelectorAll('button').forEach((b)=>{
      b.classList.toggle('is-on', (b.getAttribute('data-val')||'') === String(state[key]||''));
    });
  });
}

function wireFilters(){
  document.querySelectorAll('[data-filter]').forEach((group)=>{
    group.addEventListener('click', (e)=>{
      const b = e.target.closest('button'); if(!b) return;
      const key = group.getAttribute('data-filter');
      state[key] = b.getAttribute('data-val')||'';
      group.querySelectorAll('button').forEach((x)=>x.classList.toggle('is-on', x===b));
      render(); syncUrl();
    });
  });
  ['eolFrom','eolTo','eolNum'].forEach((id)=>{
    $(id).addEventListener('input', ()=>{
      state.from = $('eolFrom').value;
      state.to = $('eolTo').value;
      state.num = $('eolNum').value.trim();
      render(); syncUrl();
    });
  });
  $('eolHasQ').addEventListener('change', ()=>{ state.hasQ=$('eolHasQ').checked; render(); syncUrl(); });
  const q = $('eolQ');
  q.addEventListener('input', ()=>{
    state.q = q.value;
    $('eolClear').hidden = !q.value;
    if (q.value.length>=2) loadTexts().then(render);
    else render();
    syncUrl();
  });
  q.addEventListener('keydown', (e)=>{ if(e.key==='Enter'){ e.preventDefault(); loadTexts().then(render);} });
  $('eolClear').addEventListener('click', ()=>{ q.value=''; state.q=''; $('eolClear').hidden=true; render(); syncUrl(); q.focus(); });
  $('eolShelves').addEventListener('click', (e)=>{
    const b = e.target.closest('[data-eo]'); if(!b) return;
    openBinder(+b.getAttribute('data-eo'));
  });
}

async function openBinder(n){
  const r = BYN.get(n); if(!r) return;
  openN = n;
  const stage = $('eolStage');
  stage.hidden = false;
  document.body.style.overflow='hidden';
  $('folioNum').textContent = 'Executive Order '+r.n;
  $('folioTitle').textContent = r.title;
  $('folioKicker').textContent = (r.term===2?'Second term':'First term')+' · Signed by President Donald J. Trump';
  $('folioDate').textContent = r.dateLabel;
  $('folioCite').textContent = [r.citation, r.docNumber?('Document '+r.docNumber):''].filter(Boolean).join(' · ');
  $('folioStatus').textContent = r.statusNote ? ((r.status==='revoked'?'Revoked. ':r.status==='amended'?'Amended. ':r.status==='superseded'?'Superseded. ':'')+r.statusNote) : (r.status==='active'?'In force.':'');
  $('folioSum').innerHTML = highlight(esc(r.summary), toks(state.q));
  const links = [];
  links.push('<a href="'+R2_PDF+r.n+'.pdf" target="_blank" rel="noopener">Signed Federal Register PDF</a>');
  if (r.frUrl) links.push('<a href="'+esc(r.frUrl)+'" target="_blank" rel="noopener">Federal Register page</a>');
  if (r.pdfUrl) links.push('<a href="'+esc(r.pdfUrl)+'" target="_blank" rel="noopener">govinfo.gov official file</a>');
  $('folioLinks').innerHTML = links.join('');
  const qhost = $('folioQList');
  if (r.q && r.q.length){
    $('folioQ').hidden = false;
    qhost.innerHTML = r.q.map((q)=>
      '<article class="q-card">'+
        '<a href="/drops/'+q.n+'/">Q drop '+q.n+'</a>'+
        (q.why ? '<p class="q-why">'+esc(q.why)+'</p>' : '')+
        '<blockquote>'+esc(q.quote)+'</blockquote>'+
      '</article>'
    ).join('');
  } else {
    $('folioQ').hidden = true;
    qhost.innerHTML = '';
  }
  syncUrl();
  await showDocument(r);
  history.replaceState(null,'', location.pathname+location.search+'#eo-'+n);
}

function closeBinder(){
  openN = null;
  $('eolStage').hidden = true;
  document.body.style.overflow='';
  if (pdfDoc){ try{ pdfDoc.destroy(); }catch(e){} pdfDoc=null; }
  const u = new URL(location.href); u.hash='';
  history.replaceState(null,'', u.pathname+u.search);
}

async function findSignaturePage(){
  if (!pdfDoc) return 1;
  let named=0;
  for (let i=1;i<=pdfDoc.numPages;i++){
    const page = await pdfDoc.getPage(i);
    const tc = await page.getTextContent();
    const text = tc.items.map((it)=>it.str).join(' ');
    if (/Trump\.EPS/i.test(text) || (/THE WHITE HOUSE/.test(text) && /Billing code|December|January|February|March|April|May|June|July|August|September|October|November/.test(text) && !/I, DONALD J\. TRUMP/.test(text))){
      // Prefer a later page: the preamble also says "I, DONALD J. TRUMP".
      named = i;
    }
  }
  return named || 0;
}

async function showDocument(r){
  const msg = $('folioPdfMsg');
  const textEl = $('folioText');
  const canvas = $('folioCanvas');
  msg.textContent = 'Opening the official document…';
  textEl.hidden = true;
  canvas.hidden = true;
  $('folioPrev').disabled = true;
  $('folioNext').disabled = true;
  $('folioPage').textContent = '';
  if (pdfDoc){ try{ pdfDoc.destroy(); }catch(e){} pdfDoc=null; }

  const r2 = R2_PDF+r.n+'.pdf';
  const local = '/eo-library/pdfs/eo-'+r.n+'.pdf';
  const urls = [r2, local];
  if (r.pdfUrl) urls.push(r.pdfUrl);

  for (const url of urls){
    try{
      const doc = await pdfjsLib.getDocument({ url, withCredentials:false }).promise;
      pdfDoc = doc;
      pdfPage = 1;
      canvas.hidden = false;
      msg.textContent = r.hasPdf ? 'Official Federal Register PDF, including the printed presidential signature.' : '';
      await drawPage();
      const sig = await findSignaturePage();
      if (sig && sig!==pdfPage){ pdfPage=sig; await drawPage(); }
      return;
    }catch(e){ /* try next */ }
  }
  // Fallback: the full text, plus a link to the official signed PDF.
  await loadTexts();
  const raw = (TEXTS && (TEXTS[r.n] || TEXTS[String(r.n)])) || (r.title+'\n\n'+r.summary);
  textEl.hidden = false;
  textEl.textContent = raw;
  const pdfLink = r.pdfUrl || (R2_PDF+r.n+'.pdf');
  msg.innerHTML = r.hasPdf
    ? 'The official signed Federal Register PDF could not be drawn in this window. <a href="'+esc(pdfLink)+'" target="_blank" rel="noopener">Open the official signed PDF</a>. The full text of the order is below.'
    : 'No Federal Register PDF is on file for this order. The full text is below.';
}

async function drawPage(){
  if (!pdfDoc) return;
  const page = await pdfDoc.getPage(pdfPage);
  const canvas = $('folioCanvas');
  const box = canvas.parentElement.getBoundingClientRect();
  const vw = Math.max(280, Math.min(box.width-8, 820));
  const viewport = page.getViewport({ scale: 1 });
  const scale = vw / viewport.width;
  const vp = page.getViewport({ scale: Math.min(2.2, Math.max(1, scale)) });
  const ctx = canvas.getContext('2d');
  canvas.width = vp.width;
  canvas.height = vp.height;
  canvas.hidden = false;
  await page.render({ canvasContext: ctx, viewport: vp }).promise;
  $('folioPage').textContent = 'Page '+pdfPage+' of '+pdfDoc.numPages;
  $('folioPrev').disabled = pdfPage<=1;
  $('folioNext').disabled = pdfPage>=pdfDoc.numPages;
}

function wireBinder(){
  $('eolStage').addEventListener('click', (e)=>{ if (e.target.hasAttribute('data-close')) closeBinder(); });
  document.addEventListener('keydown', (e)=>{
    if ($('eolStage').hidden) return;
    if (e.key==='Escape') closeBinder();
    if (e.key==='ArrowRight') { pdfPage=Math.min((pdfDoc&&pdfDoc.numPages)||1, pdfPage+1); drawPage(); }
    if (e.key==='ArrowLeft') { pdfPage=Math.max(1, pdfPage-1); drawPage(); }
  });
  $('folioPrev').addEventListener('click', ()=>{ pdfPage=Math.max(1,pdfPage-1); drawPage(); });
  $('folioNext').addEventListener('click', ()=>{ if(pdfDoc){ pdfPage=Math.min(pdfDoc.numPages,pdfPage+1); drawPage(); } });
}

function wireShare(){
  const btn = $('eolShareBtn'); if(!btn) return;
  btn.addEventListener('click', async ()=>{
    const url = location.origin+'/eo-library/';
    const title = 'The Executive Order Library — President Donald J. Trump';
    try{
      if (navigator.share) await navigator.share({ title, url });
      else { await navigator.clipboard.writeText(url); $('eolShareMsg').hidden=false; $('eolShareMsg').textContent='Link copied.'; }
    }catch(e){
      try{ await navigator.clipboard.writeText(url); $('eolShareMsg').hidden=false; $('eolShareMsg').textContent='Link copied.'; }catch(e2){}
    }
  });
}

function bootTicker(){
  const wrap = $('eolSearchWrap');
  const input = $('eolQ');
  if (window.TRDSearchTicker && window.TRDSearchTicker.mount){
    window.TRDSearchTicker.mount({
      input, wrap,
      first: YELLOW_PROMPTS[0],
      prompts: YELLOW_PROMPTS,
      label: 'Search the Executive Orders'
    });
  }
}

function fromHash(){
  const h = (location.hash||'').replace(/^#/,'');
  const m = /^eo-(\d+)$/.exec(h);
  if (m){
    const n=+m[1];
    const el = document.getElementById('eo-'+n);
    if (el) el.scrollIntoView({block:'center'});
    openBinder(n);
  }
}

function quietSiteSearch(){
  var tn = document.getElementById('tn-q');
  var res = document.getElementById('tn-res');
  if (tn){ tn.value=''; tn.blur(); }
  if (res){ res.hidden = true; res.setAttribute('hidden',''); }
  var nav = document.getElementById('trd-nav');
  if (nav) nav.classList.remove('search-open');
  var form = document.getElementById('tn-form');
  if (form) form.classList.remove('open');
}
setStats();
chipYears();
readUrl();
quietSiteSearch();
wireFilters();
wireBinder();
wireShare();
bootTicker();
render();
if (state.q) loadTexts().then(render);
fromHash();
window.addEventListener('hashchange', fromHash);
[0,100,300,800,1600].forEach(function(ms){ setTimeout(quietSiteSearch, ms); });

// Warm the full-text index after the shelves paint.
if ('requestIdleCallback' in window) requestIdleCallback(()=>loadTexts());
else setTimeout(()=>loadTexts(), 1800);
