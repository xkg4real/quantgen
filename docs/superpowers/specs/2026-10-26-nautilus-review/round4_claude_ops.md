# Round 4 referee report: Windows operations (Claude, ops lens)

Spec: `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md`, Revision 4, 1,772 lines (cited as `spec:<line>`).
Repo: QUANTGEN at HEAD `4f5f18b` (code unchanged since `6f7c610`). `nt:` = `nautilus_trader` 1.231.0 in
`scratch:ntvenv/lib/python3.13/site-packages/nautilus_trader/`.
`scratch:` = `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/`.

My probes are in `scratch:referee4_ops/`:
- `reentry_pip_probe.sh`, with `pipdl_offline.out` and `pipdl_offline_findlinks.out`;
- `reentry_git_probe.sh`, with `reentry_git_probe.out`.

They use the Linux closure wheels already in `scratch:closure/linux/`, the scratch venv, `unshare -rn`, and
throwaway git repositories inside the probe folder. I read no pilot-window data, no ledger and no BTC price. I ran no
`tests/run_all.py`, installed nothing globally, and changed nothing outside this report and the probe folder.

Lens: the owner's machine. That means Windows 11, cp949, the Microsoft Store Python 3.13 as the global interpreter,
and the clone in OneDrive. For each step I asked three questions:
- What breaks at 3am?
- Does the message tell the owner what to do?
- What happens the second time?

## Verdict

**ACCEPT_WITH_CHANGES.** One major and four minor issues.

What revision 4 resolves:
- OPS-R3-1 and OPS-R3-3 to OPS-R3-9, as ruled.
- Every round-1 and round-2 ops issue stays resolved.
- OPS-R3-2 in three of its four parts: (b) the existing-baseline rule, (c) the firewall rule made only when absent,
  and (d) the overwrite rules.

Part (a), the re-entry rule, went into the spec exactly as I proposed it, and my proposal was wrong.

**OPS-R4-1 (major).** A second attempt at Step 7A still cannot pass as written. I measured both causes:
1. **The download line is blocked.** Re-entry starts at the `pip download` line, which runs on
   `$q\py313\python.exe`. If the first attempt reached the firewall line, the rule blocks that interpreter. Every
   UNVERIFIED Windows fact of 13.1 is tested after the firewall line. With the rule in place, pip cannot reach its
   index and the line throws "download". Having every wheel already in the folder does not help: the measured result
   is exit 1.
2. **The block never pulls.** After Claude pushes a fix, `git fetch` followed by `git switch` to the branch the clone
   is already on leaves the old code in the working tree, with exit 0. The second attempt then has two problems:
   - It tests the old code.
   - The owner's hand-off push is rejected as non-fast-forward.

   The hand-off report records no HEAD, so Claude cannot tell from it which code ran.

The fix is two runbook lines and one report field. SECURITY-R4-2 found point 1 independently and rated it minor from
the isolation lens. From the ops lens it is the same failure as OPS-R3-2, which round 3 ruled major. Point 2 is new.

## Sections reviewed

I read all of Revision 4. These parts were read line by line against the code, the installed wheels and my earlier
proposals:
- **Status, Owner context, O8, O9** (spec:5-58, 100-101).
- **§3.1 frozen pins, §3.7 encoding, §3.8, §3.9 rehearsal containment** (spec:111-118, 170-191, 193-203).
- **§4.3 launch contract and §4.4 egress layer** (spec:259-303), including the hand-off report's second control
  connect.
- **§5.1** (spec:307-332).
- **§5.2.7 census and the existing-baseline rule** (spec:452-482).
- **§5.2.9 skeleton** (spec:493-645), read for `--check-env` and `--guard-selftest` only.
- **§5.3.1 modes, `--handoff-report`, the pure steps and the seams** (spec:649-694).
- **§5.3.2 steps 0 to 3** (spec:696-719).
- **§5.3.5 lifecycle**, including the `table_sha256` naming, `write_record`, the `SetThreadExecutionState` sleep guard,
  the re-run policy and the exit codes (spec:745-778).
