// R2 upload helper for the Video Room archive (bucket trd-memes, keys under video-room/).
// Auth: Authorization: Bearer <UPLOAD_SECRET>. Supports single PUT (<95 MB) and multipart for big files.
const CORS = {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'PUT, POST, HEAD, GET, OPTIONS', 'Access-Control-Allow-Headers': 'Authorization, Content-Type'};
const J = (o, s = 200) => new Response(JSON.stringify(o), {status: s, headers: {'Content-Type': 'application/json', ...CORS}});
export default {
  async fetch(req, env) {
    const url = new URL(req.url), p = url.pathname, q = url.searchParams;
    if (req.method === 'OPTIONS') return new Response(null, {headers: CORS});
    if (p === '/' && req.method === 'GET') return new Response('trd-videos-upload ok');
    if ((req.headers.get('Authorization') || '') !== 'Bearer ' + env.UPLOAD_SECRET) return new Response('Unauthorized', {status: 401});
    const key = q.get('key') || '';
    if (!key.startsWith('video-room/') || key.includes('..')) return J({error: 'bad key'}, 400);
    const meta = {httpMetadata: {contentType: q.get('ct') || 'video/mp4', cacheControl: q.get('cc') || 'public, max-age=31536000, immutable'}};
    if (p === '/head') { const o = await env.MEMES.head(key); return J(o ? {size: o.size, etag: o.etag, ct: o.httpMetadata && o.httpMetadata.contentType} : {missing: true}); }
    if (p === '/put' && req.method === 'PUT') { const o = await env.MEMES.put(key, req.body, meta); return J({ok: true, key, size: o.size}); }
    if (p === '/mpu/create' && req.method === 'POST') { const m = await env.MEMES.createMultipartUpload(key, meta); return J({uploadId: m.uploadId}); }
    if (p === '/mpu/part' && req.method === 'PUT') {
      const m = env.MEMES.resumeMultipartUpload(key, q.get('uploadId'));
      const part = await m.uploadPart(parseInt(q.get('part'), 10), req.body); return J(part);
    }
    if (p === '/mpu/complete' && req.method === 'POST') {
      const m = env.MEMES.resumeMultipartUpload(key, q.get('uploadId'));
      const o = await m.complete((await req.json()).parts); return J({ok: true, key, size: o.size});
    }
    if (p === '/mpu/abort' && req.method === 'POST') { await env.MEMES.resumeMultipartUpload(key, q.get('uploadId')).abort(); return J({ok: true}); }
    return J({error: 'not found'}, 404);
  },
};
