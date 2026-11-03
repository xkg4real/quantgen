"""Native operator rules and paper runtime. No broker order path.

The session is lazy: constructing the desktop never opens a rules/order store.
Runtime callbacks cross a Qt signal before touching widgets. The existing
runtime/model/validator own evaluation and all confirmation/halting semantics.
"""
from dataclasses import replace
from datetime import datetime
from decimal import Decimal, InvalidOperation
import json

from .translations import display
from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QCheckBox, QPushButton, QMessageBox, QPlainTextEdit,
    QTableWidget)
from core.rules import (Rule, RuleStatus, Side, SizeMode, OrderKind, Comparator,
    PriceCondition, Limits, CancelCondition, validate, can_confirm)
from core.rules.store import RuleStore, to_dict
from core.engine.runtime import EngineRuntime
from core.engine.feed import QuoteFeed
from core.engine.state import EngineMode
from core.research.presentation import safe_detail
from .jobs import Jobs


def default_session():
    store = RuleStore()
    return store, EngineRuntime(store, QuoteFeed())


class PaperSession(QObject):
    changed = pyqtSignal()
    notified = pyqtSignal(str)

    def __init__(self, parent=None, factory=default_session):
        super().__init__(parent)
        self.factory, self.store, self.runtime = factory, None, None
        self.jobs = Jobs(self)
        self.jobs.succeeded.connect(lambda _: self.changed.emit())
        self.jobs.failed.connect(lambda code: self.notified.emit('FAILED · ' + code))
        self.jobs.busy_changed.connect(lambda _: self.changed.emit())

    def open(self):
        if self.runtime is None:
            self.store, self.runtime = self.factory()
            self.runtime.on_update = self.changed.emit
        self.changed.emit()

    def editable(self):
        if self.runtime is None: raise ValueError('Open the paper session first')
        if self.runtime.mode is EngineMode.ARMED or self.jobs.busy:
            raise ValueError('Disarm and finish the current tick before editing rules')
        # A disarmed runtime may still be finishing a provider call.
        if not self.runtime._tick_lock.acquire(blocking=False):
            raise ValueError('Wait for the current tick to finish')
        self.runtime._tick_lock.release()

    def save(self, rule, expected=None):
        self.editable()
        if self.store.get(rule.id) != expected: raise ValueError('Rule changed; reload it before saving')
        self.store.save(rule)
        # RuleStore preserves legacy best-effort writes. Do not report a save
        # as durable unless the existing on-disk representation matches.
        try:
            payload = json.loads(self.store.path.read_text(encoding='utf-8'))
            if to_dict(rule) not in payload.get('rules', []): raise OSError('Rule read-back mismatch')
        except Exception:
            self.store.load()
            self.changed.emit()
            raise OSError('Rule persistence verification failed') from None
        self.changed.emit()
        return rule

    def pause(self, rule):
        # A pause is available even while armed. Serialize against a live tick
        # so an old UI snapshot cannot overwrite its new trigger count.
        if self.runtime is None: raise ValueError('Open the session first')
        if not self.runtime._tick_lock.acquire(blocking=False):
            raise ValueError('A tick is finishing; use emergency stop or retry pause')
        try:
            latest=self.store.get(rule.id)
            if latest is None or latest.status is not RuleStatus.ACTIVE:
                raise ValueError('Rule is no longer active; reload')
            paused=latest.with_status(RuleStatus.PAUSED)
            self.store.save(paused)
            try:
                payload=json.loads(self.store.path.read_text(encoding='utf-8'))
                if to_dict(paused) not in payload.get('rules',[]): raise OSError('Pause read-back mismatch')
            except Exception:
                self.runtime.halt(detail='Rule pause could not be persisted')
                raise OSError('Pause persistence verification failed; engine halted') from None
            self.changed.emit()
        finally:
            self.runtime._tick_lock.release()

    def delete(self, rule):
        self.editable()
        if self.store.get(rule.id) != rule: raise ValueError('Rule changed; reload it')
        self.store.delete(rule.id)
        payload = json.loads(self.store.path.read_text(encoding='utf-8'))
        if any(r.get('id') == rule.id for r in payload.get('rules', [])):
            self.store.load(); self.changed.emit()
            raise OSError('Delete persistence verification failed')
        self.changed.emit()

    def tick(self):
        if self.runtime is not None and not self.jobs.busy:
            self.jobs.start(self.runtime.tick)

    def stop(self):
        if self.runtime is None: return True
        if self.jobs.busy: return False
        if self.runtime.mode is EngineMode.ARMED:
            self.runtime.disarm()
        self.runtime.stop()
        # A provider call cannot be cancelled safely. Keep the window alive
        # until the existing runtime loop has returned.
        thread = self.runtime._thread
        return thread is None or not thread.is_alive()


