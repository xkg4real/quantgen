# Bonds 화면 검증 G. 실제 UI 구동(Flet 웹 + Chromium)

> 작성 메모 (오케스트레이터): 하네스가 하위 에이전트의 보고서 파일 쓰기를 막아, 조사 에이전트가 반환한 본문과 독립 검증자가 반환한 검증 절을 내용 변경 없이 옮겼습니다. 저장소 코드는 바꾸지 않았습니다.

## G_real_ui — 실제 Bonds 화면 구동 검증 (브라우저)

### 범위와 방법
- 대상: `ui/bonds_page.py`의 실제 `build_bonds_page`. 저장소 HEAD(078981a)를 스크래치로 복사(`git archive`)해서 그 복사본을 띄웠다. 저장소 파일은 하나도 바꾸지 않았다(`git status` 깨끗함).
- 경로: **브라우저 경로가 성공했다.** Flet 0.85.2 웹 모드(`ft.run(view=WEB_BROWSER, no_cdn=True)`)로 Bonds 페이지 하나만 띄웠다. 시스템 Chromium(Playwright 1243)으로 구동했다. `flt-semantics-placeholder`를 눌러 semantics 트리를 켰다. 입력은 `input[aria-label=…]`, 드롭다운과 Run은 semantics 노드로 찾았다.
- 환경 보정 1건: flet_web 0.85.2가 `fastapi.FastAPI(openapi_prefix=…)`를 넘기는데 설치된 fastapi 0.162가 이를 거부한다(TypeError, 서버 시작 실패). 런처 안에서만 이 인자를 버리는 shim을 넣었다(G-11). 앱 코드는 건드리지 않았다.
- 데이터: FRED/yfinance 호출 함수(`core.ficc.data._fred_fetch`, `_yf_fetch`)를 런처에서 막았다(FICCError). `FRED_BASE_URL`은 닫힌 로컬 포트로 바꿨다. 캐시 TTL 0, 캐시 폴더는 스크래치. `ANTHROPIC_API_KEY`는 빈 값(Deep analysis 비활성). 키나 .env는 열지 않았다.
- 증거: (1) 전체 페이지 PNG, (2) 런처가 0.2초마다 실제 컨트롤 트리에서 뽑은 서버측 스냅숏(필드 값, 텍스트, busy 링, hedge 행 표시 여부; `state_dump.jsonl`), (3) 브라우저 semantics 텍스트.
- 한계: 소유자는 데스크톱(FLET_APP)으로 테스트했다. 나는 같은 Python 페이지 코드를 웹으로 띄웠다. 로직은 같지만 글꼴·폭 렌더링은 데스크톱에서 다를 수 있다(미확인). 실제 FRED 경로는 지시대로 막았으므로 미확인이다.

### 코드 추적 (file:function:line)
| 단계 | 위치 |
|---|---|
| 입력 파싱 | `ui/bonds_page.py:_num:38-49` (빈 값→default, `,` 전부 제거 `:40`, 비유한수 거부 `:47`) |
| Tool 전환 | `ui/bonds_page.py:build_bonds_page.on_tool:87-89` (hedge 행 보이기만, 결과는 그대로) |
| Run | `ui/bonds_page.py:run:94-224`. `:96` 결과 비움 → `page.run_thread(worker)` `:224`. Run 버튼은 비활성화되지 않음 `:237` |
| 작업자 입력 읽기 순서 | `:105` tool, `:107-108` coupon/maturity/freq/notional, `:109` ytm, `:110` **느린 곡선 적재**, `:112` **price는 적재 뒤에 읽음**, `:117` hedge 필드 |
| 결과 기록 | `:216-218` (세대 검사 없음), 오류 `fail:99-102` |
| 계산 | `core/ficc/bonds.py:analyze_bond:231-254`, `scenario_pnl:299-320`, `shocked_curve:288-296`, `carry_roll:169-208`(`h=min(horizon,maturity)` `:189`, 라벨용 `horizon=horizon` `:207-208`), `futures_hedge_ratio:323-329` |
| 곡선 | `core/ficc/data.py:load_treasury_curve:552-568`, `_provider_rows:449-495`(일괄 실패 시 id별 재시도 `:479-484`), `core/ficc/curves.py:YieldCurve._log_df:77-85` |
| 차트 제목 | `ui/fcharts.py:144,164,186` `set_title(..., loc="left")`; `ui/qcharts.py:_style:36-45`는 `ax.title`(가운데)만 색칠 `:43` |

