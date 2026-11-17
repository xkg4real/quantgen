---
status: checkpoint
reason: milestone
from: claude
task: data-source-didm
cycle: 2026-11-17
done_ids: none
next_ids: DS-1, DIDM-0, DIDM-1, DS-4a, DS-H, DS-4b
updated_at: 2026-11-17T22:12:00+09:00
stale_after_hours: 3
waiting_on: owner
work_branch: claude/data-source-didm-20261117
work_commit: 73f2868
uncommitted_changes: no
pr: none
usage_weekly_pct: unknown
usage_5h_pct: unknown
usage_resets_at: 2026-11-24T17:00:00+09:00
session: https://claude.ai/code/session_016uB1jiXnUcWg99JHtRek9T
---

# 인수인계: QUANTGEN/MAIN -> DATA_SOURCE_DIDM

운영 기준: [자동감시 취소·수동 인계](OWNER_HANDOFF_POLICY_2026-11-13.md). 다음 담당은 소유자가 이 인계를 읽고 이어받으라고 할 때만 진행합니다.

## 0. 한 줄 요약

첫 작업 3개 (DS-1 평가표, DIDM-0 사전등록·DIDM-1 스키마, DS-4a GDELT·ALFRED 커넥터 + 시점 저장소)를 작업 브랜치 `claude/data-source-didm-20261117` (`73f2868`)에 커밋·push했습니다. main 미병합, PR 없음. **소유자 답 대기**: 평가표 확인 2문항, 사전등록 P1~P5, 지시문 질문 1~4, 홈 지표 진단 출력.

## 1. 목표와 완료 조건

- **사용자 요청 (원문 그대로, 2026-11-17 `owner_answer_1117.txt`):**
  > 5. D14 : Ravenpack의 대안책 3단계 (엑셀 파일 참고)의 자료들로 구성할 예정.
  > 1. D6 : 현재 메인세션의 하부 세션 (QUANTGEN/TRADEGEN -> TRADEGEN_GITHUB 과 같은 구조)으로 3가지를 생성할 것. 이때 이미 돌아가고 있는 UI/UX 수정 세션 등은 건들지 말 것.
- **2026-11-16 Notion 요청 (원문):**
  > DIDM에서 제공해주는 정보가 어디 정보에 포함되는 건지, 어떤 range를 가지는지에 따라 이에 보완책이 되는 정보 제공 source 찾고 연결하기
  > 메인화면 아직도 리서치 홈에서 지표가 안뜨는데, 이거 고칠 것. 주요 지표 6개를 그래프와 함께 구현하도록(앱 키자마자 실시간) 해야함.
- **완료 조건:** 지시문 `plans/2026-11-17/sessions/06_DATA_SOURCE_DIDM.md` 7절 (작업 1~3), 8절 표.
- **범위 밖:** 앱 화면 (UI 세션), 웹사이트, 키 저장소·게이트웨이 코어 (결제·계정 세션), 유료 호출·가입, Polymarket 실행, main 병합 (메인).

## 2. 근거

| 종류 | 위치 | 쓴 부분 |
|---|---|---|
| 지시문 | handoff `plans/2026-11-17/sessions/06_DATA_SOURCE_DIDM.md` | 전체 |
| 메인 분석 | handoff `plans/2026-11-17/D14_RAVENPACK_ALTERNATIVES.md` | 0~13절 |
| 게이트웨이 규칙 | handoff `plans/2026-11-17/D7_ENV_STRUCTURE.md` | 5.2~5.5 (공급사 HTTP는 `data/`, core는 주입 함수) |
| 소유자 엑셀 사본 | handoff `plans/2026-11-17/OWNER_EXCEL_RAVENPACK_ALTERNATIVES.txt` | 두 O/X/? 줄, 칸 메모 F4~X4 |
| Notion DIDM | `02e5c916fe0c821bb15701f648e9db87` (2026-11-17 읽음) | TL;DR, 2, 5.1~5.6, 6.1~6.3, 8.2~8.3, 9, 10.1~10.5 |
| 병합 순서 | handoff `MERGE_QUEUE.md` (2026-11-17 21:56) | `freeze: none`; DS·DIDM PR은 F21 뒤 "각 세션 차례" |

## 3. 판단 기록

