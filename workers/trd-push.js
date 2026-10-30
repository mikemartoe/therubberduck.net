/* Cloudflare Worker: trd-push (preview name: trd-push-preview)
   Web Push (VAPID, RFC 8291 aes128gcm) for The Rubber Duck web app.
   Routes (all under /api/push):
     GET  /api/push/health            status, counts
     GET  /api/push/vapid             VAPID public key
     POST /api/push/subscribe         {subscription:{endpoint,keys:{p256dh,auth}}, topics:["drops","deltas"], tz}
     POST /api/push/unsubscribe       {endpoint}
     GET  /api/push/admin/preview     (Bearer ADMIN_TOKEN) what the next digest / drop alert would say; sends nothing
     POST /api/push/admin/test        (Bearer ADMIN_TOKEN) {endpoint} send one test alert to ONE stored subscription
   Cron (scheduled):
     "0 13 * * *"    daily Deltas digest (9 AM New York in summer, 8 AM in winter)
     "every 30 minutes" (cron 0,30 * * * *)  new-drop check against SITE/data/drops-latest.json
   Bindings: KV SUBS; secrets VAPID_PRIVATE_JWK (JSON), ADMIN_TOKEN; vars VAPID_PUBLIC_KEY, VAPID_SUBJECT, SITE,
             ALLOWED_ORIGINS (comma list), SEND_ENABLED ("true" to send from cron; anything else = dry run, logged to KV). */
