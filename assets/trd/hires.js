/* Ledger full-resolution images: thumbnail strip + deep-zoom viewer (2026-10-30).
   The strip is plain HTML (each card links to the untouched original, so it works without JS).
   On click this file lazy-loads the vendored OpenSeadragon (BSD-3) and opens a full-screen viewer:
   hover lens at full-resolution pixels, wheel/click/pinch zoom, drag pan, keyboard (+ - 0 1 L arrows Esc),
   and a "Download original" button that saves the original file byte-for-byte.
   Deep link: #hires=<slug> opens a viewer on load or hashchange; closing clears the hash (replaceState). */
(function () {
  var OSD_SRC = '/assets/trd/vendor/openseadragon-6.1.1.min.js';
  var BLOB_MAX = 150e6; // above this, let the browser handle the link itself instead of holding it in memory
  var root, viewer, lensViewer, item, lastFocus, osdLoading, lensOn = false, lastPtr = null;
  function $(s, r) { return (r || document).querySelector(s); }
  function fmtBytes(n) { return n >= 1e9 ? (n / 1e9).toFixed(2) + ' GB' : n >= 1e6 ? (n / 1e6).toFixed(1) + ' MB' : Math.round(n / 1e3) + ' KB'; }
  function fmtNum(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ','); }
  function items() { try { return JSON.parse($('#hxData').textContent); } catch (e) { return []; } }
  function loadOSD() {
    if (window.OpenSeadragon) return Promise.resolve();
    if (osdLoading) return osdLoading;
    osdLoading = new Promise(function (ok, bad) { var s = document.createElement('script'); s.src = OSD_SRC; s.onload = ok; s.onerror = bad; document.head.appendChild(s); });
    return osdLoading;
  }
  function build() {
    root = document.createElement('div');
    root.className = 'hxv'; root.hidden = true;
    root.setAttribute('role', 'dialog'); root.setAttribute('aria-modal', 'true');
    root.innerHTML = '<div class="hxv-bar"><div class="hxv-t"><b id="hxvTitle"></b><small id="hxvMeta"></small></div>' +
      '<button type="button" class="hxv-b" data-a="out" aria-label="Zoom out" title="Zoom out (-)">&minus;</button>' +
      '<button type="button" class="hxv-b" data-a="in" aria-label="Zoom in" title="Zoom in (+)">+</button>' +
      '<button type="button" class="hxv-b" data-a="one" title="Actual pixels, 100% (1)">100%</button>' +
      '<button type="button" class="hxv-b" data-a="fit" title="Fit to screen (0)">Fit</button>' +
      '<button type="button" class="hxv-b hxv-lensb" data-a="lens" aria-pressed="false" title="Magnifier lens (L)">Lens</button>' +
      '<a class="hxv-b hxv-dl" data-a="dl" href="#" download>Download original</a>' +
      '<button type="button" class="hxv-b hxv-x" data-a="close" aria-label="Close viewer" title="Close (Esc)">&times;</button></div>' +
      '<div class="hxv-st"><div class="hxv-osd" id="hxvOsd" role="img"></div><div class="hxv-lens" aria-hidden="true"><div id="hxvLens" style="width:100%;height:100%"></div></div>' +
      '<div class="hxv-z" id="hxvZoom" aria-live="polite"></div><div class="hxv-h">Hover for the lens · scroll or pinch to zoom · drag to pan · + / &minus; zoom · 1 actual pixels · Esc close</div></div>';
    root.setAttribute('aria-labelledby', 'hxvTitle');
    document.body.appendChild(root);
    root.addEventListener('click', function (e) {
      var b = e.target.closest('[data-a]'); if (!b) return;
      var a = b.getAttribute('data-a');
      if (a === 'dl') return download(e, b);
      e.preventDefault(); act(a);
    });
    root.addEventListener('keydown', onKey, true);
    var st = $('.hxv-st', root);
    st.addEventListener('pointermove', function (e) { if (e.pointerType !== 'mouse') return; lastPtr = e; moveLens(e); });
    st.addEventListener('pointerleave', function () { lastPtr = null; $('.hxv-lens', root).classList.remove('on'); });
  }
  function act(a) {
    if (a === 'close') return close();
    if (!viewer) return;
    var vp = viewer.viewport;
    if (a === 'in') vp.zoomBy(1.6);
    else if (a === 'out') vp.zoomBy(1 / 1.6);
    else if (a === 'fit') vp.goHome();
    else if (a === 'one') vp.zoomTo(vp.imageToViewportZoom(1));
    else if (a === 'lens') setLens(!lensOn);
    vp.applyConstraints();
  }
  function setLens(on) {
    lensOn = on; var b = $('[data-a="lens"]', root); if (b) b.setAttribute('aria-pressed', on ? 'true' : 'false');
    if (!on) $('.hxv-lens', root).classList.remove('on'); else if (lastPtr) moveLens(lastPtr);
  }
  function moveLens(e) {
    var lens = $('.hxv-lens', root);
    if (!lensOn || !viewer || !lensViewer || !lensViewer.world.getItemCount()) return lens.classList.remove('on');
    var st = $('.hxv-st', root).getBoundingClientRect(), x = e.clientX - st.left, y = e.clientY - st.top;
    var vpPt = viewer.viewport.viewerElementToViewportCoordinates(new OpenSeadragon.Point(x, y));
    var img = viewer.world.getItemAt(0).viewportToImageCoordinates(vpPt);
    if (img.x < 0 || img.y < 0 || img.x > item.width || img.y > item.height) return lens.classList.remove('on');
    lens.classList.add('on');
    lens.style.left = (x - 140) + 'px'; lens.style.top = (y - 140) + 'px';
    var cur = viewer.viewport.viewportToImageZoom(viewer.viewport.getZoom(true));
    var z = Math.min(4, Math.max(1, cur * 3)); // lens never shows less than 1 screen px per image px
    var lv = lensViewer.viewport;
    lv.zoomTo(lv.imageToViewportZoom(z), null, true); lv.panTo(vpPt, true);
  }
  function onKey(e) {
    var k = e.key, h = true;
    if (k === 'Escape') close();
    else if (k === '+' || k === '=') act('in');
    else if (k === '-' || k === '_') act('out');
    else if (k === '0') act('fit');
    else if (k === '1') act('one');
    else if (k === 'l' || k === 'L') act('lens');
    else if (/^Arrow/.test(k) && viewer) { var d = 0.1 / viewer.viewport.getZoom(); viewer.viewport.panBy(new OpenSeadragon.Point(k === 'ArrowLeft' ? -d : k === 'ArrowRight' ? d : 0, k === 'ArrowUp' ? -d : k === 'ArrowDown' ? d : 0)); }
    else if (k === 'Tab') { var f = [].slice.call(root.querySelectorAll('.hxv-bar .hxv-b')).filter(function (x) { return x.offsetParent; }); var i = f.indexOf(document.activeElement); if (e.shiftKey && i <= 0) { f[f.length - 1].focus(); } else if (!e.shiftKey && i === f.length - 1) { f[0].focus(); } else h = false; }
    else h = false;
    if (h) { e.preventDefault(); e.stopPropagation(); }
  }
  function zoomLabel() {
    if (!viewer || !viewer.world.getItemCount()) return;
    var z = viewer.viewport.viewportToImageZoom(viewer.viewport.getZoom(true));
    $('#hxvZoom').textContent = (z >= 0.995 && z <= 1.005 ? '100' : (z * 100).toFixed(z < 0.1 ? 1 : 0)) + '% · ' + (z >= 1 ? 'full resolution' : 'zoom in for full detail');
  }
  function download(e, a) {
    if (!window.fetch || !window.URL || item.bytes > BLOB_MAX) return; // plain link
    e.preventDefault();
    if (a.getAttribute('aria-busy') === 'true') return;
    var label = a.innerHTML; a.setAttribute('aria-busy', 'true'); a.textContent = 'Preparing download…';
    fetch(a.href, { mode: 'cors' }).then(function (r) { if (!r.ok) throw r.status; return r.blob(); }).then(function (b) {
      var u = URL.createObjectURL(b), t = document.createElement('a'); t.href = u; t.download = item.file; document.body.appendChild(t); t.click(); t.remove();
      setTimeout(function () { URL.revokeObjectURL(u); }, 60000);
    }).catch(function () { window.location.href = a.href; }).then(function () { a.innerHTML = label; a.removeAttribute('aria-busy'); });
  }
  function fallback(stage) {
    var big = item.bytes > 30e6, src = big ? item.base + 'preview.jpg' : item.original;
    stage.innerHTML = '<div class="hxv-fb"><img alt="' + item.alt.replace(/"/g, '&quot;') + '" src="' + src + '"></div>';
  }
  function open(it, from) {
    item = it; lastFocus = from || document.activeElement;
    if (!root) build();
    $('#hxvTitle').textContent = it.name;
    $('#hxvMeta').textContent = it.format + ' · ' + fmtNum(it.width) + ' × ' + fmtNum(it.height) + ' px · ' + fmtBytes(it.bytes) + ' · free to download';
    var dl = $('[data-a="dl"]', root); dl.href = it.original; dl.setAttribute('download', it.file);
    dl.innerHTML = 'Download original<span class="hxv-dd">&nbsp;(' + fmtBytes(it.bytes) + ', ' + fmtNum(it.width) + ' × ' + fmtNum(it.height) + ' px)</span>';
    dl.setAttribute('aria-label', 'Download original ' + it.file + ', ' + fmtBytes(it.bytes) + ', ' + fmtNum(it.width) + ' by ' + fmtNum(it.height) + ' pixels');
    var stage = $('#hxvOsd'); stage.setAttribute('aria-label', it.alt);
    root.hidden = false; document.documentElement.style.overflow = 'hidden';
    $('[data-a="close"]', root).focus();
    setLens(window.matchMedia && matchMedia('(hover:hover) and (pointer:fine)').matches);
    loadOSD().then(function () {
      if (viewer) { viewer.destroy(); viewer = null; } if (lensViewer) { lensViewer.destroy(); lensViewer = null; }
      stage.innerHTML = '';
      var common = { tileSources: it.base + it.slug + '.dzi', drawer: 'canvas', crossOriginPolicy: false, showNavigationControl: false, visibilityRatio: 0.5 };
      viewer = OpenSeadragon(Object.assign({ element: stage, maxZoomPixelRatio: 4, minZoomImageRatio: 0.8, animationTime: 0.6, zoomPerScroll: 1.4,
        gestureSettingsMouse: { clickToZoom: true, dblClickToZoom: false, scrollToZoom: true }, gestureSettingsTouch: { pinchToZoom: true, flickEnabled: true },
        showNavigator: true, navigatorPosition: 'TOP_RIGHT', navigatorSizeRatio: 0.14 }, common));
      lensViewer = OpenSeadragon(Object.assign({ element: $('#hxvLens'), mouseNavEnabled: false, maxZoomPixelRatio: 8, immediateRender: true, blendTime: 0, animationTime: 0, minZoomImageRatio: 0 }, common));
      viewer.addHandler('animation', zoomLabel); viewer.addHandler('open', zoomLabel);
      viewer.addHandler('open-failed', function () { fallback(stage); });
      window.trdHires.viewer = viewer; window.trdHires.lens = lensViewer;
    }, function () { fallback(stage); });
  }
  function close() {
    if (!root || root.hidden) return;
    root.hidden = true; document.documentElement.style.overflow = '';
    if (viewer) { viewer.destroy(); viewer = null; } if (lensViewer) { lensViewer.destroy(); lensViewer = null; }
    $('#hxvOsd').innerHTML = ''; $('#hxvZoom').textContent = '';
    if (lastFocus && lastFocus.focus) lastFocus.focus();
    if (HASH.test(location.hash) && window.history && history.replaceState) history.replaceState(history.state, '', location.pathname + location.search);
  }
  // Deep links: /ledger.html#hires=<slug> opens that viewer (used by the app menu); closing clears the hash without a reload.
  var HASH = /^#hires=([A-Za-z0-9_-]+)$/;
  function fromHash() {
    var m = HASH.exec(location.hash); if (!m) return;
    var it = items().filter(function (x) { return x.slug === m[1]; })[0]; if (!it) return;
    if (root && !root.hidden && item === it) return;
    open(it, document.querySelector('[data-hx="' + it.slug + '"]'));
  }
  window.addEventListener('hashchange', fromHash);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fromHash); else fromHash();
  document.addEventListener('click', function (e) {
    var c = e.target.closest && e.target.closest('[data-hx]'); if (!c || e.ctrlKey || e.metaKey || e.shiftKey || e.button) return;
    var it = items().filter(function (x) { return x.slug === c.getAttribute('data-hx'); })[0]; if (!it) return;
    e.preventDefault(); open(it, c);
  });
  window.trdHires = { open: function (slug) { var it = items().filter(function (x) { return x.slug === slug; })[0]; if (it) open(it); }, close: close };
})();
