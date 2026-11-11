# Provider parity of the pilot series (roadmap item 5-2)

`parity_check.py` compares the three md5-pinned files the pilots read (`yf_SPY.csv`, `fred_DGS3MO.csv`,
`yf_BTC-USD.csv`) with other providers' copies of the same series. Its rules are section 10.5 of
`docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md` on the research branch: the providers and thresholds of
10.5.1, the summary fields of 10.5.2, the narrow exception to 3.9, the runs of record and the procedural gate before
Step 8 (SPY, DGS3MO) and Step 9 (BTC-USD).

It runs on the owner's machine only, after Step 7A and before Step 8, from a separate clone of the tool's branch (U5),
never while a pilot, the suite or a readout runs. Claude builds and tests it on synthetic data only and reads only
`summary.json`.

The owner's step-by-step guide, in Korean with one command per step and what the screen should show, is
`docs/product/PROVIDER_PARITY_OWNER_RUN_2026-11-11.md`. It runs the same tool commands as this file. It differs in
form only: fixed folder names (`fetch1-<series>-<provider>`, `compare1-<series>`) instead of the time stamp `$t`, one
line per fetch instead of the loops, a Python line instead of `Get-FileHash` and of the PowerShell copy lines, and one
commit for the summaries of a sitting. Either form is valid; the rules are those of spec 10.5.

After the first runs of 2026-11-11 the owner ruled on the two series that were not PASS (`results/RULINGS.md`). What
follows from those rulings is in two places below: the `fmp` fetch now pages back (Fetch), which makes a second fixed
tool version, and `btc_diagnose.py` prints a few statistics of the BTC-USD disagreement (BTC-USD diagnostic). The
owner's steps for both, in Korean, are `docs/product/PROVIDER_PARITY_RERUN_2026-11-11.md`: one more `fmp` fetch into
`fetch2-spy-fmp`, one more SPY compare into `compare2-spy`, and one line that runs the diagnostic.

## Before the first run: the tool's branch, commit and sha256

Spec 10.5 names the tool's branch `claude/provider-parity-5-2` and leaves the tool's commit and sha256 to an owner
ruling before the first run. The owner gave that ruling on 2026-11-11 (P1, option 1: fixed on main's side; recorded
verbatim in `docs/nautilus_bridge/OWNER_RULINGS_LOG.md` and in `results/RULINGS.md`):