const TOPICS = ['drops', 'deltas'];
const PUSH_HOSTS = /(^|\.)(fcm\.googleapis\.com|push\.services\.mozilla\.com|push\.apple\.com|notify\.windows\.com|android\.googleapis\.com)$/;
const te = new TextEncoder();
const b64u = {
  enc(buf) { let s = ''; const a = new Uint8Array(buf); for (let i = 0; i < a.length; i++) s += String.fromCharCode(a[i]); return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); },
  dec(str) { str = str.replace(/-/g, '+').replace(/_/g, '/'); while (str.length % 4) str += '='; const r = atob(str); const a = new Uint8Array(r.length); for (let i = 0; i < r.length; i++) a[i] = r.charCodeAt(i); return a; },
};
function concat(...parts) { const n = parts.reduce((s, p) => s + p.length, 0); const o = new Uint8Array(n); let off = 0; for (const p of parts) { o.set(p, off); off += p.length; } return o; }
async function hkdf(salt, ikm, info, bits) {
  const k = await crypto.subtle.importKey('raw', ikm, 'HKDF', false, ['deriveBits']);
  return new Uint8Array(await crypto.subtle.deriveBits({ name: 'HKDF', hash: 'SHA-256', salt, info }, k, bits));
}
/* RFC 8291 payload encryption, single record, aes128gcm */
export async function encryptPayload(payload, p256dhB64, authB64) {
  const uaPublic = b64u.dec(p256dhB64), authSecret = b64u.dec(authB64);
  const asKeys = await crypto.subtle.generateKey({ name: 'ECDH', namedCurve: 'P-256' }, true, ['deriveBits']);
  const asPublic = new Uint8Array(await crypto.subtle.exportKey('raw', asKeys.publicKey));
  const uaKey = await crypto.subtle.importKey('raw', uaPublic, { name: 'ECDH', namedCurve: 'P-256' }, false, []);
  const shared = new Uint8Array(await crypto.subtle.deriveBits({ name: 'ECDH', public: uaKey }, asKeys.privateKey, 256));
  const ikm = await hkdf(authSecret, shared, concat(te.encode('WebPush: info\0'), uaPublic, asPublic), 256);
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const cek = await hkdf(salt, ikm, te.encode('Content-Encoding: aes128gcm\0'), 128);
  const nonce = await hkdf(salt, ikm, te.encode('Content-Encoding: nonce\0'), 96);
  const key = await crypto.subtle.importKey('raw', cek, 'AES-GCM', false, ['encrypt']);
  const plain = concat(typeof payload === 'string' ? te.encode(payload) : payload, new Uint8Array([2]));
  const ct = new Uint8Array(await crypto.subtle.encrypt({ name: 'AES-GCM', iv: nonce }, key, plain));
  const rs = new Uint8Array([0, 0, 16, 0]); /* 4096 */
  return concat(salt, rs, new Uint8Array([asPublic.length]), asPublic, ct);
}
export async function vapidAuth(endpoint, env) {
  const aud = new URL(endpoint).origin;
  const header = b64u.enc(te.encode(JSON.stringify({ typ: 'JWT', alg: 'ES256' })));
  const claims = b64u.enc(te.encode(JSON.stringify({ aud, exp: Math.floor(Date.now() / 1000) + 12 * 3600, sub: env.VAPID_SUBJECT || 'https://therubberduck.net/' })));
  const jwk = typeof env.VAPID_PRIVATE_JWK === 'string' ? JSON.parse(env.VAPID_PRIVATE_JWK) : env.VAPID_PRIVATE_JWK;
  const key = await crypto.subtle.importKey('jwk', { kty: 'EC', crv: 'P-256', x: jwk.x, y: jwk.y, d: jwk.d, ext: true }, { name: 'ECDSA', namedCurve: 'P-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign({ name: 'ECDSA', hash: 'SHA-256' }, key, te.encode(header + '.' + claims));
  return 'vapid t=' + header + '.' + claims + '.' + b64u.enc(sig) + ', k=' + env.VAPID_PUBLIC_KEY;
}
export async function sendPush(sub, message, env, ttl = 86400) {
  const body = await encryptPayload(JSON.stringify(message), sub.keys.p256dh, sub.keys.auth);
  const r = await fetch(sub.endpoint, { method: 'POST', body, headers: {
    Authorization: await vapidAuth(sub.endpoint, env), TTL: String(ttl), Urgency: 'normal',
    'Content-Encoding': 'aes128gcm', 'Content-Type': 'application/octet-stream', Topic: (message.tag || 'trd').slice(0, 32) } });
  return r.status;
}
async function idFor(endpoint) { return b64u.enc(await crypto.subtle.digest('SHA-256', te.encode(endpoint))).slice(0, 32); }
function cors(req, env) {
  const o = req.headers.get('origin') || '';
  const allow = (env.ALLOWED_ORIGINS || 'https://therubberduck.net,https://www.therubberduck.net').split(',').map(s => s.trim());
  return allow.includes(o) ? { 'Access-Control-Allow-Origin': o, 'Access-Control-Allow-Methods': 'GET,POST,OPTIONS', 'Access-Control-Allow-Headers': 'content-type', 'Access-Control-Max-Age': '86400', Vary: 'Origin' } : { Vary: 'Origin' };
}
function json(obj, status, extra) { return new Response(JSON.stringify(obj), { status: status || 200, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', ...(extra || {}) } }); }
function isAdmin(req, env) { const a = req.headers.get('authorization') || ''; return !!env.ADMIN_TOKEN && a === 'Bearer ' + env.ADMIN_TOKEN; }
function nyDate(d = new Date()) {
  const p = Object.fromEntries(new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(d).map(x => [x.type, x.value]));
  const label = new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', month: 'long', day: 'numeric' }).format(d);
  return { key: p.month + '-' + p.day, label };
}
async function deltasMessage(env) {
  const site = env.SITE || 'https://therubberduck.net';
  const { key, label } = nyDate();
  let idx = {};
  try { idx = await (await fetch(site + '/data/deltas-index.json', { cf: { cacheTtl: 3600 } })).json(); } catch (e) {}
  const e = idx[key];
  if (!e) return { title: "Today's Deltas: " + label, body: 'No drops on this date. Browse every date with drops.', url: '/deltas/', tag: 'deltas' };
  const yrs = e.years.length > 1 ? e.years.slice(0, -1).join(', ') + ' and ' + e.years[e.years.length - 1] : String(e.years[0]);
  return { title: "Today's Deltas: " + label, body: e.n + (e.n === 1 ? ' drop' : ' drops') + ' posted on this date in ' + yrs + '. Read them today.', url: '/deltas/' + key + '/', tag: 'deltas' };
}
async function newDropMessage(env, commit) {
  const site = env.SITE || 'https://therubberduck.net';
  let latest;
  try { latest = await (await fetch(site + '/data/drops-latest.json', { cf: { cacheTtl: 300 } })).json(); } catch (e) { return null; }
  if (!latest || !latest.n) return null;
  const seen = +(await env.SUBS.get('state:last-drop')) || 0;
  if (!seen) { if (commit) await env.SUBS.put('state:last-drop', String(latest.n)); return null; } /* first run: baseline only */
  if (latest.n <= seen) return null;
  if (commit) await env.SUBS.put('state:last-drop', String(latest.n));
  const count = latest.n - seen;
  return { title: count === 1 ? 'New drop: #' + latest.n : count + ' new drops', body: count === 1 ? 'A new drop is in the archive. Read it now.' : 'Drops #' + (seen + 1) + ' to #' + latest.n + ' are in the archive.', url: latest.url || '/ledger.html', tag: 'drops' };
}
async function fanOut(topic, message, env) {
  const live = env.SEND_ENABLED === 'true';
  let cursor, sent = 0, gone = 0, failed = 0, matched = 0;
  do {
    const page = await env.SUBS.list({ prefix: 'sub:', cursor, limit: 1000 });
    const subs = [];
    for (const k of page.keys) { if (k.metadata && Array.isArray(k.metadata.t) && !k.metadata.t.includes(topic)) continue; const v = await env.SUBS.get(k.name, 'json'); if (v && v.topics.includes(topic)) subs.push([k.name, v]); }
    matched += subs.length;
    if (live) {
      for (let i = 0; i < subs.length; i += 20) {
        await Promise.all(subs.slice(i, i + 20).map(async ([name, v]) => {
          try { const st = await sendPush(v.subscription, message, env); if (st === 404 || st === 410) { gone++; await env.SUBS.delete(name); } else if (st >= 200 && st < 300) sent++; else failed++; } catch (e) { failed++; }
        }));
      }
    }
    cursor = page.list_complete ? null : page.cursor;
  } while (cursor);
  const log = { at: new Date().toISOString(), topic, live, matched, sent, gone, failed, message };
  await env.SUBS.put('log:' + topic + ':last', JSON.stringify(log));
  return log;
}
export default {
  async fetch(req, env) {
    const url = new URL(req.url), path = url.pathname.replace(/\/+$/, '');
    const h = cors(req, env);
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: h });
    if (path === '/api/push/health') {
      const l = await env.SUBS.list({ prefix: 'sub:', limit: 1000 });
      return json({ ok: true, subscribers: l.keys.length + (l.list_complete ? '' : '+'), sendEnabled: env.SEND_ENABLED === 'true' }, 200, h);
    }
    if (path === '/api/push/vapid') return json({ publicKey: env.VAPID_PUBLIC_KEY }, 200, h);
    if (path === '/api/push/subscribe' && req.method === 'POST') {
      let b; try { b = await req.json(); } catch (e) { return json({ ok: false, error: 'bad json' }, 400, h); }
      const s = b && b.subscription, ep = s && s.endpoint;
      let host = ''; try { const u = new URL(ep); if (u.protocol === 'https:') host = u.hostname; } catch (e) {}
      if (!host || !PUSH_HOSTS.test(host) || ep.length > 1024 || !s.keys || !s.keys.p256dh || !s.keys.auth || s.keys.p256dh.length > 128 || s.keys.auth.length > 64) return json({ ok: false, error: 'bad subscription' }, 400, h);
      const topics = (Array.isArray(b.topics) ? b.topics : []).filter(t => TOPICS.includes(t));
      if (!topics.length) return json({ ok: false, error: 'no topics' }, 400, h);
      const id = await idFor(ep);
      await env.SUBS.put('sub:' + id, JSON.stringify({ subscription: { endpoint: ep, keys: { p256dh: s.keys.p256dh, auth: s.keys.auth } }, topics, tz: String(b.tz || '').slice(0, 64), created: new Date().toISOString() }), { metadata: { t: topics } });
      return json({ ok: true, id, topics }, 200, h);
    }
    if (path === '/api/push/unsubscribe' && req.method === 'POST') {
      let b; try { b = await req.json(); } catch (e) { return json({ ok: false }, 400, h); }
      if (!b || typeof b.endpoint !== 'string') return json({ ok: false }, 400, h);
      await env.SUBS.delete('sub:' + await idFor(b.endpoint));
      return json({ ok: true }, 200, h);
    }
    if (path === '/api/push/admin/preview' && isAdmin(req, env)) {
      return json({ deltas: await deltasMessage(env), newDrop: await newDropMessage(env, false), lastDrops: await env.SUBS.get('log:drops:last', 'json'), lastDeltas: await env.SUBS.get('log:deltas:last', 'json'), lastDropSeen: await env.SUBS.get('state:last-drop') });
    }
    if (path === '/api/push/admin/test' && req.method === 'POST' && isAdmin(req, env)) {
      const b = await req.json().catch(() => ({}));
      const v = b.endpoint && await env.SUBS.get('sub:' + await idFor(b.endpoint), 'json');
      if (!v) return json({ ok: false, error: 'not subscribed' }, 404);
      const status = await sendPush(v.subscription, { title: 'The Rubber Duck', body: 'Test alert. Alerts are working.', url: '/alerts/', tag: 'test' }, env, 600);
      return json({ ok: status >= 200 && status < 300, status });
    }
    if (path === '/api/push/admin/run' && req.method === 'POST' && isAdmin(req, env)) {
      const which = url.searchParams.get('job');
      if (which === 'deltas') return json(await fanOut('deltas', await deltasMessage(env), env));
      if (which === 'drops') { const m = await newDropMessage(env, true); return json(m ? await fanOut('drops', m, env) : { none: true, lastDropSeen: await env.SUBS.get('state:last-drop') }); }
      return json({ error: 'job=deltas|drops' }, 400);
    }
    return json({ ok: false, error: 'not found' }, 404, h);
  },
  async scheduled(event, env, ctx) {
    if (event.cron === '0 13 * * *') ctx.waitUntil(deltasMessage(env).then(m => fanOut('deltas', m, env)));
    else ctx.waitUntil(newDropMessage(env, true).then(m => m && fanOut('drops', m, env)));
  },
};
