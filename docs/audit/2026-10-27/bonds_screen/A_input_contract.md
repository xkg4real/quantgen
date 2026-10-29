# Bonds 화면 검증 A. 가격–YTM 입력 계약과 UI 상태

> 작성 메모 (오케스트레이터): 하네스가 하위 에이전트의 보고서 파일 쓰기를 막아, 조사 에이전트가 반환한 본문과 독립 검증자가 반환한 검증 절을 내용 변경 없이 옮겼습니다. 저장소 코드는 바꾸지 않았습니다.

## A. 가격–YTM 입력 계약과 UI 상태 (A_input_contract)

### 0. 범위와 방법
- 대상: 요청서 3.A, 2.2, 3.F 마지막 항목, 4절 1행. 표 2.1에 대한 단서도 다룬다("가격 입력 100"인데 화면 가격이 107.982 또는 92.386인 행).
- 저장소의 추적 파일은 바꾸지 않았다. 실험은 모두 `git archive HEAD` 사본에서 했다. 사본 두 개를 썼다. `repo_copy`는 HEAD 그대로이고, `repo_fix`에는 수정안을 넣었다. 끝난 뒤 `git status --porcelain` 출력은 비어 있었다.
- 화면 구동 방식은 모듈 자체 검사(`ui/bonds_page.py:247-319`)와 같다. 대체 Page는 `SimpleNamespace(run_thread=lambda fn: fn(), update=lambda: None)`이고 Curve source는 synthetic이다. 실제 `build_bonds_page`가 만든 컨트롤을 그대로 누르고 읽는다. 동시성 검사(a04)에서만 실제 스레드를 쓴다.
- 숫자는 두 가지로 다시 계산했다. 교과서 공식으로 직접 짠 구현(a03)과 저장소 함수다. 둘을 비교했다.
- 실제 Flet GUI는 띄우지 않았다(NOT_RUN). FRED 경로도 실행하지 않았다(NOT_RUN, E 차원).

### ① 요약
1. 둘 다 채운 상태에서 새로 Run을 누르면 107.982도 92.386도 나올 수 없다. `analyze_bond`가 `ValueError("Give exactly one of price or ytm.")`를 내고(`core/ficc/bonds.py:236-237`), `run()`이 먼저 결과 영역을 비우기 때문이다(`ui/bonds_page.py:96`). 테스트로 확인됨.
2. 표 2.1의 1·2행이 표시한 6개 지표(가격, 수익률, Macaulay, Modified, Convexity, DV01)는 모두 **Yield 모드에서 Price를 비운 채 실행한 결과**와 소수 자리까지 같다. Price=100 가격 모드의 결과와는 다르다. 따라서 그 화면은 이전 Run의 결과다. 그 Run 뒤에 Price 칸에 100이 들어갔다. 대체 Page에서 이 순서를 그대로 재현했다(Price='100', 화면 107.982 / 7.92y / 7.74 / 73.0 / 836). 화면에는 결과가 낡았다는 표시가 없다(A-01, P1).
3. 입력 계약의 핵심은 맞다. `_num`은 빈칸, 공백, None을 "없음"으로 본다. '0'과 '0.0'은 0으로 본다. 그래서 0% 수익률이 정상 계산된다(쿠폰 4.5%면 가격 145.000, 독립 계산 145). NaN, Inf, '1e400', 'abc', '4.5%'는 필드 이름과 함께 거부한다.
4. 그러나 이런 결함이 있다.
   - 입력을 바꾸거나 도구를 바꿔도 이전 결과가 표시 없이 남는다(A-01, A-02).
   - Yield는 4.50으로 미리 채워져 있다. 그래서 Price만 입력해도 곧바로 "exactly one" 오류가 난다. 메시지는 내부 이름 "ytm"을 쓰고, 어느 칸을 비워야 하는지 말하지 않는다. 필드 단위 오류 표시도 없다(A-03).
   - 빈칸을 조용히 기본값으로 바꾼다. Coupon은 0%, Maturity는 10y, Notional은 1e6, CF는 1.0이 된다. CF 칸의 표시 기본값은 0.8인데 빈칸이면 1.0을 쓴다(A-04).
   - '4,5'를 45로 읽는다(A-05).
   - 먼저 시작한 느린 Run이 나중 결과를 덮어쓴다. 또 입력을 곡선 로드 전후 두 시점에 읽는다(A-06).
   - 극단 입력에서 원시 예외나 엉뚱한 해법 메시지가 나온다(A-07, A-08).
