"""Offline, synthetic consistency checks; never reads studies of record."""
import json
from pathlib import Path
import tempfile
import unittest

from tools.status.snapshot import START, END, StatusError, collect, render, verify


class StatusSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'qa').mkdir()
        (self.root / 'core/calendars/data').mkdir(parents=True)
        (self.root / 'README.md').write_text(
            'personal use only. Do not distribute it as a product.\n'
            'gate.package.status = NOT_FROZEN\n' + START + END, encoding='utf-8')
        self.qa = self.root / 'qa/acceptance_results.json'
        self.qa.write_text(json.dumps([{'test': 'ok', 'status': 'PASS'},
                                       {'test': 'missing', 'status': 'NOT_RUN'}]), encoding='utf-8')
        (self.root / 'core/calendars/data/MANIFEST.yaml').write_text(
            "version: 1.0.0\nsigned_off_by: fixture\nsigned_utc: '2026-10-29T00:00:00Z'\n"
            'rows:\n- file: example.yaml\n  signed_off_by: fixture\n  md5: fixture-only\n', encoding='utf-8')
        self.refresh()

    def refresh(self):
        s = collect(self.root, '2026-10-29T01:00:00+00:00')
        p = self.root / 'README.md'; t = p.read_text(encoding='utf-8')
        p.write_text(t.split(START)[0] + render(s), encoding='utf-8')
        (self.root / 'qa/research_status.json').write_text(json.dumps(s), encoding='utf-8')
        return s

    def test_missing_calendar_payload_is_not_claimed_verified(self):
        s = verify(self.root)
        self.assertEqual(s['data_readiness']['status'], 'NOT_VERIFIED')
        self.assertEqual(s['formal_gate']['verification'], 'NOT_INSPECTED')
        self.assertEqual(s['paper_study']['status'], 'NOT_INSPECTED')
        self.assertIsNone(s['code_test']['run_at'])
        self.assertEqual(s['code_test']['counts']['NOT_RUN'], 1)
        self.assertNotIn('ready', s)

    def test_source_change_invalidates_old_snapshot(self):
        self.qa.write_text(json.dumps([{'test': 'ok', 'status': 'FAIL'}]), encoding='utf-8')
        with self.assertRaises(StatusError): verify(self.root)

    def test_summary_cannot_promote_notrun_or_gate(self):
        p = self.root / 'README.md'; t = p.read_text(encoding='utf-8')
        for old, new in [('1/2 PASS', '2/2 PASS'), ('NOT_FROZEN per README', 'PASS per README')]:
            p.write_text(t.replace(old, new), encoding='utf-8')
            with self.assertRaises(StatusError): verify(self.root)

    def test_policy_and_calendar_contradictions_refuse(self):
        p = self.root / 'README.md'; t = p.read_text(encoding='utf-8')
        for changed in [t + '\nThe calendar files are unsigned',
                        t.replace('Do not distribute it as a product.', 'Distribution permitted.')]:
            p.write_text(changed, encoding='utf-8')
            with self.assertRaises(StatusError): self.refresh()

    def test_duplicate_unknown_and_empty_qa_refuse(self):
        for rows in [[], ['invalid row'], [{'test':'x','status':'READY'}],
                     [{'test':'x','status':'PASS'}, {'test':'x','status':'PASS'}]]:
            self.qa.write_text(json.dumps(rows), encoding='utf-8')
            with self.assertRaises(StatusError): self.refresh()

    def test_missing_source_does_not_become_empty_success(self):
        self.qa.unlink()
        with self.assertRaises(OSError): verify(self.root)

    def test_malformed_calendar_shapes_refuse(self):
        p = self.root / 'core/calendars/data/MANIFEST.yaml'
        for value in ('null', '[]', 'rows: broken', 'rows: [null]', 'rows: [{}]'):
            p.write_text(value, encoding='utf-8')
            with self.assertRaises(StatusError): self.refresh()

    def test_generation_time_is_not_observation_time(self):
        s = collect(self.root, '2099-01-01T00:00:00Z')
        self.assertIsNone(s['code_test']['run_at'])
        self.assertEqual(s['data_readiness']['calendar']['signed_at'], '2026-10-29T00:00:00Z')

    def test_tampered_payload_even_with_unchanged_sources_refuses(self):
        p = self.root / 'qa/research_status.json'; s = json.loads(p.read_text(encoding='utf-8'))
        s['distribution_policy']['public_release'] = 'APPROVED'
        p.write_text(json.dumps(s), encoding='utf-8')
        with self.assertRaises(StatusError): verify(self.root)


if __name__ == '__main__':
    unittest.main()
