# Bonds 화면 검증 F. 성능·상태 관리·재현성

> 작성 메모 (오케스트레이터): 하네스가 하위 에이전트의 보고서 파일 쓰기를 막아, 조사 에이전트가 반환한 본문과 독립 검증자가 반환한 검증 절을 내용 변경 없이 옮겼습니다. 저장소 코드는 바꾸지 않았습니다.

## F. 성능·상태 관리·재현성 (요청서 3.F) — 독립 감사 결과

### 0. 범위와 방법
- 대상: `ui/bonds_page.py`(run/worker/on_tool/_num), `core/ficc/bonds.py`, `core/ficc/curves.py`, `core/ficc/data.py`(FRED·합성·캐시), `core/ficc/insights.py:narrate_bond`, `ui/fcharts.py`, `ui/qcharts.py`, `ui/ai_panel.py`, `ui/components.py`.
- 실행 환경: 클라우드 컨테이너 4 vCPU, Python 3.13.17, flet 0.85.2, matplotlib 3.11.2(Agg), numpy 2.3.5, scipy 1.18.0, pandas_datareader 0.11.1. 소유자 Windows PC의 시간은 미확인이다.
- 저장소는 건드리지 않았다(`git status` 깨끗함). 코드는 `git archive HEAD` 복사본 두 개에서 돌렸다. `repo/`는 HEAD 그대로, `repo_fixed/`는 수정안 적용본이다. 금지 4개 캐시 파일은 열지 않고 지웠다. FICC 캐시는 매번 임시 폴더(`NEXTGEN_FICC_CACHE`)를 썼다. `.env`는 열지 않았다. `tests/run_all.py`는 돌리지 않았다.
- 화면: 실제 Flet 창 대신 stand-in Page를 썼다. `run_thread`를 즉시 실행하는 것(SyncPage)과 실제 스레드를 띄우는 것(ThreadPage) 두 가지다. 렌더된 컨트롤 트리에서 글자를 뽑았다. 차트는 `fcharts._to_image`를 가로채 제목·범례·주석·막대 값을 읽었다. AI payload는 `analysis_panel`을 가로채 읽었다.
- 독립 구현: `indep.py`. 순수 Python+math로 가격·YTM(이분법)·Macaulay·Modified·Convexity·DV01(해석식과 중앙차분)·부트스트랩(log-linear DF)·z-spread·KRD·carry/roll·시나리오를 다시 짰다. 저장소 함수를 부르지 않는다.
- 겹치지 않게 인용한 기존 보고서: P01-05(재클릭 미차단, 일반), P01-09(FRED 순차 HTTP), P01-13(임포트 3초), D-03 계열(합성 표시·해설 미표시), FC-03(Price는 dirty), financial_calcs 표 11행(KRD 합/DV01 = 1+y/f 문서 일치).

### ① 요약
1. 계산은 빠르다. 합성 곡선에서 Run 1회 중앙값은 calc 220.8ms, scenarios 139.2ms, hedge 12.4ms다. 시간의 대부분은 matplotlib 차트다(calc 207.1ms). 곡선 생성·부트스트랩·analyze_bond·시나리오·해설은 모두 합쳐 12ms 안쪽이다.
2. 캐시는 동작한다(모의 FRED). 첫 Run만 네트워크를 쓴다. 이후 Run, 도구 전환, 재시작(메모리 비움 후 디스크)은 호출 0회다. TTL 21,600초가 지나면 다시 받는다.
3. FRED가 죽어 있으면 매 Run이 12번 호출한다(F-06). 실패를 기억하지 않는다. 모의 300ms로 Run마다 3.6초를 기다렸다. 실제 타임아웃이면 Run 하나에 수 분이 걸릴 수 있다(추정).
4. 재현성은 확인했다. 같은 입력·같은 스냅샷이면 숫자, 글자, 표, PNG 바이트까지 같다. 다른 프로세스·다른 PYTHONHASHSEED에서도 같다.
5. 화면 요소 간 일관성은 확인했다. 10개 사례, 410개 대조에서 카드·칩·차트 제목/범례/주석/막대·표·해설·payload가 독립 계산과 표시 자릿수까지 모두 일치했다(HEAD에서 실패 0).
6. 상태 관리에 결함이 있다. 실행 토큰이 없다. 늦게 끝난 옛 Run이 새 Run 결과를 덮는다. 옛 Run의 오류가 새 Run의 정상 결과를 지운다(F-01, P1). 한 Run 안에서도 입력을 두 시점에 읽어 섞인다(F-02). 입력을 바꾸고 Run하지 않아도 표시가 없다(F-03). 숨은 Position DV01 덮어쓰기가 남는다(F-04).
7. 일관성 점검 중 계산 결함 하나를 찾았다. 만기 ≤ 3개월이면 carry_roll이 마지막 쿠폰을 버린다(F-05, B 차원과 겹침).
8. 수정안(실행 토큰, 클릭 시점 입력 고정, "Computed for:" 줄(계산 기준), 수정 시 stale 배너, carry 한 줄)을 복사본에 적용했다. 제안 회귀 테스트가 HEAD 2/7 → 수정본 7/7이 됐다. 기존 FICC 인수 테스트는 양쪽 57/57이다.

