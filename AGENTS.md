# 이어받는 에이전트(GPT 등)를 위한 규칙

이 파일은 `xkg4real/quantgen` 레포의 `handoff` 브랜치를 읽는 에이전트가 따를 규칙입니다.
상태값과 파일 구성은 `README.md`에 있습니다.

## 1. 확인할 때

1. `handoff` 브랜치의 `CURRENT.md`를 읽습니다.
2. 맨 위 `status:`를 보고 아래 표대로 행동합니다.

| 조건 | 행동 |
|---|---|
| `status: handoff` | 이어받습니다 (2절). |
| `status: checkpoint`, `waiting_on: none`, `updated_at`이 `stale_after_hours`보다 오래됨 | Claude가 말없이 끊긴 것으로 보고 이어받습니다. `reason: stale`로 적습니다. |
| `status: checkpoint` (위 조건이 아님) | 아무것도 하지 않습니다. |
| `status: taken`, `from:`이 내가 아님 | 다른 에이전트가 작업 중이므로 아무것도 하지 않습니다. |
| `status: idle` 또는 `returned` | 아무것도 하지 않습니다. |

## 2. 이어받을 때

1. **먼저 잠급니다.** `CURRENT.md`의 `status`를 `taken`, `from`을 `gpt`로 바꾸고
   `updated_at`을 지금 시각으로 고쳐 `handoff` 브랜치에 커밋하고 push합니다.
   커밋 메시지: `handoff: taken <task>`. push가 거절되면(다른 쪽이 먼저 바꿨다면)
   최신 `CURRENT.md`를 다시 읽고 1절부터 다시 판단합니다.
2. `CURRENT.md` 9절의 지시문을 첫 지시로 삼고 0~8절을 모두 읽습니다.
3. 2절 "근거"에 적힌 파일을 직접 엽니다. 문서의 요약만 믿지 말고 원문을 확인합니다.
4. `work_branch`의 `work_commit`에서 `gpt/<task>` 브랜치를 새로 만들어 작업합니다.
   Claude의 작업 브랜치와 `main`에는 직접 push하지 않습니다.

## 3. 작업하는 동안

- 작업 단위(테스트 통과, 파일 하나 완성 등)가 끝날 때마다 `CURRENT.md`를 같은 양식으로
  갱신해 push합니다. `status: taken`은 유지하고 `work_branch`, `work_commit`,
  4~6절을 고칩니다.
- 사용자 승인이 필요한 일(7절, 8절)은 하지 말고 8절에 질문으로 남깁니다.

## 4. 끝내거나 멈출 때

- `status`를 `returned`로 바꾸고, 무엇을 했고 무엇이 남았는지 0절과 4~6절에 적습니다.
- 9절 지시문을 Claude가 이어받을 수 있게 다시 씁니다.

## 5. 이 레포에서 지킬 것

- 이 레포의 규칙 문서(`README.md`, `docs/` 아래 스펙, 사용자 결정 기록)가 이 파일보다
  우선합니다.
- 이 레포는 실제 주문 경로가 없는 연구용 앱입니다. 브로커 주문 코드를 추가하지 않습니다.
- 비밀 값(API 키, 토큰, 계좌번호)은 커밋하지 않고 문서에도 적지 않습니다.
