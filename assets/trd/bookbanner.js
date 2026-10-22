/* The Book Banner for therubberduck.net
   A full-width strip under the site header advertising The Rubber Duck's book.
   One file for the whole site: change the wording, price or link in CONFIG.
   Survives the Duck Pod's soft navigation: the same node is put back under the
   header after every body swap.
   Include once per page, in <head>, BEFORE duckpod.js:
     <link rel="stylesheet" href="/assets/trd/bookbanner.css" data-trd-keep>
     <script src="/assets/trd/bookbanner.js" data-trd-keep></script>          */
(function () {
  'use strict';

  /* ======================= CONFIG: edit here ===========================
     ON:   false switches the banner off on every page.
     URL:  where the banner goes (opens in a new tab).
     BIG:  pages that get the larger, stronger version.
     OFF:  pages that get no banner at all.                                */
  var CONFIG = {
    ON: true,
    URL: 'https://thebookofq.gumroad.com/l/egzhsa',
    LABEL: '',                             // optional tag before the kicker; empty = none
    KICKER: 'ORDER YOUR COPY',
    TITLE: 'anon mission',                 // the lead, all lowercase, exactly as Mike writes it
    OR: 'or',
    SUBTITLE: 'all you need to know about q - and how they made you afraid to ask',
    DETAIL: 'A polished, printable PDF by The Rubber Duck, for just',
    PRICE: '$19.99',
    CTA: 'Grab your copy',
    CTA_SHORT: '$19.99 \u203a',            // phones and small laptops
    BIG: /^\/merch\.html$/i,
    OFF: null,
    STORE_URL: '/merch.html',              // the header's shop sign; '' switches it off
    STORE_OFF: /^\/merch\.html$/i          // pages without the shop sign (the store itself)
  };
  /* ===================================================================== */

  var W = window, D = document;
  if (W.trdBook) return;
  /* Duck Pod drops page observers on soft navigation; recover the real constructor
     (this file loads before duckpod.js, like suggest.js). */
  var MO = W.MutationObserver;
  try { var probe = new MO(function () {}); if (probe.constructor) MO = probe.constructor; probe.disconnect(); } catch (e) {}

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

  var bar = D.createElement('aside');
  bar.id = 'trd-book';
  bar.setAttribute('aria-label', 'The Rubber Duck book: ' + CONFIG.TITLE);
  var full = CONFIG.TITLE + ' ' + CONFIG.OR + ' ' + CONFIG.SUBTITLE;
  bar.innerHTML =
    '<a class="trb-in" href="' + esc(CONFIG.URL) + '" target="_blank" rel="noopener" title="' + esc(CONFIG.KICKER.toLowerCase() + ': ' + full + '. ' + CONFIG.DETAIL + ' ' + CONFIG.PRICE + '. ' + CONFIG.CTA + '.') + '">' +
      '<span class="trb-book" aria-hidden="true">' +
        '<img class="trb-cover-img" src="/assets/trd/img/anon-mission-cover.webp" srcset="/assets/trd/img/anon-mission-cover.webp 1x, /assets/trd/img/anon-mission-cover@2x.webp 2x" alt="" width="72" height="72" decoding="async">' +
      '</span>' +
      '<span class="trb-copy">' +
        '<span class="trb-line">' +
          '<span class="trb-k">' + (CONFIG.LABEL ? '<b>' + esc(CONFIG.LABEL) + '</b>' : '') + '<span class="trb-k2">' + esc(CONFIG.KICKER) + '</span></span>' +
          '<span class="trb-t" lang="en">' + esc(CONFIG.TITLE) + '</span>' +
          '<span class="trb-p">' + esc(CONFIG.PRICE) + '</span>' +
        '</span>' +
        '<span class="trb-sub"><span class="trb-or">' + esc(CONFIG.OR) + '</span> <span class="trb-st">' + esc(CONFIG.SUBTITLE) + '</span></span>' +
        '<span class="trb-d">' + esc(CONFIG.DETAIL) + ' ' + esc(CONFIG.PRICE) + '.</span>' +
      '</span>' +
      '<span class="trb-cta"><span class="trb-cta-l">' + esc(CONFIG.CTA) + '</span><span class="trb-cta-s">' + esc(CONFIG.CTA_SHORT) + '</span></span>' +
    '</a>';

  function place() {
    var b = D.body; if (!b) return;
    var off = !CONFIG.ON || (CONFIG.OFF && CONFIG.OFF.test(location.pathname));
    if (off) { if (bar.parentNode) bar.parentNode.removeChild(bar); return; }
    bar.classList.toggle('trb-big', !!(CONFIG.BIG && CONFIG.BIG.test(location.pathname)));
    var head = null;
    for (var n = b.firstElementChild; n; n = n.nextElementSibling) {
      if (n.nodeName === 'HEADER' && n.classList.contains('banner')) { head = n; break; }
    }
    if (head) { if (head.nextElementSibling !== bar) b.insertBefore(bar, head.nextSibling); }
    else if (bar.parentNode !== b) b.insertBefore(bar, b.firstChild);
    placeSign(head);
  }

  /* ---- TRD Collectibles: one small shop sign in the header of every page (not on the store itself) ---- */
  var sign = D.createElement('a');
  sign.className = 'trd-shopsign'; sign.href = CONFIG.STORE_URL;
  sign.setAttribute('aria-label', 'Visit TRD Collectibles, the store');
  sign.innerHTML = '<span class="trd-shopsign-k" aria-hidden="true">Visit</span><span class="trd-shopsign-n" aria-hidden="true">TRD Collectibles</span>';
  function placeSign(head) {
    var inn = head && head.querySelector('.banner-in');
    var off = !CONFIG.STORE_URL || (CONFIG.STORE_OFF && CONFIG.STORE_OFF.test(location.pathname));
    if (!inn || off) { if (sign.parentNode) sign.parentNode.removeChild(sign); return; }
    if (sign.parentNode !== inn || inn.lastElementChild !== sign) inn.appendChild(sign);
  }

  /* ---- fit the title to its line: the stylesheet picks the mode per screen size
     (--trb-fit: line = size the title to the room on its line, capped at --trb-max so it stays modest,
     none = leave it to CSS) and the size range (--trb-min .. --trb-max). ---- */
  var lastW = -1, lastMode = '';
  function fit(force) {
    if (!bar.parentNode) return;
    var cs = W.getComputedStyle(bar);
    var mode = (cs.getPropertyValue('--trb-fit') || 'none').trim();
    var max = parseFloat(cs.getPropertyValue('--trb-max')) || 25;
    var min = parseFloat(cs.getPropertyValue('--trb-min')) || 13;
    var line = bar.querySelector('.trb-line'), t = bar.querySelector('.trb-t');
    if (mode !== lastMode) { bar.setAttribute('data-fit', mode); lastMode = mode; force = true; }
    if (mode !== 'line') { t.style.fontSize = ''; lastW = -1; return; }
    var w = line.clientWidth;
    if (!w || (w === lastW && !force)) return;
    lastW = w;
    var gap = parseFloat(W.getComputedStyle(line).columnGap) || 0, other = 0, n = 0;
    [].forEach.call(line.children, function (c) {
      if (c === t || W.getComputedStyle(c).display === 'none') return;
      if (Math.abs(c.offsetTop + c.offsetHeight - t.offsetTop - t.offsetHeight) > c.offsetHeight) return;   // on its own row (the store page's kicker): takes no room from the title
      other += c.getBoundingClientRect().width; n++;
    });
    t.style.fontSize = '100px';
    var nat = t.scrollWidth;
    var room = w - other - gap * n - 4;
    var size = nat ? Math.floor(100 * room / nat * 10) / 10 : max;
    t.style.fontSize = Math.max(min, Math.min(max, size)) + 'px';
  }
  var raf = W.requestAnimationFrame ? W.requestAnimationFrame.bind(W) : function (f) { return _st(f, 16); };
  var _st = W.setTimeout.bind(W), queued = false;
  function soon(force) { if (queued) return; queued = true; raf(function () { queued = false; fit(force); }); }
  var addL = EventTarget.prototype.addEventListener;

  function boot() {
    place(); fit(true);
    new MO(function () { place(); soon(true); }).observe(D.body, { childList: true });
    addL.call(W, 'resize', function () { soon(false); });
    addL.call(W, 'orientationchange', function () { soon(true); });
    if (D.fonts) { if (D.fonts.ready) D.fonts.ready.then(function () { fit(true); }); addL.call(D.fonts, 'loadingdone', function () { soon(true); }); }
    addL.call(W, 'load', function () { fit(true); });
  }
  if (D.readyState === 'loading') addL.call(D, 'DOMContentLoaded', boot); else boot();
  W.trdBook = { config: CONFIG, place: place, fit: function () { fit(true); } };
})();