### ② 심각도별 이슈
| ID | 심각도 | 판정 | 위치 | 한 줄 |
|---|---|---|---|---|
| F-01 | P1 | 테스트로 확인됨 | `ui/bonds_page.py:94-224` (`:99-102`, `:216-218`, `:224`, `:237`) | 실행 토큰이 없다. 옛 Run 결과·오류가 새 Run을 덮고, 진행 표시가 먼저 꺼진다 |
| F-02 | P2 | 테스트로 확인됨 | `ui/bonds_page.py:105-117` | 입력 일부는 곡선 로드 전, 일부(Price·CTD·CF·Position DV01)는 후에 읽는다. 한 결과에 두 시점의 입력이 섞인다 |
| F-03 | P2 | 테스트로 확인됨 | `ui/bonds_page.py:63-89`, `:125-130` | 입력·출처·도구를 바꿔도 결과가 옛것이라는 표시가 없다. 입력 반영 줄이 없다 |
| F-04 | P2 | 테스트로 확인됨 | `ui/bonds_page.py:81-83`, `:117`, `:193-201` | 숨은 Position DV01 덮어쓰기가 도구 전환·명목 변경 뒤에도 남는다. 표시가 없다 |
| F-05 | P2 | 테스트로 확인됨 | `core/ficc/bonds.py:carry_roll:201-202, 208`; 라벨 `ui/bonds_page.py:157` | 만기 ≤ 0.25y에서 마지막 쿠폰이 빠진다. T=0.25에서 총합이 −1.375/100 뛴다. 라벨은 "3m" 그대로다 |
| F-06 | P2 | 테스트로 확인됨(모의). 최악 시간은 추정 | `core/ficc/data.py:_provider_rows:474-483`, `load_treasury_curve:552-568`, `_fred_fetch:163-192` | FRED 장애 시 Run마다 12회 호출. 실패 캐시 없음 |
| F-07 | P3 | 테스트로 확인됨 | `ui/bonds_page.py:137,167-168`; `core/ficc/insights.py:112-113`; `ui/fcharts.py:144` | 같은 화면의 "per bp" 두 합계(DV01 836 vs KRD 860)가 다른 기준인데 설명이 없다 |
| F-08 | P3 | 코드로 확인됨. 위험은 미확인 | `ui/qcharts.py:21,49` | 작업 스레드에서 pyplot 사용. 60회 동시 렌더에서 오류·바이트 차이 0 |

### 코드 추적표 (Run 1회의 실제 경로)
| 단계 | 파일:함수:줄 | 비고 |
|---|---|---|
| 클릭 | `ui/bonds_page.py:run:94-97` | busy 켬, `result_host` 비움, `page.update()` |
| 스레드 | `:224` `page.run_thread(worker)` | 클릭마다 작업자 하나. 잠금·토큰·버튼 비활성화 없음(`:237`) |
| 입력 읽기 1 | `:105-109` | tool, coupon, maturity, freq, notional, ytm. 곡선 로드 전 |
| 곡선 | `:110` `load_treasury_curve` → `core/ficc/data.py:552-568` | synthetic이면 `synthetic_curve_panel:361-382`(매번 생성, 캐시 안 함). FRED면 `_treasury_from_fred:571` → `_provider_rows:449-495` → `_cache_get:233-265`/`_fetch`/`_cache_put:268-281` |
| 부트스트랩 | `:111` `curve_from_snapshot` → `core/ficc/curves.py:262-267` → `bootstrap_par_curve:165-216` | |
| 입력 읽기 2 | `:112` `_num(price)`, `:117` `_num(pos_dv01/ctd_dv01/cf)` | 곡선 로드 후 |
| 분석 | `:112` `analyze_bond` → `core/ficc/bonds.py:231-254` | z_spread `:108`, KRD `:144`, carry_roll `:169`, curve_price `:102` |
| 시나리오 | `:114` `scenario_pnl` → `bonds.py:299-320` | z-spread 다시 풂 |
| 헤지 | `:118` `futures_hedge_ratio` → `bonds.py:323-329` | |
| 카드·칩 | `:122-139`, `:156-165`, `:171-176`, `:193-206` | `ui/components.py:stat:121`, `chip:30`, `notice:67` |
| 차트 | `:166-168,177` → `ui/fcharts.py:krd_chart:133`, `scenario_chart:148`, `price_yield_chart:168` → `ui/qcharts.py:_fig:48`(pyplot), `_to_image:55` | |
| 해설 | `:140` `insights.narrate_bond` → `core/ficc/insights.py:105-139`; 헤지 문장은 `:207-209`에서 덧붙임 | |
| payload | `:141-154,188-190,210-211` → `ui/ai_panel.py:analysis_panel:26`(`payload_fn` 기본 인자로 고정) | |
| 그리기 | `:216-218` 성공, `:99-102` 실패 | 무조건 덮어씀 |
| 도구 전환 | `:87-89` `on_tool` | hedge_row 표시만 바꿈 |

### ③ 재현 단계 (요약. 상세는 findings 항목)
- F-01: `f6_threads.py` T1·T3·T4, `f6b_inorder.py`. 곡선 로더를 `threading.Event`로 막아 순서를 고정했다(sleep으로 정하지 않음).
- F-02: `f6_threads.py` T2.
- F-03·F-04: `f5_stale.py` (a)(c)(d)(e)(f), `f4_consistency.py` H2.
- F-05: `f7_carry_edge.py`.
- F-06: `f2_fred_cache.py` 변형 C·D.
- F-07: `f4_consistency.py` C1-C5·S1-S2.
- 실행: `cd /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/F_perf_state && python3 -B <script>`. 수정본은 앞에 `QG_ROOT=$PWD/repo_fixed`.

### ④ 수식 및 독립 계산

**4.1 공식(독립 구현 `indep.py`)**
| 항목 | 식 | 단위·관례 |
|---|---|---|
| 현금흐름 시점 | t_k = T − k/f, k=0..⌈T·f−1e-9⌉−1 | 년, 단순 연분수 |
| 가격 | P = Σ cf_i (1+y/f)^(−t_i f) | 100당, dirty(FC-03) |
| YTM | P(y) = P_in 이분법 [−0.5, 2.0], 폭 1e-15 | 연율, f회 복리 |
| Macaulay | Σ t_i PV_i / P | 년 |
| Modified | Mac/(1+y/f) | |
| Convexity | Σ t_i(t_i+1/f)PV_i / ((1+y/f)² P) | |
| DV01 | Mod·P/100·N·1e-4 (중앙차분 (P(y−1bp)−P(y+1bp))/2·N/100도 계산) | 통화/bp, 롱이면 양수 |
| 곡선 | t<1: z=ln(1+y t)/t. t≥1: y/f·ΣDF(t_i)+DF(T)=1을 이분법. DF는 z·t 선형 보간, 양끝 밖은 z 고정 | 연속복리 zero |
| z-spread | Σ cf_i DF(t_i) e^(−s t_i) = P | 연속 |
| KRD | 키 만기 삼각 bump ±1bp, z 고정, (P↓−P↑)/2·N/100 | zero 기준 |
| 시나리오 | zero에 bp 이동(평행) 또는 키 만기 값을 곡선 노드로 선형 보간, z 고정 재평가. P&L=(P_new−P)·N/100, %=P_new/P−1 | |
| carry/roll | h=min(0.25,T). accrued=c·100·h, funding=zero(h)·P·h. roll=clean_aged−P | 100당, 3개월 |
| 헤지 | n = pos·CF/CTD, 선물 DV01 = CTD/CF, 잔여 = pos − round(n)·CTD/CF | |

