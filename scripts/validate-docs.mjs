#!/usr/bin/env node
// Report-only OKF v0.1 conformance validator for the docs/ bundle.
// ALWAYS exits 0 (advisory, never blocks — see docs/conventions/documentation.md).
// Hard ERRORS: every non-reserved .md under docs/ (excluding docs/superpowers/) has a
// parseable frontmatter block with a non-empty `type`. Everything else is a soft WARNING.

import { readdir, readFile } from 'node:fs/promises';
import { join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

export const reservedFiles = new Set(['index.md', 'log.md']);
export const recommendedFields = ['title', 'description', 'timestamp'];
const excludedTopLevelDirs = new Set(['superpowers']);
const isoRe = /^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2})?(\.\d+)?(Z|[+-]\d{2}:\d{2})?)?$/;
const isoDateRe = /^\d{4}-\d{2}-\d{2}$/;
const linkRe = /\]\((\/[^)\s#]+)(#[^)\s]*)?\)/g;

function stripInlineComment(value) {
  let inSingle = false;
  let inDouble = false;
  for (let i = 0; i < value.length; i += 1) {
    const c = value[i];
    if (c === "'" && !inDouble) inSingle = !inSingle;
    else if (c === '"' && !inSingle) inDouble = !inDouble;
    else if (
      c === '#' &&
      !inSingle &&
      !inDouble &&
      (i === 0 || /\s/.test(value[i - 1]))
    ) {
      return value.slice(0, i);
    }
  }
  return value;
}

function unquote(value) {
  return value.replace(/^['"]|['"]$/g, '');
}

export function parseFrontmatter(text) {
  const lines = text.split(/\r?\n/);
  if (lines[0].trim() !== '---') {
    return { ok: false, reason: 'no opening --- frontmatter fence' };
  }
  let end = -1;
  for (let i = 1; i < lines.length; i += 1) {
    if (lines[i].trim() === '---') {
      end = i;
      break;
    }
  }
  if (end === -1) {
    return { ok: false, reason: 'unterminated frontmatter (no closing ---)' };
  }
  const data = {};
  let currentListKey = null;
  for (let i = 1; i < end; i += 1) {
    const raw = lines[i];
    const trimmed = raw.trim();
    if (trimmed === '' || trimmed.startsWith('#')) {
      currentListKey = null;
      continue;
    }
    if (currentListKey && /^\s*-\s+/.test(raw)) {
      data[currentListKey].push(
        unquote(stripInlineComment(raw.replace(/^\s*-\s+/, '')).trim())
      );
      continue;
    }
    const m = raw.match(/^([A-Za-z0-9_]+):\s*(.*)$/);
    if (!m) {
      return { ok: false, reason: `unparseable frontmatter line: "${raw}"` };
    }
    const key = m[1];
    const value = stripInlineComment(m[2]).trim();
    if (value === '') {
      data[key] = [];
      currentListKey = key;
      continue;
    }
    currentListKey = null;
    if (value.startsWith('[') && value.endsWith(']')) {
      data[key] = value
        .slice(1, -1)
        .split(',')
        .map((s) => unquote(s.trim()))
        .filter((s) => s !== '');
    } else {
      data[key] = unquote(value);
    }
  }
  return { ok: true, data, body: lines.slice(end + 1).join('\n') };
}

export function validateConcept(relPath, text) {
  const errors = [];
  const warnings = [];
  const fm = parseFrontmatter(text);
  if (!fm.ok) {
    errors.push(`${relPath}: ${fm.reason}`);
    return { errors, warnings };
  }
  const type = fm.data.type;
  if (typeof type !== 'string' || type.trim() === '') {
    errors.push(`${relPath}: missing or empty required \`type\` field`);
  }
  for (const field of recommendedFields) {
    if (!(field in fm.data) || String(fm.data[field]).trim() === '') {
      warnings.push(`${relPath}: missing recommended field \`${field}\``);
    }
  }
  if (fm.data.timestamp && !isoRe.test(String(fm.data.timestamp))) {
    warnings.push(`${relPath}: \`timestamp\` "${fm.data.timestamp}" is not ISO 8601`);
  }
  if (fm.data.status === 'superseded' && !fm.data.superseded_by) {
    warnings.push(`${relPath}: status superseded but no \`superseded_by\``);
  }
  return { errors, warnings };
}

export function validateReserved(relPath, text, isRoot) {
  const errors = [];
  const warnings = [];
  const base = relPath.split('/').pop();
  const hasFm = text.split('\n')[0].trim() === '---';
  if (base === 'index.md') {
    if (hasFm && !isRoot) {
      warnings.push(`${relPath}: non-root index.md must not carry frontmatter (OKF §6)`);
    }
    if (isRoot && hasFm) {
      const fm = parseFrontmatter(text);
      if (fm.ok && fm.data.okf_version !== '0.1') {
        warnings.push(`${relPath}: root index.md should declare okf_version: "0.1"`);
      }
    }
  }
  if (base === 'log.md') {
    for (const h of text.split('\n').filter((l) => /^##\s+/.test(l))) {
      const d = h.replace(/^##\s+/, '').trim();
      if (!isoDateRe.test(d)) {
        warnings.push(`${relPath}: log.md date heading "${d}" is not ISO YYYY-MM-DD`);
      }
    }
  }
  return { errors, warnings };
}

export function checkLinks(relPath, text, allRelPaths) {
  const warnings = [];
  linkRe.lastIndex = 0;
  let m;
  while ((m = linkRe.exec(text)) !== null) {
    const target = m[1].replace(/^\//, '');
    if (target.endsWith('.md') && !allRelPaths.has(target)) {
      warnings.push(`${relPath}: broken internal link -> /${target}`);
    }
  }
  return warnings;
}

function toPosixRel(rootDir, file) {
  return relative(rootDir, file).split(sep).join('/');
}

function posixDir(rel) {
  const idx = rel.lastIndexOf('/');
  return idx === -1 ? '' : rel.slice(0, idx);
}

export async function walkDocs(rootDir) {
  const out = [];
  async function walk(dir) {
    const entries = await readdir(dir, { withFileTypes: true });
    for (const e of entries) {
      const full = join(dir, e.name);
      if (e.isDirectory()) {
        if (excludedTopLevelDirs.has(toPosixRel(rootDir, full))) continue;
        await walk(full);
      } else if (e.isFile() && e.name.endsWith('.md')) {
        out.push(full);
      }
    }
  }
  await walk(rootDir);
  return out;
}

/** Warnings for concepts in `concepts` not linked (by exact basename) from an index's text. */
export function indexCoverageWarnings(indexRel, indexText, dir, concepts) {
  const warnings = [];
  const linkedBasenames = new Set();
  linkRe.lastIndex = 0;
  let m;
  while ((m = linkRe.exec(indexText)) !== null) {
    const target = m[1].replace(/^\//, '');
    if (target.endsWith('.md')) {
      linkedBasenames.add(target.split('/').pop());
    }
  }
  for (const base of concepts) {
    if (!linkedBasenames.has(base)) {
      warnings.push(
        `${indexRel}: missing index entry for ${dir ? `${dir}/` : ''}${base}`
      );
    }
  }
  return warnings;
}

async function checkIndexCoverage(rootDir, conceptDirs) {
  const warnings = [];
  for (const [dir, concepts] of conceptDirs) {
    const indexRel = dir ? `${dir}/index.md` : 'index.md';
    let indexText;
    try {
      indexText = await readFile(join(rootDir, indexRel), 'utf8');
    } catch {
      warnings.push(`${dir || '(root)'}: directory has concepts but no index.md`);
      continue;
    }
    warnings.push(...indexCoverageWarnings(indexRel, indexText, dir, concepts));
  }
  return warnings;
}

export async function validateBundle(rootDir) {
  const files = await walkDocs(rootDir);
  const errors = [];
  const warnings = [];
  const allRelPaths = new Set(files.map((f) => toPosixRel(rootDir, f)));
  const conceptDirs = new Map();
  for (const file of files) {
    const rel = toPosixRel(rootDir, file);
    const base = rel.split('/').pop();
    const text = await readFile(file, 'utf8');
    // Links are checked everywhere — index.md is the navigation backbone.
    warnings.push(...checkLinks(rel, text, allRelPaths));
    if (reservedFiles.has(base)) {
      const r = validateReserved(rel, text, rel === 'index.md');
      errors.push(...r.errors);
      warnings.push(...r.warnings);
    } else {
      const r = validateConcept(rel, text);
      errors.push(...r.errors);
      warnings.push(...r.warnings);
      const dir = posixDir(rel);
      if (!conceptDirs.has(dir)) conceptDirs.set(dir, new Set());
      conceptDirs.get(dir).add(base);
    }
  }
  warnings.push(...(await checkIndexCoverage(rootDir, conceptDirs)));
  return { errors, warnings };
}

export function formatReport({ errors, warnings }) {
  if (errors.length === 0 && warnings.length === 0) {
    return 'docs:validate — OKF bundle conformant; no warnings.';
  }
  const lines = [];
  if (errors.length > 0) {
    lines.push(`ERRORS — OKF §9 conformance (${errors.length}):`);
    for (const e of errors) lines.push(`  ${e}`);
    lines.push('');
  }
  if (warnings.length > 0) {
    lines.push(`Warnings — recommended/soft (${warnings.length}):`);
    for (const w of warnings) lines.push(`  ${w}`);
    lines.push('');
  }
  lines.push(
    `${errors.length} hard failure(s), ${warnings.length} warning(s). (Advisory — exit 0, never blocks.)`
  );
  return lines.join('\n');
}

async function main() {
  const root = process.argv[2] || 'docs';
  const result = await validateBundle(root);
  console.log(formatReport(result));
  process.exit(0);
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  main();
}
