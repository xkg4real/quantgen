"""The launch contract of the NautilusTrader bridge (spec 2026-10-26 sections 4.3, 5.2.7 and 6.7).

Every child (the sandbox, the egress probe, a test stub) starts through `run_child`, with the argv and the minimal
environment that `build_launch` builds: `-I -B -X utf8`, an absolute script path, `unshare -rn` on POSIX, a fresh
temp working directory, no inherited variable, and a tree kill on timeout. This module also reads the venv's own
files for versions and the wheel identity (the parent never imports the engine), and parses the import census.
Standard library only; it runs in the global interpreter.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import io
import json
import ntpath
import os
import posixpath
import re
import shutil
import signal
import stat
import subprocess
import sys
import sysconfig
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
SANDBOX = REPO_ROOT / "tools" / "nautilus" / "sandbox.py"
EGRESS_PROBE = REPO_ROOT / "tools" / "nautilus" / "egress_probe.py"
REQUIREMENTS = REPO_ROOT / "requirements-nautilus.txt"
GOLDEN_DIR = REPO_ROOT / "tools" / "nautilus" / "golden"
ENV_PINS = GOLDEN_DIR / "env_pins.json"
KEY = "QUANTGEN_NAUTILUS_PYTHON"
TIMEOUT_S = 900            # communicate(timeout=900), spec 4.3
DRAIN_S = 30               # communicate(timeout=30) after a kill
TAIL_CHARS = 4000          # stdout/stderr tails kept in the run record
ENV_KEYS = {"nt": frozenset({"SYSTEMROOT", "PATH", "USERPROFILE", "HOME", "TEMP", "TMP"}),
            "posix": frozenset({"PATH", "HOME", "TMPDIR", "LANG", "LC_ALL"})}
CREATE_NEW_PROCESS_GROUP = 0x00000200          # subprocess.CREATE_NEW_PROCESS_GROUP, which exists only on Windows
PINNED = ("nautilus-trader", "numpy", "pandas")
VENV_FIX = ("set QUANTGEN_NAUTILUS_PYTHON in .env to the absolute path of the venv's python, in single quotes with "
            "forward slashes, as .env.example shows; build the venv with <py313>\\python.exe -m venv and the offline "
            "install of the requirements-nautilus.txt header (spec 5.1)")
STORE_FIX = ("this venv was made from the Microsoft Store python; recreate it with "
             "<py313>\\python.exe -m venv <venv dir> (spec 4.4, 6.7)")
PARENT_NAUTILUS_REMEDY = "\n".join((                # R-03 for the parent, exactly three lines (spec 7; OPS-R3-1)
    "python -m pip uninstall -y nautilus-trader",
    "python -m pip check",
    'python -c "import numpy, pandas, scipy; print(numpy.__version__, pandas.__version__, scipy.__version__)"'))


class BridgeRefusal(Exception):
    """A refusal R-01 to R-17 of spec section 7. `str(exc)` is f"{rid}: {message}"."""

    def __init__(self, rid: str, message: str, remedy: str = "") -> None:
        super().__init__(f"{rid}: {message}")
        self.rid, self.message, self.remedy = rid, message, remedy


class ChildInvalid(Exception):
    """A child-level invalid condition C-01 to C-15. `str(exc)` is f"{cid}: {message}"."""

    def __init__(self, cid: str, message: str) -> None:
        super().__init__(f"{cid}: {message}")
        self.cid, self.message = cid, message


def _pep503(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _norm(path: str) -> str:
    return os.path.normcase(os.path.realpath(path))


def _store_python(path: str) -> bool:
    s = path.replace("/", "\\").lower()
    return "\\windowsapps\\" in s or s.endswith("\\windowsapps") or "\\packages\\pythonsoftwarefoundation." in s


# --------------------------------------------------------------------------- #
# Venv reads and the wheel identity (spec 6.7)
# --------------------------------------------------------------------------- #
def venv_key() -> str:
    """QUANTGEN_NAUTILUS_PYTHON after `import config` has loaded .env; "" when blank or an unedited <placeholder>."""
    import config
    return config._clean(KEY)


def resolve_venv_python(value: str) -> Path:
    """The venv python named by the key, after ~ and variable expansion; R-03 on a control character, a relative
    path, a file name other than python.exe or python, or a missing file. Not resolved through symlinks."""
    def refuse(why: str) -> BridgeRefusal:
        return BridgeRefusal("R-03", f"QUANTGEN_NAUTILUS_PYTHON {why}: {value!r}", VENV_FIX)
    bad = [c for c in value if ord(c) < 32 or ord(c) == 127]
    expanded = os.path.expanduser(os.path.expandvars(value))
    if bad or any(ord(c) < 32 or ord(c) == 127 for c in expanded):
        raise refuse("holds a control character")
    path = Path(expanded)
    if not path.is_absolute():
        raise refuse("is not an absolute path")
    if path.name not in ("python.exe", "python"):
        raise refuse("does not name python.exe or python")
    if not path.is_file():
        raise refuse("names a missing file")
    return path


def venv_root(python: Path) -> Path:
    """The parent of Scripts (Windows) or bin (POSIX)."""
    if python.parent.name not in ("Scripts", "bin"):
        raise BridgeRefusal("R-03", f"the venv python is not in Scripts or bin: {str(python)!r}", VENV_FIX)
    return python.parent.parent


def expected_versions(path: Path = REQUIREMENTS) -> dict[str, str]:
    """{"nautilus-trader", "numpy", "pandas"} -> version, from the == pins of requirements-nautilus.txt (5.1)."""
    found = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s;\\]+)", line)
        if m and _pep503(m[1]) in PINNED:
            found[_pep503(m[1])] = m[2]
    missing = sorted(set(PINNED) - set(found))
    if missing:
        raise ValueError(f"{path.name} pins none of {missing}")
    return found


def record_identity(record_text: str) -> tuple[str, int]:
    """(record_digest_sha256, record_entries) of a wheel RECORD by the rule of spec 6.7."""
    kept = []
    for row in csv.reader(io.StringIO(record_text)):
        if len(row) < 2 or not row[1] or "__pycache__" in row[0]:
            continue
        if row[0].endswith(("/RECORD", "/INSTALLER", "/REQUESTED", "/direct_url.json")):
            continue
        kept.append(f"{row[0]},{row[1]}")
    kept.sort()
    return hashlib.sha256("\n".join(kept).encode("utf-8")).hexdigest(), len(kept)


def _headers(path: Path) -> dict[str, str]:
    """The RFC 822 header lines of a METADATA or WHEEL file, up to the first blank line; first value wins."""
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            break
        key, sep, value = line.partition(":")
        if sep and not line[0].isspace():
            out.setdefault(key.strip(), value.strip())
    return out


def read_venv(python: Path, *, os_name: str = os.name, parent_base_executable: str = sys._base_executable) -> dict:
    """Reads pyvenv.cfg, every dist-info's METADATA and the nautilus_trader WHEEL and RECORD (spec 6.7). R-03 for
    include-system-site-packages = true and, on Windows, for a venv made from the parent's own interpreter or from
    the Microsoft Store python (4.4; OPS-R2-2). Opens no other file and starts no process."""
    root = venv_root(python)
    cfg_path = root / "pyvenv.cfg"
    if not cfg_path.is_file():
        raise BridgeRefusal("R-03", f"no pyvenv.cfg beside the venv python: {str(cfg_path)!r}", VENV_FIX)
    cfg = {}
    for line in cfg_path.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.partition("=")
        if sep:
            cfg[key.strip().lower()] = value.strip()
    if cfg.get("include-system-site-packages", "false").lower() == "true":
        raise BridgeRefusal("R-03", f"{str(cfg_path)!r} says include-system-site-packages = true", VENV_FIX)
    home, executable = cfg.get("home", ""), cfg.get("executable")
    version = cfg.get("version") or cfg.get("version_info", "")
    if os_name == "nt":
        if executable and _norm(executable) == _norm(parent_base_executable):
            raise BridgeRefusal("R-03", f"the venv was made from the global interpreter {executable!r}", STORE_FIX)
        for found in (home, executable or ""):
            if _store_python(found):
                raise BridgeRefusal("R-03", f"pyvenv.cfg names {found!r}: {STORE_FIX}", STORE_FIX)
    minor = ".".join(version.split(".")[:2])
    site = root / "Lib" / "site-packages" if os_name == "nt" else root / "lib" / f"python{minor}" / "site-packages"
    installed = {}
    for meta in sorted(site.glob("*.dist-info/METADATA")):
        head = _headers(meta)
        if head.get("Name") and head.get("Version"):
            installed[_pep503(head["Name"])] = head["Version"]
    infos = sorted(site.glob("nautilus_trader-*.dist-info"))
    if len(infos) != 1:
        raise BridgeRefusal("R-03", f"{len(infos)} nautilus_trader dist-info dirs in {str(site)!r}", VENV_FIX)
    wheel_tag = _headers(infos[0] / "WHEEL").get("Tag", "")
    digest, entries = record_identity((infos[0] / "RECORD").read_text(encoding="utf-8"))
    return {"python": str(python), "python_norm": _norm(str(python)), "root": str(root),
            "pyvenv": {"home": home, "version": version, "executable": executable,
                       "include_system_site_packages": False},
            "python_minor": minor,
            "installed": installed,
            "versions": {name: installed.get(name) for name in PINNED},
            "wheel": {"wheel_tag": wheel_tag, "platform_tag": wheel_tag.split("-", 2)[-1],
                      "record_digest_sha256": digest, "record_entries": entries}}


def load_env_pins(path: Path = ENV_PINS) -> dict:
    pins = json.loads(path.read_text(encoding="utf-8"))
    if pins.get("schema") != "nautilus-bridge-env-pins/1":
        raise ValueError(f"{path.name}: schema {pins.get('schema')!r}")
    return pins


def venv_mismatches(reads: dict, pins: dict | None = None, expected: dict | None = None) -> list[str]:
    """[] when the venv matches requirements-nautilus.txt and env_pins.json; else one
    "R-03: <field>: found <x>, expected <y>" per difference (an unknown platform tag is one mismatch)."""
    pins = load_env_pins() if pins is None else pins
    expected = expected_versions() if expected is None else {_pep503(k): v for k, v in expected.items()}
    tag = reads["wheel"]["platform_tag"]
    if tag not in pins["platforms"]:
        return [f"R-03: platform_tag: found {tag}, expected one of {sorted(pins['platforms'])}"]
    pin = pins["platforms"][tag]
    pinned = {_pep503(k): v for k, v in pin["versions"].items()}
    out = []

    def check(field: str, found, want) -> None:
        if found != want:
            out.append(f"R-03: {field}: found {found}, expected {want}")
    check("python_minor", reads["python_minor"], pin["python_minor"])
    for name in PINNED:
        found = reads["versions"].get(name)
        check(name, found, expected.get(name))
        if expected.get(name) != pinned.get(name):
            check(f"{name} (env_pins.json)", found, pinned.get(name))
    for field in ("wheel_tag", "record_digest_sha256", "record_entries"):
        check(field, reads["wheel"][field], pin[field])
    return out


def parent_nautilus() -> str | None:
    """The nautilus-trader version installed in this (the global) interpreter, or None (spec 5.3.2 step 3)."""
    try:
        return importlib.metadata.distribution("nautilus-trader").version
    except importlib.metadata.PackageNotFoundError:
        return None


def parent_pyarrow() -> str | None:
    try:
        return importlib.metadata.distribution("pyarrow").version
    except importlib.metadata.PackageNotFoundError:
        return None


def host_tag() -> str:
    """sysconfig.get_platform() with - and . replaced by _: linux_x86_64, win_amd64 (C1)."""
    return sysconfig.get_platform().replace("-", "_").replace(".", "_")


# --------------------------------------------------------------------------- #
# The launch contract (spec 4.3)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Launch:
    argv: list[str]
    env: dict[str, str]
    cwd: str
    popen_kwargs: dict


@dataclass(frozen=True)
class ChildResult:
    argv: list[str]
    returncode: int | None
    ntstatus: str | None
    timed_out: bool
    seconds: float
    stdout: str
    stderr: str
    census: list[str]
    stdout_tail: str
    stderr_tail: str


def make_tempdir() -> Path:
    """realpath(mkdtemp(prefix="qgnb_")) with home/ and tmp/ inside: the child's cwd, HOME and TMP (4.3)."""
    tempdir = Path(os.path.realpath(tempfile.mkdtemp(prefix="qgnb_")))
    (tempdir / "home").mkdir()
    (tempdir / "tmp").mkdir()
    return tempdir


