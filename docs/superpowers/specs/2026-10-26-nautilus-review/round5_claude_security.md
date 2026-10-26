# Round 5 (targeted) referee report: Claude, security-engineer lens

Scope of this targeted round (round4_rulings.md §1): the Step 7A hand-off procedure and the egress layer, on Revision 5.
Can any line of Step 7A, on a clean first attempt or on a second attempt after a failure, pass in a way that opens an
order or network path or commits a false of-record proof; do my three round-4 issues close; and does Revision 5's new
Step 7A prose (the `git pull --ff-only` line, the second ancestry check, the re-entry rule, the remove-then-create
firewall line, the `--egress-record` exit code and the R-14 Windows Remedy) introduce a new blocker or major.

I read my rounds 1 to 4 reports, the four rulings files, round5_claude_ops.md (already written), and all 1,849 lines
of Revision 5 in full, closely on Step 7A (spec L1464-1547), 4.4 and `--egress-record` (spec L285-309), 3.9 and 5.3.1
temp containment (spec L194-208, L662-717), and R-14 (spec L1218). `spec L<n>` is Revision 5 in the working tree.
`file:line` is QUANTGEN at HEAD `588c847`; code lines are unchanged since `f5742ab`. `nt:` is `nautilus_trader`
1.231.0 in `scratch:ntvenv`. `scratch:` is `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/`.

Probes are in `scratch:referee5_security/`. They read no price data, opened no real price cache, wrote no ledger row
outside a temp dir, and installed nothing globally. Every pip or Nautilus probe ran under `unshare -rn` with
`scratch:ntvenv` (pip 26.2.2) or the system `/usr/bin/python3.13`, so it had no network. `qa/acceptance_results.json`
is unchanged (md5 `16c9baa5a1777853521d485d5078e456`, equal to HEAD). I edited no repository file but this report.

## Verdict

AGREE. No blocker and no major. Three minor points, all fail-closed, none opening an order or network path.

Revision 5 is byte-for-byte unchanged where my boundary lives: the 5.2.9 skeleton and the 5.6 constants block are
identical to Revision 4 (`diff` clean against my verbatim Revision-4 extracts), both SHA-256 pins recompute from the
Revision-5 constants to the committed values, and all 46 of the 8.5 control multisets reproduce exactly under my own
scanner and the author's `scan4.py` rules. The egress layer (4.4, R-14) is still the real boundary and still fails
closed. All three of my round-4 issues are resolved as ruled. The round-5 changes are confined to the Step 7A runbook
and the of-record proof, and every failure path I walked stops with an actionable message or falls through to the
`--handoff-report` line.

## Sections reviewed

The parts I checked most closely, with the check and why the guard holds.

- **Step 7A, every line (spec L1464-1547).** Walked clean and re-entry at each line; see the next section. The order,
  the git/ancestry lines, the re-entry rule and the firewall line all fail closed.
- **4.4 egress layer and `--egress-record` (spec L285-309).** Revision 5 adds (SECURITY-R4-3): "`--egress-record`
  writes the record, then exits 2 (R-14) unless `probe.blocked` and `control_connect.ok` are both true" (spec L307).
  Of-record mode still re-reads the record's content and refuses unless `probe.blocked` and `control_connect.ok` are
  true and `venv_python`, `base_python` and `layer` equal the current run's (spec L308-309). So a record written with a
  failed proof (exit 2) cannot license a pilot: of-record re-reads it and refuses. Fail-closed.
- **R-14 (spec L1218).** Now carries the Windows Remedy for a wrong earlier rule: "if the filter's `Program` is not
  `<printed path>\py313\python.exe`, or the rule is disabled or not `-Profile Any`, the elevated firewall line of 7A.2
  again, which removes the rule by name before creating it (OPS-R4-2, SECURITY-R4-3); then `--egress-record`." This
  closes my round-4 SECURITY-R4-3 Problem 1 (a wrong rule was never corrected).
