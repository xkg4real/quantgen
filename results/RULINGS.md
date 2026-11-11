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
- 2026-11-11 (KST), added after the first runs and the owner's ruling on them: the commit and the sha256 above are
  the tool's first fixed version. It made the three runs of record of 2026-11-11 (next entry) and stays their
  version. "No run of record exists yet" was the state when this entry was written. For every later run the fixed
  version is the second one, stated under the SPY entry of 2026-11-11 below.

## 2026-11-11 (KST), all series: the first runs, each its series' run of record

The owner ran the tool on his PC on 2026-11-11 with the first fixed version and pushed the three summaries to the run
branch (`claude/provider-parity-runs-20261111`, commit `0b397f7`). Each `tool.sha256` is the first fixed version's.
Each run is its series' run of record and stays. Read from the pushed `summary.json` files only:

| Series | `run_id` | Outcome | What the summary says |
| --- | --- | --- | --- |
| SPY | `PP-20261111T051909Z-spy` | WITHHELD | `fmp` (independent): first date 2006-11-15, 494 of the table's 5,489 sessions lie before its span (allowed 5), so the pair is WITHHELD on coverage. `kis` (cross): first date 2007-08-21, 684 sessions before its span, WITHHELD on coverage. Neither pair's return comparison ran. `yahoo_now` (vintage): PASS on 5,489 common days. Reason: `no independent or cross pair was evaluated in full`. |
| DGS3MO | `PP-20261111T075307Z-rf` | PASS | `treasury` (independent): 5,475 common values, 0 beyond tolerance; the pair is WARN, not PASS, because on 3 dates the pinned file has a value and treasury has none (a warning check; the dates are in the summary). `fred_now` (vintage): PASS. `h15` (optional) not compared: `fetch_failed`. |
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
  the same `from`, and `to` = the earliest date received, until an answer reaches the first requested date, brings no
  earlier date, or twelve requests are spent. That earliest date is asked for twice on purpose: the two values the
  provider gives for it are compared at the fetch, and a fetch is not a run. Only dates inside the span asked for
  count, so no request names a later day than the one before it. Nothing else in the tool changes: thresholds,
  providers, outcome rules and summary fields are those of the three runs of record.
- The changed tool is the second fixed version:
- Tool commit fixed: `1be43ec191ce73bc4fbc7357a4b3438aca0e4bb1`
- Tool sha256 fixed (`tools/provider_parity/parity_check.py`): `78dd1f508c713f9be138466bf69f5dd92d8bfdcc3afacfa37b21fc4bf28ca80c`
- 2026-11-11 (KST), before this change merged and before any run with the second fixed version: the two values above
  replace those recorded earlier that day for it (commit `4096caa`, sha256 `f56caeb4...`), because a review of that
  tool found faults in the fmp fetch that could have cost the owner the second SPY run (a page-back request could
  name a later day than the request before it, 2027 included; two answers never shared a day, so a provider whose
  values for a day depend on the request would have ended the fetch `OK` and failed only in the compare of record; a
  file could start late without the note) and the tool was changed to fix them. No run was made with the replaced
  values. The diagnostic's sha256 below was replaced at the same time (the script changed after the same review; it
  had not been run).
- "Reaches" means an earliest date at most 7 days after the first requested date, which is 31 days before the
  table's start and need not be a session. A fetch that stops later than that still ends `OK` and says where and why
  on the console line above its `FETCH ... OK` line; the owner does not compare such a file (the guide's stop point).
- The owner fetches fmp again with it into a new folder and runs the SPY comparison one more time, with the new fmp
  file and the kis and yahoo_now files of the first sitting (a fetch record binds a file's bytes, provider, series and
  window, not the tool version). Steps: `docs/product/PROVIDER_PARITY_RERUN_2026-11-11.md`.
- This is the owner ruling that spec 10.5 requires for a later run to count: the second SPY run counts for the pilot 1
  gate. The first run (WITHHELD) stays on record, and both summaries are kept.
- DGS3MO is PASS and is not run again.
- Not verified: whether FMP serves 2004 to 2006 at all, and whether it gives one value for a day in two requests.
  If the new fmp file still starts late, or the fetch fails, the owner stops at the guide's stop point and no second
  run is made: the SPY run of record stays WITHHELD and pilot 1 stays held. If a second run is made and ends
  WITHHELD or FAIL, its summary stays on record beside the first. Either way, another change to the tool or another
  compare counts only after a new owner ruling (spec 10.5, Tool; Runs of record).

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
- Claude wrote a read-only diagnostic for the owner's PC: `tools/provider_parity/btc_diagnose.py`, sha256
  `66340bf1330f4cc985328e7756cca4a366423da7c6e47fb8d4b1fc063b64cd3c`. It makes no network call and, run with `-B`
  as the guide's line is, writes no file. The owner runs it once and pastes its console output (same guide).
- Where the diagnostic goes beyond the words of the option (Claude's reading, not the owner's words):
  - *What it reads.* The option said "PC에 남은 상세 파일에서": from the detail file left on the PC. For this check
    `detail.json` holds the 100 largest level differences of a pair and no return difference (read from the tool's
    code), so the yearly counts cannot come from it. The script reads the pinned file and the coinbase and bitstamp
    files of the first sitting again, through the fixed tool's own readers (the md5, the fetch records and the pinned
    cache guard apply as in compare), and computes kinds the exception to 3.9 names: differences between two
    providers' series, as counts, percentiles and an extreme. That exception names the tool; the script is a second
    file beside it and prints by this ruling. It opens no `detail.json`.
  - *What it prints.* The option named two kinds: the disagreement days per calendar year (`over` on the `returns`
    lines of the two pinned pairs) and the 99th percentile and the maximum of the level difference (`p99_pct` and
    `max_pct` on their `levels` lines). The script prints those and, as Claude's reading of "가격이 아닌 통계", also:
    the sha256 of the tool, of the script and of the two provider files, and whether each file had its fetch record;
    the table's window and three thresholds; the days two series share; the days compared per year; the days above
    the two level thresholds; for the disagreement days, which group each is in (`split`: against both providers,
    against one while the two venues differ, against one while they agree, or not pairable) and whether the venues
    agree on the days against both (`venues`); and the same `returns` and `levels` lines for coinbase against
    bitstamp, which involve no pinned data. All of these are counts, identifiers or constants. None is a price, a
    return or a date finer than a calendar year. The rerun guide lists them before the owner pastes anything and
    says the owner may hold the output back.
  - *The maximum.* `max_pct` is the level difference of one single day, printed without its date and to one decimal
    of a percent; a segment of fewer than 100 days prints `n/a`. The two venues' closes are public, so someone who
    found that day could work the pinned close of that one day back to about the rounding (0.05%). A reviewer did
    this on synthetic series; on the real files it is not verified.
