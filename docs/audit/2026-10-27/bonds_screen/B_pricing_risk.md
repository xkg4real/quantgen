# Bonds 화면 검증 B. 채권 가격과 위험 지표

> 작성 메모 (오케스트레이터): 하네스가 하위 에이전트의 보고서 파일 쓰기를 막아, 조사 에이전트가 반환한 본문과 독립 검증자가 반환한 검증 절을 내용 변경 없이 옮겼습니다. 저장소 코드는 바꾸지 않았습니다.

## B_pricing_risk: 가격·YTM·위험 지표 독립 검증 (요청서 3.B, 2.1, 수용 기준 '액면가 기준'·'가격 역산'·'위험 지표')

### ① 요약
- 표 2.1의 다섯 행은 원인이 확인된 값이다. 독립 구현(Decimal 60자리, 저장소 import 없음)과 저장소 함수가 1e-9보다 훨씬 작게 일치한다. 최대 차이는 3.2e-12이고, 이 값은 DV01(통화 단위)에서 나왔다. 화면 문자열 30개(5행 × 6항목)도 UI 서식 그대로 모두 재현된다.
- 가격 95와 105에서 역산한 YTM은 6.1776904062%와 4.8626816895%다. 저장소 brentq, Newton(해석 미분), numpy.roots, 이분법의 차이는 ≤8.5e-16이다.
- 쿠폰일 결제(정수 기간)에서는 par/premium/discount 규칙이 200건 모두 성립한다. 액면가 오차는 최대 1.05e-12다. 소수 만기(예: 7.3y)에서는 성립하지 않는다. 화면 Price가 dirty(전체 PV)이기 때문이다. 이 원인은 기존 FC-03이다(새 발견 아님). 쿠폰 5.5%, 7.3y, YTM 5.5%에서 화면 가격은 101.091이다. Price 100을 넣으면 YTM 5.685%가 나온다.
- 빈도 1/2/4/12 × 쿠폰 0~12% × 만기 0.1~30y × 수익률 −1~60%의 640건에서 가격·Mac·Mod·Cvx·DV01의 상대오차는 ≤2.9e-14다. 무이표채는 닫힌식과 1.1e-13까지 일치한다.
- 곡선 쪽 결과: z-spread는 ≤2.4e-15로 일치한다. KRD는 해석 미분과 상대 8e-7(중심차분 오차 수준)로 일치한다. KRD 합은 평행 zero DV01과 같다(삼각 bump의 단위분할은 정확히 성립, ≤1e-60). carry와 roll-down은 1.6e-12까지 일치하지만, 아래 B-01 경우는 예외다.
- 새 발견은 6건이다: P2 1건(B-01), P3 5건. P0·P1은 없다.
  - **B-01 (P2)**: 만기 ≤ 3개월이고 쿠폰 스텁이 있는 채권에서 roll-down, carry+roll, breakeven이 틀린다. 화면 예: 5.5% 0.25y 반기 채권의 Breakeven이 −1062.6bp로 나온다. 정답은 −509.2bp다. 기울기 곡선에서는 부호가 뒤집힌다(−423bp, 정답 +130bp).
- 실시장 정확성은 검증하지 않았다. QuantLib이 설치되어 있지 않다. 실제 FRED 곡선도 쓰지 않았다(NOT_RUN). 여기서 확인한 것은 공식과 관례의 내부 정확성뿐이다.

### 범위와 방법
- 대상 코드: `core/ficc/bonds.py`, `core/ficc/curves.py`(coupon_times, YieldCurve, key_rate_shifted), `ui/bonds_page.py`, `ui/fcharts.py`(price_yield_chart, krd_chart), `core/ficc/insights.py`(narrate_bond).
- 저장소 파일은 하나도 바꾸지 않았다. 마지막에 `git status --short`가 0줄이었고, 저장소에 새 `__pycache__`도 생기지 않았다.
- 모든 저장소 코드는 `git archive HEAD`로 만든 사본에서 `python3 -B`로 실행했다. 이 사본은 작업 트리와 코드가 같다(`diff -rq core ui`에서 pycache만 다름). 사본에는 `.env`가 없다.
- 독립 구현 `indep.py`의 구성:
  - 가격·위험: 교과서 공식, Decimal 60자리.
  - YTM: Newton(해석 미분) + 이분법 + numpy.roots(정수 기간 다항식). 저장소의 brentq와 다른 방법이다.
  - 곡선: z·t 선형 보간, 양끝 평탄 zero를 직접 구현.
  - z-spread: Newton.
  - KRD: 해석 미분.
- 같은 입력을 저장소 함수에도 넣고 비교했다.
- 기존 보고서와 겹치는 것은 ID로만 인용한다. financial_calcs.md 표 8~11행(QuantLib 대조)과 FC-03(dirty 가격)이다.

### 코드 추적표
| 단계 | 파일:함수:라인 | 내용 |
|---|---|---|
| 입력 | `ui/bonds_page.py:_num:38-49` | 빈칸이면 기본값, 숫자가 아니거나 유한하지 않으면 ValueError(필드명 포함) |
| Bond | `ui/bonds_page.py:worker:107-108` → `core/ficc/bonds.py:Bond.__post_init__:48-57` | coupon %/100, maturity(연), freq=int(dropdown 1/2/4), notional |
| 곡선 | `ui/bonds_page.py:110-111` → `core/ficc/data.py:load_treasury_curve:552-568` → `core/ficc/curves.py:curve_from_snapshot:262-266` → `bootstrap_par_curve:165-201` | UI는 항상 곡선을 넘긴다(FLAT@YTM 경로는 UI에서 쓰지 않음) |
| 분석 | `ui/bonds_page.py:112-113` → `bonds.py:analyze_bond:231-254` | price와 ytm 중 하나만 받음(236-237) |
| 현금흐름 | `bonds.py:cashflows:67-72`, `curves.py:coupon_times:41-48` | t_i = T − k/f, t_i > 0, 쿠폰 c·face/f, 마지막에 face |
| 가격·YTM | `bonds.py:_pv_terms:80-84`, `price_from_yield:87-89`, `yield_from_price:92-99`(brentq [−0.5, 2.0]) | 이산복리 (1+y/f)^(−t·f), 분수 지수 |
| 위험 | `macaulay_duration:121-123`, `modified_duration:126-127`, `convexity:130-134`, `dv01:137-141` | DV01 = Mod·P/face·N·1bp |
| 곡선 기반 | `price_from_curve:102-105`, `z_spread:108-115`, `key_rate_dv01:144-157`(`curves.py:key_rate_shifted:125-141`), `carry_roll:169-208` | 연속복리 zero, z는 연속 스프레드 |
| 표시 | `ui/bonds_page.py:131-139`(카드), `156-165`(carry), `166-168`(차트) → `ui/fcharts.py:price_yield_chart:168-187`, `krd_chart:133-145`; `core/ficc/insights.py:narrate_bond:105-139` | 서식: Price .3f, Yield .3f%, Mac .2f, Mod .2f, Cvx .1f, DV01 ,.0f |