5. 수정안: "Quote by" 선택기를 두고 비활성 칸은 끈다. 필드 단위 오류를 보인다. 입력이 바뀌면 낡은 결과 배너를 띄운다. 입력은 클릭 시점에 한 번만 읽고, 실행 세대 번호를 둔다. 스크래치 사본에서 검증했다.
   - 페이지 구동: HEAD 11/34 PASS, 수정본 34/34 PASS.
   - 제안 회귀 테스트: HEAD 2/12, 수정본 12/12.
   - 기존 FICC 인수 테스트: 57/57 PASS(양쪽).
   - 같은 입력 8건의 타일 값은 수정 전후가 모두 같다.

### ② 심각도별 이슈
| ID | 심각도 | 상태 | 한 줄 |
|---|---|---|---|
| A-01 | P1 | 테스트로 확인됨 | 입력을 바꾸고 Run하지 않으면 이전 결과가 낡았다는 표시 없이 남는다. 표 2.1 1·2행이 바로 이 상태다 |
| A-02 | P2 | 테스트로 확인됨 | 도구를 바꿔도 이전 도구의 결과가 남는다. 헤지 입력은 숨겨진 채 헤지 결과만 보이는 경우도 있다 |
| A-03 | P2 | 테스트로 확인됨 | 가격/수익률 계약이 모호하다. Yield가 미리 채워져 있고, 오류 문구가 일반적이며, 필드 단위 오류가 없다 |
| A-04 | P2 | 테스트로 확인됨 | 필수 칸이 비면 조용히 기본값을 쓴다. CF 빈칸은 1.0인데 표시 기본값은 0.8이다 |
| A-05 | P2 | 테스트로 확인됨 | 쉼표를 모두 지운다. '4,5'가 45%로 읽혀 가격 11.554가 정상 결과처럼 나온다 |
| A-06 | P2 | 테스트로 확인됨 | 느린 이전 Run이 새 결과를 덮어쓴다. 입력을 두 시점에 읽는다(P01-05의 Bonds 사례) |
| A-07 | P2 | 테스트로 확인됨 | 정의역 가드가 없다. 만기 1e-10은 IndexError, 1e5는 scipy NaN 메시지가 난다. Yield 250%는 가격 해법 오류가 된다 |
| A-08 | P3 | 테스트로 확인됨 | 오류 문구가 사용자 단위와 필드 이름을 쓰지 않는다(coupon "-0.01", "ytm", "face and notional") |
| A-09 | P3 | 테스트로 확인됨 | Position DV01 수동값이 채권을 바꿔도 남는다. 타일 이름에 수동값이라는 표시가 없다 |

P0는 없다. 주문 경로가 없고 안전 규칙 위반도 찾지 못했다.

### ③ 재현 단계(요약, 전체는 findings 필드)
- A-01: Coupon 5.5, Yield 4.5, Price 빈칸으로 Run → 107.982. Price에 100을 입력하고 Run하지 않는다. 화면은 그대로 107.982 / 4.500% / 7.92y / 7.74 / 73.0 / 836이다. 화면 어디에도 stale 표시가 없다. 2행도 같다(Coupon 4.5, Yield 5.5 → 92.386 / 8.07y / 7.86 / 74.4 / 726).
- A-06: 첫 곡선 로드에 0.6초 지연을 넣었다(FRED 지연을 흉내 낸 것). Coupon 5.5로 Run하고, Coupon을 4.5로 바꿔 다시 Run한다. 두 번째 결과 100.000이 먼저 나오고 링이 사라진다. 그 뒤 첫 작업이 107.982로 덮어쓴다. 마지막 화면은 Coupon 칸 4.5, 가격 107.982다.

### ④ 수식 및 독립 계산
코드 추적:
| 단계 | 파일:함수:라인 | 동작 |
|---|---|---|
| 입력 파싱 | `ui/bonds_page.py:_num:38-49` | `strip().replace(",", "")`. 빈 문자열이면 default를 돌려준다. `float()`가 실패하거나 결과가 유한하지 않으면 `ValueError(f"{label}: {raw!r} is not a number.")` |
| 입력 위젯 | `ui/bonds_page.py:63-83` | Yield 값 "4.50", Price 빈칸. hint는 "blank = from yield"/"blank = from price". `on_change`는 하나도 없다 |
| 도구 전환 | `ui/bonds_page.py:on_tool:87-89` | `hedge_row.visible`만 바꾼다. 결과 영역은 그대로다 |
| Run | `ui/bonds_page.py:run:94-97` | 결과를 비우고 링을 켠 뒤 `page.run_thread(worker)`(`:224`). 버튼을 끄지 않고 재진입 검사도 없다 |
| 입력 읽기 1 | `ui/bonds_page.py:worker:105-109` | tool, Bond(coupon 기본 0.0, maturity 기본 10.0, notional 기본 1e6), `y=_num(ytm)` |
| 곡선 | `ui/bonds_page.py:110-111` | `load_treasury_curve`, `curve_from_snapshot`(FRED는 시리즈당 12초 타임아웃, `config.py:145`) |
| 입력 읽기 2 | `ui/bonds_page.py:112, 117` | `_num(price)`, `_num(pos_dv01, a.dv01)`, `_num(ctd_dv01, 65.0)`, `_num(cf, 1.0)`. 곡선 로드 **뒤**에 읽는다 |
| 계약 | `core/ficc/bonds.py:analyze_bond:236-241` | `(price is None) == (ytm is None)`이면 ValueError. `is None` 비교라서 0은 값으로 취급된다 |
| 도메인 | `core/ficc/bonds.py:Bond.__post_init__:48-57`, `yield_from_price:94-98`, `_check_ytm:75-77`, `z_spread:113-114`, `carry_roll:188` | 소수 단위로 된 메시지다. 수익률을 입력해도 `carry_roll`이 `yield_from_price`의 구간 [-0.5, 2.0]을 다시 탄다 |
| 현금흐름 | `core/ficc/curves.py:coupon_times:47`, `core/ficc/bonds.py:cashflows:71` | `maturity·freq < 1e-9`이면 n=0이 되고, `cf[-1]`에서 IndexError가 난다 |
| 출력 | `ui/bonds_page.py:216-222` | 성공하면 결과를 통째로 바꾼다. 예외는 `fail()`이 오류 notice 하나로 바꾼다(이전 결과를 지운다) |