- **§5.7, §5.8** (spec:968-1010).
- **§6.3, §6.6 digests, §6.7 venv reads** (spec:1049-1155).
- **§7**, with each Remedy checked against the owner's global interpreter (spec:1169-1219).
- **§8.1 stub child; §8.3 L1-5, L1-9, L1-15, L1-19, L1-22, L1-34, L1-35; §8.4 L2-5a, L2-5b, L2-9, L2-10**
  (spec:1225-1243, 1336-1378).
- **§9 Steps 1a to 7, all of Step 7A, the Merge paragraph, the done-when, and Steps 8 to 10** (spec:1418-1506). I
  read the 7A block twice: once as the owner would paste it on a first attempt, and once as a second attempt after a
  failure at each line in turn.
- **§11 risks 5, 19, 21, 23; §13; Appendix B round-3 rows and interpretations** (spec:1583-1617, 1739-1766).

Facts I checked, with results:
- `tests/macro_m0_harness.py:38-42`: `FORBIDDEN_IMPORTS` has no `ctypes`.
- `tests/acceptance.py:50-56`: `runtime_py()` scans `core`, `data`, `ui`, `main.py` and `config.py`, not `tools/`. So
  the runner's `ctypes` call passes T-RO-01, test_08 and test_09.
- `scratch:ntvenv/.../pip/_internal/cli/index_command.py:193`: pip skips its self-version check when `--no-index` is
  given. The offline install line (5.1) therefore makes no network call on a re-run.
- `/usr/lib/python3.13/ensurepip/__init__.py:163`: ensurepip installs with `--no-index`. A repeated `python -m venv`
  line therefore makes no network call either.
- These citations are correct:
  - `tests/run_all.py:35-39`
  - `tools/debate.py:64-78`
  - `config.py:176-178`
  - `core/quant/gate_ledger.py:244-262`
  - `core/quant/gate_package.py:36-38`
- `tests/run_all.py:120-142` writes `{"test", "status", "seconds", "detail"}` rows and returns 1 on any FAIL. So the
  hand-off's "FAIL rows" and the 7A line `if ($LASTEXITCODE) { throw "suite" }` both work.

## Earlier issues

Round 1, all still resolved (spot-checked for regressions):
- OPS-1: spec:270-271, L2-10.
- OPS-2: spec:172-177.
- OPS-3: spec:702, 1178, 1481.
- OPS-4: spec:149-151, 1124-1127.
- OPS-5: spec:116-118, 1179, 1353.
- OPS-6: spec:756-764, 1215.
- OPS-7: spec:1151-1155.
- OPS-8: spec:667-676, 1474, 1476.
- OPS-9: spec:271, 274.
- OPS-10: spec:376, 274, 702, 775.
- OPS-11: spec:178.
- OPS-12: spec:859.
- OPS-13: spec:285-291, 1128-1132.
- OPS-14: spec:101.
- OPS-15: spec:753-755.

Round 2, all still resolved:
- OPS-R2-1: spec:665-666, 1451-1475.
- OPS-R2-2: spec:101, 289-291, 1057, 1130-1132.
- OPS-R2-3: spec:756-762, L1-34.
- OPS-R2-4: spec:270, L1-27.
- OPS-R2-5: spec:1374, 1498.
- OPS-R2-6: spec:774-778, and the Remedy column of section 7.
- OPS-R2-7: spec:770-773, R-17.
- OPS-R2-8: spec:272, 275.

Round 3:
- **OPS-R3-1: resolved.** R-03 now prints exactly three lines: `python -m pip uninstall -y nautilus-trader`,
  `python -m pip check`, and the version line, which must print `2.3.5 2.3.3 1.18.0`. Other closure packages are
  reported and never uninstalled. A mismatch means "stop, an owner ruling" (spec:1179). L1-22's FAIL message prints
  the same lines (spec:1353), and §3.1 agrees (spec:116-118).
- **OPS-R3-2: partly resolved.**
  - (b) is resolved: `--record-baseline` prints "unchanged" and exits 0 for an equal baseline, and exits 2 with the
    diff and the `Remove-Item` line for a different one (spec:479-482, 665-666). L1-35 tests it (spec:1366).
  - (c) is resolved: the firewall rule is created only when absent (spec:1465).
  - (d) is resolved: `--egress-record` and `--handoff-report` overwrite their files (spec:675-676).
  - (a) is open. The re-entry rule (spec:1440-1444) sends the owner to the `pip download` line, which the first
    attempt's firewall rule blocks, and the block never pulls Claude's fix. See OPS-R4-1.
