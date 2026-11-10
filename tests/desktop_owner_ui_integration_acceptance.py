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

# One application for the whole module: a QApplication made inside a test and dropped at its end
# deletes Qt objects other modules keep (wheel_guard's filter) when several modules share a process.
APP = QApplication.instance() or QApplication([])


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
        app = APP
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


class AppNotesTests(unittest.TestCase):
    def test_app_written_data_notes_read_in_korean_and_other_text_stays(self):
        from quantgen_desktop.source_notes import method_korean, note_korean
        from quantgen_desktop.translations import translate
        cases = {
            "Simulated Treasury par curve (Nelson-Siegel random walk) — no market data provider was used.":
                "넬슨-시겔 랜덤워크로 만든 합성 미국채 파 금리 곡선이며 시장 데이터 제공처를 쓰지 않았습니다.",
            "daily; Simulated series (OU rate, mean 3.50%) — no market data provider was used.":
                "일별; OU 금리 과정(평균 3.50%)으로 만든 합성 시계열이며 시장 데이터 제공처를 쓰지 않았습니다.",
            "Simulated spot (GBM, vol 7%) — no market data provider was used.":
                "GBM(변동성 7%)으로 만든 합성 현물환이며 시장 데이터 제공처를 쓰지 않았습니다.",
            "FMP_API_KEY is not configured; Simulated series (GBM, μ=8%, σ=14%) — no market data provider was used."
            " Yahoo Finance also failed (SPY: network forbidden).":
                "FMP_API_KEY가 설정되지 않음: GBM(μ=8%, σ=14%)으로 만든 합성 시계열이며 시장 데이터 제공처를 쓰지 않았습니다."
                " Yahoo Finance도 쓸 수 있는 자료를 주지 않았습니다(SPY: network forbidden).",
        }
        for english, korean in cases.items():
            self.assertEqual(note_korean(english), korean)
            self.assertEqual(translate(english, "ko"), korean)
            self.assertEqual(translate(english, "en"), english)
        for literal in ("Payer\nProvider note +1.250%", "Yahoo adjusted close", "My own note 678", None, ""):
            self.assertEqual(note_korean(literal), literal)
        self.assertEqual(method_korean("bootstrap"), "부트스트랩")
        self.assertEqual(method_korean("unknown_method"), "unknown_method")

    def test_hidden_columns_take_no_table_width(self):
        app = APP
        from quantgen_desktop.app import table, table_rows
        from quantgen_desktop.table_layout import configure_compact_table
        t = table(["Name", "Value", "Provider", "Observed"])
        table_rows(t, [["Alpha", "1.00", "FRED · a long provider name", "2026-11-10"]] * 3)
        configure_compact_table(t)
        t._compact_layout_controller.measure()
        full = t.maximumWidth()
        t.setColumnHidden(2, True); t.setColumnHidden(3, True)
        t._compact_layout_controller.measure()
        self.assertLess(t.maximumWidth(), full - 150)
        t.deleteLater(); app.processEvents()


if __name__ == "__main__":
    unittest.main()
