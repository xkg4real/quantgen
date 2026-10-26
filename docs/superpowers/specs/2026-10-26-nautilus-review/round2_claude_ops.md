# Round 2 referee report: Windows operations (Claude, ops lens)

Spec: `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md`, Revision 2 (cited as `spec:<line>`).
Repo: QUANTGEN code at `6f7c610` (the checkout is `a14954f`, which adds only the spec and the round-1 folder).
Nautilus: `nt:` = `nautilus_trader` 1.231.0 in `scratch:ntvenv/lib/python3.13/site-packages/nautilus_trader/`.
`scratch:` = `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/`.
My probes live in `scratch:referee2_ops/`. They use synthetic inputs, wheel files, source and temp git repos only. No
pilot-window data, no real ledger, no `tests/run_all.py`, no global install, no edit outside this report.

Lens: the owner's machine. Windows 11, cp949, the repo in OneDrive at `C:/Users/whydi/OneDrive/Desktop/QUANTGEN`
(`docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:19`). New this round: the global interpreter is the
**Microsoft Store Python 3.13** (`docs/asset_expansion/study.log:27, 29`; `grokteam/prereg.py:87-88`). Question asked
of every step: what breaks at 3am, and does the message tell the owner what to do?

## Verdict

**ACCEPT_WITH_CHANGES.**

Revision 2 fixes 14 of my 15 round-1 issues, and fixes them well. The launch contract now kills the process tree.
The parent's streams are UTF-8. The `.env` value is validated and printed with `repr`. A global install fails a test.
A crash leaves an `IN_PROGRESS` record. Both wheel identities are committed, and I reproduced both digests.

I still would not hand Step 7A to the owner as written. Two new majors:
1. OPS-R2-1. The Step 7A PowerShell block does not run as written. PowerShell does not wait for the GUI installer, so
   the next line runs against a half-installed interpreter. Commands chained with `;` keep going after a failure,
   and `--record-baseline` may write a baseline after a fixture failed.
2. OPS-R2-3. Revision 2 rewrites `run.json` about 26 times per pilot, by `os.replace`, inside the OneDrive-synced
   repo. One transient `WinError 5` or `32` becomes G-06 `ERROR` for a sound pilot.

OPS-8 stays open: when Step 7A fails, nothing is written for Claude to read. Six new minors follow. Each fix is small.

## Sections reviewed

- Status block and Owner context (sign-off mechanics only).
- §2 rulings O1, O9, O10, O13 and O15.
- §3.1 frozen pins, §3.3, §3.4 `.env`, §3.7 encoding, §3.8 concurrency, §3.11, §3.12.
- §4.1 to §4.4: processes, data flow, launch contract row by row, egress layer and its record.
- §5.1 header and body; §5.2.1; §5.2.3 engine row; §5.2.7 census; §5.3.1; §5.3.2 steps 0 to 4; §5.3.5 lifecycle;
  §5.7; §5.8 file table.
- §6.3 run record, §6.6 owner-edited fields, §6.7 venv reads and wheel identity, §6.8.
- §7 R-01 to R-03, R-14 to R-16, C-06, C-10, G-06, G-07.
- §8.1; §8.3 tests 5, 6, 15 to 17, 22 to 27; §8.4 tests 1, 5, 9, 10; §8.6.
- §9 Steps 3, 7A, 8 and 10; §11 risks 5, 19, 21; §13 questions 1 and 2; Appendix B rows OPS-1 to OPS-15.

Facts I checked, with results:
- Wheel identity (`scratch:referee2_ops/identity.py`, 6.7's rule): Linux wheel `a448cd20…f03f9`, 764 entries;
  Windows wheel `47d274d7…39555`, 764 entries; installed `RECORD` in `scratch:ntvenv` and `scratch:ntvenv_hash` both
  `a448cd20…`. The spec's values are right. Neither wheel has `entry_points.txt`, so pip writes no `Scripts\*.exe` row
  whose hash would depend on the machine. Wheel SHA-256 values match the pins (`5fc8e08e…`, `429ea61c…`). The body
  has 21 `--hash` lines, which matches 5.1's bracket counts.
- Import census (`census_build.py`, `run_proto.py`): an engine build gives 942 names (508 TP). Failed imports do
  appear (`winreg`, `plotly_not_here` in a control run), so try/except imports show on both platforms. A scan of every
  TP module in the census for platform-guarded imports found only `dateutil.tz.win` and `six.moves.winreg`, and both
  already appear on Linux as attempts. `nt:system/kernel.py:89-93` tries `uvloop`, so Windows will show a bare `uvloop`
  without its submodules; `uvloop*` covers it. F1 and F2 rerun with an empty `zoneinfo` TZPATH, as on Windows, changed
  only STD names and imported no `tzdata`. 5.2.7's cross-platform rule (TP differs only by `uvloop*` and
  `colorama*`) is plausible. Windows confirmation is still Step 7A's.
