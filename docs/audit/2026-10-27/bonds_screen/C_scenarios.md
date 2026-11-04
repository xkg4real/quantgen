# Bonds 화면 검증 C. 시나리오 손익(전체 재평가)

> 작성 메모 (오케스트레이터): 하네스가 하위 에이전트의 보고서 파일 쓰기를 막아, 조사 에이전트가 반환한 본문과 독립 검증자가 반환한 검증 절을 내용 변경 없이 옮겼습니다. 저장소 코드는 바꾸지 않았습니다.

## C. 시나리오 손익(Full revaluation) 검증 — 요청서 3.C, 2.3

### 0. 범위와 방법
- 대상: Bonds > Scenarios. `ui/bonds_page.py` worker → `core/ficc/data.py` → `core/ficc/curves.py` → `core/ficc/bonds.py:scenario_pnl`. 화면 출력은 `ui/fcharts.py:scenario_chart`, `core/ficc/insights.py:narrate_bond`.
- 저장소 파일은 바꾸지 않았다(`git status` 0줄). 실행은 모두 `git archive HEAD` 스크래치 사본에서 했다. 관련 코드는 기준선 커밋 eacd57d(2026-10-23) 이후 바뀌지 않았다(`git log`).
- 독립 구현 `indep.py`는 공식에서 새로 짰다. repo import 없음, 순수 float과 이분법만 쓴다. 같은 입력을 repo 함수와 독립 구현에 모두 넣어 비교했다.
- 이전 감사와 겹치는 것은 ID만 인용한다. D03-V01(부분 곡선을 FRED로 표시, P1), D03-03(해설에 합성 표시 없음), FC-03(Price는 dirty 가격).

### ① 요약
- 계산식은 코드 문서와 같다. 5개 곡선 × 2개 채권 × 9개 시나리오에서 repo와 독립 구현의 P&L 차이는 최대 3.7e-9원이다(테스트로 확인됨).
- 화면 숫자를 정확히 재현하지는 못했다(**미확인**). 실제 UST 곡선을 구하지 못했다. WebFetch로 fred.stlouisfed.org와 home.treasury.gov에 접속하면 DNS 오류(`getaddrinfo ENOTFOUND`)가 났다.
- 화면 숫자는 합성 곡선 결과가 아니다. HEAD 합성 곡선에서는 B +100bp가 −75,256으로, 화면 −74,657과 −599 차이다(테스트로 확인됨, HEAD 코드 기준).
- 화면 숫자는 이 코드의 모델로 설명된다. 모델은 연속복리 zero 이동, z-spread 고정이다. 완만한 우상향 곡선 하나로 화면 9개 숫자가 모두 ±0.53 안에 들어온다. 이 곡선을 FRED 라벨로 페이지에 넣으면 9개 중 8개는 같은 문자열이다. 나머지 하나(+25bp)는 반올림 경계라 1원 다르다. 이 곡선은 **가상**이며 시장 데이터가 아니다.
- YTM ±100bp로 계산한 값은 화면과 맞지 않는다. B +100bp는 −72,697이다. 그럴듯한 곡선 형태 범위 [−75,331, −74,175] 밖이다.
- 결함은 P0/P1 없음, P2 2건(C-01 shock 단위 미표기, C-03 fly 톱니 모양), P3 4건이다. 스크래치 수정본에서 회귀 테스트 10/10이 통과했다. HEAD에서는 6/10이 통과한다. 기존 테스트 57/57은 두 트리 모두 통과했다.

