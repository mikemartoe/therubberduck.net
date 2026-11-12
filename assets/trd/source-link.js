/* Where an 8ch.net drop link actually opens.
   8ch.net has been offline since 2019. A deep link such as
   https://8ch.net/patriotsfight/res/440.html#465 now returns the 8ch.net
   homepage (verified 2026-11-12). The Wayback Machine refuses 8ch.net itself
   (AdministrativeAccessControlException), so https://web.archive.org/web/2/<8ch url>
   is a 403, not the post.
   Thread and post ids below are the ids already stored on each drop. Nothing here
   is guessed.
   - /qresearch/ and /thestorm/: every one of those threads still answers on
     8kun.top with the same ids (the post text is the original post).
   - /cbts/: only the threads in CBTS still answer on 8kun.top. The rest were
     not captured by the Wayback Machine.
   - /patriotsfight/, /pol/, /greatawakening/: 8kun.top 404s. The Q Origins
     dchan archive has the thread, and the Wayback Machine has a capture of
     that dchan page (the /patriotsfight/ 440 capture contains drop #2491,
     post No.465). dchan.qorigins.org itself was returning 502 on 2026-11-12,
     so those links use the capture.
   - Anything else with a real /board/res/N.html id goes to that dchan thread,
     which is the archive that holds the 8chan posts the other two do not. */
