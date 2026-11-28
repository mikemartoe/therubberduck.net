#!/usr/bin/env node
/* Add SCI[F] documents to an existing unified full-text index without the
   sources of the other rooms. The result is the same index a full
   build-unified.mjs run gives for the same records: SCI[F] pages stay first in
   id order, new documents go at the end of the SCI[F] room, every later room
   shifts by the number of new passages, and the word shards and record files
   are rewritten. Run it after tools/scif-fulltext-build.py has written the new
   SCI[F] data. Excluded ids (exclude.mjs) are refused.

     node tools/search/add-scif-docs.mjs --base DIR --scif DIR --add TRD-0246[,TRD-0247] --out DIR

   --base  an extracted existing index (manifest.json, s/, r/)
   --scif  the new SCI[F] data (search/manifest.json, text/)
   --out   empty output dir, becomes the new fulltext/<hash>/ folder content */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { EXCLUDE_DOCS, excludedDoc } from './exclude.mjs';
import { tokenize, encodeIds, decodeIds } from './tokens.mjs';

const CHUNK_CHARS = 32000, STORE_CAP = 15000, SHARD_MAX = 140000;
const arg = (n) => { const i = process.argv.indexOf(n); if (i < 0) throw new Error('missing ' + n); return process.argv[i + 1]; };
const rj = (...p) => JSON.parse(fs.readFileSync(path.join(...p), 'utf8'));
const clean = (s) => String(s || '')
  .replace(/https?:\/\/\S*wikipedia\.org\S*/gi, ' ').replace(/wikipedia(?:,? the free encyclopedia)?/gi, '')
  .replace(/https?:\/\/\S+/gi, ' ').replace(/[\u0000-\u0008\u000b-\u001f\u007f]/g, ' ').replace(/\s+/g, ' ').trim();
const pre = (w, n) => (w + '_____').slice(0, n);

const base = path.resolve(arg('--base')), scif = path.resolve(arg('--scif')), out = path.resolve(arg('--out'));
const add = arg('--add').split(',').map((s) => s.trim()).filter(Boolean);
for (const id of add) if (excludedDoc(id)) throw new Error('Refusing excluded document ' + id);

const man = rj(base, 'manifest.json');
const scifRoom = man.rooms.find((r) => r.id === 'scif');
if (!scifRoom || man.rooms[0] !== scifRoom) throw new Error('SCI[F] must be the first room');

/* 1. every existing record, in id order */
const recs = [];
for (let f = 0; f < man.starts.length; f++) {
  const arr = rj(base, 'r', f + '.json');
  if (recs.length !== man.starts[f]) throw new Error('record file ' + f + ' does not start at ' + recs.length);
  for (const r of arr) recs.push(r);
}
if (recs.length !== man.records) throw new Error('record count mismatch');
for (const id of add) {
  if (recs.some((r) => r[1].startsWith('/pdfs.html?open=' + id + '&'))) throw new Error(id + ' is already in the index');
}

/* 2. new SCI[F] passages, built exactly as build-unified.mjs does */
const newRecs = [], newToks = [];
const scifMan = rj(scif, 'search/manifest.json');
const listed = new Map(scifMan.docs.map((d) => [d[0], d]));
for (const id of add) {
  if (!listed.has(id)) throw new Error(id + ' is not in the SCI[F] manifest');
  const meta = rj(scif, 'text', id + '.json');
  const title = meta.title || listed.get(id)[1];
  const pages = [];
  if (Array.isArray(meta.text)) meta.text.forEach((t, n) => pages.push([n + 1, t]));
  else for (let k = 0; k < meta.parts; k++) { const part = rj(scif, 'text', id + '.' + k + '.json'); (part.text || []).forEach((t, n) => pages.push([(part.from || k * meta.per + 1) + n, t])); }
  for (const [p, t] of pages) {
    const full = clean(t), label = clean(title + ' \u00b7 p. ' + p).slice(0, 180);
    const url = '/pdfs.html?open=' + encodeURIComponent(id) + '&p=' + p;
    if (!full) continue;
    const toks = tokenize(label + ' ' + full);
    if (!toks.length) continue;
    newRecs.push([label, url, full.length > STORE_CAP ? full.slice(0, STORE_CAP) : full]);
    newToks.push(toks);
  }
}
const N = newRecs.length, at = scifRoom.to;
console.log('new passages ' + N + ' inserted at id ' + at);

