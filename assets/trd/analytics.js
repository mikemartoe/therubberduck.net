/* Site analytics loader for therubberduck.net.
   Google Analytics 4 (G-8QQRLHEKJT) and Umami Cloud
   (website 39b0d7e9-44bb-42f0-aad8-c9e4ef61e694) live here so every public
   page can include one script. GoatCounter (gc.zgo.at) and Cloudflare
   analytics stay on the pages themselves; this file does not replace them.

   GA is queued immediately, but the gtag.js script itself waits until
   window load + requestIdleCallback so it does not compete with first paint.
   Bump the ?v= query on the <script src="/assets/trd/analytics.js"> tag
   if this file is cached. */
(function () {
  if (window.__trdAnalytics) return;
  window.__trdAnalytics = true;

  // --- Google Analytics 4 (queue now, fetch the script after first paint) ---
  var GA_ID = 'G-8QQRLHEKJT';
  window.dataLayer = window.dataLayer || [];
  function gtag(){ dataLayer.push(arguments); }
  window.gtag = gtag;
  gtag('js', new Date());
  gtag('config', GA_ID);
  function loadGa() {
    if (document.querySelector('script[src*="googletagmanager.com/gtag/js"]')) return;
    var ga = document.createElement('script');
    ga.async = true;
    ga.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
    document.head.appendChild(ga);
  }
  function afterPaint(fn) {
    var run = function () {
      if (window.requestIdleCallback) requestIdleCallback(fn, { timeout: 3000 });
      else setTimeout(fn, 1);
    };
    if (document.readyState === 'complete') run();
    else window.addEventListener('load', run);
  }
  afterPaint(loadGa);

  // --- Umami Cloud ---
  var umami = document.createElement('script');
  umami.defer = true;
  umami.src = 'https://cloud.umami.is/script.js';
  umami.setAttribute('data-website-id', '39b0d7e9-44bb-42f0-aad8-c9e4ef61e694');
  document.head.appendChild(umami);
})();
