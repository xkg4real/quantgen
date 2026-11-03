# PR-D / PR-E — ResearchRun and connected A/F1 Home

## Implemented
The existing Quant Lab calculation now produces one session ResearchRun per attempted analysis. UI inputs are captured before the worker starts; effective clamped path/horizon and explicit seed 7 are recorded. Success and failure remain distinct; the formal verdict is always NOT_RUN in this observation adapter. No numerical model, cost resolver, official gate or ledger was changed.

The v1 contract records run ID, times, execution status, model/parameters, input observation hash/source/date range/adjustment, environment versions, code commit when available and a digest of the three named Monte Carlo/GARCH/history source modules. The working tree, input vintage, time-zone/calendar, redistribution rights and canonical execution instrument remain unverified where the original source provides no evidence. Reproducibility is therefore PARTIAL, never a universal readiness flag. Provider+original symbol is display identity only, not the pending PR-B tradable instrument/cost mapping.

The code digest is intentionally bounded to the three listed modules, not a claim of hashing the entire dependency closure. No protected data file or .env is read. `computation_fingerprint` excludes run IDs/times and detects changed recorded inputs/code/parameters; it refuses absent calculation provenance. It does not prove rerunnability without the original dataset and installed dependencies.

Explicit exports: canonical JSON (personal_research, order_capable=false), or ZIP with JSON, an escaped offline HTML evidence report and per-file SHA256 manifest. `payload_json` is canonical text so its checksum is portable across Python and JavaScript float serialization. The checksum is integrity, not sender authentication or a data-right grant. No raw observations, paths, broker/account/credential fields are exported.

Home displays current-session counts/recent runs, selected P5/P50/P95, assumptions and export actions. Returning Home updates results while preserving the analysis views and in-flight market refresh. Research Library lists session results. Session memory is not historical trial accounting; save exports before closing. Strategy Lab/frozen card histories are not silently imported.

Six market tiles use explicit existing FRED/Yahoo adapters with no synthetic fallback. Observation dates, unavailable/stale states, percent changes and Treasury basis-point changes are visible. The display is daily data, not live tick data; age >7 calendar days is a descriptive UI warning, not a revised research gate. First mount makes one background refresh; manual refresh has a session exclusion guard. A failed query does not promote a cached previous reading to fresh.

The A/F1 navigation retains 16 routes and provides three guided example directions without launching calculations or modifying their options on behalf of the user. Existing engine lifetime/rules invalidation remain intact.

## Actual checks
32 bounded source tests passed on Linux before integration, including a real seeded synthetic GBM calculation through the Quant Lab callback, failure recording, export roundtrip/tamper rejection, exact-date parity, symbol-provider fallback refusal, market units/staleness, stable computation identity, report hashes and navigation preservation. Initial packaging commit 1e4057e passed both Windows and Ubuntu CI: https://github.com/xkg4real/quantgen/actions/runs/40850241657 . Later integration commits require their own run.

Flet rendered at 1600x1200 and 390x844 with an actual synthetic Monte Carlo result and explicitly labelled FIXTURE market observations; engine/store hooks were inert. This is visual and binding evidence, not live provider evidence. The cloud's existing proxy returned HTTP CONNECT 403 for FRED and Yahoo; no policy was changed. The separate owner PC process cannot be restarted by this cloud checkout.

## Completion boundary
This is PR-D's first Monte Carlo schema/adapter/export and PR-E's connected personal Home. Full cross-model historical artifacts, validated canonical execution IDs (PR-B), data acquisition/vintage/legal verification, official-gate integration and reproducibility of real datasets remain separate open dependencies. No claim that all ⑬-1 requirements for a general research OS are finished.
