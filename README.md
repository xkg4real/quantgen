# QUANTGEN 인수인계 브랜치 (`handoff`)

이 브랜치에는 코드가 없습니다. 작업 중인 에이전트(주로 Claude)가 지금 상태를 여기에
기록하고, 그 에이전트가 멈추면 다른 에이전트(주로 GPT)가 이 기록을 읽고 이어서
작업합니다. 코드 작업은 각자의 작업 브랜치에서 하고, 이 브랜치에는 인수인계 문서만
올립니다. 그래서 `main`에 PR을 합칠 필요 없이 바로 push할 수 있습니다.

## 파일

| 파일 | 역할 | 쓰는 쪽 |
|---|---|---|
| `CURRENT.md` | 지금 진행 중인 작업의 최신 인수인계 문서. 항상 하나만 둡니다. | 지금 작업을 맡은 에이전트 |
| `TEMPLATE.md` | `CURRENT.md`의 양식 | 양식을 바꿀 때만 수정 |
| `AGENTS.md` | GPT(와 다른 에이전트)가 이 브랜치를 읽는 규칙 | 사람 |
| `LEDGER.md` | 끝낸 작업을 한 줄씩 쌓는 완료 기록. 지우거나 고치지 않고 덧붙이기만 합니다. 같은 작업을 두 번 하지 않게 하는 기준입니다. | 작업을 끝낸 에이전트 |
| `archive/` | 끝났거나 새 작업으로 교체된 인수인계 문서 보관 | 교체하는 에이전트 |
| `AUTO_STATE.md` | 스크립트가 모델 없이 만든 git 상태 스냅샷(브랜치, 커밋, 커밋 안 된 변경, 마지막 메시지). 사용량 한도 직전, 한도 오류로 턴이 실패했을 때, 작업 중 주기적으로(30분 간격, 상태가 바뀐 경우만) 갱신합니다. `CURRENT.md`의 `work_branch`에서 작업하는 세션만 갱신합니다. | `tools/handoff/auto_snapshot.py` |
| `AUTO_STATE.patch` | `patch_base`(원격에 있는 커밋)부터 스냅샷 시점의 작업 트리까지의 diff. 푸시 안 된 커밋과 커밋 안 된 변경(추적 중인 파일만)이 함께 들어 있습니다. | 같은 스크립트 |

## 상태값

`CURRENT.md` 맨 위 `status:` 한 줄이 누가 무엇을 해야 하는지 정합니다.

| `status` | 의미 | 읽는 쪽이 할 일 |
|---|---|---|
| `idle` | 진행 중인 작업 없음 | 없음 |
| `checkpoint` | Claude가 작업 중이고, 작업 단위가 끝날 때마다 중간 저장함 | 읽기만 합니다. 단, 아래 "말없이 끊긴 경우"에 해당하면 이어받습니다. |
| `handoff` | Claude가 멈춤(사용량 한도, 세션 종료 등). 다른 에이전트가 이어받아야 함 | 바로 이어받습니다. |
| `taken` | 다른 에이전트가 이어받아 작업 중 (잠금) | Claude는 끼어들지 않고 `returned`를 기다리거나 사용자에게 묻습니다. |
| `returned` | 이어받은 에이전트가 일을 끝냈거나 멈추고 돌려줌 | Claude가 다음 세션 시작 때 읽고 이어갑니다. |

**말없이 끊긴 경우:** `status: checkpoint`, `waiting_on: none`인데 `CURRENT.md`의
`updated_at`과 `AUTO_STATE.md`의 `created_at`이 둘 다 `stale_after_hours`보다 오래
갱신되지 않았다면, Claude가 인수인계를 쓰지 못하고 끊긴 것으로 봅니다.
이때는 `handoff`와 똑같이 이어받고, `reason: stale`로 기록합니다.
`waiting_on`이 `owner`, `ci`, `review`이면 Claude가 무언가를 기다리는 중이므로
이어받지 않습니다. 스냅샷은 git 상태가 바뀔 때만 올라가므로, Claude는 파일을 바꾸지 않는
긴 작업 전에 checkpoint를 올리거나 `waiting_on`을 적습니다.