### ④ 수식 및 독립 계산

#### 공식·단위·관례 (코드로 확인됨, 테스트로 확인됨)
| 항목 | 코드 공식 | 단위 | 관례·가정 | 독립 대조 |
|---|---|---|---|---|
| 가격 | P = Σ cf_i (1+y/f)^(−t_i f) | face 100당 | YTM 복리 주기 = 쿠폰 빈도 f; 쿠폰 = c·100/f; 분수 지수; 결제일·경과이자 없음, 즉 전체 PV(dirty) | Decimal 합 |
| Macaulay | Σ t_i PV_i / P | 년 | t는 ACT/365F 연 | Decimal, 수치미분 −P'(1+y/f)/P |
| Modified | Mac/(1+y/f) | 년(= 수익률 1.00당 가격 변화율) | 이산 수익률 기준 | Decimal |
| Convexity | Σ t_i(t_i+1/f)PV_i/((1+y/f)²P) | 년² (P''/P; /100 관례 아님) | — | Σ cf n(n+1)/f² v^(n+2)/P(n=t·f), 수치 2차미분 |
| DV01 | Mod·P/100·N·1e-4 | 통화/bp, long이면 양수 | 1차(해석) 미분 | Decimal; 중심차분 ±1bp |
| YTM 역산 | brentq [−50%, 200%], xtol 1e-14 | 소수 | — | Newton, 이분법, numpy.roots |
| z-spread | Σ cf DF(t)e^(−zt) = P | 연속복리 | 곡선 DF × e^(−zt) | Newton(Decimal) |
| KRD | (P(−1bp)−P(+1bp))/2·N/100, 삼각 zero bump, z 고정 | 통화/bp | 연속 zero 이동 | 해석 미분 Σ cf DF e^(−st)·Δ(zt)_k(t) |
| carry | c·100·h − z(h)·P·h | 100당, 3m, 연율 아님 | z(h)를 단리처럼 사용(B-05) | 같은 공식 + DF 단리 버전 |
| roll-down | (Σ_{t>h} cf DF(t−h)e^(−z(t−h)) + 받은 쿠폰 − c·100·h) − P | 100당 | 곡선 불변, z 고정 | 독립 시평(horizon) 가치 |
| breakeven | total/(Mod·P)/1bp | bp(수익률) | 1차 근사, 오늘의 Mod | 같은 식(독립 Mod) |

#### 표 2.1 재현 (테스트로 확인됨, `t1_table21.py`)
각 행의 첫 값들은 독립 구현의 결과이고, 저장소 차이는 max|repo−독립|이다.

| 입력 | 가격 | YTM | Macaulay | Modified | Convexity | DV01(1e6) | 저장소 차이 | 화면 일치 |
|---|---|---|---|---|---|---|---|---|
| 5.5%, 10y, y 4.5% | 107.981856184988 | 4.5% | 7.918984491792 | 7.744728109332 | 73.0148182566 | 836.29011689 | 3.4e-13 | 6/6 |
| 4.5%, 10y, y 5.5% | 92.386373933112 | 5.5% | 8.072030429249 | 7.855990685401 | 74.3897908015 | 725.78649308 | 1.1e-12 | 6/6 |
| 5.5%, 10y, y 5.5% | 100.000000000000 | 5.5% | 7.823000783727 | 7.613626066888 | 71.1522272246 | 761.36260669 | 1.1e-12 | 6/6 |
| 5.5%, 10y, P 95 | 95 | 6.1776904062% | 7.756344948252 | 7.523942025901 | 69.8915699924 | 714.77449246 | 3.2e-12 | 6/6 |
| 5.5%, 10y, P 105 | 105 | 4.8626816895% | 7.884503648622 | 7.697354719364 | 72.3390287514 | 808.22224553 | 9.1e-13 | 6/6 |

- YTM 솔버 비교:
  - P 95: brentq−Newton 3.5e-16, numpy.roots−Newton −8.5e-16.
  - P 105: brentq−Newton 9.7e-17, numpy.roots−Newton 3.5e-16.
- 유한차분 대조:
  - Mac−FD는 약 1e-22다.
  - Cvx−FD는 약 7e-16이다.
  - DV01 공식값과 ±1bp 중심차분의 차이는 +1.35e-4다(3차 항). 예: 836.290117 대 836.290252.
  - 실제 +1bp 손실은 835.8960, −1bp 이익은 836.6845다(볼록성 비대칭). 화면 DV01은 이 둘 사이의 해석 미분값이다.
- 표 2.1의 행 1~3에는 "가격 입력 100"이라고 적혀 있다. 그러나 코드상 Price와 Yield가 둘 다 있으면 "Give exactly one of price or ytm."가 나온다(UI 구동으로 확인). 화면 숫자는 Price가 빈칸일 때의 수익률 경로 결과와 정확히 같다. 캡처 당시 필드 상태는 **미확인**이다.

