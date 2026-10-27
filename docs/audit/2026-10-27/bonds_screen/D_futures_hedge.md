# Bonds 화면 검증 D. Treasury 선물 헤지

> 작성 메모 (오케스트레이터): 하네스가 하위 에이전트의 보고서 파일 쓰기를 막아, 조사 에이전트가 반환한 본문과 독립 검증자가 반환한 검증 절을 내용 변경 없이 옮겼습니다. 저장소 코드는 바꾸지 않았습니다.

# D_futures_hedge: Futures hedge 검증 (요청서 3.D, 2.4, 수용 기준 "선물 헤지")

- 대상 코드: 저장소 HEAD `078981a`. 저장소 파일은 하나도 바꾸지 않았다(`git status` 깨끗함).
- 실행 위치: `git archive` 사본 두 개만 썼다. `base`는 HEAD 그대로이고, `fixed`는 아래 최소 수정안을 적용한 사본이다. 위치는 `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/D_futures_hedge/` 이다.
- UI 시험 방법: 모듈 자체 검사와 같은 방식이다. stand-in `ft.Page`로 실제 `build_bonds_page`의 컨트롤과 핸들러를 헤드리스로 구동했다. 실제 Flet 데스크톱 창을 클릭한 시험은 **NOT_RUN**이다.

## ① 요약
- **공식 자체는 맞다.** 계약 수 = Position DV01 × CF / CTD DV01 이다. Futures DV01 = CTD DV01 / CF 이다. 내 독립 구현과 저장소 `futures_hedge_ratio`를 무작위 입력 20,000건으로 비교했다. 최대 상대오차는 3.3e-16 이다.
- **화면 2.4를 재현했다.** Position DV01은 798.185618 이다. 이것은 계산기 기본 채권(쿠폰 4.5%, 10년, 반기, YTM 4.5%, 명목 1,000,000)의 DV01이다. 계약 수는 9.823823 이고 화면에 "9.82"로 나온다. Rounded는 10 이다. 잔여 DV01은 798.1856 − 10 × 81.25 = **−14.3144** 이고 화면에 "-14"로 나온다.
- **요청서의 "798 × 0.8 / 65 = 9.815..."는 계산 실수다.** 정확한 값은 9.821538 이다. 화면의 9.82는 반올림 전 DV01 798.1856에서 나온 9.823823 이다. 두 값 모두 9.82로 표시된다.
- **잔여 DV01과 Rounded는 서로 맞는다.** 두 값 모두 같은 `round(n)`을 쓴다. 수용 기준 "잔여 DV01이 실제 계약 수와 일치"를 만족한다.
- **잔여 DV01의 부호 의미:** −14.31은 과헤지라는 뜻이다. 순 듀레이션이 bp당 14.31만큼 숏이다. 금리가 1bp 내리면 약 14.31을 잃는다. 9계약이면 잔여는 +66.94 이다. 따라서 10계약이 더 가깝고 올바른 선택이다. 화면은 이 부호의 뜻을 설명하지 않는다(D-04).
- **발견 건수:** P0와 P1은 없다. P2 3건, P3 6건이다.
  - D-01: 숏 포지션이면 "Contracts to sell -9.82"와 "Sell that many to flatten a long position"이 나온다.
  - D-02: CTD DV01이나 CF를 비우면 각각 65.0, 1.0이 조용히 쓰인다. CF 필드 초기값은 0.8 이다. CF를 비우면 계약 수가 12.28이 되어 25% 늘어난다.
  - D-03: 화면이 세 가지를 말하지 않는다. 이것이 단순 DV01 근사라는 점, CTD DV01의 단위(계약 액면당), 65와 0.8이 예시값이라는 점이다.
- **최소 수정안을 사본에 적용해 시험했다.**
  - FICC acceptance: HEAD 57/57 PASS, 수정본 58/58 PASS.
  - UI 회귀 11개: HEAD 0/11 PASS, 수정본 11/11 PASS.
  - 새 acceptance 테스트를 HEAD 코드에서 돌리면 FAIL 한다(의도한 결과).
- **시장 정확성은 미확인이다.** 65와 0.8이 실제 어떤 CTD의 값인지 확인하지 않았다. 앱에는 CTD나 CF 데이터 소스가 없다.
- 기존 감사와의 관계: `functional_completeness.md` 4행은 헤지를 "합성: 계산·시나리오·헤지 정상"으로 기록했다. 이 보고서는 그 위에 표시·입력 방어 문제 D-01~D-09를 더한다. `d03_synthetic_fallback.md`의 곡선 배지 문제와는 겹치지 않는다. 헤지 수치는 곡선을 쓰지 않기 때문이다. `dv01(bond, ytm)`은 yield 기반이다(코드로 확인됨).