- **OPS-R3-3: resolved.**
  - `$q` is created (spec:1455), and the installer lives in `$q`, not the clone (spec:1440, 1458).
  - The signature line throws (spec:1458).
  - The registry query covers HKCU, HKLM and WOW6432Node (spec:1456).
  - `git add` names each file, never `-A` (spec:1481).
  - A wording remainder is in OPS-R4-5.
- **OPS-R3-4: resolved.**
  - The report gains a fresh probe and control connect, the rule dump, the FAIL rows and every `nautilus/*` row with
    the file's mtime.
  - Its tag comes from `sysconfig.get_platform()` (spec:667-674).
  - The rule dump's encoding is wrong: OPS-R4-3, which corrects my own proposal.
- **OPS-R3-5: resolved.** `table_sha256` names the table in the run id, the lock, `earlier_runs` and R-17, and the
  record keeps both digests (spec:747-752, 700, 1055, 1193). L1-5 covers a new `owner_confirmed` and a BOM-and-CRLF
  re-save (spec:1336).
- **OPS-R3-6: resolved.** `code_sha256` uses `as_posix()` paths (spec:1114-1115). L1-19 has the `PureWindowsPath`
  case (spec:1350). 7A.4 recomputes the digest on Linux (spec:1482-1483).
- **OPS-R3-7: resolved.** The ancestry check runs before the switch (spec:1453), and the merge commands are given
  (spec:1488-1492). Unpushed local `main` commits remain a gap: OPS-R4-5.
- **OPS-R3-8: resolved.** `SetThreadExecutionState(0x80000001)` is set at step 0 and cleared after the final record
  (spec:765-769). The `powercfg` lines are gone (spec:1504). Passed as a Python int, `0x80000001` converts through
  `PyLong_AsUnsignedLong`, so it raises no `OverflowError` (standard ctypes behaviour; UNVERIFIED on Windows).
- **OPS-R3-9: resolved.**
  - The suite's NotRun message prints `{value!r}` (spec:976-977).
  - R-02 has one wording, including `git push` (spec:702, 1178).
  - The `\|` note (spec:1218-1219).
  - The citations are corrected (spec:174, 271).

My round-3 notes: the Store temp-redirection note became open question 13.1 (spec:1616-1617), and revision 4's wider
containment rule makes it matter more (OPS-R4-4). The third-party-firewall note is in R-14's Remedy (spec:1190). The
other notes need no change.

## New issues

### OPS-R4-1 — major — Step 7A.2 re-entry (spec:1439-1475); 5.3.1 `--handoff-report` (spec:667-676)

**Problem.** The spec expects Step 7A to fail at least once: 13.1 lists six UNVERIFIED Windows facts, and 7A.4 plans
for "a code change after a failed Step 7A" (spec:1484-1485). The second attempt cannot pass as written.

- **(a) The download line is blocked by the first attempt's firewall rule.**
  - Re-entry "skips from the registry line to the `pip download` line" (spec:1441-1442).
  - That line runs `"$q\py313\python.exe" -m pip download ... -d "$q\wheels"` without `--no-index` (spec:1461).
  - The firewall line blocks outbound traffic for exactly that file (spec:1465).
  - pip asks its index for every requirement, even when the file already sits in `-d`. So once a first attempt has
    passed spec:1465, every later attempt throws "download" at spec:1461, and the owner skips to the hand-off.
  - The lines after the firewall line test the 13.1 facts: `--check-env` (the launcher), `--egress-record` (the rule
    binding), `--fixtures` (standard precision), and the suite (the stub start and the temp root). So this is the
    normal re-entry case, not an edge case.
- **(b) The block never pulls Claude's fix.**
  - The block runs `git fetch origin`, the ancestry check on `origin/...`, then `git switch claude/amazing-gauss-tdiguu`
    (spec:1452-1454).
  - Claude's fix and the new sign-off commit (7A.1) reach `origin` only. `git switch` to the branch already checked
    out does not move it, so the second attempt runs the old tree:
    - **If it fails again,** the hand-off shows the old failure as if the fix did not work.
    - **If it passes,** the owner writes `owner_confirmed` with the old `code_sha256`, and the 7A.3 push is rejected as
      non-fast-forward. No instruction covers that. Suppose the owner then merges:
      - 7A.4's recompute "at the 7A.3 commit" (spec:1482-1483) still matches the old code;
      - only Step 8's R-11 catches the mismatch.

    The failure mode is fail-closed. Still, it costs at least two owner and Claude cycles and produces misleading
    evidence. The same gap hits a first attempt if the clone already holds a local branch of that name from an
    earlier look.
