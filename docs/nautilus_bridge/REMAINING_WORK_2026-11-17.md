# 남은 작업 (2026-11-17판): 11-17 소유자 답 뒤에 생긴 작업 ID

작성일 2026-11-17 · 작성: 메인 세션(QUANTGEN/MAIN, session_01H6RrzMUzF8vwK8xkX977mB)의 결정 기록 작업 · 기준: main `f058145`,
handoff `68522f1`
소유자 답 원문과 아직 답을 기다리는 것: `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`의 "2026-11-17, Claude Code 채팅: 11-16 업무
지시 결정 D1~D14에 대한 답" 절

## 0. 이 문서의 자리

- `CLAUDE.md`는 작업 ID가 가장 새 `docs/nautilus_bridge/REMAINING_WORK_*.md`에서 온다고 정합니다. 이 문서가 이제 가장 새
  판입니다.
- **`REMAINING_WORK_2026-10-27.md`의 열린 ID는 모두 그대로 유효합니다.** 이 문서는 그 목록을 바꾸거나 닫지 않고 새 ID만
  더합니다. 어느 ID가 끝났는지는 handoff LEDGER가 정합니다(`python3 tools/handoff/push_handoff.py --ledger`). 참고로 handoff
  `68522f1`의 `CURRENT.md` `next_ids`는 ⑦-2, ⑨-3a/recorder/1, ⑨-3a, ⑬-2/a3, ⑬-2/k, ⑩-1/b, ⑩-2/b, ⑫-2/b, ⑬-1/c입니다.
- 새 ID는 모두 handoff 브랜치 `plans/2026-11-17/`(handoff 커밋 `c7bf6df`)에서 왔습니다. 마스터 7절(ID 체계)이 이 문서를 작업
  ID의 공식 출처로 정했습니다. 아래 "출처"의 경로는 그 폴더 기준이고, `MERGE_QUEUE.md`는 handoff 루트입니다.
- 마스터(`MASTER_WORK_DESIGN_2026-11-17.md`)와 세션 지시문 `sessions/04`·`05`·`06` 또는 후속 보고서 `D5`·`D7`·`D9`·`D11`·`D14`가
  다르면 지시문과 보고서가 우선합니다(마스터와 `OWNER_REPORT_2026-11-17.md` 머리의 안내). 병합 순서와 동결은 `MERGE_QUEUE.md`가
  정합니다.
- 이 문서는 ID를 새로 만들지 않습니다. 출처에 이름이 있는 ID만 적고, 출처에 범위가 없는 것은 "범위 미기재"로 둡니다.
- 하부 세션은 LEDGER를 직접 쓰지 않고 `--done` 문자열을 자기 인계 파일에 적어 메인에 알립니다(지시문 04·05·06의 6절).

## 1. 공통 관문

| 관문 | 내용 | 출처 |
|---|---|---|
| F 동결 | P3(⑦-2) 시작부터 F21까지 main에 아무것도 병합하지 않음. handoff `68522f1` 기준 `freeze: none` | `MERGE_QUEUE.md` |
| 병합 차례 | 하부 세션은 자기 항목이 대기열 맨 앞이거나 메인이 "병합: <세션>"이라고 적었을 때만 PR을 엶. 병합 버튼은 메인 | `MERGE_QUEUE.md` 규칙, 지시문 9절 |
| F21 뒤 | GH-1, OS-F1(PySide6 전환), KEY-2→KEY-3→KEY-4→KEY-5, DS·DIDM PR. 순서는 메인이 다시 정함 | `MERGE_QUEUE.md` "F21 뒤" |
| D7-G 승인 | 소유자 답 대기. 승인이 handoff 문서나 메인 공지에 적히기 전에는 KEY-2·KEY-3 코드, KEY-4, OS-P0-c의 `DATA_API_BASE`·`GATEWAY_PROFILE`, DIDM "앱 연결"을 시작하지 않음 | `D7_ENV_STRUCTURE.md` 0절, 지시문 04·05·06 2절 |
| 공유 파일 | `docs/compliance/source-review.json`, `FACTS.md`, `config.py`, `.github/workflows/**` 등은 모든 세션을 통틀어 한 번에 PR 하나 | 마스터 4.1 규칙 2, 지시문 9절 |
| 법인 등 | G1 법인 설립, G2 유사투자자문업, G3 PG 심사, L 변호사 의견서, 표시권 | 마스터 6절 |

