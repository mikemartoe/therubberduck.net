// Search proof of concept, SCIF room: build a Pagefind keyword index with one
// record per PDF page, so every word inside every PDF is searchable on phones
// (Pagefind loads only the small index chunks a query needs).
// Usage: node build-scif-pagefind.mjs <records.jsonl> <outDir>
import * as pagefind from 'pagefind';
import fs from 'node:fs';
import readline from 'node:readline';
const [src, out] = process.argv.slice(2);
const { index } = await pagefind.createIndex({ forceLanguage: 'en' });
let n = 0;
for await (const line of readline.createInterface({ input: fs.createReadStream(src) })) {
  if (!line) continue;
  const r = JSON.parse(line);
  const target = r.pdf ? `${r.pdf}#page=${r.page}` : `${r.url}#page=${r.page}`;
  await index.addCustomRecord({
    url: target, content: r.text, language: 'en',
    meta: { title: `${r.title} · p. ${r.page}`, doc: r.title, room: r.url, id: r.id, page: String(r.page) },
    filters: { shelf: [r.shelf || 'Other'] },
  });
  if (++n % 2000 === 0) console.log(n);
}
const { errors } = await index.writeFiles({ outputPath: out });
console.log(n, 'records', errors.length ? errors : 'ok');
await pagefind.close();
