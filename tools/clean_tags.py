#!/usr/bin/env python3
"""
clean_tags.py — clean the tag lists in the Meme Dump's memes.json.

    python3 clean_tags.py memes.json memes.cleaned.json
    python3 clean_tags.py https://therubberduck.net/memes/data/memes.json memes.json --csv tag-cleanup.csv

Python 3.8+ standard library only. Word lists are read from ./wordlists/ next to this
script (override with --lists DIR):
    words-common.txt   google-10000-english "20k.txt" (the full version of tools/data/words-common.txt)
    firstnames.txt     US first names      (smashew/NameDatabases)
    surnames.txt       US surnames         (smashew/NameDatabases)
    english-5plus.txt  dwyl/english-words words_alpha, words of 5+ letters
    allowlist.txt      optional extra words/names to always keep, one per line
Any list that is missing is skipped (the result is just stricter).

What it changes, per record (nothing else is touched: id, file, source, sha256, ocr,
faces, typeTag ... are left exactly as they are):
    topics      cleaned (see the rules below and tag-cleanup.csv for every drop)
    visualTags  busy / mid / landscape / earth / colour names ... moved OUT of topics
    entityTags  keyword concepts (trump, epstein, jfk ...) by WHOLE-word match
    textWords   up to 24 real words from the OCR text (now for every record)
    textWordCount
Safe to re-run on its own output (idempotent).
"""
import argparse, collections, csv, json, os, re, sys, urllib.request

ap = argparse.ArgumentParser(description="Clean memes.json tags.")
ap.add_argument("src", help="input memes.json (path or http(s) URL)")
ap.add_argument("dst", help="output memes.json")
ap.add_argument("--csv", default="tag-cleanup.csv", help="per-tag log of what was dropped/added")
ap.add_argument("--lists", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "wordlists"))
args = ap.parse_args()

if re.match(r"https?://", args.src):
    with urllib.request.urlopen(args.src, timeout=60) as r:
        doc = json.loads(r.read().decode("utf-8"))
else:
    with open(args.src, encoding="utf-8") as f:
        doc = json.load(f)
items = doc["items"] if isinstance(doc, dict) else doc

def load_list(name, minlen=3):
    p = os.path.join(args.lists, name)
    if not os.path.exists(p):
        if name != "allowlist.txt":
            sys.stderr.write(f"note: word list {p} not found, skipped\n")
        return set()
    with open(p, encoding="utf-8", errors="ignore") as f:
        return {l.strip().lower() for l in f if len(l.strip()) >= minlen and not l.startswith("#")}

COMMON = load_list("words-common.txt")
NAMES = load_list("firstnames.txt") | load_list("surnames.txt")
BIGDICT = load_list("english-5plus.txt", 5)

# Always-keep list: names, acronyms and real words that are in none of the lists.
# Reviewed by hand against the dropped list on 2026-10-21 (be conservative when adding).
KNOWN = {
  # site vocabulary
  "elon","flotus","wwg1wga","wwgiwga","ncswic","rfk","jfkjr","anunnaki","dyncorp","qanon","potus","djt","maga",
  "hrc","bho","gitmo","pizzagate","pedogate","adrenochrome","fauci","ghislaine","epstein","soros","schwab",
  "zelensky","obama","biden","hillary","kamala","pelosi","comey","mueller","brennan","clapper","podesta","weiner",
  "hanx","oprah","kardashian","spielberg","steinbart","qdrop","qdrops","8kun","8chan","4chan","cnn","msnbc",
  "mossad","pompeo","terramar","sigint","invesco","whoopi","canaveral","pubchem","lizardman","mdcclxxvi",
  "wikileaks","scorsese","nanotube",
  # real names / words found in the dropped list (kept as they appear)
  "kobebryant","scorcese","donaldtrump","jeffreyguterman","federalreserve","abedin","bourdain","deepak",
  "demolay","hamutal","nirmal","sternfeld","yeon","amalie","alistair","piet","marmont","mccarran","tioga",
  "justia","cubase","vecteezy","metoo","memes","whoa","swat","penne","foes","snot","subaward","unpublish",
  "fgm148javelin","ceos","qalerts",
}
KNOWN |= load_list("allowlist.txt", 2)

def is_real(w):
    if len(w) > 4 and w.endswith("s") and _real(w[:-1]): return True
    return _real(w)