### ② 심각도별 이슈
| ID | 심각도 | 상태 | 위치 | 한 줄 |
|---|---|---|---|---|
| C-01 | P2 | 테스트로 확인됨 | `bonds.py:288-292`, `curves.py:119-123`, `ui/bonds_page.py:52-56,180`, `insights.py:112-113` | "+100bp parallel"은 연속복리 zero 금리 이동이다(채권 수익률 +102.5~103.0bp에 해당). 화면 어디에도 그 말이 없다. 같은 카드의 해설은 수익률 DV01×100을 "+100bp parallel"이라 부른다 |
| C-03 | P2 | 테스트로 확인됨 | `bonds.py:283`, `ui/bonds_page.py:52-56` | "2y-5y-10y fly"가 톱니 모양이다. 3y·7y·20y가 0이다. 7y 채권 fly P&L은 −794이고, 선형 fly라면 −6,142다. Shock 열은 −12.5를 "−12"로 표시하고 3y/7y를 숨긴다 |
| C-02 | P3 | 테스트로 확인됨 | `bonds.py:266,319`, `ui/bonds_page.py:180`, `fcharts.py:160,163` | "P&L %"의 분모는 시장가치다(new/price−1). 명목금액이 아닌데 표시가 없다. A(107.982) +100bp: −7.56%. 명목 기준이면 −8.16% |
| C-04 | P3 | 테스트로 확인됨 | `bonds.py:293-296`, `data.py:593-595` | 비평행 shock을 곡선 knot에만 적용한다. 그래서 FRED가 만기 하나를 빠뜨리면 같은 이름 시나리오의 모양이 바뀐다(7y 채권 bear steepener +16.3%). D03-V01과 연결된다 |
| C-05 | P3 | 테스트로 확인됨 | `data.py:361-377` | 합성 곡선이 비현실적이다. 1m 9.59%에서 30y 7.17%로 역전되어 있고, z-spread가 −317.8bp다. 배너는 있다(`bonds_page.py:122-124`) |
| C-06 | P3 | 테스트로 확인됨 | `tests/ficc_acceptance.py:279-287`, `bonds.py:389-401` | 시나리오 테스트는 부호와 부등식만 본다. 고정 기대값, 단위 정의, shock 모양을 보는 테스트가 없다. fly 모양을 바꿔도 57/57이 그대로 통과한다 |

### ③ 재현 단계
1. 스크래치 사본: `git -C /home/user/quantgen archive HEAD | tar -x -C .../C_scenarios/repo`. 요청서가 지정한 캐시 CSV 4개는 열지 않고 지운다.
2. `cd .../C_scenarios/repo && python3 -B ../c1_reproduce.py`: 합성 곡선, 평탄 곡선 3개, 예시 정상 곡선에서 repo와 독립 구현을 비교한다. 출력은 `c1_reproduce.log/json`이다.
3. `python3 -B c2_shape.py`: (a) 역추정, (b) 곡선 형태별 범위, (c) zero 이동과 수익률 이동, (d) 볼록성 비대칭, (e) knot 사이 유효 shock.
4. `python3 -B c3_fit.py`: 제약을 둔 곡선 족(NS, 매끈한 자유 par)으로 화면 9개 숫자를 역추정한다.
5. `cd repo && python3 -B ../c4_ui.py`: 실제 `build_bonds_page`를 가짜 Page로 돌린다. S1은 합성, S2는 Auto에 FRED 스텁 실패, S3은 가상 곡선을 FRED 라벨로 넣은 경우다.
6. `cd repo && python3 -B ../c5_hyp_log.py`: 시나리오별 중간값 로그(key tenor zero, 현금흐름일 DF, 새 가격, P&L).
7. `cd repo && python3 -B ../c7_knots.py`: knot 집합에 따른 의존성.
8. `python3 -B c8_regression.py repo`와 `python3 -B c8_regression.py repo_fix`: 회귀 테스트를 수정 전후로 돌린다.
9. `python3 -B c9_existing_both.py`: 기존 self-check와 `tests/ficc_acceptance.py` 전체를 두 트리에서 돌린다. `python3 -B c10_before_after.py`는 같은 입력으로 수정 전후 값과 시간을 비교한다.

### ④ 수식과 독립 계산

#### 4.1 코드 추적표
| 단계 | 파일:함수:라인 | 내용 |
|---|---|---|
| 입력 | `ui/bonds_page.py:build_bonds_page.run.worker:104-113` | Bond(coupon/100, maturity, freq, notional). `_num(ytm)/100`. 곡선은 `load_treasury_curve(source)` |
| 곡선 데이터 | `core/ficc/data.py:load_treasury_curve:552-568`, `_treasury_from_fred:571-596`, `synthetic_curve_panel:361-377` | FRED DGS* 퍼센트를 /100(`:582`). 열별 forward fill. Auto에서 실패하면 합성 패널 |
| 스냅숏 | `data.py:CurvePanel.latest:142-143` | 마지막 행 |
| 부트스트랩 | `curves.py:curve_from_snapshot:262-267` → `bootstrap_par_curve:165-201` | t<1y: z=ln(1+y·t)/t. t≥1y: y/f·ΣDF(t_i)+DF(T)=1을 brentq로 푼다 |
| 할인 | `curves.py:YieldCurve._log_df:77-85`, `df:87-89` | knot 사이는 z·t 선형(log DF 선형), 양 끝 밖은 zero 고정 |
| z-spread | `bonds.py:z_spread:108-115`. scenario_pnl 안에서 한 번 계산(`:313`) | Σcf·DF·e^(−s·t)=P를 brentq로 푼다. 구간 [−0.5, 2.0] |
| 평행 shock | `bonds.py:shocked_curve:291-292` → `curves.py:shifted:119-123` | 모든 knot zero에 +bp·1e-4 |
| 비평행 shock | `bonds.py:_ramp:269-271`, `SCENARIO_SHOCKS:274-284`, `shocked_curve:293-296` | KEY_TENORS 위 bp를 곡선 knot에 np.interp한다(끝 밖은 고정). 그 다음 zero에 더한다 |
| 재평가 | `bonds.py:price_from_curve:102-105`, `scenario_pnl:316-319` | new = Σcf·DF′(t)·e^(−z·t) |
| P&L | `bonds.py:314,319` | pnl = (new − price)·notional/face(=100). pnl_pct = new/price − 1 |
| 화면 | `ui/bonds_page.py:170-190`, `fcharts.py:scenario_chart:148-165`, `insights.py:narrate_bond:105-139` | 표, Worst/Best 타일, 막대그래프, 해설, AI 페이로드 |

