# 인수인계 매뉴얼 (2026-10-29, 주간 사용량 95% 시점)

작성: Claude Code 메인 세션(`claude/amazing-gauss-tdiguu`). 다음 개발(ChatGPT 등)이 이 문서 하나로 이어갈 수 있게 썼습니다.
함께 읽을 것:
- `handoff` 브랜치의 `CURRENT.md`(현재 작업), `LEDGER.md`(끝난 ID), `AGENTS.md`(이어받는 규칙)
- 이 레포의 `CLAUDE.md`(인수인계 규칙)
- `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`(소유자 결정 원문)

## 1. 받은 과업 (시간순 요약)

| 과업 | 결과 | 근거 |
|---|---|---|
| QuantConnect → NautilusTrader 연구 브리지 (로드맵 ③) | **완료.** Task 1~5와 ③-6 클라우드 전체 실행·실행 기록 | `docs/superpowers/plans/2026-10-28-nautilus-execution-record.md`, LEDGER ③-1~③-6 |
| 구현 감사(141건)와 Bonds 화면 감사(41건) | 완료. 보고서와 제안 패치 | `docs/audit/2026-10-27-implementation-audit-report.md`, `docs/audit/2026-10-27/bonds_screen_audit.md` |
| ②-3 모델 한계 대장, ②-4 오류 통합 목록, ②-5 우선순위 대기열 | 완료(②-5는 순서 승인 ②-5/a, 3단계 Bonds 패치 ②-5/b) | `docs/nautilus_bridge/MODEL_LIMITS_REGISTER_2026-10-28.md`, `KNOWN_ERRORS_REGISTER_2026-10-28.md` 4절 |
| ①-2 달력 서명 | 완료. 17개 파일과 세트 1.0.0 소유자 서명(다른 Claude 세션이 수행, `main`에 있음) | LEDGER ①-2, ①-2/2, ①-2/3; `docs/audit/2026-10-27/13_signature_register.md` |
| 인수인계 프로토콜(GPT) | 사용 중. checkpoint와 LEDGER는 소유자 상시 승인 | `handoff` 브랜치 |
| PR #4 충돌 해결(3회) | 완료. `main`의 서명 달력 채택, PT-07 달력 변경 철회 | 결정 로그 "PR #4 충돌 해결" 절 |
| 소유자 답변(2026-10-29) 반영 | 진행 중(아래 3절) | 결정 로그 "(가), X-1, ②-5 …" 절 |
| PentPort 전략 감사 반영 → 남은 작업 재배치, REMAINING_WORK 개정 | **미완료.** 아래 4절의 순서는 Claude 제안 초안 | `docs/audit/2026-10-29/QUANTGEN_PentPort_Strategic_Improvement_Audit_2026-10-29.md` |

## 2. 현재 상태 (2026-10-29 15:10 KST)

- **작업 브랜치:** `claude/amazing-gauss-tdiguu`, PR #4(→ `main`, 충돌 없음). 소유자만 병합합니다.
- **마지막 검증:** 보호 캐시 없는 사본 전체 실행 825/964 passed, 2 failed, 137 not run.
  - FAIL 2건은 환경 탓입니다. 하나는 사본에 `yf_SPY.csv`가 없는 m8 dry run, 다른 하나는 리눅스에 `taskkill`이 없는 papers 테스트입니다.
  - Nautilus 스위트는 키 미설정 44/57, 키 설정 57/57입니다.
  - 실행 방법은 `handoff` `CURRENT.md` 6절의 `full_run.sh`입니다.
- **LEDGER:** ①-1~①-5, ①-2/2, ①-2/3, ②-1~②-4, ②-5/a, ②-5/b, ②-6, ③-1~③-6.
- **LEDGER 정정:** ②-5/b 행의 확인 칸 "완료 2026-10-29T15:0x+09:00"은 잘못 적은 것입니다. 실제 커밋 `4709cf2` 시각은 2026-10-29T14:58:46+09:00입니다. LEDGER는 고칠 수 없어 여기에 적습니다.
- **소유자 결정 기록:** X-1(2026-10-26 보호 캐시 접근)은 실행 기록에 포함하기로 결정됐고, 문안은 실행 기록 "Data-access history entry (X-1)"에 있습니다.
- **추가 자진 보고:** Bonds 검토 중 하위 에이전트의 `grep`이 보호 캐시 4개를 열었습니다. 일치한 내용이 없어 아무것도 출력되지 않았습니다. 결정 로그에 기록했습니다.

