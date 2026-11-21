"""Focused synthetic StockDetail render glue, real Qt and real insights panel.

The actual render_sections/set_locale/set_theme method ASTs and display helpers
are compiled unchanged from stock_detail.py. Header/chart/watchlist recipients
are lightweight recording adapters: no ResearchWindow, worker, price history,
model, provider or account is constructed. The active-chart refresh branch and
production FoldSection widget layout remain covered by the existing desktop suite.
Run under the reviewed isolated harness; module import alone starts nothing.
"""
from __future__ import annotations

import ast
import copy
from pathlib import Path
from types import SimpleNamespace
import unittest


def _actual_glue_class():
    from PyQt6.QtWidgets import QWidget
    from core.theme import DARK, LIGHT
    from quantgen_desktop.stock_detail_style import polite, sheet, text

    source = Path(__file__).resolve().parents[1] / "quantgen_desktop/stock_detail.py"
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    helpers = {"_lang", "key_figures_first", "_trim", "korean_amount", "korean_value",
               "korean_times", "term_tip", "display_row"}
    constants = {"KEY_FIGURE_ORDER", "_SCALE", "TERM_TIPS"}
    nodes = [node for node in tree.body if
             isinstance(node, ast.FunctionDef) and node.name in helpers or
             isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in constants
                                                 for t in node.targets)]
    actual = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "StockDetailView")
    methods = [node for node in actual.body if isinstance(node, ast.FunctionDef) and
               node.name in {"render_sections", "_clear_sections", "set_locale", "set_theme"}]
    assert len(methods) == 4 and len(nodes) == len(helpers) + len(constants)
    # No statement/body transformation. Only the enclosing class is a thin Qt fixture.
    adapter = ast.ClassDef(name="ActualStockDetailGlue", bases=[ast.Name(id="QWidget", ctx=ast.Load())],
                           keywords=[], body=methods, decorator_list=[])
    module = ast.fix_missing_locations(ast.Module(body=[*nodes, adapter], type_ignores=[]))
    namespace = {"__name__": "quantgen_desktop._stock_detail_glue_contract",
                 "__package__": "quantgen_desktop", "QWidget": QWidget,
                 "DARK": DARK, "LIGHT": LIGHT, "polite": polite, "sheet": sheet, "text": text}
    exec(compile(module, str(source), "exec"), namespace)
    return namespace["ActualStockDetailGlue"]


def _profile():
    from core.market.models import Instrument
    from core.research.stock_profile import StockProfile

    windows = {}
    for length in (5, 20):
        windows[length] = {"first_date": "2026-11-02", "last_date": "2026-11-20",
                           "foreign": 12.0, "institution": -8.0, "individual": -4.0,
                           "reported": dict.fromkeys(("foreign", "institution", "individual"), length)}
    return StockProfile(
        Instrument(), name="Synthetic", name_en="Synthetic", currency="KRW", last_price=100.0,
        price_basis="quote", as_of="2026-11-20", adjusted=True,
        values={"key_figures": {"basis": "quote", "per": 13.2, "pbr": 1.1, "eps": 1100.0,
                                 "bps": 16000.0, "market_cap": 100000.0, "listed_shares": 1000,
                                 "sector": "전기전자", "open": 99.0, "high": 101.0,
                                 "low": 98.0, "volume": 500.0},
                "flows": {"windows": windows},
                "short_selling": {"latest": {"date": "2026-11-20", "short_ratio_pct": 2.5,
                                               "short_qty": 20.0},
                                  "average": {"sessions": 20, "first_date": "2026-11-02",
                                              "last_date": "2026-11-20", "short_ratio_pct": 2.0,
                                              "short_qty": 15.0, "reported_ratio": 20, "reported_qty": 20}},
                "risk": {"ann_vol": .2, "max_drawdown": -.1, "var_level": .975, "var_1d": .03,
                         "cvar_1d": .04, "best_day": .02, "worst_day": -.03,
                         "positive_days": .6, "engine": "fixed_fixture"}},
        sources=dict.fromkeys(("quote", "history", "flows", "short_selling"), "KIS REST"),
        fetched=dict.fromkeys(("quote", "history", "flows", "short_selling"),
                              "2026-11-21T14:00:00+00:00"),
        reasons={"range": "insufficient_history", "returns": "insufficient_history",
                 "signals": "insufficient_history", "indicators": "insufficient_history",
                 "orderbook": "not_provided", "executions": "not_provided"})


