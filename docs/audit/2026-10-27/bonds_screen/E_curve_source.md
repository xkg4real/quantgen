# Bonds 화면 검증 E. 곡선 출처와 데이터 신뢰성

> 작성 메모 (오케스트레이터): 하네스가 하위 에이전트의 보고서 파일 쓰기를 막아, 조사 에이전트가 반환한 본문과 독립 검증자가 반환한 검증 절을 내용 변경 없이 옮겼습니다. 저장소 코드는 바꾸지 않았습니다.

## E. Curve source 및 데이터 신뢰성 (요청서 3.E, 수용 기준 "데이터 출처")

작업 위치: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/E_curve_source/` (아래에서는 `W/`로 줄여 쓴다. 전체 경로는 9장에 있다). 저장소의 추적 파일은 고치지 않았다(`git status --short` 0줄). 모든 실행은 `git archive HEAD` 스크래치 사본(`W/repo`, 수정 검증용 `W/repo_fix`)에서 했다. 소켓은 하네스가 막았다. HOME·`NEXTGEN_FICC_CACHE`·`MPLCONFIGDIR`는 `W/home`으로 돌렸다. `.env`는 열지 않았다(사본에 없음). 이 문서의 "캔드 FRED 프레임" 값(1m 4.05 … 10y 4.05, 20y 4.60, 30y 4.62 %)은 하네스용으로 지어낸 값이다. 시장 데이터가 아니다.

### ① 요약

- **출처 구분 자체는 동작한다(테스트로 확인됨).** `auto`에서 FRED가 예외를 내거나, 빈 값·5행 미만을 주거나, 2y·10y가 빠지면 합성 곡선으로 바뀐다. 이때 빨간 배너 "Synthetic data: FRED failed: …"와 칩 `curve: SYNTHETIC 2026-10-27`이 뜬다. `fred`를 명시하면 오류 배너만 뜨고 이전 결과는 지워진다. `synthetic`은 공급자를 0회 부른다.
- **약점은 "FRED이지만 믿기 어려운" 경우다.** 오래된 곡선(E-01), 만기별로 날짜가 섞인 곡선(E-02), 단위·오타 값(E-03)이 모두 녹색 `curve: FRED <날짜>` 칩으로, 배너 없이 계산된다. 일부 만기가 빠진 곡선(D03-V01)도 같다. 그때 Bonds 시나리오의 장기물 충격은 마지막 곡선 만기에서 멈춘다(E-09). 30y 채권의 bear steepener가 −59,696 대신 −22,369로 나온다.
- **날짜 의미.** FRED 칩의 날짜는 만기 합집합에서 가장 늦은 관측일이다(forward-fill 후 마지막 행). 합성 칩의 날짜는 오늘(평일)이다. 합성 숫자는 고정 seed라 매일 같고 날짜만 바뀐다. 수신 시각과 계산 시각은 화면에 없다(E-04, 기존 C01-05·D04-02).
- **부트스트랩과 보간은 독립 구현과 일치한다.** 동시 Newton 풀이와 비교했다. 4개 곡선에서 zero 차이는 ≤2.1e-15, 0~40y DF 차이는 ≤1.4e-14다. 보간은 ln DF가 t에 선형(즉 z·t 선형)이고 양 끝은 zero가 평평하다.
- **곡선과 무관한 숫자.** Price·Yield·Macaulay·Modified·Convexity·DV01·헤지 계약 수는 출처와 무관하다. FRED, 합성, 부분, 오래된 곡선에서 모두 같다. 출처에 따라 바뀌는 것은 z-spread, Carry/Roll, Breakeven, KRD, 시나리오 P&L이다.
- **소유자 화면.** 요청서 2.3의 시나리오 숫자는 현재 합성 패널로 재현되지 않는다(±100bp에서 600~712 차이). `data.py`는 2026-10-23 기준선 이후 바뀌지 않았다. 따라서 소유자 화면은 합성 곡선이 아니었다(테스트로 확인됨). 실제 FRED였는지는 칩 캡처가 없어 미확인이다.
- **실제 FRED는 NOT_RUN이다.** 프록시가 `fred.stlouisfed.org`를 403으로 막았다. 실시장 정확성은 검증하지 못했다.

### ② 심각도별 이슈

| ID | 심각도 | 판정 | 한 줄 |
|---|---|---|---|
| E-01 | P2 | 테스트로 확인됨 | 수개월 된 FRED 곡선도 녹색 칩, 경고 없음 |
| E-02 | P2 | 테스트로 확인됨 | 만기별 forward-fill이 만기별 관측일을 숨김. 칩 날짜는 가장 늦은 만기 하나가 정함 |
| E-03 | P2 | 테스트로 확인됨 | 범위·단위·급변 검사 없음. 10y 14.05 오타면 z-spread −1802.3bp가 녹색 FRED로 표시 |
| E-09 | P2 | 테스트로 확인됨 | 시나리오 충격이 곡선 knot에만 적용됨. 부분 곡선에서 30y 충격이 +50bp가 아니라 +14.3bp |
| E-04 | P3 | 테스트로 확인됨 | 칩 날짜의 종류(관측일·생성일)가 적혀 있지 않음. 합성 날짜는 매일 오늘. "504 sessions" 칩이 오해를 부름 |
| E-05 | P3 | 테스트로 확인됨 | 곡선 의존 카드·차트 제목·시나리오 표에 출처 표시 없음. 출처 표시는 배너 하나뿐 |
| E-06 | P3 | 테스트로 확인됨 | 쓰인 par·zero·DF와 보간 관례가 화면·페이로드에 없음. 보간을 바꾸면 15y z-spread가 8.1bp 다름 |
| E-07 | P3 | 테스트로 확인됨 | 실패 사유 원문 11개가 배너와 AI 페이로드에 그대로 들어감(최대 4,961자, 프록시 host:port 포함) |
| E-08 | P3 | 테스트로 확인됨 | `fred` 실패 시 곡선과 무관한 결과까지 막힘. 실패가 캐시되지 않아 오프라인 `auto`는 Run마다 약 5초 |

기존 발견사항 재확인(새 ID 아님):

| 기존 ID | 이번 재확인 | 상태 |
|---|---|---|
| D03-03 | 합성으로 바뀐 경로 전부(B·C·E_missing_2y·S)에서 Bonds 해설에 SYNTHETIC/simulated가 없다. 예: "Against the curve the bond trades at a z-spread of -315.9bp (curve price 77.523)… yields must fall 17.8bp" | 테스트로 확인됨 |
| D03-04 | Bonds는 `analysis_panel(...)`에 `deep_fn`을 넘기지 않는다(`ui/bonds_page.py:214-215`). 그래서 `core.quant.insights.deep_analysis`(`ui/ai_panel.py:33`)를 쓴다. 페이로드에는 `data_source`, `curve.source/date/note`가 있다 | 코드로 확인됨(API 호출은 NOT_RUN) |
| D03-07 | 캐시가 TTL보다 1초 늦었고 FRED가 실패하면 → `auto`는 SYNTHETIC, `fred`는 오류(e02 4단계) | 테스트로 확인됨 |
| D03-08 | 합성 칩 token이 `muted`다. 중립 칩 `bootstrap, 504 sessions`와 같은 회색이다 | 테스트로 확인됨 |
| D03-V01 | Bonds 화면 수치. 1m·3m·6m·20y·30y가 빠지면 Carry가 모든 채권에서 +0.142 → **+0.233**(3m zero가 1y knot 3.568%로 평평하게 연장됨). 20y·30y가 빠지면 4.5% 30y의 z-spread가 −12.2bp → **+41.8bp**. 칩은 녹색이고 "Missing tenors"는 페이로드 `curve.note`에만 있다 | 테스트로 확인됨 |
| C01-02 / C01-05 / C01-06 / D04-01 / D04-02 | 캐시 적중 검증 없음, 수신 시각 없음, stale 정책 없음, as_of가 지연을 가림(매크로). E-02는 D04-01과 같은 부류의 곡선 경로 사례다 | 인용(코드로 확인됨) |

### ③ 재현 단계

모든 스크립트는 `python3 -B <스크립트>`로 실행한다. `E_REPO`로 사본을 고를 수 있다(기본은 `W/repo`).

1. `e01_page_paths.py`: `core.ficc.data._fred_fetch`를 스텁으로 바꾼다. 실제 `build_bonds_page`를 stand-in Page(`run_thread=lambda fn: fn()`)로 만들고 Run을 누른다. 결과 영역의 칩·배너·카드, `analysis_panel`에 넘어간 해설·페이로드, 차트 제목(+PNG)을 모은다. 캐시 TTL은 0이다. 경우 16가지 × `auto`/`fred` × calc/scenarios(+hedge), 그리고 `synthetic`.
2. `e02_cache.py`: TTL 21600, 캐시 디렉터리는 `W/home/ficc_cache`. 차가운 캐시 → 메모리 → 디스크 순서로 읽는다. TTL 안에서 FRED 장애, TTL 초과, running-bar 10분 규칙, id별 캐시 혼합, TTL 0을 확인한다.
3. `e03_bootstrap.py`: 독립 부트스트랩(순수 Python, 동시 Newton)과 저장소 `bootstrap_par_curve`를 비교한다. 곡선 의존 카드도 독립 계산과 비교한다.
4. `e04_curve_dependence.py`: 같은 채권(쿠폰 4.5%, 수익률 4.5%, 1,000,000)의 10y·30y를 변형 곡선 8종에서 화면으로 실행한다.
5. `e06_mechanisms.py`: 충격이 knot에서 잘리는지 보고, `date.today`를 바꿔 합성 날짜가 어떻게 움직이는지 본다.
6. `e09_owner_screen_source.py`: 소유자 화면 숫자를 합성 패널과 캔드 곡선으로 다시 계산한다.
7. `e05_run_tests.py [repo]`: 기존 자체검사와 수용 테스트를 실행한다. `e07_regression.py`: 제안한 회귀 테스트. `e08_timing.py`: 실행 시간.

e01 결과(화면이 실제로 보인 것):

| 경우 | `auto` 화면 | `fred` 화면 | Run 1회당 공급자 호출 |
|---|---|---|---|
| A 정상(캔드) | 칩 `curve: FRED 2026-10-23` success, 배너 없음, z +44.6bp | 같음 | 1(11개 id 일괄) |
| B `FICCError` / `ConnectionError` | 빨간 배너 "Synthetic data: FRED failed: FRED served 0/11 tenors (…)", 칩 `curve: SYNTHETIC 2026-10-27` muted, z −315.9bp | 오류 배너만. 칩·카드 없음 | 12(일괄 1 + id별 11) |
| B 실제 `_fred_fetch`(pandas_datareader 0.11.1, 소켓 차단) | 같음. 배너 4,961자. Run 5.1~5.2초 | 오류 배너. 4.9초 | 실제 |
| C `{}` / 빈 행 / 3행(<5) | 합성 + 배너 "returned only 0/3 observations" | 오류 배너 | 1 |
| D 전체가 2026-06-30에 끝남 | 칩 `curve: FRED 2026-06-30` **success**, 배너 없음 | 같음 | 1 |
| D DGS30만 2026-08-14에 끝남(4.95) | 칩 `FRED 2026-10-23` success, 배너 없음. 30y 채권 z −47.7bp | 같음 | 1 |
| D DGS1MO만 2026-10-26 행이 더 있음 | 칩 `FRED 2026-10-26`(10/11 만기는 10-23) | 같음 | 1 |
| E DGS30 없음 / DGS20·30 없음 / 6개만 | 칩 success, 배너 없음, note는 페이로드에만 | 같음 | 12 |
| E DGS2 없음 | 합성 + 배너 "FRED served 10/11 tenors (DGS2: …)" | 오류 배너 | 12 |
| F 10y 40.5 | 오류 "Bootstrap cannot bracket a zero rate at 10y for par yield 40.5000%."(FRED 언급 없음) | 같음 | 1 |
| F 10y 마지막 값만 14.05 (`auto`만 실행) | 칩 success, z **−1802.3bp**, Roll-down +5.534, 배너 없음 | — | 1 |
| F 소수 단위(4.05 대신 0.0405) | 칩 success, z **+441.0bp**, Carry +1.115 | 같음 | 1 |
| S `synthetic` | 빨간 배너 + muted 칩 | — | 0 |

모든 합성 경우에서 해설에 "SYNTHETIC/simulated"가 없었다. 차트 제목은 `'Key-rate DV01, z-spread -315.9bp held — total 821 per bp'`, `'Scenario P&L — full revaluation, z-spread held'`로 출처가 없다. 페이로드에는 `data_source: SYNTHETIC`이 있다.

### 코드 추적표 (file:function:line)

| 단계 | 위치 | 내용 |
|---|---|---|
| 출처 선택 | `ui/bonds_page.py:29-30,75-76` | `auto` "Auto (FRED, else synthetic)", `fred`, `synthetic` |
| 곡선 로드 | `ui/bonds_page.py:build_bonds_page.run.worker:110-111` | `load_treasury_curve(source)` → `curve_from_snapshot(panel.latest())`. Run마다 다시 읽는다 |
| 라우팅 | `core/ficc/data.py:load_treasury_curve:552-568` | `synthetic` → `synthetic_curve_panel`. `fred` → `_treasury_from_fred`, `FICCError`는 그대로 올린다. `auto` → `FICCError`일 때만 합성으로 바꾸고 note에 "FRED failed: …"를 붙인다(:564-568) |
| FRED 시리즈 | `data.py:67-68` | DGS1MO, DGS3MO, DGS6MO, DGS1, DGS2, DGS3, DGS5, DGS7, DGS10, DGS20, DGS30 ↔ `UST_TENORS`(`common.py:14-15`, 1/12…30) |
| 전송 | `data.py:_fred_fetch:163-192` | pandas_datareader가 있으면 `DataReader(ids,"fred",start)`, NaN은 dropna. 없으면 `fredgraph.csv?id=&cosd=`. 무키라 URL에 키가 없다 |
| 캐시 우선 | `data.py:_provider_rows:449-495` | 키 `FRED_<id>_504`(:220-221). 일괄 실패면 id별로 다시 시도(:479-484). 5행 미만이면 실패(:487-488). 새로 받은 것만 `_cache_put`(:491) |
| 캐시 | `data.py:_cache_get:233-265`, `_cache_put:268-278`; `config.py:274,277-279` | 메모리 + `{ts,rows}` JSON. TTL은 `NEXTGEN_FICC_CACHE_TTL`(기본 21600초, import 때 한 번 읽음). 마지막 행이 기록일(UTC) 이후면 10분만(:224-230,261). TTL이 지나면 None. 실패해도 오래된 캐시를 쓰지 않는다 |
| 곡선 조립 | `data.py:_treasury_from_fred:571-596` | 6개 이상이고 2y·10y가 있어야 한다(:574-576). 날짜 합집합(:577). **퍼센트÷100**(:582). 열마다 forward-fill(:583-587). NaN 있는 행 제거, 마지막 504행(:588-589). note는 "Missing tenors"뿐(:592-594) |
| 최신 행 | `data.py:CurvePanel.latest:142-143` | 마지막 행. `date`는 합집합의 최신일 |
| 합성 | `data.py:synthetic_curve_panel:361-377`, `_business_dates:288-295` | seed `_seed("UST_PANEL")` 고정, NS 랜덤워크. 날짜는 `date.today()`에서 거꾸로 센 평일 |
| 부트스트랩 | `core/ficc/curves.py:bootstrap_par_curve:165-201` | t<1: z=ln(1+y·t)/t. t≥1: brentq로 1=y/2·ΣDF(t_i)+DF(T)을 푼다. 구간 [−0.2,1.0] |
| 보간 | `curves.py:YieldCurve._log_df:77-85` | `np.interp(t, ts, ts*zs)`. t<t₁이면 z₁·t, t>t_K이면 z_K·t |
| 곡선 의존 계산 | `core/ficc/bonds.py:z_spread:108-115`, `key_rate_dv01:144-157`, `carry_roll:169-208`(funding `curve.zero(h)` :191), `shocked_curve:288-296`, `scenario_pnl:299-320` | |
| 표시 | `ui/bonds_page.py:120-139,140,141-154,166-177,214-215` | 합성일 때만 배너(:122-124). 칩(:126-127). 카드. 해설(`insights.narrate_bond`, `core/ficc/insights.py:105-139`, 출처 문장 없음). 페이로드. 차트 제목(`ui/fcharts.py:144,164`) |

### ④ 수식 및 독립 계산

공식(코드와 독립 구현 공통):
- 단위: y = v_FRED/100 (`data.py:582`).
- 1y 미만: DF(t)=1/(1+y·t). t는 1/12, 0.25, 0.5 (ACT/365F 단순 연분수).
- 1y 이상: 1 = (y/2)·Σ_{k=0}^{n−1} DF(T−k/2) + DF(T), n=⌈2T⌉.
- 보간: ln DF(t) = −L(t). L은 (t_k, z_k·t_k)를 잇는 선형 함수다. 양 끝 밖에서는 −z₁t, −z_K t.
- z-spread: P = Σ cf_i·DF(t_i)·e^{−z t_i}. Carry(h=0.25) = c·100·h − zero(h)·P·h.
- 시나리오: 충격 곡선은 z'_k = z_k + s(t_k)·1bp이고, **곡선의 knot t_k에서만** 정의된다(`bonds.py:293-295`).

독립 부트스트랩 비교(`e03_bootstrap.py`, 동시 Newton과 저장소의 순차 brentq):

| 곡선 | knot | Newton 반복 | max\|Δzero\| | max\|ΔDF\| (0~40y, 0.05 간격) | 저장소 zero의 par 잔차(내 DF로) |
|---|---|---|---|---|---|
| 캔드 FRED 최신 행 | 11 | 4 | 8.3e-16 | 5.1e-15 | 6.6e-15 |
| 합성 최신 행 | 11 | 4 | 4.7e-16 | 6.1e-16 | 6.7e-16 |
| 부분 6개(1y~10y) | 6 | 3 | 5.6e-17 | 2.2e-16 | 1.1e-16 |
| 꺾인 테스트 곡선 | 11 | 4 | 2.1e-15 | 1.4e-14 | 1.5e-14 |

끝단 평탄 연장 확인: 부분 곡선에서 zero(0.25) = 3.567984% = zero(1y knot)이고, zero(30) = 4.059899% = zero(10y)다.

캔드 곡선 기록(만기별 값, 단위, DF; 시장 값 아님):

| id | t | par % | par 소수 | zero % (연속) | DF |
|---|---|---|---|---|---|
| DGS1MO | 0.0833 | 4.05 | 0.0405 | 4.0432 | 0.996636 |
| DGS3MO | 0.25 | 3.95 | 0.0395 | 3.9306 | 0.990222 |
| DGS6MO | 0.5 | 3.80 | 0.0380 | 3.7644 | 0.981354 |
| DGS1 | 1 | 3.60 | 0.0360 | 3.5662 | 0.964966 |
| DGS2 | 2 | 3.50 | 0.0350 | 3.4671 | 0.933007 |
| DGS3 | 3 | 3.52 | 0.0352 | 3.4884 | 0.900639 |
| DGS5 | 5 | 3.65 | 0.0365 | 3.6237 | 0.834280 |
| DGS7 | 7 | 3.85 | 0.0385 | 3.8388 | 0.764361 |
| DGS10 | 10 | 4.05 | 0.0405 | 4.0597 | 0.666331 |
| DGS20 | 20 | 4.60 | 0.0460 | 4.7393 | 0.387573 |
| DGS30 | 30 | 4.62 | 0.0462 | 4.7103 | 0.243390 |

`panel.latest()` 독립 확인: 스텁 행을 내 코드로 forward-fill하고 ÷100 해서 비교했다. 날짜가 같고 최대 차이는 6.9e-18이다(A, D 세 경우, F 소수 단위). 합성 최신 par는 9.586%(1m)부터 7.171%(30y)까지인 역전 곡선이다.

곡선 의존 카드: 독립 계산(내 DF) / 저장소, 캔드 곡선, 쿠폰 4.5%, 수익률 4.5%:

| 만기 | 가격 | z-spread (bp) | Carry 3m | +100bp P&L | −100bp P&L |
|---|---|---|---|---|---|
| 10y | 100.000000 / 100.000000 | +44.6063 / +44.6063 | +0.142344 / +0.142344 | −77,762.69 / −77,762.69 | +85,300.06 / +85,300.06 |
| 30y | 100.000000 / 100.000000 | −12.1629 / −12.1629 | +0.142344 / +0.142344 | −146,365.51 / −146,365.51 | +184,725.78 / +184,725.78 |

보간 민감도(같은 par 입력, 정보용): log-linear DF와 linear-in-zero의 z-spread 차이는 7.5y −1.040bp, 10y −0.021, 15y **−8.088**, 25y +0.256, 30y +0.047bp다.

출처별 화면 값(`e04`, 수정 전, 쿠폰 4.5%, 수익률 4.5%):

| T | 곡선 | 칩 | z | Carry | Roll | KRD 합 | +100bp | bear steep. | bull flat. | fly |
|---|---|---|---|---|---|---|---|---|---|---|
| 10 | FRED 전체(캔드) | success | +44.6 | +0.142 | +0.085 | 814 | −77,763 | −10,521 | +10,665 | +7,864 |
| 10 | SYNTHETIC | muted | −315.9 | −1.239 | −0.180 | 821 | −78,369 | −10,653 | +10,798 | +8,042 |
| 10 | 1m/3m/6m/20y/30y 없음 | success | +44.6 | **+0.233** | +0.086 | 814 | −77,761 | −10,521 | +10,664 | +7,864 |
| 10 | 10y 마지막 14.05 | success | **−1802.3** | +0.142 | **+5.534** | 659 | −63,336 | −7,081 | +7,164 | +2,441 |
| 30 | FRED 전체(캔드) | success | −12.2 | +0.142 | −0.002 | 1,639 | −146,366 | −59,696 | +67,476 | +1,373 |
| 30 | SYNTHETIC | muted | −243.7 | −1.239 | −0.062 | 1,732 | −154,148 | −64,883 | +73,518 | +1,297 |
| 30 | 20y·30y 없음 | success | **+41.8** | +0.142 | −0.005 | 1,666 | −148,634 | **−22,369** | **+23,157** | **+18,757** |
| 30 | 30y만 오래됨(4.95) | success | **−47.7** | +0.142 | +0.086 | 1,603 | −143,469 | −57,443 | +64,784 | +1,453 |

Price 100.000과 DV01(10y 798, 30y 1,637)은 모든 행에서 같다.

충격 절단(`e06_mechanisms.py`): bear steepener의 zero 이동은 2/10/20/30y에서 전체 곡선이 0/14.286/32.143/50.0bp다. 독립 램프 값과 같다. 20y·30y가 없으면 0/14.286/**14.286/14.286**bp다.

소유자 화면 출처(`e09_owner_screen_source.py`, 모델값−화면값): 쿠폰 5.5%, 수익률 4.5%에서 합성은 +100bp −623, −100bp +712다. 쿠폰 5.5%, 수익률 5.5%에서 합성은 −599/+684/−157/+163/−127/+185/−176이다. 합성 패널은 날짜와 무관하게 같은 값이다(테스트). 그러므로 화면은 합성 곡선이 아니었다.

### ⑤ 수정안 (스크래치 `W/repo_fix`에 적용·검증. 저장소에는 적용하지 않음)

전체 diff: `W/out/e_fix_diff.log`(180줄). 요지:
- `core/ficc/data.py`
  - `_treasury_from_fred` 실패 사유를 사유별로 묶고 첫 줄 160자로 자른다(E-07).
  - 10y par가 (0.1%, 25%) 밖이면 `FICCError`를 낸다(E-03, 단위 오류). 그러면 `auto`는 배너와 함께 합성으로, `fred`는 오류로 간다.
  - note에 다음을 붙인다. "Missing tenors …; beyond the longest served tenor the curve is held flat.", "Carried forward to {newest}: DGS30 last observed 2026-08-14."(E-02), "Stale: the newest observation (…) is N business days old."(`np.busday_count`, 5영업일 초과, E-01), "Check the print: one-day move above 100bp on DGS10 +1000bp."(E-03).
- `core/ficc/bonds.py:shocked_curve`: 충격 만기를 기존 곡선의 보간 zero 값으로 knot에 추가한 뒤 충격을 준다. `key_rate_shifted`와 같은 방식이다(E-09). 11개 만기가 모두 있는 곡선에서는 결과가 기존 공식과 1e-14 안에서 같다.
- `ui/bonds_page.py`
  - SYNTHETIC이 아닌데 note가 있으면 warning 배너 "Curve check: …"를 띄운다(D03-V01, E-01~03).
  - 만기가 마지막 곡선 만기보다 길면 warning 배너를 띄운다.
  - 칩을 `curve FRED, newest obs 2026-10-23` / `curve SYNTHETIC (simulated, dated …)`(error 색) / `bootstrap (log-linear DF), 11 tenors 1m-30y`로 바꾼다(E-04, D03-08).
  - 해설 끝에 출처 문장을 붙인다(D03-03). 페이로드에 `curve.par_yields`를 넣는다(E-06). KRD·시나리오 차트 제목에 출처를 넣는다(E-05).
- `ui/fcharts.py:scenario_chart(rows, subtitle="")`.
- 제안만 하고 구현하지 않은 것: E-08(곡선 실패 시 곡선과 무관한 카드는 표시, 실패 결과를 60초 메모리 캐시). 수정 후에도 남는 위험: 이력 전체가 14% 수준인 10y처럼, 범위 안이고 급변이 없는 값은 통과한다.

수정 전후, 같은 입력: 전체 곡선과 합성에서는 모든 카드·시나리오 숫자가 같고 라벨만 바뀐다. 부분 곡선(20y·30y 없음)의 30y 채권은 bear steepener −22,369 → −61,227, bull flattener +23,157 → +69,254, fly +18,757 → +1,323이 되고 warning 배너 2개가 뜬다. 기준 곡선은 여전히 10y 뒤가 평평하므로 전체 곡선 값(−59,696)과 같지는 않다.

성능(`e08_timing.py`, 스텁, TTL 0, 10회 중앙값): calc 256 → 317ms, scenarios 144 → 194ms, hedge 24 → 24ms. 곡선 로드와 파싱은 15~23ms다. 증가분의 원인(차트 제목 길이·knot 추가)은 분리하지 않았다. 캐시가 따뜻할 때(e02): `load_treasury_curve` 1.6ms, 부트스트랩 4.6ms, `analyze_bond` 3.2ms, `scenario_pnl` 0.9ms.

### ⑥ 테스트 로그

| 실행 | 대상 | 결과 |
|---|---|---|
| `python -B -m core.ficc.data`, `core.ficc.curves`, `core.ficc.bonds`, `ui.bonds_page` (e05) | `W/repo` | 4 PASS |
| `tests/ficc_acceptance.py` 중 `test_data_*` 5, `test_curve_*` 6, `test_bond_*` 9, `test_futures_hedge_arithmetic`, `test_narratives_state_their_numbers` (in-process, e05) | `W/repo` | 22 PASS (합계 26 PASS / 0 FAIL) |
| 같은 26개 | `W/repo_fix` | 26 PASS / 0 FAIL (회귀 없음) |
| 제안 회귀 테스트 10개 (`e07_regression.py`) | `W/repo` | 0 PASS / 10 FAIL (현재 동작을 드러냄, 예상대로) |
| 같은 10개 | `W/repo_fix` | 10 PASS / 0 FAIL |
| e01 페이지 경로 17가지 | `W/repo` | 실행 완료(exit 0). 결과는 ③ 표 |
| e02 캐시, e03 부트스트랩, e04 의존성, e06 메커니즘, e08 시간, e09 소유자 화면 | `W/repo`(e04·e08은 repo_fix도) | 실행 완료 |
| 실제 FRED 호출 | — | **NOT_RUN**: `curl https://fred.stlouisfed.org/...` → `CONNECT tunnel failed, response 403` |
| 실제 Flet 창 렌더링 | — | **NOT_RUN**: stand-in Page만 사용 |
| Deep analysis(Claude API) | — | **NOT_RUN**: 키 없음. 페이로드 내용만 확인 |
| `tests/run_all.py` | — | **NOT_RUN**: 금지(결과 파일을 다시 씀) |

