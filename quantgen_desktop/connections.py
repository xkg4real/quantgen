"""Native connection status. Probes run only on explicit user action.

The System page (owner-approved draft 2026-11-17, docs/product/ui_drafts_2026-11-17/draft_07_system.png) lists the
providers `config` reports, grouped as the draft shows them: what each serves, the setting NAMES it reads (never a value),
whether they are set, and this session's last access test. The list is built from the presence report alone (local, no
network: the loaders `core.research.connections.execute_connections` reads for its presence check). A row's 확인 runs
the pane's own access test for that provider through the pane's request; every result the pane shows updates the rows.
"""
from datetime import date, datetime
import html

from PyQt6.QtCore import QEvent, QObject, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import (QAbstractScrollArea, QBoxLayout, QFrame, QHBoxLayout, QLabel, QSizePolicy,
                             QVBoxLayout, QWidget)
from .qt_compat import call_later

from core.research.connections import ConnectionRequest
from core.research.presentation import safe_detail
from core.theme import LIGHT
from .page_kit import Button, Card, KeyFigures, Text, pick
from .stock_detail_style import set_prop
from .tools import ToolPane

# The pane's checks (key, label); the labels are the catalogue's source text.
TOOLS = (('presence', '설정 여부 확인 · 네트워크 조회 없음'), ('krx', 'KRX 접속 검사'),
         ('ficc', 'FRED / Yahoo 접속 검사'), ('kis', 'KIS 자산 데이터 접속 검사'),
         ('crypto', 'Upbit / Binance 공개 데이터 접속 검사'))


class ConnectionsPane(ToolPane):
    checked = pyqtSignal(object)   # each result shown (presence or an access test); the System list follows it

    def __init__(self):
        tools = list(TOOLS)
        super().__init__('데이터 연결', tools, [('configured', '기존 연결 사용')], {k: [] for k, _ in tools})
        self.run.setText('선택한 연결 확인')
        self.status.setText('설정 여부와 실제 응답을 구분합니다. 키 값은 표시하거나 저장하지 않습니다.')

    def make_request(self):
        return ConnectionRequest(self.tool.currentData())

    def show_result(self, output):
        self.clear_result()
        self.result_table('연결 상태', ['Provider', 'Status', '설정 이름 / 경로', '설명'], output.rows)
        from .status_language import mark_status_column
        mark_status_column(self.tables['연결 상태'], 1, 'connection')
        if output.request.tool == 'presence':
            self.finished('CONFIGURED는 설정의 존재만 뜻합니다. 실제 접속 성공은 별도 검사로 확인하세요.')
        else:
            self.finished('읽기 전용 접속 검사 결과입니다. 계좌 조회·주문·연결 설정 변경은 수행하지 않습니다.')
        if not output.rows or any(r[1] == 'UNAVAILABLE' for r in output.rows):
            self.status.setText('검사 종료 · 응답 불가 항목이 있습니다.')
        self.checked.emit(output)


# --------------------------------------------------------------------------------------------------------------------
# What the list shows: only the providers config reports. The catalogue below gives each known provider its group, a
# short mark and its words in English and Korean (from config's own notes); a provider config adds later still appears,
# under 기타, with config's label and note.
# --------------------------------------------------------------------------------------------------------------------
GROUPS = (
    ('domestic', ('Korean market', '국내 시장'), ('KIS · KRX access tests', 'KIS · KRX 접속 검사')),
    ('global', ('Global · macro', '해외·매크로'), ('FRED / Yahoo access test', 'FRED / Yahoo 접속 검사')),
    ('crypto', ('Crypto', '가상자산'), ('Upbit / Binance public data access test', 'Upbit / Binance 공개 데이터 접속 검사')),
    ('assist', ('Analysis aids', '분석 보조'), ('Optional · analyses run without them', '선택 연결 · 없어도 분석은 실행돼요')),
    ('other', ('Other', '기타'), None),
)

# id: (group, mark, name, sub-label, what it serves, access test key)
PROVIDERS = {
    'kis': ('domestic', 'KIS', ('KIS', 'KIS'), ('Korea Investment & Securities', '한국투자증권'),
            ('Quotes, daily prices, KOSPI/KOSDAQ index levels', '국내 시세·일별 가격·KOSPI/KOSDAQ 지수'), 'kis'),
    'opendart': ('domestic', 'DART', ('OpenDART', 'OpenDART'), ('Financial Supervisory Service', '금융감독원'),
                 ('Filings and reported financials · free key', '공시·보고된 재무제표 · 무료 키'), None),
    'krx': ('domestic', 'KRX', ('KRX', 'KRX'), ('Data marketplace', 'Data marketplace'),
            ('Whole-market session snapshots · free API key', '시장 전체 세션 스냅샷 · 무료 Open API 키 필요'),
            'krx'),
    'fmp': ('global', 'FMP', ('Financial Modeling Prep', 'Financial Modeling Prep'), None,
            ('Dividend-adjusted US end-of-day prices', '배당 조정 미국 종가'), None),
    'fred': ('global', 'FRED', ('FRED', 'FRED'), ('St. Louis Fed', 'St. Louis Fed'),
             ('Treasury curve, SOFR, credit spreads, macro', '미 국채 곡선·SOFR·OECD 단기 금리·신용 스프레드·매크로'), 'ficc'),
    'yfinance': ('global', 'YF', ('Yahoo Finance', 'Yahoo Finance'), ('yfinance', 'yfinance'),
                 ('FX spot, futures and index levels', '환율·선물·지수 수준'), 'ficc'),
    'upbit': ('crypto', 'UB', ('Upbit', 'Upbit'), ('public data', '공개 데이터'),
              ('KRW-BTC daily since 2017-09-25', 'KRW-BTC 일별 가격 · 2017-09-25부터'), 'crypto'),
    'binance': ('crypto', 'BN', ('Binance', 'Binance'), ('public data', '공개 데이터'),
                ('Spot, futures, funding · may be blocked in Korea', '현물·선물 일별 가격, 펀딩비 · 국내 접속 제한 가능'), 'crypto'),
    'upbit_account': ('crypto', 'UB', ('Upbit account', 'Upbit 계정'), ('balance only', '자산조회 전용'),
                      ('Balance reads only · no order path', '잔고 조회만 · 주문 경로 없음'), None),
    'anthropic': ('assist', 'AI', ('Claude API', 'Claude API'), ('deep analysis', '심화 해설'),
                  ('AI reading of quant results · {model}', '퀀트 결과 AI 해설 · {model}'), None),
    'gs': ('assist', 'GS', ('GS Marquee', 'GS Marquee'), ('gs_quant session', 'gs_quant 세션'),
           ('Pricing · offline analytics need no key', '상품 가격 계산 · 오프라인 분석은 키 없이 가능'), None),
}

