"""Optional native AI commentary: explicit payload preview and explicit send.

Only selected calculation reports enter this panel. Owner rulings, rule stores,
paper orders, connection settings, account holdings and source paths do not.
"""
from copy import deepcopy
import hashlib
import json

from PyQt6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QComboBox,QPushButton,QPlainTextEdit,QLineEdit,QCheckBox
from core.research.ai_connection import error_message
from core.research.presentation import safe_detail
from core.research.tool_export import plain
from core.research.ai_payload import filter_analysis_fields, private_field
from core.ficc.insights import deep_analysis
from .jobs import Jobs
from .report_actions import ReportActions


ALLOWED={'monte_carlo','portfolio','bonds','rates','fx','structuring','signals','macro','derivatives','etf','crypto','krx','strategy'}


def commentary_payload(report):
    tool=report.get('tool')
    if tool not in ALLOWED or report.get('execution_status')!='COMPLETED':
        raise ValueError('Select a completed calculation report')
    sections=[]
    for section in report.get('sections',[]):
        if private_field(section.get('name','')):continue
        sections.append(filter_analysis_fields(section))
    payload=plain({'tool':tool,'parameters':filter_analysis_fields(report.get('parameters',{})),
        'sections':sections,'official_verdict':report.get('verdict','NOT_RUN'),
        'reproducibility':report.get('reproducibility','PARTIAL'),'data_rights':report.get('data_rights','NOT_VERIFIED')})
    raw=json.dumps(payload,ensure_ascii=False,allow_nan=False,sort_keys=True)
    if len(raw.encode('utf-8'))>180_000:raise ValueError('Report is too large for commentary; choose a smaller calculation')
    return payload


class CommentaryPane(QWidget):
    def __init__(self,sources,runner=deep_analysis):
        super().__init__()
        from .app import label
        self.sources,self.runner=sources,runner
        self.payload,self.completed_payload=None,None
        layout=QVBoxLayout(self)
        layout.addWidget(label('AI 해설 · 선택 기능','heading'))
        self.status=label('계산 결과를 선택하고 전송 내용을 확인한 뒤 요청하세요. 기존 Anthropic API 연결을 사용합니다.','muted')
        layout.addWidget(self.status)
        self.input_box=QWidget();controls=QVBoxLayout(self.input_box);row=QHBoxLayout()
        self.source=QComboBox();self.reload=QPushButton('완료 결과 목록 갱신');self.preview_button=QPushButton('전송 내용 미리보기')
        for w in (self.source,self.reload,self.preview_button):row.addWidget(w)
        controls.addLayout(row)
        self.preview=QPlainTextEdit();self.preview.setReadOnly(True);self.preview.setMinimumHeight(220);controls.addWidget(self.preview)
        self.question=QLineEdit();self.question.setPlaceholderText('궁금한 점 · 비밀번호나 계좌정보는 입력하지 마세요');controls.addWidget(self.question)
        self.consent=QCheckBox('표시한 계산 결과와 질문을 외부 AI 서비스로 전송');controls.addWidget(self.consent)
        self.send=QPushButton('AI 해설 요청');self.send.setEnabled(False);controls.addWidget(self.send);layout.addWidget(self.input_box)
        self.output=QPlainTextEdit();self.output.setReadOnly(True);self.output.setMinimumHeight(250);layout.addWidget(self.output)
        self.report_actions=ReportActions(self.status);layout.addWidget(self.report_actions)
        self.jobs=Jobs(self);self.jobs.succeeded.connect(self.finished);self.jobs.failed.connect(self.failed)
        self.jobs.busy_changed.connect(lambda busy:self.input_box.setEnabled(not busy))
        self.reload.clicked.connect(self.refresh_sources);self.preview_button.clicked.connect(self.prepare)
        self.source.currentIndexChanged.connect(self.invalidate);self.consent.toggled.connect(lambda _:self.send.setEnabled(self.payload is not None and self.consent.isChecked()))
        self.send.clicked.connect(self.submit)

    def invalidate(self,*_):
        self.payload=None;self.consent.setChecked(False);self.send.setEnabled(False);self.preview.clear()
        self.output.clear();self.report_actions.clear()

    def refresh_sources(self):
        self.invalidate();self.source.clear()
        for title,report in self.sources():self.source.addItem(title,deepcopy(report))
        if self.source.count()==0:self.status.setText('먼저 계산을 완료하세요. 실패·미실행 기록은 전송하지 않습니다.')

    def prepare(self):
        self.invalidate()
        try:
            report=self.source.currentData()
            if report is None:raise ValueError('Choose a completed result')
            self.payload=commentary_payload(report)
        except (ValueError,TypeError) as exc:self.status.setText(safe_detail(exc));return
        self.preview.setPlainText(json.dumps(self.payload,ensure_ascii=False,indent=2,allow_nan=False))
        self.status.setText('이 내용과 질문만 전송합니다. AI 해설은 공식 gate 판정을 변경하지 않습니다.')

    def submit(self):
        if self.jobs.busy or self.payload is None or not self.consent.isChecked():return
        payload=deepcopy(self.payload);question=safe_detail(self.question.text(),limit=None)
        if len(question)>4000:self.status.setText('질문을 4,000자 이내로 입력하세요.');return
        self.completed_payload=payload;self.output.clear();self.report_actions.clear();self.status.setText('AI 해설 요청 중…')
        kind=payload['tool']
        if kind=='macro':
            kind={'daily':'daily_market_commentary','weekly':'weekly_fi_fx_strategy'}.get(payload['parameters'].get('tool'),kind)
        self.jobs.start(lambda:self.runner(kind,payload,question=question))

    def finished(self,result):
        if result.error:
            code = getattr(result, 'error_code', '')
            localized = ('AI 해설 실패 · ' + error_message(code, 'ko', getattr(result, 'http_status', None))) if code else None
            self.failed(safe_detail(result.error), localized=localized)
            return
        text=safe_detail(result.text,limit=None)
        self.output.setPlainText(text)
        digest=hashlib.sha256(json.dumps(self.completed_payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        self.report_actions.set_result('ai_commentary',{'source_tool':self.completed_payload['tool'],'source_payload_sha256':digest},
            [{'type':'text','text':text},{'type':'text','text':'AI-generated commentary · '+safe_detail(result.engine)+' · official verdict unchanged'}])
        self.status.setText('AI 해설 완료 · '+safe_detail(result.engine)+' · 공식 판정은 원래 기록을 유지합니다.')

    def failed(self,error, *, localized=None):
        self.output.clear();self.report_actions.clear();self.status.setText('AI FAILED · '+safe_detail(error))
        if localized:
            self.status.localized_text = {'ko': localized}
            self.status.retranslate()
