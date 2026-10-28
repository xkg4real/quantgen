"""Suite `nautilus`: the NautilusTrader bridge (spec docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md).

Layer 1 runs in the global interpreter on synthetic inputs only. Layer 2 starts children in the hash-pinned venv
named by QUANTGEN_NAUTILUS_PYTHON, through the launch contract of tools/nautilus/launch.py (spec 4.3): NOT_RUN
when the key is blank or names a missing file, FAIL when the venv is off its pins (O15).

Every test runs inside `guarded` (spec 3.3): the production ledger dirs and docs/nautilus_bridge/ are digested
before and after, and QUANTGEN_MACRO_DIR names a fresh temp dir while the test runs. `tests()` returns every test
sorted by name, then LAST_TEST, which compares the digests taken when the suite started (L1-32).

    python3 -B -m tests.nautilus_acceptance [-k <substring>] ...    prints only; never writes qa/acceptance_results.json
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import importlib.util
import inspect
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Callable, Sequence

from tests.notrun import NotRun, require_fixture
from tools.nautilus import launch

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_MANIFEST = ROOT / "tests" / "fixtures" / "nautilus" / "MANIFEST.csv"
LAST_TEST = "test_l1_32_every_test_guarded_and_ledgers_unchanged"
_ROOTS: tuple[Path, ...] | None = None
_SUITE_START: dict[str, str] | None = None


# --------------------------------------------------------------------------- #
# The guard of spec 3.3 and the layer-2 gate
# --------------------------------------------------------------------------- #
def guard_roots() -> tuple[Path, ...]:
    """Resolved once per process, at the first call, before any guard moves QUANTGEN_MACRO_DIR (spec 3.3)."""
    global _ROOTS
    if _ROOTS is None:
        import config
        _ROOTS = (Path.home() / ".nextgen" / "macro" / "ledgers", config.macro_dir() / "ledgers",
                  ROOT / "docs" / "nautilus_bridge")
    return _ROOTS


def digest_roots(roots: Sequence[Path]) -> dict[str, str]:
    """{path: md5 of its bytes} for every file under each root; an absent root adds nothing."""
    out: dict[str, str] = {}
    for root in roots:
        if root.is_file():
            out[str(root)] = hashlib.md5(root.read_bytes()).hexdigest()
        elif root.is_dir():
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    out[str(path)] = hashlib.md5(path.read_bytes()).hexdigest()
    return out


def guarded(name: str, fn: Callable[[], None]) -> Callable[[], None]:
    """Digests the guard roots before and after `fn`; while it runs, QUANTGEN_MACRO_DIR names a fresh temp dir, and
    on Windows a layer-2 test keeps the machine awake (spec 5.7). The first call records the suite-start digests.
    The after-digest is taken in `finally`, so a write is a FAIL even when `fn` raised NotRun or failed."""
    def run() -> None:
        global _SUITE_START
        roots = guard_roots()
        before = digest_roots(roots)
        if _SUITE_START is None:
            _SUITE_START = before
        saved = os.environ.get("QUANTGEN_MACRO_DIR")
        macro_tmp = tempfile.mkdtemp(prefix="qgnb_macro_")
        awake = os.name == "nt" and name.startswith("test_l2_")
        os.environ["QUANTGEN_MACRO_DIR"] = macro_tmp
        try:
            if awake:
                import ctypes
                ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)   # ES_CONTINUOUS | ES_SYSTEM_REQUIRED
            fn()
        finally:
            if awake:
                ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)   # ES_CONTINUOUS
            if saved is None:
                os.environ.pop("QUANTGEN_MACRO_DIR", None)
            else:
                os.environ["QUANTGEN_MACRO_DIR"] = saved
            shutil.rmtree(macro_tmp, ignore_errors=True)
            after = digest_roots(roots)
            changed = sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
            if changed:                 # replaces an exception in flight, which becomes its __context__
                raise AssertionError(f"{name} changed guarded files (spec 3.3): {changed}")
    run.__name__ = name
    run.nautilus_guarded = True
    return run


def layer2() -> Path:
    """The venv python for a layer-2 test: NotRun on a blank key or a missing file; a FAIL off the pins (O15)."""
    value = launch.venv_key()
    if not value:
        raise NotRun("OWNER: Nautilus venv not configured (QUANTGEN_NAUTILUS_PYTHON)")
    if not Path(os.path.expanduser(os.path.expandvars(value))).is_file():
        raise NotRun(f"OWNER: QUANTGEN_NAUTILUS_PYTHON points to a missing file: {value!r}")
    python = launch.resolve_venv_python(value)
    bad = launch.venv_mismatches(launch.read_venv(python))
    assert not bad, "the Nautilus venv is off its pins (O15): " + "; ".join(bad)
    return python


def test_l1_15_encoding_rules_hold():
    """L1-15 (spec 8.3 and 3.7; QA-R2-14): in tools/nautilus/*.py and tests/nautilus_*.py every open (a constant
    binary mode exempt), read_text and write_text passes encoding="utf-8" (or "utf-8-sig"), every text write newline=,
    every text-mode subprocess call encoding="utf-8" and errors="replace", every csv writer lineterminator="\\n"; no
    committed bridge CSV, no file launch.fixture_inputs builds (plan Task 3) and no bars.csv runner.bars_bytes builds
    (plan Task 4; the one CSV the parent writes) holds a carriage return."""
    planted = {'open(p, "w")': 2, "p.read_text()": 1, 'p.write_text(s, encoding="utf-8")': 1,
               "subprocess.run(a, text=True)": 1, "csv.writer(fh)": 1, 'open(p, "rb")': 0,
               'p.read_text(encoding="utf-8-sig")': 0, 'p.write_text(s, encoding="utf-8", newline="\\n")': 0,
               'subprocess.run(a, text=True, encoding="utf-8", errors="replace")': 0,
               "subprocess.run(a, capture_output=True)": 0, 'csv.writer(fh, lineterminator="\\n")': 0,
               'inside(root, "fills.csv").open("w", encoding="utf-8", newline="")': 0}
    for snippet, want in planted.items():
        got = encoding_offences(snippet, "planted.py")
        assert len(got) == want, (snippet, got)
    files = sorted((ROOT / "tools" / "nautilus").glob("*.py")) + sorted((ROOT / "tests").glob("nautilus_*.py"))
    assert ROOT / "tools" / "nautilus" / "launch.py" in files and Path(__file__).resolve() in files, files
    hits = [h for p in files for h in encoding_offences(p.read_text(encoding="utf-8"), p.relative_to(ROOT).as_posix())]
    assert not hits, "encoding rules of spec 3.7 broken:\n  " + "\n  ".join(hits)
    csvs = sorted((ROOT / "tests" / "fixtures" / "nautilus").glob("*.csv")) + sorted((ROOT / "tools" / "nautilus").rglob("*.csv"))
    assert csvs, "no committed bridge CSV"
    bad = [p.relative_to(ROOT).as_posix() for p in csvs if b"\r" in p.read_bytes()]
    from tools.nautilus import launch
    build = getattr(launch, "fixture_inputs", None)
    bad += [f"fixture_inputs({n!r})" for n in getattr(launch, "FIXTURES", ()) if build and b"\r" in b"".join(build(n))]
    if (ROOT / "tools" / "nautilus" / "runner.py").is_file():          # plan Task 4: the parent's bars.csv (C3, C10)
        import numpy as np
        from tools.nautilus import runner
        if b"\r" in runner.bars_bytes(np.array([1.0, 2.0]), [1, 2]):
            bad.append("runner.bars_bytes")
    assert not bad, f"carriage returns in {bad}"


def encoding_offences(source: str, rel: str) -> list[str]:
    """The AST rules of L1-15 (spec 3.7) over one file's source: "<rel>:<line>: <call>() <problem>" per broken call.
    A mode is the `mode=` keyword or the first positional string that looks like one; `open` and `fdopen` default to
    "r", `read_text` reads, `write_text` writes. A subprocess call is in text mode when it passes `text=True`,
    `universal_newlines=True`, `encoding=` or `errors=`."""
    import ast
    import re
    out = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
        kw = {k.arg: (k.value.value if isinstance(k.value, ast.Constant) else k.value) for k in node.keywords if k.arg}
        where = f"{rel}:{node.lineno}: {name}()"
        if name in ("open", "fdopen", "read_text", "write_text"):
            modes = [a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)
                     and re.fullmatch(r"[rwxab+t]{1,3}", a.value)]
            mode = {"read_text": "r", "write_text": "w"}.get(name, kw.get("mode", modes[0] if modes else "r"))
            if isinstance(mode, str) and "b" in mode:
                continue
            if kw.get("encoding") not in ("utf-8", "utf-8-sig"):
                out.append(f'{where} without encoding="utf-8"')
            if (not isinstance(mode, str) or set(mode) & set("wxa+")) and kw.get("newline") not in ("\n", ""):
                out.append(f'{where} writes text without newline="\\n"')
        elif name in ("run", "Popen", "check_output", "check_call", "call") and (
                kw.get("text") is True or kw.get("universal_newlines") is True or "encoding" in kw or "errors" in kw):
            if kw.get("encoding") != "utf-8" or kw.get("errors") != "replace":
                out.append(f'{where} in text mode without encoding="utf-8", errors="replace"')
        elif name in ("writer", "DictWriter") and kw.get("lineterminator") != "\n":
            out.append(f'{where} without lineterminator="\\n"')
    return out


def tests() -> list[tuple[str, Callable[[], None]]]:
    """Every module-level test_* sorted by name, LAST_TEST excepted; then LAST_TEST. Each one guarded."""
    guard_roots()
    found = sorted((n, f) for n, f in globals().items() if n.startswith("test_") and callable(f) and n != LAST_TEST)
    return [(n, guarded(n, f)) for n, f in found] + [(LAST_TEST, guarded(LAST_TEST, globals()[LAST_TEST]))]


# --------------------------------------------------------------------------- #
# Helpers (never named test_*)
# --------------------------------------------------------------------------- #
def _refused(call: Callable[[], object], rid: str) -> launch.BridgeRefusal:
    try:
        call()
    except launch.BridgeRefusal as exc:
        assert exc.rid == rid and str(exc).startswith(f"{rid}: "), exc
        return exc
    raise AssertionError(f"no {rid} refusal")


def _invalid(call: Callable[[], object], cid: str) -> launch.ChildInvalid:
    try:
        call()
    except launch.ChildInvalid as exc:
        assert exc.cid == cid and str(exc).startswith(f"{cid}: "), exc
        return exc
    raise AssertionError(f"no {cid}")


def _fake_venv(root: Path, *, os_name: str, record: str, tag: str, versions: dict | None = None,
               cfg: dict | None = None) -> Path:
    """A venv-shaped dir: pyvenv.cfg, an empty python file and the dist-info files read_venv reads."""
    versions = {"nautilus_trader": "1.231.0", "numpy": "2.3.5", "pandas": "2.3.3", **(versions or {})}
    lines = {"home": str(root.parent / "base"), "include-system-site-packages": "false", "version": "3.13.17",
             "executable": str(root.parent / "base" / "python3.13"), **(cfg or {})}
    minor = ".".join(lines["version"].split(".")[:2])
    if os_name == "nt":
        python, site = root / "Scripts" / "python.exe", root / "Lib" / "site-packages"
    else:
        python, site = root / "bin" / "python", root / "lib" / f"python{minor}" / "site-packages"
    python.parent.mkdir(parents=True)
    python.write_bytes(b"")
    (root / "pyvenv.cfg").write_text("".join(f"{k} = {v}\n" for k, v in lines.items()), encoding="utf-8",
                                     newline="\n")
    for name, version in versions.items():
        info = site / f"{name}-{version}.dist-info"
        info.mkdir(parents=True)
        (info / "METADATA").write_text(f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n\nVersion: 0.0\n",
                                       encoding="utf-8", newline="\n")
    info = site / f"nautilus_trader-{versions['nautilus_trader']}.dist-info"
    (info / "WHEEL").write_text(f"Wheel-Version: 1.0\nRoot-Is-Purelib: false\nTag: {tag}\n", encoding="utf-8",
                                newline="\n")
    (info / "RECORD").write_text(record, encoding="utf-8", newline="\n")
    return python


def _launch_venv(python: Path, mode_args: list[str], *, script: Path = launch.SANDBOX,
                 timeout: float = launch.TIMEOUT_S) -> launch.ChildResult:
    tmp = launch.make_tempdir()
    try:
        child = launch.build_launch(mode_args, tempdir=tmp, venv_python=python, unshare=launch.resolve_unshare(),
                                    script=script)
        result = launch.run_child(child, timeout=timeout)
    finally:
        left = launch.cleanup_tempdir(tmp)
    assert left == [], left
    return result


def _gone(pid: int) -> bool:
    """Linux: True when the process has exited (no /proc entry, or a zombie nobody has reaped yet)."""
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    except FileNotFoundError:
        return True
    return stat.rsplit(")", 1)[1].split()[0] == "Z"


# --------------------------------------------------------------------------- #
# Plan Task 1 (spec Step 3): layer 1
# --------------------------------------------------------------------------- #
LINUX_RECORD = "nautilus_trader-1.231.0.manylinux_2_35_x86_64.RECORD"
WIN_RECORD = "nautilus_trader-1.231.0.win_amd64.RECORD"
LINUX_IDENTITY = ("a448cd20501f6050edba17cf0e6fe8771e94e454213ece96ed936c15548f03f9", 764)
WIN_IDENTITY = ("47d274d79b85a43b79917e9b993fa3e68ebf68138c4a8b86527c5902cf439555", 764)
PINS_JSON = {"schema": "nautilus-bridge-env-pins/1",
             "platforms": {"manylinux_2_35_x86_64": {
                               "python_minor": "3.13",
                               "versions": {"nautilus_trader": "1.231.0", "numpy": "2.3.5", "pandas": "2.3.3"},
                               "wheel_tag": "cp313-cp313-manylinux_2_35_x86_64",
                               "record_digest_sha256": LINUX_IDENTITY[0], "record_entries": 764},
                           "win_amd64": {
                               "python_minor": "3.13",
                               "versions": {"nautilus_trader": "1.231.0", "numpy": "2.3.5", "pandas": "2.3.3"},
                               "wheel_tag": "cp313-cp313-win_amd64",
                               "record_digest_sha256": WIN_IDENTITY[0], "record_entries": 764}}}
EXPECTED_VERSIONS = {"nautilus-trader": "1.231.0", "numpy": "2.3.5", "pandas": "2.3.3"}
REQ_HEADER = (
    "# QUANTGEN NautilusTrader bridge: a research-only backtest engine, run only as a subprocess (spec 2026-10-26).",
    "# NEVER install with the global python: tests/frozen_guard.py clause (d) pins numpy 2.3.5, scipy 1.18.0 and",
    "# pandas 2.3.3, and tests/nautilus_acceptance.py fails while nautilus_trader is importable there.",
    "# Install only into the dedicated venv (spec section 4.4), never created with --system-site-packages:",
    r'#   cmd:        "%LOCALAPPDATA%\quantgen\ntvenv\Scripts\python.exe" -m pip install --require-hashes'
    r' --only-binary=:all: --no-cache-dir --no-index --find-links "%LOCALAPPDATA%\quantgen\wheels"'
    r' -r requirements-nautilus.txt',
    r'#   PowerShell: & "$env:LOCALAPPDATA\quantgen\ntvenv\Scripts\python.exe" -m pip install --require-hashes'
    r' --only-binary=:all: --no-cache-dir --no-index --find-links "$env:LOCALAPPDATA\quantgen\wheels"'
    r' -r requirements-nautilus.txt',
)
REQ_PINS = {   # spec 5.1: name -> (version, environment marker, number of --hash lines)
    "click": ("8.5.0", "", 1), "colorama": ("0.4.6", 'sys_platform == "win32"', 1), "fsspec": ("2026.2.0", "", 1),
    "msgspec": ("0.22.0", "", 2), "nautilus-trader": ("1.231.0", "", 2), "numpy": ("2.3.5", "", 2),
    "pandas": ("2.3.3", "", 2), "portion": ("2.6.3", "", 1), "pyarrow": ("26.0.0", "", 2),
    "python-dateutil": ("3.0.0", "", 1), "pytz": ("2026.5", "", 1), "six": ("1.17.0", "", 1),
    "sortedcontainers": ("2.4.0", "", 1), "tqdm": ("4.70.1", "", 1), "tzdata": ("2026.5", "", 1),
    "uvloop": ("0.22.1", 'sys_platform != "win32"', 1)}
NAUTILUS_HASHES = {"5fc8e08e98b6a47a5f0104c12ac6d8d3cefa0fd9dd2bb0d211c1b14517ff9aaf",    # win_amd64 (PyPI)
                   "429ea61c33a32cd8498d39e0ea95ebaa12b8dbfc25c71fbaba845f2b05e8ab91"}    # manylinux_2_35_x86_64
REQ_BODY_SHA256 = "49c1cee13798cbc92104bd398af422f611334db1f79260231c0c357fd7d0b5e4"
ENV_LINE = "QUANTGEN_NAUTILUS_PYTHON='C:/Users/<you>/AppData/Local/quantgen/ntvenv/Scripts/python.exe'"
ENV_HEADING = "# --- NautilusTrader bridge (research only) ----------------------------------"
PRECISION = {"manylinux_2_35_x86_64": {"HIGH_PRECISION": True, "FIXED_PRECISION": 16,
                                       "QUANTITY_MAX": 34028236692093.0, "PRICE_MAX": 17014118346046.0},
             "win_amd64": {"HIGH_PRECISION": False, "FIXED_PRECISION": 9,              # spec 3.6; UNVERIFIED to 7A
                           "QUANTITY_MAX": 18446744073.0, "PRICE_MAX": 9223372036.0}}
SYSTEM = {"manylinux_2_35_x86_64": "Linux", "win_amd64": "Windows"}
SELFTEST = {"backtest": "passed", "live": "raised", "live_clock": "raised", "sandbox": "raised", "test_clock": "passed"}


def test_l1_16_launch_builder_matches_the_contract():
    """L1-16: given os_name "nt" and "posix", build_launch builds exactly 4.3's argv and environment, with unshare on
    POSIX and each platform's process-group flag, and starts no process; make_tempdir creates home and tmp; a key
    outside the contract, or one missing, is C-10; a child_cmd that is empty or relative, or no child_cmd and no venv
    python, is a ValueError; resolve_unshare is R-14 without unshare on PATH or when `unshare -rn true` fails."""
    tmp = launch.make_tempdir()
    try:
        assert tmp.name.startswith("qgnb_") and str(tmp) == os.path.realpath(tmp), tmp
        assert (tmp / "home").is_dir() and (tmp / "tmp").is_dir()
        environ = {"PATH": "/x", "HOME": "/h", "SYSTEMROOT": r"C:\Windows", "PYTHONPATH": "/p", "NAUTILUS_PATH": "/n",
                   "QUANTGEN_NAUTILUS_PYTHON": "/v", "FMP_API_KEY": "k", "TMPDIR": "/t", "LANG": "ko_KR.UTF-8"}
        un, py = "/usr/bin/unshare", PurePosixPath("/opt/qg/ntvenv/bin/python")
        wpy = PureWindowsPath(r"C:\Users\o\AppData\Local\quantgen\ntvenv\Scripts\python.exe")
        sandbox, probe = str(launch.SANDBOX), str(launch.EGRESS_PROBE)
        posix_env = {"PATH": "/opt/qg/ntvenv/bin:/usr/bin:/bin", "HOME": f"{tmp}/home", "TMPDIR": f"{tmp}/tmp",
                     "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}
        nt_env = {"SYSTEMROOT": r"C:\Windows",
                  "PATH": r"C:\Users\o\AppData\Local\quantgen\ntvenv\Scripts;C:\Windows\System32",
                  "USERPROFILE": f"{tmp}\\home", "HOME": f"{tmp}\\home", "TEMP": f"{tmp}\\tmp", "TMP": f"{tmp}\\tmp"}
        pipes = {"stdin": subprocess.DEVNULL, "stdout": subprocess.PIPE, "stderr": subprocess.PIPE, "text": True,
                 "encoding": "utf-8", "errors": "replace"}
        head = [un, "-rn", str(py), "-I", "-B", "-X", "utf8"]
        whead = [str(wpy), "-I", "-B", "-X", "utf8"]
        run_args = ["run", "--in", str(tmp)]
        stub = ["/usr/local/bin/python3", "-I", "/r/tests/nautilus_stub_child.py", "--exit", "1"]
        wstub = [r"C:\py313\python.exe", "-I", r"C:\r\tests\nautilus_stub_child.py"]

        def no_process(*_a, **_k):
            raise AssertionError("build_launch started a process")
        saved = (subprocess.Popen, subprocess.run, shutil.which)
        subprocess.Popen = subprocess.run = no_process
        try:
            def build(mode, os_name, **kw):
                kw.setdefault("venv_python", py if os_name == "posix" else wpy)
                return launch.build_launch(mode, tempdir=tmp, os_name=os_name, environ=environ, **kw)
            group = {"posix": {"start_new_session": True}, "nt": {"creationflags": 0x00000200}}  # NEW_PROCESS_GROUP
            cases = [
                ("posix", build(["--check-env"], "posix", unshare=un), head + [sandbox, "--check-env"], posix_env),
                ("posix", build(["--guard-selftest"], "posix", unshare=un), head + [sandbox, "--guard-selftest"],
                 posix_env),
                ("posix", build(run_args, "posix", unshare=un), head + ["-X", "importtime", sandbox, *run_args],
                 posix_env),
                ("posix", build([], "posix", unshare=un, script=launch.EGRESS_PROBE), head + [probe], posix_env),
                ("posix", build(run_args, "posix", unshare=un, venv_python=None, child_cmd=stub),
                 [un, "-rn", *stub, *run_args], {**posix_env, "PATH": "/usr/local/bin:/usr/bin:/bin"}),
                ("nt", build(["--check-env"], "nt"), whead + [sandbox, "--check-env"], nt_env),
                ("nt", build(run_args, "nt", unshare=un), whead + ["-X", "importtime", sandbox, *run_args], nt_env),
                ("nt", build([], "nt", script=launch.EGRESS_PROBE), whead + [probe], nt_env),
                ("nt", build(run_args, "nt", venv_python=None, child_cmd=wstub), [*wstub, *run_args],
                 {**nt_env, "PATH": r"C:\py313;C:\Windows\System32"}),
            ]
            for n, (os_name, got, argv, env) in enumerate(cases):
                assert got.argv == argv, (n, got.argv)
                assert got.env == env, (n, got.env)
                assert got.cwd == str(tmp), (n, got.cwd)
                assert got.popen_kwargs == {**pipes, **group[os_name]}, (n, got.popen_kwargs)
            _refused(lambda: build(["--check-env"], "posix", unshare=None), "R-14")
            for bad in ({"child_cmd": ["python3"]}, {"child_cmd": []}, {}):
                try:
                    build(run_args, "posix", unshare=un, venv_python=None, **bad)
                except ValueError:
                    continue
                raise AssertionError(f"build_launch accepted venv_python=None with {bad}")
            shutil.which = lambda _name: None
            assert "not on PATH" in _refused(lambda: launch.resolve_unshare("posix"), "R-14").message
            shutil.which = lambda _name: un
            subprocess.run = lambda cmd, **_kw: subprocess.CompletedProcess(cmd, 1, "", "unshare: not permitted\n")
            assert "exited 1" in _refused(lambda: launch.resolve_unshare("posix"), "R-14").message
            assert launch.resolve_unshare("nt") is None
        finally:
            subprocess.Popen, subprocess.run, shutil.which = saved
        launch.assert_env_contract(posix_env, "posix")
        launch.assert_env_contract(nt_env, "nt")
        _invalid(lambda: launch.assert_env_contract({**posix_env, "PYTHONPATH": "/p"}, "posix"), "C-10")
        _invalid(lambda: launch.assert_env_contract({**nt_env, "FMP_API_KEY": "k"}, "nt"), "C-10")
        _invalid(lambda: launch.assert_env_contract({k: v for k, v in posix_env.items() if k != "LC_ALL"}, "posix"),
                 "C-10")
        _invalid(lambda: launch.assert_env_contract(posix_env, "nt"), "C-10")
    finally:
        left = launch.cleanup_tempdir(tmp)
    assert left == [] and not tmp.exists(), left


def test_l1_17_venv_reads_and_wheel_identity():
    """L1-17: venv reads on fake venv dirs (variable and ~ expansion, a control character, a relative path, a wrong
    file name, include-system-site-packages = true, a Windows venv on the parent's or the Store's interpreter, a
    python outside bin or Scripts, no pyvenv.cfg, two nautilus_trader dist-info dirs, a version, minor, tag or RECORD
    off its pin, requirements and env_pins.json apart: R-03); the committed RECORD fixtures give both identities.
    On POSIX the variable is $VAR, on Windows %VAR% (os.path.expandvars, spec 6.7)."""
    linux = require_fixture(LINUX_RECORD, manifest=FIXTURE_MANIFEST).read_text(encoding="utf-8")
    win = require_fixture(WIN_RECORD, manifest=FIXTURE_MANIFEST).read_text(encoding="utf-8")
    assert launch.record_identity(linux) == LINUX_IDENTITY and launch.record_identity(win) == WIN_IDENTITY
    noise = ("nautilus_trader/__pycache__/x.cpython-313.pyc,sha256=AAAA,1\n"
             "nautilus_trader-1.231.0.dist-info/INSTALLER,sha256=BBBB,4\n"
             "nautilus_trader-1.231.0.dist-info/REQUESTED,sha256=CCCC,0\n"
             "nautilus_trader-1.231.0.dist-info/direct_url.json,sha256=DDDD,9\n"
             "nautilus_trader-1.231.0.dist-info/RECORD,,\n"
             "nautilus_trader/unhashed.txt,,\n")
    assert launch.record_identity(linux + noise) == LINUX_IDENTITY
    assert launch.record_identity("\n".join(reversed(linux.splitlines())) + "\n") == LINUX_IDENTITY
    pins = launch.load_env_pins()
    with tempfile.TemporaryDirectory(prefix="qgnb_l117_") as name:
        tmp = Path(name)
        base = str(tmp / "other" / "python")
        lin = _fake_venv(tmp / "lin", os_name="posix", record=linux, tag="cp313-cp313-manylinux_2_35_x86_64")
        reads = launch.read_venv(lin, os_name="posix", parent_base_executable=base)
        assert reads["root"] == str(tmp / "lin") and launch.venv_root(lin) == tmp / "lin", reads["root"]
        assert reads["python_minor"] == "3.13" and reads["versions"] == EXPECTED_VERSIONS, reads
        assert reads["installed"] == EXPECTED_VERSIONS, reads["installed"]
        assert reads["pyvenv"]["include_system_site_packages"] is False and reads["pyvenv"]["version"] == "3.13.17"
        assert reads["wheel"] == {"wheel_tag": "cp313-cp313-manylinux_2_35_x86_64",
                                  "platform_tag": "manylinux_2_35_x86_64",
                                  "record_digest_sha256": LINUX_IDENTITY[0], "record_entries": 764}, reads["wheel"]
        assert launch.venv_mismatches(reads) == [] and launch.venv_mismatches(reads, pins) == []
        cfg_same = {"executable": base}                       # POSIX: a venv on the parent's own base is allowed
        same = _fake_venv(tmp / "same", os_name="posix", record=linux, tag="cp313-cp313-manylinux_2_35_x86_64",
                          cfg=cfg_same)
        launch.read_venv(same, os_name="posix", parent_base_executable=base)
        py313 = {"home": r"C:\qg\py313", "executable": r"C:\qg\py313\python.exe"}   # the dedicated base (4.4)
        wv = _fake_venv(tmp / "win", os_name="nt", record=win, tag="cp313-cp313-win_amd64", cfg=py313)
        wreads = launch.read_venv(wv, os_name="nt", parent_base_executable=base)
        assert wreads["wheel"]["platform_tag"] == "win_amd64" and launch.venv_mismatches(wreads) == [], wreads
        # off the pins: one "R-03: <field>: found <x>, expected <y>" per difference
        off = _fake_venv(tmp / "off", os_name="posix", record=linux, tag="cp313-cp313-manylinux_2_35_x86_64",
                         versions={"numpy": "2.3.4"}, cfg={"version": "3.12.9"})
        bad = launch.venv_mismatches(launch.read_venv(off, os_name="posix", parent_base_executable=base))
        assert "R-03: python_minor: found 3.12, expected 3.13" in bad, bad
        assert "R-03: numpy: found 2.3.4, expected 2.3.5" in bad and all(b.startswith("R-03: ") for b in bad), bad
        cut = "\n".join(linux.splitlines()[1:]) + "\n"
        rec = _fake_venv(tmp / "rec", os_name="posix", record=cut, tag="cp313-cp313-manylinux_2_35_x86_64")
        bad = launch.venv_mismatches(launch.read_venv(rec, os_name="posix", parent_base_executable=base))
        assert [b.split(":")[1].strip() for b in bad] == ["record_digest_sha256", "record_entries"], bad
        mac = _fake_venv(tmp / "mac", os_name="posix", record=linux, tag="cp313-cp313-macosx_14_0_arm64")
        bad = launch.venv_mismatches(launch.read_venv(mac, os_name="posix", parent_base_executable=base))
        assert len(bad) == 1 and bad[0].startswith("R-03: platform_tag: found macosx_14_0_arm64"), bad
        want = {**EXPECTED_VERSIONS, "numpy": "2.3.6"}         # requirements-nautilus.txt and env_pins.json apart
        assert launch.venv_mismatches(reads, pins, want) == ["R-03: numpy: found 2.3.5, expected 2.3.6"]
        skew = {**reads, "versions": {**reads["versions"], "numpy": "2.3.4"}}
        assert launch.venv_mismatches(skew, pins, want) == ["R-03: numpy: found 2.3.4, expected 2.3.6",
                                                            "R-03: numpy (env_pins.json): found 2.3.4, expected 2.3.5"]
        # layout and pyvenv.cfg refusals
        exc = _refused(lambda: launch.read_venv(tmp / "lin" / "x" / "python", os_name="posix",
                                                parent_base_executable=base), "R-03")
        assert "not in Scripts or bin" in exc.message, exc
        nocfg = _fake_venv(tmp / "nocfg", os_name="posix", record=linux, tag="cp313-cp313-manylinux_2_35_x86_64")
        (tmp / "nocfg" / "pyvenv.cfg").unlink()
        exc = _refused(lambda: launch.read_venv(nocfg, os_name="posix", parent_base_executable=base), "R-03")
        assert "no pyvenv.cfg" in exc.message, exc
        two = _fake_venv(tmp / "two", os_name="posix", record=linux, tag="cp313-cp313-manylinux_2_35_x86_64")
        (tmp / "two" / "lib" / "python3.13" / "site-packages" / "nautilus_trader-9.dist-info").mkdir()
        exc = _refused(lambda: launch.read_venv(two, os_name="posix", parent_base_executable=base), "R-03")
        assert "2 nautilus_trader dist-info dirs" in exc.message, exc
        sys_site = _fake_venv(tmp / "sys", os_name="posix", record=linux, tag="cp313-cp313-manylinux_2_35_x86_64",
                              cfg={"include-system-site-packages": "true"})
        _refused(lambda: launch.read_venv(sys_site, os_name="posix", parent_base_executable=base), "R-03")
        own = _fake_venv(tmp / "own", os_name="nt", record=win, tag="cp313-cp313-win_amd64", cfg={"executable": base})
        _refused(lambda: launch.read_venv(own, os_name="nt", parent_base_executable=base), "R-03")
        store = r"C:\Users\o\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0"
        home = _fake_venv(tmp / "store", os_name="nt", record=win, tag="cp313-cp313-win_amd64",
                          cfg={**py313, "home": store})
        exc = _refused(lambda: launch.read_venv(home, os_name="nt", parent_base_executable=base), "R-03")
        assert "Microsoft Store" in exc.message, exc
        pkg = r"C:\Users\o\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\python.exe"
        exe = _fake_venv(tmp / "pkg", os_name="nt", record=win, tag="cp313-cp313-win_amd64",
                         cfg={**py313, "executable": pkg})
        _refused(lambda: launch.read_venv(exe, os_name="nt", parent_base_executable=base), "R-03")
        # the key's value (6.7): expansion, then control characters, absolute path, file name, existence
        host = _fake_venv(tmp / "host", os_name=os.name, record=linux, tag="cp313-cp313-manylinux_2_35_x86_64")
        rel = host.relative_to(tmp).as_posix()
        token = "%QGNB_L117%" if os.name == "nt" else "$QGNB_L117"
        home_key = "USERPROFILE" if os.name == "nt" else "HOME"
        saved = {k: os.environ.get(k) for k in ("QGNB_L117", home_key)}
        os.environ["QGNB_L117"], os.environ[home_key] = str(tmp), str(tmp)
        try:
            assert launch.resolve_venv_python(f"{token}/{rel}") == host
            assert launch.resolve_venv_python(f"~/{rel}") == host
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        for value in (str(host) + "\n", str(host) + "\x7f", f"\t{host}"):
            exc = _refused(lambda: launch.resolve_venv_python(value), "R-03")
            assert repr(value) in exc.message and exc.remedy, exc
        (host.parent / "python3").write_bytes(b"")
        for value in (rel, str(host.parent / "python3"), str(tmp / "nowhere" / host.name)):
            exc = _refused(lambda: launch.resolve_venv_python(value), "R-03")
            assert repr(value) in exc.message and exc.remedy, exc


def test_l1_22_global_interpreter_has_no_nautilus():
    """L1-22: the global interpreter has no nautilus-trader distribution and cannot import nautilus_trader (FAIL, with
    R-03's three remedy lines; OPS-R3-1); pyarrow there is reported, never failed (OPS-5)."""
    found = launch.parent_nautilus()
    importable = importlib.util.find_spec("nautilus_trader") is not None
    assert found is None and not importable, (
        f"R-03: nautilus-trader in the global interpreter (distribution {found!r}, importable {importable}); run "
        f"exactly these three lines, and the last must print 2.3.5 2.3.3 1.18.0:\n{launch.PARENT_NAUTILUS_REMEDY}")
    lines = launch.PARENT_NAUTILUS_REMEDY.splitlines()
    assert lines == ["python -m pip uninstall -y nautilus-trader", "python -m pip check",
                     'python -c "import numpy, pandas, scipy; print(numpy.__version__, pandas.__version__, '
                     'scipy.__version__)"'], lines
    print(f"  pyarrow in the global interpreter: {launch.parent_pyarrow()}")


def test_l1_32_every_test_guarded_and_ledgers_unchanged():
    """L1-32: the guard of 3.3 wraps every test, this test runs last, the guarded files equal the digests taken when
    the suite started, QUANTGEN_MACRO_DIR is a fresh temp dir inside each test, and a write under a guarded root is
    a FAIL that names the file, also when the test then raises NotRun (QA-1, QA-R2-13)."""
    global _ROOTS
    import config
    entries = tests()
    names = [n for n, _ in entries]
    assert names[-1] == LAST_TEST and names[:-1] == sorted(names[:-1]) and len(set(names)) == len(names), names
    assert all(getattr(f, "nautilus_guarded", False) for _, f in entries), names
    mine = os.environ.get("QUANTGEN_MACRO_DIR", "")
    assert Path(mine).name.startswith("qgnb_macro_") and Path(mine).is_dir() and config.macro_dir() == Path(mine), mine
    assert not any(str(r).startswith(mine) for r in guard_roots()), guard_roots()
    seen: list[str] = []
    saved_roots = _ROOTS
    with tempfile.TemporaryDirectory(prefix="qgnb_l132_") as name:
        root = Path(name)
        (root / "E1.jsonl").write_text("{}\n", encoding="utf-8", newline="\n")

        def appends():
            with (root / "E1.jsonl").open("a", encoding="utf-8", newline="\n") as fh:
                fh.write("{}\n")
        _ROOTS = (root,)
        try:
            for _ in range(2):
                guarded("probe_reads", lambda: seen.append(os.environ["QUANTGEN_MACRO_DIR"]))()
            try:
                guarded("probe_appends", appends)()
            except AssertionError as exc:
                assert str(root / "E1.jsonl") in str(exc), exc
            else:
                raise AssertionError("a ledger append inside a guarded test passed")

            def appends_then_not_run():
                appends()
                raise NotRun("OWNER: probe")
            try:
                guarded("probe_appends_not_run", appends_then_not_run)()
            except AssertionError as exc:
                assert str(root / "E1.jsonl") in str(exc) and isinstance(exc.__context__, NotRun), exc
            except NotRun:
                raise AssertionError("a ledger append followed by NotRun passed as NOT_RUN") from None
        finally:
            _ROOTS = saved_roots
    assert len(set(seen)) == 2 and mine not in seen and not any(Path(s).exists() for s in seen), seen
    assert os.environ.get("QUANTGEN_MACRO_DIR") == mine
    assert _SUITE_START is not None
    now = digest_roots(guard_roots())
    changed = sorted(k for k in _SUITE_START.keys() | now.keys() if _SUITE_START.get(k) != now.get(k))
    assert not changed, f"guarded files changed since the suite started: {changed}"


def test_px_requirements_nautilus_pins_and_header():
    """Spec 5.1 and 3.4: requirements-nautilus.txt is the header verbatim, then the hashed closure body verbatim (16
    distributions with == pins and --hash lines; PyPI's nautilus-trader hashes); it is the single source of the
    version pins; QUANTGEN's own dependency files never name nautilus or pyarrow."""
    raw = (ROOT / "requirements-nautilus.txt").read_bytes()
    assert raw.isascii() and b"\r" not in raw and raw.endswith(b"\n"), "ASCII, LF line ends, a final newline"
    lines = raw.decode("ascii").splitlines()
    assert tuple(lines[:6]) == REQ_HEADER, lines[:6]
    body = "\n".join(lines[6:]) + "\n"
    assert hashlib.sha256(body.encode("ascii")).hexdigest() == REQ_BODY_SHA256, "body differs from the closure body"
    pins: dict[str, tuple[str, str, list[str]]] = {}
    current = None
    for line in lines[6:]:
        if line.startswith("    --hash=sha256:"):
            digest = line.split(":", 1)[1].rstrip(" \\")
            assert len(digest) == 64 and digest == digest.lower() and int(digest, 16) >= 0, line
            pins[current][2].append(digest)
            continue
        spec, _, marker = line.rstrip(" \\").partition(" ; ")
        current, _, version = spec.partition("==")
        pins[current] = (version, marker, [])
    assert {k: (v, m, len(h)) for k, (v, m, h) in pins.items()} == REQ_PINS, pins
    assert set(pins["nautilus-trader"][2]) == NAUTILUS_HASHES
    assert launch.REQUIREMENTS == ROOT / "requirements-nautilus.txt"
    assert launch.expected_versions() == EXPECTED_VERSIONS
    for name in ("requirements.txt", "requirements-dev.txt", "pyproject.toml"):
        text = (ROOT / name).read_text(encoding="utf-8").lower()
        assert "nautilus" not in text and "pyarrow" not in text, name


def test_px_env_example_and_env_pins():
    """Spec 3.4: .env.example gains the heading and the single-quoted, forward-slash line, which python-dotenv reads
    as written (double quotes would turn the \\n of \\ntvenv into a newline); spec 6.7 and C7: env_pins.json holds
    both platforms' pins in the bridge's JSON bytes."""
    raw = (ROOT / ".env.example").read_bytes()
    assert b"\r" not in raw, ".env.example must stay LF"
    lines = raw.decode("utf-8").splitlines()
    assert lines.count(ENV_LINE) == 1 and lines.count(ENV_HEADING) == 1, "heading or line missing or repeated"
    block = lines[lines.index(ENV_HEADING):lines.index(ENV_LINE) + 1]
    assert block and not any("%" in s for s in block), block                # no %VAR% (OPS-4)
    from dotenv import dotenv_values
    value = dotenv_values(ROOT / ".env.example")["QUANTGEN_NAUTILUS_PYTHON"]
    assert value == "C:/Users/<you>/AppData/Local/quantgen/ntvenv/Scripts/python.exe", repr(value)
    quoted = dotenv_values(stream=io.StringIO('K="C:\\Users\\o\\ntvenv\\Scripts\\python.exe"\n'))["K"]
    assert "\n" in quoted, repr(quoted)                        # the hazard the single quotes avoid
    pins_bytes = launch.ENV_PINS.read_bytes()
    assert pins_bytes == (json.dumps(PINS_JSON, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    assert launch.load_env_pins() == PINS_JSON
    for plat in PINS_JSON["platforms"].values():
        assert {k.replace("_", "-"): v for k, v in plat["versions"].items()} == launch.expected_versions()


def test_px_egress_probe_imports_json_and_socket_only():
    """Spec 4.4 and C4: the probe imports json and socket only, makes one create_connection to ("1.1.1.1", 443) with
    timeout 3, and reports a refused connect as blocked and an accepted one as not blocked (loopback only)."""
    tree = ast.parse(launch.EGRESS_PROBE.read_text(encoding="utf-8"))
    imports = sorted(a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names)
    froms = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    assert imports == ["json", "socket"] and froms == [], (imports, froms)
    calls = [n for n in ast.walk(tree)
             if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "create_connection"]
    assert len(calls) == 1, len(calls)
    spec = importlib.util.spec_from_file_location("qgnb_egress_probe", launch.EGRESS_PROBE)
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    params = inspect.signature(probe.probe).parameters
    assert [(p.name, p.default) for p in params.values()] == [("host", "1.1.1.1"), ("port", 443), ("timeout", 3)]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        port = server.getsockname()[1]
        assert probe.probe("127.0.0.1", port, 3) == {"blocked": False, "errno": None, "error": ""}
    out = probe.probe("127.0.0.1", port, 10)                  # the listener is closed: refused (or timed out)
    assert out["blocked"] is True and out["error"] and (out["errno"] is None or isinstance(out["errno"], int)), out


def test_px_census_parser_reads_importtime_lines():
    """Spec 5.2.7: parse_census keeps the third `|` field of every `import time:` line, skips the header, sorts and
    de-duplicates the names, and returns the rest of stderr unchanged; a real -X importtime run parses too."""
    stderr = ("import time: self [us] | cumulative | imported package\n"
              "import time:       101 |        101 |   _io\n"
              "import time:        55 |        300 |     nautilus_trader.core\n"
              "Traceback (most recent call last):\n"
              "import time:        10 |         10 |       plotly\n"
              "import time:         7 |          7 |   _io\n"
              "ValueError: boom\n")
    assert launch.parse_census(stderr) == (["_io", "nautilus_trader.core", "plotly"],
                                           "Traceback (most recent call last):\nValueError: boom\n")
    assert launch.parse_census("") == ([], "")
    real = subprocess.run([sys.executable, "-I", "-X", "importtime", "-c", "import json"], capture_output=True,
                          encoding="utf-8", errors="replace", timeout=60)
    names, rest = launch.parse_census(real.stderr)
    assert real.returncode == 0 and "json" in names and "json.decoder" in names and rest == "", (names[:5], rest)


# --------------------------------------------------------------------------- #
# Plan Task 1 (spec Step 3): layer 2
# --------------------------------------------------------------------------- #
def test_l2_01_check_env_pins_identity_precision():
    """L2-1: the parent's venv reads match the pins and the wheel identity; --check-env, launched through the launch
    contract, prints one JSON line with the venv's Python, the platform's precision and environment BACKTEST."""
    python = layer2()
    reads = launch.read_venv(python)
    tag = reads["wheel"]["platform_tag"]
    pin = launch.load_env_pins()["platforms"][tag]
    assert (reads["wheel"]["record_digest_sha256"], reads["wheel"]["record_entries"]) == (
        pin["record_digest_sha256"], pin["record_entries"]), reads["wheel"]
    result = _launch_venv(python, ["--check-env"])
    assert result.returncode == 0 and not result.timed_out, (result.returncode, result.stderr_tail)
    lines = result.stdout.splitlines()
    assert len(lines) == 1, result.stdout_tail
    out = json.loads(lines[0])
    assert set(out) == {"schema", "python", "system", "machine", "environment", "precision"}, out
    assert out["schema"] == "nautilus-bridge-check-env/1" and out["environment"] == "BACKTEST", out
    assert out["python"] == reads["pyvenv"]["version"] and out["python"].startswith("3.13."), out
    assert out["system"] == SYSTEM[tag] and out["precision"] == PRECISION[tag], out
    assert result.census == [], result.census[:5]


def test_l2_08_guard_selftest_outcomes():
    """L2-8 (C-2): --guard-selftest exits 0; SANDBOX, LIVE and LiveClock() raised; BACKTEST and TestClock() passed."""
    python = layer2()
    result = _launch_venv(python, ["--guard-selftest"])
    assert result.returncode == 0, (result.returncode, result.stdout_tail, result.stderr_tail)
    assert result.stdout.strip() == json.dumps(SELFTEST, sort_keys=True), result.stdout


def test_l2_09_egress_probe_blocked():
    """L2-9 (SECURITY-1): the egress probe, launched in the venv through the launch contract, reports blocked."""
    python = layer2()
    result = _launch_venv(python, [], script=launch.EGRESS_PROBE, timeout=60)
    out = json.loads(result.stdout.strip())
    assert result.returncode == 0 and out["blocked"] is True, (result.returncode, out, result.stderr_tail)
    assert set(out) == {"blocked", "errno", "error"} and out["error"], out


def test_l2_10_timeout_kills_the_child_tree():
    """L2-10 (OPS-1): a venv child that sleeps 120 s, with a sleeping grandchild, launched with timeout 3, returns
    within 15 s; the whole tree is gone (Linux: /proc; Windows: the temp dir, its cwd, can be deleted)."""
    python = layer2()
    code = ("import os, subprocess, sys, time; "
            "g = subprocess.Popen([sys.executable, '-I', '-c', 'import time; time.sleep(120)']); "
            "open('pids.txt', 'w', encoding='utf-8').write(f'{os.getpid()} {g.pid}'); time.sleep(120)")
    tmp = launch.make_tempdir()
    try:
        child = launch.build_launch([], tempdir=tmp, venv_python=None, unshare=launch.resolve_unshare(),
                                    child_cmd=[str(python), "-I", "-c", code])
        started = time.monotonic()
        result = launch.run_child(child, timeout=3)
        took = time.monotonic() - started
        pids = [int(p) for p in (tmp / "pids.txt").read_text(encoding="utf-8").split()]
    finally:
        left = launch.cleanup_tempdir(tmp)
    assert result.timed_out and result.returncode is not None and took < 15, (result.timed_out, result.returncode,
                                                                              took)
    assert left == [], left
    assert len(pids) == 2, pids
    if os.name != "nt" and Path("/proc").is_dir():
        assert all(_gone(p) for p in pids), pids


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    """Runs the tests() entries whose name contains any -k substring (all without -k); prints only."""
    for stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(Exception):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(prog="python3 -B -m tests.nautilus_acceptance")
    parser.add_argument("-k", dest="patterns", action="append", default=[],
                        help="run only the tests whose name contains this substring (repeatable)")
    args = parser.parse_args(argv)
    entries = [(n, f) for n, f in tests() if not args.patterns or any(p in n for p in args.patterns)]
    counts = {"PASS": 0, "FAIL": 0, "NOT_RUN": 0}
    for name, fn in entries:
        status, detail = "PASS", ""
        try:
            fn()
        except NotRun as exc:
            status, detail = "NOT_RUN", exc.reason
        except Exception as exc:                                        # noqa: BLE001
            status, detail = "FAIL", f"{type(exc).__name__}: {exc}"
            traceback.print_exc()
        counts[status] += 1
        print(f"{status} {name} {detail}".rstrip(), flush=True)
    print(f"\n{counts['PASS']}/{len(entries)} passed, {counts['FAIL']} failed, {counts['NOT_RUN']} not run")
    return 0 if entries and not counts["FAIL"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