def _real(w):
    return (w in COMMON or w in NAMES or w in KNOWN or w in ENTITY_KEYS or (len(w) >= 5 and w in BIGDICT))

ENTITY_TAGS = {
 "epstein": ["epstein", "ghislaine", "maxwell"], "jfk": ["jfk", "kennedy", "oswald"],
 "diana": ["diana", "dodi"], "peta": ["peta"], "fema": ["fema"],
 "covid": ["covid", "corona", "coronavirus", "pandemic", "plandemic", "vaccine", "vaccines", "vaxx"],
 "election": ["election", "elections", "ballot", "ballots", "vote", "voting", "voter", "elector", "electors"],
 "aliens": ["alien", "aliens", "ufo", "ufos", "uap", "extraterrestrial"],
 "spielberg": ["spielberg"], "smokey": ["smokey"],
 "army": ["army", "soldier", "soldiers", "military", "troop", "troops"],
 "flag": ["flag", "flags", "usa"], "mma": ["mma", "ufc"],
 "qanon": ["qanon", "q-anon", "qarmy", "wwg1wga"], "q": ["qanon", "wwg1wga", "qdrop", "qdrops"],
 "potus": ["potus", "president"], "biden": ["biden", "brandon"], "trump": ["trump", "maga", "djt"],
 "clinton": ["clinton", "clintons"], "obama": ["obama"], "putin": ["putin", "russia", "russian"],
 "hillary": ["hillary"], "hunter": ["hunter-biden"], "fauci": ["fauci"], "fbi": ["fbi"], "cia": ["cia"],
 "doj": ["doj", "justice department"], "navy": ["navy"], "seals": ["navy seal", "navy seals"],
 "antifa": ["antifa"], "blm": ["blm", "black lives"], "ukraine": ["ukraine", "ukrainian", "zelensky"],
 "israel": ["israel", "israeli", "israelis", "idf"], "vatican": ["vatican"], "pope": ["pope", "papal"],
 "celebrity": ["austin steinbart", "celine", "kardashian", "oprah"],
 "movies": ["movie", "movies", "film", "cinema", "star wars", "matrix"],
 "tv": ["tv", "episode"], "cars": ["car", "cars", "mustang", "ferrari", "truck", "drive-in"],
 "food": ["food", "pizza", "bread", "burger"],
 "animals": ["duck", "dog", "cat", "bear", "bird", "horse"],
 "religion": ["church", "bible", "jesus", "god", "prayer", "religion"],
 "historical": ["washington crossing", "1776", "revolution", "leutze"],
 "document": ["document", "memo", "letter", "report", "filing"], "chart": ["chart", "graph", "poll"],
 "tweet-screenshot": ["twitter", "tweet", "retweet"],
 "music": ["song", "album", "band", "music"], "sports": ["sport", "sports", "coach"],
 "memorial": ["memorial", "funeral", "grave"],
 "conspiracy": ["conspiracy", "coverup", "cover-up", "psyop", "false flag"],
 "protest": ["protest", "riot", "riots"], "police": ["police", "cop", "cops", "sheriff"],
 "money": ["money", "dollar", "dollars", "bank", "banks", "economy"],
 "space": ["nasa", "space", "moon", "mars"], "tech": ["tech", "robot", "computer", "internet"],
 "media": ["cnn", "msnbc", "fox news", "media", "journalist", "journalists"],
}
ENTITY_KEYS = {k for v in ENTITY_TAGS.values() for k in v} | set(ENTITY_TAGS)
FACE_TAGS = {"face", "one face", "two faces", "crowd"}
KEEP_FLAGS = {"document", "tweet-screenshot", "chart", "animated", "text-in-image", "screenshot"}
VISUAL = {"busy","flat","mid","bright","dark","landscape","portrait","square","wide","ultra-wide","tall",
  "mono","neon","green","blue","cool","red","earth","warm","neutral","thumb","small","medium","large","xl",
  "light","heavy","very-heavy","still","smooth","soft","textured","video"}
HUES = {"crimson","orange","amber","gold","yellow","green","teal","cyan","azure","blue","indigo","violet","magenta",
  "ink","charcoal","slate","grey","silver","white"}
