"""Native views over the existing validated Macro v2 readers and actions.

The legacy modules supply their established data readers; their Flet renderers
are not invoked. This pane constructs Qt widgets only. No store is read at init.
"""
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QTreeWidget, QTreeWidgetItem, QLineEdit
from core.research.presentation import safe_detail
from .tools import ToolPane, fmt


def display_fields(value):
    """Keep the original P19 display boundary at every nesting level."""
    if isinstance(value, dict):
        return {k: display_fields(v) for k, v in value.items() if 'regime' not in str(k).lower()}
    if isinstance(value, (tuple, list)):
        return [display_fields(v) for v in value]
    return value


@dataclass(frozen=True)
class MacroRecordRequest:
    tool: str = 'overlay'
    market: str = 'KR'
    source: str = 'dry_run'
    action: str = 'refresh'
    kind: str = ''
    ident: str = ''

    def validate(self):
        if self.tool not in {'overlay', 'cards', 'research'} or self.market not in {'KR', 'US'}:
            raise ValueError('Invalid macro view')
        if self.source not in {'dry_run', 'live'} or self.action not in {'refresh', 'run_dry', 'run_live', 'ack'}:
            raise ValueError('Invalid macro operation')
        if self.tool != 'overlay' and self.action != 'refresh':
            raise ValueError('Records are read only')
        if self.action == 'ack' and (self.kind not in {'alert', 'live_alert', 'halt'} or not self.ident):
            raise ValueError('Select an existing alert or halted book')


@dataclass(frozen=True)
class MacroRecordOutput:
    request: MacroRecordRequest
    data: dict


def execute_macro_records(request, *, backend=None):
    request.validate()
    if backend is not None:
        return MacroRecordOutput(request, backend(request))
    # Existing loaders enforce manifests, hash chains, effective owner rulings
    # and package checks. Never substitute an unvalidated filesystem dump.
    if request.tool == 'cards':
        from ui.macro_cards_view import load_inputs
        return MacroRecordOutput(request, load_inputs())
    if request.tool == 'research':
        from ui.research_view import load_inputs
        return MacroRecordOutput(request, load_inputs())
    import config
    from ui.macro_state_panel import load_view, live_missing, verdict_of
    from core.skills import macro_daily as MD
    from core.skills.alerts import AlertStore
    from core.engine import books as BK
    base = config.macro_dir()
    selected = base / 'dry_run' if request.source == 'dry_run' else base
    now = datetime.now(timezone.utc)
    if request.action == 'run_dry':
        MD.dry_run(base, clock=lambda: now)
        request = replace(request, source='dry_run')
        selected = base / 'dry_run'
    elif request.action == 'run_live':
        if live_missing():
            raise ValueError('Live prerequisites unavailable')
        MD.run_decision(MD.default_services(base, lambda: now), request.market, now.date(), run_mode='live')
        request = replace(request, source='live')
        selected = base
    elif request.action == 'ack':
        view = load_view(selected, request.market)
        store = AlertStore(base if request.kind == 'live_alert' else selected)
        if request.kind == 'halt':
            if verdict_of('macro_state', view.get('state'))[0] == 'refused':
                raise ValueError('Cannot acknowledge a book from a refused artifact')
            runtime = (view.get('state') or {}).get('runtime') or []
            if not any(x.get('book_id') == request.ident and x.get('engine_state') == 'HALTED' for x in runtime):
                raise ValueError('Selected book is no longer halted')
            BK.acknowledge(BK.BookRegistry(selected), request.ident, 'operator', now)
            for alert in store.open():
                if str(alert.get('code', '')).startswith('HALT_') and request.ident in (alert.get('books') or []):
                    store.acknowledge(alert['alert_id'], 'operator', now)
        else:
            if not any(x.get('alert_id') == request.ident for x in store.open()):
                raise ValueError('Selected alert is no longer open')
            store.acknowledge(request.ident, 'operator', now)
    return MacroRecordOutput(request, load_view(selected, request.market))