## 2. 새 ID

### 2.1 GitHub 정리 (메인 세션)

| ID | 범위 (한 줄) | 관문 | 출처 |
|---|---|---|---|
| GH-1 | `runtime-smoke.yml` CI 줄이기(PR마다 Linux·Windows 3.12만, 3.11·3.14는 주간·수동, 같은 PR의 이전 실행 취소), Compliance 결과물 보관 30일→7일, `tools/compliance/export.py` 링크 안내 | F21 뒤(대기열 9번). 비공개 시점과 Windows 검사를 소유자 PC로 옮길지는 소유자 선택 대기 | `sessions/01_MAIN_CLAUDE.md` T8-3, `D5_GITHUB_PRO_AND_PRIVATE.md` 3장, 마스터 2.1·4.2, `MERGE_QUEUE.md` |
| GH-2 | 파일 정리: `test_npu.py`, `mindmap/`, `.claude/launch.json`의 `godseye-dev` 항목 삭제. `_backup/`은 `archive-2026-11` 태그 뒤 | GH-1과 한 PR, F21 뒤 | 마스터 2.1·부록 F, `sessions/01_MAIN_CLAUDE.md` T8-3 |

- GH-2: `D5_GITHUB_PRO_AND_PRIVATE.md` 5장은 "F21 뒤 GH-2: 커밋 전 비밀키 검사를 CI에 추가 (제안)"이라고 적었습니다. 마스터와
  지시문 01의 GH-2에는 없는 범위라 아직 정해지지 않았습니다.

### 2.2 OS 확장 (QUANTGEN/MAIN -> OS_EXPANSION)

| ID | 범위 (한 줄) | 관문 | 출처 |
|---|---|---|---|
| OS-P0-a | 변환 도구 `tools/qt_port/pyqt6_to_pyside6.py`(`--check`, `--apply`, `--lint`)와 `tests/qt_port_acceptance.py` | 지금(브랜치) | `sessions/04_OS_EXPANSION.md` 7절 작업 1 |
| OS-P0-e | main과 UI 브랜치를 PyQt6·PySide6 두 벌로 돌리는 정식 시범, `docs/platform/PYSIDE6_TRIAL_<날짜>.md`, `PYSIDE6_UI_CHECKLIST.md` | 지금(브랜치) | 04 7절 작업 2 |
| OS-P0-f | 글꼴 대체 대안 `tools/qt_port/font_probe.py`, 세그폴트 최소 재현 `tools/qt_port/repro/` | 지금(브랜치) | 04 7절 작업 3 |
| OS-P0-c | `core/app_paths.py`의 `is_frozen()`·`user_data_dir()`, 새 `core/app_identity.py` | 지금(브랜치). `DATA_API_BASE`·`GATEWAY_PROFILE`은 D7-G 승인 뒤 | 04 8절 |
| OS-P0-b | 빌드 초안: `packaging/`, 바인딩 중립 PyInstaller spec, `platform-build.yml`, `stage.py --profile mobile` | 지금(브랜치). 실제 실행은 병합과 소유자 승인 뒤 | 04 8절 |
| OS-P0-d | 플랫폼 계획(Notion `6f75e02e…`) 개정 2판 초안, `docs/platform/PLATFORM_EXPANSION_<날짜>.md` | 소유자 확인. Notion 수정은 소유자 승인 뒤 | 04 8절 |
| OS-F1 | PySide6 전환일: UI 세션이 OS 도구로 PR 하나, 그날 `quantgen_desktop/**`·`tests/desktop_*` 잠금 | F21 뒤 + 소유자 "OS go". 자리는 F21 바로 뒤 첫 자리(D9 나안). D9 "예상 시간"의 뜻은 소유자 확인 대기 | 04 8절, `D9_PYSIDE6_ESTIMATE.md` 0절, `MERGE_QUEUE.md` |
| OS-F2 | `config.py`·`data/krx/kis_client.py`·`data/krx/opendart_client.py`의 `~/.nextgen` 경로 줄 | KEY-2 병합 뒤 | 04 4절·8절 |
| OS-F3 | 키 저장(KEY-2와 맞춤) | KEY-2와 함께 | 04 8절, 마스터 5.2 |
| OS-F4 | macOS 차이 | 04 8절 "이후" 순서(OS-F2 → `app_identity` 연결 → OS-F4 → OS-F5 → OS-M2 → OS-A1) | 04 8절 |
| OS-F5 | 범위 미기재(04 8절 "이후" 줄에 이름만 있음) | 같은 순서 | 04 8절 |
| OS-M2 | macOS `.app` | 같은 순서 | 04 8절, 마스터 2.1 |
| OS-M3 | 범위 미기재. 마스터 부록 F가 "Mac 없이 macOS" 질문의 시점("OS-M3 전 (F 뒤)")으로만 씀 | F 뒤 | 마스터 부록 F |
| OS-A1 | Android(Flet) 시험 2일: APK 크기, 첫 실행 시간, import 성공, Quant Lab 결과 1개를 데스크톱과 비교 | 같은 순서 | 04 8절 |

