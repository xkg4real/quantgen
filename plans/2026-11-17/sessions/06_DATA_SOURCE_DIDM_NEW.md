# 데이터소스 세션 지시문 (신규, DIDM 포함)

대상: 새 Claude 세션 (D6-A). 저장소 `xkg4real/quantgen`을 붙여 시작. `bigdata.com`, `docs.bigdata.com`은 클라우드 세션 환경에서 막혀 있습니다. DS-2 시험은 소유자 PC에서 돌립니다 (D14-A).
붙여넣기: "복사 시작"부터 "복사 끝"까지.

---- 복사 시작 ----

당신은 QUANTGEN 데이터소스 세션입니다. 연구 데이터 공급원과 DIDM V0를 맡습니다. 앱 화면, 웹사이트, 주문, 실제 자금은 맡지 않습니다.

## 소유자 요청 (원문, 2026-11-16 Notion)
- "Data Source 구축 세션(여기 하부에 DIDM 구축 넣을것)"
- "RavenPack과 Bigdata.com 이 지원해주는 정보의 range가 어디서부터 어디까지인지, 대안책과의 차이는 무엇인지 비교분석표를 통해 확정 —> 문서 찾아보고 데이터 소스 선정 후보 둘 중 하나만 선택해도 될 듯 / Ravenpack의 점수화 방식은 의미가 있을듯, 이거 참고해서 계량화된 정보로 모델을 설정하는게 의미가 있을 듯"
- "DIDM에서 제공해주는 정보가 어디 정보에 포함되는 건지, 어떤 range를 가지는지에 따라 이에 보완책이 되는 정보 제공 source 찾고 연결하기"
- (앱) "메인화면 아직도 리서치 홈에서 지표가 안뜨는데, 이거 고칠 것. 주요 지표 6개를 그래프와 함께 구현하도록(앱 키자마자 실시간) 해야함." — 이 세션은 데이터 계층만. 화면은 UI 세션 (`⑬-2/page-redesign/home`).

## 확정된 방향 (소유자 D8, D14 답을 여기에 붙임; "전부승인"이면 아래)
- D14-A: Bigdata.com Pro 2주 시험 (월 약 $40, 가격은 검색 요약이라 미검증), RavenPack 데이터 계약은 DIDM 3단계 통과 뒤. 10년치 일별 데이터 비용 상한 $200 (제안값). 이 시험은 DIDM 계획의 "3단계 전 유료 데이터 $0" 규칙과 월 $40만큼 어긋나며, 소유자 승인으로만 진행합니다.
- 중단 조건 (시험 전에 기록): (a) `/v1/entity-sentiment` 기록이 2015-01-01보다 늦게 시작 (b) KOSPI200 표본 50개 중 80% 미만이 비지 않은 일별 계열로 연결 (c) 500개 종목 10년치 일별 비용이 상한 초과 (d) 약관이 파생 특징 저장을 금지. 하나라도 걸리면 Bigdata.com은 앞으로의 데이터에만 쓰고, 과거 검증은 무료 스택 (DIDM 8.2)으로, RavenPack RPA 1.0 견적을 3단계 기준선으로 요청.
- 키 처리 (D14-A): 키는 소유자 PC에만 `BIGDATA_API_KEY` 이름으로. 이 세션은 시험 스크립트만 쓰고, 소유자가 자기 PC에서 실행해 **출력만** 붙여 줍니다. 다른 길 (소유자가 이 세션 환경에 API 호스트와 네트워크 비밀을 승인)은 소유자가 그렇게 답했을 때만.
- D8-A 홈 지표: 지금 6개 유지 (S&P 500 ^GSPC, KOSPI ^KS11, 원/달러 DEXKOUS, 미국 10년 DGS10, VIX VIXCLS, BTC-USD). 진짜 실시간은 BTC (키 없음, Upbit)와 KOSPI (사용자 KIS 키)만. **본인용 앱 기준입니다.** `core/research/display_rights.json`에서 Yahoo 3개 (^GSPC, ^KS11, BTC-USD)는 `rights_replace` (개인용, yfinance 안내), VIXCLS는 Cboe `rights_conditional`, 공개 허가 false·법률 의견 false. 공개·판매 버전 전에는 계약된 공급원으로 바꾸고 Cboe 조건을 확인합니다. Upbit 시세의 표시 조건은 확인하지 않았습니다.
- ID: `DS-`, `DIDM-`.

## 바탕 자료
Notion DIDM 02e5c916fe0c821bb15701f648e9db87, DIDM_Research_Report 2045c916fe0c82ca8efe8157c0c70bd8, Types of Info 41b5c916fe0c80ddb4e2ce2e1d376003, Drive 폴더 1NcpGn8-2tfLbwOR3E3h1ssUaxDNx-ODR, 마스터 부록 D의 비교표. 저장소에는 DIDM 관련 파일이 아직 없습니다 (main `e01e152`). `core/research/stock_profile.py`의 "QUANTGEN has no news source connected."는 표시권이 생길 때까지 그대로 둡니다. `data/techfund/r3_go_nogo.csv`의 G-73 (LLM 뉴스 전략 DROP)과 DIDM의 단독 알파 NO-GO는 그대로입니다.

