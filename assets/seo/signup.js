/* Email signup: progressive enhancement for .signup-form (MailerLite, double opt-in).
   Without JS the form POSTs normally (MailerLite's JSON reply opens in a new tab).
   With JS it posts via fetch() and shows an inline message. No MailerLite scripts are loaded. */
(function () {
  if (!window.fetch || !window.FormData || !window.URLSearchParams) return;
  var forms = document.querySelectorAll('form.signup-form');
  for (var i = 0; i < forms.length; i++) (function (f) {
    var msg = f.nextElementSibling, btn = f.querySelector('button');
    function say(t, err) { msg.textContent = t; msg.className = 'signup-msg' + (err ? ' err' : ''); }
    f.addEventListener('submit', function (e) {
      if (f.getAttribute('data-native')) return;           // fallback after a network error: plain POST
      e.preventDefault();
      var body = new URLSearchParams(new FormData(f)); body.append('ajax', '1');
      btn.disabled = true; say('Sending\u2026');
      fetch(f.action, { method: 'POST', body: body, mode: 'cors', credentials: 'omit' })
        .then(function (r) { return r.json(); })
        .then(function (j) {
          btn.disabled = false;
          if (j && j.success) { f.hidden = true; say('Check your inbox to confirm your email. The confirmation link finishes your signup.'); }
          else {
            var m = j && j.errors && j.errors.fields && j.errors.fields.email;
            say((m && m[0]) || 'That did not go through. Please check the address and try again.', true);
          }
        })
        .catch(function () {
          btn.disabled = false; f.setAttribute('data-native', '1');
          say('Could not reach the signup service. Press Join the list again to open it in a new tab.', true);
        });
    });
  })(forms[i]);
})();

/* Archive search in the sticky header (Vincent brief P2): the same search as the main pages' header,
   over /assets/search/site-index.json, with X posts handed to the X Archive. */
(function () {
  var wrap = document.querySelector('header.top .wrap');
  if (!wrap || document.getElementById('tn-q')) return;
  var css = document.createElement('link'); css.rel = 'stylesheet'; css.href = '/assets/trd/sitenav.css?v=2'; document.head.appendChild(css);
  var f = document.createElement('form');
  f.className = 'tn-search'; f.id = 'tn-form'; f.setAttribute('role', 'search'); f.action = '/x/'; f.method = 'get';
  f.innerHTML = '<svg class="tn-mag" viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="2.4"/><path d="M15.5 15.5 21 21" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>' +
    '<input class="tn-q" id="tn-q" name="q" type="search" placeholder="Search the archive" aria-label="Search the whole archive" autocomplete="off" role="combobox" aria-expanded="false" aria-controls="tn-res" aria-autocomplete="list">' +
    '<div class="tn-res" id="tn-res" role="listbox" aria-label="Search results" hidden></div>';
  wrap.appendChild(f);
  if (!window.trdNav) { var s = document.createElement('script'); s.src = '/assets/trd/sitenav.js?v=2'; document.head.appendChild(s); }
})();