#### 경계 조건 (`t2_edges.py`, 테스트로 확인됨)
| 경우 | 결과 |
|---|---|
| 그리드 640건(f 1/2/4/12, T 0.1~30, c 0~12%, y −1~60%) | 가격 2.9e-14, Mac 6.6e-15, Mod 6.8e-15, Cvx 9.9e-15, DV01 2.9e-14(상대), YTM 왕복 4.7e-15, Newton 대비 3.9e-15 |
| 쿠폰 0 | Mac = T, Mod = T/(1+y/f), Cvx = T(T+1/f)/(1+y/f)²: 최대 1.1e-13. 화면 64.082 / 10.00y / 9.78 / 100.4 / 627 |
| 만기 0, −1 | "maturity must be positive years" 오류(적절) |
| 만기 1e-12, 4e-10 | `IndexError: index -1 is out of bounds` → B-02 |
| 만기 1000y, 2000y | 정상(111.11). 2000y 역산은 overflow 경고만 내고 값은 맞음(5.0505% = c/P) |
| freq 0, 0.5 | 오류. freq 2.9 → 조용히 2로 처리(B-03, UI는 dropdown이라 도달 불가) |
| freq 12, 365 | 정상(코어만). UI는 1/2/4만 제공(`ui/bonds_page.py:31`) |
| 수익률 −200%(f=2) | "yield −2.0 is not usable" 오류. −199%는 1.08e48 |
| 역산 가능한 가격 범위 | 10y 5.5%: [2.7501, 34991]. 6m: [51.375, 137.0]. 범위 밖은 "No yield in [-0.5, 2.0] reproduces price …" |
| 아주 작은 가격 | 0, 음수, NaN → "price must be positive". 1e-6, 0.01, 1.0 → No yield 오류(적절) |
| Yield% 201 입력 | "No yield in [-0.5, 2.0] reproduces price 2.7364."(수익률을 넣었는데 가격 메시지) → B-04 |
| Yield% −40 입력 | "No z-spread in [-0.5, 2.0] reproduces 9852.4898." |
| Yield% 0 | 0을 빈칸으로 다루지 않음. 가격 155.000, DV01 1,289 |

#### 소수 만기와 clean/dirty (`t3_fractional.py`, 테스트로 확인됨, FC-03 재확인)
| 경우 | 첫 현금흐름 t | 화면 가격(dirty) | 경과이자 | clean | clean을 Price에 넣을 때 YTM 오차 |
|---|---|---|---|---|---|
| 7.3y, 5.5%, y 4.5% | 0.3 | 107.256456 | 1.1 | 106.156456 | +17.33bp |
| 7.3y, 5.5%, y 5.5% | 0.3 | 101.091056 | 1.1 | 99.991056 | +18.62bp |
| 7.3y, 4.0%, y 4.5% | 0.3 | 97.712767 | 0.8 | 96.912767 | +13.28bp |

실제 결제 예: 5.5% 반기, 만기 2034-02-15, 거래 2026-10-27, 결제 2026-10-28(T+1), ACT/ACT ICMA, 수익률 4.5%로 독립 계산했다.
- 직전 쿠폰 2026-08-15, 다음 쿠폰 2027-02-15. E = 184일, A = 74일, w = 0.597826.
- street 계산: dirty 107.261644, 경과이자 1.105978, clean 106.155666.
- 저장소 계산(T = 2667/365 = 7.306849): 가격 107.223769.
  - street dirty보다 −0.037875 낮다. 원인은 ACT/365F와 정확히 1/f 간격의 일정이다. 첫 쿠폰을 112일 뒤로 두는데 실제는 110일 뒤다.
  - clean보다는 +1.068103 높다.
- clean 106.155666을 Price에 넣으면 화면 YTM은 4.6681%(+16.81bp)다. 그 수익률로 계산한 DV01은 −1.20% 틀린다.
- street dirty를 넣어도 일정 차이 때문에 −0.59bp가 남는다.
- 화면 Price가 dirty라는 사실과 해결책은 FC-03에 있다. 일정 차이와 미표시 문제는 B-06에 넣었다.

#### 곡선 기반 위험 (`t4_curve_risk.py`, 11 채권 × 4 곡선 = 44 조합, 테스트로 확인됨)
곡선은 네 가지다:
- flat@y: 채권 수익률의 연속 등가 f·ln(1+y/f)인 평탄 곡선.
- sloped: zero 3.0%~5.0% 우상향.
- inverted: zero 5.5%~4.0% 역전.
- ui_synthetic: UI의 synthetic 경로(`synthetic_curve_panel().latest()`를 bootstrap). 저장소 zero knot을 독립 Curve에 그대로 넣었다(bootstrap 자체는 financial_calcs 12행에서 이미 검증됨).

| 항목 | 결과 |
|---|---|
| z-spread 저장소−독립 | 최대 2.4e-15 |
| KRD(키별) 저장소−해석미분 | 상대 최대 8.0e-7. 원인은 ±1bp 중심차분의 (h·t)²/6 오차이고 결함이 아니다 |
| 삼각 bump 단위분할 Σ_k bump_k(t) = t | UST knot ≤1e-60, KEY knot 0 (`t4b_krd_partition.py`) |
| KRD 합 − 해석 평행 zero DV01 | ≤1.65e-3(30y 분기, 통화 단위). 중심차분 오차 수준 |
| KRD 합 / 수익률 DV01 | flat에서 1.0225001 = 1+y/f(문서와 일치). 다른 곡선에서는 0.9938~1.0475. 문서의 "(1+y/f) 배"는 평탄 곡선에서만 정확하다 → B-06 |
| carry 저장소−독립 | ≤3.2e-16(같은 관례). 관례 차이는 B-05 |
| roll-down 저장소−독립 | 스텁 만기 ≤ h가 아닌 경우 ≤1.6e-12. 스텁 0.25y/0.2y/0.1y(f=2)는 정확히 −1.375/−1.650/−2.200 → B-01 |
| breakeven | 같은 경우에 일치. B-01 경우에는 틀림 |

