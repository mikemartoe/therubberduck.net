// Read-only R2 streamer for Video Room reels (bucket trd-memes, keys under video-room/).
// Why: R2 public/custom-domain access answers Range requests on objects > ~512 MB with a full 200,
// which iOS Safari refuses to play. This Worker reads R2 through the binding and always honours Range (206).
const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
  'Access-Control-Allow-Headers': 'Range, If-None-Match, If-Modified-Since',
  'Access-Control-Expose-Headers': 'Content-Length, Content-Range, Accept-Ranges, ETag',
};
function typeFor(key, o) {
  const ct = o.httpMetadata && o.httpMetadata.contentType;
  if (ct && ct !== 'application/octet-stream') return ct;
  if (key.endsWith('.mp4')) return 'video/mp4';
  if (key.endsWith('.jpg')) return 'image/jpeg';
  return 'application/octet-stream';
}
function parseRange(h, size) {
  const m = /^bytes=(\d*)-(\d*)$/.exec((h || '').trim());
  if (!m || (m[1] === '' && m[2] === '')) return null;
  let start, end;
  if (m[1] === '') { const n = Math.min(parseInt(m[2], 10), size); start = size - n; end = size - 1; }
  else { start = parseInt(m[1], 10); end = m[2] === '' ? size - 1 : Math.min(parseInt(m[2], 10), size - 1); }
  if (start >= size || start > end) return 'bad';
  return {start, end};
}
export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (req.method === 'OPTIONS') return new Response(null, {status: 204, headers: CORS});
    if (req.method !== 'GET' && req.method !== 'HEAD') return new Response('Method not allowed', {status: 405, headers: CORS});
    if (url.pathname === '/') return new Response('trd-video-stream ok', {headers: CORS});
    const key = decodeURIComponent(url.pathname.slice(1));
    if (!key.startsWith('video-room/') || key.includes('..')) return new Response('Not found', {status: 404, headers: CORS});
    const head = await env.MEMES.head(key);
    if (!head) return new Response('Not found', {status: 404, headers: CORS});
    const size = head.size, etag = head.httpEtag;
    const base = {
      ...CORS,
      'Content-Type': typeFor(key, head),
      'Accept-Ranges': 'bytes',
      'ETag': etag,
      'Last-Modified': head.uploaded.toUTCString(),
      'Cache-Control': (head.httpMetadata && head.httpMetadata.cacheControl) || 'public, max-age=31536000, immutable',
    };
    const inm = req.headers.get('If-None-Match');
    if (inm && (inm === etag || inm === '*')) return new Response(null, {status: 304, headers: base});
    const rh = req.headers.get('Range');
    const ifr = req.headers.get('If-Range');
    const r = rh && (!ifr || ifr === etag) ? parseRange(rh, size) : null;
    if (r === 'bad') return new Response(null, {status: 416, headers: {...base, 'Content-Range': 'bytes */' + size}});
    if (r) {
      const len = r.end - r.start + 1;
      const h = {...base, 'Content-Range': `bytes ${r.start}-${r.end}/${size}`, 'Content-Length': String(len)};
      if (req.method === 'HEAD') return new Response(null, {status: 206, headers: h});
      const o = await env.MEMES.get(key, {range: {offset: r.start, length: len}});
      return new Response(o.body, {status: 206, headers: h});
    }
    const h = {...base, 'Content-Length': String(size)};
    if (req.method === 'HEAD') return new Response(null, {status: 200, headers: h});
    const o = await env.MEMES.get(key);
    return new Response(o.body, {status: 200, headers: h});
  },
};
