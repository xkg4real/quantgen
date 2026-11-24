# KEY-5 요청문 v2: 화면 쪽 공급사 직접 호출 → core/gateway (UI 세션용)

작성: PAYMENTS_ACCOUNT_KEYS 세션, 2026-11-24 (메인 지시 2026-11-24 "P2. KEY-5 요청문 v2"). 이 파일은 초안입니다. 소유자가 메인의 확정 신호 뒤에 UI 세션에 붙여 넣습니다.
v1 `plans/2026-11-20/KEY5_UI_REQUEST.md` (KEY-4 head `148504a` 기준)는 낡았으므로 이 v2로 대신합니다. v1은 다른 세션이 참조할 수 있어 고치지 않고 그대로 둡니다.

## 0. 먼저 읽을 것 (전제)

1. **기준:** main `b872d8c` (2026-11-24) 과 UI PR #140 head `3483b53` (`gpt/ui-guide-chart-first-20261121`, 초안, K1a~K2d 포함). 줄 번호는 두 커밋에서 직접 읽었습니다 (`git show <ref>:<path>`).
2. **KEY-5/a는 병합됨:** PR #139 → main `dec979a` (원장 KEY-5/a). 그래서 v1 6절의 G1~G3과 3차 검토 C는 이미 main에 있습니다.
   - G1 `PROVIDER_MODULES["data.kis_stream"] = ("kis_quote",)`
   - G2 `data.kis_workspace`는 고정 로컬 `kis_quote`만 써서 막히지 않음 (순수 값 별도 목록 없음)
   - G3 `core/gateway/feed.py`의 `QuoteFeed`
   - A1R3-1 막힌 KRX·OpenDART 답에 사유
   - A1R3-4 `fmp_blocked`
   - A1R3-5 `on_change`
   - 검토 M1·M2도 main에서 고쳐짐 (메인 확인 2026-11-24: `core/gateway/feed.py:38-66`, `core/gateway/__init__.py:529-546`).
3. **OA-41 (`core.credentials.set_backend(None)` 가 안 / 나 안): 소유자 답 없음.**
   - 가 안: 시험에서만 memory·None 백엔드로 격리하고, 앱은 keyring을 유지.
   - 나 안: 앱도 `.env`만 씀.
   - 2026-11-21 메인이 기술 선택으로 **가 안**을 골랐고 GPT가 그대로 진행했습니다 (WORKBOARD OA-41 행).
   - 소유자의 명시적 답으로 세지 않습니다. 소유자가 나 안을 고르면 3절 "키 출처" 칸과 시험 격리 방식이 바뀝니다.
4. **OA-40 (PAY-3 회사 데이터 서버 위치 A 시드니 / B 서울 / C Cloudflare Workers): 아직 열림.** KEY-5 화면 작업에는 영향 없음. 회사 경로(`company`)는 지금 꺼져 있고, 화면은 `login_needed` 문구만 준비합니다.
5. **OS-F1(PySide6 전환) 뒤 적용 권장**은 v1과 같습니다. OS-F1 때 `quantgen_desktop/**`가 다시 움직이면 두 번 고치게 됩니다.

## 1. 지시문 (SESSION_PIPELINE 4절 양식)

```
[메인 → UI] 다음 일: KEY-5 화면 쪽 공급사 직접 호출을 core/gateway로
- 목표: tests/fixtures/gateway/known_direct_calls.json의 화면 항목을 0으로 (PR #140 병합 뒤 남는 8파일 25곳,
  #140이 병합되지 않으면 22파일 44곳; 아래 2절), 키·연결 화면(⑬-2/page-redesign/system/2)이 gateway.status()
  행을 그대로 그리게 한다(3절).
- 근거 파일: core/gateway/__init__.py (provider, stream, krx_gateway, ficc, keys_ready, local_key, status,
  status_loaders, endpoint, blocked, on_change, OffClient), core/gateway/feed.py (QuoteFeed),
  core/gateway/local.py (FiccData.EXPOSED·CONSTANTS), docs/commercial/GATEWAY_DESIGN.md 6절·7a절,
  tests/gateway_boundary_acceptance.py (SCREEN_CEILING, SCREEN_FILES, FROZEN).
- 완료 조건: 4절의 명령 → 모두 기대 결과.
- 하지 말 것: 5절.
- 끝나면: SESSION_PIPELINE 3절 형식으로 메인에 보고하고, --done 문자열(ID | 무엇 | 파일 | 커밋 | 검사)을 메인에 보냄.
  LEDGER는 메인이 씀.
```

