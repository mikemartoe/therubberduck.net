"""The umbrella special-order rule (Mike, Oct 26 2026) and the six-color lineup for the signed listings.

THE RULE: anything listed in the store is ours to deliver. A listed option that can't be mapped to a product our printer
(Printful) can make today is a SPECIAL ORDER: its own Stripe link with manual capture (card authorized, not charged), never
sent to Printful automatically; Mike gets alerts (new / day 4 / 24 h left / expired); we take up to 7 extra days to source
and make it; the card is charged when a partner maker confirms; if nobody can make it within those 7 days the hold is
released (or, if already charged, every penny is refunded) at once. The buyer agrees at checkout.

This file is the single place that says which listed colors are special. tools/apply_umbrella_lineup.py writes it into
merch.html; tools/build_shop_only.py then rebuilds the shop pages. The order forwarder (trd-merch, outside this repo)
keeps its own copy of the same status in printful-map.json (_special / _retired) and must agree with this file.
"""

PROMISE_DAYS = 7          # extra days we give ourselves to source and make a special order (= Stripe's card-hold window)

# (label, image key, swatch color) -- the new lineup, in display order
LINEUP = [
    ('Black', 'black', '#141414'),
    ('White', 'white', '#f3f2ee'),
    ('Navy', 'navy', '#1f2a44'),
    ('Gold', 'gold', '#d9a50a'),
    ('Tiffany Blue', 'tiffany', '#81d8d0'),
    ('Hot Pink', 'hotpink', '#dd1e78'),
]
RETIRED = ['Pink', 'Light Blue']   # never offered again on the signed listings; the forwarder refuses them

# Placeholder checkout links for special orders that don't exist in Stripe yet. A link containing '/PENDING-' is shown
# as "Special order link not live yet" and can't be clicked (merch.html script); tools/check_umbrella_ready.py fails
# the deploy while any remain. Replace each one with the real buy.stripe.com URL once Mike approves and it is created.
def pending(name):
    return 'https://buy.stripe.com/PENDING-' + name

# Live manual-capture special-order links, created Oct 26 2026 on acct_1NvT2xGC9fEXRvQS (see trd-merch/stripe-links.json)
SIGNED_TEE_SP_SXL = 'https://buy.stripe.com/bJefZhahKgVi5KD6nJ9IQ1a'   # plink_1UUrumGC9fEXRvQSXijL69MJ
SIGNED_TEE_SP_2XL = 'https://buy.stripe.com/14A8wPcpSbAY5KD9zV9IQ1b'   # plink_1UUrv4GC9fEXRvQSq9AYflZc
SIGNED_TEE_SP_3XL = 'https://buy.stripe.com/4gM5kDblO7kI4Gz9zV9IQ1c'   # plink_1UUrvCGC9fEXRvQS3MjhbEb9

# Signed listings: which lineup colors are special orders today and why (Printful variant mapping, checked Oct 26 2026
# against trd-merch/printful-map.json and the Printful catalog dumps).
SIGNED = {
    'signed-dad-hat': {
        # Yupoong 6245CM in Printful has Black, White and Navy; it has no Gold, Tiffany Blue or Hot Pink.
        'special': ['Gold', 'Tiffany Blue', 'Hot Pink'],
        'special_link': 'https://buy.stripe.com/8x2fZh9dG8oMdd5bI39IQ1d',  # plink_1UUrvKGC9fEXRvQSK5Zmr6An
    },
    'signed-trucker-hat': {
        # Richardson 112 in Printful: only "Black / White" (black front, white mesh) matches the lineup, shown as Black.
        'special': ['White', 'Navy', 'Gold', 'Tiffany Blue', 'Hot Pink'],
        'special_link': 'https://buy.stripe.com/PENDING-hold',  # trucker on hold (Mike t1957u): was 6oU9ATahKbAYdd56nJ9IQ1e;  # plink_1UUrvRGC9fEXRvQSdmlmIAGr
    },
    'signed-tee': {
        # Bella+Canvas 3001 has Gold (the Red Pill Tee already sells it), but the Signed Tee's Printful product (483809952)
        # had no Gold variants; Gold S-3XL were added to it on Oct 26 2026 (sync variants 5597415939..5597416378), so Gold is NORMAL.
        'special': ['Tiffany Blue', 'Hot Pink'],
        'special_links': {'S': SIGNED_TEE_SP_SXL, 'M': SIGNED_TEE_SP_SXL,
                          'L': SIGNED_TEE_SP_SXL, 'XL': SIGNED_TEE_SP_SXL,
                          '2XL': SIGNED_TEE_SP_2XL, '3XL': SIGNED_TEE_SP_3XL},
    },
}