## 3. 멈춘 지점 (진행 중이던 것)

| ID | 상태 | 남은 일 |
|---|---|---|
| ④-2/a | **완료(이번 커밋).** 결정 양식 `docs/nautilus_bridge/O2_O15_DECISION_FORM_2026-10-29.md`(독립 검증 반영) | 소유자가 O2~O15와 승인 문장을 정함(④-2) |
| (설명) | **완료.** R3 10.2 A 질문 설명서 `docs/superpowers/specs/2026-10-27-strategy-lab-run-registry-Q-explainer_2026-10-29.md`(독립 검증 반영) | 소유자 답 |
| ①-2/4 | 평가 **초안만 있음**(독립 검증 중단): `docs/nautilus_bridge/drafts/PT07_LOADER_ASSESSMENT_DRAFT_2026-10-29.md`. 초안 결론: CAL-13과 M-4는 Go(서명 파일 그대로 로드, 승인 불필요), CAL-14는 재서명이 필요해 제외, CAL-12는 효용이 작아 제외 | 초안 재검증. 맞으면 `main`에서 새 브랜치로 구현(달력 세션과 겹침 확인, `core/calendars/`). 테스트를 더하고 전체 실행 |
| (재배치) | REMAINING_WORK 개정 **미완료.** 계획 워크플로는 사용량 때문에 중단 | 4절 초안을 검토해 `docs/nautilus_bridge/REMAINING_WORK_2026-10-29.md` 작성. 기존 ID(①~⑪)는 바꾸지 않고, 새 일은 새 ID(예: ⑫ P0 정합성, ⑬ P1 워크플로) |

## 4. 남은 작업과 처리 순서 (Claude 제안 초안, 소유자 요약 기준)

소유자 요약(원문)은 이 문서 끝에 있습니다. 원칙은 다음 네 가지입니다.
- 정합성(P0)을 UX(P1)보다 먼저 합니다.
- 모델, 게이트, 동결 연구, 판정 기준은 소유자 승인 없이 건드리지 않습니다.
- QUANTGEN에는 실주문 경로를 두지 않습니다(TRADEGEN만).
- 공개 배포는 ⑩-1 법률·라이선스 검토 뒤에 정합니다.

**물결 0: 지금 작업 마무리**
1. ①-2/4 평가 재검증 → Go면 구현(위 3절).
2. REMAINING_WORK_2026-10-29 작성(이 절을 바탕으로), 흐름도 갱신.

**물결 1: P0 정합성(감사 PR 순서)**
1. **PR-A 상태 단일 출처(새 ID 제안 ⑫-1, 감사 QG-P0-01).**
   - `main`에서 새 브랜치로 진행합니다(소유자 지시).
   - 기계가 읽는 상태 파일(예: `tools/status/` + `research_status.json`)을 만듭니다. 칸은 code_test, data_readiness, formal_gate, paper_study, distribution_policy, 출처·시각입니다.
   - 출처끼리 모순되면 실패하는 테스트를 둡니다. 모순 예:
     - README의 743/864와 `qa/acceptance_results.json`의 749/870
     - README의 "달력 미서명"과 서명된 MANIFEST
     - 게이트 `NOT_FROZEN`
   - README를 상태 파일과 맞춥니다. README는 CRLF입니다.
   - `qa/acceptance_results.json`은 다시 만들거나 커밋하지 않습니다(소유자 Windows 기록). 모델·게이트·숫자는 바꾸지 않습니다.
2. **PR-B 종목 식별과 비용 분류(⑫-2 제안, QG-P0-02 = ②-5 대기열 5단계의 K-f·PT-01·PT-02와 겹침).**
   - `BTCUSD`가 미국 주식 비용으로 분류되는 문제입니다.
   - `core/quant/validate.py`와 `instruments.py`는 동결 하네스 파일입니다(`core/quant/gate_package.py:36`). 그래서 **소유자 승인(12.8, K-f 앞당김, 하네스 변경)**을 먼저 받습니다.
   - 승인 전에는 식별 표와 회귀 테스트 설계만 진행합니다.