## 2. 남은 화면 접점 (파일별)

### 2.1 개수 (fixture를 두 커밋에서 다시 셈)

| 기준 | 화면 | FROZEN | 합계 | 메인 확인값과 비교 |
|---|---|---|---|---|
| main `b872d8c` | 22파일 44곳 | `core/engine/feed.py` 1 | 23파일 45항목 | 같음 |
| PR #140 `3483b53` | **8파일 25곳** | 1 | 9파일 26항목 | 같음 (화면 25곳·8파일, 그중 12곳 = `ui/settings_page.py` 8 + `paper.py`·`crypto_page.py`·`macro_page.py`·`macro_state_panel.py` 각 1) |

PR #140은 14파일 19곳을 이미 gateway로 옮겼습니다 (2.3). 그러나 `SCREEN_CEILING`은 두 커밋 모두 `{"files": 22, "sites": 44}` 그대로입니다. PR #140이 병합될 때 8/25로 내리거나, KEY-5에서 0/0으로 내립니다 (4절).

### 2.2 KEY-5가 바꿀 곳 (PR #140 뒤 남는 8파일 25곳)

`gw` = `import core.gateway as gw`. 함수 안 지연 import는 `gw.provider(...)` 호출로 바꿉니다. `GatewayOff`는 지금 "키 없음"을 잡는 자리에서 잡고, 사유를 보여 줍니다 (3절).

줄 번호는 main `b872d8c`와 PR #140 `3483b53`에서 같습니다 (두 커밋에서 이 8파일의 해당 줄은 바뀌지 않음).

| # | 파일 | 줄 (main / #140) | 지금 호출 | 바꿀 gateway 입구 |
|---|---|---|---|---|
| 1 | quantgen_desktop/market_chart.py | 405 / 405 | `from data.kis_workspace import MarketDataService` | `gw.provider("data.kis_workspace").MarketDataService` |
| 2 | quantgen_desktop/market_chart.py | 412 / 412 | `from data.kis_stream import KISStream` | `gw.stream("kis_quote")` (route가 local_key·keyless일 때만, 아니면 `GatewayOff`) |
| 3 | quantgen_desktop/market_chart.py | 690 / 690 | `from data.kis_stream import subscription_for` | `gw.provider("data.kis_stream").subscription_for` (G1, main에 있음) |
| 4 | quantgen_desktop/market_chart.py | 702 / 702 | `from data.kis_workspace import availability_note` | `gw.provider("data.kis_workspace").availability_note` (G2: 고정 로컬이라 막히지 않음) |
| 5 | quantgen_desktop/market_chart.py | 718 / 718 | 같음 | 같음 |
| 6 | quantgen_desktop/market_chart.py | 1282 / 1282 | `from data.kis_workspace import supported_intervals` | `gw.provider("data.kis_workspace").supported_intervals` |
| 7 | quantgen_desktop/paper.py | 29 / 29 | `QuoteFeed()` (동결 엔진 피드, `fmp_client` 없음 → 자체 FMP 경로) | **`core.gateway.feed.QuoteFeed()`** (v1 표 14번; G3, main에 있음. `main.py`도 이것을 씀) |
| 8 | quantgen_desktop/watchlist_live.py | 45 / 45 | `from data.kis_workspace import MarketDataService` | `gw.provider("data.kis_workspace").MarketDataService` |
| 9 | quantgen_desktop/watchlist_live.py | 48 / 48 | `from data.kis_stream import KISStream` | `gw.stream("kis_quote")` |
| 10 | ui/crypto_page.py | 163 / 163 | `config.upbit_ready()` | `gw.keys_ready("upbit_account")` |
| 11 | ui/macro_page.py | 165 / 165 | `config.ficc_provider_status()` | `gw.status_loaders()[2]()` (순서: quant, KRX, FICC, crypto) 또는 3절 `gw.status()` 행 |
| 12 | ui/macro_state_panel.py | 653 / 653 | `config.kis_ready()` | `gw.keys_ready("kis_quote")` |
| 13 | ui/market_chart_page.py | 79 / 79 | `from data.kis_workspace import MarketDataService` | `gw.provider("data.kis_workspace").MarketDataService` |
| 14 | ui/market_chart_page.py | 84 / 84 | `from data.kis_stream import KISStream` | `gw.stream("kis_quote")` |
| 15 | ui/market_chart_page.py | 307 / 307 | `from data.kis_workspace import supported_intervals, availability_note` | `gw.provider("data.kis_workspace")`의 두 속성 |
| 16 | ui/market_chart_page.py | 307 / 307 | (같은 줄 두 번째 이름) | 같음 |
| 17 | ui/market_chart_page.py | 696 / 696 | `from data.kis_workspace import availability_note` | 같음 |
| 18 | ui/settings_page.py | 20 / 20 | `from data.krx.krx_market_client import KRXMarketClient` (모듈 맨 위; 114줄에서 `.probe()`) | 함수 안 `gw.provider("data.krx.krx_market_client").KRXMarketClient` (KRX Open API가 막히면 `GatewayOff` → 3절 문구) |
| 19 | ui/settings_page.py | 72 / 72 | `getattr(config, "ficc_provider_status")` (ref) | `gw.status_loaders()[2]` 또는 `gw.status()` |
| 20 | ui/settings_page.py | 138 / 138 | `from core.ficc.data import probe` | `gw.ficc().probe` (막힌 공급사는 건너뜀) |
| 21 | ui/settings_page.py | 167 / 167 | `from data.kis_markets import KISMarkets` | `gw.provider("data.kis_markets").KISMarkets` |
| 22 | ui/settings_page.py | 199 / 199 | `from data.crypto.crypto_client import probe` | `gw.provider("data.crypto.crypto_client", source="crypto_public").probe` |
| 23 | ui/settings_page.py | 248 / 248 | `config.quant_provider_status()` | `gw.status_loaders()[0]()` |
| 24 | ui/settings_page.py | 267 / 267 | `config.krx_provider_status()` | `gw.status_loaders()[1]()` |
| 25 | ui/settings_page.py | 281 / 281 | `config.crypto_provider_status()` | `gw.status_loaders()[3]()` |