화면 구동 예(synthetic, 5.5%, 10y, y 4.5%):
- 카드: z-spread −317.8bp, Carry (3m) −1.177, Roll-down −0.346, Carry+roll −1.524, Breakeven −18.2bp. 모두 독립값과 같다.
- KRD 차트 제목: "total 860 per bp". 바로 옆 DV01 카드는 836이다(비율 1.0288). 화면에 설명이 없다 → B-06.
- 이 synthetic 곡선은 3m zero가 약 9.45%다(carry 역산). 그래서 z-spread가 −318bp로 크게 나온다. 데이터 출처 문제는 E 차원에 넘긴다.

평탄 곡선 sanity:
- 5.5%, 10y, y 4.5%: carry +0.17367, roll −0.16696(pull-to-par = 일정 수익률 clean 가격 변화와 같음), total +0.00671 ≈ P·(zh)²/2.
- 같은 곡선으로 조달하므로 total이 거의 0이다. 기대와 맞다.

### ② 심각도별 이슈
| ID | 심각도 | 상태 | 위치 | 한 줄 |
|---|---|---|---|---|
| B-01 | P2 | 테스트로 확인됨 | `core/ficc/bonds.py:carry_roll:192-202` | 만기 ≤ 3개월 스텁 채권의 roll/total/breakeven 오류(경과이자 AI0만큼) |
| B-02 | P3 | 테스트로 확인됨 | `core/ficc/curves.py:coupon_times:47`, `bonds.py:cashflows:71` | 만기 ≤ 약 5e-10y에서 IndexError |
| B-03 | P3 | 테스트로 확인됨 | `bonds.py:Bond.__post_init__:53-57` | 정수가 아닌 freq를 조용히 버림(2.9 → 2) |
| B-04 | P3 | 테스트로 확인됨 | `bonds.py:analyze_bond:238-241`, `carry_roll:188` | 수익률 >200% 입력에 가격 관련 오류 문구 |
| B-05 | P3 | 테스트로 확인됨 | `bonds.py:carry_roll:191` | 연속복리 zero를 단리 조달금리로 사용 |
| B-06 | P3 | 코드로 확인됨 | `ui/bonds_page.py:63-82,131-168,226-230`, `ui/fcharts.py:144`, `bonds.py:16-18` | 화면이 관례·단위를 밝히지 않음(DV01 836 대 KRD 합 860 등) |

#### B-01 (P2, 테스트로 확인됨)
- 위치: `core/ficc/bonds.py:carry_roll:192-202`. 특히 `else: clean_aged = bond.face`(201-202).
- 재현:
  - UI: Calculator, Coupon 5.5, Maturity 0.25, Semi-annual, Yield 4.5, Curve synthetic로 Run.
  - 코어: `carry_roll(Bond(0.055, 0.25, 2), flat_curve(2*log1p(0.0225)), price_from_yield(b, 0.045))`.
- 기대: 만기까지 받은 현금 102.75에서 가격 101.613과 조달비용을 뺀 값이 total이다.
  - roll = 100 − clean0 = 100 − (101.613 − 1.375) = −0.238.
  - flat 곡선: total +0.0063, breakeven +2.5bp.
  - synthetic: total −1.265, breakeven −509.2bp.
  - sloped: breakeven +130.4bp.
- 실제:
  - roll −1.613.
  - flat: total −1.369, breakeven −550.9bp.
  - synthetic: 화면 Carry+roll −2.640, Breakeven −1062.6bp. 설명 문구도 "yields must fall 1062.6bp"라고 쓴다.
  - sloped: −423.1bp. 부호가 반대다.
  - 만기 0.25 ± 1e-7에서 total이 −1.051에서 +0.324로 불연속하게 뛴다.
- 원인: 만기가 horizon 안에 있는 분기에서 시평 가치를 face로 둔다. 그런데 가격은 dirty이므로 t=0 이전에 쌓인 경과이자 AI0 = c·100·(1/f − T)를 포함한다. 만기 때 받는 쿠폰 전액은 빠진다. 그래서 roll이 AI0만큼 작아진다.
- 영향:
  - 화면 Roll-down, Carry + roll, Breakeven 카드, Analysis 문구, AI payload의 carry_roll이 틀린다.
  - 조건: 만기 ≤ 0.25y인 모든 연·반기 채권, 그리고 0.25y 미만 분기 채권.
  - 오차 크기(5.5%, 반기, 100당): 0.25y 1.375, 0.2y 1.65, 0.1y 2.2.
  - 가격, YTM, 듀레이션, DV01, KRD, z-spread, 시나리오는 영향받지 않는다.
  - 기본값(10y) 경로에서는 나타나지 않으므로 P2로 분류했다.
- 수정(최소): 아래 diff. 만기 전에 받은 모든 현금흐름을 받은 현금으로 계산한다. 두 분기가 같은 식 `clean_aged = dirty_aged + paid − accrued`를 쓰게 한다. 기존 분기의 죽은 항 `− face if not keep.any()`도 없앤다.
- 회귀 테스트: `t7_regression.py`의 `test_carry_roll_short_stub_inside_horizon`(flat·sloped × T 0.1/0.2/0.25, |total − (Σcf − P − funding)| < 1e-9)과 `test_carry_roll_continuous_at_the_horizon_boundary`. HEAD에서 FAIL, 수정 후 PASS.

#### B-02 (P3, 테스트로 확인됨)
- 재현: Maturity "0.0000000001" → 화면 "IndexError: index -1 is out of bounds for axis 0 with size 0".
- 기대: 가격(약 102.5) 또는 명확한 검증 메시지.
- 원인: T·f < 1e-9이면 n = ceil(T·f − 1e-9) = 0이 되어 일정이 비고, `cf[-1]`에서 터진다.
- 영향: 비현실적 입력뿐이다(0.016초). 일반 예외 경로라 메시지가 불친절하다.
- 수정: `n = max(1, ...)`. T > start이면 만기일 자체는 항상 현금흐름일이다.
- 회귀 테스트: `test_tiny_maturity_prices_instead_of_index_error`. 전체 FICC 57/57은 수정 후에도 PASS.