- Anchor (`anchor/probe.py`, the real `repo_anchor`): loose ref `git:b7ed…`; after `git pack-refs --all`
  `UNVERSIONED`; after `git commit --allow-empty` `git:9fbd…` with the loose ref back; after `git gc` `UNVERSIONED`
  again. R-02's message is true, and the condition can come back.
- Interrupt (`interrupt_probe.py`): a child started with `start_new_session=True`, while the parent waits in
  `communicate(timeout=900)`, survives the parent's `KeyboardInterrupt` ("child alive: True").

## Round-1 issues

- **OPS-1 resolved.** 4.3 uses `Popen` with a new process group, `communicate(timeout=900)`, then `taskkill /T /F` or
  `killpg` before draining (spec:252-253), and L2-10 tests it (spec:1118). The interrupt path is still open:
  OPS-R2-4.
- **OPS-2 resolved.** The runner reconfigures stdout and stderr (spec:157-158), and every text-mode `subprocess`,
  `git` included, passes `encoding="utf-8", errors="replace"` (spec:160-161). L1-15 covers it (spec:1086).
- **OPS-3 resolved.** R-02 names the packed-ref case (spec:499, 959), and L1-6 has a pack-refs case (spec:1077). My
  probe confirms that a new commit writes the loose ref. The command to print at Step 8 is not written: OPS-R2-6.
- **OPS-4 resolved.** `.env.example` uses single quotes and forward slashes (spec:133-135); 6.7 expands `%VAR%` and
  `~`, refuses control characters and prints `repr(value)` (spec:912-915). One small gap: the suite's NotRun message
  (spec:754-755) does not print the value. Add `repr(value)` there too.
- **OPS-5 resolved.** L1-22 fails while `nautilus-trader` is installed in the parent (spec:1093). R-03 refuses it
  (spec:500). The header gives cmd and PowerShell forms with "NEVER install with the global python" (spec:295-299).
- **OPS-6 resolved.** An `IN_PROGRESS` record is written after registration and after each child. The final write
  catches `BaseException`, and `KeyboardInterrupt` gives `ABORTED` (spec:549-552, 995). Step 8 names power, sleep
  and updates (spec:1226). The re-run rule is still unwritten: OPS-R2-7.
- **OPS-7 resolved.** Both identities are committed at Step 3 and verified, never recorded, at 7A (spec:937-939). The
  serialisation is stated (spec:922-926), and I reproduced both values. The cross-platform census rule is written
  (spec:453-456), and Claude reviews the diff (spec:1215-1216).
- **OPS-8 open.** The runbook exists, but it does not run as written (OPS-R2-1), and the failure path is still
  missing. `--check-env`, `--fixtures` and `--timing` print only (spec:483-484). So a failed Step 7A leaves nothing
  for a Linux Claude session to read, and the done-when's "timings are recorded" (spec:1220-1221) has no artefact.
  Step 8's power and sleep conditions have no commands. Fix: see "Open round-1 issue OPS-8" below.
- **OPS-9 resolved.** The parent creates `home` and `tmp`, cleanup retries 3 times and records leftovers, and path
  checks use `normcase(realpath)` (spec:254, 260, 476).
- **OPS-10 resolved.** Porcelain v1 `-z` with all untracked files (spec:499); R-04 includes missing and unreadable
  files (spec:961); `log_colors=False` (spec:357); NTSTATUS hex (spec:259); the `STATUS` last line (spec:553-554). An
  unexpected exception before registration still has no exit code: OPS-R2-6.
