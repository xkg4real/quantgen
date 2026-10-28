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
# Plan Task 3 (spec Step 5): the sandbox and fixture_inputs
# --------------------------------------------------------------------------- #
EMPTY_LEDGER_HASH = "d751713988987e9331980363e24189ce"      # gate_ledger.ledger_hash([]): the md5 of "[]" (6.1)
INPUT_KEYS = frozenset({"schema", "strategy", "params", "instrument", "capital_usd", "cost_bps", "stress",
                        "fill_seed", "price_precision", "size_precision", "volume", "n_bars", "bars_sha256",
                        "ledger_hash_after_registration"})                            # C5: exactly these 14
F1_DATES = ("2001-01-02", "2001-01-03", "2001-01-04", "2001-01-05", "2001-01-08", "2001-01-09", "2001-01-10",
            "2001-01-11", "2001-01-12", "2001-01-15", "2001-01-16", "2001-01-17")   # weekdays; bars 21:00 UTC
F2_DATES = tuple(f"2021-01-{d:02d}" for d in range(1, 12))                          # bars 00:00 UTC next day
F1_PRICES = (97, 98, 99, 100, 104, 96, 95, 99, 101, 103, 98, 97)
F2_PRICES = (50000, 51000, 52000, 53000, 52600, 50000, 49000, 50500, 52000, 51000, 50800)
F1_INPUT = {"schema": "nautilus-bridge-input/2", "strategy": "trend_switch",
            "params": {"rule": "sma", "lookback": 3, "step": 2}, "instrument": "SPY", "capital_usd": "1005001",
            "cost_bps": "50", "stress": "1", "fill_seed": 42, "price_precision": 9, "size_precision": 0,
            "volume": "1000000000", "n_bars": 12,
            "bars_sha256": "29844d2fd9185e1d303a1f56f981ccac3bb8f840e0064a8c920f0ef2bffaf93c",
            "ledger_hash_after_registration": EMPTY_LEDGER_HASH}
F2_INPUT = {"schema": "nautilus-bridge-input/2", "strategy": "crypto_trend",
            "params": {"hysteresis": 0.2, "lookbacks": [1, 2], "mas": [2, 3]}, "instrument": "BTC/USD",
            "capital_usd": "53053", "cost_bps": "10", "stress": "1", "fill_seed": 42, "price_precision": 9,
            "size_precision": 8, "volume": "1000000000", "n_bars": 11,
            "bars_sha256": "44b665f8590413aaaea02f2faa5f50e304c5432d7b84e5972aec8183b562bb25",
            "ledger_hash_after_registration": EMPTY_LEDGER_HASH}
N1_BARS_SHA256 = "a9e3bf5523d4536c93ae8431b7599fd5a83d70abe7e62bb4ecf224b73671ef39"
SANDBOX_IMPORTS = """import argparse
import csv
import hashlib
import json
import math
import platform
from decimal import ROUND_FLOOR, Decimal
from pathlib import Path
from sys import argv, exit
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.models import FeeModel, FillModel
from nautilus_trader.common import Environment
from nautilus_trader.common.component import LiveClock, TestClock, is_backtest_force_stop
from nautilus_trader.config import BacktestEngineConfig, LoggingConfig, StrategyConfig
from nautilus_trader.model.currencies import BTC, USD
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import AccountType, OmsType, OrderSide, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId, Symbol, TraderId, Venue
from nautilus_trader.model.instruments import CurrencyPair, Equity
from nautilus_trader.model.objects import (FIXED_PRECISION, HIGH_PRECISION, PRICE_MAX, QUANTITY_MAX, Money, Price,
                                           Quantity)
from nautilus_trader.trading.strategy import Strategy
"""                                                                                  # spec 5.2.9, verbatim
SANDBOX_DEFS = ("Refused", "inside", "plain_mean", "require_backtest_environment", "require_backtest_clock",
                "make_fee_model", "build_engine", "PortConfig", "TrendSwitchConfig", "CryptoTrendConfig", "Port",
                "TrendSwitchPort", "CryptoTrendPort", "run", "check_env", "guard_selftest", "main")   # 5.2.9's order
ORDER_CALL = "submit" + "_order"          # the one exempt call, spelled so this file holds no T-RO-01 token (3.11)
PORT_METHODS = {"on_start", "on_bar", "place", "on_order_filled", "on_order_denied", "on_order_rejected"}
EXCLUDED_TEXT = ("AT_THE_CLOSE", "LatencyModel", "latency_model", "PortfolioAnalyzer", "analyzer", "report",
                 "MARGIN", "BacktestNode", "ParquetDataCatalog", "catalog", "streaming", "log_level_file",
                 "modify_order", "cancel_order", "close_position", "market_exit")   # and ORDER_CALL + "_list"
VENUE_KEYWORDS = {"oms_type": "OmsType.NETTING", "account_type": "AccountType.CASH", "bar_execution": "True",
                  "bar_adaptive_high_low_ordering": "False", "allow_cash_borrowing": "False"}   # spec 5.2.3
OUTPUTS = ["decisions.csv", "fills.csv", "manifest.json", "onbar_equity.csv"]       # spec 5.2.6
MANIFEST_KEYS = {"schema", "read_only", "mode", "python", "system", "machine", "precision", "environment",
                 "strategy_started", "input", "engine", "result", "hashes", "valid", "invalid_reasons"}   # C6
MANIFEST_RESULT_KEYS = {"bars_seen", "iterations", "backtest_end", "force_stop", "orders_total", "orders_filled",
                        "denied", "rejected", "orders_not_filled", "account_balance_usd", "final_qty",
                        "stats_pnls_empty"}
MANIFEST_ENGINE = {"run_analysis": False, "log_level": "ERROR", "log_colors": False, "account_type": "CASH",
                   "oms_type": "NETTING", "allow_cash_borrowing": False, "bar_execution": True, "fill_seed": 42}
FILLS_HEADER = "ts_event,order_side,last_qty,last_px,commission,commission_ccy,trade_id,venue_order_id"
F_TABLES = {   # spec 8.2: per fill (bar, side, last_qty, last_px at 9 decimals, commission); decisions (bar, action)
    "F1": {"fills": [(3, "BUY", "10000", "100.000000000", "5000.00"), (5, "SELL", "10000", "96.000000000", "4800.00"),
                     (7, "BUY", "9600", "99.000000000", "4752.00"), (11, "SELL", "9600", "97.000000000", "4656.00")],
           "decisions": [(3, "buy"), (5, "sell"), (7, "buy"), (9, "hold"), (11, "sell")],
           "balance": "926593.00"},
    "F2": {"fills": [(3, "BUY", "1.00000000", "53000.000000000", "53.00"),
                     (5, "SELL", "1.00000000", "50000.000000000", "50.00"),
                     (7, "BUY", "0.98812079", "50500.000000000", "49.90"),
                     (9, "SELL", "0.98812079", "51000.000000000", "50.39")],
           "decisions": [(3, "buy"), (4, "hold"), (5, "sell"), (6, "hold"), (7, "buy"), (8, "hold"), (9, "sell"),
                         (10, "hold")],
           "balance": "50343.77"},
}


def _bar_ns(day: str, crypto: bool) -> int:
    """8.2's bar time, computed with datetime (launch uses integer day arithmetic): 21:00 UTC on the date, or 00:00
    UTC on the next calendar day for the crypto fixture."""
    from datetime import date, datetime, timedelta, timezone
    d = date.fromisoformat(day) + timedelta(days=1 if crypto else 0)
    return int(datetime(d.year, d.month, d.day, 0 if crypto else 21, tzinfo=timezone.utc).timestamp()) * 10**9


def _canonical(obj: dict) -> bytes:
    """C1's input.json bytes."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sandbox_run(python: Path, raw: bytes, bars: bytes, *, prepare: Callable[[Path], None] | None = None,
                 in_arg: Callable[[Path], str] = str) -> tuple[launch.ChildResult, dict[str, bytes]]:
    """`sandbox.py run --in <in_arg(temp dir)>` through the launch contract, with these input.json and bars.csv
    bytes; `prepare(tmp)` may change the temp dir first. Returns the ChildResult and the bytes of every file the
    child left in the temp dir (input.json and bars.csv excluded); the temp dir is removed."""
    tmp = launch.make_tempdir()
    try:
        (tmp / "input.json").write_bytes(raw)
        (tmp / "bars.csv").write_bytes(bars)
        if prepare is not None:
            prepare(tmp)
        child = launch.build_launch(["run", "--in", in_arg(tmp)], tempdir=tmp, venv_python=python,
                                    unshare=launch.resolve_unshare())
        result = launch.run_child(child)
        out = {p.name: p.read_bytes() for p in sorted(tmp.iterdir())
               if p.is_file() and not p.is_symlink() and p.name not in ("input.json", "bars.csv")}
    finally:
        left = launch.cleanup_tempdir(tmp)
    assert left == [], left
    return result, out


def _positive_control(python: Path, name: str) -> dict[str, bytes]:
    """The unperturbed fixture runs: exit 0 and the four output files of 5.2.6."""
    raw, bars = launch.fixture_inputs(name)
    result, out = _sandbox_run(python, raw, bars)
    assert result.returncode == 0 and sorted(out) == OUTPUTS, (
        f"positive control {name}: exit {result.returncode}, files {sorted(out)}, stderr {result.stderr_tail[-300:]!r}")
    return out


def _refused_before_engine(label: str, reason: str, result: launch.ChildResult, out: dict[str, bytes]) -> None:
    """C-05 (section 7): exit 20, no file written, and the last stderr line "C-05: <reason>"."""
    last = (result.stderr_tail.strip().splitlines() or [""])[-1]
    assert (result.returncode, out, last) == (20, {}, f"C-05: {reason}"), (
        f"{label}: exit {result.returncode}, files {sorted(out)}, stderr {result.stderr_tail[-300:]!r}")


def _check_env_precision(python: Path) -> dict:
    """The precision block that `sandbox.py --check-env` prints, read at run time (QA-14)."""
    tmp = launch.make_tempdir()
    try:
        result = launch.run_child(launch.build_launch(["--check-env"], tempdir=tmp, venv_python=python,
                                                      unshare=launch.resolve_unshare()))
    finally:
        left = launch.cleanup_tempdir(tmp)
    assert result.returncode == 0 and left == [], (result.returncode, left, result.stderr_tail[-300:])
    return json.loads(result.stdout)["precision"]


def _check_run(name: str, raw: bytes, bars: bytes, result: launch.ChildResult, out: dict[str, bytes]) -> dict:
    """A valid run of fixture F1 or F2: exit 0; C6's manifest with every echo and hash; 8.2's fills and decisions."""
    table = F_TABLES[name]
    assert result.returncode == 0 and not result.timed_out and sorted(out) == OUTPUTS, (
        f"{name}: exit {result.returncode}, files {sorted(out)}, stderr {result.stderr_tail[-300:]!r}")
    assert out["manifest.json"].endswith(b"}\n") and all(b"\r" not in v for v in out.values()), name
    m = json.loads(out["manifest.json"])
    inp = json.loads(raw)
    ts = [int(line.split(",")[1]) for line in bars.decode("utf-8").splitlines()[1:]]
    assert set(m) == MANIFEST_KEYS and set(m["result"]) == MANIFEST_RESULT_KEYS, sorted(m)
    assert (m["schema"], m["read_only"], m["mode"], m["environment"]) == (
        "nautilus-bridge-manifest/2", True, "run", "BACKTEST"), m
    assert m["engine"] == MANIFEST_ENGINE and m["strategy_started"] is True, m["engine"]
    assert m["input"] == {"input_json_sha256": hashlib.sha256(raw).hexdigest(), "bars_sha256": inp["bars_sha256"],
                          "bars_fed": len(ts), "first_ts": ts[0], "last_ts": ts[-1], "cost_bps": inp["cost_bps"],
                          "stress": inp["stress"],
                          "ledger_hash_after_registration": inp["ledger_hash_after_registration"]}, m["input"]
    assert m["hashes"] == {f: hashlib.sha256(out[f]).hexdigest() for f in OUTPUTS if f != "manifest.json"}
    r = m["result"]
    assert (m["valid"], m["invalid_reasons"], r["bars_seen"], r["backtest_end"], r["force_stop"]) == (
        True, [], len(ts), ts[-1], False), (m["invalid_reasons"], r)
    assert (r["orders_total"], r["orders_filled"], r["denied"], r["rejected"], r["orders_not_filled"]) == (
        4, 4, 0, 0, []), r
    assert (r["account_balance_usd"], r["final_qty"], r["stats_pnls_empty"]) == (table["balance"], "0", True), r
    fills = out["fills.csv"].decode("utf-8").splitlines()
    assert fills[0] == FILLS_HEADER, fills[0]
    got = [(ts.index(int(f[0])), f[1], f[2], f[3], f[4], f[5]) for f in (row.split(",") for row in fills[1:])]
    assert got == [(*row, "USD") for row in table["fills"]], got
    decisions = out["decisions.csv"].decode("utf-8").splitlines()
    assert decisions[0] == "i,ts_event,decision,margin,action", decisions[0]
    got = [(int(d[0]), d[4]) for d in (row.split(",") for row in decisions[1:])]
    assert got == table["decisions"], got
    equity = out["onbar_equity.csv"].decode("utf-8").splitlines()
    assert equity[0] == "i,ts_event,close,cash,qty,equity_pre" and len(equity) - 1 == len(ts), equity[:2]
    return m


def _link(name: str, target: Callable[[Path], Path]) -> Callable[[Path], None]:
    """prepare(tmp): replace tmp/name by a symbolic link to target(tmp); WinError 1314 is a NotRun (OPS-R2-5)."""
    def prepare(tmp: Path) -> None:
        path, to = tmp / name, target(tmp)
        if path.exists():
            path.unlink()
        try:
            os.symlink(to, path, target_is_directory=to.is_dir())
        except OSError as exc:
            if getattr(exc, "winerror", None) == 1314:
                raise NotRun("OWNER: enable Developer Mode, or accept this NotRun") from exc
            raise
    return prepare


def _put(key: str, value) -> Callable[[dict], None]:
    def change(inp: dict) -> None:
        inp[key] = value
    return change


def _put_param(key: str, value) -> Callable[[dict], None]:
    def change(inp: dict) -> None:
        inp["params"][key] = value
    return change


def _drop(key: str) -> Callable[[dict], None]:
    def change(inp: dict) -> None:
        del inp[key]
    return change


def _swap_ts(text: str) -> str:
    """bars.csv with the timestamps of rows 3 and 4 swapped."""
    lines = text.split("\n")
    a, b = lines[4].split(","), lines[5].split(",")
    a[1], b[1] = b[1], a[1]
    lines[4], lines[5] = ",".join(a), ",".join(b)
    return "\n".join(lines)


def _repeat_ts(text: str) -> str:
    """bars.csv whose row 4 repeats row 3's timestamp."""
    lines = text.split("\n")
    a, b = lines[4].split(","), lines[5].split(",")
    b[1] = a[1]
    lines[5] = ",".join(b)
    return "\n".join(lines)


def _l2_05a_cases(precision: dict) -> list[tuple[str, str, str, Callable[[dict], None] | None,
                                                 Callable[[str], str] | None]]:
    """(rule, label, base fixture, change to input.json, change to bars.csv): one single-field perturbation per rule
    of spec 6.1 (QA-R3-4), each refused by its own rule; the maxima come from --check-env (QA-14). A bars.csv change
    re-hashes bars_sha256, so only the rule named fails."""
    qmax, pmax, fp = int(precision["QUANTITY_MAX"]), int(precision["PRICE_MAX"]), precision["FIXED_PRECISION"]
    field = "unknown or missing field"
    cases = [(field, "unknown field", "F1", _put("extra", 1), None)]
    cases += [(field, f"missing {k}", "F1", _drop(k), None) for k in sorted(INPUT_KEYS)]
    cases += [(rule, label, "F1", change, None) for rule, label, change in (
        ("schema", "schema /1", _put("schema", "nautilus-bridge-input/1")),
        ("strategy", "strategy pairs", _put("strategy", "pairs")),
        ("params fields", "trend params under crypto_trend", _put("strategy", "crypto_trend")),
        ("params is not an object", "params a list", _put("params", [])),
        ("params fields", "params extra key", _put_param("x", 1)),
        ("params.rule", "params.rule ema", _put_param("rule", "ema")),
        ("params.lookback or params.step", "lookback 0", _put_param("lookback", 0)),
        ("params.lookback or params.step", "lookback 5001", _put_param("lookback", 5001)),
        ("params.lookback or params.step", "lookback a string", _put_param("lookback", "3")),
        ("params.lookback or params.step", "lookback a bool", _put_param("lookback", True)),
        ("params.lookback or params.step", "step 0", _put_param("step", 0)),
        ("params.lookback or params.step", "step 5001", _put_param("step", 5001)),
        ("instrument", "instrument QQQ", _put("instrument", "QQQ")),
        ("capital_usd", "capital 0", _put("capital_usd", "0")),
        ("capital_usd", "capital PRICE_MAX + 1", _put("capital_usd", str(pmax + 1))),
        ("capital_usd", "capital an int", _put("capital_usd", 1005001)),
        ("capital_usd", "capital leading zero", _put("capital_usd", "01005001")),
        ("capital_usd", "capital 4301 digits", _put("capital_usd", "1" * 4301)),
        ("cost_bps", "cost_bps -1", _put("cost_bps", "-1")),
        ("cost_bps", "cost_bps 1000.5", _put("cost_bps", "1000.5")),
        ("cost_bps", "cost_bps a float", _put("cost_bps", 50.0)),
        ("cost_bps", "cost_bps NaN", _put("cost_bps", "NaN")),
        ("cost_bps", "cost_bps empty", _put("cost_bps", "")),
        ("stress", "stress 0", _put("stress", "0")),
        ("stress", "stress 3", _put("stress", "3")),
        ("stress", "stress an int", _put("stress", 1)),
        ("fill_seed", "fill_seed -1", _put("fill_seed", -1)),
        ("fill_seed", "fill_seed 2**32", _put("fill_seed", 2**32)),
        ("fill_seed", "fill_seed a float", _put("fill_seed", 42.0)),
        ("price_precision", "price_precision -1", _put("price_precision", -1)),
        ("price_precision", "price_precision FIXED_PRECISION + 1", _put("price_precision", fp + 1)),
        ("size_precision", "size_precision -1", _put("size_precision", -1)),
        ("size_precision", "size_precision FIXED_PRECISION + 1", _put("size_precision", fp + 1)),
        ("size_precision", "SPY size_precision 8", _put("size_precision", 8)),
        ("volume", "volume 0", _put("volume", "0")),
        ("volume", "volume QUANTITY_MAX + 1", _put("volume", str(qmax + 1))),
        ("volume", "volume an int", _put("volume", 1000000000)),
        ("n_bars", "n_bars 0", _put("n_bars", 0)),
        ("n_bars", "n_bars 100001", _put("n_bars", 100001)),
        ("n_bars differs from bars.csv", "n_bars 11", _put("n_bars", 11)),
        ("bars_sha256 differs from bars.csv", "bars_sha256 doctored", _put("bars_sha256", "0" * 64)),
        ("bars_sha256 format", "bars_sha256 upper case", _put("bars_sha256", F1_INPUT["bars_sha256"].upper())),
        ("bars_sha256 format", "bars_sha256 63 hex", _put("bars_sha256", F1_INPUT["bars_sha256"][:63])),
        ("ledger_hash_after_registration format", "ledger hash not hex",
         _put("ledger_hash_after_registration", "xyz")),
        ("ledger_hash_after_registration format", "ledger hash 31 hex",
         _put("ledger_hash_after_registration", EMPTY_LEDGER_HASH[:31])),
        ("ledger_hash_after_registration format", "ledger hash upper case",
         _put("ledger_hash_after_registration", EMPTY_LEDGER_HASH.upper())))]
    cases += [(rule, label, "F1", None, change) for rule, label, change in (
        ("close 3", "close with 2 decimals at 9", lambda t: t.replace("100.000000000", "100.00", 1)),
        ("close 3", "close with 10 decimals", lambda t: t.replace("100.000000000", "100.0000000000", 1)),
        ("close 3", "close zero", lambda t: t.replace("100.000000000", "0.000000000", 1)),
        ("close 3", "close above PRICE_MAX", lambda t: t.replace("100.000000000", f"{pmax + 1}.000000000", 1)),
        ("bars.csv header", "header i,ts,close", lambda t: t.replace("i,ts_ns,close", "i,ts,close", 1)),
        ("bars.csv line ends", "CRLF line ends", lambda t: t.replace("\n", "\r\n")),
        ("bars.csv line ends", "no final newline", lambda t: t[:-1]),
        ("timestamps not strictly increasing", "timestamps swapped", _swap_ts),
        ("timestamps not strictly increasing", "timestamp repeated", _repeat_ts),
        ("bars.csv row 3", "row index 4 for 3", lambda t: t.replace("\n3,", "\n4,", 1)))]
    cases += [(rule, label, "F2", change, None) for rule, label, change in (
        ("params.hysteresis", "hysteresis 1.0", _put_param("hysteresis", 1.0)),
        ("params.hysteresis", "hysteresis -0.1", _put_param("hysteresis", -0.1)),
        ("params.hysteresis", "hysteresis an int", _put_param("hysteresis", 0)),
        ("params.lookbacks", "lookbacks empty", _put_param("lookbacks", [])),
        ("params.lookbacks", "lookbacks item 5001", _put_param("lookbacks", [1, 5001])),
        ("params.mas", "mas 17 items", _put_param("mas", [2] * 17)),
        ("params.mas", "mas item 0", _put_param("mas", [0, 3])))]
    return cases


