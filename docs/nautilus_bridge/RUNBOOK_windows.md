# NautilusTrader bridge: Step 7A on Windows

This runbook repeats Step 7A of `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md` (section 9, revision 6)
in the order the spec gives it, with the PowerShell lines of 7A.2. Where this file and the spec differ, the spec
governs. No line below has run on Windows yet (UNVERIFIED until Step 7A).

**Pinned base interpreter: Python 3.13.14**, the python.org per-user amd64 installer `python-3.13.14-amd64.exe`,
installed into `%LOCALAPPDATA%\quantgen\py313` and used only for the bridge (spec 4.4, O9). It has the same 3.13
minor as the global interpreter, which is all the venv check reads (`python_minor` "3.13"). 3.13.14 is the patch the
owner's own interpreter reported when the studies of record were frozen (`grokteam/out/PREREG_book.json:126`), so a
Windows build of it exists. That python.org serves this file at the URL of the download line is UNVERIFIED: the
cloud container cannot reach python.org. If the download line fails, stop and ask Claude to pin another 3.13 patch
here; changing this file changes no digest (it is not in `code_sha256`, spec 6.6).

## O11 A2 addendum (2026-10-30)

The owner approved the registration-only E1 initialization path described in
[O11_A2_REGISTRATION.md](O11_A2_REGISTRATION.md). Complete that bounded step on the owner's Windows machine
before pilot price reads if E1 is missing/empty. Keep its receipt private. It does not satisfy the independent
review, Step 7A, host verification or `owner_confirmed` requirements below. The cloud's temporary-ledger tests
are separate from actual Windows acceptance. Existing C3 is never initialized or rewritten by A2.

## Before Step 7A

- Step 1b records the owner's decisions and implemented exceptions. Additional GPT/Gemini review is optional
  and NOT_PERFORMED under the explicit 2026-10-30 O8 decision in Appendix B. Its absence alone cannot block
  Windows hand-off. Existing Claude evidence and every technical/Windows acceptance condition remain.
- Nothing else from QUANTGEN runs meanwhile: no suite run, no frozen-study readout, no pilot (spec 3.8).
- Power is plugged in. The runner and the suite's layer-2 tests also keep the machine awake (spec 5.3.5, 5.7).

## 7A.1 The sign-off sentence (the owner, then Claude)

1. The owner writes, in the chat, the sentence of the spec's Owner context:
   "I approve spec 2026-10-26 revision <n>, the T-RO-01 exemption of its section 5.6 and the merge of
   claude/amazing-gauss-tdiguu into main. Geon Koh, <date>."
   It releases the merge and the T-RO-01 exemption only.
2. Before recording it, Claude runs `git fetch origin` and `git merge-base --is-ancestor origin/main HEAD`; if main
   has moved, Claude merges `origin/main` into the branch first, so the sentence covers the merged branch.
3. Claude records the sentence verbatim in the spec's Status block, commits, and asks the owner for approval to push;
   on approval, Claude pushes. Every Claude commit leaves `qa/acceptance_results.json` byte-identical and says so.
   Approved ordinary fixes/tests do not need a repeated general sign-off. Rerun affected technical/Windows
   validation; code/table changes still require fresh execution `owner_confirmed`. Research verdict changes,
   formal ledger execution and external publication retain separate approvals.

## 7A.2 The PowerShell block (the owner)

In the main clone, in a normal (not elevated) PowerShell window, run the lines below one at a time.

- **A throw in the five git lines** stops the block: send Claude the message, because the hand-off needs the branch.
- **A red error in any later line**: skip to the last line (`--handoff-report`), which always runs.
- **The fifth git line** (the fast-forward) brings Claude's fixes and a new sign-off into a re-entry.
- **Never** a whole-tree `checkout`, `reset`, `stash` or `clean` in the main clone, and never a worktree. `git switch`
  rewrites only files that differ; the branch leaves `docs/asset_expansion/cache/` alone.