- **(c) The hand-off records no git state.** Its parts (spec:668-674) hold no HEAD, so Claude cannot see which commit
  produced it.

**Evidence.**
- `scratch:referee4_ops/reentry_pip_probe.sh` runs the block's exact `pip download` flags with pip 26.2.2 under
  `unshare -rn`, with every Linux closure wheel already in `-d`:
  - The result is "ERROR: No matching distribution found for click==8.5.0", `exit=1`, after five retries to pypi.org
    (`pipdl_offline.out`).
  - The same command with `--no-index --find-links wheels` gives `exit=0`, "File was already downloaded"
    (`pipdl_offline_findlinks.out`).
  - On Windows the blocker is the firewall rule, not a namespace (UNVERIFIED there). Blocking exactly this
    interpreter's connections is the rule's purpose, and R-14 relies on it.
- `scratch:referee4_ops/reentry_git_probe.sh` uses throwaway repositories (`reentry_git_probe.out`):
  - The second `git switch feat` prints "Already on 'feat' ... behind 'origin/feat' by 1 commit" and exits 0.
  - `code.py` stays `v2` while `origin` holds `v3-fix`.
  - The hand-off push exits 1.
  - `git pull --ff-only` after the switch gives `v3-fix`.
- SECURITY-R4-2 (`round4_claude_security.md`) measured (a) independently.

**Proposed fix.**
1. Add one line after the switch line:
   ```
   git pull --ff-only; if ($LASTEXITCODE) { throw "pull: ask Claude" }
   ```
   It does nothing on a first attempt from a freshly created branch. On re-entry it brings Claude's fix and the new
   sign-off. Claude never commits `qa/acceptance_results.json`, a Windows baseline or a Windows egress record, so the
   leftovers of a failed attempt never block a fast-forward.
2. Replace the re-entry sentence with:
   > If `$q\py313\python.exe` exists from an earlier attempt, skip from the registry line to the `pip download` line.
   > If `$q\ntvenv\Lib\site-packages\nautilus_trader-1.231.0.dist-info` also exists, skip to the `venv` line instead:
   > the install passed, so the wheels are complete, and the firewall rule may already block pip's index.

   This key is exact. The install line comes before the firewall line, and a red error skips to the end, so the rule
   can exist only if the install passed.
   - An equivalent fix wraps the download line in
     `if (-not (Get-NetFirewallRule -DisplayName QUANTGEN-nautilus-block-out -ErrorAction SilentlyContinue)) { ... }`.
     UNVERIFIED: that a non-elevated window can read the rule.
   - Do not use "skip when `$q\wheels` exists". A download that failed halfway leaves the folder, and the install then
     throws.
3. `--handoff-report` adds `git rev-parse HEAD`, `git rev-parse origin/claude/amazing-gauss-tdiguu` and
   `git status --porcelain=v1`, each recording its own error.

### OPS-R4-2 — minor — leftovers of a failed attempt: the baseline and the firewall rule (spec:479-482, 1465; R-14, spec:1190)

**Problem.**
- **The leftover baseline.** `--record-baseline` treats any existing `modules_win_amd64.json` as a reviewed baseline:
  a different census exits 2 and waits for Claude's review (spec:479-482). After a failed first attempt, though, that
  file is an untracked leftover. 7A.3 commits it only if every line passed (spec:1477-1481), and Claude has never seen
  it. If Claude's fix changes the census, for example by adding a sandbox import:
  - the second attempt stops at the fixtures line;
  - Claude reviews a diff against a file nobody approved;
  - the owner then needs a third attempt.

  The rule protects a committed baseline. For an untracked one it adds nothing, because Claude reviews the Windows
  census against the Linux baseline at 7A.4, before any pilot (spec:1482).
