# Round 1 referee report: Windows operations (Claude, ops lens)

Spec: `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md`, Revision 1 (cited as `spec:<line>`).
Repo: QUANTGEN at HEAD `6f7c610`. Nautilus: `nt:` = `nautilus_trader` 1.231.0 in `scratch:ntvenv`.
`scratch:` = `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/`.
My probes live in `scratch:referee_ops/`. They read synthetic inputs, wheel files and source only. No pilot-window
data, no ledger, no `tests/run_all.py`, no global install.

Lens: the owner's machine. Windows 11, Python 3.13 global interpreter, no venv, cp949 locale, repo at
`C:/Users/whydi/OneDrive/Desktop/QUANTGEN` (`docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:19`).
Question asked of every step: what breaks at 3am, and does the message tell the owner what to do?

## Verdict

**ACCEPT_WITH_CHANGES.**

The overall design is sound for Windows:
- the child is launched with list argv, so spaces in paths are safe;
- the venv sits outside OneDrive;
- the child env is explicit and includes `SYSTEMROOT`;
- the child runs with `-X utf8`, and its script path is absolute;
- the pinned CSVs are byte-exact on every checkout (`.gitattributes`: `* -text`);
- the ledger already serialises appends with an OS byte lock (`core/quant/gate_ledger.py:244-262`).

I would not hand this spec to a team today without changes. Eight majors would bite on the owner's machine:
1. The 900 s timeout can hang through the venv redirector. The house hit this exact hang before (OPS-1).
2. The parent runner can die on cp949 stdout. The house hit this too (OPS-2).
3. `repo_anchor()` returns UNVERSIONED after `git gc`, and R-02 then gives a misleading reason (OPS-3).
4. Double quotes in `.env` turn `\ntvenv` into a newline. `%LOCALAPPDATA%` is never expanded (OPS-4).
5. Nothing detects a global install of Nautilus or `pyarrow` (OPS-5).
6. A pilot killed after registration leaves rows with no run record. No re-run rule exists (OPS-6).
7. The Windows wheel pin and module baseline are trust-on-first-use. Both can be firmer (OPS-7).
8. Step 7A is not a runbook. The owner has no commands, no timing tool and no way back to Claude (OPS-8).

None of them breaks a house rule by design, so none is a blocker. Each has a small, concrete fix.

## Sections reviewed

- §2 owner rulings O1, O3, O9, O10, O13: venv placement, the wheel and Windows claims.
- §3.1 frozen pins, §3.3 hermeticity, §3.6 standard precision, §3.7 encoding, §3.8 concurrency, §3.11 CRLF.
- §4.1 to §4.3: the two processes, the data flow and the launch contract, row by row.
- §5.1 `requirements-nautilus.txt`: header command, closure, hashes, yank guard.
- §5.2.1, §5.2.7: exit codes, module baseline.
- §5.3.1, §5.3.2: CLI forms, rehearsal path checks, git checks, venv checks, order of operations.
- §5.7: NotRun and FAIL semantics of the `nautilus` suite.
- §6.2, §6.3, §6.5: `wheel_identity`, run record, card file.
- §7: refusal and error table, from the owner's console.
- §8.3 test 15, §8.4, §8.6: encoding guard, layer-2 tests, container rules.
- §9 Steps 3, 7A, 8, 10: install, hand-off and pilot runbook.
- §11 risks 3 to 6, 21, 23; §13 open questions 1 and 2.

Facts I checked against source, wheels and probes, with results:
- Windows closure size: 506.1 MB unpacked over 15 wheels (`scratch:closure/win`). Longest path inside any wheel:
  76 characters (`nautilus_trader/model/tick_scheme/implementations/tiered.cp313-win_amd64.pyd`).
- DLL imports of all 111 `.pyd` files in the win_amd64 wheel (my PE reader, `scratch:referee_ops/pe_imports.py`):
  only `python313.dll`, `vcruntime140.dll`, the UCRT `api-ms-win-crt-*` set and OS DLLs (`ws2_32`, `bcrypt`, `pdh`,
  `powrprof`, `psapi`, `userenv`, `combase`, `oleaut32`, `shell32`, `crypt32`, `advapi32`, `kernel32`, `ntdll`).
  No `msvcp140.dll` and no `vcruntime140_1.dll`, so no VC++ redistributable is needed.
