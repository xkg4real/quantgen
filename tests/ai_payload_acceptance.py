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
        http.post.return_value.json.return_value = {"content": [{"type": "text", "text": "fixture response"}]}
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


if __name__ == "__main__":
    unittest.main()