- **3.9 and 5.3.1 temp containment (spec L194-208, L673).** The two-form temp root (OPS-R4-4) is unchanged from the
  wording I accepted in round 4, and the rehearsal place rule is judged in `check_table` step 1 before any file opens
  (QA-R4-2). A symlink into `docs/asset_expansion/cache/` resolves out of both roots and is refused; a byte copy with a
  pinned md5 is refused by content. Not weakened by Revision 5. I opened no real cache to confirm (house rule); the
  logic is unchanged text.
- **5.6 scan (spec L893-994) and 5.2.9 skeleton (spec L518-660).** Re-extracted both verbatim from Revision 5 and
  diffed against my Revision-4 extracts: identical. Pins and controls reproduce (Earlier issues, below).
- **Launch contract (4.3) and the of-record seams (R-11).** Unchanged: every child still starts under `unshare -rn`
  (Linux) or the firewalled dedicated interpreter (Windows), and of-record mode refuses every test seam during
  argument validation. Not in the round-5 diff.

## Step 7A walk-through

Lines are numbered as they appear in 7A.2 (spec L1489-1517). "Clean" = first attempt, `$q\py313\python.exe` absent.
"Re-entry" = `$q\py313\python.exe` exists from an earlier attempt (spec L1474). Each line either succeeds or stops
with an actionable throw; the last line always runs.

7A.1 (Claude, spec L1466-1470): `git fetch origin`; `git merge-base --is-ancestor origin/main HEAD` and, if main
moved, merge `origin/main` into the branch first (GOVERNANCE-R4-2); record the sentence, commit, push on approval.
Clean and re-entry: a moved main is merged before the sentence is recorded, so the sentence covers the merged tree.
Fail path: none that is silent; a merge conflict stops Claude, which is a human loop. OK.

1. `git fetch origin` — clean/re-entry: succeeds, or throws "fetch". Actionable.
2. `git merge-base --is-ancestor origin/main origin/claude/...` — stops with "main has moved: ask Claude to merge
   origin/main into the branch first" if origin/main is not an ancestor of the branch. Actionable; it names the fix.
3. `git merge-base --is-ancestor main origin/claude/...` (new in Revision 5, GOVERNANCE-R4-2) — stops with "local main
   has unpushed commits: push them, then ask Claude to merge origin/main" if local `main` is ahead. Actionable.
4. `git switch claude/...` — succeeds (a no-op if already on the branch, which the Merge note keeps it on), or throws
   "switch". Actionable.
5. `git pull --ff-only` (new in Revision 5, OPS-R4-1(b)) — clean: fast-forwards local to origin, bringing Claude's
   7A.1 sign-off commit and any fix; re-entry: brings Claude's fixes into the second attempt, which is the point of the
   line. A non-fast-forward (local branch commits) throws "pull: ask Claude". Actionable, and it closes round-4
   OPS-R4-1(b), which security relied on: the second attempt now runs Claude's fixed tree, so a pass writes
   `owner_confirmed` against the fixed `code_sha256`, not a stale one.
6. `$q = Join-Path ...; New-Item -Force` — idempotent; prints the path. Clean/re-entry: succeeds.
7. Registry line — clean: any `Python 3.13*` row is a prior python.org install; the owner stops and reports it (the
   Store package is not listed there). Re-entry (`$q\py313\python.exe` exists): the listed row is that install, and the
   owner skips this line. Actionable on the clean stop.
8-12. `$v`/`$inst`; `Invoke-WebRequest` (OPS-R4-5); signature check; `Start-Process` installer; installer-exit check —
   clean: run in order; each throws on its own failure ("signature", "installer exit ..."). Re-entry with `$q\wheels`:
   skipped (the owner jumps to the venv line). Actionable throws. The installer runs with no network dependency the
   firewall affects; the rule does not yet exist here.
