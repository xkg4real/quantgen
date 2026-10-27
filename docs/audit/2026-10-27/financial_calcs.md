# 금융 계산 감사 보고서: 핵심 공식·단위·가정의 독립 검증

- 감사일: 2026-10-27
- 감사 차원: `financial_calcs` (요청서 7장 4번 "금융 계산", 6장 FICC·구조화 상품 항목)
- 성격: 감사 전용. 저장소의 추적 파일은 하나도 고치지 않았다. 수정안은 이 문서 안의 diff로만 제시한다(요청서 7장 8번).
- 비밀정보: `.env`를 열지 않았다. 키·토큰을 출력하지 않았다.
- 네트워크: 시장 데이터 공급자에 접속하지 않았다. 모든 재현은 합성 데이터와 합성 곡선으로 했다. 캐시 파일은 쓰지 않았다. 금지 파일 4개(`yf_SPY.csv`, `yf_BTC-USD.csv`, `binance_BTCUSDT.csv`, `upbit_KRW-BTC.csv`)는 열지도, 읽지도, 해시하지도 않았다.
- 기준값 도구: `QuantLib 1.44`, `arch 8.0.0`을 PyPI에서 받아 스크래치 폴더(`.../audit_work/financial_calcs/refpkgs`)에만 설치했다. 전역 python과 저장소는 바꾸지 않았다. 실행은 전역 `python3 -B`(Python 3.13.17, numpy 2.3.5, scipy 1.18.0)다. 웹은 PBO 기준 구현(pypbo의 `pbo.py`) 한 파일만 읽었다.
- `tests/run_all.py`는 실행하지 않았다. 모듈 자체 검사(`python3 -B -m core.ficc.fx` 등 11개)만 실행했다. 모두 `ok`였다(`r00_selfchecks.out`). 이 검사들은 파일을 쓰지 않는다.

## 0. 요약

1. **공식 자체는 대부분 맞다.** Garman–Kohlhagen(=배당 있는 Black–Scholes) 가격과 그릭스 7종이 5개 사례에서 QuantLib와 1e-13 안에서 같다. Black-76, Bachelier, SABR(Hagan), 내재변동성 역산, 채권 가격·듀레이션·볼록성(쿠폰일 결제), 곡선 부트스트랩(독립 전역해 대비 1.6e-15), 스왑 PV, 스왑션 ATM 닫힌식, 캡, Vasicek·CIR·Hull–White 할인채도 맞다(3장 표).
2. **GARCH(1,1)-t와 GJR-t의 로그우도는 같은 모수·같은 초기값에서 `arch` 패키지와 차이 0이다.** 최적화는 `arch`의 추정치보다 높거나 같은 우도를 찾았다. 다단계 분산 예측도 같다. Hansen skew-t 밀도도 같다(1.8e-15).
3. **몬테카를로의 위험중립 드리프트**는 4개 모형 모두 E[S_T]=S_0·e^{rT}를 MC 오차 안에서 만족한다(GARCH-t 10개 시드 합성 z=+0.01). **DSR**은 Bailey–López de Prado(2014) 수치 예제(E[max SR] 0.1132, DSR 0.9004)를 재현한다.
4. **문제는 공식보다 입력·관례·적용 범위에 있다.** 발견사항 16건(P1 2, P2 5, P3 9).
   - **FC-01 (P1)** CMS 스티프너 노트가 floor/cap을 변동성 0(내재가치)으로 평가한다. UI 기본 입력에서 공정가치가 100당 +2.80~+4.40 덜 나오고 마진이 그만큼 더 나온다(10y−2y 정규변동성 50~70bp/년 가정). 화면 경고는 반대 방향(쿠폰 과대)만 말한다.
   - **FC-02 (P1)** 짧은 첫 스텁에 1/freq 전체 발생 가중을 준다. 만기가 지급주기의 정수배가 아닌 스왑은 par 금리가 크게 틀린다(18m −97.2bp, 6m −207.5bp, 2.5y −63.9bp). 캡의 ATM 행사가, 스티프너·역전환사채 쿠폰도 영향을 받는다. 정수 만기(1y, 2y, 5y, 10y, 5y5y)는 영향이 없다.
   - **FC-03 (P2)** 채권 화면의 "Price (per 100)"는 실제로는 경과이자를 포함한 dirty 가격이다. 시장의 clean 호가를 넣으면 수익률이 +10.6~+11.5bp 틀린다.
   - **FC-04 (P2)** 구조화 화면은 모든 상품을 미국채 곡선으로 할인한다. 기본 USD/KRW 이중통화예금은 원화 금리 자리에 달러 금리를 쓴다. 화면의 "plain KRW deposit 3.60%"는 달러 금리다. 원화 2.6%를 가정하면 증강 수익률이 4.87%→4.10%(77bp)로 바뀐다.
   - **FC-05 (P2)** 스왑·스왑션·캡이 미국채 CMT 곡선을 스왑 곡선으로 쓴다. 화면의 "Par rate"는 SOFR OIS 시장 금리가 아니다. 스왑 스프레드가 빠진다.
   - **FC-06 (P2)** 파생상품 화면의 선물 베이시스가 배당점수를 0으로 둔다. 배당 5포인트(지수 400, 50일) 예에서 "−125bp cheap", "암시 조달금리 −6.33%"가 표시된다.
   - **FC-07 (P2)** PBO가 λ<0만 센다. 기준 구현(pypbo)은 λ≤0이다. 격자 수 G가 홀수면 PBO가 약 1/G 낮다(잡음 G=9: 0.405 vs 0.516).
5. **조기상환 조건 민감도는 검사할 수 없다.** 조기상환형(오토콜·배리어) 상품이 코드에 없다(FC-16). README도 그런 상품을 주장하지 않는다.
6. **실시장 입력의 정확성은 검증하지 않았다.** FRED 곡선, KIS 옵션 보드와 IV, KIS 이론가의 배당 규칙은 네트워크 없이 확인할 수 없다(6장 미검증).
7. 근거 없이 정확성을 인증하지 않는다. "일치"는 3장에 적은 입력 범위와 관례 안에서만 성립한다.

## 1. 범위

- 가격·위험 공식: `core/ficc/fx.py`, `core/ficc/equity_deriv.py`, `core/ficc/swaps.py`, `core/ficc/bonds.py`, `core/ficc/curves.py`, `core/ficc/curve_models.py`, `core/ficc/ratesim.py`(닫힌식 할인채만), `core/ficc/structured.py`, `core/ficc/vol_products.py`.
- 통계·시뮬레이션: `core/quant/garch.py`, `core/quant/gjr.py`, `core/quant/montecarlo.py`, `core/quant/validate.py`(Sharpe, Lo SE, DSR, PBO; Kupiec·Christoffersen·PIT은 코드 읽기만).
- 이 공식을 부르는 화면의 입력·단위: `ui/bonds_page.py`, `ui/rates_page.py`, `ui/fx_page.py`, `ui/structuring_page.py`, `ui/derivatives_page.py`, `ui/fcharts.py`.
- 참고: `vol_products.py`에는 Black–Scholes류 가격 공식이 없다. VIX 기간구조 비율과 휴리스틱(−b/2)만 있다. 공식 검증 대상이 아니다(6장).
- 제외: `paper_live/`, `grokteam/`(열지도 실행하지도 않았다). `risk_layer`, `gate_stats`의 카드 통계, `forecast_eval`, `vol_estimators`는 다른 차원이다.

## 2. 방법

1. 각 함수의 공식, 단위, 가정을 코드에서 읽고 파일:라인으로 기록했다.
2. 기준값은 세 종류다. (a) 교과서 닫힌식 예제(Hull의 Black–Scholes 예: S=42, K=40, r=10%, σ=20%, T=0.5 → 콜 4.76, 풋 0.81; Black-76 선물옵션 예: F=K=20, r=9%, T=4/12, σ=25% → 풋 1.12). (b) QuantLib·`arch`의 독립 구현. (c) 이 감사에서 직접 쓴 독립 구현(예: 부트스트랩을 순차 brentq 대신 한 번의 다변수 근 찾기로 풀었다. 스왑 다리를 현금흐름 루프로 직접 합했다).
3. 구조화 상품은 해석 가능한 극한(변동성→0, 행사가 아주 낮음, 마진 0)과 독립 BS 가격으로 맞춰 보았다. 곡선(±100bp), 변동성, 배당(외국 금리), 행사가 민감도의 부호를 확인했다.
4. 차이가 나면 원인을 분리했다(정의 차이인지, 관례 차이인지, 결함인지).
5. 판정 기준: 재현했으면 **사실**. 코드로 확인했지만 크기가 외부 시장 데이터에 달렸으면 그 부분을 **추정**. 주장과 코드가 다르면 **오류**. 확인 못 했으면 **미검증**.

## 3. 공식별 검증표

