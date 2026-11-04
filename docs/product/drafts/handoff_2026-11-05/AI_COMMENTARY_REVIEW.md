# §10 AI (NEW-M6-12, NEW-M6-19) 설계·반박·구현·검토 기록

> **상태: 미검증 초안 (handoff 자료).** 2026-11-05 Claude 세션이 주간 사용량 한도로 멈출 때 백그라운드 워크플로 결과를 그대로 옮겼습니다.
> 소유자 승인 전이며, 3관점 검토 중(constraints 검토 미완) 수정(Fix) 단계 전에 멈췄습니다. 본문의 `/tmp/claude-0/...` 경로는 그 세션의 임시 폴더라 이제 열 수 없습니다.
> 이 폴더는 main에 병합하지 않습니다. 확정본은 새 PR에서 `docs/product/` 아래 정식 문서로 만듭니다.


구현 커밋은 `claude/s10-ai-20261104` 브랜치의 7c31417, 401fe33, 54b52eb입니다.

## 검토 지적 (2관점 완료: correctness, surfaces)

### correctness

- **blocker** `core/research/ai_output_check.py:60` The number check treats the day in a 'D Month YYYY' date ('27 October 2026') as a cited number. The 'Month YYYY' mask (line 60) runs before the 'D Month' mask (line 61) and blanks the month, so 'D Month' never matches. The day then shows up in the check line as 'not found in anything sent', or is counted as a chance match.
  - evidence: Probe /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/s10ai2/review_correctness/p8_dates.py, output p8_dates.out, against the synthetic crypto payload:
- 'Dated 27 October 2026.' gives cited=['27'], not_found=('27',).
- 'Week ending 31 October 2026' gives not_found=('31',).
- 'As of 3 November 2026, the 10y yield is 4.12%.' gives cited=['3', '4.12%'], with 3 counted as coarse.
- These forms are masked correctly: 'As of November 3, 2026', '3rd November 2026', 'On 3 November'.

This is a realistic case. REPORT_PROMPTS (core/ficc/insights.py:568-594) tell the model to 'Date the note to as_of', and _SYSTEM asks for a journal-style register, so a date written as '3 November 2026' is likely. The spec requires a 'D Month' mask, and docs/product/AI_COMMENTARY_GUARDS_2026-11-04.md:149-151 says dates are skipped. No test covers the 'D Month YYYY' form.

Suggested fix: move a mask like \b\d{1,2}\s+(?:MONTHS)\.?(?:\s+\d{4})?\b before the 'Month YYYY' pattern, and add test cases.
- **major** `core/research/ai_output_check.py:74` The % scales cover only x1 and x100, so a field the payload holds in bp and the reply quotes in percent is never matched, while the reverse direction (% field quoted in bp) is matched. A correct conversion is then listed as 'not found', with the hint that it 'may be derived (a difference or a ratio)', which is not what a unit conversion is.
  - evidence: Probe p6_check_edges.py, output p6_check_edges.out:
- ETF letf.rows drag_bp -662.79 quoted as '-6.63%' gives not_found=('6.63%',); quoted as '-662.8 bp' it is found.
- ETF variance_bp -598.79 quoted as '5.99%' gives not_found.
- Derivatives hedge.cvar95_bp -84.54 quoted as '-0.85%' gives not_found=('0.85%',).

_SYSTEM tells the model to 'quote rates in percent', and the payloads carry many *_bp fields (ETF drag_bp, variance_bp and fee_bp; derivatives mean_pnl_bp, cvar95_bp and mispricing_bp), so the model is likely to convert them.

This follows the spec's '% uses {1, 100}' rule; it is a gap in the spec, not a departure from it. Fix: add a 0.01 scale for '%' (bp-valued references), and re-measure the chance-match rates.
- **major** `core/research/ai_output_check.py:119` Only '-' and '–' are treated as range separators. In the standard Korean range form '15~20%', and in 'from 15 to 20%', the first bound is checked as a bare number with no % scaling. It is reported as not found even when the matching fraction was sent, although ranges are meant to be skipped.
  - evidence: Probe p7_tokens.py, output p7_tokens.out, with payload {'vol': 0.153, 'q': 0.15, ...}:
- '변동성은 15~20% 범위입니다.' gives cited=['15', '20%'] and not_found=('15',). 15 is compared with scale {1} only, so 0.15 never matches.
- 'Korean range 15~20% and 0.38~0.47.' counts all four bounds.

The product note (docs/product/AI_COMMENTARY_GUARDS_2026-11-04.md:151) and the spec say ranges are skipped. Line 119 skips only a '-' or '–' immediately after the number.
- **minor** `core/research/ai_output_check.py:67` Scientific notation written with a multiplication sign ('3.04 × 10⁻⁸') is parsed as '3.04' with unit '×' plus a bare '10'. Both are listed as not found, although the reply quotes the sent ADF p-value 3.04e-08 correctly. Unit spellings 'pct' and '베이시스 포인트' (with a space) are also not recognised.
  - evidence: Probe p6_check_edges.out, against the crypto payload with kimchi.adf_p 3.0387e-08:
- 'The ADF p-value is 3.04 × 10⁻⁸.' gives not_found=('3.04 ×', '10').
- 'Volatility is 15.3 pct.' against 0.153 gives not_found=('15.3',).
- '스프레드는 8 베이시스 포인트' against -0.0008 gives not_found=('8',).

The '3.0e-08' form is skipped correctly.
- **minor** `core/research/ai_output_check.py:259` The wording 'not found in anything sent' (and the KO '전송한 내용에서 찾지 못한') claims more than the check does. Keys, _SYSTEM, the kind line and VALUE_NOTE are all sent but never searched, so a number that occurs only in a key is reported as absent from everything sent.
  - evidence: Probe p10_keys.py, output p10_keys.out: payload {'cvar95_bp': -84.53}, reply 'The CVaR at the 95% level is -84.5 bp.' gives the line 'Number check (2 checked): not found in anything sent: 95%.', although '95' was sent in the key cvar95_bp. Leaving keys out matches the spec; the issue is only the wording ('in the values sent' would be accurate).
- **minor** `core/research/ai_output_check.py:17` The commit message of 54b52eb says the new module uses 're, bisect, math, dataclasses'. The module imports only re, math and dataclasses and uses a hand-written binary search.
  - evidence: git log 54b52eb: 'new pure module core/research/ai_output_check.py (re, bisect, math, dataclasses)'. core/research/ai_output_check.py:17-19 imports math, re and dataclasses, and line 177 defines _first_at_least. The module docstring at :3 correctly says 're, math and dataclasses only'.

검토 범위: Worktree /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/s10mc, commits faf9f3b..54b52eb (7c31417, 401fe33, 54b52eb). I read the full diff of all 12 files. Every probe ran with the no-network guard, socket connect raising, load_dotenv returning False, and a fake _requests. No real API call was made, and nothing under docs/asset_expansion/cache was touched.

One slip: my first payload probe (p3) wrote four files (crypto.json, etf.json, derivatives.json, payloads.pkl) into the s10mc worktree root, because I used relative paths with s10mc as the working directory. They were untracked files that I had just created, and I deleted them straight away; 'git status --short' was empty afterwards, and before and after every later probe. All other probe outputs are under /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/s10ai2/review_correctness/.

(c) stop_reason (p1_stop.out): I re-derived 32 body shapes plus a resp.json() that raises. All classify as the spec says:
- end_turn, with or without thinking or redacted_thinking blocks: OK.
- max_tokens with text, thinking only or []: OUTPUT_LIMIT.
- refusal with text or []: REFUSED, and stop_details text is not echoed.
- pause_turn, tool_use, stop_sequence, model_context_window_exceeded, compaction, unknown values and 'END_TURN': INCOMPLETE_RESPONSE.
- stop_reason missing, None or 42, and malformed bodies: INVALID_RESPONSE.
- Every failure has text '', http_status None, no 'HTTP 200' suffix, engine = model, and exactly one POST.

The claude-api skill reference (cached, not a live call) agrees on these points:
- refusal comes back as HTTP 200 with empty or partial content, and the partial output should be discarded;
- stop_details is set only on refusal;
- on Sonnet 5, omitting thinking runs adaptive thinking, and max_tokens caps thinking plus text;
- temperature, top_p and top_k return a 400 on Sonnet 5;
- model_context_window_exceeded and compaction are real stop reasons.

(b) Serialiser (p2_ser.out, 40 cases): no defect found.
- NaN, +inf and -inf (Python, np.float32/64 and inside ndarrays) become markers, and the registry meanings attach at the right (parent, field) paths: garch, letf, kimchi, ethbtc, premium_stats, nested lists, dataclasses.
- np.int64, np.uint64 and np.bool_ are handled; dt64 and td64 scalars and arrays become strings; masked and object arrays work.
- pandas Series, DataFrame (private columns dropped), Index, DatetimeIndex and categorical are handled.
- Tuple, numpy, bool, None and float keys work. Decimal, pd.NA, NaT, Timedelta, set, bytes and complex fall back to str, as before.
- The output is always strict JSON, and a clean payload gives byte-identical text to the old serialiser.
- Synthetic payload sizes (p3_payloads.out): crypto 4,206 B, ETF 4,396 B, derivatives 14,560 B. No array was cut before, apart from a 118-row list, so the 180,000-byte limit is not near.
- I checked every registry path against the payload builders (crypto_workflow.py:58-61 and :211-219, etf_workflow.py:75-77, :152 and :218, ui/quant_lab_page.py:381-397). Every GARCH fit uses dist='t', so the 'Student-t at the normal limit' wording is never shown for a normal fit.

(a)/(d) number check (p4_check.out, p6, p7, p8, p10):
- Faithful EN and KO answers on the synthetic crypto and ETF payloads gave no false not-found, apart from KO '58백분위'.
- Fabricated EN and KO numbers were all not found.
- Thousands separators, signs, %/bp/x100 scaling, Korean particles, years, tenors, ordinals, index levels, VaR and confidence levels, scale words and hyphen ranges behaved as specified.
- The defects reported above were the exceptions.

UI and tests:
- Flet _CheckNotice and the PAYLOAD_INVALID/finally path; Native check_note, its clearing, the export fields and the consent text; the label helper wraps. All read.
- 84 tests pass (p5_tests.out): ai_connection, ai_payload, desktop_commentary, ai_output_check, letf_ai_payload, desktop_letf_ai, desktop_language, desktop_typography, etf_sleeve_disclosure and fx_basis_disclosure acceptance. I grepped each module for cache use first.
- The function pins (ficc and quant no-key degrade, the 4 flet_api_guard checks) pass (p9_pins.out).
- The 'tools' grep pin is empty. Frozen and shared record files are unchanged.

Unverified: the real model's output formats and the real frequency of each stop reason; the payloads I did not run (Quant Lab, Portfolio, Signals, rates, bonds, FX, structuring, macro, Strategy Lab); on-screen rendering.

### surfaces