# The providers each access test answers for (`execute_connections` rows: KRX; fred, yfinance; KIS domains;
# upbit, binance_spot, binance_futures; or one row named after the test when the probe itself failed).
PROBE_PROVIDERS = {'krx': ('krx',), 'ficc': ('fred', 'yfinance'), 'kis': ('kis',), 'crypto': ('upbit', 'binance')}
TOOL_LABELS = dict(TOOLS)
PILLS = {'ok': ('● Configured', '● 설정됨'), 'warn': ('● Check needed', '● 확인 필요'), 'off': ('○ Not set', '○ 미설정')}

# Column widths of the list (the draft's grid: mark 34, name, setting names 146, set 92, access test 112, action 46;
# the action column is as wide as its button in the window language).
MARK_W, VARS_W, STATE_W, CHECK_W, ACTION_W, GAP = 34, 132, 88, 108, 46, 10
NAME_MIN = 190          # narrower than the columns plus this, a row puts its setting names under its name and
                        # 확인 under its status (compact)


def provider_entries(loaders=None):
    """{id: {'id', 'label', 'ready', 'vars', 'note'}} from config's presence-only reports. No value is read back:
    config returns names and a ready flag, and only those fields are kept."""
    if loaders is None:
        import config
        loaders = (config.krx_provider_status, config.ficc_provider_status, config.crypto_provider_status,
                   config.quant_provider_status)
    entries = {}
    for loader in loaders:
        for entry in loader():
            key = str(entry['id'])
            entries[key] = {'id': key, 'label': safe_detail(entry.get('label', key)), 'ready': bool(entry.get('ready')),
                            'vars': tuple(safe_detail(name) for name in entry.get('vars', ())),
                            'note': safe_detail(entry.get('note', ''))}
    return entries


def now_stamp():
    return datetime.now().strftime('%m-%d %H:%M')


def display_of(entry):
    """(group, mark, name pair, sub pair or None, serves pair, test key) for one entry."""
    known = PROVIDERS.get(entry['id'])
    if known is None:
        label = entry['label']
        mark = ''.join(ch for ch in label if ch.isalnum())[:4].upper() or '?'
        note = entry['note'] or ''
        return ('other', mark, (label, label), None, (note, note), None)
    group, mark, name, sub, serves, test = known
    if '{model}' in serves[0]:
        model = entry['note'].rsplit('Model:', 1)[-1].strip().rstrip('.') if 'Model:' in entry['note'] else ''
        serves = tuple(text.format(model=model).rstrip(' ·') for text in serves)
    return (group, mark, name, sub, serves, test)