13. `& "$q\py313\python.exe" -m pip download ... -d "$q\wheels"` — clean: no rule exists yet (created at line 16), so
   the dedicated interpreter's pip reaches PyPI and fills `$q\wheels`, or throws "download". Re-entry: reached only
   while no `QUANTGEN-nautilus-block-out` rule exists (spec L1476-1477); because the rule is created only after a
   successful download+install, a re-entry that reaches this line has no rule and the download works, or the owner
   deleted `$q\wheels` after a failed first install, in which case still no rule exists and the download works (spec
   L1478-1480). This is exactly my round-4 SECURITY-R4-2, now resolved: the re-entry never runs this line against the
   firewall. Measured (Linux, pip 26.2.2, under `unshare -rn`): with the rule analogue in place the index is
   unreachable; the re-entry order avoids the line so it never throws on a second pass. Actionable.
14. `python -m venv "$q\ntvenv"` — clean: creates the venv. Re-entry: reruns on an existing venv. Measured: a repeat
   `python3.13 -m venv` on an existing venv exits 0 (`scratch:referee5_security/pipprobe`). Throws "venv" on failure.
15. Offline install line (5.1 header, `--require-hashes --only-binary=:all: --no-index --find-links "$q\wheels"`) —
   clean: installs from the local folder. Re-entry: re-checks every wheel hash offline. Measured: an offline
   `--require-hashes` install of an already-installed distribution exits 0 even when the `--find-links` folder is empty
   ("Requirement already satisfied"), so the repeat is safe and needs no network. Throws "install" on failure.
16. Elevated firewall line, now `Remove-NetFirewallRule ... -ErrorAction SilentlyContinue; New-NetFirewallRule ...`
   (OPS-R4-2) — clean: creates the rule. Re-entry: removes any same-name rule first, then creates a fresh one, so a
   wrong earlier rule (bad program path, disabled, wrong profile) is replaced, not kept. No child runs during this
   window (the runner lines are back in the normal window), so the brief absence of the rule exposes nothing. This
   closes my round-4 SECURITY-R4-3 Problem 1. UNVERIFIED on Windows that the rule binds the redirector-started
   interpreter (no Windows host); gated by line 19's probe.
17. `.env` line — add once; harmless to re-add on re-entry.
18. `--check-env` — launches the sandbox through the firewalled venv; succeeds or throws "check-env". The engine build
   needs no outbound; any socket a loaded Rust client opens fails under the rule (UNVERIFIED on Windows, gated here).
19. `--egress-record` — clean/re-entry: writes `docs/nautilus_bridge/egress/win_amd64.json`, then exits 0 only if
   `probe.blocked` and `control_connect.ok` are both true (spec L307), else exits 2 and the line throws "egress". So a
   failed proof stops here and the owner falls through to the hand-off; it never silently licenses a pilot. This is my
   round-4 SECURITY-R4-3 Problem 2, now resolved. If the firewall does not bind the interpreter the redirector starts,
   the probe connects, `probe.blocked` is false, exit 2, throw. Fail-closed and actionable (R-14 Remedy names the fix).
20. `--fixtures --record-baseline` — clean: writes `modules_win_amd64.json`. Re-entry: the baseline from a prior
   attempt is untracked (committed only at 7A.3), so `record_baseline` replaces it and prints the diff, exit 0
   (OPS-R4-2); a tracked equal one gives "unchanged"; a tracked different one writes nothing, prints the removal line
   and exits 2 (the line has no `throw`, so the owner reads exit≠0 and the record). Does not open any path.
21-24. `--timing`; `python tests/run_all.py`; two `--fingerprint` lines — each throws on its own failure. The suite is
   the owner's Windows suite of record (8.6), not a line I am barred from (my house rule binds the Linux container and
   me). `--fingerprint` opens no data file and always prints both digests (GOVERNANCE-R4-1). Actionable throws.
25. `--handoff-report` — always runs last, whatever failed above (spec L1516); on Windows through `powershell
   -NoProfile -NonInteractive -Command` with `Format-List` (OPS-R4-3), from the global interpreter, which is allowed to
   reach the network for its own control connect. This is the fall-through that every earlier throw lands on.

Second-attempt summary: a failure at lines 18-24 (where the UNVERIFIED Windows facts live) throws, the owner skips to
line 25, commits the hand-off report (7A.3, spec L1518), and Claude fixes the tree; the owner then re-enters from line
1, line 5 pulls the fix, and the re-entry rule skips the install block safely. No second attempt reaches the
`pip download` line against the firewall, writes a false egress proof that licenses a pilot, or keeps a wrong firewall
rule. Every stop is actionable.

