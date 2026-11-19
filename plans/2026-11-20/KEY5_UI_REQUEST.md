# KEY-5 요청문 초안: 화면 쪽 공급사 직접 호출 → core/gateway (UI 세션용)

작성: PAYMENTS_ACCOUNT_KEYS 세션, 2026-11-20 (메인 지시 2026-11-20 00:50 KST). 이 파일은 초안입니다. 소유자가 메인의 확정 신호 뒤에 UI 세션에 붙여 넣습니다.

## 0. 먼저 읽을 것 (적용 전제)

1. **기준 커밋:** KEY-4 PR #133 head `148504a` (브랜치 `claude/payments-key4-20261119`, **아직 main 병합 전**). 아래 줄 번호는 이 커밋 기준입니다. 메인이 KEY-4 병합 뒤 "확정" 신호를 주면 PAYMENTS 세션이 줄 번호만 다시 맞춥니다 (`python -m tests.gateway_boundary_acceptance --write-known`이 다시 만든 목록과 대조).
2. **OS-F1(PySide6 전환) 뒤에 적용 권장.** OS-F1 날 `quantgen_desktop/**`·`tests/desktop_*`가 잠기므로, 그 전에 시작하면 두 번 고치게 됩니다 (`REMAINING_WORK_2026-11-17.md` OS-F1·KEY-5 줄).
3. **그 전에 정할 것 (소유자/메인):** `core.credentials.set_backend(None)` 사용 여부.
   - 무엇: 키·연결 화면(system/2)과 그 시험이 OS 자격 증명 저장소(keyring)를 읽게 둘지, `set_backend(None)`("OS 저장소 없음")으로 막을지.
   - 가 안: 시험에서만 `set_backend(None)`(또는 메모리 백엔드)를 쓰고 앱은 keyring을 그대로 씀. 시험이 실제 OS 저장소를 건드리지 않음.
   - 나 안: PySide6 빌드에서 keyring 사용이 불안정하면 앱도 `set_backend(None)`으로 시작하고 `.env`만 씀. 화면의 "키 출처" 칸이 달라짐.
   - 결정 전에는 UI 세션이 이 부분을 시작하지 않습니다.
4. 이 일은 D7-G 소유자 승인 뒤에만 합니다 (REMAINING_WORK 32줄).

## 1. 지시문 (SESSION_PIPELINE 4절 양식)

```
[메인 → UI] 다음 일: KEY-5 화면 쪽 공급사 직접 호출을 core/gateway로
- 목표: tests/fixtures/gateway/known_direct_calls.json의 화면 항목 22파일 44곳을 모두 gateway 입구로 바꾸고
  (아래 2절 표), 키·연결 화면(⑬-2/page-redesign/system/2)이 gateway.status() 행을 그대로 그리게 한다(3절).
- 근거 파일: core/gateway/__init__.py(provider, krx_gateway, ficc, keys_ready, status, status_loaders, stream,
  blocked, endpoint), core/gateway/local.py(FiccData.EXPOSED·CONSTANTS), docs/commercial/GATEWAY_DESIGN.md 6절·7a절,
  tests/gateway_boundary_acceptance.py(SCREEN_CEILING, SCREEN_FILES, FROZEN), main.py의 QuoteFeed 하위 클래스.
- 완료 조건: 4절의 명령 → 모두 기대 결과.
- 하지 말 것: 5절.
- 끝나면: SESSION_PIPELINE 3절 형식으로 메인에 보고하고, 메인에 --done 문자열(ID | 무엇 | 파일 | 커밋 | 검사)을 보고. LEDGER는 메인이 씀.
```

## 2. 파일별 표 (22파일 44곳, `148504a` 기준)

`gw` = `import core.gateway as gw`. "모듈 위치 그대로"인 import는 함수 안 지연 import를 `gw.provider(...)` 호출로 바꾸는 것을 뜻합니다. 막힘(`GatewayOff`)은 지금 "키 없음"과 같은 자리에서 잡되 사유를 보여 줍니다(3절).

