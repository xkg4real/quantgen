# Round 3 referee report: Windows operations (Claude, ops lens)

Spec: `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md`, Revision 3 (cited as `spec:<line>`).
Repo: QUANTGEN at HEAD `7112351` (code unchanged since `6f7c610`). Nautilus: `nt:` = `nautilus_trader` 1.231.0 in
`scratch:ntvenv/lib/python3.13/site-packages/nautilus_trader/`.
`scratch:` = `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/`.
My probes are in `scratch:referee3_ops/`. They use synthetic values, the closure file, `requirements.txt` and the
installed `pandas` metadata. I read no pilot-window data, no real ledger and no BTC price. I ran no
`tests/run_all.py`, installed nothing globally and changed nothing outside this report.

Lens: the owner's machine. Windows 11, cp949, Microsoft Store Python 3.13 as the global interpreter, and the repo in
OneDrive at `C:/Users/whydi/OneDrive/Desktop/QUANTGEN`. For every step I asked two questions. What breaks at 3am? Does
the message tell the owner what to do? This round I also asked a third: what happens the second time?

## Verdict

**ACCEPT_WITH_CHANGES.**

Revision 3 closes all 8 of my round-2 issues and OPS-8, the one round-1 issue still open. The launch contract,
`write_record`, the re-run policy, the STATUS line and the checked Step 7A block are each specified well enough to
build.

Two new majors remain. Both come partly from my own round-2 proposals. Each is a one-paragraph fix.
1. **OPS-R3-1.** R-03's printed remedy for "Nautilus in the parent" uninstalls `python-dateutil`, `pytz` and `six`
   from the global interpreter. `pandas` needs them, so after the remedy `import pandas` fails. I measured this.
2. **OPS-R3-2.** Step 7A cannot be run a second time as written:
   - the registry check on line 4 finds the first attempt's own install and says "stop";
   - the spec does not say what `--record-baseline` returns when a baseline already exists;
   - a second `New-NetFirewallRule` adds a duplicate rule.

   A first-attempt failure is likely, because §13 lists five Windows facts as UNVERIFIED.

Seven minors follow. None of them changes the design.

## Sections reviewed

- **§4.3 launch contract and §4.4 egress layer** (spec:252-295). I checked these rows against my round-2 proposals: the
  `try/except BaseException` tree kill, the drain, `PATH` built from `os.environ["SYSTEMROOT"]`, and
  `normcase(realpath)` path comparison. I also checked the Store-Python refusal and how the egress record is matched.
  I read `nt:system/kernel.py:159` (`socket.gethostname()`), which needs `SYSTEMROOT`, and CPython 3.13's
  `platform.uname()` (`/usr/lib/python3.13/platform.py:688, 837-861, 968-1007`), which the sandbox now calls.
- **§5.1 header, §5.3.1 modes, §5.3.2 steps 0-4, §5.3.5 lifecycle** (spec:299-324, 626-688, 714-737). I checked:
  - `--handoff-report` and `--record-baseline`;
  - the pure-step functions and the test seams;
  - `write_record`, the lock and the run id;
  - the re-run policy and the exit codes.
- **§6.3, §6.6, §6.7** (spec:1003-1104): the `venv` record block, `table_sha256` and `code_sha256`, and the venv reads
  with the Store refusal.
- **§7 refusal table and its Remedy column** (spec:1117-1166). Every printed remedy was checked against the owner's
  global interpreter.
- **§8.3 L1-15 to L1-34 and §8.4 L2-5a, L2-5b, L2-10** (spec:1267-1315).
- **§9 Step 7A items 1-5, its done-when, the merge paragraph, and Step 8** (spec:1370-1430). I checked these line by
  line as the owner would paste them, then again as a second attempt after a failure.
- **§11 risks 5, 21, 23; §13 question 1; Appendix B rows OPS-1 to OPS-15 and OPS-R2-1 to OPS-R2-8.**

Facts I checked, with results:
- `requirements.txt:1-14` names `pandas` (`:8`) and `tzdata` (`:5`), but not `python-dateutil`, `pytz` or `six`. The
  installed `pandas-2.3.3.dist-info/METADATA` requires `python-dateutil>=2.8.2`, `pytz>=2020.1` and `tzdata>=2022.7`.
- `.gitignore:1-6` ignores `.env`, `__pycache__/`, `.pytest_cache/`, `*.pyc`, `.claude/settings.local.json` and
  `.serena/`. It has no `*.exe` entry.
