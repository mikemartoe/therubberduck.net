/* Site header behaviour for therubberduck.net (markup + /assets/trd/sitenav.css live in each page).
   - phones: the menu and search buttons open their panels
   - search: on first use it fetches /assets/search/site-index.json (built by tools/site-search-build.py:
     rooms, every Q drop, PDFs, videos, recordings, collectibles, the book and every meme) and searches it
     in the browser. X posts are searched by the X Archive's own index: the last row hands the query to /x/.
   Listeners sit on document with the native method, so the Duck Pod's soft navigation never drops them,
   and every lookup is by id, so the freshly swapped-in header of the next page just works.            */
(function () {
  'use strict';
  var W = window, D = document;
  if (W.trdNav) return;
  var on = function (t, ty, fn, o) { EventTarget.prototype.addEventListener.call(t, ty, fn, o); };
  var IDX = '/assets/search/site-index.json?v=1', data = null, loading = null, hay = null, sel = -1, last = '';
  var RANK = [0, 6, 2, 3, 4, 1, 1, 7];   /* Room, Q drop, PDF, Video, Recording, Collectible, Book, Meme */
  function $(id) { return D.getElementById(id); }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function fold(s) { return String(s).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[\u2018\u2019]/g, "'"); }
  function load() {
    if (data || loading) return loading;
    loading = fetch(IDX).then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (j) {
      data = j; hay = j.rows.map(function (r) { return fold(r[1] + ' ' + r[3]); });
      var q = $('tn-q'); if (q && q.value.trim()) run(q.value);
    }).catch(function () { loading = null; msg('Search could not load. Try again in a moment.'); });
    return loading;
  }
  function nav() { return $('trd-nav'); }
  function box() { return $('tn-res'); }
  function msg(t) { var b = box(); if (!b) return; b.innerHTML = '<div class="tn-msg">' + esc(t) + '</div>'; b.hidden = false; }
  function close() { var b = box(), q = $('tn-q'); if (b) b.hidden = true; if (q) q.setAttribute('aria-expanded', 'false'); sel = -1; }
  function xRow(q) {
    var n = data && data.xPosts ? data.xPosts.toLocaleString('en-US') + ' ' : '';
    return '<a class="tn-x" role="option" href="/x/?q=' + encodeURIComponent(q) + '"><span class="tn-k">X</span>Search ' + n + 'X posts for \u201c' + esc(q) + '\u201d \u203a</a>';
  }
  function run(raw) {
    var q = raw.trim(), b = box(), inp = $('tn-q');
    if (!b) return;
    if (q.length < 2) { close(); return; }
    if (!data) { msg('Loading the archive index\u2026'); load(); return; }
    var words = fold(q).split(/\s+/).filter(Boolean), num = /^#?\d{1,4}$/.test(q) ? q.replace('#', '') : null, hits = [];
    for (var i = 0; i < hay.length && hits.length < 4000; i++) {
      var h = hay[i], ok = true;
      for (var k = 0; k < words.length; k++) if (h.indexOf(words[k]) < 0) { ok = false; break; }
      if (ok) hits.push(i);
    }
    var rows = data.rows, fq = fold(q);
    function score(i) {
      var r = rows[i], t = fold(r[1]), s = RANK[r[0]] * 10;
      if (t.indexOf(fq) === 0) s -= 30; else if (t.indexOf(fq) >= 0) s -= 20; else if (words.every(function (w) { return t.indexOf(w) >= 0; })) s -= 10;
      if (num && r[0] === 1 && r[2] === '/drops/' + num + '/') s -= 100;
      return s;
    }
    hits.sort(function (a, b) { return score(a) - score(b) || a - b; });
    /* a mix: at most 3 of a kind first (so 7,000 memes never bury a PDF or a drop), then fill up to 10 */
    var show = [], per = {}, rest = [];
    hits.forEach(function (i) { var t = rows[i][0]; if (show.length < 10 && (per[t] || 0) < 3) { per[t] = (per[t] || 0) + 1; show.push(i); } else rest.push(i); });
    for (var r2 = 0; show.length < 10 && r2 < rest.length; r2++) show.push(rest[r2]);
    show.sort(function (a, b) { return score(a) - score(b) || a - b; });
    var html = '';
    show.forEach(function (i) {
      var r = rows[i];
      html += '<a role="option" href="' + esc(r[2]) + '"><span class="tn-k">' + esc(data.types[r[0]]) + '</span><span class="tn-t">' + esc(r[1]) + '</span>' + (r[3] ? '<span class="tn-d">' + esc(r[3]) + '</span>' : '') + '</a>';
    });
    if (!show.length) html += '<div class="tn-msg">Nothing in the rooms, drops, PDFs, videos, recordings or memes for \u201c' + esc(q) + '\u201d.</div>';
    else if (hits.length > show.length) html += '<div class="tn-msg">' + (hits.length >= 4000 ? '4,000+' : hits.length.toLocaleString('en-US')) + ' matches; add a word to narrow it down.</div>';
    html += xRow(q);
    b.innerHTML = html; b.hidden = false; sel = -1;
    if (inp) inp.setAttribute('aria-expanded', 'true');
  }
  function opts() { var b = box(); return b ? b.querySelectorAll('a') : []; }
  function mark(n) { var o = opts(); if (!o.length) return; sel = (n + o.length) % o.length; [].forEach.call(o, function (a, i) { a.classList.toggle('on', i === sel); }); o[sel].scrollIntoView({ block: 'nearest' }); }
  var tmr = 0;
  on(D, 'input', function (e) { if (e.target && e.target.id === 'tn-q') { clearTimeout(tmr); var v = e.target.value; tmr = setTimeout(function () { run(v); }, 110); } });
  on(D, 'focusin', function (e) { if (e.target && e.target.id === 'tn-q') { load(); if (e.target.value.trim().length > 1 && data) run(e.target.value); } });
  on(D, 'pointerover', function (e) { if (e.target && e.target.closest && e.target.closest('.tn-search')) load(); }, { passive: true });
  on(D, 'keydown', function (e) {
    if (!e.target || e.target.id !== 'tn-q') { if (e.key === 'Escape' && nav()) { nav().classList.remove('menu-open', 'search-open'); syncBtns(); close(); } return; }
    if (e.key === 'ArrowDown') { e.preventDefault(); mark(sel + 1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); mark(sel - 1); }
    else if (e.key === 'Escape') { close(); }
  });
  on(D, 'submit', function (e) {
    if (!e.target || e.target.id !== 'tn-form') return;
    var o = opts(), q = $('tn-q').value.trim();
    if (!q) { e.preventDefault(); return; }
    var pick = sel >= 0 ? o[sel] : (data && o.length && !o[0].classList.contains('tn-x') ? o[0] : null);
    if (pick) { e.preventDefault(); pick.click(); }   /* else: the form goes to the X Archive search */
  });
  function syncBtns() {
    var n = nav(); if (!n) return;
    var m = $('tn-menu'), s = $('tn-sbtn');
    if (m) m.setAttribute('aria-expanded', n.classList.contains('menu-open') ? 'true' : 'false');
    if (s) s.setAttribute('aria-expanded', n.classList.contains('search-open') ? 'true' : 'false');
  }
  on(D, 'click', function (e) {
    var t = e.target, n = nav(); if (!n || !t || !t.closest) return;
    if (t.closest('#tn-menu')) { n.classList.toggle('menu-open'); n.classList.remove('search-open'); close(); syncBtns(); return; }
    if (t.closest('#tn-sbtn')) {
      n.classList.toggle('search-open'); n.classList.remove('menu-open'); syncBtns();
      if (n.classList.contains('search-open')) { load(); var q = $('tn-q'); if (q) q.focus(); } else close();
      return;
    }
    if (t.closest('.tn-res a') || t.closest('.tn-links a')) { n.classList.remove('menu-open', 'search-open'); syncBtns(); close(); return; }
    if (!t.closest('#trd-nav')) { if (n.classList.contains('menu-open') || n.classList.contains('search-open')) { n.classList.remove('menu-open', 'search-open'); syncBtns(); } close(); }
  });
  /* mark the current room */
  function current() {
    var n = nav(); if (!n) return;
    var p = location.pathname.replace(/index\.html$/, '');
    [].forEach.call(n.querySelectorAll('.tn-links a'), function (a) {
      var h = a.getAttribute('href'); if (h === p || (h === '/x/' && p.indexOf('/x/') === 0)) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
    });
  }
  current();
  var MO = W.MutationObserver; try { var pr = new MO(function () {}); if (pr.constructor) MO = pr.constructor; pr.disconnect(); } catch (x) {}
  function watch() { if (D.body) new MO(current).observe(D.body, { childList: true }); }
  if (D.readyState === 'loading') on(D, 'DOMContentLoaded', function () { current(); watch(); }); else watch();
  /* the site footer is always the last thing on the page: the suggestion section (suggest.js) and anything
     else added to the end of <body> goes above it */
  function footLast() {
    var f = D.querySelector('footer.site-foot'), b = D.body; if (!f || !b) return;
    var sg = D.getElementById('trd-suggest');
    if (f.parentNode !== b) { b.insertBefore(f, sg && sg.parentNode === b ? sg.nextSibling : null); return; }
    if (sg && sg.parentNode === b && (f.compareDocumentPosition(sg) & 4)) b.insertBefore(f, sg.nextSibling);
  }
  if (D.body) { footLast(); new MO(footLast).observe(D.body, { childList: true }); }
  else on(D, 'DOMContentLoaded', function () { footLast(); new MO(footLast).observe(D.body, { childList: true }); });
  /* footer: 'Suggestion box' opens the same card as the corner box (suggest.js); without it, go to the X profile */
  on(D, 'click', function (e) {
    var b = e.target && e.target.closest && e.target.closest('[data-sug-open]'); if (!b) return;
    if (W.trdSuggest && W.trdSuggest.open) { e.preventDefault(); W.trdSuggest.open(e); }
  });
  W.trdNav = { load: load, run: run };
})();