## 코드 추적표
| 단계 | 파일:함수:라인 | 내용 |
|---|---|---|
| 입력 필드 | `ui/bonds_page.py:build_bonds_page:77-83` | `CTD DV01 / contract` 기본값 "65", `Conversion factor` 기본값 "0.8", `Position DV01 (blank = calculator)` 공란. 단위·hint·tooltip 없음 |
| 도구 전환 | `ui/bonds_page.py:on_tool:87-89` | `hedge_row.visible`만 토글한다. 입력값은 유지된다 |
| 숫자 파싱 | `ui/bonds_page.py:_num:38-49` | 공란이면 default를 쓴다. 'abc', 'nan', 'inf', '1e400'이면 필드 이름을 넣은 ValueError를 낸다. "0"은 0.0이다(공란과 구분됨) |
| 채권·곡선 | `ui/bonds_page.py:worker:107-113` | hedge 도구도 항상 Bond를 만들고 `load_treasury_curve`, `analyze_bond`를 부른다 |
| 헤지 입력 | `ui/bonds_page.py:worker:116-118` | `_num(pos_dv01, a.dv01)`, `_num(ctd_dv01, 65.0)`, `_num(cf, 1.0)`, 그리고 `futures_hedge_ratio` |
| 표시 | `ui/bonds_page.py:worker:191-211` | 타일 6개, notice(공식과 잔여 DV01), 해설, AI payload(`contracts`만 있고 rounded·residual은 없음) |
| 오류 | `ui/bonds_page.py:worker:219-222` | FICCError·ValueError는 문구 그대로, 그 밖의 예외는 `Type: msg`로 notice에 띄운다 |
| 핵심 식 | `core/ficc/bonds.py:futures_hedge_ratio:323-329` | `ctd<=0 or cf<=0`만 검사한다. NaN·inf·overflow는 검사하지 않는다 |
| Position DV01 기본값 | `core/ficc/bonds.py:dv01:137-141`, `modified_duration:126`, `analyze_bond:231-253` | D_mod × P/100 × notional × 1bp. yield DV01이고 곡선과 무관하다 |
| 기존 테스트 | `tests/ficc_acceptance.py:297-298`, `core/ficc/bonds.py:402` | 산술 한 건만 검사한다(800·0.8/65) |
| 다른 화면 | `ui/structuring_page.py:231,267`, `core/ficc/structured.py:hedge_sheet:386-424` | "Futures DV01 / contract"를 CF 없이 그대로 쓴다(D-09) |

## ② 심각도별 이슈
| ID | 심각도 | 상태 | 위치 | 한 줄 요약 |
|---|---|---|---|---|
| D-01 | P2 | 테스트로 확인됨 | `ui/bonds_page.py:199-209` | 숏 포지션에서 "Contracts to sell -9.82", "Sell ... flatten a long position" |
| D-02 | P2 | 테스트로 확인됨 | `ui/bonds_page.py:117` | CTD·CF 공란이 65.0·1.0으로 조용히 대체된다. CF 기본값이 필드 초기값 0.8과 다르다 |
| D-03 | P2 | 코드로 확인됨 + 테스트로 확인됨 | `ui/bonds_page.py:77-83,202-206,233-235`; `README.md:96-98` | 근사라는 점, CTD DV01 단위, 예시값이라는 점, 미반영 항목을 고지하지 않는다 |
| D-04 | P3 | 테스트로 확인됨 | `ui/bonds_page.py:194-211` | 잔여 DV01 부호 설명이 없다. 잔여 타일이 없다. payload에 rounded·residual이 없다. override 여부가 표시되지 않는다 |
| D-05 | P3 | 테스트로 확인됨 | `ui/bonds_page.py:200,205,209` | `round()`가 half-to-even이다. 10.50이 10, 8.50이 8이 된다 |
| D-06 | P3 | 테스트로 확인됨 | `ui/bonds_page.py:194,203` | Position DV01을 소수 0자리로 표시한다. 표시된 식을 손으로 재계산하면 다른 값이 나오는 경우가 30%다 |
| D-07 | P3 | 테스트로 확인됨 | `core/ficc/bonds.py:327-329`; `ui/bonds_page.py:198-200` | overflow가 나면 "OverflowError" 문구가 뜬다. 비현실적인 CF를 경고하지 않는다. core가 NaN을 통과시킨다 |
| D-08 | P3 | 테스트로 확인됨 | `ui/bonds_page.py:107-113` | Position DV01을 직접 넣어도 채권 입력과 곡선 로드가 실패하면 헤지가 막힌다 |
| D-09 | P3 | 코드로 확인됨 | `ui/structuring_page.py:231`; `ui/bonds_page.py:77,198` | 같은 숫자 "65"가 두 화면에서 다른 뜻이다 |

