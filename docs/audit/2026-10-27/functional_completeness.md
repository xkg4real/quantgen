# 기능 완전성 감사 보고서 (요청서 7장 2항)

- 대상: `/home/user/quantgen`, HEAD `859a983`. 코드 파일은 `527cdf2`와 같다(그 뒤 커밋은 문서만 바꿨다).
- 날짜: 2026-10-27. 차원 key: `functional_completeness`.
- 규칙: 감사만 했다. 추적 파일은 하나도 고치지 않았다. 수정안은 부록 A의 diff로만 제시한다. diff는 저장소 밖 사본(`.../functional_completeness/patched/`)에서 적용·검증했다.
- 판정 표기: 사실(코드·실행으로 확인), 추정(가능성이 높으나 재현 안 함), 오류(주장이 틀림), 미검증(확인 못 함).

## 0. 요약

1. 16개 NAV 화면은 모두 오프라인에서 만들어진다. 실행 버튼이 있는 분석 화면 12개 중 11개는 합성 데이터로 오류 없이 돈다. 예외는 Strategy Lab 하나다.
2. **Strategy Lab의 "Run a family through the gate"는 모든 계열에서 실패한다(FC-01, P1, 사실).** 자본곡선이 날짜보다 한 점 길어 차트에서 `ValueError`가 난다. 이 예외는 worker의 try 밖에서 난다. 화면은 빈 패널과 계속 도는 진행 링만 남는다. 실데이터 실행이면 그 전에 시행 장부에 구성 12개가 먼저 등록된다.
3. statsmodels가 의존성에 직접 선언돼 있지 않다. 없으면 ADF가 조용히 NaN이 된다. 그래도 ETH/BTC 판정은 "단위근 기각 못 함"이라고 쓴다(FC-02, P2, 사실). gs-quant 2.2.1을 통해서만 간접 설치된다.
4. KIS의 원화 금리·국고채·KTB 선물·원/달러 고시 함수는 데이터 계층에 있다. 그러나 FICC 화면(Rates, Bonds, FX, Structuring)은 하나도 쓰지 않는다. 이 화면들은 미국 국채(FRED)와 합성만 고른다(FC-03, P2, 사실). 소유자 메모 "FICC가 KIS로 되는가"의 기능 측면 답이 이것이다.
5. 예측 기능(Quant Lab 팬·VaR, GARCH 분산 예측, 헤지 P&L 시뮬레이션)은 구현·UI·테스트가 모두 있다. 그러나 **게이트를 통과한 판단 지표의 현재 값은 어느 화면에도 없다**(FC-04, P2, 사실). README의 "Offered as a signal"(PASS 2건)은 판정 칩으로만 보인다. 매크로 권고 장부는 설계대로 1.0(불변식)뿐이다.
6. README의 세부 주장 일부는 화면에 없다: 경험적 가격결정 커널, vertical 차익 수, PCA 버터플라이 모니터, BTC stationarity share, 기호별 연구 칩(FC-05, P3).
7. 화면 self-check 8개가 전체 테스트(`run_all`)에 들어 있지 않다. Strategy Lab Run, Portfolio, Signals의 실행 경로를 누르는 테스트도 없다. FC-01이 이 틈으로 빠져나갔다(FC-06, P3).
8. 문서 일부가 낡았다: README 테스트 총계, `main.py` docstring, "저장소를 git에 올려라" 안내(FC-07, P3). Signals 백테스트는 비용표 대신 10 bp를 쓴다(FC-08, P3).

심각도 집계: P0 0건, P1 1건, P2 3건, P3 4건.

## 1. 범위

- 요청서 7장 2항: README가 말하는 기능 영역마다 README 주장 → 구현 모듈·함수 → UI 진입(`main.py` NAV와 페이지 빌더) → 오프라인 실행 여부 → 테스트를 추적한다.
- 영역: 매크로, FICC(금리·채권·FX·구조화), 주식(Quant Lab·Portfolio·Signals·KRX), BTC/가상자산, 파생(KOSPI200 표면), ETF, Strategy Lab, 예측과 예측 기반 판단 지표.
- 제외: 금융 공식의 정확성(다른 차원), 합성 대체 표시(D-03 보고서), 시각 필드(D-04/D-05 보고서), 캐시·공급사 비교(C-01/V-01 보고서). 겹치는 곳은 해당 보고서를 가리킨다.

## 2. 방법

1. README 전체(929줄)와 `main.py`를 읽고 기능 주장을 줄 번호로 뽑았다.
2. 각 주장을 `ui/*_page.py`의 호출 지점과 `core/`·`data/` 함수까지 grep과 코드 읽기로 따라갔다.
3. 공용 실행 틀 `_hermetic.py`: HOME과 `QUANTGEN_MACRO_DIR`를 스크래치로 옮기고, 자격증명 환경변수를 지우고(값은 출력하지 않음), `socket.connect`·`getaddrinfo`를 막는다. 모든 스크립트는 `python3 -B`로 돌렸다. 네트워크 시도는 전부 차단됐다.
4. 실행 확인:
   - 화면 self-check 10개를 프로세스 안에서 실행했다(`run_ui_selfchecks.py`).
   - 16개 NAV 빌더를 `main.py`가 가져오는 그대로 만들었다(`build_all_nav.py`).
   - 12개 분석 화면의 실행 버튼을 가짜 page로 눌렀다(`drive_pages.py`).
   - 매크로 오버레이를 KR만 dry run 했다. 허용된 캐시 파일만 스크래치로 복사했다. 금지 파일 4개는 열지 않았다(`dry_run_kr.py`).
5. 테스트 매핑: 기준 실행 `baseline2_results.json`(745 PASS / 1 FAIL / 124 NOT_RUN)과 테스트 소스를 대조했다. `tests/run_all.py`는 실행하지 않았다. 제안 패치 검증용으로 ficc·quant·expansion의 `tests()`만 스크래치 사본에서 프로세스 안에서 돌렸다.
6. 제안 패치는 `git archive HEAD`로 만든 스크래치 사본에만 적용했다(줄끝 CRLF 유지). 같은 회귀 테스트가 사본에서는 통과하고 HEAD에서는 실패하는지 확인했다.

## 3. 기능 영역별 추적표

판정 기호: **구현+UI+테스트** / **구현만** / **문서만** / **미검증**. "오프라인"은 이번 감사에서 네트워크 없이 실행한 결과다.