TYPE = {"meme","gif","clip"}
JUNK_WORDS = {"img","image","images","download","downloaded","downsized","untitled","default","hqdefault",
  "sddefault","maxresdefault","thumbnail","thumb","screenshot","screen","shot","capture","snip","photo","pic",
  "picture","copy","final","new","tmp","temp","gif","jpg","jpeg","png","webp","mp4","mov","video","original",
  "file","dsc","dcim","pxl","mvimg","vid","fullsize","resized","scaled","edit","edited","poster","large","small",
  "medium","orig","chatgpt","jan","feb","mar","apr","jun","jul","aug","sep","sept","oct","nov","dec","pm","am"}
KEEP_SHORT = {"q", "tv", "us", "uk", "un", "jfk", "cia", "fbi", "doj", "dhs", "nsa", "mma", "ufo", "uap", "blm",
  "idf", "gop", "dnc", "rnc", "nyc", "dc", "ai", "djt", "hrc", "bho", "maga", "nato", "fema", "peta", "nasa", "usaf"}
STOP = set("""a an the and or of to in on at for with from by is are was were be been this that these those it its as
his her their our your my you we they he she i not no but if then than so very just into over under about all any can
do does did how what when where which who why will would may might shall should must have has had s t re ve ll d m
one two get got out off up down here there now also only some such more most other each few own same too own""".split())

def shape_ok(w):
    if len(w) < 3: return False
    if not re.search(r"[aeiouy]", w): return False
    if re.search(r"(.)\1\1", w): return False
    if re.search(r"[bcdfghjklmnpqrstvwxz]{4,}", w): return False
    r = len(re.findall(r"[aeiouy]", w)) / len(w)
    return 0.18 <= r <= 0.80

def is_id_fragment(t):
    s = t.replace("-", "")
    if re.search(r"\d", s) and re.search(r"[a-z]", s) and s not in KEEP_SHORT and not re.fullmatch(r"\d{4}s?", s):
        return True                       # 4f4e, 535901f5, ebfsfwjw4ae1nx6, fyyko8
    if re.fullmatch(r"[0-9a-f]{6,}", s):  # long pure hex
        return True
    return False

# OCR corpus: a word-shaped token seen in 2+ different memes is probably real text
corpus = collections.Counter()
for it in items:
    toks = {t.lower() for t in re.findall(r"[A-Za-z][A-Za-z]{2,23}", it.get("ocr") or "")}
    corpus.update(toks)

def fname_words(src):
    base = re.sub(r"\.[A-Za-z0-9]+$", "", src).replace("%20", " ")
    raw = [p.lower() for p in re.split(r"[\s_\-.()\[\],+&']+", base) if p]
    base = re.sub(r"([a-z])([A-Z])", r"\1 \2", base)
    out = raw + [p.lower() for p in re.split(r"[\s_\-.()\[\],+&']+", base) if p]
    # "citizens1" -> also "citizens" (the word part a filename tag may have been reduced to)
    return out + [re.sub(r"\d+$", "", p) for p in out if re.fullmatch(r"[a-z]{3,}\d{1,3}", p)]

def ocr_words(text):
    out = []
    for tok in re.findall(r"[A-Za-z][A-Za-z]{2,23}", text or ""):
        w = tok.lower()
        if w in out or w in STOP or w in JUNK_WORDS or not shape_ok(w): continue
        if is_real(w) or (len(w) >= 4 and corpus.get(w, 0) >= 2):
            out.append(w)
    return out

def whole(blob, k):
    return re.search(r"(?<![a-z0-9])" + re.escape(k) + r"(?:s|es)?(?![a-z0-9])", blob) is not None