### 단계별 관찰 (스크린샷은 모두 `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/` 아래)
| 단계 | 입력 | 화면 | 스크린샷 |
|---|---|---|---|
| 0 | 로드, Curve source→Synthetic demo | 빈 상태 안내 "Quote it by price or by yield (leave the other blank)" | `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/S0b_synthetic_selected.png` |
| (1) 기본 계산 | 4.50%, 10y, 반기, Yield 4.50 | 빨간 "Synthetic data" 배너, 칩 `curve: SYNTHETIC 2026-10-27`. Price 100.000, Yield 4.500%, Mac 8.16y, Mod 7.98, Cvx 76.2, DV01 798, z −315.9bp, Carry −1.239, Roll −0.180, 합 −1.419, BE −17.8bp. 차트 2개 | `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/S1_default_calc.png` |
| (1b) 소유자 1행 | 5.50%, Yield 4.50 | 107.982 / 4.500% / 7.92y / 7.74 / 73.0 / 836 — 소유자 화면과 같음 | `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/S1b_c550_y450.png` |
| (2) 충돌 | Price 100 + Yield 4.50 | "Give exactly one of price or ytm." **이전 결과는 남지 않는다**(결과 영역 전체가 오류 하나로 바뀜, 이미지 0개) | `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/S2_price100_and_yield450.png` |
| (2b) 둘 다 빈 값 | | 같은 문구(구분 없음) | `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/S2b_both_blank.png` |
| (2c) Yield 0 | | 유효. Price 155.000, Mod 8.31(=Mac) — 0을 빈 값으로 취급하지 않음 | `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/S2c_yield_zero.png` |
| (2d) Price 0 | | "price must be positive, got 0.0." | `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/S2d_price_zero.png` |
| (3) Run 없이 Price 입력 | 5.50% 실행 후 Yield 지움, Price 95 입력 | 화면은 여전히 Price 107.982 / Yield 4.500%. **표시 없음** (G-02) | `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/S3b_typed_price95_no_run.png` |
| (3c/3d) Run | Price 95 / 105 | 6.178% (7.76y, 7.52, 69.9, 715) / 4.863% (7.88y, 7.70, 72.3, 808) — 소유자와 같음 | `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/S3c_price95_run.png`, `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/S3d_price105_run.png` |
| (4a) Tool→Scenarios, Run 없음 | | Calculator 결과(105.000/4.863%)가 그대로. 입력은 Yield 4.50 | `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/S4a_tool_scenarios_no_run.png` |
| (4b) Scenarios | 5.50%/4.50 | 기준 107.982. +25 −21,266, −25 +21,759, +100 −82,220(−7.61%), −100 +90,112(+8.35%), bear steep −10,997, bull steep +30,550, bear flat −29,619, bull flat +11,146, fly +8,033 | `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/S4b_scenarios_c550_y450.png` |
| (4c) Scenarios | 5.50%/5.50 | 기준 100.000. +100 −75,256, −100 +82,450, +25 −19,462, −25 +19,911, bear steep −10,015, bull steep +28,004, bear flat −27,153 | `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/S4c_scenarios_c550_y550.png` |
| (5a) Tool→Futures hedge, Run 없음 | | hedge 입력 행(CTD 65, CF 0.8, Position 빈칸)이 나타나고, **그 아래에 시나리오 결과가 그대로** 남음 | `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/S5a_tool_hedge_no_run.png` |
| (5b) hedge Run | 5.50%/5.50 | Pos 761, Fut DV01 81.25, 9.37, Rounded 9, residual +30/bp | `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/S5b_hedge_run_c550_y550.png` |
| (5c) 소유자 hedge | 4.50%/4.50 | Pos 798, 81.25, **9.82, Rounded 10**, residual **−14/bp** — 소유자 화면 재현 | `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/S5c_hedge_owner_case.png` |
| (5d) 숏 포지션 | Position DV01 −798 | "Contracts to sell −9.82", "Rounded −10", "Sell that many to flatten a long position; … +14 per bp" (G-05) | `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/S5d_hedge_short_position.png` |
| (5e) CTD 0 | | "CTD DV01 per contract and conversion factor must be positive." | `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/S5e_hedge_ctd_zero.png` |
| (5f) CF 빈칸 | | CF가 조용히 1.0000 → 12.28 계약(0.8이면 9.82) (G-03) | `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/S5f_hedge_cf_blank.png` |
| (6) Tool→Calculator, Run 없음 | | hedge 입력 행은 숨겨지고 hedge 결과(CF 1.0000)는 남음. 숨은 CF 필드는 0.8 | `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/S6_back_to_calc_no_run.png` |
| 경합 | Auto(FRED 느림, 호출당 1초) Run#1 → Synthetic·Coupon 6.00 Run#2 | +4.07초 Run#2 결과 111.973, busy 링 꺼짐. +12.31초 Run#1이 덮어씀: 입력은 Synthetic/6.00인데 화면은 100.000(4.50% 채권)+"FRED failed" 배너 (G-01) | `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/Q2_run1_overwrites_run2.png`, `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/crop_Q2_run1_overwrites_run2.png` |
| 찢어진 읽기 | Run#1(Yield 4.50, Price 빈칸) 중 Yield 지우고 Price 95 | Run#1이 "Give exactly one of price or ytm." — 클릭 시점에도, 최종 입력에도 존재하지 않은 조합 (G-01) | `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/state_dump_race_torn.jsonl` (+6.21초 행) |
| 빈 값/이상값 | Coupon 빈칸 / Maturity 빈칸 / Notional 빈칸 / Yield "4,5" / Maturity 0.1 | 0% 쿠폰 64.082 / 10y / 1,000,000 / **Yield 45.000%**, z +3251.5bp / "Carry (3m)" 라벨에 BE −2325.9bp | `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/B1_coupon_blank.png`, `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/B4_yield_comma_decimal.png`, `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/B5_maturity_short.png` |
| Auto 대체 | Auto, FRED 차단 | "Synthetic data: FRED failed: FRED served 0/11 tenors (…11번 반복…)" | `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/E1_auto_fred_blocked_fastfail.png` |

