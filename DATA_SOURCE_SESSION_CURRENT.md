# 중앙 DIDM 코드 통합 완료 — 2026-11-21T19:48:44+09:00

- status: returned-code-only · from: 메인Codex · execution2f27d0c2-57cc-46e7-97d6-fc141d4065c9. 최신 gpt/data-source-didm-20261121@6cff168 → PR138 → 실제main53e5e7230d24bfcebf77e16762e7117bb5905137. 부모6d/6cff·testedtree023/PR/ref원격대조.
- all6Runtime·문서CI·8checks success/독립검토·actual844sources/20policies PASS/publicationBLOCKED65. 공식DIDM-1·DS-4a를코드/합성범위로만LEDGER추가, DS1/OA10·실모델/표본성과·실API/권리·법률/운영·DS4d/e전체는미완료. V0승인11-18/등록문턱·AND/UTC/asof 불변, 글사본38/파생171·실제XLSX미재검증 구분.
- 별도DIDM/UI세션중복개발중지·중앙총괄유지. 다음중앙차례4hKEY45: 실제main023과준비candidate6cff동일tree를확인후최종baseline/CI/PR. 아래기록은모두이력보존. [현재전체](WEEKLY_HANDOFF_2026-11-21_2f27d0c2.md).

---

---
status: checkpoint
reason: milestone
from: claude
task: data-source
cycle: 2026-11-24
done_ids: none
next_ids: DS-5b, DS-5c, DS-5a
updated_at: 2026-11-24T21:40:00+09:00
stale_after_hours: 3
waiting_on: owner
work_branch: claude/ds-collection-status-20261124 (+ claude/ds-5bc-news-20261124@4a646ce, claude/ds-connector-fixes-20261124@241c0f4, claude/ds-home-diagnose-20261124@b70a78d, claude/ds-new-sources-plan-20261124@6a6516d)
work_commit: b4d48bc
uncommitted_changes: no
pr: none
usage_weekly_pct: unknown
usage_5h_pct: unknown
usage_resets_at: 2026-12-01T17:00:00+09:00
session: Codex DIDM 6af7214e-7798-8191-8cfe-66ba373de0ad
execution_id: 2f27d0c2-57cc-46e7-97d6-fc141d4065c9
handoff_to: QUANTGEN_MAIN_CODEX
implementation_stopped: yes
---

## DATA_SOURCE (Claude) D4·D5 — 2026-11-24T21:40+09:00

- 메인 지시 (11-24): D4 수집 운영 점검 문서·요약 명령, D5 DS-4c 설계만. D1~D3은 메인 통합 PR에 들어감 (PR 열지 않음).
- 브랜치 `claude/ds-collection-status-20261124` @ b4d48bc (origin/main de32ea1에서 분기).
- D4: tools/didm/collection_status.py (SQLite mode=ro, 건수·날짜만), tests/didm_collection_status_acceptance.py 7 OK, docs/didm/COLLECTION_STATUS_GUIDE_2026-11-24.md (명령, 읽는 법, 2015~2024 표본 채움 가능 표). 소유자 명령: `python -m tools.didm.collection_status --data-dir "$env:LOCALAPPDATA\QUANTGEN\didm"`.
- D5: docs/didm/DS4C_FEDWATCH_DESIGN_2026-11-24.md (내부 정규 형식, 시점 규칙, 파일 배치, 시험 T1~T10). 코드·호출 없음, OA-31 답 대기.
- 검사: DIDM 11모듈 + gateway_boundary + packaging_policy 221 OK.
- 메모: DS-5b/5c는 소유자가 이 세션에 직접 "N0 승인, Alpaca·Massive부터 진행하세요"라고 답해 코드까지 끝냄 (4a646ce). 메인의 "N0 답 전 시작 안 함" 지시보다 소유자 답이 먼저 왔음을 메인에 알림.

## DATA_SOURCE (Claude) DS-5b/5c 코드 — 2026-11-24T21:10+09:00

