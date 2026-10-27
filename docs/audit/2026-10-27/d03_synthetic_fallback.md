# D-03 감사 보고서: 합성 데이터 대체(fallback) 경로와 출처 표시

- 감사일: 2026-10-27
- 감사 차원: `d03_synthetic_fallback` (요청서 4장 D-03, 7장 3번 "합성 데이터 fallback")
- 성격: 감사 전용. 저장소의 추적 파일은 하나도 고치지 않았다. 수정안은 아래 diff로만 제시한다.
- 비밀정보: `.env`를 열지 않았다(이 환경에는 `.env`가 없다). 키·토큰을 출력하지 않았다.
- 네트워크: 시장 데이터 공급자에 실제로 접속하지 않았다. 모든 재현은 스텁과 합성 입력으로 했다.

## 0. 요약

1. 요청서의 D-03 주장은 **사실**이다. `core/ficc/data.py`는 `source="auto"`에서 공급자가 실패하면 합성(SYNTHETIC) 시계열로 바꾼다. `core/quant/history.py`는 자격 증명이 없을 때만 합성으로 바꾼다.
2. 데이터 생산 단계의 표시는 대체로 정확하다. `source="SYNTHETIC"`과 실패 사유가 담긴 `note`가 붙는다. 기존 테스트 5건도 이를 확인한다(재실행 결과 PASS).
3. 문제는 소비 단계다. 출처가 계산 결과 객체로 넘어가지 않는다. 화면마다 따로 배너를 붙인다. 그래서 배너 조건이 어긋나는 경로가 생긴다.
4. 가장 심각한 경로는 Crypto 화면이다(D03-01, P1). FRED의 USD/KRW만 합성으로 바뀌면 김치 프리미엄이 **+1257.30%**로 계산된다. 화면은 녹색 `source: LIVE` 칩을 보여 주고 합성 배너를 띄우지 않는다. 해설과 AI 페이로드에도 합성 표시가 없다.
5. 매크로 시트는 합성 행이 섞이면 기준일(`as_of`)이 오늘 날짜로 바뀐다(D03-02). 실제 데이터는 그보다 오래됐다. 서술형 판독(risk-on 등)도 합성 입력으로 바뀌지만 표시가 없다.
6. `analysis_panel` 호출 지점 19곳 중 14곳은 해설(Analysis 카드 문장)이 합성 여부를 말하지 않는다. Crypto 1곳은 FX만 합성일 때 말하지 않는다(D03-03). Deep analysis 시스템 프롬프트에도 합성 처리 규칙이 없다(D03-04).
7. 실행(acting) 경로는 합성 값을 거부한다. `core/ficc/pit.py:408-409`의 `synthetic_rejected`가 근거다. 실행 모듈이 `auto` 로더를 호출하는 곳은 찾지 못했다.

## 1. 범위

- 생산 지점: `core/ficc/data.py`, `core/quant/history.py`, `core/ficc/macro.py`, `data/`, `core/crypto/`.
- 소비 지점: `ui/` 전 화면, 계산 결과 객체(`core/quant/*`, `core/ficc/*`, `core/crypto/analytics.py`), 로컬 해설(`core/quant/insights.py`, `core/ficc/insights.py`, 각 화면의 `narrative()`), AI 페이로드(`ui/ai_panel.py`), 판정·카드 칩.
- "합성과 비슷한 것"도 포함했다. 공급자 값이 없을 때 하드코딩 상수로 대체하는 경로(파생상품 화면 금리 3%)다.
- 제외: `paper_live/`, `grokteam/` 실행. `paper_live/`는 grep으로 읽기만 했다(합성 로더 사용 없음).

## 2. 방법

1. `synthetic`, `SYNTHETIC`, `source`, `note`를 grep 했다. 모든 로더 호출 지점을 목록으로 만들었다.
2. 각 로더의 반환 객체가 어느 화면, 어느 계산, 어느 해설, 어느 페이로드로 가는지 코드로 따라갔다.
3. 의심 경로마다 작은 스크립트로 재현했다. 네트워크는 하네스가 막는다. 캐시는 끈다(TTL 0, 스크래치 폴더). 키는 프로세스 환경에서 지운다.
4. Flet 화면은 가짜 `page` 객체로 띄우고 버튼을 눌렀다. 그 뒤 컨트롤 트리의 텍스트를 읽어 배너·칩·해설을 확인했다.
5. 기존 테스트 5건은 모듈의 테스트 함수를 스크립트에서 직접 호출했다. `tests/run_all.py`는 실행하지 않았다.
6. 판정 기준: 재현했으면 **사실**. 코드로만 확인했고 실행 결과가 모델 출력 등에 달렸으면 **추정**. 주장과 코드가 다르면 **오류**. 확인 못 하면 **미검증**.

## 3. 요청서·README 주장 검증

| 주장 | 출처 | 판정 | 근거 |
|---|---|---|---|
| FICC 데이터 모듈은 `source='auto'`에서 공급자 실패 시 합성으로 대체한다 | 요청서 D-03 | 사실 | `core/ficc/data.py:539-541`(load_many), `:562-568`(load_treasury_curve), `:613`(load_fx_spot), `:668-671`(load_short_rate). 사유는 `_degraded`(`:506-507`)가 `note`에 넣는다. 재현 R5, R8 |
| source/note 표시 코드가 있다 | 요청서 D-03 | 사실 | `ui/rates_page.py:84-91`, `ui/bonds_page.py:120-126`, `ui/fx_page.py:99-110`, `ui/macro_page.py:121,155-157`, `ui/quant_lab_page.py:305-307`, `ui/signals_page.py:154-156`, `ui/portfolio_page.py:131-144`, `ui/strategy_lab_page.py:243-244`, `ui/etf_page.py:197-198`, `ui/structuring_page.py:137-141`, `ui/derivatives_page.py:225-227`, `ui/crypto_page.py:156-157` |
| 소비 화면이 경고를 놓치면 합성값을 실데이터로 오인할 수 있다 | 요청서 D-03 | 사실 | Crypto 화면에서 실제로 일어난다(D03-01, R1). 매크로 기준일(D03-02, R2), 해설 문장(D03-03, R3)도 해당 |
| SYNTHETIC은 "always labeled ... with a note" | `core/ficc/data.py:10-12` | 사실(생산 단계 한정) | 생산 객체에는 항상 붙는다. 소비 단계에서는 사라지는 경로가 있다(D03-01, D03-03) |
| 설정된 공급자가 실패하면 조용히 시뮬레이션하지 않고 `HistoryError`를 낸다 | `core/quant/history.py:472-474` | 사실 | 합성 대체는 `:491-496`, `:501-506`, `:507-511`의 "자격 증명 없음" 분기뿐이다. 재현 R5(c) |
| 키·네트워크가 없으면 모든 화면이 합성으로 동작하고 "loud banner"로 말한다 | `README.md:745-748` | 오류(부분) | Crypto 화면은 USD/KRW만 합성일 때 배너가 없다(R1). 파생상품 화면의 가정 금리 3%는 `input`으로 표시된다(R6) |
| 명시적으로 고른 공급자가 실패하면 예외를 낸다. `auto`만 대체한다 | `README.md:748-749` | 오류(부분) | FX 화면에서 `Yahoo`(명시)를 골라도 금리 칸은 `auto`로 불러 합성으로 떨어진다(`ui/fx_page.py:71`, R9) |
| 매크로 오버레이는 합성·열화 값이 실행에 쓰이지 않게 한다 | `README.md:750`, `:415-418` | 사실 | `core/ficc/pit.py:408-409`가 비-context 역할의 합성·auto 값을 `synthetic_rejected`로 거부한다. 기존 테스트 `test_syn_01_synthetic_rejected_for_acting_allowed_for_context` PASS(R0) |

## 4. 합성 대체가 일어나는 지점(생산자 목록)