회귀 테스트 이름: `test_e01_stale_fred_curve_is_flagged`, `test_e02_carried_forward_tenor_is_named`, `test_e02_single_newer_tenor_does_not_hide_the_lag`, `test_e03_unit_error_is_refused_and_jump_is_flagged`, `test_e04_chip_names_the_observation_date_and_clean_curve_is_quiet`(정상 곡선에서 배너가 없어야 함), `test_e05_synthetic_is_named_in_narrative_charts_and_chip`, `test_e06_payload_carries_the_par_curve`, `test_e07_failure_note_is_one_line_per_reason`, `test_e09_scenario_shocks_bite_beyond_the_last_served_tenor`, `test_d03v01_missing_tenors_are_shown_on_the_bonds_page`. 날짜는 실행일 기준으로 만든다(FRESH = 직전 영업일, STALE = 80영업일 전). 저장소에 넣을 때는 `tests/ficc_acceptance.py`의 `_no_network()` 방식으로 밀폐한다.

캐시 로그(e02):
- TTL 기본 21600.0이고, `NEXTGEN_FICC_CACHE_TTL=60`이면 60.0이다.
- 차가운 캐시: 호출 1회(11 id, start 2024-08-02), 파일 11개, 26.2ms. 메모리 적중 0회 1.4ms, 디스크 적중 0회 4.2ms.
- TTL 안에서 FRED가 죽으면: `curve: FRED 2026-10-23` success, 호출 0회.
- TTL+1초에 FRED가 죽으면: `auto`는 SYNTHETIC, `fred`는 오류다.
- 마지막 행이 오늘(UTC)인 파일은 11분 뒤 거부되고, 같은 나이라도 10-23 행이면 제공된다.
- id별 혼합: 칩이 `FRED 2026-10-26`이고, 10y 행은 10-23과 10-26이 같다(True).
- TTL 0에서 Run 3회 → 공급자 호출 3회.
- Rates·Bonds·Structuring은 모두 `days=504`라 캐시 키를 공유한다(코드로 확인됨).

