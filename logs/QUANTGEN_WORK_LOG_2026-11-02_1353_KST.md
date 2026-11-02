# QUANTGEN 작업 로그 — 2026-11-02 13:53 KST

이 문서는 2026년 11월 2일 13:53 Asia/Seoul까지 확인한 작업 결과와 진행 중인 작업을 구분한 시점 기록이다. 저장소와 사용자 다운로드용 Markdown은 같은 내용으로 제공한다. 이후 진행 상황을 소급해 완료로 표시하지 않는다.

## 1. 현재 상태

- 제품 저장소: [xkg4real/quantgen](https://github.com/xkg4real/quantgen).
- 마지막으로 확인한 main: `8b4010430a9ece2a4e1b05b234abe81d3796771f`.
- PR #54, #58, #59는 정확한 소스 커밋의 CI 성공과 원격 병합 결과를 확인했다.
- §10 결함은 정규화한 **67그룹 중 21그룹 완료, 46그룹 미완료**다. 별칭을 별도 결함으로 중복 계산하지 않는다.
- 사용자의 최신 지시는 **남은 결함 46그룹을 우선 처리**하는 것이다. 현재 새 수정·합성검증을 진행 중이며, 이번 재개 이후 추가 완료 그룹은 아직 집계하지 않았다.
- 11월 2일 13:00까지 전체 Remaining Work를 완료한다는 목표는 달성하지 못했다.
- 실제 Windows 사용자 PC 인수, 실제 API 성공, 공급사 대조, 파일럿, 법률·라이선스 증거는 클라우드 합성검사로 대체하지 않는다.

## 2. 병합 완료한 작업과 검증 근거

| PR | 변경 내용 | 소스 커밋 | main 병합 커밋 |
|---|---|---|---|
| [#54](https://github.com/xkg4real/quantgen/pull/54) | Native 한영 저작 문구, 좁은 창 레이아웃, 설정 복구, 설치본·앱 구동검증 | `29d926169b8c4c29c1def4720a06bfe1203ad365` | `8dbdc139d4ec652490d3be4476eb4b41d8c234d2` |
| [#58](https://github.com/xkg4real/quantgen/pull/58) | LETF 가정 입력, FX/CMS/선도금리 설명, 실행 주문 측면 수와 왕복 거래 수 구분 | `67e76e704574af5365bee52733bed4e2b4dd47fe` | `f673f37001b53471ff2dfe139a44db72552c9235` |
| [#59](https://github.com/xkg4real/quantgen/pull/59) | 시뮬레이션과 다른 금리 재평가 모수를 사전 거부하고 최종 정규화 모수 전달 | `947ae44c89058b8dcc4b91b338b1fc9f33ea29be` | `8b4010430a9ece2a4e1b05b234abe81d3796771f` |

### PR #54

주요 변경 파일은 `quantgen_desktop/tools.py`, `chart_study.py`, `display_prose_catalog.py`, `macro_narrative_language.py`, `model_narrative_language.py`, `translations.py`, `app.py`, 관련 데스크톱 검사와 `tools/packaging/smoke_desktop.py`다.

- 숨은 탭의 높이 계산과 Windows 콤보 최소폭으로 인한 좁은 창 넘침을 수정했다.
- 저작된 Native 설명을 한영 전환에 연결했다. 원문 공급사 자료·역사 보고서·계산 숫자는 번역 또는 재판정으로 바꾸지 않았다.
- 최종 main 통합 과정에서 Home 9개, Native 26개, 정책 47개 검사가 통과했다. 이 수들은 서로 다른 검사 묶음이며 전체 제품 검사의 합계로 주장하지 않는다.
- 새 설치 wheel의 런타임 306파일·Python 229파일이 소스와 정확히 일치함을 확인했다.
- 7페이지·독립 가이드·Home 12행·Q-SCORE, 4개 서비스 유휴 상태, 실제 API 호출 0, 합성 worker·설정·JSON/ZIP·Flet 구동을 확인했다.
- [Runtime 41386502950](https://github.com/xkg4real/quantgen/actions/runs/41386502950), [Compliance 41386502697](https://github.com/xkg4real/quantgen/actions/runs/41386502697): success.

### PR #58

주요 변경 파일은 `core/ficc/letf_assumptions.py`, `forward_conventions.py`, `equity_deriv.py`, `insights.py`, `core/quant/backtest.py`, `core/research/etf_workflow.py`, `signals_analysis.py`, `structured_disclosure.py` 및 Native/Flet 표시·검사다.

- M4-N3: LETF 펀딩 금리·수수료·배당 가정을 명시하고 기존 영금리 참고 계산을 보존했다.
- M4-N6: 조건부 CIP 설명에서 근거 없는 일반적 차익·잡음 판정을 제거했다.
- M4-N11: CMS 결과를 첫 기간의 예상 연율 쿠폰으로 명확히 설명하고 보장 수익으로 읽히지 않게 했다.
- N11: 실행된 진입·청산 측면 수, 완료 왕복 거래 수, 마지막 미실행 신호와 비용 제외 승률을 구분했다.
- M3-N06: 5y5y의 5년 단순 연율 선도금리 규약을 명시했다.
- 통합 99개와 Home 9개 검사, 독립 LETF 45개 시나리오, 주문 수 8,192개 비교, 테스트 격리 정리 36개 회귀 검증을 수행했다.
- [Runtime 41386559163](https://github.com/xkg4real/quantgen/actions/runs/41386559163), [Compliance 41386559127](https://github.com/xkg4real/quantgen/actions/runs/41386559127): success.

### PR #59

주요 변경 파일은 `core/ficc/ratesim.py`, `core/research/rates_analysis.py`, `ui/rates_page.py`, `ui/fcharts.py`, `core/ficc/insights.py`, `tests/rates_revaluation_params_acceptance.py`다.

- M3-N08: 모형·kappa·theta·sigma·r0가 시뮬레이션과 다르면 재평가 전에 거부한다. 설명용 note 차이는 허용한다.
- Hull–White 정규화 후 최종 `sim.params`를 실제 호출 경로에 전달한다.
- 집중 10개·통합 21개 검사, 이전 대비 terminal 배열 12개·PV 배열 24개·집계값/설명 144개 일치를 확인했다.
- 별도 설치본의 실제 Qt 합성 workflow 6개 검사도 수행했다. 해당 설치본은 그 검사의 정확한 기존 커밋에 한정된 증거이며 최종 CI와 구분한다.
- [Runtime 41386603330](https://github.com/xkg4real/quantgen/actions/runs/41386603330), [Compliance 41386603276](https://github.com/xkg4real/quantgen/actions/runs/41386603276): success.

세 PR의 최종 자동검사는 Windows Python 3.11/3.12/3.14 및 Ubuntu Python 3.12를 포함한다. 이는 사용자 PC의 실제 Windows 수동 인수나 실제 공급사 연결 성공을 뜻하지 않는다.

## 3. 앞선 결정·다른 세션 결과 보존

- O8: GPT/Gemini 추가 심사·스펙 공개는 수행하지 않았고 `NOT_PERFORMED` 선택사항을 유지한다. 이 미실시만으로 Windows 인계를 막지 않는다. 기존 Claude 검토 근거와 면제 기록, 기술·Windows·실행 조건은 별도로 유지한다.
- O11 A2: 연구 PR #21의 구현·연구 브랜치 병합 기록을 보존한다. 가격 읽기 전 12개 설정 등록, `n_trials = 12 + U`, `U ≤ 24` 조건을 유지한다. 실제 파일럿 실행이나 `owner_confirmed` 부여는 수행하지 않았다.
- [PR #46](https://github.com/xkg4real/quantgen/pull/46): Claude API의 인증·권한·모델·결제·속도 제한·네트워크 오류를 구분하는 기존 수정은 보존한다. 실제 사용자 키의 인증 성공은 검증하지 않았다.
- 다른 UI 세션의 [PR #60](https://github.com/xkg4real/quantgen/pull/60): 독립 가이드, Home 12행, 최대 6종목 단일 스트림, 실험 Q-SCORE 변경과 해당 CI·병합 기록을 확인하고 이번 main 통합에 보존했다. 실제 수신 시세 성공 또는 투자 예측 검증으로 주장하지 않는다.
- 다른 웹 세션의 최종 HTML·Docs 검사 결과는 그 세션의 전달 기록으로 구분했다. 새 사이트 배포는 하지 않았으며 웹 HTML·소스·ZIP은 GitHub에 올리지 않았다.
- 비공개 Companion MVP, Step7A 진단 패치, N5 합성 재현, 비교 보고서는 소유자용 인계 자료에 보존했다. 비공개 원문·패키지는 이 공개 로그에 포함하지 않는다.
- Cracker 비교 대상은 `cracker.im`이다. 공식 본문 접근 실패 부분의 기능·가격을 추정해 채우지 않았다.

## 4. 남은 46그룹 우선 처리: 이번 재개 상황

기존 STATE와 원격 CURRENT의 직전 실행·작업·인계 ID·브랜치·커밋을 대조했다. OS 배타 잠금을 확보하고, 최신 CURRENT blob 조건으로 새 실행 ID를 기록한 후 원격 재읽기를 통과했다.

- 대표 작업 브랜치: `gpt/defects-priority-20261102`.
- 시작점: 위 main `8b4010430a9ece2a4e1b05b234abe81d3796771f`.
- 작업별 격리 브랜치: `gpt/defects-strategy-20261102`, `gpt/defects-rates-20261102`, `gpt/defects-options-20261102`, `gpt/defects-crypto-20261102`, `gpt/defects-models-20261102`.
- **이 절의 작업은 진행 중이다. 소스 PR 병합·최종 CI·Notion 추가 완료로 기록하지 않았다.**

| 작업 | 현재 확인·구현 범위 | 아직 필요한 확인 |
|---|---|---|
| 전략·ADF | N10 statsmodels 반환형 호환, N6 페어 노출 설명, N9 사후 레짐 설명 수정 중. N3/N14/N5는 가정·해석 한계를 별도로 표시 | 합성 수치 보존, Native/Flet/export/AI 회귀, PR/CI |
| 금리 | Hull–White의 theta를 장기 평균으로 오해하게 하는 표시 수정 중. PCA 재가중만으로 손익이 발생하는 합성 사례 재현 | M3-N02 손익·z·진단의 일관된 기준 구현, 독립 oracle, 역사 결과와의 분리 |
| 옵션 | 동일 변동성 헤지 기준의 손익 부호 색상, MFIV 유한 행사가 범위 누락, 박스 스프레드 네 다리 호가 유효성 수정 중 | 기존 가격·경로 보존, 양 UI·export·AI 검증 |
| Crypto | 누락 mark/index가 0%·−100%가 되는 문제, 누락 보유 평가가 완전 합계처럼 보이는 문제, 미계산 z가 0.00이 되는 문제 재현 | 결측/부분 상태 전달·합성 회귀 및 양 UI 확인 |
| 모형·ETF | 고정 원형 블록 bootstrap 설명, 일간 상수비중 재조정과 매수 후 보유의 구분, 현금만 있는 sleeve의 Sharpe 수치 문제 검토 | 수치·seed 보존, 표시/메타데이터·통합 회귀 |
| AI 해설 | 출력 한도 중단 거부, 배열의 묵시적 50개 절단 제거, 비유한 값 unavailable 처리, 숫자 참조 점검과 검증 미실시 표시를 로컬 구현 | UI 표시·내보내기 회귀 및 최종 통합·CI |

AI 숫자 참조 점검은 입력 숫자와의 표기 연결만 확인한다. 숫자가 일치해도 의미·단위·주장의 진실성 검증이나 모델 심사 통과를 뜻하지 않으며 공식 판정을 바꾸지 않는다.

## 5. 실패·검사 중인 사항도 보존

- 앞선 작업 중 Windows UTF-8 읽기, 전역 audit hook의 다른 검사 간섭, Qt 고정 대기 경쟁, 좁은 창 헤더 폭 회귀가 있었다. 최종 수정 후 위 정확한 PR head의 CI 성공을 확인했으며 이전 실패를 통과로 기록하지 않았다.
- PR #54 병합은 다른 세션의 main 전진으로 한 차례 충돌 거절됐다. 강제 갱신하지 않고 양쪽 변경을 보존해 다시 검증·병합했다.
- 이번 AI 수정의 첫 검사 실행은 기본 Python에 requests/Flet/PyQt6가 없어 import 오류 3개로 전체 실패했다. 새 순수 helper 검사 5개 통과만으로 전체 성공을 주장하지 않는다.
- 기존 개발 가상환경을 사용하는 격리 검사로 다시 실행 중이다. 이 시점에는 신규 Flet 표시 검사가 실패한 상태이며 나머지 UI 검사를 계속 확인 중이다. 따라서 이번 AI 수정 전체는 아직 검증 완료가 아니다.
- 공유 환경이나 패키지·보안·네트워크 설정을 바꾸어 이 실패를 우회하지 않았다.

## 6. Notion과 인계 상태

- 사용자가 지정한 계정의 Remaining Work에서 앞선 신규 하위 항목 8개를 취소선 처리하고 재읽기로 확인했다.
- 완료 ID: `⑬-8/b2/c/b/b/native`, `⑬-2/k/cloud-runtime`, `②-5/M4-N3`, `②-5/M4-N6`, `②-5/M4-N11`, `②-5/N11`, `②-5/M3-N06`, `②-5/M3-N08`.
- 부모 항목, 부분 수정, 실제 실행 증거가 필요한 항목은 미완료로 남겼다. 이전 날짜의 수치는 역사 기록으로 보존했다.
- [13:23 KST 통합 인계문](https://github.com/xkg4real/quantgen/blob/77bb1155a58e81d95646f2023ff8b5301aceb80e/CONSOLIDATED_CLAUDE_HANDOFF_2026-11-02.md)은 원격 저장·내용 일치를 확인했다.
- 그 부분 인계의 CURRENT returned 커밋은 `a10f147249c6a860dd8b39a4ca2823ac60017aa5`다. **이후 사용자의 46그룹 우선 지시로 다시 taken 상태에서 작업 중**이므로 이를 현재 중지 상태로 읽으면 안 된다.
- Claude가 인계문을 실제 열람했다는 별도 영수증은 없다.
- 기존 시간당 예약 하나를 유지한다. 새 예약 생성·run_now·환경 이전·배포는 하지 않았다. 예약 등록을 실제 자동 실행 성공 근거로 삼지 않는다.

## 7. 다음 순서와 유지할 제약

1. 진행 중인 독립 수정의 합성 재현·회귀를 끝내고 파일·결함 ID별 완료 범위를 대조한다.
2. 정확한 소스를 push/read-back하고 PR의 해당 head CI를 확인한 뒤 승인 범위에서 병합한다.
3. 완료한 ID/commit/검증만 LEDGER에 추가하고 CURRENT·STATE 및 지정 Notion 하위 항목을 갱신한다.
4. 보호된 연구 판정·동결 harness·공식 원장·실제 주문·TRADEGEN·사전등록·홀드아웃·소유자 실행 승인 규칙은 바꾸지 않는다.
5. 비밀·계좌·비공개 원문을 공개하지 않으며, .env와 보호 캐시를 읽거나 해시하지 않는다.
6. 실제 Windows/공급사/파일럿/법률·라이선스 증거가 없는 항목은 완료로 대체하지 않는다.
7. 실행 예산이 부족해지거나 정해진 주간 반환 시점에 이르면 타 세션 결과까지 포함한 안전한 부분 인계를 남긴다. 계정 토큰 잔량은 알 수 없으며 추정하지 않는다.

이 로그의 공개는 위 상태 기록에 한정된다. GPT/Gemini에 스펙을 공개하거나 추가 모델 심사를 진행한 것이 아니다.

## 8. 13:55 KST 추가 체크포인트 — 한도 오류에 따른 안전한 부분 중단

일부 하위 실행에서 사용량 한도 오류가 실제 발생했다. 계정 잔량을 추정하지 않고, 사전 지시에 따라 새 구현을 멈추고 각 작업의 파일·검사·다음 시작점을 취합했다. 앞 절의 진행 중 상태는 아래 기록으로 보충한다.

- **금리 N09:** 로컬 커밋 `524edf7867ebd06538746cde0f6d55f334923353`, 신규 3개와 기존 13개, 총 16개 검사 PASS. 수치 엔진 불변과 Hull–White theta만 바꿨을 때 terminal/fan/curve 배열 동일 확인. 원격 PR·CI·병합은 아직 없음. N02는 합성 재현·호출 경로 감사만 수행했고 구현을 시작하지 않았다. N01/N03/N05도 진단 미구현이다.
- **전략:** 소스·문서·검사 파일을 로컬 보존했다. 앞선 격리 18개 PASS 및 12개 합성 패널의 600행 비중·진단 일치가 보고됐다. 추가 AI 전달 단언을 포함한 최종 동일 검사 결과는 취합 중이다. 로컬 커밋·원격 반영 전이다.
- **옵션:** 담당 실행이 신규 7개 합성·실제 widget 검사 PASS와 기존 P&L/실현 변동성/감마 전체 배열 및 9개 scalar 정확 일치를 보고했다. 담당 실행이 한도 오류로 끝나 최종 통합·커밋·CI는 미완료다.
- **Crypto:** 신규 9개·기존 adapter 6개 PASS가 보고됐다. 추가 narrative 8개 PASS 후 마지막 언어 전환 검사 결과를 취합 중이다. 새 premium 행의 한국어 카탈로그 연결과 최종 통합·CI는 남아 있다. NEW-M6-21은 읽기만 했고 수정하지 않았다.
- **모형·ETF:** 담당 실행이 한도 오류로 중단돼 미커밋 파일을 보존했다. canonical ResearchRun 스키마를 확장하지 않으려던 정리 과정의 파일도 남아 있으므로 다음 실행은 diff부터 검토해야 한다. 완료로 집계하지 않는다.
- **AI:** 기존 개발 가상환경에서 실행한 24개 검사 중 23개 PASS, 1개 FAIL. 실패는 Flet 컨테이너의 문자열 표현에서 자식 텍스트를 찾는 신규 검사이며, 실제 자식 Text를 확인하도록 수정·재검사하기 전까지 전체 PASS로 기록하지 않는다. 실제 Claude 호출은 없다.
- 대표가 6개 작업 트리의 변경 파일과 추적 파일 patch, 시작 커밋·브랜치 manifest를 비공개 복구 위치에 별도 복사했다. 미완성 소스는 이 공개 로그에 첨부하지 않는다.
- 새로운 완료 그룹·Notion 취소선·제품 main 변경은 **없다**. §10 현황은 **21/67 완료, 46 미완료**를 유지한다.
- 다음 실행은 저장된 원격 소유권과 로컬 상태를 먼저 대조한 뒤 이 복구 파일/로컬 커밋을 통합하고, 실패·미완료 검사부터 해결해야 한다. 기존 21개 완료 그룹을 다시 작업하지 않는다.

이 추가 기록은 안전한 부분 중단을 설명한다. 이번 결함 수정 전체가 끝났거나 Claude가 실제 수신했다는 뜻은 아니다.