`ui/settings_page.py`의 8곳(18~25)은 3절 키·연결 화면 작업과 같은 화면입니다. 3절대로 `gw.status()` 행을 그리면 23~25와 19는 그 행으로 대신할 수 있습니다.

FROZEN `core/engine/feed.py`의 `import:data.fmp.FMPQuoteClient` 1곳은 KEY-5 대상이 아닙니다 (S4 소유자 판정, 바이트 고정). `paper.py`가 `core.gateway.feed.QuoteFeed`를 쓰면 이 경로는 화면에서 더 쓰이지 않습니다.

### 2.3 PR #140이 이미 옮긴 곳 (#140이 병합되지 않으면 KEY-5가 함께 함)

main `b872d8c` 줄 → #140 `3483b53`의 바뀐 코드. 모두 2.2와 같은 입구를 씁니다.

| 파일 | main 줄 | 지금 호출 (main) | #140에서 |
|---|---|---|---|
| quantgen_desktop/app.py | 65, 80 | `from data.kis_workspace import MarketDataService` | 66–67, 82–83 `gateway.provider('data.kis_workspace').MarketDataService` |
| quantgen_desktop/home_view.py | 163 | `from core.ficc.data import load_series` | 183–184 `gateway.ficc().load_series` |
| quantgen_desktop/market_rankings.py | 159, 259 | `OVERSEAS_PRICE_DETAIL`, `MarketDataService` | 160–161, 260–261 `gateway.provider('data.kis_workspace')…` |
| quantgen_desktop/market_summary.py | 51 | `from core.ficc.data import load_series` | 52–53 `gateway.ficc().load_series` |
| quantgen_desktop/market_tools.py | 125 | `config.kis_ready()` | 124–125 `gateway.keys_ready('kis_quote')` |
| quantgen_desktop/qscore.py | 51 | `MarketDataService` | 51–52 `gateway.provider('data.kis_workspace').MarketDataService()` |
| ui/bonds_page.py | 28 | `load_treasury_curve` | 290 `gateway.ficc().load_treasury_curve` |
| ui/derivatives_page.py | 53 | `config.kis_ready()` | 53 `gateway.keys_ready("kis_quote")` |
| ui/fcharts.py | 1011 | `from core.ficc import data` | 1027 `gateway.ficc().load_short_rate` (34·1013줄 CONSTANTS import는 그대로) |
| ui/fx_page.py | 32 (3곳) | `load_fx_spot`, `load_policy_rates`, `load_short_rate` | 96·250·311·393·394 `gateway.ficc()…` |
| ui/krx_page.py | 19 | `from data.krx import KRXGateway` (타입 표기) | import 삭제, 50줄 `gateway: Any` (객체는 `gw.krx_gateway()` 결과) |
| ui/quant_lab_page.py | 27 | `from core.ficc import data as ficc_data` | 111·117 `gateway.ficc()…` |
| ui/rates_page.py | 40 (2곳) | `load_short_rate`, `load_treasury_curve` | 283·292·529 `gateway.ficc()…` |
| ui/structuring_page.py | 25 | `load_treasury_curve` | 373·416 `gateway.ficc().load_treasury_curve` |