### 수식과 독립 계산
- 독립 구현: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/verify_screen_numbers.py`. 저장소 함수를 부르지 않고 공식으로 다시 썼다.
  - 현금흐름 t_i = T − k/f, 쿠폰 100·c/f, 만기에 +100.
  - P(y) = Σ CF_i (1+y/f)^(−f·t_i). y(P)는 자체 이분법([−0.5, 2.0]).
  - Mac = Σ t·PV / P, Mod = Mac/(1+y/f), Convexity = (P(y+h) − 2P + P(y−h))/(h²P) (유한차분), DV01 = (P(y−1bp) − P(y+1bp))/2 × N/100 (중심차분).
  - 곡선: 페이지가 쓴 합성 곡선의 **zero 노드만** 입력으로 받았다(부트스트랩은 재유도하지 않음 → B/E 몫). DF(t) = exp(−z·t 선형보간), 끝은 flat zero. z-spread는 자체 이분법: Σ CF·DF(t)·e^(−s·t) = P.
  - 시나리오: zero에 bp를 더함(평행), 비평행은 키 테너 bp를 곡선 노드에 선형보간·양끝 flat. z-spread 고정 전체 재평가. P&L = (P_new − P)·N/100. P&L % = P_new/P − 1.
  - Carry = c·100·h − zero(h)·P·h. Roll = [Σ_{t>h} CF·DF(t−h)e^(−s(t−h)) + Σ_{t≤h} CF − c·100·h] − P. BE = (carry+roll)/(Mod·P)/1bp.
  - Hedge: n = posDV01 × CF / CTD; Futures DV01 = CTD/CF; 잔여 = pos − round(n)·CTD/CF.
- 결과: 화면 숫자 **171개 모두** 독립값·저장소값과 화면 자리수에서 일치(불일치 0). |독립 − 저장소| 최대 2.2e-4(DV01 중심차분 2차항).

| 단계 | 항목 | 화면 | 독립 | 저장소 |
|---|---|---|---|---|
| S1 | DV01 | 798 | 798.185750 | 798.185618 |
| S1 | z-spread | −315.9bp | −315.8787 | −315.8787 |
| S1 | Carry / Roll / BE | −1.239 / −0.180 / −17.8bp | −1.238678 / −0.180058 / −17.7745 | 같음 |
| S1b | Price / Mod / Cvx / DV01 | 107.982 / 7.74 / 73.0 / 836 | 107.981856 / 7.744728 / 73.014825 / 836.290252 | 107.981856 / 7.744728 / 73.014818 / 836.290117 |
| S3c | Yield | 6.178% | 6.177690% | 6.177690% |
| S3d | Yield | 4.863% | 4.862682% | 4.862682% |
| S4b | +100 / −100 / +25 / −25 | −82,220 / +90,112 / −21,266 / +21,759 | −82,219.86 / +90,112.35 / −21,265.59 / +21,758.51 | 같음 |
| S4b | +100 P&L % | −7.61% | −7.6142% (분모=시장가치 1,079,818.56). 명목 분모라면 −8.22% | 같음 |
| S4c | +100 / −100 / bear steep / bull steep / bear flat | −75,256 / +82,450 / −10,015 / +28,004 / −27,153 | −75,255.73 / +82,449.89 / −10,015.18 / +28,003.58 / −27,152.98 | 같음 |
| S5c | Pos / n / Rounded / 잔여 | 798 / 9.82 / 10 / −14 | 798.1858 / 9.823825 / 10 / −14.3143 | 798.1856 / 9.823823 / 10 / −14.3144 |
| S5d | n / 잔여 | −9.82 / +14 | −9.821538 / +14.5 | 같음 |
| S5f | n (CF 빈칸→1.0) | 12.28 | 12.279781 | 12.279779 |

- 소유자 2.1절 5행(곡선 무관 지표: 가격, YTM, Mac, Mod, Cvx, DV01)은 독립 계산으로 **모두 정확히 재현**된다.
- 소유자 2.4절: 798 × 0.8 / 65 = 9.8215 → "9.82". 실제 Position DV01은 798.1858이라 9.8238 → "9.82". Rounded 10, 잔여 −14.31 → "−14".
- 소유자 2.3절 시나리오 숫자는 이 합성 곡선과 다르다(+100bp: 소유자 −81,597 vs 합성 −82,220; c5.5/y5.5 +100bp −74,657 vs −75,256). 소유자 화면은 다른 곡선(아마 FRED)을 썼다. 어느 곡선인지는 **미확인**(C 몫).
- 합성 곡선 최신값: zero 9.55%(1m)→6.63%(30y), par 9.59%→7.17%. 역전되고 실제 수준과 동떨어진 값이다. 화면에는 합성 배너가 있다.
- KRD 차트 제목 "total 860 per bp"(zero 평행 DV01, z 고정)와 DV01 타일 836(수익률 DV01)이 한 화면에 함께 나온다. 비율 1.0288. 독립 계산 860.4035 = 저장소 860.4035. 정의 차이이며 오류는 아니다. 다만 설명이 없다(G-09). 그 제목은 읽을 수도 없다(G-07).

### 성능 (합성, 웹, 클릭→서버 컨트롤 변경, 0.2초 폴링 해상도)
- Calculator 0.32~0.47초, Scenarios 0.34~0.46초, Hedge 0.05~0.20초, 오류 0.03~0.08초. 곡선 적재(합성) 0.004~0.014초(`launcher_calls.log`). 나머지는 계산+matplotlib 렌더.
- Auto 경로에서 FRED가 실패하면 공급자 호출이 **12번**(일괄 1 + id별 11) 나간다. 호출당 1초로 흉내 내면 12.01초. 실제 네트워크 지연은 미확인(`data/net.py` 문서상 호출당 최대 약 3×12+1초). 관련: P01-09.
- 같은 입력 재실행 재현성: 5.50%/4.50을 S1b·S3a·S4b에서 세 번 실행. 107.982/836/−317.8bp 동일.

### 테스트 로그
| 테스트 | 대상 | 결과 |
|---|---|---|
| 브라우저 5단계+추가(`drive_bonds.js main`) | HEAD 복사본 | 22 스텝 실행 완료, 관찰은 위 표 |
| 빈 값/이상값(`drive_bonds.js blanks`) | HEAD | 5 스텝 실행 |
| 경합(`race`, `race2`) | HEAD | 재현됨(G-01) |
| `verify_screen_numbers.py` | 화면 171개 | PASS (불일치 0) |
| `python3 -B -m ui.bonds_page` 자체검사 | HEAD 복사본 | PASS ("ok") |
| `python3 -B -m core.ficc.bonds` 자체검사 | HEAD 복사본 | PASS ("ok") |
| `test_g_regression.py` (G-01a, G-01b, G-02a, G-02b, G-07) | HEAD 복사본 | **FAIL 5/5** (0/5 PASS) |
| `test_g_regression.py` | 수정 복사본 | **PASS 5/5** |
| `python3 -B -m ui.bonds_page` | 수정 복사본 | PASS |
| 브라우저 `fixcheck` | 수정 복사본 | Coupon 수정 후·Tool 전환 후 경고 배너 표시, 재실행 후 사라짐. 차트 제목 #e7ecef로 보임 |
| 브라우저 `race2` | 수정 복사본 | Run#1(12.011초) 끝났지만 버려짐. 화면은 Run#2(111.973) 유지 |
| `tests/run_all.py` | — | NOT_RUN (규칙상 금지) |
| 데스크톱(FLET_APP) 구동 | — | NOT_RUN |
| 실제 FRED 경로 | — | NOT_RUN (차단 지시) |

로그: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/test_g_regression.log`, `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/selfcheck.log`, `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/verify_screen_numbers.log`, 단계별 JSON `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/steps_main.json` 등.