단위 표기: 금리·변동성은 소수(0.05=5%). T는 연(ACT/365F 실수). "차이"는 코드값 − 기준값.

| # | 항목 | 코드 위치 | 공식 | 단위·가정 | 기준값 | 측정 차이 | 판정 |
|---|---|---|---|---|---|---|---|
| 1 | GK(=BS, q=r_for) 가격 | `core/ficc/fx.py:126-147` | S·e^{−r_f T}N(d1) − K·e^{−r_d T}N(d2) | 연속복리 평탄 금리·평탄 변동성 | QuantLib `AnalyticEuropeanEngine`(GBSM) 5사례; Hull 예 4.76/0.81; 손계산 1사례 | 최대 1.7e-13(가격 1350 규모) | 사실(일치) |
| 2 | GK 그릭스 | `fx.py:137-147` | delta e^{−r_f T}N(±d1); gamma; vega·0.01; theta/365; rho_d, rho_f; vanna −e^{−r_fT}φ(d1)d2/σ; volga vega·d1d2/σ | vega는 1 vol-pt당, theta는 달력일당, rho는 금리 1.00당 | QuantLib delta·gamma·vega·theta·rho·dividendRho; vanna·volga는 QuantLib vega의 유한차분 | ≤5e-13; vanna·volga 상대 ≤1e-6(유한차분 오차) | 사실 |
| 3 | 내재변동성 역산(GK, Black, normal) | `fx.py:150-165`, `swaps.py:256-282` | brentq [1e-4, 5], [1e-6, 0.5] | 무차익 경계 밖은 오류 | 왕복 | ≤5e-14 | 사실 |
| 4 | Black-76 | `swaps.py:208-230` | df·(F N(d1) − K N(d2)) | 연금(annuity)·명목 1당 | QuantLib `blackFormula`; Hull 선물옵션 예 1.12 | 0~6e-14 | 사실 |
| 5 | Bachelier | `swaps.py:233-253` | df·[(F−K)N(d)+σ√Tφ(d)] | nvol 소수(0.008=80bp/년), 음수 F 허용 | QuantLib `bachelierBlackFormula` | ≤9e-19 | 사실 |
| 6 | SABR(Hagan 2002) | `fx.py:217-236` | lognormal 전개 | β 고정 | QuantLib `sabrVolatility` 5사례(β=1, 0.5) | ≤6e-17 | 사실 |
| 7 | 델타→행사가 | `fx.py:168-179` | K=F·exp(∓N⁻¹(abs(δ)·e^{r_fT})σ√T+½σ²T) | spot delta, 프리미엄 미조정 | delta 방정식을 brentq로 직접 풂 | 2e-16 | 사실(관례는 FC-11) |
| 8 | 채권 가격·Macaulay·수정 듀레이션·볼록성(쿠폰일 결제) | `bonds.py:80-134` | Σcf(1+y/f)^{−t·f}; Σt·PV/P; /(1+y/f); Σt(t+1/f)PV/((1+y/f)²P) | 100당, street 관례 | QuantLib `FixedRateBond`(30/360, 반기 복리), 10y 5% y=6% | 가격 5.7e-14, Mac·Mod 2.7e-15, 볼록성 4.3e-14 | 사실 |
| 9 | DV01 | `bonds.py:137-141` | ModD·P/face·N·1bp | 1차 근사 | QuantLib `basisPointValue`(2차 항 포함) | 100당 +3.3e-5 = ½·Cvx·P·1e-8 | 사실(정의 차이, 결함 아님) |
| 10 | 채권, 쿠폰일이 아닌 결제 | `bonds.py:80-99` | 위와 같음 | 결제일·경과이자 없음 | QuantLib dirty/clean | 코드 가격 = QuantLib dirty(차이 0) | 사실 → FC-03 |
| 11 | KRD 합 vs DV01 | `bonds.py:144-157` | 삼각 bump, zero 이동 | 문서: 비율 1+y/f | 평탄 곡선 | 비율 1.025000 = 1+0.05/2 | 사실(문서와 일치) |
| 12 | 부트스트랩 | `curves.py:165-201` | 1y 미만 DF=1/(1+yt); 1y 이상 반기 par 채권 | ACT/365F, 로그선형 DF | 독립 전역해(fsolve) | zero 최대 1.55e-15, DF 3.4e-15 | 사실 |
| 13 | 보간 | `curves.py:77-89` | z·t 선형 = 구간별 상수 포워드, 양끝 평탄 zero | — | 독립 구현 | 위와 같음. 3m 포워드의 인접 점프 최대 73.9bp는 이 보간의 성질 | 사실 |
| 14 | 스왑 PV·par | `swaps.py:83-100` | N(DF_s−DF_e) − N·K·A | 단일 곡선 | 현금흐름 루프 | PV 9.3e-10(1천만 기준), par 일치 | 사실(정수 만기). 스텁은 FC-02 |
| 15 | 스왑션 | `swaps.py:340-365` | N·A·opt(F,K,T) | A는 오늘로 할인 | ATM 닫힌식 N·A·σ√T/√(2π); QuantLib | 0 | 사실 |
| 16 | 캡 | `swaps.py:382-410` | Σ N·τ·DF(t1)·opt(fwd,K,t0) | 첫 캡렛 제외 | 캡렛별 QuantLib `blackFormula` 합 | 0 | 사실(ATM 행사가는 FC-02) |
| 17 | Vasicek·CIR·HW 할인채 | `ratesim.py:161-194` | 아핀 닫힌식 | HW는 곡선 필요 | QuantLib `Vasicek`, `CoxIngersollRoss`, `HullWhite` `discountBond` 9사례 | ≤6.5e-12 | 사실 |
| 18 | Diebold–Li 적재 | `curve_models.py:35-45` | λ=0.0609/월 = 0.7308/년 | — | 곡률 적재 최대점 ≈30개월 | 29.44개월 | 사실 |
| 19 | GARCH-t 로그우도 | `garch.py:189-212` | 단위분산 t 밀도 | 일간, μ=표본평균 고정, σ²₁=표본분산 | `arch` 같은 모수·같은 σ²₁ | 0.0 | 사실 |
| 20 | GARCH 추정 | `garch.py:222-264` | L-BFGS-B, 3개 시작점 | — | `arch` MLE 모수를 코드 우도로 평가 | 코드 최대 8326.781342 ≥ 8326.777756 | 사실 |
| 21 | GARCH 예측 | `garch.py:558-571` | ω+(α+β)σ² | — | `arch` 재귀 | 상대 3.3e-16 | 사실 |
| 22 | GJR-t 로그우도·추정 | `gjr.py:113-183` | (α+γ1{ε<0})ε² | — | `arch` o=1 | 우도 차 0.0; 코드 최대 ≥ `arch` 해 | 사실(지속성은 FC-08) |
| 23 | Hansen skew-t 밀도 | `gjr.py:44-55` | Hansen(1994) | — | `arch` `SkewStudent` | ≤1.8e-15 | 사실 |
| 24 | MC 위험중립 드리프트 | `montecarlo.py:229-298` | rate − c_t, c_t=ln E[exp(shock)] | 모형별 정확 보정 | E[S_T]/S_0 = e^{rT} | z: GBM +0.25, jump +0.48, bootstrap −0.26, GARCH-t +1.75(10시드 합성 +0.01) | 사실 |
| 25 | MC VaR·CVaR(GBM) | `montecarlo.py:310-313` | 경험 분위·꼬리 평균 | — | 로그정규 닫힌식 | VaR 26.33% vs 26.37%, CVaR 31.67% vs 31.72%(MC 오차) | 사실 |
| 26 | Sharpe, Lo SE | `validate.py:137-153` | mean/sd·√252; √((1+½SR²)/T)·√252 | iid | 직접 계산 | 0 | 사실 |
| 27 | DSR | `validate.py:211-237` | Φ((SR−SR₀)√(T−1)/√(1−γ₃SR+(γ₄−1)/4·SR²)) | 기간 단위 SR, γ₄는 비초과 첨도 | BLdP 2014 수치 예(N=100, SR 2.5, T=1250, V=0.5, γ₃=−3, γ₄=10) | E[max SR] 0.1132, DSR 0.9004 | 사실 |
| 28 | PBO(CSCV) | `validate.py:240-265` | rank/(G+1)의 logit | λ<0 | pypbo(λ≤0) | 홀수 G에서 차이 | 사실 → FC-07 |
| 29 | LETF 드래그 | `equity_deriv.py:548-559` | (β−β²)/2·Σσ²Δ + ((1−β)r−f)T | — | 일일 리밸런싱 시뮬레이션 2만 경로 | β=+2: −0.06249 vs −0.06250; β=−2: −0.18757 vs −0.18750 | 사실 |
| 30 | 모형무관 분산(MFIV) | `equity_deriv.py:333-389` | Cboe 스트립 | — | 평탄 20% 보드 | 행사가 간격 2.5: +0.3bp, 5: +1.0bp, 25: +24.9bp | 사실(이산화 오차는 간격에 비례) |
| 31 | Cboe 30일 보간, 박스 금리, 패리티 잔차 | `equity_deriv.py:392-399, 432-443, 196-209` | 문헌 식 | — | 코드 읽기 + 자체 검사 | — | 사실(코드 읽기) |
| 32 | PPN 참여율 | `structured.py:144-193` | (issue−margin−100·DF)/(100·C/S) | — | 독립 BS | 0 | 사실 |
| 33 | 역전환사채 쿠폰 | `structured.py:196-248` | (issue−margin+put−100DF)/(100A) | — | 독립 BS; 옵션 없는 극한 = 1y 연간 par | 0; 3.83706853% = 3.83706853% | 사실(정수 만기) |
| 34 | 구조화 민감도 부호 | `structured.py` | — | — | 기대 부호 | PPN: vol 20→25% 참여율 0.672→0.562, 배당 2→3% 0.672→0.756, 곡선 −100/+100bp 0.545/0.773. RC: vol 25→35% 쿠폰 9.92→13.89%, 배당 2→4% 9.92→10.68%, 행사가 95→85% 9.92→6.56% | 사실(모두 기대 부호) |
| 35 | CMS 스티프너 | `structured.py:311-380` | 포워드 스프레드의 clip | 변동성 0 | Bachelier 스프레드 옵션 | +2.80~+4.40/100 | 사실 → FC-01 |