- **major** `core/research/ai_output_check.py:259` The number-check line says a number was "not found in anything sent" (KO: "전송한 내용에서 찾지 못한 숫자"). But the only references are JSON values (walk() at :150-151 reads o.values()). Numbers the app sent in key names, in _SYSTEM, or in the kind line are therefore reported to the user as never sent. This misleads in Flet, in Native and in the exported report.
  - evidence: Probe /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/s10ai2/review_surfaces/probe_text.py, output in probe_text.out [1]. It sends a Quant-Lab-like payload with keys "p05", "p95" and "garch":{"uncond_vol_365"}; the probe printed 'sent contains p05/p95/uncond_vol_365 keys: True'. The reply cites 'The 5% and 95% terminal quantiles ... annualised over 365 days'. The result is NumberCheck(checked=7, not_found=('5%', '95%', '365'), ...). EN line: 'Number check (7 checked): not found in anything sent: 5%, 95%, 365.' KO line: '전송한 내용에서 찾지 못한 숫자: 5%, 95%, 365.' 95 and 365 appear verbatim in the JSON that was sent. _SYSTEM (core/quant/insights.py:303, '3–6 short paragraphs') and kind names such as 'kospi200_derivatives' are also sent but are never references. The product note itself says 'Keys, _SYSTEM, the kind line and VALUE_NOTE never count' (docs/product/AI_COMMENTARY_GUARDS_2026-11-04.md:140-141). The user-facing sentence at :259-260 (EN) and :248-249 (KO) claims more than that. The not-found caveat at :262/:251 ('may be derived') does not cover this case. The fix is either wording such as 'not found in the calculation values sent' / '전송한 계산 값에서 찾지 못한 숫자', or counting digits in key names.
- **major** `quantgen_desktop/commentary.py:118` Commit 2 reworded the consent line because 'only this payload and question are sent' was not accurate. The status shown when the user presses send without consent still says '아래 내용만 외부 AI 서비스로 전송됩니다' ('only the content below is sent'). That contradicts the new consent text at :105 and translations.py:545. It also has no EN pair, so EN mode shows Korean.
  - evidence: probe_native.out, from /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/s10ai2/review_surfaces/probe_native.py with ctx and ui_language switched together. '[consent status after prepare] en: "This payload and your question are sent with QUANTGEN's fixed writing instructions..."'. Then '[submit without consent (:118)] en: '전송 동의에 체크해야 요청할 수 있습니다. 아래 내용만 외부 AI 서비스로 전송됩니다.'', and the same text in ko. What is actually sent besides the previewed payload: _SYSTEM, the kind line, REPORT_PROMPTS for macro, and VALUE_NOTE whenever the plain()-ed Native payload holds a null. The '[sent user message]' in the probe shows the extra framing. git grep finds the string only at commentary.py:118, with no translations.py pair. The line is unchanged since faf9f3b:quantgen_desktop/commentary.py:113, so it is a surface the consent rewording missed.
- **minor** `quantgen_desktop/commentary.py:134` Native shows and saves safe_detail(result.text), which redacts URLs and key=value secrets. The check note, however, comes from number_check on the raw reply (core/quant/insights.py:369). It can therefore list numbers that do not appear anywhere in the displayed commentary.
  - evidence: probe_text.out [2]. The reply is 'Source https://fred.stlouisfed.org/graph/?id=DGS10&cosd=7731 shows the 10y at 4.25%.'. Native output: 'Source [provider URL redacted] shows the 10y at 4.25%.'. Check line: 'Number check (2 checked): not found in anything sent: 7731. ...'. The number 7731 exists only inside the redacted URL. The export section passes through plain() and safe_detail, but the on-screen check_note (:136-138) does not. The implementer listed this case as unverified; this probe reproduces it.
- **minor** `core/research/ai_output_check.py:267` EN subject-verb agreement is wrong when exactly one match is coarse: '1 of the matches have two significant digits or fewer'.
  - evidence: probe_flet.out ('success EN') and probe_ko_spacing.out both print 'Number check (...): ... 1 of the matches have two significant digits or fewer and could match by chance.' The string at :267 is f" {check.coarse_found} of the matches have ..." with no singular form. The KO line at :256 has no such problem.
- **minor** `core/research/ai_output_check.py:28` The KO label 'Claude가 전송한 데이터로 쓴 글이며' most naturally reads as 'written from the data that Claude sent', which reverses who sent the data. EN says 'Claude wrote this from the data sent' (QUANTGEN sent it).
  - evidence: AI_LABEL['ko'] at :28-29 reads 'AI 해설 · 검증 안 됨. Claude가 전송한 데이터로 쓴 글이며 QUANTGEN은 그 논리를 확인하지 않습니다.' The subject 'Claude가' sits right before the relative clause '전송한', so the adjacent parse is 'data Claude sent'. A wording that keeps the EN meaning: '전송한 데이터를 바탕으로 Claude가 쓴 글이며'. This is a reading judgement and was not tested with users. The string is shown on both Flet (probe_flet.out) and Native (probe_native.out check_note ko).
- **minor** `quantgen_desktop/commentary.py:39` The diff points this line at the shared AI_PAYLOAD_MAX_BYTES, but its refusal is still English-only and does not name the limit. The send side's new bilingual PAYLOAD_TOO_LARGE ('180,000-byte limit' / '전송 한도(180,000바이트)') describes the same limit, so one limit gets two different explanations, and Korean users see English.
  - evidence: probe_text.out [3]: 'prepare refusal ko: Report is too large for commentary; choose a smaller calculation' (identical in en). git grep finds no translation pair for that string. The new message is in core/research/ai_connection.py MESSAGES['PAYLOAD_TOO_LARGE']; probe_flet.out 'too large' shows it in both languages. The product note (:127) presents this as 'one size limit for both UIs'. The string itself predates this diff.
- **minor** `core/research/ai_output_check.py:125` The Korean skip rules match only when the unit word directly follows the number (tail.startswith). With standard spacing, such as '20 거래일', '3 개월' or '3 억', the number is counted and listed as not found. English '20 sessions' and '3 months' are always counted. The same commentary therefore gets a different check line depending on its language and spacing.
  - evidence: probe_ko_spacing.out. '최근 20거래일 ...' gives checked 1, not_found () and skipped 1. '최근 20 거래일 ...' gives checked 2 and not_found ('20',). '3개월' is skipped, but '3 개월' gives not_found ('3',). '3억 원' is skipped, but '3 억 원' gives not_found ('3',), which lists a scale-word number as missing. 'Over the last 20 sessions' and 'Over the last 3 months' both list 20 and 3 as not found. The rules are at :125-129: tail = src[stop:] with no allowance for the space that the unit-matching code at :106 permits.

검토 범위: I reviewed git log and git diff faf9f3b..HEAD in /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/s10mc: commits 7c31417, 401fe33 and 54b52eb, 12 files. My lens was surfaces and language. The worktree is unedited: git status was empty after every probe. Probes and outputs are in /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/s10ai2/review_surfaces/: probe_native.py, probe_flet.py, probe_text.py and probe_ko_spacing.py, with matching .out files. All ran under guard/sitecustomize.py: socket connect raises, load_dotenv returns False, the API key is removed, and .env and the cache folder are refused. HTTP was a Mock that returned canned Messages bodies; no real API call was made.

Verified by running:

Flet (ui/ai_panel.py, the real deep_analysis and the FICC wrapper):
- These codes show a bilingual _ErrorNotice that re-renders on ko_KR, en_US and back: OUTPUT_LIMIT, REFUSED, INCOMPLETE_RESPONSE (pause_turn), PAYLOAD_INVALID (payload_fn raises) and PAYLOAD_TOO_LARGE.
- No partial text is shown and there is no 'HTTP 200' suffix.
- The spinner clears in every case, and no POST is made for payload failures.
- On success, the engine chip and text are unchanged, and the label and check line appear below them in EN and KO.
- For the weekly report, the REPORT_PROMPTS '252' is listed as question-only.

Native (quantgen_desktop/commentary.py):
- The reworded consent pair translates in both languages.
- check_note switches between EN and KO through localized_text.
- max_tokens and PAYLOAD_INVALID clear the output, the check note and the report.
- 'AI 해설 실패 · …' shows in KO and 'AI FAILED · …' in EN.
- Export sections and params carry stop_reason, verification NOT_VERIFIED and number_check, and verdict stays NOT_RUN.
- The KO ZIP shows the label and check line in English, which is owner choice 9 and is not reported.

Tests: 11 modules, each grepped first for cache access (0 hits), ran 93 tests, OK. The modules were ai_connection, ai_payload, desktop_commentary, desktop_letf_ai, letf_ai_payload, desktop_language, etf_sleeve_disclosure, fx_basis_disclosure, desktop_typography, ai_output_check and desktop_authored_prose_language (all *_acceptance). Every AI rendering path found by git grep goes through ui/ai_panel.py or quantgen_desktop/commentary.py.

Read only, not run, so unverified:
- Payloads on the other Flet pages (Portfolio, Signals, Rates simulation, Structuring, Quant Lab). They hold Python lists and scalars, which were never cut to 50, so removing the cut should not change their size.
- Real-model behaviour, the Windows screen and font rendering.

## 구현 보고

