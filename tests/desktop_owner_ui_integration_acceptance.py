"""Owner UI port to the native app (UI-D1..D4, 2026-11-11): checks that span screen areas.

Area tests live in tests/desktop_owner_ui_<area>_acceptance.py; this file holds what the integrator
added across areas. No network: requests are patched to fail and history loaders are injected.
"""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import unittest
from unittest.mock import patch

import dotenv
with patch.object(dotenv, "load_dotenv", return_value=False):
    from core.research.market_analysis import ETFRequest, execute_etf
    from quantgen_desktop.app import ResearchWindow
from PyQt6.QtWidgets import QApplication


class CatalogueTests(unittest.TestCase):
    def test_area_catalogues_merge_without_conflicts(self):
        from quantgen_desktop import owner_ui_language
        from quantgen_desktop.translations import KO, translate
        merged = owner_ui_language.pairs()  # raises if two areas give one English text two Korean texts
        self.assertGreater(len(merged), 100)
        for en, ko in merged.items():
            if "{" not in en:
                self.assertEqual(KO[en], ko, en)
        self.assertEqual(translate("Choose a tool, then run.", "ko"), "도구를 고른 뒤 실행하세요.")


class AutomaticSourceTests(unittest.TestCase):
    def test_etf_auto_history_is_fetched_with_best_like_the_flet_page(self):
        from core.quant.history import synthetic_history
        asked = []

        def loader(symbol, *, source, days):
            asked.append(source)
            return synthetic_history(symbol, days=days)
        with patch("requests.sessions.Session.request", side_effect=AssertionError("network forbidden")), \
                patch("core.quant.history.load_history", side_effect=loader):
            out = execute_etf(ETFRequest(code="SPY", days=300))
            self.assertEqual(asked, ["best"])
            self.assertEqual(out.data["data_source"], "SYNTHETIC")
            asked.clear()
            execute_etf(ETFRequest(code="SPY", days=300, source="synthetic"))
            self.assertEqual(asked, ["synthetic"])

    def test_tool_panes_without_a_selector_do_not_ask_for_a_source(self):
        app = QApplication.instance() or QApplication([])
        for language, prompt in (("ko", "도구를 고른 뒤 실행하세요."), ("en", "Choose a tool, then run.")):
            w = ResearchWindow(auto_refresh=False, market_loader=lambda: [], language=language)
            try:
                for name in ("rates", "fx", "structuring", "macro", "etf", "crypto", "krx"):
                    pane = getattr(w, name)
                    self.assertFalse(pane.source.isVisibleTo(w), name)
                    self.assertNotIn("출처", pane.status.text(), name)
                    self.assertNotIn("source", pane.status.text().lower(), name)
                self.assertEqual(w.rates.status.text(), prompt)
            finally:
                w.deleteLater()
                app.processEvents()


if __name__ == "__main__":
    unittest.main()