- How Claude reads the output. This is Claude's rule, not the owner's words. It was written on 2026-11-11, before any
  output existed, so that the reading cannot follow the result. It was tried on synthetic series only; into which
  case real data falls is not verified.
  1. *The files.* The output counts only when it is of the files of record: `tool_sha256` is the second fixed
     version's and `script_sha256` the value above; each `file` line shows the `file_sha256` that the summary of
     record holds for that provider, with `fetch_record=yes`; `common` is 4086 for pinned-coinbase and 4392 for
     pinned-bitstamp; `tool_over` and `tool_allowed` are 43 and 20 for coinbase, 47 and 21 for bitstamp; the late
     segment has 3555 days in each pair. If one of these differs, nothing is read from the output and Claude asks.
  2. *The groups.* Every disagreement day of a pinned pair is in exactly one group. From the `total` lines, for a
     provider p (coinbase, bitstamp): `agree` (against both providers while the two venues agree with each other:
     the pinned series stands apart); `p_only` and `differ` (the two venues differ from each other that day);
     `p_edge` (against p alone while the venues agree: no series is clearly the odd one); `p_unpaired` and
     `unpaired` (nothing can be said).
  3. *Case "the venues differ from each other".* Both of these hold. (a) For each provider p, `agree` + `p_edge` +
     `p_unpaired` + `unpaired` is at most that pair's `tool_allowed`: without the days on which the venues differ
     from each other, the pair is inside the tool's own allowance. (b) The coinbase-bitstamp pair is outside every
     late level limit that a pinned pair is outside: where a pinned pair's late `over_max` is 1 or more, so is the
     coinbase-bitstamp pair's; where a pinned pair's late `over_p99_max` is 36 or more, the coinbase-bitstamp pair's
     is 37 or more. (Of 3,555 days, 37 or more above `level_p99_max` put the 99th percentile above it for certain
     and 35 or fewer put it below; 36 leaves it open. The late band has a third limit, on the median; the summary
     of record shows both pinned pairs inside it.) Then both parts of the FAIL are shown without the pinned file:
     two exchanges' closes differ from each other on that many days and by that much. The cause counts as
     identified.
  4. *Case "the pinned series stands apart".* For each provider p, `agree` alone is above that pair's
     `tool_allowed`. The lines then say which series stands apart (the pinned one), in which years and how far. They
     do not say why: single bad closes in the pinned file, another kind of price than one venue's close, and a
     close taken at another time of day all give such counts, and the late `levels` line covers 2017 to 2026 as one
     segment. The cause is not verified.
  5. *Anything else* (one provider in case 3 and the other in case 4, or the `_edge` and unpaired days deciding):
     the cause is not identified.
- The second line ("원인 파악 완료 후 자동으로 해결 및 pilot 2 진행해주세요"): once the cause is identified, Claude
  resolves the matter and lets pilot 2 go ahead without asking again. Claude reads this within the standing rules:
  - If the cause is explained without changing the pinned file, a registration table or the code under the code
    fingerprint, Claude records the mismatch and its cause here, and treats the BTC-USD gate as passed by this ruling:
    pilot 2 goes ahead with the disagreement noted in the execution record and in 10.4 (spec 10.5, Gate). Of the
    cases above this is case 3, and only case 3.
  - In case 4 or 5 the cause is not identified, so the gate does not pass by itself. Claude reports the numbers and
    asks the owner.
  - If resolving it would need the pinned file, a table or fingerprinted code to change, that cannot be automatic: it
    voids the owner's run approval (`owner_confirmed`) and needs the owner's own acts. Claude then reports and asks.
- Pilot 2 itself is run by the owner on the owner's PC, after pilot 1 passed all hard parity checks (the runner
  enforces that, R-11).
- State when this entry was written: the diagnostic has not been run, the cause is not identified and the BTC-USD
  gate is not passed. The cause and what follows from it are added under this entry.