| # | 파일:라인 | 트리거 | 반환 | 단위·형태 |
|---|---|---|---|---|
| S1 | `core/ficc/data.py:539-541` `load_many` | `auto`, id별 공급자 실패 또는 관측치 5개 미만 | `synthetic_series(kind=_synthetic_kind(id))` | rate는 소수(0.04). FRED 실데이터는 퍼센트 원값(4.2) |
| S2 | `core/ficc/data.py:547-549` `load_series` | S1과 같음 | S1 | S1 |
| S3 | `core/ficc/data.py:562-568` `load_treasury_curve` | `auto`, FRED 곡선 실패 | `synthetic_curve_panel` | 소수 |
| S4 | `core/ficc/data.py:599-613` `load_fx_spot` | `auto`, Yahoo 실패 | `synthetic_fx` | 현실적 시작값(EURUSD 1.10 등) |
| S5 | `core/ficc/data.py:645-671` `load_short_rate`, `:674-676` `load_policy_rates` | `auto`, FRED 실패 | `_synthetic_short_rate` | 소수, 월간은 월초 날짜 |
| S6 | `core/ficc/macro.py:154-157,202-224` `macro_sheet` | `auto`, S1을 id별로 사용 | 행 단위 SYNTHETIC | `synthetic_ids`에 기록 |
| S7 | `core/quant/history.py:491-496` | 6자리 KRX 코드, KIS 미설정 | `synthetic_history` | GBM 주가형 |
| S8 | `core/quant/history.py:501-506` | KIS 도메인 기호(`NAS:AAPL`, `Y0101`, 채권 ISIN, `FX@KRW`, 선물), KIS 미설정 | `synthetic_history` | 수익률·환율도 GBM 주가형(R5c) |
| S9 | `core/quant/history.py:507-511` | 그 밖의 기호, FMP 키 없음 | `synthetic_history` | GBM 주가형 |
| S10 | `ui/etf_page.py:100-103` | 레버리지 ETF, KIS 없음 | `synthetic_history("KOSPI200")` | `index_source="synthetic index"` |
| S11 | `ui/crypto_page.py:52` | Crypto `live`에서 FRED `DEXKOUS` 실패 | S2 경유 합성 | 수준형(10~100대) 랜덤워크(R1, R5b) |
| S12 | `ui/derivatives_page.py:71,79` | KIS 보드, 금리 칸 공란, CD 91d(Y0112) 없음 | 상수 3% | 라벨 `"input"`(R6) |
| S13 | `ui/quant_lab_page.py:80-99` | rf가 FRED가 아니면 | 상수 3% | 칩에 "assumed" 표시. 합성 rf는 거부(양호) |

명시적 `source="synthetic"` 선택은 사용자가 고른 데모다. 위 목록에서 뺐다.

## 5. 소비 경로 추적 매트릭스

| 소비 경로 | 입력 | 배너 | 출처 칩 | 로컬 해설에 표시 | AI 페이로드의 출처 | 판정류 칩 |
|---|---|---|---|---|---|---|
| Rates / curve `rates_page.py:103-153` | S3 | 있음 `:111` | muted `:91,122` | 있음 `ficc/insights.py:102` | `source` | — |
| Rates / swap `:156-197` | S3 | 있음 `:167` | muted | **없음** | `curve_source` | — |
| Rates / swaption·cap `:200-288` | S3 | 있음 `:209` | muted | **없음** | `curve_source` | — |
| Rates / simulation `:291-358` | S3+S5 | 있음 `:311-312` | muted | **없음** | `series.source`, `curve_source` | — |
| Bonds `bonds_page.py:104-200` | S3 | 있음 `:122-124` | muted `:126` | **없음** | `data_source` | — |
| Structuring `structuring_page.py:137-211` | S3 | 있음 `:139-141` | muted `:157` | **없음** | `curve.source` | — |
| FX forward·option·carry `fx_page.py:183-371` | S4+S5 | 있음 `:105-110` | muted `:100-102` | **없음** | forward만 금리 출처, option은 spot만 | — |
| Macro sheet `macro_page.py:153-182` | S6 | 있음 `:155-157` | 행 Source 열 error `:121` | 있음 | `synthetic_ids` | 판독 칩·헤드라인 타일에 **없음** |
| Quant Lab `quant_lab_page.py:268-380` | S7·S9 | 있음 `:305-307` | muted `:323-325` | **없음** | `data_source` | 저장된 M9 등급 칩 `:333` |
| Signals `signals_page.py:133-198` | S7·S9 | 있음 `:154-156` | — | **없음** | `data_source` | 전략 수익 칩 |
| Portfolio `portfolio_page.py:100-198` | S7·S9 | 있음 `:133-138` | muted `:143-144` | **없음** | `synthetic_symbols` | — |
| Strategy Lab `strategy_lab_page.py:230-277` | S7·S9 | 있음 `:243-244` | muted `:257-259` | **없음** | `sources` | 결정 칩 `:251`(보류 안 됨) |
| ETF `etf_page.py:188-248` | S7·S9·S10 | 있음 `:197-198` | muted `:212` | 있음 `:163-164` | `data_source` | 연구 판정 칩 `:233-236` |
| **Crypto live(FX만 합성)** `crypto_page.py:142-199` | S11 | **없음**(`:156` 조건은 전체 합성일 때만) | 녹색 `LIVE` + 기본 muted `USD/KRW` | **없음** | **`source: LIVE`, FX 출처 키 없음** | 연구 판정 칩 |
| **Derivatives KIS(CD 없음)** `derivatives_page.py:52-136` | S12 | 없음 | `rate 3.00% (input)` | `(input)` | **`rate_source` 키 없음** | — |

양호한 통제(발견사항 아님, 사실):
- 합성 결과는 캐시에 쓰지 않는다(`core/ficc/data.py:27-28,531-534`; 테스트 PASS).
- 실행 입력은 PIT 저장소에서 합성·auto 값을 거부한다(`core/ficc/pit.py:408-409`).
- context 로그는 합성 항목을 빼고 경보를 남긴다(`core/ficc/context_log.py:501-510,841-842`).
- Strategy Lab은 합성 실행을 시험 원장에 등록하지 않는다(`ui/strategy_lab_page.py:60-61`; R7에서 `ledger_n=None`).
- 연구 스크립트는 합성 입력이면 중단한다(`docs/asset_expansion_study.py:397-399`).
- Quant Lab은 합성 rf를 쓰지 않고 3% 가정으로 바꾸며 칩에 적는다(`ui/quant_lab_page.py:86-99`).
- 실행 모듈(`core.quant.`, `core.engine.`, `core.rules.` 등)에서 `load_history`, `load_many` 등 `auto` 로더 호출은 없다(grep). 이 모듈들은 `History`를 인자로 받기만 한다.

## 6. 발견사항

### 6.1 요약 표

| ID | 심각도 | 판정 | 위치 | 한 줄 요약 |
|---|---|---|---|---|
| D03-01 | P1 | 사실 | `ui/crypto_page.py:45-62,118-131,156-160` | USD/KRW만 합성일 때 김치 프리미엄 +1257%를 `LIVE`로 표시. 배너·해설·페이로드 모두 표시 없음 |
| D03-02 | P2 | 사실 | `core/ficc/macro.py:170-224`, `ui/macro_page.py:161-168` | 합성 행이 매크로 기준일을 오늘로 당김. 판독 칩·요약·헤드라인 타일에 합성 표시 없음. 실패 사유 미표시 |
| D03-03 | P2 | 사실 | `core/ficc/insights.py:105-327,512-545`, `core/quant/insights.py:138-257`, 결과 데이터클래스 15종 | Analysis 카드 19곳 중 14곳(+Crypto 조건부 1곳)의 해설이 합성을 말하지 않음. 결과 객체에 출처 필드 없음 |
| D03-04 | P2 | 사실(프롬프트)·추정(AI 출력) | `core/quant/insights.py:263-282`, `ui/ai_panel.py:40-58` | Deep analysis 시스템 프롬프트에 합성 처리 규칙 없음. 결과 카드에 합성 배지 없음 |
| D03-05 | P2 | 사실 | `ui/derivatives_page.py:71,79,178-181` | CD 91d가 없으면 하드코딩 3%를 `input`으로 표시. 페이로드에 `rate_source` 없음 |
| D03-06 | P3 | 사실 | `core/ficc/data.py:311-352,539-541`, `core/quant/history.py:501-506` | 대체되면 같은 id의 단위·규모가 바뀜(퍼센트→소수 100배, 환율 1380→100대, 수익률→주가형). `Series`에 단위 필드 없음 |
| D03-07 | P3 | 사실 | `core/ficc/data.py:233-265,449-495` | TTL을 조금 넘긴 실제 캐시가 있어도 공급자 실패 시 합성을 반환 |
| D03-08 | P3 | 사실 | `ui/*` 출처 칩, `core/ficc/data.py:288-295`, `core/quant/history.py:250-257` | 합성 칩 색 규칙이 화면마다 다름(대부분 muted, 매크로만 error). 합성 날짜가 오늘로 끝나 실데이터보다 최신처럼 보임 |
| D03-09 | P3 | 사실 | `ui/strategy_lab_page.py:98-104,249-251`, `ui/quant_lab_page.py:333` | 합성 입력 옆에 판정·등급 칩(결정, 저장된 M9 PASS)을 그대로 표시 |
| D03-10 | P3 | 사실 | `ui/fx_page.py:66-72,310-311` | FX 화면에서 `Yahoo`(명시)를 골라도 금리는 `auto`로 합성 대체 |