- 소유자 요청 원문: "N0 승인, Alpaca·Massive부터 진행하세요" (EODHD DS-5a 유료는 보류, N1 답 대기).
- 브랜치 `claude/ds-5bc-news-20261124` @ 4a646ce (origin/main b872d8c에서 분기, PR 없음: MERGE_QUEUE "병합: DATA_SOURCE" 대기).
- 파일: data/didm/alpaca_news.py (신규, 키는 APCA 헤더만, include_content=false), data/didm/massive_news.py (fetch_page, Bearer 헤더, 12.5초 간격), core/didm/ingest/news_store.py (신규, 시점 저장소 행; 본문·요약 없음), tools/didm/collect_daily.py (--alpaca-news, --massive-news, --news-start, --news-end, --news-max-pages), data/didm/keys.py (ENV_ONLY_KEYS: ALPACA_API_KEY_ID, ALPACA_API_SECRET_KEY, MASSIVE_API_KEY), tools/didm/keys.py, tests/didm_news_connectors_acceptance.py (12), runtime-smoke, docs/compliance/08-third-parties.md DIDM 행.
- 판단: 새 키 이름은 core.credentials에 없어 RESEARCH_KEYS(저장소 등록 전제 시험 있음)와 분리해 환경변수로만 읽음 → 결제·계정 세션이 이름을 등록하면 RESEARCH_KEYS로 옮김.
- 검사: DIDM 11모듈+gateway_boundary+third_party_notices+packaging_policy 232 OK; `git diff origin/main -- core ':!core/didm'` 비어 있음; check_vendor_eval 엑셀 값 변경 0.
- 중단 지점: 실제 무료 키 응답 미확인 (Alpaca 무료 계정이 REST 뉴스를 허용하는지, Massive 무료 뉴스 과거 깊이). 소유자 PC 실행 대기 (waiting_on: owner).
- 다음: 소유자가 무료 키 발급·setx → `python -m tools.didm.collect_daily --data-dir "$env:LOCALAPPDATA\QUANTGEN\didm" --no-gdelt --alpaca-news AAPL --massive-news AAPL --news-start 2026-11-01 --news-max-pages 2`. 완료 조건: 두 줄 모두 "articles N>0", 오류 시 HTTP 코드 문구로 플랜 한계 판정 → NEW_SOURCES_PLAN에 기록.

## 메인 Codex DIDM 통합 시작 — 2026-11-21T17:35:29+09:00

DS-H codePR137→main6d25a33(parent72a+497/tree1c26a4be tested정확동일),전체6Runtime/Compliance·독립검토PASS. 원격DIDMabd를동일gpt작업으로이어실제최신mainmerge한다. 첫시도는기존proxy promisorblob 수신실패로시작전중단/clean보존, 명시공개path만mapping·materialize후재시도. AUTO_STATE과거main스냅샷/보호cache/.env/실제home는사용하지않는다. sourceproducer만runtime합집합/08·20기술문서·증거문구수정,QA/programread-only독립검토,최종baseline/원격/PR는root. 글사본원문38값과파생171칸분리·실제XLSX이번미검증, 과거openpyxl이력/값/V0/판정불변. 새대기PR/전체DIDM·실API·권리/법률/실운영완료없음. [이번실행](WEEKLY_HANDOFF_2026-11-21_2f27d0c2.md).

## 중앙 부분 인계 — 2026-11-21T14:54:13+09:00

DS-H137 exact497의 문서CI/독립PASS·전체Runtime진행. 후속메인배정03:27의코드/PR먼저·진단오면추가문구와최신소유자중앙조건부merge승인을대조해 code-only기술통합과OA09실진단/홈연결완료를구분한다. OA09면제/parent완료아님. DIDMabd는그대로원격보존(새code/policy/PR없음), 다음최신DSH main합류의runtime합집합182paths/167modules/173targets예측·startup/home누락0계획. actual최종844source/20리뷰는아직아니다.08/wheel경계·20/명시data-dir SQLitefootprint최소안R2는독립검토완료/private보존, 기존연구용도·보존/삭제/권리/등록/판정기준불변.20입력원문이현재DIDM/finalOS와다르므로최종mainmerge후최신SHA/old_str로적용한다. 실제DB/API/CLI/모형/PC/출시는실행하지않았다. [전체인계](WEEKLY_HANDOFF_2026-11-21_1bfaa7d8.md).

## 중앙 Codex DS-H 초안 — 2026-11-21T14:36:47+09:00

별도 DIDM 세션의 새 구현 중지는 유지하며, 단일 창구 root가 기존 승인을 수행했다. DS-H gpt/ds-home-indicators-20261121 최신4973111, 부모7ce+main72a, 정확5본문·tree/ref 대조 후 초안 PR137. 합성172/준법47PASS(중복),20정책·실제809소스 정합성PASS/publicationBLOCKED. 독립 최종 검토 PASS를 받았고 문서 CI는 성공했고 전체 Runtime CI 및 OA09 실제 진단 조건 대조는 남았다. 원문 조건 차이를 임의 면제하지 않으며 실제 공급사/API/소유자 진단·DS-H 완료를 주장하지 않는다. DIDMabd10c6와 사전등록/문턱·모형/LLM/cutoff 선택은 보존한다. 다음 DIDM PR은 DS-H 순서가 해결된 뒤 최신 main·최종 검토/CI로 진행한다. [중앙 인계](WEEKLY_HANDOFF_2026-11-21_1bfaa7d8.md).

