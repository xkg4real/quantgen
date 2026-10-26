# Round 4: Claude's own critique and the ruling on every referee issue

Date: 2026-10-26. Spec revision 4. GPT and Gemini: still not run.

Tally: security AGREE (3 minor), quant AGREE (3 minor), QA AGREE (6 minor), governance AGREE (5 minor), ops ACCEPT
WITH CHANGES (1 major, 4 minor). Open from earlier: OPS-R3-2 part (a), restated as OPS-R4-1.

## 1. Claude's own critique and the closing rule

Under C-8 a major reopens the debate. OPS-R4-1 is a major in the Windows hand-off procedure (Step 7A re-entry), not
in the bridge's design. Ruling: apply every round-4 issue in revision 5, then a **targeted round 5** by the two
personas whose lens covers Step 7A and the egress layer (ops and security). The other three referees agreed in
round 4 and their remaining points are wording; their round-4 items are applied without another round. If round 5
raises no major, the moderator closes Step 1a.

C-9 (minor). Governance R4-5 notes that the quant referee's round-4 probe re-scored the stored `S_E1_trend_krx`
grid on four real KRX ETF caches and `fred_DGS3MO.csv`. That is outside both pilot windows and outside both pilot
families' configurations, but it is still a look at real data by this programme. It goes into the 10.4 data-access
history verbatim, as proposed.

## 2. Rulings (all ACCEPT as proposed by the referee, with these specifics)

### Ops
- OPS-R4-1 ACCEPT: after the switch line, `git pull --ff-only` with a throw that says to ask Claude. Re-entry skips
  to the venv line when `$q\wheels` exists (the offline `--require-hashes` install re-checks every hash), and to the
  pip download line only while no `QUANTGEN-nautilus-block-out` rule exists. This also resolves SECURITY-R4-2.
- OPS-R4-2 ACCEPT: the existing-baseline rule applies only to a git-tracked baseline; an untracked leftover is
  replaced and its diff printed; L1-35 adds the case. The firewall line removes any rule of that name before it
  creates the rule.
- OPS-R4-3 ACCEPT: the hand-off report uses `powershell -NoProfile -NonInteractive -Command` with `Format-List`
  cmdlet output, not `netsh`.
- OPS-R4-4 ACCEPT: the temp root is computed in two forms (`realpath(gettempdir())` and `realpath(dirname(mkdtemp()))`)
  and a path is inside if it lies under either; the repository stays excluded.
- OPS-R4-5 ACCEPT: an explicit `Invoke-WebRequest ... -OutFile $inst` line with the version taken from the runbook's
  pinned value; the second ancestry check for local `main`; the other two points as proposed.

### Security
- SECURITY-R4-1 ACCEPT: risk 2 and 5.2.2 say rule F rejects the direct spellings, that an attribute path through a
  loaded module can still reach `sys.modules`, and that the egress layer bounds any use.
- SECURITY-R4-2 ACCEPT: resolved by OPS-R4-1's re-entry order.
- SECURITY-R4-3 ACCEPT: `--egress-record` writes the record, then exits 2 (R-14) unless `probe.blocked` and
  `control_connect.ok` are both true; R-14's Windows Remedy covers a wrong earlier rule (program path, disabled,
  profile not Any).

### Quant
- QUANT-R4-1 ACCEPT: L2-12 builds the reference as the stored card was built, with `n_years` as calendar years
  touched; leaving the whole-year value must give exactly the `n_years` drift.
- QUANT-R4-2 ACCEPT: `reference_drift(sc_qg, wf_qg, grid, ref)`; G-08 applies whenever `reference_card` is not
  null, and of-record mode requires it for C3-BTCUSD.
- QUANT-R4-3 ACCEPT: the three wording fixes.

### QA
- QA-R4-1 ACCEPT: raising stand-ins for `yfinance`, `pandas_datareader` and `pandas_datareader.data` in
  `sys.modules` around the study calls, restored in `finally`; the trimmed cache names are asserted.
- QA-R4-2 ACCEPT: the rehearsal place rule for `prices_file` is judged in `check_table` (step 1).
- QA-R4-3 ACCEPT: the echoes of `bars_fed`, `first_ts` and `last_ts` are checked against the parent's own values;
  C-02 is re-derived against them; C-09 checks the equity row count.
- QA-R4-4 ACCEPT: pure `record_baseline(golden_dir, tag, census)`; L1-3 checks via the `child_started` hook; the
  helper interpreter rule as proposed.
- QA-R4-5 ACCEPT: the four wording fixes.
- QA-R4-6 ACCEPT: `fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)` written explicitly; `msvcrt.locking` on Windows
  as in `gate_ledger`.

### Governance
- GOVERNANCE-R4-1 ACCEPT: `--fingerprint` validates the table with owner fields optional, opens no data file, and
  always prints `table_sha256` and `code_sha256`; `host_fingerprint` or null with the reason.
- GOVERNANCE-R4-2 ACCEPT: 7A.1 fetches and checks ancestry, merging `origin/main` first if it moved; 7A.4 checks the
  sentence commit is an ancestor of the 7A.3 commit and lists the files changed between them.
- GOVERNANCE-R4-3 ACCEPT: the rule reads "Claude never writes or edits `owner_confirmed` or `host_fingerprint` in a
  committed table (`docs/nautilus_bridge/registration/`); tests write them only into tables under the system temp
  dir."
- GOVERNANCE-R4-4 ACCEPT: of-record C3-BTCUSD refuses with R-11 unless `runs/` holds an of-record E1-SPY record with
  `parity.hard_pass` true for all 12 columns at both cost levels and the same `code_sha256`; an L1 case on temp
  roots.
- GOVERNANCE-R4-5 ACCEPT: Status, Step 1a, Appendix B round-4 column and rulings, and the 10.4 row (C-9).

## 3. Rejected

None.