## 4. 발견사항

### 4.1 요약 표

| ID | 심각도 | 판정 | 위치 | 한 줄 요약 |
|---|---|---|---|---|
| FC-01 | P1 | 사실(크기는 추정) | `core/ficc/structured.py:311-380` | 스티프너 floor/cap을 내재가치로 평가. 공정가치 −2.8~−4.4/100 |
| FC-02 | P1 | 사실 | `core/ficc/curves.py:41-48,110-116` | 짧은 스텁에 전체 발생 가중. 18m 스왑 par −97bp |
| FC-03 | P2 | 사실 | `core/ficc/bonds.py:80-99`, `ui/bonds_page.py:69,112` | "Price"가 dirty. clean 호가 입력 시 +10.6~11.5bp |
| FC-04 | P2 | 사실(KRW 금리 수준은 가정) | `ui/structuring_page.py:11-12,50-53,269-271` | KRW 상품을 미국채 곡선으로. 증강 수익률 +77bp |
| FC-05 | P2 | 사실(스프레드 크기 미검증) | `ui/rates_page.py:95-96,155-178` | 미국채 곡선을 스왑 곡선으로. par는 SOFR 금리가 아님 |
| FC-06 | P2 | 사실(배당 크기 추정) | `ui/derivatives_page.py:121-122,149-151,240-241` | 선물 베이시스에 배당 0 |
| FC-07 | P2 | 사실 | `core/quant/validate.py:264`, `core/quant/gate_stats.py:723` | PBO가 λ<0만 셈. 홀수 G에서 ≈1/G 과소 |
| FC-08 | P3 | 사실 | `core/quant/gjr.py:115,176` | skew-t에서도 지속성에 γ/2 사용 |
| FC-09 | P3 | 사실 | `core/quant/garch.py:478-482,548` | AIC 모수 수에 μ 빠짐. GBM 대비 ΔAIC +2 유리 |
| FC-10 | P3 | 사실 | `core/quant/montecarlo.py:144-163` | 점프 = 한 번의 정규 × 횟수(머튼과 다름) |
| FC-11 | P3 | 사실(시장 관례는 추정) | `core/ficc/common.py:25-39` 외 | 캘린더·영업일·결제일 없음, FX 델타·단기금리 관례 단순화 |
| FC-12 | P3 | 사실 | `core/ficc/swaps.py:200-205`, `core/ficc/equity_deriv.py:491` | 만기 시 d1 부호 반대, 죽은 조건식 |
| FC-13 | P3 | 사실 | `core/ficc/equity_deriv.py:55-59,85` | `implied_repo`가 관례 인자를 무시 |
| FC-14 | P3 | 사실 | `core/ficc/fx.py:432-443` | 캐리 백테스트 "Sharpe" = CAGR/vol |
| FC-15 | P3 | 사실 | `tests/ficc_acceptance.py`, `tests/quant_acceptance.py` | 테스트가 독립 기준값을 거의 고정하지 않음 |
| FC-16 | P3 | 사실 | `core/ficc/structured.py` 전체 | 조기상환형 상품 없음, 이산 배당 없음 |

### 4.2 상세

#### FC-01 · P1 · 사실(크기는 추정) — CMS 스티프너의 floor/cap 옵션 가치가 빠졌다

| 항목 | 내용 |
|---|---|
| ID | FC-01 |
| 심각도 | P1 (화면의 핵심 수치인 공정가치·마진이 기본 입력에서 크게 틀린다) |
| 판정 | 사실: floor/cap을 포워드 스프레드의 내재가치로만 평가한다(코드). 추정: 오차 크기는 스프레드 변동성 가정(50~70bp/년)에 달렸다 |
| 파일·함수·라인 | `core/ficc/structured.py:311-325` `_cms_coupons` (`cpn = max(leverage * spread, floor)`, `min(cpn, cap)`), `:328-380` `steepener_note`, 경고 문구 `:372-374`. UI 기본값 `ui/structuring_page.py:53-55`(레버리지 4, floor 0, cap 없음, 5y, 연 1회) |
| 재현 단계 | `python3 -B .../financial_calcs/r07_structured.py` 4번. 모듈 자체 검사의 par 곡선, 레버리지 4, floor 0, cap 없음, 5y. 각 쿠폰을 Bachelier로 E[max(4S,0)]=4·[F·N(F/sd)+sd·φ(F/sd)], sd=σ_n√t0로 다시 평가 |
| 기대 결과 | floor는 보유자가 산 옵션이다. 미래에 정해지는 쿠폰(t0>0)은 시간가치를 가져야 한다. 공정가치에 그 가치가 들어가야 한다 |
| 실제 결과 | 코드 공정가치 86.1175. σ_n=50bp/년이면 88.9214(+2.8039), 70bp/년이면 90.5155(+4.3980). 포워드 스프레드 +51.0, +37.9, +25.1, +16.1, +17.1bp로 floor에 가깝다. 화면 경고는 "CMS 볼록성 조정이 없어 쿠폰이 과대"라고만 말한다. 실제 순효과는 반대 방향이다 |
| 영향 | "Margin (per 100)"이 2.8~4.4포인트 과대. 판매사 마진 판단, 상품 비교, AI 해설 페이로드가 모두 이 숫자를 쓴다. cap이 있으면 cap의 시간가치도 빠져 반대 방향 오차가 섞인다 |
| 수정안 | 아래 diff. 스프레드 정규변동성 입력(`spread_nvol`)을 받아 floorlet·caplet을 Bachelier로 평가한다. UI에 "Spread normal vol (bp)" 칸을 추가하고, 비우면 지금처럼 내재가치로 평가하되 화면에 "floor/cap 시간가치 제외"를 표시한다. 경고 문구를 "볼록성 조정 없음 + floor/cap 시간가치 포함(가정 vol X bp)"로 바꾼다 |
| 회귀 테스트 | `ficc/test_steepener_floor_has_time_value`: 자체 검사 곡선, 5y, L=4, floor 0. `fv(nvol=0.005) − fv(nvol=None)`가 2.8039±0.01이고 >0. `nvol=1e-12`이면 내재가치 결과와 1e-9 안에서 같다. cap 2%를 넣으면 nvol 증가에 따라 cap 쪽 가치가 줄어든다(부호 검사) |

