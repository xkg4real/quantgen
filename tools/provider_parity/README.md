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
  values is right again: the two lines below, `$fixed` under Setup, the Korean guide (its table row and steps 6 and
  7) and `results/RULINGS.md`. The rulings log and `docs/compliance/FACTS.md` state them too; those two are prose
  records and are checked by hand.

```
Tool commit fixed by the owner ruling: 49a3a67b246d020381b27067103d1a7ba4795f9e
Tool sha256 fixed by the owner ruling: d651795e4b4776d096601a43989c7f45c375ae120b75a64179432f469d2daca1
```

Every summary records the sha256 of the tool that wrote it (`tool.sha256`); a run with other tool bytes counts only by
an owner ruling (spec 10.5, Tool).

## Setup (PowerShell)

```powershell
$rc = "<the research clone>"                         # read only: the tables, the pinned files and its .env
$fixed = "49a3a67b246d020381b27067103d1a7ba4795f9e"
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
summary come later, so the head itself is not the fixed commit.)

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
  `has_fetch_record`; a file compared from anywhere else shows `false`, and Claude will ask where it came from.
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

## Tests

```
python -B -m unittest tests.provider_parity_acceptance -v
```

114 cases on synthetic series, with every provider faked in the process and socket connects patched to raise: each
threshold of 10.5.1 from both sides, every outcome and exit code, the provider map, the 2027-01-01 cut-off, the summary
allow-list, where the tool may write, key handling, a cp949 console, the tool started as a module, and every statement
of the fixed tool commit and sha256. The fetchers are checked against values typed by hand (epoch seconds, request
parameters, expected rows), and the tool's own HTTP function runs with `urlopen` replaced. The suite reads no cache
file, no `.env` and nothing under `~/.nextgen`; in the repository it reads the tool, this guide, the Korean guide,
`results/RULINGS.md` and the CI workflow.

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
- The tool has not run on Windows and has not read a real pilot file. The suite was run on Linux only (Python 3.13,
  numpy 2.3.5, pandas 2.3.3). Checked on Linux only, with stand-ins: a link to a folder named `asset_expansion/cache`
  (not a Windows junction or an 8.3 short name), a folder named `OneDrive` and the three OneDrive variable names
  (not a real OneDrive), LF under simulated Windows text mode, and a folder that cannot be removed (simulated).
- The PowerShell lines of this guide have not been run. The steps of the Korean guide were followed on Linux only:
  the same git and python commands rewritten for bash, a synthetic research clone and stand-in transports (`urlopen`,
  a stand-in `yfinance` module and a stand-in for the app's KIS client module), with the clone and the push against a
  scratch repository. Its last section lists what that could not show.
- The thresholds of 10.5.1 were set without real data, so the rate of false FAIL on real series is unknown.
- yfinance 1.7.0 routes its tz, cookie and ISIN caches through `set_tz_cache_location` (read from its source, not
  from a download); another version may keep a cache elsewhere.
