#!/usr/bin/env node
/* Build the unified full-text index for the header search.
   The index is not committed. Load it from TRD_FULLTEXT_BASE in
   assets/trd/fulltext-search.js (a local path for this preview, or an R2 URL later).

   From the repo root:
     node tools/search/build-unified.mjs
     node tools/search/build-unified.mjs --scif ./scif
     node tools/search/build-unified.mjs --scif https://HOST/scif/
     node tools/search/build-unified.mjs --scif https://HOST/scif/ --scif-manifest ./scif/search/manifest.json

   --scif is the SCI[F] root, a directory or a URL, with the same layout as scif/:
   search/manifest.json and text/<id>.json (plus text/<id>.<part>.json when split).
   TRD-0087 is never read and never written. See exclude.mjs. */
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
import { EXCLUDE_DOCS, excludedUrl, selectDocs } from './exclude.mjs';
import { STOP_WORDS, tokenize, encodeIds } from './tokens.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
process.chdir(ROOT);

const STORE_CAP = 15000;
const CHUNK_CHARS = 32000;
const SHARD_MAX = 140000;
const LABELS = {
  scif: 'SCI[F]',
  drop: 'Q drop',
  eo: 'EO',
  x: 'X post',
  meme: 'Meme',
  lyric: 'Lyric',
  listen: 'Recording',
  video: 'Video',
};

function arg(name, fallback) {
  const i = process.argv.indexOf(name);
  if (i < 0) return fallback;
  const v = process.argv[i + 1];
  if (!v || v.startsWith('--')) {
    console.error('Missing value for ' + name);
    process.exit(1);
  }
  return v;
}

function isUrl(s) {
  return /^https?:\/\//i.test(String(s || ''));
}

function assertExclusionList() {
  const { keep, skipped } = selectDocs([
    ['TRD-0087', 'no', 'x', 92, 0, ''],
    ['TRD-0129', 'no', 'x', 1, 0, ''],
    ['TRD-0001', 'yes', 'y', 10, 0, ''],
  ]);
  if (skipped.join(',') !== 'TRD-0087,TRD-0129' || keep.length !== 1 || keep[0][0] !== 'TRD-0001') {
    throw new Error('Exclusion list failed its self-check');
  }
}

