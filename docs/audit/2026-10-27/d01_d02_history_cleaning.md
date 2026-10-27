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
