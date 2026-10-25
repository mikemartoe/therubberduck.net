/* TRD anonymous visit analytics (time on site, pages, page order, rooms used, share taps).
   - No cookies, no personal info, no fingerprinting. A visit is a random id kept in localStorage for
     30 minutes of inactivity, then thrown away; nothing ties two visits together.
   - Skipped entirely when the browser sends Global Privacy Control or Do Not Track.
   - Sends small JSON batches with navigator.sendBeacon to ENDPOINT (the trd-visits Worker,
     workers/trd-visits/). While ENDPOINT is empty this file only keeps its queue in memory: STUB, nothing leaves the page.
   - GoatCounter (page counts, referrers, utm campaigns, share-tap events) keeps running as before; this adds
     the per-visit view GoatCounter cannot give (paths, order, time, multi-room).
   Debug: localStorage['trd.v.debug']='1' logs every payload to the console.                                */
(function () {
  'use strict';
  var W = window, D = document;
  if (W.trdVisit) return;
  var ENDPOINT = '';                         /* e.g. '/api/v' once the Worker route is live */
  var IDLE = 30 * 60 * 1000, KEY = 'trd.v';
  var listen = EventTarget.prototype.addEventListener, _setTimeout = W.setTimeout;
  var off = navigator.globalPrivacyControl === true || navigator.doNotTrack === '1' || W.doNotTrack === '1';
  var debug = false; try { debug = localStorage.getItem('trd.v.debug') === '1'; } catch (e) {}

  function rid() { var a = new Uint8Array(8); (W.crypto || W.msCrypto).getRandomValues(a); return Array.prototype.map.call(a, function (b) { return ('0' + b.toString(16)).slice(-2); }).join(''); }
  function store() { try { return JSON.parse(localStorage.getItem(KEY) || 'null'); } catch (e) { return null; } }
  function save(v) { try { localStorage.setItem(KEY, JSON.stringify(v)); } catch (e) {} }
  var now = Date.now(), v = store(), fresh = false;
  if (!v || !v.id || now - (v.last || 0) > IDLE) { v = { id: rid(), seq: 0, start: now }; fresh = true; }

  function room(p) {
    p = (p || '/').toLowerCase();
    if (p === '/' || p === '/index.html') return 'home';
    var r = [[/^\/ledger|^\/drops\//, 'ledger'], [/^\/videos|^\/watch\//, 'videos'], [/^\/listening-room|^\/listen\//, 'listening'],
      [/^\/pdfs|^\/library\/|^\/scif\//, 'scif'], [/^\/x\//, 'x-archive'], [/^\/memes/, 'memes'], [/^\/album/, 'album'],
      [/^\/merch|^\/shop\//, 'shop'], [/^\/book\//, 'book'], [/^\/sponsor/, 'sponsor'], [/^\/process/, 'process']];
    for (var i = 0; i < r.length; i++) if (r[i][0].test(p)) return r[i][1];
    return 'other';
  }
  var Q = [], cur = null, shown = 0, visibleMs = 0;
  function push(type, extra) {
    v.seq += 1; v.last = Date.now(); save(v);
    var h = { v: v.id, n: v.seq, t: type, ts: v.last };
    for (var k in extra) if (extra[k] != null && extra[k] !== '') h[k] = extra[k];
    Q.push(h); if (debug) try { console.log('[trd.visit]', h); } catch (e) {}
  }
  function flush() {
    if (!Q.length || off || !ENDPOINT) return;
    var body = JSON.stringify(Q); Q = [];
    try { if (!navigator.sendBeacon(ENDPOINT, new Blob([body], { type: 'text/plain' }))) throw 0; }
    catch (e) { try { fetch(ENDPOINT, { method: 'POST', body: body, keepalive: true, credentials: 'omit' }); } catch (x) {} }
  }
  function leave() {
    if (!cur) return;
    if (shown) { visibleMs += Date.now() - shown; shown = 0; }
    push('leave', { p: cur, ms: Math.min(visibleMs, 6 * 3600 * 1000) });
    cur = null;
  }
  function view() {
    var p = location.pathname;
    if (p === cur) return;
    leave();
    cur = p; visibleMs = 0; shown = D.visibilityState === 'visible' ? Date.now() : 0;
    var x = { p: p, room: room(p) };
    if (fresh) {
      fresh = false;
      try {
        var r = D.referrer ? new URL(D.referrer).hostname : '';
        if (r && r !== location.hostname) x.ref = r.replace(/^www\./, '');
        var sp = new URLSearchParams(location.search);
        ['utm_source', 'utm_medium', 'utm_campaign'].forEach(function (k) { var val = sp.get(k); if (val) x[k.slice(4)] = val.slice(0, 60); });
      } catch (e) {}
      x.dev = Math.min(screen.width, screen.height) < 600 ? 'phone' : 'desktop';
    }
    push('view', x); flush();
  }
  if (off) { W.trdVisit = { event: function () {}, off: true }; return; }

  /* soft navigations (assets/trd/duckpod.js uses history.pushState) */
  var ps = history.pushState;
  history.pushState = function () { var r = ps.apply(this, arguments); _setTimeout(view, 0); return r; };
  listen.call(W, 'popstate', function () { _setTimeout(view, 0); });
  listen.call(D, 'visibilitychange', function () {
    if (D.visibilityState === 'hidden') { if (shown) { visibleMs += Date.now() - shown; shown = 0; } push('hide', { p: cur, ms: visibleMs }); flush(); }
    else { shown = Date.now(); v.last = Date.now(); save(v); }
  });
  listen.call(W, 'pagehide', function () { leave(); flush(); });

  W.trdVisit = {
    event: function (name, props) { var x = { p: location.pathname, e: String(name).slice(0, 30) }; props = props || {}; if (props.platform) x.platform = String(props.platform).slice(0, 20); if (props.item) x.item = String(props.item).slice(0, 60); push('event', x); flush(); },
    queue: function () { return Q.slice(); }, room: room
  };
  view();
})();