- `SYSTEMROOT` is load-bearing. Every kernel calls `socket.gethostname()` (`nt:system/kernel.py:159`), and Winsock
  needs it.
- The 3.13 `getpath` script reads `__PYVENV_LAUNCHER__` without checking `use_environment`; it checks
  `PYTHONHOME` only under `use_environment`. I unmarshalled the frozen code from
  `/usr/lib/x86_64-linux-gnu/libpython3.13.so.1.0`; the disassembly is in `scratch:referee_ops/getpath_dis.txt`,
  source lines 300-321 against 334-335. So `-I` most likely does not break the venv redirector. The Windows C side
  is UNVERIFIED.

## Issues

### OPS-1 — major — §4.3 (timeout row), §7 C-06, Step 7A

**Problem.** The launch contract runs the child with `subprocess.run(..., timeout=900)`. On Windows the venv's
`Scripts\python.exe` is a redirector. It starts the base interpreter as a second process, which inherits the stdout
and stderr pipes. On timeout, `subprocess.run` kills the redirector only. It then drains pipes that the surviving
grandchild still holds open. The parent can hang for as long as the grandchild runs. At 3am that means a pilot frozen
after registration, with no run record.

**Evidence.**
- The house already hit this hang on the owner's machine. The docstring of `tools/debate.py:62-79` says:
  "subprocess.run's own timeout kills only the child and then waits on pipes that grandchildren … still hold open, so
  it can hang for the whole referee run." The fix there is `taskkill /T /F /PID` before draining.
- Ruling R9 accepted that process-tree kill as required behaviour
  (`docs/superpowers/plans/2026-10-23-execution-record.md:93`).
- CPython's own `multiprocessing` bypasses the venv redirector on Windows (bpo-35797). It launches
  `sys._base_executable` and sets `__PYVENV_LAUNCHER__` itself (`/usr/lib/python3.13/multiprocessing/popen_spawn_win32.py:62-67`).
- Whether 3.13's venv redirector kills its child when it is killed (a job object) is UNVERIFIED. The spec marks the
  redirector UNVERIFIED (spec:265-266), but its contract still picks `subprocess.run`.

**Proposed fix.**
- Launch through one helper that copies `tools/debate.py:_run`: `Popen` with `encoding="utf-8"` and
  `errors="replace"`, then `communicate(timeout=900)`. On timeout, run `taskkill /T /F /PID <pid>` on Windows (kill
  the process group on POSIX), then drain.
- Alternative: launch the base interpreter named by `home` in the venv's `pyvenv.cfg`, with
  `__PYVENV_LAUNCHER__=<venv python.exe>` in the env, as `multiprocessing` does. That removes the grandchild.
  C-10 already tolerates the variable.
- Add a layer-2 test. Run `<venv python> -I -c "import time; time.sleep(120)"` through the same helper with
  `timeout=3`. Assert that it returns within 15 s, that no child process survives, and that the temp dir can be
  deleted. Add it to the Step 7A done-when.

### OPS-2 — major — §3.7, §5.3.1, §8.3 test 15

**Problem.** The spec protects the child's encoding (`-X utf8`) but not the parent's. The parent runs as
`python -B -m tools.nautilus.runner`, with no UTF-8 mode. When its stdout is a pipe or a file, Python uses the locale
codec, cp949, with `errors="strict"`. That happens under a redirect, a scheduler, or an agent's shell. The runner
prints child tails that the spec itself decodes with `errors="replace"`, and U+FFFD cannot be encoded in cp949. The
first such print after registration raises `UnicodeEncodeError`. The G-06 handler then prints again and can fail
the same way.

**Evidence.**
- `tests/run_all.py:5-8` records the same failure: "The default on Windows Korean locale is cp949, which cannot encode
  the em dash or the Hangul … so the runner died with `UnicodeEncodeError`". The fix is at `tests/run_all.py:33-37`
  (`stream.reconfigure(encoding="utf-8", errors="replace")`).
- My probe: U+FFFD, U+2014 (em dash) and U+2713 fail to encode in cp949. U+0394 (Δ) and U+2265 (≥) succeed.
- Spec 4.3 (spec:260) decodes child output with `errors="replace"`, which produces U+FFFD. Spec 6.3 stores
  `stdout_tail` and `stderr_tail`.
