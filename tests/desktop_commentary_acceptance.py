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
        self.window.navigate('library');self.runner.assert_not_called()
        p=self.prepare();p.submit();self.runner.assert_not_called()
        p.consent.setChecked(True);p.submit();self.wait()
        self.runner.assert_called_once();self.assertEqual(p.output.toPlainText(),'Fixture commentary')
        self.assertEqual(p.report_actions.report['verdict'],'NOT_RUN')
        p.refresh_sources();self.assertIsNone(p.report_actions.report);self.assertFalse(p.send.isEnabled())

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