#### 4.2 공식, 단위, 관례
- 가격: P = Σ cf_i (1+y/f)^(−f·t_i). 단위는 액면 100당 dirty 가격이다(FC-03). 현금흐름일 t_i = T − k/f. 정산일과 경과이자는 없다.
- 곡선: 연속복리 zero z(t). DF(t)=exp(−z(t)·t). knot 사이는 z·t를 선형 보간한다.
- 시나리오: z′_k = z_k + Δ_k. 평행이면 Δ_k = Δ이다. log DF가 knot 사이에서 선형이므로 **모든 t에서 정확히** DF′(t)=DF(t)·e^(−Δ·t)다. c5 로그에서 모든 key tenor의 dzero가 +100.00이다.
- z 고정의 순서: (1) 원래 곡선과 원래 가격으로 z를 구한다. (2) 곡선 zero를 흔든다. (3) DF′(t)·e^(−z·t)로 할인한다. 평행 이동이면 z+Δ로 할인하는 것과 같다. 그래서 곡선의 **수준**은 z가 흡수한다. 평탄 곡선 3.00%, 4.45%, 5.43%가 소수 첫째 자리까지 같은 P&L을 낸다(c1).
- P&L(Δ) = Σ PV_i·(e^(−Δ·t_i) − 1). 이때 Σ PV_i = P다. 평행 P&L은 곡선 **모양**(PV 가중치)에만 의존한다.
- 1bp에서 zero 이동 P&L ÷ 수익률 이동 P&L = 1 + y/f (dr_c/dy = 1/(1+y/f)).

#### 4.3 독립 계산 대조 (repo와 indep 차이 최대값, 원)
| 곡선 | 최대 \|Δzero\| | 최대 \|ΔP&L\| |
|---|---|---|
| 합성(days=504, 라벨 2026-10-27) | 2.4e-16 | 3.7e-9 |
| 평탄 4.4501% / 5.4257% / 3.0000% cc | 0 | 4.3e-10 / 6.6e-9 / 5.7e-10 |
| 예시 정상 곡선(시장 아님) | 9.9e-16 | 1.9e-9 |
| 가상 적합 곡선(c5) | 7.3e-16 | < 0.1 표시 단위에서 동일 |

#### 4.4 화면 대조 (명목 1,000,000, P&L 원)
| 채권/시나리오 | 화면 | 가상 적합 곡선 | 평탄(자기 수익률) | 합성 HEAD | YTM±Δ(수익률 이동) |
|---|---|---|---|---|---|
| A 5.5%/4.5% 기준가 | 107.982 | 107.982 | 107.982 | 107.982 | 107.982 |
| A +100bp | −81,597 | −81,596.5 | −81,724.3 | −82,219.9 | −79,818.6 |
| A −100bp | +89,400 | +89,400.0 | +89,545.9 | +90,112.3 | +87,710.3 |
| B 5.5%/5.5% 기준가 | 100.000 | 100.000 | 100.000 | 100.000 | 100.000 |
| B +25bp | −19,305 | −19,304.5(표시 −19,304) | −19,336.7 | −19,461.7 | −18,813.6 |
| B −25bp | +19,748 | +19,748.5 | +19,781.8 | +19,911.0 | +19,258.3 |
| B +100bp | −74,657 | −74,657.2 | −74,780.1 | −75,255.7 | −72,696.7 |
| B −100bp | +81,766 | +81,766.2 | +81,906.3 | +82,449.9 | +79,818.6 |
| B bear steepener | −9,888 | −9,888.1 | −9,913.9 | −10,015.2 | 해당 없음 |
| B bull steepener | +27,819 | +27,819.0 | +27,856.6 | +28,003.6 | 해당 없음 |
| B bear flattener | −26,977 | −26,977.0 | −27,012.8 | −27,153.0 | 해당 없음 |

