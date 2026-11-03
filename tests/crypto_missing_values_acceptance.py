"""§10 Crypto rework (NEW-M6-14, NEW-M6-15, NEW-M6-22): a missing value stays missing.

Before: a missing Upbit close became 0.0 (premium -100%), a missing perpetual mark or
index price gave 0% or -100%, a coin without a KRW price was valued at 0 inside a total
shown as the whole account, and an uncomputable 1-year z read +0.00. Offline fixtures
only: provider calls are replaced and sockets are refused.
"""
from datetime import date, timedelta
import math
import os
import re
import socket
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import dotenv
import numpy as np
with patch.object(dotenv, "load_dotenv", return_value=False):
    from core.crypto.analytics import kimchi_premium
    from core.research import crypto_workflow as W
    from data.crypto import crypto_client as C


def days(n, start=date(2024, 1, 1)):
    return [(start + timedelta(days=i)).isoformat() for i in range(n)]


class NoNetwork(unittest.TestCase):
    def setUp(self):
        guard = patch.object(socket.socket, "connect", side_effect=AssertionError("network forbidden"))
        guard.start(); self.addCleanup(guard.stop)


class ProviderValues(NoNetwork):
    def test_perp_premium_is_unavailable_without_both_prices(self):
        cases = {
            "both": ({"markPrice": "101", "indexPrice": "100"}, 1.0),
            "no index": ({"markPrice": "101"}, None),            # was 0.0 %
            "no mark": ({"indexPrice": "100"}, None),            # was -100 %
            "zero mark": ({"markPrice": "0", "indexPrice": "100"}, None),
            "text": ({"markPrice": "n/a", "indexPrice": "100"}, None),
        }
        for name, (reply, expected) in cases.items():
            with self.subTest(name), patch.object(C, "_get", return_value=reply):
                got = C.BinancePublic().premium_index("BTCUSDT")
            if expected is None:
                self.assertIsNone(got["premium_pct"])
                self.assertIsNone(W.perp_premium_pct(got))
            else:
                self.assertAlmostEqual(got["premium_pct"], expected)
                self.assertAlmostEqual(W.perp_premium_pct(got), expected)
        with patch.object(C, "_get", return_value={"markPrice": "1", "indexPrice": "1"}):
            got = C.BinancePublic().premium_index()
        self.assertIsNone(got["next_funding_time"])   # was 1970-01-01
        self.assertIsNone(got["last_funding_rate"])   # was 0.0, read by the AI as a 0% funding rate
        with patch.object(C, "_get", return_value={"markPrice": "1", "indexPrice": "1", "lastFundingRate": "-0.0001"}):
            self.assertEqual(C.BinancePublic().premium_index()["last_funding_rate"], -0.0001)

    def test_upbit_day_without_a_close_is_left_out(self):
        page = [{"candle_date_time_utc": f"{d}T00:00:00", "trade_price": p, "opening_price": 1, "high_price": 1,
                 "low_price": 1, "candle_acc_trade_volume": 1, "candle_acc_trade_price": 1}
                for d, p in zip(days(3), (90_000_000, None, 91_000_000))]
        older = [{"candle_date_time_utc": "2023-12-31T00:00:00", "trade_price": 89_000_000, "opening_price": 1,
                  "high_price": None, "low_price": 1, "candle_acc_trade_volume": 1, "candle_acc_trade_price": 1},
                 {"candle_date_time_utc": "2023-12-30T00:00:00", "trade_price": 88_000_000, "opening_price": 1,
                  "high_price": 1, "low_price": 1, "candle_acc_trade_volume": 1, "candle_acc_trade_price": 1}]
        with patch.object(C, "_get", side_effect=[page, older, []]) as get:
            got = C.UpbitPublic().daily("KRW-BTC", days=3)
        # Skipped days are not counted: paging goes on until three usable days.
        self.assertEqual(got.dates, ("2023-12-30", days(3)[0], days(3)[2]))
        self.assertEqual(got.close, (88_000_000.0, 90_000_000.0, 91_000_000.0))
        self.assertEqual(get.call_count, 2)

    def test_ticker_without_a_price_reports_none(self):
        with patch.object(C, "_get", return_value=[{"market": "KRW-BTC", "trade_price": None}]):
            row = C.UpbitPublic().ticker("KRW-BTC")[0]
        self.assertEqual((row["price"], row["change_pct"], row["volume_24h_krw"]), (None, None, None))
        with patch.object(C, "_get", return_value={"indexPrice": "100"}):
            probe = C.probe()["binance_futures"]
        self.assertFalse(probe["ok"]); self.assertEqual(probe["detail"], "price missing")