- 마스터 7절은 플랫폼 계획의 F1–F6, A1–A7, M1–M7, S1–S3을 모두 `OS-` 접두어로 바꾼다고 정했습니다. 위 표에 없는 나머지의
  범위는 OS-P0-d(개정 2판)에서 정합니다(미검증).
- 법인 뒤의 서명(D-U-N-S, Apple 조직, Windows OV), Android 업로드 키, 스토어는 출처에 ID가 없습니다.

### 2.3 결제·계정·API 키 (QUANTGEN/MAIN -> PAYMENTS_ACCOUNT_KEYS)

| ID | 범위 (한 줄) | 관문 | 출처 |
|---|---|---|---|
| PAY-A1 | 관리자 안내서 `docs/commercial/accounts/ADMIN_GUIDE.md`(D11 소유자 지시의 산출물) | 지금 | `sessions/05_PAYMENTS_ACCOUNT_KEYS.md` 7절 작업 1 |
| PAY-A2 | 계정 설정 묶음 `docs/commercial/accounts/ACCOUNT_SETUP.md`: 운영 풀 `quantgen-prod` 설정표, 소유자 AWS 순서, 웹사이트 요청 ACC-1~ACC-10, 정책 문서 값 | 지금. 소유자 결정 3개(운영자 표기, 메일함, 만 14세) 전에는 자리표시 | 05 7절 작업 2 |
| KEY-1 | 환경변수 이름 목록 `docs/commercial/ENV_NAMES.md`(비밀 10개, 설정 16개, 이름만) | 지금 | 05 7절 작업 3 |
| KEY-2 | 자격증명 저장소 `core/credentials/**`(OS 키 보관함, `quantgen_cloud` 자리 없음), KIS 토큰 캐시 | D7-G 승인 뒤 브랜치, 병합은 F21 뒤 | 05 7절 작업 3, `MERGE_QUEUE.md` |
| KEY-3 | 공급원 게이트웨이: 설계 문서 `docs/commercial/GATEWAY_DESIGN.md`, 코드 `core/gateway/**`와 경계 시험 | 설계는 지금, 코드는 D7-G 승인 뒤. 병합은 KEY-2 뒤 | 05 8절, `D7_ENV_STRUCTURE.md` 5장 |
| KEY-4 | `core/` 18개 파일의 공급사 호출 46곳과 `main.py:54`를 게이트웨이로 | KEY-3 병합 뒤 | 05 8절 |
| KEY-5 | 화면 쪽 25곳과 키·연결 화면(`status()` 행). **UI 세션 몫** | KEY-4 뒤, OS-F1 뒤 권장 | 05 8절, `D7_ENV_STRUCTURE.md` 5.6절 |
| PAY-0 | 결제 문의 7건 초안 `docs/commercial/inquiries/` | 지금. 발송은 소유자 | 05 8절 |
| PAY-2 | 결제 설계 문서(일정, 재시도, 상향·하향, 일할 계산, 해지, 가격 인상 고지). 시나리오 A만 | 지금 | 05 8절 |
| PAY-1 | 데스크톱 로그인 `core/account/**`(같은 풀의 `quantgen-desktop` 클라이언트). 계정 화면은 UI 세션 | 웹 계정 공개 뒤 | 05 8절 |
| PAY-3 | 서버 저장소(회사 데이터 서버). 위치는 소유자에게 먼저 여쭘 | 법인·계약 전에는 설계만 | 05 8절 |
| PAY-4 | 카드 PG | 법인과 PG 승인 뒤(G1, G3) | 05 8절, 마스터 6절 |

### 2.4 웹사이트 요청 ACC-1~ACC-10 (소유자를 거쳐 웹사이트 세션에 전달)