가상 적합 곡선(c3 Fit 2, NS, τ∈[1,5], |β2|≤3%)의 par는 다음과 같다. 1m 4.092, 3m 4.021, 6m 3.948, 1y 3.881, 2y 3.906, 3y 3.992, 5y 4.145, 7y 4.239, 10y 4.317, 20y 4.408, 30y 4.439(%). 잔차 최대는 0.53이다. 다른 곡선 족(매끈한 자유 par, 2s10s +32bp)도 잔차 ±1.0 안에 든다. 해는 유일하지 않다. 그래서 날짜를 특정할 수 없다. 화면 숫자가 말하는 것은 "0~10y 구간이 완만한 우상향(2s10s 약 +30~+55bp)"까지다. 10y 채권은 10y 넘는 par에 영향을 받지 않는다.

#### 4.5 곡선 모양 의존도 (가격 고정, z가 수준 흡수)
조건: NS 400개 무작위 모양, β0 4.5%, |10y−3m| ≤ 200bp, par는 0.25~9%. 범위는 다음과 같다.

| 항목 | 최소 | 최대 | 폭 |
|---|---|---|---|
| A +100 | −82,298 | −81,092 | 1,206 (1.48%) |
| A −100 | +88,822 | +90,201 | 1,379 |
| B +100 | −75,331 | −74,175 | 1,156 (1.55%) |
| B −100 | +81,214 | +82,536 | 1,322 |
| B ±25 | −19,481~−19,178 / +19,617~+19,931 | | 약 310 |
| B bear steep / bear flat / bull steep | −10,031~−9,783 / −27,175~−26,837 / +27,672~+28,027 | | 250~355 |

기울기와 B +100 P&L의 상관은 +0.837이다. 가파를수록 손실이 작다. 장기 현금흐름의 PV 가중치가 줄기 때문이다. 기준 모양별 B +100은 다음과 같다. 평탄 −74,780, +200bp 가파름 −74,421, −148bp 역전 −75,037, 혹 모양 −74,890. 화면 값은 모두 범위 안이다. 수익률 이동 값(−72,697)은 범위 밖이다.

#### 4.6 zero 이동과 수익률 이동의 차이 (평탄 곡선 = 자기 수익률)
| 채권 | Δ | zero 이동 | 수익률 이동 | 비율 | 1+y/f | 같은 가격의 수익률 이동 |
|---|---|---|---|---|---|---|
| A | +1bp | −854.7 | −835.9 | 1.02251 | 1.02250 | +1.023bp |
| A | +100 | −81,724.3 | −79,818.6 | 1.02388 | | +102.506bp |
| A | −100 | +89,545.9 | +87,710.3 | 1.02093 | | −101.995bp |
| B | +1bp | −781.9 | −761.0 | 1.02751 | 1.02750 | +1.028bp |
| B | +100 | −74,780.1 | −72,696.7 | 1.02866 | | +103.007bp |
| B | −100 | +81,906.3 | +79,818.6 | 1.02616 | | −102.494bp |

해설 문장 예시(가상 곡선, A): "DV01 is 836 per bp; a +100bp parallel move costs roughly 83,629 before convexity"와 "worst '+100bp parallel' at −81,597"가 같은 카드에 있다. zero 기준 1차항은 KRD 합×100 = 85,374다. 볼록성 +3,778을 더하면 −81,597이 된다. 수익률 기준이면 −79,819다. 두 정의가 같은 이름으로 섞여 있다(C-01).

#### 4.7 볼록성 비대칭
| 채권 | Mac | 화면 볼록성(수익률) | 연속 볼록성 = C·k² − Mac/f | 2차 예측 | +4차 | 평탄 실제 | 화면 |
|---|---|---|---|---|---|---|---|
| A | 7.9190 | 73.0148 | 72.3780 | 7,815.5 | 7,821.6 | 7,821.6 | 7,803 |
| B | 7.8230 | 71.1522 | 71.2079 | 7,120.8 | 7,126.3 | 7,126.3 | 7,109 |

비대칭 = P&L(+100) + P&L(−100) ≈ C_cont·Δ²·P·N/100이다. 화면 값은 평탄 예측보다 0.24% 작다. 우상향 곡선 가중치 때문이다. 가상 곡선에서는 7,803.5와 7,109.0으로 같다. 화면 볼록성 73.0을 단위 변환 없이 쓰면 7,884(+1.0%)다. B ±25bp는 화면 443, 예측 445.0이다. 결론: 상승 손실 < 하락 이익의 크기 차이는 표시된 볼록성과 맞는다. 다만 zero와 수익률 단위 변환이 필요하다.

