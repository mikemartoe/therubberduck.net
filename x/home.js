'use strict';
(function(){
  const PER = 30;
  const form = document.getElementById('f'), $ = id => document.getElementById(id);
  const KEYS = ['q', 'from', 'to', 'y', 'sort', 'type', 'media', 'qr', 'h', 'm', 'd'];
  const hm = /^#(?:id=)?(\d{6,25})$/.exec(location.hash);
  if(hm){ location.replace('/x/post.html?id=' + hm[1]); return; }
  let results = [], page = 1, st = {};
  function readURL(){
    const u = new URLSearchParams(location.search); st = {};
    KEYS.forEach(k => { const v = u.get(k); if(v) st[k] = v; });
    page = Math.max(1, parseInt(u.get('page') || '1', 10) || 1);
    KEYS.forEach(k => { if(form.elements[k]) form.elements[k].value = st[k] || (form.elements[k].tagName === 'SELECT' ? form.elements[k].options[0].value : ''); });
  }
  function writeURL(push){
    const u = new URLSearchParams(); KEYS.forEach(k => { if(st[k]) u.set(k, st[k]); }); if(page > 1) u.set('page', page);
    const s = u.toString(); history[push ? 'pushState' : 'replaceState'](null, '', s ? '?' + s : location.pathname);
  }
  function fromForm(){ st = {}; KEYS.forEach(k => { const v = (form.elements[k].value || '').trim(); if(v && !['new', 'all', 'any'].includes(v)) st[k] = v; }); }
  async function run(){
    $('count').textContent = 'Searching'; $('time').textContent = '';
    const t0 = performance.now();
    try{
      results = await search(st, (a, b) => { $('count').textContent = 'Checking phrase in ' + a + ' of ' + b + ' months'; });
    }catch(e){ $('count').textContent = 'Search failed: ' + e.message; return; }
    const ms = performance.now() - t0;
    window.__lastSearchMs = ms;
    const any = Object.keys(st).some(k => k !== 'sort');
    $('count').textContent = fmtN(results.length) + (any ? ' matching posts' : ' posts') ;
    $('time').textContent = 'found in ' + (ms < 1000 ? Math.round(ms) + ' ms' : (ms / 1000).toFixed(2) + ' s');
    await render();
  }
  async function render(){
    const pages = Math.max(1, Math.ceil(results.length / PER)); if(page > pages) page = pages;
    const slice = results.slice((page - 1) * PER, page * PER);
    const t0 = performance.now();
    const posts = await Promise.all(slice.map(postAt));
    $('res').innerHTML = posts.length ? posts.map(p => postHtml(p)).join('') : '<div class="msg">No posts match. Try fewer words, a wider date range, or Reset.</div>';
    window.__lastRenderMs = performance.now() - t0;
    const pg = $('pager');
    if(pages <= 1){ pg.innerHTML = ''; return; }
    pg.innerHTML = '<button type="button" data-p="1"' + (page === 1 ? ' disabled' : '') + '>First</button><button type="button" data-p="' + (page - 1) + '"' + (page === 1 ? ' disabled' : '') + '>Prev</button>' +
      '<span>Page <input type="number" min="1" max="' + pages + '" value="' + page + '" aria-label="Page number"> of ' + fmtN(pages) + '</span>' +
      '<button type="button" data-p="' + (page + 1) + '"' + (page === pages ? ' disabled' : '') + '>Next</button><button type="button" data-p="' + pages + '"' + (page === pages ? ' disabled' : '') + '>Last</button>';
  }
  function go(p, scroll){ page = p; writeURL(true); render().then(() => { if(scroll) $('count').scrollIntoView({block: 'start'}); }); }
  $('pager').addEventListener('click', e => { const b = e.target.closest('button[data-p]'); if(b && !b.disabled) go(+b.dataset.p, true); });
  $('pager').addEventListener('change', e => { if(e.target.tagName === 'INPUT'){ const pages = Math.ceil(results.length / PER); go(Math.min(pages, Math.max(1, +e.target.value || 1)), true); } });
  form.addEventListener('submit', e => { e.preventDefault(); fromForm(); page = 1; writeURL(true); run(); });
  form.addEventListener('change', e => { if(e.target.tagName === 'SELECT' || e.target.type === 'date'){ fromForm(); page = 1; writeURL(true); run(); } });
  $('reset').addEventListener('click', () => { history.pushState(null, '', location.pathname); readURL(); run(); });
  window.addEventListener('popstate', () => { readURL(); run(); });
  document.addEventListener('click', e => {
    const a = e.target.closest && e.target.closest('.tx a[href^="/x/?h="]'); if(!a) return;
    e.preventDefault(); st = {h: decodeURIComponent(a.getAttribute('href').slice(6))}; page = 1; writeURL(true); readURL(); run(); window.scrollTo(0, 0);
  });
  (async function init(){
    readURL();
    if(matchMedia('(max-width:1000px)').matches && !Object.keys(st).some(k => k !== 'q')) $('adv').open = false;
    await meta();
    const years = [...new Set(META.months.map(m => m.slice(0, 4)))];
    $('y').insertAdjacentHTML('beforeend', years.map(y => '<option>' + y + '</option>').join('')); if(st.y) $('y').value = st.y;
    const first = META.ids.length ? new Date(META.ts[0] * 1000).toISOString().slice(0, 10) : '', last = new Date(META.ts[META.n - 1] * 1000).toISOString().slice(0, 10);
    $('stats').textContent = fmtN(META.n) + ' posts by @TheRubberDuck79, ' + first + ' to ' + last + ' (UTC), exactly as posted. Search the full text, filter, and open any post on its own page.';
    run();
    getJSON(D + 'facets.json').then(f => {
      [['h', '#'], ['m', '@'], ['d', '']].forEach(([k]) => { $('dl-' + k).innerHTML = f[k].map(([v, c]) => '<option value="' + esc(v) + '">' + c + ' posts</option>').join(''); });
    });
    getJSON(D + 'dl/files.json').then(rows => {
      const mb = b => (b / 1048576).toFixed(1) + ' MB';
      $('dlt').innerHTML = rows.map(([y, n, j, c]) => '<tr><td>' + y + '</td><td>' + fmtN(n) + '</td><td><a href="' + D + 'dl/posts-' + y + '.jsonl.gz" download>posts-' + y + '.jsonl.gz</a> (' + mb(j) + ')</td><td><a href="' + D + 'dl/posts-' + y + '.csv.gz" download>posts-' + y + '.csv.gz</a> (' + mb(c) + ')</td></tr>').join('');
    });
  })();
})();
