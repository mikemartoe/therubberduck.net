/* Cloudflare Worker: trd-mobile-fix
   Serves homepage HTML + critical TRD assets from GitHub raw while Pages
   builds are unhealthy. Do NOT re-add header dock/watermark experiments
   unless Mike explicitly asks. Known-good mobile: logo duck beside title,
   suggestion box + support duck bottom-right beside cassette. */
const RAW = 'https://raw.githubusercontent.com/mikemartoe/therubberduck.net/main';
const PROXY = new Set([
  '/assets/trd/suggest.css',
  '/assets/trd/suggest.js',
  '/assets/trd/bookbanner.css',
  '/assets/trd/bookbanner.js',
]);
function isProxied(path) {
  if (PROXY.has(path)) return true;
  if (path.startsWith('/assets/trd/img/')) return true;
  if (path.startsWith('/images/brand/')) return true;
  return false;
}
function typeFor(path) {
  if (path.endsWith('.css')) return 'text/css; charset=utf-8';
  if (path.endsWith('.js')) return 'application/javascript; charset=utf-8';
  if (path.endsWith('.png')) return 'image/png';
  if (path.endsWith('.webp')) return 'image/webp';
  if (path.endsWith('.jpg') || path.endsWith('.jpeg')) return 'image/jpeg';
  if (path.endsWith('.gif')) return 'image/gif';
  if (path.endsWith('.svg')) return 'image/svg+xml';
  return 'application/octet-stream';
}
export default {
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname;
    if (isProxied(path)) {
      const upstream = await fetch(RAW + path + '?v=' + Date.now(), { cf: { cacheTtl: 0, cacheEverything: false } });
      if (!upstream.ok) return fetch(request);
      const body = await upstream.arrayBuffer();
      return new Response(body, { status: 200, headers: { 'content-type': typeFor(path), 'cache-control': 'public, max-age=3600' } });
    }
    let html;
    let status = 200;
    if (path === '/' || path === '/index.html') {
      const rawHtml = await fetch(RAW + '/index.html?v=' + Date.now(), { cf: { cacheTtl: 0, cacheEverything: false } });
      if (rawHtml.ok) { html = await rawHtml.text(); }
      else { const resp = await fetch(request); html = await resp.text(); status = resp.status; }
    } else {
      const resp = await fetch(request);
      const ct = resp.headers.get('content-type') || '';
      if (!ct.includes('text/html')) return resp;
      html = await resp.text(); status = resp.status;
    }
    html = html.replace(new RegExp('<style id="trd-mobile-fix">[\\s\\S]*?<\\/style>', 'g'), '');
    html = html.replace(new RegExp('<script id="trd-mobile-dock">[\\s\\S]*?<\\/script>', 'g'), '');
    return new Response(html, { status, headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' } });
  }
};