#### B-03 (P3, 테스트로 확인됨)
- `Bond(0.05, 10, freq=2.9).freq == 2`다. 오류 없이 반기로 계산한다.
- UI dropdown(1/2/4)으로는 도달할 수 없다. 코어 API의 위생 문제다.
- 수정: 정수가 아니면 거부한다.
- 회귀 테스트: `test_non_integer_freq_is_rejected`.

#### B-04 (P3, 테스트로 확인됨)
- Yield % 201을 넣으면 "No yield in [-0.5, 2.0] reproduces price 2.7364."가 나온다.
- 원인: `carry_roll:188`이 가격에서 수익률을 [−50%, 200%] 범위로 다시 푼다.
- 기대: 입력한 수익률이 허용 범위 밖이라는 메시지.
- 수정: `analyze_bond`에서 ytm 범위를 검사하고 수익률 메시지를 낸다.
- 남는 점: −40% 같은 큰 음수 수익률은 z-spread 범위 오류로 남는다.
- 회귀 테스트: `test_yield_outside_range_gets_a_yield_message`.

#### B-05 (P3, 테스트로 확인됨)
- 코드: funding = z(h)·P·h. 연속복리 zero를 단리처럼 쓴다. DF와 일관된 단리 조달 P·(1/DF(h) − 1)보다 약 P(zh)²/2 작다.
- 크기(100당):
  - 3.4~4.5% 곡선: 0.0035~0.0067. breakeven 영향 ≤0.1bp.
  - 현재 synthetic 곡선(z(3m) 9.45%): 0.0304. carry −1.1773 → −1.2077, breakeven −18.22 → −18.58bp.
- 수정: `funding = price*(1/DF(h) − 1)`. 자체 검사 377행도 같이 바꾼다.
- 회귀 테스트: `test_funding_uses_simple_rate_from_df`.

#### B-06 (P3, 코드로 확인됨)
- 화면(`ui/bonds_page.py`)에 아래 내용이 하나도 없다. 근거는 docstring `bonds.py:10-22`와 README의 "Day count is ACT/365 simple"뿐이다.
  - Price가 결제일·경과이자 없는 dirty PV라는 것(FC-03).
  - Maturity가 ACT/365F 연이고, 쿠폰이 만기부터 정확히 1/f 간격이라는 것(실제 달력과 −0.59bp 차이 예).
  - Yield가 f회 복리라는 것, z-spread가 연속복리라는 것.
  - DV01은 수익률 DV01(1차)이고, KRD 차트 total은 zero 곡선 DV01이라는 것(화면 836 대 860, 2.9% 차이).
  - Modified/Convexity 단위(년, 년²).
  - Carry/Roll이 3개월간 100당 값이고 연율이 아니라는 것. 카드에는 "per 100"이 없다.
- docstring의 "KRD 합은 (1+y/f)배"는 평탄 곡선에서만 정확하다. 측정 비율은 0.9938~1.0475였다.
- 수정: 계산 결과에 muted notice를 추가한다. "DV01 (yield)" 라벨, KRD 제목 "zero-curve DV01 total", 단위 tooltip을 붙인다. docstring 문장을 고친다. clean 입력은 FC-03 수정안을 따른다.
- 회귀 테스트(제안, NOT_RUN): `ui/bonds_page.py` 자체 검사에서 calc 실행 후 texts에 "dirty", "ACT/365F", "yield DV01"이 있는지 확인한다.

### ③ 재현 단계
1. 사본 생성: `git -C /home/user/quantgen archive HEAD | tar -x -C <W>/repo_copy`. 그다음 cache 4개 파일을 연 적 없이 삭제한다.
2. `cd <W>/repo_copy && python3 -B <W>/t1_table21.py <W>/repo_copy`: 표 2.1과 규칙 200건.
3. `python3 -B <W>/t2_edges.py <W>/repo_copy`: 경계 조건.
4. `python3 -B <W>/t3_fractional.py <W>/repo_copy`: 7.3y와 실제 결제.
5. `python3 -B <W>/t4_curve_risk.py <W>/repo_copy`, 그리고 `python3 -B <W>/t4b_krd_partition.py`.
6. `MPLBACKEND=Agg python3 -B <W>/t5_ui_drive.py <W>/repo_copy`: 실제 `build_bonds_page`를 가짜 page와 synthetic 곡선으로 구동해 화면 문자열을 기록한다.
7. 수정 검증:
   - `python3 -B <W>/apply_fix.py <W>/fix_copy`(patch A).
   - `--funding`으로 `<W>/fixB_copy`(A+B).
   - 각각에서 `t7_regression.py`, `-m core.ficc.bonds`, `-m ui.bonds_page`, `-m tests.ficc_acceptance` 실행.
8. 전후 비교: `python3 -B <W>/t9_before_after.py <W>`.

### ⑤ 수정안 (사본에서만 적용·검증; 저장소 미변경)
- `<W>/proposed_fix.diff` 요약:
  - `core/ficc/bonds.py`:
    - `Bond.__post_init__`: 정수 freq만 허용(B-03).
    - `carry_roll`: funding을 DF 기반 단리로(B-05, 선택 patch B). 만기 ≤ horizon 분기는 `dirty_aged, paid = 0.0, sum(amounts)`로 바꾸고 공통식 `clean_aged = dirty_aged + paid − accrued`를 쓴다(B-01).
    - `analyze_bond`: ytm 범위 검사(B-04).
    - 자체 검사 377행 갱신(B-05).
  - `core/ficc/curves.py:coupon_times:47`: `n = max(1, …)`(B-02).
- 주의: 저장소의 두 파일은 CRLF 줄끝이다. 실제 적용 시 CRLF를 유지해야 한다.
- 전후 비교(synthetic 곡선, 같은 입력):

