/* Red Pill Room — Spotify-lookalike player & time-synced lyrics
   Powered by window.trdPod so audio keeps running seamlessly across the site. */
(function () {
  'use strict';
  var W = window, D = document;
  if (W.trdAlbumPlayer) return;

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function fmt(s) {
    s = Math.max(0, Math.floor(s || 0));
    return Math.floor(s / 60) + ':' + ('0' + (s % 60)).slice(-2);
  }
  function svg(paths, vb) {
    return '<svg viewBox="' + (vb || '0 0 24 24') + '" aria-hidden="true" focusable="false">' + paths + '</svg>';
  }

  var IC = {
    play: svg('<path fill="currentColor" d="M8 5.14v13.72a.5.5 0 0 0 .77.42l10.28-6.86a.5.5 0 0 0 0-.84L8.77 4.72A.5.5 0 0 0 8 5.14Z"/>'),
    pause: svg('<path fill="currentColor" d="M7 4h3.5v16H7zM13.5 4H17v16h-3.5z"/>'),
    prev: svg('<path fill="currentColor" d="M5 5h2.4v14H5zM19 5v14L8.5 12z"/>'),
    next: svg('<path fill="currentColor" d="M16.6 5H19v14h-2.4zM5 5v14l10.5-7z"/>'),
    shuffle: svg('<path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M16 3h5v5M4 20L21 3M21 16v5h-5M15 15l6 6M4 4l5 5"/>'),
    repeat: svg('<path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="m17 2 4 4-4 4M3 11v-1a4 4 0 0 1 4-4h14M7 22l-4-4 4-4M21 13v1a4 4 0 0 1-4 4H3"/>'),
    volHi: svg('<path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M11 5 6 9H2v6h4l5 4V5zM15.54 8.46a5 5 0 0 1 0 7.07M19.07 4.93a10 10 0 0 1 0 14.14"/>'),
    volLo: svg('<path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M11 5 6 9H2v6h4l5 4V5zM15.54 8.46a5 5 0 0 1 0 7.07"/>'),
    volMute: svg('<path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M11 5 6 9H2v6h4l5 4V5zM23 9l-6 6M17 9l6 6"/>'),
    lyrics: svg('<path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v3M8 22h8"/>'),
    expand: svg('<path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/>'),
    collapse: svg('<path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M4 14h6v6M20 10h-6V4M14 10l7-7M3 21l7-7"/>'),
    down: svg('<path fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" d="m6 9 6 6 6-6"/>'),
    share: svg('<path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8M16 6l-4-4-4 4M12 2v13"/>'),
    search: svg('<circle cx="11" cy="11" r="8" fill="none" stroke="currentColor" stroke-width="2"/><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" d="m21 21-4.3-4.3"/>'),
    queue: svg('<path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M3 6h14M3 12h14M3 18h10M18 15l4 3-4 3z"/>'),
    ext: svg('<path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M7 17 17 7M9 7h8v8"/>'),
    video: svg('<rect x="2" y="5" width="20" height="14" rx="2" fill="none" stroke="currentColor" stroke-width="2"/><path fill="currentColor" d="M10 9.2v5.6a.5.5 0 0 0 .76.42l4.8-2.8a.5.5 0 0 0 0-.84l-4.8-2.8A.5.5 0 0 0 10 9.2z"/>')
  };

  var dataCache = null;
  var lyricsCache = {};

  function loadTracks() {
    if (dataCache) return Promise.resolve(dataCache);
    return fetch('/data/album/tracks.json', { credentials: 'same-origin' })
      .then(function (r) { if (!r.ok) throw new Error('tracks.json failed'); return r.json(); })
      .then(function (d) { dataCache = d; return d; });
  }

  function loadLyrics(fileId) {
    if (!fileId) return Promise.resolve(null);
    if (lyricsCache[fileId]) return Promise.resolve(lyricsCache[fileId]);
    return fetch('/data/album/lyrics/' + encodeURIComponent(fileId) + '.json', { credentials: 'same-origin' })
      .then(function (r) { if (!r.ok) return null; return r.json(); })
      .then(function (d) { if (d) lyricsCache[fileId] = d; return d; })
      .catch(function () { return null; });
  }

  function sliderMarkup(cls, label) {
    return '<div class="ap-slider ' + cls + '" role="slider" tabindex="0" aria-label="' + esc(label) + '" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0">' +
      '<div class="ap-slider-track"><div class="ap-slider-fill"></div><span class="ap-slider-knob"></span></div>' +
      '</div>';
  }

  function mount(opts) {
    opts = opts || {};
    var rootEl = typeof opts.root === 'string' ? D.querySelector(opts.root) : opts.root;
    if (!rootEl) return;

    D.body.classList.add('al-room-player');
    var mode = opts.mode || rootEl.getAttribute('data-page-mode') || 'album';
    var initialSlug = opts.initialTrack || rootEl.getAttribute('data-initial-track') || '';
    if (!initialSlug) {
      var sp = new URLSearchParams(location.search);
      initialSlug = sp.get('track') || '';
      if (!initialSlug && location.hash && location.hash.indexOf('track=') >= 0) {
        initialSlug = decodeURIComponent(location.hash.replace(/^#/, '').split('track=')[1].split('&')[0]);
      }
    }

    var pod = W.trdPod;
    var showRemaining = false;
    var lastVol = 1;
    var activeLyricsSlug = null;
    var currentLyrics = null;
    var activeLineIdx = -1;
    var manualUntil = {};
    var autoScrolling = {};
    var sheetTab = 'now';
    var filterQuery = '';
    var scrubbing = false;
    var lastShareTrack = '';
    var rafId = 0;

    function getState() {
      if (pod) return pod.state();
      return { src: 'album', i: 0, playing: false, started: false, t: 0, d: 286, vol: 1, shuffle: false, repeat: 'off' };
    }
    function liveTime() {
      var s = getState();
      if (pod && pod.audio && pod.audio.getAttribute('src') && !pod.audio.paused && pod.audio.readyState >= 1 && !pod.audio.seeking) {
        return pod.audio.currentTime;
      }
      return s.t || 0;
    }

    loadTracks().then(function (album) {
      var tracks = album.tracks || [];
      if (!tracks.length) return;

      function findTrackIndex(q) {
        if (!q) return -1;
        q = String(q).toLowerCase();
        for (var i = 0; i < tracks.length; i++) {
          if (tracks[i].slug === q || tracks[i].fileId === q || String(tracks[i].n) === q) return i;
        }
        return -1;
      }

      var initIdx = findTrackIndex(initialSlug);
      if (initIdx >= 0 && pod) {
        var curS = pod.state();
        if (!curS.started || curS.i !== initIdx) {
          pod.loadIndex(initIdx, 0);
        }
      }

      /* Build workspace HTML */
      var coverBig = album.cover || '/images/opt/album-cover-card.jpg';
      var coverSmall = album.coverSmall || '/assets/trd/img/red-pill-cover-192.jpg';

      var workspaceHTML =
        '<div class="al-wrap">' +
          '<div class="al-ws-head">' +
            '<div>' +
              '<p class="eyebrow">' + (mode === 'song' ? 'the red pill room · single track' : 'the red pill room · player &amp; lyrics') + '</p>' +
              '<h2 id="tracklist-title">' + (mode === 'song' ? 'now playing in the red pill room' : 'stream the record, follow the lyrics') + '</h2>' +
            '</div>' +
            '<p class="al-ws-sub">22 tracks · 1 hr 21 min · free in the red pill room</p>' +
          '</div>' +

          '<div class="al-ws-grid">' +
            /* Left column: queue / tracklist */
            '<div class="ap-queue-card">' +
              '<div class="ap-queue-bar">' +
                '<button class="ap-play-circle is-accent js-album-play" type="button" aria-label="play or pause album">' + IC.play + '</button>' +
                '<button class="ap-icon-btn js-shuffle" type="button" aria-label="shuffle" aria-pressed="false" title="shuffle">' + IC.shuffle + '</button>' +
                '<button class="ap-icon-btn js-repeat" type="button" aria-label="repeat" title="repeat">' + IC.repeat + '<span class="ap-repeat-one" hidden>1</span></button>' +
                '<span class="ap-queue-meta"><b>' + tracks.length + '</b> tracks</span>' +
                '<div class="ap-search-wrap">' + IC.search +
                  '<input class="ap-search js-filter" type="search" placeholder="filter tracks" aria-label="filter tracks">' +
                '</div>' +
              '</div>' +
              '<div class="ap-track-hdr" aria-hidden="true"><span>#</span><span>title</span><span></span><span>time</span></div>' +
              '<ol class="ap-tracklist js-tracklist" aria-label="album tracklist"></ol>' +
              '<p class="ap-empty js-empty" hidden>no matching tracks</p>' +
            '</div>' +

            /* Right column: Now Playing + Lyrics + Share */
            '<div class="ap-stage">' +
              '<section class="ap-np-card" aria-label="now playing">' +
                '<div class="ap-np-top">' +
                  '<img class="ap-np-art" src="' + coverBig + '" width="208" height="208" alt="The Red Pill Album cover">' +
                  '<div class="ap-np-meta">' +
                    '<p class="ap-np-kicker js-np-kicker">track 01 of 22</p>' +
                    '<h3 class="ap-np-title"><span class="js-np-title"></span><span class="ap-exp js-np-exp" hidden title="explicit">E</span></h3>' +
                    '<p class="ap-np-artist">' + esc(album.artist) + ' · ' + esc(album.album) + '</p>' +
                    '<div class="ap-np-actions">' +
                      '<a class="ap-pill-btn js-np-apple" href="#" target="_blank" rel="noopener">Apple Music ' + IC.ext + '</a>' +
                      '<button class="ap-pill-btn js-watch-video" type="button">' + IC.video + ' watch video</button>' +
                      '<button class="ap-pill-btn js-open-sheet" type="button">' + IC.expand + ' full player</button>' +
                    '</div>' +
                  '</div>' +
                '</div>' +

                '<div class="ap-stage-scrub">' +
                  '<div class="ap-scrub-wrap">' +
                    '<span class="ap-time js-time-el">0:00</span>' +
                    sliderMarkup('js-scrub', 'seek position') +
                    '<span class="ap-time is-end js-time-end" title="click to toggle remaining time">0:00</span>' +
                  '</div>' +
                  '<div class="ap-stage-transport">' +
                    '<div class="ap-stage-btns">' +
                      '<button class="ap-icon-btn js-shuffle" type="button" aria-label="shuffle" aria-pressed="false">' + IC.shuffle + '</button>' +
                      '<button class="ap-icon-btn js-prev" type="button" aria-label="previous track">' + IC.prev + '</button>' +
                      '<button class="ap-play-circle js-play" type="button" aria-label="play or pause">' + IC.play + '</button>' +
                      '<button class="ap-icon-btn js-next" type="button" aria-label="next track">' + IC.next + '</button>' +
                      '<button class="ap-icon-btn js-repeat" type="button" aria-label="repeat">' + IC.repeat + '<span class="ap-repeat-one" hidden>1</span></button>' +
                    '</div>' +
                    '<div class="ap-stage-vol">' +
                      '<button class="ap-icon-btn js-mute" type="button" aria-label="mute or unmute">' + IC.volHi + '</button>' +
                      sliderMarkup('ap-vol-slider js-vol', 'volume') +
                    '</div>' +
                  '</div>' +
                '</div>' +
              '</section>' +

              /* Lyrics card */
              '<section class="ap-lyrics-card" id="lyrics" aria-label="synced lyrics">' +
                '<div class="ap-lyrics-head">' +
                  '<div class="ap-lyrics-label"><span class="dot" aria-hidden="true"></span><span>lyrics</span></div>' +
                  '<div class="ap-lyrics-tools">' +
                    '<button class="ap-pill-btn js-watch-video" type="button">' + IC.video + ' watch video</button>' +
                    '<button class="ap-pill-btn js-theater-open" type="button" title="expand lyrics">' + IC.expand + ' expand</button>' +
                  '</div>' +
                '</div>' +
                '<div class="ap-lyrics-scroll js-lyrics-box" data-box="stage"></div>' +
                '<button class="ap-resync-btn js-resync" data-box="stage" type="button" hidden>resync</button>' +
                '<div class="ap-lyrics-foot">' +
                  '<span class="js-lyrics-foot-note">tap any line to jump to that part of the song</span>' +
                  '<span class="js-lyrics-source"></span>' +
                '</div>' +
              '</section>' +

              /* Share song card */
              '<section class="ap-share-card" id="share-song" aria-label="share this song">' +
                '<div class="ap-share-head">' +
                  '<h3>share this song</h3>' +
                  '<a class="ap-share-url js-share-url" href="#" hidden></a>' +
                '</div>' +
                '<div class="ap-share-slot js-share-slot"></div>' +
              '</section>' +
            '</div>' +
          '</div>' +
        '</div>';

      rootEl.innerHTML = workspaceHTML;

      /* Persistent desktop bar + mobile mini-bar + theater + mobile full-screen sheet */
      var existingDock = D.getElementById('al-player-chrome');
      if (existingDock) existingDock.remove();
      var chrome = D.createElement('div');
      chrome.id = 'al-player-chrome';
      chrome.innerHTML =
        /* Desktop bottom bar */
        '<aside class="ap-bar" aria-label="now playing bar">' +
          '<div class="ap-bar-left">' +
            '<img class="ap-bar-art" src="' + coverSmall + '" width="54" height="54" alt="">' +
            '<div class="ap-bar-meta">' +
              '<div class="ap-bar-title js-bar-title"></div>' +
              '<div class="ap-bar-artist">' + esc(album.artist) + '</div>' +
            '</div>' +
            '<button class="ap-icon-btn js-jump-share" type="button" aria-label="share this song" title="share">' + IC.share + '</button>' +
          '</div>' +
          '<div class="ap-bar-center">' +
            '<div class="ap-bar-controls">' +
              '<button class="ap-icon-btn js-shuffle" type="button" aria-label="shuffle" aria-pressed="false" title="shuffle">' + IC.shuffle + '</button>' +
              '<button class="ap-icon-btn js-prev" type="button" aria-label="previous track" title="previous">' + IC.prev + '</button>' +
              '<button class="ap-play-circle js-play" type="button" aria-label="play or pause" title="play / pause">' + IC.play + '</button>' +
              '<button class="ap-icon-btn js-next" type="button" aria-label="next track" title="next">' + IC.next + '</button>' +
              '<button class="ap-icon-btn js-repeat" type="button" aria-label="repeat" title="repeat">' + IC.repeat + '<span class="ap-repeat-one" hidden>1</span></button>' +
            '</div>' +
            '<div class="ap-scrub-wrap">' +
              '<span class="ap-time js-time-el">0:00</span>' +
              sliderMarkup('js-scrub', 'seek position') +
              '<span class="ap-time is-end js-time-end" title="click to toggle remaining time">0:00</span>' +
            '</div>' +
          '</div>' +
          '<div class="ap-bar-right">' +
            '<button class="ap-icon-btn js-theater-open" type="button" aria-label="lyrics view" title="lyrics">' + IC.lyrics + '</button>' +
            '<button class="ap-icon-btn js-jump-queue" type="button" aria-label="queue" title="queue">' + IC.queue + '</button>' +
            '<button class="ap-icon-btn js-mute" type="button" aria-label="mute or unmute" title="mute">' + IC.volHi + '</button>' +
            sliderMarkup('ap-vol-slider js-vol', 'volume') +
          '</div>' +
        '</aside>' +

        /* Mobile mini-bar */
        '<div class="ap-mbar" aria-label="mini player">' +
          '<img class="ap-mbar-art" src="' + coverSmall + '" width="42" height="42" alt="">' +
          '<button class="ap-mbar-open js-open-sheet" type="button" aria-label="open now playing">' +
            '<div class="ap-mbar-title js-bar-title"></div>' +
            '<div class="ap-mbar-sub js-mbar-sub"></div>' +
          '</button>' +
          '<button class="ap-icon-btn js-mbar-lyrics" type="button" aria-label="open lyrics">' + IC.lyrics + '</button>' +
          '<button class="ap-icon-btn js-play" type="button" aria-label="play or pause">' + IC.play + '</button>' +
          '<div class="ap-mbar-prog"><i class="js-mbar-fill"></i></div>' +
        '</div>' +

        /* Desktop/Tablet Lyrics Theater modal */
        '<div class="ap-theater js-theater" role="dialog" aria-modal="true" aria-label="full-screen lyrics" hidden>' +
          '<div class="ap-theater-top">' +
            '<div class="ap-theater-song">' +
              '<img src="' + coverSmall + '" width="44" height="44" alt="">' +
              '<div><h2 class="js-np-title"></h2><p>' + esc(album.artist) + ' · ' + esc(album.album) + '</p></div>' +
            '</div>' +
            '<button class="ap-pill-btn js-theater-close" type="button">' + IC.collapse + ' close</button>' +
          '</div>' +
          '<div class="ap-theater-scroll js-lyrics-box" data-box="theater"></div>' +
          '<button class="ap-resync-btn js-resync" data-box="theater" type="button" hidden>resync</button>' +
        '</div>' +

        /* Mobile Full-Screen Now Playing Sheet */
        '<div class="ap-sheet js-sheet" role="dialog" aria-modal="true" aria-label="now playing" hidden>' +
          '<div class="ap-sheet-top">' +
            '<button class="ap-icon-btn js-sheet-close" type="button" aria-label="collapse player">' + IC.down + '</button>' +
            '<div class="ap-sheet-ctx"><small>playing from</small><b>' + esc(album.album) + '</b></div>' +
            '<button class="ap-icon-btn js-sheet-share-btn" type="button" aria-label="share this song">' + IC.share + '</button>' +
          '</div>' +

          '<div class="ap-sheet-tabs" role="tablist">' +
            '<button class="ap-sheet-tab is-on" data-tab="now" type="button" role="tab" aria-selected="true">now playing</button>' +
            '<button class="ap-sheet-tab" data-tab="lyrics" type="button" role="tab" aria-selected="false">lyrics</button>' +
            '<button class="ap-sheet-tab" data-tab="queue" type="button" role="tab" aria-selected="false">queue</button>' +
          '</div>' +

          '<div class="ap-sheet-pane js-pane-now">' +
            '<div class="ap-sheet-art-wrap"><img class="ap-sheet-art" src="' + coverBig + '" alt="The Red Pill Album cover"></div>' +
            '<div class="ap-sheet-meta">' +
              '<div style="min-width:0">' +
                '<h2 class="js-np-title"></h2>' +
                '<p>' + esc(album.artist) + '</p>' +
              '</div>' +
              '<button class="ap-icon-btn js-sheet-share-btn" type="button" aria-label="share">' + IC.share + '</button>' +
            '</div>' +
            '<div class="ap-scrub-wrap">' +
              '<span class="ap-time js-time-el">0:00</span>' +
              sliderMarkup('js-scrub', 'seek position') +
              '<span class="ap-time is-end js-time-end">0:00</span>' +
            '</div>' +
            '<div class="ap-sheet-transport">' +
              '<button class="ap-icon-btn js-shuffle" type="button" aria-label="shuffle" aria-pressed="false">' + IC.shuffle + '</button>' +
              '<button class="ap-icon-btn js-prev" type="button" aria-label="previous track">' + IC.prev + '</button>' +
              '<button class="ap-play-circle is-accent js-play" type="button" aria-label="play or pause">' + IC.play + '</button>' +
              '<button class="ap-icon-btn js-next" type="button" aria-label="next track">' + IC.next + '</button>' +
              '<button class="ap-icon-btn js-repeat" type="button" aria-label="repeat">' + IC.repeat + '<span class="ap-repeat-one" hidden>1</span></button>' +
            '</div>' +
            '<div class="ap-sheet-vol">' +
              '<button class="ap-icon-btn js-mute" type="button" aria-label="mute or unmute">' + IC.volHi + '</button>' +
              sliderMarkup('js-vol', 'volume') +
            '</div>' +
            '<div class="ap-sheet-lpreview js-sheet-lpreview">' +
              '<div class="ap-sheet-lpreview-hd"><span>lyrics</span><button class="ap-pill-btn js-go-lyrics" type="button">expand</button></div>' +
              '<div class="ap-sheet-lpreview-lines js-lpreview-lines"></div>' +
            '</div>' +
            '<div class="ap-share-slot js-sheet-share-slot" style="margin-top:14px"></div>' +
          '</div>' +

          '<div class="ap-sheet-pane ap-sheet-lyrics-pane js-pane-lyrics" hidden>' +
            '<div class="ap-lyrics-scroll js-lyrics-box" data-box="sheet"></div>' +
            '<button class="ap-resync-btn js-resync" data-box="sheet" type="button" hidden>resync</button>' +
            '<div class="ap-sheet-mini-ctrl">' +
              '<div class="ap-scrub-wrap">' +
                '<span class="ap-time js-time-el">0:00</span>' +
                sliderMarkup('js-scrub', 'seek position') +
                '<span class="ap-time is-end js-time-end">0:00</span>' +
              '</div>' +
              '<div style="display:flex;justify-content:center;align-items:center;gap:18px;margin-top:8px">' +
                '<button class="ap-icon-btn js-prev" type="button" aria-label="previous track">' + IC.prev + '</button>' +
                '<button class="ap-play-circle js-play" type="button" aria-label="play or pause">' + IC.play + '</button>' +
                '<button class="ap-icon-btn js-next" type="button" aria-label="next track">' + IC.next + '</button>' +
              '</div>' +
            '</div>' +
          '</div>' +

          '<div class="ap-sheet-pane js-pane-queue" hidden>' +
            '<ol class="ap-sheet-queue-list js-sheet-queue"></ol>' +
          '</div>' +
        '</div>';

      var mainParent = rootEl.parentNode || D.body;
      mainParent.appendChild(chrome);

      var scope = D;
      var tracklistEl = rootEl.querySelector('.js-tracklist');
      var sheetQueueEl = chrome.querySelector('.js-sheet-queue');
      var emptyEl = rootEl.querySelector('.js-empty');
      var filterEl = rootEl.querySelector('.js-filter');
      var theaterEl = chrome.querySelector('.js-theater');
      if (!chrome.querySelector('.js-video-overlay')) {
        chrome.insertAdjacentHTML('beforeend',
          '<div class="ap-video-overlay js-video-overlay" hidden>' +
            '<div class="ap-video-backdrop js-video-close" aria-hidden="true"></div>' +
            '<div class="ap-video-dialog" role="dialog" aria-modal="true" aria-labelledby="ap-video-title">' +
              '<div class="ap-video-bar">' +
                '<h3 class="ap-video-heading" id="ap-video-title"><span class="js-video-kicker">watch video</span><span class="js-video-title"></span></h3>' +
                '<button class="ap-pill-btn js-video-close" type="button">close</button>' +
              '</div>' +
              '<video class="ap-video-el js-lyric-video" playsinline webkit-playsinline controls preload="metadata" controlslist="nodownload"></video>' +
            '</div>' +
          '</div>'
        );
      }
      var videoOverlay = chrome.querySelector('.js-video-overlay');
      var lyricVideo = chrome.querySelector('.js-lyric-video');

      var sheetEl = chrome.querySelector('.js-sheet');

      function renderTrackRows() {
        var q = filterQuery.trim().toLowerCase();
        var visible = 0;
        var html = tracks.map(function (t, i) {
          var match = !q || t.title.toLowerCase().indexOf(q) >= 0 || String(t.n) === q;
          if (match) visible++;
          return '<li class="ap-row" data-i="' + i + '"' + (match ? '' : ' hidden') + '>' +
            '<div class="ap-row-num">' +
              '<span class="ap-row-n">' + t.n + '</span>' +
              '<span class="ap-eq" aria-hidden="true"><i></i><i></i><i></i></span>' +
              '<button class="ap-row-play" type="button" aria-label="play ' + esc(t.title) + '">' + IC.play + '</button>' +
            '</div>' +
            '<div class="ap-row-info">' +
              '<div class="ap-row-title-line">' +
                '<span class="ap-row-title">' + esc(t.title) + '</span>' +
                (t.explicit ? '<span class="ap-exp" title="explicit">E</span>' : '') +
                (t.hasLyrics ? '<span class="ap-badge-lyrics">lyrics</span>' : '') +
              '</div>' +
              '<div class="ap-row-sub">' + esc(album.artist) + '</div>' +
            '</div>' +
            '<div class="ap-row-acts">' +
              (t.videoUrl ? '<button class="ap-row-video js-row-video" type="button" aria-label="watch video for ' + esc(t.title) + '">watch video</button>' : '') +
              (t.shareUrl ? '<a class="ap-row-share" href="' + esc(t.shareUrl) + '" title="share ' + esc(t.title) + '" aria-label="share ' + esc(t.title) + '">' + IC.share + '</a>' : '') +
            '</div>' +
            '<div class="ap-row-dur">' + esc(t.len) + '</div>' +
            '<span class="ap-row-prog" aria-hidden="true"><i></i></span>' +
          '</li>';
        }).join('');
        tracklistEl.innerHTML = html;
        sheetQueueEl.innerHTML = tracks.map(function (t, i) {
          return '<li class="ap-row" data-i="' + i + '">' +
            '<div class="ap-row-num"><span class="ap-row-n">' + t.n + '</span><span class="ap-eq" aria-hidden="true"><i></i><i></i><i></i></span><button class="ap-row-play" type="button" aria-label="play ' + esc(t.title) + '">' + IC.play + '</button></div>' +
            '<div class="ap-row-info"><div class="ap-row-title-line"><span class="ap-row-title">' + esc(t.title) + '</span>' + (t.hasLyrics ? '<span class="ap-badge-lyrics">lyrics</span>' : '') + '</div><div class="ap-row-sub">' + esc(album.artist) + '</div></div>' +
            '<div class="ap-row-acts">' + (t.videoUrl ? '<button class="ap-row-video js-row-video" type="button" aria-label="watch video for ' + esc(t.title) + '">watch video</button>' : '') + '</div>' +
            '<div class="ap-row-dur">' + esc(t.len) + '</div>' +
          '</li>';
        }).join('');
        emptyEl.hidden = visible > 0;
      }
      renderTrackRows();

      function bindQueueClicks(ol) {
        ol.addEventListener('click', function (e) {
          if (e.target.closest('.ap-row-share') || e.target.closest('.js-row-video')) return;
          var li = e.target.closest('.ap-row');
          if (!li || !pod) return;
          var idx = +li.getAttribute('data-i');
          if (e.target.closest('.ap-row-play') || li.classList.contains('is-current')) {
            pod.toggleIndex(idx);
          } else {
            pod.playIndex(idx);
          }
        });
      }
      bindQueueClicks(tracklistEl);
      bindQueueClicks(sheetQueueEl);

      filterEl.addEventListener('input', function () {
        filterQuery = filterEl.value;
        renderTrackRows();
        paintAll(getState(), true);
      });

      /* Bind play/prev/next/shuffle/repeat/mute across workspace + bar + sheet */
      function bindAll(sel, fn) {
        [].forEach.call(scope.querySelectorAll(sel), function (el) {
          if (el.closest('#trd-pod')) return;
          el.addEventListener('click', fn);
        });
      }

      bindAll('.js-play', function () { if (pod) pod.toggle(); });
      bindAll('.js-album-play', function () {
        if (!pod) return;
        var s = pod.state();
        if (!s.started && initialSlug) {
          var idx = findTrackIndex(initialSlug);
          if (idx >= 0) { pod.playIndex(idx); return; }
        }
        pod.toggle();
      });
      bindAll('.js-prev', function () { if (pod) pod.prev(); });
      bindAll('.js-next', function () { if (pod) pod.next(); });
      bindAll('.js-shuffle', function () { if (pod) pod.toggleShuffle(); });
      bindAll('.js-repeat', function () { if (pod) pod.cycleRepeat(); });
      bindAll('.js-mute', function () {
        if (!pod) return;
        var s = pod.state();
        if (s.vol > 0) { lastVol = s.vol; pod.setVolume(0); }
        else { pod.setVolume(lastVol > 0.05 ? lastVol : 1); }
      });
      bindAll('.js-time-end', function () { showRemaining = !showRemaining; paintTimes(getState(), liveTime()); });

      /* Theater & Sheet open/close */
      function openTheater() {
        theaterEl.hidden = false;
        D.body.classList.add('al-theater-open');
        syncLyricHighlight(liveTime(), true);
      }
      function closeTheater() {
        theaterEl.hidden = true;
        D.body.classList.remove('al-theater-open');
      }
      function setSheetTab(tab) {
        sheetTab = tab;
        [].forEach.call(sheetEl.querySelectorAll('.ap-sheet-tab'), function (b) {
          var on = b.getAttribute('data-tab') === tab;
          b.classList.toggle('is-on', on);
          b.setAttribute('aria-selected', on ? 'true' : 'false');
        });
        sheetEl.querySelector('.js-pane-now').hidden = tab !== 'now';
        sheetEl.querySelector('.js-pane-lyrics').hidden = tab !== 'lyrics';
        sheetEl.querySelector('.js-pane-queue').hidden = tab !== 'queue';
        if (tab === 'lyrics') syncLyricHighlight(liveTime(), true);
      }
      function openSheet(tab) {
        sheetEl.hidden = false;
        D.body.classList.add('al-sheet-open');
        setSheetTab(tab || 'now');
      }
      function closeSheet() {
        sheetEl.hidden = true;
        D.body.classList.remove('al-sheet-open');
      }

      function currentTrack() {
        var s = getState();
        return tracks[s.i] || tracks[0];
      }
      function openVideoFor(track) {
        if (!track || !track.videoUrl || !videoOverlay || !lyricVideo) return;
        if (pod && pod.pause) pod.pause();
        if (theaterEl && !theaterEl.hidden) closeTheater();
        lyricVideo.pause();
        lyricVideo.setAttribute('playsinline', '');
        lyricVideo.setAttribute('webkit-playsinline', '');
        lyricVideo.poster = track.videoPoster || '';
        if (lyricVideo.src !== (new URL(track.videoUrl, location.href)).href) {
          lyricVideo.src = track.videoUrl;
        }
        var titleEl = videoOverlay.querySelector('.js-video-title');
        if (titleEl) titleEl.textContent = track.title || '';
        videoOverlay.hidden = false;
        D.body.classList.add('al-video-open');
        var playP = lyricVideo.play();
        if (playP && playP.catch) playP.catch(function () {});
      }
      function closeVideo() {
        if (!videoOverlay || videoOverlay.hidden) return;
        if (lyricVideo) {
          lyricVideo.pause();
        }
        videoOverlay.hidden = true;
        D.body.classList.remove('al-video-open');
      }
      bindAll('.js-watch-video', function () { openVideoFor(currentTrack()); });
      bindAll('.js-video-close', closeVideo);
      function bindRowVideos(ol) {
        if (!ol) return;
        ol.addEventListener('click', function (e) {
          var btn = e.target.closest('.js-row-video');
          if (!btn) return;
          e.preventDefault();
          e.stopPropagation();
          var li = btn.closest('.ap-row');
          if (!li) return;
          var idx = +li.getAttribute('data-i');
          openVideoFor(tracks[idx]);
        });
      }
      bindRowVideos(tracklistEl);
      bindRowVideos(sheetQueueEl);

      bindAll('.js-theater-open', openTheater);
      bindAll('.js-theater-close', closeTheater);
      bindAll('.js-open-sheet', function () { openSheet('now'); });
      bindAll('.js-mbar-lyrics', function () { openSheet('lyrics'); });
      bindAll('.js-go-lyrics', function () { setSheetTab('lyrics'); });
      bindAll('.js-sheet-close', closeSheet);
      [].forEach.call(sheetEl.querySelectorAll('.ap-sheet-tab'), function (b) {
        b.addEventListener('click', function () { setSheetTab(b.getAttribute('data-tab')); });
      });

      bindAll('.js-jump-queue', function () {
        var el = D.getElementById('tracklist') || rootEl;
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
      bindAll('.js-jump-share', function () {
        var el = D.getElementById('share-song');
        if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      });
      bindAll('.js-sheet-share-btn', function () {
        var slot = sheetEl.querySelector('.js-sheet-share-slot');
        if (sheetTab !== 'now') setSheetTab('now');
        if (slot) slot.scrollIntoView({ behavior: 'smooth', block: 'center' });
      });

      D.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
          if (videoOverlay && !videoOverlay.hidden) { closeVideo(); return; }
          if (!theaterEl.hidden) closeTheater();
          if (!sheetEl.hidden) closeSheet();
        }
      });

      /* Scrub & volume sliders (pointer drag + click + arrow keys) */
      function bindSlider(el, isVol) {
        function pctFromEvent(ev) {
          var r = el.getBoundingClientRect();
          if (!r.width) return 0;
          return Math.max(0, Math.min(1, (ev.clientX - r.left) / r.width));
        }
        function apply(p) {
          if (!pod) return;
          if (isVol) { pod.setVolume(p); return; }
          var d = getState().d || 1;
          pod.seek(p * d);
        }
        el.addEventListener('pointerdown', function (ev) {
          if (ev.button > 0) return;
          scrubbing = !isVol;
          el.classList.add('is-dragging');
          try { el.setPointerCapture(ev.pointerId); } catch (e) {}
          apply(pctFromEvent(ev));
        });
        el.addEventListener('pointermove', function (ev) {
          if (!el.classList.contains('is-dragging')) return;
          apply(pctFromEvent(ev));
        });
        function end(ev) {
          if (!el.classList.contains('is-dragging')) return;
          el.classList.remove('is-dragging');
          scrubbing = false;
          try { el.releasePointerCapture(ev.pointerId); } catch (e) {}
        }
        el.addEventListener('pointerup', end);
        el.addEventListener('pointercancel', end);
        el.addEventListener('keydown', function (ev) {
          if (!pod) return;
          var s = getState();
          if (isVol) {
            if (ev.key === 'ArrowRight' || ev.key === 'ArrowUp') { ev.preventDefault(); pod.setVolume(s.vol + 0.05); }
            if (ev.key === 'ArrowLeft' || ev.key === 'ArrowDown') { ev.preventDefault(); pod.setVolume(s.vol - 0.05); }
          } else {
            if (ev.key === 'ArrowRight') { ev.preventDefault(); pod.seek((s.t || 0) + 5); }
            if (ev.key === 'ArrowLeft') { ev.preventDefault(); pod.seek((s.t || 0) - 5); }
          }
        });
      }
      [].forEach.call(scope.querySelectorAll('.js-scrub'), function (el) { bindSlider(el, false); });
      [].forEach.call(scope.querySelectorAll('.js-vol'), function (el) { bindSlider(el, true); });

      /* Lyrics boxes & manual-scroll detection */
      var lyricBoxes = [].slice.call(scope.querySelectorAll('.js-lyrics-box'));
      lyricBoxes.forEach(function (box) {
        var name = box.getAttribute('data-box');
        function markManual() {
          if (autoScrolling[name]) return;
          manualUntil[name] = Date.now() + 5000;
          var btn = scope.querySelector('.js-resync[data-box="' + name + '"]');
          if (btn && currentLyrics) btn.hidden = false;
        }
        box.addEventListener('wheel', markManual, { passive: true });
        box.addEventListener('touchstart', markManual, { passive: true });
        box.addEventListener('pointerdown', markManual, { passive: true });
        box.addEventListener('click', function (e) {
          var lineBtn = e.target.closest('.ap-l-line');
          if (!lineBtn || !pod) return;
          var t = parseFloat(lineBtn.getAttribute('data-t'));
          if (!isNaN(t)) {
            manualUntil[name] = 0;
            var rb = scope.querySelector('.js-resync[data-box="' + name + '"]');
            if (rb) rb.hidden = true;
            pod.seek(t);
            if (!getState().playing) pod.play();
          }
        });
      });

      [].forEach.call(scope.querySelectorAll('.js-resync'), function (btn) {
        btn.addEventListener('click', function () {
          var name = btn.getAttribute('data-box');
          manualUntil[name] = 0;
          btn.hidden = true;
          syncLyricHighlight(liveTime(), true);
        });
      });

      function renderLyricsBoxes(track, data) {
        currentLyrics = data;
        activeLineIdx = -1;
        var previewLinesEl = sheetEl.querySelector('.js-lpreview-lines');
        var previewWrap = sheetEl.querySelector('.js-sheet-lpreview');
        var sourceEl = rootEl.querySelector('.js-lyrics-source');

        if (!data || !data.lines || !data.lines.length) {
          var emptyHTML =
            '<div class="ap-lyrics-empty">' +
              '<p>synced lyrics for <b>' + esc(track.title) + '</b> are coming next — previewing <b>Enjoy The Show</b> now.</p>' +
              '<button class="ap-pill-btn js-jump-enjoy" type="button">jump to Enjoy The Show</button>' +
            '</div>';
          lyricBoxes.forEach(function (b) { b.innerHTML = emptyHTML; });
          [].forEach.call(scope.querySelectorAll('.js-jump-enjoy'), function (b) {
            b.addEventListener('click', function () {
              var idx = findTrackIndex('enjoy-the-show');
              if (idx >= 0 && pod) pod.playIndex(idx);
            });
          });
          [].forEach.call(scope.querySelectorAll('.js-resync'), function (b) { b.hidden = true; });
          if (previewWrap) previewWrap.hidden = true;
          if (sourceEl) sourceEl.textContent = '';
          return;
        }

        if (previewWrap) previewWrap.hidden = false;
        if (sourceEl) sourceEl.textContent = 'artist lyrics · synced';

        var linesHTML = data.lines.map(function (ln, idx) {
          if (ln.break || !ln.text) {
            return '<button type="button" class="ap-l-line ap-l-break" data-idx="' + idx + '" data-t="' + ln.t + '" aria-label="instrumental interlude at ' + fmt(ln.t) + '"><i></i><i></i><i></i></button>';
          }
          return '<button type="button" class="ap-l-line" data-idx="' + idx + '" data-t="' + ln.t + '">' + esc(ln.text) + '</button>';
        }).join('');

        lyricBoxes.forEach(function (b) {
          b.innerHTML = linesHTML;
          b.scrollTop = 0;
        });

        if (previewLinesEl) {
          var firstThree = data.lines.filter(function (l) { return l.text; }).slice(0, 3);
          previewLinesEl.innerHTML = firstThree.map(function (l, i) {
            return '<div class="' + (i === 0 ? 'is-cur' : 'is-dim') + '">' + esc(l.text) + '</div>';
          }).join('');
        }
        syncLyricHighlight(liveTime(), true);
      }

      function findLineIndex(lines, t) {
        if (!lines || !lines.length) return -1;
        var idx = 0;
        for (var i = 0; i < lines.length; i++) {
          if (t + 0.08 >= lines[i].t) idx = i;
          else break;
        }
        return idx;
      }

      function scrollBoxToLine(box, el, instant) {
        var name = box.getAttribute('data-box');
        if (!el || box.offsetParent === null) return;
        if (!instant && manualUntil[name] && Date.now() < manualUntil[name]) return;
        var target = el.offsetTop - box.clientHeight * 0.36 + el.offsetHeight * 0.5;
        target = Math.max(0, target);
        autoScrolling[name] = true;
        box.scrollTo({ top: target, behavior: instant ? 'auto' : 'smooth' });
        setTimeout(function () { autoScrolling[name] = false; }, 420);
        var rb = scope.querySelector('.js-resync[data-box="' + name + '"]');
        if (rb) rb.hidden = true;
      }

      function syncLyricHighlight(t, forceScroll) {
        if (!currentLyrics || !currentLyrics.lines) return;
        var lines = currentLyrics.lines;
        var idx = findLineIndex(lines, t);
        if (idx === activeLineIdx && !forceScroll) return;
        activeLineIdx = idx;

        lyricBoxes.forEach(function (box) {
          var btns = box.querySelectorAll('.ap-l-line');
          for (var i = 0; i < btns.length; i++) {
            var b = btns[i];
            b.classList.toggle('is-active', i === idx);
            b.classList.toggle('is-past', i < idx);
          }
          if (btns[idx]) scrollBoxToLine(box, btns[idx], !!forceScroll);
        });

        var previewLinesEl = sheetEl.querySelector('.js-lpreview-lines');
        if (previewLinesEl) {
          var slice = [];
          for (var j = Math.max(0, idx); j < lines.length && slice.length < 3; j++) {
            if (lines[j].text) slice.push({ text: lines[j].text, cur: j === idx });
          }
          if (!slice.length) {
            slice = lines.filter(function (l) { return l.text; }).slice(0, 3).map(function (l, k) {
              return { text: l.text, cur: k === 0 };
            });
          }
          previewLinesEl.innerHTML = slice.map(function (item) {
            return '<div class="' + (item.cur ? 'is-cur' : 'is-dim') + '">' + esc(item.text) + '</div>';
          }).join('');
        }
      }

      function paintShare(track) {
        if (lastShareTrack === track.slug) return;
        lastShareTrack = track.slug;
        var slot = rootEl.querySelector('.js-share-slot');
        var sheetSlot = sheetEl.querySelector('.js-sheet-share-slot');
        var urlEl = rootEl.querySelector('.js-share-url');

        if (!track.shareUrl) {
          if (urlEl) { urlEl.hidden = true; urlEl.textContent = ''; }
          var msg =
            '<div class="ap-share-pending">' +
              '<span>individual song share page for <b>' + esc(track.title) + '</b> is next — previewing <b>Enjoy The Show</b>.</span>' +
              '<a class="ap-pill-btn" href="/album/enjoy-the-show/">open Enjoy The Show share page</a>' +
            '</div>';
          if (slot) slot.innerHTML = msg;
          if (sheetSlot) sheetSlot.innerHTML = '';
          return;
        }

        var fullUrl = 'https://therubberduck.net' + track.shareUrl;
        if (urlEl) {
          urlEl.hidden = false;
          urlEl.href = track.shareUrl;
          urlEl.textContent = fullUrl;
        }

        function buildShareEl(compact) {
          if (!W.trdShare) return null;
          return W.trdShare.build({
            kind: 'song',
            id: track.slug,
            page: fullUrl,
            text: track.title + ' — ' + album.album + ' · ' + album.artist,
            thumb: '/images/album/og/' + track.fileId + '.jpg',
            file: '/images/album/og/' + track.fileId + '.jpg',
            fileName: track.fileId + '.jpg',
            only: ['x', 'truth', 'fb', 'email', 'sms', 'link'],
            compact: !!compact,
            groupLabel: 'share ' + track.title
          });
        }

        if (slot) {
          slot.innerHTML = '';
          var el = buildShareEl(false);
          if (el) slot.appendChild(el);
        }
        if (sheetSlot) {
          sheetSlot.innerHTML = '';
          var sel = buildShareEl(true);
          if (sel) sheetSlot.appendChild(sel);
        }
      }

      function paintTimes(s, t) {
        var d = s.d > 0 ? s.d : (tracks[s.i] ? tracks[s.i].secs : 1);
        t = Math.max(0, Math.min(d, t || 0));
        var pct = Math.min(100, Math.max(0, (t / d) * 100));

        [].forEach.call(scope.querySelectorAll('.js-time-el'), function (el) { el.textContent = fmt(t); });
        [].forEach.call(scope.querySelectorAll('.js-time-end'), function (el) {
          el.textContent = showRemaining ? ('-' + fmt(Math.max(0, d - t))) : fmt(d);
        });
        [].forEach.call(scope.querySelectorAll('.js-scrub'), function (sl) {
          sl.querySelector('.ap-slider-fill').style.width = pct + '%';
          sl.querySelector('.ap-slider-knob').style.left = pct + '%';
          sl.setAttribute('aria-valuenow', Math.round(pct));
        });
        var mf = chrome.querySelector('.js-mbar-fill');
        if (mf) mf.style.width = pct + '%';

        var activeRow = tracklistEl.querySelector('.ap-row[data-i="' + s.i + '"] .ap-row-prog i');
        if (activeRow) activeRow.style.width = pct + '%';
      }

      var lastTrackIdx = -1;
      function paintAll(s, force) {
        var idx = Math.max(0, Math.min(tracks.length - 1, s.i || 0));
        var tr = tracks[idx];
        var t = liveTime();

        /* Play/Pause icons */
        [].forEach.call(scope.querySelectorAll('.js-play, .js-album-play'), function (b) {
          b.innerHTML = s.playing ? IC.pause : IC.play;
          b.setAttribute('aria-pressed', s.playing ? 'true' : 'false');
        });

        /* Shuffle & Repeat */
        [].forEach.call(scope.querySelectorAll('.js-shuffle'), function (b) {
          b.classList.toggle('is-active', !!s.shuffle);
          b.setAttribute('aria-pressed', s.shuffle ? 'true' : 'false');
        });
        [].forEach.call(scope.querySelectorAll('.js-repeat'), function (b) {
          var on = s.repeat === 'all' || s.repeat === 'one';
          b.classList.toggle('is-active', on);
          b.setAttribute('aria-label', 'repeat: ' + (s.repeat || 'off'));
          var badge = b.querySelector('.ap-repeat-one');
          if (badge) badge.hidden = s.repeat !== 'one';
        });

        /* Volume */
        var v = typeof s.vol === 'number' ? s.vol : 1;
        var vIcon = v <= 0.01 ? IC.volMute : (v < 0.5 ? IC.volLo : IC.volHi);
        [].forEach.call(scope.querySelectorAll('.js-mute'), function (b) { b.innerHTML = vIcon; });
        [].forEach.call(scope.querySelectorAll('.js-vol'), function (sl) {
          var vp = Math.round(v * 100);
          sl.querySelector('.ap-slider-fill').style.width = vp + '%';
          sl.querySelector('.ap-slider-knob').style.left = vp + '%';
          sl.setAttribute('aria-valuenow', vp);
        });

        /* Track metadata & rows */
        if (idx !== lastTrackIdx || force) {
          lastTrackIdx = idx;
          var kicker = rootEl.querySelector('.js-np-kicker');
          if (kicker) kicker.textContent = 'track ' + (tr.n < 10 ? '0' + tr.n : tr.n) + ' of ' + tracks.length;
          [].forEach.call(scope.querySelectorAll('.js-np-title'), function (el) { el.textContent = tr.title; });
          [].forEach.call(scope.querySelectorAll('.js-bar-title'), function (el) { el.textContent = tr.title; });
          var mbarSub = chrome.querySelector('.js-mbar-sub');
          if (mbarSub) mbarSub.textContent = album.artist + (tr.hasLyrics ? ' · lyrics' : '');
          var expEl = rootEl.querySelector('.js-np-exp');
          if (expEl) expEl.hidden = !tr.explicit;
          var appleEl = rootEl.querySelector('.js-np-apple');
          if (appleEl) appleEl.href = tr.appleUrl;

          paintShare(tr);

          if (activeLyricsSlug !== tr.fileId) {
            activeLyricsSlug = tr.fileId;
            if (tr.hasLyrics) {
              loadLyrics(tr.fileId).then(function (data) {
                if (activeLyricsSlug === tr.fileId) renderLyricsBoxes(tr, data);
              });
            } else {
              renderLyricsBoxes(tr, null);
            }
          }
        }

        [tracklistEl, sheetQueueEl].forEach(function (ol) {
          [].forEach.call(ol.querySelectorAll('.ap-row'), function (row) {
            var ri = +row.getAttribute('data-i');
            var cur = ri === idx;
            var playing = cur && !!s.playing;
            row.classList.toggle('is-current', cur);
            row.classList.toggle('is-playing', playing);
            var pb = row.querySelector('.ap-row-play');
            if (pb) pb.innerHTML = playing ? IC.pause : IC.play;
            var pr = row.querySelector('.ap-row-prog i');
            if (pr && !cur) pr.style.width = '0%';
          });
        });

        paintTimes(s, t);
        syncLyricHighlight(t, false);
      }

      D.addEventListener('trdpod:state', function (e) { paintAll(e.detail, false); });
      paintAll(getState(), true);

      /* 60fps lyric & progress loop while playing */
      function loop() {
        var s = getState();
        if (s.playing && !scrubbing) {
          var t = liveTime();
          paintTimes(s, t);
          syncLyricHighlight(t, false);
        }
        rafId = W.requestAnimationFrame(loop);
      }
      rafId = W.requestAnimationFrame(loop);
    });
  }

  W.trdAlbumPlayer = { mount: mount };
})();