#### 4.8 시나리오 이름과 부호 (key tenor bp)
| 시나리오 | 3m | 1y | 2y | 3y | 5y | 7y | 10y | 20y | 30y | 판정 |
|---|---|---|---|---|---|---|---|---|---|---|
| bear steepener | 0 | 0 | 0 | +1.79 | +5.36 | +8.93 | +14.29 | +32.14 | +50 | 장기가 더 오름. 관례와 맞음 |
| bull steepener | −50 | −48.74 | −47.06 | −45.38 | −42.02 | −38.66 | −33.61 | −16.81 | 0 | 단기가 더 내림. 맞음 |
| bear flattener | +50 | +48.74 | +47.06 | +45.38 | +42.02 | +38.66 | +33.61 | +16.81 | 0 | 단기가 더 오름. 맞음 |
| bull flattener | 0 | 0 | 0 | −1.79 | −5.36 | −8.93 | −14.29 | −32.14 | −50 | 장기가 더 내림. 맞음 |
| 2y-5y-10y fly | 0 | 0 | −12.5 | 0 | +25 | 0 | −12.5 | 0 | 0 | 톱니 모양(C-03) |

앱 자체 분류기 `curves.py:_regime:313-322`(10y로 bull/bear, 2s10s로 steep/flat)에 넣으면 4개 이름이 모두 그대로 나온다(c8 테스트 PASS). 2s10s 변화는 ±13.4~14.3bp다. "50bp"는 3m~30y 끝점 기준이다.

#### 4.9 중간값 로그 발췌 (가상 곡선, B, z = +116.2472bp)
기준 zero(%): 3m 4.0013, 1y 3.8431, 2y 3.8681, 3y 3.9562, 5y 4.1150, 7y 4.2145, 10y 4.2974, 20y 4.3989, 30y 4.4361.

| 시나리오 | DF(0.5y) / ×e^(−zt) | DF(10y) / ×e^(−zt) | 새 가격 | P&L(repo) | P&L(indep) |
|---|---|---|---|---|---|
| +100bp | 0.975753 / 0.970098 | 0.588759 / 0.524146 | 92.53428 | −74,657.2 | −74,657.2 |
| −100bp | 0.985559 / 0.979848 | 0.719112 / 0.640193 | 108.17662 | +81,766.2 | +81,766.2 |
| bear steep | 0.980644 / 0.974960 | 0.641450 / 0.571054 | 99.01119 | −9,888.1 | −9,888.1 |
| bear flat | 0.978216 / 0.972547 | 0.629171 / 0.560123 | 97.30230 | −26,977.0 | −26,977.0 |

손검산: 10y zero 4.2974%+1% → e^(−0.52974)=0.58876. e^(−0.0116247·10)=0.89025. 곱은 0.52414로 맞는다. 전체 로그(첫 3개와 마지막 3개 현금흐름일, 모든 시나리오, A·B)는 `c5_hyp_log.json`에 있다. 합성·평탄·예시 곡선 로그는 `c1_reproduce.json`에 있다.

### ⑤ 수정안 (스크래치 `repo_fix`에만 적용, 저장소 미변경)
- `fix_bonds_page.diff` (C-01, C-02, C-03 표시): 헤더를 "Shock (bp, zero cc)"와 "P&L % of MV"로 바꾼다. 평행 shock 문구는 "+100bp all zeros"로 한다. 비평행 shock은 모든 key tenor를 소수 1자리로 보인다. 표 아래에 muted 안내를 단다: "Shocks move continuously-compounded zero rates with the z-spread held; +100bp of zero is about +102.2bp of this bond's yield … P&L % is P&L / market value".
- `fix_insights.diff` (C-01): "DV01 is … per bp of its yield; a +100bp move in that yield costs …"로 바꾼다. 시나리오 문장은 "Of 9 zero-curve scenarios (z-spread held) …"로 바꾼다.
- `fix_fcharts.diff` (C-02): x축을 "P&L on notional (in brackets: % of market value)"로 바꾼다.
- `fix_bonds.diff` (C-03, C-04): fly를 `np.interp(k, [2,5,10], [−12.5, 25, −12.5])`로 바꾼다(2y~10y 사이 선형, 밖은 고정). 끝을 1y/20y에서 0으로 줄이는 안도 있다. **정의 변경이므로 소유자가 정한다.** `shocked_curve`는 shock tenor를 knot으로 먼저 넣는다(보간값이라 기준 곡선은 그대로). `key_rate_shifted`(curves.py:135-138)와 같은 방식이다. `ScenarioRow.pnl_pct` 주석과 `scenario_pnl` docstring에 단위를 적는다.
- 수정 전후 같은 입력 비교(c10): 11개 만기 전체 곡선에서는 평행·ramp 8행이 소수 첫째 자리까지 같다. fly만 바뀐다(가상 B +7,093.0 → +6,510.3, 7y 채권 −796.9 → −6,137.2). 7y knot이 없는 곡선에서는 7y 채권 bear steepener가 HEAD −5,866.8, 수정 −5,043.7이다. 전체 knot 곡선은 −5,043.8이다. 시간은 scenario_pnl 1회(9개 시나리오)에 0.7~1.4ms로 수정 전후 차이가 없다.