dropped = collections.Counter(); reason_of = {}; examples = collections.defaultdict(list)
kept_ct = collections.Counter(); added = collections.Counter()
before_total = after_total = 0
for it in items:
    old = list(it.get("topics") or [])
    before_total += len(old)
    fw = fname_words(it.get("source", "")) + fname_words(it.get("title", ""))
    ow = ocr_words(it.get("ocr", ""))
    blob = " ".join([" ".join(fw), (it.get("ocr") or "").lower(), (it.get("title") or "").lower()])
    blob = re.sub(r"[_\-]+", " ", blob)
    ents = [tag for tag, keys in ENTITY_TAGS.items() if any(whole(blob, k.replace("-", " ")) or whole(blob, k) for k in keys)]
    new, vis = [], [v for v in (it.get("visualTags") or []) if isinstance(v, str)]
    def drop(t, why):
        dropped[(t, why)] += 1; examples[(t, why)].append(it["id"])
    for t in old:
        tl = t.lower()
        if tl in FACE_TAGS or tl in KEEP_FLAGS:
            if tl == "screenshot" and not it.get("screenshot") and "screenshot" not in (it.get("source","").lower()):
                pass
            new.append(tl); continue
        if tl in TYPE:
            drop(tl, "type word (kept as the Type filter)"); continue
        if tl in VISUAL or tl in HUES or tl.startswith(("deep-", "pale-")):
            if tl not in vis: vis.append(tl)
            drop(tl, "visual descriptor (kept as a Look filter, not a topic)"); continue
        if tl in ENTITY_TAGS:
            if tl in ents: new.append(tl)
            else: drop(tl, "keyword false positive (matched inside another word)")
            continue
        if re.fullmatch(r"\d{4}s?", tl):
            new.append(tl); continue          # years / decades
        camel = None
        tl_word = re.sub(r"\d+$", "", tl)
        for src_ in (it.get("source", ""), it.get("title", "")):
            parts = [p.lower() for p in re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])", re.sub(r"\.[A-Za-z0-9]+$", "", src_))]
            if len(parts) > 1 and "".join(parts) == tl_word and all(is_real(p) for p in parts if len(p) > 2):
                camel = parts
        if camel and tl not in KNOWN:
            drop(tl, "joined-up filename words (split into separate words)")
            new.extend(p for p in camel if len(p) > 2 and p not in STOP and p not in JUNK_WORDS)
            continue
        m = re.fullmatch(r"([a-z]{3,})(\d{1,3})", tl)
        if m and tl not in KNOWN and m.group(1) in JUNK_WORDS:
            drop(tl, "filename junk word"); continue
        if m and tl not in KNOWN and (is_real(m.group(1)) or shape_ok(m.group(1))):
            drop(tl, "word with a number glued on (word kept)"); new.append(m.group(1)); continue
        if tl in KNOWN:
            new.append(tl); continue
        if is_id_fragment(tl):
            drop(tl, "hash/ID fragment"); continue
        if tl in JUNK_WORDS:
            drop(tl, "filename junk word"); continue
        if len(tl) < 3 and tl not in KEEP_SHORT:
            drop(tl, "too short"); continue
        if tl in STOP:
            drop(tl, "stopword"); continue
        in_fname = tl in fw
        if in_fname:
            # human-chosen filename words: keep if they look like words / names
            if is_real(tl) or tl in KEEP_SHORT or shape_ok(tl):
                new.append(tl)
            else:
                drop(tl, "filename gibberish (not word-shaped)")
            continue
        # came from OCR
        if tl in ow or tl in KEEP_SHORT or is_real(tl):
            new.append(tl)
        else:
            drop(tl, "OCR noise (not a dictionary word, known name or repeated word)")
    for e in ents:
        if e not in new:
            new.append(e); added[(e, "keyword (whole-word match)")] += 1
    # dedupe, keep order
    seen = set(); new = [t for t in new if not (t in seen or seen.add(t))]
    it["topics"] = new
    it["visualTags"] = vis
    it["entityTags"] = ents
    it["textWords"] = ow[:24]
    it["textWordCount"] = len(ow[:24])
    after_total += len(new)
    for t in new: kept_ct[t] += 1


if isinstance(doc, dict):
    doc["count"] = len(items)
    doc["tagsCleaned"] = "clean_tags.py v2"
with open(args.dst + ".tmp", "w", encoding="utf-8") as f:
    json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))
os.replace(args.dst + ".tmp", args.dst)

with open(args.csv, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["tag", "action", "reason", "records", "example_ids"])
    for (t, why), n in sorted(dropped.items(), key=lambda x: (-x[1], x[0])):
        w.writerow([t, "dropped", why, n, " ".join(examples[(t, why)][:5])])
    for (t, why), n in sorted(added.items(), key=lambda x: -x[1]):
        w.writerow([t, "added", why, n, ""])

summ = collections.Counter(); uniq = collections.Counter()
for (t, why), n in dropped.items(): summ[why] += n; uniq[why] += 1
print(f"records {len(items)} | tag uses before {before_total} after {after_total} | distinct tags after {len(kept_ct)}")
for why, n in summ.most_common(): print(f"  dropped  {why}: {uniq[why]} distinct, {n} uses")
print(f"  added    keyword (whole-word match): {len(added)} distinct, {sum(added.values())} uses")
print(f"  records with no topic tags left: {sum(1 for it in items if not it['topics'])}")