def resolve_unshare(os_name: str = os.name) -> str | None:
    """None on Windows. POSIX: the unshare binary, which must run `unshare -rn true` with exit 0, else R-14."""
    if os_name == "nt":
        return None
    exe = shutil.which("unshare")
    if exe is None:
        raise BridgeRefusal("R-14", "unshare is not on PATH", "a Linux host with user namespaces (spec 4.4)")
    probe = subprocess.run([exe, "-rn", "true"], stdin=subprocess.DEVNULL, capture_output=True, encoding="utf-8",
                           errors="replace", timeout=60)
    if probe.returncode != 0:
        raise BridgeRefusal("R-14", f"`unshare -rn true` exited {probe.returncode}: {probe.stderr.strip()[-300:]}",
                            "a Linux host with user namespaces (spec 4.4)")
    return exe


def assert_env_contract(env: Mapping[str, str], os_name: str) -> None:
    want = ENV_KEYS["nt" if os_name == "nt" else "posix"]
    if set(env) != want:
        raise ChildInvalid("C-10", f"child environment keys {sorted(env)}; the contract allows exactly {sorted(want)}")


def build_launch(mode_args: Sequence[str], *, tempdir: Path, venv_python: Path | None, os_name: str = os.name,
                 unshare: str | None = None, child_cmd: Sequence[str] | None = None, script: Path = SANDBOX,
                 environ: Mapping[str, str] = os.environ) -> Launch:
    """The argv, environment, cwd and Popen arguments of one child, exactly as spec 4.3's table. Starts no process."""
    pathmod = ntpath if os_name == "nt" else posixpath
    if child_cmd is not None:
        if not child_cmd or not pathmod.isabs(str(child_cmd[0])):
            raise ValueError(f"child_cmd must start with an absolute path: {list(child_cmd)!r}")
        command = [str(c) for c in child_cmd]
    else:
        if venv_python is None:
            raise ValueError("venv_python is required without child_cmd")
        importtime = Path(script) == SANDBOX and list(mode_args[:1]) == ["run"]
        command = [str(venv_python), "-I", "-B", "-X", "utf8", *(["-X", "importtime"] if importtime else []),
                   str(script)]
    bin_dir = pathmod.dirname(command[0])
    home, tmp = pathmod.join(str(tempdir), "home"), pathmod.join(str(tempdir), "tmp")
    pipes = {"stdin": subprocess.DEVNULL, "stdout": subprocess.PIPE, "stderr": subprocess.PIPE, "text": True,
             "encoding": "utf-8", "errors": "replace"}
    if os_name == "nt":
        root = environ["SYSTEMROOT"]
        env = {"SYSTEMROOT": root, "PATH": f"{bin_dir};{root}\\System32", "USERPROFILE": home, "HOME": home,
               "TEMP": tmp, "TMP": tmp}
        argv = [*command, *mode_args]
        popen_kwargs = {**pipes, "creationflags": CREATE_NEW_PROCESS_GROUP}
    else:
        if not unshare:
            raise BridgeRefusal("R-14", "a POSIX child needs unshare -rn (spec 4.4)",
                                "a Linux host with user namespaces (spec 4.4)")
        env = {"PATH": f"{bin_dir}:/usr/bin:/bin", "HOME": home, "TMPDIR": tmp, "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}
        argv = [unshare, "-rn", *command, *mode_args]
        popen_kwargs = {**pipes, "start_new_session": True}
    assert_env_contract(env, os_name)
    return Launch(argv=argv, env=env, cwd=str(tempdir), popen_kwargs=popen_kwargs)


def kill_tree(proc: subprocess.Popen, os_name: str = os.name) -> None:
    """Windows: taskkill /T /F; POSIX: SIGKILL to the child's process group (start_new_session made it a leader)."""
    if os_name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], stdin=subprocess.DEVNULL,
                       capture_output=True, encoding="utf-8", errors="replace")
        if proc.poll() is None:
            proc.kill()
        return
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        if proc.poll() is None:
            proc.kill()


