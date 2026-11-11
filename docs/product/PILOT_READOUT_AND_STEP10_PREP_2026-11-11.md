# Pilot readout and Step 10 closing: working document

Written 2026-11-11 (KST) by a Claude Code session. Reader: the session that reads the owner's results and closes
Step 10 of the NautilusTrader bridge (roadmap items 5-2, 6-1, 6-2, 7-1, 7-2). The reader needs no access to the
conversation this came from. Sentences meant for the owner are in Korean and can be pasted once the `<...>` parts
are filled.

Who may do what. Any session, Claude or GPT, may use Part 1 to read the owner's results and report them. Committing
on the research branch is narrower: the owner's ruling P2 names "this session" (이 세션), the Claude session that
put the question to him (`log-main:705`, `log-main:757`). It names no other session. A GPT session, or another
Claude session that takes over, asks the owner before it commits anything on the research branch (section 2.10,
item 0).

This file changes no code. It sits under `docs/product/`, which the compliance check monitors
(`check:105-108`), so committing it on a main-side branch needs the same baseline refresh as section 3.1.

Roadmap IDs are written here as 5-2, 6-1, 6-2, 7-1 and 7-2. In `REMAINING_WORK_2026-10-27.md` and in the handoff
ledger they are ⑤-2, ⑥-1, ⑥-2, ⑦-1 and ⑦-2 (`rw:132-135`, `rw:117`).

## 0. Read this first

### 0.1 Where things stand (checked 2026-11-11, after main moved to `83046c1`)

