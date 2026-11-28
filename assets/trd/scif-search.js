/* SCI[F] full-text search engine (browser side). Built by tools/scif-fulltext-build.py.
   Searches the text INSIDE every PDF in the room, page by page, plus titles, shelves and keywords.
   Nothing is loaded until the first search: a small manifest, then only the index shards for the words
   typed (about 5-150 KB each), then the text of the few pages shown as snippets (about 180 KB per part).
   API (window.scifSearch):
     search(query)            -> Promise {terms, docs:[{i,id,title,shelf,nPages,pages:[...],score,pageLevel}], total, totalPages, ignored, phrases}
     snippets(doc, res, n)    -> Promise [{p, html}]   (n snippets, highlighted, from pages that really match)
     href(doc, p)             -> /pdfs.html?open=TRD-0001&p=12
     manifest()               -> Promise {docs:[[id,title,shelf,pages,per,kw]...]}
     pageText(id, p)          -> Promise string        (the canonical page-level text, reusable by other tools)
   Query syntax: words are ANDed on the same page; "quoted phrase"; word* for any ending. */
(function () {
  'use strict';
  var W = window; if (W.scifSearch) return;
  var BASE = 'https://scif-search.therubberduck.net/scif-search/3de5950a08/';   /* Cloudflare R2, versioned folder; stamped by tools/scif-fulltext-build.py */
  var man = null, manP = null, shardSet = null, splitSet = null, stopSet = null, shardP = {}, metaP = {}, partP = {};
  function get(u) { return fetch(u).then(function (r) { if (!r.ok) throw new Error(u); return r.json(); }); }
  function fold(s) { return String(s).toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g, '').replace(/[\u2018\u2019]/g, "'"); }
  /* same length as the input, for finding snippet positions */
  function foldLen(s) { var o = '', c, f; for (var i = 0; i < s.length; i++) { c = s.charAt(i); f = c.toLowerCase(); if (f.length !== 1) f = c; if (f.charCodeAt(0) > 127) { var n = c.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase(); f = n.length === 1 ? n : f; } o += f; } return o; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function rx(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }
  var TOKEN = /[a-z0-9]{3,30}|[0-9]{2}/g;
  function manifest() {
    if (manP) return manP;
    manP = get(BASE + 'search/manifest.json').then(function (m) { man = m; shardSet = {}; m.shards.forEach(function (s) { shardSet[s] = 1; }); splitSet = {}; m.split.forEach(function (s) { splitSet[s] = 1; }); stopSet = {}; m.stop.forEach(function (s) { stopSet[s] = 1; }); m.hay = m.docs.map(function (d) { return foldLen(d[1] + ' ' + d[2] + ' ' + d[5] + ' ' + d[0]); }); m.hayT = m.docs.map(function (d) { return foldLen(d[1] + ' ' + d[0]); }); return m; });
    manP.catch(function () { manP = null; });
    return manP;
  }
  function shardName(w) { var p = (w + '__').slice(0, 2); while (splitSet[p] && p.length < 5) p = (w + '_____').slice(0, p.length + 1); return p; }
  function shard(p) { return shardP[p] || (shardP[p] = get(BASE + 'search/' + encodeURIComponent(p) + '.json').catch(function (e) { delete shardP[p]; throw e; })); }
  function parse(entry) { var m = {}; entry.split(';').forEach(function (e) { var k = e.indexOf(':'); m[+e.slice(0, k)] = e.slice(k + 1).split(',').map(Number); }); return m; }
  function union(a, b) { for (var d in b) { if (!a[d]) a[d] = b[d]; else { var s = {}, o = []; a[d].concat(b[d]).forEach(function (p) { if (!s[p]) { s[p] = 1; o.push(p); } }); a[d] = o.sort(function (x, y) { return x - y; }); } } return a; }
  function exact(words) {
    var by = {}, out = {};
    words.forEach(function (w) { var n = shardName(w); if (shardSet[n]) (by[n] = by[n] || []).push(w); });
    return Promise.all(Object.keys(by).map(function (n) { return shard(n).then(function (sh) { by[n].forEach(function (w) { if (sh[w]) union(out, parse(sh[w])); }); }); })).then(function () { return out; });
  }
  function prefixed(pre) {
    var names = man.shards.filter(function (s) { return s.indexOf(pre) === 0 || pre.indexOf(s) === 0; }).slice(0, 40), out = {};
    return Promise.all(names.map(function (n) { return shard(n); })).then(function (shs) {
      var ws = []; shs.forEach(function (sh) { for (var w in sh) if (w.indexOf(pre) === 0) ws.push(w); });
      ws.sort(function (a, b) { return a.length - b.length || (a < b ? -1 : 1); });
      ws.slice(0, 300).forEach(function (w) { for (var i = 0; i < shs.length; i++) if (shs[i][w]) { union(out, parse(shs[i][w])); break; } });
      return out;
    });
  }
  function variants(t) { var v = [t]; if (t.length > 3 && /s$/.test(t) && !/ss$/.test(t)) v.push(t.slice(0, -1)); else if (!/s$/.test(t)) { v.push(t + 's'); } return v; }
  function parseQuery(q) {
    var phrases = [], terms = [], seen = {}, ignored = [], re = /"([^"]+)"|(\S+)/g, m;
    function add(t, wild) { if (seen[t]) { if (wild) seen[t].wild = true; return; } seen[t] = { t: t, wild: !!wild, prefix: false }; terms.push(seen[t]); }
    while ((m = re.exec(q))) {
      if (m[1] !== undefined) { var f = fold(m[1]); var tk = f.match(TOKEN) || []; if (tk.length) { phrases.push(f.replace(/\s+/g, ' ').trim()); tk.forEach(function (t) { add(t, false); }); } }
      else { var w = fold(m[2]), wild = /\*$/.test(w), tk2 = w.match(TOKEN) || []; if (!tk2.length) { if (w.replace(/[^a-z0-9]/g, '')) ignored.push(m[2]); continue; } tk2.forEach(function (t, i) { add(t, wild && i === tk2.length - 1); }); }
    }
    return { terms: terms, phrases: phrases, ignored: ignored };
  }
  function search(q) {
    return manifest().then(function () {
      var pq = parseQuery(q), terms = [], ignored = pq.ignored.slice();
      pq.terms.forEach(function (x) { if (stopSet[x.t]) ignored.push(x.t); else terms.push(x); });
      var res = { terms: terms, phrases: pq.phrases, ignored: ignored, docs: [], total: 0, totalPages: 0 };
      if (!terms.length) return res;
      return Promise.all(terms.map(function (x, k) {
        var p = x.wild ? prefixed(x.t) : exact(variants(x.t));
        return p.then(function (m) { if (!x.wild && !Object.keys(m).length && x.t.length >= 3) { x.prefix = true; return prefixed(x.t); } if (x.wild) x.prefix = true; return m; });
      })).then(function (maps) {
        var docs = Object.keys(maps[0]);
        maps.forEach(function (m) { docs = docs.filter(function (d) { return m[d]; }); });
        var out = [], pageLevel = true;
        docs.forEach(function (d) {
          var ps = maps[0][d].filter(function (p) { return maps.every(function (m) { return m[d].indexOf(p) >= 0; }); });
          if (ps.length) out.push({ d: +d, pages: ps, pageLevel: true });
        });
        if (!out.length && docs.length && terms.length > 1) {   /* same document, different pages */
          pageLevel = false;
          docs.forEach(function (d) { var best = maps.reduce(function (a, m) { return m[d].length < a.length ? m[d] : a; }, maps[0][d]); out.push({ d: +d, pages: best, pageLevel: false }); });
        }
        res.pageLevel = pageLevel;
        var tf = terms.map(function (x) { return x.t; });
        res.docs = out.map(function (o) {
          var dd = man.docs[o.d], n = o.pages.length, hay = man.hay[o.d], ht = man.hayT[o.d];
          var s = Math.log(1 + n) * 10 + 30 * Math.min(1, n / Math.max(1, dd[3]) * 4);
          if (tf.every(function (t) { return ht.indexOf(t) >= 0; })) s += 60; else if (tf.every(function (t) { return hay.indexOf(t) >= 0; })) s += 25;
          if (!pageLevel) s -= 20;
          return { i: o.d, id: dd[0], title: dd[1], shelf: dd[2], nPages: dd[3], pages: o.pages, score: s, pageLevel: o.pageLevel };
        }).sort(function (a, b) { return b.score - a.score || a.i - b.i; });
        res.total = res.docs.length; res.totalPages = res.docs.reduce(function (a, d) { return a + d.pages.length; }, 0);
        return res;
      });
    });
  }
  function meta(id) { return metaP[id] || (metaP[id] = get(BASE + 'text/' + id + '.json').catch(function (e) { delete metaP[id]; throw e; })); }
  function part(id, k) { var key = id + '.' + k; return partP[key] || (partP[key] = get(BASE + 'text/' + id + '.' + k + '.json').catch(function (e) { delete partP[key]; throw e; })); }
  function pageTextSafe(id, p) {
    return meta(id).then(function (m) {
      if (m.text) return m.text[p - 1] || '';
      var k = Math.floor((p - 1) / m.per);
      return part(id, k).then(function (pt) { return pt.text[p - pt.from] || ''; });
    }).catch(function () { return ''; });
  }
  function partOf(id, p, m) { return m.text ? 0 : Math.floor((p - 1) / m.per); }
  function termRx(x) {
    var vs = x.prefix || x.wild ? [x.t] : variants(x.t), body = vs.map(rx).join('|');
    return x.prefix || x.wild ? '(' + rx(x.t) + '[a-z0-9]*)' : '(?:' + body + ')';
  }
  function makeSnippet(text, res) {
    var f = foldLen(text), pos = [];
    res.terms.forEach(function (x, ti) {
      var r = new RegExp('(^|[^a-z0-9])(' + (x.prefix || x.wild ? rx(x.t) + '[a-z0-9]*' : variants(x.t).map(rx).join('|')) + ')(?![a-z0-9])', 'g'), m;
      while ((m = r.exec(f)) && pos.length < 400) { var st = m.index + m[1].length; pos.push([st, m[2].length, ti]); if (m[2].length === 0) r.lastIndex++; }
    });
    res.phrases.forEach(function (ph) { var i = f.indexOf(ph); while (i >= 0 && pos.length < 600) { pos.push([i, ph.length, -1]); i = f.indexOf(ph, i + ph.length); } });
    if (!pos.length) return { html: esc(text.slice(0, 220)) + (text.length > 220 ? '\u2026' : ''), hits: 0, distinct: 0 };
    pos.sort(function (a, b) { return a[0] - b[0]; });
    var W2 = 230, best = 0, bs = 0, bi = 0;
    for (var i = 0; i < pos.length; i++) {
      var seen = {}, c = 0;
      for (var j = i; j < pos.length && pos[j][0] < pos[i][0] + W2 - 40; j++) { if (!seen[pos[j][2]]) { seen[pos[j][2]] = 1; c++; } }
      if (c > best) { best = c; bi = i; }
    }
    var start = Math.max(0, pos[bi][0] - 70), end = Math.min(text.length, start + W2);
    if (start > 0) { var sp = text.indexOf(' ', start); if (sp > -1 && sp < pos[bi][0]) start = sp + 1; }
    if (end < text.length) { var sp2 = text.lastIndexOf(' ', end); if (sp2 > pos[bi][0] + 1) end = sp2; }
    var html = '', cur = start;
    pos.filter(function (p) { return p[0] >= start && p[0] + p[1] <= end; }).forEach(function (p) {
      if (p[0] < cur) { return; }
      html += esc(text.slice(cur, p[0])) + '<mark>' + esc(text.slice(p[0], p[0] + p[1])) + '</mark>'; cur = p[0] + p[1];
    });
    html += esc(text.slice(cur, end));
    return { html: (start > 0 ? '\u2026' : '') + html + (end < text.length ? '\u2026' : ''), hits: pos.length, distinct: best };
  }
  function snippets(doc, res, n) {
    n = n || 3;
    return meta(doc.id).then(function (m) {
      var cand = [], used = {}, nparts = 0;
      for (var i = 0; i < doc.pages.length && cand.length < 12; i++) {
        var p = doc.pages[i], k = partOf(doc.id, p, m);
        if (!used[k]) { if (nparts >= 3) continue; used[k] = 1; nparts++; }
        cand.push(p);
      }
      return Promise.all(cand.map(function (p) { return pageTextSafe(doc.id, p).then(function (t) { return { p: p, t: t }; }); })).then(function (pg) {
        var out = [];
        pg.forEach(function (x) {
          if (!x.t) return;
          if (res.phrases.length) { var f = foldLen(x.t).replace(/\s+/g, ' '); if (!res.phrases.every(function (ph) { return f.indexOf(ph) >= 0; })) return; }
          var s = makeSnippet(x.t, res); out.push({ p: x.p, html: s.html, rank: s.distinct * 100 + Math.min(s.hits, 50) });
        });
        out.sort(function (a, b) { return b.rank - a.rank || a.p - b.p; });
        return out.slice(0, n).sort(function (a, b) { return a.p - b.p; });
      });
    });
  }
  function href(doc, p) { return '/pdfs.html?open=' + encodeURIComponent(doc.id) + (p ? '&p=' + p : ''); }

  /* Preview overlay: TRD-0246 (Wikimedia unredacted scan). Live indexes are unchanged. */
  var EXTRA_BASE = 'https://scif-search.therubberduck.net/preview-trd-0246/';
  var extraIdx = null, extraP = null;
  function extraIndex() {
    if (extraP) return extraP;
    extraP = fetch(EXTRA_BASE + 'index.json').then(function (r) { if (!r.ok) throw new Error('extra'); return r.json(); }).then(function (m) { extraIdx = m; return m; });
    extraP.catch(function () { extraP = null; });
    return extraP;
  }
  function searchExtra(q) {
    return extraIndex().then(function (ex) {
      var pq = parseQuery(q), terms = [], ignored = pq.ignored.slice();
      pq.terms.forEach(function (x) { if (stopSet && stopSet[x.t]) ignored.push(x.t); else terms.push(x); });
      var empty = { terms: terms, phrases: pq.phrases, ignored: ignored, docs: [], total: 0, totalPages: 0, pageLevel: true };
      if (!terms.length) return empty;
      var pages = null;
      terms.forEach(function (x) {
        var ps = [];
        if (x.wild) {
          Object.keys(ex.postings).forEach(function (w) { if (w.indexOf(x.t) === 0) ps = ps.concat(ex.postings[w]); });
        } else {
          variants(x.t).forEach(function (v) { if (ex.postings[v]) ps = ps.concat(ex.postings[v]); });
        }
        var uniq = [], seen = {};
        ps.sort(function (a, b) { return a - b; }).forEach(function (p) { if (!seen[p]) { seen[p] = 1; uniq.push(p); } });
        pages = pages ? pages.filter(function (p) { return uniq.indexOf(p) >= 0; }) : uniq;
      });
      if (pq.phrases.length && pages && pages.length) {
        pages = pages.filter(function (p) {
          var f = foldLen(ex.text[p - 1] || '').replace(/\s+/g, ' ');
          return pq.phrases.every(function (ph) { return f.indexOf(ph) >= 0; });
        });
      }
      if (!pages || !pages.length) return empty;
      var doc = { i: 100000, id: ex.id, title: ex.title, shelf: ex.shelf, nPages: ex.pages, pages: pages, score: 80, pageLevel: true };
      return { terms: terms, phrases: pq.phrases, ignored: ignored, docs: [doc], total: 1, totalPages: pages.length, pageLevel: true };
    }).catch(function () { return { terms: [], phrases: [], ignored: [], docs: [], total: 0, totalPages: 0 }; });
  }
  function searchBoth(q) {
    return Promise.all([search(q).catch(function () { return { terms: [], phrases: [], ignored: [], docs: [], total: 0, totalPages: 0 }; }), searchExtra(q)]).then(function (pair) {
      var a = pair[0], b = pair[1];
      if (!b || !b.docs || !b.docs.length) return a;
      a.docs = (a.docs || []).concat(b.docs).sort(function (x, y) { return (y.score || 0) - (x.score || 0); });
      a.total = a.docs.length;
      a.totalPages = a.docs.reduce(function (n, d) { return n + (d.pages ? d.pages.length : 0); }, 0);
      if (b.terms && b.terms.length && !(a.terms && a.terms.length)) a.terms = b.terms;
      return a;
    });
  }
  function pageTextBoth(id, p) {
    if (id === 'TRD-0246') return extraIndex().then(function (ex) { return (ex.text && ex.text[p - 1]) || ''; }).catch(function () { return ''; });
    return pageTextSafe(id, p);
  }
  function snippetsBoth(doc, res, n) {
    if (doc.id !== 'TRD-0246') return snippets(doc, res, n);
    return extraIndex().then(function (ex) {
      n = n || 3;
      var out = [];
      (doc.pages || []).slice(0, 12).forEach(function (p) {
        var t = (ex.text && ex.text[p - 1]) || '';
        if (!t) return;
        if (res.phrases && res.phrases.length) {
          var f = foldLen(t).replace(/\s+/g, ' ');
          if (!res.phrases.every(function (ph) { return f.indexOf(ph) >= 0; })) return;
        }
        var sn = makeSnippet(t, res);
        out.push({ p: p, html: sn.html, rank: sn.distinct * 100 + Math.min(sn.hits, 50) });
      });
      out.sort(function (a, b) { return b.rank - a.rank || a.p - b.p; });
      return out.slice(0, n).sort(function (a, b) { return a.p - b.p; });
    });
  }
  W.scifSearch = { search: searchBoth, snippets: snippetsBoth, href: href, manifest: manifest, pageText: pageTextBoth, fold: fold, version: function () { return BASE; } };

})();
