# Owner rulings on the 5-2 provider parity runs

Spec 2026-10-26 section 10.5 (owner ruling P-D9): every owner ruling on a provider parity run is written here, next to
the earlier result, which stays. Step 10 carries the rulings into the execution record and the spec's Status block.
The spec names branch `claude/provider-parity-5-2` for this file; by the ruling of 2026-11-11 below it lives on `main`
and on the run branch `claude/provider-parity-runs-20261111`, where the owner pushes each `results/<run_id>/summary.json`.

A ruling is needed before:
- a later run of a series that already has a run of record counts (new fetches or the same files);
- a change to the providers or thresholds of 10.5.1 after any summary exists;
- Step 8 (SPY, DGS3MO) or Step 9 (BTC-USD), when that series' run of record is not PASS: the ruling either holds the
  pilot or lets it go ahead with the disagreement noted in the execution record and in 10.4;
- a run with tool bytes other than those 10.5 fixes counts.

Each entry: the date (KST), the series, the `run_id` it concerns, the owner's words verbatim, and what follows.

## 2026-11-11 (KST), all series, before any run: where the tool is fixed (P1)

Claude's question, as put to the owner: where to write down the fixed version of the provider parity tool. Option 1
(recommended): on main's side, in the tool's rulings file, after PR #102 merges; the owner has nothing more to do.
Option 2: in the spec on the research branch, which adds a commit there and makes the owner pull and repeat two checks
before the pilots.

Owner's words, verbatim:

> 1번으로 승인하겠노

What follows:
- Tool commit fixed: `5202482e3c24de871b8483608b8a03beb07abe1e`
- Tool sha256 fixed (`tools/provider_parity/parity_check.py`): `f2fe72cdee6344076fd6dfec8943259f44bc52445c66cdaf482a19e269770184`
- 2026-11-11 (KST), before PR #102 merged: the two values above replace those first recorded here (commit `49a3a67`,
  sha256 `d651795e...`), because a code review of PR #102 found faults in the tool that could have cost the owner a
  run of record (F1: the H.15 fetch could read another maturity's column and end the DGS3MO run FAIL; F2: a file
  fetched for other dates than the table's was compared and could end a series WITHHELD) and the tool was changed to
  fix them; no run existed.
- Run branch the owner clones and pushes summaries to: `claude/provider-parity-runs-20261111` (cut from `main`; it contains the fixed commit).
- The research branch gets no commit for this. The spec's branch name (`claude/provider-parity-5-2`) differs from the
  above; Step 10 records the difference in the execution record.
- No run of record exists yet.
