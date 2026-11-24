# 홈 지표 6개 데이터 계층 (DS-H, 2026-11-20)

- 담당: DATA_SOURCE_DIDM 세션. 화면 연결은 UI 세션 (`⑬-2/page-redesign/home` 실데이터 연결).
- 근거: 소유자 요청 (Notion, 2026-11-16) "메인화면 … 주요 지표 6개를 그래프와 함께 구현하도록(앱 키자마자 실시간)", 소유자 결정 D8 (2026-11-17: 6개 유지, 실시간은 BTC (Upbit)와 KOSPI (사용자 KIS 키가 있을 때)만, 나머지는 '일별(지연)'), D7-G/KEY-4 (core는 `core.gateway`로만 공급사에 닿음).
- 코드: `core/research/markets.py` `load_home_indicators(days=30, ...)`. 시험: `tests/home_indicators_acceptance.py` (오프라인 가짜 공급사).
- 기존 `load_markets()`는 그대로 둡니다 (KEY-4 같은 답 시험이 고정).

## 호출

```python
from core.research.markets import load_home_indicators
rows = load_home_indicators(days=90)      # 6행, SPECS 순서. 네트워크는 이 한 번의 호출 안에서만
```

- 일별 6개는 **게이트웨이 로더를 한 번 호출**합니다: `gateway.ficc().load_many([...6개...], source="auto", days=days)`. Yahoo 그룹(^GSPC, ^KS11, BTC-USD)과 FRED 그룹(DEXKOUS, DGS10, VIXCLS)을 기존 로더에 넘깁니다. 이 1회는 Python 로더 호출 수이며, 공급사별 실제 HTTP 요청 1회를 보장하지 않습니다. 라이브러리·fallback·조회 ID에 따라 여러 HTTP 요청이 발생할 수 있고, 실제 요청 횟수는 여기서 검증하지 않았습니다.
- 실시간: BTC = `gateway.provider("data.crypto.crypto_client", source="crypto_public")`의 Upbit `KRW-BTC` ticker (키 없음). KOSPI = `gateway.keys_ready("kis_quote")`가 참일 때만 KIS `index("KOSPI")` (키가 없으면 부르지 않음).
- 화면은 시작 직후 이 함수를 **작업 스레드에서** 부르고, 실시간 값은 같은 함수를 `live=True`로 주기적으로 다시 부르거나 (일별은 캐시 권장) 따로 갱신합니다. 주기 결정은 UI 세션.

## 행 (dict)

| 키 | 뜻 |
|---|---|
| `label`, `symbol`, `provider` (`YFINANCE`/`FRED`), `unit`, `route` | `SPECS` 그대로 |
| `value`, `change`, `observation_date` | 마지막 관측값, 전일 대비 (% 단위; `unit == "%"`인 금리는 ×100 = bp), 관측일 |
| `status` | `OBSERVED` / `STALE` (관측일이 7일 넘게 지남) / `UNAVAILABLE` |
| `reason_code`, `error_code` | 실패 사유 코드 (`FAILURE_REASONS` 중 하나), 예외 이름. 공급사 문구·URL은 들어가지 않음 |
| `history` | `[{"date", "value"}]` 오래된 것부터, 최대 `days`개. 그래프용. 실패하면 `[]` |
| `delay` | `delayed_daily` (Yahoo) / `daily` (FRED) — 화면의 "일별(지연)" 표시용 |
| `display` | `{"source", "policy", "outcome", "publication_authorization"}` — `core/research/display_rights.json`의 `home` 행. Yahoo 3개 `rights_replace`, FRED 2개 `rights_conditional`, VIX `rights_conditional` (Cboe). 공개 허가 false |
| `live` | BTC·KOSPI만, 나머지는 `None`. `{"source" (UPBIT/KIS), "unit", "value", "change_pct", "as_of", "status" (LIVE / KEY_NEEDED / UNAVAILABLE), "reason_code", "display_outcome"}` |

주의:
- **BTC의 실시간 값은 원화 (`KRW-BTC`, Upbit)이고, 일별 값·그래프는 달러 (`BTC-USD`, Yahoo)입니다.** 단위가 다르므로 한 숫자로 섞지 말고 `live.unit`을 함께 보여 주세요. (하나로 맞추려면 소유자 결정 필요: 일별도 Upbit 원화로 바꾸거나, 실시간을 Binance USDT로 바꾸기.)
- **합성 값은 없습니다.** 로더가 공급사 실패로 모의 시계열을 돌려주면 그 행은 `UNAVAILABLE`, `value`·`history`가 비고 `reason_code`에 이유 (예: `rate_limited`, `network_error`, `connection_not_configured` = 게이트웨이에서 꺼짐).
- 실시간 값이 실패해도 일별 행은 그대로입니다 (`live.status = UNAVAILABLE`).
- KIS 키 준비 상태를 확인하는 과정 자체가 실패해도 KOSPI의 실시간 필드만 `UNAVAILABLE`로 격리합니다. 나머지 일별 행과 BTC 실시간 값은 반환하고, 예외 문구 대신 허용된 `reason_code`만 제공합니다.
- 이력에 남길 모든 관측일은 실제 달력의 `YYYY-MM-DD` 형식인지 검증합니다. 중간 날짜가 잘못된 행도 `UNAVAILABLE`로 반환하며 잘못된 차트 이력을 게시하지 않습니다.

