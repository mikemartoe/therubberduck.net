/* Cloudflare Worker: trd-visits  (NOT DEPLOYED: see README.md)
   POST /api/v          JSON array of hits from assets/trd/visit.js -> D1 table hits
   GET  /api/v/report   ?days=30  aggregate report (needs header  Authorization: Bearer <REPORT_KEY>)
   Never stores IP addresses, user agents or cookies. Rows older than 400 days are deleted by the cron. */
const TYPES = new Set(['view', 'leave', 'hide', 'event']);
const s = (x, n) => (typeof x === 'string' && x ? x.slice(0, n) : null);
const i = (x) => (Number.isFinite(x) ? Math.max(0, Math.min(Math.round(x), 2 ** 31)) : null);

async function ingest(req, env) {
  const origin = req.headers.get('origin') || '';
  if (origin && !/^https:\/\/(www\.)?therubberduck\.net$/.test(origin)) return new Response('', { status: 403 });
  const text = await req.text();
  if (text.length > 20000) return new Response('', { status: 413 });
  let rows; try { rows = JSON.parse(text); } catch { return new Response('', { status: 400 }); }
  if (!Array.isArray(rows)) return new Response('', { status: 400 });
  const now = Date.now();
  const stmt = env.DB.prepare(`INSERT OR IGNORE INTO hits (visit,seq,ts,type,path,room,ms,ref,source,medium,campaign,dev,event,platform,item)
    VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11,?12,?13,?14,?15)`);
  const batch = [];
  for (const h of rows.slice(0, 50)) {
    if (!h || !/^[0-9a-f]{16}$/.test(h.v) || !TYPES.has(h.t) || !Number.isInteger(h.n)) continue;
    batch.push(stmt.bind(h.v, h.n, now, h.t, s(h.p, 200), s(h.room, 20), i(h.ms), s(h.ref, 80), s(h.source, 60), s(h.medium, 30),
      s(h.campaign, 60), s(h.dev, 10), s(h.e, 30), s(h.platform, 20), s(h.item, 60)));
  }
  if (batch.length) await env.DB.batch(batch);
  return new Response(null, { status: 204, headers: { 'access-control-allow-origin': 'https://therubberduck.net' } });
}

async function report(url, env) {
  const days = Math.min(400, Math.max(1, parseInt(url.searchParams.get('days') || '30', 10)));
  const since = Date.now() - days * 864e5;
  const q = (sql) => env.DB.prepare(sql).bind(since).all().then((r) => r.results);
  const [totals, rooms, flows, shared, platforms, sources, roomTime] = await Promise.all([
    q(`WITH v AS (SELECT visit, SUM(CASE WHEN type='view' THEN 1 ELSE 0 END) pages,
          SUM(CASE WHEN type='leave' THEN ms ELSE 0 END) ms, COUNT(DISTINCT CASE WHEN type='view' THEN room END) rooms
        FROM hits WHERE ts>=?1 GROUP BY visit)
       SELECT COUNT(*) visits, AVG(pages) pages_per_visit, AVG(ms)/1000.0 avg_seconds,
              AVG(CASE WHEN rooms>1 THEN 1.0 ELSE 0 END) multi_room_share FROM v`),
    q(`SELECT room, COUNT(*) views, COUNT(DISTINCT visit) visits FROM hits WHERE type='view' AND ts>=?1 GROUP BY room ORDER BY views DESC`),
    q(`WITH o AS (SELECT visit, group_concat(room, ' > ') path FROM (SELECT visit, room FROM hits WHERE type='view' AND ts>=?1 ORDER BY visit, seq) GROUP BY visit)
       SELECT path, COUNT(*) visits FROM o GROUP BY path ORDER BY visits DESC LIMIT 15`),
    q(`SELECT item, COUNT(*) taps FROM hits WHERE type='event' AND event='share' AND ts>=?1 GROUP BY item ORDER BY taps DESC LIMIT 20`),
    q(`SELECT platform, COUNT(*) taps FROM hits WHERE type='event' AND event='share' AND ts>=?1 GROUP BY platform ORDER BY taps DESC`),
    q(`SELECT source, medium, COUNT(*) visits FROM hits WHERE type='view' AND source IS NOT NULL AND ts>=?1 GROUP BY source, medium ORDER BY visits DESC`),
    q(`SELECT room, AVG(ms)/1000.0 avg_seconds FROM hits WHERE type='leave' AND ts>=?1 GROUP BY room ORDER BY avg_seconds DESC`),
  ]);
  return Response.json({ days, totals: totals[0], rooms, flows, shared, platforms, returns_by_source: sources, time_by_room: roomTime });
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (url.pathname === '/api/v' && req.method === 'POST') return ingest(req, env);
    if (url.pathname === '/api/v/report' && req.method === 'GET') {
      if (!env.REPORT_KEY || req.headers.get('authorization') !== 'Bearer ' + env.REPORT_KEY) return new Response('', { status: 401 });
      return report(url, env);
    }
    return new Response('', { status: 404 });
  },
  async scheduled(_e, env) { await env.DB.prepare('DELETE FROM hits WHERE ts < ?1').bind(Date.now() - 400 * 864e5).run(); },
};
