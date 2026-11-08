#!/usr/bin/env python3
"""Checks the pinned Military Intelligence feature stays on the verified stream file."""
import json, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
EXACT = "\u203c\ufe0f\U0001f3b6MILITARY INTELLIGENCE\U0001f3b6\u203c\ufe0f\n\n\"The Walken Edit\"\n\n\U0001f449\U0001f3fc lyrics by Q."
URL = "https://stream.therubberduck.net/video-room/military-intelligence-walken-edit-20261108.mp4"
SHA = "4f58a944bc30a713cd929f73153747728e774b06ed93f2869e3b86ec5c96dfb1"
rec = next(v for v in json.loads((ROOT / "data/video-room-local.json").read_text()) if v["id"] == "lmiwalken01")
js = json.loads((ROOT / "data/video-room-local.js").read_text().split(" = ", 1)[1].rstrip().rstrip(";"))
jsrec = next(v for v in js if v["id"] == "lmiwalken01")
page = (ROOT / "videos/share/lmiwalken01.html").read_text()
room = (ROOT / "videos.html").read_text()
assert jsrec == rec
assert rec["desc"] == EXACT and rec["mq"] == EXACT.split("\n\n")
assert rec["published"] is True and rec["pinned"] is True
assert rec["u"] == rec["mediaUrl"] == URL
assert rec["probe"]["sha256"] == SHA and rec["probe"]["bytes"] == 69988129
assert "icloud" not in URL and not URL.endswith(".mov")
blob = json.dumps(rec) + page
assert "qalerts" not in blob.lower() and "icloud.com" not in blob
assert "autoplay" not in page
assert 'href="/videos.html#v=lmiwalken01"' in page
assert "PINNED_ID = 'lmiwalken01'" in room and "v.pinned ? null : nextPlayable" in room
assert "lmiwalken01.html" in (ROOT / "sitemaps/video-share.xml").read_text()
print("ok")