```diff
--- a/core/ficc/structured.py
+++ b/core/ficc/structured.py
@@ -49,7 +49,7 @@
 from core.ficc.bonds import Bond, cashflows, price_from_curve
 from core.ficc.common import BP, FICCError, tenor_label
 from core.ficc.curves import YieldCurve, coupon_times
 from core.ficc.fx import garman_kohlhagen
-from core.ficc.swaps import Swap, par_swap_rate, swap_dv01
+from core.ficc.swaps import Swap, bachelier, par_swap_rate, swap_dv01
@@ -311,15 +311,27 @@
 def _cms_coupons(curve: YieldCurve, T: float, freq: int, leverage: float, floor: float,
-                 cap: float | None) -> list[tuple[float, float, float, float]]:
+                 cap: float | None, spread_nvol: float | None = None
+                 ) -> list[tuple[float, float, float, float]]:
     """(t_start, t_end, forward 10y−2y spread, coupon) per period, spread fixed at
-    t_start off the forward curve."""
+    t_start off the forward curve. With `spread_nvol` (normal vol of the spread,
+    decimal per year) a coupon fixing at t_start > 0 is E[clip(L·S, floor, cap)],
+    S ~ N(fwd, nvol²·t_start) = L·fwd + L·put(floor/L) − L·call(cap/L), undiscounted
+    Bachelier. None keeps the intrinsic (zero-vol) value."""
     ends = coupon_times(T, freq)
     starts = [0.0] + [float(t) for t in ends[:-1]]
     rows = []
     for t0, t1 in zip(starts, ends):
         spread = (par_swap_rate(curve, 10.0, freq=1, start=t0)
                   - par_swap_rate(curve, 2.0, freq=1, start=t0))
-        cpn = max(leverage * spread, floor)
-        if cap is not None:
-            cpn = min(cpn, cap)
+        if spread_nvol and t0 > 0:
+            cpn = leverage * (spread + bachelier(spread, floor / leverage, t0, spread_nvol,
+                                                 1.0, call=False).price)
+            if cap is not None:
+                cpn -= leverage * bachelier(spread, cap / leverage, t0, spread_nvol, 1.0).price
+        else:
+            cpn = max(leverage * spread, floor)
+            if cap is not None:
+                cpn = min(cpn, cap)
         rows.append((t0, float(t1), spread, cpn))
     return rows
```

`steepener_note`에 `spread_nvol: float | None = None`을 추가하고 `_cms_coupons` 두 호출(`:341`, `:344`)에 넘긴다. `ui/structuring_page.py:53-55`의 `"steep"` 필드에 `("nvol", "Spread normal vol (bp)", "", 170)`을 추가하고 `_price`에서 bp→소수로 바꿔 넘긴다.

#### FC-02 · P1 · 사실 — 짧은 첫 스텁이 1/freq 전체를 발생시킨다

| 항목 | 내용 |
|---|---|
| ID | FC-02 |
| 심각도 | P1 (스왑 가격기가 받는 입력에서 par 금리가 수십~수백 bp 틀린다) |
| 판정 | 사실 |
| 파일·함수·라인 | `core/ficc/curves.py:41-48` `coupon_times`(T − k/freq), `:110-112` `annuity`(Σ DF/freq), `:114-116` `par_rate`. 문서 `curves.py:19-20`("a short first stub still carries a full 1/freq weight"). 사용처 `core/ficc/swaps.py:78-85`, `:346`, `:392`; `core/ficc/ratesim.py:340,370`; `core/ficc/structured.py:213`(RC), `:345`(스티프너 `cpn / freq`). UI 입력 `ui/rates_page.py:158-163`, `:379`("10y or 5y5y" 힌트, 아무 테너 허용). 개발자도 곡선 차트에서 이 톱니를 피해 갔다: `ui/fcharts.py:71-76` |
| 재현 단계 | `python3 -B .../financial_calcs/r09_stub_periods.py`. 같은 곡선에서 코드 par와 "스텁은 자기 길이만 발생" par 비교 |
| 기대 결과 | 새로 시작하는 스왑의 첫 짧은 기간은 그 길이(t1−start)만큼만 고정이자가 발생한다. par 금리는 만기 0.5년 단위로 매끄럽게 변한다 |
| 실제 결과 | 연 1회 스왑 par: 3m 1.0625% vs 4.2500%(−318.7bp), 6m 2.0750% vs 4.1500%(−207.5bp), 18m 2.8467% vs 3.8184%(−97.2bp), 2.5y −63.9bp, 5.25y −51.0bp, 7.5y −27.5bp. 1y·2y·5y·10y는 0bp. 올바른 par 3.8184%의 18m 지급 스왑이 PV −187,041(1천만당)로 나온다. 1.6y 분기 캡의 "ATM" 행사가가 3.4276%인데 캡렛은 자기 길이만 발생하므로 실제 par 3.7591%와 어긋난다. 18m 역전환사채는 0.5년 뒤 연 쿠폰 6.758% 전액을 준다(반년 기준 연율 13.5%) |
| 영향 | 비정수 테너 스왑·포워드 스왑·스왑션(F, A 모두)·캡 ATM 행사가가 틀린다. 시나리오 재평가(`ratesim.horizon_pv_distribution`)도 같은 연금을 쓴다. 정수 테너 기본값(10y, 5y)만 쓰면 드러나지 않는다 |
| 수정안 | 아래 diff. 연금에 스텁 발생 길이를 쓴다. 채권 쿠폰은 실제로 전액 지급되므로 `bonds.cashflows`와 부트스트랩(`curves.py:187-191`)은 그대로 둔다. RC는 채권 관례를 명시해 `curve.annuity` 대신 Σ DF를 쓰거나, 비정수 만기를 거부한다. 스티프너는 `cpn / freq` 대신 `cpn * (t1 − t0)` |
| 회귀 테스트 | `ficc/test_swap_par_rate_accrues_the_stub_only`: 자체 검사 곡선에서 `par_swap_rate(c, 1.5)`가 `(1−DF(1.5))/(0.5·DF(0.5)+DF(1.5))`와 1e-12 안에서 같다. 그 금리의 18m 스왑 PV가 1e-6 안에서 0. 10y par는 4.01935877%로 변하지 않는다(r03의 곡선). 기존 `test_curve_bootstrap_round_trips_par_inputs`는 그대로 통과해야 한다 |

```diff
--- a/core/ficc/curves.py
+++ b/core/ficc/curves.py
@@ -110,7 +110,13 @@ class YieldCurve:
     def annuity(self, maturity: float, freq: int = 2, start: float = 0.0) -> float:
-        """Σ DF(t_i)/freq over coupon dates in (start, T]."""
-        return float(np.sum(self.df(coupon_times(maturity, freq, start))) / freq)
+        """Σ τ_i·DF(t_i) over coupon dates in (start, T]: τ_i = 1/freq, except a
+        short first stub, which accrues only its own length t_1 − start. (A
+        seasoned bond's full first coupon lives in `bonds.cashflows`, not here.)"""
+        ts = coupon_times(maturity, freq, start)
+        tau = np.diff(np.concatenate([[start], ts]))
+        return float(np.sum(tau * self.df(ts)))
--- a/core/ficc/structured.py
+++ b/core/ficc/structured.py
@@ -213 +213,2 @@
-    ann, df = curve.annuity(T, 1), float(curve.df(T))
+    # bond convention: a full coupon on every date (the Bond below pays exactly that)
+    ann, df = sum(float(curve.df(t)) for t in coupon_times(T, 1)), float(curve.df(T))
@@ -345 +346 @@
-        return 100.0 * c.df(T) + sum(100.0 * cpn / freq * c.df(t1) for _, t1, _, cpn in cpns)
+        return 100.0 * c.df(T) + sum(100.0 * cpn * (t1 - t0) * c.df(t1) for t0, t1, _, cpn in cpns)
```

#### FC-03 · P2 · 사실 — 채권 화면의 "Price"는 dirty 가격이다

| 항목 | 내용 |
|---|---|
| ID | FC-03 |
| 심각도 | P2 |
| 판정 | 사실 |
| 파일·함수·라인 | `core/ficc/bonds.py:80-84` `_pv_terms`, `:87-89` `price_from_yield`, `:92-99` `yield_from_price`(현금흐름 전부의 현재가치 = dirty). 문서 `bonds.py:12-14`("no accrued interest … clean-ish"). UI 라벨 `ui/bonds_page.py:69` `"Price (per 100)"`, 호출 `:112`. 화면·README 어디에도 dirty라는 말이 없다 |
| 재현 단계 | `python3 -B .../financial_calcs/r02_bonds.py` 2·3번. 4% 반기 채권, 잔존 7년 4개월. QuantLib 30/360으로 같은 시간 격자를 만들어 dirty·clean 계산. UST 4.5% 2036-02-15, 거래 2026-10-27(T+1), ACT/ACT ICMA |
| 기대 결과 | 화면에 시장 호가(clean)를 넣으면 같은 수익률이 나와야 한다. 또는 라벨이 dirty라고 말해야 한다 |
| 실제 결과 | 코드 가격 = QuantLib dirty(100.662271, 차이 0). clean 99.995604를 넣으면 수익률 4.106187%(참 4.0000%, +10.6bp). y=5%에서 +11.4bp. 실제 UST 예에서 clean 99.9921을 넣으면 4.61451%(참 4.5%, +11.5bp). 같은 수익률에서 코드 가격과 QuantLib dirty의 차이 −0.046/100은 일수 관례·결제일 차이다(FC-11) |
| 영향 | 수익률, 듀레이션, DV01, z-spread, 캐리·롤다운, 시나리오 손익이 모두 틀린 수익률에서 계산된다. 오차 ≈ 경과이자/(ModD·P) |
| 수정안 | 아래 diff. 경과이자 함수와 clean 입력 경로를 추가한다. UI 라벨을 "Clean price (per 100)"로 바꾸고 "Accrued", "Dirty" 통계를 보인다. 기존 `price=`는 dirty 의미로 유지해 기존 테스트를 깨지 않는다 |
| 회귀 테스트 | `ficc/test_bond_clean_quote_off_cycle`: `Bond(0.04, 7+4/12, 2)`의 `accrued_interest`가 0.666667±1e-6. `analyze_bond(b, clean_price=99.995604).ytm`이 0.04±1e-6(QuantLib 기준값). `ui/bonds_page.py` 자체 검사의 라벨 조회(`:288`)도 새 라벨로 바꾼다 |

