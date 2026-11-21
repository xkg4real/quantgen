"""Synthetic injected stock-detail contracts. Run only under the reviewed isolated harness.

No provider/client constructor, real model/history, credentials, endpoint or account
is used. Empty price history intentionally keeps existing research computations out.
"""
import copy
from types import SimpleNamespace
import unittest

from core.market.detail_insights import (build_insights, normalize_executions,
                                         normalize_orderbook, peer_comparison)
from core.market.models import Instrument
from core.research.stock_profile import build_profile, load_profile
from data.krx.kis_client import KISClient, KISError, Quote, check_quotation_path
from data.kis_markets import KISMarkets


RECEIVED = "2026-11-21T14:00:00+00:00"
BOOK = {"output1": {"aspr_acpt_hour": "123456", "askp1": "101", "askp_rsqn1": "10",
                    "bidp1": "100", "bidp_rsqn1": "20", "total_askp_rsqn": "10", "total_bidp_rsqn": "20"},
        "output2": {"antc_cnpr": "99", "antc_vol": "30"}}
TRADES = {"output": [{"stck_cntg_hour": "123456", "stck_prpr": "100", "cntg_vol": "3", "tday_rltv": "123.45"}]}


def quote():
    return Quote("005930", "Synthetic", 100, 1, 1, 20, None, 101, 99, 99,
                 source="KIS", as_of=RECEIVED, per=10, pbr=1.5, bps=60)


def profile(**kwargs):
    return build_profile(Instrument(), candles=(), quote=quote(), **kwargs)


