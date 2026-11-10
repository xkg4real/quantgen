# Provider parity of the pilot series (roadmap item 5-2)

`parity_check.py` compares the three md5-pinned files the pilots read (`yf_SPY.csv`, `fred_DGS3MO.csv`,
`yf_BTC-USD.csv`) with other providers' copies of the same series. Its rules are section 10.5 of
`docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md` on the research branch: the providers and thresholds of
10.5.1, the summary fields of 10.5.2, the narrow exception to 3.9, the runs of record and the procedural gate before
Step 8 (SPY, DGS3MO) and Step 9 (BTC-USD).

It runs on the owner's machine only, after Step 7A and before Step 8, from a separate clone of the tool's branch (U5),
never while a pilot, the suite or a readout runs. Claude builds and tests it on synthetic data only and reads only
`summary.json`.

Spec 10.5 names the tool's branch `claude/provider-parity-5-2` and leaves its commit and sha256 to an owner ruling
before the first run. Clone that branch at the commit fixed for the run, and before the first run compare
`git rev-parse HEAD` and `(Get-FileHash tools\provider_parity\parity_check.py -Algorithm SHA256).Hash.ToLower()` with
the fixed values. Every summary records the sha256 of the tool that wrote it (`tool.sha256`).

## Setup (PowerShell)

```powershell
$rc = "<the research clone>"                         # read only: the tables, the pinned files and its .env
$origin = git -C $rc remote get-url origin
git clone --branch claude/provider-parity-5-2 --single-branch $origin "$env:LOCALAPPDATA\quantgen\pp_clone"
cd "$env:LOCALAPPDATA\quantgen\pp_clone"
$pp = "$env:LOCALAPPDATA\quantgen\provider_parity"   # every output folder goes under here, outside every git clone
python -B -m tools.provider_parity.parity_check selftest   # last line: SELFTEST PASS checks=11 failures=0
```

Use the global interpreter the app uses (numpy, pandas, requests; yfinance for `yahoo_now`), not the dedicated
Nautilus interpreter. Keys are read by name from `--env-file` (FMP_API_KEY for `fmp`; KIS_APP_KEY, KIS_APP_SECRET and
optionally KIS_BASE_URL for `kis`); nothing else in that file is read and no value is printed or written. Do not copy
the `.env` and do not type a key into the shell. The `kis` fetch uses the app's KIS client, which reads and may
rewrite its access token `~/.nextgen/kis_token.json`; nothing else under `~/.nextgen` is touched.

Every `--out` is a folder that does not exist yet. The tool refuses one inside any git work tree (the research clone,
this clone or another) and one under a folder named `asset_expansion`, `.nextgen` or `ledgers`, so nothing it writes
enters the research clone, `docs/asset_expansion/` or a ledger. Files are UTF-8 with LF. Console lines use the
console's own encoding (cp949 or UTF-8); a character it lacks is printed as a backslash escape.

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
days) and `meta.json`. Every request names its last date (at most 2026-12-30), and a response holding an observation
dated on or after 2027-01-01 is refused before anything is written. When a fetch succeeds but its first date is far
after the window start, compare still takes the file: its coverage check counts the uncovered days. `short_history` is
the reason to declare when a provider cannot serve the window at all.

Settle every fetch of a series before its compare. A fetch is not a run and may be repeated into a new folder;
compare is what makes the run of record. No provider endpoint has been called while the tool was built (see the last
section), so if a fetch ends `UNAVAILABLE fetch_failed` or `ERROR`, send Claude that line and the line above it (they
carry no value and no key) before declaring the provider unavailable.

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
  before opening or hashing it. `--repo` is the research clone and must not contain this tool: a clone that holds
  the tool is refused, because the tool runs from a separate clone (U5).
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

## Owner rulings (`results/RULINGS.md` on the tool's branch, P-D9)

The file is written when the first ruling is needed; Step 10 carries its rulings into the execution record and the
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

78 cases on synthetic series, with every provider faked in the process and socket connects patched to raise: each
threshold of 10.5.1 from both sides, every outcome and exit code, the provider map, the 2027-01-01 cut-off, the summary
allow-list, where the tool may write, key handling, a cp949 console, and the tool started as a module. The suite reads
no cache file, no `.env` and nothing under `~/.nextgen`.

## Not verified (no network was used to build the tool)

- No provider was called and no provider documentation was fetched. Endpoint shapes are taken from the repository's
  own clients where they exist (FMP, KIS, Binance, FRED, yfinance). The others are written from memory of the
  providers' public interfaces and are the least certain part of the tool: the Coinbase candles endpoint, the Bitstamp
  OHLC endpoint, the Treasury XML feed (`BC_3MONTH`, one page per year) and the H.15 Data Download Program series id
  (the response must name `RIFLGFCM03_N.B`, else the fetch fails). Also unknown: KIS exchange code `AMS` for SPY,
  FMP's history depth on the owner's plan and Coinbase's first candle. A response of an unexpected shape ends
  `UNAVAILABLE fetch_failed`; a well-formed response of the wrong series shows as a coverage, calendar or value
  disagreement in compare.
- The tool has not run on Windows and has not read a real pilot file. The suite was run on Linux only (Python 3.13,
  numpy 2.3.5, pandas 2.3.3).
- The thresholds of 10.5.1 were set without real data, so the rate of false FAIL on real series is unknown.
- yfinance 1.7.0 routes its tz, cookie and ISIN caches through `set_tz_cache_location` (read from its source, not
  from a download); another version may keep a cache elsewhere.