- `tests/run_all.py:137` always writes `qa/acceptance_results.json`. `:142` returns 1 on any FAIL, so the Step 7A
  line `if ($LASTEXITCODE) { throw "suite" }` works.
- The committed Windows full run (`ac86705`) shows 749 PASS, 0 FAIL, 121 NOT_RUN and about 12.8 minutes of test time.
  The 7A done-when's "0 FAIL" is reachable.
- `origin/main` (`716bf77`) is an ancestor of the branch HEAD. The branch is 4 commits ahead.

## Earlier issues

Round 1:
- OPS-1: resolved. `Popen`, a new process group, a tree kill on timeout and on any exception, a 30 s drain, and L2-10
  (spec:262-263, 1315).
- OPS-2: resolved. The parent's streams are reconfigured, and every text-mode `subprocess` passes `encoding="utf-8"`
  (spec:168-172). L1-15 covers it (spec:1285).
- OPS-3: resolved. Step 2 names the packed-ref case, R-02 prints a command, and L1-6 has a pack-refs case
  (spec:671, 1126, 1276). The wording mismatch is listed under OPS-R3-9.
- OPS-4: resolved. Single quotes in `.env.example`, expansion, refusal of control characters, and `repr(value)` in
  R-03 (spec:144-146, 1073-1076). The suite's NotRun message still prints no value: minor, OPS-R3-9.
- OPS-5: resolved. L1-22 and the R-03 check (spec:672, 1292). The remedy that R-03 prints is wrong: new issue
  OPS-R3-1.
- OPS-6: resolved. `IN_PROGRESS`, `ABORTED` and `run.final.<pid>.json` (spec:722-728).
- OPS-7: resolved. Both identities are committed at Step 3 and verified at 7A (spec:1100-1104).
- OPS-8: resolved. `--handoff-report` runs last whatever failed, and it is committed and pushed (spec:644-647, 1405,
  1407). Step 8 gives the `powercfg` lines (spec:1430). Gaps in the report are listed under OPS-R3-4.
- OPS-9: resolved. `home` and `tmp` are created, `rmtree` retries, and leftovers are recorded (spec:263, 266).
- OPS-10: resolved. Porcelain v1 `-z`, `log_colors=False`, NTSTATUS hex and the STATUS line (spec:266, 368, 671, 734).
- OPS-11: resolved. The table is read with `utf-8-sig` (spec:173-174).
- OPS-12: resolved. The card is written with `open(path, "x", newline="\n")` (spec:818).
- OPS-13: resolved. The dedicated base interpreter, and `include-system-site-packages` is refused (spec:277-283,
  1078).
- OPS-14: resolved. About 506 MB, and `colorama` pinned (spec:97, 314).
- OPS-15: resolved. The per-table lock and R-16 (spec:719-721, 1140).

Round 2:
- OPS-R2-1: resolved. One command per line with checks, `Start-Process -Wait -PassThru`, the dedicated interpreter's
  pip, and `--record-baseline` refusing on a fixture mismatch (spec:642-643, 1383-1406). Re-runs and the installer's
  folder are new issues OPS-R3-2 and OPS-R3-3.
- OPS-R2-2: resolved. O9 names the Store Python, R-03 refuses a Store base, and the record holds the parent's
  executable (spec:97, 281-283, 1011, 1079-1081).
- OPS-R2-3: resolved. `write_record` with retries, best-effort intermediate writes, a fallback file and L1-34
  (spec:722-728, 1304).
- OPS-R2-4: resolved. `try/except BaseException` kills the tree, drains and re-raises; L1-27 covers the
  `child_started` hook (spec:262, 1297).
- OPS-R2-5: resolved. L2-5a always runs; L2-5b is NotRun on WinError 1314; the 7A done-when names it (spec:1312, 1425).
- OPS-R2-6: resolved. The Remedy column, the STATUS line for every mode, and `STATUS REFUSED exit=2` before
  registration (spec:733-737, 1123-1164). R-03's parent remedy is harmful: OPS-R3-1.
- OPS-R2-7: resolved. R-17, `--rerun-of`, `supersedes` and the card-of-record rule (spec:729-732, 1141). Which digest
  identifies a table is unclear: OPS-R3-5.
- OPS-R2-8: resolved. `PATH` is built from `os.environ["SYSTEMROOT"]`, paths compare as `normcase(realpath)`, and L1-23
  has a Windows case (spec:264, 267, 1293).

## New issues