- The installer is downloaded into `$q`, never into the clone. The dedicated interpreter's pip downloads the wheels
  before the firewall rule exists; the global pip never runs.

**Re-entry** (a second attempt after a failed one):
- If `$q\py313\python.exe` exists from an earlier attempt, the registry line lists that install: skip from the
  registry line to the rule check line.
- The rule check line shows whether the rule `QUANTGEN-nautilus-block-out` exists (empty output: no rule).
- While no rule exists, go on to the `pip download` line whatever `$q\wheels` holds: pip reuses every finished file
  whose hash it verifies. The rule exists only after an install has passed, because a red error at the install line
  skips to the last line.
- Once the rule exists, re-enter at the `venv` line: the rule blocks that interpreter's pip, and the offline
  `--require-hashes` install re-checks every hash. If `$q\wheels` is then missing, first run the elevated
  `Remove-NetFirewallRule` line alone, then re-enter at the download line.
- That a normal window can read the rule is UNVERIFIED; if it cannot, take the rule to exist once the elevated lines
  have run.
- The `venv`, install and runner lines are safe to repeat; the first firewall line removes any rule of that name
  before the second creates it; `--record-baseline` treats an existing baseline as spec 5.2.7 says.

```powershell
git fetch origin; if ($LASTEXITCODE) { throw "fetch" }
git merge-base --is-ancestor origin/main origin/claude/amazing-gauss-tdiguu; if ($LASTEXITCODE) { throw "main has moved: ask Claude to merge origin/main into the branch first" }
git merge-base --is-ancestor main origin/claude/amazing-gauss-tdiguu; if ($LASTEXITCODE) { throw "local main has unpushed commits: push them, then ask Claude to merge origin/main" }
git switch claude/amazing-gauss-tdiguu; if ($LASTEXITCODE) { throw "switch" }
git merge --ff-only origin/claude/amazing-gauss-tdiguu; if ($LASTEXITCODE) { throw "fast-forward: ask Claude" }
$q = Join-Path $env:LOCALAPPDATA "quantgen"; New-Item -ItemType Directory -Force $q | Out-Null; $q   # note the printed path
$u = "Microsoft\Windows\CurrentVersion\Uninstall\*"; Get-ItemProperty "HKCU:\Software\$u", "HKLM:\Software\$u", "HKLM:\Software\WOW6432Node\$u" -ErrorAction SilentlyContinue | ? DisplayName -like "Python 3.13*"
#   first attempt: any row is a python.org 3.13 already registered; stop and report it (the Store package is not listed there)
$v = "3.13.14"; $inst = "$q\python-$v-amd64.exe"   # the patch this runbook pins
$ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri "https://www.python.org/ftp/python/$v/python-$v-amd64.exe" -OutFile $inst
if ((Get-AuthenticodeSignature $inst).Status -ne "Valid") { throw "signature" }   # signer: Python Software Foundation (UNVERIFIED)
$p = Start-Process $inst -Wait -PassThru -ArgumentList "/quiet", "InstallAllUsers=0", "TargetDir=$q\py313", "PrependPath=0", "Include_launcher=0", "Shortcuts=0", "/log", "$q\py313-install.log"
if ($p.ExitCode -ne 0) { throw "installer exit $($p.ExitCode); see $q\py313-install.log" }
Get-NetFirewallRule -DisplayName QUANTGEN-nautilus-block-out -ErrorAction SilentlyContinue   # rule check
#   empty output (always on a first attempt): no rule, go on to the next line; a rule listed: skip to the venv line,
#   unless $q\wheels is missing: then the elevated Remove-NetFirewallRule line alone first, then the next line
& "$q\py313\python.exe" -m pip download --require-hashes --only-binary=:all: --no-deps -r requirements-nautilus.txt -d "$q\wheels"; if ($LASTEXITCODE) { throw "download" }
& "$q\py313\python.exe" -m venv "$q\ntvenv"; if ($LASTEXITCODE) { throw "venv" }
& "$env:LOCALAPPDATA\quantgen\ntvenv\Scripts\python.exe" -m pip install --require-hashes --only-binary=:all: --no-cache-dir --no-index --find-links "$env:LOCALAPPDATA\quantgen\wheels" -r requirements-nautilus.txt; if ($LASTEXITCODE) { throw "install" }
# elevated PowerShell, same Windows account, the printed path written out in full; both lines, then close that window:
Remove-NetFirewallRule -DisplayName QUANTGEN-nautilus-block-out -ErrorAction SilentlyContinue
New-NetFirewallRule -DisplayName "QUANTGEN-nautilus-block-out" -Direction Outbound -Action Block -Program "<printed path>\py313\python.exe" -Profile Any
# back in the normal window: add the .env line of 3.4 with the owner's path if absent, then:
python -B -m tools.nautilus.runner --check-env; if ($LASTEXITCODE) { throw "check-env" }
python -B -m tools.nautilus.runner --egress-record; if ($LASTEXITCODE) { throw "egress" }
python -B -m tools.nautilus.runner --fixtures --record-baseline; if ($LASTEXITCODE) { throw "fixtures" }
python -B -m tools.nautilus.runner --timing; if ($LASTEXITCODE) { throw "timing" }
python tests/run_all.py; if ($LASTEXITCODE) { throw "suite" }
python -B -m tools.nautilus.runner --fingerprint --table docs\nautilus_bridge\registration\pilot1_E1_spy.json; if ($LASTEXITCODE) { throw "fingerprint" }
python -B -m tools.nautilus.runner --fingerprint --table docs\nautilus_bridge\registration\pilot2_C3_btcusd.json; if ($LASTEXITCODE) { throw "fingerprint" }
python -B -m tools.nautilus.runner --handoff-report                      # always, last, whatever failed after the git lines
```

