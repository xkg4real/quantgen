# LA-01 fix: the NAV line close keeps both of its bindings

This is roadmap part **⑨-1/2/a**, the first fix from the 2026-11-04 look-ahead audit. The audit report is
`docs/nautilus_bridge/LOOKAHEAD_AUDIT_2026-11-04.md` at commit `7749450` on branch
`claude/lookahead-audit-20261104` (not on main); LA-01 is at its lines 261-277, and the reproductions are
`lookahead_evidence_2026-11-04/keys_binding.py` and `la01_nav_line.py` at the same commit.

The owner's ruling, verbatim from `docs/nautilus_bridge/OWNER_RULINGS_LOG.md:546` on main:

> L-2 = (가) 높음 2건(LA-01, LA-02)부터 별도 브랜치에서 수정 시작, 병합은 동결 해제 뒤 [권고]

The log maps L-1 and L-2 to ⑨-1 at line 553. The main freeze was lifted by ruling U4-나 on 2026-11-04.
Base: main `ed8df4a`. Branch: `claude/lookahead-la01-20261110`. LA-02 (the REFDATA point-in-time tests) is
not part of this change.

## Cause

`data/macro/series_registry.yaml` binds the group `NAV_LINE_CLOSES` (only `KRX_069500_OFFICIAL_CLOSE`, the
close of ETF 069500) twice, under the same consumer `nav`:

1. `acting_exposure` for `recommended` and `specification`, with `halt_after_consecutive_decisions: 3`;
2. `forward_sim` for `forward_sim:R-28` and `forward_sim:R-29`.

