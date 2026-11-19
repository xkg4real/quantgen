"""KEY-3 boundary test (GATEWAY_DESIGN.md section 3): app code reaches data providers only through core/gateway.

It counts, per file, the lines in core/, quantgen_desktop/, ui/ and main.py that import a provider client, call
yfinance, name the Anthropic API host, or call a config key function. core/gateway/ is the one place allowed to.
KNOWN lists today's direct calls (main ca5da08: 30 files, 69 lines). A new direct call fails the test; so does a
file whose count went down without KNOWN being lowered, so the list cannot go stale. KEY-4 brings the core/ and
main.py rows to zero, KEY-5 (UI session) the screen rows."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN = ("core", "quantgen_desktop", "ui")
ALLOWED_DIRS = ("core/gateway/",)
PATTERN = re.compile(
    r"(from|import) data\.(krx|fmp|crypto|kis_markets|kis_stream|kis_workspace|net)"
    r"|(^|[^a-z_])(import yfinance|from yfinance|yf\.(download|Ticker|Tickers))"
    r"|api\.anthropic\.com"
    r"|config\.(kis_ready|kis_credentials|fmp_key|fmp_ready|opendart_key|opendart_ready|krx_key|krx_ready"
    r"|anthropic_key|ai_ready|gs_client_id|gs_client_secret|upbit_ready|upbit_keys)\(")

KNOWN = {
    "core/engine/feed.py": 1,
    "core/ficc/curve_models.py": 1,
    "core/ficc/data.py": 2,
    "core/market/detail_model.py": 1,
    "core/market/market_cap.py": 2,
    "core/market/qscore_rankings.py": 1,
    "core/quant/gsq.py": 2,
    "core/quant/history.py": 13,
    "core/quant/insights.py": 3,
    "core/research/ai_connection.py": 2,
    "core/research/connections.py": 3,
    "core/research/crypto_workflow.py": 4,
    "core/research/derivatives_workflow.py": 2,
    "core/research/etf_workflow.py": 3,
    "core/research/market_analysis.py": 1,
    "core/research/market_board.py": 1,
    "core/research/watchlist.py": 1,
    "main.py": 1,
    "quantgen_desktop/app.py": 2,
    "quantgen_desktop/market_chart.py": 6,
    "quantgen_desktop/market_rankings.py": 2,
    "quantgen_desktop/market_tools.py": 1,
    "quantgen_desktop/qscore.py": 1,
    "quantgen_desktop/watchlist_live.py": 2,
    "ui/crypto_page.py": 1,
    "ui/derivatives_page.py": 1,
    "ui/krx_page.py": 1,
    "ui/macro_state_panel.py": 1,
    "ui/market_chart_page.py": 4,
    "ui/settings_page.py": 3,
}


def scan() -> dict[str, int]:
    files = [ROOT / "main.py"]
    for top in SCAN:
        files.extend(sorted((ROOT / top).rglob("*.py")))
    found = {}
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        if any(rel.startswith(d) for d in ALLOWED_DIRS) or "__pycache__" in rel:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        count = sum(1 for line in text.splitlines() if PATTERN.search(line))
        if count:
            found[rel] = count
    return found


class BoundaryTest(unittest.TestCase):
    def test_no_new_direct_provider_calls(self):
        found = scan()
        grew = {f: (KNOWN.get(f, 0), n) for f, n in found.items() if n > KNOWN.get(f, 0)}
        self.assertEqual(grew, {}, "new direct provider calls; go through core.gateway (known, now)")

    def test_known_list_is_not_stale(self):
        found = scan()
        shrank = {f: (n, found.get(f, 0)) for f, n in KNOWN.items() if found.get(f, 0) < n}
        self.assertEqual(shrank, {}, "fewer direct calls than KNOWN says; lower KNOWN (known, now)")

    def test_known_totals(self):
        core_lines = sum(n for f, n in KNOWN.items() if f.startswith("core/") or f == "main.py")
        screen_lines = sum(n for f, n in KNOWN.items() if f.startswith(("quantgen_desktop/", "ui/")))
        self.assertEqual((len(KNOWN), core_lines + screen_lines), (30, 69))
        self.assertEqual((core_lines, screen_lines), (44, 25))


if __name__ == "__main__":
    unittest.main()