- **OPS-11 resolved.** The table is read with `utf-8-sig` (spec:162-163, 498).
- **OPS-12 resolved.** The bridge writes the card with `newline="\n"` and `open(path, "x")`, not `ModelCard.save`
  (spec:641). The run record holds the card's md5, not the reverse (spec:642, 885).
- **OPS-13 resolved.** A dedicated base interpreter is named (spec:88, 270-272). `pyvenv.cfg` is read, and
  `include-system-site-packages = true` is refused (spec:916-918). New evidence changes one detail: OPS-R2-2.
- **OPS-14 resolved.** The size is about 506 MB (spec:88), `colorama==0.4.6` is pinned (spec:305), and clause (d)
  is cited at `:91` (spec:102).
- **OPS-15 resolved.** A per-table OS lock (spec:546-548) and the freshness refusal R-16 (spec:497, 973).

### Open round-1 issue OPS-8: what is still missing

- **Failure bundle.** Add `runner --handoff-report`, run last in Step 7A whatever happened before it. It writes
  `docs/nautilus_bridge/handoff/<platform tag>.json` with:
  - the `--check-env` JSON and the parent's `sys.executable`, `sys._base_executable` and `sys.version`;
  - fixture results and diffs against the goldens, with child tails;
  - the census diff against the Linux baseline;
  - the two timings.
  The owner commits and pushes it whether Step 7A passed or failed. The 7A done-when names this file as the place
  the timings are "recorded".
- **Step 8 commands.** Add `powercfg /change standby-timeout-ac 0` and `powercfg /change hibernate-timeout-ac 0`,
  and the reverse after the run. Updates are paused in Settings, which has no stable command (UNVERIFIED).

## New issues

### OPS-R2-1 — major — §9 Step 7A item 2 (spec:1198-1211), §5.3.1 (spec:482-484)

**Problem.** The Step 7A command block fails on the owner's machine in four ways.
- (a) Line 3 runs `.\python-3.13.<x>-amd64.exe /quiet …` directly. PowerShell waits for console programs but returns
  at once from GUI-subsystem programs. The python.org installer is a WiX Burn bundle, which is a GUI program. So line 4
  (`& "…\py313\python.exe" -m venv …`) runs before the install ends. Pasted as a block, it fails with "not
  recognized". A second try then meets an install already in progress. No exit code is checked and no log is kept.
- (b) Nothing checks where the installer came from. Nothing checks whether a python.org 3.13 is already registered
  for this user. If one is, the bundle would modify or upgrade that install rather than add a second one beside it
  (UNVERIFIED; I could not fetch the installer docs).
- (c) Lines are chained with `;`, which runs the next command even after a failure, and PowerShell 5.1 has no `&&`.
  5.3.1 does not say whether `--fixtures --record-baseline` writes the baseline when a fixture fails. A standard
  precision mismatch in F1 could still leave `modules_win_amd64.json` on disk, and item 3 commits it.
- (d) The firewall line runs "in an elevated PowerShell". If the owner elevates with another account,
  `$env:LOCALAPPDATA` names that account's folder, and the rule binds a path that does not exist. The probe then
  refuses (fail closed), but nothing tells the owner why. The block also never says to close the elevated window,
  so the runner and the suite may run elevated.

**Evidence.** spec:1200-1207. 5.3.1 says only "`--record-baseline` also writes the census baseline" (spec:483-484).
The PowerShell wait behaviour is standard. The installer's subsystem is UNVERIFIED here: the container has no
PowerShell and no installer, and python.org is unreachable from it.

**Proposed fix.** Replace the block with one command per line, each followed by `if ($LASTEXITCODE) { throw }`
where it applies. The installer lines:
```
$base = Join-Path $env:LOCALAPPDATA "quantgen\py313"      # run in the normal window; note the printed path
Get-ItemProperty HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* | ? DisplayName -like "Python 3.13*"
#   any row here is a python.org 3.13 install: stop and report it (the Store package does not appear here)
(Get-AuthenticodeSignature .\python-3.13.<x>-amd64.exe).Status      # must be Valid, signer Python Software Foundation
$p = Start-Process .\python-3.13.<x>-amd64.exe -Wait -PassThru -ArgumentList "/quiet","InstallAllUsers=0",
     "TargetDir=$base","PrependPath=0","Include_launcher=0","Shortcuts=0","/log","$base-install.log"
if ($p.ExitCode -ne 0) { throw "installer exit $($p.ExitCode); see $base-install.log" }
```
Then: download the wheels with `& "$base\python.exe" -m pip download …` while the network is still open
(OPS-R2-2); create the venv; install offline. Create the firewall rule with the literal path printed above, not
`$env:LOCALAPPDATA`, and close the elevated window afterwards. 5.3.1: `--record-baseline` writes only when F1, F2
and N1 all match their goldens. Otherwise it exits non-zero and writes nothing.

