"""Synthetic offline mutation tests for document/source review; no live user stores."""
from copy import deepcopy
import json
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.compliance.check import (BASELINE, DOC_DIR, HEADINGS, KNOWN_FINDINGS,
    OPERATOR_FIELDS, PROFILE, REGISTRY, REQUIREMENTS, CheckError, check, collect,
    dependencies, main, profile_blockers, record_publication, refresh, source_inventory, write_reports)


class ComplianceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / DOC_DIR).mkdir(parents=True)
        (self.root / 'ui').mkdir()
        (self.root / 'core').mkdir()
        (self.root / 'assets').mkdir()
        self.put('pyproject.toml', '[project]\nname="fixture"\nversion="0"\ndependencies=["flet==0.85.2"]\n')
        self.put('ui/example.py', 'VALUE = 1\n')
        self.put('core/example.py', 'VALUE = 1\n')
        self.put('assets/example.svg', '<svg>fixture</svg>\n')
        self.rows = [{'id': i, 'path': f'{DOC_DIR}/{i:02d}-fixture.md', 'title': f'문서 {i}',
                      'source_patterns': ['ui/**'] if i == 1 else ['core/**']} for i in range(1, 21)]
        self.write_json(REGISTRY, {'schema_version': 1, 'documents': self.rows})
        for row in self.rows:
            self.put(row['path'], f"# 문서 양식\n\n문서 ID: QG-C{row['id']:02d} · 버전: 1.0 · 검토일: 2026-01-01 · 상태: review-required\n\n" + '\n\n'.join(
                f'## {heading}\n\n' + ('| 요청 번호 | 검토자 | 근거 |\n|---|---|---|\n| 수동 입력 | 담당자 입력 | 증빙 링크 |' if heading == '양식' else
                '이 절은 현재 소스에서 확인한 내용과 검토할 실행 기준을 구체적으로 기록합니다.') for heading in HEADINGS) + '\n')
        item = {'status': 'unverified', 'evidence': None, 'reviewed_by': None, 'reviewed_on': None, 'rationale': None}
        self.profile = {'schema_version': 1, 'jurisdiction': 'KR', 'operator': {key: None for key in OPERATOR_FIELDS},
                        'requirements': {key: deepcopy(item) for key in REQUIREMENTS},
                        'known_findings': {key: deepcopy(item) for key in KNOWN_FINDINGS}}
        self.write_json(PROFILE, self.profile)
        self.refresh()

    def put(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def write_json(self, name, value):
        self.put(name, json.dumps(value, ensure_ascii=False, indent=2) + '\n')

    def refresh(self, selected=None):
        return refresh(self.root, 'fixture-reviewer', 'Reviewed synthetic source and policy changes.', selected)

    def stale(self):
        return {x['id'] for x in check(self.root)['documents_needing_review']}

    def test_consistency_does_not_claim_publication_approval(self):
        result = check(self.root)
        self.assertEqual(result['consistency_status'], 'PASS')
        self.assertEqual(result['publication_status'], 'BLOCKED')
        self.assertEqual(result['document_count'], 20)
        self.assertGreater(len(result['publication_blockers']), 20)
        self.refresh()
        self.assertEqual(check(self.root)['publication_status'], 'BLOCKED')

    def test_mapped_source_modification_targets_document(self):
        self.put('ui/example.py', 'VALUE = 2\n')
        self.assertEqual(self.stale(), {1})
        self.assertEqual(check(self.root)['changed_sources'][0]['change'], 'modified')

    def test_unmapped_new_source_requires_all_documents(self):
        self.put('new_feature/service.py', 'NEW = True\n')
        self.assertEqual(self.stale(), set(range(1, 21)))
        changed = check(self.root)['changed_sources']
        self.assertEqual(changed[0]['change'], 'added')
        self.assertEqual(changed[0]['documents'], list(range(1, 21)))

    def test_new_source_inside_broad_core_mapping_still_requires_all(self):
        self.put('core/privacy_service.py', 'NEW = True\n')
        self.assertEqual(self.stale(), set(range(1, 21)))
        self.assertEqual(check(self.root)['changed_sources'][0]['documents'], list(range(1, 21)))

    def test_code_packages_named_accounts_cache_and_research_cannot_hide_source(self):
        names = ('core/accounts/delete.py', 'core/credentials/tokens.py', 'core/cache/store.py',
                 'core/logs/export.py', 'core/research/connections.py', 'core/frozen/delete.py', 'core/holdout/schema.py')
        for name in names:
            self.put(name, 'CODE = True\n')
        self.assertTrue(set(names).issubset(source_inventory(self.root)))
        self.assertEqual(self.stale(), set(range(1, 21)))

    def test_new_javascript_and_composer_manifests_require_review(self):
        for name in ('package.json', 'package-lock.json', 'web/package.json', 'composer.json', 'deno.json'):
            self.put(name, '{"dependencies":{"analytics-sdk":"1.0.0"}}\n')
            self.assertIn(name, source_inventory(self.root))
            self.assertEqual(self.stale(), set(range(1, 21)))
            self.refresh()

    def test_deleted_and_renamed_sources_are_detected(self):
        path = self.root / 'ui/example.py'
        path.unlink()
        self.assertEqual(self.stale(), set(range(1, 21)))
        self.assertEqual(check(self.root)['changed_sources'][0]['change'], 'deleted')
        self.put('ui/renamed.py', 'VALUE = 1\n')
        self.assertEqual({x['change'] for x in check(self.root)['changed_sources']}, {'deleted', 'added'})

    def test_broken_local_links_block_structure_but_template_links_are_allowed(self):
        name = self.rows[0]['path']
        original = (self.root / name).read_text(encoding='utf-8')
        self.put(name, original + '\n[없는 문서](99-missing.md)\n')
        self.assertEqual(check(self.root)['consistency_status'], 'FAIL')
        with self.assertRaises(CheckError):
            self.refresh()
        self.put(name, original + '\n[양식 자리]({{url}})\n[현재 문서](01-fixture.md)\n')
        self.refresh()
        self.assertEqual(check(self.root)['consistency_status'], 'PASS')

    def test_dependency_and_asset_changes_require_review(self):
        self.put('pyproject.toml', '[project]\nname="fixture"\nversion="0"\ndependencies=["flet==99"]\n')
        self.assertEqual(self.stale(), set(range(1, 21)))
        self.refresh()
        self.put('assets/example.svg', '<svg>changed rights</svg>\n')
        self.assertEqual(self.stale(), set(range(1, 21)))

    def test_policy_edit_invalidates_its_own_review(self):
        name = self.rows[12]['path']
        self.put(name, (self.root / name).read_text(encoding='utf-8') + '\n정책 본문 변경\n')
        self.assertEqual(self.stale(), {13})

    def test_supplemental_evidence_and_pipeline_are_monitored(self):
        for name in ('FACTS', 'SOURCES', 'RELEASE_GAPS', 'PIPELINE', 'README'):
            self.put(f'{DOC_DIR}/{name}.md', f'# {name}\n변경 증거\n')
            self.assertEqual(self.stale(), set(range(1, 21)))
            self.refresh()

    def test_metadata_mismatch_and_future_date_are_structure_errors(self):
        name = self.rows[0]['path']
        original = (self.root / name).read_text(encoding='utf-8')
        for bad in (original.replace('QG-C01', 'QG-C02'), original.replace('2026-01-01', '2099-01-01'),
                    original.replace('상태: review-required', '상태: certified')):
            self.put(name, bad)
            self.assertEqual(check(self.root)['consistency_status'], 'FAIL')

    def test_publication_approval_cannot_be_accidentally_read_from_form(self):
        name = self.rows[0]['path']
        original = (self.root / name).read_text(encoding='utf-8')
        self.put(name, original.replace('상태: review-required', '상태: approved')
                 + '\n승인자: form example reviewer\n승인 근거: form example only\n')
        self.refresh()
        self.assertTrue(any('document 1: publication status requires' in x for x in check(self.root)['publication_blockers']))

    def test_partial_refresh_cannot_hide_other_stale_documents(self):
        self.put('unknown.py', 'VALUE = 1\n')
        self.refresh([1])
        result = check(self.root)
        self.assertEqual(self.stale(), set(range(2, 21)))
        self.assertTrue(result['changed_sources'])
        self.refresh(list(range(2, 21)))
        self.assertEqual(check(self.root)['consistency_status'], 'PASS')

    def test_missing_empty_and_duplicate_document_sections_fail(self):
        name = self.rows[0]['path']
        original = (self.root / name).read_text(encoding='utf-8')
        for bad in (original.replace('## 양식', '## 없음'), original + '\n## 양식\n다시\n', '# 문서\n'):
            self.put(name, bad)
            self.assertEqual(check(self.root)['consistency_status'], 'FAIL')
            with self.assertRaises(CheckError):
                self.refresh()
        (self.root / name).unlink()
        self.assertEqual(check(self.root)['consistency_status'], 'FAIL')

    def test_extra_numbered_document_is_not_silently_ignored(self):
        self.put(f'{DOC_DIR}/21-extra.md', '# Extra\n')
        self.assertEqual(check(self.root)['consistency_status'], 'FAIL')

    def test_registry_duplicate_and_traversal_are_rejected(self):
        rows = deepcopy(self.rows)
        rows[0]['id'] = 2
        self.write_json(REGISTRY, {'schema_version': 1, 'documents': rows})
        with self.assertRaises(CheckError):
            collect(self.root)
        rows = deepcopy(self.rows)
        rows[0]['path'] = '../../.env'
        self.write_json(REGISTRY, {'schema_version': 1, 'documents': rows})
        with self.assertRaises(CheckError):
            collect(self.root)

    def test_secret_private_and_user_data_payloads_are_not_opened(self):
        # Invalid UTF-8 makes accidental content parsing fail; inventory must ignore these.
        for name in ('.env', '.env.backup', '.aws/config.py', 'paper_live/user.py', 'research_notes/secret.py',
                     'data/accounts/user.json', 'data/private.json', 'core/cache/account.json', 'core/tokens/credentials.ini'):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'PRIVATE\xff\x00')
        result = check(self.root)
        self.assertEqual(result['consistency_status'], 'PASS')
        self.assertNotIn('PRIVATE', json.dumps(result))
        self.assertFalse(set(source_inventory(self.root)) & {'.env', 'data/private.json'})

    def approve_synthetic_fixture(self):
        self.profile['operator'] = {key: 'synthetic valid field' for key in OPERATOR_FIELDS}
        for group in ('requirements', 'known_findings'):
            for item in self.profile[group].values():
                item.update(status='verified', evidence='synthetic protected review reference',
                            reviewed_by='synthetic reviewer', reviewed_on='2026-01-01', rationale='synthetic review reason')
        self.write_json(PROFILE, self.profile)
        for row in self.rows:
            name = row['path']
            text = (self.root / name).read_text(encoding='utf-8')
            self.put(name, text.replace('상태: review-required',
                     '상태: approved · 승인자: synthetic reviewer · 승인 근거: synthetic protected review reference'))
        self.refresh()

    def test_consistency_refresh_never_reapproves_stale_publication_snapshot(self):
        self.approve_synthetic_fixture()
        self.assertEqual(check(self.root)['publication_status'], 'BLOCKED')
        record_publication(self.root, 'synthetic reviewer', 'Reviewed this synthetic scope for publication evidence.', 'synthetic protected approval reference')
        self.assertEqual(check(self.root)['publication_status'], 'REVIEW_RECORDED')
        self.put('ui/example.py', 'VALUE = 2\n')
        self.assertEqual(check(self.root)['publication_status'], 'BLOCKED')
        self.refresh()
        self.assertEqual(check(self.root)['consistency_status'], 'PASS')
        self.assertEqual(check(self.root)['publication_status'], 'BLOCKED')
        record_publication(self.root, 'synthetic reviewer', 'Reviewed the changed synthetic scope for publication evidence.', 'synthetic protected approval reference v2')
        self.assertEqual(check(self.root)['publication_status'], 'REVIEW_RECORDED')
        name = self.rows[0]['path']
        self.put(name, (self.root / name).read_text(encoding='utf-8') + '\n변경된 공개 정책 문구\n')
        self.refresh()
        self.assertEqual(check(self.root)['publication_status'], 'BLOCKED')

    def test_publication_record_requires_resolved_evidence(self):
        with self.assertRaises(CheckError):
            record_publication(self.root, 'synthetic reviewer', 'Synthetic scope was inspected for publication.', 'synthetic reference')

    def test_report_leaf_symlink_is_refused_without_overwriting_target(self):
        output = self.root / 'output'
        output.mkdir()
        target = self.root / 'unrelated.txt'
        target.write_text('ORIGINAL', encoding='utf-8')
        try:
            (output / 'report.json').symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest('symlinks unavailable')
        with self.assertRaises(CheckError):
            write_reports(output, check(self.root))
        self.assertEqual(target.read_text(encoding='utf-8'), 'ORIGINAL')

    def test_malformed_config_produces_safe_failure_reports(self):
        self.put(PROFILE, 'NOT_JSON_PRIVATE_VALUE')
        output = self.root / 'output'
        with patch('tools.compliance.check.ROOT', self.root), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = main(['--check', '--report-dir', str(output)])
        self.assertEqual(code, 2)
        payload = (output / 'report.json').read_text(encoding='utf-8')
        self.assertEqual(json.loads(payload)['consistency_status'], 'FAIL')
        self.assertNotIn('NOT_JSON_PRIVATE_VALUE', payload)
        self.assertTrue((output / 'report.md').exists())

    def test_source_symlink_is_never_followed(self):
        target = self.root / '.env'
        target.write_bytes(b'PRIVATE')
        link = self.root / 'ui/linked.py'
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest('symlinks unavailable')
        with self.assertRaises(CheckError):
            source_inventory(self.root)

    def test_line_ending_normalization_works_for_windows_checkout(self):
        path = self.root / 'ui/example.py'
        path.write_bytes(b'VALUE = 1\r\n')
        doc = self.root / self.rows[0]['path']
        doc.write_bytes(doc.read_bytes().replace(b'\n', b'\r\n'))
        self.assertEqual(check(self.root)['consistency_status'], 'PASS')

    def test_publication_markers_remain_blocked_after_review(self):
        path = self.root / self.rows[0]['path']
        self.put(self.rows[0]['path'], path.read_text(encoding='utf-8').replace('## 정책 또는 구현 기준\n', '## 정책 또는 구현 기준\n\n{{operator.legal_name}}\n'))
        self.refresh()
        result = check(self.root)
        self.assertEqual(result['consistency_status'], 'PASS')
        self.assertTrue(any('document 1:' in x for x in result['publication_blockers']))

    def test_invalid_profile_and_missing_finding_cannot_pass(self):
        self.profile['requirements']['privacy_review']['status'] = 'approved'
        self.write_json(PROFILE, self.profile)
        with self.assertRaises(CheckError):
            check(self.root)
        self.profile['requirements']['privacy_review']['status'] = 'unverified'
        self.profile['known_findings'].pop(KNOWN_FINDINGS[0])
        self.write_json(PROFILE, self.profile)
        with self.assertRaises(CheckError):
            check(self.root)

    def test_verified_and_not_applicable_require_evidence_reviewer_and_date(self):
        item = self.profile['requirements']['privacy_review']
        item['status'] = 'not_applicable'
        self.write_json(PROFILE, self.profile)
        self.assertTrue(any('privacy_review: evidence' in x for x in profile_blockers(self.root)))
        item.update(evidence='docs/compliance/fixture-evidence.md', reviewed_by='담당 검토자',
                    reviewed_on='2026-01-01', rationale='합성 테스트에서 근거 형식만 확인함')
        self.write_json(PROFILE, self.profile)
        self.assertFalse(any('privacy_review:' in x for x in profile_blockers(self.root)))
        item['reviewed_on'] = '2099-01-01'
        self.write_json(PROFILE, self.profile)
        self.assertTrue(any('privacy_review: valid' in x for x in profile_blockers(self.root)))

    def test_profile_change_requires_all_document_review(self):
        self.profile['operator']['legal_name'] = '합성 사업자'
        self.write_json(PROFILE, self.profile)
        self.assertEqual(check(self.root)['consistency_status'], 'FAIL')
        with self.assertRaises(CheckError):
            self.refresh([1])

    def test_refresh_requires_explicit_non_placeholder_attribution(self):
        for reviewer, note in ((None, None), ('TBD', 'reviewed source and policy'), ('담당자', '짧음')):
            with self.assertRaises(CheckError):
                refresh(self.root, reviewer, note)

    def test_direct_dependency_references_cannot_leak_credentials(self):
        self.put('pyproject.toml', '[project]\nname="fixture"\nversion="0"\ndependencies=["pkg @ https://secret:credential@host.example/pkg.whl"]\n')
        declarations = dependencies(self.root)
        self.assertNotIn('credential', json.dumps(declarations))
        self.assertNotIn('secret', json.dumps(declarations))
        self.assertIn('redacted', declarations[0])

    def test_duplicate_json_keys_fail_closed(self):
        self.put(PROFILE, '{"schema_version":1,"schema_version":1}')
        with self.assertRaises(CheckError):
            check(self.root)


if __name__ == '__main__':
    unittest.main()