### ⑥ 테스트 로그
| 테스트 | 트리 | 결과 |
|---|---|---|
| self-check core.ficc.bonds / curves / insights / ui.fcharts / ui.bonds_page | HEAD 사본 | PASS 5/5 (c9) |
| 같은 self-check | 수정 사본 | PASS 5/5 |
| tests/ficc_acceptance.py 전체(모듈 단독 실행, run_all 아님) | HEAD / 수정 | 57/57 PASS / 57/57 PASS |
| ficc_acceptance 채권 관련 11개 + self-check 3개 | HEAD | 14/14 PASS (c6) |
| c8 회귀 테스트 10개 | HEAD | 6 PASS, 4 FAIL(test_ramp_shock_bites…: 10.459 vs 8.929; test_fly_is_linear…; test_ui_states_shock_units…; test_narrative_separates…). 결함을 잡는 것이 목적인 FAIL이다 |
| c8 회귀 테스트 10개 | 수정 | 10/10 PASS |
| c1 repo와 독립 구현 대조 | HEAD | PASS (최대 3.7e-9) |
| c4 S1 화면 표와 core 값 문자열 일치(A, B) | HEAD | PASS |
| c4 S2 Auto에서 FRED 스텁 실패: 배너, 칩 `curve: SYNTHETIC 2026-10-27`, B +100 −75,256 | HEAD | PASS |
| c4 S3 가상 곡선의 화면 문자열 대조 | HEAD | 9개 중 8개 같음, +25bp는 −19,304 vs −19,305 |
| 실제 FRED/UST 곡선으로 재구성 | — | NOT_RUN (WebFetch DNS 실패. 앱 fetcher 사용은 금지) |
| tests/run_all.py | — | NOT_RUN (금지 규칙) |
| 실제 Flet 데스크톱 창 | — | NOT_RUN (가짜 Page로 대체) |

### ⑦ 남은 리스크와 미확인
- **미확인**: 화면 숫자의 정확한 재현, 사용한 곡선 날짜, FRED 값. 시도한 URL은 FRED fredgraph.csv(11개 id), FRED 시리즈 페이지, Treasury TextView와 CSV, CNBC이다. 모두 `getaddrinfo ENOTFOUND`였다. Stocklake MCP는 "WebFetch만" 규칙 때문에 쓰지 않았다.
- **미확인**: 소유자 PC의 코드 버전. "합성 곡선이 아니었다"는 판단은 HEAD 코드와 같다는 전제 위에 있다.
- **미확인**: 시장 정확성. 시나리오는 모델 시나리오다. 순간 충격, 단일 곡선, z-spread 고정, 연속복리 zero 이동, carry와 시간 경과 없음, dirty 가격 기준(FC-03)이다. 실거래 손익과 맞는지는 검증하지 않았다.
- fly 재정의(C-03)는 수치가 바뀌는 정의 변경이다. 소유자가 승인해야 한다.
- 부분 곡선(D03-V01)이면 비평행 시나리오 모양도 바뀐다(C-04). 수정은 모양 의존성만 없앤다. 부분 곡선 경고는 D03-V01 수정이 맡는다.

### 스크립트와 산출물 경로
`/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/C_scenarios/` 아래 파일:
- 스크립트: `indep.py`, `c1_reproduce.py`, `c2_shape.py`, `c3_fit.py`, `c4_ui.py`, `c5_hyp_log.py`, `c6_existing_tests.py`, `c7_knots.py`, `c8_regression.py`, `c9_existing_both.py`, `c10_before_after.py`, `c11_fix_ui.py`
- 로그와 JSON: 각 스크립트와 같은 이름의 `.log`, `.json`
- 수정 diff: `fix_bonds.diff`, `fix_bonds_page.diff`, `fix_insights.diff`, `fix_fcharts.diff`
- 트리: 스크래치 사본 `repo/`(HEAD), 수정본 `repo_fix/`

### 독립 검증 (C_scenarios)