3. **PR-C Strategy Lab 누적 시행(= ⑨-3a, QG-P0-03).** R3 설계 승인과 10.2 A 답(설명서 있음) 뒤에 시작합니다. 기존 판정은 ⑨-3d까지 그대로 둡니다(그림자 산출).
4. **Nautilus 교차검증 완료(병행, ④~⑦).**
   - ④-2 소유자 결정(양식 있음) → ④-3 → ⑤-1 Windows 인계(소유자 PC, `docs/nautilus_bridge/RUNBOOK_windows.md`) → ⑤-2 공급사 대조 → ⑥-1 파일럿 1(SPY) → ⑥-2 파일럿 2(BTC, 1이 통과할 때만) → ⑦-1 → ⑦-2 `main` 병합.
   - O11: `E1.jsonl`이 없으므로 파일럿 1 전에 E1 원장을 어떻게 시작할지 소유자가 정해야 합니다.
   - ④-1(GPT·Gemini)은 필수가 아닙니다. 소유자가 Appendix B에 대체 심사를 기록할 수 있습니다.
5. **데이터 출처 검증(⑤-2, ⑨-2, QG-P0-05).**
6. **②-5 대기열의 결정이 필요 없는 단계:** 7단계 PT-04 등(`KNOWN_ERRORS_REGISTER` 4.1). 10절 결함 분류는 소유자 결정을 기다립니다.

**물결 2: P1 워크플로(소유자 요약 3번)**
- **PR-D ResearchRun 계약(⑬-1 제안, QG-P1-03):** PR-B 뒤. 스키마와 어댑터만 만들고 UI는 다시 쓰지 않습니다.
- **PR-E 6개 워크스페이스와 Research Home(⑬-2 제안, QG-P1-01·02):** PR-A·PR-D 뒤.
  - 워크스페이스는 Research Home, Markets, Build & Test, Portfolio & Risk, Research Library, System입니다.
  - 기존 16개 페이지는 모두 유지합니다.
  - NOT_RUN·REJECT를 초록 "준비 완료"로 뭉치지 않습니다.
- **PR-F 패키징·CI 스모크(⑫-3 제안, QG-P0-07·08):** PR-A와 함께 시작하고, 병합 관문 역할을 합니다.
- 그 밖의 P1은 PR-E 뒤입니다. Model Evidence Card(②-3 확장), 실행 비교, 위험 대시보드, 진행 표시 UX, 읽기 전용 SDK, TRADEGEN 피드백 격리(⑪-1)가 여기에 속합니다.

**물결 3: 배포 관문** ⑩-1 법률·데이터 라이선스 검토 → ⑩-2. README "개인 사용 전용"과 로드맵의 "무료 배포"가 충돌하므로 이것부터 정리합니다.

**범위 밖(당분간):** 리더보드, 소셜 트레이딩, PFOF 브로커리지, 실주문 API, 엔진 전면 재작성.

## 5. 소유자 결정 대기 (막는 순서)

1. ④-2: O2~O15 판정과 승인 문장. 양식은 `O2_O15_DECISION_FORM_2026-10-29.md`입니다.
2. PR-B: 동결 하네스 변경 승인, 12.8, K-f 앞당김.
3. R3 설계 rev 2 승인과 10.2 A 답(설명서 있음).
4. ②-5 10절 결함(임시 ID 71개, 신규 관찰 14건) 분류 여부.
5. ⑦-4 BS-21 조달비용 공식 변경 여부.
6. O11: E1 원장 시작 방법.
7. 감사 §12의 나머지 결정. 오류 목록 4.4에 순서대로 있습니다.

## 6. 반드시 지킬 것

- 보호 캐시 `docs/asset_expansion/cache/{yf_SPY,yf_BTC-USD,binance_BTCUSDT,upbit_KRW-BTC}.csv`는 열거나 읽거나 해시하지 않습니다.
  - 검색에는 `--exclude-dir=docs/asset_expansion/cache`를 붙입니다.
  - 전체 실행은 `full_run.sh`(sparse 사본)로만 합니다.