### 6.2 상세

#### D03-01 · P1 · 사실 — Crypto 화면: 합성 USD/KRW로 계산한 김치 프리미엄을 `LIVE`로 표시

| 필드 | 내용 |
|---|---|
| 파일·함수·라인 | `ui/crypto_page.py` `_live` `:45-57`(특히 `:52` `load_series("DEXKOUS", source="auto")`, `:57` `"source": "LIVE"`), `analyze` `:60-63`, `narrative` `:100-120`(`:118` 전체 합성일 때만 표시), `payload` `:123-131`(`usdkrw_source` 없음), 화면 `:156-160`(배너 조건 `a["source"] == "SYNTHETIC"`, `USD/KRW` 칩은 기본 muted). 합성 형태는 `core/ficc/data.py:311-317`(`DEXKOUS`→`level`), `:346-349`(10~100 랜덤워크) |
| 재현 단계 | `python3 -B /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/d03_synthetic_fallback/r1_crypto_dexkous.py`. FRED는 실패 스텁. Upbit/Binance는 스텁(BTC 약 60,000 USDT, Upbit = Binance × 1,380 × 1.01, 즉 실제 프리미엄 +1.00%). 화면은 가짜 `page`로 띄우고 Refresh를 누름 |
| 기대 결과 | 실환율이 없으면 김치 프리미엄을 계산하지 않거나, 계산하더라도 오류색 배너와 해설·페이로드에 합성 입력을 명시. 출처 칩은 `LIVE`가 아니어야 함 |
| 실제 결과 | `DEXKOUS` 합성값 last 106.12(범위 85.0~110.73, 실제는 약 1,380). `kimchi last_pct = +1257.30 %`. `a['source']='LIVE'`, `usdkrw_source='SYNTHETIC'`. 페이로드에 `usdkrw_source` 키 없음, JSON 어디에도 `SYNTHETIC` 없음. 해설 첫 문장 "Korea pays +1257.30 % against the world price…", 합성 언급 없음. 화면에 합성 배너 없음. 칩은 `source: LIVE`(success 녹색)와 `USD/KRW: SYNTHETIC`(기본 muted) |
| 영향 | 화면의 핵심 수치가 실제의 1,000배 이상 틀린다. 녹색 LIVE 칩이 출처를 보증하는 것처럼 보인다. z-score(-0.3), 반감기 같은 부속 통계는 정상처럼 보여 오류를 숨긴다. Deep analysis는 LIVE 데이터로 알고 해설한다. 주문 경로가 없으므로 P0는 아니다. FRED는 키 없이 쓰이므로 FRED만 막힌 환경(방화벽, FRED 장애, `pandas_datareader` 오류)에서 일어날 수 있다(빈도는 미검증) |
| 수정안 | 7.1 diff. (1) `auto` 대신 실환율 체인: KIS `FX@KRW`(`data/kis_markets.py:64,496-497`, KIS 설정 시) → FRED `DEXKOUS` 명시 호출 → 실패 시 김치 프리미엄 계산 거부. (2) `analyze`가 `kimchi=None`과 `kimchi_error`를 돌려주고 화면은 오류 배너를 띄움. (3) 페이로드에 `usdkrw_source` 추가. (4) `source`는 모든 다리가 실데이터일 때만 `LIVE` |
| 회귀 테스트 | `test_d03_crypto_live_never_prices_kimchi_on_synthetic_fx`: FRED 실패 스텁 + 크립토 스텁에서 `a = analyze(source="live")`. `assert a["kimchi"] is None and "USD/KRW" in a["kimchi_error"]` 또는 `assert a["usdkrw_source"] != "SYNTHETIC"`. `assert "usdkrw_source" in payload(a)`. 화면 텍스트에 `"Kimchi premium not computed"` 배너가 있어야 함 |

#### D03-02 · P2 · 사실 — 매크로 시트: 합성 행이 기준일을 오늘로 당기고, 판독에 합성 표시가 없다

| 필드 | 내용 |
|---|---|
| 파일·함수·라인 | `core/ficc/macro.py` `macro_sheet` `:223`(`as_of=max(r.last_date for r in rows)`), `_regime_from` `:170-199`(요약 문자열에 합성 표시 없음), `_row` `:128-139`(`MacroRow`에 `note` 없음). 합성 날짜 `core/ficc/data.py:288-295`(오늘의 평일로 끝남). 화면 `ui/macro_page.py:161-163`(as of 칩), `:164-165`(판독 칩·요약), `:166-169`(헤드라인 타일, 출처 없음). 해설 `core/ficc/insights.py:380-406`("Daily read for {as_of}") |
| 재현 단계 | `python3 -B …/d03_synthetic_fallback/r2_macro_asof.py`. FRED·Yahoo 스텁은 2026-10-23(금)까지 데이터. 1차: 전부 정상. 2차: `DGS10`, `BAMLH0A0HYM2`만 실패 |
| 기대 결과 | 기준일은 실데이터 행의 최신일(2026-10-23). 합성 입력이 들어간 판독(curve·risk)은 그 사실을 표시. 헤드라인 타일도 합성 표시. 실패 사유를 볼 수 있음 |
| 실제 결과 | 정상 시 `as_of 2026-10-23`. 2개 실패 시 `as_of 2026-10-27`(오늘). 출처별 최종일: FRED 10-23, YFINANCE 10-23, SYNTHETIC 10-27. 판독이 `neutral→risk-on`, `unchanged→bull flattener`로 바뀜. 요약 문자열에 `SYNTHETIC` 없음. 해설 첫 줄 "Daily read for 2026-10-27". 화면 칩 `as of 2026-10-27`. 배너는 있음("2/18 indicators are SYNTHETIC: DGS10, BAMLH0A0HYM2"). 실패 사유("FRED failed …")는 화면 어디에도 없음. `UST 10y`, `HY OAS` 타일은 일반 타일과 같은 모양 |
| 영향 | 기준일이 실제 데이터보다 최신처럼 보인다(D-04와 겹침). 일간·주간 리포트 프롬프트는 "Date the note to as_of"(`core/ficc/insights.py:559,573`)를 지시하므로 AI 리포트 날짜도 틀린다. 판독 칩(risk-on 등)은 합성 입력이 결정했는데 표시가 없다. 배너는 있으므로 P1은 아니다 |
| 수정안 | 7.2 diff. `as_of`는 비합성 행에서만 계산. `_regime_from`이 쓴 입력 중 합성 id를 요약에 붙임. `MacroRow.note` 추가, Source 셀 툴팁에 사유. 헤드라인 타일에 `· SYNTHETIC`과 오류색 |
| 회귀 테스트 | `test_d03_macro_as_of_ignores_synthetic_rows`: 부분 실패 스텁에서 `assert sheet.as_of == max(r.last_date for r in sheet.rows if r.source != "SYNTHETIC")`. `test_d03_macro_read_names_synthetic_inputs`: `assert "SYNTHETIC" in sheet.regime.summary` (입력 id가 합성일 때), 전부 실데이터면 `not in` |

#### D03-03 · P2 · 사실 — 로컬 해설과 결과 객체가 출처를 잃는다