**The `.env` line** (spec 3.4): single quotes, forward slashes, no `%VAR%`. In double quotes python-dotenv would turn
the `\n` of `\ntvenv` into a newline. This line prints it with your path, ready to paste into `.env`:

```powershell
"QUANTGEN_NAUTILUS_PYTHON='" + ("$q\ntvenv\Scripts\python.exe" -replace '\\', '/') + "'"
```

**What each runner line must show:**
- `--check-env`: the pinned versions, the `win_amd64` identity `47d274d7...` with 764 entries, `HIGH_PRECISION`
  false and `FIXED_PRECISION` 9; `--guard-selftest`'s five outcomes; `STATUS OK exit=0`.
- `--egress-record`: writes `docs\nautilus_bridge\egress\win_amd64.json` with `probe.blocked` and
  `control_connect.ok` both true. A failed control connect prints its error first: this network does not reach
  1.1.1.1:443, so the record cannot prove the rule; run Step 7A on a network that does, or ask Claude.
- `--fixtures --record-baseline`: F1, F2 and N1 match their goldens, and `tools\nautilus\golden\modules_win_amd64.json`
  is written. A differing fixture writes nothing and exits 2; the hand-off stops and no pilot runs.
- `--timing`: the `BacktestEngine` import time and the wall time of 12 synthetic runs of 5,600 bars.
- `python tests/run_all.py`: 0 FAIL, the `nautilus` layer-2 tests PASS, `nautilus/test_l2_05b_input_linked_to_env_refused`
  the only `nautilus/*` NOT_RUN allowed (it needs Developer Mode for a symbolic link).
- `--fingerprint` (each table): `table_sha256`, `code_sha256`, then `host_fingerprint <64 hex>`; a
  `host_fingerprint null (...)` stops here (R-15, O11): the family ledger is missing or empty on this machine, and
  follow the separately approved O11 A2 procedure for E1; unresolved C3 still stops. Do not bypass R-15.
- `--handoff-report`: writes `docs\nautilus_bridge\handoff\win_amd64.json`, each part with its own result or error.

## 7A.3 Commit what Step 7A produced (the owner)

