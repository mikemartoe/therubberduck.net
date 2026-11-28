/* Email signup: .signup-form now hands off to Substack (the one newsletter, chosen by Mike 2026-11-23).
   With JS: the reader's email opens therubberduck78.substack.com/subscribe?email=... in a new tab,
   where they press Subscribe; this page says so plainly and never claims success itself.
   Without JS the form still POSTs to its HTML action (old MailerLite list) until the page templates are rebuilt. */
(function () {
  var SUB = 'https://therubberduck78.substack.com/subscribe';
  var forms = document.querySelectorAll('form.signup-form');
  function ev(r, t) {
    var path = 'event/form/newsletter-' + r, title = 'Form: newsletter signup ' + t + ' (' + location.pathname + ')';
    try {
      if (window.trdTrack) window.trdTrack(path, title, 0);
      else if (window.goatcounter && window.goatcounter.count) window.goatcounter.count({ path: path, title: title, event: true });
      if (window.trdVisit) window.trdVisit.event('form', { name: 'newsletter', result: r });
    } catch (e) {}
  }
  for (var i = 0; i < forms.length; i++) (function (f) {
    var msg = f.nextElementSibling, inp = f.querySelector('input[type=email]');
    function say(html, err) { if (!msg) return; msg.innerHTML = html; msg.className = 'signup-msg' + (err ? ' err' : ''); }
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      var addr = (inp && inp.value || '').trim();
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(addr)) { say('that email doesn\'t look right. check it and try again.', true); if (inp) inp.focus(); return; }
      var url = SUB + '?email=' + encodeURIComponent(addr) + '&utm_source=therubberduck.net&utm_medium=inline';
      var win = null;
      try { win = window.open(url, '_blank'); if (win) win.opener = null; } catch (x) { win = null; }
      ev('substack-handoff', 'handed off to Substack');
      f.hidden = true;
      say('almost there. press <b>subscribe</b> on the substack tab ' + (win ? 'that just opened' : 'here') +
          ', and the sunday recap starts coming. <a href="' + url.replace(/"/g, '&quot;') + '" target="_blank" rel="noopener">' +
          (win ? 'tab didn\'t open? finish here' : 'finish on substack') + '</a>');
    });
  })(forms[i]);
})();

/* Archive search in the sticky header (Vincent brief P2): the same search as the main pages' header,
   over /assets/search/site-index.json, with X posts handed to the X Archive. */
(function () {
  var wrap = document.querySelector('header.top .wrap');
  if (!wrap || document.getElementById('tn-q')) return;
  var css = document.createElement('link'); css.rel = 'stylesheet'; css.href = '/assets/trd/sitenav.css?v=8917b1b4e2'; document.head.appendChild(css);
  var f = document.createElement('form');
  f.className = 'tn-search'; f.id = 'tn-form'; f.setAttribute('role', 'search'); f.action = '/x/'; f.method = 'get';
  f.innerHTML = '<svg class="tn-mag" viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="2.4"/><path d="M15.5 15.5 21 21" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>' +
    '<input class="tn-q" id="tn-q" name="q" type="search" placeholder="Search the archive" aria-label="Search the whole archive" autocomplete="off" role="combobox" aria-expanded="false" aria-controls="tn-res" aria-autocomplete="list">' +
    '<div class="tn-res" id="tn-res" role="listbox" aria-label="Search results" hidden></div>';
  wrap.appendChild(f);
  if (!window.trdNav) { var s = document.createElement('script'); s.src = '/assets/trd/sitenav.js?v=6f4020eadf'; document.head.appendChild(s); }
})();