The spec requires both (QUANTGEN_MACRO_INTEGRATION.md L1891: "Roles are bound per (series, consumer, books),
never per series ... each with its own failure action").

`pit_snapshot` in `core/skills/macro_daily.py` stored one binding per `(series_id, consumer)` key. The loop
wrote `bindings[key] = b` for every binding, so the forward_sim binding overwrote the acting one. Reads were
correct (they resolve to the acting binding), but the two readers of the stored binding were not:

- `data_ok` passed the stored binding to `on_input_failure`. A missing NAV close became a forward_sim failure
  only. Neither KR book failed closed, no counter advanced, and no HALT followed.
- `lag_audit` built the series' roles from the stored bindings and saw only `forward_sim`. A look-ahead
  violation on the NAV close therefore took neither the acting branch (OPS HALT plus a page) nor the
  risk-model branch.

A static enumeration in the audit (keys_binding.py) found this to be the only `(series, consumer)` collision
in the shipped registry. In a US decision the series is never read.

## Fix (core/skills/macro_daily.py only)

1. `pit_snapshot` keeps every binding of a key as a tuple: `bindings[key] = bindings.get(key, ()) + (b,)`.
   The inputs dict, its keys and its values are unchanged (`inputs[key] = v`).
2. `data_ok` applies each binding's own failure action. For the NAV close:
   - The acting binding adds both KR books to `failed_by_book` with limit 3, adds one `fail_closed`
     component naming `recommended:KR` and `specification:KR`, and raises `ACTING_INPUT_FAIL_CLOSED`.
   - The forward_sim binding still lists the close under `forward_failed` for R-28 and R-29 and raises
     `FORWARD_SIM_INPUT_FAIL_CLOSED`.

   `INPUT_DISPUTED` is raised at most once per `(series, consumer)` key. Its book list is the union of the
   key's bindings' books, in binding order. Without this, a disputed NAV close would raise two alerts that
   share one `macro_state` alert id (the id does not include the books).
3. `lag_audit` takes the union of roles over every binding of a key.

Not changed: the key shape, `data/macro/series_registry.yaml`, `data/macro/rules_v2.0.0.json`, the rules
store, `core/ficc/contracts.py` and every other module.

### Rejected alternatives

- Storing only the resolved (acting) binding would drop the forward_sim action that L1891 requires, and
  `extras.forward_failed` would change.
- Putting the role in the key would change the key shape. That breaks the injection in
  `tests/macro_m8_pipeline.py` (`ctx.state["inputs"][("KOSPI_OFFICIAL_CLOSE", None)]`) and would list the
  NAV value twice in the lag audit.
- Changing the registry consumer is ruled out: the registry is cross-checked against the rules store's
  `data_contracts.roles`, and the spec requires consumer `nav`.

## Runtime behaviour, before and after

The cases below are a live KR decision on a synthetic store, built as the audit's la01_nav_line.py builds it.
Each was run on `ed8df4a` and on the fix with a scratch probe script that is
not committed.

| Case | ed8df4a | After the fix |
| --- | --- | --- |
| NAV close absent on 3 consecutive KR decisions (2026-09-30, 10-01, 10-02) | `data_ok` pass, `fail_closed` empty, NAV in `forward_failed` for R-28 and R-29, `macro_state.fail_closed` false, both KR books ARMED | `data_ok` fail_closed with one component `{KRX_069500_OFFICIAL_CLOSE, [recommended:KR, specification:KR]}`, NAV still in `forward_failed` for R-28 and R-29, `macro_state.fail_closed` true. Both KR books ARMED after decisions 1 and 2 and HALTED at decision 3, class OPS, reason `acting_input_stale:KRX_069500_OFFICIAL_CLOSE` (halt_after 3, not the default 2). US books ARMED |
| Last NAV close stamped available_at 06:00Z, before its 06:30:30Z publication bound | `lag_audit` fail with violation `available_at_utc >= publication_instant`, `halted` empty, no alert, books ARMED | Same violation, `halted == [recommended:KR, specification:KR]`, both HALTED with class OPS, reason `lag_audit_violation`, rearm_mode operator, and one `LAG_AUDIT_VIOLATION` page alert naming both books. US books ARMED |
| NAV official close disputed by a vendor close (stock tolerance: exact) | One `INPUT_DISPUTED` naming only `forward_sim:R-28`, `forward_sim:R-29` | One `INPUT_DISPUTED` naming `recommended:KR`, `specification:KR`, `forward_sim:R-28`, `forward_sim:R-29`. A dispute is not a failure: books ARMED, `data_ok` pass |

On "late" stamps: the audit's case is an `available_at` earlier than the publication instant, which claims
availability before the close could have been published. That is the look-ahead violation `lag_audit` exists
to catch. From reading `pit_value`, a row stamped after the decision instant is invisible to the read, so for
an acting close it becomes a missing input, which is the first row above. That second statement comes from
reading the code and was not run as a separate case.

## What is unchanged

- **Healthy inputs.** A scratch script (not committed) runs `kr_store()` (every input fresh, NAV rows
  included) through three KR decisions and one US decision. It records all 32 artifacts, every step result,
  the run halts, `forward_failed`, the 20 alert-store rows and the book modes. On `ed8df4a` two runs were
  byte-identical. Between `ed8df4a` and the fix, the only differences are the 32 `provenance.tree_hash`
  values. That field is the sha256 of `core/**/*.py`, so any source edit changes it by construction. Nothing
  else differs.
- `test_replay_01_reproduces_the_artifacts_byte_for_byte` passes after the fix.
- Gate package and card surface: `core/skills/macro_daily.py` is not in `HARNESS_SOURCES`
  (`core/quant/gate_package.py`), so no gate-package change. No card, card verdict, ledger, register,
  frozen study, golden, `tests/macro_registry.csv`, `data/macro/*` or `qa/acceptance_results.json` changes.
- No recorded research number or verdict changes. Only the failure-path classification of the daily
  runtime changes.

## Regression test

`tests/macro_m8_pipeline.py::test_la01_nav_line_close_keeps_the_failure_action_of_each_binding` sits after
the T-SCOPE-01 (e)/(f) block, away from the I-01 dry-run block. It builds its stores synthetically from
`_kospi_store`, `kr_rows(nav=False)`, `_close_row(..., available=...)` and `_hedge_store`, and asserts the
three "after" columns above.

It carries no `test_ids`, so `tests/macro_registry.csv` and its T-HERM-01 sync are untouched. As a result,
`tests/run_all.py --milestone Mk` does not select it, because that selection goes by `test_ids`. Plain
`run_all` and `python -m tests.macro_m8_pipeline` do run it. Tagging it T-LAG-01 and T-ROLE-01 would need the
registry sync; that is left for the owner to decide.

Red and green, both through a guarded single-test runner (below):

- With only the test added (core identical to `ed8df4a`): **FAIL** at the first assertion, because `data_ok`
  status was `pass` with an empty `fail_closed`.
- With the fix: **PASS** (1 test, about 2 s).

## Verification run (local Linux, Python 3.13 venv)

Every run went through a runner that installs `sys.addaudithook` before importing the repository. The hook
refuses any `open`, `os.listdir` or `os.scandir` of a path containing `asset_expansion/cache`, any `.env`
file and `~/.nextgen`, and refuses every `socket.connect`. Each named test function is wrapped in
`unittest.FunctionTestCase`. The guard was self-tested first: it refused a fake `asset_expansion/cache` path
and a loopback connect. It made 0 refusals in every run below.

- New test: FAIL on `ed8df4a`, PASS after the fix.
- `tests.macro_m8_pipeline`: the 20 named test functions other than the I-01 dry run (which reads the vendor
  cache) and `test_i01_golden_clauses_refdata` (NOT_RUN, REFDATA). 20 of 20 OK, about 20 s.
- `tests.macro_m8_integration`: all 3 test functions, by name. 3 of 3 OK.
- `tests.macro_m6_context::test_ctx_01_static_import_scan_and_positive_controls`: OK.
- Probe and healthy-output comparison as described above.
- `python -m tools.compliance.check --check` failed before the refresh, as expected for changed sources.
  After `--refresh-baseline --documents 1..20` (reviewer "Claude la01 review") it reports consistency PASS
  and publication BLOCKED. The FACTS section is `docs/compliance/FACTS.md#lookahead-la01-2026-11-10`.

## Unverified

- **Live runs on the owner's PC** (Windows, real KR data and ingest): not run. Per the audit (LA-03), live
  ingest is not yet connected, so every live acting input already fails closed. The audit's view, which is an
  inference, is that the net live effect today is nil. That is not verified here.
- **Full module and suite runs:** `python -m tests.macro_m8_pipeline` and `tests/run_all.py` were not run.
  They need the cache-free harness copy, because the I-01 dry run reads `DRY_RUN_CACHE`.
- Not run: the T-RO-01 static scans and the T-HERM-01 registry test (`tests/macro_m0_harness.py`), and
  `tests/macro_m9_scenarios.py` (it imports `tests.macro_m9_lab`). The change adds no import, call or test
  id, so they should be unaffected; that is a reading, not a run.
- **CI:** neither workflow runs the macro suites. `runtime-smoke.yml`'s path filter does not list
  `core/skills/macro_daily.py` or `tests/macro_m8_pipeline.py`. Only the compliance review runs on the PR.
- **Merge with the Step 7A research branch,** which edits other parts of `tests/macro_m8_pipeline.py`: not
  attempted.
- **The halt order on the owner's PC:** the test asserts `[recommended:KR, specification:KR]` from the
  synthetic store. Real stores with more failing inputs could add other components and alerts.