| # | 파일 | 줄 | 지금 호출 | 바꿀 gateway 입구 |
|---|---|---|---|---|
| 1 | quantgen_desktop/app.py | 65 | `from data.kis_workspace import MarketDataService` | `gw.provider("data.kis_workspace").MarketDataService` |
| 2 | quantgen_desktop/app.py | 80 | 같음 | 같음 |
| 3 | quantgen_desktop/home_view.py | 163 | `from core.ficc.data import load_series` | `gw.ficc().load_series` |
| 4 | quantgen_desktop/market_chart.py | 405 | `from data.kis_workspace import MarketDataService` | `gw.provider("data.kis_workspace").MarketDataService` |
| 5 | quantgen_desktop/market_chart.py | 412 | `from data.kis_stream import KISStream` | `gw.stream("kis_quote")` (route가 local_key/keyless일 때만, 아니면 GatewayOff) |
| 6 | quantgen_desktop/market_chart.py | 690 | `from data.kis_stream import subscription_for` | **G1 필요** (6절): `data.kis_stream`이 PROVIDER_MODULES에 없음 |
| 7 | quantgen_desktop/market_chart.py | 702 | `from data.kis_workspace import availability_note` | `gw.provider("data.kis_workspace").availability_note` (또는 G2) |
| 8 | quantgen_desktop/market_chart.py | 718 | 같음 | 같음 |
| 9 | quantgen_desktop/market_chart.py | 1282 | `from data.kis_workspace import supported_intervals` | `gw.provider("data.kis_workspace").supported_intervals` (또는 G2) |
| 10 | quantgen_desktop/market_rankings.py | 159 | `from data.kis_workspace import OVERSEAS_PRICE_DETAIL` | `gw.provider("data.kis_workspace").OVERSEAS_PRICE_DETAIL` (또는 G2) |
| 11 | quantgen_desktop/market_rankings.py | 259 | `from data.kis_workspace import MarketDataService` | `gw.provider("data.kis_workspace").MarketDataService` |
| 12 | quantgen_desktop/market_summary.py | 51 | `from core.ficc.data import load_series` | `gw.ficc().load_series` |
| 13 | quantgen_desktop/market_tools.py | 125 | `config.kis_ready()` | `gw.keys_ready("kis_quote")` |
| 14 | quantgen_desktop/paper.py | 29 | `QuoteFeed()` (동결 피드, `fmp_client` 없음 → 자체 FMP 경로) | `main.py`의 게이트웨이 하위 클래스 `QuoteFeed`를 공용 모듈로 옮겨 재사용 (**G3**), 또는 `fmp_client=`에 `gw.provider("data.fmp").FMPQuoteClient()`(GatewayOff면 `None`) |
| 15 | quantgen_desktop/qscore.py | 51 | `from data.kis_workspace import MarketDataService` | `gw.provider("data.kis_workspace").MarketDataService` |
| 16 | quantgen_desktop/watchlist_live.py | 45 | 같음 | 같음 |
| 17 | quantgen_desktop/watchlist_live.py | 48 | `from data.kis_stream import KISStream` | `gw.stream("kis_quote")` |
| 18 | ui/bonds_page.py | 28 (호출 290) | `from core.ficc.data import load_treasury_curve` | `gw.ficc().load_treasury_curve` |
| 19 | ui/crypto_page.py | 163 | `config.upbit_ready()` | `gw.keys_ready("upbit_account")` |
| 20 | ui/derivatives_page.py | 53 | `config.kis_ready()` | `gw.keys_ready("kis_quote")` |
| 21 | ui/fcharts.py | 1011 (호출 1025) | `from core.ficc import data` → `data.load_short_rate(...)` | `gw.ficc().load_short_rate(...)` (34줄 `CurvePanel, Series`는 CONSTANTS라 그대로) |
| 22 | ui/fx_page.py | 32 (호출 250·311·393) | `load_fx_spot` | `gw.ficc().load_fx_spot` (`G10_KRW`, `Series`는 CONSTANTS라 그대로) |
| 23 | ui/fx_page.py | 32 (호출 394) | `load_policy_rates` | `gw.ficc().load_policy_rates` |
| 24 | ui/fx_page.py | 33 (호출 96) | `load_short_rate` | `gw.ficc().load_short_rate` |
| 25 | ui/krx_page.py | 19 | `from data.krx import KRXGateway` (51줄 타입 표기용) | import 지우고 타입은 문자열/`Any`; 객체는 `main.py`가 넘기는 `gw.krx_gateway()` 결과 그대로 |
| 26 | ui/macro_page.py | 165 | `config.ficc_provider_status()` | `gw.status_loaders()[2]()` (순서: quant, KRX, FICC, crypto) 또는 3절의 `gw.status()` 행 |
| 27 | ui/macro_state_panel.py | 653 | `config.kis_ready()` | `gw.keys_ready("kis_quote")` |
| 28 | ui/market_chart_page.py | 79 | `from data.kis_workspace import MarketDataService` | `gw.provider("data.kis_workspace").MarketDataService` |
| 29 | ui/market_chart_page.py | 84 | `from data.kis_stream import KISStream` | `gw.stream("kis_quote")` |
| 30 | ui/market_chart_page.py | 307 | `from data.kis_workspace import supported_intervals, availability_note` | `gw.provider("data.kis_workspace")` 속성 (또는 G2) |
| 31 | ui/market_chart_page.py | 307 | (같은 줄 두 번째 이름) | 같음 |
| 32 | ui/market_chart_page.py | 696 | `from data.kis_workspace import availability_note` | 같음 |
| 33 | ui/quant_lab_page.py | 27 (호출 111·117, 495) | `from core.ficc import data as ficc_data` | `gw.ficc()`; 495줄 자체 점검의 `ficc_data.load_series = _boom` 바꿔 끼우기는 `gw.ficc()` 객체가 아니라 시험 쪽 patch로 옮김 |
| 34 | ui/rates_page.py | 40 (호출 529) | `load_short_rate` | `gw.ficc().load_short_rate` |
| 35 | ui/rates_page.py | 40 (호출 283·292) | `load_treasury_curve` | `gw.ficc().load_treasury_curve` |
| 36 | ui/settings_page.py | 20 | `from data.krx.krx_market_client import KRXMarketClient` (모듈 맨 위) | 함수 안 `gw.provider("data.krx.krx_market_client").KRXMarketClient` |
| 37 | ui/settings_page.py | 72 | `getattr(config, "ficc_provider_status")` (ref) | `gw.status_loaders()[2]` 또는 `gw.status()` |
| 38 | ui/settings_page.py | 138 | `from core.ficc.data import probe` | `gw.ficc().probe` (막힌 공급사는 건너뜀) |
| 39 | ui/settings_page.py | 167 | `from data.kis_markets import KISMarkets` | `gw.provider("data.kis_markets").KISMarkets` |
| 40 | ui/settings_page.py | 199 | `from data.crypto.crypto_client import probe` | `gw.provider("data.crypto.crypto_client").probe` |
| 41 | ui/settings_page.py | 248 | `config.quant_provider_status()` | `gw.status_loaders()[0]()` |
| 42 | ui/settings_page.py | 267 | `config.krx_provider_status()` | `gw.status_loaders()[1]()` |
| 43 | ui/settings_page.py | 281 | `config.crypto_provider_status()` | `gw.status_loaders()[3]()` |
| 44 | ui/structuring_page.py | 25 (호출 373·416) | `from core.ficc.data import load_treasury_curve` | `gw.ficc().load_treasury_curve` |