```diff
--- a/core/ficc/bonds.py
+++ b/core/ficc/bonds.py
@@ -72,6 +72,20 @@ def cashflows(bond: Bond) -> tuple[np.ndarray, np.ndarray]:
     cf[-1] += bond.face
     return t, cf
 
 
+def accrued_interest(bond: Bond) -> float:
+    """Coupon accrued in the running period, per `face`. The schedule is
+    t_i = T − k/freq, so that period began at t_1 − 1/freq (<= 0)."""
+    t1 = float(cashflow_times(bond)[0])
+    return bond.coupon * bond.face * max(0.0, 1.0 / bond.freq - t1)
+
+
+def dirty_from_clean(bond: Bond, clean: float) -> float:
+    """Every price in this module is the dirty (full) price; quotes are clean."""
+    return clean + accrued_interest(bond)
+
+
 def _check_ytm(bond: Bond, ytm: float) -> None:
@@ -231,8 +245,14 @@
 def analyze_bond(bond: Bond, *, price: float | None = None, ytm: float | None = None,
-                 curve: YieldCurve | None = None, horizon: float = 0.25) -> BondAnalytics:
+                 curve: YieldCurve | None = None, horizon: float = 0.25,
+                 clean_price: float | None = None) -> BondAnalytics:
@@
-    if (price is None) == (ytm is None):
+    if clean_price is not None:
+        if price is not None:
+            raise ValueError("Give the dirty price or the clean price, not both.")
+        price = dirty_from_clean(bond, clean_price)
+    if (price is None) == (ytm is None):
         raise ValueError("Give exactly one of price or ytm.")
--- a/ui/bonds_page.py
+++ b/ui/bonds_page.py
@@ -69 +69 @@
-    price = ft.TextField(label="Price (per 100)", width=140, hint_text="blank = from yield",
+    price = ft.TextField(label="Clean price (per 100)", width=160, hint_text="blank = from yield",
@@ -112 +112 @@
-                a = analyze_bond(bond, price=_num(price), ytm=None if y is None else y / 100.0,
+                a = analyze_bond(bond, clean_price=_num(price), ytm=None if y is None else y / 100.0,
```

#### FC-04 · P2 · 사실 — 구조화 화면이 원화 상품을 미국채 곡선으로 할인한다

| 항목 | 내용 |
|---|---|
| ID | FC-04 |
| 심각도 | P2 |
| 판정 | 사실. 원화 금리 수준(2.6%)은 비교용 가정이다(추정) |
| 파일·함수·라인 | `ui/structuring_page.py:11-12`(모듈 문서에만 "KRW DCD는 UST 곡선으로 할인, KRW 호가 아님"), `:49-51`(DCD 기본값 USD/KRW 1350, K 1300), `:269-271`(항상 `load_treasury_curve`), `_render :136-141`(합성 곡선 경고만 있음). `core/ficc/structured.py:266-268`(`dep_rate`), `:288-290`·`:296-299`("plain KRW deposit" 문구) |
| 재현 단계 | `python3 -B .../financial_calcs/r07_structured.py` 3번. UI 기본 입력으로 (a) 미국채형 곡선, (b) 원화 평탄 2.6% 곡선 비교 |
| 기대 결과 | 원화 다리는 원화 곡선으로 할인한다. 아니면 화면이 "원화 금리 아님"을 말한다 |
| 실제 결과 | (a) 증강 수익률 4.8683%, "plain KRW deposit" 3.6000%(실제로는 미국 금리), 포워드 1346.91. (b) 4.0980%, 2.6085%, 1343.60. 증강 수익률 차이 77bp. 화면에는 통화 불일치 경고가 없다 |
| 영향 | KRW 이중통화예금의 수익률·마진·풋 가치·헤지 규모가 틀린다. 원화로 표시된 금리가 달러 금리다. EQ 기초자산(예: KOSPI200)을 고르면 같은 문제가 생긴다 |
| 수정안 | 1단계(최소): 아래 diff로 통화가 USD가 아니면 경고를 띄운다. 2단계: 호가 통화별 곡선을 쓴다. KRW는 이미 있는 `core/ficc/curve_models.py:242-257` `krw_curve_panel`(KIS CD91+국고채)을 연결하고, KIS가 없으면 계산을 거부하거나 경고와 함께 사용자 입력 금리를 쓴다 |
| 회귀 테스트 | `ui/test_structuring_non_usd_leg_is_flagged`: DCD USD/KRW 렌더 결과에 "discounted on the US Treasury curve" 문구가 있다. 2단계 후: KRW 평탄 2.6% 곡선을 주입하면 증강 수익률 4.0980%±1e-4 |

```diff
--- a/ui/structuring_page.py
+++ b/ui/structuring_page.py
@@ -139,6 +139,12 @@ def _render(page, tool, r, panel, curve):
     if synthetic:
         blocks.append(notice("Synthetic data: " + (panel.note or "simulated curve panel."),
                              "error", icon=ft.Icons.SCIENCE_OUTLINED))
+    if r.currency != "USD":
+        blocks.append(notice(
+            f"The {r.currency} leg is discounted on the US Treasury curve ({panel.source}): every "
+            f"rate labelled {r.currency} on this card is a USD rate. Mechanics only, not a "
+            f"{r.currency} quote.", "warning", icon=ft.Icons.WARNING_AMBER_ROUNDED))
```

#### FC-05 · P2 · 사실(스프레드 크기 미검증) — 스왑·스왑션·캡이 미국채 곡선을 스왑 곡선으로 쓴다

| 항목 | 내용 |
|---|---|
| ID | FC-05 |
| 심각도 | P2 |
| 판정 | 사실: 곡선 출처는 FRED DGS(미국채 CMT)뿐이다. 미검증: 실제 SOFR 스왑 스프레드 크기(이 환경에서 시장 데이터를 받을 수 없다) |
| 파일·함수·라인 | `core/ficc/data.py:67-68`(`_TREASURY_IDS`), `:552`. `ui/rates_page.py:95-96`(`_curve`), `:155-178`(`_run_swap`: "Par rate", 칩 `1/yr both legs`). `core/ficc/swaps.py:12-16`("Default freq=1 mirrors SOFR OIS annual/annual") |
| 재현 단계 | 코드 읽기. `r03_curves_swaps.py` 2번: 미국채 반기 par 3.98%(10y)에서 연 1회 "스왑" par 4.019% |
| 기대 결과 | SOFR OIS 스왑은 SOFR OIS 곡선으로 평가한다. 아니면 화면이 "미국채 곡선 대용, 스왑 스프레드 없음"이라고 말한다 |
| 실제 결과 | 화면의 "Par rate"는 미국채 곡선에서 나온 연 1회 금리다. 칩은 "curve FRED"만 보인다. 스왑 스프레드(SOFR 스왑 − 미국채)는 반영되지 않는다 |
| 영향 | par 금리, 오프마켓 스왑 PV, 포워드 스왑 금리, 스왑션 프리미엄의 기준 포워드가 시장과 스왑 스프레드만큼 다르다. DV01·KRD의 모양은 거의 같다 |
| 수정안 | 1단계: 칩 `chip("UST curve as swap curve: no swap spread", "warning")`을 `_run_swap`, `_run_option`에 추가하고 README "Swap pricer" 행에 같은 말을 쓴다. 2단계: SOFR OIS 곡선 공급자가 필요하다(5장). 들어오면 `YieldCurve`를 바꿔 끼우면 된다(README "OIS-discounting upgrade slots in behind `YieldCurve`") |
| 회귀 테스트 | `ui/test_rates_swap_names_its_curve`: 스왑 결과 칩에 "no swap spread" 문구가 있다 |

#### FC-06 · P2 · 사실(배당 크기 추정) — 선물 베이시스의 rich/cheap 판정이 배당을 빼고 계산된다

