/* The Duck Pod: a site-wide player for The Red Pill Album by The Rubber Duck.
   - One <audio> element that lives for the whole visit.
   - A small soft-navigation router: internal links fetch the next page and swap
     head styles + body content, so the pod and its audio are never torn down.
   - Heavy app pages (and anything the router cannot run safely) load normally;
     the pod then resumes the saved track and position from localStorage.
   Include once per page, in <head>:
     <link rel="stylesheet" href="/assets/trd/duckpod.css" data-trd-keep>
     <script src="/assets/trd/duckpod.js" data-trd-keep></script>          */
(function () {
  'use strict';
  var W = window, D = document;
  if (W.trdPod) return;

  /* ================= album ================= */
  var ALBUM = 'The Red Pill Album', ARTIST = 'The Rubber Duck';
  var COVER = '/assets/trd/img/red-pill-cover-192.jpg';
  var COVER_BIG = '/images/opt/album-cover-card.jpg';
  var TRACKS = [
    ['01-and-frogs-to-destroy-them', 'And Frogs To Destroy Them', '2:36'],
    ['02-boom-boom-boom', 'Boom, Boom, Boom', '3:23'],
    ['03-dark-to-light', 'Dark to Light', '2:50'],
    ['04-enjoy-the-show', 'Enjoy The Show', '4:46'],
    ['05-follow-marina-abramovic', 'Follow Marina Abramovic', '3:03'],
    ['06-full-control', 'Full Control', '3:19'],
    ['07-god-wins', 'GOD WINS', '2:39'],
    ['08-military-intelligence', 'Military Intelligence', '3:38'],
    ['09-mockingbird', 'Mockingbird', '4:56'],
    ['10-q-clearance-patriot', 'Q Clearance Patriot', '6:04'],
    ['11-shall-we-play-a-game', 'Shall We Play a Game', '2:48'],
    ['12-the-storm-is-upon-us', 'The Storm Is Upon Us', '2:51'],
    ['13-there-is-no-qanon', 'There is no Qanon', '3:37'],
    ['14-trumpxiputin-trump-zee-pootin', 'Trumpxiputin (trump-zee-pootin)', '3:49'],
    ['15-very-dangerous-animal', 'Very Dangerous Animal', '4:33'],
    ['16-welcome-to-epstein-island', 'Welcome To Epstein Island', '3:24'],
    ['17-what-happened-to-diana', 'What happened to Diana', '3:54'],
    ['18-what-makes-a-movie-good', 'What makes a movie GOOD', '3:04'],
    ['19-who-follows-satan', 'Who Follows Satan', '2:31'],
    ['20-who-is-rachel-c-handler', 'Who is Rachel (C)handler', '3:24'],
    ['21-wizards-warlocks', 'Wizards & Warlocks', '3:44'],
    ['22-alice-in-wonderland', 'Alice in Wonderland', '6:26']
  ].map(function (t) { var p = t[2].split(':'); return { src: '/audio/' + t[0] + '.mp3', title: t[1], len: t[2], secs: (+p[0]) * 60 + (+p[1]) }; });
  var N = TRACKS.length;

  /* ================= keep originals before any page script runs ================= */
  var EP = EventTarget.prototype;
  var addL = EP.addEventListener, remL = EP.removeEventListener;
  var _setTimeout = W.setTimeout.bind(W), _clearTimeout = W.clearTimeout.bind(W);
  var _setInterval = W.setInterval.bind(W), _clearInterval = W.clearInterval.bind(W);
  var _raf = W.requestAnimationFrame ? W.requestAnimationFrame.bind(W) : function (f) { return _setTimeout(f, 16); };
  function on(t, type, fn, o) { addL.call(t, type, fn, o); }

  /* ================= storage ================= */
  var KEY = 'trdPod.v1', HINT_KEY = 'trdPod.hinted';
  var S = { i: 0, t: 0, playing: false, started: false, view: 'mini', back: 'mini', vol: 1, clicker: true, pos: null, at: 0 };
  try { var saved = JSON.parse(localStorage.getItem(KEY) || 'null'); if (saved) for (var k in S) if (k in saved) S[k] = saved[k]; } catch (e) {}
  if (!(S.i >= 0 && S.i < N)) S.i = 0;
  if (['mini', 'full', 'pill'].indexOf(S.view) < 0) S.view = 'mini';
  function save() { try { S.at = Date.now(); localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} }

  /* ================= page-scope sandbox for soft navigation =================
     Listeners, timers and observers created by page scripts are recorded so the
     next soft navigation can clean them up (the page they belonged to is gone). */
  var epoch = 0, tracked = [], intervals = [], observers = [], runningScripts = false;
  /* Only code from this site's pages is sandboxed. Anything else running in the
     window (browser extensions, analytics from other origins, test tools) keeps
     its listeners and timers untouched. */
  var ORIGIN = location.origin + '/';
  function fromPage() {
    if (runningScripts) return true;
    var st = (new Error()).stack || '', lines = st.split('\n');
    for (var n = 1; n < lines.length; n++) {
      var ln = lines[n];
      if (ln.indexOf('duckpod.js') >= 0) continue;
      if (ln.indexOf(ORIGIN) >= 0) return true;
    }
    return false;
  }
  function wrapAdd(target) {
    target.addEventListener = function (type, fn, opts) {
      if (runningScripts && fn && ((target === D && type === 'DOMContentLoaded') || (target === W && type === 'load'))) {
        var f = fn; _setTimeout(function () { try { typeof f === 'function' ? f.call(target, new Event(type)) : f.handleEvent(new Event(type)); } catch (err) { console.error(err); } }, 0);
        return;
      }
      if (fromPage()) tracked.push([target, type, fn, opts]);
      return addL.call(target, type, fn, opts);
    };
  }
  wrapAdd(W); wrapAdd(D);
  W.setTimeout = function (fn, ms) {
    if (typeof fn !== 'function' || !fromPage()) return _setTimeout.apply(W, arguments);
    var e = epoch, args = [].slice.call(arguments, 2);
    return _setTimeout(function () { if (e === epoch) fn.apply(W, args); }, ms);
  };
  W.setInterval = function () {
    var id = _setInterval.apply(W, arguments); if (fromPage()) intervals.push(id); return id;
  };
  W.requestAnimationFrame = function (fn) {
    if (!fromPage()) return _raf(fn);
    var e = epoch; return _raf(function (ts) { if (e === epoch) fn(ts); });
  };
  ['IntersectionObserver', 'MutationObserver', 'ResizeObserver'].forEach(function (name) {
    var Orig = W[name]; if (!Orig) return;
    var Wrapped = function (cb, o) { var ob = new Orig(cb, o); if (fromPage()) observers.push(ob); return ob; };
    Wrapped.prototype = Orig.prototype;
    try { W[name] = Wrapped; } catch (e) {}
  });
  function leavePage() {
    epoch++;
    tracked.forEach(function (l) { try { remL.call(l[0], l[1], l[2], l[3]); } catch (e) {} });
    tracked = [];
    intervals.forEach(function (id) { _clearInterval(id); }); intervals = [];
    observers.forEach(function (o) { try { o.disconnect(); } catch (e) {} }); observers = [];
  }

  /* ================= helpers ================= */
  function fmt(s) { s = Math.max(0, Math.floor(s || 0)); return Math.floor(s / 60) + ':' + ('0' + (s % 60)).slice(-2); }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function svg(d, vb) { return '<svg viewBox="' + (vb || '0 0 24 24') + '" aria-hidden="true" focusable="false"><path fill="currentColor" d="' + d + '"/></svg>'; }
  var I = {
    play: 'M8 5.14v13.72a.5.5 0 0 0 .77.42l10.28-6.86a.5.5 0 0 0 0-.84L8.77 4.72A.5.5 0 0 0 8 5.14Z',
    pause: 'M7 4h3.4v16H7zM13.6 4H17v16h-3.4z',
    pp: 'M1 2v12l8-6zM12 2h3v12h-3zM17 2h3v12h-3z',
    prev: 'M2 2h2.5v12H2zM13 2v12L5 8zM21 2v12l-8-6z',
    next: 'M11 2v12l8-6zM3 2v12l8-6zM19.5 2H22v12h-2.5z',
    up: 'M12 7.5l7 7-1.6 1.6-5.4-5.4-5.4 5.4L5 14.5z',
    down: 'M12 16.5l-7-7 1.6-1.6 5.4 5.4 5.4-5.4L19 9.5z',
    move: 'M12 2l3.2 3.2-1.4 1.4L13 5.8V11h5.2l-.8-.8 1.4-1.4L22 12l-3.2 3.2-1.4-1.4.8-.8H13v5.2l.8-.8 1.4 1.4L12 22l-3.2-3.2 1.4-1.4.8.8V13H5.8l.8.8-1.4 1.4L2 12l3.2-3.2 1.4 1.4-.8.8H11V5.8l-.8.8-1.4-1.4z',
    pill: 'M8.5 4.5a5 5 0 0 1 7.07 0l4 4a5 5 0 0 1-7.07 7.07l-4-4a5 5 0 0 1 0-7.07Zm1.41 1.41a3 3 0 0 0 0 4.24L11.76 12 16 7.76l-1.85-1.85a3 3 0 0 0-4.24 0Z',
    volLo: 'M3 9h4l5-4v14l-5-4H3z',
    volHi: 'M3 9h4l5-4v14l-5-4H3zM15 8.5a5 5 0 0 1 0 7l-1.4-1.4a3 3 0 0 0 0-4.2zM17.8 5.7a9 9 0 0 1 0 12.6l-1.4-1.4a7 7 0 0 0 0-9.8z'
  };

  /* ================= click sound + haptics ================= */
  var actx = null, lastBuzz = 0;
  function clickSound(kind) {
    if (!S.clicker) return;
    try {
      var A = W.AudioContext || W.webkitAudioContext; if (!A) return;
      actx = actx || new A();
      if (actx.state === 'suspended') actx.resume();
      var sr = actx.sampleRate, len = Math.floor(sr * (kind === 'press' ? 0.006 : 0.0025));
      var buf = actx.createBuffer(1, len, sr), d = buf.getChannelData(0);
      for (var n = 0; n < len; n++) d[n] = (Math.random() * 2 - 1) * Math.pow(1 - n / len, 4);
      var src = actx.createBufferSource(), hp = actx.createBiquadFilter(), g = actx.createGain();
      src.buffer = buf; hp.type = 'highpass'; hp.frequency.value = kind === 'press' ? 1400 : 2600;
      g.gain.value = kind === 'press' ? 0.22 : 0.16;
      src.connect(hp); hp.connect(g); g.connect(actx.destination); src.start();
    } catch (e) {}
    var now = Date.now();
    if (now - lastBuzz > 35) { lastBuzz = now; try { navigator.vibrate && navigator.vibrate(5); } catch (e) {} }
  }

  /* ================= audio ================= */
  var audio = D.createElement('audio');
  audio.preload = 'none';
  audio.volume = Math.max(0, Math.min(1, S.vol));
  var pendingSeek = null, loadSeq = 0, countedSeq = -1;
  function loadTrack(i, t) {
    S.i = (i + N) % N; S.t = t || 0; loadSeq++;
    audio.src = TRACKS[S.i].src;
    pendingSeek = S.t > 0 ? S.t : null;
    setMedia();
  }
  on(audio, 'loadedmetadata', function () {
    if (pendingSeek != null) { try { audio.currentTime = Math.min(pendingSeek, Math.max(0, audio.duration - 1)); } catch (e) {} pendingSeek = null; }
    render();
  });
  function play() {
    if (!S.started) { S.started = true; if (!audio.getAttribute('src')) loadTrack(S.i, S.t); }
    if (!audio.getAttribute('src')) loadTrack(S.i, S.t);
    hush();
    var p = audio.play();
    if (p && p.catch) p.catch(function () { S.playing = false; render(); save(); });
  }
  function pause() { audio.pause(); }
  function toggle() { if (audio.paused) play(); else pause(); }
  function playIndex(i) { S.started = true; loadTrack(i, 0); play(); }
  function toggleIndex(i) { if (S.started && i === S.i && audio.getAttribute('src')) toggle(); else playIndex(i); }
  function next() { var was = !audio.paused || !S.started; playIndex2(S.i + 1, was); }
  function prev() {
    if (audio.currentTime > 3) { audio.currentTime = 0; if (!S.started) play(); return; }
    playIndex2(S.i - 1, !audio.paused || !S.started);
  }
  function playIndex2(i, autoplay) { S.started = true; loadTrack(i, 0); if (autoplay) play(); else render(); save(); }
  on(audio, 'play', function () { S.playing = true; render(); save(); countPlay(); });
  /* one GoatCounter event each time a track starts from the top (not on pause/resume or a resumed reload) */
  function countPlay() {
    try {
      var at = pendingSeek != null ? pendingSeek : audio.currentTime;
      if (countedSeq === loadSeq || at >= 2 || !W.trdTrack) return;
      countedSeq = loadSeq;
      var n = S.i + 1, t = TRACKS[S.i].title;
      W.trdTrack('event/album-track/' + (n < 10 ? '0' : '') + n + '-' + W.trdTrack.slug(t, 40), 'Red Pill Album: ' + n + '. ' + t, 0);
    } catch (e) {}
  }
  on(audio, 'pause', function () { if (!audio.ended) { S.playing = false; S.t = audio.currentTime; render(); save(); } });
  on(audio, 'ended', function () {
    if (S.i + 1 < N) playIndex(S.i + 1);
    else { loadTrack(0, 0); S.playing = false; render(); save(); }
  });
  var lastSave = 0;
  on(audio, 'timeupdate', function () {
    if (pendingSeek != null) return;
    S.t = audio.currentTime; tick(); var now = Date.now();
    if (now - lastSave > 1000) { lastSave = now; save(); }
  });
  on(W, 'pagehide', function () { if (audio.getAttribute('src') && pendingSeek == null) S.t = audio.currentTime; save(); });
  on(D, 'visibilitychange', function () { if (D.visibilityState === 'hidden') { if (audio.getAttribute('src') && pendingSeek == null) S.t = audio.currentTime; save(); } });

  /* other sound on the page: whichever media the visitor starts last wins */
  function hush() {
    [].forEach.call(D.querySelectorAll('video,audio'), function (m) { if (m !== audio && !m.paused && !m.muted) m.muted = true; });
  }
  function otherMedia(e) {
    var m = e.target;
    if (!m || m === audio || !/^(VIDEO|AUDIO)$/.test(m.nodeName)) return;
    if (!m.paused && !m.muted && m.volume > 0 && !audio.paused) pause();
  }
  on(D, 'play', otherMedia, true); on(D, 'volumechange', otherMedia, true);

  /* Media Session: lock screen / headset controls */
  function setMedia() {
    if (!('mediaSession' in navigator) || !W.MediaMetadata) return;
    try {
      navigator.mediaSession.metadata = new MediaMetadata({ title: TRACKS[S.i].title, artist: ARTIST, album: ALBUM,
        artwork: [{ src: COVER, sizes: '192x192', type: 'image/jpeg' }, { src: COVER_BIG, sizes: '1200x1200', type: 'image/jpeg' }] });
    } catch (e) {}
  }
  if ('mediaSession' in navigator) {
    try {
      navigator.mediaSession.setActionHandler('play', play);
      navigator.mediaSession.setActionHandler('pause', pause);
      navigator.mediaSession.setActionHandler('previoustrack', prev);
      navigator.mediaSession.setActionHandler('nexttrack', next);
    } catch (e) {}
  }

  /* ================= UI ================= */
  var root, dock, els = {}, screen = 'intro', sel = 0, scrub = false, volTimer = 0;
  function build() {
    root = D.createElement('div');
    root.id = 'trd-pod';
    root.setAttribute('data-trd-keep', '');
    var trackLis = TRACKS.map(function (t, i) { return '<li data-i="' + i + '" role="option"><span>' + esc(t.title) + '</span><em>' + t.len + '</em></li>'; }).join('');
    root.innerHTML =
      '<div class="tp-dock">' +
        '<div class="tp-hint" aria-hidden="true">' + svg(I.move) + 'Drag me anywhere</div>' +
        /* full device */
        '<section class="tp-device tp-shell" aria-label="The Duck Pod: The Red Pill Album player">' +
          '<div class="tp-top">' +
            '<button class="tp-tool tp-to-mini" type="button" aria-label="Collapse player" title="Collapse">' + svg(I.down) + '</button>' +
            '<div class="tp-grip tp-grab" title="Drag to move. Double-tap to reset.">' + '<span class="tp-move">' + svg(I.move) + '</span><i></i></div>' +
            '<button class="tp-tool tp-to-pill" type="button" aria-label="Minimize player" title="Minimize">' + svg(I.pill) + '</button>' +
          '</div>' +
          '<div class="tp-bezel"><div class="tp-screen">' +
            '<div class="tp-hdr"><span class="tp-st"></span><b class="tp-hdr-t">Now Playing</b><span class="tp-batt" aria-hidden="true"></span></div>' +
            '<div class="tp-view tp-v-intro"><img class="tp-cover" src="' + COVER + '" alt="" width="56" height="56">' +
              '<p class="tp-intro-t" style="margin-bottom:0">Play The Red Pill Album</p><p class="tp-intro-s" style="margin-bottom:0">22 tracks by The Rubber Duck</p></div>' +
            '<div class="tp-view tp-v-now">' +
              '<div class="tp-count"></div>' +
              '<div class="tp-np"><img class="tp-cover" src="' + COVER + '" alt="" width="52" height="52">' +
                '<div class="tp-meta"><div class="tp-mq tp-title"><span></span></div><div class="tp-artist">The Rubber Duck</div><div class="tp-album">' + ALBUM + '</div></div></div>' +
              '<div class="tp-progrow"><div class="tp-prog-wrap"><div class="tp-prog"><i></i><span class="tp-knob"></span></div>' +
                '<div class="tp-times"><span class="tp-el">0:00</span><span class="tp-rem">-0:00</span></div></div>' +
                '<div class="tp-volrow">' + svg(I.volLo) + '<div class="tp-prog"><i class="tp-voli"></i></div>' + svg(I.volHi) + '</div></div>' +
            '</div>' +
            '<div class="tp-view tp-v-menu"><ul class="tp-list" role="listbox" aria-label="Tracks">' + trackLis +
              '<li data-i="clicker" role="option"><span class="tp-clk">Clicker</span><em class="tp-clkv"></em></li></ul></div>' +
          '</div></div>' +
          '<div class="tp-wheel" role="group" aria-label="Click wheel. Turn to change volume or scroll.">' +
            '<button class="tp-w tp-w-menu" type="button" aria-label="Menu: track list">MENU</button>' +
            '<button class="tp-w tp-w-prev" type="button" aria-label="Previous track">' + svg(I.prev, '0 0 23 16') + '</button>' +
            '<button class="tp-w tp-w-next" type="button" aria-label="Next track">' + svg(I.next, '0 0 23 16') + '</button>' +
            '<button class="tp-w tp-w-pp" type="button" aria-label="Play or pause">' + svg(I.pp, '0 0 21 16') + '</button>' +
            '<button class="tp-center" type="button" aria-label="Select"></button>' +
          '</div>' +
        '</section>' +
        /* mini strip */
        '<section class="tp-strip tp-shell tp-grab" aria-label="The Red Pill Album player">' +
          '<div class="tp-sgrip" title="Drag to move. Double-tap to reset."><span class="tp-move">' + svg(I.move) + '</span><i></i></div>' +
          '<div class="tp-disc"><button class="tp-mini-btn" type="button" aria-label="Play The Red Pill Album"></button></div>' +
          '<div class="tp-lcd" role="button" tabindex="0" aria-label="Open the full player">' +
            '<img class="tp-cover" src="' + COVER + '" alt="" width="36" height="36">' +
            '<div class="tp-meta"><div class="tp-mq tp-title"><span></span></div><div class="tp-album"></div></div>' +
            '<div class="tp-sprog"><i></i></div></div>' +
          '<div class="tp-stools">' +
            '<button class="tp-tool tp-to-full" type="button" aria-label="Open the full player" title="Open">' + svg(I.up) + '</button>' +
            '<button class="tp-tool tp-to-pill" type="button" aria-label="Minimize player" title="Minimize">' + svg(I.pill) + '</button>' +
          '</div>' +
        '</section>' +
        /* minimized */
        '<button class="tp-pill tp-grab" type="button" aria-label="Open The Red Pill Album player"><span class="tp-pill-cap"></span></button>' +
      '</div>';
    root.insertBefore(audio, root.firstChild);
    dock = root.querySelector('.tp-dock');
    function q(s) { return root.querySelector(s); }
    function qa(s) { return [].slice.call(root.querySelectorAll(s)); }
    els = {
      st: q('.tp-st'), hdr: q('.tp-hdr-t'), count: q('.tp-count'), titles: qa('.tp-title'), titleSpans: qa('.tp-title span'),
      fill: q('.tp-prog-wrap .tp-prog i'), knob: q('.tp-knob'), el: q('.tp-el'), rem: q('.tp-rem'), voli: q('.tp-voli'),
      list: q('.tp-list'), lis: qa('.tp-list li'), clkv: q('.tp-clkv'), wheel: q('.tp-wheel'), center: q('.tp-center'),
      miniBtn: q('.tp-mini-btn'), sAlbum: q('.tp-lcd .tp-album'), sfill: q('.tp-sprog i'), lcd: q('.tp-lcd')
    };
    wire();
    D.body.appendChild(root);
    setView(S.view, true);
    render();
    applyPos();
    maybeHint();
  }
  function attach() {
    if (!root) return;
    if (root.parentNode !== D.body || root !== D.body.lastElementChild) D.body.appendChild(root);
  }

  function setView(v, quiet) {
    if (v !== 'pill') S.back = v;
    S.view = v; root.setAttribute('data-view', v);
    if (!quiet) { save(); _raf(applyPos); }
  }
  function setScreen(s) {
    screen = s; root.setAttribute('data-screen', s);
    scrub = false; root.classList.remove('tp-scrub');
    if (s === 'menu') { sel = S.i; drawMenu(); }
    renderHeader();
  }

  function renderHeader() {
    els.hdr.textContent = screen === 'menu' ? ALBUM : (screen === 'intro' ? 'The Duck Pod' : 'Now Playing');
    els.st.innerHTML = S.playing ? svg(I.play) : (S.started ? svg(I.pause) : '');
  }
  function marquee() {
    els.titles.forEach(function (box) {
      var span = box.firstChild; box.classList.remove('tp-run');
      var over = span.scrollWidth - box.clientWidth;
      if (over > 2 && box.offsetParent) {
        box.style.setProperty('--tp-mqx', -(over + 6) + 'px');
        box.style.setProperty('--tp-mqd', Math.max(6, over / 12 + 5) + 's');
        box.classList.add('tp-run');
      }
    });
  }
  var lastTitle = '';
  function render() {
    if (!root) return;
    var t = TRACKS[S.i];
    root.classList.toggle('tp-playing', S.playing);
    if (!S.started && screen !== 'menu') setScreen('intro');
    else if (S.started && screen === 'intro') setScreen('now');
    renderHeader();
    var title = S.started ? t.title : 'Play The Red Pill Album';
    if (title !== lastTitle) { lastTitle = title; els.titleSpans.forEach(function (s) { s.textContent = title; }); _raf(marquee); }
    els.count.textContent = (S.i + 1) + ' of ' + N;
    els.sAlbum.textContent = S.started ? ALBUM + '  \u00b7  ' + (S.i + 1) + ' of ' + N : '22 tracks by The Rubber Duck';
    els.miniBtn.innerHTML = svg(S.playing ? I.pause : I.play);
    els.miniBtn.setAttribute('aria-label', S.playing ? 'Pause' : (S.started ? 'Play ' + t.title : 'Play The Red Pill Album'));
    els.lis.forEach(function (li, i) { li.classList.toggle('tp-cur', S.started && i === S.i); });
    els.clkv.textContent = S.clicker ? 'On' : 'Off';
    syncDoor();
    tick();
    emit();
  }
  function dur() { return isFinite(audio.duration) && audio.duration > 0 ? audio.duration : TRACKS[S.i].secs; }
  function cur() { return pendingSeek != null ? pendingSeek : (audio.getAttribute('src') ? audio.currentTime : S.t); }
  function tick() {
    if (!root) return;
    var d = dur(), c = cur(), pct = Math.min(100, (c / d) * 100) + '%';
    els.fill.style.width = pct; els.knob.style.left = pct; els.sfill.style.width = S.started ? pct : '0%';
    els.el.textContent = fmt(c); els.rem.textContent = '-' + fmt(d - c);
    emitSoon();
  }
  var emitQueued = false;
  function emitSoon() { if (emitQueued) return; emitQueued = true; _raf(function () { emitQueued = false; emit(); }); }
  function state() { return { i: S.i, title: TRACKS[S.i].title, playing: S.playing, started: S.started, t: cur(), d: dur(), view: S.view }; }
  function emit() { try { D.dispatchEvent(new CustomEvent('trdpod:state', { detail: state() })); } catch (e) {} }

  function drawMenu() {
    els.lis.forEach(function (li, i) { li.classList.toggle('tp-sel', i === sel); li.setAttribute('aria-selected', i === sel ? 'true' : 'false'); });
    var li = els.lis[sel], box = els.list;
    if (li) { var top = li.offsetTop, h = li.offsetHeight; if (top < box.scrollTop) box.scrollTop = top; else if (top + h > box.scrollTop + box.clientHeight) box.scrollTop = top + h - box.clientHeight; }
  }
  function showVol() {
    root.classList.add('tp-vol'); els.voli.style.width = (audio.volume * 100) + '%';
    _clearTimeout(volTimer); volTimer = _setTimeout(function () { root.classList.remove('tp-vol'); }, 1600);
  }

  /* one notch of the wheel: dir = +1 clockwise, -1 counter-clockwise */
  function notch(dir) {
    clickSound('tick');
    if (screen === 'menu') { sel = Math.max(0, Math.min(els.lis.length - 1, sel + dir)); drawMenu(); return; }
    if (scrub && S.started) {
      var d = dur(), t = Math.max(0, Math.min(d - 0.5, cur() + dir * Math.max(3, d / 60)));
      if (audio.getAttribute('src') && pendingSeek == null) audio.currentTime = t; else { S.t = t; pendingSeek = t; }
      tick(); return;
    }
    audio.volume = Math.max(0, Math.min(1, Math.round((audio.volume + dir * 0.0625) * 16) / 16));
    S.vol = audio.volume; save(); showVol();
  }
  function select() {
    clickSound('press');
    if (screen === 'menu') {
      var li = els.lis[sel]; if (!li) return;
      if (li.getAttribute('data-i') === 'clicker') { S.clicker = !S.clicker; save(); render(); return; }
      playIndex(+li.getAttribute('data-i')); setScreen('now'); return;
    }
    if (screen === 'intro') { play(); return; }
    scrub = !scrub; root.classList.toggle('tp-scrub', scrub);
  }
  function menu() {
    clickSound('press');
    setScreen(screen === 'menu' ? (S.started ? 'now' : 'intro') : 'menu');
  }

  /* ================= wiring ================= */
  var suppressUntil = 0;
  function guard(fn) { return function (e) { if (Date.now() < suppressUntil) { e.preventDefault(); return; } fn(e); }; }
  function wire() {
    function bind(sel, fn) { [].forEach.call(root.querySelectorAll(sel), function (b) { on(b, 'click', guard(fn)); }); }
    bind('.tp-w-menu', menu);
    bind('.tp-w-prev', function () { clickSound('press'); prev(); });
    bind('.tp-w-next', function () { clickSound('press'); next(); });
    bind('.tp-w-pp', function () { clickSound('press'); toggle(); });
    bind('.tp-center', select);
    bind('.tp-mini-btn', function () { clickSound('press'); toggle(); });
    bind('.tp-to-full', function () { clickSound('press'); setView('full'); });
    bind('.tp-to-mini', function () { clickSound('press'); setView('mini'); });
    bind('.tp-to-pill', function () { clickSound('press'); setView('pill'); });
    /* pointer taps on the pill are handled by the drag code; this covers the keyboard */
    bind('.tp-pill', function (e) { if (e.detail !== 0) return; clickSound('press'); setView(S.back === 'full' ? 'full' : 'mini'); });
    on(els.lcd, 'keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setView('full'); } });
    on(els.list, 'click', guard(function (e) {
      var li = e.target.closest('li'); if (!li) return;
      sel = els.lis.indexOf(li); drawMenu(); select();
    }));

    /* turning the wheel */
    var wheel = els.wheel, turning = null;
    function ang(e) { var r = wheel.getBoundingClientRect(); return Math.atan2(e.clientY - (r.top + r.height / 2), e.clientX - (r.left + r.width / 2)) * 180 / Math.PI; }
    on(wheel, 'pointerdown', function (e) {
      if (e.button > 0 || e.target.closest('.tp-center')) return;
      turning = { id: e.pointerId, a: ang(e), acc: 0, total: 0, captured: false };
    });
    on(wheel, 'pointermove', function (e) {
      if (!turning || e.pointerId !== turning.id) return;
      var a = ang(e), d = a - turning.a;
      if (d > 180) d -= 360; if (d < -180) d += 360;
      turning.a = a; turning.acc += d; turning.total += Math.abs(d);
      if (turning.total > 10 && !turning.captured) { turning.captured = true; wheel.classList.add('tp-turning'); try { wheel.setPointerCapture(e.pointerId); } catch (x) {} }
      while (turning.acc >= 15) { turning.acc -= 15; notch(1); }
      while (turning.acc <= -15) { turning.acc += 15; notch(-1); }
      if (turning.captured) e.preventDefault();
    });
    function endTurn() { if (turning && turning.captured) suppressUntil = Date.now() + 350; turning = null; wheel.classList.remove('tp-turning'); }
    on(wheel, 'pointerup', endTurn); on(wheel, 'pointercancel', endTurn);
    var wheelAcc = 0;
    on(wheel, 'wheel', function (e) {
      e.preventDefault(); wheelAcc += e.deltaY;
      while (wheelAcc >= 40) { wheelAcc -= 40; notch(1); }
      while (wheelAcc <= -40) { wheelAcc += 40; notch(-1); }
    }, { passive: false });
    on(root.querySelector('.tp-device'), 'keydown', function (e) {
      if (e.key === 'ArrowDown' || e.key === 'ArrowRight' && screen === 'menu') { e.preventDefault(); notch(1); }
      else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft' && screen === 'menu') { e.preventDefault(); notch(-1); }
      else if (e.key === 'Escape') { e.preventDefault(); if (screen === 'menu') menu(); else setView('mini'); }
    });

    wireDrag();
    on(W, 'resize', function () { _raf(applyPos); });
    on(W, 'orientationchange', function () { _setTimeout(applyPos, 250); });
  }

  /* ================= dragging ================= */
  function interactive(t) { return t.closest('button:not(.tp-pill),.tp-wheel,.tp-list,[role="button"]:not(.tp-lcd)') ; }
  function applyPos() {
    if (!dock) return;
    if (!S.pos) { dock.classList.remove('tp-placed'); dock.style.left = dock.style.top = ''; return; }
    var r = dock.getBoundingClientRect(), vw = D.documentElement.clientWidth, vh = W.innerHeight;
    var m = 6, x = S.pos.x * Math.max(0, vw - r.width), y = S.pos.y * Math.max(0, vh - r.height);
    x = Math.max(m, Math.min(vw - r.width - m, x)); y = Math.max(m, Math.min(vh - r.height - m, y));
    dock.classList.add('tp-placed'); dock.style.left = x + 'px'; dock.style.top = y + 'px';
  }
  function resetPos() { S.pos = null; save(); applyPos(); clickSound('press'); }
  function wireDrag() {
    var drag = null, lastTap = 0;
    on(dock, 'pointerdown', function (e) {
      if (e.button > 0) return;
      var grab = e.target.closest('.tp-grab,.tp-grip,.tp-sgrip,.tp-shell');
      if (!grab || (interactive(e.target) && !e.target.closest('.tp-grip,.tp-sgrip'))) return;
      var r = dock.getBoundingClientRect();
      drag = { id: e.pointerId, sx: e.clientX, sy: e.clientY, ox: r.left, oy: r.top, w: r.width, h: r.height, moved: false,
        onGrip: !!e.target.closest('.tp-grip,.tp-sgrip'), onLcd: !!e.target.closest('.tp-lcd'), onPill: !!e.target.closest('.tp-pill') };
      if (e.pointerType !== 'mouse') e.preventDefault();
      try { dock.setPointerCapture(e.pointerId); } catch (x) {}
    });
    on(dock, 'pointermove', function (e) {
      if (!drag || e.pointerId !== drag.id) return;
      var dx = e.clientX - drag.sx, dy = e.clientY - drag.sy;
      if (!drag.moved) {
        if (Math.abs(dx) + Math.abs(dy) < 6) return;
        drag.moved = true; dock.classList.add('tp-dragging'); endHint(true);
      }
      e.preventDefault();
      var vw = D.documentElement.clientWidth, vh = W.innerHeight, m = 6;
      var x = Math.max(m, Math.min(vw - drag.w - m, drag.ox + dx)), y = Math.max(m, Math.min(vh - drag.h - m, drag.oy + dy));
      dock.classList.add('tp-placed'); dock.style.left = x + 'px'; dock.style.top = y + 'px';
      drag.x = x; drag.y = y;
    });
    function end(e) {
      if (!drag || e.pointerId !== drag.id) return;
      var d = drag; drag = null; dock.classList.remove('tp-dragging');
      if (d.moved) {
        var vw = D.documentElement.clientWidth, vh = W.innerHeight;
        S.pos = { x: Math.max(0, Math.min(1, d.x / Math.max(1, vw - d.w))), y: Math.max(0, Math.min(1, d.y / Math.max(1, vh - d.h))) };
        save(); suppressUntil = Date.now() + 300; return;
      }
      if (e.type === 'pointercancel') return;
      if (d.onGrip) { var now = Date.now(); if (now - lastTap < 380) { lastTap = 0; resetPos(); } else lastTap = now; return; }
      /* the tap's own click lands on whatever the new view puts under the finger (the mini play button
         sits where the pill was): swallow it so expanding never toggles playback */
      if (d.onLcd || d.onPill) suppressUntil = Date.now() + 400;
      if (d.onLcd) { clickSound('press'); setView('full'); }
      else if (d.onPill) { clickSound('press'); setView(S.back === 'full' ? 'full' : 'mini'); }
    }
    on(dock, 'pointerup', end); on(dock, 'pointercancel', end);
    on(dock, 'dblclick', function (e) { if (e.target.closest('.tp-grip,.tp-sgrip')) { e.preventDefault(); } });
    /* stop touch scrolling while a drag is live */
    on(dock, 'touchmove', function (e) { if (drag) e.preventDefault(); }, { passive: false });
  }

  /* ================= a page can host the strip itself =================
     A page element marked [data-trd-pod-door] (the homepage door) stands in for the
     floating strip until the album has been started, so two strips never show at once. */
  var launching = false, hintPending = false;
  function syncDoor() {
    if (!root) return;
    /* Homepage tape deck stands in for the floating strip whenever the door is on the page,
       even after the album has started — so the white mini player does not float over the shop. */
    var hide = !!D.querySelector('[data-trd-pod-door]') && !launching;
    var was = root.classList.contains('tp-doorhide');
    root.classList.toggle('tp-doorhide', hide);
    if (was && !hide && hintPending) { hintPending = false; maybeHint(); }
  }
  /* Start the album from a page strip and fly that strip to the floating spot, then go to href. */
  function launchFrom(src, href) {
    if (launching || !root) return;
    launching = true;
    if (href) getPage(href).catch(function () {});
    if (S.view !== 'mini') setView('mini', true);
    play();                                   /* inside the tap, so the browser allows it */
    var rm = W.matchMedia && W.matchMedia('(prefers-reduced-motion: reduce)').matches;
    root.classList.remove('tp-doorhide');
    var from = src.getBoundingClientRect(), to = dock.getBoundingClientRect();
    function done() {
      launching = false; root.classList.remove('tp-arriving'); render(); applyPos();
      if (href) go(new URL(href, location.href).href, true);
    }
    if (rm || !src.animate || !from.width) { done(); return; }
    root.classList.add('tp-arriving');   /* hidden until its fade animation takes over below */
    var ghost = src.cloneNode(true);
    ghost.classList.add('tp-ghost'); ghost.removeAttribute('id');
    ghost.style.left = from.left + 'px'; ghost.style.top = from.top + 'px';
    ghost.style.width = from.width + 'px'; ghost.style.height = from.height + 'px';
    root.appendChild(ghost);
    src.style.visibility = 'hidden';
    var hostDoor = src.closest('[data-trd-pod-door]'); if (hostDoor) hostDoor.classList.add('tpd-detached');
    var midL = (from.left + to.left) / 2, midT = Math.min(from.top, to.top) - Math.min(90, W.innerHeight * 0.12);
    var midW = (from.width + to.width) / 2, midH = (from.height + to.height) / 2;
    var lift = '0 0 0 1px #8f8f8f,0 0 0 3px #e9e9e9,0 0 0 4px #9c9c9c,0 34px 60px -10px rgba(0,0,0,.85),0 10px 24px rgba(0,0,0,.5)';
    var a = ghost.animate([
      { left: from.left + 'px', top: from.top + 'px', width: from.width + 'px', height: from.height + 'px', transform: 'translateY(0) scale(1) rotate(0)', opacity: 1, offset: 0 },
      { left: from.left + 'px', top: from.top + 'px', width: from.width + 'px', height: from.height + 'px', transform: 'translateY(-16px) scale(1.04) rotate(-1.5deg)', boxShadow: lift, opacity: 1, offset: 0.24 },
      { left: midL + 'px', top: Math.max(8, midT) + 'px', width: midW + 'px', height: midH + 'px', transform: 'translateY(0) scale(1.03) rotate(1.5deg)', boxShadow: lift, opacity: 1, offset: 0.62 },
      { left: to.left + 'px', top: to.top + 'px', width: to.width + 'px', height: to.height + 'px', transform: 'translateY(0) scale(1) rotate(0)', opacity: 1, offset: 0.9 },
      { left: to.left + 'px', top: to.top + 'px', width: to.width + 'px', height: to.height + 'px', transform: 'none', opacity: 0, offset: 1 }
    ], { duration: 1100, easing: 'cubic-bezier(.45,0,.2,1)', fill: 'forwards' });
    /* the real strip fades in under the ghost as it lands (same clock as the flight) */
    root.classList.remove('tp-arriving');
    if (dock.animate) dock.animate([{ opacity: 0 }, { opacity: 0, offset: 0.86 }, { opacity: 1 }], { duration: 1100, easing: 'linear' });
    a.onfinish = function () { ghost.remove(); done(); };
  }

  /* ================= first-visit hint ================= */
  var hintTimer = 0;
  function maybeHint() {
    var seen = false; try { seen = localStorage.getItem(HINT_KEY); } catch (e) {}
    if (seen || S.pos) return;
    _setTimeout(function () {
      if (!dock || dock.classList.contains('tp-dragging')) return;
      if (root.classList.contains('tp-doorhide') || launching) { hintPending = true; return; }
      dock.classList.add('tp-hinting', 'tp-nudge');
      hintTimer = _setTimeout(function () { endHint(true); }, 6000);
    }, 900);
  }
  function endHint(remember) {
    if (!dock) return;
    _clearTimeout(hintTimer);
    if (dock.classList.contains('tp-hinting') || remember) { try { localStorage.setItem(HINT_KEY, '1'); } catch (e) {} }
    dock.classList.remove('tp-hinting', 'tp-nudge');
  }

  /* ================= soft navigation ================= */
  /* Pages that are full single-page apps (or load their own script files) load
     normally; the pod picks up again from the saved position. */
  var FULL = /^\/(ledger\.html|memes\.html|Qdrops(\/|$)|x(\/|$)|album\/|process\/|scif\/)/i;
  var curPath = location.pathname + location.search, navToken = 0, cache = {};
  function softURL(a, e) {
    if (!a || !a.href || (e && (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey))) return null;
    if (a.target && a.target !== '_self') return null;
    if (a.hasAttribute('download') || a.hasAttribute('data-trd-full') || /\bexternal\b/.test(a.rel || '')) return null;
    if (a.getAttribute('href').charAt(0) === '#') return null;
    var u; try { u = new URL(a.href, location.href); } catch (x) { return null; }
    if (u.origin !== location.origin || !/^https?:$/.test(u.protocol)) return null;
    var last = u.pathname.split('/').pop();
    if (last.indexOf('.') >= 0 && !/\.html?$/i.test(last)) return null;   // pdf, mp3, images, zips
    if (FULL.test(u.pathname)) return null;
    if (u.pathname + u.search === curPath && u.hash) return null;          // same-page anchor
    return u;
  }
  function getPage(href) {
    var k = href.split('#')[0];
    if (!cache[k]) {
      cache[k] = fetch(k, { credentials: 'same-origin' }).then(function (r) {
        if (!r.ok || !/text\/html/i.test(r.headers.get('content-type') || '')) throw new Error('not html');
        return r.text();
      });
      cache[k].catch(function () { delete cache[k]; });
      _setTimeout(function () { delete cache[k]; }, 60000);
    }
    return cache[k];
  }
  function needsFull(doc) {
    if (doc.querySelector('meta[http-equiv="refresh" i],script[type="module"],body[data-trd-full]')) return true;
    return [].some.call(doc.querySelectorAll('script[src]'), function (s) { return !s.hasAttribute('data-trd-keep') && !/gc\.zgo\.at/.test(s.getAttribute('src')); });
  }
  function isHeadAsset(n) {
    if (n.hasAttribute && n.hasAttribute('data-trd-keep')) return false;
    var tag = n.nodeName;
    if (tag === 'STYLE') return true;
    if (tag === 'LINK') return /\b(stylesheet|canonical)\b/i.test(n.rel);
    if (tag === 'META') return /^(description|theme-color)$/i.test(n.name || '') || /^og:/i.test(n.getAttribute('property') || '') || /^twitter:/i.test(n.name || '');
    if (tag === 'SCRIPT') return !/gc\.zgo\.at/.test(n.getAttribute('src') || '');
    return false;
  }
  function runnable(s) { var t = (s.getAttribute('data-trd-type') || '').toLowerCase(); return !s.src && (!t || /^(text|application)\/(java|ecma)script$/.test(t)); }
  function restoreType(s) { var t = s.getAttribute('data-trd-type'); s.removeAttribute('data-trd-type'); if (t) s.setAttribute('type', t); else s.removeAttribute('type'); }
  function runScript(old) {
    var s = D.createElement('script');
    [].forEach.call(old.attributes, function (a) { if (a.name !== 'type' && a.name !== 'data-trd-type') s.setAttribute(a.name, a.value); });
    /* each page script runs in its own function scope, so top-level const/let
       from one page never collide with the next page's */
    s.text = '(function(){' + old.text + '\n}).call(window);';
    old.parentNode.replaceChild(s, old);
  }
  function go(href, push, y) {
    var token = ++navToken;
    root.classList.add('tp-loading');
    return getPage(href).then(function (html) {
      if (token !== navToken) return;
      var doc = new DOMParser().parseFromString(html, 'text/html');
      if (needsFull(doc)) { push ? location.assign(href) : location.replace(href); return; }
      [].forEach.call(doc.querySelectorAll('script'), function (sc) { sc.setAttribute('data-trd-type', sc.getAttribute('type') || ''); sc.setAttribute('type', 'text/x-trd-inert'); });
      if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
      try { history.replaceState(Object.assign({}, history.state, { trd: 1, y: W.scrollY }), ''); } catch (x) {}
      if (push) history.pushState({ trd: 1, y: 0 }, '', href);
      swap(doc);
      curPath = location.pathname + location.search;
      var target = location.hash && D.getElementById(decodeURIComponent(location.hash.slice(1)));
      if (target) target.scrollIntoView();
      else W.scrollTo({ top: y || 0, left: 0, behavior: 'instant' });
      if (W.goatcounter && typeof W.goatcounter.count === 'function') {
        try { W.goatcounter.count({ path: location.pathname, title: D.title }); } catch (x) {}
      }
    }).catch(function () { if (token === navToken) { push ? location.assign(href) : location.replace(href); } })
      .then(function () { if (root) root.classList.remove('tp-loading'); });
  }
  function swap(doc) {
    leavePage();
    D.title = doc.title;
    ['lang', 'class', 'data-theme', 'style', 'dir'].forEach(function (a) {
      var v = doc.documentElement.getAttribute(a);
      if (v == null) D.documentElement.removeAttribute(a); else D.documentElement.setAttribute(a, v);
    });
    /* head: drop the old page's styles and meta, bring in the new page's */
    var head = D.head, anchor = head.querySelector('[data-trd-keep]');
    [].slice.call(head.children).forEach(function (n) { if (isHeadAsset(n)) n.remove(); });
    var headScripts = [];
    [].forEach.call(doc.head.children, function (n) {
      if (!isHeadAsset(n)) return;
      var c = D.importNode(n, true);
      head.insertBefore(c, anchor);
      if (c.nodeName === 'SCRIPT') headScripts.push(c);
    });
    /* body: everything except the pod */
    var b = D.body;
    [].slice.call(b.attributes).forEach(function (a) { b.removeAttribute(a.name); });
    [].forEach.call(doc.body.attributes, function (a) { b.setAttribute(a.name, a.value); });
    [].slice.call(b.childNodes).forEach(function (n) { if (n !== root) b.removeChild(n); });
    var frag = D.createDocumentFragment();
    [].slice.call(doc.body.childNodes).forEach(function (n) { if (!(n.id === 'trd-pod')) frag.appendChild(D.importNode(n, true)); });
    b.insertBefore(frag, root);
    attach();
    runningScripts = true;
    try {
      headScripts.concat([].slice.call(b.querySelectorAll('script'))).forEach(function (s) {
        if (!s.hasAttribute('data-trd-type') || s.closest('#trd-pod')) return;
        if (runnable(s)) runScript(s); else restoreType(s);
      });
    } finally { runningScripts = false; }
    var main = D.querySelector('main') ;
    if (main) { if (!main.hasAttribute('tabindex')) main.setAttribute('tabindex', '-1'); try { main.focus({ preventScroll: true }); } catch (x) {} }
    render(); _raf(marquee);
  }
  on(W, 'click', function (e) {
    var a = e.target && e.target.closest && e.target.closest('a[href]');
    if (!a || (root && root.contains(a))) return;
    var u = softURL(a, e); if (!u) return;
    e.preventDefault();
    go(u.href, true);
  });
  function prefetch(e) { var a = e.target && e.target.closest && e.target.closest('a[href]'); var u = a && softURL(a); if (u) getPage(u.href).catch(function () {}); }
  on(D, 'pointerover', prefetch, { passive: true });
  on(D, 'touchstart', prefetch, { passive: true });
  on(W, 'popstate', function (e) {
    var p = location.pathname + location.search;
    if (p === curPath) return;                    // hash-only change: the page handles it
    if (FULL.test(location.pathname)) { location.reload(); return; }
    go(location.href, false, e.state && e.state.y);
  });

  /* The browser blocked resuming after a full page load (no tap on this page yet).
     The visitor was listening, so the first tap or key press on the page carries on. */
  function armResume() {
    function go2(e) {
      if (root && e.target && root.contains(e.target)) return disarm();   // the pod's own buttons decide
      disarm(); if (audio.paused) play();
    }
    function disarm() { remL.call(D, 'pointerdown', go2, true); remL.call(D, 'keydown', go2, true); }
    addL.call(D, 'pointerdown', go2, true); addL.call(D, 'keydown', go2, true);
  }

  /* ================= boot ================= */
  function boot() {
    build();
    /* a full page load (fallback page or reload): pick the album back up */
    if (S.started) {
      audio.preload = 'metadata';
      loadTrack(S.i, S.t);
      if (S.playing && Date.now() - S.at < 5 * 60 * 1000) {
        var p = audio.play();
        if (p && p.catch) p.catch(function () { S.playing = false; render(); armResume(); });
      } else { S.playing = false; render(); }
    }
  }
  if (D.readyState === 'loading') on(D, 'DOMContentLoaded', boot); else boot();

  W.trdPod = { play: play, pause: pause, toggle: toggle, playIndex: playIndex, toggleIndex: toggleIndex, next: next, prev: prev,
    state: state, tracks: TRACKS.map(function (t) { return { title: t.title, src: t.src, length: t.len }; }), audio: audio,
    view: function (v) { if (v) setView(v); return S.view; }, resetPosition: resetPos, launchFrom: launchFrom, navigate: function (h) { return go(h, true); } };
})();
