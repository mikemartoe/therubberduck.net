/* Shared rolling search prompts for the Drop Ledger and the installed app home (/app/).
   Mounts an aria-hidden ticker over an empty, unfocused input. The input keeps its aria-label. */
(function (root) {
  'use strict';
  var FIRST = 'Search the Q drops';
  var PROMPTS = [
    FIRST,
    '#4966',
    'Hillary',
    'Oct 2018',
    'future proves past',
    'today',
    'what about Hillary?',
    'FISA',
    'WWG1WGA',
    '10/22/2020',
    'Flynn',
    'the storm',
    'today ± 3 days',
    'why was Flynn fired?',
    'map',
    'HRC Oct 2018',
    'POTUS',
    'yesterday',
    'how do we know?',
    'mockingbird',
    '#1',
    'Iran',
    'nothing can stop',
    'what about the storm?',
    'did Q mention Iran?',
    'what did Q say about Iran?',
    'Sessions',
    'this day',
    'flag',
    'who is Q?',
    '2018',
    'seal'
  ];

  var CSS = '.arc-ph-line{position:absolute;left:0;right:0;white-space:nowrap;transform:translateY(0);opacity:1;transition:transform .42s cubic-bezier(.16,1,.3,1),opacity .42s ease}' +
    '.arc-ph-line.is-out{transform:translateY(-110%);opacity:0}' +
    '.arc-ph-line.is-in{transform:translateY(110%);opacity:0}' +
    '.arc-ph-line.is-in.is-up{transform:translateY(0);opacity:1}' +
    '.arc-ph.is-off{opacity:0;visibility:hidden}' +
    '@media (prefers-reduced-motion:reduce){.arc-ph{display:none!important}}';

  function ensureCSS() {
    var d = document;
    if (d.getElementById('trd-search-ticker-css')) return;
    var st = d.createElement('style');
    st.id = 'trd-search-ticker-css';
    st.textContent = CSS;
    (d.head || d.documentElement).appendChild(st);
  }

  function mount(opts) {
    opts = opts || {};
    var d = document;
    var input = opts.input;
    var wrap = opts.wrap;
    if (!input || !wrap) return;
    if (wrap.getAttribute('data-trd-tick-on')) return;
    wrap.setAttribute('data-trd-tick-on', '1');
    var cs = wrap.currentStyle || (root.getComputedStyle && getComputedStyle(wrap));
    if (cs && cs.position === 'static') wrap.style.position = 'relative';
    var reduce = root.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduce) {
      if (!input.getAttribute('placeholder')) input.setAttribute('placeholder', FIRST);
      return;
    }
    ensureCSS();
    input.setAttribute('placeholder', '');
    if (!input.getAttribute('aria-label')) input.setAttribute('aria-label', opts.label || 'Search the Q drops');
    var ph = d.createElement('div');
    ph.className = 'arc-ph';
    if (opts.tickId) ph.id = opts.tickId;
    ph.setAttribute('aria-hidden', 'true');
    var line = d.createElement('span');
    line.className = 'arc-ph-line';
    line.textContent = FIRST;
    ph.appendChild(line);
    wrap.appendChild(ph);
    var i = 0, timer = null, moving = false;
    var photos = typeof opts.photos === 'function' ? opts.photos : function () { return false; };
    function busy() { return d.activeElement === input || !!(input.value && input.value.length) || photos(); }
    function show(on) { ph.classList.toggle('is-off', !on); }
    function schedule() {
      clearTimeout(timer);
      timer = setTimeout(tick, (i === 0) ? 2800 : 2200);
    }
    function tick() {
      if (busy()) { show(false); schedule(); return; }
      show(true);
      if (moving) { schedule(); return; }
      i = (i + 1) % PROMPTS.length;
      var incoming = d.createElement('span');
      incoming.className = 'arc-ph-line is-in';
      incoming.textContent = PROMPTS[i];
      ph.appendChild(incoming);
      line.classList.add('is-out');
      moving = true;
      requestAnimationFrame(function () { requestAnimationFrame(function () { incoming.classList.add('is-up'); }); });
      setTimeout(function () {
        if (line.parentNode) line.parentNode.removeChild(line);
        incoming.classList.remove('is-in', 'is-up');
        line = incoming; moving = false;
      }, 440);
      schedule();
    }
    input.addEventListener('focus', function () { show(false); clearTimeout(timer); });
    input.addEventListener('blur', function () { if (!busy()) { show(true); schedule(); } });
    input.addEventListener('input', function () {
      if (input.value) show(false);
      else if (d.activeElement !== input) { show(true); schedule(); }
    });
    if (input.value) show(false);
    else schedule();
  }

  function boot() {
    var wrap = document.querySelector('[data-trd-ticker]');
    if (!wrap) return;
    var sel = wrap.getAttribute('data-trd-ticker-input');
    var input = (sel && document.getElementById(sel)) || wrap.querySelector('input, textarea');
    mount({
      input: input,
      wrap: wrap,
      tickId: wrap.getAttribute('data-trd-ticker-id') || '',
      label: wrap.getAttribute('data-trd-ticker-label') || ''
    });
  }

  root.TRDSearchTicker = { mount: mount, FIRST: FIRST, PROMPTS: PROMPTS };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})(typeof window !== 'undefined' ? window : this);
