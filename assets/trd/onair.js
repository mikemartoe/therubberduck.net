/* ON AIR · LIVE light-box sign (therubberduck.net). One shared file on every room landing page.
   Reads /live.json:
     { "live": false, "liveUrl": "", "liveLabel": "",
       "latestArticle": { "slug": "", "title": "", "url": "", "publishedAt": "YYYY-MM-DD or ISO" } }
   Lights up when (a) live === true  ->  click opens liveUrl, label = liveLabel || "LIVE NOW"
               or (b) the newest DUCK SAUCE article is unseen by this visitor and was published
                   within the last 24h, or is newer than the last article this visitor saw (localStorage)
                   -> click opens the article, label "NEW DISPATCH".
   Dim otherwise. Re-checks every 2 minutes while the tab is visible. See README-LIVE.md. */
(function () {
  'use strict';
  if (window.__trdOnAir) return; window.__trdOnAir = 1;
  var SEEN = 'trd-onair-seen', DAY = 864e5, POLL = 12e4;
  var css = ''
  + '.trd-onair{position:fixed;z-index:1001;left:14px;top:62px;display:flex;flex-direction:column;align-items:flex-start;gap:5px;text-decoration:none;-webkit-tap-highlight-color:transparent;transition:opacity .3s ease,transform .3s ease}'
  + '.trd-onair .oa-box{position:relative;display:flex;flex-direction:column;align-items:center;justify-content:center;box-sizing:border-box;width:96px;height:40px;padding:3px 6px 2px;border-radius:5px;'
  + 'background:linear-gradient(180deg,#2b2520,#141010);box-shadow:0 0 0 1px #000,inset 0 1px 0 rgba(255,255,255,.12),0 4px 10px rgba(0,0,0,.6)}'
  + '.trd-onair .oa-box::before{content:"";position:absolute;inset:4px;border-radius:2px;background:linear-gradient(180deg,#4a443b,#36312a);box-shadow:inset 0 0 0 1px rgba(0,0,0,.6),inset 0 2px 6px rgba(0,0,0,.55);transition:background .4s ease,box-shadow .4s ease}'
  + '.trd-onair .oa-box::after{content:"";position:absolute;left:3px;right:3px;top:1px;height:1px;background:linear-gradient(90deg,transparent,rgba(255,255,255,.25),transparent)}'
  + '.trd-onair .oa-on,.trd-onair .oa-sub{position:relative;z-index:1;line-height:1;white-space:nowrap;transition:color .4s ease,text-shadow .4s ease}'
  + '.trd-onair .oa-on{font:700 21px/1 "TRN Steelfish","Steelfish","Arial Narrow",Impact,sans-serif;letter-spacing:.09em;margin-right:-.09em;color:#8c3a31;text-shadow:0 1px 0 rgba(0,0,0,.45)}'
  + '.trd-onair .oa-sub{margin-top:1px;font:700 7.5px/1 "TRN Courier","Courier Prime","Courier New",monospace;letter-spacing:.38em;margin-right:-.38em;text-transform:uppercase;color:#7d715c}'
  + '.trd-onair .oa-lbl{display:none;padding:4px 6px 3px;border-radius:3px;background:rgba(11,8,5,.88);border:1px solid #5a4020;color:#ffd77a;font:700 9.5px/1 "TRN Courier","Courier Prime","Courier New",monospace;letter-spacing:.12em;text-transform:uppercase;white-space:nowrap;box-shadow:0 3px 8px rgba(0,0,0,.5)}'
  + '.trd-onair .oa-lbl i{font-style:normal;margin-left:5px}'
  + '.trd-onair.is-dim{cursor:default;opacity:.9}'
  + '.trd-onair.is-lit{cursor:pointer}'
  + '.trd-onair.is-lit .oa-box::before{background:radial-gradient(120% 140% at 50% 40%,#fffdf6 0,#fbf1dc 55%,#ecd9b4 100%);box-shadow:inset 0 0 0 1px rgba(120,60,20,.35),inset 0 0 10px rgba(255,190,120,.55)}'
  + '.trd-onair.is-lit .oa-box{box-shadow:0 0 0 1px #000,inset 0 1px 0 rgba(255,255,255,.12),0 4px 10px rgba(0,0,0,.6),0 0 16px 3px rgba(255,214,150,.55),0 0 42px 10px rgba(255,150,70,.28)}'
  + '.trd-onair.is-lit .oa-on{color:#d9161b;text-shadow:0 0 2px rgba(255,40,30,.7),0 0 8px rgba(255,60,40,.45)}'
  + '.trd-onair.is-lit .oa-sub{color:#b3201c}'
  + '.trd-onair.is-lit .oa-lbl{display:inline-block}'
  + '.trd-onair.is-lit:hover .oa-lbl,.trd-onair.is-lit:focus-visible .oa-lbl{border-color:#e3a82b;color:#fff}'
  + '.trd-onair:focus-visible{outline:3px solid #ffd77a;outline-offset:3px;border-radius:6px}'
  + '.trd-onair.is-away.is-dim{opacity:0;pointer-events:none;transform:translateY(-6px)}'
  + '@media (prefers-reduced-motion:no-preference){.trd-onair.is-lit .oa-box{animation:oaGlow 5s ease-in-out infinite}.trd-onair.is-lit .oa-on{animation:oaFlick 7s linear infinite}}'
  + '@keyframes oaGlow{0%,100%{filter:brightness(1)}50%{filter:brightness(1.08)}}'
  + '@keyframes oaFlick{0%,61%,63.5%,66%,100%{opacity:1}62%{opacity:.55}64.5%{opacity:.75}}'
  /* compact sign: phones (in the header bar, right of the logo), small laptops, and the top strip on pages without the header */
  + '.trd-onair.compact .oa-box{width:74px;height:32px;padding:2px 4px 2px}'
  + '.trd-onair.compact .oa-box::before{inset:3px}'
  + '.trd-onair.compact .oa-on{font-size:15.5px}'
  + '.trd-onair.compact .oa-sub{font-size:6.5px;letter-spacing:.16em;margin-right:-.16em}'
  + '.trd-onair.compact .oa-lbl{display:none!important}'
  + '.trd-onair-strip{display:flex;align-items:center;height:40px;padding:0 10px;background:#0b0805;border-bottom:1px solid #3a2814;position:relative;z-index:5}'
  + '.trd-onair.in-strip{position:relative;left:auto;top:auto}'
  + '.trd-onair.in-nav{position:relative;left:auto;top:auto;flex:none;margin:0 0 0 2px}'
  + '.trd-onair.in-nav.is-dim{opacity:.9}'
  + '.trd-onair.in-nav.tight .oa-box{width:62px}.trd-onair.in-nav.tight .oa-on{font-size:14px}.trd-onair.in-nav.tight .oa-sub{letter-spacing:.04em;margin-right:0}'
  + '.trd-onair.no-nav{top:10px;left:10px}'
  + '@media print{.trd-onair{display:none}}';

  var st = document.createElement('style'); st.id = 'trd-onair-css'; st.textContent = css;
  (document.head || document.documentElement).appendChild(st);

  var el, state = { lit: false, href: '', mode: '' }, data = null;
  var onNewsroom = /^\/newsroom(\.html|\/)?/.test(location.pathname);
  function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  function ts(s) { if (!s) return NaN; var t = Date.parse(/^\d{4}-\d{2}-\d{2}$/.test(s) ? s + 'T12:00:00-05:00' : s); return t; }

  function build() {
    el = document.createElement('a');
    el.className = 'trd-onair is-dim';
    el.setAttribute('aria-label', 'On air: nothing live right now');
    el.innerHTML = '<span class="oa-box" aria-hidden="true"><span class="oa-on">ON AIR</span><span class="oa-sub">Live</span></span><span class="oa-lbl" aria-hidden="true"></span>';
    el.addEventListener('click', function (e) {
      if (!state.lit) { e.preventDefault(); return; }
      if (state.mode === 'new' && data && data.latestArticle) lsSet(SEEN, data.latestArticle.slug || '');
    });
    place();
  }
  function place() {
    var inn = document.querySelector('.trd-nav .tn-in'), logo = inn && inn.querySelector('.tn-logo');
    var w = window.innerWidth, narrow = window.matchMedia('(max-width:820px)').matches;
    el.classList.remove('in-nav', 'no-nav', 'tight', 'compact', 'in-strip'); el.style.top = '';
    var strip = document.querySelector('.trd-onair-strip');
    if (inn && logo && narrow) {
      el.classList.add('in-nav', 'compact');
      if (el.parentNode !== inn) logo.insertAdjacentElement('afterend', el);
      var btn = inn.querySelector('.tn-menu');
      if (btn && btn.getBoundingClientRect().left - el.getBoundingClientRect().right < 6) el.classList.add('tight');
    } else if (!inn && w < 1200) {
      // pages without the site header (Drop Ledger): a slim strip on top of the page, sign on the left
      if (!strip) { strip = document.createElement('div'); strip.className = 'trd-onair-strip'; document.body.insertBefore(strip, document.body.firstChild); }
      el.classList.add('in-strip', 'compact');
      if (el.parentNode !== strip) strip.appendChild(el);
    } else {
      if (!inn) el.classList.add('no-nav');
      if (w < 1200) el.classList.add('compact');
      if (el.parentNode !== document.body) document.body.appendChild(el);
      if (inn) { var nb = document.querySelector('.trd-nav').getBoundingClientRect().bottom; el.style.top = Math.max(0, Math.round(nb)) + 10 + 'px'; }
    }
    if (strip && el.parentNode !== strip) { strip.parentNode.removeChild(strip); }
  }
  function render() {
    var sub = el.querySelector('.oa-sub'), lbl = el.querySelector('.oa-lbl');
    el.classList.toggle('is-lit', state.lit); el.classList.toggle('is-dim', !state.lit);
    if (state.lit) {
      el.href = state.href; el.removeAttribute('aria-disabled'); el.tabIndex = 0;
      if (state.external) { el.target = '_blank'; el.rel = 'noopener'; } else { el.removeAttribute('target'); el.removeAttribute('rel'); }
      lbl.innerHTML = state.label + '<i>&rsaquo;</i>';
      sub.textContent = el.classList.contains('compact') ? (state.mode === 'live' ? 'Live now' : 'New post') : 'Live';
      el.setAttribute('aria-label', state.aria); el.title = state.aria;
    } else {
      el.removeAttribute('href'); el.setAttribute('aria-disabled', 'true'); el.tabIndex = -1; el.removeAttribute('title');
      sub.textContent = 'Live';
      el.setAttribute('aria-label', 'On air sign: nothing live right now');
    }
  }
  function decide(d) {
    data = d || {}; var a = data.latestArticle || {};
    if (data.live === true && data.liveUrl) {
      var ext = /^https?:/i.test(data.liveUrl) && data.liveUrl.indexOf(location.host) < 0;
      state = { lit: true, mode: 'live', href: data.liveUrl, external: ext, label: data.liveLabel || 'Live now',
        aria: 'On air: The Rubber Duck is live now' + (data.liveLabel ? ', ' + data.liveLabel : '') + '. Open the broadcast' };
    } else if (a.slug && a.url) {
      var seen = lsGet(SEEN), t = ts(a.publishedAt), fresh = !isNaN(t) && Date.now() - t < DAY;
      if (onNewsroom) { lsSet(SEEN, a.slug); seen = a.slug; }
      var unseen = seen !== a.slug;
      var lit = unseen && (fresh || (seen !== null && seen !== ''));
      if (seen === null && !fresh) lsSet(SEEN, a.slug); // first visit, nothing new: remember the baseline
      state = lit ? { lit: true, mode: 'new', href: a.url, label: 'New dispatch',
        aria: 'On air: new DUCK SAUCE dispatch, ' + (a.title || 'read the newest article') } : { lit: false };
    } else state = { lit: false };
    render();
  }
  function load() {
    var x = new XMLHttpRequest();
    x.open('GET', '/live.json?t=' + Math.floor(Date.now() / 6e4), true);
    x.onload = function () { if (x.status >= 200 && x.status < 300) { try { decide(JSON.parse(x.responseText)); } catch (e) {} } };
    x.send();
  }
  function onScroll() { el.classList.toggle('is-away', !el.classList.contains('in-nav') && !el.classList.contains('in-strip') && (window.scrollY || 0) > 160); }
  function start() {
    build(); render(); load(); onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    var rt; window.addEventListener('resize', function () { clearTimeout(rt); rt = setTimeout(function () { place(); render(); onScroll(); }, 120); });
    setInterval(function () { if (!document.hidden) load(); }, POLL);
    document.addEventListener('visibilitychange', function () { if (!document.hidden) load(); });
    window.trdOnAir = { refresh: load, set: decide };
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
