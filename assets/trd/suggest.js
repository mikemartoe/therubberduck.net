/* The Suggestion Box for therubberduck.net
   A wooden box at the foot of every page (and a small hand-painted suggestion box beside the support duck, bottom-right).
   Clicking it opens a typed index card; on send the card drops into the slot.
   Survives the Duck Pod's soft navigation: the same nodes are put back after
   every body swap, so a half-written card is never lost.
   Include once per page, in <head>, BEFORE duckpod.js:
     <link rel="stylesheet" href="/assets/trd/suggest.css" data-trd-keep>
     <script src="/assets/trd/suggest.js" data-trd-keep></script>             */
(function () {
  'use strict';

  /* ======================= CONFIG: edit here ===========================
     ENDPOINT: where cards are posted (FormSubmit.co, free, no account).
       NEEDS ONE-TIME ACTIVATION. The first card ever sent from the live site
       makes FormSubmit email therubberduk@gmail.com an "Activate Form" link.
       Click it once; cards sent before that are delivered after activation.
       Optional, after activation: FormSubmit's email also gives a random
       string. Swap it in for the address below to keep the address out of
       the page source:  'https://formsubmit.co/ajax/<random-string>'
       (FormSubmit treats that as a new form, so it may ask to activate once more.)
     Set ENDPOINT to '' to switch sending off (the card says the box is closed).
     SHOW_TAB: the "Suggestions" opener, a small hand-painted suggestion box beside the support duck
       on every page and at every width (never taller than the duck; a little smaller on phones).
       The box takes the bottom-right corner and the duck steps left of it at every width.
       If the album player is in the way the box stands above the duck instead.  */
  var CONFIG = {
    ENDPOINT: 'https://formsubmit.co/ajax/therubberduk@gmail.com',
    SUBJECT: 'Suggestion Box: therubberduck.net',
    SHOW_TAB: true
  };
  /* ===================================================================== */

  var W = window, D = document;
  if (W.trdSuggest) return;
  if (typeof W.TRD_SUGGEST_ENDPOINT === 'string') CONFIG.ENDPOINT = W.TRD_SUGGEST_ENDPOINT;   // test hook

  /* Duck Pod sandboxes page listeners/timers/observers and drops them on soft
     navigation. These must outlive every page, so use untouched originals:
     EventTarget.prototype is never patched, the observer's real constructor is
     recovered from an instance, and setTimeout is captured before duckpod.js
     loads (keep this script above it in <head>). */
  var addL = EventTarget.prototype.addEventListener;
  function on(t, type, fn, o) { addL.call(t, type, fn, o); }
  var MO = W.MutationObserver;
  try { var probe = new MO(function () {}); if (probe.constructor) MO = probe.constructor; probe.disconnect(); } catch (e) {}
  var reduce = W.matchMedia ? W.matchMedia('(prefers-reduced-motion: reduce)') : { matches: false };
  var _st = W.setTimeout.bind(W);   // captured before duckpod.js patches it (this file loads first)
  function wait(ms) { return new Promise(function (r) { _st(r, ms); }); }
  var RO = W.ResizeObserver || null;                                // originals, captured before duckpod.js wraps them
  var _raf = W.requestAnimationFrame ? W.requestAnimationFrame.bind(W) : function (f) { return _st(f, 16); };

  /* ================= the box, drawn ================= */
  var uidN = 0;
  function boxSVG(withPeek) {
    var u = 'trs' + (++uidN);
    var peek = withPeek
      ? '<g class="trs-peek"><rect x="93" y="13" width="54" height="22" rx="1.5" fill="#F4ECD6"/>' +
        '<rect x="93" y="17" width="54" height="1.3" fill="#C0281E"/><rect x="98" y="22.5" width="40" height=".8" fill="#A9BDD3"/>' +
        '<rect x="98" y="27.5" width="34" height=".8" fill="#A9BDD3"/></g>'
      : '';
    return '<svg viewBox="0 0 240 192" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false">' +
      '<defs>' +
        '<linearGradient id="' + u + 'w" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5E2615"/><stop offset="1" stop-color="#3A140A"/></linearGradient>' +
        '<linearGradient id="' + u + 't" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5A2414"/><stop offset="1" stop-color="#7E3822"/></linearGradient>' +
        '<linearGradient id="' + u + 'm" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8A4128"/><stop offset=".25" stop-color="#6A2A17"/><stop offset="1" stop-color="#3E160B"/></linearGradient>' +
        '<linearGradient id="' + u + 'p" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4A1A0D"/><stop offset="1" stop-color="#220A05"/></linearGradient>' +
        '<linearGradient id="' + u + 'b" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F6DC93"/><stop offset=".35" stop-color="#D2A24A"/><stop offset=".62" stop-color="#9C6B25"/><stop offset=".85" stop-color="#E5BF68"/><stop offset="1" stop-color="#B8852F"/></linearGradient>' +
        '<filter id="' + u + 'g" x="0" y="0" width="100%" height="100%">' +
          '<feTurbulence type="fractalNoise" baseFrequency="0.006 0.24" numOctaves="3" seed="11" result="n"/>' +
          '<feColorMatrix in="n" type="matrix" values="0 0 0 0 .06  0 0 0 0 .02  0 0 0 0 .01  1.9 0 0 0 -.72" result="s"/>' +
          '<feComposite in="s" in2="SourceGraphic" operator="in" result="c"/>' +
          '<feMerge><feMergeNode in="SourceGraphic"/><feMergeNode in="c"/></feMerge>' +
        '</filter>' +
        '<radialGradient id="' + u + 'h" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#000" stop-opacity=".6"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>' +
      '</defs>' +
      '<ellipse cx="120" cy="186" rx="118" ry="6" fill="url(#' + u + 'h)"/>' +
      /* plinth */
      '<rect x="5" y="164" width="230" height="20" rx="2" fill="url(#' + u + 'p)" filter="url(#' + u + 'g)"/>' +
      '<rect x="5" y="164" width="230" height="1.5" fill="#8A4128" opacity=".7"/>' +
      /* body */
      '<rect x="15" y="56" width="210" height="109" fill="url(#' + u + 'w)" filter="url(#' + u + 'g)"/>' +
      '<rect x="27" y="68" width="186" height="85" rx="2" fill="none" stroke="#000" stroke-opacity=".55" stroke-width="2"/>' +
      '<rect x="28.5" y="69.5" width="184" height="83" rx="2" fill="none" stroke="#FFBE96" stroke-opacity=".16" stroke-width="1"/>' +
      /* lid: top face, slot, molding */
      '<path d="M25 20H215L235 47H5Z" fill="url(#' + u + 't)" filter="url(#' + u + 'g)"/>' +
      '<path d="M25 20H215" stroke="#000" stroke-opacity=".5"/>' +
      '<rect x="56" y="26" width="128" height="15" rx="7.5" fill="url(#' + u + 'b)"/>' +
      '<rect x="57.5" y="27.5" width="125" height="12" rx="6" fill="none" stroke="#5a3a10" stroke-opacity=".6"/>' +
      '<rect class="trs-slot" x="63" y="30" width="114" height="7" rx="3.5" fill="#050505"/>' +
      peek +
      '<rect x="63" y="34.2" width="114" height="2.8" rx="1.4" fill="#050505"/>' +
      '<rect x="2" y="46" width="236" height="12" rx="2" fill="url(#' + u + 'm)"/>' +
      '<rect x="2" y="57" width="236" height="1.5" fill="#1E0904"/>' +
      /* brass corner guards */
      '<path d="M15 150v15h15v-3H18v-12Z" fill="url(#' + u + 'b)"/><path d="M225 150v15h-15v-3h12v-12Z" fill="url(#' + u + 'b)"/>' +
      '<path d="M15 71V58h13v3H18v10Z" fill="url(#' + u + 'b)"/><path d="M225 71V58h-13v3h10v10Z" fill="url(#' + u + 'b)"/>' +
      /* the plate */
      '<rect x="44" y="88" width="152" height="32" rx="3" fill="url(#' + u + 'b)"/>' +
      '<rect x="44" y="88" width="152" height="32" rx="3" fill="none" stroke="#3a2408" stroke-opacity=".55"/>' +
      '<rect x="48" y="92" width="144" height="24" rx="1.5" fill="none" stroke="#6b4a14" stroke-opacity=".55" stroke-width=".8"/>' +
      '<g fill="#7a5418"><circle cx="49.5" cy="104" r="2"/><circle cx="190.5" cy="104" r="2"/></g>' +
      '<g stroke="#FCEBB5" stroke-width=".6" stroke-opacity=".8"><path d="M48.3 104h2.4M189.3 104h2.4"/></g>' +
      '<text x="120" y="109.2" text-anchor="middle" textLength="122" lengthAdjust="spacingAndGlyphs" font-family="\'TRS Cinzel\',Cinzel,\'Times New Roman\',serif" font-weight="700" font-size="13.2" fill="#FFF0C2" fill-opacity=".55">SUGGESTION BOX</text>' +
      '<text x="120" y="108.4" text-anchor="middle" textLength="122" lengthAdjust="spacingAndGlyphs" font-family="\'TRS Cinzel\',Cinzel,\'Times New Roman\',serif" font-weight="700" font-size="13.2" fill="#3A2408">SUGGESTION BOX</text>' +
      /* keyhole */
      '<circle cx="120" cy="138" r="6.5" fill="url(#' + u + 'b)"/><circle cx="120" cy="136.6" r="1.9" fill="#120603"/><path d="M118.9 137.5h2.2l.7 4h-3.6Z" fill="#120603"/>' +
    '</svg>';
  }

  /* ================= nodes ================= */
  function el(tag, cls, html) { var n = D.createElement(tag); if (cls) n.className = cls; if (html != null) n.innerHTML = html; return n; }
  function today() {
    var m = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'], d = new Date();
    return d.getDate() + ' ' + m[d.getMonth()] + ' ' + d.getFullYear();
  }

  var sec = el('section', '');
  sec.id = 'trd-suggest';
  sec.setAttribute('aria-label', 'Suggestion box');
  sec.innerHTML =
    '<button class="trs-open" type="button" aria-haspopup="dialog">' +
      '<span class="trs-art">' + boxSVG(true) + '</span>' +
      '<span class="trs-copy">' +
        '<span class="trs-eyebrow">Suggestions welcome</span>' +
        '<span class="trs-h">Got an idea for the site?</span>' +
        '<span class="trs-p">Write it on a card and drop it in the slot.</span>' +
        '<span class="trs-cta">Fill out a card</span>' +
      '</span>' +
    '</button>';

  var fx = el('div', '');
  fx.id = 'trd-suggest-fx';
  fx.innerHTML = '<button class="trs-tab" type="button" aria-haspopup="dialog" aria-label="Suggestions: open the suggestion box" title="Suggestions">' +
    '<img src="/assets/trd/img/suggestion-box-trd.webp" srcset="/assets/trd/img/suggestion-box-trd.webp 1x, /assets/trd/img/suggestion-box-trd@2x.webp 2x" alt="" width="176" height="240" decoding="async" draggable="false">' +
    '<span class="trs-tip" aria-hidden="true">Suggestions</span></button>';
  try { if (!sessionStorage.getItem('trs-hello')) { fx.classList.add('trs-hello'); sessionStorage.setItem('trs-hello', '1'); } } catch (e) { fx.classList.add('trs-hello'); }

  var dlg = el('dialog', 'trs-dlg');
  dlg.setAttribute('aria-labelledby', 'trs-title');
  dlg.innerHTML =
    '<div class="trs-stage"><div class="trs-inner">' +
      '<button class="trs-x" type="button">Close</button>' +
      '<div class="trs-wrap">' +
        '<form class="trs-card trs-form" novalidate>' +
          '<div class="trs-head"><h2 class="trs-title" id="trs-title">Suggestion</h2><span class="trs-date"></span></div>' +
          '<p class="trs-to">To: The Rubber Duck. Ideas, fixes, requests.</p>' +
          '<label class="trs-f"><span class="trs-l">Your suggestion <em class="trs-req">(required)</em></span>' +
            '<textarea name="suggestion" maxlength="3000" required aria-required="true" aria-describedby="trs-msg"></textarea></label>' +
          '<div class="trs-row">' +
            '<label class="trs-f"><span class="trs-l">Name <em>(optional)</em></span><input name="name" type="text" maxlength="80" autocomplete="name"></label>' +
            '<label class="trs-f"><span class="trs-l">Email <em>(for a reply)</em></span><input name="email" type="email" maxlength="120" autocomplete="email" inputmode="email"></label>' +
          '</div>' +
          '<label class="trs-hp" aria-hidden="true">Leave this empty<input name="_honey" type="text" tabindex="-1" autocomplete="off"></label>' +
          '<p class="trs-msg" id="trs-msg" role="alert"></p>' +
          '<div class="trs-foot"><p class="trs-note">Email is optional and only used to reply.</p>' +
            '<button class="trs-btn trs-send" type="submit">Drop it in the box</button></div>' +
        '</form>' +
        '<div class="trs-card trs-thanks" hidden>' +
          '<div class="trs-stamp">Received</div>' +
          '<p class="trs-ty"><span class="trs-tyv" aria-hidden="true"></span><span class="trs-caret" aria-hidden="true"></span><span class="trs-sr" role="status"></span></p>' +
          '<p class="trs-ty2"></p>' +
          '<div class="trs-acts"><button class="trs-btn trs-ghost trs-again" type="button">Write another</button><button class="trs-btn trs-done" type="button">Close</button></div>' +
        '</div>' +
      '</div>' +
      '<div class="trs-art">' + boxSVG(false) + '</div>' +
    '</div></div>';

  function q(s, r) { return (r || dlg).querySelector(s); }
  var form = q('.trs-form'), thanks = q('.trs-thanks'), msg = q('.trs-msg'), send = q('.trs-send');
  var ta = form.elements.suggestion, inName = form.elements.name, inEmail = form.elements.email, hp = form.elements._honey;
  var dlgArt = q('.trs-inner > .trs-art'), slot = q('.trs-slot', dlgArt), busy = false, opener = null;

  /* ================= placement + soft-navigation survival ================= */
  function place() {
    corner();
    var b = D.body; if (!b) return;
    var pod = D.getElementById('trd-pod'), ref = pod && pod.parentNode === b ? pod : null;
    sec.classList.toggle('trs-nopod', !ref);
    fx.classList.toggle('trs-tab-off', !CONFIG.SHOW_TAB);
    if (sec.parentNode !== b) { if (dlg.open) resetAfterNav(); b.insertBefore(sec, ref); }
    if (fx.parentNode !== b) b.insertBefore(fx, ref);
    if (dlg.parentNode !== b) b.insertBefore(dlg, ref);
    fit();
  }

  /* ================= the box opener: beside the duck, clear of the player, its hint and the duck ================= */
  var tab = q('.trs-tab', fx), fitQ = false, watched = [], ro = null, mo = null;
  var wide = W.matchMedia ? W.matchMedia('(min-width: 481px)') : { matches: true };     // breakpoint for duck step distance (CSS); box stays right of duck either way
  function corner() {                                               // Duck Pod's soft navigation copies the new page's <html> class, so this is re-applied
    var h = D.documentElement, want = !!CONFIG.SHOW_TAB;
    if (h.classList.contains('trs-box-r') !== want) h.classList.toggle('trs-box-r', want);
  }
  corner();                                                         // before first paint, so the duck never jumps
  function vis(n) {
    if (!n || !n.isConnected) return null;
    var cs = W.getComputedStyle(n); if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) return null;
    var r = n.getBoundingClientRect(); return r.width && r.height ? r : null;
  }
  function obstacles() {
    var out = [], dock = D.querySelector('#trd-pod .tp-dock'), hint = dock && dock.classList.contains('tp-hinting') && dock.querySelector('.tp-hint');
    [dock, hint].forEach(function (n) { var r = vis(n); if (r) out.push({ r: r, g: 10 }); });
    var duck = D.querySelector('.trd-sup-duck'), dr = vis(duck);
    if (dr) out.push({ r: duckBox(duck) || dr, g: 4 });
    return out;
  }
  /* the duck's resting box: its wiggle and hover rotate it, so measure the layout, not the transformed rect */
  function duckBox(duck) {
    var sup = D.getElementById('trdSup'), sr = vis(sup);
    if (!sr || duck.parentNode !== sup) return null;
    return { left: sr.right - duck.offsetWidth, right: sr.right, top: sr.bottom - duck.offsetHeight, bottom: sr.bottom };
  }
  function watch() {                                                // re-measure when the player or the duck changes size, view or place
    var want = [D.getElementById('trd-pod'), D.querySelector('#trd-pod .tp-dock'), D.getElementById('trdSup')].filter(Boolean);
    if (want.length === watched.length && want.every(function (n, i) { return n === watched[i]; })) return;
    watched = want;
    if (mo) mo.disconnect(); if (ro) ro.disconnect();
    mo = new MO(fit); ro = RO ? new RO(fit) : null;
    want.forEach(function (n) {
      mo.observe(n, { attributes: true, attributeFilter: ['class', 'style', 'data-view', 'hidden'] });
      if (ro) ro.observe(n.id === 'trd-pod' ? (n.querySelector('.tp-dock') || n) : n);
    });
  }
  function hits(b, obs) {
    for (var i = 0; i < obs.length; i++) {
      var o = obs[i].r, g = obs[i].g;
      if (b.right + g > o.left && b.left - g < o.right && b.bottom + g > o.top && b.top - g < o.bottom) return o;
    }
    return null;
  }
  function fit() { if (!fitQ) { fitQ = true; _raf(fitNow); } }
  function fitNow() {
    fitQ = false;
    if (!fx.isConnected) return;
    tab.setAttribute('title', 'Suggestions');
    watch();
    var sup = D.getElementById('trdSup'), duck = D.querySelector('.trd-sup-duck');
    fx.classList.toggle('trs-behind', !!(sup && !sup.hidden && sup.classList.contains('open')));
    var w = tab.offsetWidth, h = tab.offsetHeight; if (!w || !h) return;
    /* phones: suggestion box top-left in the black header band; duck stays top-right via CSS */
    if (W.matchMedia && W.matchMedia('(max-width: 480px)').matches) {
      fx.style.setProperty('--trs-l', '8px');
      fx.style.setProperty('--trs-t', '10px');
      fx.style.removeProperty('--trs-r');
      fx.style.removeProperty('--trs-b');
      fx.style.setProperty('--trs-lift', '0px');
      return;
    }
    /* where the fixed layer's right and bottom edges are, in client coordinates */
    var cw = D.documentElement.clientWidth, ch = W.innerHeight, sr = vis(sup), dr = duck && vis(duck) && sr ? duckBox(duck) : null;
    var cands = [];
    if (dr) {
      var scs = W.getComputedStyle(sup), offR = parseFloat(scs.right) || 0, offB = parseFloat(scs.bottom) || 0;
      cw = sr.right + offR; ch = sr.bottom + offB;
      /* stand on the duck's baseline: the bottom of its image (object-fit: contain inside the padded button) */
      var img = duck.querySelector('img'), dcs = W.getComputedStyle(duck), base = offB + (parseFloat(dcs.paddingBottom) || 0);
      if (img && img.naturalWidth && img.clientWidth) {
        var ih = Math.min(img.clientHeight, img.clientWidth * img.naturalHeight / img.naturalWidth);
        base += (img.clientHeight - ih) / 2 + ih * 0.03;                       // the duck's rounded base sits ~3% above its picture's edge
      }
      var dw = duck.offsetWidth, dh = duck.offsetHeight;
      if (D.documentElement.classList.contains('trs-box-r')) {
        cands.push({ r: Math.max(0, offR - w - 8), b: base });                    // corner, right of the (moved) duck, same baseline
      } else {
        cands.push({ r: offR + dw + 10, b: base });                               // no corner claim: just left of the duck
      }
      cands.push({ r: offR + Math.round((dw - w) / 2), b: offB + dh + 8 });          // the player is in the way: stand on top of the duck
    } else {
      cands.push({ r: 14, b: 14 });                                               // no duck: the corner
    }
    var obs = obstacles(), pick = null, best = null;
    cands.forEach(function (c) {
      if (pick) return;
      var box = { left: cw - c.r - w, right: cw - c.r, top: ch - c.b - h, bottom: ch - c.b }, lift = 0;
      for (var pass = 0; pass < 6; pass++) {                       // step above whatever it would touch
        var o = hits(box, obs); if (!o) break;
        var gg = 10, d = box.bottom + gg - o.top; lift += d; box.top -= d; box.bottom -= d;
      }
      if (box.top < 8) lift = Math.max(0, lift - (8 - box.top));    // never push it off the top
      c.lift = lift;
      if (!lift) pick = c; else if (!best || lift < best.lift) best = c;
    });
    pick = pick || best || cands[0];                               // a clear spot wins; otherwise the smallest lift
    fx.style.setProperty('--trs-r', Math.round(pick.r) + 'px');
    fx.style.setProperty('--trs-b', Math.round(pick.b) + 'px');
    fx.style.setProperty('--trs-lift', Math.round(pick.lift || 0) + 'px');
    fx.style.removeProperty('--trs-l');
    fx.style.removeProperty('--trs-t');
  }
  on(W, 'resize', fit);
  try { on(wide, 'change', fit); } catch (e) {}
  if (W.visualViewport) { on(W.visualViewport, 'resize', fit); on(W.visualViewport, 'scroll', fit); }
  on(W, 'load', fit);
  _st(fit, 400); _st(fit, 1500);
  _st(function () { fx.classList.remove('trs-hello'); }, 4000);     // the first-load glow runs once, then never again
  function resetAfterNav() { try { dlg.close(); } catch (e) {} D.documentElement.classList.remove('trs-lock'); }
  function boot() {
    corner();
    place();
    new MO(function () { place(); }).observe(D.body, { childList: true });
    new MO(function () { corner(); fit(); }).observe(D.documentElement, { attributes: true, attributeFilter: ['class'] });
  }

  /* ================= open / close ================= */
  function freshCard() {
    busy = false; send.disabled = false; send.textContent = 'Drop it in the box';
    form.hidden = false; thanks.hidden = true; msg.textContent = '';
    form.style.visibility = ''; dlgArt.style.transform = '';
    [].forEach.call(form.querySelectorAll('[aria-invalid]'), function (n) { n.removeAttribute('aria-invalid'); });
  }
  function open(e) {
    opener = e && e.currentTarget || null;
    if (!thanks.hidden) { form.reset(); freshCard(); }
    q('.trs-date').textContent = today();
    if (!dlg.open) { try { dlg.showModal(); } catch (x) { dlg.setAttribute('open', ''); } }
    D.documentElement.classList.add('trs-lock');
    try { ta.focus({ preventScroll: true }); } catch (x) { ta.focus(); }
  }
  function close() {
    if (busy) return;
    if (dlg.open) { try { dlg.close(); } catch (x) { dlg.removeAttribute('open'); } }
  }
  on(dlg, 'close', function () {
    D.documentElement.classList.remove('trs-lock');
    if (!thanks.hidden) { form.reset(); freshCard(); }
    if (opener && opener.isConnected) { try { opener.focus({ preventScroll: true }); } catch (x) {} }
  });
  on(dlg, 'cancel', function (e) { if (busy) e.preventDefault(); });
  on(dlg, 'click', function (e) { if (e.target === dlg || e.target.classList.contains('trs-stage')) close(); });
  on(q('.trs-open', sec), 'click', open);
  on(q('.trs-tab', fx), 'click', open);
  on(q('.trs-x'), 'click', close);
  on(q('.trs-done'), 'click', close);
  on(q('.trs-again'), 'click', function () { form.reset(); freshCard(); try { ta.focus(); } catch (x) {} });

  /* ================= validate + send ================= */
  function bad(field, text) { field.setAttribute('aria-invalid', 'true'); msg.textContent = text; try { field.focus(); } catch (x) {} return false; }
  function valid() {
    [ta, inEmail].forEach(function (n) { n.removeAttribute('aria-invalid'); });
    msg.textContent = '';
    if (ta.value.trim().length < 3) return bad(ta, 'The card is blank. Write your suggestion first.');
    var em = inEmail.value.trim();
    if (em && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(em)) return bad(inEmail, 'That email does not look right. Fix it or leave it blank.');
    return true;
  }
  function post() {
    if (hp.value) return Promise.resolve(true);                         // a bot filled the honeypot: pretend, send nothing
    if (!CONFIG.ENDPOINT) return Promise.reject(new Error('closed'));
    var em = inEmail.value.trim(), nm = inName.value.trim();
    var data = {
      _subject: CONFIG.SUBJECT, _template: 'table', _captcha: 'false',
      suggestion: ta.value.trim(),
      name: nm || '(not given)',
      page: location.href
    };
    if (em) { data.email = em; data._replyto = em; }
    return fetch(CONFIG.ENDPOINT, {
      method: 'POST', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' }, body: JSON.stringify(data)
    }).then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) {
      if (r.ok && String(j.success) === 'true') return true;              // FormSubmit answers 200 + "false" on refusals
      var m = String(j.message || '');
      throw new Error(/activat/i.test(m) ? 'activation' : 'refused');
    }); });
  }
  on(form, 'submit', function (e) {
    e.preventDefault();
    if (busy || !valid()) return;
    busy = true; send.disabled = true; send.textContent = 'Posting...';
    post().then(function () { return drop(); }, function (err) {
      busy = false; send.disabled = false; send.textContent = 'Drop it in the box';
      var why = err && err.message;
      msg.textContent = why === 'activation' || why === 'closed'
        ? 'The box is not open for cards just yet. Please try again soon.'
        : 'The slot is jammed and the card did not go through. Please try again in a minute.';
    });
  });

  /* ================= the drop ================= */
  function drop() {
    var who = inName.value.trim(), hadEmail = !!inEmail.value.trim();
    var line = 'Thank you' + (who ? ', ' + who.split(/\s+/)[0] : '') + '. Your card is in the box.';
    var line2 = hadEmail ? 'If a reply is in order, it will come to the email you left.' : 'Every card helps make the site better.';
    var wrap = q('.trs-wrap'), h0 = wrap.offsetHeight;

    send.textContent = 'Drop it in the box';
    var anim = Promise.resolve();
    if (!reduce.matches && form.animate) {
      var c = form.getBoundingClientRect(), s0 = slot.getBoundingClientRect();
      var w = form.offsetWidth, h = form.offsetHeight;                 // untransformed size
      var s = Math.min(.4, (s0.width * .8) / w);
      var tx = (s0.left + s0.width / 2) - (c.left + c.width / 2);
      var lineY = s0.top + s0.height * .55, top0 = c.top + (c.height - h) / 2;
      var ty1 = lineY - top0 - h * s, ty2 = lineY - top0 + 1;
      var T = function (x, y, sc, r) { return 'translate(' + x + 'px,' + y + 'px) scale(' + sc + ') rotate(' + r + 'deg)'; };
      var fly = form.animate([
        { offset: 0, transform: T(0, 0, 1, -.6), clipPath: 'inset(0 0 0 0)', easing: 'cubic-bezier(.3,0,.2,1)' },
        { offset: .16, transform: T(0, -10, 1.015, 0), clipPath: 'inset(0 0 0 0)', easing: 'cubic-bezier(.5,0,.2,1)' },
        { offset: .56, transform: T(tx, ty1 - 16, s, 0), clipPath: 'inset(0 0 0 0)', easing: 'ease-in-out' },
        { offset: .66, transform: T(tx, ty1, s, 0), clipPath: 'inset(0 0 0 0)', easing: 'cubic-bezier(.55,0,.85,.4)' },
        { offset: 1, transform: T(tx, ty2, s, 0), clipPath: 'inset(0 0 100% 0)' }
      ], { duration: 1500, fill: 'forwards' });
      anim = fly.finished.then(function () {
        form.style.visibility = 'hidden';
        return dlgArt.animate([
          { transform: 'translateY(0) scaleY(1)' }, { transform: 'translateY(3px) scaleY(.985)', offset: .35 },
          { transform: 'translateY(-1px) scaleY(1.004)', offset: .7 }, { transform: 'translateY(0) scaleY(1)' }
        ], { duration: 320, easing: 'ease-out' }).finished;
      }).then(function () { fly.cancel(); });
    }
    return anim.then(function () {
      form.style.visibility = '';
      form.hidden = true; thanks.hidden = false;
      q('.trs-ty2').textContent = line2;
      q('.trs-sr').textContent = line + ' ' + line2;
      var v = q('.trs-tyv'), caret = q('.trs-caret');
      if (reduce.matches || !wrap.animate) { v.textContent = line; caret.hidden = true; busy = false; try { q('.trs-done').focus(); } catch (x) {} return; }
      var h1 = wrap.offsetHeight;
      wrap.animate([{ height: h0 + 'px', overflow: 'hidden' }, { height: h1 + 'px', overflow: 'hidden' }], { duration: 260, easing: 'cubic-bezier(.16,1,.3,1)' });
      thanks.animate([{ opacity: 0, transform: 'translateY(8px) rotate(.4deg)' }, { opacity: 1, transform: 'rotate(-.6deg)' }], { duration: 320, easing: 'ease-out' });
      v.textContent = ''; caret.hidden = false;
      var i = 0;
      return wait(260).then(function step() {
        if (i >= line.length) { caret.hidden = true; busy = false; try { q('.trs-done').focus({ preventScroll: true }); } catch (x) {} return; }
        v.textContent = line.slice(0, ++i);
        return wait(line.charAt(i - 1) === '.' || line.charAt(i - 1) === ',' ? 120 : 26).then(step);
      });
    });
  }

  /* ================= start ================= */
  if (D.readyState === 'loading') on(D, 'DOMContentLoaded', boot); else boot();
  W.trdSuggest = { open: open, close: close, config: CONFIG };
})();
