"""DS-H: load_home_indicators -- six Home rows with history, display rights and live values. Offline fakes only."""
from __future__ import annotations

import unittest
from datetime import date, timedelta
from types import SimpleNamespace as N
from unittest import mock

from core.research import markets
from core.research.markets import SPECS, load_home_indicators

TODAY = date(2026, 11, 19)
IDS = [s[1] for s in SPECS]


def series(source, n=40, last=TODAY, start=100.0, note=""):
    dates = tuple((last - timedelta(days=n - 1 - i)).isoformat() for i in range(n))
    return N(source=source, dates=dates, values=tuple(start + i for i in range(n)), note=note)


def good_batch(ids, source, days):
    return {i: series("YFINANCE" if i in ("^GSPC", "^KS11", "BTC-USD") else "FRED") for i in ids}


class Calls:
    def __init__(self, fn=good_batch):
        self.fn, self.calls = fn, []

    def __call__(self, ids, *, source, days):
        self.calls.append((tuple(ids), source, days))
        return self.fn(ids, source, days)


def btc_ok():
    return {"value": 131_000_000.0, "change_pct": 1.5, "as_of": "2026-11-19T01:00:00+00:00"}


def kospi_ok():
    return {"value": 2_650.5, "change_pct": -0.4, "as_of": "2026-11-19T01:00:00+00:00"}


def run(**kw):
    kw.setdefault("series_loader", Calls())
    kw.setdefault("btc_live", btc_ok)
    kw.setdefault("kospi_live", kospi_ok)
    kw.setdefault("kis_ready", lambda: True)
    kw.setdefault("today", TODAY)
    return load_home_indicators(**kw)


class Batching(unittest.TestCase):
    def test_one_loader_call_for_all_six(self):
        loader = Calls()
        rows = run(series_loader=loader, days=60)
        self.assertEqual(len(loader.calls), 1)
        self.assertEqual(loader.calls[0], (tuple(IDS), "auto", 60))
        self.assertEqual([r["symbol"] for r in rows], IDS)

    def test_minimum_days(self):
        loader = Calls()
        run(series_loader=loader, days=2)
        self.assertEqual(loader.calls[0][2], 5)


class Rows(unittest.TestCase):
    def test_values_history_and_change(self):
        rows = {r["symbol"]: r for r in run(days=30)}
        gspc = rows["^GSPC"]
        self.assertEqual(gspc["status"], "OBSERVED")
        self.assertEqual(gspc["value"], 139.0)
        self.assertAlmostEqual(gspc["change"], (139 / 138 - 1) * 100)
        self.assertEqual(len(gspc["history"]), 30)
        self.assertEqual(gspc["history"][-1], {"date": TODAY.isoformat(), "value": 139.0})
        self.assertEqual(rows["DGS10"]["change"], 100.0)          # percent series: bp-style x100 like load_markets
        self.assertEqual(rows["DEXKOUS"]["delay"], "daily")
        self.assertEqual(gspc["delay"], "delayed_daily")

    def test_display_rights_per_row(self):
        rows = {r["symbol"]: r for r in run()}
        self.assertEqual(rows["^GSPC"]["display"]["outcome"], "rights_replace")
        self.assertEqual(rows["VIXCLS"]["display"]["policy"], "cboe")
        self.assertEqual(rows["DGS10"]["display"]["outcome"], "rights_conditional")
        self.assertFalse(rows["^GSPC"]["display"]["publication_authorization"])

    def test_stale(self):
        def old(ids, source, days):
            return {i: series("YFINANCE" if i[0] in "^B" else "FRED", last=TODAY - timedelta(days=10)) for i in ids}
        self.assertTrue(all(r["status"] == "STALE" for r in run(series_loader=Calls(old))))

    def test_future_observation_rejected(self):
        def future(ids, source, days):
            return {i: series("YFINANCE" if i[0] in "^B" else "FRED", last=TODAY + timedelta(days=1)) for i in ids}
        rows = run(series_loader=Calls(future))
        self.assertTrue(all(r["status"] == "UNAVAILABLE" and r["value"] is None for r in rows))


