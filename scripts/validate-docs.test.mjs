import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  parseFrontmatter,
  validateConcept,
  validateReserved,
  checkLinks,
  indexCoverageWarnings,
} from './validate-docs.mjs';

test('parseFrontmatter reads a simple block', () => {
  const r = parseFrontmatter('---\ntype: Decision\ntitle: X\ntags: [a, b]\n---\nbody');
  assert.equal(r.ok, true);
  assert.equal(r.data.type, 'Decision');
  assert.deepEqual(r.data.tags, ['a', 'b']);
  assert.equal(r.body.trim(), 'body');
});

test('parseFrontmatter fails without an opening fence', () => {
  assert.equal(parseFrontmatter('no frontmatter here').ok, false);
});

test('parseFrontmatter fails on an unterminated block', () => {
  assert.equal(parseFrontmatter('---\ntype: Decision\nbody with no close').ok, false);
});

test('validateConcept flags missing type as a hard error', () => {
  const { errors } = validateConcept('a.md', '---\ntitle: X\n---\nbody');
  assert.equal(errors.length, 1);
  assert.match(errors[0], /type/);
});

test('validateConcept flags an empty type as a hard error', () => {
  const { errors } = validateConcept('a.md', '---\ntype:   \n---\nbody');
  assert.equal(errors.length, 1);
});

test('validateConcept warns (not errors) on missing recommended fields', () => {
  const { errors, warnings } = validateConcept('a.md', '---\ntype: Decision\n---\nbody');
  assert.equal(errors.length, 0);
  assert.ok(warnings.some((w) => /description/.test(w)));
  assert.ok(warnings.some((w) => /timestamp/.test(w)));
});

test('validateConcept warns on a non-ISO timestamp', () => {
  const { warnings } = validateConcept(
    'a.md',
    '---\ntype: Decision\ntitle: X\ndescription: d\ntimestamp: yesterday\n---\nb'
  );
  assert.ok(warnings.some((w) => /ISO/.test(w)));
});

test('validateReserved warns when a non-root index.md carries frontmatter', () => {
  const { warnings } = validateReserved(
    'client-gui/index.md',
    '---\ntype: X\n---\n',
    false
  );
  assert.ok(warnings.some((w) => /frontmatter/.test(w)));
});

test('validateReserved warns on a non-ISO log.md date heading', () => {
  const { warnings } = validateReserved(
    'log.md',
    '# Log\n\n## June 2026\n* Update\n',
    false
  );
  assert.ok(warnings.some((w) => /ISO/.test(w)));
});

test('checkLinks warns on a broken bundle-absolute .md link', () => {
  const warnings = checkLinks('a.md', 'see [x](/missing/x.md)', new Set(['a.md']));
  assert.equal(warnings.length, 1);
});

test('checkLinks passes a resolvable link and ignores directory links', () => {
  const warnings = checkLinks(
    'a.md',
    '[ok](/b.md) and [dir](/client-gui/)',
    new Set(['a.md', 'b.md'])
  );
  assert.equal(warnings.length, 0);
});

test('parseFrontmatter keeps a # inside quotes and strips a trailing comment', () => {
  const r = parseFrontmatter('---\ntitle: "a # b"\ntype: Decision # note\n---\nx');
  assert.equal(r.data.title, 'a # b');
  assert.equal(r.data.type, 'Decision');
});

test('parseFrontmatter reads a multi-line block list', () => {
  const r = parseFrontmatter('---\ntype: Decision\ntags:\n  - a\n  - b\n---\nx');
  assert.deepEqual(r.data.tags, ['a', 'b']);
});

test('parseFrontmatter tolerates CRLF line endings', () => {
  const r = parseFrontmatter('---\r\ntype: Decision\r\n---\r\nbody');
  assert.equal(r.ok, true);
  assert.equal(r.data.type, 'Decision');
});

test('indexCoverageWarnings does not treat focus.md as covered by slide-focus.md', () => {
  const idx = '- [Slide Focus](/d/slide-focus.md)';
  const warnings = indexCoverageWarnings('d/index.md', idx, 'd', [
    'focus.md',
    'slide-focus.md',
  ]);
  assert.ok(warnings.some((w) => /focus\.md/.test(w) && !/slide-focus/.test(w)));
});
