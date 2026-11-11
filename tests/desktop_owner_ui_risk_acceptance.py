"""Owner UI review (2026-11-10), area risk: Portfolio, Signals, Monte Carlo, risk table, home summary, paper.

Issues 13 (the portfolio result), 04/12 (no data-source selector; the app fetches by itself), 14 (no
English or raw ids on a Korean screen) and 11 (headed bullets, not a wall of text), checked on what the
owner sees in the native window, in Korean and in English. Offscreen, no network, fixture histories.
"""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from copy import deepcopy
from dataclasses import replace
import json
import math
import re
import unittest
from unittest.mock import patch

import dotenv
with patch.object(dotenv, "load_dotenv", return_value=False):
    from tests.desktop_acceptance import (fixture_runner, history_fixture, portfolio_fixture, signals_fixture)
    from quantgen_desktop.app import ResearchWindow
from core.research.analysis import AnalysisRequest, execute_analysis
from core.research.portfolio_analysis import PortfolioRequest, execute_portfolio
from core.research.signals_analysis import SignalsRequest, execute_signals
from core.research.runs import new_run
from quantgen_desktop.localization import UiLabel
from quantgen_desktop.narrative_view import NarrativeView
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QMessageBox, QTableWidget
from tests.qt_fixture_cleanup import delete_owned_widget

RAW_IDS = ("max_sharpe", "min_vol", "risk_parity", "equal_weight", "ma_cross", "rsi_revert", "garch_t")


def visible_texts(root):
    """Every visible label text and table cell under `root` (what the owner reads)."""
    out = [w.text() for w in root.findChildren(UiLabel) if w.isVisibleTo(root.window()) and w.isVisible()]
    for table in root.findChildren(QTableWidget):
        if not table.isVisible():
            continue
        for r in range(table.rowCount()):
            for c in range(table.columnCount()):
                item = table.item(r, c)
                if item is not None:
                    out.append(item.text())
    return out


class OwnerUiRiskTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        network = patch("requests.sessions.Session.request", side_effect=AssertionError("network forbidden"))
        network.start(); self.addCleanup(network.stop)

    def window(self, language):
        w = ResearchWindow(auto_refresh=False, market_loader=lambda: [], analysis_runner=fixture_runner,
                           portfolio_runner=portfolio_fixture, signals_runner=signals_fixture, language=language)
        w.resize(1440, 1000); w.show(); self.settle()

        def cleanup():
            self.wait_idle(w)
            with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
                w.close()
            delete_owned_widget(w)
        self.addCleanup(cleanup)
        return w

    def settle(self):
        for _ in range(4):
            self.app.processEvents(); QTest.qWait(5)

    def wait_idle(self, w):
        for _ in range(1500):
            self.app.processEvents()
            if not w.jobs.busy:
                return
            QTest.qWait(10)
        self.fail("worker did not finish")

    def assert_rows_fit(self, table):
        self.assertEqual(table.verticalScrollBar().maximum(), 0)
        self.assertEqual(table.height(), table._content_height_controller.content_height())

    # ------------------------------------------------------------------ data source (04/12)
    def test_core_requests_accept_best_and_pass_it_to_the_history_loader(self):
        seen = []

        def loader(symbol, source="auto", **kw):
            seen.append(source)
            offset = len(seen)
            return replace(history_fixture(), symbol=symbol, closes=tuple(
                100 + .05 * i + math.sin(i * (.4 + .1 * offset)) * 3 + math.cos(i * .1 + offset) for i in range(120)))
        PortfolioRequest(("A", "B"), source="best").validate()
        execute_portfolio(PortfolioRequest(("A", "B"), source="best"), history_loader=loader)
        execute_signals(SignalsRequest(source="best"), history_loader=loader)
        request = AnalysisRequest(symbol="TEST", source_requested="best", model="gbm", n_paths=200, horizon_days=5)
        execute_analysis(request, new_run(request.parameters()), history_loader=loader,
                         rate_reader=lambda s: (.03, "assumed fixture rate"))
        self.assertEqual(seen, ["best"] * 4)

    def test_selectors_are_hidden_and_requests_ask_for_the_automatic_source(self):
        w = self.window("ko")
        w.navigate("risk")
        for combo in (w.portfolio.source, w.signals.source, w.source):
            self.assertTrue(combo.isHidden())
            self.assertEqual(combo.currentData(), "best")
            self.assertGreaterEqual(combo.findData("synthetic"), 0)   # still selectable by tests and scripts
        self.assertNotIn(w.source, [control for _, control in w.quant_form.fields])
        self.assertNotIn(w.portfolio.source, [control for _, control in w.portfolio.form.fields])
        self.assertTrue(w.signals.source_label.isHidden())
        sent = []
        w.portfolio.requested.connect(sent.append); w.signals.requested.connect(sent.append)
        w.portfolio.symbols.setText("ONE,TWO,THREE"); w.portfolio.submit(); self.wait_idle(w)
        w.risk_tabs.setCurrentWidget(w.signals); w.signals.submit(); self.wait_idle(w)
        self.assertEqual([q.source for q in sent], ["best", "best"])
        w.navigate("quant"); w.symbol.setText("TEST"); w.paths.setValue(200); w.horizon.setValue(5)
        w.model.setCurrentIndex(w.model.findData("gbm")); w.run_analysis(); self.wait_idle(w)
        self.assertEqual(w.session.runs()[0]["parameters"]["source_requested"], "best")

    # ------------------------------------------------------------------ portfolio (13, 14, 11)
    def run_portfolio(self, w):
        w.navigate("risk")
        w.portfolio.symbols.setText("ONE,TWO,THREE")
        w.portfolio.source.setCurrentIndex(w.portfolio.source.findData("synthetic"))
        w.portfolio.submit(); self.wait_idle(w); self.settle()

    def test_portfolio_before_a_run_says_what_to_do_instead_of_empty_tables(self):
        w = self.window("ko"); w.navigate("risk"); self.settle()
        p = w.portfolio
        self.assertTrue(p.empty.isVisible())
        self.assertIn("[포트폴리오 분석 실행]", p.empty.text())
        self.assertFalse(p.comparison.isVisible())
        self.assertFalse(p.result.isVisible())

    def test_portfolio_korean_reads_verdict_first_with_display_names_and_fitted_tables(self):
        w = self.window("ko"); self.run_portfolio(w)
        p = w.portfolio
        self.assertFalse(p.empty.isVisible()); self.assertTrue(p.result.isVisible())
        self.assertEqual(p.summary_title.text(), "최대 샤프 지수 포트폴리오")
        self.assertIn("비중이 큰 종목은", p.summary.text())
        self.assertIn("합성 데이터(ONE, TWO, THREE)", p.synthetic.text())
        self.assertIn("데이터 출처: ONE · 합성 데이터", p.provenance.text())
        self.assertEqual(p.status.text(), "계산 완료 · 공식 투자 판정 없음")
        self.assertEqual([p.comparison.item(r, 0).text() for r in range(4)],
                         ["최대 샤프 지수", "최소 변동성", "리스크 패리티(위험 균등)", "동일 비중"])
        self.assertEqual({p.comparison.item(r, 4).text() for r in range(4)}, {"예"})
        self.assertEqual(p.comparison.item(0, 5).text(), "100.00% · 선택")
        self.assertEqual(p.comparison.item(1, 5).text(), "100.00% · 비교용")
        shown = "\n".join(visible_texts(p))
        for raw in RAW_IDS + ("True", "False", "solver converged", "selected", "comparison"):
            self.assertNotIn(raw, shown)
        for table in (p.comparison, p.weights, p.correlation):
            self.assert_rows_fit(table)
        view = p.narrative_view
        self.assertIsInstance(view, NarrativeView)
        self.assertEqual(view.headings()[0], "요약")
        self.assertIn("데이터", view.headings())
        self.assertTrue(view.lines())
        self.assertFalse(p.notes.isVisible())        # the full paragraph is folded under the bullets
        p.notes_fold.toggle.setChecked(True); self.settle()
        self.assertTrue(p.notes.isVisible())
        self.assertNotIn("equal_weight", p.notes.text())

    def test_portfolio_english_window_stays_english_and_report_is_unchanged_by_language(self):
        w = self.window("en"); self.run_portfolio(w)
        p = w.portfolio
        report = json.dumps(p.exports.report, sort_keys=True, default=str)
        raw_notes = p.notes.source_text
        self.assertEqual(p.summary_title.text(), "Max Sharpe portfolio")
        self.assertEqual(p.comparison.item(0, 0).text(), "Max Sharpe")
        self.assertEqual(p.comparison.item(0, 4).text(), "Yes")
        self.assertEqual(p.comparison.item(0, 5).text(), "100.00% · selected")
        self.assertEqual(p.status.text(), "Calculation complete · no official investment verdict")
        self.assertEqual(p.narrative_view.headings()[0], "Summary")
        self.assertFalse(re.search("[가-힣]", "\n".join(visible_texts(p.result))))
        with patch.object(w.jobs, "start", side_effect=AssertionError("no recompute")):
            for language in ("ko", "en", "ko"):
                w.set_language(language); self.settle()
                self.assertEqual(json.dumps(p.exports.report, sort_keys=True, default=str), report)
                self.assertEqual(p.notes.source_text, raw_notes)
                self.assertEqual(p.comparison.item(0, 0).text(), "최대 샤프 지수" if language == "ko" else "Max Sharpe")
                self.assertEqual(p.narrative_view.headings()[0], "요약" if language == "ko" else "Summary")
        portfolios = next(s["data"] for s in p.exports.report["sections"] if s["type"] == "portfolios")
        self.assertEqual(set(portfolios), {"max_sharpe", "min_vol", "risk_parity", "equal_weight"})

    # ------------------------------------------------------------------ signals (04/12, 14)
    def test_signals_summary_and_backtest_words_switch_language_without_changing_the_export(self):
        w = self.window("ko"); w.navigate("risk"); w.risk_tabs.setCurrentWidget(w.signals)
        pane = w.signals
        pane.submit(); self.wait_idle(w); self.settle()
        sections = json.dumps(pane.sections, sort_keys=True, default=str)
        report = deepcopy(pane.report)
        metrics = next(s for s in pane.sections if s.get("name") == "Backtest metrics")
        self.assertIn(("Strategy", "ma_cross"), [tuple(r) for r in metrics["rows"]])   # export keeps the id
        table = pane.tables["Backtest metrics"]
        title = pane.summary_box.findChildren(UiLabel)[0]
        for language in ("ko", "en", "ko"):
            w.set_language(language); self.settle()
            ko = language == "ko"
            self.assertEqual(title.text(), "TEST 기술적 관측" if ko else "TEST technical read")
            body = pane.summary_box.findChildren(UiLabel)[1].text()
            self.assertIn("매수 후 보유" if ko else "buy-and-hold", body)
            self.assertEqual(table.item(0, 1).text(), "이동평균 교차" if ko else "MA crossover")
            self.assertEqual(table.item(1, 1).text(), "단기 20 · 장기 50" if ko else "Fast 20 · slow 50")
            self.assertIn(table.item(5, 1).text(), ("예", "아니오") if ko else ("Yes", "No"))
            self.assert_rows_fit(table)
            self.assert_rows_fit(pane.tables["Composite"])
            self.assertEqual(json.dumps(pane.sections, sort_keys=True, default=str), sections)
            self.assertEqual(pane.report, report)
        shown = "\n".join(visible_texts(pane.result))
        for raw in ("ma_cross", "{'fast'", "True", "False"):
            self.assertNotIn(raw, shown)

    # ------------------------------------------------------------------ Monte Carlo, risk table, home (14, 11)
    def test_monte_carlo_notes_risk_table_and_home_summary_read_in_the_window_language(self):
        w = self.window("ko"); w.navigate("risk"); self.settle()
        self.assertTrue(w.risk_empty.isVisible()); self.assertFalse(w.risk_table.isVisible())
        self.assertIn("몬테카를로", w.risk_empty.text())
        w.navigate("quant")
        w.symbol.setText("TEST"); w.source.setCurrentIndex(w.source.findData("synthetic"))
        w.paths.setValue(200); w.horizon.setValue(5); w.run_analysis(); self.wait_idle(w); self.settle()
        raw = w.quant_notes.source_text
        text = w.quant_notes.text()
        for heading in ("데이터", "가정", "GARCH 적합"):
            self.assertIn(heading + "\n• ", text)
        self.assertIn("위험프리미엄 방식", text)
        for english in ("risk premium:", "converged=", "Next-session", "at_bound"):
            self.assertNotIn(english, text)
        self.assertIn("assumed fixture rate", text)          # provider/fixture text stays as written
        w.navigate("risk"); self.settle()
        self.assertTrue(w.risk_table.isVisible()); self.assertFalse(w.risk_empty.isVisible())
        self.assertEqual(w.risk_table.item(0, 1).text(), "GARCH(1,1)-t")
        self.assertEqual(w.risk_table.item(0, 5).text(), "합성 데이터(SYNTHETIC)")
        self.assert_rows_fit(w.risk_table)
        self.assertIn("미실행(NOT_RUN)", w.home_summary.text())
        self.assertNotIn("garch_t", w.home_summary.text())
        w.set_language("en"); self.settle()
        self.assertIn("Data\n• Synthetic data · SYNTHETIC", w.quant_notes.text())
        self.assertIn("risk premium:", w.quant_notes.text())
        self.assertEqual(w.quant_notes.source_text, raw)
        self.assertIn("verdict NOT_RUN", w.home_summary.text())
        self.assertEqual(w.risk_table.item(0, 5).text(), "SYNTHETIC")

    def test_paper_tables_wait_for_an_open_session(self):
        w = self.window("ko"); w.navigate("risk"); w.risk_tabs.setCurrentWidget(w.paper); self.settle()
        for widget in w.paper.session_widgets:
            self.assertFalse(widget.isVisible())
        self.assertIn("[모의 세션 읽기]", w.paper.dashboard.text())


if __name__ == "__main__":
    unittest.main()