웹사이트 세션(`xkg4real/website`, 이 저장소와 main 대기열 밖)이 구현합니다. 결제·계정 세션이 PAY-A2에서 요청문을 만들고,
소유자가 웹사이트 세션에 붙입니다. 가입 화면은 플래그 `AUTH_UI_ENABLED=false`인 채로 배포하고, 켜기(공개)는 D11 진행 순서
7단계(소유자 시험, 공개 전 체크, 법률 확인 뒤)입니다. 이 요청이 마스터의 WEB-3·WEB-4를 대신합니다. 출처: `D11_ACCOUNTS_AND_ADMIN_GUIDE.md`
4장, 05 7절 작업 2.

| ID | 범위 (한 줄) |
|---|---|
| ACC-1 | 가입 화면(이메일, 비밀번호, 필수 약관·만 14세, 선택 광고 메일 기본 해제, 시드니 보관 안내) |
| ACC-2 | 이메일 인증 화면(6자리 코드, "코드 다시 받기") |
| ACC-3 | 로그인(SRP, MFA 단계, 계정 존재를 드러내지 않는 오류 문구) |
| ACC-4 | 비밀번호 찾기·새 비밀번호 |
| ACC-5 | 계정 페이지(이메일·비밀번호 변경, 2단계 인증, 광고 메일, 탈퇴, 내 정보 내려받기) |
| ACC-6 | 머리글·문구(로그인·가입 버튼은 플래그 뒤, 운영자 표기는 메인의 정책 PR 병합 뒤) |
| ACC-7 | 보안(라이브러리 고정, CSP, 토큰 보관) |
| ACC-8 | 하단(처리방침 링크 강조, 개인정보 문의 메일) |
| ACC-9 | 시험(개발 풀 끝에서 끝까지 자동 시험, 운영 풀 수동 시험 1회) |
| ACC-10 | 소유자에게 줄 것(앱 클라이언트 설정 확인표, 플래그 켜기 전 체크리스트) |

### 2.5 데이터소스·DIDM (QUANTGEN/MAIN -> DATA_SOURCE_DIDM)

| ID | 범위 (한 줄) | 관문 | 출처 |
|---|---|---|---|
| DS-1 | 대안 평가표 `docs/didm/VENDOR_EVAL_2026-11.md`(소유자 엑셀 9개 대안 × 19개 정보 유형) | 지금. 소유자 확인 | `sessions/06_DATA_SOURCE_DIDM.md` 7절 작업 1 |
| DIDM-0 | 사전등록 `docs/didm/PREREG_V0.md` | 지금. 소유자 승인 전에는 결과를 보지 않는 단계만 | 06 7절 작업 2 |
| DIDM-1 | 점수 스키마 `docs/didm/SCORE_SCHEMA_V0.md`, `core/didm/llm/schema.py`, `tests/didm_schema_acceptance.py` | 지금(브랜치) | 06 7절 작업 2 |
| DS-4a | 키 없는 커넥터 GDELT·ALFRED와 시점 저장소(`data/didm/`, `core/didm/`, `tools/didm/collect_daily.py`) | 지금(브랜치) | 06 7절 작업 3 |
| DS-H | 홈 지표 6개의 데이터 계층(`load_home_indicators`) | 소유자 진단 출력 뒤. 병합은 F21 뒤 대기열(소유자가 P3 전 자리를 주면 그때) | 06 8절, 마스터 4.2 10번 |
| DS-4b | Alpha Vantage, Tiingo, Cryptopanic | 소유자가 무료 키를 만든 뒤 | 06 8절 |
| DS-4c | CME FedWatch 종가판 | Stage 2 시작과 소유자 답(D14 질문 2) | 06 8절 |
| DS-4d | OpenDART·KIND, SEC EDGAR, ECOS | 소유자 답(D14 질문 3) | 06 8절 |
| DS-4e | Polymarket 실행, Kalshi | 변호사 확인(D14 질문 4) | 06 8절 |
| DS-3 | RavenPack RPA 1.0 견적 문안과 Bigdata.com 기준선 비교 | DIDM Stage 3 통과 뒤 | 06 8절, `D14_RAVENPACK_ALTERNATIVES.md` |
| DS-2 | **쓰지 않음.** Bigdata.com Pro 시험(★A 초안)은 D14 답에 따라 삭제 | — | 06 2.1절 |

