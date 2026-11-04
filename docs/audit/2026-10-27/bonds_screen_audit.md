# Bonds 화면 검증 보고서 (2026-10-27)

> **저장소 사본 안내 (오케스트레이터).** 이 보고서는 워크플로 에이전트가 반환한 본문을 내용 변경 없이 옮긴 것입니다. 본문의 `/tmp/claude-0/...scratchpad/...` 경로는 클라우드 세션이 끝나면 사라집니다. 다음 사본은 저장소에 남겼습니다.
> - 제안 패치(저장소에 적용하지 않음): `docs/audit/2026-10-27/bonds_screen/proposed_patch/bonds_screen.diff`. `git apply --check`가 통과합니다. 적용은 소유자 승인 뒤에 합니다.
> - 새 회귀 테스트 모듈 사본: `docs/audit/2026-10-27/bonds_screen/proposed_patch/bonds_screen_acceptance.py.txt`. 패치를 적용하면 `tests/bonds_screen_acceptance.py`로 들어갑니다.
> - 패치 단계 테스트 로그(`patch/logs2/`의 사본): `docs/audit/2026-10-27/bonds_screen/test_logs/`.
> - 오케스트레이터 독립 재실행 결과: `docs/audit/2026-10-27/bonds_screen/test_logs/orchestrator_recheck.txt`. 패치본은 새 모듈 33/33 PASS, ficc_acceptance 57/57 PASS입니다. 현재 코드는 새 모듈 4/33 PASS, 29 FAIL입니다.
> - 차원별 조사·검증 보고서: `docs/audit/2026-10-27/bonds_screen/A_input_contract.md` ~ `G_real_ui.md`.
> - 실제 UI 스크린샷: `docs/audit/2026-10-27/bonds_screen/shots/`.


- 대상: Bonds > Calculator & risk / Scenarios / Futures hedge.
- 요청서: `docs/audit/2026-10-27/bonds_screen_request.md`(소유자 원문). 이 보고서는 요청서 6절의 순서 ① ~ ⑦을 따릅니다.
- 대상 코드: HEAD `319f732`입니다. 요청서를 저장한 `078981a` 이후 코드는 바뀌지 않았습니다. `git diff 078981a 319f732 -- ui core tests config.py data README.md requirements.txt pyproject.toml main.py`의 결과가 0줄입니다.
- 저장소의 추적 파일은 바꾸지 않았습니다. 마지막 `git status --short`의 결과도 0줄입니다.
- 실험은 모두 `git archive HEAD`로 만든 스크래치 사본에서 했습니다. 사본에 있던 캐시 CSV 4개는 열지 않고 지웠습니다. `.env`는 열지 않았습니다. `tests/run_all.py`는 실행하지 않았습니다.
- 근거 보고서: 차원별 보고서 7개입니다(`docs/audit/2026-10-27/bonds_screen/A_input_contract.md` ~ `G_real_ui.md`). 각 보고서에는 독립 검증 절이 붙어 있습니다. 이 보고서는 그 결과를 통합합니다. 핵심 숫자와 테스트는 이 보고서를 쓰면서 다시 실행했습니다(⑥ 6.1).
- 판정 용어: 코드로 확인됨 / 테스트로 확인됨 / 미확인. 테스트 결과는 PASS / FAIL / NOT_RUN으로 적습니다. NOT_RUN은 통과로 세지 않습니다.
- 심각도:
  - P0: 잘못된 돈·의사결정 숫자를 실제처럼 보이거나 안전 규칙을 어김.
  - P1: 사용자에게 보이는 틀린 숫자, 화면 중단, 합성·낡은 데이터를 실제처럼 보임.
  - P2: 경계 사례의 오류, 빠진 방어, 오해를 부르는 UI 상태.
  - P3: 위생·문서.
- 이슈 ID: `BS-xx`는 이 보고서의 통합 ID입니다. 괄호 안은 차원 보고서 ID와 그 검증 심각도입니다(검증자가 추가한 ID 포함). 이전 감사 ID(FC-03, D03-03, D03-V01, P01-05 등)는 인용만 합니다.
- 경로 약어: `W` = `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work`. 주요 파일의 전체 경로는 부록 A에 있습니다.
- 스크린샷 경로: `docs/audit/2026-10-27/bonds_screen/shots/<파일 이름>`.

---

## ① 요약

### 1.1 결론

1. 계산식은 이 코드의 모델 안에서 맞습니다. 표 2.1의 숫자 30개(5행 × 6항목)가 독립 구현과 표시 자리수까지 모두 같습니다. 해석식끼리의 최대 차이는 3.2e-12입니다(DV01, 통화 단위). (테스트로 확인됨)
2. 가장 큰 문제는 계산이 아니라 화면 상태입니다. 지금 보이는 결과가 지금 보이는 입력에서 나왔다는 보장이 없습니다. 원인은 BS-01(P1)과 BS-02(P2)입니다. (테스트로 확인됨)
3. 통합 이슈는 41건입니다: P0 0, P1 1, P2 17, P3 23.
   - 차원 보고서에서 검증 뒤 유지된 행은 79개입니다(검증 심각도 P1 1, P2 36, P3 42).
   - 이 중 74개가 저장소 결함이고(P1 1, P2 33, P3 40), 41건으로 묶었습니다.
   - 나머지 5개(A-12 P2, C의 M-01 P2·M-02 P2, D의 M-1 P3·M-5 P3)는 조사자가 낸 수정안의 결함입니다. 최종 패치에서 처리했습니다(⑤ 5.6).
   - ID별 검증 심각도는 2.1 표의 '관련 ID' 열과 부록 B에 있습니다.
4. 수정 패치는 스크래치 사본에만 있고 저장소에는 적용하지 않았습니다.
   - 패치 사본: 새 회귀 테스트 33/33 PASS.
   - HEAD 사본: 같은 테스트 4/33 PASS.
   - 기존 FICC 인수 테스트: 양쪽 모두 57/57 PASS.
   - 최종 패치에도 P3 문구 결함 1건이 남습니다. 시나리오 notice가 1차 근사(+102.2bp)를 평탄 곡선의 값이라고 부릅니다(5.6 RP-01).
5. 실시장 정확성은 검증하지 않았습니다. 실제 FRED 호출, QuantLib 대조, 데스크톱 창 클릭은 모두 NOT_RUN입니다.

### 1.2 화면 숫자가 증명하는 것과 증명하지 않는 것

증명하는 것 (테스트로 확인됨):
- 표 2.1의 가격·수익률·Macaulay·Modified·Convexity·DV01은 코드의 정의대로 정확히 계산됐습니다. 정의는 ④ 4.2에 있습니다.
- 95와 105에서 역산한 수익률 6.178%와 4.863%는 맞습니다. Newton, 이분법, numpy.roots로 구한 값과 8.5e-16 안에서 같습니다.
- 가격과 쿠폰의 관계도 맞습니다. 쿠폰 = 수익률이면 100.000, 쿠폰 > 수익률이면 100 초과, 쿠폰 < 수익률이면 100 미만입니다. 쿠폰일 정산(정수 기간) 200건에서 위반이 0건입니다.
- 헤지 9.82는 표시된 식으로 계산하면 맞는 값입니다. Rounded 10과 잔여 −14도 서로 맞습니다.
- 시나리오의 방향(금리 상승 시 손실, 하락 시 이익)과 비대칭의 크기는 볼록성과 맞습니다.

증명하지 않는 것:
- 시장 가격과 맞는지는 증명하지 않습니다. Price는 정산일과 경과이자가 없는 전체 현재가치(dirty)입니다(FC-03).
  - 10년 정수 기간 예시는 경과이자가 0이라 영향이 없습니다.
  - 7.3년 같은 소수 만기에 clean 호가를 넣으면 수익률이 +13~+19bp 틀립니다.
- 2.3 시나리오 숫자가 맞는지도 증명하지 않습니다.
  - 이 숫자는 그날 쓰인 곡선에 달려 있습니다. 곡선 스냅샷이 없어 정확히 재현하지 못했습니다(미확인).
  - 현재 합성 곡선의 결과와 다릅니다. B +100bp에서 −75,256 대 화면 −74,657입니다.
  - 따라서 HEAD 코드였다면 합성 곡선 결과가 아닙니다. 실제 FRED였는지는 미확인입니다.
- "+100bp parallel"은 채권 수익률 +100bp가 아닙니다.
  - 코드는 연속복리 zero 금리에 100bp를 더하고 z-spread를 고정합니다.
  - 이것은 이 채권 수익률로 약 +102.5~+103.2bp입니다.
  - 수익률을 +100bp 올려 재평가하면 B는 −72,697입니다.
- 헤지 수량이 실제로 사야 할 계약 수라는 증명도 아닙니다.
  - 65와 0.8은 입력 예시값입니다.
  - CTD 변경, basis, 인도 옵션, invoice price는 모델에 없습니다.
- 소유자가 Position DV01 칸을 비웠는지 798을 입력했는지는 화면으로 구분할 수 없습니다(4.5, 미확인).
- 표 2.1 1·2행은 "가격 입력 100"의 결과가 아닙니다. 1.3을 보십시오.

### 1.3 "가격 입력 100"인데 107.982와 92.386이 나온 이유 (테스트로 확인됨, 원인 가설은 미확인)

- Price와 Yield를 둘 다 채우고 Run하면 숫자가 나오지 않습니다.
  - 코어가 "Give exactly one of price or ytm."을 냅니다(`core/ficc/bonds.py:analyze_bond:236-237`).
  - 화면은 Run을 시작할 때 결과를 비웁니다(`ui/bonds_page.py:run:96`).
  - 그래서 오류 문구 하나만 남습니다.
- 1·2행의 숫자 6개는 Price를 비운 Yield 모드의 결과와 소수 자리까지 같습니다. Price=100 가격 모드였다면 숫자가 다릅니다.

| 행 | 화면 | Yield 모드(Price 빈칸) 독립 계산 | Price=100 가격 모드 독립 계산 |
|---|---|---|---|
| 1 (쿠폰 5.5, Yield 4.5) | 107.982 / 4.500% / 7.92y / 7.74 / 73.0 / 836 | 107.981856 / 4.500% / 7.919 / 7.745 / 73.015 / 836.29 | 100.000 / 5.500% / 7.823 / 7.614 / 71.15 / 761.36 |
| 2 (쿠폰 4.5, Yield 5.5) | 92.386 / 5.500% / 8.07y / 7.86 / 74.4 / 726 | 92.386374 / 5.500% / 8.072 / 7.856 / 74.390 / 725.79 | 100.000 / 4.500% / 8.161 / 7.982 / 76.21 / 798.19 |

- 같은 화면을 그대로 재현했습니다.
  - 절차: Yield 모드로 Run합니다. Price 칸에 100을 넣고 Run하지 않습니다.
  - 결과: 화면은 107.982 / 4.500% / 7.92y / 7.74 / 73.0 / 836 그대로입니다. 2행도 92.386 / 726 그대로입니다.
  - 결과가 낡았다는 표시는 0건입니다. 입력칸 8개 중 `on_change`가 있는 칸도 0개입니다.
  - 근거: `W/final_report/logs/stale_head.log`, 차원 A의 a02, 실제 UI 스크린샷 `S3b_typed_price95_no_run.png`(Price 95로 같은 현상).
- 결론: 그 캡처는 이전 Yield 모드 Run의 결과입니다. 그 뒤 Price 칸이 바뀌었는데 화면이 알리지 않았습니다(BS-02).
- 미확인 가설:
  - H1: 소유자가 Run 뒤에 Price 칸에 100을 입력하고 캡처했다.
  - H2: 빈 Price 칸 안에 크게 보이는 라벨 "Price (per 100)"을 입력값 100으로 읽었다.
  - H2에는 정황이 있습니다. 웹 렌더에서는 빈 칸 안에 라벨이 값처럼 보입니다(`crop_Q2_run1_overwrites_run2.png`의 Price 칸). hint "blank = from yield"는 포커스가 있을 때만 보였습니다. 데스크톱 창은 확인하지 못했습니다.
- 3행(5.5/5.5)은 두 모드의 결과가 같습니다. 쿠폰 = 수익률이면 가격이 100이기 때문입니다. 그래서 어느 모드였는지는 구분할 수 없지만, 결과는 맞습니다.
- 같은 화면은 다른 경로로도 생길 수 있습니다. 느린 이전 Run이 늦게 끝나 새 결과를 덮는 경우입니다(BS-01).
- 패치 사본에서 같은 조작을 하면 결과 위에 배너가 뜹니다: "Inputs changed since this result was computed. Press Run to refresh it."(`W/final_report/logs/stale_patched.log`).

### 1.4 주요 결함

- BS-01 (P1) 동시 Run 문제입니다.
  - 늦게 끝난 이전 Run이 새 결과를 덮거나, 그 Run의 오류가 새 결과를 지웁니다.
  - 작업자 스레드가 입력을 곡선 로드 전과 후에 나눠 읽습니다.
  - 진행 링이 작업이 끝나기 전에 꺼집니다.
- BS-02 (P2) 입력이나 도구를 바꿔도 이전 결과가 표시 없이 남습니다. 표 2.1 1·2행이 이 상태입니다.
- BS-05, BS-06 (P2) 빈칸이 조용히 기본값이 됩니다(쿠폰 0%, CF 1.0 등). '4,5'는 45%로 읽힙니다.
- BS-08 (P2) 만기 3개월 이하 채권의 Roll-down, Carry + roll, Breakeven이 틀립니다. 예: 5.5%, 0.25년, 합성 곡선에서 Breakeven이 −1062.6bp로 나옵니다.
- BS-09, BS-10 (P2) 시나리오의 단위(연속복리 zero)가 화면에 없습니다. 곡선의 일부 만기가 빠지면 같은 이름의 시나리오가 다른 모양이 됩니다.
- BS-12, BS-13 (P2) 숏 포지션에 "Contracts to sell −9.82"가 나옵니다. 헤지가 근사라는 점과 입력 단위를 알리지 않습니다.
- BS-14 ~ BS-17 (P2) FRED 곡선 경로 문제입니다.
  - 오래되거나, 날짜가 섞이거나, 단위가 틀린 FRED 곡선도 녹색 칩을 달고 계산됩니다.
  - 응답이 없는 망에서는 auto Run 한 번이 약 24분 걸립니다(E 검증에서 1,446.6초 측정).
- BS-18 (P2) FICC 차트 제목이 어두운 배경에 검정으로 그려져 보이지 않습니다. "z-spread held"와 KRD 합계가 가려집니다.

### 1.5 수용 기준(요청서 4절) 판정

| 수용 기준 | HEAD 판정 | 패치 사본 판정 | 근거 등급 | 근거 |
|---|---|---|---|---|
| 가격/YTM 상호 배타성 | 미충족 | 충족 | 테스트로 확인됨(HEAD: 브라우저와 stand-in, 패치: stand-in). 데스크톱 표시는 미확인 | HEAD: Price만 넣으면 YTM을 계산합니다(95 → 6.178%). YTM만 넣으면 Price를 계산합니다(5.5 → 100.000). 둘 다 채운 경우와 둘 다 빈 경우가 같은 문구 "Give exactly one of price or ytm."이고, 필드 표시가 없습니다. 그래서 "명확한 오류"에 미달합니다. 패치: 두 경우의 문구가 다르고("both are filled" / "both are blank") 두 칸 모두에 field error가 붙습니다. 근거는 test_price_yield_exclusive_with_field_errors(stand-in 페이지)입니다. |
| 액면가 기준 | 충족 | 충족 | 테스트로 확인됨 | 독립값 100.000000000000, 허용 오차 1e-9, 저장소와의 차이 1.1e-12. |
| 가격 역산 | 충족 | 충족 | 테스트로 확인됨(QuantLib은 NOT_RUN) | 6.1776904062%, 4.8626816895%. 저장소 brentq와 Newton·이분법·numpy.roots의 차이는 8.5e-16 이하입니다. QuantLib은 미설치입니다. |
| 위험 지표 | 충족 | 충족 | 테스트로 확인됨 | Macaulay·Convexity는 유한차분과, DV01은 ±1bp 중심차분과 일치합니다(차이 1.35e-4, 3차항). 단위 정의는 ④ 4.2에 적었습니다. HEAD 화면에는 단위가 없습니다(BS-22). 패치는 Conventions notice로 알립니다. |
| 시나리오 재평가: 중간값 로그와 재현 | 충족 | 충족 | 테스트로 확인됨 | 시나리오마다 key tenor의 zero, DF, DF·e^(−zt), 새 가격, P&L을 로그로 남겼습니다(C의 c1, c5). 합성·평탄·가상 곡선에서 저장소와 독립 구현의 차이는 3.7e-9원 이하입니다. |
| 시나리오 재평가: 소유자 2.3 화면 숫자 | 미확인 | 미확인 | 미확인 | 그날의 곡선 스냅샷이 없습니다. 가상 우상향 곡선(시장 자료 아님)으로 9개 중 8개 문자열이 같았지만, 날짜와 출처를 특정할 수 없습니다. |
| 선물 헤지 | 충족 | 충족 | 테스트로 확인됨(어느 입력 경로였는지는 미확인) | 화면 'Position DV01 798', '9.82', 'Rounded 10', 잔여 '−14'는 두 경로가 똑같이 만듭니다. 칸을 비운 경우: 계산기 DV01 798.185618 × 0.8 / 65 = 9.823823, 잔여 −14.3144. 798을 입력한 경우: 798 × 0.8 / 65 = 9.821538, 잔여 −14.50. HEAD는 Position DV01을 0자리로 보이므로 화면만으로는 구분할 수 없습니다(`W/critic/indep.log`, `W/patch/logs2/compare_ba.txt` 'position 798 typed' 행). 요청서의 "9.815…"는 오기입니다. 두 경로 모두 잔여가 실제 Rounded 10과 맞습니다. 잔여 부호의 뜻은 HEAD에 없고 패치에 있습니다. |
| 데이터 출처: 실제 FRED 강제 | 미확인 | 미확인 | 미확인(NOT_RUN) | FRED 접속이 프록시에서 403으로 막혔습니다. FRED 표시 경로는 stub과 로컬 프록시로만 시험했습니다. |
| 데이터 출처: synthetic fallback 강제 | 부분 충족 | 충족, 단 차트 제목의 출처는 미반영(BS-35) | 테스트로 확인됨 | 배지는 맞습니다: 빨간 배너 "Synthetic data: FRED failed: …", 칩 `curve: SYNTHETIC 2026-10-27`, payload `data_source: SYNTHETIC`. 그러나 as-of 칩은 오늘 날짜이고, 숫자는 매일 같은 고정 시뮬레이션입니다(BS-34, `core/ficc/data.py:_business_dates:288-295`, 고정 seed `:366`). 카드·차트 제목·시나리오 표·해설에도 출처가 없습니다(BS-35, D03-03). 패치는 칩을 "SYNTHETIC (simulated, dated …)"로 바꾸고 해설에 출처를 넣었습니다. |
| 회귀 테스트(단위 테스트 추가와 CI 실행) | 미충족 | 미확인 | HEAD: 코드로 확인됨(해당 테스트 없음). 패치: 테스트로 확인됨(33/33). CI: 미확인 | HEAD에는 해당 회귀 테스트가 없습니다. 패치는 `tests/bonds_screen_acceptance.py` 33개를 추가하고 run_all에 `bonds`로 등록했습니다. 저장소에 CI 설정이 없어 CI 실행은 미확인입니다. |

---

## ② 심각도별 이슈

### 2.1 목록

'관련 ID' 열은 차원 보고서 ID와 그 검증 심각도입니다. 79행 전체 매핑은 부록 B에 있습니다.