| 항목 | 내용 |
|---|---|
| ID | FC-06 |
| 심각도 | P2 |
| 판정 | 사실: `div_pts` 없이 호출한다. 추정: 실제 KOSPI200 배당점수 크기(만기월에 따라 다르다) |
| 파일·함수·라인 | `ui/derivatives_page.py:121-122`(`ED.basis_report(..., exchange_theo=...)`, `div_pts` 기본 0), 화면 통계 `:240-241`("Mispricing", 20bp 넘으면 빨강; "Implied funding"), 해설 `:149-151`. `core/ficc/equity_deriv.py:48-59, 81-87` |
| 재현 단계 | `python3 -B .../financial_calcs/r08_equity_deriv.py` 1번. S=400, CD 2.8%, 50일. 시장이 배당 5포인트를 반영한 선물 가격 |
| 기대 결과 | 배당을 반영한 공정가치 대비 0bp, 암시 조달금리 2.80% |
| 실제 결과 | 화면 경로: 공정가치 401.534, "−125.0bp cheap", 암시 조달금리 −6.325%. 배당 반영 시 0.0bp, 2.800%. 해설은 KIS 이론가와의 차이를 "the dividend-point convention"이라고만 쓰고 rich/cheap 판정은 그대로 둔다 |
| 영향 | 배당이 큰 만기에서 선물이 체계적으로 "cheap"으로, 암시 조달금리가 음수로 보인다. 빨간 표시가 뜬다 |
| 수정안 | KIS 이론가가 있으면 배당점수를 역산해 넣는다(아래 diff). 없으면 "dividends excluded" 칩을 띄우고 rich/cheap 문장을 생략한다. 역산 후에는 `theo_gap_pts`가 0이 되므로 해설 문장도 바꾼다 |
| 회귀 테스트 | `ficc/test_basis_with_dividend_points_is_fair`: `basis_report(400·(1+0.028·50/365)−5, 400, 0.028, 50/365, div_pts=5).mispricing_bp`가 0±1e-9, `implied_rate`가 0.028±1e-12. `ui/test_derivatives_basis_uses_theo_dividends`: 합성 보드에서 theo를 주면 Mispricing이 0bp 근처 |

```diff
--- a/ui/derivatives_page.py
+++ b/ui/derivatives_page.py
@@ -121,2 +121,7 @@
-    basis = ED.basis_report(fq["price"], fq["underlying_level"], rate, max(fq.get("days_left") or 1, 1) / 365.0,
-                            exchange_theo=fq.get("theo"))
+    tau = max(fq.get("days_left") or 1, 1) / 365.0
+    theo = fq.get("theo")
+    # KIS's theoretical price nets the expected dividend points: back them out at our rate so
+    # rich/cheap is read against a dividend-aware fair value (0 and a chip when no theo is served)
+    div_pts = max(fq["underlying_level"] * (1.0 + rate * tau) - theo, 0.0) if theo else 0.0
+    basis = ED.basis_report(fq["price"], fq["underlying_level"], rate, tau, div_pts=div_pts,
+                            exchange_theo=theo)
```

#### FC-07 · P2 · 사실 — PBO가 λ<0만 센다

| 항목 | 내용 |
|---|---|
| ID | FC-07 |
| 심각도 | P2 (게이트 지표) |
| 판정 | 사실 |
| 파일·함수·라인 | `core/quant/validate.py:257-264` `pbo_cscv`(`np.mean(logits < 0)`), `core/quant/gate_stats.py:719-723` `pbo_on_claim`(같은 관례, 문서 `:661`) |
| 재현 단계 | `python3 -B .../financial_calcs/r06b_pbo_ties.py`. 잡음 격자(1500×G)를 G마다 40개. 코드 PBO와 λ≤0 PBO 비교. `r06_validate.py` 3번(G=3 극단 예) |
| 기대 결과 | 기준 구현 pypbo(`pbo.py`: `phi = 1.0 if lam <= 0`)처럼 OOS 순위가 정확히 중앙(λ=0)인 경우를 과적합으로 센다. 잡음 격자에서 PBO≈0.5 |
| 실제 결과 | G=8(짝수) 차이 0. G=9: 평균 0.405 vs 0.516(차이 0.112), G=15: 0.484 vs 0.561, G=27: 0.414 vs 0.453. 잡음 격자 중 코드는 ≤0.20인데 기준은 >0.20인 비율: G=9 7%, G=15 3%, G=27 5% |
| 영향 | 홀수 격자에서 과적합 확률이 약 1/G 낮게 나온다. `pbo_max 0.05`, `pbo_reject 0.20` 경계 근처의 판정이 바뀔 수 있다. 다만 REJECT는 "승자가 OOS에서 지는 비율" 조건과 함께 읽으므로 영향이 줄어든다 |
| 수정안 | 두 곳의 `< 0`을 `<= 0`으로. `GATE`는 사전 등록 값이므로 소유자 승인과 재등록 절차를 따른다. 고정 기준값(QF3 잡음 레시피 0.535897, `test_t_pbo_01_noise_control_reproduces`, `test_pbo01_noise_control_200_panels_and_objectives`)은 G가 홀수면 다시 산출해야 한다 |
| 회귀 테스트 | `quant/test_pbo_counts_the_median_rank_as_overfit`: 시드 7의 1500×9 잡음 행렬에서 `pbo_cscv`가 독립 구현(λ≤0)과 1e-12 안에서 같다. 짝수 G에서는 기존 값이 그대로다 |

```diff
--- a/core/quant/validate.py
+++ b/core/quant/validate.py
@@ -264 +264 @@
-    return {"pbo": float(np.mean(logits < 0)), "n_splits": int(logits.size),
+    return {"pbo": float(np.mean(logits <= 0)), "n_splits": int(logits.size),
--- a/core/quant/gate_stats.py
+++ b/core/quant/gate_stats.py
@@ -723 +723 @@
-    return {**base, "pbo": float(np.mean(logits < 0)), "winner_loses_share": share,
+    return {**base, "pbo": float(np.mean(logits <= 0)), "winner_loses_share": share,
```

#### FC-08 · P3 · 사실 — GJR skew-t의 지속성에 γ/2를 쓴다

| 항목 | 내용 |
|---|---|
| ID | FC-08 |
| 심각도 | P3 (검증 게이트의 채점 전용 모듈) |
| 판정 | 사실 |
| 파일·함수·라인 | `core/quant/gjr.py:115`(정상성 벌점 `alpha + beta + 0.5 * gamma`), `:176`(`pers = p[1] + p[3] + 0.5 * p[2]`) |
| 재현 단계 | `python3 -B .../financial_calcs/r04_garch.py` 3번. Hansen skew-t에서 E[z²·1{z<0}]를 수치 적분 |
| 기대 결과 | 지속성 = α + β + γ·E[z²·1{z<0}]. 대칭이면 0.5 |
| 실제 결과 | ν=6, λ=−0.3: 0.6048. λ=−0.1: 0.5372. 코드는 항상 0.5. γ=0.15이면 지속성이 0.016 과소. 이 표본의 적합 λ=+0.013에서는 0.96543 vs 0.96469(작음) |
| 영향 | 왼쪽 꼬리가 긴 적합에서 비정상(지속성≥1)에 가까운 모형이 정상성 검사를 통과할 수 있다. 반감기 해석이 낙관적이다 |
| 수정안 | 적합 후 m=E[z²1{z<0}]를 적분으로 구해 `persistence = α+β+γ·m`으로 보고하고, m을 쓴 값이 0.995를 넘으면 `stationarity` 플래그를 단다. 최적화 안의 벌점도 같은 m(ν, λ의 표로 근사)을 쓴다 |
| 회귀 테스트 | `quant/test_gjr_skewt_persistence_uses_negative_second_moment`: m(6, −0.3)=0.6048±1e-3; `fit.persistence == α+β+γ·m` |

#### FC-09 · P3 · 사실 — GARCH의 AIC가 μ를 모수로 세지 않는다

| 항목 | 내용 |
|---|---|
| ID | FC-09 |
| 심각도 | P3 |
| 판정 | 사실 |
| 파일·함수·라인 | `core/quant/garch.py:478-482`(`k = 4 if dist == "t" else 3`), `:548`(`delta_aic_vs_gbm=(4 - 2 * ll_gbm) - aic`, GBM은 μ·σ 2개) |
| 재현 단계 | `r04_garch.py` 1번 마지막 줄 |
| 기대 결과 | 같은 자료에서 추정한 표본평균 μ도 두 모형 모두에서 센다(GARCH-t k=5) |
| 실제 결과 | ΔAIC 500.68. μ를 세면 498.68. GARCH 쪽에 2만큼 유리 |
| 영향 | 경계 사례에서만 "GARCH preferred" 판정이 바뀐다. 실무 영향은 작다 |
| 수정안 | `k = (4 if dist == "t" else 3) + 1  # + mu, estimated from the same sample`. BIC도 같이 바뀐다 |
| 회귀 테스트 | `quant/test_garch_aic_counts_the_mean`: t 적합에서 `aic == 2*5 − 2*loglik` |

#### FC-10 · P3 · 사실 — 점프 모형이 머튼 복합 포아송과 다르다

