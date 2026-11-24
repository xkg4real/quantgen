# 남은 작업 (2026-11-24판): 하부 세션 5개와 새 작업 ID

- 작성: 메인 세션 QUANTGEN/MAIN, 2026-11-24. 근거: 소유자 지시 2026-11-24(원문은 `OWNER_RULINGS_LOG.md` 2026-11-24 절과 handoff `SESSION_PIPELINE.md` 0-1절), 메인 워크플로 검증(handoff `plans/2026-11-24/`).
- 이 문서는 `CLAUDE.md`가 말하는 "가장 새 `REMAINING_WORK_*.md`"다. **`REMAINING_WORK_2026-10-27.md`와 `REMAINING_WORK_2026-11-17.md`의 열린 ID는 모두 그대로 유효하다.** 이 문서는 그 목록을 바꾸거나 닫지 않고 새 ID만 더한다. 어느 ID가 끝났는지는 handoff LEDGER가 정한다(`python3 tools/handoff/push_handoff.py --ledger`).
- 새 세션 일과 앞 판의 남은 일은 **함께 병행**한다(소유자, 2026-11-24).

## 0. 2026-11-20 이후 닫힌 ID (원장 기준)

| ID | 병합 | 비고 |
|---|---|---|
| OS-F2 | PR #136 → `72a055f` | 코드와 자동 검증만. 실제 소유자 자료 이전은 하지 않음 |
| DS-H/code | PR #137 → `6d25a33` | DS-H 부모는 소유자 진단 출력(OA-09) 뒤 |
| DIDM-1, DS-4a | PR #138 → `53e5e72` | |
| KEY-5/a | PR #139 → `dec979a` | |
| GH-2 | PR #147 → `dfae585` | `_backup/`과 archive 태그는 범위 밖 |
| PAY-0, PAY-2 | PR #149 → `de32ea1` | 초안. 문의 발송과 결정 P2-01~P2-15는 소유자 |

## 1. 세션 (2026-11-24부터 하부 세션 5개)

| 세션 | 맡는 ID | 인계 문서 (handoff) |
|---|---|---|
| PAYMENTS_ACCOUNT_KEYS | KEY-*, PAY-* | `PAYMENTS_SESSION_CURRENT.md` |
| OS_EXPANSION | OS-* | `OS_SESSION_CURRENT.md` |
| DATA_SOURCE (전 DATA_SOURCE_DIDM) | DS-* | `DATA_SOURCE_SESSION_CURRENT.md` |
| DIDM_DEV | DIDM-* | `DIDM_SESSION_CURRENT.md` |
| QUANTGPT | QGPT-* | `QUANTGPT_SESSION_CURRENT.md` |

- DATA_SOURCE와 DIDM_DEV의 파일 경계는 handoff `WORKBOARD.md` 맨 위 블록에 있다. 한 경로는 한 세션만 고친다.
- 하부 세션은 LEDGER를 직접 쓰지 않고 `--done` 문자열을 메인에 보낸다(11-17판 0절과 같음).
- UI/UX·웹사이트 세션은 소유자를 거쳐서만 닿는다. TRADEGEN 쪽과는 handoff `QUANTGPT_TRADEGEN.md`(인터페이스만)로 공유한다.

## 2. 새 ID

### 2.1 QuantGPT (QUANTGEN/MAIN -> QUANTGPT)

자체 LLM 시스템(코드명 QuantGPT). 설계·실행 명세서 v1.0 전문은 이 저장소에 두지 않는다(소유자 결정 2026-11-24, 저장소가 공개 상태). 여기에는 ID와 한 줄 범위만 적는다. 코드는 당분간 브랜치 `claude/quantgpt-q0-20261124`의 최상위 디렉터리 `qgpt/`에 있고(소유자 결정: 공개 quantgen에서 시작), main PR은 메인이 차례를 정한 뒤에만 연다.