## 중앙 Codex 최신 검토·원격 보존 — 2026-11-21T12:33:42+09:00

소유자의단일창구·5담당승인으로root가DATA를인수했다. 별도DIDM채팅의새구현중단은유지하고본중앙담당이이어간다. [중앙인계](WEEKLY_HANDOFF_2026-11-21_a3da2627.md).
최신원격DIDM은 **abd10c6**(parent8781267)이다. 같은receipt/payload·다른메타데이터를조용히버리는계약불일치를고쳐StoreError로거절·rollback하며기존schema/UNIQUE/asofSQL/사전등록/문턱불변. old5회귀실패→store13/DIDM137PASS, 독립8PASS. 홈7ce3791공통131PASS/독립6, 공급사대조147합성PASS. 실제API/실연구/성능완료로확대하지않는다.
3파일commit/parent/blob/branch/core본문readback일치, 로컬detachedHEAD도abd10c6동일·보호경로제외clean. OS136새CI후병합→DSH→DIDM차례. 준법기준선·필수CI·PR·main병합·done_ids는미완료다. 현재새수동질문은없고기존OA09/10/38/46만유지한다. 아래878·132개기록은이전관측이력이다.

# 인수인계: DATA_SOURCE_DIDM -> QUANTGEN 메인 Codex

운영 기준: 메인↔하부 세션 사이는 [SESSION_PIPELINE](SESSION_PIPELINE.md) (소유자 지시 2026-11-20: 메인이 보낸 일은 바로 착수, 끝나면 바로 메인에 보고). GPT 인계는 그대로 [자동감시 취소·수동 인계](OWNER_HANDOFF_POLICY_2026-11-13.md) (소유자가 이어받으라고 할 때만).

## 0. 한 줄 요약

**2026-11-24 재개 (DATA_SOURCE, 메인 지시 11-24):** 이 세션은 이제 **DATA_SOURCE**만 (데이터 수집·공급사). DIDM 모형 (`core/didm/llm/**`, `core/didm/novelty.py`, `tests/didm_{schema,novelty}_acceptance.py`, `docs/didm/PREREG_V0.md`·`SCORE_SCHEMA_V0.md`)은 새 세션 DIDM_DEV (session_016uB1jj8iv57xVbx6EbLLwq). 11-20 인계 뒤 GPT가 병합: DS-H/code PR #137 (6d25a33), DS·DIDM 코드 PR #138 (53e5e72), EODHD·Alpaca·Massive 파서 #142~#144, V0 검사 #145. 이전 브랜치 f80b3b0·c206b10은 모두 main에 있음 (다시 하지 않음).

| 일 | 브랜치 @ 커밋 | 상태 | 확인 |
|---|---|---|---|
| D1 커넥터 고침 2건 (GPT Kalshi 입력 검사 77c37c5 + ALFRED 개정 기간 593c943) | `claude/ds-connector-fixes-20261124` @ `241c0f4` | PR 전, MERGE_QUEUE 13번 "병합: DATA_SOURCE" 뒤 | sources 31 OK, ingest 27 OK, DIDM 7개 152 OK, 파서 3종 56 OK, didm_* 10개 208 OK, gateway_boundary 15 OK, core/didm 밖 core 변경 0. source-review.json은 main 쪽 유지 (기준선은 PR 직전) |
| D2 홈 지표 진단 한 줄 명령 (OA-09) | `claude/ds-home-diagnose-20261124` @ `b70a78d` | PR 자리 메인이 정함 | `python -m core.research.markets` 클라우드 종료 0·6줄·stderr 0; home_indicators 23 OK, 새 diagnose 7 OK, 회귀 60 OK |
| D3 새 공급사 3곳 계획 (문서) | `claude/ds-new-sources-plan-20261124` @ `6a6516d` | 소유자 확인 N0·N1 대기 | check_vendor_eval 엑셀 바뀐 칸 0, vendor_eval 시험 OK |

PR 순서·절차: 메인이 MERGE_QUEUE에 적은 뒤에만. 최신 main merge → 시험 → `python -m tools.compliance.check --refresh-baseline ...` (맨 마지막) → `--check` PASS → PR.