### 심각도별 이슈
| ID | 심각도 | 판정 | 요지 |
|---|---|---|---|
| G-01 | P2 | 테스트로 확인됨 | 늦게 끝난 이전 Run이 새 결과를 덮어씀. 작업자가 입력을 서로 다른 시점에 읽음. busy 링이 먼저 꺼짐 (관련 P01-05) |
| G-02 | P2 | 테스트로 확인됨 | 입력 변경·Tool 전환 뒤 이전 결과가 표시 없이 남음 |
| G-03 | P2 | 테스트로 확인됨 | 빈 칸이 조용히 기본값이 됨: Coupon→0%, Maturity→10y, Notional→1e6, CF→1.0(필드 초기값 0.8과 다름), CTD→65 |
| G-04 | P2 | 테스트로 확인됨 | 모든 필드에서 `,` 제거: Yield "4,5" → 45% |
| G-05 | P2 | 테스트로 확인됨 | 숏 포지션에 "Contracts to sell −9.82"와 "flatten a long position" 문구. 잔여 부호 정의 없음 |
| G-06 | P2 | 테스트로 확인됨 | 만기 < 3m에서 "Carry (3m)" 라벨이 실제 구간(h=만기)과 다르고 BE −2325.9bp 같은 값을 그대로 표시 |
| G-07 | P3 | 테스트로 확인됨 | 모든 FICC 차트 제목(loc="left")이 검정 #000000 on #171d21(대비 약 1.2:1). "z-spread held", "total 860 per bp"가 안 보임 |
| G-08 | P3 | 테스트로 확인됨 | 오류 문구가 필드명과 다르고, 둘 다 입력/둘 다 빈칸을 구분 못하고, 필드 강조 없음. 안내문은 첫 Run 뒤 사라짐 |
| G-09 | P3 | 테스트로 확인됨 | 잘린 라벨, 단위 없는 타일, P&L % 분모 미표기, Shock 열 단위 없음·−12.5를 −12로 표기, DV01 836 vs KRD 860 설명 없음, 드롭다운 접근성 이름 없음 |
| G-10 | P3 | 테스트로 확인됨 | FRED 실패 배너가 같은 오류를 11번 나열. 실패 시 호출 12번 |
| G-11 | P3 | 테스트로 확인됨 | flet_web 0.85.2 + fastapi 0.162 비호환으로 웹 모드 시작 실패. fastapi 미고정 |
| G-12 | P3 | 코드로 확인됨 | 자체검사가 작업자를 동기 실행해서 G-01/G-02를 원리적으로 못 잡음 |