이 밖에 `core/engine/feed.py`의 `import:data.fmp.FMPQuoteClient` 1곳은 **동결(FROZEN)**이라 KEY-5 대상이 아닙니다 (S4 소유자 판정, 바이트 고정).

## 3. 키·연결 화면 (⑬-2/page-redesign/system/2, KEY-4 2차 검토 F10)

- 화면은 `gw.status()`가 주는 행을 **그대로** 그립니다. 행: `source`, `label_key`, `route`, `state`, `needs`(빠진 키 **이름**), `key_sources`, `delay`, `display_right`, `error`. 값은 없음.
- `state`별로 다른 문구를 씁니다. 지금처럼 모두 "키 없음"으로 뭉치지 않습니다.

| state / route | 뜻 | 화면 문구 초안 (확정은 UI 세션 + 소유자) |
|---|---|---|
| `ready` | 바로 씀 | 연결됨 |
| `key_needed` | 내 PC 경로인데 키가 없음 (`needs`에 이름) | 키 없음: `<이름>` 입력 필요 |
| `off` | 이 판(profile)에서 끈 공급사 | 이 판에서는 쓰지 않음 |
| `login_needed` (route `company`) | 회사 서버 경유, 로그인 전 | 회사 서버 경유: 로그인 필요 |
| `error` 칸에 값 | routes.json을 읽지 못해 모두 막힘 | 연결 설정 파일 오류: 공급사 사용 중지 |
| `GatewayOff` 사유 (`blocked()`의 "off"/"company") | 화면 동작 중 막힘 | 위 off/company 문구와 같게 |