공식(독립 구현 a03, 저장소를 import하지 않음). n = T·f, d = 1 + y/f, t_k = k/f.
P = Σ (c/f·100)/d^k + 100/d^n. Mac = Σ t_k·PV_k / P. Mod = Mac/d. Cvx = Σ t_k(t_k+1/f)PV_k / (d²P). DV01 = Mod·P/100·N·1e-4. y(P)는 [-0.49, 1.99]에서 이분법(200회)으로 푼다.

표 2.1 단서(쿠폰 연 c, 10년, 반기, N=1e6):
| 행 | 화면 | 독립: Yield 모드(Price 빈칸) | 독립: 가격 모드(Price=100 또는 95/105) | 일치 |
|---|---|---|---|---|
| 1 (c 5.5, Y 4.5, "P 100") | 107.982 / 4.500% / 7.92 / 7.74 / 73.0 / 836 | 107.981856 / 4.500% / 7.918984 / 7.744728 / 73.014818 / 836.29 | 100.000 / 5.500% / 7.823 / 7.614 / 71.15 / 761.36 | Yield 모드만 |
| 2 (c 4.5, Y 5.5, "P 100") | 92.386 / 5.500% / 8.07 / 7.86 / 74.4 / 726 | 92.386374 / 5.500% / 8.07203 / 7.855991 / 74.389791 / 725.79 | 100.000 / 4.500% / 8.161 / 7.982 / 76.21 / 798.19 | Yield 모드만 |
| 3 (c 5.5, Y 5.5, "P 100") | 100.000 / 5.500% / 7.82 / 7.61 / 71.2 / 761 | 100.000 / 7.823001 / 7.613626 / 71.152227 / 761.36 | 같음 | 둘 다(구분 불가) |
| 4 (c 5.5, P 95) | 95.000 / 6.178% / 7.76 / 7.52 / 69.9 / 715 | — | 95 / 6.1777% / 7.756345 / 7.523942 / 69.89157 / 714.77 | 가격 모드 |
| 5 (c 5.5, P 105) | 105.000 / 4.863% / 7.88 / 7.70 / 72.3 / 808 | — | 105 / 4.8627% / 7.884504 / 7.697355 / 72.339029 / 808.22 | 가격 모드 |

저장소 함수와 독립 구현의 차이(같은 입력, 5행 모두): 최대 3.6e-12(DV01). 수익률 차이는 5.3e-16 이하다. 이 값들은 단위 일관성 확인이다. 시장 정확성을 검증한 것은 아니다. 더 깊은 B 검증은 B 차원 몫이다. 결제일·경과이자 생략 문제(가격이 dirty)는 `financial_calcs.md` FC-03이 다룬다.

경계값 독립 확인:
- 0% 수익률, 쿠폰 4.5%: P = 100 + 20·2.25 = 145.000. Mac = (2.25·105 + 1000)/145 = 8.52586. DV01 = 8.52586·1.45·100 = 1,236.25. 화면 145.000 / 1,236. 일치.
- '4,5' → 45%: 2.25·(1 − 1.225^−20)/0.225 + 100·1.225^−20 = 11.5542. 화면 11.554. 계산은 맞지만 사용자가 뜻한 입력이 아니다.
- Coupon 빈칸 → 0%: 100/1.0225^20 = 64.0816. 화면 64.082, Mac 10.00y.
- CF 빈칸: 798.1856·1.0/65 = 12.2798. 화면 12.28. 표시된 0.8을 썼다면 9.8238.

