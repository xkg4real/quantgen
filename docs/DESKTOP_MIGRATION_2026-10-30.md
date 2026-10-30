# Native PyQt6 desktop migration — first verified slice

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
| Markets | Six existing daily observations, dates/provider/status and correct bp/% units; Bonds calculator, scenario revaluation and futures hedge | Other detailed asset pages remain in Flet; Bonds AI panel pending |
| Build & Test | All four existing Monte Carlo models, data source, seed, target, drift/ERP, percentile fan, loss risk and GARCH diagnostic notes | Stored model grades and AI commentary panel not migrated |
| Portfolio & Risk | Four existing objectives, weights/risk contributions, frontier, correlation, source/convention/convergence notices | Native portfolio export, Signals and paper-execution screens pending |
| Research Library | Session Monte Carlo results, native JSON and report ZIP save dialog | No persistent history browser; only explicit export |
| System | Existing bounded recorded-status verification, native theme switch | Credential editing and rule editor pending |

Both Monte Carlo and portfolio use the existing `core.quant` functions. New
`core.research.analysis` and `portfolio_analysis` adapters capture inputs before
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

1. Rates and FX: map the existing units, source warnings, partial-curve
   handling, all input branches and risk/chart outputs before porting controls.
2. Structuring, Derivatives, ETF and Crypto; preserve current models and labels.
3. Macro sheet and views, Strategy Lab and Signals. Preserve trial registration,
   gate/provenance semantics and approval boundaries; no live stores in tests.
4. KRX, paper-only Trading, Rules, Settings and the optional AI commentary panel.
   No broker order path or TRADEGEN code belongs in this migration.
5. Keyboard/focus, resize/DPI, installer/icon and actual Windows visual acceptance;
   compare every native route with its retained Flet counterpart.
6. Only then change the default desktop launch/distribution instructions.

Do not remove or route unmigrated features to blank native placeholders. The
preview's scope notices identify where the Flet application is still required.

## Verification commands

```text
python -m unittest tests.desktop_acceptance tests.packaging_policy_acceptance -v
python -m unittest tests.research_contract_acceptance tests.research_home_acceptance -v
```

Native fixture tests inject deterministic histories, prohibit network calls and
patch dotenv loading before importing core modules. They exercise all four
Monte Carlo models against direct engine results, currency-aware funding/fallback,
portfolio solvers, Bonds pricing/scenarios/hedge, six native workspaces, background delivery/duplicate exclusion,
failure redaction, explicit file export/cancel and close-during-work behavior.
The packaging workflow builds an allowlisted wheel on Windows/Linux and runs
`tools/packaging/smoke_desktop.py` **outside the checkout** with socket and protected
file access blocked. No live quotes, actual ledgers or frozen studies are tested.
An offscreen Windows test is not a manual Windows display/DPI acceptance result.