| ID | 심각도 | 판정 | 관련 ID (검증 심각도) | 위치 | 내용 | 패치 |
|---|---|---|---|---|---|---|
| BS-01 | P1 | 테스트로 확인됨 | F-01 P1, A-06 P2, F-02 P2, G-01 P2 (P01-05 인용) | ui/bonds_page.py:run:94-224 | 동시 Run에서 이전 결과·오류가 새 결과를 덮음. 입력을 두 시점에 읽음 | 반영 |
| BS-02 | P2 | 테스트로 확인됨 | A-01 P2, A-02 P2, F-03 P2, G-02 P2 | ui/bonds_page.py:63-89 | 입력·도구를 바꿔도 이전 결과가 표시 없이 남음 | 반영 |
| BS-03 | P2 | 테스트로 확인됨 | F-04 P2, A-09 P3 | ui/bonds_page.py:81-83, 117, 193-201 | 숨은 Position DV01 수동값이 남고 표시가 없음 | 반영 |
| BS-04 | P2 | 테스트로 확인됨 | A-03 P2, G-08 P3, A-08 P3 | ui/bonds_page.py:69-72; core/ficc/bonds.py:236-237 | 가격/수익률 계약이 모호함. 같은 오류 문구, 필드 표시 없음 | 반영(모드 선택기 제외) |
| BS-05 | P2 | 테스트로 확인됨 | A-04 P2, G-03 P2, D-02 P2 | ui/bonds_page.py:107-108, 117 | 빈칸을 조용히 기본값으로 바꿈(CF 1.0 대 표시 0.8) | 반영 |
| BS-06 | P2 | 테스트로 확인됨 | A-05 P2, G-04 P2, A-10 P3 | ui/bonds_page.py:_num:40, 48 | 쉼표를 모두 지움. '4,5'가 45% | 반영 |
| BS-07 | P2 | 테스트로 확인됨 | A-07 P2, B-02 P3, B-04 P3, M-1(B) P3 | core/ficc/curves.py:47; bonds.py:188; ui/bonds_page.py:107 | 정의역 방어 없음. IndexError, scipy 문구, GB 메모리 | 반영(코어 만기 상한 제외) |
| BS-08 | P2 | 테스트로 확인됨 | B-01 P2, F-05 P2, G-06 P2, M-3(B) P3 | core/ficc/bonds.py:carry_roll:189-208 | 만기가 horizon 안인 채권의 carry/roll·breakeven 오류 | 반영 |
| BS-09 | P2 | 테스트로 확인됨 | C-01 P2 (F-07 일부, F-07은 BS-22에서 셈) | core/ficc/bonds.py:288-292; ui/bonds_page.py:52-56, 180; insights.py:112-113 | 시나리오 충격 단위(연속복리 zero) 미표시, 해설과 정의 혼용 | 반영(notice 괄호 문구에 P3 잔여, RP-01) |
| BS-10 | P2 | 테스트로 확인됨 | C-04 P2, E-09 P2 | core/ficc/bonds.py:shocked_curve:293-296 | 충격을 곡선 knot에만 적용. 부분 곡선에서 모양이 바뀜 | 반영 |
| BS-11 | P2 | 테스트로 확인됨 | C-03 P2 | core/ficc/bonds.py:283; ui/bonds_page.py:52-56 | fly 정의가 문서화되지 않음. −12.5를 −12로 표시 | 표시만 반영 |
| BS-12 | P2 | 테스트로 확인됨 | D-01 P2, G-05 P2 | ui/bonds_page.py:199-209 | 숏 포지션에 "Contracts to sell −9.82" | 반영 |
| BS-13 | P2 | 코드로 확인됨(고지·hint·tooltip 부재, D-03) + 테스트로 확인됨(단위 오입력, M-2(D)) | D-03 P2, M-2(D) P3 | ui/bonds_page.py:77-83, 196-206 | 헤지 근사·단위·예시값 미고지. 1,000배 단위 오입력 무경고 | 반영(README 제외) |
| BS-14 | P2 | 테스트로 확인됨 | E-01 P2 | core/ficc/data.py:_treasury_from_fred:571-596 | 오래된 FRED 곡선도 녹색 칩, 경고 없음 | 반영 |
| BS-15 | P2 | 테스트로 확인됨 | E-02 P2, E-V01 P2 | core/ficc/data.py:577-589, 220-221 | 만기별 관측일이 섞인 곡선을 한 날짜로 표시 | 반영 |
| BS-16 | P2 | 테스트로 확인됨 | E-03 P2 | core/ficc/data.py:582 | 곡선 값의 범위·단위·급변 검사 없음 | 반영 |
| BS-17 | P2 | 테스트로 확인됨 | E-V03 P2, G-V01 P2, F-06 P2, G-10 P3 | core/ficc/data.py:_fred_fetch:168, _provider_rows:474-484 | 응답 없는 망에서 Run 한 번에 약 24분. 실패를 기억하지 않음 | 부분 반영 |
| BS-18 | P2 | 테스트로 확인됨 | G-07 P2(P3에서 올림) | ui/qcharts.py:_style:43; ui/fcharts.py:144, 164, 186 | 차트 제목이 검정이라 보이지 않음 | 반영 |
| BS-19 | P3 | 테스트로 확인됨 | A-11 P3 | ui/bonds_page.py:_num:49 | Yield '-0'이 '-0.000%'로 표시 | 반영 |
| BS-20 | P3 | 테스트로 확인됨 | B-03 P3 | core/ficc/bonds.py:53-57 | 정수가 아닌 freq를 조용히 버림(코어 API) | 미반영 |
| BS-21 | P3 | 테스트로 확인됨 | B-05 P3 | core/ficc/bonds.py:carry_roll:191 | 조달비용에 연속복리 zero를 단리처럼 사용 | 미반영 |
| BS-22 | P3 | 테스트로 확인됨 | B-06 P3, F-07 P3, F-M2 P3 | ui/bonds_page.py:63-168; bonds.py:15-18 | 계산 관례 미고지. (1+y/f) 문서 조건 누락 | 부분 반영 |
| BS-23 | P3 | 테스트로 확인됨 | M-2(B) P3 | ui/bonds_page.py:34-35, 137; insights.py:50-53 | 작은 명목에서 DV01이 0으로 표시 | 반영(KRD 제목 제외) |
| BS-24 | P3 | 테스트로 확인됨 | C-02 P3 | core/ficc/bonds.py:319; ui/bonds_page.py:180 | P&L %의 분모(시장가치) 미표기 | 반영(차트 축 제외) |
| BS-25 | P3 | 테스트로 확인됨 | C-05 P3, E-V02 P3 | core/ficc/data.py:361-377 | 합성 곡선 최신 행이 9.6% 역전(문서는 약 4%) | 미반영 |
| BS-26 | P3 | 테스트로 확인됨(C-06) / 코드로 확인됨(G-12, M-4(D)) | C-06 P3, G-12 P3, M-4(D) P3 | tests/ficc_acceptance.py:279-287; ui/bonds_page.py:247-319 | 시나리오 골든값 없음, self-check 동기 실행, UI 회귀가 CI 밖 | 부분 반영 |
| BS-27 | P3 | 테스트로 확인됨 | D-04 P3 | ui/bonds_page.py:194-211 | 잔여 DV01 부호 설명·타일·payload 없음 | 반영 |
| BS-28 | P3 | 테스트로 확인됨 | D-05 P3 | ui/bonds_page.py:200, 205, 209 | 반올림이 half-to-even(10.50 → 10) | 반영 |
| BS-29 | P3 | 테스트로 확인됨 | D-06 P3 | ui/bonds_page.py:194, 203 | Position DV01을 0자리로 표시해 손검산 불일치 | 반영 |
| BS-30 | P3 | 테스트로 확인됨 | D-07 P3 | core/ficc/bonds.py:327-329 | 헤지 overflow·NaN 방어 없음 | 반영 |
| BS-31 | P3 | 테스트로 확인됨 | D-08 P3, E-08 P3 | ui/bonds_page.py:107-113 | 곡선·채권 단계 실패가 곡선과 무관한 결과까지 막음 | 미반영 |
| BS-32 | P3 | 코드로 확인됨 | D-09 P3 | ui/structuring_page.py:231; core/ficc/structured.py:420 | Structuring과 Bonds의 "DV01 / contract" 의미 차이 | 미반영 |
| BS-33 | P3 | 코드로 확인됨 | M-3(D) P3 | docs/audit/2026-10-27/functional_completeness.md:146 | 기존 FC-03의 KTB 선물 연결 제안이 CF 전제와 충돌 | 미반영 |
| BS-34 | P3 | 테스트로 확인됨 | E-04 P3 | ui/bonds_page.py:126-127; data.py:288-295 | 칩 날짜의 뜻이 불명확. 합성 날짜 = 오늘 | 반영 |
| BS-35 | P3 | 테스트로 확인됨 | E-05 P3 | ui/bonds_page.py:131-187; ui/fcharts.py:144, 164 | 곡선 의존 카드·차트·표에 출처 없음 | 부분 반영 |
| BS-36 | P3 | 테스트로 확인됨 | E-06 P3, F-M1 P3 | ui/bonds_page.py:141-154 | 사용한 곡선 값과 스냅샷 id를 기록하지 않음 | 부분 반영 |
| BS-37 | P3 | 테스트로 확인됨 | E-07 P3, G-10 P3(문구, BS-17에서 셈) | core/ficc/data.py:574-576; ui/bonds_page.py:123 | 실패 사유 11회 반복, 환경 정보가 payload에 들어감 | 반영(주소 제거는 없음) |
| BS-38 | P3 | 코드로 확인됨(위험은 미확인) | F-08 P3 | ui/qcharts.py:21, 48-62 | 작업 스레드에서 pyplot 사용 | 미반영 |
| BS-39 | P3 | 테스트로 확인됨 | G-09 P3 | ui/bonds_page.py:67-82 | 라벨 잘림, 단위 없음, Dropdown 접근성 이름 없음 | 부분 반영 |
| BS-40 | P3 | 테스트로 확인됨 | G-11 P3 | requirements.txt:1; pyproject.toml:11 | flet_web 0.85.2와 fastapi 0.162 비호환(웹 모드) | 미반영 |
| BS-41 | P3 | 테스트로 확인됨 | G-V02 P3 | ui/bonds_page.py:163-164 | Breakeven 툴팁이 음수 값과 반대 뜻 | 반영 |

P0는 없습니다. 주문 경로가 없고, 안전 규칙 위반도 찾지 못했습니다. 합성 데이터는 배너로 표시됩니다.

### 2.2 P1

**BS-01 · P1 · 테스트로 확인됨 · 동시 Run에서 이전 결과가 새 결과를 덮음** (F-01 P1, A-06 P2, F-02 P2, G-01 P2)
- 재현 1 (실제 브라우저, G race2):
  1. Curve source를 Auto로 둡니다. FRED는 호출당 1초 지연 뒤 12회 실패하도록 막았습니다.
  2. Coupon 4.50, Yield 4.50으로 Run #1을 누릅니다.
  3. 이어서 Synthetic demo, Coupon 6.00으로 바꾸고 Run #2를 누릅니다.
  4. +4.07초: Run #2의 결과 111.973이 뜨고 진행 링이 꺼집니다.
  5. +12.31초: Run #1이 100.000과 "FRED failed" 배너로 화면을 덮습니다. 입력칸은 Synthetic demo / 6.00 그대로입니다.
  - 스크린샷: `Q1_run2_shown_run1_pending.png`, `Q2_run1_overwrites_run2.png`, `crop_Q2_run1_overwrites_run2.png`.
- 재현 2 (stand-in 페이지, 실제 스레드, F):
  - 늦은 이전 결과가 덮습니다. 최종 화면은 107.982와 "The 5.50% 10y" 해설인데 Coupon 칸은 4.5입니다.
  - 늦게 실패한 이전 Run의 FRED 오류가 새 Run의 정상 결과를 지웁니다.
- 재현 3 (찢어진 읽기):
  - F: 클릭한 뒤 곡선 로드 중에 Coupon 4.5, Price 105, CF 0.7로 고칩니다. 결과는 Price 105.000, 4.863%, CF 0.7000, 8.70계약이고, 해설은 "The 5.50% … prices at 105.000"입니다. 어느 한 순간에도 존재하지 않았던 입력 조합입니다.
  - G: Yield 4.50으로 Run한 뒤 실행 중에 Yield를 지우고 Price 95를 넣습니다. "Give exactly one of price or ytm."가 나옵니다. 클릭할 때도, 마지막 입력도 두 칸이 동시에 차 있던 적이 없습니다.
- 원인:
  - 클릭할 때마다 작업자 스레드를 새로 띄웁니다(`ui/bonds_page.py:224`). 재진입 검사, 버튼 비활성화(`:237`), 실행 토큰이 없습니다.
  - 작업자는 살아 있는 입력칸을 곡선 로드 전(`:105-109`)과 후(`:112`, `:117`)에 읽습니다.
  - 성공 경로(`:216-218`)와 실패 경로(`fail:99-102`) 모두 결과 영역을 조건 없이 바꿉니다.
  - Flet 0.85.2의 `run_thread`는 실제 executor 스레드입니다(`flet/controls/page.py:827-846`, F 검증).
- 영향: FRED가 느릴 때 다시 누르면 다른 입력으로 계산한 숫자가 현재 결과처럼 보입니다. 링이 꺼져 계산이 끝난 것처럼 보입니다. 세 도구 모두 해당합니다.
- 최소 수정:
  - 클릭할 때 UI 스레드에서 입력 전체를 한 번 읽고 검증합니다(`_snapshot`).
  - 실행 토큰 `state['run']`을 둡니다.
  - 결과와 오류는 lock 안에서 자기가 최신 토큰일 때만 그립니다.
- 회귀 테스트: test_newest_run_wins_when_runs_finish_out_of_order, test_late_failure_does_not_replace_a_newer_result, test_a_run_uses_the_inputs_of_its_click. HEAD에서 FAIL, 패치에서 PASS입니다.
- 남는 것: Run 버튼 비활성화(P01-05)는 넣지 않았습니다. 무효가 된 작업자는 끝까지 실행되고, 네트워크 비용도 그대로 듭니다.
- 심각도 메모: F는 P1, A와 G는 같은 원인을 P2로 적었습니다. 통합 판정은 P1입니다. 다른 입력의 결과를 아무 표시 없이 현재 결과처럼 보이기 때문입니다(P1 정의의 "낡은 데이터를 실제처럼 표시").

### 2.3 P2

**BS-02 · 입력·도구를 바꿔도 이전 결과가 표시 없이 남음** (A-01 P2, A-02 P2, F-03 P2, G-02 P2)
- 재현:
  1. Calculator에서 Coupon 5.5, Yield 4.5, Price 빈칸으로 Run합니다. 결과는 107.982입니다. Price에 100을 넣고 Run하지 않으면 화면이 그대로입니다(1.3).
  2. Calculator 결과가 있는 상태에서 Tool을 Futures hedge로 바꿉니다. 헤지 입력줄 아래에 calc 결과가 그대로 남습니다.
  3. hedge Run 뒤 Tool을 Calculator로 바꿉니다. 헤지 입력은 숨겨지는데 "Contracts to sell" 결과는 남습니다.
  - 스크린샷: `S3b_typed_price95_no_run.png`, `S4a_tool_scenarios_no_run.png`, `S5a_tool_hedge_no_run.png`, `S6_back_to_calc_no_run.png`.
- 원인:
  - TextField 8개에 `on_change`가 없고, Coupons/year·Curve source에 `on_select`가 없습니다.
  - `on_tool`은 `hedge_row.visible`만 바꿉니다(`:87-89`).
  - 결과가 어떤 입력으로 계산됐는지 기록하지 않습니다.
- 영향: 모든 도구에 해당합니다. 화면에 보이는 입력과 다른 입력으로 계산한 가격·DV01·시나리오·헤지가 진짜 결과처럼 남습니다. 소유자 표 2.1의 1·2행이 실제 사례입니다.
- 최소 수정:
  - 모든 입력에 변경 핸들러를 답니다.
  - 현재 입력이 결과를 만든 입력과 다르면 결과 위에 경고 배너를 띄웁니다. 값을 되돌리면 배너가 사라집니다.
  - 결과 맨 위에 "Computed for: …" 줄을 둡니다.
- 회귀 테스트: test_edit_after_run_marks_the_result_and_revert_unmarks, test_every_input_has_a_change_handler, test_echo_keeps_the_typed_digits_and_names_the_served_curve. HEAD에서 FAIL, 패치에서 PASS입니다.
- 심각도 메모: A는 P1로 올렸고 검증자가 P2로 낮췄습니다. 타일이 실제로 쓴 Price/Yield를 보이고 해설이 쿠폰·만기를 적기 때문입니다. 이 보고서도 P2로 둡니다.

**BS-03 · 숨은 Position DV01 수동값이 남음** (F-04 P2, A-09 P3)
- 재현:
  1. hedge에서 Position DV01 798로 Run합니다.
  2. calc로 바꿔 Notional 2,000,000으로 Run합니다.
  3. 다시 hedge로 Run합니다.
  - 결과: DV01 카드는 1,596인데 Position DV01은 798, Contracts는 9.82입니다. 계산기 DV01로 계산하면 1,596.37 × 0.8 / 65 = 19.65계약입니다.
- 원인: 숨겨진 칸이 값을 그대로 유지합니다. 수동값과 계산값을 같은 라벨로 보입니다. 툴팁만 "unless overridden"이라고 적습니다.
- 영향: 수동값을 잊으면 이 예에서 헤지가 절반이 됩니다.
- 최소 수정: 라벨을 "Position DV01 (override)" / "(calculator)"로 나눕니다. 수동값이 계산기 DV01과 1%보다 많이 다르면 경고를 띄웁니다.
- 회귀 테스트: test_hedge_override_is_named_and_warned. 반영했습니다.

**BS-04 · 가격/수익률 계약이 모호함** (A-03 P2, G-08 P3, A-08 P3)
- 재현:
  - 기본 화면(Yield가 4.50으로 미리 채워짐)에서 Price 100만 넣고 Run하면 "Give exactly one of price or ytm."가 나옵니다.
  - 두 칸을 모두 비워도 같은 문구입니다.
  - Coupon −1을 넣으면 "coupon must be a finite non-negative decimal, got -0.01."이 나옵니다(소수 단위, 필드 이름 없음).
  - 헤지의 CTD 0·−1, CF 0·−0.8은 모두 같은 문구 "CTD DV01 per contract and conversion factor must be positive."를 냅니다. 어느 칸이 틀렸는지 말하지 않습니다(BS-05의 헤지 입력 표).
  - 스크린샷: `S2_price100_and_yield450.png`, `S2b_both_blank.png`.
- 원인:
  - 계약을 코어에서만 검사하고, 코어 문구(내부 이름 ytm, 소수 단위)를 그대로 보입니다.
  - 필드 오류(TextField.error)를 설정하는 곳이 0곳입니다.
  - 빈 화면 안내는 첫 Run 뒤 사라집니다.
- 영향: 가격으로 호가하려는 사용자는 처음에 반드시 오류를 만납니다. 어느 칸을 고칠지 알 수 없습니다.
- 최소 수정:
  - 화면에서 먼저 검증하고, 둘 다 채운 경우와 둘 다 빈 경우에 다른 문구를 씁니다.
  - 두 칸 모두에 field error를 붙입니다. 메시지에는 화면 라벨과 사용자 단위를 씁니다.
  - 한 칸을 고치면 두 칸에 붙은 짝 오류를 함께 지웁니다.
  - "Quote by" 모드 선택기는 넣지 않았습니다. 수용 기준 4-1의 뜻이 바뀌므로 소유자가 정할 일입니다.
- 회귀 테스트: test_price_yield_exclusive_with_field_errors, test_clearing_one_of_price_and_yield_clears_the_pair_error.

**BS-05 · 빈칸을 조용히 기본값으로 바꿈** (A-04 P2, G-03 P2, D-02 P2)
- 재현:
  - Coupon 빈칸: 0% 무이표채로 계산합니다(64.082, DV01 627, 독립 계산 64.081647).
  - Maturity 빈칸: 10년. Notional 빈칸: 1,000,000.
  - hedge에서 CF 빈칸: CF 1.0000, 12.28계약, Rounded 12, 잔여 +18입니다. 칸에 보이던 0.8이었다면 9.82입니다.
  - CTD 빈칸: 65로 계산합니다(9.82계약).
  - 스크린샷: `B1_coupon_blank.png`, `B2_maturity_blank.png`, `B3_notional_blank.png`, `S5f_hedge_cf_blank.png`.
- 헤지 입력 방어 전체 결과(요청 3.D 다섯째 항목, 테스트로 확인됨). stand-in 페이지, 합성 곡선, 기본 채권(4.5%, 10년, Yield 4.5)입니다. 근거: `W/critic/drive_edges_head.log`, `W/critic/drive_edges_patched.log`, `W/corrections_r1/drive_hedge.log`. CTD 0은 실제 브라우저에서도 같았습니다(3.4 단계 5e).

| 입력 | HEAD | 패치 |
|---|---|---|
| CTD 0 | "CTD DV01 per contract and conversion factor must be positive." | "CTD DV01 / contract: must be > 0, got 0." |
| CTD −1 | 같은 공통 문구 | "CTD DV01 / contract: must be > 0, got -1." |
| CF 0 | 같은 공통 문구 | "Conversion factor: must be > 0, got 0." |
| CF −0.8 | 같은 공통 문구 | "Conversion factor: must be > 0, got -0.8." |
| CF 'abc' | "Conversion factor: 'abc' is not a number." | 같음 |
| CTD 빈칸 | 오류 없이 65로 계산, 9.82계약, Rounded 10 | "CTD DV01 / contract: required." |
| CF 빈칸 | 오류 없이 1.0으로 계산, 12.28계약, Rounded 12 | "Conversion factor: required." |

  - HEAD의 공통 문구는 `core/ficc/bonds.py:futures_hedge_ratio:327-328`에서 나옵니다. 0과 음수는 막지만 어느 칸인지 말하지 않습니다(BS-04, BS-13의 필드 오류 부재 근거).
- 원인: `_num(field, default)`의 기본값을 씁니다(`:107-108`, `:117`). CF 기본값 1.0이 칸의 초기값 0.8과 다릅니다.
- 영향: 사용자가 지정하지 않은 채권과 헤지 비율로 결과가 나옵니다. CF는 계약 수가 25% 달라집니다.
- 최소 수정: Coupon·Maturity·Notional·CTD·CF를 필수로 바꿉니다. 빈칸이면 "<라벨>: required." 필드 오류를 냅니다. Position DV01만 "빈칸 = 계산기 값"을 유지합니다. 0 이하 값은 칸별 문구로 거부합니다.
- 회귀 테스트: test_required_fields_have_no_silent_default.

**BS-06 · 쉼표를 모두 지움** (A-05 P2, G-04 P2, A-10 P3)
- 재현:
  - Yield '4,5'(Coupon 4.50 기본값, 10년, 반기) → 45.000%, Price 11.554, z-spread +3251.5bp, DV01 35입니다(독립 계산 11.554249. 쿠폰 5.5%라면 13.738입니다).
  - '1,0,0'은 100, '1_000'은 1000으로 읽힙니다.
  - '1,2a'의 오류 문구는 "'12a' is not a number."입니다(사용자가 친 적 없는 값).
  - 스크린샷: `B4_yield_comma_decimal.png`.
- 원인: `_num`이 위치와 관계없이 쉼표를 지웁니다(`:40`). `float()`는 밑줄도 받습니다. 오류 문구에 쉼표를 지운 값을 씁니다.
- 영향: 소수점 쉼표 오타가 10배 다른 수익률이 되어 정상 결과처럼 표시됩니다.
- 최소 수정: 쉼표는 세 자리 구분자일 때만 받습니다. 오류 문구에는 입력 원문을 씁니다.
- 회귀 테스트: test_zero_negative_nan_inf_and_comma_inputs.

**BS-07 · 정의역 방어 없음** (A-07 P2, B-02 P3, B-04 P3, M-1(B) P3)
- 재현:
  - Maturity 1e-10: "IndexError: index -1 is out of bounds for axis 0 with size 0".
  - Maturity 1e5: "The function value at x=-0.5 is NaN; solver cannot continue."
  - 코어에서 만기 1e7: 10.2초, 메모리 933MB. 만기 1e8: 2.5GB 상한에서 MemoryError.
  - Yield 201: "No yield in [-0.5, 2.0] reproduces price 2.7364." 수익률을 넣었는데 가격 문구가 나옵니다.
  - Yield −45: "No z-spread in [-0.5, 2.0] reproduces 17993.5701."
  - Maturity 0과 −1은 코어가 명확히 거부합니다("maturity must be positive years, got 0.0." / "… got -1.0."). Price 0.01과 1은 "No yield in [-0.5, 2.0] reproduces price 0.0100." / "… 1.0000."입니다(3.3 참고).