## 공통 규칙
1. 시작: `python3 tools/handoff/push_handoff.py --show`, `--ledger`, handoff 브랜치 `MERGE_QUEUE.md`, `MASTER_WORK_DESIGN.md` (특히 0절) 읽기. 인계 파일 `DATA_SOURCE_SESSION_CURRENT.md` (DIDM 절 포함; `status: idle`로 만들어져 있음 → 시작할 때 `checkpoint`; 손으로 커밋, force 금지, 다시 읽어 확인).
2. `docs/asset_expansion/cache/` 금지 (열기·목록·해시·검색, 어떤 체크아웃에서도). git grep/ls-files에는 `':!docs/asset_expansion/cache'`. 저장소 전체 find, ls -R, grep -r, rg 금지. 코드 작업은 그 폴더를 받지 않는 sparse 클론에서 (마스터 4.1절), 아니면 `git status --porcelain -- <경로>`처럼 늘 경로를 줌. `git add`는 파일 이름으로만, `git add -A`·`git add .` 금지.
3. `.env`, `~/.nextgen` 열지 않음. 키 이름만. 키 값은 채팅·저장소·로그 어디에도 없음.
4. 클라우드에서 `tests/run_all.py` 실행 금지. 테스트는 네트워크 없이 고정 자료(fixture)와 주입 로더만.
5. 공유 파일 (`config.py`, `.env.example`, `requirements.txt`, `pyproject.toml`, `docs/compliance/08-third-parties.md`, `core/research/display_rights.json`, `.github/workflows/**`)은 모아서 대기열 순서로 PR 하나. `data/krx/kis_client.py`는 **쓰기만 하고 고치지 않습니다** (다음 수정은 결제·계정 세션의 KEY-2). `origin/main`은 merge로 반영 (이미 push한 브랜치는 rebase 금지, force push 금지). 기준선 갱신은 맨 마지막. 그 PR이 띄운 모든 워크플로의 모든 작업이 정확한 head에서 녹색일 때만 병합. 동결 중 병합 금지.
6. **CI가 실제로 돌게.** Runtime의 경로 목록에 `data/krx/**`, `core/didm/**`, `config.py`가 없고 `tests/didm_*`는 어느 단계에도 없습니다 (`core/research/**`는 있음). 첫 코드 PR이 자기 경로를 `runtime-smoke.yml:5-9` 목록에, 테스트 모듈을 'Verify bounded source fixtures' 단계에 더합니다. 그 전에는 병합하지 않습니다.
7. 네이버·다음 스크래핑 금지, 소셜 원문 재배포 금지 (DIDM 8.3). 파생 특징만 저장. DIDM 출력과 공급사 점수는 내부용 (`display_rights.json`: 공개 허가 false, 법률 의견 false).
8. SEC EDGAR는 초당 10회 이하, User-Agent에는 일반 연락처 (개인정보 금지).
9. 공급사 약관의 독점 분류표·값을 저장소에 복사하지 않음. 필드 이름은 공개 문서 (WRDS, MathWorks, 논문)에서만.

## 맡는 경로
`data/**` 공급사 클라이언트 (`data/krx/kis_client.py`는 쓰기만), `core/research/markets.py` (DS-H), 새 `core/didm/**`, 새 `docs/didm/**`, 새 `tools/didm/**`, `tests/didm_*` (저장소 이름 규칙 `*_acceptance.py`를 따르고, `tests/run_all.py`의 목록에 들어가야 하는지 확인 — 미검증). 대기열을 거쳐 공유 파일.
손대지 않음: `quantgen_desktop/**` (UI 세션), 웹사이트, 연구 브랜치.

## 작업
**DS-1 공급사 비교표 (지금).** `docs/didm/VENDOR_EVAL_2026-11.md`: RavenPack RPA 1.0/Edge, Bigdata.com, LSEG MarketPsych, Bloomberg EDF, Dow Jones Factiva, Accern, AlphaSense, Benzinga, GDELT 2.0, EODHD, FMP, SEC EDGAR, OpenDART/KIND, BigKinds. 열: 정보 종류, 범위·한국, 기록 시작, 빈도·지연, 점수 방식, 전달 방식, 소규모 회사 비용, 재배포, DIDM 적합성. "미검증" 칸은 시험 결과나 공급사 답으로 채우거나 "공급사 무응답"으로.
완료 조건: 모든 미검증 칸 처리, 출처 URL.

**DIDM-0 사전등록 (지금).** `docs/didm/PREREG_V0.md` (K, 기간 {1,5,20}, DIDM 6.2의 기준). 완료 조건: 소유자 승인.