def _drain(proc: subprocess.Popen) -> tuple[str, str]:
    try:
        return proc.communicate(timeout=DRAIN_S)
    except subprocess.TimeoutExpired as exc:
        def text(x) -> str:
            return x.decode("utf-8", "replace") if isinstance(x, bytes) else (x or "")
        return text(exc.stdout), text(exc.stderr)


def run_child(launch: Launch, *, timeout: float = TIMEOUT_S, on_started: Callable[[], None] | None = None,
              os_name: str = os.name) -> ChildResult:
    """Runs one child as `launch` says; a timeout or any BaseException after Popen kills the whole tree and drains the
    pipes; a BaseException is re-raised (OPS-R2-4). Never deletes the temp dir."""
    started = time.monotonic()
    proc = subprocess.Popen(launch.argv, cwd=launch.cwd, env=launch.env, **launch.popen_kwargs)
    timed_out = False
    try:
        if on_started is not None:
            on_started()
        try:
            out, err = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            kill_tree(proc, os_name)
            out, err = _drain(proc)
    except BaseException:
        kill_tree(proc, os_name)
        _drain(proc)
        raise
    code = proc.poll()
    ntstatus = (f"0x{code & 0xFFFFFFFF:08X}" if os_name == "nt" and code is not None
                and (code & 0xFFFFFFFF) >= 0xC0000000 else None)
    census, rest = parse_census(err or "")
    return ChildResult(argv=list(launch.argv), returncode=code, ntstatus=ntstatus, timed_out=timed_out,
                       seconds=round(time.monotonic() - started, 3), stdout=out or "", stderr=err or "",
                       census=census, stdout_tail=(out or "")[-TAIL_CHARS:], stderr_tail=rest[-TAIL_CHARS:])