class NoSyntheticValues(unittest.TestCase):
    def test_simulated_series_is_unavailable(self):
        def degraded(ids, source, days):
            out = good_batch(ids, source, days)
            out["^GSPC"] = series("SYNTHETIC", note="YFINANCE failed: YFRateLimitError: Too Many Requests; simulated series.")
            out["VIXCLS"] = series("SYNTHETIC", note="FRED failed: ConnectionError: x; simulated series.")
            return out
        rows = {r["symbol"]: r for r in run(series_loader=Calls(degraded))}
        for sym, reason in (("^GSPC", "rate_limited"), ("VIXCLS", "network_error")):
            self.assertEqual(rows[sym]["status"], "UNAVAILABLE")
            self.assertIsNone(rows[sym]["value"])
            self.assertEqual(rows[sym]["history"], [])
            self.assertEqual(rows[sym]["reason_code"], reason)
            self.assertEqual(rows[sym]["error_code"], "ProviderFallback")
        self.assertEqual(rows["DGS10"]["status"], "OBSERVED")

    def test_gateway_off_note(self):
        def off(ids, source, days):
            out = good_batch(ids, source, days)
            out["^KS11"] = series("SYNTHETIC", note="yahoo is off in profile commercial; simulated series.")
            return out
        row = {r["symbol"]: r for r in run(series_loader=Calls(off))}["^KS11"]
        self.assertEqual(row["reason_code"], "connection_not_configured")

    def test_whole_batch_failure(self):
        def boom(ids, source, days):
            raise ConnectionError("https://example?api_key=SECRET")
        rows = run(series_loader=Calls(boom))
        self.assertTrue(all(r["status"] == "UNAVAILABLE" and r["reason_code"] == "network_error" for r in rows))
        self.assertFalse(any("SECRET" in repr(r) for r in rows))

    def test_missing_id(self):
        def partial(ids, source, days):
            out = good_batch(ids, source, days)
            out.pop("DEXKOUS")
            return out
        row = {r["symbol"]: r for r in run(series_loader=Calls(partial))}["DEXKOUS"]
        self.assertEqual((row["status"], row["reason_code"]), ("UNAVAILABLE", "invalid_response"))

    def test_non_finite_points_dropped_not_filled(self):
        def nan(ids, source, days):
            out = good_batch(ids, source, days)
            s = out["^GSPC"]
            out["^GSPC"] = N(source=s.source, dates=s.dates, values=s.values[:-1] + (float("nan"),), note="")
            return out
        row = {r["symbol"]: r for r in run(series_loader=Calls(nan))}["^GSPC"]
        self.assertEqual(row["value"], 138.0)
        self.assertEqual(len(row["history"]), 30)                 # 39 finite points left, last 30 kept
        self.assertEqual(row["history"][-1]["value"], 138.0)
        self.assertNotIn(TODAY.isoformat(), [p["date"] for p in row["history"]])


class Live(unittest.TestCase):
    def test_only_btc_and_kospi_have_live(self):
        rows = {r["symbol"]: r for r in run()}
        self.assertEqual({s for s, r in rows.items() if r["live"] is not None}, {"^KS11", "BTC-USD"})

    def test_btc_live_is_krw_and_separate_from_usd_history(self):
        row = {r["symbol"]: r for r in run()}["BTC-USD"]
        self.assertEqual(row["unit"], "USD")
        self.assertEqual((row["live"]["unit"], row["live"]["source"], row["live"]["status"]), ("KRW", "UPBIT", "LIVE"))
        self.assertEqual(row["live"]["value"], 131_000_000.0)
        self.assertEqual(row["live"]["display_outcome"], "rights_verify")
        self.assertEqual(row["value"], 139.0)                       # daily USD value untouched

    def test_kospi_live_needs_user_key_and_is_not_called_without(self):
        called = []
        rows = {r["symbol"]: r for r in run(kis_ready=lambda: False, kospi_live=lambda: called.append(1))}
        self.assertEqual(rows["^KS11"]["live"]["status"], "KEY_NEEDED")
        self.assertIsNone(rows["^KS11"]["live"]["value"])
        self.assertEqual(called, [])

    def test_kospi_live_with_key(self):
        live = {r["symbol"]: r for r in run()}["^KS11"]["live"]
        self.assertEqual((live["status"], live["value"], live["source"]), ("LIVE", 2650.5, "KIS"))

    def test_live_failure_keeps_daily_row(self):
        def fail():
            raise TimeoutError("read timed out")
        row = {r["symbol"]: r for r in run(btc_live=fail)}["BTC-USD"]
        self.assertEqual(row["status"], "OBSERVED")
        self.assertEqual((row["live"]["status"], row["live"]["reason_code"]), ("UNAVAILABLE", "network_timeout"))

    def test_bad_live_value_rejected(self):
        for bad in ({"value": None}, {"value": 0}, {"value": float("inf")}):
            row = {r["symbol"]: r for r in run(btc_live=lambda bad=bad: bad)}["BTC-USD"]
            self.assertEqual(row["live"]["status"], "UNAVAILABLE")
            self.assertIsNone(row["live"]["value"])

    def test_live_off(self):
        self.assertTrue(all(r["live"] is None for r in run(live=False)))


class DefaultsGoThroughGateway(unittest.TestCase):
    def test_default_loaders_use_gateway_entry_points(self):
        from core import gateway
        fake_ficc = mock.Mock()
        fake_ficc.load_many.side_effect = lambda ids, source, days: good_batch(ids, source, days)
        upbit = mock.Mock()
        upbit.ticker.return_value = [{"price": 1.0e8, "change_pct": 0.5, "as_of": "t"}]
        cc = N(UpbitPublic=lambda: upbit)
        kis = mock.Mock()
        kis.index.return_value = {"level": 2600.0, "change_pct": 0.1, "as_of": "t"}
        kis_mod = N(requests=object(), KISClient=lambda: kis)

        def provider(module, source=None):
            return {"data.crypto.crypto_client": cc, "data.krx.kis_client": kis_mod}[module]

        with mock.patch.object(gateway, "ficc", return_value=fake_ficc), \
                mock.patch.object(gateway, "provider", side_effect=provider) as prov, \
                mock.patch.object(gateway, "keys_ready", return_value=True):
            rows = {r["symbol"]: r for r in load_home_indicators(30, today=TODAY)}
        fake_ficc.load_many.assert_called_once()
        self.assertEqual(rows["BTC-USD"]["live"]["value"], 1.0e8)
        self.assertEqual(rows["^KS11"]["live"]["value"], 2600.0)
        kis.index.assert_called_once_with("KOSPI")
        self.assertIn(mock.call("data.crypto.crypto_client", source="crypto_public"), prov.call_args_list)

    def test_load_markets_unchanged(self):
        self.assertTrue(callable(markets.load_markets))
        self.assertEqual(len(SPECS), 6)


if __name__ == "__main__":
    unittest.main()
