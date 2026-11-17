"""PyQt6 -> PySide6 port helper (OS-P0-a): rewrite, counts and lint on fixed snippets; no Qt, no network."""
import contextlib
import io
from pathlib import Path
import tempfile
import textwrap
import unittest

from tools.qt_port import pyqt6_to_pyside6 as port

OLD, NEW = port.OLD, port.NEW
SIG, SLOT = "pyqt" + "Signal", "pyqt" + "Slot"


def src(text):
    return textwrap.dedent(text).replace("@OLD@", OLD).replace("@SIG@", SIG).replace("@SLOT@", SLOT)


SAMPLE = src('''\
    """Module docstring that names @OLD@ as prose."""
    import importlib.util
    from @OLD@.QtCore import Qt, QTimer, @SIG@, @SLOT@
    from @OLD@.QtWidgets import QWidget
    import @OLD@.QtGui
    from @OLD@ import sip

    HAS_QT = importlib.util.find_spec("@OLD@") is not None
    BANNED = ('@OLD@', 'requests')
    LABEL = "Native @OLD@ desktop"  # @OLD@ in a comment stays


    class Panel(QWidget):
        changed = @SIG@(str)

        @@SLOT@()
        def refresh(self):
            if sip.isdeleted(self.child) or not sip.isdeleted(self):
                sip.delete(self.child)
            return @OLD@.QtGui.QColor
    ''')


class RewriteTests(unittest.TestCase):
    def test_imports_names_and_sip_are_rewritten(self):
        out, changes = port.rewrite(SAMPLE)
        self.assertIn(f"from {NEW}.QtCore import Qt, QTimer, Signal, Slot", out)
        self.assertIn(f"from {NEW}.QtWidgets import QWidget", out)
        self.assertIn(f"import {NEW}.QtGui", out)
        self.assertIn("import shiboken6", out)
        self.assertNotIn("import sip", out)
        self.assertIn("changed = Signal(str)", out)
        self.assertIn("@Slot()", out)
        self.assertIn("if (not shiboken6.isValid(self.child)) or shiboken6.isValid(self):", out)
        self.assertIn("shiboken6.delete(self.child)", out)
        self.assertIn(f"return {NEW}.QtGui.QColor", out)
        self.assertIn(f'find_spec("{NEW}")', out)
        self.assertIn(f"BANNED = ('{NEW}', 'requests')", out)
        self.assertGreaterEqual(len(changes), 12)
        compile(out, "<rewritten>", "exec")

    def test_prose_and_comments_are_left_alone(self):
        out, _ = port.rewrite(SAMPLE)
        self.assertIn(f'"""Module docstring that names {OLD} as prose."""', out)
        self.assertIn(f'LABEL = "Native {OLD} desktop"  # {OLD} in a comment stays', out)

    def test_second_run_changes_nothing(self):
        once, _ = port.rewrite(SAMPLE)
        twice, changes = port.rewrite(once)
        self.assertEqual(once, twice)
        self.assertEqual(changes, [])

    def test_python_program_inside_a_string_is_rewritten(self):
        text = src("""\
            program = r'''
            from @OLD@.QtWidgets import QApplication
            from @OLD@ import sip
            sip.delete(window)
            '''
            script = ("import sys\\n"
                      "assert not any(name.startswith(n) for n in ('@OLD@', 'data'))\\n")
            """)
        out, _ = port.rewrite(text)
        self.assertIn(f"from {NEW}.QtWidgets import QApplication", out)
        self.assertIn("import shiboken6\nshiboken6.delete(window)", out)
        self.assertIn(f"('{NEW}', 'data')", out)
        self.assertEqual(port.rewrite(out)[0], out)

    def test_sip_with_nested_call_argument(self):
        out, _ = port.rewrite("ok = not sip.isdeleted(cache[key][0])\n")
        self.assertEqual(out, "ok = shiboken6.isValid(cache[key][0])\n")
        out, _ = port.rewrite("dead = any(sip.isdeleted(b) for b in blocks)\n")
        self.assertEqual(out, "dead = any((not shiboken6.isValid(b)) for b in blocks)\n")

    def test_unrelated_words_are_not_touched(self):
        text = "mysip.isdeleted(x)\nobj.sip.delete(y)\nSignal = 1\npyqtSignalLike = 2\n"
        self.assertEqual(port.rewrite(text)[0], text)


