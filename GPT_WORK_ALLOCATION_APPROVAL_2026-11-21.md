# QUANTGEN 업무 분담·진행 승인안 — 2026-11-21

상태: **소유자 승인 대기**. 소유자 요청: “정리해서 당신이 어떻게 분담하여 어떤 업무를 진행할지, 정리해서 승인요청해주세요.”
execution: 679bce35-4b1b-4e15-baa3-8194c64c5b70
기준: 최초 handoff3b0062c901e79bab973a6229a03adcfe06686a77, 후속069868ad8a3a55cc8df3da65a4bd4bfbc4381fd6(DATA 세션 인수), main f065ec92dbce1e1b34e4adb0b6dbed724305a2f4, 확인 시각 2026-11-21T10:50:32+09:00.

## 1. 현재까지 확인한 결과

- 메인: 이전 GPT PR121/122와 Step10/P3/F는 Claude가 완료했다. KEY-4/a까지 main에 들어가 있다. 오래된 PR12 외 새 준비 작업 PR은 아직 없다.
- 사업: 분석·연구·시뮬레이션·모의투자 도구, 국내 카드 PG 월구독 시나리오 A. 가격·정책 문서와 실제 영업/결제 개통은 구분한다. 법인/규제/PG/법률/표시권 관문은 남아 있다.
- 계정·결제: KEY1~4/a main 완료. 최신 PAYMENTS 인계에는 AWS 설정·T1~T15 완료, 웹 preview 이후 T16~T19b/W9~W10 미완료로 기록됐다. PAY0/PAY2 e869064는 문의/설계 문서이며 실제 결제 코드가 아니다. OA32 발송·OA39 정책 답은 소유자 몫이다.
- 데이터·DIDM: DS-H f80b3b0과 DS/DIDM c206b10은 준비 브랜치다. 최신 인계의 공식무료6곳 소유자PC 확인을 예측 성능·표시권·전체 출시 완료로 바꾸지 않는다. 뉴스 방향은 GDELT+자체NLP, AlphaVantage/Tiingo/CryptoPanic 무료뉴스 제약으로 DS4b 보류다.
- 플랫폼: OS-F2 e44c48e는 main f065ec9를 합친 준비 브랜치다. UI7쪽과 PySide6 전환은 별도 UI 확인/대기열을 따른다.

원문: [WORKBOARD](WORKBOARD.md), [MERGE_QUEUE](MERGE_QUEUE.md), [PAYMENTS](PAYMENTS_SESSION_CURRENT.md), [DATA/DIDM](DATA_SOURCE_SESSION_CURRENT.md), [OS](OS_SESSION_CURRENT.md). 문서가 다르면 실제 git과 최신 세션 상단 기록을 대조한다.

## 2. 승인 요청하는 업무 분담

| 담당 | 업무·결과물 | 완료 기준 |
| --- | --- | --- |
| GPT 총괄(본 세션) | 최신 결정·남은일 정리, 각 담당 배정, 독립 검토 결과 반영, PR 순서 관리, CURRENT/WORKBOARD/LEDGER·sapientia Remaining Work 최소 갱신 | commit·PR·실제 검사 근거가 일치하고 완료한 하위만 기록 |
| OS 담당 | OS-F2 경로 선택·동의받은 migration 결함 수정, Windows/macOS 호환 검토, 관련 합성 검사와 PR 준비 | 목적지 경합/marker 실패 시 데이터 보존, 경로 선택 안정성, 지원하지 않는 이동은 명확히 거절, CRLF·동결 엔진 보존, 관련 CI 통과 |
| 기존 DIDM Codex 세션 + 본 세션의 검토 담당 | 별도 세션이 이미 인수했으므로 DS-H/DS-DIDM 구현은 그 세션에 유지. 본 세션은 보고된 commit의 독립검토·대기열/통합만 담당 | 동시 수정/선점 없음. 기존 승인 공급원·스키마·소유자 미결 사항을 유지하고 실제 성능/권리 근거와 구분 |
| 페이먼트·게이트웨이 담당 | KEY5a M1/M2와 후속 지적 검증·수정, KEY5 UI 연계 요청문, PAY0/PAY2 설계·승인 질문 정리 | 삭제/차단된 키로 provider 호출0, 갱신 중 차단 client 노출0 등 고치기 전 실패/수정 후 성공 근거. 결제 정책 미답은 임의 확정하지 않음 |
| 독립 검토 담당 | 각 변경의 보안·회귀·테스트 적정성·출처 검토 | 구현 담당과 별도로 검토하고 실패/미실시/증거 공백을 기록, 총괄이 병합 판단 |

