/* Cold-query cost of the unified index. Reads search/unified the way the
   browser does: manifest, one shard per word, then the passage files for the
   hits shown in the header (one per room, chosen from three candidates).
   A second query reuses files already touched. Nothing is uploaded. */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { tokenize, decodeIds, shardName } from './tokens.mjs';
import { excludedUrl } from './exclude.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const dir = path.join(root, 'search/unified');
const man = JSON.parse(fs.readFileSync(path.join(dir, 'manifest.json'), 'utf8'));
const split = new Set(man.split);
const shardSet = new Set(man.shards);
const fileCache = new Map();

function load(rel, bucket) {
  const p = path.join(dir, rel);
  const bytes = fs.statSync(p).size;
  bucket.push({ rel, bytes });
  if (fileCache.has(rel)) return fileCache.get(rel);
  const json = JSON.parse(fs.readFileSync(p, 'utf8'));
  fileCache.set(rel, json);
  return json;
}
function roomOf(id) {
  const rs = man.rooms;
  let lo = 0, hi = rs.length - 1;
  while (lo < hi) {
    const mid = (lo + hi + 1) >> 1;
    if (rs[mid].from <= id) lo = mid;
    else hi = mid - 1;
  }
  const r = rs[lo];
  return id >= r.from && id < r.to ? r : null;
}
function fileOf(id) {
  const s = man.starts;
  let lo = 0, hi = s.length - 1;
  while (lo < hi) {
    const mid = (lo + hi + 1) >> 1;
    if (s[mid] <= id) lo = mid;
    else hi = mid - 1;
  }
  return lo;
}
function intersect(a, b) {
  const out = [];
  let i = 0, j = 0;
  while (i < a.length && j < b.length) {
    if (a[i] < b[j]) i++;
    else if (a[i] > b[j]) j++;
    else { out.push(a[i]); i++; j++; }
  }
  return Int32Array.from(out);
}
function search(q, sample, seen) {
  const touched = [];
  const manifestRel = 'manifest.json';
  if (!seen.has(manifestRel)) {
    touched.push({ rel: manifestRel, bytes: fs.statSync(path.join(dir, manifestRel)).size });
    seen.add(manifestRel);
  }
  const terms = tokenize(q);
  const lists = terms.map((word) => {
    const name = shardName(word, split);
    if (!shardSet.has(name)) return new Int32Array(0);
    const rel = 's/' + name + '.json';
    if (!seen.has(rel)) {
      const sh = load(rel, touched);
      seen.add(rel);
      return decodeIds(sh[word]);
    }
    return decodeIds(fileCache.get(rel)[word]);
  });
  lists.sort((a, b) => a.length - b.length);
  let ids = lists[0] || new Int32Array(0);
  for (let i = 1; i < lists.length && ids.length; i++) ids = intersect(ids, lists[i]);
  const buckets = new Map();
  const counts = new Map();
  for (const id of ids) {
    const room = roomOf(id);
    if (!room) continue;
    counts.set(room.id, (counts.get(room.id) || 0) + 1);
    if (!buckets.has(room.id)) buckets.set(room.id, []);
    const b = buckets.get(room.id);
    if (b.length < sample) b.push(id);
  }
  const hits = [];
  for (const room of man.rooms) {
    const idsIn = buckets.get(room.id) || [];
    let best = null;
    for (const id of idsIn) {
      const f = fileOf(id);
      const rel = 'r/' + f + '.json';
      let rows;
      if (!seen.has(rel)) {
        rows = load(rel, touched);
        seen.add(rel);
      } else rows = fileCache.get(rel);
      const rec = rows[id - man.starts[f]];
      if (!rec) continue;
      if (excludedUrl(rec[1])) throw new Error('excluded hit ' + rec[1]);
      best = { room: room.label, title: rec[0], url: rec[1] };
      break;
    }
    if (best) hits.push(Object.assign({ n: counts.get(room.id) || 0 }, best));
  }
  const bytes = touched.reduce((a, x) => a + x.bytes, 0);
  return { q, terms, total: ids.length, hits, fetches: touched.length, bytes, files: touched.map((t) => t.rel) };
}

const queries = process.argv.slice(2);
const list = queries.length ? queries : [
  'military intelligence',
  'muslim brotherhood',
  'extradition already',
  'state secrets',
  'mockingbird',
  'wwg1wga',
];
let seen = new Set();
for (const q of list) {
  const cold = new Set();
  const r = search(q, 3, cold);
  console.log('\nQUERY ' + JSON.stringify(q));
  console.log('cold fetches ' + r.fetches + '  ' + (r.bytes / 1024).toFixed(1) + ' KB  passages ' + r.total);
  for (const h of r.hits) console.log('  ' + h.room.padEnd(12) + String(h.n).padStart(6) + '  ' + h.title.slice(0, 70) + '  ' + h.url.slice(0, 90));
  const warm = search(q, 3, cold);
  console.log('same query again, new fetches ' + warm.fetches + '  ' + (warm.bytes / 1024).toFixed(1) + ' KB');
  seen = cold;
}
console.log('\nindexed records', man.records, 'excluded', JSON.stringify(man.excluded));