- Layer-1 test 15 checks only `open`, `read_text` and `write_text` (spec:1053-1054). It does not check `git` or
  child `subprocess` calls, which decode with cp949 unless they pass `encoding=`. The house's own git helper passes it
  (`tools/paper/study.py:60`).

**Proposed fix.**
- At import, `tools/nautilus/runner.py` reconfigures `sys.stdout` and `sys.stderr` exactly as
  `tests/run_all.py:33-37` does.
- Every `subprocess` call in `tools/nautilus/`, the `git` calls included, passes `encoding="utf-8",
  errors="replace"`.
- Extend layer-1 test 15 to any `subprocess.run`, `Popen` or `check_output` call with `text=True` or
  `universal_newlines=True`: it must pass `encoding=`.
- Add a layer-1 test that drives the runner's status printer with a cp949 `TextIOWrapper` as stdout and a tail that
  contains U+FFFD.

### OPS-3 — major — §5.3.2 step 2, §7 R-02, §9 Step 7A, §13

**Problem.** `repo_anchor()` reads `.git/HEAD`, then the loose ref file it names. It has no `packed-refs` fallback.
`git gc` packs refs, and Git for Windows runs `gc --auto` on its own after fetches and commits. After a pack, a
healthy clone returns UNVERSIONED. R-02 then refuses with "Anchor UNVERSIONED". The owner reads that as "not a git
repo". The design fails closed, which is right, but the message is misleading and the remedy is not written down.
Synth listed this as UNVERIFIED. The spec dropped it from §13.

**Evidence.**
- `core/quant/gate_ledger.py:122-131` (`repo_anchor`).
- Probe in a temp repo, on a branch named like the feature branch, calling the real function:
  `loose: git:5605a61…`; after `git pack-refs --all`: `UNVERSIONED`; after `git checkout --detach`:
  `git:5605a61…`. `git rev-parse HEAD` gave the sha throughout.
- map02 §3.4: "It has no `packed-refs` fallback … UNVERIFIED there." Synth §5.2 lists "`repo_anchor()` on the owner's
  clone (packed refs, OneDrive)". The spec has no "packed" anywhere.
- House precedent for runs of record: "A clone's detached HEAD gives `git:<eacd57d…>`"
  (`docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:83-88`).

**Proposed fix.**
- Step 7A, after the commit: the owner runs `git switch --detach HEAD` before each pilot. A detached `HEAD` holds the
  sha itself, so `repo_anchor()` never reads a ref. Step 10 switches back to the branch before committing outputs.
  Untracked outputs carry over.
- R-02 diagnoses the case. If `repo_anchor()` is UNVERSIONED, `.git` is a directory and `git rev-parse HEAD`
  succeeds, the runner prints: "the branch ref is packed; run `git switch --detach HEAD` and re-run". If `.git` is a
  file, it prints the worktree message.
- Add a packed-refs case to layer-1 test 6. Restore the item to §13.

### OPS-4 — major — §2 O9, §4.3 "venv python", §5.1 header, §5.7

**Problem.** The `.env` line for `QUANTGEN_NAUTILUS_PYTHON` has two traps, and the spec's own wording leads into
both:
- `config.py` loads `.env` with python-dotenv. Dotenv decodes `\n`, `\t`, `\r`, `\a`, `\b`, `\f`, `\v` and `\\`
  inside double quotes. The spec's venv folder is `ntvenv`. So `"C:\…\quantgen\ntvenv\Scripts\python.exe"` becomes
  a path that contains a newline.
- O9 and the header write `%LOCALAPPDATA%\…`. Dotenv expands only `${VAR}`, so `%LOCALAPPDATA%` stays literal.
- Both paths then fail "not a file". Layer 2 reports `NotRun("… points to a missing file")` and does not show the
  value, so the newline stays invisible.

**Evidence.**
- python-dotenv 1.2.3 probe (`scratch:referee_ops/dotenv_probe/`):
  `A_DQ 'C:\\Users\\geon\\AppData\\Local\\quantgen\ntvenv\\Scripts\\python.exe'` (a real newline);
  single-quoted and unquoted values stay intact; `A_PCT '%LOCALAPPDATA%\\quantgen\\…'` stays literal.
