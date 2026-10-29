"""Validate supplied data evidence in memory. Never loads or approves a store."""
from datetime import date, datetime
import hashlib
import math

from .runs import canonical

REQUIRED = {'series_id','provider','retrieved_at','vintage','adjustment','timezone','calendar',
            'unit','license_reference','license_scope','sha256'}


def validate_data_receipt(metadata, rows):
    if set(metadata) != REQUIRED or any(not isinstance(v,str) or not v.strip() for v in metadata.values()):
        raise ValueError('Incomplete data receipt')
    if metadata['license_scope'] not in {'PERSONAL_RESEARCH','PUBLIC_REDISTRIBUTION'}:
        raise ValueError('Unknown license scope')
    if datetime.fromisoformat(metadata['retrieved_at']).tzinfo is None:
        raise ValueError('Retrieval timestamp requires timezone')
    if not rows: raise ValueError('No observations')
    dates=[]
    for row in rows:
        if set(row) != {'date','value'}: raise ValueError('Unexpected row fields')
        date.fromisoformat(row['date']); dates.append(row['date'])
        if isinstance(row['value'],bool) or not isinstance(row['value'],(int,float)) or not math.isfinite(row['value']):
            raise ValueError('Non-finite observation')
    if dates != sorted(set(dates)): raise ValueError('Duplicate/unordered observations')
    actual=hashlib.sha256(canonical(rows).encode()).hexdigest()
    if metadata['sha256'] != actual: raise ValueError('Data receipt hash mismatch')
    return {'status':'STRUCTURE_VERIFIED','observations':len(rows),'sha256':actual,
            'license_authenticity':'NOT_VERIFIED','provider_parity':'NOT_RUN','gate_verdict':'NOT_RUN'}


def compare_observations(primary, independent, *, tolerance):
    """Compare exact dates only; never silently truncate or fill a missing date."""
    if not math.isfinite(tolerance) or tolerance < 0: raise ValueError('Invalid tolerance')
    def index(rows):
        result={}
        for r in rows:
            if r['date'] in result or not math.isfinite(r['value']): raise ValueError('Invalid comparison rows')
            result[r['date']]=r['value']
        return result
    a,b=index(primary),index(independent)
    if not a or set(a)!=set(b):
        return {'status':'INCOMPLETE','missing_primary':sorted(set(b)-set(a)), 'missing_independent':sorted(set(a)-set(b))}
    maximum=max(abs(a[d]-b[d]) for d in a)
    return {'status':'MATCH_WITHIN_TOLERANCE' if maximum<=tolerance else 'MISMATCH','max_absolute_difference':maximum,'observations':len(a)}
