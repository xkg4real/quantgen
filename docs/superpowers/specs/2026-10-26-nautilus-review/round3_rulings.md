# Round 3: Claude's own critique and the ruling on every referee issue

Date: 2026-10-26. Spec revision 3. Referees: the same five Claude personas; security was pressed on its round-2
AGREE and re-confirmed it with an independent scan of the sandbox skeleton (no hits). GPT and Gemini: still not run.

Tally: security AGREE (2 minor), QA AGREE (12 minor), governance AGREE (7 minor), quant ACCEPT WITH CHANGES
(1 major, 2 minor), ops ACCEPT WITH CHANGES (2 major, 7 minor). No blocker. No earlier issue open except the part of
QUANT-R2-5 that QUANT-R3-1 restates.

## 1. Claude's own critique

C-7 (minor). Revision 3 deviates from the round-2 rulings in nine stated places (the architect's "rulings not
applied exactly"). I have read each one. All nine are accepted as written: each is either forced by a measured fact
(F4 scope, `platform.uname`, the `sum()` compensation, G-08 tolerance when rounding changed a close) or a strictly
safer reading (code_sha256 included, the "refused during argument validation is not a run" clarification). They need
no further change except where a round-3 issue below refines them.

C-8 (minor). The debate should close after round 4. Remaining items are local and testable. If any round-4 referee
raises only minor issues, the moderator applies them and closes Step 1a without a round 5; a new major reopens it.

## 2. Rulings

All round-3 issues are ACCEPTED as proposed by their referee, with these specifics:

### Quant
- QUANT-R3-1 ACCEPT (first option): G-08 compares `len({d[:4] for d in wf_qg.dates})` (calendar years touched, the
  rule that wrote the stored card) with the card's `n_years`, and records `sc_qg.n_years` (whole years) beside it.
- QUANT-R3-2 ACCEPT: `rf_file null` means `rf = 0.0`, the study default (`docs/asset_expansion_study.py:175`); the
  overlay is zero and R-06 does not apply; add L2-12, the synthetic crypto rehearsal through the runner.
- QUANT-R3-3 ACCEPT: integers and dicts exact; floats within 1e-9; `bench_p` within 1/2000; `reference_card` and
  `reference_card_md5` in the pilot-2 table, refused on mismatch (R-11), checked by L1-29.

### Ops
- OPS-R3-1 ACCEPT: R-03's remedy prints only `python -m pip uninstall -y nautilus-trader`, `python -m pip check`, and
  the version line that must print `2.3.5 2.3.3 1.18.0`. Other closure packages are reported, never uninstalled.
- OPS-R3-2 ACCEPT: Step 7A gains a re-entry rule (skip the installer when `py313\python.exe` exists; create the
  firewall rule only when absent; `--record-baseline` with an existing equal baseline exits 0, with a different one
  exits 2 and names the diff).
- OPS-R3-3 to OPS-R3-9 ACCEPT as proposed (installer under `$q`, signature check that throws, HKCU and HKLM incl.
  WOW6432Node; hand-off report gains a fresh probe, the firewall rule dump and the suite's FAIL rows, named by
  `sysconfig.get_platform()`; `table_sha256` everywhere, both digests recorded; `as_posix()` paths in
  `code_sha256`; ancestry check before `git switch` and the post-Step-10 merge commands; `SetThreadExecutionState`
  in the parent instead of `powercfg`; the wording and citation fixes).

### QA
- QA-R3-1 to QA-R3-12 ACCEPT as proposed. In particular: `fixture_inputs(name)` in `launch.py` at Step 5; the parent
  re-derives C-01 to C-04 and C-15 and `--doctor` writes `valid: true`, exit 0; `table_sha256` keys the re-run guard;
  L2-5a perturbs one field per 6.1 rule; stub `--probe` mode and explicit `probe_cmd`; `run()` returns its exit code
  and never re-raises, the CLI maps it to `SystemExit`; seams `tree_refusal`, `check_p0a`, `write_record(replace=,
  sleep=)`; `invalid_reasons` begin with their section-7 id; the crypto moving averages use the same plain loop;
  the Store-Python stub question goes to 13.1 and 7A with the py313 fallback; L2-7 and N6 outcomes are UNVERIFIED
  until Step 7 and a WITHHELD names the predicate; census equality everywhere; Step 8's evidence is the hash echo.

### Security
- SECURITY-R3-1 ACCEPT: `if __name__ == "__main__":` guards `exit(main())`; the architect confirms the skeleton
  still passes rules A to F (a bare `Name` `__name__` is not an `Attribute`).
- SECURITY-R3-2 no change (fail-closed is the right direction); the spec adds one sentence telling maintainers to
  keep sandbox diagnostics free of denied tokens.

### Governance
- GOVERNANCE-R3-1 ACCEPT: `code_sha256` covers `core.quant.gate_package.HARNESS_SOURCES` (imported, one home), plus
  `docs/asset_expansion_study.py` and `config.py`.
- GOVERNANCE-R3-2 ACCEPT: L1-10 passes `ledger_dir=<temp>` and uses configurations outside both pilot grids
  (SPY `sma/127/21`, BTC-USD hysteresis 0.333); every nautilus test runs with a fresh temp `QUANTGEN_MACRO_DIR`,
  restored in `finally`.
- GOVERNANCE-R3-3 ACCEPT: in rehearsal, `prices_file` must resolve under `tempfile.gettempdir()`; the md5 refusal
  stays for byte copies; L1-9 adds a case naming a tracked cache file.
- GOVERNANCE-R3-4 ACCEPT: 7A.3 names `qa/acceptance_results.json`; Step 10 says the file is committed only from an
  owner's Windows full run.
- GOVERNANCE-R3-5 ACCEPT: Step 2 Claude-only rule "Claude never writes or edits `owner_confirmed` or
  `host_fingerprint`"; the approval form as proposed.
- GOVERNANCE-R3-6 ACCEPT: Step 1a is done when the moderator closes the Claude debate (C-8); the plan names the
  revision it implements; Appendix B gains the Claude round-3 rows; 10.4 gains one row per referee round.
- GOVERNANCE-R3-7 ACCEPT: cite `core/quant/gate_package.py:36-38`.

## 3. Rejected

None.