- 키 값, 마스킹한 키 일부도 보이지 않습니다 (D7-G 규칙 5).

## 4. 완료 조건

| 명령 | 기대 결과 |
|---|---|
| `python -m unittest tests.gateway_boundary_acceptance` | PASS, 그리고 `SCREEN_CEILING`을 `{"files": 0, "sites": 0}`으로 내린 상태에서도 PASS (같은 PR에서 상한을 0/0으로 바꿈, `SCREEN_FILES` 빈 목록) |
| `python -m tests.gateway_boundary_acceptance --write-known` 뒤 `git diff tests/fixtures/gateway/known_direct_calls.json` | 화면 항목 0, `core/engine/feed.py` FROZEN 1줄만 |
| 화면 같은 답 시험 (새 파일, `tests/gateway_same_answer_acceptance.py` 방식) | 바꾸기 **전** main에서 고정값(fixture)을 만들고, 바꾼 뒤 같은 요청에 같은 답. 방식: 공급사 가짜를 실제 시그니처에 묶고(`inspect.signature(...).bind`), 호출 기록과 결과를 `canon()`으로 정리해 비교(부동소수 rel 1e-6 / abs 1e-9). 화면은 PyQt6 offscreen / Flet 가짜 Page로 그림 |
| 막힘 시험 | profile `commercial`(fmp off), `krx_open_api: off`, routes 파일 깨짐 각각에서 화면이 뜨고 3절 문구가 나옴, 네트워크 호출 0 |
| 화면 문구 변경 목록 | PR 본문에 바뀐 문구 표 (전/후, 한·영) |
| UI 기존 시험 | UI 107개 모듈 기준 실패 집합이 main과 같음 |
| `python3 -B -m tools.compliance.check --check` | PASS |

## 5. 하지 말 것

- UI 세션 범위 밖 파일 수정 (`core/**`, `data/**`, `main.py`, `config.py`). 필요한 gateway 변경은 6절처럼 PAYMENTS 세션이나 메인에 요청.
- 동결 파일: `core/engine/feed.py`, `state.py`, `runtime.py`, `__init__.py` (S4 판정, 바이트 고정).
- `core/gateway/routes.json`의 값 변경, profile 값 변경.
- 키 값 쓰기·출력·요청, `.env`·`~/.nextgen` 열기. 시험은 `.env`를 읽지 않음(dotenv patch).
- `tools/provider_parity/parity_check.py` 수정 (sha 고정).

