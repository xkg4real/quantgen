"""Native interaction fixtures; no provider calls, real rules, studies or secrets."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch
from zipfile import ZipFile

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import dotenv
with patch.object(dotenv,'load_dotenv',return_value=False):
    from quantgen_desktop.app import ResearchWindow
from PyQt6.QtWidgets import QApplication,QLabel,QFileDialog
from PyQt6.QtCore import QSettings,Qt
from PyQt6.QtGui import QColor,QKeyEvent
from PyQt6.QtTest import QTest
from core.i18n import LocaleContext


class NativeIndicatorGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        deny=patch('requests.sessions.Session.request',side_effect=AssertionError('Network forbidden'))
        deny.start();self.addCleanup(deny.stop)
        self.provider=Mock(side_effect=AssertionError('Provider forbidden'))
        self.window=ResearchWindow(auto_refresh=False,locale='ko_KR',market_loader=self.provider,connections_runner=self.provider)
        self.window.resize(1000,800);self.window.show();self.app.processEvents()
        from tests.qt_fixture_cleanup import delete_owned_widget
        self.addCleanup(delete_owned_widget,self.window)

    def test_reference_screen_selection_shares_history_and_never_starts_jobs(self):
        w=self.window
        self.assertFalse(w.indicator_guide.isVisible())
        w.nav['guide'].click();self.app.processEvents()
        self.assertEqual(w.stack.currentIndex(), w.route_indices['guide'])
        self.assertTrue(w.nav['guide'].isChecked())
        guide=w.indicator_guide
        self.assertTrue(guide.isVisible());self.assertEqual(guide.keys,())
        baseline=guide.series.dates
        guide.options['sma'].setFocus();QTest.keyClick(guide.options['sma'],Qt.Key.Key_Space)
        self.assertEqual(guide.keys,('sma',));self.assertEqual(guide.case_name,'2022')
        guide.choose('rsi');guide.options['macd'].click();self.app.processEvents()
        self.assertEqual(guide.case_name,'2020');self.assertEqual(guide.series.dates,baseline)
        self.assertEqual(guide.keys,('sma','rsi','macd'))
        self.assertGreater(guide.chart.renderer().viewBoxF().height(),0)
        guide.move_cursor(100);self.assertEqual(guide.slider.value(),100)
        self.assertEqual(guide.chart.cursor,100)
        self.assertFalse(w.jobs.busy);self.assertEqual(w.session.runs(),[])
        self.assertIsNone(w.paper_session.runtime);self.provider.assert_not_called()
        guide.clear.click();self.assertEqual(guide.keys,())

    def test_language_change_preserves_controls_and_current_guide_selection(self):
        w=self.window;guide=w.indicator_guide
        w.symbol.setText('005930');w.target.setText('1234.50');w.seed.setValue(123)
        guide.choose('rsi');guide.move_cursor(100)
        original=(w.symbol.text(),w.target.text(),w.seed.value(),w.source.currentData(),w.model.currentData())
        w.locale_picker.setCurrentIndex(w.locale_picker.findData('en_US'));self.app.processEvents()
        self.assertEqual(w.nav['home'].text(),'Research Home')
        self.assertIn('Choose an indicator',guide.intro.text())
        self.assertIn('Choose several',guide.selection_title.text())
        self.assertEqual(guide.focus,'rsi');self.assertTrue(guide.options['rsi'].isChecked())
        self.assertEqual(guide.keys,('rsi',));self.assertEqual(guide.cursor,100)
        self.assertEqual((w.symbol.text(),w.target.text(),w.seed.value(),w.source.currentData(),w.model.currentData()),original)
        w.locale_picker.setCurrentIndex(w.locale_picker.findData('fr_FR'));self.app.processEvents()
        self.assertEqual(w.ctx.language,'en');self.assertIn('English',w.locale_notice.text())
        self.assertEqual(w.ctx.number(1234.5),'1\u202f234,50')
        self.assertEqual(w.target.text(),'1234.50')

    def test_guide_export_is_explicit_localized_and_cancel_writes_nothing(self):
        guide=self.window.indicator_guide;guide.set_locale(LocaleContext('en_US'));guide.choose('rsi')
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'guide.zip'
            with patch.object(QFileDialog,'getSaveFileName',return_value=('', '')):guide.save_report()
            self.assertFalse(list(Path(folder).iterdir()))
            with patch.object(QFileDialog,'getSaveFileName',return_value=(str(path),'ZIP')):guide.save_report()
            with ZipFile(path) as archive:self.assertIn('What does it measure?',archive.read('report.html').decode())

    def test_rights_inventory_search_and_language_are_display_only(self):
        pane=self.window.data_rights
        pane.search.setText('DEXKOUS');self.app.processEvents()
        self.assertFalse(pane.tree.topLevelItem(0).isHidden())
        leaves=[pane.tree.topLevelItem(g).child(i) for g in range(pane.tree.topLevelItemCount())
                for i in range(pane.tree.topLevelItem(g).childCount())]
        shown=[item for item in leaves if not item.isHidden()]
        self.assertTrue(shown)
        self.assertTrue(all(item.text(0)=='DEXKOUS' for item in shown))
        pane.tree.setCurrentItem(shown[0]);self.app.processEvents()
        self.assertIn('Federal Reserve',pane.detail.text())
        pane.set_locale(LocaleContext('en_US'))
        self.assertIn('Daily',pane.tree.topLevelItem(0).child(0).text(2))
        self.provider.assert_not_called()

    def test_vector_chart_background_keyboard_and_selection_survive_theme_resize(self):
        w=self.window;w.nav['guide'].click();guide=w.indicator_guide
        for key in ('sma','ema','rsi','macd','bb'):guide.choose(key)
        for theme in (0,1):
            w.change_theme(theme)
            for width in (1000,1360,2400):
                w.resize(width,800);self.app.processEvents()
                chart=guide.chart;pixmap=chart.grab();image=pixmap.toImage();dpr=pixmap.devicePixelRatio()
                self.assertEqual(int(chart.renderer().viewBoxF().width()),chart.width())
                colour=image.pixelColor(round((chart.width()-30)*dpr),round((chart.height()-15)*dpr))
                self.assertEqual(colour,QColor(w.colors.surface))
                self.assertEqual(guide.keys,('sma','ema','rsi','macd','bb'))
        guide.chart.keyPressEvent(QKeyEvent(QKeyEvent.Type.KeyPress,Qt.Key.Key_Home,Qt.KeyboardModifier.NoModifier))
        self.assertEqual(guide.cursor,0)
        guide.chart.keyPressEvent(QKeyEvent(QKeyEvent.Type.KeyPress,Qt.Key.Key_End,Qt.KeyboardModifier.NoModifier))
        self.assertEqual(guide.cursor,len(guide.series.closes)-1)
        w.navigate('home');self.assertFalse(guide.isVisible())
        w.nav['guide'].click();self.assertEqual(guide.keys,('sma','ema','rsi','macd','bb'))

    def test_visible_multiple_choices_and_optional_terms_need_no_typing(self):
        from PyQt6.QtWidgets import QLineEdit
        w=self.window;w.navigate('guide');guide=w.indicator_guide;self.app.processEvents()
        from core.education.indicators import STUDIES
        self.assertEqual(set(guide.options),{s.key for s in STUDIES})
        self.assertFalse(guide.findChildren(QLineEdit))
        for key in ('rsi','bb'):
            button=guide.options[key];self.assertTrue(button.isVisible())
            button.setFocus();QTest.keyClick(button,Qt.Key.Key_Space)
        self.assertEqual(guide.keys,('rsi','bb'))
        self.assertTrue(guide.detail.isVisible());self.assertFalse(guide.detail_body.isVisible())
        guide.detail_more.click();self.assertTrue(guide.detail_body.isVisible())
        self.assertEqual([h.text() for h,b in guide.detail_sections],
                         [w.ctx.t(f) for f in ('meaning','look','interpret','limit')])
        self.assertTrue(all(b.text() for h,b in guide.detail_sections))
        case,dates=guide.case_name,guide.series.dates
        index=guide.terms.findData('duration');guide.terms.setCurrentIndex(index);guide.terms.activated.emit(index)
        self.assertEqual(guide.focus,'duration');self.assertEqual((guide.case_name,guide.series.dates),(case,dates))
        self.assertFalse(guide.terms.isEditable());self.assertEqual(guide.detail_category.text(),'금리·채권')
        guide.options['rsi'].click();self.assertEqual(guide.keys,('bb',))
        guide.chips['bb'].remove_button.click();self.assertEqual(guide.keys,())
        self.assertFalse(w.jobs.busy);self.provider.assert_not_called()

    def test_choice_language_switch_and_layout_preserve_selection(self):
        import re
        w=self.window;w.navigate('guide');guide=w.indicator_guide;guide.choose('sma');guide.choose('rsi')
        for language in ('en_US','ko_KR'):
            w.locale_picker.setCurrentIndex(w.locale_picker.findData(language));self.app.processEvents()
            for width in (1000,1440):
                w.resize(width,800)
                for _ in range(8):self.app.processEvents()
                self.assertEqual(guide.keys,('sma','rsi'))
                self.assertEqual(w.stack.currentWidget().horizontalScrollBar().maximum(),0)
                for button in guide.options.values():
                    self.assertTrue(button.parentWidget().rect().contains(button.geometry()))
                    self.assertGreaterEqual(button.height(),button.heightForWidth(button.width()))
            if language=='en_US':
                texts=[guide.selection_title.text(),guide.detail_title.text(),guide.detail_category.text(),
                       guide.selected_label.text(),*[b.text()+b.accessibleDescription() for b in guide.options.values()],
                       guide.intro.text(),guide.steps.text()]
                self.assertFalse([t for t in texts if re.search('[가-힣]',t)])

    def test_region_preference_round_trips_without_changing_financial_inputs(self):
        with tempfile.TemporaryDirectory() as folder:
            store=QSettings(str(Path(folder)/'locale.ini'),QSettings.Format.IniFormat)
            w=self.window;w.language_store=store;w.target.setText('1234.50')
            w.locale_picker.setCurrentIndex(w.locale_picker.findData('de_DE'));store.sync()
            self.assertEqual(store.value('ui/locale'),'de_DE')
            self.assertEqual(store.value('ui/language'),'en')
            self.assertEqual(w.target.text(),'1234.50')
            restored=ResearchWindow(auto_refresh=False,locale=store.value('ui/locale'),language_store=store)
            self.addCleanup(restored.deleteLater)
            self.assertEqual(str(restored.ctx.locale),'de_DE')
            self.assertEqual(restored.ctx.number(1234.5),'1.234,50')
            self.assertEqual(restored.locale_notice.text(),restored.ctx.t('language_fallback'))


if __name__=='__main__':unittest.main()