# Unsigned listings in the same lineup (Mike approved Oct 26 2026: Duck Dad Hat moves to the new lineup; Light Blue, Pink and
# Charcoal retired). Yupoong 6245CM in Printful has Black, White and Navy but no Gold, Tiffany Blue or Hot Pink -> special orders.
UNSIGNED = {
    'duck-dad-hat': {
        'special': ['Gold', 'Tiffany Blue', 'Hot Pink'],
        'img': 'duck-dad-hat_%s_product',
        'special_link': 'https://buy.stripe.com/00wfZh2PidJ62yraDZ9IQ1f',  # plink_1UUrvYGC9fEXRvQSDH1GFaLj
    },
}
# Unsigned Trucker Hat (Oct 26 2026, hat colors): the listing's demo shows the six lineup colors, so all six are sold.
# Richardson 112 in Printful has four two-tones (Black / White, Charcoal / Black, Heather Grey / Black, Heather Grey / White), all
# NORMAL; the demo's "Black" IS Black / White (black front, white mesh). White, Navy, Gold, Tiffany Blue and Hot Pink have no
# Richardson 112 blank in Printful -> special orders on their own link. Kept out of UNSIGNED on purpose: tools/apply_umbrella_lineup.py
# would rewrite the card to the six-color lineup and drop the two-tones. tools/apply_trucker_lineup.py writes this into merch.html.
TRUCKER = {
    'duck-trucker-hat': {
        'special': ['White', 'Navy', 'Gold', 'Tiffany Blue', 'Hot Pink'],
        'img': 'duck-trucker-hat-sp_%s',     # tools/make_trucker_special_photos.py (recolored Printful mockup, no pill)
        'special_link': 'https://buy.stripe.com/PENDING-hold',  # trucker on hold (Mike t1957u): was aFa5kD61uawUb4XdQb9IQ1h;  # plink_1UUzh0GC9fEXRvQS7z44aKlu
        'demo_label': {'black': 'Black / White'},
    },
}
# US shipping on the special-order links (Stripe shipping rates, read back Oct 26 2026): unsigned $4.95 (shr_1UUtZq), signed $8.95
# (shr_1UUtjw). The regular hat links charge $4.75 (unsigned) / $8.95 (signed).
SPECIAL_SHIP = {'duck-dad-hat': '4.95', 'duck-trucker-hat': '4.95', 'signed-dad-hat': '8.95', 'signed-trucker-hat': '8.95'}

RETIRED_UNSIGNED = {'duck-dad-hat': ['Light Blue', 'Pink', 'Charcoal']}

# ---- wording (one place) ----
# Oct 26 2026 (Mike): shipping time is the same standard time across the board; a special order adds UP TO 7 EXTRA DAYS on top of
# the item's standard time. Public text never gives the reason for the 7 days (no "source", "partner" or "maker" wording).
STD_SHIP_UNSIGNED = '3-8 business days'      # regular items
STD_SHIP_SIGNED = 'about 2 to 3 weeks'       # signed pieces: hand-signed and numbered, then mailed (unchanged)
EXTRA = 'up to 7 extra days'

def special_when(signed):
    """'Ships in 3-8 business days, plus up to 7 extra days' (signed: 'about 2 to 3 weeks, plus ...')."""
    return 'Ships in %s, plus %s' % (STD_SHIP_SIGNED if signed else STD_SHIP_UNSIGNED, EXTRA)

PROMISE_TITLE = 'The TRD Promise'
PROMISE_TEXT = ('If it&rsquo;s listed here, it&rsquo;s ours to deliver. Everything ships in our standard time. A few colors are special '
                'orders and may take up to 7 extra days; your card is only authorized, not charged, until we confirm your order. If we '
                'can&rsquo;t fill it within those 7 days, every penny comes back to you.')
# store card note (short) -- unsigned / signed
NOTE_UNSIGNED = ('<b>Special order</b> Ships in 3-8 business days, plus up to 7 extra days. Card authorized, not charged, until we confirm '
                 'your order. Not filled within 7 days? Hold released at once, you pay nothing. You&rsquo;ll agree at checkout.')
NOTE_SIGNED = ('<b>Special order</b> Ships in about 2 to 3 weeks (signed and numbered by hand), plus up to 7 extra days. Card authorized, '
               'not charged, until we confirm your order. Not filled within 7 days? Hold released at once, you pay nothing. You&rsquo;ll agree at checkout.')
SHIP_SPECIAL = 'Special order: up to 7 extra days'
SHIPIN_SPECIAL_UNSIGNED = '3-8d +7d'
SHIPIN_SPECIAL_SIGNED = '2-3w +7d'
# listing pages (long)
LISTING_SPECIAL = ('{colors} {verb}. Special-order colors ship in {std}{signed}, plus up to 7 extra days. Your card is only '
                   'authorized, not charged, until we confirm your order. If we can&rsquo;t fill it within those 7 days, the hold is released at '
                   'once and you pay nothing; if you were already charged, every penny is refunded. '
                   'You&rsquo;ll be asked to agree at checkout.')