기존 보고서와 겹치는 것(중복 기재 안 함): FC-03(Price가 dirty), D03-03(Bonds 해설에 합성 표시 없음; S1 해설에도 없음을 화면에서 재확인), D03-08(합성 칩 muted, 합성 날짜=오늘; 화면 칩 `curve: SYNTHETIC 2026-10-27` 재확인), P01-05(재클릭 미차단; G-01은 그 위에 찢어진 읽기와 덮어쓰기의 화면 증거를 더함. P01-05의 잠금 수정만으로는 찢어진 읽기가 남는다), P01-09/C01-06(공급자 호출·stale 정책).

### 수정안 (스크래치 복사본에서 적용·검증, 저장소 미변경)
- 패치 스크립트 `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/apply_fix.py`, diff `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/fix_bonds_page.diff`(+38줄), `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/fix_qcharts.diff`(+2/−1줄, CRLF 유지).
- G-01: `run()`에서 세대 번호를 올리고 모든 입력을 클릭 시점에 `SimpleNamespace(label, value)`로 복사한다. 작업자는 복사본만 읽는다. 결과·오류 기록 전에 `gen != state["gen"]`이면 버린다.
- G-02: 모든 TextField `on_change`, 드롭다운 `on_select`, `on_tool`이 `mark_stale()`을 부른다. 현재 입력이 결과를 만든 스냅숏과 다르면 경고 배너 "Inputs changed since the last Run…"를 결과 위에 띄운다.
- G-07: `ui/qcharts.py:_style`에서 `for loc in ("left","center","right"): ax.set_title("", loc=loc, color=pal.text)`.
- G-03/G-04/G-05/G-06/G-08/G-09/G-10/G-11: 아래 각 이슈의 fix 필드(제안, 미적용).

