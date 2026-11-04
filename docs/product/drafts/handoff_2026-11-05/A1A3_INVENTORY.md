# A1·A3 조사 결과 (inventory 4건, 읽기 전용)

> **상태: 미검증 초안 (handoff 자료).** 2026-11-05 Claude 세션이 주간 사용량 한도로 멈출 때 백그라운드 워크플로 결과를 그대로 옮겼습니다.
> 소유자 승인 전이며, 반박 검토(challenge) 단계 전에 멈췄습니다. 본문의 `/tmp/claude-0/...` 경로는 그 세션의 임시 폴더라 이제 열 수 없습니다.
> 이 폴더는 main에 병합하지 않습니다. 확정본은 새 PR에서 `docs/product/` 아래 정식 문서로 만듭니다.


## Native(PyQt6) 한국어 용어 조사

NATIVE (PyQt6, quantgen_desktop/) KOREAN-UI SWEEP — worktree s10 at 516953a. `git diff --quiet faf9f3b HEAD` passed, so the tree is identical to main faf9f3b. The sweep was read-only: `git status --short` was empty before and after. Scratch files were written only under /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3.

0. METHOD
- Runtime sweep [run]: harness.py and harness2.py built ResearchWindow(language='ko', auto_refresh=False) offscreen with these guards: requests and socket network blocked, dotenv.load_dotenv and dotenv_values patched (no .env read), and core.quant.gate_ledger.family_ledger blocked. Data came from the fixtures in tests/desktop_acceptance.py and tests/desktop_macro_acceptance.py (synthetic curves, FX and histories).
- Sub-tools run:
  - Every sub-tool of Rates(4), FX(3), Structuring(4), Macro sheet(3), Macro v2(3), Signals(3), Strategy(2) and Connections(5).
  - Bonds (the default tool; the scenarios table rendered).
  - Derivatives, ETF and Crypto with the synthetic source.
  - KRX: refusal, daily and a quote fixture.
  - Monte Carlo: gbm, garch_t, bootstrap and jump.
  - Portfolio.
- Captured per widget: labels, buttons, combo items, tabs, table headers, first-column cells, placeholders, tooltips, chart footers and legends, and bar labels. Each was recorded with its English source and the Korean actually shown.
- Full per-pane list (1,549 rows; columns page, pane, kind, english_source, korean_shown, flags): /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/out/inventory.tsv
- Same list as plain text: /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/out/all.txt
- Raw records: /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/out/records.json and /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/out/records2.json
- Catalog analysis: /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/out/catalogs.json
- Inventory flag counts: EN_ONLY 243, MIXED 89, RAW_STATUS 82, COLLISION 55, TERM:거래일 31, TERM:측정 항목 8, TERM:측정값 3, TERM:관측 창 2, TERM:필드 2. 필드 also appears in the KRX/ETF quote tables, which harness2 checked.
- [read] means the exact source line was read.

1. HOW NATIVE KOREAN IS RESOLVED (root cause of many defects)
- quantgen_desktop/translations.py:640-644 display() calls translate(), which looks things up in this order:
  1. The KO dict. It is built from `(_PAIRS + _TERMS)` (line 592), so a _TERMS entry silently overrides a _PAIRS entry.
  2. display_prose_catalog, appended to _PAIRS (587-588).
  3. macro_narrative_language.PAIRS, which overrides everything before it (610-612).
  4. Core constants (614-620).
  5. Templates compiled with re.S (596-602), tried on the WHOLE multi-line text (628-631).
  6. The CMS grammar (632-634).
  7. A per-line split (635-636).
  8. If nothing matched, ctx.text() (core/i18n.py:46-60): core/ui_legacy_messages.py EN_TO_KO (shared with the Flet app), then the core/ui_messages.py LEGACY keys, then core/ui_dynamic_messages.
- Other Korean sources:
  - Inline ko/en pairs: watchlist.py, markets_view.py, market_chart.py and core/research/stock_profile.py.
  - ctx.t keys in indicator_guide.py and data_rights.py.
  - localized_text variants from the *_narrative.py and *_language.py modules.
- Result-table first-column captions translate only when headers[0]=='Metric' (tools.py:229-230) or when the pane calls localize_columns or localize_cell (model_narrative_language.py:11-29). bonds.py builds its own tables with neither, so every bond caption stays English.
- Verified at runtime: '필드' (Field), '구성 지표' (Component), '밝게' (Light), '몬테카를로' (Monte Carlo tab), '주식위험프리미엄 · %' (ERP · %) and '검증 판정' (verdict) all come from the shared legacy/Flet fallback, not from the Native catalog.

2. COUNTS PER CATALOG FILE
- translations.py: 563 'en|ko' lines.
  - Blocks: _PAIRS 9-248 = 239; _TERMS 251-466 = 215; 469-480 = 11; 483-563 = 80; 566 = 2; 568 = 2; 570-584 = 14.
  - The final KO dict has 774 keys (it includes the display-prose and macro pairs, 2 core constants and 3 aliases at 605-608).
  - 1 internal conflict: 'Instrument' at 198 (종목) vs 313 (상품); 상품 wins.
  - 39 Korean values mix in English words; 26 Korean values carry raw status tokens.
- display_prose_catalog.py: 167 pairs (21-187) plus cms_schedule_korean (5-18).
  - 1 shadowed conflict: 'Margin · per 100' at 93 (마진 · 100당) loses to translations.py:352 (마진 · 액면 100당).
  - 2 mixed values (106, 187).
- macro_narrative_language.py: 49 pairs (4-30) and 3 generators.
  - It overrides translations.py for: 'Macro sheet' (거시 지표표, line 6, over 489 매크로 현황), 'Daily commentary' (일일 시장 해설, 6, over 379 일별 해설) and 'Last' (최근값, 14, over 431 최종 관측일).
  - 2 mixed values.
- market_narrative_language.py: 6 generators, 83 lines containing Hangul.
- market_diagnostics_language.py: 3 generators, 25 lines.
- model_narrative_language.py: 5 functions, 41 lines.
- rates_narrative.py: 6 functions, 56 lines; dicts SHAPES (4), REGIMES (7) and COMPONENTS (3) at 11-15.
- fx_narrative.py: 4 functions, 55 lines.
- bonds_portfolio_narrative.py: 6 functions, 56 lines; _NOTE_PARTS has 4 patterns (15-32).
- Inline pair modules:
  - watchlist.py: 72 _text call sites, plus _NAMES 12, _STATUS 7 and _LIVE_STATUS 8 (31-66).
  - markets_view.py: 37.
  - market_chart.py: 74 (20 of its lines use 해요체).
  - paper.py: 3.
  - indicator_guide.py: 40 ctx.t calls plus 35 t().
  - data_rights.py: 12 ctx.t.
  - core/research/stock_profile.py: 66 t(ko,en).
- Pane files with Korean literal sources (Korean shown as is, English via reverse lookup), counted as lines containing Hangul: app.py 74, rates.py 35, fx.py 26, macro_records.py 26, structuring.py 24, bonds.py 19, commentary.py 18, portfolio.py 16, strategy.py 15, tools.py 13, signals.py 13, macro.py 11, connections.py 10.
- Shared fallbacks reached by Native:
  - core/ui_legacy_messages.py EN_TO_KO: 467 entries. 35 of them give different Korean for the same English than the Native catalog (Native wins in Native, so the Flet app shows a different word). Examples: Provider 공급자/공급처, Model 모델/모형, Sessions 거래일/관측 수, Strike 행사가격/행사가, Research Library 연구 보관함/연구 라이브러리, Macro sheet 거시 지표표/거시경제 관측, Macro v2 매크로 v2/거시경제 v2, Volatility regime 변동성 상태/변동성 국면, Metric 측정 항목/지표.
  - core/ui_messages.py MESSAGES['ko']: 177 keys.
- core/education/glossary.py: 32 terms used by the Indicator guide, including 샤프 지수, 최대낙폭 · MDD, 몬테카를로 시뮬레이션, GARCH 모형, 부트스트래핑, 볼록성 · 컨벡시티, 그릭스 · 델타·감마·베가·세타, 내재변동성, SABR 모형, 원금보장형 구조화 상품, 선물환, 캐리. This is the natural single source for the "one glossary" (UI-10). The UI labels currently disagree with it (see GL-1).

3. PER-PANE RUNTIME COUNTS [run]
Distinct visible strings in Korean mode, excluding accessibility names and pure codes.

| Pane | Visible | Korean | Mixed | English only | Raw status |
|---|---|---|---|---|---|
| rail | 14 | 13 | 0 | 1 | 0 |
| home | 13 | 10 | 3 | 0 | 1 |
| home watchlist | 23 | 21 | 1 | 0 | 0 |
| markets_view | 25 | 19 | 0 | 0 | 0 |
| tools page | 10 | 10 | 0 | 0 | 0 |
| bonds | 47 | 25 | 4 | 16 | 1 |
| rates | 132 | 50 | 10 | 62 | 4 |
| fx | 109 | 99 | 4 | 6 | 2 |
| structuring | 122 | 103 | 10 | 9 | 1 |
| derivatives | 70 | 49 | 4 | 14 | 1 |
| etf | 44 | 30 | 5 | 8 | 2 |
| krx | 29 | 22 | 0 | 7 | 1 |
| crypto | 62 | 35 | 5 | 18 | 2 |
| macro sheet | 74 | 61 | 3 | 0 | 23 |
| macro v2 | 71 | 22 | 4 | 45 | 8 |
| Monte Carlo/Build | 46 | 32 | 5 | 6 | 6 |
| strategy | 65 | 32 | 8 | 25 | 5 |
| risk page | 13 | 10 | 0 | 1 | 0 |
| portfolio | 40 | 23 | 7 | 10 | 1 |
| signals | 101 | 90 | 5 | 1 | 2 |
| paper | 25 | 24 | 1 | 0 | 1 |
| library | 11 | 9 | 2 | 0 | 1 |
| commentary | 9 | 9 | 0 | 0 | 0 |
| system | 13 | 12 | 1 | 0 | 2 |
| connections | 24 | 23 | 0 | 1 | 0 |
| rules | 56 | 52 | 4 | 0 | 0 |
| data rights | 7 | 6 | 1 | 0 | 0 |
| indicator guide | 30 | 28 | 1 | 0 | 0 |

- The Markets stock chart pane (market_chart.py, checked by harness2) is entirely Korean.
- Worst panes: Rates, Macro v2, Strategy, Crypto, Bonds, Derivatives.

4. FLAGGED FINDINGS (current → proposed pairs are in items)

A. UI-1 naming [run]
- The tool buttons show "거시 지표표" and "매크로 v2" (app.py:55-57 TOOL_PANES).
  - 거시 지표표 comes from macro_narrative_language.py:6, which overrides translations.py:489 매크로 현황.
  - 매크로 v2 comes from translations.py:490.
- Related labels: the Macro pane title "Macro · 시장 관측과 로컬 해설" (translations.py:242, macro.py:30) is mixed; the macro sheet caption at translations.py:239 / macro_narrative_language.py:8-9 is mixed.
- The Flet fallback has a third pair, 거시경제 관측 / 거시경제 v2 (core/ui_legacy_messages.py:232).

B. UI-2 status values
- Native never shows raw "OBSERVED" in the swept screens. watchlist.py:53 maps it to "일별 관측" (Home price tooltip and detail dialog; test pin tests/desktop_watchlist_acceptance.py:88).
- Raw tokens that ARE shown in Korean mode [run]:
  - Library run table: COMPLETED, NOT_RUN (app.py:1004-1005).
  - Home summary: "판정 NOT_RUN · 재현성 PARTIAL" and the raw model id "jump" (app.py:1007-1009).
  - Monte Carlo status: "COMPLETED · 검증 NOT_RUN · 재현성 PARTIAL" (translations.py:132).
  - Library caption (translations.py:121).
  - System panel: NOT_VERIFIED/NOT_FROZEN/NOT_INSPECTED/NOT_APPROVED (translations.py:126) and "749 PASS / 0 FAIL / 121 NOT_RUN" (translations.py:124).
  - Connections: CONFIGURED/NOT_CONFIGURED/REACHABLE/UNAVAILABLE (core/research/connections.py:33,53-56; connections.py:22), plus "CONFIGURED는 …" (translations.py:537).
  - Derivatives static-arbitrage check status: COMPUTED (market_tools.py:83).
  - ETF study decision: NOT_LOADED (market_tools.py:147).
  - Macro bar labels and table: "· SYNTHETIC" (18 rows).
  - Macro v2: ARMED, REJECT, BUILD_AS_INSURANCE, NOT_FROZEN, "context_log · NOT_LOADED" (macro_records.py:283).
  - Strategy: "판정: WITHHELD · No PASS / REJECT…".
  - FX SABR: "수치 해법 CONVERGED".
  - KRX: "UNAVAILABLE · 공급자 응답을…" (translations.py:529) and "EMPTY · …" (530).
  - "SYNTHETIC · …" (525, 527, 528, 541).
  - Paper/Rules [read, not run]: PAUSED (paper.py:293), rule status enum values (281, 296), "HALT 확인" (228).
  - Inconsistent: translations.py:535 already says "PCA 미실행", while elsewhere the same state reads "검증 NOT_RUN".
- STALE is worded 4 ways: 오래된 자료 (watchlist.py:52, markets_view card), 오래된 관측 여부 (FX header, translations.py:34), 오래된 값 · 조회 실패 (market_chart.py:1007), 수신 지연 (watchlist.py:238).

C. UI-6b Rates/KRX wording [run]
- 관측 창: "Lookback · sessions" → 관측 창 · 거래일 (translations.py:405, Rates curve form) and "Fast / lookback / RSI period" → 빠른 이동평균 / 관측 창 / RSI 기간 (translations.py:403, Signals form).
- 거래일 used as a field label or unit (31 inventory rows):
  - Sessions 거래일 (363; ETF, Strategy).
  - Horizon sessions · blank = expiry → 기간 거래일 · 공란 = 만기 (357; Derivatives/KOSPI200).
  - Paths / sessions → 경로 수 / 거래일 (display_prose_catalog.py:82).
  - Rebalance · sessions → 리밸런싱 · 거래일 (333).
  - Horizon · sessions → 분석 기간 · 거래일 (62).
  - Fan-chart footer "0 → N 거래일" (248).
- The Native KRX pane itself has no 관측 창 or 거래일. Its only field is "6자리 KRX 코드". The KRX pane's mistranslations are different: "Quote" → 호가 (translations.py:371), daily headers date/open/high/low/close/volume left raw (market_tools.py:276-277), and "Observations" → 관측.
- Rates provenance says "80 observations" in English (rates.py:60), while Bonds says "30 거래일" (bonds_portfolio_narrative.py:130-131).

D. UI-10 Field/Metric mistranslation and per-asset mixing
- The "Field" header → 필드 comes from the legacy fallback core/ui_legacy_messages.py:253 [run]. It appears in:
  - ETF Quote (market_tools.py:133).
  - KRX Quote (market_tools.py:272).
  - Macro v2 records (macro_records.py:251).
  - The Macro v2 tree header (macro_records.py:132), which stays English "Field / Recorded value" because QTreeWidget headers are not handled by LanguageController.
- Under "필드" the rows are raw English keys [run]:
  - KRX: ticker, name, price, change, change_pct, volume, market_cap, high, low, open, currency, per, eps, sector, listed_shares.
  - ETF: price, nav, premium_pct, tracking_error_pct, cu_units, lp_holding_pct.
- Elsewhere the same table type reads heading "측정값" (Metrics, translations.py:427) over column "측정 항목" (Metric, translations.py:566; pinned by tests/desktop_language_acceptance.py:77).
- The same Metric/Value table shape therefore reads 측정 항목/값 in FX, Structuring and Signals; 필드/값 plus English keys in ETF and KRX; and English captions in Bonds (no localized_columns, bonds.py:51).
- ETH/BTC table: only 'verdict' is translated (→ 검증 판정, legacy); n, last_ratio, adf_p and z_2y stay raw (market_tools.py:224-226).

E. UI-11a bond, derivative and structured terms [run]
- Bonds (bonds.py):
  - All 12 metric captions are English (82-87): Price, Yield, Macaulay duration, Modified duration, Convexity, DV01, z-spread, Curve price, Carry · 0.25 years, Roll-down, Carry + roll, Breakeven.
  - Value units are English (83-84, 87): "years", "currency / bp".
  - Headers are English: "Key tenor · years", "DV01 · currency / bp" (53); Shock · bp, P&L, P&L % (54).
  - Chart legend "Duration tangent" (88) and axes "Yield (%)" / "Price per 100" (52) are English.
  - Meanwhile the Korean narrative already says 매콜리 듀레이션 / 수정 듀레이션 / 볼록성 / z-스프레드 / 캐리 / 롤다운 (bonds_portfolio_narrative.py:56-80). The same screen therefore shows the Korean term in the prose and the English term in the table. The glossary says 볼록성 · 컨벡시티 and 듀레이션; Korean usage favours 맥컬리 over 매콜리.
- Structuring:
  - Headings "Greeks" (structuring.py:61), "Leg decomposition" (66), "Maturity payoff" (63) and "Hedge sheet" (68) are English.
  - Greeks column header "Risk" → 위험 (should be 민감도).
  - Leg "ATM call" and row "Leverage" stay English; chart labels "Payoff", "Underlying at maturity", "Per 100 notional" and "Realized 10y–2y spread · bp" stay English.
  - "Hedge 부호" is mixed (translations.py:533).
- Rates swaption rows are English (rates.py:93,100-102): Delta · per +1bp, Gamma · per bp², Vega · per 1bp normal vol, Theta · 1 day, Annuity, Premium / notional, Other-model vol.
- Rates swap rows are English (86-88): Par rate, Fixed, PV, DV01 · +1bp P&L, Carry · first period, Roll-down · 1y. Also "Key-rate DV01" and "Forward swaps" (89-90).
- Rates curve: 'Curve table' plus Zero/DF/Par/1y forward/Change · 20d (73); "PCA loadings" and "PCA variance" with Component/Explained/Latest score (81-82); level/slope/curvature are English in the table although the narrative says 수준/기울기/곡률 (rates_narrative.py:15).
- Rates simulation: Kappa, Half-life, Theta, Sigma, Initial rate, Terminal mean, P(terminal > threshold), "Horizon curve · median path", "Model zero" (111-116). Here "Theta" means long-run mean, which collides with option theta.
- FX option Greeks ARE translated (translations.py:445-451). Derivatives is mostly translated (display_prose_catalog.py:63-92), but its headings are English (market_tools.py:51,71,75,76,82): 'Futures & volatility', 'Implied volatility smile', 'Risk-neutral density', 'Hedge simulation', 'Static arbitrage checks'. Check keys call_vertical/call_butterfly/put_* stay raw (83).

F. UI-14/15 navigation
- 'Build & Test' → 설계 및 검증 (translations.py:46; source app.py:251, page title 521).
- 'Portfolio & Risk' → 포트폴리오 및 위험 (translations.py:47; app.py:251, 583).
- Also mentioned in translations.py:470 (the desktop migration text).
- Renaming to "분석" puts it right next to "분석 도구" (Analysis tools, translations.py:42) in the rail; the owner may want to confirm.
- The rail is sized from its widest label (app.py fit_sidebar 311-330), so shorter labels shrink it.

G. Same English, different Korean across panes [run unless noted]
- Forward: FX 선물환 (correct; translations.py:456). But Rates swaption metric "Forward" (rates.py:100) and Caplets header (rates.py:106) also show 선물환, which is wrong. Prose uses 선도/선도가격 (display_prose_catalog.py:63,155,163); rates narrative uses 선도금리.
- Equity: Structuring underlying 주식 (correct; translations.py:503). Strategy walk-forward y-axis 'Equity' (strategy.py:64) also shows 주식 — footer "OOS observations · 주식" — wrong. FX and Signals equity curves show 누적 가치.
- Component: Signals 구성 지표 (ok). Rates PCA 'Component' (rates.py:82) also shows 구성 지표, which is wrong (should be 주성분); the source is legacy core/ui_legacy_messages.py:240.
- Last: Macro sheet 최근값 (ok). FX "Data sources" date column (fx.py:38) also shows 최근값, which is wrong; translations.py:431 최종 관측일 is shadowed by macro_narrative_language.py:14.
- Light/Dark: 밝게 (core/ui_messages.py:152, which also has 'theme_light': 라이트 at :12) next to 다크 (translations.py:53).
- Monte Carlo: tab 몬테카를로 (legacy :232), but Home/Library text says "Monte Carlo" (translations.py:84,120); the glossary says 몬테카를로 시뮬레이션.
- Strike: 행사가격 (translations.py:434, fx_narrative) vs 행사가 (display_prose_catalog.py:72,77,108; option_disclosure; rates_narrative).
- Model: 모델 (translations.py:57) vs 모형 (14 lines: 정규 모형, 헤지 모형, 모형 비의존…, glossary "GARCH 모형").
- Provider: 공급자 (translations.py:100, market_tools, display prose) vs 공급처 (watchlist.py 21 lines, stock_profile, data_rights tree header).
- Sharpe: raw "Sharpe" (ETF, FX carry, portfolio header, Signals, Strategy rows), "최대 Sharpe" (translations.py:462), 샤프비율 (bonds_portfolio_narrative.py:22,89; market_narrative_language.py:67; sleeve_disclosure), 샤프 비율 (fx_narrative.py:56), 샤프 지수 (glossary).
- Principal-protected note: 원금보장형 노트 (combo, translations.py:335), 원금보장형 상품 (product cell, display_prose_catalog.py:141), 원금보장형 구조화 상품 (glossary). Reverse convertible: 역전환형 노트 (336) vs 역전환형 상품 (142).
- Spacing and wording drift: 발행 가격 (339) vs 발행가격 (prose 47); 액면 100당 (339, 352, 280) vs 100당 (prose 44, 46).
- Coupon: 표면금리 % (Bonds) vs 쿠폰 % (Structuring) vs 채권 쿠폰 % (Rates).
- Expiry: 옵션 만기 (324) vs 만기 (355).
- Curve-change regimes: rates_narrative.py:12-14 '금리 하락·기울기 확대' vs macro_narrative_language.py:18-19 '금리 하락·곡선 가팔라짐' for the same 'bull steepener'.
- Curve: 수익률곡선 (macro header) vs 수익률 곡선 (rates).
- UST: 미국채 (macro table) vs UST (macro narrative, Structuring caption).
- Daily: 일일 vs 일별.
- Quote → 호가 (translations.py:371) is used for the KRX tool and the ETF/KRX price-snapshot tables, which hold last price and OHLC, not an order book.
- Light theme also exists as 'Light · A|라이트 · A' (translations.py:52, unused by the current combo).

H. Mixed Korean/English inside catalog values [read]: 43 entries
- translations.py (39): 51, 60, 84, 93, 104, 118, 120, 129, 135, 145, 153, 159, 161, 163, 164, 167, 189, 190, 205, 206, 223, 235, 239, 241-244, 462, 470, 478, 526, 533, 545, 554-557, 559, 562.
- display_prose_catalog.py: 106, 187.
- macro_narrative_language.py: 5, 8.
- Key examples (proposals in items MX-*):
  - 239: "이 탭은 descriptive macro sheet입니다. v2 Overlay·Model cards·Research register는 …"
  - 533: "Hedge 부호"
  - 60: "Symbols · pairs는 y, x 순서"
  - 129: "Symbol과 유한한 양수 Target"
  - 135, 164, 167: "Price/Yield"
  - 153: "Frontier"
  - 159: "equal_weight는"
  - 161: "solver converged="
  - 163, 241-244: "Bonds ·", "Rates ·", "Macro ·", "Signals ·", "Structuring ·" pane titles
  - 189: "Rules ·"
  - 223: "Paper Trading ·"
  - 190, 478: "엔진 Arm"
  - 235: "Live 실행"
  - 205-206: "UTC offset"
  - 526: "Last prints only ·"
  - 545, 554-556: gate / book / refusal

I. Template bug (multi-line swallow) [run]
- translations.py:602 compiles templates with re.S and `.+?` groups, and translate() (628-636) tries them on the whole multi-line text before splitting lines. A first-line template therefore captures the following lines into a placeholder. Evidence:
  - Derivatives header: line 2 "Session synthetic · 135 strikes · rate 3.200% (assumed)" stays English (template display_prose_catalog.py:107 captured it into {asof}; source market_tools.py:44-45).
  - Strategy: "…누적 원장 설정 None⏎Walk-forward: IS 756 / … {'step': 42}개". A stray "개" lands after the dict because line 2 was swallowed into {count} (display_prose_catalog.py:119; source strategy.py:50-51).
  - ETF: "전략별 가격 기준: Simulated series … · 연구카드: NOT_LOADED" (display_prose_catalog.py:109).