`AUTO_STATE.md`의 `reason: rate_limit_error`는 한도에 걸렸을 가능성이 높다는 신호입니다.
하지만 서비스가 일시적으로 바빠서 생긴 오류일 수도 있으므로, 이것만으로 이어받지는 않습니다.

## 주간 일정 (사용자가 정한 것)

| 시점 (KST) | 일 |
|---|---|
| 화요일 17:00 | Claude 사용량이 다시 채워짐. Claude는 **새 작업 전에** `CURRENT.md`(GPT가 `returned`로 돌려준 문서)와 `LEDGER.md`를 읽고, GPT가 어디까지 했는지 확인한 뒤 이어갑니다. |
| 주중 | Claude가 작업 단위마다 checkpoint를 올리고, 끝낸 일을 `LEDGER.md`에 기록합니다. |
| 주간 사용량 98% | Claude가 `status: handoff` 문서를 올립니다. |
| 목요일 00:00부터 1시간 간격 | GPT가 `CURRENT.md`를 확인합니다. `handoff`를 발견하면 확인을 멈추고 작업합니다. |
| 다음 화요일 17:00 전 | GPT가 끝낸 일을 `LEDGER.md`에 기록하고, `status: returned`로 돌려줍니다. 일이 남았어도 진행 상황을 적어 돌려줍니다. |

한 번에 한 작업만 진행합니다. 앞 작업이 끝나야 다음 작업을 시작합니다.

## 작업 ID와 완료 기록

- 작업 ID는 `docs/nautilus_bridge/REMAINING_WORK_*.md`(최신 날짜)의 순서 표기(`③-1`, `③-2` 등)를 씁니다.
  한 항목을 나눠서 끝내면 `③-2/a`, `③-2/b`처럼 씁니다.
- `CURRENT.md`의 `done_ids`에는 끝낸 ID, `next_ids`에는 남은 ID를 적습니다. `next_ids`에는
  `LEDGER.md`에 이미 있는 ID를 넣지 않습니다.
- 작업을 시작하기 전에 `LEDGER.md`에서 그 ID와 바뀐 파일을 찾아봅니다. 이미 있으면 다시 하지 않습니다.

## 흐름

```
Claude 작업 중 ── 작업 단위마다 ──▶ CURRENT.md (status: checkpoint)
      │
      ├─ 사용량 98% 도달 / 세션 끝 ──▶ CURRENT.md (status: handoff)
      │
      └─ 말없이 끊김 ──────────────▶ checkpoint가 오래됨 → stale로 간주

GPT ── 이 브랜치 확인 ──▶ handoff 또는 stale 발견
      ──▶ status: taken 으로 잠금 → gpt/<작업명> 브랜치에서 이어서 작업
      ──▶ 작업 중에도 CURRENT.md 갱신 → 끝나면 status: returned

Claude 복귀 ──▶ CURRENT.md와 LEDGER.md 읽기 → returned면 GPT가 한 일을 확인하고 이어받기,
              taken이면 기다리거나 사용자에게 확인
```

## 규칙 요약

- `CURRENT.md`는 덮어쓰기 방식입니다. 이전 내용은 git 기록에 남습니다. 새 작업으로
  바꿀 때만 기존 문서를 `archive/YYYY-MM-DD-HHMM-<작업명>.md`로 옮깁니다.
- 시각은 모두 한국 시간(+09:00)의 ISO 8601로 적습니다. 예: `2026-10-28T21:30:00+09:00`
- 비밀 값(API 키, 토큰, 계좌번호)은 절대 적지 않습니다. `.env`의 변수 이름만 적습니다.
- 커밋 메시지는 `handoff: <status> <작업명>` 형식으로 씁니다.
- 앞부분(front matter)은 `key: value` 한 줄씩 씁니다. 값에 따옴표를 붙이거나 줄을 들여쓰지
  않습니다. 읽을 수 없는 `CURRENT.md`는 잠긴 것으로 취급되어, 다른 에이전트가 손대지 못합니다.
