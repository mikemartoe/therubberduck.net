/* TRD stack (Mike t1964u): collect up to 4 Q drops or memes, then get all their images and a post
   that carries only their links (one per line, in the order they were added). The visitor writes
   their own words. X and Truth Social take up to 4 pictures per post; neither lets a web link attach
   pictures, so the images are downloaded (or handed to the phone's share sheet) and attached by hand.
   Loaded after share.js. It adds an "Add to stack (n of 4)" button to every drop/meme share row, and
   a page calls trdStack.mount(el) to show the stack tray inside its own pinned bar.
   The stack lives in localStorage (trd.stack.v1), so it follows the visitor between rooms and visits. */
(function () {
  'use strict';
  var W = window, D = document;
  if (W.trdStack || !W.trdShare) return;
  var KEY = 'trd.stack.v1', SEEN = 'trd.stack.seen', MAX = 4;
  var items = load(), trays = [], rows = [];

  function load() { try { var a = JSON.parse(localStorage.getItem(KEY) || '[]'); return Array.isArray(a) ? a.filter(function (i) { return i && i.page && i.img; }).slice(0, MAX) : []; } catch (e) { return []; } }
  function store() { try { localStorage.setItem(KEY, JSON.stringify(items)); } catch (e) {} refresh(); }
  function k(o) { return o.kind + ':' + o.id; }
  function idx(o) { for (var i = 0; i < items.length; i++) if (k(items[i]) === k(o)) return i; return -1; }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function track(a, it) {
    try { if (W.trdTrack) W.trdTrack('event/stack/' + a + (it ? '/' + it.kind + '-' + it.id : ''), 'Stack: ' + a + (it ? ' ' + it.kind + ' ' + it.id : ''), 0); } catch (e) {}
    try { if (W.trdVisit) W.trdVisit.event('stack', { action: a, item: it ? it.kind + '-' + it.id : '', n: items.length }); } catch (e) {}
  }
  function seen() { try { return localStorage.getItem(SEEN) === '1'; } catch (e) { return false; } }
  function markSeen() { try { localStorage.setItem(SEEN, '1'); } catch (e) {} }
  function isVideo(u) { return /\.(mp4|webm|mov|m4v|ogv)(\?|$)/i.test(u || ''); }

  function add(o) {
    if (idx(o) > -1) return 'dup';
    if (items.length >= MAX) return 'full';
    items.push({ kind: o.kind, id: String(o.id), page: o.page, img: o.img, thumb: o.thumb || o.img, name: o.name, label: o.label });
    markSeen(); store(); track('add', o); return 'ok';
  }
  function remove(key) { items = items.filter(function (i) { return k(i) !== key; }); store(); }
  function clear() { items = []; store(); track('clear'); }
  function links() { return items.map(function (i) { return i.page; }).join('\n'); }

  /* ---------- the share-row button ---------- */
  function rowLabel(o) {
    var i = idx(o), n = items.length;
    if (i > -1) return 'In your stack (' + (i + 1) + ' of ' + MAX + ') \u00b7 Open stack';
    if (n >= MAX) return 'Stack full (4 of 4) \u00b7 Open stack';
    return '+ Add to stack (' + (n + 1) + ' of ' + MAX + ')';
  }
  function paintRow(r) {
    var b = r.el.querySelector('.stk-btn'); if (!b) return;
    b.textContent = rowLabel(r.o);
    b.classList.toggle('stk-in', idx(r.o) > -1 || items.length >= MAX);
    var nw = r.el.querySelector('.stk-new'); if (nw) nw.hidden = seen();
  }
  var build0 = W.trdShare.build;
  W.trdShare.build = function (o) {
    var row = build0.apply(this, arguments);
    try {
      if ((o.kind === 'drop' || o.kind === 'meme') && o.stack !== false && !isVideo(o.file)) {
        var s = { kind: o.kind, id: String(o.id), page: o.page, img: o.igFile || o.file, thumb: o.thumb || o.file,
                  name: o.igFile ? String(o.fileName || '').replace(/\.(\w+)$/, '-4x5.$1') : o.fileName,
                  label: o.label || (o.kind === 'drop' ? 'Q drop #' + o.id : 'Meme ' + o.id) };
        var box = D.createElement('div');
        box.className = 'stk-add';
        box.innerHTML = '<button type="button" class="stk-btn"></button>' +
          '<p class="stk-new"><b>New: stack up to 4.</b> X and Truth Social take 4 pictures per post. Add up to four ' + (o.kind === 'drop' ? 'drops' : 'memes') +
          ' and you get all four images plus their links, ready to post with your own words.</p>';
        row.appendChild(box);
        var r = { el: box, o: s }; rows.push(r); paintRow(r);
        box.querySelector('.stk-btn').addEventListener('click', function () {
          if (idx(s) > -1 || items.length >= MAX) openSheet(); else add(s);
          paintRow(r);
        });
      }
    } catch (e) {}
    return row;
  };

  /* ---------- the tray ---------- */
  function mount(el) {
    if (!el) return;
    var t = D.createElement('div');
    t.className = 'stk-tray'; t.hidden = true;
    t.setAttribute('role', 'region'); t.setAttribute('aria-label', 'Your stack');
    el.appendChild(t); trays.push(t); paintTray(t);
    t.addEventListener('click', function (e) {
      var x = e.target.closest('[data-stk-x]'); if (x) { remove(x.getAttribute('data-stk-x')); return; }
      if (e.target.closest('.stk-open,.stk-th')) openSheet();
    });
  }
  function paintTray(t) {
    t.hidden = !items.length;
    if (!items.length) { t.innerHTML = ''; return; }
    var slots = '';
    for (var i = 0; i < MAX; i++) {
      var it = items[i];
      slots += it ? '<span class="stk-slot"><button type="button" class="stk-th" aria-label="Open stack: ' + esc(it.label) + '"><img src="' + esc(it.thumb) + '" alt="" loading="lazy"></button>' +
        '<button type="button" class="stk-x" data-stk-x="' + esc(k(it)) + '" aria-label="Remove ' + esc(it.label) + ' from the stack">&times;</button></span>' : '<span class="stk-slot stk-empty" aria-hidden="true"></span>';
    }
    t.innerHTML = '<span class="stk-slots">' + slots + '</span><span class="stk-count">Stack ' + items.length + ' / ' + MAX + '</span>' +
      '<button type="button" class="stk-open">Open stack<span class="stk-n"> ' + items.length + '/' + MAX + '</span></button>';
  }

  /* ---------- the sheet ---------- */
  var sheet = null, lastFocus = null;
  function openSheet() {
    lastFocus = D.activeElement;
    if (!sheet) {
      sheet = D.createElement('div');
      sheet.className = 'stk-sheet'; sheet.setAttribute('role', 'dialog'); sheet.setAttribute('aria-modal', 'true'); sheet.setAttribute('aria-labelledby', 'stkTitle');
      D.body.appendChild(sheet);
      sheet.addEventListener('click', onSheet);
      D.addEventListener('keydown', function (e) { if (e.key === 'Escape' && sheet && sheet.classList.contains('open')) closeSheet(); });
    }
    paintSheet();
    sheet.classList.add('open');
    D.documentElement.classList.add('stk-lock');
    var c = sheet.querySelector('.stk-close'); if (c) c.focus({ preventScroll: true });
    track('open');
  }
  function closeSheet() {
    if (!sheet) return;
    sheet.classList.remove('open'); D.documentElement.classList.remove('stk-lock');
    if (lastFocus && lastFocus.focus) try { lastFocus.focus({ preventScroll: true }); } catch (e) {}
  }
  function canShareFiles() { try { return !!(navigator.canShare && navigator.canShare({ files: [new File(['x'], 'x.png', { type: 'image/png' })] })); } catch (e) { return false; } }
  function paintSheet() {
    if (!sheet) return;
    var n = items.length, what = items.every(function (i) { return i.kind === 'drop'; }) ? (n === 1 ? 'drop' : 'drops') : (n === 1 ? 'item' : 'items');
    var body;
    if (!n) {
      body = '<p class="stk-sub">Your stack is empty. Open Share on any drop or meme and tap Add to stack.</p>';
    } else {
      body = '<ol class="stk-steps"><li>Get the images, then attach them to your post.</li><li>Post: the links are already in it, one per line, in this order. Add your own words.</li></ol>' +
        '<ol class="stk-grid">' + items.map(function (it, i) {
          return '<li><a class="stk-img" href="' + esc(it.img) + '" target="_blank" rel="noopener"><img src="' + esc(it.img) + '" alt="' + esc(it.label) + '" loading="lazy"><b>' + (i + 1) + '</b></a>' +
            '<span class="stk-cap">' + esc(it.label) + '</span><button type="button" class="stk-rm" data-stk-x="' + esc(k(it)) + '">Remove</button></li>';
        }).join('') + '</ol>' +
        '<pre class="stk-links" aria-label="The links that go in your post">' + esc(links()) + '</pre>' +
        '<div class="stk-acts">' +
          (canShareFiles() ? '<button type="button" class="stk-a stk-primary" data-stk="share">Share ' + n + ' image' + (n > 1 ? 's' : '') + '</button><button type="button" class="stk-a" data-stk="dl">Download</button>'
                           : '<button type="button" class="stk-a stk-primary" data-stk="dl">Download ' + (n > 1 ? 'all ' + n + ' images' : 'the image') + '</button>') +
          '<button type="button" class="stk-a" data-stk="x">Post on X</button>' +
          '<button type="button" class="stk-a" data-stk="truth">Post on Truth Social</button>' +
          '<button type="button" class="stk-a" data-stk="copy">Copy the links</button>' +
          '<button type="button" class="stk-a stk-quiet" data-stk="clear">Clear stack</button>' +
        '</div><p class="stk-msg" role="status" aria-live="polite"></p>';
    }
    sheet.innerHTML = '<div class="stk-card"><button type="button" class="stk-close" aria-label="Close the stack">&times;</button>' +
      '<h2 id="stkTitle">Your stack: ' + n + ' ' + what + (n < MAX && n ? ' <small>(room for ' + (MAX - n) + ' more)</small>' : '') + '</h2>' + body + '</div>';
  }
  function say(t) { var m = sheet && sheet.querySelector('.stk-msg'); if (m) m.textContent = t; }
  function fetchBlob(u) { return fetch(u, { mode: 'cors', credentials: 'omit' }).then(function (r) { if (!r.ok) throw 0; return r.blob(); }); }
  function saveBlob(b, name) { var a = D.createElement('a'), u = URL.createObjectURL(b); a.href = u; a.download = name; D.body.appendChild(a); a.click(); a.remove(); setTimeout(function () { URL.revokeObjectURL(u); }, 5000); }
  function fname(it, b) { var n = it.name || (it.kind + '-' + it.id); if (!/\.\w{2,4}$/.test(n)) n += '.' + ((b && b.type.split('/')[1]) || 'png'); return n; }
  function download() {
    track('download');
    var list = items.slice(), i = 0, opened = 0;
    say('Downloading ' + list.length + ' image' + (list.length > 1 ? 's' : '') + '...');
    (function next() {
      if (i >= list.length) { say(opened ? 'Your browser held back ' + (opened === list.length ? 'the downloads' : opened + ' of them') + '. Tap each numbered picture above to open it full size, then save it.' : 'Done. Attach the images to your post, then tap Post on X or Truth Social.'); return; }
      var it = list[i++];
      fetchBlob(it.img).then(function (b) { saveBlob(b, fname(it, b)); }, function () { opened++; })
        .then(function () { setTimeout(next, 450); });
    })();
  }
  function shareFiles() {
    track('share-files');
    say('Getting the images...');
    Promise.all(items.map(function (it) { return fetchBlob(it.img).then(function (b) { return new File([b], fname(it, b), { type: b.type || 'image/png' }); }); }))
      .then(function (files) {
        if (!navigator.canShare({ files: files })) throw 0;
        return navigator.share({ files: files, text: links() }).then(function () { say(''); }, function () { say(''); });
      }).catch(function () { download(); });
  }
  function onSheet(e) {
    if (e.target === sheet || e.target.closest('.stk-close')) { closeSheet(); return; }
    var x = e.target.closest('[data-stk-x]'); if (x) { remove(x.getAttribute('data-stk-x')); track('remove'); return; }
    var b = e.target.closest('[data-stk]'); if (!b) return;
    var a = b.getAttribute('data-stk'), en = encodeURIComponent(links());
    if (a === 'dl') download();
    else if (a === 'share') shareFiles();
    else if (a === 'x') { track('post-x'); W.open('https://x.com/intent/tweet?text=' + en, '_blank', 'noopener,width=680,height=640'); say('Attach the images in the X window, add your words above the links, and post.'); }
    else if (a === 'truth') { track('post-truth'); W.open('https://truthsocial.com/share?text=' + en, '_blank', 'noopener,width=680,height=640'); say('Attach the images in Truth Social, add your words above the links, and post.'); }
    else if (a === 'copy') { track('copy'); copy(links()); }
    else if (a === 'clear') { clear(); }
  }
  function copy(t) {
    function ok() { say('Links copied.'); }
    function legacy() { var ta = D.createElement('textarea'); ta.value = t; ta.style.cssText = 'position:fixed;opacity:0;top:0'; D.body.appendChild(ta); ta.select(); try { D.execCommand('copy'); ok(); } catch (e) { say(t); } ta.remove(); }
    try { if (navigator.clipboard && navigator.clipboard.writeText) { navigator.clipboard.writeText(t).then(ok, legacy); return; } } catch (e) {}
    legacy();
  }

  function refresh() {
    trays = trays.filter(function (t) { return D.body.contains(t); });
    rows = rows.filter(function (r) { return D.body.contains(r.el); });
    trays.forEach(paintTray); rows.forEach(paintRow);
    if (sheet && sheet.classList.contains('open')) paintSheet();
  }
  W.addEventListener('storage', function (e) { if (e.key === KEY) { items = load(); refresh(); } });

  W.trdStack = { mount: mount, add: add, remove: remove, clear: clear, items: function () { return items.slice(); }, links: links, open: openSheet, close: closeSheet, MAX: MAX };
})();
