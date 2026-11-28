/* Unified full-text search. Runs in the browser. No analytics, no query logging.
   ONE constant: TRD_FULLTEXT_BASE is where the index files live (trailing slash).
   Production files are on R2 at this version. Token rules match tools/search/tokens.mjs.
   TRD-0087 and TRD-0129 are not in this index. */
(function () {
  'use strict';
  var W = window;
  if (W.trdFulltext) return;
  var TRD_FULLTEXT_BASE = 'https://scif-search.therubberduck.net/fulltext/981b404b79/';
  var BASE = TRD_FULLTEXT_BASE;
  var man = null, manP = null, stopSet = null, splitSet = null, shardSet = null;
  var cache = Object.create(null);
  var net = { fetches: 0, bytes: 0 };
  var TOKEN = /[a-z0-9]{2,30}/g;

  function fold(s) {
    return String(s || '').toLowerCase().normalize('NFKD').replace(/\p{M}/gu, '').replace(/[\u2018\u2019\u201c\u201d']/g, '');
  }
  function rawTokens(s) {
    var m = fold(s).match(TOKEN);
    if (!m) return [];
    var seen = {}, out = [], i, t;
    for (i = 0; i < m.length; i++) {
      t = m[i];
      if (t.length < 3 && !/^[0-9]{2}$/.test(t)) continue;
      if (seen[t]) continue;
      seen[t] = 1;
      out.push(t);
    }
    return out;
  }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function rx(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }
  function get(rel) {
    if (cache[rel]) return cache[rel];
    var p = fetch(BASE + rel).then(function (r) {
      if (!r.ok) throw new Error(rel);
      return r.arrayBuffer();
    }).then(function (buf) {
      net.fetches++;
      net.bytes += buf.byteLength;
      return JSON.parse(new TextDecoder('utf-8').decode(buf));
    });
    p.catch(function () { delete cache[rel]; });
    cache[rel] = p;
    return p;
  }
  function manifest() {
    if (manP) return manP;
    manP = get('manifest.json').then(function (m) {
      man = m;
      stopSet = {};
      (m.stop || []).forEach(function (s) { stopSet[s] = 1; });
      splitSet = {};
      (m.split || []).forEach(function (s) { splitSet[s] = 1; });
      shardSet = {};
      (m.shards || []).forEach(function (s) { shardSet[s] = 1; });
      return m;
    });
    manP.catch(function () { manP = null; });
    return manP;
  }
  function shardName(w) {
    var p = (w + '_____').slice(0, 2);
    while (splitSet[p] && p.length < 5) p = (w + '_____').slice(0, p.length + 1);
    return p;
  }
  function decode(s) {
    if (!s) return new Int32Array(0);
    var p = s.split('.'), out = new Int32Array(p.length), prev = -1, i;
    for (i = 0; i < p.length; i++) { prev += parseInt(p[i], 36) + 1; out[i] = prev; }
    return out;
  }
  function postings(word) {
    if (stopSet[word]) return Promise.resolve(new Int32Array(0));
    var name = shardName(word);
    if (!shardSet[name]) return Promise.resolve(new Int32Array(0));
    return get('s/' + name + '.json').then(function (sh) { return decode(sh[word]); });
  }
  function intersect(a, b) {
    var out = [], i = 0, j = 0;
    while (i < a.length && j < b.length) {
      if (a[i] < b[j]) i++;
      else if (a[i] > b[j]) j++;
      else { out.push(a[i]); i++; j++; }
    }
    return Int32Array.from(out);
  }
  function roomOf(id) {
    var rs = man.rooms, lo = 0, hi = rs.length - 1, mid, r;
    while (lo < hi) {
      mid = (lo + hi + 1) >> 1;
      if (rs[mid].from <= id) lo = mid;
      else hi = mid - 1;
    }
    r = rs[lo];
    return id >= r.from && id < r.to ? r : null;
  }
  function fileOf(id) {
    var s = man.starts, lo = 0, hi = s.length - 1, mid;
    while (lo < hi) {
      mid = (lo + hi + 1) >> 1;
      if (s[mid] <= id) lo = mid;
      else hi = mid - 1;
    }
    return lo;
  }
  function termPattern(terms) {
    return terms.map(function (t) {
      return t.split('').map(rx).join("['\u2019]?");
    }).join('|');
  }
  function excerpt(text, terms) {
    var flat = String(text || '').replace(/\s+/g, ' ').trim();
    if (!flat) return '';
    var re = new RegExp('(^|[^A-Za-z0-9])(' + termPattern(terms) + ')(?![A-Za-z0-9])', 'gi');
    var m = re.exec(flat);
    var pos = m ? m.index + m[1].length : 0;
    var start = Math.max(0, pos - 70);
    var end = Math.min(flat.length, (m ? pos : 0) + 160);
    if (start > 0) { var sp = flat.lastIndexOf(' ', start + 12); if (sp > start - 20 && sp < start + 24) start = sp + 1; }
    var slice = flat.slice(start, end);
    var re2 = new RegExp('(^|[^A-Za-z0-9])(' + termPattern(terms) + ')(?![A-Za-z0-9])', 'gi');
    var html = '', last = 0, hit;
    while ((hit = re2.exec(slice))) {
      var a = hit.index + hit[1].length;
      html += esc(slice.slice(last, a)) + '<mark>' + esc(hit[2]) + '</mark>';
      last = a + hit[2].length;
      if (!hit[2].length) re2.lastIndex++;
    }
    html += esc(slice.slice(last));
    return (start > 0 ? '\u2026' : '') + html + (end < flat.length ? '\u2026' : '');
  }
  function score(rec, terms) {
    var title = fold(rec[0]), text = fold(rec[2]), s = 0, i, at;
    for (i = 0; i < terms.length; i++) {
      if (title.indexOf(terms[i]) >= 0) s += 40;
      at = text.indexOf(terms[i]);
      if (at >= 0) s += Math.max(0, 80 - at / 40);
    }
    return s;
  }
  function search(q, opt) {
    opt = opt || {};
    var sample = opt.sample || 4;
    var show = opt.show || sample;
    var only = opt.only || '';
    var before = { fetches: net.fetches, bytes: net.bytes };
    return manifest().then(function () {
      var terms = rawTokens(q).filter(function (t) { return !stopSet[t]; });
      var empty = { q: q, terms: terms, total: 0, rooms: [], fetches: 0, bytes: 0 };
      if (!terms.length) {
        empty.fetches = net.fetches - before.fetches;
        empty.bytes = net.bytes - before.bytes;
        return empty;
      }
      return Promise.all(terms.map(postings)).then(function (lists) {
        lists.sort(function (a, b) { return a.length - b.length; });
        var ids = lists[0];
        for (var i = 1; i < lists.length && ids.length; i++) ids = intersect(ids, lists[i]);
        var buckets = {}, counts = {}, order = [];
        for (var k = 0; k < ids.length; k++) {
          var id = ids[k], room = roomOf(id);
          if (!room) continue;
          counts[room.id] = (counts[room.id] || 0) + 1;
          if (only && room.id !== only) continue;
          var b = buckets[room.id];
          if (!b) { b = buckets[room.id] = []; order.push(room); }
          if (b.length < sample) b.push(id);
        }
        var files = {}, need = [];
        order.forEach(function (room) {
          buckets[room.id].forEach(function (id) {
            var f = fileOf(id);
            if (!files[f]) { files[f] = 1; need.push(f); }
          });
        });
        return Promise.all(need.map(function (f) { return get('r/' + f + '.json').then(function (rows) { return { f: f, rows: rows }; }); })).then(function (loaded) {
          var byFile = {};
          loaded.forEach(function (x) { byFile[x.f] = x.rows; });
          function recAt(id) {
            var f = fileOf(id);
            var rows = byFile[f];
            if (!rows) return null;
            return rows[id - man.starts[f]] || null;
          }
          var rooms = order.map(function (room) {
            var hits = buckets[room.id].map(function (id) {
              var rec = recAt(id);
              if (!rec) return null;
              return { title: rec[0], url: rec[1], excerpt: excerpt(rec[2], terms), score: score(rec, terms) };
            }).filter(Boolean).sort(function (a, b) { return b.score - a.score; }).slice(0, show);
            return { id: room.id, label: room.label, total: counts[room.id] || 0, hits: hits };
          }).filter(function (r) { return r.hits.length; });
          var totalAll = 0;
          man.rooms.forEach(function (r) { totalAll += counts[r.id] || 0; });
          var total = only ? (counts[only] || 0) : totalAll;
          return {
            q: q,
            terms: terms,
            total: total,
            rooms: rooms,
            fetches: net.fetches - before.fetches,
            bytes: net.bytes - before.bytes
          };
        });
      });
    });
  }

  function ensureCss() {
    if (document.getElementById('tn-full-css')) return;
    var st = document.createElement('style');
    st.id = 'tn-full-css';
    st.textContent = [
      '@media (min-width:821px){',
      '.tn-res .tn-full{margin-top:4px;border-top:1px solid #3a2814;padding-top:4px}',
      '.tn-res .tn-full-h{padding:4px 10px 2px;color:#e3a82b;font:700 10px/1.4 "TRN Courier","Courier New",monospace;letter-spacing:.12em;text-transform:uppercase}',
      '.tn-res .tn-full .tn-d{white-space:normal;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}',
      '.tn-res .tn-full mark{background:#ffd54a;color:#000;padding:0 1px}',
      '.tn-res .tn-full-all{color:#ffd77a;font-weight:700}',
      '}',
      '@media (max-width:820px){',
      '.tn-res .tn-full{margin-top:6px;border-top:1px solid #3a2814;padding-top:6px}',
      '.tn-res .tn-full-h{padding:6px 10px 4px;color:#e3a82b;font:700 11px/1.4 "TRN Courier","Courier New",monospace;letter-spacing:.12em;text-transform:uppercase}',
      '.tn-res .tn-full a{padding:10px 10px}',
      '.tn-res .tn-full .tn-d{white-space:normal;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;font-size:13px}',
      '.tn-res .tn-full mark{background:#ffd54a;color:#000;padding:0 1px}',
      '.tn-res .tn-full-all{color:#ffd77a;font-weight:700;padding-top:12px;padding-bottom:12px}',
      '}'
    ].join('');
    (document.head || document.documentElement).appendChild(st);
  }
  function blockHtml(res, q) {
    if (!res || !res.total) return '';
    var h = '<div class="tn-full"><div class="tn-full-h">In the text</div>';
    res.rooms.forEach(function (room) {
      var hit = room.hits[0];
      if (!hit) return;
      h += '<a role="option" href="' + esc(hit.url) + '"><span class="tn-k">' + esc(room.label) + '</span><span class="tn-t">' + esc(hit.title) + '</span><span class="tn-d">' + hit.excerpt + '</span></a>';
    });
    h += '<a class="tn-full-all" role="option" href="/search.html?q=' + encodeURIComponent(q) + '">All ' + res.total.toLocaleString('en-US') + ' full-text matches</a></div>';
    return h;
  }
  function fill(box, q, still) {
    ensureCss();
    return searchBoth(q, { sample: 3, show: 1 }).then(function (res) {
      if (still && !still()) return res;
      var inp = document.getElementById('tn-q');
      if (!box || !inp || inp.value.trim() !== String(q).trim()) return res;
      var slot = box.querySelector('.tn-full-slot');
      if (!slot) return res;
      slot.innerHTML = blockHtml(res, q);
      if (res.total) { var empty = box.querySelector('#tn-empty'); if (empty) empty.remove(); }
      return res;
    }).catch(function () { return null; });
  }
  function pageHtml(res, q, only) {
    var chips = '<div class="ft-chips"><button type="button" data-room=""' + (only ? '' : ' aria-pressed="true"') + '>All rooms</button>';
    (man.rooms || []).forEach(function (r) {
      chips += '<button type="button" data-room="' + esc(r.id) + '"' + (only === r.id ? ' aria-pressed="true"' : '') + '>' + esc(r.label) + '</button>';
    });
    chips += '</div>';
    if (!res.terms.length) {
      return chips + '<p class="ft-wait">Type a word of at least three letters.</p>';
    }
    if (!res.total) {
      return chips + '<p class="ft-wait">No passage contains every word in \u201c' + esc(q) + '\u201d.</p>';
    }
    var h = chips + '<p class="ft-count">' + res.total.toLocaleString('en-US') + ' passages</p>';
    res.rooms.forEach(function (room) {
      h += '<section class="ft-room"><h2>' + esc(room.label) + '</h2>';
      room.hits.forEach(function (hit) {
        h += '<a class="ft-hit" href="' + esc(hit.url) + '"><b>' + esc(hit.title) + '</b><span>' + hit.excerpt + '</span></a>';
      });
      if (room.total > room.hits.length) h += '<p class="ft-more">' + room.total.toLocaleString('en-US') + ' in this room. The list shows the first matches.</p>';
      h += '</section>';
    });
    return h;
  }
  function renderPage(el, q) {
    var only = '';
    function draw() {
      el.innerHTML = '<p class="ft-wait">Searching the text\u2026</p>';
      return searchBoth(q, { sample: only ? 12 : 4, show: only ? 12 : 4, only: only }).then(function (res) {
        el.innerHTML = pageHtml(res, q, only);
        [].forEach.call(el.querySelectorAll('[data-room]'), function (b) {
          b.addEventListener('click', function () {
            only = b.getAttribute('data-room') || '';
            draw();
          });
        });
        return res;
      }).catch(function () {
        el.innerHTML = '<p class="ft-wait">The full-text index is not at this address yet (' + esc(BASE) + ').</p>';
      });
    }
    return draw();
  }


  /* Preview overlay: TRD-0246 page records, merged into the SCI[F] room. */
  var EXTRA_BASE = 'https://scif-search.therubberduck.net/preview-trd-0246/';
  var extraIdx = null, extraP = null;
  function extraIndex() {
    if (extraP) return extraP;
    extraP = fetch(EXTRA_BASE + 'index.json').then(function (r) { if (!r.ok) throw new Error('extra'); return r.json(); }).then(function (m) { extraIdx = m; return m; });
    extraP.catch(function () { extraP = null; });
    return extraP;
  }
  function extraHits(q) {
    return extraIndex().then(function (ex) {
      var terms = rawTokens(q);
      if (!terms.length) return [];
      var pages = null;
      terms.forEach(function (t) {
        var ps = (ex.postings && ex.postings[t]) ? ex.postings[t].slice() : [];
        pages = pages ? pages.filter(function (p) { return ps.indexOf(p) >= 0; }) : ps;
      });
      if (!pages || !pages.length) return [];
      return pages.map(function (p) {
        var text = (ex.text && ex.text[p - 1]) || '';
        var title = ex.title + ' \u00b7 p. ' + p;
        var rec = [title, '/pdfs.html?open=' + encodeURIComponent(ex.id) + '&p=' + p, text];
        return { title: title, url: rec[1], excerpt: excerpt(text, terms), score: score(rec, terms) + 20 };
      }).sort(function (a, b) { return b.score - a.score; });
    }).catch(function () { return []; });
  }
  var _search = search;
  function searchBoth(q, opt) {
    opt = opt || {};
    return Promise.all([_search(q, opt).catch(function () { return { q: q, terms: [], total: 0, rooms: [] }; }), extraHits(q)]).then(function (pair) {
      var res = pair[0], extra = pair[1] || [];
      if (!extra.length) return res;
      if (opt.only && opt.only !== 'scif') return res;
      var show = opt.show || opt.sample || 4;
      var room = null, rooms = res.rooms ? res.rooms.slice() : [];
      for (var i = 0; i < rooms.length; i++) if (rooms[i].id === 'scif') room = rooms[i];
      if (!room) {
        room = { id: 'scif', label: 'SCI[F]', total: 0, hits: [] };
        rooms.unshift(room);
      }
      var seen = {};
      room.hits.forEach(function (h) { seen[h.url] = 1; });
      extra.forEach(function (h) {
        if (seen[h.url]) return;
        room.hits.push(h);
        room.total++;
        res.total++;
      });
      room.hits.sort(function (a, b) { return (b.score || 0) - (a.score || 0); });
      if (room.hits.length > show) room.hits = room.hits.slice(0, show);
      res.rooms = rooms;
      return res;
    });
  }
  W.trdFulltext = { search: searchBoth, fill: fill, renderPage: renderPage, base: BASE };

})();
