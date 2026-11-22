/* TRD support strip: wires "Share this drop" / "Share the Ledger" to the
   existing assets/trd/share.js row (compact, in-page, no popup). */
(function () {
  'use strict';
  var W = window, D = document;
  var SITE = 'https://therubberduck.net';
  var SHARE_ONLY = ['x', 'truth', 'fb', 'email', 'sms', 'link'];

  function loadScript(src, ok) {
    return new Promise(function (resolve, reject) {
      if (ok && ok()) { resolve(); return; }
      var s = D.createElement('script');
      s.src = src;
      s.onload = function () { resolve(); };
      s.onerror = function () { reject(); };
      D.head.appendChild(s);
    });
  }

  function fillDrop(host, n) {
    var C = W.TRD_DROP_CARDS || { base: 'https://memes.therubberduck.net/drops/', long: [], v2: [], v2base: 'https://memes.therubberduck.net/drops/v2/' };
    var B = (C.v2 && C.v2.indexOf(n) > -1) ? C.v2base : C.base;
    host.appendChild(W.trdShare.build({
      kind: 'drop', id: String(n),
      page: SITE + '/drops/share/' + n + '.html',
      text: 'Q drop #' + n,
      thumb: B + 'og/' + n + '.jpg',
      file: B + 'card/' + n + '.png',
      igFile: (C.long && C.long.indexOf(n) > -1) ? (B + 'ig/' + n + '.png') : null,
      fileName: 'q-drop-' + n + '.png',
      compact: true, only: SHARE_ONLY,
      groupLabel: 'Share Q drop #' + n
    }));
  }

  function fillLedger(host) {
    host.appendChild(W.trdShare.build({
      kind: 'ledger', id: 'ledger',
      page: SITE + '/ledger.html',
      text: 'The Drop Ledger',
      thumb: SITE + '/images/brand/room-ledger-20261103.jpg',
      file: SITE + '/images/brand/room-ledger-20261103.jpg',
      fileName: 'drop-ledger.jpg',
      compact: true, only: SHARE_ONLY,
      groupLabel: 'Share the Ledger'
    }));
  }

  function fillHome(host) {
    host.appendChild(W.trdShare.build({
      kind: 'home', id: 'home',
      page: SITE + '/',
      text: 'The Rubber Duck',
      thumb: SITE + '/images/brand/room-home-20261103.jpg',
      file: SITE + '/images/brand/room-home-20261103.jpg',
      fileName: 'the-rubber-duck.jpg',
      compact: true, only: SHARE_ONLY,
      groupLabel: 'Share the site'
    }));
  }

  function ensureShare(cb) {
    var jobs = [];
    if (!W.trdShare) jobs.push(loadScript('/assets/trd/share.js?v=20261030c', function () { return !!W.trdShare; }));
    if (!W.TRD_DROP_CARDS) jobs.push(loadScript('/data/drop-cards.js', function () { return !!W.TRD_DROP_CARDS; }).catch(function () {}));
    Promise.all(jobs).then(cb, cb);
  }

  function wire(root) {
    var btn = root.querySelector('.trd-ss-share');
    var host = root.querySelector('.trd-ss-share-row');
    if (!btn || !host) return;
    btn.addEventListener('click', function () {
      var open = btn.getAttribute('aria-expanded') === 'true';
      if (open) {
        host.hidden = true;
        btn.setAttribute('aria-expanded', 'false');
        return;
      }
      host.hidden = false;
      btn.setAttribute('aria-expanded', 'true');
      if (host.getAttribute('data-ready') === '1') return;
      ensureShare(function () {
        if (!W.trdShare) return;
        host.innerHTML = '';
        var kind = root.getAttribute('data-ss-kind');
        var id = root.getAttribute('data-ss-id');
        if (kind === 'ledger') fillLedger(host);
        else if (kind === 'home') fillHome(host);
        else fillDrop(host, parseInt(id, 10));
        host.setAttribute('data-ready', '1');
      });
    });
  }

  function init() {
    var nodes = D.querySelectorAll('.trd-ss');
    for (var i = 0; i < nodes.length; i++) wire(nodes[i]);
  }
  if (D.readyState === 'loading') D.addEventListener('DOMContentLoaded', init);
  else init();
})();
