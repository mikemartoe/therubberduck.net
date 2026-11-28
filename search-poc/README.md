# Search proof of concept (preview branch only, not linked from the site)

SCIF room: full-text keyword search over every PDF page (Pagefind), plus an
offline semantic-search demo (bge-small embeddings) that shows how AI search
would find passages by meaning.

Rebuild (from the repo root):

    python3 tools/search-poc/extract-scif-records.py /tmp/scif-pages.jsonl
    (cd tools/search-poc && node build-scif-pagefind.mjs /tmp/scif-pages.jsonl ../../search-poc/scif/pagefind)
    python3 tools/search-poc/semantic-scif.py build /tmp/scif-pages.jsonl /tmp/scif-semantic
    python3 tools/search-poc/semantic-scif.py query /tmp/scif-semantic "who wrote about mind war"

The generated Pagefind index (113 MB, 22,856 small files for 22,191 PDF pages)
is not committed. A phone downloads only the few chunks a query needs. In
production it would be served from R2 or committed by the build step.
Page text comes from the SCIF retitle work (JSON per doc with page-level text
and OCR for scanned pages); this POC only reads it.