def system_sheet(p, dark):
    """The list's and the side column's own rules, on top of the page kit's."""
    from .stock_detail_style import line_color
    from .typography import TONE_COLORS, mix
    t = TONE_COLORS[bool(dark)]
    line = line_color(p)
    faint = mix(p.muted, p.surface, 0.42)
    return f"""
      QWidget#sysPlain {{ background: transparent; }}
      QLabel[sys='mark'] {{ background: {p.surface_2}; color: {p.accent}; border-radius: 9px; font-size: 11px;
                            font-weight: 600; }}
      QLabel[sys='status'], QLabel[sys='note'] {{ font-size: 12px; color: {p.muted}; }}
      QLabel[sys='desc'] {{ font-size: 12px; color: {p.muted}; }}
      QLabel[sys='vars'] {{ font-size: 11px; color: {p.muted}; }}
      QLabel[sys='vars'][none='true'] {{ font-size: 12px; color: {faint}; }}
      QLabel[sys='state'] {{ font-size: 12px; font-weight: 500; padding: 3px 9px; border-radius: 10px;
                             color: {p.muted}; background: {p.surface_2}; }}
      QLabel[sys='state'][tone='ok'] {{ color: {p.success}; background: {p.accent_soft}; }}
      QLabel[sys='state'][tone='warn'] {{ color: {p.warning}; background: {t['flat_tint']}; }}
      QLabel[sys='check'] {{ font-size: 12px; color: {p.muted}; }}
      QLabel[sys='check'][tone='ok'] {{ color: {p.success}; }}
      QLabel[sys='check'][tone='warn'] {{ color: {p.warning}; }}
      QLabel[sys='check'][tone='bad'] {{ color: {p.error}; }}
      QLabel[sys='time'], QLabel[sys='groupNote'], QLabel[sys='foot'] {{ font-size: 11px; color: {faint}; }}
      QLabel[sys='head'], QLabel[sys='group'] {{ font-size: 12px; font-weight: 500; color: {p.muted}; }}
      QLabel[sys='groupCount'], QLabel[sys='dash'] {{ font-size: 12px; color: {faint}; }}
      QLabel[sys='sample'] {{ background: {p.surface_2}; color: {p.muted}; border-radius: 9px; padding: 8px 10px;
                              font-size: 13px; }}
      QFrame[sys='line'] {{ background: {line}; border: 0; }}
      QFrame[sys='record'] QLabel {{ font-size: 13px; }}
      QFrame[sys='record'] QLabel[kit='cardTitle'] {{ font-size: 15px; }}
      QPushButton[sys='check'] {{ padding: 5px 10px; border: 0; border-radius: 8px; background: {p.surface_2};
                                  color: {p.text}; font-size: 12px; font-weight: 500; }}
      QPushButton[sys='check']:hover {{ background: {p.accent_soft}; color: {p.accent}; }}
      QPushButton[sys='check']:focus {{ border: 2px solid {p.accent}; padding: 3px 8px; }}
      QPushButton[sys='check']:disabled {{ color: {faint}; }}
    """


def plain_backgrounds(root):
    """Plain container widgets take the window sheet's `QWidget { background }`; on a card or in the right column
    that shows as grey boxes. Name them so `system_sheet` keeps them transparent (named widgets keep their name)."""
    for widget in (root, *root.findChildren(QWidget)):
        if type(widget) is QWidget and not widget.objectName():
            widget.setObjectName('sysPlain')


def dock_connection_form(pane, side, page):
    """The pane's form in the right column (`tools.dock_form`), with 도구 and 데이터 출처 one above the other at the
    column's full width (the draft's wide fields), its run button pinned in the column's foot and its status line
    under that button. The panel's own heading is hidden: the fold around it names the section."""
    from .tools import dock_form
    dock_form(pane.input_box, pane.run, side, page=page)
    grid = getattr(pane, '_top_grid', None)
    if grid is not None:
        cells = [grid.itemAtPosition(row, column) for column in range(2) for row in range(2)]
        widgets = [cell.widget() for cell in cells if cell is not None and cell.widget() is not None]
        for widget in widgets:
            grid.removeWidget(widget)
        for index, widget in enumerate(widgets):
            grid.addWidget(widget, index, 0)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 0)
        grid.setVerticalSpacing(6)
        for combo in (pane.tool, pane.source):
            combo.setMinimumContentsLength(8)   # the whole option stays in the popup and the tooltip
    for heading in pane.input_box.findChildren(QLabel):
        if heading.property('role') == 'heading':
            heading.hide()
            break
    pane.status.setProperty('sys', 'status')
    pane.status.setAlignment(Qt.AlignmentFlag.AlignHCenter)
    side.foot.addWidget(pane.status)


def sys_text(pair='', role='', *, wrap=False):
    widget = Text(pair, wrap=wrap)
    widget.setProperty('sys', role)
    return widget


def line():
    frame = QFrame()
    frame.setProperty('sys', 'line')
    frame.setFixedHeight(1)
    return frame


class LiveText(Text):
    """A Text worked out again at each language change (`source(language) -> str`), e.g. a format sample of the
    window locale: the page kit calls `set_language` after the window's locale changes."""

    def __init__(self, source, kit='', **options):
        self.source = source
        super().__init__('', kit, **options)

    def render(self):
        try:
            value = self.source(self.language)
        except Exception:
            value = '—'
        if self.text() != value:
            self.setText(value)


class RowButton(Button):
    """A row's 확인; read aloud with its provider ("KIS 확인", "Check KIS")."""

    def __init__(self, name):
        self.name_pair = name
        super().__init__(('Check', '확인'), '')

    def render(self):
        super().render()
        name = pick(self.language, self.name_pair)
        self.setAccessibleName(f'{name} 확인' if self.language == 'ko' else f'Check {name}')