소유자 대기: OA-09 (D2의 새 한 줄 명령으로), N0 (EODHD·Alpaca·Massive 쓸지), N1 (EODHD 유료 시점), OA-46 (BTC 단위), OA-38, OA-10(c).

### (아래는 11-24 이전 기록)



### 최우선: QUANTGEN 메인 Codex로 인계 — 2026-11-21T11:59:26+09:00

**소유자 최신 지시 (2026-11-21, 이 DIDM 채팅 원문):**
> 앞으로 QUANTGEN 메인 Codex 세션이 작업을 총괄합니다. 현재 진행한 변경을 보존하고, 브랜치·최신 커밋·PR·검증 결과·미커밋 변경·남은 작업·소유자 결정 사항을 인계 문서에 기록해주세요. 원격 반영 여부까지 확인한 뒤 작업을 인계 상태로 전환하고, 새로운 구현은 시작하지 마세요. 메인 세션이 이어받습니다.

**담당 전환:** 이후 구현·PR·병합·다음 작업 배정은 QUANTGEN 메인 Codex가 총괄한다. 이 DATA_SOURCE_DIDM 세션은 변경을 보존하고 인계 상태로 전환했으며 새 구현을 시작하지 않는다. 아래 과거의 자동 배정·이 세션 재개 관련 문구보다 이 최신 소유자 지시가 우선한다.

| 구분 | DS·DIDM | DS-H 홈 지표 |
|---|---|---|
| 보존된 브랜치 | `gpt/data-source-didm-20261121` | `gpt/ds-home-indicators-20261121` |
| 최신 커밋 (로컬 = 원격) | `87812679aec6f333d91b867f5892e523e0da9b0c` | `7ce37917102af9793d3ccbe851c0554058089df9` |
| 로컬 작업 폴더 | `/workspace/didm_dev` | `/workspace/didm_home` |
| PR | 없음 — 해당 head branch로 전체 상태(open/closed/merged) 조회 결과 0건 | 없음 — 동일 조회 결과 0건 |
| 미커밋·staged·untracked 변경 | 없음 (보호 캐시 경로 제외한 허용 범위 git status/diff 확인) | 없음 (같은 방식) |
| 원격 반영 | GitHub branch ref GET으로 위 SHA 일치 재확인 | GitHub branch ref GET으로 위 SHA 일치 재확인 |
| 검증 결과 | DIDM 132 PASS, 공급사 대조 147 PASS, 엑셀 원본 변경 0칸 | 홈23 포함 홈·공통131 PASS |
| 변경 설명 | `docs/didm/IMPLEMENTATION_REVIEW_2026-11-21.md` | `docs/product/HOME_INDICATORS_DATA_2026-11-20.md` |

검증 결과는 앞선 구현 작업에서 실행한 로그를 이번 인계에서 재확인한 것이다. 이번 차례에는 새 구현·수익률 실험·시험 재실행 없이 상태 확인과 인계 문서 갱신만 했다.
검증 로그·격리 실행기: `/workspace/didm_work/resume_20261121/`의 `didm_final.log`, `home_regression.log`, `provider_regression_shm.log`, `run_offline.py`, `run_regression.py` (로컬 보조 자료; 코드 변경 자체는 위 두 원격 브랜치에 보존).
인계 확인 시 원격 main은 `f065ec92dbce1e1b34e4adb0b6dbed724305a2f4`이며 이 두 작업은 아직 main 미병합이다. compliance 기준선 갱신·PR CI는 아직 하지 않았으므로 통과를 주장하지 않는다.

**메인이 이어갈 남은 작업**
1. 최신 중앙 CURRENT·WORKBOARD·MERGE_QUEUE를 확인한다. 이번 조회 기준 순서는 OS-F2(4e) → DS-H(4f) → DS·DIDM(4g)이며, 대기열에는 아직 옛 Claude 브랜치가 적혀 있다. 메인은 이번 **GPT 브랜치/최신 SHA**로 이어받아 대기열을 갱신해야 한다.
2. 차례에 맞춰 최신 main을 해당 브랜치에 merge하고 §9의 검증을 수행한다. DS·DIDM은 DS-H 병합 후 main을 다시 합친다. CI workflow의 기존 main 검사와 DIDM/홈 검사를 모두 보존한다.
3. 각 PR 직전 마지막에 compliance 기준선 갱신·check를 수행한다. 새 파일로 20개 문서 재검토 대상임을 PR에 명시한다. 독립 검토·CI 확인·병합 및 LEDGER/WORKBOARD 완료 기록은 메인이 처리한다. 현재 `done_ids: none`은 아직 main 병합 전이라는 뜻이다.
4. 앱 UI 연결·실제 정답 집합 채점·모형 유의성/초과수익 검증·TRADEGEN 적용은 이번 구현 검증과 구분해 후속 배정한다. 합성자료 정확도 1.00을 실제 성과로 간주하지 않는다.