| 필드 | 내용 |
|---|---|
| 파일·함수·라인 | 표시 없음: `core/ficc/insights.py` `narrate_bond:105`, `narrate_swap:142`, `narrate_swaption:162`, `narrate_cap_floor:187`, `narrate_fx_forward:208`, `narrate_fx_option:227`, `narrate_carry:256`, `narrate_ratesim:300`, `narrate_structured:512`; `core/quant/insights.py` `narrate_monte_carlo:138`, `narrate_signals:196`, `narrate_backtest:213`, `narrate_portfolio:238`; `ui/strategy_lab_page.py:139-145`; `ui/derivatives_page.py:139-175`. 표시 있음: `narrate_curve:102`, `narrate_macro:372-375`, `narrate_daily_brief:405-406`, `narrate_weekly_strategy:502-504`, `ui/etf_page.py:163-164`, `ui/crypto_page.py:118-119`(전체 합성일 때만). 결과 클래스 중 `source` 필드가 있는 것은 `YieldCurve`뿐. `MCResult`, `BacktestResult`, `SignalReport`, `RiskReport`, `OptimizedPortfolio`, `SwapReport`, `SwaptionReport`, `CapFloorReport`, `RateSimResult`, `HorizonPV`, `GKReport`, `CarryBacktest`, `BondAnalytics`, `ProductReport`, `KimchiPremium`에는 없다(AST 확인) |
| 재현 단계 | `python3 -B …/d03_synthetic_fallback/r3_narratives.py`. FRED·Yahoo 실패, 키 없음. Rates 화면은 모듈 수준 워커를 직접 실행하고 Analysis 카드 문장을 읽음. 나머지는 화면이 호출하는 해설 함수를 같은 객체로 호출 |
| 기대 결과 | 입력에 합성이 있으면 Analysis 카드 문장 자체가 그것을 말함. 배너와 떨어져 복사·인용돼도 출처가 남음 |
| 실제 결과 | 배너는 모두 있음. 해설의 합성 표시: rates/curve True; rates/swap·swaption·cap·sim False; quant_lab/monte_carlo, signals, portfolio False; fx/forward·option·carry False. 즉 측정한 11개 중 10개가 False. 코드로 본 bonds, structuring, strategy lab, derivatives 해설도 표시 없음(`narrate_bond`의 `note`는 곡선 출처를 담지 않음, `core/ficc/bonds.py:242-253`). `analysis_panel` 호출 지점 19곳(`grep`) 기준으로 항상 표시 있음 4곳(rates curve, macro sheet, macro daily·weekly, ETF), 조건부 1곳(Crypto), 표시 없음 14곳 |
| 영향 | 해설은 선택 가능한 텍스트다(`selectable=True`, `ui/ai_panel.py:71`). 복사하거나 화면 아래쪽만 보면 합성 수치가 시장 판독처럼 읽힌다. carry 해설은 합성 데이터로 "Latest basket: long …; short …"를 말한다. 출처가 결과 객체에 없으므로 새 화면을 만들 때마다 배너를 다시 짜야 한다. 이 구조가 D03-01을 낳았다 |
| 수정안 | 7.3 diff. 1단계: `analysis_panel(..., synthetic=[...])` 규칙 하나로 해설 앞에 합성 문장을 붙이고 배지를 단다. 각 화면은 이미 아는 출처를 넘긴다. 2단계: 결과 데이터클래스에 `sources: tuple[str, ...] = ()`(기본값으로 위치 생성자 호환)를 추가하고 계산 함수가 입력의 `source`를 전파 |
| 회귀 테스트 | `test_d03_every_analysis_panel_labels_synthetic`: 오프라인 `auto`에서 각 화면 워커(rates 5, fx 3, quant lab, signals, portfolio, strategy lab, bonds, structuring, derivatives synthetic)의 마지막 블록 텍스트에 대해 `assert "SYNTHETIC" in narrative_text`. 실데이터 스텁에서는 `not in` |

#### D03-04 · P2 · 사실(프롬프트)·추정(AI 출력) — Deep analysis에 합성 처리 규칙이 없다

| 필드 | 내용 |
|---|---|
| 파일·함수·라인 | `core/quant/insights.py` `_SYSTEM` `:263-282`(synthetic, simulated, source 언급 없음), `deep_analysis` `:299-341`. `ui/ai_panel.py:45-54`(결과 카드에 `engine:` 칩만, 합성 배지 없음). FICC 리포트 두 종류만 `synthetic_ids` 표시를 지시(`core/ficc/insights.py:559,573`) |
| 재현 단계 | `python3 -B …/d03_synthetic_fallback/r4_deep_request.py`. 더미 키 문자열로 버튼만 활성화. `_requests.post`를 기록기로 바꿔 요청을 가로챔(전송 없음). Rates swaption과 simulation 화면의 Deep analysis 버튼을 누름 |
| 기대 결과 | 시스템 프롬프트가 합성 입력이면 첫 문장에서 밝히라고 지시. 페이로드에 합성 목록이 표준 키로 들어감. 결과 카드에 배지 |
| 실제 결과 | 두 경우 모두 시스템 프롬프트에 합성 관련 규칙 없음(False). 페이로드에는 `curve_source: SYNTHETIC`(및 `series.source`)이 있음. swaption 페이로드에는 실패 사유가 없음. Crypto 페이로드는 `source: LIVE`이고 FX 출처 키가 없음(R1 [3]) |
| 영향 | 모델이 출처 필드를 무시하면 합성 수치를 시장 판독처럼 쓴 글이 `engine: claude-…` 칩과 함께 나온다. 실제 모델 응답은 호출하지 않았으므로 이 부분은 추정이다 |
| 수정안 | 7.3 diff의 `_SYSTEM` 한 문장 추가, 페이로드 `synthetic_inputs` 표준 키, 결과 카드 배지 |
| 회귀 테스트 | `test_d03_deep_request_declares_synthetic_inputs`: 가로챈 요청에서 `assert "synthetic_inputs" in payload and payload["synthetic_inputs"]` 그리고 `assert "SYNTHETIC" in req["system"]`(규칙 문장 존재) |

#### D03-05 · P2 · 사실 — 파생상품 화면: 하드코딩 3%를 `input`으로 표시

| 필드 | 내용 |
|---|---|
| 파일·함수·라인 | `ui/derivatives_page.py` `snapshot` `:71`(`cd`가 없으면 0.03), `:79`(`rate_source=("CD 91d (KIS)" if rate_pct is None and cd else "input")`), `payload` `:178-181`(`rate_source` 없음), 칩 `:233`, 해설 `:148-149` |
| 재현 단계 | `python3 -B …/d03_synthetic_fallback/r6_derivatives_rate.py`. `config.kis_ready`를 True로, `KISMarkets`를 스텁으로 교체. `krw_yields_snapshot()`은 Y0112 없이 반환. 금리 칸 공란 |
| 기대 결과 | 라벨 `ASSUMED 3.00% (KIS returned no CD 91d)`와 경고색. 페이로드에 `rate_source` |
| 실제 결과 | `rate used = 0.0300`, `rate_source = 'input'`. 해설 "fair value at 3.00% (input) is 1127.85, so the contract is cheap by 8 bp". 페이로드에 `rate_source` 없음 |
| 영향 | 사용자가 넣지 않은 값을 사용자 입력으로 표시한다. 선물 공정가·미스프라이싱(bp)·박스 금리 비교가 가정값에 달렸는데 출처가 틀리게 적힌다 |
| 수정안 | 7.4 diff |
| 회귀 테스트 | `test_d03_derivatives_assumed_rate_is_labeled`: 같은 스텁에서 `assert s["rate_source"].startswith("ASSUMED")` 그리고 `assert payload(s)["rate_source"] == s["rate_source"]` |

#### D03-06 · P3 · 사실 — 대체 시 단위·규모·형태가 바뀐다

