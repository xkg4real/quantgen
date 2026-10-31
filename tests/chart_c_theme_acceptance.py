"""C-layout and theme transitions preserve the computed data and user inputs."""
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
import flet as ft
import dotenv
with patch.object(dotenv,'load_dotenv',return_value=False):
    from ui.qcharts import _fig, _to_image
    from ui.theme_controller import apply_palette
    from core.theme import LIGHT, DARK, set_mode
    from ui.indicator_guide import IndicatorGuide
    from core.i18n import LocaleContext


class ThemeContractTests(unittest.TestCase):
    def tearDown(self):set_mode('light')

    def test_figure_repaints_existing_data_and_source_limits_without_reanalysis(self):
        set_mode('light')
        fig,ax=_fig(4,3,LIGHT)
        x=np.arange(12); y=x*x
        line,=ax.plot(x,y,color=LIGHT.accent)
        ax.set_title('Observed data',loc='left');ax.set_xlabel('Date');ax.set_ylabel('Price')
        image=_to_image(fig)
        first=image.image.src; limits=ax.get_ylim()
        image.render_theme(DARK)
        self.assertNotEqual(image.image.src,first)
        np.testing.assert_array_equal(line.get_xdata(),x)
        np.testing.assert_array_equal(line.get_ydata(),y)
        self.assertEqual(ax.get_ylim(),limits)
        from matplotlib.colors import to_rgba
        np.testing.assert_allclose(fig.get_facecolor(),to_rgba(DARK.surface))
        image.render_theme(LIGHT)
        self.assertEqual(image.image.src,first)

    def test_theme_updates_nested_styles_without_replacing_financial_form(self):
        field=ft.TextField(value='1234.50',color=LIGHT.text,bgcolor=LIGHT.surface)
        button=ft.Button('Run',style=ft.ButtonStyle(bgcolor=LIGHT.accent,
                          side=ft.BorderSide(1,LIGHT.border)))
        view=ft.Column([field,button])
        apply_palette(view,DARK)
        self.assertIs(view.controls[0],field)
        self.assertEqual(field.value,'1234.50')
        self.assertEqual(field.bgcolor,DARK.surface)
        self.assertEqual(button.style.side.color,DARK.border)
        apply_palette(view,LIGHT)
        self.assertEqual(field.color,LIGHT.text)
        self.assertEqual(field.value,'1234.50')

    def test_guide_dark_mode_and_resize_keep_sample_selection_and_cursor(self):
        page=SimpleNamespace(width=1500,qg_locale=LocaleContext('ko_KR'))
        set_mode('light'); guide=IndicatorGuide(page)
        guide.toggle('rsi');guide.toggle('sma');guide.move_cursor(45)
        before=(guide.keys,guide.series.dates,guide.cursor)
        set_mode('dark');apply_palette(guide,DARK)
        self.assertEqual((guide.keys,guide.series.dates,guide.cursor),before)
        self.assertEqual(guide.palette,DARK)
        page.width=390;apply_palette(guide,DARK)
        self.assertEqual((guide.keys,guide.series.dates,guide.cursor),before)
        self.assertIsNone(guide.image.width)


class NativeStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PyQt6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])

    def test_wide_minimum_hints_cannot_trap_the_scroll_area_above_breakpoint(self):
        from PyQt6.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QLabel, QBoxLayout
        from quantgen_desktop.chart_study import ChartStudy
        chart, reading = QLabel('chart'), QLabel('reading')
        chart.setMinimumWidth(480); reading.setMinimumWidth(420)
        study = ChartStudy(chart, reading)
        body = QWidget(); QVBoxLayout(body).addWidget(study)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(body)
        self.addCleanup(scroll.deleteLater); self.addCleanup(scroll.hide)
        scroll.resize(1200, 500); scroll.show(); self.app.processEvents()
        self.assertEqual(study.split.direction(), QBoxLayout.Direction.LeftToRight)
        scroll.resize(700, 500)
        self.app.processEvents(); self.app.processEvents()
        self.assertLessEqual(study.width(), scroll.viewport().width())
        self.assertEqual(study.split.direction(), QBoxLayout.Direction.TopToBottom)
        scroll.resize(1200, 500); self.app.processEvents()
        self.assertEqual(study.split.direction(), QBoxLayout.Direction.LeftToRight)

    def test_responsive_split_and_dark_restart_preserve_the_same_observations(self):
        import tempfile
        from pathlib import Path
        from PyQt6.QtCore import QSettings
        from PyQt6.QtWidgets import QBoxLayout
        with patch.object(dotenv,'load_dotenv',return_value=False):
            from quantgen_desktop.app import ResearchWindow
        with tempfile.TemporaryDirectory() as folder:
            settings=QSettings(str(Path(folder)/'ui.ini'),QSettings.Format.IniFormat)
            window=ResearchWindow(auto_refresh=False,language_store=settings)
            self.addCleanup(window.deleteLater);self.addCleanup(window.hide)
            window.resize(1600,1000);window.show();window.guide_open.click()
            guide=window.indicator_guide;guide.buttons['rsi'].click();guide.move_cursor(45)
            self.app.processEvents()
            before=(guide.keys,guide.series.dates,guide.cursor)
            self.assertEqual(guide.study.split.direction(),QBoxLayout.Direction.LeftToRight)
            window.theme.setCurrentIndex(1);self.app.processEvents()
            self.assertEqual(settings.value('ui/theme'),'dark')
            self.assertEqual(window.colors,DARK)
            self.assertEqual((guide.keys,guide.series.dates,guide.cursor),before)
            window.resize(1000,800);self.app.processEvents()
            self.assertEqual(guide.study.split.direction(),QBoxLayout.Direction.TopToBottom)
            reopened=ResearchWindow(auto_refresh=False,theme_mode=settings.value('ui/theme'))
            self.addCleanup(reopened.deleteLater)
            self.assertEqual(reopened.colors,DARK)
            self.assertEqual(reopened.theme.currentIndex(),1)


if __name__=='__main__':unittest.main()
