"""Manual lane publication against a private local bare repository."""
from __future__ import annotations

import contextlib
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools.handoff import push_handoff as publisher


OS_DOC = "OS_SESSION_CURRENT.md"
UI_DOC = "UI_SESSION_CURRENT.md"
DATA_DOC = "DATA_SOURCE_SESSION_CURRENT.md"
PAY_DOC = "PAYMENTS_SESSION_CURRENT.md"
WEB_DOC = "WEBSITE_AWS_SESSION_CURRENT.md"
DIDM_DOC = "DIDM_SESSION_CURRENT.md"
QGPT_DOC = "QUANTGPT_SESSION_CURRENT.md"
LEDGER = ("# LEDGER\n| id | date | cycle | who | what | files | commit | checks |\n"
          "|---|---|---|---|---|---|---|---|\n")
CENTRAL = b"---\nstatus: taken\nfrom: gpt\ntask: central\nupdated_at: 2026-01-15\nsession: other\n---\n"
ENV_KEYS = {
    "GIT_ALLOW_PROTOCOL": "file", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_TERMINAL_PROMPT": "0", "GIT_AUTHOR_NAME": "Fixture", "GIT_COMMITTER_NAME": "Fixture",
    "GIT_AUTHOR_EMAIL": "fixture@example.invalid", "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
}


def session(task, *, status="handoff", owner="claude", session_id="one", execution="ex1"):
    return (f"---\nstatus: {status}\nfrom: {owner}\ntask: {task}\nupdated_at: 2026-01-15\n"
            f"session: {session_id}\nwork_branch: task/work\nexecution_id: {execution}\n---\n").encode()


class HandoffDocTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.remote = self.root / "upstream.git"
        self.clone = self.root / "writer"
        self.peer = self.root / "peer"
        # In particular, never inherit an enclosing Git worktree, object directory or index.
        keep = ("PATH", "SystemRoot", "windir", "COMSPEC", "PATHEXT", "TMP", "TEMP", "TMPDIR", "LANG", "LC_ALL")
        allowed_env = {k: os.environ[k] for k in keep if k in os.environ}
        env = patch.dict(os.environ, {**allowed_env, **ENV_KEYS}, clear=True)
        env.start()
        self.addCleanup(env.stop)
        self.git(self.root, "init", "--bare", "-q", "-b", "handoff", str(self.remote))
        self.git(self.root, "clone", "-q", str(self.remote), str(self.clone))
        files = {"CURRENT.md": CENTRAL, "LEDGER.md": LEDGER.encode(), "AUTO_STATE.md": b"protected snapshot\n",
                 "MERGE_QUEUE.md": b"queue\n", OS_DOC: session("os-expansion"), UI_DOC: "# 화면 기록\r\n".encode(),
                 DATA_DOC: "# 최신 소식\n\n---\nstatus: returned\n---\n".encode(),
                 PAY_DOC: session("payments-account-keys"), WEB_DOC: b"# Website notes\n",
                 DIDM_DOC: session("didm-dev"), QGPT_DOC: session("quantgpt")}
        for name, raw in files.items():
            (self.clone / name).write_bytes(raw)
        self.git(self.clone, "-c", "core.autocrlf=false", "add", "--", *files)
        self.git(self.clone, "commit", "-qm", "synthetic initial state")
        self.git(self.clone, "push", "-q", "origin", "handoff")
        self.git(self.root, "-c", "core.autocrlf=false", "clone", "-q", str(self.remote), str(self.peer))
        old_cwd = Path.cwd()
        self.addCleanup(os.chdir, old_cwd)
        os.chdir(self.clone)

    @staticmethod
    def git(cwd, *args):
        return subprocess.run(["git", "-c", "core.autocrlf=false", "-C", str(cwd), *args],
                              cwd=cwd, capture_output=True, check=True).stdout

    def tip(self):
        return self.git(self.remote, "rev-parse", "refs/heads/handoff").strip()

    def remote_bytes(self, name):
        return self.git(self.remote, "show", f"refs/heads/handoff:{name}")

    def run_cli(self, *args):
        capture = io.StringIO()
        with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(capture):
            try:
                return publisher.main(list(map(str, args)))
            except SystemExit as exc:
                return exc.code

    def peer_write(self, name, data):
        (self.peer / name).write_bytes(data)
        self.git(self.peer, "add", "--", name)
        self.git(self.peer, "commit", "-qm", "other writer")
        self.git(self.peer, "push", "-q", "origin", "handoff")

    def test_only_named_report_changes_and_original_writer_index_worktree_survive(self):
        original = self.tip().decode()
        (self.clone / "scratch.txt").write_text("do not touch")
        self.git(self.clone, "add", "--", "scratch.txt")
        index = (self.clone / ".git/index").read_bytes()
        data = b"\xef\xbb\xbf# Edited heading\r\n"
        (self.clone / UI_DOC).write_bytes(data)
        self.assertEqual(self.run_cli("--doc", UI_DOC), 0)
        self.assertEqual(self.git(self.remote, "diff", "--name-only", original, "handoff").splitlines(),
                         [UI_DOC.encode()])
        self.assertEqual(self.remote_bytes(UI_DOC), data)
        self.assertEqual(self.remote_bytes("CURRENT.md"), CENTRAL)
        self.assertEqual((self.clone / ".git/index").read_bytes(), index)
        self.assertEqual(self.git(self.clone, "rev-parse", "HEAD").strip().decode(), original)
        self.assertEqual((self.clone / "scratch.txt").read_text(), "do not touch")
        verified = self.tip()
        self.assertEqual(self.run_cli("--doc", UI_DOC), 0)
        self.assertEqual(self.tip(), verified)

    def test_all_existing_report_formats_and_single_argument_cli(self):
        for name in (OS_DOC, DATA_DOC, PAY_DOC, WEB_DOC, UI_DOC, DIDM_DOC, QGPT_DOC):
            path = self.clone / name
            raw = b"## Manual update\n\n" + path.read_bytes()
            path.write_bytes(raw)
            self.assertEqual(self.run_cli("--doc", path), 0, name)
            self.assertEqual(self.remote_bytes(name), raw)

    def test_new_lanes_take_only_their_own_task_and_the_data_lane_takes_both_names(self):
        # 2026-11-24: DIDM development and QuantGPT have lanes; the data lane is "data-source" (old name still accepted).
        # The QuantGPT lane also takes "quantgpt-q0", the name in the document that session first published by hand.
        for name, task in ((DIDM_DOC, "didm-dev"), (QGPT_DOC, "quantgpt"), (DATA_DOC, "data-source")):
            raw = session(task, status="returned")
            (self.clone / name).write_bytes(raw)
            self.assertEqual(self.run_cli("--doc", name), 0, (name, task))
            self.assertEqual(self.remote_bytes(name), raw)
        self.assertIsNone(publisher.lane_refusal(DATA_DOC, {}, {"task": "data-source-didm"}))
        self.assertIsNone(publisher.lane_refusal(QGPT_DOC, {}, {"task": "quantgpt-q0"}))
        self.assertEqual(publisher.lane_tasks(DATA_DOC), ("data-source", "data-source-didm"))
        self.assertEqual(publisher.lane_tasks(DIDM_DOC), ("didm-dev",))
        self.assertEqual(publisher.lane_tasks(QGPT_DOC), ("quantgpt", "quantgpt-q0"))
        self.assertEqual(publisher.lane_tasks(OS_DOC), ("os-expansion",))
        self.assertEqual(publisher.lane_tasks(PAY_DOC), ("payments-account-keys",))
        self.assertEqual(publisher.lane_tasks(UI_DOC), ())
        self.assertEqual(publisher.lane_tasks(WEB_DOC), ())
        # A report lane (UI, website) refuses every assigned name, including each name of a lane that has two.
        for name, task in ((DIDM_DOC, "quantgpt"), (QGPT_DOC, "didm-dev"), (DATA_DOC, "didm-dev"),
                           (OS_DOC, "data-source"), (UI_DOC, "quantgpt"), (PAY_DOC, "data-source-didm"),
                           (UI_DOC, "data-source"), (WEB_DOC, "data-source-didm"), (UI_DOC, "didm-dev"),
                           (WEB_DOC, "quantgpt-q0"), (QGPT_DOC, "data-source"), (DIDM_DOC, "quantgpt-q0"),
                           (OS_DOC, "quantgpt-q0")):
            self.assertEqual(publisher.lane_refusal(name, {}, {"task": task}),
                             "the document names a task assigned to a different lane", (name, task))
        before = self.remote_bytes(OS_DOC)
        (self.clone / OS_DOC).write_bytes(session("quantgpt", status="returned"))
        self.assertEqual(self.run_cli("--doc", OS_DOC), 3)
        self.assertEqual(self.remote_bytes(OS_DOC), before)

    def test_out_of_tree_drafts_preserve_published_markdown(self):
        path = self.root / WEB_DOC
        prior = self.remote_bytes(WEB_DOC)
        path.write_bytes(b"entirely unrelated\n")
        self.assertEqual(self.run_cli("--doc", path), 3)
        path.write_bytes(prior + b"new note\n")
        self.assertEqual(self.run_cli("--doc", path), 0)
        self.assertEqual(self.remote_bytes(WEB_DOC), path.read_bytes())

    def test_stale_edit_preexisting_at_command_start_cannot_overwrite(self):
        old = self.remote_bytes(UI_DOC)
        self.peer_write(UI_DOC, old + b"peer change\n")
        self.git(self.clone, "fetch", "-q", "origin", "handoff")
        (self.clone / UI_DOC).write_bytes(old + b"mine\n")
        self.assertEqual(self.run_cli("--doc", UI_DOC), 3)
        self.assertEqual(self.remote_bytes(UI_DOC), old + b"peer change\n")

    def test_detached_handoff_checkout_supports_editing_in_place(self):
        self.git(self.clone, "checkout", "--detach", "-q", "origin/handoff")
        (self.clone / OS_DOC).write_bytes(session("os-expansion", status="returned"))
        self.assertEqual(self.run_cli("--doc", OS_DOC), 0)
        self.assertEqual(self.remote_bytes(OS_DOC), session("os-expansion", status="returned"))

    def test_topic_checkout_can_edit_an_index_copy_of_the_fetched_report(self):
        self.git(self.clone, "checkout", "-qb", "feature")
        self.git(self.clone, "rm", "--", UI_DOC)
        self.git(self.clone, "commit", "-qm", "code branch lacks report")
        self.git(self.clone, "checkout", "origin/handoff", "--", UI_DOC)
        proposed = b"updated without repeating old heading\n"
        (self.clone / UI_DOC).write_bytes(proposed)
        self.assertEqual(self.run_cli("--doc", UI_DOC), 0)
        self.assertEqual(self.remote_bytes(UI_DOC), proposed)

    def test_portable_draft_cannot_use_an_already_advanced_tracking_ref_as_its_base(self):
        path = self.root / UI_DOC
        path.write_bytes(b"edit made in separate folder\n")
        self.peer_write(UI_DOC, b"new report during edit\n")
        self.git(self.clone, "fetch", "-q", "origin", "handoff")
        self.assertEqual(self.run_cli("--doc", path), 3)
        self.assertEqual(self.remote_bytes(UI_DOC), b"new report during edit\n")

    def test_rejects_a_lexically_protected_source_path(self):
        protected = self.root / "docs/asset_expansion/cache"
        protected.mkdir(parents=True)
        (protected / UI_DOC).write_bytes(self.remote_bytes(UI_DOC))
        self.assertEqual(self.run_cli("--doc", protected / UI_DOC), 2)

    def test_resolved_directory_aliases_and_source_file_symlink(self):
        protected = self.root / "docs/asset_expansion/cache"
        protected.mkdir(parents=True)
        (protected / UI_DOC).write_bytes(self.remote_bytes(UI_DOC))
        alias = self.root / "alias"
        forbidden = self.root / "blocked-alias"
        linked_file = self.root / UI_DOC
        try:
            alias.symlink_to(self.clone, target_is_directory=True)
        except OSError as exc:
            if os.name == "nt" and (getattr(exc, "winerror", None) == 1314 or isinstance(exc, PermissionError)):
                self.skipTest("Windows user lacks permission to create the test symlinks")
            raise
        forbidden.symlink_to(protected, target_is_directory=True)
        linked_file.symlink_to(self.clone / UI_DOC)
        self.assertEqual(self.run_cli("--doc", alias / UI_DOC), 0)
        self.assertEqual(self.run_cli("--doc", forbidden / UI_DOC), 2)
        self.assertEqual(self.run_cli("--doc", linked_file), 2)

    def test_race_on_target_preserves_winner(self):
        push = publisher.push_commit
        def racing_push(remote, branch, sha):
            self.peer_write(UI_DOC, b"peer's update\n")
            return push(remote, branch, sha)
        (self.clone / UI_DOC).write_bytes(b"my update\n")
        with patch.object(publisher, "push_commit", side_effect=racing_push):
            self.assertEqual(self.run_cli("--doc", UI_DOC), 3)
        self.assertEqual(self.remote_bytes(UI_DOC), b"peer's update\n")

    def test_race_on_another_lane_rebuilds_without_dropping_either_report(self):
        push = publisher.push_commit
        first = True
        def racing_push(remote, branch, sha):
            nonlocal first
            if first:
                first = False
                self.peer_write(WEB_DOC, b"website update\n")
            return push(remote, branch, sha)
        (self.clone / UI_DOC).write_bytes(b"UI update\n")
        with patch.object(publisher, "push_commit", side_effect=racing_push):
            self.assertEqual(self.run_cli("--doc", UI_DOC), 0)
        self.assertEqual(self.remote_bytes(UI_DOC), b"UI update\n")
        self.assertEqual(self.remote_bytes(WEB_DOC), b"website update\n")

    def test_readback_uses_latest_target_and_original_bytes(self):
        push = publisher.push_commit
        def changed_after_push(remote, branch, sha):
            pushed = push(remote, branch, sha)
            self.git(self.peer, "pull", "-q", "--ff-only", "origin", "handoff")
            self.peer_write(UI_DOC, b"newer report\n")
            return pushed
        (self.clone / UI_DOC).write_bytes(b"sent first\n")
        with patch.object(publisher, "push_commit", side_effect=changed_after_push):
            self.assertEqual(self.run_cli("--doc", UI_DOC), 4)
        self.assertEqual(self.remote_bytes(UI_DOC), b"newer report\n")

    def test_explicit_task_and_active_owner_cannot_be_replaced_by_another_session(self):
        path = self.clone / OS_DOC
        path.write_bytes(session("payments-account-keys"))
        self.assertEqual(self.run_cli("--doc", path), 3)
        active = session("os-expansion", status="taken")
        self.peer_write(OS_DOC, active)
        self.git(self.clone, "restore", "--", OS_DOC)
        self.git(self.clone, "pull", "-q", "--ff-only", "origin", "handoff")
        for other in (session("os-expansion", owner="gpt"), session("os-expansion", session_id="another"),
                      session("os-expansion", execution="another"), b"# Just Markdown\n"):
            path.write_bytes(other)
            self.assertEqual(self.run_cli("--doc", path), 3)
        path.write_bytes(active + b"same owner\n")
        self.assertEqual(self.run_cli("--doc", path), 0)

    def test_create_previously_missing_assigned_lane(self):
        self.git(self.peer, "rm", "--", PAY_DOC)
        self.git(self.peer, "commit", "-qm", "not provisioned")
        self.git(self.peer, "push", "-q", "origin", "handoff")
        self.git(self.clone, "pull", "-q", "--ff-only", "origin", "handoff")
        proposed = session("payments-account-keys", status="checkpoint")
        (self.clone / PAY_DOC).write_bytes(proposed)
        self.assertEqual(self.run_cli("--doc", PAY_DOC), 0)
        self.assertEqual(self.remote_bytes(PAY_DOC), proposed)

    def test_bad_inputs_and_control_options_never_change_remote(self):
        before = self.tip()
        for args in [
            ("--doc", "CURRENT.md"), ("--doc", "AUTO_STATE.md"), ("--doc", "LEDGER.md"),
            ("--doc", "MERGE_QUEUE.md"), ("--doc", "WORKBOARD.md"), ("--doc", ".env"),
            ("--doc", "other/../" + UI_DOC), ("--doc", UI_DOC, "--branch", "main"),
            ("--doc", UI_DOC, "--force"), ("--doc", UI_DOC, "--done", "x"), ("--doc", UI_DOC, "--key", "x"),
            ("--doc", UI_DOC, "--show"), ("--doc", UI_DOC, "--ledger"), ("draft.md", "--doc", UI_DOC),
        ]:
            with self.subTest(args=args):
                self.assertEqual(self.run_cli(*args), 2)
        for bad in (b"", b"\xff", b"contains\0nul"):
            (self.clone / UI_DOC).write_bytes(bad)
            self.assertEqual(self.run_cli("--doc", UI_DOC), 2)
        self.assertEqual(self.tip(), before)

    def test_default_current_lock_show_and_ledger_remain_separate(self):
        self.assertEqual(self.run_cli("--show"), 0)
        self.assertEqual(self.run_cli("--ledger"), 0)
        draft = self.root / "central.md"
        draft.write_bytes(session("central", owner="claude"))
        self.assertEqual(self.run_cli(draft), 3)
        draft.write_bytes(session("central", owner="gpt", status="returned"))
        done = f"t8-test | report | fixture | {self.tip().decode()} | synthetic"
        self.assertEqual(self.run_cli(draft, "--done", done), 0)
        self.assertEqual(self.remote_bytes("CURRENT.md"), draft.read_bytes())
        self.assertIn(b"| t8-test |", self.remote_bytes("LEDGER.md"))


if __name__ == "__main__":
    unittest.main()
