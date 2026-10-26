"""Rebuild only the shop listing pages (shop/<slug>/index.html) and the merch.html structured data from merch.html,
without the full site build (tools/seo-build.py runs drops, X, library, sitemaps and more).
Added on branch umbrella-special-orders (Oct 26 2026). Usage, from the repo root:  python3 tools/build_shop_only.py"""
import importlib.util, os
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'seo-build.py')
spec = importlib.util.spec_from_file_location('seobuild', p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
items = m.build_shop()
m.ROOMS = {'merch.html': m.ROOMS['merch.html']}   # only the store page carries the product list
m.build_rooms(items)
print('rebuilt %d shop pages + merch.html structured data' % len(items))