def test_px_fixture_inputs_follow_6_1_and_8_2():
    """Spec 8.2, 6.1, C1 and C5 (QA-R3-1): launch.fixture_inputs builds F1, F1r, F2 and N1 as C1's canonical
    input.json bytes with exactly the 14 fields, and LF bars.csv bytes whose rows, timestamps (21:00 UTC on
    weekdays from 2001-01-02; 00:00 UTC the day after each date from 2021-01-01) and closes are 8.2's; the ledger
    hash is an empty ledger's; F1r's child inputs are F1's; N1 is F1 with volume "4000" and 2 price decimals; any
    other name is a KeyError."""
    from core.quant import gate_ledger
    assert launch.FIXTURES == ("F1", "F1r", "F2", "N1"), launch.FIXTURES
    assert gate_ledger.ledger_hash([]) == EMPTY_LEDGER_HASH
    built = {name: launch.fixture_inputs(name) for name in launch.FIXTURES}
    for name, (raw, bars) in built.items():
        assert launch.fixture_inputs(name) == (raw, bars), f"{name}: two calls differ"
        inp = json.loads(raw)
        assert raw == _canonical(inp) and set(inp) == INPUT_KEYS, (name, raw[:80])
        assert b"\r" not in raw + bars and bars.endswith(b"\n") and not raw.endswith(b"\n"), name
        assert inp["bars_sha256"] == hashlib.sha256(bars).hexdigest(), name
        crypto = name == "F2"
        dates, prices = (F2_DATES, F2_PRICES) if crypto else (F1_DATES, F1_PRICES)
        decimals = "0" * inp["price_precision"]
        want = ["i,ts_ns,close"] + [f"{i},{_bar_ns(d, crypto)},{c}.{decimals}"
                                    for i, (d, c) in enumerate(zip(dates, prices))]
        assert bars.decode("utf-8").split("\n") == want + [""], (name, bars[:120])
    assert json.loads(built["F1"][0]) == F1_INPUT and json.loads(built["F2"][0]) == F2_INPUT
    assert built["F1r"] == built["F1"]
    n1 = json.loads(built["N1"][0])
    assert n1 == {**F1_INPUT, "volume": "4000", "price_precision": 2, "bars_sha256": N1_BARS_SHA256}, n1
    assert (_bar_ns("2001-01-02", False), _bar_ns("2021-01-01", True)) == (978469200000000000, 1609545600000000000)
    for other in ("F3", "f1", "N2", ""):
        try:
            launch.fixture_inputs(other)
        except KeyError:
            continue
        raise AssertionError(f"fixture_inputs({other!r}) did not raise KeyError")


def test_px_sandbox_avoids_excluded_constructs():
    """Spec Step 5 done-when, 5.2.3, 5.2.5, 5.2.9 (C-5) and 5.6: sandbox.py keeps 5.2.9's import block verbatim and
    its classes and functions in order, with no __init__ and no super(); on_start starts with the clock guard and
    ends by setting strategy_started; Port.place's one statement is the one order call; no code path uses
    AT_THE_CLOSE, allow_cash_borrowing=True, a latency model, the PortfolioAnalyzer, a report as equity, a MARGIN
    account or another order verb; the venue is NETTING and CASH with bar execution, FillModel(1.0, 0.0, seed) and
    the fee closure; the engine runs without the analyzer at log level ERROR without colours; orders are MARKET GTC;
    and the real sandbox gives no T-RO-01 hit."""
    from tests.acceptance import _code_only
    from tests.macro_m0_harness import _offences
    source = launch.SANDBOX.read_text(encoding="utf-8")
    assert SANDBOX_IMPORTS in source, "sandbox.py lost 5.2.9's import block"
    tree = ast.parse(source)
    defs = [n.name for n in tree.body if isinstance(n, (ast.ClassDef, ast.FunctionDef))]
    order = [n for n in defs if n in SANDBOX_DEFS]
    assert order == list(SANDBOX_DEFS), f"sandbox.py keeps 5.2.9's classes and functions in order: {order}"
    classes = {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}
    port = {f.name: f for f in classes["Port"].body if isinstance(f, ast.FunctionDef)}
    assert set(port) == PORT_METHODS, sorted(port)
    assert [ast.unparse(s) for s in port["place"].body] == [f"self.{ORDER_CALL}(order)"], ast.unparse(port["place"])
    start = port["on_start"].body
    assert (ast.unparse(start[0]), ast.unparse(start[-1])) == (
        "require_backtest_clock(self.clock)", "self.strategy_started = True"), ast.unparse(port["on_start"])
    for cls in ("TrendSwitchPort", "CryptoTrendPort"):
        assert [f.name for f in classes[cls].body if isinstance(f, ast.FunctionDef)] == ["decide"], cls
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    functions = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert "__init__" not in functions and "super" not in names and "state" not in attrs, "rule F3; map03 2.5"
    code = _code_only(launch.SANDBOX)
    assert code.count(ORDER_CALL) == 1, code.count(ORDER_CALL)
    excluded = [w for w in (*EXCLUDED_TEXT, ORDER_CALL + "_list") if w in code]
    assert excluded == [], excluded
    every_call = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]

    def callee(c: ast.Call) -> str:
        return c.func.id if isinstance(c.func, ast.Name) else c.func.attr if isinstance(c.func, ast.Attribute) else ""
    kw: dict[str, list[str]] = {}
    for c in every_call:
        for k in c.keywords:
            kw.setdefault(k.arg, []).append(ast.unparse(k.value))
    flags = (kw["allow_cash_borrowing"], kw["run_analysis"], kw["log_level"], kw["log_colors"], kw["time_in_force"])
    assert flags == (["False"], ["False"], ["'ERROR'"], ["False"], ["TimeInForce.GTC"]), flags
    named = {n: [c for c in every_call if callee(c) == n] for n in ("add_venue", "FillModel", ORDER_CALL, "place")}
    assert {n: len(v) for n, v in named.items()} == dict.fromkeys(named, 1), {n: len(v) for n, v in named.items()}
    venue = {k.arg: ast.unparse(k.value) for k in named["add_venue"][0].keywords}
    assert {k: venue.get(k) for k in VENUE_KEYWORDS} == VENUE_KEYWORDS, venue
    assert venue["fee_model"] == "make_fee_model(inp['cost_bps'], inp['stress'])", venue["fee_model"]
    fill = {k.arg: ast.unparse(k.value) for k in named["FillModel"][0].keywords}
    assert (fill.get("prob_fill_on_limit"), fill.get("prob_slippage"), "random_seed" in fill) == (
        "1.0", "0.0", True), fill
    factory = sorted({callee(c) for c in every_call
                      if isinstance(c.func, ast.Attribute) and ast.unparse(c.func.value) == "self.order_factory"})
    assert factory == ["market"], factory
    assert _offences(launch.SANDBOX) == [], _offences(launch.SANDBOX)


def test_l2_04_fills_identical_across_processes():
    """L2-4 (spec 3.5): F1 and F2 each run in two separate processes through the launch contract and give the same
    fills.csv SHA-256; every output file and both import censuses are identical too; each run is valid, its
    manifest has C6's fields, echoes and hashes, and its fills and decisions are 8.2's."""
    python = layer2()
    for name in ("F1", "F2"):
        raw, bars = launch.fixture_inputs(name)
        runs = [_sandbox_run(python, raw, bars) for _ in range(2)]
        for result, out in runs:
            _check_run(name, raw, bars, result, out)
        (r1, o1), (r2, o2) = runs
        assert hashlib.sha256(o1["fills.csv"]).hexdigest() == hashlib.sha256(o2["fills.csv"]).hexdigest(), name
        assert o1 == o2, [f for f in OUTPUTS if o1[f] != o2[f]]
        assert r1.census == r2.census and len(r1.census) > 100, (name, len(r1.census), len(r2.census))


def test_l2_05a_refusals_exit_20_before_the_engine():
    """L2-5a (spec 6.1, 7 C-05; QA-R3-4, QA-14, QA-R2-8): F1 and F2 unperturbed exit 0; then each single-field
    perturbation of 6.1, an input.json that is not JSON and a bars.csv that is not UTF-8 exit 20 with no file written
    and the refusing rule on stderr ("C-05: input refused: <rule>"); QUANTITY_MAX, PRICE_MAX and FIXED_PRECISION are
    read from --check-env at run time."""
    python = layer2()
    for name in ("F1", "F2"):
        _positive_control(python, name)
    cases = _l2_05a_cases(_check_env_precision(python))
    for rule, label, name, change, bars_change in cases:
        raw, bars = launch.fixture_inputs(name)
        inp = json.loads(raw)
        if bars_change is not None:
            bars = bars_change(bars.decode("utf-8")).encode("utf-8")
            inp["bars_sha256"] = hashlib.sha256(bars).hexdigest()
        if change is not None:
            change(inp)
        result, out = _sandbox_run(python, _canonical(inp), bars)
        _refused_before_engine(label, f"input refused: {rule}", result, out)
    raw, bars = launch.fixture_inputs("F1")
    result, out = _sandbox_run(python, b"{not json", bars)
    _refused_before_engine("input.json not JSON", "input refused: input.json is not UTF-8 JSON", result, out)
    inp, bad = json.loads(raw), bars[:-1] + b"\xff\n"
    inp["bars_sha256"] = hashlib.sha256(bad).hexdigest()
    result, out = _sandbox_run(python, _canonical(inp), bad)
    _refused_before_engine("bars.csv not UTF-8", "input refused: bars.csv is not UTF-8", result, out)
    print(f"  {len(cases) + 2} perturbations refused with exit 20")


def test_l2_05b_input_linked_to_env_refused():
    """L2-5b (spec 5.2.8; SECURITY-3): with input.json a symbolic link to the repo's .env, the sandbox exits 20 with
    no file written, before it opens anything; so it does with bars.csv linked there, and with a --in that is
    relative or that is not its own resolve() (a link to the temp dir). F1 unlinked exits 0. Without the right to
    make a link on Windows (WinError 1314): NotRun (OPS-R2-5)."""
    python = layer2()
    _positive_control(python, "F1")
    raw, bars = launch.fixture_inputs("F1")
    in_rule = "run needs --in <an absolute directory equal to its own resolve()>"
    for label, reason, prepare, in_arg in (
            ("input.json linked to the repo's .env", "input refused: input.json",
             _link("input.json", lambda tmp: ROOT / ".env"), str),
            ("bars.csv linked to the repo's .env", "input refused: bars.csv",
             _link("bars.csv", lambda tmp: ROOT / ".env"), str),
            ("--in .", in_rule, None, lambda tmp: "."),
            ("--in a link to the temp dir", in_rule, _link("alias", lambda tmp: tmp), lambda tmp: str(tmp / "alias"))):
        result, out = _sandbox_run(python, raw, bars, prepare=prepare, in_arg=in_arg)
        _refused_before_engine(label, reason, result, out)


# --------------------------------------------------------------------------- #
# Plan Task 4 (spec Step 6): the runner, the stub child, goldens and the census baseline
# --------------------------------------------------------------------------- #
STUB = ROOT / "tests" / "nautilus_stub_child.py"
GOLDEN_DIR = ROOT / "tools" / "nautilus" / "golden"
ONE_SMA = {"rule": ["sma"], "lookback": [126], "step": [21]}            # a one-column grid: two children
REHEARSAL_LIKE = {                                                       # the fields of 10.1 and 10.2 a table copies
    "E1-SPY": {"family_id": "E1", "rule": "E1", "market": "US", "strategy": "trend_switch", "symbol": "SPY",
               "instrument": "SPY", "axes": {"rule": ["sma", "tsmom"], "lookback": [126, 210, 252], "step": [21, 42]},
               "cost_bps": 50.0, "embargo": 21, "size_precision": 0, "domain": None, "card_id": "NB_E1_trend_spy",
               "claim_label": "pre-specified on historical data; the SPY series was used inside S_E1_trend_us with "
                              "the same 12-setting grid; not confirmatory"},
    "C3-BTCUSD": {"family_id": "C3", "rule": "C3", "market": "CRYPTO", "strategy": "crypto_trend",
                  "symbol": "BTC-USD", "instrument": "BTC/USD", "axes": {"hysteresis": [0.0, 0.222, 0.444, 0.667, 0.889]},
                  "cost_bps": 10.0, "embargo": 1, "size_precision": 8, "domain": {"hysteresis": [0.0, 0.889]},
                  "card_id": "NB_C3_crypto_trend_btcusd",
                  "claim_label": "pre-specified on historical data, engine replication: stored card "
                                 "S_C3_crypto_trend_btcusd on the same file and configurations, grid revised on "
                                 "this file; not new evidence about the rule"}}
SPEC_FILLS = {   # spec 8.2: (bar, side, last_qty, last_px, commission) of F1 and F2
    "F1": ((3, "BUY", "10000", "100.000000000", "5000.00"), (5, "SELL", "10000", "96.000000000", "4800.00"),
           (7, "BUY", "9600", "99.000000000", "4752.00"), (11, "SELL", "9600", "97.000000000", "4656.00")),
    "F2": ((3, "BUY", "1.00000000", "53000.000000000", "53.00"), (5, "SELL", "1.00000000", "50000.000000000", "50.00"),
           (7, "BUY", "0.98812079", "50500.000000000", "49.90"), (9, "SELL", "0.98812079", "51000.000000000", "50.39"))}
SPEC_R = {       # spec 8.2: Nautilus R (to 1e-7) and the QUANTGEN pnl of F1, F1r and F2
    "F1": (0, 0, 0, 0.0348258, -0.0769230, -0.0050000, 0, 0.0151256, 0.0198010, -0.0485413, -0.0102036),
    "F1r": (0.0001, 0.0001, 0.0001, 0.0348258, -0.0769230, -0.0049005, 0.0001, 0.0151256, 0.0198010, -0.0485413,
            -0.0102035),
    "F2": (0, 0, 0, -0.0085386, -0.0494297, -0.0010000, 0, 0.0286743, -0.0192308, -0.0009999)}
SPEC_PNL = {
    "F1": (0, 0, 0, 0.0350000, -0.0769231, -0.0050000, 0, 0.0152020, 0.0198020, -0.0485437, -0.0102041),
    "F1r": (0.0001, 0.0001, 0.0001, 0.0350000, -0.0769231, -0.0049000, 0.0001, 0.0152020, 0.0198020, -0.0485437,
            -0.0102041),
    "F2": (0, 0, 0, -0.0085472, -0.0494297, -0.0010000, 0, 0.0287030, -0.0192308, -0.0010000)}
GOLDEN_SPEC = {  # spec 8.2 and 6.8, typed in: prices at each fixture's precision, dates of ts_event in UTC
    "F1": {"schema": "nautilus-bridge-golden/1", "fixture": "F1", "status": "valid", "exit_code": 0, "bars_fed": 12,
           "bars_seen": 12, "force_stop": False,
           "fills": [{"date": "2001-01-05", "side": "BUY", "qty": "10000", "price": "100.000000000", "commission": "5000.00"},
                     {"date": "2001-01-09", "side": "SELL", "qty": "10000", "price": "96.000000000", "commission": "4800.00"},
                     {"date": "2001-01-11", "side": "BUY", "qty": "9600", "price": "99.000000000", "commission": "4752.00"},
                     {"date": "2001-01-17", "side": "SELL", "qty": "9600", "price": "97.000000000", "commission": "4656.00"}],
           "final_cash": "926593.00", "final_qty": "0", "invalid_reasons": []},
    "F2": {"schema": "nautilus-bridge-golden/1", "fixture": "F2", "status": "valid", "exit_code": 0, "bars_fed": 11,
           "bars_seen": 11, "force_stop": False,
           "fills": [{"date": "2021-01-05", "side": "BUY", "qty": "1.00000000", "price": "53000.000000000", "commission": "53.00"},
                     {"date": "2021-01-07", "side": "SELL", "qty": "1.00000000", "price": "50000.000000000", "commission": "50.00"},
                     {"date": "2021-01-09", "side": "BUY", "qty": "0.98812079", "price": "50500.000000000", "commission": "49.90"},
                     {"date": "2021-01-11", "side": "SELL", "qty": "0.98812079", "price": "51000.000000000", "commission": "50.39"}],
           "final_cash": "50343.77", "final_qty": "0", "invalid_reasons": []},
    "N1": {"schema": "nautilus-bridge-golden/1", "fixture": "N1", "status": "invalid", "exit_code": 10, "bars_fed": 12,
           "bars_seen": 4, "force_stop": True,
           "fills": [{"date": "2001-01-05", "side": "BUY", "qty": "1000", "price": "100.00", "commission": "500.00"}],
           "final_cash": "904501.00", "final_qty": "1000",
           "invalid_reasons": ["C-01: forced stop", "C-02: bars seen fewer than bars fed"]}}


