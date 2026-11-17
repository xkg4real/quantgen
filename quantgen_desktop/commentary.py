"""Optional native AI commentary: explicit payload preview and explicit send.

Only selected calculation reports enter this panel. Owner rulings, rule stores,
paper orders, connection settings, account holdings and source paths do not.
"""
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QComboBox,QPushButton,QPlainTextEdit,QLineEdit,QCheckBox,QFrame
from core.research.ai_connection import error_message
from core.research.ai_output_check import AI_LABEL, NumberCheck, check_line
from core.research.presentation import safe_detail
from core.research.tool_export import plain
from core.research.ai_payload import AI_PAYLOAD_MAX_BYTES, filter_analysis_fields, private_field
from core.ficc.insights import deep_analysis
from .jobs import Jobs
from .report_actions import ReportActions


ALLOWED={'monte_carlo','portfolio','bonds','rates','fx','structuring','signals','macro','derivatives','etf','crypto','krx','strategy'}


class _PayloadError(ValueError):
    def __init__(self,code):
        self.code=code
        super().__init__(error_message(code))


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
    try:
        raw=json.dumps(payload,ensure_ascii=False,allow_nan=False,sort_keys=True).encode('utf-8')
    except (TypeError,ValueError):
        raise _PayloadError('PAYLOAD_INVALID') from None
    # The send side measures the same UTF-8 JSON with the same '>' (core.research.ai_payload).
    if len(raw)>AI_PAYLOAD_MAX_BYTES:raise _PayloadError('PAYLOAD_TOO_LARGE')
    return payload


CONSENT_WORDS=('Send the displayed calculation and question to the external AI service',
               '표시한 계산 결과와 질문을 외부 AI 서비스로 전송')


def _ConsentText(box):
    """The consent check box's words as a wrapping label; a click on them toggles the box (docked pane only)."""
    from .page_kit import Text

    class ConsentText(Text):
        def mouseReleaseEvent(self, event):
            if event.button()==Qt.MouseButton.LeftButton and box.isEnabled() and self.rect().contains(event.position().toPoint()):
                box.toggle();return
            super().mouseReleaseEvent(event)
    text=ConsentText(CONSENT_WORDS,'',wrap=True)
    text.setProperty('lib','consent')
    text.setCursor(Qt.CursorShape.PointingHandCursor)
    return text