- Fix: use `[^\n]+?` or drop re.S, or split lines before trying templates.

J. 13-8: English model, provider and inline notes still shown in Korean mode [run]
- Monte Carlo:
  - Metric rows (app.py:903-907): P5 / P50 / P95, Sample vol (ann.) / Next-session vol (ann.), P(loss), VaR 95 / CVaR, Paths / horizon / seed, P(terminal ≥ target), Horizon-average vol (ann.).
  - Notes (app.py:909-929): drift_note "risk premium: rf … convexity correction …"; the vol disclosure "Historical log-return sample volatility, annualized using 252 sessions." / "Next-session conditional forecast volatility…"; jump note "No >3σ daily moves … jump model degrades to GBM."; GARCH notes "Innovations are effectively normal…"; "Horizon-average volatility: …"; "GARCH fit:", "converged=… · persistence=… · half-life=… sessions", "at_bound:", "note:", "se_note:", "eta 95% profile interval:".
  - The bootstrap disclosure IS Korean.
  - Risk table headers P(loss)/VaR 95/CVaR/Source (app.py:593).
- Provider/panel notes:
  - "Simulated Treasury par curve (Nelson-Siegel random walk) — no market data provider was used." is shown TWICE on Bonds (panel.note and curve.note, bonds_portfolio_narrative.py:131-133) and also on Rates and Structuring (rates.py:60, structuring.py:40).
  - "Simulated series (GBM…) — no market data provider was used." (ETF, Strategy).
  - Rates swap/option provenance is fully English (rates.py:91, 94-95; e.g. "10y payer K=…, bootstrap curve … single-curve, ACT/365F, DV01 central +/-1bp.", "payer bachelier; single-curve, annuity discounted to today.").
  - Rates simulation series and params notes (rates.py:118).
  - FX "직접 입력한 금리: none" (translations.py:572 with a raw 'none').
- Strategy: decision reason, walk-forward note, chosen config dict, 'Study scorecard', Card/Decision headers, 'Validation statistics' with all 16 rows except Trades/Max drawdown (strategy.py:35, 55-62), 'Walk-forward equity', 'Benchmark' legend.
- Macro v2 (45 English-only strings):
  - Headings (macro_records.py:201-217, 261-279): 'Volatility labels · display only', 'Flags', 'Overlay records · values as recorded', 'Display-only books · not a recommendation', 'Inputs and fail-closed inputs', 'Provenance', 'Owner decisions / inputs / proposals', 'Macro model cards', 'Tech-fund drafts…', 'CRY-1 controls…', 'Design priors · not gate PASS', 'Other markets', 'Go / No-go register', 'Do not build', 'Cross-spec proposals · owner confirmation', 'Open questions', 'Backlog and council queue', 'Council resolutions and modules'.
  - Buttons 'Open Quant Council page' / 'Open Macro Neural Link page'.
  - Card captions from ui/macro_cards_view.py:32-34.
  - DISCLAIMERS and WEIGHT_CAPTION.
  - "Gate package:" (182).
  - Card table headers Card/Verdict/Disposition/Label/Book (200).
- Crypto (market_tools.py):
  - Weekday rows Mon…Sun (227).
  - 'Premium / volatility' (204); 'AR(1) amplitude half-life · observations' (206).
  - 'Kimchi premium' and 'Perpetual funding' charts (211, 218) with axes Days / Annualized · % / USDT per BTC and legend '7-day mean annualized %'.
- ETF (market_tools.py): 'ETF price / NAV' (130), 'Descriptive sleeve backtests' with sleeve keys trend/vol_target/buy_hold raw (145-148), 'Trend switch vs buy & hold' and 'Trend' legend (149-150), Sharpe header.
- Portfolio:
  - Comparison column suffix " · selected" / " · comparison" and True/False convergence (portfolio.py:69-70) [read].
  - Narrative "max-sharpe 포트폴리오", "THREE은" (bonds_portfolio_narrative.py:87).
  - "선택 목적 max_sharpe" (106), "risk_parity:" prefix.
- Particle and number style:
  - "10y payer은" (rates_narrative.py:49).
  - "RSI 62은" (display_prose_catalog.py:133-135).
  - "오 년" (core/ficc/forward_conventions.py:9; rates_narrative.py:27).
  - "일 년" (rates_narrative.py:29,56).

K. Raw internal ids shown as Korean-mode combo items [run]
- Rates: Method bootstrap/nelson_siegel/svensson (rates.py:12); Instrument swaption/cap/floor (15); simulation Model vasicek/cir/hull_white (19); Revalue none/bond/swap (21).
- Strategy Lab data source: synthetic/auto/kis/fmp/yfinance/crypto (strategy.py:12).
- Portfolio source: auto/fmp/kis/yfinance/synthetic (portfolio.py:26).
- Bonds source (hidden).

L. Tone
- market_chart.py uses 해요체 (20 lines, e.g. 379 "…늦게 반응할 수 있어요."); the rest of the app uses 합니다체.

