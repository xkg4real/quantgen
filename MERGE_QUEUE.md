# MERGE_QUEUE — main 병합 순서와 동결 (메인 세션이 관리)

updated_at: 2026-11-19T01:32:00+09:00
coordinator: 메인 세션 (QUANTGEN/MAIN, https://claude.ai/code/session_01H6RrzMUzF8vwK8xkX977mB)
freeze: **OFF** — 2026-11-19T01:32:00+09:00 해제. 소유자 F22 완료 보고("F22까지 성공적으로 마무리했습니다."), main `6e077dc`(소유자 `--no-ff` 병합, 부모 `8e026ab`·`13f4dea`), 그 push의 Compliance success, PR #4 merged. (동결 기간: 2026-11-18T19:10:45+09:00 ~ 위 시각)

## 지금 순서

| # | 항목 | 브랜치·PR | 상태 | 병합 |
|---|---|---|---|---|
| 1 | ~~R3 outage 기록 (GPT)~~ | PR #122 | **병합 완료 main `f058145`** (11-17 23:1x KST) | 메인 |
| 2 | UI 세션 PR (시장 메인·지표 결론부) | `claude/friendly-bardeen-r6xe8f` | PR #122 병합 전 PNG 승인이 없어 원칙상 F21 뒤(D2-A). 소유자가 P3 시작 전에 승인하면 P3 앞에 넣을 수 있음 | 메인 |
| 3 | ~~⑦-1 Step 10 마감 기록~~ | 연구 브랜치 | **완료 `efe5bb2`** (11-17 22:06 KST) | — |
| 4 | P3: main → 연구 브랜치 병합, 소유자 F1~F22 | PR #4 | ⑦-1 뒤. **여기서 freeze 시작** | 소유자 F21 |
| 5 | 결정 기록 PR (11-17 소유자 답, 자진 보고) | 메인이 만듦 | **다음** (P3 앞) | 메인 |

## F21 뒤 — 지금 순서 (2026-11-19 메인이 정함)

| # | 항목 | 브랜치·PR | 상태 |
|---|---|---|---|
| 1 | ⑦-2/a 병합 뒤 main 정리 (README 시험 표·bonds 행, `qa/research_status.json`, 준법 기준선, 확인 문장 복사, 자진 보고) | 메인이 만듦 | **지금 진행** |
| 2 | 정책 문서 PR (D11 Q1~Q3) | 메인이 만듦 | ⑦-2/a 다음 |
| 3 | OS 작은 PR | OS 세션 | 메인이 "병합: OS"라고 적으면 PR 열기 |
| 4 | OS PySide6 전환 PR | OS 세션 | 3 다음 |
| 5 | UI 7쪽 + PySide6 준비 (`claude/friendly-bardeen-r6xe8f`) | UI 세션 | 소유자 실행 확인 뒤 |
| 6 | KEY-2 → KEY-3 → KEY-4 → KEY-5 | PAYMENTS 세션 | PR 본문에 코드 지문 이동 적기 |
| 7 | DS·DIDM | DS 세션 | 차례가 오면 |

아래 목록은 위 순서의 근거입니다.

### F21 뒤 (근거)

- GH-1: CI 줄이기 / Windows 검사를 소유자 PC로 + 비공개 전환 — 소유자 선택 대기 (D5 후속).
- OS 작은 PR(도구·`app_identity`·패키징 초안, 공유 파일 `core/app_paths.py`·`runtime-smoke.yml` 경로·`platform-build.yml`) — **F21 뒤 첫 자리**, 그다음 OS: PySide6 전환 PR (D9 나안). P3 전에는 받지 않음: P3 병합 후보(`local/p3-candidate` 끝 `f0c8872`)가 main `7c33955` 기준이라 main이 바뀌면 병합과 전체 검사를 다시 해야 함. `qa/` 두 파일을 휠에 넣을지는 지금 그대로 두고 그 PR에서 근거와 함께 제안.
- P3 상태 (2026-11-18): 병합·전체 검사 끝, push 보류 — 코드 지문 판정(P3-가/나/다) 소유자 답 대기.
- 정책 문서 PR (메인, D11 소유자 답 Q1~Q3 반영) — F21 뒤 앞쪽. 소유자 원문(2026-11-19 00:19 KST, PAYMENTS 세션; 메인이 그 세션 대화 기록에서 확인): "Q1 답변 : 예, 다만 제가 법인 설립 설립이 완료되었다고 여기에 말하는 순간 바로 해당 법인 명으로 수정 가능하도록 해주세요 / Q2 답변 : 일단 contact@quantgeneration.com으로 하겠습니다. 현재 웹사이트의 구조도 이렇게 되어있습니다. / Q3 답변 : 예". 값: 브랜치 `claude/payments-keys-20261117` @ `687bf65` `docs/commercial/accounts/ACCOUNT_SETUP.md` 4부 (운영자 개인·"(주)" 없음, 책임자 같은 사람, 메일 contact@quantgeneration.com, 최소 연령 14/유료 19). 대상 문서 01·02·04·06·07·08·16·17·18·20, release-profile.json.
- KEY-2 → KEY-3 → KEY-4 → KEY-5 — **D7-G 소유자 승인됨 (2026-11-18 14:15 KST, OS 세션에서, 원문: "그러면 D7-G의 방식대로 진행하겠습니다")**. 브랜치 작업은 지금 시작 가능, main 병합은 F21 뒤 이 순서.
- DS·DIDM PR — 각 세션 차례가 오면.

## 규칙

- 하부 세션은 자기 항목이 이 표의 맨 앞이거나 메인이 "병합: <세션>"이라고 적었을 때만 PR을 엽니다 (비공개 전환 뒤 CI는 유료).
- 병합 버튼은 메인이 누릅니다 (CI 통과 시, merge commit).
- UI/UX 세션과 웹사이트 세션의 브랜치·인계 파일은 아무도 고치지 않습니다. 그 세션에 줄 요청은 소유자를 거칩니다.
- **코드 지문 주의 (2026-11-18):** `config.py`는 Nautilus 브리지 code_sha256의 입력입니다. P3-가(소유자 11-18 "1번 : (가) 승인")로 지문은 ec72fab3…가 되고, F21 뒤 KEY-2(`config.py` 변경)가 들어가면 또 바뀝니다. 그런 PR은 본문에 이 사실을 적고, 다음 기록 실행 전에 소유자가 owner_confirmed 두 줄을 새로 씁니다(Claude는 쓰지 않음).
