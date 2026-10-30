# Native PyQt6 desktop migration — native workflows and acceptance status

The desktop now has a separate native Qt entry point. Browser access still uses
the existing Flet `main.py`; neither its routes nor calculation engines changed.
This is an opt-in preview, **not a completed replacement for all Flet screens**.

## Run from a checkout or installed wheel

```text
python -m pip install ".[desktop]"
python -m quantgen_desktop
```

An installed wheel also provides `quantgen-desktop`. The optional dependency is
PyQt6 6.12.0. A regular installation without the `desktop` extra still supports
the existing Flet browser launcher. Do not uninstall Flet during this migration.
PyQt licensing must be considered separately before any future public or
commercial distribution; current repository policy remains personal use.

## Implemented native flows

| Workspace | Working native scope | Limits |
|---|---|---|
| Research Home | Session Monte Carlo counts, daily market observations, last computed fan and provenance | Counts exclude portfolio optimizations; no historical ledger scan |
| Markets | Six existing daily observations, dates/provider/status and correct bp/% units; Bonds calculator/scenarios/hedge, Rates curve/swap/options/simulation FX forward/smile/carry, four structured notes and descriptive macro sheet/daily/weekly commentary; Derivatives board, ETF sleeves, Crypto analytics and six KRX datasets | Native Macro v2 overlay/cards/register use the existing validated readers; optional AI commentary is in Research Library. Native ETF/Crypto study cards are explicitly NOT_LOADED |
| Build & Test | All four existing Monte Carlo models, data source, seed, target, drift/ERP, percentile fan, loss risk and GARCH diagnostic notes | Strategy Lab seven-family validation and explicit study-card viewer; optional AI commentary is in Research Library |
| Portfolio & Risk | Four existing objectives, weights/risk contributions, frontier, correlation, source/convention/convergence notices; technical composite and three costed backtests | Explicit JSON/ZIP exports; native paper-only runtime controls |
| Research Library | Session Monte Carlo results, native JSON and report ZIP save dialog | No persistent history browser; only explicit export |
| System | Existing bounded recorded-status verification, native theme switch | Explicit presence and KRX/FICC/KIS/Crypto probes; native rule editor with blank financial inputs |

Both Monte Carlo and portfolio use the existing `core.quant` functions. New
`core.research` adapters capture inputs before
workers start. They do not contain replacement pricing/optimization formulas.
The existing formal gate remains unchanged. Calculation completion retains
`NOT_RUN`, `PARTIAL`, and `NOT_APPLIED` in ResearchRun exports.

Qt renders widgets and charts directly; no browser, Flet process, embedded web
view or localhost listener is started by the native entry point. A single worker
queue prevents overlapping analysis/refresh jobs. Qt signals marshal completion
to the GUI thread. Navigation remains available while a calculation runs.
The current preview waits for a running job before allowing window close; job
cancellation is not implemented. Provider error categories are displayed without
raw credential-bearing URLs. Failed Monte Carlo runs are retained in the session.

## Remaining migration, in order

1. Rates/FX native computation branches are ported; live provider acceptance remains pending.
   The optional AI commentary uses the existing backend. Rates uses the existing curve coverage policy
   and does not incorporate the separate Claude PT-04 branch.
2. Derivatives, ETF, Crypto and KRX native adapters are implemented. Live API acceptance remains pending.
3. Macro v2 and Strategy Lab are ported; preserve trial registration,
   gate/provenance semantics and approval boundaries; no live stores in tests.
4. Paper-only Trading, Rules and Settings are ported. Optional AI commentary is available in Research Library.
   No broker order path or TRADEGEN code belongs in this migration.
5. Keyboard/focus, resize/DPI, installer/icon and actual Windows visual acceptance;
   compare every native route with its retained Flet counterpart.
6. Only then change the default desktop launch/distribution instructions.

Do not remove or route unmigrated features to blank native placeholders. The
preview's scope notices identify where the Flet application is still required.

## Verification commands

```text
python -m unittest tests.desktop_acceptance tests.desktop_market_acceptance tests.desktop_strategy_acceptance tests.desktop_macro_acceptance tests.desktop_paper_acceptance tests.desktop_commentary_acceptance tests.packaging_policy_acceptance -v
python -m unittest tests.research_contract_acceptance tests.research_home_acceptance -v
```

Native fixture tests inject deterministic histories, prohibit network calls and
patch dotenv loading before importing core modules. They exercise all four
Monte Carlo models against direct engine results, currency-aware funding/fallback,
portfolio solvers, Bonds pricing/scenarios/hedge, Rates tool branches and bp/% conversions,
FX domestic/foreign rates, delta strikes and carry conventions, structured-note legs/hedges,
technical signals and costed backtests, macro observation units, six native workspaces, background delivery/duplicate exclusion,
failure redaction, explicit file export/cancel and close-during-work behavior.
The packaging workflow builds an allowlisted wheel on Windows/Linux and runs
`tools/packaging/smoke_desktop.py` **outside the checkout** with socket and protected
file access blocked. No live quotes, actual ledgers or frozen studies are tested.
An offscreen Windows test is not a manual Windows display/DPI acceptance result.

