/* The Rubber Duck service worker (PWA preview, 2026-10-30).
   - Caches only a small static shell (offline page, app CSS/JS, icons).
   - Pages (HTML) are always network-first and are never stored; offline, the
     offline page is shown instead. Drop pages are never cached here.
   - Everything else goes straight to the network (normal HTTP caching).
   - Handles push alerts (new drops, daily Deltas digest). */
var VERSION = 'trd-shell-20261030a';
var SHELL = [
  '/offline.html',
  '/assets/trd/pwa.css?v=20261030a',
  '/assets/trd/pwa.js?v=20261030a',
  '/images/app/app-icon-192.png',
  '/images/app/app-icon-maskable-192.png',
  '/images/app/duck-white.svg'
];
self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(VERSION).then(function (c) { return c.addAll(SHELL); }).then(function () { return self.skipWaiting(); }));
});
self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k.indexOf('trd-shell-') === 0 && k !== VERSION; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});
self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;
  var url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  if (req.mode === 'navigate') {
    e.respondWith(fetch(req).catch(function () {
      return caches.match('/offline.html').then(function (r) { return r || new Response('Offline', { status: 503, headers: { 'content-type': 'text/plain' } }); });
    }));
    return;
  }
  if (SHELL.indexOf(url.pathname + url.search) !== -1) {
    e.respondWith(caches.match(req).then(function (r) { return r || fetch(req); }));
  }
});
self.addEventListener('push', function (e) {
  var d = {};
  try { d = e.data ? e.data.json() : {}; } catch (x) { d = { body: e.data ? e.data.text() : '' }; }
  var title = d.title || 'The Rubber Duck';
  e.waitUntil(self.registration.showNotification(title, {
    body: d.body || '',
    icon: '/images/app/app-icon-192.png',
    badge: '/images/app/app-icon-maskable-192.png',
    tag: d.tag || 'trd',
    data: { url: d.url || '/' }
  }));
});
self.addEventListener('notificationclick', function (e) {
  e.notification.close();
  var target = new URL((e.notification.data && e.notification.data.url) || '/', self.location.origin).href;
  e.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (list) {
    for (var i = 0; i < list.length; i++) { if (list[i].url === target && 'focus' in list[i]) return list[i].focus(); }
    return self.clients.openWindow(target);
  }));
});