- `config.py:26-27` calls `load_dotenv()` with defaults (`interpolate=True` expands `${VAR}` only).
  `config._clean` strips quotes after dotenv has already decoded the escapes (`config.py:32-39`).
- Spec: O9 (spec:96), header (spec:278), NotRun messages (spec:752-754).

**Proposed fix.**
- `.env.example` gains a commented example with an unquoted absolute path:
  `QUANTGEN_NAUTILUS_PYTHON=C:\Users\whydi\AppData\Local\quantgen\ntvenv\Scripts\python.exe`, and the line
  "no quotes, no %VAR%".
- The runner and the suite share one validator. It refuses a value that contains a control character or `%`, that is
  not absolute, or that does not end in `Scripts\python.exe` (Windows) or `bin/python` (POSIX). Every message prints
  `repr(value)` and the fix.
- Optionally, name the folder so that no segment after a backslash starts with one of `abfnrtv`, for example
  `…\quantgen\NTVenv`. Dotenv's escape set is lower-case only.
- Make a non-blank key that names a missing file a FAIL, not NotRun. The owner configured it, so a broken value is a
  regression. A blank key stays NotRun.

### OPS-5 — major — §3.1, §5.1 header, §5.3.2 step 3, §8.3

**Problem.** "Nautilus is never installed into the global interpreter" (spec:108) is a rule with no detector. The
header's install command (spec:278) uses cmd syntax only. In PowerShell, which is likely the owner's default
terminal (UNVERIFIED), it fails to parse. The obvious 3am "fix" is `python -m pip install --require-hashes -r
requirements-nautilus.txt`, which is a global install. The file pins numpy 2.3.5 and pandas 2.3.3, the same as the
global interpreter. So that install changes nothing that frozen_guard clause (d) checks. It silently adds
`nautilus_trader` and the banned `pyarrow` to the global interpreter.

**Evidence.**
- `tests/frozen_guard.py:85-91` compares only the versions in `LIBS`. Nothing checks for the absence of a package.
- `scratch:closure/requirements-nautilus.body.txt` pins `numpy==2.3.5`, `pandas==2.3.3`, `pyarrow==26.0.0`.
- The `pyarrow` ban: `research_notes/QUANTGEN v2 integration map/00_coordinator_rulings.md:54-55` (cited at
  spec:88).

**Proposed fix.**
- Runner step 3 and a new layer-1 test check the parent interpreter:
  - `importlib.metadata.version("nautilus_trader")` and `version("pyarrow")` must raise `PackageNotFoundError`;
  - numpy, pandas and scipy must equal the frozen pins.
- On failure, R-03 prints "Nautilus or pyarrow is installed in the global interpreter" and the exact uninstall line.
- The header gives both shells:
  - cmd: `"%LOCALAPPDATA%\quantgen\ntvenv\Scripts\python.exe" -m pip install …`
  - PowerShell: `& "$env:LOCALAPPDATA\quantgen\ntvenv\Scripts\python.exe" -m pip install …`
- The header also gives the venv creation line (see OPS-8).

### OPS-6 — major — §5.3.2 steps 9 to 16, §7 intro and G-06, §9 Step 8

**Problem.** The run record is written once, at the end (step 16). §7 promises that "After registration, every outcome
writes a run record" (spec:923-924). A process that is killed cannot keep that promise. On a home Windows machine,
the causes are ordinary:
- an automatic Windows Update restart, which is scheduled outside active hours, that is, at night;
- sleep;
- closing the console window;
- Ctrl+C, which raises `KeyboardInterrupt`, a `BaseException` that an `except Exception` handler misses.

The result is 24 immutable ledger rows with no record that explains them. The spec also never says whether the
owner may re-run. Layer-1 test 5 shows that a re-run appends 0 rows (spec:1039). Nothing says when a re-run is
legitimate, or how its record cites the earlier one.

**Evidence.**
- Spec:509 (step 16 is the only write); spec:921-924; G-06 at spec:958.
- `core/quant/gate_ledger.py:337-355`: a duplicate `config_id` appends nothing, so a re-run is mechanically safe.
- Whether a subprocess timeout counts sleep time on Windows is UNVERIFIED. If it does, a laptop that sleeps during a
  child wakes into C-06 and a WITHHELD record.

