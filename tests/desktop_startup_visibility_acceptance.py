"""Qt startup exposure contracts without a full app, settings, data or providers.

A parentless child shown before insertion into a layout becomes a transient
top-level window. Observe actual Show events, rather than inferring visibility
from the finished hierarchy after that window has already disappeared.
"""
from __future__ import annotations

import unittest


class DesktopApplicationStyleAcceptance(unittest.TestCase):
    def check_fusion_lifetime(self):
        from PyQt6 import sip
        from PyQt6.QtCore import QEvent
        from PyQt6.QtWidgets import QApplication, QLabel, QProxyStyle, QStyleFactory

        self.assertIsNone(QApplication.instance())
        from quantgen_desktop import use_fusion_style  # also runs before QApplication exists

        class Witness(QLabel):
            style_changes = 0

            def changeEvent(self, event):
                if event.type() == QEvent.Type.StyleChange:
                    self.style_changes += 1
                super().changeEvent(event)

        class NamedProxy(QProxyStyle):
            def name(self):
                return "fusion"

        for _ in range(2):
            app = QApplication(["style-test", "-platform", "offscreen"])
            app.setStyleSheet("")  # Qt may retain the process stylesheet across application lifetimes
            self.assertIsNotNone(app.setStyle("Windows"))
            use_fusion_style()
            self.assertEqual(app.style().name().lower(), "fusion")
            label = Witness()
            label.show()
            sheet = "QLabel { color: #345678; }"
            app.setStyleSheet(sheet)
            app.processEvents()
            wrapper, changes = app.style(), label.style_changes
            use_fusion_style()
            app.processEvents()
            self.assertIs(app.style(), wrapper, "Fusion under QSS was reinstalled")
            self.assertEqual(label.style_changes, changes)

            # Another component can replace the base while the same QSS stays active.
            self.assertIsNotNone(app.setStyle("Windows"))
            use_fusion_style()
            self.assertEqual(app.styleSheet(), sheet)
            app.setStyleSheet("")
            self.assertEqual(app.style().name().lower(), "fusion")

            for stylesheet in ("", sheet):
                app.setStyleSheet(stylesheet)
                app.setStyle(NamedProxy("Windows"))
                use_fusion_style()
                self.assertEqual(app.styleSheet(), stylesheet)
                app.setStyleSheet("")
                self.assertEqual(app.style().metaObject().className(), "QFusionStyle")

            app.setStyleSheet(sheet)
            ambiguous = app.style()
            extra = QStyleFactory.create("Fusion")
            extra.setParent(ambiguous)
            use_fusion_style()
            self.assertIsNot(app.style(), ambiguous, "An ambiguous wrapper must use the normal fallback")
            self.assertEqual(app.styleSheet(), sheet)
            sip.delete(label)
            sip.delete(app)
            self.assertIsNone(QApplication.instance())

    def test_fusion_survives_application_stylesheets_and_recreation(self):
        # Other UI tests share a QApplication. Exercise its entire lifetime in an isolated process.
        import subprocess
        import sys
        from pathlib import Path

        subprocess.run(
            [sys.executable, "-B", "-c", "from tests.desktop_startup_visibility_acceptance import "
             "DesktopApplicationStyleAcceptance as Case; Case().check_fusion_lifetime()"],
            cwd=Path(__file__).resolve().parents[1], check=True, timeout=30,
        )


class DesktopStartupVisibilityAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PyQt6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        from PyQt6.QtCore import QEvent, QObject
        from PyQt6.QtWidgets import QWidget

        class ShowObserver(QObject):
            def __init__(self):
                super().__init__()
                self.events = []

            def eventFilter(self, watched, event):
                if (event.type() == QEvent.Type.Show
                        and isinstance(watched, QWidget) and watched.isWindow()):
                    self.events.append({
                        "id": id(watched),
                        "type": type(watched).__name__,
                        "name": watched.objectName(),
                        "text": watched.text() if hasattr(watched, "text") else "",
                    })
                return False

        self.observer = ShowObserver()
        self.app.installEventFilter(self.observer)
        self.widgets = []

    def tearDown(self):
        from PyQt6.QtCore import QCoreApplication, QEvent
        self.app.removeEventFilter(self.observer)
        for widget in reversed(self.widgets):
            widget.close()
            widget.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete.value)
        self.app.processEvents()

    def _keep(self, widget):
        self.widgets.append(widget)
        return widget

    def test_hidden_cards_do_not_show_transient_top_level_windows(self):
        from quantgen_desktop.page_kit import Card
        for title, note in (("A titled card", "A note"), ("A title", None), (None, None)):
            with self.subTest(title=title, note=note):
                self.observer.events.clear()
                card = self._keep(Card(title, note))
                self.assertTrue(card.isHidden())
                self.assertIs(card.head_host.parentWidget(), card)
                self.assertIs(card.title.parentWidget(), card.head_host)
                self.assertEqual(card.head_host.isHidden(), title is None)
                self.assertEqual(card.note.isHidden(), note is None)
                self.assertEqual(self.observer.events, [], "construction exposed a child window")

    def test_hidden_reading_notes_do_not_show_transient_label_windows(self):
        from quantgen_desktop.page_kit import Soft
        for title, text in (("Reading", "A short explanation"), ("Reading", None),
                            (None, "Explanation only"), (None, None)):
            with self.subTest(title=title, text=text):
                self.observer.events.clear()
                note = self._keep(Soft(title, text))
                self.assertTrue(note.isHidden())
                self.assertIs(note.title.parentWidget(), note)
                self.assertIs(note.text.parentWidget(), note)
                self.assertEqual(note.title.isHidden(), title is None)
                self.assertEqual(note.text.isHidden(), text is None)
                self.assertEqual(self.observer.events, [], "construction exposed a note label")

    def test_hidden_workspaces_do_not_show_transient_toolbar_titles(self):
        from quantgen_desktop.page_kit import Workspace
        for title in ("Technical indicator guide", None):
            with self.subTest(title=title):
                self.observer.events.clear()
                workspace = self._keep(Workspace(title))
                workspace.add_mode(("Chart", "차트"))
                workspace.side.add_page(("Settings", "설정"))
                workspace.finish()
                self.assertTrue(workspace.isHidden())
                self.assertIs(workspace.title.parentWidget(), workspace.toolbar_host)
                self.assertIs(workspace.toolbar_host.parentWidget(), workspace)
                self.assertEqual(workspace.title.isHidden(), title is None)
                self.assertEqual(self.observer.events, [], "construction exposed a toolbar title")

    def test_toolbar_badges_wait_for_the_workspace_and_follow_text_language_and_suppression(self):
        from quantgen_desktop.page_kit import Workspace

        workspace = self._keep(Workspace(side=False))
        badge = workspace.add_badge(("Delayed", "지연"), "warn")
        empty = workspace.add_badge()
        self.assertEqual(self.observer.events, [], "constructing a toolbar badge exposed a window")
        self.assertIs(badge.parentWidget(), workspace.toolbar_host)
        self.assertEqual(badge.property("kit"), "badge")
        self.assertEqual(badge.property("tone"), "warn")
        self.assertEqual(badge.text(), "● 지연")
        workspace.show()
        self.app.processEvents()
        self.assertTrue(badge.isVisible())
        self.assertTrue(empty.isHidden())
        workspace.set_language("en")
        self.assertEqual(badge.text(), "● Delayed")
        badge.suppress(True)
        badge.set_pair(("● Updated", "갱신"))
        workspace.set_language("ko")
        self.assertTrue(badge.isHidden())
        badge.suppress(False)
        self.assertTrue(badge.isVisible())
        self.assertEqual(badge.text(), "● 갱신")
        empty.set_pair("Ready")
        self.assertTrue(empty.isVisible())
        empty.set_pair("")
        self.assertTrue(empty.isHidden())
        self.assertEqual({event["id"] for event in self.observer.events}, {id(workspace)})

    def test_explicit_host_show_retains_titles_notes_and_optional_header_behavior(self):
        from PyQt6.QtWidgets import QPushButton, QVBoxLayout, QWidget
        from quantgen_desktop.page_kit import Card, Soft, Workspace

        host = self._keep(QWidget())
        host.setObjectName("intentional-startup-host")
        layout = QVBoxLayout(host)
        card = Card(("Title", "제목"), ("Note", "주석"))
        untitled = Card()
        note = Soft(("Reading", "읽는 법"), ("Explanation", "설명"))
        workspace = Workspace(("Workspace", "작업 화면"), side=False)
        for widget in (card, untitled, note, workspace):
            layout.addWidget(widget)
        self.assertEqual(self.observer.events, [], "hidden page construction showed a window")
        host.resize(800, 700)
        host.show()
        self.app.processEvents()
        self.assertEqual({event["id"] for event in self.observer.events}, {id(host)})
        self.assertTrue(card.head_host.isVisible())
        self.assertTrue(card.title.isVisible())
        self.assertTrue(card.note.isVisible())
        self.assertTrue(note.title.isVisible())
        self.assertTrue(note.text.isVisible())
        self.assertTrue(workspace.title.isVisible())
        self.assertTrue(untitled.head_host.isHidden())
        button = QPushButton("More")
        untitled.add_head_widget(button)
        self.app.processEvents()
        self.assertTrue(untitled.head_host.isVisible())
        self.assertIs(button.parentWidget(), untitled.head_host)
        self.assertEqual({event["id"] for event in self.observer.events}, {id(host)})
        card.set_language("en")
        note.set_language("en")
        workspace.set_language("en")
        self.assertEqual(card.title.text(), "Title")
        self.assertEqual(card.note.text(), "Note")
        self.assertEqual(note.title.text(), "Reading")
        self.assertEqual(note.text.text(), "Explanation")
        self.assertEqual(workspace.title.text(), "Workspace")


if __name__ == "__main__":
    unittest.main()