### OPS-R3-1 — major — §7 R-03 Remedy (spec:1127), §5.3.2 step 3 (spec:672), §3.1 (spec:112-114)

**Problem.** For "`nautilus-trader` installed in the parent", R-03 prints "the printed `python -m pip uninstall -y` line
of the closure's packages absent from `requirements.txt`". The closure pins 16 distributions (spec:314-317).
`requirements.txt` lists `pandas` but not its own dependencies `python-dateutil`, `pytz` and `six`. The printed line
therefore removes them from the global interpreter. The owner had them before the accidental install, because
`pandas` needs them. After the remedy:
- `import pandas` fails, and so does every QUANTGEN app, paper_live readout and suite run;
- the frozen_guard cannot even check the pins.

The same line also removes `pyarrow`, which 3.1 and GOVERNANCE-7 say may belong to other owner packages ("reported,
not failed"). It also removes `click`, `colorama`, `fsspec` and `tqdm`, which are common dependencies of other tools.

The error came from my own round-2 OPS-R2-6, which proposed "the packages that the closure adds and `requirements.txt`
lacks". That rule is wrong because `requirements.txt` lists top-level packages only.

**Evidence.**
- `requirements.txt:1-14` has no `python-dateutil`, `pytz` or `six`.
- `pandas-2.3.3.dist-info/METADATA` has `Requires-Dist: python-dateutil>=2.8.2`, `pytz>=2020.1` and `tzdata>=2022.7`.
- `scratch:referee3_ops/remedy_probe.py`, run with `-I` under `scratch:ntvenv`, computed the set:
  `['click', 'colorama', 'fsspec', 'msgspec', 'nautilus-trader', 'portion', 'pyarrow', 'python-dateutil', 'pytz', 'six', 'sortedcontainers', 'tqdm', 'uvloop']`.
  With those modules blocked, it printed:
  `pandas import fails: Unable to import required dependencies: | pytz: No module named 'pytz' ... | dateutil: No module named 'dateutil' ...`
  (`remedy_probe.out`).

**Proposed fix.** Replace the parent remedy in R-03 (spec:1127) with:
```
python -m pip uninstall -y nautilus-trader
python -m pip check
python -c "import numpy, pandas, scipy; print(numpy.__version__, pandas.__version__, scipy.__version__)"
```
The last line must print `2.3.5 2.3.3 1.18.0`. The other closure packages are reported, as `pyarrow` already is, and
never uninstalled. If `pip check` or the versions are off, the message is "stop; an owner ruling". Never print a
bulk uninstall. L1-22's FAIL message prints the same three lines.

### OPS-R3-2 — major — §9 Step 7A item 2 (spec:1383-1406), §5.2.7 (spec:466-467), §5.3.1 (spec:639-648)

**Problem.** The spec expects Step 7A may fail and be run again: "If Step 7A fails and code changes afterwards, the
sentence does not cover the changed code" (spec:48-49, 1413-1414). §13 lists five Windows facts that are UNVERIFIED
until 7A, so a first-attempt failure is likely. As written, a second attempt cannot pass:
- (a) **Line 4 stops the re-run.** The registry check (spec:1387-1388) exists because a python.org per-user install
  is listed under `HKCU:\...\Uninstall`. The first attempt's own `py313` is such an install, so the second attempt
  lists it, and the runbook says "stop and report it". This rule came from my OPS-R2-1 proposal and did not consider a
  re-run.
- (b) **The fixtures line on a re-run is unspecified.** `--record-baseline` "never overwrites a baseline" (spec:466),
  but the spec gives no exit code for "a baseline already exists". Consider a first attempt where the fixtures passed
  and a later line, such as the suite, failed. The untracked `tools/nautilus/golden/modules_win_amd64.json` stays on
  disk. If Claude's fix then changes the census, the second attempt either:
  - throws "fixtures" and stops 7A, if the existing file makes it exit non-zero; or
  - keeps a stale baseline, which L2-6 then fails in the suite.

  The owner gets no instruction for either case.
- (c) **Duplicate firewall rules.** `New-NetFirewallRule` (spec:1396) adds a second rule with the same display name,
  since `Name` is a new GUID. R-14's check `Get-NetFirewallRule -DisplayName ...` then returns two rules.
- (d) **Overwrite rules are missing.** For `--egress-record` and `--handoff-report`, the spec does not say whether a
  second run overwrites the file. For the hand-off it must, because 7A.3 commits it "whatever happened".

**Evidence.** spec:1387-1388, 1396, 1400, 1405; spec:466-467, 642-643. The HKCU listing of per-user python.org installs
is the runbook's own premise (spec:1388). Burn's registration of the bundle is standard but UNVERIFIED on the owner's
machine.

**Proposed fix.**
- Add a re-entry rule at the top of the block: "If `$q\py313\python.exe` exists from an earlier attempt, skip from the
  registry line to the `pip download` line. The listed row is that install." `python -m venv` and the offline install
  are safe to repeat.
- Create the firewall rule only when it is absent:
  ```
  if (-not (Get-NetFirewallRule -DisplayName QUANTGEN-nautilus-block-out -ErrorAction SilentlyContinue)) { New-NetFirewallRule ... }
  ```
- `--record-baseline`, when a baseline already exists:
  - if the new union equals it, exit 0 with "unchanged";
  - otherwise exit 2, write nothing, print the diff and the line
    `Remove-Item tools\nautilus\golden\modules_win_amd64.json`, and say to run it only after Claude has reviewed the
    diff in the hand-off.
- `--egress-record` and `--handoff-report` always overwrite their file, and git keeps the history.
- Add a layer-1 case for the existing-baseline rule.

### OPS-R3-3 — minor — §9 Step 7A item 2 (spec:1375-1376, 1386-1391)

**Problem.**
- The installer is "downloaded into the current folder", and that folder is the main clone. `.gitignore` has no
  `*.exe` entry, so `python-3.13.<x>-amd64.exe` (about 27 MB, UNVERIFIED) stays untracked in the repo root. Three
  things follow:
  - the 7A done-when "`git status --porcelain` is empty" fails;
  - at Step 8, R-01 refuses with "commit or remove the printed paths";
  - a `git add -A` in 7A.3 would commit and push the installer.

  OneDrive also syncs it.
- `$q` is printed but never created. The installer's `/log "$q\py313-install.log"` then names a file in a folder that
  does not exist yet. Whether Burn creates the folder is UNVERIFIED.
- The Authenticode line and the registry line print results but stop nothing. The owner has to read "Valid" and an
  empty list. The registry line also misses an all-users python.org 3.13 under `HKLM:`.

**Proposed fix.**
- Start with `New-Item -ItemType Directory -Force $q | Out-Null`.
- Download the installer to `$q` and run `& "$q\python-3.13.<x>-amd64.exe"`.
- Add `if ((Get-AuthenticodeSignature $inst).Status -ne 'Valid') { throw "signature" }`.
- Run the registry query over both `HKCU:` and `HKLM:` (including `WOW6432Node`).
- 7A.3 names the files to `git add` one by one, never `-A`.

### OPS-R3-4 — minor — §5.3.1 `--handoff-report` (spec:644-647), Step 7A.3 (spec:1407-1411)

**Problem.** The hand-off report is the only file Claude sees after a failed 7A. The egress record and
`qa/acceptance_results.json` are committed only "if every line passed". The report holds check-env, guard-selftest,
the fixtures, the census and the timings. It misses the two steps most likely to fail:
- **Egress.** "Does the firewall rule bind the interpreter the redirector starts" is UNVERIFIED (§13 item 1). If
  `--egress-record` fails, Claude has neither the probe JSON nor `control_connect` nor the rule's state.
- **The suite.** If `python tests/run_all.py` fails, Claude has no FAIL rows, although `tests/run_all.py:137` always
  writes them.

The file name also depends on the platform tag, which 6.7 takes from the venv's `WHEEL` (spec:1085). If the venv was
never created, the report has no tag to use.

**Proposed fix.** The report adds three parts:
- a fresh probe and parent control connect, in the egress-record shape;
- the read-only output of
  `netsh advfirewall firewall show rule name=QUANTGEN-nautilus-block-out verbose`;
- the FAIL rows and every `nautilus/*` row of `qa/acceptance_results.json`, with that file's mtime.

The tag for the report's file name comes from the parent (`sysconfig.get_platform()` with `-` replaced by `_`), so the
report is named `win_amd64.json` even with no venv.

### OPS-R3-5 — minor — §5.3.5 (spec:716-732), §6.3 `table` (spec:1009), §6.6 (spec:1065-1069)

**Problem.** The spec uses two digests of a table:
- `sha256(table bytes)` for the run id and the lock (spec:716, 719);
- `table_sha256`, the canonical JSON without the owner fields, for `owner_confirmed` (spec:1065).

`earlier_runs` and R-17 match "the same table SHA-256" (spec:727), which most naturally reads as the raw bytes. Every
legitimate hand edit changes the raw bytes but not `table_sha256`:
- a new `owner_confirmed`, which a code change requires;
- a re-saved BOM or CRLF.

R-17 then sees no earlier run, and a second card is written without `supersedes`. That is the case OPS-R2-7 was meant
to catch. The card-of-record rule ("the latest `CARD_WRITTEN` ... no later record supersedes") still picks the newer
card, so the harm is limited to the missing refusal and the missing link.

**Evidence.** `scratch:referee3_ops/table_id_probe.py`:

| Table | raw sha256 (first 16 hex) | `table_sha256` (first 16 hex) |
|---|---|---|
| as committed | `138f45ce4b05568d` | `fb486532a2161e0c` |
| new `owner_confirmed` | `55f8865089e4be6b` | `fb486532a2161e0c` |
| BOM and CRLF re-save | `7d6413cea8fe780e` | `fb486532a2161e0c` |

**Proposed fix.** The lock name, the run-id suffix, `earlier_runs` and R-17 all use 6.6's `table_sha256`. 6.3's `table`
field stores both digests, each named. L1-5 adds a case: an earlier `CARD_WRITTEN` record, then the same table with a
changed `owner_confirmed`, must still give R-17.

### OPS-R3-6 — minor — §6.6 `code_sha256` (spec:1066-1069)

**Problem.** `code_sha256` hashes the sorted lines `"<repo-relative path>,<sha256>"`, and the spec says only that the
bytes match across platforms. It does not fix the path separator. On Windows, `str(path.relative_to(root))` gives
`tools\nautilus\runner.py`, so the digest differs from Linux for the same tree. Runs of record still work, because the
owner's `--fingerprint` and the runner both run on Windows. But Claude, in the 7A.4 review on Linux, cannot recompute
the `code <16 hex>` the owner quoted, and so cannot confirm that `owner_confirmed` names the reviewed tree.

**Evidence.** `scratch:referee3_ops/code_sha_probe.py` hashes the same bytes under both path flavours. The POSIX paths
give `52a09226e4bd76a5` and the Windows paths give `5918ee109e14f909` (`code_sha_probe.out`).

**Proposed fix.** Use `path.relative_to(repo_root).as_posix()`. 7A.4's review recomputes `code_sha256` on Linux at
the 7A.3 commit and compares it with both tables' `owner_confirmed`. L1-19 asserts that a `PureWindowsPath`-built list
gives the same digest.

### OPS-R3-7 — minor — Step 7A item 2 (spec:1385), Merge paragraph (spec:1417-1419), Step 10 (spec:1432)

**Problem.** `git switch claude/amazing-gauss-tdiguu` moves the owner's only working clone onto the feature branch.
The clone stays there through the pilots, which take days. The owner's other jobs run from the same clone, such as the
H2 readout. The spec has three gaps:
- It never checks that the branch still contains the owner's current `main`. If `origin/main` has moved past
  `716bf77` by then, the switch rolls those files back in the working tree. Other jobs then run on older code.
- It never says when the clone returns to `main`.
- It never gives the merge commands.

**Proposed fix.** Before the switch:
```
git merge-base --is-ancestor origin/main origin/claude/amazing-gauss-tdiguu; if ($LASTEXITCODE) { throw "main has moved: ask Claude to merge origin/main into the branch first" }
```
After Step 10, give the merge commands: `git switch main`, `git pull --ff-only`, `git merge --no-ff
claude/amazing-gauss-tdiguu`, `git push origin main`. Until then, readouts wait or run from a separate clone.

### OPS-R3-8 — minor — Step 8 (spec:1430)

**Problem.** "Restoring the old values afterwards" gives no way to learn the old values. `powercfg /change` may also
need elevation on some machines (UNVERIFIED). A run that dies leaves sleep turned off.

**Proposed fix.** Either print the current values first with
`powercfg /query SCHEME_CURRENT SUB_SLEEP STANDBYIDLE` and `... HIBERNATEIDLE`, or better, have the runner (the
parent, not the sandbox) call `SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)` from step 0 until the
final record. Windows releases that request when the process exits, so nothing needs restoring, and it needs no
admin. T-RO-01 does not forbid `ctypes` outside the sandbox (`tests/macro_m0_harness.py:38-42`). If the second option
is taken, the `powercfg` lines go.

### OPS-R3-9 — minor — wording and citations

- 5.7 (spec:931-932): the suite's NotRun "points to a missing file" still prints no value. Add `repr(value)`, as R-03
  does. This was carried from my round-2 note on OPS-4.
- R-02: step 2's message says "a new commit (the hand-off commit) writes the loose ref" (spec:671), while the Remedy
  column says `git commit --allow-empty -m "nautilus: re-anchor"` (spec:1126). At Step 8 the hand-off commit is in the
  past. Use the Remedy wording in both places and add "then `git push`", so the anchor is reachable from `origin`.
- R-14's Remedy (spec:1138) contains `\|`, which is markdown escaping. The runner must print `|`.
- Citations: `tests/run_all.py:35-38` (spec:169) is `:35-39`; `tools/debate.py:64-79` (spec:263) is `:64-78`.

## Why I agree or not

I do not agree yet, for two reasons. Both hit the failure paths that my lens exists to cover. Both also come partly from
my own round-2 proposals.
- OPS-R3-1: the spec tells the runner to print a remedy that breaks `pandas` in the global interpreter. A team building
  Step 6 would implement it exactly as written.
- OPS-R3-2: a team writing the runbook (Step 7) and `--record-baseline` (Step 6) would have an open question: what
  happens on the second attempt of Step 7A? A failed first attempt is the expected case.

Steps 2 to 5 can start today; nothing in them depends on these issues. If the moderator applies the fixes for OPS-R3-1
and OPS-R3-2 as proposed, I agree without another round. The minors can go in the same edit or into the Step 2 plan.

## Notes

- **Correction to my round 2.** OPS-R3-1 corrects OPS-R2-6's remedy rule. OPS-R3-2 (a) corrects OPS-R2-1's "stop and
  report it".
- **Ctrl+C on Windows** (UNVERIFIED). On 3.13 Windows, `communicate(timeout=...)` waits in `Thread.join`, and a lock
  wait there may not be interruptible. A `KeyboardInterrupt` may therefore arrive only when the current child ends,
  which takes seconds to minutes. This is harmless because the 4.3 handler still kills the tree. Closing the console
  window ends both processes.
- **`platform.uname()` in the sandbox** (UNVERIFIED on Windows). Its `_node()` calls `socket.gethostname()`. It queries
  WMI and then falls back to `cmd /c ver` and the `PROCESSOR_ARCHITECTURE` variable, which the child does not get
  (`/usr/lib/python3.13/platform.py:688, 837-861, 1005`). So `machine` may be empty. Nothing compares it.
- **Store-Python temp redirection** (UNVERIFIED).
  - 4.3's `os.path.realpath(mkdtemp())` is correct whether or not Store Python redirects TEMP writes.
  - The rehearsal check, "under `realpath(tempfile.gettempdir())`" (spec:635), would refuse if redirection applied. A
    redirected temp dir resolves under `...\Packages\PythonSoftwareFoundation...\LocalCache`.
  - The house's Windows evidence does not settle this. `tools/paper/selfcheck.py:835-859` passes either way.
  - The 7A suite would expose it. Cheap hardening: compute the temp root once as
    `realpath(dirname(mkdtemp()))`.
- **Egress probe with the network down.** A per-run probe that reports `blocked: true` while the machine is offline
  proves nothing about the rule. Of-record mode relies on the 7A record's `control_connect`. Adding a per-run parent
  control connect would close this. It is security's call; I raise no issue.
- **Third-party firewalls.** An antivirus suite that replaces Windows Firewall would leave the rule unenforced. The
  probe catches this, and R-14's Remedy names it. Whether the owner runs one is UNVERIFIED.
- **`Start-Process -ArgumentList`** joins its items with spaces and does not quote them. That is safe for
  `C:\Users\whydi\...`, but it would split `TargetDir` for a profile path that contains a space.
- **Lock file in OneDrive.** The lock file is created without a retry. A transient WinError 32 there becomes "an
  unexpected exception before registration", that is `STATUS REFUSED exit=2`. That is harmless, but the message is a
  traceback rather than "another runner is active".
- **Overlap.** None with `round3_claude_security.md` (SECURITY-R3-1, R3-2) or `round3_claude_quant.md` (QUANT-R3-1 to
  R3-3).
- **Probe files.** In `scratch:referee3_ops/`: `remedy_probe.py` and `remedy_probe.out`, `table_id_probe.py` and
  `table_id_probe.out`, `code_sha_probe.py` and `code_sha_probe.out`. None reads pilot-window data, a ledger or a BTC
  price, and none installs anything.
