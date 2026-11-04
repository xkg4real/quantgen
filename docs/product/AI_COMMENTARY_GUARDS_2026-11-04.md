# AI commentary: stop reason, strict payload, number check and label (§10 NEW-M6-12, NEW-M6-19)

Model register entry 149 (M6-19, the AI commentary path) lists NEW-M6-12 and
NEW-M6-19 among its related errors. Claude fixed the four limitations of that
entry that carry no other ID, on product main `faf9f3b`, in three commits on
`claude/s10-ai-20261104`:

| Commit | Limitation | What changes |
| --- | --- | --- |
| `7c31417` | (c) the Messages API `stop_reason` was never read | A reply that did not end with `end_turn` fails closed; its text is never shown, saved or exported. |
| `401fe33` | (b) payload serialisation | Strict JSON, full arrays, non-finite numbers as markers that carry the field's meaning, one size limit for both UIs. |
| this note's commit | (a) the output is never checked, (d) the same request can give different text | An advisory number check and a "not verified" label under every finished reply. |

AI commentary stays advisory. No verdict, card, gate, ledger, register or study
harness is read or written; `core/quant/strategies.py`, `core/quant/validate.py`
and `docs/asset_expansion_study.py` are unchanged.

## Which ID is which: still ambiguous

- Both IDs appear only in the related-errors cell of entry 149
  (`2da6469:docs/nautilus_bridge/MODEL_LIMITS_REGISTER_2026-10-28.md:3454-3473`,
  summary row :452). The known-errors register lists both with no sentence.
- `docs/product/SECTION10_QUEUE_2026-10-30.json` marks both
  `mapping_needs_disambiguation: true` (:704-713 and :784-793 on `faf9f3b`).
  Neither ID is in the handoff `LEDGER.md`.
- The other IDs in that cell cover other limitations: D03-04 (no
  synthetic-disclosure rule), D03-01 (Crypto FX source), P01-13 (app import
  time) and NEW-M6-18 (Upbit holdings payload, done). None of them is touched here.
- That leaves four limitations for two IDs: (a) the output is never verified;
  (b) arrays are cut to 50 elements and NaN/Infinity go out as bare tokens;
  (c) `stop_reason` is never read; (d) the same input can give different output.
- The register's close method (MODEL_LIMITS:175) names (a) and (c). Reading the
  IDs as code defects with line citations gives {(b), (c)} just as well, so the
  earlier "12 = (a), 19 = (c)" hint is dropped.

Following Crypto PR #68 (NEW-M6-14 and NEW-M6-22), all four are fixed, so both
IDs are covered whatever the pairing. Both IDs are recorded against all three
commits; the owner maps them later.

## Reproduction on faf9f3b

No network and no real Anthropic call in any probe: socket connect raises,
`dotenv.load_dotenv` returns False, `ANTHROPIC_API_KEY` is removed, and
`core.quant.insights._requests` is a fake that returns canned Messages bodies.

Evidence: `probe_before_after.py` (run for this note) loads `core/quant/insights.py`
from `faf9f3b` as a separate module beside today's tree and sends the same canned
bodies and payload to both. The Flet and Native rows come from the earlier design
probes on `faf9f3b` (`s10ai2/design/probe_render_current.out`), read here, not re-run.