| # | 영역 | README 주장 | 구현 (file:line) | UI 진입 | 오프라인 실행 | 테스트 | 판정 |
|---|---|---|---|---|---|---|---|
| 1 | 매크로 시트 | `README.md:62-80` 18개 지표, 1d/1w/1m/3m 변화, z·백분위, 서술 판독, 보고서 버튼 2개 | `core/ficc/macro.py:61` `INDICATORS`(18개 확인), `:202` `macro_sheet`, `:237` `daily_brief`, `:255` `weekly_brief` | `main.py:71` NAV `macro` → `ui/macro_page.py:88` `build_macro_page` → `:192` `macro_sheet` | 합성: 표·차트·해설·보고서 2종 정상 | `ficc/test_macro_*` 3건, `macro_ui_overlay`(페이지 빌드) | 구현+UI+테스트 |
| 2 | 매크로 v2(오버레이·카드·리서치) | `README.md:316-628` | `core/skills/macro_daily.py`, `core/quant/{risk_layer,cards,gate_package,…}`, `ui/macro_state_panel.py:661`, `ui/macro_cards_view.py:313`, `ui/research_view.py:302` | `ui/macro_page.py:44-46` 뷰 선택, `:227` 지연 빌드 | KR dry run 정상. 화면에 `VENDOR DATA · DRY RUN` 칩, `recommended:KR composed 1.000`. 카드는 전부 NOT RUN(설계대로) | macro 421 PASS / 121 NOT_RUN(baseline2) | 구현+UI+테스트(정식 카드 실행은 설계상 차단, US dry run은 미검증) |
| 3 | 금리(Rates) | `README.md:82-89` 부트스트랩·NS/NSS·PCA, 스왑, 스왑션·캡플로어, Vasicek/CIR/HW | `core/ficc/curves.py:165,215,221,262,325,374`, `swaps.py:152,208,233,340,382`, `ratesim.py:50,106,218,344` | NAV `rates` → `ui/rates_page.py:364`, 작업 함수 `:103,:156,:200,:291` | 합성: 4개 도구 모두 정상 | ficc 다수(부트스트랩, NS, PCA, 스왑, 스왑션 패리티, 캡, ratesim 4건) | 구현+UI+테스트(페이지 self-check는 run_all 밖, FC-06) |
| 4 | 채권(Bonds) | `README.md:91-98` | `core/ficc/bonds.py:231,299,323` | NAV `bonds` → `ui/bonds_page.py:59`, `:110-118` | 합성: 계산·시나리오·헤지 정상 | `ficc/test_bond_*` 10건, `test_futures_hedge_arithmetic` | 구현+UI+테스트 |
| 5 | FX | `README.md:100-106` CIP·GK·SABR·캐리 바스켓 | `core/ficc/fx.py:57,64,126,168,201,217,346,384` | NAV `fx` → `ui/fx_page.py:122`, `:185-313` | 합성: 선도·옵션·캐리 정상 | `ficc/test_fx_*`, `test_gk_*`, `test_sabr_*`, `test_carry_*` | 구현+UI+테스트 |
| 6 | 구조화(Structuring) | `README.md:108-118` 4개 상품, 헤지 시트 | `core/ficc/structured.py:144,196,251,328,386` | NAV `structuring` → `ui/structuring_page.py:217`, `:91-111`, `:269-274` | 합성: 4개 상품 정상(self-check) | `ficc/test_ppn_*`, `test_reverse_convertible_*`, `test_dcd_*`, `test_steepener_*`, `test_hedge_sheet_*` | 구현+UI+테스트 |
| 7 | KIS FICC 데이터(원화 금리, KTB, KTB·USD 선물, 원/달러 고시, 수급·공매도) | `README.md:715` | `data/kis_markets.py:55-64, 492-512, 561-626`, `core/ficc/curve_models.py:242` `krw_curve_panel` | FICC 화면 연결 없음. Derivatives의 CD91 금리(`ui/derivatives_page.py:69-71`)와 `load_history` 단일 시계열 경로(`core/quant/history.py:296-317`)만 있음 | 키 없음 → 미실행(가짜 KIS로만 확인) | `expansion/kis_markets_paging_and_shapes`(가짜 전송) | 구현만(FC-03) |
| 8 | Quant Lab | `README.md:135-181` 4개 모형, 드리프트 4종, 자체 채점 칩 | `core/quant/montecarlo.py:66,229`, `garch.py:446,558,674`, `docs/quant_lab/*.json` | NAV `quant` → `ui/quant_lab_page.py:239`, `:287-288` | 합성: 4개 모형 정상 | quant 53건, `macro_ui_views` Quant Lab 2건 | 구현+UI+테스트 |
| 9 | Portfolio | `README.md:183-188` 목적 4종, 프런티어, 무작위 1,500개 | `core/quant/optimize.py:68,103`(`n_cloud=1500` 확인) | NAV `portfolio` → `ui/portfolio_page.py:75`, `:111-117` | 합성: 4개 목적 정상 | `quant/test_optimizer_*`, `test_frontier_*`, `test_risk_parity_*` | 구현+UI+테스트(실행 경로 테스트 없음, FC-06) |
| 10 | Signals | `README.md:190-196` 6개 구성요소, 비용 반영 백테스트 | `core/quant/signals.py:90`(6개 확인), `backtest.py:29,107` | NAV `signals` → `ui/signals_page.py:95`, `:136-139` | 합성: 전략 3종 정상 | `quant/test_signal*`, `test_backtest_*`, `macro_ui_views/test_signals_page_header_notice` | 구현+UI+테스트(비용 기본값 FC-08) |
| 11 | KRX 시세(상속) | `README.md:763-772` | `data/krx/gateway.py` | NAV `krx` → `ui/krx_page.py:32` | 빌드만 확인. 실시세 미검증 | `safety/test_21`, `test_22`, engine 92건 | 구현+UI+테스트(실시세 미검증) |
| 12 | 파생(KOSPI200 표면) | `README.md:209-222` | `ui/derivatives_page.py:51-136` `snapshot`, `core/ficc/equity_deriv.py`(basis, IV, SVI, MFIV, RND, box, 헤지 시뮬레이션) | NAV `derivatives` → `ui/derivatives_page.py:195`, `:215` | 합성 보드: gbm·garch_t 정상. KIS 보드는 키 없음 오류 안내 | `expansion/selfcheck_equity_deriv`, KIS 가짜 전송 테스트. 페이지 self-check는 run_all 밖 | 구현+UI+테스트. 단 가격결정 커널은 문서만(FC-05) |
| 13 | ETF | `README.md:224-230` NAV·괴리·바스켓·LETF drag·슬리브 | `ui/etf_page.py:45-128` `analyze`, `core/ficc/equity_deriv.py:548` `letf_drag` | NAV `etf` → `ui/etf_page.py:176`, `:190` | 합성·auto(키 없음): 슬리브·LETF drag 정상. NAV·괴리·바스켓은 KIS 전용 | `expansion/etf_page_adjusted_sleeves`(가짜 KIS) | 구현+UI+테스트 |
| 14 | 가상자산(BTC) | `README.md:232-241` 김치 프리미엄, 펀딩, GARCH-t, ETH/BTC, 요일표 | `core/crypto/analytics.py:69,136,170,178`, `data/crypto/crypto_client.py`, `ui/crypto_page.py:60-97` | NAV `crypto` → `ui/crypto_page.py:134`, `:147` | 합성 정상. live는 네트워크 차단으로 오류 안내(미검증) | `expansion/selfcheck_crypto_analytics`, `selfcheck_crypto_page`, `crypto_client_refusals_and_router` | 구현+UI+테스트(ADF 의존 FC-02, 합성 환율 D03-01) |
| 15 | Strategy Lab 점수표 | `README.md:243-251, 272-312` 카드 34개 5/11/18 | `core/quant/validate.py:847` `load_cards`, `docs/asset_expansion/cards/*.json`(34개, PASS 5·REVISE 11·REJECT 18 확인) | NAV `lab` → `ui/strategy_lab_page.py:158-212` | 정상 | `macro_ui_views/test_strategy_lab_builds_with_foreign_cards_in_a_temp_cards_dir` | 구현+UI+테스트 |
| 16 | Strategy Lab 계열 실행 | `README.md:246-248` "runnable on any symbols and source through the same gate" | `core/quant/strategies.py:162-379`, `validate.py:345,492`, `ui/strategy_lab_page.py:85-136` `run_family` | `ui/strategy_lab_page.py:227-279` | **실패**: 7개 계열 전부 차트에서 `ValueError`(FC-01) | `expansion/selfcheck_strategy_lab`은 `run_family`만 부름. Run 클릭 테스트 없음 | 구현만(UI 경로 고장) |
| 17 | 예측 | Quant Lab 팬·VaR·손실확률(`README.md:147-149`), GARCH 분산 기간구조(ETF, `:227-229`), 헤지 P&L(파생, `:219-220`), 변동성 추정기(매크로 vt) | 8·12·13행의 모듈, `core/quant/vol_estimators.py`, `forecast_eval.py` | 각 화면 | 합성 정상 | quant 53, `macro_m3_estimators` 12 PASS / 8 NOT_RUN | 구현+UI+테스트 |
| 18 | 예측: Diebold–Li | `README.md:301`(REJECT로 표시) | `core/ficc/curve_models.py:1-21`(`dns_study`) | 화면 호출 없음. 카드 `M_B1_dns`(REJECT)만 점수표에 표시 | 해당 없음 | `expansion/selfcheck_curve_models` | 구현만(연구 스크립트 `docs/asset_expansion_study.py:450,479`; 기각돼 비노출은 의도) |
| 19 | 예측 기반 판단 지표 | `README.md:281-285` "Offered as a signal", `:357-362` 권고 장부 | Signals 종합 점수(`signals.py:157-170`), 매크로 권고 장부, PASS 카드 `S_C3_*` | Signals는 "Context only" 표시. 권고 장부는 1.000. PASS 카드는 판정 칩뿐 | KR dry run: `recommended:KR composed 1.000` | 각 영역 테스트 | 현재 판단 값 표시는 문서만(FC-04) |

## 4. 요청서·README 주장 검증