### 남은 위험 / 미확인
- 데스크톱 앱에서의 동일 동작과 라벨 잘림 폭: 미확인(웹만 구동).
- 실제 FRED 곡선에서의 화면 숫자, as-of 의미, 지연: 미확인(차단).
- 소유자 2.3절 시나리오 숫자의 곡선 출처: 미확인.
- 부트스트랩·보간 자체의 정확성: 미확인(G는 zero 노드를 입력으로 받음; B/E 몫).
- Deep analysis(Claude) 경로: 키 없음으로 비활성 상태만 확인.
- 실거래·시장 정확성: 검증하지 않았다. 화면 숫자는 "코드와 독립 공식이 일치한다"는 것까지만 확인했다.

### 스크립트·산출물 경로
- 런처 `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/launch_bonds_web.py`, 서버 제어 `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/server.sh`
- 브라우저 구동 `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/drive_bonds.js` (모드 main, blanks, race, race2, fixcheck), 탐색 `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/probe.js`, `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/probe2.js`
- 독립 계산 `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/verify_screen_numbers.py` → `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/verify_screen_numbers.json`
- 제목 색 확인 `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/check_title_color.py`
- 회귀 테스트 `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/test_g_regression.py`
- 수정 복사본 `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/fixcopy/`, 수정 후 스크린샷 `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/crop_F1_fix_edit_no_run.png`, `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/FIX_Q2_run1_overwrites_run2.png`, `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/G_real_ui/shots/zoom_FIX_chart_title.png`

### 독립 검증 (G_real_ui)

