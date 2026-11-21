"""OS-F2 storage preparation at the actual GUI entry functions, without Qt/Flet or real home.

Compile the unmodified entry function ASTs with fake GUI dependencies. Stop at
the first GUI operation so these tests exercise storage ordering, not GUI code.
"""
import ast
import builtins
import contextlib
import io
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

from core import app_paths


ROOT = Path(__file__).resolve().parents[1]


class GuiReached(RuntimeError):
    pass


def entry_function(path, prepare, events):
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "core.app_paths":
            return types.SimpleNamespace(ensure_user_data_dir=prepare)
        if name == "windows_branding":
            return types.SimpleNamespace(set_app_identity=lambda: True, bind_window_icons=Mock())
        return original_import(name, *args, **kwargs)

    def gui(*args, **kwargs):
        events.append("gui")
        raise GuiReached()

    scope = {"__name__": "startup_fixture", "__package__": "quantgen_desktop",
             "__builtins__": {**vars(builtins), "__import__": fake_import},
             "QApplication": gui, "LocaleContext": gui, "sys": sys,
             "ft": types.SimpleNamespace(Page=object)}
    module = ast.Module(body=[node], type_ignores=[])
    exec(compile(module, str(ROOT / path), "exec"), scope)
    return scope["main"]


class StartupStorageTests(unittest.TestCase):
    def test_native_prepares_storage_before_creating_qapplication(self):
        events = []
        prepare = Mock(side_effect=lambda: events.append("prepare"))
        main = entry_function("quantgen_desktop/app.py", prepare, events)
        with self.assertRaises(GuiReached):
            main()
        self.assertEqual(events, ["prepare", "gui"])
        prepare.assert_called_once_with()

    def test_native_preparation_failure_returns_nonzero_before_gui(self):
        events = []
        prepare = Mock(side_effect=PermissionError("sensitive fixture path"))
        main = entry_function("quantgen_desktop/app.py", prepare, events)
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            self.assertEqual(main(), 1)
        self.assertEqual(events, [])
        self.assertIn("startup stopped", output.getvalue())
        self.assertNotIn("sensitive fixture path", output.getvalue())

    def test_flet_prepares_storage_before_touching_the_page(self):
        events = []
        prepare = Mock(side_effect=lambda: events.append("prepare"))
        main = entry_function("main.py", prepare, events)
        page = types.SimpleNamespace()
        with self.assertRaises(GuiReached):
            main(page)
        self.assertEqual(events, ["prepare", "gui"])
        self.assertEqual(vars(page), {})
        prepare.assert_called_once_with()

    def test_flet_preparation_failure_stops_before_page_or_engine(self):
        events = []
        prepare = Mock(side_effect=PermissionError("sensitive fixture path"))
        main = entry_function("main.py", prepare, events)
        page = types.SimpleNamespace()
        with self.assertRaisesRegex(RuntimeError, "startup stopped") as caught:
            main(page)
        self.assertEqual(events, [])
        self.assertEqual(vars(page), {})
        self.assertNotIn("sensitive fixture path", str(caught.exception))

    def test_both_entrypoints_mark_platform_root_before_later_legacy_creation(self):
        for path in ("quantgen_desktop/app.py", "main.py"):
            with self.subTest(path=path), tempfile.TemporaryDirectory() as tmp:
                home = Path(tmp)
                env = {"QUANTGEN_DATA_DIR": "", "FLET_APP_STORAGE_DATA": "",
                       "XDG_DATA_HOME": str(home / "xdg")}
                events = []
                main = entry_function(path, app_paths.ensure_user_data_dir, events)
                with patch.dict(os.environ, env), patch.object(Path, "home", return_value=home), \
                        patch.object(sys, "platform", "linux"):
                    with self.assertRaises(GuiReached):
                        main() if path.startswith("quantgen_desktop/") else main(types.SimpleNamespace())
                    selected = app_paths.user_data_dir()
                    self.assertTrue((selected / app_paths.DATA_MARKER).is_file())
                    (home / ".nextgen").mkdir()
                    self.assertEqual(app_paths.user_data_dir(), selected)
                    # Repeated application starts preserve the same root and marker.
                    with self.assertRaises(GuiReached):
                        main() if path.startswith("quantgen_desktop/") else main(types.SimpleNamespace())
                    self.assertEqual(app_paths.user_data_dir(), selected)

    def test_desktop_launchers_share_main_and_selfcheck_stays_separate(self):
        launcher = (ROOT / "packaging/launch_desktop.py").read_text(encoding="utf-8")
        module = (ROOT / "quantgen_desktop/__main__.py").read_text(encoding="utf-8")
        project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn("from quantgen_desktop.app import main", launcher)
        self.assertLess(launcher.index("return selfcheck.run("), launcher.index("from quantgen_desktop.app import main"))
        self.assertIn("from .app import main", module)
        self.assertIn("quantgen_desktop.app:main", project)


if __name__ == "__main__":
    unittest.main()