| # | 주장 | 출처 | 판정 | 근거 |
|---|---|---|---|---|
| 1 | README의 매크로·FICC·주식·BTC·파생·구조화·예측 기능이 구현돼 UI에서 호출된다 | 요청서 7장 2항(검증 요청) | 대부분 사실, 일부 오류 | 3장 표. Strategy Lab 계열 실행은 UI에서 동작하지 않는다(FC-01). KIS FICC는 화면 연결이 없다(FC-03). 세부 4건은 화면에 없다(FC-05) |
| 2 | "With zero keys and no network, every page still works on synthetic data" | `README.md:745-747` | 오류(1곳) | 분석 화면 12개 중 11개는 합성으로 동작한다(`drive_pages.log`). Strategy Lab Run은 합성으로도 실패한다(FC-01) |
| 3 | "every strategy family … runnable on any symbols and source through the same gate" | `README.md:246-248` | 오류(UI) / 사실(코어) | `run_family`는 7개 계열 모두 판정을 낸다. 화면은 차트에서 멈춘다 |
| 4 | Strategy Lab 카드 34개, 5 PASS / 11 REVISE / 18 REJECT | `README.md:274-278` | 사실 | `docs/asset_expansion/cards/*.json` 집계 |
| 5 | 매크로 시트 지표 18개 | `README.md:69` | 사실 | `core/ficc/macro.py:61` |
| 6 | Signals 구성요소 6개 | `README.md:192` | 사실 | `core/quant/signals.py:96-155` |
| 7 | 프런티어 무작위 포트폴리오 1,500개 | `README.md:187` | 사실 | `core/quant/optimize.py:104` |
| 8 | NAV 16개, FICC 5개가 먼저 | `README.md:13-14, 771-772` | 사실 | `main.py:70-87` |
| 9 | 파생 화면에 "경험적 가격결정 커널" | `README.md:217-218` | 오류(UI) | `pricing_kernel`(`core/ficc/equity_deriv.py:419`)은 self-check(`:617`)에서만 호출. 화면은 f_Q와 (garch_t일 때만) f_P를 그린다 |
| 10 | PCA 버터플라이를 모니터로 제공 | `README.md:286-289` | 오류(UI) | `curve_models.butterfly_signal` 호출 화면 없음. Rates는 단순 2s5s10s fly만(`ui/rates_page.py:115`) |
| 11 | Quant Lab이 "모든 적합 옆에" 위반율과 skew-t 판정을 보인다 | `README.md:307-308` | 부분 사실 | `ui/quant_lab_page.py:165-187`은 기호와 무관하게 SPY·KODEX 200 카드만 보인다 |
| 12 | KIS가 원화 금리, KTB, 수급, 공매도를 제공 | `README.md:715` | 사실(데이터 계층) | `data/kis_markets.py:492-626`. 화면 연결은 FC-03 |
| 13 | 테스트 총계 743/864 | `README.md:878` | 오류(낡음) | 저장 결과 `qa/acceptance_results.json`: 870건 중 749 PASS, 121 NOT_RUN. papers 43 → 49 |
| 14 | 과거 기록 870건 중 749 PASS, 121 NOT_RUN | 요청서 3장 | 사실 | `qa/acceptance_results.json` 집계 |
| 15 | FICC·매크로 오프라인 자체 검사 ok | 요청서 3장 | 사실(이번 재실행) | 화면 self-check 10개 모두 OK(`ui_selfchecks.log`) |
| 16 | 소유자가 저장소를 git에 올려야 한다 | `README.md:357, 585-586`, `core/skills/macro_daily.py:1073-1074` | 오류(낡음) | `README.md:48`: 분할 이후 git 관리 중. 실제 차단 요인은 `core/ficc/macro_artifacts.py:33` 상수 `UNVERSIONED`(분할 명세 3.3절 결정). FC-07 |

## 5. 발견사항

### 5.1 요약 표

| ID | 심각도 | 판정 | 파일·함수·라인 | 한 줄 요약 |
|---|---|---|---|---|
| FC-01 | P1 | 사실 | `ui/strategy_lab_page.py:227-279`, `:130-131`, `:118`; `ui/xcharts.py:72-81`; `core/quant/strategies.py:93-94` | Strategy Lab 계열 실행이 모든 계열에서 차트 `ValueError`로 멈춘다. 빈 패널과 도는 링만 남고, 실데이터면 장부에 시행이 먼저 등록된다 |
| FC-02 | P2 | 사실 | `core/quant/strategies.py:266-271`; `core/crypto/analytics.py:170-175`; `requirements.txt`; `pyproject.toml:10-17` | statsmodels 미선언. ADF가 NaN이 돼도 ETH/BTC 판정은 "기각 못 함"으로 나온다 |
| FC-03 | P2 | 사실 | `data/kis_markets.py:55-64, 492-626`; `core/ficc/curve_models.py:242-258`; `ui/rates_page.py:43-44, 95, 104`; `ui/bonds_page.py:29-30, 110`; `ui/structuring_page.py:32-33, 269`; `core/ficc/data.py:617-631` | KIS 원화 금리·KTB·원/달러 기능이 FICC 화면에 연결되지 않았다. FX의 KRW 금리는 월간 OECD 계열이다 |
| FC-04 | P2 | 사실 | `README.md:281-285`; `ui/crypto_page.py:94-96, 158-160`; `ui/strategy_lab_page.py:130-136, 261-274`; `core/quant/strategies.py:330-348` | 게이트를 통과한 판단 지표의 현재 값이 어느 화면에도 없다 |
| FC-05 | P3 | 사실 | `ui/derivatives_page.py:201, 251-263`; `core/ficc/equity_deriv.py:212-240, 419-426`; `ui/rates_page.py:115`; `ui/crypto_page.py:94-96`; `ui/quant_lab_page.py:165-187` | README 세부 기능 5개가 화면에 없거나 다른 대상을 보인다 |
| FC-06 | P3 | 사실 | `tests/expansion_acceptance.py:323-345`; `tests/macro_ui_views.py:264-295` | 화면 self-check 8개와 Run·Optimize·Analyze 실행 경로가 전체 테스트 밖이다 |
| FC-07 | P3 | 사실 | `README.md:357, 585-586, 877-878`; `main.py:8-9, 17-18`; `core/skills/macro_daily.py:1073-1074`; `core/quant/gate_package.py:46` | 테스트 총계, docstring, "git에 올려라" 안내가 낡았다 |
| FC-08 | P3 | 사실 | `ui/signals_page.py:114-115, 136-139`; `core/quant/backtest.py:108` | Signals 백테스트가 비용표(US 50 bp, KRX 주식 35 bp) 대신 10 bp를 쓰고, 화면에 비용을 표시하지 않는다 |

### 5.2 상세

#### FC-01 · P1 · 사실 — Strategy Lab 계열 실행이 모든 계열에서 실패한다

| 항목 | 내용 |
|---|---|
| ID | FC-01 |
| 심각도 | P1 |
| 판정 | 사실. 예외와 화면 상태는 동기 가짜 page로 재현했다. 실제 Flet 창에서 예외가 로그로만 남는지는 추정이다 |
| 파일·함수·라인 | `core/quant/strategies.py:93-94` `equity_curve`는 `[1.0] + cumprod`라 P&L보다 한 점 길다. `ui/strategy_lab_page.py:130-131`이 이것을 `wf.pnl`로 만들고, `:273`이 `xc.equity_chart(r["wf"].dates, …)`에 넘긴다. `ui/xcharts.py:76-78`의 `x[-eq.size:]`는 날짜 수(n)만큼만 잘리고 `eq`는 n+1이라 matplotlib가 거부한다. worker의 try(`ui/strategy_lab_page.py:231-240`)는 `run_family`만 감싸고, 렌더링(`:241-277`)은 감싸지 않는다. `run_family`는 채점 전에 `register_trials`(`:118`)를 부른다 |
| 재현 단계 | `python3 -B -W ignore /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/functional_completeness/repro_lab_chart.py` |
| 기대 결과 | Run을 누르면 판정 칩, 지표 타일, OOS 자본곡선, 해설이 나오고 진행 링이 사라진다 |
| 실제 결과 | 7개 계열 × 2개 길이(1500, 2600 세션) 14건 모두 `ValueError: x and y must have same first dimension, but have shapes (722,) and (723,)` 형태. 페이지 수준: 예외가 worker 밖으로 나가고 `ring.visible == True`, 결과 패널은 비어 있다. 실데이터로 표시한 실행(합성 시계열에 `source="YFINANCE"`를 붙임, 네트워크 없음)에서 E1 장부에 구성 12개가 먼저 기록됐다 |
| 영향 | README의 Strategy Lab 핵심 기능 하나가 UI에서 동작하지 않는다. 운영자는 결과를 못 보고, 종목을 바꿔 다시 돌리기 쉽다. 그때마다 보지 못한 결과의 구성이 계열 장부에 쌓인다. 이후 카드의 시행 수 계산에 들어간다. R3 run registry 설계(`docs/superpowers/specs/2026-10-27-strategy-lab-run-registry-design.md`)도 이 순서(등록 → 채점 → 렌더 실패)를 고려해야 한다. 점수표 부분은 영향 없다. ETF 화면의 같은 차트 호출은 길이가 맞아 정상이다(`ui/etf_page.py:238`) |
| 수정안 | 부록 A의 FC-01 diff. (1) `equity_chart`가 날짜보다 긴 곡선의 앞 점을 버린다. 점 i는 날짜 i 수익 뒤의 자본이다. (2) worker를 `work()`로 바꾸고 바깥 `worker()`가 모든 예외를 오류 안내로 바꾸며 링을 끈다. 사본에서 ficc 57, quant 53, expansion 30건 모두 통과 |
| 회귀 테스트 | `tests/expansion_acceptance.py::test_strategy_lab_run_renders_every_family`: 7개 계열 각각 Run 뒤 오류 안내 없음, `ring.visible is False`, `ft.Image` 존재. 추가로 `test_equity_chart_accepts_a_curve_one_point_longer_than_its_dates`, `test_strategy_lab_render_failure_becomes_a_notice`(차트 함수가 RuntimeError를 내도 "RuntimeError: chart exploded" 안내와 링 꺼짐). 세 테스트 모두 HEAD에서 실패, 사본에서 통과(`regression_tests.py`) |