- 원인:
  - UI에 범위 검사가 없습니다.
  - `coupon_times`가 현금흐름 0개(n=0)를 허용합니다(`core/ficc/curves.py:47`).
  - 만기 상한이 없습니다.
  - `carry_roll`이 가격에서 수익률을 다시 풉니다(`bonds.py:188`).
  - 깊은 음수 수익률에서는 z-spread 구간이 먼저 걸립니다. 합성 곡선 기준 하한은 freq 1에서 −33.5%~−35.2%, freq 2에서 −36.9%~−39.0%, freq 4에서 −38.8%~−41.1%입니다.
- 영향: 극단 입력이나 오타에서 원인을 알 수 없는 문구가 나옵니다. 만기 오타 한 번에 수 초와 GB 단위 메모리를 씁니다. 틀린 숫자는 나오지 않습니다.
- 최소 수정:
  - UI 범위를 Maturity (0, 100], Yield % (−50, 200]로 두고 필드 오류를 냅니다.
  - `coupon_times`에서 n ≥ 1로 둡니다.
  - z-spread 실패를 입력 필드를 밝힌 문구로 바꿉니다.
- 회귀 테스트: test_tiny_maturity_prices_instead_of_index_error, test_a_quote_too_far_from_the_curve_names_the_field, test_zero_negative_nan_inf_and_comma_inputs.
- 남는 것:
  - 코어 `Bond`에는 만기 상한이 없습니다(API 위생).
  - 가격 하한 쪽 문구는 패치 뒤에도 필드를 밝히지 않습니다. Price 0.01이면 여전히 "No yield in [-0.5, 2.0] reproduces price 0.0100."이고, 구간이 소수 단위입니다(P3, 테스트로 확인됨, `W/critic/drive_edges_patched.log`). 패치는 만기만 "Maturity (years): must be > 0 and <= 100"으로 바꿨습니다.

**BS-08 · 만기가 horizon 안인 채권의 carry/roll** (B-01 P2, F-05 P2, G-06 P2, M-3(B) P3)
- 재현:
  - Calculator, Coupon 5.5, Maturity 0.25, Semi-annual, Yield 4.5, 합성 곡선: Roll-down −1.613, Carry + roll −2.640, Breakeven −1062.6bp.
  - Maturity 0.1, Coupon 4.5: "Carry (3m)" −0.520, Roll −1.796, Breakeven −2325.9bp.
  - 스크린샷: `B5_maturity_short.png`.
- 독립 계산:
  - 0.25년: 만기까지 받는 현금 102.75 − 가격 101.6132 − 조달 z(h)·P·h = −1.2650.
  - 0.1년: −0.516.
  - 만기 0.25 ± 1e-7에서 HEAD의 total이 불연속하게 뜁니다.
  - 기울기 곡선에서는 Breakeven 부호가 바뀝니다(HEAD −423.1bp, 단순식 +130.4bp).
- 원인:
  - 만기가 horizon 안이면 시평 가치를 face로 둡니다(`bonds.py:carry_roll:201-202`). 가격은 dirty라 t=0 이전 경과이자를 포함합니다. 그런데 시평 가치를 face로 두어, 만기 쿠폰 중 그 경과분 c·100·(1/f − T)이 빠집니다. 시평까지 쌓인 경과분 c·100·T는 carry로 들어갑니다.
  - 라벨은 요청한 horizon(3m)을 쓰는데 계산은 h = min(0.25, T)를 씁니다.
  - 채권이 시평까지 남지 않는데도 breakeven 식을 적용합니다.
- 영향:
  - 대상 카드: Roll-down, Carry + roll, Breakeven, 해설, AI payload.
  - 대상 채권: 만기 0.25년 이하의 연·반기 채권, 0.25년 미만의 분기 채권.
  - 오차: 100당 c·100·(1/f − T)입니다. 5.5% 반기 0.25년이면 1.375입니다(4.7 표의 −1.375, −1.430, −2.200과 같음).
  - 가격, 수익률, 듀레이션, DV01, KRD, z-spread, 시나리오는 영향이 없습니다.
- 최소 수정:
  - 만기 분기에서 받은 현금 전부를 씁니다(total = Σcf − P − 조달).
  - horizon = h를 반환합니다.
  - breakeven은 NaN으로 두고 화면에 "n/a"를 보입니다. 해설은 "no yield move changes this hold-to-maturity result"로 씁니다.
- 회귀 테스트: test_carry_roll_for_a_bond_maturing_inside_the_horizon, test_narrative_for_a_bond_maturing_inside_the_horizon. 이 보고서의 재실행에서 패치 total −1.2650이 독립값 −1.2650과 같았습니다.
- 심각도 메모: 경계 사례라 P2로 둡니다. 검증자는 "P1 경계"라고 적었습니다.

**BS-09 · 시나리오 충격 단위가 표시되지 않음** (C-01 P2, F-07 일부)
- 재현:
  - 5.5%, 10년, 수익률 5.5%, 자기 수익률의 평탄 곡선: Scenarios +100bp는 −74,780.1입니다.
  - 수익률을 +100bp 올려 재평가하면 −72,696.7입니다.
  - 1bp에서 두 값의 비율은 1.02751 = 1 + y/f입니다.
  - 가상 곡선에서 해설은 "DV01 is 836 per bp; a +100bp parallel move costs roughly 83,629 before convexity"라고 씁니다. 같은 카드의 표는 "+100bp parallel −81,597"입니다.
- 원인: `scenario_pnl`은 `curve.shifted(bp)`로 연속복리 zero에 bp를 더합니다. 표 헤더는 "Shock", 문구는 "+100bp parallel"뿐입니다. 해설, DV01, 가격-수익률 차트는 채권 수익률 기준입니다.
- 영향: YTM ±100bp나 DV01 × 100으로 표를 검산하면 설명되지 않는 2.3~2.9% 차이가 납니다(명목 1,000,000에서 약 1,900~2,100).
- 최소 수정:
  - 헤더를 "Shock (bp, cc zero rates)", "P&L % of MV"로 바꿉니다.
  - notice에 이 곡선에서 +100bp 행이 채권 수익률을 실제로 얼마나 움직였는지(예: +103.2bp) 보입니다.
  - 비교 기준으로는 1차 근사 100·(1 + y/f) = +102.2bp(y 4.5%, 반기)를 씁니다. 이 값은 1bp 극한의 기울기입니다. 평탄 곡선에서 +100bp zero 이동의 정확한 수익률 변화는 (f + y)(e^{Δ/f} − 1)이고, A는 +102.506bp, B는 +103.007bp입니다(4.4).
  - 해설에는 "per bp of the bond's own yield"라고 기준을 밝힙니다.
- 회귀 테스트: test_scenario_pnl_is_reprice_times_notional_with_zero_rate_shocks, test_scenario_notice_reports_this_curves_yield_move, test_narrative_separates_yield_dv01_from_zero_curve_scenarios.
- 남는 것(최종 패치, P3, 테스트로 확인됨): 패치본 notice(`ui/bonds_page.py:374-390`)는 괄호 안의 1차 근사 +102.2bp를 "on a curve flat at this yield"의 값이라고 적습니다. 평탄 4.5% 곡선에서 같은 notice는 "moves its yield by +102.5bp (+102.2bp, 100 x (1 + y/f), on a curve flat at this yield)"를 보여 두 숫자가 어긋납니다. 테스트 `tests/bonds_screen_acceptance.py:877-890`이 이 문구를 그대로 단언합니다(5.6 RP-01).

**BS-10 · 충격을 곡선 knot에만 적용** (C-04 P2, E-09 P2)
- 재현:
  - 4.5% 30년 채권, FRED가 DGS20·DGS30을 주지 않음(auto): bear steepener −22,369(전체 곡선 −59,696), bull flattener +23,157(+67,476), fly +18,757(+1,373). 칩은 녹색 FRED이고 배너가 없습니다.
  - 7y knot이 빠진 곡선의 7년 채권: bear steepener −5,866.8(전체 −5,043.8, +16.3%).
- 원인:
  - `shocked_curve`가 충격을 곡선 knot에만 더합니다(`bonds.py:293-296`).
  - 마지막 knot 뒤에서는 zero가 평탄하므로 충격도 평탄해집니다.
  - `key_rate_shifted`는 bump tenor를 knot으로 넣지만 `shocked_curve`는 넣지 않습니다.
- 영향: 부분 곡선(D03-V01 조건)에서 장기 시나리오 손익이 약 1/3로 줄고, 같은 이름의 시나리오가 다른 모양이 됩니다. 11개 만기가 모두 있으면 영향이 없습니다.
- 최소 수정: 충격 tenor를 보간한 zero 값으로 knot에 넣은 뒤 bp를 더합니다. 전체 곡선에서는 결과가 바뀌지 않습니다(가격 차이 < 1e-9).
- 회귀 테스트: test_named_shocks_bite_at_their_own_tenors_on_a_partial_curve.

**BS-11 · fly 정의가 문서화되지 않음** (C-03 P2)
- 재현:
  - Shock 열은 "3m +0 / 2y -12 / 5y +25 / 10y -12 / 30y +0"을 보입니다.
  - 실제 정의는 2y −12.5, 3y 0, 5y +25, 7y 0, 10y −12.5, 20y 0입니다.
  - 4.5% 7년 채권(평탄 4.5%)의 fly 손익은 −794입니다. 2y·5y·10y 사이를 선형으로 잇는 fly였다면 −6,142입니다.
- 원인: SCENARIO_SHOCKS가 중간 key tenor를 0으로 둡니다(`bonds.py:283`). `_shock_text`는 5개 tenor만 `:+.0f`로 보여서, −12.5가 half-even 반올림으로 −12가 됩니다.
- 해석 정정(검증자): HEAD의 모양은 앱 KRD 삼각 bump의 조합 −12.5·KR2 + 25·KR5 − 12.5·KR10과 같습니다(7년 채권 −796.9 대 −800.9). 일관된 정의이고, 결함은 표시와 문서입니다.
- 영향: 3~4년, 6~9년 채권의 fly 손익이 문서화되지 않은 모양에서 나옵니다.
- 최소 수정(반영): 모든 key tenor를 소수 한 자리로 표시하고, 정의를 주석에 적습니다. 정의 자체는 HEAD 그대로입니다. 선형 fly로 바꿀지는 소유자가 정합니다. 바꾼다면 양 끝을 1y·20y에서 0으로 줄여야 합니다(M-02).
- 회귀 테스트: test_scenario_pnl_is_reprice_times_notional_with_zero_rate_shocks("-12.5"와 "7y +0.0" 표시를 단언합니다).

**BS-12 · 숏 포지션 헤지 문구** (D-01 P2, G-05 P2)
- 재현: hedge, Position DV01 −798.19, CTD 65, CF 0.8로 Run합니다. 화면은 "Contracts to sell −9.82", "Rounded −10", "Sell that many to flatten a long position; the residual after rounding is +14 per bp."입니다. 스크린샷: `S5d_hedge_short_position.png`.
- 원인: 라벨과 문구가 롱 포지션을 전제합니다(`ui/bonds_page.py:199-209`). 부호는 식에서만 처리됩니다.
- 영향:
  - 부호를 포함한 숫자는 수학적으로 맞습니다(n −9.8238, 잔여 +14.31).
  - 그러나 "음수 매도"를 해석해야 매수라는 것을 압니다. 방향을 반대로 읽을 수 있습니다.
  - Bond가 notional ≤ 0을 거부하므로 숏은 수동값으로만 들어옵니다.
- 최소 수정: n ≥ 0이면 sell, 아니면 buy로 쓰고 절댓값을 보입니다. 문구와 해설도 같은 방향 단어를 씁니다.
- 회귀 테스트: test_hedge_798_x_08_over_65_side_rounding_and_residual.

**BS-13 · 헤지 근사·단위·예시값을 알리지 않음** (D-03 P2, M-2(D) P3)
- 판정: 고지·hint·tooltip 부재는 코드로 확인됨입니다(D-03, 화면 구동으로도 관찰). 단위 오입력이 1,000배 수량으로 조용히 나오는 것은 테스트로 확인됨입니다(M-2(D)).
- 재현:
  - 화면, docstring, README 어디에도 다음 내용이 없습니다: 단순 DV01 근사라는 것, CTD DV01의 단위(계약 액면당), 65와 0.8이 예시값이라는 것.
  - CTD를 0.065(액면 100당 단위로 잘못 입력)로 넣으면 9,823.82계약이 경고 없이 나옵니다.
  - 표시는 "CTD DV01 / contract 0.07"이라, 표시된 값으로는 공식을 재현할 수 없습니다.
  - CTD·CF 칸에는 필드 오류가 없고, 0·음수 입력의 공통 문구도 칸을 지목하지 않습니다(BS-05 표).
- 원인: 고지, hint, tooltip이 없습니다. CTD를 고정 2자리로 표시합니다. 크기 검사가 없습니다.
- 영향: 예시값으로 나온 수량을 실제 헤지 수량으로 읽을 수 있습니다. 단위 오입력이 1,000배 수량으로 조용히 나옵니다.
- 최소 수정:
  - notice "A DV01 approximation: futures DV01 = CTD DV01 / CF, with CTD DV01 per contract face; CTD and CF are your inputs, not market data; CTD switches, basis, delivery options, invoice price and yield beta are not modelled."를 띄웁니다.
  - CTD를 유효숫자로 표시합니다.
  - CF가 0.1~2 밖이거나 선물 DV01이 계약당 5~1000 밖이면 "Check the units … A rough guide, not exchange data" 경고를 띄웁니다. 이 범위는 거래소 자료와 대조하지 않았습니다(미확인).
- 회귀 테스트: test_hedge_override_is_named_and_warned(단위 경고), test_hedge_798_x_08_over_65_side_rounding_and_residual.
- 남는 것: README 설명은 넣지 않았습니다.

**BS-14 · 오래된 FRED 곡선이 녹색으로 표시됨** (E-01 P2)
- 재현: `_fred_fetch` stub이 11개 시리즈를 모두 2026-06-30에서 끝냅니다(오늘은 10-27). auto와 fred 모두 칩이 `curve: FRED 2026-06-30` 녹색이고 배너가 없습니다. z-spread는 +44.6bp, carry는 +0.142입니다.
- 원인: 최신 관측일을 오늘과 비교하지 않습니다. note는 SYNTHETIC일 때만 보입니다(`ui/bonds_page.py:122`).
- 영향:
  - 오래된 곡선으로 계산한 z-spread, carry/roll, KRD, 시나리오가 현재 값처럼 보입니다.
  - 날짜는 칩에 보이므로 숨겨지지는 않습니다.
  - 캐시는 원인이 아닙니다(TTL 6시간). FRED 자체의 갱신이 멈출 때만 생깁니다. 빈도는 미확인입니다.
- 최소 수정: 최신 관측일이 5영업일보다 오래되면 note "Stale: …"을 붙이고, "Curve check:" 경고 배너와 warning 칩을 보입니다.
- 회귀 테스트: test_stale_carried_forward_and_bad_unit_curves_are_flagged.

**BS-15 · 만기별 관측일이 섞인 곡선** (E-02 P2, E-V01 P2)
- 재현 1: DGS30만 2026-08-14(4.95)에서 끝나게 합니다. 칩은 `FRED 2026-10-23` 녹색입니다. 30년 채권의 z는 −47.7bp입니다(30y가 같은 날 4.62%라면 −12.2bp).
- 재현 2:
  1. Macro 화면이 DGS2·DGS10·DGS30을 10-22까지 캐시합니다.
  2. 그 뒤 FRED가 10-23 행을 냅니다.
  3. Bonds를 실행합니다. 칩은 `FRED 2026-10-23` 녹색인데, 10y는 10-22 값 4.05%입니다(10-23 값은 4.13%).
  4. z는 +44.6bp입니다. 모든 만기가 10-23이었다면 +36.8bp입니다.
- 원인:
  - 날짜 합집합 위에서 열마다 forward-fill한 뒤 마지막 행을 씁니다(`data.py:577-589`). 만기별 마지막 관측일은 버립니다.
  - FRED id별 캐시 키를 Macro·Rates·Structuring·Bonds가 공유합니다(`days=504`).
- 영향: 날짜가 섞인 곡선이 한 날짜와 녹색 칩으로 표시됩니다. 평소 사용(Macro를 연 뒤 6시간 안에 Bonds 실행)에서도 생깁니다. 차이는 보통 1영업일, 수 bp입니다.
- 최소 수정: 늦은 id는 캐시를 건너뛰고 한 번 다시 받습니다(TTL > 0일 때, 캐시 항목당 1회). 그래도 늦으면 "Carried forward to …: DGS30 last observed …" 경고를 띄웁니다.
- 회귀 테스트: test_curve_lagging_in_a_shared_cache_is_refetched, test_lagging_refetch_is_tried_once_per_cache_entry, test_stale_carried_forward_and_bad_unit_curves_are_flagged.
- 심각도 메모: P2를 유지합니다. 차이는 보통 1영업일·수 bp입니다(재현 z +44.6 대 +36.8bp). 가격·수익률·듀레이션·DV01·헤지는 곡선과 무관합니다. 다만 칩 날짜가 실제 관측일과 달라 P1("낡은 데이터를 실제처럼 표시")의 경계에 있습니다.

**BS-16 · 곡선 값을 검사하지 않음** (E-03 P2)
- 재현:
  - DGS10의 마지막 값만 14.05(4.05 대신): 칩 녹색, z −1802.3bp, Roll-down +5.534, Breakeven +71.1bp, 배너 없음.
  - 소수 단위(0.0405): z +441.0bp, Carry +1.115, 녹색.
  - 40.5: "Bootstrap cannot bracket a zero rate at 10y for par yield 40.5000%." FRED를 언급하지 않고, auto도 합성으로 대체하지 않습니다.
- 원인: v/100 변환 외에 범위·단위·급변 검사가 없습니다(`data.py:582`).
- 영향: 공급자 쪽 오타나 단위 변경이 실데이터 라벨을 단 큰 숫자가 됩니다. FRED H.15는 관리되는 출처라 실제 빈도는 낮을 것으로 보지만 미확인입니다.
- 최소 수정: 10y par가 0.1%~25% 밖이면 FICCError를 냅니다. auto는 표시된 합성으로, fred는 오류로 갑니다. 하루 변동이 100bp를 넘으면 "Check the print" 경고를 띄웁니다.
- 회귀 테스트: test_stale_carried_forward_and_bad_unit_curves_are_flagged.
- 남는 것: 이력 전체가 그럴듯한 수준에서 틀린 값은 통과합니다.

**BS-17 · FRED 실패 경로의 시간** (E-V03 P2, G-V01 P2, F-06 P2, G-10 P3)
- 재현:
  - 응답하지 않는 로컬 프록시(blackhole)를 두고 다른 연결은 막았습니다.
  - id 1개 `_fred_fetch`: 120.5초, 연결 4회.
  - HEAD의 전체 auto Run: 1,446.6초, 연결 48회(12 fetch × 4회).
  - 즉시 실패하는 망: Run마다 약 5초, 호출 12회. 여러 번 Run해도 줄지 않습니다.
  - FRED_BASE_URL을 바꿔도 이 경로는 고정 URL을 씁니다.
- 원인:
  - `_pdr.DataReader(ids, "fred", start)`에 timeout과 재시도 인자가 없습니다(`core/ficc/data.py:_fred_fetch:168`). 그래서 pandas_datareader 0.11.1의 기본값(timeout 30초, retry_count 3)을 쓰고, `config.HTTP_TIMEOUT_SECONDS`(12초)는 무시됩니다.
  - 일괄 호출이 실패하면 id 11개를 하나씩 다시 시도합니다(`data.py:474-484`).
  - 실패를 기억하지 않습니다.
- 영향:
  - 기본 출처가 auto인 Bonds·Rates·Structuring이 패킷을 버리는 방화벽이나 응답 없는 프록시 뒤에서 Run마다 약 24분 멈춥니다.
  - 다시 누르면 BS-01과 겹칩니다.
  - 틀린 숫자는 나오지 않습니다. 결국 표시된 합성 곡선으로 계산합니다.
- 최소 수정:
  - `FredReader(…, retry_count=0, timeout=HTTP_TIMEOUT_SECONDS)`를 씁니다.
  - 전송 실패이면서 경과 시간이 0.5 × timeout 이상이면 id별 재시도를 건너뜁니다. HTTP 404 같은 응답 오류는 계속 id별로 재시도합니다.
- 회귀 테스트: test_fred_fetch_is_bounded_and_a_hung_batch_is_not_retried_per_id, test_slow_batch_with_an_http_error_is_still_retried_per_id.
- 결과: timeout 3초로 둔 blackhole에서 3.11초, 호출 1회입니다.
- 남는 것: 실패 기억(negative cache)과 FRED_BASE_URL 반영은 넣지 않았습니다.

**BS-18 · 차트 제목이 보이지 않음** (G-07 P2, P3에서 올림)
- 재현: FICC 차트 어디서나 왼쪽 제목 색이 #000000이고 배경은 #171d21입니다(대비 약 1.2:1). 가려지는 제목의 예는 "Key-rate DV01, z-spread −317.8bp held — total 860 per bp", "Scenario P&L — full revaluation, z-spread held"입니다. 스크린샷: `zoom_chart_title.png`.
- 원인:
  - `ui/qcharts.py:_style:43`이 가운데 제목(`ax.title`)만 색칠합니다.
  - `ui/fcharts.py:144, 164, 186`은 `loc="left"`를 씁니다.
  - 앱 전체의 `set_title` 28곳이 `loc="left"`이고, `main.py`는 항상 다크 테마입니다(G 검증).
- 영향: 차트 제목에 담긴 가정("z-spread held"), KRD 합계, 다른 화면의 출처 표시와 고지문이 앱 전체에서 보이지 않습니다. 검증자가 P3에서 P2로 올렸습니다.
- 최소 수정: `_style`에서 left·center·right 제목 세 개 모두에 `pal.text` 색을 줍니다.
- 회귀 테스트: test_chart_left_titles_use_the_palette_text_colour. `zoom_FIX_chart_title.png`은 G 단계에서 같은 수정을 적용한 화면입니다.