| 필드 | 내용 |
|---|---|
| 파일·함수·라인 | `core/ficc/data.py:20-22`(FRED는 퍼센트 원값), `:311-317`(`_synthetic_kind`), `:330-339`(rate는 소수), `:346-349`(level 10~100), `:539-541`. `Series`(`:77-84`)에 단위 필드 없음. `core/quant/history.py:501-506`(KIS 도메인 수익률·채권·환율 → GBM 주가형) |
| 재현 단계 | `python3 -B …/d03_synthetic_fallback/r5_units_kind.py` |
| 기대 결과 | 같은 id는 대체돼도 같은 단위와 비슷한 규모. 또는 단위가 객체에 명시돼 소비자가 출처가 아닌 단위로 변환 |
| 실제 결과 | `DGS10` FRED last 4.2210, 대체 0.0386(109배 차이), `Series`에 `unit` 없음. `DEXKOUS` 103.41(실제 약 1,380), `DEXJPUS` 51.95(약 150), `DEXUSEU` 91.28(약 1.08). `load_history("Y0101")` 377.30, `KR103501GE31` 401.27, `FX@KRW` 231.26 |
| 영향 | 지금은 소비자가 `source == "FRED"`로 단위를 분기해 막는다(`core/ficc/macro.py:131-132,171-176`, `ui/quant_lab_page.py:89-95`). 이 규칙을 모르는 새 소비자는 100배 오류를 낸다. 실제로 D03-01이 규모 불일치에서 생겼다 |
| 수정안 | 7.5. `Series.unit` 추가(기본 ""), 로더가 채움, 소비자는 `unit`으로 변환. FRED 경유 FX id에 현실적 시작값 표(`_FX_START`와 같은 방식). KIS 도메인 기호(`Y0`, 채권 ISIN, `FX@`)는 KIS가 없으면 합성 대신 `HistoryError` |
| 회귀 테스트 | `test_d03_fallback_keeps_unit`: FRED 스텁(4.2)과 실패의 두 결과에 대해 `assert live.unit == syn.unit` 또는 `0.2 < live.last / syn.last < 5`. `test_d03_kis_domain_without_kis_raises`: `load_history("Y0101", source="auto")`가 KIS 미설정에서 `HistoryError` |

#### D03-07 · P3 · 사실 — 조금 지난 실제 캐시보다 합성을 우선한다

| 필드 | 내용 |
|---|---|
| 파일·함수·라인 | `core/ficc/data.py` `_cache_get` `:233-265`(TTL 지나면 None), `_provider_rows` `:449-495`(실패 시 오래된 캐시를 다시 보지 않음), `load_many` `:539-541` |
| 재현 단계 | `python3 -B …/d03_synthetic_fallback/r8_stale_cache_vs_synthetic.py`. 스크래치 캐시에 2시간 된 실제 `DGS10` 파일, TTL 1시간, FRED 실패 |
| 기대 결과 | 실제지만 오래된 값을 `stale` 표시와 함께 반환. 또는 최소한 선택지로 제공 |
| 실제 결과 | 실제 행 60개가 있는데도 `source=SYNTHETIC`, last 0.0386 반환 |
| 영향 | 일시적 장애 때 실제 값 대신 시뮬레이터 값이 나온다. 표시는 되지만 정보 손실이 크다. C-01(캐시)과 겹친다 |
| 수정안 | `_cache_get(key, allow_stale=True)` 경로 추가. `_provider_rows`가 실패 id에 대해 오래된 캐시를 찾고, 찾으면 행과 함께 `stale` 사유를 돌려줌. `Series.note`에 `STALE cache written <UTC ts>; FRED failed: …`. 출처는 FRED 유지, 상태 필드(`status="stale"`)로 구분. PIT 경로(`not_before`)에는 적용하지 않음 |
| 회귀 테스트 | `test_d03_stale_real_cache_beats_synthetic`: 같은 설정에서 `assert s.source == "FRED" and "STALE" in s.note` |

#### D03-08 · P3 · 사실 — 출처 배지 규칙이 화면마다 다르고, 합성 날짜가 최신처럼 보인다

| 필드 | 내용 |
|---|---|
| 파일·함수·라인 | 합성 칩 색: muted — `ui/rates_page.py:91`, `ui/fx_page.py:100-102`, `ui/quant_lab_page.py:323-325`, `ui/portfolio_page.py:143-144`, `ui/strategy_lab_page.py:257-259`, `ui/etf_page.py:212`, `ui/bonds_page.py:126`, `ui/structuring_page.py:157`, `ui/crypto_page.py:158-159`(USD/KRW는 기본값 muted). error — `ui/macro_page.py:121,162`. 실데이터는 success(녹색). `chip` 기본 토큰 muted(`ui/components.py:30`). 합성 날짜: `core/ficc/data.py:288-295`, `core/quant/history.py:250-257` |
| 재현 단계 | 코드 확인. R1의 칩 출력(`source: LIVE` 녹색, `USD/KRW: SYNTHETIC` muted). R2·R5의 `last_date=2026-10-27` |
| 기대 결과 | 하나의 규칙: SYNTHETIC은 오류색과 단어("simulated"), ASSUMED는 경고색, 실데이터는 성공색. 날짜 칩은 합성이면 "simulated to"로 표기 |
| 실제 결과 | 합성 칩이 실데이터 칩(녹색)보다 눈에 덜 띈다. 합성 날짜 칩 `… → 2026-10-27`이 실데이터(10-23)보다 최신으로 보인다 |
| 영향 | 배너를 놓친 사용자에게 칩이 반대 신호를 준다. v2 어휘 표(`ui/components.py:138-176`)와 같은 방식의 출처 어휘가 없다 |
| 수정안 | 7.6 diff: `SOURCE_STYLE`과 `source_chip()`을 `ui/components.py`에 추가하고 각 화면의 `_src_chip`, `_chips`를 교체 |
| 회귀 테스트 | `test_d03_source_chip_rule`: `source_chip("curve", "SYNTHETIC")`의 텍스트에 `"SYNTHETIC"`과 `"simulated"`, 테두리 색이 `active().error`. `"ASSUMED 3%"`는 `warning`, `"FRED"`는 `success`. 정적 테스트: `ui/` 안에서 `"muted" if … == "SYNTHETIC"` 패턴 0건 |

#### D03-09 · P3 · 사실 — 합성 입력 옆에 판정·등급 칩을 그대로 보인다

| 필드 | 내용 |
|---|---|
| 파일·함수·라인 | `ui/strategy_lab_page.py:98-104`(보류 조건은 비용뿐), `:249-251`(결정 칩), `:148-155`(페이로드 결정). `ui/quant_lab_page.py:333`(`_grade_blocks(_lab_grade(symbol))`를 출처와 무관하게 표시). `ui/etf_page.py:233-236`, `ui/crypto_page.py:160` |
| 재현 단계 | `python3 -B …/d03_synthetic_fallback/r7_verdicts_on_synthetic.py` |
| 기대 결과 | 입력에 합성이 있으면 게이트 결정을 보류(`WITHHELD`). 저장된 실데이터 등급은 합성 적합 결과 옆에 두지 않거나 "이 실행과 무관" 표시 |
| 실제 결과 | Strategy Lab: sources 전부 SYNTHETIC, `withheld False`, 결정 `INSUFFICIENT_DATA`가 칩과 페이로드에 그대로. 해설에 SYNTHETIC 없음. 원장 등록은 안 함(`ledger_n None`, 양호). Quant Lab: `069500`이 SYNTHETIC인데 저장된 등급 `PASS` 칩을 같은 결과 영역에 표시 |
| 영향 | 배너("the verdict below is a toy")는 있다. 그래도 결정 칩이 PASS·REJECT 색으로 나오면 판정처럼 읽힌다. Quant Lab에서는 합성 팬 차트와 실데이터 PASS 등급이 한 화면에 섞인다 |
| 수정안 | 7.7 diff |
| 회귀 테스트 | `test_d03_strategy_lab_withholds_verdict_on_synthetic`: `assert payload(run_family(..., source="synthetic"))["decision"] == "WITHHELD"`. `test_d03_quant_lab_hides_stored_grade_on_synthetic`: 합성 실행 화면 텍스트에 `"M9 gate"` 없음 |

#### D03-10 · P3 · 사실 — FX 화면: 명시 공급자를 골라도 금리는 합성으로 대체

| 필드 | 내용 |
|---|---|
| 파일·함수·라인 | `ui/fx_page.py` `_rate` `:66-72`(`"synthetic"`이 아니면 항상 `"auto"`), `do_carry` `:310-311`, 선택지 `:40-41` |
| 재현 단계 | `python3 -B …/d03_synthetic_fallback/r9_fx_explicit_yahoo.py` |
| 기대 결과 | `Yahoo`(명시)를 고르면 spot처럼 금리도 대체 없이 실패(예외) |
| 실제 결과 | 금리는 `SYNTHETIC` 0.0364 반환. 같은 설정에서 spot은 `FICCError` |
| 영향 | README의 "명시 공급자는 예외" 계약과 다르다. 배너는 뜨므로 영향은 작다 |
| 수정안 | 7.8 diff |
| 회귀 테스트 | `test_d03_fx_explicit_source_does_not_degrade_rates`: FRED 실패에서 `_rate(blank, "USD", "yfinance")`가 `FICCError` |