`_num` 입력표(a01, HEAD; 기준 파서는 독립 구현):
| raw | `_num` | 기준 | 판정 |
|---|---|---|---|
| None, '', '   ' | 없음(default) | 없음 | 일치 |
| '0', '0.0', '-0', '-1', ' 4.5 ', '+4.5' | 0, 0, -0, -1, 4.5, 4.5 | 같음 | 일치 |
| 'nan', 'NaN', 'inf', '-inf', '1e400', 'abc', '4.5%', '0x10', '−4.5'(U+2212) | ValueError "Yield %: '…' is not a number." | 거부 | 일치 |
| '1,000' | 1000 | 1000 | 일치 |
| '4,5' / '1,0,0' / '1_000' | 45 / 100 / 1000 | 거부 | **불일치(A-05)** |
| '４.５'(전각) | 4.5 | 4.5 | 일치 |
| '1e-400' | 0.0(언더플로) | 0.0 | 일치(가격이면 "price must be positive") |

### ⑤ 수정안(최소 diff, 스크래치 사본에서 검증, 저장소에는 미적용)
전체 diff: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/A_input_contract/a06_fix.diff`(266줄). 대상은 `ui/bonds_page.py`이고, 선택 사항으로 `core/ficc/curves.py` 한 줄이 있다. 핵심만 보인다.
```diff
+_QUOTES = [("yield", "Yield"), ("price", "Price")]
+_MAX_MATURITY = 100.0
+_NUM_RE = re.compile(r"[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)?(?:\.\d*)?(?:[eE][+-]?\d+)?")
+class _FieldError(ValueError):            # field + msg; page sets field.error = msg
-def _num(field, default=None):
+def _num(field, default=None, *, required=False, gt=None, ge=None, le=None):
+    # blank -> default or "required."; comma only as thousands; range in user units
+    quote = ft.Dropdown(label="Quote by", value="yield", options=[Yield, Price])
-    price = ft.TextField(..., hint_text="blank = from yield")
+    price = ft.TextField(..., hint_text="Quote by = Price", disabled=True)
+    stale = notice("Inputs changed since this result was computed. Press Run to refresh it.", "warning")
+    state = {"gen": 0, "raw": None}
+    def on_input(e=None): stale.visible = state["raw"] is not None and _raw() != state["raw"]
+    # every TextField.on_change, freq/source/quote/tool on_select -> on_input (quote also toggles disabled)
     def run(e=None):
+        # read ALL inputs once, on the click: coupon ge 0, maturity (0,100], notional > 0,
+        # px (price mode, > 0) or y (yield mode, (-50, 200]), hedge: CTD > 0, CF > 0 required
+        # on _FieldError: field.error = msg, error notice, return (no thread)
+        state["gen"] += 1; gen, state["raw"] = state["gen"], _raw()
         def worker():