## ③ 재현 단계
1. 사본을 만든다: `git -C /home/user/quantgen archive HEAD | tar -x -C <dir>`. 지정된 캐시 CSV 4개는 열지 않고 지웠다.
2. 독립 계산: `python3 -B -I indep_hedge.py <base> indep_hedge_out.json`. 결과는 `indep_hedge.log`에 있다.
3. 화면 구동 32케이스: `python3 -B -I ui_drive_hedge.py <base|fixed> ui_drive_<x>.json`. 결과는 `ui_drive_base.log`, `ui_drive_fixed.log`에 있다. 곡선은 synthetic이다. FRED 케이스는 `_fred_fetch`를 예외를 내는 stub으로 바꿨다. 캐시는 scratch 폴더를 썼다.
4. UI 회귀: `python3 -B -I ui_regression.py <base|fixed>`. 결과는 `ui_regression.log`에 있다.
5. 기존 테스트: `python3 -B -I run_subset.py <base|fixed>`로 `tests/ficc_acceptance.py`의 test_*를 프로세스 안에서 전부 돌렸다. `run_all.py`는 쓰지 않았다. 사본에서 `python3 -B -m core.ficc.bonds`, `python3 -B -m ui.bonds_page`도 돌렸다.
6. 화면에서 직접 재현하려면 Tool을 Futures hedge, Curve source를 Synthetic demo로 둔다.
   - D-01: Position DV01에 `-798.19`를 넣고 Run.
   - D-02: Conversion factor를 지우고 Run.
   - D-05: Position DV01 `682.5`, CF `1`로 Run.
   - D-07: CTD DV01 `1e-320`로 Run.
   - D-08: Position DV01 `798`, Price `100`, Yield `4.5`로 Run.

## ④ 수식 및 독립 계산
### 4.1 Position DV01(공란일 때) = 계산기 채권의 yield DV01
- 독립식(par 채권, n = 20기): D_mod = (1/y)·(1 − (1+y/2)^−20) = 7.9818561850. 가격은 100.0000000000 이다.
- DV01 = D_mod × P/100 × N × 1e-4 = **798.185618**
- 독립 중앙차분(±1bp, 직접 짠 가격식): 798.185750. 차이 1.3e-4는 2차 항 때문이다.
- 저장소 `analyze_bond(...).dv01` = 798.185618. 독립 해석식과의 차이는 1.1e-12 이다.
- Notional 5,000,000이면 3,990.93이 된다(화면 구동 23번). 공란 fallback은 그 순간 입력된 Coupon, Maturity, Freq, Price 또는 Yield, Notional을 쓴다.

### 4.2 화면 2.4 독립 계산
| 항목 | 798 (손계산 입력) | 798.185618 (화면 내부값) | 화면 표시 |
|---|---|---|---|
| Futures DV01 = 65/0.8 | 81.25 | 81.25 | 81.25 |
| n = pos × CF / CTD | 9.821538 | 9.823823 | 9.82 |
| Rounded | 10 | 10 | 10 |
| 잔여 = pos − 10 × 81.25 | −14.50 | **−14.3144** | -14 |
| 9계약일 때 잔여 | +66.75 | +66.94 | (표시 없음) |
| 11계약일 때 잔여 | −95.75 | −95.56 | (표시 없음) |

### 4.3 부호 규약
- DV01은 롱이 양수다(`bonds.py:15`).
- 잔여 = 헤지 후 순 DV01 이다. 양수면 아직 롱(헤지 부족)이다. 음수면 과헤지(순 숏)다.
- 숏 포지션(−798.19)이면 n = −9.8239 이고 `round`는 −10 이다. 잔여는 +14.31 이다. 수학적으로 일관된다. 매수 10계약이 맞는 답이다. 문제는 문구다(D-01).

### 4.4 반올림 탐침 (Python `round` 대 half-up)
| n | 화면 Rounded(`round`) | half-up | 잔여(화면) | 잔여(half-up) |
|---|---|---|---|---|
| 9.50 (617.5, CF 1) | 10 | 10 | −32.5 | −32.5 |
| 10.50 (682.5, CF 1) | **10** | 11 | +32.5 | −32.5 |
| 8.50 (552.5, CF 1) | **8** | 9 | +32.5 | −32.5 |
| −9.50 | −10 | −10 | +32.5 | +32.5 |

정확히 .5일 때는 두 규칙 모두 |잔여|가 같다. 경제적 차이는 없다. 표시 기대와 어긋날 뿐이다.