class CommentaryPane(QWidget):
    def __init__(self,sources,runner=deep_analysis):
        super().__init__()
        from .app import label
        self.sources,self.runner=sources,runner
        self.payload,self.completed_payload=None,None
        layout=QVBoxLayout(self)
        self.docked=False
        self.heading=label('AI 해설 · 선택 기능','heading');layout.addWidget(self.heading)
        self.prompt='계산 결과를 선택하고 전송 내용을 확인한 뒤 요청하세요. 기존 Anthropic API 연결을 사용합니다.'
        self.status=label(self.prompt,'muted')
        layout.addWidget(self.status)
        self.input_box=QWidget();controls=QVBoxLayout(self.input_box);row=QHBoxLayout();self._controls,self._row=controls,row
        self.source=QComboBox();self.reload=QPushButton('완료 결과 목록 갱신');self.preview_button=QPushButton('전송 내용 미리보기')
        for w in (self.source,self.reload,self.preview_button):row.addWidget(w)
        controls.addLayout(row)
        self.preview=QPlainTextEdit();self.preview.setReadOnly(True);self.preview.setMinimumHeight(220);controls.addWidget(self.preview)
        self.question=QLineEdit();self.question.setPlaceholderText('궁금한 점 · 비밀번호나 계좌정보는 입력하지 마세요');controls.addWidget(self.question)
        self.consent=QCheckBox('표시한 계산 결과와 질문을 외부 AI 서비스로 전송');controls.addWidget(self.consent)
        # Owner B3: the button always answers. It walks the user through the steps it needs
        # (choose a result → preview → consent); nothing is sent without the consent tick.
        self.send=QPushButton('AI 해설 요청');self.send.setCursor(Qt.CursorShape.PointingHandCursor)
        controls.addWidget(self.send);layout.addWidget(self.input_box)
        self.output=QPlainTextEdit();self.output.setReadOnly(True);self.output.setMinimumHeight(250);layout.addWidget(self.output)
        # 'Not verified' label and advisory number check of a finished reply; empty until one exists.
        self.check_note=label('','muted');layout.addWidget(self.check_note)
        self.report_actions=ReportActions(self.status);layout.addWidget(self.report_actions)
        self.jobs=Jobs(self);self.jobs.succeeded.connect(self.finished);self.jobs.failed.connect(self.failed)
        self.jobs.busy_changed.connect(lambda busy:self.input_box.setEnabled(not busy))
        self.reload.clicked.connect(self.refresh_sources);self.preview_button.clicked.connect(self.prepare)
        self.source.currentIndexChanged.connect(self.invalidate);self.consent.toggled.connect(lambda _:self._mark_ready())
        self.send.clicked.connect(self.submit);self.question.textEdited.connect(self._question_edited)

    def _question_edited(self,_text):
        # Consent covers the question as it stood when ticked; an edited question needs it again.
        if self.consent.isChecked():
            self.consent.setChecked(False)
            self.status.setText('질문이 바뀌었습니다. 전송 동의에 다시 체크하세요.')

    def _mark_ready(self):
        self.send.setProperty('primary',self.payload is not None and self.consent.isChecked())
        self.send.style().unpolish(self.send);self.send.style().polish(self.send)

    def showEvent(self,event):
        super().showEvent(event)
        if self.source.count()==0 and not self.jobs.busy:self.refresh_sources()

    def invalidate(self,*_):
        self.payload=None;self.consent.setChecked(False);self._mark_ready();self.preview.clear()
        self.output.clear();self.check_note.setText('');self.report_actions.clear()
        self._sync()

    def refresh_sources(self):
        self.invalidate();self.source.clear()
        for title,report in self.sources():self.source.addItem(title,deepcopy(report))
        if self.source.count()==0:self.status.setText('먼저 계산을 완료하세요. 실패·미실행 기록은 전송하지 않습니다.')
        elif self.docked:self.status.setText(self.prompt)   # a stale 'complete a calculation first' would mislead

    def prepare(self):
        self.invalidate()
        try:
            report=self.source.currentData()
            if report is None:raise ValueError('Choose a completed result')
            self.payload=commentary_payload(report)
        except _PayloadError as exc:
            self.status.setText(error_message(exc.code))
            self.status.localized_text={language:error_message(exc.code,language) for language in ('en','ko')}
            self.status.retranslate();return
        except (ValueError,TypeError) as exc:self.status.setText(safe_detail(exc));return
        self.preview.setPlainText(json.dumps(self.payload,ensure_ascii=False,indent=2,allow_nan=False))
        self.status.setText('이 내용과 질문을 QUANTGEN의 고정 작성 지침과 함께 전송합니다. 지침에는 계좌나 개인 정보가 없습니다. AI 해설은 공식 gate 판정을 변경하지 않습니다.')

    def submit(self):
        if self.jobs.busy:return
        if self.payload is None:
            if self.source.count()==0:self.refresh_sources()
            if self.source.count()==0:return  # refresh_sources already says to finish a calculation first
            self.prepare()
            if self.payload is not None:
                self.status.setText('전송할 내용을 아래에 표시했습니다. 확인한 뒤 전송 동의에 체크하고 다시 누르세요.')
                self.consent.setFocus()
            return
        if not self.consent.isChecked():
            self.status.setText('전송 동의에 체크해야 요청할 수 있습니다. 표시한 계산 결과와 질문을 QUANTGEN의 고정 작성 지침과 함께 외부 AI 서비스로 전송합니다.')
            self.consent.setFocus();return
        payload=deepcopy(self.payload);question=safe_detail(self.question.text(),limit=None)
        if len(question)>4000:self.status.setText('질문을 4,000자 이내로 입력하세요.');return
        self.completed_payload=payload;self.output.clear();self.check_note.setText('');self.report_actions.clear();self.status.setText('AI 해설 요청 중…')
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
        check=getattr(result,'number_check',None);check=check if isinstance(check,NumberCheck) else None
        redacted=text!=result.text
        if redacted:
            # The supplied check describes the original reply. Its numeric tokens may
            # disclose details removed above; keep that provenance on result, but do
            # not display/export it or imply the displayed reply was checked again.
            check=None
            check_lines={
                'en':'Number check: not shown because private details were removed from the reply. The displayed text was not checked again.',
                'ko':'숫자 대조: 응답의 비공개 정보를 가렸으므로 결과를 표시하지 않습니다. 표시된 글은 다시 대조하지 않았습니다.',
            }
        else:
            check_lines={language:check_line(check,language) for language in ('en','ko')}
        notes={language:AI_LABEL[language]+'\n'+check_lines[language] for language in ('en','ko')}
        self.check_note.setText(notes['ko']);self.check_note.localized_text=notes;self.check_note.retranslate()
        digest=hashlib.sha256(json.dumps(self.completed_payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        self.report_actions.set_result('ai_commentary',{'source_tool':self.completed_payload['tool'],'source_payload_sha256':digest,
            'stop_reason':getattr(result,'stop_reason','') or 'NOT_RECORDED','verification':'NOT_VERIFIED',
            'number_check':asdict(check) if check else None,
            'number_check_status':'WITHHELD_REDACTED_REPLY' if redacted else ('COMPLETED' if check else 'NOT_RUN'),
            'number_check_basis':'ORIGINAL_REPLY_BEFORE_DISPLAY_REDACTION' if redacted else ('DISPLAYED_REPLY' if check else 'NOT_RUN')},
            [{'type':'text','text':text},{'type':'text','text':'AI-generated commentary · '+safe_detail(result.engine)+' · official verdict unchanged'},
             {'type':'text','text':AI_LABEL['en']},{'type':'text','text':check_lines['en']}])
        self.status.setText('AI 해설 완료 · '+safe_detail(result.engine)+' · 공식 판정은 원래 기록을 유지합니다.')
        self._sync()

    def failed(self,error, *, localized=None):
        self.output.clear();self.check_note.setText('');self.report_actions.clear();self.status.setText('AI FAILED · '+safe_detail(error))
        if localized:
            self.status.localized_text = {'ko': localized}
            self.status.retranslate()
        self._sync()

    # The Research Library's right column (owner-approved draft 2026-11-17, draft_06_library.png) -------------------
    def dock(self, fold):
        """Place the pane in the library's 'AI 해설' fold: the fold names it, the refresh action sits in the fold's head,
        the picker reads '보낼 계산 결과' with a short preview button, and a prepared payload is summarised (what is sent,
        its status marks, what is left out) above the full JSON. The preview, the reply and its exports show once they
        hold something. Widgets, signals, consent and sending are unchanged."""
        from .page_kit import Text
        from .stock_detail_style import numbers
        self.docked = True
        self.heading.hide()
        layout = self.layout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self._controls.setContentsMargins(0, 0, 0, 0)
        self._controls.setSpacing(8)
        self.input_box.setProperty('lib', 'plain')    # the column's surface, not the window's background
        self._row.removeWidget(self.reload)
        self.reload.setProperty('lib', 'link')
        self.reload.setProperty('qg_literal', True)          # its short label follows set_language
        self.reload.setCursor(Qt.CursorShape.PointingHandCursor)
        fold.head.layout().addWidget(self.reload, 0, Qt.AlignmentFlag.AlignVCenter)
        self.jobs.busy_changed.connect(lambda busy: self.reload.setEnabled(not busy))   # outside input_box now
        self.preview_button.setProperty('qg_literal', True)   # its short label follows set_language
        self.preview_button.setProperty('kit', 'secondary')
        self._row.setSpacing(8)
        self._row.setStretch(0, 1)
        self.source_caption = Text(('Result to send', '보낼 계산 결과'), 'fieldLabel')
        self._controls.insertWidget(0, self.source_caption)
        layout.removeWidget(self.status)
        self.status.setProperty('kit', 'hint')
        self.summary = QFrame()
        self.summary.setProperty('lib', 'payload')
        box = QVBoxLayout(self.summary)
        box.setContentsMargins(12, 10, 12, 10)
        box.setSpacing(5)
        head = QHBoxLayout()
        head.setSpacing(10)
        title = Text(('Payload', '전송 내용'), '')
        title.setProperty('lib', 'payloadHead')
        self.summary_note = numbers(Text('', '', wrap=True))   # fits the 320 px column in English
        self.summary_note.setProperty('lib', 'payloadNote')
        self.summary_note.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        head.addWidget(title)
        head.addWidget(self.summary_note, 1)
        box.addLayout(head)
        self.summary_rows = []
        for _ in range(2):
            line = QHBoxLayout()
            line.setSpacing(10)
            key, value = Text('', ''), Text('', '', wrap=True)
            key.setProperty('lib', 'payloadKey')
            value.setProperty('lib', 'payloadValue')
            value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            line.addWidget(key, 0, Qt.AlignmentFlag.AlignTop)
            line.addWidget(value, 1)
            box.addLayout(line)
            self.summary_rows.append((key, value))
        self._controls.insertWidget(2, self.summary)
        self._controls.insertWidget(3, self.status)
        # The consent's words wrap beside its box: a check box cannot wrap, and its English line is wider than the
        # column. Clicking the words ticks the box, as clicking a check box's own text does.
        index = self._controls.indexOf(self.consent)
        self._controls.removeWidget(self.consent)
        self.consent.setText('')
        self.consent.setProperty('qg_literal', True)
        self.consent_text = _ConsentText(self.consent)
        consent_row = QHBoxLayout()
        consent_row.setContentsMargins(0, 0, 0, 0)
        consent_row.setSpacing(8)
        consent_row.addWidget(self.consent, 0, Qt.AlignmentFlag.AlignTop)
        consent_row.addWidget(self.consent_text, 1)
        self._controls.insertLayout(index, consent_row)
        self.preview.setMinimumHeight(150)
        self.output.setMinimumHeight(160)
        self.preview.textChanged.connect(self._sync)
        self.output.textChanged.connect(self._sync)
        self.set_language(getattr(self.window(), 'ui_language', 'ko'))
        self._sync()
        return self

    def set_language(self, language):
        if not self.docked:
            return
        from .page_kit import pick
        self.language = language
        self.reload.setText(pick(language, ('Refresh list', '완료 결과 목록 갱신')))
        self.reload.setAccessibleName(pick(language, ('Refresh completed results', '완료 결과 목록 갱신')))
        self.preview_button.setText(pick(language, ('Preview', '미리보기')))
        self.preview_button.setAccessibleName(pick(language, ('Preview the payload', '전송 내용 미리보기')))
        self.consent.setAccessibleName(pick(language, CONSENT_WORDS))
        for widget in (self.source_caption, self.summary_note, self.consent_text,
                       *[w for pair in self.summary_rows for w in pair]):
            widget.set_language(language)
        self._sync()

    def _sync(self, *_):
        """Docked only: show the payload summary, the JSON preview, the reply and its exports once they exist."""
        if not getattr(self, 'docked', False):
            return
        from .library_view import payload_summary
        self.preview.setVisible(bool(self.preview.toPlainText()))
        self.output.setVisible(bool(self.output.toPlainText()))
        self.check_note.setVisible(bool(self.check_note.text()))
        self.report_actions.setVisible(self.report_actions.report is not None)
        self.summary.setVisible(self.payload is not None)
        if self.payload is not None:
            try:
                head, rows = payload_summary(self.payload)
            except (TypeError, ValueError):
                self.summary.hide()
                return
            self.summary_note.set_pair(head)
            for (key, value), (caption, text) in zip(self.summary_rows, rows):
                key.set_pair(caption)
                value.set_pair(text)
