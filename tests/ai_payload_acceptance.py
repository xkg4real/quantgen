"""NEW-M6-18: synthetic holdings and injected HTTP only; no accounts or API."""
from copy import deepcopy
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import dotenv
with patch.object(dotenv, "load_dotenv", return_value=False):
    from core.research import crypto_workflow as W
    from core.quant import insights
    from ui.ai_panel import analysis_panel
import flet as ft


def computed_result():
    return {"source": "SYNTHETIC", "kimchi": SimpleNamespace(last_pct=2, last_z=.4,
        mean_pct=1, max_pct=3, half_life_days=8, adf_p=.01, pred_t=.2, n=100),
        "funding": None, "premium_index": {"premium_pct": .01}, "garch": {"nu": 8},
        "ethbtc": {"adf_p": .1}, "weekday": {}, "verdicts": {"example": "NOT_RUN"},
        "balances": [{"currency": "FIXTURE", "total": 23, "avg_buy_price": 654,
                      "krw_value": 15042, "account": "fake-private-holding-marker"}]}


class AiPayloadTests(unittest.TestCase):
    def test_crypto_payload_keeps_market_results_and_excludes_holdings(self):
        a = computed_result(); before = deepcopy(a)
        payload = W.payload(a)
        self.assertNotIn("holdings", payload)
        self.assertNotIn("fake-private-holding-marker", json.dumps(payload))
        self.assertEqual(payload["kimchi"]["last_pct"], 2)
        self.assertEqual(payload["verdicts"], {"example": "NOT_RUN"})
        self.assertEqual(a, before)  # local account display still has its input

    def test_final_http_boundary_filters_nested_account_fields(self):
        payload = {"price": 42, "holdings": [{"avg_buy_price": "fake-private-holding-marker"}],
                   "nested": [{"balances": {"currency": "fake-private-balance-marker"}, "vol": .2}],
                   "API_KEY": "fake-private-key-marker", "verdict": "NOT_RUN"}
        before = deepcopy(payload)
        http = Mock(); http.post.return_value.status_code = 200
        http.post.return_value.json.return_value = {"content": [{"type": "text", "text": "fixture response"}],
                                                    "stop_reason": "end_turn"}
        with patch.object(insights.config, "anthropic_key", return_value="fixture-key"), \
             patch.object(insights.config, "ai_model", return_value="fixture-model"), \
             patch.object(insights, "_requests", http):
            result = insights.deep_analysis("crypto_market", payload)
        self.assertFalse(result.error)
        sent = http.post.call_args.kwargs["json"]["messages"][0]["content"]
        self.assertNotIn("fake-private-", sent)
        self.assertIn('"price": 42', sent)
        self.assertIn('"vol": 0.2', sent)
        self.assertIn("NOT_RUN", sent)
        self.assertEqual(payload, before)

    def test_flet_custom_runner_gets_filtered_snapshot_only_after_click(self):
        source = {"holdings": [{"quantity": "fake-private-holding-marker"}], "price": 42}
        runner = Mock(return_value=insights.Analysis("fixture response", "fixture"))
        page = Mock(); page.run_thread.side_effect = lambda worker: worker()
        with patch.object(insights, "ai_ready", return_value=True):
            panel = analysis_panel(page, kind="crypto_market", narrative="local", payload_fn=lambda: source, deep_fn=runner)
        runner.assert_not_called()
        row = panel.content.controls[3]
        button = next(c for c in row.controls if isinstance(c, ft.Button))
        button.on_click(None)
        runner.assert_called_once()
        self.assertEqual(runner.call_args.args[1], {"price": 42})
        self.assertIn("holdings", source)

    def test_flet_disclosure_covers_fixed_instructions_and_value_notes_in_both_languages(self):
        from core.i18n import LocaleContext
        from ui.localization import translate_controls
        runner=Mock();payload_fn=Mock(return_value={"price":42})
        page=Mock();page.qg_locale=LocaleContext('ko_KR')
        with patch.object(insights,'ai_ready',return_value=True):
            panel=analysis_panel(page,kind='portfolio',narrative='local',payload_fn=payload_fn,deep_fn=runner)
        disclosure=panel.content.controls[4]
        self.assertIn('고정 작성 지침',disclosure.value)
        question=panel.content.controls[3].controls[0];question.value='synthetic question'
        for language,phrases in (
            ('en_US',('selected analysis type','your question','fixed writing instructions',
                      'When needed','missing, undefined or unbounded values','holdings and balances are excluded')),
            ('ko_KR',('분석 종류','질문','고정 작성 지침','값이 있으면 그 표기 설명','보유 내역과 잔고는 제외')),
        ):
            translate_controls(panel,LocaleContext(language))
            for phrase in phrases:self.assertIn(phrase,disclosure.value)
            self.assertEqual(question.value,'synthetic question')
        payload_fn.assert_not_called();runner.assert_not_called();page.run_thread.assert_not_called()

    def test_flet_error_keeps_local_narrative_and_shows_safe_action(self):
        from core.research.ai_connection import error_message
        message = error_message('AUTHENTICATION', http_status=401)
        runner = Mock(return_value=insights.Analysis('', 'fixture', message, 'AUTHENTICATION', 401))
        page = Mock(); page.run_thread.side_effect = lambda worker: worker()
        with patch.object(insights, 'ai_ready', return_value=True):
            panel = analysis_panel(page, kind='portfolio', narrative='Local computed explanation',
                                   payload_fn=lambda: {'price':42}, deep_fn=runner)
        rows = panel.content.controls
        next(c for c in rows[3].controls if isinstance(c, ft.Button)).on_click(None)
        self.assertEqual(rows[1].value, 'Local computed explanation')
        self.assertIn('ANTHROPIC_API_KEY', str(rows[-1].controls))
        from ui.localization import translate_controls
        from core.i18n import LocaleContext
        banner = rows[-1].controls[0]
        translate_controls(banner, LocaleContext('ko_KR'))
        self.assertIn('인증 실패', banner.content.content.controls[1].value)
        translate_controls(banner, LocaleContext('en_US'))
        self.assertIn('authentication failed', banner.content.content.controls[1].value)
        self.assertNotIn('인증 실패', banner.content.content.controls[1].value)
        self.assertFalse(rows[3].controls[-1].visible)
        runner.assert_called_once()

    def test_flet_cut_off_reply_shows_the_notice_not_the_text(self):
        from ui.ai_panel import _ErrorNotice
        from ui.localization import translate_controls
        from core.i18n import LocaleContext
        partial = "The Sharpe ratio of 0.42 over the window is modest, and the drawdown of"
        http = Mock(); http.post.return_value.status_code = 200
        http.post.return_value.json.return_value = {
            "content": [{"type": "thinking", "thinking": ""}, {"type": "text", "text": partial}],
            "stop_reason": "max_tokens"}
        page = Mock(); page.run_thread.side_effect = lambda worker: worker()
        with patch.object(insights.config, "anthropic_key", return_value="fixture-key"), \
             patch.object(insights.config, "ai_model", return_value="fixture-model"), \
             patch.object(insights, "_requests", http), \
             patch.object(insights, "ai_ready", return_value=True):
            panel = analysis_panel(page, kind="portfolio", narrative="Local computed explanation",
                                   payload_fn=lambda: {"price": 42})
            rows = panel.content.controls
            next(c for c in rows[3].controls if isinstance(c, ft.Button)).on_click(None)
        http.post.assert_called_once()
        self.assertEqual(len(rows[-1].controls), 1)
        banner = rows[-1].controls[0]
        self.assertIsInstance(banner, _ErrorNotice)
        self.assertEqual(banner.result.error_code, "OUTPUT_LIMIT")
        self.assertFalse(any(partial in str(t.value) for t in texts(panel)))
        translate_controls(banner, LocaleContext("ko_KR"))
        self.assertTrue(any("출력 한도" in str(t.value) for t in texts(banner)))
        translate_controls(banner, LocaleContext("en_US"))
        self.assertTrue(any("output limit" in str(t.value) for t in texts(banner)))
        self.assertEqual(rows[1].value, "Local computed explanation")
        self.assertFalse(rows[3].controls[-1].visible)

    def test_payload_is_strict_json_with_full_arrays_and_labelled_nonfinite_values(self):
        import datetime as dt
        import math
        import numpy as np
        import pandas as pd
        from core.research import ai_payload as AP

        def refuse(token):
            raise AssertionError(f"bare {token} token")

        dates = pd.date_range("2026-01-01", periods=100, freq="D")
        payload = {
            "series": np.arange(120.0), "matrix": np.ones((120, 2)),
            "dated": pd.Series(np.arange(100.0), index=dates),
            "frame": pd.DataFrame({"px": np.arange(80.0), "vol": np.full(80, .2)}),
            "tbl": pd.DataFrame({"account_balance": [1.0, 2.0], "px": [3.0, 4.0]}),
            "rows": np.array([{"holding": "fake-private-holding-marker", "px": 1.0}], dtype=object),
            "garch": {"nu": math.inf, "nu_interval_95": (13.9, math.inf), "half_life": math.inf,
                      "half_life_interval_95": (12.0, math.inf), "uncond_vol_365": math.nan},
            "kimchi": {"half_life_days": math.inf, "adf_p": math.nan},
            "plain_nan": math.nan, "plain_inf": np.float64(math.inf), "plain_ninf": -math.inf,
            "missing": None, "i64": np.int64(7), "flag": np.bool_(True),
            "dt64": np.datetime64("2026-10-30"), "td64": np.timedelta64(3, "D"),
            "day": dt.date(2026, 10, 30), "ts": pd.Timestamp("2026-10-30"),
            (1, 2): "tuple-key", np.int64(3): "numpy-key", True: "bool-key", None: "none-key",
        }
        keys_before = list(payload)
        series_before = payload["series"].copy()
        sent = AP.ai_payload_json(payload)
        obj = json.loads(sent.text, parse_constant=refuse)
        self.assertEqual(list(payload), keys_before)
        self.assertTrue(np.array_equal(payload["series"], series_before))
        self.assertTrue(math.isinf(payload["garch"]["nu"]))
        self.assertEqual(AP.ai_payload_json(payload), sent)

        self.assertEqual(len(obj["series"]), 120); self.assertEqual(obj["series"][-1], 119.0)
        self.assertEqual(len(obj["matrix"]), 120); self.assertEqual(obj["matrix"][-1], [1.0, 1.0])
        self.assertEqual(len(obj["dated"]["values"]), 100)
        self.assertEqual(len(obj["dated"]["index"]), 100)
        self.assertTrue(obj["dated"]["index"][-1].startswith("2026-04-10"))
        self.assertEqual(len(obj["frame"]["data"]), 80); self.assertEqual(len(obj["frame"]["index"]), 80)
        self.assertEqual(obj["frame"]["columns"], ["px", "vol"])

        garch = obj["garch"]
        self.assertTrue(garch["nu"].startswith("+inf: normal innovations"))
        self.assertEqual(garch["nu_interval_95"][0], 13.9)
        self.assertIn("upper end of this interval", garch["nu_interval_95"][1])
        self.assertNotIn("normal innovations (", garch["nu_interval_95"][1])
        self.assertIn("this end of the interval reaches persistence 1", garch["half_life_interval_95"][1])
        self.assertEqual(garch["half_life"], AP.NONFINITE_MEANINGS[("garch", "half_life", "+inf")])
        self.assertEqual(garch["uncond_vol_365"], AP.NONFINITE_MEANINGS[("garch", "uncond_vol_365", "NaN")])
        self.assertEqual(obj["kimchi"]["half_life_days"], AP.NONFINITE_MEANINGS[("kimchi", "half_life_days", "+inf")])
        self.assertEqual(obj["kimchi"]["adf_p"], AP.NONFINITE_MEANINGS[("kimchi", "adf_p", "NaN")])
        self.assertEqual(obj["plain_nan"], AP.NAN_MARKER)
        self.assertEqual(obj["plain_inf"], AP.POS_INF_MARKER)
        self.assertEqual(obj["plain_ninf"], AP.NEG_INF_MARKER)
        self.assertEqual((sent.marked, sent.nulls), (10, 1))
        for marker in list(AP.NONFINITE_MEANINGS.values()) + [AP.NAN_MARKER, AP.POS_INF_MARKER, AP.NEG_INF_MARKER]:
            self.assertTrue(marker.startswith(AP.MARKER_PREFIXES), marker)
            self.assertFalse(set(marker) & set("23456789"), marker)

        self.assertIn('"i64": 7', sent.text); self.assertNotIn('"i64": 7.0', sent.text)
        self.assertIs(obj["flag"], True)
        for key in ("dt64", "td64", "day", "ts"):
            self.assertEqual(obj[key], str(payload[key]))
        self.assertEqual(obj["(1, 2)"], "tuple-key"); self.assertEqual(obj["3"], "numpy-key")
        self.assertEqual(obj["true"], "bool-key"); self.assertEqual(obj["null"], "none-key")

        for private in ("account_balance", "fake-private-holding-marker", "holding"):
            self.assertNotIn(private, sent.text)
        self.assertEqual(obj["tbl"]["columns"], ["px"])
        self.assertEqual(obj["rows"], [{"px": 1.0}])

    def test_synthetic_crypto_and_etf_send_nu_infinity_as_normal_innovations(self):
        import math
        from core.quant.history import synthetic_history
        from core.research import etf_workflow as EW
        from core.research.ai_payload import VALUE_NOTE
        import core.quant.validate as V
        import core.quant.gate_ledger as GL

        def refuse(token):
            raise AssertionError(f"bare {token} token")

        with patch("socket.socket.connect", side_effect=AssertionError("No live network")), \
             patch.object(V, "load_cards", side_effect=AssertionError("No study cards")), \
             patch.object(GL, "family_ledger", side_effect=AssertionError("No ledger")):
            crypto = W.payload(W.analyze(source="synthetic", card_loader=lambda p: [], include_balances=False))
            etf = EW.payload(EW.analyze("122630", source="synthetic", card_loader=lambda p: [],
                                        history_loader=lambda c, source, days: synthetic_history(c, days=days)))
            for name, payload, section in (("crypto", crypto, "garch"), ("etf", etf, "letf")):
                with self.subTest(payload=name):
                    # Synthetic GBM returns fit at the normal limit: nu = +inf means normal innovations.
                    self.assertTrue(math.isinf(payload[section]["nu"]))
                    http = Mock(); http.post.return_value.status_code = 200
                    http.post.return_value.json.return_value = {
                        "content": [{"type": "text", "text": "fixture"}], "stop_reason": "end_turn"}
                    with patch.object(insights.config, "anthropic_key", return_value="fixture-key"), \
                         patch.object(insights.config, "ai_model", return_value="fixture-model"), \
                         patch.object(insights, "_requests", http):
                        result = insights.deep_analysis("crypto_market" if name == "crypto" else "etf_structure", payload)
                    self.assertFalse(result.error)
                    content = http.post.call_args.kwargs["json"]["messages"][0]["content"]
                    self.assertIn('"nu": "+inf: normal innovations', content)
                    self.assertIn(VALUE_NOTE, content)
                    segment = content.split("Computed results:\n", 1)[1].split("\n\n" + VALUE_NOTE, 1)[0]
                    json.loads(segment, parse_constant=refuse)    # strict: no bare NaN or Infinity

    def test_oversized_or_unserialisable_payload_is_refused_before_any_request(self):
        from core.research.ai_connection import error_message
        from core.research.ai_payload import AI_PAYLOAD_MAX_BYTES, ai_payload_json

        def call(payload):
            http = Mock(); http.post.return_value.status_code = 200
            http.post.return_value.json.return_value = {
                "content": [{"type": "text", "text": "fixture"}], "stop_reason": "end_turn"}
            with patch.object(insights.config, "anthropic_key", return_value="fixture-key"), \
                 patch.object(insights.config, "ai_model", return_value="fixture-model"), \
                 patch.object(insights, "_requests", http):
                return insights.deep_analysis("portfolio", payload), http

        def sized(total):
            base = len(ai_payload_json({"text": "가" * 59_000}).text.encode("utf-8"))
            payload = {"text": "가" * 59_000 + "a" * (total - base)}
            self.assertEqual(len(ai_payload_json(payload).text.encode("utf-8")), total)
            return payload

        over, http = call(sized(AI_PAYLOAD_MAX_BYTES + 1))
        self.assertEqual((over.error_code, over.text, over.engine), ("PAYLOAD_TOO_LARGE", "", "none"))
        http.post.assert_not_called()
        at, http = call(sized(AI_PAYLOAD_MAX_BYTES))
        self.assertEqual(at.error_code, ""); http.post.assert_called_once()
        with patch.object(insights, "ai_payload_json", side_effect=ValueError("fixture")):
            broken, http = call({"price": 42})
        self.assertEqual((broken.error_code, broken.text, broken.engine), ("PAYLOAD_INVALID", "", "none"))
        http.post.assert_not_called()
        self.assertNotIn("fixture", broken.error)
        for surrogate in ("\ud800", "\udfff"):
            with self.subTest(surrogate=repr(surrogate)):
                invalid, http = call({"text": surrogate})
                self.assertEqual((invalid.error_code, invalid.text, invalid.engine),
                                 ("PAYLOAD_INVALID", "", "none"))
                http.post.assert_not_called()
                self.assertNotIn(surrogate, invalid.error)
        for language in ("en", "ko"):
            self.assertIn("180,000", error_message("PAYLOAD_TOO_LARGE", language))
            self.assertTrue(error_message("PAYLOAD_INVALID", language))
        self.assertNotEqual(error_message("PAYLOAD_INVALID", "en"), error_message("PAYLOAD_INVALID", "ko"))

    def test_flet_spinner_clears_when_the_payload_cannot_be_prepared(self):
        from ui.ai_panel import _ErrorNotice

        def payload_fn():
            raise ValueError("fixture payload failure")

        page = Mock(); page.run_thread.side_effect = lambda worker: worker()
        http = Mock()
        with patch.object(insights.config, "anthropic_key", return_value="fixture-key"), \
             patch.object(insights, "_requests", http), \
             patch.object(insights, "ai_ready", return_value=True):
            panel = analysis_panel(page, kind="portfolio", narrative="Local computed explanation",
                                   payload_fn=payload_fn)
            rows = panel.content.controls
            next(c for c in rows[3].controls if isinstance(c, ft.Button)).on_click(None)
        http.post.assert_not_called()
        self.assertEqual(len(rows[-1].controls), 1)
        self.assertIsInstance(rows[-1].controls[0], _ErrorNotice)
        self.assertEqual(rows[-1].controls[0].result.error_code, "PAYLOAD_INVALID")
        self.assertFalse(any("fixture payload failure" in str(t.value) for t in texts(panel)))
        self.assertFalse(rows[3].controls[-1].visible)
        self.assertEqual(rows[1].value, "Local computed explanation")

    def test_flet_success_shows_label_and_number_check(self):
        from core.i18n import LocaleContext
        from core.research.ai_output_check import AI_LABEL
        from ui.localization import translate_controls
        import core.quant.validate as V
        import core.quant.gate_ledger as GL
        reply = "The Sharpe ratio of 9.99 sits well above the sample's 0.42."
        http = Mock(); http.post.return_value.status_code = 200
        http.post.return_value.json.return_value = {"content": [{"type": "text", "text": reply}],
                                                    "stop_reason": "end_turn"}
        page = Mock(); page.run_thread.side_effect = lambda worker: worker()
        with patch("socket.socket.connect", side_effect=AssertionError("No live network")), \
             patch.object(V, "load_cards", side_effect=AssertionError("No study cards")), \
             patch.object(GL, "family_ledger", side_effect=AssertionError("No ledger")), \
             patch.object(insights.config, "anthropic_key", return_value="fixture-key"), \
             patch.object(insights.config, "ai_model", return_value="fixture-model"), \
             patch.object(insights, "_requests", http), \
             patch.object(insights, "ai_ready", return_value=True):
            panel = analysis_panel(page, kind="portfolio", narrative="Local computed explanation",
                                   payload_fn=lambda: {"sharpe": 0.42, "price": 42})
            rows = panel.content.controls
            next(c for c in rows[3].controls if isinstance(c, ft.Button)).on_click(None)
        http.post.assert_called_once()
        host = rows[-1]
        self.assertEqual(host.controls[1].value, reply)        # the commentary text is unchanged
        values = [str(t.value) for t in texts(host)]
        self.assertIn(AI_LABEL["en"], values)
        line = next(v for v in values if v.startswith("Number check"))
        self.assertIn("9.99", line); self.assertNotIn("0.42,", line)
        self.assertEqual(rows[1].value, "Local computed explanation")
        self.assertFalse(rows[3].controls[-1].visible)
        translate_controls(host, LocaleContext("ko_KR"))
        values = [str(t.value) for t in texts(host)]
        self.assertTrue(any("검증 안 됨" in v for v in values))
        self.assertTrue(any(v.startswith("숫자 대조") and "9.99" in v for v in values))
        self.assertIn(reply, values)
        translate_controls(host, LocaleContext("en_US"))
        values = [str(t.value) for t in texts(host)]
        self.assertIn(AI_LABEL["en"], values)
        self.assertFalse(any("검증" in v for v in values))

        runner = Mock(return_value=insights.Analysis("x", "fixture"))
        with patch.object(insights, "ai_ready", return_value=True):
            panel = analysis_panel(page, kind="portfolio", narrative="local",
                                   payload_fn=lambda: {"price": 42}, deep_fn=runner)
            rows = panel.content.controls
            next(c for c in rows[3].controls if isinstance(c, ft.Button)).on_click(None)
        self.assertIn("Number check: not run.", [str(t.value) for t in texts(rows[-1])])


def texts(root):
    """Every ft.Text under a control, through `controls` and `content`."""
    if isinstance(root, ft.Text):
        yield root
    for child in getattr(root, "controls", None) or []:
        yield from texts(child)
    content = getattr(root, "content", None)
    if isinstance(content, ft.Control):
        yield from texts(content)


if __name__ == "__main__":
    unittest.main()