### 2.4 P3

| ID | 관련 | 재현 | 원인 | 영향 | 최소 수정 | 회귀 테스트 | 패치 |
|---|---|---|---|---|---|---|---|
| BS-19 | A-11 P3 | Yield '-0'으로 Run하면 Price 145.000, Yield '-0.000%', 해설 "a yield of -0.000%" | float('-0')이 음의 0이고, 포맷이 부호를 그대로 찍음 | 0% 수익률이 음수처럼 보임 | _num이 v + 0.0을 반환 | test_zero_negative_nan_inf_and_comma_inputs | 반영 |
| BS-20 | B-03 P3 | Bond(0.05, 10, freq=2.9).freq == 2 | int()로 잘라냄 | UI는 1/2/4 Dropdown이라 도달 불가. 코어 API 위생 | 정수가 아니면 ValueError | B의 t7 test_non_integer_freq_is_rejected | 미반영 |
| BS-21 | B-05 P3 | 자기 수익률의 평탄 곡선(z=0)에서 정답 total은 0인데 HEAD는 0.0067 = P(e^(zh) − 1 − zh). 합성 곡선 carry −1.1773, DF와 일관된 값은 −1.2077 | funding = z(h)·P·h. 연속복리 zero를 단리처럼 씀 | 100당 0.0035~0.0304, breakeven 0.4bp 이하 | funding = P·(1/DF(h) − 1) | B의 t7 test_funding_uses_simple_rate_from_df | 미반영(관례 결정은 소유자) |
| BS-22 | B-06 P3, F-07 P3, F-M2 P3 | 화면에 dirty, 정산일, 경과이자, ACT/365F, 복리 기준, 단위 문구가 없음. DV01 836 옆에 KRD "total 860 per bp"가 설명 없이 있음. docstring의 "KRD 합 = (1+y/f) × DV01"은 평탄 곡선에서만 맞음(합성 곡선에서 비율 1.0288, 1.0342) | 모델 단순화가 docstring에만 있음 | 같은 화면의 "per bp" 숫자 2개가 2.9% 다름. clean 호가 입력 시 생기는 오차를 화면에서 알 수 없음 | Conventions notice, docstring에 조건 명시, 해설에 기준 명시 | test_narrative_separates_yield_dv01_from_zero_curve_scenarios | 부분(KRD 차트 제목 미반영) |
| BS-23 | M-2(B) P3 | Notional 500이면 DV01 카드 "0", 해설 "the DV01 is 0 per bp"(실제 0.418) | 항상 `,.0f`로 서식 | 금리 위험이 0처럼 보임 | 절댓값 100 미만이면 소수 둘째 자리 | test_narrative_separates_… ("0.42" 단언) | 반영(카드·해설) |
| BS-24 | C-02 P3 | 합성 곡선 A +100bp: 표 "P&L %" −7.61%(시장가치 기준). 명목 기준이면 −8.22% | 분모 미표기(bonds.py:319, 헤더 :180) | 프리미엄·디스카운트 채권에서 해석이 달라짐 | 헤더 "P&L % of MV" | test_scenario_pnl_is_reprice_… | 반영(차트 x축 제외) |
| BS-25 | C-05 P3, E-V02 P3 | 합성 패널의 최신 행이 par 9.586%(1m)에서 7.171%(30y)로 역전. docstring은 "level ~4%". 4.5% 10년 채권 z −315.9bp | 누적 랜덤워크의 첫 행을 고정하고 마지막 행을 씀 | 오프라인·대체 Run마다 비현실적 숫자(배너는 있음) | 워크를 뒤집거나 평균회귀를 넣음 | E 검증 v08_regression_m2 | 미반영(다른 화면 숫자가 바뀜) |
| BS-26 | C-06 P3, G-12 P3, M-4(D) P3 | 기존 시나리오 테스트는 부호·부등식만 봄(테스트로 확인됨, C-06). 페이지 self-check는 작업자를 동기로 돌려 BS-01·BS-02를 원리적으로 잡지 못함(코드로 확인됨, G-12). UI 회귀가 CI 밖에 있음(코드로 확인됨, M-4(D)) | 테스트 설계 | 회귀를 놓침 | 골든값·정의 테스트, 비동기 하네스, run_all 등록 | tests/bonds_screen_acceptance.py 33개 | 부분(CI 없음, self-check 미등록) |
| BS-27 | D-04 P3 | notice는 "residual after rounding is -14 per bp."뿐. 부호 뜻이 없고 payload에 rounded·residual이 없음 | 표시·payload 설계 누락 | −14를 손실 14로 오해할 수 있음 | "Net DV01 after hedge" 타일, over/under-hedged 표기, payload 확장 | test_hedge_798_… | 반영 |
| BS-28 | D-05 P3 | Position 682.5, CF 1이면 10.50인데 Rounded 10. 8.50은 8 | 내장 round()가 half-to-even | 정확히 .5일 때만. 잔여 크기는 같음 | 0에서 먼 쪽으로 반올림(round_contracts) | test_rounding_is_half_away_from_zero_as_decided | 반영 |
| BS-29 | D-06 P3 | Coupon 0, Yield 0.75이면 "924 x 0.8000 / 65.00 = 11.38"(924로 손계산하면 11.37). 격자 1,640개 중 491개(29.9%)가 불일치 | Position DV01을 0자리로 표시 | 수동 검산자가 오판할 수 있음. 798 입력과 빈칸(798.19)도 화면으로 구분되지 않음(4.5) | 소수 둘째 자리 표시 | test_hedge_798_… | 반영 |
| BS-30 | D-07 P3 | CTD 1e-320 또는 pos 1e308·CF 2이면 "OverflowError: cannot convert float infinity to integer". CF 1e-300이면 300자리가 넘는 타일. 코어가 NaN을 통과시킴 | 코어가 0 이하만 검사 | 극단 입력에서만 생김. 화면은 죽지 않음 | isfinite 검사, overflow 오류, CF 범위 경고 | test_hedge_798_…(방어 입력 6종) | 반영 |
| BS-31 | D-08 P3, E-08 P3 | fred 출처에서 FRED가 실패하면 가격·DV01·헤지 카드까지 없음. Position DV01을 직접 넣어도 채권 입력 오류나 곡선 실패면 헤지가 안 나옴 | worker가 곡선을 먼저 로드하고 try 하나로 감쌈 | 가용성 문제. 틀린 숫자는 없음 | 곡선과 무관한 카드는 따로 표시, 도구별 경로 분리 | 제안: fred 오프라인 + Position 798이면 9.82 표시 | 미반영 |
| BS-32 | D-09 P3 | Structuring "Futures DV01 / contract"에 65를 넣으면 12.28계약. Bonds "CTD DV01 / contract" 65, CF 0.8이면 9.82 | 두 화면의 입력 규약이 다름 | 화면을 오갈 때 혼동 | 라벨 "(= CTD DV01 / CF)" 또는 입력 통일 | 라벨 문자열 테스트 | 미반영(범위 밖) |
| BS-33 | M-3(D) P3 | functional_completeness.md:146의 FC-03 제안 "Bonds 헤지에 KTB 선물 연결" | 현재 식은 CF가 필수. KTB 선물은 현금결제이고 CF가 없음(일반 지식, KRX 사양 미대조) | 그대로 구현하면 계약 수가 틀림. 현재 코드에는 영향 없음 | 제안에 단서 추가 | KTB 경로 구현 시 | 미반영(문서) |
| BS-34 | E-04 P3 | 칩 `curve: FRED 2026-10-23`은 합집합의 최신 관측일, `curve: SYNTHETIC 2026-10-27`은 오늘(숫자는 매일 같음). "bootstrap, 504 sessions" 칩도 있음 | 칩 문자열. 합성 날짜는 `data.py:_business_dates:288-295`가 오늘부터 거꾸로 만들고, 값은 고정 seed(`:366`) | 날짜를 다운로드일이나 평가일로 오해 | "curve FRED, newest obs …", "SYNTHETIC (simulated, dated …)" | test_synthetic_and_fred_are_labelled_apart_with_a_mocked_fetch | 반영(수신 시각 제외) |
| BS-35 | E-05 P3 | 합성 Run에서 카드, 차트 제목, 시나리오 표, Worst/Best에 출처가 없고 배너만 있음 | 출처 표시를 배너 하나에 의존 | 잘라낸 차트나 표가 시장 결과처럼 보임 | 해설·칩·차트 제목에 출처 | test_synthetic_and_fred_…(칩, 해설) | 부분(차트 제목 미반영) |
| BS-36 | E-06 P3, F-M1 P3 | payload curve는 source/date/method/note뿐. 날짜는 같고 값만 다른 두 FRED 응답이 같은 칩·payload인데 z는 40.24bp 대 10.60bp | 메타데이터만 기록 | 화면 숫자를 나중에 재현할 수 없음(2.3이 미확인인 원인) | payload에 par_yields, zeros, fetched_at, snapshot_id | test_synthetic_and_fred_… | 부분(par_yields만) |
| BS-37 | E-07 P3, G-10 P3 | auto에서 FRED가 실패하면 배너가 같은 사유를 11번 반복(최대 4,961자). 프록시 host:port가 payload note에 들어간 경우가 있었음 | errors.items()를 그대로 이어 붙임 | 가독성. 환경 정보가 외부 AI 요청에 실릴 수 있음(키는 없음) | 사유별로 묶고 400자로 자름 | test_failed_fred_reasons_keep_the_cause_once | 반영(주소 제거 없음) |
| BS-38 | F-08 P3 | 4스레드 × 15회 동시 렌더에서 예외 0, PNG 차이 0 | 작업 스레드에서 pyplot 사용 | 재현되지 않음. 드물게 그림이 섞일 가능성(미확인) | matplotlib.figure.Figure 객체 API 또는 lock | F의 T5 스트레스 테스트 | 미반영 |
| BS-39 | G-09 P3 | "Semi-annu", "Auto (FRED, else synth"가 잘림. 타일에 단위 없음. Dropdown semantics 이름 없음 | 고정 폭, 접근성 라벨 없음 | 가독성 | 폭 조정, 라벨·tooltip | 헤더 문자열 테스트 | 부분(헤더 단위만) |
| BS-40 | G-11 P3 | 웹 모드 시작 시 TypeError 'openapi_prefix'(fastapi 0.162.0) | fastapi 버전 미고정 | 웹 QA·배포 실패. 데스크톱은 영향 없음 | 호환 fastapi 고정 또는 데스크톱 전용 명시 | 새 인터프리터에서 FastAPI() 생성 스모크 | 미반영 |
| BS-41 | G-V02 P3 | 기본 입력·합성 곡선: Breakeven −17.8bp인데 툴팁은 "Yield rise that wipes out carry + roll", 해설은 "yields must fall 17.8bp" | 툴팁이 고정 문자열 | 같은 숫자를 반대 뜻으로 설명 | 부호에 따라 툴팁을 바꿈 | G 검증 v_m2_test | 반영 |

---

## ③ 재현 단계

### 3.1 환경

- 컨테이너: Linux, Python 3.13.17, flet 0.85.2, matplotlib 3.11.2(Agg), numpy 2.3.5, scipy 1.18.0, pandas_datareader 0.11.1.
- 사본 만들기: `git -C /home/user/quantgen archive HEAD | tar -x -C <dir>`. 캐시 CSV 4개는 열지 않고 지웁니다.
- 네트워크 격리:
  - `HTTPS_PROXY`와 `HTTP_PROXY`를 `http://127.0.0.1:9`(닫힌 포트)로 둡니다.
  - `NEXTGEN_FICC_CACHE`는 스크래치 폴더, `MPLBACKEND`는 Agg로 둡니다.
  - FRED 경로는 `core.ficc.data._fred_fetch` stub이나 로컬 프록시(blackhole, 403)로만 시험했습니다.
- 화면 구동 방식은 두 가지입니다.
  1. stand-in Page: `ui/bonds_page.py` self-check와 같은 방식입니다. 동기 실행과 실제 스레드 실행을 모두 썼습니다.
  2. 실제 브라우저(G): Flet 웹 모드와 Chromium(Playwright)을 썼고, semantics 트리로 클릭했습니다. 웹 모드를 띄우려고 런처 안에서만 fastapi 인자 shim을 넣었습니다(BS-40). 앱 코드는 바꾸지 않았습니다.
- 데스크톱 창은 띄우지 않았습니다(NOT_RUN).

### 3.2 이 보고서의 재실행 명령

`F` = `W/final_report`입니다. `F/head`는 HEAD 사본이고, `F/patched`는 HEAD에 `W/patch/bonds_screen.diff`를 적용한 사본입니다.

```bash
ENV="env -u NO_PROXY HTTPS_PROXY=http://127.0.0.1:9 HTTP_PROXY=http://127.0.0.1:9 MPLBACKEND=Agg"
cd F/head    && $ENV NEXTGEN_FICC_CACHE=F/cache_head python3 -B ../scripts/spot.py "$PWD"    # 표 2.1, 헤지, 시나리오, 짧은 만기
cd F/head    && $ENV NEXTGEN_FICC_CACHE=F/cache_head python3 -B ../scripts/stale.py "$PWD"   # 1.3의 낡은 결과 화면
cd F/patched && $ENV NEXTGEN_FICC_CACHE=F/cache_patched python3 -B ../scripts/stale_handler.py "$PWD"
python3 -B W/patch/scripts/run_module_tests.py F/patched tests.bonds_screen_acceptance F/logs/patched_bonds.json
python3 -B W/patch/scripts/run_module_tests.py F/head tests.bonds_screen_acceptance F/patched/tests/bonds_screen_acceptance.py F/logs/head_bonds_xrun.json
python3 -B W/patch/scripts/run_module_tests.py <copy> tests.ficc_acceptance <out.json>
python3 -B -m ui.bonds_page    # core.ficc.bonds / curves / data / insights 도 같은 방식, 각 사본 안에서
# 경계 입력 재확인(같은 네트워크 격리)
python3 -B W/critic/drive_edges.py F/head ; python3 -B W/critic/drive_edges.py F/patched
python3 -B W/corrections_r1/drive_hedge.py F/head ; python3 -B W/corrections_r1/drive_hedge.py F/patched
python3 -I W/corrections_r1/recheck.py   # 볼록성 예측, 0.24% 기준, 599~712, 헤지 두 경로, 평탄 곡선 정확값
```

차원별 재현 스크립트(모두 `W/<차원>/` 아래):
- A: a01_num_contract.py, a02_page_drive.py, a03_lead_independent.py, a04_threads.py, a05_extremes.py, a07_regression_tests.py
- B: indep.py, t1_table21.py, t2_edges.py, t3_fractional.py, t4_curve_risk.py, t5_ui_drive.py, t7_regression.py
- C: indep.py, c1_reproduce.py ~ c10_before_after.py
- D: indep_hedge.py, ui_drive_hedge.py, ui_regression.py
- E: scripts/e01_page_paths.py ~ e09_owner_screen_source.py
- F: f1_perf.py ~ f9_numbers.py, proposed_test_bonds_ui_state.py
- G: launch_bonds_web.py, server.sh, drive_bonds.js(모드 main, blanks, race, race2, fixcheck), verify_screen_numbers.py, test_g_regression.py
- 검증자 스크립트: `W/verify_<차원>/`
- 비평가 재실행: `W/critic/` (indep.py, indep_curve.py, drive_edges.py)

### 3.3 화면 관찰 사실 / 코드로 확인된 사실 / 아직 확인하지 못한 가설

| 화면 관찰 사실 | 코드로 확인된 사실 | 아직 확인하지 못한 가설 |
|---|---|---|
| (2.1) 입력 7개(Coupon %, Maturity, Coupons / year, Price, Yield %, Notional, Curve source)와 결과 카드 11개가 보인다 | (코드로 확인됨) 입력은 ui/bonds_page.py:63-83에 있다. Coupons/year는 1/2/4 Dropdown이다(:31). 카드는 :131-139와 :156-165에 있다. Price 칸은 빈칸, Yield 칸은 "4.50"으로 시작한다 | 없음 |
| (2.1 1행) 5.5%, 10년, YTM 4.5%, "가격 입력 100" → 107.982 / 4.500% / 7.92y / 7.74 / 73.0 / 836 | (테스트로 확인됨) 6개 숫자는 Price를 비운 Yield 모드 결과와 같다(독립 107.981856, 7.918984, 7.744728, 73.014818, 836.290117). Price=100 가격 모드라면 100.000 / 5.500% / 761이다. 둘 다 채운 새 Run은 오류만 남긴다. Run 뒤 Price에 100을 넣으면 같은 화면이 표시 없이 남는다 | H1: Run 뒤에 100을 입력하고 캡처했다. H2: 빈 칸 안의 라벨 "Price (per 100)"을 값으로 읽었다. 둘 다 미확인 |
| (2.1 2행) 4.5%, 10년, YTM 5.5%, "가격 입력 100" → 92.386 / 5.500% / 8.07y / 7.86 / 74.4 / 726 | (테스트로 확인됨) 1행과 같다. Yield 모드 독립 92.386374 / 725.786. 가격 모드라면 100.000 / 4.500% / 798이다 | 1행과 같음 |
| (2.1 3행) 5.5%, 10년, YTM 5.5% → 100.000 / 5.500% / 7.82y / 7.61 / 71.2 / 761 | (테스트로 확인됨) 두 모드의 결과가 같다. 독립값 100.000000000000, 저장소와의 차이 1.1e-12 | 어느 모드였는지 미확인(결과에는 영향 없음) |
| (2.1 4행) Price 95 → 6.178% / 7.76y / 7.52 / 69.9 / 715 | (테스트로 확인됨) Newton 6.1776904062%. 세 독립 해법과의 차이는 8.5e-16 이하 | 없음 |
| (2.1 5행) Price 105 → 4.863% / 7.88y / 7.70 / 72.3 / 808 | (테스트로 확인됨) 4.8626816895%. 위험 지표 차이는 9.1e-13 | 없음 |
| (2.2) Price 100 + Yield 4.5, 또는 Price 105 + Yield 4.5에서 "Give exactly one of price or ytm." | (코드로 확인됨) core/ficc/bonds.py:analyze_bond:236-237에서 price와 ytm이 둘 다 None이거나 둘 다 값이면 ValueError. (테스트로 확인됨) 재현됐고, 이전 결과는 지워진다(ui/bonds_page.py:96) | 없음 |
| (2.2 질문) 두 칸을 어떻게 비워야 하는지 UI가 안내하는가 | (테스트로 확인됨) Yield는 4.50으로 미리 채워져 있다. 빈 화면 안내 "(leave the other blank)"는 첫 Run 뒤 사라진다. hint는 웹 렌더에서 포커스가 있을 때만 보였다. 필드 오류는 0건이다. 둘 다 채운 경우와 둘 다 빈 경우가 같은 문구다 | 데스크톱 창의 hint 표시 방식은 미확인 |
| (2.2 질문) 빈 값과 0을 구분하는가. NaN/Inf·음수는 어떻게 되는가 | (테스트로 확인됨) `_num`은 빈 문자열·공백만 있는 칸·None을 "없음"으로 본다. '0'은 0이다. Yield 0이면 쿠폰 4.5%에서 145.000(독립 145), 5.5%에서 155.000이다. Price 0은 "price must be positive, got 0.0."이다. '-0'은 '-0.000%'로 보인다(BS-19). 'nan', 'inf', '-inf', '1e400'은 `ui/bonds_page.py:_num:47-48`에서 필드 라벨과 함께 거부한다(예: "Yield %: 'nan' is not a number."; Price·Coupon의 'nan'도 같다). Yield 칸이 공백뿐이고 Price가 비면 빈칸으로 처리되어 "Give exactly one of price or ytm."이 나온다. 음수: Coupon −1은 "coupon must be a finite non-negative decimal, got -0.01."(BS-04), Notional −5는 "face and notional must be positive.", 음수 Yield는 유효 입력이고 −45%에서 z-spread 구간 오류가 난다(BS-07). 근거: A_input_contract.md:17, :89-91, `W/critic/drive_edges_head.log` | 없음 |
| (3.B 질문) 만기 0/음수, 매우 작은 가격 | (테스트로 확인됨) Maturity 0 → "maturity must be positive years, got 0.0.", −1 → "… got -1.0."(코어의 명확한 오류, `core/ficc/bonds.py:Bond.__post_init__:51-52`). Price 0.01 → "No yield in [-0.5, 2.0] reproduces price 0.0100.", Price 1 → "… 1.0000."(`bonds.py:yield_from_price:97-98`). 둘 다 필드 라벨이 없고 구간이 소수 단위다. 패치 사본: 만기는 "Maturity (years): must be > 0 and <= 100, got 0."로 바뀌고, 작은 가격 문구는 그대로다(`W/critic/drive_edges_head.log`, `drive_edges_patched.log`) | 없음 |
| (2.2 질문) 오류 뒤에 이전 결과가 남는가 | (테스트로 확인됨) 오류가 난 Run은 이전 결과를 지운다. 그러나 입력만 바꾸고 Run하지 않으면 이전 결과가 표시 없이 남는다(BS-02). 동시 Run에서는 늦은 이전 Run의 오류가 새 결과를 지운다(BS-01) | 없음 |
| (2.3) 5.5%/4.5%: 기준 107.982, +100bp −81,597, −100bp +89,400 | (테스트로 확인됨) 기준가는 곡선과 무관하고 독립값과 같다. P&L은 곡선에 달려 있다. 코드는 연속복리 zero 이동, z 고정이다. HEAD 합성 곡선은 −82,220 / +90,112로 다르다. 평탄 곡선 −81,724 / +89,546, 수익률 ±100bp −79,819 / +87,710이다. 가상 우상향 곡선은 −81,596.5 / +89,400.0이다 | 소유자가 실행한 곡선(날짜·출처)은 미확인. 소유자 PC의 코드 버전도 미확인 |
| (2.3) 5.5%/5.5%: 기준 100.000, +100bp −74,657, −100bp +81,766, +25bp −19,305, −25bp +19,748, bear steepener −9,888, bull steepener +27,819, bear flattener −26,977 | (테스트로 확인됨) 합성 곡선은 −75,256 / +82,450 / −19,462 / +19,911 / −10,015 / +28,004 / −27,153으로 다르다(차이 −599 ~ +684). 곡선 모양 400개 범위 안이다(B +100bp [−75,331, −74,175]). 수익률 이동값 −72,697은 범위 밖이다. 가상 곡선이 9개 중 8개 문자열을 재현한다(+25bp는 −19,304.5라 "−19,304") | 실제 FRED였는지 미확인. 상승형 곡선에 가깝다는 것은 정황일 뿐이다 |
| (2.3) 금리 상승 시 손실, 하락 시 이익, 비대칭 | (테스트로 확인됨) 모든 곡선에서 성립한다. 비대칭 A 7,803, B 7,109는 평탄 곡선 실제값(4차) 7,821.6 / 7,126.3보다 0.24%(A −0.238%, B −0.243%), 2차 예측 7,815.5 / 7,120.8보다 0.16~0.17%(A −0.160%, B −0.166%) 작다 | 없음 |
| (2.4) Position 798, CTD 65, CF 0.8 → Futures DV01 81.25, 9.82, Rounded 10, 문구 "798 × 0.8000 / 65.00 = 9.82" | (테스트로 확인됨) 두 입력 경로가 같은 화면을 만든다. 칸을 비운 경우: 계산기 기본 채권(4.5%, 10년, 반기, 수익률 4.5%, 명목 1,000,000)의 수익률 DV01 798.185618 → n 9.823823, 잔여 −14.3144. 798을 입력한 경우: n 9.821538, 잔여 −14.50. HEAD는 `_money`가 0자리라 두 경우 모두 'Position DV01 798', '9.82', 'Rounded 10', '−14'를 보인다(`W/critic/indep.log`, `W/patch/logs2/compare_ba.txt` 'position 798 typed' 행). 요청서의 9.815는 오기다. 두 경우 모두 잔여 음수는 과헤지다 | 소유자가 Position DV01 칸을 비웠는지 798을 입력했는지는 미확인 |
| (2.4 질문) 계약 DV01 정의, CTD·CF, 부호, 잔여, 계약 명목, 인도 옵션 | (코드로 확인됨) 식은 core/ficc/bonds.py:323-329, 문구는 롱 전제(ui/bonds_page.py:199-209). (테스트로 확인됨) 숏이면 "Contracts to sell −9.82"가 나온다. CTD 0·−1, CF 0·−0.8은 칸을 지목하지 않는 공통 문구로 거부된다(BS-05 표). CTD 변경·basis·인도 옵션·invoice price는 반영하지 않고, 고지도 없다 | CME 계약 액면($100,000, ZT는 $200,000)은 검색 결과로만 봤다(원문 사양 미대조). 65와 0.8의 시장 근거는 미확인 |

