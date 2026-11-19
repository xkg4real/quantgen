---
status: checkpoint
reason: milestone
from: claude
task: data-source-didm
cycle: 2026-11-17
done_ids: none
next_ids: DS-1, DIDM-0, DIDM-1, DS-4a, DS-4d, DS-4e, DS-4b, DS-H
updated_at: 2026-11-20T02:07:54+09:00
stale_after_hours: 3
waiting_on: owner
work_branch: claude/data-source-didm-20261117
work_commit: c206b10
uncommitted_changes: no
pr: none
usage_weekly_pct: unknown
usage_5h_pct: unknown
usage_resets_at: 2026-11-24T17:00:00+09:00
session: https://claude.ai/code/session_016uB1jiXnUcWg99JHtRek9T
---

# 인수인계: QUANTGEN/MAIN -> DATA_SOURCE_DIDM

운영 기준: 메인↔하부 세션 사이는 [SESSION_PIPELINE](SESSION_PIPELINE.md) (소유자 지시 2026-11-20: 메인이 보낸 일은 바로 착수, 끝나면 바로 메인에 보고). GPT 인계는 그대로 [자동감시 취소·수동 인계](OWNER_HANDOFF_POLICY_2026-11-13.md) (소유자가 이어받으라고 할 때만).

## 0. 한 줄 요약

DS-1 평가표 소유자 확인 완료, DIDM-0 사전등록 V0 **소유자 승인** (2026-11-18), 신규성 모형 (`core/didm/novelty.py`) 추가, DS-4a·4d·4e 커넥터까지 작업 브랜치 `claude/data-source-didm-20261117` (`1739376`). main 미병합, PR 없음 (대기열 차례 전). **남은 소유자 입력**: 홈 지표 진단 출력, PC 실행 출력 (키·연락처 설정 뒤).

## 1. 목표와 완료 조건

- **사용자 요청 (원문 그대로, 2026-11-17 `owner_answer_1117.txt`):**
  > 5. D14 : Ravenpack의 대안책 3단계 (엑셀 파일 참고)의 자료들로 구성할 예정.
  > 1. D6 : 현재 메인세션의 하부 세션 (QUANTGEN/TRADEGEN -> TRADEGEN_GITHUB 과 같은 구조)으로 3가지를 생성할 것. 이때 이미 돌아가고 있는 UI/UX 수정 세션 등은 건들지 말 것.
- **2026-11-16 Notion 요청 (원문):**
  > DIDM에서 제공해주는 정보가 어디 정보에 포함되는 건지, 어떤 range를 가지는지에 따라 이에 보완책이 되는 정보 제공 source 찾고 연결하기
  > 메인화면 아직도 리서치 홈에서 지표가 안뜨는데, 이거 고칠 것. 주요 지표 6개를 그래프와 함께 구현하도록(앱 키자마자 실시간) 해야함.
- **완료 조건:** 지시문 `plans/2026-11-17/sessions/06_DATA_SOURCE_DIDM.md` 7절 (작업 1~3), 8절 표.
- **범위 밖:** 앱 화면 (UI 세션), 웹사이트, 키 저장소·게이트웨이 코어 (결제·계정 세션), 유료 호출·가입, Polymarket 실행, main 병합 (메인).

## 1.1 소유자 답 (2026-11-18, 원문 그대로)

> 1. 아뇨, 위 두 파일에서 나온 RavenPack 외 대안책으로 사용 가능한 데이터 공급원 9개를 의미하는 겁니다.
> 2. 네 가능합니다
> 3. 네 진행하세요. 진행하고 나서 만약 QUANTGEN 앱 내부 아키텍처 혹은 단순한 코드/파일을 바꿔야하는 부분이 있다면 저한테 알려주세요.
> 4. 네 Kalshi로 진행하겠습니다.

"위 두 파일" = 소유자 엑셀 (원본 업로드, 글 사본과 같음 확인)과 MTFE 문서 (handoff `plans/2026-11-18/OWNER_MTFE_RAVENPACK_REVIEW_2026-11-11.md`). 같은 메시지의 작업 지시: "/karpathy-guidelines /trading-skills-navigator 등의 스킬들을 조합해 업무를 진행해주세요. 이때, Claude.md 파일에 있는 가이드라인을 먼저 읽고 나서 작업을 진행해주세요." (karpathy-guidelines는 이 세션의 스킬 목록에 없음; trading-skills-navigator는 추천 스크립트가 빠진 채 동기화되어 수동으로 고름.)

