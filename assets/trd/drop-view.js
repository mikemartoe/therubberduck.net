/* Isolated drop view for therubberduck.net.
   Click a drop number anywhere it is shown and that one drop opens in its own
   floating window: number, full text, uncropped images, and the usual share row.
   Desktop: drag the title bar, resize the corner, open more than one to compare.
   Phone: one nearly full-screen window at a time.
   The address hash #view-N reopens that window. Share buttons still use
   /drops/share/N.html so the social preview card is unchanged.
   #drop-N deep links are left alone. */
(function () {
  'use strict';
  var W = window, D = document;
  if (W.trdDropView) return;

  var SITE = 'https://therubberduck.net';
  var MAX = 4966;
  var SHARE_ONLY = ['x', 'truth', 'fb', 'email', 'sms', 'link'];
  var PHRASE = /\b(?:Q\s+)?drops?\s+((?:#\d{1,4})(?:\s*(?:,|&|and)\s*#\d{1,4})*)/gi;
  var HASH = /^#view-(\d+)$/;
  var phoneQ = W.matchMedia ? W.matchMedia('(max-width: 760px)') : { matches: false };
  var wins = [];
  var z = 2147482900;
  var seq = 0;
  var map = null;
  var mapP = null;
  var scrim = null;
  var scheduled = 0;

  function phone() { return !!(phoneQ.matches); }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; });
  }
  function nthSunday(y, m, nth) {
    var dow = new Date(Date.UTC(y, m - 1, 1)).getUTCDay();
    return 1 + ((7 - dow) % 7) + 7 * (nth - 1);
  }
  function whenOf(ts) {
    var y = new Date(ts * 1000).getUTCFullYear();
    var start = Date.UTC(y, 2, nthSunday(y, 3, 2), 7) / 1000;
    var end = Date.UTC(y, 10, nthSunday(y, 11, 1), 6) / 1000;
    var off = (ts >= start && ts < end) ? -4 : -5;
    var x = new Date((ts + off * 3600) * 1000);
    var months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
    var h = x.getUTCHours(), mi = x.getUTCMinutes(), h12 = h % 12 || 12;
    return months[x.getUTCMonth()] + ' ' + x.getUTCDate() + ', ' + x.getUTCFullYear() + ', ' +
      h12 + ':' + (mi < 10 ? '0' : '') + mi + ' ' + (h < 12 ? 'AM' : 'PM') + ' ET';
  }
  function shortWhen(ts) {
    var y = new Date(ts * 1000).getUTCFullYear();
    var start = Date.UTC(y, 2, nthSunday(y, 3, 2), 7) / 1000;
    var end = Date.UTC(y, 10, nthSunday(y, 11, 1), 6) / 1000;
    var off = (ts >= start && ts < end) ? -4 : -5;
    var x = new Date((ts + off * 3600) * 1000);
    var mon = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return x.getUTCDate() + ' ' + mon[x.getUTCMonth()] + ' ' + x.getUTCFullYear();
  }
  function valid(n) { n = +n; return n >= 1 && n <= MAX && n === (n | 0); }
  function setMax(n) { if (n > MAX) { MAX = n; schedule(); } }

  function ensureCss() {
    if (D.querySelector('link[data-trd-drop-view]')) return;
    var l = D.createElement('link');
    l.rel = 'stylesheet';
    l.href = '/assets/trd/drop-view.css?v=20261112a';
    l.setAttribute('data-trd-drop-view', '');
    l.setAttribute('data-trd-keep', '');
    (D.head || D.documentElement).appendChild(l);
  }
  function hasScript(part) {
    var list = D.scripts;
    for (var i = 0; i < list.length; i++) if ((list[i].src || '').indexOf(part) !== -1) return true;
    return false;
  }
  function loadScript(src, ready) {
    if (ready()) return Promise.resolve();
    return new Promise(function (res, rej) {
      if (hasScript(src.split('?')[0])) {
        var t = setInterval(function () { if (ready()) { clearInterval(t); res(); } }, 40);
        setTimeout(function () { clearInterval(t); ready() ? res() : rej(); }, 8000);
        return;
      }
      var s = D.createElement('script');
      s.src = src;
      s.onload = function () { res(); };
      s.onerror = function () { rej(new Error(src)); };
      (D.head || D.documentElement).appendChild(s);
    });
  }
  function ensureShareCss() {
    var links = D.querySelectorAll('link[rel="stylesheet"]');
    for (var i = 0; i < links.length; i++) if ((links[i].getAttribute('href') || '').indexOf('/assets/trd/share.css') !== -1) return;
    var l = D.createElement('link');
    l.rel = 'stylesheet';
    l.href = '/assets/trd/share.css?v=20261030c';
    l.setAttribute('data-trd-keep', '');
    (D.head || D.documentElement).appendChild(l);
  }

  function indexDrops(raw) {
    var o = {}, max = MAX;
    for (var i = 0; i < raw.length; i++) {
      var r = raw[i];
      o[r[0]] = r;
      if (r[0] > max) max = r[0];
    }
    setMax(max);
    return o;
  }
  function loadMap() {
    if (map) return Promise.resolve(map);
    if (W.QDROPS) { map = indexDrops(W.QDROPS); return Promise.resolve(map); }
    if (mapP) return mapP;
    mapP = loadScript('/data/drops.js', function () { return !!W.QDROPS; }).then(function () {
      map = indexDrops(W.QDROPS || []);
      return map;
    }, function (e) { mapP = null; throw e; });
    return mapP;
  }

  function dropFromHref(href) {
    var u;
    try { u = new URL(href, location.href); } catch (e) { return 0; }
    if (u.origin !== location.origin && u.hostname !== 'therubberduck.net' && u.hostname !== 'www.therubberduck.net') return 0;
    var m = u.pathname.match(/^\/drops\/(\d+)\/?$/) || u.pathname.match(/^\/drops\/share\/(\d+)\.html$/);
    if (m && valid(+m[1])) return +m[1];
    var h = (u.hash || '').match(/^#drop-(\d+)$/);
    if (h && valid(+h[1]) && /(?:^|\/)ledger\.html$/.test(u.pathname)) return +h[1];
    if (h && valid(+h[1]) && (u.pathname === location.pathname) && /(?:^|\/)ledger\.html$/.test(location.pathname)) return +h[1];
    return 0;
  }
  function wholeLink(text, n) {
    var t = String(text || '').replace(/\s+/g, ' ').trim();
    if (!t || t.length > 80) return false;
    if (/\b(open|previous|next|ledger|page|proof|tweet)\b/i.test(t)) return false;
    if (new RegExp('^#?' + n + '$').test(t)) return true;
    if (new RegExp('^(?:Q\\s+)?drops?\\s+#' + n + '$', 'i').test(t)) return true;
    var rest = t.replace(new RegExp('^(?:Q\\s+)?drops?\\s+#' + n + '\\b', 'i'), '');
    if (rest !== t && rest.length <= 48 && !/#\d/.test(rest) && /^[,·\s]/.test(rest)) return true;
    return false;
  }

  function linkTextNode(node) {
    var s = node.nodeValue;
    if (!s || s.indexOf('#') === -1 || !/drop/i.test(s)) return;
    var p = node.parentNode;
    if (!p || !p.closest) return;
    if (p.closest('script,style,textarea,noscript,button,.shr,.dv-num,[data-dv-open]')) return;
    PHRASE.lastIndex = 0;
    var m, spans = [], guard = 0;
    while ((m = PHRASE.exec(s))) {
      if (++guard > 40) break;
      var chunk = m[1], base = m.index + m[0].length - chunk.length;
      var re = /#(\d{1,4})/g, mm;
      while ((mm = re.exec(chunk))) {
        var n = +mm[1];
        if (!valid(n)) continue;
        spans.push([base + mm.index, base + mm.index + mm[0].length, n]);
      }
      if (!m[0].length) PHRASE.lastIndex++;
    }
    if (!spans.length) return;
    var frag = D.createDocumentFragment(), last = 0;
    spans.forEach(function (sp) {
      if (sp[0] > last) frag.appendChild(D.createTextNode(s.slice(last, sp[0])));
      var b = D.createElement('button');
      b.type = 'button';
      b.className = 'dv-num';
      b.setAttribute('data-dv-open', String(sp[2]));
      b.textContent = s.slice(sp[0], sp[1]);
      b.setAttribute('aria-label', 'Open Q drop ' + sp[2] + ' on its own');
      frag.appendChild(b);
      last = sp[1];
    });
    if (last < s.length) frag.appendChild(D.createTextNode(s.slice(last)));
    p.replaceChild(frag, node);
  }
  function walk(root) {
    if (!root || root.nodeType !== 1) return;
    var w = D.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: function (n) {
        if (!n.nodeValue || n.nodeValue.indexOf('#') === -1) return NodeFilter.FILTER_REJECT;
        var parent = n.parentNode;
        if (!parent || !parent.closest) return NodeFilter.FILTER_REJECT;
        if (parent.closest('script,style,textarea,noscript,.shr')) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    }), nodes = [], n;
    while ((n = w.nextNode())) nodes.push(n);
    nodes.forEach(linkTextNode);
  }
  function markLinks(root) {
    if (!root || !root.querySelectorAll) return;
    var as = root.querySelectorAll('a[href]');
    for (var i = 0; i < as.length; i++) {
      var a = as[i];
      if (a.hasAttribute('data-dv-ready') || a.closest('.shr')) continue;
      var n = dropFromHref(a.getAttribute('href'));
      if (!n) { a.setAttribute('data-dv-ready', ''); continue; }
      a.setAttribute('data-dv-ready', '');
      if (wholeLink(a.textContent, n)) {
        a.setAttribute('data-dv-open', String(n));
        a.classList.add('dv-hit');
        if (!a.getAttribute('aria-label')) a.setAttribute('aria-label', 'Open Q drop ' + n + ' on its own');
      }
    }
  }
  /* "Q drop #35" is sometimes split so the number is its own link (the X archive
     turns #35 into a hashtag). If the number sits right after "drop", it is that drop. */
  function precededByDrop(a) {
    var prev = a.previousSibling, text = '';
    while (prev && text.length < 40) {
      if (prev.nodeType === 3) text = prev.nodeValue + text;
      else if (prev.nodeType === 1 && prev.getAttribute && prev.getAttribute('data-dv-open')) {
        return /^\s*(?:,|&|and)\s*$/i.test(text);
      } else break;
      if (/\b(?:Q\s+)?drops?\s*$/i.test(text)) return true;
      prev = prev.previousSibling;
    }
    return /\b(?:Q\s+)?drops?\s*$/i.test(text);
  }
  function markDropHashes(root) {
    if (!root.querySelectorAll) return;
    var as = root.querySelectorAll('a');
    for (var i = 0; i < as.length; i++) {
      var a = as[i];
      if (a.hasAttribute('data-dv-open') || a.closest('.shr')) continue;
      var m = String(a.textContent || '').replace(/\s+/g, '').match(/^#(\d{1,4})$/);
      if (!m || !valid(+m[1]) || !precededByDrop(a)) continue;
      a.setAttribute('data-dv-open', m[1]);
      a.classList.add('dv-hit');
      if (!a.getAttribute('aria-label')) a.setAttribute('aria-label', 'Open Q drop ' + m[1] + ' on its own');
    }
  }
  function enhance(root) {
    if (!root || root.nodeType !== 1) return;
    markLinks(root);
    walk(root);
    markDropHashes(root);
  }
  function schedule() {
    if (scheduled) return;
    scheduled = W.requestAnimationFrame(function () {
      scheduled = 0;
      if (D.body) enhance(D.body);
    });
  }

  function textHTML(s) {
    return String(s || '').split('\n').map(function (line) {
      var h = esc(line);
      return /^&gt;/.test(h) ? '<span class="dv-gt">' + h + '</span>' : h;
    }).join('\n');
  }
  function viewHref(n) { return SITE + '/#view-' + n; }
  function setHash(n) {
    var next = '#view-' + n;
    if (location.hash === next) return;
    try { history.replaceState(history.state, '', location.pathname + location.search + next); } catch (e) {}
  }
  function clearHash() {
    if (!HASH.test(location.hash || '')) return;
    try { history.replaceState(history.state, '', location.pathname + location.search); } catch (e) {}
  }
  function topWin() {
    var best = null;
    wins.forEach(function (w) { if (!best || w._z > best._z) best = w; });
    return best;
  }
  function raise(win) {
    win._z = ++z;
    win.style.zIndex = String(win._z);
    wins.forEach(function (w) { w.classList.toggle('dv-front', w === win); });
    setHash(win._n);
  }
  function place(win) {
    if (phone()) return;
    var i = seq++ % 6;
    var w = Math.min(480, Math.max(300, W.innerWidth - 48));
    var h = Math.min(640, Math.max(280, W.innerHeight - 64));
    win.style.width = w + 'px';
    win.style.height = h + 'px';
    win.style.left = Math.max(12, Math.round((W.innerWidth - w) / 2 - 70 + i * 26)) + 'px';
    win.style.top = Math.max(12, 36 + (i % 4) * 22) + 'px';
  }
  function ensureScrim() {
    if (scrim) return scrim;
    scrim = D.createElement('div');
    scrim.className = 'dv-scrim';
    scrim.hidden = true;
    scrim.addEventListener('click', function () { if (phone()) closeAll(); });
    (D.documentElement || D.body).appendChild(scrim);
    return scrim;
  }
  function syncScrim() {
    if (!scrim) return;
    scrim.hidden = !(phone() && wins.length);
  }
  function close(win) {
    var i = wins.indexOf(win);
    if (i < 0) return;
    wins.splice(i, 1);
    win.remove();
    syncScrim();
    var next = topWin();
    if (next) setHash(next._n);
    else clearHash();
    if (win._back && win._back.focus) { try { win._back.focus({ preventScroll: true }); } catch (e) {} }
  }
  function closeAll() {
    wins.slice().forEach(close);
  }
  function findWin(n) {
    for (var i = 0; i < wins.length; i++) if (wins[i]._n === n) return wins[i];
    return null;
  }

  function shareRow(host, n, rec) {
    ensureShareCss();
    var jobs = [
      loadScript('/assets/trd/share.js?v=20261030c', function () { return !!W.trdShare; }),
      loadScript('/data/drop-cards.js', function () { return !!W.TRD_DROP_CARDS; }).catch(function () {})
    ];
    Promise.all(jobs).then(function () {
      if (!host.isConnected || !W.trdShare) {
        host.innerHTML = '<p class="dv-url"><a href="' + esc(SITE + '/drops/share/' + n + '.html') + '">Share page for Q drop #' + n + '</a></p>';
        return;
      }
      var C = W.TRD_DROP_CARDS || { base: 'https://memes.therubberduck.net/drops/', long: [], v2: [], v2base: 'https://memes.therubberduck.net/drops/v2/' };
      var B = (C.v2 && C.v2.indexOf(n) > -1) ? C.v2base : C.base;
      var when = rec ? shortWhen(rec[1]) : '';
      host.innerHTML = '';
      host.appendChild(W.trdShare.build({
        kind: 'drop', id: String(n),
        page: SITE + '/drops/share/' + n + '.html',
        text: 'Q drop #' + n + (when ? ' \u00b7 ' + when : ''),
        thumb: B + 'og/' + n + '.jpg',
        file: B + 'card/' + n + '.png',
        igFile: (C.long && C.long.indexOf(n) > -1) ? (B + 'ig/' + n + '.png') : null,
        fileName: 'q-drop-' + n + '.png',
        compact: true, only: SHARE_ONLY,
        groupLabel: 'Share Q drop #' + n
      }));
      var p = D.createElement('p');
      p.className = 'dv-url';
      p.innerHTML = 'View link <a href="' + esc(viewHref(n)) + '">therubberduck.net/#view-' + n + '</a>' +
        ' · <a href="/drops/' + n + '/">Drop page</a>';
      host.appendChild(p);
    }, function () {
      host.innerHTML = '<p class="dv-url"><a href="' + esc(SITE + '/drops/share/' + n + '.html') + '">Share page for Q drop #' + n + '</a></p>';
    });
  }
  function imagesHTML(n) {
    var DI = W.TRD_DROP_IMAGES;
    var a = DI && DI.d && (DI.d[n] || DI.d[String(n)]);
    if (!a || !a.length) return '';
    return '<div class="dv-imgs">' + a.map(function (im, i) {
      var alt = 'Image ' + (i + 1) + ' attached to Q drop #' + n;
      return '<img src="' + esc(DI.base + im.src) + '" width="' + im.w + '" height="' + im.h + '" alt="' + esc(alt) + '" decoding="async">';
    }).join('') + '</div>';
  }
  function fill(win, rec) {
    var n = win._n, body = win.querySelector('.dv-body');
    var when = rec ? whenOf(rec[1]) : '';
    var text = rec ? (rec[5] || '') : '';
    body.innerHTML =
      (when ? '<p class="dv-when">' + esc(when) + '</p>' : '') +
      (text ? '<div class="dv-text">' + textHTML(text) + '</div>' : '<p class="dv-empty">No body text in the capture — an image-only post.</p>') +
      '<div class="dv-pics"></div><div class="dv-share"></div>';
    enhance(body.querySelector('.dv-text'));
    var pics = body.querySelector('.dv-pics');
    loadScript('/data/drop-images.js', function () { return !!W.TRD_DROP_IMAGES; }).then(function () {
      if (!pics.isConnected) return;
      pics.innerHTML = imagesHTML(n);
    }, function () {});
    shareRow(body.querySelector('.dv-share'), n, rec);
  }
  function drag(win, bar) {
    bar.addEventListener('pointerdown', function (e) {
      if (phone() || e.button !== 0 || (e.target.closest && e.target.closest('button,a'))) return;
      raise(win);
      var r = win.getBoundingClientRect();
      var dx = e.clientX - r.left, dy = e.clientY - r.top;
      win.style.left = r.left + 'px';
      win.style.top = r.top + 'px';
      win.style.right = 'auto';
      win.style.bottom = 'auto';
      function move(ev) {
        var x = Math.max(0, Math.min(W.innerWidth - 80, ev.clientX - dx));
        var y = Math.max(0, Math.min(W.innerHeight - 40, ev.clientY - dy));
        win.style.left = x + 'px';
        win.style.top = y + 'px';
      }
      function up() {
        bar.removeEventListener('pointermove', move);
        bar.removeEventListener('pointerup', up);
        bar.removeEventListener('pointercancel', up);
      }
      bar.addEventListener('pointermove', move);
      bar.addEventListener('pointerup', up);
      bar.addEventListener('pointercancel', up);
      try { bar.setPointerCapture(e.pointerId); } catch (err) {}
    });
  }
  function open(n, opt) {
    n = +n;
    opt = opt || {};
    if (!valid(n) && !(n >= 1 && n <= 9999)) return null;
    ensureCss();
    var have = findWin(n);
    if (have) { raise(have); if (!phone()) have.querySelector('.dv-x').focus(); return have; }
    if (phone()) closeAll();
    var back = D.activeElement;
    var id = 'dv-t-' + n + '-' + (++seq);
    var win = D.createElement('div');
    win.className = 'dv-win';
    win.setAttribute('role', 'dialog');
    win.setAttribute('aria-modal', phone() ? 'true' : 'false');
    win.setAttribute('aria-labelledby', id);
    win._n = n;
    win._back = back && back.nodeType === 1 ? back : null;
    win.innerHTML =
      '<div class="dv-bar">' +
        '<h2 class="dv-n" id="' + id + '" tabindex="0"><span>#</span>' + n + '</h2>' +
        '<button type="button" class="dv-x" aria-label="Close">\u00d7</button>' +
      '</div>' +
      '<div class="dv-body"><p class="dv-msg">Opening drop #' + n + '\u2026</p></div>';
    ensureScrim();
    (D.documentElement || D.body).appendChild(win);
    wins.push(win);
    place(win);
    raise(win);
    syncScrim();
    drag(win, win.querySelector('.dv-bar'));
    win.addEventListener('pointerdown', function () { raise(win); });
    win.querySelector('.dv-x').addEventListener('click', function () { close(win); });
    win.querySelector('.dv-x').focus();
    loadMap().then(function (all) {
      if (!win.isConnected) return;
      var rec = all[n];
      if (!rec) {
        win.querySelector('.dv-body').innerHTML = '<p class="dv-empty">No drop #' + n + ' in the archive.</p>';
        return;
      }
      fill(win, rec);
    }, function () {
      if (win.isConnected) win.querySelector('.dv-body').innerHTML = '<p class="dv-empty">The drop could not be loaded. Try the <a href="/drops/' + n + '/">drop page</a>.</p>';
    });
    return win;
  }

  function onClick(e) {
    if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    var t = e.target && e.target.closest && e.target.closest('[data-dv-open]');
    if (!t || t.closest('.shr')) return;
    var n = +t.getAttribute('data-dv-open');
    if (!n) return;
    e.preventDefault();
    e.stopPropagation();
    if (e.stopImmediatePropagation) e.stopImmediatePropagation();
    open(n);
  }
  D.addEventListener('click', onClick, true);
  D.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      var top = topWin();
      if (!top) return;
      e.preventDefault();
      e.stopPropagation();
      close(top);
      return;
    }
    if (e.key !== 'Enter' && e.key !== ' ') return;
    var t = e.target && e.target.closest && e.target.closest('[data-dv-open]');
    if (!t || t.tagName === 'A' || t.tagName === 'BUTTON') return;
    e.preventDefault();
    open(+t.getAttribute('data-dv-open'));
  }, true);

  function fromHash() {
    var m = (location.hash || '').match(HASH);
    if (m) open(+m[1], { fromHash: true });
  }
  W.addEventListener('hashchange', fromHash);

  function boot() {
    ensureCss();
    if (D.body) enhance(D.body);
    fromHash();
    var MO = W.MutationObserver;
    if (!MO || !D.body) return;
    if (phoneQ.addEventListener) phoneQ.addEventListener('change', function () {
      if (phone() && wins.length > 1) {
        var keep = topWin();
        wins.slice().forEach(function (w) { if (w !== keep) close(w); });
      }
      syncScrim();
    });
    var pending = false;
    new MO(function () {
      if (pending) return;
      pending = true;
      W.requestAnimationFrame(function () { pending = false; if (D.body) enhance(D.body); });
    }).observe(D.body, { childList: true, subtree: true });
  }
  if (D.readyState === 'loading') D.addEventListener('DOMContentLoaded', boot); else boot();

  W.trdDropView = { open: open, close: close, closeAll: closeAll, enhance: enhance };
})();