#### FC-02 · P2 · 사실 — statsmodels 미선언, ADF NaN이 판정으로 바뀐다

| 항목 | 내용 |
|---|---|
| ID | FC-02 |
| 심각도 | P2 |
| 판정 | 사실(코드·재현). gs-quant 경유 간접 설치는 PyPI 메타데이터로 확인(gs-quant 2.2.1 `requires_dist`에 `statsmodels>=0.14.5`). 이전 gs-quant 버전의 의존성은 미검증 |
| 파일·함수·라인 | `core/quant/strategies.py:266-271` `adf_pvalue`가 모든 예외를 삼키고 NaN을 돌려준다. `core/crypto/analytics.py:170-175` `eth_btc_test`: `nan < 0.05`가 거짓이라 "no rejection of a unit root (the expected null)". 소비처: `ui/etf_page.py:77, 141, 211`, `ui/crypto_page.py:105, 117`, `core/quant/strategies.py:309`(pairs 공적분 비율), `core/ficc/curve_models.py:213`. 선언 누락: `requirements.txt`, `pyproject.toml:10-17` |
| 재현 단계 | `python3 -B /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/functional_completeness/repro_statsmodels_missing.py` (statsmodels를 `sys.modules`에서 숨긴 경우와 아닌 경우를 비교) |
| 기대 결과 | statsmodels가 직접 의존성이다. 검정이 돌지 않으면 "ADF not run"이라고 쓴다 |
| 실제 결과 | 숨김: 김치 ADF p `nan`, ETH/BTC ADF p `nan`, 판정 "no rejection of a unit root (the expected null)", 해설 "(ADF p nan, …)". 있음: 김치 3.0e-08, ETH/BTC 0.433, 같은 판정 문구. 원 기준 실행(statsmodels 없음)에서 `selfcheck_strategies`, `selfcheck_curve_models`, `selfcheck_crypto_analytics` 3건이 NaN으로 FAIL(`baseline_results.json`) |
| 영향 | README Setup대로 설치했는데 gs-quant 설치가 실패하거나 빠지면(README는 gs-quant를 선택 계층처럼 설명, `README.md:754-761`) ETF 괴리·김치 프리미엄·ETH/BTC·pairs의 ADF가 경고 없이 빈다. ETH/BTC는 검정 없이 판정 문장을 낸다 |
| 수정안 | 부록 A의 FC-02 diff: `requirements.txt`, `pyproject.toml`에 `statsmodels>=0.14` 추가. `eth_btc_test`가 NaN이면 "ADF not run (statsmodels unavailable or the test failed)". 추가 제안(미적용): `adf_pvalue`가 `ImportError`를 따로 잡아 한 번 경고를 남기고, ETF·Crypto 칩이 NaN이면 "ADF not run"을 쓴다 |
| 회귀 테스트 | `tests/expansion_acceptance.py::test_eth_btc_verdict_says_not_run_when_adf_is_unavailable`(`adf_pvalue`를 NaN으로 바꾸고 판정에 "not run" 포함 단언), `test_statsmodels_is_declared`(두 매니페스트에 문자열 존재). HEAD 실패, 사본 통과 |

#### FC-03 · P2 · 사실 — KIS FICC 데이터가 FICC 화면에 연결돼 있지 않다

| 항목 | 내용 |
|---|---|
| ID | FC-03 |
| 심각도 | P2 |
| 판정 | 사실(연결 부재). KIS 실제 응답과 수익률 관행은 미검증 |
| 파일·함수·라인 | 데이터 계층: `data/kis_markets.py:55-64`(`KRW_YIELD_CODES`, `KRW_CURVE_TENORS`, `FX_KRW_CODE`), `:492-512`(`krw_yield_daily`, `usdkrw_daily`, `krw_yields_snapshot`), `:561-626`(`bond_quote`, `bond_daily`, `bond_info`, `investor_daily`, `short_sale_daily`), `core/ficc/curve_models.py:242-258` `krw_curve_panel`(호출처는 `docs/asset_expansion_study.py`뿐). 화면: `ui/rates_page.py:43-44` 출처가 auto/fred/synthetic뿐, `:95, :104` `load_treasury_curve`; `ui/bonds_page.py:29-30, 110`; `ui/structuring_page.py:32-33, 269`; FX의 KRW 금리 `core/ficc/data.py:628`(`IR3TIB01KRM156N`, 월간; 같은 파일 `:617-618` 주석은 OECD 계열이 6-8개월 늦다고 적는다) |
| 재현 단계 | `grep -rn "investor_daily\|short_sale_daily\|bond_quote\|bond_info\|usdkrw_daily\|krw_yield_daily\|krw_curve_panel" --include=*.py ui core data` → `core/ficc/curve_models.py` 외 호출 없음. 연결 검증: `python3 -B -W ignore .../regression_tests.py /home/user/quantgen` → `test_krw_curve_source_prices_off_kis_without_synthetic`가 `ImportError: cannot import name 'load_curve'` |
| 기대 결과 | README(`:715`)가 KIS로 원화 금리를 받는다고 말하고, 소유자가 FICC를 KIS로 보길 원한다. 최소한 Rates·Bonds·Structuring이 원화 곡선(CD91 + KTB)을 고를 수 있어야 한다 |
| 실제 결과 | FICC 화면은 미국 국채 곡선만 쓴다. 원화 금리는 Derivatives의 CD91 할인율(`ui/derivatives_page.py:69-71`)과, 주식 화면에 `Y0101` 같은 기호를 넣었을 때의 단일 "가격" 시계열(`core/quant/history.py:296-317`)로만 화면에 닿는다. 수급·공매도·KTB 시세 함수는 앱 호출처가 없다 |
| 영향 | 국고채 곡선, 원화 스왑, KTB 가격·위험, 원화 캐리를 화면에서 분석할 수 없다. FX 캐리의 KRW 금리는 지연된 월간 계열이다 |
| 수정안 | 부록 A의 FC-03 diff: `core/ficc/data.py`에 `load_curve(source)` 추가. `kis_krw`면 `krw_curve_panel`, 키가 없으면 합성으로 바꾸지 않고 거절. Rates·Bonds·Structuring에 "KRW curve (KIS: CD 91d + KTB)" 선택지 추가. 금리 시뮬레이션은 SOFR 보정이라 KRW 곡선이면 거절. 주의: 부트스트랩 기본 `freq=2`(`core/ficc/curves.py:165`)는 KTB 반기 이표와 맞는다고 보았다(추정). CD91은 단기 금리를 3개월 par 점으로 쓴다. FRED 경로의 1·3개월 물도 같은 방식이다. 추가 제안(미적용): `load_short_rate("KRW")`가 KIS 설정 시 `Y0112`(CD 91d) 일간 계열을 쓰고, Bonds 헤지에 KTB 선물(`A65…`)을 연결 |
| 회귀 테스트 | `tests/ficc_acceptance.py::test_krw_curve_source_prices_off_kis_without_synthetic`(본문은 `regression_tests.py`): 가짜 `KISMarkets.krw_yield_daily`로 `load_curve("kis_krw").source == "KIS"`, `tenors[0] == 0.25`; `_run_curve`·`_run_swap` 결과에 "Synthetic" 없음, "KIS" 칩 있음; `kis_ready()`가 거짓이면 예외에 "KIS" 포함. 사본 통과, HEAD 실패 |

#### FC-04 · P2 · 사실 — 게이트를 통과한 판단 지표의 현재 값이 화면에 없다

