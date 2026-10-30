"""Recorded evidence, not live readiness. Never traverses research stores.

Generate: python -m tools.status.snapshot --write
Verify:   python -m tools.status.snapshot --check
Only README, recorded QA and calendar MANIFEST are read; no runtime imports.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

import yaml

START = '<!-- research-status:start -->'
END = '<!-- research-status:end -->'
ROOT = Path(__file__).resolve().parents[2]
INPUTS = ('README.md', 'qa/acceptance_results.json', 'core/calendars/data/MANIFEST.yaml')
OUTPUT = 'qa/research_status.json'


class StatusError(ValueError):
    pass


def outside_block(text: str) -> str:
    if text.count(START) != 1 or text.count(END) != 1:
        raise StatusError('README requires exactly one status block')
    a, rest = text.split(START)
    _, b = rest.split(END)
    return a + START + END + b


def collect(root: Path, generated_at: str) -> dict:
    raw = {name: (root / name).read_bytes() for name in INPUTS}
    readme = raw['README.md'].decode('utf-8').replace('\r\n', '\n')
    declared = outside_block(readme)
    if 'gate.package.status = NOT_FROZEN' not in declared:
        raise StatusError('formal gate declaration changed: review source mapping')
    if ('commercial quantitative finance research application' not in declared
            or "As of 2026-10-30, QUANTGEN's commercial launch is an owner-approved decision" not in declared
            or 'personal use only' in declared or 'Do not distribute it as a product.' in declared):
        raise StatusError('distribution declaration changed: owner review required')
    if 'The calendar files are unsigned' in declared:
        raise StatusError('README contradicts current calendar manifest')
    qa = json.loads(raw[INPUTS[1]])
    if not isinstance(qa, list) or not qa:
        raise StatusError('recorded QA must be a nonempty list')
    counts = Counter()
    names = set()
    for row in qa:
        if not isinstance(row, dict) or row.get('status') not in ('PASS', 'FAIL', 'NOT_RUN') or not row.get('test'):
            raise StatusError('unknown or malformed QA result')
        if row['test'] in names:
            raise StatusError('duplicate QA test name')
        names.add(row['test'])
        counts[row['status']] += 1
    manifest = yaml.safe_load(raw[INPUTS[2]])
    if not isinstance(manifest, dict):
        raise StatusError('calendar manifest must be an object')
    rows = manifest.get('rows', [])
    if (not isinstance(rows, list) or not rows
            or any(not isinstance(r, dict) or not isinstance(r.get('file'), str) for r in rows)
            or len({r['file'] for r in rows}) != len(rows)):
        raise StatusError('calendar manifest has missing/duplicate rows')
    signed = bool(manifest.get('signed_off_by') and manifest.get('signed_utc')
                  and all(r.get('signed_off_by') and r.get('md5') for r in rows))
    if not signed:
        raise StatusError('calendar signing metadata missing: review README and manifest')
    # README digest excludes generated block, preventing self-referential hashes.
    raw['README.md'] = declared.encode('utf-8')
    sources = [{'path': p, 'sha256': hashlib.sha256(raw[p]).hexdigest(),
                'normalization': 'LF; generated block excluded' if p == 'README.md' else 'raw bytes'}
               for p in INPUTS]
    return {
        'schema_version': 1, 'generated_at': generated_at,
        'scope': 'recorded repository evidence; not a test run or deployment verdict',
        'sources': sources,
        'code_test': {'status': 'RECORDED', 'counts': {k: counts[k] for k in ('PASS','FAIL','NOT_RUN')},
                      'total': len(qa), 'run_at': None, 'run_commit': None,
                      'note': 'QA source does not record run time/commit. Do not infer them from generation.'},
        'data_readiness': {'status': 'NOT_VERIFIED', 'calendar': {
            'status': 'SIGNED_METADATA', 'version': str(manifest['version']),
            'files': len(rows), 'signed_at': str(manifest['signed_utc']),
            'verification': 'manifest metadata only; individual calendar payloads not verified here'},
            'note': 'Calendar signatures do not supply missing datasets or data licenses.'},
        'formal_gate': {'status': 'NOT_FROZEN', 'evidence': 'README declaration',
                        'verification': 'NOT_INSPECTED', 'note': 'Frozen gate/package artifacts excluded.'},
        'paper_study': {'status': 'NOT_INSPECTED', 'note': 'Actual ledgers and frozen studies excluded.'},
        'distribution_policy': {'status': 'COMMERCIAL', 'evidence': 'README Regulatory note',
                                'public_release': 'OWNER_APPROVED', 'decision_date': '2026-10-30',
                                'note': 'Owner launch decision; not regulatory endorsement or technical readiness.'},
    }


def render(status: dict) -> str:
    c = status['code_test']; cal = status['data_readiness']['calendar']
    return '\n'.join([
        START, '### Recorded repository status', '',
        'Generated from explicit sources; **not a new test run or overall readiness verdict**.', '',
        '| Dimension | Recorded evidence |', '|---|---|',
        f"| Code tests | {c['counts']['PASS']}/{c['total']} PASS; {c['counts']['FAIL']} FAIL; {c['counts']['NOT_RUN']} NOT_RUN. Run time/commit not supplied by source. |",
        f"| Calendars | {cal['files']} signed metadata rows, set {cal['version']}; signed {cal['signed_at']}. Payload verification is separate. |",
        '| Data readiness | NOT_VERIFIED; missing reference data remains a separate blocker. |',
        '| Formal gate | NOT_FROZEN per README; protected package NOT_INSPECTED. |',
        '| Paper studies | NOT_INSPECTED; no ledger or holdout access. |',
        '| Distribution | COMMERCIAL; launch decision OWNER_APPROVED (2026-10-30). |', '',
        'Machine-readable evidence: [qa/research_status.json](qa/research_status.json).',
        'Check: `python -m tools.status.snapshot --check`. Historical dated tables below remain historical.', END])


def verify(root: Path) -> dict:
    status = json.loads((root / OUTPUT).read_text(encoding='utf-8'))
    expected = collect(root, status['generated_at'])
    if status != expected:
        raise StatusError('status snapshot is stale or contradictory; regenerate after reviewing sources')
    readme = (root / 'README.md').read_text(encoding='utf-8')
    block = START + readme.split(START)[1].split(END)[0] + END
    if block != render(expected):
        raise StatusError('README status summary disagrees with source snapshot')
    return expected


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--write', action='store_true')
    mode.add_argument('--check', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.check:
            result = verify(ROOT)
        else:
            result = collect(ROOT, datetime.now(timezone.utc).isoformat())
            old = (ROOT / 'README.md').read_bytes()
            nl = '\r\n' if b'\r\n' in old else '\n'
            text = old.decode('utf-8').replace('\r\n', '\n')
            a, rest = text.split(START); _, b = rest.split(END)
            (ROOT / 'README.md').write_bytes((a + render(result) + b).replace('\n', nl).encode('utf-8'))
            (ROOT / OUTPUT).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
            verify(ROOT)
        print(json.dumps({'status': 'consistent', 'recorded_code_test': result['code_test']}))
        return 0
    except (ValueError, KeyError, OSError, TypeError) as exc:
        print(f'Status check failed: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