| 항목 | 내용 |
|---|---|
| ID | FC-10 |
| 심각도 | P3 |
| 판정 | 사실 |
| 파일·함수·라인 | `core/quant/montecarlo.py:144-150`(`rng.normal(jump_mu, jump_sig) * n_jumps`), 보정 `:159-162`(n² 항, n≤15 부분합). 모듈 문서 `:12-14`는 "Merton jump-diffusion" |
| 재현 단계 | `python3 -B .../financial_calcs/r05_montecarlo.py` 3번 |
| 기대 결과 | 머튼: n개의 독립 점프 합 ~ N(n·μ_J, n·σ_J²). ln E[exp] = λ(e^{μ_J+σ_J²/2} − 1) |
| 실제 결과 | 보정은 코드 자신의 구성과는 정확히 맞는다(위험중립 z=+0.48). 분산 비율 코드/머튼: 보정된 일간 λ=0.008에서 1.0036, 가상의 λ=0.2에서 1.074 |
| 영향 | 3σ 분할로 보정된 λ에서는 무시할 수준. 문서와 구현의 불일치 |
| 수정안 | `jump_shocks = n_jumps * jump_mu + np.sqrt(n_jumps) * jump_sig * rng.standard_normal(size)`; `corr = 0.5*d_sig**2 − lam*jump_mu + lam*(exp(jump_mu + 0.5*jump_sig**2) − 1)`. 시드 결과가 바뀌므로 고정값 테스트를 확인한다 |
| 회귀 테스트 | `quant/test_mc_jump_matches_merton`: λ=0.2에서 점프 충격 분산이 λ(σ_J²+μ_J²)와 MC 오차 안에서 같다. 위험중립 드리프트 검사 유지 |

#### FC-11 · P3 · 사실(시장 관례는 추정) — 캘린더·영업일·결제일이 없다. FX 관례가 단순화돼 있다

| 항목 | 내용 |
|---|---|
| ID | FC-11 |
| 심각도 | P3 (문서화된 단순화. 다만 요청서 6장이 확인을 요구한 항목이다) |
| 판정 | 사실: 코드에 캘린더·영업일 조정·결제 지연이 없다. 추정: USDJPY·USDKRW 시장의 프리미엄 조정 델타 관례 |
| 파일·함수·라인 | `core/ficc/common.py:25-39` `parse_tenor`('3m'=0.25, '2w'=2/52), `core/ficc/curves.py:12`, `core/ficc/bonds.py:12-14`, `core/ficc/fx.py:10-14`(spot lag 없음, 프리미엄 미조정 spot delta), `:168-179`. FX 선도 금리: `ui/fx_page.py:66-72` → `core/ficc/data.py:617-622`(SOFR·ECB 예금금리·SONIA 같은 정책·익일물 금리 또는 OECD 월평균을 모든 만기에 사용). 파생 만기: `ui/derivatives_page.py:76`(세션 날짜 0시 기준 달력일/365) |
| 재현 단계 | `r08_equity_deriv.py` 5·6번, `r02_bonds.py` 3번 |
| 기대 결과 | 요청서 6장: day count, calendar, business-day convention, 결제일이 상품별로 명시되고 적용된다 |
| 실제 결과 | 3m=0.25(13주 어음 91/365=0.249315), 2w=0.038462(14/365=0.038356), 윤년 무시. UST 실제 사례에서 같은 수익률의 가격 차이 −0.046/100(일수 관례+T+1). USDJPY 1y 10% 25Δ 행사가: 미조정 154.394/135.879 vs 프리미엄 조정 153.633/135.228(행사가의 약 −48bp). 1y 선도에 익일물 금리 사용 |
| 영향 | 개별 오차는 작다(가격 수 센트, 수익률 1bp 미만). FC-03과 겹치면 커진다. 엔·원 스마일의 25Δ 행사가가 시장 호가 행사가와 어긋난다 |
| 수정안 | 설명형. (1) 채권·스왑에 날짜 기반 일정(결제일, 영업일 조정, 상품별 일수 관례: UST ACT/ACT ICMA, KTB ACT/ACT, SOFR ACT/360)을 도입하거나, 최소한 FC-03의 경과이자와 결제일 입력을 추가한다. (2) FX에 `premium_adjusted` 옵션(USDJPY·USDKRW 기본 켬). (3) FX 선도에는 만기별 기간 금리(OIS 또는 KIS 원화 곡선)를 쓴다. (4) 화면 칩에 "ACT/365F, no calendar"를 표시한다 |
| 회귀 테스트 | `ficc/test_ust_dirty_price_act_act`: UST 4.5% 2036-02-15, 거래 2026-10-27, y=4.5% → dirty 100.897012, clean 99.992121(QuantLib 1.44 ACT/ACT ICMA, T+1). `ficc/test_fx_pa_delta_strike`: USDJPY 예의 PA 25Δ 콜 행사가 153.633±1e-3 |

#### FC-12 · P3 · 사실 — 만기 시 d1 부호가 반대다. 죽은 조건식이 있다

| 항목 | 내용 |
|---|---|
| ID | FC-12 |
| 심각도 | P3 (표시값. 현재 소비처 없음) |
| 판정 | 사실 |
| 파일·함수·라인 | `core/ficc/swaps.py:200-205` `_intrinsic`(`math.inf * sign`: 콜·풋 부호로 정함). `core/ficc/equity_deriv.py:491`(`rate_daily=None if drift_daily is not None else None`, 항상 None) |
| 재현 단계 | `r01_options.py` 마지막 줄: `black76(0.03, 0.04, 0.0, 0.2).d1` |
| 기대 결과 | OTM 콜이면 d1=−∞ |
| 실제 결과 | +∞. `.d1`, `.d2`를 읽는 곳은 저장소에 없다(grep) |
| 영향 | 지금은 없음. 나중에 d1으로 확률(N(d2))을 표시하면 반대 값이 나온다 |
| 수정안 | `d = (math.inf if F > K else -math.inf) if F != K else 0.0`로 d1=d2=d. `equity_deriv.py:491`은 `rate_daily=None`으로 단순화 |
| 회귀 테스트 | `ficc/test_intrinsic_d1_sign`: OTM 콜 d1=−∞, ITM 콜 +∞, OTM 풋 +∞ |

#### FC-13 · P3 · 사실 — `implied_repo`가 관례 인자를 무시한다

| 항목 | 내용 |
|---|---|
| ID | FC-13 |
| 심각도 | P3 |
| 판정 | 사실 |
| 파일·함수·라인 | `core/ficc/equity_deriv.py:55-59` `implied_repo`(항상 KRX 단리), `:85`(`basis_report`가 `convention`을 넘기지 않음) |
| 재현 단계 | `r08_equity_deriv.py` 1번 셋째 줄 |
| 기대 결과 | `convention="cont"`면 연속복리 암시 금리 |
| 실제 결과 | 공정가치는 연속복리(396.5180)인데 암시 금리는 단리 2.8000%(연속 등가 2.8300%) |
| 영향 | 화면은 KRX 기본값만 쓰므로 현재 영향 없음 |
| 수정안 | `implied_repo(..., convention="krx")`에 `if convention != "krx": return math.log(F / (spot - div_pts)) / T` 추가, `basis_report`가 넘긴다 |
| 회귀 테스트 | `ficc/test_implied_repo_follows_convention`: 두 관례 모두 `fair_value(S, implied_repo(F,…), T, …) == F`(1e-12) |

#### FC-14 · P3 · 사실 — 캐리 백테스트의 "Sharpe"가 다른 정의다

| 항목 | 내용 |
|---|---|
| ID | FC-14 |
| 심각도 | P3 |
| 판정 | 사실 |
| 파일·함수·라인 | `core/ficc/fx.py:432-443`(`sharpe = CAGR / ann_vol`). 게이트는 `core/quant/validate.py:137-143`(산술평균/표준편차·√252) |
| 재현 단계 | `r08_equity_deriv.py` 4번(같은 일간 손익) |
| 기대 결과 | 앱 전체에서 같은 Sharpe 정의 |
| 실제 결과 | 0.428(캐리 화면식) vs 0.467(게이트식). 차이 ≈ σ²/2/σ |
| 영향 | 화면 간 비교가 어긋난다 |
| 수정안 | `sharpe=validate.sharpe(daily)`로 바꾸거나 라벨을 "CAGR/vol"로 바꾼다 |
| 회귀 테스트 | `ficc/test_carry_backtest_sharpe_matches_gate`: `bt.sharpe == validate.sharpe(np.diff(bt.equity)/bt.equity[:-1])` |

#### FC-15 · P3 · 사실 — 테스트가 독립 기준값을 거의 고정하지 않는다

