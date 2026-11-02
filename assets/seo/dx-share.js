/* Share rows on the Deltas date pages (/deltas/MM-DD/), built with the site's share module (assets/trd/share.js).
   - "Share this date": the date page itself (its preview card is images/deltas/og/MM-DD.png), with the labelled
     buttons used in the Meme Dump and Video Room share bars, link-preview platforms only (as in the Video Room).
   - Under every drop: the Drop Ledger's compact icon row, sharing /drops/share/N.html (that drop's preview card,
     opens the drop in The Drop Ledger), with the same text and platforms as the Ledger.
   Written by tools/seo-deltas-build.py into each date page; no tracking beyond what share.js already does. */
(function () {
  'use strict';
  var S = window.trdShare, D = document;
  if (!S) return;
  var ONLY = ['x', 'truth', 'fb', 'email', 'sms', 'link'];
  var MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  var host = D.querySelector('.dx-share-row');
  if (host) {
    var id = host.getAttribute('data-share-id'), card = host.getAttribute('data-share-card');
    host.appendChild(S.build({ kind: 'delta', id: id, page: host.getAttribute('data-share-page'), text: host.getAttribute('data-share-text'),
      noPic: true, only: ONLY, thumb: card, file: card, igFile: null, fileName: 'q-drop-deltas-' + id + '.png',
      groupLabel: host.getAttribute('data-share-label') || 'Share this date' }));
    host.closest('.dx-share').hidden = false;
  }
  var lis = D.querySelectorAll('.dx-year .dx-list > li');
  for (var i = 0; i < lis.length; i++) {
    var li = lis[i], a = li.querySelector('a[href^="/drops/"]'), t = li.querySelector('time');
    var m = a && /^\/drops\/(\d+)\/$/.exec(a.getAttribute('href')); if (!m || li.querySelector('.shr')) continue;
    var n = m[1], iso = t ? t.getAttribute('datetime').slice(0, 10).split('-') : null;
    var when = iso ? (parseInt(iso[2], 10) + ' ' + MON[parseInt(iso[1], 10) - 1] + ' ' + iso[0]) : '';
    li.appendChild(S.build({ kind: 'drop', id: n, page: 'https://therubberduck.net/drops/share/' + n + '.html',
      text: 'Q drop #' + n + (when ? ' \u00b7 ' + when : ''), fileName: 'q-drop-' + n + '.png', compact: true, only: ONLY,
      groupLabel: 'Share Q drop #' + n }));
  }
})();
