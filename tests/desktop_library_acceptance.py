"""Research Library on the owner-approved draft (2026-11-17, docs/product/ui_drafts_2026-11-17/draft_06_library.png).

The page shows the session's runs as rows, a preview of the selected run and its evidence in the right column; the run
table (its columns, status roles and selection) stays the record the two exports save. Offline: deterministic
histories, no network, no store, no AI call."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import dotenv
with patch.object(dotenv, "load_dotenv", return_value=False):
    from quantgen_desktop.app import ResearchWindow
from core.research.runs import read_export
from core.research.tool_export import make_report
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QAbstractButton, QApplication, QLabel, QMessageBox
from tests.desktop_acceptance import fixture_runner


class ResearchLibraryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        network = patch("requests.sessions.Session.request", side_effect=AssertionError("network forbidden"))
        network.start()
        self.addCleanup(network.stop)
        self.commentary = Mock(side_effect=AssertionError("nothing is sent without the user's action"))
        self.window = ResearchWindow(auto_refresh=False, market_loader=lambda: [], analysis_runner=fixture_runner,
                                     commentary_runner=self.commentary, language="en")
        self.window.resize(1360, 900)
        self.window.show()
        self.app.processEvents()
        self.addCleanup(self.close)

    def close(self):
        self.wait_idle()
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
            self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def wait_idle(self):
        for _ in range(1500):
            self.app.processEvents()
            if not self.window.jobs.busy:
                return
            QTest.qWait(10)
        self.fail("Worker did not finish in 15 seconds")

    def settle(self):
        for _ in range(6):
            self.app.processEvents()
            QTest.qWait(10)

    def run_mc(self, symbol, *, fail=False):
        w = self.window
        w.symbol.setText(symbol)
        w.source.setCurrentIndex(w.source.findData("synthetic"))
        w.model.setCurrentIndex(w.model.findData("gbm"))
        w.drift.setCurrentIndex(w.drift.findData("zero"))
        w.paths.setValue(200)
        w.horizon.setValue(5)
        if fail:
            w.analysis_runner = Mock(side_effect=RuntimeError("fixture failure"))
        w.run_analysis()
        self.wait_idle()
        w.analysis_runner = fixture_runner
        return w.session.runs()[0]

    def test_rows_mirror_the_session_and_drive_the_run_table(self):
        w = self.window
        failed = self.run_mc("FAIL", fail=True)
        first = self.run_mc("TEST")
        second = self.run_mc("TWO")
        w.navigate("library")
        self.settle()
        self.assertEqual([row.key for row in w.library_rows], [second["run_id"], first["run_id"], failed["run_id"]])
        # The run table keeps its columns and status roles; it is what the exports save.
        self.assertEqual(w.run_table.rowCount(), 3)
        self.assertEqual(w.run_table._qg_status_columns, {2: "execution", 3: "official"})
        self.assertEqual(w.run_table.item(2, 2).toolTip(), "FAILED")
        # Until the user picks a row the newest completed run is shown, and the run table follows the list.
        self.assertEqual(w.library_selected, second["run_id"])
        self.assertEqual(w.run_table.item(w.run_table.currentRow(), 0).data(Qt.ItemDataRole.UserRole), second["run_id"])
        # A click on a row selects it there and in the run table.
        rect = w.library_list.row_rect(1)
        QTest.mouseClick(w.library_list, Qt.MouseButton.LeftButton, pos=rect.center().toPoint())
        self.assertEqual(w.library_selected, first["run_id"])
        self.assertEqual(w.run_table.item(w.run_table.currentRow(), 0).data(Qt.ItemDataRole.UserRole), first["run_id"])
        # The keyboard moves the selection; a caller selecting in the run table moves the list.
        w.library_list.setFocus()
        QTest.keyClick(w.library_list, Qt.Key.Key_Down)
        self.assertEqual(w.library_selected, failed["run_id"])
        w.run_table.selectRow(0)
        self.assertEqual(w.library_selected, second["run_id"])
        self.assertEqual(w.library_list.current, second["run_id"])
        # The choice survives a new run; filters and the search only change what the list shows.
        w.run_table.selectRow(1)
        self.run_mc("THREE")
        self.assertEqual(w.library_selected, first["run_id"])
        w.library_search.setText("two")
        self.assertEqual([row.key for row in w.library_list.shown], [second["run_id"]])
        w.library_search.clear()
        w.library_filter.set_current(2, emit=True)    # 포트폴리오
        self.assertEqual(w.library_list.shown, [])
        w.library_filter.set_current(0, emit=True)
        self.assertEqual(len(w.library_list.shown), 4)
        counts = {pair.keys[0].text(): pair.keys[1].text() for pair in w.library_counts.flow.items}
        self.assertEqual((counts["Completed"], counts["Failed"], counts["Verdict"]), ("3", "1", "NOT_RUN"))

    def test_evidence_and_preview_read_the_record(self):
        w = self.window
        failed = self.run_mc("FAIL", fail=True)
        run = self.run_mc("TEST")
        w.navigate("library")
        self.settle()
        values = {check.label[0]: (check.state, check.value[0]) for check in self.checks()}
        self.assertEqual(values["Random seed"], ("ok", str(run["parameters"]["seed"])))
        digest = run["data"]["fingerprint_sha256"]
        self.assertEqual(values["Data fingerprint"], ("ok", f"sha256 {digest[:4]}…{digest[-4:]}"))
        self.assertEqual(values["Data vintage · licence"], ("warn", "NOT_VERIFIED"))
        self.assertEqual(values["Trading costs"], ("none", "NOT_APPLIED"))
        self.assertEqual(values["Verdict"], ("none", "NOT_RUN"))
        figures = {pair.keys[0].text(): pair.keys[1].text() for pair in w.library_preview_figures.flow.items}
        self.assertEqual(figures["Median"], f"{run['metrics']['p50']:,.2f}")
        self.assertIs(w.library_chart.result, w.outputs[run["run_id"]].result)
        # A failed record shows what it holds and nothing more: no fingerprint, no figures, no chart.
        w.library_select(failed["run_id"])
        values = {check.label[0]: (check.state, check.value[0]) for check in self.checks()}
        self.assertEqual(values["Data fingerprint"], ("none", "no data"))
        self.assertEqual(w.library_preview_figures.items, ())
        self.assertIsNone(w.library_chart.result)
        self.assertIn("RuntimeError", w.library_preview_text.text())
        self.commentary.assert_not_called()

    def checks(self):
        from quantgen_desktop.library_view import evidence
        return evidence(self.window.library_list.entry())[0]

    def test_saving_is_explicit_and_marks_only_that_run(self):
        w = self.window
        run = self.run_mc("TEST")
        w.navigate("library")
        self.settle()
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(list(Path(folder).iterdir()), [])     # nothing is saved by running or showing
            target = Path(folder) / "run.json"
            with patch("quantgen_desktop.app.QFileDialog.getSaveFileName", return_value=(str(target), "")):
                w.save_json.click()
            self.assertEqual(read_export(target.read_bytes()), run)
        self.assertIn("Save complete", w.export_status.text())
        self.assertEqual(w.library_saved, {run["run_id"]})
        self.assertTrue(w.library_rows[0].saved)
        counts = {pair.keys[0].text(): pair.keys[1].text() for pair in w.library_counts.flow.items}
        self.assertEqual((counts["Saved"], counts["Not saved"]), ("1", "0"))
        # The latest portfolio report is listed; its own page saves it, so the two exports step aside for it.
        request = {"symbols": ["ONE", "TWO"], "source": "synthetic", "objective": "max_sharpe", "max_weight": 1.0}
        w.portfolio.exports.report = make_report("portfolio", request, [
            {"type": "portfolios", "data": {"max_sharpe": {"sharpe": 0.5, "ann_return": 0.1, "ann_vol": 0.2}}}])
        w.refresh_views()
        portfolio = next(row for row in w.library_rows if row.kind == "portfolio")
        self.assertEqual(portfolio.figure, "0.500")
        w.library_select("portfolio")
        self.assertFalse(w.save_json.isEnabled())
        self.assertTrue(w.library_export_hint.isVisible())
        self.assertEqual(w.run_table.currentRow(), -1)
        w.library_select(run["run_id"])
        self.assertTrue(w.save_json.isEnabled() and w.save_bundle.isEnabled())

    def test_language_switch_and_layout_keep_every_contract(self):
        w = self.window
        self.run_mc("FAIL", fail=True)
        self.run_mc("TEST")
        runner = Mock(side_effect=AssertionError("a language switch refetches nothing"))
        w.analysis_runner = runner
        w.navigate("library")
        keys = [row.key for row in w.library_rows]
        for theme in (0, 1):
            w.theme.setCurrentIndex(theme)
            for language in ("ko", "en"):
                w.set_language(language)
                for width in (1000, 1360, 2000):
                    w.resize(width, 760)
                    self.settle()
                    with self.subTest(theme=theme, language=language, width=width):
                        self.assertEqual([row.key for row in w.library_rows], keys)
                        page = w.stack.currentWidget()
                        self.assertEqual(page.horizontalScrollBar().maximum(), 0)
                        self.assertEqual(w.library_workspace.canvas_scroll.horizontalScrollBar().maximum(), 0)
                        side = w.library_workspace.side.pages.currentWidget()
                        self.assertLessEqual(side.widget().minimumSizeHint().width(), side.viewport().width())
                        self.assert_no_cut_text(w.library_workspace)
                        lead = w.library_lead.text()
                        self.assertIn("이번 세션" if language == "ko" else "this session", lead)
        runner.assert_not_called()
        self.commentary.assert_not_called()

    def assert_no_cut_text(self, root):
        from quantgen_desktop.stock_detail_style import ElidedLabel
        for label in root.findChildren(QLabel):
            if not label.isVisible() or label.wordWrap() or not label.text() or isinstance(label, ElidedLabel):
                continue
            need = label.fontMetrics().horizontalAdvance(label.text())
            self.assertGreaterEqual(label.contentsRect().width() + 1, need, label.text())
        for button in root.findChildren(QAbstractButton):
            if button.isVisible() and button.text():
                self.assertGreaterEqual(button.width() + 1, button.sizeHint().width(), button.text())


if __name__ == "__main__":
    unittest.main()
