/* TRD click and event tracking (GoatCounter).
   Invisible and fire-and-forget: it never touches the page, never delays a click and never
   blocks navigation. GoatCounter's count() sends with navigator.sendBeacon, so a hit survives
   the page unloading. If GoatCounter is blocked or not loaded, nothing happens (events made in
   the first seconds are held briefly and sent once it loads; they are dropped after 8 s).
   One file for the whole site. Include once per page, in <head>, with data-trd-keep:
     <script src="/assets/trd/track.js" data-trd-keep></script>
   Pages call  window.trdTrack(path, title)  for their own events. The same path is counted at
   most once per 1.5 s, so a double-click or a tap plus a click is one event.
   This file also counts, for every page, with one delegated listener:
     outbound Gumroad, Stripe and Buy Me a Coffee links, the header links, the homepage shop,
     book strip and room tapes, and the Process page's buttons.                                   */
(function () {
  'use strict';
  var W = window, D = document;
  if (W.trdTrack) return;
  var last = {}, Q = [], qT = 0, GAP = 1500, HOLD = 8000;
  /* the site router (duckpod.js) drops page listeners and timers on every soft navigation,
     so this file registers its listeners with the native method and never relies on one timer */
  var listen = EventTarget.prototype.addEventListener;

  function slug(s, n) {
    return String(s == null ? '' : s).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, n || 60).replace(/-+$/, '') || 'unknown';
  }
  function send(path, title) {
    var gc = W.goatcounter;
    if (!gc || typeof gc.count !== 'function') return false;
    try { gc.count({ path: path, title: title || path, event: true }); } catch (e) {}
    return true;
  }
  function flush() {
    qT = 0;
    var now = Date.now(), keep = [];
    Q.forEach(function (e) { if (!send(e[0], e[1]) && now - e[2] < HOLD) keep.push(e); });
    Q = keep;
    later();
  }
  function later() {
    if (!Q.length || (qT && Date.now() - qT < 1000)) return;
    qT = Date.now(); setTimeout(flush, 400);
  }
  function track(path, title, gap) {
    try {
      if (!path) return;
      path = String(path);
      var now = Date.now(), g = gap == null ? GAP : gap;
      if (last[path] && now - last[path] < g) return;
      last[path] = now;
      if (Q.length) flush();
      if (!send(path, title)) { Q.push([path, title, now]); later(); }
    } catch (e) {}
  }

  function home() { return /^\/(index\.html)?$/i.test(location.pathname); }
  function txt(el) { return (el && (el.getAttribute('aria-label') || el.textContent) || '').replace(/\s+/g, ' ').trim(); }

  /* the event for a link, or null when the link is not tracked */
  function forLink(a) {
    if (!a || !a.getAttribute) return null;
    var href = a.getAttribute('href') || '', u;
    try { u = new URL(href, location.href); } catch (e) { return null; }
    var host = u.hostname.replace(/^www\./, ''), seg = u.pathname.split('/').filter(Boolean);

    if (a.closest('#trd-ambook, #trd-book')) return ['click/book-gumroad', 'Book: anon mission Volume 1 (Gumroad)'];
    if (/(^|\.)gumroad\.com$/.test(host) || host === 'gum.co') return ['click/out/gumroad/' + slug(seg[seg.length - 1] || host), 'Gumroad: ' + (txt(a) || u.href).slice(0, 80)];
    if (host === 'buy.stripe.com' || host === 'checkout.stripe.com' || host === 'donate.stripe.com') {
      var item = a.closest('[data-slug]');
      if (item) {
        var nm = item.querySelector('.bk-nm'), col = item.querySelector('.cname'), sz = item.querySelector('select.size');
        var opt = [col && col.textContent, sz && sz.value].filter(Boolean).join(', ');
        return ['click/buy/' + slug(item.getAttribute('data-slug')), 'Buy: ' + ((nm && nm.textContent) || item.getAttribute('data-slug')).trim() + (opt ? ' (' + opt + ')' : '')];
      }
      return ['click/out/stripe/' + slug(seg[0] || host), 'Stripe: ' + (txt(a) || u.href).slice(0, 80)];
    }
    if (host === 'buymeacoffee.com') return ['click/support-bmc', 'Support the Duck (Buy Me a Coffee)'];

    if (a.closest('.banner .meta')) {
      if (host === 'x.com' || host === 'twitter.com') return ['click/header/x', 'Header: @' + (seg[0] || 'X') + ' on X'];
      if (/\/ledger\.html$/i.test(u.pathname)) return ['click/header/ledger', 'Header: The Drop Ledger'];
      if (/\/album(\.html|\/)?$/i.test(u.pathname)) return ['click/header/album', 'Header: The Red Pill Album'];
      return ['click/header/' + slug(txt(a)), 'Header: ' + txt(a)];
    }

    if (home()) {
      if (a.matches('a.shop')) return ['click/shop-enter', 'Homepage: TRD Collectibles shop (Step inside)'];
      if (a.matches('a.deck')) return ['click/album-open', 'Homepage: tape deck, open the album player'];
      if (a.matches('a.spine')) {
        var room = seg.length ? seg[seg.length - 1].replace(/\.html?$/i, '') : 'home';
        return ['click/tape/' + slug(room), 'Homepage tape: ' + txt(a.querySelector('.sp-n') || a)];
      }
    }
    if (/^\/process\.html$/i.test(location.pathname) && a.matches('.k-cta, a.btn')) return ['click/process/' + slug(txt(a)), 'Process: ' + txt(a)];
    return null;
  }

  /* count a link the way a real click on it would (used by pages that open links from script) */
  function link(a) { var ev = forLink(a); if (ev) track(ev[0], ev[1]); }

  /* one delegated listener: counts only clicks that will really follow the link
     (bubble phase, so a page script that cancels the click to do something else is respected) */
  function onClick(e) {
    try {
      if (e.type === 'auxclick' && e.button !== 1) return;
      if (e.type === 'click' && e.button !== 0) return;
      if (e.defaultPrevented) return;
      var a = e.target && e.target.closest && e.target.closest('a[href]');
      if (a) link(a);
    } catch (x) {}
  }
  listen.call(D, 'click', onClick, false);
  listen.call(D, 'auxclick', onClick, false);

  track.link = link;
  track.forLink = forLink;
  track.slug = slug;
  W.trdTrack = track;
})();
