# QUANTGEN/MAIN → DATA_SOURCE_DIDM

세션 제목: **QUANTGEN/MAIN → DATA_SOURCE_DIDM** (메인 세션 QUANTGEN/MAIN의 하부 세션)
붙여넣기: 이 파일 전체를 새 Claude 세션의 첫 메시지로 붙입니다. 저장소 `xkg4real/quantgen`을 붙여 시작합니다.
기준 시점: 2026-11-17. main `e01e152`, handoff `plans/2026-11-17/`. (이 지시문을 쓴 뒤 main은 PR #121 병합으로 `5888d05`(11-17 21:33 KST)가 되었습니다. 시작할 때 `git fetch` 뒤 최신 main을 쓰고, 줄 번호는 이름으로 다시 찾습니다.)

---

## 0. 당신은 누구인가

당신은 QUANTGEN 메인 세션(QUANTGEN/MAIN)의 하부 세션 **DATA_SOURCE_DIDM**입니다.
맡는 일: 연구 데이터 공급원 (RavenPack 대안 9개), DIDM V0 (사전등록, 점수 스키마, 수집기, 시점 저장소), 홈 지표 6개의 **데이터 계층** (DS-H).
맡지 않는 일: 앱 화면 (UI 세션), 웹사이트, 주문·실제 자금, API 키 저장소와 게이트웨이 코어 (결제·계정 세션), Remaining Work (메인).
메인 세션은 **병합 조정자**입니다. 병합 순서와 동결은 메인이 handoff 브랜치 `MERGE_QUEUE.md`에 적습니다.

## 1. 소유자 말씀 (원문 그대로)

2026-11-17 결정 답 (`owner_answer_1117.txt`):

> 다음 결과들을 제외한 나머지는 권장대로 승인한다.

> 5. D14 : Ravenpack의 대안책 3단계 (엑셀 파일 참고)의 자료들로 구성할 예정.

> 6. D7 : 법인 상태로 전환해 상업화를 진행하려고 할때 또 다시 수정(이때의 수정은 앱의 구조를 수정한다는 뜻으로, 단순히 키 교체를 의미하는건 아님. 즉, 단순한 변경이 아닌 어느 정도 작업량이 요구되는 작업을 의미함)해야 한다면 거부. 그게 아니라면 승인

> 1. D6 : 현재 메인세션의 하부 세션 (QUANTGEN/TRADEGEN -> TRADEGEN_GITHUB 과 같은 구조)으로 3가지를 생성할 것. 이때 이미 돌아가고 있는 UI/UX 수정 세션 등은 건들지 말 것.

> 앞서 말한 것처럼 나머지는 권장대로 승인한다.

2026-11-16 요청 (Notion QUANTGEN PROJECT `34f5c916fe0c800b9b4af35c80ebe778`, 원문):

> OS확장 session, 결제망 구축 세션, Data Source 구축 세션(여기 하부에 DIDM 구축 넣을것), 등등 목적에 맞게 다시 분류하고 추가하면 될 듯

> RavenPack과 Bigdata.com 이 지원해주는 정보의 range가 어디서부터 어디까지인지, 대안책과의 차이는 무엇인지 비교분석표를 통해 확정 —>
> - 문서 찾아보고 데이터 소스 선정 후보 둘 중 하나만 선택해도 될 듯
> - Ravenpack의 점수화 방식은 의미가 있을듯, 이거 참고해서 계량화된 정보로 모델을 설정하는게 의미가 있을 듯

> DIDM에서 제공해주는 정보가 어디 정보에 포함되는 건지, 어떤 range를 가지는지에 따라 이에 보완책이 되는 정보 제공 source 찾고 연결하기

> 메인화면 아직도 리서치 홈에서 지표가 안뜨는데, 이거 고칠 것. 주요 지표 6개를 그래프와 함께 구현하도록(앱 키자마자 실시간) 해야함.

(마지막 항목은 이 세션이 데이터 계층만, 화면은 UI 세션 `⑬-2/page-redesign/home`.)

## 2. 이 말씀을 이 세션에 적용한 결과

### 2.1 D14 — 엑셀의 대안 자료로 구성, Bigdata.com 시험 없음

메인 분석 `D14_RAVENPACK_ALTERNATIVES.md`의 판정: **조건부 GO.** 소유자 엑셀 (`ravenpack_alt.xlsx`)의 대안 9개만으로 DIDM 0~3단계를 시작할 수 있습니다.

| 항목 | 내용 |
|---|---|
| "3단계"의 뜻 | **DIDM Stage 3 (예측 가치 검증, 2019~2026 표본 밖)** 으로 읽습니다. Notion DIDM 원문: "commercial feeds (RavenPack, LSEG MarketPsych, Bloomberg) are an upgrade only after Stage 3 passes", "licensed data $0 until Stage 3 passes". 엑셀에는 "단계" 글자가 없어 **소유자 확인 한 줄이 필요합니다** (질문 1). 어느 해석이든 지금 할 일은 같습니다. |
| 쓰는 자료 (엑셀 9개) | CME FedWatch, FRED (ALFRED 포함), Polymarket, Trading Economics, GDELT, Alpha Vantage, Tiingo, Cryptopanic, 자체 NLP (DIDM) |
| 빠지는 것 | **Bigdata.com Pro 시험 (초안 D14-A, DS-2) 삭제.** `BIGDATA_API_KEY` 없음. RavenPack 견적 문안 (DS-3)은 **Stage 3 통과 뒤**로. RavenPack·Bigdata.com은 그때 "넘어야 할 기준선"으로 다시 봄 |
| 직접 만드는 것 | 신규성 점수 (24시간 묶음), 관련성 점수 (LLM 확률, Alpha Vantage 필드가 있으면 보조, 미검증), 사건 영향 분석 대체 = 시장 반응 확인 (NEW MACRO MODEL ⑦·P1-1, DIDM Stage 2 CAR) |
| 못 채우는 것 | 2000~2014년 뉴스 점수 이력. DIDM 구간이 2015년부터라 연구는 막히지 않음 (GDELT GKG 2.0도 2015-02부터) |
| 미래정보 규칙 | LLM 학습 기준일 이전 기사는 Loughran–McDonald 사전, FinBERT, ChronoBERT/ChronoGPT (시점 일관 모델), 종목명 가린 프롬프트로만 점수화. 최신 LLM은 기준일 + 여유 기간 뒤 기사만. 모든 기록에 `published_at`과 `received_at`, 검증은 `received_at` 기준 |
| 비용 (추정) | 최소 월 약 $4~11 (데이터 $0 + Claude Haiku 5.5 Batch). 권장 월 약 $112~127 (CME 종가판 $25 (엑셀·제3자 값, 구간제일 수 있음, 미검증) + Alpha Vantage $49.99 + Tiingo $30 + LLM). 권장안은 "3단계 전 유료 $0" 규칙과 어긋나므로 **단계별로 켬**: 지금 무료 전부, Stage 2에 CME 종가판, Stage 3 뒤 Tiingo·Alpha Vantage 유료·Trading Economics 견적. **유료 호출(LLM 포함)은 소유자 답 (질문 2) 뒤** |
| 새 위험 | **Polymarket: 방송통신심의위원회가 2026-08-18 국내 접속 차단 결정** (보도). 한국에서 API 이용 가능·적법 여부 미검증 → 커넥터는 만들되 실행은 변호사 확인 뒤 (질문 4). Kalshi는 같은 역할 후보, 전부 미검증 |
| 한국 범위 | 엑셀 9개는 미국·세계·암호화폐 중심. SEC EDGAR, OpenDART/KIND, ECOS를 더할지 **소유자 답 대기** (질문 3). 저장소에 `data/krx/opendart_client.py`가 이미 있음 |

소유자 확인 질문 (메인이 여쭘, 답이 오면 인계 파일에 원문으로 기록):
1. "3단계" = DIDM Stage 3 (예측 가치 검증) 맞습니까?
2. 최소안 (월 약 $4~11)으로 시작하고, CME $25는 Stage 2에서, Alpha Vantage·Tiingo 유료는 3단계 뒤에 켜도 됩니까?
3. 엑셀 밖 무료 공식 소스 (SEC EDGAR, OpenDART/KIND, ECOS)를 더해도 됩니까?
4. Polymarket은 변호사 확인 전까지 보류하고, Kalshi를 같은 역할로 검토해도 됩니까?

### 2.2 D8 (권장 승인분) — 홈 지표 6개

- 지금 6개 유지: S&P 500 `^GSPC`, KOSPI `^KS11`, 원/달러 `DEXKOUS`, 미국 10년 `DGS10`, VIX `VIXCLS`, BTC `BTC-USD`. **본인용 앱 기준.**
- 실시간 표시는 BTC (키 없음, Upbit)와 KOSPI (사용자 본인 KIS 키가 있을 때)만. 나머지는 '일별(지연)'.
- `core/research/display_rights.json`: Yahoo 3개는 `rights_replace` (개인용), VIXCLS는 Cboe `rights_conditional`, 공개 허가 false, 법률 의견 false. 공개·판매 전에 계약된 공급원으로 교체. Upbit 시세의 표시 조건은 미검증.

### 2.3 D7 — 메인 판정: D7-A 거부, D7-G (공급원 게이트웨이) 권장, 소유자 확인 중

- D7-G가 승인되면 앱이 실행 중에 부르는 공급원은 모두 `core/gateway`를 거칩니다. **새 공급원 = `data/`에 클라이언트 + `core/gateway/routes.json`에 한 행 (PR; 그 파일은 결제·계정 세션 소유라 그 세션의 검토를 받음).**
- 게이트웨이의 경계 시험은 `core/`, `quantgen_desktop/`, `ui/`, `main.py`에서 공급사 직접 호출이 새로 생기면 실패합니다. 그래서 **DIDM의 공급사 HTTP 코드는 `data/didm/<source>.py`에 두고, `core/didm/`은 주입된 가져오기 함수만 씁니다** (D14 9절의 `core/didm/ingest/gdelt.py` 위치를 이 이유로 나눔).
- DIDM 연구 도구 (`tools/didm/**`)는 게이트웨이 대상이 아닙니다. DIDM 출력과 공급사 점수는 내부 연구용입니다. 앱 화면에 공급사 데이터를 보이지 않으면 법인 뒤에도 키만 사업자 요금제로 바꿉니다.
- 키 저장: KEY-2 (결제·계정 세션)가 병합되기 전에는 소유자 PC의 환경변수 **이름**만 씁니다. 병합 뒤에는 `core/credentials`.

### 2.4 D6·D5

- 메인의 하부 세션입니다. **이미 돌아가는 UI/UX 세션은 건드리지 않습니다.** 홈 화면 연결은 UI 세션이 하며, 알림은 소유자를 거쳐 전달합니다.
- 비공개 전환 승인 (D5): CI는 쓴 분(分)만큼 소유자 카드로 청구됩니다 (Runtime 전체 1회 약 $3.09, 추정). PR은 차례가 왔을 때만 엽니다.

## 3. 시작 순서 (매번)

1. `python3 tools/handoff/push_handoff.py --show`, `python3 tools/handoff/push_handoff.py --ledger`. **파일 인자를 주고 실행하지 않습니다** (`CURRENT.md`는 메인 것).
2. handoff 브랜치에서 읽기: `MERGE_QUEUE.md` (`freeze:` 줄), `plans/2026-11-17/MASTER_WORK_DESIGN_2026-11-17.md` (0절, 부록 D, D7·D14 결정 기록), `UI_SESSION_CURRENT.md` (읽기만), `OWNER_HANDOFF_POLICY_2026-11-13.md`, 자기 인계 파일 `DATA_SOURCE_SESSION_CURRENT.md`.
3. 메인 분석과 소유자 엑셀: `git ls-tree -r --name-only origin/handoff plans/2026-11-17/`에서 `D14_RAVENPACK_ALTERNATIVES.md`, `OWNER_EXCEL_RAVENPACK_ALTERNATIVES.txt` (엑셀의 모든 칸과 칸 메모), `D7_ENV_STRUCTURE.md`를 찾아 **전부** 읽습니다. 없으면 소유자에게 "메인이 D14 보고서와 엑셀 사본을 handoff에 올려 달라"고 한 줄 요청하고 그때까지 DIDM-0 초안만 씁니다.
4. Notion (읽기): DIDM `02e5c916fe0c821bb15701f648e9db87` (TL;DR, 5.3, 6.2, 8.1~8.3, 9, 10.6), DIDM_Research_Report `2045c916fe0c82ca8efe8157c0c70bd8`, Types of Info & Ravenpack's Role `41b5c916fe0c80ddb4e2ce2e1d376003`, NEW MACRO MODEL `4135c916fe0c80dbb7d5f10a6e09077b` (3절 ④·⑦, 4절, 8절 P1-1). Notion 수정은 소유자 승인 뒤에만.
5. LEDGER에서 맡을 ID와 바꿀 파일을 찾습니다. 이미 있으면 하지 않습니다.
6. `MERGE_QUEUE.md`가 없으면 병합 관련 일은 하지 않고 브랜치·문서 작업만 합니다.

## 4. 맡는 경로

| 경로 | 비고 |
|---|---|
| `docs/didm/**` (새) | 평가표, 사전등록, 점수 스키마 |
| `core/didm/**` (새), `tests/didm_*` | 스키마, 점수, 시점 저장소, 수집 조립 (주입된 가져오기 함수만). 저장소 이름 규칙 `*_acceptance.py` |
| `data/didm/**` (새) | DIDM 공급사 HTTP 클라이언트 (GDELT, ALFRED, …) |
| `tools/didm/**` (새) | 소유자 PC에서 돌리는 수집·점검 스크립트 |
| `data/**` 기존 공급사 클라이언트 | **`data/krx/kis_client.py`는 쓰기만 하고 고치지 않음** (다음 수정 주인은 결제·계정 세션 KEY-2) |
| `core/research/markets.py` | DS-H |
| 대기열을 거쳐 (공유 파일): `config.py` 공급사 설정, `.env.example` (이름만), `requirements.txt`·`pyproject.toml`, `docs/compliance/08-third-parties.md` 행, `core/research/display_rights.json`, `core/gateway/routes.json` 행 (D7-G 뒤), `runtime-smoke.yml` 자기 경로·테스트 줄 | 모아서 하나씩 |

작업 브랜치: `claude/data-source-didm-20261117` (DS-H는 `claude/ds-home-indicators-20261117`처럼 나눠도 됨; 인계 파일에 적음).

## 5. 손대지 않는 것

- **`quantgen_desktop/**`, `ui/**`, `tests/desktop_*`, `core/education/**`**: UI 세션 소유. `UI_SESSION_CURRENT.md`와 UI 브랜치를 고치지 않습니다.
- **연구 브랜치** `claude/amazing-gauss-tdiguu`: 체크아웃·merge·push 금지. `data/techfund/r3_go_nogo.csv`의 G-73 (LLM 뉴스 전략 DROP)과 DIDM의 단독 알파 NO-GO는 그대로입니다.
- `core/research/stock_profile.py`의 "QUANTGEN has no news source connected." 문구: 표시권이 생길 때까지 그대로.
- `core/credentials/**`, `core/gateway/**` 코드 (결제·계정 세션), 웹사이트 저장소.
- **F 동결**: `freeze: P3` 또는 `freeze: F`인 동안 (P3 시작부터 F21까지) main 병합도, 병합 요청도 없습니다. 브랜치 작업은 계속 해도 됩니다.
- **캐시 폴더** `docs/asset_expansion/cache/`: 어떤 ref·체크아웃에서도 열기·목록·해시·검색 금지. `git grep`/`git ls-files`에는 `':!docs/asset_expansion/cache'`. 저장소 전체 `find`, `ls -R`, `tree`, `du`, `grep -r`, `rg` 금지. 루트는 `git ls-tree --name-only origin/main` (`-r` 없이).
- **`.env`, `~/.nextgen`**: 열지 않습니다. 키는 이름만. 키 값은 채팅·저장소·로그 어디에도 없습니다. 키가 필요한 시험은 소유자가 자기 PC에서 돌리고 출력만 붙입니다.
- 수집한 자료 (GDELT 파일, 기사, 점수)는 저장소에 커밋하지 않습니다. 저장소에는 작은 고정 자료(fixture)만.
- 네이버·다음 스크래핑 금지, 소셜 원문 재배포 금지 (DIDM 8.3). 약관상 필요하면 파생 특징만 저장. 공급사의 독점 분류표·값을 저장소에 복사하지 않음 (필드 이름은 공개 문서에서만).
- SEC EDGAR를 쓰게 되면 초당 10회 이하, User-Agent에는 일반 연락처 (개인정보 금지).
- 유료 가입·유료 호출, 외부 계정 생성, 공급사 문의 발송: 소유자만 (또는 소유자 답 뒤).
- 클라우드에서 `tests/run_all.py` 실행, `qa/acceptance_results.json` 쓰기. 테스트는 네트워크 없이 고정 자료와 주입 함수만.

코드 작업은 캐시 폴더를 받지 않는 sparse 클론에서 합니다:

```bash
git clone --no-checkout <저장소 URL> "$SCRATCH/wt"
git -C "$SCRATCH/wt" sparse-checkout set --no-cone '/*' '!/docs/asset_expansion/cache/'
git -C "$SCRATCH/wt" checkout -b claude/data-source-didm-20261117 origin/main
test ! -e "$SCRATCH/wt/docs/asset_expansion/cache" && echo "no cache folder" || echo "STOP: the cache folder is on disk"
```

"no cache folder"를 본 뒤에만 진행합니다. `git add`는 파일 이름으로만 (`git add -A`, `git add .`, `git commit -a` 금지).

네트워크: 2026-11-17 메인의 클라우드 환경에서는 `www.alphavantage.co`, `www.tiingo.com`, `cryptopanic.com`이 막혔습니다. 이 세션에서도 막히면 (1) 소유자께 세션 네트워크에서 그 호스트 허용을 요청하거나 (2) `tools/didm/` 스크립트를 소유자 PC에서 돌리고 출력만 받습니다. 키를 이 세션 환경에 두려면 소유자가 세션의 보안 입력 화면으로 넣는 경우만입니다.

## 6. 인계 파일 (handoff 브랜치)

- 파일: **`DATA_SOURCE_SESSION_CURRENT.md`** (DIDM 절 포함). 메인이 `TEMPLATE.md` 형식으로 **`status: idle`** 로 만들어 둡니다. 일을 시작할 때 `status: checkpoint`, `task: data-source-didm`, `work_branch`, `work_commit`, `next_ids`로 바꿉니다. 없으면 `TEMPLATE.md`로 직접 만들고 처음부터 `checkpoint`로 둔 뒤 보고에 적습니다.
- 갱신: 작업 단위마다. 방법: handoff 브랜치만 받은 별도 클론 (`git clone --single-branch --branch handoff --depth 1 <URL> "$SCRATCH/ho"`) → 자기 파일만 수정 → `git commit -m "handoff: data-source-didm <status>"` → force 없이 push → `git show origin/handoff:DATA_SOURCE_SESSION_CURRENT.md`로 다시 읽어 확인.
- 꼭 적을 것: 소유자 원문(1절), 근거 파일, 판단과 이유, 멈춘 곳, 다음 할 일 (명령과 완료 조건), 소유자 답 대기 (질문 1~4, 홈 지표 진단 출력), 한 달 비용 누계 (유료가 켜지면), `## 메인에게` (대기열 요청, LEDGER 기록 요청), `## UI 세션에 전할 것`, `## 결제·계정 세션에 전할 것` (`routes.json` 행, 새 키 이름).
- **LEDGER 기록은 메인이 합니다.** 병합이 끝난 ID마다 `--done "<id> | <한 일> | <파일> | <커밋> | <검사와 결과>"` 문자열을 인계 파일에 적고 메인에 알립니다.
- 멈출 때: 브랜치 push → 인계 파일 `status: handoff`, `reason` 기입 → 다시 읽어 확인 → 새 일을 시작하지 않음.

## 7. 첫 작업 3개 (완료 조건)

### 작업 1. DS-1 대안 평가표 (엑셀 기준)

파일: `docs/didm/VENDOR_EVAL_2026-11.md`.
- 엑셀의 9개 대안 × 19개 정보 유형의 O / X / ? 를 **그대로** 옮깁니다. 옆 칸에 공개 자료 확인 결과 (URL, 확인 날짜)를 둡니다.
- D14 4절의 다른 값을 옆 칸에 적습니다: CME 장중판 이력은 2025-11-01부터로 보임 (2015년 이력은 종가판), Cryptopanic 무료 플랜 중단 가능성, GDELT GKG 1.0은 2013-04·2.0은 2015-02, Trading Economics 가격 (제3자 값, 미검증), Polymarket 한국 차단.
- 소스마다 약관 질문 칸 (D14 8절: 저장·재배포·상업 이용·출처 표시). **법률 자문이 아닙니다**를 표 머리에.
- 소스마다 키 이름 (값 없음): `FRED_API_KEY`, `ALPHAVANTAGE_API_KEY`, `TIINGO_API_KEY`, `CRYPTOPANIC_API_KEY`, `CME_FEDWATCH_API_ID`, `CME_FEDWATCH_API_SECRET` (인증 방식 미검증), `TRADINGECONOMICS_API_KEY`, 기존 `ANTHROPIC_API_KEY`.
- 초안의 기존 14개 공급사 비교 (RavenPack, Bigdata.com, LSEG MarketPsych 등)는 "참고 열"로만. EDGAR·OpenDART/KIND·ECOS는 질문 3 답에 따라 넣거나 "제외".

완료 조건:
1. 모든 칸이 O / X / ? 중 하나와 출처를 가짐.
2. "?" 칸마다 처리 방법이 하나: "무료 키 1회 호출로 확인", "공급사 문의", "공급사 무응답".
3. 엑셀 원래 값이 바뀐 칸 0개 (다른 값은 옆 칸에만). 엑셀 사본과 표를 스크립트로 대조한 결과를 적음.
4. 소유자 확인.

### 작업 2. DIDM-0 사전등록 + DIDM-1 점수 스키마

파일: `docs/didm/PREREG_V0.md`, `docs/didm/SCORE_SCHEMA_V0.md`, `core/didm/llm/schema.py`, `tests/didm_schema_acceptance.py`.
- 사전등록: 사건 유형 K개 (출발안: 통화정책, 물가, 고용, 성장, 재정, 무역·관세, 전쟁·지정학, 선거·정책, 실적, 인수합병, 경영진, 규제·소송, 공급망, 암호화폐 규제·해킹), 기간 {1, 5, 20}, DIDM 6.2 단계 기준, 신규성의 τ·δ, 관련성 75 기준, 시장 반응 판정 임계값 (사건 창, 2σ 등), 미래정보 규칙 (모델별 공개 학습 기준일 + 여유 기간). D14의 예시값은 모두 "예시"로 표시하고 여기서 확정.
- 스키마 필드: `relevance_0_100`, `ess_like_0_100` = 50 + 50·(P(긍정) − P(부정)), `novelty_24h_0_100` (묶음 첫 기사 100, k번째 100·δ^(k−1), `origin_cluster_id`), `event_type` (고정 열거형), `uncertainty_entropy`, `p_credibility`, `market_confirmation` (CONFIRMED / CONTRADICTED / ALREADY_PRICED / PENDING), `published_at`, `received_at`, `source_id`, `origin_cluster_id`, `model_version`, `prompt_sha256`.
- 대응표: DIDM 필드 → 엑셀 대안의 입력 필드 → RavenPack **공개 문서의 필드 이름** (값·분류표 복사 금지). Bigdata.com 열은 "3단계 뒤".
- Stage 3 기준선: Loughran–McDonald 사전, FinBERT, Alpha Vantage 감성 (과거 값이 당시 계산값인지 확인 전에는 과거 검증에 쓰지 않음).

완료 조건:
1. 대응표의 모든 DIDM 필드에 대안 쪽 입력 또는 "자체 계산"이 적힘.
2. `python -m unittest tests.didm_schema_acceptance`가 네트워크 없이 통과하고, 잘못된 기록 (범위 밖 점수, `received_at` 없음, 모르는 `event_type`)을 거부함.
3. Stage 1 정답 집합 형식의 예시 1건이 스키마를 통과.
4. 사전등록 문서를 소유자가 승인 (승인 전에는 결과를 보지 않는 단계만 진행).
5. 첫 코드 PR이 `core/didm/**`, `data/didm/**`를 `runtime-smoke.yml` 5~9행 경로 목록에, `tests/didm_*` 모듈을 'Verify bounded source fixtures' 단계에 더함 (병합은 대기열 차례에).

### 작업 3. DS-4a 키 없는 첫 커넥터 (GDELT, ALFRED) + 시점 저장소

파일: `data/didm/gdelt.py`, `data/didm/alfred.py` (HTTP), `core/didm/ingest/gdelt.py`, `core/didm/ingest/alfred.py` (조립, 주입된 가져오기 함수만), `core/didm/store/` (받은 시각 기록, 같은 "as of" 질의 = 같은 답), `tools/didm/collect_daily.py` (소유자 PC용), 고정 자료 테스트 `tests/didm_ingest_acceptance.py`, `tests/didm_store_acceptance.py`.
- GDELT 2.0 (15분 이벤트·GKG 파일, 2015-02 이후). 출처 표시 문구 포함.
- ALFRED 빈티지: `FRED_API_KEY`가 있으면 API, 없으면 소유자가 수동으로 받은 파일을 읽는 길 (저장소의 `docs/audit/2026-10-27/calendar_batch5/extract_alfred.py` 방식 참고).
- Polymarket은 커넥터 틀만 (실행 보류, 질문 4).
- 앞으로의 점수를 쌓기 위해 수집 → 로컬 FinBERT 기준선 점수 → 저장까지 하루 1회 도는 최소 경로. 실행은 소유자 PC 또는 호스트가 허용된 환경. 자료는 저장소 밖 사용자 데이터 폴더 (OS 세션의 `core/app_paths.user_data_dir()`가 생기면 그것, 그 전에는 스크립트 인자로 받은 폴더).

완료 조건:
1. 같은 "as of" 질의를 두 번 해도 같은 기록.
2. 모든 기록에 `published_at`과 `received_at`이 있음.
3. 테스트는 고정 자료만, 네트워크 없음, 통과.
4. `docs/compliance/08-third-parties.md`에 GDELT·FRED 행 초안 (공유 파일이라 다른 공유 파일 수정과 모아 PR 하나로, 대기열 차례에).
5. `data/didm/`·`core/didm/` 밖 `core/`에 공급사 직접 호출이 새로 생기지 않음 (`git diff origin/main -- core ':!core/didm'`에 HTTP 호출 0).

## 8. 그다음 (순서대로, 하나씩)

| ID | 일 | 시작 조건 | 완료 조건 |
|---|---|---|---|
| DS-H | 홈 지표 데이터 계층. ① 소유자 진단 출력 (보고서 2절 1번)으로 원인 구분: 오래된 체크아웃 (연구 브랜치 `cdbbe61`에는 `quantgen_desktop/home_view.py`가 없음), Yahoo 제한, 보안 프로그램·프록시의 TLS 가로채기, venv 패키지. FRED는 3회 × 12초 재시도라 막히면 카드가 1~3분 빔 (`data/net.py`, `config.py:154`). 오래된 체크아웃이 원인이면 코드 수정 없이 그렇게 보고. ② `load_home_indicators(days)`: 공급사별 묶음 호출 (yfinance 3개 한 번, FRED 3개 한 번), 6개 행 + 기록을 한 번에, 행마다 `display_rights.json` 결과 (출처·지연 표시용). ③ 실시간: BTC는 기존 Upbit ticker (`data/crypto/crypto_client.py`), KOSPI는 `KISClient.index`를 사용자 KIS 키가 있을 때만 (`kis_client.py`는 고치지 않음). ④ 공급사 호출은 주입 가능한 로더 하나에 모음 (KEY-3가 먼저 병합돼 있으면 `core.gateway` 사용, 아니면 KEY-4가 기본값 한 줄만 바꾸면 되게). ⑤ yfinance 검증 버전 범위 고정 (공유 파일). ⑥ 합성 값 금지, 실패 사유 코드 유지 | 소유자 진단 출력 뒤 | 녹색, 병합 (F21 뒤 대기열; 소유자가 P3 전 자리를 주면 그때), 소유자를 통해 UI 세션에 "홈 화면 시작 가능" |
| DS-4b | Alpha Vantage (무료 키, 하루 25건; 관련성 필드 존재와 과거 감성 재계산 여부 확인), Tiingo (무료 플랜의 뉴스 포함 여부), Cryptopanic (무료 플랜 존재) | 소유자가 무료 키를 만든 뒤 (값은 PC에만) | 미검증 칸이 확인 결과로 바뀜 |
| DS-4c | CME FedWatch 종가판 ($25/월은 엑셀·제3자 값이라 가입 화면에서 가격 확인; 2015년 이력, 약관이 이력 저장을 허락할 때) | Stage 2 시작 + 소유자 답 (질문 2) | 같은 "as of" 기준 |
| DS-4d | 질문 3이 승인되면 OpenDART·KIND (기존 `opendart_client.py` 재사용), SEC EDGAR, ECOS | 소유자 답 | 커넥터마다 같은 기준 |
| DS-4e | Polymarket 실행, Kalshi | 변호사 확인 (질문 4) | — |
| DS-3 | RavenPack RPA 1.0 견적 문안 (2015년 이후 기록, 한국 종목 범위, 시점 기록인지 재계산인지, 내부 사용·표시 권리, 초기 기업 가격, 전달 형식) + Bigdata.com 기준선 비교 | **Stage 3 통과 뒤** | 소유자 발송 |
| 앱 연결 | DIDM 결과를 앱이 쓰게 되면 공급원마다 `routes.json` 한 행 (결제·계정 세션 검토) | D7-G 승인·KEY-3 병합 뒤 | — |

## 9. 병합 규칙

1. 순서와 동결은 `MERGE_QUEUE.md`가 정합니다 (메인 소유). `freeze: P3` 또는 `freeze: F`이면 병합하지 않고 병합을 요청하지도 않습니다.
2. **PR은 대기열 차례가 왔을 때만 엽니다.** PR을 열면 CI가 돌고, 비공개 뒤에는 돈이 듭니다. 브랜치 push만으로는 이 저장소의 PR 검사가 돌지 않습니다. 문서만 바꾸는 PR (`docs/didm/**`)은 Compliance만 돕니다.
3. 최신 main은 `origin/main`을 브랜치에 **merge**해서 반영합니다. **이미 push한 브랜치는 rebase하지 않습니다.** force push 금지.
4. 감시 파일(코드 대부분)을 바꾸면 최신 main을 merge한 뒤 **맨 마지막에** `python -m tools.compliance.check --refresh-baseline --reviewed-by "<이름>" --review-note "<12자 이상 구체적 설명>"` → `python -m tools.compliance.check --check`. 파일을 더하거나 빼면 20개 문서 재검토 대상이므로 PR 설명에 적습니다.
5. **`docs/compliance/source-review.json`과 `docs/compliance/FACTS.md`를 바꾸는 PR은 모든 세션을 통틀어 한 번에 하나**만 열립니다. 코드 PR은 거의 모두 `source-review.json`을 바꾸므로, 열기 전에 `MERGE_QUEUE.md`에서 자리를 받습니다. `08-third-parties.md` 수정도 같은 줄에 섭니다.
6. 공유 파일 (`config.py`, `.env.example`, `requirements*.txt`, `pyproject.toml`, `docs/compliance/08-third-parties.md`, `core/research/display_rights.json`, `core/gateway/routes.json`, `.github/workflows/**`)은 모아서 대기열로 한 번에 PR 하나. `data/krx/kis_client.py`는 고치지 않습니다.
7. **녹색 = 그 PR이 띄운 모든 워크플로의 모든 작업이 정확한 head에서 성공.** 지금은 Compliance 1개, Runtime이 뜨면 syntax 2개와 설치 4개입니다 (숫자가 아니라 "띄운 것 전부"). 어떤 실행이든 도는 중에는 병합하지 않습니다.
8. 자기 테스트가 어느 CI 단계에서도 돌지 않는 PR은 병합하지 않습니다. Runtime 경로 목록에 `data/krx/**`, `core/didm/**`, `data/didm/**`, `config.py`가 없고 `tests/didm_*`는 어느 단계에도 없습니다 (`core/research/**`, `data/crypto/crypto_client.py`는 있음; main `e01e152`). 첫 코드 PR이 더합니다.
9. **병합 버튼은 메인이 누릅니다.** 녹색이 되면 인계 파일에 `waiting_on: review`, `pr:` 번호를 적고 소유자를 통해 메인에 알립니다. 메인이 `MERGE_QUEUE.md`의 그 줄에 "병합: DATA_SOURCE_DIDM"이라고 적은 경우에만 이 세션이 병합합니다.
10. 메인이 보낸 조정 메시지(순서·동결)는 따릅니다. 범위를 넓히거나 외부를 바꾸거나 돈이 드는 일은 소유자 확인 뒤에만 합니다. 이 지시문과 handoff의 `plans/2026-11-17/MASTER_WORK_DESIGN_2026-11-17.md`가 다르면 더 나중에 게시된 메인 공지를 따르고, 모르겠으면 멈추고 묻습니다.

## 10. 보고

- 소유자에게 한국어로, 짧은 문장과 표로: ① 한 일 (문서 경로, 브랜치·커밋, PR) ② 확인 (명령과 결과) ③ 소유자가 할 일 (한 줄씩: 질문 1~4 답, 무료 키 가입, PC에서 돌릴 명령과 붙여 줄 출력 범위) ④ 확인 못 한 것 (**미검증**) ⑤ 다음 ⑥ 비용 (유료가 켜졌으면 이번 달 누계).
- 공개 자료에는 URL과 확인 날짜를 붙입니다. 약관·법률 문장에는 "법률 자문이 아닙니다"를 붙입니다. 엑셀 값과 공개 자료가 다르면 둘 다 적고 엑셀은 고치지 않습니다.
- 같은 내용을 `DATA_SOURCE_SESSION_CURRENT.md`에 적습니다.

## 11. 확인 못 한 것 (미검증)

- Tiingo 가격 ($30/$50)과 무료 플랜의 뉴스 API 포함 여부; CME FedWatch 종가판 가격 ($25, 구간제 여부)·장중판 가격·이력 시작일·인증 방식·이력 저장 허용; Cryptopanic 무료 플랜 존재와 필드 이름; Alpha Vantage 관련성 필드·과거 뉴스 깊이·과거 감성 재계산 여부·상업 조건; Trading Economics 가격과 컨센서스 포함 요금제.
- Polymarket API의 한국 내 이용 가능·적법 여부, Kalshi 전부. **법률 자문이 아닙니다.**
- FRED 분당 120건 (제3자), 시리즈별 상업 조건.
- Claude 각 모델의 학습 기준일, 사고 토큰을 포함한 실제 LLM 비용 (D14의 가격은 2026-11-03 공개 가격 사본 기준).
- 엑셀 메모의 "계획서 3.2·3.3·4.1" 원문 문서 (Notion·Drive·저장소에서 못 찾음; 같은 내용은 NEW MACRO MODEL).
- 홈 지표가 소유자 PC에서 안 뜨는 실제 원인 (진단 출력 전).
- Upbit 시세의 표시 조건.

## 12. 출처

- 소유자: `owner_answer_1117.txt` (2026-11-17, 1절 원문), Notion QUANTGEN PROJECT `34f5c916fe0c800b9b4af35c80ebe778` (11-16 절, 2026-11-17 조회), 소유자 엑셀 `ravenpack_alt.xlsx`의 글 사본 `OWNER_EXCEL_RAVENPACK_ALTERNATIVES.txt`.
- 메인 분석: `D14_RAVENPACK_ALTERNATIVES.md` (2026-11-17; 0~13절), `D7_ENV_STRUCTURE.md` (5.5절 "새 공급원 규칙"), 소유자 보고서 초안 D8 행.
- Notion: DIDM `02e5c916fe0c821bb15701f648e9db87`, DIDM_Research_Report `2045c916fe0c82ca8efe8157c0c70bd8`, Types of Info & Ravenpack's Role `41b5c916fe0c80ddb4e2ce2e1d376003`, NEW MACRO MODEL `4135c916fe0c80dbb7d5f10a6e09077b` (모두 2026-11-17 메인이 읽음).
- 저장소 `origin/main` `e01e152`: `.github/workflows/runtime-smoke.yml:5-9, 90`, `config.py:154, 280`, `data/krx/opendart_client.py`, `data/crypto/crypto_client.py`, `core/research/markets.py`, `core/research/display_rights.json`, `docs/audit/2026-10-27/calendar_batch5/extract_alfred.py`.
- 공개 자료 (D14 13절, 모두 2026-11-17 검색; 일부 호스트는 직접 열지 못해 검색 요약 기준): Alpha Vantage https://alphavantage.co/premium ; Tiingo https://api.tiingo.com/products/news-api ; CME FedWatch https://www.cmegroup.com/market-data/market-data-api/fedwatch-api.html ; Cryptopanic https://cryptopanic.com/developers/api/about ; GDELT https://blog.gdeltproject.org/introducing-gkg-2-0-the-next-generation-of-the-gdelt-global-knowledge-graph/ , https://www.gdeltproject.org/about.html ; FRED/ALFRED https://fred.stlouisfed.org/docs/api/fred/fred_vs_alfred.html ; Trading Economics https://tradingeconomics.com/analytics/pricing.aspx ; Polymarket https://docs.polymarket.com/api-reference/rate-limits , 한국 차단 보도 https://koreatimes.co.kr/business/companies/20260819/korea-moves-to-block-polymarket-over-illegal-gambling .