### OPS-R2-2 — minor — §2 O9 (spec:88), §4.4 (spec:270-275), §6.7 (spec:916-918), Step 7A

**Problem.** The owner's global interpreter is the Microsoft Store Python 3.13. The spec never says so, and three
things follow from it.
- The runbook's first step (spec:1200) runs the Store interpreter's pip and writes into `%LOCALAPPDATA%`. python.org
  has documented that Store Python's writes under AppData can be redirected to the package's private `LocalCache`. If
  so, the venv's pip, which is not a Store process, finds an empty wheels folder and fails with "No matching
  distribution". House evidence suggests Temp writes are visible to other processes (see Evidence), so this is
  UNVERIFIED and probably minor. It also means the runbook runs the global pip, which the header tells the owner
  never to use.
- The owner's habit, `python -m venv …`, would build the venv on the Store interpreter. 6.7 only warns when `home`
  lies under `WindowsApps`. The egress probe then refuses because the rule does not bind that interpreter. The
  refusal names the probe, not the real cause.
- The Store interpreter updates its own patch level (`grokteam/prereg.py:87-88`). The parent's version can change
  between Step 7A and Step 8. That is harmless, because the pins check the minor version only, but the run record
  should show it.

**Evidence.** `docs/asset_expansion/study.log:27, 29` (site-packages under
`…\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\…`). `grokteam/prereg.py:87`. Visibility of
Store-written Temp files: `docs/b1_evidence/b1_experiment.py:123` wrote under `AppData\Local\Temp\claude\…`, and
`b1_results.json` reached the repo. The temp-dir git sandbox (`tools/paper/selfcheck.py:835-859`) passes on Windows
(`qa/acceptance_results.json` at `ac86705`). So the bridge's own parent-to-child temp dirs are not at risk.

**Proposed fix.**
- O9 and 4.4 state: "global interpreter: Microsoft Store Python 3.13; never used to create the venv or run pip for
  the bridge".
- Step 7A downloads the wheels with `<py313>\python.exe -m pip download`, before the firewall rule exists. The
  global pip never runs.
- 6.7 refuses (R-03) a `home` or `executable` under `WindowsApps` or `\Packages\PythonSoftwareFoundation.`. The
  message: "this venv was made from the Microsoft Store python; recreate it with `<py313>\python.exe -m venv …`".
- The run record's `venv` block adds the parent's `sys.executable`, `sys._base_executable` and `sys.version`.

### OPS-R2-3 — major — §5.3.5 (spec:549-552), §6.3 `earlier_runs` (spec:835), §7 G-06 (spec:994)

**Problem.** Revision 2 rewrites `run.json` with a `.tmp` file and `os.replace`:
- right after registration;
- after each child: 24 for pilot 1, 10 for pilot 2;
- at the end.
The folder is `docs/nautilus_bridge/runs/<id>/`, inside the OneDrive-synced repo. On Windows, `os.replace` fails
with `PermissionError` (WinError 5 or 32) while another process has the source or target open. The OneDrive client,
Defender and the indexer all open newly written files. Nothing in the spec catches this error after registration,
so G-06 turns a sound pilot into `ERROR` (exit 4). The final write can fail the same way and leave `IN_PROGRESS`.
Separately, `earlier_runs` reads every earlier `run.json`. With Files On-Demand, an online-only placeholder read
while offline raises too.

**Evidence.**
- The repo is in OneDrive (`docs/superpowers/plans/2026-10-23-quantgen-paper-pipeline.md:19`). The house already
  works around OneDrive: `core/quant/gate_package.py:69` and `grokteam/book.py:803`.
- pip wraps `os.replace` in a retry for this Windows failure:
  `scratch:ntvenv/lib/python3.13/site-packages/pip/_internal/utils/filesystem.py:71`
  (`replace = retry(stop_after_delay=1, wait=0.25)(os.replace)`).