- The reviewed tool is on `main` (PR #102). `claude/provider-parity-5-2` still holds the unfinished tool of 2026-11-05
  (commit `777fc5b`, marked "do not merge") and is not used. The difference from the branch name in spec 10.5 is
  carried into the Step 10 execution record; the research branch gets no extra commit for it.
- The owner clones the run branch `claude/provider-parity-runs-20261111`, which is cut from `main` and contains the fixed commit. Summaries are
  pushed to that branch, never to `main`.
- A change to the tool after the ruling changes its sha256, and the suite fails until every statement of the fixed
  values is right again: the two lines below, `$fixed` under Setup, the two Korean guides (the first guide's table
  row and steps 6 and 7, the rerun guide's table row and steps 5 and 6) and `results/RULINGS.md`. The rulings log and
  `docs/compliance/FACTS.md` state them too; those two are prose records and are checked by hand.

The tool has had two fixed versions. The two lines below are the second, the one every run from now on is made with:

```
Tool commit fixed by the owner ruling: (recorded by the next commit)
Tool sha256 fixed by the owner ruling: (recorded by the next commit)
```

- The second fixed version follows the owner's ruling of 2026-11-11 on the first SPY run ("SPY-가-승인", verbatim in
  `results/RULINGS.md`). Only `fetch_fmp` changed: it pages back (see Fetch). Thresholds, providers, outcome rules and
  summary fields are those of the first runs. By that ruling a second SPY run made with this version counts for the
  pilot 1 gate; the first run stays on record.
- The first fixed version is the version of the runs of record of 2026-11-11 (SPY WITHHELD, DGS3MO PASS, BTC-USD
  FAIL). Their summaries carry its sha256 as `tool.sha256`, and it stays their version:
  - first fixed version, commit `5202482e3c24de871b8483608b8a03beb07abe1e`
  - first fixed version, sha256 `f2fe72cdee6344076fd6dfec8943259f44bc52445c66cdaf482a19e269770184`
- Before any run, on 2026-11-11 (KST) and before PR #102 merged, the first fixed version's values had replaced the
  ones first recorded (commit `49a3a67`, sha256 `d651795e...`): a code review found faults in the tool and it was
  changed (`results/RULINGS.md`).

Every summary records the sha256 of the tool that wrote it (`tool.sha256`); a run with other tool bytes counts only by
an owner ruling (spec 10.5, Tool).

## Setup (PowerShell)

```powershell
$rc = "<the research clone>"                         # read only: the tables, the pinned files and its .env
$fixed = "(recorded by the next commit)"
$origin = git -C $rc remote get-url origin
git clone --branch claude/provider-parity-runs-20261111 --single-branch $origin "$env:LOCALAPPDATA\quantgen\pp_clone"
cd "$env:LOCALAPPDATA\quantgen\pp_clone"
git merge-base --is-ancestor $fixed HEAD; $LASTEXITCODE                                  # 0: the fixed commit is here
git diff --quiet $fixed HEAD -- tools/provider_parity/parity_check.py; $LASTEXITCODE     # 0: the tool is as it was there
(Get-FileHash tools\provider_parity\parity_check.py -Algorithm SHA256).Hash.ToLower()    # the fixed sha256
$pp = "$env:LOCALAPPDATA\quantgen\provider_parity"   # every output folder goes under here, outside every git clone
python -B -m tools.provider_parity.parity_check selftest   # last line: SELFTEST PASS checks=11 failures=0
```

If either git line prints anything but 0, or the hash differs from the fixed sha256 above, stop: it is not the tool
the ruling fixed. (The branch's head moves on after the fixed commit: this guide's two lines and every committed
summary come later, so the head itself is not the fixed commit.) A clone made for the first runs holds the first
fixed version until it is updated: `git pull --ff-only` in it, then the same three checks with the values above (the
rerun guide's steps 4 to 8).

Use the global interpreter the app uses (numpy, pandas, requests; yfinance for `yahoo_now`), not the dedicated
Nautilus interpreter. Keys are read by name from `--env-file` (FMP_API_KEY for `fmp`; KIS_APP_KEY, KIS_APP_SECRET and
optionally KIS_BASE_URL for `kis`); nothing else in that file is read and no value is printed or written. Do not copy
the `.env` and do not type a key into the shell. The `kis` fetch uses the app's KIS client, which reads and may
rewrite its access token `~/.nextgen/kis_token.json`; nothing else under `~/.nextgen` is touched.

Every `--out` is a folder that does not exist yet. The tool refuses one inside any git work tree (the research clone,
this clone or another) and one under a folder named `asset_expansion`, `.nextgen` or `ledgers`, so nothing it writes
enters the research clone, `docs/asset_expansion/` or a ledger. It also refuses one inside a OneDrive folder (a folder
whose name starts with `OneDrive`, or the folder the `OneDrive`, `OneDriveConsumer` or `OneDriveCommercial`
environment variable names): OneDrive uploads what is written there, and `detail.json` and the raw responses stay on
this machine. Documents and Desktop are often inside OneDrive; `%LOCALAPPDATA%` is not. The tool does not know other
sync clients (Dropbox, Google Drive, iCloud), so keep the outputs out of their folders too. Files are UTF-8 with LF.
Console lines use the console's own encoding (cp949 or UTF-8); a character it lacks is printed as a backslash escape.

## Fetch (one provider per call; each `--out` is a new folder)

```powershell
$t = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
# SPY and DGS3MO: the window of pilot1_E1_spy.json
foreach ($p in "fmp", "kis", "yahoo_now") {
  python -B -m tools.provider_parity.parity_check fetch --series spy --provider $p --start 2004-12-01 --end 2026-09-25 --out "$pp\F-$t-spy-$p" --env-file "$rc\.env" }
foreach ($p in "treasury", "h15", "fred_now") {
  python -B -m tools.provider_parity.parity_check fetch --series rf --provider $p --start 2004-12-01 --end 2026-09-25 --out "$pp\F-$t-rf-$p" }
# BTC-USD: the window of pilot2_C3_btcusd.json
foreach ($p in "coinbase", "bitstamp", "binance") {
  python -B -m tools.provider_parity.parity_check fetch --series btc --provider $p --start 2014-09-17 --end 2026-09-25 --out "$pp\F-$t-btc-$p" }
```

Each call ends with `FETCH <series> <provider> OK exit=0 csv=<file>`, or `... UNAVAILABLE <reason> exit=4 csv=-` with
the reason to give compare (`no_key`, `plan_or_access`, `fetch_failed`) and a line above it that says what is missing
(for example `UNAVAILABLE: FMP_API_KEY is not set (--env-file or the environment)`), or `REFUSED exit=2`/`ERROR exit=4`.
Only an `OK` fetch writes a folder: the raw responses, the `date,value` CSV (window start - 31 days to window end + 7
days) and `meta.json`. Every request is bounded before 2027-01-01: by an explicit last date of at most 2026-12-30 or,
for the Treasury's yearly file, by a calendar year of at most 2026. A response holding an observation dated on or
after 2027-01-01 is refused before anything is written. When a fetch succeeds but its first date is far after the
window start, compare still takes the file: its coverage check counts the uncovered days. `short_history` is the
reason to declare when a provider cannot serve the window at all.

The line above `FETCH ... OK` reads `rows <n>, first <date>, last <date>, weekend dates <n>` for SPY and DGS3MO, and
`..., missing days <n>` for BTC-USD. `weekend dates` must be 0: a US session or a Treasury business day never falls on
a weekend, so any other count means the provider labels its days differently (a Korean date, or a UTC time read in
local time). Do not compare that file and do not declare `short_history`; send Claude the line. `missing days` counts
the UTC days absent inside the file's own span; compare lists them as a calendar WARN.

For `kis` the same line can end with `; kis paging stopped at <date>, after the first requested date <date>: <reason>`.
The `kis` fetch pages back 100 sessions at a time, and this says that the page-back ended before it reached the first
requested date (31 days before `--start`): `a page brought no new date` (KIS has nothing earlier, or answered with the
same page again) or `the budget of <n> requests ran out` (its pages were shorter than 100 sessions). The file then
starts at that date because of the fetch. The fetch is still `OK`, but settle it before compare: send Claude the
line. (A file that starts on or before the window start still covers the window; one that starts later would count
against coverage.)

For `fmp` the same line can end with `; fmp paging stopped at <date>, after the first requested date <date>: <reason>`.
FMP can answer a from/to request with only the most recent rows of the span: in the owner's first run it sent exactly
5,000 rows, the first dated 2006-11-15, for a span that starts on 2004-10-31. The first fixed version took that
answer for the whole history and said nothing. The `fmp` fetch now reads the earliest date of each answer and, while
that date lies more than 7 days after the first requested date, asks again for the days before it: the same `from`,
and `to` = the day before that earliest date. It stops when an answer reaches the first requested date, and then the
line carries no note. "Reaches" means an earliest date at most 7 days after the first requested date, which is 31
days before `--start` and need not be a session (2004-10-31 is a Sunday): a week covers a weekend and the holidays
beside it. It also stops, with the note, on `an answer brought no earlier date` (FMP sent an empty list for the
days asked for, or only dates the tool already holds) or `the budget of 12 requests ran out`. The fetch is then still
`OK` and the file starts at that date because of the provider or the fetch: settle it before compare and send Claude
the line. Answers are merged by date. A date that two answers give with different values ends the fetch
`UNAVAILABLE fetch_failed` (`fmp gave one date two different values in two answers`): the tool never picks one. A
later request that fails (an HTTP error, a message in place of rows, rows without `adjClose`) fails the whole fetch
with `; request <n> of the page-back` on the line, and nothing is written. Every request's parameters, never the key,
and every raw answer (`raw/fmp_000.json`, `raw/fmp_001.json`, ...) are in the fetch folder. A provider that answers
the whole span is asked once, as before. One known cost of the 7-day rule: a cap that happens to end inside that week
leaves up to five sessions unfetched at the very start of the file, more than three weeks before `--start`, which
compare never reads for SPY.

Settle every fetch of a series before its compare. A fetch is not a run and may be repeated into a new folder;
compare is what makes the run of record. No provider endpoint has been called while the tool was built (see the last
section), so if a fetch ends `UNAVAILABLE fetch_failed` or `ERROR`, or `UNAVAILABLE plan_or_access` for a provider
that needs no key, send Claude that line and the line above it before declaring the provider unavailable. The two
lines carry no key, and the only part of a provider's answer they quote is the start of an error answer. The line
above says:

- for a provider without a key (coinbase, bitstamp, binance, treasury, h15, fred_now): the HTTP status and, for a
  status of 400 or above, the first 200 bytes of the provider's error answer, with every byte outside printable ASCII
  as `\xNN` and every decimal number masked as `#.#`. `HTTP 403` from one of these is usually a proxy or a firewall
  on the way, not the provider's plan, although the tool files 401, 402 and 403 under `plan_or_access`;
- for `fmp`: the HTTP status only, because its URL holds the key;
- for `kis`: the exception type and, when the app's client reports them, `token`, the HTTP status and KIS's message
  code (`msg_cd`), never the message text;
- for `ERROR`: the exception type and the tool's own line numbers (`at parity_check.py lines ...`).

## Compare (one call per series)

```powershell
$tab = "$rc\docs\nautilus_bridge\registration"
python -B -m tools.provider_parity.parity_check compare --series spy --table "$tab\pilot1_E1_spy.json" --repo $rc `
  --pair fmp "$pp\F-$t-spy-fmp\spy_fmp.csv" --pair kis "$pp\F-$t-spy-kis\spy_kis.csv" `
  --pair yahoo_now "$pp\F-$t-spy-yahoo_now\spy_yahoo_now.csv" --out "$pp\C-$t-spy" --owner-run
python -B -m tools.provider_parity.parity_check compare --series rf --table "$tab\pilot1_E1_spy.json" --repo $rc `
  --pair treasury "$pp\F-$t-rf-treasury\rf_treasury.csv" --pair fred_now "$pp\F-$t-rf-fred_now\rf_fred_now.csv" `
  --pair h15 "$pp\F-$t-rf-h15\rf_h15.csv" --out "$pp\C-$t-rf" --owner-run
python -B -m tools.provider_parity.parity_check compare --series btc --table "$tab\pilot2_C3_btcusd.json" --repo $rc `
  --pair coinbase "$pp\F-$t-btc-coinbase\btc_coinbase.csv" --pair binance "$pp\F-$t-btc-binance\btc_binance.csv" `
  --pair bitstamp "$pp\F-$t-btc-bitstamp\btc_bitstamp.csv" --out "$pp\C-$t-btc" --owner-run
```

- Every required provider (SPY: fmp, kis, yahoo_now; DGS3MO: treasury, fred_now; BTC-USD: coinbase, binance) is either
  a `--pair` or an `--unavailable <provider> <reason>` (reasons: no_key, plan_or_access, fetch_failed,
  short_history). The optional ones (h15, bitstamp) may be left out. Roles and conventions are fixed in the tool.
- The result is the last line, `PARITY <series> <PASS|FAIL|WITHHELD|REFUSED|ERROR> exit=<n> summary=<path or ->`
  (exit 0 PASS, 1 FAIL, 3 WITHHELD, 2 refused, 4 error). A line that does not start with `PARITY` means no result.
- The output folder holds `summary.json` (counts, outcomes, decade buckets, calendar dates; the tool refuses to write
  anything else) and `detail.json` (the per-date values and differences). `detail.json` stays on this machine.
- `--owner-run` says this is the owner's machine: without it the tool refuses a file under `asset_expansion/cache`
  before opening or hashing it, whether the path is spelled that way or only leads there (a link or a junction).
  `--repo` is the research clone and must not contain this tool: a clone that holds the tool is refused, because the
  tool runs from a separate clone (U5).
- A `--pair` file inside its fetch folder is checked against that folder's `meta.json`: a file edited, renamed or
  replaced after its fetch is refused (fetch again into a new folder). Each pair in the summary carries
  `has_fetch_record`; a file compared from anywhere else shows `false`, and Claude will ask where it came from. The
  record binds the file's bytes, its provider and series and the window it was fetched for. It does not bind the tool
  version: a file fetched with the first fixed version is taken by the second (`read_provider` reads `schema`,
  `provider`, `series`, `csv.file`, `csv.sha256` and `window` of the record and nothing else), which is what the
  second SPY run relies on for the kis and yahoo_now files of the first sitting.
- The same record says which `--start` and `--end` the file was fetched for. A file fetched for a window that starts
  after the table's start or ends before the table's end is refused before anything is compared:
  `REFUSED: <file>: its fetch record's window <start>..<end> does not cover the table's window <start>..<end>; ...`.
  10.5.1 measures coverage over the provider's own first-to-last span (P-D5), and a fetch made with another series'
  dates is short because of the request, not because of the provider; compared, it would end WITHHELD on coverage,
  a run of record. Fetch again with the table's dates into a new folder. A fetch for a wider window is taken.
- A SPY pair that ends WITHHELD on coverage with `n_common` near 80 % of `n_a` points to a date label one calendar
  day off, not to a short history. The calendar check does not run on a WITHHELD pair, so the summary shows the
  coverage counts only. Report it; do not declare `short_history`. The fetch line's `weekend dates` shows the same
  thing before compare.
- If the lines above the result are `LEFT BEHIND: <folder> ...` and `ERROR: ...`, a write failed and the folder could
  not be removed (a virus scanner or a sync client held a file). It is not a run, and whatever it holds is not a
  result (`detail.json` is written first, so there is never a summary without its detail): delete it by hand and run
  again into a new folder.
- The pilot table is read as plain UTF-8 JSON. A table saved with a BOM is refused (`cannot be read as a pilot table
  (JSONDecodeError)`), although the runner's `--fingerprint` tolerates one. Do not re-save a table to cure it (its
  bytes are what `owner_confirmed` quotes): send Claude the line. The two tables as committed at Step 7A.3 (`563db54`
  on the research branch) have no BOM.
- A provider whose history starts late is compared inside its own span (P-D5); A's dates outside the span count
  against `edge_uncovered_max` (5 for SPY and DGS3MO, 471 for BTC-USD), and above that the pair is WITHHELD on
  coverage. The repository's own Binance client notes that BTCUSDT starts on 2017-08-17; if the fetched file starts
  there, the `binance` pair ends WITHHELD on coverage. It is a diagnostic pair, so the series outcome does not depend
  on it.

## After each PASS, FAIL or WITHHELD run

```powershell
$run = (Get-Content "$pp\C-$t-spy\summary.json" | ConvertFrom-Json).run_id      # PP-<UTC>-spy
New-Item -ItemType Directory "results\$run" | Out-Null
Copy-Item "$pp\C-$t-spy\summary.json" "results\$run\summary.json"
git add "results\$run\summary.json"
git commit -m "5-2: $run summary"
git push
```

- Every summary is committed, whatever its outcome. Never add `detail.json`, a fetch folder or a CSV.
- Per series, the first PASS, FAIL or WITHHELD run is the run of record. A REFUSED or ERROR run writes nothing and is
  not a run. A later run counts only after an owner ruling written next to the earlier result in
  `results/RULINGS.md`; the earlier result stays.
- Step 8 starts when the SPY and DGS3MO runs of record say PASS, or `results/RULINGS.md` holds a ruling for each that
  does not; Step 9 likewise for BTC-USD. The runner does not check this gate.
- Rulings so far (2026-11-11, `results/RULINGS.md`): the SPY run of record is WITHHELD, and a second SPY run made with
  the second fixed version counts for the Step 8 gate; the BTC-USD run of record is FAIL, and its cause is looked at
  before Step 9 with the diagnostic below. DGS3MO is PASS.
- Send Claude the three `PARITY` lines; Claude reads only the pushed `summary.json` files.

## Owner rulings (`results/RULINGS.md`, P-D9)

The file starts with the ruling of 2026-11-11 that fixes the tool; later rulings are added on the run branch next to
the result they concern. Step 10 carries its rulings into the execution record and the
spec's Status block. A ruling is needed before:

- a later run of a series that already has a run of record counts (new fetches or the same files);
- a change to the providers or thresholds of 10.5.1 after any summary exists;
- Step 8 (SPY, DGS3MO) or Step 9 (BTC-USD), when that series' run of record is not PASS: the ruling either holds the
  pilot or lets it go ahead with the disagreement noted in the execution record and in 10.4;
- a run with tool bytes other than those 10.5 fixes counts.

Each entry gives the date (KST), the series, the `run_id` it concerns, the owner's words verbatim, and what follows.
The earlier result is never removed.

## BTC-USD diagnostic (`btc_diagnose.py`)

The BTC-USD run of record of 2026-11-11 ended FAIL against coinbase and bitstamp. The owner ruled ("BTC-나-승인",
verbatim in `results/RULINGS.md`) that the cause is looked at before pilot 2, and that statistics which are not prices
may leave the PC through the chat: per calendar year the number of disagreement days, and the 99th percentile and the
maximum of the level difference. `btc_diagnose.py` prints those and nothing else. It is not a run: it writes no file,
makes no network call, writes no summary and changes no outcome. The owner runs it once, from the tool clone's root,
and pastes the whole console output:

```powershell
python -B -m tools.provider_parity.btc_diagnose --table "$tab\pilot2_C3_btcusd.json" --repo $rc `
  --pair coinbase "<fetch folder>\btc_coinbase.csv" --pair bitstamp "<fetch folder>\btc_bitstamp.csv" --owner-run
```

- It reads the pinned file and the two provider files only through this tool's own readers (`read_table`,
  `read_pinned`, `read_provider`), aligns them with `_common` and takes every threshold from `THRESHOLDS`, so the
  dates and definitions are those of the run of record. The md5, the fetch records and the `--owner-run` guard apply
  as in compare. It takes the BTC-USD table and `coinbase` and `bitstamp`, each once, and refuses anything else.
- A disagreement day is a day whose log-return difference between two series is above `ret_diff_big` (0.02), the
  definition of the tool's `levels_and_returns` check. The level difference of a day is `abs(log(P_x / P_y))`.
- Lines, in order: `BTCDIAG 1` with the sha256 of the tool file and of the script; `window` (the table's start and
  end, the thresholds used); `common` (days two series share); `returns` (per year and in total: days compared and
  disagreement days, for pinned against each provider and for coinbase against bitstamp, which involves no pinned
  data); `levels` (per segment, before and from `late_from`: the 99th percentile and the maximum of the level
  difference in percent with two decimals, and the days above `level_p99_max` and `level_max`); `split` (per year:
  the disagreement days against both providers, against one only, and against one on a day the other was not
  compared); `venues` (per year, of the days against both: on how many the two venues agree with each other, differ,
  or were not compared with each other); and the result line `BTCDIAG <OK|REFUSED|ERROR> exit=<n>` (0, 2, 4).
- How to read it: if most `both` days are `agree` days, the pinned series stands apart from two venues that agree
  with each other; if the disagreement days are `_only` days or `differ` days, the venues stand apart from each
  other.
- Limits. It never prints a price, a return, a difference of one named day or a date finer than a calendar year (the
  table's start and end and the threshold `late_from` aside). Every line is held to an allow-list of shapes before
  the first one is printed. Before that the script holds its own numbers to the tool's `levels_and_returns` check of
  the same pair (count of disagreement days, days per segment, decade buckets) and prints no data when they differ.
  The 99th percentile and the maximum are exact statistics that 10.5.2 keeps out of `summary.json`; they leave the
  machine by this ruling only, rounded to two decimals of a percent. The kinds it computes are those the exception
  to 3.9 names: differences between two providers' series, as counts, percentiles and an extreme. It computes no lag
  count, no median, no correlation and nothing of one series alone.
- Its sha256 is written in `results/RULINGS.md` and in the rerun guide, and the suite holds both statements to the
  file's bytes. It is not part of the fixed tool version: a change to it changes no run.

## Tests

```
python -B -m unittest tests.provider_parity_acceptance tests.provider_parity_btc_diagnose_acceptance -v
```

124 cases on synthetic series, with every provider faked in the process and socket connects patched to raise: each
threshold of 10.5.1 from both sides, every outcome and exit code, the provider map, the 2027-01-01 cut-off, the summary
allow-list, where the tool may write, key handling, a cp949 console, the tool started as a module, the `fmp`
page-back (a capped provider at several cap sizes, a history that really starts late, overlapping answers that agree
and that disagree, the request budget, failed and empty answers on the first and on a later request, rows without an
ISO date, and a fetch and compare that ends PASS where one answer alone ended WITHHELD), the rerun guide (its tool
lines and its two Python lines run as they are written in the guide file, and every failure line its table quotes
for the fetch and the compare raised and compared with the table), and every statement of the fixed tool commit and
sha256 (current statements against the tool file, the first version's values as marked history only). The fetchers
are checked against values typed by hand (epoch seconds, request parameters, expected rows), and the tool's own HTTP
function runs with `urlopen` replaced. The suite reads no cache file, no `.env` and nothing under `~/.nextgen`; in
the repository it reads the tool, the diagnostic script (for its sha256), this guide, the two Korean guides,
`results/RULINGS.md` and the CI workflow.

The second module holds the diagnostic in 15 cases, on synthetic series built with the first module's helpers: the
yearly counts add up to the tool's own `n_big_return_diff_days` of the same files; the level statistics equal values
computed from the files parsed by hand and fall in the tool's buckets; a perturbed pinned series reads as `both` and
`agree`, a perturbed venue as `_only`; refusals; the output allow-list, with no price, no return and no day of the
data in the output; no file opened for writing and no socket; the script run as the owner runs it, and the rerun
guide's diagnostic line run as it is written there.

The suite is not registered in `tests/run_all.py` and has no row in the root `README.md`: both files are left as they
are on main until the owner says otherwise, so the Step 10 merge of the research branch meets no conflict there. CI
runs the suite in the "bounded source fixtures" step of `.github/workflows/runtime-smoke.yml`, for a pull request
that changes a path on that workflow's filter. Every file the suite reads is on the filter. The root `README.md`,
`tests/run_all.py` and `docs/compliance/FACTS.md` are not (the workflow takes half an hour), so no case reads them:
that the first two do not name this suite is a record (here and in section 8 of the Korean guide; checked by hand
with `git grep` when the tool was fixed), and FACTS is held by `python -B -m tools.compliance.check --check`.

## Not included

- The design draft (4.1 and its test plan) also has the formal tool compare the 2025-2026 SPY sessions with the signed
  NYSE calendar. That check is not built: spec 10.5 and 10.5.1 do not list it, and it would have to enter `COMPUTES`
  and 10.5.1 before any summary exists. It is an open question for the owner.
- The same draft expects a SPY provider with next-day labels to end `calendar` FAIL. Here coverage is judged first
  (10.5.1), so such a pair ends WITHHELD and its calendar check does not run; with another evidence pair clean, the
  series can still PASS. The fetch line's `weekend dates` and the note under Compare are what show the shift.

## Not verified (no network was used to build the tool)

- No provider was called and no provider documentation was fetched. Endpoint shapes are taken from the repository's
  own clients where they exist (FMP, KIS, Binance, FRED, yfinance). The others are written from memory of the
  providers' public interfaces and are the least certain part of the tool: the Coinbase candles endpoint, the Bitstamp
  OHLC endpoint, the Treasury XML feed (`BC_3MONTH`, one page per year) and the H.15 Data Download Program series id
  (the values are read from the one column whose `Unique Identifier` is `RIFLGFCM03_N.B`; a response without that
  column, or with it twice, ends `UNAVAILABLE fetch_failed`). Also unknown: KIS exchange code `AMS` for SPY,
  FMP's history depth on the owner's plan and Coinbase's first candle. A response of an unexpected shape ends
  `UNAVAILABLE fetch_failed`; a well-formed response of the wrong series shows as a coverage, calendar or value
  disagreement in compare.
- What the owner's runs of 2026-11-11 showed, read from the three pushed summaries and the lines the owner sent:
  eight of the nine providers were fetched and compared; `h15` was declared `fetch_failed`; FMP answered one request
  with exactly 5,000 rows from 2006-11-15; the kis file starts on 2007-08-21; the coinbase file starts on 2015-07-20.
  Still not verified, because Claude has called no provider: that FMP cuts an answer by rows and honours `to`, so
  that a second request brings the days before; whether FMP has SPY before 2006-11-15 at all; and what FMP answers
  for a span in which it has no row (the tool takes an empty list as "nothing earlier" and treats anything else as a
  failed fetch). The second fixed version and the diagnostic have not run on Windows or on a real file.
- Claude has not run the tool on Windows and has not read a real pilot file. The first fixed version ran on the
  owner's Windows PC on 2026-11-11 and read the real pinned files there; of those runs Claude has seen the three
  pushed summaries and the lines the owner sent, nothing else. The suite was run on Linux only (Python 3.13,
  numpy 2.3.5, pandas 2.3.3). Checked on Linux only, with stand-ins: a link to a folder named `asset_expansion/cache`
  (not a Windows junction or an 8.3 short name), a folder named `OneDrive` and the three OneDrive variable names
  (not a real OneDrive), LF under simulated Windows text mode, and a folder that cannot be removed (simulated).
- The PowerShell lines of this guide have not been run. The owner followed the Korean guide's lines on Windows on
  2026-11-11, through its push (run branch commit `0b397f7` holds the three summaries). Claude followed the steps of
  both Korean guides on Linux only: the same git and python commands rewritten for bash, a synthetic research clone
  and stand-in transports, with a scratch repository on disk in place of GitHub. For the rerun guide the stand-ins
  were an in-process fake FMP and a synthetic key file under another name than `.env`, and its `git push` was not
  run. The last section of each guide lists what that could not show.
- The thresholds of 10.5.1 were set without real data, so the rate of false FAIL on real series is unknown.
- yfinance 1.7.0 routes its tz, cookie and ISIN caches through `set_tz_cache_location` (read from its source, not
  from a download); another version may keep a cache elsewhere.
