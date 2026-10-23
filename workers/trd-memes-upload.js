// R2 upload helper for trd-memes. PUT /<key> with Authorization: Bearer <UPLOAD_SECRET>
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'PUT, HEAD, GET, OPTIONS',
          'Access-Control-Allow-Headers': 'Authorization, Content-Type',
        },
      });
    }
    if (request.method === 'PUT') {
      const auth = request.headers.get('Authorization') || '';
      if (auth !== 'Bearer ' + env.UPLOAD_SECRET) {
        return new Response('Unauthorized', { status: 401 });
      }
      const key = decodeURIComponent(url.pathname.replace(/^\/+/, ''));
      if (!key || key.includes('..')) {
        return new Response('Bad key', { status: 400 });
      }
      const ct = request.headers.get('Content-Type') || 'application/octet-stream';
      await env.MEMES.put(key, request.body, {
        httpMetadata: { contentType: ct },
      });
      return new Response(JSON.stringify({ ok: true, key }), {
        headers: { 'Content-Type': 'application/json' },
      });
    }
    if (request.method === 'HEAD' || request.method === 'GET') {
      // health only at /
      if (url.pathname === '/' || url.pathname === '') {
        return new Response('trd-memes-upload ok', { status: 200 });
      }
      return new Response('Not found', { status: 404 });
    }
    return new Response('Method not allowed', { status: 405 });
  },
};