**4.2 독립 계산 대조(f9_numbers.py, 오늘 합성 스냅샷 2026-10-27)**
독립 부트스트랩 zero와 저장소 zero의 최대 차이 2.36e-16.
| 사례 | 가격 | YTM | Mac | Mod | Cvx | DV01 | 최대 |차| (가격·위험) | KRD 합 |차| | carry/roll |차| | 화면 관찰값(2.1)과 표시 자릿수 일치 |
|---|---|---|---|---|---|---|---|---|---|---|
| 5.5/10 y4.5 | 107.981856 | 4.500% | 7.919 | 7.745 | 73.015 | 836.290 | 2.3e-13 | 1.1e-13 | 1.8e-12 | 6/6 |
| 4.5/10 y5.5 | 92.386374 | 5.500% | 8.072 | 7.856 | 74.390 | 725.786 | 0 | 7.1e-11 | 8.6e-13 | 6/6 |
| 5.5/10 y5.5 | 100.000000 | 5.500% | 7.823 | 7.614 | 71.152 | 761.363 | 1.4e-14 | 1.4e-10 | 2.0e-12 | 6/6 |
| 5.5/10 p95 | 95.000000 | 6.177690% | 7.756 | 7.524 | 69.892 | 714.774 | 5.9e-12 | 1.4e-10 | 1.5e-11 | 6/6 |
| 5.5/10 p105 | 105.000000 | 4.862682% | 7.885 | 7.697 | 72.339 | 808.222 | 0 | 7.1e-11 | 2.8e-13 | 6/6 |
| 4.5/10 y4.5 | 100.000000 | 4.500% | 8.161 | 7.982 | 76.209 | 798.186 | 0 | 1.4e-10 | 2.7e-12 | (헤지 798 일치) |
해석식 DV01과 중앙차분 DV01의 차이는 1.1e-4~1.4e-4 통화/bp다. ½·Cvx 2차 항 크기와 같다(정의 차이, 결함 아님).
2.3절 시나리오 화면값은 미확인이다. 오늘 합성 곡선의 +100bp/−100bp는 5.5/10 y4.5에서 −82,220/+90,112, y5.5에서 −75,256/+82,450이다. 화면값(−81,597/+89,400, −74,657/+81,766)과 다르다. 소유자 화면은 다른 곡선(아마 FRED)에서 돈 것으로 보인다(추정). 곡선 스냅샷이 없어 재현할 수 없다.

**4.3 일관성 대조(f4_consistency.py, HEAD)**
| 사례 | 대조 수 | 실패 | DV01 카드 | KRD 합(차트 제목) | 비율 |
|---|---|---|---|---|---|
| C1 calc 5.5/10 y4.5 | 40 | 0 | 836.290 | 860.403 | 1.02883 |
| C2 calc 4.5/10 y5.5 | 40 | 0 | 725.786 | 750.014 | 1.03338 |
| C3 calc 5.5/10 y5.5 | 40 | 0 | 761.363 | 787.384 | 1.03418 |
| C4 calc p95 | 40 | 0 | 714.774 | 741.798 | 1.03781 |
| C5 calc p105 | 40 | 0 | 808.222 | 833.091 | 1.03077 |
| S1 scen y4.5 | 46 | 0 | 836.290 | 860.403 | 1.02883 |
| S2 scen y5.5 | 46 | 0 | 761.363 | 787.384 | 1.03418 |
| H1 hedge 4.5/10 y4.5 | 39 | 0 | 798.186 | 820.588 | 1.02807 |
| H2 hedge pos 798, 명목 2m | 39 | 0 | 1,596.371 | 1,641.177 | 1.02807 |
| E1 calc 만기 0.1y | 40 | 0 | 10.004 | 10.229 | 1.02250 |
대조 대상: 카드 7~13개, 칩 3개, 해설 문장 9개 이상, P/Y 차트 제목·범례 2개, KRD 제목·막대 높이, 시나리오 표 9행·Worst/Best·차트 주석·막대 폭, 헤지 카드·notice 잔여·해설, payload 숫자 15개. 차트 함수는 같은 `bond`·`a.ytm`·`a.krd`·`rows`로 다시 계산한다. 막대 값은 독립값과 1e-6 안에서 같다. payload는 화면과 같은 객체에서 나온다.
E1의 실패 0은 "저장소 식과 같다"는 뜻이다. 그 식 자체의 결함은 F-05다.

**4.4 성능(f1_perf.py, 합성 곡선, 20회, ms, 중앙값/p95)**
| 단계 | calc | scenarios | hedge |
|---|---|---|---|
| 곡선 로드(합성 생성) | 4.34 / 6.19 | 4.41 / 5.68 | 4.05 / 4.41 |
| 부트스트랩 | 4.07 / 6.06 | 4.12 / 4.81 | 3.92 / 5.64 |
| analyze_bond | 2.59 / 3.57 | 2.74 / 3.21 | 2.60 / 2.75 |
| scenario_pnl | – | 0.82 / 1.09 | – |
| 헤지 비율 | – | – | 0.00 / 0.00 |
| 차트(matplotlib) | 207.09 / 256.99 | 123.21 / 150.22 | – |
| 해설 | 0.04 / 0.06 | 0.04 / 0.06 | 0.03 / 0.03 |
| analysis_panel | 0.43 / 0.60 | 0.38 / 0.49 | 0.29 / 0.77 |
| 기타 UI | 1.55 / 2.21 | 2.70 / 4.14 | 1.39 / 1.75 |
| 합계 | 220.77 / 269.59 | 139.19 / 166.24 | 12.39 / 16.70 |
첫 Run(임포트 후): calc 243.1, scenarios 136.8, hedge 11.8. 앱 임포트 약 3초는 P01-13 참조.
analyze_bond 내부(중앙값 ms): price_from_yield 0.010, yield_from_price 0.168, z_spread 0.376, KRD(9×2 재평가) 1.297, carry_roll(z-spread·YTM 다시 풂) 0.629, 듀레이션·볼록성·DV01 0.058, 합계 2.561. scenario_pnl 0.744.