def parse_census(stderr: str) -> tuple[list[str], str]:
    """(sorted unique module names from the `import time:` lines, the stderr without those lines) (spec 5.2.7)."""
    names, rest = set(), []
    for line in stderr.splitlines(keepends=True):
        if line.startswith("import time:"):
            fields = line.split("|")
            name = fields[2].strip() if len(fields) >= 3 else ""
            if name and name != "imported package":
                names.add(name)
            continue
        rest.append(line)
    return sorted(names), "".join(rest)


def cleanup_tempdir(tempdir: Path) -> list[str]:
    """rmtree with up to 3 attempts 0.5 s apart; returns the paths still present ([] when gone); never raises."""
    def onexc(func, path, _exc) -> None:
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except OSError:
            pass
    for attempt in range(3):
        if attempt:
            time.sleep(0.5)
        try:
            shutil.rmtree(tempdir, onexc=onexc)
        except OSError:
            pass
        if not os.path.lexists(tempdir):
            return []
    try:
        return sorted(str(p) for p in Path(tempdir).rglob("*")) or [str(tempdir)]
    except OSError:
        return [str(tempdir)]


# --------------------------------------------------------------------------- #
# Fixtures F1, F1r, F2 and N1 (spec 8.2, 6.1; QA-R3-1): the one builder of their child inputs
# --------------------------------------------------------------------------- #
FIXTURES = ("F1", "F1r", "F2", "N1")
_FIXTURE_CLOSES = {"F1": (97, 98, 99, 100, 104, 96, 95, 99, 101, 103, 98, 97),
                   "F2": (50000, 51000, 52000, 53000, 52600, 50000, 49000, 50500, 52000, 51000, 50800)}