| Case | faf9f3b | After |
| --- | --- | --- |
| `max_tokens` with partial text | shown as success (text kept) | `OUTPUT_LIMIT`, no text |
| `max_tokens` with only a thinking block | `INVALID_RESPONSE` ("unreadable response") | `OUTPUT_LIMIT` |
| `refusal` with partial text | shown as success | `REFUSED`, no text |
| `refusal` with empty content | `INVALID_RESPONSE` | `REFUSED` |
| `pause_turn`, `tool_use`, `stop_sequence`, `model_context_window_exceeded` | shown as success | `INCOMPLETE_RESPONSE` |
| `stop_reason` missing or null, with text | shown as success | `INVALID_RESPONSE` |
| `end_turn` | success | success, `stop_reason = "end_turn"` |
| Flet, `max_tokens` partial | card shows `engine: …` and the cut-off text | error notice, no text |
| Native, `max_tokens` partial | "AI commentary complete", text saveable as a report | failure status, nothing to save |
| 120-element array | 50 sent (oldest kept) | 120 sent |
| `garch.nu = inf`, `adf_p = nan` | bare `Infinity`, `NaN`: not strict JSON | `"+inf: normal innovations (…)"`, `"NaN: not available or not defined"` |
| `np.int64(7)`, `np.bool_(True)` | `7.0`, `"True"` | `7`, `true` |
| Hangul string | `\u` escapes | UTF-8 characters |
| Tuple dict key | `TypeError` out of `deep_analysis`; Flet spinner stays on | sent as `"(1, 2)"` |
| A reply citing an invented 9.99 | shown with no check or label | shown unchanged, with the label and "not found in anything sent: 9.99" |

## Behaviour after the change

### (c) stop reason, commit `7c31417`

`core.research.ai_connection.reply_result(body)` classifies every HTTP 200 body in
this fixed order:

1. body not a dict, `content` missing or not a list, or a text block whose `text`
   is not a string: `INVALID_RESPONSE`;
2. `stop_reason` missing, null or not a string: `INVALID_RESPONSE`;
3. `refusal`: `REFUSED`, even when text came back; `stop_details` is provider text
   and is never read or shown;
4. `max_tokens`: `OUTPUT_LIMIT`, even when only a thinking block or nothing came back;
5. any other value except `end_turn`: `INCOMPLETE_RESPONSE` (`pause_turn`,
   `tool_use`, `model_context_window_exceeded`, `compaction`, unknown values, and
   `stop_sequence`, because QUANTGEN sends no stop sequences);
6. `end_turn` with empty text: `INVALID_RESPONSE`; otherwise success with
   `Analysis.stop_reason = "end_turn"`.

Every failure has empty text, `engine` = the model and no HTTP status, so no
"(HTTP 200)" suffix. One POST, no retry. The request is byte-identical apart from
reading `max_tokens` from `OUTPUT_TOKEN_LIMIT = 1500`.

| Surface | Cut-off, refused or paused reply |
| --- | --- |
| Flet (every page, `ui/ai_panel.py`) | The existing `_ErrorNotice` shows the new EN/KO message and re-renders on a language switch. The partial text appears nowhere. |
| Native (`quantgen_desktop/commentary.py`) | `finished()` routes to `failed()` with the Korean text; output and the report buttons stay cleared, so nothing can be saved. |

The `OUTPUT_LIMIT` message quotes the 1,500-token limit, says the limit can include
the model's internal reasoning, and does not blame the question.

### (b) payload, commit `401fe33`

`core.research.ai_payload.ai_payload_json(payload)` is now the only serialiser
for the AI request. It runs the NEW-M6-18 field filter first (unchanged), then:

- arrays, pandas `Series` and `DataFrame` are sent in full; pandas index labels
  are kept (`{"index", "values"}`, or `to_dict(orient="split")`);
- numpy integers stay integers, `np.bool_` becomes `true`/`false`; dates,
  datetimes, `pd.Timestamp` and numpy datetime64/timedelta64 scalars give the
  same strings as before;
- keys are written as `json.dumps` would write them (tuple and numpy keys no longer
  raise); a key that only appears after conversion (a DataFrame column, a dict
  inside an object array) is also dropped when it is a private field name;
- NaN, +inf and -inf become marker strings. Where the field's meaning is known
  (`NONFINITE_MEANINGS`), the marker says it, e.g. GARCH `nu = +inf` is
  `"+inf: normal innovations (the fitted Student-t degrees of freedom are at the
  normal limit, eta = 0)"`, not "unavailable". Other fields get a generic marker;
- `json.dumps(..., ensure_ascii=False, allow_nan=False)`: strict JSON, Hangul as
  UTF-8 characters rather than `\u` escapes.

When the payload carries a marker or a JSON null, the user message adds one
English `VALUE_NOTE` paragraph that explains the conventions. `_SYSTEM` is
byte-identical.