-            bond = Bond(coupon=_num(coupon, 0.0) / 100.0, ...); y = _num(ytm)
-            a = analyze_bond(bond, price=_num(price), ...)
+            a = analyze_bond(bond, price=px, ytm=None if y is None else y / 100.0, curve=curve)
-            result_host.controls = blocks
+            if gen != state["gen"]: return           # a newer Run owns the screen
+            stale.visible = _raw() != state["raw"]   # edited while this ran
+            result_host.controls = [stale] + blocks
-   stat("Position DV01", ...)
+   stat("Position DV01 (override)" if typed else "Position DV01 (calculator)", ...)
--- core/ficc/curves.py
-    n = int(math.ceil((maturity - start) * freq - 1e-9))
+    n = max(1, int(math.ceil((maturity - start) * freq - 1e-9)))   # T itself always pays
```
- UX 선택: 모드 선택기를 썼다. 지금 어느 칸이 입력인지 화면에 보인다. 비활성 칸은 회색으로 꺼진다. 그래서 "둘 다 채움"이 모호하지 않다. 수용 기준 4-1의 "둘 다 입력이면 오류"는 "선택한 모드의 칸만 쓰고, 그 칸이 비면 필드 오류"로 바뀐다. 이 해석은 소유자 확인이 필요하다. 대안은 한 칸을 편집하면 다른 칸을 자동으로 비우는 방식이다. 이 방식은 비워진 사실을 사용자가 놓치기 쉬워서 2순위로 둔다.
- 모듈 자체 검사도 바꿨다. 기존 `:288-290`은 "둘 다 채움 → 오류"를 검사한다. 수정본에서는 이것을 모드 계약, 필드 오류, 낡은 결과 배너, '4,5' 거부 검사로 바꿨다. 수정본에서 `python3 -B -m ui.bonds_page` 결과는 `ok`다.
- P01-05의 잠금과 버튼 비활성화는 이 diff에 넣지 않았다. 세대 번호는 화면을 지킨다. 하지만 중복 네트워크 호출은 막지 못한다. 두 수정은 함께 넣어야 한다.

### ⑥ 테스트 로그(PASS/FAIL/NOT_RUN)
| 테스트 | HEAD | 수정본 | 로그 |
|---|---|---|---|
| a01 `_num`/코어 계약 표(24개 raw, 21개 코어 사례) | 실행. 불일치 3개('4,5', '1,0,0', '1_000') | — | `a01_num_contract.log` |
| a02 실제 페이지 구동(34개 검사) | 11 PASS / 23 FAIL | 34 PASS / 0 FAIL | `a02_page_drive_head.log`, `a02_page_drive_fix.log` |
| a03 표 2.1 독립 재계산 | 실행. 1·2행은 Yield 모드만 일치 | — | `a03_lead_independent.log` |
| a04 실제 스레드 R1(덮어쓰기), R2(두 시점 읽기) | FAIL, FAIL | PASS, PASS | `a04_threads_head.log`, `a04_threads_fix.log` |
| a05 극단값 위치·만기 시간 | 실행(T=1e4 0.044s, 1e5 NaN 오류 0.05s, 1e6 0.68s) | — | `a05_extremes.log` |
| a07 제안 회귀 테스트 12개 | 2/12 PASS | 12/12 PASS | `a07_regression_head.log`, `a07_regression_fix.log` |
| `tests/ficc_acceptance.py` 전체(in-process, 캐시는 스크래치, TTL 0) | 57/57 PASS | 57/57 PASS | `a08_ficc_acceptance_*.log` |
| `python3 -B -m ui.bonds_page` 자체 검사 | ok | ok(갱신본) | `selfcheck_bonds_page_*.log` |
| `-m core.ficc.bonds`, `-m core.ficc.curves` 자체 검사 | ok, ok | ok, ok | `selfcheck_core.ficc.*` |
| a09 수정 전후 같은 입력 8건의 타일 비교, Run 시간 | — | 8/8 SAME. 중앙값: calc 0.19-0.22s → 0.22-0.26s(측정 잡음 수준), scenarios 0.14→0.16s, hedge 0.012→0.015s | `a09_compare.log` |
| 실제 Flet 창 렌더링, 힌트 표시 방식 | NOT_RUN | NOT_RUN | — |
| FRED 실데이터 경로 | NOT_RUN | NOT_RUN | (E 차원) |
| `tests/run_all.py` | NOT_RUN(규칙상 금지) | NOT_RUN | — |
Run 시간은 대체 Page 기준이다(`update`는 아무 일도 안 함, 합성 곡선). 실제 렌더링 시간과 FRED 요청 시간은 들어 있지 않다.

### 화면 관찰 / 코드 확인 / 가설
| 구분 | 내용 |
|---|---|
| 화면 관찰(소유자) | 둘 다 채우고 Run → "Give exactly one of price or ytm."(2.2). "가격 입력 100" 옆에 107.982/92.386(2.1) |
| 코드로 확인됨 | 계약 검사 `bonds.py:236-237`. 오류가 나면 결과를 지운다(`bonds_page.py:96,100`). `on_change` 없음. `on_tool`은 표시 여부만 바꾼다. 빈칸 기본값 `:107-108,117` |
| 테스트로 확인됨 | 둘 다 채운 새 Run은 107.982를 낼 수 없다. Run 없이 Price=100을 입력하면 1·2행 화면이 숫자 하나까지 재현된다. 0% 수익률은 유효하다. 오류는 이전 결과를 대체한다 |
| 미확인 가설 H1 | 소유자가 Yield 모드로 Run한 뒤 Price에 100을 입력하고 캡처했다(재현과 정확히 일치하지만, 실제로 그랬는지는 확인 불가) |
| 미확인 가설 H2 | 빈 Price 칸에 표시되는 라벨 "Price (per 100)"를 입력값 100으로 읽었다. Flutter `InputDecoration.hintText` 문서에 따르면 labelText가 있으면 hint는 포커스가 있을 때만 보인다. 그러면 "blank = from yield"는 평소에 안 보인다. GUI를 실행하지 않아 미확인이다 |

### ⑦ 남은 리스크
- 수정안은 스크래치 사본에만 있다. 저장소에는 적용하지 않았다. 적용 여부는 소유자가 결정한다.
- 실제 Flet 클라이언트에서 확인하지 못한 것이 있다(NOT_RUN): 비활성 칸의 모양, `TextField.error` 표시, 키 입력마다 `page.update()`가 일으키는 지연.
- 수익률 -50%~-45% 구간은 수정본에서도 코어의 z-spread 구간 오류 메시지로 끝난다(B 차원).
- 음수 notional(숏 포지션)은 표현할 수 없다. 헤지 방향 문제는 D 차원이다.
- 가격이 dirty라는 문제는 `financial_calcs.md` FC-03이다. 합성 곡선 해설 표시는 `d03_synthetic_fallback.md` D03-03이 다룬다.
- UI 자체 검사가 CI에 없다(`functional_completeness.md` FC-06). a07 테스트를 `tests/`에 넣고 acceptance 목록에 올려야 회귀를 막는다.
- 중복 클릭 시 네트워크 호출이 두 번 나간다(`p01_performance.md` P01-05). 이번 diff는 표시 오류만 막는다.

### 스크립트 경로
`/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/A_input_contract/`에 있다: `a_helpers.py`, `a01_num_contract.py`, `a02_page_drive.py`, `a03_lead_independent.py`, `a04_threads.py`, `a05_extremes.py`, `a06_apply_fix.py`(→ `a06_fix.diff`, `repo_fix/`), `a07_regression_tests.py`, `a08_existing_tests.py`, `a09_before_after.py`. 실행 방법: `python3 -B -W ignore <script> <tree> <label>`. tree는 `repo_copy` 또는 `repo_fix`다.

### 독립 검증

검증 범위와 방법
- 저장소 추적 파일은 바꾸지 않았다. 작업 전후 `git status --porcelain`은 0줄이다.
- 작업 폴더: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/verify_A_input_contract/`
- 이 폴더에 `git archive HEAD` 사본 세 개를 만들었다.
  - `repo_head`: HEAD 그대로다.
  - `repo_fixv`: 조사자의 `a06_fix.diff`를 내가 직접 적용했다.
  - `repo_m2`: 아래 누락 항목의 최소 수정본이다.
