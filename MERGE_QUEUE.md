# MERGE_QUEUE — main 병합 순서와 동결 (메인 세션이 관리)

updated_at: 2026-11-20T00:45:00+09:00
전체 업무 체크리스트: `WORKBOARD.md` · 세션 연결 규칙: `SESSION_PIPELINE.md` (2026-11-20 소유자 지시)
coordinator: 메인 세션 (QUANTGEN/MAIN, https://claude.ai/code/session_01H6RrzMUzF8vwK8xkX977mB)
freeze: **OFF** — 2026-11-19T01:32:00+09:00 해제. 소유자 F22 완료 보고("F22까지 성공적으로 마무리했습니다."), main `6e077dc`(소유자 `--no-ff` 병합, 부모 `8e026ab`·`13f4dea`), 그 push의 Compliance success, PR #4 merged. (동결 기간: 2026-11-18T19:10:45+09:00 ~ 위 시각)

## 지금 순서

| # | 항목 | 브랜치·PR | 상태 | 병합 |
|---|---|---|---|---|
| 1 | ~~R3 outage 기록 (GPT)~~ | PR #122 | **병합 완료 main `f058145`** (11-17 23:1x KST) | 메인 |
| 2 | ~~UI 세션 PR (시장 메인·지표 결론부)~~ | PR #124 | **병합 완료 main `8e026ab`** (⑬-2/market-hub/main) | 메인 |
| 3 | ~~⑦-1 Step 10 마감 기록~~ | 연구 브랜치 | **완료 `efe5bb2`** (11-17 22:06 KST) | — |
| 4 | ~~P3: main → 연구 브랜치 병합, 소유자 F1~F22~~ | PR #4 | **완료** main `6e077dc` (⑦-2, 11-19 01:32 KST freeze 해제) | 소유자 F21 |
| 5 | ~~결정 기록 PR (11-17 소유자 답, 자진 보고)~~ | ⑦-1/rulings | **완료** `7c33955` | 메인 |

## F21 뒤 — 지금 순서 (2026-11-19 01:40 KST 메인이 정함; 준비된 것부터)

| # | 항목 | 브랜치·PR | 상태 |
|---|---|---|---|
| 1 | ~~⑦-2/a 병합 뒤 main 정리~~ | PR #126 | **병합 완료 main `56fe32a`** (2026-11-19 03:08 KST, CI 전부 녹색) |
| 2 | ~~OS 작은 PR~~ | PR #127 | **병합 완료 main `c28b1d7`** (2026-11-19 05:09 KST, CI 전부 녹색) |
| 3 | ~~KEY-2~~ | PR #128 | **병합 완료 main `3249af7`** (2026-11-19 10:40 KST). code_sha256 → `10c27010…` |
| 3b | ~~KEY-2/b~~ | PR #129 | **병합 완료 main `ca5da08`** (2026-11-19 12:18 KST) |
| 4 | ~~정책 문서 PR-1~~ | PR #130 | **병합 완료 main `edbe9f7`** (2026-11-19 15:03 KST). PR-2(계정 서비스 설명)는 AWS 풀·웹 계정 화면 뒤 |
| 4a | ~~CI 겹친 실행 자동 취소 + GH-1 기록~~ | PR #131 | **병합 완료 main `ab24dec`** (2026-11-19 16:58 KST) |
| 4b | ~~KEY-3 (게이트웨이)~~ | PR #132 | **병합 완료 main `9f76b07`** (2026-11-19 19:07 KST) |
| 4c | KEY-4 (core 26파일 90곳·main.py를 게이트웨이로, 동결 feed.py는 S4 예외, KEY-3 검토 잔여 9건) | PAYMENTS PR #133 @ `d6a1997` | **병합: PAYMENTS_ACCOUNT_KEYS**. 메인 검토 4회(1차 막힘 2 → 2차 앱 시작 회귀 → 3차 막힘 없음 → 표적 재확인 시험 전부 FIXED, 11-20 02:0x). **d6a1997 CI 녹색이면 메인이 merge commit** |
| 4d | 메인 문서 PR: CLAUDE.md(SESSION_PIPELINE·WORKBOARD 포인터, "법인 설립 완료" → handoff INCORPORATION_CHECKLIST.md), OWNER_RULINGS_LOG(11-19 계정 결정 3건: 비밀번호 특수문자, HTML 인증 메일, 이메일 MFA 유지) | 메인 | KEY-4 바로 뒤 (11-20 메인이 정함) |
| 4d' | KEY-4/a 계정 문서 고침 (ADMIN_GUIDE 6.1 두 번째 확인 정의, OWNER_STEPS T18 표·Reset password 시험 단계, 작은 것 F4–F9, 자체 시험 1줄) | PAYMENTS | KEY-4 뒤, 4d와 같은 자리(파일 안 겹침) |
| 5 | UI 7쪽 + PySide6 준비 | UI `claude/friendly-bardeen-r6xe8f` | 소유자 실행 확인 뒤 (UI 세션 브랜치는 아무도 고치지 않음) |
| 6 | PySide6 전환 (`pyqt6_to_pyside6 --apply` + `switch_day.py --apply`, 화면 문구 3곳은 UI 세션) | OS | 5 뒤 (OS 세션 제안 순서: UI PR → 전환) |
| 4e | KEY-5/a gateway 준비 3건 (data.kis_stream 입구, kis_workspace 순수 값 목록, QuoteFeed 하위 클래스 공용 모듈) | PAYMENTS | KEY-4·4d 뒤 (11-20 메인이 정함) |
| 7 | KEY-5 (화면 쪽 22파일/44곳 + quantgen_desktop/paper.py, 키·연결 화면) | PAYMENTS 요청문(handoff plans/2026-11-20/KEY5_UI_REQUEST.md) + UI 구현(소유자 경유) | 6 뒤 권장, 4e 뒤 |
| 8 | DS·DIDM | DS | 차례가 오면. UI 확인이 늦어지면 5보다 앞으로 당길지 메인이 정함 |
| 제안 | OS-F2 (~/.nextgen → user_data_dir, config.py 포함 → Nautilus 지문 바뀜) | OS | 11-20 브랜치 작업 배정. 자리는 메인이 정함. owner_confirmed 다시 쓰기는 이것 뒤 |
| 제안 | OS PySide6 간헐 종료 원인 기록 (`claude/os-pyside6-abort-20261119` @ `8262d6c`, 5파일) | OS | OS-F2 PR 또는 OS-F1 날 PR에 묶기 (메인이 정함) |
| 제안 | 정책 문서 PR-2 (계정 서비스 설명) | 메인/PAYMENTS | AWS 운영 풀 + 웹 계정 화면 뒤 |
| 미정 | GH-2 정리 PR (test_npu.py, mindmap/, launch.json, _backup/ 태그 뒤) | 메인 | 빈 자리에 |

한 번에 PR 하나만 main 병합 대기에 둡니다(모두 `docs/compliance/source-review.json`을 바꾸므로 앞 PR이 병합된 뒤 최신 main을 합치고 기준선을 다시 갱신).

아래 목록은 위 순서의 근거입니다.

### F21 뒤 (근거)

- ~~GH-1: CI 줄이기 / Windows 검사를 소유자 PC로 + 비공개 전환~~ — **닫힘 (2026-11-19 15:08 KST 소유자 "두번째꺼 (비용부담 없음)로 하겠습니다"): 공개 유지.** runtime-smoke 겹친 실행 자동 취소만 적용(PR #131), Windows 3버전 유지.
- OS 작은 PR(도구·`app_identity`·패키징 초안, 공유 파일 `core/app_paths.py`·`runtime-smoke.yml` 경로·`platform-build.yml`) — **F21 뒤 첫 자리**, 그다음 OS: PySide6 전환 PR (D9 나안). P3 전에는 받지 않음: P3 병합 후보(`local/p3-candidate` 끝 `f0c8872`)가 main `7c33955` 기준이라 main이 바뀌면 병합과 전체 검사를 다시 해야 함. `qa/` 두 파일을 휠에 넣을지는 지금 그대로 두고 그 PR에서 근거와 함께 제안.
- P3 상태 (2026-11-18): 병합·전체 검사 끝, push 보류 — 코드 지문 판정(P3-가/나/다) 소유자 답 대기.
- 정책 문서 PR (메인, D11 소유자 답 Q1~Q3 반영) — F21 뒤 앞쪽. 소유자 원문(2026-11-19 00:19 KST, PAYMENTS 세션; 메인이 그 세션 대화 기록에서 확인): "Q1 답변 : 예, 다만 제가 법인 설립 설립이 완료되었다고 여기에 말하는 순간 바로 해당 법인 명으로 수정 가능하도록 해주세요 / Q2 답변 : 일단 contact@quantgeneration.com으로 하겠습니다. 현재 웹사이트의 구조도 이렇게 되어있습니다. / Q3 답변 : 예". 값: 브랜치 `claude/payments-keys-20261117` @ `687bf65` `docs/commercial/accounts/ACCOUNT_SETUP.md` 4부 (운영자 개인·"(주)" 없음, 책임자 같은 사람, 메일 contact@quantgeneration.com, 최소 연령 14/유료 19). 대상 문서 01·02·04·06·07·08·16·17·18·20, release-profile.json.
- KEY-2 → KEY-3 → KEY-4 → KEY-5 — **D7-G 소유자 승인됨 (2026-11-18 14:15 KST, OS 세션에서, 원문: "그러면 D7-G의 방식대로 진행하겠습니다")**. 브랜치 작업은 지금 시작 가능, main 병합은 F21 뒤 이 순서.
- DS·DIDM PR — 각 세션 차례가 오면.

## 규칙

- 하부 세션은 자기 항목이 이 표의 맨 앞이거나 메인이 "병합: <세션>"이라고 적었을 때만 PR을 엽니다 (GitHub는 공개 유지 — 2026-11-19 소유자 GH-1 결정. 그래도 PR 하나씩: 모두 `docs/compliance/source-review.json`을 바꾸므로).
- 병합 버튼은 메인이 누릅니다 (CI 통과 시, merge commit).
- UI/UX 세션과 웹사이트 세션의 브랜치·인계 파일은 아무도 고치지 않습니다. 그 세션에 줄 요청은 소유자를 거칩니다.
- **owner_confirmed 다시 쓰기 (2026-11-19 메인이 정함):** 다음 Nautilus 기록 실행 직전에 한 번만(OS-F2가 config.py를 또 바꾸므로 지금은 하지 않음). 소유자가 최신 main 클론의 보통 앱 Python으로 `python -B -m tools.nautilus.runner --fingerprint --table <두 표>`(읽기만) → 각 표의 "owner_confirmed" 한 줄만 출력된 form으로(UTF-8, BOM 없음; host_fingerprint는 같으면 그대로) → 브랜치 `owner/nautilus-confirm-<YYYYMMDD>` + PR(main 직접 push 금지) → 메인이 Linux에서 code_sha256 재계산해 대조, CI 녹색이면 병합. 그날 이 표에 자리를 둠. Claude는 이 줄을 쓰지 않음.
- **코드 지문 주의 (2026-11-18):** `config.py`는 Nautilus 브리지 code_sha256의 입력입니다. P3-가(소유자 11-18 "1번 : (가) 승인")로 지문은 ec72fab3…가 되고, F21 뒤 KEY-2(`config.py` 변경)가 들어가면 또 바뀝니다. 그런 PR은 본문에 이 사실을 적고, 다음 기록 실행 전에 소유자가 owner_confirmed 두 줄을 새로 씁니다(Claude는 쓰지 않음).
