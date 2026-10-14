/* util/csv.js — a tolerant, RFC-4180-ish CSV parser.

   Handles: quoted fields, embedded commas, embedded quotes ("" escape),
   embedded newlines inside quotes, CRLF or LF line endings, a trailing
   newline, and blank lines (skipped). It does NOT try to be a full RFC
   validator — it is deliberately forgiving so a slightly-off industrial
   export still loads, while still reporting structural problems.

   parseCSV(text) -> { header: string[], rows: string[][], errors: string[] } */

export function parseCSV(text) {
  const errors = [];
  if (typeof text !== 'string' || text.length === 0) {
    return { header: [], rows: [], errors: ['The file is empty.'] };
  }
  // Strip a UTF-8 BOM if present.
  if (text.charCodeAt(0) === 0xfeff) text = text.slice(1);

  const records = [];
  let field = '';
  let record = [];
  let inQuotes = false;
  let sawAny = false;

  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQuotes) {
      if (c === '"') {
        if (text[i + 1] === '"') { field += '"'; i++; }
        else inQuotes = false;
      } else field += c;
      continue;
    }
    if (c === '"') { inQuotes = true; sawAny = true; continue; }
    if (c === ',') { record.push(field); field = ''; sawAny = true; continue; }
    if (c === '\r') { continue; } // swallow CR; the LF ends the line
    if (c === '\n') {
      record.push(field); field = '';
      // Skip fully-blank lines.
      if (!(record.length === 1 && record[0] === '')) records.push(record);
      record = []; sawAny = false;
      continue;
    }
    field += c; sawAny = true;
  }
  // Flush the last field/record if the file did not end with a newline.
  if (inQuotes) errors.push('A quoted value was never closed; the last row may be misaligned.');
  if (sawAny || field !== '' || record.length) {
    record.push(field);
    if (!(record.length === 1 && record[0] === '')) records.push(record);
  }

  if (records.length === 0) return { header: [], rows: [], errors: ['The file has no rows.'] };

  const header = records[0].map((h) => h.trim());
  const rows = records.slice(1);

  // Report ragged rows but keep them (padded/truncated) so the parse doesn't fail.
  const width = header.length;
  let ragged = 0;
  const norm = rows.map((r) => {
    if (r.length !== width) {
      ragged++;
      if (r.length < width) return r.concat(Array(width - r.length).fill(''));
      return r.slice(0, width);
    }
    return r;
  });
  if (ragged > 0) errors.push(`${ragged} row(s) did not match the ${width}-column header and were aligned to it.`);

  return { header, rows: norm, errors };
}

/* Turn header + rows into an array of {colName: value} objects. */
export function toObjects(header, rows) {
  return rows.map((r) => {
    const o = {};
    for (let i = 0; i < header.length; i++) o[header[i]] = r[i];
    return o;
  });
}

/* Coerce a raw string cell to a number, or null if it isn't numeric.
   Treats '', 'NA', 'NaN', 'null', 'none' (any case) as missing. */
export function toNumber(v) {
  if (v == null) return null;
  const s = String(v).trim();
  if (s === '' || /^(na|nan|null|none|n\/a)$/i.test(s)) return null;
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
}

export function isMissing(v) {
  if (v == null) return true;
  const s = String(v).trim();
  return s === '' || /^(na|nan|null|none|n\/a)$/i.test(s);
}