class Holdings(NoNetwork):
    def test_unpriced_coin_is_not_valued_and_the_total_says_partial(self):
        balances = [{"currency": "KRW", "total": 50_000.0, "avg_buy_price": 0.0},
                    {"currency": "BTC", "total": 0.01, "avg_buy_price": 80_000_000.0},
                    {"currency": "XYZ", "total": 3.0, "avg_buy_price": 10.0}]
        valued = W.value_holdings(balances, {"KRW-BTC": 90_000_000.0})
        self.assertEqual([b["krw_value"] for b in valued], [50_000.0, 900_000.0, None])  # XYZ was 0
        summary = W.holdings_summary(valued)
        self.assertEqual(summary, {"total_krw": 950_000.0, "unvalued": ["XYZ"], "complete": False})
        self.assertTrue(W.holdings_summary(valued[:2])["complete"])

    def test_one_unknown_market_does_not_erase_every_price(self):
        class Public:
            calls = []
            def ticker(self, markets):
                self.calls.append(list(markets))
                if "KRW-XYZ" in markets:
                    raise C.CryptoError("Upbit ticker: HTTP 404", status=404)
                return [{"market": m, "price": 1000.0} for m in markets]
        public = Public()
        self.assertEqual(W.krw_prices(public, ["KRW-BTC", "KRW-XYZ"]), {"KRW-BTC": 1000.0, "KRW-XYZ": None})
        self.assertEqual(public.calls, [["KRW-BTC", "KRW-XYZ"], ["KRW-BTC"], ["KRW-XYZ"]])
        self.assertEqual(W.krw_prices(public, []), {})  # KRW only: no request at all
        self.assertEqual(len(public.calls), 3)

        class Down:
            calls = 0
            def ticker(self, markets):
                Down.calls += 1
                raise C.CryptoError("Upbit ticker: HTTP 503", status=503)
        for error in (503, 429, None):  # an outage is a failed read, not "no KRW price", and is not retried per coin
            Down.calls = 0
            def ticker(self, markets, error=error):
                Down.calls += 1
                raise C.CryptoError("Upbit ticker: failed", status=error)
            Down.ticker = ticker
            with self.subTest(error), self.assertRaises(C.CryptoError):
                W.krw_prices(Down(), ["KRW-BTC", "KRW-ETH"])
            self.assertEqual(Down.calls, 1)

    def test_zero_quantity_is_worth_zero_and_cost_basis_keeps_precision(self):
        valued = W.value_holdings([{"currency": "XYZ", "total": 0.0}], {})
        self.assertEqual(valued[0]["krw_value"], 0.0)
        self.assertTrue(W.holdings_summary(valued)["complete"])
        self.assertEqual(W.cost_basis_text({"avg_buy_price": 80_000_000.0, "unit_currency": "KRW"}), "80,000,000 KRW")
        self.assertEqual(W.cost_basis_text({"avg_buy_price": 0.00002, "unit_currency": "BTC"}), "2e-05 BTC")
        self.assertEqual(W.cost_basis_text({"avg_buy_price": 1500.0}), "1,500")


class KimchiZ(NoNetwork):
    def series(self, n, premium):
        keys = days(n)
        btc = 100 * np.exp(np.cumsum(np.random.default_rng(n).normal(0, .01, n)))
        return keys, btc, dict(zip(keys, btc * 1300 * (1 + premium)))

    def test_short_history_has_no_z(self):
        keys, btc, upbit = self.series(60, np.full(60, .02))
        got = kimchi_premium(upbit, dict(zip(keys, btc)), dict(zip(keys, np.full(60, 1300.))))
        self.assertTrue(math.isnan(got.last_z))  # was 0.0, shown as +0.00
        self.assertIsNone(W.z_text(got.last_z))

    def test_flat_window_has_no_z_but_a_varying_one_is_unchanged(self):
        keys = days(200)
        flat = kimchi_premium(dict.fromkeys(keys, 132_600.0), dict.fromkeys(keys, 100.0), dict.fromkeys(keys, 1300.0))
        self.assertTrue(np.isnan(flat.z_1y).all())  # no variation: was 0.0 from index 90 on
        self.assertTrue(math.isnan(flat.last_z))
        premium = np.random.default_rng(7).normal(.02, .004, 200)
        keys, btc, upbit = self.series(200, premium)
        got = kimchi_premium(upbit, dict(zip(keys, btc)), dict(zip(keys, np.full(200, 1300.))))
        prem = (upbit[keys[-1]] / (btc[-1] * 1300.) - 1) * 100
        window = got.premium_pct[:-1]  # the 199 earlier observations; the current one is not in its own window
        self.assertAlmostEqual(got.last_z, (prem - window.mean()) / window.std(ddof=1))

    def test_missing_or_zero_prices_are_left_out_not_minus_100(self):
        keys, btc, upbit = self.series(120, np.full(120, .02))
        upbit[keys[-1]] = 0.0          # a missing Upbit close that became 0
        usd = dict(zip(keys, btc)); usd[keys[50]] = float("nan")
        fx = dict(zip(keys, np.full(120, 1300.))); fx[keys[-2]] = 0.0
        got = kimchi_premium(upbit, usd, fx)
        self.assertNotIn(keys[-1], got.dates); self.assertNotIn(keys[50], got.dates)
        self.assertTrue(np.all(np.isfinite(got.premium_pct)))
        self.assertAlmostEqual(got.last_pct, 2.0, places=6)
        self.assertGreater(got.premium_pct.min(), -50)


