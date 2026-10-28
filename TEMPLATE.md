---
status: checkpoint            # idle | checkpoint | handoff | taken | returned
reason: milestone             # milestone | usage_limit_weekly | usage_limit_5h | session_end | manual | stale
from: claude                  # 마지막으로 이 문서를 쓴 에이전트: claude | gpt
task: <작업명-영문-소문자>     # 예: t-cal-02-calendar-audit
updated_at: <YYYY-MM-DDTHH:MM:SS+09:00>
stale_after_hours: 3          # 이 시간 넘게 갱신이 없으면 말없이 끊긴 것으로 봄
waiting_on: none              # none | owner | ci | review
work_branch: <claude/... 또는 gpt/...>
work_commit: <작업 브랜치의 마지막 커밋 해시 7자리. 원격에 push된 커밋이어야 함>
uncommitted_changes: no       # yes면 5절에 무엇이 커밋되지 않았는지 적음
pr: none                      # PR 번호 또는 none
usage_weekly_pct: unknown     # 기록 시점의 주간 사용량(%) 또는 unknown
usage_5h_pct: unknown         # 기록 시점의 5시간 사용량(%) 또는 unknown
usage_resets_at: unknown      # 한도가 풀리는 시각 또는 unknown
session: <Claude 세션 링크 또는 GPT 대화 식별자>
---

# 인수인계: <작업 제목>

## 0. 한 줄 요약

<지금 어디까지 왔고, 다음 사람이 가장 먼저 할 일은 무엇인지 한두 문장으로.>

## 1. 목표와 완료 조건

- **사용자 요청 (원문 그대로):**
  > <사용자가 한 말을 고치지 말고 그대로 인용>
- **완료 조건:** <무엇이 되면 끝인지. 확인할 수 있는 형태로.>
- **범위 밖:** <이번 작업에서 하지 않기로 한 것>

## 2. 근거

무엇을 근거로 작업하고 있었는지 적습니다. 다음 사람이 같은 자료를 열어볼 수 있게 경로를 정확히 씁니다.

| 종류 | 위치 | 이 작업에서 쓰는 부분 |
|---|---|---|
| 매뉴얼/스펙 | `<repo 내 경로>` | <섹션, 규칙 번호> |
| 사용자 결정 | `<결정 기록 파일 경로>` 또는 <날짜, 원문> | <무엇을 결정했는지> |
| 외부 자료 | <URL> | <무엇을 확인했는지> |

## 3. 판단 기록

| 결정 | 이유 | 버린 대안과 이유 |
|---|---|---|
| <무엇을 하기로 했나> | <왜> | <다른 선택지와 버린 이유> |

## 4. 진행 상황

- [x] <끝난 일> — 근거 커밋 `<해시>`
- [ ] <진행 중인 일> ← **여기서 멈춤**
- [ ] <남은 일>

**마지막으로 통과한 검증:**

```
<명령>
<결과 요약: 예) 37 passed>
```

## 5. 중단 지점

<정확히 어떤 파일, 함수, 명령을 하다가 멈췄는지. 커밋되지 않은 변경이 있으면 파일 목록과 내용 요약. 실패 중인 테스트가 있으면 이름과 에러 메시지.>

## 6. 다음 할 일 (순서대로)

1. <구체적인 첫 단계. 실행할 명령이 있으면 그대로 적음>
2. <두 번째 단계>
3. <세 번째 단계>

## 7. 주의사항 / 하지 말 것

- <사용자 승인 없이 하면 안 되는 것>
- <건드리면 안 되는 파일이나 데이터>
- <이미 시도했다가 실패한 방법과 실패 이유>

## 8. 사용자에게 물어야 할 것

- <답을 받아야 진행할 수 있는 질문. 없으면 "없음">

## 9. 이어받는 에이전트에게 주는 지시문

아래 블록을 그대로 첫 지시로 사용합니다. 이 문서를 쓴 에이전트가 직접 작성합니다.

```
너는 xkg4real/quantgen 레포의 "<작업 제목>" 작업을 이어받는다.
1. handoff 브랜치의 CURRENT.md와 AGENTS.md를 먼저 읽어라.
2. CURRENT.md의 status를 taken으로, from을 gpt로 바꾸고 updated_at을 갱신해 handoff 브랜치에 push해라.
3. AGENTS.md 2절 4번에 따라 시작 지점을 정해 gpt/<task> 브랜치를 만들어 작업해라. 보통은 <work_branch>의 <work_commit>이다.
4. <이 작업에 필요한 구체적 지시>
5. 작업 단위가 끝날 때마다 CURRENT.md를 같은 양식으로 갱신해라. 끝나거나 멈출 때는 status를 returned로 바꿔라.
```

## 10. 결과 확인 방법

```
<작업이 맞게 됐는지 확인하는 명령과 기대 결과>
```