def _fixture():
    from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
    from core.theme import LIGHT
    from quantgen_desktop.stock_insights import StockInsightsPanel

    class RecordedSection(QWidget):
        """Rendering recipient only; actual production glue chooses all rows."""
        def __init__(self, parent):
            super().__init__(parent)
            self.title = QLabel(self)
            self.rows, self.note = (), ""

        def set_title(self, value):
            self.title.setText(value)

        def set_rows(self, rows, **kwargs):
            self.rows, self.note = tuple(rows), kwargs.get("note", "")

        def set_theme(self, dark):
            self.dark = bool(dark)

    class Recipient:
        def __getattr__(self, name):
            if name not in {"translate", "set_locale", "set_theme"}:
                raise AssertionError("unexpected recipient " + name)
            return lambda *args, **kwargs: None

    class Fixture(_actual_glue_class()):
        def __init__(self):
            super().__init__()
            self.ctx, self.dark, self.palette = SimpleNamespace(language="ko"), False, LIGHT
            self.profile, self.instrument, self.completer = _profile(), None, None
            self.side = QWidget(self)
            self.side.sections = {key: RecordedSection(self.side) for key in
                                  ("key_figures", "range", "risk", "technical", "supply")}
            self.side.unavailable = QLabel(self.side)
            self.side.watchlist = Recipient()
            self.insights = StockInsightsPanel(self.side)
            layout = QVBoxLayout(self)
            layout.addWidget(self.side)
            column = QVBoxLayout(self.side)
            column.addWidget(self.insights)
            for section in self.side.sections.values():
                column.addWidget(section)
            column.addWidget(self.side.unavailable)
            self.risk, self.mark, self.picker = Recipient(), Recipient(), Recipient()
            self.notes = SimpleNamespace(isHidden=lambda: True)
            self.chart = SimpleNamespace(chart=SimpleNamespace(months=(), theme={}), detail=False)
            self.fetch_calls = []

        def _technical_rows(self):
            return []  # Indicator engines are outside this render-glue fixture.

        def _toolbar_texts(self): pass
        def _sync_interval(self, **kwargs): pass
        def _sync_watch(self): pass
        def render_header(self): pass
        def _sync_periods(self): pass
        def _render_qscore(self): pass

        def load_profile(self, *args, **kwargs):
            self.fetch_calls.append((args, kwargs))
            raise AssertionError("rendering must not request a profile")

    return Fixture()


class StockInsightsGlueAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PyQt6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.view = _fixture()
        self.view.show()
        self.app.processEvents()

    def tearDown(self):
        self.view.close()
        self.view.deleteLater()
        self.app.processEvents()

    def test_actual_render_glue_deduplicates_only_covered_data_and_keeps_fallback(self):
        from PyQt6.QtWidgets import QLabel
        view, original = self.view, self.view.profile
        snapshot = copy.deepcopy((original.values, original.sources, original.fetched, original.reasons))
        view.render_sections()
        self.assertEqual(view.insights.covered_sections, frozenset({"flows", "short_selling"}))
        self.assertEqual(view.insights.covered_key_figures, frozenset({"per", "pbr"}))
        self.assertFalse(view.side.sections["supply"].isVisibleTo(view.side))
        labels = {row.label for row in view.side.sections["key_figures"].rows}
        self.assertFalse({"PER", "PBR"} & labels)
        self.assertTrue({"EPS", "BPS", "업종", "상장 주식 수", "시가총액 (계산값)"}.issubset(labels))
        per = [w for w in view.insights.findChildren(QLabel) if w.property("insightRole") == "value"
               and w.toolTip().startswith("PER —")]
        self.assertEqual(len(per), 1)
        self.assertEqual(per[0].text(), "13.20배")
        self.assertIn(original.sources["quote"], per[0].toolTip())
        self.assertIn(original.fetched["quote"], per[0].toolTip())
        self.assertEqual({row["group"]: row["net_qty"] for row in view.insights.model["flows"]},
                         {"foreign": 12.0, "institution": -8.0, "individual": -4.0})
        self.assertTrue(all(row["buy_fraction"] is None for row in view.insights.model["flows"]))
        self.assertEqual(view.insights.model["shorts"]["ratio_pct"], 2.5)
        self.assertEqual(snapshot, (original.values, original.sources, original.fetched, original.reasons))

        partial = copy.deepcopy(original)
        partial.values.pop("short_selling")
        partial.reasons["short_selling"] = "not_provided"
        view.profile = partial
        view.render_sections()
        self.assertEqual(view.insights.covered_sections, frozenset({"flows"}))
        self.assertIn("공매도", view.side.unavailable.toolTip())
        self.assertTrue(view.side.unavailable.isVisibleTo(view.side))

        missing = copy.deepcopy(partial)
        missing.values.pop("flows")
        missing.values["key_figures"].update(per=None, pbr=None)
        missing.reasons["flows"] = "no_observations"
        view.profile = missing
        view.render_sections()
        self.assertEqual(view.insights.covered_sections, frozenset())
        self.assertEqual(view.insights.covered_key_figures, frozenset())
        self.assertIn("EPS", {row.label for row in view.side.sections["key_figures"].rows})
        self.assertIn("투자자별 순매수", view.side.unavailable.toolTip())
        metrics = view.insights.model["metrics"]
        self.assertTrue(all(row["value"] is None for row in metrics))
        self.assertTrue(all(row["status"] == "unavailable" for row in metrics))

        view.profile = None
        view.render_sections()
        self.assertIsNone(view.insights.model)
        self.assertEqual(view.insights.body.count(), 0)
        self.assertEqual(view.side.sections["key_figures"].rows, ())
        view.profile = original
        view.render_sections()
        self.assertEqual(view.insights.covered_sections, frozenset({"flows", "short_selling"}))
        self.assertEqual(view.fetch_calls, [])

    def test_actual_locale_theme_glue_rerenders_fixed_profile_without_refetch(self):
        from PyQt6.QtWidgets import QLabel
        from core.theme import DARK, LIGHT
        view = self.view
        original = copy.deepcopy((view.profile.values, view.profile.sources, view.profile.fetched))
        view.render_sections()
        view.set_locale(SimpleNamespace(language="en"))
        view.set_theme(True)
        self.app.processEvents()
        self.assertEqual(view.insights.language, "en")
        self.assertTrue(view.insights.dark)
        self.assertIn(DARK.surface, view.insights.styleSheet())
        self.assertTrue(any(w.text() == "Valuation at a glance" for w in view.insights.findChildren(QLabel)))
        per = [w for w in view.insights.findChildren(QLabel) if w.property("insightRole") == "value"
               and w.toolTip().startswith("PER —")]
        self.assertEqual([w.text() for w in per], ["13.20x"])
        self.assertNotIn("PER", {row.label for row in view.side.sections["key_figures"].rows})
        risk_labels = {row.label for row in view.side.sections["risk"].rows}
        self.assertIn("1-day VaR 97.5%", risk_labels)
        self.assertIn("1-day CVaR 97.5%", risk_labels)
        view.set_locale(SimpleNamespace(language="ko"))
        view.set_theme(False)
        self.app.processEvents()
        self.assertIn(LIGHT.surface, view.insights.styleSheet())
        self.assertTrue(any(w.text() == "기업 가치 한눈에" for w in view.insights.findChildren(QLabel)))
        self.assertEqual(original, (view.profile.values, view.profile.sources, view.profile.fetched))
        self.assertEqual(view.fetch_calls, [])


if __name__ == "__main__":
    unittest.main()
