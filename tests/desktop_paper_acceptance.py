"""Native rule authoring and paper controls with temporary stores only."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch, Mock
import dotenv
with patch.object(dotenv,'load_dotenv',return_value=False):
    from quantgen_desktop.app import ResearchWindow
    from quantgen_desktop.paper import decimal, date_value
    from core.rules import Rule, Side, SizeMode, OrderKind, Comparator, PriceCondition, RuleStatus
    from core.rules.store import RuleStore
    from core.engine.runtime import EngineRuntime
    from core.engine.feed import QuoteFeed
    from core.engine.state import EngineMode
    from core.engine.orders import SimulatedOrder, OrderStatus
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtTest import QTest


def fixture_rule():
    return Rule(name='Synthetic fixture',symbol='FIXTURE',market='US',side=Side.BUY,
        size_mode=SizeMode.QUANTITY,size_value=Decimal(2),order_kind=OrderKind.MARKET,
        conditions=(PriceCondition(Comparator.AT_OR_BELOW,Decimal(10)),))


class NativePaperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.factory=Mock(side_effect=self.make_session)
        self.window=ResearchWindow(auto_refresh=False,paper_factory=self.factory)
        self.addCleanup(self.cleanup)

    def make_session(self):
        store=RuleStore(self.root/'rules.json')
        feed=QuoteFeed(Mock(),fmp_client=Mock())
        runtime=EngineRuntime(store,feed,state_path=self.root/'engine.json')
        runtime._ensure_thread=Mock() # no provider-loop thread in this fixture
        return store,runtime

    def cleanup(self):
        for _ in range(200):
            self.app.processEvents()
            if not self.window.paper_session.jobs.busy:break
            QTest.qWait(10)
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Yes):self.window.close()
        self.window.deleteLater();self.app.processEvents()

    def open(self):self.window.paper_session.open();return self.window.paper_session

    def test_launch_is_lazy_and_financial_fields_are_blank(self):
        self.factory.assert_not_called();self.assertEqual(list(self.root.iterdir()),[])
        pane=self.window.rules
        for k in ('side','size_mode','order_kind'):self.assertIsNone(pane.fields[k].currentData())
        for k in ('symbol','market','size_value','limit_price','max_triggers'):self.assertEqual(pane.fields[k].text(),'')
        self.assertFalse(self.window.paper_halt.isEnabled())
        self.window.navigate('system');self.factory.assert_not_called()

    def test_confirm_activation_edit_reconfirmation_and_restart(self):
        s=self.open();p=self.window.rules;p.load_rule(fixture_rule());p.save()
        self.assertEqual(p.base.status,RuleStatus.DRAFT)
        p.rules.selectRow(0)
        with self.assertRaises(ValueError):p.change_status()
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Yes):p.confirm()
        self.assertEqual(p.base.status,RuleStatus.CONFIRMED);self.assertEqual(s.runtime.mode,EngineMode.DISARMED)
        p.rules.selectRow(0);p.change_status();self.assertEqual(s.store.all()[0].status,RuleStatus.ACTIVE)
        p.edit_selected();p.fields['size_value'].setText('3');p.save()
        self.assertEqual(p.base.status,RuleStatus.DRAFT);self.assertIsNone(p.base.confirmed_at)
        self.assertTrue(s.store.history(p.base.id))
        self.assertEqual(RuleStore(s.store.path).get(p.base.id),p.base)

    def test_invalid_and_stale_edits_do_not_confirm(self):
        s=self.open();p=self.window.rules;p.load_rule(fixture_rule());p.save()
        for value in ('NaN','Infinity','-Infinity'):
            p.fields['size_value'].setText(value);self.assertFalse(p.confirm_button.isEnabled())
            with self.assertRaises(ValueError):p.save()
        p.load_rule(s.store.all()[0]);old=p.base;s.store.save(old.edit(notes='concurrent'))
        with self.assertRaises(ValueError):p.save()
        with self.assertRaises(ValueError):date_value('2026-10-30T12:00:00')

    def test_failed_persistence_rolls_back_and_reports_failure(self):
        s=self.open();p=self.window.rules;p.load_rule(fixture_rule());p.save();old=p.base
        p.fields['size_value'].setText('4')
        with patch.object(s.store,'_flush',return_value=None):
            with self.assertRaises(OSError):p.save()
        self.assertEqual(s.store.get(old.id),old)

    def test_rule_pause_while_armed_preserves_latest_trigger_count(self):
        s=self.open();r=fixture_rule().confirm().activate();s.save(r)
        s.runtime.arm();p=self.window.rules;p.rules.selectRow(0)
        newer=replace(r,trigger_count=2);s.store.save(newer)
        s.pause(r)
        self.assertEqual(s.store.get(r.id).trigger_count,2)
        self.assertEqual(s.store.get(r.id).status,RuleStatus.PAUSED)
        self.assertEqual(s.runtime.mode,EngineMode.ARMED)

    def test_failed_pause_persistence_halts_engine(self):
        s=self.open();r=fixture_rule().confirm().activate();s.save(r);s.runtime.arm()
        with patch.object(s.store,'_flush',return_value=None):
            with self.assertRaises(OSError):s.pause(r)
        self.assertEqual(s.runtime.mode,EngineMode.HALTED)

    def test_halt_is_global_and_ack_never_rearms(self):
        s=self.open();s.runtime.arm();self.assertEqual(s.runtime.mode,EngineMode.ARMED)
        self.assertFalse(self.window.rules.form.isEnabled())
        self.window.navigate('markets');self.window.paper_halt.click()
        self.assertEqual(s.runtime.mode,EngineMode.HALTED)
        self.assertFalse(s.runtime.arm()[0]);self.window.paper.buttons['ack'].click()
        self.assertEqual(s.runtime.mode,EngineMode.DISARMED)
        self.assertFalse(s.runtime.state.requires_manual_rearm)
        self.factory.assert_called_once()

    def test_fill_cancel_and_callback_from_worker_stay_native(self):
        s=self.open();r=fixture_rule()
        for i in range(2):s.runtime.book.place(SimulatedOrder(str(i),r.id,1,r.name,r.symbol,r.market,Side.BUY,OrderKind.MARKET,Decimal(2),None,Decimal(20),Decimal(10)))
        t=threading.Thread(target=s.runtime._notify);t.start();t.join();self.app.processEvents()
        p=self.window.paper;p.orders.selectRow(0);first=p.orders.item(0,0).text();p.settle(True);p.refresh()
        self.assertEqual(s.runtime.book.get(first).status,OrderStatus.FILLED)
        p.orders.selectRow(0);second=p.orders.item(0,0).text();p.settle(False)
        self.assertEqual(s.runtime.book.get(second).status,OrderStatus.CANCELLED)
        restored=EngineRuntime(s.store,s.runtime.feed,state_path=self.root/'engine.json')
        self.assertEqual(len(restored.book.all()),2);self.assertEqual(restored.mode,EngineMode.DISARMED)

    def test_close_waits_for_inflight_paper_job(self):
        s=self.open();gate=threading.Event()
        s.jobs.start(lambda:gate.wait(2))
        self.window.show();self.assertFalse(self.window.close());gate.set()
        for _ in range(200):
            self.app.processEvents()
            if not s.jobs.busy:break
            QTest.qWait(10)
        self.assertTrue(self.window.close())


if __name__=='__main__':unittest.main()