- 페이지 구동기(`vh.py`)와 독립 공식(`indep.py`)은 새로 짰다. 조사자 스크립트를 쓰지 않았다. `indep.py`는 저장소를 import하지 않는다. Convexity와 DV01은 유한차분으로, YTM은 뉴턴법으로 구한다. 조사자의 해석식이나 brentq와 다른 방법이다.
- 실제 Flet 창, FRED 경로, `tests/run_all.py`는 실행하지 않았다(NOT_RUN).
- 첨부 docx에는 화면 캡처가 없다. `word/media`가 없고 문서 썸네일만 있다. 그래서 H1/H2는 계속 미확인이다.

| id | 유지 여부 | 정정 심각도 | 정정 상태 | 근거 |
|---|---|---|---|---|
| A-01 | 유지 | P2 (P1에서 낮춤) | 테스트로 확인됨 | 재현은 정확하다. Run 뒤 Price='100'을 넣어도 107.982/4.500%/7.92y/7.74/73.0/836이 그대로다. 92.386/8.07y/7.86/74.4/726도 같다. stale 표시는 0건이고 `on_change`가 있는 TextField도 0개다(`v01_page_head.json`). P2로 낮춘 이유: 결과 타일이 실제로 쓴 Price/Yield를 스스로 보여 주고, 해설문이 쿠폰과 만기를 적는다. 그래서 이것은 틀린 숫자가 아니라 오해를 부르는 UI 상태다(P2 정의). 요약 2항의 "그 Run 뒤에 Price 칸에 100이 들어갔다"는 H1 가설이다. 사실로 쓰면 안 된다. 확인된 것은 "1·2행 숫자는 Run 시점에 Price가 비어 있던 Yield 모드 결과"까지다 |
| A-02 | 유지 | P2 | 테스트로 확인됨 | calc→hedge: hedge 입력줄은 보이고 calc 타일(Carry + roll)은 그대로다. hedge(pos 500)→calc: 입력줄은 숨겨지고 'Contracts to sell 6.15'와 'Position DV01 500'이 남는다(`v01`) |
| A-03 | 유지 | P2 | 테스트로 확인됨 (Flutter hint 표시 방식만 미확인) | 기본 화면은 Coupon 4.50, Yield 4.50이다. Price만 넣으면 'Give exactly one of price or ytm.'가 난다. 둘 다 비워도 같다. `TextField.error` 설정은 0건이다(`v01`) |
| A-04 | 유지 | P2 | 테스트로 확인됨 | Coupon 빈칸이면 64.082 / 10.00y / 627이다(독립 계산 64.081647). CF 빈칸이면 CF 타일 1.0000, 12.28이다(독립 12.27978). 0.8이면 9.82다(독립 9.82382). Maturity와 Notional 빈칸은 10y와 1e6으로 조용히 계산한다 |
| A-05 | 유지 | P2 | 테스트로 확인됨 | '4,5'는 Yield 45.000%, 가격 11.554, DV01 35로 나온다(독립 11.554249). '1,0,0'은 100, '1_000'은 1000이다. 수정안은 '4,5'는 거부하지만 쿠폰 상한이 없다. 그래서 '45'(소수점 누락) 오타는 HEAD와 수정본 모두 가격 423.265로 통과한다(`v09`) |
| A-06 | 유지 | P2 | 테스트로 확인됨 | 실제 스레드로 재현했다(`v02_race_head.json`). R1: 두 번째 결과 100.000이 먼저 나오고 링이 꺼진다. 그 뒤 첫 작업이 107.982로 덮어쓴다. Coupon 칸은 4.5다. R2: 유효한 입력인데 'exactly one' 오류가 난다. 조사자가 놓친 증거가 하나 더 있다. R3: hedge 도구에서 로드 중에 Coupon 5.5→4.5, CF 0.8→1.0으로 바꾸면 오류 없이 Price 107.982(쿠폰 5.5)와 CF 1.0000이 섞인 결과가 나온다. 수정본에서는 R1, R2, R3 모두 클릭 시점 스냅샷이 유지된다(`v02_race_fix.log`) |
| A-07 | 유지 | P2 | 테스트로 확인됨 | HEAD 재현: 만기 1e-10은 IndexError, 1e5는 scipy NaN 메시지다. Yield 250은 'No yield … 1.8000', -45는 'No z-spread … 17993.5701'이다. 비용을 실측했다(`v08`): 1e6은 0.73s/207MB, 1e7은 9.8s/910MB, 3e7은 28.8s/2.5GB다. 선형이므로 1e8은 약 8GB로 추정된다(미실행, 미확인). Run 버튼이 꺼지지 않아 연타하면 메모리가 배로 는다. 수정안에는 결함이 있다(아래 '수정안 검토' ①②③) |
| A-08 | 유지 | P3 | 테스트로 확인됨 | 문구 6종을 재현했다(`v01` A07_A08). 헤지 문구 'CTD DV01 per contract and conversion factor must be positive.'(`bonds.py:327-328`)도 두 칸 중 어느 칸인지 말하지 않는다(코드로 확인됨) |
| A-09 | 유지 | P3 | 테스트로 확인됨 | Notional 5M으로 바꾼 뒤 hedge를 Run해도 Position DV01 타일은 500이고 Contracts는 6.15다. 계산기 DV01은 3,990.93이다(독립 유한차분) |