검증자 작업 폴더: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/verify_G_real_ui/`. HEAD는 8159532다. 078981a 이후 바뀐 것은 문서뿐이고 `ui/`·`core/`는 같다. 저장소 `git status`는 깨끗하다. 브라우저는 다시 띄우지 않았다. 대신 실제 스레드(`threading.Thread`, Flet 0.85.2 `run_in_executor`와 같은 동시 실행)로 페이지를 프로세스 안에서 구동했다(`v_ui.py`). 조사자의 스크린샷 `crop_Q2_run1_overwrites_run2.png`과 `zoom_chart_title.png`은 직접 열어 봤다.

| id | 유지 여부 | 정정 심각도 | 정정 상태 | 근거 |
|---|---|---|---|---|
| G-01 | 유지 | P2 | 테스트로 확인됨 | 실제 스레드로 재현했다(`v_ui_HEAD.log`). Run#2 뒤에 Run#1이 결과를 덮어써서 최종 화면은 100.000인데 Coupon 칸은 6.00이다. Run#2가 끝나면 busy 링이 꺼진다. 찢어진 읽기에서는 "Give exactly one of price or ytm."이 나온다. 조사자의 `test_g_regression.py`도 다시 돌렸다. HEAD 0/5, 수정본 5/5다. G-01 수정은 맞다. |
| G-02 | 유지(수정안 불완전) | P2 | 테스트로 확인됨 | 버그는 재현된다. 조사자 수정본에 구멍이 있다. Run이 **진행 중일 때** 바꾼 입력은 결과가 도착해도 표시되지 않는다(`v_ui_FIX.log` FIXGAP). 실행 중에는 `state["shown"]`이 None이고, 작업자는 끝날 때 다시 비교하지 않기 때문이다. 수정: 성공·실패 두 경로에서 `state["shown"] = snap` 뒤의 `page.update()`를 `mark_stale()`로 바꾼다(`fix2_on_top_of_G_fix.diff`). 바꾼 뒤 FIXGAP은 해소되고, `test_g_regression` 5/5, `python3 -B -m ui.bonds_page`는 "ok"다. |
| G-03 | 유지 | P2 | 테스트로 확인됨 | 빈 Coupon으로 0% 채권 64.081647이 오류 없이 나온다. CF를 비우면 1.0000이 되어 12.279779계약이다(독립 계산과 같음). 필드 초기값은 0.8이다. |
| G-04 | 유지 | P2 | 테스트로 확인됨 | "4,5"가 45.000%가 된다. Price 11.554249, z +3251.53bp, DV01 34.53(독립 계산과 같음). |
| G-05 | 유지 | P2 | 테스트로 확인됨 | 포지션이 −798이면 "Contracts to sell" −9.82와 "flatten a long position"이 함께 나온다. 수정안의 over/under 판정은 롱(잔여 −14.31, over)과 숏(+14.5, over) 모두 맞다. 덧붙여 +14.5는 `:+,.0f`의 half-even 반올림 때문에 "+14"로 표시된다. |
| G-06 | 유지(원인·수정 불완전) | P2 | 테스트로 확인됨 | 표시값 −0.520 / −1.796 / −2325.9bp는 재현된다. 다만 근본 원인은 B-01이다. 만기가 3m 안이면 `carry_roll` 합계에서 c·100·(1/f−T) = **1.8**이 빠진다. 현금 기준 합계는 −0.516인데 화면은 −2.316이다. BE는 −517.8bp여야 하는데 −2325.9bp다. 라벨만 고치거나 BE를 숨기면 틀린 "Carry + roll"은 그대로 남는다. B-01 수정과 함께 해야 한다. |
| G-07 | 유지 | **P2**(P3에서 상향) | 테스트로 확인됨 | 범위가 FICC 차트보다 넓다. `ui/` 안의 `set_title` 28곳(fcharts·qcharts·xcharts)이 모두 `loc="left"`이고, `main.py:96`은 항상 dark다. 그래서 출처 표시(`qcharts.py:89` "({history.source})", `fcharts.py:108` "({panel.source})")와 고지문(`fcharts.py:396` "descriptive read, not a regime model (P19)")이 앱 전체에서 보이지 않는다. 출처 표시와 고지문이 사라지는 것은 화면을 오해하게 만드는 상태이므로 P2로 올린다. 픽셀 확인(`v_g07.log`): HEAD 제목은 (0,0,0)이고 수정본은 #e7ecef다. 수정의 부작용도 없다. `_style`은 제목을 넣은 뒤의 축에는 불리지 않는다(`fcharts:201,294`는 twin 축, `xcharts:115`는 제목보다 먼저). |
| G-08 | 유지 | P3 | 테스트로 확인됨 | 둘 다 입력한 경우와 둘 다 빈 경우가 같은 문구다. 어느 필드에도 `error_text`가 없다. hint가 포커스 때만 보인다는 것은 웹 관찰뿐이다. |
| G-09 | 유지 | P3 | 테스트로 확인됨 | `f"{-12.5:+.0f}"`는 "-12"다. `pnl_pct = new/price − 1`이다. KRD 합계 860.4035와 DV01 836.2901의 비율은 1.0288인데, (1+y/f)는 1.0225다. 그래서 제안 문구의 "~"는 꼭 필요하다. Dropdown 접근성 이름 없음은 웹 semantics(`probe_nodes.json`)로만 확인했다. |
| G-10 | 유지(지연 설명 정정) | P3 | 테스트로 확인됨 | `_fred_fetch` 호출 12번(일괄 11 + id별 1×11)과 note 안 사유 11회 반복을 재현했다(`v_g10.log`). 정정: 기본 경로는 pandas_datareader(필수 의존성)다. 그래서 `data/net.py`의 한도가 아니라 HTTP **48회** × timeout 30초다(G-V01). 수정안의 "transport error" 규칙도 구체적이지 않다. 같은 FICCError면 1회만 부른다는 회귀 테스트와도 맞지 않는다. 구체안은 G-V01의 `_TransportError`다. |
| G-11 | 유지 | P3 | 테스트로 확인됨 | 깨끗한 인터프리터에서 `flet_web.fastapi.FastAPI()`를 만들면 `TypeError: ... 'openapi_prefix'`가 난다. fastapi 0.162.0의 `__init__`에는 **kwargs가 없다. 데스크톱 모드는 영향이 없다. |
| G-12 | 유지 | P3 | 코드로 확인됨 | `ui/bonds_page.py:260`의 `run_thread=lambda fn: fn()`는 작업자를 동기로 돌린다. HEAD 자체검사는 "ok"인데 `v_ui.py`는 13/13을 재현한다. |

#### 독립 재계산 (검증자 구현: 해석적 도함수와 Newton. 조사자는 유한차분과 이분법을 썼다)
`v_numbers.py` → `v_numbers.log`, `v_numbers.json`. 합성 곡선은 zero 노드(9.548%→6.634%)만 입력으로 받았다. DF, z-spread, 충격, 재평가는 직접 구현했다. |내 값 − 저장소 값|은 최대 7.2e-6이다(KRD 합계, 중심차분).

| 항목 | 화면 | 검증자 | 저장소 |
|---|---|---|---|
| 5.5%/10y/y4.5 Price | 107.982 | 107.981856 | 107.981856 |
| 같은 채권 DV01 | 836 | 836.290117 | 836.290117 |
| Price 95 → Yield | 6.178% | 6.177690% | 6.177690% |
| S4b +100bp P&L | −82,220 | −82,219.856 | −82,219.856 |
| S4c bear steepener | −10,015 | −10,015.177 | −10,015.177 |
| 헤지 n / 잔여 | 9.82 / −14 | 9.823823 / −14.314382 | 같음 |
| S1 Carry / Roll / BE | −1.239 / −0.180 / −17.8 | −1.238678 / −0.180058 / −17.774502 | 같음 |
| 경합 Run#2 Price(6% 쿠폰) | 111.973 | 111.972784 | — |

위 숫자는 코드와 독립 공식이 서로 맞는다는 뜻일 뿐이다. 시장 정확성은 검증하지 않았다.

#### 실행하지 않은 것
- `tests/run_all.py`: NOT_RUN(규칙상 금지).
- 데스크톱(FLET_APP) 구동: NOT_RUN.
- 브라우저 재구동: NOT_RUN(조사자 스크린샷과 프로세스 안 구동으로 대신했다).
- 실제 FRED: NOT_RUN.
- 수정 사본에서 `tests/ficc_acceptance.py`: NOT_RUN.

### 놓친 항목

#### G-V01 · P2 · 테스트로 확인됨: 기본 FRED 경로(pandas_datareader)가 설정 timeout과 URL을 무시한다. Auto 대체까지 HTTP 48회, 1회 timeout 30초
- 위치:
  - `core/ficc/data.py:_fred_fetch:166-172`: `_pdr.DataReader(ids, "fred", start)`를 timeout·재시도 지정 없이 부른다.
  - `:479-484`: 일괄 호출이 실패하면 id별로 다시 부른다.
  - pandas_datareader 0.11.1 `_BaseReader`: 기본값 `retry_count=3, timeout=30`, `FredReader.url`은 고정값이다.
  - `requirements.txt:14`: pandas-datareader는 필수 의존성이다.
- 재현: `python3 -B v_pdr_timeout.py <copy>`. `requests.Session.get`을 즉시 `ConnectTimeout`을 내는 stub으로 바꿨다. 네트워크는 쓰지 않았다.
- 기대: `config.HTTP_TIMEOUT_SECONDS`(12초)와 `config.FRED_BASE_URL`을 따른다. 대체까지 걸리는 시간에 상한이 있다.
- 실제:
  - HTTP 시도 48회, timeout은 모두 30초다.
  - `FRED_BASE_URL`을 바꿔도 URL은 `https://fred.stlouisfed.org/graph/fredgraph.csv`다.
  - 즉시 실패해도 4.84초가 걸린다.
  - 모든 시도가 timeout까지 매달리면 48×30초 ≈ 24분이다(산술값이며 관측하지는 않았다).
