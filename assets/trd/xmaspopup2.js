/* Full-screen Christmas pop-up v2 (therubberduck.net homepage). LIVE Nov 17 2026 (Mike approved). Loaded by index.html (xmaspopup block).
   Shows the three bundle heroes ($79 / $129 / $179). Each one opens the Christmas page at that bundle's section.
   Close: the big "X EXIT" button, the Esc key, tapping outside the graphics, or "No thanks, take me to the site".
   Same frequency as v1: homepage only, hidden for 24h after a close (localStorage trd.xmasBundle.closed), off after Dec 25 2026.
   window.TRD_XMAS_PREVIEW = true -> always show (ignores the 24h close) so the preview can be checked. */
(function(){
  'use strict';
  if (window.__trdXmas2) return; window.__trdXmas2 = 1;
  var PREVIEW = !!window.TRD_XMAS_PREVIEW;
  var PAGE = window.TRD_XMAS_PAGE || '/christmas/';
  var path = location.pathname;
  if (path !== '/' && path !== '/index.html' && path !== '/index.htm') return;
  if (Date.now() >= Date.parse('2026-12-26T05:00:00.000Z')) return;
  var KEY = 'trd.xmasBundle.closed';
  if (!PREVIEW) { try { var v = localStorage.getItem(KEY); if (v && (Date.now() - Number(v)) < 864e5) return; } catch (e) {} }
  var TIERS = [
    { id: 'christmas-bundle', img: '/store-img/xmas-bundle-hero', price: '$79', items: 'Tee, baseball cap, sticker',
      alt: 'The Rubber Duck Christmas Bundle, $79 shipping included: tee, baseball cap and sticker' },
    { id: 'christmas-bundle-big-duck', img: '/store-img/xmas-bundle-big-duck-hero', price: '$129', items: 'Tee, baseball cap, mug, koozie, 2 stickers + FREE $50 ad',
      alt: 'The Rubber Duck Christmas Bundle: Big Duck, $129 shipping included' },
    { id: 'christmas-bundle-trd-mvp', img: '/store-img/xmas-bundle-trd-mvp-hero', price: '$179', items: 'Hoodie, tee, baseball cap, mug, koozie, patch, 3 stickers + FREE $50 ad',
      alt: 'The Rubber Duck Christmas Bundle: TRD-MVP, $179 shipping included' }
  ];
  var css = ''
  + '#xbp-root.x2{position:fixed;inset:0;z-index:2147483600;display:flex;flex-direction:column;align-items:stretch;justify-content:flex-start;padding:0;animation:none;color:#faf4e6;font-family:Roboto,"Helvetica Neue",Arial,sans-serif;'
  + 'background:radial-gradient(120% 80% at 50% 0%,#1f5a3c 0%,#123726 45%,#08180f 100%);overflow:hidden;-webkit-overflow-scrolling:touch}'
  + '#xbp-root.x2 *{box-sizing:border-box}'
  + '#xbp-root.x2 .x2-snow{position:absolute;inset:0;pointer-events:none;opacity:.55;background-image:radial-gradient(2px 2px at 20px 30px,#fff,transparent),radial-gradient(2px 2px at 140px 80px,#fff,transparent),radial-gradient(1.5px 1.5px at 90px 150px,#fff,transparent),radial-gradient(2.5px 2.5px at 200px 200px,#fff,transparent),radial-gradient(1.5px 1.5px at 260px 40px,#fff,transparent);background-size:300px 260px}'
  + '#xbp-root.x2 .x2-lights{position:absolute;left:0;right:0;top:0;height:22px;pointer-events:none;background-image:radial-gradient(circle at 12px 12px,#ff4b4b 0 5px,transparent 6px),radial-gradient(circle at 42px 12px,#ffd35a 0 5px,transparent 6px),radial-gradient(circle at 72px 12px,#5bdc8a 0 5px,transparent 6px),radial-gradient(circle at 102px 12px,#6fb6ff 0 5px,transparent 6px);background-size:120px 22px;filter:drop-shadow(0 0 6px rgba(255,220,140,.8))}'
  + '@media (prefers-reduced-motion:no-preference){#xbp-root.x2 .x2-snow{animation:x2snow 18s linear infinite}#xbp-root.x2{animation:x2in .25s ease}}'
  + '@keyframes x2snow{from{background-position:0 0}to{background-position:0 260px}}@keyframes x2in{from{opacity:0}to{opacity:1}}'
  + '#xbp-root.x2 #xbp-exit{position:absolute;top:max(14px,env(safe-area-inset-top));right:max(14px,env(safe-area-inset-right));z-index:3;display:flex;align-items:center;gap:10px;min-height:58px;padding:8px 20px 8px 14px;'
  + 'border:3px solid #fff;border-radius:999px;background:#c8202b;color:#fff;font:900 22px/1 Roboto,Arial,sans-serif;letter-spacing:.08em;cursor:pointer;box-shadow:0 6px 18px rgba(0,0,0,.45)}'
  + '#xbp-root.x2 #xbp-exit .x2-x{display:grid;place-items:center;width:36px;height:36px;border-radius:50%;background:#fff;color:#c8202b;font-size:26px;font-weight:900;letter-spacing:0}'
  + '#xbp-root.x2 #xbp-exit:hover,#xbp-root.x2 #xbp-exit:focus-visible{background:#e63a33;outline:3px solid #ecbe5a;outline-offset:3px}'
  + '#xbp-root.x2 .x2-wrap{position:relative;z-index:1;flex:1;min-height:0;display:flex;flex-direction:column;align-items:center;padding:30px 24px 16px}'
  + '#xbp-root.x2 .x2-hi{margin:0;font-family:Yellowtail,"Brush Script MT",cursive;font-size:clamp(2rem,4vw,3.2rem);line-height:1.1;color:#ecbe5a;text-align:center;text-shadow:0 2px 10px rgba(0,0,0,.4)}'
  + '#xbp-root.x2 .x2-sub{margin:4px 0 0;font-size:clamp(1rem,1.6vw,1.25rem);text-align:center;color:#faf4e6}'
  + '#xbp-root.x2 .x2-row{flex:1;min-height:0;width:100%;max-width:1500px;display:flex;justify-content:center;align-items:center;gap:2.2vw;padding:18px 0 10px}'
  + '#xbp-root.x2 .x2-card{display:flex;flex-direction:column;align-items:center;flex:0 0 auto;width:min(31%,calc(100vh - 270px),calc(100dvh - 270px));text-decoration:none;color:#faf4e6;min-width:0}'
  + '#xbp-root.x2 .x2-card img{display:block;width:100%;height:auto;border-radius:14px;box-shadow:0 12px 30px rgba(0,0,0,.5);transition:transform .18s}'
  + '#xbp-root.x2 .x2-card:hover img,#xbp-root.x2 .x2-card:focus-visible img{transform:translateY(-4px) scale(1.01)}'
  + '#xbp-root.x2 .x2-card:focus-visible{outline:3px solid #ecbe5a;outline-offset:6px;border-radius:14px}'
  + '#xbp-root.x2 .x2-btn{margin-top:10px;padding:12px 22px;border-radius:10px;background:#c8202b;color:#fff;font-weight:800;font-size:1.1rem;white-space:nowrap;box-shadow:0 4px 12px rgba(0,0,0,.35)}'
  + '#xbp-root.x2 .x2-foot{position:relative;z-index:1;text-align:center;padding:4px 16px max(16px,env(safe-area-inset-bottom))}'
  + '#xbp-root.x2 .x2-cut{margin:0;font-weight:700;color:#ecbe5a}'
  + '#xbp-root.x2 .x2-no{margin-top:6px;background:none;border:0;color:#faf4e6;text-decoration:underline;font:600 1rem Roboto,Arial,sans-serif;cursor:pointer;padding:8px}'
  + '#xbp-root.x2 .x2-dots,#xbp-root.x2 .x2-swipe{display:none}'
  + '@media (max-width:760px),(max-aspect-ratio:4/5){'
  + '#xbp-root.x2 .x2-wrap{padding:84px 0 6px}#xbp-root.x2 .x2-hi,#xbp-root.x2 .x2-sub{padding:0 16px}'
  + '#xbp-root.x2 .x2-row{justify-content:flex-start;overflow-x:auto;scroll-snap-type:x mandatory;gap:14px;padding:14px 9vw 8px;scrollbar-width:none}'
  + '#xbp-root.x2 .x2-row::-webkit-scrollbar{display:none}'
  + '#xbp-root.x2 .x2-card{flex:0 0 auto;width:min(82vw,calc(100dvh - 340px));scroll-snap-align:center}'
  + '#xbp-root.x2 .x2-card img{width:100%;height:auto}'
  + '#xbp-root.x2 .x2-swipe{display:block;margin:2px 0 0;font-size:.95rem;color:#e9dcc0;text-align:center}'
  + '#xbp-root.x2 .x2-dots{display:flex;justify-content:center;gap:8px;margin:4px 0 2px}'
  + '#xbp-root.x2 .x2-dots i{width:10px;height:10px;border-radius:50%;background:rgba(255,255,255,.35)}#xbp-root.x2 .x2-dots i.on{background:#ecbe5a}'
  + '#xbp-root.x2 #xbp-exit{min-height:54px;font-size:20px;padding:7px 16px 7px 10px}}';
  function el(t, a, h) { var n = document.createElement(t); if (a) for (var k in a) n.setAttribute(k, a[k]); if (h != null) n.innerHTML = h; return n; }
  function open() {
    var st = el('style', { id: 'xmaspopup2-css' }); st.textContent = css; document.head.appendChild(st);
    var root = el('div', { id: 'xbp-root', 'class': 'x2', role: 'dialog', 'aria-modal': 'true', 'aria-labelledby': 'x2-hi' });
    root.appendChild(el('div', { 'class': 'x2-snow', 'aria-hidden': 'true' }));
    root.appendChild(el('div', { 'class': 'x2-lights', 'aria-hidden': 'true' }));
    var exit = el('button', { id: 'xbp-exit', type: 'button', 'aria-label': 'Exit and go to the site' }, '<span class="x2-x" aria-hidden="true">\u00d7</span>EXIT');
    var wrap = el('div', { 'class': 'x2-wrap' });
    wrap.appendChild(el('h2', { 'class': 'x2-hi', id: 'x2-hi' }, 'Merry Christmas from The Rubber Duck'));
    wrap.appendChild(el('p', { 'class': 'x2-sub' }, 'Three Christmas bundles, shipping included on all of them. Pick the one that fits.'));
    var row = el('div', { 'class': 'x2-row' });
    TIERS.forEach(function (t) {
      var a = el('a', { 'class': 'x2-card', href: PAGE + '#' + t.id, 'data-tier': t.id });
      var pic = el('picture');
      pic.appendChild(el('source', { type: 'image/webp', srcset: t.img + '.webp' }));
      pic.appendChild(el('img', { src: t.img + '.jpg', width: '1000', height: '1000', alt: t.alt, decoding: 'async' }));
      pic.style.cssText = 'display:block;width:100%';
      a.appendChild(pic);
      a.appendChild(el('span', { 'class': 'x2-btn' }, 'See the ' + t.price + ' bundle'));
      row.appendChild(a);
    });
    wrap.appendChild(row);
    var dots = el('div', { 'class': 'x2-dots', 'aria-hidden': 'true' }, '<i class="on"></i><i></i><i></i>');
    wrap.appendChild(dots);
    wrap.appendChild(el('p', { 'class': 'x2-swipe' }, 'Swipe to see all 3 \u2192'));
    var foot = el('div', { 'class': 'x2-foot' });
    foot.appendChild(el('p', { 'class': 'x2-cut' }, 'Order by Sunday, December 6 to have it by Christmas.'));
    var no = el('button', { 'class': 'x2-no', type: 'button' }, 'No thanks, take me to the site');
    foot.appendChild(no);
    root.appendChild(exit); root.appendChild(wrap); root.appendChild(foot);
    var prev = document.activeElement, prevOverflow = document.body.style.overflow;
    function hide() {
      try { localStorage.setItem(KEY, String(Date.now())); } catch (e) {}
      document.removeEventListener('keydown', onKey, true);
      if (root.parentNode) root.parentNode.removeChild(root);
      document.body.style.overflow = prevOverflow;
      if (prev && typeof prev.focus === 'function') try { prev.focus(); } catch (e) {}
    }
    function onKey(e) {
      if (e.key === 'Escape') { e.preventDefault(); hide(); return; }
      if (e.key !== 'Tab') return;
      var f = Array.prototype.filter.call(root.querySelectorAll('a[href],button'), function (n) { return n.getClientRects().length; });
      if (!f.length) return;
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
    exit.addEventListener('click', hide);
    no.addEventListener('click', hide);
    root.addEventListener('click', function (e) { if (!e.target.closest('.x2-card, #xbp-exit, .x2-no')) hide(); });
    row.addEventListener('scroll', function () {
      var w = row.scrollWidth - row.clientWidth; var i = w > 0 ? Math.round(row.scrollLeft / w * 2) : 0;
      Array.prototype.forEach.call(dots.children, function (d, k) { d.className = k === i ? 'on' : ''; });
    }, { passive: true });
    document.addEventListener('keydown', onKey, true);
    document.body.style.overflow = 'hidden';
    document.body.appendChild(root);
    try { exit.focus({ preventScroll: true }); } catch (e) {}
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { requestAnimationFrame(open); });
  else requestAnimationFrame(open);
})();
