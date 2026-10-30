/* TRD share row: one module for the Drop Ledger, the Meme Dump and the Video Room.
   window.trdShare.build(opts) returns a share row element:
     opts = { kind:'drop'|'meme'|'video', id:'520', page:'https://therubberduck.net/drops/share/520.html',
              text:'Q drop #520', thumb:<preview image url>, file:<full image url>, igFile:<4:5 image url or null>,
              fileName:'q-drop-520.png', hints:{ig:..., tiktok:...} (optional: replaces the default hint lines) }
   Video Room: file/thumb are the poster frame, never the video, so a share tap never downloads a video.
   Every outbound link carries utm_source=<platform>&utm_medium=share&utm_campaign=<kind>-<id>.
   Every tap is counted: GoatCounter event (assets/trd/track.js) + the anonymous visit beacon (assets/trd/visit.js).
   What each button really does:
     X, Truth Social, Facebook  open the platform's share page with the link (and text where the platform allows it)
     Email, Text                open the device's mail / messages app with the text and link filled in
     TikTok, Instagram          neither accepts a post from a web page. On phones that can share files, the
                                system share sheet opens with the image; otherwise the image downloads. Either
                                way the link is copied and a one-line instruction shows.
     Copy link                  copies the link.                                                                 */
(function () {
  'use strict';
  var W = window, D = document;
  if (W.trdShare) return;
  var SITE = 'https://therubberduck.net';
  function svg(d, fill) { return '<svg viewBox="0 0 24 24" aria-hidden="true"' + (fill ? ' class="f"' : '') + '>' + d + '</svg>'; }
  var I = {
    x: svg('<path d="M14.234 10.162 22.977 0h-2.072l-7.591 8.824L7.251 0H.258l9.168 13.343L.258 24H2.33l8.016-9.318L16.749 24h6.993zm-2.837 3.299-.929-1.329L3.076 1.56h3.182l5.965 8.532.929 1.329 7.754 11.09h-3.182z"/>', 1),
    truth: svg('<path d="M3 4h13v3.6h-4.6V20H7.6V7.6H3z"/><rect x="16.6" y="16.2" width="4.4" height="3.8" rx=".4"/>', 1),
    fb: svg('<path d="M9.101 23.691v-7.98H6.627v-3.667h2.474v-1.58c0-4.085 1.848-5.978 5.858-5.978.401 0 .955.042 1.468.103a8.68 8.68 0 0 1 1.141.195v3.325a8.623 8.623 0 0 0-.653-.036 26.805 26.805 0 0 0-.733-.009c-.707 0-1.259.096-1.675.309a1.686 1.686 0 0 0-.679.622c-.258.42-.374.995-.374 1.752v1.297h3.919l-.386 2.103-.287 1.564h-3.246v8.245C19.396 23.238 24 18.179 24 12.044c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.628 3.874 10.35 9.101 11.647Z"/>', 1),
    tiktok: svg('<path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/>', 1),
    ig: svg('<path d="M7.0301.084c-1.2768.0602-2.1487.264-2.911.5634-.7888.3075-1.4575.72-2.1228 1.3877-.6652.6677-1.075 1.3368-1.3802 2.127-.2954.7638-.4956 1.6365-.552 2.914-.0564 1.2775-.0689 1.6882-.0626 4.947.0062 3.2586.0206 3.6671.0825 4.9473.061 1.2765.264 2.1482.5635 2.9107.308.7889.72 1.4573 1.388 2.1228.6679.6655 1.3365 1.0743 2.1285 1.38.7632.295 1.6361.4961 2.9134.552 1.2773.056 1.6884.069 4.9462.0627 3.2578-.0062 3.668-.0207 4.9478-.0814 1.28-.0607 2.147-.2652 2.9098-.5633.7889-.3086 1.4578-.72 2.1228-1.3881.665-.6682 1.0745-1.3378 1.3795-2.1284.2957-.7632.4966-1.636.552-2.9124.056-1.2809.0692-1.6898.063-4.948-.0063-3.2583-.021-3.6668-.0817-4.9465-.0607-1.2797-.264-2.1487-.5633-2.9117-.3084-.7889-.72-1.4568-1.3876-2.1228C21.2982 1.33 20.628.9208 19.8378.6165 19.074.321 18.2017.1197 16.9244.0645 15.6471.0093 15.236-.005 11.977.0014 8.718.0076 8.31.0215 7.0301.0839m.1402 21.6932c-1.17-.0509-1.8053-.2453-2.2287-.408-.5606-.216-.96-.4771-1.3819-.895-.422-.4178-.6811-.8186-.9-1.378-.1644-.4234-.3624-1.058-.4171-2.228-.0595-1.2645-.072-1.6442-.079-4.848-.007-3.2037.0053-3.583.0607-4.848.05-1.169.2456-1.805.408-2.2282.216-.5613.4762-.96.895-1.3816.4188-.4217.8184-.6814 1.3783-.9003.423-.1651 1.0575-.3614 2.227-.4171 1.2655-.06 1.6447-.072 4.848-.079 3.2033-.007 3.5835.005 4.8495.0608 1.169.0508 1.8053.2445 2.228.408.5608.216.96.4754 1.3816.895.4217.4194.6816.8176.9005 1.3787.1653.4217.3617 1.056.4169 2.2263.0602 1.2655.0739 1.645.0796 4.848.0058 3.203-.0055 3.5834-.061 4.848-.051 1.17-.245 1.8055-.408 2.2294-.216.5604-.4763.96-.8954 1.3814-.419.4215-.8181.6811-1.3783.9-.4224.1649-1.0577.3617-2.2262.4174-1.2656.0595-1.6448.072-4.8493.079-3.2045.007-3.5825-.006-4.848-.0608M16.953 5.5864A1.44 1.44 0 1 0 18.39 4.144a1.44 1.44 0 0 0-1.437 1.4424M5.8385 12.012c.0067 3.4032 2.7706 6.1557 6.173 6.1493 3.4026-.0065 6.157-2.7701 6.1506-6.1733-.0065-3.4032-2.771-6.1565-6.174-6.1498-3.403.0067-6.156 2.771-6.1496 6.1738M8 12.0077a4 4 0 1 1 4.008 3.9921A3.9996 3.9996 0 0 1 8 12.0077"/>', 1),
    email: svg('<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3.5 6.5l8.5 6.5 8.5-6.5"/>'),
    sms: svg('<path d="M4 5h16v11H9l-5 4z"/><path d="M8 10.5h.01M12 10.5h.01M16 10.5h.01"/>'),
    link: svg('<path d="M10 14a4.5 4.5 0 006.4 0l3-3a4.5 4.5 0 00-6.4-6.4l-1.2 1.2"/><path d="M14 10a4.5 4.5 0 00-6.4 0l-3 3a4.5 4.5 0 006.4 6.4l1.2-1.2"/>')
  };
  var P = [
    ['x', 'X'], ['truth', 'Truth'], ['fb', 'Facebook'], ['tiktok', 'TikTok'],
    ['ig', 'Instagram'], ['email', 'Email'], ['sms', 'Text'], ['link', 'Copy link']
  ];
  /* utm_source names (what shows up in the analytics) */
  var SRC = { x: 'x', truth: 'truthsocial', fb: 'facebook', tiktok: 'tiktok', ig: 'instagram', email: 'email', sms: 'sms', link: 'copylink' };
  var HINT = {
    ig: 'Image saved + link copied. Post it on Instagram, paste the link in a story link sticker.',
    tiktok: 'Image saved + link copied. Post it on TikTok as a photo, paste the link in the caption.',
    igShare: 'Link copied. Pick Instagram, then paste the link in a story link sticker.',
    tiktokShare: 'Link copied. Pick TikTok, then paste the link in the caption.',
    link: 'Link copied.'
  };

  /* GoatCounter event titles per kind (the event path is always event/<kind>-share/<platform>/<id>) */
  var LABEL = { drop: 'Q drop #', meme: 'Meme ', video: 'Video ' };

  function tagged(page, p, camp) {
    var u = new URL(page, SITE);
    u.searchParams.set('utm_source', SRC[p]);
    u.searchParams.set('utm_medium', 'share');
    u.searchParams.set('utm_campaign', camp);
    return u.href;
  }
  /* the exact URL each button opens (exported so it can be tested) */
  function hrefFor(p, o) {
    var camp = o.kind + '-' + o.id, link = tagged(o.page, p, camp), e = encodeURIComponent;
    switch (p) {
      case 'x': return 'https://x.com/intent/tweet?text=' + e(o.text) + '&url=' + e(link);
      case 'truth': return 'https://truthsocial.com/share?text=' + e(o.text) + '&url=' + e(link);
      case 'fb': return 'https://www.facebook.com/sharer/sharer.php?u=' + e(link);
      case 'email': return 'mailto:?subject=' + e(o.text) + '&body=' + e(o.text + '\n' + link);
      case 'sms': return 'sms:?&body=' + e(o.text + ' ' + link);
      default: return link;   /* tiktok, ig, link: the link itself (copied) */
    }
  }
  function count(p, o) {
    try { if (W.trdTrack) W.trdTrack('event/' + o.kind + '-share/' + SRC[p] + '/' + o.id, (LABEL[o.kind] || (o.kind + ' ')) + o.id + ' shared: ' + SRC[p], 0); } catch (e) {}
    try { if (W.trdVisit) W.trdVisit.event('share', { platform: SRC[p], item: o.kind + '-' + o.id }); } catch (e) {}
  }
  function copyText(t) {
    try { if (navigator.clipboard && navigator.clipboard.writeText) return navigator.clipboard.writeText(t).then(function () { return true; }, function () { return legacy(t); }); } catch (e) {}
    return Promise.resolve(legacy(t));
  }
  function legacy(t) {
    var ta = D.createElement('textarea'); ta.value = t; ta.setAttribute('readonly', ''); ta.style.cssText = 'position:fixed;opacity:0;top:0';
    D.body.appendChild(ta); ta.select(); var ok = false; try { ok = D.execCommand('copy'); } catch (e) {} ta.remove(); return ok;
  }
  function fetchBlob(url) {
    return fetch(url, { mode: 'cors', credentials: 'omit' }).then(function (r) { if (!r.ok) throw 0; return r.blob(); });
  }
  function saveBlob(blob, name) {
    var a = D.createElement('a'), u = URL.createObjectURL(blob);
    a.href = u; a.download = name; D.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(u); }, 4000);
  }

  function build(o) {
    /* o.only: optional list of platform keys to offer (e.g. ['x','truth','fb','email','sms','link']).
       o.compact: icon-only inline row (label in aria-label + title), no preview picture. */
    var row = D.createElement('div'), list = o.only ? P.filter(function (p) { return o.only.indexOf(p[0]) > -1; }) : P;
    if (o.compact) o.noPic = true;
    row.className = 'shr' + (o.noPic ? ' shr-nopic' : '') + (o.compact ? ' shr-compact' : '');
    row.setAttribute('data-share-kind', o.kind);
    row.innerHTML =
      (o.noPic ? '' : '<a class="shr-pic" href="' + o.file + '" target="_blank" rel="noopener"><img src="' + o.thumb + '" alt="" loading="lazy" decoding="async"></a>') +
      (o.compact ? '<span class="shr-lbl" aria-hidden="true">Share</span>' : '') +
      '<div class="shr-btns" role="group" aria-label="' + (o.groupLabel || 'Share') + '">' + list.map(function (p) {
        var lab = (p[0] === 'link' ? 'Copy link' : 'Share to ' + p[1]);
        return '<button type="button" class="shr-b shr-' + p[0] + '" data-p="' + p[0] + '" aria-label="' + lab + '"' + (o.compact ? ' title="' + lab + '"' : '') + '>' + I[p[0]] + (o.compact ? '' : '<span>' + p[1] + '</span>') + '</button>';
      }).join('') + '</div>' +
      '<p class="shr-hint" role="status" aria-live="polite" hidden></p>';
    var hint = row.querySelector('.shr-hint'), files = {}, H = o.hints ? Object.assign({}, HINT, o.hints) : HINT;
    function say(t) { hint.textContent = t; hint.hidden = !t; }
    /* fetch the image now so the share sheet can open inside the tap (iOS needs that) */
    function prep(url) { if (!files[url]) files[url] = fetchBlob(url).then(function (b) { files[url + ':b'] = b; return b; }, function () { files[url + ':b'] = null; return null; }); return files[url]; }
    var pic = (o.igFile || o.file);
    if (navigator.canShare && list.some(function (p) { return p[0] === 'ig' || p[0] === 'tiktok'; })) prep(pic);
    row.querySelector('.shr-btns').addEventListener('click', function (ev) {
      var b = ev.target.closest('[data-p]'); if (!b) return;
      var p = b.getAttribute('data-p'), href = hrefFor(p, o);
      count(p, o);
      if (p === 'x' || p === 'truth' || p === 'fb') { W.open(href, '_blank', 'noopener,width=680,height=640'); say(''); return; }
      if (p === 'email' || p === 'sms') { location.href = href; say(''); return; }
      if (p === 'link') { copyText(href).then(function (ok) { say(ok ? H.link : href); if (ok && o.compact) { clearTimeout(row._t); row._t = setTimeout(function () { say(''); }, 2600); } }); return; }
      /* tiktok / ig */
      copyText(href);
      var blob = files[pic + ':b'], name = o.fileName.replace(/\.(\w+)$/, (o.igFile ? '-4x5' : '') + '.$1');
      if (blob && navigator.canShare) {
        var f = new File([blob], name, { type: blob.type || 'image/png' });
        if (navigator.canShare({ files: [f] })) {
          navigator.share({ files: [f] }).catch(function () {});
          say(H[p === 'ig' ? 'igShare' : 'tiktokShare']); return;
        }
      }
      (blob ? Promise.resolve(blob) : fetchBlob(pic)).then(function (bb) { saveBlob(bb, name); }, function () { W.open(pic, '_blank', 'noopener'); });
      say(H[p]);
    });
    return row;
  }
  W.trdShare = { build: build, hrefFor: hrefFor, tagged: tagged, HINT: HINT, PLATFORMS: P, SRC: SRC };
})();