**4.5 FRED 모의·캐시(f2_fred_cache.py, 임시 캐시, TTL 21,600초, 마지막 관측 2026-10-26)**
| 변형 | Run | 벽시계 ms | 네트워크 대기 ms | 호출 | id 요청 | 칩 |
|---|---|---|---|---|---|---|
| A 호출당 300ms | 콜드 #1 | 573.9 | 305.6 | 1 | 11 | curve: FRED 2026-10-26 |
| A | 메모리 웜 #2~#5 | 237.4~301.1 | 0 | 0 | 0 | 같음 |
| A | 도구 scenarios / hedge | 174.1 / 11.0 | 0 | 0 | 0 | 같음 |
| A | source=fred(같은 키) | 212.5 | 0 | 0 | 0 | 같음 |
| A | 디스크 웜(메모리 비움=재시작) | 219.5 | 0 | 0 | 0 | 같음 |
| A | TTL 경과 | 562.0 | 305.4 | 1 | 11 | 같음 |
| B id당 300ms(실제 pdr·requests는 id마다 HTTP 1회) | 콜드 #1 | 3,542.0 | 3,310.6 | 1 | 11 | 같음 |
| B | 웜 | 202.9~323.4 | 0 | 0 | 0 | 같음 |
| C FRED 장애, auto | #1/#2/#3 | 3,811.6 / 3,887.4 / 3,939.1 | 3,602 매번 | 12 매번 | 22 매번 | curve: SYNTHETIC 2026-10-27 + 합성 경고 |
| D FRED 장애, fred | #1 | 3,604.2 | 3,602.3 | 12 | 22 | 오류 notice "FRED served 0/11 tenors (…)" |
pandas_datareader 경로는 id마다 HTTP 1회, 시도 4회(retry_count 3), 시도당 timeout 30초다(설치된 0.11.1 소스 확인). requests 경로는 `config.py:145` 12초, `data/net.py:43-50` 재시도 2회다.

**4.6 재현성(f3_repro.py)**
| 점검 | 결과 |
|---|---|
| 같은 프로세스 3회(calc y, calc p95, scenarios, hedge) | payload float.hex, 모든 글자, 표, PNG sha256 동일 |
| 프로세스 간(PYTHONHASHSEED 0 / 12345 / 현재) | 다이제스트 a12e7244…cbb801 셋 다 동일 |
| 모의 FRED 콜드 / 메모리 웜 / 디스크 웜 | 동일 |
주의: 합성 곡선 값은 시드 고정이라 날마다 같다. 그러나 날짜 라벨은 오늘이다(`core/ficc/data.py:_business_dates:288-295`). 다른 날 실행하면 칩·문장이 바뀐다(D-03·D-04 계열과 같은 원인, 새 결함 아님). 오늘 합성 곡선은 1m 9.586%, 30y 7.171%다. 4.5% 채권의 z-spread가 −317.8bp로 나온다. 합성 경고는 뜬다(D-03 범위).

**4.7 상태(f5_stale.py, HEAD)**
| 상황 | 관찰 |
|---|---|
| 입력 변경 후 Run 없음 | TextField `on_change` 0/8, Coupons/Curve source `on_select` 없음. 화면 변화 없음. 칩은 "notional 1,000,000", "2x coupons" 그대로. stale 문구 없음 |
| 실패한 Run 뒤 | 옛 카드·차트·해설은 지워지고 오류 notice만 남음(정상). 진행 표시 꺼짐. 필드별 오류 없음(A 차원) |
| calc 결과 후 hedge 선택 | hedge 입력 줄이 나타나지만 calc 카드(Carry 등) 그대로. 화면 어디에도 도구 이름 없음 |
| hedge 결과 후 calc 선택 | hedge 입력 숨김, "Contracts to sell 10.29" 카드는 남음 |
| 출처 변경 후 Run 없음 | 칩 "curve: SYNTHETIC 2026-10-27", 드롭다운은 fred |
| 입력 반영 위치 | 쿠폰·만기: 해설(그리고 calc의 P/Y 차트 제목 PNG)만. 빈도·명목: 칩·해설. 출처: 칩. 가격/수익률 입력 방식: 없음. 도구: 없음 |

**4.8 스레드(f6_threads.py, f6b_inorder.py, HEAD vs 수정본)**
| 테스트 | HEAD | 수정본 |
|---|---|---|
| T1 A(쿠폰 5.5) 막힘 → 쿠폰 4.5 → B 완료 → A 완료 | B 직후 Price 100.000, 링 꺼짐, A 살아 있음. 최종 Price 107.982, 해설 "The 5.50% 10y", 필드 4.5 | 최종 100.000, 해설 "The 4.50% 10y" |
| T1b 둘 다 진행 중, 옛 A가 먼저 끝남 | B 로드 중 화면 Price 107.982, 링 꺼짐 | 화면 비어 있고 링 켜짐 → 최종 100.000 |
| T2 클릭(5.5/95/CF 0.8) 후 로드 중 수정(4.5/105/0.7) | Price 105.000, Yield 4.863%, CF 0.7000, 계약 8.70, 해설 "The 5.50% … prices at 105.000" | Price 95.000, Yield 6.178%, CF 0.8000, 계약 8.80 |
| T3 A(fred) 늦게 실패, B(synthetic) 먼저 성공 | 최종: 오류 "FRED served 0/11 tenors (DGS1MO: ReadTimeout: mock)."만, 카드 0, 드롭다운 synthetic | 최종 B 결과(107.982) 유지 |
| T4 진행 표시 | 옛 작업자가 남았는데 링 꺼짐. Run 버튼 비활성화 없음 | 최신 Run 기준으로만 꺼짐(옛 결과는 버림) |
| T5 pyplot 동시 렌더 4스레드×15 | 오류 0, PNG 바이트 차이 0, 16.0초 | 오류 0, 차이 0, 14.9초 |