**Proposed fix.**
- Right after step 10, write a provisional run record atomically (a temp file, then `os.replace`). It carries
  `status: "REGISTERED"` and the full `registration` block. Update it at each phase. The final write replaces it.
- The final write sits in a `try/finally` that catches `BaseException`.
- Re-run rule:
  - A re-run with the same table is allowed only when the earlier record is `REGISTERED` (an orphan), `ERROR`, or
    `WITHHELD` for an infrastructure reason only (C-06 timeout or crash, or cleanup).
  - A re-run is never allowed after a hard parity failure or after a gate decision. The child is deterministic, so a
    re-run can only re-roll infrastructure.
  - The new record names the earlier `bridge_run_id` in a `supersedes` field.
- Step 8 runbook: plug in the power, disable sleep, pause updates for the run window, and run from a console that
  stays open.

### OPS-7 — major — §5.2.7, §5.3.1 `--record-baseline`, §6.2, §9 Step 7A.4, §13 q2

**Problem.** The Windows `wheel_identity` pin and the Windows module baseline are both recorded on the target machine
by `--record-baseline`. That is trust-on-first-use. The acceptance rule "the baseline's diff against the Linux one
shows only platform modules" is undefined, and no reviewer is named. The pin can be computed today. The open
question on install methods is already answerable.

**Evidence.**
- The spec's measured Linux digest `0ad0bfc4…` reproduces only when **every** sorted `path,hash` line ends in `\n`.
  A plain `"\n".join` gives `81de6b39…`. The spec does not state the serialisation. QA's proposed definition
  (`round1_claude_qa.md:308`) omits the trailing newline and would not reproduce the spec's own value.
- With the trailing-newline form:
  - Linux wheel RECORD: `0ad0bfc426d243f6334b0883b8a05e223199c6f6275359bbcd0c3cfa308407fb`, 761 entries;
  - installed in `scratch:ntvenv` (by path, `direct_url.json` present): the same value;
  - installed in `scratch:ntvenv_hash` (by name, no `direct_url.json`): the same value.
  So §13 question 2 and the Step 3 check are answered on Linux. `direct_url_sha256` differs between the two
  installs (present against null), so it cannot be part of the equality.
- Windows wheel `scratch:nt_win/…win_amd64.whl`, whose SHA-256 is `5fc8e08e…9aaf`, the spec's pin: digest
  `f5f53b9e603606f63b6a04620391d430acdf095210ee98b542dad1d74de2035b`, 761 entries. Equality after a real Windows
  install is UNVERIFIED. pip writes RECORD paths with `/` on every platform.
- Module set after `from nautilus_trader.backtest.engine import BacktestEngine` on Linux (minimal env, `-I -B -X
  utf8`): 974 modules. They include 5 `uvloop`, 33 `pyarrow` and the POSIX-only `fcntl`, `grp`, `pwd` and
  `_posixsubprocess`. Windows will lack `uvloop` and add `nt`, `_winapi`, `msvcrt` and similar. So a diff will exist,
  and "only platform modules" needs a rule.

**Proposed fix.**
- Commit the `win_amd64` entry of `env_pins.json` at Step 3, computed from the hashed wheel. Step 7A verifies it and
  never records it.
- Define `record_digest_sha256 = sha256("".join(l + "\n" for l in sorted(rows)))`, where `rows` are the
  `path,hash` lines under `nautilus_trader/` with a hash, encoded as UTF-8. Compare `wheel_tag`,
  `record_digest_sha256` and `record_entries` only, as QA also proposes.
- Baseline rule:
  - the `nautilus_trader.*` subset must equal Linux's exactly;
  - other differences must fall in a list declared in the spec: Windows and POSIX stdlib modules, and `uvloop.*`
    absent on Windows.
- `--record-baseline` prints the diff and refuses to overwrite an existing baseline. The owner commits the diff
  output with the baseline, and Claude reviews it before any pilot.

### OPS-8 — major — §9 Step 7A, Step 8, O9, §5.3.1

**Problem.** Step 7A tells the owner what to achieve, not what to type. It has six gaps:
- There is no venv creation command. It does not say which interpreter creates the venv.
- It does not forbid `--system-site-packages`.
- It gives no PowerShell form.
- The done-when needs the time of "12 synthetic runs of 5,600 bars" (spec:1175). None of the four CLI forms in
  §5.3.1 (spec:450-453) measures that.