## 1.2 소유자 답 (2026-11-18 둘째, 원문 그대로)

평가표 8절:
> 1. 네 맞습니다. 다만 직접 구현이 필연적이므로, 표기를 X 대신 O로 해주세요
> 2. ?에 대해서 별도 처리할 필요는 없으나, 대안책의 자산별관련성점수의 경우 X로 확정입니다.

사전등록 8절:
> 1. 원래 출발안 14개가 기존 12개의 범주를 포함하면서 확장한 것이라면 (즉 12개에는 있으나 14개에는 분류가 달라 없는 경우가 아닌 경우) 14개로 시작
> 2. 시간만을 더미변수로 간주하고 점수로 매기기보다, 가능한 모든 요소(변수화)를 고려한 데이터과학/계량경제학적 모형(다중회귀든 time series든 상관 없음)을 세우고(이때의 y변수는 신규성이 되는 것도 하나 세울 것), 이때 기존 cutoff(0.75)에서 test를 했을 때 기대되는 accuracy가 0.9 이상이 되도록 하여 신규성을 평가할 것.
> 3. 승인
> 4. 승인, 단 여기서 말하는 LLM이 어떤 LLM인지가 중요. 위 문서에서 말하는 자체 개발 LLM을 의미하는거가 맞다면 승인.
> 5. 위 내용을 반영한 상태에서 승인

"위 문서" = 소유자 "QUANTGEN 장기 비전 첫걸음 초안" (2026-11-17), 사본 handoff `plans/2026-11-18/OWNER_LONG_TERM_VISION_FIRST_STEP_2026-11-17.md`.