| ID | 범위 (한 줄) | 관문 |
|---|---|---|
| QGPT-00 | 세션·ID 등록(이 문서, handoff 세션 지도) | 메인 세션 |
| QGPT-01 | 패키지 골격과 CI. QGPT-01/a는 `qgpt/` 골격 | 비공개 저장소는 소유자 작업 |
| QGPT-02 | 출력 계약(작업 유형 7종, 공통 봉투), 전략 카드 표준 QSS v0 | 지금 |
| QGPT-03 | 정책 필터(tool 모드 차단, owner 모드 기록) | 지금(코드). 규칙 목록 전체는 소유자 확인 뒤 |
| QGPT-04 | 숫자·인용·스키마·시점 누출 검사 | 지금 |
| QGPT-05 | 시도 원장(시도 1회 = 목적함수 + 데이터 버전 + 하이퍼파라미터 + 시드 + 모델 버전)과 DSR | 지금. QGPT-12보다 먼저 |
| QGPT-10 | 평가 문항 생성기와 문항 | QGPT-02~04 뒤. 문항 본문 공개 여부는 소유자 확인 |
| QGPT-11 | 채점기, 평가·학습·보정 묶음 분리 검사 | QGPT-10 설계와 함께(가짜 백엔드로 먼저) |
| QGPT-12 | 기준선 실행 | 소유자 작업(계정·예산) 뒤 |
| QGPT-20 | 근거 저장소 인덱스와 시점 필터 | 지금(문서·카드). 공시 부분은 약관 확인 뒤 |
| QGPT-21 | 호스트 도구 프로토콜(주문·계좌·키 함수 없음) | 지금 |
| QGPT-22 | 적응 방식 결정 문서 | 기준선 뒤, 소유자 승인 |
| QGPT-30 | TRADEGEN 통합(다리 모듈, import 경계 시험) | 소유자 승인. TRADEGEN 쪽 세션이 수행 |
| QGPT-31 | QUANTGEN 통합(공개 빌드에서는 꺼짐 고정) | 기준선 관문 뒤. 화면은 UI 세션 몫 |
| QGPT-32 | tool 모드 레드팀 관문 | QGPT-31 뒤 |
| QGPT-40, 41, 42 | 미세조정 데이터, 학습, 채택 평가와 모델 카드 | QGPT-22가 Go일 때 |
| QGPT-50, 51, 52 | 내보내기·양자화, 배포 매니페스트, 기기 벤치마크 | 채택 뒤. 52는 소유자 PC |
| QGPT-60, 61, 62 | 그림자 운영, 정기 재학습, DIDM 보조(뉴스 유형 판단) 어댑터 | 배포 뒤. 62는 DIDM Stage 1 관문 |

- QUANTGEN 공개 앱에서 QuantGPT를 켜는 것은 법인 설립 뒤 법령 검토 관문을 지난 뒤 소유자가 정한다. 그 전에는 공개 빌드에서 꺼진 채로 둔다.
- QuantGPT 출력은 주문·주문 초안·자동 실행 신호를 만들지 않는다. 가격 방향·확률 예측값도 내지 않는다(handoff `QUANTGPT_TRADEGEN.md` 1절).

### 2.2 DIDM 개발 (QUANTGEN/MAIN -> DIDM_DEV)

| ID | 범위 (한 줄) | 관문 |
|---|---|---|
| DIDM-2 | 채점기 계약: 모델이 내는 판단 `didm-judgement-v0`, 레코드 조립, JSON Schema 내보내기, 적합성 예시 | 지금 |
| DIDM-3 | 모델 학습 마감일 목록 `docs/didm/MODEL_CUTOFFS.md`와 자격 규칙(마감 + 3개월, 모르면 자격 없음). DIDM-3/a는 규칙 코드와 검증된 행만 | 지금. 남은 행은 출처 확인 뒤 |
| DIDM-4 | Stage 0 모의실험(Version 0): 모수 회복, 포함률, 검정력, 판정 | 지금 |
| DIDM-5 | Stage 1 측정 도구(κ, macro-F1, 연결 정밀도·재현율, ECE, Brier skill, 보정), 골드셋 표본 규칙과 라벨 안내 | DIDM-2 뒤 |
| DIDM-6 | 기준선 채점기(Loughran-McDonald, FinBERT 래퍼) | DIDM-2, DIDM-3 뒤. 사전 라이선스 확인 |
| DIDM-7 | 개체 연결, 근접 중복 군집화, 유사도 | 저장소, DIDM-2 뒤 |
| DIDM-8 | 시장 확인과 거시 서프라이즈(사전등록 4절 규칙) | DIDM-2 뒤 |
| DIDM-9 | 신뢰 상태와 충격 구성 | DIDM-7 뒤 |
| DIDM-S1 | Stage 1 실행(참신성 시험 포함) | DIDM-5, 6, 7, 골드셋, 자격 있는 모델. 라벨 담당은 소유자 결정 |
| DIDM-S2 ~ DIDM-S5 | 사건 연구, 예측 가치, QUANTGEN 관문, 그림자 운영 | 앞 단계 Go. 유료 자료와 법률 의견은 소유자 |

