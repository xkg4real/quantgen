# D7 다시 보기: `.env` 없이 실행 — 법인 전환 때 앱 구조를 또 고쳐야 하나

- 작성: 2026-11-17. 기준: `origin/main` `e01e152` (2026-11-14 00:50 KST). 읽기만 했습니다. (검토 시점에 main은 PR #121 병합으로 `5888d05`(2026-11-17 21:33 KST)가 됐습니다. 이 문서가 인용한 파일은 그 병합에서 바뀌지 않았습니다.)
- `.env`, `~/.nextgen`은 열지 않았습니다. 이 문서에는 변수 **이름**만 있고 값은 0개입니다.
- 법률·약관 내용은 공개 자료와 기존 Notion 상업화 분석서를 정리한 것입니다. **법률 자문이 아닙니다.** 계약이 필요한지는 코스콤·공급사의 서면 답과 변호사 의견으로 확정해야 합니다.
- 확인하지 못한 것은 **미검증**으로 적었습니다. 공수는 모두 **추정**입니다.

---

## 0. 결론

소유자 조건 (2026-11-17 답, 원문):
> "법인 상태로 전환해 상업화를 진행하려고 할때 또 다시 수정(이때의 수정은 앱의 구조를 수정한다는 뜻으로, 단순히 키 교체를 의미하는건 아님. 즉, 단순한 변경이 아닌 어느 정도 작업량이 요구되는 작업을 의미함)해야 한다면 거부. 그게 아니라면 승인"

| 안 | 판정 | 이유 (한 줄) |
|---|---|---|
| **D7-A 원안** (앱에서 키 입력 → Windows 자격 증명 관리자 + 키 없는 기본값, `.env`는 개발 예비) | **거부** | 키를 **어디에 두는지**만 바꿉니다. 앱이 공급사를 **직접 부르는 코드 31개 파일 72곳**은 그대로입니다. 법인 뒤 계약 데이터가 회사 서버나 계약 공급사로 오면 이 72곳을 다시 고쳐야 합니다. 이것은 구조 수정입니다. |
| **D7-G** (D7-A + 공급원 게이트웨이, 지금 만듦) | **권장** | 앱이 공급사를 부르는 길을 지금 `core/gateway` 한 곳으로 모읍니다. 지금은 "내 PC 키"와 "키 없는 공급원" 길만 켭니다. "회사 데이터 서버" 길은 같은 자리에 만들어 두고 꺼 둡니다. 법인 뒤에는 **설정 파일, 회사 서버, 계약**만 남습니다. |

- **D7-G는 11-17 보고서에 없던 새 안이라 소유자 승인이 필요합니다.** 승인이 handoff 문서나 메인 공지에 적히기 전에는 코드 작업(KEY-2 포함)을 시작하지 않고, KEY-1 이름 목록과 KEY-3 설계 문서만 씁니다 (공통 규칙 11: 답이 없는 결정에 걸린 작업은 시작하지 않음).
- 추가 공수: 원안 대비 **약 6~9 작업일**, 원안 포함 **약 8~11 작업일** (추정, 5.6절).
- D7-A의 좋은 부분 (키 입력 화면, 키 보관함, 키 없는 기본값, `.env`는 개발 예비)은 D7-G 안에 그대로 들어갑니다. 버리는 것이 아니라 한 층을 더합니다.
- 소유자의 11-16 메모와도 맞습니다: "만약 법인 설립이 필요한 부분이면서 법인 설립 이후 이 방법을 실행했을때 앱의 작동 워크플로우가 수정이 필요하다면 미리 수정할 것." (Notion 11-16, `notion_1116.md:24-25`)

---

## 1. 지금 앱이 키를 읽는 방법 (코드 사실)

- 환경을 읽는 곳은 **두 군데뿐**입니다.
  - `config.py:34` — `_clean(name)`이 `os.getenv(name)`을 읽고, 빈 값과 `<...>` 자리표시를 버립니다.
  - `core/markets.py:222` — `NEXTGEN_MAX_AGE_<코드>` (시장별 시세 유효시간).
  - `quantgen_desktop/`, `data/`, `ui/`, `main.py`에는 `getenv`·`os.environ`·`load_dotenv`가 0건입니다 (git grep).
- `.env`는 `config.py:25-29`에서 `load_dotenv()`로 읽습니다. 실패하면 무시합니다. 그래서 앱은 이미 `.env` 없이 켜집니다.
- 키 값은 화면에 나오지 않습니다. 설정·연결 화면은 "있음/없음"과 이름만 봅니다 (`config.py:157-170`, `config.py:238-251`, `core/research/connections.py:21-34`, `quantgen_desktop/connections.py:6-13`).
- 키 입력 화면, `QSettings`의 키 저장, `keyring` 사용은 아직 없습니다 (git grep 0건).

### 1.1 비밀 키 이름 (10개)

| 이름 | 읽는 줄 (`config.py`) | 쓰는 곳 | 키가 없으면 | 상용판에서 성격 |
|---|---|---|---|---|
| `KIS_APP_KEY`, `KIS_APP_SECRET` | :77, :81 | `data/krx/kis_client.py:206,237`, `data/kis_stream.py:223` (실시간 승인키) | 국내·해외 시세, 차트, 랭킹, 실시간이 막힘 | **사용자 증권사 키** (사용자에게 남음) |
| `UPBIT_ACCESS_KEY`, `UPBIT_SECRET_KEY` | :261, :265 | `data/crypto/crypto_client.py:339` (보유 자산) | 보유 자산만 막힘. 공개 시세는 됨 | **사용자 거래소 키** |
| `FMP_API_KEY` | :53 | `data/fmp/quote_client.py:115`, `core/quant/history.py:126`, `core/market/market_cap.py` (기본값), `core/engine/feed.py:96` | 미국 일봉·시세가 막힘 | 회사 표시 계약 또는 제외 |
| `KRX_API_KEY` | :141 | `data/krx/krx_market_client.py:77,84` | 전체 시장 스냅샷이 막힘 | 약관 확인 필요 (미검증) |
| `OPENDART_API_KEY` | :133 | `data/krx/opendart_client.py:72` | 공시·재무가 막힘 | 사용자 본인 키 (1인 1키라고 알려짐, 2차 출처) |
| `ANTHROPIC_API_KEY` | :219 | `core/quant/insights.py:59,321` | AI 해설만 꺼짐 | 1차는 사용자 키, 나중에 회사 중계 선택 |
| `GS_CLIENT_ID`, `GS_CLIENT_SECRET` | :231, :235 | `core/quant/gsq.py:54,75` | 선택 기능만 꺼짐 | 상용판 제외 후보 |

### 1.2 비밀이 아닌 설정 이름 (16개)

| 이름 | 줄 | 용도 |
|---|---|---|
| `FMP_BASE_URL`, `NEXTGEN_FMP_MIN_INTERVAL` | `config.py:62`, `:68` | FMP 주소, 같은 종목 재조회 간격 |
| `KIS_BASE_URL` | :84 | KIS 주소 (실전/모의) |
| `OPENDART_BASE_URL`, `KRX_BASE_URL` | :136, :150 | 공급사 주소 |
| `NEXTGEN_HTTP_TIMEOUT` | :154 | 요청 시간 제한 |
| `NEXTGEN_TRADING_DIR`, `QUANTGEN_MACRO_DIR` | :179, :186 | 로컬 저장 폴더 |
| `NEXTGEN_QUOTE_MAX_AGE`, `NEXTGEN_ENGINE_TICK`, `NEXTGEN_NO_DATA_GRACE` | :191, :194, :203 | 규칙 엔진 시세 유효시간·주기·허용 누락 |
| `QUANTGEN_AI_MODEL` | :227 | AI 해설 모델 이름 |
| `FRED_BASE_URL`, `NEXTGEN_FICC_CACHE_TTL`, `NEXTGEN_FICC_CACHE` | :280, :283, :287 | FRED 주소, FICC 캐시 |
| `NEXTGEN_MAX_AGE_<코드>` | `core/markets.py:222` | 시장별 시세 유효시간 |

- `.env.example`에는 이 중 14개 이름이 있습니다 (이름만 셈).
- Notion 상업화 분석서는 "소스상 환경변수 이름 47개"라고 적었습니다. 저장소 전체 (도구·연구 포함) 기준으로 보입니다. 앱 실행에 쓰는 것은 위 26개입니다. 차이는 KEY-1에서 확인합니다 (**미검증**).

### 1.3 디스크·메모리에 남는 자격 정보

- KIS 접근 토큰: `~/.nextgen/kis_token.json`에 평문 (`data/krx/kis_client.py:54`, 쓰기 `:190-191`). 앱키가 아니라 약 24시간짜리 토큰입니다.
- KIS 실시간 승인키: 메모리에만 둡니다 (`data/kis_stream.py:245`).
- 작은 함정: `KISClient`는 만들 때 한 번만 `ready`를 정합니다 (`data/krx/kis_client.py:174`). 앱에서 키를 넣어도 이미 만든 객체는 모릅니다. 키 입력 화면을 붙이면 클라이언트를 다시 만들어야 합니다 (D7-A든 D7-G든 필요. D7-G는 게이트웨이가 한 곳에서 처리).

---

## 2. 지금 앱이 공급사를 부르는 방법

- 모든 호출이 **사용자 PC에서 공급사로 바로** 나갑니다. 회사 서버는 없습니다.
- 공급사 클라이언트는 `data/` (KIS, KRX, OpenDART, FMP, Upbit/Binance)와 `core/` 안 몇 곳에 있습니다.
  - FRED·Yahoo: `core/ficc/data.py:53,178,200`
  - Yahoo: `core/market/routing.py:269`, `core/market/market_cap.py:137`
  - Anthropic: `core/quant/insights.py:42,344`
  - GS Marquee: `core/quant/gsq.py`
- 문제는 이 클라이언트를 **여러 층이 직접** 부른다는 점입니다. `data/` 밖에서 공급사 클라이언트 import, `yfinance` 직접 호출, `config`의 키 함수 사용을 센 결과 (git grep):

| 층 | 파일 | 곳 | 예 |
|---|---|---|---|
| `core/` | 18 | 46 | `core/quant/history.py` 13곳 (FMP·KIS·Upbit·Binance), `core/research/*_workflow.py`, `core/research/watchlist.py:57`, `core/engine/feed.py:96` |
| `quantgen_desktop/` (데스크톱 화면) | 6 | 14 | `market_chart.py:405,412` (`MarketDataService`, `KISStream` 직접), `watchlist_live.py:45,48`, `app.py:65,80`, `market_tools.py:125` |
| `ui/` (Flet, 모바일 후보) | 6 | 11 | `market_chart_page.py:79,84`, `settings_page.py:20,167,199` |
| `main.py` | 1 | 1 | `:54` `KRXGateway` |
| **합계** | **31** | **72** | |

- 이 수는 셈 방식에 따라 1~2곳 달라집니다. 검토 때 같은 기준으로 다시 세니 `core/`는 19개 파일 47곳이었습니다 (예: `core/ficc/curve_models.py:245`의 `KISMarkets` 직접 import, `core/ficc/data.py:57`의 `data.net` 공용 세션 포함 여부). 정확한 목록은 KEY-3 경계 시험이 만듭니다. 판정에는 영향이 없습니다.
- 시험 쪽: 24개 시험 파일이 이 클라이언트나 키 함수를 122곳에서 부르거나 바꿔 끼웁니다.
- 좋은 점이 있습니다. "한 곳으로 모으기"의 예가 이미 코드에 있습니다.
  - `data/krx/gateway.py:1-17` — KIS·KRX·OpenDART를 기능별로 고르고, 결과마다 출처를 붙입니다 (`Answer`, `:29-38`).
  - 많은 core 함수가 `loader=`, `status_loaders=`, `probe_loaders=` 같은 주입 자리를 이미 갖고 있습니다 (`core/research/markets.py:81`, `core/research/connections.py:21`).
  - 이 모양을 앱 전체로 넓히면 됩니다.

---

## 3. 상업 출시 때 무엇이 필요한가

| 필요 | 내용 | 근거 |
|---|---|---|
| 회사 명의 데이터 권리 | 판매용 프로그램에 시세를 쓰면 개인도 별도 계약 대상 (KRX 안내). Yahoo(yfinance)는 개인용 → 상용판 제거. FMP는 소프트웨어 표시에 별도 계약. KIS 제휴사는 코스콤 계약 없이 자사 화면에 시세를 쓸 수 없음 | Notion 상업화 분석서 항목 5 (KRX, yfinance, FMP, KIS 안내 인용) |
| 사용자별 권한 통제와 보고 | 거래소 데이터를 여러 사용자에게 배포하는 회사는 사용자 권한(entitlement)을 통제하고 사용자 수를 정기 보고 (Nasdaq 정책 예) | Nasdaq 정책 문서 (검색 요약, 원문 미열람 → **미검증**) |
| 그래서 데이터 길이 바뀜 | 회사가 계약한 데이터는 보통 ① 회사 서버를 거쳐 오거나 (서버가 계정·요금제 확인) ② 계약 공급사가 회사가 발급한 사용자별 토큰으로 직접 줍니다. 회사 키는 설치파일에 넣을 수 없습니다 | 분석서 항목 4 ("운영자 키는 앱에서 모두 제거") |
| 사용자 계정 | 회원·결제·라이선스·업데이트 서버. 소유자가 D11에서 정식 계정을 지금 만들기로 함 | 분석서 항목 7, 소유자 11-17 답 D11 |
| 사용자 증권사 키는 사용자에게 | KIS 제휴는 투자일임·자문 제도권 회사만 → 사용자 본인 키. 증권사 키·계좌·주문은 서버를 지나지 않음 | 분석서 항목 2, 7 |

주의할 점:
- 분석서 항목 7은 "시세도 서버를 지나가지 않는다"고 적었습니다.
- 그러나 항목 5에서 KIS·KRX 시세 표시권은 "코스콤 확인 전 출시 보류"입니다.
- 즉 **어떤 데이터가 회사 서버로 오게 될지는 계약 답이 와야 정해집니다.** 지금 정할 수 없습니다. 그래서 앱은 "내 키로 직접"과 "회사 서버 경유" 두 길을 모두 받을 수 있어야 합니다.

---

## 4. 판정: D7-A 원안은 법인 뒤 구조 수정이 필요한가 → **예**

법인 뒤 생길 수 있는 세 경우에서, D7-A 원안이면 앱이 해야 할 일:

| 법인 뒤 상황 | D7-A 원안에서 앱이 할 일 | 종류 |
|---|---|---|
| ① 모두 사용자 키로 유지하고 Yahoo·FMP만 뺌 (가장 가벼운 경우) | Yahoo를 쓰는 홈 지표 3개 (`core/research/markets.py:6-13`), FICC 환율·선물 (`core/ficc/data.py`), 주식 일봉 대체 경로 (`core/market/routing.py`, `quantgen_desktop/app.py:61-85`), 시가총액 (`core/market/market_cap.py`)을 다른 공급사로 다시 연결. 유료 요금제에 따라 기능을 여닫는 확인을 `config.*_ready()`를 쓰는 곳마다 추가 | 구조 수정 (중) |
| ② 계약 데이터를 회사 서버가 중계 | 72곳을 서버 호출로 바꾸고, 결과 변환, 실시간 스트림 경로, 로그인 토큰 연결을 새로 작성 | 구조 수정 (대) |
| ③ 계약 공급사가 사용자별 토큰 발급 | 공급사 클라이언트마다 토큰 받는 흐름, 계정 연동, 준비 여부 판단을 바꿈 | 구조 수정 (중) |

원안의 `quantgen_cloud` "자리"로 막을 수 없는 이유:
- 원안은 키 보관함 (KEY-2) 안에 "꺼진 공급원 `quantgen_cloud` 자리"를 둡니다 (마스터 5.3절, 세션 05 KEY-2).
- 그런데 회사 서버는 공급사 키를 앱에 **내려주지 않습니다**. 내려주면 회사 키가 사용자 PC에 놓입니다. 분석서 항목 4가 이를 금지합니다.
- 회사 서버는 **데이터**를 줍니다. 그래서 키 보관함에 자리를 두어도 72곳의 호출 길은 그대로이고, 법인 뒤에 다시 고쳐야 합니다.

판정: 소유자 기준 ("단순한 변경이 아닌 어느 정도 작업량이 요구되는 작업")에 걸립니다. **D7-A 원안: 거부.**

---

## 5. 대안 D7-G: 공급원 게이트웨이 + 자격증명 저장소 (지금 만듦)

### 5.1 한 줄 설명

앱 (화면과 core)은 공급사를 직접 부르지 않고 `core/gateway` 하나만 부릅니다. 게이트웨이 뒤의 "길"만 설정으로 바꿉니다. 지금 켜는 길은 "내 PC 키"와 "키 없는 공급원"입니다. 법인 뒤에는 같은 자리의 "회사 데이터 서버" 길을 켭니다.

```mermaid
flowchart LR
  UI["화면<br/>quantgen_desktop · ui"] --> GW
  CORE["core 분석·연구"] --> GW
  GW["core/gateway<br/>client · ready · status · stream"] --> R{"routes.json<br/>personal / commercial"}
  R -->|local_key| L["내 PC 길<br/>기존 data/ 클라이언트"]
  R -->|keyless| K["키 없는 공급원<br/>FRED · Upbit/Binance 공개"]
  R -.->|company (지금 꺼짐)| RM["회사 서버 길<br/>remote.py"]
  L --> P1["KIS · Upbit 잔고<br/>(사용자 키, 늘 내 PC)"]
  L --> P2["OpenDART · Anthropic 등"]
  CRED["core/credentials<br/>키 보관함 (Windows 자격 증명 관리자)"] --> L
  ACC["core/account<br/>로그인 토큰 (D11)"] -.-> RM
  RM -.-> SRV["회사 데이터 서버<br/>같은 dispatch.py + 회사 키<br/>(법인 뒤)"]
  SRV -.-> LIC["계약 공급사<br/>(코스콤·Yahoo 대체 등)"]
```

### 5.2 부품

| 부품 | 경로 (새) | 하는 일 | 지금 | 법인 뒤 |
|---|---|---|---|---|
| 자격증명 저장소 | `core/credentials/` | `get / set / delete / status(이름)`. 찾는 순서: 프로세스 환경변수 → OS 키 보관함 (Windows 자격 증명 관리자, macOS 키체인; service "QUANTGEN") → `.env` (개발판만). 토큰 캐시 (KIS 토큰, 계정 토큰) | 사용자 키 + KIS 토큰 | 같은 코드. 계정 토큰, 공급사가 준 사용자별 토큰도 여기 |
| 이름 목록 | `core/credentials/names.py` | 이름마다 종류: 사용자 증권사 키 / 사용자 데이터 키 / 사용자 AI 키 / 계정 / 개발 전용 | KEY-1 표 그대로 | 표만 갱신 |
| 게이트웨이 입구 | `core/gateway/__init__.py` | 앱에 네 가지만 보여 줌: `client(이름)`, `ready(이름)`, `status()`, `stream(...)` | 켜짐 | 그대로 |
| 길 설정 | `core/gateway/routes.json` | 공급원마다 길 순서: `local_key` / `keyless` / `company` / `off`. 프로필 2개: `personal` (지금), `commercial` (초안, 꺼짐) | `personal` | `commercial` 값을 계약 결과로 채움 |
| 내 PC 길 | `core/gateway/local.py` | 기존 `data/` 클라이언트와 `core/ficc/data.py` 등을 그대로 감쌈. 키는 `config` → 자격증명 저장소로만 읽음 | 켜짐 | 사용자 키 공급원에 계속 씀 |
| 회사 서버 길 | `core/gateway/remote.py` | 일반 전달기: (공급원, 함수, 인자)를 회사 서버로 보내고 결과를 받음. 계정 토큰을 붙임. 실시간은 웹소켓. 허용 함수 목록만 보냄 | 꺼짐 (주소 빈 값). 시험은 가짜 서버로 | 주소만 넣으면 켜짐 |
| 결과 변환 | `core/gateway/codec.py` | `Quote`, `Candle`, `MarketSnapshot`, 시계열 표, `Answer`를 JSON으로/에서 | 시험에 씀 | 그대로 |
| 서버 쪽 처리기 | `core/gateway/dispatch.py` | (공급원, 함수, 인자)를 받아 내 PC 길로 실행. 회사 서버는 **이 같은 코드**를 회사 키로 돌림 | 가짜 서버 시험에 씀 | 회사 서버에 그대로 탑재 |
| 준비 상태 | `ready(이름)` | "키 필요 / 로그인 필요 / 요금제 필요 / 키 없이 됨 / 꺼짐" + 필요한 이름 | 키 여부만 | 계정·요금제도 같은 자리에서 |
| 경계 시험 | `tests/gateway_boundary_acceptance.py` | `core/`, `quantgen_desktop/`, `ui/`, `main.py`에서 `data.*` 공급사 import, `yfinance`, 공급사 주소 직접 호출, `config`의 키 함수 사용이 새로 생기면 실패. 처음에는 "알려진 예외 목록" 72곳으로 시작하고, KEY-4·KEY-5가 0으로 줄임 | 켜짐 | 계속 켜짐 (다른 세션이 새 기능을 넣어도 구조가 다시 흩어지지 않게) |

### 5.3 지켜야 할 규칙

1. 사용자 증권사·거래소 키를 쓰는 공급원 (KIS 시세·잔고·주문, Upbit 잔고)은 `routes.json`에서 `local_key`로 고정합니다. `remote.py`는 이런 공급원을 받으면 거절합니다 (시험으로 확인). 분석서 항목 7의 "서버는 증권사 키·계좌·주문을 다루지 않음" 그대로입니다.
2. 회사 키는 설치파일, `routes.json`, 저장소 어디에도 두지 않습니다. 회사 서버의 비밀 저장소에만 둡니다.
3. 공개판 빌드는 `.env`를 읽지 않습니다 (`core/app_identity.py`의 "개발판" 표시 하나로 끔).
4. 결과마다 출처·지연·표시권 결과를 붙입니다 (`core/research/display_rights.json`과 연결). 화면은 이 값을 그대로 보여 줍니다. 그래서 공급원이 바뀌어도 화면 코드는 바뀌지 않습니다.
5. 키 입력 화면과 연결 화면은 `gateway.status()`가 주는 행을 그대로 그립니다. 공급원 이름을 화면 코드에 박지 않습니다. 법인 뒤 "회사 제공 (로그인 필요)" 행이 생겨도 화면 수정이 없습니다.
6. 키를 넣거나 지우면 게이트웨이가 해당 클라이언트를 다시 만듭니다 (1.3절의 `ready` 함정 해결). 재시작이 필요 없습니다.

### 5.4 공급원별 길 (예시. 법인 뒤 값은 계약 답으로 확정)

| 공급원 | 키 종류 | 지금 (`personal`) | 법인 뒤 (`commercial`, 예시) |
|---|---|---|---|
| KIS 시세·차트·실시간 | 사용자 증권사 키 | `local_key` | 코스콤이 사용자 키 구조를 허용하면 `local_key`, 아니면 `company` (코스콤 계약 데이터) — **미정** |
| KIS 잔고·주문 (주문은 나중) | 사용자 증권사 키 | `local_key` 고정 | `local_key` 고정 (서버 금지) |
| Upbit 잔고 | 사용자 거래소 키 | `local_key` 고정 | `local_key` 고정 |
| Upbit/Binance 공개 시세 | 키 없음 | `keyless` | `keyless` 또는 `company` (표시 조건 **미검증**) |
| FRED (금리·환율·VIXCLS) | 키 없음 | `keyless` | `keyless` + 고지 문구. VIXCLS는 Cboe 조건 확인 뒤 `company` 또는 `off` |
| Yahoo (yfinance) | 키 없음, 개인용 | `keyless` | `company` (서버가 대체 공급사로 같은 모양의 답) 또는 `off` |
| FMP | 키 | `local_key` | `company` (표시 계약) 또는 `off` |
| KRX Open API | 키 | `local_key` | `local_key` 또는 `company` (약관 **미검증**) |
| OpenDART | 키 (1인 1키) | `local_key` | `local_key` (사용자 본인 키) |
| Anthropic (AI 해설) | 사용자 키 | `local_key` (기본 꺼짐) | `local_key`. 수요 확인 뒤 `company` 중계 선택 |
| GS Marquee | 개인 키 | `local_key` | `off` 후보 |

### 5.5 지금 고치는 파일과 담당 세션

담당 원칙 (오늘 지시): 화면 (`quantgen_desktop/**`)은 UI 세션. 자격증명·게이트웨이 코드는 결제·계정 (API 키 포함) 하부 세션.

| 묶음 (ID 제안) | 파일 | 담당 | 공유 파일 (대기열 경유) |
|---|---|---|---|
| **KEY-2** 자격증명 저장소 (원안 그대로, `quantgen_cloud` 자리만 뺌) | 새 `core/credentials/**`, `tests/credentials_*`; `config.py` `_clean` (비밀 이름 10개만 저장소로); `data/krx/kis_client.py` 토큰 캐시 (`:54`, `:179-191`); `requirements.txt`·`pyproject.toml` (`keyring`); `runtime-smoke.yml` 경로·시험 줄 | 결제·계정 | `config.py`, `kis_client.py`, `requirements.txt`, `pyproject.toml`, `.github/workflows/**` |
| **KEY-3** 게이트웨이 뼈대 | 새 `core/gateway/**` (입구, `routes.json`, `local.py`, `remote.py`, `codec.py`, `dispatch.py`), `tests/gateway_*` (가짜 서버 시험, 경계 시험) | 결제·계정 | `runtime-smoke.yml` 경로·시험 줄 |
| **KEY-4** core 호출 옮기기 | `core/` 18개 파일의 **공급사 호출 줄 46곳만** + `main.py:54`. 다른 줄은 손대지 않음. `core/research/markets.py`는 데이터소스 세션이 DS-H 안에서 같은 규칙으로 | 결제·계정 (+ 데이터소스: `markets.py`) | 없음 (단, KEY-4 기간에 이 줄들의 수정 권한을 마스터 3.1 표에 적음) |
| **KEY-5** 화면 쪽 옮기기 | `quantgen_desktop/` 6개 파일 14곳 (`app.py`, `market_chart.py`, `market_rankings.py`, `qscore.py`, `watchlist_live.py`, `market_tools.py`), `ui/` 6개 파일 11곳. 키 입력 화면·연결 화면을 `status()` 행으로 그림 | **UI 세션** (결제·계정 세션은 API만 제공) | 없음 |
| `app_identity` 값 자리 | `core/app_identity.py`에 `DATA_API_BASE` (빈 값), `GATEWAY_PROFILE` (`personal`), 개발판 표시 | OS 세션 | 없음 |
| 새 공급원 규칙 | 앱이 실행 중에 부르는 새 공급원 (예: Bigdata.com)은 `data/`에 클라이언트를 만들고 `routes.json`에 한 행 추가 (PR). 연구 도구 (`tools/didm/**`)는 대상 아님 | 데이터소스 | `routes.json` (결제·계정 세션 소유) |

### 5.6 공수 (추정, 한 세션의 작업일. 리뷰·CI 대기 제외)

| 묶음 | 작업일 | 비고 |
|---|---|---|
| KEY-2 | 1.5~2 | 원안과 같음 |
| KEY-3 | 3~4 | "`personal` ↔ 가짜 서버 경유 `commercial`로 바꿔도 같은 답" 시험 포함 |
| KEY-4 | 2~3 | 시험 24개 파일 122곳 중 일부 손봄. 주입 자리가 이미 있는 곳은 기본값만 바꿈 |
| KEY-5 | 1~1.5 | 키 화면·계정 화면 자체는 D7-A·D11 몫이라 별도 |
| `app_identity` 자리 | 0.2 | OS 세션 기존 작업에 포함 |
| **합계** | **약 8~11** (원안 대비 **+6~9**) | 병합은 대기열 10번 (F21 뒤) 순서: KEY-2 → KEY-3 → KEY-4 → KEY-5. 달력 기간은 대기열에 따라 2~3주 (추정) |

- KEY-5는 PyQt6→PySide6 변환 (D9)과 같은 화면 파일을 만집니다. 둘의 순서는 메인 세션이 대기열에서 정합니다. 권장: 변환을 먼저 하고 KEY-5를 뒤에 (KEY-5는 import 몇 줄이라 다시 맞추기 쉬움).

### 5.7 법인 때 남는 일 (설정·서버·계약만)

| 일 | 누가 | 종류 | 앱 코드 수정 |
|---|---|---|---|
| 계약: 코스콤/KRX, Yahoo 대체 공급사, FMP 표시 계약 또는 제외, Cboe (VIX), (선택) Anthropic 중계 약관 | 소유자 (법인) | 계약 | 없음 |
| 회사 데이터 서버: `dispatch.py`를 회사 키로 돌림, 계정·요금제 확인, 사용자 수 기록·보고, 속도 제한·캐시 | 결제·계정 세션 + AWS 설정 담당 (PAY-3) | 서버 | 없음 |
| Yahoo 대체: 서버 쪽에서 대체 공급사로 같은 모양의 답을 만듦 | 데이터소스 세션 (서버 쪽) | 서버 | 없음 |
| `routes.json`의 `commercial` 값 확정, `display_rights.json` 갱신 | 결제·계정 + 데이터소스 | 설정 | 설정 파일만 |
| `core/app_identity.py`: `DATA_API_BASE`, 운영 Cognito ID, `GATEWAY_PROFILE="commercial"`, 개발판 표시 끔 | OS 세션 | 설정 | 설정값만 |
| 서명된 공개 빌드 | OS 세션 | 빌드 | 없음 |

### 5.8 남는 위험

| 위험 | 영향 | 줄이는 법 |
|---|---|---|
| 계약 공급사가 "사용자 PC에서만 도는 SDK"만 허용 | 그 공급사용 내 PC 클라이언트 하나를 새로 만듦 (새 공급원 추가, 0.5~1일 추정). 화면·core 수정은 없음 | 계약 협상 때 "서버 API 제공"을 조건으로 물음 (**미검증**) |
| 계약이 화면에 특정 고지나 동의 창을 요구 | 문구 추가가 필요할 수 있음 | 출처·고지 문구를 결과 데이터에 실어 화면이 그대로 표시 (5.3 규칙 4) |
| 실시간 스트림을 회사 서버로 중계 | 서버 비용·지연 | 계약·서버 단계에서 판단. 사용자 키 허용 시 `local_key` 유지 |
| PyInstaller 묶음에서 keyring 백엔드 인식 | 키 저장 실패 | PyInstaller 6.18.0 소스에 keyring 훅이 있음. 실제 Windows 빌드 확인은 **미검증** (OS 세션 빌드 시험에 포함) |
| 개발 PC (Linux)의 키 보관함 | 개발 편의 | keyring은 Secret Service·KWallet도 지원. 동작은 **미검증**. 안 되면 `.env` 개발 예비 |
| "47개 이름" 수치 차이 | 목록 누락 | KEY-1에서 확인 (**미검증**) |

---

## 6. 초안에 반영할 곳 (메인 세션이 고칠 것)

| 위치 | 지금 | 바꿀 내용 |
|---|---|---|
| `OWNER_REPORT` D7 행 | "★A ... 법인 뒤에도 흐름이 같습니다" | "A 원안 거부 (데이터 길은 법인 뒤 다시 고쳐야 함) → ★G = A + 공급원 게이트웨이" |
| `MASTER` 5.3절 마지막 줄 | "자격증명 저장소 (KEY-2)에 `quantgen_cloud` 공급원 자리" | "공급원 게이트웨이 (KEY-3)에 회사 서버 길 (꺼짐)과 `commercial` 프로필 초안" |
| `MASTER` 부록 C 행 A·C | A: "법인 뒤에도 흐름 그대로", C: "자리만 미리" | A: "키 저장은 그대로. 데이터 길은 게이트웨이가 맡아야 그대로", C: "게이트웨이 회사 서버 길을 지금 만들고 꺼 둠 (D7-G)" |
| `MASTER` 3.1 세션 표, 7절 ID 표, 4.2 대기열 | KEY-2만 | 결제·계정 경로에 `core/gateway/**`, `tests/gateway_*`, KEY-4 기간의 core 18개 파일 공급사 호출 줄. ID KEY-3, KEY-4, KEY-5. 대기열 10번에 KEY-3 → KEY-4 → KEY-5 |
| `sessions/05` (결제·계정) | KEY-2의 "꺼진 공급원 `quantgen_cloud` 자리" | 그 줄 삭제. KEY-3, KEY-4 작업과 완료 조건 (경계 시험의 예외 목록 0, 가짜 서버 시험 녹색) 추가 |
| `sessions/02` (UI) | 키 화면 | **고치지 않음** (소유자 D6: 이미 돌아가는 UI/UX 세션은 건드리지 않음). KEY-5와 "키 화면·연결 화면은 `gateway.status()` 행을 그대로 그림"은 결제·계정 세션 인계 파일의 `## UI 세션에 전할 것`에 적고, 소유자가 원할 때 UI 세션에 옮김 |
| `sessions/06` (데이터소스) | DS-H `load_home_indicators` | 게이트웨이 경유. 새 공급원은 `routes.json` 한 행 |
| `sessions/04` (OS) | `app_identity` | `DATA_API_BASE`, `GATEWAY_PROFILE`, 개발판 표시 추가 |

---

## 7. 출처

저장소 (`origin/main` `e01e152`, 2026-11-14, 2026-11-17 읽음):
- `config.py:25-29, 32-39, 53-287` (변수 이름·줄), `core/markets.py:219-226`
- `data/krx/kis_client.py:20-24, 54, 174, 179-191, 206, 237`, `data/kis_stream.py:222-245`
- `data/krx/gateway.py:1-38`, `core/research/connections.py:21-34`, `core/research/markets.py:6-13, 81-83`
- `quantgen_desktop/app.py:61-85`, `quantgen_desktop/market_chart.py:405, 412`, `quantgen_desktop/watchlist_live.py:45, 48`, `quantgen_desktop/connections.py:6-13`
- 집계: `git grep`으로 `data/` 밖 `core/`·`quantgen_desktop/`·`ui/`·`main.py`의 공급사 import·`yfinance`·`api.anthropic.com`·`config` 키 함수 사용 = 31개 파일 72곳. `tests/` 24개 파일 122곳.
- `.env.example` 이름 14개 (값은 읽지 않음).

소유자·내부 문서:
- 소유자 11-17 답 (`owner_answer_1117.txt`, D7·D11 항목).
- Notion 11-16 메모 (`notion_1116.md:24-25, 29`).
- Notion "QUANTGEN 상업화 실행 분석서" `40e5c916fe0c815ba983dd4c4cc7992c` (2026-11-04 작성, 2026-11-06 수정, 2026-11-17 조회): 항목 2 (계좌 연동), 4 (API 키와 .env), 5 (시세 표시 권리), 7 (서버 구성).
- 업무 설계도 초안 `MASTER_WORK_DESIGN_2026-11-17.md` 3.1절, 5.3절, 부록 C; `sessions/05_PAYMENTS_ACCOUNT_KEYS_NEW.md` KEY-2.

공개 자료:
- KIS 제휴 안내 https://apiportal.koreainvestment.com/provider — 분석서 인용. 이번에 직접 열지 않음.
- KRX 데이터 수신 방법 https://openapi.krx.co.kr/contents/OPP/DATA/OPPDATA003.jsp — 분석서 인용. 2026-11-17 재확인 시도는 이 세션 네트워크에서 호스트가 막혀 실패 (**미검증**; 다시 보려면 세션 네트워크 설정에서 `openapi.krx.co.kr` 허용 필요).
- FMP 표시 라이선스 안내 https://site.financialmodelingprep.com/insights/platform/can-you-use-fmp-data-in-a-public-app-website-or-client-dashboard — 분석서 인용. 2026-11-17 재확인 시도는 호스트 차단으로 실패 (**미검증**; `site.financialmodelingprep.com` 허용 필요).
- yfinance 개인 사용 안내 https://github.com/ranaroussi/yfinance — 분석서 인용.
- Nasdaq 시스템 신청서 (사용자 수 월 보고) https://nasdaq.com/docs/systemapplication_0.pdf, Nasdaq 준수 정책 (권한 시스템 통제·보고) https://www.nasdaqtrader.com/content/AdministrationSupport/Policy/COMPLIANCEPOLICY.pdf — 2026-11-17 웹 검색 요약. 원문은 열지 않음 (**미검증**).
- Python keyring https://github.com/jaraco/keyring — 2026-11-17 열람: 지원 백엔드 macOS Keychain, Freedesktop Secret Service, KWallet, Windows Credential Locker.
- PyInstaller 6.18.0 keyring 훅 (Debian 소스 사본) https://sources.debian.org/src/pyinstaller/6.18.0%2Bds-3/PyInstaller/hooks/hook-keyring.py — 2026-11-17 검색. 실제 빌드 확인은 **미검증**.

이 문서의 법률·약관 관련 내용은 법률 자문이 아닙니다.
