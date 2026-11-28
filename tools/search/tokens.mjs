/* Token rules for the unified index. The browser copy lives in
   assets/trd/fulltext-search.js (rawTokens + the manifest stop list).
   Keep the fold and the regex in step with that file. */

export const STOP_WORDS = (
  'the and for that with this from are was were been have has had not but you your they their them ' +
  'what when where who how why all any can will just about into over than then its his her she him ' +
  'our out also more some such only other which would could should there here because while after ' +
  'before under between through during without within these those does did each both most many much ' +
  'very onto off via inc'
).split(/\s+/).filter(Boolean);

const STOP = new Set(STOP_WORDS);
const TOKEN = /[a-z0-9]{2,30}/g;

export function fold(s) {
  return String(s || '')
    .toLowerCase()
    .normalize('NFKD')
    .replace(/\p{M}/gu, '')
    .replace(/[\u2018\u2019\u201c\u201d']/g, '');
}

/* Unique tokens, stop words removed, in first-seen order. */
export function tokenize(s) {
  const m = fold(s).match(TOKEN);
  if (!m) return [];
  const seen = new Set();
  const out = [];
  for (const t of m) {
    if (t.length < 3 && !/^[0-9]{2}$/.test(t)) continue;
    if (STOP.has(t) || seen.has(t)) continue;
    seen.add(t);
    out.push(t);
  }
  return out;
}

export function encodeIds(ids) {
  let prev = -1;
  const parts = new Array(ids.length);
  for (let i = 0; i < ids.length; i++) {
    parts[i] = (ids[i] - prev - 1).toString(36);
    prev = ids[i];
  }
  return parts.join('.');
}

export function decodeIds(s) {
  if (!s) return new Int32Array(0);
  const p = s.split('.');
  const out = new Int32Array(p.length);
  let prev = -1;
  for (let i = 0; i < p.length; i++) {
    prev += parseInt(p[i], 36) + 1;
    out[i] = prev;
  }
  return out;
}

export function shardName(word, split) {
  const set = split instanceof Set ? split : new Set(split || []);
  let p = (word + '_____').slice(0, 2);
  while (set.has(p) && p.length < 5) p = (word + '_____').slice(0, p.length + 1);
  return p;
}