- When 7A fails, "the hand-off stops and no pilot runs". The owner is not told what to send back.
- Step 8 says "Claude reads the outputs", but Claude is a Linux session ("a session like this one", spec:1104). Run
  records stay untracked until Step 10. No path brings them to Claude.

**Evidence.** Spec:1162-1186; the header at spec:273-279; §5.3.1 at spec:449-468.

**Proposed fix.** Add a numbered Windows runbook to §9, with exact cmd and PowerShell lines:
1. From the repo root, create the venv with the same `python` that runs the suite: `python -m venv <dir>`. Not
   `py -3.13`, and never `--system-site-packages`.
2. Install with `--require-hashes --only-binary=:all: --no-cache-dir`. Do not upgrade pip. Optionally install
   offline from a kept closure with `--no-index --find-links <dir>`. `scratch:closure/win` already holds all 15
   Windows wheels, 162 MB. A by-name install from that folder writes no `direct_url.json`, so it matches the pin.
3. Write the `.env` line in the OPS-4 form.
4. Run `--check-env`, then `--fixtures`.
5. Add a `--timing` mode, or fold timing into `--fixtures`. It prints the import time and the time of 12 runs of
   5,600 synthetic bars.
6. On any 7A failure, the runner writes one bundle, `docs/nautilus_bridge/handoff/<platform tag>.json`. It holds the
   check-env JSON, fixture diffs and child tails. The owner commits and pushes it.
7. After each pilot, the owner commits the run record and card and pushes them. A commit between pilots is allowed.
   The next pilot then anchors the new commit, which still holds the code.

### OPS-9 — minor — §4.3 env and cwd rows, §4.1 "then deletes the dir", §5.3.1 rehearsal row

**Problem.**
- The env points `USERPROFILE`, `HOME`, `TEMP` and `TMP` at `<tempdir>\home` and `<tempdir>\tmp`. The spec never says
  that the parent creates them.
- "Then deletes the dir" has no failure policy. On Windows, `shutil.rmtree` right after a child exits can raise
  `PermissionError [WinError 32]`. Defender may still be scanning the new files, or a redirector grandchild may still
  be alive (OPS-1). After registration, an unhandled raise becomes G-06 `ERROR`, so a pilot's status turns on a
  cleanup race.
- "Must resolve under `tempfile.gettempdir()`" does not say that both sides are resolved. On Windows, case
  differences and 8.3 short names break a naive prefix test.

**Evidence.** Spec:256, 214-216, 458. The owner's username is ASCII (`whydi`), so short names are unlikely here. A
general implementation still needs the rule.

**Proposed fix.**
- The parent creates `home` and `tmp` before launch.
- Cleanup is best effort: `shutil.rmtree(onexc=…)` with three retries 0.5 s apart. It never changes the status.
  Leftover paths go into the run record.
- The path checks compare `os.path.normcase(os.path.realpath(x))` on both sides.

### OPS-10 — minor — §5.3.2 step 2 (R-01), §7 R-04, §5.3.1 exit codes, §6.3 tails

**Problem.**
- The R-01 check parses `git status --porcelain` but does not fix its format. By default, git collapses untracked
  folders and octal-quotes non-ASCII names. A prefix test then fails on a quoted path inside an exempt folder.
- OneDrive conflict copies such as `<name>-<PC>.json` make the tree dirty.
- No refusal promises to list what it found.
- R-04 covers a price md5 mismatch, but not a missing or unreadable price file. An OneDrive Files On-Demand
  placeholder read while offline is one case. No exit code is defined for an unexpected exception before
  registration.
- Child tails will carry ANSI colour codes, because `LoggingConfig.log_colors` defaults to `True`
  (`nt:common/config.py:680`).
- A Windows crash code arrives as a bare `3221226505`.

**Evidence.**
- My porcelain probe (`scratch:referee_ops/porcelain_probe/`): the default output is `?? docs/nautilus_bridge/runs/`.
  `-uall` gives `?? "docs/nautilus_bridge/runs/\355\225\234…"`. `--porcelain=v1 -z -uall` gives raw UTF-8 names,
  one per file.