- House precedent for best-effort state writes: `core/engine/runtime.py:378-385`.
- How often this happens on the owner's machine is UNVERIFIED.

**Proposed fix.**
- One helper, `write_record(path, obj)`. It writes to `mkstemp` in the same folder, fsyncs, then calls `os.replace`
  with up to 10 tries over 5 s on `PermissionError`.
- Intermediate writes are best effort. A failure adds to `record_write_failures` and never changes the status.
- The final write retries for longer. If it still fails, it writes `run.final.<pid>.json` beside the record, and the
  `STATUS` line names that file.
- Compute `earlier_runs` before registration (step 0), best effort. An unreadable record is listed as
  `UNREADABLE`.
- Add a layer-1 test with an `os.replace` seam that raises twice and then succeeds: the status is unchanged. When it
  always raises: the run continues, and the final write falls back.

### OPS-R2-4 — minor — §4.3 process and timeout rows (spec:252-253), §7 G-07 (spec:995)

**Problem.** The tree is killed only on timeout. By design, the child runs in its own process group or session, so
the console's Ctrl+C does not reach it. If the parent raises `KeyboardInterrupt`, or any other exception, while
`communicate` waits, the child keeps running. On POSIX it then has no timeout at all. A helper copied from
`tools/debate.py:64-77` uses `with Popen(...)`. Its `__exit__` waits about 0.25 s after a `KeyboardInterrupt` and
returns. After any other exception it waits for the child with no bound. Either way the record says `ABORTED` while
the child still holds its temp dir, and cleanup leaves it behind.

**Evidence.** `scratch:referee2_ops/interrupt_probe.py`: "parent got KeyboardInterrupt; child alive: True". Whether
Ctrl+C interrupts `communicate(timeout=…)` on Windows mid-child is UNVERIFIED. Closing the console window kills both
processes.

**Proposed fix.** Wrap the wait in `try/except BaseException`. On any exception: kill the tree, call
`communicate(timeout=30)`, then re-raise. On the timeout path, drain with `communicate(timeout=30)` as well, so a
surviving pipe holder cannot hang the parent. Add an L1-27 case: a hook raises `KeyboardInterrupt` while a sleeping
stub child runs. Assert `ABORTED`, that the stub's PID is gone and that the temp dir was removed.

### OPS-R2-5 — minor — §8.4 L2-5 (spec:1113), Step 7A done-when (spec:1221)

**Problem.** L2-5 is "NotRun on Windows if the OS refuses the link". Without admin rights or Developer Mode, Windows
refuses `os.symlink` (WinError 1314). Step 7A then needs "the `nautilus` layer-2 tests PASS". If the whole of L2-5
turns NotRun, the done-when fails. If the owner reads it loosely instead, the volume, precision and SHA-256 refusals
go untested on Windows.

**Proposed fix.** Split L2-5. L2-5a (volume, precision, doctored `bars_sha256`) always runs. L2-5b (the `.env`
symlink) is NotRun on WinError 1314, with "OWNER: enable Developer Mode, or accept this NotRun". The 7A done-when
names L2-5b as the only NotRun allowed.

### OPS-R2-6 — minor — §5.3.5 (spec:553-555), §7 R-02, R-03, R-14, R-16

**Problem.** The spec says every refusal prints "the one command that fixes them", but no command is written down. So
each implementer would invent one. Where the spec must decide:
- **R-02, packed refs.** At Step 8 "the hand-off commit" is already in the past, and a later `gc` can pack the ref
  again (my anchor probe). Print `git commit --allow-empty -m "nautilus: re-anchor"`.
- **R-14 on Windows.** Print the checks `Get-NetFirewallRule -DisplayName QUANTGEN-nautilus-block-out |
  Get-NetFirewallApplicationFilter` and `Get-NetFirewallProfile | Select Name, Enabled`. Say that a third-party
  firewall can disable Windows Firewall rules.
- **R-16.** Print the file and the seconds left until 600 s have passed.
- **R-03, Nautilus in the parent.** Print the uninstall line for the packages that the closure adds and
  `requirements.txt` lacks.
- **Crash before registration.** An unexpected exception before registration has no exit code. Python's default is 1,
  which 5.3.5 assigns to WITHHELD. Rule: print the traceback tail, then `STATUS REFUSED exit=2`.