### 3.4 실제 UI 구동 결과 (G, 브라우저)

조건: HEAD 코드, Flet 웹 모드, Chromium. FRED·yfinance 호출 함수는 런처에서 막았습니다. 캐시 TTL은 0이고, `ANTHROPIC_API_KEY`는 빈 값입니다. 스크린샷은 모두 `docs/audit/2026-10-27/bonds_screen/shots/` 아래에 있습니다.

| 단계 | 조작 | 화면 결과 | 스크린샷 |
|---|---|---|---|
| 0 | 로드, Curve source → Synthetic demo | 빈 화면 안내 "Quote it by price or by yield (leave the other blank)" | S0_initial.png, S0b_synthetic_selected.png |
| 1 | 4.50%, 10년, 반기, Yield 4.50, Run | 빨간 "Synthetic data" 배너, 칩 `curve: SYNTHETIC 2026-10-27`. 100.000 / 4.500% / 8.16y / 7.98 / 76.2 / 798, z −315.9bp, Carry −1.239, Roll −0.180, 합 −1.419, BE −17.8bp | S1_default_calc.png |
| 1b | 5.50%, Yield 4.50 | 107.982 / 4.500% / 7.92y / 7.74 / 73.0 / 836. 소유자 1행과 같다 | S1b_c550_y450.png |
| 2 | Price 100 + Yield 4.50, Run | "Give exactly one of price or ytm."만 남는다. 이전 결과와 차트는 지워진다 | S2_price100_and_yield450.png, crop_S2_price100_and_yield450.png |
| 2b | 두 칸 모두 빈칸 | 같은 문구 | S2b_both_blank.png, crop_S2b_both_blank.png |
| 2c | Yield 0 | 유효하다. 155.000, Mod 8.31 | S2c_yield_zero.png |
| 2d | Price 0 | "price must be positive, got 0.0." | S2d_price_zero.png |
| 3 | 5.50%로 Run한 뒤 Yield를 지우고 Price 95 입력, Run하지 않음 | 107.982 / 4.500% 그대로. 표시 없음 | S3a_good_run.png, S3b_typed_price95_no_run.png, crop_S3b_typed_price95_no_run.png |
| 3c, 3d | Price 95 / 105로 Run | 6.178%(7.76y, 7.52, 69.9, 715) / 4.863%(7.88y, 7.70, 72.3, 808). 소유자 화면과 같다 | S3c_price95_run.png, S3d_price105_run.png |
| 4a | Tool → Scenarios, Run하지 않음 | Calculator 결과가 그대로 남는다 | S4a_tool_scenarios_no_run.png |
| 4b | Scenarios, 5.50%/4.50 | 107.982. +100 −82,220(−7.61%), −100 +90,112, +25 −21,266, −25 +21,759, bear steep −10,997, bull steep +30,550, bear flat −29,619, bull flat +11,146, fly +8,033 | S4b_scenarios_c550_y450.png |
| 4c | Scenarios, 5.50%/5.50 | 100.000. +100 −75,256, −100 +82,450, +25 −19,462, −25 +19,911, bear steep −10,015, bull steep +28,004, bear flat −27,153 | S4c_scenarios_c550_y550.png |
| 5a | Tool → Futures hedge, Run하지 않음 | 헤지 입력줄이 나타나고, 그 아래에 시나리오 결과가 그대로 남는다 | S5a_tool_hedge_no_run.png, crop_S5a_tool_hedge_no_run.png |
| 5b | hedge, 5.50%/5.50 | Pos 761, 81.25, 9.37, Rounded 9, 잔여 +30/bp | S5b_hedge_run_c550_y550.png |
| 5c | hedge, 4.50%/4.50(소유자 경우), Position DV01 칸 빈칸 | 798, 81.25, 9.82, Rounded 10, 잔여 −14/bp. 소유자 화면과 같다. 798을 입력해도 같은 화면이다(3.3, 4.5) | S5c_hedge_owner_case.png |
| 5d | Position DV01 −798 | "Contracts to sell −9.82", "Rounded −10", "flatten a long position … +14 per bp" | S5d_hedge_short_position.png, crop_S5d_hedge_short_position.png |
| 5e | CTD 0 | "CTD DV01 per contract and conversion factor must be positive." | S5e_hedge_ctd_zero.png |
| 5f | CF 빈칸 | CF 1.0000, 12.28계약 | S5f_hedge_cf_blank.png |
| 6 | Tool → Calculator, Run하지 않음 | 헤지 입력은 숨겨지고 헤지 결과(CF 1.0000)는 남는다. 숨은 CF 칸은 0.8 | S6_back_to_calc_no_run.png, crop_S6_back_to_calc_no_run.png |
| 경합 | Auto(FRED 호출당 1초)로 Run #1, Synthetic·Coupon 6.00으로 Run #2 | +4.07초에 Run #2의 111.973이 뜨고 링이 꺼진다. +12.31초에 Run #1이 100.000과 "FRED failed" 배너로 덮는다 | Q0_initial.png, Q1_run2_shown_run1_pending.png, Q2_run1_overwrites_run2.png, crop_Q1_run2_shown_run1_pending.png, crop_Q2_run1_overwrites_run2.png |
| B1 ~ B3 | Coupon / Maturity / Notional 빈칸 | 0% 쿠폰 64.082 / 10년 / 1,000,000 | B1_coupon_blank.png, B2_maturity_blank.png, B3_notional_blank.png |
| B4 | Yield '4,5'(Coupon 4.50) | 45.000%, z +3251.5bp | B4_yield_comma_decimal.png |
| B5 | Maturity 0.1 | "Carry (3m)" −0.520, BE −2325.9bp | B5_maturity_short.png |
| E1 | Auto, FRED 차단(즉시 실패) | "Synthetic data: FRED failed: FRED served 0/11 tenors (…11번 반복…)" | E1_auto_fred_blocked_fastfail.png, crop_E1_auto_fred_blocked_fastfail.png |
| 확대 | 차트 제목, 입력줄, 타일 | 검정 제목(대비 약 1.2:1), 라벨 잘림, 단위 없는 타일 | zoom_chart_title.png, zoom_inputs_row.png, zoom_stats.png |
| G 수정본 | G가 만든 수정본(최종 패치가 아님)에서 Coupon 수정, 경합, 차트 제목 확인 | 수정 후 배너가 뜨고, 재실행하면 사라진다. 경합에서 Run #2(111.973)가 유지된다. 제목이 보인다 | F0_fix_calc_run.png, F1_fix_edit_no_run.png, crop_F1_fix_edit_no_run.png, F2_fix_rerun.png, F3_fix_tool_switch_no_run.png, FIX_Q0_initial.png, FIX_Q1_run2_shown_run1_pending.png, FIX_Q2_run1_overwrites_run2.png, zoom_FIX_chart_title.png |

- 같은 입력을 세 번 실행했습니다(5.50%/4.50, 단계 S1b, S3a, S4b). 107.982 / 836 / −317.8bp로 모두 같습니다.
- 화면 숫자 171개를 독립 공식으로 다시 계산했습니다. 불일치는 0개입니다(`W/G_real_ui/verify_screen_numbers.log`). 곡선 zero 노드는 저장소 부트스트랩 값을 입력으로 썼습니다.
- 클릭부터 결과까지(웹, 합성 곡선): calc 0.32~0.47초, scenarios 0.34~0.46초, hedge 0.05~0.20초, 오류 0.03~0.08초.
- T_R0 ~ T_R3 스크린샷은 초기 경합 시도입니다. 근거로 쓰지 않았습니다.
- 브라우저에서 시험하지 않은 헤지 입력(CTD −1, CF 0·−0.8·'abc', CTD 빈칸)은 stand-in 페이지로 시험했습니다(BS-05 표).
- 최종 패치는 실제 브라우저로 다시 구동하지 않았습니다(NOT_RUN). stand-in 페이지로만 확인했습니다.

### 3.5 요청서 3.A~3.F 항목별 판정

요청서 3절의 bullet은 34개입니다(A 5, B 6, C 7, D 6, E 5, F 5). 판정은 HEAD 기준입니다.

| 항목 | 요청 내용(요약) | 판정 | 근거 |
|---|---|---|---|
| A1 | Price와 YTM 중 정확히 하나 조건 | 코드로 확인됨 | `core/ficc/bonds.py:analyze_bond:236-237`. 화면 재현도 됨(3.4 단계 2, 2b) |
| A2 | 빈 문자열·공백·None·0·음수·NaN/Inf 처리 | 테스트로 확인됨 | 3.3 '(2.2 질문) 빈 값과 0' 행. `_num:38-49`, A_input_contract.md:89-91, `W/critic/drive_edges_head.log` |
| A3 | 모드 선택 또는 자동 비우기 UX 제안 | 제안함(판정 대상 아님) | BS-04 최소 수정. 두 칸 field error와 늘 보이는 안내는 패치에 반영(stand-in 테스트). "Quote by" 모드 선택기는 미반영(소유자 결정) |
| A4 | 검증 실패 뒤 이전 결과 잔존 방지, 필드별 오류 | 테스트로 확인됨 | HEAD: 오류 Run은 결과를 지움(`:96`). 입력만 바꾸면 남음(BS-02). 동시 Run에서 덮음(BS-01). 필드 오류 0곳(BS-04). 숨은 수동값(BS-03) |
| A5 | 도구 전환 시 상태 공유·잔존 | 테스트로 확인됨 | BS-02(3.4 단계 4a, 5a, 6), BS-03 |
| B1 | 반기 가격 공식, 복리 주기, 쿠폰율 변환 | 테스트로 확인됨 | 4.2, 4.3(Decimal 60자리 독립 구현, 640건 그리드) |
| B2 | Mac/Mod/Cvx/DV01 정의·단위·스케일 | 테스트로 확인됨 | 4.2, 4.3. 단위는 4.2에 명시. HEAD 화면에는 단위 없음(BS-22) |
| B3 | par / premium / discount 관계 | 테스트로 확인됨 | 정수 기간 200건 위반 0(4.3) |
| B4 | 95·105 역산과 독립 해법 대조 | 테스트로 확인됨 | Newton·이분법·numpy.roots, 차이 8.5e-16 이하(4.3). QuantLib은 NOT_RUN |
| B5 | 만기 0/음수, 쿠폰 0, 빈도 1/2/4/12, 극단 수익률, 작은 가격 | 테스트로 확인됨 | 만기 0/−1과 작은 가격(3.3 '(3.B 질문)' 행). 쿠폰 0(BS-05, 64.082). 빈도 1/2/4/12(4.3 640건, 12는 코어에서만 가능, UI는 1/2/4). 극단 수익률(BS-07) |
| B6 | 날짜·정산일·경과이자·day-count 한계 명시 | 코드로 확인됨 + 테스트로 확인됨. HEAD에 고지 없음 | 단순화는 `bonds.py:15-18` docstring에만 있음. 화면 문자열 스캔에서 dirty·settle·ACT·365·compound가 0회(B-06 검증, `W/verify_B_pricing_risk/v11_b06_textscan.log`). 오차 크기는 4.8. 패치는 Conventions notice(BS-22 부분 반영) |
| C1 | 곡선 평행·비틀기 재구성 수식과 코드 위치 | 코드로 확인됨 | 4.1(scenario_pnl → shocked_curve → shifted, _ramp, SCENARIO_SHOCKS), 4.4 key tenor 표. 부분 곡선 동작은 테스트로 확인됨(BS-10) |
| C2 | 'z-spread held' 반영과 적용 순서 | 코드로 확인됨 | `bonds.py:313`에서 원래 곡선·가격으로 z를 한 번 구하고 충격 곡선에 고정(4.4). 수준 불변(평탄 3.0/4.45/5.43% 곡선이 같은 P&L)은 테스트로 확인됨 |
| C3 | 기준·시나리오 가격 출력, P&L = (new − base) × N / 100 | 테스트로 확인됨 | 4.4 중간값 로그(C의 c1, c5). 저장소 대 독립 3.7e-9원 이하 |
| C4 | 4.5%·5.5% 화면 ±25/±100 독립 재현 | 독립 대 저장소는 테스트로 확인됨. 소유자 화면 숫자는 미확인 | 4.4 표. 그날 곡선 스냅샷 없음. 가상 곡선 8/9 일치는 정황 |
| C5 | 상승 손실·하락 이익, 볼록성 비대칭 | 테스트로 확인됨 | 4.4 비대칭 항목(평탄 실제값 대비 0.24%, 2차 예측 대비 0.16~0.17%) |
| C6 | 시나리오 이름과 부호의 통상 정의 | 코드로 확인됨 | 4.4 key tenor 이동, `curves._regime:313-322`. fly 표시는 BS-11 |
| C7 | P&L % 분모 | 테스트로 확인됨 | 시장가치 기준 −7.61%, 명목이면 −8.22%. HEAD 미표기(BS-24) |
| D1 | 계약 수 공식의 적용 조건, 계약 DV01·CF 정의 | 코드로 확인됨 | `bonds.py:323-329`, 4.5 조건 목록. HEAD에 문서 없음(BS-13) |
| D2 | 롱/숏에 따른 매수/매도 방향 | 테스트로 확인됨 | BS-12(숏에 "sell −9.82") |
| D3 | 반올림 뒤 잔여 DV01과 화면 설명 | 테스트로 확인됨 | 4.5, BS-27, BS-28 |
| D4 | Position DV01 공란 시 기준 | 테스트로 확인됨 | 4.5(계산기 채권의 수익률 DV01, 곡선 무관), BS-03 |
| D5 | CTD·CF 0/음수, 공란·문자 방어 | 테스트로 확인됨 | BS-05의 헤지 입력 표(HEAD는 0·음수를 공통 문구로 거부, 공란은 조용히 기본값) |
| D6 | 단순 DV01 근사라는 명시 | 코드로 확인됨. HEAD에 고지 없음 | D-03, BS-13 |
| E1 | Auto에서 FRED와 synthetic 구분 표시 | stub·로컬 프록시로 테스트로 확인됨. 실제 FRED는 미확인(NOT_RUN) | 4.6 출처별 표시, 3.4 E1, BS-34 |
| E2 | 실패·빈 데이터·오래된 데이터 처리 | 테스트로 확인됨 | 4.6(실패·빈 데이터 → 배너와 SYNTHETIC). 오래된 FRED는 녹색(BS-14). 날짜 섞임(BS-15). 이상값(BS-16) |
| E3 | as-of 날짜의 뜻 | 테스트로 확인됨 | BS-34(FRED = 합집합의 최신 관측일, SYNTHETIC = 오늘, 값은 고정) |
| E4 | 만기별 값·보간·단위·DF 기록과 fail-safe | 테스트로 확인됨 | 4.6(퍼센트 ÷ 100, ln DF 선형, 부트스트랩 대조). 검사 없음(BS-16). 값 미기록(BS-36) |
| E5 | synthetic 곡선 시나리오의 출처 고지 | 테스트로 확인됨 | 배너만 있고 결과 블록에 출처 없음(BS-35) |
| F1 | Run당 시간, 데이터·계산 분리 | 테스트로 확인됨. 실제 FRED 시간은 NOT_RUN | 5.5 |
| F2 | 같은 입력·스냅샷 재실행 재현 | 테스트로 확인됨 | 3.4(같은 입력 세 번 107.982 / 836 / −317.8bp). 곡선 스냅샷을 기록하지 않아 과거 화면은 재현 불가(BS-36) |
| F3 | 캐싱과 중복 호출 | 테스트로 확인됨 | 4.6 캐시(차가운 캐시 1회, 이후 0회). 실패 시 Run마다 12회(BS-17) |
| F4 | 카드·차트·해설의 입력·결과 일관성 | 테스트로 확인됨 | F 일관성 410/410(6.3), G 화면 숫자 171/171. 예외: 동시 Run(BS-01), 해설과 표의 '+100bp' 정의 차이(BS-09), 보이지 않는 차트 제목(BS-18) |
| F5 | Run 전 결과가 이전 값임을 구분 | 테스트로 확인됨 | HEAD는 구분 불가(BS-02, `F/logs/stale_head.log`). 패치는 배너(`stale_patched.log`) |

---

## ④ 수식 및 독립 계산

### 4.1 코드 추적표 (UI 컨트롤 → 핸들러 → 코어 함수)

| UI 컨트롤 | 핸들러 | 코어 함수 | file:function:line |
|---|---|---|---|
| 입력 파싱(모든 TextField) | Run 때 worker가 읽음 | `_num` | ui/bonds_page.py:_num:38-49 |
| Coupon %, Maturity, Coupons / year, Notional | 변경 핸들러 없음. Run 때 worker가 읽음 | `Bond` | ui/bonds_page.py:build_bonds_page:63-74 → worker:107-108 → core/ficc/bonds.py:Bond:40-57 |
| Price (per 100), Yield % | Run 때 worker가 읽음(:109 곡선 로드 전, :112 로드 후) | `analyze_bond` (계약 검사 236-237) | ui/bonds_page.py:69-72 → worker:109, 112 → core/ficc/bonds.py:analyze_bond:231-254 |
| Curve source | Run 때 worker가 읽음 | `load_treasury_curve` → `_treasury_from_fred` → `_provider_rows` → `_fred_fetch` 또는 `synthetic_curve_panel` → `CurvePanel.latest` → `curve_from_snapshot` → `bootstrap_par_curve` → `YieldCurve._log_df` | ui/bonds_page.py:75-76 → worker:110-111 → core/ficc/data.py:load_treasury_curve:552-568, _treasury_from_fred:571-596, _provider_rows:449-495, _fred_fetch:163-192, synthetic_curve_panel:361-377, CurvePanel.latest:142-143 → core/ficc/curves.py:curve_from_snapshot:262-267, bootstrap_par_curve:165-201, YieldCurve._log_df:77-85 |
| Tool | `on_tool` | 없음(결과 영역을 건드리지 않음) | ui/bonds_page.py:on_tool:87-89, :91 |
| Run 버튼 | `run` → `page.run_thread(worker)` | 없음 | ui/bonds_page.py:run:94-97, :224, :237 |
| Calculator 카드(가격·위험) | worker | `price_from_yield`, `yield_from_price`, `macaulay_duration`, `modified_duration`, `convexity`, `dv01` | core/ficc/bonds.py:87-89, 92-99, 121-123, 126-127, 130-134, 137-141; 표시 ui/bonds_page.py:131-139 |
| z-spread, KRD, Carry/Roll/Breakeven 카드 | worker | `z_spread`, `key_rate_dv01`(`YieldCurve.key_rate_shifted`), `carry_roll` | core/ficc/bonds.py:108-115, 144-157, 169-208; 표시 ui/bonds_page.py:156-165 |
| 가격-수익률 차트, KRD 차트 | worker | `fcharts.price_yield_chart`, `fcharts.krd_chart`, `qcharts._style` | ui/fcharts.py:168-187, 133-145; ui/qcharts.py:_style:36-45; 호출 ui/bonds_page.py:166-168 |
| Scenarios 표·차트·Worst/Best | worker | `scenario_pnl` → `shocked_curve` → `YieldCurve.shifted`, `_ramp`, `SCENARIO_SHOCKS`; `fcharts.scenario_chart` | core/ficc/bonds.py:299-320, 288-296, 269-271, 274-284; core/ficc/curves.py:shifted:119-123; ui/fcharts.py:148-165; ui/bonds_page.py:114, 170-190, _shock_text:52-56 |
| Futures hedge 카드·notice | worker | `futures_hedge_ratio` | ui/bonds_page.py:117-118, 191-211 → core/ficc/bonds.py:323-329 |
| Analysis 해설, AI payload | worker | `insights.narrate_bond`, `ai_panel.analysis_panel` | core/ficc/insights.py:narrate_bond:105-139; ui/ai_panel.py:analysis_panel:26; ui/bonds_page.py:140-154, 214-215 |
| 배너·칩·타일 | worker | `notice`, `chip`, `stat` | ui/components.py:notice:67, chip:30, stat:121; ui/bonds_page.py:120-130 |
| 오류 표시 | `fail` | 없음 | ui/bonds_page.py:fail:99-102, 219-222 |