## Market tools and explicit analysis reports

The browser and native Derivatives/ETF/Crypto views now share their original computation
assembly in `core.research`; pricing functions and formal gates are unchanged. The Flet
ETF adapter retains its injectable history boundary and adjusted-close fallback. Native
ETF/Crypto requests do not read study-card stores by default; missing verdicts remain
NOT_LOADED. Crypto holdings are a separate explicit, read-only opt-in. KRX provider
refusals remain UNAVAILABLE and cannot be exported as completed calculations.

Successful ToolPane analyses offer JSON and ZIP reports with input snapshots, chart/table
sections, code/runtime evidence and a checksum manifest. These use the separate
`quantgen.analysis-report/1` format: official validation NOT_RUN, reproducibility PARTIAL,
data rights NOT_VERIFIED. They are not promoted into full ResearchRun records. Save is
explicit and atomic; cancellation writes nothing, failed reruns clear stale exports.

Portfolio and Bonds now export their numeric results, inputs and source evidence through
the same explicit report contract. Invalid requests and failed reruns clear stale reports.
System has a connection pane: presence is CONFIGURED/NOT_CONFIGURED; explicit probes
report REACHABLE/UNAVAILABLE. No probe runs when opening the app or selecting a tool;
credential values are excluded. Windows UTF-8 report reads are explicit in tests.

Strategy Lab shares the original seven family grids and cost/registration/scoring workflow
with Flet. Its native default is synthetic; real-data requests retain the existing
registration semantics. This migration does not implement the separate cumulative trial
registry redesign or change gate thresholds. Costs below the table floor keep WITHHELD,
registered cards retain their recorded refusals, and a failed registration blocks scoring.
Synthetic tests refuse network, actual ledgers and card-store reads.

Macro v2 uses native searchable record trees over the existing validated readers.
Missing/quarantined artifacts suppress calculation values and exports while retaining
alert, owner-input and separately validated calendar diagnostics. Formal verdicts
and dispositions remain distinct; no exposure is recomputed from design weights.
Dry/live actions and acknowledgement use existing prerequisites and stores only on
explicit clicks; acceptance tests inject fixtures and never execute actual stores.
Unavailable offline council documents are labelled rather than silently replaced.

Rules and paper controls share a lazy session: no rule/order store opens at desktop startup.
Blank financial inputs stay blank. Existing validation, revisions, confirmation, activation,
halt/acknowledgement and simulated fill/cancel behavior remain in the existing core.
Rule writes require disk read-back; stale edits and failed writes do not report success.
The editor requires disarming and completion of an in-flight tick before modifications.
A sidebar emergency stop remains available across all workspaces. Engine callbacks enter
the GUI through Qt signals; closing disarms/stops the loop and waits for an active provider
call. Tests use temporary rules/engine files and injected providers; no actual ledger is used.

## Optional AI commentary

Research Library lists completed calculation snapshots. Preview and a separate explicit
send action precede every request through the existing Anthropic backend. Opening the app,
navigating, calculating or preparing the preview makes no AI call. Connection settings,
Macro v2 owner records, Rules and paper stores are excluded; account/holdings sections are
removed from eligible reports. Questions and returned diagnostics are redacted for common
credential forms. Daily/weekly macro requests retain the existing report-format prompts.
Responses remain AI commentary, not gate results; errors clear stale response exports.
All acceptance responses are injected. No real API/key availability is claimed.

## Windows launch and remaining acceptance

After installing `.[desktop]`, run `Start-QUANTGEN-Desktop.cmd` from this checkout (or
`python -m quantgen_desktop`). The launcher selects the checkout `.venv` first, then the
existing `%LOCALAPPDATA%\QUANTGEN\venv`; it does not install dependencies or edit PATH.
Browser use remains `flet run main.py --web --host 127.0.0.1 --port 8550`.

CI proves an installed wheel starts outside the checkout and bounded fixture tests pass
on Windows Python 3.12/3.14 and Ubuntu 3.12. It is not a signed Windows installer or a real
monitor/DPI acceptance. Before treating this preview as the default replacement, check:

- Windows 100%, 125%, 150% scaling: six workspaces, sidebar, long record tables, keyboard focus.
- Light/dark mode, window resize, F1 taskbar icon and saved JSON/ZIP dialogs.
- Synthetic calculation and rule/paper flow; optional real providers only with valid user rights.
- Closing during a job keeps the window; closing an armed paper session stops its loop.
- Flet browser launch remains available independently.

Remaining external work: live-provider/AI acceptance, manual Windows visual/DPI verification
and any chosen standalone signed installer. These are not marked complete by offscreen CI.