| 항목 | 내용 |
|---|---|
| ID | FC-04 |
| 심각도 | P2 |
| 판정 | 사실(표시 부재). README "Offered"의 의도(점수표 노출인지, 현재 상태 표시인지)는 추정 |
| 파일·함수·라인 | `README.md:281-285`(KRW-BTC·BTC-USD crypto trend PASS, "Offered as a signal"). `ui/crypto_page.py:94-96, 158-160`은 카드 판정 칩만 보인다. `core/quant/strategies.py:330-348` `crypto_trend`는 상태를 계산하지만 호출처는 Strategy Lab 격자(`ui/strategy_lab_page.py:42`)뿐이다. Strategy Lab 결과(`:261-274`)는 OOS 지표와 곡선만 보이고 마지막 가중치는 없다. 매크로: `README.md:357-362`, dry run 권고 장부 1.000. Signals: `ui/signals_page.py:27` "Context only" |
| 재현 단계 | `grep -rn "crypto_trend(" --include=*.py ui core` → 격자 정의 외 없음. `python3 -B .../dry_run_kr.py` → `recommended:KR: composed = 1.000 × min(1.0, ladder 1.00 …) = 1.000` |
| 기대 결과 | README가 "신호로 제공"이라고 하면, PASS 규칙의 오늘 상태(long/flat, 시작일)와 카드 판정·데이터 출처가 한 화면에 있어야 한다. 아니면 README가 "점수표에서 PASS, 현재 상태는 표시하지 않음"이라고 써야 한다 |
| 실제 결과 | 예측(팬, VaR, 분산 예측, 헤지 시뮬레이션)은 보인다. 판단 지표 셋은 이렇다: Signals 종합 점수는 검증 없는 맥락 정보로 표시된다. 매크로 권고 장부는 카드가 모두 NOT RUN이라 불변식 1.0만 나온다(설계대로). PASS 카드 2건은 판정 칩뿐이다 |
| 영향 | 요청서의 "예측 기반 판단 지표"가 UI에서 호출되는지에 대한 답은 "검증된 것은 현재 값이 없다"이다. 오류 계산은 아니다. README 문구와 화면이 다르다 |
| 수정안 | 소유자 결정이 필요하다(분할 뒤 QUANTGEN은 연구 전용이고, 매매 아이디어 문구는 TRADEGEN으로 옮겼다). 안 A: Crypto 화면에 "C3 crypto trend 상태" 타일 추가. Upbit KRW-BTC·Binance BTCUSDT 종가에 카드 `rules`의 매개변수로 `S.crypto_trend`를 적용하고, 상태·전환일·카드 판정·"vendor data, not an order" 표시를 붙인다. 합성이면 타일을 숨긴다. 안 B: README `:281`을 "PASS on the scorecard (no live state is displayed)"로 고친다 |
| 회귀 테스트 | 안 A: `tests/expansion_acceptance.py::test_crypto_page_shows_c3_state_with_its_card`(합성 소스에서는 타일 없음, 가짜 Upbit 전송에서는 "C3" 텍스트와 PASS 칩과 "not an order" 존재). 안 B: `tests/macro_ui_components.py`의 README 검사에 "Offered as a signal" 부재 단언 |

#### FC-05 · P3 · 사실 — README 세부 기능 5개가 화면에 없거나 다른 대상을 보인다

| 항목 | 내용 |
|---|---|
| ID | FC-05 |
| 심각도 | P3 |
| 판정 | 사실 |
| 파일·함수·라인 | (1) 가격결정 커널(`README.md:217-218`): `core/ficc/equity_deriv.py:419-426` `pricing_kernel`은 self-check(`:617`)만 호출. 화면 `ui/derivatives_page.py:257-263`은 f_Q와 f_P만, 기본 엔진은 gbm(`:201`)이라 기본 화면에는 f_Q만. f_P도 Quant Lab이 아니라 이 화면의 GARCH 적합(`:128-131`). (2) vertical 차익 수(`README.md:215`): `equity_deriv.py:212-240`이 계산, 화면 `:251-252`와 해설 `:160-161`은 butterfly만. (3) PCA 버터플라이 모니터(`README.md:286-289`): `core/ficc/curve_models.py`의 `butterfly_weights`/`butterfly_signal` 화면 호출 없음. Rates는 단순 fly(`ui/rates_page.py:115`, `core/ficc/curves.py:344`). (4) BTC stationarity share(`README.md:236-237`): 카드 `D_C2_garch_btc`의 `stats.stationarity_share = 0.780`이 Crypto 화면에는 없다(점수표 상세 줄에는 있다). (5) Quant Lab 연구 칩(`README.md:307-308` "beside every fit"): `ui/quant_lab_page.py:165-187`은 기호와 무관하게 SPY·KODEX 200 카드만 보인다. BTC 적합에 `D_C2_*`(REVISE)가 안 보인다 |
| 재현 단계 | `python3 -B -W ignore .../drive_pages.py` → `derivatives/gbm`, `garch_t` 모두 "kernel shown: False | vertical shown: False". 나머지는 grep |
| 기대 결과 | README 문장이 가리키는 수치가 해당 화면에 있다 |
| 실제 결과 | 위 5건 모두 화면에 없거나 다른 대상 |
| 영향 | 기능 목록을 README로 판단하면 과대평가한다. 계산 오류는 아니다 |
| 수정안 | (1) `xc.density_chart`에 `p_samples`가 있으면 보조축에 `pricing_kernel(rnd, p_samples)["kernel"]`을 그리고, 문서를 "GARCH-t 엔진 선택 시"로 고친다. (2) "Butterfly viol." 타일 툴팁에 `call_vertical`/`put_vertical`을 추가. (3) README `:289`에서 "the PCA fly"를 빼거나 Rates 곡선 도구에 `butterfly_signal` z-점수 칩을 단다(카드 REVISE 표시와 함께). (4) Crypto 칩에 `stationarity_share`를 붙인다. (5) `_study_chips(symbol)`로 바꿔 `cost_class(symbol) == "crypto"`면 `D_C2_*`를 보인다 |
| 회귀 테스트 | `test_derivatives_garch_engine_draws_the_kernel`(garch_t 실행 후 차트 수와 "kernel" 범례), `test_quant_lab_study_chips_follow_the_symbol`(`BTC-USD` 합성 실행에 "D_C2" 또는 "bitcoin" 칩) |

#### FC-06 · P3 · 사실 — 화면 실행 경로가 전체 테스트 밖이다

| 항목 | 내용 |
|---|---|
| ID | FC-06 |
| 심각도 | P3 |
| 판정 | 사실 |
| 파일·함수·라인 | `tests/expansion_acceptance.py:323-345`의 `_selfcheck` 목록에 UI는 `strategy_lab_page`(코어 `run_family`만 호출)와 `crypto_page`(`analyze`만)뿐. `ui/{rates,bonds,fx,structuring,macro,derivatives,etf,quant_lab}_page.py`의 `__main__` self-check은 어떤 테스트도 실행하지 않는다. `tests/macro_ui_views.py:264-295`는 Strategy Lab·Signals 페이지를 만들기만 한다. Portfolio 페이지를 만드는 테스트는 없다 |
| 재현 단계 | `grep -rn "_selfcheck(" tests/*.py`; `python3 -B -W ignore .../run_ui_selfchecks.py` → 10개 모두 OK(약 12초, 네트워크 0) |
| 기대 결과 | 화면의 실행 버튼 경로가 회귀 테스트에 있다 |
| 실제 결과 | 위와 같다. FC-01이 이 틈으로 통과했다 |
| 영향 | UI 회귀를 놓친다. 데이터 의존이 아니라 테스트 누락이다(오프라인으로 돈다) |
| 수정안 | 부록 A의 `tests/expansion_acceptance.py` diff: self-check 8개와 FC-01·FC-02 테스트를 `tests()`에 추가. 사본에서 expansion 20 → 30건 모두 통과. README 표(`:872`)의 expansion 수치도 함께 고친다. Portfolio·Signals는 `drive_pages.py`의 방식으로 버튼 클릭 테스트를 추가 |
| 회귀 테스트 | `expansion/selfcheck_ui_{rates_page,…,quant_lab_page}`, `expansion/strategy_lab_run_renders_every_family`, 신규 `test_portfolio_optimize_renders_all_objectives`, `test_signals_analyze_renders_each_strategy`(오류 안내 없음, 이미지 2개 이상, Analysis 카드 존재) |

#### FC-07 · P3 · 사실 — 낡은 문서와 안내 문구

| 항목 | 내용 |
|---|---|
| ID | FC-07 |
| 심각도 | P3 |
| 판정 | 사실 |
| 파일·함수·라인 | (1) `README.md:878` 총계 743/864, `:877` papers 43. 저장 결과는 749/870, papers 49. (2) `main.py:8-9` Quant Lab 모형 목록에 기본값 GARCH-t가 없다(`core/quant/montecarlo.py:66`은 4개, 기본 `garch_t`). `main.py:17-18` "a regime read"는 README `:73-76`의 "not a regime model (P19)"과 어긋난다. (3) `README.md:357, 585-586`, `core/skills/macro_daily.py:1073-1074`(화면의 Open owner actions), `core/quant/gate_package.py:46`, `core/skills/macro_daily.py:351`이 "저장소를 git에 올려라"라고 한다. `README.md:48`은 분할 이후 git 관리 중이라고 한다. 실제 차단은 `core/ficc/macro_artifacts.py:33` `GIT_HASH = "UNVERSIONED"` 상수이며, 분할 명세 `docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:155-158`이 소유자 결정 사항으로 남겼다 |
| 재현 단계 | `python3 -B -c` 로 `qa/acceptance_results.json` 집계(870/749/121). grep "repository under git" |
| 기대 결과 | 문서와 화면 안내가 현재 상태와 실제 차단 요인을 말한다 |
| 실제 결과 | 위와 같다 |
| 영향 | 소유자가 이미 끝난 일(git)을 할 일로 보거나, 진짜 결정(상수를 git HEAD에 묶을지)을 놓친다 |
| 수정안 | README 총계 행을 저장 결과로 갱신하거나 날짜를 붙인 "as of" 문구로 바꾼다. `main.py` docstring을 README와 맞춘다. 안내 문구를 "owner decision pending: tie MA.GIT_HASH / lab.GIT_HASH to the git HEAD (split spec §3.3); the repository is under git since 2026-10-23"로 바꾼다. 같은 문자열을 단언하는 테스트도 함께 고친다: `tests/macro_m7_cards.py:206, 774`, `tests/macro_m7_integration.py:267`, `tests/macro_m7_ledger.py:417`, `tests/macro_m8_pipeline.py:717`, `tests/macro_ui_overlay.py:213` |
| 회귀 테스트 | `tests/macro_ui_components.py::test_readme_carries_both_disclaimers_and_no_stale_counts`에 `"743/864"` 부재와 "under git since" 존재 단언 추가 |