## 7. 수정안(diff, 적용하지 않음)

공통 원칙(제안):
- **출처 형식 하나.** 모든 시계열과 결과는 `source`(공급자 또는 SYNTHETIC/ASSUMED), `note`(사유), `unit`을 가진다. 여러 입력을 쓴 결과는 입력 출처 목록을 가진다.
- **UI 배지 규칙 하나.** SYNTHETIC은 오류색과 "simulated" 단어, ASSUMED는 경고색, 실데이터는 성공색. 결과 영역 첫 줄 배너, Analysis 카드 첫 문장, Deep analysis 결과 카드 배지, 차트 제목에 같은 표시.
- **거부 규칙.** 실행 경로는 지금처럼 PIT에서 거부한다. 표시 경로에서도 "비율·차이" 지표(김치 프리미엄, basis, 판정)는 한 다리라도 합성이면 계산하지 않거나 판정을 보류한다. `auto`는 "실제 공급자 체인"을 뜻하고, 합성은 사용자가 고른 데모 모드로만 쓰는 방향을 권한다.

### 7.1 D03-01 Crypto

```diff
--- a/ui/crypto_page.py
+++ b/ui/crypto_page.py
@@ -42,19 +42,43 @@ def _synthetic() -> dict:
             "oi": [], "source": "SYNTHETIC"}
 
 
+def _usdkrw(days: int) -> tuple[dict, str]:
+    """USD/KRW from a real fixing only: KIS FX@KRW when KIS is configured, else FRED DEXKOUS asked
+    explicitly (an explicit provider raises). Never the SYNTHETIC fallback of source="auto"."""
+    from core.ficc.data import load_series
+    errors = []
+    if config.kis_ready():
+        try:
+            from data.kis_markets import KISMarkets
+            b = KISMarkets().usdkrw_daily(days=days)
+            return dict(zip(b.dates, b.close)), "KIS FX@KRW"
+        except Exception as exc:
+            errors.append(f"KIS: {type(exc).__name__}: {exc}")
+    try:
+        s = load_series("DEXKOUS", source="fred", days=days)
+        return dict(zip(s.dates, s.values)), "FRED DEXKOUS"
+    except Exception as exc:
+        errors.append(f"FRED: {type(exc).__name__}: {exc}")
+    raise RuntimeError("no real USD/KRW fixing (" + "; ".join(errors) + ")")
+
+
 def _live(days: int) -> dict:
-    from core.ficc.data import load_series
     from data.crypto.crypto_client import BinancePublic, UpbitPublic
     up = UpbitPublic().daily("KRW-BTC", days=days)
     bn = BinancePublic()
     btc = bn.daily("BTCUSDT", days=days)
     fund = bn.funding("BTCUSDT", days=min(days, 1500)).daily()
-    fx = load_series("DEXKOUS", source="auto", days=days + 100)
+    try:
+        usdkrw, usdkrw_source = _usdkrw(days + 100)
+        usdkrw_error = ""
+    except RuntimeError as exc:
+        usdkrw, usdkrw_source, usdkrw_error = {}, "UNAVAILABLE", str(exc)
     return {"dates": btc.dates, "upbit": dict(zip(up.dates, up.close)), "binance": dict(zip(btc.dates, btc.close)),
-            "usdkrw": dict(zip(fx.dates, fx.values)), "usdkrw_source": fx.source, "funding_daily": fund,
+            "usdkrw": usdkrw, "usdkrw_source": usdkrw_source, "usdkrw_error": usdkrw_error, "funding_daily": fund,
             "eth": dict(zip(*(lambda c: (c.dates, c.close))(bn.daily("ETHUSDT", days=days)))),
@@ -60,7 +84,10 @@ def _live(days: int) -> dict:
 def analyze(*, days: int = 730, source: str = "live") -> dict:
     d = _live(days) if source == "live" else _synthetic()
-    out: dict = {"source": d["source"], "usdkrw_source": d.get("usdkrw_source", "synthetic")}
-    out["kimchi"] = CA.kimchi_premium(d["upbit"], d["binance"], d["usdkrw"])
+    out: dict = {"source": d["source"], "usdkrw_source": d.get("usdkrw_source", "SYNTHETIC"),
+                 "kimchi_error": d.get("usdkrw_error", "")}
+    # a premium is a ratio of three prices: computed only when the FX leg is a real fixing (or the whole run is a demo)
+    out["kimchi"] = CA.kimchi_premium(d["upbit"], d["binance"], d["usdkrw"]) if d["usdkrw"] else None
@@ def payload(a: dict) -> dict:
-    return {"source": a["source"], "kimchi": {"last_pct": kp.last_pct, ...
+    return {"source": a["source"], "usdkrw_source": a["usdkrw_source"], "kimchi_error": a.get("kimchi_error", ""),
+            "kimchi": (None if kp is None else {"last_pct": kp.last_pct, ...}),
```

위 `payload` 줄의 `...`는 기존 키를 그대로 둔다는 뜻이다(축약). 화면(`build_crypto_page` worker)과 `narrative`도 같이 바꾼다.
- `kp is None`이면 `notice("Kimchi premium not computed: " + a["kimchi_error"], "error")`를 띄운다. 김치 통계 타일과 차트는 건너뛴다. 해설의 첫 문장도 건너뛴다.
- 배너 조건을 `a["source"] == "SYNTHETIC" or a["usdkrw_source"] in ("SYNTHETIC", "UNAVAILABLE")`로 넓힌다.
- 칩은 7.6의 `source_chip("USD/KRW", a["usdkrw_source"])`를 쓴다.
- 펀딩·GARCH·ETH/BTC·요일 표는 FX가 필요 없으므로 그대로 둔다.

### 7.2 D03-02 매크로

```diff
--- a/core/ficc/macro.py
+++ b/core/ficc/macro.py
@@ def _regime_from(series: dict[str, Series], rows: dict[str, MacroRow]) -> Regime:
     inflation = _trend(rows["T10YIE"].chg_1m, 10 * BP)
     real = _trend(rows["DFII10"].chg_1m, 15 * BP)
+    used = ("DGS10", "DGS2", "VIXCLS", "BAMLH0A0HYM2", "DTWEXBGS", "T10YIE", "DFII10")
+    syn = [i for i in used if i in series and series[i].source == "SYNTHETIC"]
     summary = (f"[{DESCRIPTIVE_READ_NOTE}] "
@@
                f"{(rows['DFII10'].chg_1m or 0) / BP:+.0f}bp).")
+    if syn:
+        summary += f" SYNTHETIC inputs in this read: {', '.join(syn)}."
     return Regime(curve=curve, risk=risk, dollar=dollar, inflation=inflation,
@@ def macro_sheet(*, source: str = "auto", days: int = 504) -> MacroSheet:
-    return MacroSheet(as_of=max(r.last_date for r in rows), rows=rows,
+    live = [r.last_date for r in rows if r.source != "SYNTHETIC"]
+    # a simulated row is dated today by construction: it must not move the sheet's as_of
+    return MacroSheet(as_of=max(live) if live else max(r.last_date for r in rows), rows=rows,
```

```diff
--- a/ui/macro_page.py
+++ b/ui/macro_page.py
@@ def read_row(rg: Regime) -> ft.Row:
         chip(f"real yields: {rg.real_rates}", "accent"),
-    ], spacing=6, wrap=True)
+    ] + ([chip("read uses SYNTHETIC inputs", "error")] if "SYNTHETIC inputs" in rg.summary else []),
+        spacing=6, wrap=True)
@@ def render(sheet: MacroSheet) -> list[ft.Control]:
-        tiles = [stat(r.label, _level(r), tooltip=f"1d {_chg(r, r.chg_1d)}, z {r.z_1y:+.2f}",
-                      token="error" if abs(r.z_1y) >= 2 else "text")
+        tiles = [stat(r.label + (" · SYNTHETIC" if r.source == "SYNTHETIC" else ""), _level(r),
+                      tooltip=f"1d {_chg(r, r.chg_1d)}, z {r.z_1y:+.2f}",
+                      token="error" if (abs(r.z_1y) >= 2 or r.source == "SYNTHETIC") else "text")
```

