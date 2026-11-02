"""Recover malformed persisted UI preferences without providers or user stores."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import dotenv
with patch.object(dotenv, "load_dotenv", return_value=False):
    from quantgen_desktop.app import ResearchWindow
from core.i18n import LocaleContext
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication


class DesktopStartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_invalid_locale_types_have_usable_english_formatting(self):
        for value in (None, True, 42, ["ko_KR"], {"locale": "ko_KR"}, b"ko_KR"):
            with self.subTest(value=value):
                context = LocaleContext(value)
                self.assertEqual(str(context.locale), "en_US")
                self.assertEqual(context.language, "en")
                self.assertEqual(context.number(1234.5), "1,234.50")
        for value, expected in (("ko-KR", "ko_KR"), ("de_DE", "de_DE"), ("not_a_locale", "en_US")):
            self.assertEqual(str(LocaleContext(value).locale), expected)

    def test_invalid_persisted_locale_can_be_repaired_from_the_window(self):
        with tempfile.TemporaryDirectory() as folder, \
             patch("requests.sessions.Session.request", side_effect=AssertionError("Network forbidden")):
            path = Path(folder) / "settings.ini"
            settings = QSettings(str(path), QSettings.Format.IniFormat)
            settings.setValue("ui/locale", 42)
            settings.sync()
            reopened = QSettings(str(path), QSettings.Format.IniFormat)
            window = ResearchWindow(auto_refresh=False, locale=reopened.value("ui/locale"), language_store=reopened)
            try:
                self.assertEqual(window.nav["home"].text(), "Research Home")
                self.assertEqual(window.locale_picker.currentData(), "en_US")
                self.assertFalse(window.jobs.busy)
                self.assertIsNone(window.paper_session.runtime)
                window.set_language("ko")
                reopened.sync()
                self.assertEqual(window.nav["home"].text(), "연구 홈")
                self.assertEqual(QSettings(str(path), QSettings.Format.IniFormat).value("ui/locale"), "ko_KR")
            finally:
                window.close()
                window.deleteLater()
                self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
