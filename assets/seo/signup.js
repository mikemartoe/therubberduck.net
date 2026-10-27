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
