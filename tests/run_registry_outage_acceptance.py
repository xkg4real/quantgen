"""ENG-16 checks with synthetic failure text and temporary files only."""
from concurrent.futures import ThreadPoolExecutor
import copy
import inspect
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from core.quant import run_registry_outage as outage
from core.quant.run_registry_recorder import DetachedRecorder
from core.quant.run_registry_store import SingleSegmentStore
from tests.run_registry_recorder_acceptance import AT, request


def failure():
    return {'recorded_utc': '2026-11-14T00:00:00.000000Z',
            'run_id': 'LAB-20261114T000000.000000Z-E1-0123abcd',
            'family_id': 'E1', 'symbols_typed': ['TEST'], 'stage': 'REQUESTED',
            'error': {'hook': 'started', 'type': 'OSError', 'message': '합성 오류\n새 줄'}}


class OutageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root/'unrecorded.jsonl'
        self.writer = outage.OutageWriter(self.path)

    def recorder(self, sink=None):
        path = self.root/'registry.jsonl'
        return DetachedRecorder(in_run_store=SingleSegmentStore(path, lock_timeout=0),
            after_run_store=SingleSegmentStore(path, lock_timeout=0),
            clock=lambda: AT, monotonic=lambda: 0, token_source=lambda: '0123abcd',
            outage_sink=self.writer if sink is None else sink, writer='synthetic tests')

    def test_constructor_does_not_create_a_file_or_sidecar(self):
        self.assertEqual(list(self.root.iterdir()), [])
        self.assertEqual(self.writer.path, self.path)

    def test_canonical_utf8_lf_and_no_chain_fields(self):
        record = failure()
        line = self.writer(record)
        self.assertEqual(self.path.read_bytes(), line)
        self.assertEqual(line.count(b'\n'), 1)
        self.assertNotIn(b'\r', line)
        self.assertIn('합성'.encode(), line)
        self.assertEqual(json.loads(line), record)
        self.assertEqual(set(json.loads(line)), set(record))
        self.assertEqual(list(self.root.iterdir()), [self.path])

    def test_appending_preserves_existing_bytes_and_order(self):
        first = self.writer(failure())
        second = failure(); second['error']['message'] = 'second failure'
        end = self.writer(second)
        self.assertEqual(self.path.read_bytes(), first + end)

    def test_payload_is_not_mutated(self):
        record = failure(); before = copy.deepcopy(record)
        self.writer(record)
        self.assertEqual(record, before)

    def test_unknown_time_and_identity_stay_unknown(self):
        record = failure()
        record.update(recorded_utc=None, run_id=None, family_id=None)
        self.assertEqual(json.loads(self.writer(record)), record)

    def test_invalid_records_do_not_create_files(self):
        cases = []
        for key, value in [('recorded_utc','2026-11-14T00:00:00'),
                           ('recorded_utc','badZ'), ('recorded_utc', 1),
                           ('run_id', []), ('family_id', False),
                           ('symbols_typed', ['TEST', 2]), ('stage','UNKNOWN')]:
            record=failure();record[key]=value;cases.append(record)
        record=failure();record['extra']=1;cases.append(record)
        record=failure();del record['error'];cases.append(record)
        record=failure();record['error']['message']='x'*501;cases.append(record)
        record=failure();record['error']['hook']='';cases.append(record)
        record=failure();record['error']['extra']='not allowed';cases.append(record)
        record=failure();record['error']['type']=None;cases.append(record)
        for record in cases:
            with self.subTest(record=record), self.assertRaises(outage.OutageError):
                self.writer(record)
            self.assertFalse(self.path.exists())

    def test_invalid_unicode_fails_before_file_creation(self):
        record=failure();record['error']['message']='\ud800'
        with self.assertRaises(UnicodeError):self.writer(record)
        self.assertFalse(self.path.exists())

    def test_requires_absolute_fixed_name_and_existing_parent(self):
        for path in ('unrecorded.jsonl', self.root/'registry.jsonl'):
            with self.assertRaises(outage.OutageError):outage.OutageWriter(path)
        with self.assertRaises(FileNotFoundError):
            outage.OutageWriter(self.root/'absent'/'unrecorded.jsonl')
        self.assertFalse((self.root/'absent').exists())
        with self.assertRaises(AttributeError):self.writer.path=self.root/'other.jsonl'

    def test_budget_validation_and_mutation(self):
        for value in (-1, 3, float('inf'), float('nan'), True, '1'):
            with self.subTest(value=value), self.assertRaises(outage.OutageError):
                outage.OutageWriter(self.path, lock_timeout=value)
        self.writer.lock_timeout=float('inf')
        with self.assertRaises(outage.OutageError):self.writer(failure())
        self.assertFalse(self.path.exists())

    def test_path_lock_timeout_does_not_write(self):
        self.writer.lock_timeout=0
        lock=outage._path_lock(self.writer._key, outage.time.monotonic())
        try:
            with self.assertRaises(outage.OutageLockTimeout):self.writer(failure())
            self.assertFalse(self.path.exists())
        finally:lock.release()

    def test_lock_map_timeout_does_not_write(self):
        self.writer.lock_timeout=0
        with outage._LOCKS_GUARD:
            with self.assertRaises(outage.OutageLockTimeout):self.writer(failure())
        self.assertFalse(self.path.exists())

    def test_same_path_instances_serialize_threads(self):
        other=outage.OutageWriter(self.path)
        def put(i):
            record=failure();record['error']['message']=str(i)
            (self.writer if i % 2 else other)(record)
        with ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(put, range(64)))
        rows=[json.loads(line) for line in self.path.read_bytes().splitlines()]
        self.assertEqual(len(rows),64)
        self.assertEqual({row['error']['message'] for row in rows},{str(i) for i in range(64)})
        self.assertEqual(list(self.root.iterdir()),[self.path])

    def test_flush_and_fsync_are_both_requested(self):
        real=outage.os.fdopen
        calls=[]
        class Spy:
            def __init__(self,fd,*a,**k):self.file=real(fd,*a,**k)
            def __enter__(self):return self
            def __exit__(self,*a):self.file.close()
            def write(self,b):calls.append('write');return self.file.write(b)
            def flush(self):calls.append('flush');return self.file.flush()
            def fileno(self):return self.file.fileno()
        real_sync=outage.os.fsync
        def sync(fd):calls.append('fsync');return real_sync(fd)
        with patch.object(outage.os,'fdopen',Spy), patch.object(outage.os,'fsync',sync):
            self.writer(failure())
        self.assertEqual(calls,['write','flush','fsync'])

    def test_fsync_failure_reports_uncertainty_without_retry(self):
        with patch.object(outage.os,'fsync',side_effect=OSError('synthetic fsync failure')) as sync:
            with self.assertRaises(outage.OutageWriteUncertain):self.writer(failure())
            self.assertEqual(sync.call_count,1)
        self.assertEqual(len(self.path.read_bytes().splitlines()),1)

    def test_short_write_preserves_torn_tail_and_refuses_next_append(self):
        real=outage.os.fdopen
        class Short:
            def __init__(self,fd,*a,**k):self.file=real(fd,*a,**k)
            def __enter__(self):return self
            def __exit__(self,*a):self.file.close()
            def write(self,b):return self.file.write(b[:7])
        with patch.object(outage.os,'fdopen',Short):
            with self.assertRaises(outage.OutageWriteUncertain):self.writer(failure())
        before=self.path.read_bytes()
        self.assertEqual(len(before),7)
        with self.assertRaises(outage.OutageError):self.writer(failure())
        self.assertEqual(self.path.read_bytes(),before)

    def test_incomplete_existing_tail_is_not_repaired(self):
        self.path.write_bytes(b'{"unfinished":')
        with self.assertRaises(outage.OutageError):self.writer(failure())
        self.assertEqual(self.path.read_bytes(),b'{"unfinished":')

    def test_complete_existing_lines_are_not_claimed_as_chain_verified(self):
        # The outage log is outside the registry chain: only the append boundary
        # is screened here. Parsing/reporting prior records remains separate.
        before=b'preexisting invalid JSON\n';self.path.write_bytes(before)
        tail=self.writer(failure())
        self.assertEqual(self.path.read_bytes(),before+tail)

    def test_directory_destination_is_refused(self):
        self.path.mkdir()
        with self.assertRaises(outage.OutageError):self.writer(failure())
        self.assertTrue(self.path.is_dir())

    def test_final_symlink_is_refused_when_supported(self):
        target=self.root/'untouched';target.write_bytes(b'original')
        try:self.path.symlink_to(target)
        except (OSError,NotImplementedError):self.skipTest('Symlink permission unavailable on this host')
        with self.assertRaises(outage.OutageError):self.writer(failure())
        self.assertEqual(target.read_bytes(),b'original')

    @unittest.skipUnless(hasattr(os,'mkfifo'),'POSIX FIFO fixture')
    def test_fifo_is_refused_without_blocking(self):
        os.mkfifo(self.path)
        with self.assertRaises(outage.OutageError):self.writer(failure())

    def test_open_failure_leaves_no_file_and_releases_lock(self):
        with patch.object(outage.os,'open',side_effect=PermissionError('synthetic refusal')):
            with self.assertRaises(PermissionError):self.writer(failure())
        self.assertFalse(self.path.exists())
        self.writer.lock_timeout=0
        self.writer(failure())

    def test_recorder_sends_exactly_one_durable_outage(self):
        rec=self.recorder()
        with patch.object(SingleSegmentStore,'append',side_effect=OSError('synthetic store failure')):
            self.assertFalse(rec.started(request()))
        rows=[json.loads(s) for s in self.path.read_bytes().splitlines()]
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['error']['hook'],'started')
        self.assertIsNone(rows[0]['run_id'])
        self.assertEqual(rows[0]['family_id'],'E1')
        self.assertIsNone(rec.outage_error)
        before=self.path.read_bytes()
        self.assertFalse(rec.finish())
        self.assertEqual(self.path.read_bytes(),before)

    def test_recorder_exposes_outage_failure_without_replacing_original_error(self):
        rec=self.recorder()
        original=RuntimeError('original calculation error')
        self.path.write_bytes(b'bad tail')
        with self.assertRaises(RuntimeError) as raised:
            try:raise original
            finally:rec.finish(error=original)
        self.assertIs(raised.exception,original)
        self.assertEqual(rec.state,'DISABLED')
        self.assertEqual(rec.outage_error['type'],'OutageError')
        self.assertEqual(self.path.read_bytes(),b'bad tail')

    def test_clock_failure_is_written_as_unknown_time(self):
        rec=self.recorder();rec._clock=lambda: (_ for _ in ()).throw(OSError('clock unavailable'))
        self.assertFalse(rec.started(request()))
        self.assertIsNone(json.loads(self.path.read_bytes())['recorded_utc'])

    def test_recorder_keeps_uncertain_outage_visible_without_repeating_it(self):
        rec=self.recorder()
        with patch.object(SingleSegmentStore,'append',side_effect=OSError('store failure')):
            with patch.object(outage.os,'fsync',side_effect=OSError('outage fsync failure')) as sync:
                self.assertFalse(rec.started(request()))
                self.assertEqual(sync.call_count,1)
        self.assertEqual(rec.outage_error['type'],'OutageWriteUncertain')
        before=self.path.read_bytes()
        self.assertEqual(len(before.splitlines()),1)
        self.assertFalse(rec.finish())
        self.assertEqual(self.path.read_bytes(),before)

    def test_base_exception_is_not_swallowed(self):
        with patch.object(outage.os,'open',side_effect=KeyboardInterrupt()):
            with self.assertRaises(KeyboardInterrupt):self.writer(failure())
        self.writer.lock_timeout=0
        self.writer(failure())

    def test_source_has_no_environment_discovery_or_os_sidecar_lock(self):
        source=inspect.getsource(outage)
        for text in ('import config','getenv(', 'environ[','datetime.now(',
                     'datetime.utcnow(', 'fcntl', 'msvcrt', '.mkdir(', '.unlink('):
            self.assertNotIn(text,source)


if __name__ == '__main__':
    unittest.main()
