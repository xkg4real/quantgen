"""Recorded metadata/terms review, separate from actual permission or a legal opinion."""
import json
from pathlib import Path


FIELDS=('summary','free_service','paid_service','realtime_delayed','storage','export','derived','attribution','fees')
OUTCOMES={'rights_available','rights_conditional','rights_replace','rights_verify'}


def display_rights():
    record=json.loads(Path(__file__).with_name('display_rights.json').read_text(encoding='utf-8'))
    if record.get('format')!='quantgen.display-rights-review/1' or record.get('publication_authorization') is not False:
        raise ValueError('Unsupported display-rights review')
    for row in record['home']+record['registered_series']:
        if row['outcome'] not in OUTCOMES or row['policy'] not in record['policies']:
            raise ValueError('Invalid rights classification')
    return record


def policy_detail(record,row,ctx):
    policy=record['policies'][row['policy']]
    fields=[(ctx.t('rights_'+key),policy[key][ctx.language]) for key in FIELDS]
    fields.append((ctx.t('source'),'\n'.join(policy['evidence'])))
    return fields
