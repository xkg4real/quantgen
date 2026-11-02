"""Exercise real Flet route builders with inert providers and temporary state."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import dotenv
with patch.object(dotenv, "load_dotenv", return_value=False):
    import main
    import core.skills.macro_daily as macro_daily
    from core.engine.feed import QuoteFeed
    from core.engine.runtime import EngineRuntime
    from core.engine.state import EngineMode
    from core.rules.store import RuleStore
from core.theme import set_mode
from tests.research_home_acceptance import Page, walk


class NavigationPage(Page):
    def run_thread(self, *args, **kwargs):
        raise AssertionError("Route construction must not start provider work")

    def run_task(self, *args, **kwargs):
        raise AssertionError("Route construction must not start asynchronous work")


class FletRuntimeTests(unittest.TestCase):
    def test_real_routes_render_after_locale_theme_and_size_changes(self):
        self.addCleanup(set_mode, "light")
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            store = RuleStore(root / "rules.json")
            feed = QuoteFeed(Mock(), fmp_client=Mock())
            engine = EngineRuntime(store, feed, state_path=root / "engine.json")
            page = NavigationPage()
            with patch.object(main, "RuleStore", return_value=store), \
                 patch.object(main, "EngineRuntime", return_value=engine), \
                 patch.object(macro_daily, "on_app_start") as startup, \
                 patch("ui.strategy_lab_page.load_cards", return_value=[]), \
                 patch("requests.sessions.Session.request", side_effect=AssertionError("Network forbidden")):
                main.main(page)
                routes = ["home", "library", "system"] + [row[0] for row in main.NAV]
                for locale, theme, width in (("en_US", "light", 1440), ("ko_KR", "dark", 390)):
                    page.qg_change_locale(locale)
                    page.qg_change_theme(theme)
                    page.width = width
                    page.on_resize(None)
                    for route in routes:
                        with self.subTest(route=route, locale=locale, theme=theme):
                            controls = [c for root_control in page.controls for c in walk(root_control)]
                            next(c for c in controls if c.data == "mobile-menu").on_click(None)
                            buttons = [c for c in walk(page.dialog) if c.data == {"route": route}]
                            self.assertTrue(buttons, route)
                            buttons[-1].on_click(None)
                            self.assertIsNone(page.dialog)
                            self.assertTrue(page.controls)
                startup.assert_called_once_with(background=True)
                self.assertEqual(engine.mode, EngineMode.DISARMED)
                self.assertIsNone(engine._thread)
                self.assertEqual(list(root.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
