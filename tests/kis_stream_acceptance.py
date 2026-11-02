"""Offline protocol and stream lifecycle acceptance tests; no real credentials."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from queue import Empty, Queue
from types import SimpleNamespace
import threading
import unittest
from unittest.mock import Mock, patch

from core.market.models import Instrument
from data import kis_stream as stream
from data.krx.kis_client import KISError, KISUnavailable

NOW = datetime(2026, 11, 2, 2, 15, tzinfo=timezone.utc)
KRX = Instrument()


def domestic_row(width=47, *, code="005930", price="70000", clock="111500"):
    row = ["0"] * width
    for index, value in {0: code, 1: clock, 2: price, 3: "5", 4: "100", 5: "0.14",
                         12: "7", 13: "10007", 33: "20261102", 43: "0"}.items():
        row[index] = value
    return row


def frame(tr_id, rows, encrypted="0"):
    return f"{encrypted}|{tr_id}|{len(rows):03d}|" + "^".join(value for row in rows for value in row)


class TickParsingTests(unittest.TestCase):
    def test_documented_46_and_47_field_batches_preserve_volume_and_signed_change(self):
        for width in (46, 47):
            rows = [domestic_row(width), domestic_row(width, price="70010", clock="111501")]
            ticks = stream.parse_ticks(frame("H0STCNT0", rows), KRX, now=NOW)
            self.assertEqual([t.price for t in ticks], [70000, 70010])
            self.assertEqual(ticks[0].volume, 7)
            self.assertEqual(ticks[0].cumulative_volume, 10007)
            self.assertEqual(ticks[0].change, -100)
            self.assertEqual(ticks[0].change_pct, -.14)
            self.assertEqual(ticks[0].timestamp, "2026-11-02T11:15:00+09:00")
            self.assertEqual(ticks[0].received_at, "2026-11-02T02:15:00.000+00:00")

    def test_malformed_mixed_width_encrypted_unrelated_and_expected_prices_are_ignored(self):
        row = domestic_row()
        expected = domestic_row(); expected[43] = "C"
        invalid_day = domestic_row(); invalid_day[33] = "20261340"
        negative_volume = domestic_row(); negative_volume[12] = "-7"
        missing_cumulative = domestic_row(); missing_cumulative[13] = ""
        cases = ["garbage", "0|H0STCNT0|000|", "0|H0STCNT0|x|x", b"\xff",
                 frame("H0STCNT0", [row], encrypted="1"),
                 frame("H0STCNT0", [domestic_row(code="000660")]),
                 frame("H0STCNT0", [row, domestic_row(46)]),
                 frame("H0STCNT0", [domestic_row(price="NaN")]),
                 frame("H0STCNT0", [domestic_row(clock="256100")]),
                 frame("H0STCNT0", [expected]), frame("H0STCNT0", [invalid_day]),
                 frame("H0STCNT0", [missing_cumulative]),
                 frame("H0STCNT0", [negative_volume]), frame("H0BJCNT0", [row])]
        for data in cases:
            with self.subTest(data=str(data)[:65]):
                self.assertEqual(stream.parse_ticks(data, KRX, now=NOW), ())

    def test_overseas_uses_exchange_local_date_dst_and_marks_asian_free_delay(self):
        for exchange, day, offset in (("NAS", "20261030", "-04:00"),
                                      ("NAS", "20261102", "-05:00"),
                                      ("HKS", "20261102", "+08:00")):
            instrument = Instrument("overseas_stock", "AAPL" if exchange == "NAS" else "00700", exchange)
            spec = stream.subscription_for(instrument)
            row = ["0"] * 26
            for index, value in {0: spec.tr_key, 1: instrument.code, 3: day, 4: day,
                                 5: "100001", 11: "213.75", 12: "2", 13: "1.25",
                                 14: ".59", 19: "10", 20: "204000"}.items():
                row[index] = value
            tick, = stream.parse_ticks(frame(spec.tr_id, [row]), instrument, now=NOW)
            self.assertTrue(tick.timestamp.endswith(offset))
            self.assertEqual(tick.price, 213.75)
            self.assertEqual(tick.volume, 10)
            self.assertEqual("delayed 15 min" in tick.source, exchange == "HKS")
            row[0] = "R" + row[0][1:]
            self.assertEqual(stream.parse_ticks(frame(spec.tr_id, [row]), instrument, now=NOW), ())

    def test_domestic_futures_schemas_and_bond_have_correct_price_and_volume_positions(self):
        cases = [(Instrument("domestic_future", "101W12"), 50, 5, 2, 4, 9, 10),
                 (Instrument("domestic_future", "A65612", "CF"), 50, 5, 2, 4, 9, 10),
                 (Instrument("domestic_future", "111V06", "JF"), 49, 2, 4, 5, 9, 10),
                 (Instrument("domestic_future", "201W12300", "O"), 58, 2, 4, 5, 9, 10),
                 (Instrument("domestic_future", "201W12300", "JO"), 53, 2, 4, 5, 9, 10),
                 (Instrument("bond", "KR103502GD31"), 19, 6, 4, 5, 7, 16)]
        for instrument, width, price, diff, rate, volume, cumulative in cases:
            spec = stream.subscription_for(instrument)
            row = ["0"] * width
            row[0] = instrument.code
            row[2 if instrument.asset == "bond" else 1] = "111500"
            row[3] = "5"
            for index, value in ((price, "312.25"), (diff, "1.5"), (rate, ".48"),
                                 (volume, "2"), (cumulative, "902")):
                row[index] = value
            tick, = stream.parse_ticks(frame(spec.tr_id, [row]), instrument, now=NOW)
            self.assertEqual((tick.price, tick.change, tick.volume, tick.cumulative_volume), (312.25, -1.5, 2, 902))
            self.assertIn("inferred", tick.source)

    def test_dateless_day_session_never_becomes_tomorrow_when_receipt_is_late(self):
        instrument = Instrument("bond", "KR103502GD31")
        row = ["0"] * 19
        row[0], row[2], row[6], row[7], row[16] = instrument.code, "091500", "10000", "2", "100"
        tick, = stream.parse_ticks(frame("H0BJCNT0", [row]), instrument,
                                   now=datetime(2026, 11, 2, 14, 30, tzinfo=timezone.utc))
        self.assertEqual(tick.timestamp, "2026-11-02T09:15:00+09:00")
        row[2] = "235959"
        tick, = stream.parse_ticks(frame("H0BJCNT0", [row]), instrument,
                                   now=datetime(2026, 11, 2, 15, 0, tzinfo=timezone.utc))
        self.assertEqual(tick.timestamp, "2026-11-02T23:59:59+09:00")

    def test_ambiguous_or_unsupported_subscriptions_fail_before_credentials_or_network(self):
        client = SimpleNamespace(ready=True, base_url="https://openapi.koreainvestment.com:9443", timeout_s=1)
        source = stream.KISStream(client)
        with patch.object(stream, "_approval_key", side_effect=AssertionError("unexpected network")):
            for instrument in (Instrument("overseas_future", "GCZ26"),
                               Instrument("domestic_future", "111V06"), Instrument("bond", "WRONG")):
                with self.assertRaises(ValueError): source.start(instrument, lambda t: None, lambda s: None)
            client.base_url = "https://openapivts.koreainvestment.com:29443"
            with self.assertRaises(ValueError):
                source.start(Instrument("overseas_stock", "AAPL", "NAS"), lambda t: None, lambda s: None)


class FakeConnection:
    def __init__(self, messages=()):
        self.queue = Queue()
        for message in messages: self.queue.put(message)
        self.sent = []
        self.pongs = []
        self.closed = threading.Event()

    def recv(self, timeout):
        try:
            value = self.queue.get(timeout=timeout)
        except Empty:
            raise TimeoutError from None
        if value is None: raise ConnectionError("closed")
        return value

    def send(self, message): self.sent.append(json.loads(message))
    def pong(self, message): self.pongs.append(message)
    def close(self): self.closed.set(); self.queue.put(None)


class StreamLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.client = SimpleNamespace(ready=True, base_url="https://openapi.koreainvestment.com:9443", timeout_s=.2)
        self.source = stream.KISStream(self.client)
        self.addCleanup(self.source.stop)

    def test_ack_heartbeat_and_stop_are_separate_from_receiving_a_fresh_tick(self):
        heartbeat = json.dumps({"header": {"tr_id": "PINGPONG"}})
        ack = json.dumps({"header": {"tr_id": "H0STCNT0", "tr_key": "005930"}, "body": {"rt_cd": "0"}})
        connection = FakeConnection([ack, heartbeat])
        subscribed, arrived = threading.Event(), threading.Event()
        statuses, ticks = [], []
        def status(value):
            statuses.append(value)
            if value == "SUBSCRIBED": subscribed.set()
        def tick(value): ticks.append(value); arrived.set()
        with patch.object(stream, "_approval_key", return_value="PRIVATE_APPROVAL"), \
             patch.object(stream, "_connect", return_value=connection) as connect:
            self.source.start(KRX, tick, status)
            self.assertTrue(subscribed.wait(1))
            self.assertNotIn("LIVE", statuses)
            connection.queue.put(frame("H0STCNT0", [domestic_row()]))
            self.assertTrue(arrived.wait(1))
            self.source.stop()
            self.assertFalse(self.source.running)
            self.assertEqual(len(ticks), 1)
            self.assertEqual(connection.pongs, [heartbeat.encode()])
            self.assertEqual([m["header"]["tr_type"] for m in connection.sent], ["1", "2"])
            self.assertEqual(connection.sent[0]["body"]["input"], {"tr_id": "H0STCNT0", "tr_key": "005930"})
            self.assertEqual(connect.call_args.args[0], "ws://ops.koreainvestment.com:21000")
            self.assertNotIn("PRIVATE_APPROVAL", str(statuses) + str(ticks))

    def test_callback_can_stop_without_self_join_or_later_live_status(self):
        connection = FakeConnection([frame("H0STCNT0", [domestic_row(), domestic_row(price="70010")])])
        stopped, statuses, ticks = threading.Event(), [], []
        def tick(value):
            ticks.append(value)
            self.source.stop()
            stopped.set()
        with patch.object(stream, "_approval_key", return_value="private"), \
             patch.object(stream, "_connect", return_value=connection):
            self.source.start(KRX, tick, statuses.append)
            self.assertTrue(stopped.wait(1))
            self.source.stop()
            self.assertEqual(len(ticks), 1)
            self.assertNotIn("LIVE", statuses)

    def test_two_views_keep_independent_connections_and_stopping_one_preserves_the_other(self):
        first_ready, second_ready, second_tick = threading.Event(), threading.Event(), threading.Event()
        first_ack = json.dumps({"header": {"tr_id": "H0STCNT0", "tr_key": "005930"}, "body": {"rt_cd": "0"}})
        second_ack = json.dumps({"header": {"tr_id": "H0STCNT0", "tr_key": "000660"}, "body": {"rt_cd": "0"}})
        first_connection, second_connection = FakeConnection([first_ack]), FakeConnection([second_ack])
        second = stream.KISStream(self.client)
        self.addCleanup(second.stop)
        with patch.object(stream, "_approval_key", return_value="same-server-side-key"), \
             patch.object(stream, "_connect", side_effect=[first_connection, second_connection]):
            self.source.start(KRX, lambda t: None,
                              lambda s: first_ready.set() if s == "SUBSCRIBED" else None)
            self.assertTrue(first_ready.wait(1))
            second.start(Instrument(code="000660"), lambda t: second_tick.set(),
                         lambda s: second_ready.set() if s == "SUBSCRIBED" else None)
            self.assertTrue(second_ready.wait(1))
            self.source.stop()
            self.assertTrue(first_connection.closed.is_set())
            self.assertFalse(second_connection.closed.is_set())
            self.assertTrue(second.running)
            second_connection.queue.put(frame("H0STCNT0", [domestic_row(code="000660")]))
            self.assertTrue(second_tick.wait(1))

    def test_subscription_rejection_is_terminal_and_does_not_expose_server_body(self):
        rejection = json.dumps({"header": {"tr_id": "H0STCNT0"},
                                "body": {"rt_cd": "1", "msg1": "SECRET_PROVIDER_BODY"}})
        connection = FakeConnection([rejection])
        finished, statuses = threading.Event(), []
        def status(value):
            statuses.append(value)
            if value.startswith("ERROR:"): finished.set()
        with patch.object(stream, "_approval_key", return_value="private"), \
             patch.object(stream, "_connect", return_value=connection) as connect:
            self.source.start(KRX, lambda t: None, status)
            self.assertTrue(finished.wait(1))
            self.source.stop()
            self.assertEqual(connect.call_count, 1)
            self.assertNotIn("SECRET_PROVIDER_BODY", str(statuses))
            self.assertNotIn("LIVE", statuses)

    def test_connection_failure_retries_are_bounded_and_errors_are_sanitized(self):
        finished, statuses = threading.Event(), []
        def status(value):
            statuses.append(value)
            if value.startswith("ERROR:"): finished.set()
        with patch.object(stream, "_approval_key", return_value="private"), \
             patch.object(stream, "_connect", side_effect=OSError("SECRET_URL")) as connect, \
             patch.object(stream, "_MAX_FAILURES", 2):
            self.source.start(KRX, lambda t: None, status)
            self.assertTrue(finished.wait(2))
            self.source.stop()
            self.assertEqual(connect.call_count, 2)
            self.assertIn("RECONNECTING", statuses)
            self.assertNotIn("SECRET_URL", str(statuses))

    def test_missing_credentials_fail_without_starting_a_worker(self):
        self.client.ready = False
        with patch.object(stream, "_approval_key", side_effect=AssertionError("network")):
            with self.assertRaises(KISUnavailable):
                self.source.start(KRX, lambda t: None, lambda s: None)
        self.assertFalse(self.source.running)

    def test_approval_uses_secretkey_and_reuses_the_24_hour_key_in_memory(self):
        response = Mock(status_code=200)
        response.json.return_value = {"approval_key": "APPROVAL"}
        with patch.object(config := stream.config, "kis_credentials", return_value=("KEY", "SECRET")), \
             patch.object(stream, "_APPROVAL_CACHE", {}), \
             patch.object(stream._requests, "post", return_value=response) as post:
            self.assertEqual(stream._approval_key(self.client), "APPROVAL")
            self.assertEqual(stream._approval_key(self.client), "APPROVAL")
            self.assertEqual(post.call_count, 1)
            self.assertEqual(post.call_args.kwargs["json"],
                             {"grant_type": "client_credentials", "appkey": "KEY", "secretkey": "SECRET"})
            self.assertTrue(post.call_args.args[0].endswith("/oauth2/Approval"))
        with patch.object(config, "kis_credentials", return_value=("KEY", "SECRET")), \
             patch.object(stream, "_APPROVAL_CACHE", {}), \
             patch.object(stream._requests, "post", side_effect=RuntimeError("PRIVATE")):
            with self.assertRaisesRegex(KISError, "approval request failed") as error:
                stream._approval_key(self.client)
            self.assertNotIn("PRIVATE", str(error.exception))


if __name__ == "__main__": unittest.main()