M. Owner ruling check (provider/date columns not shown in live views, PR #71)
- The Native analysis tools still show such columns: Macro sheet 'Source' and 'Observed date' (macro.py:59); FX 'Data sources' table Provider/First/Last (fx.py:38); FX carry 'Rate date' (fx.py:46).
- Whether PR #71's ruling covers analysis tools is unverified (the ETF and KRX quote tables already hide as_of/source, market_tools.py:131-134, 270-274).

N. Tests that pin the current Korean
- tests/desktop_market_tabs_acceptance.py:22 (tool button list incl. 거시 지표表/매크로 v2 — exact string is '거시 지표표').
- tests/desktop_language_acceptance.py:77 ('측정 항목').
- tests/desktop_watchlist_acceptance.py:88 ('일별 관측').
- tests/desktop_language_acceptance.py:62 pins the English nav 'Build && Test' (unaffected by a Korean rename).

O. A1/A3 overlap (relevant to the owner's question about running A1 and A3 together)
- A1 touches: translations.py, macro_narrative_language.py, display_prose_catalog.py, the *_narrative.py files, core/ui_legacy_messages.py:253, core/ui_messages.py:152, and the captions and localized_columns in bonds.py, rates.py, fx.py, structuring.py, market_tools.py, macro_records.py, strategy.py, portfolio.py, app.py (nav/MC) and watchlist.py.
- A3 touches bonds.py (UI-11b side-by-side tables), app.py and strategy.py (UI-9 right-side explanations on 설계/검증), tools.py, chart_study.py and theme (glass separation, UI-12 term panel).
- Files both touch: bonds.py, app.py, strategy.py, tools.py and probably structuring.py.
- Running both at once is feasible if each file has one owner, or if A1's catalog-only changes merge first.
- UI-12's "알아보기" side panel and UI-10's glossary can share core/education/glossary.py.

### 확인하지 못한 것

These were not checked at runtime:
- Paper Trading and Rules screens after opening a paper session: rule status enum values, PAUSED, dashboard text and decision rows. These were checked only by reading paper.py:281-296.
- The Commentary pane after an AI request.
- The stock profile sections on the Markets one-stock page. They need a live profile; there are 66 t(ko,en) pairs in core/research/stock_profile.py, read only by count.
- The Bonds 'Scenarios' and 'Futures hedge' tools (only the default calculator ran; its scenario table did render).
- ETF with a real quote and the AZ/LETF tables (the quote table was rendered directly in harness2).
- KRX snapshot, indices, filings and financials outputs.
- Every QMessageBox, plus the Market details and Q-SCORE dialogs.
- Live data paths of any kind (network blocked).

Other limits:
- Per-pane counts come from synthetic fixtures; real data can add rows, e.g. more provider notes.
- Whether the PR #71 ruling (no provider or observation-date columns in live views) covers the Native analysis tools (Macro sheet, FX) was not checked.
- The QUANTGEN_REMAINING_2026-11-03 document is not in the repository, so the owner's wording was taken from the task text.
- Where the owner saw a raw "OBSERVED": no raw occurrence exists in the swept Native screens, so it may be in the Flet app (other sweep).
- The proposed Korean terms are suggestions for the owner's glossary decision, not checked against any official KOFIA or KRX term list.
- Nothing was changed and no tests were run. The test pins listed (tests/desktop_market_tabs_acceptance.py:22, tests/desktop_language_acceptance.py:77, tests/desktop_watchlist_acceptance.py:88) were found by reading only.

### 항목 목록 (84개)

```json
[
 {
  "id": "N1-a",
  "where": "app.py:55-57 TOOL_PANES 'Macro sheet'; macro_narrative_language.py:6 (overrides translations.py:489)",
  "current": "거시 지표표 (button and combo) / 매크로 v2",
  "proposed": "매크로 지표 / 매크로 v2 (one family name, 매크로, for both). Remove the dead translations.py:489 매크로 현황 and update tests/desktop_market_tabs_acceptance.py:22",
  "note": "UI-1 [run]. The Flet fallback says 거시경제 관측/거시경제 v2 (core/ui_legacy_messages.py:232); align it in the Flet sweep"
 },
 {
  "id": "N1-b",
  "where": "translations.py:242 / macro_narrative_language.py:5; macro.py:30",
  "current": "Macro · 시장 관측과 로컬 해설",
  "proposed": "매크로 · 시장 관측과 해설",
  "note": "Mixed language; 로컬 해설 is unclear"
 },
 {
  "id": "N1-c",
  "where": "translations.py:239 and macro_narrative_language.py:8-9 (Macro pane caption)",
  "current": "이 탭은 descriptive macro sheet입니다. v2 Overlay·Model cards·Research register는 분석 도구의 매크로 v2에서 확인합니다.",
  "proposed": "이 탭은 설명용 매크로 지표표입니다. v2 오버레이·모델 카드·연구 등록부는 분석 도구 › 매크로 v2에서 확인하세요.",
  "note": "[run]"
 },
 {
  "id": "NV-14",
  "where": "translations.py:46 (source app.py:251, 521)",
  "current": "설계 및 검증",
  "proposed": "설계/검증",
  "note": "UI-14. The English nav stays 'Build & Test'"
 },
 {
  "id": "NV-15",
  "where": "translations.py:47 (source app.py:251, 583)",
  "current": "포트폴리오 및 위험",
  "proposed": "분석",
  "note": "UI-15. It sits next to '분석 도구' (translations.py:42) in the rail; the owner may want '분석' vs '분석 도구' distinguished"
 },
 {
  "id": "ST-1",
  "where": "watchlist.py:53 _STATUS['OBSERVED'] (Home price tooltip / detail dialog)",
  "current": "일별 관측",
  "proposed": "정상 관측 (일별)",
  "note": "UI-2. Raw OBSERVED is not visible in the swept Native screens; update the test pin tests/desktop_watchlist_acceptance.py:88"
 },
 {
  "id": "ST-2",
  "where": "watchlist.py:52; translations.py:34 (FX header 'Stale'); market_chart.py:1007; watchlist.py:238",
  "current": "오래된 자료 / 오래된 관측 여부 / 오래된 값 · 조회 실패 / 수신 지연",
  "proposed": "지연 자료 (one word); FX column 'Stale' → 지연 여부",
  "note": "Same status, four wordings"
 },
 {
  "id": "ST-3",
  "where": "app.py:1004-1005 (Library run table), app.py:1009 (Home summary), translations.py:132, 121",
  "current": "COMPLETED / NOT_RUN / PARTIAL / '판정 NOT_RUN · 재현성 PARTIAL'",
  "proposed": "완료 / 미실행 / 부분 — e.g. '판정 미실행 · 재현성 부분'",
  "note": "Display label only; keep the raw token in exports or tooltips. translations.py:535 already uses 'PCA 미실행'"
 },
 {
  "id": "ST-4",
  "where": "translations.py:126, 124 (System panel)",
  "current": "데이터 NOT_VERIFIED · 공식 게이트 NOT_FROZEN … NOT_INSPECTED … NOT_APPROVED; 'PASS / FAIL / NOT_RUN'",
  "proposed": "데이터 미검증 · 공식 게이트 미동결 (문서 기록) / 동결 연구 미점검 · 공개 배포 미승인; 통과 / 실패 / 미실행",
  "note": "[run]"
 },
 {
  "id": "ST-5",
  "where": "core/research/connections.py:33,53-56 rendered by connections.py:22; translations.py:537",
  "current": "CONFIGURED / NOT_CONFIGURED / REACHABLE / UNAVAILABLE; 'CONFIGURED는 설정의 존재만 뜻합니다'",
  "proposed": "설정됨 / 미설정 / 접속 가능 / 응답 없음; '설정됨은 설정이 있다는 뜻일 뿐입니다'",
  "note": "[run]. Map at display time only"
 },
 {
  "id": "ST-6",
  "where": "translations.py:525, 527, 528, 541; macro bar labels and table '· SYNTHETIC'; app.py:909 '합성 데이터 · SYNTHETIC'",
  "current": "SYNTHETIC · 모든 시세는 합성 데이터입니다. / '미국채 2y · SYNTHETIC'",
  "proposed": "합성 데이터 · 모든 시세는 합성 데이터입니다. / '미국채 2y · 합성'",
  "note": "Avoid writing 합성 twice ('합성 데이터 · SYNTHETIC')"
 },
 {
  "id": "ST-7",
  "where": "translations.py:529, 530 (KRX status); market_tools.py:266, 279",
  "current": "UNAVAILABLE · 공급자 응답을 확인하세요… / EMPTY · 공급자가 빈 결과를 반환했습니다.",
  "proposed": "조회 불가 · 제공처 응답을 확인하세요. 대체 값은 만들지 않습니다. / 결과 없음 · 제공처가 빈 결과를 보냈습니다.",
  "note": ""
 },
 {
  "id": "ST-8",
  "where": "market_tools.py:83 (Static arbitrage 'Status'), :147 (ETF 'Study decision'), macro_records.py:251 (engine ARMED), strategy decision line, fx SABR 'CONVERGED'",
  "current": "COMPUTED / NOT_LOADED / ARMED / WITHHELD / CONVERGED / REJECT",
  "proposed": "계산 완료 / 조회 전 / 엔진 활성 / 판정 보류 / 수렴 / 기각 (verdict tokens shown as '기각 (REJECT)' where research identity matters)",
  "note": "Do not change verdicts or exports; labels only"
 },
 {
  "id": "ST-9",
  "where": "paper.py:281, 288, 293, 296; translations.py:228, 477-478",
  "current": "'저장 확인 완료 · {raw status}', 'CONFIRMED · 활성화는 별도입니다.', 'PAUSED', '{status} · 엔진 Arm은 별도입니다.', 'HALT 확인'",
  "proposed": "'저장 확인 완료 · {상태}', '확인 완료 · 활성화는 별도입니다.', '일시 정지', '{상태} · 엔진 활성화는 별도입니다.', '긴급 정지 확인'",
  "note": "[read]; not run (needs an opened paper session)"
 },
 {
  "id": "RK-1",
  "where": "translations.py:405 (Rates curve form 'Lookback · sessions')",
  "current": "관측 창 · 거래일",
  "proposed": "관찰 기간 (거래일 수)",
  "note": "UI-6b [run]"
 },
 {
  "id": "RK-2",
  "where": "translations.py:403 (Signals form)",
  "current": "빠른 이동평균 / 관측 창 / RSI 기간",
  "proposed": "단기 이동평균 / 관찰 기간 / RSI 기간",
  "note": ""
 },
 {
  "id": "RK-3",
  "where": "translations.py:363 'Sessions' (ETF, Strategy forms)",
  "current": "거래일",
  "proposed": "조회 기간 (거래일 수)",
  "note": "As a field label, 거래일 reads like a date, not a count"
 },
 {
  "id": "RK-4",
  "where": "translations.py:357 (Derivatives/KOSPI200)",
  "current": "기간 거래일 · 공란 = 만기",
  "proposed": "보유 기간 (거래일 수) · 비우면 만기까지",
  "note": ""
 },
 {
  "id": "RK-5",
  "where": "translations.py:62, 333; display_prose_catalog.py:82",
  "current": "분석 기간 · 거래일 / 리밸런싱 · 거래일 / 경로 수 / 거래일",
  "proposed": "분석 기간 (거래일 수) / 리밸런싱 주기 (거래일) / 경로 수 / 거래일 수",
  "note": ""
 },
 {
  "id": "RK-6",
  "where": "translations.py:355, 356, 320-321 ('blank = …')",
  "current": "만기 · 공란 = 최근 만기 / 금리 % · 공란 = 공급자",
  "proposed": "만기 · 비우면 최근월물 / 금리 % · 비우면 제공처 값",
  "note": "'공란 = …' is code-style shorthand"
 },
 {
  "id": "RK-7",
  "where": "rates.py:60 (provenance line)",
  "current": "SYNTHETIC · 2026-11-04 · 80 observations · bootstrap",
  "proposed": "합성 · 2026-11-04 · 관측 80개 · 부트스트래핑",
  "note": "Bonds already says '30 거래일' (bonds_portfolio_narrative.py:131)"
 },
 {
  "id": "RK-8",
  "where": "translations.py:371 'Quote' (KRX tool combo; ETF/KRX table title market_tools.py:133, 272)",
  "current": "호가",
  "proposed": "현재가 시세 (combo) / 시세 (table title)",
  "note": "The table holds price and OHLC, not an order book"
 },
 {
  "id": "RK-9",
  "where": "market_tools.py:276-277 (KRX daily table headers from provider keys)",
  "current": "date / open / high / low / close / volume",
  "proposed": "일자 / 시가 / 고가 / 저가 / 종가 / 거래량",
  "note": "[run]. Header-only display map"
 },
 {
  "id": "FM-1",
  "where": "core/ui_legacy_messages.py:253 fallback for 'Field'/'Fields'; market_tools.py:133, 272; macro_records.py:251",
  "current": "필드",
  "proposed": "항목 (or the owner's word 측정값, used consistently)",
  "note": "UI-10 [run]. Add a Native entry so the legacy fallback is not reached"
 },
 {
  "id": "FM-2",
  "where": "translations.py:427 'Metrics' (table titles) and 566 'Metric' (column)",
  "current": "측정값 (title) over 측정 항목 (column)",
  "proposed": "주요 지표 (title) / 항목 (column) / 값",
  "note": "Update tests/desktop_language_acceptance.py:77"
 },
 {
  "id": "FM-3",
  "where": "market_tools.py:272 (KRX Quote rows = asdict keys)",
  "current": "ticker, name, price, change, change_pct, volume, market_cap, high, low, open, currency, per, eps, sector, listed_shares",
  "proposed": "종목코드, 종목명, 현재가, 전일 대비, 등락률, 거래량, 시가총액, 고가, 저가, 시가, 통화, PER, EPS, 업종, 상장주식수",
  "note": "[run] via harness2. Localize the caption column only; values and exports unchanged"
 },
 {
  "id": "FM-4",
  "where": "market_tools.py:133 (ETF Quote rows)",
  "current": "price, nav, premium_pct, tracking_error_pct, cu_units, lp_holding_pct",
  "proposed": "현재가, 순자산가치(NAV), 괴리율 %, 추적오차 %, 설정단위(CU) 주식 수, LP 보유 비중 %",
  "note": "Korean ETF market terms"
 },
 {
  "id": "FM-5",
  "where": "market_tools.py:224-226 (ETH/BTC table)",
  "current": "n / last_ratio / adf_p / z_2y / 검증 판정",
  "proposed": "관측 수 / 최근 비율 / ADF p값 / 2년 z점수 / 검증 판정",
  "note": "Only 'verdict' is currently translated (legacy)"
 },
 {
  "id": "FM-6",
  "where": "macro_records.py:132 (QTreeWidget header), :251 (table)",
  "current": "Field / Recorded value (tree, English) and 필드 / Recorded value (table)",
  "proposed": "항목 / 기록값",
  "note": "LanguageController does not visit QTreeWidget headers"
 },
 {
  "id": "BD-1",
  "where": "bonds.py:82-87 (metric captions); bonds.py:51 table() has no localized_columns",
  "current": "Price, Yield, Macaulay duration, Modified duration, Convexity, DV01, z-spread, Curve price, Carry · 0.25 years, Roll-down, Carry + roll, Breakeven",
  "proposed": "가격 (액면 100당), 만기수익률, 맥컬리 듀레이션, 수정 듀레이션, 볼록성(컨벡시티), DV01, Z-스프레드, 곡선 기준 가격, 캐리 · 0.25년, 롤다운, 캐리+롤다운, 손익분기 금리 변화",
  "note": "UI-11a [run]. The narrative says 매콜리; unify to 맥컬리 (bonds_portfolio_narrative.py:56)"
 },
 {
  "id": "BD-2",
  "where": "bonds.py:83-84, 87 (value units)",
  "current": "'8.163 years', '798.12 currency / bp', '+2.60 bp'",
  "proposed": "'8.163년', '798.12 (통화/bp)'",
  "note": "Unit words only; numbers unchanged"
 },
 {
  "id": "BD-3",
  "where": "bonds.py:53-54 (headers)",
  "current": "Key tenor · years / DV01 · currency / bp / Shock · bp / P&L / P&L %",
  "proposed": "주요 만기 · 년 / 만기별 DV01 · 통화/bp / 금리 충격 · bp / 손익 / 손익률 %",
  "note": "Scenario 'New price' is already 새 가격"
 },
 {
  "id": "BD-4",
  "where": "bonds.py:52, 88 (chart)",
  "current": "Yield (%) · Price per 100 / legend 'Duration tangent'",
  "proposed": "수익률 (%) · 액면 100당 가격 / 듀레이션 접선",
  "note": ""
 },
 {
  "id": "BD-5",
  "where": "structuring.py:61 heading 'Greeks', header 'Risk'",
  "current": "Greeks / 위험",
  "proposed": "민감도(그릭스) / 민감도",
  "note": "Glossary: 그릭스 · 델타·감마·베가·세타 (core/education/glossary.py)"
 },
 {
  "id": "BD-6",
  "where": "structuring.py:66, 63, 68",
  "current": "Leg decomposition / Maturity payoff / Hedge sheet",
  "proposed": "구성요소별 분해 / 만기 손익 / 헤지 내역",
  "note": "The 'Leg' header is already 구성요소"
 },
 {
  "id": "BD-7",
  "where": "structuring.py:48 ('Leverage'), leg name 'ATM call', chart labels :63-64",
  "current": "Leverage / ATM call / Payoff / Underlying at maturity / Per 100 notional / Realized 10y–2y spread · bp",
  "proposed": "레버리지 / ATM 콜 / 손익 / 만기 시 기초자산 가격 / 액면 100당 / 실현 10y–2y 스프레드 · bp",
  "note": ""
 },
 {
  "id": "BD-8",
  "where": "translations.py:533 (structuring.py:70)",
  "current": "Hedge 부호: + 매수 / 고정금리 지급, − 매도 / 고정금리 수취. 실제 주문을 실행하지 않습니다.",
  "proposed": "헤지 부호: + 매수 / 고정금리 지급, − 매도 / 고정금리 수취. 실제 주문은 내지 않습니다.",
  "note": ""
 },
 {
  "id": "BD-9",
  "where": "rates.py:93, 100-102 (swaption metrics)",
  "current": "Premium / notional, Annuity, Delta · per +1bp, Gamma · per bp², Vega · per 1bp normal vol, Theta · 1 day, Other-model vol",
  "proposed": "명목금액 대비 프리미엄, 애뉴이티(연금계수), 델타 · +1bp당, 감마 · bp²당, 베가 · 정규 변동성 1bp당, 세타 · 1일, 다른 모형 기준 변동성",
  "note": "[run]"
 },
 {
  "id": "BD-10",
  "where": "rates.py:86-90 (swap)",
  "current": "Swap, Par rate, Fixed, PV, DV01 · +1bp P&L, Annuity, Carry · first period, Roll-down · 1y; 'Key-rate DV01', 'Forward swaps', header 'Currency / bp'",
  "proposed": "스왑, 파 스왑금리, 고정금리, 현재가치, DV01 · +1bp 손익, 애뉴이티, 캐리 · 첫 기간, 롤다운 · 1년; 만기별 DV01(KRD), 선도 스왑금리, 통화/bp",
  "note": ""
 },
 {
  "id": "BD-11",
  "where": "rates.py:65, 73, 81-83",
  "current": "Shape, Regime, Lookback, NS/NSS fit RMSE, 2s5s10s_fly, 1y_fwd_1y_ahead; Curve table (Zero, DF, Par, 1y forward, Change · 20d); PCA loadings / PCA variance (Component → 구성 지표, Explained, Latest score, level/slope/curvature)",
  "proposed": "곡선 형태, 변화 유형, 관찰 기간, NS/NSS 적합 오차(RMSE), 2s5s10s 버터플라이, 1년 후 1y 금리 변화; 수익률 곡선 표 (제로금리, 할인계수, 파 수익률, 1년 선도금리, 변화 · 20거래일); 주성분 적재값 / 주성분 설명력 (주성분, 설명 비율, 최근 점수, 수준/기울기/곡률)",
  "note": "Narrative already uses 수준/기울기/곡률 (rates_narrative.py:15)"
 },
 {
  "id": "BD-12",
  "where": "rates.py:111-116 (simulation)",
  "current": "Kappa · /year, Half-life · years, Theta, Sigma, Initial rate, Terminal mean, P(terminal > threshold), Horizon curve · median path, Model zero, axes Years / Short rate · %",
  "proposed": "평균회귀 속도 κ · /년, 반감기 · 년, 장기 평균 θ, 변동성 σ, 초기 금리, 만기 평균, 만기 금리가 임계값을 넘을 확률, 기간 말 곡선 · 중앙 경로, 모형 제로금리, 년 / 단기금리 · %",
  "note": "'Theta' here is the long-run mean, not option theta"
 },
 {
  "id": "BD-13",
  "where": "market_tools.py:51, 71, 75, 76, 82-83 (Derivatives)",
  "current": "Futures & volatility / Implied volatility smile / Risk-neutral density / Hedge simulation / Static arbitrage checks / call_vertical … put_butterfly / axes Index points, Density / legend Q density",
  "proposed": "선물·변동성 / 내재변동성 스마일 / 위험중립 밀도 / 헤지 시뮬레이션 / 정적 차익거래 검사 / 콜 수직 스프레드 … 풋 버터플라이 / 지수 포인트, 밀도 / Q 밀도",
  "note": ""
 },
 {
  "id": "BD-14",
  "where": "display_prose_catalog.py:108 via market_tools.py:45",
  "current": "Session synthetic · 135 strikes · rate 3.200% (assumed)  [stays English]",
  "proposed": "세션 {session} · 행사가격 {n}개 · 금리 {rate} ({source})",
  "note": "Blocked by TP-1"
 },
 {
  "id": "CL-1",
  "where": "translations.py:456 'Forward' used by rates.py:100 (swaption metric) and :106 (Caplets header)",
  "current": "선물환",
  "proposed": "선도금리 in Rates (keep 선물환 in FX)",
  "note": "Needs a context-specific key, e.g. 'Forward rate'"
 },
 {
  "id": "CL-2",
  "where": "translations.py:503 'Equity' used by strategy.py:64 (y-axis)",
  "current": "OOS observations · 주식",
  "proposed": "표본 외 관측 · 누적 가치",
  "note": "[run] wrong sense; Structuring 'Equity' = 주식 is correct"
 },
 {
  "id": "CL-3",
  "where": "core/ui_legacy_messages.py:240 'Component' used by rates.py:82",
  "current": "구성 지표",
  "proposed": "주성분 (PCA table); keep 구성 지표 for Signals",
  "note": "Use separate keys"
 },
 {
  "id": "CL-4",
  "where": "macro_narrative_language.py:14 'Last' overrides translations.py:431; used by fx.py:38 (date column)",
  "current": "최근값 (FX Data sources date column)",
  "proposed": "최종 관측일 in FX; 최근값 in Macro",
  "note": "[run]"
 },
 {
  "id": "CL-5",
  "where": "core/ui_messages.py:152 'light' (also :12 'theme_light' 라이트); translations.py:53 'Dark'",
  "current": "밝게 / 다크",
  "proposed": "라이트 / 다크 (or 밝은 테마 / 어두운 테마)",
  "note": "[run] rail theme combo (app.py:268)"
 },
 {
  "id": "CL-6",
  "where": "core/ui_legacy_messages.py:232 (tab, app.py:526) vs translations.py:84, 120",
  "current": "tab 몬테카를로; text 'Monte Carlo'",
  "proposed": "몬테카를로 everywhere (glossary: 몬테카를로 시뮬레이션)",
  "note": ""
 },
 {
  "id": "CL-7",
  "where": "translations.py:434 vs display_prose_catalog.py:72, 77, 108; core/research/option_disclosure.py; rates_narrative.py",
  "current": "행사가격 / 행사가",
  "proposed": "행사가격",
  "note": "KRX standard term"
 },
 {
  "id": "CL-8",
  "where": "translations.py:57 'Model' vs 14 lines using 모형 (display_prose 71-72, rates_narrative 113, market_narrative 22/139, macro 123, glossary)",
  "current": "모델 / 모형",
  "proposed": "모형 for quantitative models (GARCH 모형, 정규 모형); keep 모델 카드 as a proper name",
  "note": ""
 },
 {
  "id": "CL-9",
  "where": "translations.py:100 and display prose/market_tools (공급자) vs watchlist.py (21 lines)/stock_profile/data_rights (공급처)",
  "current": "공급자 / 공급처",
  "proposed": "제공처 (one term app-wide)",
  "note": "Also matches the Flet legacy 공급처"
 },
 {
  "id": "CL-10",
  "where": "strategy/ETF/FX/portfolio/signals 'Sharpe'; translations.py:462; bonds_portfolio_narrative.py:22, 89; fx_narrative.py:56; market_narrative_language.py:67",
  "current": "Sharpe / 최대 Sharpe / 샤프비율 / 샤프 비율",
  "proposed": "샤프 지수 / 최대 샤프 지수 (glossary core/education/glossary.py 'sharpe')",
  "note": ""
 },
 {
  "id": "CL-11",
  "where": "translations.py:335-336 vs display_prose_catalog.py:141-142, 144",
  "current": "원금보장형 노트 / 원금보장형 상품; 역전환형 노트 / 역전환형 상품; CMS 스티프너 상품",
  "proposed": "원금보장형 구조화 상품 / 역전환형(리버스 컨버터블) 상품 / CMS 스티프너 상품 — same word in the combo and the result",
  "note": ""
 },
 {
  "id": "CL-12",
  "where": "translations.py:339, 352, 280 vs display_prose_catalog.py:44, 46, 47, 93",
  "current": "발행 가격 · 액면 100당 / 발행가격 / 공정가치 · 100당 / 값 · 100당",
  "proposed": "발행가격 · 액면 100당 / 공정가치 · 액면 100당 / 가치 · 액면 100당",
  "note": "display_prose 93 is shadowed (dead)"
 },
 {
  "id": "CL-13",
  "where": "translations.py:275 (Bonds), 346 (Structuring), 505 (Rates)",
  "current": "표면금리 % / 쿠폰 % / 채권 쿠폰 %",
  "proposed": "Bonds: 표면금리 %; Rates: 채권 표면금리 %; Structuring: 쿠폰 %",
  "note": "Fix the rule and use it consistently"
 },
 {
  "id": "CL-14",
  "where": "rates_narrative.py:12-14 vs macro_narrative_language.py:18-19",
  "current": "bull steepener = 금리 하락·기울기 확대 (Rates) / 금리 하락·곡선 가팔라짐 (Macro)",
  "proposed": "One table: 강세 스티프닝(금리 하락·기울기 확대) etc., shared by both modules",
  "note": ""
 },
 {
  "id": "CL-15",
  "where": "translations.py:324 vs 355, 302",
  "current": "옵션 만기 / 만기",
  "proposed": "옵션 만기 for options; 만기 for futures/bonds",
  "note": "Minor"
 },
 {
  "id": "CL-16",
  "where": "macro.py header 'Curve' (macro_narrative_language.py:11) vs rates; macro table 미국채 vs narrative UST",
  "current": "수익률곡선 / 수익률 곡선; 미국채 2y / UST 2y",
  "proposed": "수익률 곡선; 미국채 (2y) everywhere",
  "note": ""
 },
 {
  "id": "CL-17",
  "where": "translations.py:198 (dead) vs 313",
  "current": "'Instrument' defined twice: 종목 / 상품 (상품 wins)",
  "proposed": "Delete line 198 or split into 'Instrument (stock)' and 'Instrument (product)'",
  "note": "Catalog hygiene"
 },
 {
  "id": "MX-1",
  "where": "translations.py:163, 241, 242, 243, 244, 189, 223",
  "current": "Bonds · … / Rates · … / Macro · … / Signals · … / Structuring · … / Rules · 모의 실행 전용 / Paper Trading · 실제 주문 없음",
  "proposed": "채권 · … / 금리 · … / 매크로 · … / 신호 · … / 구조화 상품 · … / 규칙 · 모의 실행 전용 / 모의매매 · 실제 주문 없음",
  "note": "Pane titles keep their English prefixes"
 },
 {
  "id": "MX-2",
  "where": "translations.py:60, 129",
  "current": "Symbols · pairs는 y, x 순서 / 입력을 확인하세요. Symbol과 유한한 양수 Target이 필요합니다.",
  "proposed": "종목 코드 · 페어는 y, x 순서 / 입력을 확인하세요. 종목 코드와 0보다 큰 목표 가격이 필요합니다.",
  "note": ""
 },
 {
  "id": "MX-3",
  "where": "translations.py:135, 164, 167",
  "current": "Price/Yield와 … / Price를 입력할 때는 Yield를 비웁니다 / Price/Yield 중 하나만",
  "proposed": "가격/수익률과 … / 가격을 입력할 때는 수익률을 비우세요 / 가격과 수익률 중 하나만",
  "note": ""
 },
 {
  "id": "MX-4",
  "where": "translations.py:153, 159, 161",
  "current": "…Frontier·무작위 구름… / equal_weight는 1/N 고정 비중 / 계산 완료 · solver converged=True · 공식 투자 판정 없음",
  "proposed": "…효율적 투자선·무작위 구름… / 동일 비중은 1/N으로 고정 / 계산 완료 · 최적화 수렴: 예 · 공식 투자 판정 없음",
  "note": "Narrative already says 효율적 투자선"
 },
 {
  "id": "MX-5",
  "where": "translations.py:190, 478, 235, 205-206",
  "current": "엔진 Arm / Live 실행 / ISO 날짜+UTC offset",
  "proposed": "엔진 활성화 / 실데이터 실행 / ISO 날짜 + UTC 오프셋",
  "note": "The Arm button is already 엔진 활성화 (509)"
 },
 {
  "id": "MX-6",
  "where": "translations.py:526",
  "current": "Last prints only · 장외/마감 시 호가는 동시 체결 가능한 가격이 아닙니다.",
  "proposed": "최종 체결가 기준 · 장외·마감 시세는 동시에 체결할 수 있는 가격이 아닙니다.",
  "note": ""
 },
 {
  "id": "MX-7",
  "where": "translations.py:545, 554, 555, 556",
  "current": "공식 gate 판정 / 권장 book / Research register · 표시 전용 … book 입력 / FORWARD-SIM·refusal은 권장이 아닙니다",
  "proposed": "공식 게이트 판정 / 권장 북 / 연구 등록부 · 표시 전용 … 북 입력 / 전진 시뮬레이션·거부 북은 권장이 아닙니다",
  "note": ""
 },
 {
  "id": "MX-8",
  "where": "translations.py:84, 93, 104, 120",
  "current": "이번 세션의 Monte Carlo … / Quant Lab에서 연구 시작 → / Quant Lab · 기존 계산 엔진으로 가격 분포 분석",
  "proposed": "이번 세션의 몬테카를로 … / 몬테카를로에서 연구 시작 → / 몬테카를로 · 가격 분포 분석",
  "note": "Build & Test subtitle (also relevant to UI-9)"
 },
 {
  "id": "TP-1",
  "where": "translations.py:596-602 (re.S, .+?) with translate() at 628-636",
  "current": "First-line templates swallow later lines: Derivatives line 2 stays English; Strategy shows '…누적 원장 설정 None⏎Walk-forward: … {'step': 42}개'",
  "proposed": "Compile placeholders as [^\\n]+? (no re.S) or split lines before matching templates",
  "note": "[run] Real bug; affects display_prose_catalog.py:107-109, 119-120"
 },
 {
  "id": "NR-1",
  "where": "app.py:903-907 (MC metric rows; only 'Spot' translates)",
  "current": "P5 / P50 / P95, Sample vol (ann.), Next-session vol (ann.), P(loss), VaR 95 / CVaR, Paths / horizon / seed, P(terminal ≥ target), Horizon-average vol (ann.)",
  "proposed": "P5 / P50 / P95, 표본 변동성(연율), 다음 거래일 변동성(연율), 손실 확률, VaR 95 / CVaR, 경로 수 / 기간 / 시드, 만기 가격 ≥ 목표가 확률, 기간 평균 변동성(연율)",
  "note": "13-8"
 },
 {
  "id": "NR-2",
  "where": "app.py:909-929 (MC notes)",
  "current": "English drift_note, vol disclosure, jump note, GARCH fit lines (converged=…, at_bound:, note:, se_note:, eta 95% profile interval)",
  "proposed": "Korean variants via localized_text (as the bootstrap disclosure already does, core/research/mc_disclosure BOOTSTRAP_TEXT_KO); raw diagnostics behind a '상세' toggle",
  "note": "13-8. Also an A3/UI-12 clutter candidate"
 },
 {
  "id": "NR-3",
  "where": "bonds_portfolio_narrative.py:131-133; rates.py:60; structuring.py:40",
  "current": "'Simulated Treasury par curve (Nelson-Siegel random walk) — no market data provider was used.' (shown twice on Bonds)",
  "proposed": "'모의 미국채 파 곡선(넬슨-시겔 랜덤워크) · 시장 데이터 제공처를 쓰지 않았습니다.' shown once",
  "note": "Provider note (13-8 / UI-12)"
 },
 {
  "id": "NR-4",
  "where": "rates.py:91, 94-95, 103, 118",
  "current": "'1,000,000 notional · 1 payments/year · single curve · ACT/365F⏎10y payer K=…'; 'bachelier · +80.00 bp normal · 1,000,000 notional⏎payer bachelier; single-curve…'; '1y × 5y · Payer'",
  "proposed": "'명목금액 1,000,000 · 연 1회 지급 · 단일 곡선 · ACT/365F'; 'Bachelier · 정규 변동성 80bp · 명목금액 1,000,000'; '1y × 5y · 고정금리 지급형'",
  "note": "13-8"
 },
 {
  "id": "NR-5",
  "where": "strategy.py:35, 50-62, 64",
  "current": "Study scorecard (Card/Decision), Validation statistics rows (OOS Sharpe, 90% interval, Deflated Sharpe, PBO, OOS / IS, 2× cost Sharpe, Positive years, Plateau, Plateau edge, Benchmark Sharpe/difference/p, Haircut Sharpe), Walk-forward equity, legend Benchmark, decision reason sentence",
  "proposed": "연구 성적표 (카드/판정), 검증 통계 (표본 외 샤프 지수, 90% 구간, 디플레이티드 샤프 지수, 과적합 확률(PBO), 표본 외/표본 내, 비용 2배 샤프 지수, 플러스 연도 비율, 안정 구간, 안정 구간 경계, 벤치마크 샤프 지수/차이/p값, 할인 샤프 지수), 순차 전진 누적 가치, 벤치마크",
  "note": "25 English-only strings [run]"
 },
 {
  "id": "NR-6",
  "where": "macro_records.py:109, 182, 200-217, 222, 261-279; ui/macro_cards_view.py:32-34",
  "current": "Macro dry run / Gate package: / Card, Verdict, Disposition, Label, Book / Volatility labels · display only / Flags / Overlay records · values as recorded / Display-only books · not a recommendation / Inputs and fail-closed inputs / Provenance / Owner decisions / inputs / proposals / Design priors · not gate PASS / Go / No-go register / Do not build / Open questions … (45 strings)",
  "proposed": "매크로 모의 검사 / 게이트 패키지: / 카드, 판정, 처리, 라벨, 북 / 변동성 라벨 · 표시 전용 / 플래그 / 오버레이 기록 · 기록값 그대로 / 표시 전용 북 · 권장 아님 / 입력과 실패 시 차단 입력 / 출처 / 소유자 결정·입력·제안 / 설계 사전 가중치 · 게이트 통과 아님 / 진행 여부 등록부 / 만들지 않을 항목 / 미결 질문 …",
  "note": "Macro v2 is the largest untranslated pane"
 },
 {
  "id": "NR-7",
  "where": "market_tools.py:204-227 (Crypto)",
  "current": "Premium / volatility, AR(1) amplitude half-life · observations, Kimchi premium, Perpetual funding, 7-day mean annualized %, Days, Annualized · %, USDT per BTC, weekdays Mon…Sun",
  "proposed": "프리미엄·변동성, AR(1) 진폭 반감기 · 관측 수, 김치 프리미엄, 무기한 선물 펀딩비, 7일 평균 연율 %, 일, 연율 · %, BTC당 USDT, 월·화·수·목·금·토·일",
  "note": ""
 },
 {
  "id": "NR-8",
  "where": "market_tools.py:130, 145-150 (ETF)",
  "current": "ETF price / NAV; Descriptive sleeve backtests with rows trend / vol_target / buy_hold; header Sharpe; Trend switch vs buy & hold; legend Trend",
  "proposed": "ETF 가격 / 순자산가치; 전략별 백테스트(설명용) — 추세 전환 / 변동성 목표 / 매수 후 보유; 샤프 지수; 추세 전환 대 매수 후 보유; 추세 전환",
  "note": ""
 },
 {
  "id": "NR-9",
  "where": "portfolio.py:69-70; bonds_portfolio_narrative.py:87, 106",
  "current": "'100.00% · selected' / '· comparison', True/False; 'max-sharpe 포트폴리오…', 'THREE은', '선택 목적 max_sharpe'",
  "proposed": "'· 선택' / '· 비교', 예/아니오; '최대 샤프 지수 포트폴리오…', 'THREE는', '선택 목적: 최대 샤프 지수'",
  "note": "[read] for portfolio.py:69-70; narrative [run]"
 },
 {
  "id": "NR-10",
  "where": "rates_narrative.py:27, 29, 49, 56; core/ficc/forward_conventions.py:9; display_prose_catalog.py:133-135",
  "current": "오 년 단리 / 향후 일 년간 / '10y payer은' / 일 년 롤다운 / 'RSI 62은'",
  "proposed": "5년 단리 / 향후 1년간 / '10y 고정금리 지급 스왑은' / 1년 롤다운 / 'RSI {rsi}: 과매수 구간입니다' (no particle after a number)",
  "note": ""
 },
 {
  "id": "CB-1",
  "where": "rates.py:12, 15, 19, 21",
  "current": "bootstrap / nelson_siegel / svensson; swaption / cap / floor; vasicek / cir / hull_white; none / bond / swap",
  "proposed": "부트스트래핑 / 넬슨-시겔 / 스벤슨; 스왑션 / 캡 / 플로어; 바시첵 / CIR / 헐-화이트; 없음 / 채권 / 스왑",
  "note": "Display text only; keep the combo data ids"
 },
 {
  "id": "CB-2",
  "where": "strategy.py:12; portfolio.py:26",
  "current": "synthetic / auto / kis / fmp / yfinance / crypto",
  "proposed": "합성 데이터 시연 / 자동 / KIS / FMP / Yahoo / 가상자산 거래소",
  "note": "Other panes already use 'Auto · …' and 'Synthetic demo'"
 },
 {
  "id": "TN-1",
  "where": "market_chart.py (20 lines, e.g. 379)",
  "current": "…변화에 늦게 반응할 수 있어요. (해요체)",
  "proposed": "…변화에 늦게 반응할 수 있습니다. (합니다체, as in the rest of the app)",
  "note": "Style choice for the owner"
 },
 {
  "id": "GL-1",
  "where": "core/education/glossary.py (32 terms) vs UI labels",
  "current": "Glossary: 샤프 지수, 최대낙폭 · MDD, 몬테카를로 시뮬레이션, GARCH 모형, 부트스트래핑, 볼록성 · 컨벡시티, 그릭스, 내재변동성, 원금보장형 구조화 상품, 선물환. UI: Sharpe / 최대 낙폭 / Monte Carlo / 모델 / 블록 부트스트랩 / Convexity / Greeks / 내재 변동성 / 원금보장형 노트",
  "proposed": "Make the glossary the single term source for labels (A1 UI-10) and for the 알아보기 side panel (A3 UI-12); add the missing Korean-used English (DV01, ATM, SABR, CVaR, PBO)",
  "note": "One glossary for both A1 and A3"
 },
 {
  "id": "RL-1",
  "where": "macro.py:59; fx.py:38, 46",
  "current": "Macro table shows Source and Observed date columns; FX shows Data sources (Provider/First/Last) and a carry 'Rate date' column",
  "proposed": "Hide them on screen (keep them in exports), as already done for ETF/KRX quotes (market_tools.py:131-134, 270-274)",
  "note": "Only if the PR #71 ruling covers analysis tools: unverified"
 }
]
```

## Flet 브라우저 용어 조사

FLET BROWSER SWEEP (ui/, main.py, core/ui_legacy_messages.py, core/i18n.py, core/ui_messages.py), worktree s10 at 516953a (content identical to faf9f3b: `git diff faf9f3b HEAD` is empty). Read-only. Scratch outputs are in /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/ (flet_english_in_korean.tsv, compare.json, render_ko.json, literals.json, plus the scripts that produced them). `git status --porcelain` in s10 is clean after the run.

0. HOW FLET KOREAN WORKS, AND WHY IT MATTERS FOR BOTH APPS
- Flet translates only by exact match. core/i18n.py:46-60 `LocaleContext.text` tries static_text (core/ui_legacy_messages.py EN_TO_KO/KO_TO_EN), then LEGACY keys (core/ui_messages.py:188-193), then ISO dates, then dynamic templates (core/ui_dynamic_messages.py). Any other text stays as written. ui/localization.py:6-34 applies this to Text.value, button content, Option.text, tooltip, hint_text, helper_text and label.
- Most Flet page source is English, so Korean mode mixes Korean and English on every page. I extracted 2,209 display-candidate literals from ui/*.py and main.py: 1,556 are English with no catalog entry, 129 are English that the Native catalog already translates, 229 are translated by Flet, and 295 are codes. I also built 15 page views offline with a stub page in ko_KR, with the network and file writes blocked and no workers started. On the initial screens, English strings outnumber Korean on every analysis page: bonds 11 English / 14 Korean, rates 36/14, fx 25/7, structuring 31/10, derivatives 14/2, etf 18/3, crypto 7/3, macro 15/4, strategy lab 185/13, quant 15/7, portfolio 12/5, signals 13/6, macro overlay 10/0.
- Result tables mix languages within a single header row (rendered with ko.text):
  - bonds stats ui/bonds_page.py:132-138: 가격 | Yield | Macaulay | Modified | Convexity | DV01 | z-spread
  - bonds scenarios :181: Scenario | Shock | New price | P&L | P&L % (all English)
  - structuring legs ui/structuring_page.py:183: Leg | Kind | 값 | Detail
  - structuring hedge :191: 상품 | Quantity | 단위 | Rationale
  - KRX daily ui/krx_page.py:126-127: 날짜 | Open | High | Low | 종가 | 거래량
  - KRX snapshot :156-158: Code | 이름 | Market | 종가 | Chg % | 거래량 | Mkt cap
  - macro sheet ui/macro_page.py:43: Group | 지표 | Last | 1d | 1w | 1m | 3m | z (1y) | pct (1y) | 출처
  - rates curve ui/rates_page.py:137: Tenor | Zero | Par | 1y fwd | Chg
  - fx smile ui/fx_page.py:286: Point | 행사가 | Vol | Spot delta
  - fx carry :354-355: all English.
- Charts never translate. ui/fcharts.py (15 set_title calls), ui/qcharts.py and ui/xcharts.py (44 title/label/legend calls) render matplotlib PNGs, so their titles, axes and legends are baked in English. translate_controls cannot reach them. Several titles also embed the provider and date (fcharts.py:90, :108, :258, :396).
- CROSS-APP COUPLING: Native `display()` (quantgen_desktop/translations.py:640-644) falls back to `ctx.text`, which is the Flet catalog, whenever Native has no entry. Editing core/ui_legacy_messages.py or core/ui_messages.py therefore also changes Native screens.
  - UI-10 root cause: core/ui_legacy_messages.py:253 `'Fields':'필드','Field':'필드'` is what Native shows in its ETF and KRX "Quote" tables (quantgen_desktop/market_tools.py:133 and :272, both `['Field','Value']`) and in macro_records.py:251. Native has no 'Field' entry of its own (verified: translate('Field','ko') returns 'Field' and ctx.text returns '필드').

1. NATIVE vs FLET KOREAN FOR THE SAME ENGLISH TERM (46 catalog differences, all checked by code: Native translate() vs Flet LocaleContext('ko_KR').text())
Format: English: Native / Flet (Flet source line).
- Navigation and names:
  - Research Home: 연구 홈 / 리서치 홈 (core/ui_messages.py:14)
  - Indicator guide: 기술지표 가이드 / 지표 가이드 (:21)
  - Build & Test (also 'Build && Test'): 설계 및 검증 (translations.py:46) / 설계·검증 (:16)
  - Portfolio & Risk (also '&&'): 포트폴리오 및 위험 (translations.py:47) / 포트폴리오·위험 (:17)
  - Research Library: 연구 보관함 (translations.py:48) / 연구 라이브러리 (ui_legacy_messages.py:205 via EN_TO_KO; this shadows MESSAGES 'library' 연구 기록 at ui_messages.py:18)
  - Connections: 연결 / 데이터 연결 (:132)
  - Signals: 신호 (translations.py:485) / 기술적 관측 (:129)
  - Macro: 매크로 (translations.py:497) / 거시경제 (:139)
  - Macro sheet: 거시 지표표 (macro_narrative_language.py:6, which overrides translations.py:489 매크로 현황, so Native itself has two names) / 거시경제 관측 (ui_legacy_messages.py:232)
  - Macro v2: 매크로 v2 / 거시경제 v2 (:232)
  - Light · A: 라이트 · A / 밝게; Dark: 다크 / 어둡게 (ui_messages.py:152-153; Flet's own theme_light at :12 says 라이트)
  - Native desktop preview text: …Flet 브라우저 유지 / …Flet 브라우저도 지원 (ui_legacy_messages.py:223)
- Inputs:
  - Model: 모델 (translations.py:57) / 모형 (ui_legacy_messages.py:227, ui_messages.py:161)
  - Symbol: 종목 코드 / 종목·통화쌍 (:227, ui_messages.py:146)
  - Symbols · comma separated: 종목 코드 · 쉼표로 구분 / 종목 · 쉼표로 구분 (:235)
  - Drift: 추세 가정 / 드리프트 (:227)
  - Horizon · sessions: 분석 기간 · 거래일 / 분석 기간 · 관측 수 (:228)
  - Paths: 시뮬레이션 경로 수 / 경로 수
  - Seed: 난수 시드 / 시드
  - Synthetic demo: 합성 데이터 시연 / 합성 시연 (:229)
  - Risk premium · rf + ERP: 위험 프리미엄 / 위험프리미엄 (:230)
  - Zero · stress: 0 · 스트레스 가정 / 0 · 스트레스
  - Sample mean · noisy: 표본 평균 · 추정 오차 유의 / 표본 평균 · 잡음 주의 (:231)
  - Provider: 공급자 (translations.py:100) / 공급처 (:233, ui_messages.py:113). Flet's own Korean sources use 공급자 (ui_legacy_messages.py:15, 34, 79, 80, 180, 187).
- Results:
  - Metric: 측정 항목 / 지표 (:233)
  - strong bullish / bullish / bearish / strong bearish: 강한 상승 우위 / 상승 우위 / 하락 우위 / 강한 하락 우위 vs Flet 강한 상승 관측 / 상승 관측 / 하락 관측 / 강한 하락 관측 (:245)
  - At bound: 경계 도달 / 경계값 도달 (:237)
  - Price vs 50-day / 200-day SMA: 가격과 50일 이동평균 / 가격과 SMA50의 위치 (:254)
  - Volatility regime: 변동성 상태 / 변동성 국면 (:255)
  - Reason: 사유 / 이유 (:241)
  - Observations: 관측 (translations.py:443) / 관측값 (:251)
  - Sessions: 거래일 (translations.py:363) / 관측 수 (:251)
  - Calendar days: 달력일 / 달력 일수 (:251)
- Bonds and options:
  - Annual: 연 1회 (translations.py:269, next to Native's own 반기 and 분기) / 연간 (:248)
  - Calculator & risk: 계산 및 위험 / 가격·위험 계산 (:249)
  - Position DV01 · optional: …선택 입력 / …선택 (:247)
  - CTD DV01 / contract: 계약당 최저가인도채권 DV01 / 계약당 CTD DV01 (:247)
  - Strike: 행사가격 (translations.py:434) / 행사가 (:250)
  - Expiry: 옵션 만기 (translations.py:324) / 만기 (:251)
- Feature names that differ between the apps:
  - Flet "Execution · simulated" 모의 실행 (main.py:216) vs Native "Paper Trading" 모의매매
  - Flet nav "Quant Lab" 분포 분석 (ui_messages.py:135), while Flet's Korean sentences still say "Quant Lab" (research_home.py:157, 158, 203, 259, 260) and "Strategy Lab" (:230)
  - main.py:246 hard-codes "실시간 시세 · 차트" vs Native "실시간 시세·차트 열기"
- Korean words that cover different English terms in Flet:
  - 지표 = Indicator, Metric, metrics
  - 관측값 = Observations, Observed value
  - 만기 = Expiry, Maturity
  - 필드 = Field, Fields
- Shadowing bugs inside the Flet catalog:
  - EN_TO_KO 'Close':'종가' (ui_legacy_messages.py:238) shadows MESSAGES 'close' 닫기 (ui_messages.py:119). Any 'Close' button would read 종가.
  - 'Signal' always becomes 신호선 (ui_messages.py:155).
  - LEGACY 'Macro sheet':'macro' (ui_messages.py:190) is dead code.
  - Lower-case LEGACY words (ui_messages.py:192-193) translate a card kind of 'model' to 모형 while 'strategy' and 'distribution' stay English in the same Strategy Lab list (ui/strategy_lab_page.py:59, :80).
- Flet shows English where Native already has Korean: 129 occurrences, about 95 unique (full list in the TSV, kind english_in_ko_native_has_korean). Examples:
  - rates_page.py:41-42, 389, 398, 410-413
  - structuring_page.py:31-32, 44, 144-152, 183, 191, 224-230
  - fx_page.py:39-40, 130, 140, 207-214, 275, 286-290, 332-355
  - krx_page.py:23-24, 156
  - macro_page.py:43-45
  - trading_page.py:38, 136, 140, 208
- Context collisions if Native's glossary is reused as is:
  - 'Forward' is 선물환 (translations.py:456). That is correct for FX but wrong for Rates (rates_page.py:228 swaption forward and :279 caplet forward), where it should be 선도금리.
  - 'Point' is 지점 (translations.py:433, fx_page.py:286 and :290), which reads awkwardly.
  - 'Quote' is 호가 (translations.py:371). On the KRX quote card it means a price snapshot, not bid/ask.

2. OWNER ITEMS AS THEY APPEAR IN FLET
- UI-1: Flet has one Macro page (nav 거시경제). Its View dropdown (ui/macro_page.py:44-45) offers 거시경제 관측 plus three v2 views still in English: Overlay state, Model cards, Research register. The home and library pages say 매크로 연구 and "Macro의 Research register…" / "Macro 열기" (research_home.py:257-258). Flet alone mixes 거시경제, 매크로 and Macro, and Native mixes 매크로, 거시 지표표 and 매크로 현황.
- UI-2: Flet already maps OBSERVED to 일별 관측 (research_home.py:172), the same as Native watchlist.py:53. Other raw status words are still visible in Flet:
  - execution_status COMPLETED, RUNNING, FAILED (research_home.py:151, 263)
  - input-status chips ok, warmup, disputed, not run, stale, missing… (ui/components.py:165-171, used at macro_state_panel.py:437 and :440)
- UI-6b:
  - Rates: "Lookback (sessions)" is English (rates_page.py:383), and so are Horizon (years) :407 and Threshold :409.
  - KRX page: entirely English (krx_page.py:23-28, 35-37, 56-66, 108-116, 126-168, 184-190).
  - Flet's own awkward term: 관측 수 for Sessions (the ETF field renders 관측 수; ui_legacy_messages.py:251).
  - Native's 관측 창 · 거래일 is at translations.py:405.
- UI-10: the Field/필드 root cause and the mixed tables are in section 0. The Flet 관측 family is awkward:
  - Composite 종합 관측값 :239
  - Signal components 지표별 관측값 :240
  - Stance 관측 방향 :241
  - bullish 상승 관측 :245
  - Signals 기술적 관측 (ui_messages.py:129)
  - The practice-guide text at research_home.py:228-232 tells the user to pick English labels (Data source, Symbol, Model, Drift, Paths, Horizon) that Korean mode never shows.
- UI-11a: in Flet the bond and structuring Greeks and legs are all English:
  - bonds_page.py:132-138, 157-167, 181, 194-200
  - structuring_page.py:61-63 (Delta, Gamma, Vega, DV01, 2s10s DV01 labels), :181 Legs, :183, :189 Hedge sheet, :191, :192
  - rates_page.py:231-235 swaption Greeks
  - fx_page.py:275, :286
  - Native: Greeks, Leg decomposition and Hedge sheet titles are also untranslated (quantgen_desktop/structuring.py:61, 66, 68). Native's English source strings differ from Flet's (Native 'Delta · per +1% spot', Flet 'Delta (per +1% spot)'), so the two catalogs cannot share keys today.
- UI-14 and UI-15: core/ui_messages.py:16-17 and translations.py:46-47; the Home shortcut at research_home.py:224 says '포트폴리오 · 위험' (ui_legacy_messages.py:205). Naming collision: Native's left nav already has 분석 도구 ("Analysis tools", quantgen_desktop/app.py:249, :425) right next to the item being renamed 분석. Flet also uses 분석 실행, 분석 화면 열기 and 분석 결과 선택.
- 13-8 in Flet: nothing is localized. All 18 local-narrative sites are English:
  - bonds_page.py:140, :207
  - crypto_page.py:103
  - derivatives_page.py:132
  - etf_page.py:158
  - fx_page.py:237, :308, :378
  - macro_page.py:133, :140, :142
  - portfolio_page.py:209
  - quant_lab_page.py:400
  - rates_page.py:156, :200, :257, :293, :363
  - signals_page.py:206-207
  - strategy_lab_page.py:168
- The analysis panel chrome (ui/ai_panel.py:52-53, 69, 78-98: Analysis, engine: local, question label and hint, Deep analysis, two disclaimers) and the model and provider notes are also English: bonds :123, :213; quant :324, :340, :343, :348, :354; signals :169, :183; portfolio :136-140, :146; crypto :50; derivatives :75; etf :172.
- Native Korean narrators exist and do not depend on Qt, so Flet could reuse them:
  - quantgen_desktop/bonds_portfolio_narrative.py: bond_korean, portfolio_korean
  - rates_narrative.py: curve, swap, swaption, cap_floor and simulation narrators
  - fx_narrative.py: carry_korean, sabr_korean
  - macro_narrative_language.py: macro_korean, summary_korean, sheet_note_korean
  - market_narrative_language.py: etf, crypto and derivatives narrators
  - model_narrative_language.py: signals_korean, structured_korean, strategy_variants
- PR #71 RULING NOT APPLIED IN FLET. Provider and observation date are still visible in live views. The ruling log (docs/nautilus_bridge/OWNER_RULINGS_LOG.md, 2026-11-04 section) records "Flet 브라우저 화면은 바꾸지 않았습니다". Places:
  - research_home.py:173 and :178 (tile "provider · observation date"), :216 subtitle
  - market_chart_page.py:538-544 (출처 … 마지막 봉 … 시세 시각 … 수신)
  - macro_page.py:43 and :121 (Source column), :161 (as-of chip)
  - krx_page.py:71 (Source: provider), :116 (Source · as of row)
  - rates_page.py:125
  - structuring_page.py:159-160
  - derivatives_page.py:78
  - fcharts.py:90, :108, :258

3. A3 IN FLET
- UI-9: Flet has no right-side explanation pane. Build & Test pages put explanations inline:
  - quant_lab_page.py:37 (source text "Auto (KIS for 6-digit, else FMP)"), :56 SMOKE chip, :340, :343, :354 (three size-11 captions), :348 (provider-note chip, i.e. the FMP and KIS notes), GARCH captions :110, :129, :138, :155
  - signals_page.py:27 (FMP option), :29 notice, :183 (provider-note chip)
  - strategy_lab_page.py:89, :93, :181
  - structuring_page.py:294, :299
  - trading_page.py:355
  - rules_page.py:255-263 (FMP HTTP 402 notice)
- UI-11b:
  - Flet bonds results are one vertical Column: wrapped stat rows, then card(price_yield_chart) at bonds_page.py:165 and card(krd_chart) at :166, each full width; scenarios put chart :176 above table :177-186. Flet has no two-table bond layout like Native.
  - card() (ui/components.py:51-64) is the single place to add a glass style. Flet 0.85.2 Container has a `blur` parameter and ft.Blur exists (verified). No blur or glass styling exists in ui/ or core/theme.py today.
- UI-12:
  - Text size 10 appears at 42 sites, size 11 at 71, size 9 at 1 (main.py:206). The stat label is size 10 (components.py:127).
  - The two ai_panel disclaimers appear on every result page.
  - For 알아보기: Flet 0.85.2 ft.Text has on_selection_change, with TextSelectionChangeEvent.selected_text, and ft.SelectionArea has on_change (both verified by introspection). 55 Text controls are already selectable=True. Glossary data already exists in core/education/glossary.py: TERMS with ko/en name, summary, meaning, use and limit; search() at :421; sections() at :381.
  - Flet charts are PNGs, so "what it means on the current chart" has to come from the result payload, not from chart interaction.

4. RUNNING A1 AND A3 TOGETHER (relevant to the owner's question)
- In Flet, A1 (label strings) and A3 (layout) touch the same page files (ui/bonds_page.py, structuring_page.py, quant_lab_page.py, rates_page.py, krx_page.py, macro_page.py, research_home.py). Running them in parallel will conflict unless split by file or done in sequence per page.
- A1 catalog edits in core/ui_legacy_messages.py and core/ui_messages.py also change Native, through the display() fallback.
- A3 work concentrated in ui/components.py (card and stat) and in the layout code is separable.
- Tests that pin current labels:
  - tests/research_home_acceptance.py:93, :166 (리서치 홈)
  - tests/desktop_market_tabs_acceptance.py (거시 지표표, 매크로 v2)
  - tests/desktop_language_acceptance.py and tests/desktop_startup_acceptance.py (연구 홈)

### 확인하지 못한 것

- Only the initial screens of 15 Flet views were rendered (stub page; no worker run, no network). The result-view strings (tables, stats, chips, narratives) are classified from source literals and from ko.text on those literals, not from running each analysis.
- The KRX, trading, rules, settings, home and market-chart pages were not built. Their findings come from code reading.
- A live Flet browser session (actual layout, wrapping, overflow and how blur looks) was not run. Whether ft.Blur gives an acceptable glass look in the browser renderer is unverified.
- The exact payload and behaviour of Text.on_selection_change in a running browser is unverified. Only the class signature was inspected.
- Whether the Native macro_records.py:132 QTreeWidget header 'Field' is translated is unverified (LanguageController handles QTableWidget headers; I did not trace QTreeWidget). The :251 result_table site is.
- That the Native Korean narrators accept the Flet-side result objects without adaptation is unverified for macro_korean, fx_korean, rates_korean and market_variants, which take Native 'out' wrappers. curve_korean, swap_korean, bond_korean, portfolio_korean, carry_korean and sabr_korean take core objects (signatures read, not run).
- Whether Flet's Monte Carlo narrative has any Korean counterpart in Native is unverified.
- Where Native still shows OBSERVED untranslated (UI-2) is outside this sweep and was not located.
- The proposed Korean terms are recommendations against general Korean financial usage. No authoritative industry glossary was consulted (no network).
- Imports for compare.py and literals.py loaded config.py, which calls load_dotenv(). No .env file exists in s10 or any of its parent directories: only .env.example is listed, and that is a name listing only, nothing was opened. All later runs stubbed dotenv.
- No file under docs/asset_expansion/cache was opened; the Strategy Lab build read docs/asset_expansion/cards, which is a different directory.

### 항목 목록 (50개)

```json
[
 {
  "id": "F-UI1-a",
  "where": "core/ui_messages.py:139 ('macro'); Native quantgen_desktop/translations.py:497",
  "current": "Flet nav Macro = 거시경제; Native = 매크로",
  "proposed": "매크로 (both apps)",
  "note": "Owner decision on the stem; Flet home already says 매크로 연구 (research_home.py:257)"
 },
 {
  "id": "F-UI1-b",
  "where": "core/ui_legacy_messages.py:232 (used by ui/macro_page.py:44); Native macro_narrative_language.py:6 and translations.py:489",
  "current": "Flet 거시경제 관측; Native 거시 지표표 (and a second, overridden Native entry 매크로 현황)",
  "proposed": "매크로 지표표 in all three places (delete the duplicate at translations.py:489)",
  "note": "Also delete the dead LEGACY 'Macro sheet':'macro' at core/ui_messages.py:190"
 },
 {
  "id": "F-UI1-c",
  "where": "core/ui_legacy_messages.py:232",
  "current": "'Macro v2':'거시경제 v2' (Native fallback only)",
  "proposed": "매크로 v2"
 },
 {
  "id": "F-UI1-d",
  "where": "ui/macro_page.py:44-45 (View dropdown)",
  "current": "Overlay state / Model cards / Research register (English in ko mode)",
  "proposed": "매크로 v2 · 오버레이 상태 / 매크로 v2 · 모형 카드 / 매크로 v2 · 연구 기록부",
  "note": "Native: 오버레이 상태 / 모델 카드 / 연구 등록부; choose one set for both"
 },
 {
  "id": "F-UI1-e",
  "where": "ui/research_home.py:257-258",
  "current": "Macro의 Research register와 연구 카드에서 근거를 확인하세요. / Macro 열기",
  "proposed": "매크로 화면의 연구 기록부와 연구 카드에서 근거를 확인하세요. / 매크로 열기"
 },
 {
  "id": "F-UI2-a",
  "where": "ui/research_home.py:172; Native quantgen_desktop/watchlist.py:53",
  "current": "OBSERVED -> 일별 관측 (both apps already translate it here)",
  "proposed": "정상 관측 in both maps if the owner wants that phrase everywhere; STALE 오래된 관측 · 확인 필요 unchanged",
  "note": "Find the Native place where OBSERVED still shows raw (outside this sweep)"
 },
 {
  "id": "F-UI2-b",
  "where": "ui/research_home.py:151, 263",
  "current": "raw execution_status COMPLETED / RUNNING / FAILED",
  "proposed": "완료 / 실행 중 / 실패 (code kept in tooltip)",
  "note": "Verdict codes PASS/NOT_RUN stay per 13-8/a"
 },
 {
  "id": "F-UI2-c",
  "where": "ui/components.py:165-171 (shown at macro_state_panel.py:437, 440)",
  "current": "ok, warmup, disputed, not run, stale, missing, provisional rejected, session mismatch, synthetic rejected, fail closed",
  "proposed": "정상, 준비 중, 이의 제기, 미실행, 지연, 누락, 잠정값 거부, 세션 불일치, 합성 데이터 거부, 안전 차단",
  "note": "Owner decision whether these count as status values like OBSERVED"
 },
 {
  "id": "F-UI6b-a",
  "where": "ui/rates_page.py:383 (Flet); quantgen_desktop/translations.py:405 (Native)",
  "current": "Flet 'Lookback (sessions)' (English); Native 관측 창 · 거래일",
  "proposed": "조회 기간 (일), with tooltip 거래일 기준"
 },
 {
  "id": "F-UI6b-b",
  "where": "core/ui_legacy_messages.py:228, 251; Native translations.py:62, 333, 357, 363; ui/fx_page.py Rebalance/History (sessions); ui/quant_lab_page.py Horizon (sessions)",
  "current": "Horizon · sessions = 분석 기간 · 관측 수 (Flet) / 분석 기간 · 거래일 (Native); Sessions = 관측 수 / 거래일; Rebalance · sessions = 리밸런싱 · 거래일",
  "proposed": "예측 기간 (일); 기간 (일); 리밸런싱 주기 (일); 과거 데이터 기간 (일). Keep 거래일 only in prose.",
  "note": "One unit word for every sessions field in both apps"
 },
 {
  "id": "F-UI6b-c",
  "where": "core/ui_legacy_messages.py:251; Native translations.py",
  "current": "Calendar days = 달력 일수 (Flet) / 달력일 (Native)",
  "proposed": "달력 기준 일수"
 },
 {
  "id": "F-UI6b-d",
  "where": "ui/krx_page.py:23-28",
  "current": "Quote / Daily OHLCV / Disclosures (DART) / Financials (DART) / Whole-market snapshot / Index levels (English); Native Quote = 호가",
  "proposed": "현재가 / 일별 시세 / 공시 (DART) / 재무제표 (DART) / 전 종목 시세 / 지수",
  "note": "호가 means bid/ask; this is a price snapshot"
 },
 {
  "id": "F-UI6b-e",
  "where": "ui/krx_page.py:35, 37, 108-116, 126-127, 136-137, 146-147, 156-158, 167-168",
  "current": "KRX code, Data, Change, Change %, Open / High / Low, Market cap, Open, High, Low, Report, Filer, Receipt, Statement, Account, This term, Prev term, Code, Market, Chg %, Mkt cap, Index, Level",
  "proposed": "종목 코드, 조회 항목, 전일 대비, 등락률, 시가 / 고가 / 저가, 시가총액, 시가, 고가, 저가, 보고서명, 제출인, 접수번호, 재무제표, 계정과목, 당기, 전기, 종목코드, 시장, 등락률, 시가총액, 지수명, 지수"
 },
 {
  "id": "F-UI10-a",
  "where": "core/ui_legacy_messages.py:253 (shared; Native fallback at quantgen_desktop/translations.py:640-644 reaches market_tools.py:133, 272 and macro_records.py:251)",
  "current": "'Fields':'필드', 'Field':'필드'",
  "proposed": "'Field' and 'Fields' -> 항목",
  "note": "Root cause of 필드 in the Native ETF and KRX quote tables"
 },
 {
  "id": "F-UI10-b",
  "where": "core/ui_legacy_messages.py:233, 257; Native translations.py:427 and the Metric entry near :564",
  "current": "Metric = 지표 (Flet) / 측정 항목 (Native); metrics = 지표; Metrics (table title) = 측정값 (Native)",
  "proposed": "Metric -> 항목; Metrics -> 주요 지표; Indicator stays 지표",
  "note": "Flet uses 지표 for Indicator, Metric and metrics"
 },
 {
  "id": "F-UI10-c",
  "where": "core/ui_legacy_messages.py:239-241, 245",
  "current": "Composite 종합 관측값; Signal components 지표별 관측값; Component 구성 지표; Stance 관측 방향; bullish 상승 관측 etc.",
  "proposed": "종합 점수; 구성 지표별 점수; 구성 지표; 방향; 강한 상승 우위 / 상승 우위 / 중립 / 하락 우위 / 강한 하락 우위 (the Native wording)"
 },
 {
  "id": "F-UI10-d",
  "where": "core/ui_messages.py:129; Native translations.py:485",
  "current": "Signals = 기술적 관측 (Flet) / 신호 (Native)",
  "proposed": "기술적 분석 (both)",
  "note": "Owner decision"
 },
 {
  "id": "F-UI10-e",
  "where": "ui/strategy_lab_page.py:59, 80 (via LEGACY at core/ui_messages.py:192)",
  "current": "card kind: model -> 모형, but strategy and distribution stay English in the same list",
  "proposed": "Explicit kind map: model 모형, strategy 전략, distribution 분포; remove the lower-case LEGACY words"
 },
 {
  "id": "F-UI10-f",
  "where": "core/ui_legacy_messages.py:227; core/ui_messages.py:146, 161; Native translations.py:57",
  "current": "Model 모형 (Flet) / 모델 (Native); Symbol 종목·통화쌍 / 종목 코드; Symbols · comma separated 종목 · 쉼표로 구분 / 종목 코드 · 쉼표로 구분",
  "proposed": "Pick one of 모형 or 모델 for both apps (모형 recommended for statistical and pricing models); Symbol -> 종목 코드 (통화쌍 only on FX pages); 종목 코드 (쉼표로 구분)"
 },
 {
  "id": "F-UI10-g",
  "where": "core/ui_legacy_messages.py:227-231",
  "current": "Drift 드리프트; Paths 경로 수; Seed 시드; Synthetic demo 합성 시연; Zero · stress 0 · 스트레스; Sample mean · noisy 표본 평균 · 잡음 주의",
  "proposed": "드리프트 가정; 시뮬레이션 경로 수; 난수 시드; 합성 데이터 시연; 0 (스트레스 가정); 표본 평균 · 추정 오차 유의"
 },
 {
  "id": "F-UI10-h",
  "where": "core/ui_messages.py:113; core/ui_legacy_messages.py:233 and Korean sources at :15, 34, 79, 80, 180, 187; Native translations.py:100",
  "current": "Provider 공급처 (Flet) / 공급자 (Native); Flet itself mixes the two",
  "proposed": "제공처 (one word, both apps)"
 },
 {
  "id": "F-UI10-i",
  "where": "core/ui_legacy_messages.py:237, 241, 248; Native translations.py:269-271",
  "current": "At bound 경계값 도달 / 경계 도달; Reason 이유 / 사유; Annual 연간 (Flet) / 연 1회 (Native, beside 반기 and 분기)",
  "proposed": "비중 한도 도달; 사유; frequencies 연 1회 / 연 2회 / 연 4회 under the label 연간 이자 지급 횟수"
 },
 {
  "id": "F-UI10-j",
  "where": "core/ui_legacy_messages.py:254-255",
  "current": "Price vs 50-day SMA 가격과 SMA50의 위치; Volatility regime 변동성 국면 (Native 변동성 상태)",
  "proposed": "50일 이동평균 대비 가격; 변동성 국면 (both)"
 },
 {
  "id": "F-UI10-k",
  "where": "ui/rates_page.py:228, 279 (Native glossary translations.py:456)",
  "current": "Forward (English in Flet); Native maps Forward to 선물환",
  "proposed": "Rates: 선도금리; FX: 선물환 (separate keys, e.g. 'Forward rate')",
  "note": "Context collision; do not reuse Native's 'Forward' on Rates"
 },
 {
  "id": "F-UI10-l",
  "where": "ui/fx_page.py:286, 290; Native translations.py:433",
  "current": "Point (English in Flet) / 지점 (Native)",
  "proposed": "구분"
 },
 {
  "id": "F-UI10-m",
  "where": "ui/fcharts.py, ui/qcharts.py, ui/xcharts.py (59 title/axis/legend calls)",
  "current": "Chart text baked into PNGs in English; translate_controls cannot reach it",
  "proposed": "Pass the language into the chart builders and re-render on locale change"
 },
 {
  "id": "F-UI10-n",
  "where": "ui/research_home.py:228, 230, 232",
  "current": "Data source를 synthetic, Symbol을 SPY, Model을 gbm으로 선택하세요… (English label names)",
  "proposed": "데이터 출처를 합성 데이터 시연, 종목 코드를 SPY, 모형을 GBM으로 선택하세요…",
  "note": "Korean mode never shows the English labels this text refers to"
 },
 {
  "id": "F-UI10-o",
  "where": "ui/research_home.py:157, 158, 203, 259, 260 ('Quant Lab'), :230 ('Strategy Lab'); core/ui_messages.py:134-135",
  "current": "Korean sentences say Quant Lab / Strategy Lab while the nav says 분포 분석 / 전략 실험실",
  "proposed": "Use the nav names in the sentences (분포 분석 열기, 전략 실험실에서 …)"
 },
 {
  "id": "F-UI10-p",
  "where": "core/ui_legacy_messages.py:238; core/ui_messages.py:119, 155",
  "current": "'Close' -> 종가 shadows 'close' -> 닫기; 'Signal' always -> 신호선",
  "proposed": "Context keys (e.g. 'Close price' -> 종가, 'Signal line' -> 신호선)",
  "note": "Latent; no Flet Close button found today"
 },
 {
  "id": "F-UI10-q",
  "where": "core/ui_messages.py:12, 152-153; Native translations.py",
  "current": "Light 밝게 / Dark 어둡게 (Flet) vs theme_light 라이트 (Flet) and 라이트 / 다크 (Native)",
  "proposed": "라이트 / 다크 (both)"
 },
 {
  "id": "F-UI11a-a",
  "where": "ui/bonds_page.py:132-138",
  "current": "가격 | Yield | Macaulay | Modified | Convexity | DV01 | z-spread",
  "proposed": "가격 | 수익률 | 맥컬리 듀레이션 | 수정 듀레이션 | 볼록성 | DV01 | Z-스프레드"
 },
 {
  "id": "F-UI11a-b",
  "where": "ui/bonds_page.py:157-167",
  "current": "Carry (…) / Roll-down / Carry + roll / Breakeven / 'Key-rate DV01, z-spread … held'",
  "proposed": "캐리 / 롤다운 / 캐리+롤다운 / 손익분기 금리 상승폭 / 만기 구간별 DV01 (KRD)"
 },
 {
  "id": "F-UI11a-c",
  "where": "ui/bonds_page.py:181, 194-200",
  "current": "Scenario | Shock | New price | P&L | P&L %; Futures DV01, Contracts to sell, Rounded",
  "proposed": "시나리오 | 금리 충격 | 변동 후 가격 | 손익 | 손익률; 선물 DV01, 매도 계약 수, 반올림 계약 수"
 },
 {
  "id": "F-UI11a-d",
  "where": "ui/structuring_page.py:61-63",
  "current": "Delta (per +1% spot), Gamma (per +1%), Vega (per vol-pt), DV01 (per -1bp), 2s10s DV01 (per +1bp)",
  "proposed": "델타 (현물 +1%당), 감마 (+1%당), 베가 (변동성 1%p당), DV01 (-1bp당), 2s10s DV01 (+1bp당)",
  "note": "Native uses different English sources ('Delta · per +1% spot'); unify the keys"
 },
 {
  "id": "F-UI11a-e",
  "where": "ui/structuring_page.py:181, 183, 189, 191, 192; Native quantgen_desktop/structuring.py:61, 66, 68",
  "current": "Legs (per 100 of notional, signed for the holder); Leg | Kind | 값 | Detail; Hedge sheet (…); 상품 | Quantity | 단위 | Rationale; 'No first-order hedge: every Greek is zero.' Native titles Greeks / Leg decomposition / Hedge sheet untranslated",
  "proposed": "구성 요소 분해 (액면 100 기준, 보유자 관점 부호); 구성 요소 | 유형 | 가치 | 세부 내용; 헤지 내역 (+ 매수·고정금리 지급, − 매도·고정금리 수취); 상품 | 수량 | 단위 | 근거; 1차 헤지 없음: 모든 민감도가 0입니다. Titles: 민감도(그릭스), 구성 요소 분해, 헤지 내역",
  "note": "Native 'Leg' is 구성요소 (no space); pick one spelling"
 },
 {
  "id": "F-UI11a-f",
  "where": "ui/rates_page.py:229-235, 265-269",
  "current": "Strike / Premium (two stats both labelled Premium) / Delta (per +1bp fwd) / Gamma (per bp²) / Vega / Theta (1d) / Other-model vol / Caplets / Dearest caplet",
  "proposed": "행사가격 / 프리미엄 · 금액 and 프리미엄 · bp / 델타 (선도금리 +1bp당) / 감마 (bp²당) / 베가 / 세타 (1일) / 대체 모형 변동성 / 캐플릿 / 최고가 캐플릿"
 },
 {
  "id": "F-UI11a-g",
  "where": "core/ui_legacy_messages.py:247, 250-251; Native translations.py:324, 434",
  "current": "CTD DV01 / contract 계약당 CTD DV01 (Flet) / 계약당 최저가인도채권 DV01 (Native); Strike 행사가 / 행사가격; Expiry 만기 / 옵션 만기",
  "proposed": "계약당 CTD DV01 (CTD stays English); 행사가격 (and 행사가격 %); 옵션 만기 for options, 만기 otherwise"
 },
 {
  "id": "F-UI14",
  "where": "core/ui_messages.py:16; quantgen_desktop/translations.py:46",
  "current": "설계·검증 (Flet) / 설계 및 검증 (Native)",
  "proposed": "설계/검증 (both)"
 },
 {
  "id": "F-UI15",
  "where": "core/ui_messages.py:17; quantgen_desktop/translations.py:47; ui/research_home.py:224 + core/ui_legacy_messages.py:205",
  "current": "포트폴리오·위험 (Flet nav), 포트폴리오 및 위험 (Native), Home shortcut '포트폴리오 · 위험'",
  "proposed": "분석 (as asked); the Home shortcut becomes the same word",
  "note": "Collides with Native nav 분석 도구 (quantgen_desktop/app.py:249, 425). Ask the owner whether 포트폴리오 분석 is acceptable."
 },
 {
  "id": "F-NAV-a",
  "where": "core/ui_messages.py:14 (pinned by tests/research_home_acceptance.py:93, 166); Native translations.py:40",
  "current": "Research Home 리서치 홈 (Flet) / 연구 홈 (Native)",
  "proposed": "연구 홈 (both); update the Flet test"
 },
 {
  "id": "F-NAV-b",
  "where": "core/ui_legacy_messages.py:205 (EN_TO_KO), ui/research_home.py:224, core/ui_messages.py:18; Native translations.py:48",
  "current": "연구 라이브러리 (Flet nav and shortcut), 연구 기록 (shadowed MESSAGES entry), 연구 보관함 (Native)",
  "proposed": "연구 보관함 (both)"
 },
 {
  "id": "F-NAV-c",
  "where": "core/ui_messages.py:21, 132; main.py:216, 246",
  "current": "Indicator guide 지표 가이드; Connections 데이터 연결 (Native 연결); Execution · simulated 모의 실행 (Native Paper Trading 모의매매); 실시간 시세 · 차트",
  "proposed": "기술지표 가이드; 데이터 연결 (both); 모의매매 (both); 실시간 시세·차트"
 },
 {
  "id": "F-138-a",
  "where": "ui/bonds_page.py:140; crypto_page.py:103; derivatives_page.py:132; etf_page.py:158; fx_page.py:237, 308, 378; macro_page.py:133, 140, 142; portfolio_page.py:209; quant_lab_page.py:400; rates_page.py:156, 200, 257, 293, 363; signals_page.py:206; strategy_lab_page.py:168",
  "current": "Every Flet local narrative is English in ko mode",
  "proposed": "Reuse the Qt-free Native narrators (bonds_portfolio_narrative, rates_narrative, fx_narrative, macro_narrative_language, market_narrative_language, model_narrative_language); move them under core/ so both apps import one copy. Keep the English original for exports.",
  "note": "Flet Monte Carlo has no known Korean narrator (unverified)"
 },
 {
  "id": "F-138-b",
  "where": "ui/ai_panel.py:52-53, 69, 78-98",
  "current": "Ask the analyst something specific (optional) / Deep analysis / Analysis / engine: local / two English disclaimers on every result page",
  "proposed": "분석가에게 질문 (선택) / 심층 분석 / 분석 / 엔진: 로컬 / one short Korean disclaimer, rest in a tooltip"
 },
 {
  "id": "F-138-c",
  "where": "ui/bonds_page.py:123, 213; quant_lab_page.py:324, 340, 343, 348, 354; signals_page.py:169, 183; portfolio_page.py:136-140, 146; crypto_page.py:50; derivatives_page.py:75; etf_page.py:172",
  "current": "Provider, model and method notes in English, many as chips or size-11 captions",
  "proposed": "Korean variants (Native has several: model_note_korean, sheet_note_korean, letf_korean, coverage_korean); show the provider note in a tooltip only"
 },
 {
  "id": "F-RULING-71",
  "where": "ui/research_home.py:173, 178, 216; market_chart_page.py:538-544; macro_page.py:43, 121, 161; krx_page.py:71, 116; rates_page.py:125; structuring_page.py:159-160; derivatives_page.py:78; fcharts.py:90, 108, 258",
  "current": "Flet still shows provider and observation date/time in live views; PR #71 deliberately left Flet unchanged",
  "proposed": "Apply the 2026-11-04 ruling to Flet: provider and time in a tooltip, export keeps them, stale, delayed and failed states stay visible as text",
  "note": "Needs the owner to confirm that the ruling covers the browser app"
 },
 {
  "id": "F-UI9",
  "where": "ui/quant_lab_page.py:37, 56, 110, 129, 138, 155, 340, 343, 348, 354; signals_page.py:27, 29, 183; strategy_lab_page.py:89, 93, 181; structuring_page.py:294, 299; trading_page.py:355; rules_page.py:255-263",
  "current": "Inline English captions, provider-note chips (FMP and KIS notes) and long empty-state paragraphs on the Build & Test pages; Flet has no right-side pane",
  "proposed": "Source dropdown shows only 자동 / FMP / KIS (rule in a tooltip); drop the provider-note chips; move method captions into one collapsed 참고 section (ft.ExpansionTile) per page; shorten empty states to one sentence"
 },
 {
  "id": "F-UI11b",
  "where": "ui/bonds_page.py:165-166 (calc charts), :176-186 (scenario chart + table); ui/components.py:51-64 (card)",
  "current": "Vertical stack; each chart card full width; scenario table under its chart; plain bordered cards",
  "proposed": "ft.ResponsiveRow with col md=6 for the two charts, and chart | table side by side for scenarios; glass card in card(): semi-transparent surface + Container blur=ft.Blur(...) + light border",
  "note": "ft.Blur and Container.blur verified in Flet 0.85.2"
 },
 {
  "id": "F-UI12-a",
  "where": "ui/ (size=10 at 42 sites, size=11 at 71, size=9 at main.py:206); ui/components.py:127",
  "current": "Many muted 10-11 px captions and notes; stat labels at 10 px",
  "proposed": "Minimum 12 px for body notes and 11 px for chip text; move non-essential notes into tooltips or the 참고 section"
 },
 {
  "id": "F-UI12-b",
  "where": "Flet Text controls (55 already selectable=True); core/education/glossary.py:35-354 (TERMS), :381 (sections), :421 (search)",
  "current": "No term lookup from selected text",
  "proposed": "Text.on_selection_change (event.selected_text) -> 알아보기 button -> side panel showing glossary sections (개념 / 적용 / 이 결과에서의 의미, filled from the page's result payload)",
  "note": "Charts are PNG images, so 'on the current chart' must come from the payload"
 }
]
```

## A3 배치 조사 (UI-9, UI-11b, 유리 질감)

A3 LAYOUT SWEEP (UI-9, UI-11b, glass style). Read-only. Worktree s10 at 516953a; its tree is identical to faf9f3b (git diff faf9f3b HEAD is empty). git status was clean after every run, and no file under s10 is newer than my scripts. Every script and output is under /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/.

HOW THE SCREENS WERE RENDERED (offline only)
- Screenshot script: /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/shoot_a3.py. It follows the shoot_after.py pattern, with these offline controls:
  - dotenv.load_dotenv and dotenv_values patched, so no .env is read.
  - requests and socket blocked.
  - config.fmp_key/fmp_ready/kis_ready patched to empty/False. This is the owner's reported "no FMP key" state from REMAINING B1.
  - HOME and XDG dirs pointed at ui_a1a3/home. QT_SCALE_FACTOR=1, window 1360x900.
- Build & Test runs the production execute_analysis with the production load_history. With no keys, load_history takes its own synthetic fallback and adds its own "FMP_API_KEY is not configured; ..." note. It also runs the production funding_rate with FRED loaders that raise, which gives its own "rf 3.00% assumed · FRED unavailable" line. Inputs: symbol AAPL, every other control at its default (GARCH(1,1)-t, premium drift, 126 sessions, 5000 paths, seed 7).
- Bonds uses tests.desktop_acceptance.bond_fixture (a synthetic curve panel) with the default inputs.
- Screenshots in /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/shots/ (each in _ko and _en):
  - Build & Test viewport at 1360x900: buildtest_before, buildtest_top, buildtest_result.
  - Build & Test full pages: buildtest_full (1360), buildtest_1000w_full.
  - Bonds viewport at 1360x900: bonds_top, bonds_tables, bonds_chart.
  - Bonds full pages: bonds_calc_full, bonds_scenarios_full, bonds_calc_1000w_full.
  - Measurements: a3_measure_ko.json and a3_measure_en.json.
- Runtime prototypes. Widgets were re-parented in memory only; no repository change.
  - proto_bonds.py writes proto_bonds_{calc,scenarios}_{1360,1000}w_full_{ko,en}.png, proto_bonds_{calc,scenarios}_view_{ko,en}.png and proto_bonds_measure_{ko,en}.json.
  - proto_buildtest.py writes proto_buildtest_{1360,1000}w_full_{ko,en}.png and proto_buildtest_measure_{ko,en}.json.

(1) UI-9: THE BUILD & TEST RIGHT-SIDE EXPLANATION
Widgets:
- Page: app.py:521.
- Results panel: panel("분포와 근거"), app.py:567.
- Chart: FanChart, app.py:568, minimum height 240 (charts.py:84, :112).
- Right text: self.quant_notes, one UiLabel of role "muted" (app.py:573) with 14px body text (typography.py:172), muted colour (:183), word-wrapped and selectable (app.py:103-109).
- Layout: ChartStudy(chart, notes) (app.py:575), split 2:1 (chart_study.py:17), stacking below a breakpoint of 820 (chart_study.py:7, :61-64).
- Text source: built in job_succeeded at app.py:908-930 as one "\n"-joined string.

Layout bug: app.py:575 uses `inner.insertWidget(0, ChartStudy(...))`. Index 0 sits before the heading that panel() adds at app.py:144-145, so the chart and notes draw above the panel heading "분포와 근거" (visible in buildtest_full_ko.png).

Measured at 1360x900 (ko):
- ChartStudy 1050x527: chart 688x240, notes 344x527. That leaves 287px of blank space under the chart.
- English: notes 342x544.
- At 1000x700 (viewport 814) the split stacks: chart 690x240, then notes 690x340.

Exact current text (ko run; source_text and Korean display are identical except the first line, so 12 of 13 lines stay English in Korean mode):
1. "합성 데이터 · SYNTHETIC · 2024-11-29 → 2026-11-04" (app.py:909; provider plus observation dates)
2. "FMP_API_KEY is not configured; Simulated series (GBM, μ=13%, σ=36%) — no market data provider was used." (h.note: history.py:511 plus :259-260)
3. "rf 3.00% assumed · FRED unavailable" (value.funding_note, analysis.py:73)
4. "risk premium: rf 3.00% + ERP 4.00% = expected (arithmetic) return 7.00%; log drift = that - convexity correction 6.28% (per step from each path's conditional variance, horizon average; normal innovations) = +0.72%" (r.drift_note, montecarlo.py:211-231)
5. "Innovations are effectively normal (the t fit found no heavier tail), so they are drawn unbounded and no cap applies." (r.bound_note, montecarlo.py:280-281)
6. "Next-session conditional forecast volatility, annualized using 252 sessions." (mc_disclosure.py:10-11)
7. "Horizon-average volatility: sqrt(mean forecast daily variance) * sqrt(252), using the engine innovation convention" (app.py:916, mc_disclosure.py:15)
8. "GARCH fit: alpha=0.0000, beta=0.9910, nu=510.930" (app.py:921)
9. "converged=True · persistence=0.9910 · half-life=76.47 sessions" (app.py:922)
10. "at_bound: ('alpha',)" (app.py:923-925; a raw Python tuple)
11. "note: GARCH(1,1)-t on 503 sessions, mu fixed at -0.084%/day: alpha=0.000 beta=0.991 persistence=0.991 nu=510.9 (10.9 to normal); normal innovations (nu = 511 > 100); alpha at bound; standard errors undefined: the information matrix is not positive definite at the optimum." (repeats line 8's numbers)
12. "se_note: the information matrix is not positive definite at the optimum" (repeats the end of line 11)
13. "eta 95% profile interval: (0.0, 0.0919318057082417)" (app.py:929; raw float with 17 digits)

Lines that appear only in other cases:
- r.jump_note (montecarlo.py:141, :156)
- the bootstrap text (mc_disclosure.py:30-38; a required disclosure)
- "Target probability: final price >= ..." (app.py:918)
- "{alpha|beta|persistence} 95% Wald interval: (lo, hi)", as raw tuples (app.py:926-928)
- "interval_at_bound: ..."

FMP and provider sentences:
- Line 1 (provider plus dates).
- Line 2. Its other forms: "KIS credentials are not configured; ..." (history.py:496, :506); "FMP close adjusted for splits and dividends" or "FMP close, NOT dividend-adjusted (no adjClose in the response)" (:183-184); "KIS 수정주가: adjusted for splits and rights, cash dividends not included" (:225); "Yahoo adjusted close" (:281); and the suffix "; cached YYYY-MM-DD HH:MM" (:438).
- Line 3. Its other forms: "rf x% · FRED DGS3MO date" (analysis.py:70); "rf x% · KRW 3m · FRED date · monthly" (:65); "Funding rate not applied for this drift" (:87).
- In the same form, the data source combo shows "Auto · KIS / FMP" and "FMP" (app.py:536; Korean "자동 · KIS / FMP" at translations.py:294).

What makes it cluttered:
- It is one undifferentiated muted label with no sections or bullets, and it wraps mid-token ("half-\nlife").
- It mixes developer debug output (raw tuples, `converged=True`, a 17-digit float, `field: value` keys).
- It repeats itself: line 11 repeats line 8, line 12 repeats line 11, and the volatility value is already a table row.
- It shows provider and key-configuration messages.
- It is English in Korean mode: none of lines 2-13 has a catalog entry (git grep found them only in app.py).
- At 1360 it is 2.2 times taller than the chart, so the left column is blank under the chart.

Nearby issues:
- The quant_metrics minimum height is 280 (app.py:571), but its 8 rows need 324. The last row, "Horizon-average vol (ann.)", sits behind an inner scroll at both widths.
- The status line "COMPLETED · 검증 NOT_RUN · 재현성 PARTIAL" (app.py:931) and the caption at app.py:576 are A1 or UI-12 material.

What the MC notes are tied to:
- They are display-only. The MC export holds the run record, not the notes (export_selected, app.py:1028; completed() in runs.py:111-133 records data.source, adjustment and parameters.rf_rate but not the "assumed" flag).
- Tests read the label:
  - desktop_acceptance.py:390 needs 'annualized using 252 sessions' in quant_notes.text() (English).
  - desktop_acceptance.py:404 needs 'final price >= 100.00 after 5 sessions'.
  - mc_bootstrap_disclosure_acceptance.py:530-556 needs BOOTSTRAP_TEXT exactly once in English, BOOTSTRAP_TEXT_KO in Korean, source_text unchanged, and the lines identical apart from the bootstrap line.

Recommended mechanism: keep quant_notes.source_text as is (all evidence) and display a cleaned variant through the existing UiLabel.localized_text / display_variants pattern (localization.py:24-27; bonds_portfolio_narrative.py:168-171). The required disclosures then stay, and the tests above either still pass or need only targeted updates.

Runtime prototype (proto_buildtest): heading first, then chart, then a sectioned reading column (eyebrow-role section heads, typography.py:177) and a collapsed "▸ 모델 진단 자세히 보기" toggle.
- ChartStudy height at 1360 went from 527 to 240 (ko) and from 544 to 293 (en), so the chart and text columns now match.
- At 1000 it is 690x483 (stacked).

(2) UI-11b: THE BONDS PANE
Current widget order inside BondsPane's QVBoxLayout (bonds.py:25, spacing 18, no outer panel except the form):
1. Form panel: panel('Bonds · 가격·위험·시나리오·선물 헤지'), bonds.py:26-50.
2. metrics: table(['Metric','Value']), minimum height 360, bonds.py:51.
3. ChartStudy(chart LineChart 280px, notes), inserted at index 2 (bonds.py:56-58).
4. krd: table(['Key tenor · years','DV01 · currency / bp']), minimum height 260, bonds.py:53.
5. scenarios: 5 columns, minimum height 310, hidden unless Tool = Scenarios (bonds.py:54, :91).
6. hedge label (bonds.py:55).
7. exports (bonds.py:59-61).

So "the two tables" are metrics and krd. They are not adjacent: the chart and notes sit between them. All tables sit directly on the page background with no panel; only the form has the QFrame#panel depth.

Why there is empty right space:
- table() (app.py:149-162) sets QHeaderView Stretch on every column of a table with 7 or fewer headers. Each 2-column table spans the whole pane, which measured 1114px (ko) and 1108px (en) at 1360.
- Each column is 552px wide, but the content needs only 114/131px (metrics) and 122/144px (krd). Values therefore start mid-table, about 1114 − 275 = 840px of each row is blank, and the right half of each table is empty.
- At 1000 the columns are 372px wide and the content needs the same 114-144px.

Why the tables look overlapped or clipped:
- metrics has 12 rows that need 468px against a minimum of 360. Roll-down, Carry + roll and Breakeven are hidden behind an inner scroll bar.
- krd has 9 rows that need 360px against 260. The 10, 20 and 30-year rows are hidden, and the "10" row is cut off at the table edge.
- Scenarios has 9 rows that need 1129px against 310.
- A real overlap of widgets was not reproduced offscreen at 1360x900 or 1000x700. In the measured geometry each widget starts 18px below the previous one.

Bond notes (bond_notes, bonds_portfolio_narrative.py:131-135; bonds.py:98-103):
- "Synthetic curve · not current market data" / "합성 곡선 · 현재 시장 데이터 아님"
- "SYNTHETIC · 2026-11-04 · bootstrap · 30 sessions" / "... · 30 거래일" (provider, date and method; still listed as known issue 7 in docs/product/MARKETS_WATCHLIST_2026-11-04.md:83)
- "Simulated Treasury par curve (Nelson-Siegel random walk) — no market data provider was used." shown twice: curve.note copies panel.note (curves.py:266-267 ← data.py:140), so the duplicate appears whenever panel.note is non-empty.
- Then the narrative.

Scenarios table: the "Shock · bp" cell is `str(r.shock_bp)` (bonds.py:90). For the curve-shape scenarios (bonds.py core :274-288) that prints a raw dict, for example "{0.25: 0.0, 1.0: 0.0, 2.0: 0.0, 3.0: 1.7857142857142858, ...}". It needs 1375px and makes rows very tall. Flet already formats this with _shock_text (ui/bonds_page.py:52-56). The export keeps the scenario objects, not the cell text (bonds.py:108).

Side-by-side requirements (measured; prototype proto_bonds):
- Pane width: 1114/1108px at 1360 and 754/748px at 1000 (ko/en).
- Two columns with an 18px gap: 548/545px each at 1360 and 368/365px at 1000.
- Inside panel() (22px side margins plus the border), each table is 502/499px at 1360 and 322/319px at 1000.
- Needed width: 245px for metrics and 266px for krd (header hints included).
- With column 0 set to ResizeToContents, column 1 to Stretch, and each table's height fitted to its rows (header 36 + 36 per row; no inner scroll), all 21 rows show at both widths and horizontal and vertical scroll maxima are 0.
  - Panel heights: 545 (metrics) and 437 (krd).
  - The krd panel ends 108px above the metrics panel. That is new empty space on the right.
- The chart and notes wrapped in a panel stay side by side at 1360 (chart 700x280, notes 350x323) and stack at 1000 (inner 708 < 820).
- The prototype's page height at 1360 is 1744 against 1760 today, but nothing hides behind an inner scroll any more.

(3) GLASS AND PANEL-DEPTH STYLE TO REUSE
- typography.py:27-33, PANEL_DEPTH:
  - Light: top #FFFFFF, bottom #FAF9F4, edge_top #ECEDE6, edge_bottom #D2D5C9.
  - Dark: #1B2A23, #15201B, #3F5649, #0A110E.
- typography.py:168-171: `QFrame#panel` has a vertical qlineargradient, a 1px border with a lighter top edge, a 2px bottom edge and 14px radius. `QFrame#panel QLabel` has a transparent background.
- The helper is app.py:138-146: panel(title) gives margins 22/20, spacing 12 and a heading label of role 'heading' (typography.py:174, an 18px/600 label with a 3px accent left bar). Other uses: markets_view.py:401, :714, :1026.
- Constraints:
  - No QGraphicsDropShadowEffect: the rationale is at typography.py:28-29, and test desktop_typography_acceptance.py:325 enforces it. "Glass" must therefore be stylesheet-only.
  - desktop_typography_acceptance.py:345-348 pins the gradient and the bottom-edge colours #D2D5C9 and #0A110E.
  - There is no translucent or "glass" token yet. The rounded chevrons and lists from PR #71 (typography.py:99-135) are the existing "liquid glass" work.
- Gotcha seen in the prototype: a plain QWidget container placed inside a panel paints p.bg through `QWidget { background: p.bg }` (typography.py:166), which draws a grey box inside the card. A new reading container needs a QFrame with an object name and a transparent rule, or its labels added directly. ChartStudy, a QWidget subclass, does not paint a background.

### 확인하지 못한 것

These were checked offscreen on Linux only (PyQt6, QT_SCALE_FACTOR=1, the bundled QG Interface fonts, light theme). The following were not checked:
- Rendering on Windows, the dark theme, and 125% or 150% scaling.
- What the owner meant by "겹치지 않게" (no overlap). No real widget overlap appeared at 1360x900 or 1000x700. The explanation that hidden rows behind inner scroll bars read as overlap is an inference.
- Real FMP, FRED or KIS notes. Only the no-key synthetic path and the FRED-failure path were rendered. The FRED and KIS note texts above are quoted from code, not seen on screen.
- Other models and tools. Only the default GARCH(1,1)-t run was rendered for Build & Test, so the GBM, jump and bootstrap notes, the Wald-interval lines and the target-price sentence were not seen on screen. The Bonds hedge tool was not rendered.
- Column widths after A1 translates the bond metric labels and headers into Korean. Measured needs (114/131px and 122/144px) are for today's English labels.
- Page-level horizontal scroll in the prototypes. Table horizontal and vertical scroll maxima were measured and were 0; the page's own horizontal scroll was not.
- The Strategy Lab tab of Build & Test.
- The Flet browser pages (left unchanged under the 2026-11-03 ruling).
- Whether existing tests pass after the proposed changes. I ran no test suite. Test constraints were read from the test source only.

### 항목 목록 (20개)

```json
[
 {
  "id": "UI9-1",
  "where": "quantgen_desktop/app.py:575 (panel() adds the heading at app.py:144-145)",
  "current": "inner.insertWidget(0, ChartStudy(quant_chart, quant_notes)) puts the chart and notes ABOVE the panel heading '분포와 근거' / 'Distribution and evidence'",
  "proposed": "inner.insertWidget(1, ...): heading, then chart and reading, then metrics table, then caption",
  "note": "Verified in buildtest_full_ko.png and buildtest_full_en.png; proto_buildtest shows the fixed order"
 },
 {
  "id": "UI9-2",
  "where": "app.py:909-910; core/quant/history.py:511 (also :496, :506, :183-184, :225, :281, :438)",
  "current": "Line 1 '합성 데이터 · SYNTHETIC · 2024-11-29 → 2026-11-04'; line 2 'FMP_API_KEY is not configured; Simulated series (GBM, μ=13%, σ=36%) — no market data provider was used.'",
  "proposed": "Show only a data badge: '합성 데이터 · 시장 데이터가 아닙니다' / 'Synthetic data · not market data' (shown only when SYNTHETIC). Drop the FMP/KIS key sentence, the provider name, the cached stamp and the date range from the display; keep them in source_text.",
  "note": "The synthetic warning must stay (history.py:11-16 rationale). Key-configuration status belongs on System > Connections."
 },
 {
  "id": "UI9-3",
  "where": "app.py:910 ← core/research/analysis.py:65, :70, :73, :87",
  "current": "'rf 3.00% assumed · FRED unavailable' (or 'rf x% · FRED DGS3MO date')",
  "proposed": "Fold into the assumption line: '무위험금리 3.00%(가정값)' / 'Risk-free 3.00% (assumed)'. Write '(가정값)' only when FRED failed; drop the provider name and date.",
  "note": "'Assumed' is not in the export (runs.py:131-132 records only rf_rate), so do not drop it entirely. Owner decision."
 },
 {
  "id": "UI9-4",
  "where": "app.py:910 ← core/quant/montecarlo.py:211-231",
  "current": "'risk premium: rf 3.00% + ERP 4.00% = expected (arithmetic) return 7.00%; log drift = that - convexity correction 6.28% (per step from each path's conditional variance, horizon average; normal innovations) = +0.72%'",
  "proposed": "Assumption section, two bullets: '무위험금리 3.00%(가정값) + 주식위험프리미엄 4.00%' and '로그 추세 +0.72%/년 (볼록성 보정 6.28% 차감)'. The 'per step ...' method clause moves to the details section.",
  "note": "Numbers copied from r.rf_rate, r.erp, r.mu_annual and r.correction_annual, never recomputed. Korean wording is A1/13-8 territory."
 },
 {
  "id": "UI9-5",
  "where": "app.py:910 ← montecarlo.py:273-281",
  "current": "'Innovations are effectively normal (the t fit found no heavier tail), so they are drawn unbounded and no cap applies.' (or the long '±Z cap' sentence)",
  "proposed": "Model bullet: 'GARCH(1,1)-t · 꼬리가 정규분포에 가까워 상한 없이 추출'. The full cap sentence goes to details.",
  "note": ""
 },
 {
  "id": "UI9-6",
  "where": "app.py:914-917; core/research/mc_disclosure.py:10-11, :15",
  "current": "'Next-session conditional forecast volatility, annualized using 252 sessions.' plus 'Horizon-average volatility: sqrt(mean forecast daily variance) * sqrt(252), using the engine innovation convention'",
  "proposed": "One bullet: '변동성: 다음 거래일 조건부 예측을 252거래일로 연율화'. The formula line goes to details.",
  "note": "Test desktop_acceptance.py:390 needs 'annualized using 252 sessions' in the English display text; keep the phrase or update the test."
 },
 {
  "id": "UI9-7",
  "where": "app.py:920-929",
  "current": "'GARCH fit: alpha=0.0000, beta=0.9910, nu=510.930' / 'converged=True · persistence=0.9910 · half-life=76.47 sessions' / \"at_bound: ('alpha',)\" / 'note: GARCH(1,1)-t on 503 sessions, ...' (repeats the parameters) / 'se_note: ...' (repeats the end of note) / 'eta 95% profile interval: (0.0, 0.0919318057082417)' / Wald intervals printed as raw tuples",
  "proposed": "Visible: '지속성 0.9910 · 반감기 76.47거래일'. Everything else goes in a collapsed '▸ 모델 진단 자세히 보기' section as labelled rows (α, β, ν, 수렴 여부, 경계에 걸린 계수, 표준오차, 95% 구간), with tuples formatted as 'lo–hi' at the precision already used. Remove the duplicate se_note line from the display.",
  "note": "Formatting the display changes no number. The raw text stays in source_text."
 },
 {
  "id": "UI9-8",
  "where": "app.py:573 (one UiLabel of role 'muted'); app.py:930; translations.py (no entries for lines 2-13)",
  "current": "13 lines in one undifferentiated muted label; English in Korean mode except line 1",
  "proposed": "Keep source_text and switch the display through localized_text (localization.py:24-27; the display_variants pattern at bonds_portfolio_narrative.py:168-171). Sections: 데이터 / 가정 / 모델 + details toggle. Section heads use role 'eyebrow' (typography.py:177).",
  "note": "Tests mc_bootstrap_disclosure_acceptance.py:530-556 need the bootstrap text once (EN) and BOOTSTRAP_TEXT_KO (KO), with source_text unchanged. desktop_acceptance.py:404 needs the target sentence."
 },
 {
  "id": "UI9-9",
  "where": "quantgen_desktop/chart_study.py:17, :45-49 (2:1 split)",
  "current": "At 1360: chart 688x240 next to notes 344x527, leaving 287px blank under the chart. At 1000 the two stack (690x240, then 690x340).",
  "proposed": "With the sectioned summary (UI9-2 to UI9-8) the reading column measures 344x240 (ko) and 342x293 (en) at 1360, level with the chart (proto_buildtest_1360w_full_*.png). The 2:1 split needs no change.",
  "note": "Measured in the runtime prototype only"
 },
 {
  "id": "UI9-10",
  "where": "app.py:571",
  "current": "quant_metrics.setMinimumHeight(280); 8 rows need 324px, so 'Horizon-average vol (ann.)' hides behind an inner scroll",
  "proposed": "Fit the height to the rows after table_rows (header + rowHeights + frame) and turn off the vertical scroll bar; the same helper serves Bonds",
  "note": ""
 },
 {
  "id": "UI9-11",
  "where": "app.py:536; translations.py:294",
  "current": "Data source items 'Auto · KIS / FMP' ('자동 · KIS / FMP'), 'FMP', 'KIS · KRX', 'Synthetic demo'",
  "proposed": "Label the auto item '자동' / 'Auto'. Whether to hide the FMP item is for the owner (B1: FMP not configured, replacement provider pending).",
  "note": "Changing the label is display-only; removing the option changes behaviour."
 },
 {
  "id": "UI11b-1",
  "where": "quantgen_desktop/app.py:149-162 (Stretch for 7 or fewer headers); bonds.py:51, :53",
  "current": "metrics and krd each span the full pane (1114px ko / 1108px en at 1360). Each column is 552px but the content needs 114/131px (metrics) and 122/144px (krd), so about 75% of each row is blank and the values start mid-table.",
  "proposed": "For the two bond tables only: column 0 ResizeToContents, column 1 Stretch, placed side by side (UI11b-3)",
  "note": "Optional: right-align the numeric column."
 },
 {
  "id": "UI11b-2",
  "where": "bonds.py:51 (min 360), :53 (min 260), :54 (min 310)",
  "current": "metrics: 12 rows need 468px, 3 hidden (Roll-down, Carry + roll, Breakeven). krd: 9 rows need 360px, 3 hidden; the '10' row is cut at the edge. scenarios: 9 rows need 1129px. Hidden rows behind inner scroll bars likely read as clipping or overlap.",
  "proposed": "Fit metrics and krd heights to their rows (468 and 360) with ScrollBarAlwaysOff. Prototype measured vscroll_max = 0 and hscroll_max = 0 at 1360 and 1000 in both languages.",
  "note": "Real widget overlap was not reproduced offscreen."
 },
 {
  "id": "UI11b-3",
  "where": "bonds.py:25-61 (VBox order: form, metrics, ChartStudy, krd, scenarios, hedge, exports)",
  "current": "Vertical stack with the chart and notes between the two tables",
  "proposed": "Order: form panel; a QHBoxLayout (spacing 18) holding [panel '핵심 지표' / 'Key metrics' with metrics] and [panel '만기별 DV01' / 'Key-rate DV01' with krd]; panel '가격-수익률 곡선' / 'Price–yield curve' with ChartStudy; panel '금리 시나리오' / 'Rate scenarios' with scenarios (scenarios tool only); hedge; exports. Measured: each column is 548/545px at 1360 (tables 502/499) and 368/365px at 1000 (tables 322/319), against content needs of 245 (metrics) and 266 (krd). It fits at the 1000px minimum window.",
  "note": "Prototype: proto_bonds_calc_view_*.png and proto_bonds_*_{1360,1000}w_full_*.png. Panel titles need catalog entries (A1)."
 },
 {
  "id": "UI11b-4",
  "where": "Bonds after the side-by-side change (prototype measurement)",
  "current": "With top alignment the krd panel (437px) ends 108px above the metrics panel (545px), leaving new blank space on the right",
  "proposed": "Owner choice. (a) Equal-height panels: no AlignTop, so the bottom edges line up. (b) Put the hedge result (hedge tool) under krd in the right column. SignedBars (charts.py:274-283) is too tall at 34 + 9×28 = 286px.",
  "note": ""
 },
 {
  "id": "UI11b-5",
  "where": "bonds_portfolio_narrative.py:131-135; bonds.py:98-101; core/ficc/curves.py:266-267; core/ficc/data.py:140",
  "current": "'Simulated Treasury par curve (Nelson-Siegel random walk) — no market data provider was used.' shown twice (panel.note and curve.note are the same string)",
  "proposed": "In the display variant, skip curve.note when it equals panel.note. source_text and the export stay the same.",
  "note": "The duplicate appears whenever panel.note is non-empty (synthetic, FRED fallback, missing tenors)."
 },
 {
  "id": "UI11b-6",
  "where": "bonds_portfolio_narrative.py:130-133; bonds.py:99-100 (known issue 7 in docs/product/MARKETS_WATCHLIST_2026-11-04.md:83)",
  "current": "'합성 곡선 · 현재 시장 데이터 아님' / 'SYNTHETIC · 2026-11-04 · bootstrap · 30 거래일' / the provider note",
  "proposed": "Display only '합성 곡선 · 현재 시장 데이터 아님' when synthetic, followed by the narrative. Drop the provider, date, method and session count from the display; the export provenance section (bonds.py:106-107) keeps them.",
  "note": "Follows the PR #71 ruling (no provider or observation-date text in views)"
 },
 {
  "id": "UI11b-7",
  "where": "bonds.py:90",
  "current": "'Shock · bp' cell = str(r.shock_bp), e.g. '{0.25: 0.0, 1.0: 0.0, 2.0: 0.0, 3.0: 1.7857142857142858, ...}' (needs 1375px; very tall rows)",
  "proposed": "Reuse the Flet formatter ui/bonds_page.py:52-56 _shock_text: '+25bp parallel' or '3m +0 / 2y +0 / 5y +5 / 10y +14 / 30y +50' (or move it to core). The export keeps the scenario objects (bonds.py:108).",
  "note": "Display formatting only"
 },
 {
  "id": "GLASS-1",
  "where": "quantgen_desktop/typography.py:27-33 (PANEL_DEPTH), :168-171 (QFrame#panel), app.py:138-146 (panel())",
  "current": "Only the Bonds form uses the raised panel; the tables and the chart sit on the page background with no separation",
  "proposed": "Wrap each Bonds block in the existing panel(title): same gradient, top edge, 2px bottom edge and 14px radius in both themes. No new tokens are needed. If a lighter 'glass' variant is wanted, add a stylesheet-only QFrame#panel[variant='glass'] using the same PANEL_DEPTH values.",
  "note": "QGraphicsDropShadowEffect is banned (typography.py:28-29; test desktop_typography_acceptance.py:325); :345-348 pins the panel gradient and edge colours"
 },
 {
  "id": "GLASS-2",
  "where": "typography.py:166",
  "current": "`QWidget { background: p.bg }` makes a plain QWidget container inside a panel paint a grey box (seen in proto_buildtest)",
  "proposed": "Make a new reading or summary container a QFrame with an object name and a transparent rule, or add its labels directly to the panel layout",
  "note": "ChartStudy (a QWidget subclass) does not paint a background"
 }
]
```

## A3 설명·용어 패널 조사 (UI-12)

UI-12 조사 결과입니다 (읽기 전용, A3 UI-12)

요약 (소유자께)
- 화면 설명이 지저분한 주된 원인은 Native 분석 도구들의 `ToolPane.text()`입니다(quantgen_desktop/tools.py:211-221). 결과 하나에 회색(muted, 14px) 문단을 2~8개씩 쌓습니다. 한국어로 결과 화면 하나에 최대 2,285자(Strategy Lab), 영어로는 최대 3,361자(ETF)입니다. 이 문단들 안에 공급사·관측일 줄, "합성 데이터" 문구 2~3번 반복, 같은 문장이 두 번 나오는 버그, 한국어 화면에 남은 영어 원문(FMP_API_KEY…), 내부 코드("DO-NOT-BUILD TF-12", "P19")가 섞여 있습니다.
- "알아보기" 패널은 지금 코드로 만들 수 있습니다. 화면의 모든 글(QLabel)은 이미 마우스로 선택할 수 있습니다(app.py:107, market_chart.py:371, watchlist.py:77). 앱 전체에 이벤트 필터를 하나 걸면 드래그나 더블클릭으로 고른 글을 잡아낼 수 있고, 시험용 코드로 확인했습니다.
  - 용어 데이터: 32개 용어집(core/education/glossary.py)을 그대로 씁니다. `sections()` 주석에 이미 "term side panel"이 적혀 있습니다(glossary.py:382).
  - 새로 만들 것: 선택한 글에서 용어를 찾는 함수가 필요합니다. 지금 있는 `search()`는 "듀레이션과", "RSI가", "Modified duration 4.2"를 찾지 못하고, "VaR를"은 엉뚱하게 CVaR로 잡습니다.
- AI 호출은 필요 없습니다. 패널은 로컬 용어집과 화면에 이미 표시된 값만 씁니다.
- Flet도 가능합니다. 다만 선택한 위치(좌표)를 알 수 없어서 "알아보기" 버튼을 고정된 자리에 두어야 합니다. 차트 안의 글은 이미지라서 선택할 수 없습니다.

0. 근거와 방법
- 작업 트리: s10은 HEAD 516953a(브랜치 claude/s10-models-20261104)입니다. `git diff faf9f3b HEAD`가 비어 있으므로 내용은 main faf9f3b와 같습니다. probe를 돌린 뒤 `git status`가 비어 있음을 확인했고, s10 안에서 바뀐 파일은 없습니다.
- 실행해서 측정한 프로그램(모두 오프라인 fake, 네트워크 차단, ko·en 각각 실행): /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/ui_a1a3/ui12/probe.py
  - 하는 일: ResearchWindow를 1360x940으로 만들고, 모든 경로와 모든 도구를 test fixture로 실행합니다. 그다음 QLabel마다 생성 위치(file:line), role, 실제 픽셀 크기(QFontInfo), 보이는지, 선택 가능한지, 글자 수를 기록합니다.
  - 결과 파일: …/ui12/out/labels_ko.json (1766건), …/ui12/out/labels_en.json (1825건), …/ui12/out/stock_ko.json, …/ui12/out/profile_ko.json (종목 화면 프로필과 차트 값. 만든 프로그램은 …/ui12/probe_stock.py)
  - 분석 프로그램: …/ui12/analyze.py, …/ui12/flet_scan.py (Flet AST 스캔)
  - 시험용 프로토타입: …/ui12/proto_select.py (선택 감지), …/ui12/proto_match.py (용어 찾기)
  - 다른 sweep이 만든 …/ui_a1a3/out/records.json은 읽기만 했습니다. 표 첫 칸의 항목명을 용어집과 대조하는 데 썼습니다.
- 글자 크기 기준: caption은 12px(typography.py:179-180), 본문 QLabel과 muted는 14px(typography.py:166, 178), 표 머리글은 12px(typography.py:192)입니다. caption 12px은 tests/desktop_typography_acceptance.py:326이 고정하고 있고, 소유자가 승인한 글자 크기 체계입니다(typography.py:1).

1. Native: 지저분한 설명과 작은 글씨 목록 (file:line, role/px, 최대 길이 ko/en)

결과 영역 전체
- tools.py:217 ToolPane.text → muted 14px. 결과 화면 하나에 쌓이는 muted 문단 수와 글자 수(ko)는 아래와 같습니다. en은 대략 1.4~1.8배입니다.

  | 결과 화면 | 문단 수 | 글자 수 (ko) |
  |---|---|---|
  | derivatives | 6 | 1,949 |
  | etf | 6 | 1,929 |
  | crypto | 8 | 1,788 |
  | strategy run | 7 | 2,285 |
  | structuring steep | 6 | 1,347 |
  | fx option | 6 | 1,368 |
  | macro weekly | 8 | 1,292 |
  | rates curve | 4 | 908 |

  내보내기(export)는 tools.py:215-216의 self.sections에서 만들어집니다. 그래서 화면 배치만 바꾸면 내보내기 원문은 그대로 남습니다.

- 공급사·관측일 줄(provenance)이 있는 곳: rates.py:59-60, 118 / structuring.py:40-42 / bonds.py:98-101(notes는 bonds.py:56에서 만든 label) / fx.py:37 / macro.py:45, 48, 50 / market_tools.py:44-47, 125-127, 196-198, 261 / signals.py:30 / strategy.py:45-48 / portfolio.py:75-78 / app.py:909-910(Monte Carlo).
- 같은 문장이 두 번 나오는 버그: p.note와 c.note가 같은 문장 "Simulated Treasury par curve (Nelson-Siegel random walk) — no market data provider was used."라서 두 번 연달아 출력됩니다. rates.py:60, structuring.py:40, bonds.py:98-101입니다. probe에서 rates(curve·swap·option·sim), structuring 4개 도구, bonds 모두 한 문단 안에 같은 줄이 두 번 있음을 확인했습니다.
- "합성 데이터"를 여러 번 말하는 곳:
  - macro.py:45, 48, 50: "기준일 … · SYNTHETIC: 18" / "합성 데이터 포함: DGS2 … GC=F" / "18개 중 18개 지표가 합성(SYNTHETIC)입니다: …"로 세 번입니다.
  - market_tools.py:44+46, 125+127, 196+198: 두 번씩입니다.
  - app.py:909-910: "합성 데이터 · SYNTHETIC"과 h.note "FMP_API_KEY is not configured; …"입니다.
- 모든 결과 위에 붙는 caption: tools.py:249-251, caption 12px, 32자/66자, "분석 해설 · 선택 언어로 표시하며 내보내기에는 원문 유지". 상태 줄 tools.py:257(muted 42자/123자)은 모든 도구에서 같은 문장입니다.

Build & Test (UI-9와 겹침)
- app.py:909-930 → quant_notes(app.py:573, muted 14px): 한국어 화면에서 1,238자, 13줄입니다. 대부분 영어로 남아 있습니다: "FMP_API_KEY is not configured; Simulated series (GBM, μ=13%, σ=36%) — no market data provider was used.", "rf 3.00% assumed · FRED unavailable", "GARCH fit: alpha=…", "converged=… · persistence=… · half-life=…", "at_bound: …", "alpha 95% Wald interval: …".
- app.py:576: caption 60자/127자.
- Strategy Lab 입력란 위 caption: strategy.py:19(101자/190자), strategy.py:21(EXPOSURE_HELP, 158자/286자). 둘 다 12px이고 항상 보입니다.

Markets 종목 화면
- market_chart.py:335 indicator_help(1068에서 채움): 14px, 지표 5개를 다 켜면 402자/659자입니다. 같은 지표 설명이 market_chart.py:377-390 `_indicator_explanation`에 따로 있어서 용어집·ui_messages와 설명이 두 군데입니다.
- market_chart.py:336 guide: 237자/462자, "차트 읽는 법 ?" 토글 뒤에 숨어 있습니다.
- market_chart.py:331 chart_help: muted 39자/79자.
- market_chart.py:351 limitations: 95자/165자, 항상 보입니다.
- market_chart.py:283 availability: 90자/204자, "데이터 설명" 접힘 안에 있습니다.
- market_chart.py:334 feed_notice.
- indicator_reading(market_chart.py:1150-1154)에 "밴드 위: 71,211.325626 · 밴드 아래: 70,980.674374"처럼 소수점 6자리가 나옵니다. 같은 값이 프로필에는 "71,211 KRW"로 나옵니다.
- markets_view.py:725 프로필 note(caption 12px) 문구: "참고용 · v2 신호 아님 (DO-NOT-BUILD TF-12). 거래 원장에 연결되지 않습니다. 매수·매도 추천이 아닙니다." 출처는 core/research/stock_profile.py:673-674, 1072입니다.
- "제공되지 않는 정보" 섹션(stock_profile.py:642, 1086): "제공되지 않음"이나 "자료가 전달되지 않았습니다" 줄이 9개 있습니다.
- 행 이름(markets_view.py:737)은 muted 14px이고, 출처·시각은 툴팁에만 있습니다. PR #71 결정대로입니다.

Home
- app.py:360: caption 12px "이번 세션의 Monte Carlo · 투자 판정과 별개"가 카드 3개에 똑같이 붙습니다.
- app.py:375: caption 55자/109자 "P5–P95는 …".
- watchlist.py:779-781 안내문: 72자, 14px.

Library
- app.py:613: caption 12px, 90자/165자, 상태 코드가 원문 그대로입니다("재현성 PARTIAL · … 비용 NOT_APPLIED · 검증 NOT_RUN").
- app.py:611: muted 54자.

System
- app.py:671: 112자/182자.
- app.py:672: muted 85자/120자(NOT_VERIFIED, NOT_FROZEN…).
- app.py:675: 이전 현황 291자/446자.
- app.py:676: 45자/78자.
- data_rights.py:24 법률 caption: 12px, 208자/371자, URL이 그대로 노출됩니다.
- data_rights.py:29 intro: 105자/243자.

Portfolio
- portfolio.py:39 scope: caption 12px, 184자/329자.
- portfolio.py:46: caption 89자/168자.
- portfolio.py:45 notes: muted 724자/1,123자, 종목마다 "ONE: SYNTHETIC · 2026-01-01 → 2026-04-30 · …" 줄이 들어갑니다.

그 밖
- ETF 입력 caption market_tools.py:110-112: 12px, 112자/205자.
- Indicator guide의 작은 caption 7개: indicator_guide.py:116, 167, 168, 179, 180, 183, 188. 168은 "Federal Reserve Board H.10, DEXUSEU 역산·반올림 표본"을 포함합니다. 길이는 36~102자(ko), 82~180자(en)입니다.
- bonds.py:48: 한국어와 영어가 섞임("Price를 입력할 때는 Yield를 비웁니다").

선택 가능 여부
- 측정한 서로 다른 label 467개 중 448개가 마우스로 선택됩니다(TextSelectableByMouse).
- 선택이 안 되는 19개는 Paper·Rules 폼의 QFormLayout 행 제목입니다(paper.py:172).

2. Native "알아보기" 용어 패널 설계

2a. 선택한 글 감지
- 선택·드래그(주 방식): label 생성 함수 3곳이 모두 TextSelectableByMouse를 켭니다(app.py:107, market_chart.py:371, watchlist.py:77).
  - QApplication에 이벤트 필터를 하나 걸면(또는 wheel_guard처럼 LanguageController 순회에서 위젯마다 붙이면, localization.py:84-87) MouseButtonRelease 시점에 선택이 이미 잡혀 있습니다. proto_select.py에서 확인했고 결과는 '수정 듀레이션'이었습니다.
  - 더블클릭하면 띄어쓰기 단위로 선택되어 조사가 붙습니다('듀레이션과', 확인함).
  - 버튼 형태: 마우스를 놓은 자리에 작은 "알아보기" 버튼(칩)을 띄우고 포커스는 가져오지 않습니다. 다음 클릭, 스크롤, Esc에서 사라집니다.
- 오른쪽 클릭: QLabel에는 공개된 createStandardContextMenu가 없습니다. 그래서 "복사 / 모두 선택 / 알아보기: <용어>" 메뉴를 직접 만들어야 합니다.
  - 표(QTableWidget): viewport의 ContextMenu 이벤트가 필터에 들어오고, 키보드로 연 경우(reason=Keyboard)도 확인했습니다. 현재 셀을 기준으로 찾습니다. 지역화된 Metric 열은 영어 원문(CAPTION_ROLE, app.py:162-163, localization.py:123-127)으로 대조합니다.
- 마우스 올리기(hover): 1단계에서는 권하지 않습니다. label은 PlainText(app.py:104)이고, RichText 링크로 바꾸면 공급사에서 온 문자열을 escape해야 합니다.
- 키보드: label은 마우스로만 선택되고 focusPolicy는 ClickFocus입니다(확인함). quantgen_desktop에는 지금 QShortcut이나 QKeySequence가 없습니다.
  - 제안: F1로 패널을 엽니다. 검색창이 열리고, 선택한 글이나 현재 표 셀의 용어가 미리 들어가 있습니다.
  - Esc로 닫고 원래 포커스로 돌아갑니다. 표에서는 Shift+F10이나 메뉴 키로 같은 메뉴가 열립니다.
  - 패널과 각 섹션에 accessible name을 붙입니다. 화면낭독기 사용자는 F1 경로를 씁니다(떠 있는 칩은 화면낭독기가 읽지 못합니다).

2b. 선택한 글에서 용어 찾기
- glossary.search(glossary.py:421)는 입력 앞부분을 이름과 맞추는 방식이라 선택한 글에는 맞지 않습니다. 확인 결과:
  - '듀레이션과', '변동성은', 'RSI가', 'Modified duration 4.2', '볼린저 밴드에', 'GARCH(1,1)-t' → 결과 없음
  - 'VaR를' → ('cvar',) (틀림)
- 새 함수 terms_in(text, scope)를 만들어야 합니다. 조사(과·와·은·는·이·가·을·를·의·에·로·으로 …)를 떼고, 가장 긴 별칭부터 맞추고, 영어는 단어 경계로 자릅니다. 애매한 별칭(forward, curve, 1bp, 밴드, 봉, IV, vol, MA, ES, bootstrap)은 화면 범위(scope)를 함께 봅니다.
- proto_match.py로 14개 문장을 시험했습니다:
  - 맞게 찾은 것: '1일 VaR 95%'→var, '1일 CVaR 95%'→cvar, '볼린저 상단 (20, 2σ)'→bb, 'Modified duration 4.2'→duration, 'GARCH(1,1)-t'→garch, '연간 변동성'→volatility, '듀레이션과'→duration
  - 'Delta · per +1bp'(rates)는 greeks와 dv01 두 개가 나옵니다. 둘 다 보여 주면 됩니다.
  - 'Block bootstrap'은 의도대로 막혔습니다. 용어집의 bootstrap은 금리 곡선 부트스트래핑이라 Monte Carlo 모델과 다른 개념입니다.

2c. 기존 용어 데이터 (32개, PR #64 커밋 7de46d4)
- core/education/glossary.py의 TERMS(36-345)는 아래 범주로 나뉩니다:
  - 지표 5: sma, ema, rsi, macd, bb
  - 시장 3: candlestick, volume, quote_delay
  - 위험 7: volatility, mdd, var, cvar, sharpe, beta, correlation
  - 모형 4: monte_carlo, percentile_band, garch, backtest
  - 금리 6: yield_curve, bootstrap, duration, convexity, dv01, swap_rate
  - 파생 4: greeks, implied_vol, sabr, protected_note
  - 외환 2: fx_forward, carry
  - 앱 1: q_score
- 패널에 바로 쓸 수 있는 함수: name/category/summary/sections(363-389). sections는 지표면 (의미, 보는 법, 해석, 한계), 그 밖은 (의미, 쓰임, 한계)를 돌려줍니다. 한국어 소제목은 '무엇을 나타내나요?', '어디에 쓰나요?', '해석의 한계'입니다.
- 화면 배치는 IndicatorGuide._render_detail(indicator_guide.py:353-370)을 다시 쓸 수 있습니다. "가이드에서 자세히"는 navigate('guide')와 indicator_guide.choose(key)(indicator_guide.py:258)로 연결합니다.
- 기존 Q-SCORE 도움말(watchlist.py:386-412의 "?" 버튼, ScoreHelpDialog 599, q_score_help는 core/research/qscore.py:38)과 market_chart._indicator_explanation은 같은 설명을 두 번째로 갖고 있습니다. 한 곳으로 합쳐야 합니다.

2d. 용어집에 없는 용어 (표 항목명에는 나오는데 해당 용어가 없음)
- 채권: z-spread, roll-down, breakeven, YTM
- 금리: 2s10s·5s30s 같은 금리차, butterfly, 선도금리 1y1y·5y5y(지금은 별칭 'forward'가 fx_forward로 연결됨), annuity, par rate, Nelson-Siegel, PCA의 level·slope·curvature, mean-reversion의 kappa·half-life, swaption, cap/floor, Bachelier·Black
- 외환: ATM, 25d risk reversal, rho, 통화 베이시스
- 파생: basis, box rate, implied funding, butterfly arbitrage, SVI, RND
- 가상자산: kimchi premium, funding rate, AR(1) half-life, ADF
- 신호·전략: momentum, 승률, PBO, IS/OOS, walk-forward, deflated Sharpe(sharpe와 다른 개념)
- 구조화: DCD, CMS, leverage, enhanced yield, 할인채
- 포트폴리오: efficient frontier, risk parity, equal weight, max Sharpe, 위험 기여도
- Monte Carlo: P(loss), ERP, drift, GBM, jump, block bootstrap, Student-t
- 종목 화면: 52주 범위, 공매도 비중, 투자자별 순매수, PER·EPS·시가총액
- 표 항목명 403개 중 86개만 용어와 이어졌고 317개는 이어지지 않았습니다. 다만 이어지지 않은 317개에는 종목·코드명도 섞여 있습니다.

2e. "현재 차트에서의 의미"에 쓸 수 있는 값 (새로 계산하지 않고 이미 표시된 값만 인용)
- Markets 차트: snapshot, _cursor, indicator_series(snapshot)의 커서 위치 값(market_chart.py:1150-1154). 지표에는 core/education/chart.py:143-163 reading_text의 기존 문장('reading_rsi_high' 등)을 다시 씁니다.
- 종목 프로필: StockView.profile의 섹션과 행(label/value/hint)(markets_view.py:885-893, ProfileRow는 stock_profile.py:79). 공급사가 들어 있는 hint는 다시 보여 주지 않습니다(PR #71 결정).
- Indicator guide: series, keys, cursor, reading_text/cursor_text(indicator_guide.py:372-377).
- Monte Carlo: self.outputs[run_id].result(p05·p95·prob_loss·var_pct·cvar_pct, garch)와 quant_metrics 표(app.py:893-905).
- Bonds: o.analytics(modified·macaulay·convexity·dv01·krd·carry_roll)와 metrics 표(bonds.py:81-87), exports.report.
- Portfolio: chart.output, exports.report(portfolio.py:64-99).
- 그 밖의 ToolPane: self.sections(table/line/bars/text)와 bind_output 뒤의 self.report(tools.py:205-245, 259-266).
- Home: all_q_scores()(app.py:762-770).
- 공통 방안: 지금 보고 있는 화면의 표에서 첫 칸 원문(CAPTION_ROLE)이 그 용어의 별칭과 맞는 행을 찾아 "현재 결과: <항목> = <값>"으로 보여 줍니다. 화면별 provider는 그 위에 덧붙입니다.
- 용어별 해석 문장(예: "수정 듀레이션 4.21 → 금리 1%p 상승 시 약 4.2% 하락")은 새로 쓰는 글이고 숫자 재진술도 들어갑니다. 2단계로 미루고 소유자 검토를 받아야 합니다.

2f. AI 호출
- 필요 없습니다. 패널은 로컬에서만 동작합니다.
- 기존 동의 절차: 결과 선택 → 미리보기 → 동의 체크 → 전송이고, 질문을 고치면 동의가 풀립니다(commentary.py:69-73, 107-125). commentary_payload는 완료된 계산 보고서만 받습니다(ALLOWED, commentary.py:21-38).
- "AI에게 더 묻기"를 넣는다면 Library 해설 패널로 질문을 넘겨주기만 하고 패널에서는 아무것도 보내지 않습니다. 이 경우 소유자 결정이 필요합니다.

2g. 패널 위치
- ResearchWindow는 QMainWindow입니다(app.py:184). 오른쪽 QDockWidget이나 320~360px 열로 둡니다.
- 최소 창 1000px(app.py:224)에서 사이드바 168~208px(typography.py:39)를 빼면 내용 폭은 약 800px이고, ChartStudy breakpoint 820(chart_study.py:7) 때문에 이미 세로로 쌓입니다. 패널이 내용을 밀면 폼이 잘릴 수 있습니다(UI-6a, UI-18 위험).
- 그래서 1280px보다 좁으면 내용 위에 겹쳐 띄우고, 넓으면 옆에 붙입니다.

3. Flet (ui/)
- 작은 글씨: ft.Text 호출 235개 중 159개가 12px 이하입니다(12px 77, 11px 70, 10px 12). selectable=을 넘기는 호출은 55개뿐입니다.
  - 10px: components.py:127, portfolio_page.py:55-57, 166-170, signals_page.py:85, 90, trading_page.py:202, macro_state_panel.py:224
  - 그 밖: research_home.py:173-178의 _text(…,10/11)
- 공급사 안내가 아직 화면에 나옵니다:
  - market_chart_page.py:104, 539-545(11px, "출처 … · 마지막 봉 … · 시세 시각 … · 수신 …")
  - research_home.py:173, 178(10px, "provider · 관측일")
  - krx_page.py:71(11px, "Source: …")
  - rates_page.py:90-91의 출처 칩(125, 183, 239, 275, 330-331에서 사용)
  - quant_lab_page.py:237, 340, 354(11px 노트)
  - settings_page.py:60, 94, 123
  - README.md:896에 "The Flet browser is unchanged"라고 적혀 있습니다.
- AI 안내: ai_panel.py:91, 96(11px)이고, 미리보기나 동의 체크 없이 버튼을 누르면 바로 보냅니다(ai_panel.py:57-75). 그래서 Flet 용어 패널에는 AI 경로를 넣지 않아야 합니다.
- 선택 감지 API: flet 0.85.2(requirements.txt:1)에서 ft.Text(selectable=True, on_selection_change=…)가 TextSelectionChangeEvent.selected_text를 줍니다(확인함).
  - SelectionArea.on_change에는 선택한 글이 들어 있지 않습니다(소스 확인).
  - 선택 위치는 오프셋만 있고 화면 좌표가 없습니다. 그래서 "알아보기"는 고정 위치 버튼으로 둡니다.
  - translate_controls(ui/localization.py:6-33)가 매번 update 전에 모든 컨트롤을 돌므로, 여기서 prose Text에 selectable과 handler를 붙일 수 있습니다. 숫자 데이터(data={'numeric':True})는 건너뜁니다.
- 오른쪽 클릭: ft.ContextMenu가 있지만, 웹에서는 page.browser_context_menu.disable()을 해야 해서 브라우저의 복사 메뉴가 사라집니다(Flet 문서 확인).
- 패널 위치: LocalizedRoot 행(main.py:308-311)의 오른쪽 열, 또는 page.end_drawer/show_end_drawer(있는 것 확인함)입니다.
- 현재 값: 19개 analysis_panel(…, payload_fn) 호출(ai_panel.py:44)에서 payload_fn을 page에 등록해 두면 됩니다. filter_analysis_fields로 이미 걸러진 데이터를 로컬에서만 읽습니다.
- 차트: fcharts의 matplotlib 차트와 market_chart_page.py:114, 516의 SVG는 이미지입니다. 그래서 "이 차트의 용어" 칩을 따로 둡니다.
- 단축키: page.on_keyboard_event가 있고(확인함) 지금은 쓰는 곳이 없습니다.
- Flet 지표 가이드(ui/indicator_guide.py:8-9)는 지금 용어집을 쓰지 않습니다.

4. 바꿀 때 지킬 제약
- 테스트가 고정한 문자열:
  - tests/macro_ui_views.py:295 (Flet SIGNALS_NOTICE의 "DO-NOT-BUILD TF-12")
  - tests/ficc_acceptance.py:654 (daily 보고서의 "P19")
  - tests/desktop_macro_language_acceptance.py:34
  - tests/desktop_typography_acceptance.py:326 (caption 12px)
- 따라서 화면 표시층(번역 catalog나 presentation)에서만 바꾸고, core 문자열과 export는 그대로 둡니다.
- 겹치는 작업: UI-9(Build & Test 오른쪽 설명, app.py:909-930)와 UI-10(표준 용어집)입니다. 용어집 하나(core/education/glossary.py)에 표준 한국어 이름을 두고 UI-10과 함께 쓰기를 권합니다.

### 확인하지 못한 것

- Flet의 실제 동작은 실행해 보지 않았습니다. 확인한 것은 flet 0.85.2의 API와 소스뿐입니다. 아래는 확인하지 않았습니다.
  - on_selection_change가 드래그 중 얼마나 자주 발생하는지, 데스크톱 클라이언트와 웹에서 다르게 동작하는지
  - NavigationDrawer에 임의의 컨트롤을 넣을 수 있는지
  - ContextMenu가 데스크톱 클라이언트에서 어떻게 동작하는지
  - 소유자가 Flet을 브라우저(--web)로 쓰는지, 기본 데스크톱 뷰로 쓰는지(main.py:343은 view를 지정하지 않은 ft.run)
- PR #71의 '공급사·관측일 미표시' 결정이 Flet과 분석 결과 본문까지 해당하는지는 확인하지 않았습니다(README.md:896에는 Flet이 바뀌지 않았다고 적혀 있습니다).
- 측정은 Linux offscreen, QT_SCALE_FACTOR=1, 번들 폰트로만 했습니다. 아래는 확인하지 않았습니다.
  - Windows에서 칩 위치, DPI 125·150%, QDockWidget 스타일, 겹침 패널이 어떻게 보이는지
  - Narrator 같은 화면낭독기 동작
- 글자 수는 fixture와 합성 데이터 기준입니다. 실제 KIS·FMP·FRED 데이터에서는 문구와 길이가 다릅니다. 프로필의 '제공되지 않는 정보' 9행은 fixture에 수급·공매도·재무 자료가 없어서 나온 결과입니다.
- Signals 결과의 muted 문단은 probe에서 탭이 숨겨져 있어 측정되지 않았습니다. signals.py:27, 30은 코드만 읽었습니다.
- 용어 찾기 프로토타입(proto_match.py)은 14개 문장으로만 시험했습니다. 조사 목록이 충분한지, 전체 화면 문구에서 정확도가 어떤지는 확인하지 않았습니다.
- 테스트가 고정한 문자열은 TF-12, P19, '원문 유지', FMP_API_KEY, caption 12px만 grep했습니다. 제안한 다른 문구 변경이 걸리는 테스트가 더 있는지는 확인하지 않았습니다(tests/run_all.py는 금지라 실행하지 않았습니다).
- '해설 패널로 넘기기'(T-07)와 패널 레이아웃(T-05)은 설계안일 뿐 만들어 보지 않았습니다. 선택 감지와 표 메뉴 이벤트는 scratch 프로토타입으로만 확인했습니다.
- UI-9와 UI-10을 다른 sweep이 어떻게 제안하는지는 보지 않았습니다. 겹치는 항목은 N-05, N-14, N-22, T-08입니다.

### 항목 목록 (40개)

```json
[
 {
  "id": "N-01",
  "where": "quantgen_desktop/tools.py:211-221 (ToolPane.text → label muted 14px at :217); all FICC/market panes",
  "current": "결과마다 muted 문단 2~8개가 세로로 쌓임. 측정(ko): derivatives 6개/1,949자, etf 6/1,929, crypto 8/1,788, strategy run 7/2,285; en 최대 3,361자(etf)",
  "proposed": "3단으로 나눕니다: ① 상태 칩 한 줄(예: \"합성 데이터 · 실제 시장 데이터 아님\") ② 해설은 오른쪽 읽기 열 ③ \"출처·가정 보기\" 접힘 섹션(기본은 접힘)에 provenance·관례 문단을 넣습니다. text()에 kind='provenance' 같은 표시를 붙여 놓을 자리만 바꿉니다.",
  "note": "export는 그대로입니다. text()가 표시 전에 self.sections에 먼저 넣기 때문입니다(tools.py:215-216)."
 },
 {
  "id": "N-02",
  "where": "rates.py:59-60,118; structuring.py:40-42; bonds.py:98-101; fx.py:37; macro.py:45; market_tools.py:44,125,196,261; signals.py:30; strategy.py:45-48; portfolio.py:75-78; app.py:909",
  "current": "\"SYNTHETIC · 2026-11-04 · 80 observations · bootstrap ⏎ Simulated Treasury par curve (Nelson-Siegel random walk) — no market data provider was used.\" / \"069500 · SYNTHETIC · 2024-11-29 → 2026-11-04\" / \"Provider: KIS\" 같은 공급사·관측일·관측 수 줄",
  "proposed": "화면 본문에서 빼서 N-01의 \"출처·가정 보기\" 접힘으로 옮깁니다. 실제 데이터일 때는 칩도 두지 않고, 합성이거나 지연·일부 이력일 때만 칩 하나를 둡니다.",
  "note": "PR #71의 '라이브 화면에는 공급사·관측일 열을 두지 않는다'는 결정을 분석 결과 본문까지 넓히는 것입니다. 소유자 확인이 필요합니다. export와 툴팁은 그대로 둡니다."
 },
 {
  "id": "N-03",
  "where": "rates.py:60; structuring.py:40; bonds.py:98-101",
  "current": "p.note와 c.note가 같아서 \"Simulated Treasury par curve (Nelson-Siegel random walk) — no market data provider was used.\"가 한 문단 안에 두 번 나옴(probe에서 rates 4개 도구, structuring 4개, bonds 모두 확인)",
  "proposed": "표시할 때 같은 줄을 한 번만 보여 줍니다(dict.fromkeys). 예: \"합성 곡선 · 실제 시장 데이터 아님\" 한 줄",
  "note": "원문 export를 바꿀지는 소유자 결정입니다. 기본안은 표시만 정리하는 것입니다."
 },
 {
  "id": "N-04",
  "where": "macro.py:45,48,50; market_tools.py:44+46,125+127,196+198; app.py:909-910",
  "current": "macro: \"기준일 2026-11-04 · SYNTHETIC: 18\" + \"합성 데이터 포함: DGS2, DGS10, … GC=F\" + \"18개 중 18개 지표가 합성(SYNTHETIC)입니다: …\"(3번 반복). derivatives: \"synthetic · 만기 DEMO …\" + \"SYNTHETIC · 모든 시세는 합성 데이터입니다.\"",
  "proposed": "칩 하나만 둡니다: \"합성 데이터 · 실제 시장 데이터 아님\". 계열 ID 목록은 접힘 섹션으로 옮깁니다.",
  "note": "합성 여부 표시는 숨기면 안 되는 경고이므로 칩 한 개는 반드시 남깁니다."
 },
 {
  "id": "N-05",
  "where": "quantgen_desktop/app.py:909-930 → quant_notes label app.py:573 (muted 14px); Build & Test 오른쪽 열",
  "current": "한국어 화면에서 1,238자, 13줄이고 대부분 영어: \"FMP_API_KEY is not configured; Simulated series (GBM, μ=13%, σ=36%) — no market data provider was used.\" / \"rf 3.00% assumed · FRED unavailable\" / \"GARCH fit: alpha=…\" / \"converged=True · persistence=… · half-life=…\" / \"alpha 95% Wald interval: …\"",
  "proposed": "요약 3줄: \"데이터: 합성 시계열(시장 데이터 공급사 미연결)\" / \"무위험금리: 3.00% 가정\" / \"모형: GARCH(1,1)-t · 수렴\". GARCH 진단과 구간은 \"모형 진단\" 접힘 섹션으로 옮기고, 환경 변수 이름은 System > 연결에서만 보여 줍니다.",
  "note": "UI-9 담당 영역과 겹칩니다. 숫자는 바꾸지 않습니다."
 },
 {
  "id": "N-06",
  "where": "quantgen_desktop/tools.py:249-251 (caption 12px)",
  "current": "\"분석 해설 · 선택 언어로 표시하며 내보내기에는 원문 유지\" / \"Analysis narrative · display language; original retained in export\"가 모든 결과 위에 붙음",
  "proposed": "화면에서 지웁니다. 같은 뜻은 저장 버튼 툴팁으로 옮깁니다: \"원문은 내보내기 파일에 그대로 보관됩니다\"",
  "note": "번역 쌍은 translations.py:566, 571에 있습니다."
 },
 {
  "id": "N-07",
  "where": "quantgen_desktop/tools.py:257 (status, muted)",
  "current": "\"계산 완료 · 출처·관측일·가정을 확인하세요. 공식 검증 판정은 별도입니다.\"(모든 도구에서 같은 문장)",
  "proposed": "\"계산 완료\" 옆에 칩 \"공식 판정 아님\"을 둡니다. 출처는 N-01의 접힘 섹션이 대신합니다.",
  "note": ""
 },
 {
  "id": "N-08",
  "where": "quantgen_desktop/market_chart.py:335 (filled at :1068), explanations at :377-390",
  "current": "선택한 지표 설명을 이어 붙인 문단. 지표 5개면 402자/659자(14px). 같은 내용이 용어집(ui_messages)에도 따로 있음",
  "proposed": "이 문단을 없앱니다. 지표 버튼 툴팁은 남기고, 지표 이름을 선택하거나 버튼의 \"?\"를 누르면 알아보기 패널이 커서 위치의 값과 함께 열립니다.",
  "note": "설명 출처를 하나로 합칩니다. 키 이름도 'bollinger'(차트)와 'bb'(용어집)로 다르므로 대응표가 필요합니다."
 },
 {
  "id": "N-09",
  "where": "market_chart.py:351 (limitations), :331 (chart_help), :336 (guide), :283 (availability), :334 (feed_notice)",
  "current": "limitations 95자/165자가 항상 보임: \"체결 수신은 장 운영과 이용 권한에 따라 달라집니다. 해외 시세는 지연될 수 있어요. …\"",
  "proposed": "chart_help 한 줄만 남기고, limitations는 \"데이터 설명 · 수신 설정\" 접힘(market_chart.py:256-307) 안으로 옮깁니다. 지연이나 공백은 경고 칩으로 그대로 보여 줍니다.",
  "note": ""
 },
 {
  "id": "N-10",
  "where": "quantgen_desktop/market_chart.py:1150-1154 (indicator_reading)",
  "current": "\"밴드 위: 71,211.325626 · 밴드 아래: 70,980.674374\"(프로필에는 같은 값이 \"71,211 KRW\")",
  "proposed": "SMA·EMA와 같은 자릿수로 보여 줍니다: \"밴드 위: 71,211 · 밴드 아래: 70,981\"",
  "note": "표시 반올림만 바뀝니다. 값과 export는 그대로입니다. 소유자 확인을 권합니다."
 },
 {
  "id": "N-11",
  "where": "core/research/stock_profile.py:673-674,1072 → markets_view.py:725 (caption 12px); quantgen_desktop/signals.py:15,27; translations.py:381",
  "current": "\"참고용 · v2 신호 아님 (DO-NOT-BUILD TF-12). 거래 원장에 연결되지 않습니다. 매수·매도 추천이 아닙니다.\"",
  "proposed": "\"참고용 지표이며 매수·매도 추천이 아닙니다.\"",
  "note": "내부 코드를 화면에서 빼는 것입니다. tests/macro_ui_views.py:295가 Flet 문구를 고정하므로 표시층에서만 바꾸고, core 원문과 export는 그대로 둡니다."
 },
 {
  "id": "N-12",
  "where": "core/research/stock_profile.py:642,1086 (\"제공되지 않는 정보\" 섹션)",
  "current": "\"제공되지 않음\"이나 \"자료가 전달되지 않았습니다\" 행 9개(뉴스, 애널리스트 의견, 배당, 호가, 재무 지표 …)",
  "proposed": "한 줄로 줄입니다: \"이 화면에서 제공하지 않는 항목: 뉴스·애널리스트 의견·배당·호가·재무 지표\"(펼치면 자세히)",
  "note": "README.md:884-885에 적힌 기능 설명과 맞춰야 합니다."
 },
 {
  "id": "N-13",
  "where": "quantgen_desktop/app.py:358-362 (caption ×3), app.py:375",
  "current": "카드 3개 밑에 \"이번 세션의 Monte Carlo · 투자 판정과 별개\"가 세 번. \"P5–P95는 시뮬레이션 분포의 중앙 90% 구간입니다. 수익 보장이나 95% 신뢰구간이 아닙니다.\"",
  "proposed": "카드 줄 밑에 한 번만: \"이번 세션 Monte Carlo 실행 수 · 투자 판정 아님\". 두 번째 문장은 \"P5–P95: 시뮬레이션 중앙 90% 구간\"으로 줄이고, 'P5–P95'를 선택하면 percentile_band 용어가 열립니다.",
  "note": ""
 },
 {
  "id": "N-14",
  "where": "quantgen_desktop/app.py:613 (caption 12px)",
  "current": "\"재현성 PARTIAL · 데이터 빈티지/라이선스 미검증 · 비용 NOT_APPLIED · 검증 NOT_RUN ⏎ 동결 연구·과거 원장·비밀 설정을 탐색하지 않습니다.\"",
  "proposed": "칩 4개: \"재현성 일부\" \"데이터 권리 미검증\" \"비용 미반영\" \"검증 미실행\". 두 번째 줄은 System으로 옮깁니다.",
  "note": "상태 코드 번역은 A1(UI-2)과 같은 용어집을 씁니다. export의 원래 코드는 그대로 둡니다."
 },
 {
  "id": "N-15",
  "where": "quantgen_desktop/app.py:669-676 (System)",
  "current": "\"기록된 검사: 749 PASS / 0 FAIL / 121 NOT_RUN …\", \"데이터 NOT_VERIFIED · 공식 게이트 NOT_FROZEN (문서 기록) …\", 이전 현황 291자/446자 \"PyQt6 네이티브: Home, Markets(…)…\"",
  "proposed": "\"개발 정보\" 접힘 섹션 하나로 묶습니다. 기본 화면에는 \"이 데스크톱은 미리보기 버전입니다\" 한 줄만 둡니다.",
  "note": "개발자용 정보입니다."
 },
 {
  "id": "N-16",
  "where": "quantgen_desktop/data_rights.py:24 (legal caption 12px), :29 (intro)",
  "current": "208자/371자 법률 안내가 12px이고 URL \"https://www.fsc.go.kr/no010101/82887\"이 그대로 보임",
  "proposed": "본문 14px로 3문장 이내로 줄이고, URL은 \"근거 보기\" 링크 버튼으로 바꿉니다.",
  "note": "법률 문구는 뜻을 바꾸지 말고 배치만 바꿉니다."
 },
 {
  "id": "N-17",
  "where": "quantgen_desktop/strategy.py:19-21 (caption 12px, 항상 보임)",
  "current": "101자/190자 \"실데이터 실행은 기존 연구 원장에 시행을 기록합니다. … 누적 원장 기반 전환은 별도 작업입니다.\" + 158자/286자 EXPOSURE_HELP",
  "proposed": "한 줄로 줄이고(\"실데이터 실행만 연구 원장에 기록됩니다\"), 나머지는 \"규칙·노출 설명\" 접힘 섹션으로 옮깁니다. DSR과 총노출은 용어집에 추가합니다.",
  "note": "'누적 원장 기반 전환은 별도 작업입니다'는 내부 진행 상황이라 사용자 화면에서 뺍니다."
 },
 {
  "id": "N-18",
  "where": "quantgen_desktop/portfolio.py:39 (scope caption), :46 (caption), :45 (notes, from :75-78)",
  "current": "scope 184자/329자(12px), 면책 89자/168자(12px), notes 724자/1,123자(종목마다 \"ONE: SYNTHETIC · 2026-01-01 → 2026-04-30 · Deterministic test fixture\")",
  "proposed": "scope는 \"선택한 목적에만 종목당 상한 적용 · 롱온리·완전투자\" 한 줄로 줄이고, 종목별 출처는 접힘 섹션으로 옮깁니다.",
  "note": ""
 },
 {
  "id": "N-19",
  "where": "quantgen_desktop/market_tools.py:110-112 (ETF 입력 caption 12px)",
  "current": "\"LETF 전용: 금리 0 비교 기준에서는 금리 입력란을 비워 두세요. 시나리오에는 조달금리와 보수가 필요하며, …\"(112자/205자)",
  "proposed": "입력란마다 툴팁으로 나눕니다(조달금리, 보수, 배당수익률). 화면에는 \"입력값은 가정이며 실제 펀드 비용이 아닙니다\" 한 줄만 둡니다.",
  "note": ""
 },
 {
  "id": "N-20",
  "where": "quantgen_desktop/indicator_guide.py:116,167,168,179,180,183,188 (caption 12px ×6, muted ×1)",
  "current": "\"과거 기준환율 · 실시간 아님 · Federal Reserve Board H.10, DEXUSEU 역산·반올림 표본 ⏎ USD/EUR · 2019. 9. 3. → 2020. 12. 31.\" + \"이 표본은 일별 기준환율입니다. 실제 시가·고가·저가·거래량이 없어 …\" 등",
  "proposed": "168과 179를 합칩니다: \"표본: USD/EUR 일별 기준환율(2019.9–2020.12) · 캔들·거래량 없음\". 183과 188을 합칩니다: \"교육용 과거 사례 · 전략 검증이나 매매 권고가 아닙니다\"",
  "note": "가이드는 학습용 화면이라 설명이 많은 편이어도 괜찮지만, 공급사 이름은 툴팁으로 옮깁니다."
 },
 {
  "id": "N-21",
  "where": "quantgen_desktop/typography.py:179-180 (caption 12px); tests/desktop_typography_acceptance.py:326",
  "current": "60자 넘는 설명 문장도 caption(12px)으로 표시함(N-14, N-16, N-17, N-18, N-19, N-20)",
  "proposed": "글자 크기 체계는 그대로 둡니다. caption은 입력란 이름과 짧은 메타데이터(60자 미만)에만 쓰고, 긴 문장은 14px 본문으로 접힘 섹션 안에 둡니다.",
  "note": "caption을 13px로 키우려면 소유자가 승인한 글자 크기 체계를 바꾸고 테스트도 고쳐야 하므로 소유자 결정이 필요합니다."
 },
 {
  "id": "N-22",
  "where": "quantgen_desktop/bonds.py:48 (caption 12px)",
  "current": "\"가격과 수익률 중 하나만 입력하세요. Price를 입력할 때는 Yield를 비웁니다.\"",
  "proposed": "\"가격과 수익률 중 하나만 입력하세요. 가격을 입력하면 수익률 칸은 비워 두세요.\"",
  "note": "A1(UI-10) 용어 작업과 겹칩니다."
 },
 {
  "id": "T-01",
  "where": "Native, new TermLookup (QApplication event filter, or per-widget like wheel_guard via localization.py:84-87)",
  "current": "QLabel 선택은 되지만(app.py:107, market_chart.py:371, watchlist.py:77) 선택 후 할 수 있는 일이 없음",
  "proposed": "MouseButtonRelease 때 hasSelectedText()이면 놓은 자리 옆에 \"알아보기\" 칩을 띄웁니다. 포커스는 가져오지 않고, Esc·스크롤·다른 클릭에서 닫힙니다. 누르면 오른쪽 패널이 열립니다.",
  "note": "proto_select.py로 확인: 필터가 놓는 순간 '수정 듀레이션' 선택을 받음, 더블클릭은 '듀레이션과'(조사 포함)를 선택함."
 },
 {
  "id": "T-02",
  "where": "Native, QLabel/표 context menu",
  "current": "QLabel 기본 메뉴(복사, 모두 선택)뿐이고 표에는 메뉴가 없음",
  "proposed": "메뉴: \"복사\" / \"모두 선택\" / \"알아보기: 듀레이션\". 표는 viewport 메뉴에서 현재 셀을 쓰고, Metric 열은 CAPTION_ROLE 영어 원문(app.py:162-163)으로 대조합니다.",
  "note": "QLabel에는 공개 createStandardContextMenu가 없어서 복사 기능을 직접 만들어야 합니다. 키보드로 연 표 메뉴(reason=Keyboard)가 필터에 들어오는 것은 확인했습니다."
 },
 {
  "id": "T-03",
  "where": "Native, keyboard/accessibility",
  "current": "label은 마우스로만 선택되고(TextSelectableByMouse) focusPolicy는 ClickFocus. 앱 전체에 QShortcut이 없음",
  "proposed": "F1을 누르면 패널이 열리고 검색창에 포커스가 갑니다(선택한 글이나 현재 표 셀의 용어가 미리 들어감). Esc로 닫고 원래 포커스로 돌아갑니다. 표에서는 Shift+F10이나 메뉴 키를 씁니다. 패널과 섹션에 accessible name을 붙입니다. 화면낭독기 사용자는 F1 경로를 씁니다.",
  "note": "Hover 밑줄 링크는 1단계에서 빼둡니다(PlainText label, app.py:104)."
 },
 {
  "id": "T-04",
  "where": "core/education/glossary.py (new terms_in(text, scope) next to search at :421)",
  "current": "search()는 입력 앞부분을 맞추는 방식이라 선택한 글에서 실패함: '듀레이션과'→(), 'RSI가'→(), 'Modified duration 4.2'→(), '볼린저 밴드에'→(), 'VaR를'→('cvar',)(틀림)",
  "proposed": "조사를 떼고, 가장 긴 별칭부터 맞추고, 영어는 단어 경계로 자르고, 애매한 별칭(forward, curve, 1bp, 밴드, 봉, IV, vol, MA, ES, bootstrap)은 화면 범위를 함께 봅니다.",
  "note": "proto_match.py 결과: '1일 VaR 95%'→var, '볼린저 상단 (20, 2σ)'→bb, 'GARCH(1,1)-t'→garch, 'Modified duration 4.2'→duration. 'Block bootstrap'은 금리 bootstrap과 헷갈리지 않게 막힘."
 },
 {
  "id": "T-05",
  "where": "Native panel (QDockWidget right of ResearchWindow, app.py:184) reusing glossary.sections (glossary.py:381-389) and IndicatorGuide._render_detail layout (indicator_guide.py:353-370)",
  "current": "용어 설명은 기술지표 가이드 화면 안에서만 볼 수 있음",
  "proposed": "패널 구성: 제목과 범주 / 개념(무엇을 나타내나요?) / 적용(어디에 쓰나요? · 해석의 한계) / 현재 화면에서의 의미 / \"가이드에서 자세히 보기\"(navigate('guide')+choose(key), indicator_guide.py:258). 후보가 여럿이면 칩으로 고릅니다. 폭은 320~360px이고, 창이 1280px보다 좁으면 내용 위에 겹쳐 띄웁니다.",
  "note": "최소 창 1000px(app.py:224)에서 내용을 옆으로 밀면 폼이 잘릴 위험이 있습니다(UI-6a, UI-18)."
 },
 {
  "id": "T-06",
  "where": "Native, per-pane term_context(key) providers",
  "current": "현재 화면 값과 용어를 이어 주는 장치가 없음",
  "proposed": "공통 방안: 지금 화면의 표에서 별칭과 맞는 행을 찾아 \"현재 결과: 수정 듀레이션 = 4.213\"처럼 보여 줍니다. 화면별 추가: Markets 차트는 indicator_series 커서 값(market_chart.py:1150-1154)과 reading_text 문장(core/education/chart.py:143-163), 프로필은 행 값(markets_view.py:885-893), MC는 outputs[run_id].result(app.py:893-905), Bonds는 analytics(bonds.py:81-87), Portfolio는 chart.output, ToolPane은 sections/report(tools.py:205-266), Home은 Q-SCORE(app.py:762-770)",
  "note": "새 계산은 없고 이미 표시된 값만 인용합니다. 공급사가 들어 있는 hint는 다시 보여 주지 않습니다. 용어별 해석 문장(숫자 재진술 포함)은 2단계로 미루고 소유자 검토를 받습니다."
 },
 {
  "id": "T-07",
  "where": "AI/consent: quantgen_desktop/commentary.py:21-38,69-73,107-125",
  "current": "AI 해설은 Library에서만 됩니다(결과 선택 → 미리보기 → 동의 체크 → 전송, 질문을 고치면 동의가 풀림)",
  "proposed": "패널은 AI를 부르지 않고 로컬에서만 동작합니다. 넣는다면 \"AI에게 더 묻기\"는 Library 해설 패널로 질문을 넘겨주기만 하고, 패널에서는 아무것도 보내지 않습니다.",
  "note": "용어 하나는 '완료된 계산 보고서'(ALLOWED)가 아닙니다. 그래서 해설 패널로 넘기려면 소유자 결정이 필요합니다."
 },
 {
  "id": "T-08",
  "where": "core/education/glossary.py TERMS (36-345)",
  "current": "32개 용어. 표 항목명 403개 중 86개만 용어와 이어지고 317개는 이어지지 않음(종목·코드명 포함). 'forward' 별칭은 fx_forward로만 감",
  "proposed": "1차 추가 후보: z-spread, 롤다운, 손익분기(bp), YTM, 금리차(2s10s), 선도금리(1y1y·5y5y), 연금계수, 파 금리, 스왑션, 캡·플로어, 리스크 리버설·ATM, 베이시스, 김치 프리미엄, 펀딩비, 모멘텀, 승률, PBO, IS/OOS·워크포워드, DSR, 효율적 투자선, 위험기여도, 리스크 패리티, P(loss), ERP·드리프트, 블록 부트스트랩, 52주 범위, 공매도 비중, PER·EPS·시가총액",
  "note": "UI-10 표준 한국어 용어집과 출처를 하나로 합칠 것을 권합니다(용어마다 '표준 이름' 필드 추가)."
 },
 {
  "id": "T-09",
  "where": "quantgen_desktop/market_chart.py:377-390; watchlist.py:599-650 (ScoreHelpDialog) + core/research/qscore.py:38",
  "current": "지표 설명과 Q-SCORE 설명이 용어집 밖에 따로 있음",
  "proposed": "용어집 하나로 합칩니다. Q-SCORE의 \"?\" 버튼(watchlist.py:386-412)은 패널의 q_score 항목을 엽니다.",
  "note": "설명이 서로 달라지는 것을 막습니다."
 },
 {
  "id": "F-01",
  "where": "ui/*.py ft.Text (AST scan)",
  "current": "ft.Text 235개 중 159개가 12px 이하(12px 77, 11px 70, 10px 12). selectable=을 넘기는 것은 55개",
  "proposed": "설명 문장은 13px 이상으로 하고 selectable=True로 바꿉니다. 10px은 표 머리글·라벨·빈 문자열에만 쓰고 설명 문장에는 쓰지 않습니다(components.py:127, portfolio_page.py:55-57,166-170, signals_page.py:85,90, trading_page.py:202, macro_state_panel.py:224).",
  "note": ""
 },
 {
  "id": "F-02",
  "where": "ui/market_chart_page.py:104,539-545; ui/research_home.py:173,178; ui/krx_page.py:71; ui/rates_page.py:90-91 (chips at 125,183,239,275,330-331)",
  "current": "\"출처 KIS · 120봉 · 마지막 봉 … · 시세 시각 … · 수신 …\"(11px), Home 타일 \"provider · 관측일\"(10px), \"Source: …\"(11px)",
  "proposed": "PR #71 결정을 Flet에도 적용한다면 툴팁으로 옮깁니다. 합성이나 지연일 때만 칩을 둡니다.",
  "note": "README.md:896은 \"The Flet browser is unchanged\". 이 결정이 Flet에도 해당하는지는 소유자 확인이 필요합니다."
 },
 {
  "id": "F-03",
  "where": "ui/ai_panel.py:57-75,91,96",
  "current": "\"Deep analysis sends calculated results and your question to Anthropic. …\"(11px). 미리보기나 동의 체크 없이 버튼을 누르면 바로 보냄",
  "proposed": "Flet 용어 패널에는 AI 경로를 넣지 않습니다. 안내 문구는 13px로 키웁니다. 동의 절차를 Native와 맞추는 일은 별도 항목으로 둡니다(B3·13-9 관련).",
  "note": ""
 },
 {
  "id": "F-04",
  "where": "Flet selection: ft.Text(selectable=True, on_selection_change) (flet 0.85.2); hook in ui/localization.py:6-33 translate_controls",
  "current": "선택 이벤트를 쓰는 곳이 없음. SelectionArea.on_change에는 선택한 글이 들어 있지 않음",
  "proposed": "translate_controls 순회에서 설명 문장 Text에 selectable과 handler를 붙입니다. 숫자 데이터(data={'numeric':True})는 건너뜁니다. 선택한 글은 debounce한 뒤 고정 위치 칩 \"알아보기: <용어>\"로 보여 줍니다.",
  "note": "TextSelection은 오프셋만 있고 화면 좌표가 없어서 선택한 자리 옆에 띄울 수 없습니다."
 },
 {
  "id": "F-05",
  "where": "main.py:308-311 (LocalizedRoot row) or page.end_drawer/show_end_drawer",
  "current": "패널 없음",
  "proposed": "오른쪽 열 ft.Container(폭 320, 열고 닫기)를 둡니다. 내용은 glossary.sections를 그대로 쓰고, 번역은 translate_controls가 처리합니다.",
  "note": "ft.ContextMenu(오른쪽 클릭)는 웹에서 page.browser_context_menu.disable()이 필요해서 브라우저 복사 메뉴가 사라집니다. 그래서 주 경로로는 권하지 않습니다."
 },
 {
  "id": "F-06",
  "where": "ui/ai_panel.py:44 analysis_panel(payload_fn) – 19 call sites",
  "current": "payload_fn은 AI로 보낼 때만 씀",
  "proposed": "analysis_panel이 page에 '현재 결과 맥락'으로 payload_fn을 등록하고, 용어 패널이 로컬에서만 읽어 \"현재 결과: …\"를 보여 줍니다.",
  "note": "filter_analysis_fields로 이미 걸러진 데이터입니다. 네트워크는 쓰지 않습니다."
 },
 {
  "id": "F-07",
  "where": "ui/fcharts.py (matplotlib), ui/market_chart_page.py:114,516 (SVG ft.Image)",
  "current": "차트 안의 글은 이미지라서 선택할 수 없음",
  "proposed": "차트 아래에 \"이 차트의 용어\" 칩 줄을 둡니다(예: DV01, 볼록성).",
  "note": "Native의 LineChart, SignedBars, QSvgWidget 차트도 같은 방식으로 합니다."
 },
 {
  "id": "F-08",
  "where": "Flet keyboard: ft.Page.on_keyboard_event (unused in main.py/ui)",
  "current": "단축키 없음",
  "proposed": "F1로 패널과 검색을 열고, Esc로 닫습니다.",
  "note": ""
 },
 {
  "id": "F-09",
  "where": "ui/indicator_guide.py:8-9",
  "current": "Flet 지표 가이드는 용어집을 쓰지 않음(지표 5개 칩만 있음)",
  "proposed": "용어 패널과 같은 glossary 모듈을 써서 Native와 용어를 맞춥니다.",
  "note": "UI-13(검색형 가이드)은 Native에만 적용되어 있습니다."
 }
]
```