반영 (커밋 `1739376`): 평가표에 "대안책 (소유자 확정)" 열 (N=O, O=X, W=O; 엑셀 열은 그대로, 검사 바뀐 칸 0), 자체 NLP 직접 구현 칸 G·H·K·N·W·X = O (D1), 관련성 X (D2), "?" 처리 안 함. 사전등록: 14개 유형 (12개의 모든 범주가 14개에 대응 확인), 신규성 = 모형 P̂(새 사건) (시간순 70/30 검정, 컷오프 0.75, 목표 정확도 ≥ 0.90, 관련성 모형 동일 틀), LLM 기준일 규칙에 자체 개발 LLM 정의 추가, **V0 승인 기록**.

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
- [x] 소유자 답 1~4 반영 — `VENDOR_EVAL` 0.1·3·5·6·8절, `PREREG_V0` 1·4·8절. 커밋 `7bf99b3`.
- [x] DS-4d EDGAR·OpenDART·ECOS 커넥터 (KIND는 공개 API 없음 → 연결 안 함, OpenDART로 대신) + DS-4e Kalshi 커넥터 — `core/didm/ingest/{filings,ecos,kalshi}.py`, `data/didm/{edgar,opendart,ecos,kalshi}.py`, `tests/didm_sources_acceptance.py`, `collect_daily.py` 옵션, 08 행·CI 줄. 커밋 `7bf99b3`. **실제 호출 미실행** (키·UA 없음, Kalshi 호스트 막힘 → 사유 코드 확인).
- [x] 소유자 답 (평가표 8절, 사전등록 P1~P5) 반영 + 신규성 모형 — `core/didm/novelty.py`, `tests/didm_novelty_acceptance.py` (시뮬레이션: 정보 있는 자료 검정 정확도 1.00 / 무작위 표지 0.466 불통과), 스키마 14개 유형·`novelty_0_100`. 커밋 `1739376`.
- [x] 소유자 PC 1차 실행 (2026-11-18): `setx`로 `ECOS_API_KEY`·`FRED_API_KEY`는 빈 값, `SEC_EDGAR_USER_AGENT`는 일반 연락처로 저장, 같은 창의 확인에서 네 이름 모두 False (setx는 새 창부터 보임; OPENDART는 `.env`에 있음). 수정: `collect_daily`가 `config`를 import해 `.env`를 읽고 `--check-keys` (이름·True/False만) 추가. 커밋 `d6b1edd`. **소유자 재확인 대기.**
- [x] 소유자 PC 첫 수집 (2026-11-18, worktree `Desktop\QUANTGEN_didm`; 원래 폴더의 `qa/acceptance_results.json` 미커밋 변경은 건드리지 않음): ALFRED CPIAUCSL 3,364행, EDGAR 147건 성공. Kalshi 200개 저장됐으나 현재 필드 (`*_dollars`, `*_fp`)를 못 읽어 가격 없음·liquid 0 → 파서 `kalshi-v0.2`·쪽 따라가기로 고침. GDELT `HTTPError` → 단계·상태 코드 출력 추가. ECOS 722Y001 0건 → 결과 코드 출력·`--ecos-items` 추가. OpenDART 키 없음 (worktree에 `.env` 없음). 커밋 `23bb47c`, `VENDOR_EVAL` 3.1. **소유자 재실행 대기.**
- [x] 소유자 PC 둘째 실행 (2026-11-18): Kalshi 해결 (236개, 가격 236, 유동 80). ECOS 통계표 확정 `722Y001/0101000` = 기준금리 (`060Y001` 데이터 없음), 그러나 월 시계열 INFO-200 → `--ecos-probe` 추가. GDELT 최신 export 404 (게시 전) → 직전 두 칸 대체 + `--gdelt-day` (하루 96칸; 기존은 15분 한 칸만) 추가. 커밋 `5fadc20`, `VENDOR_EVAL` 3.1. **셋째 실행 대기.**
- [x] 소유자 PC 셋째 실행 (2026-11-18): GDELT 최신 칸 3,090행, 하루치 20261117 96파일·127,432행 (해결). ECOS 0건 원인 = PowerShell이 따옴표 없는 `0101000`을 `101000`으로 바꿈 (항목 코드 없이 306행 받음) → 6자리 숫자 항목 코드 거부·따옴표 안내. 커밋 `a790ce8`. 남은 확인: ECOS 따옴표 재실행, OpenDART (worktree에 키 없음).
- [x] 소유자 PC 넷째 실행 (2026-11-18): ECOS 기준금리 월별 34개월 (따옴표, 해결). OpenDART는 worktree에 `.env`가 없어 `DARTUnavailable` → `--env-file` 추가 (커밋 `17a1d66`). 확인 완료 5/6 (ALFRED, EDGAR, Kalshi, GDELT, ECOS), OpenDART만 남음.
- [x] 소유자 승인 (2026-11-19, 원문): "이후 key-3 승인을 완료했고 위 제안을 승인햇습니다. 이에 맞게 지금 부족한 API키/자료 공급원 연결을 진행해주세요. 만약 제가 수동으로 작업해야한다면 이 역시 table 형식으로 어떤 항목을 어떻게 언제 하는지를 알려주세요" ("위 제안" = 결제·계정 세션의 "KEY-3 PR에 연구용 키 이름 9개를 자격 증명 저장소에"). 반영: main `ca5da08` merge (`b935bec`, runtime-smoke 충돌 = main 줄 + DIDM 경로·시험만 다시 더함), `data/didm/keys.py` (저장소가 이름을 알면 `core.credentials.get`, 아니면 환경변수), `tools/didm/keys.py` (status / set 숨김 입력), DS-4b Alpha Vantage·Tiingo·CryptoPanic 연결 (`core/didm/ingest/news.py`, `data/didm/{alphavantage,tiingo,cryptopanic}.py`, `tests/didm_news_acceptance.py`). DIDM 시험 95 OK. 커밋 `df05b21`. 실제 호출은 소유자 무료 키 가입 뒤.
- [x] 메인 지시 (2026-11-20 00:50 KST, SESSION_PIPELINE) 3): main `9f76b07` (KEY-3) merge commit `f60e314` (runtime-smoke 충돌 = main 줄 + DIDM 경로·시험만 다시 더함). DIDM 시험 95 + `RealStoreRoundTrip` 3 = 98 OK. `tests.credentials_acceptance`·`gateway_*` 3개·`provider_parity` 208 OK (skip 3) — main `9f76b07`에서도 같은 결과 (실패 집합 둘 다 비어 있음). `data/didm/keys.py`가 KEY-3 저장소 경로와 맞음: 연구용 9개 이름 모두 `kind=research`, 저장 → 키링에서 읽기, 환경변수 우선. 커밋 `eb4f3a5`. **PR 직전 상태** (최신 main 합침; 남은 것 = 준수 기준선 갱신 → `--check` → PR, MERGE_QUEUE 8행 "병합: DATA_SOURCE_DIDM" 뒤). `compliance --check` 지금 FAIL (새 파일, 문서 20개 재검토 대상) = 예상.
- [ ] DS-H 홈 지표 데이터 계층 — **KEY-4 (PR #133, `core/research/markets.py`) 병합 뒤 main에서 시작** (메인 지시)
- [x] OA-07 OpenDART 소유자 PC 확인 (2026-11-19): 9쪽, 819건. 공식·무료 공급원 6곳 모두 확인 끝. 남은 확인 = 무료 키 3곳 (OA-08).
- [-] DS-4b CryptoPanic 보류 (2026-11-20, 소유자 지적 확인): 무료 API 없음 (공식 요금: Growth $50/주·$199/월, Enterprise $899/월~; 무료 Developer 2026-04-01 종료 보도). 단계별 비용 결정에 따라 뺌, 코드는 남김. 암호화폐 감성 X열은 Alpha Vantage로 채움. OA-08은 무료 키 2개 (Alpha Vantage, Tiingo). 커밋 `4abe761`.
- [ ] OA-08 첫 실행 (2026-11-20): `Alpha Vantage failed: NewsError`, `Tiingo failed: RuntimeError` — 원인 문구가 숨겨져 있었음 → 공급사 오류 문구 (키 가림) 출력하게 고침, 커밋 아래 work_commit. **소유자 재실행 대기** (`--alphavantage AAPL --tiingo nvda`).
- [-] DS-4b 전체 보류 (2026-11-20, OA-08 소유자 PC): Alpha Vantage NEWS_SENTIMENT = "premium endpoint", Tiingo news = HTTP 403 "no permission to access the News API", CryptoPanic = 유료만. 무료로 되는 곳 0 → 단계별 비용 결정대로 보류, 코드는 남김. 뉴스는 GDELT·자체 NLP, 공시는 EDGAR·OpenDART. OA-08 닫힘. 같은 커밋에 safe_detail 가림→자르기 순서 수정 (메인 검토). 커밋 `c206b10`.
- [-] DS-3 — 계획에 없음 (메인 11-20: 소유자 11-18 답 1 "3단계" = RavenPack 대안 9개, Bigdata.com 시험 없음 → RavenPack 견적·Bigdata.com 비교 없음). OA-38 소유자 확인 대기, 원하시면 다시 엶
<!-- old DS-H line kept below for history -->
- [ ] DS-H 홈 지표 데이터 계층 ← **소유자 진단 출력 대기** (아직 손대지 않음)
- [ ] DS-4b Alpha Vantage·Tiingo·Cryptopanic 무료 키 1회 확인 ← 소유자 무료 키 가입 대기

**마지막으로 통과한 검증 (작업 브랜치 `73f2868`, Python 3.13, 2026-11-17 22:10 KST):**

```
python -m tools.didm.check_vendor_eval --excel <handoff 엑셀 사본>
-> columns 19, alternative cells 171, '?' cells 15, excel compared: yes / excel cells changed: 0 / OK
python -m unittest tests.didm_store_acceptance tests.didm_ingest_acceptance tests.didm_sources_acceptance tests.didm_schema_acceptance tests.didm_vendor_eval_acceptance
-> 2026-11-18 1739376: OK (네트워크 없음; + tests.didm_novelty_acceptance 6)
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

- (c) 평가표 판단 2칸 확인 (2026-11-18 대화에서 여쭘): 자체 NLP 열에서 뉴스 수집 F·실시간 J는 X로 둠 (다른 공급원의 일), 자체 NLP 관련성 칸은 소유자 답 "관련성 X 확정"대로 X로 둠 (DIDM 내부에서는 계산함). 이대로 맞는지.

- ~~지시문 질문 1~4~~ → 2026-11-18 답함 (1.1절).
- ~~평가표 8절~~ → 2026-11-18 답함 (1.2절).
- ~~사전등록 P1~P5~~ → 2026-11-18 승인 (1.2절).
- 신규성 모형의 보조 조건 (검정 정확도가 "전부 새 사건" 다수 범주 정확도를 넘을 것)을 정식 조건으로 할지 — 사전등록 4.1절 "제안".
- 자체 개발 LLM의 현재 상태 (기반 모델·학습 자료 마지막 날짜) — `MODEL_CUTOFFS.md`에 필요 (장기 비전 초안 7절과 같은 질문).
- 홈 지표 진단 출력 (마스터 부록 H4의 진단 명령 결과).
- (선택) 무료 키 가입: `FRED_API_KEY`, `ALPHAVANTAGE_API_KEY`, `TIINGO_API_KEY`, `CRYPTOPANIC_API_KEY` — 값은 PC에만.

## 앱 구조·파일 영향 (소유자 답 3의 요청, 2026-11-18)

- 앱 화면·`core/` (DIDM 밖)·`config.py`: **바꾼 것 없음.** 새 공급원은 모두 연구 도구 경로 (`tools/didm`, `data/didm`, `core/didm`)에만 있고 앱이 부르지 않음 (D7-G 규칙).
- 공유 파일 (PR 때 대기열로): `runtime-smoke.yml` 경로·시험 줄, `08-third-parties.md` 행 (브랜치에 있음), `source-review.json` 기준선 갱신 (PR 직전), `.env.example`에 이름 추가 제안 `FRED_API_KEY`, `ECOS_API_KEY`, `SEC_EDGAR_USER_AGENT` (아직 안 고침).
- `requirements.txt`: 바꿀 것 없음 (표준 라이브러리 + 기존 requests). FinBERT용 `transformers`·`torch`는 소유자 PC 선택 설치.
- 결합 한 곳: `data/didm/opendart.py`가 `OpenDARTClient._get` (밑줄 함수)을 씀. 결제·계정 세션 KEY-2가 OpenDART 키 처리를 바꾸면 같이 확인해야 함.
- 나중에 앱이 DIDM 결과를 보이려면: 공급원마다 `routes.json` 한 행 + `display_rights.json` + 법률 의견 (구조 변경, 소유자에게 먼저 알림).

## 메인에게

- 대기열 요청: DS·DIDM 첫 코드 PR 자리 (F21 뒤). 묶음 = 작업 브랜치 전체 (`docs/didm/**`, `core/didm/**`, `data/didm/**`, `tools/didm/**`, `tests/didm_*`, `tests/fixtures/didm/**`, 공유 파일 `runtime-smoke.yml` 경로·시험 줄, `docs/compliance/08-third-parties.md` 행). 이 PR은 `source-review.json`도 바꿉니다 (한 번에 하나 규칙).
- LEDGER: 아직 요청 없음 (병합된 ID 없음). 병합 뒤 `--done` 문자열을 여기에 적습니다.
- 질문 1~4 답은 소유자가 이 세션에 직접 줌 (1.1절). "3단계" = DIDM Stage 3이 아니라 대안 9개라는 답은 `D14_RAVENPACK_ALTERNATIVES.md` 1절 해석과 다르니 메인 문서도 고쳐 주세요.

## UI 세션에 전할 것

- 없음 (DS-H는 진단 출력 뒤 시작; `load_home_indicators()`가 병합되면 소유자를 통해 "홈 화면 시작 가능"을 알림).

## 결제·계정 세션에 전할 것

- (2026-11-19) 데이터소스 쪽 준비 끝: `data/didm/keys.py`가 `credentials.names.is_secret(name)`이 참이면 `credentials.get/status/set`을 씀. KEY-3 브랜치 `8a2886b`의 `RESEARCH` 9개와 이름이 같음 (`data.didm.keys.RESEARCH_KEYS`). KEY-3 PR이 main에 들어가면 데이터소스 쪽 코드 수정 없이 저장소 경로로 바뀜. 따로 요청할 것 없음.

- 새 키 이름 (값 없음, 제안): `FRED_API_KEY` (DS-4a ALFRED, 연구 도구 전용), `ECOS_API_KEY`, `SEC_EDGAR_USER_AGENT` (연락처 문자열; DS-4d), OpenDART는 기존 `OPENDART_API_KEY` (`data/didm/opendart.py`가 `OpenDARTClient._get` 사용), DS-4b용 `ALPHAVANTAGE_API_KEY`, `TIINGO_API_KEY`, `CRYPTOPANIC_API_KEY`; Stage 2 뒤 `CME_FEDWATCH_API_ID`, `CME_FEDWATCH_API_SECRET`; Stage 3 뒤 `TRADINGECONOMICS_API_KEY`.
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