- **The stale firewall rule.** The firewall rule is created only when absent, matched by display name (spec:1465). A
  rule made wrongly on the first attempt survives every re-entry, for example one with a mistyped path or a narrower
  profile. SECURITY-R4-3 raised this. The same one-line form below also covers it.

**Proposed fix.**
- **The baseline.** In 5.2.7, the existing-baseline rule applies only to a baseline git tracks
  (`git ls-files --error-unmatch <path>` exits 0). An untracked baseline is a leftover: `--record-baseline` replaces it
  and prints the diff. L1-35 adds the untracked case.
- **The firewall rule.** The elevated line becomes:
  ```
  Remove-NetFirewallRule -DisplayName QUANTGEN-nautilus-block-out -ErrorAction SilentlyContinue; New-NetFirewallRule -DisplayName "QUANTGEN-nautilus-block-out" -Direction Outbound -Action Block -Program "<printed path>\py313\python.exe" -Profile Any
  ```
  There is then always exactly one rule, always on the printed path. This keeps OPS-R3-2 (c) fixed. R-14's Windows
  Remedy names the same line.
- **The egress exit code.** I support SECURITY-R4-3's second point: `--egress-record` exits 2 unless `probe.blocked`
  and `control_connect.ok` are both true.

### OPS-R4-3 — minor — the hand-off's firewall dump is decoded as UTF-8 under cp949 (spec:670-672; §3.7, spec:172-177)

**Problem.** Section 5.3.1 puts the output of `netsh advfirewall firewall show rule name=QUANTGEN-nautilus-block-out
verbose` into the report. Section 3.7 makes every text-mode subprocess call decode UTF-8 with `errors="replace"`, and
the house locale is cp949 (spec:172). On a Korean Windows, netsh prints localized labels and values in the console
code page (UNVERIFIED: no Windows host here). Decoded as UTF-8, they become runs of U+FFFD. Only the ASCII survives,
which is the rule name and the program path.

The fields Claude needs after a failed egress line are the localized ones:
- enabled;
- action;
- direction;
- profiles.

My round-3 proposal named netsh; this corrects it.

**Proposed fix.** Replace netsh with the cmdlets R-14's Remedy already uses. Run them through
`powershell -NoProfile -NonInteractive -Command` with `Format-List`. Property and enum names are English, so the
output is ASCII:
```
Get-NetFirewallRule -DisplayName QUANTGEN-nautilus-block-out | Format-List DisplayName, Enabled, Direction, Action, Profile
Get-NetFirewallRule -DisplayName QUANTGEN-nautilus-block-out | Get-NetFirewallApplicationFilter | Format-List Program
Get-NetFirewallProfile | Format-List Name, Enabled
```
Alternatively, keep netsh and decode that one call with `encoding="oem"`, a Windows-only Python codec. L1-15 still
accepts it as an `encoding=` argument.

### OPS-R4-4 — minor — Store-Python temp redirection now gates every rehearsal (spec:198-203, 658, 1616-1617)

**Problem.** Revision 4 extends the "under `tempfile.gettempdir()`" rule from the ledger and output dirs to the
prices file (GOVERNANCE-R3-3). The comparison is `normcase(realpath(p))` against `normcase(realpath(gettempdir()))`.

Python's Windows notes say the Store package writes new files under shared locations such as TEMP to a private copy.
They also say `realpath` of such a file returns the private path, under
`...\Packages\PythonSoftwareFoundation.Python.3.13_...\LocalCache\Local\...`. This is UNVERIFIED for 3.13 on
Windows 11, and quoted from memory of the docs.

The parent of every layer-1 runner test, and of L2-7 and L2-12, is the Store Python (O9). If redirection applies:
1. each of those tests creates its ledger, output dir and synthetic prices with `mkdtemp`, gets R-10, and fails;
2. the 7A suite line fails;
3. a code change, a new sign-off and a re-entry follow.

Section 13.1 asks the question, but no answer is planned.

**Proposed fix.** Add one sentence to 3.9 and 5.3.1. The temp root is computed once per process, in two forms:
- `normcase(realpath(gettempdir()))`;
- `normcase(realpath(dirname(d)))`, where `d = mkdtemp()` is removed at once.

A path is inside the temp dir when it lies under either root. Neither root contains the repository, so
GOVERNANCE-R3-3's purpose holds, and L1-9's cases are unchanged.