**4.9 carry/roll 경계(f7_carry_edge.py, 5.5% 쿠폰, y 4.5%, 합성 곡선, 100당)**
| 만기 | 가격 | HEAD 합계 | 독립(관례 일치) | 차이 | HEAD 손익분기 bp | 라벨/h |
|---|---|---|---|---|---|---|
| 0.30 | 101.3874 | −1.2694 | −1.2694 | 0 | −426.7 | 3m/0.25 |
| 0.2501 | 101.6128 | −1.2650 | −1.2650 | 0 | −509.0 | 3m/0.25 |
| 0.25 | 101.6132 | −2.6400 | −1.2650 | −1.3750 | −1062.6 | 3m/0.25 |
| 0.24 | 101.6584 | −2.6457 | −1.2157 | −1.4300 | −1108.8 | 3m/0.24 |
| 0.10 | 102.2938 | −2.7181 | −0.5181 | −2.2000 | −2716.9 | 3m/0.10 |
수정본은 모든 행에서 차이 0이다. 라벨은 h를 따른다("Carry (36d)").

### ⑤ 수정안 (복사본 `repo_fixed/`에 적용·검증. 저장소에는 적용하지 않음)
- `ui/bonds_page.py`: (1) 실행 토큰 `run_id`와 `paint()` 가드. 최신 Run만 결과·오류·진행 표시를 바꾼다. (2) `_Frozen`으로 클릭 순간의 필드 값을 고정한다. 작업자는 살아 있는 필드를 읽지 않는다. (3) 결과 맨 위에 "Computed for: …" 줄(요청의 "계산 기준" 줄. 화면 언어에 맞춰 영어)을 둔다. 도구, 쿠폰, 만기, 빈도, 입력 방식(yield/price input), 명목, 곡선 출처·날짜, 헤지면 CTD DV01·CF·position DV01(override/calculator). (4) Run 뒤 입력 수정·드롭다운 변경·도구 전환 시 결과 위 stale 배너. 다음 Run에서 숨김.
- `core/ficc/bonds.py:carry_roll`: 만기 안에 끝나는 채권은 모든 현금흐름을 현금으로 본다. `horizon=h`로 실제 기간을 돌려준다.
- 선택(미적용): P01-05의 잠금/버튼 비활성화(중복 작업 비용). 토큰은 정확성만 고친다. FRED 실패 캐시(F-06). pyplot 대신 `matplotlib.figure.Figure`(F-08). payload에 같은 입력 반영 사전.
- 성능 영향: HEAD/수정본 교차 측정 합계 calc 220.5·236.0 vs 267.9·250.4ms, scenarios 146.6·129.1 vs 136.6·139.4ms, hedge 12.6·11.7 vs 13.9·11.7ms. 차트 잡음 범위 안이다. 추가 작업은 필드 8개 복사와 문자열 하나다.

```diff
--- a/ui/bonds_page.py
+++ b/ui/bonds_page.py
@@ -49,6 +49,13 @@
     return v
 
 
+class _Frozen:
+    """A field's label and value as they were when Run was pressed (what `_num` reads)."""
+
+    def __init__(self, field) -> None:
+        self.label, self.value = field.label, field.value
+
+
 def _shock_text(shock) -> str:
@@ -83,42 +90,76 @@
     busy = ft.ProgressRing(visible=False, width=20, height=20)
     result_host = ft.Column(spacing=14)
+    run_id = [0]                      # token of the newest Run; an older worker never paints
+    stale = notice("Inputs changed since the last Run: the results below are for the inputs on "
+                   "their 'Computed for' line. Press Run to update.", "warning", icon=ft.Icons.HISTORY)
+    stale.visible = False
+
+    def mark_stale(e=None) -> None:
+        if run_id[0] and not stale.visible:
+            stale.visible = True
+            page.update()
+
+    for _f in (coupon, maturity, price, ytm, notional, ctd_dv01, cf, pos_dv01):
+        _f.on_change = mark_stale
+    for _d in (freq, source):
+        _d.on_select = mark_stale
 
     def on_tool(e=None) -> None:
         hedge_row.visible = tool.value == "hedge"
+        stale.visible = stale.visible or bool(run_id[0])
         page.update()
@@
     def run(e=None) -> None:
+        run_id[0] += 1
+        me = run_id[0]
+        F = {f: _Frozen(f) for f in (coupon, maturity, price, ytm, notional, ctd_dv01, cf, pos_dv01)}
+        kind0, freq0, source0 = tool.value or "calc", freq.value or "2", source.value or "auto"
         busy.visible = True
+        stale.visible = False
         result_host.controls = []
         page.update()
 
-        def fail(text: str) -> None:
-            result_host.controls = [notice(text, "error", icon=ft.Icons.ERROR_OUTLINE)]
+        def paint(controls: list) -> None:
+            if me != run_id[0]:                       # a newer Run owns the screen
+                return
+            result_host.controls = controls
             busy.visible = False
             page.update()
 
+        def fail(text: str) -> None:
+            paint([notice(text, "error", icon=ft.Icons.ERROR_OUTLINE)])
+
         def worker():
-            kind = tool.value or "calc"
+            kind = kind0
             try:
-                bond = Bond(coupon=_num(coupon, 0.0) / 100.0, maturity=_num(maturity, 10.0),
-                            freq=int(freq.value or "2"), notional=_num(notional, 1e6))
-                y = _num(ytm)
-                panel = load_treasury_curve(source=source.value or "auto")
+                bond = Bond(coupon=_num(F[coupon], 0.0) / 100.0, maturity=_num(F[maturity], 10.0),
+                            freq=int(freq0), notional=_num(F[notional], 1e6))
+                y = _num(F[ytm])
+                px = _num(F[price])
+                panel = load_treasury_curve(source=source0)
                 curve = curve_from_snapshot(panel.latest())
-                a = analyze_bond(bond, price=_num(price), ytm=None if y is None else y / 100.0,
+                a = analyze_bond(bond, price=px, ytm=None if y is None else y / 100.0,
                                  curve=curve)
@@
-                    pos, ctd, c = _num(pos_dv01, a.dv01), _num(ctd_dv01, 65.0), _num(cf, 1.0)
+                    pos, ctd, c = _num(F[pos_dv01], a.dv01), _num(F[ctd_dv01], 65.0), _num(F[cf], 1.0)
@@
-                blocks: list[ft.Control] = []
+                quote = f"yield {y:.3f}% (input)" if y is not None else f"price {px:.3f} (input)"
+                echo = (f"Computed for: {dict(_TOOLS)[kind]} | coupon {bond.coupon * 100:.2f}% | "
+                        f"{bond.maturity:g}y | {bond.freq}x | {quote} | notional {_money(bond.notional)} | "
+                        f"curve {curve.source} {curve.date}")
+                if kind == "hedge":
+                    echo += (f" | CTD DV01 {hedge[1]:,.2f} | CF {hedge[2]:.4f} | position DV01 "
+                             f"{_money(hedge[0])} ("
+                             f"{'override' if (F[pos_dv01].value or '').strip() else 'calculator'})")
+                blocks: list[ft.Control] = [ft.Text(echo, size=12, color=pal.muted, selectable=True)]
@@
-                result_host.controls = blocks
-                busy.visible = False
-                page.update()
+                paint(blocks)
@@
-        ft.Column([result_host], scroll=ft.ScrollMode.AUTO, expand=True),
+        ft.Column([stale, result_host], scroll=ft.ScrollMode.AUTO, expand=True),
--- a/core/ficc/bonds.py   (CRLF 파일. 줄바꿈 유지해서 적용)
+++ b/core/ficc/bonds.py
@@ -181,7 +181,8 @@
-    A bond that matures inside the horizon rolls to face.
+    A bond that matures inside the horizon pays face and its last coupon(s) in
+    cash; `horizon` on the result is the horizon actually used, min(horizon, maturity).
@@ -198,14 +199,14 @@
-    else:
-        clean_aged = bond.face
+    else:                             # matures inside the horizon: every cashflow is cash
+        clean_aged = float(np.sum(cashflows(bond)[1])) - accrued
@@
-                     breakeven_bp=total / slope / BP if slope > 0 else 0.0, horizon=horizon)
+                     breakeven_bp=total / slope / BP if slope > 0 else 0.0, horizon=h)
```
전체 diff: `proposed_fix.diff`(153줄). 적용 스크립트: `apply_fix.py`(`repo_fixed` 외 경로 거부).

