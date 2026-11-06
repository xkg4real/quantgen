"""Optional commentary boundaries; every AI response is injected."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from copy import deepcopy
import threading
import unittest
from unittest.mock import patch,Mock
import dotenv
with patch.object(dotenv,'load_dotenv',return_value=False):
    from quantgen_desktop.app import ResearchWindow
    from quantgen_desktop.commentary import commentary_payload
    from core.quant.insights import Analysis
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication,QMessageBox
from PyQt6.QtTest import QTest


def report(tool='crypto'):
    return {'tool':tool,'execution_status':'COMPLETED','verdict':'NOT_RUN',
        'parameters':{'source':'synthetic','account':'never send'},
        'code':{'private_path':'never send'},
        'sections':[{'type':'table','name':'Upbit holdings · read only','rows':[['private account',123]]},
                    {'type':'table','name':'Price metrics','rows':[['price',42]]}]}


class NativeCommentaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        self.runner=Mock(return_value=Analysis('Fixture commentary','fixture-model'))
        self.window=ResearchWindow(auto_refresh=False,commentary_runner=self.runner)
        self.addCleanup(self.cleanup)

    def cleanup(self):
        self.wait()
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Yes):self.window.close()
        self.window.deleteLater();self.app.processEvents()

    def wait(self):
        for _ in range(300):
            self.app.processEvents()
            if not self.window.commentary.jobs.busy:return
            QTest.qWait(10)
        self.fail('Commentary worker did not finish')

    def prepare(self):
        p=self.window.commentary;p.sources=lambda:[('fixture',report())]
        p.refresh_sources();p.prepare();return p

    def test_only_explicit_successful_calculations_and_no_accounts(self):
        r=report();before=deepcopy(r);out=commentary_payload(r)
        self.assertNotIn('never send',str(out));self.assertNotIn('private account',str(out))
        self.assertEqual(out['sections'][0]['rows'],[['price',42]]);self.assertEqual(r,before)
        for tool in ('macro_records','connections','paper','rules'):
            with self.assertRaises(ValueError):commentary_payload(report(tool))
        for status in ('FAILED','RUNNING','NOT_RUN'):
            bad=report();bad['execution_status']=status
            with self.assertRaises(ValueError):commentary_payload(bad)

    def test_startup_navigation_preview_never_calls_ai_and_send_is_explicit(self):
        self.window.ui_language='ko'
        self.window.navigate('library');self.runner.assert_not_called()
        p=self.prepare();p.submit();self.runner.assert_not_called()
        p.consent.setChecked(True);p.submit();self.wait()
        self.runner.assert_called_once();self.assertEqual(p.output.toPlainText(),'Fixture commentary')
        self.assertEqual(p.report_actions.report['verdict'],'NOT_RUN')
        p.refresh_sources();self.assertIsNone(p.report_actions.report)
        # Owner B3: the button always answers, but each click without consent only guides the user.
        self.assertTrue(p.send.isEnabled());self.assertEqual(p.send.cursor().shape(),Qt.CursorShape.PointingHandCursor)
        p.submit();self.assertIsNotNone(p.payload);self.assertIn('전송 동의',p.status.text())
        self.assertTrue(p.preview.toPlainText())
        p.submit();self.assertIn('전송 동의에 체크',p.status.text())
        self.runner.assert_called_once()
        # Consent covers the question as it stood when ticked: a user edit asks for it again.
        p.consent.setChecked(True);p.question.setText('programmatic');self.assertTrue(p.consent.isChecked())
        QTest.keyClicks(p.question,'?');self.assertFalse(p.consent.isChecked())
        p.submit();self.assertIn('전송 동의에 체크',p.status.text());self.runner.assert_called_once()

    def test_error_clears_previous_result_and_redacts_provider_secrets(self):
        p=self.prepare();p.consent.setChecked(True);p.submit();self.wait()
        self.runner.return_value=Analysis('','fixture',error='https://provider/?key=hidden Bearer sensitive')
        p.submit();self.wait();self.assertIsNone(p.report_actions.report)
        self.assertNotIn('sensitive',p.status.text());self.assertNotIn('key=hidden',p.status.text())

    def test_auth_error_translates_on_switch_without_retry_or_success_export(self):
        from core.research.ai_connection import error_message
        p=self.prepare();before=deepcopy(p.payload)
        self.runner.return_value=Analysis('', 'fixture-model', error_message('AUTHENTICATION'),
                                          'AUTHENTICATION', 401)
        p.consent.setChecked(True);p.submit();self.wait()
        self.window.ui_language='ko';p.status.retranslate()
        self.assertIn('인증 실패',p.status.text());self.assertIn('HTTP 401',p.status.text())
        self.window.ui_language='en';p.status.retranslate()
        self.assertIn('authentication failed',p.status.text());self.assertNotIn('인증',p.status.text())
        self.assertEqual(p.output.toPlainText(),'');self.assertIsNone(p.report_actions.report)
        self.assertEqual(p.payload,before);self.runner.assert_called_once()

    def test_refused_or_cut_off_reply_is_neither_shown_nor_exportable(self):
        from core.ficc import insights as ficc_insights
        from core.quant import insights
        p=self.prepare();p.runner=ficc_insights.deep_analysis
        partial='The figures describe a portfolio whose'
        bodies=[({'content':[{'type':'text','text':partial}],'stop_reason':'refusal',
                  'stop_details':{'type':'refusal','category':None,'explanation':'provider explanation'}},('거절','declined')),
                ({'content':[{'type':'thinking','thinking':''}],'stop_reason':'max_tokens'},('출력 한도','output limit'))]
        for body,(ko,en) in bodies:
            with self.subTest(stop=body['stop_reason']):
                http=Mock();http.post.return_value.status_code=200;http.post.return_value.json.return_value=body
                with patch.object(insights.config,'anthropic_key',return_value='fixture-key'), \
                     patch.object(insights.config,'ai_model',return_value='fixture-model'), \
                     patch.object(insights,'_requests',http):
                    p.consent.setChecked(True);p.submit();self.wait()
                http.post.assert_called_once()
                self.assertEqual(p.output.toPlainText(),'');self.assertIsNone(p.report_actions.report)
                self.window.ui_language='ko';p.status.retranslate();self.assertIn(ko,p.status.text())
                self.assertNotIn(partial,p.status.text());self.assertNotIn('provider explanation',p.status.text())
                self.window.ui_language='en';p.status.retranslate();self.assertIn(en,p.status.text())
        self.runner.assert_not_called()

    def test_native_size_limit_matches_the_send_limit(self):
        import json
        from core.quant import insights
        from core.research.ai_payload import AI_PAYLOAD_MAX_BYTES, filter_analysis_fields
        from core.research.tool_export import plain

        def sized(target):
            r = {'tool': 'crypto', 'execution_status': 'COMPLETED', 'verdict': 'NOT_RUN',
                 'parameters': {'source': 'synthetic'}, 'sections': [{'type': 'text', 'text': ''}]}
            def native(r):          # what commentary_payload measures, before its size check
                return plain({'tool': r['tool'], 'parameters': filter_analysis_fields(r['parameters']),
                              'sections': [filter_analysis_fields(s) for s in r['sections']],
                              'official_verdict': 'NOT_RUN', 'reproducibility': 'PARTIAL',
                              'data_rights': 'NOT_VERIFIED'})
            def size(r):
                return len(json.dumps(native(r), ensure_ascii=False, allow_nan=False,
                                      sort_keys=True).encode('utf-8'))
            r['sections'][0]['text'] = '가' * 59_900
            r['sections'][0]['text'] += 'a' * (target - size(r))
            self.assertEqual(size(r), target)
            return r, native(r)

        for target in (AI_PAYLOAD_MAX_BYTES - 1, AI_PAYLOAD_MAX_BYTES, AI_PAYLOAD_MAX_BYTES + 1):
            with self.subTest(bytes=target):
                r, payload = sized(target)
                try:
                    payload = commentary_payload(r); accepted = True
                except ValueError:
                    accepted = False
                http = Mock(); http.post.return_value.status_code = 200
                http.post.return_value.json.return_value = {
                    'content': [{'type': 'text', 'text': 'fixture'}], 'stop_reason': 'end_turn'}
                with patch.object(insights.config, 'anthropic_key', return_value='fixture-key'), \
                     patch.object(insights, '_requests', http):
                    sent = insights.deep_analysis('crypto_market', payload)
                self.assertEqual(accepted, target <= AI_PAYLOAD_MAX_BYTES)
                self.assertEqual(accepted, sent.error_code != 'PAYLOAD_TOO_LARGE')
                self.assertEqual(http.post.called, accepted)

    def test_consent_status_names_the_fixed_instructions(self):
        p = self.prepare()
        self.window.ui_language = 'ko'; p.status.retranslate()
        self.assertIn('고정 작성 지침', p.status.text())
        self.window.ui_language = 'en'; p.status.retranslate()
        self.assertIn('fixed writing instructions', p.status.text())
        self.assertNotIn('고정', p.status.text())
        p.submit()
        self.assertIn('send consent', p.status.text())
        self.assertIn('fixed writing instructions', p.status.text())
        self.assertIn('your question', p.status.text())
        self.window.ui_language = 'ko'; p.status.retranslate()
        self.assertIn('전송 동의에 체크', p.status.text())
        self.assertIn('고정 작성 지침', p.status.text())
        self.assertIn('질문', p.status.text())
        self.assertNotIn('아래 내용만', p.status.text())
        self.runner.assert_not_called()

    def test_invalid_or_oversized_preview_is_localized_without_sending(self):
        from core.research.ai_connection import error_message
        p=self.window.commentary
        for text,code in (('가'*60_000,'PAYLOAD_TOO_LARGE'),
                          ('fixture-private-marker \ud800','PAYLOAD_INVALID')):
            with self.subTest(code=code):
                source=report();source['sections']=[{'type':'text','text':text}]
                with self.assertRaises(ValueError) as refused:commentary_payload(source)
                self.assertEqual(str(refused.exception),error_message(code))
                p.sources=lambda:[('fixture',source)]
                p.refresh_sources();p.prepare()
                self.assertIsNone(p.payload);self.assertEqual(p.preview.toPlainText(),'')
                self.assertEqual(p.output.toPlainText(),'');self.assertIsNone(p.report_actions.report)
                for language in ('en','ko'):
                    self.window.ui_language=language;p.status.retranslate()
                    self.assertEqual(p.status.text(),error_message(code,language))
                    self.assertNotIn('fixture-private-marker',p.status.text())
                    if code=='PAYLOAD_TOO_LARGE':self.assertIn('180,000',p.status.text())
                p.consent.setChecked(True);p.submit()
                self.assertIsNone(p.payload)
                self.runner.assert_not_called()

    def test_redacted_reply_withholds_original_numeric_tokens_from_note_and_export(self):
        import json
        from core.research.ai_output_check import AI_LABEL, NumberCheck
        raw='Source https://example.invalid/?start=773100117 shows 42. api_key=982710119'
        check=NumberCheck(3,('773100117','982710119'),(),1,0,0)
        result=Analysis(raw,'fixture-model',stop_reason='end_turn',number_check=check)
        self.runner.return_value=result
        p=self.prepare();p.consent.setChecked(True);p.submit();self.wait()
        self.assertIn('[provider URL redacted]',p.output.toPlainText())
        self.assertIn('shows 42',p.output.toPlainText())
        for language,explanation in (('en','The displayed text was not checked again.'),
                                     ('ko','표시된 글은 다시 대조하지 않았습니다.')):
            self.window.ui_language=language;p.check_note.retranslate()
            self.assertIn(AI_LABEL[language],p.check_note.text())
            self.assertIn(explanation,p.check_note.text())
            for hidden in check.not_found:self.assertNotIn(hidden,p.check_note.text())
        exported=p.report_actions.report
        self.assertEqual(exported['verdict'],'NOT_RUN')
        self.assertEqual(exported['parameters']['verification'],'NOT_VERIFIED')
        self.assertIsNone(exported['parameters']['number_check'])
        self.assertEqual(exported['parameters']['number_check_status'],'WITHHELD_REDACTED_REPLY')
        self.assertEqual(exported['parameters']['number_check_basis'],'ORIGINAL_REPLY_BEFORE_DISPLAY_REDACTION')
        for hidden in check.not_found:self.assertNotIn(hidden,json.dumps(exported))
        self.assertIn('The displayed text was not checked again.',exported['sections'][-1]['text'])
        self.assertEqual(result.text,raw);self.assertIs(result.number_check,check)
        self.runner.assert_called_once()

    def test_success_label_and_export_stay_advisory(self):
        from core.research.ai_output_check import AI_LABEL, NumberCheck, check_line
        p=self.prepare();p.consent.setChecked(True);p.submit();self.wait()
        self.assertEqual(p.output.toPlainText(),'Fixture commentary')
        self.window.ui_language='ko';p.check_note.retranslate()
        self.assertIn('검증 안 됨',p.check_note.text());self.assertIn('숫자 대조: 실행하지 않음.',p.check_note.text())
        self.window.ui_language='en';p.check_note.retranslate()
        self.assertEqual(p.check_note.text(),AI_LABEL['en']+'\n'+check_line(None,'en'))
        report=p.report_actions.report
        self.assertEqual(report['verdict'],'NOT_RUN')
        self.assertEqual(report['parameters']['verification'],'NOT_VERIFIED')
        self.assertEqual(report['parameters']['stop_reason'],'NOT_RECORDED')
        self.assertIsNone(report['parameters']['number_check'])
        texts=[s['text'] for s in report['sections']]
        self.assertEqual(texts[0],'Fixture commentary')
        self.assertIn(AI_LABEL['en'],texts);self.assertIn(check_line(None,'en'),texts)
        p.refresh_sources();self.assertEqual(p.check_note.text(),'')

        check=NumberCheck(1,('9.99',),(),0,0,0)
        self.runner.return_value=Analysis('Fixture commentary','fixture-model',stop_reason='end_turn',number_check=check)
        p=self.prepare();p.consent.setChecked(True);p.submit();self.wait()
        self.window.ui_language='ko';p.check_note.retranslate();self.assertIn('9.99',p.check_note.text())
        self.assertIn('찾지 못한 숫자',p.check_note.text())
        self.window.ui_language='en';p.check_note.retranslate();self.assertIn(check_line(check,'en'),p.check_note.text())
        report=p.report_actions.report
        self.assertEqual(report['parameters']['stop_reason'],'end_turn')
        self.assertEqual(report['parameters']['number_check']['not_found'],['9.99'])
        self.assertEqual(report['parameters']['number_check_status'],'COMPLETED')
        self.assertEqual(report['parameters']['number_check_basis'],'DISPLAYED_REPLY')
        self.assertIn(check_line(check,'en'),[s['text'] for s in report['sections']])
        self.assertEqual(report['verdict'],'NOT_RUN')

        gate=threading.Event()
        def blocked(*a,**kw):gate.wait(2);return Analysis('Fixture commentary','fixture-model')
        self.runner.side_effect=blocked
        p.consent.setChecked(True);p.submit()
        self.assertEqual(p.check_note.text(),'');gate.set();self.wait()
        self.assertTrue(p.check_note.text())
        self.runner.side_effect=None
        self.runner.return_value=Analysis('','fixture-model',error='fixture failure')
        p.consent.setChecked(True);p.submit();self.wait()
        self.assertEqual(p.check_note.text(),'');self.assertEqual(p.output.toPlainText(),'')
        self.assertIsNone(p.report_actions.report)

    def test_daily_prompt_kind_and_close_guard(self):
        gate=threading.Event()
        def runner(*a,**kw):gate.wait(2);return Analysis('daily fixture','fixture')
        p=self.window.commentary;p.runner=Mock(side_effect=runner)
        r=report('macro');r['parameters']['tool']='daily';p.sources=lambda:[('daily',r)]
        p.refresh_sources();p.prepare();p.consent.setChecked(True);p.submit()
        self.window.show();self.assertFalse(self.window.close());gate.set();self.wait()
        self.assertEqual(p.runner.call_args.args[0],'daily_market_commentary')

    def test_collection_excludes_records_and_reads_only_current_reports(self):
        self.assertEqual(self.window.commentary_sources(),[])
        self.window.connections.report=report('connections');self.window.macro_records.report=report('macro_records')
        self.window.portfolio.exports.report=report('portfolio');self.window.crypto.report=report()
        sources=self.window.commentary_sources()
        self.assertEqual([name for name,_ in sources],['portfolio','crypto'])


if __name__=='__main__':unittest.main()