| Case | Before | After |
| --- | --- | --- |
| Serialisation fails | A tuple or numpy dict key raised `TypeError` out of `deep_analysis`; the Flet spinner stayed on | Such keys are now written as text. Any remaining failure is `PAYLOAD_INVALID` locally with nothing posted; the Flet worker also catches a failing `payload_fn` and always clears the spinner |
| Payload over 180,000 bytes | Flet: no limit; Native: refused at preview | `PAYLOAD_TOO_LARGE` before any request. `AI_PAYLOAD_MAX_BYTES` is shared, and both sides measure UTF-8 JSON with `ensure_ascii=False` and `>`, so a payload Native accepted at preview is never refused after consent |
| Native consent line | "Only this payload and question will be sent." | Says the payload and question are sent with QUANTGEN's fixed writing instructions, which contain no account or personal data (EN/KO pair replaced in `quantgen_desktop/translations.py`) |

### (a) and (d) number check and label, third commit

`core/research/ai_output_check.py` (pure: `re`, `math`, `dataclasses`)
compares the numbers cited in a finished reply with the JSON object that was
sent. It runs only after `end_turn`; if it raises, the reply is still shown with
`number_check = None` ("not run"). It never changes the text, an error code, the
payload or a verdict, and never blocks display.

- References: numeric leaves; strings that are a whole formatted number
  (`'2.345%'`, the ETF code `'122630'`); numbers inside other free-text strings
  (`'σ=27%'`), except marker strings and dates. Keys, `_SYSTEM`, the kind line and
  `VALUE_NOTE` never count.
- Numbers found only in the question text (the operator's question, plus the
  report-format instructions for the FICC report kinds) are listed apart, never as
  data.
- A number matches when it equals some reference after rounding to the printed
  decimals or truncation, with % as ×1 or ×100 and bp as ×1, ×100 or ×10,000. The
  sign is ignored. Matches with two significant digits or fewer are counted as
  "could match by chance".
- Dates, years, tenors and windows (10-year, 52주), ordinals and identifiers (5th,
  M6-19, 2y/5y), index levels (S&P 500, KOSPI 200), confidence levels (95% VaR),
  scale words (1.2 billion, 3억) and ranges (15-20%) are skipped.

| Surface | Finished reply |
| --- | --- |
| Flet | Under the unchanged `engine:` chip and text: a muted label line and the number-check line (`_CheckNotice`, EN/KO, re-rendered on a language switch). The error branch is unchanged. |
| Native | A new muted line under the output (`check_note`): the label and the check line, EN/KO. Cleared on a new source, a new request and a failure. The output box still holds exactly the reply text. |
| Native export | Two more text sections (English label and check line), and `stop_reason`, `verification: NOT_VERIFIED` and `number_check` in the request fields. `make_report` keeps `verdict: NOT_RUN`. |

Label (EN): "AI commentary · not verified. Claude wrote this from the data sent;
QUANTGEN does not check its reasoning, and the same request can give different
text. It does not change any official verdict." The label covers (d): on the
default model `claude-sonnet-5` (`config.py:224`) `temperature`, `top_p` and
`top_k` return a 400 (claude-api skill reference, not a real call), so the
non-reproducibility is disclosed, not removed.

What a match does not show: that the number is attached to the right measure
(a swapped "volatility 0.42, Sharpe 15.3%" still matches), its sign, a derived
number (a difference or ratio shows as not found), or verdict words. The line
says so.

Chance matches, measured on the three synthetic payloads with the final rules
(`probe_calibration.py`: each number cited alone, share that matches anything sent):

| Cited form | Crypto | ETF | Derivatives |
| --- | --- | --- | --- |
| Integer 1-99, no unit | 17% | 14% | 9% |
| 0.xx | 22% | 17% | 24% |
| x.x | 12% | 1% | 14% |
| x.x% | 17% | 10% | 26% |
| Integer bp 1-99 | 42% | 32% | 34% |
| x.xx (three significant digits) | 2% | 0% | 2% |
| xx.x% (three significant digits) | 5% | 2% | 12% |

