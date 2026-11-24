/* Bold Substack signup pop-up (therubberduck.net).
   Shows once per visitor after ~20s or on desktop exit-intent (not on first load).
   Dismiss/subscribe remembered 14 days. Never opens while #mission-dlg is open.
   Never opens on pages that already show an inline signup form (form.signup-form / form.n).
   Subscribing: the reader's email is handed to Substack's own subscribe page
   (therubberduck78.substack.com/subscribe?email=...) in a new tab, where they press Subscribe.
   Cross-site posts to Substack's API do not subscribe anyone (tested 2026-11-23), so this
   pop-up never claims success itself; it says what to do next on the Substack tab.
   Preview: ?trd_signup=1 (ignores timer and localStorage). */
(function () {
  'use strict';
  var W = window, D = document;
  if (W.trdSignupPop) return;
  W.trdSignupPop = true;

  var LS = 'trd-signup-pop';
  var HOLD = 14 * 864e5;
  var DELAY = 20000;
  var EXIT_GRACE = 3000;
  var SUB = 'https://therubberduck78.substack.com/subscribe';
  var IMG = '/assets/trd/img/signup-duck.webp';

  var dlg, form, email, err, ok, shown = false, shownOnce = false, timer, exitArmed = false;

  function forced() {
    try { return new URLSearchParams(location.search).get('trd_signup') === '1'; } catch (e) { return false; }
  }
  function missionOpen() {
    var m = D.getElementById('mission-dlg');
    return !!(m && (m.open || m.hasAttribute('open')));
  }
  function remembered() {
    try {
      var v = parseInt(localStorage.getItem(LS), 10);
      return !!(v && (Date.now() - v) < HOLD);
    } catch (e) { return false; }
  }
  function remember() {
    if (forced()) return;
    try { localStorage.setItem(LS, String(Date.now())); } catch (e) {}
  }
  function pageUrl() {
    try { return location.href.split('#')[0]; } catch (e) { return 'https://therubberduck.net/'; }
  }

  function build() {
    if (dlg) return dlg;
    dlg = D.createElement('dialog');
    dlg.className = 'trd-signup';
    dlg.id = 'trd-signup';
    dlg.setAttribute('aria-labelledby', 'trd-signup-title');
    dlg.innerHTML =
      '<div class="trd-signup-card">' +
        '<button type="button" class="trd-signup-x" aria-label="Close">&times;</button>' +
        '<div class="trd-signup-art">' +
          '<img src="' + IMG + '" width="960" height="825" alt="The Rubber Duck&trade;" decoding="async">' +
        '</div>' +
        '<div class="trd-signup-copy">' +
          '<p class="trd-signup-k">The Rubber Duck&trade;</p>' +
          '<h2 class="trd-signup-h" id="trd-signup-title">WEEKLY SAUCE<br>DELIVERY</h2>' +
          '<p class="trd-signup-s">the free weekly recap, in your inbox every sunday night.</p>' +
          '<form class="trd-signup-form" action="' + SUB + '" method="get" target="_blank" novalidate>' +
            '<label class="visually-hidden" for="trd-signup-email" style="position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0">Email</label>' +
            '<input class="trd-signup-email" id="trd-signup-email" name="email" type="email" autocomplete="email" inputmode="email" required placeholder="your email address">' +
            '<button class="trd-signup-go" type="submit">Subscribe</button>' +
            '<p class="trd-signup-err" role="status" hidden></p>' +
          '</form>' +
          '<p class="trd-signup-fine">free weekly recap. unsubscribe in one click. we never sell or share your email.</p>' +
          '<div class="trd-signup-ok" hidden role="status" aria-live="polite">' +
            '<p class="trd-signup-ok-h">almost there.</p>' +
            '<p class="trd-signup-ok-s">press <b>subscribe</b> on the substack tab that just opened, and the sunday recap starts coming.</p>' +
            '<a class="trd-signup-go trd-signup-again" href="' + SUB + '" target="_blank" rel="noopener">tab didn\'t open? finish here</a>' +
          '</div>' +
        '</div>' +
      '</div>';
    D.body.appendChild(dlg);
    form = dlg.querySelector('.trd-signup-form');
    email = dlg.querySelector('#trd-signup-email');
    err = dlg.querySelector('.trd-signup-err');
    ok = dlg.querySelector('.trd-signup-ok');
    dlg.querySelector('.trd-signup-x').addEventListener('click', function (e) { e.preventDefault(); close(); });
    dlg.addEventListener('click', function (e) { if (e.target === dlg) close(); });
    dlg.addEventListener('close', function () { shown = false; remember(); });
    dlg.addEventListener('cancel', function () { remember(); });
    form.addEventListener('submit', onSubmit);
    return dlg;
  }

  function sayErr(t) {
    if (!err) return;
    if (!t) { err.hidden = true; err.textContent = ''; return; }
    err.hidden = false;
    err.textContent = t;
  }

  function track(path, title) {
    try {
      if (W.trdTrack) W.trdTrack(path, title, 0);
      else if (W.goatcounter && W.goatcounter.count) W.goatcounter.count({ path: path, title: title, event: true });
    } catch (e) {}
  }

  function subUrl(addr) {
    return SUB + '?email=' + encodeURIComponent(addr) + '&utm_source=therubberduck.net&utm_medium=popup';
  }

  /* Handed off, not subscribed: say so plainly and keep a link in case the tab was blocked. */
  function handedOff(addr, opened) {
    remember();
    if (form) form.hidden = true;
    var fine = dlg && dlg.querySelector('.trd-signup-fine');
    if (fine) fine.hidden = true;
    var again = ok && ok.querySelector('.trd-signup-again');
    if (again) {
      again.href = subUrl(addr);
      again.textContent = opened ? 'tab didn\'t open? finish here' : 'finish on substack';
    }
    var s2 = ok && ok.querySelector('.trd-signup-ok-s');
    if (s2 && !opened) s2.innerHTML = 'one more tap: press <b>subscribe</b> on substack, and the sunday recap starts coming.';
    if (ok) ok.hidden = false;
    sayErr('');
  }

  function onSubmit(e) {
    e.preventDefault();
    sayErr('');
    var addr = (email && email.value || '').trim();
    if (!addr || !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(addr)) {
      sayErr('that email doesn\'t look right. check it and try again.');
      if (email) email.focus();
      return;
    }
    /* window.open inside the submit handler counts as the reader's own click, so it is not blocked. */
    var win = null;
    try { win = W.open(subUrl(addr), '_blank'); if (win) win.opener = null; } catch (x) { win = null; }
    track('event/form/substack-handoff', 'Form: Substack signup handed off (' + location.pathname + ')');
    handedOff(addr, !!win);
  }

  function open() {
    if (shown || missionOpen()) return;
    build();
    if (typeof dlg.showModal === 'function') dlg.showModal();
    else dlg.setAttribute('open', '');
    shown = true;
    shownOnce = true;
    if (email && !form.hidden) {
      try { email.focus(); } catch (e) {}
    }
  }

  function close() {
    if (!dlg) return;
    if (typeof dlg.close === 'function' && dlg.open) dlg.close();
    else {
      dlg.removeAttribute('open');
      shown = false;
      remember();
    }
  }

  function tryOpen() {
    if (shownOnce || shown) return;
    if (!forced() && remembered()) return;
    if (missionOpen()) return;
    open();
  }

  function schedule() {
    if (forced()) {
      tryOpen();
      return;
    }
    if (remembered()) return;
    timer = setTimeout(function () {
      if (missionOpen()) {
        var m = D.getElementById('mission-dlg');
        if (m) m.addEventListener('close', tryOpen, { once: true });
        return;
      }
      tryOpen();
    }, DELAY);

    function armExit() { exitArmed = true; }
    setTimeout(armExit, EXIT_GRACE);
    D.addEventListener('mouseout', function (e) {
      if (!exitArmed || shownOnce || shown || remembered() || missionOpen()) return;
      if (e.clientY > 0) return;
      if (e.relatedTarget) return;
      if (W.matchMedia && !W.matchMedia('(pointer:fine) and (min-width:900px)').matches) return;
      tryOpen();
    });
  }

  function hasInlineForm() {
    return !!D.querySelector('form.signup-form, form.n');
  }

  function start() {
    if (hasInlineForm() && !forced()) return;   /* the page already offers a signup: never stack a pop-up on it */
    build();
    schedule();
  }
  if (D.readyState === 'loading') D.addEventListener('DOMContentLoaded', start);
  else start();
})();