2026-11-21T10:50:17+09:00에 DATA_SOURCE_SESSION_CURRENT가 별도 Codex DIDM 세션의 taken으로 갱신됐다(execution didm-gpt-20261121-6af7214e). 해당 active task는 선점하거나 다시 구현하지 않는다. 다른 세션 전달은 직접 도구가 없으므로 공용 인계와 소유자 경유로 한다.

읽기·분석과 격리된 수정/검증은 병렬로 진행하되 **PR 병합은 OS-F2 → DS-H → DS/DIDM → KEY5a 순서로 한 번에 하나**다. 각 차례마다 최신main을 반영하고 source-review 기준선은 마지막에 갱신한다.

승인 범위는 위 기존 인계의 독립 구현·수정·검증·PR 생성과, 필수 CI 및 독립 검토가 통과한 변경의 merge commit 병합이다. 새 사업 정책·실제 영업/결제·권리/법률 판정·외부 배포를 승인한 것으로 보지 않는다.

## 3. 승인 후 첫 실행 단위

1. OS-F2 로컬 수정안을 완결한다. 아래 재현된 경합과 marker/실제 writer 연결을 검토해 경로 계산의 부작용과 동결 엔진 불변 조건을 함께 지킨다. 해결되지 않은 항목을 숨긴 채 병합하지 않는다.
2. 최신main과 비교한 허용된 관련 회귀·code_sha256·준법 정합성을 검증한다. 전체 run_all/보호 연구 입력을 쓰지 않는다. code hash 변경은 기존 OS-F2 승인대로 이유와 새 값을 PR에 기록하고, owner_confirmed를 대신 쓰지 않는다.
3. OS-F2 PR을 만들고 CI/독립 검토 후 병합한다. 해당 완료 하위만 원장/Remaining Work에 기록한다.
4. 다음 차례 DS-H/DS-DIDM을 통합하는 동안 KEY5a 결함 수정·합성 회귀를 별도 브랜치에서 병렬 준비한다.
5. UI/웹 전달 요청과 소유자 질문을 한 목록으로 모은다. 해당 별도 세션을 직접 고치지 않는다.

## 4. 승인 요청 전 이미 한 일·현재 중단점

- 인계6문서·pipeline/workboard/merge queue·OS·PAYMENTS·DATA 원문과 최신refs를 확인하고 OS 배타 잠금 및 CURRENT CAS/read-back을 했다.
- OS-F2 독립 검토: migration이 목적지 경합 때 중첩 이동하고 marker 실패 때 legacy가 이미 사라지는 문제, 새 writer 경로가 이후 legacy 생성에 따라 바뀌는 문제, Windows POSIX mode 단정을 찾았다.
- OS-F2 두 파일의 **로컬 미커밋 초안**: no-replace native rename(Linux/macOS/Windows), marker를 이동 전에 작성, cross-filesystem/미지원은 copy-delete 없이 거절, Windows 권한 검사의 플랫폼 구분, 새 회귀2개. 수정 전 두 검사 실패(FAIL1/ERROR1), 수정 후 migration7개 Linux PASS. 전체 suite·Windows/macOS·writer 연결 완결은 미검증이다. 원격 코드 push/새 PR/main 변경 없음.
- KEY5a: 정확한 기존 함수 AST와 합성 adapter로 삭제키/off/company stale FMP3건과 KRX 갱신 중 fail-open1건을 재현했다. 기존 코드에서 회귀4개 실패. 제품 수정은 아직 없다.
- 사용자 승인안 요청에 따라 추가 구현을 중단했다. 로컬 수정과 근거는 private checkpoint에 보존했다. 이 문서는 승인 요청이며 승인 완료 기록이 아니다.
- 새 완료ID/취소선 없음. Notion 쓰기는 이번 실행에서 아직 하지 않았다. 민감 자료·계정 식별자는 이 문서에 포함하지 않는다.

## 5. 유지할 보호 범위와 별도 조건

- .env·실제 ~/.nextgen·보호cache의 내용/목록/검색/해시 금지; 실제 원장·tests/run_all·macro_m8/m9·qa 결과 재생성·owner_confirmed/host_fingerprint·태그 push 금지.
- 테스트는 합성 자료와 격리 임시 저장소. CI의 Windows 결과와 소유자 PC 실제 실행을 구분한다.
- UI/UX·웹사이트 세션은 소유자 경유. UI7쪽의 실제PC 확인 전 바인딩 전환과 KEY5 화면 연결을 무단 진행하지 않는다.
- 법인/규제/PG/법률·라이선스/데이터표시권, 실제 API/실연구 성능 근거를 문서/합성검증으로 대체하지 않는다.
- PAY0 문의 발송, PAY2 정책 확정, OA10 등 실제 미결정은 소유자 답을 받는다.
- 자동감시 예약/새 run_now/외부 릴리스·사이트 배포 없음. SESSION_PIPELINE의 업무 연결은 승인된 범위에서 적용한다.
