import hashlib
import unittest
from core.research.runs import canonical
from core.research.intake import validate_data_receipt, compare_observations
from tools.status.data_readiness import collect


class DataReadinessTests(unittest.TestCase):
    def test_inventory_preserves_not_run_and_does_not_infer_acquisition(self):
        report=collect()
        self.assertEqual(len(report['series']),73)
        self.assertEqual(len(report['recorded_blockers']),121)
        self.assertTrue(all(r['acquisition_status']=='NOT_VERIFIED' for r in report['series']))
        self.assertTrue(all(r['current_status']=='NOT_RETESTED' for r in report['recorded_blockers']))

    def test_receipt_integrity_does_not_certify_license(self):
        rows=[{'date':'2026-10-28','value':4.1}]
        meta=dict(series_id='TEST',provider='TEST',retrieved_at='2026-10-29T00:00:00+00:00',vintage='test',
                  adjustment='none',timezone='UTC',calendar='TEST',unit='pct',license_reference='fixture-only',
                  license_scope='PERSONAL_RESEARCH',sha256=hashlib.sha256(canonical(rows).encode()).hexdigest())
        self.assertEqual(validate_data_receipt(meta,rows)['license_authenticity'],'NOT_VERIFIED')
        rows[0]['value']=4.2
        with self.assertRaises(ValueError): validate_data_receipt(meta,rows)

    def test_parity_missing_dates_not_silent_inner_join(self):
        a=[{'date':'2026-10-28','value':4.1}];b=a+[{'date':'2026-10-29','value':4.2}]
        self.assertEqual(compare_observations(a,b,tolerance=.01)['status'],'INCOMPLETE')
        self.assertEqual(compare_observations(a,[{'date':'2026-10-28','value':4.3}],tolerance=.01)['status'],'MISMATCH')
        self.assertEqual(compare_observations(a,a,tolerance=0)['status'],'MATCH_WITHIN_TOLERANCE')


if __name__=='__main__': unittest.main()