```json
{
 "commits": [
  "7c314170b43332af585625c9f85a164beeb645f6 Check the Messages API stop reason before AI commentary is shown (§10 NEW-M6-12, NEW-M6-19: limitation c)",
  "401fe33db414ae105f9487dc4fbd603aacb7e61d Send AI payloads as strict JSON with full arrays and meaning-bearing non-finite markers (§10 NEW-M6-12, NEW-M6-19: limitation b)",
  "54b52ebf5f460dbbbe12382563db58950db53f2c Label AI commentary as not verified and add an advisory number check (§10 NEW-M6-12, NEW-M6-19: limitations a and d)"
 ],
 "files_changed": [
  "core/quant/insights.py",
  "core/research/ai_connection.py",
  "core/research/ai_payload.py",
  "core/research/ai_output_check.py (new)",
  "ui/ai_panel.py",
  "quantgen_desktop/commentary.py",
  "quantgen_desktop/translations.py",
  "tests/ai_connection_acceptance.py",
  "tests/ai_payload_acceptance.py",
  "tests/desktop_commentary_acceptance.py",
  "tests/ai_output_check_acceptance.py (new)",
  "docs/product/AI_COMMENTARY_GUARDS_2026-11-04.md (new)"
 ],
 "tests": [
  {
   "module": "baseline faf9f3b, before any edit: 24 modules listed below except ai_output_check",
   "ran": 207,
   "result": "OK"
  },
  {
   "module": "commit 1 (7c31417): same 24 modules",
   "ran": 211,
   "result": "OK"
  },
  {
   "module": "commit 2 (401fe33): same 24 modules",
   "ran": 217,
   "result": "OK. After 3 small pre-commit tweaks (kept import json, boolean DataFrame column mask, a comment), 6 modules re-run: 43 OK"
  },
  {
   "module": "commit 3 (54b52eb): 25 modules total",
   "ran": 229,
   "result": "OK"
  },
  {
   "module": "tests.ai_output_check_acceptance (new)",
   "ran": 10,
   "result": "OK"
  },
  {
   "module": "tests.ai_connection_acceptance",
   "ran": 9,
   "result": "OK"
  },
  {
   "module": "tests.ai_payload_acceptance",
   "ran": 10,
   "result": "OK"
  },
  {
   "module": "tests.desktop_commentary_acceptance",
   "ran": 10,
   "result": "OK"
  },
  {
   "module": "tests.letf_ai_payload_acceptance",
   "ran": 1,
   "result": "OK"
  },
  {
   "module": "tests.desktop_letf_ai_acceptance",
   "ran": 1,
   "result": "OK"
  },
  {
   "module": "tests.crypto_missing_values_acceptance",
   "ran": 14,
   "result": "OK"
  },
  {
   "module": "tests.option_disclosure_acceptance",
   "ran": 11,
   "result": "OK"
  },
  {
   "module": "tests.etf_sleeve_disclosure_acceptance",
   "ran": 18,
   "result": "OK"
  },
  {
   "module": "tests.mc_bootstrap_disclosure_acceptance",
   "ran": 15,
   "result": "OK"
  },
  {
   "module": "tests.desktop_authored_prose_language_acceptance",
   "ran": 9,
   "result": "OK"
  },
  {
   "module": "tests.desktop_language_acceptance",
   "ran": 7,
   "result": "OK"
  },
  {
   "module": "tests.desktop_typography_acceptance",
   "ran": 14,
   "result": "OK"
  },
  {
   "module": "tests.fx_basis_disclosure_acceptance",
   "ran": 4,
   "result": "OK"
  },
  {
   "module": "tests.cms_coupon_disclosure_acceptance",
   "ran": 7,
   "result": "OK"
  },
  {
   "module": "tests.desktop_bonds_portfolio_language_acceptance",
   "ran": 7,
   "result": "OK"
  },
  {
   "module": "tests.desktop_macro_language_acceptance",
   "ran": 10,
   "result": "OK"
  },
  {
   "module": "tests.forward_convention_acceptance",
   "ran": 5,
   "result": "OK"
  },
  {
   "module": "tests.letf_index_acceptance",
   "ran": 6,
   "result": "OK"
  },
  {
   "module": "tests.mc_volatility_acceptance",
   "ran": 3,
   "result": "OK"
  },
  {
   "module": "tests.sabr_diagnostics_acceptance",
   "ran": 6,
   "result": "OK"
  },
  {
   "module": "tests.signals_trade_count_acceptance",
   "ran": 9,
   "result": "OK"
  },
  {
   "module": "tests.stock_profile_acceptance",
   "ran": 34,
   "result": "OK"
  },
  {
   "module": "tests.strategy_exposure_acceptance",
   "ran": 5,
   "result": "OK"
  },
  {
   "module": "tests.terminal_target_acceptance",
   "ran": 4,
   "result": "OK"
  },
  {
   "module": "function pins: ficc_acceptance.test_report_prompt_and_deep_analysis_degrade_without_network, quant_acceptance.test_deep_analysis_without_key_degrades_without_network, the 4 tests.flet_api_guard.tests(), and the core.ficc.insights no-key path (engine 'none')",
   "ran": 7,
   "result": "7 ok at baseline and after each of the 3 commits"
  },
  {
   "module": "python -B -m core.ficc.insights (__main__ self-check)",
   "ran": 1,
   "result": "ok after commits 2 and 3 (not run after commit 1)"
  },
  {
   "module": "git grep -n \"\\\"tools\\\"\\|'tools'\" -- core/quant/insights.py (the tests/macro_m1_pit.py:1079 pin)",
   "ran": 1,
   "result": "no match after every commit"
  }
 ],
 "decisions": "I implemented the corrected spec in three commits on claude/s10-ai-20261104 in the s10mc worktree, in the required order: 7c31417 (c), 401fe33 (b), 54b52eb (a)+(d) plus the product note. Nothing was pushed, and the worktree is clean. The pairing of NEW-M6-12 and NEW-M6-19 to the limitations is still ambiguous. Following the PR #68 precedent, every commit message names both IDs and states the ambiguity.\n\nChoices I made where the spec left room or could not be followed literally:\n1. The pandas branch runs before the datetime64 rule in _jsonable. Otherwise a datetime-valued Series would match the dtype-kind rule first and lose its index. This is a reordering of spec rules 6 and 7; the outcomes the spec states are unchanged.\n2. Private-name filtering of DataFrame columns, DataFrame row labels and Series labels happens before to_dict. With orient='split', column names land in a list, not as keys, so the Mapping rule alone could not drop the spec's 'account_balance' column.\n3. Numbers in free-text payload strings are extracted with the same comma-grouped number pattern and the same date masks as the AI text. So '1,350.5' counts as one reference, and a date inside a sentence adds no references. Whole ISO-date strings and marker strings are skipped, as the spec says.\n4. Every token-level skip rule counts in NumberCheck.skipped, following the spec wording; the proto counted only some of them. Masked dates and times are not counted.\n5. found excludes coarse matches, so checked = found + coarse_found + len(not_found) + len(question_only).\n6. ai_output_check.py imports only re, math and dataclasses. For speed I search a sorted reference window with a hand-written binary search instead of bisect. A 3,000-case fuzz against brute force gave 0 mismatches.\n7. core/ui_legacy_messages.py:105 is not edited. The spec made it optional, the pair is not displayed anywhere, and leaving it avoids one more source-review hash.\n8. `import json` stays in insights.py through commit 2, where it is unused, because commit 3 uses it again.\n9. _payload_to_json is kept as an alias that returns ai_payload_json(payload).text.\n10. Flet and Native accept number_check only when it is a NumberCheck instance; anything else is treated as 'not run'.\n11. The Flet worker maps any exception from payload_fn or a custom runner to PAYLOAD_INVALID and clears the spinner in a finally block, as specified.\n12. The product note is written in English, in the style of OPTION_DISCLOSURE.\n\nHow I ran things:\n- Every run put the earlier probe guard first on PYTHONPATH (a copy at /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/s10impl/guard/sitecustomize.py). It makes socket connect raise, returns False from load_dotenv, removes ANTHROPIC_API_KEY, and refuses .env and docs/asset_expansion/cache. All HTTP was faked.\n- Python was v313 with -B, PYTHONDONTWRITEBYTECODE=1 and QT_QPA_PLATFORM=offscreen.\n- Before running a module I grepped it for cache references. tests.macro_m6_context was skipped because it rglobs docs/, which would list the protected folder. Also not run: tests/macro_m1_pit.py, macro_m8_pipeline, macro_m9_lab and run_all.py.\n- Two files use CRLF line endings (core/quant/insights.py and ui/ai_panel.py), and .gitattributes is '-text'. Every edit kept CRLF; the diffs are clean.\n\nProbes and outputs are in /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/s10impl/:\n- probe_before_after.py loads core/quant/insights.py from faf9f3b beside today's tree and gives the before/after table in the note. Output: runs/c3_before_after.out.\n- probe_c2.py compares the old and new synthetic payload text. It matches the spec: Crypto and ETF change only nu to the marker; ETF Hangul now goes out as UTF-8; Derivatives changes only parity_check.within 90.0 to 90.\n- probe_calibration.py measures chance matches with the final rules; the results are tabulated in the note.\n\nNot done here, for the main session:\n- Add tests.ai_output_check_acceptance to .github/workflows/runtime-smoke.yml at :90, and the new and changed AI files to the paths list at :6.\n- Update docs/compliance/source-review.json: new hashes for the changed files, plus entries for core/research/ai_output_check.py and tests/ai_output_check_acceptance.py.\n- Update the SECTION10 queue entries (:704-713 and :784-793), the triage, FACTS, ui_website_updates, research_status and README.\n- Adjacent finding, left as a separate task: the Native crypto table shows GARCH nu = +inf as '—' (quantgen_desktop/market_tools.py:209 and tools.py:18-19), so the Native AI payload loses 'normal innovations'.",
 "unverified": "- No real Anthropic call was made; all bodies were canned.\n- Real frequency of max_tokens and refusal stops on claude-sonnet-5 is unknown, including how much adaptive thinking takes from the 1,500-token budget. The spec leaves that measurement to ⑬-9/b.\n- The Messages API semantics come from the claude-api skill reference (cached 2026-10-06), not from a live response: the stop_reason values including model_context_window_exceeded and compaction, refusal arriving as HTTP 200 with empty or partial content, stop_details filled only on refusal, and temperature returning a 400 on Sonnet 5.\n- How the model reacts to the markers and VALUE_NOTE was not tested.\n- These payloads were read, not run, for arrays, pandas objects and non-finite values: Quant Lab, Portfolio, Signals, rates, bonds, FX, structuring, macro and Strategy Lab. The Quant Lab claim (VALUE_NOTE whenever prob_target_basis is None) comes from reading ui/quant_lab_page.py:372 only.\n- The 'before' rows for the Flet and Native screens come from the earlier design probe s10ai2/design/probe_render_current.out, which I read and did not re-run. The engine-level before rows I re-ran myself with probe_before_after.py.\n- The number check runs on the raw reply text, while Native displays and saves safe_detail(text). The difference only matters when a reply contains a URL or secret-like text; not measured.\n- Not checked: the Windows screen, real KIS and Upbit data, and on-screen rendering of the new label lines. tests.desktop_typography_acceptance passes, so the glyphs in the string literals are covered.\n- The register citations (2da6469 MODEL_LIMITS :175, :452, :3454-3473) and the queue lines were confirmed by reading the exact lines. The known-errors register lines were not re-read."
}
```

## 반박 검토가 찾은 문제 (설계 단계)

