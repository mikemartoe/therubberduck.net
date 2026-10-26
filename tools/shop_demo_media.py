"""Demo media (video + photo per color) shown under a shop listing's facts, in an "In the box" section.
One color tab row per listing; tapping a color swaps the video and photo. Muted autoplay loop, Sound button.
Files: /store-img/demo/<slug>_<color>_demo.{mp4,jpg,webp} (720x1280, 8 s).
Used by tools/seo-build.py build_shop(); keep markup self-contained (archive.css is shared by every archive page)."""
import html

# The six demo colors (Mike, Oct 25 2026: show the full color set; colors are being added to the lineup).
COLORS = [
    ('black', 'Black', '#111111'),
    ('white', 'White', '#f3f2ee'),
    ('tiffany', 'Tiffany Blue', '#81d8d0'),
    ('hotpink', 'Hot Pink', '#ff2a8a'),
    ('navy', 'Navy', '#1d2b4f'),
    ('gold', 'Gold', '#c9a43a'),
]

# slug -> (what the demo shows, extra caption sentence or '', list of color keys that have media)
DEMO_MEDIA = {
    'duck-trucker-hat': ('Trucker hat', '', [c[0] for c in COLORS]),
}

def _figs(slug, kind, key, label):
    b = '/store-img/demo/%s_%s_demo' % (slug, key)
    a = html.escape('%s, %s, lifted above the TRD box' % (kind, label))
    return ('<figure class="dm"><div class="dm-v"><video src="%s.mp4" poster="%s.jpg" width="720" height="1280" muted loop playsinline autoplay preload="metadata" aria-label="%s"></video>'
            '<button type="button" class="dm-snd" aria-pressed="false" aria-label="Turn sound on">&#128263; Sound</button></div>'
            '<figcaption><span class="dm-c">%s</span> &middot; video</figcaption></figure>'
            '<figure class="dm"><picture><source srcset="%s.webp" type="image/webp"><img src="%s.jpg" alt="%s" width="720" height="1280" loading="lazy" decoding="async"></picture>'
            '<figcaption><span class="dm-c">%s</span> &middot; photo</figcaption></figure>') % (b, b, a, label, b, b, a, label)

def demo_block(slug):
    entry = DEMO_MEDIA.get(slug)
    if not entry:
        return ''
    kind, extra, keys = entry
    cols = [c for c in COLORS if c[0] in keys]
    names = [c[1] for c in cols]
    names_txt = ', '.join(names[:-1]) + ' and ' + names[-1] if len(names) > 1 else names[0]
    tabs = ''.join('<button type="button" role="tab" class="dm-t" data-c="%s" data-l="%s" aria-selected="%s" style="--sw:%s"><i></i>%s</button>'
                   % (k, html.escape(l), 'true' if i == 0 else 'false', sw, html.escape(l)) for i, (k, l, sw) in enumerate(cols))
    k0, l0, _ = cols[0]
    css = ('<style>.dmx{margin:6px 0 10px}.dm-tabs{display:flex;gap:8px;overflow-x:auto;padding:2px 2px 10px;scrollbar-width:thin;-webkit-overflow-scrolling:touch}'
           '.dm-t{flex:0 0 auto;display:inline-flex;align-items:center;gap:7px;font:600 14px/1 system-ui,sans-serif;color:var(--ink);background:transparent;border:1px solid var(--line);border-radius:999px;padding:9px 13px 9px 9px;cursor:pointer;min-height:40px}'
           '.dm-t i{width:18px;height:18px;border-radius:50%;background:var(--sw);box-shadow:inset 0 0 0 1px rgba(128,128,128,.55)}'
           '.dm-t[aria-selected="true"]{border-color:var(--gold);box-shadow:0 0 0 1px var(--gold) inset}'
           '.dms{display:flex;flex-wrap:wrap;gap:14px}.dm{margin:0;flex:1 1 220px;max-width:300px}'
           '.dm video,.dm img{display:block;width:100%;height:auto;aspect-ratio:9/16;object-fit:cover;border-radius:6px;border:1px solid var(--line);background:#111}'
           '.dm-v{position:relative}.dm-snd{position:absolute;right:8px;bottom:8px;font:700 13px/1 system-ui,sans-serif;color:#140e05;background:var(--gold);border:0;border-radius:999px;padding:8px 12px;cursor:pointer;opacity:.92}'
           '.dm-snd[aria-pressed="true"]{background:var(--ink)}.dm figcaption{color:var(--muted);font-size:13px;margin-top:6px}'
           '@media(max-width:640px){.dms{gap:10px}.dm{flex-basis:calc(50% - 5px)}}</style>')
    js = ('<script>(function(){var rm=window.matchMedia&&matchMedia("(prefers-reduced-motion: reduce)").matches;'
          'document.querySelectorAll(".dmx").forEach(function(x){var s=x.getAttribute("data-slug"),v=x.querySelector("video"),b=x.querySelector(".dm-snd"),'
          'src=x.querySelector("source"),img=x.querySelector("img"),tabs=x.querySelectorAll(".dm-t");'
          'if(rm){v.removeAttribute("autoplay");v.pause();}'
          'function setb(){b.setAttribute("aria-pressed",String(!v.muted));b.setAttribute("aria-label",v.muted?"Turn sound on":"Mute");b.innerHTML=v.muted?"&#128263; Sound":"&#128266; Mute";}'
          'b.addEventListener("click",function(){v.muted=!v.muted;if(!v.muted){document.querySelectorAll(".dmx video").forEach(function(o){if(o!==v)o.muted=true;});v.play();}setb();});'
          'tabs.forEach(function(t){t.addEventListener("click",function(){if(t.getAttribute("aria-selected")==="true")return;'
          'tabs.forEach(function(o){o.setAttribute("aria-selected",String(o===t));});'
          'var c=t.getAttribute("data-c"),l=t.getAttribute("data-l"),p="/store-img/demo/"+s+"_"+c+"_demo",a=x.getAttribute("data-kind")+", "+l+", lifted above the TRD box";'
          'v.poster=p+".jpg";v.src=p+".mp4";v.setAttribute("aria-label",a);src.srcset=p+".webp";img.src=p+".jpg";img.alt=a;'
          'x.querySelectorAll(".dm-c").forEach(function(e){e.textContent=l;});if(!rm||!v.muted)v.play().catch(function(){});});});});})();</script>')
    cap = ('<p class="meta">The demo shows the %s in each color: %s. %sNew colors are being added to the lineup; the colors you can order today are listed above. '
           'Demo music from The Red Pill Album (&ldquo;The Storm Is Upon Us&rdquo;).</p>') % (kind.lower(), html.escape(names_txt), extra)
    return ('<h2>In the box</h2>' + css +
            '<div class="dmx" data-slug="%s" data-kind="%s"><div class="dm-tabs" role="tablist" aria-label="Demo color">%s</div><div class="dms">%s</div>%s</div>'
            % (slug, html.escape(kind), tabs, _figs(slug, kind, k0, l0), cap) + js)