| 결정 | 이유 | 버린 대안 |
|---|---|---|
| 평가표: 엑셀 두 줄은 그대로, 대안 9×19는 메모로 풀어 칸마다 근거 기호 | 엑셀에는 대안별 O/X/?가 없음 (두 줄뿐). 지시문은 "9개 × 19개를 그대로" — 그대로 옮길 대안별 값이 없어서 메모에서 풀고, 엑셀 두 줄과 모순 없음을 스크립트로 확인 | 대안별 값을 공개 자료로 새로 판정 (엑셀 기준이 아니게 됨) |
| 자체 NLP는 메모에 이름이 있는 칸 (I, L)만 O, 직접 계산 항목은 X (`N4규칙`) | 엑셀 N·W열이 "자체 구현"을 "제공 안 함 X"로 셈. 그래야 엑셀 X칸과 모순 없음 | 자체 NLP를 계산 가능한 모든 칸 O (엑셀 N열 X와 모순) |
| 사건 유형 12개 + none (무역·관세+공급망, 인수합병+경영진 합침) | Notion DIDM 5.1 "K ≤ 12 in V0". 지시문 출발안은 14개 → 소유자 질문 P1 | 14개 그대로 (DIDM 5.1과 다름) |
| 스키마는 표준 라이브러리만 | `requirements.txt`에 pydantic·jsonschema 없음. 공유 파일 변경을 줄임 | pydantic 추가 (대기열 공유 파일 PR 필요) |
| 시점 저장소 = sqlite 추가 전용, `as_of`는 `received_at ≤ t`의 최신판 | DIDM 10.3 bitemporal, "같은 as of = 같은 답" | 파일별 JSON (질의·중복 처리 어려움) |
| GDELT·ALFRED HTTP는 `data/didm/`, `core/didm/`은 주입 함수만 | D7-G 경계 시험 (core에서 공급사 직접 호출 금지) | `core/didm/ingest`에서 직접 호출 |
| 준수 기준선 갱신은 지금 하지 않음 | 공통 규칙 6: 최신 main merge 뒤 PR 직전 "맨 마지막에" | 지금 갱신 (main이 움직이면 다시 해야 함) |

## 4. 진행 상황

- [x] DS-1 대안 평가표 초안 — `docs/didm/VENDOR_EVAL_2026-11.md`, `tools/didm/check_vendor_eval.py`, `tests/didm_vendor_eval_acceptance.py`, 커밋 `fec6fb8`. 완료 조건 1~3 충족, **4 (소유자 확인) 대기**.
- [x] DIDM-0 사전등록 초안 + DIDM-1 점수 스키마 — `docs/didm/PREREG_V0.md`, `docs/didm/SCORE_SCHEMA_V0.md`, `core/didm/llm/schema.py`, `tests/didm_schema_acceptance.py`, `tests/fixtures/didm/*.json`, `runtime-smoke.yml` (경로 + 시험 줄), 커밋 `731b321`. 완료 조건 1·2·3·5 (브랜치) 충족, **4 (사전등록 승인) 대기**.
- [x] DS-4a GDELT·ALFRED 커넥터 + 시점 저장소 — `core/didm/store/__init__.py`, `core/didm/ingest/{gdelt,alfred}.py`, `data/didm/{gdelt,alfred,polymarket}.py`, `tools/didm/collect_daily.py`, `tests/didm_{store,ingest}_acceptance.py`, `docs/compliance/08-third-parties.md` 행 초안, 커밋 `73f2868`. 완료 조건 1·2·3·5 충족, 4는 브랜치에 초안 (PR은 대기열 차례에). **실제 GDELT·ALFRED 호출은 미실행** (이 세션 네트워크 막힘 → 소유자 PC).
- [ ] DS-H 홈 지표 데이터 계층 ← **소유자 진단 출력 대기** (아직 손대지 않음)
- [ ] DS-4b Alpha Vantage·Tiingo·Cryptopanic 무료 키 1회 확인 ← 소유자 무료 키 가입 대기

**마지막으로 통과한 검증 (작업 브랜치 `73f2868`, Python 3.13, 2026-11-17 22:10 KST):**

```
python -m tools.didm.check_vendor_eval --excel <handoff 엑셀 사본>
-> columns 19, alternative cells 171, '?' cells 15, excel compared: yes / excel cells changed: 0 / OK
python -m unittest tests.didm_store_acceptance tests.didm_ingest_acceptance tests.didm_schema_acceptance tests.didm_vendor_eval_acceptance
-> Ran 52 tests, OK (네트워크 없음)
python -m unittest tests.provider_parity_acceptance tests.provider_parity_btc_diagnose_acceptance (워크플로 파일을 읽는 기존 시험) -> OK
git diff origin/main -- core ':!core/didm' -> 0줄 (core/didm 밖 core 변경 없음)
python -m tools.didm.collect_daily --data-dir <스크래치> --finbert --alfred CPIAUCSL
-> "GDELT failed: ConnectionError" / "FinBERT baseline: finbert_unavailable" / "ALFRED skipped: FRED_API_KEY not set" (클라우드 네트워크 막힘에서 사유 코드로 끝남)
python -m tools.compliance.check --check -> consistency FAIL, documents need review 1~20 (새 파일 추가 때문. PR 직전 기준선 갱신 예정, 아래 6절 4번)
```