| 경우 | 항목 | HEAD | patch A | patch A+B |
|---|---|---|---|---|
| 5.5%, 10y, y 4.5% | 가격, DV01 | 107.9819, 836.29 | 같음 | 같음 |
| 5.5%, 10y, y 4.5% | carry / total / breakeven | −1.1773 / −1.5238 / −18.22bp | 같음 | −1.2077 / −1.5542 / −18.58bp |
| 5.5%, 0.25y, f2 | roll / total / breakeven | −1.6132 / −2.6400 / −1062.63bp | −0.2382 / −1.2650 / −509.18bp | −0.2382 / −1.2936 / −520.69bp |
| 5.5%, 0.2y, f2 | roll / total / breakeven | −1.8396 / −2.6677 / −1339.20bp | −0.1896 / −1.0177 / −510.88bp | −0.1896 / −1.0360 / −520.10bp |
| 5.5%, 0.25y, f4(정상 경우) | roll / total | −0.2472 / −1.2417 | 같음 | −0.2472 / −1.2700 |

- patch A의 스텁 결과(−509.1786bp)는 독립 계산값과 정확히 같다.
- 성능(중앙값, 같은 머신): analyze_bond 1.6~4.7ms(HEAD), 1.7~3.1ms(A), 2.0~3.0ms(A+B). 차이는 측정 잡음 수준이다.
  - synthetic 패널 로드 6.7/4.5/5.1ms, bootstrap 4.5/4.1/4.4ms.
  - FRED 요청 시간과 차트 렌더링 시간은 재지 않았다(NOT_RUN).

### ⑥ 테스트 로그 (PASS / FAIL / NOT_RUN)
| 테스트 | 대상 | 결과 | 로그 |
|---|---|---|---|
| t1 표 2.1 + 규칙 200건 | HEAD 사본 | PASS(최대 3.2e-12, 규칙 불일치 0, 화면 30/30 일치) | t1_table21.log |
| t2 그리드 640건, 무이표 닫힌식 | HEAD | PASS(2.9e-14, 1.1e-13) | t2_edges.log |
| t2 미세 만기 | HEAD | FAIL → B-02 | t2_edges.log |
| t2 Yield 201% 메시지 | HEAD | FAIL → B-04 | t2_edges.log |
| t3 7.3y와 실제 결제 | HEAD | 측정 완료(dirty 확인, FC-03) | t3_fractional.log, t3b_schedule_offset.log |
| t4 44 조합 z/KRD/carry/roll/breakeven | HEAD | PASS, 단 스텁 12 조합 roll/total/breakeven FAIL → B-01 | t4_curve_risk.log |
| t4b 단위분할 | 독립 | PASS | t4b_krd_partition.log |
| t5 UI 구동 18회 | HEAD 사본 build_bonds_page | 화면 문자열 = 독립값. B-01, B-02, B-04가 화면에 나타남 | t5_ui_drive.log |
| `python3 -B -m core.ficc.bonds` | HEAD / A / A+B | PASS / PASS / PASS | t6_repo_tests.log, t7_after_patchA.log, t7_after_patchAB.log |
| `python3 -B -m ui.bonds_page` | HEAD / A / A+B | PASS / PASS / PASS | 같은 로그 |
| ficc_acceptance 채권 10건(in-process) | HEAD / A | 10/10 PASS / 10/10 PASS | t6_repo_tests.log, t7_after_patchA.log |
| ficc_acceptance 전체 57건 | HEAD / A / A+B | 57/57 / 57/57 / 57/57 PASS | t8_ficc_head.log, t8_ficc_patchA.log, t7_after_patchAB.log |
| t7 회귀 7건 | HEAD | 6 FAIL, 1 PASS(예상대로) | t7_before.log |
| t7 회귀 7건 | patch A | 6 PASS, 1 FAIL(funding은 patch B 전용) | t7_after_patchA.log |
| t7 회귀 7건 | patch A+B | 7/7 PASS | t7_after_patchAB.log |
| tests/run_all.py | — | NOT_RUN(qa 파일을 다시 씀, 금지) | — |
| QuantLib 대조 | — | NOT_RUN(미설치; financial_calcs 8~11행 인용) | — |
| 실제 FRED 곡선 위 z/KRD/carry | — | NOT_RUN | — |
| 사람이 Flet 창에서 클릭 | — | NOT_RUN(가짜 page로 같은 코드 경로 구동) | — |
| B-06 UI 문구 회귀 테스트 | — | NOT_RUN(제안만) | — |

### ⑦ 남은 리스크와 미확인
- **미확인**: 표 2.1 행 1~3의 "가격 입력 100"이 실제로 입력되어 있었는지. 코드상 둘 다 있으면 오류가 나므로, 캡처 시점에는 Price가 빈칸이었을 것으로 보인다.
- **미확인**: 실시장 정확성. 실제 UST의 clean 호가·결제·ACT/ACT 쿠폰 달력으로 Bloomberg나 QuantLib과 대조하지 않았다. 실제 결제 예는 독립 street 공식으로만 계산했다.
- **미확인**: FRED 곡선에서의 z-spread, carry, roll 수치. 공식은 곡선과 무관하게 4개 곡선에서 검증했다.
- **미확인**: 회귀 테스트를 저장소와 CI에 추가하는 일. 제안 코드는 스크래치에만 있다.
- 다른 차원으로 넘길 관찰(이 차원의 발견으로 올리지 않음):
  - (A) Coupon 칸이 빈칸이면 0% 쿠폰으로 조용히 계산한다(`ui/bonds_page.py:107`, UI 구동에서 0 입력과 같은 결과).
  - (E) 현재 synthetic 곡선의 3m zero가 약 9.45%여서 z-spread가 −318bp, carry가 크게 음수로 나온다.
- breakeven은 1차 근사다(오늘의 Mod 사용, 볼록성·시평 듀레이션 무시). 설명 문구에 '근사'라는 말이 없다(B-06 범위).

