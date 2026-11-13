"""Do not keep the market blank while other quotes or market caps are pending."""
import threading
from dataclasses import replace
from unittest.mock import Mock
from tests.desktop_home_markets_markets_acceptance import Base,FakeService,member,kr_batch,Clock
from tests.qt_fixture_cleanup import delete_owned_widget
from quantgen_desktop.market_rankings import RankingBoard,ProductionRankingLoader,kis_batch,daily_batch
from core.market import rankings as R
from core.i18n import LocaleContext
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt


class MarketFirstPaintTests(Base):
    def test_us_prices_are_published_before_optional_details_without_extra_requests(self):
        service=FakeService();seen=[]
        def partial(batch):seen.append((batch,tuple(c[1] for c in service.calls)))
        result=kis_batch(service,'us',(member('AAPL'),member('JPM')),details={},partial=partial,sleep=lambda _:None)
        self.assertEqual([r.member.code for r in seen[0][0].records],['AAPL'])
        self.assertEqual(seen[0][1],('HHDFS00000300',))
        self.assertEqual(seen[1][1],('HHDFS00000300','HHDFS00000300'))
        self.assertEqual([c[1] for c in service.calls],['HHDFS00000300']*2+['HHDFS76200200']*2)
        self.assertTrue(all(r.market_cap for r in result.records))
        again=kis_batch(FakeService(),'us',(member('AAPL'),member('JPM')),details={},sleep=lambda _:None)
        self.assertEqual([(r.member.code,r.price,r.market_cap) for r in result.records],
                         [(r.member.code,r.price,r.market_cap) for r in again.records])

    def test_first_rows_are_clickable_before_last_response_and_never_a_final_rank(self):
        release=threading.Event();batch=kr_batch();opened=[]
        def loader(group,members,cancelled=None,progress=None,partial=None):
            partial(replace(batch,records=batch.records[:1]));progress(1,len(members))
            release.wait(20)
            return batch
        loader.supports_partial=True
        board=RankingBoard(loader=loader,auto_load=False,locale=LocaleContext('ko_KR'),clock=Clock())
        self.addCleanup(delete_owned_widget,board);self.addCleanup(release.set)
        board.open_requested.connect(opened.append);board.show();board.refresh(manual=True)
        try:
            self.wait(lambda:len(board.ranked)==1)
            self.assertTrue(board.jobs.busy);self.assertEqual(board.batches,{})
            self.assertEqual(board.ranked[0].rank,0)
            self.assertIn('불러오는 중',board.badge.text())
            self.assertIn('전체 조회',board.footnote.text())
            QTest.mouseClick(board.rows[0],Qt.MouseButton.LeftButton)
            self.assertEqual(len(opened),1)
        finally:release.set()
        self.wait(lambda:not board.jobs.busy)
        self.assertIsNone(board._preview);self.assertEqual(board.batches['kr'],batch)
        self.assertTrue(any(row.rank for row in board.ranked))
        # Subsequent refresh does not replace a complete ranking with a partial list.
        board._epoch+=1;board._loading=('kr',1,81)
        board._on_partial(board._epoch,replace(batch,records=batch.records[:1]))
        self.assertIsNone(board._preview)

    def test_market_switch_cancels_old_round_and_ignores_its_late_preview(self):
        release=threading.Event();cancelled_seen=threading.Event();batch=kr_batch()
        def loader(group,members,cancelled=None,progress=None,partial=None):
            partial(batch)
            release.wait(20)
            if cancelled():cancelled_seen.set()
            return batch
        loader.supports_partial=True
        board=RankingBoard(loader=loader,auto_load=False,clock=Clock());board.show()
        self.addCleanup(delete_owned_widget,board);self.addCleanup(release.set)
        board.refresh(manual=True);self.wait(lambda:board._preview is not None)
        epoch=board._epoch
        board.set_page('us');self.assertTrue(board._cancel.is_set())
        board._on_partial(epoch,batch);self.assertIsNone(board._preview)
        release.set();self.wait(lambda:not board.jobs.busy)
        self.assertTrue(cancelled_seen.is_set());self.assertEqual(board.batches,{})
        self.assertEqual(board.ranked,[])