- R-06 has "missing, unreadable" but R-04 does not (spec:931, 933).

**Proposed fix.**
- Use `git status --porcelain=v1 -z --untracked-files=all` with `encoding="utf-8"`.
- Every refusal prints the offending items and the one command that fixes them.
- R-04 reads "missing, unreadable or md5 differs" and prints the OS error. Any exception before registration exits 2
  with its message.
- The last console line is always `STATUS <status> exit=<n> record=<path>`.
- Decode Windows NTSTATUS return codes in the record, for example `0xC0000409`, `0xC0000135` and `0xC000013A`.
- Pass `LoggingConfig(log_colors=False)`.

### OPS-11 — minor — §5.3.1 `owner_confirmed`, §9 Step 7A.6

**Problem.** The owner fills `owner_confirmed` by editing a JSON table by hand. PowerShell 5.1's
`Set-Content -Encoding UTF8` writes a BOM, and Notepad offers "UTF-8 with BOM". The spec reads every file with
`encoding="utf-8"` (§3.7). `json.loads` then raises `JSONDecodeError: Unexpected UTF-8 BOM`. That is an R-11-like
refusal at 3am, for a file the owner thinks is fine.

**Evidence.** Probe: `json.loads(bom_text)` raises that error after a `utf-8` decode and succeeds after a `utf-8-sig`
decode.

**Proposed fix.** Add `python -B -m tools.nautilus.runner --confirm <table> --by "<name>"`. It writes the field as
UTF-8 without a BOM, with LF line endings. As a fallback, read tables with `utf-8-sig` and print a clear message.

### OPS-12 — minor — §3.7, §6.3 `card.md5`, §6.5

**Problem.** §3.7 says text writes pass `newline="\n"`. The card is written by unchanged house code,
`ModelCard.save`, which calls `write_text(…, encoding="utf-8")` with no `newline=`. On Windows the card is CRLF. Its
md5 therefore differs from a Linux rehearsal of the same content. That is harmless if the spec says so. A reviewer who
compares card md5s across platforms would otherwise see a false mismatch. Separately, the card and the run record
each need the other's md5. QA-9 raised that circularity; I concur.

**Evidence.** `core/quant/validate.py:830-834`; spec:169-170, 864, 916.

**Proposed fix.** State that the card's md5 is over its on-disk bytes, CRLF on Windows, and is never compared across
platforms. Resolve the circularity as QA-9 proposes.

### OPS-13 — minor — §2 O9, §5.2.1 `--check-env`, Step 7A.3

**Problem.** The spec never says which interpreter creates the venv, and `--check-env` cannot see it. Microsoft Store
Python redirects writes under `%LOCALAPPDATA%` into a private
`…\Packages\PythonSoftwareFoundation.Python.3.13_…\LocalCache\Local\…` copy. Python's Windows docs list this as a
known issue (UNVERIFIED for this owner, whose distribution is not recorded anywhere in the repo). The owner would then
not find `%LOCALAPPDATA%\quantgen\ntvenv` in Explorer. A venv created with `--system-site-packages` would also expose
the global site-packages to the child.

**Evidence.** A repo grep finds no record of the owner's Python distribution. `pyvenv.cfg` carries `home` and
`include-system-site-packages`.

**Proposed fix.** `--check-env` reports `home` and `include-system-site-packages` from `pyvenv.cfg`, plus
`sys._base_executable`. The runner refuses `include-system-site-packages = true`. Step 7A records whether `home`
equals the directory of the suite interpreter, and warns if it lies under `WindowsApps`.

### OPS-14 — minor — §2 O9, §11 risk 23, §5.1, §3.1

**Problem.** Three statements are stale or off by one:
- "About 940 MB" (spec:96, 1323) is the Linux `site-packages` size (map01 §10.2). The Windows closure unpacks to
  506.1 MB (my measurement over `scratch:closure/win`), plus `.pyc` files.
- §5.1 says the other hashes and the `colorama` version are "collected in Step 3" (spec:285-291). They already exist
  in `scratch:closure/requirements-nautilus.body.txt` (`colorama==0.4.6`, both-platform hashes for every dist).
- §3.1 cites `tests/frozen_guard.py:90` for clause (d). The assert is at `:91`.