/* 3. postings: decode, shift ids at or after the SCI[F] end, add the new ones */
const post = new Map();
for (const f of fs.readdirSync(path.join(base, 's'))) {
  const sh = rj(base, 's', f);
  for (const w in sh) {
    const ids = decodeIds(sh[w]);
    const a = new Array(ids.length);
    for (let i = 0; i < ids.length; i++) a[i] = ids[i] >= at ? ids[i] + N : ids[i];
    post.set(w, a);
  }
}
newToks.forEach((toks, k) => { for (const w of toks) { const a = post.get(w); if (a) a.push(at + k); else post.set(w, [at + k]); } });
/* new ids are larger than every old SCI[F] id and smaller than every shifted id: re-sort to keep the order */
for (const a of post.values()) a.sort((x, y) => x - y);

/* 4. rooms */
const rooms = man.rooms.map((r, i) => i === 0
  ? { ...r, to: r.to + N, n: r.n + N, textBytes: r.textBytes + newRecs.reduce((s, x) => s + x[2].length, 0) }
  : { ...r, from: r.from + N, to: r.to + N });
const idRoomOf = (id) => { for (const r of rooms) if (id >= r.from && id < r.to) return r.id; return null; };

/* 5. records into chunk files (same flush rule as the full build) */
fs.rmSync(out, { recursive: true, force: true });
fs.mkdirSync(path.join(out, 'r'), { recursive: true }); fs.mkdirSync(path.join(out, 's'), { recursive: true });
const all = recs.slice(0, at).concat(newRecs, recs.slice(at));
const starts = []; let buf = [], bufStart = 0, bufBytes = 0;
const flush = () => { if (!buf.length) return; starts.push(bufStart); fs.writeFileSync(path.join(out, 'r', (starts.length - 1) + '.json'), JSON.stringify(buf)); buf = []; bufBytes = 0; };
all.forEach((r, id) => { if (!buf.length) bufStart = id; buf.push(r); bufBytes += r[0].length + r[1].length + r[2].length; if (bufBytes >= CHUNK_CHARS) flush(); });
flush();

/* 6. shards */
const shards = new Map(), roomIndexBytes = Object.create(null);
for (const r of rooms) roomIndexBytes[r.id] = 0;
for (const [w, ids] of post) {
  const enc = encodeIds(ids), counts = Object.create(null);
  for (const id of ids) { const rm = idRoomOf(id); counts[rm] = (counts[rm] || 0) + 1; }
  const share = enc.length / ids.length;
  for (const rm in counts) roomIndexBytes[rm] += share * counts[rm];
  const k = pre(w, 2); if (!shards.has(k)) shards.set(k, new Map()); shards.get(k).set(w, enc);
}
const split = new Set();
for (let guard = 0; guard < 20; guard++) {
  const big = [];
  for (const [k, m] of shards) { if (k.length >= 5) continue; let n = 2; for (const [w, v] of m) n += w.length + v.length + 4; if (n > SHARD_MAX) big.push(k); }
  if (!big.length) break;
  for (const k of big) { const m = shards.get(k); shards.delete(k); split.add(k); for (const [w, v] of m) { const k2 = pre(w, k.length + 1); if (!shards.has(k2)) shards.set(k2, new Map()); shards.get(k2).set(w, v); } }
}
const shardNames = [...shards.keys()].sort();
for (const k of shardNames) { const o = {}; for (const [w, v] of shards.get(k)) o[w] = v; fs.writeFileSync(path.join(out, 's', k + '.json'), JSON.stringify(o)); }
for (const r of rooms) r.indexBytes = Math.round(roomIndexBytes[r.id] || 0);

const manifest = { ...man, rev: Date.now().toString(36), built: new Date().toISOString().slice(0, 10), split: [...split].sort(), shards: shardNames, starts, rooms, records: all.length };
fs.writeFileSync(path.join(out, 'manifest.json'), JSON.stringify(manifest));

/* 7. exclusion scan: no excluded id or URL anywhere in the passages */
let seen = 0;
for (const f of fs.readdirSync(path.join(out, 'r'))) for (const rec of rj(out, 'r', f)) {
  seen++;
  for (const id of EXCLUDE_DOCS) if (rec[1].includes(id)) throw new Error('Excluded id in a result URL: ' + rec[1]);
  if (rec[1].startsWith('/library/epstein-black-book/')) throw new Error('Excluded library URL in the index');
}
const hash = crypto.createHash('sha256').update(fs.readFileSync(path.join(out, 'manifest.json'))).digest('hex').slice(0, 10);
console.log('records ' + seen + ' (was ' + man.records + '); words ' + post.size + '; shards ' + shardNames.length + '; record files ' + starts.length);
console.log('exclusion scan ok (' + EXCLUDE_DOCS.join(',') + ' absent)');
console.log('R2 prefix: fulltext/' + hash + '/');
