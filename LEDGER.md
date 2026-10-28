# 완료 기록 (LEDGER)

Claude와 GPT가 끝낸 작업을 한 줄씩 쌓는 기록입니다. 같은 작업을 두 번 하지 않기 위한 장부입니다.

- **지우거나 고치지 않습니다.** 맨 아래에 행을 덧붙이기만 합니다.
- **작업을 시작하기 전에** 이 표에서 작업 ID와 바뀐 파일을 찾아봅니다. 이미 있는 ID는 다시 하지 않습니다.
  사용자가 그 일을 더 해 달라고 하면 `③-3/2`처럼 새 ID를 붙입니다.
- **작업 ID**는 `docs/nautilus_bridge/REMAINING_WORK_*.md`(최신 날짜)의 순서 표기(`③-1`, `⑨-3a` 등)를 씁니다.
  한 항목을 나눠서 끝냈다면 `③-2/a`, `③-2/b`처럼 붙입니다.
- **주기**는 사용량이 다시 채워진 화요일 17:00(KST)의 날짜입니다. 예: `2026-10-27`은
  2026-10-27 17:00부터 2026-11-03 17:00 전까지입니다.
- **커밋**은 원격(GitHub)에 push된 커밋이어야 합니다.
- Claude는 `tools/handoff/push_handoff.py --done "id | 한 일 | 바뀐 파일 | 커밋 | 확인 방법과 결과"`로
  행을 추가합니다. 스크립트가 시각, 주기, 누가를 채우고, 이미 있는 ID나 push 안 된 커밋은 거부합니다.
  GPT는 같은 형식으로 직접 한 줄을 덧붙입니다.
- 이 기록이 생기기 전에 끝난 일은 로드맵 문서와 `main`의 git 기록을 봅니다.

| id | 완료 시각 (KST) | 주기 | 누가 | 한 일 | 바뀐 파일 | 커밋 | 확인 방법과 결과 |
|---|---|---|---|---|---|---|---|
| ①-2 | 2026-10-29T02:56:18+09:00 | 2026-10-27 | claude | 2027년 KRX·NYSE·FED·SIFMA 휴장일 감사 후 소유자 서명(Geon Koh, 2026-10-28T06:35:52Z), PR #7로 main 병합(98ccae6) | core/calendars/data/holidays_KRX.yaml, holidays_NYSE.yaml, holidays_FED.yaml, holidays_SIFMA.yaml, MANIFEST.yaml, tests/macro_m1_calendars.py, docs/audit/2026-10-27/01~03 | 3917bc0 | python -m tests.macro_m1_calendars 18/22 통과·실패 0·미실행 4, test_cal02_2027_files_signed_before_2026_11_01 PASS (2026-10-29 재실행) |