### ⑦ 남은 리스크와 미확인

- 미확인: 실제 FRED 응답의 형식, 지연, 만기별 동시 갱신 여부. 프록시 403으로 호출하지 못했다.
- 미확인: 1y 미만 단리 DF(t=1/12…)와 1y 이상 반기 par 해석이 Treasury CMT 방법론과 얼마나 맞는지. 공식 문서를 열지 못했다. 실시장 z-spread·carry 정확성도 미확인이다. "검증 완료"라고 할 근거가 없다.
- 미확인: 소유자 화면이 실제 FRED였는지. 합성이 아니었다는 것만 테스트로 확인됐다.
- 미확인: E-02·E-03 상황이 실제로 얼마나 자주 생기는지. 위 결과는 스텁으로 강제한 것이다.
- 남은 위험: 수정 후에도 이력 전체가 그럴듯하게 틀린 값은 통과한다. 수신 시각 표시는 C01-05·D04-02 수정이 필요하다. 합성 곡선 수준(1m 9.6%, 10y 7.8%)은 현실과 멀지만 배너로 표시된다.
- 성능 증가 50~60ms의 원인은 분리하지 않았다.

### 9. 스크립트·산출물 경로

`W` = `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/E_curve_source`

스크립트:
- `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/E_curve_source/scripts/ecommon.py`
- `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/E_curve_source/scripts/e01_page_paths.py`
- `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/E_curve_source/scripts/e02_cache.py`
- `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/E_curve_source/scripts/e03_bootstrap.py`
- `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/E_curve_source/scripts/e04_curve_dependence.py`
- `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/E_curve_source/scripts/e05_run_tests.py`
- `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/E_curve_source/scripts/e06_mechanisms.py`
- `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/E_curve_source/scripts/e07_regression.py`
- `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/E_curve_source/scripts/e08_timing.py`
- `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/E_curve_source/scripts/e09_owner_screen_source.py`