독립 재계산 (조사자 숫자 점검, `v04_spot.log`, `v13_repo_vs_indep.log`)
- 1행 Yield 모드(c 5.5, y 4.5): P 107.981856, Mac 7.918984, Mod 7.744728, Cvx(유한차분) 73.014819, DV01(유한차분) 836.2901. 조사자 값과 일치한다.
- 4행 P=95: 뉴턴법 y 6.177690%, Mac 7.756345, DV01 714.774. 일치한다.
- 5행 P=105: y 4.862682%, DV01 808.222, Cvx 72.33906(유한차분 잡음 3.6e-5). 일치한다.
- 0% 수익률: P 145.000, Mac 8.525862, DV01 1,236.25. '4,5' → 11.554249. Coupon 빈칸 → 64.081647. 모두 일치한다.
- 저장소 함수와 내 구현의 차이: 가격 6.7e-13, 수익률 8.3e-16. Convexity와 DV01은 유한차분 대비 3.6e-5, 1.3e-7이다(차분 잡음). 단위 일관성만 확인한 것이다. 시장 정확성은 검증하지 않았다.

수정안 검토 (`a06_fix.diff`)
- 회귀 테스트를 다시 돌렸다. 내 사본에서 HEAD 2/12, 수정본 12/12다(`v03_a07_rerun.log`). 테스트가 수정 전에 실패하고 수정 후에 통과하는 것을 확인했다.
- `python3 -B -m ui.bonds_page`는 수정본에서 ok다. `tests/ficc_acceptance.py`는 양쪽 모두 57/57이다(`v06_ficc_*.log`).
- 같은 입력 9건(calc, scenarios 표 30줄, hedge 포함)의 타일과 표는 수정 전후가 모두 같다. 'Position DV01' 라벨만 바뀐다(`v07_compare.log`).
- 다만 다음 결함이 있다.
  - ① diff가 그대로 적용되지 않는다. HEAD의 `core/ficc/curves.py`는 CRLF로 저장돼 있다(`git ls-files --eol`: i/crlf). 그래서 `patch -p1`이 'different line endings'로 실패한다. 조사자의 `repo_fix/core/ficc/curves.py`는 파일 전체가 LF로 바뀌어 있다. 이것은 `.gitattributes`의 "never convert line endings" 규칙을 어긴다. 적용할 때는 CRLF를 지키는 한 줄 변경으로 해야 한다.
  - ② 코어의 `n = max(1, …)`는 IndexError를 없앤다. 대신 만기 1e-10에서 Breakeven -2,250,000,278,533.8bp가 정상 결과처럼 표시된다(`v09_fix_probe_fix.log`). UI의 만기 하한이 `gt=0`이기 때문이다. 이 변경은 B 차원의 만기<horizon breakeven 가드(`verify_B_pricing_risk` `test_m3_no_breakeven_for_a_bond_maturing_inside_the_horizon`)와 함께 넣어야 한다. 아니면 UI에 의미 있는 최소 만기를 두어야 한다.
  - ③ "수익률 -50%~-45% 구간만 남는다"는 서술은 틀리다. 합성 곡선(10y zero 7.50%)에서 10y 4.5% 채권은 수익률 -38.28% 아래부터 z-spread 구간 오류가 난다. -40%도 실패한다(`v10_ytm_floor.log`). 이 경계는 곡선 수준에 따라 움직인다.