`MacroRow`에 `note: str = ""`를 끝에 추가하고 `_row`가 `note=s.note`를 넘긴다. 표의 Source 셀 툴팁에 `r.note`를 보인다. 그러면 "FRED failed: …" 사유가 화면에 나온다.

### 7.3 D03-03, D03-04 해설과 Deep analysis

```diff
--- a/ui/ai_panel.py
+++ b/ui/ai_panel.py
@@
 def analysis_panel(page: ft.Page, *, kind: str, narrative: str,
                    payload_fn: Callable[[], dict],
-                   deep_fn: Callable[..., "insights.Analysis"] | None = None) -> ft.Control:
+                   deep_fn: Callable[..., "insights.Analysis"] | None = None,
+                   synthetic: tuple[str, ...] | list[str] = ()) -> ft.Control:
@@
     pal = active()
     deep = deep_fn or insights.deep_analysis
+    synthetic = tuple(synthetic)
+    if synthetic and "SYNTHETIC" not in narrative:
+        narrative = (f"SYNTHETIC inputs ({', '.join(synthetic)}): every number below describes a simulator, "
+                     "not the market. " + narrative)
@@
         def worker():
-            result = deep(kind, payload_fn(), question=question.value or "")
+            result = deep(kind, {**payload_fn(), "synthetic_inputs": list(synthetic)},
+                          question=question.value or "")
@@
                 deep_host.controls = [
-                    ft.Row([chip(f"engine: {result.engine}", "accent")], spacing=6),
+                    ft.Row([chip(f"engine: {result.engine}", "accent")]
+                           + ([chip("SYNTHETIC inputs", "error")] if synthetic else []), spacing=6),
@@
-                chip("engine: local", "muted")], spacing=8),
+                chip("engine: local", "muted")]
+               + ([chip("SYNTHETIC inputs", "error")] if synthetic else []), spacing=8),
```

```diff
--- a/core/quant/insights.py
+++ b/core/quant/insights.py
@@ _SYSTEM = (
-    "headers, no bullet lists, no disclaimers about being an AI. If the "
-    "operator's question asks for a report format, follow that format."
+    "headers, no bullet lists, no disclaimers about being an AI. If the "
+    "operator's question asks for a report format, follow that format. "
+    "If synthetic_inputs is non-empty, or any field named source, data_source, "
+    "curve_source or usdkrw_source is SYNTHETIC, ASSUMED or UNAVAILABLE, open with "
+    "one sentence that says so, and treat those numbers as properties of a simulator "
+    "or an assumption, never as market observations."
 )
```

화면 호출 예(나머지 화면도 같은 방식):

```diff
--- a/ui/rates_page.py
+++ b/ui/rates_page.py
@@ def _run_swap(...)
     blocks.append(analysis_panel(page, kind="rates_swap",
                                  narrative=insights.narrate_swap(rep),
-                                 payload_fn=lambda p=payload: p))
+                                 payload_fn=lambda p=payload: p,
+                                 synthetic=["UST curve"] if panel.source == "SYNTHETIC" else []))
```

2단계(권장): 결과 데이터클래스 15종 끝에 `sources: tuple[str, ...] = ()`를 추가한다. 계산 함수가 입력 `History.source`, `YieldCurve.source`, `Series.source`를 모은다. 그러면 화면이 출처를 따로 들고 다닐 필요가 없다.

### 7.4 D03-05 파생상품 금리 라벨

```diff
--- a/ui/derivatives_page.py
+++ b/ui/derivatives_page.py
@@ def snapshot(...)
         rate = (rate_pct / 100.0) if rate_pct is not None else (cd / 100.0 if cd else 0.03)
+        rate_source = ("input" if rate_pct is not None else "CD 91d (KIS)" if cd
+                       else "ASSUMED 3.00% (KIS returned no CD 91d)")
@@
-                   rate=rate, rate_source=("CD 91d (KIS)" if rate_pct is None and cd else "input"), T=T,
+                   rate=rate, rate_source=rate_source, T=T,
@@ def payload(s: dict) -> dict:
-            "rate": s["rate"], "forward": s["F"], "k0": s["k0"], "futures": s["futures"],
+            "rate": s["rate"], "rate_source": s["rate_source"], "forward": s["F"], "k0": s["k0"],
+            "futures": s["futures"],
```

화면 칩 `:233`은 `rate_source`가 `ASSUMED`로 시작하면 `warning` 토큰을 쓴다.

### 7.5 D03-06 단위

```diff
--- a/core/ficc/data.py
+++ b/core/ficc/data.py
@@ class Series:
     values: tuple[float, ...]
     note: str = ""
+    unit: str = ""                    # "pct" (FRED raw) | "decimal" | "level" | "price" | "fx"; "" = unknown
@@ def synthetic_series(...)
-    return Series(id=id, label=id, source="SYNTHETIC", dates=_business_dates(days),
+    return Series(id=id, label=id, source="SYNTHETIC", dates=_business_dates(days),
+                  unit={"rate": "decimal", "price": "price", "level": "level"}[kind],
```

- `_series_from_rows`는 FRED이고 `_synthetic_kind(id) == "rate"`면 `unit="pct"`를 넣는다.
- `load_short_rate`의 `.scaled(0.01)` 뒤에는 `unit="decimal"`.
- `macro._row`와 `_regime_from.chg`는 `s.source == "FRED"` 대신 `s.unit == "pct"`로 변환한다.
- FRED 경유 FX id(`DEXKOUS`, `DEXJPUS`, `DEXUSEU`)는 `_FX_START` 같은 시작값 표를 쓴다.
- `core/quant/history.py:501-506`은 KIS 도메인 기호에 대해 합성 대신 `HistoryError("KIS credentials are not configured …")`를 낸다. 수익률·채권·환율을 주가형 GBM으로 흉내 내지 않는다.

### 7.6 D03-08 배지 규칙

```diff
--- a/ui/components.py
+++ b/ui/components.py
@@ INPUT_STATUS_STYLE ... (뒤에 추가)
+SOURCE_TOKEN: dict[str, str] = {"SYNTHETIC": "error", "UNAVAILABLE": "error", "ASSUMED": "warning"}
+
+
+def source_chip(label: str, source: str, *, note: str = "") -> ft.Container:
+    """The one provenance badge. SYNTHETIC and UNAVAILABLE are error-toned and say so in words; an assumed
+    constant is warning-toned; a provider is success-toned. Same rule on every page (D-03)."""
+    s = str(source or "unknown")
+    token = next((t for k, t in SOURCE_TOKEN.items() if s.upper().startswith(k)), "success")
+    text = f"{label}: {s}" + (" · simulated, not market data" if s.upper() == "SYNTHETIC" else "")
+    return chip(text, token, tooltip=note)
```

각 화면의 `_src_chip`(`ui/rates_page.py:90-91`), `_chips`(`ui/fx_page.py:99-102`)와 인라인 출처 칩을 `source_chip`으로 바꾼다. 합성 날짜 칩은 `"simulated to {last_date}"`로 표기한다.

### 7.7 D03-09 판정 보류

```diff
--- a/ui/strategy_lab_page.py
+++ b/ui/strategy_lab_page.py
@@ def run_family(...)
-    withheld = ("" if floor is not None and cost_bps >= floor else
+    hists = [load_history(s, source=source, days=days) for s in symbols]
+    synthetic = [h.symbol for h in hists if h.source == "SYNTHETIC"]
+    withheld = (f"No PASS / REJECT: {', '.join(synthetic)} are SYNTHETIC, so this run tests the code, not a market."
+                if synthetic else "" if floor is not None and cost_bps >= floor else
@@
-    hists = [load_history(s, source=source, days=days) for s in symbols]
```

```diff
--- a/ui/quant_lab_page.py
+++ b/ui/quant_lab_page.py
@@
-            blocks.extend(_grade_blocks(_lab_grade(symbol.value or "")))
+            if hist.source != "SYNTHETIC":                 # a stored real-data grade is not a grade of this demo fan
+                blocks.extend(_grade_blocks(_lab_grade(symbol.value or "")))
```