- (b) Two registry meanings are wrong. Per core/quant/garch.py:142-156, nu_interval is 'high = inf when the interval reaches the normal' and half_life_interval is 'inf where the interval reaches 1'. The spec gives ('garch','nu_interval_95','+inf') the point-estimate wording 'normal innovations', and ('garch','half_life_interval_95','+inf') the wording 'persistence at or above 1'. A fit with nu = 8 and interval (5, inf) would then be described to the model as having normal innovations. Probe c3: a real t-fit has interval (13.98, inf), and both nu and the interval's upper bound go out as 'normal innovations'. Interval bounds need their own meanings, worded without digits so that '95%' does not end up in the AI text and come back as 'not found'.
- (b) The byte-identity claim is false. The spec appends VALUE_NOTE whenever sent.nulls > 0, so any payload holding None changes, yet the spec lists None among the byte-identical types. Probe c1 measured the three synthetic payloads. Crypto has 1 null (funding.bootstrap_p) plus the nu marker. ETF has 6 nulls and two non-ASCII strings that now go out as raw UTF-8: letf.name 'KODEX 레버리지' and sleeve_price_basis with μ, σ and —. So 'ETF: only letf.nu changes' is incomplete. Derivatives is right: 0 nulls, no VALUE_NOTE, and only parity_check.within changes (90.0 to 90). Quant Lab sends prob_target_basis = None when there is no target (ui/quant_lab_page.py:371), so it also gets the note (read, not run).
- (a) The string-leaf regex as written in the spec, [+-−], is a character range from U+002B to U+2212 that includes ASCII letters and digits. Strings such as 'A12', 'x1.5', 'Q3', 'M6' and 'T10' would count as reference numbers (probe c2). It must be [+\-−], as in design/proto.py:182.
- (a) 'Never counted: date and ID strings' is false for IDs made only of digits. The ETF code '122630' and letf.interpretation.historical_study_fund '122630' fully match the formatted-number pattern and are counted (probe c1). Counting them is useful, because an AI citing the fund code is then 'found'. The statement needs correcting, not the code.
- (a) False 'not found in anything sent': numbers inside free-text payload strings are never references. Examples are ETF sleeve_price_basis 'Simulated series (GBM, μ=3%, σ=27%)', letf time_convention 'SESSIONS/252', crypto funding.interpretation and derivatives hedge.scope. AI text citing '27%' reports it as not found (probe c10). Numbers from free-text leaves (other than markers and ISO dates) should be added as data references.
- (a) The date masks are wrong. The month-name mask matches the first two digits of a year, so 'October 2026' leaves a spurious '26' and 'March 2025' a '25', both not found. D/M/Y slash dates are not masked, although the spec says they are: proto masks only YYYY/M/D, so '03/11/2026' leaves '03'. The Korean dotted date '2026.11.03' is read as the number 2026.11, and '10월' (a month on its own) as 10. All four were reported not found (probe c2).
- (a) The Korean skip list hides real and invented numbers. '9.99일 때' ('when it is 9.99') is skipped because 일 is on the tenor list, so an invented number escapes the check. '7.77만큼' is skipped by the scale word 만. '67,012달러' is skipped by 달 (but 달러 is 'dollar'). '0.42차이' is skipped by 차. '7.2년' is skipped although a duration is a measurement (probe c2). Fix: tenor words skip integers only; 달러, 차이 and 주식 are excluded; 만큼 is not a scale word (probe c6, proto_fix.py).
- (a) English needs skip rules the spec lacks. Scale words: '3.4 million' is not found and '1.2 billion' matches by chance. Confidence levels: '95% VaR' and '99% CVaR' are not found unless var_level is in the payload. Index names: 'S&P 500' and 'KOSPI 200' are not found (probe c2). Ranges such as '15-20%' and '0.38-0.47' are skipped entirely; this should be stated as unchecked.
- (a) The question_only bucket does not work for report-prompt numbers. Question tokens go through the same skip rules, so the weekly REPORT_PROMPTS yields no tokens at all: '252-session', '1-week', '1-month', 1991 and 2018 are all skipped. AI text 'the trailing 252 sessions' then reports 252 as not found instead of question-only (probe c2). Question references must take every run of digits. With that fix it lands in question_only (probe c6).
- (Native) The spec clears check_note only in invalidate() and failed(). submit() at quantgen_desktop/commentary.py:117 clears output and report_actions when a request starts, so the previous label and check line stay on screen beside an empty output until the new reply arrives. check_note must be cleared at :117 too.
- (b, privacy) filter_analysis_fields runs before conversion, so keys created by _jsonable are never filtered. A DataFrame column 'account_balance' and a 'holding' key inside dicts in an object ndarray both go out with the proposed serialiser (probe c3). This is not a regression, because today str(df) shows the column name and tolist() keeps the dicts, but the rewritten boundary should apply private_field to every Mapping it emits.
- (b) The pandas conversion drops index labels. pd.Series.tolist() and DataFrame.to_dict('list') lose a DatetimeIndex, whereas today's str() display shows the dates (probe c3). The problem is latent: none of the three synthetic payloads has pandas objects. Fix: a Series becomes {'index', 'values'} and a DataFrame uses orient='split'.
- (b) str(k) changes bool and None keys from today's JSON 'true' and 'null' to 'True' and 'None' (probe c3). Key text should follow json.dumps.
- (c) The OUTPUT_LIMIT text states that the limit 'counts the model's internal reasoning'. That holds only for models that think when the thinking parameter is omitted; QUANTGEN_AI_MODEL may name one that does not, such as Haiku 4.5. The text should say the limit 'can include' reasoning. Minor.
- (evidence) The spec says acceptance and refusal agree at 179,992 B and cites probe_proto2.out. probe_proto2.out shows four sizes, all refused. The accepted case is in probe_proto.out, whose 180010 line ('native refused, proposed 179,964 B sent') is a probe artifact: it measured the report, not a payload. Probe c9 re-tested with the real commentary_payload at 179,999, 180,000 and 180,001 B, and the two gates agree exactly. Also, Analysis moved +1 line from 7fc53e2 (now :43-49), not +4; the later blocks moved +4.
- (tests missed) tests/desktop_typography_acceptance.py checks that every string literal in core/research/*.py and core/quant/insights.py has glyphs in the bundled fonts, so the new ai_output_check.py regexes and the new messages are scanned. Probe c4 found no missing glyphs; the test is added to the run list. tests/flet_api_guard.py checks the ui/ai_panel.py controls but runs only through tests/run_all.py, so call its tests() directly. Probe c8: 4 ok at baseline.
- (records) docs/compliance/source-review.json holds a hash for every source these commits change (core/quant/insights.py, core/research/ai_connection.py, core/research/ai_payload.py, ui/ai_panel.py, quantgen_desktop/commentary.py, quantgen_desktop/translations.py, core/ui_legacy_messages.py and three of the four test modules; tests/desktop_commentary_acceptance.py is not checked), and the new files will be unreviewed. The main session must refresh it. runtime-smoke.yml:6 also lacks paths for ai_connection.py, ai_payload.py, ui/ai_panel.py and commentary.py.
- (minor) The Native export appends only English label and check-line sections, so a ko ZIP shows them in English: localized_html translates catalog strings only. This matches the existing 'AI-generated commentary' line. Recorded as owner choice 9.

### 확인하지 못한 것

I did not call the real API. These come from the claude-api skill (cached 2026-10-06), not from a real call:
- the stop_reason set;
- model_context_window_exceeded on 4.5+ models;
- compaction only on on-demand compaction requests;
- refusal returning HTTP 200 with empty or partial content;
- stop_details being null except on refusal;
- Sonnet 5 running adaptive thinking with display 'omitted' when thinking is omitted;
- temperature returning a 400 on Sonnet 5;
- thinking {type: disabled} being accepted on Sonnet 5 and returning a 400 on Sonnet 5.5 and Opus 5.5.

Not found in the skill lines I read, so still unverified:
- that a non-streaming reply always carries a string stop_reason;
- that max_tokens caps thinking plus text.

Not measured: how often max_tokens or refusal occur at 1500 tokens, and whether VALUE_NOTE or the markers change how the model words its output.

The corrected tokenizer rules ran only in my probe (challenge/proto_fix.py):
- on 25 constructed English and Korean fragments and the spec's 6 cases (c6);
- not on real model output;
- I did not re-measure chance-match rates after adding free-text references.

Designed but not prototyped:
- the privacy filter after conversion;
- the pandas index forms;
- json-style key text;
- the corrected interval markers.
For these I only showed the current leak, index loss and key change (c3), and read garch.py:142-156.

Not run:
- the Flet _CheckNotice, Native check_note clearing in submit(), and every new test (none written);
- the payloads for rates, bonds, fx, structuring, macro, portfolio, signals, strategy and the real Quant Lab page. The Quant Lab null comes from reading :371.

The Korean wording was reviewed only by me.

Other things I did not run:
- The compliance consequence of hash drift is read from source-review.json and the header of tools/compliance/check.py. I did not run tests/compliance_acceptance.py.
- I did not check whether requests' json= serialisation escapes non-ASCII text on the wire. This does not affect the size gate, which measures the inner UTF-8 text.

What I did run:
- baseline 17 OK (c7);
- the flet_api_guard functions (c8);
- the glyph check on the prototype strings (c4);
- the exact size boundary (c9);
- the current stop_reason defects (c5).
Git status was empty before and after every probe.

## 소유자 선택 사항 (설계 단계)

Decisions left to the owner, each with the default this spec uses:

1. What to do with text cut off at max_tokens.
   - Default: discard it. The reply fails closed with OUTPUT_LIMIT and nothing is shown or saved.
   - Alternative: show the partial text under a 'cut off at the output limit' banner and keep it out of export.
   - The register's close method (MODEL_LIMITS:175, 'max_tokens면 잘렸다고 표시한다') means 'mark it as cut off'. The failure notice satisfies that, but the register does not require discarding the text.

2. stop_sequence.
   - Default: treat it as incomplete (INCOMPLETE_RESPONSE), because QUANTGEN sends no stop_sequences.
   - Alternative: accept it as complete. Do this only if stop sequences are ever added to the request.

3. Output budget.
   - Default: no change to max_tokens 1500, effort or thinking in this work. That is a cost decision.
   - Measure real truncation first under ⑬-9/b.
   - Any thinking setting depends on the model. On Sonnet 5, thinking {type: disabled} is accepted; on Sonnet 5.5 and Opus 5.5 it returns a 400. QUANTGEN_AI_MODEL can name either.

4. Native consent text.
   - Default: reword it to say the payload and question are sent with QUANTGEN's fixed writing instructions.
   - Alternative: keep the old text and show VALUE_NOTE inside the preview instead.

5. Number check thresholds and scope.
   - Default: matches with two significant digits or fewer are reported as 'could match by chance'.
   - Default: verdict words (PASS, FAIL, REJECT, NOT_RUN) are not compared, and the label says so. Comparing them is an optional advisory extension.

6. Native report nulls.
   - Default: keep plain() turning non-finite values into null, which is the report contract. Native reports therefore cannot tell NaN from ±inf; the note says 'missing or not a finite number'.
   - Changing that contract would be a separate decision.

7. Native crypto table showing '—' for GARCH nu = +inf.
   - Default: leave it to a separate task, outside this change.

8. Flet label placement.
   - Default: a label line under the text with no new chip, so the Flet catalog is not edited.
   - Alternative: also add an 'AI commentary · not verified' chip next to the engine chip.

9. Pairing NEW-M6-12 and NEW-M6-19 to limitations.
   - Default: both IDs recorded against all three commits, with the pairing stated as ambiguous.

## ID 대응 메모

The pairing between the two IDs and the limitations is still ambiguous.

Where the IDs appear:
- NEW-M6-12 and NEW-M6-19 appear only in the related-errors cell of model register entry 149 (M6-19). That entry is at 2da6469:docs/nautilus_bridge/MODEL_LIMITS_REGISTER_2026-10-28.md:3454-3473; the summary row is at :452.
- The known-errors register describes both as listed only in that cell, with no sentence.
- docs/product/SECTION10_QUEUE_2026-10-30.json marks both as mapping_needs_disambiguation true, reproduction NOT_RUN and correction NOT_IMPLEMENTED. NEW-M6-12 is at :704-713 and NEW-M6-19 at :784-793 on faf9f3b.
- Neither ID is in origin/handoff LEDGER.md.

What the other IDs in that cell cover:
- D03-04 is the synthetic-disclosure rule.
- D03-01 is the Crypto FX source.
- P01-13 is app import time.
- NEW-M6-18 is the Upbit holdings payload, already done.

That leaves these unlabelled limitations:
- (a) the output content is never verified;
- (b) arrays are cut to the first 50 elements, and NaN and Infinity go out as bare tokens;
- (c) stop_reason is never read;
- (d) the same input can give different output, which can only be labelled.

The earlier hint 'NEW-M6-12 = (a), NEW-M6-19 = (c)' is dropped. Reading the IDs as code defects with line citations gives {(b), (c)} just as well, and nothing excludes (a) or (d).

Following the Crypto PR #68 precedent for NEW-M6-14 and NEW-M6-22 (LEDGER.md:138 and :140), this spec fixes all four candidates, so both IDs are covered whichever pairing the owner picks:
- commit 1 covers (c);
- commit 2 covers (b);
- commit 3 covers (a) and (d).

Record each ID (for example ②-5/NEW-M6-12 and ②-5/NEW-M6-19) against all three commits. Name which limitation each commit closes, so the owner can tie each ID to its own commit later without re-reading the code.

## 수정된 설계 전문 (반박 반영)

QUANTGEN §10 NEW-M6-12 and NEW-M6-19 (register entry 149, the M6-19 AI commentary path). This is the consolidated implementation spec, re-checked on main faf9f3b: worktree s10mc, branch claude/s10-ai-20261104, git status empty before and after every probe. The skeptical review's corrections are applied.

=== 0. EVIDENCE AND LOCATIONS (faf9f3b) ===

Probes

Folder /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/s10ai2/design/:
- guard/sitecustomize.py does the following:
  - socket connect, connect_ex and create_connection raise;
  - dotenv.load_dotenv returns False;
  - ANTHROPIC_API_KEY is removed from the environment;
  - open, listdir, scandir and iterdir refuse .env and docs/asset_expansion/cache.
- The other probes:
  - probe_c_current, probe_b_current and probe_render_current;
  - proto.py;
  - probe_proto and probe_proto2.
- Note on probe_proto.out: its line 'Hangul payload near 180010: native prepare refused; proposed 179964 B -> sent' is a probe artifact. Native refused, so the probe measured the report rather than a payload.
- probe_proto2.out shows equal byte counts at four sizes; all four are above the limit.

Folder /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/s10ai2/challenge/ (same guard):
- c1_payloads: nulls, non-ASCII strings and digit-only strings in the three synthetic payloads.
- c2_numbers: the number check on 25 English and Korean fragments.
- c3_serialiser: privacy, pandas index, keys and interval markers.
- c4_glyphs: the bundled-font glyph check.
- c5_stop_current: current stop_reason handling.
- c6_fix_check with proto_fix.py: the corrected tokenizer rules.
- c7_baseline: 17 OK.
- c8_flet_guard: 4 ok.
- c9_size: the exact size boundary.
- c10_text_leaves: numbers inside free-text payload strings.

Fakes: core.quant.insights._requests is replaced by a Mock that returns canned Messages bodies. No real API call was made.

Line numbers

These were re-read on faf9f3b. Relative to 7fc53e2, Analysis moved down 1 line and the later blocks moved down 4.

core/quant/insights.py:
- Analysis :43-49.
- _SYSTEM :282-301.
- _payload_to_json :304-316:
  - default() :305-314;
  - o.tolist()[:50] :309;
  - np.floating and np.integer go to float :310-311;
  - json.dumps without allow_nan :316.
- deep_analysis :319-363:
  - failure() :323-324;
  - serialisation outside any try :332-333;
  - POST :336-344, with max_tokens 1500 at :341;
  - content and text join :353-360;
  - empty-text check :361-362;
  - success :363.

core/research/ai_connection.py:
- MESSAGES :3-46; INVALID_RESPONSE :37-39.
- error_message :49-53.
- response_error :56-69.
- transport_error :72-79.

core/research/ai_payload.py:
- filter_analysis_fields :19-27.
- PRIVATE_WORDS :10-11.

core/ficc/insights.py:
- REPORT_PROMPTS :568-594.
- Wrapper deep_analysis :602-608.
- __main__ self-check :744-749.

ui/ai_panel.py:
- _ErrorNotice :29-41.
- analysis_panel :44-102:
  - busy :56;
  - worker :63-73;
  - success render :68-71;
  - rows :83-99;
  - deep_host appended at :99.

quantgen_desktop/commentary.py:
- commentary_payload :24-37; size check :35-36.
- prepare :92-100; consent status :100.
- submit :102-121; clears output and report at :117.
- finished :123-134; export :131-133; success status :134.
- failed :136-140.

quantgen_desktop/translations.py:
- :545 consent pair.
- :549 success template.
- TEMPLATES built in file order :591-602.
- translate :622-637.

Other files:
- core/ui_legacy_messages.py:105: the dead consent pair (Flet catalog).
- quantgen_desktop/localization.py:11-33: UiLabel and localized_text; LanguageController calls UiLabel.retranslate.
- quantgen_desktop/jobs.py:17-27: an exception becomes failed(type name).
- core/research/tool_export.py:14-22: plain() turns non-finite values into None.
- core/quant/garch.py:
  - :103 and :107-108: field meanings;
  - :142-156: nu_interval, whose upper end is inf when the interval reaches the normal limit, and half_life_interval, which is inf where the interval reaches 1;
  - :267-271: _half_life;
  - :473 and :476: nu = inf.
- core/quant/strategies.py:284-299: half_life and adf_pvalue.

Surfaces (verified)

Pages that pass core.ficc.insights.deep_analysis:
- Only ui/macro_page.py:132-135 and :148-149.

Pages that pass core.quant.insights.deep_analysis explicitly:
- ui/crypto_page.py:103-104 (import :19);
- ui/etf_page.py:158-159 (import :25);
- ui/derivatives_page.py:132-133 (import :26);
- ui/strategy_lab_page.py:168-169 (import :21).

Pages that pass no deep_fn and so get the core.quant default:
- ui/quant_lab_page.py:399;
- ui/portfolio_page.py:208;
- ui/signals_page.py:208;
- ui/rates_page.py:155, :199, :256, :292 and :362;
- ui/bonds_page.py:214;
- ui/fx_page.py:235, :307 and :377;
- ui/structuring_page.py:212.

Native:
- quantgen_desktop/app.py:614-617 builds CommentaryPane.
- Its default runner is core.ficc.insights.deep_analysis (commentary.py:16 and :41).
- Its sources come from commentary_sources at :620-636.

Every path ends in core.quant.insights.deep_analysis. Rendering happens only in ui/ai_panel.py (Flet) and quantgen_desktop/commentary.py (Native), and export only through ReportActions. git grep finds no other place that stores or shows AI text. The _backup/ copies are inert.

Defects reproduced on faf9f3b

(c) stop_reason; probes probe_c_current and challenge c5, quant and FICC weekly both:
- These are shown as success:
  - max_tokens with partial text;
  - refusal with partial text;
  - pause_turn;
  - stop_sequence;
  - model_context_window_exceeded;
  - an unknown value;
  - stop_reason missing, null or non-string with text.
- These get INVALID_RESPONSE, which is the wrong diagnosis:
  - max_tokens with only a thinking block;
  - refusal with empty content.
- Flet shows the cut-off text under 'engine: …'.
- Native shows 'AI commentary complete ·' and makes the text saveable.

(b) serialisation:
- Arrays are cut to their first 50 elements.
- Bare NaN, Infinity and -Infinity tokens go out, so the text is not strict JSON.
- Type handling:
  - np.int64 7 becomes 7.0;
  - np.bool_ becomes the string 'True';
  - a pd.Series becomes its shortened display text.
- Tuple or np.int64 dict keys raise TypeError out of deep_analysis before the POST. In Flet the spinner then stays on.
- Synthetic payloads:
  - Crypto sends garch.nu as Infinity.
  - ETF 122630 sends letf.nu as Infinity.
- Hangul is \u-escaped, which takes 1.78 times the UTF-8 bytes, and the model reads the literal escapes.

(a) and (d): there is no output check, and neither UI carries a 'not verified' or reproducibility label.

Messages API semantics

Source: claude-api skill, cached 2026-10-06; no real call was made.
- stop_reason takes these values:
  - end_turn;
  - max_tokens;
  - stop_sequence;
  - tool_use;
  - pause_turn, which comes from server-tool loops;
  - refusal;
  - model_context_window_exceeded on 4.5+ models, distinct from max_tokens (model-migration.md:450);
  - compaction, only on on-demand compaction requests (preserved-thinking-migration/causes.md:63).
- refusal:
  - It comes back as HTTP 200, with empty content when it fires before any output or with partial text when it fires mid-output.
  - The skill says to discard partial output (model-migration.md:1383).
  - stop_details is filled only on refusal, may be null, and its explanation is provider text.
- claude-sonnet-5:
  - Omitting thinking runs adaptive thinking with display 'omitted', so thinking blocks carry empty text.
  - temperature, top_p and top_k return a 400.
  - thinking {type: disabled} is accepted. On Sonnet 5.5 and Opus 5.5 it returns a 400.

=== COMMIT 1 — (c) stop_reason ===

Behaviour

After an HTTP 200, deep_analysis classifies the body in this exact order:
1. resp.json() raises: INVALID_RESPONSE.
2. The body is not a dict: INVALID_RESPONSE.
3. content is missing or not a list: INVALID_RESPONSE.
4. Any dict block with type 'text' has a non-string text: INVALID_RESPONSE.
5. stop_reason is missing, None or not a str: INVALID_RESPONSE. This keeps tests/ai_connection_acceptance.py:71-75 unchanged.
6. 'refusal': REFUSED, even when text came back. stop_details is never read or shown.
7. 'max_tokens': OUTPUT_LIMIT, even when only a thinking block came back or content is [].
8. Any value other than 'end_turn' gives INCOMPLETE_RESPONSE. This covers pause_turn, tool_use, model_context_window_exceeded, compaction, unknown values, and stop_sequence, because QUANTGEN sends no stop_sequences.
9. 'end_turn': join the text blocks. Empty text after strip gives INVALID_RESPONSE.
10. Success returns Analysis(text, model, stop_reason='end_turn').

Rules for every failure path:
- Every failure returns text '', engine=model and http_status None.
- failure() never receives 200.
- There is no retry; the request stays a single POST.
- The request is unchanged: model, system=_SYSTEM, timeout 60, and no thinking, temperature, tools or stop_sequences.
- Cut-off text is discarded and never shown, saved or exported (default; owner choice 1).

Files

core/research/ai_connection.py:
- Add OUTPUT_TOKEN_LIMIT = 1500 and COMPLETE_STOP_REASONS = ('end_turn',).
- Add reply_result(body) -> (error_code or '', text, stop_reason), implementing steps 2-9.
- Add the new MESSAGES. Build OUTPUT_LIMIT with an f-string from OUTPUT_TOKEN_LIMIT.

core/quant/insights.py:
- Import OUTPUT_TOKEN_LIMIT and reply_result.
- The request json uses "max_tokens": OUTPUT_TOKEN_LIMIT.
- Replace :353-363 with:
  - try body = resp.json() / except: INVALID_RESPONSE;
  - code, text, stop = reply_result(body);
  - if code: return failure(code, model);
  - return Analysis(text, model, stop_reason=stop).
- No '"tools"' or "'tools'" literal may appear in this file (tests/macro_m1_pit.py:1079).
- Analysis gets stop_reason: str = "" as its last field.

New user texts

MESSAGES are (EN, KO); n = f'{OUTPUT_TOKEN_LIMIT:,}'.

OUTPUT_LIMIT
- EN: "Claude reached QUANTGEN's output limit of {n} tokens before finishing (stop reason: max_tokens). The limit can include the model's internal reasoning as well as the visible text, so a long report format or long reasoning can use it up. The unfinished text was not shown or saved, and no automatic retry was made. Local calculations and official verdicts are unchanged."
- KO: "Claude가 글을 끝내기 전에 QUANTGEN의 출력 한도({n}토큰)에 도달했습니다(중단 사유: max_tokens). 이 한도에는 화면에 보이는 글뿐 아니라 모델의 내부 추론이 포함될 수 있으므로, 보고서 형식이 길거나 추론이 길어지면 한도를 다 쓸 수 있습니다. 끝나지 않은 글은 표시하거나 저장하지 않았고 자동 재시도도 하지 않았습니다. 로컬 계산과 공식 판정은 그대로입니다."

REFUSED
- EN: "Claude declined to write this commentary (stop reason: refusal). Any partial text was not shown or saved, and no automatic retry was made. Local calculations and official verdicts are unchanged."
- KO: "Claude가 이 해설 작성을 거절했습니다(중단 사유: refusal). 일부 작성된 글이 있어도 표시하거나 저장하지 않았고 자동 재시도도 하지 않았습니다. 로컬 계산과 공식 판정은 그대로입니다."

INCOMPLETE_RESPONSE
- EN: "Claude's reply did not end normally (its stop reason was not end_turn), so it was treated as incomplete. The text was not shown or saved, and no automatic retry was made. Local calculations and official verdicts are unchanged."
- KO: "Claude 응답이 정상적으로 끝나지 않아(중단 사유가 end_turn이 아님) 완성되지 않은 응답으로 처리했습니다. 글은 표시하거나 저장하지 않았고 자동 재시도도 하지 않았습니다. 로컬 계산과 공식 판정은 그대로입니다."

Both UIs pick these up with no code change:
- Flet: _ErrorNotice shows them in EN or KO and re-renders on a language switch.
- Native: finished() routes to failed() with the localized KO text (commentary.py:124-127), and report_actions stays cleared.

These stay byte-identical: _SYSTEM, the user message, the request json, the existing MESSAGES, and the success rendering in both UIs.

Tests

Existing fixtures to change:
- tests/ai_connection_acceptance.py:67-70: add 'stop_reason': 'end_turn' to the body at :68-69 and assert r.stop_reason == 'end_turn'. Lines :71-75 stay unchanged.
- tests/ai_payload_acceptance.py:41: add "stop_reason": "end_turn". Without it, the test fails at :46.

New, in tests/ai_connection_acceptance.py, using self.call():

test_stop_reason_is_read_after_the_body_and_before_the_text:
- end_turn with a thinking block then text: OK.
- stop_sequence: INCOMPLETE_RESPONSE.
- max_tokens with text, with only a thinking block, and with []: OUTPUT_LIMIT.
- refusal with partial text and stop_details.explanation 'fixture-key-secret provider explanation': REFUSED, with the explanation absent from r.error.
- refusal with []: REFUSED.
- pause_turn, tool_use, model_context_window_exceeded, compaction and 'future_value': INCOMPLETE_RESPONSE.
- stop_reason missing, None, 42 or [] with text: INVALID_RESPONSE.
- end_turn with []: INVALID_RESPONSE.
- end_turn with text 42: INVALID_RESPONSE.
- Every failure: text '', http_status None, and 'HTTP 200' not in r.error.

test_cut_off_messages_are_bilingual_and_name_the_limit:
- EN and KO differ.
- KO contains Hangul; EN contains none.
- Both OUTPUT_LIMIT texts contain f'{OUTPUT_TOKEN_LIMIT:,}' and 'max_tokens'.
- EN contains 'output limit' and 'reasoning'; KO contains '출력 한도' and '추론'.
- The sent json has max_tokens == OUTPUT_TOKEN_LIMIT and no stop_sequences, thinking or temperature key.

New, in tests/ai_payload_acceptance.py:

test_flet_cut_off_reply_shows_the_notice_not_the_text:
- Use the real deep_analysis with a fake _requests returning max_tokens and partial text.
- rows[-1].controls is a single _ErrorNotice, and the partial text is in no ft.Text.
- After translate_controls: ko_KR shows '출력 한도'; en_US shows 'output limit'.
- rows[3].controls[-1].visible is False, and post is called once.

New, in tests/desktop_commentary_acceptance.py:

test_refused_or_cut_off_reply_is_neither_shown_nor_exportable:
- Set p.runner = core.ficc.insights.deep_analysis.
- Hold the insights.config and _requests patches across submit() and wait().
- Run refusal with partial text, then max_tokens with only a thinking block.
- Each time: output '' and report None.
- ui_language 'ko' gives '거절' or '출력 한도'; 'en' gives 'declined' or 'output limit'.

Commit message: "Check the Messages API stop reason before AI commentary is shown (§10 NEW-M6-12, NEW-M6-19: limitation c)".

=== COMMIT 2 — (b) serialisation ===

One serialiser for every path

Add core/research/ai_payload.py ai_payload_json(payload) -> PayloadText, a frozen dataclass with text: str, marked: int and nulls: int.
- It runs filter_analysis_fields first (the NEW-M6-18 boundary, unchanged).
- Then it runs _jsonable(value, parent_key, field_key).

_jsonable rules, in this order:
1. A dataclass becomes asdict.
2. A Mapping becomes a dict.
   - Keys become text the way json.dumps would write them:
     - a numpy scalar is converted with .item() first;
     - str stays as is;
     - bool becomes 'true' or 'false';
     - None becomes 'null';
     - int becomes str(int);
     - float uses float.__repr__;
     - anything else becomes str(k).
   - Every key for which ai_payload.private_field(key) is true is dropped. This also catches keys created by conversion, such as DataFrame columns and dicts inside object arrays, which the first filter cannot see.
3. list and tuple become a list.
4. None, bool and str pass through.
5. datetime.date, datetime.datetime and time (pd.Timestamp included) become str(o), identical to today.
6. numpy datetime64 or timedelta64 (dtype.kind in 'mM'): scalars become str(o), arrays become [str(x) …].
7. pandas objects (pandas imported lazily), so index labels are kept:
   - DataFrame: to_dict(orient='split'), giving index, columns and data, then recursed.
   - Series: {'index': [...], 'values': [...]}, recursed.
8. Anything else with .tolist() that is not a Python int or float (ndarray, numpy scalars including np.bool_, pandas Index) is converted with .tolist() at FULL length, with no [:50], and recursed.
9. int stays int.
10. float, np.float64 included:
    - finite: as is;
    - NaN: a marker string;
    - +inf or -inf: a marker string.
11. Anything else becomes str(o).

Then json.dumps(obj, ensure_ascii=False, allow_nan=False), keeping the default ', ' and ': ' separators.

Non-finite markers

The registry NONFINITE_MEANINGS is keyed on (enclosing dict key, field key, kind). For list elements the list's key is the field key.

Normal-innovation limit:
- ('garch','nu','+inf') and ('letf','nu','+inf'): "+inf: normal innovations (the fitted Student-t degrees of freedom are at the normal limit, eta = 0)".
- ('garch','nu_interval_95','+inf'): "+inf: the upper end of this interval reaches the normal limit (eta = 0); normal innovations are not excluded".

Half-life:
- ('garch','half_life','+inf') and ('garch','half_life_sessions','+inf'): "+inf: persistence at or above 1, so a variance shock does not halve".
- ('garch','half_life_interval_95','+inf'): "+inf: this end of the interval reaches persistence 1, where a variance shock does not halve".

Unconditional volatility:
- ('garch','uncond_vol_365','NaN'), ('garch','uncond_vol_annual','NaN') and ('letf','uncond_vol','NaN'): "NaN: undefined, because persistence is at or above 1 (no unconditional variance)".
- ('garch','uncond_vol_annual','+inf') takes the same wording with the '+inf:' prefix.

AR(1) half-life:
- ('kimchi','half_life_days','+inf'), ('ethbtc','half_life_days','+inf') and ('premium_stats','half_life','+inf'): "+inf: no decaying AR(1) fit (missing or non-decaying); not slow mean reversion; read the decay status".

ADF p-value:
- ('kimchi','adf_p','NaN'), ('ethbtc','adf_p','NaN') and ('premium_stats','adf_p','NaN'): "NaN: not available; the ADF test could not be computed".

Generic markers, for every other path:
- NaN: "NaN: not available or not defined".
- +inf: "+inf: not a finite number; read the status or note fields beside it".
- -inf: "-inf: not a finite number; read the status or note fields beside it".

Markers contain no digits other than '0' and '1'.

Meanings are taken from:
- core/quant/garch.py :103, :107-108, :142-156, :267-271 and :473-476;
- core/quant/strategies.py:284-299;
- core/research/crypto_workflow.py:58-61;
- core/research/etf_workflow.py:75-77 and :152;
- core/crypto/analytics.py:119 and :200-201;
- ui/quant_lab_page.py:381-397.

deep_analysis

Payload handling:
- try sent = ai_payload_json(payload) / except Exception: return failure('PAYLOAD_INVALID'). Engine is 'none' and nothing is posted.
- If len(sent.text.encode('utf-8')) > AI_PAYLOAD_MAX_BYTES: return failure('PAYLOAD_TOO_LARGE'), with no POST.

User message:
- Starts with f"Analysis type: {kind}\n\nComputed results:\n{sent.text}".
- If sent.marked or sent.nulls, "\n\n" + VALUE_NOTE follows.
- Then the operator question, exactly as today.

VALUE_NOTE is model-facing and in English: "Value conventions in the computed results: a string starting "NaN:" marks a value that is not available or not defined; a string starting "+inf:" or "-inf:" marks an unbounded or limiting value, not a measurement. The text after the colon gives the meaning (for example "+inf: normal innovations" for a Student-t degrees-of-freedom parameter). JSON null means the value was missing or not a finite number in the source. Describe these values by that meaning; never quote them as numbers or estimate them."

_SYSTEM stays byte-identical. _payload_to_json becomes an alias returning ai_payload_json(payload).text, or is deleted; no test references it.

Size limit

- AI_PAYLOAD_MAX_BYTES = 180_000 lives in core/research/ai_payload.py.
- commentary.py:36 uses the constant.
- Native and the send side both measure UTF-8 JSON written with ensure_ascii=False and use the same '>' comparison.
- Probe c9 used the real commentary_payload. At 179,999 and 180,000 B, prepare accepts and the send side sends. At 180,001 B, prepare refuses.
- A payload accepted by prepare() therefore cannot be refused after consent.
- Import direction: ai_connection imports the constant from ai_payload, never the reverse.

Flet worker (ui/ai_panel.py:63-73)

- try result = deep(kind, filter_analysis_fields(payload_fn()), question=…) / except Exception: result = insights.Analysis('', 'none', error_message('PAYLOAD_INVALID'), 'PAYLOAD_INVALID').
- Render inside try/finally, with busy.visible = False and page.update() in the finally.

Native consent (commentary.py:100)

- The new KO source is: "이 내용과 질문을 QUANTGEN의 고정 작성 지침과 함께 전송합니다. 지침에는 계좌나 개인 정보가 없습니다. AI 해설은 공식 gate 판정을 변경하지 않습니다."
- Replace translations.py:545 with this EN|KO pair: "This payload and your question are sent with QUANTGEN's fixed writing instructions, which contain no account or personal data. AI commentary does not change official gate verdicts.|<KO above>".
- Optionally replace the dead pair at core/ui_legacy_messages.py:105 the same way.
- No test pins the old string (git grep).

New user texts

PAYLOAD_TOO_LARGE (m = f'{AI_PAYLOAD_MAX_BYTES:,}')
- EN: "The calculation data is larger than the {m}-byte limit for AI commentary, so nothing was sent and nothing was cut. Choose a smaller calculation. Local results are unchanged."
- KO: "계산 데이터가 AI 해설 전송 한도({m}바이트)보다 커서 아무것도 보내지 않았고, 데이터를 잘라 보내지도 않았습니다. 더 작은 계산을 선택하세요. 로컬 결과는 그대로입니다."

PAYLOAD_INVALID
- EN: "QUANTGEN could not prepare the calculation data for AI commentary, so nothing was sent. Local results are unchanged."
- KO: "QUANTGEN이 AI 해설에 보낼 계산 데이터를 준비하지 못해 아무것도 보내지 않았습니다. 로컬 결과는 그대로입니다."

What changes in the user message

The message stays byte-identical only for payloads with:
- no None;
- no non-finite value;
- no numpy integer or bool;
- no array or pandas object;
- no bool or None dict key;
- only ASCII strings.

Measured on the synthetic payloads (probe c1):
- Crypto: garch.nu changes to its marker, and VALUE_NOTE is appended. The payload also holds null funding.bootstrap_p.
- ETF: letf.nu changes to its marker, and VALUE_NOTE is appended (6 nulls). letf.name 'KODEX 레버리지' and sleeve_price_basis (μ, σ, —) now go out as UTF-8 characters instead of \u escapes.
- Derivatives: only parity_check.within changes, from 90.0 to 90. It has 0 nulls, so no VALUE_NOTE.
- Quant Lab also gets VALUE_NOTE whenever prob_target_basis is None (read, not run).

Unchanged:
- Native commentary_payload and its preview;
- plain(), make_report and report_bytes, including verdict NOT_RUN and 'Non-finite observations are null';
- filter_analysis_fields and PRIVATE_WORDS.

Tests, commit 2

Existing pins that must still pass:
- tests/ai_payload_acceptance.py:49-50;
- tests/ai_connection_acceptance.py:26;
- tests/letf_ai_payload_acceptance.py:86-88;
- tests/desktop_commentary_acceptance.py:51-59.

New, in tests/ai_payload_acceptance.py:

test_payload_is_strict_json_with_full_arrays_and_labelled_nonfinite_values:
- The output parses with json.loads(parse_constant=raise).
- Lengths:
  - np.arange(120) gives 120 values, the last 119.0;
  - a 120x2 matrix gives 120 rows;
  - a date-indexed pd.Series of 100 gives 'values' of 100 and 'index' of date strings;
  - a DataFrame of 80 rows gives 'data' of 80 rows and keeps 'index'.
- Markers:
  - garch.nu has the normal-innovations wording;
  - garch.nu_interval_95[1] has the interval wording, not 'normal innovations';
  - garch.half_life_interval_95[1] has the interval wording;
  - garch.half_life, garch.uncond_vol_365, kimchi.half_life_days and adf_p have their registry meanings;
  - the generic NaN, +inf and -inf markers appear where expected.
- Types:
  - '"i64": 7';
  - np.bool_ becomes true;
  - dt64, td64, date and Timestamp give the same strings as today.
- Keys: a tuple key gives '(1, 2)'; an np.int64 key gives '3'; True and None keys give 'true' and 'null'.
- Privacy: a DataFrame column 'account_balance' and a 'holding' key inside an object ndarray are absent.
- The input is not mutated.

test_synthetic_crypto_and_etf_send_nu_infinity_as_normal_innovations:
- Build with CW.analyze(source='synthetic', card_loader=lambda p: [], include_balances=False) and with EW.analyze('122630', source='synthetic', card_loader=lambda p: [], history_loader=lambda c, source, days: synthetic_history(c, days=days)).
- Patch socket.socket.connect, load_cards and family_ledger to raise.
- The content contains '"nu": "+inf: normal innovations' and VALUE_NOTE.
- The JSON segment is strict, and no bare Infinity or NaN appears.

test_oversized_or_unserialisable_payload_is_refused_before_any_request:
- One byte over the limit (Hangul plus ASCII padding) gives PAYLOAD_TOO_LARGE, and post is not called.
- A payload exactly at the limit is sent.
- Patching ai_payload_json to raise gives PAYLOAD_INVALID, and post is not called.
- Both languages of PAYLOAD_TOO_LARGE contain '180,000'.

test_flet_spinner_clears_when_the_payload_cannot_be_prepared:
- payload_fn raises ValueError.
- deep_host holds a single _ErrorNotice with code PAYLOAD_INVALID.
- rows[3].controls[-1].visible is False.

New, in tests/desktop_commentary_acceptance.py:
- test_native_size_limit_matches_the_send_limit: at 179,999, 180,000 and 180,001 B (the c9 method), commentary_payload accepts if and only if deep_analysis with fake HTTP does not return PAYLOAD_TOO_LARGE.
- test_consent_status_names_the_fixed_instructions: 'ko' shows '고정 작성 지침'; 'en' shows 'fixed writing instructions'.

Commit message: "Send AI payloads as strict JSON with full arrays and meaning-bearing non-finite markers (§10 NEW-M6-12, NEW-M6-19: limitation b)".

=== COMMIT 3 — (a) NUMBER CHECK + (d) LABEL ===

New pure module core/research/ai_output_check.py (re, json, math and dataclasses only):
- NumberCheck, a frozen dataclass: checked, not_found, question_only, found, coarse_found, skipped (tuples and ints).
- number_check(text, sent_payload, question='').
- check_line(check, language).
- AI_LABEL.
- COARSE_SIGNIFICANT_DIGITS = 2 and MAX_LISTED = 10.

References

sent_payload is json.loads(sent.text).

Data references:
- (i) numeric leaves: int and float, bool excluded.
- (ii) string leaves that are a whole formatted number, matched by ^\s*[+\-−]?(\d{1,3}(,\d{3})+|\d+)(\.\d+)?\s*(%|bp)?\s*$. Write the escaped hyphen exactly: unescaped, '+-−' is a character range that matches letters. This includes codes made only of digits, such as the ETF code '122630', so an AI citing the code is 'found'.
- (iii) every run of digits (with an optional decimal part, % or bp) inside the other free-text string leaves, such as ETF sleeve_price_basis 'σ=27%', 'SESSIONS/252' or the crypto funding interpretation. These are excluded: marker strings starting 'NaN:', '+inf:' or '-inf:', and strings that are ISO dates or datetimes.

Never counted: keys, date strings, marker strings, _SYSTEM, the kind line and VALUE_NOTE.

Question references are every run of digits in the question string deep_analysis received, after strip, with no skip rules (years and hyphenated windows included). For the macro report kinds this includes REPORT_PROMPTS, so '252-session' gives 252. Numbers matched only there go to question_only.

Tokens in the AI text

Masked first:
- ISO dates and datetimes;
- YYYY/M/D;
- D/M/Y or M/D/Y with '/' (\b\d{1,2}/\d{1,2}/\d{2,4}\b);
- dotted YYYY.M.D (\d{4}\.\s?\d{1,2}\.\s?\d{1,2}\.?);
- hh:mm(:ss);
- 'YYYY년 M월( D일)' and 'M월( D일)', including a month on its own such as '10월';
- 'Month D(, YYYY)' with (?!\d) after D, so 'October 2026' is not split;
- 'Month YYYY';
- 'D Month'.
Month names include the three-letter forms and 'Sept'.

Number pattern: \d{1,3}(,\d{3})+(\.\d+)? or \d+(\.\d+)?.

An optional unit follows after one optional space, matched longest first:
- %: '%' and '%p', 'percent', 'per cent', 'percentage point(s)', 'pp', '퍼센트(포인트)';
- bp: 'bp', 'bps', 'basis point(s)', '베이시스포인트';
- x: 'x', '×', '배'.

A token is skipped (counted in skipped) when:
- the previous character is an ASCII letter, digit, '_', '.' or ',';
- the previous character is '-', '–' or '/' and is itself preceded by an ASCII letter or digit;
- it directly follows an index name and one space: S&P, KOSPI, KOSDAQ, Nasdaq, FTSE, Nikkei, Russell, Stoxx, DAX or CAC;
- the next character after the unit is an ASCII letter, digit or '_';
- it is a unitless compound modifier: number, '-', then a letter or digit (10-year, 1-week, and ranges such as 15-20% or 0.38-0.47, which are therefore not checked);
- it is a percentage followed by VaR, CVaR, ES, 'expected shortfall', 'confidence', CI, 'interval', 신뢰 or 구간;
- it is unitless and followed by thousand, million, billion, trillion, mn, bn or tn;
- it is a unitless INTEGER followed by 년, 개월, 달, 주, 거래일, 영업일, 일, 세션, 분기, 시간, 번째 or 차, unless the word is 달러, 차이 or 주식. Decimals before these words are counted, for example a 7.7일 half-life, or 9.99일 때 ('when it is 9.99');
- it is unitless and followed by 만, 억, 조 or 천, unless the word is 만큼;
- it is a unitless four-digit integer from 1900 to 2100 with no comma (a year). Integer prices in that range written without a comma are skipped too.

Hangul particles after a number are allowed: 0.42이며, 15.3%입니다, 105.2원, 8bp로. The sign is ignored.

Matching

- Let c be the cited absolute value, d its printed decimals and u its unit.
- Scales: '%' uses {1, 100}; 'bp' uses {1, 100, 10000}; x and no unit use {1}.
- c is found when, for some reference v and scale s, |c − |v|·s| ≤ 0.5·10^−d (plus 1e-9 relative), or c equals |v|·s truncated to d decimals.
- Precedence: data first, then question_only, else not_found.
- A data match with 2 or fewer significant digits counts as coarse_found.

Calibration (probe_proto.out, measured on the three synthetic payloads with the earlier rules; the free-text references added here raise these rates slightly, not measured):

| Cited form (2 or fewer significant digits) | Chance match |
|---|---|
| Integer 1-99, no unit | 9-19% |
| 0.xx | 17-24% |
| x.x | 3-16% |
| x.x% | 12-24% |
| Integer bp 1-99 | 35-44% |

| Cited form (3 significant digits) | Chance match |
|---|---|
| Unitless | 0-3% |
| xx.x% | 3-4%; 13% on the 425-leaf derivatives board |

Verified cases (probe_proto2 and challenge c6, with the corrected rules in proto_fix.py)

Not found:
- invented 9.99 and 47.5%;
- invented 9.99일 때 and 7.77만큼.

Found:
- 15.3% against 0.153;
- 8bp against -0.0008;
- -80.3bp against -80.25;
- 2.35% against '2.345%';
- 67,012달러 against 67012.34.

Question-only:
- 2.40 that is only in the question;
- 252 sessions, from the weekly prompt's '252-session'.

Skipped:
- (1991);
- 2y/5y/10y;
- 5th;
- M6-19;
- 2026-11-03;
- 'November 3, 2026';
- 10-year and 1-week;
- 3억;
- 52주;
- 95% VaR;
- 1.2 billion;
- S&P 500;
- KOSPI 200.

No spurious tokens (now masked) from:
- 'October 2026';
- '03/11/2026';
- '2026.11.03';
- '10월'.

Documented limits:
- Swapped measures (volatility 0.42, Sharpe 15.3%) are still 'found'; the check is not semantic.
- Enumerations '(1)', 'T+2' and 'eta = 0' are coarse chance matches.

deep_analysis

- After success: try check = number_check(text, json.loads(sent.text), question.strip()) / except Exception: check = None.
- Return Analysis(text, model, stop_reason=stop, number_check=check), with the field number_check: NumberCheck | None = None.
- The check never changes text, error_code, payload or verdict, and never blocks display.

Label and check texts

AI_LABEL
- EN: "AI commentary · not verified. Claude wrote this from the data sent; QUANTGEN does not check its reasoning, and the same request can give different text. It does not change any official verdict."
- KO: "AI 해설 · 검증 안 됨. Claude가 전송한 데이터로 쓴 글이며 QUANTGEN은 그 논리를 확인하지 않습니다. 같은 요청에도 다른 글이 나올 수 있습니다. 공식 판정은 바뀌지 않습니다."
- The label covers (d) as well.

check_line, simple cases:
- None:
  - EN: "Number check: not run."
  - KO: "숫자 대조: 실행하지 않음."
- checked == 0:
  - EN: "Number check: the commentary cites no numbers to compare."
  - KO: "숫자 대조: 해설에 대조할 숫자가 없습니다."

check_line, general case, EN:
- "Number check ({checked} checked): not found in anything sent: {list|none}."
- If not_found: " A number that was not found may be derived (a difference or a ratio) rather than wrong."
- If question_only: " Only in the question text (your question or the report-format instructions), not in the calculation data: {qlist}."
- If coarse_found: " {k} of the matches have two significant digits or fewer and could match by chance."
- Always: " A match means only that the number occurs somewhere in the data sent, allowing rounding and %/bp scaling; its sign, the measure it refers to, and verdict words are not checked."

check_line, general case, KO:
- "숫자 대조(확인한 숫자 {checked}개): 전송한 내용에서 찾지 못한 숫자: {list|없음}."
- If not_found: " 찾지 못한 숫자는 틀린 값이 아니라 차이나 비율처럼 계산해 낸 값일 수도 있습니다."
- If question_only: " 계산 데이터가 아니라 질문 문장(사용자 질문 또는 보고서 형식 지침)에만 있는 숫자: {qlist}."
- If coarse_found: " 일치한 숫자 중 {k}개는 유효숫자가 두 자리 이하라 우연히 일치했을 수 있습니다."
- Always: " 일치는 그 숫자가 전송한 데이터 어딘가에 있다는 뜻일 뿐입니다(반올림과 %·bp 환산 허용). 부호, 숫자가 가리키는 항목, 판정 단어는 확인하지 않습니다."

Lists show the first 10, then " and {n} more" / " 외 {n}개".

Flet (ui/ai_panel.py)

class _CheckNotice(ft.Container):
- Its render_locale(ctx) sets self.ctx = ctx, as _ErrorNotice does; otherwise translate_controls re-renders it on every update.
- It builds an ft.Column of two muted size-11 ft.Text: AI_LABEL[lang] and check_line(getattr(result, 'number_check', None), lang).
- lang is 'ko' if ctx.language == 'ko', else 'en'. Fallback locales already report 'en'.
- The locale comes from page.qg_locale, defaulting to en_US.

Panel changes:
- The success branch becomes [the unchanged engine chip Row, the unchanged ft.Text(result.text), _CheckNotice(result, page)].
- The error branch is unchanged, and new controls live only inside deep_host.
- In the docstring at :7-8, 'streams' becomes 'shows'.

Native (quantgen_desktop/commentary.py)

__init__:
- Add self.check_note = label('', 'muted') right after self.output (:61).
- It starts empty, so tests/desktop_language_acceptance.py:37-42 holds.

finished(), success:
- The output text stays exactly safe_detail(result.text).
- check_note:
  - setText(AI_LABEL['ko'] + '\n' + check_line(nc, 'ko'));
  - then localized_text = {'en': AI_LABEL['en'] + '\n' + check_line(nc, 'en'), 'ko': <KO>};
  - then retranslate().
- Export: append the sections AI_LABEL['en'] and check_line(nc, 'en') after the existing line at :133.
- Request fields: 'stop_reason': getattr(result, 'stop_reason', '') or 'NOT_RECORDED', 'verification': 'NOT_VERIFIED', 'number_check': asdict(nc) if nc else None.
- make_report keeps verdict NOT_RUN.

Clearing:
- invalidate(), failed() AND submit() at :117, where output and report_actions are cleared, call self.check_note.setText('').

Untouched:
- The success status (:134) and translations.py:549, which avoids the template-order trap and any change to core/ui_dynamic_messages.py.

Tests, commit 3

New tests/ai_output_check_acceptance.py, pure and with no network:
- Every case under 'Verified cases', including the Korean ones (9.99일 때, 7.77만큼, 67,012달러, 0.42차이, 10월, 2026.11.03).
- The English ones: October 2026, 03/11/2026, 95% VaR, 1.2 billion, S&P 500, KOSPI 200, and 252 sessions under the weekly prompt.
- The [+\-−] regex refuses 'A12', 'Q3', 'M6' and 'T10'.
- '27%' is found against ETF-like sleeve_price_basis text.
- '122630' is found against the code string.
- Coarse counting.
- Truncation with 'and 3 more' / '외 3개'.
- check_line in both languages for None, zero numbers and the general case.
- Inputs are not mutated.
- The main session must add the module to .github/workflows/runtime-smoke.yml at :6 (paths) and :90 (modules).

tests/ai_connection_acceptance.py:
- Success has a non-None number_check and stop_reason 'end_turn'.
- Patching number_check to raise still gives success, with number_check None.

tests/ai_payload_acceptance.py, test_flet_success_shows_label_and_number_check:
- Use the real deep_analysis with an end_turn body citing 9.99.
- The text is unchanged, AI_LABEL['en'] is shown, and a line lists 9.99.
- ko_KR shows '검증 안 됨' and '숫자 대조'; en_US switches back.
- A Mock runner returning Analysis('x', 'fixture') shows 'Number check: not run.'.
- load_cards and family_ledger are patched to raise.

tests/desktop_commentary_acceptance.py, test_success_label_and_export_stay_advisory:
- output == 'Fixture commentary'.
- check_note switches between EN and KO on ui_language.
- Report sections include the label and the check line.
- parameters.verification == 'NOT_VERIFIED' and verdict == 'NOT_RUN'.
- refresh_sources(), a new submit() and a later failure each clear check_note.

Existing tests that build Analysis with two arguments must keep passing:
- tests/desktop_commentary_acceptance.py:31, :81, :88 and :100;
- tests/ai_payload_acceptance.py:56 and :71;
- tests/letf_ai_payload_acceptance.py:26;
- tests/etf_sleeve_disclosure_acceptance.py:678;
- tests/fx_basis_disclosure_acceptance.py:152;
- tests/desktop_letf_ai_acceptance.py:45.

Commit message: "Label AI commentary as not verified and add an advisory number check (§10 NEW-M6-12, NEW-M6-19: limitations a and d)".

=== HOW TO VERIFY EACH COMMIT ===

1. Before running any module, grep it for 'asset_expansion/cache' and for cache-CSV helpers. The modules below had 0 hits; ficc_acceptance's 'cache' is the provider cache, and only its function pin is run. Never run tests/macro_m1_pit.py, tests.macro_m9_lab, tests.macro_m8_pipeline or tests/run_all.py.
2. Run with cwd s10mc, PYTHONPATH=., QT_QPA_PLATFORM=offscreen and PYTHONDONTWRITEBYTECODE=1:
   v313/bin/python -B -m unittest tests.ai_connection_acceptance tests.ai_payload_acceptance tests.desktop_commentary_acceptance tests.desktop_letf_ai_acceptance tests.letf_ai_payload_acceptance tests.desktop_language_acceptance tests.etf_sleeve_disclosure_acceptance tests.fx_basis_disclosure_acceptance tests.desktop_typography_acceptance
   desktop_typography_acceptance scans every string literal in core/research/*.py and core/quant/insights.py for bundled-font glyphs; probe c4 found none missing in the prototype strings. From commit 3 on, add tests.ai_output_check_acceptance.
3. Call these directly:
   - tests/ficc_acceptance.py:700 test_report_prompt_and_deep_analysis_degrade_without_network;
   - tests/quant_acceptance.py:525 test_deep_analysis_without_key_degrades_without_network;
   - every function in tests.flet_api_guard.tests() (baseline: 4 ok, probe c8).
4. git grep -n "\"tools\"\|'tools'" -- core/quant/insights.py must return nothing (the tests/macro_m1_pit.py:1079 pin).
5. core/ficc/insights.py:744-749 still gives engine 'none' on the no-key path.
6. The baseline before commit 1 is 17 OK (probe c7).

=== OUT OF SCOPE / ADJACENT ===

- These carry other IDs and are not touched:
  - D03-04: no synthetic-disclosure rule in _SYSTEM;
  - D03-01: the Crypto FX source;
  - P01-13: import time;
  - NEW-M6-18: done.
- Adjacent finding, from reading quantgen_desktop/market_tools.py:209 and quantgen_desktop/tools.py:18-19: the Native crypto table shows GARCH nu = +inf as '—', so the Native AI payload loses 'normal innovations' before plain(). This is a separate task.
- Ledger overlap:
  - ⑬-9/a (handoff LEDGER.md:110, PR46) set the rules kept here.
  - ⑬-9/b, still open, is where real max_tokens and refusal frequency should be measured.
- The main session updates these records:
  - SECTION10_QUEUE :704-713 and :784-793;
  - SECTION10_TRIAGE;
  - FACTS;
  - ui_website_updates;
  - research_status;
  - README;
  - docs/compliance/source-review.json, which hashes every source changed here: core/quant/insights.py, core/research/ai_connection.py, core/research/ai_payload.py, ui/ai_panel.py, quantgen_desktop/commentary.py, quantgen_desktop/translations.py, core/ui_legacy_messages.py if edited, and the test modules it lists (tests/ai_connection_acceptance.py, tests/ai_payload_acceptance.py, tests/letf_ai_payload_acceptance.py). It also needs entries for the new core/research/ai_output_check.py and tests/ai_output_check_acceptance.py.
  - runtime-smoke.yml: suggest adding these to the :6 paths as well: core/research/ai_connection.py, core/research/ai_payload.py, core/research/ai_output_check.py, ui/ai_panel.py, quantgen_desktop/commentary.py and tests/ai_connection_acceptance.py.
- Do not edit those records here.

=== MAPPING NOTE ===

The pairing between the two IDs and the limitations is still ambiguous.

Where the IDs appear:
- NEW-M6-12 and NEW-M6-19 appear only in the related-errors cell of model register entry 149 (2da6469:docs/nautilus_bridge/MODEL_LIMITS_REGISTER_2026-10-28.md:3454-3473; summary row :452). The known-errors register lists both with no sentence.
- SECTION10_QUEUE marks both mapping_needs_disambiguation true, reproduction NOT_RUN and correction NOT_IMPLEMENTED (:704-713 and :784-793 on faf9f3b).
- Neither ID is in LEDGER.md.

What the other IDs in that cell cover:
- D03-04: the synthetic-disclosure rule.
- D03-01: the Crypto FX source.
- P01-13: app import time.
- NEW-M6-18: the Upbit holdings payload, done.

That leaves these limitations without an ID:
- (a) the output is never verified;
- (b) arrays are cut to 50 elements, and NaN and Infinity go out as bare tokens;
- (c) stop_reason is never read;
- (d) the same input can give different output, which can only be labelled.

The register's close method (MODEL_LIMITS:175) covers (a) and (c). Reading the IDs as code defects with line citations gives {(b), (c)} just as well, so the '12 = (a), 19 = (c)' hint is dropped.

Following Crypto PR #68 (NEW-M6-14 and NEW-M6-22, LEDGER.md:138 and :140), all four limitations are fixed:
- commit 1 covers (c);
- commit 2 covers (b);
- commit 3 covers (a) and (d).

Record both IDs against all three commits, and name which limitation each commit closes.

=== OWNER CHOICES (defaults used) ===

1. Text cut off at max_tokens.
   - Default: discard it (OUTPUT_LIMIT).
   - Alternative: show it under a 'cut off at the output limit' banner and keep it out of export.
   - MODEL_LIMITS:175 means 'mark it as cut off'; it does not require discarding.
2. stop_sequence.
   - Default: INCOMPLETE_RESPONSE.
   - Alternative: accept it, but only if stop sequences are ever added to the request.
3. Output budget.
   - Default: no change to max_tokens 1500, effort or thinking. Measure under ⑬-9/b first.
   - Any thinking setting depends on the model: thinking {type: disabled} is accepted on Sonnet 5 and returns a 400 on Sonnet 5.5 and Opus 5.5.
4. Native consent text.
   - Default: reworded.
   - Alternative: keep it and show VALUE_NOTE in the preview.
5. Number check thresholds and scope.
   - Default: 2 or fewer significant digits counts as coarse.
   - Default: verdict words are not compared.
   - Default: the English and Korean skip lists above; ranges are not checked.
6. Native report nulls.
   - Default: keep plain() turning non-finite values into null, which is the report contract.
7. Native crypto table showing '—' for nu = +inf.
   - Default: a separate task.
8. Flet label placement.
   - Default: a label line, with no new chip.
9. Export language.
   - Default: English label and check line in the canonical report, like the existing 'AI-generated commentary' line. A Korean ZIP shows them in English.
10. VALUE_NOTE trigger.
   - Default: appended when there are markers or nulls, so most payloads that hold None change.
   - Alternative: a null-only sentence for payloads without markers.
11. Pairing of NEW-M6-12 and NEW-M6-19.
   - Default: both IDs recorded against all three commits.
