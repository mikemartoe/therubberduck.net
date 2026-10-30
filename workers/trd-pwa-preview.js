/* Cloudflare Worker: trd-pwa-preview (PREVIEW ONLY, workers.dev, never on therubberduck.net routes)
   Serves the pwa-preview-20261030 branch of mikemartoe/therubberduck.net from GitHub raw so Mike can
   try the web app, install banner and alerts on a phone before anything goes live. noindex everywhere. */
const BRANCH = 'pwa-preview-20261030';
const RAW = 'https://raw.githubusercontent.com/mikemartoe/therubberduck.net/' + BRANCH;
const TYPES = { html: 'text/html; charset=utf-8', css: 'text/css; charset=utf-8', js: 'application/javascript; charset=utf-8', mjs: 'application/javascript; charset=utf-8', json: 'application/json; charset=utf-8', webmanifest: 'application/manifest+json', svg: 'image/svg+xml', png: 'image/png', jpg: 'image/jpeg', jpeg: 'image/jpeg', webp: 'image/webp', gif: 'image/gif', ico: 'image/x-icon', woff2: 'font/woff2', woff: 'font/woff', ttf: 'font/ttf', txt: 'text/plain; charset=utf-8', xml: 'application/xml', pdf: 'application/pdf', mp3: 'audio/mpeg', m4a: 'audio/mp4', mp4: 'video/mp4' };
function ext(p) { const m = p.match(/\.([a-z0-9]+)$/i); return m ? m[1].toLowerCase() : ''; }
async function get(p) { return fetch(RAW + encodeURI(decodeURI(p)), { cf: { cacheTtl: 60, cacheEverything: true } }); }
export default {
  async fetch(req) {
    const url = new URL(req.url);
    if (req.method !== 'GET' && req.method !== 'HEAD') return new Response('Method not allowed', { status: 405 });
    let p = url.pathname;
    if (p.endsWith('/')) p += 'index.html';
    let r = await get(p), e = ext(p);
    if (r.status === 404 && !e) {
      r = await get(p + '.html'); e = 'html';
      if (r.status === 404) { const d = await get(p + '/index.html'); if (d.ok) return Response.redirect(url.origin + url.pathname + '/' + url.search, 301); }
    }
    if (r.status === 404) { const nf = await get('/404.html'); return new Response(nf.ok ? nf.body : 'Not found', { status: 404, headers: { 'content-type': TYPES.html, 'x-robots-tag': 'noindex' } }); }
    const h = new Headers({ 'content-type': TYPES[e] || 'application/octet-stream', 'x-robots-tag': 'noindex, nofollow', 'cache-control': e === 'html' || p === '/sw.js' ? 'no-cache' : 'public, max-age=300' });
    if (p === '/sw.js') h.set('service-worker-allowed', '/');
    return new Response(r.body, { status: r.status, headers: h });
  },
};