def _runner():
    """tools.nautilus.runner, imported by each test that needs it, so a missing runner fails only Task 4's tests."""
    from tools.nautilus import runner
    return runner


def stub_python() -> str:
    """sys.executable, unless it lies under WindowsApps (the Store python) and the dedicated
    %LOCALAPPDATA%\\quantgen\\py313\\python.exe exists: then that file (8.1; QA-R3-10)."""
    py313 = Path(os.environ.get("LOCALAPPDATA") or "/nonexistent") / "quantgen" / "py313" / "python.exe"
    parts = [p.lower() for p in Path(os.path.normcase(os.path.realpath(sys.executable))).parts]
    return str(py313) if "windowsapps" in parts and py313.is_file() else sys.executable


def stub_cmd(*flags: str) -> list[str]:
    return [stub_python(), "-I", str(STUB), *flags]


def stub_probe_cmd() -> list[str]:
    return stub_cmd("--probe")


def synth_prices(seed, n, p0, p1, planted=()):                       # spec 8.2, verbatim
    import numpy as np
    lr = np.random.default_rng(seed).normal(0.0, np.where(np.arange(n) // 250 % 2 == 0, 0.008, 0.02))
    lr += (np.log(p1 / p0) - lr.sum()) / n                         # drift from about p0 to about p1
    for k, i in enumerate(planted):
        lr[i] = np.log(1.1 if k % 2 == 0 else 0.9)                 # planted +10 % and -10 % days
    return np.round(p0 * np.exp(np.cumsum(lr)), 9)


def synth_rf(n):                                                   # stepped: 0, 2, 5 and 1 % a year
    import numpy as np
    return np.repeat([0.0, 0.02, 0.05, 0.01], -(-n // 4))[:n] / 252


def _bdates(n: int) -> list[str]:
    """Spec 8.2's calendar: pd.bdate_range("2001-01-02", periods=n)."""
    import pandas as pd
    return [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2001-01-02", periods=n)]


def _md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def _write_prices(path: Path, dates: Sequence[str], prices) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("Date,Close\n" + "".join(f"{d},{p:.9f}\n" for d, p in zip(dates, prices)), encoding="utf-8",
                    newline="\n")
    return _md5(path)


def _write_rf(path: Path, dates: Sequence[str], rf) -> str:
    """A DGS3MO-shaped file: percent a year (rf * 252 * 100); a None value is a blank, as FRED leaves holidays."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = "".join(f"{d},{'' if x is None else repr(float(x) * 252 * 100)}\n" for d, x in zip(dates, rf))
    path.write_text("DATE,DGS3MO\n" + rows, encoding="utf-8", newline="\n")
    return _md5(path)


def write_rehearsal_table(tmp: Path, *, like: str = "E1-SPY", prices, dates: Sequence[str], rf=None, **fields) -> Path:
    """The prices file, the DGS3MO-shaped file when rf is given, and <tmp>/table.json: a 6.6 table with pilot
    "rehearsal" and every other field from pilot `like` (10.1 or 10.2), study_configs [], no reference card, md5s
    computed, no owner field; `fields` override any key (a new `axes` without `grid` recomputes the grid). Written
    without sort_keys: the axes keys keep the study's call order, which fixes the grid's column order (spec 5.3.2 step 1)."""
    from core.quant import strategies as S
    t = {"schema": "nautilus-bridge-table/1", "pilot": "rehearsal", **REHEARSAL_LIKE[like],
         "prices_file": str(tmp / "prices.csv"), "prices_md5": _write_prices(tmp / "prices.csv", dates, prices),
         "start": dates[0], "end": dates[-1], "rf_file": None, "rf_md5": None, "capital_usd": "1000000",
         "price_precision": 9, "volume": "1000000000", "fill_seed": 42,
         "hypothesis": "synthetic rehearsal: both engines give the same matrix", "study_configs": [],
         "reference_card": None, "reference_card_md5": None}
    if rf is not None:
        t.update(rf_file=str(tmp / "DGS3MO.csv"), rf_md5=_write_rf(tmp / "DGS3MO.csv", dates, rf))
    t.update(fields)
    t["grid"] = fields["grid"] if "grid" in fields else S.grid_from(**t["axes"])
    path = tmp / "table.json"
    path.write_text(json.dumps(t, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return path


def run_rehearsal(table: Path, tmp: Path, *, flags: Sequence[str] = (), **run_kwargs) -> tuple[int, dict | None]:
    """runner.run in rehearsal mode with the stub child and the stub probe, ledger and outputs under tmp; returns
    the exit code and the newest run.json under tmp/out (None when no run folder holds one)."""
    code = _runner().run(table, mode="rehearsal", ledger_dir=tmp / "ledgers", out_dir=tmp / "out",
                         child_cmd=stub_cmd(*flags), probe_cmd=stub_probe_cmd(), **run_kwargs)
    runs = sorted((tmp / "out").glob("NB-*/run.json"))
    return code, (json.loads(runs[-1].read_text(encoding="utf-8")) if runs else None)


def _small_table(tmp: Path, *, n: int = 320, axes: dict | None = None, with_rf: bool = True, **fields) -> Path:
    """A synthetic SPY-like rehearsal table: synth_prices(7, n, 100, 150), synth_rf(n), one sma column by default."""
    return write_rehearsal_table(tmp, prices=synth_prices(7, n, 100.0, 150.0), dates=_bdates(n),
                                 rf=synth_rf(n) if with_rf else None, axes=axes or ONE_SMA, **fields)


def _captured(fn: Callable[[], object]) -> tuple[object, str]:
    """fn() with stdout captured: (its result, what it printed)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        out = fn()
    return out, buf.getvalue()


def _step_hooks(seen: list[int]) -> dict:
    """after_step0 .. after_step17, each appending its step number to `seen`."""
    return {f"after_step{n}": (lambda _ctx, n=n: seen.append(n)) for n in range(18)}


def _plain_row(rule: str, k: int) -> dict:
    return {"rule": rule, "params": {"k": k}, "timing_class": "COMPLIANT", "span": ["2001-01-02", "2002-03-01"],
            "market": "US", "run_utc": "2026-10-28T00:00:00Z", "phase": "research", "script": "tests/nautilus_acceptance.py"}


def _code_root(dst: Path) -> Path:
    """A temp copy of every file code_sha256 reads, so of-record checks run on a temp repository root."""
    for p in _runner().code_paths(ROOT):
        target = dst / p.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(p.read_bytes())
    return dst


def _of_record_table(path: Path, pilot: str, code: str, **fields) -> Path:
    """An of-record table under the system temp dir only (GOVERNANCE-R3-5), whose owner_confirmed quotes its own
    table_sha256 and `code`. It names the pilot's files; check_table never opens a data file."""
    from core.quant import strategies as S
    runner = _runner()
    e1 = pilot == "E1-SPY"
    t = {"schema": "nautilus-bridge-table/1", "pilot": pilot, **REHEARSAL_LIKE[pilot],
         "prices_file": "docs/asset_expansion/cache/" + ("yf_SPY.csv" if e1 else "yf_BTC-USD.csv"),
         "prices_md5": runner.PINNED_REAL_MD5["SPY" if e1 else "BTC-USD"],
         "start": "2004-12-01" if e1 else "2014-09-17", "end": "2026-09-25",
         "rf_file": "docs/asset_expansion/cache/fred_DGS3MO.csv" if e1 else None,
         "rf_md5": "661722143f24930a29b58c535d227c1b" if e1 else None, "capital_usd": "1000000", "price_precision": 9,
         "volume": "1000000000", "fill_seed": 42, "hypothesis": "of-record shape, temp only", "study_configs": [],
         "reference_card": None, "reference_card_md5": None, "host_fingerprint": "0" * 64}
    t.update(fields)
    t["grid"] = fields["grid"] if "grid" in fields else S.grid_from(**t["axes"])
    t.setdefault("owner_confirmed", f"Geon Koh, 2026-10-28, table {runner.table_sha256(t)[:16]}, code {code[:16]}")
    path.write_text(json.dumps(t, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return path


def _fixture_series(name: str):
    """(capital, ts, closes) of an 8.2 fixture, from launch.fixture_inputs (C2)."""
    import numpy as np
    raw, bars = launch.fixture_inputs(name)
    rows = [r.split(",") for r in bars.decode("utf-8").splitlines()[1:]]
    return json.loads(raw)["capital_usd"], [int(r[1]) for r in rows], np.array([float(r[2]) for r in rows])


def test_l1_01_return_reconstruction_f1_f1r_f2():
    """L1-1 (5.3.3): R rebuilt from 8.2's fills matches 8.2's Nautilus R on F1, F1r and F2 to 1e-7, with the cash
    overlay on F1r; the final cash, the fill bars and TV (the bar T-1 fill dropped) follow; QUANTGEN's simulate gives
    8.2's pnl; a fill off every bar timestamp is C-09."""
    import numpy as np
    from decimal import Decimal
    from core.quant import strategies as S
    runner = _runner()
    rebuilt = {}
    for name in ("F1", "F1r", "F2"):
        capital, ts, closes = _fixture_series("F2" if name == "F2" else "F1")
        rf = np.full(len(ts), 0.0001 if name == "F1r" else 0.0)
        fills = [{"ts_event": ts[b], "order_side": side, "last_qty": Decimal(q), "last_px": Decimal(px),
                  "commission": Decimal(c), "commission_ccy": "USD", "trade_id": f"T{k}", "venue_order_id": f"O{k}"}
                 for k, (b, side, q, px, c) in enumerate(SPEC_FILLS["F2" if name == "F2" else "F1"])]
        rb = rebuilt[name] = runner.rebuild_returns(fills, closes, ts, rf, Decimal(capital))
        assert rb.R.shape == (len(ts) - 1,) and np.max(np.abs(rb.R - np.array(SPEC_R[name]))) <= 1e-7, (name, rb.R)
        assert rb.E_minus[0] == float(capital) and rb.fill_bars == [3, 5, 7, 9 if name == "F2" else 11], rb.fill_bars
        if name == "F2":
            W = S.crypto_trend(closes, lookbacks=(1, 2), mas=(2, 3), hysteresis=0.2)
            pnl, _ = S.simulate(closes, W, cost_bps=10.0, cash_daily=rf)
            assert rb.final_cash.quantize(Decimal("0.000001")) == Decimal("50343.770395"), rb.final_cash
            assert np.flatnonzero(rb.TV).tolist() == [3, 5, 7, 9], rb.TV
        else:
            W = S.trend_switch(closes, rule="sma", lookback=3, step=2)
            pnl, turnover = S.simulate(closes, W, cost_bps=50.0, cash_daily=rf)
            assert turnover.tolist() == [0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0], turnover
            assert rb.final_cash == Decimal("926593") and np.flatnonzero(rb.TV).tolist() == [3, 5, 7], rb.TV
            assert abs(rb.TV[3] - 1_000_000 / 1_005_001) < 1e-12, rb.TV[3]
        assert np.max(np.abs(pnl - np.array(SPEC_PNL[name]))) <= 1e-7, (name, pnl)
    moved = np.abs(rebuilt["F1r"].R - rebuilt["F1"].R)
    assert all(moved[t] < 1e-8 for t in (3, 4, 7, 8, 9)), moved
    capital, ts, closes = _fixture_series("F1")
    off = [{"ts_event": ts[3] + 1, "order_side": "BUY", "last_qty": Decimal(1), "last_px": Decimal(100),
            "commission": Decimal("0.50"), "commission_ccy": "USD", "trade_id": "T", "venue_order_id": "O"}]
    _invalid(lambda: runner.rebuild_returns(off, closes, ts, np.zeros(len(ts)), Decimal(capital)), "C-09")


def test_l1_03_children_start_after_registration():
    """L1-3 (QA-6, QA-R4-4, QA-R4-5): with the stub child, a child_started hook finds every config_id of the table in
    the temp ledger and input.json's ledger hash equal to family_ledger(...).hash(); no child exits 1; the record
    carries the post-registration hash, both data md5s and every child manifest echoing it."""
    from core.quant import gate_ledger
    with tempfile.TemporaryDirectory(prefix="qgnb_l103_") as name:
        tmp = Path(name)
        table = _small_table(tmp, axes={"rule": ["sma", "tsmom"], "lookback": [126], "step": [21]})
        t = json.loads(table.read_text(encoding="utf-8"))
        expected = {gate_ledger.config_id({"rule": "E1", "params": dict(g, symbols=["SPY"], cost_bps=50.0),
                                           "timing_class": "COMPLIANT"}) for g in t["grid"]}
        seen = []

        def started(lc):
            ledger = gate_ledger.family_ledger("E1", tmp / "ledgers")
            rows = ledger.rows()
            inp = json.loads((Path(lc.cwd) / "input.json").read_text(encoding="utf-8"))
            seen.append(({r["config_id"] for r in rows}, inp["ledger_hash_after_registration"], ledger.hash(rows),
                         inp["stress"]))
        (code, rec), out = _captured(lambda: run_rehearsal(table, tmp, hooks={"child_started": started}))
        assert rec is not None and len(seen) == 4, out[-2000:]
        assert all(ids == expected and echoed == now for ids, echoed, now, _ in seen), seen
        assert [s for *_, s in seen] == ["1", "2", "1", "2"], seen
        assert [c["returncode"] for c in rec["children"]] == [0, 0, 0, 0], rec["children"]
        assert all(c["invalid"] == [] for c in rec["children"]), [c["invalid"] for c in rec["children"]]
        reg = rec["registration"]
        assert reg["hash_after"] == seen[0][1] and (reg["n_raw_before"], reg["n_raw_after"]) == (0, 2), reg
        assert {r["config_id"] for r in reg["rows"]} == expected and all(r["appended"] for r in reg["rows"]), reg
        assert all(c["manifest"]["input"]["ledger_hash_after_registration"] == reg["hash_after"]
                   for c in rec["children"])
        assert all(isinstance(rec["times"][k], str) for k in ("registered_utc", "first_child_utc")), rec["times"]
        assert (rec["data"]["prices_md5"], rec["data"]["rf_md5"]) == (t["prices_md5"], t["rf_md5"]), rec["data"]
        assert rec["stub_child"] is True and rec["provenance"]["p0a"]["passed"] is True and rec["census"] == {}


def test_l1_04_broken_chain_stops_before_children():
    """L1-4 (R-09): a broken chain in the temp family ledger refuses at step 10, before registration and before any
    child; the ledger's bytes are unchanged and no run folder exists."""
    from core.quant import gate_ledger
    with tempfile.TemporaryDirectory(prefix="qgnb_l104_") as name:
        tmp = Path(name)
        table = _small_table(tmp)
        ledger = gate_ledger.family_ledger("E1", tmp / "ledgers")
        gate_ledger.register_trial(ledger, _plain_row("E1", 1))
        ledger.path.write_bytes(ledger.path.read_bytes().replace(b'"US"', b'"KR"'))   # row_md5 no longer matches
        old = time.time() - 700
        os.utime(ledger.path, (old, old))                                               # not R-16's freshness
        before, steps, started = ledger.path.read_bytes(), [], []
        hooks = {**_step_hooks(steps), "child_started": started.append}
        (code, rec), out = _captured(lambda: run_rehearsal(table, tmp, hooks=hooks))
        assert (code, rec) == (2, None) and "R-09: " in out, out[-2000:]
        assert out.splitlines()[-1] == "STATUS REFUSED exit=2 record=-", out[-500:]
        assert steps == list(range(10)) and started == [], (steps, started)
        assert ledger.path.read_bytes() == before and not list((tmp / "out").glob("NB-*"))


def test_l1_06_tree_refusals_r01_r02():
    """L1-6 (5.3.2 step 2): check_tree and tree_refusal on a temp git repository: a modified tracked file and an
    untracked file outside docs/nautilus_bridge/runs/ refuse (R-01), an untracked file under runs/ passes, a worktree
    and packed refs refuse with their own messages (R-02), git missing is R-02; rehearsal returns None for each."""
    from core.quant import gate_ledger
    runner = _runner()
    git = shutil.which("git")
    if git is None:
        raise NotRun("OWNER: git not on PATH")
    with tempfile.TemporaryDirectory(prefix="qgnb_l106_") as name:
        tmp, repo = Path(name), Path(name) / "repo"

        def g(*args: str) -> str:
            out = subprocess.run([git, "-c", "user.name=qgnb", "-c", "user.email=qgnb@example.invalid", "-c",
                                  "commit.gpgsign=false", *args], cwd=repo, capture_output=True, encoding="utf-8",
                                 errors="replace", timeout=60)
            assert out.returncode == 0, (args, out.stderr)
            return out.stdout

        def judge(root: Path = repo):
            found = runner.check_tree(root, gate_ledger.repo_anchor, git)
            assert runner.tree_refusal(found, "rehearsal") is None, found
            return found, runner.tree_refusal(found, "of-record")
        repo.mkdir()
        g("init", "-q", "-b", "main")
        (repo / "a.txt").write_text("a\n", encoding="utf-8", newline="\n")
        g("add", "a.txt")
        g("commit", "-q", "-m", "a")
        found, rid = judge()
        assert rid is None and found["clean"] and found["anchor"] == f"git:{g('rev-parse', 'HEAD').strip()}", found
        runs = repo / "docs" / "nautilus_bridge" / "runs" / "NB-x"
        runs.mkdir(parents=True)
        (runs / "run.json").write_text("{}\n", encoding="utf-8", newline="\n")
        found, rid = judge()
        assert rid is None and found["porcelain_exempt"] == ["?? docs/nautilus_bridge/runs/NB-x/run.json"], found
        (repo / "a.txt").write_text("b\n", encoding="utf-8", newline="\n")
        found, rid = judge()
        assert rid == "R-01" and found["offending"] == [" M a.txt"], found
        g("checkout", "--", "a.txt")
        (repo / "b.txt").write_text("b\n", encoding="utf-8", newline="\n")
        found, rid = judge()
        assert rid == "R-01" and found["offending"] == ["?? b.txt"], found
        (repo / "b.txt").unlink()
        g("worktree", "add", "-q", str(tmp / "wt"))
        found, rid = judge(tmp / "wt")
        assert rid == "R-02" and "worktree" in found["anchor_problem"], found
        g("pack-refs", "--all")
        found, rid = judge()
        assert rid == "R-02" and "packed" in found["anchor_problem"], found
        assert 'git commit --allow-empty -m "nautilus: re-anchor"' in found["anchor_problem"], found
        found = runner.check_tree(repo, gate_ledger.repo_anchor, None)
        assert found["head"] is None and runner.tree_refusal(found, "of-record") == "R-02", found
        assert runner.tree_refusal(found, "rehearsal") is None


def test_l1_07_data_refusals_r04_r05_r06():
    """L1-7 (5.3.2 steps 5 and 6): R-04 (missing, unreadable, doctored md5), R-05 (N5's duplicated and swapped
    dates, under 300 rows, a close failing the round trip), R-06 (missing, doctored md5, a NaN before the first
    observation; no 3 % fallback, K8) on synthetic files; a blank DGS3MO value mid-series takes the prior value and
    P0a then passes (QUANT-R2-1); run() refuses R-04 and R-06 at their steps."""
    import numpy as np
    runner = _runner()
    with tempfile.TemporaryDirectory(prefix="qgnb_l107_") as name:
        tmp = Path(name)
        n, dates = 320, _bdates(320)
        prices = synth_prices(7, n, 100.0, 150.0)
        kw = {"start": dates[0], "end": dates[-1], "instrument": "SPY", "mode": "rehearsal"}
        good = _write_prices(tmp / "p.csv", dates, prices)
        p = runner.load_prices(tmp / "p.csv", md5=good, **kw)
        assert p.dates == tuple(dates) and p.closes.tobytes() == prices.tobytes() and not p.rounding_changed
        assert p.ts[:2] == [978469200 * 10**9, 978555600 * 10**9] and p.md5 == good, p.ts[:2]
        cut = runner.load_prices(tmp / "p.csv", md5=good, **dict(kw, start=dates[10], end=dates[-11]))
        assert cut.dates == tuple(dates[10:-10]), len(cut.dates)
        _refused(lambda: runner.load_prices(tmp / "missing.csv", md5=good, **kw), "R-04")
        _refused(lambda: runner.load_prices(tmp / "p.csv", md5="0" * 32, **kw), "R-04")
        (tmp / "bad.csv").write_bytes(b"\xff\xfe garbage")
        _refused(lambda: runner.load_prices(tmp / "bad.csv", md5=_md5(tmp / "bad.csv"), **kw), "R-04")
        for label, ds, ps in (("299 rows", dates[:299], prices[:299]),
                              ("duplicated", dates[:150] + [dates[149]] + dates[151:], prices),
                              ("swapped", dates[:150] + [dates[151], dates[150]] + dates[152:], prices)):
            md5 = _write_prices(tmp / f"{label}.csv", ds, ps)
            exc = _refused(lambda: runner.load_prices(tmp / f"{label}.csv", md5=md5, **kw), "R-05")
            assert ("300" in exc.message) == (label == "299 rows"), (label, exc)
        runner.check_round_trip(prices)
        _refused(lambda: runner.check_round_trip(np.array([100.0, 0.1 + 0.2])), "R-05")
        rf = synth_rf(n)
        rmd5 = _write_rf(tmp / "r.csv", dates, rf)
        got, data = runner.load_rf(tmp / "r.csv", md5=rmd5, dates=p.dates)
        assert data == (tmp / "r.csv").read_bytes() and np.max(np.abs(got - rf)) < 1e-15, np.max(np.abs(got - rf))
        _refused(lambda: runner.load_rf(tmp / "missing.csv", md5=rmd5, dates=p.dates), "R-06")
        _refused(lambda: runner.load_rf(tmp / "r.csv", md5="0" * 32, dates=p.dates), "R-06")
        late = _write_rf(tmp / "late.csv", dates[5:], rf[5:])
        _refused(lambda: runner.load_rf(tmp / "late.csv", md5=late, dates=p.dates), "R-06")
        blank = [None if k == 100 else x for k, x in enumerate(rf)]
        bmd5 = _write_rf(tmp / "blank.csv", dates, blank)
        got, _ = runner.load_rf(tmp / "blank.csv", md5=bmd5, dates=p.dates)
        assert got[100] == got[99] and not np.isnan(got).any(), got[98:102]
        for sub, fields, rid, upto in (("r04", {"prices_md5": "0" * 32}, "R-04", 4),
                                       ("r06", {"rf_md5": "0" * 32}, "R-06", 5)):
            steps = []
            table = _small_table(tmp / sub, **fields)
            (code, rec), out = _captured(lambda: run_rehearsal(table, tmp / sub, hooks=_step_hooks(steps)))
            assert (code, rec) == (2, None) and f"{rid}: " in out and steps == list(range(upto + 1)), (rid, steps)
        steps = []
        table = _small_table(tmp / "blank", with_rf=False, rf_file=str(tmp / "blank.csv"), rf_md5=bmd5)

        def stop(_ctx):
            steps.append(7)
            raise RuntimeError("stop after P0a (planted)")
        (code, rec), out = _captured(lambda: run_rehearsal(table, tmp / "blank", hooks={"after_step7": stop}))
        assert (code, rec) == (2, None) and steps == [7] and "stop after P0a (planted)" in out, out[-2000:]
        assert not (tmp / "blank" / "ledgers" / "E1.jsonl").exists()


def test_l1_08_cost_refusals_r07():
    """L1-8 (K15): R-07 for an uncosted symbol (VOD.L) and for 40 bp on SPY; through run(), at step 8."""
    runner = _runner()
    exc = _refused(lambda: runner.check_cost("VOD.L", 50.0), "R-07")
    assert "VOD.L" in exc.message, exc
    exc = _refused(lambda: runner.check_cost("SPY", 40.0), "R-07")
    assert "below the floor 50" in exc.message, exc
    assert runner.check_cost("SPY", 50.0) == (50.0, {"SPY": "us"})
    assert runner.check_cost("BTC-USD", 10.0) == (10.0, {"BTC-USD": "crypto"})
    with tempfile.TemporaryDirectory(prefix="qgnb_l108_") as name:
        tmp, steps = Path(name), []
        table = _small_table(tmp, cost_bps=40.0)
        (code, rec), out = _captured(lambda: run_rehearsal(table, tmp, hooks=_step_hooks(steps)))
        assert (code, rec) == (2, None) and "R-07: cost_bps 40 is below the floor 50 bp for SPY" in out, out[-2000:]
        assert steps == list(range(8)) and not (tmp / "ledgers" / "E1.jsonl").exists(), steps


def test_l1_09_place_and_content_refusals_r10():
    """L1-9 (3.9; GOVERNANCE-R2-3, GOVERNANCE-R3-3, QA-R4-2): R-10 for a ledger or output dir outside the temp root
    (argument validation, nothing created); for a synthetic file whose md5 is planted as the pinned BTC md5, and one
    planted as the pinned SPY md5 with end 2004-11-30 (step 5); for a table naming a tracked file of
    docs/asset_expansion/cache/ with prices_md5 of 32 zeros, by check_table and by run() with no after_step1 hook,
    so the place is judged before any hash; for a reference card outside the temp root. No real file is read."""
    runner = _runner()
    locks = ROOT / "docs" / "nautilus_bridge" / "runs" / ".locks"
    had_locks = locks.exists()
    with tempfile.TemporaryDirectory(prefix="qgnb_l109_") as name:
        tmp = Path(name)
        table = _small_table(tmp / "a")
        outside = Path.home() / "qgnb_not_a_temp_dir"
        for kw in ({"ledger_dir": outside, "out_dir": tmp / "out"},
                   {"ledger_dir": tmp / "ledgers", "out_dir": ROOT / "docs" / "nautilus_bridge" / "runs"}):
            steps = []
            code, out = _captured(lambda: runner.run(table, mode="rehearsal", child_cmd=stub_cmd(),
                                                     probe_cmd=stub_probe_cmd(), hooks=_step_hooks(steps), **kw))
            assert code == 2 and "R-10: rehearsal needs --ledger-dir and --out-dir inside the temp root" in out, out
            assert steps == [], steps
        assert not outside.exists() and locks.exists() == had_locks
        md5 = json.loads(table.read_text(encoding="utf-8"))["prices_md5"]
        saved = dict(runner.PINNED_REAL_MD5)
        try:
            for symbol, sub, fields in (("BTC-USD", "a", {}), ("SPY", "b", {"end": "2004-11-30"})):
                runner.PINNED_REAL_MD5.update(saved)
                runner.PINNED_REAL_MD5[symbol] = md5                       # the synthetic file, planted as the pin
                planted = _small_table(tmp / sub, **fields)
                steps = []
                (code, rec), out = _captured(lambda: run_rehearsal(planted, tmp / sub, hooks=_step_hooks(steps)))
                assert (code, rec) == (2, None) and "is a byte copy of a pinned real series" in out, out[-2000:]
                assert "R-10: " in out and steps == [0, 1, 2, 3, 4], steps
        finally:
            runner.PINNED_REAL_MD5.clear()
            runner.PINNED_REAL_MD5.update(saved)
        for k, rel in enumerate(("docs/asset_expansion/cache/yf_SPY.csv", "docs/asset_expansion/cache/binance_BTCUSDT.csv")):
            for j, value in enumerate((rel, str(ROOT / rel))):
                sub = tmp / f"cache{k}{j}"
                bad = _small_table(sub, prices_file=value, prices_md5="0" * 32)
                exc = _refused(lambda: runner.check_table(bad, "rehearsal", sub / "ledgers", "qgnb-host", ROOT), "R-10")
                assert repr(value) in exc.message, exc
                steps = []
                (code, rec), out = _captured(lambda: run_rehearsal(bad, sub, hooks=_step_hooks(steps)))
                assert (code, rec) == (2, None) and "R-10: " in out and steps == [0], (steps, out[-1000:])
        card = "docs/asset_expansion/cards/S_C3_crypto_trend_btcusd.json"
        bad = _small_table(tmp / "card", reference_card=str(ROOT / card), reference_card_md5="0" * 32)
        _refused(lambda: runner.check_table(bad, "rehearsal", tmp / "ledgers", "qgnb-host", ROOT), "R-10")


def test_l1_10_config_id_equals_strategy_lab():
    """L1-10 (K9): the bridge row's config_id for SPY sma/127/21 at 50.0 (E1) and BTC-USD hysteresis 0.333 at 10.0
    (C3) equals the one ui.strategy_lab_page.register_trials writes with ledger_dir given explicitly; neither is a
    pilot configuration (GOVERNANCE-R3-2). An int cost would be another configuration."""
    import ui.strategy_lab_page as lab
    from core.quant import gate_ledger
    runner = _runner()
    with tempfile.TemporaryDirectory(prefix="qgnb_l110_") as name:
        tmp, dates = Path(name), _bdates(320)
        for like, family, theta, cost, symbol in (
                ("E1-SPY", "trend_switch", {"rule": "sma", "lookback": 127, "step": 21}, 50.0, "SPY"),
                ("C3-BTCUSD", "crypto_trend", {"hysteresis": 0.333}, 10.0, "BTC-USD")):
            table = {**REHEARSAL_LIKE[like], "pilot": "rehearsal", "cost_bps": cost}
            row = runner.ledger_row(table, theta, span=(dates[0], dates[-1]), run_utc="2026-10-28T00:00:00Z",
                                    anchor=gate_ledger.repo_anchor(), bridge_run_id="NB-x")
            bridge = gate_ledger.register_trial(gate_ledger.family_ledger(row["rule"], tmp / "bridge"), row,
                                                script=runner.SCRIPT)
            n = lab.register_trials(family, [symbol], [theta], cost, dates, ["YAHOO"], ledger_dir=tmp / f"lab_{like}")
            lab_row = gate_ledger.family_ledger(lab.FAMILY_ID[family], tmp / f"lab_{like}").rows()[0]
            assert n == 1 and lab_row["config_id"] == bridge.row["config_id"], (lab_row, bridge.row)
            assert bridge.row["params"] == dict(theta, symbols=[symbol], cost_bps=cost), bridge.row["params"]
            assert type(bridge.row["params"]["cost_bps"]) is float and bridge.row["run_kind"] == "variant"
            assert bridge.row["source"] == ("nautilus-bridge rehearsal; engines quantgen.simulate + nautilus_trader "
                                            "1.231.0; run NB-x"), bridge.row["source"]
            as_int = dict(row, params=dict(row["params"], cost_bps=int(cost)))
            assert gate_ledger.config_id(as_int) != bridge.row["config_id"]


def test_l1_11_register_result_row_md5():
    """L1-11 (A-1): the recorded row_md5 is result.row["row_md5"] for an appended row and for a duplicate, never
    RegisterResult's third element, which on an append is the md5 of the line (the next row's prev_row_md5)."""
    from core.quant import gate_ledger
    runner = _runner()
    with tempfile.TemporaryDirectory(prefix="qgnb_l111_") as name:
        ledger = gate_ledger.family_ledger("E1", Path(name))
        first = gate_ledger.register_trial(ledger, _plain_row("E1", 1))
        second = gate_ledger.register_trial(ledger, _plain_row("E1", 2))
        dup = gate_ledger.register_trial(ledger, dict(_plain_row("E1", 1), run_utc="2026-10-28T01:00:00Z"))
        rows = ledger.rows()
        assert first.appended and second.appended and not dup.appended and len(rows) == 2
        assert first.row_md5 != first.row["row_md5"] and first.row_md5 == rows[1]["prev_row_md5"]
        assert dup.row_md5 == dup.row["row_md5"] == rows[0]["row_md5"]
        got = [runner.registration_entry(col, r) for col, r in enumerate((first, second, dup))]
        assert got == [{"col": 0, "config_id": rows[0]["config_id"], "row_md5": rows[0]["row_md5"], "appended": True},
                       {"col": 1, "config_id": rows[1]["config_id"], "row_md5": rows[1]["row_md5"], "appended": True},
                       {"col": 2, "config_id": rows[0]["config_id"], "row_md5": rows[0]["row_md5"], "appended": False}]


def test_l1_12_census_judgement():
    """L1-12 (5.2.7; QA-R3-12): on a census parsed from doctored -X importtime stderr, an extra TP name, a missing TP
    name, an extra NT name and nautilus_trader.adapters.binance (even in the baseline) each give C-08; an extra STD
    name does not."""
    runner = _runner()
    base = ["_io", "_sysconfigdata__linux_x86_64-linux-gnu", "json", "json.decoder", "msgspec", "nautilus_trader",
            "nautilus_trader.backtest.engine", "numpy", "numpy._core", "pandas", "sitecustomize"]
    stderr = "import time: self [us] | cumulative | imported package\n" + "".join(
        f"import time:        1 |          1 |   {n}\n" for n in reversed(base)) + "ValueError: boom\n"
    census, rest = launch.parse_census(stderr)
    assert census == base and rest == "ValueError: boom\n", (census, rest)
    assert [runner.census_class(n) for n in ("nautilus_trader.model", "zoneinfo", "_sysconfigdata_x", "uvloop")] == [
        "NT", "STD", "STD", "TP"]
    assert runner.judge_census(census, base) == []
    assert runner.judge_census(census + ["zoneinfo", "zoneinfo._common"], base) == []
    assert runner.judge_census(census + ["plotly"], base) == ["C-08: TP names added: plotly"]
    assert runner.judge_census([n for n in census if n != "msgspec"], base) == ["C-08: TP names missing: msgspec"]
    assert runner.judge_census(census + ["nautilus_trader.live.node"], base) == [
        "C-08: NT names added: nautilus_trader.live.node"]
    binance = "nautilus_trader.adapters.binance"
    assert runner.judge_census(census + [binance], base + [binance]) == [f"C-08: denied modules imported: {binance}"]


def test_l1_18_gate_bootstrap_b_refusal_r08():
    """L1-18: with GATE["bootstrap_B"] set to 300 inside try/finally, run() refuses R-08 at step 9, before
    registration; GATE is restored."""
    from core.quant import validate
    with tempfile.TemporaryDirectory(prefix="qgnb_l118_") as name:
        tmp, steps = Path(name), []
        table = _small_table(tmp)
        saved = validate.GATE["bootstrap_B"]
        try:
            validate.GATE["bootstrap_B"] = 300
            (code, rec), out = _captured(lambda: run_rehearsal(table, tmp, hooks=_step_hooks(steps)))
        finally:
            validate.GATE["bootstrap_B"] = saved
        assert (code, rec) == (2, None) and "R-08: GATE['bootstrap_B'] is 300, not 2000" in out, out[-2000:]
        assert steps == list(range(9)) and validate.GATE["bootstrap_B"] == 2000, steps
        assert not (tmp / "ledgers" / "E1.jsonl").exists()


def test_l1_19_table_refusals_r11():
    """L1-19 (6.6; GOVERNANCE-R2-2, GOVERNANCE-R3-1, GOVERNANCE-R4-4, OPS-R3-6): R-11 through check_table for a
    table that is not JSON, a missing or unknown field, a wrong type and a grid that differs from grid_from(axes);
    of-record: a pilot value off, a key field edited and a sandbox byte or a core/quant/validate.py byte changed
    after owner_confirmed; a PureWindowsPath-built path list gives the same code_sha256; run(mode="of-record") with
    a seam refuses in argument validation and creates no runs/.locks; of-record C3-BTCUSD on a temp root refuses
    without a reference card, without an of-record E1-SPY record and with one WITHHELD for a parity failure."""
    runner = _runner()
    locks = ROOT / "docs" / "nautilus_bridge" / "runs" / ".locks"
    had_locks = locks.exists()
    with tempfile.TemporaryDirectory(prefix="qgnb_l119_") as name:
        tmp = Path(name)
        table = _small_table(tmp / "r")
        good = json.loads(table.read_text(encoding="utf-8"))
        assert runner.check_table(table, "rehearsal", tmp / "ledgers", "qgnb-host", ROOT) == good

        def variant(change) -> Path:
            t = json.loads(json.dumps(good))
            change(t)
            path = tmp / "variant.json"
            path.write_text(json.dumps(t), encoding="utf-8", newline="\n")
            return path
        (tmp / "notjson.json").write_text("{not json\n", encoding="utf-8", newline="\n")
        for path in (tmp / "notjson.json", variant(lambda t: t.pop("embargo")), variant(lambda t: t.update(x=1)),
                     variant(lambda t: t.update(embargo="21")), variant(lambda t: t["grid"].pop()),
                     variant(lambda t: t.update(pilot="E1-SPY")), variant(lambda t: t.update(price_precision=2)),
                     variant(lambda t: t["grid"][0].update(lookback=0))):
            _refused(lambda: runner.check_table(path, "rehearsal", tmp / "ledgers", "qgnb-host", ROOT), "R-11")
        root = _code_root(tmp / "root")
        code = runner.code_sha256(root)
        assert code == runner.code_sha256(ROOT)
        win_root = PureWindowsPath("C:/Users/o/QUANTGEN")
        paths = runner.code_paths(ROOT)
        win = [win_root / PureWindowsPath(p.relative_to(ROOT).as_posix()) for p in paths]
        by_win = dict(zip(win, paths))
        assert runner.code_digest(win_root, win, lambda w: by_win[w].read_bytes()) == code
        e1 = _of_record_table(tmp / "e1.json", "E1-SPY", code)
        chk = lambda path: runner.check_table(path, "of-record", tmp / "ledgers", "qgnb-host", root)   # noqa: E731
        assert "does not exist" in _refused(lambda: chk(e1), "R-15").message      # R-11 passed, R-15 is next
        exc = _refused(lambda: chk(_of_record_table(tmp / "cap.json", "E1-SPY", code, capital_usd="999999")), "R-11")
        assert "capital_usd" in exc.message, exc
        t = json.loads(e1.read_text(encoding="utf-8"))
        t["embargo"] = 22
        (tmp / "edited.json").write_text(json.dumps(t), encoding="utf-8", newline="\n")
        assert "owner_confirmed" in _refused(lambda: chk(tmp / "edited.json"), "R-11").message
        for rel in ("tools/nautilus/sandbox.py", "core/quant/validate.py"):
            orig = (root / rel).read_bytes()
            (root / rel).write_bytes(orig + b"\n")
            try:
                assert "owner_confirmed" in _refused(lambda: chk(e1), "R-11").message, rel
            finally:
                (root / rel).write_bytes(orig)
        for seam in ({"child_cmd": stub_cmd()}, {"probe_cmd": stub_probe_cmd()}, {"hooks": {}}, {"timeout": 3},
                     {"ledger_dir": tmp / "ledgers"}, {"register_fn": lambda *a, **k: None}):
            code_, out = _captured(lambda: runner.run(e1, mode="of-record", **seam))
            assert code_ == 2 and "R-11: of-record mode takes no test seam" in out, (seam, out[-500:])
        assert locks.exists() == had_locks
        card = "docs/asset_expansion/cards/S_C3_crypto_trend_btcusd.json"
        (root / card).parent.mkdir(parents=True, exist_ok=True)
        (root / card).write_bytes(b'{"card": "a temp stand-in"}\n')
        c3 = _of_record_table(tmp / "c3.json", "C3-BTCUSD", code, reference_card=card,
                              reference_card_md5=_md5(root / card))
        nocard = _of_record_table(tmp / "c3n.json", "C3-BTCUSD", code)
        assert "reference_card" in _refused(lambda: chk(nocard), "R-11").message
        assert "E1-SPY" in _refused(lambda: chk(c3), "R-11").message
        e1_record = {"mode": "of-record", "pilot": "E1-SPY", "status": "WITHHELD", "table": {"code_sha256": code},
                     "parity": {"hard_pass": False}, "registration": {"rows": [{}] * 12}}
        run_dir = root / "docs" / "nautilus_bridge" / "runs" / "NB-20261101T000000000000Z-00000000"
        run_dir.mkdir(parents=True)
        (run_dir / "run.json").write_text(json.dumps(e1_record), encoding="utf-8", newline="\n")
        assert "E1-SPY" in _refused(lambda: chk(c3), "R-11").message
        e1_record.update(status="WITHHELD", parity={"hard_pass": True})
        (run_dir / "run.json").write_text(json.dumps(e1_record), encoding="utf-8", newline="\n")
        assert "C3.jsonl does not exist" in _refused(lambda: chk(c3), "R-15").message   # the precondition holds


def test_l1_20a_p0a_against_the_study_loaders():
    """L1-20, P0a cases (QUANT-1, QA-R4-1): check_p0a on a synthetic cache dir: equal arrays pass and return the
    study's panel; a doctored study.rf_daily or a doctored close refuses R-13; a cache dir without yf_SPY.csv, and
    one without fred_DGS3MO.csv, refuse R-13 while the stand-in records the blocked download; REFRESH true is R-13;
    sys.modules holds no stand-in afterwards."""
    import numpy as np
    runner = _runner()
    study = runner.load_study(ROOT)
    with tempfile.TemporaryDirectory(prefix="qgnb_l120_") as name:
        tmp = Path(name)
        n, dates = 320, _bdates(320)
        cache = tmp / "cache"
        md5 = _write_prices(cache / "yf_SPY.csv", dates, synth_prices(7, n, 100.0, 150.0))
        rmd5 = _write_rf(cache / "fred_DGS3MO.csv", dates, synth_rf(n))
        p = runner.load_prices(cache / "yf_SPY.csv", md5=md5, start=dates[0], end=dates[-1], instrument="SPY",
                               mode="rehearsal")
        rf, _ = runner.load_rf(cache / "fred_DGS3MO.csv", md5=rmd5, dates=p.dates)
        arrays = {"symbol": "SPY", "start": dates[0], "dates": p.dates, "closes": p.closes, "rf": rf}
        pn = runner.check_p0a(study, cache, arrays)
        assert tuple(pn.dates) == p.dates and pn.prices.shape == (n, 1) and study.CACHE == cache
        assert runner.check_p0a(study, cache, dict(arrays, rf=None)).dates == pn.dates      # pilot 2: no rf

        def no_stand_ins() -> bool:
            return not any(isinstance(sys.modules.get(m), runner._Blocked)
                           for m in ("yfinance", "pandas_datareader", "pandas_datareader.data"))
        assert no_stand_ins()
        real = study.rf_daily
        try:
            study.rf_daily = lambda index: real(index) + 1e-12
            assert "rf differ" in _refused(lambda: runner.check_p0a(study, cache, arrays), "R-13").message
        finally:
            study.rf_daily = real
        closes = p.closes.copy()
        closes[200] += 1e-9
        assert "closes differ" in _refused(lambda: runner.check_p0a(study, cache, dict(arrays, closes=closes)),
                                           "R-13").message
        (tmp / "no_yf").mkdir()
        shutil.copy(cache / "fred_DGS3MO.csv", tmp / "no_yf" / "fred_DGS3MO.csv")
        exc = _refused(lambda: runner.check_p0a(study, tmp / "no_yf", arrays), "R-13")
        assert "yfinance.download" in exc.message and no_stand_ins(), exc
        (tmp / "no_fred").mkdir()
        shutil.copy(cache / "yf_SPY.csv", tmp / "no_fred" / "yf_SPY.csv")
        exc = _refused(lambda: runner.check_p0a(study, tmp / "no_fred", arrays), "R-13")
        assert "rf differ" in exc.message and "pandas_datareader.data" in exc.message and no_stand_ins(), exc
        study.REFRESH = True
        try:
            _refused(lambda: runner.check_p0a(study, cache, arrays), "R-13")
        finally:
            study.REFRESH = False
        assert np.array_equal(pn.prices[:, 0], p.raw)


def test_l1_23_egress_refusals_r14():
    """L1-23 (SECURITY-1, R-14): a stub probe printing {"blocked": false} refuses at step 4; check_egress_record
    refuses a missing record, another base_python, an unblocked probe, a failed control connect and another layer,
    and on Windows accepts paths differing only in case or slash direction (4.3)."""
    runner = _runner()
    with tempfile.TemporaryDirectory(prefix="qgnb_l123_") as name:
        tmp, steps = Path(name), []
        table = _small_table(tmp)
        probe = tmp / "open_probe.py"
        probe.write_text("print('{\"blocked\": false, \"errno\": null, \"error\": \"\"}')\n", encoding="utf-8",
                         newline="\n")
        code, out = _captured(lambda: runner.run(table, mode="rehearsal", ledger_dir=tmp / "ledgers",
                                                 out_dir=tmp / "out", child_cmd=stub_cmd(),
                                                 probe_cmd=[stub_python(), "-I", str(probe)], hooks=_step_hooks(steps)))
        assert code == 2 and "R-14: the egress probe was not blocked" in out and steps == [0, 1, 2, 3], out[-2000:]
        nt = os.name == "nt"
        facts = {"venv_python": r"C:\Users\o\AppData\Local\quantgen\ntvenv\Scripts\python.exe" if nt
                 else "/opt/qg/ntvenv/bin/python",
                 "base_python": r"C:\Users\o\AppData\Local\quantgen\py313\python.exe" if nt else "/usr/bin/python3.13",
                 "layer": runner.LAYER}
        record_dir = tmp / "egress"
        record_dir.mkdir()
        _refused(lambda: runner.check_egress_record(record_dir, facts), "R-14")
        base = {"schema": "nautilus-bridge-egress/1", "platform_tag": launch.host_tag(), **facts,
                "probe": {"blocked": True, "errno": 101, "error": "unreachable"},
                "recorded_utc": "2026-10-28T00:00:00.000000Z", "control_connect": {"ok": True, "error": ""}}

        def put(**changes) -> None:
            (record_dir / f"{launch.host_tag()}.json").write_text(json.dumps({**base, **changes}), encoding="utf-8",
                                                                  newline="\n")
        put()
        runner.check_egress_record(record_dir, facts)
        for changes, word in (({"base_python": facts["base_python"] + "x"}, "base_python"),
                              ({"probe": {"blocked": False, "errno": None, "error": ""}}, "does not prove"),
                              ({"control_connect": {"ok": False, "error": "timeout"}}, "does not prove"),
                              ({"layer": "something else"}, "layer")):
            put(**changes)
            assert word in _refused(lambda: runner.check_egress_record(record_dir, facts), "R-14").message, changes
        if nt:
            put(**{k: facts[k].upper().replace("\\", "/") for k in ("venv_python", "base_python")})
            runner.check_egress_record(record_dir, facts)


def test_l1_24_ledger_and_host_refusals_r15():
    """L1-24 (GOVERNANCE-3; R-15): of-record check_table on temp dirs refuses a missing family ledger, an empty one
    and a host fingerprint off by one character (R-15), and a broken chain (R-09); with the right fingerprint the
    whole of-record table check passes. host_fingerprint is 6.6's sha256, None for a ledger without a row."""
    from core.quant import gate_ledger
    runner = _runner()
    with tempfile.TemporaryDirectory(prefix="qgnb_l124_") as name:
        tmp = Path(name)
        root = _code_root(tmp / "root")
        code, ledgers = runner.code_sha256(root), tmp / "ledgers"
        chk = lambda path: runner.check_table(path, "of-record", ledgers, "qgnb-host", root)   # noqa: E731
        table = _of_record_table(tmp / "t.json", "E1-SPY", code)
        assert "does not exist" in _refused(lambda: chk(table), "R-15").message
        ledgers.mkdir()
        (ledgers / "E1.jsonl").write_bytes(b"")
        assert "holds no row" in _refused(lambda: chk(table), "R-15").message
        ledger = gate_ledger.family_ledger("E1", ledgers)
        gate_ledger.register_trial(ledger, _plain_row("E1", 1))
        fp = runner.host_fingerprint("qgnb-host", ledger)
        assert fp == hashlib.sha256(("qgnb-host\n" + ledger.rows()[0]["row_md5"]).encode("utf-8")).hexdigest()
        assert runner.host_fingerprint("qgnb-host", gate_ledger.family_ledger("C3", ledgers)) is None
        t = json.loads(table.read_text(encoding="utf-8"))
        for value, rid in ((fp[:-1] + ("0" if fp[-1] != "0" else "1"), "R-15"), (fp, None)):
            t["host_fingerprint"] = value                    # outside table_sha256, so owner_confirmed still holds
            table.write_text(json.dumps(t), encoding="utf-8", newline="\n")
            if rid:
                assert "host_fingerprint" in _refused(lambda: chk(table), rid).message
            else:
                assert chk(table) == t
        raw = ledger.path.read_bytes()
        ledger.path.write_bytes(raw.replace(b'"US"', b'"KR"'))
        _refused(lambda: chk(table), "R-09")


def test_l1_25_lock_and_freshness_r16():
    """L1-25 (5.3.5; QA-R2-3, QA-R4-6): take_lock refuses while another handle holds the table lock (flock, not
    lockf, so it conflicts inside one process) and passes after release; a C3.jsonl or family ledger touched now
    refuses, one touched 601 s ago passes; a refused take_lock leaves no lock behind."""
    runner = _runner()
    with tempfile.TemporaryDirectory(prefix="qgnb_l125_") as name:
        tmp = Path(name)
        out, sha = tmp / "out", "ab" * 32
        c3, e1 = tmp / "ledgers" / "C3.jsonl", tmp / "ledgers" / "E1.jsonl"
        lock, earlier = runner.take_lock(out, sha, [c3, e1], None)
        assert earlier == [] and lock.path == out / ".locks" / f"{sha[:16]}.lock"
        try:
            assert "another runner is active" in _refused(lambda: runner.take_lock(out, sha, [c3, e1], None),
                                                          "R-16").message
        finally:
            lock.release()
        runner.take_lock(out, sha, [c3, e1], None)[0].release()
        old = time.time() - 601
        for path in (c3, e1):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"")
            assert "wait" in _refused(lambda: runner.take_lock(out, sha, [c3, e1], None), "R-16").message, path
            os.utime(path, (old, old))
            runner.take_lock(out, sha, [c3, e1], None)[0].release()


def test_l1_26a_lifecycle_records_and_exits():
    """L1-26 without its G-05 case (5.3.5; G-06, G-07, R-12): IN_PROGRESS is on disk after registration; a hook
    raising KeyboardInterrupt gives ABORTED, exit 5; a hook raising ValueError gives ERROR, exit 4, G-06 with the
    traceback; a register_fn raising on the third row gives R-12, REFUSED_REGISTRATION, exit 3, two rows recorded."""
    from core.quant import gate_ledger
    with tempfile.TemporaryDirectory(prefix="qgnb_l126_") as name:
        tmp, seen = Path(name), []
        table = _small_table(tmp / "a")

        def at12(ctx):
            rec = json.loads((ctx.run_dir / "run.json").read_text(encoding="utf-8"))
            seen.append((rec["status"], rec["registration"]["hash_after"], ctx.hash_after_registration,
                         len(rec["children"])))
            raise KeyboardInterrupt
        (code, rec), out = _captured(lambda: run_rehearsal(table, tmp / "a", hooks={"after_step12": at12}))
        h = rec["registration"]["hash_after"]
        assert seen == [("IN_PROGRESS", h, h, 0)] and (code, rec["status"]) == (5, "ABORTED"), (seen, out[-1000:])
        assert rec["error"]["message"] == "G-07: KeyboardInterrupt after registration", rec["error"]
        assert out.splitlines()[-1] == f"STATUS ABORTED exit=5 record={tmp / 'a' / 'out' / rec['bridge_run_id'] / 'run.json'}"
        table = _small_table(tmp / "c")

        def boom(_ctx):
            raise ValueError("planted after step 13")
        (code, rec), out = _captured(lambda: run_rehearsal(table, tmp / "c", hooks={"after_step13": boom}))
        assert (code, rec["status"], rec["children"]) == (4, "ERROR", []), out[-1000:]
        assert rec["error"]["message"] == "G-06: ValueError: planted after step 13" and "boom" in rec["error"]["traceback"]
        table = _small_table(tmp / "d", axes={"rule": ["sma"], "lookback": [126, 210, 252], "step": [21]})
        calls = []

        def third(ledger, row, *, script=None):
            calls.append(row)
            if len(calls) == 3:
                raise OSError("disk full (planted)")
            return gate_ledger.register_trial(ledger, row, script=script)
        (code, rec), out = _captured(lambda: run_rehearsal(table, tmp / "d", register_fn=third))
        assert (code, rec["status"]) == (3, "REFUSED_REGISTRATION"), out[-1000:]
        assert rec["error"]["message"] == "R-12: register_trial raised OSError: disk full (planted)", rec["error"]
        assert [r["col"] for r in rec["registration"]["rows"]] == [0, 1] and rec["children"] == []
        assert gate_ledger.family_ledger("E1", tmp / "d" / "ledgers").n_raw == 2


def test_l1_27_child_failures_and_doctored_manifests():
    """L1-27 (section 7): stubs that exit 1, sleep past timeout=3 (the tree is killed and the call returns), write
    no manifest or write invalid JSON give C-06; a child_started hook raising KeyboardInterrupt while a sleeping stub
    runs gives ABORTED, exit 5, and the temp dir is removed (OPS-R2-4); a wrong --guard-selftest outcome gives R-03
    (QA-R2-10); doctored manifests (valid true, exit 0) give their own id (QA-R3-2)."""
    dirs: list[Path] = []

    def rehearse(*flags: str, **kw):
        tmp = Path(tempfile.mkdtemp(prefix="qgnb_l127_"))
        dirs.append(tmp)
        (code, rec), out = _captured(lambda: run_rehearsal(_small_table(tmp), tmp, flags=flags, **kw))
        return code, rec, out
    try:
        for flags, want in ((("--exit", "1"), "C-06: exit 1"), (("--sleep", "60"), "C-06: timed out after 3 s"),
                            (("--no-manifest",), "C-06: manifest.json missing"),
                            (("--bad-json",), "C-06: manifest.json missing or not a JSON object")):
            started = time.monotonic()
            code, rec, out = rehearse(*flags, timeout=3)
            assert rec is not None and len(rec["children"]) == 2, (flags, out[-1000:])
            assert all(any(r.startswith(want) for r in c["invalid"]) for c in rec["children"]), (
                flags, [c["invalid"] for c in rec["children"]])
            assert time.monotonic() - started < 60 and rec["cleanup_leftovers"] == [], flags
        cwds = []

        def interrupt(lc):
            cwds.append(lc.cwd)
            raise KeyboardInterrupt
        code, rec, out = rehearse("--sleep", "60", hooks={"child_started": interrupt})
        assert (code, rec["status"]) == (5, "ABORTED") and len(cwds) == 1 and not Path(cwds[0]).exists(), out[-1000:]
        assert out.splitlines()[-1].startswith("STATUS ABORTED exit=5 record=")
        code, rec, out = rehearse("--selftest-wrong")
        assert (code, rec) == (2, None) and "R-03: --guard-selftest misbehaved" in out, out[-1000:]
        for cid in ("C-01", "C-02", "C-03", "C-04", "C-07", "C-09", "C-11", "C-14", "C-15"):
            code, rec, out = rehearse("--doctor", cid)
            assert rec is not None and len(rec["children"]) == 2, (cid, out[-1000:])
            for c in rec["children"]:
                assert c["returncode"] == 0 and c["manifest"]["valid"] is True, (cid, c["returncode"])
                assert any(r.startswith(f"{cid}: ") for r in c["invalid"]), (cid, c["invalid"])
    finally:
        for d in dirs:
            shutil.rmtree(d, ignore_errors=True)


def test_l1_33_goldens_equal_the_spec_tables():
    """L1-33 (QA-R2-6, QA-R3-8): the committed F1, F2 and N1 goldens, in C1's JSON bytes, equal 8.2's tables typed
    in above, compared as 6.8 says (strings and integers exactly, money within 0.005, reasons by id)."""
    runner = _runner()
    for name, want in GOLDEN_SPEC.items():
        raw = (GOLDEN_DIR / f"{name}.json").read_bytes()
        got = json.loads(raw)
        assert raw == (json.dumps(got, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8"), name
        assert set(got) == set(want) and runner.compare_golden(got, want) == [], (
            name, runner.compare_golden(got, want))
    f1, n1 = GOLDEN_SPEC["F1"], GOLDEN_SPEC["N1"]
    assert runner.compare_golden(dict(f1, final_cash="926593.004"), f1) == []
    assert runner.compare_golden(dict(f1, final_cash="926593.006"), f1) == [
        "final_cash: '926593.006' != '926593.00'"]
    assert runner.compare_golden(dict(f1, fills=[dict(f1["fills"][0], price="100.00")] + f1["fills"][1:]), f1) == [
        "fill 0 price: '100.00' != '100.000000000'"]
    assert runner.compare_golden(dict(n1, invalid_reasons=["C-01: other words", "C-02: x"]), n1) == []


def test_l1_34_write_record_retries_and_fallback():
    """L1-34 (OPS-R2-3, QA-R3-7): write_record retries a replace that raises PermissionError twice (no-op sleep) and
    writes; one that always raises leaves the old bytes and raises after 10 attempts; a run whose every record write
    fails lists the intermediate writes and falls back to run.final.<pid>.json, which the STATUS line names."""
    runner = _runner()
    with tempfile.TemporaryDirectory(prefix="qgnb_l134_") as name:
        tmp = Path(name)
        path = tmp / "w" / "run.json"
        path.parent.mkdir()
        path.write_text("{}\n", encoding="utf-8", newline="\n")
        calls, sleeps = [], []

        def flaky(src, dst):
            calls.append(src)
            if len(calls) <= 2:
                raise PermissionError(13, "held by the indexer (planted)")
            os.replace(src, dst)
        obj = {"status": "IN_PROGRESS", "children": [1, 2]}
        runner.write_record(path, obj, replace=flaky, sleep=sleeps.append)
        assert json.loads(path.read_text(encoding="utf-8")) == obj and len(calls) == 3 and sleeps == [0.5, 0.5]
        assert b"\r" not in path.read_bytes() and sorted(p.name for p in path.parent.iterdir()) == ["run.json"]

        def never(src, dst):
            raise PermissionError(13, "always held (planted)")
        try:
            runner.write_record(path, {"status": "ERROR"}, replace=never, sleep=sleeps.append)
        except PermissionError:
            pass
        else:
            raise AssertionError("write_record did not raise after 10 attempts")
        assert json.loads(path.read_text(encoding="utf-8")) == obj and len(sleeps) == 2 + 9, len(sleeps)
        assert sorted(p.name for p in path.parent.iterdir()) == ["run.json"]
        table = _small_table(tmp / "r")
        real = runner.write_record
        runner.write_record = lambda p, o, **kw: real(p, o, replace=never, sleep=lambda _s: None)
        try:
            def stop(_ctx):
                raise KeyboardInterrupt
            (code, rec), out = _captured(lambda: run_rehearsal(table, tmp / "r", hooks={"after_step15": stop}))
        finally:
            runner.write_record = real
        finals = list((tmp / "r" / "out").glob("NB-*/run.final.*.json"))
        assert (code, rec) == (5, None) and [f.name for f in finals] == [f"run.final.{os.getpid()}.json"], out[-1000:]
        final = json.loads(finals[0].read_text(encoding="utf-8"))
        assert final["status"] == "ABORTED" and len(final["children"]) == 2, final["status"]
        assert [f.split(":")[0] for f in final["record_write_failures"]] == [
            "IN_PROGRESS", "child 0 x1", "child 0 x2", "final"], final["record_write_failures"]
        assert out.splitlines()[-1] == f"STATUS ABORTED exit=5 record={finals[0]}", out[-500:]


def test_l1_35_record_baseline_rules():
    """L1-35 (5.2.7; OPS-R3-2, OPS-R4-2, OPS-R5-3, QA-R4-4): record_baseline on a temp golden dir: a new file is
    written in C1's bytes; a tracked equal baseline gives exit 0 "unchanged"; a tracked different one gives exit 2,
    the diff and the removal line and leaves the bytes; an untracked different one is replaced, its diff printed,
    exit 0; a tracked path with no file, as after the removal line, is written, exit 0."""
    runner = _runner()
    with tempfile.TemporaryDirectory(prefix="qgnb_l135_") as name:
        golden = Path(name)
        census = ["_io", "json", "msgspec", "nautilus_trader", "nautilus_trader.backtest.engine"]
        path = golden / "modules_test_tag.json"
        assert runner.record_baseline(golden, "test_tag", census, tracked=False, python="3.13.17") == (
            0, ["+ STD _io", "+ STD json", "+ TP msgspec", "+ NT nautilus_trader",
                "+ NT nautilus_trader.backtest.engine", "written modules_test_tag.json"])
        written = json.loads(path.read_text(encoding="utf-8"))
        assert written == {"schema": "nautilus-bridge-census/1", "platform_tag": "test_tag", "python": "3.13.17",
                           "recorded_from": ["F1", "F2"], "census": census}, written
        before = path.read_bytes()
        assert before == (json.dumps(written, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
        assert runner.record_baseline(golden, "test_tag", list(reversed(census)), tracked=True) == (0, ["unchanged"])
        code, lines = runner.record_baseline(golden, "test_tag", census + ["plotly"], tracked=True)
        removal = ("Remove-Item tools\\nautilus\\golden\\modules_test_tag.json" if os.name == "nt"
                   else "rm tools/nautilus/golden/modules_test_tag.json")
        assert code == 2 and lines[0] == "+ TP plotly" and lines[-1] == removal and path.read_bytes() == before, lines
        assert runner.record_baseline(golden, "test_tag", census[:-1], tracked=False) == (
            0, ["- NT nautilus_trader.backtest.engine", "written modules_test_tag.json"])
        assert json.loads(path.read_text(encoding="utf-8"))["census"] == census[:-1]
        path.unlink()
        code, lines = runner.record_baseline(golden, "test_tag", census, tracked=True)
        assert code == 0 and lines[-1] == "written modules_test_tag.json" and path.is_file(), lines


def test_l2_02_f1_f2_match_goldens():
    """L2-2 (K6, QA-12): F1 and F2 through the exact launch contract match their committed goldens and 8.2; each
    manifest is valid with run_analysis false and stats_pnls_empty true."""
    python = layer2()
    runner = _runner()
    unshare = launch.resolve_unshare()
    for name in ("F1", "F2"):
        got = runner.run_fixture(name, python, unshare)
        want = json.loads((GOLDEN_DIR / f"{name}.json").read_text(encoding="utf-8"))
        assert runner.compare_golden(got["golden"], want) == [], (name, runner.compare_golden(got["golden"], want))
        assert runner.compare_golden(got["golden"], GOLDEN_SPEC[name]) == [], name
        m = got["manifest"]
        assert got["result"].returncode == 0 and m["valid"] is True, (name, got["result"].stderr_tail[-500:])
        assert m["engine"]["run_analysis"] is False and m["result"]["stats_pnls_empty"] is True, m["engine"]


def test_l2_03_n1_matches_golden():
    """L2-3 (QA-2): N1 (volume 4000, 2 price decimals) matches its golden: one fill, a forced stop, 4 of 12 bars,
    exit 10 with C-01 and C-02, which the parent re-derives from the manifest (5.2.7)."""
    python = layer2()
    runner = _runner()
    got = runner.run_fixture("N1", python, launch.resolve_unshare())
    want = json.loads((GOLDEN_DIR / "N1.json").read_text(encoding="utf-8"))
    assert runner.compare_golden(got["golden"], want) == [] and runner.compare_golden(got["golden"], GOLDEN_SPEC["N1"]) == []
    raw, bars = launch.fixture_inputs("N1")
    _, ts, _ = _fixture_series("N1")
    m = got["manifest"]
    reasons = runner.manifest_reasons(m, n_bars=12, first_ts=ts[0], last_ts=ts[-1],
                                      bars_sha256=hashlib.sha256(bars).hexdigest(),
                                      input_sha256=hashlib.sha256(raw).hexdigest(),
                                      ledger_hash=json.loads(raw)["ledger_hash_after_registration"],
                                      check_env={"precision": m["precision"], "environment": "BACKTEST"})
    assert [r.split(":")[0] for r in reasons] == ["C-01", "C-02"], reasons


def test_l2_06_census_matches_platform_baseline():
    """L2-6 (5.2.7; QA-R3-12): the F1 and F2 import censuses match this platform's committed baseline under 5.2.7's
    rule (NT and TP sets equal, no adapters or network module)."""
    python = layer2()
    runner = _runner()
    tag = launch.read_venv(python)["wheel"]["platform_tag"]
    path = GOLDEN_DIR / f"modules_{tag}.json"
    assert path.is_file(), f"no census baseline {path.name}: runner --fixtures --record-baseline records it"
    rec = json.loads(path.read_text(encoding="utf-8"))
    assert (rec["schema"], rec["platform_tag"], rec["recorded_from"]) == ("nautilus-bridge-census/1", tag, ["F1", "F2"])
    assert rec["census"] == sorted(set(rec["census"])), "the census is sorted and unique"
    unshare = launch.resolve_unshare()
    for name in ("F1", "F2"):
        got = runner.run_fixture(name, python, unshare)
        assert got["census"] and runner.judge_census(got["census"], rec["census"]) == [], (
            name, runner.judge_census(got["census"], rec["census"]))


# --------------------------------------------------------------------------- #
# Plan Task 5 (spec Step 7): parity, selection, gate hand-off, card, pilot tables and the three new runner modes
# --------------------------------------------------------------------------- #
REGISTRATION = ROOT / "docs" / "nautilus_bridge" / "registration"
PILOT_TABLES = {"E1-SPY": REGISTRATION / "pilot1_E1_spy.json", "C3-BTCUSD": REGISTRATION / "pilot2_C3_btcusd.json"}
CARDS = ROOT / "docs" / "asset_expansion" / "cards"
CARD_AXES = {"rule": ["sma", "tsmom"], "lookback": [126, 252], "step": [21]}   # the L2-7 grid: four columns
PILOT1_AXES = {"rule": ["sma", "tsmom"], "lookback": [126, 210, 252], "step": [21, 42]}
PILOT2_AXES = {"hysteresis": [0.0, 0.222, 0.444, 0.667, 0.889]}
ENGINE_6_5 = ("per-column event-driven replication (nautilus_trader 1.231.0 BacktestEngine, same-bar close); "
              "walk-forward column switches are not executed in either engine")
SCOPE_6_5 = "parity validates the engine, not the data; P0 ties the inputs to the study's loaders"
F1_DECISIONS = ((3, 1, "buy"), (5, 0, "sell"), (7, 1, "buy"), (9, 1, "hold"), (11, 0, "sell"))      # spec 8.2
N8_BASE = {"sr_oos": 1.19, "se_lo": 0.3, "ci90": (0.72, 1.64), "sr_is": 1.3, "oos_is": 0.9, "dsr": 0.9999, "pbo": 0.19,
           "pbo_slope": 0.0, "prob_loss_oos": 0.0, "sr_stress": 1.16, "turnover_annual": 10.0, "n_trades": 144,
           "n_sessions": 3634, "years_positive": 0.82, "n_years": 11, "max_year_share": 0.2, "plateau": 1.0,
           "edge": False, "regime": {}, "total_return": 5.0, "max_drawdown": -0.5, "haircut_sr": 0.7, "bench_sr": 0.9,
           "n_trials": 11, "n_configs": 5, "bench_diff": 0.3, "bench_p": 0.07}     # near pilot 2's stored card (N8)


def _parity():
    """tools.nautilus.parity, imported by each test that needs it, so a missing module fails only Task 5's tests."""
    from tools.nautilus import parity
    return parity


def _days(n: int) -> list[str]:
    """Spec 8.2's crypto calendar: pd.date_range("2001-01-01", periods=n, freq="D")."""
    import pandas as pd
    return [d.strftime("%Y-%m-%d") for d in pd.date_range("2001-01-01", periods=n, freq="D")]


def _card_table(tmp: Path, **fields) -> Path:
    """A synthetic SPY-like table whose stub-child rehearsal ends CARD_WRITTEN: synth_prices(7, 1000, 100, 150),
    synth_rf(1000), the four columns of CARD_AXES at 50 bp, embargo 21."""
    return write_rehearsal_table(tmp, prices=synth_prices(7, 1000, 100.0, 150.0), dates=_bdates(1000),
                                 rf=synth_rf(1000), axes=CARD_AXES, **fields)


def _rehearse(table: Path, tmp: Path, **kw) -> tuple[int, dict | None, str]:
    """run_rehearsal with stdout captured: (exit code, the newest run.json, what the runner printed)."""
    (code, rec), out = _captured(lambda: run_rehearsal(table, tmp, **kw))
    return code, rec, out


def _f1_leg(stress: int, *, rf, commissions=None, echo_stress=None):
    """A Leg of F1 (spec 8.2) from its golden fills, rebuilt by the runner; commissions and the manifest's stress echo
    can be planted."""
    from decimal import Decimal
    runner = _runner()
    capital, ts, closes = _fixture_series("F1")
    fills = [{"ts_event": ts[b], "order_side": side, "last_qty": Decimal(q), "last_px": Decimal(px),
              "commission": Decimal(c if commissions is None else commissions[k]), "commission_ccy": "USD",
              "trade_id": f"T{k}", "venue_order_id": f"O{k}"} for k, (b, side, q, px, c) in enumerate(SPEC_FILLS["F1"])]
    decisions = [{"i": i, "ts_event": ts[i], "decision": d, "margin": 0.0, "action": a} for i, d, a in F1_DECISIONS]
    manifest = {"input": {"cost_bps": "50", "stress": str(echo_stress or stress)}}
    rebuilt = runner.rebuild_returns(fills, closes, ts, rf, Decimal(capital))
    return runner.Leg(0, stress, {}, manifest, fills, decisions, [], rebuilt, [])


def _f1_checks(leg, weights, rf) -> dict:
    """parity.leg_checks on F1 with QUANTGEN's pnl at the leg's cost level from `weights`."""
    from core.quant import strategies as S
    _, _, closes = _fixture_series("F1")
    pnl, turnover = S.simulate(closes, weights[:, None], cost_bps=50.0 * leg.stress, cash_daily=rf)
    return _parity().leg_checks(leg, strategy="trend_switch", theta={"rule": "sma", "lookback": 3, "step": 2},
                                closes=closes, rf=rf, weights=weights, pnl=pnl, turnover=turnover, cost_bps=50.0)


def _failed(x: dict) -> list[str]:
    return [p for p in _parity().HARD if p in x and not x[p]["pass"]]


def _qg_matrices(closes, fn, grid, cost: float, rf):
    """QUANTGEN's pnl, pnl at 2x and turnover, column by column as the runner's step 13 computes them."""
    import numpy as np
    from core.quant import strategies as S
    cols = [S.simulate(closes, np.asarray(fn(closes, **g), dtype=float), cost_bps=cost, cash_daily=rf) for g in grid]
    stress = [S.simulate(closes, np.asarray(fn(closes, **g), dtype=float), cost_bps=2 * cost, cash_daily=rf)[0]
              for g in grid]
    return np.column_stack([c[0] for c in cols]), np.column_stack(stress), np.column_stack([c[1] for c in cols])


def _same_wf(a, b) -> list[str]:
    """The fields where two WalkForward objects differ, arrays compared by their bytes."""
    import numpy as np
    out = []
    for k in ("dates", "origins", "chosen", "n_configs", "note"):
        out += [k] if getattr(a, k) != getattr(b, k) else []
    for k in ("pnl", "pnl_stress", "turnover", "is_sharpes"):
        x, y = np.asarray(getattr(a, k)), np.asarray(getattr(b, k))
        out += [k] if x.shape != y.shape or x.dtype != y.dtype or x.tobytes() != y.tobytes() else []
    return out


def _reference_stats(closes, dates, grid, *, cost: float, embargo: int, n_trials: int, domain) -> tuple:
    """The stored-card reference as the study built it (L2-12, L1-29): asdict(score_strategy) of QUANTGEN's matrix,
    plus chosen_last, with n_years by the calendar-years rule that wrote the stored cards. Returns (stats, sc, wf)."""
    import numpy as np
    from dataclasses import asdict
    from core.quant import strategies as S, validate
    pnl, stress, turnover = _qg_matrices(closes, S.crypto_trend, grid, cost, np.zeros(len(closes)))
    wf = validate.walk_forward(pnl, dates[1:], turnover=turnover, pnl_stress=stress, embargo=embargo)
    bench = dict(zip(dates[1:], closes[1:] / closes[:-1] - 1.0))
    sc = validate.score_strategy(wf, grid=grid, full_pnl=pnl, n_trials=n_trials,
                                 bench_daily=np.array([bench[d] for d in wf.dates]), seed=11, domain=domain)
    stats = {k: v for k, v in asdict(sc).items() if k not in ("lines", "regime")}
    stats.update(chosen_last=grid[wf.chosen[-1]], n_years=len({d[:4] for d in wf.dates}))
    return stats, sc, wf


def _write_card_file(path: Path, stats: dict) -> str:
    path.write_text(json.dumps({"card_id": "S_REHEARSAL_reference", "stats": stats}, indent=1, ensure_ascii=False),
                    encoding="utf-8", newline="\n")
    return _md5(path)


def _crypto_table(tmp: Path, n: int, **fields) -> Path:
    """A synthetic BTC-like table (spec 8.2's L2-12 generator, n days from 2001-01-01), pilot 2's grid, no rf."""
    return write_rehearsal_table(tmp, like="C3-BTCUSD", prices=synth_prices(5, n, 400.0, 60000.0), dates=_days(n),
                                 axes=PILOT2_AXES, **fields)


def test_l1_02_parity_functions():
    """L1-2 (5.4.1, 5.5; N2, N4, N7, N8): F1 and F1r meet 8.2's assertions (P1 = 1, P4, P7) and stay inside the P10
    bound; N2 fails P1, P2 and P4; the P1 exemption takes a 1e-10 QUANTGEN margin, not 2e-9; P7's tie (0.13 passes,
    0.12 fails) and N7 (ii) to (iv); N4's P11 mismatches at gap 0 with QUANTGEN's selection kept; N8 through
    parity.agree; a planted P5 warning still writes a card; a Nautilus score planted REJECT is WITHHELD with the
    hand-off's full G-02 text."""
    import dataclasses
    import numpy as np
    from decimal import Decimal
    from core.quant import strategies as S, validate
    parity = _parity()
    _, ts, closes = _fixture_series("F1")
    W = np.asarray(S.trend_switch(closes, rule="sma", lookback=3, step=2), dtype=float)[:, 0]
    for rf in (np.zeros(12), np.full(12, 0.0001)):                      # F1, F1r: 8.2's assertions
        x = _f1_checks(_f1_leg(1, rf=rf), W, rf)
        assert x["P1"]["value"] == 1.0 and x["P10"]["rows_over"] == [] and x["P4"]["pass"] and x["P7"]["pass"], x
        assert x["P4"]["fill_bars"] == [3, 5, 7] and abs(x["P10"]["max_gap"] - 1.742e-4) < 1e-6, x["P10"]
    flipped = W.copy()
    flipped[9:11] = 0.0                                                 # N2: the hold at bar 9 flipped to off
    x = _f1_checks(_f1_leg(1, rf=np.zeros(12)), flipped, np.zeros(12))
    assert x["P1"]["value"] < 1 and {"P1", "P2", "P4"} <= set(_failed(x)), x
    margins = np.full(12, 0.5)
    for planted, exempt in ((1e-10, True), (2e-9, False)):
        margins[9] = planted
        got = parity.p1(_f1_leg(1, rf=np.zeros(12)).decisions, flipped, margins, [3, 5, 7, 9, 11])
        assert got["pass"] is exempt and got["mismatches"] == [9] and len(got["exempt"]) == int(exempt), got
    tie = [{"last_qty": Decimal(25), "last_px": Decimal("1.00"), "commission": Decimal(c), "commission_ccy": "USD"}
           for c in ("0.13", "0.12")]
    echo = {"input": {"cost_bps": "50", "stress": "1"}}
    assert parity.cents(Decimal("0.125")) == 13 and parity.p7(tie[:1], echo, cost_bps=50.0, stress=1)["pass"]
    assert not parity.p7(tie[1:], echo, cost_bps=50.0, stress=1)["pass"]
    half = [c for *_, c in SPEC_FILLS["F1"]]                            # 1x commissions on a 2x leg
    x = _f1_checks(_f1_leg(2, rf=np.zeros(12), commissions=half), W, np.zeros(12))
    assert x["P7"]["bad_fills"] == [0, 1, 2, 3] and x["P7"]["echo"] is True and "P7" in _failed(x), x["P7"]   # N7 (ii)
    x = _f1_checks(_f1_leg(2, rf=np.zeros(12), commissions=half, echo_stress=1), W, np.zeros(12))
    assert x["P7"]["bad_fills"] == [0, 1, 2, 3] and x["P7"]["echo"] is False, x["P7"]               # N7 (iii)
    n = 1500
    dates, closes2 = _bdates(n)[1:], synth_prices(11, n, 100.0, 150.0)
    grid = S.grid_from(**PILOT1_AXES)
    pnl, stress, turnover = _qg_matrices(closes2, S.trend_switch, grid, 50.0, 0.0)
    wf_qg = validate.walk_forward(pnl, dates, turnover=turnover, pnl_stress=stress, embargo=21)
    wf_i = parity.select_matched(pnl, pnl, turnover, dates, wf_qg, embargo=21)                       # N7 (i)
    p12_i = parity.p12(wf_qg, wf_i)
    p3_2x = [parity.pair_checks(pnl[:, g], stress[:, g])["abs_dsr"] for g in range(len(grid))]
    print(f"N7 (i): P12 2x {p12_i['2x']}; P3 at 2x per column, max {max(p3_2x):.5f} (bar 0.01)")
    assert p12_i["1x"]["pass"] and not p12_i["2x"]["pass"] and max(p3_2x) > parity.BARS["P3"], (p12_i, p3_2x)
    shifted = pnl + 0.0001                                                                            # N7 (iv)
    wf_iv = parity.select_matched(shifted, stress + 0.0001, turnover, dates, wf_qg, embargo=21)
    pairs = [parity.pair_checks(shifted[:, g], pnl[:, g]) for g in range(len(grid))]
    assert all(p["corr"] >= parity.BARS["P2"] and p["abs_dsr"] > parity.BARS["P3"] for p in pairs), pairs
    p12_iv = parity.p12(wf_qg, wf_iv)["1x"]
    assert p12_iv["corr"] >= parity.BARS["P2"] and p12_iv["abs_dsr"] > parity.BARS["P3"] and not p12_iv["pass"], p12_iv
    base = np.random.default_rng(3).normal(0.0004, 0.01, size=(1000, 1))                            # N4
    M = np.hstack([base, base])
    Mn = M.copy()
    Mn[:, 1] += 1e-6
    d4 = _bdates(1001)[1:]
    wf4 = validate.walk_forward(M, d4, turnover=np.zeros_like(M), pnl_stress=M, embargo=21)
    own = validate.walk_forward(Mn, d4, turnover=np.zeros_like(M), pnl_stress=Mn, embargo=21)
    rep = parity.p11(wf4, own)
    assert rep and all(r["quantgen"] == 0 and r["nautilus"] == 1 and r["is_sharpe_gap"] == 0.0 for r in rep), rep
    matched = parity.select_matched(Mn, Mn, np.zeros_like(M), d4, wf4, embargo=21)
    assert matched.chosen == wf4.chosen and parity.p12(wf4, matched)["1x"]["pass"], matched.chosen

    def scored(**kw):
        s = validate.StrategyScore(**dict(N8_BASE, **kw))
        validate._decide_strategy(s)
        return s
    gate = validate.GATE
    assert parity.agree(scored(pbo=0.19), scored(pbo=0.21), gate) == (True, None)                     # N8 (a)
    assert parity.agree(scored(n_configs=12, bench_p=0.5, prob_loss_oos=0.09),
                        scored(n_configs=12, bench_p=0.5, prob_loss_oos=0.11), gate) == (False, "decision mismatch")
    assert parity.agree(scored(prob_loss_oos=0.09), scored(prob_loss_oos=0.11), gate) == (False, "decision mismatch")
    assert parity.agree(scored(bench_p=float("nan")), scored(bench_p=float("nan")), gate) == (
        False, "benchmark test dropped")
    preds = parity.gate_predicates(scored(), gate)
    assert len(preds) == 18 and all(type(v) is bool for v in preds.values()), preds

    def plant_p5(ctx):                       # one fill 2e-6 above its close; its commission recomputed, so P7 holds
        leg = ctx.legs[(0, 1)]
        f = leg.fills[0]
        f["last_px"] = (f["last_px"] * Decimal("1.000002")).quantize(Decimal("0.000000001"))
        f["commission"] = Decimal(parity.cents(f["last_qty"] * f["last_px"] * Decimal("0.005"))) / 100
    scores = []

    def nautilus_rejects(wf, **kw):          # G-02 through the hand-off: the second score (sc_nt) says REJECT
        scores.append(validate.score_strategy(wf, **kw))
        return dataclasses.replace(scores[-1], decision="REJECT") if len(scores) == 2 else scores[-1]
    with tempfile.TemporaryDirectory(prefix="qgnb_l102_") as name:
        tmp = Path(name)
        code, rec, out = _rehearse(_card_table(tmp), tmp, hooks={"after_step15": plant_p5})
        assert (code, rec["status"]) == (0, "CARD_WRITTEN"), out[-1500:]
        assert [w for w in rec["parity"]["warnings"] if w.startswith("P5: column 0")] and rec["parity"]["hard_pass"]
        code, rec, out = _rehearse(_card_table(tmp / "g02"), tmp / "g02", score_fn=nautilus_rejects)
        q = rec["gate"]["quantgen"]["decision"]
        want = f"G-02: decision mismatch: quantgen {q}, nautilus REJECT; predicates differ: none"
        assert (code, rec["status"], rec["card"], rec["withheld_reasons"]) == (1, "WITHHELD", None, [want]), out[-1500:]
        assert q != "REJECT" and rec["gate"]["agree"] == {"ok": False, "reason": "decision mismatch"}, rec["gate"]


def test_l1_05_rerun_policy_r17():
    """L1-5 (5.3.5; OPS-R2-7, OPS-R3-5, QA-R3-3, QA-R2-3): after a first run ends CARD_WRITTEN, the same table
    refuses with R-17, also with a new owner_confirmed and re-saved with a BOM and CRLF; with --rerun-of and a reason
    it appends 0 rows, records appended false for every row, names the first run in earlier_runs and supersedes, and
    prints a planted IN_PROGRESS record."""
    from core.quant import gate_ledger
    runner = _runner()
    with tempfile.TemporaryDirectory(prefix="qgnb_l105_") as name:
        tmp = Path(name)
        table = _card_table(tmp)
        code, first, out = _rehearse(table, tmp)
        assert (code, first["status"]) == (0, "CARD_WRITTEN"), out[-1500:]
        ledger = tmp / "ledgers" / "E1.jsonl"
        old = time.time() - 601
        os.utime(ledger, (old, old))                    # R-16's freshness passes from here on (QA-R2-3)
        t = json.loads(table.read_text(encoding="utf-8"))
        sha = runner.table_sha256(t)
        signed = tmp / "signed.json"
        confirmed = f"Geon Koh, 2026-10-28, table {sha[:16]}, code {'0' * 16}"
        signed.write_text(json.dumps(dict(t, owner_confirmed=confirmed), indent=1, ensure_ascii=False),
                          encoding="utf-8", newline="\n")
        bom = tmp / "bom.json"
        crlf = json.dumps(t, indent=1, ensure_ascii=False).replace("\n", "\r\n")
        bom.write_bytes(b"\xef\xbb\xbf" + crlf.encode("utf-8"))
        for path in (table, signed, bom):
            code, rec, out = _rehearse(path, tmp)
            assert code == 2 and rec["bridge_run_id"] == first["bridge_run_id"], (path.name, out[-800:])
            assert f"R-17: earlier runs of this table: {first['bridge_run_id']} CARD_WRITTEN" in out, out[-800:]
        planted = tmp / "out" / f"NB-20000101T000000000000Z-{sha[:8]}"
        planted.mkdir()
        (planted / "run.json").write_text(json.dumps({"bridge_run_id": planted.name, "status": "IN_PROGRESS",
                                                      "table": {"table_sha256": sha}}), encoding="utf-8", newline="\n")
        code, rec, out = _rehearse(table, tmp, rerun_of=first["bridge_run_id"], reason="L1-5 re-run")
        assert code == 0 and rec["bridge_run_id"] != first["bridge_run_id"], out[-1500:]
        assert f"earlier run {planted.name} ended IN_PROGRESS" in out, out[-1500:]
        assert rec["supersedes"] == first["bridge_run_id"] and rec["rerun_reason"] == "L1-5 re-run", rec["supersedes"]
        assert {e["bridge_run_id"] for e in rec["earlier_runs"]} == {first["bridge_run_id"], planted.name}
        reg = rec["registration"]
        assert reg["n_raw_before"] == reg["n_raw_after"] == 4 and not any(r["appended"] for r in reg["rows"]), reg
        assert gate_ledger.family_ledger("E1", tmp / "ledgers").n_raw == 4


def test_l1_13_parity_failure_withholds_without_card():
    """L1-13 (G-01): a parity failure (the stub's --fee-1x charges 1x at stress 2, N7) writes no card and exactly one
    WITHHELD record into the temp output dir, exit 1."""
    with tempfile.TemporaryDirectory(prefix="qgnb_l113_") as name:
        tmp = Path(name)
        code, rec, out = _rehearse(_small_table(tmp, n=600), tmp, flags=("--fee-1x",))
        assert (code, rec["status"], rec["card"]) == (1, "WITHHELD", None), out[-1500:]
        assert any(r.startswith("P7: column 0 (rule=sma, lookback=126, step=21), 2x") for r in rec["withheld_reasons"])
        assert rec["parity"]["hard_pass"] is False and rec["gate"]["quantgen"] is None, rec["gate"]
        assert sorted(p.name for p in (tmp / "out").iterdir() if p.name != ".locks") == [rec["bridge_run_id"]]
        assert sorted(p.name for p in (tmp / "out" / rec["bridge_run_id"]).iterdir()) == ["run.json"]
        assert out.splitlines()[-1].startswith("STATUS WITHHELD exit=1 record=")


def test_l1_14_gate_unchanged_and_g04():
    """L1-14 (5.5 step 6): GATE is deep-equal before and after a synthetic end-to-end scoring that writes a card; a
    score_fn that mutates GATE gives G-04: ERROR, exit 4, no card."""
    import copy
    from core.quant import validate
    saved = copy.deepcopy(validate.GATE)

    def mutating(wf, **kw):
        validate.GATE["dsr_min"] = 0.5
        return validate.score_strategy(wf, **kw)
    try:
        with tempfile.TemporaryDirectory(prefix="qgnb_l114_") as name:
            tmp = Path(name)
            code, rec, out = _rehearse(_card_table(tmp / "a"), tmp / "a")
            assert (code, rec["status"]) == (0, "CARD_WRITTEN") and validate.GATE == saved, out[-1500:]
            code, rec, out = _rehearse(_card_table(tmp / "b"), tmp / "b", score_fn=mutating)
            assert (code, rec["status"], rec["card"]) == (4, "ERROR", None), out[-1500:]
            want = "G-04: GATE differs from its snapshot after scoring: ['dsr_min']"
            assert rec["error"]["message"] == want, rec["error"]
            assert not list((tmp / "b" / "out" / rec["bridge_run_id"]).glob("NB_*.json"))
            assert out.splitlines()[-1].startswith("STATUS ERROR exit=4 record=")
    finally:
        validate.GATE.clear()
        validate.GATE.update(saved)


def test_l1_20b_p0b_benchmark_withholds():
    """L1-20's P0b case (5.4.1; QUANT-1): the benchmark from the runner's rounded closes equals the study's
    expression on the study's prices, byte for byte; a doctored study panel (one price moved by 1e-6 after step 15)
    withholds with P0b, exit 1, and the record's provenance says so."""
    import dataclasses
    from types import SimpleNamespace
    import numpy as np
    parity = _parity()
    closes = synth_prices(7, 600, 100.0, 150.0)
    assert parity.p0b("trend_switch", closes, closes[:, None])["pass"] and parity.p0b("crypto_trend", closes,
                                                                                    closes[:, None])["pass"]
    for strategy, text in parity.STUDY_BENCH.items():
        pn = SimpleNamespace(prices=closes[:, None])
        expected = np.asarray(eval(text, {"pn": pn}))                # the study's own text, evaluated
        assert parity.study_benchmark(strategy, closes[:, None]).tobytes() == expected.tobytes(), strategy

    def doctor(ctx):
        prices = np.array(ctx.study_pn.prices, dtype=float)
        prices[300, 0] += 1e-6
        ctx.study_pn = dataclasses.replace(ctx.study_pn, prices=prices)
    with tempfile.TemporaryDirectory(prefix="qgnb_l120b_") as name:
        tmp = Path(name)
        code, rec, out = _rehearse(_small_table(tmp / "a", n=600), tmp / "a")
        assert rec["provenance"]["p0b"]["pass"] is True, rec["provenance"]
        assert not any(r.startswith("P0b") for r in rec["withheld_reasons"]), rec["withheld_reasons"]
        code, rec, out = _rehearse(_small_table(tmp / "b", n=600), tmp / "b", hooks={"after_step15": doctor})
        assert (code, rec["status"], rec["card"]) == (1, "WITHHELD", None), out[-1500:]
        assert rec["provenance"]["p0b"] == {"pass": False, "rows": 599, "study_rows": 599, "first_difference": 299}
        assert any(r.startswith("P0b: the benchmark differs") for r in rec["withheld_reasons"]), rec["withheld_reasons"]


def test_l1_21_select_matched_reproduces_wf_qg():
    """L1-21 (5.4.2): select_matched on QUANTGEN's own matrices reproduces walk_forward's result field by field, bit
    for bit, for pilot 1's grid (embargo 21, with a cash rate) and pilot 2's (embargo 1)."""
    import numpy as np
    from core.quant import strategies as S, validate
    parity = _parity()
    cases = (("trend", synth_prices(7, 1500, 100.0, 150.0), _bdates(1500), S.trend_switch, PILOT1_AXES, 50.0,
              synth_rf(1500), 21),
             ("crypto", synth_prices(5, 1600, 400.0, 60000.0), _days(1600), S.crypto_trend, PILOT2_AXES, 10.0,
              np.zeros(1600), 1))
    for label, closes, dates, fn, axes, cost, rf, embargo in cases:
        grid = S.grid_from(**axes)
        pnl, stress, turnover = _qg_matrices(closes, fn, grid, cost, rf)
        wf = validate.walk_forward(pnl, dates[1:], turnover=turnover, pnl_stress=stress, embargo=embargo)
        got = parity.select_matched(pnl, stress, turnover, dates[1:], wf, embargo=embargo)
        assert len(wf.origins) > 3 and _same_wf(got, wf) == [], (label, _same_wf(got, wf))


def test_l1_26b_ledger_moved_g05():
    """L1-26's G-05 case (5.5 step 7): an after_step16 hook that appends a row to the family ledger after
    registration makes assert_hash_at_run raise: WITHHELD "ledger moved after registration", exit 1, no card."""
    from core.quant import gate_ledger
    with tempfile.TemporaryDirectory(prefix="qgnb_l126b_") as name:
        tmp = Path(name)

        def append(ctx):
            gate_ledger.register_trial(ctx.ledger, _plain_row("E1", 99), script="tests/nautilus_acceptance.py")
        code, rec, out = _rehearse(_card_table(tmp), tmp, hooks={"after_step16": append})
        assert (code, rec["status"], rec["card"]) == (1, "WITHHELD", None), out[-1500:]
        assert [r for r in rec["withheld_reasons"] if r.startswith("G-05: ledger moved after registration: E1:")], (
            rec["withheld_reasons"])
        assert gate_ledger.family_ledger("E1", tmp / "ledgers").n_raw == 5
        assert not list((tmp / "out" / rec["bridge_run_id"]).glob("NB_*.json"))


def test_l1_28_card_and_record_bytes():
    """L1-28 (5.5 steps 8 and 9; QA-9, OPS-12): the record's card md5 equals the md5 of the card's bytes; results_file
    is the run id; the card has no carriage return; writing a card to an existing path raises."""
    parity = _parity()
    with tempfile.TemporaryDirectory(prefix="qgnb_l128_") as name:
        tmp = Path(name)
        code, rec, out = _rehearse(_card_table(tmp), tmp)
        assert (code, rec["status"]) == (0, "CARD_WRITTEN"), out[-1500:]
        path = Path(rec["card"]["path"])
        raw = path.read_bytes()
        assert path.parent.name == rec["bridge_run_id"] and path.name == "NB_E1_trend_spy.json", path
        assert rec["card"]["md5"] == hashlib.md5(raw).hexdigest() and b"\r" not in raw
        card = json.loads(raw.decode("utf-8"))
        assert (card["results_file"], card["results_md5"]) == (rec["bridge_run_id"], ""), card["results_file"]
        assert card["card_id"] == "NB_E1_trend_spy", card["card_id"]
        assert card["decision"] == rec["gate"]["nautilus"]["decision"] == rec["gate"]["quantgen"]["decision"]
        try:
            parity.write_card(path, "{}")
        except FileExistsError:
            pass
        else:
            raise AssertionError("write_card overwrote an existing card")
        assert path.read_bytes() == raw


def test_l1_29_trial_counts_protocol_and_reference_drift():
    """L1-29 (QUANT-4, QUANT-R2-5, QUANT-R3-1, QUANT-R3-3, QUANT-R4-1): both pilot tables' study_configs equal the
    stored cards' grids, symbols and costs and 10.2's run 2/3 values; n_trials = family_n_raw + U on planted rows;
    each table's embargo, cost, grid, domain and the benchmark expression equal the study's calls; reference_drift on
    hand-built scores; pilot 2's reference md5; a stub rehearsal whose reference moves one float by 2e-9 is WITHHELD
    "reference drift", exit 1."""
    import ast
    import numpy as np
    from core.quant import gate_ledger, validate
    parity, runner = _parity(), _runner()
    tables = {k: json.loads(p.read_text(encoding="utf-8-sig")) for k, p in PILOT_TABLES.items()}
    cards = {n: json.loads((CARDS / f"{n}.json").read_text(encoding="utf-8")) for n in (
        "S_E1_trend_us", "S_E1_trend_krx", "S_C3_crypto_trend_btcusd", "S_C3_crypto_trend_krwbtc")}

    def from_card(c):
        return [(sorted(c["universe"]["symbols"]), c["costs"]["cost_bps"], g) for g in c["rules"]["grid"]]
    have = {k: [(c["symbols"], c["cost_bps"], c["params"]) for c in t["study_configs"]] for k, t in tables.items()}
    assert have["E1-SPY"] == from_card(cards["S_E1_trend_us"]) + from_card(cards["S_E1_trend_krx"])
    runs23 = [(["BTC-USD"], 10.0, {"hysteresis": h}) for h in (0.05, 0.1, 0.2, 0.3, 0.4, 0.5)]
    assert have["C3-BTCUSD"] == runs23 + from_card(cards["S_C3_crypto_trend_krwbtc"])
    ledger_note = cards["S_C3_crypto_trend_btcusd"]["trials"]["ledger"][0]
    assert "run 2/3: hysteresis [0.05, 0.1, 0.2, 0.3, 0.4, 0.5]" in ledger_note, ledger_note
    t1 = tables["E1-SPY"]
    with tempfile.TemporaryDirectory(prefix="qgnb_l129_") as name:
        ledger = gate_ledger.family_ledger("E1", Path(name))
        for g in t1["grid"][:3]:                                    # three bridge rows
            gate_ledger.register_trial(ledger, runner.ledger_row(t1, g, span=("2004-12-01", "2026-09-25"),
                                                                 run_utc="2026-10-28T00:00:00Z", anchor="UNVERSIONED",
                                                                 bridge_run_id="NB-test"))
        for c in t1["study_configs"][:2] + t1["study_configs"][12:13]:    # two US Lab rows and one KRX row
            params = dict(c["params"], symbols=sorted(c["symbols"]), cost_bps=float(c["cost_bps"]))
            gate_ledger.register_trial(ledger, dict(_plain_row("E1", 0), params=params,
                                                    market="US" if c["cost_bps"] == 50.0 else "KR"))
        counts = parity.trial_counts(t1, ledger.rows())
    assert {k: counts[k] for k in ("len_grid", "family_n_raw", "market_n_raw", "U", "n_trials")} == {
        "len_grid": 12, "family_n_raw": 6, "market_n_raw": 5, "U": 21, "n_trials": 27}, counts
    assert len(set(parity.study_config_ids(t1))) == 24 and len(set(parity.study_config_ids(tables["C3-BTCUSD"]))) == 11
    study = runner.load_study(ROOT)
    tree = ast.parse((ROOT / "docs" / "asset_expansion_study.py").read_text(encoding="utf-8"))
    fns = {f.name: f for f in tree.body if isinstance(f, ast.FunctionDef)}

    def calls(fn, name):
        return [n for n in ast.walk(fns[fn]) if isinstance(n, ast.Call) and ast.unparse(n.func).endswith(name)]

    def bench_text(fn):
        return [ast.unparse(n.value) for n in ast.walk(fns[fn]) if isinstance(n, ast.Assign)
                and ast.unparse(n.targets[0]) == "bench"][0]
    for fn, pilot, cost_key, strategy in (("run_trend", "E1-SPY", "us", "trend_switch"),
                                          ("run_crypto_trend", "C3-BTCUSD", "crypto", "crypto_trend")):
        t = tables[pilot]
        axes = {k.arg: ast.literal_eval(k.value) for k in calls(fn, "grid_from")[0].keywords}
        card_kw = {k.arg: k.value for k in calls(fn, "strategy_card")[0].keywords}
        domain = ast.literal_eval(card_kw["domain"]) if "domain" in card_kw else None
        assert t["axes"] == axes and t["grid"] == runner.S.grid_from(**axes) and list(t["axes"]) == list(axes), pilot
        assert t["embargo"] == ast.literal_eval(card_kw["embargo"]) and t["cost_bps"] == study.COST[cost_key], pilot
        cost_text = ast.unparse(card_kw["cost_bps"])
        assert cost_text in ("COST[cost_key]", f"COST[{cost_key!r}]"), cost_text
        assert (t["domain"] is None and domain is None) or {k: tuple(v) for k, v in t["domain"].items()} == domain
        assert bench_text(fn) == parity.STUDY_BENCH[strategy], (fn, bench_text(fn))
    ref_card = cards["S_C3_crypto_trend_btcusd"]
    t2 = tables["C3-BTCUSD"]
    assert (t2["grid"], t2["embargo"], t2["cost_bps"]) == (ref_card["rules"]["grid"], ref_card["rules"]["embargo"],
                                                          ref_card["costs"]["cost_bps"])
    assert t2["reference_card_md5"] == _md5(ROOT / t2["reference_card"]) == "d0bb0882fb51dec361cf2ddb160186bb"
    dates = tuple(d.strftime("%Y-%m-%d") for d in runner.pd.date_range("2016-10-14", "2026-09-25", freq="D"))
    wf = validate.WalkForward(dates=dates, pnl=np.zeros(len(dates)), pnl_stress=np.zeros(len(dates)),
                              turnover=np.zeros(len(dates)), origins=(756,), chosen=(0,), is_sharpes=np.zeros((1, 5)),
                              n_configs=5)
    sc = validate.StrategyScore(**dict(N8_BASE, n_years=9, n_sessions=len(dates)))
    grid = runner.S.grid_from(**PILOT2_AXES)
    ref = dict(N8_BASE, n_years=11, n_sessions=len(dates), ci90=[0.72, 1.64], chosen_last={"hysteresis": 0.0})
    assert parity.reference_drift(sc, wf, grid, ref) == []
    assert parity.reference_drift(sc, wf, grid, dict(ref, n_sessions=len(dates) + 1)) == ["n_sessions"]
    assert parity.reference_drift(sc, wf, grid, dict(ref, sr_oos=1.19 + 2e-9)) == ["sr_oos"]
    assert parity.reference_drift(sc, wf, grid, dict(ref, ci90=[0.72, 1.64 - 2e-9], n_years=9)) == ["n_years", "ci90"]
    n, crypto = 900, runner.S.grid_from(**PILOT2_AXES)
    closes, days = synth_prices(5, n, 400.0, 60000.0), _days(n)
    stats, _sc, _wf = _reference_stats(closes, days, crypto, cost=10.0, embargo=1, n_trials=5,
                                       domain={"hysteresis": (0.0, 0.889)})
    with tempfile.TemporaryDirectory(prefix="qgnb_l129e_") as name:
        tmp = Path(name)
        card = tmp / "reference_card.json"
        md5 = _write_card_file(card, dict(stats, sr_oos=stats["sr_oos"] + 2e-9))
        code, rec, out = _rehearse(_crypto_table(tmp, n, reference_card=str(card), reference_card_md5=md5), tmp)
        assert (code, rec["status"], rec["card"]) == (1, "WITHHELD", None), out[-1500:]
        assert rec["gate"]["reference"]["drift"] == ["sr_oos"], rec["gate"]["reference"]
        assert "G-08: reference drift: sr_oos" in rec["withheld_reasons"], rec["withheld_reasons"]


def test_l1_30_card_labels_and_engine_text():
    """L1-30 (6.5; QUANT-6, QUANT-11, QUANT-R2-4): a written card carries the claim label, the engine text (STUB with
    the stub child, 6.5's text otherwise), parity_scope and stats.quantgen_score; every committed table's claim_label
    starts with "exploratory", "pre-specified on historical data" or "confirmatory"."""
    parity = _parity()
    for pilot, path in PILOT_TABLES.items():
        t = json.loads(path.read_text(encoding="utf-8-sig"))
        assert t["pilot"] == pilot and t["claim_label"].startswith(parity.CLAIM_PREFIXES), (pilot, t["claim_label"])
        assert "owner_confirmed" not in t and "host_fingerprint" not in t, pilot          # GOVERNANCE-R4-3
        assert parity.card_rules(t, stub_child=False)["engine"] == ENGINE_6_5
    with tempfile.TemporaryDirectory(prefix="qgnb_l130_") as name:
        tmp = Path(name)
        table = _card_table(tmp)
        t = json.loads(table.read_text(encoding="utf-8"))
        code, rec, out = _rehearse(table, tmp)
        assert (code, rec["status"]) == (0, "CARD_WRITTEN"), out[-1500:]
        card = json.loads(Path(rec["card"]["path"]).read_text(encoding="utf-8"))
        assert card["rules"] == parity.card_rules(t, stub_child=True) and card["rules"]["engine"] == "STUB", card["rules"]
        assert card["rules"]["claim_label"] == t["claim_label"] and card["rules"]["parity_scope"] == SCOPE_6_5
        assert card["hypothesis"] == f"{t['claim_label']}: {t['hypothesis']}" and card["kind"] == "strategy"
        q = card["stats"]["quantgen_score"]
        assert q["decision"] == card["decision"] and "lines" not in q and q["n_configs"] == 4, q
        assert card["stats"]["parity"]["hard_pass"] is True and card["trials"]["N_planned"] == 4, card["trials"]
        assert card["decision"] in ("PASS", "REVISE", "REJECT", "INSUFFICIENT_DATA")


def test_l1_31_walk_forward_raise_g03():
    """L1-31 (G-03; QA-R2-2): a 400-row synthetic table makes walk_forward raise after registration; the run is
    WITHHELD, exit 1, and the reason names the walk_forward exception; a score_fn that raises on the card table is
    WITHHELD the same way, naming score_strategy, after every hard check passed."""

    def raises(wf, **kw):
        raise ValueError("planted in score_fn")
    with tempfile.TemporaryDirectory(prefix="qgnb_l131_") as name:
        tmp = Path(name)
        code, rec, out = _rehearse(_small_table(tmp, n=400), tmp)
        assert (code, rec["status"], rec["card"]) == (1, "WITHHELD", None), out[-1500:]
        want = "G-03: walk_forward raised ValueError: need at least 546 sessions for one walk-forward step, got 399"
        assert rec["withheld_reasons"] == [want] and rec["gate"]["error"] == want, rec["withheld_reasons"]
        assert rec["parity"]["hard_pass"] is False and rec["parity"]["failed"] == [], rec["parity"]["failed"]
        code, rec, out = _rehearse(_card_table(tmp / "score"), tmp / "score", score_fn=raises)
        want = "G-03: score_strategy raised ValueError: planted in score_fn"
        assert (code, rec["status"], rec["card"], rec["withheld_reasons"]) == (1, "WITHHELD", None, [want]), out[-1500:]
        assert rec["parity"]["hard_pass"] is True and rec["gate"]["error"] == want and rec["gate"]["quantgen"] is None
        assert rec["gate"]["trial_counts"]["n_trials"] == 4, rec["gate"]["trial_counts"]


def test_l1_36_fingerprint_reads_no_data():
    """L1-36 (GOVERNANCE-R4-1), with the 3.3 guard's temp QUANTGEN_MACRO_DIR: --fingerprint on both committed pilot
    tables prints table_sha256, code_sha256 and host_fingerprint null with the reason and exits 0; on a copy whose
    prices_file names a missing file it still exits 0; an invalid table exits 2 after printing both digests."""
    runner = _runner()
    code_sha = runner.code_sha256(ROOT)
    with tempfile.TemporaryDirectory(prefix="qgnb_l136_") as name:
        tmp = Path(name)
        missing = tmp / "missing.json"
        t = json.loads(PILOT_TABLES["E1-SPY"].read_text(encoding="utf-8"))
        missing.write_text(json.dumps(dict(t, prices_file="docs/asset_expansion/cache/yf_NOT_THERE.csv"), indent=1),
                           encoding="utf-8", newline="\n")
        bad = tmp / "bad.json"
        bad.write_text(json.dumps(dict(t, cost_bps=40.0, pilot="E1-SPY", volume="5")), encoding="utf-8", newline="\n")
        for path in (*PILOT_TABLES.values(), missing, bad):
            table = json.loads(path.read_text(encoding="utf-8-sig"))
            code, out = _captured(lambda: runner.main(["--fingerprint", "--table", str(path)]))
            lines = out.splitlines()
            assert lines[:2] == [f"table_sha256 {runner.table_sha256(table)}", f"code_sha256 {code_sha}"], lines
            if path == bad:
                assert code == 2 and lines[-1] == "STATUS REFUSED exit=2 record=-" and "R-11" in out, out
                continue
            ledger = Path(os.environ["QUANTGEN_MACRO_DIR"]) / "ledgers" / f"{table['family_id']}.jsonl"
            want = f"host_fingerprint null (the family ledger {ledger} does not exist; R-15, O11)"
            assert code == 0 and lines[2] == want, lines
            assert lines[-1] == "STATUS OK exit=0 record=-", lines


def test_l2_07_synthetic_end_to_end_rehearsal():
    """L2-7 (8.4; QA-R3-11): synth_prices(7, 1500, 100, 150) and synth_rf(1500), the four columns of CARD_AXES at
    50 bp, embargo 21, through the real sandbox: every hard check passes, both scores are in the run record, and the
    run ends with a card whose decision is in validate.DECISIONS and whose engine text is 6.5's, or WITHHELD naming
    the differing predicates with their two values (G-02); never a new seed after the result."""
    from core.quant import validate
    layer2()
    runner = _runner()
    with tempfile.TemporaryDirectory(prefix="qgnb_l207_") as name:
        tmp = Path(name)
        table = write_rehearsal_table(tmp, prices=synth_prices(7, 1500, 100.0, 150.0), dates=_bdates(1500),
                                      rf=synth_rf(1500), axes=CARD_AXES)
        (code, out) = _captured(lambda: runner.run(table, mode="rehearsal", ledger_dir=tmp / "ledgers",
                                                   out_dir=tmp / "out"))
        rec = json.loads(next((tmp / "out").glob("NB-*/run.json")).read_text(encoding="utf-8"))
        assert rec["stub_child"] is False and rec["parity"]["hard_pass"] is True, (rec["withheld_reasons"], out[-1500:])
        assert rec["gate"]["quantgen"]["stats"] and rec["gate"]["nautilus"]["stats"] and len(rec["children"]) == 8
        worst = min(x["P2"]["value"] for x in rec["parity"]["legs"])
        print(f"L2-7: {rec['status']}; quantgen {rec['gate']['quantgen']['decision']}, nautilus "
              f"{rec['gate']['nautilus']['decision']}; worst corr {worst}")
        if code == 0:
            card = json.loads(Path(rec["card"]["path"]).read_text(encoding="utf-8"))
            assert card["decision"] in validate.DECISIONS and card["rules"]["engine"] == ENGINE_6_5, card["rules"]
        else:
            assert code == 1 and rec["withheld_reasons"] and all(
                r.startswith("G-02: decision mismatch: ") for r in rec["withheld_reasons"]), rec["withheld_reasons"]


def test_l2_11_n6_stress():
    """L2-11 (N6; QUANT-10, QA-R2-12): synth_prices(2026, 5500, 80, 650, planted every 252 bars from 252) with
    synth_rf(5500), pilot 1's 12 columns at 50 bp, 1x and 2x through the real sandbox: every hard check passes; the
    worst correlation and absolute Sharpe gap are printed next to the bars and map 03's (0.99999901, 0.0013)."""
    layer2()
    runner = _runner()
    with tempfile.TemporaryDirectory(prefix="qgnb_l211_") as name:
        tmp = Path(name)
        table = write_rehearsal_table(tmp, prices=synth_prices(2026, 5500, 80.0, 650.0, planted=range(252, 5292, 252)),
                                      dates=_bdates(5500), rf=synth_rf(5500), axes=PILOT1_AXES)
        (code, out) = _captured(lambda: runner.run(table, mode="rehearsal", ledger_dir=tmp / "ledgers",
                                                   out_dir=tmp / "out"))
        rec = json.loads(next((tmp / "out").glob("NB-*/run.json")).read_text(encoding="utf-8"))
        legs = rec["parity"]["legs"]
        worst_corr, worst_dsr = min(x["P2"]["value"] for x in legs), max(x["P3"]["value"] for x in legs)
        print(f"N6: worst corr {worst_corr:.8f} (bar 0.9999, map 03 0.99999901); worst abs dSR {worst_dsr:.5f} "
              f"(bar 0.01, map 03 0.0013); {rec['status']}")
        assert len(legs) == 24 and rec["parity"]["hard_pass"] is True, (rec["parity"]["failed"], out[-1500:])
        assert code in (0, 1) and all(r.startswith("G-02") for r in rec["withheld_reasons"]), rec["withheld_reasons"]


def test_l2_12_crypto_rehearsal_reference():
    """L2-12 (QUANT-R3-2, QUANT-R4-1): the L2-12 series (8.2), pilot 2's grid, embargo 1, domain, 10 bp, no cash
    rate, through the real sandbox, with a temp reference card built as the stored card was built: both scores in
    the record and gate.reference holding an empty drift list; a card, or WITHHELD naming its reason (G-02 only);
    the same reference with the whole-year n_years left in gives exactly ["n_years"]."""
    layer2()
    parity, runner = _parity(), _runner()
    n, grid = 1600, runner.S.grid_from(**PILOT2_AXES)
    closes, days = synth_prices(5, n, 400.0, 60000.0), _days(n)
    stats, sc, wf = _reference_stats(closes, days, grid, cost=10.0, embargo=1, n_trials=5,
                                     domain={"hysteresis": (0.0, 0.889)})
    whole = dict(stats, n_years=sc.n_years)                    # the whole-year count left in
    assert parity.reference_drift(sc, wf, grid, whole) == ["n_years"], (sc.n_years, stats["n_years"])
    with tempfile.TemporaryDirectory(prefix="qgnb_l212_") as name:
        tmp = Path(name)
        card = tmp / "reference_card.json"
        md5 = _write_card_file(card, stats)
        table = _crypto_table(tmp, n, reference_card=str(card), reference_card_md5=md5)
        (code, out) = _captured(lambda: runner.run(table, mode="rehearsal", ledger_dir=tmp / "ledgers",
                                                   out_dir=tmp / "out"))
        rec = json.loads(next((tmp / "out").glob("NB-*/run.json")).read_text(encoding="utf-8"))
        assert rec["parity"]["hard_pass"] is True and rec["gate"]["reference"]["drift"] == [], (
            rec["withheld_reasons"], rec["gate"]["reference"], out[-1500:])
        gate = rec["gate"]
        assert gate["quantgen"]["stats"]["n_sessions"] == stats["n_sessions"] and gate["nautilus"]["stats"], gate
        print(f"L2-12: {rec['status']}; quantgen {gate['quantgen']['decision']}, nautilus {gate['nautilus']['decision']}; "
              f"reference n_years {gate['reference']['n_years_calendar']} calendar, "
              f"{gate['reference']['n_years_whole']} whole")
        assert code in (0, 1) and all(r.startswith("G-02") for r in rec["withheld_reasons"]), rec["withheld_reasons"]


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