## 3. 키·연결 화면 (⑬-2/page-redesign/system/2, KEY-4 2차 검토 F10)

- 화면은 `gw.status()`가 주는 행을 **그대로** 그립니다. 값은 없습니다. 행의 칸:
  - `source`, `label_key` (`gateway.source.<id>`), `route`, `state`
  - `needs`: 빠진 키 **이름**
  - `key_sources`, `delay`, `display_right`, `error`
- 키 값은 보이지 않고, 마스킹한 키 일부도 보이지 않습니다 (D7-G 규칙 5).
- `state`·`route`·사유별로 다른 문구를 씁니다. 지금처럼 모두 "키 없음"으로 뭉치지 않습니다.
- 영어 사유는 main `b872d8c`의 실제 문자열입니다. 한국어 문구는 초안이고, 확정은 UI 세션과 소유자가 합니다.

| state / 사유 | 뜻 | gateway가 주는 영어 사유 (main 실제 문자열) | 화면 문구 초안 |
|---|---|---|---|
| `ready` | 바로 씀 | — | 연결됨 |
| `key_needed` | 내 PC 경로인데 키가 없음 | `needs`에 키 이름 | 키 없음: `<이름>` 입력 필요 |
| `off` | 이 판(profile)에서 끈 공급사 | `GatewayOff`·`OffClient.reason`: `"<source> is off in profile <profile>"` | 이 판에서는 쓰지 않음 |
| `login_needed` (route `company`) | 회사 서버 경유, 로그인 전 | `"<source> is served by the company route in profile <profile>"` (core 입구는 끝에 `": only through client()"`가 붙음) | 회사 서버 경유: 로그인 필요 |
| FMP 막힘 (`core.gateway.feed.QuoteFeed.fmp_blocked`) | 시세 피드의 FMP | off: `"FMP market data is turned off. Check data-source settings."`<br>company: `"FMP market data is provided through the company connection. This device's key is not used."`<br>그 밖: `"FMP market data is unavailable. Check data-source settings."` | 위 off / company 문구와 같은 뜻 |
| KRX·OpenDART 막힘 (`gw.krx_gateway()` 답의 `reason`) | `market_snapshot`·`filings`·`financials`·`quote`·`indices` | `OffClient.reason`이 답에 실림 (A1R3-1). "Set KRX_API_KEY" 대신 이 사유 | 위 off / company 문구와 같게 |
| `error` 칸에 값 | routes.json을 읽지 못해 모두 막힘 | `_route_error` | 연결 설정 파일 오류: 공급사 사용 중지 |

- **바뀜 반영:** 경로 설정을 다시 읽거나 키를 넣고 지우면 화면을 다시 그립니다. 방법은 `gw.on_change(listener)`이고, `listener(name)`의 `name`은 공급원 id 또는 키 이름이며 전체일 때는 `""`입니다.
  - 이미 만든 `krx_gateway()` 객체와 `core.gateway.feed.QuoteFeed`는 KEY-5/a 덕분에 스스로 갱신됩니다.
