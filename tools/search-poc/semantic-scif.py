#!/usr/bin/env python3
"""Search proof of concept, SCIF room: semantic (meaning-based) search.

build:  chunk every PDF page into ~900-character passages, embed each with
        bge-small-en-v1.5 (384 dims, runs on CPU, free) and save the vectors.
query:  embed a question and return the closest passages with doc, page and a
        deep link (PDF URL #page=N). In production the same vectors go to
        Cloudflare Vectorize and the query embedding runs in Workers AI.
Usage:  semantic-scif.py build <records.jsonl> <outdir>
        semantic-scif.py query <outdir> "question" [k]
"""
import json, os, sys, time, numpy as np, onnxruntime as ort
from tokenizers import Tokenizer
M = os.environ.get('BGE_DIR', '/workspace/search-poc-models/bge-small')
tok = Tokenizer.from_file(M + '/tokenizer.json'); tok.enable_truncation(256); tok.enable_padding()
so = ort.SessionOptions(); so.intra_op_num_threads = os.cpu_count()
sess = ort.InferenceSession(M + '/model_quantized.onnx', so)
names = [i.name for i in sess.get_inputs()]
def embed(texts):
    enc = tok.encode_batch(texts)
    ids = np.array([e.ids for e in enc], dtype=np.int64); am = np.array([e.attention_mask for e in enc], dtype=np.int64)
    feed = {'input_ids': ids, 'attention_mask': am}
    if 'token_type_ids' in names: feed['token_type_ids'] = np.zeros_like(ids)
    v = sess.run(None, feed)[0][:, 0]            # CLS pooling (bge)
    return v / np.linalg.norm(v, axis=1, keepdims=True)
def chunks(text, n=900, step=750):
    text = ' '.join(text.split())
    for s in range(0, max(1, len(text) - 150), step):
        c = text[s:s + n]
        if len(c) > 80: yield c
if sys.argv[1] == 'build':
    src, out = sys.argv[2], sys.argv[3]; os.makedirs(out, exist_ok=True)
    meta, buf, vecs, t0 = [], [], [], time.time()
    for line in open(src, encoding='utf-8'):
        r = json.loads(line)
        for c in chunks(r['text']):
            meta.append([r['id'], r['title'], r['shelf'], r['page'], r['url'], r['pdf'], c]); buf.append(c)
            if len(buf) == 64:
                vecs.append(embed(buf).astype(np.float16)); buf = []
                if len(meta) % 6400 == 0: print(len(meta), 'chunks', round(time.time() - t0), 's', flush=True)
    if buf: vecs.append(embed(buf).astype(np.float16))
    np.save(out + '/vectors.npy', np.vstack(vecs))
    json.dump(meta, open(out + '/chunks.json', 'w', encoding='utf-8'), ensure_ascii=False)
    print(len(meta), 'chunks embedded in', round(time.time() - t0), 's')
else:
    out, q = sys.argv[2], sys.argv[3]; k = int(sys.argv[4]) if len(sys.argv) > 4 else 5
    V = np.load(out + '/vectors.npy').astype(np.float32); meta = json.load(open(out + '/chunks.json', encoding='utf-8'))
    qv = embed(['Represent this sentence for searching relevant passages: ' + q])[0]
    sc = V @ qv; top = np.argsort(-sc)[:k * 4]; seen, res = set(), []
    for i in top:
        m = meta[i]; key = (m[0], m[3])
        if key in seen: continue
        seen.add(key); res.append(dict(score=round(float(sc[i]), 3), id=m[0], title=m[1], shelf=m[2], page=m[3],
                                       link=(m[5] or m[4]) + '#page=' + str(m[3]), passage=m[6][:300]))
        if len(res) == k: break
    print(json.dumps(dict(query=q, results=res), ensure_ascii=False, indent=1))