- `.env`를 열지 않습니다. `tests/run_all.py`를 직접 실행하지 않습니다. `qa/acceptance_results.json`(md5 `16c9baa5…`)은 다시 만들거나 커밋하지 않습니다.
- 동결 하네스(`HARNESS_SOURCES`), 게이트, 동결 연구, 판정 기준, 서명된 달력 파일은 소유자 승인 없이 고치지 않습니다.
- `paper_live/`, `grokteam/`은 고치지 않습니다. 태그는 push하거나 옮기지 않습니다. `owner_confirmed`, `host_fingerprint`, 서명 필드는 쓰지 않습니다.
- `main`에 직접 push하지 않습니다. PR 병합은 소유자가 합니다.
- CRLF 파일을 고칠 때는 CRLF를 유지합니다. 해당 파일은 `README.md`, `tests/run_all.py`, `core/ficc/bonds.py`, `curves.py`, `ui/qcharts.py` 등입니다.

## 7. 소유자 요약 (원문, 2026-10-29)

> 1. 핵심 판단: QUANTGEN에 퀀트 모델은 충분합니다. 문제는 뛰어난 리서치 코드베이스가 파편화되어 있어 추적하기 어렵고, 하나의 워크플로로 쓰기 힘들다는 점입니다. 보고서는 QUANTGEN을 증거 중심의 "리서치 운영체제(research OS)"로 포지셔닝하라고 권고합니다. 실제 자금 매매는 모두 TRADEGEN에 맡기고, PentPort는 엔진이 더 우수하다는 근거가 아니라 제품 설계의 명확성을 참고하는 벤치마크로만 봐야 한다고 봅니다.
> 2. UX보다 정합성 먼저 (P0): 가장 먼저 서로 충돌하는 상태 기록을 맞춰야 합니다. README는 743/864 PASS인데 QA 파일은 749/870이고, 캘린더는 이미 서명됐는데 README에는 아직 "미서명"으로 적혀 있습니다. 그다음 할 일은 다음과 같습니다.
>    * BTCUSD가 거래비용 분류에서 잘못 분류되는 문제 수정
>    * Strategy Lab이 현재 파라미터 그리드뿐 아니라 과거 시행 전체를 세도록 수정
>    * NautilusTrader 독립 교차검증 백테스트 완료
>    * 데이터 출처 검증 완료
> 3. 워크플로 재구성 (P1): 사이드바 16개 탭을 6개 워크스페이스로 묶습니다. Research Home, Markets, Build & Test, Portfolio & Risk, Research Library, System입니다. 핵심 제품 단위는 재현 가능한 "ResearchRun"이 되며, 여기에 데이터 버전, 코드 커밋, 비용, 랜덤 시드, 검증 게이트 버전, 판정을 기록합니다. NOT_RUN이나 REJECT 같은 결과는 절대 하나의 초록색 "준비 완료"로 뭉뚱그리지 않습니다.
> 4. 공개 배포는 별도로 관문을 두고 결정: 한국 법률 검토와 데이터 라이선스 확인이 먼저입니다. 로드맵의 "무료 배포" 계획이 README의 "개인 사용 전용" 문구와 충돌한다는 점도 이유입니다. 리더보드, 소셜 트레이딩, PFOF 브로커리지, 실주문 API, 엔진 전면 재작성은 당분간 명시적으로 범위에서 제외됩니다.
> 5. 시작점: 정해진 순서대로 6개의 PR을 진행합니다. 첫 번째인 PR-A는 기계가 읽을 수 있는 상태 파일과, 출처끼리 모순되면 실패하는 테스트를 만드는 작업입니다. 새 브랜치에서 보수적으로 진행하고 모델, 게이트, 동결된 연구(frozen studies)는 건드리지 않습니다. 판정 기준을 바꾸려면 반드시 소유자인 사용자님의 승인이 필요합니다.

원문 감사 보고서: `docs/audit/2026-10-29/QUANTGEN_PentPort_Strategic_Improvement_Audit_2026-10-29.md`.