- **키 출처 칸 (`key_sources`):** OA-41이 가 안(앱은 keyring 유지)인 동안 keyring / `.env` / 없음이 나옵니다. 소유자가 나 안을 고르면 `.env` / 없음만 나옵니다.

## 4. 완료 조건

| 명령 | 기대 결과 |
|---|---|
| `python -m unittest tests.gateway_boundary_acceptance` | PASS. 같은 PR에서 `SCREEN_CEILING`을 `{"files": 0, "sites": 0}`으로 내리고 `SCREEN_FILES`를 빈 목록으로 한 상태에서 PASS |
| `python -m tests.gateway_boundary_acceptance --write-known` 뒤 `git diff tests/fixtures/gateway/known_direct_calls.json` | 화면 항목 0. `core/engine/feed.py` FROZEN 1줄만 남음 (totals: `screens` 0, `core_and_main` 1, `files` 1) |
| 화면 같은 답 시험 (새 시험, `tests/gateway_same_answer_acceptance.py` 방식) | 아래 순서로 만들고, 바꾼 뒤 같은 요청에 같은 답이 나와야 함 |
| 막힘 시험 | 세 조건 각각에서 화면이 뜨고 3절 문구가 나오며 네트워크 호출이 0이어야 함 (`gateway_main_acceptance`처럼 요청 기록) |
| 화면 문구 변경 목록 | PR 본문에 바뀐 문구 표 (전/후, 한·영, 3절 행별) |
| UI 기존 시험 | 실패 집합이 main과 같음 |
| `python -m unittest tests.gateway_acceptance tests.gateway_main_acceptance tests.gateway_same_answer_acceptance tests.gateway_remote_acceptance` | main과 같은 수 이상 OK |
| `python3 -B -m tools.compliance.check --check` | consistency PASS |

**화면 같은 답 시험 만드는 순서**
1. 바꾸기 **전** main에서 고정값(fixture)을 만듭니다.
2. 공급사 가짜를 실제 시그니처에 묶습니다 (`inspect.signature(...).bind`).
3. 호출 기록과 답을 `canon()`으로 비교합니다. 실수는 rel 1e-6 / abs 1e-9 허용, 긴 목록은 앞뒤 정확 + 합·제곱합·위치가중합, 정수는 정확.
4. 날짜에 따라 바뀌는 문구는 지웁니다.

**막힘 시험의 세 조건**
- profile `commercial` (fmp off)
- `krx_open_api: off`
- routes 파일이 깨진 경우

## 5. 하지 말 것

- 이 문서는 **요청만** 합니다. `quantgen_desktop/**`·`ui/**` 수정은 UI 세션 몫이고, PAYMENTS 세션은 그 파일을 고치지 않습니다.
- `gpt/*` 브랜치(예: PR #140 `gpt/ui-guide-chart-first-20261121`)를 다른 세션이 고치지 않습니다. #140과 KEY-5의 순서는 메인이 MERGE_QUEUE에 정합니다.
- UI 세션 범위 밖 파일 (`core/**`, `data/**`, `main.py`, `config.py`)을 고치지 않습니다. gateway 쪽 변경이 필요하면 메인을 거쳐 PAYMENTS 세션에 요청합니다.
- 동결 파일 `core/engine/feed.py`, `state.py`, `runtime.py`, `__init__.py`를 건드리지 않습니다 (S4 판정, 바이트 고정).
- `core/gateway/routes.json`의 값이나 profile 값을 바꾸지 않습니다.
- 키 값을 쓰거나 출력하거나 요청하지 않고, `.env`·사용자 데이터 폴더의 키 파일을 열지 않습니다. 시험은 `.env`를 읽지 않습니다 (dotenv patch, scratch HOME).
- `tools/provider_parity/parity_check.py`를 수정하지 않습니다 (sha 고정).

## 6. 소유자가 붙여 넣는 방법 (한 줄)

메인의 확정 신호 뒤, UI 세션 대화창에 "handoff 브랜치 `plans/2026-11-24/KEY5_UI_REQUEST_V2.md`를 읽고 1절 지시문대로 진행해 주세요"라고 붙여 넣습니다.