#### FC-08 · P3 · 사실 — Signals 백테스트가 비용표를 쓰지 않는다

| 항목 | 내용 |
|---|---|
| ID | FC-08 |
| 심각도 | P3 |
| 판정 | 사실 |
| 파일·함수·라인 | `ui/signals_page.py:114-115` 비용 기본값 `"10"`, `:136-139` 그대로 `run_backtest`에 전달. `core/quant/backtest.py:108` 기본 10. 비용표 `core/quant/validate.py:78` `COST_BP_PER_SIDE`(US 50, KRX 주식 35). 결과 칩(`ui/signals_page.py:160-170`)에 비용 표시 없음. 비교: Strategy Lab(`ui/strategy_lab_page.py:92-103`)과 ETF(`ui/etf_page.py:84`)는 비용표를 쓴다 |
| 재현 단계 | `drive_pages.py`의 Signals 실행(AAPL, 기본값) → 페이로드 `cost_bps = 10`. 패치 확인 `python3 -B -W ignore .../check_signals_patch.py <root>` |
| 기대 결과 | `README.md:445-453`(P10) "Every backtest … is charged QUANTGEN's per-side costs". P10은 매크로 원칙 절에 있지만 문장은 일반적이다. 최소한 사용한 비용을 화면에 보인다 |
| 실제 결과 | AAPL 백테스트가 10 bp로 계산되고 화면은 비용을 말하지 않는다 |
| 영향 | 같은 기호의 성과가 Signals와 Strategy Lab에서 다른 비용 가정으로 나온다. Signals는 "Context only"라 판정에 쓰이지 않는다 |
| 수정안 | 부록 A의 FC-08 diff: 빈칸이면 `cost_floor_bp([symbol])`의 표 값, 표에 없으면 입력 요구. 칩 "cost 50 bp/side (table)" 추가. 사본 확인: AAPL 빈칸 → 50 (table), 005930 → 35 (table), 10 입력 → 10 (typed). Flet API guard 통과 |
| 회귀 테스트 | `tests/macro_ui_views.py::test_signals_cost_defaults_to_the_table`(합성 AAPL 실행 텍스트에 "cost 50 bp/side (table)") |

## 6. 소유자 메모와 이 차원의 관계

- "(-> FICC/BTC 모두 KIS에서 접근 가능한지 …)": 공급사별 가능 범위와 권장 공급사는 C-01/V-01 보고서 7장(`docs/audit/2026-10-27/c01_v01_cache_and_vendors.md:394-421`)에 있다. 이 보고서는 화면 연결만 본다.
  - FICC: KIS 원화 금리·KTB·원/달러는 데이터 계층에 있으나 FICC 화면에 없다(FC-03). 부록 A의 `load_curve` diff가 가장 작은 연결이다. 가짜 KIS로 화면까지 돈다는 것을 확인했다. 실제 KIS 응답은 미검증이다.
  - BTC: 현물·펀딩은 Upbit·Binance(무키)로 구현돼 Crypto 화면에 연결돼 있다(3장 14행). KIS에는 BTC 현물이 없다. CME BTC 선물 함수(`data/kis_markets.py:514`)는 있으나 라우팅이 없다(C-01 보고서).
- "(-> 공급사필요)"(관측일·발표일 구분): 한국 공식 거시(ECOS·KOSIS) 클라이언트 부재는 C-01 보고서 V01-03이 다룬다. 기능 측면에서는 매크로 시트 18개 지표가 모두 미국·달러 계열이고 한국 지표가 없다는 점만 덧붙인다(`core/ficc/macro.py:61`).

## 7. 미검증 항목

- 실공급자 경로 전부(KIS, FRED, Yahoo, Upbit, Binance, FMP, OpenDART, KRX). 네트워크 규칙상 실행하지 않았다. Crypto live와 Derivatives KIS는 오류 안내 문구만 확인했다.
- 실제 Flet 창에서 `page.run_thread` 예외의 처리(로그 출력 여부). 동기 가짜 page로만 재현했다.
- 매크로 dry run의 US 시장. `yf_SPY.csv`(금지 파일)를 읽어야 해서 실행하지 않았다. KR만 허용 파일 사본으로 실행했다. `macro_ui_overlay`의 dry run 테스트도 저장소를 대상으로는 돌리지 않았다.
- KIS 원화 수익률의 관행(par인지, 이표 주기, 일간 이력 길이). FC-03 패치는 가짜 전송으로만 검증했다.
- gs-quant 설치 경로(이 환경에 없음)와 그 오프라인 계층, 이전 gs-quant 버전의 statsmodels 의존.
- Deep analysis(Claude API) 경로. 키와 네트워크가 없다.
- 제안 패치의 전체 스위트 영향. ficc 57, quant 53, expansion 30, Flet API guard는 사본에서 통과했다. `macro_ui_views`는 부분 사본에서 13/14였고, 실패 1건(`test_research_dnb_37_plus_17_resolutions_12_and_open_buttons_point_at_files`)은 패치 없는 같은 부분 사본에서도 똑같이 실패했다(사본에 없는 파일 때문). macro·engine·safety·paper·papers 전체는 사본에서 돌리지 않았다.
- FC-04 안 A의 코드. 소유자 결정 전이라 작성·검증하지 않았다.

## 8. 재현 스크립트 경로

모두 `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/functional_completeness/` 아래에 있다.

| 파일 | 내용 |
|---|---|
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/functional_completeness/_hermetic.py` | 공용 틀: HOME·macro dir 스크래치, 자격증명 변수 제거, 소켓 차단 |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/functional_completeness/run_ui_selfchecks.py` | 화면 self-check 10개 실행(결과 `ui_selfchecks.log`) |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/functional_completeness/build_all_nav.py` | `main.py` NAV 16개 빌드 |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/functional_completeness/drive_pages.py` | 12개 분석 화면 실행 버튼 구동(결과 `drive_pages.log`) |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/functional_completeness/repro_lab_chart.py` | FC-01: 계열별 차트 실패, 페이지 상태, 장부 선등록 |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/functional_completeness/repro_statsmodels_missing.py` | FC-02: statsmodels 유무 비교 |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/functional_completeness/dry_run_kr.py` | 매크로 KR dry run(허용 파일 사본만)과 Overlay 화면 렌더 |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/functional_completeness/probe_offline_msgs.py` | Crypto live·Derivatives KIS의 오프라인 안내 문구 |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/functional_completeness/make_patch.py` | 부록 A 패치를 스크래치 사본 `patched/`에 적용(줄끝 유지) |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/functional_completeness/regression_tests.py` | 제안 회귀 테스트. 인자로 코드 루트(저장소 또는 `patched`) |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/functional_completeness/run_suites_inprocess.py` | ficc·quant·expansion `tests()`를 프로세스 안에서 실행(결과 `suites_patched.log`). 저장소를 대상으로 `macro_ui_overlay`를 넘기지 말 것(금지 파일을 읽는 dry run 포함) |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/functional_completeness/check_signals_patch.py` | FC-08 패치 확인과 Flet API guard |
| `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/functional_completeness/proposed_fixes.diff` | 부록 A 원본 diff(CRLF 파일의 줄끝 포함) |

재현 순서 예: `cd` 없이 `python3 -B -W ignore <경로>/repro_lab_chart.py`. 패치 검증: `git archive HEAD core data ui config.py main.py docs/asset_expansion/cards docs/quant_lab tests requirements.txt pyproject.toml | tar -x -C <스크래치>/patched` → `python3 -B <경로>/make_patch.py` → `python3 -B -W ignore <경로>/regression_tests.py <스크래치>/patched`.

## 부록 A. 제안 패치 (unified diff, HEAD `859a983` 기준, 미적용)

적용하지 않았다. 아래는 가독성을 위해 CR을 뺀 판이다. `ui/rates_page.py`, `ui/structuring_page.py`, `requirements.txt`, `pyproject.toml`은 CRLF 파일이다. 적용할 때는 `proposed_fixes.diff`(줄끝 포함)를 쓰거나 줄끝을 보존해야 한다. FC-03의 회귀 테스트 본문은 `regression_tests.py`의 `test_krw_curve_source_prices_off_kis_without_synthetic`를 `tests/ficc_acceptance.py`로 옮기면 된다.