**소유자 결정 사항 (확정과 미결 구분)**
- 확정: RavenPack 대안 9개를 뜻하는 “3단계” 해석, 공식 무료 소스 추가, Kalshi 선택. Alpha Vantage·Tiingo·CryptoPanic 뉴스는 무료 이용 불가 확인 후 보류; OA-08 무료 키 확인은 종료되어 재요청하지 않는다.
- 확정: 사전등록 V0 승인, 기존 범주를 포괄하는 사건 유형14개, 신규성을 다변량 모형으로 평가, 확률 문턱0.75·목표 정확도0.90, 자체 개발 LLM 포함 학습 cutoff 규칙. PREREG_V0 원문은 보존했다.
- 미결 OA-09: 소유자 PC 홈 지표 진단 출력. 미결 OA-10: 신규성 다수 범주 대비 보조 조건, 자체 LLM 기반 모델·학습 cutoff, 평가표 판단(c) 확인.
- 미결 OA-38: RavenPack 견적/Bigdata 비교를 계획에서 제외한 해석 확인. 미결 OA-46: BTC 실시간 KRW와 일별 USD의 표시 단위 결정. 이번 인계에서 새 결정을 추정하거나 새 소유자 질문을 만들지 않는다.
- 최신 확정: **QUANTGEN 메인 Codex가 총괄하며 이 세션의 새 구현은 중단한다.**

초기 연구 보고서 산출물도 보존되어 있다: `/workspace/didm_output/02_DIDM_Research_Methods_v02_Illustrated.{pdf,md}`, `03_DIDM_Initial_Specification_v02_Illustrated.{pdf,md}` (네 파일 존재 확인). 이 보고서 파일은 코드 브랜치의 원격 반영 대상과 구분되는 로컬 산출물이다.

이 문서는 메인이 읽을 수 있는 공용 handoff 보고다. 다른 채팅으로 직접 메시지를 보냈다는 뜻은 아니다. 중앙 CURRENT·다른 세션 문서·원장·제품 코드는 이번 인계에서 수정하지 않았다.

---


**최신 2026-11-21 GPT 검토 완료 / 병합 차례 대기 (2026-11-21T11:03:55+09:00):**
- DS-H: `gpt/ds-home-indicators-20261121` @ `7ce37917102af9793d3ccbe851c0554058089df9` (main `f065ec9` merge `107fee4`). KIS 준비상태 확인 오류를 실시간 한 행으로 격리하고, 중간 이력 날짜까지 검증. 홈23을 포함한 홈·gateway·credentials·연구계약 **131 tests PASS**.
- DS·DIDM: `gpt/data-source-didm-20261121` @ `87812679aec6f333d91b867f5892e523e0da9b0c` (main `f065ec9` merge `80d79d8`). 신규성 정답/확률 입력·차원·범위 검증, UTC/DST 시각 일관성, 동일시각 분할 거부, 사전등록의 동일종목 AND 동일유형 조건, GDELT/FinBERT 완료 시각 기록, ALFRED 전체 pagination·오류 격리, 점수 단위 문구를 수정. **DIDM 132 tests PASS**; 공급사 대조 **147 tests PASS**; 원본 엑셀 변경 **0칸**.
- 두 브랜치 push 완료, 작업 트리 깨끗함. Claude 원래 브랜치·중앙 CURRENT·WORKBOARD·MERGE_QUEUE·LEDGER는 변경하지 않음. **main 미병합, PR 없음.** 로드맵 ID는 병합 전이므로 완료 원장에 추가하지 않음.
- 최신 queue의 4e(OS-F2) → 4f(DS-H) → 4g(DS·DIDM)를 지킴. 메인은 이제 위 **GPT 브랜치**를 이어받아야 하며, 오래된 Claude head에서 별도 수정을 시작하면 이번 보완이 빠짐.
- 변경 근거·시험·한계: DIDM 브랜치 `docs/didm/IMPLEMENTATION_REVIEW_2026-11-21.md`; 홈 계약 `docs/product/HOME_INDICATORS_DATA_2026-11-20.md`.
- 실제 공급사 호출·LLM 다운로드/유료 호출·실제 정답집합·초과수익 검정은 하지 않음. 신규성 1.00은 합성자료 시험값뿐. 확률0.75·목표정확도0.90·70/30·ridge1e-3 유지, PREREG_V0 파일 불변.
- 기존 소유자 입력 OA-09/OA-10/OA-38/OA-46만 유지. 새 수동 작업 요청 없음. 무료 뉴스 키 재발급/가입은 이미 닫힌 OA-08이므로 다시 요구하지 않음.
- **아래 11-20 이전 기록의 빈 체크박스·§6 과거 실행명령·§8 무료키 문구는 당시 이력이다. 현재 상태는 이 문단과 §9를 우선한다.**