class DetailInsightsAcceptance(unittest.TestCase):
    def test_same_quote_response_adds_optional_pbr_without_extra_call(self):
        client = object.__new__(KISClient)
        calls = []
        def get(*args, **kwargs):
            calls.append((args, kwargs))
            return {"output": {"stck_prpr": "100", "per": "10", "pbr": "1.5", "bps": "60", "lstn_stcn": "1,000"}}
        client._get = get
        result = client.quote("005930")
        self.assertEqual((result.per, result.pbr, result.bps), (10, 1.5, 60))
        self.assertEqual(len(calls), 1)
        self.assertIs(calls[0][1]["retry"], False)
        old = Quote("005930", "Old", 100, None, None, None, None, None, None, None)
        self.assertIsNone(old.pbr)
        self.assertIsNone(old.bps)

    def test_investor_same_payload_keeps_gross_and_net_separate(self):
        markets = object.__new__(KISMarkets)
        calls = []
        def get(*args, **kwargs):
            calls.append(args[0])
            return {"output2": [{"stck_bsop_date": "20261120", "frgn_ntby_qty": "7",
                                  "frgn_shnu_vol": "10", "frgn_seln_vol": "4",
                                  "prsn_shnu_vol": "20", "prsn_seln_vol": "9",
                                  "orgn_shnu_vol": "30", "orgn_seln_vol": "12"}]}
        markets._get = get
        row = markets.investor_daily("005930", days=1)[0]
        self.assertEqual(len(calls), 1)
        self.assertEqual((row["foreign_net_qty"], row["foreign_buy_qty"], row["foreign_sell_qty"]), (7, 10, 4))
        self.assertEqual((row["individual_buy_qty"], row["institution_sell_qty"]), (20, 12))

    def test_two_new_rest_methods_each_make_one_nonretry_attempt(self):
        client = object.__new__(KISClient)
        calls = []
        def get(path, tr, params, **kwargs):
            calls.append((path, tr, params, kwargs))
            return BOOK if "asking" in path else TRADES
        client._get = get
        self.assertIsNotNone(client.orderbook("005930"))
        self.assertIsNotNone(client.executions("005930"))
        self.assertEqual([r[1] for r in calls], ["FHKST01010200", "FHKST01010300"])
        self.assertTrue(all(r[3] == {"retry": False} for r in calls))
        self.assertTrue(all(r[2] == {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": "005930"} for r in calls))

    def test_exact_readonly_boundary_still_refuses_account_order_finance(self):
        path = "/uapi/domestic-stock/v1/quotations/inquire-ccnl"
        self.assertEqual(check_quotation_path(path), path)
        for bad in ("/uapi/domestic-stock/v1/trading/order-cash", "/oauth2/tokenP",
                    "/uapi/domestic-stock/v1/finance/financial-ratio", "/uapi/account", "/uapi/domestic-stock/v1/quotations/unknown"):
            with self.subTest(path=bad), self.assertRaises(KISError):
                check_quotation_path(bad)

    def test_depth_keeps_provider_clock_receipt_and_expected_distinct(self):
        value = normalize_orderbook(BOOK, received_at=RECEIVED)
        self.assertEqual((value["provider_time"], value["market_date"], value["received_at"]), ("123456", "", RECEIVED))
        self.assertEqual(value["levels"][0]["ask_price"], 101)
        self.assertEqual(value["expected"]["price"], 99)
        self.assertEqual(len(value["levels"]), 10)
        self.assertEqual(value, normalize_orderbook(value))

    def test_depth_never_fills_missing_size_or_nonfinite_price_with_zero(self):
        raw = {"output1": {"askp1": "100", "askp_rsqn1": "", "bidp1": "nan", "bidp_rsqn1": "2"}}
        self.assertIsNone(normalize_orderbook(raw))
        raw["output1"].update(bidp1="99", bidp_rsqn1="0", aspr_acpt_hour="256199")
        value = normalize_orderbook(raw)
        self.assertEqual(value["levels"][0]["bid_qty"], 0)
        self.assertIsNone(value["levels"][0]["ask_price"])
        self.assertEqual(value["provider_time"], "")

    def test_execution_strength_is_provider_value_not_percent_or_forecast(self):
        value = normalize_executions(TRADES, received_at=RECEIVED)
        self.assertEqual(value["rows"][0]["strength"], 123.45)
        self.assertEqual(value["strength_unit"], "provider value")
        self.assertEqual(value["market_date"], "")
        self.assertEqual(value["kind"], "REST snapshot")
        self.assertEqual(value, normalize_executions(value))

    def test_execution_rejects_invalid_trade_but_retains_zero_strength(self):
        data = {"output": [{"stck_prpr": "100", "cntg_vol": "-1", "tday_rltv": "20"},
                           {"stck_prpr": "100", "cntg_vol": "0", "tday_rltv": "0"},
                           {"stck_prpr": "100", "cntg_vol": "1", "tday_rltv": "inf"}]}
        rows = normalize_executions(data)["rows"]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["strength"], 0)
        self.assertIsNone(rows[1]["strength"])

    def test_gross_percentage_uses_same_day_pairs_and_reports_coverage(self):
        flows = [{"date": "2026-11-19", "foreign_net_qty": 5, "foreign_buy_qty": 10, "foreign_sell_qty": 4},
                 {"date": "2026-11-20", "foreign_net_qty": -2, "foreign_buy_qty": 20}]
        p = profile(flows=flows)
        row = next(r for r in build_insights(p)["flows"] if r["group"] == "foreign")
        self.assertEqual(row["net_qty"], 3)  # not overwritten by the different gross-pair subset
        self.assertEqual((row["buy_qty"], row["sell_qty"], row["reported_pairs"], row["sessions"]), (10, 4, 1, 2))
        self.assertAlmostEqual(row["buy_fraction"], 10 / 14)
        self.assertEqual((row["first_date"], row["last_date"]), ("2026-11-19", "2026-11-20"))

    def test_zero_denominator_and_negative_or_missing_gross_are_unavailable(self):
        p = profile(flows=[{"date": "2026-11-20", "individual_net_qty": 0, "individual_buy_qty": 0,
                            "individual_sell_qty": 0, "foreign_buy_qty": -1, "foreign_sell_qty": 3}])
        rows = {r["group"]: r for r in build_insights(p)["flows"]}
        self.assertIsNone(rows["individual"]["buy_fraction"])
        self.assertEqual(rows["individual"]["net_qty"], 0)
        self.assertEqual(rows["foreign"]["reported_pairs"], 0)

    def test_existing_net_only_profile_keeps_signed_shares(self):
        p = profile(flows=[{"date": "2026-11-20", "foreign_net_qty": -8}])
        row = next(r for r in build_insights(p)["flows"] if r["group"] == "foreign")
        self.assertEqual(row["net_qty"], -8)
        self.assertIsNone(row["buy_fraction"])

    def test_profile_short_percentage_is_not_multiplied_by100(self):
        p = profile(shorts=[{"date": "2026-11-20", "short_qty": 2, "short_ratio_pct": 1.45, "volume": 100}])
        self.assertEqual(build_insights(p)["shorts"]["ratio_pct"], 1.45)
        invalid = profile(shorts=[{"date": "2026-11-20", "short_qty": -2, "short_ratio_pct": 145, "volume": 100}])
        self.assertIsNone(build_insights(invalid)["shorts"]["ratio_pct"])
        self.assertIsNone(build_insights(invalid)["shorts"]["qty"])

    def test_load_budget_and_legacy_optional_methods(self):
        calls = []
        class Client:
            ready = True
            def quote(self, code): calls.append("quote"); return quote()
            def orderbook(self, code): calls.append("orderbook"); return normalize_orderbook(BOOK, received_at=RECEIVED)
            def executions(self, code): calls.append("executions"); return normalize_executions(TRADES, received_at=RECEIVED)
        p = load_profile(Instrument(), router=None, quote_client=Client())
        self.assertEqual(calls, ["quote", "orderbook", "executions"])
        self.assertIsNotNone(build_insights(p)["orderbook"])
        legacy = SimpleNamespace(ready=True, quote=lambda code: quote())
        p = load_profile(Instrument(), router=None, quote_client=legacy)
        self.assertEqual(p.reasons["orderbook"], "not_provided")
        self.assertEqual(p.last_price, 100)

    def test_optional_failure_unready_and_overseas_do_not_trigger_more_calls(self):
        calls = []
        class Client:
            ready = True
            def quote(self, code): return quote()
            def orderbook(self, code): calls.append("orderbook"); raise RuntimeError("DO_NOT_DISPLAY_PROVIDER_TEXT")
            def executions(self, code): calls.append("executions"); return TRADES
        c = Client()
        p = load_profile(Instrument(), router=None, quote_client=c)
        self.assertEqual(calls, ["orderbook", "executions"])
        self.assertEqual(p.last_price, 100)
        self.assertNotIn("DO_NOT_DISPLAY_PROVIDER_TEXT", repr((p.values, p.reasons, p.errors)))
        c.ready = False
        load_profile(Instrument(), router=None, quote_client=c)
        load_profile(Instrument("overseas_stock", "AAPL", "NAS"), router=None, quote_client=Client())
        self.assertEqual(calls, ["orderbook", "executions"])

    def test_no_roe_psr_or_theme_average_from_unrelated_supplied_numbers(self):
        p = profile()
        p.values["key_figures"].update(roe=20, psr=5, sps=50)
        model = build_insights(p)
        self.assertEqual([m["value"] for m in model["metrics"]], [10, 1.5, None, None])
        self.assertEqual(model["comparison"]["status"], "unavailable")

    def test_displayed_gross_split_totals100_without_changing_raw_fraction(self):
        from decimal import Decimal
        from quantgen_desktop.stock_insights import display_split
        for fraction, expected in ((1 / 2000, ("0.1%", "99.9%")),
                                   (1999 / 2000, ("100.0%", "0.0%")),
                                   (0, ("0.0%", "100.0%")), (1, ("100.0%", "0.0%")),
                                   (0.5, ("50.0%", "50.0%"))):
            with self.subTest(fraction=fraction):
                before = fraction
                result = display_split(fraction)
                self.assertEqual(result, expected)
                self.assertEqual(sum(Decimal(v.rstrip("%")) for v in result), Decimal("100.0"))
                self.assertEqual(fraction, before)
        for invalid in (None, float("nan"), float("inf"), -0.1, 1.1, True):
            self.assertEqual(display_split(invalid), (None, None))

    def test_peer_mean_requires_verified_matching_metadata_and_excludes_negative_pe(self):
        meta = {"metric": "per", "unit": "x", "period": "FY2025", "basis": "synthetic matched basis", "as_of": "2026-11-20"}
        data = dict(meta, membership={"verified": True, "kind": "theme", "id": "synthetic", "source": "test",
                                     "proof": "synthetic-only", "as_of": "2026-11-20", "members": ["A", "B", "C"]},
                    observations=[dict(meta, member=k, value=n, source="test") for k, n in (("A", 10), ("B", 20), ("C", -5))])
        before = copy.deepcopy(data)
        value = peer_comparison(data)
        self.assertEqual((value["mean"], value["included"], value["total"], value["kind"]), (15, 2, 3, "theme"))
        self.assertEqual(data, before)
        data["membership"]["verified"] = False
        self.assertIsNone(peer_comparison(data)["mean"])

    def test_peer_mismatched_period_and_duplicate_ids_do_not_make_an_average(self):
        meta = {"metric": "per", "unit": "x", "period": "FY2025", "basis": "synthetic", "as_of": "2026-11-20"}
        data = dict(meta, membership={"verified": True, "kind": "sector", "id": "industry", "source": "test", "proof": "test",
                                     "as_of": "2026-11-20", "members": ["A", "B"]},
                    observations=[dict(meta, member="A", value=10, source="test"), dict(meta, member="B", value=20, source="test", period="Q12026")])
        self.assertIsNone(peer_comparison(data)["mean"])
        data["observations"].append(dict(meta, member="A", value=30, source="test"))
        self.assertEqual(peer_comparison(data)["reason"], "duplicate_peer")

    def test_panel_renders_injected_input_changes_language_and_clears(self):
        from PyQt6.QtWidgets import QApplication, QLabel
        from quantgen_desktop.stock_insights import StockInsightsPanel
        from core.theme import DARK, LIGHT
        from quantgen_desktop.typography import mix
        app = QApplication.instance() or QApplication([])
        panel = StockInsightsPanel()
        p = profile(orderbook=BOOK, executions=TRADES)
        panel.set_profile(p, language="ko")
        self.assertTrue(any("기업 가치" in label.text() for label in panel.findChildren(QLabel)))
        self.assertIn(LIGHT.surface, panel.styleSheet())
        self.assertIn(LIGHT.text, panel.styleSheet())
        self.assertIn(mix(LIGHT.border, LIGHT.bg, 0.5), panel.styleSheet())
        self.assertEqual(panel.covered_key_figures, frozenset({"per", "pbr"}))
        self.assertNotIn("flows", panel.covered_sections)
        panel.set_profile(p, language="en", dark=True)
        self.assertTrue(any("Valuation" in label.text() for label in panel.findChildren(QLabel)))
        self.assertIn(DARK.surface, panel.styleSheet())
        self.assertIn(DARK.text, panel.styleSheet())
        panel.set_profile(None)
        self.assertIsNone(panel.model)
        self.assertEqual(panel.body.count(), 0)
        panel.close()
        app.processEvents()


if __name__ == "__main__":
    unittest.main()