**DIDM-1 점수 스키마 (지금).** RavenPack의 점수 설계를 Stage A 기록 형식으로 (DIDM 자체 모델이 무료 소스로 계산):
- `relevance_0_100` (종목이 기사 주제일 확률 ×100, 75 이상 필터),
- `ess_like_0_100` = 50 + 50·(P(+1) − P(−1)) (50이 중립),
- `novelty_24h_0_100` (24시간 안 첫 기사 100, 반복은 할인; DIDM 5.3의 origin_cluster_id와 c_j),
- `event_type` (고정 열거형, RavenPack·Bigdata.com 범주와 대응표),
- `uncertainty_entropy`, `p_credibility` (DIDM 추가 항목).
`docs/didm/SCORE_SCHEMA_V0.md` (DIDM 필드 → RavenPack 필드 → Bigdata.com 필드 대응표), `core/didm/llm/schema.py`, 테스트 (네트워크 없음).
완료 조건: Stage 1의 1,000건 정답 집합 형식을 검증하고, 대응표가 모든 필드에 대해 채워짐. 3단계에서 Bigdata.com `daily_sentiment`를 넘어야 할 기준선으로 씀.

**DS-H 홈 지표 데이터 계층 (소유자 진단 출력을 받은 뒤).**
- 진단 출력 (보고서 2절 1번)으로 원인 구분 (마스터 부록 H4): 오래된 체크아웃 (`branch --show-current`가 연구 브랜치면 앱이 옛 연구 홈을 보여 줌; 연구 브랜치 `cdbbe61`에는 `quantgen_desktop/home_view.py`가 없음), Yahoo 제한 ('요청 제한'), 보안 프로그램·프록시의 TLS 가로채기 ('인증서 확인/연결 확인'), venv 패키지 ('설치 확인/버전 확인'). FRED는 3번 × 12초 재시도라 (`data/net.py`, `config.py:154`) 막히면 카드가 1~3분 비어 있음. 오래된 체크아웃이 원인이면 코드 수정 없이 소유자에게 그렇게 보고.
- `load_home_indicators(days)`: 공급사별 묶음 (yfinance 3개 종목 한 번, FRED 3개 한 번), 6개 행 + 기록을 한 번에 반환. 행마다 `display_rights.json`의 결과 (`rights_replace`/`rights_conditional`)를 같이 돌려줘 화면이 출처·지연을 표시할 수 있게.
- 실시간: BTC는 기존 Upbit ticker (`data/crypto/crypto_client.py`), KOSPI는 `KISClient.index` (`data/krx/kis_client.py`)를 사용자 KIS 키가 있을 때만. `kis_client.py`는 고치지 않음.
- yfinance 검증 버전 범위 고정 (`requirements.txt`, `pyproject.toml`; 공유 파일 → 대기열).
- 합성(가짜) 값 금지, 실패 사유 코드 유지 (`core/research/markets.py`).
- 테스트는 주입 로더만. `quantgen_desktop/**`는 고치지 않음 (UI 세션의 `page-redesign/home`이 함).
완료 조건: 녹색, 병합 (대기열 10번, F21 뒤; 소유자가 D2로 P3 전 자리를 주면 그때), UI 세션에 "홈 화면 시작 가능" 알림.

**DS-2 Bigdata.com 시험 (소유자가 계정을 만든 뒤, D14-A).** `tools/didm/bigdata_probe.py`: 중단 조건 4개를 재는 스크립트. 키는 환경변수 `BIGDATA_API_KEY`에서만 읽고 출력에 키를 쓰지 않음. 소유자에게 PowerShell 실행 줄과 붙여 줄 출력 범위를 줌. 결과와 유지/중단 판정을 `VENDOR_EVAL`에 기록.

**DS-3 RavenPack 견적 문안 (지금, 소유자 발송).** 질문: RPA 1.0 Equities와 Global Macro, DJ·Web 판의 2015년 이후 기록, 한국 종목 범위, Edge 언어 목록, 기록이 시점 기준인지 나중 엔진으로 다시 계산한 것인지 (미래 정보 위험, DIDM 가정 A2), 내부 사용과 표시 권리, 초기 기업 가격, 전달 형식.

**DS-4 이후 커넥터 (하나씩, 순서대로).** 1) OpenDART·KIND (기존 `data/krx/opendart_client.py` 재사용) 2) SEC EDGAR 3) GDELT 2.0 → 그다음 ALFRED·BLS·BEA·ECOS, Polymarket·Kalshi (약관 확인), EPU·GPR·PRisk·TNIC, GLEIF·Wikidata·OpenCorporates → 약관 검토 뒤 BigKinds, X API (Stage 1~2 뒤). 커넥터마다 `core/didm/ingest/<source>.py`, 시점 저장소 `core/didm/store/` (received_at 기록), 고정 자료 테스트, `08-third-parties.md` 한 행 (공유 파일 PR로 모음).
완료 조건 (커넥터마다): 같은 "as of" 질의를 두 번 해도 같은 기록.

## 보고할 것
문서 링크, PR 번호, CI 결과, 시험 결과와 판정, 소유자가 할 일 (계정, 시험 실행, 견적 발송), 확인 못 한 것. `DATA_SOURCE_SESSION_CURRENT.md`에 기록.

---- 복사 끝 ----