**2026-11-21 GPT 인수:** 소유자 요청으로 이 세션 전용 범위를 인수함 (`didm-gpt-20261121-6af7214e`). DS-H `f80b3b0`와 DS·DIDM `c206b10`을 별도 `gpt/` 브랜치에서 검증·검토·필요한 수정 후 push한다. 중앙 CURRENT/대기열/원장은 메인 세션 소유로 유지. PR은 4e → 4f → 4g 순서를 따른다. 다른 Codex 채팅으로 직접 보내는 도구가 없어 이 파일의 `메인에게` 절로 결과를 공유한다.

**2026-11-20 인계 (주간 사용량 98%, 메인 지시 05:3x KST):** 새 작업 없이 멈춤. 두 브랜치 모두 push·깨끗함.
- `claude/ds-home-indicators-20261120` @ `f80b3b0` — DS-H (`load_home_indicators`), 대기열 **4f** (OS-F2 4e 뒤).
- `claude/data-source-didm-20261117` @ `c206b10` — DS·DIDM 전체 (평가표, 사전등록 V0 승인, 스키마, 신규성 모형, 공급원 9개 연결, 키 = core.credentials), 대기열 **4g** (DS-H 병합 뒤 main 다시 합침).
- 두 PR 모두 메인이 MERGE_QUEUE에 "병합: DATA_SOURCE_DIDM"을 적은 뒤에만: 최신 main merge → DIDM/DS-H 시험 → `python -m tools.compliance.check --refresh-baseline --reviewed-by "<이름>" --review-note "<12자 이상>"` (맨 마지막) → `--check` PASS → PR (새 파일 추가로 20개 문서 재검토 대상임을 PR 본문에).
- 재개: 2026-11-24 17:00 KST (Claude) 또는 소유자가 GPT에게 이어받으라고 할 때.
- 열린 소유자 일: OA-09 (홈 지표 진단 출력), OA-10 (a)(b)(c), OA-38 (DS-3 계획 제외 확인), OA-46 (BTC 단위). 이 세션 쪽으로 온 답은 인계 문서 8절·1.x절에 원문으로 기록.

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
- [x] DS-H 코드 (메인 배정 2026-11-20 03:27 KST, KEY-4 main `8445187` 뒤): 별도 브랜치 `claude/ds-home-indicators-20261120` @ `f80b3b0`. `core/research/markets.py` `load_home_indicators(days)` (일별 6개 한 번 호출 `gateway.ficc().load_many`, 행마다 기록·표시권·지연, 실시간 BTC Upbit KRW·KOSPI KIS (키 있을 때만), 합성 값 거부, 주입 가능), `tests/home_indicators_acceptance.py` 20 OK, 화면용 계약 `docs/product/HOME_INDICATORS_DATA_2026-11-20.md`, runtime-smoke 줄. 회귀: 게이트웨이 경계·같은 답·main·원격·자격 증명·홈·연구 계약 = 브랜치 177 OK, main 157 OK (실패 집합 같음). `load_markets` 그대로. PR은 메인이 대기열 자리 정한 뒤. OA-09 진단 오면 원인 구분을 계약 문서에 더함. 소유자 결정 거리: BTC 실시간 원화 vs 일별 달러 (지금은 따로 표시).
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