- 4-1 수용 기준의 해석 변경(모드 선택기)은 조사자 말대로 소유자 확인이 필요하다.

누락 항목 (전체)

**A-10 · P3 · 테스트로 확인됨: 숫자 오류 문구가 사용자가 입력한 값이 아니라 쉼표를 지운 값을 보여 준다**
- 위치: `ui/bonds_page.py:_num:40,48`
- 재현: Coupon %에 '1,2a'를 넣고 Run한다.
- 기대: `Coupon %: '1,2a' is not a number.`
- 실제: `Coupon %: '12a' is not a number.`
- 원인: `raw = strip().replace(",", "")`로 바꾼 값을 메시지에 그대로 쓴다.
- 영향: 사용자는 자기가 친 적 없는 값을 본다. 쉼표 문제(A-05)를 스스로 찾기 어렵다.
- 수정: 메시지에는 strip만 한 raw를 쓰고, `float()`에만 `replace(",", "")`를 쓴다(`v12_missed_fix.diff`). `a06_fix.diff`도 이 문제를 고친다.
- 회귀 테스트: `v11_missed_tests.py::t_error_echoes_what_was_typed`. HEAD FAIL, a06 수정본 PASS, v12 수정본 PASS.

**A-11 · P3 · 테스트로 확인됨: Yield '-0'이 '-0.000%'로 표시된다**
- 위치: `ui/bonds_page.py:_num:49`(-0.0을 그대로 돌려줌), `core/ficc/common.py:pct_text:70-71`
- 재현: Yield %에 '-0'을 넣고 Run한다(쿠폰 4.5, 10y).
- 기대: Yield '0.000%'
- 실제: Price 145.000, Yield '-0.000%'. 해설문도 'a yield of -0.000%'라고 쓴다.
- 원인: `float('-0')`은 IEEE 음의 0이다. 포맷이 부호를 그대로 찍는다.
- 영향: 0% 수익률이 음수처럼 보인다(3.A의 '0과 음수 구분' 항목).
- 수정: `_num`이 `v + 0.0`을 돌려준다(-0.0 + 0.0 = 0.0, `v12_missed_fix.diff`). `a06_fix.diff`에는 이 수정이 없다.
- 회귀 테스트: `v11_missed_tests.py::t_negative_zero_yield_shows_as_zero`. HEAD FAIL, a06 수정본 FAIL, v12 수정본 PASS. 자체 검사도 ok다.

**A-12 · P2 · 테스트로 확인됨: 조사자 수정안의 결함(저장소 코드가 아님). 만기 하한 없이 coupon_times를 n≥1로 바꾸면 오류가 터무니없는 숫자로 바뀐다**
- 위치: `a06_fix.diff`의 `core/ficc/curves.py:47` 변경과 UI `_num(maturity, gt=0.0)`. 근본 원인은 `core/ficc/bonds.py:carry_roll:206-208`이다.
- 재현: `repo_fixv`에서 Maturity '1e-10' 또는 '0.0000001'로 Run한다.
- 기대: 필드 오류를 내거나 Breakeven을 표시하지 않는다.
- 실제: Price 102.250, Breakeven -2,250,000,278,533.8bp(1e-10) 또는 -2,250,000,081.7bp(1e-7)가 정상 결과처럼 나온다. HEAD에서는 IndexError 메시지였다.
- 원인: duration이 0에 가까운데 breakeven = total/(Mod·P)를 계산한다.
- 영향: 수정안을 이대로 적용하면, 지금은 거부되는 입력이 틀린 숫자로 표시된다.
- 수정: B의 만기<horizon breakeven 가드와 함께 적용한다. 또는 UI 만기 하한을 둔다. 적용할 때 CRLF를 지킨다.
- 회귀 테스트: Maturity '1e-10' → Breakeven 타일이 없거나 필드 오류. a06 수정본에서 FAIL(`v09_fix_probe_fix.log`).

스크립트와 로그: 위 작업 폴더의 `vh.py`, `indep.py`, `v01_page.py`, `v02_race.py`, `v04_spot.py`, `v05_probe.py`, `v07_beforeafter.py`, `v09_fix_probe.py`, `v11_missed_tests.py`, 그리고 각 `.json`/`.log` 파일.
