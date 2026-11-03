"""Inventory explicit metadata only. Does not open market stores or trial ledgers."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

import yaml

ROOT = Path(__file__).resolve().parents[2]


def collect(root=ROOT):
    registry_bytes = (root / 'data/macro/series_registry.yaml').read_bytes()
    qa_bytes = (root / 'qa/acceptance_results.json').read_bytes()
    registry = yaml.safe_load(registry_bytes)
    tests = json.loads(qa_bytes)
    items = []
    for name, entry in sorted(registry['series'].items()):
        items.append(dict(series_id=name, source=entry.get('source'), alternatives=entry.get('sources', []),
            frequency=entry.get('frequency'), unit=entry.get('unit', entry.get('contract', {}).get('unit')),
            timezone=entry.get('obs_date_tz'), calendar=entry.get('obs_calendar'), schedule=entry.get('schedule'),
            production_channel=entry.get('production_channel'), history_channel=entry.get('history_channel'),
            adjustment_basis=entry.get('adjustment_basis'), inventory_scope='metadata_only',
            acquisition_status='NOT_VERIFIED', license_status='NOT_VERIFIED', parity_status='NOT_RUN'))
    blockers=[]; files={}
    for row in tests:
        if row['status'] != 'NOT_RUN': continue
        reason = row.get('reason') or row.get('detail') or ''
        category = reason.split(':',1)[0] if ':' in reason else 'UNCLASSIFIED'
        if category not in {'OWNER','REFDATA','ENV','NETWORK','DEPENDENCY','FROZEN'}: category='OTHER'
        required=sorted(set(re.findall(r'[A-Za-z0-9_][A-Za-z0-9_.-]*\.csv',reason)))
        blockers.append(dict(test=row['test'], recorded_status='NOT_RUN', category=category,
            required_files=required, current_status='NOT_RETESTED', reason=reason))
        for filename in required: files.setdefault(filename,[]).append(row['test'])
    return dict(schema='quantgen.data-readiness/1', registry_version=registry['version'],
        scope='Inventory, not acquisition/license certification; historical QA is not a current run',
        inputs_sha256={'registry':hashlib.sha256(registry_bytes).hexdigest(),'recorded_qa':hashlib.sha256(qa_bytes).hexdigest()},
        series=items, recorded_blockers=blockers, blocker_counts=dict(Counter(r['category'] for r in blockers)),
        acquisition_queue=[dict(filename=k, affected_tests=v, status='NEEDS_SOURCE_AND_RIGHTS',
                               priority='P0' if k.startswith(('krx_','fred_','FRED_')) else 'P1') for k,v in sorted(files.items())])


if __name__ == '__main__':
    print(json.dumps(collect(),ensure_ascii=False,indent=2))