### OPS-R4-5 — minor — wording and small gaps in Step 7A and 5.2.7

- **Installer.** 7A.2 says the installer is "downloaded into `$q`" (spec:1440) but gives neither a command nor a
  version, and `$inst` holds a literal `<x>` (spec:1458). Say two things: when the download happens (after the `$q`
  line), and where `<x>` comes from (the 3.13 patch the owner picks, the same minor as the global interpreter). Or give
  the line:
  ```
  Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.13.<x>/python-3.13.<x>-amd64.exe" -OutFile $inst
  ```
  The signature line then checks the download.
- **Local `main`.** The ancestry line checks `origin/main` only (spec:1453). Local `main` commits that were never
  pushed are rolled back in the working tree by the switch, for example a committed `qa/acceptance_results.json` from
  a Windows full run. Add:
  ```
  git merge-base --is-ancestor main origin/claude/amazing-gauss-tdiguu; if ($LASTEXITCODE) { throw "local main has unpushed commits: push them, then ask Claude to merge origin/main" }
  ```
- **Linux remedy.** 5.2.7 prints a PowerShell `Remove-Item` line on every platform (spec:481). On Linux (Step 6) it
  should print `rm tools/nautilus/golden/modules_<tag>.json`.
- **Sleep during 7A.**
  - `SetThreadExecutionState` covers table runs only (spec:765-767). The 7A suite runs about 13 minutes of house tests
    (Windows run `ac86705`) plus the layer-2 children, whose duration nobody has measured on Windows yet. Step 7A.2
    could carry Step 8's "power plugged in" sentence.
  - On Modern Standby laptops, `ES_SYSTEM_REQUIRED` alone may not keep a desktop app running once the display turns
    off. Adding `ES_DISPLAY_REQUIRED`, which makes `0x80000003`, is a cheap guard (UNVERIFIED).

## Why I agree or not

I do not agree yet, because of one major on the failure path my lens exists to cover. A failed first Step 7A is the
expected case, and round 3 ruled that the second attempt must work (OPS-R3-2, major). As written, it still cannot:
- It stops at the download line every time the first attempt reached the firewall rule.
- Otherwise it runs the code Claude has just replaced.

Both causes are deterministic, measured, and partly my own round-3 proposal.

The rest of revision 4 can be built. In particular:
- the launch contract;
- `write_record`;
- the `table_sha256` naming;
- the R-03 remedy;
- the hand-off report;
- the sleep guard.

If the moderator applies OPS-R4-1's fix as proposed, I agree without another round: the pull line, the dist-info
re-entry key, and the git fields in the hand-off. The minors can go into the same edit, into the Step 2 plan, or into
the runbook at Step 7. Steps 2 to 6 do not depend on any of them, except that the hand-off fields of OPS-R4-1(c) and
OPS-R4-3 are built at Step 6.

## Notes

- **Corrections to my own round 3.** OPS-R4-1 (a) corrects the re-entry point I proposed in OPS-R3-2 (a). OPS-R4-3
  corrects the netsh dump I proposed in OPS-R3-4.
- **Overlap with security.** SECURITY-R4-2 is OPS-R4-1 (a). I rate it major for the reason given in the Verdict, and I
  prefer the dist-info key over "skip when `$q\wheels` exists". SECURITY-R4-3: OPS-R4-2 gives one elevated line for
  its first problem, and I support its exit-code sentence.
- **Overlap with quant.** None with QUANT-R4-1 to QUANT-R4-3.
- **Not raised:**
  - `Start-Process -ArgumentList` still splits `TargetDir` for a profile path that contains a space. The owner's
    path does not.
  - A failed installer that leaves registry rows but no `py313\python.exe` would stop a re-entry at the registry
    line. Rare, and the message says to report it.
  - The control connect to 1.1.1.1:443 assumes the owner's network allows it. UNVERIFIED, and the record says so if
    it fails.
- **Probe files** in `scratch:referee4_ops/`:
  - `reentry_pip_probe.sh`, `pipdl_offline.out` and `pipdl_offline_findlinks.out`;
  - `reentry_git_probe.sh` and `reentry_git_probe.out`;
  - `wheels/` and `requirements-nautilus.txt`, which are copies of the Linux closure.

  None reads pilot-window data, a ledger or a BTC price, and none installs anything outside the probe folder.