**방법.** 내 독립 구현 `vindep.py`를 공식에서 새로 짰다. repo import는 없고, 순수 float와 이분법만 쓴다. HEAD 사본(`repo/`)을 새로 만들었다. 조사자 diff 4개는 내 사본 `repo_fix/`에 그대로 적용됐다. 결과는 조사자 `repo_fix`의 core/ui와 같다. 결함 2건을 고친 보정본 `repo_fix2/`도 만들었다. 저장소는 바꾸지 않았다(`git status` 0줄). 실제 UST 곡선은 NOT_RUN이다. curl로 FRED와 Treasury에 접속하면 프록시가 `CONNECT tunnel failed, response 403`을 돌려준다.

**직접 다시 계산한 수치(vindep, 명목 1,000,000).**
- 평탄 곡선(자기 수익률): B +100 −74,780.06, −100 +81,906.35. A +100 −81,724.34, −100 +89,545.90. B ±25 −19,336.73 / +19,781.81.
- YTM 이동: A +100 −79,818.56. B +100 −72,696.73. B −100 +79,818.56.
- 1bp 비율(zero/수익률): A 1.0225000, B 1.0275000. 1+y/f와 같다. 같은 가격이 되는 수익률 이동: A +102.506/−101.995bp, B +103.007/−102.494bp.
- 가상 곡선(조사자 c3 `par_pct` 전체 정밀도): 화면 문자열 9개 중 8개가 같다. B +25bp는 −19,304.47로 화면 −19,305와 다르다. z는 A 18.526bp, B 116.247bp다. 비대칭(±100)은 A 7,803.5, B 7,109.0이다.
- 합성 곡선(repo 생성기의 par를 내 bootstrap에 넣음): par 9.586%(1m)~7.171%(30y). z는 A −317.75bp, B −220.80bp다. B +100은 −75,255.73이다.
- repo와 vindep의 P&L 차이는 평탄·가상·합성 곡선, A와 B 전체에서 최대 2.0e-9다.
- fly: 4.5% 7y 채권은 −794.2(앱), 선형 fly는 −6,142.1이다. C-04: 7y knot가 없을 때 −5,866.8, 전체 knot일 때 −5,043.8이다. knot를 넣은 수정본은 −5,043.7이다.

| id | 유지 여부 | 정정 심각도 | 정정 상태 | 근거 |
|---|---|---|---|---|
| C-01 | 유지 | P2 | 테스트로 확인됨 | 위 수치를 독립 구현으로 재현했다. 가상 곡선 A의 해설은 "costs roughly 83,629"이고, 같은 카드의 표는 −81,597이다(v4). 다만 수정안 안내문의 "so parallel rows exceed DV01 x bp"는 +100bp 행에서 거짓이다(M-01). 회귀 테스트는 이 문구를 잡지 못한다. |
| C-03 | 유지(해석 정정) | P2 | 테스트로 확인됨 | 수치와 "−12" 표시를 재현했다. 그러나 HEAD 모양은 앱 KRD 삼각 bump의 조합 −12.5·KR2+25·KR5−12.5·KR10과 같다. 7y는 −796.9 대 −800.9, 10y는 7,093.0 대 7,039.7이다(v8). 일관된 key-rate 정의이고, 결함은 표시와 문서다. 수정안의 "밖은 고정" fly는 1y/20y/30y 값을 크게 바꾼다(M-02). |
| C-02 | 유지 | P3 | 테스트로 확인됨 | A +100은 −7.5565%(MV 기준)와 −8.16%(명목 기준)로 재현된다. HEAD 헤더 "P&L %"를 UI 구동으로 확인했다(v7). |
| C-04 | 유지 | **P3→P2** | 테스트로 확인됨 | 등급 기준의 "edge case에서 틀림"에 해당한다. FRED가 6개 이상 만기만 주면(`data.py:584`) 이름은 같은데 시나리오 모양이 바뀐다. 7y 채권 bear steepener는 −5,866.8 대 −5,043.8(+16.3%)이다. 기본 곡선 차이의 몫은 0.1뿐이다(knot 삽입 시 −5,043.7). 7y 유효 shock은 10.459bp인데 ramp는 8.929bp다. knot 삽입 수정은 기본 가격을 바꾸지 않는다(101.5453866 동일). |
| C-05 | 유지 | P3 | 테스트로 확인됨 | 합성 par, z, B +100을 재현했다. 배너는 있다(`bonds_page.py:122-124`). 제안된 회귀 테스트는 실행하지 않았다(NOT_RUN). |
| C-06 | 유지 | P3 | 테스트로 확인됨 | 내 사본에서 기존 self-check 5/5와 `tests/ficc_acceptance.py` 57/57이 HEAD와 수정본 모두 PASS다. c8은 HEAD 6/10, 수정본 10/10이다. 실패 4건은 조사자가 적은 것과 같다(v3, v6). |

