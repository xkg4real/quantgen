# MERGE_QUEUE — main 병합 순서와 동결 (메인 세션이 관리)

updated_at: 2026-11-17T21:56:00+09:00
coordinator: 메인 세션 (QUANTGEN/MAIN, https://claude.ai/code/session_01H6RrzMUzF8vwK8xkX977mB)
freeze: none — F 동결은 P3(연구 브랜치 병합)이 시작될 때 켜지고 F21까지 유지. 동결 중에는 main에 아무것도 병합하지 않음.

## 지금 순서

| # | 항목 | 브랜치·PR | 상태 | 병합 |
|---|---|---|---|---|
| 1 | R3 outage 기록 (GPT) | PR #122 `gpt/r3-outage-20261114` | main `5888d05` 병합본 `994e9f9`에서 전체 CI 대기 | 메인 |
| 2 | UI 세션 PR (시장 메인·지표 결론부) | `claude/friendly-bardeen-r6xe8f` | 소유자가 PNG를 PR #122 병합 전에 승인하면 P3 바로 앞(D2-A), 아니면 F21 뒤 | 메인 |
| 3 | ⑦-1 Step 10 마감 기록 | 연구 브랜치 `claude/amazing-gauss-tdiguu` | 작성·검증 중 (연구 브랜치 커밋, main 병합 아님) | — |
| 4 | P3: main → 연구 브랜치 병합, 소유자 F1~F22 | PR #4 | ⑦-1 뒤. **여기서 freeze 시작** | 소유자 F21 |
| 5 | 결정 기록 PR (11-17 소유자 답, 자진 보고) | 메인이 만듦 | PR #122 뒤, P3 앞 | 메인 |

## F21 뒤 (순서는 메인이 다시 정함)

- GH-1: CI 줄이기 / Windows 검사를 소유자 PC로 + 비공개 전환 — 소유자 선택 대기 (D5 후속).
- OS: PySide6 전환 PR — F21 바로 뒤 첫 자리 (D9 나안). 준비 작업은 지금 브랜치에서.
- KEY-2 → KEY-3 → KEY-4 → KEY-5 — **D7-G 소유자 승인 뒤에만**.
- DS·DIDM PR — 각 세션 차례가 오면.

## 규칙

- 하부 세션은 자기 항목이 이 표의 맨 앞이거나 메인이 "병합: <세션>"이라고 적었을 때만 PR을 엽니다 (비공개 전환 뒤 CI는 유료).
- 병합 버튼은 메인이 누릅니다 (CI 통과 시, merge commit).
- UI/UX 세션과 웹사이트 세션의 브랜치·인계 파일은 아무도 고치지 않습니다. 그 세션에 줄 요청은 소유자를 거칩니다.
