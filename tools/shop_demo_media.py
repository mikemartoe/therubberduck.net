"""Demo media (video + photo) shown under a shop listing's facts.
Only listings whose existing color options match the demo hat get media.
Used by tools/seo-build.py build_shop(); keep markup self-contained (archive.css is shared by every archive page)."""

DEMO_MEDIA = {
    # Black / White is the only trucker color on the listing that matches a demo hat (black front, white mesh).
    'duck-trucker-hat': [
        {'color': 'Black / White', 'base': '/store-img/demo/duck-trucker-hat_black-white_demo'},
    ],
}

def demo_block(slug):
    items = DEMO_MEDIA.get(slug)
    if not items:
        return ''
    figs = []
    for i, m in enumerate(items):
        b = m['base']; c = m['color']
        figs.append(
            '<figure class="dm"><div class="dm-v"><video src="%s.mp4" poster="%s.jpg" width="720" height="1280" muted loop playsinline autoplay preload="metadata" aria-label="Trucker hat, %s, lifted above the TRD box"></video>'
            '<button type="button" class="dm-snd" aria-pressed="false" aria-label="Turn sound on">&#128263; Sound</button></div>'
            '<figcaption>%s &middot; video</figcaption></figure>'
            '<figure class="dm"><picture><source srcset="%s.webp" type="image/webp"><img src="%s.jpg" alt="Trucker hat, %s, above the TRD box" width="720" height="1280" loading="lazy" decoding="async"></picture>'
            '<figcaption>%s &middot; photo</figcaption></figure>' % (b, b, c, c, b, b, c, c))
    return ('<h2>In the box</h2><style>.dms{display:flex;flex-wrap:wrap;gap:14px;margin:6px 0 10px}.dm{margin:0;flex:1 1 220px;max-width:300px}'
            '.dm video,.dm img{display:block;width:100%;height:auto;aspect-ratio:9/16;object-fit:cover;border-radius:6px;border:1px solid var(--line);background:#111}'
            '.dm-v{position:relative}.dm-snd{position:absolute;right:8px;bottom:8px;font:700 13px/1 system-ui,sans-serif;color:#140e05;background:var(--gold);border:0;border-radius:999px;padding:8px 12px;cursor:pointer;opacity:.92}'
            '.dm-snd[aria-pressed="true"]{background:var(--ink)}.dm figcaption{color:var(--muted);font-size:13px;margin-top:6px}'
            '@media(max-width:640px){.dm{flex-basis:calc(50% - 7px)}}</style>'
            '<div class="dms">{FIGS}</div><p class="meta">Demo with music from The Red Pill Album (&ldquo;The Storm Is Upon Us&rdquo;). The hat as made to order is pictured at the top of this page.</p>'
            '<script>(function(){var rm=window.matchMedia&&matchMedia("(prefers-reduced-motion: reduce)").matches;'
            'document.querySelectorAll(".dm-v").forEach(function(w){var v=w.querySelector("video"),b=w.querySelector(".dm-snd");'
            'if(rm){v.removeAttribute("autoplay");v.pause();}'
            'b.addEventListener("click",function(){v.muted=!v.muted;if(!v.muted){document.querySelectorAll(".dm-v video").forEach(function(o){if(o!==v)o.muted=true;});v.play();}'
            'b.setAttribute("aria-pressed",String(!v.muted));b.setAttribute("aria-label",v.muted?"Turn sound on":"Mute");b.innerHTML=v.muted?"&#128263; Sound":"&#128266; Mute";});});})();</script>'
            ).replace('{FIGS}', ''.join(figs))