- 영향:
  - 패킷을 버리는 망에서는 Bonds Auto Run의 busy 링이 몇 분 동안 돈다. 취소 수단이 없고, 다시 누르면 G-01이 겹친다.
  - 조사자가 넣은 `FRED_BASE_URL` 차단은 이 경로에서 효과가 없었다. 실제 차단은 `_fred_fetch` 패치가 했다.
- 수정(`fix_m1.diff`, 스크래치에 적용):
  - `FredReader(ids, start=start, retry_count=1, pause=0.5, timeout=config.HTTP_TIMEOUT_SECONDS)`를 쓴다.
  - 응답이 아예 없으면(메시지에 "\nException:\n") `_TransportError(FICCError)`를 낸다. 이 경우 `_provider_rows`는 id별 재시도를 하지 않는다.
  - 같은 사유가 반복되면 note에 한 번만 쓴다.
- 회귀 테스트 `v_m1_test.py`:
  - T1: 시도 ≤4회, timeout은 모두 설정값.
  - T2: 폐지 id 하나가 404여도 나머지 10개 만기를 살린다.
  - 결과: HEAD 1/2(T1 FAIL: 48회, 30초). 수정본 2/2(2회, 12.0초, 1.01초). `python3 -B -m core.ficc.data`는 "ok"다.

#### G-V02 · P3 · 테스트로 확인됨: Breakeven 타일의 툴팁이 음수 값과 모순된다
- 위치: `ui/bonds_page.py:163-164`의 툴팁은 "Yield rise that wipes out carry + roll" 하나로 고정돼 있다. 해설 쪽은 `core/ficc/insights.py:122-126`에서 부호를 처리한다.
- 재현: 기본 입력(4.50%/10y/Yield 4.50)에 합성 곡선으로 Run한다(`v_m2_test.py`).
- 기대: 값이 음수면 "금리가 내려야 본전"이라는 뜻으로 표시한다.
- 실제: 타일은 −17.8bp인데 툴팁은 "Yield rise"라고 한다. 같은 화면의 해설은 "yields must fall 17.8bp ... to break even"이다.
- 영향: 기본 화면에서 같은 숫자를 두 가지 반대 의미로 설명한다.
- 수정(`fix_m2.diff`): `tooltip = "Yield rise that wipes out carry + roll" if cr.total >= 0 else "Carry + roll is negative: yields must fall this much to break even"`.
- 회귀: `v_m2_test.py` 결과 HEAD FAIL, 수정본 PASS. 페이지 자체검사는 "ok"다.