### 4.2 공식 비교표

예시 입력은 쿠폰 5.5%, 10년, 반기, 수익률 4.5%, 명목 1,000,000입니다. 다른 입력을 쓴 행은 따로 적었습니다. "독립 계산"은 저장소를 import하지 않는 구현입니다(B는 Decimal 60자리, C는 순수 float, 이 보고서의 spot.py는 순수 math).

| 항목 | 공식 | 단위 | 복리·할인 관례 | 가정 | 독립 계산 | 화면/코드 값 | 차이 |
|---|---|---|---|---|---|---|---|
| 가격 | P = Σ cf_k · (1 + y/f)^(−f·t_k), t_k = T − k/f, 쿠폰 100c/f, 만기에 +100 | 액면 100당 | f회 복리 이산 할인, 분수 지수 | 정산일·경과이자 없음, 즉 full PV(dirty). t는 만기에서 거꾸로 센 ACT/365F 연 | 107.981856184988 | 107.982 / 107.981856 | 3.4e-13 |
| YTM 역산(P 95) | P(y) = 95의 근 | 연율 소수 | f회 복리 | 구간 [−50%, 200%] | Newton 6.1776904062% | 6.178% / brentq | 3.5e-16 |
| Macaulay | Σ t·PV / P | 년 | 같은 할인 | 같음 | 7.918984491792 | 7.92y | 1e-12 미만 |
| Modified | Mac / (1 + y/f) | 년(수익률 1.00당 가격 변화율) | 이산 수익률 기준 | 같음 | 7.744728109332 | 7.74 | 1e-12 미만 |
| Convexity | Σ t(t + 1/f)·PV / ((1 + y/f)²·P) | 년² (P''/P, 100으로 나누는 관례 아님) | 같음 | 같음 | 73.0148182566 | 73.0 | 1e-11 미만 |
| DV01 | Mod · P / 100 · N · 1e-4 | 통화/bp, 롱이면 양수 | 1차 해석 미분 | 수익률 이동 | 836.29011689 (±1bp 중심차분 836.290252) | 836 | 해석식 3.4e-13, 중심차분 1.35e-4(3차항) |
| z-spread(합성 곡선) | Σ cf · DF(t) · e^(−s·t) = P | bp, 연속복리 | DF = exp(−z(t)·t), z·t 선형 보간, 양 끝 zero 평탄 | z-spread 하나로 곡선 전체를 평행 이동 | −317.75bp | −317.8bp | 2.4e-15(소수) |
| KRD 합 | 키 tenor 삼각 bump ±1bp, (P↓ − P↑)/2 · N/100 | 통화/bp | zero 연속 이동, z 고정 | 삼각 bump의 합 = 평행 이동 | 해석 미분 합 860.4034 | "total 860 per bp" / 860.4035 | 상대 8e-7(중심차분 오차) |
| Carry (3m) | 100c·h − z(h)·P·h | 100당, 3개월, 연율 아님 | z(h)를 단리처럼 사용(BS-21) | h = min(0.25, T) | −1.177343 | −1.177 | 3.2e-16 이하 |
| Roll-down | [Σ(t > h) cf·DF(t − h)·e^(−s(t − h)) + 받은 쿠폰 − 100c·h] − P | 100당 | 곡선 불변, z 고정 | 만기 > h(만기 ≤ h는 BS-08) | −0.346437 | −0.346 | 1.6e-12 이하 |
| Breakeven | (carry + roll) / (Mod · P) / 1bp | bp | 1차 근사 | 오늘의 Mod | −18.2207bp | −18.2bp | 일치 |
| 시나리오 P&L(5.5%/5.5%, 평탄 곡선) | (P_new − P)·N/100, P_new = Σ cf·DF′(t)·e^(−z·t), z′_k = z_k + Δ_k | 통화 | 연속복리 zero에 bp를 더함, z 고정 | 순간 충격, 단일 곡선. 비평행은 키 tenor 값을 곡선 knot에 선형 보간 | +100bp −74,780.06 | −74,780.1 (저장소, 평탄 곡선) | 6.6e-9 이하 |
| P&L %(합성 곡선, A +100bp) | P_new / P − 1 | 시장가치 대비 | 같음 | 명목 대비 아님 | −82,219.86 / 1,079,818.56 = −7.614% | −7.61% | 일치(명목 대비라면 −8.22%) |
| 헤지 계약 수 | n = posDV01 · CF / CTD DV01 | 계약 | 선물 DV01 = CTD DV01 / CF | yield beta 1, CTD 고정, 작은 변동 | 9.823823 (pos 798.185618, 칸을 비운 경우) / 9.821538 (798 입력) | 9.82 | 상대 3.3e-16 |
| 잔여 DV01 | pos − round(n) · CTD/CF | 통화/bp, 음수 = 과헤지 | 같음 | HEAD는 half-to-even 반올림 | −14.3144 (빈칸) / −14.50 (798 입력) | "−14" | 일치 |
| 부트스트랩 | t < 1: z = ln(1 + y·t)/t. t ≥ 1: (y/2)·Σ DF(t_i) + DF(T) = 1 | 연속복리 zero | 1년 미만 단리, 이상 반기 par | ACT/365F, FRED 퍼센트 ÷ 100 | 동시 Newton | 순차 brentq | zero 2.1e-15, DF 1.4e-14 이하 |

### 4.3 표 2.1 독립 재현

| 입력 | 가격 | YTM | Macaulay | Modified | Convexity | DV01 | 저장소 차이 | 화면 일치 |
|---|---|---|---|---|---|---|---|---|
| 5.5%, 10y, y 4.5% | 107.981856184988 | 4.5% | 7.918984491792 | 7.744728109332 | 73.0148182566 | 836.29011689 | 3.4e-13 | 6/6 |
| 4.5%, 10y, y 5.5% | 92.386373933112 | 5.5% | 8.072030429249 | 7.855990685401 | 74.3897908015 | 725.78649308 | 1.1e-12 | 6/6 |
| 5.5%, 10y, y 5.5% | 100.000000000000 | 5.5% | 7.823000783727 | 7.613626066888 | 71.1522272246 | 761.36260669 | 1.1e-12 | 6/6 |
| 5.5%, 10y, P 95 | 95 | 6.1776904062% | 7.756344948252 | 7.523942025901 | 69.8915699924 | 714.77449246 | 3.2e-12 | 6/6 |
| 5.5%, 10y, P 105 | 105 | 4.8626816895% | 7.884503648622 | 7.697354719364 | 72.3390287514 | 808.22224553 | 9.1e-13 | 6/6 |

- 출처: B 차원(Decimal 60자리, Newton·이분법·numpy.roots)입니다. 같은 값을 F(순수 Python), G(171개 화면 숫자), 각 검증자(Illinois, Newton), 비평가(`W/critic/indep.log`)가 따로 재현했습니다.
- 이 보고서의 재실행(spot.py)에서 유한차분 독립값과 저장소의 차이는 1.35e-4 이하였습니다. 이는 DV01 중심차분의 3차항 크기입니다. 표시 자리수에서는 모두 같습니다.
- 규칙 검사:
  - 정수 기간 200건에서 par/premium/discount 위반은 0건입니다.
  - 빈도 1/2/4/12 × 쿠폰 0~12% × 만기 0.1~30년 × 수익률 −1~60%의 640건에서 상대 차이는 2.9e-14 이하입니다.
  - 무이표채는 닫힌식(Mac = T)과 1.1e-13 안에서 맞습니다.

### 4.4 시나리오

모델: z-spread는 원래 곡선과 원래 가격으로 한 번 구합니다(`bonds.py:313`). 그다음 곡선의 zero를 흔들고, DF′(t)·e^(−z·t)로 할인합니다.
- 평행 이동이면 knot 사이에서도 정확히 DF′(t) = DF(t)·e^(−Δ·t)입니다.
- 곡선의 수준은 z가 흡수합니다. 평탄 3.0%, 4.45%, 5.43% 곡선이 같은 P&L을 냅니다.
- 그래서 P&L은 곡선의 모양(PV 가중치)에만 달려 있습니다.

| 채권 / 시나리오 | 화면(소유자) | 가상 적합 곡선(시장 아님) | 평탄 곡선(자기 수익률) | HEAD 합성 곡선 | 수익률 ±Δ 이동 |
|---|---|---|---|---|---|
| A 5.5%/4.5% 기준가 | 107.982 | 107.982 | 107.982 | 107.982 | 107.982 |
| A +100bp | −81,597 | −81,596.5 | −81,724.3 | −82,219.9 | −79,818.6 |
| A −100bp | +89,400 | +89,400.0 | +89,545.9 | +90,112.3 | +87,710.3 |
| B 5.5%/5.5% 기준가 | 100.000 | 100.000 | 100.000 | 100.000 | 100.000 |
| B +25bp | −19,305 | −19,304.5 | −19,336.7 | −19,461.7 | −18,813.6 |
| B −25bp | +19,748 | +19,748.5 | +19,781.8 | +19,911.0 | +19,258.3 |
| B +100bp | −74,657 | −74,657.2 | −74,780.1 | −75,255.7 | −72,696.7 |
| B −100bp | +81,766 | +81,766.2 | +81,906.3 | +82,449.9 | +79,818.6 |
| B bear steepener | −9,888 | −9,888.1 | −9,913.9 | −10,015.2 | 해당 없음 |
| B bull steepener | +27,819 | +27,819.0 | +27,856.6 | +28,003.6 | 해당 없음 |
| B bear flattener | −26,977 | −26,977.0 | −27,012.8 | −27,153.0 | 해당 없음 |

- 독립 구현과 저장소의 P&L 차이: 합성·평탄·예시·가상 곡선에서 최대 3.7e-9원입니다. 검증자 구현으로는 2.0e-9원입니다.
- 이 보고서의 재실행에서도 평탄 곡선과 합성 곡선의 저장소 값이 위 표와 같았습니다(`F/logs/spot_head.log`).
- 가상 적합 곡선(par %): 1m 4.092, 3m 4.021, 6m 3.948, 1y 3.881, 2y 3.906, 3y 3.992, 5y 4.145, 7y 4.239, 10y 4.317, 20y 4.408, 30y 4.439.
  - 해는 유일하지 않습니다. 화면 숫자가 말해 주는 것은 "0~10년 구간이 완만한 우상향(2s10s 약 +30~+55bp)"이라는 데까지입니다.
  - 이 반올림 값으로 다시 계산하면 문자열 일치는 9개 중 7개입니다. 8/9는 전체 정밀도 값(`W/C_scenarios/c3_fit.json`)으로만 나옵니다.
- 곡선 모양 의존도(NS 모양 400개, 가격 고정):
  - B +100bp: [−75,331, −74,175](폭 1.55%).
  - A +100bp: [−82,298, −81,092].
  - 기울기와의 상관은 +0.837입니다. 곡선이 가파를수록 손실이 작습니다.
  - 화면 값은 범위 안에 있고, 수익률 이동값(−72,697)은 범위 밖에 있습니다.
- zero 이동과 수익률 이동의 비교(평탄 곡선):
  - 1bp 비율: A 1.02251, B 1.02751. 각각 1 + y/f(1.0225, 1.0275)와 같습니다. 이것은 1bp 극한의 1차 기울기입니다.
  - 같은 가격을 만드는 수익률 이동: A +102.506 / −101.995bp, B +103.007 / −102.494bp.
  - 평탄 곡선에서 +Δ zero 이동의 정확한 수익률 변화는 (f + y)(e^{Δ/f} − 1)입니다. Δ = 0.01이면 A +102.506bp, B +103.007bp로 위 값과 같습니다. 1차 근사 100·(1 + y/f)는 A +102.25bp, B +102.75bp입니다(`W/corrections_r1/recheck.log`).
- 볼록성 비대칭(P&L(+100) + P&L(−100)):
  - 화면: A 7,803, B 7,109.
  - 연속 볼록성 C_cont = C·(1 + y/f)² − Mac/f입니다(A 72.378, B 71.208).
  - 2차 예측 = C_cont × Δ² × P × N/100, Δ = 0.01 → 7,815.5 / 7,120.8. 4차까지: 7,821.6 / 7,126.3(= 평탄 곡선 실제값).
  - 화면 값은 평탄 곡선 실제값(4차) 대비 0.24%(A −0.238%, B −0.243%), 2차 예측 대비 0.16~0.17%(A −0.160%, B −0.166%) 작습니다. 차이는 우상향 곡선의 가중치 때문입니다. 가상 곡선에서는 7,803.5와 7,109.0으로 같습니다.
  - 비평가가 다시 계산해 같은 값을 얻었습니다(`W/critic/indep.log`, `W/corrections_r1/recheck.log`).
- 시나리오 이름과 부호(key tenor 이동, bp):
  - bear steepener: 2y 이하 0, 10y +14.29, 30y +50.
  - bull steepener: 3m −50, 10y −33.61, 30y 0.
  - bear flattener: 3m +50, 10y +33.61, 30y 0.
  - bull flattener: 3y −1.79, 10y −14.29, 30y −50.
  - 네 이름 모두 교과서 정의와 앱 분류기 `curves._regime:313-322`에 맞습니다. fly는 BS-11을 보십시오.
- 중간값 로그 예(가상 곡선, B, z = +116.2472bp, +100bp):
  - DF(10y) 0.588759, 여기에 e^(−zt)를 곱하면 0.524146. 새 가격 92.53428, P&L −74,657.2(저장소와 독립 구현이 같음).
  - 손검산: e^(−0.52974) = 0.58876, e^(−0.0116247·10) = 0.89025, 곱 0.52414.
  - 전체 로그: `W/C_scenarios/c5_hyp_log.json`, `W/C_scenarios/c1_reproduce.json`.

### 4.5 선물 헤지

| 항목 | 798 입력 | 칸을 비운 경우(계산기 DV01 798.185618) | 화면 |
|---|---|---|---|
| Position DV01 표시 | "798" | "798" | 798 |
| Futures DV01 = 65 / 0.8 | 81.25 | 81.25 | 81.25 |
| n = pos × CF / CTD | 9.821538 | 9.823823 | 9.82 |
| Rounded | 10 | 10 | 10 |
| 잔여 = pos − 10 × 81.25 | −14.50 | −14.3144 | −14 |
| 9계약일 때 잔여 | +66.75 | +66.94 | 표시 없음 |

- 두 경로 모두 같은 화면을 만듭니다. HEAD는 Position DV01을 0자리로 보이고, −14.50은 half-even 서식으로 "−14"가 됩니다. 소유자가 어느 쪽이었는지는 미확인입니다(`W/critic/indep.log`, `W/patch/logs2/compare_ba.txt` 'position 798 typed' 행, `W/corrections_r1/recheck.log`).
- 저장소 함수와 독립 구현을 무작위 입력 20,000건으로 비교했습니다. 최대 상대 차이는 3.3e-16입니다.
- Position DV01을 비우면 그 순간 계산기에 입력된 채권의 수익률 DV01을 씁니다. 곡선과는 무관합니다. Notional이 5,000,000이면 3,990.93이 됩니다.
- 이 근사가 성립하는 조건:
  - 선물 가격이 CTD 선도가격 / CF를 따라갑니다(net basis가 거의 일정).
  - 금리가 움직이는 동안 CTD가 바뀌지 않습니다.
  - 헤지 대상과 CTD의 수익률이 같은 bp만큼 움직입니다(yield beta 1). 예를 들어 β = 0.9라면 10계약 뒤 잔여는 +66.94입니다(가정 예시).
  - 변동이 작아야 합니다(1차 근사).
  - CTD DV01이 계약 1개 액면당 통화/bp여야 합니다.
  - 엄밀히는 인도일 기준 forward DV01을 써야 합니다.
- 반영하지 않는 것: CTD 변경, gross/net basis와 repo, 인도 옵션, invoice price(선물가 × CF + 경과이자), variation margin tail.
- KRX KTB 국채선물은 현금결제이고 CF가 없습니다. 그래서 이 식을 그대로 쓸 수 없습니다(일반 지식, 사양서 미대조).

### 4.6 곡선과 데이터 경로

- FRED 시리즈와 단위: DGS1MO ~ DGS30(`data.py:67-68`)이고, 퍼센트를 100으로 나눕니다(`:582`). 독립 forward-fill과 비교한 차이는 6.9e-18입니다.
- 부트스트랩: 독립 동시 Newton과 비교했습니다. 4개 곡선에서 zero 차이 2.1e-15 이하, 0~40년 DF 차이 1.4e-14 이하입니다.
- 보간: ln DF가 t에 선형(z·t 선형)이고, 양 끝 밖은 zero가 평탄합니다. linear-in-zero 보간과 비교하면 15y z-spread가 8.088bp 다릅니다.
- 출처에 따라 바뀌는 숫자: z-spread, Carry/Roll, Breakeven, KRD, 시나리오 P&L.
- 출처와 무관한 숫자: Price, Yield, Macaulay, Modified, Convexity, DV01, 헤지(변형 곡선 8종에서 같음).
- 출처별 표시(HEAD):
  - FRED 정상: 녹색 칩, 배너 없음.
  - auto에서 FRED 실패, 빈 데이터, 5행 미만, 2y·10y 누락: 빨간 배너와 회색 SYNTHETIC 칩.
  - fred 명시에서 실패: 오류 배너만.
  - synthetic: 공급자를 부르지 않음.
- 캐시:
  - 키는 `FRED_<id>_504`, TTL 기본 21,600초입니다.
  - 차가운 캐시에서는 호출 1회(11개 id)이고, 이후 Run·도구 전환·재시작은 0회입니다.
  - TTL 안에서는 FRED가 죽어도 캐시를 씁니다. TTL이 지나면 auto는 SYNTHETIC, fred는 오류입니다.
- 소유자 화면: HEAD 합성 패널은 소유자 숫자를 재현하지 못합니다(±100bp에서 599~712 차이: B +100bp 598.7, A −100bp 712.3). 합성 패널은 날짜와 무관하게 같은 값입니다. 다만 소유자 PC의 코드 버전을 모르므로 "합성이 아니었다"는 결론은 조건부입니다(미확인).

### 4.7 짧은 만기 carry/roll (5.5% 쿠폰, 수익률 4.5%, 합성 곡선, 100당)

| 만기 | 가격 | HEAD 합계 | 독립(같은 관례) | 차이 | HEAD Breakeven | 라벨 / 실제 h |
|---|---|---|---|---|---|---|
| 0.30 | 101.3874 | −1.2694 | −1.2694 | 0 | −426.7bp | 3m / 0.25 |
| 0.2501 | 101.6128 | −1.2650 | −1.2650 | 0 | −509.0bp | 3m / 0.25 |
| 0.25 | 101.6132 | −2.6400 | −1.2650 | −1.3750 | −1062.6bp | 3m / 0.25 |
| 0.24 | 101.6584 | −2.6457 | −1.2157 | −1.4300 | −1108.8bp | 3m / 0.24 |
| 0.10 | 102.2938 | −2.7181 | −0.5181 | −2.2000 | −2716.9bp | 3m / 0.10 |

차이는 c·100·(1/f − T)와 같습니다(0.25: 5.5 × 0.25 = 1.375, 0.24: 5.5 × 0.26 = 1.430, 0.10: 5.5 × 0.4 = 2.200). 패치 사본에서는 모든 행의 차이가 0입니다. 라벨은 실제 h를 따르고(예: "Carry (36d)"), 만기가 horizon 안이면 Breakeven은 "n/a"입니다.

### 4.8 소수 만기와 clean/dirty (FC-03 재확인)

| 경우 | 화면 가격(dirty) | 경과이자 | clean | clean을 Price에 넣었을 때 YTM 오차 |
|---|---|---|---|---|
| 7.3y, 5.5%, y 4.5% | 107.256456 | 1.1 | 106.156456 | +17.33bp |
| 7.3y, 5.5%, y 5.5% | 101.091056 | 1.1 | 99.991056 | +18.62bp |
| 7.3y, 4.0%, y 4.5% | 97.712767 | 0.8 | 96.912767 | +13.28bp |

실제 결제 예(독립 street 공식): 5.5% 반기, 만기 2034-02-15, 결제 2026-10-28, ACT/ACT ICMA.
- dirty 107.261644, 경과이자 1.105978, clean 106.155666.
- 저장소 가격은 107.223769입니다. 일정 차이(ACT/365F, 정확히 1/f 간격) 때문에 street dirty보다 0.037875 낮습니다.
- clean을 넣으면 화면 YTM은 4.6681%(+16.81bp)입니다.
- street dirty를 넣어도 일정 차이로 −0.59bp가 남습니다.

---

## ⑤ 수정안

### 5.1 패치 개요