## Earlier issues

Round 4 (all three resolved):
- **SECURITY-R4-1 (minor): resolved as ruled (wording).** 5.2.2 now reads "Rule F rejects the direct spellings
  (`import sys`, module-alias subscripts, dunders, dynamic calls); an attribute path through a loaded module can still
  reach `sys.modules`, which the scan cannot fully close; the egress layer bounds any use" (spec L378-380), and risk 2
  carries the same (spec L1635). The optional rule-F hardening was not applied, as ruled; rules A to F, the skeleton
  and both pins are unchanged (confirmed below).
- **SECURITY-R4-2 (minor): resolved (as OPS-R4-1).** The re-entry order skips to the `venv` line when `$q\wheels`
  exists and reaches the `pip download` line only while no `QUANTGEN-nautilus-block-out` rule exists (spec L1476-1477),
  so no second attempt runs `pip download` through the firewalled interpreter. Walked at line 13 above.
- **SECURITY-R4-3 (minor): resolved.** `--egress-record` exits 2 unless both proof flags are true (spec L307); R-14's
  Windows Remedy covers a wrong earlier rule (spec L1218); the firewall line removes any same-name rule before it
  creates the rule (spec L1507).

Rounds 1 to 3, re-checked against Revision 5 (no regression):
- **SECURITY-1 (blocker): resolved.** Egress is mandatory and in scope (3.12, 4.4), the scan is one layer of three.
  I re-confirmed under `unshare -rn` that a process the child `exec`s inherits the empty network namespace: a grandchild
  started with `os.execlp` still fails to connect with errno 101 (`scratch:referee5_security`, run under `unshare -rn`).
  So the Linux boundary binds not only the child but anything it launches.
- **SECURITY-2 to SECURITY-7, SECURITY-R2-1, SECURITY-R2-2, SECURITY-R3-1, SECURITY-R3-2: resolved, unchanged.** Both
  pins recompute to the committed `2792ad4a...` and `70bcf50f...` (`scratch:referee5_security/pins.py`). All 8.5
  controls reproduce exactly under my scanner and the author's rules (`scratch:referee5_security/controls_r5.py`:
  mismatches 0; e.g. verbs {A, CALL x8, TEXT}, `sys.modules` {C3, E, F1}, module chain {F4}, path {F5}, os call {F6},
  14 banned-module and 12 banned-name controls each as stated). The non-subscript reach probes (SECURITY-R4-1) still
  give NO HITS under both scanners, as conceded; the egress layer bounds any use.

## New issues

### SECURITY-R5-1 (minor): one re-entry combination has no stated target line

- **Section:** Step 7A.2 re-entry (spec L1474-1480).
- **Problem.** The re-entry rule gives two targets: `$q\wheels` exists -> the `venv` line; `$q\wheels` missing and no
  firewall rule -> the `pip download` line. It does not name a target for "`$q\py313\python.exe` exists, `$q\wheels`
  missing, and the `QUANTGEN-nautilus-block-out` rule exists".
- **Why it is only minor and fail-closed.** That combination cannot arise in the documented flow: the rule is created
  (line 16) only after the download (line 13) and install (line 15) have passed, and the download creates `$q\wheels`;
  the only deletion of `$q\wheels` the runbook directs is "before a first passing install" (spec L1478-1480), when no
  rule yet exists. If an owner reached it by a manual deletion out of order, the worst case is that they run the
  `pip download` line, which throws "download" because the rule blocks that interpreter, and they fall through to
  `--handoff-report` (spec L1516) exactly as the old SECURITY-R4-2 behaviour: one owner round trip, no route opened and
  no false proof. So it costs owner time, not safety.
- **Proposed fix (optional).** Add one clause: "if `$q\wheels` is missing but the rule exists, run the elevated
  `Remove-NetFirewallRule` of the firewall line, then re-enter at the `pip download` line" (or simply "delete the
  rule and `$q\wheels`, then re-enter from the download line").