**[DATA_SOURCE_DIDM → 메인] 완료 보고: 기존 DS-H·DS·DIDM 브랜치 검토·수정·오프라인 재검증 (main 병합 전)**
- 브랜치/커밋: DS-H `gpt/ds-home-indicators-20261121` @ `7ce37917102af9793d3ccbe851c0554058089df9`; DIDM `gpt/data-source-didm-20261121` @ `87812679aec6f333d91b867f5892e523e0da9b0c`. PR 없음.
- 검사: DIDM132, 홈·공통131, 공급사147 모두 PASS; Excel0변경; diff --check PASS. 신규성 독립 재검토26 PASS, 미해결 중대 지적 없음.
- 다음: 4e 뒤 4f를 위 GPT 홈 브랜치로 진행. DS-H 병합 뒤 GPT DIDM 브랜치에 최신 main merge → 관련 검사 → compliance 기준선 마지막 갱신/check → 4g PR. 20개 compliance 문서 재검토 대상 표시 필요.
- 소유자 손이 새로 필요한 일: 없음. 기존 OA 항목 유지.
- 공용 파일로 보고를 기록했으며, 다른 채팅 직접 메시지는 지원 도구 부재로 보내지 못함.


**2026-11-21 GPT checkpoint:** DS-H는 `gpt/ds-home-indicators-20261121` @ `7ce37917102af9793d3ccbe851c0554058089df9`로 push/read-back 완료. main `f065ec9` merge (`107fee4`), KIS 준비상태 예외 행 격리·잘못된 이력 날짜 거부 수정, 홈/게이트웨이/키/연구계약 131 tests PASS (홈23 포함, fixture/소켓 차단). 4e OS-F2 뒤 이 GPT 브랜치를 사용하세요. DS·DIDM은 최신 main merge `80d79d8` 위 입력검증·시점 누출·ALFRED pagination·사전등록 정의 일치 수정 마무리 중; 완료 SHA는 다음 checkpoint에 기록. PR/기준선은 대기열 차례에만. 이 파일은 공유 보고이며 다른 채팅 직접 메시지 전달은 아님.

- 대기열 요청: DS·DIDM 첫 코드 PR 자리 (F21 뒤). 묶음 = 작업 브랜치 전체 (`docs/didm/**`, `core/didm/**`, `data/didm/**`, `tools/didm/**`, `tests/didm_*`, `tests/fixtures/didm/**`, 공유 파일 `runtime-smoke.yml` 경로·시험 줄, `docs/compliance/08-third-parties.md` 행). 이 PR은 `source-review.json`도 바꿉니다 (한 번에 하나 규칙).
- LEDGER: 아직 요청 없음 (병합된 ID 없음). 병합 뒤 `--done` 문자열을 여기에 적습니다.
- 질문 1~4 답은 소유자가 이 세션에 직접 줌 (1.1절). "3단계" = DIDM Stage 3이 아니라 대안 9개라는 답은 `D14_RAVENPACK_ALTERNATIVES.md` 1절 해석과 다르니 메인 문서도 고쳐 주세요.

## UI 세션에 전할 것

- 없음 (DS-H는 진단 출력 뒤 시작; `load_home_indicators()`가 병합되면 소유자를 통해 "홈 화면 시작 가능"을 알림).

## 결제·계정 세션에 전할 것

- (2026-11-19) 데이터소스 쪽 준비 끝: `data/didm/keys.py`가 `credentials.names.is_secret(name)`이 참이면 `credentials.get/status/set`을 씀. KEY-3 브랜치 `8a2886b`의 `RESEARCH` 9개와 이름이 같음 (`data.didm.keys.RESEARCH_KEYS`). KEY-3 PR이 main에 들어가면 데이터소스 쪽 코드 수정 없이 저장소 경로로 바뀜. 따로 요청할 것 없음.

- 새 키 이름 (값 없음, 제안): `FRED_API_KEY` (DS-4a ALFRED, 연구 도구 전용), `ECOS_API_KEY`, `SEC_EDGAR_USER_AGENT` (연락처 문자열; DS-4d), OpenDART는 기존 `OPENDART_API_KEY` (`data/didm/opendart.py`가 `OpenDARTClient._get` 사용), DS-4b용 `ALPHAVANTAGE_API_KEY`, `TIINGO_API_KEY`, `CRYPTOPANIC_API_KEY`; Stage 2 뒤 `CME_FEDWATCH_API_ID`, `CME_FEDWATCH_API_SECRET`; Stage 3 뒤 `TRADINGECONOMICS_API_KEY`.
- `routes.json` 행: 지금 없음. DIDM 수집은 `tools/didm/` 연구 도구라 게이트웨이 대상 아님 (D7 5.5). 앱이 DIDM 결과를 쓰게 되면 그때 공급원마다 한 행 요청.

## 9. 이어받는 메인 Codex에게 주는 지시문