class CountTests(unittest.TestCase):
    def test_counts_match_the_snippet(self):
        c = port.count(SAMPLE)
        self.assertEqual(c.imports, 4)
        self.assertEqual(c.signal, 2)
        self.assertEqual(c.slot, 2)
        self.assertEqual(c.prop, 0)
        self.assertEqual(c.sip, 4)
        self.assertEqual(c.prose, 3)  # docstring, LABEL, comment
        self.assertEqual(c.changes, len(port.rewrite(SAMPLE)[1]))


class LintTests(unittest.TestCase):
    SNIPPET = src("""\
        from @OLD@.QtCore import QChar, QTimer
        from @OLD@.QtGui import QFontDatabase

        def setup(app, document, writer, table, combo, w, Side):
            for script in (QChar.Script.Script_Hangul,):
                QFontDatabase.addApplicationFallbackFontFamily(script, 'QG')
            document.print(writer)
            if app.receivers(app.open_requested) > 0:
                pass
            w.findChildren((QComboBox, QSpinBox))
            w.findChildren(QComboBox)
            combo.addItem('Buy', Side.BUY)
            combo.addItem('None', None)
            table.setItemDelegateForColumn(0, Delegate(table))
            table.setItemDelegateForColumn(1, app.kept_delegate)
            QTimer.singleShot(0, w.update)

        class Menu:
            def eventFilter(self, watched, event):
                if watched in self.roots:
                    return self.handlers.get(watched)
                return self.table[watched]
        """)

    def groups(self):
        found = port.lint(self.SNIPPET, "snippet.py")
        return {(f.group, f.line) for f in found}, found

    def test_each_known_risk_is_reported_with_its_line(self):
        groups, _ = self.groups()
        expected = {("8-font", 1), ("8-font", 5), ("8-font", 6), ("1-print", 7), ("3-receivers", 8),
                    ("2-findChildren", 10), ("4-combo-data", 12), ("9-delegate", 14), ("6-deferred", 16),
                    ("5-qobject-key", 20), ("5-qobject-key", 21), ("5-qobject-key", 22)}
        self.assertTrue(expected <= groups, sorted(expected - groups))

    def test_safe_forms_are_not_reported(self):
        groups, _ = self.groups()
        for line in (11, 13, 15):  # one type at a time, constant data, a kept delegate
            self.assertFalse([g for g in groups if g[1] == line], line)

    def test_bound_method_single_shot_is_its_own_group(self):
        text = src("""\
            from @OLD@.QtCore import QTimer
            class C:
                def f(self):
                    QTimer.singleShot(0, self.apply)
                    QTimer.singleShot(5, self.view.refresh)
                    QTimer.singleShot(0, lambda: self.apply())
                    QTimer.singleShot(0, self.make(1))
                    self.timer.start(0)
            """)
        found = {(f.line, f.group) for f in port.lint(text, "c.py")}
        self.assertEqual(found, {(4, "6-bound"), (5, "6-bound"), (6, "6-deferred"), (7, "6-deferred")})


class CommandTests(unittest.TestCase):
    def test_apply_refuses_a_git_checkout_and_is_idempotent_on_a_scratch_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            (root / "pkg").mkdir()
            (root / "pkg" / "a.py").write_text(SAMPLE, encoding="utf-8")
            with self.assertRaises(SystemExit):
                port.cmd_apply(root, ("pkg",))
            (root / ".qt_port_scratch").write_text("", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                first = port.cmd_apply(root, ("pkg",))
                second = port.cmd_apply(root, ("pkg",))
            self.assertEqual(first["files changed"], 1)
            self.assertEqual(second, {"files changed": 0})

    def test_docs_and_the_protected_cache_are_never_requested(self):
        for bad in (["docs"], ["docs/asset_expansion/cache"], ["."]):
            with self.subTest(bad=bad), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                port.main(["--check", *bad])
        self.assertFalse(port._allowed("docs/asset_expansion/cache/x.py"))
        self.assertFalse(port._allowed("tools/qt_port/pyqt6_to_pyside6.py"))
        self.assertTrue(port._allowed("quantgen_desktop/app.py"))

    def test_tool_source_survives_its_own_rewrite(self):
        source = Path(port.__file__).read_text(encoding="utf-8")
        self.assertEqual(port.rewrite(source)[0], source)


if __name__ == "__main__":
    unittest.main()