class ProviderRow(QWidget):
    """One provider: mark, name and what it serves, the setting names, set or not, the last access test, 확인."""

    def __init__(self, entry, on_check):
        super().__init__()
        self.entry = entry
        self.group, self.mark, self.name, self.sub, self.serves, self.test = display_of(entry)
        self.ready = entry['ready']
        self.read_at = None          # when the presence was read
        self.probe = None            # {'state': 'ok'|'partial'|'fail', 'ok', 'total', 'at'}
        self.language, self.colors, self.compact = 'ko', LIGHT, None
        row = QHBoxLayout(self)
        row.setContentsMargins(8, 7, 8, 7)
        row.setSpacing(GAP)
        mark = sys_text(self.mark, 'mark')
        mark.setFixedSize(MARK_W, 30)
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(mark, 0, Qt.AlignmentFlag.AlignVCenter)
        block = QVBoxLayout()
        block.setContentsMargins(0, 0, 0, 0)
        block.setSpacing(2)
        self.title = QLabel()
        self.title.setProperty('qg_literal', True)
        self.title.setTextFormat(Qt.TextFormat.RichText)
        self.title.setWordWrap(True)
        self.desc = sys_text(self.serves, 'desc', wrap=True)
        names = '\n'.join(entry['vars'])
        none = ('No key needed', '키 필요 없음')
        self.vars_inline = sys_text(names or none, 'vars', wrap=True)
        for widget in (self.title, self.desc, self.vars_inline):
            block.addWidget(widget)
        row.addLayout(block, 1)
        self.vars = sys_text(names or none, 'vars', wrap=True)
        for widget in (self.vars, self.vars_inline):
            widget.setProperty('none', 'false' if names else 'true')
        self.vars.setFixedWidth(VARS_W)
        row.addWidget(self.vars, 0, Qt.AlignmentFlag.AlignVCenter)
        self.state = QWidget()
        self.state_box = QBoxLayout(QBoxLayout.Direction.LeftToRight, self.state)
        self.state_box.setContentsMargins(0, 0, 0, 0)
        self.state_box.setSpacing(GAP)
        pill_host = QWidget()
        pill_row = QHBoxLayout(pill_host)
        pill_row.setContentsMargins(0, 0, 0, 0)
        self.pill = sys_text('', 'state')
        pill_row.addWidget(self.pill)
        pill_row.addStretch(1)
        pill_host.setFixedWidth(STATE_W)
        self.pill_host = pill_host
        check_host = QWidget()
        check = QVBoxLayout(check_host)
        check.setContentsMargins(0, 0, 0, 0)
        check.setSpacing(1)
        self.check = sys_text('', 'check', wrap=True)
        self.time = sys_text('', 'time')
        check.addWidget(self.check)
        check.addWidget(self.time)
        check_host.setFixedWidth(CHECK_W)
        self.state_box.addWidget(pill_host, 0, Qt.AlignmentFlag.AlignVCenter)
        self.state_box.addWidget(check_host, 0, Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(self.state, 0, Qt.AlignmentFlag.AlignVCenter)
        # The action column: 확인 where the pane has an access test for this provider, a dash where it has none.
        self.action = QWidget()
        self.action.setFixedWidth(ACTION_W)
        self.actions = QHBoxLayout(self.action)
        self.actions.setContentsMargins(0, 0, 0, 0)
        if self.test is not None:
            self.button = RowButton(self.name)
            self.button.setProperty('kit', None)
            self.button.setProperty('sys', 'check')
            self.button.clicked.connect(lambda checked=False: on_check(self.test))
            self.actions.addWidget(self.button, 0, Qt.AlignmentFlag.AlignRight)
        else:
            self.button = None
            dash = sys_text('—', 'dash')
            self.actions.addWidget(dash, 0, Qt.AlignmentFlag.AlignRight)
        self.row = row
        row.addWidget(self.action, 0, Qt.AlignmentFlag.AlignVCenter)
        self.widths = (STATE_W, ACTION_W)
        self.set_compact(False)
        self.render()

    # State -------------------------------------------------------------------------------------------------------
    def tone(self):
        if self.probe is not None and self.probe['state'] != 'ok':
            return 'warn'
        return 'ok' if self.ready else 'off'

    def set_ready(self, ready, at):
        self.ready, self.read_at = bool(ready), at
        self.render()

    def set_probe(self, state, ok, total, details, at):
        self.probe = {'state': state, 'ok': ok, 'total': total, 'at': at}
        self.check.setToolTip('\n'.join(details))
        self.render()

    def render(self):
        tone = self.tone()
        self.pill.set_pair(PILLS[tone])
        set_prop(self.pill, 'tone', '' if tone == 'off' else tone)
        if self.probe is not None:
            state, ok, total = self.probe['state'], self.probe['ok'], self.probe['total']
            text = {'ok': ('Responded', '응답 확인'), 'fail': ('No response', '응답 없음'),
                    'partial': (f'Partial {ok}/{total}', f'일부 응답 {ok}/{total}')}[state]
            self.check.set_pair(text)
            set_prop(self.check, 'tone', {'ok': 'ok', 'fail': 'bad', 'partial': 'warn'}[state])
            self.time.set_pair(self.probe['at'])
        elif self.test is not None:
            self.check.set_pair(('Not tested yet', '접속 검사 전'))
            set_prop(self.check, 'tone', '')
            self.time.set_pair('')
        else:
            self.check.set_pair(('Settings only', '설정만 확인'))
            set_prop(self.check, 'tone', '')
            self.time.set_pair(self.read_at or '')
        self.time.setVisible(bool(self.time.text()))
        self.render_title()
        if self.button is not None:
            self.button.setToolTip(TOOL_LABELS.get(self.test, ''))

    def render_title(self):
        p = self.colors
        name = html.escape(pick(self.language, self.name))
        text = f"<span style='font-size:14px; font-weight:500; color:{p.text}'>{name}</span>"
        if self.sub is not None:
            text += f"&nbsp; <span style='font-size:12px; color:{p.muted}'>{html.escape(pick(self.language, self.sub))}</span>"
        if self.title.text() != text:
            self.title.setText(text)
        self.title.setAccessibleName(pick(self.language, self.name))

    def set_compact(self, compact):
        """Wide: the draft's columns. Compact (a narrow canvas): the setting names go under the name, and the status,
        the access test and 확인 stack in one column, so the name keeps room to read."""
        if compact == self.compact:
            return
        self.compact = compact
        self.vars.setVisible(not compact)
        self.vars_inline.setVisible(compact)
        self.state_box.setDirection(QBoxLayout.Direction.TopToBottom if compact else QBoxLayout.Direction.LeftToRight)
        self.state_box.setSpacing(4 if compact else GAP)
        if compact:
            self.row.removeWidget(self.action)
            self.state_box.addWidget(self.action, 0, Qt.AlignmentFlag.AlignLeft)
            self.action.setVisible(self.button is not None)
        else:
            self.state_box.removeWidget(self.action)
            self.row.addWidget(self.action, 0, Qt.AlignmentFlag.AlignVCenter)
            self.action.show()
        self.fit(*self.widths)

    def fit(self, state, action):
        """Column widths for the window language: the status column as wide as its widest pill, the action column as
        its widest 확인 (English words are wider than the draft's Korean)."""
        self.widths = (state, action)
        stacked = max(CHECK_W, state)
        if self.compact:
            self.state.setFixedWidth(stacked)
            self.pill_host.setFixedWidth(stacked)
            self.action.setFixedWidth(stacked)
            if self.button is not None:
                self.actions.setAlignment(self.button, Qt.AlignmentFlag.AlignLeft)
        else:
            self.state.setFixedWidth(state + GAP + CHECK_W)
            self.pill_host.setFixedWidth(state)
            self.action.setFixedWidth(action)
            if self.button is not None:
                self.actions.setAlignment(self.button, Qt.AlignmentFlag.AlignRight)

    def pill_width(self):
        """The widest of this row's three pill texts in the window language, with the pill's padding."""
        from PyQt6.QtGui import QFontMetrics
        self.pill.ensurePolished()
        metrics = QFontMetrics(self.pill.font())
        texts = [pick(self.language, pair) for pair in PILLS.values()]
        frame = self.pill.sizeHint().width() - metrics.horizontalAdvance(self.pill.text())   # padding and margins
        return max(metrics.horizontalAdvance(text) for text in texts) + max(frame, 2 * 9) + 2

    def set_language(self, language):
        self.language = language
        if self.button is not None:
            self.button.set_language(language)   # before the list measures the action column
        self.render()

    def set_theme(self, colors):
        self.colors = colors
        self.render_title()


class ConnectionList(QWidget):
    """The draft's list: a column header, then one group per kind of provider and a row per provider."""
    check_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.rows = {}
        self.groups = []
        self.language, self.compact = 'ko', None
        self.widths = (STATE_W, ACTION_W)
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(0)
        head = QWidget()
        heads = QHBoxLayout(head)
        heads.setContentsMargins(8, 9, 8, 9)
        heads.setSpacing(GAP)
        spacer = QWidget()
        spacer.setFixedWidth(MARK_W)
        heads.addWidget(spacer)
        self.head_name = sys_text(('Provider · used for', '공급처 · 쓰는 곳'), 'head')
        self.head_vars = sys_text(('Setting names', '설정 이름'), 'head')
        self.head_state = sys_text(('Setting', '설정 여부'), 'head')
        self.head_check = sys_text(('Access test', '접속 검사'), 'head')
        heads.addWidget(self.head_name, 1)
        for widget, width in ((self.head_vars, VARS_W), (self.head_state, STATE_W), (self.head_check, CHECK_W)):
            widget.setFixedWidth(width)
            heads.addWidget(widget)
        self.head_action = QWidget()
        self.head_action.setFixedWidth(ACTION_W)
        heads.addWidget(self.head_action)
        column.addWidget(head)
        column.addWidget(line())
        self.body = QVBoxLayout()
        self.body.setContentsMargins(0, 0, 0, 0)
        self.body.setSpacing(0)
        column.addLayout(self.body)
        self.empty = sys_text(('Could not read the settings · run “Check configuration” on the right.',
                               '설정을 읽지 못했어요 · 오른쪽에서 설정 여부 확인을 실행해 보세요.'), 'desc', wrap=True)
        self.empty.setContentsMargins(8, 16, 8, 16)
        self.empty.hide()
        column.addWidget(self.empty)
        self.set_compact(False)

    def build(self, entries, at):
        while self.body.count():
            item = self.body.takeAt(0)
            if item.widget() is not None:
                item.widget().hide()
                item.widget().deleteLater()
        self.rows, self.groups = {}, []
        self.empty.setVisible(not entries)
        by_group = {}
        order = {key: index for index, key in enumerate(PROVIDERS)}   # the draft's order inside a group
        for entry in sorted(entries.values(), key=lambda entry: order.get(entry['id'], len(order))):
            by_group.setdefault(display_of(entry)[0], []).append(entry)
        for key, title, note in GROUPS:
            members = by_group.get(key, ())
            if not members:
                continue
            head = QWidget()
            heads = QHBoxLayout(head)
            heads.setContentsMargins(8, 12, 8, 4)
            heads.setSpacing(8)
            heads.addWidget(sys_text(title, 'group'), 0, Qt.AlignmentFlag.AlignBottom)
            heads.addWidget(sys_text(str(len(members)), 'groupCount'), 0, Qt.AlignmentFlag.AlignBottom)
            heads.addStretch(1)
            if note is not None:
                remark = sys_text(note, 'groupNote', wrap=True)
                remark.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
                heads.addWidget(remark, 0, Qt.AlignmentFlag.AlignBottom)
            self.body.addWidget(head)
            self.groups.append(head)
            for index, entry in enumerate(members):
                if index:
                    self.body.addWidget(line())
                row = ProviderRow(entry, self.check_requested.emit)
                row.read_at = at
                row.set_language(self.language)
                row.set_compact(bool(self.compact))
                self.rows[entry['id']] = row
                self.body.addWidget(row)
        plain_backgrounds(self)
        self.fit_columns()

    def fit_columns(self):
        """Every row's status and action columns as wide as their widest content in the window language."""
        buttons = [row.button for row in self.rows.values() if row.button is not None]
        for button in buttons:
            button.ensurePolished()
        action = max([ACTION_W] + [button.sizeHint().width() for button in buttons])
        state = max([STATE_W] + [row.pill_width() for row in list(self.rows.values())[:1]])
        self.widths = (state, action)
        self.head_action.setFixedWidth(action)
        self.head_state.setFixedWidth(max(CHECK_W, state) if self.compact else state)
        for row in self.rows.values():
            row.fit(state, action)
        self.set_compact(self.width() < self.wide_needs())

    def wide_needs(self):
        """The width the draft's columns need with a readable name column."""
        state, action = self.widths
        return 16 + MARK_W + VARS_W + state + CHECK_W + action + 5 * GAP + NAME_MIN

    def apply_presence(self, rows, at):
        """A presence result (label, CONFIGURED | NOT_CONFIGURED, names, note) updates the rows it names."""
        by_label = {row.entry['label']: row for row in self.rows.values()}
        for values in rows:
            row = by_label.get(str(values[0])) if values else None
            if row is not None and len(values) > 1:
                row.set_ready(values[1] == 'CONFIGURED', at)

    def apply_probe(self, test, rows, at):
        """An access test result (name, REACHABLE | UNAVAILABLE, path, detail) updates the providers it answers for."""
        targets = [key for key in PROBE_PROVIDERS.get(test, ()) if key in self.rows]
        if not targets:
            return
        found = {key: [] for key in targets}
        for values in rows:
            values = tuple(values or ())
            if not values:
                continue
            name = str(values[0]).strip().lower()
            hits = [key for key in targets if name == key or name.startswith(key + '_')]
            if not hits:
                hits = targets   # one provider per test (KIS domains), or the test's own failure row
            for key in hits:
                found[key].append(values)
        for key, answers in found.items():
            if not answers:
                continue
            ok = sum(1 for values in answers if len(values) > 1 and values[1] == 'REACHABLE')
            total = len(answers)
            state = 'ok' if ok == total else 'partial' if ok else 'fail'
            details = [' · '.join(safe_detail(v, limit=200) for v in values[:2] + tuple(v for v in values[3:4] if v))
                       for values in answers]
            self.rows[key].set_probe(state, ok, total, details, at)

    def counts(self):
        tones = [row.tone() for row in self.rows.values()]
        probed = [row.probe for row in self.rows.values() if row.probe is not None]
        last = max((probe['at'] for probe in probed), default=None)
        return {'ok': tones.count('ok'), 'warn': tones.count('warn'), 'off': tones.count('off'),
                'answered': sum(1 for probe in probed if probe['state'] == 'ok'), 'probed': len(probed), 'last': last}

    def set_buttons_enabled(self, enabled):
        for row in self.rows.values():
            if row.button is not None:
                row.button.setEnabled(enabled)

    def set_compact(self, compact):
        if compact == self.compact:
            return
        self.compact = compact
        self.head_vars.setVisible(not compact)
        self.head_check.setVisible(not compact)
        self.head_state.set_pair(('Setting · access test', '설정 여부 · 접속 검사') if compact
                                 else ('Setting', '설정 여부'))
        state, _action = self.widths
        self.head_state.setFixedWidth(max(CHECK_W, state) if compact else state)
        self.head_action.setVisible(not compact)
        for row in self.rows.values():
            row.set_compact(compact)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.set_compact(self.width() < self.wide_needs())

    def set_language(self, language):
        self.language = language
        for row in self.rows.values():
            row.set_language(language)
        self.fit_columns()

    def set_theme(self, colors):
        for row in self.rows.values():
            row.set_theme(colors)
        self.fit_columns()


class Meter(QWidget):
    """The draft's small bar before the summary: configured, check needed and not set, in proportion."""

    def __init__(self):
        super().__init__()
        self.parts = (0, 0, 0)
        self.setFixedSize(132, 6)
        self.setAccessibleName('')

    def set_parts(self, ok, warn, off):
        self.parts = (ok, warn, off)
        self.update()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.StyleChange:
            self.update()

    def paintEvent(self, event):
        from .typography import mix
        p = getattr(self.window(), 'colors', LIGHT)
        total = sum(self.parts)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        if not total:
            painter.setBrush(QColor(p.surface_2))
            painter.drawRoundedRect(self.rect(), 3, 3)
            return
        colors = (p.success, mix(p.warning, p.surface, 0.25), mix(p.border, p.muted, 0.12))
        shown = [(n, c) for n, c in zip(self.parts, colors) if n]
        room = self.width() - 2 * (len(shown) - 1)
        x = 0.0
        for index, (n, color) in enumerate(shown):
            width = room * n / total if index < len(shown) - 1 else self.width() - x
            painter.setBrush(QColor(color))
            painter.drawRoundedRect(int(round(x)), 0, max(2, int(round(width))), self.height(), 3, 3)
            x += width + 2


class _EnabledWatch(QObject):
    def __init__(self, callback, parent):
        super().__init__(parent)
        self.callback = callback

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.EnabledChange:
            self.callback(watched.isEnabled())
        return False


class ConnectionsView(QWidget):
    """The System page's 연결 tab: the lead line, the summary line, the provider list in a card, then the pane (its
    results) and anything the page adds below (`column`). `stamp` (when the settings were read) goes in the toolbar."""

    def __init__(self, loaders=None):
        super().__init__()
        self.loaders = loaders
        self.language = 'ko'
        self.pane = None
        self.read_at = None
        self.column = QVBoxLayout(self)
        self.column.setContentsMargins(0, 0, 0, 0)
        self.column.setSpacing(12)
        lead = QHBoxLayout()
        lead.setContentsMargins(0, 0, 0, 0)
        lead.setSpacing(8)
        self.lead = Text(('Data connections', '데이터 연결'), 'lead')
        self.lead_note = Text('', 'leadNote', wrap=True)
        self.lead_note.setContentsMargins(0, 2, 0, 0)   # on the lead's baseline
        lead.addWidget(self.lead, 0, Qt.AlignmentFlag.AlignTop)
        lead.addWidget(self.lead_note, 1)
        self.column.addLayout(lead)
        summary = QHBoxLayout()
        summary.setContentsMargins(0, 0, 0, 0)
        summary.setSpacing(14)
        self.meter = Meter()
        summary.addWidget(self.meter, 0, Qt.AlignmentFlag.AlignTop)
        self.figures = KeyFigures()
        summary.addWidget(self.figures, 1)
        self.summary = summary
        self.column.addLayout(summary)
        self.card = Card(margins=(18, 6, 18, 12), spacing=0)
        self.list = ConnectionList()
        self.list.check_requested.connect(self.run_check)
        self.card.body.addWidget(self.list)
        foot = QHBoxLayout()
        foot.setContentsMargins(8, 10, 0, 0)
        foot.setSpacing(8)
        self.foot_note = sys_text(('“Configured” only means a setting exists; actual access is confirmed by an access test. '
                                   'Access tests are read-only: no account reads, orders or connection-setting changes.',
                                   '설정됨은 설정의 존재만 뜻해요. 실제 접속은 접속 검사로 따로 확인해요 · 접속 검사는 '
                                   '읽기 전용이며 계좌 조회·주문·연결 설정 변경을 하지 않아요.'), 'foot', wrap=True)
        foot.addWidget(self.foot_note, 1)
        self.foot_actions = QHBoxLayout()
        self.foot_actions.setSpacing(6)
        foot.addLayout(self.foot_actions)
        self.card.body.addWidget(line())
        self.card.body.addLayout(foot)
        self.column.addWidget(self.card)
        self.stamp = Text('', 'hint')
        self.read_settings()

    # Data -----------------------------------------------------------------------------------------------------------
    def read_settings(self):
        """Read config's presence report (local; no network, no values) and rebuild the list."""
        try:
            entries = provider_entries(self.loaders)
        except Exception:
            entries = {}
        self.read_at = now_stamp() if entries else None
        self.list.build(entries, self.read_at)
        self.refresh()

    def apply_output(self, output):
        """A result the pane showed: presence updates set / not set; an access test updates its providers."""
        test = getattr(getattr(output, 'request', None), 'tool', None)
        rows = tuple(getattr(output, 'rows', ()) or ())
        at = now_stamp()
        if test == 'presence':
            if not self.list.rows:
                self.read_settings()
            self.list.apply_presence(rows, at)
            self.read_at = at
        else:
            self.list.apply_probe(test, rows, at)
        self.refresh()

    def attach(self, pane):
        """Show `pane` (a ConnectionsPane) here: its results below the list, its exports at the card's foot; its form
        docks into the page's right column (the page does that). A row's 확인 runs the pane's own request."""
        self.pane = pane
        signal = getattr(pane, 'checked', None)
        if signal is not None:
            signal.connect(self.apply_output)
        layout = pane.layout()
        exports = [getattr(pane, name, None) for name in ('export_json', 'export_zip')]
        if layout is not None and exports[0] is not None:
            for index in range(layout.count()):
                item = layout.itemAt(index)
                if item.layout() is not None and item.layout().indexOf(exports[0]) >= 0:
                    layout.takeAt(index)
                    break
            for button in exports:
                button.setProperty('sys', 'check')
                button.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
                self.foot_actions.addWidget(button, 0, Qt.AlignmentFlag.AlignBottom)
        if layout is not None:
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(16)
        self.column.addWidget(pane)
        box = getattr(pane, 'input_box', None)
        if box is not None:
            # The window disables the form while a job runs; the rows' 확인 follow it.
            box.installEventFilter(_EnabledWatch(self.list.set_buttons_enabled, self))
            self.list.set_buttons_enabled(box.isEnabled())

    def run_check(self, test):
        """A row's 확인: choose that access test in the pane's form and submit it (the pane's own request path)."""
        pane = self.pane
        if pane is None or not hasattr(pane, 'tool') or not pane.input_box.isEnabled():
            return
        index = pane.tool.findData(test)
        if index < 0:
            return
        pane.tool.setCurrentIndex(index)
        pane.submit()

    # Display --------------------------------------------------------------------------------------------------------
    def refresh(self):
        counts = self.list.counts()
        total = len(self.list.rows)
        ko = self.language == 'ko'
        self.lead_note.set_pair((f'· {total} providers · recorded evidence and this session’s results kept apart',
                                 f'· 공급처 {total}곳 · 기록된 근거와 이번 실행 결과를 구분해요'))
        self.meter.set_parts(counts['ok'], counts['warn'], counts['off'])
        items = [(('Configured', '설정됨'), str(counts['ok']), ''),
                 (('Check needed', '확인 필요'), str(counts['warn']), 'warn' if counts['warn'] else ''),
                 (('Not set', '미설정'), str(counts['off']), '')]
        if counts['probed']:
            items += [(('Responding', '접속 응답'), f"{counts['answered']} / {counts['probed']}", ''),
                      (('Last access test', '마지막 접속 검사'), counts['last'], '')]
        else:
            items.append((('Access tests', '접속 검사'), '아직 안 함' if ko else 'none yet', ''))
        self.figures.language = self.language
        self.figures.set_items(items)
        self.stamp.set_pair((f'Settings read {self.read_at}', f'설정 읽음 {self.read_at}') if self.read_at
                            else ('Settings not read', '설정 읽지 못함'))

    def set_language(self, language):
        self.language = 'ko' if str(language).startswith('ko') else 'en'
        self.list.set_language(self.language)
        self.refresh()

    def set_theme(self, colors):
        self.list.set_theme(colors)
        self.meter.update()


class ThemeFollower(QObject):
    """Re-applies `system_sheet` to `targets` (and calls their `set_theme`) whenever the page's Workspace takes a new
    theme: `Workspace.set_theme`, which the window calls for every Workspace, restyles the Workspace itself."""

    def __init__(self, workspace, targets):
        super().__init__(workspace)
        self.workspace, self.targets, self.dark = workspace, list(targets), None
        workspace.installEventFilter(self)
        self.apply()

    def apply(self):
        ws = self.workspace
        if ws.dark == self.dark and self.dark is not None:
            return
        self.dark = ws.dark
        sheet = system_sheet(ws.colors, ws.dark)
        for target in self.targets:
            target.setStyleSheet(sheet)
            if hasattr(target, 'set_theme'):
                target.set_theme(ws.colors)

    def eventFilter(self, watched, event):
        if watched is self.workspace and event.type() == QEvent.Type.StyleChange:
            self.apply()
        return False


class ToolbarFit(QObject):
    """Hides a quiet toolbar item (when the settings were read) while the toolbar would be wider than the page, so
    the page never scrolls sideways (A3: a narrow window in English); it shows again when there is room."""

    def __init__(self, workspace, widget):
        super().__init__(workspace)
        self.workspace, self.widget, self.viewport = workspace, widget, None
        self.watch()

    def area(self):
        parent = self.workspace.parentWidget()
        while parent is not None and not isinstance(parent, QAbstractScrollArea):
            parent = parent.parentWidget()
        return parent

    def watch(self):
        area = self.area()
        if area is not None and area.viewport() is not self.viewport:
            self.viewport = area.viewport()
            self.viewport.installEventFilter(self)
        self.fit()

    def eventFilter(self, watched, event):
        if watched is self.viewport and event.type() == QEvent.Type.Resize:
            self.fit()
        return False

    def fit(self):
        try:
            self._fit()
        except RuntimeError:   # a deferred call after the window closed
            pass

    def _fit(self):
        if self.viewport is None:
            return
        page = self.workspace.parentWidget()
        margins = page.layout().contentsMargins() if page is not None and page.layout() is not None else None
        room = self.viewport.width() - (margins.left() + margins.right() if margins is not None else 0)
        bar = self.workspace.toolbar_host
        extra = self.widget.sizeHint().width() + self.workspace.toolbar.spacing()
        base = bar.minimumSizeHint().width() - (0 if self.widget.isHidden() else extra)
        show = base + extra <= room
        if show == self.widget.isHidden():
            self.widget.setVisible(show)

    def set_language(self, language):
        call_later(self, 0, self.fit)   # after the toolbar's texts took the new language


def focus_order(*parts):
    """Chain keyboard focus through `parts` in reading order (toolbar, canvas, right column). A part is a widget or a
    container whose focusable descendants keep their own order. Widgets made late (the toolbar's switch needs the
    tab pages first) otherwise sit at the end of the window's chain and Tab leaves the page from the toolbar."""
    chain = []
    for part in parts:
        if part is None:
            continue
        if part.focusPolicy() & Qt.FocusPolicy.TabFocus and not part.findChildren(QWidget):
            chain.append(part)
            continue
        inside = []
        widget, start, steps = part.nextInFocusChain(), part, 0
        while widget is not None and widget is not start and steps < 20000:
            if (part.isAncestorOf(widget) and widget.focusPolicy() & Qt.FocusPolicy.TabFocus
                    and not isinstance(widget, QAbstractScrollArea)):
                inside.append(widget)
            widget, steps = widget.nextInFocusChain(), steps + 1
        chain += [widget for widget in inside if widget not in chain]
    for first, second in zip(chain, chain[1:]):
        QWidget.setTabOrder(first, second)
    return chain


def locale_samples(window):
    """(date sample, number sample) of the window's locale, as LiveTexts for the 언어·지역 fold."""
    def ctx():
        return getattr(window, 'ctx', None)
    sample_date = LiveText(lambda language: ctx().date(date.today()))
    sample_number = LiveText(lambda language: ctx().number(76000.5))
    for widget in (sample_date, sample_number):
        widget.setProperty('sys', 'sample')
    return sample_date, sample_number