| 항목 | 내용 |
|---|---|
| ID | FC-15 |
| 심각도 | P3 |
| 판정 | 사실 |
| 파일·함수·라인 | `tests/ficc_acceptance.py`, `tests/quant_acceptance.py`. 기준 실행 `baseline2_results.json`에서 금융 계산 관련 83건: PASS 78, NOT_RUN 5(`test_m0_15_e_labels_bootstrap_refdata`, `test_g_kr_02b_delta_sharpe_shares_refdata`, `test_step03_dsr_vs_no_steps_reference_run_pending`, `test_g_dsr_02_r03_net_of_cost_golden_refdata`, `test_pbo01_kospi_vt_grid_refdata`) |
| 재현 단계 | 테스트 이름과 본문 읽기 |
| 기대 결과 | 가격 공식마다 외부 기준값(교과서·QuantLib) 하나 이상을 고정한다 |
| 실제 결과 | 대부분 항등식이다(왕복, 패리티, 수치 미분, 합=DV01). 이런 테스트는 공식이 일관되게 틀려도 통과한다. 예외: DSR의 BLdP 재현, PBO 잡음 대조. NOT_RUN 5건은 통과로 보지 않는다 |
| 영향 | FC-01·FC-02·FC-03 같은 결함을 기존 테스트가 잡지 못했다 |
| 수정안 | 이 감사의 기준값을 고정 테스트로 추가한다: Hull BS 4.76/0.81, Black-76 풋 1.12, QuantLib GK 그릭스(r01), 10y 5% 채권 y=6% 가격 92.5612625698·Mac 7.8949973402·볼록성 71.7853980129(r02), off-cycle dirty/clean(r02), 1y5y ATM 스왑션(r03), Vasicek·CIR·HW 할인채(r03), arch 우도 동일성(r04, 패키지 의존이면 우도 숫자를 고정) |
| 회귀 테스트 | 위 목록 자체 |

#### FC-16 · P3 · 사실 — 조기상환형 상품이 없다. 배당은 연속 수익률뿐이다

| 항목 | 내용 |
|---|---|
| ID | FC-16 |
| 심각도 | P3 (요청서 6장의 검사 항목을 수행할 대상이 없다) |
| 판정 | 사실 |
| 파일·함수·라인 | `core/ficc/structured.py` 전체(4개 상품: PPN, RC, DCD, 스티프너). 오토콜·배리어·녹인·조기상환 용어 0건(`r07_structured.py` 5번). 배당은 `r_for_or_div` 평탄 연속 수익률(`structured.py:27-29`) |
| 재현 단계 | `r07_structured.py` 5번 |
| 기대 결과 | 요청서: "조기상환 조건의 민감도를 검사" |
| 실제 결과 | 검사 불가. README `:108-118`도 조기상환 상품을 주장하지 않는다(README 주장과 코드는 일치) |
| 영향 | 국내 판매 비중이 큰 ELS(스텝다운 오토콜) 류를 이 앱으로 평가할 수 없다. 이산 배당(KOSPI200의 12월·3월 집중)을 반영할 수 없다 |
| 수정안 | 기능 추가 범위다. 추가한다면: 다중 관측일 오토콜·녹인을 MC(위험중립, 이산 배당 일정, 기초자산 상관)로 평가하고, 해석해가 있는 단순 사례(단일 관측 디지털, 배리어 없는 경우 = 디지털 콜 묶음)로 검증한다 |
| 회귀 테스트 | 추가 시: 단일 관측일·배리어 없음의 오토콜 = 디지털 콜 + 채권의 닫힌식(1e-3 MC 오차 안), 조기상환 확률의 vol·배당·상관 민감도 부호 |

## 5. 소유자 메모와의 관계 ("공급사필요", "FICC/BTC KIS 접근")

이 차원의 결함 중 일부는 공식이 아니라 **입력 공급자 부재**에서 온다. 요청서 7장 8번에 따라 구현하지 않았다. 공급자 전반의 답은 `docs/audit/2026-10-27/c01_v01_cache_and_vendors.md` 7장을 따른다. 금융 계산에 필요한 입력만 정리한다.

| 입력 | 지금 | 필요한 것 | 관련 |
|---|---|---|---|
| SOFR OIS 스왑 곡선 | 없음(미국채 CMT로 대신) | 스왑 곡선 공급자. KIS는 미국 10·30년 금리만 준다(c01_v01 7장, 코드 근거) | FC-05 |
| 원화 할인 곡선 | 코드는 있음(`curve_models.krw_curve_panel`, KIS CD91+국고채) 그러나 화면에 연결 안 됨 | 구조화·FX 화면에 연결. 공식 지표는 ECOS(클라이언트 없음, V01-03) | FC-04, FC-11 |
| 스왑션·캡 변동성, FX 변동성 표면(ATM/RR/BF) | 사용자 입력 | 표면 공급자 없음. 출처 표시 필요 | 3장 4·6행 |
| 10y−2y 스프레드 변동성 | 없음 | 스프레드 옵션 평가용 vol(역사적 추정 또는 CMS 스프레드 옵션 호가) | FC-01 |
| KOSPI200 배당점수 | 없음 | KIS 이론가에서 역산 가능(FC-06 diff) | FC-06 |

BTC 관련 계산(김치 프리미엄 등)은 이 차원에서 다루지 않았다(d03, c01_v01 보고서 참조).

## 6. 미검증 항목

- 실시장 입력의 정확성: FRED DGS 수익률, KIS 옵션 보드·KIS IV의 관례, KIS 이론가의 배당·금리 규칙. 네트워크가 없다.
- FC-05의 실제 스왑 스프레드 크기, FC-06의 만기월별 실제 배당점수, FC-01의 실제 10y−2y 정규변동성. 외부 데이터가 필요하다.
- CMS 볼록성 조정의 크기. 계산하지 않았다(FC-01의 반대 방향 효과).
- `vol_products.py`: 기대 월간 드리프트 −b/2와 롤다운 백테스트는 휴리스틱·실증 대상이다. 공식 검증 대상이 아니고 데이터로 검증하지 않았다.
- `equity_deriv.hedge_pnl_simulation`의 손익 항등식, SVI 적합과 Gatheral–Jacquier g(k), 위험중립 밀도: 식은 문헌과 같다(코드 읽기). 독립 수치 기준값과 비교하지 않았다. 모듈 자체 검사만 통과했다.
- `ratesim.calibrate`의 OLS 보정 품질, Hull–White 시뮬레이션 평균의 곡선 재현: 닫힌식 할인채만 QuantLib와 비교했다.
- `validate.kupiec`: x=0 또는 x=n이면 우도비 대신 점수(z²) 검정을 쓴다(`validate.py:633-635`). 정확한 LR(−2n·ln(1−α))과 p값이 다르다. 게이트 최소 표본(500/1000)에서는 결론이 같다는 것을 손계산으로만 확인했다.
- `fx.carry_backtest`의 무예견성: 코드 읽기와 자체 검사만.
- 화면의 퍼센트·bp 표시 변환: 코드 읽기만(`ui/rates_page.py:205`, `ui/structuring_page.py:57,87`). 렌더링 확인은 하지 않았다.
- 이 차원 밖: `risk_layer`, `gate_stats` 카드 통계, `forecast_eval`, `vol_estimators`, `forward_sim`, `sleeves`. 성능은 계측하지 않았다.

## 7. 재현 스크립트 경로

모두 `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/audit_work/financial_calcs/`에 있다. 각 스크립트는 같은 이름의 `.out` 파일에 결과를 남긴다. 실행: 해당 폴더에서 `python3 -B <스크립트>`.

| 스크립트 | 내용 |
|---|---|
| `r00_selfchecks.out` | 모듈 자체 검사 11개 결과(모두 ok) |
| `r01_options.py` | GK·그릭스·Black-76·Bachelier·SABR·역산 vs QuantLib, 교과서 예. 76건 중 불일치 1건(FC-12) |
| `r02_bonds.py` | 채권 가격·듀레이션·볼록성·DV01 vs QuantLib, clean/dirty, 일수 관례, 캐리·롤, KRD |
| `r03_curves_swaps.py` | 부트스트랩 독립 해, 스왑 다리, 스왑션·캡, DNS 적재, Vasicek·CIR·HW |
| `r04_garch.py` | GARCH-t·GJR-t 우도·추정·예측 vs `arch`, skew-t 밀도, GJR 지속성 |
| `r05_montecarlo.py`, `r05b_garch_martingale_seeds.py` | 위험중립 드리프트, VaR·CVaR, 점프 구성, GARCH-t 10시드 |
| `r06_validate.py`, `r06b_pbo_ties.py` | Sharpe·Lo SE·DSR 논문 예, PBO 동점 처리 |
| `r07_structured.py` | PPN·RC 독립 가격·민감도, DCD 통화, 스티프너 floor 가치, 조기상환 용어 검색 |
| `r08_equity_deriv.py` | 베이시스 배당, LETF 드래그, MFIV 이산화, Sharpe 정의, 테너 관례, FX PA 델타 |
| `r09_stub_periods.py` | 스텁 발생 가중의 par·PV·캡 ATM·RC 쿠폰 영향 |
| `refpkgs/` | QuantLib 1.44, arch 8.0.0(스크래치 전용 설치) |