ETF·Crypto의 연구 판정 칩은 데이터가 합성이면 `"study verdict (real data, not this run)"` 툴팁을 붙이거나 숨긴다.

### 7.8 D03-10 FX 명시 공급자

```diff
--- a/ui/fx_page.py
+++ b/ui/fx_page.py
@@ def _rate(field: ft.TextField, ccy: str, source: str) -> tuple[float, Series | None]:
-    s = load_short_rate(ccy, source="synthetic" if source == "synthetic" else "auto")
+    # an explicit spot provider means "live only": rates are then asked of FRED explicitly, and raise
+    s = load_short_rate(ccy, source={"synthetic": "synthetic", "auto": "auto"}.get(source, "fred"))
@@ def do_carry() -> list[ft.Control]:
-        rates = load_policy_rates(list(G10_KRW), days=days,
-                                  source="synthetic" if src == "synthetic" else "auto")
+        rates = load_policy_rates(list(G10_KRW), days=days,
+                                  source={"synthetic": "synthetic", "auto": "auto"}.get(src, "fred"))
```

### 7.9 실행 경로 거부의 회귀 고정

지금 실행 모듈은 `auto` 로더를 부르지 않는다(사실, grep). 이를 테스트로 고정할 것을 권한다. `core/ficc/context_log.py:71-83`의 `ACTING_MODULE_PREFIXES` 정적 스캔에 금지 호출 목록을 더한다: `load_history`, `load_many`, `load_series`, `load_fx_spot`, `load_short_rate`, `load_policy_rates`, `load_treasury_curve`, `synthetic_history`, `synthetic_series`, `synthetic_fx`, `synthetic_curve_panel`.

## 8. 회귀 테스트 제안(새 모듈 `tests/d03_provenance.py`, 작성하지 않음)

모두 기존 `tests/ficc_acceptance.py`의 `_no_network()` 방식으로 밀폐한다.

| 테스트 이름 | 핵심 assertion |
|---|---|
| `test_d03_crypto_live_never_prices_kimchi_on_synthetic_fx` | FRED 실패 + 크립토 스텁: `a["kimchi"] is None` 또는 `a["usdkrw_source"] != "SYNTHETIC"`. `"usdkrw_source" in payload(a)` |
| `test_d03_macro_as_of_ignores_synthetic_rows` | `sheet.as_of == max(비합성 행 last_date)` |
| `test_d03_macro_read_names_synthetic_inputs` | 판독 입력이 합성이면 `"SYNTHETIC" in sheet.regime.summary` |
| `test_d03_every_analysis_panel_labels_synthetic` | 오프라인 `auto`의 모든 화면 워커에서 Analysis 문장에 `"SYNTHETIC"` |
| `test_d03_deep_request_declares_synthetic_inputs` | 가로챈 요청: `payload["synthetic_inputs"]` 비어 있지 않음, 시스템 프롬프트에 규칙 문장 |
| `test_d03_derivatives_assumed_rate_is_labeled` | `s["rate_source"].startswith("ASSUMED")`, 페이로드에 같은 값 |
| `test_d03_fallback_keeps_unit` | `live.unit == syn.unit`(또는 비율 0.2~5) |
| `test_d03_kis_domain_without_kis_raises` | `load_history("Y0101", source="auto")` → `HistoryError` |
| `test_d03_stale_real_cache_beats_synthetic` | `s.source == "FRED" and "STALE" in s.note` |
| `test_d03_source_chip_rule` | SYNTHETIC→error+"simulated", ASSUMED→warning, FRED→success |
| `test_d03_strategy_lab_withholds_verdict_on_synthetic` | `payload(r)["decision"] == "WITHHELD"` |
| `test_d03_quant_lab_hides_stored_grade_on_synthetic` | 합성 실행 화면 텍스트에 `"M9 gate"` 없음 |
| `test_d03_fx_explicit_source_does_not_degrade_rates` | `_rate(blank, "USD", "yfinance")` → `FICCError` |
| `test_d03_no_acting_module_calls_auto_loaders` | 실행 모듈 AST 스캔에서 금지 호출 0건 |

## 9. 소유자 메모와의 관계("공급사 필요", "FICC/BTC를 KIS에서 받을 수 있는지")

D-03의 근본 원인은 `auto`에 두 번째 실제 공급자가 없다는 점이다. 공급자 선정 전체는 다른 차원의 과제다. 여기서는 D-03에 바로 쓰이는 사실만 적는다. 코드 근거이며 실제 접속은 미검증이다.
- KIS 코드에는 원화 FICC 경로가 있다: 국고채 수익률 `Y01xx`, CD 91d `Y0112`(`data/kis_markets.py:56-60`), 원/달러 `FX@KRW`(`:64,496-497`), KRX 선물·옵션, 채권 ISIN 일별. 미국 금리는 KIS 코드에 UST 10y·30y와 Fed funds(`US_YIELD_CODES`, `:61`)만 있다. 1m~30y 전체 곡선, SOFR, 신용 OAS는 코드상 FRED뿐이다.
- BTC는 KIS 코드에 없다. 크립토는 키 없는 Upbit·Binance 공개 API다(`data/crypto/crypto_client.py:134-275`).
- 그래서 D03-01의 USD/KRW는 7.1처럼 KIS `FX@KRW` → FRED `DEXKOUS`(명시) → 거부 순서가 가장 단순하다. 합성은 체인에 넣지 않는다.

## 10. 미검증 항목

- 실제 공급자(FRED, Yahoo, KIS, FMP, Upbit, Binance)의 응답과 장애 빈도. 네트워크를 쓰지 않았다. 따라서 D03-01이 현실에서 얼마나 자주 일어나는지는 미검증이다.
- Deep analysis의 실제 모델 응답. 요청만 가로챘고 모델은 호출하지 않았다(D03-04의 출력 부분은 추정).
- 화면의 실제 시각적 두드러짐(색 대비, 배너 위치). 컨트롤 트리 텍스트만 읽었고 렌더링 화면은 보지 않았다.
- KIS `krw_yields_snapshot()`이 실제로 Y0112를 빠뜨리는 경우가 있는지. R6은 스텁으로 경로만 재현했다.
- KIS `FX@KRW`, Yahoo `KRW=X`의 실제 가용성·발표 시각, FRED `DEXKOUS`의 발표 지연(D-04 범위).
- `ui/trading_page.py`, `ui/krx_page.py`, `ui/rules_page.py`, `ui/settings_page.py`, `ui/research_view.py`, `ui/macro_state_panel.py`, `ui/macro_cards_view.py`는 grep으로 합성 로더 사용이 없음을 확인했다. 화면 실행은 하지 않았다.
- `grokteam/`은 열지 않았다. `paper_live/`는 grep만 했다(합성 로더 사용 없음).
- 전체 테스트는 다시 돌리지 않았다. 관련 기존 테스트 5건만 함수 단위로 실행했다(모두 PASS, R0).

## 11. 재현 스크립트 경로

모두 저장소 밖 스크래치 폴더에 있다. 실행: `python3 -B <경로>`.

- 하네스(네트워크 차단, 캐시 끔, 키 제거): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/d03_synthetic_fallback/_harness.py`
- R0 기존 테스트 5건: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/d03_synthetic_fallback/r0_existing_tests.py`
- R1 Crypto USD/KRW(D03-01, D03-08): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/d03_synthetic_fallback/r1_crypto_dexkous.py`
- R2 매크로 기준일·판독(D03-02): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/d03_synthetic_fallback/r2_macro_asof.py`
- R3 해설 표시(D03-03): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/d03_synthetic_fallback/r3_narratives.py`
- R4 Deep analysis 요청(D03-04): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/d03_synthetic_fallback/r4_deep_request.py`
- R5 단위·형태·날짜(D03-06, D03-08): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/d03_synthetic_fallback/r5_units_kind.py`
- R6 파생상품 금리 라벨(D03-05): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/d03_synthetic_fallback/r6_derivatives_rate.py`
- R7 판정·등급 칩(D03-09): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/d03_synthetic_fallback/r7_verdicts_on_synthetic.py`
- R8 오래된 캐시 대 합성(D03-07): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/d03_synthetic_fallback/r8_stale_cache_vs_synthetic.py`
- R9 FX 명시 공급자(D03-10): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/d03_synthetic_fallback/r9_fx_explicit_yahoo.py`
