"""Execution-count/time aggregation oracles using only offline feed fixtures."""
from dataclasses import replace
from datetime import datetime, timedelta
import unittest

from core.market.live import apply_tick, bucket
from core.market.models import Candle, ChartRequest, Instrument, LIVE_INTERVALS, MarketQuote, MarketSnapshot, MarketTick


class ReceivedBarsTests(unittest.TestCase):
    instrument = Instrument()
    origin = datetime.fromisoformat('2026-11-02T09:00:00+09:00')

    def snapshot(self, interval='1tick', *, limit=120):
        return MarketSnapshot(ChartRequest(self.instrument, interval, limit), (),
                              MarketQuote(self.instrument, price=200, volume=900000,
                                          market_time=self.origin.isoformat()))

    def tick(self, *, seconds=0, price=100, volume=2, cumulative=1002, **kwargs):
        return MarketTick(self.instrument, (self.origin + timedelta(seconds=seconds)).isoformat(),
                          price, volume, cumulative, **kwargs)

    def test_first_received_trade_ignores_quote_and_session_total_for_bar_volume(self):
        for interval in LIVE_INTERVALS:
            before = self.snapshot(interval)
            after = apply_tick(before, self.tick())
            self.assertEqual(after.candles, (Candle(self.origin.isoformat(), 100, 100, 100, 100, 2,
                                                  sequence=1, trade_count=1),))
            self.assertEqual(after.quote.volume, 1002)
            self.assertEqual(before.candles, ())

    def test_same_second_same_price_size_distinct_executions_and_replay(self):
        out = self.snapshot()
        for cumulative in (1002, 1004, 1006):
            out = apply_tick(out, self.tick(cumulative=cumulative))
        self.assertEqual([c.sequence for c in out.candles], [1, 2, 3])
        self.assertEqual(len({c.timestamp for c in out.candles}), 1)
        self.assertIs(apply_tick(out, self.tick(cumulative=1006)), out)
        self.assertIs(apply_tick(out, self.tick(cumulative=1004)), out)

    def test_ten_trade_bar_independent_ohlcv_oracle(self):
        prices = [100, 102, 101, 99, 103, 105, 100, 98, 104, 101, 106]
        out = self.snapshot('10tick')
        for index, price in enumerate(prices):
            out = apply_tick(out, self.tick(price=price, cumulative=1002 + 2 * index))
        self.assertEqual(out.candles, (
            Candle(self.origin.isoformat(), 100, 105, 98, 101, 20, sequence=1, trade_count=10),
            Candle(self.origin.isoformat(), 106, 106, 106, 106, 2, sequence=2, trade_count=1)))

    def test_hundred_trade_boundary_uses_received_count(self):
        out = self.snapshot('100tick')
        for index in range(101):
            out = apply_tick(out, self.tick(cumulative=1002 + 2 * index))
        self.assertEqual([c.trade_count for c in out.candles], [100, 1])
        self.assertEqual([c.volume for c in out.candles], [200, 2])

    def test_second_buckets_clock_aligned_without_filling_quiet_periods(self):
        for seconds in (1, 5, 10, 30):
            out = self.snapshot(f'{seconds}s')
            out = apply_tick(out, self.tick(seconds=seconds * 2))
            out = apply_tick(out, self.tick(seconds=seconds * 2, price=103, cumulative=1004))
            out = apply_tick(out, self.tick(seconds=seconds * 6, price=99, cumulative=1006))
            self.assertEqual(len(out.candles), 2)
            self.assertEqual((out.candles[0].open, out.candles[0].high, out.candles[0].close,
                              out.candles[0].volume, out.candles[0].trade_count), (100, 103, 103, 4, 2))
            self.assertNotIn('Live gap', out.note)
        self.assertEqual(bucket('2026-11-02T09:17:37+09:00', '30s'), '2026-11-02T09:17:30+09:00')

    def test_gap_restarts_partial_tick_group_without_reconstructing_trades(self):
        out = apply_tick(self.snapshot('10tick'), self.tick())
        out = apply_tick(out, self.tick(seconds=1, price=104, cumulative=1010))
        self.assertEqual([c.trade_count for c in out.candles], [1, 1])
        self.assertEqual([c.volume for c in out.candles], [None, 2])
        self.assertIn('Live gap', out.note)
        out = apply_tick(out, self.tick(seconds=2, cumulative=1012))
        self.assertEqual(out.candles[-1].trade_count, 2)
        self.assertEqual(out.candles[-1].volume, 4)

    def test_gap_after_closed_tick_bar_retains_known_volume(self):
        out = apply_tick(self.snapshot(), self.tick())
        out = apply_tick(out, self.tick(seconds=1, cumulative=1100))
        self.assertEqual([c.volume for c in out.candles], [2, 2])

    def test_second_gap_marks_unknown_volume_without_distributing_missing_trades(self):
        for seconds in (1, 20):
            out = apply_tick(self.snapshot('10s'), self.tick())
            out = apply_tick(out, self.tick(seconds=seconds, cumulative=1200))
            self.assertIsNone(out.candles[-1].volume)
            self.assertIn('Live gap', out.note)
            self.assertEqual(len(out.candles), 1 if seconds == 1 else 2)

    def test_session_reset_starts_new_group_and_accepts_reset_cumulative_volume(self):
        out = apply_tick(self.snapshot('10tick'), self.tick())
        out = apply_tick(out, self.tick(seconds=86400, cumulative=2))
        self.assertEqual([c.trade_count for c in out.candles], [1, 1])
        self.assertEqual([c.sequence for c in out.candles], [1, 2])
        self.assertEqual(out.quote.volume, 2)

    def test_exchange_local_day_controls_reset(self):
        ins = Instrument('overseas_stock', 'AAPL', 'NAS')
        out = MarketSnapshot(ChartRequest(ins, '10tick'), ())
        first = MarketTick(ins, '2026-11-03T00:59:59+00:00', 100, 2, 1002)
        out = apply_tick(out, first)
        out = apply_tick(out, replace(first, timestamp='2026-11-03T14:30:00+00:00', cumulative_volume=2))
        self.assertEqual(len(out.candles), 2)
        self.assertEqual(out.candles[-1].timestamp, '2026-11-03T09:30:00-05:00')
        self.assertEqual(out.quote.currency, 'USD')

    def test_invalid_or_unidentifiable_executions_cannot_mutate_snapshot(self):
        out = apply_tick(self.snapshot(), self.tick(seconds=2))
        trade = self.tick(seconds=3, cumulative=1004)
        invalid = (replace(trade, instrument=Instrument(code='000660')),
                   replace(trade, timestamp='2026-11-02T09:00:01+09:00'),
                   replace(trade, timestamp='2026-11-02T09:00:03'),
                   replace(trade, price=float('nan')), replace(trade, price=0),
                   replace(trade, volume=-1), replace(trade, volume=0),
                   replace(trade, volume=float('inf')), replace(trade, volume=None),
                   replace(trade, cumulative_volume=None), replace(trade, cumulative_volume=1),
                   replace(trade, cumulative_volume=float('nan')), replace(trade, cumulative_volume=1003),
                   replace(trade, source='KIS REST'))
        for item in invalid:
            self.assertIs(apply_tick(out, item), out)

    def test_adjusted_or_accidentally_supplied_rest_history_is_rejected(self):
        out = self.snapshot()
        adjusted = replace(out, request=replace(out.request, adjusted=True))
        self.assertIs(apply_tick(adjusted, self.tick()), adjusted)
        history = replace(out, candles=(Candle('2026-11-02', 99, 102, 98, 101, 5000),))
        self.assertIs(apply_tick(history, self.tick()), history)

    def test_bounded_history_preserves_sequence_and_actual_tied_timestamps(self):
        out = self.snapshot(limit=500)
        for index in range(600):
            out = apply_tick(out, self.tick(cumulative=1002 + 2 * index))
        self.assertEqual(len(out.candles), 500)
        self.assertEqual([c.sequence for c in out.candles], list(range(101, 601)))
        self.assertEqual({c.timestamp for c in out.candles}, {self.origin.isoformat()})

    def test_delayed_feed_label_is_preserved(self):
        source = 'KIS WebSocket · free feed delayed 15 min'
        out = apply_tick(self.snapshot(), self.tick(source=source))
        self.assertEqual(out.source, source)
        self.assertEqual(out.quote.source, source)

    def test_identity_metadata_rejects_invalid_counts(self):
        for invalid in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                Candle('2026-11-02', 100, 100, 100, 100, sequence=invalid)
            with self.assertRaises(ValueError):
                Candle('2026-11-02', 100, 100, 100, 100, trade_count=invalid)


if __name__ == '__main__':
    unittest.main()