So a match of a two-digit number is weak evidence; the line says how many matches
are that coarse. The Derivatives board (14,560 bytes) gives the most chance matches.

## What stays identical

- `_SYSTEM`, the request fields, one POST with no retry, the existing error codes
  and their EN/KO messages.
- The success rendering: Flet `engine:` chip and text, the Native output box and
  success status (`translations.py` success template untouched).
- For a payload with no None, no non-finite number, no numpy integer or bool, no
  array or pandas object, no bool or None key and only ASCII strings, the user
  message is byte-identical.
- Native `commentary_payload`, its preview, `plain()` (non-finite → null is the
  report contract), `make_report`, `report_bytes` and `verdict NOT_RUN`.
- `filter_analysis_fields` and `PRIVATE_WORDS` (NEW-M6-18).
- The Flet catalog (`core/ui_legacy_messages.py`) is not edited; its old consent
  pair is not displayed anywhere.

Measured on the synthetic payloads (no network):

| Payload | Change in the sent JSON | `VALUE_NOTE` |
| --- | --- | --- |
| Crypto (synthetic) | `garch.nu` → normal-innovations marker | yes (also one null, `funding.bootstrap_p`) |
| ETF 122630 (synthetic) | `letf.nu` → normal-innovations marker; `letf.name` and `sleeve_price_basis` as UTF-8 instead of `\u` escapes | yes (six nulls) |
| Derivatives (synthetic board) | `parity_check.within` `90.0` → `90` | no |

Quant Lab sends `prob_target_basis: None` whenever `mc.prob_target` is None
(`ui/quant_lab_page.py:372`), so it also gets the note then (read, not run).

## Owner choices (defaults taken)

1. Text cut off at `max_tokens`: discarded (`OUTPUT_LIMIT`). Alternative: show it
   under a "cut off at the output limit" banner, kept out of export.
   MODEL_LIMITS:175 means "mark it as cut off"; it does not require discarding.
2. `stop_sequence`: `INCOMPLETE_RESPONSE`. Accept it only if stop sequences are
   ever added to the request.
3. Output budget: `max_tokens` 1500, effort and thinking unchanged. Measure real
   truncation under ⑬-9/b first. Any thinking setting depends on the model
   (`thinking: {type: disabled}` is accepted on Sonnet 5 and a 400 on Sonnet 5.5
   and Opus 5.5).
4. Native consent text: reworded. Alternative: keep it and show `VALUE_NOTE` in
   the preview.
5. Number check: two significant digits or fewer counts as coarse; verdict words
   are not compared; ranges are not checked; the English and Korean skip lists
   above.
6. Native report nulls: `plain()` keeps turning non-finite values into null.
7. The Native crypto table shows GARCH `nu = +inf` as "—", so the Native AI payload
   loses "normal innovations" before `plain()` (read at
   `quantgen_desktop/market_tools.py:209` and `quantgen_desktop/tools.py:18-19`).
   Left to a separate task.
8. Flet label placement: a label line, no new chip.
9. Export language: the canonical report carries the English label and check
   line, like the existing "AI-generated commentary" line; a Korean ZIP shows them
   in English.
10. `VALUE_NOTE` trigger: markers or nulls, so most payloads that hold a None now
    carry the note. Alternative: a null-only sentence.
11. Pairing of NEW-M6-12 and NEW-M6-19: both IDs against all three commits.

## Unverified

- Every probe and test used fake HTTP; no real Anthropic call was made. How often a
  real reply stops at `max_tokens` (adaptive thinking on the default
  `claude-sonnet-5` counts against the 1,500 tokens) or at `refusal` is unknown;
  measure it under ⑬-9/b before changing the budget.
- The Messages API semantics used here (the `stop_reason` values,
  `model_context_window_exceeded`, `compaction`, `refusal` returning HTTP 200 with
  empty or partial content, `stop_details` only on refusal) come from the
  claude-api skill reference cached 2026-10-06, not from a real response.
- How the model reacts to the markers and `VALUE_NOTE` (whether it describes
  `nu = +inf` as normal innovations) is not tested.
