/* Documents that stay on the shelf and keep their own pages, and are never
   put in a search index this tool builds. TRD-0087 is the scanned contact
   directory. The room still lists it. Search must not. */
/* TRD-0087 stays on the shelf. TRD-0129 is a saved 404, not a document; the card stays. */
export const EXCLUDE_DOCS = Object.freeze(['TRD-0087', 'TRD-0129']);

/* Owner toggle. true: /library/epstein-black-book/ is left out of this index.
   tools/site-search-build.py uses the same URL skip for the title index. */
export const DROP_LIBRARY_TITLE = true;
export const EXCLUDE_URLS = Object.freeze(DROP_LIBRARY_TITLE ? ['/library/epstein-black-book/'] : []);

const DOC_SET = new Set(EXCLUDE_DOCS);
const URL_SET = new Set(EXCLUDE_URLS);

export function excludedDoc(id) {
  return DOC_SET.has(String(id || '').trim());
}

export function excludedUrl(url) {
  const u = String(url || '');
  if (URL_SET.has(u)) return true;
  for (const id of EXCLUDE_DOCS) if (u.includes(id)) return true;
  return false;
}

/* docs are SCI[F] manifest rows: [id, title, shelf, pages, per, kw]. */
export function selectDocs(docs) {
  const keep = [];
  const skipped = [];
  for (const d of docs || []) {
    const id = Array.isArray(d) ? d[0] : d && d.id;
    if (excludedDoc(id)) skipped.push(id);
    else keep.push(d);
  }
  return { keep, skipped };
}
