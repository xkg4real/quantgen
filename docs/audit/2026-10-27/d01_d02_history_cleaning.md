# D-01·D-02 감사 보고서: 가격 이력 정제(_clean_rows)와 중복 날짜

> 복원 메모 (오케스트레이터): 하네스가 조사 에이전트의 보고서 파일 쓰기를 거부했습니다. 이 파일은 그 에이전트가 반환한 구조화 결과(요약, 발견사항, 미검증 항목)를 내용 변경 없이 옮긴 것입니다. 원본은 워크플로 저널 `wf_4ff8dbcc-e3c`에 있습니다.

## 요약 (조사 에이전트 원문)

[D-01·D-02 가격 이력 정제 감사 | 커밋 fdc1728 | 감사만 수행, 추적 파일 무수정]

■ 범위: core/quant/history.py(_clean_rows, fmp/kis/yf/crypto/kis_market/synthetic_history, _cached, load_history, History.log_returns/simple_returns), data/crypto/crypto_client.py(Candles.to_history, Upbit/Binance daily), data/kis_markets.py(_bars, _page_back, Bars.to_history, overseas_chart), data/krx/kis_client.py(_f, daily), core/ficc/data.py(_yf_fetch, _fred_fetch, _provider_rows), 하류(risk, montecarlo, signals, backtest, optimize, strategies.align_panel, crypto/analytics._align, UI 작업자), 캘린더(core/calendars legacy JSON, clocks, data/*.yaml).

■ 방법: 코드 직접 대조(파일:라인). 재현 스크립트는 스크래치에서 python3 -B, 네트워크 0건(공급자 전송부 전부 가짜), 자격증명 함수 패치·미출력, .env 미개봉, 캐시는 NEXTGEN_FICC_CACHE로 스크래치. 실데이터는 docs/asset_expansion/cache 허용 파일 42개만(금지 4개는 이름 검사로 제외, 미개봉; git archive 복사본에서도 열지 않고 삭제). 패치는 git archive HEAD 복사본 2벌(tree, tree_patched) 중 tree_patched에만 적용해 시험. tests/run_all.py 미실행. 저장소에 git apply --check(쓰기 없음) 통과.

■ 요청서 주장 판정
- D-01 "_clean_rows가 None·>0만 검사 후 정렬" = 사실(history.py:97-102, 98행 `c is not None and c > 0`). "inf가 남음" = 사실(+inf, 1e400, np.float64 inf 생존). "비유한 값이 수익률·변동성·시뮬레이션에 전파" = 사실. "NaN 검사 없음" = 부분 사실: _clean_rows 안에서는 nan>0이 거짓이라 우연히 제거(무기록), 그러나 가상자산·KIS 비주식·캐시 경로로는 NaN이 History에 들어감.
- D-02 "중복 날짜 제거 없음" = 사실(_clean_rows). 단 "시스템 전체에 없음"은 부분 오류: KIS·Upbit·Binance·_bars는 dict로 암묵 제거하나 규칙이 경로마다 다름(유지/먼저/나중), 기록 없음.
- "관측 간격 검증 필요" = 사실: History 경로에 없음. clocks.completeness_check(core/calendars/clocks.py:389)는 테스트에서만 호출.

■ 핵심 영향(재현): 중간 inf 1개 → analyze_history vol=nan, Sharpe=0, VaR 1d는 유한(3.6%)이라 정상처럼 보임; MC sigma=nan, var_pct=0(montecarlo.py:327 max(0.0,nan)=0.0) → 화면에 VaR 0%; 백테스트 nan; 바스켓 최적화가 경고 없이 [0.5,0.5]. 마지막 값 inf면 signals "strong bullish". 같은 날짜 2배 값 1행 → 단일자산 vol 0.329→0.939, MC VaR 13.5%→36.0%; 바스켓은 dict로 나중 행만 사용(화면 간 불일치). 실데이터: CL=F 2020-04-20 종가 -37.63이 기록 없이 사라지고 04-17→04-21 -60.2%가 1세션으로; Yahoo KS 개별주 2025-09-19 결측, KS ETF 2024-10-30·2024-11-05 결측(1세션으로 계산), 2007~08 휴장일 행 11개 중 10개가 전일 종가 반복. KRX 캘린더(legacy KRX.json, draft holidays_KRX.yaml)에 2026-06-03·2026-07-17 휴장일 없음(추정).

■ 데이터 흐름(정제 진입점): FMP·KIS주식·Yahoo는 _clean_rows 통과(inf 생존, ≤0 무기록 삭제, 중복은 FMP·Yahoo 유지 / KIS 페이지 안 나중·페이지 사이 먼저). 가상자산(Candles.to_history)·KIS 비주식(Bars.to_history)·캐시(_cached)는 _clean_rows 우회. FICC _provider_rows는 sorted만(Yahoo inf·중복 통과).

■ 정제 정책 제안: (1) 단일 진입점 clean_rows(rows, positive, label) → (dates, closes, CleanReport); 모든 공급자·to_history·FICC(_tidy, positive=False)가 사용, 캐시는 읽을 때 _well_formed 실패 시 재조회. (2) 실수만 수용, bool 거부, NaN/±inf 제거·카운트. (3) 가격 ≤0은 제거하되 날짜를 note에 명시, 금리(positive=False)는 유지. (4) 날짜 ISO 정규화(YYYYMMDD·ISO datetime 허용), 해석 불가 제거·카운트, 엄격 오름차순. (5) 중복: 같은 값→병합·카운트; 마지막 세션만 값 다름→나중 행 유지+note(진행 중 봉 재발행); 그 외 충돌→HistoryError(두 값 명시, fail closed). 전 구간 keep-last를 택하지 않은 이유: FMP 응답은 최신순이라 '나중 행'이 최신 개정이 아님. 공급자 우선순위는 History(단일 공급자)가 아니라 이미 PIT 저장소(core/ficc/pit.py:331-337 _best_per_obs)가 담당. (6) 급등락 |ln r|>max(25%, 8×1.4826×MAD)는 note에 날짜만, 삭제 금지(요청서 §6). (7) 캘린더 대비 결측·비세션 행은 보고만(채우거나 지우지 않음), 커버리지 밖은 '판정 불가 일수', CRYPTO는 매일 세션. (8) log_returns/simple_returns는 비유한·≤0 가격에서 ValueError(UI가 이미 ValueError를 알림으로 표시: ui/quant_lab_page.py:291-295, ui/portfolio_page.py:118-122). (9) 모든 처리 결과는 History.note(캐시 note 포함)에 기록. __post_init__ 불변식 강제안은 기존 픽스처(tests/quant_acceptance.py:487-488 반복 날짜, tests/macro_m1_pit.py:354 "d")가 깨지므로 기각.

■ 제안 패치(미적용): core/quant/history.py(clean_rows, CleanReport, _iso_day, _spikes, _well_formed, gap_report, _gap_note, History.from_rows, _checked_prices; fmp/kis/yf 경로 교체; _cached 재검증·gap note), data/kis_markets.py(_bars에 math.isfinite·positive 플래그, overseas_chart의 CHART_YIELD는 positive=False, Bars.to_history→History.from_rows), data/crypto/crypto_client.py(Candles.to_history→History.from_rows), core/ficc/data.py(_tidy로 _provider_rows 정제), 새 tests/history_cleaning_acceptance.py(12건). history.py는 저장소에서 CRLF 줄끝 — 바이트 그대로 diff가 git apply --check 통과. 성능 참고: 504행 clean_rows 1.19 ms, 약 730일 gap_report 0.84 ms.

■ 시험 결과(스크래치 복사본, 프로세스 내 tests() 호출, 저장소 결과 파일 무변경): 묶음 quant(53)·ficc(57)·expansion(20)·macro 중 m1_pit/m9_lab/m1_integration(42 PASS, 11 NOT_RUN). HEAD 복사본 172 PASS/11 NOT_RUN/0 FAIL → 패치 복사본 184 PASS(신규 12 포함)/11 NOT_RUN/0 FAIL, 기존 테스트 상태 변화 0건. 신규 모듈은 HEAD 코드에서 ImportError(clean_rows 없음)로 실패. 나머지 묶음(safety, engine, ui, paper, grokteam, guard, papers, macro 나머지)은 패치로 돌리지 않음.

■ 재현 스크립트·산출물(모두 /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/d01_d02_history_cleaning/): r01_clean_rows.py(+r01_out.txt) 값·날짜 검사; r02_provider_paths.py(+r02_out.txt, r02_after_out.txt) 공급자 경로·캐시; r03_downstream.py(+r03_out.txt) 하류 전파; r04_cache_scan.py(+r04_out.txt) 허용 캐시 42개 스캔; r05_ks_detail.py(+r05_out.txt) KS 결측·휴장일 행; r06_clf_negative.py(+r06_out.txt) CL=F 음수; r07_gaps.py(+r07_out.txt) 결측·연율화·캘린더 커버리지; r08_before_after.py(+r08_out.txt) HEAD 대 패치; apply_patch.py(저장소 경로면 거부); proposed_d01_d02.diff / proposed_d01_d02_lf.diff; run_subset.py, subset_before.json, subset_after.json, subset_after.log; tree/, tree_patched/(git archive 복사본, 금지 4개 파일 제거). 실행 예: cd /home/user/quantgen && python3 -B <위 경로>/r03_downstream.py, 패치 복사본은 QG_ROOT=<위 경로>/tree_patched 지정.

■ 보고서 파일: 하네스가 서브에이전트의 보고서 파일 쓰기를 거부해서 docs/audit/2026-10-27/d01_d02_history_cleaning.md는 만들지 못했다. 우회하지 않았다. 본문은 이 결과(summary, findings, unverified)에 모두 들어 있다. 오케스트레이터가 이 내용으로 파일을 써야 한다.

- **제안 diff (미적용):** `scratchpad/audit_work/d01_d02_history_cleaning/proposed_d01_d02.diff` (바이트 그대로, CRLF 보존) 및 `proposed_d01_d02_lf.diff`. 저장소에는 적용하지 않았습니다.

## 발견사항 상세

### D12-01 (P1, 사실)

- **심각도:** P1
- **판정:** 사실
- **파일·함수·라인:** core/quant/history.py _clean_rows 97-102 (98행 `c is not None and c > 0`); 호출부 fmp_history 178, kis_history 221, yf_history 275; History.log_returns 88-90, simple_returns 92-94
- **재현 단계:** cd /home/user/quantgen && python3 -B /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/d01_d02_history_cleaning/r01_clean_rows.py (값 블록); r02_provider_paths.py A(FMP JSON Infinity 토큰·문자열 "inf"), B(KIS _f("inf")), C(Yahoo); r03_downstream.py inf_mid / inf_last
- **기대 결과:** NaN·±inf는 History에 들어가지 않고, 버린 개수가 note에 남는다
- **실제 결과:** +inf, float("1e400"), np.float64("inf")가 남는다. FMP 경로 non_finite=2, KIS 경로 inf 1개 생존. NaN·-inf는 c>0이 거짓이라 빠지지만 기록 없음
- **영향:** inf_mid: analyze_history ann_vol=nan, ann_return=nan, Sharpe=0(nan을 0으로), VaR 1d=3.6%(정상처럼 보임); MC(gbm·garch_t) sigma=nan, var_pct=0 (montecarlo.py:327 max(0.0,nan)=0.0 → 화면 VaR 0%); 백테스트 total=nan; align_histories 공분산 nan → optimize_portfolio가 경고 없이 [0.5,0.5]. inf_last: signals composite 60.15 'strong bullish', last=inf
- **수정안:** clean_rows()로 교체: math.isfinite 검사, CleanReport(non_finite 등)를 History.note에 결합(_with_note). History._checked_prices()로 log_returns/simple_returns가 비유한·≤0에서 ValueError. diff: proposed_d01_d02.diff (core/quant/history.py 부분)
- **회귀 테스트:** tests/history_cleaning_acceptance.py::test_non_finite_and_non_numeric_closes_never_survive_and_are_counted (all finite and >0, rep.non_finite==4, note에 '4 NaN/inf close(s) dropped'); ::test_returns_refuse_a_series_that_is_not_finite_and_positive (inf·nan·0·-1 각각 ValueError)

### D12-02 (P1, 사실)

- **심각도:** P1
- **판정:** 사실
- **파일·함수·라인:** core/quant/history.py:97-102(중복 처리 없음); fmp_history 167-178(유지), yf_history 275(유지), kis_history 208-214(페이지 안 나중 행 덮어씀/페이지 사이 먼저 행), data/kis_markets.py _bars 146-151(나중)·_page_back 186-197(먼저), data/crypto/crypto_client.py Upbit 150-153·Binance 211-214(먼저), core/ficc/data.py:486(sorted만); 소비부 core/quant/risk.py:149, core/quant/strategies.py:63, core/crypto/analytics.py:43-45(dict → 나중 행)
- **재현 단계:** r01_clean_rows.py 날짜 블록(duplicate date A/B: 두 행 모두 남고 입력 순서가 결과 결정); r02 A·C·F(중복 유지), B(KIS 페이지 내 중복: 999.0만 남고 130.0은 무기록 소실), E(_bars 나중 행); r03 dup_mid; r08 dup-mid 2x
- **기대 결과:** 명시된 단일 중복 정책, 모든 경로 동일 규칙, 처리 결과가 note에 기록
- **실제 결과:** 정책 없음, 경로마다 유지/먼저/나중, 기록 없음. 같은 History가 단일자산 계산에선 두 행 모두, 바스켓(dict)에선 나중 행만 사용
- **영향:** r03 dup_mid(같은 날 2배 값 1행): 단일자산 ann_vol 0.329→0.939(2.85배), MC gbm VaR 13.5%→36.0%, 백테스트 세션 300→301, 바스켓 vol 0.949. r08 저변동 시계열 0.108→2.020
- **수정안:** 정책: 같은 값(rel 1e-9) 병합·카운트; 마지막 세션만 값 다르면 나중 행 유지+note; 그 외 충돌은 HistoryError(날짜와 두 값 명시). 공급자 우선순위는 PIT 저장소(core/ficc/pit.py:331-337 _best_per_obs)가 담당. kis_history는 seen 집합으로 페이징하고 모든 행을 clean_rows에 넘기도록 변경(proposed_d01_d02.diff)
- **회귀 테스트:** ::test_identical_rows_of_one_session_merge_and_are_counted (len(ds)==len(set(ds))==40, merged_duplicates==2); ::test_two_different_closes_for_an_earlier_session_raise_and_name_both (HistoryError 메시지에 날짜·120·555·"FMP 'KO'"); ::test_two_different_closes_for_the_last_session_keep_the_later_row_and_say_so (cs[-1]==140.5, note); ::test_every_provider_path_applies_the_rule (KIS 페이지 내 중복 → HistoryError)

### D12-03 (P1, 사실)

- **심각도:** P1
- **판정:** 사실
- **파일·함수·라인:** data/crypto/crypto_client.py Candles.to_history 81-84, UpbitPublic.daily 161 (float(x or 0.0)), BinancePublic.daily 223; data/kis_markets.py Bars.to_history 87-90, _bars 150 (c>0 → inf 통과); core/quant/history.py crypto_history 284-293, kis_market_history 296-318
- **재현 단계:** r02_provider_paths.py D(Upbit trade_price None·0·"NaN", Binance "inf"·"0"·"NaN"), E(_bars "inf"); r08_before_after.py HEAD upbit
- **기대 결과:** 모든 History 생성 경로가 같은 정제 규칙을 거친다
- **실제 결과:** _clean_rows 완전 우회. Upbit: non_finite=1, ≤0=2(결측 가격이 0.0 종가). Binance: non_finite=2, ≤0=1. _bars: inf 1개 생존. note 없음
- **영향:** log(0)=-inf, r08 HEAD upbit zero/nan → vol=nan. KRW-BTC·BTCUSDT는 auto 라우팅(history.py:497-498)으로 Quant Lab·Portfolio·Signals에 직행. Candles를 직접 쓰는 ui/crypto_page.py:53-55(김치 프리미엄)도 0.0 가격을 받음(그 계산은 미검증)
- **수정안:** History.from_rows(symbol, source, dates, closes, note, adjustment, positive) 추가, Candles.to_history·Bars.to_history가 사용; _bars에 math.isfinite. Upbit `or 0.0` 자체는 Candles 소비부에서 별도 수정 권고
- **회귀 테스트:** ::test_every_provider_path_applies_the_rule (Candles 종가 0.0 → History에 0.0 없음, note에 'at or below zero dropped')

### D12-04 (P2, 사실)

- **심각도:** P2
- **판정:** 사실
- **파일·함수·라인:** core/quant/history.py _cached 429-442 (436행 길이만 비교), 452 (json.dumps 기본 allow_nan=True → 비표준 Infinity 토큰)
- **재현 단계:** r02_provider_paths.py G: 첫 호출이 inf 2·중복 1 시리즈를 캐시에 기록, _requests=None으로 둔 두 번째 호출이 파일에서 그대로 반환
- **기대 결과:** 저장본도 정제 규칙을 통과해야 사용, 파일은 표준 JSON
- **실제 결과:** 파일에 Infinity 토큰(엄격 파서 거부), 캐시 적중이 n=41·non_finite=2·dup=1 반환, note엔 'cached …'만
- **영향:** TTL(기본 6시간, config.py:274) 동안 재실행해도 같은 nan; 사용자가 재실행으로 복구 불가
- **수정안:** 읽을 때 _well_formed(ISO 날짜, 엄격 오름차순, 유한 실수) 실패 시 재조회(패치). 추가 권고: 정제 후 json.dumps(allow_nan=False). FICC _cache_get(core/ficc/data.py:236-265)은 C-01 단위에서 확인
- **회귀 테스트:** ::test_a_cache_file_holding_infinity_is_refetched_not_served (Infinity 캐시 파일이 있을 때 fetch 1회 호출, 결과 전부 유한)

### D12-05 (P2, 사실)

- **심각도:** P2
- **판정:** 사실
- **파일·함수·라인:** core/quant/history.py:98; data/kis_markets.py:150
- **재현 단계:** r06_clf_negative.py: 허용 캐시 yf_CL_F.csv 2020-01~06 행을 가짜 _yf_fetch로 yf_history('CL=F')에 투입
- **기대 결과:** 제거는 불가피(로그수익률 불가)해도 날짜·개수를 note에 기록(요청서 §6: 자동 삭제 금지, 경고·검토)
- **실제 결과:** 2020-04-20 종가 -37.63 행이 사라지고 note는 'Yahoo adjusted close'뿐; 2020-04-17→04-21 로그수익률 -0.6017이 1세션으로 계산
- **영향:** 사용자가 시계열이 완전하다고 오인, 극단 사건이 다른 날 수익률로 이동
- **수정안:** CleanReport.non_positive에 날짜 기록, note에 'N close(s) at or below zero dropped (날짜…)'(패치)
- **회귀 테스트:** ::test_a_close_at_or_below_zero_is_dropped_and_named_unless_the_series_is_a_rate (rep.non_positive==('2026-01-11','2026-01-12'), note 문구, positive=False면 -37.63·0.0 유지)

### D12-06 (P2, 사실)

- **심각도:** P2
- **판정:** 사실
- **파일·함수·라인:** core/quant/history.py 전체(급등락 검사 없음); core/quant/montecarlo.py _simulate_jump 132-140(3σ 분리만, 경고 없음)
- **재현 단계:** r08_before_after.py 'spike 3x'(하루만 3배)
- **기대 결과:** 급등락은 삭제하지 않고 경고·검토 대상(요청서 §6)
- **실제 결과:** HEAD: vol 3.227, note 추가 없음
- **영향:** 데이터 오류성 급등(단위·분할 누락)과 실제 사건을 구분할 단서가 화면에 없음
- **수정안:** _spikes(): |ln r| > max(25%, 8×1.4826×MAD) 날짜를 note에 기록, 값 유지(패치). r04 스캔상 VIX는 25% 초과 61일이라 MAD 하한이 오탐 완화
- **회귀 테스트:** ::test_a_large_move_is_flagged_and_kept (400.0 유지, 두 날짜가 rep.spikes에, note에 'kept, check it')

### D12-07 (P2, 사실)

- **심각도:** P2
- **판정:** 사실
- **파일·함수·라인:** core/quant/history.py 전체(간격 검사 없음); core/calendars/clocks.py:389 completeness_check는 tests/macro_m1_calendars.py:700-705에서만 호출; core/quant/risk.py:75 gs_quant 분기는 실제 날짜 대신 bdate_range 사용
- **재현 단계:** r04_cache_scan.py, r05_ks_detail.py(허용 파일만), r07_gaps.py(합성)
- **기대 결과:** 캘린더 대비 결측 세션·비거래일 행을 보고(채우거나 지우지 않음)
- **실제 결과:** 보고 없음. 실데이터: KS 개별주 2025-09-19 결측(09-18→09-22 +3.91%가 1세션), KS ETF 2024-10-30·2024-11-05 결측, 069500은 2007년 이후 574세션 결측, 2007~08 휴장일 행 11개 중 10개가 전일 종가 반복. 합성: 504세션 중 50 결측 → ann_vol 0.1916→0.2047(+6.8%)
- **영향:** 변동성 과대, 바스켓 교집합(risk.py:140-143)에서 행이 조용히 감소, 백테스트 보유기간 왜곡
- **수정안:** gap_report(dates, market)·_gap_note(): KRX·US는 core.calendars.is_trading_day, CRYPTO는 매일, 커버리지 밖은 '판정 불가 일수'로만 집계, _cached에서 note 결합(패치). 선행: D12-08 수정, legacy 캘린더 커버리지(현재 2026-01-01~2027-12-31) 과거 확장, 서명 캘린더(현재 CalendarUnsigned) 서명
- **회귀 테스트:** ::test_missing_sessions_are_reported_against_the_calendar_and_never_filled (US 2026-03-11 결측·2026-03-28 토요일 행 보고, CRYPTO 하루 결측 보고, 2024년 날짜는 ((),(),10), History 길이 불변)

### D12-08 (P2, 추정)

- **심각도:** P2
- **판정:** 추정
- **파일·함수·라인:** data/calendars/KRX.json (exchange_calendars 4.13.2, 2026-08-18 생성) holidays; core/calendars/data/holidays_KRX.yaml (UNSIGNED DRAFT, 28-308행)
- **재현 단계:** r07_gaps.py: calendars.is_trading_day('KRX', date(2026,6,3)) → True, (2026,7,17) → True; r05_ks_detail.py: 허용 캐시 KS 10종목 모두 두 날짜 행 없음
- **기대 결과:** 2026-06-03(지방선거), 2026-07-17(제헌절)은 KRX 휴장일
- **실제 결과:** 거래일로 기록. 웹 검색 2차 출처 요약: '한국거래소는 6월 3일 지방선거일과 7월 17일 제헌절에 증권·파생·일반상품시장을 휴장'(2026-05-20 보도). 원문 news.bizwatch.co.kr은 프록시 DNS 실패로 미확인
- **영향:** D12-07 간격 검사 거짓 양성; _may_be_trading(history.py:363-387 → markets.is_open)이 휴장일을 장중으로 판단; 서명 예정 캘린더에도 누락
- **수정안:** 소유자가 KRX 공지 원문 확인 후 holidays_KRX.yaml에 두 행(kind: closed, source_url: 공지) 추가·서명, data/calendars/KRX.json 생성 시 같은 수동 보정 적용. 서명 파일이라 diff 미제시
- **회귀 테스트:** tests/macro_m1_calendars.py: assert legacy.is_trading_day('KRX', date(2026,6,3)) is False and legacy.is_trading_day('KRX', date(2026,7,17)) is False

### D12-09 (P2, 사실)

- **심각도:** P2
- **판정:** 사실
- **파일·함수·라인:** data/kis_markets.py _bars 150, overseas_chart 476-490 (CHART_YIELD 'I': Y0101, Y0204 등); core/quant/history.py kis_market_history 312-313
- **재현 단계:** r02_provider_paths.py E2: 0.25, 0.10, 0.00, -0.05, 0.05 입력
- **기대 결과:** 금리는 0·음수도 유효 관측값
- **실제 결과:** 0.00과 -0.05가 무기록 삭제(5→3). 허용 캐시 fred_DGS3MO.csv에 0.00 관측 21건 존재(실제 발생 사례)
- **영향:** 제로금리 구간이 지워져 곡선·차트 왜곡
- **수정안:** _bars(..., positive=False)를 overseas_chart의 CHART_YIELD에서 사용, Bars.to_history가 symbol 'I:'면 positive=False로 정제; 0 금리에 로그수익률 시도 시 _checked_prices가 ValueError(패치)
- **회귀 테스트:** ::test_every_provider_path_applies_the_rule (Y0204 행에서 0.0·-0.05 유지, 'inf' 제거, len(y)==39, 0.0 in y.to_history().closes)

### D12-10 (P2, 사실)

- **심각도:** P2
- **판정:** 사실
- **파일·함수·라인:** core/ficc/data.py _yf_fetch 195-211 (208행 dropna는 NaN만), _provider_rows 486 (sorted만)
- **재현 단계:** r02_provider_paths.py C2(가짜 yfinance.download DataFrame: inf·0·중복 인덱스), F(load_series('EURUSD=X', source='yfinance'))
- **기대 결과:** 유한 값, 날짜당 한 행(금리는 0·음수 허용)
- **실제 결과:** C2: inf 1·0 1·중복 1 통과. F: Series에 inf 1, 중복 날짜 1
- **영향:** FX 현물 등 Yahoo 기반 FICC 시리즈 오염; 일부 소비부만 np.isfinite로 방어(core/ficc/fx.py:405)
- **수정안:** _tidy(rows, label) = clean_rows(positive=False); 충돌 중복이면 errors[i]에 이유 기록 → 명시 source는 FICCError, auto는 기존 계약대로 SYNTHETIC+이유(D-03 감사와 조율 필요)(패치)
- **회귀 테스트:** ::test_ficc_rows_with_a_conflicting_date_are_refused_with_the_reason (충돌 시 rows==[]·이유에 날짜, inf 제거, -0.5 유지)

### D12-11 (P2, 사실)

- **심각도:** P2
- **판정:** 사실
- **파일·함수·라인:** core/quant/history.py:47 TRADING_DAYS=252; core/quant/risk.py:84,87,90; core/quant/montecarlo.py:115-116; core/calendars/clocks.py:30 ANNUALISATION_DAYS={'CRYPTO':365} 미사용
- **재현 단계:** r07_gaps.py '[crypto]': 연 80% 변동성, 연 365봉 합성 시리즈
- **기대 결과:** 가상자산은 365로 연율화
- **실제 결과:** analyze_history ann_vol=0.643 (0.804배; 이론 √(252/365)=0.831)
- **영향:** 가상자산 연율 변동성·수익률·Sharpe 과소, MC 연 drift를 1/252 단위로 365봉 경로에 적용
- **수정안:** periods_per_year(history): source UPBIT/BINANCE 또는 _looks_crypto면 clocks.annualisation_days('CRYPTO'), 아니면 252 → risk·montecarlo에 전달. 금융계산 감사 단위와 조율(이번 diff 미포함)
- **회귀 테스트:** 365봉 σ=0.80 합성 시리즈에서 abs(analyze_history(h).ann_vol/0.80 - 1) < 0.05

### D12-12 (P3, 사실)

- **심각도:** P3
- **판정:** 사실
- **파일·함수·라인:** core/quant/history.py:99 (문자열 정렬), fmp_history 170 ([:10]만)
- **재현 단계:** r01_clean_rows.py 날짜 블록
- **기대 결과:** ISO 정규화, 해석 불가 행 제거·기록, 엄격 오름차순
- **실제 결과:** '20260105'가 '2026-01-06' 뒤로, '2026-1-9'가 맨 뒤로, ''·'N/A' 유지
- **영향:** 형식이 섞이면 수익률 순서가 뒤집힘(현재 공급자 경로는 형식을 맞춰 노출 낮음)
- **수정안:** _iso_day() 정규화·검증(패치)
- **회귀 테스트:** ::test_dates_are_normalised_or_dropped_and_the_output_is_strictly_ascending (결과 ('2026-01-02','2026-01-05','2026-01-06'), bad_date==4)

### D12-13 (P3, 사실)

- **심각도:** P3
- **판정:** 사실
- **파일·함수·라인:** core/quant/history.py:98
- **재현 단계:** r01_clean_rows.py "101.5", "abc"
- **기대 결과:** 숫자 문자열은 변환, 아니면 제거·기록; 오류라면 HistoryError
- **실제 결과:** TypeError: '>' not supported between instances of 'str' and 'int'
- **영향:** UI가 원문 예외를 그대로 표시(ui/quant_lab_page.py:296-299). 현재 호출부는 float/None만 넘겨 도달 불가
- **수정안:** clean_rows의 float() 변환과 non_numeric 카운트(패치)
- **회귀 테스트:** ::test_non_finite_and_non_numeric_closes_never_survive_and_are_counted ('abc', None, True → non_numeric==3)

### D12-14 (P3, 사실)

- **심각도:** P3
- **판정:** 사실
- **파일·함수·라인:** core/quant/history.py fmp_history 166 (가격 필드 결측만 셈), 172-175 (변환 실패 무기록 continue)
- **재현 단계:** r08_before_after.py HEAD fmp nan / zero
- **기대 결과:** 버린 모든 행이 note에 기록
- **실제 결과:** n=59로 한 행이 빠졌지만 note 추가 없음
- **영향:** 사용자가 결측을 모름
- **수정안:** _with_note(note, rep)로 CleanReport 결합; 기존 'N session(s) without adjClose dropped' 문구 유지(tests/quant_acceptance.py:229)(패치)
- **회귀 테스트:** ::test_every_provider_path_applies_the_rule (FMP Infinity → note에 '1 NaN/inf close(s) dropped')

### D12-15 (P3, 사실)

- **심각도:** P3
- **판정:** 사실
- **파일·함수·라인:** core/quant/history.py synthetic_history 250-257 (평일만)
- **재현 단계:** r07_gaps.py '[synthetic]'
- **기대 결과:** 합성이라도 실제 거래일 형태
- **실제 결과:** 2026-01-01, 01-19, 02-16, 04-03, 05-25 등 US 휴장일에 값 존재
- **영향:** 실데이터와 바스켓 시 교집합에서 행이 빠질 뿐 계산 오류는 아님
- **수정안:** 낮은 우선순위: 합성 날짜 생성에 캘린더 사용 또는 note에 명시
- **회귀 테스트:** (선택) 2026년 구간 합성 날짜가 calendars.is_trading_day('US', d) is not False

### D12-16 (P3, 사실)

- **심각도:** P3
- **판정:** 사실
- **파일·함수·라인:** docs/asset_expansion_study.py _cached 68-79 (79행 `s[s > 0] if (s > 0).all() or name.startswith("_") is False else s`)
- **재현 단계:** 코드 읽기만(이 스크립트는 금지 파일을 읽으므로 실행하지 않음)
- **기대 결과:** inf·중복 인덱스 검사, 명확한 조건
- **실제 결과:** dropna()만; 79행은 우선순위 때문에 '이름이 _로 시작하지 않으면 항상 양수만'으로 동작
- **영향:** 연구 산출물 재현성(앱 화면 영향 없음)
- **수정안:** s = s[np.isfinite(s)]; 중복 인덱스 검출·보고; 79행을 명시적 조건으로
- **회귀 테스트:** 합성 CSV(inf·중복)로 _cached 단위 테스트 추가

## 미검증 항목

- 보고서 파일 미작성: 하네스가 서브에이전트의 docs/audit/2026-10-27/d01_d02_history_cleaning.md 쓰기를 거부함(우회하지 않음). 오케스트레이터가 이 결과로 파일을 만들어야 함
- 실제 공급자(FMP, Yahoo, KIS, Upbit, Binance)가 중복 날짜·inf를 실제로 보내는지: 네트워크 호출 없음. yfinance가 일부 비미국 거래소에서 마지막 봉을 두 번 내는 사례는 추정
- KRX 2026-06-03·2026-07-17 휴장: 거래소 공지 원문 미확인(news.bizwatch.co.kr DNS 실패), 2차 보도 요약과 Yahoo 데이터 부재가 일치할 뿐
- Yahoo KS 결측(개별주 2025-09-19, ETF 2024-10-30·2024-11-05)이 공급자 누락인지 실제 휴장인지 KIS·KRX 원천과 교차 확인하지 않음
- core/quant/risk.py analyze_history의 gs_quant 분기(bdate_range로 날짜 대체): 이 환경에 gs_quant가 없어 실행하지 않음
- Flet UI에서 nan·VaR 0%가 실제로 어떻게 표시되는지: 코드 경로로만 추론
- Upbit·Binance·KIS _page_back의 페이지 간 중복이 항상 같은 값인지(패치는 '먼저 행 유지'를 그대로 둠)
- ui/crypto_page.py 김치 프리미엄 등 Candles 직접 소비부가 Upbit 0.0 가격으로 받는 영향
- FICC _cache_get 재검증(C-01), 합성 데이터 대체 표기(D-03), 연율화 공식 전반: 다른 감사 단위
- 패치가 전체 870건 테스트에 주는 영향: quant·ficc·expansion·macro(m1_pit/m9_lab/m1_integration)·신규만 실행; safety, engine, ui, paper, grokteam, guard, papers, macro 나머지는 미실행
- 성능 수치(clean_rows 1.19 ms, gap_report 0.84 ms)는 1회 측정 참고값

<!-- verifier-section -->

## 독립 검증 결과

검증 대상: `docs/audit/2026-10-27/d01_d02_history_cleaning.md` (발견 16건). 코드 기준은 HEAD 4665e6e입니다. fdc1728 이후 `core/ data/ ui/ tests/ config.py`는 바뀌지 않았습니다(`git diff --stat` 빈 결과).

방법은 다음과 같습니다.
- 인용된 코드를 직접 읽었습니다.
- P0~P2 발견은 재현 스크립트를 새로 써서 다시 돌렸습니다. 네트워크 호출은 0건이고, 모든 전송부는 가짜입니다. 자격증명 함수는 더미로 바꿨고 `.env`는 열지 않았습니다.
- 실데이터는 허용된 캐시 파일만 썼습니다. 금지 파일 4개는 열기 전에 이름으로 거부했습니다.
- 제안 패치는 스크래치 복사본(`tree_fix`)에만 적용했습니다. 저장소는 수정하지 않았습니다(`git status` 빈 결과).

모든 산출물은 `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/verify_d01_d02_history_cleaning/`에 있습니다. 아래에서는 이 경로를 `W/`로 줄여 씁니다.

### 판정 표

| id | 유지 여부 | 정정 판정 | 정정 심각도 | 근거 |
|---|---|---|---|---|
| D12-01 | 유지 | 사실 | P1→**P2** | `history.py:98` `c is not None and c > 0`이 +inf를 통과시킵니다(W/v01_out.txt). FMP·KIS·Yahoo 경로에서도 inf가 남습니다(W/v02_out.txt A·B·C). 하류 결과: vol=nan, Sharpe=0, MC VaR=0(`montecarlo.py:327` `max(0.0,nan)`), inf가 마지막 행이면 signals 'strong bullish'(W/v03_out.txt). 다만 실데이터 근거가 없습니다. 허용 캐시 42개에 inf는 0건이고, 실제 공급자가 inf를 보낸 사례도 없습니다. 그래서 "에지 입력에 대한 가드 누락"으로 보고 P2로 내립니다. 부분 정정 1건: 포트폴리오 화면은 "경고 없이 [0.5,0.5]"가 아닙니다. `ui/portfolio_page.py:153-154`가 'solver did not converge' 오류 칩과 vol 'nan%'를 보여줍니다. |
| D12-02 | 유지 | 사실 | P1→**P2** | 중복 정책이 없고 경로마다 규칙이 다릅니다. FMP는 두 행을 모두 유지합니다(W/v02 A). KIS 페이지 안에서는 나중 행이 남습니다(W/v02 B: 130 유지, 999 소실). `_bars`도 나중 행이 남습니다(E). 같은 날짜에 2배 값 1행이 끼면 vol 0.29→0.93입니다(W/v03 dup_mid). 다만 실데이터에서 중복이 생길 경로는 대부분 위쪽에서 이미 막힙니다. yfinance 1.7.0은 `scrapers/history.py:532-536`의 `fix_Yahoo_returning_live_separate`와 `df.index.duplicated(keep='first')`로 중복을 지웁니다. KIS·Upbit·Binance는 dict로 중복을 제거합니다. 허용 캐시 42개에 중복은 0건입니다. 그래서 P2입니다. 인용 오류 1건: `core/crypto/analytics.py:43-45` `_align`은 이미 만들어진 dict를 받습니다. 실제로 dict를 만드는 곳은 `ui/crypto_page.py:53-55`입니다. |
| D12-03 | 유지 | 사실 | P1→**P2** | `Candles.to_history`(`crypto_client.py:81-84`)와 `Bars.to_history`(`kis_markets.py:87-90`)는 정제를 거치지 않습니다. Upbit에서 None은 `float(x or 0.0)` 때문에 0.0 종가가 되고, "NaN"은 nan으로 남습니다(W/v02 D). 추가 증거: Upbit 마지막 종가가 0.0이면 김치 프리미엄 last_pct=-100.0입니다(W/v08_out.txt). 실제 공급자에서 결측 종가는 드물기 때문에 P2입니다. |
| D12-04 | 유지 | 사실 | P2→**P3** | 재현됩니다. 캐시 파일에 `Infinity` 토큰이 들어가고, 엄격한 파서는 이를 거부합니다. 공급자 장애 시 inf 1개·중복 1개인 캐시가 그대로 나옵니다(W/v05_out.txt). 패치 트리에서는 다시 조회합니다(W/v05_fix_out.txt). 다만 독립 결함이 아니라 D12-01의 파생입니다. "TTL 6시간 동안"이라는 설명도 일부 틀립니다. 장중에 받은 시리즈는 10분만 쓰입니다(`history.py:360, 434-435`). 6시간은 `"live": false`인 파일에만 해당합니다. |
| D12-05 | 유지 | 사실 | P2 | 허용 파일 `yf_CL_F.csv`로 재현했습니다. 2020-04-20의 -37.63 행이 note 없이 사라지고, 04-17→04-21 로그수익률 -0.6017이 1세션 수익률로 계산됩니다(W/v04_out.txt). 이 구간은 Strategy Lab 기본값 days=5000(`ui/strategy_lab_page.py:223`)으로 실제 앱에서 닿습니다. |
| D12-06 | 유지 | 사실 | P2 | 코드상 급등락 검사가 없습니다. History는 frozen이고, 정제 후 note를 덧붙이는 코드가 없습니다. 요청서 §6의 "경고·검토" 요구가 빠졌으므로 가드 누락으로 봅니다. |
| D12-07 | 유지 (수정안은 **부적합**) | 사실 | P2 | 간격 검사가 없다는 점은 사실입니다. `completeness_check`는 테스트에서만 호출됩니다. 증거 정정: 허용 파일 `yf_005930.KS.csv`를 XKRX(2000년부터)와 대조하면, 비세션 행이 11개가 아니라 **99개**이고 그중 97개가 전일 종가 반복입니다(W/v07_out.txt). 조사자는 exchange_calendars 기본 시작일(약 20년 전)을 써서 적게 셌습니다. **수정안 문제**: 패치의 gap note를 실제 KRX 504세션(2024-08-26~2026-09-23)에 적용하면 결측으로 2026-06-03·2026-07-17만 보고합니다. 둘 다 실제 휴장일이므로 오탐입니다. 진짜 결측인 2025-09-19는 커버리지 밖이라 놓칩니다. 여기에 "493 day(s) outside the KRX calendar coverage" 문구가 모든 시리즈에 붙습니다(W/v06_out.txt). 따라서 D12-08 보정과 과거 커버리지 확장 전에 배포하면 안 됩니다. |
| D12-08 | 유지 | 추정 | P2 | `data/calendars/KRX.json`의 2026 휴장일 목록과 draft `holidays_KRX.yaml`에 06-03·07-17이 없습니다. `is_trading_day('KRX', …)`도 두 날짜 모두 True를 돌려줍니다(W/v04_out.txt). 허용 KS 파일들에도 두 날짜 행이 없습니다. 웹 검색 결과 요약도 "한국거래소는 6월 3일 지방선거일과 7월 17일 제헌절에 증권·파생·일반상품시장을 휴장"이라고 합니다([bizwatch 2026-05-20](https://news.bizwatch.co.kr/article/market/2026/05/20/0023)). 원문은 확인하지 못했습니다. bloomingbit.io와 hankyung.com은 DNS 실패로 열리지 않았습니다. 그래서 판정은 추정으로 둡니다. 두 날짜는 이미 지났습니다. 영향은 서명 예정 캘린더와 간격 검사 오탐에 몰립니다. |
| D12-09 | 유지 | 사실 | P2→**P3** | 0.00과 -0.05가 삭제되는 것은 재현됩니다(W/v02 E2: 5→3). 그러나 이 경로(CHART_YIELD)로 들어오는 시리즈는 KTB·CD·콜·UST 10y/30y·Fed funds(`kis_markets.py:56-61`)뿐입니다. 이들은 도달 가능한 기간에 0 이하가 된 적이 없습니다. 조사자가 근거로 든 `fred_DGS3MO`의 0.00 21건은 FRED 시리즈라서 이 경로와 무관합니다. 근거가 맞지 않아 P3로 내립니다. |
| D12-10 | 유지 (일부 과장) | 사실 | P2 | FICC Yahoo 경로에서 inf 1개·0.0 1개가 `load_series`까지 통과합니다(W/v02 F). 중복이 통과한다는 부분은 가짜 `download`가 yfinance 자체의 중복 제거를 우회해서 생긴 결과입니다. 실제로는 거의 생기지 않습니다. 수정안 문제: `_tidy(positive=False)`는 FX 현물의 0.0을 그대로 둡니다. 가격과 FX에는 positive=True를 써야 합니다. 또 auto 경로에서 충돌 중복을 HistoryError로 막으면 결과가 SYNTHETIC 대체로 이어집니다(D-03 조율 필요). |
| D12-11 | 유지 | 사실 | P2→**P1** | 365봉/년, σ=0.80 합성 시리즈에서 `analyze_history` ann_vol=0.661입니다. 365 기준 0.795의 0.831배입니다(이론값 √(252/365)=0.831, W/v03_out.txt). 모든 가상자산 심볼의 Quant Lab "Vol (ann.)"·"Drift (ann.)"(`ui/quant_lab_page.py:316-317`)가 17% 낮게 나옵니다. 프로젝트 자체 규칙(`core/calendars/clocks.py:30` CRYPTO=365)과도 어긋납니다. MC는 봉당 drift를 `value/252`로 씁니다(`montecarlo.py:243-244`). 그래서 365봉 경로에서는 연 drift가 1.45배로 들어갑니다. 화면에 보이는 숫자가 계통적으로 틀리므로 P1입니다. 조사자 수정안의 약점: `_looks_crypto('BTC-USD')`가 False입니다(`history.py:333-335`). 그래서 Yahoo BTC-USD가 빠집니다. 날짜로 판정하는 대안 diff를 아래에 붙였고 검증했습니다. |
| D12-12 | 유지 | 사실 | P3 | W/v01: '20260105'가 '2026-01-06' 뒤에 오고, '2026-1-9'는 맨 뒤로 갑니다. 빈 문자열은 그대로 남습니다. 현재 공급자들은 ISO 형식을 맞춰 보내므로 노출은 낮습니다. |
| D12-13 | 유지 | 사실 | P3 | W/v01: 문자열 '101.5'를 넣으면 TypeError가 납니다. 현재 호출부로는 도달할 수 없습니다. |
| D12-14 | 유지 | 사실 | P3 | 코드 확인: `history.py:166`은 필드가 없는 경우만 셉니다. 172-175는 변환 실패를 기록 없이 넘깁니다. NaN과 0 이하 값의 삭제도 note에 남지 않습니다. |
| D12-15 | 유지 | 사실 | P3 | 코드 확인: `history.py:253-256`은 평일만 만듭니다. 그래서 휴장일에도 값이 생깁니다. |
| D12-16 | 유지 | 사실 | P3 | `docs/asset_expansion_study.py:79`의 연산자 우선순위 해석은 맞습니다. 다만 funding(129행)과 FRED(98행)는 `_cached`를 거치지 않습니다. 그래서 0 이하 값 필터는 가격에만 걸리고 실해는 없습니다. 위생 문제입니다. |

### 제안 수정안·회귀 테스트 검토

1. **패치 적용 시험(사실).** `proposed_d01_d02.diff`는 HEAD 복사본에 `git apply`로 깨끗하게 적용됩니다. safety·engine·ui·quant·ficc·expansion·macro 전체(779행)를 HEAD와 패치 트리에서 돌렸습니다(W/run_head.json, W/run_fix.json).
   - 기존 테스트의 상태 변화는 0건입니다.
   - 신규 12건은 모두 PASS입니다.
   - 양쪽 모두에서 실패한 1건(`macro_m8_pipeline/test_dry_run_end_to_end_on_the_local_cache`)은 두 트리를 동시에 돌려 생긴 CPU 경합으로 120초 제한을 넘은 것입니다. 기준선에서는 PASS입니다.
   - paper·grokteam·guard·papers는 규칙에 따라 돌리지 않았습니다.
2. **회귀 테스트의 "수정 전 실패"는 ImportError 때문입니다.** 신규 모듈이 HEAD에 없는 `clean_rows`·`gap_report`를 import하므로, HEAD에서는 동작이 아니라 import 단계에서 실패합니다. HEAD에도 있는 공개 API만 쓰는 동작 테스트를 W/v09_behaviour_tests.py로 만들었습니다. HEAD에서 5/5 FAIL(동작 실패)이고, 패치 트리에서는 4/4 PASS입니다. 연율화 테스트는 패치 범위 밖이라 여전히 FAIL입니다. 신규 모듈에 이 방식의 테스트를 함께 넣기를 권합니다.
3. **D12-07의 gap note는 현재 데이터에서 오탐만 냅니다(W/v06).** D12-08 보정 전에는 `_cached`에서 `_with_gap`을 빼야 합니다. "outside coverage" 문구는 커버리지가 완전할 때만 쓰거나 아예 빼야 합니다. 추가 회귀 테스트로 이것을 권합니다: 2026-01-02~2026-09-30 KRX 세션에서 06-03·07-17이 없는 시리즈는 "missing" note가 0건이어야 합니다.
4. **note의 노출 문제(M02).** 패치는 모든 경고를 `History.note`에만 넣습니다. 그런데 포트폴리오와 Strategy Lab은 note를 초록 칩의 툴팁으로만 보여줍니다. 그래서 §6이 요구하는 "경고"가 사용자에게 보이지 않습니다.
5. **D12-11 대안 diff (검증됨).** 스크래치 `tree_ann`에 적용했습니다. 동작 테스트가 PASS이고, quant·expansion 73건 모두 PASS입니다(W/run_ann.log).
```diff
--- a/core/quant/history.py
+++ b/core/quant/history.py
@@ -47,6 +47,15 @@
 TRADING_DAYS = 252
 
 
+def periods_per_year(dates) -> int:
+    """Bars per year of a daily series: 365 when it trades on weekends (crypto: Upbit, Binance, Yahoo
+    BTC-USD), else 252. Read from the dates, so a basket aligned on weekdays only stays at 252."""
+    if len(dates) < 20:
+        return TRADING_DAYS
+    weekend = sum(1 for d in dates if date.fromisoformat(str(d)[:10]).weekday() >= 5)
+    return 365 if weekend / len(dates) > 0.10 else TRADING_DAYS
+
+
 class HistoryError(RuntimeError):
--- a/core/quant/risk.py
+++ b/core/quant/risk.py
@@ -14,7 +14,7 @@
-from core.quant.history import History, TRADING_DAYS
+from core.quant.history import History, TRADING_DAYS, periods_per_year
@@ -68,7 +68,8 @@
     engine = "local"
-    if _GS_OK:
+    ppy = periods_per_year(history.dates)       # 365 for a weekend-trading (crypto) series
+    if _GS_OK and ppy == TRADING_DAYS:          # gs_quant infers 252 from business-day spacing
@@ -81,16 +82,16 @@
-            ann_vol = float(np.std(r, ddof=1)) * math.sqrt(TRADING_DAYS)
+            ann_vol = float(np.std(r, ddof=1)) * math.sqrt(ppy)
             mdd = float(np.min(_drawdown_curve(px)))
     else:
-        ann_vol = float(np.std(r, ddof=1)) * math.sqrt(TRADING_DAYS)
+        ann_vol = float(np.std(r, ddof=1)) * math.sqrt(ppy)
         mdd = float(np.min(_drawdown_curve(px)))
-    ann_ret = float(np.mean(r)) * TRADING_DAYS
+    ann_ret = float(np.mean(r)) * ppy
@@
-    down_vol = (float(np.std(downside, ddof=1)) * math.sqrt(TRADING_DAYS)
+    down_vol = (float(np.std(downside, ddof=1)) * math.sqrt(ppy)
```
   MC 쪽도 같은 방식으로 바꿔야 합니다. `run_monte_carlo`에서 `ppy`를 구하고, `rate_daily`·`drift_daily`를 `value/ppy`로 계산합니다(`montecarlo.py:243-244`). 표시용 `sigma_annual`·`mu_annual`·`correction_annual`은 일 단위 값에 `ppy`를 곱해 연율화합니다. 경로 생성의 일 단위 σ는 지금과 같으므로 그대로 둡니다. 이 부분은 설명만 하고 diff는 넣지 않았습니다.
   회귀 테스트는 `tests/quant_acceptance.py::test_crypto_series_annualised_with_365`입니다. 2024-10-01부터 730일, σ=0.80/√365 합성 시리즈에서 `analyze_history(h).ann_vol == std(r)·√365`(상대오차 1e-9)를 확인합니다. 같은 날짜를 평일로만 줄인 시리즈에서는 √252를 확인합니다. HEAD에서는 0.661 대 0.795로 FAIL입니다.

### 놓친 발견사항

**M01. 결측 필드를 0.0으로 채움 (ETF NAV·괴리율, KIS OHLC·거래량, Upbit OHLC)**
- 심각도: P2
- 판정: 사실
- 파일·함수·라인:
  - `data/kis_markets.py:153` `_bars`의 `col`: `float(_f(...) or 0.0)`
  - `data/kis_markets.py:233-234` `etf_nav_daily`의 nav·prem: `or 0.0`
  - `data/crypto/crypto_client.py:161` Upbit `g`
  - 소비부 `ui/etf_page.py:73-78`: premium의 mean·sd·z·ADF·half-life 계산
- 재현 단계: `cd /home/user/quantgen && python3 -B W/v08_zero_fill.py`. 가짜 KIS 클라이언트가 60행 중 2행에서 nav·dprt를 빼고 보냅니다.
- 기대 결과: 빈 필드는 결측(NaN)으로 남습니다. 통계는 유한한 값만 씁니다. 빠진 일수는 표시합니다.
- 실제 결과: premium==0.0 2행, nav==0.0 2행입니다. 괴리율 평균이 0.35 대신 0.338로 나옵니다.
- 영향: ETF 화면의 괴리율 통계(평균·z·ADF·반감기)가 조용히 0% 쪽으로 기웁니다. 0%는 정상 범위의 값이라 사용자가 알아챌 수 없습니다. D12-03의 Upbit `or 0.0`과 같은 패턴인데, 조사자는 종가만 다뤘습니다.
- 수정안: 아래 diff입니다. 스크래치 `tree_m1`에서 검증했습니다. 재현에서 0.0 채움 행이 0건이 되고, expansion·ui·ficc 81건이 모두 PASS입니다(W/m1_fix.diff, W/run_m1.log).
```diff
--- a/data/kis_markets.py
+++ b/data/kis_markets.py
@@ -30,6 +30,7 @@
 import io
+import math
 import re
@@ -140,6 +141,12 @@
+def _num(value) -> float:
+    """A KIS field as a float; a missing or unreadable field is NaN, never 0.0."""
+    x = _f(value)
+    return float(x) if x is not None and math.isfinite(x) else math.nan
+
+
 def _bars(symbol: str, rows: list[dict], keys: dict[str, str], *, note: str = "",
@@ -150,7 +157,7 @@
-    col = lambda k: tuple(float(_f(seen[d].get(keys[k])) or 0.0) for d in ds) if k in keys else ()  # noqa: E731
+    col = lambda k: tuple(_num(seen[d].get(keys[k])) for d in ds) if k in keys else ()  # noqa: E731
@@ -230,8 +237,8 @@
-        nav = tuple(float(_f(by[d].get("nav")) or 0.0) for d in b.dates)
-        prem = tuple(float(_f(by[d].get("dprt")) or 0.0) for d in b.dates)
+        nav = tuple(_num(by[d].get("nav")) for d in b.dates)
+        prem = tuple(_num(by[d].get("dprt")) for d in b.dates)
--- a/ui/etf_page.py
+++ b/ui/etf_page.py
@@ -70,8 +70,9 @@
-    if out.get("premium_pct") is not None and out["premium_pct"].size > 60:
-        prem = out["premium_pct"]
+    if out.get("premium_pct") is not None and np.isfinite(out["premium_pct"]).sum() > 60:
+        prem = out["premium_pct"][np.isfinite(out["premium_pct"])]      # a day KIS left blank is not a 0% premium
+        out["premium_missing"] = int((~np.isfinite(out["premium_pct"])).sum())
```
  Upbit `g`도 종가 외 필드는 같은 `_num` 규칙으로 바꿔야 합니다. 종가는 D12-03 패치가 처리합니다.
- 회귀 테스트: `tests/expansion_acceptance.py::test_etf_nav_blank_premium_is_missing_not_zero`. 가짜 클라이언트 행 중 2개에서 dprt를 빼고 다음을 확인합니다.
  - `sum(math.isnan(x) for x in b.extra["premium_pct"]) == 2`
  - `0.0 not in b.extra["premium_pct"]`
  - HEAD에서는 0.0이 2개라 FAIL입니다.

**M02. 데이터 품질 note가 포트폴리오·Strategy Lab에서 툴팁에만 숨겨짐**
- 심각도: P3
- 판정: 사실 (코드 확인)
- 파일·함수·라인: `ui/portfolio_page.py:143-144`(초록 'success' 칩의 `tooltip=h.note`), `ui/strategy_lab_page.py:257-259`(같은 방식). 비교: `ui/quant_lab_page.py:326`과 `ui/signals_page.py:169-170`은 note를 칩 본문에 보여줍니다.
- 재현 단계: 코드를 읽어 확인했습니다. 두 화면에서 `h.note`는 합성 데이터일 때를 빼고 툴팁에만 들어갑니다. 칩 색은 SYNTHETIC이 아니면 항상 success입니다.
- 기대 결과: 정제 결과("N session(s) … dropped", "FMP close, NOT dividend-adjusted" 등)는 경고 색의 보이는 요소로 나타나야 합니다(요청서 §6: 경고와 검토 대상).
- 실제 결과: 마우스를 올려야만 보입니다. 경고가 있는 시리즈도 초록 칩으로 표시됩니다.
- 영향: D-01·D-02 패치가 note에 경고를 넣어도, 두 주요 화면에서는 경고가 보이지 않습니다.
- 수정안: History에 `warnings: tuple[str, ...]`를 추가하거나, CleanReport가 비어 있지 않은지 여부를 노출합니다. 두 화면은 그 경우 칩을 'error' 토큰으로 칠하고, 문장을 `notice(...)`로 덧붙입니다. 예시: `chip(..., "error" if h.warnings else "success", tooltip=h.note)`, 그리고 `blocks.append(notice("; ".join(h.warnings), "error"))`.
- 회귀 테스트: `tests/flet_api_guard.py::test_portfolio_surfaces_cleaning_warnings`. warnings가 있는 History 2개로 결과 블록을 만들고, 'error' 토큰 칩 또는 notice에 경고 문구가 들어 있는지 확인합니다. HEAD에서는 툴팁뿐이라 FAIL입니다.

### 재현 파일

모두 W/ 아래에 있습니다.
- v01_clean_rows.py(+v01_out.txt)
- v02_provider_paths.py(+v02_out.txt)
- v03_downstream.py(+v03_out.txt)
- v04_real_cache.py(+v04_out.txt)
- v05_cache.py(+v05_out.txt, v05_fix_out.txt)
- v06_fix_gap_note.py(+v06_out.txt)
- v07_ks_xkrx.py(+v07_out.txt)
- v08_zero_fill.py(+v08_out.txt)
- v09_behaviour_tests.py(+v09_head_out.txt, v09_fix_out.txt)
- vrun.py, run_head/run_fix/run_ann/run_m1(.json/.log)
- apply_ann_fix.py, ann_fix_*.diff
- apply_m1_fix.py, m1_fix.diff
- tree_head/, tree_fix/, tree_ann/, tree_m1/: git archive 복사본입니다. 금지 파일 4개는 추출 단계에서 제외했습니다.

### 미검증

- 실제 공급자가 inf나 중복을 보내는지는 확인하지 못했습니다. 네트워크 호출을 하지 않았습니다.
- KRX 휴장 공지 원문은 열지 못했습니다(DNS 차단).
- Flet 화면이 실제로 어떻게 렌더링되는지는 코드로만 추론했습니다.
- 연율화 수정의 MC 부분은 설명만 했고 실행 검증은 하지 않았습니다.