| Fact | Value | How it was checked |
|---|---|---|
| Research branch | `origin/claude/amazing-gauss-tdiguu`, head `8a8c247` | `git rev-parse` |
| Main | `origin/main` `83046c1` (PR #103, merged 2026-11-11 13:53 KST; before it `9fc3817`, PR #102, 12:21 KST, and `96cca1f`, PR #101, 06:00 KST); merge base with the research branch `bb35b3b` | `git rev-parse`, `git log --first-parent`, `git merge-base` |
| Pilot outputs | none: `docs/nautilus_bridge/runs/` does not exist on the research branch | `git ls-tree --name-only <ref> docs/nautilus_bridge/runs/` printed nothing |
| Code fingerprint (`code_sha256`, the hash over the bridge's code files) | `f995600b36c75523fe6079ab5209e60d94c2b5d0ac44437673fe4bc71c055620` | recomputed from git objects at `8a8c247` by the rule of `runner:183-200`; 27 files |
| Table fingerprints (`table_sha256`) | pilot 1 `d76d2d7301ffe92ca5198404ba1cbe07fd11890489c227e20cced8c4c4e07347`; pilot 2 `e2ec073c309cbfc75ff476c03dda96337c45b46ce3f18129df96fb4d74462aba` | recomputed by the rule of `runner:176-180`; both `owner_confirmed` quote their first 16 hex (`t1:70`, `t2:50`) |
| Files changed on the research branch since the 7A.3 evidence commit `563db54` | the spec only | `git diff --name-only 563db54 <ref>` |
| Provider parity tool (5-2) | commit `5202482e3c24de871b8483608b8a03beb07abe1e`, sha256 `f2fe72cdee6344076fd6dfec8943259f44bc52445c66cdaf482a19e269770184` | `git show origin/main:tools/provider_parity/parity_check.py \| sha256sum`; `git diff --quiet 5202482 origin/main -- tools/provider_parity/parity_check.py` exit 0 |
| Where the tool is | on `origin/main` since PR #102 (merge commit `9fc3817`), unchanged at `83046c1`. PR #103 added tests only (`tests/provider_parity_acceptance.py`); the tool file, its README, the owner guide and `results/RULINGS.md` are the same blobs as at `b92275f` | `git diff --quiet b92275f origin/main -- <each file>` exit 0 |
| Run branch for summaries | `origin/claude/provider-parity-runs-20261111` exists, head `9fc3817`. `results/` holds `RULINGS.md` only: no summary has been pushed yet | `git branch -r`, `git ls-tree --name-only <branch> results/` |
| Handoff ledger | no row for 6-1, 6-2, 7-1 or 7-2. 5-1 is done. For 5-2 the rows are ⑤-2/a, ⑤-2/a2, ⑤-2/b (2026-11-11T12:22:49+09:00, the tool) and ⑤-2/b/2 (13:53:48+09:00, more tests). No row yet for the owner's run or for the readout: the handoff document lists ⑤-2/d, ⑤-2/e, ⑥-1/prep, ⑥-1, ⑥-2, ⑦-1 and ⑦-2 in `next_ids` | `git show origin/handoff:LEDGER.md`, lines 154-159, 193, 195; `git show origin/handoff:CURRENT.md`, line 8, at handoff commit `74744d4` |
| Owner rulings P2, P3, P4 | recorded on `origin/main` at `83046c1`, section "2026-11-11 ... 전부승인" | `git grep -n "전부승인" origin/main -- docs/nautilus_bridge/OWNER_RULINGS_LOG.md` prints lines 697 and 748 |
| Merge rehearsal (decision P3) | done locally on `9fc3817`, never pushed; recorded in `docs/product/STEP10_MERGE_REHEARSAL_2026-11-11.md` | that file |

So the run folders will be named `NB-<UTC>-d76d2d73` (pilot 1) and `NB-<UTC>-e2ec073c` (pilot 2): the name ends with
the first 8 hex of `table_sha256` (`runner:211-213`).

### 0.2 Source keys

Every field name, file name, code and threshold below carries a key and a line. Lines were read on 2026-11-11.

| Key | File | Ref |
|---|---|---|
| `spec` | `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md` | research branch, `8a8c247` |
| `runner` | `tools/nautilus/runner.py` | research branch, `8a8c247` |
| `parity` | `tools/nautilus/parity.py` | research branch, `8a8c247` |
| `runbook` | `docs/nautilus_bridge/RUNBOOK_windows.md` | research branch, `8a8c247` |
| `record` | `docs/superpowers/plans/2026-10-28-nautilus-execution-record.md` | research branch, `8a8c247` |
| `t1`, `t2` | `docs/nautilus_bridge/registration/pilot1_E1_spy.json`, `pilot2_C3_btcusd.json` | research branch, `8a8c247` |
| `run_all`, `guard` | `tests/run_all.py`, `tests/frozen_guard.py` | research branch, `8a8c247` |
| `validate` | `core/quant/validate.py` | research branch, `8a8c247` |
| `rb-readme` | `README.md` | research branch, `8a8c247` |
| `rb-log` | `docs/nautilus_bridge/OWNER_RULINGS_LOG.md` | research branch, `8a8c247` |
| `pc` | `tools/provider_parity/parity_check.py` | tool commit `5202482` |
| `pp-readme`, `guide`, `rulings-md` | `tools/provider_parity/README.md`, `docs/product/PROVIDER_PARITY_OWNER_RUN_2026-11-11.md`, `results/RULINGS.md` | `b92275f` (PR #102); the same blobs on `origin/main` `83046c1` |
| `log-pp` | `docs/nautilus_bridge/OWNER_RULINGS_LOG.md` | `b92275f` (PR #102); its lines 675-695 are lines 675-695 of `log-main` |
| `log-main`, `rw` | `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`, `docs/nautilus_bridge/REMAINING_WORK_2026-10-27.md` | `origin/main` `83046c1` |
| `snapshot`, `check` | `tools/status/snapshot.py`, `tools/compliance/check.py` | `origin/main` `83046c1` (both unchanged since `96cca1f`) |
| `sheet` | `docs/product/PILOT_OWNER_RUN_2026-11-11.md`, the owner's run sheet | committed with this file |
| `rehearsal` | `docs/product/STEP10_MERGE_REHEARSAL_2026-11-11.md` | committed with this file |
| `draft` | `docs/nautilus_bridge/PROVIDER_PARITY_DESIGN_DRAFT_2026-11-04.md` | `origin/claude/provider-parity-design-20261104` `6b3149d` |

Read a research-branch file with `git show origin/claude/amazing-gauss-tdiguu:<path>`. "Not verified" marks a
statement that could not be traced to a line or a command result (Korean text: 미검증).

### 0.3 Rules that bind the reader

1. Never open, list, hash or search `docs/asset_expansion/cache/` in any checkout. No repository-wide `find`,
   `ls -R`, `grep -r`, `rg` or `git ls-files` without a path. Search with
   `git grep -n <pattern> -- <paths> ':!docs/asset_expansion/cache'`. List one named folder with
   `git ls-tree --name-only <ref> <dir>/`. In a checkout that holds the cache folder, `git status` without a path
   also stats that folder's files and scans its directory: give it paths (`git status --porcelain -- <paths>`), or
   work in a clone that never checks the folder out. The commands in this document read commits with `git show`,
   `git ls-tree`, `git log` and commit-to-commit `git diff`, which touch no working file.
2. Never open `.env` or anything under `~/.nextgen`. Name variables, never values.
3. Never run `tests/run_all.py` in the cloud (`spec:240-241`). Never write `qa/acceptance_results.json`: it is
   committed only from the owner's Windows full run (`spec:1633`), and every Claude commit leaves it byte-identical and
   says so (`spec:1528`).
4. `owner_confirmed` and `host_fingerprint` are written only by the owner (`spec:1637-1638`, `record:37`).
5. Who writes what on the research branch:

| Path | Who | Source |
|---|---|---|
| `docs/nautilus_bridge/runs/NB-*/` (pilot run folders) | the owner | `spec:1631` |
| `qa/acceptance_results.json` | the owner, from the Windows full run | `spec:1633` |
| the Step 10 execution record, the spec, `README.md`, and under `docs/nautilus_bridge/runs/` only the `PP-*` copies of section 2.6 | the Claude session P2 names; any other session only after asking the owner | owner decision P2, below |
| everything else (`tools/nautilus/**`, `tests/nautilus_*.py`, the tables, `paper_live/`, `grokteam/`, cards, ledgers) | nobody | P2; `spec:1633` |

6. No Claude commit lands on the research branch before the owner has pushed both pilot run folders and the Step 10
   full run. A commit in between moves HEAD, and the owner would have to pull and repeat the two 7A.5 checks before
   the next pilot (`spec:1610-1614`).

Owner decisions that bind this work:

| Decision | Text | Where recorded |
|---|---|---|
| P1 (2026-11-11) | "1번으로 승인하겠노": the tool's commit and sha256 are fixed on main's side | `log-main:675-695`, `rulings-md:17-39` |
| P2 (2026-11-11) | Recommendation as put to the owner: "이 세션이 맡음. 범위는 마감 기록·스펙·README·실행 기록 폴더로 한정합니다. 한 세션이 맡아야 ⑤-2처럼 일이 빠지지 않습니다." Owner's answer to the whole batch: "전부승인". As recorded: "연구 브랜치 `claude/amazing-gauss-tdiguu`에 이 세션이 커밋할 수 있습니다. 범위는 Step 10 마감 기록, 스펙, README, `docs/nautilus_bridge/runs/` 실행 기록 폴더로 한정합니다." `tools/nautilus/**`, `tests/nautilus_*.py`, the runner, the tables, `owner_confirmed` and `host_fingerprint` stay untouched. "This session" is the Claude session that asked; no other session is named | `log-main:705` (the recommendation), `log-main:748` (the answer), `log-main:757` (as recorded). The section before it still ends "P2~P4 ... 답을 기다립니다" (`log-main:695`); the section at 697 is the answer |
| P3 (2026-11-11) | "마감 확인 뒤 Claude가 main을 연구 브랜치에 합쳐 충돌을 풀고 전체 테스트를 돌립니다. 소유자는 충돌 없는 병합만 하시면 됩니다." As recorded: after the Step 10 checks Claude merges main into the research branch, resolves the conflicts and runs the full test in a cache-free copy; H-D5 stays until then; the owner makes the merge commit on main himself | `log-main:706`, `log-main:758` |
| P4 (2026-11-11) | "이 세 가지는 병합 뒤로 미룸" (the order module, the R3 Lab screen wiring, the LA-07 harness change) | `log-main:707`, `log-main:759` |
| H-D5 (2026-11-04) | "7A.5부터 Step 10 병합까지는 main을 연구 브랜치에 합치지 않음" | `log-main:508` |
| Merge | the owner's own merge commit, `git merge --no-ff`, never a squash or a rebase, the branch ref kept | `spec:1615-1619`, `runbook:211-221` |
| Gate before the pilots | section 1.1.5 below | `spec:1743-1747` |
| P-D8 (2026-11-04) | "Pilot 1 전에 세 시계열 모두": all three series are compared before pilot 1 | `log-main:521`, `spec:1720-1721` |

## Part 1. Readout checklists

Two small read-only scripts are in appendices A and B. Both were run only on stand-ins (see "Not verified").

The owner's steps for the pilots, the full run and the merge are in the sibling document
`docs/product/PILOT_OWNER_RUN_2026-11-11.md` (`sheet`, committed with this file). Its section I lists what the
owner pastes: for each pilot the two A6 lines, the five A7 lines, the last four console lines from `parity:` to
`STATUS`, every `reason:` line and the exit code; for the full run its last line and the three E4 lines; for the
merge the F11 line with three commit ids. Its section K lists the ten points it leaves to the owner; they overlap
with section 5 here. Its steps B2 and D2 are the two pilot commands, E2 the full run, F10 the merge and F12 the
push to main.

### 1.1 Provider parity (5-2): the pasted lines and the three summaries

What the owner sends (`guide:365-374`): the last two lines of each of the nine fetches (18 lines), the last line of
each of the three compares (3 `PARITY` lines), the `git status --short` lines and the last two lines of `git push`.
The three `summary.json` files arrive by the push to the run branch, as `results/<run_id>/summary.json`.

To read the summaries (after the owner's push):

```bash
git fetch origin claude/provider-parity-runs-20261111
git ls-tree --name-only origin/claude/provider-parity-runs-20261111 results/
git show origin/claude/provider-parity-runs-20261111:results/<run_id>/summary.json | python3 -B -I read_summary.py
```

Claude reads only `summary.json`. `detail.json`, the fetch folders and the CSVs never leave the owner's machine
(`spec:1736-1737`, `guide:376-380`). If the owner pastes any of them, do not read on: say so and ask him to delete
the paste.

#### 1.1.1 The 18 fetch lines

1. Read: the last line of each fetch. Compare with: `FETCH <series> <provider> OK exit=0 csv=<path>` (`pc:888`).
   Then: `OK` goes on. `FETCH ... UNAVAILABLE <reason> exit=4 csv=-` (`pc:1752-1755`) means nothing was written; the
   reason is `no_key`, `plan_or_access` or `fetch_failed` (`pp-readme:94-96`). A fourth reason, `short_history`, is
   never printed by a fetch; it is declared in compare when a provider cannot serve the window at all (`pc:98`,
   `pp-readme:100-102`). `REFUSED exit=2` or `ERROR exit=4` (`pc:1748-1751`, `pc:1756-1759`) is not a fetch; read
   the line above it.
2. Read: the line above, `rows <n>, first <date>, last <date>, weekend dates <n>` for SPY and DGS3MO, or
   `..., missing days <n>` for BTC-USD (`pc:886-887`, `pc:832-840`). Compare with: `weekend dates 0` on all six SPY
   and DGS3MO fetches (`guide:243`). Then: any other count means the provider labels its days differently. That file
   is not compared and `short_history` is not declared (`pp-readme:104-107`).
3. Read: `first`. Compare with: SPY on or before 2004-12-01; DGS3MO on or before 2004-11-05; `coinbase` and
   `bitstamp` on or before 2016-01-01; `binance` is not judged (`guide:244`). Then: a later first date counts against
   coverage. The 2016-01-01 bound follows from `edge_uncovered_max` 471 (`pc:146`). The 2004-11-05 bound is the
   guide's; its derivation is not verified here.
4. Read: `last`. Compare with: 2026-09-25 or later on all nine (`guide:245`).
5. Read: the `kis` line. Compare with: no text `; kis paging stopped at <date>, after the first requested date
   <date>: <reason>` (`pc:621-622`, `guide:246`). Then: if it is there, the file starts late because of the fetch, not
   because of the provider. Settle it before compare.
6. Read: `missing days` on the three BTC-USD fetches. Compare with: nothing; any count is allowed (`guide:248`).
   Then: compare lists those days as a calendar WARN.
7. Then, for the whole set: compare is what makes the run of record, and a fetch may be repeated into a new folder
   (`pp-readme:118-119`). If any of 1 to 5 fails, the owner stops before compare (`guide:240`) and Claude writes the
   compare line for that case: a provider that could not be fetched is named as `--unavailable <provider> <reason>`
   (`pc:1497-1515`). Never suggest a new fetch or a new compare in order to turn a FAIL or WITHHELD into PASS
   (`guide:363`).

#### 1.1.2 The 3 PARITY lines

8. Read: the last line of each compare. Compare with: `PARITY <series> <PASS|FAIL|WITHHELD> exit=<0|1|3>
   summary=<path>` (`pc:1556`, `pc:115`). Then: that run is a run. `PARITY <series> REFUSED exit=2 summary=-`
   (`pc:1764`) or `ERROR exit=4 summary=-` (`pc:1768`) wrote nothing and is not a run (`spec:1739`); the cause is
   fixed and the same line is run again.
9. Read: the outcome on the line. Compare with: `outcome` in the pushed summary of the same `run_id`. Then: if they
   differ, stop and report; do not choose one.
10. Read: the `git status --short` lines. Compare with: every line is `A  results/PP-.../summary.json`
    (`guide:320`). Then: any other line means something else was staged; stop and ask.

#### 1.1.3 Each `summary.json`

Top-level keys, exactly these 14 (`pc:1408-1409`): `schema`, `tool`, `run_id`, `created_utc`, `series`, `window`,
`pinned`, `providers`, `thresholds`, `integrity`, `pairs`, `outcome`, `n_a_outside_evidence_spans`,
`withheld_reasons`. The names were confirmed by building three synthetic summaries with the tool's own
`compare` and `build_summary`.

11. Read: `schema`. Compare with: `provider-parity-summary/1` (`pc:82`).
12. Read: `tool.sha256`. Compare with: `f2fe72cdee6344076fd6dfec8943259f44bc52445c66cdaf482a19e269770184`
    (`pp-readme:36-37`). Then: if different, the run counts only by an owner ruling recorded with the result
    (`spec:1718-1719`).
13. Read: `run_id`, `created_utc`, `series`. Compare with: `run_id` is `PP-<created_utc>-<series>`, `created_utc` is
    `YYYYMMDDTHHMMSSZ`, `series` is `spy`, `rf` or `btc` (`pc:1394-1396`, `pc:86`). `rf` is DGS3MO. Then: if a series
    has more than one folder under `results/`, the earliest `created_utc` is the run of record; a later one counts
    only by an owner ruling in `results/RULINGS.md` (`spec:1738-1742`).
14. Read: `pinned.file`, `pinned.md5`, `pinned.md5_ok`. Compare with: the table (`pc:124-126`, `pc:1397`):

    | series | `pinned.file` | `pinned.md5` | table line |
    |---|---|---|---|
    | spy | `yf_SPY.csv` | `d2164597d576e1b2fcadde063065811d` | `t1:10-11` |
    | rf | `fred_DGS3MO.csv` | `661722143f24930a29b58c535d227c1b` | `t1:14-15` |
    | btc | `yf_BTC-USD.csv` | `bc76f530ff24ab445367fe826150bc10` | `t2:10-11` |

    Then: `md5_ok` is always true in a written summary, because the tool refuses a file whose md5 differs before it
    compares (`pc:959-961`).
15. Read: `window.start`, `window.end`. Compare with: 2004-12-01 and 2026-09-25 for spy and rf (`t1:12-13`);
    2014-09-17 and 2026-09-25 for btc (`t2:12-13`). Also: `window.end` and every `last_date` in the coverage checks
    are before 2027-01-01. The spec lets no observation dated on or after 2027-01-01 be requested, stored or
    compared (`spec:1723-1724`). Then: a later date is reported to the owner at once.
16. Read: `providers`, `thresholds`. Compare with: nothing by hand. The tool refuses to write a summary whose
    provider map or thresholds differ from its own (`pc:1431-1434`). They are printed so the reader sees the bar next
    to each outcome.
17. Read: `outcome`. Compare with: `PASS`, `FAIL` or `WITHHELD` (`pc:1364-1370`). A series is never `WARN`.
18. Read: `integrity`, the checks of the pinned file alone. Each entry has `id`, `kind`, `outcome` and its counts
    (`pc:206-207`). spy: `integrity_a` with `n_rows`, `n_dropped_blank`, `n_dropped_nonpositive`,
    `no_split_shaped_jump` (`pc:1118-1127`). btc: `integrity_a` with `n_rows`, `n_dropped_blank`,
    `n_dropped_nonpositive`, `n_missing_days_a`, `missing_a`, `truncated`, `no_implausible_jump` (`pc:1190-1203`).
    rf: `units` with `percent_units_ok` (`pc:1272-1281`) and `seed` with `seed_before_start` (`pc:1284-1288`). Then: a
    `FAIL` here makes the series FAIL. btc `integrity_a` can be `WARN` (1 to 5 missing days), which does not fail the
    series.
19. Read: `pairs`. Each has `provider`, `role`, `convention`, `file_sha256`, `has_fetch_record`, `outcome`, `checks`
    (`pc:1358-1360`). Compare with: every required provider is either a pair or named in `withheld_reasons` as
    `<provider> not compared: <reason>` (`pc:1363`, `pc:1510-1513`). Required: spy `fmp`, `kis`, `yahoo_now`; rf
    `treasury`, `fred_now`; btc `coinbase`, `binance`. Optional: `h15`, `bitstamp` (`pc:90-97`).
20. Read: `has_fetch_record` of each pair. Compare with: `true`. Then: `false` means the file was compared from
    outside its fetch folder; ask the owner where it came from (`pp-readme:160-162`).
21. Read: each pair's `outcome` and each check's `outcome`. A pair is `FAIL` when a hard check fails, `WITHHELD` when
    coverage is not PASS or a hard check is WITHHELD, else `WARN` when any check warns, else `PASS`
    (`pc:1351-1357`). A `vintage` or `diagnostic` pair reports FAIL as WARN and its checks have kind `warn`
    (`pc:1063-1069`). Then: list every WARN and every WITHHELD pair in the report, with the check id.
22. Read: `n_a_outside_evidence_spans`. It counts the pinned file's dates that no fully evaluated independent or
    cross pair spans (`pc:1371-1375`). Then: report the number. No threshold applies to it.
23. Read: `withheld_reasons`. Compare with: it is filled for unavailable providers even when the series is PASS
    (`pc:1363`); the text `no independent or cross pair was evaluated in full` appears only with WITHHELD
    (`pc:1366-1368`, `pc:1382`).
24. Then: apply the verdict rule of 1.1.4 by hand to `integrity` and `pairs` and check that it gives `outcome`.

Checks inside a pair, with the fields a summary carries:

| Series | Check id | Fields | Outcome rule | Lines |
|---|---|---|---|---|
| all | `coverage` | `n_a`, `n_b`, `n_common`, `n_a_outside_b_span`, `coverage_ok`, `first_date`, `last_date` | PASS or WITHHELD | `pc:1080-1096` |
| spy, btc | `calendar` | `n_only_a`, `n_only_b`, `only_a`, `only_b`, `truncated`; spy also `n_weekend_a` | spy: FAIL on any difference; btc: WARN | `pc:1099-1115` |
| spy, `total` pairs (`fmp`, `yahoo_now`) | `returns_same_convention` | `n_days`, `n_over_tol`, `n_allowed`, `max_abs_bucket`, `drift_range_bucket`, `max_ok`, `drift_ok` | PASS or FAIL | `pc:1130-1147` |
| spy, `split` pair (`kis`) | `adjustment_convention` | `n_full_years`, `n_years_expected_ex_days`, `n_years_off_by_one`, `n_years_off_more`, `n_negative_gap_days`, `n_allowed`, `n_too_large_gap_days`, `yield_band_ok` | WITHHELD with no full year; FAIL; WARN when a year is off by one; PASS | `pc:1150-1187` |
| btc | `day_boundary` | `lag`, `lag0_strictly_fewest` | PASS only when `lag` is 0 and strictly fewest | `pc:1212-1235` |
| btc | `levels_and_returns` | `late` and `early`, each `n_days`, `p50_bucket`, `p99_bucket`, `max_bucket`, `within_band`; `n_big_return_diff_days`, `n_allowed` | FAIL on the late band or on too many big days; WARN on the early band | `pc:1238-1269` |
| rf | `values` | `n_common_values`, `n_off_by_tol`, `max_abs_bucket` | FAIL when any day is off | `pc:1305-1308` |
| rf | `blanks` (kind `warn`) | `n_blank_a_value_b`, `blank_a_value_b`, `n_value_a_absent_b`, `value_a_absent_b`, `truncated` | WARN or PASS | `pc:1309-1312` |

Shapes a real summary can show that the table does not list:

- The other checks run only when `coverage` is PASS (`pc:1343`). A pair whose coverage is WITHHELD holds the
  `coverage` check alone.
- WITHHELD is also possible for `calendar` (no overlap, `pc:1102-1103`), `returns_same_convention` (fewer than two
  common days, `pc:1133-1134`), `day_boundary` (`pc:1219-1220`, `pc:1229-1230`) and `levels_and_returns`
  (`pc:1241-1242`).
- An empty `late` or `early` segment is `{"n_days": 0}` and nothing else (`pc:1248-1250`).

A summary holds counts, calendar dates, booleans and decade buckets such as `<=1e-04`, never a price, a return or an
exact difference (`spec:1772-1777`, `pc:1422-1491`). Do not ask the owner for the exact values behind a bucket: they
are in `detail.json`, which stays on his machine.

#### 1.1.4 Verdict rule and tolerances

Series verdict (`pc:1362-1370`, `spec:1765-1766`): FAIL when a check of the pinned file alone fails or any
`independent` or `cross` pair is FAIL. Otherwise WITHHELD when no `independent` or `cross` pair ended PASS or WARN.
Otherwise PASS. Exit codes 0 PASS, 1 FAIL, 3 WITHHELD, 2 refused, 4 error (`pc:115-116`).

Tolerances (`pc:129-167`, the same numbers as `spec:1759-1761`):

| Series | Tolerance | Value |
|---|---|---|
| SPY | `coverage_min`; `edge_uncovered_max` | 0.99; 5 |
| SPY | `ret_diff_tol`; `ret_diff_max`; `ret_diff_share_max`; `ret_diff_floor_days` | 2e-4; 2e-3; 0.005; 5 |
| SPY | `drift_range_max`; `jump_abs_max` | 5e-3; 0.25 |
| SPY | `ex_gap_min`; `ex_gap_max`; `ex_days_per_year`; `yield_band` | 5e-4; 2e-2; 4 (3 or 5 is WARN); [0.005, 0.04] |
| BTC-USD | `coverage_min`; `edge_uncovered_max`; `late_from` | 0.95; 471; 2017-01-01 |
| BTC-USD | `level_p50_max`; `level_p99_max`; `level_max` | 0.003; 0.015; 0.05 |
| BTC-USD | `early_level_p99_max`; `early_level_max` (WARN only) | 0.03; 0.10 |
| BTC-USD | `missing_days_warn_max`; `jump_log_abs_max`; `ret_diff_big`; `ret_diff_share_max` | 5; 0.7; 0.02; 0.005 |
| DGS3MO | `coverage_min`; `edge_uncovered_max`; `value_tol_pct` | 0.99; 5; 0.005 |
| DGS3MO | `range_pct`; `unit_max_at_least_pct`; `seed_lookback_days` | [-1.0, 20.0]; 1.0; 31 |

The tolerances were set without real data, so the rate of false FAIL on the real series is unknown
(`pp-readme:271`).

#### 1.1.5 Gate rule

`spec:1743-1747`: Step 8 (pilot 1) starts only when the SPY and DGS3MO runs of record say PASS, or the owner has
written a ruling for each that does not. Step 9 (pilot 2) likewise for BTC-USD, in addition to the pilot-1 condition
that the runner enforces (R-11). The gate is a procedure: the runner does not check it. Per series the first run that
ends PASS, FAIL or WITHHELD is the run of record (`spec:1738-1739`).

Two points the owner's sheet also states, so the message to the owner must match them:

- All three series are compared before pilot 1 (P-D8, `spec:1720-1721`, `log-main:521`). The first sitting starts
  only when all three summaries are pushed, although only SPY and DGS3MO gate pilot 1.
- A written ruling does not open the gate by itself. A ruling on a series that is not PASS "either holds the pilot
  or lets it go ahead" (`spec:1745-1747`). Say "the gate is passed" only for PASS or for a ruling that says go
  ahead. The message that releases pilot 2 names both facts in one sentence: pilot 1 has `parity.hard_pass` true,
  and the BTC-USD gate is passed (`sheet`, sitting 2 and section C item 6).

#### 1.1.6 A series that is not PASS: what to put to the owner

The owner's ruling P-D6 names two courses: hold the pilot, or go ahead with a note (`log-main:519`,
`spec:1745-1747`). The design draft lists a third and its cost (`draft:259-265`). Put all three, with the costs:

| Option | What it means | Cost | Source |
|---|---|---|---|
| 1. Note and go ahead | The table and the pinned file stay. The disagreement is written into the execution record and spec 10.4 | None in time. The card's data wording does not change | `draft:263`, `spec:1745-1747` |
| 2. Hold the pilot | Step 8 or 9 waits until the cause is found | Schedule | `draft:264` |
| 3. Replace the data | A new `prices_file` or `rf_file` with a new md5 and a new table | The runner's constants change, so `code_sha256` changes, both `owner_confirmed` become invalid, and 7A.2 to 7A.5 are done again | `draft:265-276` |

A separate ruling, not one of the three: whether a later run of the same series counts (new fetches or the same
files). It counts only after an owner ruling recorded next to the earlier result, which stays (`spec:1739-1741`).
This is the natural question when a series is WITHHELD because a provider could not be fetched.

Where the owner's sentence goes: `results/RULINGS.md` on the run branch, next to the result it concerns. Each entry
gives the date (KST), the series, the `run_id`, the owner's words verbatim and what follows (`rulings-md:15`,
`pp-readme:206-219`). Step 10 carries every such ruling into the execution record and the spec's Status block
(`spec:1750-1753`).

#### 1.1.7 Report sentences (Korean)

All three PASS:

> 공급사 대조 결과를 읽었습니다. 공급사 대조는 파일럿이 읽는 고정 파일 세 개를 다른 공급사 자료와 맞춰 본 검사입니다.
> SPY, DGS3MO(금리), BTC-USD 모두 PASS입니다. 요약 세 개는 판정으로 고정한 도구(sha256 f2fe72cd…0184)로 만들어졌고,
> 고정 파일의 md5도 표와 같습니다. sha256과 md5는 파일 내용이 같은지 확인하는 지문 값입니다.
> 경고는 `<없습니다 | n건입니다: 시계열, 공급사, 검사 이름>`.
> 이 결과로 파일럿 1(SPY)을 시작하실 수 있습니다. 파일럿 2(BTC-USD)는 파일럿 1이 패리티 검사를 통과한 뒤에 시작합니다.
> 패리티 검사는 QUANTGEN 계산과 Nautilus 계산이 같은지 보는 검사입니다.

A series is FAIL:

> `<시계열>` 대조가 FAIL입니다. 고정 파일 자체 검사나 독립·교차 공급사와의 비교가 미리 정한 허용치를 넘었다는 뜻입니다.
> 걸린 곳은 공급사 `<공급사>`의 `<검사 이름>` 검사입니다. 요약에는 값이 없고 개수와 구간만 있습니다. 제가 볼 수 있는 것은
> `<예: 허용치를 넘은 날 n일, 허용 n일>`까지입니다. 이 실행이 그 시계열의 기록 실행입니다. 기록 실행은 시계열마다 처음
> PASS, FAIL, WITHHELD로 끝난 실행이며, 다시 돌린 결과는 소유자 판정 없이는 인정되지 않습니다.
> 아래에서 하나를 골라 주십시오.
> 1번. 불일치를 기록에 적고 파일럿을 진행합니다. 표와 고정 파일은 그대로 둡니다.
> 2번. 원인을 찾을 때까지 이 시계열의 파일럿을 미룹니다.
> 3번. 자료를 바꿉니다. 이 경우 러너의 코드 지문이 바뀌어 Windows 인계(Step 7A)의 7A.2부터 7A.5까지를 다시 해야 합니다.
> 코드 지문은 실행 코드 파일들의 해시입니다.
> `<시계열> = 1번`처럼 한 줄로 답해 주시면 됩니다. 답하신 문장은 고치지 않고 판정 기록 파일(results/RULINGS.md)에 그대로 적습니다.

A series is WITHHELD:

> `<시계열>` 대조가 WITHHELD(판정 보류)입니다. 끝까지 비교된 독립·교차 공급사가 하나도 없어서 통과도 실패도 아니라는
> 뜻입니다. 이유: `<요약의 withheld_reasons 문구, 또는 coverage가 PASS가 아닌 공급사>`.
> 위의 1번·2번·3번 가운데 하나를 골라 주십시오. 공급사에서 다시 받아 다시 대조한 결과를 인정할지도 따로 정하실 수
> 있습니다. 그 경우 앞선 결과는 지우지 않고 함께 남습니다.

A fetch line is off, before any compare:

> `<공급사>` 수신 줄이 기대와 다릅니다: `<붙여 주신 줄>`. `<weekend dates가 0이 아님 | first가 기간 시작보다 늦음 |
> kis paging stopped at 문구가 있음 | UNAVAILABLE>`. 대조는 시계열마다 첫 실행이 기록으로 남으므로 아직 돌리지 마십시오.
> `<이 경우에 쓸 대조 줄을 아래에 적었습니다 | 원인을 확인한 뒤 다시 알려 드리겠습니다>`.

`tool.sha256` differs from the fixed value:

> `<시계열>` 요약을 만든 도구 파일이 판정으로 고정한 것과 다릅니다(요약의 tool.sha256이 고정값과 다름). 스펙 10.5에 따라
> 이 실행은 소유자 판정이 있어야만 인정됩니다. 도구 클론을 최신으로 맞추지 않은 채 돌렸는지 확인해 주십시오.

The owner decides: which option for a series that is not PASS; whether a later run counts; whether a run made with
other tool bytes counts; any change to the providers or thresholds after a summary exists (`pp-readme:210-216`).
Claude decides none of these.

### 1.2 Pilot 1 (Step 8, E1-SPY): the run folder

The command the owner runs (`spec:1631`):
`python -B -m tools.nautilus.runner --table docs/nautilus_bridge/registration/pilot1_E1_spy.json --of-record`.
It registers 12 settings in the E1 ledger and runs 24 children: one per setting at 1x and at 2x cost
(`runner:1439-1443`, `t1:17-30`). Cost is 50 bp per side, 100 bp at 2x (`t1:31`).

Where the outputs are (`runner:1256`, `runner:1396`, `runner:1472`, `parity:517`):

```
docs/nautilus_bridge/runs/
  NB-<UTC as %Y%m%dT%H%M%S%fZ>-d76d2d73/
    run.json                 the run record, schema nautilus-bridge-run/2
    NB_E1_trend_spy.json     the card; only when status is CARD_WRITTEN (card_id from t1:41)
  .locks/                    git-ignored
```

A fallback `run.final.<pid>.json` appears only when the final write of `run.json` failed (`runner:1473-1484`).

To read (after the owner's push):

```bash
git fetch origin claude/amazing-gauss-tdiguu
git ls-tree --name-only origin/claude/amazing-gauss-tdiguu docs/nautilus_bridge/runs/
git ls-tree --name-only origin/claude/amazing-gauss-tdiguu docs/nautilus_bridge/runs/<bridge_run_id>/
git show origin/claude/amazing-gauss-tdiguu:docs/nautilus_bridge/runs/<bridge_run_id>/run.json | python3 -B -I read_run.py
```

`run.json` keeps every fill, with prices at the fill bars (`runner:1127`, `spec:1148`). Reading it after the registered
run is the designed flow ("Claude reads the outputs after the owner pushes them", `spec:1631`). The script in
appendix B prints no fill row. Do not print the `fills` lists, and enter the read in the data-access history
(section 2.5).

#### 1.2.1 Checklist

1. Read: the owner's last console line. Compare with: `STATUS <status> exit=<n> record=<path or ->`
   (`runner:1484`). Exit codes: 0 card written, 1 WITHHELD, 2 refused before registration, 3 refused at registration,
   4 ERROR, 5 ABORTED (`runner:11-13`, `spec:855-859`). Then: `STATUS REFUSED exit=2 record=-` wrote nothing, to the
   repository or to a ledger (`runner:1513-1518`); the lines above it give the refusal id (R-01 to R-17) and a line
   `remedy: ...` (`runner:96-118`), or the tail of a traceback when an unexpected exception stopped the run before
   registration (`runner:1537-1540`). Go to 1.2.6.
2. Read: the `record=` path. Compare with: it ends in `run.json`. Then: if it names `run.final.<pid>.json`, the
   final write of `run.json` failed. Normally both files are then in the folder: an older `run.json` whose `status`
   is `IN_PROGRESS`, written right after registration and after each child (`runner:1426`, `runner:1443`,
   `runner:1457`), and the fallback with the final status (`runner:1472-1477`). The re-run check and the pilot-2
   check read only `run.json` (`runner:246`, `runner:416`). Left as it is, the stale `IN_PROGRESS` record lets a
   plain re-run through (`runner:253`) and makes the runner refuse pilot 2 with R-11 although pilot 1 passed,
   because `parity` is still null in that record (`runner:419-420`). So: Claude reads the fallback file by its own
   name; no re-run and no pilot 2 starts; and the owner replaces `run.json` with the fallback before either
   (`record:183`: "the owner renames it to `run.json`"). That replacement is the owner's decision and his edit. The
   owner's sheet tells him to send the line and wait for one rename line from Claude (`sheet`, section G). No
   PowerShell line for it was tried on Windows (not verified): write it for the folder state the owner reports,
   and say that it overwrites the `IN_PROGRESS` file.
3. Read: the folder list. Compare with: one new folder whose name ends `-d76d2d73`, holding `run.json` and, with a
   card, `NB_E1_trend_spy.json`. Then: any other file in the folder is reported, not interpreted.
4. Read: `schema`, `mode`, `pilot`, `stub_child`. Compare with: `nautilus-bridge-run/2`, `of-record`, `E1-SPY`,
   `false` (`runner:62`, `runner:1230-1231`, `runner:1296`).
5. Read: `status`. Compare with: one of `IN_PROGRESS`, `CARD_WRITTEN`, `WITHHELD`, `REFUSED_REGISTRATION`, `ERROR`,
   `ABORTED` (`runner:60`). Then: see 1.2.3.
6. Read: `git.head`, `git.anchor`, `git.clean`, `git.offending`, `git.anchor_problem` (`runner:478-479`,
   `runner:1306`). Compare with: `anchor` is `git:<head>`, `clean` true, `offending` empty, `anchor_problem` null;
   `head` is on the research branch (`git merge-base --is-ancestor <head> origin/claude/amazing-gauss-tdiguu`).
   Then: write `head` down. Step 10's diff check starts from the earliest such head (section 2.9).
7. Read: `table.table_sha256`, `table.code_sha256` (`runner:1296-1298`). Compare with: the two values of 0.1.
   Then: a different `code_sha256` means a code file changed after 7A.3. The runner refuses that case with R-11
   unless `owner_confirmed` was rewritten (`runner:430-433`), so report it at once.
8. Read: `data` (`runner:1336-1338`, `runner:1344`). Compare with: `prices_md5` `d2164597d576e1b2fcadde063065811d`,
   `rf_md5` `661722143f24930a29b58c535d227c1b`, `start` 2004-12-01, `end` 2026-09-25 (`t1:11-15`). Report
   `sessions` and `rounding_changed`.
9. Read: `provenance.p0a`, `provenance.p0b` (`runner:1364`, `parity:480`). Compare with: `p0a.passed` true,
   `p0b.pass` true.
10. Read: `costs` (`runner:1371-1372`). Compare with: `cost_bps` 50.0, `floor_bp` not above 50.0, `stress` 2.0.
11. Read: `egress.probe.blocked` (`runner:1320`, `runner:581`). Compare with: `true`.
12. Read: `registration` (`runner:1380-1382`, `runner:1411-1412`, `runner:786-787`): `family_id`, `ledger_path`,
    `hash_before`, `hash_after`, `n_raw_before`, `n_raw_after`, `market_n_raw`, `rows` of
    `{col, config_id, row_md5, appended}`. Compare with: `family_id` `E1`; 12 rows, `col` 0 to 11. Then: `appended`
    false means the row was already there, which Step 8 allows ("appended or already present", `spec:1631`). The
    owner reported 12 E1 rows from the 2026-11-04 registration (`spec:2140-2143`), so 12 times false is the likely
    case. That is not verified: the ledger is on the owner's machine.
13. Read: `children`, 24 entries of `col`, `stress`, `returncode`, `ntstatus`, `timed_out`, `seconds`, `manifest`,
    `census_sha256`, `fills`, `stdout_tail`, `stderr_tail`, `invalid` (`runner:1164-1165`, `runner:1111-1113`).
    Compare with: `returncode` 0, `timed_out` false and `invalid` empty on all 24;
    `manifest.input.ledger_hash_after_registration` equals `registration.hash_after` on all 24 (`runner:1005-1006`,
    `runner:1103`). Then: that echo is Step 8's evidence that every child ran after registration (`spec:1631`).
14. Read: `parity.hard_pass` (`parity:482`). Compare with: `true`. Then: see 1.2.2 for the checks behind it.
15. Read: `parity.failed` and `parity.warnings`, two lists of text lines (`parity:377-378`, `parity:381`,
    `parity:398`). Then: quote every line of `failed`; count and list `warnings`.
    Steps 16 to 20 need `parity.hard_pass` true. When it is false the runner does not score: `gate.trial_counts`,
    `gate.quantgen`, `gate.nautilus`, `gate.agree` and `gate.reference` are all null (`parity:483`, `parity:487`;
    test L1-13 asserts it, `tests/nautilus_acceptance.py:2524`), and the console shows `parity: hard_pass False ...`,
    `decisions: quantgen None, nautilus None`, the `reason:` lines and STATUS, with no `trial counts:` line
    (`parity:467`). Take the row counts from `registration.n_raw_after` and `registration.market_n_raw` then, and
    write "trial counts not computed".
16. Read: `gate.trial_counts` (`parity:250-252`): `len_grid`, `family_n_raw`, `market_n_raw`, `U`, `n_trials`,
    `study_configs_absent`. Compare with: `len_grid` 12; `n_trials` equals `family_n_raw + U`; `U` at most 24
    (`spec:1650`, `t1:42-67`). If E1 still holds only the 12 rows of 2026-11-04, the counts are 12, 12, 12, 24 and 36.
    These are the values the runbook expects on the registration line (`runbook:136-138`); the owner reported only
    that E1 held 12 rows (`spec:2140-2143`), and 24 and 36 follow from 12 rows by `parity:246-252`. No source
    records them as seen (not verified). A larger `family_n_raw` is not an error; report it.
17. Read: `gate.quantgen` and `gate.nautilus`, each `decision`, `reason`, `revise_target`, `predicates`, `stats`
    (`parity:432-437`). Compare with: the two `decision` values are equal and each is one of `PASS`, `REVISE`,
    `REJECT`, `INSUFFICIENT_DATA` (`validate:50`).
18. Read: `gate.agree` (`parity:497`): `ok`, `reason`. Compare with: `ok` true. Then: `reason` is
    `decision mismatch` or `benchmark test dropped` otherwise (`parity:274-280`).
19. Read: `gate.reference`. Compare with: `null`; pilot 1 names no reference card (`t1:68-69`).
20. Read: `gate.selection` (`parity:484-485`): `origins`, `chosen`, `note`. Compare with: the spec expects 38
    origins from the row counts alone (`spec:1653-1654`). Report the count; a different count is a finding, not a
    failure rule.
21. Read: `withheld_reasons` (`runner:1509`). Compare with: empty when `status` is `CARD_WRITTEN`.
22. Read: `card` (`parity:518`): `path`, `md5`. Compare with: the md5 of the pushed card file,
    `git show <ref>:docs/nautilus_bridge/runs/<id>/NB_E1_trend_spy.json | md5sum`. This comparison is this document's
    own check, not the spec's. The card is written once, with LF, and never overwritten (`parity:353-357`).
23. Read: the card file. Its top-level fields (`validate:802-825`): `card_id`, `kind`, `hypothesis`, `rules`,
    `universe`, `data`, `costs`, `protocol`, `trials`, `seed`, `stats`, `tests`, `decision`, `decision_reason`,
    `revise_target`, `lines`, `decay_haircut`, `created`, `author`, `results_file`, `results_md5`, `citations`.
    Compare with: `card_id` `NB_E1_trend_spy`; `decision` equals `gate.nautilus.decision`; `results_file` equals
    the `bridge_run_id` (`parity:349-350`); `trials` holds `N_planned`, `N_total`, `family_id`, `family_n_raw`,
    `market_n_raw`, `U`, `study_configs_absent`, `config_ids`, `row_md5s`, `ledger_hash_at_run`, `ledger`
    (`parity:332-339`); `stats.parity` holds `hard_pass`, `worst_corr`, `worst_abs_dsr`, `max_daily_gap`, `P12`,
    `warnings`, `bars` (`parity:314-320`); `stats.quantgen_score` shows QUANTGEN's own score (`parity:331`);
    `rules.claim_label` is the table's (`parity:311`, `t1:40`).
24. Read: `earlier_runs`, `supersedes`, `rerun_reason`, `record_write_failures`, `cleanup_leftovers`, `error`
    (`runner:1231-1236`). Compare with: empty, null, null, empty, empty, null on a first clean run. Then: report
    anything else.

#### 1.2.2 The parity checks and their tolerances

`parity.legs` is a list of 24 entries, one per (column, cost level), each with `col`, `stress`, `P13` and, when
`P13.pass` is true, `P1` to `P10` (`parity:147-178`). `parity.P0b`, `parity.P11` and `parity.P12` are separate
(`parity:382-383`). `parity.bars` and `parity.owner_bars` print the bars used (`parity:26-28`).

| ID | What | Bar | Kind | Fields in `run.json` | Lines |
|---|---|---|---|---|---|
| P0a | dates, 9-decimal closes and cash rate equal the study's loaders, byte for byte | equal | hard; a failure refuses with R-13 before registration | `provenance.p0a.passed` | `spec:872`, `runner:716-747` |
| P0b | the benchmark from the runner's closes equals the study's expression | equal | hard, withholds | `parity.P0b`: `pass`, `rows`, `study_rows`, `first_difference` | `spec:872`, `parity:189-195` |
| P1 | the child's logged decision against QUANTGEN's on every decision bar | 100 %, except a decision whose QUANTGEN margin is below 1e-9; each exemption listed | hard | `P1`: `value`, `decision_bars`, `same_bars`, `mismatches`, `exempt`, `pass`, `owner_pass` | `spec:873`, `parity:123-133` |
| P2 | correlation of the rebuilt Nautilus returns and QUANTGEN's | at least 0.9999 | hard | `P2`: `value`, `pass`, `owner_pass` | `spec:874`, `parity:159-160` |
| P3 | absolute Sharpe difference | at most 0.01 | hard | `P3`: `value`, `pass`, `owner_pass` | `spec:875`, `parity:161-162` |
| P4 | bars with a fill equal the bars where QUANTGEN's weight changes | equal | hard | `P4`: `fill_bars`, `dw_bars`, `pass` | `spec:876`, `parity:163-164` |
| P5 | largest gap of a fill price from the close | at most 1e-6 | warning | `P5`: `value`, `pass` | `spec:877`, `parity:165-166` |
| P6 | turnover ratio | in [0.99, 1.005] | warning | `P6`: `value`, `pass` | `spec:878`, `parity:167-169` |
| P7 | each commission recomputed, to the cent, in USD; the manifest echoes cost and stress | equal | hard | `P7`: `bad_fills`, `echo`, `pass` | `spec:879`, `parity:136-144` |
| P8 | drawdown difference | at most 0.005 | warning | `P8`: `value`, `pass` | `spec:880`, `parity:171` |
| P9 | tracking error | at most 0.001 | warning | `P9`: `value`, `pass` | `spec:881`, `parity:172-173` |
| P10 | daily gap bound, per row | no row over the bound | warning | `P10`: `max_gap`, `rows_over`, `pass` | `spec:882`, `parity:174-177` |
| P11 | Nautilus's own selection against QUANTGEN's, per origin | reported | diagnostic, never withholds | `parity.P11`: list of `origin`, `quantgen`, `nautilus`, `match`, `is_sharpe_gap` | `spec:883`, `parity:218-225` |
| P12 | P2 and P3 on the selection-matched out-of-sample series, at 1x and 2x | as P2 and P3 | hard | `parity.P12`: `1x` and `2x`, each `corr`, `abs_dsr`, `pass`, `owner_pass` | `spec:884`, `parity:228-230`, `parity:88-92` |
| P13 | completeness: the child's own checks and the parent's re-derivation, the census, the reconciliation, the ledger-hash echo | all pass | hard | `P13`: `pass`, `reasons` (the C-xx ids of that child). An invalid leg holds `P13` only, with no `P1` to `P10` | `spec:885`, `parity:151-154` |

`parity.hard_pass` is true only when `parity.failed` is empty, no walk-forward error occurred and P12 was computed
(`parity:482`). Every hard failure withholds the verdict for the whole grid (`spec:865-866`). Warnings P5, P6, P8, P9
and P10 never withhold; they go into the run record and the card (`spec:895`, `spec:1304`). The owner's original bars
(P1 0.98, P2 0.99, P3 0.05) are printed next to the corrected ones as `owner_pass` (`parity:28`).

The runner also prints these lines above the STATUS line (`parity:458-473`): `parity: hard_pass ...; worst corr ...
(bar 0.9999, owner 0.99); worst abs dSR ... (bar 0.01, owner 0.05)`, `trial counts: len_grid ..., family_n_raw ...,
market_n_raw ..., U ..., n_trials ...`, `decisions: quantgen ..., nautilus ...` and one `reason: ...` line per
reason.

#### 1.2.3 Status values

| `status` | Exit | Meaning | Card | Lines |
|---|---|---|---|---|
| `CARD_WRITTEN` | 0 | every hard check passed, both engines reached the same decision, the ledger did not move | yes | `parity:515-522` |
| `WITHHELD` | 1 | the run finished and no card was written; `withheld_reasons` says why | no | `parity:523` |
| `REFUSED_REGISTRATION` | 3 | registering a row raised (R-12); the rows appended so far stay | no | `runner:1492-1494` |
| `ERROR` | 4 | an unexpected exception after registration (G-06), or the gate constants changed during the run (G-04) | no | `runner:1505-1506`, `parity:504-509` |
| `ABORTED` | 5 | interrupted after registration (G-07), for example Ctrl+C | no | `runner:1495-1496`, `runner:1507-1508` |
| `IN_PROGRESS` | none | the process died before the final write, or the final write failed and a `run.final.<pid>.json` sits beside it (step 2 of 1.2.1) | no | `runner:1414`, `runner:1426`, `runner:1472-1477` |

What WITHHELD means. It is a run status, not a verdict on the strategy. The 12 rows are registered and stay, because
the ledger is append-only (`spec:259-262`). No card exists, because the two engines could not be shown to agree, or
the reference could not be reproduced. "WITHHELD is never a card decision" (`spec:944-945`). The reasons that can
appear in `withheld_reasons`:

| Reason text starts with | Cause | Lines |
|---|---|---|
| `C-01:` to `C-15:` then `(column <n> (...), <1\|2>x)`, or `P13: no rebuild (column ...)` | a child run was invalid | `parity:375-376`, `spec:1280-1294` |
| `P13: column <n> (...), <1\|2>x: {...}` | the same invalid child once more: `P13` is one of the hard checks, so the line of `parity:377` is added for it after the child's own C-xx lines | `parity:29`, `parity:377` |
| `P1:`, `P2:`, `P3:`, `P4:`, `P7:` then `column <n> (...), <1\|2>x:` | that hard check failed for that column and cost level | `parity:377` |
| `P0b:` | the benchmark differs from the study's | `parity:381` |
| `P12: 1x:` or `P12: 2x:` | the selection-matched series failed P2 or P3 | `parity:398` |
| `G-02: decision mismatch: quantgen X, nautilus Y; predicates differ: ...` | the engines' decisions or gate predicates differ | `parity:498-499`, `parity:440-444` |
| `G-02: benchmark test dropped` | a score has no benchmark test | `parity:276-277` |
| `G-03:` | `walk_forward` or the scoring raised | `parity:393`, `parity:403`, `parity:430` |
| `G-05: ledger moved after registration` | a row was added to the ledger during the run | `parity:422`, `parity:514` |
| `G-08: reference drift: <fields>` | pilot 2 only, see 1.3 | `parity:502` |

Which WITHHELD records the spec counts as a valid end of Step 8 (`spec:1631`): one that names the failing hard
check; or, when parity passed, one that says "decision mismatch". Step 9 adds "reference drift" (`spec:1632`). A
WITHHELD with `parity.hard_pass` true for another reason (`G-02: benchmark test dropped`, `G-03`, `G-05`) is not
named as an end by either row. What follows it needs the owner's ruling (section 5, question 14).

Re-runs. A re-run is refused (R-17) unless every earlier record of the table is `IN_PROGRESS`, `ABORTED`, `ERROR`, or
`WITHHELD` with reasons that all start with `C-06`, or the owner passes `--rerun-of <bridge_run_id> --reason
"<text>"` (`runner:253-254`, `runner:290-293`, `spec:851-854`).

The C-06 case does not work the way the spec says. By the code as read, a child that ends with C-06 puts two lines
into the reasons: `C-06: ... (column ...)` and `P13: column ...: {...}` (`parity:375-377`, because `HARD` holds
`P13`, `parity:29`). The second line does not start with `C-06`, so `runner:254` is false and a plain re-run is
refused with R-17. The three expressions were copied into a stand-in and gave `['C-06: exit 1 (column 0 (...), 1x)',
"P13: column 0 (...), 1x: {...}"]` and `False`. Not verified on a real run; no test covers it (L1-5,
`tests/nautilus_acceptance.py:2474-2513`, tests a `CARD_WRITTEN` record and a planted `IN_PROGRESS` one). So tell
the owner that a WITHHELD run with C-06 lines needs `--rerun-of` and a reason, unless a real refusal or acceptance
shows otherwise.

Which card counts after a re-run (`spec:853-854`): "the new record names that run in `supersedes`. The card of
record is the latest `CARD_WRITTEN` card that no later record supersedes." When a table has more than one `NB-`
folder, do the whole readout for each folder and name the card of record.

#### 1.2.4 The expected verdict for pilot 1

The spec states it before the run (`spec:1672-1680`): "Pilot 1: a non-PASS verdict is expected". In the gate's own
order: INSUFFICIENT_DATA first, when there are fewer than 30 out-of-sample trades; otherwise REJECT on the benchmark
test; REVISE is unlikely. "Any of these is a finding about the rule, not a bridge failure; changing the grid after
seeing the result is a new trial." So the good outcome of pilot 1 is `status` `CARD_WRITTEN` with a card whose
`decision` is `INSUFFICIENT_DATA` or `REJECT`. A synthetic rehearsal did end that way: "L2-7: CARD_WRITTEN; quantgen
INSUFFICIENT_DATA, nautilus INSUFFICIENT_DATA" (`record:149`). No parity number exists for the pilot window by
design; real margins are unverified until this run (`spec:927-929`).

#### 1.2.5 Step 8 "Done when", clause by clause

Quoted from `spec:1631`:

| Clause | Where to see it |
|---|---|
| "E1 holds the 12 `config_id`s, appended or already present, and recorded" | `registration.rows`: 12 entries with `config_id`, `row_md5`, `appended` |
| "every manifest echoes the post-registration ledger hash" | checklist step 13 |
| "every hard check passes for all 12 columns at 1x and 2x, or a WITHHELD record names the failing check" | `parity.hard_pass`, or `status` `WITHHELD` with `withheld_reasons` |
| "if parity passed, the run folder holds `NB_E1_trend_spy.json` with the decision both engines reached, the four trial counts, the manifest hashes and the selection used, or a WITHHELD record says \"decision mismatch\"" | the card: `decision`, `stats.quantgen_score`, `trials`. For "the selection used" the card holds `rules.selection`, which is one fixed sentence (`parity:33`, `parity:310`), plus `stats.chosen_last` and `stats.walk_forward` (`parity:328-329`); the lists of origins and chosen columns are only in `run.json` under `gate.selection` (`parity:484-485`). For "the manifest hashes" the card holds `trials.row_md5s` and `trials.ledger_hash_at_run` (`parity:335-336`); the per-child manifests with their `hashes` are in `run.json` under `children[].manifest`, not in the card. Whether that meets "the manifest hashes" and "the selection used" is not verified; record both as wording points in the Step 10 record |
| "the owner has committed and pushed the run folder" | the folder is on `origin/claude/amazing-gauss-tdiguu` |

#### 1.2.6 Report sentences (Korean) and the owner's decisions

`CARD_WRITTEN`, decision `INSUFFICIENT_DATA` or `REJECT` (the expected case):

> 파일럿 1 결과를 읽었습니다. 실행은 끝까지 돌았고 카드 NB_E1_trend_spy.json이 만들어졌습니다. 카드는 판정을 적은 기록
> 파일입니다. 패리티 검사는 12개 설정 모두, 비용 1배와 2배에서 통과했습니다. 패리티 검사는 QUANTGEN 계산과 Nautilus
> 계산이 같은지 보는 검사입니다. 두 계산의 일별 수익률 상관은 가장 낮은 값이 `<값>`(기준 0.9999 이상)이고,
> Sharpe 차이의 최댓값은 `<값>`(기준 0.01 이하)입니다. Sharpe는 위험 대비 수익을 재는 지표입니다.
> 두 엔진의 판정은 같고 `<INSUFFICIENT_DATA(자료 부족) | REJECT(기각)>`입니다.
> 이 판정은 스펙 10.3이 실행 전에 미리 적어 둔 예상과 같습니다. 전략 규칙에 대한 결과이며 브리지의 실패가 아닙니다.
> 브리지는 QUANTGEN과 Nautilus를 잇는 장치입니다.
> 시행 수는 격자 12, E1 원장 `<n>`행, 미국 시장 행 `<n>`, 등록되지 않은 과거 설정(U) `<n>`, 합계 `<n>`입니다. 격자는 미리
> 정해 둔 설정 묶음이고, 원장은 시행을 한 줄씩 쌓는 기록 장부입니다.
> 경고는 `<없습니다 | n건: 검사 이름, 설정, 비용 수준>`. 경고는 판정을 막지 않습니다.
> `<BTC-USD 대조가 PASS이므로 파일럿 2를 시작하실 수 있습니다 | 파일럿 2는 BTC-USD 대조에 대한 판정을 주신 뒤에 시작합니다>`.

`CARD_WRITTEN`, decision `PASS` or `REVISE` (not the expected case):

> 파일럿 1이 카드를 만들었고 판정은 `<PASS | REVISE>`입니다. 스펙 10.3은 실행 전에 자료 부족이나 기각을 예상했으므로
> 예상과 다릅니다. 패리티 검사는 통과했습니다. 이 결과를 보고 설정을 바꾸면 새 시행으로 세어야 하므로 아무것도 바꾸지
> 않았습니다. 판정 사유 문구는 `<decision_reason>`입니다.

`WITHHELD`, `parity.hard_pass` false:

> 파일럿 1이 WITHHELD(판정 보류)로 끝났습니다. 카드는 없습니다. 두 엔진의 결과가 기준 안에서 같다고 확인하지 못했다는
> 뜻이며, 전략이 좋다 나쁘다는 판정이 아닙니다. 걸린 검사: `<withheld_reasons의 줄 그대로>`.
> 등록된 12행은 원장에 그대로 남습니다. 이 상태에서는 러너가 파일럿 2를 거부합니다(R-11). 러너는 파일럿을 돌리는
> 프로그램입니다.
> 다음에 무엇을 할지는 스펙에 절차가 없어 소유자 판정이 필요합니다. 제가 원인을 정리해 선택지를 따로 올리겠습니다.

`WITHHELD`, `parity.hard_pass` true, reason `G-02: decision mismatch`:

> 파일럿 1이 WITHHELD(판정 보류)로 끝났습니다. 패리티 검사는 12개 설정 모두 통과했지만 카드는 만들어지지 않았습니다.
> 이유: decision mismatch, 곧 두 엔진의 판정이나 판정 조건이 다릅니다(`<mismatch 줄 그대로>`).
> 스펙은 이것도 Step 8의 유효한 끝으로 적고 있습니다. 러너의 파일럿 2 조건은 패리티 통과이므로 파일럿 2는 막히지 않습니다.

`WITHHELD`, `parity.hard_pass` true, another reason (`G-02: benchmark test dropped`, `G-03` or `G-05`):

> 파일럿 1이 WITHHELD(판정 보류)로 끝났습니다. 패리티 검사는 12개 설정 모두 통과했지만 카드는 만들어지지 않았습니다.
> 이유: `<benchmark test dropped: 기준 수익과의 비교가 빠짐 | G-03: 채점 계산이 오류를 냄 | G-05: 실행 도중 원장이 바뀜>` (`<사유 줄 그대로>`).
> 스펙은 이 경우를 Step 8의 끝으로 적지 않았습니다. 그래서 이 실행으로 Step 8을 끝난 것으로 볼지, 원인을 본 뒤 다시
> 돌릴지는 소유자 판정이 필요합니다. 다시 돌리려면 사유 문장이 있어야 합니다. 러너의 파일럿 2 조건은 패리티 통과이므로
> 러너가 파일럿 2를 막지는 않습니다.
> `<G-05일 때: 원장에 쓴 다른 프로그램이 무엇이었는지 먼저 찾겠습니다. 실행하는 동안 QUANTGEN 앱이나 다른 작업이 열려 있었는지 알려 주십시오.>`

`ERROR`, `ABORTED` or `IN_PROGRESS`:

> 파일럿 1이 `<상태>`로 끝났습니다. `<예기치 않은 오류 | 실행이 중단됨 | 기록이 진행 중으로 남음>`: `<error.message>`.
> 이 경우 러너는 사유 문장 없이 같은 명령을 다시 받아 줍니다. 등록된 행은 그대로 다시 쓰입니다.
> 다시 실행하기 전에 원인을 먼저 확인하겠습니다. 실행 여부는 답을 드린 뒤에 정해 주십시오.

`WITHHELD` whose reasons are C-06 lines (a child died or timed out):

> 파일럿 1이 WITHHELD(판정 보류)로 끝났습니다. 24번의 실행 가운데 `<n>`번이 중간에 죽거나 시간을 넘겼습니다: `<C-06 줄 그대로>`.
> 스펙은 이런 경우 사유 문장 없이 다시 실행할 수 있다고 적었습니다. 그런데 러너 코드를 읽어 보면 같은 실행에 대해
> `P13:`으로 시작하는 사유 줄이 함께 붙어서, 러너가 앞선 실행 번호와 사유 문장을 요구할 것으로 보입니다
> (`--rerun-of <실행 번호> --reason "<사유>"`). 실제 실행으로 확인한 것은 아닙니다(미검증).
> 원인을 먼저 확인해 보고하겠습니다. 다시 실행할지와 사유 문장은 그 뒤에 정해 주십시오.

`REFUSED_REGISTRATION` (exit 3):

> 파일럿 1이 원장에 설정을 등록하는 도중에 멈췄습니다(R-12). 그때까지 등록된 행은 원장에 남아 있습니다.
> 이 경우 러너는 같은 명령을 그대로 받아 주지 않습니다. 다시 실행하려면 앞선 실행 번호와 사유 문장을 함께 적어야 합니다
> (`--rerun-of <실행 번호> --reason "<사유>"`). 원인을 먼저 확인해 보고하겠습니다. 사유 문장은 소유자께서 정해 주십시오.

`STATUS REFUSED exit=2`:

> 러너가 등록 전에 실행을 거부했습니다(`<R-xx>`). 저장소와 원장에는 아무것도 쓰지 않았습니다. 이유: `<거부 줄>`.
> 러너가 알려 준 조치: `<remedy 줄>`. `<제가 확인할 것 | 소유자께서 하실 것>`.

The record names `run.final.<pid>.json`:

> 실행 기록이 run.json이 아니라 `<run.final.<pid>.json>`으로 저장됐습니다. 마지막 쓰기가 한 번 실패했다는 뜻입니다.
> 같은 폴더의 run.json은 "진행 중" 상태에서 멈춘 옛 기록입니다. 러너는 run.json만 읽으므로, 이대로 두면 파일럿 2가
> 거부되고 재실행 규칙도 어긋납니다. 그래서 파일럿 2나 재실행 전에 run.json을 이 파일로 바꿔야 합니다.
> 바꾸는 것은 소유자의 결정이고, 옛 run.json을 덮어씁니다. 바꾸기로 하시면 한 줄을 적어 드리겠습니다. 그 전에는
> 파일럿 2도 재실행도 하지 마십시오. 저는 올라온 `<run.final.<pid>.json>`을 그 이름으로 읽겠습니다.

The owner decides: what follows a parity failure (the documents give no procedure); what follows a WITHHELD with
parity passed that is not "decision mismatch"; whether to re-run and the reason sentence for `--rerun-of ...
--reason`; any change to code or a table, which needs Windows re-validation and a new `owner_confirmed`
(`spec:1607-1609`); whether pilot 2 starts; whether a `run.json` is replaced by its fallback. Claude never writes a
table field, never re-runs and never edits a run folder.

### 1.3 Pilot 2 (Step 9, C3-BTCUSD): the run folder

The spec's Step 9 row gives no literal command (`spec:1632`). By the runner's usage line (`runner:4`) it is
`python -B -m tools.nautilus.runner --table docs/nautilus_bridge/registration/pilot2_C3_btcusd.json --of-record`;
the owner's run sheet is the authority for the exact line. It registers 5 settings in the C3 ledger and runs 10
children, at 10 bp and 20 bp (`t2:17-24`). There is no cash rate: `rf_file` is null (`t2:14-15`,
`runner:1339-1340`). The folder is `NB-<UTC>-e2ec073c`, and the card is `NB_C3_crypto_trend_btcusd.json` (`t2:34`).

Everything in 1.2 applies with these differences.

1. Read: before anything, whether the runner refused with R-11. Compare with: the text `of-record C3-BTCUSD needs
   an of-record E1-SPY record whose parity passed for all 12 columns at both cost levels under code <16 hex>`
   (`runner:436-438`). Then: the runner looks for a `run.json` under `docs/nautilus_bridge/runs/*/` on the owner's
   disk with `mode` `of-record`, `pilot` `E1-SPY`, the same `table.code_sha256`, `parity.hard_pass` true and 12
   registration rows (`runner:413-424`). It does not require `status` `CARD_WRITTEN`. It never reads a
   `run.final.<pid>.json`.
2. Read: `pilot`, `table.table_sha256`. Compare with: `C3-BTCUSD`; the pilot-2 value of 0.1.
3. Read: `data`. Compare with: `prices_md5` `bc76f530ff24ab445367fe826150bc10`, `rf_file` null, `rf_md5` null,
   `start` 2014-09-17, `end` 2026-09-25 (`t2:10-15`).
4. Read: `costs.cost_bps`. Compare with: 10.0 (`t2:24`).
5. Read: `registration`. Compare with: `family_id` `C3`; 5 rows, `col` 0 to 4. `n_raw_before` is whatever C3 held:
   the owner reported at least 17 rows on 2026-11-04 and did not send the exact count (`spec:2142-2143`). C3 also
   holds paper_live rows of other markets (`spec:1664`).
6. Read: `children`. Compare with: 10 entries, as step 13 of 1.2.1.
7. Read: `parity.legs`. Compare with: 10 entries; the bars are those of 1.2.2.
8. Read: `gate.trial_counts`. Compare with: `len_grid` 5; `U` at most 11 (`spec:1664`, `t2:35-47`); `market_n_raw`
   counts the rows whose market is `CRYPTO` (`parity:251`, `t2:6`).
9. Read: `gate.quantgen.predicates.pbo_meaningful`, and the same under `gate.nautilus`. Compare with: `false`.
   With 5 columns PBO is reported for information only (`spec:1632`, `spec:1667`, `parity:258`): the gate needs 8
   configurations before PBO counts (`validate:58-68`, `pbo_min_configs` 8). The over-search check then "uses the
   share of splits where the in-sample winner loses" (`spec:1632`). Read, on both sides: `predicates.flat`,
   `predicates.pbo_ok`, `predicates.pbo_reject` and `stats.prob_loss_oos`. Compare with: `flat` is
   `prob_loss_oos <= 0.10`; `pbo_ok` equals `flat`; `pbo_reject` is `false` (`parity:258-262`, `validate:68`,
   `prob_loss_max` 0.10). Report `stats.pbo` and `stats.prob_loss_oos` as numbers.
10. Read: `gate.reference` (`parity:447-455`): `card`, `drift`, `n_years_calendar`, `n_years_whole`. Compare with:
    `card` `docs/asset_expansion/cards/S_C3_crypto_trend_btcusd.json` (`t2:48`); `drift` empty. The spec says the
    card will report 9 whole years where the stored card reports 11 calendar years (`spec:1688-1689`), so
    `n_years_calendar` 11 and `n_years_whole` 9 are what it expects; those two numbers are not verified here.
    Then: see "Reference drift" below.
11. Read: the card file `NB_C3_crypto_trend_btcusd.json`. Compare with: as step 23 of 1.2.1;
    `rules.claim_label` is the pilot-2 label (`t2:33`). For the clause "reports PBO for information only": the card
    holds `tests.pbo` (`parity:348`) and, inside `stats`, `pbo` and `prob_loss_oos` (`parity:327`). The card has no
    field that says "for information only"; that follows from the 5 configurations and the predicates of step 9,
    which are in `run.json`, not in the card. Record this as a wording point in the Step 10 record.

Reference drift (G-08). The run recomputes QUANTGEN's own score and compares it with the stored card
`S_C3_crypto_trend_btcusd`, whose md5 the table pins (`t2:48-49`). `gate.reference.drift` lists every field that is
not reproduced (`parity:291-304`, `parity:452-453`):

| Name in `drift` | Compared how |
|---|---|
| `reference_card_md5` | the card's bytes against the table's md5 |
| `chosen_last` | the last chosen setting, exactly |
| `n_trades`, `n_sessions` | exactly |
| `n_years` | the number of calendar years in the walk-forward dates against the stored card's value |
| `sr_oos`, `ci90`, `oos_is`, `sr_stress`, `years_positive`, `plateau`, `pbo`, `prob_loss_oos` | within 1e-9 |
| `bench_p` | within 1/2000 |

A non-empty list gives `WITHHELD` with the reason `G-08: reference drift: <fields>` and no card (`parity:502`,
`spec:1302`). The spec counts that as a valid end of Step 9 (`spec:1632`).

Expected verdict (`spec:1682-1689`): the stored card on the same file and five settings is PASS (SR 1.19
[0.72, 1.64], DSR 1.00, 144 trades, benchmark p 0.07). If parity holds and the reference is reproduced, the expected
verdict is PASS. "A non-PASS with parity passing would be a finding to investigate, not a reason to tune anything."

Step 9 "Done when" (`spec:1632`): "Step 8's conditions hold for 5 columns at 10 and 20 bp, a WITHHELD \"reference
drift\" (G-08) being a valid end too (QUANT-R4-3); `NB_C3_crypto_trend_btcusd.json` reports PBO for information
only, and over-search uses the share of splits where the in-sample winner loses".

Report sentences (Korean):

`CARD_WRITTEN`, decision `PASS`, `drift` empty (the expected case):

> 파일럿 2 결과를 읽었습니다. 카드 NB_C3_crypto_trend_btcusd.json이 만들어졌고 판정은 PASS입니다. 스펙 10.3의 예상과
> 같습니다. 패리티 검사는 5개 설정 모두, 비용 10bp와 20bp에서 통과했습니다(가장 낮은 상관 `<값>`, 기준 0.9999 이상.
> Sharpe 차이 최대 `<값>`, 기준 0.01 이하).
> 저장된 카드 S_C3_crypto_trend_btcusd와의 비교도 맞았습니다. 달라진 항목이 없습니다.
> 이 카드는 같은 파일과 같은 설정을 다른 엔진으로 다시 계산한 것이며, 규칙에 대한 새 증거가 아닙니다.
> 시행 수는 격자 5, C3 원장 `<n>`행, 암호화폐 시장 행 `<n>`, U `<n>`, 합계 `<n>`입니다. 설정이 5개라 PBO는 참고로만 적혀 있습니다.
> PBO는 격자에서 고른 설정이 표본 밖에서 뒤처질 확률입니다.
> 이제 Step 10의 Windows 전체 검사를 실행하실 수 있습니다.

`WITHHELD`, reason `G-08: reference drift`:

> 파일럿 2가 WITHHELD(판정 보류)로 끝났습니다. 이유는 reference drift입니다. QUANTGEN 쪽 계산이 저장된 카드
> S_C3_crypto_trend_btcusd의 수치를 다시 만들지 못했다는 뜻입니다. 달라진 항목: `<drift 목록>`.
> 패리티 검사는 `<통과했습니다 | 아래 검사에서 걸렸습니다>`. 스펙은 이것도 Step 9의 유효한 끝으로 적고 있습니다.
> 원인은 따로 살펴 보고하겠습니다. 표나 설정은 바꾸지 않았습니다.

`CARD_WRITTEN`, decision not `PASS`:

> 파일럿 2가 카드를 만들었고 판정은 `<판정>`입니다. 스펙 10.3은 PASS를 예상했으므로 예상과 다릅니다. 패리티 검사는
> 통과했습니다. 스펙은 이 경우를 조사할 결과로 적고 있으며, 설정을 고칠 이유로 보지 않습니다. 사유 문구: `<decision_reason>`.

R-11 refusal:

> 러너가 파일럿 2를 거부했습니다(R-11). 저장소와 원장에는 아무것도 쓰지 않았습니다. 러너는 같은 코드 지문으로 패리티를
> 통과한 파일럿 1 기록(run.json)이 실행 기록 폴더에 있어야 파일럿 2를 돌립니다.
> `<파일럿 1 기록의 parity.hard_pass가 false입니다 | 파일럿 1 기록이 run.final 이름으로 남아 있습니다 | 그 밖의 이유>`.

The other cases use the sentences of 1.2.6 with "파일럿 2" and 5 settings.

The owner decides: the same points as pilot 1; whether a reference drift is investigated before Step 10 or noted and
carried; whether Step 10 closes when pilot 2 did not run. Step 10's Done-when says "run folders ... are committed"
(`spec:1633`) and no document says what happens when pilot 2 is blocked.

### 1.4 The Windows full run (Step 10)

The owner runs `python tests/run_all.py` on Windows and commits `qa/acceptance_results.json` (`spec:1633`,
`runbook:113`). Read the pushed file with git. Never regenerate it and never run the suite in the cloud.

The file is a JSON list of rows `{test, status, seconds, detail}`, with `reason` on NOT_RUN rows
(`run_all:127-142`, `run_all:154`). `test` is `<suite>/<name>` (`run_all:95-102`). The console summary the owner sees
is `<passed>/<total> passed, <failed> failed, <not run> not run; <path>` (`run_all:158`).

The baseline to compare with is the 7A.2 run at `563db54`: 964 rows, 844 PASS, 0 FAIL, 120 NOT_RUN; `nautilus` 57
PASS; `guard` 5 PASS; `macro` 426 PASS and 120 NOT_RUN (counted from the file at that commit on 2026-11-11).

The owner's sheet stops him before the commit unless four things hold in his three-line summary (`sheet`, step
E4): no FAIL; 964 rows; no `nautilus` NOT_RUN other than the one named test; `guard` 5 PASS. So a pushed file
should already meet items 2 to 4 below. If the owner stopped, he sends the last line of E2, the three E4 lines and
the E5 lines, and nothing is pushed: answer from those lines, and tell him whether to commit.

```bash
REF=origin/claude/amazing-gauss-tdiguu
git log -3 --format='%h %ad %an %s' --date=iso $REF -- qa/acceptance_results.json
git show $REF:qa/acceptance_results.json | python3 -B -I -c '
import collections, json, sys
rows = json.loads(sys.stdin.buffer.read().decode("utf-8"))
st = collections.Counter(r["status"] for r in rows)
print("rows", len(rows), "PASS", st["PASS"], "FAIL", st["FAIL"], "NOT_RUN", st["NOT_RUN"])
print("duplicate names", len(rows) - len({r["test"] for r in rows}))
by = collections.defaultdict(collections.Counter)
for r in rows:
    by[r["test"].split("/", 1)[0]][r["status"]] += 1
for s in sorted(by):
    print(s, dict(by[s]))
for r in rows:
    if r["status"] == "FAIL" or (r["test"].startswith(("nautilus/", "guard/")) and r["status"] != "PASS"):
        print("LOOK", r["status"], r["test"], (r.get("detail") or r.get("reason") or "")[:200])
'
```

Row by row against 7A.2 (write both files to a scratch folder outside every checkout first):

```bash
git show 563db54:qa/acceptance_results.json > "$SCRATCH/acc_7a.json"
git show $REF:qa/acceptance_results.json > "$SCRATCH/acc_step10.json"
python3 -B -I -c '
import json, sys
a, b = ({r["test"]: r["status"] for r in json.load(open(p, encoding="utf-8"))} for p in sys.argv[1:3])
print("added", sorted(set(b) - set(a)))
print("removed", sorted(set(a) - set(b)))
print("changed", sorted((t, a[t], b[t]) for t in set(a) & set(b) if a[t] != b[t]))
' "$SCRATCH/acc_7a.json" "$SCRATCH/acc_step10.json"
```

Both snippets were run on 2026-11-11 against the file as it is now (the 7A.2 file) and printed the numbers above.

1. Read: the commit that last changed the file. Compare with: a commit made on the owner's machine after both pilot
   folders were pushed, changing this file only. The owner's Step 7A commits carry the author name `unknown`
   (`fe37e82`, `e3c61cb`, `9d8d9c6`, `563db54`), and Claude's carry `Claude`, so tell them apart by that; never print
   an author's e-mail. Then: if the last commit is still `563db54`, the Step 10 run has not been pushed yet.
2. Read: the count of `FAIL`. Compare with: 0 (`spec:1633`). Then: any FAIL keeps Step 10 open. Quote the row's
   `test` and `detail`.
3. Read: the rows whose `test` starts `nautilus/`. Compare with: 57 rows at 7A.2, all PASS. Step 10 asks for "0 FAIL
   with the `nautilus` suite counted" (`spec:1633`). Step 7A allowed one NOT_RUN,
   `nautilus/test_l2_05b_input_linked_to_env_refused`, which needs Developer Mode (`spec:1624-1625`,
   `runbook:153-154`). Then: any other `nautilus/` NOT_RUN means the layer-2 tests did not run. Their reason text
   names the `.env` variable `QUANTGEN_NAUTILUS_PYTHON` (`spec:1057-1059`). Report it; do not count the suite as
   run.
4. Read: the five `guard/` rows (`guard:66-94`): `guard/test_a_tag_is_annotated_and_peels_to_the_baseline`,
   `guard/test_b_tagged_pins_match_prereg_and_frozen_rule`, `guard/test_c_no_forward_look_before_it_opens`,
   `guard/test_d_library_versions_match_the_pins_while_a_readout_is_pending`,
   `guard/test_d_pending_readouts_retire_only_when_all_three_are_in`. Compare with: the (a), (b) and (d) rows PASS,
   which is what "frozen_guard (a), (b) and (d) pass there" asks (`spec:1633`; the clauses are defined at
   `guard:7-11`). Report (c) as well.
5. Read: total, PASS, NOT_RUN, and the per-suite counts. Compare with: the 7A.2 baseline, row by row. Then: every
   added, removed or changed row is named in the report and in the closing record with its cause. This is the first
   full run after the pilots added ledger rows; whether any row depends on that is not verified.
6. Read: the summary line the owner pastes. Compare with: the counts from the pushed file. Then: if they differ, the
   pushed file is not from that run; ask.
7. Then: only when 2 to 6 hold does the closing work of Part 2 start. The numbers for `README.md` come from this
   file (section 2.7).

Report sentences (Korean):

0 FAIL, `nautilus` and `guard` as expected:

> Windows 전체 검사 결과 파일을 읽었습니다. `<통과>/<전체>` 통과, 실패 0, 미실행 `<n>`입니다. nautilus 묶음은 `<57>`개가 모두
> 통과했고, 동결 연구 보호 검사(frozen_guard) (a), (b), (d)도 통과했습니다. 2026-11-04 실행(844/964 통과, 실패 0, 미실행 120)과
> 비교해 달라진 행은 `<없습니다 | n개입니다: 검사 이름, 이전 상태, 지금 상태>`.
> 이것으로 Step 10의 소유자 실행은 끝났습니다. 이제 제가 마감 기록을 쓰겠습니다. 연구 브랜치에서 제가 고치는 파일은
> 마감 기록, 스펙, README, 실행 기록 폴더의 대조 요약 사본뿐입니다.

One or more FAIL:

> Windows 전체 검사에 실패가 `<n>`건 있습니다. Step 10은 실패 0이어야 닫힙니다. 실패한 검사: `<검사 이름>`, 사유: `<detail>`.
> 원인을 확인해 보고하겠습니다. 연구 브랜치의 코드는 제가 고칠 수 없는 범위이므로, 고쳐야 하면 방법을 따로 여쭙겠습니다.

`nautilus/` rows NOT_RUN beyond L2-5b:

> nautilus 묶음의 2층 검사 `<n>`개가 실행되지 않았습니다(미실행). 사유 문구는 `<reason>`입니다. Step 10은 nautilus 묶음이
> 집계에 들어가야 하므로 이 결과로는 닫을 수 없습니다. `.env`에 QUANTGEN_NAUTILUS_PYTHON 줄이 있는지만 확인해 주십시오.
> 값은 보내지 마십시오.

The owner decides: how a FAIL is fixed, since any fix to code on the research branch is outside what Claude may
commit there and would change `code_sha256`; whether the full run is repeated; whether a second Windows full run is
wanted after the merge of main into the research branch (no document asks for one).

## Part 2. Step 10 closing record

### 2.1 The "Done when" clauses, quoted

Step 10, who and what (`spec:1633`): "The owner runs the full suite on Windows and updates the README counts and
Total row from it (C-4); Claude writes `docs/superpowers/plans/2026-10-<dd>-nautilus-bridge-execution-record.md` with
every ruling made, its cost if wrong, and the data-access history of 10.4."

Step 10, Done when (`spec:1633`), clause by clause:

1. "The Windows full run shows 0 FAIL with the `nautilus` suite counted"
2. "`qa/acceptance_results.json` is committed only from an owner's Windows full run (Step 7A.2 and this step), never
   from Linux (GOVERNANCE-R3-4)"
3. "frozen_guard (a), (b) and (d) pass there"
4. "run folders and the execution record are committed"
5. "`git diff --name-only` against the earliest HEAD that the pilot run records store (Step 7A item 5) lists only
   paths under `docs/nautilus_bridge/runs/`, the execution record, `README.md`, `qa/acceptance_results.json` and this
   spec, so nothing under `paper_live/`, `grokteam/`, `docs/asset_expansion/cards/` or the harness sources of
   `core/quant/gate_package.py:36-38` changed (GOVERNANCE-R3-1, GOVERNANCE-R3-7, GOVERNANCE-R4-2)"

10.4 (`spec:1693`): "This list goes verbatim into the execution record (map04 R23)." The list is the table at
`spec:1695-1706`; the claim labels follow at `spec:1708-1710`. The spec's Status adds (`spec:9-10`): "The ⑤-2 rows of
10.4 are written at Step 10."

10.5, the Step 10 bullet (`spec:1750-1753`): "The summaries of record are copied to
`docs/nautilus_bridge/runs/PP-<UTC>-<series>/provider_parity_summary.json`, and the execution record states their
sha256, the tool's commit and sha256, and each outcome. The rulings in `results/RULINGS.md` go into the execution
record and this spec's Status block (P-D9)."

10.5, Outputs (`spec:1736-1737`): "`detail.json` stays there; the owner decides what happens to it after Step 10
(P-D7)."

10.5, Gate (`spec:1745-1747`): "A ruling on a series that is not PASS either holds the pilot or lets it go ahead with
the disagreement noted in the execution record and in 10.4."

Step 7A item 5 (`spec:1612-1614`): "Before each pilot the owner runs `git pull --ff-only` again and repeats the two
7A.5 checks ... The pilot then anchors to that HEAD, and its run record stores it."

### 2.2 Order of work

1. Wait for three pushes by the owner: the pilot 1 folder, the pilot 2 folder, the Step 10
   `qa/acceptance_results.json`. Finish the readouts of Part 1.
2. Work in a scratch clone of the research branch that never checks out `docs/asset_expansion/cache/`. Never
   work in the owner's clone. The recipe, with the whole folder excluded:

   ```bash
   git clone --no-checkout <repository url or local path> "$SCRATCH/close"
   git -C "$SCRATCH/close" sparse-checkout set --no-cone '/*' '!/docs/asset_expansion/cache/'
   git -C "$SCRATCH/close" checkout claude/amazing-gauss-tdiguu
   test ! -e "$SCRATCH/close/docs/asset_expansion/cache" && echo "no cache folder" || echo "STOP: the cache folder is on disk"
   ```

   Go on only after `no cache folder`. Do not reuse the recipe of the execution record (`record:41-46`): it
   excludes four named files only, so the folder and any other file tracked in it stay on disk, and its check
   step is a `git ls-files` without a path, which rule 1 of 0.3 forbids. The recipe above was tried on
   2026-11-11 on a synthetic repository with the same folder layout (git 2.43.0): no cache folder on disk, the
   other folders present, `git status --porcelain` empty. It was not run on the real repository by this
   document's author (not verified there).
3. Run the diff check of 2.9 on the owner's last commit, before changing anything. Write its output down.
4. Copy the summaries of record (2.6). Edit the record (2.3 to 2.5), `README.md` (2.7) and the spec (2.8).
5. Run the pre-commit checklist (2.10) and the diff check again. Commit.
6. Push only as the owner has allowed. At Step 7A Claude asked for approval before each push (`spec:1527-1528`).
   Whether P2 covers the push itself is an open question (section 5).
7. Only after this does decision P3 apply: Claude merges main into the research branch, resolves the conflicts and
   runs the cache-free full test. After that merge the diff check of 2.9 lists main's files by design, so its
   result of record is the one from step 5.

### 2.3 Headings and placeholder lines to add to the execution record

File: `docs/superpowers/plans/2026-10-28-nautilus-execution-record.md` on the research branch. It is LF, 327 lines,
and ends with the section "2026-10-30 O8 follow-up applied" (`record:316-327`). The spec names another file,
`2026-10-<dd>-nautilus-bridge-execution-record.md`. The record's own ruling 18 left two ways open: "At Step 10 the
close-out record either extends this file under the spec's name or cites it. Cost if wrong: one rename."
(`record:94`). This skeleton takes neither literally: it extends the file and keeps its name, pending the owner's
answer to question 5 of section 5. If the owner chooses the rename, the record's path changes in three places of
this document: the filter of 2.9, item 3 of 2.10 and the ⑦-1 ledger row of 3.4. Append after line 327:

```markdown
## Step 10 close-out (<YYYY-MM-DD>)

Written by Claude, the session that the owner's ruling P2 of 2026-11-11 names (quoted in section 7 below).
<If another session writes this: its name, and the owner's sentence that allows it to commit here.> This section
and the ones after it are the close-out record that spec Step 10 names
`docs/superpowers/plans/2026-10-<dd>-nautilus-bridge-execution-record.md`. It extends this file and keeps this
file's name. Ruling 18 above left two ways open, a rename to the spec's name or a new file that cites this one;
<the owner's answer on the name, verbatim, or "the owner was not asked; the name is kept">.
Everything here was read from pushed files with git. Nothing was run on real data in the cloud.

### 1. Commits on this branch that this file does not name yet

In first-parent order (`git log --first-parent e089e59..HEAD`; `e089e59` of 2026-10-30 is the last commit that
changed this file), with two earlier commits that this file never names. "Author" is the author name git shows.

| What | Commit | Author | Files |
|---|---|---|---|
| Bonds screen patch (②-5/b); earlier than `e089e59`, not named above | `4709cf2` | Claude | `core/ficc/bonds.py`, `core/ficc/curves.py`, `core/ficc/data.py`, `core/ficc/insights.py`, `ui/bonds_page.py`, `ui/qcharts.py`, `tests/bonds_screen_acceptance.py`, `tests/run_all.py`, `README.md`, the rulings log, this file |
| O11 A2 registration tool; earlier than `e089e59`, not named above | `d7b175f` | xkg4real | `tools/nautilus/register_e1.py`, `tests/nautilus_registration_acceptance.py`, `.github/workflows/nautilus-registration.yml`, `docs/nautilus_bridge/O11_A2_REGISTRATION.md`, the runbook, the spec, the rulings log |
| Merge of pull request #21 | `0510719` | xkg4real | <from `git show --stat 0510719`> |
| Merge of main `7fc53e2` for Step 7A.1 (⑤-1/a) | `92cc00f` | Claude | <the conflicts and how each was resolved, from the merge message> |
| L1-15 encoding fixes; committed tables may carry the owner fields (⑤-1/a) | `85d2e51` | Claude | `tools/nautilus/register_e1.py` (inside `code_sha256`), `tests/nautilus_acceptance.py`, `tests/nautilus_registration_acceptance.py` |
| O11 A2 placed inside Step 7A.2; its receipt kept out of git (⑤-1/a) | `611c718` | Claude | `docs/nautilus_bridge/.gitignore`, `docs/nautilus_bridge/O11_A2_REGISTRATION.md`, the runbook, the spec |
| Merge of main `bb35b3b`, the start of the merge freeze (⑤-1/a) | `c95b3aa` | Claude | <the conflicts and how each was resolved, from the merge message> |
| Step 7A prep: review follow-ups (⑤-1/a) | `2c299c9` | Claude | `core/ficc/bonds.py`, `quantgen_desktop/bonds.py`, `quantgen_desktop/bonds_portfolio_narrative.py`, `tests/bond_funding_acceptance.py`, `tests/desktop_bonds_portfolio_language_acceptance.py`, `docs/nautilus_bridge/O11_A2_REGISTRATION.md`, the runbook, the spec |
| Step 7A.1 owner sign-off recorded verbatim (⑤-1/a) | `0bc9595` | Claude | the spec, the rulings log |
| Step 7A hand-off reports | `fe37e82`, `e3c61cb`, `9d8d9c6` | unknown (the owner's machine) | `docs/nautilus_bridge/handoff/win_amd64.json` |
| Step 7A re-entry fixes (⑤-1/b) | `e07da98` | Claude | `tests/macro_m8_pipeline.py`, `tests/nautilus_acceptance.py` |
| Step 7A records and both tables' owner fields | `563db54` | unknown (the owner's machine) | `docs/nautilus_bridge/egress/win_amd64.json`, both tables, `qa/acceptance_results.json`, `tools/nautilus/golden/modules_win_amd64.json` |
| Step 7A.4 review (⑤-1/c) | `83ee469` | Claude | the spec |
| Spec 10.5 (P-D3) | `8a8c247` | Claude | the spec |
| Pilot 1 run folder | `<sha>` | <author name; the owner> | `docs/nautilus_bridge/runs/<NB-...-d76d2d73>/` |
| Pilot 2 run folder | `<sha>` | <author name; the owner> | `docs/nautilus_bridge/runs/<NB-...-e2ec073c>/` |
| Step 10 Windows full run | `<sha>` | <author name; the owner> | `qa/acceptance_results.json` |
| <any re-anchor commit "nautilus: re-anchor" the owner made before a pilot> | `<sha>` | <author name; the owner> | none (an empty commit) |
| This close-out | `<sha>` | <who> | this file, the spec, `README.md`, `docs/nautilus_bridge/runs/PP-*/` |

### 2. Step 7A on Windows (2026-11-04), as recorded

- Full run at `563db54`: 844/964 passed, 0 failed, 120 not run; `nautilus` 57 PASS; `guard` 5 PASS.
- `code_sha256` `f995600b36c75523…`; `table_sha256` `d76d2d7301ffe92c…` (E1), `e2ec073c309cbfc7…` (C3).
- Timing from the hand-off report: engine import <1.94> s; 12 synthetic runs of 5,600 bars <35.1> s.
- O11 A2 registration: owner-reported, the receipt is private (spec Appendix B, 7A.4 review).
- <anything of the 7A.4 review that Step 10 must repeat>

### 3. Provider parity (5-2, spec 10.5)

- Tool: `tools/provider_parity/parity_check.py`, commit `5202482e3c24de871b8483608b8a03beb07abe1e`,
  sha256 `f2fe72cdee6344076fd6dfec8943259f44bc52445c66cdaf482a19e269770184`, fixed by the owner's ruling P1.
- Where it lives: `main` (PR #102, merge commit `9fc38175c79549b9cb2082193051832ab1d06f07`) and the run branch
  `claude/provider-parity-runs-20261111`.
  Spec 10.5 names `claude/provider-parity-5-2`; that branch holds the unfinished tool of 2026-11-05 and was not used.

| Series | Run of record (`run_id`) | Outcome | `tool.sha256` is the fixed one | sha256 of the summary | Copied to |
|---|---|---|---|---|---|
| SPY | `<PP-...-spy>` | <PASS/FAIL/WITHHELD> | <yes/no> | `<64 hex>` | `docs/nautilus_bridge/runs/<PP-...-spy>/provider_parity_summary.json` |
| DGS3MO | `<PP-...-rf>` | <...> | <...> | `<64 hex>` | `docs/nautilus_bridge/runs/<PP-...-rf>/provider_parity_summary.json` |
| BTC-USD | `<PP-...-btc>` | <...> | <...> | `<64 hex>` | `docs/nautilus_bridge/runs/<PP-...-btc>/provider_parity_summary.json` |

- Providers not compared, with the reason: <from `withheld_reasons`, or none>
- Warnings: <series, provider, check id, or none>
- Later runs and whether they count: <none | run_id and the ruling>
- Owner rulings from `results/RULINGS.md` (P-D9), verbatim, each with date (KST), series and `run_id`:
  - 2026-11-11, all series, before any run (P1): "1번으로 승인하겠노"
  - <later rulings, or "none">
- Gate: Step 8 started on <date> with SPY <outcome> and DGS3MO <outcome>; Step 9 on <date> with BTC-USD <outcome>.

### 4. Pilot 1 (Step 8): E1-SPY

- Run: `<bridge_run_id>`, `git.head` `<sha>`, started <UTC>, finished <UTC>, status `<status>`, exit <n>.
- Registration: 12 rows, <n> appended, <n> already present; E1 `n_raw` <before> to <after>.
- Children: 24, <n> valid; total <seconds> s.
- Parity: `hard_pass` <true/false>; worst corr <value> (bar 0.9999); worst abs dSR <value> (bar 0.01);
  P12 1x <corr, abs_dsr>, 2x <corr, abs_dsr>; P1 exemptions <n>; warnings <n>: <list>.
- Trial counts: <`len_grid` 12, `family_n_raw` <n>, `market_n_raw` <n>, `U` <n>, `n_trials` <n> | not computed:
  `parity.hard_pass` was false, so the run was not scored; `registration.n_raw_after` <n>, `market_n_raw` <n>>.
- Decisions: quantgen <decision | none>, nautilus <decision | none>; `agree.ok` <true/false | not computed>.
- Card: `<NB_E1_trend_spy.json | none>`, md5 `<32 hex>`; decision <...>; reason "<decision_reason>".
- Against spec 10.3 (expected INSUFFICIENT_DATA, else REJECT): <as expected | differs: ...>
- Withheld reasons, verbatim: <none | lines>
- Re-runs: <none | `--rerun-of <id>`, reason "<text>">. One paragraph like this one for each `NB-...-d76d2d73` folder.
- Card of record: `<bridge_run_id>`, the latest `CARD_WRITTEN` card that no later record supersedes (spec 5.3.5),
  or none.

### 5. Pilot 2 (Step 9): C3-BTCUSD

- Run: `<bridge_run_id>`, `git.head` `<sha>`, started <UTC>, finished <UTC>, status `<status>`, exit <n>.
- Registration: 5 rows, <n> appended; C3 `n_raw` <before> to <after>; `market_n_raw` <n>.
- Children: 10, <n> valid.
- Parity: `hard_pass` <...>; worst corr <value>; worst abs dSR <value>; P12 <...>; warnings <n>.
- Trial counts: <`len_grid` 5, `family_n_raw` <n>, `market_n_raw` <n>, `U` <n>, `n_trials` <n> | not computed, as
  in section 4>.
- Reference (G-08): drift <empty | fields>; `n_years_calendar` <n>, `n_years_whole` <n>.
- PBO, for information only (5 configurations): `pbo` <value>, `prob_loss_oos` <value>, `pbo_meaningful` false.
- Decisions, card and reason: <as section 4>
- Against spec 10.3 (expected PASS): <as expected | differs: ...>
- Re-runs and card of record: <as section 4>

### 6. The Windows full run of record (Step 10)

- Commit `<sha>` by the owner, <date>. <passed>/<total> passed, 0 failed, <n> not run.
- `nautilus`: <n> PASS, <n> NOT_RUN (<names>). `guard`: (a) <...>, (b) <...>, (c) <...>, (d) <...>, <...>.
- Against the 7A.2 run (`563db54`): added <rows>, removed <rows>, changed <rows>, each with its cause.
- `qa/acceptance_results.json` was written by no Claude commit; md5 before and after this close-out `<32 hex>`.

### 7. Rulings since ruling 19, each with its cost if wrong

<Before this table is final, read every source from where ruling 19 stops and give each owner ruling, and each
decision made on the owner's behalf, a row of its own: this branch's `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`
from its section "2026-10-28 ... ③-4 진행" to the end; main's `OWNER_RULINGS_LOG.md` from its section
"2026-11-04 ... Step 7A 동안 main 병합 동결" to the end; the spec's Status block and Appendix B;
`results/RULINGS.md` on the run branch. The rows below are the ones found on 2026-11-11.>

| # | Date | Ruling (verbatim where the owner's) | Source | Cost if wrong |
|---|---|---|---|---|
| <n> | 2026-10-29 | PR #4 conflicts: on the owner's instruction to decide from the two T-CAL-02 sessions, Claude took main's owner-signed calendars and withdrew this branch's PT-07 | this branch's rulings log, section "2026-10-29 ... PR #4 충돌 해결" | <...> |
| <n> | 2026-10-29 | "Bonds 패치 적용은 진행해주세요": the Bonds screen patch `4709cf2` landed on this branch | this branch's rulings log, section "2026-10-29 ... (가), X-1, ②-5" | <...> |
| <n> | 2026-10-29 | X-1 disclosure: "1. X-1 공개 여부 포함" | the same section; this file, "Data-access history entry (X-1)" | <...> |
| <n> | 2026-10-30 | O2 to O15, O8 optional review, O11 A2 | this branch's rulings log, the two sections of 2026-10-30; spec Status | <...> |
| <n> | 2026-11-03 and 2026-11-04 | Step 7A session: pre-check decisions, the fixes `85d2e51`, `611c718`, `2c299c9` and the re-entry fixes `e07da98` (Claude's decisions, each with what it changed) | this branch's rulings log, section "2026-11-04 ... (Step 7A 세션)"; the commits | <...> |
| <n> | 2026-11-04 | 7A.1 sign-off sentence | spec Status | <...> |
| <n> | 2026-11-04 | main merge freeze during Step 7A, and its lift (U4-나) | this branch's rulings log, section "2026-11-04 ... main 병합 동결"; main's log, section "main 병합 동결 해제 (U4-나)" | <...> |
| <n> | 2026-11-04 | "six.moves.winreg 판정 -> 승인" | spec Appendix B | <...> |
| <n> | 2026-11-04 | U5, P-D2 to P-D9 | spec Appendix B; main's log, section "소유자 결정표 2차 답" | <...> |
| <n> | 2026-11-04 | pilot anchor: "1. Continue with option(가)." | spec Appendix B | <...> |
| <n> | 2026-11-04 | H-D5: main is not merged into this branch from 7A.5 to the Step 10 merge | main's log, the same section | <...> |
| <n> | 2026-11-11 | P1: "1번으로 승인하겠노" | `results/RULINGS.md`; main's log, section "⑤-2 대조 도구의 버전 고정 위치 (P1)" | <...> |
| <n> | 2026-11-11 | P2, P3, P4: "전부승인" | main's log, section "결정 요청 P·A·B·C·D 묶음에 대한 답" | <...> |
| <n> | <date> | <5-2 rulings on a series that is not PASS> | `results/RULINGS.md` | <...> |
| <n> | <date> | <pilot re-run reasons, parity-failure rulings, rulings on a WITHHELD that the spec does not name as an end> | <...> | <...> |
| <n> | <date> | <rulings on the open questions of the pilot and closing documents: the record's file name, who updates the README counts, `--no-edit`, what the P3 merge holds> | <...> | <...> |
| <n> | <date> | <decisions Claude made on the owner's behalf during this close-out> | <...> | <...> |

Number the rows from 20 in date order once the list is complete.

### 8. Spec deviations

<the ten items carried from "Spec deviations to carry to Step 10 and the spec's next revision", then those found
since; see the list in the working document>

### 9. Data-access history (spec 10.4)

<the table of spec 10.4, verbatim, then the rows added at Step 10>

### 10. Step 10 Done-when, clause by clause

| Clause | Evidence |
|---|---|
| 0 FAIL with the `nautilus` suite counted | section 6 |
| `qa/acceptance_results.json` only from the owner's Windows full run | `git log --format='%h %an %s' <7A.3 parent>..HEAD -- qa/acceptance_results.json`: <commits; none authored by Claude> |
| frozen_guard (a), (b), (d) pass | section 6 |
| run folders and the execution record are committed | <folders>, this commit |
| `git diff --name-only <earliest pilot HEAD>` lists only the allowed paths | earliest HEAD `<sha>`; output: <paths>; paths outside the list: none |

### 11. Still open after Step 10

- `detail.json` of the provider parity runs: the owner decides (P-D7).
- The merge of `main` into this branch (owner ruling P3) and the owner's merge into `main`.
- <deferred findings of this file that still stand>
```

Facts already filled in above and their sources: the commits and their files (`git log --first-parent
e089e59..8a8c247` and `git show --name-only` of each commit on the research branch, with the cache folder excluded
from the listing; the owner's four Step 7A commits carry the author name `unknown`; `4709cf2` and `d7b175f` are
ancestors of `e089e59` and the record's text holds neither hash); the 7A.2 counts
(the file at `563db54`); the fingerprints (`spec:2194-2196` and section 0.1); the timing (the `timing` part of
`docs/nautilus_bridge/handoff/win_amd64.json`: `import_us` 1936529, `total_s` 35.138); the A2 note
(`spec:2140-2143`). The "cost if wrong" cells are for the closing session to write; no source gives them.

The record also keeps lines "for the Step 10 record" from the Linux key-set run (`record:148-153`): the L2-7, N6,
L2-12, N7 (i) and "80 perturbations" lines. Cite them next to the pilot results so a reader can compare the synthetic
margins with the real ones.

### 2.4 Carry-over: "Spec deviations to carry to Step 10 and the spec's next revision"

The section is `record:171-184`. It holds ten items, all "implemented as ruled" (`record:173`):

| # | Item | What it says | Line |
|---|---|---|---|
| 1 | T1 CI 7 | Rule A of spec 5.6 gives no hit when no order-call node is collected. Under the literal 5.6 a sandbox with no order call would get one A hit | `record:175` |
| 2 | T1 CI 9 | L1-17 tests `%VAR%` on Windows and `$VAR` on POSIX, because `os.path.expandvars` expands per platform (spec 8.3) | `record:176` |
| 3 | T2 CI 4 | C1 accepts `newline=""` for a csv writer that uses `lineterminator="\n"`; it writes the same LF bytes as spec 3.7's literal `newline="\n"` | `record:177` |
| 4 | T3 CI 1 | From Task 3 on, an exit 20 writes no file, and its last stderr line is `C-05: <reason>`. Two lines of 5.2.9's `main` change | `record:178` |
| 5 | T5 CI 1 | `parity.corr` counts two constant series that agree within 1e-12 as 1.0. P2's literal Pearson is undefined for a column that never trades when rf is 0 | `record:179` |
| 6 | T5 CI 3 | `--fingerprint` prints both digests. It exits 0 only for a table that validates against 6.6. An invalid table gets R-11 and exit 2 | `record:180` |
| 7 | T1-R4 | (a) `tests/nautilus_acceptance.py` is created at spec Step 3, although spec 5.8 names Steps 4 to 7. (b) `.env.example` gains a heading, three comment lines and the line, where spec 3.4 says "a heading and one line" | `record:181` |
| 8 | T2-m8 | `nautilus_tests()` calls `bridge_tests()` inside its `try`, so a collection failure becomes the single FAIL row `import` | `record:182` |
| 9 | T4-R5 (spec gap) | `_earlier_runs` (R-17) and `e1_parity_passed` read only `<out root>/*/run.json`, never a `run.final.<pid>.json` fallback. When a STATUS line names a fallback, the owner renames it to `run.json` before any re-run or pilot-2 run. Spec 5.3.5 should name the fallback for both readers | `record:183` |
| 10 | X8 (review T4-R7) | `--fingerprint`, `--timing` and `--handoff-report` moved from spec Step 6 to plan Task 5 (spec Step 7). So Task 4's commit holds all of 5.3 except these three modes | `record:184` |

Item 5 matters in the pilot readout: a column that never trades shows `P2.value` 1.0 by this rule, not by a
measured correlation. Item 9 matters before pilot 2 (checklist 1.2.1 step 2).

Deviations found since, for the closing session to confirm and add. Each is a difference between the spec's text and
what was done or ruled; none is decided here:

| Point | Spec text | What happened | Source |
|---|---|---|---|
| Tool branch | 10.5 names `claude/provider-parity-5-2` | the tool is on main and the run branch, by ruling P1; the research branch got no commit for it | `spec:1716`, `rulings-md:36-38` |
| Tool commit and sha256 | 10.5 leaves them out "until the tool exists" | fixed in `results/RULINGS.md` and the tool's README, not in the spec | `spec:1717-1718`, `pp-readme:19-38` |
| Execution record's file name | `2026-10-<dd>-nautilus-bridge-execution-record.md` | the existing file is extended | `spec:1633`, `record:94` |
| Who updates the README counts | "The owner ... updates the README counts and Total row" | P2 puts README in Claude's commit scope; the remaining-work table also gives Claude the count | `spec:1633`, `rw:135` |
| Step 9 command | no literal command in the Step 9 row | the owner's run sheet gives one from the runner's usage line | `spec:1632`, `runner:4` |
| "the manifest hashes" in the card | Step 8 Done-when lists them among the card's content | the card holds `row_md5s` and `ledger_hash_at_run`; the manifests are in `run.json` | `spec:1631`, `parity:332-339` |
| Merge of main before the owner's merge | the runbook's four merge lines assume no conflict | ruling P3: Claude merges main into the branch after the Step 10 checks | `runbook:211-221`, `log-main:758` |
| Re-run after a C-06-only WITHHELD | 5.3.5 and R-17: such a record may be re-run without `--rerun-of` | by the code as read, the reasons of that record also hold a `P13: column ...` line, so the all-C-06 test is false and a plain re-run is refused (not verified on a real run) | `spec:851-852`, `spec:1279`, `parity:29`, `parity:375-377`, `runner:253-254` |
| WITHHELD with parity passed | Steps 8 and 9 name "decision mismatch" and "reference drift" as valid ends | the runner can also end WITHHELD with parity passed for `benchmark test dropped`, G-03 and G-05; no document says whether that ends the step | `spec:1631-1632`, `parity:277`, `parity:422`, `parity:430`, `parity:514` |
| "the selection used" and "PBO for information only" in the card | Step 8 and Step 9 Done-when | the card holds a fixed selection sentence, `stats.chosen_last`, `tests.pbo` and `stats.prob_loss_oos`; the origins, the chosen columns and the predicates are in `run.json` | `spec:1631-1632`, `parity:33`, `parity:327-329`, `parity:348`, `parity:484-485` |
| Merge message editor | the runbook's merge line has no `-m` and no `--no-edit` | the owner's sheet shows the editor first (its step F9) and asks the owner whether `--no-edit` may be used | `runbook:218`, `sheet` section K item 8 |

### 2.5 Carry-over: "Data-access history entry (X-1)" and the rows of 10.4

The section is `record:290-302`. The owner ruled on 2026-10-29 that it goes into the record: "1. X-1 공개 여부 포함"
(`record:292`). It holds:

| Item | Content | Line |
|---|---|---|
| What happened | On 2026-10-26, before the plan, two cloud full-suite baseline runs ran in the real clone through the wrapper (`docs/audit/2026-10-27/artifacts/run_all_cloud_run1.log`, `run_all_cloud_run2.log`). Three existing `macro` tests opened protected caches while they ran | `record:294` |
| Test 1 | `macro/macro_m8_pipeline/test_dry_run_end_to_end_on_the_local_cache`: `yf_SPY.csv` | `record:295` |
| Test 2 | `macro/macro_m3_estimators/test_g_b5_02_spy_refdata_with_smoke_on_local_cache`: `yf_SPY.csv` | `record:296` |
| Test 3 | `macro/macro_tf_gov/test_cry1_study_runs_offline_end_to_end_on_the_local_caches`: `binance_BTCUSDT.csv` and `upbit_KRW-BTC.csv` | `record:297` |
| What Claude saw | Test names, PASS/FAIL statuses and counts only. No price value appears in either log. Run 1's dry-run failure detail is an empty `AssertionError` | `record:298` |
| Rule affected | Spec section 9, row 2 ("Claude reads no real BTC price and no SPY row on or after 2004-12-01"; "never opens or hashes ..."). The test processes opened the files | `record:299` |
| Since then | Every full run of the plan used a sparse clone where the four caches are skip-worktree and absent (X-1, T5-1): seven runs through ③-6 and three after the `main` merges. No bridge test opens a cache file | `record:300` |
| Pilot relevance | Pilot 1 (SPY) and pilot 2 (BTC-USD) are registered on these series. Claude's view was limited to statuses, so no design choice used their values. The entry exists so a reader of the pilot results can weigh that | `record:301` |
| Later event | 2026-10-29, about 05:50 UTC: while reviewing the Bonds patch, a Claude sub-agent's first recursive `grep` (`--include='*.csv'`) did not exclude `docs/asset_expansion/cache/`, so the four protected caches were opened by grep. Nothing matched, nothing was printed and nothing was hashed; later searches excluded the folder. No value from the files reached Claude | `record:302` |

The two self-reports behind it are in the research branch's rulings log (`rb-log:383`, `rb-log:496`).

The X-1 entry has six bullets and the 10.4 table has five columns. Two bullets, "Rule affected" (`record:299`)
and "Pilot relevance" (`record:301`), fit no column. So the skeleton's section 9 keeps the six X-1 bullets as text
beside the table; the table rows below carry only what the columns can hold.

Events after 2026-10-29. The closing record needs every later event in which a protected path was opened, listed,
searched or stat-ed by a Claude or GPT process, with date, what ran and what was seen. What is known on 2026-11-11,
and from where:

| Date | What ran | What was seen | Source |
|---|---|---|---|
| 2026-10-29 | one more full run in a cache-free copy at `4709cf2` (825/964 passed, 2 failed, 137 not run), after the X-1 sentence "seven runs through ③-6 and three after the `main` merges" was written | statuses and counts only; the four caches were absent from that copy | handoff ledger, row ②-5/b (`git show origin/handoff:LEDGER.md`, line 39) |
| 2026-11-11 | git commands (`status`, `add`, `commit`, `diff --check`) in scratch worktrees of the main clone that hold the full tree: the merge rehearsal worktree and the worktree in which these three documents were committed. Git stats every tracked file of a worktree, the protected folder included | nothing: no command named, listed, opened, hashed or searched the folder, and git prints no content | the fix helper's report on the rehearsal, repeated in the rehearsal record (`rehearsal`, section 4); `git -C <worktree> sparse-checkout list` answers "this worktree is not sparse" for both |
| 2026-11-11 | the Bonds test modules of the rehearsal, each behind a Python audit hook that refuses and counts any open or listing of the protected folder, of a file named `.env` or of the real `~/.nextgen` | the count was 0 in every run | `rehearsal`, section 4 |
| on or before 2026-11-11 04:49 KST; the exact dates are not written down | a helper (sub-worker) of the lead session walked the protected cache folder by name twice: once with a git index query and once with `find` | "파일을 열지는 않음": no file was opened. The owner was told, and answered "규칙은 꼭 지키자". Since then the helpers' instructions name the exclusion | the handoff document, `git show origin/handoff:CURRENT.md`, lines 107 and 156 at handoff commit `74744d4`; the sentence first appears in handoff commit `52eb246` |

The last row comes from the handoff document only. `log-main` (at `83046c1`) and `rb-log` hold no entry for it: a
search for 자진 보고, 위반 and the cache path finds only the entries of 2026-10-28 and 2026-10-29. The handoff
document is rewritten at every checkpoint, so its line may be gone at Step 10. Not verified: the dates of the two
walks, which listing each one printed, and whether any file name of the folder reached a model's context. The
session that holds the conversation writes these in before the closing commit and, with the owner's leave, into
the rulings log. A session without that conversation asks the owner; it does not leave the row out and does not
guess.

Every cloud full run made after 2026-10-29 gets its own line in the "Since then" text, with how the copy was made
(the whole-folder recipe of 2.2 or the four-file recipe of `record:41-46`) and its counts. That includes the lead
session's cache-free full test of the P3 merge.

Rows to add to the 10.4 table at Step 10 (the table itself, `spec:1695-1706`, goes in verbatim first). The columns
are When, Who, Data, What was computed, Ledger rows. These are proposals; every `<...>` is filled from a pushed
record, and nothing is claimed that a record does not show:

| When | Who | Data | What was computed | Ledger rows |
|---|---|---|---|---|
| 2026-10-26 | Claude, two cloud full-suite baseline runs (X-1) | `yf_SPY.csv`, `binance_BTCUSDT.csv`, `upbit_KRW-BTC.csv`, opened by three existing `macro` tests | test statuses and counts only; no price value in either log | none |
| 2026-10-29 | Claude sub-agent, one recursive grep (X-1, later event) | the four protected caches, opened by grep | nothing matched, printed or hashed | none |
| 2026-10-29 and later | Claude, cloud full runs after the X-1 entry | none of the protected caches: each run used a copy without them | test statuses and counts | none |
| <dates; on or before 2026-11-11> | a Claude helper session, two walks of the protected folder by name (a git index query, `find`) | the folder's file names; no file was opened | nothing computed; <what the listings showed, from the session that ran them> | none |
| 2026-11-11 | Claude, git commands in non-sparse scratch worktrees (merge rehearsal, these documents) | the protected folder's files, stat-ed by git, never opened by a command | nothing | none |
| 2026-11-04 | owner, Step 7A.2 on Windows | <the O11 A2 registration reads no price; the fixtures and timing are synthetic; the full suite ran with the caches present> | <registration only; suite statuses> | E1: 12 rows (owner-reported) |
| <date> | owner, provider parity tool (5-2) | the three pinned files on the pilot windows, and nine providers' series fetched on the same machine; the `kis` fetch reads, and may rewrite, the app's KIS access token `~/.nextgen/kis_token.json` and writes nothing else under `~/.nextgen` (`spec:1748-1749`) | only the kinds the tool's `COMPUTES` table names (10.5, exception to 3.9): calendar membership, differences between providers, range and gap checks of one series; no observation dated on or after 2027-01-01 (`spec:1723-1724`) | none |
| <date> | Claude | the three `summary.json` (counts, dates, booleans, decade buckets) | read only | none |
| <date> | owner, pilot 1 of record | `yf_SPY.csv` 2004-12-01 to 2026-09-25, `fred_DGS3MO.csv` | the 12 registered settings at 1x and 2x on both engines; parity; walk-forward; both scores | E1: <n appended, n already present> |
| <date> | Claude | the pushed `run.json` and card of pilot 1 (fills at the fill bars, statistics) | readout only | none |
| <date> | owner, pilot 2 of record | `yf_BTC-USD.csv`, whole file | the 5 registered settings at 10 and 20 bp on both engines; parity; reference comparison; both scores | C3: <n appended> |
| <date> | Claude | the pushed `run.json` and card of pilot 2 | readout only | none |
| <date> | owner, Step 10 Windows full suite | <the caches present on the owner's machine> | suite statuses | none |
| <date> | <5-2 ruling on a series that is not PASS, if any: the disagreement, as 10.5's Gate requires> | <...> | <...> | <...> |

### 2.6 The provider parity copies under `runs/`

```
docs/nautilus_bridge/runs/
  NB-<UTC>-d76d2d73/run.json, NB_E1_trend_spy.json              owner, Step 8
  NB-<UTC>-e2ec073c/run.json, NB_C3_crypto_trend_btcusd.json    owner, Step 9
  PP-<UTC>-spy/provider_parity_summary.json                     Claude, Step 10
  PP-<UTC>-rf/provider_parity_summary.json                      Claude, Step 10
  PP-<UTC>-btc/provider_parity_summary.json                     Claude, Step 10
```

- The folder name is the summary's `run_id`, `PP-<created_utc>-<series>` with series `spy`, `rf` or `btc`
  (`pc:1394-1396`, `spec:1751`).
- The file is a byte copy of `results/<run_id>/summary.json` on the run branch, under the new name
  `provider_parity_summary.json`:

```bash
RUNS=origin/claude/provider-parity-runs-20261111
mkdir -p docs/nautilus_bridge/runs/<run_id>
git show $RUNS:results/<run_id>/summary.json > docs/nautilus_bridge/runs/<run_id>/provider_parity_summary.json
git show $RUNS:results/<run_id>/summary.json | sha256sum
sha256sum docs/nautilus_bridge/runs/<run_id>/provider_parity_summary.json
```

  The two sha256 lines must be equal; that value goes into the record (section 3 of the skeleton).
- Copy the runs of record: per series the first run that ended PASS, FAIL or WITHHELD (`spec:1738-1739`). When a
  later run counts by an owner ruling, the spec does not say whether the earlier, the later or both are copied. That
  is an open question (section 5).
- The pilot-2 precondition and the re-run check read `*/run.json` and `NB-*-<8 hex>/run.json` (`runner:416`,
  `runner:246`). A `PP-*` folder holds no `run.json`, so it does not enter either. This follows from reading the two
  lines; it was not run.
- `docs/nautilus_bridge/.gitignore` ignores `runs/.locks/` and `runs/A2-E1-*` only, so the `PP-*` folders are
  tracked.

### 2.7 README lines

`README.md` is CRLF on all 995 lines at `8a8c247`, and `.gitattributes` is `* -text`, so git converts nothing. The
spec's rule: "README (C-4, CRLF, Edit tool only)" (`spec:1069`), and "at Step 10 the owner's Windows full run fills
that row and the Total row" (`spec:1071-1072`).

The two lines:

| Line | Now | Becomes |
|---|---|---|
| `rb-readme:937`, the `nautilus` row, last cell | `counted at the Windows run of record` | `<n> PASS` or `<n> PASS / <m> NOT_RUN`, from the pushed file (7A.2 value: 57 PASS) |
| `rb-readme:938`, the Total row, last cell | `743/864 passed, 0 failed, 121 not run (2026-10-23)` | `<passed>/<total> passed, 0 failed, <not run> not run (<YYYY-MM-DD>, Windows)` (7A.2 value: 844/964, 0, 120) |

Do not touch the block between `<!-- research-status:start -->` and `<!-- research-status:end -->`
(`rb-readme:890-906`). `tools/status/snapshot.py` writes it, together with `qa/research_status.json`
(`snapshot:139-146`), and that file is outside both P2 and the Step 10 path list. See section 3.2.

How to keep the line endings: change bytes inside the two lines only. Either the Edit tool with the exact cell text,
or this, which was tried on a scratch copy of the file on 2026-11-11 and left 995 CRLF lines with only lines 937 and
938 different:

```python
from pathlib import Path
p = Path("README.md")
data = p.read_bytes()
edits = [(b"| counted at the Windows run of record |\r\n", b"| <n> PASS |\r\n"),
         (b"| 743/864 passed, 0 failed, 121 not run (2026-10-23) |\r\n",
          b"| <passed>/<total> passed, 0 failed, <not run> not run (<YYYY-MM-DD>, Windows) |\r\n")]
for old, new in edits:
    assert data.count(old) == 1
    data = data.replace(old, new)
assert data.count(b"\r\n") == data.count(b"\n") and b"\r\r" not in data
p.write_bytes(data)
```

Then check: `git diff --numstat README.md` prints `2	2	README.md`, and
`git show :README.md | grep -c $'\r$'` equals the line count after `git add README.md`.

After the change the other rows of the table still show the 2026-10-23 numbers (`rb-readme:908` says so), there is
no `bonds` row although the pushed file has `bonds/` rows, and the rows no longer sum to the Total. The spec changes
only the two rows. Whether to change more is an open question (section 5).

### 2.8 Spec Status lines

The spec is LF. Add one bullet at the top of the Status block (before `spec:6`), in the form of the existing
bullets. Placeholders:

```markdown
- **<YYYY-MM-DD> Step 10 close-out (Claude, the session owner ruling P2 of 2026-11-11 names; <a different session
  writes its own name and the owner's sentence that allows it>).** The pilots and the Windows
  full run of record are in; the close-out record is in
  `docs/superpowers/plans/2026-10-28-nautilus-execution-record.md` ("Step 10 close-out").
  - Provider parity (10.5): runs of record `<PP-...-spy>` <outcome>, `<PP-...-rf>` <outcome>, `<PP-...-btc>`
    <outcome>, copied to `docs/nautilus_bridge/runs/PP-*/provider_parity_summary.json`. Tool commit
    `5202482e3c24de871b8483608b8a03beb07abe1e`, sha256
    `f2fe72cdee6344076fd6dfec8943259f44bc52445c66cdaf482a19e269770184`.
  - Owner ruling P1 (2026-11-11, verbatim): "1번으로 승인하겠노". The tool's commit and sha256 are fixed on main's
    side (`results/RULINGS.md`); the tool is on `main` and on the run branch
    `claude/provider-parity-runs-20261111`, not on `claude/provider-parity-5-2` as 10.5 says.
  - Rulings carried from `results/RULINGS.md` (P-D9), verbatim: <"..." (date KST, series, run_id) | none besides P1>.
  - Pilot 1 `<bridge_run_id>`: status <...>, `parity.hard_pass` <...>, decision <...>. Pilot 2 `<bridge_run_id>`:
    status <...>, `parity.hard_pass` <...>, decision <...>, reference drift <none | fields>.
  - Windows full run, commit `<sha>`: <passed>/<total> passed, 0 failed, <n> not run.
  - This commit changes only this spec, the execution record, `README.md` and `docs/nautilus_bridge/runs/PP-*/`.
    `qa/acceptance_results.json` is byte-identical. `code_sha256` stays `f995600b36c75523…`.
```

Also in the spec at Step 10:
- 10.4 (`spec:1695-1706`): append the rows of section 2.5. The Status bullet of 2026-11-04 says they are written at
  Step 10 (`spec:9-10`).
- Appendix B: one entry that quotes P1, P2, P3 and P4 verbatim (from `log-main:688`, `log-main:705-707` and
  `log-main:748`), in the form of the 2026-11-04 entry (`spec:2149-2203`), and lists what this commit changed.
- 10.5's Tool bullet (`spec:1716-1719`) still says the tool is not written and its commit is not fixed. P1 says the
  difference is carried into the Step 10 record and the research branch gets no extra commit for it
  (`rulings-md:37-38`). Whether the bullet's text is also rewritten at Step 10 is for the closing session to settle
  with the owner; the Status bullet above states the facts either way.

### 2.9 The final diff check

The earliest HEAD is the earliest `git.head` among the of-record run records (`runner:483-484`, `runner:1306`;
`spec:1633`, `spec:2197-2200`). If the owner pulled `8a8c247` before pilot 1 and made no other commit first, it is
`8a8c247`; read it from the records, do not assume it.

```bash
REF=origin/claude/amazing-gauss-tdiguu          # after the close-out commit: HEAD of the scratch clone
git ls-tree --name-only $REF docs/nautilus_bridge/runs/
git show $REF:docs/nautilus_bridge/runs/<NB folder>/run.json | python3 -B -I -c '
import json, sys
r = json.loads(sys.stdin.buffer.read().decode("utf-8"))
print(r["mode"], r["pilot"], r["status"], r["git"]["head"])'
git merge-base --is-ancestor <head A> <head B>; echo $?     # 0: A is the earlier one
BASE=<earliest head>
git diff --name-only $BASE $REF
git diff --name-only $BASE $REF | grep -v -E '^(docs/nautilus_bridge/runs/|docs/superpowers/plans/2026-10-28-nautilus-execution-record\.md$|README\.md$|qa/acceptance_results\.json$|docs/superpowers/specs/2026-10-26-nautilus-bridge-design\.md$)'
```

The last line must print nothing (grep then exits 1). Allowed paths (`spec:1633`): anything under
`docs/nautilus_bridge/runs/`; the execution record; `README.md`; `qa/acceptance_results.json`; the spec. The filter
was tried on 2026-11-11: from `83ee469` and from `563db54` to `8a8c247` it prints nothing; from `e07da98` it prints
five files, as it should: four of the 7A.3 evidence files (the egress record, both tables and
`tools/nautilus/golden/modules_win_amd64.json`) and the hand-off report of `9d8d9c6`. The fifth 7A.3 evidence
file, `qa/acceptance_results.json`, is on the allowed list and so is not printed.

The filter holds the execution record's present file name. If the owner chooses the rename of question 5, put the
new name into the filter, or the record itself is printed as a path outside the list.

The clause also names what must not have changed. Check each directly:

```bash
git diff --name-only $BASE $REF -- paper_live grokteam docs/asset_expansion/cards \
  core/quant/gate_stats.py core/quant/gate_ledger.py core/quant/cardp.py core/quant/cards.py \
  core/quant/card_lines.py core/quant/instruments.py core/quant/costed.py core/quant/validate.py \
  core/quant/strategies.py core/quant/gjr.py docs/macro_overlay_study.py
```

It must print nothing. The eleven files are `HARNESS_SOURCES` at `core/quant/gate_package.py:36-38` on the research
branch.

### 2.10 Pre-commit checklist (decision P2)

Before `git commit` on the research branch, every line must hold:

0. The session is allowed to commit there. The owner's answer "전부승인" and the P2 text are on `origin/main`:
   `git grep -n "전부승인" origin/main -- docs/nautilus_bridge/OWNER_RULINGS_LOG.md` prints two lines (697 and 748
   at `83046c1`). If it prints nothing, stop. P2 names the Claude session that asked the owner. A different
   session, GPT or Claude, stops here and asks the owner; his sentence goes into the rulings log and into the
   first paragraph of the skeleton before anything is committed.
1. The clone is the cache-free scratch clone of 2.2: `test ! -e docs/asset_expansion/cache && echo "no cache
   folder"` prints `no cache folder`. Only then run `git status --porcelain`; in a clone that holds the folder a
   `git status` without a path stats the folder's files (rule 1 of 0.3). It shows only these entries:
   ` M docs/superpowers/plans/2026-10-28-nautilus-execution-record.md`,
   ` M docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md`, ` M README.md`, and `??` entries under
   `docs/nautilus_bridge/runs/PP-`. Anything else is restored or removed before going on.
2. Each path is named in `git add`. Never `git add -A` or `git add .` (`spec:1597`, `runbook:188`).
3. `git diff --cached --name-only | grep -v -E '^(docs/nautilus_bridge/runs/PP-[0-9TZ]+-(spy|rf|btc)/provider_parity_summary\.json$|docs/superpowers/plans/2026-10-28-nautilus-execution-record\.md$|README\.md$|docs/superpowers/specs/2026-10-26-nautilus-bridge-design\.md$)'`
   prints nothing. The filter holds the execution record's present file name; change it if the owner chooses the
   rename of question 5.
4. `git diff --cached --name-only -- qa/acceptance_results.json` prints nothing, and
   `git show HEAD:qa/acceptance_results.json | md5sum` is the same before and after the commit. The commit message
   says the file is byte-identical (`spec:1528`).
5. No staged path is under `docs/nautilus_bridge/runs/NB-`: the pilot folders are the owner's.
6. No input of `code_sha256` changed since `563db54`:

```bash
git diff --name-only 563db54 HEAD -- tools/nautilus requirements-nautilus.txt docs/asset_expansion_study.py config.py \
  core/quant/gate_stats.py core/quant/gate_ledger.py core/quant/cardp.py core/quant/cards.py \
  core/quant/card_lines.py core/quant/instruments.py core/quant/costed.py core/quant/validate.py \
  core/quant/strategies.py core/quant/gjr.py docs/macro_overlay_study.py
```

   It must print nothing (the path list is `runner:183-190`). It printed nothing for `563db54..8a8c247` on
   2026-11-11. This git check stands in for the runner's `--fingerprint` mode, which imports `config` and so loads
   `.env` (`runner:1767`); do not run that mode in the cloud.
7. Neither table changed: `git diff --name-only 563db54 HEAD -- docs/nautilus_bridge/registration` prints nothing.
8. Each `provider_parity_summary.json` has the sha256 written in the record (2.6).
9. `README.md`: `git diff --cached --numstat -- README.md` prints `2	2	README.md`, and the staged file is still CRLF
   on every line (2.7). The record and the spec are still LF: `git show :<path> | grep -c $'\r$'` prints 0.
10. The diff check of 2.9 prints nothing outside the list when run on the staged tree's commit.
11. The commit message ends with the attribution lines the session is given, and names the roadmap ID (7-1).

## Part 3. After the owner's merge into main

The merge itself is the owner's (`runbook:211-221`): `git switch main`, `git pull --ff-only`,
`git merge --no-ff claude/amazing-gauss-tdiguu`, `git push origin main`. The branch ref is kept so every ledger
anchor stays reachable. Roadmap item 7-2 is done when that merge commit is on `origin/main`.

What follows is the cleanup on main, through the usual pull-request path. Whether parts of it are done earlier,
inside Claude's merge of main into the research branch (P3), is an open question (section 5).

### 3.1 Compliance baseline refresh

Command (from the repository root, in a clone without the protected caches):

```bash
python3 -B -m tools.compliance.check --refresh-baseline --documents $(seq 1 20) --reviewed-by "<who>" --review-note "<what>"
```

Why it is needed. The check compares the monitored source paths of the working tree with the baseline
`docs/compliance/source-review.json` (`check:26`, `check:460-479`). The merge adds monitored paths that main's
baseline does not list. Any added or deleted path is taken to affect all 20 documents (`check:478-479`), and each
document's digest includes the list of monitored paths (`check:281-282`), so all 20 show "related source changed
since review" and `--check` exits 1 (`check:488-497`, `check:593`). The Compliance workflow runs `--check` on every
push to main and on every pull request (`.github/workflows/compliance-review.yml:3-6`, `:55` on main). So after the
owner's push the workflow fails on main, and on every later pull request, until the baseline is refreshed.

Which paths. Applying the rule `monitored()` (`check:93-120`) to the names that are on the research branch and not
on main gives 13 paths that the merge adds: `tools/nautilus/__init__.py`, `egress_probe.py`, `launch.py`,
`parity.py`, `register_e1.py`, `runner.py`, `sandbox.py`; `tests/nautilus_acceptance.py`,
`tests/nautilus_registration_acceptance.py`, `tests/nautilus_stub_child.py`, `tests/bonds_screen_acceptance.py`;
`requirements-nautilus.txt`; `.github/workflows/nautilus-registration.yml`. `git grep` finds no line naming
`tools/nautilus`, `tests/nautilus` or `requirements-nautilus` in main's baseline. The merge rehearsal then ran
`--check` on a merged tree (research `8a8c247` with main `9fc3817`): exit 1, all 20 documents need review, 679
monitored files against a baseline of 666, the same 13 files new to the baseline, and 13 more files whose content
differs from the baseline (`rehearsal`, section 4). main's baseline changed again at `83046c1`, so those counts
are not verified for the main of Step 10. An earlier estimate in the session's notes said 18 files plus the
requirements file; it is superseded by the run.

What the options need (`check:428-457`): `--reviewed-by` and `--review-note` must be real text, the note at least
12 characters, and neither may contain a placeholder word such as TODO, TBD, UNKNOWN, UNVERIFIED, PENDING, EXAMPLE,
PLACEHOLDER, NOT_CONFIGURED, 미정, "확인 필요" or "입력 필요" (`check:39`, `check:314-315`, `check:429-430`).
`--documents` takes ids 1 to 20 (`check:436-437`). The command then runs the check and prints
`{"consistency_status": "PASS", ...}` with exit 0 when the baseline is consistent (`check:584-593`).

A refresh records that a named person reviewed the 20 compliance documents against the changed sources. Read what
the new sources mean for the documents before running it; the command does not review anything.

The tool walks the working tree, but it prunes `docs/` to `docs/product` and `docs/compliance` and skips folders
named `cache` outside the source roots (`check:130-146`, `check:35`), so by its code it does not enter
`docs/asset_expansion/cache/`. Run it in a cache-free clone all the same.

Verify with `python3 -B -m tools.compliance.check --check` (exit 0) and
`python3 -B -m unittest tests.compliance_acceptance tests.compliance_export_acceptance -v`
(`compliance-review.yml:52`).

### 3.2 `qa/research_status.json`

The generator, found with `git grep -n "research_status" origin/main -- tools tests qa .github README.md`, is
`tools/status/snapshot.py` (`snapshot:24`). Commands (`snapshot:3-4`, `snapshot:129-133`):

```bash
python3 -B -m tools.status.snapshot --write     # rewrites qa/research_status.json and README's status block
python3 -B -m tools.status.snapshot --check     # prints {"status": "consistent", ...} and exits 0
```

It reads only `README.md`, `qa/acceptance_results.json` and `core/calendars/data/MANIFEST.yaml` (`snapshot:23`). It
needs the `yaml` package (`snapshot:18`). `--write` keeps README's CRLF (`snapshot:140-144`).

Why it is needed. The snapshot stores the sha256 of `qa/acceptance_results.json` and of README outside the status
block, and the PASS, FAIL and NOT_RUN counts (`snapshot:77-86`). `--check` fails when any of them differs
(`snapshot:117-126`). After the merge main carries the Windows results file and the changed README, so the snapshot
on main is stale until `--write` runs. On main `--check` passes (run on 2026-11-11 at `96cca1f`: "consistent",
749/870; the generator and its three inputs are unchanged from `96cca1f` to `83046c1`, `git diff --quiet` exit 0).
On the research branch the snapshot has been stale since `563db54`: it records sha256 `89cd556c…` for a results
file whose sha256 is `2540b8ae…` (computed 2026-11-11); the rehearsal confirmed that `--check` fails on the four
files of `8a8c247` and passes after `--write` on the merged tree, 844/964 (`rehearsal`, section 2.2 and 4).

Where it bites: the runtime workflow runs `--check` on pull requests that touch its path filter
(`.github/workflows/runtime-smoke.yml:5-6`, `:92` on main). It is not triggered by a push to main.

After `--write`, the README status block's "Code tests" line shows the new counts (`snapshot:107`). The block notes
that the run time and commit are "not supplied by source"; do not add them by hand.

### 3.3 README test counts on main

After the merge, README's `nautilus` row and Total row carry the Step 10 Windows numbers. Those numbers describe the
research branch's tree at the Step 10 run. The merged tree has main's tests as well, so its true counts are neither
main's nor the research branch's. Main's README today has the same Total row as the research branch,
`743/864 passed, 0 failed, 121 not run (2026-10-23)` (main `README.md:957`), and no `nautilus` or `bonds` row (a
search of main's README for lines starting `| nautilus ` or `| bonds ` finds none). `qa/acceptance_results.json` on
main after the merge is the Step 10 file, for the same reason.

What to do is not written anywhere. The candidates are: leave the Step 10 numbers with their date, or have the
owner run the Windows full suite once more on merged main and commit that file. Open question (section 5).

The provider parity suite is not registered in `tests/run_all.py` and has no README row, on purpose, "until the
owner says otherwise" (`pp-readme:235-236`). That stays as it is through the merge.

### 3.4 Handoff ledger rows

Format: `python3 tools/handoff/push_handoff.py <file> --done "<id> | <what> | <files> | <commit> | <check and
result>"`. Write the ID plainly. Publish each when its item is finished, move the ID from `next_ids` to `done_ids`,
and never list a ledger ID in `next_ids`. No secret, no price and no host name in a row. The ledger had no row for
these four IDs on 2026-11-11; look again before publishing.

| ID | Finished when | Row to publish |
|---|---|---|
| ⑥-1 | Step 8's Done-when holds (`spec:1631`) and the readout was reported to the owner (`rw:133`) | `--done "⑥-1 \| 파일럿 1(SPY, E1 12개 설정) 소유자 실행과 Claude 판독: 상태 <status>, hard_pass <true/false>, 카드 판정 <decision 또는 없음> \| docs/nautilus_bridge/runs/<NB-...-d76d2d73>/ \| <소유자 커밋> \| run.json 판독: 자식 <n>/24개 유효, 패리티 최저 상관 <값>, Sharpe 차이 최대 <값>, 시행 수 <n 또는 계산 안 됨>"` |
| ⑥-2 | Step 9's Done-when holds (`spec:1632`) and the readout was reported (`rw:134`) | `--done "⑥-2 \| 파일럿 2(BTC-USD, C3 5개 설정) 소유자 실행과 Claude 판독: 상태 <status>, hard_pass <true/false>, 카드 판정 <decision 또는 없음>, reference drift <없음/항목> \| docs/nautilus_bridge/runs/<NB-...-e2ec073c>/ \| <소유자 커밋> \| run.json 판독: 자식 <n>/10개 유효, 패리티 최저 상관 <값>, 시행 수 <n 또는 계산 안 됨>"` |
| ⑦-1 | all five clauses of Step 10's Done-when hold (2.1) and the close-out commit is on the research branch (`rw:135`) | `--done "⑦-1 \| Step 10 마감: Windows 전체 검사 <통과>/<전체> 실패 0, 마감 기록, 스펙 Status와 10.4, README 두 줄, 공급사 대조 요약 사본 3개 \| docs/superpowers/plans/2026-10-28-nautilus-execution-record.md, docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md, README.md, docs/nautilus_bridge/runs/PP-*/ \| <소유자의 전체 검사 커밋>, <마감 커밋> \| git diff --name-only <가장 이른 파일럿 HEAD>: 허용 경로만, qa 파일 불변, code_sha256 f995600b 불변"` |
| ⑦-2 | the owner's merge commit is on `origin/main` and the branch ref still exists (`rw:117`, `runbook:211-221`) | `--done "⑦-2 \| 연구 브랜치 claude/amazing-gauss-tdiguu를 main에 병합(소유자의 --no-ff 병합 커밋), 병합 전 Claude가 main을 연구 브랜치에 합쳐 충돌 해결(P3) \| <충돌을 푼 파일 목록 요약> \| <P3 병합 커밋>, <소유자 병합 커밋> \| 캐시 없는 전체 검사 <통과>/<전체> 실패 <n>, 병합 뒤 compliance --check PASS, status snapshot --check 일치"` |

In the actual command the cell separator is a plain `|`; the backslashes above are only table escaping. The
cleanup of 3.1 and 3.2 belongs in the 7-2 row's check cell only if it was done; otherwise give it its own part ID,
for example `⑦-2/a`. A ledger row cannot be rewritten once published, so fill every `<...>` from the record
itself: the number of valid children is the count of `children` entries with an empty `invalid`, not 24 or 10 by
default. The ⑦-1 row holds the execution record's present path; change it if the owner chooses the rename of
question 5.

### 3.5 Open owner decision P-D7: `detail.json`

The owner's ruling of 2026-11-04: "P-D7 = (가) 6.2 목록 승인. detail.json 처리는 Step 10 뒤에 정함 [권고]"
(`log-main:520`). The spec: "`detail.json` stays there; the owner decides what happens to it after Step 10"
(`spec:1736-1737`). The owner's guide tells him to keep the whole `%LOCALAPPDATA%\quantgen\provider_parity` folder
until then (`guide:346`). The file holds the per-date values and differences (`pp-readme:154-155`), so it never goes
into a repository or a chat. No document lists the choices. Ask after Step 10:

> 공급사 대조 때 PC에 남겨 둔 detail.json과 수신 폴더를 어떻게 할지 정해 주십시오. detail.json은 날짜별 값과 차이가 든
> 파일이라 저장소나 채팅으로 내보내지 않습니다. 지금은 `%LOCALAPPDATA%\quantgen\provider_parity` 폴더에 그대로 있습니다.
> 예를 들면 그대로 보관, 삭제, PC 안의 다른 폴더로 옮겨 보관이 있습니다. 2026-11-04 결정(P-D7)에서 Step 10 뒤에 정하기로
> 하신 항목입니다.

### 3.6 Other things the merge brings to main

- A new workflow, `.github/workflows/nautilus-registration.yml`. It runs on every pull request that touches
  `docs/nautilus_bridge/*.md`, the spec, the execution record, `tools/nautilus/register_e1.py` or its test
  (lines 13-20 of that file on the research branch), on Ubuntu and Windows. The rulings log is one of those
  `docs/nautilus_bridge/*.md` files, so pull requests that record rulings will start this job. Read from the file;
  not run.
- `tests/run_all.py` on main gains the `nautilus` and `bonds` suites (`run_all:46`, `run_all:95`, `run_all:102`).
- The amended T-RO-01 test of spec 5.6 (`tests/macro_m0_harness.py`) arrives on main with the merge. The sign-off
  sentence of 2026-11-04 released that exemption outside the branch (`spec:17-20`).
- Decision P4: the order module, the R3 Lab screen wiring and the LA-07 harness change start only after this merge.
- The merge itself was rehearsed on 2026-11-11 (`rehearsal`): five conflicts, of which the Bonds page needs
  hand work, three follow-up patches to two tests and one message file, and seven display choices for the owner.
  Read that record before the P3 merge and repeat the rehearsal on the main of that day.

## 4. Not verified

- No pilot has run. Every `run.json` and card field name comes from the code that writes them
  (`runner`, `parity`, `validate`). No real run record exists yet, so none was read. Appendix B's script ran only on
  a hand-made stand-in with those field names.
- No provider parity summary exists. The field names were confirmed on three synthetic summaries built with the
  tool's own functions. Appendix A's script ran only on those.
- The owner's machine: whether `8a8c247` was pulled, the clean tree, the firewall rule, the E1 and C3 row counts.
  The E1 and C3 counts are owner-reported (`spec:2140-2143`). The trial counts 24 and 36 for pilot 1 are derived
  from 12 rows, not seen.
- Every main-side fact is for `origin/main` `83046c1`. main moved twice while these documents were written. Check
  the main of the day before relying on a line number, a count or the rehearsal.
- The C-06 re-run rule (1.2.3): read from `parity:375-377` and `runner:253-254` and tried on a stand-in of the
  copied expressions, not on the real runner.
- The sparse recipe of 2.2: tried on a synthetic repository with the same folder layout, not on the real one.
- The PowerShell line that replaces a stale `run.json` with its fallback: none was written or tried.
- The files of the merge commits `0510719`, `92cc00f` and `c95b3aa`: left as placeholders in the skeleton, not
  read here.
- That the Compliance workflow fails on GitHub after the owner's merge: the same check command exits 1 on the
  local rehearsal merge (`rehearsal`, section 4); GitHub itself was not observed, and the baseline changed at
  `83046c1`.
- That the first full suite after the pilots still shows 0 FAIL.
- The two walks of the protected folder by a helper: recorded only in the handoff document; dates and details are
  not written down (2.5).
- The bounds on `first` for DGS3MO fetches (2004-11-05) and the expected `n_years` values of pilot 2 (11 and 9): the
  guide's and the spec's statements, not re-derived.
- GitHub state: branch protection on main, CI results. No network call was made for this document.
- Nothing here was run on Windows or in PowerShell.

## 5. Open questions for the owner (not decided here)

> Decided on 2026-11-11 (KST). The owner answered "전부승인합노." to a decision table that holds these 19 questions,
> K section K and the rehearsal's choices: `docs/product/DECISIONS_PILOT_CLOSE_MERGE_2026-11-11.md`. Each row of the
> table names its question here as `R<n>`. What each answer decides is recorded in `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`,
> section "2026-11-11, Claude Code 채팅: 파일럿·마감·병합 결정 27건에 대한 답". Question 2 was decided as "not now: put the
> choice with the cause when it arises". The questions below are left as they were asked.

1. Pilot 1 ends with `parity.hard_pass` false. What then: find the cause and re-run (a code fix means Windows
   re-validation and a new `owner_confirmed`), or close without pilot 2? No document gives the procedure.
2. May Step 10 close, and the merge go ahead, when pilot 2 did not run? Step 10's Done-when says "run folders ... are
   committed".
3. Does ruling P2 cover pushing Claude's close-out commit to the research branch, or is each push approved first, as
   at Step 7A?
4. README at Step 10: only the `nautilus` row and the Total row, as the spec says, or also the other rows and a new
   `bonds` row? With only two rows changed the table no longer sums to the Total.
5. The close-out record: extend the existing file and keep its name (this skeleton), or rename it to the spec's
   name?
6. What Claude's merge of main into the research branch (P3) holds besides the conflict resolutions: the three
   follow-up patches S1 to S3 (two tests and one message file), the regenerated status snapshot with its README
   line, the compliance baseline refresh, and the seven display choices of the Bonds page (`rehearsal`, sections
   2.4 and 5). Inside the merge, main is consistent the moment the owner merges, and
   `docs/compliance/source-review.json`, `qa/research_status.json` and test files enter a research-branch commit,
   which P2's four kinds of file do not name. In a pull request on main afterwards, main's Compliance check fails
   in between.
7. After Claude's merge of main into the research branch: is one more Windows full run wanted, and which run do
   README's counts on main describe?
8. A provider parity series that is WITHHELD because a provider could not be fetched: may a later run count?
9. When a later provider parity run counts by ruling, which summary is copied under `runs/` at Step 10: the first,
   the later, or both?
10. `detail.json` and the fetch folders on the owner's machine (P-D7): keep, delete or move.
11. Does the sign-off sentence of 2026-11-04 cover the branch after main has been merged into it under P3?
12. Is the run folder of a run that ended `REFUSED_REGISTRATION`, `ERROR` or `ABORTED` committed too? Step 10 says
    only "run folders ... are committed". The answer also sets which record holds the earliest HEAD for the diff
    check of 2.9.
13. Events after 2026-10-29 in which a protected path was opened, searched or walked: which ones go into the
    data-access history of the close-out record, and with what wording? The two walks by a helper are recorded
    only in the handoff document (2.5).
14. A pilot ends WITHHELD with `parity.hard_pass` true for a reason the spec does not name as an end:
    `benchmark test dropped`, G-03 or G-05. Does that end the step, or is a re-run with a reason sentence wanted?
15. May the owner's merge line carry `--no-edit`, so that no editor opens? It differs from the runbook's literal
    line by that one word (`sheet`, section K item 8).
16. Who updates the README counts at Step 10: the owner, as the spec's Step 10 row says, or Claude, as the
    remaining-work table says (`rw:135`) and P2's file list allows?
17. After pilot 2, does the owner wait for Claude's readout before the Windows full run? The owner's sheet says
    wait; the spec gives only the order.
18. Does P2 extend to a successor session (GPT or another Claude), or does each successor ask before it commits
    on the research branch?
19. If a pilot ends WITHHELD only because a child died or timed out (C-06): is a re-run with a reason sentence
    acceptable? The spec promises a plain re-run; the code as read asks for the reason.

Questions 1, 7, 11, 12, 15, 16 and 17 are also in the owner's sheet (its section K, items 1, 2, 3, 4, 8, 5 and 7);
its item 6 is question 3, its item 9 is question 14 and its item 10 is question 6.

## Appendix A. `read_summary.py`

Reads one provider parity `summary.json` from stdin. Read only. Tried on synthetic summaries only.

```python
"""Read one provider parity summary.json from stdin and print the readout values. Read only."""
import hashlib
import json
import sys

FIXED_TOOL_SHA256 = "f2fe72cdee6344076fd6dfec8943259f44bc52445c66cdaf482a19e269770184"
PINNED = {"spy": ("yf_SPY.csv", "d2164597d576e1b2fcadde063065811d", "2004-12-01", "2026-09-25"),
          "rf": ("fred_DGS3MO.csv", "661722143f24930a29b58c535d227c1b", "2004-12-01", "2026-09-25"),
          "btc": ("yf_BTC-USD.csv", "bc76f530ff24ab445367fe826150bc10", "2014-09-17", "2026-09-25")}

raw = sys.stdin.buffer.read()
s = json.loads(raw.decode("utf-8"))
series = s["series"]
want = PINNED[series]
print("file sha256", hashlib.sha256(raw).hexdigest())
print("schema", s["schema"], "| run_id", s["run_id"], "| run_id form ok", s["run_id"] == f"PP-{s['created_utc']}-{series}")
print("tool sha256 is the fixed one:", s["tool"]["sha256"] == FIXED_TOOL_SHA256)
print("pinned", s["pinned"], "| file and md5 as the table's:", (s["pinned"]["file"], s["pinned"]["md5"]) == want[:2])
print("window", s["window"], "| as the table's:", (s["window"]["start"], s["window"]["end"]) == want[2:])
print("OUTCOME", series, s["outcome"], "| n_a_outside_evidence_spans", s["n_a_outside_evidence_spans"])
print("withheld_reasons", s["withheld_reasons"])
for c in s["integrity"]:
    print("integrity", c["id"], c["kind"], c["outcome"], {k: v for k, v in c.items() if k not in ("id", "kind", "outcome")})
named = {p["provider"] for p in s["pairs"]} | {r.split(" not compared: ")[0] for r in s["withheld_reasons"] if " not compared: " in r}
print("required providers not accounted for:", sorted(p for p, v in s["providers"].items() if v["required"] and p not in named))
for p in s["pairs"]:
    print("pair", p["provider"], p["role"], p["convention"], "| outcome", p["outcome"], "| has_fetch_record", p["has_fetch_record"])
    for c in p["checks"]:
        print("   ", c["id"], c["kind"], c["outcome"], {k: v for k, v in c.items() if k not in ("id", "kind", "outcome")})
```

## Appendix B. `read_run.py`

Reads one pilot `run.json` from stdin. Read only; it prints no fill row. Tried on a hand-made stand-in only.

```python
"""Read one pilot run record (run.json) from stdin and print the readout values. Read only; prints no fill row."""
import json
import sys

rec = json.loads(sys.stdin.buffer.read().decode("utf-8"))
g = lambda d, *ks: None if d is None else (g(d.get(ks[0]), *ks[1:]) if ks else d)  # noqa: E731

print("schema", rec.get("schema"), "| mode", rec.get("mode"), "| pilot", rec.get("pilot"), "| stub_child", rec.get("stub_child"))
print("bridge_run_id", rec.get("bridge_run_id"))
print("status", rec.get("status"), "| error", g(rec, "error", "message"))
print("earlier_runs", rec.get("earlier_runs"), "| supersedes", rec.get("supersedes"), "| rerun_reason", rec.get("rerun_reason"))
print("times", rec.get("times"))
print("git.head", g(rec, "git", "head"), "| anchor", g(rec, "git", "anchor"), "| clean", g(rec, "git", "clean"),
      "| offending", g(rec, "git", "offending"), "| anchor_problem", g(rec, "git", "anchor_problem"))
print("table_sha256", g(rec, "table", "table_sha256"))
print("code_sha256 ", g(rec, "table", "code_sha256"))
print("owner_confirmed", g(rec, "table", "table", "owner_confirmed"))
d = rec.get("data") or {}
print("data", {k: d.get(k) for k in ("prices_md5", "rf_md5", "start", "end", "sessions", "rounding_changed")})
print("provenance.p0a", g(rec, "provenance", "p0a"), "| p0b", g(rec, "provenance", "p0b"))
print("costs", rec.get("costs"))
print("egress.probe.blocked", g(rec, "egress", "probe", "blocked"), "| layer", g(rec, "egress", "layer"))
reg = rec.get("registration") or {}
rows = reg.get("rows") or []
print("registration", {k: reg.get(k) for k in ("family_id", "n_raw_before", "n_raw_after", "market_n_raw")},
      "| rows", len(rows), "| appended", sum(1 for r in rows if r.get("appended")),
      "| hash_before == hash_after", reg.get("hash_before") == reg.get("hash_after"))
kids = rec.get("children") or []
echo = [g(c, "manifest", "input", "ledger_hash_after_registration") == reg.get("hash_after") for c in kids]
print("children", len(kids), "| returncodes", sorted({str(c.get("returncode")) for c in kids}),
      "| invalid", sum(1 for c in kids if c.get("invalid")), "| timed_out", sum(1 for c in kids if c.get("timed_out")),
      "| ledger-hash echo ok", sum(echo), "of", len(echo), "| seconds", round(sum(c.get("seconds") or 0 for c in kids), 1))
print("census tags", sorted(rec.get("census") or {}))
p = rec.get("parity") or {}
print("parity.hard_pass", p.get("hard_pass"), "| bars", p.get("bars"), "| owner_bars", p.get("owner_bars"))
legs = [x for x in p.get("legs") or [] if g(x, "P13", "pass")]
print("legs", len(p.get("legs") or []), "| P13 pass", len(legs))
if legs:
    print("worst P2 corr", min(x["P2"]["value"] for x in legs), "| worst P3 abs dSR", max(x["P3"]["value"] for x in legs),
          "| max P10 gap", max(x["P10"]["max_gap"] for x in legs))
    for k in ("P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10"):
        bad = [(x["col"], x["stress"]) for x in legs if not x[k]["pass"]]
        print(" ", k, "not passed at (col, stress):", bad)
    print("  P1 exempt decisions:", [(x["col"], x["stress"], x["P1"]["exempt"]) for x in legs if x["P1"]["exempt"]])
print("P0b", p.get("P0b"))
print("P12", p.get("P12"))
p11 = p.get("P11") or []
print("P11 origins", len(p11), "| selection differs at", [x["origin"] for x in p11 if not x["match"]])
print("parity.failed", len(p.get("failed") or []))
for line in p.get("failed") or []:
    print("  FAILED", line[:300])
print("parity.warnings", len(p.get("warnings") or []))
for line in p.get("warnings") or []:
    print("  WARNING", line[:300])
gate = rec.get("gate") or {}
print("gate.trial_counts", gate.get("trial_counts"))
for side in ("quantgen", "nautilus"):
    s = gate.get(side) or {}
    print(f"gate.{side}", s.get("decision"), "|", s.get("reason"), "| revise_target", s.get("revise_target"))
    print("   predicates false:", sorted(k for k, v in (s.get("predicates") or {}).items() if not v))
print("gate.agree", gate.get("agree"), "| gate.error", gate.get("error"))
print("gate.reference", gate.get("reference"))
sel = gate.get("selection") or {}
print("gate.selection origins", len(sel.get("origins") or []), "| chosen", sel.get("chosen"), "| note", sel.get("note"))
print("withheld_reasons", len(rec.get("withheld_reasons") or []))
for line in rec.get("withheld_reasons") or []:
    print("  REASON", str(line)[:300])
print("card", rec.get("card"))
print("cleanup_leftovers", rec.get("cleanup_leftovers"), "| record_write_failures", rec.get("record_write_failures"))
```
