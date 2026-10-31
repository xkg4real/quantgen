"""Flet reference-screen callbacks without a server, stores or network."""
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import dotenv
with patch.object(dotenv,'load_dotenv',return_value=False):
    from ui.indicator_guide import IndicatorGuide
from ui.localization import translate_controls
from ui.research_home import ResearchHome
from ui.data_rights import DataRightsPanel
from core.i18n import LocaleContext
from core.quant.history import History


class BrowserIndicatorGuideTests(unittest.TestCase):
    def setUp(self):
        self.page=SimpleNamespace(width=390,qg_locale=LocaleContext('ko_KR'))
        p=patch('requests.sessions.Session.request',side_effect=AssertionError('Network forbidden'))
        p.start();self.addCleanup(p.stop)

    def test_initial_and_multiple_selection_are_aligned_without_io_on_home(self):
        with patch('pathlib.Path.open',side_effect=AssertionError('No file IO before guide opens')):
            home=ResearchHome(self.page,lambda route:None)
        self.assertIsNone(home.indicator_guide)
        home.toggle_indicator_guide();guide=home.indicator_guide
        self.assertEqual(guide.keys,());self.assertTrue(home.guide_host.visible)
        guide.toggle('sma');guide.toggle('rsi');guide.toggle('macd')
        self.assertEqual(guide.keys,('sma','rsi','macd'));self.assertEqual(guide.case_name,'2020')
        self.assertTrue(guide.image.src.startswith('data:image/svg+xml;base64,'))
        guide.clear_selection();self.assertEqual(guide.keys,())

    def test_page_local_languages_and_cursor_do_not_reset_selection(self):
        guide=IndicatorGuide(self.page);guide.toggle('rsi');guide.move_cursor(50)
        other=IndicatorGuide(SimpleNamespace(width=1100,qg_locale=LocaleContext('en_US')))
        self.assertIn('Learn technical',other.controls[0].value)
        self.assertIn('기술적',guide.controls[0].value)
        translate_controls(guide,LocaleContext('en_US'))
        self.assertIn('Learn technical',guide.controls[0].value)
        self.assertEqual(guide.keys,('rsi',));self.assertEqual(guide.cursor,50)
        self.assertEqual(other.keys,())

    def test_real_history_explorer_reuses_input_dates_and_not_a_teaching_sample(self):
        from datetime import date,timedelta
        history=History('FIXTURE','SYNTHETIC',tuple((date(2020,1,1)+timedelta(days=i)).isoformat() for i in range(80)),tuple(100+i*.1 for i in range(80)))
        guide=IndicatorGuide(self.page,history=history);guide.toggle('macd');guide.toggle('bb')
        self.assertEqual(guide.case_name,'research')
        self.assertEqual(guide.series.dates,history.dates)
        self.assertEqual(guide.series.closes,history.closes)
        self.assertEqual(guide.meta['provider'],history.source)

    def test_browser_rights_panel_covers_sources_and_translates_without_fetches(self):
        panel=DataRightsPanel(self.page)
        self.assertEqual(len(panel.record['home']),6)
        translate_controls(panel,LocaleContext('en_US'))
        self.assertIn('Home observations',panel.entries.controls[0].value)


if __name__=='__main__':unittest.main()