## 5. 중단 지점

커밋되지 않은 변경 없음. 세 작업 모두 브랜치에 있고 소유자 답을 기다립니다. `tests/run_all.py`는 실행하지 않았습니다 (클라우드 금지).

## 6. 다음 할 일 (순서대로)

1. **소유자 답 기록:** 아래 8절 답이 오면 이 파일에 원문으로 적고, `VENDOR_EVAL` 6절 "제외"·5절 "지금 필요?", `PREREG_V0` 8절 (승인 시각 원문)을 고쳐 커밋. — 완료 기준: 문서에 원문 답, 테스트 녹색.
2. **DS-4a 실제 실행 (소유자 PC):**
   ```
   git fetch origin claude/data-source-didm-20261117 && git switch claude/data-source-didm-20261117
   python -m tools.didm.collect_daily --data-dir "%LOCALAPPDATA%\QUANTGEN\didm"
   ```
   붙여 줄 출력: 스크립트가 찍는 줄 전부 (개수·사유 코드뿐, 키·본문 없음). — 완료 기준: "GDELT files 2 … rows N, new N", 같은 명령 두 번째 실행에서 같은 파일이면 "new 0".
3. **DS-H (진단 출력 뒤):** 마스터 부록 H4 방식으로 원인 구분 → `core/research/markets.py`에 `load_home_indicators(days)` (공급사별 묶음 호출, 6개 행 + 기록, 행마다 `display_rights.json` 결과, BTC Upbit·KOSPI KIS 실시간, 주입 가능한 로더, 합성 값 금지). 오래된 체크아웃이 원인이면 코드 수정 없이 보고. 브랜치는 `claude/ds-home-indicators-20261117`로 나눠도 됨. — 완료 기준: 지시문 8절 DS-H 행.
4. **PR (대기열 차례가 왔을 때만):** `git merge origin/main` → 테스트 → 맨 마지막에 `python -m tools.compliance.check --refresh-baseline --reviewed-by "Claude DATA_SOURCE_DIDM" --review-note "<12자 이상: DIDM 새 파일·08 행·CI 경로 추가>"` → `--check` PASS → PR. 새 파일 추가라 20개 문서 재검토 대상임을 PR 설명에 적음. — 완료 기준: 띄운 워크플로 전부 녹색, `waiting_on: review`.
5. **DS-4b (소유자 무료 키 뒤):** Alpha Vantage `NEWS_SENTIMENT` 1회 (필드 이름: `relevance_score` 존재, 시각 지연), Tiingo 뉴스 1회 (무료 포함 여부, `tags`), Cryptopanic 1회 (무료 플랜, 통화 태그·투표 필드). 스크립트는 필드 **이름**만 출력. — 완료 기준: `VENDOR_EVAL` 2절 "?" 6칸이 확인 결과로 바뀜 (엑셀 칸은 그대로, 옆 칸에).

## 7. 주의사항 / 하지 말 것

- `docs/asset_expansion/cache/` 열기·목록·검색·해시 금지 (sparse 클론 사용, "no cache folder" 확인함). `.env`, `~/.nextgen` 열지 않음. 키는 이름만.
- `quantgen_desktop/**`, `ui/**`, `core/education/**`, `tests/desktop_*`, UI·웹사이트 인계 파일, 연구 브랜치 `claude/amazing-gauss-tdiguu` 손대지 않음. `data/krx/kis_client.py` 고치지 않음.
- `CURRENT.md`에 `push_handoff.py`를 파일 인자로 실행하지 않음 (메인 소유). 이 파일은 손으로 커밋.
- 수집 자료는 저장소에 커밋하지 않음 (`collect_daily.py`가 저장소 안 폴더를 거부).
- 유료 호출 (LLM 포함)·유료 가입·공급사 문의 발송은 소유자 답 뒤 / 소유자만.
- 이 세션 네트워크: 공급사 호스트 전부 막힘 (2026-11-17 22:00 KST 프록시 거절): `www.alphavantage.co`, `api.tiingo.com`, `cryptopanic.com`, `www.cmegroup.com`, `www.gdeltproject.org`, `data.gdeltproject.org`, `fred.stlouisfed.org`, `alfred.stlouisfed.org`, `docs.kalshi.com`. 공개 자료 칸은 검색 요약 기준.