## 확인 (2026-11-20, 브랜치 `claude/ds-home-indicators-20261120`)

- `tests.home_indicators_acceptance` 20 OK (한 번 호출, 기록·변화율, 표시권, 합성 값 거부, 게이트웨이 꺼짐 사유, 전체 실패 시 비밀 문구 없음, NaN은 버리고 채우지 않음, 실시간 단위·키 없을 때 호출 안 함, 실패 격리, 기본 경로가 `gateway.ficc/provider/keys_ready`를 씀).
- 게이트웨이 경계·같은 답·main·원격, 자격 증명, 홈·연구 계약 시험: 브랜치 177 OK, main `8445187` 157 OK (실패 집합 같음, 둘 다 없음).
- 실제 공급사 호출은 하지 않음 (클라우드 네트워크 막힘). 소유자 PC 진단 (OA-09)이 오면 원인 구분을 이 문서에 더함.

## 인계 재검증 보완 (2026-11-21)

- 오프라인 주입 재현에서 KIS 준비 상태 확인 예외가 함수 전체로 전파되는 경우와, 과거 이력 중간의 잘못된 날짜가 `OBSERVED`로 반환되는 경우를 확인해 수정했습니다.
- `tests.home_indicators_acceptance`는 23개 시험으로 확장했습니다. 준비 상태 확인 실패의 행 격리·문구 비노출, 잘못된 이력 날짜·비표준 날짜 거부, `live=False`일 때 준비 상태와 시세 미호출을 검증합니다.
- 모든 검증은 주입한 가짜 공급사와 소켓 차단 하에서 수행하며, 실제 HTTP·사용자 키·계정 저장소에 접근하지 않습니다.

## 소유자 PC 진단 (OA-09, 2026-11-24)

옛 H4 명령을 대신합니다. 앱 폴더에서:

```
python -m core.research.markets
```

- 여섯 줄 (지표마다 한 줄): `<기호> <상태> reason=<사유 코드> live=<실시간 상태>[ via=<yfinance가 남긴 원인>]`. 값·키·URL·공급사 문구는 나오지 않습니다. 늘 종료 코드 0.
- `via=`: yfinance는 네트워크 막힘·TLS 가로채기·요청 제한을 "빈 결과"로 바꿔 돌려주므로 (`reason=no_observations`), 진단 때만 yfinance 자체 기록을 모아 원인을 붙입니다: `rate_limited` (Yahoo 요청 제한), `certificate_error` (보안 프로그램·프록시의 TLS 가로채기), `network_timeout`, `network_error`.
- 명령은 먼저 앱 자료 폴더를 준비합니다 (`core.app_paths.ensure_user_data_dir`, 새 폴더는 본인만 읽기 권한 + QUANTGEN 표식). 준비가 거부되면 여섯 줄 모두 `reason=data_dir_unavailable`이고 공급사를 부르지 않습니다 (검토 PD-3).
- **아무것도 출력되지 않고 끝나면 오래된 체크아웃**입니다 (이 명령이 들어가기 전 코드는 출력 없이 종료 코드 0). 2026-10-29 이전 체크아웃은 `No module named core.research.markets`로 실패합니다. 두 경우 모두 코드 수정 없이 최신 main으로 바꾸면 됩니다.
- 읽는 법 (2026-11-24 검토 DS-3 + D11 사유 코드 분류 반영, 명령이 실제로 내는 값 기준):

| 출력 | 뜻 |
|---|---|
| FRED 3줄 `reason=network_error`, Yahoo 3줄 `via=network_error`, BTC `live=UNAVAILABLE/network_error` | 프록시를 거치는 연결이 막힘 (회사망·프록시 설정) |
| FRED 3줄 `reason=network_error`, Yahoo 3줄 `via=network_error` | **직접 연결 (보통 집 PC)에서 네트워크 실패**: DNS 실패·연결 거부·연결 끊김 (D11부터 FRED도 구분; 그 전 코드는 `provider_unavailable`) |
| FRED 3줄 `reason=network_timeout`, Yahoo 3줄 `via=network_timeout` 또는 `via=network_error` | 응답 없는 네트워크 (방화벽이 조용히 버림, 매우 느린 망). 아래 6분 주의 |
| FRED 3줄만 `provider_unavailable`, Yahoo 줄은 `OBSERVED` | FRED 쪽 오류 (서버 5xx 재시도 소진 등 전송이 아닌 실패) |
| Yahoo 3줄만 `via=certificate_error` | 보안 프로그램·프록시의 TLS 가로채기 |
| Yahoo 3줄만 `via=rate_limited` | Yahoo 요청 제한 (잠시 뒤 다시) |
| `dependency_missing` | venv 패키지 설치 |
| 출력 없음 | 오래된 체크아웃 (위) |

- 무응답 네트워크에서는 FRED 재시도 때문에 **명령이 약 6분 동안 아무것도 출력하지 않다가** 여섯 줄을 냅니다 (검토 실측 359.9초). 앱의 홈 카드도 그동안 빕니다.
