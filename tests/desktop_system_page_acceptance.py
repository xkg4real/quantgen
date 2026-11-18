"""System on the owner-approved draft (2026-11-17, docs/product/ui_drafts_2026-11-17/draft_07_system.png).

The provider list is built only from config's presence reports, shows setting names and never a value, runs the
pane's own access test from a row's 확인, and a language switch reads nothing. The toolbar and right-column controls
drive the existing widgets (system_tabs, the rail's theme selector). Offline: the network is patched to fail."""
import os
import re
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from quantgen_desktop.app import ResearchWindow
import config
from PyQt6.QtCore import QCoreApplication, QEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QAbstractButton, QApplication, QLabel
from core.research.connections import ConnectionOutput, ConnectionRequest, execute_connections
from tests.qt_fixture_cleanup import delete_owned_widget

SECRET = 'fixture-secret-value-7f3a'


def krx_status():
    return [{'id': 'kis', 'label': 'KIS (한국투자증권)', 'ready': True, 'vars': ('KIS_APP_KEY', 'KIS_APP_SECRET'),
             'note': 'Read-only quotes.', 'value': SECRET},
            {'id': 'krx', 'label': 'KRX Data marketplace', 'ready': False, 'vars': ('KRX_API_KEY',), 'note': 'Key.'}]


def ficc_status():
    return [{'id': 'fred', 'label': 'FRED (St. Louis Fed)', 'ready': True, 'vars': (), 'note': 'Keyless.'},
            {'id': 'yfinance', 'label': 'Yahoo Finance (yfinance)', 'ready': True, 'vars': (), 'note': 'Keyless.'}]


def crypto_status():
    return [{'id': 'upbit_account', 'label': 'Upbit account (자산조회 only)', 'ready': False,
             'vars': ('UPBIT_ACCESS_KEY', 'UPBIT_SECRET_KEY'), 'note': 'Balance only.', 'secret': SECRET}]


def quant_status():
    return [{'id': 'anthropic', 'label': 'Claude API (deep analysis)', 'ready': True, 'vars': ('ANTHROPIC_API_KEY',),
             'note': 'AI narrative analysis of quant results. Model: fixture-model.'}]


class SystemPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        network = patch('requests.sessions.Session.request', side_effect=AssertionError('network forbidden'))
        network.start()
        self.addCleanup(network.stop)
        self.loaders = {name: Mock(side_effect=fn) for name, fn in (
            ('krx_provider_status', krx_status), ('ficc_provider_status', ficc_status),
            ('crypto_provider_status', crypto_status), ('quant_provider_status', quant_status))}
        for name, mock in self.loaders.items():
            patcher = patch.object(config, name, mock)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.probes = {'ficc': Mock(return_value={'fred': {'ok': True, 'detail': '20 obs'},
                                                  'yfinance': {'ok': False, 'detail': 'Timeout'}})}
        self.runner = Mock(side_effect=lambda q: execute_connections(q, probe_loaders=self.probes))
        self.window = ResearchWindow(auto_refresh=False, locale='ko_KR', market_loader=Mock(side_effect=AssertionError),
                                     connections_runner=self.runner)
        self.addCleanup(delete_owned_widget, self.window)
        self.window.resize(1440, 900)
        self.window.show()
        self.window.navigate('system')
        self.settle()

    def settle(self):
        for _ in range(6):
            self.app.processEvents()
            # Deliver deferred deletes as the running app's event loop does (processEvents alone does not outside
            # app.exec()): key figures replaced on a language switch are hidden children until then.
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete.value)

    def wait_idle(self):
        for _ in range(1000):
            self.app.processEvents()
            if not self.window.jobs.busy:
                return
            QTest.qWait(10)
        self.fail('worker did not finish')

    def texts(self, root):
        found = []
        for widget in root.findChildren(QLabel):
            found += [widget.text(), widget.toolTip(), widget.accessibleName()]
        for widget in root.findChildren(QAbstractButton):
            found += [widget.text(), widget.toolTip(), widget.accessibleName()]
        return '\n'.join(found)

    def test_rows_come_from_config_and_show_setting_names_never_values(self):
        view = self.window.connections_view
        self.assertEqual(set(view.list.rows), {'kis', 'krx', 'fred', 'yfinance', 'upbit_account', 'anthropic'})
        shown = self.texts(self.window.system_workspace)
        for name in ('KIS_APP_KEY', 'KIS_APP_SECRET', 'KRX_API_KEY', 'UPBIT_ACCESS_KEY', 'ANTHROPIC_API_KEY'):
            self.assertIn(name, shown)
        self.assertNotIn(SECRET, shown)
        self.assertIn('fixture-model', shown)
        tones = {key: row.tone() for key, row in view.list.rows.items()}
        self.assertEqual(tones, {'kis': 'ok', 'krx': 'off', 'fred': 'ok', 'yfinance': 'ok', 'upbit_account': 'off',
                                 'anthropic': 'ok'})
        # Only providers with an access test in the pane get 확인; the others show a dash.
        with_check = {key for key, row in view.list.rows.items() if row.button is not None}
        self.assertEqual(with_check, {'kis', 'krx', 'fred', 'yfinance'})
        self.assertTrue(view.stamp.text().startswith('설정 읽음'))
        self.runner.assert_not_called()   # building the page reads presence only; no access test runs

    def test_row_check_runs_the_pane_request_and_updates_the_rows(self):
        w = self.window
        view, pane = w.connections_view, w.connections
        view.list.rows['fred'].button.click()
        self.wait_idle()
        self.runner.assert_called_once_with(ConnectionRequest('ficc'))
        self.probes['ficc'].assert_called_once_with()
        self.assertEqual(pane.tool.currentData(), 'ficc')
        self.assertEqual(pane.report['verdict'], 'NOT_RUN')
        self.assertEqual(view.list.rows['fred'].probe['state'], 'ok')
        self.assertEqual(view.list.rows['yfinance'].probe['state'], 'fail')
        self.assertEqual(view.list.rows['yfinance'].tone(), 'warn')
        self.assertIsNone(view.list.rows['kis'].probe)
        self.assertEqual(view.list.counts()['answered'], 1)
        self.assertEqual(view.list.counts()['probed'], 2)
        # The pane's table and narrative stay in the canvas; the exports are enabled at the list's foot.
        self.assertIn('연결 상태', pane.tables)
        self.assertTrue(pane.export_json.isEnabled())
        self.assertTrue(view.card.isAncestorOf(pane.export_json))
        # While a job runs the rows' 확인 follow the disabled form.
        pane.input_box.setEnabled(False)
        self.assertFalse(view.list.rows['kis'].button.isEnabled())
        pane.input_box.setEnabled(True)
        self.assertTrue(view.list.rows['kis'].button.isEnabled())

    def test_presence_result_updates_set_or_not_set(self):
        view, pane = self.window.connections_view, self.window.connections
        pane.show_result(ConnectionOutput(ConnectionRequest('presence'), (
            ('KIS (한국투자증권)', 'NOT_CONFIGURED', 'KIS_APP_KEY · KIS_APP_SECRET', 'note'),
            ('Unknown provider', 'CONFIGURED', '', ''))))
        self.assertEqual(view.list.rows['kis'].tone(), 'off')
        self.assertEqual(view.list.rows['fred'].tone(), 'ok')
        self.assertEqual(set(view.list.rows), {'kis', 'krx', 'fred', 'yfinance', 'upbit_account', 'anthropic'})

    def test_language_switch_reads_nothing_and_renders_english(self):
        w = self.window
        for mock in self.loaders.values():
            mock.reset_mock()
        with patch.object(w.jobs, 'start', side_effect=AssertionError('a language switch must not start jobs')):
            for language in ('en', 'ko', 'en'):
                w.set_language(language)
                self.settle()
        for mock in self.loaders.values():
            mock.assert_not_called()
        self.runner.assert_not_called()
        labels = [v.text() for v in w.system_workspace.findChildren(QLabel)]
        labels += [v.text() for v in w.system_workspace.findChildren(QAbstractButton)]
        self.assertFalse([t for t in labels if re.search('[가-힣]', re.sub(r'https?://\S+', '', t))])

    def test_toolbar_and_right_column_drive_the_existing_widgets(self):
        w = self.window
        ws = w.system_workspace
        switch = next(widget for widget in ws.toolbar_host.findChildren(type(w.system_theme))
                      if len(widget.buttons) == 3)
        switch.buttons[1].click()
        self.assertIs(w.system_tabs.currentWidget(), w.rules)
        self.assertFalse(ws.side.foot_host.isVisible())   # 선택한 연결 확인 belongs to 연결
        w.open_data_rights()
        self.assertIs(w.system_tabs.currentWidget(), w.data_rights)
        self.assertEqual(switch.current(), 2)
        switch.buttons[0].click()
        self.assertIs(w.system_tabs.currentWidget(), w.connections_view)
        self.assertTrue(ws.side.foot_host.isVisible())
        self.assertTrue(ws.side.foot_host.isAncestorOf(w.connections.run))
        w.system_theme.buttons[1].click()
        self.assertEqual(w.theme.currentIndex(), 1)
        w.theme.setCurrentIndex(0)
        self.assertEqual(w.system_theme.current(), 0)


if __name__ == '__main__':
    unittest.main()
