/* Loads the shared isolated-drop window on every archive page that includes this file,
   including a normal browser tab (the app bar below still runs only when installed). */
(function () {
  if (window.trdDropView || document.querySelector('script[data-trd-drop-view]')) return;
  var s = document.createElement('script');
  s.src = '/assets/trd/drop-view.js?v=20261112a';
  s.setAttribute('data-trd-drop-view', '');
  s.setAttribute('data-trd-keep', '');
  (document.head || document.documentElement).appendChild(s);
})();
/* The Rubber Duck web app: app bar for the static archive pages (Deltas, Q Proofs, Q drop pages).
   Does nothing in a normal browser tab. Only when the page runs inside the installed app
   (display-mode: standalone, or iOS navigator.standalone) it:
     - swaps the website header (room links) for a slim app bar: Back, the duck (app home /app/), Menu
       with the same links as the app home menu, so there is always a way back inside the app window;
     - points "Home" links (brand, breadcrumb, footer) at the app home /app/ instead of the website homepage;
     - opens links to other sites (X, Rumble) in a new window, so the app page stays where it was;
     - jumps within the page (Jump to 2017) without adding history steps, so Back leaves the page.
   Back = the previous page in the app when there is one, otherwise the app home.
   No tracking, no storage. Loaded in <head> (not deferred) so the website header never flashes. */
(function () {
  'use strict';
  var W = window, D = document, H = D.documentElement;
  var sa = false;
  try { sa = (W.matchMedia && W.matchMedia('(display-mode: standalone)').matches) || W.navigator.standalone === true; } catch (e) {}
  if (!sa || W.trdAppBar) return;
  W.trdAppBar = true;
  H.classList.add('trd-standalone');
  var css = D.createElement('style');
  css.textContent =
    '.trd-standalone header.top{display:none}' +
    '.trd-standalone{scroll-padding-top:72px}' +
    '.tab{position:sticky;top:0;z-index:50;background:#050A07;border-bottom:1px solid #34533D;padding-top:env(safe-area-inset-top,0px)}' +
    '.tab-in{max-width:960px;margin:0 auto;padding:8px 18px;display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:12px}' +
    '.tab a,.tab button,.tab summary{font:700 15px/1 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;letter-spacing:.04em;color:#E8F4E9;text-decoration:none}' +
    '.tab-back{justify-self:start;display:inline-flex;align-items:center;gap:6px;min-height:44px;min-width:44px;padding:0 14px 0 10px;border:1px solid #34533D;background:#0B140E;cursor:pointer;border-radius:0}' +
    '.tab-back svg{width:18px;height:18px;stroke:#00ED39;fill:none;stroke-width:2.6;stroke-linecap:round;stroke-linejoin:round}' +
    '.tab-home{display:flex;align-items:center;gap:8px;min-height:44px}.tab-home img{width:34px;height:auto;display:block}' +
    '.tab-home span{font:800 13px/1.05 system-ui,-apple-system,"Segoe UI",Arial,sans-serif;letter-spacing:.02em;color:#fff}' +
    '.tab-menu{justify-self:end;position:relative}' +
    '.tab-menu summary{list-style:none;min-height:44px;min-width:76px;display:flex;align-items:center;justify-content:center;border:1px solid #34533D;background:#0B140E;cursor:pointer}' +
    '.tab-menu summary::-webkit-details-marker{display:none}.tab-menu[open] summary{border-color:#00ED39;color:#00ED39}' +
    '.tab-menu nav{position:absolute;right:0;top:52px;width:240px;max-height:calc(100vh - 96px);overflow-y:auto;background:#0B140E;border:1px solid #34533D;padding:8px 0;box-shadow:0 10px 30px rgba(0,0,0,.55)}' +
    '.tab-menu nav a{display:flex;align-items:center;min-height:48px;padding:0 16px;font-weight:400}' +
    '.tab-menu nav a:hover,.tab-menu nav a:focus{background:#13241A;color:#00ED39}' +
    '.tab a:focus-visible,.tab button:focus-visible,.tab summary:focus-visible{outline:2px solid #00ED39;outline-offset:2px}';
  (D.head || H).appendChild(css);

  var MENU = [['/app/', 'App home'], ['/ledger.html', 'Drop Ledger'], ['/deltas/', 'Deltas'], ['/q-proofs/', 'Q Proofs'],
    ['/videos.html', 'Videos'], ['/listening-room.html', 'Audio'], ['/pdfs.html', 'Docs'], ['/x/', 'X Archive'],
    ['/alerts/', 'Get alerts'], ['/merch.html', 'Shop']];

  function sameOriginReferrer() {
    try { return !!D.referrer && new URL(D.referrer).origin === location.origin && D.referrer !== location.href; } catch (e) { return false; }
  }
  function back() {
    if (W.history.length > 1 && sameOriginReferrer()) { W.history.back(); return; }
    location.href = '/app/';
  }

  function build() {
    if (D.querySelector('.tab')) return;
    var bar = D.createElement('div');
    bar.className = 'tab';
    bar.innerHTML = '<div class="tab-in">' +
      '<button type="button" class="tab-back" aria-label="Back"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 18l-6-6 6-6"/></svg>Back</button>' +
      '<a class="tab-home" href="/app/" aria-label="The Rubber Duck app home"><img src="/images/app/duck-white.svg" alt="" width="34" height="29"><span>THE RUBBER<br>DUCK</span></a>' +
      '<details class="tab-menu"><summary>MENU</summary><nav aria-label="App">' +
      MENU.map(function (m) { return '<a href="' + m[0] + '">' + m[1] + '</a>'; }).join('') +
      '</nav></details></div>';
    D.body.insertBefore(bar, D.body.firstChild);
    bar.querySelector('.tab-back').addEventListener('click', back);
    var menu = bar.querySelector('.tab-menu');
    D.addEventListener('click', function (e) { if (menu.open && !menu.contains(e.target)) menu.open = false; });
    D.addEventListener('keydown', function (e) { if (e.key === 'Escape' && menu.open) { menu.open = false; menu.querySelector('summary').focus(); } });

    /* links: "Home" -> app home, other sites -> new window */
    var as = D.querySelectorAll('a[href]');
    for (var i = 0; i < as.length; i++) {
      var a = as[i]; if (bar.contains(a)) continue;
      var raw = a.getAttribute('href'), u;
      try { u = new URL(raw, location.href); } catch (e) { continue; }
      if (u.protocol !== 'http:' && u.protocol !== 'https:') continue;
      if (u.origin !== location.origin) { a.target = '_blank'; a.rel = 'noopener'; continue; }
      if (u.pathname === '/' || u.pathname === '/index.html') { if (!u.hash) a.setAttribute('href', '/app/'); }
    }
  }

  /* in-page jumps (#y2017) scroll without a history step, so Back always leaves the page */
  D.addEventListener('click', function (e) {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey) return;
    var a = e.target.closest && e.target.closest('a[href^="#"]'); if (!a) return;
    var id = decodeURIComponent(a.getAttribute('href').slice(1)), t = id && D.getElementById(id); if (!t) return;
    e.preventDefault();
    t.scrollIntoView({ behavior: 'smooth', block: 'start' });
    try { W.history.replaceState(W.history.state, '', '#' + id); } catch (x) {}
  });

  if (D.readyState === 'loading') D.addEventListener('DOMContentLoaded', build); else build();
})();