- Payloads other than the synthetic Crypto, ETF and Derivatives ones (Quant Lab,
  Portfolio, Signals, rates, bonds, FX, structuring, macro, Strategy Lab) were
  read, not run, for arrays, pandas objects and non-finite values.
- The number check runs on the raw reply; Native shows and saves
  `safe_detail(text)`, which only redacts URLs and secrets, so the two can differ
  slightly when a reply contains such text (not measured).
- The Windows screen, real KIS/Upbit data and the bundled-font rendering of the new
  lines on screen were not checked; `tests.desktop_typography_acceptance` passes
  (it checks the glyphs of string literals in `core/research/*.py`).

## Checks

All offline: socket connect raises, `dotenv.load_dotenv` returns False, and the
HTTP layer is a fake. Run from the repository root with `PYTHONPATH=.` and
`QT_QPA_PLATFORM=offscreen`:

```
python -B -m unittest tests.ai_output_check_acceptance tests.ai_connection_acceptance \
  tests.ai_payload_acceptance tests.desktop_commentary_acceptance
```

New or changed tests:

- `tests/ai_output_check_acceptance.py` (new, pure, 10 tests): invented, rounded,
  scaled, Korean, free-text, code and question-only numbers; skipped and masked
  dates, tenors, windows, indices and ranges; the escaped-hyphen regex; coarse
  counts; truncated lists; EN/KO lines; no mutation.
- `tests/ai_connection_acceptance.py`: the stop-reason matrix, the three messages,
  the request fields, the success `stop_reason` and `number_check`, and a raising
  check that still succeeds. The two success fixtures gained `stop_reason: end_turn`.
- `tests/ai_payload_acceptance.py`: Flet cut-off notice, strict JSON with full arrays
  and markers, the synthetic Crypto and ETF `nu` markers, the size and
  serialisation refusals, the Flet spinner, and the Flet label and check line.
- `tests/desktop_commentary_acceptance.py`: Native refusal and thinking-only
  `max_tokens` through the real `core.ficc` runner, the shared size limit at
  179,999 / 180,000 / 180,001 bytes, the consent line, and the advisory label,
  check line and export fields.

These suites were also run on every commit and pass:
`letf_ai_payload`, `desktop_letf_ai`, `crypto_missing_values`, `option_disclosure`,
`etf_sleeve_disclosure`, `mc_bootstrap_disclosure`, `desktop_authored_prose_language`,
`desktop_language`, `desktop_typography`, `fx_basis_disclosure`,
`cms_coupon_disclosure`, `desktop_bonds_portfolio_language`,
`desktop_macro_language`, `forward_convention`, `letf_index`, `mc_volatility`,
`sabr_diagnostics`, `signals_trade_count`, `stock_profile`, `strategy_exposure`,
`terminal_target` (all `*_acceptance`), plus
`tests/ficc_acceptance.py::test_report_prompt_and_deep_analysis_degrade_without_network`,
`tests/quant_acceptance.py::test_deep_analysis_without_key_degrades_without_network`,
the four `tests.flet_api_guard` checks and the no-key path of `core.ficc.insights`
(engine `none`). `python -m core.ficc.insights` passes on the second and third
commits. `git grep -n "\"tools\"\|'tools'" -- core/quant/insights.py` stays empty
(the `tests/macro_m1_pit.py:1079` pin). Not run: `tests/macro_m1_pit.py`,
`tests.macro_m6_context` (it walks `docs/`, which holds a protected folder),
`tests.macro_m8_pipeline`, `tests.macro_m9_lab` and `tests/run_all.py`.

Records not edited here (the main session updates them): the SECTION10 queue and
triage, `docs/compliance/FACTS.md`, `docs/compliance/source-review.json` (new hashes
for the changed sources and entries for `core/research/ai_output_check.py` and
`tests/ai_output_check_acceptance.py`), `.github/workflows/runtime-smoke.yml`
(add `tests.ai_output_check_acceptance` to the module list and the new and changed
AI files to the paths), `docs/product/ui_website_updates/`, `qa/research_status.json`
and `README.md`.