산출물(`/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/E_curve_source/out/`):
- `e01_page_paths.json` / `.log`, `e02_cache.json` / `.log`, `e03_bootstrap.json` / `.log`
- `e04_curve_dependence_repo.json`, `e04_curve_dependence_repo_fix.json` (+ `.log`)
- `e05_tests_repo.json`, `e05_tests_repo_fix.json` (+ `.log`)
- `e06_mechanisms.log`
- `e07_regression_repo.json`, `e07_regression_repo_fix.json` (+ `.log`)
- `e08_timing.log`, `e09_owner_screen_source.log`, `e_fix_diff.log`
- `png/` (차트 219개, 예: `png/S_synthetic_calc_1.png`)

스크래치 사본: `W/repo`(HEAD), `W/repo_fix`(수정안 적용).

### 독립 검증

검증 위치: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/verify_E_curve_source/` (아래 `V/`). 내 사본은 `V/repo`(HEAD 8159532)다. 조사자의 수정 사본(`E_curve_source/repo_fix`)은 `V/repo_fix`로 복사해 썼다. 이 사본은 HEAD와 비교해 4개 파일(`core/ficc/data.py`, `core/ficc/bonds.py`, `ui/bonds_page.py`, `ui/fcharts.py`)만 다르다(`diff -rq`로 확인). 추적 파일은 고치지 않았다(`git status --short` 0줄). 모든 실행은 소켓을 막은 상태에서 했다. `.env`는 열지 않았다.

**독립 재계산.** `V/vmath.py`는 순수 Python 이분법 구현이다. 저장소도 조사자 코드도 import하지 않는다. 조사자가 제시한 숫자를 모두 다시 계산했고, 모두 일치했다(`V/out/v01_independent.json`).
- zero 11개(4자리)와 DF 11개(6자리). 예: 10y 4.0597%, DF 0.666331.
- 10y z +44.6063bp, 30y z −12.1629bp, Carry 0.142344.
- ±100bp P&L: 10y −77,762.69 / +85,300.06, 30y −146,365.51 / +184,725.78. 30y bear steepener −59,695.70.
- 부분 곡선 30y: z +41.76bp, bear steepener −22,369.24. 수정안 적용 시 −61,226.68 / +69,254.07 / +1,322.75.
- D03-V01: Carry 0.23300, 3m zero 3.56798%.
- 10y 오타: z −1802.33bp. 소수 단위: z +441.01bp, Carry 1.11513.
- 30y 지연: z −47.74bp, +100bp −143,469.05.
- 보간 민감도: −1.040 / −0.021 / −8.088 / +0.256 / +0.047bp.

**화면 재현.** `V/v02_page_cases.py`로 실제 `build_bonds_page`를 실행했다. 경우 11개 × `auto`/`fred` × 10y/30y × calc/scenarios를 돌렸고, 결과는 `V/out/v02_page_cases.json`에 있다. 칩, 배너, 카드 값과 공급자 호출 수가 조사자 표와 같았다.

| id | 유지 여부 | 정정 심각도 | 정정 상태 | 근거 |
|---|---|---|---|---|
| E-01 | 유지 | P2 | 테스트로 확인됨 | 내 스텁(11개 id 모두 2026-06-30에 끝남)에서 칩이 `curve: FRED 2026-06-30` success다. 배너는 없고 z는 +44.6bp, payload `curve.note`는 `''`다. 날짜가 칩에 보이고, 원인은 FRED 자체의 갱신 중단뿐이다(만료 캐시는 쓰이지 않는다). 그래서 P2다. 회귀 테스트는 HEAD에서 FAIL, 수정안에서 PASS다 |
| E-02 | 유지(재현 조건 보강) | P2 | 테스트로 확인됨 | DGS30을 08-14 값 4.95로 두면 30y z −47.7bp, 칩은 10-23이다. DGS1MO만 10-26 행이 있으면 칩이 10-26이 된다. 정상 사용에서도 생긴다. Macro 화면과 캐시 키를 공유하기 때문이다(E-V01). 수정안은 경고만 붙이고 지연된 값을 그대로 쓴다(v05: 10y 4.05%, 경고 표시) |
| E-03 | 유지 | P2 | 테스트로 확인됨 | 오타 경우를 화면에서 재현했다: z −1802.3bp, Roll +5.534, Breakeven +71.1bp. 소수 단위는 z +441.0bp, Carry +1.115다. 40.5 경우는 내 부트스트랩도 구간을 잡지 못한다. 7y까지의 쿠폰 PV만으로 액면을 넘기 때문이다. 즉 오류 자체는 맞고, 빠진 것은 출처 표시와 `auto` 대체다 |
| E-09 | 유지 | P2 | 테스트로 확인됨 | 2/10/20/30y 충격이 독립 계산으로 0/14.286/32.143/50.0bp(전체 곡선), 0/14.286/14.286/14.286bp(부분 곡선)다. 회귀 테스트는 HEAD에서 14.2857로 FAIL, 수정안에서 PASS다. 전체 곡선에서는 수정 전후가 같다(KEY_TENORS ⊂ UST_TENORS) |
| E-04 | 유지 | P3 | 테스트로 확인됨 | `date.today`를 2026-10-27, 11-03, 2027-03-15로 바꿔 봤다. 칩 날짜는 따라 바뀌었고 par는 그대로였다(10y 7.84145%, 1m 9.58586%). 세션 칩 숫자는 이력 길이에 따라 498과 504를 오간다. 계산에는 마지막 행 하나만 쓰인다(`bonds_page.py:111`) |
| E-05 | 유지 | P3 | 테스트로 확인됨 | 합성 실행에서 차트 제목은 `'Key-rate DV01, z-spread -315.9bp held'`와 `'Scenario P&L — full revaluation, z-spread held'`다. 해설에 SYNTHETIC이나 simulated가 없다(모든 합성 경우) |
| E-06 | 유지 | P3 | 테스트로 확인됨 | payload `curve`의 키는 source/date/method/note 네 개뿐이다(`bonds_page.py:145-146`). 15y −8.088bp를 독립 계산으로 재현했다 |
| E-07 | 유지(수치는 환경 의존) | P3 | 테스트로 확인됨 | 실제 `_fred_fetch`(pdr 0.11.1)로 돌렸다. 배너는 4,807자이고 RemoteDataError가 11번 나온다. 프록시 호스트는 배너와 payload에 있다(True). userinfo는 없다(False). 조사자의 4,961자와의 차이는 하네스의 소켓 차단 문구 길이(14자 × 11)다. 프록시 노출은 프록시가 설정된 환경에서만 생긴다 |
| E-08 | 유지(영향 과소평가) | P3 | 테스트로 확인됨 | `fred`에서 hedge 도구도 오류 배너만 남는다. 배치가 예외를 내면 Run마다 12회 호출한다. 배치가 빈 dict를 돌려주면 1회다(조사자의 "E DGS2 없음 → 12"는 스텁에 따라 달라진다). 네트워크가 멈춘 경우 "약 5초"가 아니라 1,446.6초다. 이것은 원인이 달라 E-V03으로 따로 올린다. 제안한 60초 음성 캐시로는 첫 Run의 24분을 막지 못한다 |

**회귀 테스트와 수정안 점검.**
- `e07_regression.py` 10개를 내 사본에서 다시 돌렸다. HEAD는 0 PASS / 10 FAIL, `repo_fix`는 10 PASS / 0 FAIL이다(`V/rt/`).
- 범위를 넓혀 `tests/ficc_acceptance.py` 57개 전부와 모듈 자체검사 8개를 돌렸다. 자체검사 대상은 `data`, `curves`, `bonds`, `bonds_page`, `rates_page`, `structuring_page`, `ratesim`, `fcharts`다. HEAD와 `repo_fix` 모두 65 PASS / 0 FAIL이다(`V/out/v03_tests_*.json`).
- 수정안은 올바르고 대체로 최소다. 단, E-02 수정은 표시만 하고 재조회는 하지 않는다(E-V01 참조).
- 조사자의 성능 주장 "수정 후 50~60ms 증가"는 재현되지 않았다. 7회 중앙값으로 HEAD calc 235~241ms와 fix 228~265ms, scenarios 159~164ms와 164~172ms다. 잡음 범위 안이다.

**요약 문장 정정.** "소유자 화면은 합성 곡선이 아니었다(테스트로 확인됨)"는 범위가 너무 넓다.
- 테스트로 확인된 것: HEAD의 합성 곡선은 소유자 숫자를 재현하지 못한다. 차이는 +100bp −622.9, −100bp +712.3, 5.5%/5.5%에서 −598.7 / +683.9 / −156.7 / +163.0 / −127.2 / +184.6 / −176.0이다. 저장소 함수와 vmath가 같은 값을 냈다.
- 이 저장소의 코드 이력은 2026-10-23 기준선 커밋 하나뿐이다("before the TRADEGEN split"). 소유자가 실행한 코드 버전은 알 수 없다. 그래서 "합성이 아니었다"는 결론은 **미확인(조건부)**이다.
- 참고: 캔드 곡선(상승형, 약 4%)은 소유자 숫자에 가깝다. +100bp −81,498(화면 −81,597), 5.5%/5.5%에서 −74,564(−74,657), bear steepener −9,866(−9,888)이다. 시장과 비슷한 곡선이라는 정황일 뿐 증거는 아니다.

### 조사자가 놓친 발견

#### E-V01 [P2, 테스트로 확인됨] Macro 화면과 Bonds 곡선이 FRED 캐시 키를 공유해, 평소 사용에서도 날짜가 섞인 곡선이 녹색 칩으로 나온다
- 위치: `core/ficc/macro.py:62-64,150-152,202`의 `macro_sheet(days=504)`가 `load_many([... "DGS2","DGS10","DGS30" ...], days=504)`를 부른다. 그러면 `core/ficc/data.py:220-221`의 `_cache_key`로 `FRED_DGS2_504`, `FRED_DGS10_504`, `FRED_DGS30_504`가 생긴다. `_treasury_from_fred:571-589`(`_provider_rows` 캐시 우선 + 합집합 forward-fill)가 이 파일을 그대로 읽는다.
- 재현(`V/v05_shared_cache.py`, TTL 21600, 오프라인 스텁):
  1. FRED 최신일이 10-22일 때 Macro 방식으로 3개 id를 읽는다.
  2. FRED가 10-23 행을 내놓는다(2y +6bp, 10y +8bp, 30y +7bp).
  3. Bonds를 실행한다. 공급자 호출은 1회이고, 나머지 8개 id만 받는다.
  4. 칩은 `curve: FRED 2026-10-23` success이고 배너는 없다. 그런데 2y·10y·30y는 10-22 값이다(10y 4.05%, 정답 4.13%).
  5. 4.5% 10y 채권의 z는 화면 +44.6bp다. 모든 만기를 10-23으로 맞추면 +36.8bp다(vmath).
- 기대 결과: 한 날짜로 맞춘 곡선을 쓰거나, 늦은 만기를 다시 받는다.
- 영향: Macro를 연 뒤 6시간 안에 Bonds·Rates·Structuring을 쓰고, 그 사이 FRED가 갱신되면 곡선 의존 숫자가 틀린다. 차이는 보통 1영업일, 수 bp다. E-02와 같은 부류이고, 실제로 일어날 수 있는 경로다.
- 수정(`V/out/m1_fix2_diff.log`, `repo_fix` 위에 적용): `_treasury_from_fred` 앞부분에서 마지막 날짜가 newest보다 이른 id를 캐시 없이 한 번 다시 받는다. 그래도 늦으면 E-02의 note를 남긴다.
- 회귀 테스트 `V/v07_regression_m1.py::test_m1_macro_cache_does_not_age_the_bonds_curve`:
  - HEAD는 FAIL(10y 0.0405).
  - 조사자 `repo_fix`도 FAIL(경고만 하고 0.0405).
  - `repo_fix2`는 PASS. 같은 사본에서 65/65와 e07 10/10이 통과했다.

#### E-V02 [P3, 테스트로 확인됨] 합성 "오늘" 곡선이 문서의 "level ~4%"와 달리 9.6% 역전 곡선이다
- 위치: `core/ficc/data.py:361-377` `synthetic_curve_panel`. docstring(:362-363)은 "level ~4%"라고 쓴다. 그런데 503걸음 랜덤워크의 **마지막** 행을 화면이 쓴다.
- 독립 재유도 결과(seed 4143046924):
  - 첫 행은 2.541%(1m)에서 3.933%(30y)까지다.
  - 마지막 행은 9.586% / 10y 7.841% / 30y 7.171%다.
  - b0는 0.0400에서 0.0682로, b1은 −0.0150에서 +0.0277로 움직였다.
- 그래서 오프라인이거나 `auto`가 대체된 모든 Bonds 실행에서 4.5% 액면 채권이 z −315.9bp, Carry −1.239로 나온다. 배너가 있으므로 P3다.
- 수정(`V/out/m2_diff.log`): 워크를 뒤집는 한 줄(`b0, b1, b2 = b0[::-1], b1[::-1], b2[::-1]`)을 넣는다. 결정성은 유지되고, 최신 행이 기준 수준이 된다. 수정 후 z +69.4bp, Carry +0.472다.
- 회귀 테스트 `V/v08_regression_m2.py`: HEAD는 FAIL(10y 0.0784), 수정본은 PASS. FICC 65/65가 통과했다. 합성 숫자를 고정해 둔 다른 스위트(`tests/run_all.py`)는 금지 규칙 때문에 NOT_RUN이다.

#### E-V03 [P2, 테스트로 확인됨] 네트워크가 멈추면 `auto` Run 한 번이 24분 걸린다
- 원인:
  - `core/ficc/data.py:167`의 `_pdr.DataReader(ids, "fred", start)`는 timeout 인자가 없다. 그래서 pandas_datareader 0.11.1 기본값(timeout=30, retry_count=3, 즉 4회 시도)을 쓴다. `config.HTTP_TIMEOUT_SECONDS`(12초, `config.py:145`)를 무시한다.
  - 일괄 실패 뒤에는 `_provider_rows:474-484`가 11개 id를 하나씩 다시 시도한다.
- 재현(`V/v09_blackhole.py`): 로컬 black-hole 프록시를 쓰고, 다른 연결은 모두 차단했다.
  - id 하나: 120.5초, 연결 4회.
  - 전체 `auto` Run(HEAD): **1,446.6초**, 연결 48회(12 fetch × 4).
  - 이 실행의 칩은 캡처하지 못했다. walk 수정 전에 시작한 프로세스였기 때문이다. 최종 합성 대체는 코드로 확인됨(`data.py:564-568`).
- 영향: 기본 출처 `auto`인 Bonds·Rates·Structuring이 침묵 드롭 방화벽, 응답 없는 프록시, 캡티브 포털에서 Run마다 약 24분 멈춘다. 화면이 죽지는 않고 결국 합성 결과를 표시하므로 P2다. P01 보고서는 순차 호출만 다뤘고 timeout 예산은 다루지 않았다.
- 수정(`V/out/m3_diff.log`): `FredReader(ids, start=start, retry_count=0, timeout=config.HTTP_TIMEOUT_SECONDS).read()`를 쓴다. 일괄 호출이 timeout까지 걸려 실패했다면 id별 재시도를 하지 않는다. 빨리 실패한 경우(폐지된 id 등)에는 재시도를 유지한다.
  - 수정 후 id 하나 12.1초, 전체 Run 12.4초이고, 칩은 `curve: SYNTHETIC 2026-10-27`이다.
  - 주의: 시간 기준 생략은 yfinance 일괄 호출에도 적용된다.
- 회귀 테스트 `V/v10_regression_m3.py`(3개): HEAD는 1 PASS / 2 FAIL(멈춘 배치를 12회 시도, pdr 경로에 timeout 없음). 수정본은 3 PASS. FICC 65/65가 통과했다.

### 실행 로그 요약
| 실행 | 결과 |
|---|---|
| v01 독립 재계산(vmath, 저장소 import 없음) | 조사자 수치 전부 일치 |
| v02 화면 경우 89회 실행 | 칩·배너·카드가 조사자 표와 일치(호출 수 차이는 스텁 설계 때문) |
| v03 FICC 57 + 자체검사 8 | repo 65/0, repo_fix 65/0, repo_fix2 65/0, repo_m2 65/0, repo_m3 65/0 |
| e07 조사자 회귀 10개 | repo 0/10, repo_fix 10/0, repo_fix2 10/0 |
| v07/v08/v10 신규 회귀 | 모두 HEAD에서 FAIL, 수정본에서 PASS |
| v09 멈춘 네트워크 | HEAD 1,446.6초, 수정본 12.4초 |
| 실제 FRED, 실제 Flet 창, Claude API, `tests/run_all.py` | NOT_RUN(프록시 403, stand-in Page만 사용, 키 없음, 금지) |
