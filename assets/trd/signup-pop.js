/* Bold Substack signup pop-up (therubberduck.net).
   Shows once per visitor after ~20s or on desktop exit-intent (not on first load).
   Dismiss/subscribe remembered 14 days. Never opens while #mission-dlg is open.
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
  var API = 'https://therubberduck78.substack.com/api/v1/free?nojs=true';
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
          '<h2 class="trd-signup-h" id="trd-signup-title">JOIN THE<br>DUCK SAUCE</h2>' +
          '<p class="trd-signup-s">The weekly recap from The Rubber Duck&trade;, free in your inbox every Sunday night.</p>' +
          '<form class="trd-signup-form" action="' + API + '" method="post" novalidate>' +
            '<input type="hidden" name="source" value="embed">' +
            '<input type="hidden" name="first_url" value="">' +
            '<input type="hidden" name="current_url" value="">' +
            '<label class="visually-hidden" for="trd-signup-email" style="position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0">Email</label>' +
            '<input class="trd-signup-email" id="trd-signup-email" name="email" type="email" autocomplete="email" inputmode="email" required placeholder="Email address">' +
            '<button class="trd-signup-go" type="submit">Subscribe</button>' +
            '<p class="trd-signup-err" role="status" hidden></p>' +
          '</form>' +
          '<p class="trd-signup-ok" hidden>You\'re in. Check your inbox to confirm.</p>' +
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

  function setUrls() {
    var u = pageUrl();
    var first = form.querySelector('[name="first_url"]');
    var cur = form.querySelector('[name="current_url"]');
    if (first) first.value = u;
    if (cur) cur.value = u;
  }

  function sayErr(t) {
    if (!err) return;
    if (!t) { err.hidden = true; err.textContent = ''; return; }
    err.hidden = false;
    err.textContent = t;
  }

  function success() {
    remember();
    if (form) form.hidden = true;
    if (ok) ok.hidden = false;
    sayErr('');
  }

  function fallback(addr) {
    var url = SUB + (addr ? ('?email=' + encodeURIComponent(addr)) : '');
    try { W.open(url, '_blank', 'noopener'); } catch (e) { W.location.href = url; }
  }

  function onSubmit(e) {
    e.preventDefault();
    sayErr('');
    var addr = (email && email.value || '').trim();
    if (!addr || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(addr)) {
      sayErr('Enter a valid email address.');
      if (email) email.focus();
      return;
    }
    setUrls();
    var btn = form.querySelector('.trd-signup-go');
    if (btn) btn.disabled = true;
    var body = new URLSearchParams({
      email: addr,
      source: 'embed',
      first_url: pageUrl(),
      current_url: pageUrl()
    });
    /* Embed-shaped POST (email, source=embed, first_url, current_url). no-cors so the
       request is sent as a simple form post; the response is opaque. If the request
       cannot be sent, open the Substack subscribe page in a new tab. */
    fetch(API, {
      method: 'POST',
      mode: 'no-cors',
      credentials: 'omit',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8' },
      body: body.toString()
    }).then(function () {
      success();
    }).catch(function () {
      fallback(addr);
    }).then(function () {
      if (btn) btn.disabled = false;
    });
  }

  function open() {
    if (shown || missionOpen()) return;
    build();
    setUrls();
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

  function start() {
    build();
    schedule();
  }
  if (D.readyState === 'loading') D.addEventListener('DOMContentLoaded', start);
  else start();
})();