### 스크립트와 산출물 경로
`<W>` = /tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/B_pricing_risk
- 스크립트: `<W>/indep.py`, `<W>/t1_table21.py`, `<W>/t2_edges.py`, `<W>/t3_fractional.py`, `<W>/t4_curve_risk.py`, `<W>/t4b_krd_partition.py`, `<W>/t5_ui_drive.py`, `<W>/t6_repo_tests.py`, `<W>/apply_fix.py`, `<W>/t7_regression.py`, `<W>/t9_probe.py`, `<W>/t9_before_after.py`
- 결과(JSON): `<W>/t1_table21.json`, `<W>/t2_edges.json`, `<W>/t3_fractional.json`, `<W>/t4_curve_risk.json`, `<W>/t5_ui_drive.json`, `<W>/t9_before_after.json`
- 로그: `<W>/*.log`
- 수정 diff: `<W>/proposed_fix.diff`
- 사본: `<W>/repo_copy`(HEAD), `<W>/fix_copy`(patch A), `<W>/fixB_copy`(A+B)

### 독립 검증

검증 대상은 B_pricing_risk 보고서의 발견 6건(B-01~B-06)이다. 저장소는 바꾸지 않았다(`git status --short` 0줄). 저장소 코드는 `git archive HEAD` 사본 세 개에서만 실행했다.
- `head`: HEAD 그대로.
- `patched`: 조사자의 `proposed_fix.diff` 적용.
- `mfix`: patched에 아래 M-1~M-3 수정을 더함.

독립 구현 `my_indep.py`는 저장소를 import하지 않는다. Decimal 50자리다. 조사자와 다른 수치 경로를 썼다.
- YTM: Illinois regula falsi.
- 위험 지표: 가격함수의 h=1e-15 중심차분.
- 곡선: bootstrap을 직접 구현.
- z-spread: 이분법.
- KRD: 해석 미분.

| id | 유지 여부 | 정정 심각도 | 정정 상태 | 근거 |
|---|---|---|---|---|
| B-01 | 유지 | P2 (유지, P1 경계) | 테스트로 확인됨 | 재현값: synthetic 0.25y Breakeven 저장소 −1062.625bp, 독립 −509.1786bp. 0.2y −1339.20 대 −510.88. flat −550.906 대 +2.5406. sloped −423.081 대 +130.366. HEAD에서 연 6% 0.1y는 −5386.7bp, 1개월 채권은 −2751.0bp. 화면 카드 값도 같다(`v3_ui_head.log`). 수정은 roll과 total을 바로잡는다. 다만 T ≤ horizon일 때 breakeven과 "Carry (3m)" 라벨 문제가 남는다(M-3). `proposed_fix.diff`에는 patch B(funding)도 같이 들어 있다. |
| B-02 | 유지 | P3 | 테스트로 확인됨 | UI에서 Maturity 0.0000000001을 넣으면 "IndexError: index -1 is out of bounds…"가 나온다. 수정 후에는 102.750으로 계산된다. 그러나 화면이 "Macaulay 0.00y", "Breakeven −521.3bp"를 보여 준다. M-3 수정과 함께 넣거나, 1일 미만 만기를 거부하는 편이 낫다. |
| B-03 | 유지 | P3 | 테스트로 확인됨 | freq=2.9는 2로, freq=1.5는 1로 조용히 바뀐다. 수정 후에는 거부된다. 부작용으로 문자열 freq도 거부되지만, grep 결과 그런 호출자는 없다. |
| B-04 | 유지 | P3 | 테스트로 확인됨 | HEAD에서는 "No yield in [-0.5, 2.0] reproduces price 2.7364."가 나온다. 수정 후 화면은 "Yield 201% is outside the supported range [-50%, 200%]."다. Yield −40은 여전히 z-spread 문구가 나온다(보고서 기재와 같음). |
| B-05 | 유지 | P3 | 테스트로 확인됨 | 결정적 증거가 있다. 채권 자기 수익률의 flat 곡선(z=0)에서 정답 total은 0이다. HEAD total은 0.0067074377로, P(e^{zh}−1−zh)와 정확히 같다. DF 조달로 바꾸면 −2.2e-15다. synthetic carry는 −1.1773에서 −1.2077로 바뀐다(patched 화면 −1.208). 이 조달 관례는 docstring 19-20행에 적혀 있다. 하지만 DF 할인과 일관되지 않는다. |
| B-06 | 유지 | P3 | 테스트로 확인됨 (코드로 확인됨에서 정정) | 화면 텍스트, tooltip, hint를 모두 훑었다. dirty, clean, accru, settle, ACT, 365, compound, continuous는 한 번도 나오지 않는다(`v11_b06_textscan.log`). KRD 합 860.40 대 DV01 836.29도 독립 계산과 같다. 보정할 점: 카드에는 "per 100"이 없지만, Analysis 문구에는 "per 100"이 있다. 추가 근거: 문구 "+100bp parallel move costs roughly 83,629 before convexity"는 수익률 DV01을 쓴다. Scenarios의 "+100bp parallel"은 zero 곡선 이동이고, 1차값은 86,040, 전체 재평가는 −82,220이다(synthetic). |

#### 독립 재계산 (스팟체크, 저장소 함수와 별도)
1. **표 2.1 다섯 행**(`v1_table.log`)
   - 내 값과 저장소의 최대 차이는 3.18e-12다. 조사자 고정값과는 ≤3.7e-9로, 고정값의 반올림 수준이다.
   - YTM: P95는 6.177690406202%, P105는 4.862681689519%다. 저장소와 차이는 −3.5e-16, −9.7e-17이다.
   - 화면 문자열 30개가 모두 같다.
   - 정수 기간 par/premium/discount 위반은 0건이다. 7.3y는 101.0911이고, Price 100에서 YTM은 5.6846%다(FC-03).
2. **synthetic 곡선 10y 5.5% @4.5%**(`v2_curve.log`)
   - 내가 직접 bootstrap한 knot와 저장소 knot의 차이는 3.6e-16이다.
   - z-spread −317.8bp(차이 1.4e-17).
   - KRD 합: 해석값 860.4034, 저장소 860.4035. 키별 상대오차는 ≤1.6e-7이다.
   - carry −1.177343, roll −0.346437, total −1.52378, breakeven −18.2207bp. 조사자 값과 같다.