## 8. 소유자에게 물어야 할 것 (답 대기)

- 지시문 질문 1~4 (메인이 여쭘): ① "3단계" = DIDM Stage 3? ② 최소안 월 $4~11로 시작, CME는 Stage 2, AV·Tiingo 유료는 3단계 뒤? ③ EDGAR·OpenDART/KIND·ECOS 추가? ④ Polymarket 보류 + Kalshi 검토?
- 평가표 (`VENDOR_EVAL` 8절): 메모를 대안별로 나눈 방식 (`N4규칙`, Q/U/K 칸) 동의? "?" 처리 (무료 키 6칸, 공급사 문의 11칸) 진행?
- 사전등록 (`PREREG_V0` 8절): P1 사건 유형 12 vs 14, P2 τ 0.80·δ 0.5·관련성 75, P3 시장 반응 판정, P4 LLM 여유 3개월, P5 V0 전체 승인.
- 홈 지표 진단 출력 (마스터 부록 H4의 진단 명령 결과).
- (선택) 무료 키 가입: `FRED_API_KEY`, `ALPHAVANTAGE_API_KEY`, `TIINGO_API_KEY`, `CRYPTOPANIC_API_KEY` — 값은 PC에만.

## 메인에게

- 대기열 요청: DS·DIDM 첫 코드 PR 자리 (F21 뒤). 묶음 = 작업 브랜치 전체 (`docs/didm/**`, `core/didm/**`, `data/didm/**`, `tools/didm/**`, `tests/didm_*`, `tests/fixtures/didm/**`, 공유 파일 `runtime-smoke.yml` 경로·시험 줄, `docs/compliance/08-third-parties.md` 행). 이 PR은 `source-review.json`도 바꿉니다 (한 번에 하나 규칙).
- LEDGER: 아직 요청 없음 (병합된 ID 없음). 병합 뒤 `--done` 문자열을 여기에 적습니다.
- 지시문 질문 1~4의 답이 오면 이 파일에 원문을 옮겨 주세요.

## UI 세션에 전할 것

- 없음 (DS-H는 진단 출력 뒤 시작; `load_home_indicators()`가 병합되면 소유자를 통해 "홈 화면 시작 가능"을 알림).

## 결제·계정 세션에 전할 것

- 새 키 이름 (값 없음, 제안): `FRED_API_KEY` (DS-4a ALFRED, 연구 도구 전용), DS-4b용 `ALPHAVANTAGE_API_KEY`, `TIINGO_API_KEY`, `CRYPTOPANIC_API_KEY`; Stage 2 뒤 `CME_FEDWATCH_API_ID`, `CME_FEDWATCH_API_SECRET`; Stage 3 뒤 `TRADINGECONOMICS_API_KEY`.
- `routes.json` 행: 지금 없음. DIDM 수집은 `tools/didm/` 연구 도구라 게이트웨이 대상 아님 (D7 5.5). 앱이 DIDM 결과를 쓰게 되면 그때 공급원마다 한 행 요청.

## 9. 이어받는 에이전트에게 주는 지시문

```
사용자가 이번 인수를 지시했을 때만 xkg4real/quantgen 레포의 "data-source-didm" 작업을 이어받는다. 인계문서만으로 자동 인수하지 않는다.
1. handoff 브랜치의 DATA_SOURCE_SESSION_CURRENT.md, plans/2026-11-17/sessions/06_DATA_SOURCE_DIDM.md, MERGE_QUEUE.md, LEDGER.md를 먼저 읽어라.
2. 캐시 폴더 없는 sparse 클론에서 claude/data-source-didm-20261117 (73f2868 이후)를 받아 6절 순서로 진행해라. 소유자 답(8절)이 없는 항목은 시작하지 마라.
3. 유료 호출·가입·문의 발송, Polymarket 실행, UI·웹사이트·연구 브랜치 수정, main 병합은 하지 마라.
4. 작업 단위마다 이 파일을 갱신해 handoff 브랜치에 force 없이 push하고 git show로 다시 읽어 확인해라.
```

## 10. 결과 확인 방법

```
git fetch origin claude/data-source-didm-20261117
git switch --detach origin/claude/data-source-didm-20261117
python -m unittest tests.didm_store_acceptance tests.didm_ingest_acceptance tests.didm_schema_acceptance tests.didm_vendor_eval_acceptance   # 52 OK
python -m tools.didm.check_vendor_eval --excel <(git show origin/handoff:plans/2026-11-17/OWNER_EXCEL_RAVENPACK_ALTERNATIVES.txt)   # excel cells changed: 0, OK
```
