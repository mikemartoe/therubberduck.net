/* DUCK SAUCE story share: visible front-page OG card + X / Facebook / Text / Email / Copy link.
   Native Share sheet on phones that support navigator.share. Built with assets/trd/share.js. */
(function () {
  'use strict';
  var S = window.trdShare, D = document;
  if (!S) return;
  var host = D.querySelector('.dx-share-row');
  if (!host) return;
  var id = host.getAttribute('data-share-id');
  var card = host.getAttribute('data-share-card') || ('https://therubberduck.net/images/newsroom/og/' + id + '.jpg');
  var page = host.getAttribute('data-share-page');
  var text = host.getAttribute('data-share-text');
  var only = ['x', 'fb', 'sms', 'email', 'link'];
  var row = S.build({
    kind: 'newsroom',
    id: id,
    page: page,
    text: text,
    only: only,
    thumb: card,
    file: card,
    igFile: null,
    fileName: 'the-rubber-duck-' + id + '.jpg',
    groupLabel: host.getAttribute('data-share-label') || 'Share this piece'
  });
  /* keep Mike\'s platform order (share.js filters in its own platform-list order) */
  var btns = row.querySelector('.shr-btns');
  if (btns) {
    var map = {};
    Array.prototype.forEach.call(btns.querySelectorAll('[data-p]'), function (b) {
      map[b.getAttribute('data-p')] = b;
    });
    only.forEach(function (k) { if (map[k]) btns.appendChild(map[k]); });
    if (navigator.share) {
      var b = D.createElement('button');
      b.type = 'button';
      b.className = 'shr-b shr-native';
      b.setAttribute('aria-label', 'Share');
      b.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v10M8 7l4-4 4 4" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/><path d="M5 14v5a2 2 0 002 2h10a2 2 0 002-2v-5" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg><span>Share</span>';
      b.addEventListener('click', function () {
        navigator.share({ title: text, text: text, url: page }).catch(function () {});
      });
      btns.insertBefore(b, btns.firstChild);
    }
  }
  host.appendChild(row);
  var sec = host.closest('.dx-share');
  if (sec) sec.hidden = false;
})();