- diff: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/patch/bonds_screen.diff`
- sha256: `0466725dbe1ce6080ea10856ef119cb4d920bd4e3de9208545c85710e3475d80`
- 규모: 9개 파일, +1436 −112.
  - README.md 2, core/ficc/bonds.py 98, core/ficc/curves.py 2, core/ficc/data.py 87, core/ficc/insights.py 14, tests/bonds_screen_acceptance.py 949(새 파일), tests/run_all.py 4, ui/bonds_page.py 389, ui/qcharts.py 3.
- 적용 확인(이 보고서 작성 때 다시 확인함):
  - 저장소 HEAD `319f732`에서 `git apply --check`가 통과합니다.
  - 새 archive 사본에 적용하면 `W/patch/patched`의 9개 파일과 바이트까지 같습니다.
  - CRLF 파일 5개(README.md, core/ficc/bonds.py, core/ficc/curves.py, tests/run_all.py, ui/qcharts.py)의 줄끝이 보존됩니다(`.gitattributes`의 byte-exact 규칙).
- 저장소에는 적용하지 않았습니다. 적용 여부는 소유자가 정합니다.
- 적용한다면 소유자가 `python tests/run_all.py` 전체로 `qa/acceptance_results.json`을 다시 만들어 함께 커밋해야 합니다. 이 감사는 규칙상 그 파일을 만들 수 없었습니다.
- 적용 전에 RP-01(5.6)의 notice 문구와 테스트 단언을 함께 고치기를 권합니다.

### 5.2 hunk별 내용

| 파일 | hunk (HEAD 줄) | 고치는 것 | 이슈 |
|---|---|---|---|
| ui/bonds_page.py | @@ -6,16 (모듈 docstring) | 화면이 쓰는 관례와 입력 계약을 문서화 | BS-22 |
| ui/bonds_page.py | @@ -29,31 (_num, 상수) | `_num(required, gt, ge, le)`과 `_FieldError` 추가. 쉼표는 세 자리 구분자만 허용. 오류 문구에 원문 사용. −0을 0으로. STALE_TEXT 상수 | BS-04, BS-05, BS-06, BS-07, BS-19 |
| ui/bonds_page.py | @@ -66,106 (build_bonds_page 본문) | 모든 입력에 변경 핸들러와 낡음 배너. `_snapshot()`으로 클릭 때 한 번만 읽고 검증. 실행 토큰과 lock 안의 `paint()`. fail도 paint 경유. "Computed for: … curve requested … · served …". 칩 문구. "Curve check" 배너. 해설의 출처 문장. payload `inputs`·`par_yields`. z-spread 실패를 입력 필드 문맥으로. Conventions notice. 짝 field error 지우기 | BS-01, BS-02, BS-04, BS-07, BS-14, BS-15, BS-16, BS-22, BS-34, BS-35, BS-36 |
| ui/bonds_page.py | @@ -177, @@ -185,37 (시나리오·헤지 블록) | 헤더 "Shock (bp, cc zero rates)", "P&L % of MV". 모든 key tenor를 소수 한 자리로. 이 곡선의 실제 수익률 변화 notice(괄호 문구는 RP-01). 헤지 side(sell/buy), 절댓값, Rounded(0에서 먼 쪽), "Net DV01 after hedge", override/calculator 라벨과 차이 경고, 단위 경고, 근사 고지, payload 확장. Breakeven "n/a"와 부호별 툴팁. 작은 DV01 소수 표시 | BS-03, BS-08, BS-09, BS-11, BS-12, BS-13, BS-23, BS-24, BS-27, BS-28, BS-29, BS-41 |
| ui/bonds_page.py | @@ -225, @@ -235, @@ -278 | 빈 화면 안내를 늘 보이는 문구로. 레이아웃에 배너 자리. self-check에 assert 추가 | BS-04, BS-02 |
| core/ficc/bonds.py | @@ -10,15 (docstring) | "dirty PV"라고 명시. (1+y/f) 비율은 평탄 곡선에서만 성립한다고 적음 | BS-22 |
| core/ficc/bonds.py | @@ -162, @@ -181, @@ -189 (CarryRoll, carry_roll) | 만기 ≤ horizon이면 받은 현금 전부로 total 계산, horizon = h 반환, breakeven NaN. 일반 분기의 죽은 항 제거 | BS-08 |
| core/ficc/bonds.py | @@ -263 (ScenarioRow) | pnl_pct 분모 주석 | BS-24 |
| core/ficc/bonds.py | @@ -280 (SCENARIO_SHOCKS) | fly 정의(−12.5·KR2 + 25·KR5 − 12.5·KR10) 주석. 정의는 바꾸지 않음 | BS-11 |
| core/ficc/bonds.py | @@ -287,20 (shocked_curve) | 충격 tenor를 보간 zero 값으로 knot에 넣은 뒤 bp를 더함 | BS-10 |
| core/ficc/bonds.py | @@ -323 (futures_hedge_ratio, round_contracts) | 비유한 입력·overflow면 ValueError. 정확한 0에서 먼 쪽 반올림 `round_contracts`. 근사·단위 docstring | BS-28, BS-30, BS-13 |
| core/ficc/bonds.py | @@ -400 (self-check) | round_contracts assert | BS-28 |
| core/ficc/curves.py | @@ -44 (coupon_times) | n = max(1, …): 만기일은 늘 현금흐름일 | BS-07 |
| core/ficc/data.py | @@ -42, @@ -66 (import, 상수) | monotonic 시계. stale 5영업일, 급변 100bp, 10y 범위 0.1%~25% | BS-14, BS-16, BS-17 |
| core/ficc/data.py | @@ -165 (_fred_fetch) | `FredReader(…, retry_count=0, timeout=HTTP_TIMEOUT_SECONDS)` | BS-17 |
| core/ficc/data.py | @@ -215, @@ -446, @@ -472 (_LAG_TRIED, _transport_failure, _provider_rows) | 전송 실패이면서 경과 시간이 0.5 × timeout 이상일 때만 id별 재시도 생략 | BS-17 |
| core/ficc/data.py | @@ -570 (load_treasury_curve) | 실패 사유를 묶고 400자로 자름. 늦은 id를 캐시 항목당 한 번만 다시 받음 | BS-15, BS-37 |
| core/ficc/data.py | @@ -589 (_treasury_from_fred) | 10y 범위 검사. note에 Stale, Carried forward, 큰 하루 변동, Missing tenors(보간 설명) | BS-14, BS-15, BS-16 |
| core/ficc/insights.py | @@ -109, @@ -120, @@ -130 (narrate_bond) | DV01을 "per bp of the bond's own yield"로. 작은 DV01은 소수 둘째 자리. 만기가 horizon 안이면 breakeven 대체 문장. "zero-curve scenarios (z-spread held)" | BS-09, BS-08, BS-23 |
| ui/qcharts.py | @@ -40 (_style) | left·center·right 제목 모두 pal.text 색 | BS-18 |
| tests/bonds_screen_acceptance.py | 새 파일 | 회귀 테스트 33개. 숫자는 파일 안의 독립 공식(_ind_*)과 비교 | BS-26 |
| tests/run_all.py | @@ -43, @@ -77, @@ -128 | `bonds/` 묶음 등록과 --suite 도움말 | BS-26 |
| README.md | @@ -850 | --suite 목록에 bonds 추가 | BS-26 |

반영하지 않은 것과 그 이유:

| 항목 | 이유 |
|---|---|
| BS-17 실패 기억(negative cache) | 기억하는 동안 모든 FICC 화면에서 auto/fred 재시도의 뜻이 바뀝니다. 기존 테스트가 `_fred_fetch`를 실패에서 성공으로 연달아 바꿉니다. 그래서 국소 수정이 아닙니다. 조용한 망에서 Run 한 번은 약 12초로 줄었지만, 반복하면 매번 기다립니다 |
| BS-17 FRED_BASE_URL 반영 | pandas_datareader 경로는 고정 URL을 씁니다. FredReader를 subclass해야 해서 최소 수정 범위를 넘습니다 |
| BS-01 Run 버튼 비활성화(P01-05) | 토큰만으로 잘못된 결과가 화면에 그려지는 일은 없어집니다. 중복 작업 비용과 pyplot 동시 사용(BS-38)은 남습니다 |
| BS-11 fly 정의 변경 | 정의를 바꾸면 숫자가 바뀝니다. 소유자가 정할 일입니다 |
| BS-04 "Quote by" 모드 선택기 | 수용 기준 4-1의 뜻이 바뀝니다. 배타 규칙, 두 칸 field error, 늘 보이는 안내로 대신했습니다 |
| BS-07 가격 하한 문구의 필드 표시 | 작은 가격의 "No yield in [-0.5, 2.0] …" 문구는 그대로입니다(P3 잔여) |
| BS-21 funding 관례 | 모든 채권의 Carry가 바뀝니다(합성 곡선에서 100당 0.03). 관례는 소유자가 정할 일입니다 |
| BS-20, BS-25, BS-31, BS-32, BS-33, BS-38, BS-40 | 코어 API 위생, 다른 화면 숫자 변경, worker 구조 분리, 다른 화면이나 문서, 재현되지 않음, 의존성 문제입니다 |
| BS-13 README 설명, BS-22 KRD 차트 제목, BS-24 차트 x축, BS-35 차트 제목 출처, BS-36 snapshot_id·fetched_at, BS-39 폭·접근성 | 부분 항목입니다. fcharts와 README는 건드리지 않았습니다 |
| 회귀 테스트 CI 실행 | 저장소에 CI 설정이 없습니다(코드로 확인됨) |

### 5.3 리뷰 판정과 처리

- 독립 리뷰어는 리뷰 전 패치(v1)를 다시 적용하고 다시 실행했습니다. 판정은 "수정 후 승인"(approve_with_changes)입니다.
- 지적 13건(P2 2건, P3 11건)을 모두 검증한 뒤 반영했습니다. 거부한 지적은 없습니다. 일부는 근거를 갖고 변형해서 반영했습니다. RV-13은 일부만 해결됐습니다(RP-01).

| RV | 심각도 | 지적 | 처리 |
|---|---|---|---|
| RV-01 | P2 | 경과 시간만 보고 id별 재시도를 생략했습니다. 그래서 느리지만 살아 있는 망에서 404 하나가 곡선 전체를 실패시켰습니다. HEAD는 10 tenor로 성공, v1은 0/11 실패였습니다 | 리뷰 제안대로 "전송 실패이면서 경과 ≥ 0.5 × timeout"으로 바꿨습니다. slow_batch에서 HEAD와 최종 패치 모두 10 tenor로 성공합니다 |
| RV-02 | P2 | 늦은 실패 테스트가 HEAD와 구별되지 않았습니다(핸들러 단언을 빼면 HEAD도 PASS) | 두 Run의 입력을 같게 하고, fetch가 첫 호출에만 답하게 바꿨습니다. HEAD FAIL, 패치 PASS입니다 |
| RV-03 | P3 | 사유를 첫 줄 160자로 잘라 원인이 사라졌습니다 | 전문을 묶어 자릅니다. 리뷰 제안 240자 대신 400자로 했습니다. 403 프록시 문구가 321자라 240자로 자르면 "403 Forbidden"이 잘리기 때문입니다 |
| RV-04 | P3 | 해설에 "so"가 두 번 나와 인과가 잘못 읽혔습니다 | 문장을 고쳤습니다 |
| RV-05 | P3 | 짝 field error가 한 칸에 남았습니다. stale 쓰기가 lock 밖에 있었습니다 | 반영했습니다. 리뷰 제안의 `in` 대신 `is`로 비교합니다. Flet 0.85.2 컨트롤은 값이 같으면 ==가 True이기 때문입니다(실측) |
| RV-06 | P3 | 깊은 음수 수익률에서 z-spread 문구가 필드를 밝히지 않았습니다 | 입력 필드 문맥으로 바꾸고 주석을 고쳤습니다. 하한은 빈도마다 다르게 실측했습니다(freq 1은 −35%에서도 실패) |
| RV-07 | P3 | Computed for 줄이 요청한 출처만 보였고, 유효숫자가 6자리였습니다 | "curve requested … · served …"와 유효숫자 12자리로 바꿨습니다 |
| RV-08 | P3 | Missing tenors 문구가 보간 방식과 맞지 않았습니다 | curves.py:82-83과 맞게 고쳤습니다 |
| RV-09 | P3 | 대조하지 않은 CF 범위와 ZN 수치를 사실처럼 썼습니다 | "A rough guide, not exchange data"로 바꾸고 ZN 수치를 뺐습니다 |
| RV-10 | P3 | 늦은 id 재조회가 Run마다 반복될 수 있었습니다 | TTL > 0일 때만, 기록 시각을 비교해, 캐시 항목당 1회만 다시 받습니다 |
| RV-11 | P3 | HEAD에서 F 테스트가 하네스 단언 때문에 먼저 실패했습니다. 저장소 코드를 부르지 않는 테스트가 있었습니다 | 핸들러 존재는 별도 테스트로 단언합니다. 산술만 하던 테스트는 docstring으로 옮겼습니다 |
| RV-12 | P3 | README --suite 목록에 bonds가 없었고, CI가 없었습니다 | README는 고쳤습니다(CRLF 보존). CI와 qa 파일은 반영하지 않았습니다 |
| RV-13 | P3 | notice의 (1+y/f)는 평탄 곡선에서만 정확합니다 | 일부 해결. 이 곡선에서의 실제 값(예: +103.2bp)을 보이게 했습니다. 평탄 4.5% 곡선에서 그 값 +102.5bp는 독립 정확식 (f + y)(e^{Δ/f} − 1)과 일치합니다. 다만 지적 자체가 부정확했습니다. 100·(1 + y/f) = +102.2bp는 평탄 곡선에서도 1bp 극한의 1차 근사일 뿐이고, 정확값은 +102.5bp입니다. 패치는 괄호에 이 1차 근사를 "on a curve flat at this yield"의 값으로 적어, 같은 평탄 곡선의 +102.5bp와 어긋납니다(RP-01, P3, 미해결) |

- 리뷰 반영분은 2차 독립 리뷰를 받지 않았습니다. 대신 리뷰 전 패치에 새 테스트 파일을 실행하면 22/33이고, 실패 11개가 모두 이번 리뷰 항목입니다. 이 보고서를 쓰면서 최종 패치를 다시 실행했습니다(⑥ 6.1).

### 5.4 수정 전후, 같은 입력 비교 (합성 곡선, stand-in 페이지)

| 입력 | HEAD | 패치 |
|---|---|---|
| 표 2.1 다섯 행(가격, 수익률, Mac, Mod, Cvx, DV01, z, Carry/Roll/합/BE) | 예: 5.5/4.5 → 107.982 / 4.500% / 7.92y / 7.74 / 73.0 / 836 / −317.8bp / −1.177 / −0.346 / −1.524 / −18.2bp | 다섯 행 모두 같은 값 |
| Price 100 + Yield 4.5 | "Give exactly one of price or ytm." | "Fill exactly one of Price (per 100) and Yield %: both are filled. Clear one; the blank one is computed from the other." |
| 두 칸 모두 빈칸 | 같은 문구 | "Fill exactly one of Price (per 100) and Yield %: both are blank." |
| Scenarios 5.5/4.5, 5.5/5.5(새 가격, P&L) | 예: +100bp 99.760 / −82,220 | 모든 행이 같음 |
| fly 표시 | "3m +0 / 2y -12 / 5y +25 / 10y -12 / 30y +0" | "3m +0.0 / 1y +0.0 / 2y -12.5 / 3y +0.0 / 5y +25.0 / 7y +0.0 / 10y -12.5 / 20y +0.0 / 30y +0.0" |
| 가상 곡선(소유자 숫자 근사) | −81,596.5 / +89,400.0 / −74,657.2 / … | 같음 |
| 부분 곡선(20y·30y 없음), 30년 채권 | bear steepener −22,434.36, bull flattener +23,224.91, fly +18,830.51 | −61,437.59, +69,496.02, +1,333.73. +100bp는 −148,984.65로 같음 |
| 헤지 기본(798.19, 65, 0.8) | Position DV01 "798", sell 9.82, Rounded 10, 잔여 타일 없음 | "Position DV01 (calculator)" 798.19, sell 9.82, Rounded 10, Net DV01 −14.31(over-hedged) |
| 헤지 798 입력 | "Position DV01" "798", 9.82, Rounded 10, notice "-14 per bp"(빈칸 경우와 같은 화면) | "Position DV01 (override)" 798.00, 9.82, Rounded 10, Net DV01 −14.50 |
| 헤지 숏(−798.19) | "Contracts to sell −9.82", Rounded −10 | "Contracts to buy 9.82", Rounded 10, Net +14.31 |
| 헤지 682.5, CF 1 | 10.50 → Rounded 10 | 10.50 → Rounded 11, Net −32.50 |
| 헤지 CF 빈칸 | CF 1.0000, 12.28 | "Conversion factor: required." |
| 헤지 CTD −1 / CF 0 / CF −0.8 | 모두 "CTD DV01 per contract and conversion factor must be positive." | "CTD DV01 / contract: must be > 0, got -1." / "Conversion factor: must be > 0, got 0." / "… got -0.8." |
| 헤지 CTD 0.065 | Futures DV01 "0.08", 9,823.82 | "0.08125", 9,823.82와 "Check the units … A rough guide, not exchange data" |
| 만기 0.25, 5.5/4.5 | Roll −1.613, 합 −2.640, BE −1062.6bp | Roll −0.238, 합 −1.265, BE n/a |
| 만기 0.1, 4.5/4.5 | "Carry (3m)" −0.520, Roll −1.796, 합 −2.316, BE −2325.9bp | "Carry (36d)" −0.520, Roll +0.004, 합 −0.516, BE n/a |
| 만기 1e-10 | "IndexError: index -1 is out of bounds …" | 102.250, DV01 0.00, "Carry (0m)", BE n/a |
| 만기 0 | "maturity must be positive years, got 0.0." | "Maturity (years): must be > 0 and <= 100, got 0." |
| 만기 1e5 | "The function value at x=-0.5 is NaN; solver cannot continue."¹ | "Maturity (years): must be > 0 and <= 100, got 1e5." |
| Price 0.01 | "No yield in [-0.5, 2.0] reproduces price 0.0100." | 같음(필드 표시 없음, BS-07 잔여) |
| Yield '4,5' | 45.000%, 11.554 | "Yield %: '4,5' is not a number." |
| Yield '-0' | "-0.000%" | "0.000%" |
| Coupon 빈칸 | 0% 채권 64.082 | "Coupon %: required." |
| 낡은 결과(1.3 조작) | 표시 0건 | "Inputs changed since this result was computed. Press Run to refresh it." |
| FRED 403 프록시 | 같은 사유 11번 반복, 4.93초, 12호출 | 사유 1묶음("…Tunnel connection failed: 403 Forbidden"), 1.24초, 12호출 |
| 응답 없는 망(timeout 3초, auto) | NOT_RUN(HEAD의 기본 경로는 E 검증에서 1,446.6초) | 3.11초, 1호출, "Read timed out. (read timeout=3.0)" |

¹ 이 셀의 근거는 `W/A_input_contract/a05_extremes.log:17`과 비평가 재실행 `W/critic/drive_edges_head.log`입니다. 패치 단계 비교 하네스는 이 경우 HEAD 메시지를 기록하지 못했습니다(`W/patch/logs2/compare_ba.txt:77-78`이 `{} []`, `ba_head.json` edges 'maturity 1e5'의 notes가 빈 목록). 만기 0, Price 0.01, 헤지 CTD·CF 행의 근거는 `W/critic/drive_edges_*.log`와 `W/corrections_r1/drive_hedge.log`입니다.

### 5.5 성능 (같은 기계, 순차 실행, Run당 중앙값; data = load_treasury_curve 시간)

| 도구 / 경로 | HEAD wall (data / compute) | 패치 wall (data / compute) |
|---|---|---|
| calc, 합성 곡선(5회) | 0.2726초 (0.0046 / 0.2681) | 0.2203초 (0.0046 / 0.2157) |
| scenarios, 합성 곡선(5회) | 0.1365초 (0.0043 / 0.1322) | 0.1496초 (0.0046 / 0.1451) |
| hedge, 합성 곡선(5회) | 0.0130초 (0.0042 / 0.0087) | 0.0205초 (0.0050 / 0.0135) |
| calc, FRED stub 정상(3회) | 0.2019초 (data 0.0005) | 0.2086초 (data 0.0006) |
| 응답 없는 FRED stub(auto, timeout을 0.2초로 줄임) | 2.71초, 12호출 | 0.41초, 1호출 |

- 합성 경로의 ms 단위 차이는 측정 잡음 수준입니다.
- HEAD의 단계별 시간(F, 20회 중앙값): 곡선 생성 4.3ms, 부트스트랩 4.1ms, analyze_bond 2.6ms, scenario_pnl 0.8ms, 해설 0.04ms. 시간 대부분은 matplotlib 차트입니다(calc 207.1ms).
- 실제 FRED 요청 시간은 NOT_RUN입니다.
- 모의 FRED에서 차가운 캐시 Run은 573.9ms였고, 그중 네트워크 대기가 305.6ms였습니다.

### 5.6 조사자 수정안에서 발견한 결함과 최종 패치의 처리

| ID | 심각도 | 결함 | 최종 패치 처리 |
|---|---|---|---|
| A-12 | P2 | A의 수정안(coupon_times n ≥ 1, 만기 하한 0 초과)을 그대로 넣으면 만기 1e-10에서 Breakeven −2,250,000,278,533.8bp가 정상 결과처럼 나옴 | 만기가 horizon 안이면 breakeven을 NaN("n/a")으로 둠(BS-08). 패치 화면은 102.250, BE n/a |
| M-01 (C) | P2 | 안내문 "parallel rows exceed DV01 x bp"가 +100bp 행에서 거짓 | 안내문에 "exceed"가 없고 실제 수익률 변화를 보임. 테스트가 "exceed"가 없음을 단언. 단 괄호 문구는 RP-01 |
| M-02 (C) | P2 | 선형 fly의 "밖은 고정"이 단기·장기를 −12.5bp 평행 이동시킴 | fly 정의를 HEAD 그대로 두고 표시만 고침 |
| M-1 (D) | P3 | floor(abs(n) + 0.5)의 부동소수 결함(0.49999999999999994 → 1, 2^52+1 오류) | round_contracts가 정확히 계산함. 두 경우를 테스트로 단언 |
| M-5 (D) | P3 | fix.diff가 LF로 정규화돼 CRLF 파일에 적용되지 않음 | 최종 diff는 HEAD blob 기준으로 git이 생성함. CRLF 보존, `git apply --check` 통과 |
| G 수정본의 구멍(G 검증, G-02 안) | P2 | Run 중에 바꾼 입력이 결과 도착 뒤에 표시되지 않음 | `paint()`가 그릴 때 현재 입력과 클릭 때 입력을 비교해 배너를 켬 |
| RP-01 (최종 패치 잔여) | P3 | 시나리오 notice(패치본 `ui/bonds_page.py:374-390`)가 괄호에 1차 근사 100·(1 + y/f) = +102.2bp를 "on a curve flat at this yield"의 값으로 적음. 평탄 4.5% 곡선에서 같은 notice가 "moves its yield by +102.5bp (+102.2bp, 100 x (1 + y/f), on a curve flat at this yield)"를 보여 같은 곡선에 두 값이 나옴. 정확값은 (f + y)(e^{Δ/f} − 1) = +102.5bp. 테스트 `tests/bonds_screen_acceptance.py:877-890`이 이 문구를 그대로 단언함(888행은 +102.5bp, 889-890행은 +102.2bp 괄호 문구). 판정: 테스트로 확인됨 | 미처리. 수정: 괄호를 "about 100 x (1 + y/f) per bp for small shocks"로 바꾸거나 정확식 (f + y)(e^{Δ/f} − 1)을 쓰고, 889-890행의 단언을 함께 고침 |

---

## ⑥ 테스트 로그

### 6.1 이 보고서 작성 단계의 재실행 (2026-10-27)

사본 `F/head`는 HEAD `319f732`이고, `F/patched`는 HEAD에 `bonds_screen.diff`를 적용한 것입니다. 네트워크는 닫힌 프록시로 막았습니다.

| 테스트 | HEAD 사본 | 패치 사본 | 로그 (F = W/final_report) |
|---|---|---|---|
| tests.bonds_screen_acceptance(새 모듈 33개, HEAD에는 같은 파일을 실행) | FAIL 29 / PASS 4 | PASS 33/33 | F/logs/head_bonds_xrun.log, F/logs/patched_bonds.log |
| tests.ficc_acceptance(in-process) | PASS 57/57 | PASS 57/57 | F/logs/head_ficc.log, F/logs/patched_ficc.log |
| self-check: ui.bonds_page, core.ficc.bonds, curves, data, insights | PASS 5/5 ("ok") | PASS 5/5 | F/logs/head_selfchecks.log, F/logs/patched_selfchecks.log |
| 독립 공식 대 저장소(spot.py): 표 2.1, 헤지, 평탄·합성 시나리오 | PASS(표시값 30/30 일치, 최대 차이 1.35e-4) | PASS(저장소 출력 줄이 HEAD와 같음) | F/logs/spot_head.log, F/logs/spot_patched.log |
| 짧은 만기 carry(spot.py STUB) | FAIL(합계 −2.6400, 독립 −1.2650) | PASS(−1.2650) | 같은 로그 |
| 낡은 결과 재현(stale.py) | 재현됨(표시 0건, on_change 0/8) | 배너 표시, on_change 8/8 | F/logs/stale_head.log, F/logs/stale_patched.log |
| 경계 입력 구동(비평가 drive_edges.py: 만기 0/−1/1e5, 작은 가격, NaN/Inf, 공백, 헤지 칸) | 3.3·BS-05·5.4의 HEAD 문구 재현 | 3.3·BS-05·5.4의 패치 문구 재현 | W/critic/drive_edges_head.log, W/critic/drive_edges_patched.log |
| 헤지 입력 구동(drive_hedge.py: CTD 0/−1/빈칸, CF 0/−0.8/'abc'/빈칸) | 공통 문구 4건, 'abc' 필드 문구, 빈칸 2건은 조용히 기본값 | 칸별 문구 7건 | W/corrections_r1/drive_hedge.log |
| 독립 재계산(recheck.py: 볼록성 예측, 0.24% 기준, 599~712, 헤지 두 경로, 평탄 곡선 정확값) | 4.4·4.5·4.6의 수치와 일치 | — | W/corrections_r1/recheck.log |
| `git apply --check`(저장소, HEAD 319f732) | — | 통과 | — |
| 새 사본에 적용한 결과와 W/patch/patched 9개 파일 바이트 비교 | — | 같음 | — |
| 저장소 `git status --short` | 0줄 | — | — |

HEAD에서 PASS한 4개는 다음과 같습니다.
- 특성화 테스트 3개(test_request_table_21_rows_match_independent_formulas, test_par_premium_discount_and_ytm_inversion, test_duration_convexity_dv01_by_finite_differences). HEAD의 계산이 맞기 때문입니다.
- test_slow_batch_with_an_http_error_is_still_retried_per_id. HEAD는 늘 id별로 재시도하기 때문입니다.

패치 사본의 33/33에는 RP-01의 모순된 문구를 단언하는 test_scenario_notice_reports_this_curves_yield_move가 포함됩니다. 이 테스트의 PASS는 문구가 정확하다는 뜻이 아닙니다.

### 6.2 패치 단계 실행 (로그: W/patch/logs2)

| 테스트 | HEAD 사본 | 패치 사본 |
|---|---|---|
| self-check core.ficc.bonds / curves / insights / data, ui.bonds_page | PASS 5 | PASS 5 |
| tests.ficc_acceptance | PASS 57/57 | PASS 57/57 |
| tests.flet_api_guard | PASS 4/4 | PASS 4/4 |
| tests.bonds_screen_acceptance | FAIL(4/33) | PASS 33/33 |
| tests.quant_acceptance | PASS 53/53 | PASS 53/53 |
| tests.macro_m1_pit | PASS 24, NOT_RUN 7 | PASS 24, NOT_RUN 7 |
| tests.macro_m1_integration | PASS 7/7 | PASS 7/7 |
| engine_acceptance::test_81 | PASS | PASS |
| tests.expansion_acceptance | PASS 20/20 | PASS 20/20 |
| tests.macro_acceptance | PASS 419, FAIL 1, NOT_RUN 122 | 같음(테스트별 상태 차이 0) |
| run_all.select + run(ficc 다음 bonds, 한 프로세스, main 미실행) | NOT_RUN(HEAD에는 bonds 묶음이 없음) | ficc PASS 57, bonds PASS 33 |
| 리뷰 전 패치(v1)에 새 테스트 파일 실행 | — | 22/33. 실패 11개가 모두 리뷰 항목 |

macro_acceptance의 FAIL 1개는 `macro_m8_pipeline/test_dry_run_end_to_end_on_the_local_cache`(AssertionError)입니다. HEAD에서도 똑같이 실패하며 Bonds 범위 밖입니다.

### 6.3 차원별 실행 요약 (각 차원은 자기 수정본으로 시험함. 최종 패치는 이를 하나로 합친 것)

| 차원 | 실행한 것 | HEAD | 차원 수정본 | 근거 |
|---|---|---|---|---|
| A 입력 계약 | _num 표 24개, 페이지 구동 34검사, 스레드 R1·R2, 회귀 12 | 페이지 11/34, 회귀 2/12, 스레드 FAIL | 34/34, 12/12, PASS | A_input_contract.md |
| B 가격·위험 | 표 2.1, 규칙 200건, 그리드 640건, 곡선 44조합, UI 18회, 회귀 7 | 일치(최대 3.2e-12), 회귀 1/7 | 회귀 7/7 | B_pricing_risk.md |
| C 시나리오 | 재현 c1, 모양 c2, 적합 c3, UI c4, 회귀 10 | 회귀 6/10 | 10/10 | C_scenarios.md |
| D 선물 헤지 | 독립 20,000건, UI 구동 32, 회귀 11 | 회귀 0/11, ficc 57/57 | 11/11, ficc 58/58 | D_futures_hedge.md |
| E 곡선 출처 | 페이지 경로 17종, 캐시, 부트스트랩 4곡선, 회귀 10, 멈춘 망 | 회귀 0/10, 멈춘 망 1,446.6초 | 10/10, 12.4초 | E_curve_source.md |
| F 성능·상태 | 성능, 캐시, 재현성, 일관성 410개, 스레드 T1~T5, 회귀 7 | 일관성 410/410, 회귀 2/7 | 회귀 7/7 | F_perf_state.md |
| G 실제 UI | 브라우저 27스텝, 화면 숫자 171개, 회귀 5 | 숫자 171/171 일치, 회귀 0/5 | 회귀 5/5 | G_real_ui.md |

각 차원의 검증자는 저장소를 import하지 않는 별도 구현(Illinois, Newton, 해석 미분, 이분법)으로 숫자를 다시 계산했습니다. 모두 조사자 값과 맞았습니다.

### 6.4 NOT_RUN (통과로 세지 않음)

- `python tests/run_all.py` 전체: 규칙상 실행하지 않았습니다(qa/acceptance_results.json을 다시 씀).
- 실제 FRED 접속: egress 프록시가 403으로 막습니다. 실패 경로는 로컬 403 프록시로 재현했습니다.
- QuantLib 대조: 설치되어 있지 않습니다. 이전 결과(financial_calcs.md 8~11행)만 인용합니다.
- 데스크톱(FLET_APP) 창 클릭: 웹 모드로 대신했습니다.
- 최종 패치의 실제 브라우저 구동: stand-in 페이지로만 확인했습니다.
- CI 실행: 저장소에 CI 설정이 없습니다.
- Deep analysis(Claude API): 키가 없습니다. payload 내용만 확인했습니다.
- 패치 단계에서 HEAD의 blackhole 전체 로드: 다시 돌리지 않았습니다. E 검증의 실측 1,446.6초를 인용합니다.
- Windows에서의 메모리·시간 동작.

---

## ⑦ 남은 리스크

1. 실시장 정확성은 미확인입니다.
   - 가격은 정산일·경과이자가 없는 dirty PV입니다(FC-03).
   - 현금흐름 일정은 ACT/365F로 만기에서 거꾸로 셉니다. 실제 쿠폰 달력과 다릅니다(예: −0.59bp).
   - 이 감사는 공식이 코드의 정의대로 계산된다는 것까지만 보였습니다.
2. 2.3 시나리오 숫자는 계속 미확인입니다. 그날 곡선의 스냅샷이 없습니다. 패치 뒤에도 snapshot_id와 수신 시각은 기록하지 않습니다(par_yields만 추가).
3. FRED 실데이터 경로는 실제로 시험하지 못했습니다.
   - Treasury CMT 방법론과 이 코드의 관례(1년 미만 단리 DF, 1년 이상 반기 par)가 얼마나 맞는지 미확인입니다.
   - 합성 곡선은 비현실적인 수준(1m 9.6%)이지만, 배너로 표시됩니다. as-of 칩은 HEAD에서 오늘 날짜입니다(BS-34).
4. 패치는 저장소에 적용되지 않았습니다. 소유자 결정이 필요한 항목:
   - fly 정의(BS-11).
   - funding 관례(BS-21).
   - "Quote by" 모드 선택기를 넣을지(BS-04).
5. `core/ficc/data.py` 변경은 Bonds만의 것이 아닙니다.
   - FRED timeout, id별 재시도 규칙, 10y 범위 검사, note, 늦은 id 재조회는 Rates·Structuring·Macro의 FRED 로드에도 적용됩니다.
   - 재시도 규칙은 yfinance 일괄 호출에도 적용됩니다.
   - quant·macro·expansion 테스트 결과는 그대로였지만, 그 화면들은 구동하지 않았습니다.
6. 중복 클릭 시 무효가 된 작업자는 끝까지 실행됩니다. 조용한 망에서는 Run마다 약 12초를 기다립니다(실패 기억 없음). pyplot 동시 사용(BS-38)의 안전성도 미확인입니다.
7. 실제 데스크톱 창에서 field error, 배너, 늘 보이는 안내가 어떻게 보이는지는 미확인입니다.
8. CI가 없습니다. 회귀 테스트는 run_all에 등록했지만, 누군가 실행해야 효과가 있습니다. `qa/acceptance_results.json`은 소유자가 다시 만들어야 합니다.
9. 새 테스트 중 일부는 HEAD에서 동작이 아니라 새 API나 라벨이 없어서 먼저 실패합니다(round_contracts 없음, "Position DV01 (calculator)" 키 없음). 해당 동작 차이는 5.4의 전후 비교로 확인했습니다.
10. 헤지:
    - 65와 0.8은 예시값입니다.
    - 단위 경고 범위(CF 0.1~2, 선물 DV01 5~1000)는 거래소 자료와 대조하지 않았습니다.
    - KTB 선물에는 이 식을 쓸 수 없습니다.
    - CME 계약 액면은 원문 사양과 대조하지 않았습니다.
    - 소유자 화면의 Position DV01이 빈칸이었는지 798 입력이었는지는 미확인입니다(4.5).
11. 실패 사유 문구에서 프록시 주소를 지우는 처리는 없습니다. 오류 종류에 따라 주소가 payload에 남을 수 있습니다(미확인).
12. 늦은 id 재조회 기록(_LAG_TRIED)은 프로세스 메모리에만 있습니다. 앱을 다시 시작하면 한 번 더 다시 받습니다.
13. 패치 뒤 만기 1e-10 같은 극단 입력은 "Carry (0m)" 라벨과 DV01 0.00으로 표시됩니다. 틀린 숫자는 아니지만 의미가 약합니다.
14. 리뷰 반영분은 2차 독립 리뷰를 받지 않았습니다. 테스트 재실행으로만 확인했습니다.
15. 최종 패치에 문구 결함이 남습니다(P3, 테스트로 확인됨).
    - RP-01: 시나리오 notice가 1차 근사 +102.2bp를 평탄 곡선의 값이라고 부릅니다. 같은 평탄 곡선의 정확값 +102.5bp와 어긋납니다. 테스트가 이 문구를 단언합니다(5.6).
    - BS-07 잔여: 작은 가격의 "No yield in [-0.5, 2.0] …" 문구는 필드를 밝히지 않고 소수 구간을 씁니다.

---

## 부록 A: 주요 경로

- 요청서: `docs/audit/2026-10-27/bonds_screen_request.md`
- 차원 보고서: `docs/audit/2026-10-27/bonds_screen/A_input_contract.md`, `B_pricing_risk.md`, `C_scenarios.md`, `D_futures_hedge.md`, `E_curve_source.md`, `F_perf_state.md`, `G_real_ui.md`
- 스크린샷: `docs/audit/2026-10-27/bonds_screen/shots/`
- 패치 diff: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/patch/bonds_screen.diff`
- 새 테스트 모듈(패치 사본): `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/patch/patched/tests/bonds_screen_acceptance.py`
- 패치 단계 로그: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/patch/logs2/` (compare_ba.txt, suite_head.json, suite_patched.json, slow_batch_3copies.log, proxy403_*.json, blackhole_t3_*.json)
- 리뷰 로그와 리뷰 수정 diff: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/review/`
- 이 보고서의 재실행 스크립트와 로그: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/final_report/scripts/` (spot.py, stale.py, stale_handler.py), `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/final_report/logs/`
- 비평가 재실행: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/critic/` (indep.py, indep.log, indep_curve.log, drive_edges.py, drive_edges_head.log, drive_edges_patched.log)
- 정정 단계 재확인: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/corrections_r1/` (recheck.py, recheck.log, drive_hedge.py, drive_hedge.log)
- 차원별 작업 폴더: `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/<A_input_contract ~ G_real_ui>/`, 검증자 폴더 `/tmp/claude-0/-home-user-quantgen/244a07c1-ef5e-50fd-a9f1-360db0f46038/scratchpad/bonds_work/verify_<차원>/`

## 부록 B: 유지된 finding 79개의 검증 심각도와 통합 ID

- 합계 79 = P1 1 + P2 36 + P3 42입니다.
- 저장소 결함 74개(P1 1, P2 33, P3 40)는 BS-01 ~ BS-41로 묶었습니다. 수정안 결함 5개(P2 3, P3 2)는 5.6에서 처리했습니다.
- 검증자가 심각도를 바꾼 것: A-01 P1 → P2, C-04 P3 → P2, G-07 P3 → P2. B-01은 P2 유지(P1 경계).
- G-10은 BS-17에서 한 번만 셉니다(문구 부분은 BS-37). F-07은 BS-22에서 셉니다(BS-09 일부).

| ID | 차원 | 검증 심각도 | 판정 | 통합 |
|---|---|---|---|---|
| A-01 | A | P2(P1에서 낮춤) | 테스트로 확인됨 | BS-02 |
| A-02 | A | P2 | 테스트로 확인됨 | BS-02 |
| A-03 | A | P2 | 테스트로 확인됨(hint 표시 방식만 미확인) | BS-04 |
| A-04 | A | P2 | 테스트로 확인됨 | BS-05 |
| A-05 | A | P2 | 테스트로 확인됨 | BS-06 |
| A-06 | A | P2 | 테스트로 확인됨 | BS-01 |
| A-07 | A | P2 | 테스트로 확인됨 | BS-07 |
| A-08 | A | P3 | 테스트로 확인됨 | BS-04 |
| A-09 | A | P3 | 테스트로 확인됨 | BS-03 |
| A-10 | A(검증자) | P3 | 테스트로 확인됨 | BS-06 |
| A-11 | A(검증자) | P3 | 테스트로 확인됨 | BS-19 |
| A-12 | A(검증자, 수정안 결함) | P2 | 테스트로 확인됨 | 5.6 |
| B-01 | B | P2(P1 경계) | 테스트로 확인됨 | BS-08 |
| B-02 | B | P3 | 테스트로 확인됨 | BS-07 |
| B-03 | B | P3 | 테스트로 확인됨 | BS-20 |
| B-04 | B | P3 | 테스트로 확인됨 | BS-07 |
| B-05 | B | P3 | 테스트로 확인됨 | BS-21 |
| B-06 | B | P3 | 테스트로 확인됨(코드로 확인됨에서 정정) | BS-22 |
| M-1(B) | B(검증자) | P3 | 테스트로 확인됨 | BS-07 |
| M-2(B) | B(검증자) | P3 | 테스트로 확인됨 | BS-23 |
| M-3(B) | B(검증자) | P3 | 테스트로 확인됨 | BS-08 |
| C-01 | C | P2 | 테스트로 확인됨 | BS-09 |
| C-02 | C | P3 | 테스트로 확인됨 | BS-24 |
| C-03 | C | P2 | 테스트로 확인됨(해석 정정) | BS-11 |
| C-04 | C | P2(P3에서 올림) | 테스트로 확인됨 | BS-10 |
| C-05 | C | P3 | 테스트로 확인됨 | BS-25 |
| C-06 | C | P3 | 테스트로 확인됨 | BS-26 |
| M-01(C) | C(검증자, 수정안 결함) | P2 | 테스트로 확인됨 | 5.6 |
| M-02(C) | C(검증자, 수정안 결함) | P2 | 테스트로 확인됨 | 5.6 |
| D-01 | D | P2 | 테스트로 확인됨 | BS-12 |
| D-02 | D | P2 | 테스트로 확인됨 | BS-05 |
| D-03 | D | P2 | 코드로 확인됨(화면 구동으로도 관찰) | BS-13 |
| D-04 | D | P3 | 테스트로 확인됨 | BS-27 |
| D-05 | D | P3 | 테스트로 확인됨 | BS-28 |
| D-06 | D | P3 | 테스트로 확인됨 | BS-29 |
| D-07 | D | P3 | 테스트로 확인됨 | BS-30 |
| D-08 | D | P3 | 테스트로 확인됨 | BS-31 |
| D-09 | D | P3 | 코드로 확인됨 | BS-32 |
| M-1(D) | D(검증자, 수정안 결함) | P3 | 테스트로 확인됨 | 5.6 |
| M-2(D) | D(검증자) | P3 | 테스트로 확인됨 | BS-13 |
| M-3(D) | D(검증자) | P3 | 코드로 확인됨(시장 사실은 미확인) | BS-33 |
| M-4(D) | D(검증자) | P3 | 코드로 확인됨 | BS-26 |
| M-5(D) | D(검증자, 수정안 결함) | P3 | 테스트로 확인됨 | 5.6 |
| E-01 | E | P2 | 테스트로 확인됨 | BS-14 |
| E-02 | E | P2 | 테스트로 확인됨 | BS-15 |
| E-03 | E | P2 | 테스트로 확인됨 | BS-16 |
| E-04 | E | P3 | 테스트로 확인됨 | BS-34 |
| E-05 | E | P3 | 테스트로 확인됨 | BS-35 |
| E-06 | E | P3 | 테스트로 확인됨 | BS-36 |
| E-07 | E | P3 | 테스트로 확인됨 | BS-37 |
| E-08 | E | P3 | 테스트로 확인됨 | BS-31 |
| E-09 | E | P2 | 테스트로 확인됨 | BS-10 |
| E-V01 | E(검증자) | P2 | 테스트로 확인됨 | BS-15 |
| E-V02 | E(검증자) | P3 | 테스트로 확인됨 | BS-25 |
| E-V03 | E(검증자) | P2 | 테스트로 확인됨 | BS-17 |
| F-01 | F | P1 | 테스트로 확인됨 | BS-01 |
| F-02 | F | P2 | 테스트로 확인됨 | BS-01 |
| F-03 | F | P2 | 테스트로 확인됨 | BS-02 |
| F-04 | F | P2 | 테스트로 확인됨 | BS-03 |
| F-05 | F | P2 | 테스트로 확인됨 | BS-08 |
| F-06 | F | P2 | 테스트로 확인됨(모의. 최악 시간은 E-V03이 실측) | BS-17 |
| F-07 | F | P3 | 테스트로 확인됨 | BS-22(BS-09 일부) |
| F-08 | F | P3 | 코드로 확인됨(위험은 미확인) | BS-38 |
| F-M1 | F(검증자) | P3 | 테스트로 확인됨 | BS-36 |
| F-M2 | F(검증자) | P3 | 테스트로 확인됨 | BS-22 |
| G-01 | G | P2 | 테스트로 확인됨 | BS-01 |
| G-02 | G | P2 | 테스트로 확인됨 | BS-02 |
| G-03 | G | P2 | 테스트로 확인됨 | BS-05 |
| G-04 | G | P2 | 테스트로 확인됨 | BS-06 |
| G-05 | G | P2 | 테스트로 확인됨 | BS-12 |
| G-06 | G | P2 | 테스트로 확인됨 | BS-08 |
| G-07 | G | P2(P3에서 올림) | 테스트로 확인됨 | BS-18 |
| G-08 | G | P3 | 테스트로 확인됨 | BS-04 |
| G-09 | G | P3 | 테스트로 확인됨 | BS-39 |
| G-10 | G | P3 | 테스트로 확인됨 | BS-17(문구는 BS-37) |
| G-11 | G | P3 | 테스트로 확인됨 | BS-40 |
| G-12 | G | P3 | 코드로 확인됨 | BS-26 |
| G-V01 | G(검증자) | P2 | 테스트로 확인됨 | BS-17 |
| G-V02 | G(검증자) | P3 | 테스트로 확인됨 | BS-41 |