def combo(enum, value=None):
    c = QComboBox(); c.addItem('선택', None)
    for member in enum: c.addItem(member.value, member)
    c.setCurrentIndex(c.findData(value))
    return c


def decimal(text):
    if not text.strip(): return None
    try: value = Decimal(text.strip())
    except InvalidOperation: raise ValueError('Enter a decimal number') from None
    if not value.is_finite(): raise ValueError('Number must be finite')
    return value


def date_value(text):
    if not text.strip(): return None
    value = datetime.fromisoformat(text.strip())
    if value.tzinfo is None: raise ValueError('Time requires an explicit UTC offset')
    return value


class RulesPane(QWidget):
    def __init__(self, session):
        super().__init__()
        from .app import label, table
        self.session, self.base = session, Rule()
        self.loading = False
        layout = QVBoxLayout(self)
        layout.addWidget(label('Rules · 모의 실행 전용', 'heading'))
        self.status = label('규칙·가격·수량은 직접 입력합니다. 저장 → 확인 → 활성화 → 엔진 Arm을 구분합니다.', 'muted')
        layout.addWidget(self.status)
        actions = QHBoxLayout()
        for title, fn in [('규칙 읽기', self.open), ('새 규칙', self.new), ('선택 편집', self.edit_selected),
                          ('선택 활성/일시정지', self.change_status), ('선택 삭제', self.delete_selected),
                          ('선택 변경 이력', self.history)]:
            b=QPushButton(title); b.clicked.connect(lambda checked=False, f=fn:self.guard(f)); actions.addWidget(b)
        layout.addLayout(actions)
        self.rules = table(['Name', 'Symbol', 'Status', 'Revision', 'Triggers']); self.rules.setMinimumHeight(170)
        layout.addWidget(self.rules)
        self.form = QWidget(); form = QFormLayout(self.form); self.fields = {}; self.errors = {}
        specs = [('name','이름',None),('symbol','종목',None),('market','시장 코드',None),
                 ('side','방향',Side),('size_mode','수량 방식',SizeMode),('size_value','수량/금액',None),
                 ('order_kind','주문 종류',OrderKind),('limit_price','지정가',None),
                 ('valid_from','시작 · ISO 날짜+UTC offset',None),('valid_to','종료 · ISO 날짜+UTC offset',None),
                 ('max_triggers','최대 실행 횟수',None),('max_order_amount','건별 한도',None),('max_daily_amount','일별 한도',None),
                 ('after_seconds','미체결 취소 초',None),('cancel_comparator','취소 가격 조건',Comparator),('cancel_level','취소 조건 가격',None),('notes','메모',None)]
        for key,title,enum in specs:
            w=combo(enum) if enum else QLineEdit(); w.setAccessibleName(title); self.fields[key]=w
            form.addRow(title,w)
            err=label('', 'caption'); self.errors[key]=err; form.addRow('',err)
            (w.currentIndexChanged if enum else w.textChanged).connect(self.preview)
        self.all_conditions=QCheckBox('모든 조건 충족 (해제하면 OR)'); self.all_conditions.setChecked(True)
        self.all_conditions.toggled.connect(self.preview); form.addRow(self.all_conditions)
        self.conditions=QTableWidget(0,2); self.conditions.setHorizontalHeaderLabels(['Comparator','Price']); self.conditions.setMinimumHeight(160)
        form.addRow('가격 조건',self.conditions)
        condition_actions=QHBoxLayout()
        for title,fn in [('조건 추가',self.add_condition),('선택 조건 삭제',self.remove_condition)]:
            b=QPushButton(title);b.clicked.connect(fn);condition_actions.addWidget(b)
        form.addRow(condition_actions)
        self.preview_text=QPlainTextEdit();self.preview_text.setReadOnly(True);self.preview_text.setMinimumHeight(160)
        form.addRow('입력 확인',self.preview_text)
        submit=QHBoxLayout();self.save_button=QPushButton('저장');self.confirm_button=QPushButton('요약 검토 후 확인')
        self.save_button.clicked.connect(lambda:self.guard(self.save));self.confirm_button.clicked.connect(lambda:self.guard(self.confirm))
        submit.addWidget(self.save_button);submit.addWidget(self.confirm_button);form.addRow(submit)
        layout.addWidget(self.form)
        session.changed.connect(self.refresh);session.notified.connect(self.status.setText)
        self.load_rule(Rule()); self.refresh()

    def guard(self, fn):
        try: fn()
        except Exception as exc: self.status.setText('FAILED · '+safe_detail(exc))

    def open(self): self.session.open()

    def selected(self):
        if self.session.store is None: raise ValueError('Read rules first')
        row=self.rules.currentRow()
        if row<0: raise ValueError('Select a rule')
        result=self.session.store.get(self.rules.item(row,0).data(Qt.ItemDataRole.UserRole))
        if result is None: raise ValueError('Rule no longer exists')
        return result

    def refresh(self):
        from .app import table_rows
        rules=self.session.store.all() if self.session.store is not None else ()
        selected=self.rules.item(self.rules.currentRow(),0) if self.rules.currentRow()>=0 else None
        selected_id=selected.data(Qt.ItemDataRole.UserRole) if selected else None
        table_rows(self.rules,[[r.name,r.symbol,r.status.value,r.revision,r.trigger_count] for r in rules],[r.id for r in rules])
        for i,r in enumerate(rules):
            if r.id==selected_id:self.rules.selectRow(i)
        editable=self.session.runtime is not None and self.session.runtime.mode is not EngineMode.ARMED and not self.session.jobs.busy
        self.form.setEnabled(editable)

    def new(self): self.load_rule(Rule())
    def edit_selected(self): self.load_rule(self.selected())

    def load_rule(self,r):
        self.loading=True;self.base=r
        values=to_dict(r);values.update(values['limits']);values['after_seconds']=r.cancel.after_seconds
        values.update(cancel_comparator=r.cancel.if_price_beyond.comparator if r.cancel.if_price_beyond else None,
                      cancel_level=r.cancel.if_price_beyond.level if r.cancel.if_price_beyond else None)
        for key,w in self.fields.items():
            value=values.get(key)
            if isinstance(w,QComboBox):
                value=getattr(r,key,value)
                w.setCurrentIndex(w.findData(value))
            else:w.setText('' if value is None else str(value))
        self.all_conditions.setChecked(r.require_all_conditions);self.conditions.setRowCount(0)
        for c in r.conditions:self.add_condition(c)
        self.loading=False;self.preview()

    def add_condition(self,c=None):
        if self.conditions.rowCount()>=8:return
        row=self.conditions.rowCount();self.conditions.insertRow(row)
        select=combo(Comparator,c.comparator if isinstance(c,PriceCondition) else None)
        price=QLineEdit(str(c.level) if isinstance(c,PriceCondition) else '')
        self.conditions.setCellWidget(row,0,select);self.conditions.setCellWidget(row,1,price)
        select.currentIndexChanged.connect(self.preview);price.textChanged.connect(self.preview);self.preview()

    def remove_condition(self):
        if self.conditions.currentRow()>=0:self.conditions.removeRow(self.conditions.currentRow());self.preview()

    def collect(self):
        v={k:w.currentData() if isinstance(w,QComboBox) else w.text().strip() for k,w in self.fields.items()}
        conditions=[]
        for i in range(self.conditions.rowCount()):
            comp=self.conditions.cellWidget(i,0).currentData();level=decimal(self.conditions.cellWidget(i,1).text())
            if comp is None or level is None:raise ValueError('Every condition needs a comparator and price')
            conditions.append(PriceCondition(comp,level))
        cc,cl=v['cancel_comparator'],decimal(v['cancel_level'])
        if (cc is None)!=(cl is None):raise ValueError('Cancel condition needs both comparator and price')
        if cl is not None and cl<=0:raise ValueError('Cancel price must be positive')
        return replace(self.base, name=v['name'],symbol=v['symbol'],market=v['market'],side=v['side'],
            size_mode=v['size_mode'],size_value=decimal(v['size_value']),order_kind=v['order_kind'],limit_price=decimal(v['limit_price']),
            conditions=tuple(conditions),require_all_conditions=self.all_conditions.isChecked(),
            valid_from=date_value(v['valid_from']),valid_to=date_value(v['valid_to']),
            limits=Limits(int(v['max_triggers']) if v['max_triggers'] else None,decimal(v['max_order_amount']),decimal(v['max_daily_amount'])),
            cancel=CancelCondition(int(v['after_seconds']) if v['after_seconds'] else None,PriceCondition(cc,cl) if cc else None),notes=v['notes'])

    def preview(self,*_):
        if self.loading:return
        for e in self.errors.values():e.setText('')
        try:
            rule=self.collect();report=validate(rule)
            for key,e in self.errors.items():
                names={key,'limits.'+key,'cancel.'+key}
                e.setText('\n'.join(i.message for i in report.issues if i.field in names))
            self.preview_text.setPlainText(rule.summary()+'\n\n'+'\n'.join(i.severity.value+' · '+i.field+': '+i.message for i in report.issues))
            self.confirm_button.setEnabled(can_confirm(rule).ok)
        except (ValueError,InvalidOperation) as exc:
            self.preview_text.setPlainText(str(exc));self.confirm_button.setEnabled(False)

    def save(self):
        candidate=self.collect();old=self.session.store.get(candidate.id)
        if old is not None and old!=self.base:raise ValueError('Rule changed; reload before saving')
        changes={k:getattr(candidate,k) for k in ('name','symbol','market','side','size_mode','size_value','order_kind','limit_price','conditions','require_all_conditions','valid_from','valid_to','limits','cancel','notes')}
        result=old.edit(**changes) if old else candidate
        self.session.save(result,old);self.load_rule(result);self.status.setText('저장 확인 완료 · '+result.status.value)

    def confirm(self):
        self.save();rule=self.base;report=can_confirm(rule)
        if not report.ok:raise ValueError('Fix the blocking fields before confirmation')
        text=rule.summary()+'\n\n'+'\n'.join(i.message for i in report.warnings)+'\n\n'+display(self, '확인은 엔진을 활성화하지 않습니다.')
        if QMessageBox.question(self,display(self,'규칙 확인'),text,QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
        result=self.session.save(rule.confirm(),rule);self.load_rule(result);self.status.setText('CONFIRMED · 활성화는 별도입니다.')

    def change_status(self):
        rule=self.selected()
        if rule.status is RuleStatus.ACTIVE:
            self.session.pause(rule);self.status.setText('PAUSED');return
        elif rule.status in (RuleStatus.CONFIRMED,RuleStatus.PAUSED) and rule.is_confirmed and validate(rule).ok:new=RuleStatus.ACTIVE
        else:raise ValueError('Confirm a valid rule before activation')
        self.session.save(rule.with_status(new),rule);self.status.setText(new.value+' · 엔진 Arm은 별도입니다.')

    def delete_selected(self):
        rule=self.selected()
        if QMessageBox.question(self,display(self,'규칙 삭제'),display(self,rule.name+' 및 변경 이력을 삭제할까요?'),QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)==QMessageBox.StandardButton.Yes:
            self.session.delete(rule);self.new()

    def history(self):
        rule=self.selected();self.preview_text.setPlainText(json.dumps(self.session.store.history(rule.id),ensure_ascii=False,indent=2))


class PaperPane(QWidget):
    def __init__(self,session):
        super().__init__()
        from .app import label,table
        self.session=session;layout=QVBoxLayout(self)
        layout.addWidget(label('Paper Trading · 실제 주문 없음','heading'))
        self.status=label('명시적으로 세션을 열기 전에는 규칙/모의 기록을 읽지 않습니다.','muted');layout.addWidget(self.status)
        actions=QHBoxLayout();self.buttons={}
        for key,title,fn in [('open','모의 세션 읽기',session.open),('arm','Arm',self.arm),('disarm','Disarm',lambda:session.runtime.disarm()),
            ('halt','긴급 정지',lambda:session.runtime.halt()),('ack','HALT 확인',lambda:session.runtime.acknowledge()),
            ('tick','한 번 평가',session.tick),('reset','모의 기록 초기화',self.reset)]:
            b=QPushButton(title);b.clicked.connect(lambda checked=False,f=fn:self.guard(f));actions.addWidget(b);self.buttons[key]=b
        layout.addLayout(actions)
        self.dashboard=label('아직 세션을 읽지 않았습니다.');layout.addWidget(self.dashboard)
        self.venues=table(['Market','Trading state','Reason','Active rules']);self.venues.setMinimumHeight(150);layout.addWidget(self.venues)
        self.orders=table(['ID','Symbol','Side','Quantity','Kind','Trigger','Limit']);self.orders.setMinimumHeight(200);layout.addWidget(self.orders)
        settle=QHBoxLayout()
        for title,fn in [('선택 모의 체결',lambda:self.settle(True)),('선택 모의 취소',lambda:self.settle(False))]:
            b=QPushButton(title);b.clicked.connect(lambda checked=False,f=fn:self.guard(f));settle.addWidget(b)
        layout.addLayout(settle)
        self.decisions=table(['UTC','Rule','Outcome','Reason','Quoted price']);self.decisions.setMinimumHeight(240);layout.addWidget(self.decisions)
        session.changed.connect(self.refresh);session.notified.connect(self.status.setText);self.refresh()

    def guard(self,fn):
        try:
            fn();self.refresh()
        except Exception as exc:self.status.setText('FAILED · '+safe_detail(exc))

    def arm(self):
        ok,message=self.session.runtime.arm();self.status.setText(safe_detail(message))

    def refresh(self):
        from .app import table_rows
        runtime=self.session.runtime
        for key,b in self.buttons.items():b.setEnabled(key=='open' or runtime is not None)
        if runtime is None:return
        self.buttons['tick'].setEnabled(not self.session.jobs.busy)
        d=runtime.dashboard()
        counts=d['orders_today']
        self.dashboard.setText(safe_detail(
            f"{d['describe']}\nActive rules {d['active_rules']} / {d['total_rules']} · Fired today {d['fired_today']} · Rejected {d['rejected_today']}\n"
            f"Simulated orders · Open {counts['OPEN']} · Filled {counts['FILLED']} · Cancelled {counts['CANCELLED']} · Rejected {counts['REJECTED']}\n"
            f"Today's notional {d['notional_today']} · Last evaluation {d['last_tick'] or 'not run'}\n"
            f"{d['halt_detail'] or ''}\n"+
            '\n'.join(f'Quote unavailable: {symbol} · {misses} attempts · {reason}' for symbol,misses,reason in d['degraded'])+
            ('\nStale calendars: '+str(d['calendar_stale']) if d['calendar_stale'] else ''),limit=None))
        table_rows(self.venues,[[v['code'], 'OPEN' if v['open'] else 'CLOSED' if v['open'] is False else 'UNKNOWN',safe_detail(v['why'] or v['describe']),v['rules']] for v in d['venues']])
        self.buttons['ack'].setEnabled(d['needs_ack']);self.buttons['arm'].setEnabled(not d['needs_ack'] and runtime.mode is not EngineMode.ARMED)
        selected=self.orders.item(self.orders.currentRow(),0) if self.orders.currentRow()>=0 else None
        ident=selected.text() if selected else None
        orders=d['open_orders'];table_rows(self.orders,[[o.id,o.symbol,o.side.value,o.quantity,o.kind.value,o.trigger_price,o.limit_price] for o in orders])
        for i,o in enumerate(orders):
            if o.id==ident:self.orders.selectRow(i)
        table_rows(self.decisions,[[d.at.isoformat(),d.rule_name,d.outcome.value,safe_detail(d.reason),d.quote_price] for d in runtime.decisions(200)])

    def settle(self,fill):
        if self.session.runtime is None or self.orders.currentRow()<0:raise ValueError('Select an open simulated order')
        runtime=self.session.runtime;ident=self.orders.item(self.orders.currentRow(),0).text();order=runtime.book.get(ident)
        if order is None or not order.open:raise ValueError('Order is no longer open')
        if fill:
            price=order.limit_price if order.limit_price is not None else order.trigger_price
            ok,message=runtime.book.fill(ident,price)
        else:ok,message=runtime.book.cancel(ident)
        runtime._persist();self.status.setText(safe_detail(message or ('모의 기록 완료' if ok else '거절')))

    def reset(self):
        self.session.editable()
        if QMessageBox.question(self,display(self,'모의 기록 초기화'),display(self,'모의 주문·판정·교차 이력을 초기화할까요? 규칙은 유지됩니다.'),QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)==QMessageBox.StandardButton.Yes:
            self.session.runtime.reset_practice()