function clean(s) {
  return String(s || '')
    .replace(/https?:\/\/\S*wikipedia\.org\S*/gi, ' ')
    .replace(/wikipedia(?:,? the free encyclopedia)?/gi, '')
    .replace(/https?:\/\/\S+/gi, ' ')
    .replace(/[\u0000-\u0008\u000b-\u001f\u007f]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function unescapeHtml(s) {
  return String(s || '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;|&apos;|&#x27;/g, "'")
    .replace(/&middot;/g, '·')
    .replace(/&#\d+;/g, ' ');
}

function stripTags(s) {
  return unescapeHtml(String(s || '').replace(/<[^>]+>/g, ' '));
}

async function readJson(base, rel) {
  if (isUrl(base)) {
    const root = base.endsWith('/') ? base : base + '/';
    const url = new URL(rel.replace(/^\//, ''), root);
    const r = await fetch(url, { headers: { 'User-Agent': 'therubberduck-preview' } });
    if (!r.ok) throw new Error('GET ' + url + ' -> ' + r.status);
    return r.json();
  }
  return JSON.parse(fs.readFileSync(path.join(base, rel), 'utf8'));
}

function clock(sec) {
  sec = Math.max(0, Math.floor(+sec || 0));
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return m + ':' + String(s).padStart(2, '0');
}

function textFrag(s) {
  const words = clean(s).split(/\s+/).slice(0, 6).join(' ');
  if (words.length < 12) return '';
  return '#:~:text=' + encodeURIComponent(words);
}

function pre(w, n) {
  return (w + '_____').slice(0, n);
}

function dirBytes(dir) {
  let n = 0;
  let b = 0;
  if (!fs.existsSync(dir)) return { n, b };
  for (const f of fs.readdirSync(dir)) {
    const st = fs.statSync(path.join(dir, f));
    if (st.isFile()) {
      n++;
      b += st.size;
    }
  }
  return { n, b };
}

function scanExcluded(outDir) {
  const rdir = path.join(outDir, 'r');
  let seen = 0;
  for (const f of fs.readdirSync(rdir)) {
    const arr = JSON.parse(fs.readFileSync(path.join(rdir, f), 'utf8'));
    for (const rec of arr) {
      seen++;
      const url = rec[1];
      if (excludedUrl(url)) throw new Error('Excluded document was written into the index: ' + url);
      for (const id of EXCLUDE_DOCS) {
        if (String(url).includes(id)) throw new Error('Excluded id in a result URL: ' + url);
      }
    }
  }
  if (!seen) throw new Error('Index has no records');
  return seen;
}

async function main() {
  assertExclusionList();
  /* Same folder the live SCI[F] search uses. Override with --scif for a local copy. */
const SCIF_R2 = 'https://scif-search.therubberduck.net/scif-search/2beb375c5b/';
const scif = arg('--scif', SCIF_R2);
  const scifManifest = arg('--scif-manifest', '');
  const out = path.resolve(arg('--out', 'search/unified'));
  if (out === ROOT || !out.startsWith(ROOT + path.sep)) {
    throw new Error('--out must stay inside the repo');
  }

  const man = scifManifest
    ? JSON.parse(fs.readFileSync(path.resolve(scifManifest), 'utf8'))
    : await readJson(scif, 'search/manifest.json');
  const listed = new Map((man.docs || []).map((d) => [d[0], d]));
  const { keep, skipped } = selectDocs(man.docs || []);
  if (listed.has('TRD-0087') && !skipped.includes('TRD-0087')) {
    throw new Error('TRD-0087 is in the SCI[F] manifest and the exclusion list did not drop it');
  }
  for (const id of skipped) {
    if (!EXCLUDE_DOCS.includes(id)) throw new Error('Unexpected skip ' + id);
  }

  fs.rmSync(out, { recursive: true, force: true });
  fs.mkdirSync(path.join(out, 'r'), { recursive: true });
  fs.mkdirSync(path.join(out, 's'), { recursive: true });

  const post = Object.create(null);
  const stats = Object.create(null);
  const idRoom = [];
  const roomOrder = [];
  let nextId = 0;
  let buf = [];
  let bufStart = 0;
  let bufBytes = 0;
  const starts = [];

  function flush() {
    if (!buf.length) return;
    starts.push(bufStart);
    fs.writeFileSync(path.join(out, 'r', (starts.length - 1) + '.json'), JSON.stringify(buf));
    buf = [];
    bufBytes = 0;
  }

  function begin(room) {
    roomOrder.push({ id: room, from: nextId });
  }
  function end() {
    roomOrder[roomOrder.length - 1].to = nextId;
  }

  function add(room, title, url, text) {
    const full = clean(text);
    const label = clean(title).slice(0, 180);
    if (!full || !label || !url) return false;
    if (excludedUrl(url)) throw new Error('Refusing to index excluded URL ' + url);
    const toks = tokenize(label + ' ' + full);
    if (!toks.length) return false;
    const id = nextId++;
    const stored = full.length > STORE_CAP ? full.slice(0, STORE_CAP) : full;
    if (!buf.length) bufStart = id;
    buf.push([label, url, stored]);
    bufBytes += label.length + url.length + stored.length;
    idRoom[id] = room;
    const st = stats[room] || (stats[room] = { n: 0, text: 0 });
    st.n++;
    st.text += stored.length;
    for (const w of toks) {
      const a = post[w];
      if (a) a.push(id);
      else post[w] = [id];
    }
    if (bufBytes >= CHUNK_CHARS) flush();
    return true;
  }

  /* SCI[F] pages. Excluded ids are not opened. */
  begin('scif');
  let missing = 0;
  let scifPages = 0;
  for (let i = 0; i < keep.length; i++) {
    const d = keep[i];
    const id = d[0];
    let meta;
    try {
      meta = await readJson(scif, 'text/' + id + '.json');
    } catch (e) {
      missing++;
      continue;
    }
    const title = meta.title || d[1] || id;
    const pages = [];
    if (Array.isArray(meta.text)) {
      meta.text.forEach((t, n) => pages.push([n + 1, t]));
    } else if (meta.parts) {
      for (let k = 0; k < meta.parts; k++) {
        const part = await readJson(scif, 'text/' + id + '.' + k + '.json');
        const from = part.from || k * (meta.per || 1) + 1;
        (part.text || []).forEach((t, n) => pages.push([from + n, t]));
      }
    }
    for (const [p, t] of pages) {
      const href = '/pdfs.html?open=' + encodeURIComponent(id) + '&p=' + p;
      if (add('scif', title + ' · p. ' + p, href, t)) scifPages++;
    }
    if ((i + 1) % 40 === 0) process.stdout.write('scif ' + (i + 1) + '/' + keep.length + '\n');
  }
  end();
  const skippedNote = EXCLUDE_DOCS.map((id) => id + (listed.has(id) ? ' (' + listed.get(id)[3] + ' pages, not read)' : ' (not in this source)')).join(', ');
  console.log('SCI[F] indexed pages ' + scifPages + '; missing files ' + missing + '; excluded ' + skippedNote);

  /* Q drops. */
  begin('drop');
  const window = {};
  vm.runInNewContext(fs.readFileSync('data/drops.js', 'utf8'), { window });
  if (!Array.isArray(window.QDROPS)) throw new Error('data/drops.js did not set QDROPS');
  let drops = 0;
  for (const row of window.QDROPS) {
    const n = row[0];
    const text = row[5];
    if (add('drop', 'Q drop ' + n, '/drops/' + n + '/', 'Q drop ' + n + ' ' + (text || ''))) drops++;
  }
  end();
  console.log('Q drops ' + drops);

  /* Executive orders. Section anchors are not in the HTML, so each section
     gets a text fragment when the opening words are long enough to be specific. */
  begin('eo');
  let orders = 0;
  let sections = 0;
  const eoDirs = fs.readdirSync('eo-library').filter((name) => /^\d+$/.test(name));
  for (const num of eoDirs) {
    const html = fs.readFileSync(path.join('eo-library', num, 'index.html'), 'utf8');
    const titleM = html.match(/<p class="eo-doc-title">([\s\S]*?)<\/p>/);
    const title = clean(stripTags(titleM ? titleM[1] : 'Executive Order ' + num));
    const bodyM = html.match(/<div class="eo-doc-body">([\s\S]*?)<\/div>\s*<\/div>\s*<\/section>/);
    const paras = bodyM
      ? [...bodyM[1].matchAll(/<p[^>]*>([\s\S]*?)<\/p>/g)].map((m) => clean(stripTags(m[1]))).filter(Boolean)
      : [];
    const groups = [];
    let cur = null;
    for (const p of paras) {
      const hm = p.match(/^(?:Section\s+\d+[A-Za-z]?|Sec\.\s+\d+[A-Za-z]?)\b/);
      if (hm) {
        if (cur) groups.push(cur);
        cur = { heading: hm[0], text: p };
      } else if (!cur) {
        cur = { heading: '', text: p };
      } else {
        cur.text += ' ' + p;
      }
    }
    if (cur) groups.push(cur);
    if (!groups.length) {
      if (add('eo', 'EO ' + num + ' · ' + title, '/eo-library/' + num + '/', title)) {
        orders++;
        sections++;
      }
      continue;
    }
    let any = false;
    for (const g of groups) {
      const label = 'EO ' + num + ' · ' + (g.heading ? g.heading + ' · ' : '') + title;
      const frag = textFrag(g.text);
      if (add('eo', label, '/eo-library/' + num + '/' + frag, 'Executive Order ' + num + ' ' + g.text)) {
        any = true;
        sections++;
      }
    }
    if (any) orders++;
  }
  end();
  console.log('Executive orders ' + orders + '; sections ' + sections);

  /* X posts. */
  begin('x');
  let posts = 0;
  const months = fs.readdirSync('x/data/p').filter((f) => f.endsWith('.json')).sort();
  for (const f of months) {
    const arr = JSON.parse(fs.readFileSync(path.join('x/data/p', f), 'utf8'));
    for (const p of arr) {
      if (!p || !p.i || !p.x) continue;
      const when = (p.c || '').slice(0, 10);
      const line = clean(p.x).slice(0, 140);
      const label = (when ? when + ' · ' : '') + (line || 'X post');
      if (add('x', label, '/x/post.html?id=' + p.i, p.x)) posts++;
    }
  }
  end();
  console.log('X posts ' + posts);

  /* Meme OCR, only where the image text yields real tokens. */
  begin('meme');
  const mem = JSON.parse(fs.readFileSync('memes/data/memes.json', 'utf8'));
  let memes = 0;
  let memesOcr = 0;
  for (const it of mem.items || []) {
    const ocr = clean(it.ocr || '');
    const words = (it.textWords || []).map((w) => clean(w)).filter((w) => w.length >= 3);
    if (ocr) memesOcr++;
    const blob = clean((ocr + ' ' + words.join(' ')).trim());
    if (!blob) continue;
    const label = (it.title || it.id) + ' · meme';
    if (add('meme', label, '/memes/share/' + it.id + '.html', blob)) memes++;
  }
  end();
  console.log('Memes with an OCR field ' + memesOcr + '; indexed ' + memes);

  /* Time-synced lyrics. Each sung line is its own hit. */
  begin('lyric');
  const album = JSON.parse(fs.readFileSync('data/album/tracks.json', 'utf8'));
  let lines = 0;
  let tracks = 0;
  for (const t of album.tracks || []) {
    const lp = path.join('data/album/lyrics', t.fileId + '.json');
    if (!fs.existsSync(lp)) continue;
    const lyr = JSON.parse(fs.readFileSync(lp, 'utf8'));
    let n = 0;
    for (const ln of lyr.lines || []) {
      if (!ln || !String(ln.text || '').trim()) continue;
      const at = +ln.t || 0;
      const href = '/album/' + t.slug + '/#t=' + at;
      if (add('lyric', t.title + ' · ' + clock(at), href, ln.text)) {
        lines++;
        n++;
      }
    }
    if (n) tracks++;
  }
  end();
  console.log('Lyric tracks ' + tracks + '; lines ' + lines);

  /* Listening Room summaries and minute notes. Rumble can start at t= seconds. */
  begin('listen');
  const lhtml = fs.readFileSync('listening-room.html', 'utf8');
  const key = 'const DATA = ';
  const at = lhtml.indexOf(key);
  if (at < 0) throw new Error('listening-room.html has no DATA');
  const data = JSON.parse(lhtml.slice(at + key.length, lhtml.indexOf(';\n', at)));
  let volumes = 0;
  let notes = 0;
  for (const v of data.vols || []) {
    const base = '/listening-room.html#vol=' + v.id;
    const summary = [v.t, v.sum, v.note, v.post, (v.topics || []).join(' '), (v.people || []).join(' ')].filter(Boolean).join(' ');
    if (add('listen', v.t, base, summary)) volumes++;
    const mn = v.min;
    if (!mn) continue;
    if (mn.sum) add('listen', v.t + ' · summary', base, mn.sum);
    if (mn.closing) add('listen', v.t + ' · close', base, mn.closing);
    for (const top of mn.tops || []) {
      const stamp = v.src === 'rumble' && top.s != null ? base + '&t=' + (+top.s) : base;
      const label = v.t + (top.at ? ' · ' + top.at : '');
      if (add('listen', label, stamp, (top.t || '') + ' ' + (top.x || ''))) notes++;
    }
  }
  end();
  console.log('Recordings ' + volumes + '; minute notes ' + notes);

  /* Video titles and descriptions. No transcripts are in the repo. */
  begin('video');
  let videos = 0;
  const watchDirs = fs.readdirSync('watch').filter((name) => fs.existsSync(path.join('watch', name, 'index.html')));
  for (const id of watchDirs) {
    const html = fs.readFileSync(path.join('watch', id, 'index.html'), 'utf8');
    const h1 = html.match(/<h1>([\s\S]*?)<\/h1>/);
    const body = html.match(/<div class="text">([\s\S]*?)<\/div>/);
    const title = clean(stripTags(h1 ? h1[1] : id));
    const desc = clean(stripTags(body ? body[1] : ''));
    if (add('video', title, '/watch/' + id + '/', title + ' ' + desc)) videos++;
  }
  end();
  console.log('Videos ' + videos);
  flush();

  /* Inverted index, sharded by prefix. A shard over SHARD_MAX chars is split. */
  const shards = new Map();
  const roomIndexBytes = Object.create(null);
  for (const r of roomOrder) roomIndexBytes[r.id] = 0;
  const words = Object.keys(post);
  for (const w of words) {
    const ids = post[w];
    const enc = encodeIds(ids);
    const counts = Object.create(null);
    for (const id of ids) {
      const rm = idRoom[id];
      counts[rm] = (counts[rm] || 0) + 1;
    }
    const share = enc.length / ids.length;
    for (const rm in counts) roomIndexBytes[rm] += share * counts[rm];
    delete post[w];
    const k = pre(w, 2);
    if (!shards.has(k)) shards.set(k, new Map());
    shards.get(k).set(w, enc);
  }
  const split = new Set();
  for (let guard = 0; guard < 20; guard++) {
    const big = [];
    for (const [k, m] of shards) {
      if (k.length >= 5) continue;
      let n = 2;
      for (const [w, v] of m) n += w.length + v.length + 4;
      if (n > SHARD_MAX) big.push(k);
    }
    if (!big.length) break;
    for (const k of big) {
      const m = shards.get(k);
      shards.delete(k);
      split.add(k);
      for (const [w, v] of m) {
        const k2 = pre(w, k.length + 1);
        if (!shards.has(k2)) shards.set(k2, new Map());
        shards.get(k2).set(w, v);
      }
    }
  }
  const shardNames = [...shards.keys()].sort();
  for (const k of shardNames) {
    const obj = {};
    for (const [w, v] of shards.get(k)) obj[w] = v;
    fs.writeFileSync(path.join(out, 's', k + '.json'), JSON.stringify(obj));
  }

  const rooms = roomOrder.map((r) => ({
    id: r.id,
    label: LABELS[r.id],
    from: r.from,
    to: r.to,
    n: (stats[r.id] && stats[r.id].n) || 0,
    textBytes: (stats[r.id] && stats[r.id].text) || 0,
    indexBytes: Math.round(roomIndexBytes[r.id] || 0),
  }));
  const rev = Date.now().toString(36);
  const manifest = {
    v: 1,
    rev,
    built: new Date().toISOString().slice(0, 10),
    exclude: EXCLUDE_DOCS.slice(),
    excluded: skipped.map((id) => ({ id, pages: listed.has(id) ? listed.get(id)[3] : 0, indexed: false })),
    stop: STOP_WORDS,
    split: [...split].sort(),
    shards: shardNames,
    starts,
    rooms,
    records: nextId,
  };
  fs.writeFileSync(path.join(out, 'manifest.json'), JSON.stringify(manifest));

  const scanned = scanExcluded(out);
  const rec = dirBytes(path.join(out, 'r'));
  const sh = dirBytes(path.join(out, 's'));
  const manBytes = fs.statSync(path.join(out, 'manifest.json')).size;
  const total = rec.b + sh.b + manBytes;
  console.log('---');
  console.log('records written ' + scanned + '; words ' + words.length + '; shards ' + sh.n + '; record files ' + rec.n);
  console.log('total ' + (total / 1e6).toFixed(2) + ' MB  (passages ' + (rec.b / 1e6).toFixed(2) + ' MB, word index ' + (sh.b / 1e6).toFixed(2) + ' MB, manifest ' + (manBytes / 1024).toFixed(1) + ' KB)');
  for (const r of rooms) {
    console.log(
      r.id.padEnd(8) +
        String(r.n).padStart(7) +
        '  text ' + (r.textBytes / 1e6).toFixed(2).padStart(6) + ' MB' +
        '  index ' + (r.indexBytes / 1e6).toFixed(2).padStart(6) + ' MB'
    );
  }
  console.log('exclusion scan ok (' + EXCLUDE_DOCS.join(',') + ' absent)');
  console.log('index: ' + path.relative(ROOT, out));
}

main().catch((e) => {
  console.error(e && e.stack ? e.stack : e);
  process.exit(1);
});
