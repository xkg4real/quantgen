"""Explicit report saving shared by standalone native result views."""
from .translations import display
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QFileDialog
from core.research.tool_export import make_report, report_bytes
from core.research.export import save_desktop_export


class ReportActions(QWidget):
    def __init__(self, status):
        super().__init__()
        self.status, self.report = status, None
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.json_button, self.zip_button = QPushButton('분석 JSON 저장'), QPushButton('보고서 ZIP 저장')
        for button, bundle in ((self.json_button, False), (self.zip_button, True)):
            button.setEnabled(False)
            button.clicked.connect(lambda checked=False, b=bundle: self.save(b))
            layout.addWidget(button)

    def clear(self):
        self.report = None
        self.json_button.setEnabled(False)
        self.zip_button.setEnabled(False)

    def set_result(self, tool, request, sections):
        self.report = make_report(tool, request, sections)
        self.json_button.setEnabled(True)
        self.zip_button.setEnabled(True)

    def save(self, bundle):
        if self.report is None:
            return
        extension = 'zip' if bundle else 'json'
        filename, _ = QFileDialog.getSaveFileName(self, display(self, '분석 결과 저장'),
            f"quantgen-{self.report['tool']}.{extension}", f'Report (*.{extension})')
        if not filename:
            return
        try:
            save_desktop_export(filename, report_bytes(self.report, bundle=bundle), extension=extension)
        except (OSError, ValueError, TypeError) as exc:
            self.status.setText(f'저장 실패 · {type(exc).__name__} · 경로와 확장자를 확인하세요.')
            return
        self.status.setText('분석 보고서 저장 완료 · 공식 검증 NOT_RUN')