### ⑥ 테스트 로그
| 테스트 | 대상 | 결과 | 로그 |
|---|---|---|---|
| `python3 -B -m ui.bonds_page` 자체 검사 | HEAD 복사본 / 수정본 | PASS / PASS | head_selfchecks.log, fixed_selfchecks.log |
| `python3 -B -m core.ficc.bonds` 자체 검사 | HEAD / 수정본 | PASS / PASS | 같음 |
| `tests/ficc_acceptance.py` tests() 57개(in-process) | HEAD / 수정본 | 57/57 PASS / 57/57 PASS | ficc_tests_head.log, ficc_tests_fixed.log |
| 제안 회귀 테스트 7개 | HEAD | 2/7 PASS. FAIL: newest_run_wins, run_reads_inputs_once, late_failure, stale_banner_and_echo, carry_no_jump | proposed_tests_head.log |
| 같음 | 수정본 | 7/7 PASS | proposed_tests_fixed.log |
| f1 성능 | HEAD / 수정본 / 교차 2회 | 측정 완료 | f1_perf*.log, f1_perf_ab.log |
| f2 캐시·FRED 모의 | HEAD | 측정 완료 | f2_fred_cache.log |
| f3 재현성 | HEAD | PASS(전부 동일) | f3_repro.log |
| f4 일관성 410개 | HEAD | 410/410 일치 | f4_consistency_head.log |
| f4 일관성 | 수정본 | 402/410. 실패 8개는 E1 carry 값이 F-05 수정으로 바뀐 것(의도) | f4_consistency_fixed.log |
| f5 상태 | HEAD | 결함 재현 | f5_stale.log |
| f6 스레드 T1-T5 | HEAD / 수정본 | T1-T3 결함 재현 / 해소. T5 양쪽 오류 0 | f6_threads.log, f6_threads_fixed.log |
| f6b 동시 진행 | HEAD / 수정본 | 결함 재현 / 해소 | f6b_inorder_head.log, f6b_inorder_fixed.log |
| f7 carry 경계 | HEAD / 수정본 | 차이 최대 −2.2 / 0 | f7_carry_edge_head.log, f7_carry_edge_fixed.log |
| f8 수정 검증(배너·반영 줄) | 수정본 | ALL_OK true | f8_fix_verify.log |
| f9 독립 수치 | HEAD | 최대 |차| 1.5e-11(손익분기), 화면 관찰 30/30 일치 | f9_numbers.log |
| `tests/run_all.py` | – | NOT_RUN(규칙상 금지: qa/acceptance_results.json을 다시 씀) | – |
| 실제 Flet 데스크톱 창 | – | NOT_RUN(stand-in Page만) | – |
| 실제 FRED 네트워크 | – | NOT_RUN(모의만) | – |

### ⑦ 남은 리스크와 미확인
- 실제 Flet 런타임에서 `page.update()`를 여러 스레드가 부를 때의 동작은 미확인이다. stand-in Page로 순서 결함만 증명했다.
- pyplot 스레드 안전성(F-08)은 60회 동시 렌더에서 문제를 못 봤다. 문제가 없다는 증거는 아니다. 미확인.
- 실제 FRED 지연·타임아웃·부분 실패의 빈도와 시간은 미확인이다. F-06의 최악 시간은 코드에서 계산한 추정이다.
- 2.3절 화면 시나리오 수치는 곡선 스냅샷이 없어 재현하지 못했다(미확인). 곡선과 무관한 2.1절 수치는 모두 재현했다.
- 소유자 PC의 Run 시간은 미확인이다. 여기 수치는 클라우드 컨테이너 값이다.
- 합성 곡선의 수준(단기 9.6%)과 오늘 날짜 라벨은 D-03·D-04·E 차원 범위다. 여기서는 재현성 맥락으로만 적었다.
- 수정본의 stale 배너는 실패한 Run 뒤에도 켜질 수 있다(`run_id`가 실패 Run도 센다). 해롭지 않지만 문구가 정확하지 않을 수 있다.
- 실거래·시장 정확성은 이 차원에서 검증하지 않았다. 위 일치는 "화면이 같은 입력·같은 계산을 쓴다"는 뜻이다. 공식이 시장 관례와 맞는다는 증거는 아니다.

### 스크립트·산출물 경로 (모두 /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/F_perf_state/)
harness.py, indep.py, f1_perf.py, f2_fred_cache.py, f3_repro.py, f4_consistency.py, f5_stale.py, f6_threads.py, f6b_inorder.py, f7_carry_edge.py, f8_fix_verify.py, f9_numbers.py, run_ficc_tests.py, apply_fix.py, proposed_fix.diff, proposed_test_bonds_ui_state.py, 결과 *.json·*.log, 복사본 repo/(HEAD), repo_fixed/(수정본), orig/(원본 두 파일).