### SECURITY-R5-2 (minor): the `--fixtures --record-baseline` line carries no `throw`, unlike its neighbours

- **Section:** Step 7A.2 (spec L1511); 5.2.7 `record_baseline` (spec L490-497).
- **Problem.** Every other runner line in 7A.2 ends with `if ($LASTEXITCODE) { throw "<tag>" }`, but the
  `--fixtures --record-baseline` line does not. On re-entry, a *tracked* baseline that differs makes `--record-baseline`
  exit 2 and write nothing (spec L492-494); with no `throw`, the owner's one-line-at-a-time reading relies on noticing
  the non-zero exit and the printed removal line rather than a red stop. A fixture mismatch (F1/F2/N1 off a golden) also
  exits 2 here with no throw.
- **Why it is only minor and fail-closed.** It never opens a path: a census or fixture mismatch cannot license a
  pilot, because an of-record run re-judges the census against the committed baseline (C-08) and re-runs the fixtures,
  and Claude reviews the diff at 7A.4 before any pilot. The cost is that a Step 7A failure at this line is quieter than
  the others; the owner must read the exit code. The common re-entry case (an untracked leftover baseline) is replaced
  and exits 0 by design (OPS-R4-2), so this only bites when a baseline is already committed and differs.
- **Proposed fix (optional).** Append `; if ($LASTEXITCODE) { throw "fixtures" }` to that line as well (the tag is
  already used by the next-to-last `--fixtures` wording), so a non-zero exit stops the sequence like every neighbour.

## Why I agree or not

I agree, and I confirm the AGREE I gave in rounds 2, 3 and 4 after reading all of Revision 5 for this targeted round.
Four reasons from the isolation lens.

1. **The boundary is byte-identical where it matters.** The 5.2.9 skeleton and the 5.6 constants block diff clean
   against my verbatim Revision-4 extracts; both pins recompute to the committed values; all 8.5 controls reproduce
   under two independent scanners. Nothing in Revision 5 touches rule A's single-call exemption, the deny-lists or the
   launch contract, so the "one order call, widen only by changing a pinned digest" guarantee is unchanged.
2. **The egress layer still fails closed, and Revision 5 tightened the proof.** Of-record mode needs a passing per-run
   probe and a matching Step 7A record (R-14); `--egress-record` now exits 2 on a failed proof and of-record re-reads
   the record's content, so a bad or stale proof refuses rather than cards. The firewall line replaces any wrong
   earlier rule. On Linux I re-confirmed the namespace binds even an `exec`-ed grandchild (errno 101).
3. **Every Step 7A failure path is actionable or falls through to the hand-off.** I walked the clean and the
   second-attempt case at each line. The new `git pull --ff-only` line (OPS-R4-1(b)) is the one that security depended
   on: the second attempt now runs Claude's fixed tree, so a pass writes `owner_confirmed` against the correct
   `code_sha256`. No re-entry reaches `pip download` through the firewall, writes a false egress proof, or keeps a
   wrong rule.
4. **What remains is minor and fail-closed.** SECURITY-R5-1 and SECURITY-R5-2 cost owner time, not isolation. The two
   Windows facts that stay UNVERIFIED by construction (does the firewall bind the redirector-started interpreter; does
   Windows pip re-enter as measured on Linux) are gated correctly by the Step 7A probe and record.

Moderator-rejected points across rounds 1 to 4: none ("Rejected: None" in all four rulings), so I re-raise nothing.
The growth to 1,849 lines (+4.3 percent, C-6) is within budget.

Probe files, all in `scratch:referee5_security/`:
- `skeleton_r5.py`, `constants_r5.py`, `ps_r5.txt`: verbatim extracts of Revision 5 (skeleton/constants identical to
  Revision 4).
- `pins.py` (both pins recompute), `controls_r5.py` (0 mismatches over the 8.5 controls), `scan_mine.py` (my scanner).
- `pipprobe/`: the offline pip re-entry measurements (venv repeat exit 0; offline `--require-hashes` repeat exit 0).