**Proposed fix.** Correct the size to about 0.5 to 0.6 GB on Windows. Fill in `colorama==0.4.6` and the collected
hashes, or point to the scratch file. Fix the line number.

### OPS-15 — minor — §3.8, §5.3.2

**Problem.** "Never concurrent with the suite" and single-run-at-a-time are enforced by instruction only. The ledger
itself is safe: appends hold an OS byte lock (`core/quant/gate_ledger.py:244-262`). Two runner instances of the same
table, started in two consoles at 3am, are not safe. Both pass `assert_hash_at_run`, because the second appended 0
rows. Both then write `cards/NB_E1_trend_spy.json`, and the last writer wins.

**Proposed fix.** The runner holds an exclusive lock for the whole run, using the same `msvcrt.locking` or
`fcntl.flock` pattern on `<ledger dir>/.nautilus_runner.lock`. A second instance refuses with "another runner is
active". Optionally, the runner refuses while `qa/acceptance_results.json` is open for writing. That is a cheap
signal that a suite is running.

## Notes

- **Long paths.** No risk. The longest path inside any Windows wheel is 76 characters. The venv base
  `C:\Users\whydi\AppData\Local\quantgen\ntvenv\Lib\site-packages\` is about 60.
- **Paths with spaces or Korean characters.** The known paths are ASCII: the repo at
  `C:/Users/whydi/OneDrive/Desktop/QUANTGEN` and `C:\Users\whydi\AppData\Local\agy\bin\agy.exe`
  (`tools/debate.py:47`). List argv handles spaces. Windows passes argv as UTF-16, so `-X utf8` does not affect
  paths. The real non-ASCII risk is in text output (OPS-2) and in porcelain parsing (OPS-10).
- **Byte-exact data.** `.gitattributes` holds `* -text`. `git ls-files --eol` shows `i/crlf w/crlf attr/-text` for
  `yf_SPY.csv`, `fred_DGS3MO.csv`, `config.py`, `README.md`, `requirements.txt` and `tests/run_all.py`. So the md5
  pins hold on Windows whatever `core.autocrlf` is. `config.py` is CRLF too, which §3.11 does not list. It is not
  edited, so this does not matter.
- **Antivirus.** The first import scans `nautilus_pyo3.pyd` (141.9 MB) and `backtest/engine.pyd` (82.1 MB). Linux
  import takes about 1 s (map01 §10.2). The 900 s timeout is ample. Controlled Folder Access is not a risk: the child
  writes only under `%TEMP%`, and the parent is the same `python.exe` that already writes
  `qa/acceptance_results.json` into the repo. Reinstalling the venv while a child, the suite or an editor holds its
  `.pyd` files fails with `WinError 5`, so never repair the venv during a run. Smart App Control or WDAC blocking of
  unsigned `.pyd` files is UNVERIFIED. The global stack already loads unsigned PyPI binaries, so it is unlikely.
- **Minimal env.** Every run calls `log_sysinfo` (`nt:backtest/engine.pyx:2071-2075`) whatever the log level, and
  the Rust core links `pdh`, `powrprof`, `userenv` and `combase`. How these behave under the minimal env on Windows
  is UNVERIFIED. Running F1, F2 and N1 through the exact contract at Step 7A covers it. Keep that gate.
- **`__PYVENV_LAUNCHER__`.** The 3.13 `getpath` reads it whatever `-I` says (see "Sections reviewed"). Whether the C
  side then clears it from the environment is UNVERIFIED. C-10's tolerance is harmless either way.
- **Overlap with other round-1 reports.** QA-9 (circular md5) and QA's wheel-identity fields overlap OPS-12 and
  OPS-7. OPS-7 adds the trailing-newline serialisation, the precomputed Windows digest and the by-name against
  by-path result. SECURITY-4 (no egress control on Windows) is outside my lens. Its proposed Step 7A outbound-connect
  probe fits naturally into the OPS-8 runbook.
- **Probe files.** `scratch:referee_ops/pe_imports.py`, `scratch:referee_ops/getpath_dis.txt`,
  `scratch:referee_ops/dotenv_probe/`, `scratch:referee_ops/anchor_probe/`, `scratch:referee_ops/porcelain_probe/`,
  `scratch:referee_ops/modprobe/`. None touched pilot-window data, a real ledger or the global interpreter's packages.