**이 절의 실행 담당은 QUANTGEN 메인 Codex다. DATA_SOURCE_DIDM 세션은 최신 소유자 지시에 따라 새 구현을 중단했으며, 인계 파일 상태나 기존 큐만으로 스스로 재개하지 않는다.**

1. 소유자의 이번 작업 지시 범위에서만 재개한다. 이 문서 상태 자체는 자동 인수 신호가 아니다. 중앙 CURRENT와 DATA 전용 파일의 execution 소유권을 확인한다.
2. SESSION_PIPELINE, 최신 MERGE_QUEUE, WORKBOARD 2.4, LEDGER를 읽는다. 현재 완료 ID는 main 병합 전이므로 원장에 없다. 다른 담당의 taken은 선점하지 않는다.
3. 보호 캐시 없는 sparse checkout에서 **GPT 브랜치**를 쓴다: DS-H `7ce37917102af9793d3ccbe851c0554058089df9`, DIDM `87812679aec6f333d91b867f5892e523e0da9b0c`. Claude의 원래 브랜치에 이번 수정이 들어 있다고 가정하지 않는다.
4. 메인의 기존 배정 범위에서 4e → 4f → 4g 순서. 4f에서는 최신 main을 홈 브랜치에 merge. 4g에서는 DS-H가 병합된 최신 main을 DIDM 브랜치에 merge. runtime-smoke 충돌은 최신 main 경로/시험 + 해당 DS-H/DIDM 경로/시험을 모두 보존한다. rebase/force push 금지.
5. DIDM 검사:
   `python -m unittest tests.didm_schema_acceptance tests.didm_vendor_eval_acceptance tests.didm_store_acceptance tests.didm_ingest_acceptance tests.didm_sources_acceptance tests.didm_novelty_acceptance tests.didm_news_acceptance` → 132 PASS (추가 수정 전 기준).
   `python -m tools.didm.check_vendor_eval --excel <handoff 엑셀 사본>` → Excel cells changed 0.
6. 홈 검사:
   `python -m unittest tests.home_indicators_acceptance tests.gateway_boundary_acceptance tests.gateway_same_answer_acceptance tests.gateway_main_acceptance tests.gateway_remote_acceptance tests.credentials_acceptance tests.research_home_acceptance tests.research_contract_acceptance` → 131 PASS (홈23 포함).
7. 공급사 대조:
   `python -m unittest tests.provider_parity_acceptance tests.provider_parity_btc_diagnose_acceptance` → 147 PASS. 임시 출력 경로는 git 작업 트리 밖이어야 함. 이번 환경은 /tmp/.git 및 /workspace/.git 표식으로 139개가 기존main/작업브랜치 동일하게 실패했으나, **TMPDIR=/dev/shm/didm-verification**에서 147 모두 PASS. 경로 보호 코드를 약화하지 않는다.
8. 검사는 실제 .env 자동 로드·사용자 키링·네트워크를 차단하고 fixture만 사용한다. 이번 스크래치 실행기: `/workspace/didm_work/resume_20261121/run_offline.py` (DIDM), `run_regression.py` (공통). 다른 환경에서는 동등한 격리를 설정한다. HOME 변수 변경, tests/run_all, macro_m8/m9, qa/acceptance_results.json 재생성 금지.
9. PR 차례가 오면 마지막에 compliance `--refresh-baseline --reviewed-by "<담당>" --review-note "<구체적 검토>"` → `--check` PASS. 새 파일 때문에 20개 문서 재검토 대상임을 PR에 기재. 이 시점까지 기준선은 의도적으로 갱신하지 않았으며 **compliance 통과/PR CI 통과를 주장하지 않는다**.
10. 병합은 메인 담당. UI/웹사이트/연구 브랜치·키/게이트웨이 코어, 실제 원장·보호 캐시·비밀 파일·유료 호출은 범위 밖. 앱 표시 연결과 실증연구는 별도 다음 작업이다. 작업 완료마다 DATA 파일을 CAS로 갱신하고 read-back한다.

## 10. 결과 확인 방법

```
git fetch origin claude/data-source-didm-20261117
git switch --detach origin/claude/data-source-didm-20261117
python -m unittest tests.didm_store_acceptance tests.didm_ingest_acceptance tests.didm_schema_acceptance tests.didm_vendor_eval_acceptance   # 52 OK
python -m tools.didm.check_vendor_eval --excel <(git show origin/handoff:plans/2026-11-17/OWNER_EXCEL_RAVENPACK_ALTERNATIVES.txt)   # excel cells changed: 0, OK
```