## 6. 먼저 필요한 gateway 쪽 일 (PAYMENTS 세션이 따로 PR)

| ID | 무엇 | 왜 |
|---|---|---|
| G1 | `PROVIDER_MODULES`에 `"data.kis_stream": ("kis_quote",)` 추가, 또는 `subscription_for`를 순수 함수 목록으로 | 표 6번: 지금 gateway 입구가 없음 |
| G2 | `data.kis_workspace`의 순수 값(`availability_note`, `supported_intervals`, `OVERSEAS_PRICE_DETAIL`)을 FiccData.CONSTANTS처럼 공급사 접근이 아닌 목록으로 둘지 | 막힌 상태에서도 안내 문구는 보여야 함 |
| G3 | `main.py`의 `QuoteFeed` 하위 클래스를 공용 모듈(예: `core/gateway/feed.py`)로 옮김 | 표 14번 `paper.py`가 재사용 |

G1–G3이 KEY-5 PR보다 먼저 병합돼야 합니다. 메인이 순서를 정합니다.

## 7. 소유자가 붙여 넣는 방법

메인이 "KEY-5 확정"이라고 알리면, 이 파일의 1절 상자와 2–6절을 UI 세션 대화창에 그대로 붙여 넣습니다 (`git show origin/handoff:plans/2026-11-20/KEY5_UI_REQUEST.md`).

---

## 부록: PAY-3 회사 데이터 서버 위치 (소유자에게 물을 질문, 메인이 묶어서 전달)

**질문:** 상업판에서 앱이 공급사 데이터를 받을 "회사 데이터 서버"(`DATA_API_BASE`, routes의 `company` 경로)를 어디에 둘까요? 아래 셋 중 하나를 골라 주세요. 비용은 모두 **미검증 추정**이고, 공급사 계약(코스콤·KRX 등)이 서버 위치나 국내 보관을 요구하면 그 조건이 우선입니다 (**법률 자문이 아닙니다**; 근거: 계약 전이라 조건 미확인, `INCORPORATION_CHECKLIST.md` E1).

| 안 | 내용 | 장점 | 단점 | 월 비용 추정 (미검증) |
|---|---|---|---|---|
| A. AWS 시드니, Golden Hour Code 계정 | API Gateway + Lambda (회원 풀 `quantgen-prod`와 같은 계정·리전) | 계정·권한·CloudTrail(`qg-audit`)·예산 경보를 하나로; Cognito 토큰 검증이 바로 붙음 | 한국 사용자·KRX/KIS까지 왕복 지연이 큼(약 130–150ms, 미검증) | 사용자 적을 때 $0–10 (무료 사용량 안) |
| B. AWS 서울 (ap-northeast-2), 같은 계정 | 같은 구성 또는 Lightsail 작은 서버 1대 | 한국 사용자·국내 공급사와 가까움; 국내 보관 요구가 있으면 맞추기 쉬움 | 리전 두 곳 관리(회원은 시드니, 데이터는 서울); 예산·경보를 서울에도 설정 | Lambda형 $0–10, Lightsail형 약 $5–10 |
| C. Cloudflare Workers | DNS가 이미 Cloudflare에 있음 | 사용자 가까운 곳에서 응답; 무료 한도가 큼(미검증) | 공급사 키를 Cloudflare 비밀값에 둠(AWS와 감사 기록 분리); 실행 시간 제한; Python 지원 범위 미검증 | 무료~$5 |

**PAYMENTS 세션 제안:** 공급사 계약 조건이 나오기 전에는 **A**로 시작하고, 국내 보관이나 지연 요구가 확인되면 B로 옮기기. 앱은 `DATA_API_BASE` 한 줄만 바뀌므로 옮기는 비용이 작습니다 (GATEWAY_DESIGN 8절).