```diff
--- a/ui/xcharts.py
+++ b/ui/xcharts.py
@@ -74,10 +74,12 @@
     pal = active()
     fig, ax = _fig(9.5, 3.2, pal)
     x = np.arange(len(dates))
-    eq = np.asarray(equity, dtype=float)
+    # strategies.equity_curve starts with a 1.0 before the first P&L date, one point more than
+    # `dates`: keep the last len(dates) points, so point i is the equity after date i's return.
+    eq = np.asarray(equity, dtype=float)[-x.size:]
     ax.plot(x[-eq.size:], eq, color=pal.accent, linewidth=1.3, label=labels[0])
     if bench is not None:
-        b = np.asarray(bench, dtype=float)
+        b = np.asarray(bench, dtype=float)[-x.size:]
         ax.plot(x[-b.size:], b, color=pal.muted, linewidth=1.0, label=labels[1])
     idx, lab = _thin_dates(list(dates))
     ax.set_xticks(idx); ax.set_xticklabels(lab)
--- a/ui/strategy_lab_page.py
+++ b/ui/strategy_lab_page.py
@@ -227,7 +227,7 @@
     def run(e=None) -> None:
         busy.visible = True; host.controls = []; page.update()
 
-        def worker():
+        def work():
             try:
                 syms = [s.strip() for s in (symbols.value or "").split(",") if s.strip()]
                 r = run_family(family.value or "trend_switch", syms, source=source.value or "auto",
@@ -276,6 +276,13 @@
                                          payload_fn=lambda p=payload(r): p, deep_fn=insights.deep_analysis))
             host.controls = blocks; busy.visible = False; page.update()
 
+        def worker():
+            try:
+                work()
+            except Exception as exc:                  # a render failure must not leave the ring spinning on an empty panel
+                host.controls = [notice(f"{type(exc).__name__}: {exc}", "error", icon=ft.Icons.ERROR_OUTLINE)]
+                busy.visible = False; page.update()
+
         page.run_thread(worker)
 
     lab = ft.Column([
--- a/requirements.txt
+++ b/requirements.txt
@@ -7,6 +7,7 @@
 numpy>=1.26
 pandas>=2.1
 scipy>=1.11
+statsmodels>=0.14   # ADF in core.quant.strategies.adf_pvalue (ETF premium, kimchi, ETH/BTC, pairs)
 matplotlib>=3.8
 gs-quant>=1.0
 # QUANTGEN FICC core — keyless market data (FRED, Yahoo Finance)
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -12,7 +12,7 @@
   "pyyaml>=6.0",
   "requests>=2.31",
   "python-dotenv>=1.0", "tzdata>=2024.1; sys_platform == 'win32'",
-  "numpy>=1.26", "pandas>=2.1", "scipy>=1.11", "matplotlib>=3.8", "gs-quant>=1.0",
+  "numpy>=1.26", "pandas>=2.1", "scipy>=1.11", "statsmodels>=0.14", "matplotlib>=3.8", "gs-quant>=1.0",
   "yfinance>=0.2", "pandas-datareader>=0.10",
 ]
 
--- a/core/crypto/analytics.py
+++ b/core/crypto/analytics.py
@@ -170,9 +170,11 @@
 def eth_btc_test(eth: dict[str, float], btc: dict[str, float]) -> dict:
     dates, (e, b) = _align(eth, btc)
     x = np.log(e / b)
-    return {"n": len(dates), "last_ratio": float(e[-1] / b[-1]), "adf_p": adf_pvalue(x),
+    p = adf_pvalue(x)
+    return {"n": len(dates), "last_ratio": float(e[-1] / b[-1]), "adf_p": p,
             "half_life_days": half_life(x), "z_2y": float((x[-1] - x[-730:].mean()) / x[-730:].std(ddof=1)) if x.size > 100 else float("nan"),
-            "verdict": ("mean-reverting at 5 %" if adf_pvalue(x) < 0.05 else "no rejection of a unit root (the expected null)")}
+            "verdict": ("ADF not run (statsmodels unavailable or the test failed)" if not math.isfinite(p) else
+                        "mean-reverting at 5 %" if p < 0.05 else "no rejection of a unit root (the expected null)")}
 
 
 def weekday_table(dates: Sequence[str], close: np.ndarray, volume: np.ndarray) -> dict:
--- a/core/ficc/data.py
+++ b/core/ficc/data.py
@@ -568,6 +568,18 @@
         return replace(p, note=f"FRED failed: {exc}; simulated curve panel. {p.note}")
 
 
+def load_curve(*, source: str = "auto", days: int = 504) -> CurvePanel:
+    """The FICC pages' curve. `kis_krw` is the KRW par grid from KIS (CD 91d + KTB
+    1/3/5/10/20/30y, `core.ficc.curve_models.krw_curve_panel`); it never falls back to
+    synthetic. Every other source is the UST curve of `load_treasury_curve`."""
+    if source == "kis_krw":
+        if not config.kis_ready():
+            raise FICCError("KIS_APP_KEY / KIS_APP_SECRET are not configured; the KRW curve comes from KIS.")
+        from core.ficc.curve_models import krw_curve_panel
+        return krw_curve_panel(days=days)
+    return load_treasury_curve(source=source, days=days)
+
+
 def _treasury_from_fred(days: int) -> CurvePanel:
     rows, errors = _provider_rows("FRED", list(_TREASURY_IDS), days)
     have = [(i, t) for i, t in zip(_TREASURY_IDS, UST_TENORS) if i in rows]
--- a/ui/rates_page.py
+++ b/ui/rates_page.py
@@ -30,7 +30,7 @@
 from core.ficc.bonds import Bond
 from core.ficc.common import BP, FICCError, parse_forward_tenor, parse_tenor, tenor_label
 from core.ficc.curves import analyze_curve, curve_from_snapshot, curve_pca
-from core.ficc.data import load_short_rate, load_treasury_curve
+from core.ficc.data import load_curve, load_short_rate
 from core.ficc.ratesim import MODELS, calibrate, horizon_pv_distribution, simulate
 from core.ficc.swaps import Swap, Swaption, analyze_swap, price_cap_floor, price_swaption
 from core.theme import RADII
@@ -41,7 +41,8 @@
 _TOOLS = [("curve", "Yield curve"), ("swap", "Swap pricer"),
           ("option", "Swaption / cap-floor"), ("sim", "Rate simulation")]
 _SOURCES = [("auto", "Auto (FRED, synthetic fallback)"), ("fred", "FRED"),
-            ("synthetic", "Synthetic demo")]
+            ("synthetic", "Synthetic demo"),
+            ("kis_krw", "KRW curve (KIS: CD 91d + KTB)")]
 _METHODS = [("bootstrap", "Bootstrap"), ("nelson_siegel", "Nelson-Siegel"),
             ("svensson", "Svensson")]
 _MODEL_LABELS = {"vasicek": "Vasicek", "cir": "CIR", "hull_white": "Hull-White"}
@@ -92,7 +93,7 @@
 
 
 def _curve(source: str, method: str = "bootstrap"):
-    panel = load_treasury_curve(source=source)
+    panel = load_curve(source=source)
     return panel, curve_from_snapshot(panel.latest(), method=method)
 
 
@@ -101,7 +102,7 @@
 # can drive them without a Flet page.
 # --------------------------------------------------------------------------- #
 def _run_curve(page, *, source: str, method: str, lookback: int) -> list[ft.Control]:
-    panel = load_treasury_curve(source=source)
+    panel = load_curve(source=source)
     report = analyze_curve(panel, lookback=lookback, method=method)
     try:
         pca = curve_pca(panel)
@@ -292,6 +293,8 @@
              threshold_pct: float | None, instrument: str, instr_tenor_text: str,
              coupon_pct: float) -> list[ft.Control]:
     """instrument: none | bond | swap — what to revalue at the horizon."""
+    if source == "kis_krw":
+        raise FICCError("Rate simulation is calibrated on SOFR (USD); a KRW overnight series is not wired yet.")
     series = load_short_rate("USD", source=source)
     panel, curve = _curve(source)
     params = calibrate(series, model=model)
--- a/ui/bonds_page.py
+++ b/ui/bonds_page.py
@@ -18,7 +18,7 @@
 from core.ficc.bonds import Bond, analyze_bond, futures_hedge_ratio, scenario_pnl
 from core.ficc.common import FICCError, bp_text, pct_text, tenor_label
 from core.ficc.curves import curve_from_snapshot
-from core.ficc.data import load_treasury_curve
+from core.ficc.data import load_curve
 from core.theme import RADII, active
 from ui import fcharts
 from ui.ai_panel import analysis_panel
@@ -27,7 +27,8 @@
 _TOOLS = [("calc", "Calculator & risk"), ("scenarios", "Scenarios"),
           ("hedge", "Futures hedge")]
 _SOURCES = [("auto", "Auto (FRED, else synthetic)"), ("fred", "FRED"),
-            ("synthetic", "Synthetic demo")]
+            ("synthetic", "Synthetic demo"),
+            ("kis_krw", "KRW curve (KIS: CD 91d + KTB)")]
 _FREQS = [("1", "Annual"), ("2", "Semi-annual"), ("4", "Quarterly")]
 
 
@@ -107,7 +108,7 @@
                 bond = Bond(coupon=_num(coupon, 0.0) / 100.0, maturity=_num(maturity, 10.0),
                             freq=int(freq.value or "2"), notional=_num(notional, 1e6))
                 y = _num(ytm)
-                panel = load_treasury_curve(source=source.value or "auto")
+                panel = load_curve(source=source.value or "auto")
                 curve = curve_from_snapshot(panel.latest())
                 a = analyze_bond(bond, price=_num(price), ytm=None if y is None else y / 100.0,
                                  curve=curve)
--- a/ui/structuring_page.py
+++ b/ui/structuring_page.py
@@ -21,7 +21,7 @@
 from core.ficc import insights, structured
 from core.ficc.common import BP, FICCError, parse_tenor, pct_text, tenor_label
 from core.ficc.curves import curve_from_snapshot
-from core.ficc.data import load_treasury_curve
+from core.ficc.data import load_curve, load_treasury_curve
 from core.theme import RADII, active
 from ui.ai_panel import analysis_panel
 from ui.components import card, chip, empty_state, notice, section, stat
@@ -30,7 +30,8 @@
 _TOOLS = [("ppn", "Principal-protected note"), ("rc", "Reverse convertible"),
           ("dcd", "Dual-currency deposit"), ("steep", "Steepener note")]
 _SOURCES = [("auto", "Auto (FRED, synthetic fallback)"), ("fred", "FRED"),
-            ("synthetic", "Synthetic demo")]
+            ("synthetic", "Synthetic demo"),
+            ("kis_krw", "KRW curve (KIS: CD 91d + KTB)")]
 _DEFAULT_MATURITY = {"ppn": "3y", "rc": "1y", "dcd": "3m", "steep": "5y"}
 
 # Per-product term sheet: (key, label, default text, width). Percent keys are
@@ -266,7 +267,7 @@
                 N = _parse({"n": ("Notional", notional.value)})["n"]
                 fut = _parse({"f": ("Futures DV01 / contract", futures.value)})["f"] \
                     if (futures.value or "").strip() else None
-                panel = load_treasury_curve(source=source.value or "auto")
+                panel = load_curve(source=source.value or "auto")
                 curve = curve_from_snapshot(panel.latest())
                 report = _price(k, curve, maturity=T, notional=N,
                                 underlying=underlying.value or "FX", v=v)
--- a/ui/signals_page.py
+++ b/ui/signals_page.py
@@ -17,6 +17,7 @@
 from core.quant.backtest import STRATEGIES, run_backtest
 from core.quant.history import HistoryError, load_history
 from core.quant.signals import SignalReport, compute_signals
+from core.quant.validate import cost_floor_bp
 from core.quant import insights
 from core.theme import RADII, active
 from ui.ai_panel import analysis_panel
@@ -111,8 +112,9 @@
                           border_radius=RADII["md"],
                           tooltip="ma_cross: slow SMA · rsi_revert: exit-above "
                                   "RSI level · momentum: unused")
-    cost = ft.TextField(label="Cost (bps)", width=100, value="10",
-                        border_radius=RADII["md"])
+    cost = ft.TextField(label="Cost (bps)", width=100, value="", hint_text="table",
+                        border_radius=RADII["md"],
+                        tooltip="Blank charges QUANTGEN's per-side table rate (core.quant.validate.COST_BP_PER_SIDE).")
     busy = ft.ProgressRing(visible=False, width=20, height=20)
     result_host = ft.Column(spacing=14)
 
@@ -135,8 +137,12 @@
                 strat = strategy.value or "ma_cross"
                 hist = load_history(symbol.value, source=source.value or "auto")
                 report = compute_signals(hist)
-                bt = run_backtest(hist, strategy=strat, params=_params(strat),
-                                  cost_bps=float(cost.value or "10"))
+                typed = (cost.value or "").strip()
+                table = cost_floor_bp([hist.symbol])[0]
+                if not typed and table is None:
+                    raise ValueError(f"QUANTGEN has no cost row for {hist.symbol}; type a cost.")
+                cost_used = float(typed) if typed else table
+                bt = run_backtest(hist, strategy=strat, params=_params(strat), cost_bps=cost_used)
             except (HistoryError, ValueError) as exc:
                 result_host.controls = [notice(str(exc), "error",
                                                icon=ft.Icons.ERROR_OUTLINE)]
@@ -166,6 +172,7 @@
                 chip(f"max DD {bt.max_drawdown * 100:.1f}%"),
                 chip(f"exposure {bt.exposure * 100:.0f}%"),
                 chip(f"{bt.n_trades} trades · win {wr}"),
+                chip(f"cost {bt.cost_bps:g} bp/side ({'typed' if typed else 'table'})"),
             ] + ([chip(f"{hist.source}: {hist.note}")]
                  if hist.note and hist.source != "SYNTHETIC" else []), spacing=6, wrap=True))
             blocks.append(card(qcharts.equity_chart(bt)))
--- a/tests/expansion_acceptance.py
+++ b/tests/expansion_acceptance.py
@@ -320,6 +320,46 @@
     assert [V.cost_class(s) for s in ("005930", "005935.KS", "105560", "BTCUSDT", "NAS:AAPL", "A01612", "FX@KRW")] ==         ["krx_stock", "krx_stock", "krx_stock", "crypto", "us", "futures", "fx"], "stocks at 35 bp, not the ETF row"
 
 
+def test_strategy_lab_run_renders_every_family():
+    """FC-01: pressing Run renders a result (chart included) for every family, and a render failure
+    becomes a notice instead of a spinning ring over an empty panel."""
+    from types import SimpleNamespace
+    import flet as ft
+    from ui import strategy_lab_page as S
+
+    def walk(c):
+        yield c
+        for ch in list(getattr(c, "controls", None) or []) + [getattr(c, "content", None)]:
+            if ch is not None and not isinstance(ch, str):
+                yield from walk(ch)
+    root = S.build_strategy_lab_page(SimpleNamespace(run_thread=lambda fn: fn(), update=lambda: None))
+    cs = list(walk(root))
+    dd = {d.label: d for d in cs if isinstance(d, ft.Dropdown)}
+    tf = {t.label: t for t in cs if isinstance(t, ft.TextField)}
+    ring = next(c for c in cs if isinstance(c, ft.ProgressRing))
+    run = next(b for b in cs if isinstance(b, ft.Button) and b.content == "Run")
+    for fam in S.FAMILIES:
+        dd["Family"].value, dd["Source"].value = fam, "synthetic"
+        tf["Symbols (comma)"].value = {"pairs": "AAA, BBB", "crypto_trend": "KRW-BTC"}.get(fam, "AAA, BBB, CCC")
+        tf["Sessions"].value = "1500"
+        run.on_click(None)
+        found = [t.value for t in walk(root) if isinstance(t, ft.Text) and isinstance(t.value, str)]
+        assert not any(t.startswith(("ValueError", "TypeError", "IndexError")) for t in found), (fam, found[:3])
+        assert ring.visible is False and any(isinstance(c, ft.Image) for c in walk(root)), fam
+
+
+def test_eth_btc_verdict_says_not_run_when_adf_is_unavailable():
+    """FC-02: a NaN ADF p-value is 'not run', never 'no rejection of a unit root'."""
+    import core.crypto.analytics as CA
+    d = {(date(2025, 1, 1) + timedelta(days=i)).isoformat(): 100.0 + i for i in range(300)}
+    saved, CA.adf_pvalue = CA.adf_pvalue, (lambda x: float("nan"))
+    try:
+        out = CA.eth_btc_test(d, {k: v * 1.01 for k, v in d.items()})
+    finally:
+        CA.adf_pvalue = saved
+    assert "not run" in out["verdict"], out["verdict"]
+
+
 def tests():
     return [
         ("kis_markets_paging_and_shapes", test_kis_markets_paging_and_shapes),
@@ -342,7 +382,11 @@
         ("selfcheck_vol_products", _selfcheck("core/ficc/vol_products.py")),
         ("selfcheck_crypto_analytics", _selfcheck("core/crypto/analytics.py")),
         ("selfcheck_crypto_page", _selfcheck("ui/crypto_page.py")),
-    ]
+        ("strategy_lab_run_renders_every_family", test_strategy_lab_run_renders_every_family),
+        ("eth_btc_adf_not_run_is_not_a_verdict", test_eth_btc_verdict_says_not_run_when_adf_is_unavailable),
+    ] + [(f"selfcheck_ui_{p}", _selfcheck(f"ui/{p}.py")) for p in
+         ("rates_page", "bonds_page", "fx_page", "structuring_page", "macro_page", "derivatives_page",
+          "etf_page", "quant_lab_page")]
 
 
 if __name__ == "__main__":
```