**보고서 정정(결함 아님).** 4.4에 적힌 par 목록은 소수 3자리로 반올림되어 있다. 이 값으로 다시 계산하면 문자열 일치는 9개 중 7개다. A +100이 "−81,596"이 된다. 8/9는 `c3_fit.json`의 전체 정밀도 값으로만 재현된다.

**놓친 항목(수정안 결함 2건).**

**M-01 (P2, 테스트로 확인됨) — 수정안 안내문이 +100bp 행에 대해 틀린 말을 한다.**
- 위치: `C_scenarios/fix_bonds_page.diff`(notice "…so parallel rows exceed DV01 x bp"), `fix_bonds.diff`(`scenario_pnl` docstring "a parallel row is that factor larger than DV01-based estimates").
- 재현: `repo_fix`에서 Scenarios를 실행한다(5.5%/10y/4.5%, synthetic). 안내문은 "…+102.2bp of this bond's yield, so parallel rows exceed DV01 x bp"라고 한다. 표의 +100 행은 −82,220이고 DV01×100은 83,629다. 가상 곡선에서는 A −81,597 대 83,629, B −74,657 대 76,136이다.
- 원인: 1차 계수(1+y/f)만 보고 볼록성을 빼먹었다. 실제 순서는 |P&L(+100)| < DV01·100 < (1+y/f)·DV01·100 < P&L(−100)이다.
- 영향: 수정을 그대로 적용하면 단위 혼동을 고치려던 안내문이 새로 틀린 문장을 화면에 띄운다.
- 수정: 그 구절을 "(first order; convexity then trims losses and adds to gains)"로 바꾼다. docstring도 같은 뜻으로 고친다(`fix2_vs_fix.diff`).
- 회귀 테스트: `v10_regress_fix.py::test_m01_notice_matches_the_numbers`. 결과는 HEAD FAIL(안내문 없음), repo_fix FAIL("exceed"), repo_fix2 PASS다.

**M-02 (P2, 테스트로 확인됨) — 수정안 fly의 "밖은 고정"이 단기와 장기를 −12.5bp 평행 이동시킨다.**
- 위치: `C_scenarios/fix_bonds.diff`(`np.interp(k, [2,5,10], [-12.5,25,-12.5])`)와 c8 `test_fly_is_linear_between_wings_and_belly`(2/3/5/7/10y만 고정).
- 재현: `v5_fly_ends.py`, 가상 곡선, 4.5% 채권을 4.5%에 둔다. 1y는 0에서 +1,237, 20y는 +1,340에서 +13,970, 30y는 +1,347에서 +18,215가 된다. −12.5bp 평행 이동이면 30y는 +21,102다. 조사자의 전후 비교(c10)는 7y와 10y만 보고했다.
- 원인: 날개 값이 1y 이하와 20y 이상까지 이어진다.
- 영향: 같은 "2y-5y-10y fly" 이름 아래 장기 채권 행이 사실상 강세 평행 이동 손익이 된다. 정의 변경의 범위가 보고되지 않았다.
- 수정: 최소 수정은 표시와 문서만 고치는 것이다. HEAD 정의는 KRD와 일관되므로 그대로 둔다. 소유자가 선형 fly를 원하면 끝을 1y/20y에서 0으로 줄인다: `np.interp(k,[1,2,5,10,20],[0,-12.5,25,-12.5,0])`. 그러면 1y는 0, 30y는 772가 된다.
- 회귀 테스트: `v10_regress_fix.py::test_m02_fly_ends_are_not_a_level_shift`(0.25/1/20/30y = 0). 결과는 HEAD PASS, repo_fix FAIL(0.25y = −12.5), repo_fix2 PASS다. repo_fix2는 c8 10/10, bonds/bonds_page self-check ok, ficc_acceptance 57/57이다.

**테스트 로그 요약.** v3: c8 HEAD 6/10, fix 10/10. v6: self-check 5/5와 acceptance 57/57, 두 트리 모두. v10: HEAD 1/2, fix 0/2, fix2 2/2. v11: fix2 acceptance 57/57. 실제 FRED 곡선, 실제 Flet 창, `tests/run_all.py`는 NOT_RUN이다.

산출물: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/verify_C_scenarios/` (vindep.py, v1~v11 스크립트와 로그, fix2_vs_fix.diff, repo/, repo_fix/, repo_fix2/).