- `docs/didm/PREREG_V0.md`와 등록된 임계값은 바꾸지 않는다. `didm-score-v0`의 유형·필수 필드·버전 변경은 새 스키마 버전이다.

### 2.3 데이터 수집 (QUANTGEN/MAIN -> DATA_SOURCE)

| ID | 범위 (한 줄) | 관문 |
|---|---|---|
| DS-4a/2 | ALFRED 개정값 유효기간 검사 | 지금 |
| DS-4e/2 | Kalshi 입력 검사(가격·건수·쪽 넘김) | 지금. DS-4e는 이 뒤에 닫음 |
| DS-H/diag | 홈 지표 진단 한 줄 명령 `python -m core.research.markets` | 지금. DS-H 부모는 소유자 출력 뒤 |
| DS-5a, DS-5b, DS-5c | EODHD, Alpaca 뉴스, Massive 뉴스의 실제 연결(HTTP, 키 이름, 저장, 수집기 선택) | 소유자가 세 공급사를 공급원으로 더할지 확인한 뒤. main에는 입력 파서만 있음 |

### 2.4 결제·계정·키 (QUANTGEN/MAIN -> PAYMENTS_ACCOUNT_KEYS)

| ID | 범위 (한 줄) | 관문 |
|---|---|---|
| KEY-5/a/2 | KEY-5/a 검토의 작은 지적 점검과 빠진 시험 1개 | 지금 |
| PAY-1/design | 데스크톱 로그인 설계 문서(시스템 브라우저 + PKCE) | 지금(문서). 코드는 웹 계정 공개 뒤 |
| PAY-3/design | 회사 데이터 서버 설계 문서(위치 세 안 공통 부분과 차이) | 지금(문서). 위치는 소유자 결정 |

- 정책 문서 PR-2(계정 서비스 설명)는 11-17판 2.7절의 ID 없는 일 그대로다. 초안은 PAYMENTS, 병합은 메인.

### 2.5 OS 확장 (QUANTGEN/MAIN -> OS_EXPANSION)

| ID | 범위 (한 줄) | 관문 |
|---|---|---|
| OS-A1/apk-evidence | Android APK 검사 도구와 수동 빌드 워크플로 보강 | 지금. 실제 빌드와 기기 확인은 소유자 |
| OS-F2/guide | 자료 폴더 이전 안내 한 장(소유자용) | 지금 |
| OS-F1/lint16 | 변환 도구 lint 규칙 16: Qt 가상 함수 이름을 가리는 속성 대입 | 지금 |

### 2.6 메인 세션

| ID | 범위 (한 줄) |
|---|---|
| SESSION-PIPELINE/2 | 하부 세션 5개 반영: `CLAUDE.md`, `tools/handoff/push_handoff.py`의 세션 문서 이름, 이 문서, 결정 기록 |

## 3. 확인하지 못한 것 (미검증)

- QuantGPT 범위는 소유자가 준 명세서 v1.0을 메인이 줄인 것이다. 전문과 다른 곳이 있으면 전문이 우선하고 이 문서를 고친다.
- UI PR #140(초안)의 담당과 그 안의 KEY-5 화면 변경은 소유자 결정 전이다. KEY-5, OS-F1의 순서는 그 뒤에 정한다.
- 공수, 비용, 가격은 이 문서에서 다루지 않았다.