### 4.5 이 DV01 헤지가 표준 근사로 성립하는 조건 (CME BPV 헤지비율과 같은 식)
1. 선물 가격이 CTD 선도가격 / CF 를 따라간다. 즉 net basis가 거의 일정하다. 그러면 dF ≈ dP_CTD / CF 이고 Futures DV01 ≈ CTD DV01 / CF 이다.
2. 금리 변동 중 CTD가 바뀌지 않는다. 전환점 근처에서는 선물 DV01이 섞이고 인도 옵션 때문에 음의 볼록성이 생긴다.
3. 헤지 대상 채권과 CTD의 수익률이 같은 bp만큼 움직인다(yield beta 1). 그렇지 않으면 n = pos DV01 × β × CF / CTD DV01 이다. 예: β = 0.9이면 10계약 후 잔여는 798.19 − 10 × 81.25 × 0.9 = +66.94 이다(가정 예시). 10년물을 ZN(CTD 약 6.5~7.5년)으로 헤지하면 곡선 기울기 위험이 남는다.
4. 작은 변동에서의 1차 근사다. DV01이 바뀌면 다시 헤지해야 한다.
5. 단위가 맞아야 한다.
   - Position DV01은 포지션 전체의 통화/bp 이다.
   - "CTD DV01 / contract"는 **선물 1계약 액면에 해당하는 CTD의 통화/bp** 여야 한다. 예: CME ZN·ZF·ZB 액면 $100,000, 2년물(ZT) $200,000. 이 사양은 검색 결과로만 봤고 원문 사양서와 대조하지 않았다(미확인). 출처는 [CME 10-Year T-Note contract specs](https://cmegroup.com/trading/interest-rates/us-treasury/10-year-us-treasury-note_contractSpecs_futures.html), [CME Understand Treasuries Contract Specifications](https://www.cmegroup.com/education/courses/introduction-to-treasuries/understand-treasuries-contract-specifications.html) 이다.
   - 액면 100당 DV01 0.065를 넣으면 계약 수가 1,000배(약 9,824)가 된다. UI는 이 단위를 말하지 않는다(D-03).
6. 엄밀히는 CTD의 인도일 기준 forward DV01을 써야 한다. 현물 DV01은 이를 조금 과대평가한다. 이 차이는 반영하지 않는다.
7. 반영하지 않는 것: CTD 변경, gross/net basis와 repo, 인도 옵션(quality, timing, wildcard, end-of-month), invoice price(= 선물가 × CF + 경과이자), variation margin tail.
   - UI(`bonds_page.py`), 모듈 docstring(`bonds.py:1-22`), README(`README.md:96-98`) 어디에도 이런 고지가 없다. grep으로 "100,000", "basis", "delivery", "invoice"를 찾아봤고 해당하는 내용이 없었다.
   - basis에 관한 설명은 research note(`research_notes/QUANTGEN asset coverage expansion/bonds_commodities.md:131-140`)에만 있다.

### 4.6 입력 경계 (HEAD 화면 구동 결과)
| 입력 | HEAD 화면 결과 |
|---|---|
| CTD 0 / −65 | "CTD DV01 per contract and conversion factor must be positive." |
| CTD 공란 | 65.0을 조용히 사용한다. 결과는 기본값과 같다 |
| CTD 'abc' / 'nan' / 'inf' | "CTD DV01 / contract: 'abc' is not a number." |
| CTD 1e-320 | "OverflowError: cannot convert float infinity to integer" |
| CF 0 / −0.8 | positive 오류 |
| CF 공란 | **CF 1.0000, Futures DV01 65.00, 12.28 → 12, 잔여 +18** |
| CF 'abc' | "Conversion factor: 'abc' is not a number." |
| CF 1e-300 | Futures DV01 타일이 300자리가 넘는 숫자다. CF는 "0.0000", 계약 0.00, 잔여 +798 |
| CF 1e6 | 12,279,779계약. 경고 없음 |
| pos 0 | 0계약, 잔여 +0 |
| pos 1e9 | 12,307,692계약, 잔여 +25 |
| pos 1e308, CF 2 | OverflowError 문구 |
| pos ' 1,000 ' | 1,000으로 처리된다(쉼표와 공백 허용) |

모든 경우에 진행 링이 멈추고 화면은 죽지 않는다.

## ⑤ 수정안 (사본에서만 적용·시험했다. 저장소에는 적용하지 않았다)
`fix.diff`(+/− 131줄)의 요지는 다음과 같다.
1. `core/ficc/bonds.py`
   - `futures_hedge_ratio`에 유한성 검사와 overflow 검사를 넣는다.
   - 새 `FuturesHedge`/`futures_hedge`를 만든다. 계약 수, futures DV01, rounded(0.5는 0에서 먼 쪽으로), 잔여 DV01을 한곳에서 계산한다.
2. `ui/bonds_page.py`
   - CTD와 CF를 필수 입력으로 바꾼다(공란이면 오류).
   - 두 필드에 hint와 tooltip을 단다: 계약 액면당, 사용자 입력이며 시장 데이터가 아님.
   - 부호에 따라 "Contracts to sell/buy"를 쓰고 절대값을 보인다.
   - "Residual DV01" 타일을 추가한다.
   - Position DV01과 공식을 소수 2자리로 보인다.
   - notice에 잔여 상태(still long / over-hedged / flat)와 근사·미반영 항목을 쓴다.
   - CF가 0.1~2 밖이면 경고한다.
   - payload에 side, rounded, residual_dv01, futures_dv01을 넣는다.
   - 자체 검사에 assert 1개를 추가한다.
3. `tests/ficc_acceptance.py`: 화면 케이스, 반올림, 부호, 방어 입력을 검사하는 `test_futures_hedge_screen_case_rounding_residual_and_sign`을 추가한다.

핵심 hunk는 다음과 같다.
```diff
-                    pos, ctd, c = _num(pos_dv01, a.dv01), _num(ctd_dv01, 65.0), _num(cf, 1.0)
-                    hedge = (pos, ctd, c, futures_hedge_ratio(pos, ctd, c))
+                    ctd, c = _num(ctd_dv01), _num(cf)
+                    if ctd is None or c is None:
+                        raise ValueError("CTD DV01 / contract and Conversion factor are required.")
+                    hedge = futures_hedge(_num(pos_dv01, a.dv01), ctd, c)
...
-                        stat("Contracts to sell", f"{n:,.2f}", token="accent"),
-                        stat("Rounded", f"{round(n):,d}"),
+                        stat(f"Contracts to {side}", f"{abs(h.contracts):,.2f}", token="accent"),
+                        stat("Rounded", f"{abs(h.rounded):,d}", tooltip="Halves away from zero"),
+                        stat("Residual DV01", f"{h.residual_dv01:+,.2f}", ...),
```
```diff
+    vals = (position_dv01, ctd_dv01_per_contract, conversion_factor)
+    if not all(math.isfinite(v) for v in vals):
+        raise ValueError("Position DV01, CTD DV01 and conversion factor must be finite.")
...
+    n = position_dv01 * conversion_factor / ctd_dv01_per_contract
+    if not math.isfinite(n):
+        raise ValueError("Hedge ratio overflows; check the DV01 and conversion-factor scales.")
+    k = int(math.copysign(math.floor(abs(n) + 0.5), n))   # in futures_hedge
```
수정 전후 같은 입력 비교(기본 입력):
- HEAD: "798 x 0.8000 / 65.00 = 9.82 ... residual -14 per bp"
- 수정본: "798.19 x 0.8000 / 65.00 = 9.82: sell 10. Residual after rounding -14.31 per bp (over-hedged, net short). DV01 approximation ... not modelled."

계산값은 그대로다(n 9.823823, rounded 10).

diff에 넣지 않은 제안:
- D-08: Position DV01을 직접 넣은 hedge는 채권 생성과 곡선 로드를 건너뛴다.
- D-09: Structuring 라벨을 "Futures DV01 / contract (= CTD DV01 / CF)"로 바꾼다.
- README Bonds 절에 근사 한계를 한 줄 더한다.

## ⑥ 테스트 로그 (PASS / FAIL / NOT_RUN)
| 테스트 | base (HEAD) | fixed | 로그 |
|---|---|---|---|
| `python3 -B -m core.ficc.bonds` 자체 검사 | PASS | PASS | selfcheck.log, selfcheck_fixed.log |
| `python3 -B -m ui.bonds_page` 자체 검사 | PASS | PASS(새 assert 포함) | 같음 |
| `tests/ficc_acceptance.py` 전체 test_*, 프로세스 안에서 실행 | 57/57 PASS | 58/58 PASS | ficc_acceptance_base.log, ficc_acceptance_fixed.log |
| 새 acceptance 테스트를 HEAD 코드에서 실행 | FAIL (AttributeError, 예상대로) | (위 표에서 PASS) | new_test_on_base.log |
| UI 회귀 R1~R9 (11개) | 0 PASS / 11 FAIL (이 FAIL들이 발견 사항이다) | 11 PASS | ui_regression.log |
| 독립 대 저장소 비교 (DV01, n, 무작위 20,000건) | 일치 (1.1e-12, 3.3e-16) | - | indep_hedge.log |
| 화면 구동 32케이스 | 기록됨 | 기록됨 | ui_drive_base.log, ui_drive_fixed.log |
| `tests/run_all.py` | NOT_RUN (금지 규칙) | NOT_RUN | - |
| 실제 Flet 창 클릭 | NOT_RUN | NOT_RUN | - |
| 실제 FRED 곡선에서의 hedge | NOT_RUN (offline stub만) | NOT_RUN | - |

성능 참고: UI 회귀 1회(Run 약 35번, synthetic 곡선)의 총 소요는 3.3~3.7초다. Run 한 번에 약 0.1초다. 프로세스 시작 시간이 포함되어 있다.

## ⑦ 남은 리스크
- 앱에는 CTD나 CF 데이터가 없다. 65와 0.8은 실제 어떤 계약의 값과도 연결되지 않은 예시값이다. 결과가 시장에서 정확한지는 미확인이다.
- 계약 액면($100,000, $200,000)은 웹 검색 결과로만 확인했다. CME 원문 사양서와 대조해야 한다.
- basis, CTD 변경, yield beta로 생기는 헤지 오차를 정량화하지 않았다.
- KTB 국채선물은 현금결제이고 CF가 없다. 이 식을 그대로 적용할 수 없다. 현재 화면은 UST 전제다.
- 실제 GUI 클릭 시험과 실제 FRED 경로에서의 hedge는 실행하지 않았다.
- 수정안은 저장소에 적용하지 않았다. 적용 여부는 소유자가 결정한다.

## 스크립트와 산출물
폴더는 `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/D_futures_hedge/` 이다.
- 스크립트: `indep_hedge.py`, `ui_drive_hedge.py`, `ui_regression.py`, `run_subset.py`, `apply_fix.py`, `new_test_on_base.py`
- 산출물: `fix.diff`, `indep_hedge_out.json`, `ui_drive_base.json`, `ui_drive_fixed.json`, 그리고 위의 `*.log` 파일들

### 독립 검증

- 기준: 현재 HEAD는 `8159532`다. 조사자가 본 `078981a`과의 차이는 감사 보고서 md 한 개뿐이다. `ui/bonds_page.py`, `core/ficc/bonds.py`, `tests/ficc_acceptance.py`의 diff는 비어 있다. 저장소는 바꾸지 않았다(`git status` 0줄).
- 사본: `git archive HEAD`로 `base`와 `fixed`를 직접 만들었다. 캐시 CSV 4개는 열지 않고 지웠다. `fixed`에는 조사자의 `fix.diff`를 적용했다. 적용 결과는 조사자의 `fixed` 사본과 바이트까지 같았다(CRLF 보존).
- 독립 재계산(직접 짠 가격식, 저장소 함수 미사용):
  - 기본 채권 DV01: 해석식 798.1856184988, ±1e-6 중앙차분 798.1856186277이다. 저장소 `analyze_bond().dv01`는 798.1856184987964로 해석식과 일치한다.
  - n(화면): 9.823822996908이다. n(798 손입력): 9.821538461538이다. 요청서의 9.815는 오기다.
  - 잔여: 10계약 −14.3143815, 9계약 +66.9356185.
  - 쿠폰 0%, YTM 0.75%: DV01 924.4071, n 11.3773(화면 "11.38")이다. 표시된 924로 손계산하면 11.3723("11.37")이다.
  - Notional 5,000,000: DV01 3,990.928.
  - 격자 1,640개를 독립 구현으로 돌렸다. 표시 계약 수와 손계산 불일치는 491건(29.9%)이다. 조사자 수치와 같다.
- 화면 구동: stand-in Page로 23케이스를 돌렸다(`vdrive_base.log`, `vdrive_fixed.log`). D-01, D-02, D-05, D-07, D-08 화면 문구를 모두 그대로 재현했다.
- 테스트 로그(`vtests.log`, `vui_regression.log`):
  - ficc_acceptance: base 57/57 PASS, fixed 58/58 PASS.
  - 자체 검사 `-m core.ficc.bonds`, `-m ui.bonds_page`: 양쪽 모두 PASS.
  - UI 회귀 11개: base 0/11, fixed 11/11.
  - 새 acceptance 테스트를 base 코드에서 돌리면 FAIL이다. 원인은 AttributeError(`futures_hedge` 없음)뿐이다.
  - `tests/run_all.py`, 실제 Flet 창 클릭, 실제 FRED 경로는 NOT_RUN이다.

| id | 유지 여부 | 정정 심각도 | 정정 상태 | 근거 |
|---|---|---|---|---|
| D-01 | 유지 | P2 | 테스트로 확인됨 | Position DV01 −798.19를 넣었다. 화면은 'Contracts to sell -9.82', 'Rounded -10', "Sell that many to flatten a long position ... +14"이다. `Bond`가 notional<=0을 거부한다(`bonds.py:55`). 그래서 숏은 override로만 들어온다. 부호 붙은 수치는 맞고 문구만 틀리므로 P2가 맞다. 수정본은 'Contracts to buy 9.82 / Rounded 10 / Residual +14.31'이다. 단, 회귀 테스트 R2는 scratch에만 있고 CI에 없다(M-4). |
| D-02 | 유지 | P2 | 테스트로 확인됨 | CF를 비우면 'CF 1.0000, Futures DV01 65.00, 12.28, Rounded 12, +18'이다. CTD를 비우면 65.0이 조용히 쓰인다. 수정본은 "...are required." 오류를 낸다. R4는 base FAIL, fixed PASS다. 다만 CI에 들어가는 테스트는 없다(M-4). |
| D-03 | 유지 | P2 | 코드로 확인됨(+화면 구동으로도 확인) | `bonds_page.py:77-83`에 hint와 tooltip이 없다. notice(:202-206)와 README:96-98에 근사·단위 고지가 없다. CTD 0.065를 넣으면 9,823.82계약(1,000배)이 경고 없이 나온다(케이스 17). 수정본도 이 단위 오입력은 막지 못한다(M-2). |
| D-04 | 유지 | P3 | 테스트로 확인됨 | notice는 'residual after rounding is -14 per bp.'뿐이다. payload.hedge 키는 4개다(`:210-211`). |
| D-05 | 유지 | P3 | 테스트로 확인됨 | 682.5/CF 1이면 '10.50 → Rounded 10', 552.5면 '8.50 → 8'이다. 수정안의 `floor(|n|+0.5)`에는 부동소수 결함이 있다. 또 2자리 표시와 어긋나는 문제가 남는다(M-1). |
| D-06 | 유지 | P3 | 테스트로 확인됨 | 독립 격자에서 491/1,640(29.9%)을 재현했다. 예: '924 x 0.8000 / 65.00 = 11.38'. 수정은 Position DV01만 2자리로 바꾼다. CTD DV01은 여전히 2자리라서 0.065가 '0.07'로 보인다. 그러면 공식을 재현할 수 없다(M-2). |
| D-07 | 유지 | P3 | 테스트로 확인됨 | CTD 1e-320과 pos 1e308/CF 2는 'OverflowError: cannot convert float infinity to integer'를 낸다. CF 1e-300이면 300자리가 넘는 Futures DV01 타일이 나온다. core는 nan과 inf를 그대로 반환한다. 수정본은 앞의 두 경우에 'Hedge ratio overflows'를 내고 CF 경고를 띄운다. |
| D-08 | 유지 | P3 | 테스트로 확인됨 | override 798에 Price와 Yield를 함께 넣으면 'Give exactly one...'이다. FRED offline stub에 override 798이면 'FRED served 0/11 tenors'이고 헤지가 나오지 않는다. |
| D-09 | 유지 | P3 | 코드로 확인됨 | `structured.py:420`은 `n = dv01 / futures_dv01_per_contract`로 CF가 없다. `ui/structuring_page.py:231` 라벨은 'Futures DV01 / contract'다. 같은 '65'가 Bonds에서는 CTD DV01이다(798/65=12.28 대 9.82). 참고로 Structuring 쪽은 매수/매도 부호를 문구에 반영한다. Bonds만 고정 'sell'이다. |

수정안 검토 요약:
- 공식과 계산값은 바뀌지 않는다(n 9.823823, rounded 10).
- `fix.diff`는 그대로는 적용되지 않는다(M-5).
- 반올림 구현에 작은 결함이 있다(M-1).
- CTD 스케일 방어가 없다(M-2).
- UI 회귀가 CI 밖에 있다(M-4).
- 이 넷을 빼면 최소 수정으로 타당하다. 조사자 해설(부호 규약, 9·11계약 잔여, β 예시 +66.94, CME 액면 $100k/$200k는 미확인, KTB는 현금결제)에서 오류는 찾지 못했다.

### 조사자가 놓친 항목

**M-1 (P3, 테스트로 확인됨) 수정안 `futures_hedge`의 반올림 결함**
- 위치: fix.diff `core/ficc/bonds.py` `futures_hedge`의 `k = int(math.copysign(math.floor(abs(n) + 0.5), n))`. 표시는 `ui/bonds_page.py` 수정본의 `f"{abs(h.contracts):,.2f}"`.
- 재현:
  - fixed 사본에서 `futures_hedge(0.49999999999999994, 1, 1)`은 rounded 1, residual −0.5이다. 내장 `round`는 0이다. 0계약이면 |잔여|가 0.49999로 더 작다.
  - `futures_hedge(2**52+1, 1, 1)`은 rounded 4503599627370498이다. 정답은 …497이다.
  - 화면에서 Position DV01 682.1815, CF 1이면 'Contracts to sell 10.50', 'Rounded 10'이다. 그런데 tooltip은 'Halves away from zero'라고 한다.
- 원인: `x+0.5`의 부동소수 반올림. 그리고 표시 2자리와 반올림 기준(미반올림 n)이 서로 다르다.
- 영향: 극단 경계에서만 생긴다. 경제적 영향은 거의 없다. 다만 수정의 목적(표시와 일치)을 완전히는 못 이룬다.
- 수정: `f = math.floor(abs(n)); k = int(math.copysign(f + (abs(n) - f >= 0.5), n))`로 쓴다. `x - floor(x)`는 정확하다. tooltip은 'rounded from the unrounded ratio'로 바꾸거나 n을 3자리 이상 보인다.
- 회귀 테스트: `futures_hedge(0.49999999999999994,1,1).rounded == 0`, `futures_hedge(2**52+1,1,1).rounded == 2**52+1`. 현재 수정본에서 FAIL, 고친 뒤 PASS.

**M-2 (P3, 테스트로 확인됨) CTD DV01 표시 정밀도와 스케일 방어 부재(수정본에도 남음)**
- 위치: `ui/bonds_page.py:196,198,203` (`f"{ctd:,.2f}"`, `f"{ctd / c:,.2f}"`). 수정본에서도 같다.
- 재현: CTD DV01 `0.065`(액면 100당 단위 오입력)로 Run.
  - HEAD: 'CTD DV01 / contract 0.07', 'Futures DV01 0.08', '798 x 0.8000 / 0.07 = 9,823.82', 'Rounded 9,824', 잔여 '-0'.
  - 수정본: '798.19 x 0.8000 / 0.07 = 9,823.82', 잔여 '-0.01'. 경고가 없다. 수정본의 경고는 CF 범위(0.1~2)뿐이다.
- 기대: 표시된 숫자로 공식을 재현할 수 있어야 한다(798.19×0.8/0.07 = 9,122이지 9,823이 아니다). 1,000배 단위 오입력은 경고해야 한다.
- 원인: CTD를 고정 2자리로 표시한다. futures DV01 크기를 검사하지 않는다.
- 영향: D-03이 말한 1,000배 오류가 수정 후에도 조용히 남는다.
- 수정: CTD와 Futures DV01을 `:,.4g`로 표시한다. futures DV01(=CTD/CF)이 계약당 대략 10~500(통화/bp) 밖이면 'per contract face?' 경고 notice를 띄운다. 이 범위는 추정이다. ZT·ZN·ZB 실제 DV01 범위와 대조하지 않았으므로 미확인이다.
- 회귀 테스트: CTD '0.065' 입력 시 경고 notice가 있어야 하고 notice 공식에 '0.065'가 보여야 한다. HEAD와 현 수정본 모두 FAIL이다.

**M-3 (P3, 코드로 확인됨; 시장 사실은 미확인) 기존 감사 FC-03의 제안 'Bonds 헤지에 KTB 선물 연결'이 현재 식과 맞지 않는다**
- 위치: `docs/audit/2026-10-27/functional_completeness.md:146`("Bonds 헤지에 KTB 선물(`A65…`)을 연결", 미적용 제안). 식은 `core/ficc/bonds.py:323-329`.
- 근거:
  - Bonds 헤지는 '선물 DV01 = CTD DV01 / CF'를 전제한다.
  - KRX KTB 선물은 현금결제다. 바스켓 평균 수익률로 가격을 정하고 CF가 없다. 이 사실은 일반 지식이며 KRX 사양서와 대조하지 않았다(미확인).
- 영향: 제안대로 구현하면 CF 입력이 무의미해진다. 계약 수가 틀려진다.
- 수정: FC-03 제안에 단서를 단다. KTB 선물은 선물가격식으로 DV01을 직접 계산하고 CF 경로를 쓰지 않는다. 화면에 'UST 실물인도 선물 전제'를 적는다.
- 회귀 테스트: KTB 연결을 구현할 때 KTB 경로에서 CF 입력을 받지 않는지, 선물가격식 DV01과 유한차분이 일치하는지 검사한다.

**M-4 (P3, 코드로 확인됨) UI 결함의 회귀 테스트가 CI에 없다**
- 위치: `tests/run_all.py:45`(ficc는 `tests.ficc_acceptance.tests`만 돈다), `tests/expansion_acceptance.py:323-345`(`ui/bonds_page.py` self-check는 없다), fix.diff의 `ui/bonds_page.py` `__main__` assert 1개.
- 재현:
  - 새 acceptance 테스트를 HEAD에서 돌리면 FAIL한다. 그러나 원인은 `AttributeError: futures_hedge`뿐이다. D-01 문구, D-02 공란 기본값, D-07 UI 문구 결함을 직접 검사하지 않는다.
  - R2, R4, R5, R8은 scratch `ui_regression.py`에만 있다.
- 영향: 수정이 들어가도 D-01과 D-02가 회귀하면 CI가 잡지 못한다. 수용 기준 '회귀 테스트: CI에서 실행'을 충족하지 못한다. FC-06(페이지 self-check 8개가 run_all 밖)과 같은 원인이다. 헤지 수정에 특정된 공백이다.
- 수정:
  - R2, R4, R5, R8을 `ui/bonds_page.py` self-check에 assert로 옮긴다.
  - `_selfcheck("ui/bonds_page.py")`를 `tests/expansion_acceptance.py:tests()`에 등록한다. 이것은 FC-06 수정과 같이 진행한다.
- 회귀 테스트: 등록 후 HEAD 코드에서 FAIL하고 수정본에서 PASS해야 한다.

**M-5 (P3, 테스트로 확인됨) 산출물 `fix.diff`가 그대로는 적용되지 않는다**
- 위치: `core/ficc/bonds.py`는 git에서 CRLF다(`git ls-files --eol`: i/crlf). `.gitattributes`는 `* -text`이고 "Byte-exact: ... never convert line endings" 규칙이 있다.
- 재현: pristine 사본에서 실행한다.
  - `git apply --check -p1 fix.diff`의 결과는 "patch failed: core/ficc/bonds.py:323"이다.
  - `patch --dry-run`의 결과는 "Hunk #1 FAILED (different line endings)"이다.
- 원인: diff가 LF로 정규화되어 있다. 조사자의 `apply_fix.py`는 CRLF를 보존해서 시험은 정상이었다. 하지만 소유자에게 넘길 diff는 적용이 실패한다. 강제로 적용하면 줄끝이 섞인다.
- 수정: CRLF를 보존한 diff를 다시 만든다(`diff --strip-trailing-cr` 금지, `git diff --binary` 사용). 또는 `apply_fix.py`를 공식 적용 수단으로 명시한다.
- 회귀 테스트: pristine 사본에서 `git apply --check`가 0으로 끝나야 한다. 적용 후 `file core/ficc/bonds.py`가 'CRLF'여야 한다.

산출물 폴더는 `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/verify_D_futures_hedge/`이다. 파일은 vdrive.py, vdrive2.py, vdrive_base.log/json, vdrive_fixed.log/json, vgrid.py, vgrid.log, vrun_acc.py, vui_regression.py, vui_regression.log, vtests.log다.
