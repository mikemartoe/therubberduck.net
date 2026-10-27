#!/usr/bin/env python3
"""Cards v2 (2026-10-27): re-render ONLY the drops that have attached files, now with their real images, into a NEW
local folder so no existing R2 key (drops/{card,og,og2,ig}/N, immutable 1-year cache) is overwritten.

  1. images   .work/drop-images/<drop>_<i>.<ext> + manifest.json   (fetched separately: QAGG, qanon.pub fallback)
  2. render   python3 tools/drop-cards/cards_v2.py render [--jobs 4]
              -> .work/drops-v2/{card,og,ig,og2}/N.*  (= R2 trd-memes drops/v2/...), manifest.json, og2-report.json
  3. pointers python3 tools/drop-cards/cards_v2.py pointers
              -> tools/drop-cards/cards-v2.json, data/drop-cards.js (v2base + v2 list, long list updated),
                 drops/share/N.html and drops/N/index.html og:image -> drops/v2/og2/N.jpg (+ og:image:height)
Nothing here uploads, deploys or pushes. Upload drops/v2/ to R2 BEFORE the pointer changes go live.
"""
import json, os, re, subprocess, sys, shutil, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, ".work", "drops-v2")
PREFIX = "v2/"
HDR = json.load(open(os.path.join(HERE, "header-table.json")))
NUMS = sorted(r["drop"] for r in HDR if r["files"])

def run_parallel(cmds):
    ps = [subprocess.Popen(c, cwd=ROOT) for c in cmds]
    return [p.wait() for p in ps]

def render(jobs):
    os.makedirs(OUT, exist_ok=True)
    nums = [str(n) for n in NUMS]
    # card/ og/ ig/ via render_cards.py (resumable, sharded)
    run_parallel([[sys.executable, os.path.join(HERE, "render_cards.py"), "--out", OUT, "--shard", f"{k}/{jobs}"] + nums for k in range(jobs)])
    man = {}
    for k in range(jobs):
        p = os.path.join(OUT, f"manifest.shard{k}.json")
        if os.path.exists(p): man.update(json.load(open(p)))
    json.dump(man, open(os.path.join(OUT, "manifest.json"), "w"), indent=0, sort_keys=True)
    # og2/ via rightsize.py
    rs = [os.path.join(ROOT, ".work", f"drops-v2-rs{k}") for k in range(jobs)]
    run_parallel([[sys.executable, os.path.join(HERE, "rightsize.py"), "--out", rs[k]] + nums[k::jobs] for k in range(jobs)])
    os.makedirs(os.path.join(OUT, "og2"), exist_ok=True)
    rep = {}
    for d in rs:
        rep.update(json.load(open(os.path.join(d, "report.json"))))
        for f in os.listdir(os.path.join(d, "after")): shutil.move(os.path.join(d, "after", f), os.path.join(OUT, "og2", f))
        shutil.rmtree(d)
    json.dump(rep, open(os.path.join(OUT, "og2-report.json"), "w"), indent=1, sort_keys=True)
    miss = [n for n in NUMS if str(n) not in man or "error" in rep.get(str(n), {"error": 1})]
    print(f"v2: {len(NUMS)} drops, card manifest {len(man)}, og2 {sum(1 for v in rep.values() if 'error' not in v)}, failed {miss}")

def pointers():
    man = json.load(open(os.path.join(OUT, "manifest.json"))); rep = json.load(open(os.path.join(OUT, "og2-report.json")))
    ok = [n for n in NUMS if str(n) in man and "error" not in rep.get(str(n), {"error": 1})]
    v2 = {"prefix": PREFIX, "note": "drops re-rendered 2026-10-27 with their real attached images (tools/drop-cards/cards_v2.py); "
          "images on R2 trd-memes drops/v2/{card,og,og2,ig}/", "drops": {str(n): {"long": man[str(n)]["long"], "og2_h": rep[str(n)]["h"]} for n in ok}}
    open(os.path.join(HERE, "cards-v2.json"), "w").write(json.dumps(v2, indent=0, sort_keys=True) + "\n")
    sp = importlib.util.spec_from_file_location("dsb", os.path.join(ROOT, "tools", "drop-share-build.py"))
    dsb = importlib.util.module_from_spec(sp); sp.loader.exec_module(dsb)        # reads cards-v2.json
    # data/drop-cards.js: keep every existing non-v2 drop's long flag (the full card manifest is not on this box)
    js = open(os.path.join(ROOT, "data", "drop-cards.js")).read()
    old_long = json.loads(re.search(r"long:(\[[^\]]*\])", js).group(1))
    allns = sorted(dsb.V2D.keys() | set(range(1, 4967)))
    fake = {str(n): {"long": n in old_long} for n in allns}
    open(os.path.join(ROOT, "data", "drop-cards.js"), "w").write(dsb.drop_cards_js(allns, fake))
    raw = open(os.path.join(ROOT, "data", "drops.js"), encoding="utf-8").read().strip()
    drops = {d[0]: d for d in json.loads(raw[raw.index("["):raw.rstrip(";").rindex("]") + 1])}
    for n in ok:
        open(os.path.join(ROOT, "drops", "share", f"{n}.html"), "w", encoding="utf-8").write(dsb.page(drops[n]))
        p = os.path.join(ROOT, "drops", str(n), "index.html"); s = open(p, encoding="utf-8").read()
        s2 = s.replace(f"https://memes.therubberduck.net/drops/og2/{n}.jpg", f"https://memes.therubberduck.net/drops/{PREFIX}og2/{n}.jpg")
        assert s2 != s, n
        open(p, "w", encoding="utf-8").write(s2)
    print(f"pointers: {len(ok)} drops -> drops/{PREFIX}")

if __name__ == "__main__":
    a = sys.argv[1:]
    jobs = int(a[a.index("--jobs") + 1]) if "--jobs" in a else 4
    if a and a[0] == "render": render(jobs)
    elif a and a[0] == "pointers": pointers()
    else: print(__doc__)
