# A / F1 Research Home — bounded UI step ⑬-2/a

The application opens on Research Home with the selected ivory/deep-green A palette
and F1 Open Horizon symbol. Six workspaces group the existing 16 route keys.
All old pages remain available; their calculation code is unchanged. An engine/store
instance still outlives navigation; cached analysis views survive route changes and
resize; Execution still rebuilds on entry and Rules still invalidates its cached view.
The existing once-per-process macro startup hook is preserved, not duplicated.

## What is connected

System reads the bounded PR-A recorded evidence and refuses stale/invalid sources.
Research Home's recent runs, counts, market quotes, distribution and reports are
**not connected yet**. They explicitly show unavailable/unknown, never invented values,
zero counts or investment readiness. Existing analysis pages remain the place to run
calculations and inspect live data. The Home performs no provider query, simulation,
AI request or ledger scan. No ResearchRun backend or automatic data collection was added.
P5–P95 copy correctly says central 90% of the simulated distribution.

The six-workspace structure is implemented, but full PR-E includes data adapters and
workflow acceptance dependent on PR-D; it is not marked complete by this UI step.
Command palette/favorites, data-linked run comparison and every legacy page's narrow
mobile table layout are outside this bounded shell change.

## Verification

- `python -m unittest tests.status_snapshot_acceptance tests.research_home_acceptance -v`:
  15 PASS (9 status fixtures + 6 UI behavior checks). UI tests stub data views, engine,
  store and startup hook. Config dotenv loading is disabled during import.
- Existing `tests.flet_api_guard.tests()`: 4 PASS.
- Existing safety checks `test_14_page_resize_handler_matches_the_flet_api` and
  `test_15_views_are_cached_across_navigation`: 2 PASS.
- `python -m tools.status.snapshot --check`: consistent. Snapshot regenerated after
  cherry-pick because Claude's README differs from main; source QA remains byte-identical.
- Chromium/Flet 0.85.2 rendered actual Home controls at 1600×1200 and 390×844, including
  scrolling and the mobile menu. This uses `tools/ui/preview_home.py` inert fixtures,
  not a live calculation/engine acceptance run. No JavaScript page errors.
- The first render exposed missing Korean glyphs; a bundled renamed Noto CJK KR subset
  fixes them without a font download. F1 SVG and font requests returned HTTP 200.
  All 11,172 modern Hangul syllables are included; SIL OFL 1.1 is bundled.
- Muted text was darkened from the initial A token to #646E68 for >=4.5:1 contrast
  on the soft card background. Other A palette roles and existing dark/system API remain.
- The browser's optional Rive WASM CDN request failed with `net::ERR_CERT_AUTHORITY_INVALID`.
  This UI has no Rive control and rendered successfully. No TLS/proxy/security setting
  was changed; fully offline Flet-web packaging is not claimed.
- Matplotlib fell back to a temporary cache because the system home is read-only;
  this is not a project data-cache read. No global environment or dependency setting changed.

Run the safe preview from the repository root with `python tools/ui/preview_home.py`,
then open http://127.0.0.1:8767. Analysis routes are visibly inert fixtures in this preview.
Production launch remains `python main.py`; do not use production launch as an offline
smoke test because its existing startup hook and real stores are intentionally preserved.

Full suite, Windows packaging, actual provider/engine behavior and deployment are NOT_RUN.
No main push, PR creation/merge, release, TRADEGEN edit, frozen study, real ledger,
holdout, credential or protected-price-cache access is part of this change.

## Branch composition and rollback

The integrated UI branch starts from Claude work `0a91f265` plus roadmap `7f44f9f`,
then cherry-picks the separately reviewable main-based calendar/status changes:
`2ff977d` → `9d9262b`, `514e8ae` → `db575a4`, `98a645f` → `253e849`.
Revert only the UI commit to restore the previous shell; revert the earlier separate
changes independently if desired. Owner review/merge is still required before deployment.
