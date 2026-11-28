/* The exclusion list has to hold before any index is written. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { DROP_LIBRARY_TITLE, EXCLUDE_DOCS, EXCLUDE_URLS, excludedDoc, excludedUrl, selectDocs } from './exclude.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const docs = [
  ['TRD-0087', 'skipped', 'EPSTEIN', 92, 0, ''],
  ['TRD-0129', 'skipped', '404', 1, 0, ''],
  ['TRD-0001', 'kept', 'PSYOP', 10, 0, ''],
];
const { keep, skipped } = selectDocs(docs);
assert.deepEqual(skipped, ['TRD-0087', 'TRD-0129']);
assert.deepEqual(keep.map((d) => d[0]), ['TRD-0001']);
assert.equal(DROP_LIBRARY_TITLE, true);
assert.equal(excludedUrl('/library/epstein-black-book/'), true);
assert.equal(excludedUrl('/pdfs.html?open=TRD-0087&p=1'), true);
assert.equal(excludedUrl('/pdfs.html?open=TRD-0129&p=1'), true);
assert.equal(excludedUrl('/pdfs.html?open=TRD-0001&p=1'), false);
assert.ok(EXCLUDE_DOCS.includes('TRD-0087') && EXCLUDE_DOCS.includes('TRD-0129'));
assert.ok(EXCLUDE_URLS.includes('/library/epstein-black-book/'));

const build = fs.readFileSync(path.join(root, 'tools/search/build-unified.mjs'), 'utf8');
assert.ok(build.includes('https://scif-search.therubberduck.net/scif-search/2beb375c5b/'));
const extract = fs.readFileSync(path.join(root, 'tools/scif-text-extract.py'), 'utf8');
assert.ok(extract.includes('def needs_ocr'));
assert.ok(!extract.includes('n < 25 or (n < 150 and p.get_images())'));
console.log('exclude.test.mjs: TRD-0087 and TRD-0129 dropped; library title toggle is on');
