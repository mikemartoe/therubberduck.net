/* The Suggestion Box for therubberduck.net
   A wooden box at the foot of every page (and a small side tab on wide screens).
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
     SHOW_TAB: the small "Suggestions" tab on the right edge of wide screens.
     TAB_OFF: pages whose content runs to the right edge get no tab.          */
  var CONFIG = {
    ENDPOINT: 'https://formsubmit.co/ajax/therubberduk@gmail.com',
    SUBJECT: 'Suggestion Box: therubberduck.net',
    SHOW_TAB: true,
    TAB_OFF: /^\/memes\.html$/i
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
  fx.innerHTML = '<button class="trs-tab" type="button" aria-haspopup="dialog" aria-label="Open the suggestion box"><i></i><span>Suggestions</span></button>';

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
    var b = D.body; if (!b) return;
    var pod = D.getElementById('trd-pod'), ref = pod && pod.parentNode === b ? pod : null;
    sec.classList.toggle('trs-nopod', !ref);
    fx.classList.toggle('trs-tab-on', !!CONFIG.SHOW_TAB && !(CONFIG.TAB_OFF && CONFIG.TAB_OFF.test(location.pathname)));
    if (sec.parentNode !== b) { if (dlg.open) resetAfterNav(); b.insertBefore(sec, ref); }
    if (fx.parentNode !== b) b.insertBefore(fx, ref);
    if (dlg.parentNode !== b) b.insertBefore(dlg, ref);
  }
  function resetAfterNav() { try { dlg.close(); } catch (e) {} D.documentElement.classList.remove('trs-lock'); }
  function boot() {
    place();
    new MO(function () { place(); }).observe(D.body, { childList: true });
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