- 마스터의 DS-4는 DS-4a~DS-4e를 묶은 이름입니다. 마스터 5.1은 DS-3을 "지금"에 두었으나 지시문 06(나중, 우선)은 Stage 3 뒤로
  옮겼습니다.
- "앱 연결"(DIDM 결과를 앱이 쓸 때 공급원마다 `core/gateway/routes.json` 한 행)은 출처에 ID가 없습니다. D7-G 승인과 KEY-3 병합
  뒤입니다(06 8절).

### 2.6 다른 세션의 ID (마스터가 정의, 여기서는 참고로만 등록)

| ID | 담당 | 범위 (한 줄) | 관문 | 출처 |
|---|---|---|---|---|
| WEB-0 | 웹사이트 세션 | 사이트 CI | 웹사이트 저장소 안 | 마스터 2.1·3.1·7절 |
| WEB-1 | 웹사이트 세션 | 색 추가(D10-A 사프란/황토) | 같음 | 마스터 2.1, 부록 E |
| WEB-2 | 웹사이트 세션 | 문구 정리(humanizer). 뜻이 바뀌면 main `docs/compliance` 먼저 | 같음 | 마스터 2.1, 부록 E |
| WEB-3 | 웹사이트 세션 | 출시 알림 폼과 백엔드 코드. **D11 변경으로 ACC 요청이 대신함** | — | 마스터 2.1, D11 4장 |
| WEB-4 | 웹사이트 세션 | 우리 로그인 UI(플래그 꺼짐). **D11 변경으로 ACC 요청이 대신함** | — | 마스터 2.1, D11 4장 |
| WEB-5 | 웹사이트 세션 | 로그인 후 화면 틀 | WEB-4(지금은 ACC) 뒤 | 마스터 2.1, 부록 E |
| ⑬-2/page-redesign/system | UI/UX 세션 | 마이페이지, 연결 탭 삭제 | 시안 승인 뒤, 병합은 F21 뒤 | 마스터 0절·2.1·7절 |
| ⑬-2/page-redesign/home | UI/UX 세션 | 홈 지표 6개와 그래프 | 시안 승인과 DS-H 뒤, 병합은 F21 뒤 | 마스터 0절·2.1·7절 |
| ⑬-2/page-redesign/system/2 | UI/UX 세션 | API 키 화면 | KEY-2와 page-redesign/system 뒤 | 마스터 2.1·7절 |

- UI/UX 세션과 웹사이트 세션의 브랜치와 인계 파일은 아무도 고치지 않고, 그 세션에 줄 요청은 소유자를 거칩니다
  (`MERGE_QUEUE.md` 규칙). 웹사이트 저장소 쪽 상태는 이 문서에서 확인하지 않았습니다(미검증).
- UI 세션 지시문 `sessions/02_UI_UX.md`의 `UI-` 번호는 그 세션의 것이라 여기 등록하지 않습니다.

### 2.7 ID가 없는 메인 세션 일 (출처가 ID를 주지 않음, 새로 만들지 않음)

- 이 결정 기록 PR(`MERGE_QUEUE.md` 5번), P3·F 뒤 main PR(LEDGER ⑦-2), 회원가입 정책 문서 PR(D11이 정식 계정으로 바뀌어 값은
  PAY-A2에서 받음: 문서 01, 02, 06, 07, 08, 16, 17, 18, 20과 `release-profile.json`, `D11_ACCOUNTS_AND_ADMIN_GUIDE.md` 0절),
  웹 거래 결정 메모(D12-A, ⑦-2 뒤, 그 뒤 기존 M-12), `push_handoff.py --doc` 확장(`sessions/01_MAIN_CLAUDE.md` T8).

## 3. 확인하지 못한 것 (미검증)

- 이 문서는 git에 있는 파일만 읽어 만들었습니다. 세 하부 세션의 인계 파일(handoff `OS_SESSION_CURRENT.md`,
  `PAYMENTS_SESSION_CURRENT.md`, `DATA_SOURCE_SESSION_CURRENT.md`)과 그 뒤의 진척은 읽지 않았습니다.
- 공수, 비용, 가격은 출처에서 모두 추정이거나 미검증입니다. 이 문서는 그 값을 다시 계산하지 않았습니다.
- ACC·WEB 항목은 다른 저장소의 일이라 그쪽에서 확인하지 않았습니다.