class MacroRecordsPane(ToolPane):
    def __init__(self):
        super().__init__('Macro v2', [('overlay', 'Overlay state'), ('cards', 'Model cards'), ('research', 'Research register')],
            [('dry_run', 'Dry-run artifacts'), ('live', 'Live artifacts')],
            {'overlay': [('market', 'Market', [('KR', 'Korea'), ('US', 'United States')])], 'cards': [], 'research': []})
        self.run.setText('기록 새로 읽기')
        actions = QHBoxLayout()
        self.dry_button, self.live_button = QPushButton('Macro dry run'), QPushButton('Macro live decision')
        for button, action in ((self.dry_button, 'run_dry'), (self.live_button, 'run_live')):
            button.clicked.connect(lambda checked=False, a=action: self.request_action(a))
            actions.addWidget(button)
        self.input_box.layout().addLayout(actions)
        self.tool.currentIndexChanged.connect(self.action_visibility)
        self.status.setText('기록은 명시적으로 읽습니다. Live 실행은 기존 서명 달력·연결 조건을 충족해야 합니다.')

    def action_visibility(self):
        enabled = self.tool.currentData() == 'overlay'
        self.dry_button.setEnabled(enabled)
        self.live_button.setEnabled(enabled)

    def make_request(self):
        return MacroRecordRequest(self.tool.currentData(), self.values().get('market', 'KR'), self.source.currentData())

    def request_action(self, action, kind='', ident=''):
        self.requested.emit(replace(self.make_request(), action=action, kind=kind, ident=ident))

    def details(self, title, data):
        """Expandable, searchable native record tree; never stringify whole stores."""
        from .app import label
        tree = QTreeWidget()
        tree.setHeaderLabels(['Field', 'Recorded value'])
        tree.setMinimumHeight(220)
        tree.setColumnWidth(0, 300)
        def add(parent, key, value):
            item = QTreeWidgetItem([str(key), '' if isinstance(value, (dict, list, tuple)) else safe_detail(value, limit=None)])
            parent.addChild(item)
            if isinstance(value, dict):
                for k, v in value.items(): add(item, k, v)
            elif isinstance(value, (list, tuple)):
                for i, v in enumerate(value): add(item, i, v)
        if isinstance(data, dict):
            for k, v in data.items(): add(tree.invisibleRootItem(), k, v)
        else: add(tree.invisibleRootItem(), title, data)
        search = QLineEdit(); search.setPlaceholderText('이 기록에서 필드·값 검색')
        search.setAccessibleName(title + ' search')
        def filter_tree(text):
            text = text.casefold()
            def visit(item):
                own = text in (item.text(0)+' '+item.text(1)).casefold()
                children = [visit(item.child(i)) for i in range(item.childCount())]
                visible = own or any(children)
                item.setHidden(not visible)
                if text and any(children): item.setExpanded(True)
                if own:
                    def show_children(node):
                        for i in range(node.childCount()):
                            node.child(i).setHidden(False); show_children(node.child(i))
                    show_children(item)
                return visible
            for i in range(tree.topLevelItemCount()): visit(tree.topLevelItem(i))
        search.textChanged.connect(filter_tree)
        self.result_layout.addWidget(label(title, 'heading'))
        self.result_layout.addWidget(search); self.result_layout.addWidget(tree)
        self.tables[title] = tree
        self.sections.append({'type': 'records', 'name': title, 'data': data})

    def show_result(self, out):
        self.clear_result()
        d = out.data
        if out.request.tool == 'cards': self.show_cards(d)
        elif out.request.tool == 'research': self.show_research(d)
        else:
            self.source.setCurrentIndex(self.source.findData(out.request.source))
            self.show_overlay(d)

    def show_cards(self, d):
        from ui.macro_cards_view import GROUPS, VERDICTS, _group, _reason
        if not all(isinstance(d.get(k), t) for k, t in (('cards', list), ('verdicts', list), ('gate_status', dict), ('headers', list))):
            raise ValueError('Invalid validated card snapshot')
        gate = d['gate_status']
        self.text(f"Gate package: {gate.get('status', 'UNKNOWN')}\n" + '\n'.join(map(str, gate.get('reasons') or [])))
        self.text('BUILD_AS_INSURANCE / FORWARD_SIM / REFUSAL_BOOK는 용도 표기이며 PASS 판정이 아닙니다. 조회는 검증이나 승인을 수행하지 않습니다.')
        last = {r.get('card_id'): r for r in d['verdicts'] if isinstance(r, dict)}
        for key, title, caption in GROUPS:
            group = [c for c in d['cards'] if isinstance(c, dict) and _group(c) == key]
            if not group: continue
            self.text(caption)
            rows = []
            for c in group:
                row = last.get(c.get('card_id'))
                verdict = str((row or c).get('verdict') or 'NOT_RUN')
                disposition = str((row or c).get('disposition') or 'DESCRIPTIVE')
                code, reason = _reason(c, row, verdict, gate)
                if verdict not in VERDICTS: verdict, code, reason = 'INVALID', 'invalid_verdict', 'Not a schema verdict; fail closed'
                rows.append([c.get('card_id'), verdict, disposition, code, c.get('label'), c.get('instrument_book')])
                self.details(str(c.get('card_id')), {'verdict': verdict, 'disposition': disposition, 'reason': reason,
                    'record': {k: v for k, v in c.items() if k not in {'verdict', 'disposition'}},
                    'headers': [h for h in d['headers'] if h.get('card_id') == c.get('card_id')]})
            self.result_table(title, ['Card', 'Verdict', 'Disposition', 'Reason', 'Label', 'Book'], rows)
        self.details('Tech-fund drafts · NOT_RUN / not a recommendation', d.get('techfund', []))
        self.details('CRY-1 controls · vendor trials, not formal card results', d.get('cry1', []))
        self.finished('검증된 원문 기록을 표시했습니다. 조회가 공식 판정이나 권장 book을 바꾸지 않습니다.')

    def show_research(self, d):
        from ui.research_view import DISCLAIMERS, WEIGHT_CAPTION, PAGES
        if (not all(isinstance(d.get(k), dict) for k in ('tf', 'backlog', 'council'))
                or not d['tf'].get('weights') or not d['tf'].get('register')):
            raise ValueError('Invalid research record')
        self.text('\n'.join(DISCLAIMERS)); self.text(WEIGHT_CAPTION)
        tf = d['tf']
        for key, title in (('weights', 'Design priors · not gate PASS'), ('other_markets', 'Other markets'),
                           ('register', 'Go / No-go register'), ('dnb', 'Do not build'),
                           ('xs', 'Cross-spec proposals · owner confirmation'), ('open_questions', 'Open questions')):
            self.details(title, tf.get(key, []))
        self.details('Backlog and council queue', d['backlog'])
        self.details('Council resolutions and modules', {k: v for k, v in d['council'].items() if k != 'pages'})
        # Only shipped council documents; never open a URL/path supplied by a record.
        for title, path in PAGES.items():
            button = QPushButton(title)
            button.setEnabled(Path(path).is_file())
            button.setToolTip('Opens the shipped offline document' if button.isEnabled() else 'Document unavailable in this installation')
            button.clicked.connect(lambda checked=False, p=path: QDesktopServices.openUrl(QUrl.fromLocalFile(str(p))))
            self.result_layout.addWidget(button)
        self.finished('Research register · 표시 전용. 설계 가중치를 노출·규칙·book 입력으로 보내지 않습니다.')

    def show_overlay(self, d):
        from ui.macro_state_panel import verdict_of, _book_ids, composition_lines
        state = d.get('state')
        if state is None:
            self.text('NOT_LOADED · macro_state가 없습니다. 값을 추정하지 않습니다.')
            self.status.setText('NOT_LOADED · 실행 기록 없음')
            self.show_overlay_support(d)
            return
        verdict, issues = verdict_of('macro_state', state)
        if verdict == 'refused':
            self.text('REFUSED · 검증에 실패한 macro_state의 수치는 표시하지 않습니다.\n' + '\n'.join(issues))
            self.status.setText('REFUSED · fail closed')
            self.show_overlay_support(d)
            return
        self.text(f"{state.get('market')} · {state.get('effective_session')} · {state.get('decision_utc')} · {state.get('run_mode')}\n" + '\n'.join(issues))
        usable = []
        for overlay in d.get('overlays', []):
            v, errors = verdict_of('overlay_decision', overlay)
            if v == 'refused': self.text('Overlay refused · ' + '\n'.join(errors))
            else: usable.append(overlay)
        mg = next((o for o in usable if o.get('family') == 'market_gross'), None)
        ids, runtime, books = _book_ids(state)
        for ident in ids:
            entry, book = runtime.get(ident, {}), books.get(ident, {})
            self.result_table(ident, ['Field', 'Recorded value'], [('engine', entry.get('engine_state')),
                ('composed', fmt(book.get('composed'))), ('gross', fmt(book.get('gross'))), ('binding', book.get('binding_factor'))])
            self.text('\n'.join(composition_lines(state, ident, entry, book, mg)))
            if entry.get('engine_state') == 'HALTED':
                self.details(ident + ' · HALT', entry.get('halt', {}))
                if not (entry.get('halt') or {}).get('ack_utc'):
                    button = QPushButton('HALT 확인 · ' + ident)
                    button.clicked.connect(lambda checked=False, i=ident: self.request_action('ack', 'halt', i))
                    self.result_layout.addWidget(button)
        # Preserve the original P19 rule: volatility labels, no regime state.
        self.details('Volatility labels · display only', display_fields(state.get('vol') or {}))
        self.details('Flags', display_fields(state.get('flags') or {}))
        self.details('Overlay records · values as recorded', display_fields([
            {k: v for k, v in o.items() if k not in {'forward_sim', 'refusal'}} for o in usable]))
        self.details('Display-only books · not a recommendation', {
            'forward_sim': state.get('forward_sim', {}), 'refusal_books': state.get('refusal_books', {}),
            'overlay_forward_sim': [x for o in usable for x in o.get('forward_sim', [])],
            'overlay_refusal': [x for o in usable for x in o.get('refusal', [])]})
        self.details('Inputs and fail-closed inputs', {'inputs': state.get('inputs', []),
            'fail_closed_inputs': (state.get('extras') or {}).get('fail_closed_inputs', [])})
        self.show_overlay_support(d, state)
        self.details('Provenance', {k: state.get(k) for k in ('schema', 'schema_version', 'git_hash',
            'tree_hash', 'knowledge_utc', 'data_snapshot_id', 'config_hash', 'generated_at_utc')})
        self.finished('기록된 구성 값을 표시했습니다. 화면에서 노출을 재계산하지 않습니다. FORWARD-SIM·refusal은 권장이 아닙니다.')

    def show_overlay_support(self, d, state=None):
        """Keep diagnostics visible even when the calculation artifact is refused."""
        from ui.macro_state_panel import verdict_of
        self.details('Owner decisions / inputs / proposals', {'recorded': (state or {}).get('owner_decisions', {}),
                     'items': d.get('owner_items', {})})
        for kind in ('context_log', 'event_calendar'):
            record = d.get(kind)
            if record is None: self.text(kind + ' · NOT_LOADED'); continue
            v, errors = verdict_of(kind, record)
            if v == 'refused': self.text(kind + ' · REFUSED · ' + '\n'.join(errors))
            else: self.details(kind, display_fields(record))
        for alert in d.get('alerts', []):
            ident = alert.get('alert_id')
            self.text(f"{alert.get('severity')} · {alert.get('code')} · {alert.get('message', alert.get('detail', ''))}")
            if ident and not alert.get('ack_utc'):
                kind = 'live_alert' if alert.get('store') == 'live' else 'alert'
                button = QPushButton('알림 확인 · ' + str(ident))
                button.clicked.connect(lambda checked=False, i=ident, k=kind: self.request_action('ack', k, i))
                self.result_layout.addWidget(button)