- **Other modes.** `--check-env`, `--egress-record`, `--fixtures`, `--timing` and `--fingerprint` also end with
  the `STATUS` line, so the runbook can stop at the first non-zero exit.

**Proposed fix.** Add a "Remedy" column to section 7 with the commands above, and extend the `STATUS` rule to every
mode.

### OPS-R2-7 — minor — §5.3.5 (spec:545, 551-552), §6.3, Step 8 (carried from OPS-6)

**Problem.** No status forbids a re-run. A second run after `CARD_WRITTEN` writes a second `NB_E1_trend_spy.json`
into a new folder. Nothing says which card is the card of record, or that the new record supersedes the old one. At
3am after `ERROR` or `ABORTED`, the owner has no rule to follow.

**Proposed fix.**
- A re-run is allowed when every earlier record of the table is `IN_PROGRESS`, `ABORTED`, `ERROR`, or `WITHHELD` for
  an infrastructure reason only (C-06).
- Otherwise the runner refuses with exit 2, unless the owner passes `--rerun-of <id> --reason "<text>"`.
- The new record names the earlier run in `supersedes`.
- The card of record is the latest `CARD_WRITTEN` that no later record supersedes.

### OPS-R2-8 — minor — §4.3 Windows env row (spec:255), §4.4 (spec:285-286), §6.7 (spec:917-918)

**Problem.**
- `PATH = <venv Scripts dir>;%SYSTEMROOT%\System32`: an environment dict passed to `CreateProcess` is not expanded.
  Written literally, System32 is not on the child's PATH.
- The spec does not say how paths are compared in three checks: the egress record's `venv_python` and `base_python`
  against the current run's, and `executable` against `sys._base_executable`. The `.env` value can change from forward
  to back slashes, or to a `%LOCALAPPDATA%` form, without any real change. A raw string compare then refuses an
  of-record run with "egress record does not match".

**Proposed fix.** Build the PATH entry from `os.environ["SYSTEMROOT"]`. Compare paths everywhere as
`os.path.normcase(os.path.realpath(p))`. Store both the raw and the normalised form in the record.

## Notes

- **Correction to my round 1.** OPS-13 said the owner's Python distribution is "not recorded anywhere in the repo". It
  is recorded: it is the Store package (`docs/asset_expansion/study.log:27`). The dedicated interpreter of 4.4 is the
  right design for it, because a firewall rule on the Store interpreter would also block QUANTGEN's own fetches.
- **Citation drift.** 3.7 cites `tests/run_all.py:33-37` for the reconfigure loop. It sits at `:35-39`, and the call
  is at `:37`. My round 1 had the same drift.
- **`git switch` and the checkout rule.** Step 7A cites "never a whole-tree `checkout`" next to `git switch`
  (spec:1194-1199). The rule protects cache-file mtimes
  (`docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:89-91`). `git switch` rewrites only
  paths that differ between the two commits, and the branch leaves `docs/asset_expansion/cache/` alone. The runbook
  should say so, or the owner may stop at that line.
- **L2-10 "no child survives".** `os.kill(pid, 0)` is not a liveness check on Windows. There, 0 is
  `signal.CTRL_C_EVENT`, so the call sends a console control event. Use the temp-dir deletion the test already makes
  (a live process whose cwd is that dir blocks deletion), or `tasklist /FI "PID eq <pid>"`.
- **Minimal Windows env.** On 3.13, `platform.machine()` asks WMI first and falls back to `PROCESSOR_ARCHITECTURE`,
  which the child does not get. The manifest's `machine` may be empty (UNVERIFIED). Nothing compares it.
- **Venv redirector.** The 3.13 venv launcher probably holds its child in a kill-on-close job object (UNVERIFIED).
  The tree kill stays either way; it is harmless.
- **Overlap.** None with `round2_claude_security.md` or `round2_claude_quant.md`.
- **Probe files.** All in `scratch:referee2_ops/`: `identity.py`, `census_build.py`, `census_notz.py`,
  `run_proto.py` (runs `scratch:rev2_probe/rev2_sandbox_proto.py`, which prints only), `anchor/`,
  `interrupt_probe.py`, and their outputs. None read pilot-window data, a real ledger, a real BTC price, or changed a
  global package.