3. **B-01 수치**: 위 표의 값이 모두 재현된다.
4. **역산 가능 가격 범위와 실제 결제 예**(`v9_misc.log`)
   - 가격 범위: [2.75009, 34991.39].
   - w 0.597826, street dirty 107.261644, 경과이자 1.105978, clean 106.155666.
   - 저장소식 가격 107.223769. 첫 현금흐름은 112일 뒤다.
   - clean을 입력하면 YTM은 4.66806%다.
   - 모두 보고서와 같다.

#### 수정안 검증
- CRLF를 LF로 바꾼 뒤 `proposed_fix.diff`가 깨끗하게 적용된다.
- 내 회귀 테스트 `v5_regress.py`(7건)
  - HEAD: 6 FAIL, 1 PASS.
  - patched: 7/7 PASS.
  - 처음에는 내 테스트 하나의 식이 틀려 있었다. 고친 뒤 결과다.
- 조사자 `t7_regression.py`: HEAD 6 FAIL, 1 PASS. patched 7/7 PASS.
- 자체 검사 `-m core.ficc.bonds`, `-m core.ficc.curves`, `-m ui.bonds_page`: head, patched, mfix 모두 ok.
- `tests.ficc_acceptance` in-process: head, patched, mfix 모두 57/57 PASS.
- B-01 수정은 정확하고 최소다. 하지만 완결되지 않았다(M-3). B-02 수정도 정확하지만, 의미 없는 숫자를 화면에 띄운다(M-3, M-1 하한 쪽과 묶을 것).

#### 누락 발견 (전문)

**M-1 (P3, 테스트로 확인됨) 만기 상한이 없다**
- 위치: `core/ficc/bonds.py:Bond.__post_init__:51-52`, `core/ficc/curves.py:coupon_times:47-48`, `ui/bonds_page.py:107`.
- 재현(`v4_bigT.log`, `v7_ui_extra.log`):
  - UI Maturity 20000: "The function value at x=-0.5 is NaN; solver cannot continue."(0.02초).
  - 1000000: 같은 문구(0.62초).
  - 코어 1e7: 10.2초, RSS 933MB.
  - 1e8: 2.5GB 상한에서 "MemoryError: Unable to allocate 1.49 GiB".
- 기대: 상한을 넘으면 즉시 만기 관련 오류 메시지를 낸다.
- 원인: 상한 검사가 없다. 일정 배열의 크기가 T·f다. z_spread는 −0.5에서 exp(0.5t)가 overflow하고 DF가 underflow해서 NaN이 된다(T ≳ 1.1e4).
- 영향: 잘못된 숫자는 나오지 않는다. 문구가 불친절하다. 0을 더 쳐 넣는 오타 하나로 Run 한 번에 수 초와 GB 단위 메모리를 쓴다.
- 수정: `if self.maturity > 100.0: raise ValueError(...)`.
- 회귀 테스트: `v10_missed.py test_m1`. HEAD FAIL, mfix PASS. 57/57 유지.

**M-2 (P3, 테스트로 확인됨) 작은 명목금액에서 DV01이 0으로 보인다**
- 위치: `ui/bonds_page.py:34-35,137`(`,.0f`), `core/ficc/insights.py:50-53,110-111`, `ui/fcharts.py:144`.
- 재현: Notional 500이면 DV01 카드가 "0"이고, 문구는 "the DV01 is 0 per bp"다. Notional 1000이면 "1"이다(실제 0.418, 0.836).
- 기대: 0.42, 0.84.
- 영향: 위험이 0인 것처럼 보인다. KRD 제목도 "total 0 per bp"가 된다.
- 수정: |DV01| < 100이면 소수 둘째 자리까지 쓴다. 카드, 문구, KRD 제목 모두에 적용한다(mfix는 카드만 고침).
- 회귀 테스트: `test_m2`. HEAD FAIL, mfix PASS.

**M-3 (P3, 테스트로 확인됨) 만기가 horizon 안이면 breakeven과 기간 라벨이 틀린다 (B-01 수정 후에도 남음)**
- 위치: `core/ficc/bonds.py:carry_roll:189,201-208`, `ui/bonds_page.py:157,163`, `core/ficc/insights.py:122-128`.
- 재현:
  - patched에서 0.25y 5.5% 반기 @4.5%, synthetic: "Breakeven −520.7bp", "yields must fall 520.7bp…".
  - 1/12y: −5.1bp(HEAD −2751.0bp).
  - 라벨은 "Carry (3m)"인데 실제 계산 기간은 h=T=1m이다.
- 기대: breakeven은 n/a로 둔다. 라벨은 실제 기간 h로 한다.
- 원인: 시평에 채권이 없다(dirty_aged=0). 그래서 어떤 수익률 변화도 total을 바꾸지 못한다. 그런데도 공식을 적용하고, horizon은 요청값을 그대로 반환한다.
- 영향: 화면이 사실과 다른 문장을 보여 준다. HEAD에서는 B-01에 가려져 있다.
- 수정: 이 분기에서 breakeven을 NaN으로, horizon을 h로 반환한다. 카드는 "n/a (matures inside horizon)", 문구는 대체 문장을 쓴다.
- 회귀 테스트: `test_m3`. HEAD FAIL, patched FAIL, mfix PASS. 57/57 유지. 수정 diff는 `mfix_extra.diff`.

#### 미실행 (NOT_RUN)
- 실제 FRED 곡선.
- QuantLib 대조(미설치).
- 사람이 Flet 창에서 직접 클릭.
- Windows에서 M-1 메모리 동작(Linux ulimit에서만 측정).

#### 경로
산출물은 모두 `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/verify_B_pricing_risk/` 아래에 있다.
- 스크립트: `my_indep.py`, `v1_table.py`, `v2_curve.py`, `v3_ui.py`, `v4_bigT.py`, `v5_regress.py`, `v6_repo_suites.py`, `v7_ui_extra.py`, `v10_missed.py`
- 로그: `*.log`
- diff: `mfix_extra.diff`
- 사본: `head`, `patched`, `mfix`