(function () {
  'use strict';
  var W = window, D = document;
  if (W.trdSourceLink) return;
  var CBTS = {
    74470: 1, 82147: 1, 85308: 1, 92197: 1, 93014: 1, 98535: 1, 120902: 1, 121693: 1,
    126564: 1, 128199: 1, 128973: 1, 142052: 1, 145318: 1, 148453: 1, 150923: 1,
    153368: 1, 154170: 1, 156622: 1, 157461: 1, 238736: 1, 248147: 1, 251305: 1
  };
  /* Latest status-200 Wayback capture of the dchan page for that thread. */
  var WB = {
    'patriotsfight/1': '20240229052728',
    'patriotsfight/62': '20240229052325',
    'patriotsfight/440': '20240907135714',
    'greatawakening/1': '20240303113226',
    'greatawakening/452': '20240303113224',
    'cbts/139594': '20220625215404',
    'pol/10913010': '20250614230957',
    'pol/11028937': '20260210163307',
    'pol/11034208': '20260208062921',
    'pol/11113218': '20260207101123',
    'pol/12444696': '20260217071904',
    'pol/13401747': '20260207103817',
    'pol/13444555': '20260207162132',
    'pol/13526747': '20260211063112',
    'pol/13575898': '20260209161626',
    'pol/13576054': '20260209185114',
    'pol/13576140': '20260207190848',
    'pol/13580425': '20260208034406',
    'pol/13582002': '20260208204001',
    'pol/13582374': '20260208175833',
    'pol/13584825': '20260207205808',
    'pol/13585320': '20260210135717',
    'pol/13594585': '20260207122550',
    'pol/13603409': '20260208101547',
    'pol/13604241': '20260207022144',
    'pol/13607496': '20260209200703',
    'pol/13619661': '20260210154116',
    'pol/13619977': '20260211072632',
    'pol/13621032': '20260208191753',
    'pol/13622783': '20260214075054',
    'pol/13626143': '20260207092309',
    'pol/13626219': '20260216085256',
    'pol/13626420': '20260208123348',
    'pol/13627597': '20260213162335',
    'pol/13627721': '20260207070750',
    'pol/13627820': '20260207115351',
    'pol/13627827': '20260213014953',
    'pol/13628895': '20260207031802',
    'pol/13629482': '20260215104755',
    'pol/13632003': '20260213135236',
    'pol/13637652': '20260208112244',
    'pol/13638690': '20260209114256'
  };
  function hostOf(u) {
    try { return new URL(u, location.href).hostname.replace(/^www\./i, ''); } catch (e) { return ''; }
  }
  function label(u) {
    var h = hostOf(u);
    if (h === 'archive.4plebs.org' || /\.?4plebs\.org$/i.test(h)) return 'See original drop now';
    if (/archive\.(today|ph|li|is|vn|md)$/i.test(h)) return 'archive.today capture';
    if (/web\.archive\.org$/i.test(h)) return 'Wayback Machine capture';
    if (h === '8kun.top' || /\.8kun\.top$/i.test(h)) return '8kun post';
    if (h === '8ch.net' || /\.8ch\.net$/i.test(h)) return '8chan post';
    if (h === '4chan.org' || /\.4chan\.org$/i.test(h)) return '4chan post';
    if (/dchan/i.test(h)) return 'dChan archive capture';
    return h ? ('source: ' + h) : 'source link';
  }
  /* '' means this 8ch.net address has no thread id, so it must not be opened
     (8ch.net would show its homepage). Any other site is returned unchanged. */
  function url(raw) {
    if (!raw) return '';
    var u;
    try { u = new URL(String(raw), location.href); } catch (e) { return String(raw); }
    var host = u.hostname.replace(/^www\./i, '');
    if (host !== '8ch.net') return u.href;
    var path = u.pathname.replace(/\/{2,}/g, '/');
    var m = path.match(/^\/([^/]+)\/res\/(\d+)\.html$/i);
    var board, thread, hash = u.hash || '';
    if (!m) return '';
    board = m[1].toLowerCase();
    thread = m[2];
    /* drops.js stored /greatawakening/res/0.html for two drops. header-table.json
       has the real thread: post 110 is in thread 1, post 452 is thread 452. */
    if (board === 'greatawakening' && thread === '0') {
      if (hash === '#110') thread = '1';
      else if (hash === '#452') thread = '452';
      else return '';
    }
    var key = board + '/' + thread;
    var tail = '/' + board + '/res/' + thread + '.html' + hash;
    if (board === 'qresearch' || board === 'thestorm' || (board === 'cbts' && CBTS[thread])) {
      return 'https://8kun.top' + tail;
    }
    if (WB[key]) return 'https://web.archive.org/web/' + WB[key] + '/https://dchan.qorigins.org' + tail;
    return 'https://dchan.qorigins.org' + tail;
  }
  function fix(a) {
    if (!a || a.nodeType !== 1 || a.tagName !== 'A') return;
    if (a.getAttribute('data-trd-src')) return;
    var h = a.getAttribute('href');
    if (!h || h.indexOf('8ch.net') < 0) return;
    var next = url(h);
    a.setAttribute('data-trd-src', h);
    if (!next || next === h) return;
    a.setAttribute('href', next);
    if (!a.getAttribute('target')) { a.setAttribute('target', '_blank'); a.setAttribute('rel', 'nofollow noopener'); }
    var hostEl = a.querySelector && a.querySelector('.src-host');
    if (hostEl) hostEl.textContent = hostOf(next);
    var lbl = a.querySelector && a.querySelector('.src-lbl');
    if (lbl && a.classList && a.classList.contains('src-post')) lbl.textContent = label(next);
  }
  function scan(root) {
    if (!root || !root.querySelectorAll) return;
    if (root.tagName === 'A') fix(root);
    var list = root.querySelectorAll('a[href*="8ch.net"]:not([data-trd-src])');
    for (var i = 0; i < list.length; i++) fix(list[i]);
  }
  var queued = false;
  function later() {
    if (queued) return;
    queued = true;
    (W.requestAnimationFrame || W.setTimeout)(function () { queued = false; if (D.body) scan(D.body); });
  }
  function start() {
    if (!D.body) return;
    scan(D.body);
    if (W.MutationObserver) new W.MutationObserver(later).observe(D.body, { childList: true, subtree: true });
  }
  if (D.readyState === 'loading') D.addEventListener('DOMContentLoaded', start);
  else start();
  W.trdSourceLink = { url: url, label: label, host: hostOf, scan: scan };
})();
