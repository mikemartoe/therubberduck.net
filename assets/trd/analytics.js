/* Site analytics loader for therubberduck.net.
   Google Analytics 4 (G-8QQRLHEKJT) lives here so every public page can
   include one script. GoatCounter (gc.zgo.at) and Cloudflare analytics stay
   on the pages themselves; this file does not replace them.

   To add Umami later, fill in the Umami section below and leave this file's
   name and the <script src="/assets/trd/analytics.js"> tag on the pages
   unchanged (bump the ?v= query on that tag if the file is cached). */
(function () {
  if (window.__trdAnalytics) return;
  window.__trdAnalytics = true;

  // --- Google Analytics 4 ---
  var GA_ID = 'G-8QQRLHEKJT';
  window.dataLayer = window.dataLayer || [];
  function gtag(){ dataLayer.push(arguments); }
  window.gtag = gtag;
  gtag('js', new Date());
  gtag('config', GA_ID);
  var ga = document.createElement('script');
  ga.async = true;
  ga.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
  document.head.appendChild(ga);

  // --- Umami (add later) ---
  // var umami = document.createElement('script');
  // umami.defer = true;
  // umami.src = 'https://cloud.umami.is/script.js';
  // umami.setAttribute('data-website-id', 'YOUR-UMAMI-WEBSITE-ID');
  // document.head.appendChild(umami);
})();
