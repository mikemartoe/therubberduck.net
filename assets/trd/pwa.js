/* The Rubber Duck web app (PWA): service worker, install banner, push alerts. Preview 2026-10-30.
   Alerts UI renders into any element with [data-trd-alerts]. Install banner shows on phones/tablets only. */
(function () {
  var CFG = window.TRD_PWA_CONFIG || {};
  var host = location.hostname;
  var isPreview = /workers\.dev$|^localhost$|^127\.0\.0\.1$/.test(host);
  var API = CFG.api || (isPreview ? 'https://trd-push-preview.therubberduck.workers.dev/api/push' : '/api/push');
  var VAPID = CFG.vapidPublicKey || 'BCRxkKFAATzp_KcV5LBLYLfFV1MndJnTJSknDKV-kcgi03VTC_kij5qQJ2RIEzYX0_N_9rAzKqKvRWpsaLuJXiM';
  var ML_DELTAS_GROUP = CFG.mailerliteDeltasGroup || ''; /* MailerLite group id for the email Deltas digest; empty = hook off */
  var ua = navigator.userAgent || '';
  var isIOS = /iPad|iPhone|iPod/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  var standalone = (window.matchMedia && matchMedia('(display-mode: standalone)').matches) || navigator.standalone === true;
  var small = window.matchMedia && matchMedia('(max-width: 899px), (pointer: coarse)').matches;
  var canPush = 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
  var IOS_LINE = 'On iPhone, alerts work after you add The Rubber Duck to your Home Screen (iOS 16.4 or later): tap Share, then Add to Home Screen.';
  function ls(k, v) { try { if (v === undefined) return localStorage.getItem(k); if (v === null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch (e) { return null; } }
  function el(tag, cls, html) { var e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }
  function track(name) { try { if (window.trdTrack) window.trdTrack('event/pwa/' + name, 'PWA: ' + name, 0); } catch (e) {} }

  /* ---- service worker ---- */
  var regP = null;
  if ('serviceWorker' in navigator) {
    regP = new Promise(function (res) {
      function go() { navigator.serviceWorker.register('/sw.js', { scope: '/' }).then(res, function () { res(null); }); }
      if (document.readyState === 'complete') go(); else window.addEventListener('load', go);
    });
  }

  /* ---- install banner (phones and tablets only; never on desktop) ---- */
  var bip = null;
  window.addEventListener('beforeinstallprompt', function (e) { e.preventDefault(); bip = e; maybeBanner(); });
  window.addEventListener('appinstalled', function () { ls('trd-pwa-installed', '1'); hideBanner(); track('installed'); });
  var banner = null;
  function dismissedRecently() { var t = +ls('trd-pwa-dismiss') || 0; return Date.now() - t < 30 * 864e5; }
  function hideBanner() { if (banner) { banner.remove(); banner = null; } }
  function maybeBanner() {
    if (banner || standalone || !small || dismissedRecently() || CFG.noBanner || document.querySelector('[data-trd-alerts]')) return;
    var iosSafari = isIOS && /Safari/.test(ua) && !/CriOS|FxiOS|EdgiOS/.test(ua);
    if (!bip && !iosSafari) return;
    banner = el('aside', 'trd-pwa-bar');
    banner.setAttribute('role', 'dialog'); banner.setAttribute('aria-label', 'Install The Rubber Duck app');
    var text = bip ? 'Install The Rubber Duck on your home screen for one-tap access and alerts.'
                   : 'Add The Rubber Duck to your Home Screen: tap Share, then Add to Home Screen.';
    banner.innerHTML = '<img class="trd-pwa-ico" src="/images/app/app-icon-192.png" alt="" width="44" height="44">' +
      '<p class="trd-pwa-txt"><b>THE RUBBER DUCK APP</b><span>' + text + '</span></p>' +
      '<div class="trd-pwa-acts">' + (bip ? '<button type="button" class="trd-pwa-go">Install</button>' : '<a class="trd-pwa-go" href="/alerts/#inst-h">How to add</a>') +
      '<button type="button" class="trd-pwa-x">Not now</button></div>';
    document.body.appendChild(banner);
    var go = banner.querySelector('button.trd-pwa-go');
    if (go) go.addEventListener('click', function () { bip.prompt(); bip.userChoice.then(function (c) { track('prompt-' + c.outcome); bip = null; hideBanner(); }); });
    banner.querySelector('.trd-pwa-x').addEventListener('click', function () { ls('trd-pwa-dismiss', String(Date.now())); hideBanner(); track('banner-dismiss'); });
    track('banner-shown');
  }
  setTimeout(maybeBanner, 4000);

  /* ---- push alerts ---- */
  function b64u(s) { s = s.replace(/-/g, '+').replace(/_/g, '/'); while (s.length % 4) s += '='; var r = atob(s), a = new Uint8Array(r.length); for (var i = 0; i < r.length; i++) a[i] = r.charCodeAt(i); return a; }
  function api(path, body) { return fetch(API + path, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body), credentials: 'omit' }).then(function (r) { if (!r.ok) throw new Error('api ' + r.status); return r.json(); }); }
  function getSub() { return regP ? regP.then(function (reg) { return reg ? reg.pushManager.getSubscription() : null; }) : Promise.resolve(null); }

  function renderAlerts(box) {
    box.classList.add('trd-alerts');
    box.innerHTML = '<h2 class="ta-h">GET ALERTS</h2>' +
      '<p class="ta-p">Choose what you want. You can change or stop alerts here at any time.</p>' +
      '<div class="ta-opts">' +
      '<label class="ta-opt"><input type="checkbox" name="drops" checked><span><b>New drops</b><i>When a new drop is added to the archive.</i></span></label>' +
      '<label class="ta-opt"><input type="checkbox" name="deltas" checked><span><b>Daily Deltas digest</b><i>Each morning: the drops posted on this date in past years.</i></span></label>' +
      '</div><div class="ta-acts"><button type="button" class="ta-on">Turn on alerts</button><button type="button" class="ta-off" hidden>Turn off</button></div>' +
      '<p class="ta-msg" role="status" aria-live="polite"></p>' +
      '<p class="ta-mail">Prefer email? <a href="' + (document.querySelector('form.signup-form') ? '#signup-h' : '/alerts/#signup-h') + '">Get updates by email</a></p>';
    var on = box.querySelector('.ta-on'), off = box.querySelector('.ta-off'), msg = box.querySelector('.ta-msg');
    var cbs = box.querySelectorAll('.ta-opt input');
    function say(t, err) { msg.textContent = t; msg.classList.toggle('err', !!err); }
    function topics() { var t = []; for (var i = 0; i < cbs.length; i++) if (cbs[i].checked) t.push(cbs[i].name); return t; }
    var saved = ls('trd-push-topics');
    if (saved) { var s = saved.split(','); for (var i = 0; i < cbs.length; i++) cbs[i].checked = s.indexOf(cbs[i].name) !== -1; }
    if (isIOS && !standalone) { on.disabled = true; say(IOS_LINE); return; }
    if (!canPush) { on.disabled = true; say('This browser does not support alerts. Try Chrome, Edge, Firefox or Safari.'); return; }
    if (Notification.permission === 'denied') { on.disabled = true; say('Alerts are blocked for this site in your browser settings.', true); return; }
    getSub().then(function (sub) { if (sub && saved) { on.textContent = 'Save choices'; off.hidden = false; say('Alerts are on.'); } });
    on.addEventListener('click', function () {
      var t = topics();
      if (!t.length) { say('Pick at least one alert, or press Turn off.', true); return; }
      on.disabled = true; say('Asking your browser\u2026');
      Notification.requestPermission().then(function (p) {
        if (p !== 'granted') throw new Error('perm');
        return regP.then(function (reg) {
          return reg.pushManager.getSubscription().then(function (s) { return s || reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: b64u(VAPID) }); });
        });
      }).then(function (sub) {
        return api('/subscribe', { subscription: sub.toJSON(), topics: t, tz: (Intl.DateTimeFormat().resolvedOptions().timeZone || '') });
      }).then(function () {
        ls('trd-push-topics', t.join(',')); on.disabled = false; on.textContent = 'Save choices'; off.hidden = false;
        say('Alerts are on: ' + t.map(function (x) { return x === 'drops' ? 'new drops' : 'daily Deltas digest'; }).join(' and ') + '.'); track('push-on');
      }).catch(function (e) {
        on.disabled = false;
        say(e && e.message === 'perm' ? 'Alerts were not allowed. You can allow them in your browser settings.' : 'That did not go through. Please try again in a minute.', true);
      });
    });
    off.addEventListener('click', function () {
      off.disabled = true;
      getSub().then(function (sub) {
        if (!sub) return;
        var ep = sub.endpoint;
        return sub.unsubscribe().then(function () { return api('/unsubscribe', { endpoint: ep }).catch(function () {}); });
      }).then(function () { ls('trd-push-topics', null); off.disabled = false; off.hidden = true; on.textContent = 'Turn on alerts'; say('Alerts are off.'); track('push-off'); });
    });
  }

  /* ---- email digest hook: adds a Deltas digest choice to the existing newsletter form once a MailerLite group is set ---- */
  function emailHook() {
    if (!ML_DELTAS_GROUP) return;
    var forms = document.querySelectorAll('form.signup-form');
    for (var i = 0; i < forms.length; i++) {
      var f = forms[i]; if (f.querySelector('.ta-ml')) continue;
      var l = el('label', 'ta-ml', '<input type="checkbox" name="groups[]" value="' + ML_DELTAS_GROUP + '" checked> Also send the daily Deltas digest');
      f.insertBefore(l, f.querySelector('button'));
    }
  }

  function boot() {
    var boxes = document.querySelectorAll('[data-trd-alerts]');
    for (var i = 0; i < boxes.length; i++) renderAlerts(boxes[i]);
    emailHook();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
  window.trdPwa = { api: API, showBanner: maybeBanner };
})();
