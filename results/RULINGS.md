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
- First fixed version, commit: `5202482e3c24de871b8483608b8a03beb07abe1e`
- First fixed version, sha256 of `tools/provider_parity/parity_check.py`: `f2fe72cdee6344076fd6dfec8943259f44bc52445c66cdaf482a19e269770184`
- The first fixed version is the tool of the three runs of record of 2026-11-11 (next entry) and stays their
  version. For every later run the fixed version is the second one, under the SPY entry of 2026-11-11 below.
- 2026-11-11 (KST), before PR #102 merged: the two values above replace those first recorded here (commit `49a3a67`,
  sha256 `d651795e...`), because a code review of PR #102 found faults in the tool that could have cost the owner a
  run of record (F1: the H.15 fetch could read another maturity's column and end the DGS3MO run FAIL; F2: a file
  fetched for other dates than the table's was compared and could end a series WITHHELD) and the tool was changed to
  fix them; no run existed.
- Run branch the owner clones and pushes summaries to: `claude/provider-parity-runs-20261111` (cut from `main`; it contains the fixed commit).
- The research branch gets no commit for this. The spec's branch name (`claude/provider-parity-5-2`) differs from the
  above; Step 10 records the difference in the execution record.
- No run of record existed when this ruling was given. The first runs are the next entry.

## 2026-11-11 (KST), all series: the first runs, each its series' run of record

The owner ran the tool on his PC on 2026-11-11 with the first fixed version and pushed the three summaries to the run
branch (`claude/provider-parity-runs-20261111`, commit `0b397f7`). Each `tool.sha256` is the first fixed version's.
Each run is its series' run of record and stays. Read from the pushed `summary.json` files only:

| Series | `run_id` | Outcome | What the summary says |
| --- | --- | --- | --- |
| SPY | `PP-20261111T051909Z-spy` | WITHHELD | `fmp` (independent): first date 2006-11-15, 494 of the table's 5,489 sessions lie before its span (allowed 5), so the pair is WITHHELD on coverage. `kis` (cross): first date 2007-08-21, 684 sessions before its span, WITHHELD on coverage. Neither pair's return comparison ran. `yahoo_now` (vintage): PASS on 5,489 common days. Reason: `no independent or cross pair was evaluated in full`. |
| DGS3MO | `PP-20261111T075307Z-rf` | PASS | `treasury` (independent): 5,475 common values, 0 beyond tolerance. `fred_now` (vintage): PASS. `h15` (optional) not compared: `fetch_failed`. |
| BTC-USD | `PP-20261111T075328Z-btc` | FAIL | `coinbase` (independent): 43 days with a log-return difference above 0.02 (allowed 20), and the late segment outside the level band; calendar and day boundary PASS. `bitstamp` (independent, optional): 47 such days (allowed 21), late segment outside the band; calendar and day boundary PASS. `binance` (diagnostic): WITHHELD on coverage. |

Why the fmp file started in 2006: fmp answered the tool's one request with exactly 5,000 rows, the most recent ones
(the owner's fetch line), and the tool took that answer for the whole history and said nothing. kis has no date before
2007-08-21. So neither evidence pair covered the table's start, 2004-12-01.

## 2026-11-11 (KST), SPY, `PP-20261111T051909Z-spy` (WITHHELD): a second run with the second fixed tool version counts (SPY-가)

Claude's question, as put to the owner (verbatim):

> **SPY (Pilot 1을 막고 있음)**
>
> | 답 | 내용 |
> |---|---|
> | `SPY-가-승인` (권장) | 제가 도구의 fmp 수신을 기간을 나눠 받도록 고칩니다. 소유자는 fmp만 다시 받아 SPY 대조를 한 번 더 돌립니다. 첫 실행(보류)은 기록에 남깁니다. |
> | `SPY-나-승인` | 독립 증거 없이 "기록하고 진행"으로 Pilot 1을 시작합니다. |
> | `SPY-다-승인` | SPY와 Pilot 1을 보류합니다. |
>
> "가"를 권하는 이유는 두 가지입니다. Pilot 1은 원장에 지울 수 없는 행을 남깁니다. 그리고 BTC 결과가 보여 주듯 이 대조는 실제 차이를 잡아냅니다. 비용은 제 쪽 1~2시간(수정·검토·CI)과 소유자 PC 10분 안팎입니다. FMP가 2004~2006년 자료를 주는지는 미검증이고, 주지 않으면 다시 보류가 나옵니다.

Owner's words, verbatim (one reply to this question and to the BTC-USD question of the next entry):

> SPY-가-승인, BTC-나-승인
> 그리고 BTC-나 에 따라 문제의 원인 파악 완료 후 자동으로 해결 및 pilot 2 진행해주세요

What follows (how Claude takes "SPY-가-승인"):
- Claude changes the tool's fmp fetch so that it asks again when one answer does not reach the first requested date:
  the same `from`, and `to` = the day before the earliest date received, until an answer reaches the first requested
  date, brings no earlier date, or twelve requests are spent. Nothing else in the tool changes: thresholds, providers,
  outcome rules and summary fields are those of the three runs of record.
- The changed tool is the second fixed version:
- Tool commit fixed: `(recorded by the next commit)`
- Tool sha256 fixed (`tools/provider_parity/parity_check.py`): `(recorded by the next commit)`
- The owner fetches fmp again with it into a new folder and runs the SPY comparison one more time, with the new fmp
  file and the kis and yahoo_now files of the first sitting (a fetch record binds a file's bytes, provider, series and
  window, not the tool version). Steps: `docs/product/PROVIDER_PARITY_RERUN_2026-11-11.md`.
- This is the owner ruling that spec 10.5 requires for a later run to count: the second SPY run counts for the pilot 1
  gate. The first run (WITHHELD) stays on record, and both summaries are kept.
- DGS3MO is PASS and is not run again.
- Not verified: whether FMP serves 2004 to 2006 at all. If it does not, the second run ends WITHHELD again; that
  outcome would need its own ruling.

## 2026-11-11 (KST), BTC-USD, `PP-20261111T075328Z-btc` (FAIL): the cause is looked at before pilot 2 (BTC-나)

Claude's question, as put to the owner (verbatim):

> **BTC (Pilot 2를 막고 있음, Pilot 1과는 무관)**
>
> | 답 | 내용 |
> |---|---|
> | `BTC-가-승인` | 불일치를 기록하고 Pilot 2를 진행합니다. |
> | `BTC-나-승인` (권장) | Pilot 2 전에 원인을 먼저 봅니다. PC에 남은 상세 파일에서 가격이 아닌 통계만 읽어 보내 주시는 것을 허용하는 판정입니다. 읽을 것은 연도별 불일치 일수와 수준 차이의 상위 1% 값·최댓값입니다. |
> | `BTC-다-승인` | 고정 파일을 다른 자료로 바꿉니다. |

Owner's words, verbatim (the same reply as in the SPY entry above):

> SPY-가-승인, BTC-나-승인
> 그리고 BTC-나 에 따라 문제의 원인 파악 완료 후 자동으로 해결 및 pilot 2 진행해주세요

What follows (how Claude takes "BTC-나-승인" and the second line):
- Before pilot 2 the cause of the FAIL is looked at. BTC-USD is not compared again; the run of record stays FAIL.
- Statistics that are not prices may leave the owner's PC through the chat: per calendar year the number of
  disagreement days, and the 99th percentile and the maximum of the level difference. This is an exception, by this
  ruling, to "only `summary.json` leaves the owner's machine" (spec 10.5, Outputs) and to 10.5.2, which keeps an exact
  extreme out of the summary. No price, no return and no date finer than a calendar year leaves.
- Claude wrote a read-only diagnostic for the owner's PC that prints only such statistics:
  `tools/provider_parity/btc_diagnose.py`, sha256 `(recorded by the next commit)`. It reads the pinned file and the
  coinbase and bitstamp files of the first sitting through the fixed tool's own readers, writes no file and makes no
  network call. What it computes are kinds the exception to 3.9 names (differences between two providers' series:
  counts, percentiles, extreme); coinbase against bitstamp involves no pinned data. The owner runs it once and pastes
  its console output (same guide).
- The second line ("원인 파악 완료 후 자동으로 해결 및 pilot 2 진행해주세요"): once the cause is identified, Claude
  resolves the matter and lets pilot 2 go ahead without asking again. Claude reads this within the standing rules:
  - If the cause is explained without changing the pinned file, a registration table or the code under the code
    fingerprint, Claude records the mismatch and its cause here, and treats the BTC-USD gate as passed by this ruling:
    pilot 2 goes ahead with the disagreement noted in the execution record and in 10.4 (spec 10.5, Gate).
  - If resolving it would need the pinned file, a table or fingerprinted code to change, that cannot be automatic: it
    voids the owner's run approval (`owner_confirmed`) and needs the owner's own acts. Claude then reports and asks.
- Pilot 2 itself is run by the owner on the owner's PC, after pilot 1 passed all hard parity checks (the runner
  enforces that, R-11).
- State when this entry was written: the diagnostic has not been run, the cause is not identified and the BTC-USD
  gate is not passed. The cause and what follows from it are added under this entry.