### 독립 검증

검증 작업 폴더: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/verify_F_perf_state/`. `repo/`는 내가 새로 만든 HEAD 복사본이다. `repo_fixed/`는 조사자의 `apply_fix.py`로 패치한 복사본이다. 저장소의 `git status`는 깨끗하다(0줄). 금지된 캐시 4개는 열지 않고 지웠다. `.env`는 열지 않았다. `tests/run_all.py`는 실행하지 않았다.

| id | 유지 여부 | 정정 심각도 | 정정 상태 | 근거 |
|---|---|---|---|---|
| F-01 | 유지 | P1 | 테스트로 확인됨 | `v_threads.py`로 실제 스레드를 띄워 재현했다. T1: B가 끝난 뒤 Price는 100.000이다. A가 끝나면 107.982로 바뀌고 해설은 "The 5.50% 10y"인데, 입력 필드는 4.5다. T1b: B가 로드 중일 때 A의 107.982가 보이고 진행 링은 꺼져 있다. T3: 늦게 실패한 A의 오류 notice만 남고 B의 결과는 사라진다. Flet 0.85.2에서 `run_thread`는 실제 executor 스레드다(`flet/controls/page.py:827-846`). 따라서 stand-in 페이지에서만 생기는 문제가 아니다. P01-05(P2, 일반 재클릭)와 겹친다. 다만 P01-05의 잠금 수정만 넣으면 두 번째 클릭이 무시될 뿐이다. 그래도 옛 결과는 새 입력 아래에 그대로 남는다. 그래서 토큰이 따로 필요하고 P1을 유지한다. 수정안에 대한 주의: `paint`의 검사와 대입 사이에 새 Run이 끼어드는 마이크로초 단위의 틈이 있다. 최종 상태는 새 Run이 다시 덮어쓰므로 정확하다. |
| F-02 | 유지 | P2 | 테스트로 확인됨 | `v_threads.py` T2를 HEAD에서 돌렸다. 결과는 Price 105.000, Yield 4.863%, CF 0.7000, 계약 8.70이고, 해설은 "The 5.50% … prices at 105.000"이다. 수정본에서는 95.000, 6.178%, 0.8000, 8.80이다. 코드도 같은 상황을 보여 준다. `:105-109`는 곡선 로드 전에, `:112`와 `:117`은 로드 후에 입력을 읽는다. |
| F-03 | 유지 | P2 | 테스트로 확인됨 | TextField 8개 가운데 `on_change`가 있는 것은 0개다. freq와 source에는 `on_select`가 없다. 입력을 바꾼 뒤 Run 없이 화면 글자를 비교하면 그대로다. 칩은 "2x coupons", "notional 1,000,000"에 머문다. 도구를 바꾼 뒤에도 "Carry (…)" 카드가 남는다. 화면 어디에도 도구 이름이 없다. |
| F-04 | 유지 | P2 | 테스트로 확인됨 | 재현값은 DV01 1,596, Position DV01 798, Contracts 9.82다. "override"라는 표시는 없다. 계산기 DV01 기준이라면 1,596.371×0.8/65 = 19.6476으로, 독립 계산과 일치한다. 보정: hedge 도구에서는 필드(값 798, 라벨 "(blank = calculator)")가 보인다. 필드가 숨는 것은 다른 도구를 고른 동안뿐이다. 핵심 결함은 override 값과 `a.dv01`이 크게 달라도 경고가 없다는 점이다. |
| F-05 | 유지 | P2 | 테스트로 확인됨 | 독립 계산 결과다(만기 현금 합 − 가격 − funding). T=0.2501일 때 −1.2650, T=0.25일 때 HEAD는 −2.6400, 독립값은 −1.2650이다. T=0.10일 때 HEAD는 −2.7181, 독립값은 −0.5181이다. `horizon=0.25`가 그대로 반환되어 라벨이 "3m"으로 남는다. 추가 근거: freq=1, T=0.25이면 −5.4368 대 −1.3118로 −4.125만큼 어긋난다. freq 4와 12에서는 T=0.25에서 끊김이 없다. **B 차원과 중복이다.** `B_pricing_risk/proposed_fix.diff`가 같은 else 분기를 같은 결과로 고친다. 병합은 한 번만 해야 한다. `horizon=h`(라벨 수정)는 F에서만 나온 부분이다. 수정안에 대한 주의: `apply_fix.py`가 `core/ficc/bonds.py`의 CRLF를 LF로 바꿨다(CR 403개 → 0개). 의미가 바뀌는 부분은 3개 hunk뿐이다. 저장소에 적용할 때는 diff에 적힌 대로 CRLF를 유지해야 한다. |
| F-06 | 유지 | P2 | 테스트로 확인됨(모의). 최악 시간은 추정 | 모의 장애(호출당 100ms)를 auto와 fred에서 각각 3회 돌렸다. 매번 `_fred_fetch` 12회(id 22개)가 호출되고, 두 번째 Run부터도 줄지 않는다. 정상 FRED에서는 웜 상태 호출이 0회다. pandas_datareader 0.11.1 소스를 확인했다. `_get_response`는 `RequestException`을 `retry_count+1`=4회 재시도하고 timeout은 30초다. 따라서 "Run당 약 24분"은 연결이 응답 없이 막힌(blackhole) 경우의 추정이다. DNS 실패나 연결 거부처럼 즉시 실패하면 Run당 수 초다(추정). |
| F-07 | 유지 | P3 | 테스트로 확인됨 | DV01 836.290과 KRD 합 860.403을 독립 계산으로 재현했다. KRD 합은 Σt·cf·DF·e^{-zt}·1bp·N/100으로 계산한 zero DV01 860.403과 같다. **원인 서술은 바로잡아야 한다.** 비율이 1+y/f가 되는 것은 bond의 yield와 같은 평탄 곡선일 때뿐이다(1.0225). 화면 곡선에서는 1.02883(y4.5)과 1.03418(y5.5)이다. financial_calcs 11행은 평탄 곡선을 시험한 결과다(F-M2 참조). |
| F-08 | 유지 | P3 | 코드로 확인됨(위험은 미확인) | `ui/qcharts.py:21`과 `:48-52`에서 pyplot `plt.subplots`/`plt.close`를 작업 스레드에서 쓴다. P01-05의 영향 칸이 이미 이 위험을 "추정 위험"으로 적었다. 부분 중복이다. |

**독립 수치 재계산** (`v_indep.py`, `v_curve_spot.py`. 저장소 가격 함수는 부르지 않았다. 곡선 DF만 데이터로 썼다.)
- 5.5/10 y4.5: P 107.981856, Mac 7.919, Mod 7.745, Cvx 73.015, DV01 836.290(중앙차분 836.290).
- p95 YTM 6.177690%, p105 YTM 4.862682%. 4.5/10 y5.5: P 92.386374, DV01 725.786. 조사자 표와 6/6 사례 모두 일치한다.
- z-spread: 독립값 −317.75bp, 저장소 −317.75bp. ±100bp: 독립값 −82,220/+90,112, 저장소도 같다.
- 헤지: 9.8215(override 798) 대 19.6476(계산기 1,596.371).
- 성능(`v_perf.py`, 10회 중앙값): calc 259.8ms, scenarios 164.9ms, hedge 12.3ms. 단계별로는 load 4.17, bootstrap 4.18, analyze 2.65, scenario 0.81ms다. 조사자 값과 같은 크기이고, 차이는 차트 잡음 범위다.

**수정안·회귀 테스트 확인**
- 제안 테스트 7개를 내 복사본에서 돌렸다. HEAD 2/7, 수정본 7/7이다. HEAD에서 실패한 것은 newest_run_wins, reads_inputs_once, late_failure, stale_banner_and_echo, carry_no_jump이다. 수정 전 실패, 수정 후 통과가 확인됐다.
- `tests/ficc_acceptance.py` tests()를 in-process로 돌렸다. HEAD와 수정본 모두 57/57이다.
- `python3 -B -m core.ficc.bonds`, `-m ui.bonds_page` 자체 검사는 두 복사본 모두 ok다.
- 수정본에서 `v_threads.py`를 돌렸다. T1b는 로드 중 화면이 비고 링이 켜졌다가 최종 100.000이다. T2는 95.000, T3는 B의 107.982를 유지한다.
- NOT_RUN: 실제 Flet 데스크톱 창, 실제 FRED 네트워크, `tests/run_all.py`(규칙상 금지).

### 조사자가 놓친 항목

#### F-M1 · P3 · 테스트로 확인됨 — 결과가 어떤 곡선 값에서 나왔는지 기록하지 않는다(재현·감사 불가)
- 위치: `ui/bonds_page.py:125-130`(칩은 출처·날짜·방법·세션 수만 보임), `:141-154`(payload `curve`는 source/date/method/note만 담음), `core/ficc/data.py:268-281`(캐시는 TTL 뒤 같은 키로 덮어써서 과거 스냅샷이 남지 않음).
- 재현: `v_repro_gap.py`. 모의 FRED에 날짜는 같고 수준만 다른 두 응답(4.0%대, 4.3%대)을 주고 scenarios 5.5/10 y4.5로 Run한다.
- 기대: 결과마다 사용한 곡선 노드(만기별 par/zero), 수신 시각 또는 스냅샷 해시가 남는다. 그래야 같은 스냅샷으로 다시 계산할 수 있다(요청서 3.F 둘째 항목, 4절 "시나리오 재평가… 로그").
- 실제: 두 Run 모두 칩이 "curve: FRED 2026-10-26", "bootstrap, 84 sessions"이고 payload `curve`도 같다. 그런데 z-spread는 40.24bp 대 10.60bp, +100bp는 −81,567.87 대 −81,566.48로 다르다. 화면 글자에도 par 금리 값이 없다. 조사자도 이 때문에 2.3절 화면 시나리오 값을 재현하지 못했다.
- 원인: payload와 칩이 곡선의 메타데이터만 싣는다.
- 영향: 화면의 z-spread, carry, KRD, 시나리오 숫자를 나중에 검증하거나 재현할 수 없다. 2.3절 값은 계속 미확인으로 남는다.
- 수정: payload `curve`에 `tenors`, `par_yields`, `zeros`, `fetched_at`(캐시 ts), `snapshot_id`(par 값의 sha256 앞 12자)를 넣는다. 결과 맨 위에 "curve FRED 2026-10-26 · id abc123def456" 한 줄을 둔다. 원하면 노드 표를 접힌 상태로 보인다.
- 회귀 테스트: payload의 `par_yields`가 `panel.latest().par_yields`와 같은지 확인한다. 날짜가 같고 값이 다른 두 패널은 `snapshot_id`가 달라야 한다.

#### F-M2 · P3 · 테스트로 확인됨 — "KRD 합 = DV01×(1+y/f)" 설명은 평탄 곡선에서만 맞다
- 위치: `core/ficc/bonds.py:15-18` docstring. 같은 주장을 F-07 원인 서술과 financial_calcs 11행(평탄 곡선 시험)이 인용한다.
- 재현: `v_curve_spot.py`.
- 기대: docstring이 성립 조건을 밝힌다.
- 실제: bond의 yield와 같은 평탄 곡선에서는 1.0225(=1+0.045/2)다. 화면의 합성 곡선에서는 1.02883(5.5/10 y4.5)과 1.03418(5.5/10 y5.5)이다. 1+y/f(1.0225, 1.0275)와 다르다. 독립 zero DV01 860.403과 787.384는 KRD 합과 같다.
- 원인: 비율이 곡선 모양과 z-spread 가중에 따라 달라지는데, 문서는 이를 상수처럼 적었다.
- 영향: 검토자나 AI가 두 숫자의 차이를 "문서대로"라고 보고 넘길 수 있다. 화면 라벨이 없는 F-07 문제를 키운다.
- 수정: docstring에 "곡선이 bond의 yield에서 평탄할 때(z≈0)만 (1+y/f)배. 그 밖에는 곡선 모양에 따라 다름"이라고 적는다.
- 회귀 테스트: 아무 곡선에서나 KRD 합이 해석식 zero DV01(Σt·cf·DF·e^{-zt}·1bp·N/100)과 1e-3 안에서 같은지 본다. 평탄 곡선에서는 비율이 1+y/f와 1e-6 안에서 같은지 본다.