1. Whatever happened after the five git lines, commit and push the hand-off report:
   ```powershell
   git add docs/nautilus_bridge/handoff/win_amd64.json
   git commit -m "nautilus: Step 7A hand-off report (win_amd64)"
   git push
   ```
   A null host fingerprint stops here (R-15, O11).
2. If every line passed, fill both tables, then commit them with the Step 7A outputs as one change group. In each of
   `docs/nautilus_bridge/registration/pilot1_E1_spy.json` and `pilot2_C3_btcusd.json`, the last line before the
   closing `}` is `"reference_card_md5": ...`. Add a comma at its end and these two lines after it, with the values
   that table's `--fingerprint` printed (the first 16 hex of each digest, as the `owner_confirmed form:` line shows):
   ```
    "owner_confirmed": "Geon Koh, <YYYY-MM-DD>, table <16 hex>, code <16 hex>",
    "host_fingerprint": "<64 hex>"
   ```
   `owner_confirmed` approves of-record runs of that table. Then:
   ```powershell
   git add tools/nautilus/golden/modules_win_amd64.json docs/nautilus_bridge/egress/win_amd64.json docs/nautilus_bridge/registration/pilot1_E1_spy.json docs/nautilus_bridge/registration/pilot2_C3_btcusd.json qa/acceptance_results.json
   git commit -m "nautilus: Step 7A records (win_amd64), owner fields of both pilot tables"
   git push
   ```
   Name each path; never `git add -A`. This commit also writes the branch's loose ref.

## 7A.4 Claude's review (the next session)

Claude reviews the hand-off report and census diff. The scoped sign-off must remain an ancestor of the 7A.3
commit. List intervening changes and verify their approved scope. Ordinary fixes require fresh affected
technical/Windows evidence, not repeated general approval. Record that exact validation baseline commit;
from it to 7A.3, only evidence files may change (census baseline, egress record, hand-off report, both tables
and `qa/acceptance_results.json`);
recomputes `code_sha256` on Linux at the 7A.3 commit with `python3 -B -m tools.nautilus.runner --fingerprint --table
<table>` and compares it with both tables' `owner_confirmed`; and records the review in the spec's Appendix B.
Claude's review commit changes only the spec. If another change is needed, rerun the affected technical/Windows
checks and refresh code/table-bound `owner_confirmed`; do not reuse stale execution approval. No pilot runs
before that review. The O8 waiver changes no R-09/R-11/R-15 or freshness requirement.

## 7A.5 Before Step 8 (the owner)

```powershell
git pull --ff-only
```
The pilots anchor to that HEAD, and every pilot run record stores it.

## After Step 10: the merge (the owner)

A merge commit the owner makes himself, never a squash or a rebase, keeping the branch ref so every ledger anchor stays
reachable:
```powershell
git switch main
git pull --ff-only
git merge --no-ff claude/amazing-gauss-tdiguu
git push origin main
```
Until then the clone stays on the branch; readouts wait, or run from a separate clone, never during a pilot.

## Done when (spec Step 7A)

On Windows, `--check-env` reports the pinned versions, the `win_amd64` identity `47d274d7...` with 764 entries,
`HIGH_PRECISION` false and `FIXED_PRECISION` 9, and `--guard-selftest` behaves; the egress record shows
`probe.blocked` and `control_connect.ok` true; F1, F2 and N1 run through the exact launch contract and match their
goldens, or the hand-off stops and no pilot runs; the census diff obeys spec 5.2.7 and Claude has reviewed it; the
hand-off report holds the import time and the time of 12 synthetic runs of 5,600 bars; the full run shows 0 FAIL with
the `nautilus` layer-2 tests PASS, L2-5b the only `nautilus/*` NOT_RUN allowed, and the stub children start through
the interpreter spec 8.1's rule picks, recorded in the hand-off report; frozen_guard (a), (b) and (d) pass;
`repo_anchor()` returns `git:<the 7A.5 HEAD>`; `git status --porcelain` is empty.