def _fixture_ts(name: str) -> list[int]:
    """The bar timestamps (ns) of a fixture (spec 8.2, 5.2.4): F1, F1r and N1 at 21:00 UTC on the 12 weekdays from
    2001-01-02; F2 at 00:00 UTC on the calendar day after each of its 11 dates from 2021-01-01."""
    from datetime import date, timedelta
    if name == "F2":
        days = [date(2021, 1, 2) + timedelta(days=k) for k in range(len(_FIXTURE_CLOSES["F2"]))]
        hour = 0
    else:
        days, d = [], date(2001, 1, 2)
        while len(days) < len(_FIXTURE_CLOSES["F1"]):
            if d.weekday() < 5:
                days.append(d)
            d += timedelta(days=1)
        hour = 21
    return [((d - date(1970, 1, 1)).days * 86400 + hour * 3600) * 10**9 for d in days]


def fixture_inputs(name: str) -> tuple[bytes, bytes]:
    """(input.json bytes, bars.csv bytes) of fixture `name` (spec 8.2 and 6.1), the one builder that L2-4, L2-5a,
    L2-5b, --fixtures, --write-goldens and L1-33 use (QA-R3-1). input.json is C1's canonical JSON, no trailing
    newline; bars.csv is LF. ledger_hash_after_registration is gate_ledger.ledger_hash([]), the hash of an empty
    ledger, since fixtures register nothing (6.1). F1r's child inputs are F1's: F1r differs only in the parent's rf,
    0.0001 per session (QUANT-R2-6). N1 is F1 with volume "4000" and 2 price decimals. KeyError for another name."""
    if name not in FIXTURES:
        raise KeyError(name)
    from core.quant.gate_ledger import ledger_hash
    crypto = name == "F2"
    p = 2 if name == "N1" else 9
    closes = _FIXTURE_CLOSES["F2" if crypto else "F1"]
    rows = ["i,ts_ns,close"] + [f"{i},{t},{c:.{p}f}" for i, (t, c) in enumerate(zip(_fixture_ts(name), closes))]
    bars = ("\n".join(rows) + "\n").encode("utf-8")
    if crypto:
        head = {"strategy": "crypto_trend", "params": {"hysteresis": 0.2, "lookbacks": [1, 2], "mas": [2, 3]},
                "instrument": "BTC/USD", "capital_usd": "53053", "cost_bps": "10", "size_precision": 8}
    else:
        head = {"strategy": "trend_switch", "params": {"rule": "sma", "lookback": 3, "step": 2},
                "instrument": "SPY", "capital_usd": "1005001", "cost_bps": "50", "size_precision": 0}
    inp = {**head, "schema": "nautilus-bridge-input/2", "stress": "1", "fill_seed": 42, "price_precision": p,
           "volume": "4000" if name == "N1" else "1000000000", "n_bars": len(closes),
           "bars_sha256": hashlib.sha256(bars).hexdigest(), "ledger_hash_after_registration": ledger_hash([])}
    return json.dumps(inp, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"), bars