class Texts(NoNetwork):
    def analysis(self, z):
        out = W.analyze(source="synthetic", include_balances=False, card_loader=lambda _p: [])
        from dataclasses import replace
        out["kimchi"] = replace(out["kimchi"], last_z=z)
        out["premium_index"] = {"premium_pct": None, "mark": None, "index": 100.0}
        return out

    def test_narratives_and_payload_say_unavailable_instead_of_zero(self):
        from quantgen_desktop.market_narrative_language import crypto_korean
        a = self.analysis(float("nan"))
        en, ko = W.narrative(a), crypto_korean(a)
        self.assertIn("z unavailable", en); self.assertIn("z는 계산할 수 없습니다", ko)
        for text in (en, ko):
            self.assertIsNone(re.search(r"\bnan\b", text, re.IGNORECASE), text)
        body = W.payload(a)
        self.assertIsNone(body["kimchi"]["z"])
        self.assertIsNone(body["premium_index"]["premium_pct"])
        self.assertIn("+0.4 standard", W.narrative(self.analysis(.4)))


class NativeDisplay(NoNetwork):
    @classmethod
    def setUpClass(cls):
        from PyQt6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_crypto_pane_shows_dashes_and_a_partial_holdings_note(self):
        from dataclasses import replace
        from PyQt6.QtWidgets import QLabel, QTableWidget
        from core.research.market_analysis import CryptoRequest, execute_crypto
        import config
        with patch.object(config, "upbit_ready", return_value=False):
            out = execute_crypto(CryptoRequest(source="synthetic", include_balances=True))
        out.data["kimchi"] = replace(out.data["kimchi"], last_z=float("nan"))
        out.data["balances"] = W.value_holdings(
            [{"currency": "BTC", "total": .01, "avg_buy_price": 1.0, "unit_currency": "KRW"},
             {"currency": "XYZ", "total": 3.0, "avg_buy_price": 1.0, "unit_currency": "KRW"}],
            {"KRW-BTC": 90_000_000.0})
        with patch.object(dotenv, "load_dotenv", return_value=False):
            from quantgen_desktop.app import ResearchWindow
        window = ResearchWindow(auto_refresh=False); self.addCleanup(window.deleteLater)
        pane = window.crypto
        pane.show_result(out)
        cells = {}
        for table in pane.findChildren(QTableWidget):
            for row in range(table.rowCount()):
                cells[table.item(row, 0).text()] = [table.item(row, c).text() for c in range(1, table.columnCount())]
        self.assertEqual(cells["Premium z"], ["—"])
        self.assertEqual(cells["XYZ"][-1], "—")          # was 0.0000
        self.assertEqual(cells["BTC"][1], "1 KRW")  # the cost basis names its currency
        notes = " ".join(label.text() for label in pane.findChildren(QLabel))
        self.assertIn("No KRW price for XYZ", notes)
        # The note names held coins, so like the holdings table it stays out of AI commentary (NEW-M6-18).
        import json
        from quantgen_desktop.commentary import commentary_payload
        pane.bind_output("crypto", out)  # the tool name
        sent = json.dumps(commentary_payload(pane.report), ensure_ascii=False)
        self.assertNotIn("XYZ", sent)  # the unpriced holding's name is not sent
        self.assertIn("Premium / volatility", sent)  # market results are still sent


if __name__ == "__main__":
    unittest.main()
