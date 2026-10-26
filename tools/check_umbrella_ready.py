#!/usr/bin/env python3
"""Deploy gate for the umbrella special-order change (tools/umbrella_lineup.py).
Fails (exit 1) while merch.html or any shop page still carries a https://buy.stripe.com/PENDING-* placeholder, i.e. before the
manual-capture special-order links have been created in Stripe and pasted in. Run before every deploy of this branch."""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bad = []
for dp, dn, fn in os.walk(ROOT):
    if '/.git' in dp or '/node_modules' in dp:
        continue
    for f in fn:
        if f.endswith(('.html', '.js', '.json')):
            p = os.path.join(dp, f)
            try:
                t = open(p, encoding='utf-8', errors='ignore').read()
            except OSError:
                continue
            for m in sorted(set(re.findall(r'buy\.stripe\.com/PENDING-[A-Za-z0-9-]+', t))):
                bad.append((os.path.relpath(p, ROOT), m))
for p, m in bad:
    print('NOT READY: %s still has %s' % (p, m))
print('umbrella links: %s' % ('NOT READY (%d placeholders)' % len(bad) if bad else 'ready, no PENDING placeholders'))
sys.exit(1 if bad else 0)
