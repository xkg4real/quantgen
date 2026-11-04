# 파일럿 시계열 공급사 대조 설계 초안 (⑤-2)

- 상태: **초안, 소유자 검토 대기.** 이 문서의 허용치, 공급사, 순서는 모두 제안입니다. 승인된 것은 없습니다.
- **소유자 결정 반영 2026-11-04:** 12절 D-1~D-9에 소유자 답을 원문으로 적었습니다(12.1). 위 줄의 "승인된 것은 없습니다"는 결정 전의 상태입니다. 승인된 내용은 12.1에 있습니다.
- 작성: Claude (Step 7A 세션), 2026-11-04.
- 기준 커밋: `0bc9595`, 브랜치 `claude/amazing-gauss-tdiguu`. Step 7A.1(소유자 서명 기록)은 끝났고, 소유자의 Windows Step 7A.2는 아직입니다(`docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md:6-14`).
- 새로 만든 파일: 이 문서, `docs/nautilus_bridge/provider_parity_prototype/parity_check.py`, 같은 폴더의 `test_parity_check.py`. 추적 파일은 하나도 바꾸지 않았습니다. 커밋하지 않았습니다. 커밋 위치는 8.5절의 결정 사항입니다.
- 개정 1(같은 날): 검토 의견 15건을 코드와 대조해 고쳤습니다. 12건은 그대로, 3건은 일부 고쳐 반영했고, 거부한 것은 없습니다. 원형도 고쳤습니다. `day_boundary`는 상관 대신 차이만 쓰고, 공급사 역할은 도구에 고정하며, 오류는 종료 코드 4입니다(4.4, 5.5, 6.4, 11절).
- 줄여 쓰는 말: "스펙"은 `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md`, "러너"는 `tools/nautilus/runner.py`, "연구"는 `docs/asset_expansion_study.py`, "권리 표"는 `core/research/display_rights.json`, "공급사 감사"는 `docs/audit/2026-10-27/suppliers_ficc_btc.md`입니다.

## 0. 한눈에 보기

- **무엇을.** 파일럿이 읽는 세 파일을 다른 공급사 자료와 대조합니다. SPY 종가(`yf_SPY.csv`), BTC-USD 종가(`yf_BTC-USD.csv`), 무위험 금리 DGS3MO(`fred_DGS3MO.csv`)입니다.
- **어디서.** 도구는 소유자 PC에서만 실제 파일을 읽습니다. Claude는 합성 데이터로만 도구를 만들고 시험합니다.
- **Claude가 받는 것.** `summary.json` 하나입니다. 개수, 판정, 10단위 구간, 달력 날짜만 들어 있습니다. 가격, 수익률, 금리 값, 날짜별 차이는 `detail.json`에만 있고, 이 파일은 소유자 PC에 남습니다(6절).
- **판정.** 검사마다 PASS, FAIL, WARN, WITHHELD 가운데 하나입니다. 허용치는 결과를 보기 전에 정합니다(5절).
- **사전 등록의 빈틈을 막습니다(5.5).** 공급사의 역할과 규약은 도구에 고정합니다. 승인된 공급사는 모두 시도하고, 못 받은 것은 이유와 함께 요약에 남깁니다. 시계열마다 첫 완전 실행이 기록 실행입니다.
- **순서가 핵심입니다.** `tools/nautilus/` 아래에 도구를 넣으면 `code_sha256`이 바뀌어 `owner_confirmed`가 무효가 됩니다. 7A.5 뒤에 연구 브랜치에 파일을 더하면 Step 10의 diff 규칙에 걸립니다(8.1).
- **권고(8.3).** 선택지 A입니다.
  - 도구는 연구 브랜치 밖의 별도 브랜치에 둡니다.
  - 소유자는 7A.5 뒤, Step 8 전에 별도 클론에서 도구를 돌립니다.
  - 3.9 예외와 관문 규칙은 스펙만 바꾸는 커밋 하나로 7A.5 pull 전에 넣습니다. 허용치, 공급사 지도, 출력 허용 목록은 그 커밋의 스펙 본문에 그대로 넣습니다(부록 A).
  - 결과는 Step 10에 `runs/`, 스펙 10.4, 실행 기록에 적습니다. 이 세 곳은 Step 10 규칙이 허용하는 경로입니다.
  - A에서 자료 교체가 필요해지면 Step 7A 전체를 다시 합니다(5.4). 이 비용을 줄이려면 7A.2 전에 대조하는 A'를 고를 수 있습니다(8.2, D-1).
- **소유자 결정 9건**은 12절에 있습니다. **UNVERIFIED 목록**은 13절에 있습니다.
- **원형.** 비교 부분만 만들었습니다. 합성 데이터 26개 사례가 통과했습니다(11절). 실제 파일에는 돌리지 않았습니다.

## 1. 목적, 근거, 범위

### 1.1 과업 원문

| 출처 | 원문 |
|---|---|
| `docs/nautilus_bridge/REMAINING_WORK_2026-10-27.md:132` | "⑤-2 \| **파일럿 시계열 공급사 대조** \| Claude: 도구와 스펙 개정 → 사용자 PC에서 실행 \| ⑤-1, ⑥-1 전 필수" |
| `docs/nautilus_bridge/ROADMAP_REVIEW_2026-10-27.md:162` | "⑤-2 \| 2-1 **파일럿 시계열 공급사 대조** \| Claude: 도구 작성과 스펙 개정 → 사용자 PC에서 실행, 결과만 기록 \| ⑤-1. 반드시 ⑥-1 전" |
| `docs/audit/2026-10-29/QUANTGEN_PentPort_Strategic_Improvement_Audit_2026-10-29.md:179` | "compare the exact SPY/BTC pilot samples across independent providers and produce dates of disagreement … vendor disagreements report exact dates and magnitude before pilot." |
| `docs/nautilus_bridge/HANDOFF_MANUAL_2026-10-29.md:74` | "**데이터 출처 검증(⑤-2, ⑨-2, QG-P0-05).**" |
| `docs/nautilus_bridge/HANDOFF_MANUAL_2026-10-29.md:118` | 소유자 요약 원문의 "데이터 출처 검증 완료" |

### 1.2 왜 필요한가

- 브리지의 패리티는 엔진을 검증합니다. 데이터는 검증하지 않습니다. 카드에 "parity validates the engine, not the data"라고 적습니다(스펙 `:1163`).
- P0a는 러너가 읽은 값과 연구 로더가 읽은 값이 같은지 봅니다(스펙 `:771`). 같은 파일을 두 번 읽는 검사이므로, 파일 자체가 틀렸는지는 알 수 없습니다.
- md5 고정은 파일이 바뀌지 않았다는 것만 보장합니다. Yahoo가 수정주가 이력을 다시 쓰는 위험은 스펙 위험 12번에 있습니다(스펙 `:1705`).
- 그래서 ⑤-2는 고정된 파일이 다른 공급사의 같은 시계열과 맞는지 파일럿 전에 확인합니다.

### 1.3 범위

| 넣은 것 | 뺀 것 |
|---|---|
| 세 시계열(SPY, BTC-USD, DGS3MO)의 파일럿 구간 대조 | QG-P0-05의 나머지(모든 백테스트 입력에 지문·수집 시각·라이선스 붙이기). ⑨-2와 ResearchRun(PR-D) 몫입니다 |
| 날짜·달력, 종가, 배당·분할 조정, BTC 하루 경계, 빠진 날, 금리 단위 | 데이터 교체. 교체에는 새 표, 러너 수정, 새 `owner_confirmed`가 필요합니다(5.4) |
| 허용치와 판정, Claude 출력 제한, 기록 위치, Step 7A와의 순서 | 러너 수정. `tools/nautilus/`는 건드리지 않습니다(8.1) |
| 도구 인터페이스 초안, 합성 시험 계획, 비교 부분 원형 | 공급사 수신 코드. 원형에는 네트워크 코드가 없습니다 |

### 1.4 이 초안을 쓰며 읽은 것과 읽지 않은 것

- **읽은 것(코드와 문서만):** 스펙, 러너, 두 파일럿 표, 연구 로더, `core/quant/history.py`, `core/ficc/data.py`, `data/crypto/crypto_client.py`, `data/kis_markets.py`, `config.py`의 키 이름, 권리 표, 공급사 감사, 달력 YAML의 머리, 테스트의 스캔 범위. 개정 1에서 더 읽은 것: `data/krx/kis_client.py`(토큰 경로), 러너의 `fingerprint_mode`와 `_check_place`, `config.py`의 `macro_dir`, `tests/macro_m0_harness.py`의 T-RO-01 목록, 저장소 문서의 DTB3 언급(검색).
- **읽지 않은 것:** 보호 캐시 4개(`yf_SPY.csv`, `yf_BTC-USD.csv`, `binance_BTCUSDT.csv`, `upbit_KRW-BTC.csv`)는 이 sparse 클론에 없고 열지도 해시하지도 않았습니다. `fred_DGS3MO.csv`도 열지 않았습니다. `paper_live/out*/`, `grokteam/out/book/`, `~/.nextgen`, `.env`도 열지 않았습니다.
- **네트워크:** 데이터 공급사에 요청하지 않았습니다.
- **실행한 것:** 원형의 합성 자체 시험과 스캐너 패턴 재현뿐입니다. 허용된 인터프리터(`mvenv`, numpy 2.3.5, pandas 2.3.3)로, 새 HOME과 TMPDIR에서 돌렸습니다(11절).

## 2. 대조할 세 시계열

| 시계열 | 고정 파일과 md5 | 구간 | 러너가 읽는 방법 | 근거 |
|---|---|---|---|---|
| SPY 종가 | `docs/asset_expansion/cache/yf_SPY.csv`, `d2164597d576e1b2fcadde063065811d` | 2004-12-01 ~ 2026-09-25 | Yahoo `auto_adjust=True` 종가. 줄의 날짜 글자로 먼저 거르고, 첫 열을 색인으로, `dropna`, 0 초과, 300행 이상, `np.round(raw, 9)` | `docs/nautilus_bridge/registration/pilot1_E1_spy.json:10-13`; 스펙 `:769`, `:1629`; 연구 `:82-91`; 러너 `:644-675` |
| BTC-USD 종가 | `docs/asset_expansion/cache/yf_BTC-USD.csv`, `bc76f530ff24ab445367fe826150bc10` | 2014-09-17 ~ 2026-09-25(파일 전체), 7일 달력 | 위와 같음. 날짜 D는 UTC D+1 00:00에 닫히는 하루로 읽음 | `docs/nautilus_bridge/registration/pilot2_C3_btcusd.json:10-13`; 스펙 `:1644`; 러너 `:629-634` |
| 무위험 금리 DGS3MO(파일럿 1만) | `docs/asset_expansion/cache/fred_DGS3MO.csv`, `661722143f24930a29b58c535d227c1b` | SPY 세션에 맞춰 앞값 채움 | 퍼센트 값을 `dropna` 뒤 SPY 날짜로 `ffill`, `/100/252`. 3% 대체값은 쓰지 않음. 파일럿 2는 `rf_file: null`, rf = 0 | `pilot1_E1_spy.json:14-15`; 스펙 `:770`; 러너 `:678-695`; `pilot2_C3_btcusd.json:14-15` |

- 연구의 원래 로더는 금리를 읽다 예외가 나면 연 3%를 씁니다(연구 `:152-153`). 러너는 이 대체값을 쓰지 않고 R-06으로 거부합니다(스펙 `:770`).
  - 관찰(범위 밖): 같은 로더의 `fillna(0.03)`은 `/ 100.0` 앞에 있습니다(연구 `:150`). 그래서 첫 관측 전의 빈칸은 연 3%가 아니라 연 0.03%로 채워집니다. 예외 경로의 3%와 단위가 다릅니다. DGS3MO가 연구 구간보다 먼저 시작하면 영향이 없습니다(시작일 UNVERIFIED). 러너는 이 채움도 쓰지 않습니다(스펙 `:770`).
- 2004-12-01 이전 SPY 구간은 map 03이 이미 썼습니다(스펙 `:1683`). 이 과업은 그 구간을 다시 계산하지 않습니다.

## 3. 시계열별 공급사와 데이터 권리

역할은 네 가지입니다.
- **independent(독립):** 같은 규약의 다른 공급사입니다. 판정에 씁니다.
- **cross(교차 규약):** 규약이 다른 공급사입니다. SPY 총수익 조정과 분할만 조정을 견줘 배당 조정을 확인합니다. 판정에 씁니다.
- **vintage(수신 시점):** 같은 공급사를 지금 다시 받은 것입니다. 이력 재작성만 봅니다. 결과는 WARN까지만 냅니다.
- **diagnostic(진단):** 단위나 기초가 달라 참고만 합니다. 결과는 WARN까지만 냅니다.

아래 표의 공급사별 역할과 규약은 도구에 상수로 고정합니다(원형 `PROVIDERS`, `parity_check.py:57-64`). 명령줄로는 공급사 이름과 파일만 넘기고, 역할이나 규약은 고를 수 없습니다(5.5). 표에서 "선택"이 아닌 공급사는 필수입니다.

권리 표는 공개 승인도 법률 의견도 아니라고 적고(권리 표 `:4-5`), 각 시리즈에 "provider-level; dataset-specific rights remain unverified"라고 적습니다(예: `:66`, `:77`). 아래 권리 칸은 그 표와 공급사 감사를 옮긴 것이며, 법률 의견이 아닙니다.

### 3.1 SPY

| 공급사 | 코드 경로 | 규약 | 키 | 이력 깊이 | 역할 | 권리 상태 |
|---|---|---|---|---|---|---|
| Yahoo(고정 파일 A) | 연구 `:82-91`(`yfinance.download(..., auto_adjust=True)`) | 총수익 조정 | 없음 | 파일에 있음 | A | `yahoo`: rights_replace. 개인 API 접근은 서비스 권리가 아님(권리 표 `:862-905`) |
| FMP dividend-adjusted | `core/quant/history.py:123-187`. 응답 전체에서 `adjClose`를 한 번에 고름(`:163-165`) | 총수익 조정 | `FMP_API_KEY`(`config.py:52-53`) | 플랜에 따름. 2004년까지 닿는지 UNVERIFIED | independent | `fmp`: rights_conditional. 개인 플랜은 서비스 표시 계약이 아니고, 캐시·보관 범위는 서면 확인 필요(권리 표 `:1086`~) |
| KIS 해외 일봉 `AMS:SPY`, `MODP=1` | `data/kis_markets.py:459-473`; `core/quant/history.py:296-318`(`:308` "splits, not dividends") | 분할만 조정(가격 수익) | `KIS_APP_KEY`, `KIS_APP_SECRET`(`config.py:76-81`) | 100행씩 뒤로 넘김. 깊이 UNVERIFIED. SPY의 거래소 코드가 `AMS`인지 UNVERIFIED | cross | `kis_krx`: rights_conditional. 개인 투자용 API와 제3자 표시 권리는 다름(권리 표 `:1041`~; 공급사 감사 `:398`) |
| Yahoo 재수신 | `core/ficc/data.py:203-208`(`auto_adjust=True`) | 총수익 조정 | 없음 | 같음 | vintage | `yahoo`(위와 같음) |

### 3.2 BTC-USD

| 공급사 | 코드 경로 | 규약 | 키 | 이력 깊이 | 역할 | 권리 상태 |
|---|---|---|---|---|---|---|
| Yahoo(고정 파일 A) | 연구 `:82-91`. 배당 없음(`core/quant/history.py:279`) | USD, 하루 경계 UTC로 가정(UNVERIFIED) | 없음 | 파일에 있음 | A | `yahoo`(위와 같음) |
| Coinbase Exchange `BTC-USD` 일봉 | **코드 없음.** 공급사 감사가 권고만 함(`:306`, `:329`, `:341`) | USD, 단일 거래소, 버킷 시작 시각 라벨(UNVERIFIED) | 없음 | 2015년 시작으로 알려짐(UNVERIFIED; 공급사 감사 `:442`도 미확인). 늦게 시작해도 판정이 막히지 않게, 덮는 비율은 B의 구간 안에서 재고 구간 밖 날짜는 따로 셉니다(5.1, D-5) | independent | 공급사 감사: 사용자 기기 조회만, 캐시 배포 금지, 원문 미확인(`:404`, `:435`) |
| Bitstamp `BTC/USD` 일봉 | 코드 없음, 감사에도 없음 | USD | 없음 | 2014-09-17 이전부터로 알려짐(UNVERIFIED) | independent(선택). Coinbase가 없는 첫 몇 달을 덮음 | UNVERIFIED |
| Binance `BTCUSDT` | `data/crypto/crypto_client.py:189-226`. 날짜는 시작 시각의 UTC 날짜(`:221`) | **USDT** 호가 | 없음 | 2017-08-17부터(`crypto_client.py:7-8`) | diagnostic. USDT는 USD가 아니고, 구간의 약 76%만 덮음 | `Binance`: rights_verify(권리 표 `:1345`~) |

### 3.3 DGS3MO

| 공급사 | 코드 경로 | 단위 | 키 | 역할 | 권리 상태 |
|---|---|---|---|---|---|
| FRED 캐시(고정 파일 A) | 연구 `:94-104` | 퍼센트, 소수 2자리 | 없음 | A | DGS3MO는 권리 표에 없음. 같은 H.15 계열인 DGS10은 `fed_public`, rights_conditional(권리 표 `:33`, `:906`~). DGS3MO의 분류는 UNVERIFIED |
| US Treasury 일별 par yield curve의 "3 Mo" | **코드 없음.** 공급사 감사가 2순위로 권고(`:262-268`, `:331`, `:343`, `:415`) | 퍼센트 | 없음 | independent. 재무부가 원자료를 내고 H.15가 옮긴다는 관계는 UNVERIFIED | `Treasury`: rights_verify(권리 표 `:1216`~). 공급사 감사는 "미 연방 저작물, 추정"(`:402`) |
| FRED fredgraph 재수신 | `core/ficc/data.py:167-200`, `config.py:277` | 퍼센트 | 없음 | vintage | `fed_public`(위와 같음) |
| 연준 H.15 Data Download Program | 코드 없음 | 퍼센트 | 없음 | independent(선택) | UNVERIFIED |

### 3.4 쓰지 않는 공급사와 이유

| 공급사·경로 | 이유 | 근거 |
|---|---|---|
| `load_history(source="auto")` | 설정이 없으면 합성 시계열로 바뀝니다. 설정된 공급사가 실패하면 합성으로 바뀌지 않고 `HistoryError`를 냅니다. 설정 여부에 따라 결과의 뜻이 바뀌므로 대조에 쓰지 않습니다. 도구는 공급사 함수를 직접 부르고, `source`가 `SYNTHETIC`이면 거부합니다 | `core/quant/history.py:464-511`(독스트링 `:472-474`; 합성 분기 `:494`, `:504`, `:509`) |
| Upbit `KRW-BTC` | 원화 호가입니다. 김치 프리미엄 때문에 같은 시계열이 아닙니다 | `data/crypto/crypto_client.py:137-165` |
| CoinGecko | 상위 목록만 가져오는 코드입니다. 일봉 이력 경로가 없습니다 | `data/crypto/crypto_client.py:280` |
| KIS CME BTC 선물 | 선물이고 다른 상품입니다 | 공급사 감사 `:81` |
| FRED DTB3 | 다른 시계열입니다. 저장소의 통합 설계 문서는 DTB3를 할인율 기준이라 적고 환산을 요구합니다. 그 정의를 1차 출처로는 확인하지 않았습니다(UNVERIFIED). 레지스트리는 DTB3를 H.15 계열의 `history` 역할로만 적습니다 | `QUANTGEN_Quant_Council_2026-10-03/claude_code/QUANTGEN_MACRO_INTEGRATION.md:1440`; `data/macro/series_registry.yaml:572` |

### 3.5 이번 실행의 권리 처리(제안)

- 소유자 PC에서 개인 연구용으로만 받습니다. 받은 원자료는 소유자 PC의 `%LOCALAPPDATA%\quantgen\provider_parity\` 아래에 두고, 어떤 git 저장소에도 넣지 않습니다.
  - 공급사 감사가 이미 지적한 대로, 지금도 벤더 CSV 46개가 라이선스 기록 없이 git에 있습니다(SF-06, `suppliers_ficc_btc.md:113-118`). 새 파일을 더하지 않습니다.
- 커밋하는 `summary.json`에는 공급사 값이 없습니다. 그래서 재배포가 아닙니다. 다만 파생 지표는 입력 권리를 승계한다는 원칙이 있습니다(권리 표 `derived`, `:1388`~). 요약만 커밋해도 되는지는 D-4에서 소유자가 정합니다.
- 키는 이름만 적습니다: `FMP_API_KEY`, `KIS_APP_KEY`, `KIS_APP_SECRET`. 도구는 키 값을 출력하거나 기록하지 않습니다.

## 4. 무엇을 비교하나

검사 ID는 원형의 이름과 같습니다(`parity_check.py`의 줄 번호를 함께 적습니다).

### 4.1 날짜와 달력

| ID | 대상 | 내용 | 원형 |
|---|---|---|---|
| `coverage` | 모두 | B의 첫날~끝날 안에 있는 A의 날짜를 B가 얼마나 덮는지. 그 구간 밖 A의 날짜 수(`n_a_outside_b_span`)는 따로 세고 따로 상한을 둡니다. 금리는 A에 값이 있는 날만 셉니다 | `:276-296` |
| `calendar` | SPY, BTC | 겹치는 구간 안에서 A에만 있는 날(`only_a`)과 B에만 있는 날(`only_b`). SPY는 주말 날짜도 셉니다 | `:299-315` |

- 시계열 요약에는 어떤 독립·교차 짝의 구간에도 들지 않는 A의 날짜 수(`n_a_outside_evidence_spans`)를 적습니다(원형 `compare`, `:588-593`). 이 날들은 A 자체의 무결성 검사만 받습니다.

- SPY의 서명된 NYSE 달력은 2025-01-01 ~ 2027-12-31만 덮습니다(`core/calendars/data/holidays_NYSE.yaml:5-7`). 그래서 2004~2024년은 공급사끼리만 견줍니다. 2025~2026년은 서명 달력과도 견주는 것을 정식 도구에 넣습니다.
- 공급사가 날짜를 한국 날짜로 붙이면 거의 모든 날이 어긋나고 주말 날짜가 생깁니다. `calendar`가 이를 FAIL로 잡습니다. KIS의 `xymd`가 현지 날짜인지는 UNVERIFIED입니다.

### 4.2 종가와 수익률(SPY, 같은 규약)

| ID | 내용 | 원형 |
|---|---|---|
| `returns_same_convention` | 공통 날짜에서 하루 단순수익률의 차이 d = r_A − r_B. 허용치를 넘는 날 수, 최대 절댓값, log(P_A/P_B)의 변동 폭 | `:330-347` |
| `integrity_a` | A의 빈값·0 이하 행 수, 분할 모양의 큰 하루 변동이 없는지 | `:318-327` |

- 수준(level)은 직접 견주지 않습니다. 수정주가는 받은 시점 뒤의 배당만큼 전체가 상수배로 달라지기 때문입니다. 그래서 수준 비율은 값이 아니라 **변동 폭**만 봅니다.

### 4.3 배당과 분할 조정(SPY, 교차 규약)

| ID | 내용 | 원형 |
|---|---|---|
| `adjustment_convention` | A(총수익)와 B(분할만)의 수익률 격차 g. 해마다 양의 격차가 있는 날이 4일인지, 음의 격차와 너무 큰 격차가 없는지, 해마다 격차 합이 배당수익률 범위에 드는지 | `:350-386` |

- SPY는 분기 배당이고 분할한 적이 없다고 가정합니다(둘 다 UNVERIFIED, 13절).
- 격차 합의 값은 내보내지 않습니다. 6.3절에서 이유를 적습니다.

### 4.4 BTC 하루 경계와 시간대

| ID | 내용 | 원형 |
|---|---|---|
| `day_boundary` | B의 라벨을 k = −1, 0, +1일 밀 때마다, 하루 로그수익률의 차이 abs(r_A(t) − r_B(t+k))가 `ret_diff_big`(0.02)를 넘는 날 수를 셉니다. k = 0의 날 수가 다른 둘보다 엄격히 적어야 PASS입니다 | `:410-433` |
| `levels_and_returns` | abs(log(P_A/P_B))의 중앙값, 99분위, 최댓값. 2017-01-01 전후로 나눕니다. 큰 수익률 차이가 있는 날 수 | `:436-467` |

- `day_boundary`는 상관계수를 쓰지 않습니다. 상관은 두 시계열 각각의 표준편차, 곧 한 공급사 시계열의 변동성을 계산해야 나옵니다. 3.9 예외(부록 A)는 한 시계열의 변동성을 계산하지 않는다고 적으므로, 상관은 예외 밖입니다. 차이의 개수만으로도 밀린 라벨을 잡습니다. 라벨이 맞으면 차이는 거래소 간 잡음뿐입니다. 하루 밀리면 차이가 서로 다른 두 날의 수익률 차이가 되어 대부분의 날이 2%를 넘습니다(합성 시험 `btc_labels_shifted_by_one_day_fail_the_boundary_check`).
- 러너는 BTC 날짜 D를 UTC D+1 00:00에 닫히는 하루로 읽습니다(러너 `:629-634`). Binance도 시작 시각의 UTC 날짜를 라벨로 씁니다(`crypto_client.py:221`). Upbit 일봉도 UTC 날짜 라벨입니다(`crypto_client.py:138`, `:151`). Yahoo와 Coinbase의 라벨 규칙은 UNVERIFIED이고, `day_boundary`가 이를 자료로 확인합니다.

### 4.5 빠진 날

| ID | 내용 | 원형 |
|---|---|---|
| `integrity_a`(BTC) | A의 첫날부터 끝날까지 UTC 날짜 가운데 빠진 날 수와 그 날짜 | `:389-401` |

- 러너는 날짜가 엄격히 늘기만 하면 받습니다(러너 `:669-670`). BTC에서 하루가 빠지면 이틀 수익률이 한 행에 합쳐집니다. 그래서 따로 셉니다.

### 4.6 무위험 금리 단위와 공백

| ID | 내용 | 원형 |
|---|---|---|
| `units` | A의 모든 값이 −1~20 퍼센트 범위에 있고, 구간 최댓값이 1 이상인지. 범위는 레지스트리의 미국 국채 범위입니다(`data/macro/series_registry.yaml:69`) | `:470-495` |
| `values` | 둘 다 값이 있는 날에 abs(A − B)가 0.005 퍼센트포인트 이상인 날 수 | 같음 |
| `blanks` | A는 비었는데 B는 값이 있는 날, A는 값이 있는데 B에 행이 없는 평일 | 같음 |
| `seed` | 시작일 이전에 A의 관측값이 있는지. 러너의 `ffill`에 필요합니다(러너 `:688-693`) | `run`, `:654-660` |

- FRED 캐시는 채권시장 휴일에 빈칸이 있습니다(`core/calendars/data/source_skipped.yaml:128`; `holidays_SIFMA.yaml:103`). 서명된 SIFMA 달력도 2025~2027년만 덮습니다(`holidays_SIFMA.yaml:5-7`).
- 0.00%가 실제로 나오는 시기가 있으므로, 금리는 0 이하를 버리지 않습니다(원형 `_to_series`, `:184-194`).

## 5. 사전 등록 허용치와 판정

### 5.1 허용치(제안)

허용치는 원형의 `THRESHOLDS`(`parity_check.py:86-124`)와 같고, `summary.json`에 그대로 찍힙니다. 실제 자료로 보정하지 않았습니다. 실제 자료를 보지 않는 것이 이 설계의 조건이기 때문입니다. 그래서 거짓 FAIL의 비율은 모릅니다(UNVERIFIED).

**SPY**

| 항목 | 값 | 이유 |
|---|---|---|
| `coverage_min` | 0.99 | 미국 주식 세션은 공급사마다 같아야 합니다. B의 구간 안 A 세션 기준 |
| `edge_uncovered_max` | 5 | B의 구간 밖 A 세션 수의 상한. SPY 구간 전체를 대조해야 하므로 작게 둡니다. FMP 이력이 2004-12-01까지 닿지 않으면 그 짝은 WITHHELD입니다 |
| `ret_diff_tol` / `ret_diff_max` | 2e-4 / 2e-3 | 2자리 종가의 반올림은 100달러에서 하루 수익률을 최대 약 1e-4 움직입니다. 종가 체결가 출처(주 시장 종가 경매와 통합 시세)가 다르면 1센트가 더 어긋날 수 있어 두 배를 둡니다. 2e-3을 넘는 하루 차이는 자료 오류로 봅니다 |
| `ret_diff_share_max`, `ret_diff_floor_days` | 0.5%, 5일 | 허용치를 넘는 날은 max(5, 0.5% × 세션 수)까지 둡니다 |
| `drift_range_max` | 5e-3 | 총수익 조정 방식의 차이(배당을 전일 종가로 나누는 방식과 당일 재투자 방식)는 이차 항이라 22년에 1e-3 안팎으로 추정합니다. 가격 수익만 담긴 파일이면 연 1~2%씩 벌어져 이 기준을 크게 넘습니다 |
| `jump_abs_max` | 0.25 | SPY의 하루 변동은 이보다 작습니다(UNVERIFIED). 넘으면 분할 모양의 오류로 봅니다 |
| `ex_gap_min` / `ex_gap_max` | 5e-4 / 2e-2 | 분기 배당은 가격의 약 0.3~0.6%입니다(UNVERIFIED) |
| `ex_days_per_year` | 4 | 해마다 4일이면 PASS, 3일이나 5일이면 WARN, 그 밖은 FAIL. 1월 7일 이전과 12월 24일 이후에 비교일이 있는 해만 셉니다 |
| `yield_band` | [0.005, 0.04] | 해마다 격차 합이 이 범위에 드는지 불리언 하나로만 보고합니다 |

**BTC-USD**

| 항목 | 값 | 이유 |
|---|---|---|
| `coverage_min` | 0.95 | B의 구간 안 A 날짜 기준. 거래소 장애일을 허용합니다 |
| `edge_uncovered_max` | 471 | B의 구간 밖 A 날짜 수의 상한. 471은 2014-09-17~2015-12-31의 날 수이므로, B가 2016-01-01까지 시작하면 됩니다. Coinbase의 시작일이 미확인(UNVERIFIED)이라, 시작일 때문에 결과를 보기 전부터 WITHHELD가 되는 일을 막습니다. 덮지 못한 날 수는 요약에 따로 남습니다(4.1). 다른 길은 D-5에 있습니다 |
| `day_boundary`의 허용치 | `ret_diff_big`(0.02)을 함께 씀 | 라벨이 맞으면 하루 차이는 거래소 간 잡음(0.3~1%)이라 2%를 넘는 날이 드뭅니다. 하루 밀리면 차이의 표준편차가 약 √2 × 4% ≈ 5.7%라 대부분의 날이 2%를 넘습니다. 잡음과 변동성 수치는 가정입니다(UNVERIFIED) |
| `late_from` | 2017-01-01 | 그 전에는 USD 거래소가 적고 거래소 간 차이가 컸습니다. 앞 구간은 WARN만 냅니다 |
| 뒤 구간 `level_p50_max`, `level_p99_max`, `level_max` | 0.003, 0.015, 0.05 | Yahoo는 여러 거래소를 모은 가격으로 보입니다(UNVERIFIED). 한 거래소와 견주므로 어느 정도 차이를 허용합니다 |
| 앞 구간 `early_level_p99_max`, `early_level_max` | 0.03, 0.10 | WARN만 |
| `missing_days_warn_max` | 5 | A에서 빠진 날이 0이면 PASS, 1~5면 WARN, 그보다 많으면 FAIL |
| `jump_log_abs_max` | 0.7 | 하루 로그수익률이 이보다 크면 비정상으로 봅니다 |
| `ret_diff_big`, `ret_diff_share_max` | 0.02, 0.5% | 로그수익률 차이가 2%를 넘는 날이 0.5%보다 많으면 FAIL |

**DGS3MO**

| 항목 | 값 | 이유 |
|---|---|---|
| `coverage_min` | 0.99 | A에 값이 있는 날 기준 |
| `value_tol_pct` | 0.005 | 두 공급사 모두 소수 2자리 퍼센트이므로 값이 같아야 합니다 |
| `range_pct`, `unit_max_at_least_pct` | [−1, 20], 1.0 | 비율(0.05)이나 bp(500)로 들어온 파일을 잡습니다. 구간 최댓값이 1% 미만이면 퍼센트가 아니라고 봅니다 |
| `seed_lookback_days` | 31 | 시작일 31일 전부터 읽어 첫 `ffill` 값을 확인합니다 |
| `edge_uncovered_max` | 5 | B의 구간 밖, A에 값이 있는 날 수의 상한 |

- **바꾸는 규칙.** 소유자가 승인한 날 이후 어떤 `summary.json`이라도 생긴 뒤에 허용치를 바꾸면, 그 사실과 바꾸기 전 결과를 함께 기록합니다. 파일럿의 격자를 결과를 본 뒤 바꾸는 것을 새 시행으로 다루는 것과 같은 원칙입니다(스펙 `:1664`). 공급사 지도와 재실행에도 같은 규칙을 둡니다(5.5).

### 5.2 판정의 뜻

| 판정 | 검사 하나 | 공급사 짝 하나 | 시계열 |
|---|---|---|---|
| PASS | 허용치 안 | hard 검사가 모두 PASS이고 WARN 없음 | FAIL이 없고, 독립 또는 교차 짝 하나 이상이 끝까지 평가됨. 그 짝들의 구간 밖 A 날짜 수(`n_a_outside_evidence_spans`)를 함께 적음 |
| WARN | WARN 기준에 걸림: vintage·diagnostic 짝의 FAIL, BTC 앞 구간 수준 차이, 한 해 배당일 3일이나 5일, BTC에서 빠진 날 1~5일, BTC 날짜 불일치, 금리 공백 불일치 | WARN이 하나라도 있음 | (시계열 판정에는 없음. WARN은 목록으로만) |
| FAIL | hard 허용치를 넘음 | hard 검사 하나라도 FAIL | A의 무결성 검사나 독립·교차 짝 하나라도 FAIL |
| WITHHELD | 계산할 수 없음 | B의 구간 안 덮는 비율이 기준 미만, B의 구간 밖 A 날짜가 상한 초과, 또는 hard 검사가 계산 불가 | FAIL이 없고, 끝까지 평가된 독립·교차 짝이 없음 |

- vintage와 diagnostic 짝의 FAIL은 WARN으로 낮춥니다(원형 `_demote`, `:264-270`). 이 짝들만으로는 시계열이 PASS가 되지 않습니다. 어느 공급사가 어느 역할인지는 도구에 고정돼 있어, 역할을 바꿔 FAIL을 WARN으로 낮출 수 없습니다(5.5).
- 집계 규칙은 원형 `compare`(`:545-595`)에 있습니다. 종료 코드는 PASS 0, FAIL 1, WITHHELD 3, 거부 2, 오류 4입니다. 판정은 종료 코드만이 아니라 콘솔 마지막 줄 `PARITY ...`로 읽습니다(6.4).

### 5.3 파일럿 관문(제안)

- ⑥-1(Step 8, 파일럿 1)은 SPY와 DGS3MO가 모두 PASS일 때 시작합니다. 둘 중 하나라도 PASS가 아니면, 소유자가 그 시계열에 대해 판정 문장을 쓴 뒤에 시작합니다.
- ⑥-2(Step 9, 파일럿 2)는 BTC-USD에 같은 규칙을 둡니다. 파일럿 1 패리티 통과라는 기존 조건(스펙 `:1616`; 러너 `:436-438`)은 그대로입니다.
- 이 관문은 절차 규칙입니다. 러너가 강제하게 하려면 `tools/nautilus/`를 고쳐야 하고, 그러면 `code_sha256`이 바뀝니다(8.1). 그래서 강제 코드는 넣지 않습니다.

### 5.4 PASS가 아닐 때 소유자의 선택지

| 선택지 | 뜻 | 비용 |
|---|---|---|
| 주석을 달고 진행 | 표와 파일을 그대로 두고, 불일치를 실행 기록과 스펙 10.4에 적습니다 | 카드의 데이터 출처 문구는 바뀌지 않습니다. 표를 바꾸면 `owner_confirmed`가 무효가 되기 때문입니다 |
| 파일럿 보류 | 원인을 찾을 때까지 Step 8이나 9를 미룹니다 | 일정 |
| 자료 교체 | 새 `prices_file`(또는 `rf_file`)과 md5로 새 표를 만듭니다 | 아래 (1)~(6). 권고 순서 A에서는 대조가 7A.5 뒤이므로, 교체는 Step 7A 전체를 다시 하는 일입니다 |

자료 교체의 비용을 나눠 적습니다.

| # | 비용 | 근거 |
|---|---|---|
| (1) | 러너는 고정 가격 파일의 md5(`PINNED_REAL_MD5`)와 DGS3MO 경로(`DGS3MO_FILE`)를 코드에 갖고 있습니다. R-10은 리허설에서 고정 실파일의 바이트 복사본을 md5로 거부하고, 리허설이 쓸 수 있는 실제 금리 파일을 이 경로 하나로 묶습니다. 가격 파일을 바꾸고 이 규칙을 지키려면 md5 상수를, 금리 파일을 새 경로로 바꾸려면 경로 상수를 고쳐야 합니다. 어느 쪽이든 `code_sha256`이 바뀌어 두 표 모두 새 `owner_confirmed`가 필요합니다(S-1, S-2). 러너를 고치지 않으면 새 실파일의 복사본은 R-10에 걸리지 않습니다 | 러너 `:58`, `:67`, `:323`, `:653-655`; `code_paths` `:183-190` |
| (2) | 새 가격 파일은 `docs/asset_expansion/` 아래에 들어갑니다. 스펙 5.8은 이 폴더를 "Unchanged on purpose"로 적습니다. 같은 경로에 덮어쓰면 동결 연구가 읽는 캐시가 바뀝니다 | 스펙 `:1081-1083` |
| (3) | 두 표는 S-3의 증거 파일이라 7A.2~7A.3 사이에 바뀔 수 있습니다. 러너와 캐시 파일은 증거 파일이 아닙니다. 표, 러너, 캐시 모두 Step 10 허용 경로(S-6)에는 없습니다 | 스펙 `:1589-1590`, `:1617` |
| (4) | 표의 `table_sha256`이 바뀌어 새 `owner_confirmed`가 필요합니다. E1의 `config_id`는 파일을 키에 넣지 않으므로 같은 12행이 다시 쓰입니다 | 스펙 `:1185-1193`, `:1151-1156` |
| (5) | 파일럿 2의 `claim_label`은 "stored card S_C3_crypto_trend_btcusd on the same file"이라고 적습니다. 파일을 바꾸면 이 문장이 거짓이 됩니다. 그 문구는 스펙 10.2가 정하므로 스펙도 고쳐야 합니다. 저장 카드가 옛 파일로 계산됐으므로 G-08 "reference drift"로 WITHHELD가 될 수도 있습니다 | `pilot2_C3_btcusd.json:33`; 스펙 `:1181`, `:1648`, `:927`, `:1649` |
| (6) | 7A.2~7A.5를 다시 합니다. 러너 변경은 Windows 기술 검사를 다시 거쳐야 하고(S-4), 7A.4 검토와 7A.5 pull도 다시 합니다 | 스펙 `:1564-1575`(2단계 명령), `:1586-1598`(4~5단계) |

- 7A.2 전에 대조하는 A'(8.2)를 고르면, 교체가 필요할 때 Windows 증거를 만들기 전에 흡수할 수 있습니다. (2)와 (5)는 그대로입니다. (1)과 (4)의 러너·표 변경은 7A.2 전에 들어가므로 처음 쓰는 `owner_confirmed`에 담기고, (6)의 재진입은 없어집니다. 다만 러너 변경은 7A.1 서명 뒤의 "끼어든 변경"이므로, 7A.4가 확인할 소유자의 승인 범위 문장이 따로 필요합니다(스펙 `:1586-1590`). 이 선택은 D-1에서 소유자가 정합니다.

### 5.5 공급사 고정과 재실행 규칙(제안)

허용치만 미리 정하면 빈틈이 남습니다. 역할을 바꿔 FAIL을 WARN으로 낮추거나, PASS가 나올 때까지 다시 받아 다시 돌릴 수 있기 때문입니다. 그래서 아래를 함께 사전 등록합니다.

| 규칙 | 내용 | 원형 |
|---|---|---|
| 공급사 지도 고정 | 공급사별 역할과 규약은 3절 표 그대로 도구의 상수입니다. 명령줄은 `--pair <공급사> <파일>`만 받습니다. 시계열에 없는 공급사, 두 번 적은 공급사는 거부합니다. 지도는 `summary.json`의 `providers`에 그대로 찍힙니다 | `PROVIDERS`, `:57-64`; `_accounted_pairs`, `:606-623`; `run`, `:668-669` |
| 모든 필수 공급사 시도 | 필수 공급사는 대조하거나 `--unavailable <공급사> <이유>`로 적어야 합니다. 이유는 `no_key`, `plan_or_access`, `fetch_failed`, `short_history` 가운데 하나입니다. 빠뜨리면 거부합니다. 못 받은 공급사는 `withheld_reasons`에 "`<공급사>` not compared: `<이유>`"로 남습니다 | `UNAVAILABLE_REASONS`, `:65`; `compare`, `:580` |
| 모든 요약 커밋 | 종료 코드 0, 1, 3으로 끝난 실행의 `summary.json`은 판정과 관계없이 모두 별도 브랜치에 커밋합니다 | 절차(8.4 5단계) |
| 기록 실행 | 시계열마다 첫 완전 실행(종료 0, 1, 3)이 기록 실행입니다. 거부(2)와 오류(4)는 아무것도 쓰지 않으므로 실행으로 세지 않습니다. 원인을 고쳐 다시 돌립니다 | 절차 |
| 나중 실행 | 새로 받은 자료든 같은 자료든, 기록 실행 뒤의 실행은 소유자가 이유를 적은 판정 문장을 앞 결과 옆(`results/RULINGS.md`)에 남긴 뒤에만 셉니다. 앞 결과는 지우지 않습니다 | 스펙 R-17(`:1266`, `:838`)과 5.1의 바꾸는 규칙과 같은 원칙 |

- 공급사 지도를 바꾸는 것도 허용치를 바꾸는 것과 같이 다룹니다. 어떤 요약이라도 생긴 뒤에 바꾸면, 그 사실과 바꾸기 전 결과를 함께 기록합니다.

## 6. Claude가 실제 가격을 보지 않는 방법

### 6.1 누가 어디서 무엇을 하나

| 단계 | 누가 | 어디서 | 실제 자료 |
|---|---|---|---|
| 도구 작성과 시험 | Claude | 보호 캐시가 없는 sparse 클론, 합성 자료 | 없음 |
| 공급사 수신(fetch) | 소유자 | 소유자 PC, 전역 인터프리터. 방화벽 규칙은 전용 인터프리터에만 걸리므로 수신에 영향이 없습니다(스펙 `:330-331`) | 소유자 PC에만 |
| 대조(compare) | 소유자 | 소유자 PC. 출력 폴더는 git 작업 트리 밖이어야 합니다 | 소유자 PC에만 |
| 요약 검토 | Claude | 소유자가 push한 `summary.json` | 없음 |

- 이 규칙의 근거는 Step 2의 전역 제약 "Claude reads no real BTC price and no SPY row on or after 2004-12-01"과 보호 캐시를 열거나 해시하지 않는다는 문장입니다(스펙 `:1502`).
- 과거에 테스트 프로세스와 `grep`이 보호 캐시를 연 일이 있습니다(`docs/nautilus_bridge/OWNER_RULINGS_LOG.md:383-405`, `:496-506`). 그래서 도구에 경로 장치를 둡니다(6.4).

### 6.2 Claude에게 돌아오는 출력: 허용 목록

| 필드 | 형태 | Claude에게 | 이유 |
|---|---|---|---|
| `schema`, `run_id`, `created_utc`, `tool.sha256`, `pinned.md5`, `md5_ok`, `file_sha256` | 식별자, 해시 | 허용 | 값 정보가 없습니다 |
| `window.start`, `window.end`, `thresholds`, `providers` | 날짜, 상수, 공급사 지도(역할·규약·필수 여부) | 허용 | 미리 정한 값입니다 |
| `n_rows`, `n_a`, `n_b`, `n_common`, `n_a_outside_b_span`, `n_a_outside_evidence_spans`, `first_date`, `last_date` | 정수, 날짜 | 허용 | 세션 수와 범위는 달력 사실입니다. 스펙도 행 수만으로 OOS 세션 수를 적습니다(스펙 `:1637-1638`) |
| `only_a`, `only_b`, `missing_a`, `blank_a_value_b`, `value_a_absent_b`(각 100개까지) | 날짜 목록 | 허용 | 거래일과 휴일은 공개 사실입니다 |
| `n_over_tol`, `n_negative_gap_days`, `n_big_return_diff_days`, `n_off_by_tol` 등 | 정수 | 허용 | 자료 품질의 개수입니다 |
| `*_bucket` | `<=1e-04` 같은 10단위 구간 | 허용 | 정확한 크기 대신 씁니다 |
| `max_ok`, `drift_ok`, `within_band`, `yield_band_ok`, `lag0_strictly_fewest`, `no_split_shaped_jump`, `no_implausible_jump`, `percent_units_ok`, `seed_before_start` | 불리언 | 허용 | 각 1비트입니다 |
| `lag` | −1, 0, 1 | 허용 | 라벨 규칙입니다 |
| 검사·짝·시계열 판정, `withheld_reasons`(못 받은 공급사와 이유 포함) | 열거값, 문장 | 허용 | |
| 가격, 수익률, 금리 값, 날짜별 차이, 정확한 최대 차이와 그 날짜, `day_boundary`의 이동별 초과 일수, 해마다 배당 격차 합, 수준 비율의 값 | — | **금지.** `detail.json`에만 | 6.3 |

- 감사는 "exact dates and magnitude"를 요구합니다(감사 `:179`). 이 요구는 `detail.json`이 채웁니다. 소유자는 정확한 날짜와 크기를 봅니다. Claude는 개수와 구간만 봅니다.

### 6.3 허용한 출력도 새는가

- **수준 비율의 값: 샙니다.** 두 수정주가의 상수배 차이는 두 수신 시점 사이의 배당을 그때 가격으로 나눈 값입니다. 공개된 배당액과 합치면 가격 수준이 나옵니다. 그래서 변동 폭의 구간만 냅니다.
- **해마다 배당 격차 합: 샙니다.** 그 해의 배당수익률에 가깝습니다. 공개된 배당액과 합치면 그 해의 가격 수준이 나옵니다. 그래서 범위 안에 드는지 불리언 하나만 냅니다(원형 `:351-353` docstring).
- **정확한 최대 차이와 그 날짜: 조금 샙니다.** BTC에서 거래소 간 차이는 급락 때 커집니다. "어느 날 큰 괴리"는 시장 사건을 가리킵니다. 그래서 크기는 구간으로, 날짜는 내지 않습니다. 큰 차이가 있는 날 수도 해마다가 아니라 전체 합만 냅니다.
- **이동별 초과 일수: 조금 샙니다.** ±1일 이동에서 차이가 2%를 넘는 날의 비율은 BTC 하루 변동성에 따라 움직입니다. 그래서 `lag`와 "0일 이동이 엄격히 가장 적은지" 불리언 하나만 냅니다. 원형은 상관계수를 계산하지 않습니다(4.4).
- **개수, 달력 날짜, 구간: 사실상 새지 않습니다.** 자료 품질에 대한 정보이고 가격 경로에 대한 정보가 아닙니다.
  - 예외 하나: BTC의 `only_a`, `only_b` 날짜는 거래소 장애일과 겹칠 수 있고, 장애는 급변일에 잦습니다. 사건 하나에 1비트 수준입니다. 더 좁히려면 BTC는 날짜 없이 개수만 냅니다(D-7).
- **불리언(점프 없음 등): 1비트씩 샙니다.** "SPY 하루 변동이 25%를 넘은 적 없다" 같은 공개 사실 수준입니다. 전체 20비트 안팎입니다. 받아들일지는 D-7에서 소유자가 정합니다.
- **남는 한계.** Claude 모델은 학습 자료로 SPY와 BTC의 역사를 대략 압니다. 이 보호는 파일을 읽지 않는다는 절차적 보호입니다. 두 파일럿 표의 claim_label이 이미 "pre-specified on historical data … not confirmatory"라고 적는 것과 같은 수준입니다(`pilot1_E1_spy.json:40`, `pilot2_C3_btcusd.json:33`).
- **파일럿 뒤.** 파일럿 1·2의 기록이 커밋되면 등록된 시험에 영향을 줄 길이 없어집니다. 그 뒤 `detail.json`을 커밋할지는 Step 10 이후 소유자가 정합니다(D-7).

### 6.4 기계적 장치(원형에 있음)

| 장치 | 내용 | 원형 |
|---|---|---|
| 경로 장치 | `asset_expansion/cache` 아래 경로는 `--owner-run` 없이는 열거나 해시하기 전에 거부합니다. Claude는 이 플래그를 쓰지 않습니다 | `guard_path`, `:159-164` |
| 출력 위치 | 출력 폴더가 이미 있거나 git 작업 트리 안이면 거부합니다. 연구 클론의 `git status`를 더럽히지 않습니다 | `inside_git_worktree`, `:167-169`; `run`, `:641-642` |
| 구간 밖 줄 | 날짜 글자로 먼저 거르고, 구간 밖 줄의 값은 파싱하지 않습니다(러너와 같은 방식) | `_window_frame`, `:172-181`; 러너 `:658-661` |
| 공급사 지도 | 역할과 규약은 상수에서만 옵니다. 필수 공급사를 빠뜨리거나 다른 공급사를 넣으면 거부합니다(5.5) | `PROVIDERS`, `:57-64`; `_accounted_pairs`, `:606-623` |
| 계산 목록 | 검사마다 무엇을 계산하는지 상수로 적고, 자체 시험이 실제 검사 ID와 이 목록이 같은지, 코드에 상관·평균·표준편차·분산 호출이 없는지 확인합니다(부록 A와 짝) | `COMPUTES`, `:68-80`; 시험 `every_check_is_named_in_COMPUTES_and_no_other_statistic_is_used` |
| 요약 검증 | 실수는 `thresholds` 밖에서 금지, 정수는 `n_*`와 `lag`만, 날짜는 날짜 키에만, 문자열 속 소수는 금지. 어기면 파일을 쓰기 전에 멈춥니다 | `assert_summary_safe`, `:505-532` |
| 거부 문구 | 읽기 오류는 예외의 종류만 출력합니다. 예외 문장이 파일의 칸을 인용할 수 있기 때문입니다 | `read_pinned`, `:208-210` |
| 오류 | 그 밖의 예외도 종류만 출력하고 종료 코드 4로 끝냅니다. FAIL(1)과 섞이지 않습니다. 두 파일은 폴더를 만들기 전에 문자열로 만들어 두므로, 요약 검증이나 직렬화에서 난 오류는 아무것도 남기지 않습니다 | `run`, `:672-680`, `:685-688` |
| 콘솔 | 마지막 줄은 `PARITY <series> <판정> exit=<n> summary=<경로>`뿐입니다. 판정은 `PASS`, `FAIL`, `WITHHELD`, `REFUSED`, `ERROR` 가운데 하나입니다 | `run`, `:681-691` |

- **소유자 쪽 규칙(제안).** `detail.json`, 그 내용, 화면 캡처를 채팅이나 커밋에 넣지 않습니다. 콘솔은 마지막 줄만 전합니다. 결과는 종료 코드가 아니라 그 마지막 줄로 판단합니다. 마지막 줄이 `PARITY`로 시작하지 않으면(파이썬 자체의 오류 등) 결과가 없는 것으로 봅니다.

## 7. 결과 기록

| 무엇 | 어디 | 언제 | 근거 |
|---|---|---|---|
| 원자료, 정규화 CSV, 메타데이터, `summary.json`, `detail.json` | 소유자 PC `%LOCALAPPDATA%\quantgen\provider_parity\PP-<UTC>-<series>\` | 실행 때 | OneDrive와 클론 밖. 스펙의 venv 위치 원칙과 같습니다(스펙 `:140`) |
| 모든 `summary.json`(시계열마다 최소 하나) | 별도 브랜치(권고 이름 `claude/provider-parity-5-2`)의 `results/PP-<UTC>-<series>/summary.json` | Step 8 전에 소유자가 커밋·push(경로를 하나씩 `git add`) | 파일럿 전에 실행했다는 시각 증거. 첫 완전 실행이 기록 실행입니다(5.5). Claude가 읽는 곳 |
| 요약 사본 | 연구 브랜치 `docs/nautilus_bridge/runs/PP-<UTC>-<series>/provider_parity_summary.json` | Step 10 | Step 10 허용 경로입니다(스펙 `:1617`) |
| 데이터 접근 이력 | 스펙 10.4의 새 행(부록 B) | Step 10 | 10.4는 실행 기록에 그대로 옮겨집니다(스펙 `:1677`) |
| 실행 기록 절 "⑤-2 provider parity" | `docs/superpowers/plans/2026-10-28-nautilus-execution-record.md` | Step 10 | 요약의 sha256, 도구 sha256, 판정, 소유자 판정 문장 |
| PASS가 아닐 때 소유자 판정 문장 | Step 10 전에는 별도 브랜치의 `results/RULINGS.md`, Step 10에 실행 기록과 스펙 Status로 옮김 | 판정 때 | `OWNER_RULINGS_LOG.md`는 Step 10 허용 경로에 없습니다(스펙 `:1617`) |

- 수신이 클론과 `--out` 밖에 쓰는 곳은 `kis`의 접근 토큰 `~/.nextgen/kis_token.json` 하나입니다(9.2). 장부(`~/.nextgen/macro/ledgers`)는 건드리지 않습니다.
- 요약 사본의 파일 이름은 `run.json`이 아닙니다. 러너는 `runs/*/run.json`과 `NB-*-<8hex>/run.json`만 읽습니다(러너 `:246`, `:416`). 그래서 파일럿 기록으로 오인되지 않습니다.
- 파일 형식: `summary.json`은 `provider-parity-summary/1`, `detail.json`은 `provider-parity-detail/1`입니다(원형 `:50-51`). 원형이 만든 예시는 11절에 있습니다.

## 8. Step 7A와의 순서

### 8.1 묶는 규칙

| # | 규칙 | 근거 |
|---|---|---|
| S-1 | `code_sha256`은 `tools/nautilus/**/*.py`, `tools/nautilus/golden/*.json`, `requirements-nautilus.txt`, 하네스 소스, `docs/asset_expansion_study.py`, `config.py`의 해시입니다. 스펙과 그 밖의 문서는 들어가지 않습니다 | 스펙 `:1186-1191`; 러너 `:183-190`; `core/quant/gate_package.py:36-38` |
| S-2 | of-record 실행은 `owner_confirmed`가 지금 트리의 `code_sha256` 앞 16자를 인용해야 합니다. 다르면 R-11로 거부합니다 | 러너 `:427-434`; 스펙 `:1183`, `:1192-1193` |
| S-3 | 7A.2 검증 기준 커밋부터 7A.3 커밋까지는 증거 파일(census, egress, 인계 보고서, 두 표, `qa/acceptance_results.json`)만 바뀔 수 있습니다 | 스펙 `:1586-1590`; `RUNBOOK_windows.md:190-196` |
| S-4 | 7A.4 Claude 검토 커밋은 스펙만 바꿉니다. 다른 변경이 필요하면 영향받는 기술·Windows 검사를 다시 거칩니다 | 스펙 `:1593-1596`; `RUNBOOK_windows.md:197-201` |
| S-5 | 7A.5에서 소유자가 pull한 HEAD에 파일럿이 묶이고, 실행 기록이 그 HEAD를 저장합니다 | 스펙 `:1597-1598`; `RUNBOOK_windows.md:203-208` |
| S-6 | Step 10: 7A.5 HEAD 대비 `git diff --name-only`에 `docs/nautilus_bridge/runs/` 아래, 실행 기록, `README.md`, `qa/acceptance_results.json`, 스펙만 나와야 합니다 | 스펙 `:1617` |
| S-7 | of-record 실행 때 작업 트리는 `docs/nautilus_bridge/runs/` 아래 미추적 파일을 빼고 깨끗해야 합니다(R-01) | 러너 `:475-495`(`:494`); 스펙 `:766` |
| S-8 | 파일럿 구간은 등록 전에 계산하지 않습니다. 러너도 등록 전에는 md5, 날짜, 반올림, P0a만 합니다 | 스펙 `:234-236`, `:1635` |
| S-9 | 파일럿, 스위트, 동결 연구 판독은 겹치지 않습니다 | 스펙 `:220-228` |
| S-10 | `nautilus` 스위트의 각 테스트는 `docs/nautilus_bridge/`를 전후로 다이제스트하고, 바뀌면 실패합니다 | 스펙 `:177-182` |
| S-11 | T-RO-01은 `core/`, `data/`, `ui/`, `main.py`, `config.py`, `docs/*.py`(최상위만), `tools/**`, `papers/**`를 스캔합니다. 다른 세 테스트는 `docs/**/*.py`를 재귀로 스캔합니다 | `tests/macro_m0_harness.py:110-117`; `tests/acceptance.py:50-56`; `tests/macro_m6_context.py:506`; `tests/macro_m7_ledger.py:328`; `tests/macro_tf_gov.py:290` |
| S-12 | `main`은 7A.3 커밋까지 병합 동결입니다 | 스펙 `:11-13` |
| S-13 | 판독은 별도 클론에서 할 수 있다는 선례가 있습니다 | 스펙 `:1602-1603`; `RUNBOOK_windows.md:221` |
| S-14 | 2027-01-01 이후 자료는 어떤 설계에도 쓰지 않습니다. 도구는 그날 이후 날짜의 관측을 요청하지도, 저장하지도, 비교하지도 않습니다(9.1) | `REMAINING_WORK_2026-10-27.md:122` |

- 등록 시점에 따른 S-8의 무게. E1은 O11 A2가 7A.2에서 12개 설정을 가격을 읽기 전에 등록할 수 있습니다(스펙 `:1567-1568`; `O11_A2_REGISTRATION.md`). 그렇게 되면 SPY 대조는 등록 뒤입니다. E1에 이미 행이 있어 A2가 건너뛰어지면, 12개 설정은 파일럿 1의 11단계에서 등록됩니다. C3는 늘 파일럿 2의 11단계에서 등록됩니다(스펙 `:775`). 그래서 BTC 대조는 늘 등록 전이고, SPY는 경우에 따라 등록 전입니다. A'(8.2)에서는 SPY도 늘 등록 전입니다. 어느 쪽이든 스펙 예외 문장이 필요합니다(부록 A).

### 8.2 선택지

| 선택지 | 내용 | `code_sha256`·`owner_confirmed` | 7A.2~7A.4 규칙(S-3, S-4) | Step 10(S-5, S-6) | 3.9(S-8) | 비용 |
|---|---|---|---|---|---|---|
| **A. 별도 브랜치·별도 클론 + 스펙만 바꾸는 커밋** | 도구는 `claude/provider-parity-5-2`에 둡니다(연구 브랜치에 Step 10 전까지 넣지 않음). 소유자는 7A.5 뒤 별도 클론에서 실행하고, 연구 클론의 고정 파일은 읽기만 합니다. 스펙 예외는 7A.5 pull 전에 스펙만 바꾸는 커밋으로 넣습니다 | 바뀌지 않음(S-1) | 지킴. 스펙만 바꾸는 커밋은 7A.3 뒤이고 S-4와 같은 모양입니다 | 지킴. 결과는 Step 10에 허용 경로로만 들어갑니다 | 스펙 예외로 해결 | 소유자 PC에 클론이 하나 더 필요합니다. 별도 클론에는 `.env`가 없으므로 키 처리 방법이 필요합니다(9.3). 스펙 문장을 소유자가 승인해야 합니다 |
| **A'. A와 같되 7A.2 전에 대조** | 도구와 별도 클론은 A와 같습니다. 스펙만 바꾸는 커밋을 7A.2 시작 전에 연구 브랜치에 넣고, 소유자는 7A.2를 시작하기 전에 별도 클론에서 대조합니다 | 바뀌지 않음(S-1) | 스펙 커밋은 7A.1 서명 커밋(`0bc9595`)과 7A.3 사이의 "끼어든 변경"이므로 7A.4가 승인 범위를 확인합니다. 소유자의 부록 A 승인 문장이 그 범위라는 해석은 UNVERIFIED입니다. 대조 자체는 연구 클론을 건드리지 않습니다. 7A.2 기준선과 7A.3 사이에 대조하는 것은 권하지 않습니다. 그 사이에는 스펙도 바꿀 수 없고(S-3), 교체가 생기면 7A.2를 다시 해야 합니다 | 지킴 | 스펙 예외로 해결 | 7A.2가 도구 작성, 독립 검증, 소유자 실행만큼 늦어집니다. 로드맵의 "⑤-1 선행"(`REMAINING_WORK_2026-10-27.md:132`)과 순서가 어긋나므로 소유자 결정이 필요합니다. 대신 자료 교체가 필요할 때 Windows 증거를 만들기 전에 흡수합니다(5.4) |
| **B. 7A.2 전(또는 7A.2 재진입 전)에 연구 브랜치에 착지** | 도구를 `tools/nautilus/` 밖(예: `tools/provider_parity/`)에 두고 지금 연구 브랜치에 커밋합니다. 7A.2 기준선에 들어갑니다 | 바뀌지 않음(S-1) | 7A.1 서명 커밋(`0bc9595`)과 7A.3 사이의 변경이므로 7A.4가 "승인 범위 안인지" 확인해야 합니다. ⑤-2 도구는 스펙 rev 6 범위 밖이므로 소유자 승인이 필요합니다. 7A.2 뒤에 도구를 고치면 재진입입니다 | 지킴 | 스펙 예외는 여전히 필요 | 7A.2가 도구 작성·검토만큼 늦어집니다. 새 테스트가 Windows 전체 실행과 README 집계에 들어갑니다. `tools/**`이므로 T-RO-01 스캔 대상입니다(S-11) |
| **C. 스펙 개정으로 Step 10 허용 경로를 넓히고 7A.5 뒤에 착지** | Step 10 목록에 `tools/provider_parity/**` 등을 더하고, 도구를 7A.5 뒤 연구 브랜치에 커밋합니다 | 바뀌지 않음 | 지킴 | S-6은 개정으로 지키지만, 파일럿 1 전에 커밋하면 파일럿이 7A.5 HEAD가 아닌 HEAD에 묶여 S-5와 어긋납니다. S-5도 고쳐야 합니다 | 스펙 예외 필요 | 거버넌스 규칙 두 개(S-5, S-6)를 바꿉니다. 도구 코드는 7A Windows 증거에 들어가지 않습니다 |
| D. `tools/nautilus/` 아래에 착지 | 러너 옆에 둡니다 | **바뀜.** `owner_confirmed` 무효, R-11(S-2) | 7A 재진입 | — | — | 권하지 않음. 7A.2~7A.3을 다시 해야 합니다 |
| E. ⑤-2를 Step 10 뒤로 미룸 | 파일럿을 먼저 돌립니다 | 영향 없음 | 영향 없음 | 영향 없음 | — | 권하지 않음. 로드맵의 "⑥-1 전 필수"(`REMAINING_WORK_2026-10-27.md:132`)와 어긋납니다 |

### 8.3 권고: A

- 새 서명 범위 없이 `code_sha256`, 7A의 증거, S-5·S-6 규칙을 모두 그대로 두는 길은 A뿐입니다. B와 C도 `code_sha256`은 바꾸지 않지만, B는 7A.4가 확인할 새 승인 범위가 필요하고 C는 S-5와 S-6을 고쳐야 합니다.
- 연구 브랜치에는 스펙만 바꾸는 커밋 하나만 더합니다. 이 커밋은 7A.5 HEAD에 들어가므로, 파일럿이 7A.5 HEAD에 묶인다는 S-5와 맞습니다.
- 결과는 Step 10에 `runs/`, 스펙, 실행 기록에만 들어가므로 S-6과 맞습니다.
- 별도 클론에서 돌리는 것은 판독의 선례와 같습니다(S-13).
- 대신 소유자 PC에 클론이 하나 더 생기고, 키 처리를 정해야 합니다(9.3, D-4).
- A의 약점은 자료 교체의 비용입니다. 대조가 7A.5 뒤이므로 교체가 필요하면 Step 7A 전체를 다시 합니다(5.4). 교체 가능성을 크게 보면 A'가 낫고, 7A.2를 미루지 않는 것을 크게 보면 A가 낫습니다. 이 저울질은 D-1에서 소유자가 합니다. Claude 권고는 A입니다. 로드맵의 순서와 맞고, PASS가 아닐 때도 "주석을 달고 진행"이나 "파일럿 보류"가 먼저 쓸 수 있는 선택지이기 때문입니다.

**스펙만 바꾸는 커밋을 언제 넣나.**
- 7A.4 검토 커밋 안에 넣을 수 있습니다. 그 커밋은 스펙만 바꾸기 때문입니다(S-4). 다만 검토와 무관한 내용을 섞게 됩니다.
- 검토 커밋 바로 뒤, 7A.5 pull 전에 따로 넣을 수도 있습니다. 소유자의 `git pull --ff-only`가 둘 다 가져오고, 7A.5 HEAD는 뒤 커밋이 됩니다.
- 어느 쪽이 7A.4·7A.5 문장의 뜻에 맞는지는 해석입니다(UNVERIFIED). D-3에서 소유자가 정합니다. 권고는 "검토 커밋 바로 뒤, 따로"입니다. 검토 기록과 새 규칙을 나눠 읽을 수 있기 때문입니다.

### 8.4 권고안의 진행 순서

| 단계 | 누가 | 할 일(명령) | 끝난 기준 |
|---|---|---|---|
| 0 | 소유자 | 이 초안을 읽고 12절 D-1~D-9를 정합니다 | 소유자 문장 |
| 1 | Claude | `main`의 동결 tip `bb35b3b`에서 `claude/provider-parity-5-2`를 만들고, 도구(수신 + 비교), 합성 시험, README를 씁니다. 도구는 `tools/provider_parity/`에 `__init__.py`와 함께 둡니다(나중에 `main`에 들어가도 `tools/nautilus/` 밖). `tools/__init__.py`는 `bb35b3b`에 이미 있습니다. 독립 검증을 거치고 커밋·push합니다 | 합성 시험 PASS. 보호 캐시를 열지 않음. 그 브랜치에서 T-RO-01 PASS(UNVERIFIED, 실행 전). 도구의 커밋 sha와 `parity_check.py`의 sha256이 정해짐 |
| 2 | 소유자 → Claude | 부록 A 문장을 승인합니다. Claude는 1단계의 커밋 sha와 sha256을 10.5에 적어, 7A.4 검토 커밋 뒤, 7A.5 pull 전에 스펙만 바꾸는 커밋으로 넣습니다. `code_sha256` 확인은 장부를 열지 않는 길로 합니다. 스크래치의 허용 인터프리터로, `HOME`과 `TMPDIR`은 새 스크래치 폴더(HOME이 TMPDIR 안이 아님), `QUANTGEN_MACRO_DIR`은 빈 임시 폴더로 두고, `.env`가 없는 클론 루트에서 `<mvenv>/bin/python -B -E -c "from pathlib import Path; from tools.nautilus.runner import code_sha256; print('code_sha256', code_sha256(Path('.')))"`를 돌립니다. `--fingerprint`는 `config`를 불러 `.env`를 찾고 가족 장부(`config.macro_dir()/ledgers`)를 열므로 이 단계에서 쓰지 않습니다(러너 `:1767-1770`; `config.py:25-29`, `:182-184`). 이 명령은 아직 돌려 보지 않았습니다(UNVERIFIED) | `git diff --name-only <7A.4 커밋> HEAD`가 스펙 하나. 출력의 `code_sha256` 앞 16자가 두 표의 `owner_confirmed`와 같음 |
| 3 | 소유자 | 7A.5 `git pull --ff-only` | `RUNBOOK_windows.md:203-208` |
| 4 | 소유자 | `%LOCALAPPDATA%\quantgen\pp_clone`에 별도 브랜치만 클론합니다. 주소는 연구 클론의 것을 씁니다: `$origin = git -C <연구 클론> remote get-url origin`, 이어서 `git clone --branch claude/provider-parity-5-2 --single-branch $origin "$env:LOCALAPPDATA\quantgen\pp_clone"`. 그 폴더(클론 루트)로 옮겨 `python -B -m tools.provider_parity.parity_check fetch`와 `compare`를 시계열마다 돌립니다(9절). 파일럿, 스위트, 판독과 겹치지 않게 합니다(S-9) | 시계열마다 `PARITY` 줄과 `summary.json`. 연구 클론에서 `git status --porcelain`이 빈 출력 |
| 5 | 소유자 | 4단계에서 생긴 `summary.json`을 모두(5.5) 별도 브랜치의 `results/` 아래로 복사해 경로를 하나씩 `git add`하고 커밋·push합니다. `detail.json`은 넣지 않습니다 | push됨. 시계열마다 기록 실행이 하나 |
| 6 | Claude | 요약을 읽고 판정과 권고를 적습니다. PASS가 아니면 5.4의 선택지를 정리합니다 | 소유자 판정 문장(PASS면 불필요) |
| 7 | 소유자 | Step 8 파일럿 1. BTC는 D-8대로 Step 9 전까지 | 스펙 `:1615` |
| 8 | Claude | Step 10에 요약 사본을 `runs/`에, 스펙 10.4 행과 실행 기록 절을 씁니다 | S-6 규칙 만족 |

- A'를 고르면 순서가 바뀝니다. 0, 1단계 뒤 2단계의 스펙 커밋을 7A.2 시작 전에 넣고, 4~6단계를 7A.2 전에 합니다. 그다음 Step 7A를 원래 순서대로 진행하고, 3단계(7A.5 pull)와 7, 8단계가 뒤따릅니다. 2단계의 끝난 기준은 `git diff --name-only 0bc9595 HEAD`가 스펙 하나인 것으로 바뀌고, 그때는 아직 `owner_confirmed`가 없으므로 `code_sha256`은 기록만 합니다.

### 8.5 이 초안과 원형 자체의 커밋 위치

- 이 초안과 원형도 연구 브랜치에 커밋하면 S-3의 대상입니다.
  - 7A.2 기준선 **뒤에** 커밋하면, 7A.3까지 증거 파일만 바뀐다는 규칙을 어깁니다.
  - 7A.2 **전에** 커밋하면, 7A.4가 확인할 "끼어든 변경"이 됩니다. 문서와 `docs/` 아래 원형이고 `code_sha256`에는 들어가지 않습니다(S-1). 그래도 `docs/**/*.py`를 스캔하는 세 테스트가 원형을 읽습니다(S-11). 원형은 세 테스트의 패턴을 재현한 검사에서 걸리지 않았습니다(11.2). 실제 스위트로는 확인하지 않았습니다(UNVERIFIED).
- **권고:** 연구 브랜치에 커밋하지 않고, 1단계의 별도 브랜치에 커밋합니다. 연구 브랜치에 두려면 7A.2를 시작하기 전에, 소유자가 "끼어든 변경"으로 승인한다는 문장과 함께 넣습니다(D-2).

## 9. 도구 인터페이스 초안

### 9.1 명령

```
python -B -m tools.provider_parity.parity_check fetch    --series {spy|btc|rf} --provider <이름> --start <날짜> --end <날짜> --out <작업 트리 밖 폴더> [--env-file <연구 클론>\.env]
python -B -m tools.provider_parity.parity_check compare  --table <연구 클론>\docs\nautilus_bridge\registration\<표>.json --repo <연구 클론> --series {spy|btc|rf} --pair <공급사> <정규화 CSV> [...] [--unavailable <공급사> <이유> ...] --out <새 폴더> --owner-run
python -B -m tools.provider_parity.parity_check selftest
```

- 세 명령 모두 pp_clone의 루트에서 모듈 형태(`-m`)로 돌립니다. `fetch`는 `core.quant.history`, `data.kis_markets`, `core.ficc.data`, `config`를 불러옵니다(9.2). 파일 경로로 돌리면 `sys.path[0]`이 도구 폴더가 되어 이 import가 실패합니다. 스펙도 러너를 `python -B -m tools.nautilus.runner`로 돌립니다(스펙 `:1566-1575`). `tools/__init__.py`는 있고(`bb35b3b`에도 있음), 정식 도구는 `tools/provider_parity/__init__.py`를 더합니다.
- `--pair`는 공급사 이름과 파일만 받습니다. 역할과 규약은 도구의 공급사 지도에서 옵니다(5.5). 원형은 이미 이렇게 동작합니다(원형 `run`, `:635-636`).
- 원형의 `compare`는 `--a`, `--a-md5`, `--start`, `--end`를 직접 받습니다(원형 `:631-634`). 정식 도구는 `--table`과 `--repo`에서 이 넷을 읽습니다. `prices_file`(SPY, BTC) 또는 `rf_file`(rf), 그 md5, `start`, `end`입니다. 표를 쓰지 않고 읽기만 합니다.
- `fetch`의 정규화 CSV는 `start − 31일`부터 `end + 7일`까지로 자릅니다.
- **2027-01-01 규칙(S-14).** 2027-01-01 이후 날짜의 관측은 요청하지도, 저장하지도, 비교하지도 않습니다.
  - 9.2의 기존 함수는 끝 날짜를 받지 않고, 부른 날까지의 자료를 돌려줍니다(`core/quant/history.py:130-134`는 `from`만 보냄; `data/kis_markets.py:466-471`과 `_page_back` `:180-205`는 오늘부터 뒤로 넘김; `core/ficc/data.py:203-208`은 `period`만 받음; `data/crypto/crypto_client.py:192-217`은 지금부터 뒤로 넘김). 그래서 대조가 2026-12-31을 넘겨 미뤄지면 이 함수들은 2027년 관측을 받아 옵니다.
  - 그래서 `fetch`는 UTC 날짜가 2027-01-01 이후이면 거부합니다. 예외는 요청에 2026-12-31 이전의 끝 날짜를 명시하는 수신 함수뿐입니다. 후보는 FMP `to`, fredgraph `coed`, Coinbase `end`, yfinance `end`, Treasury 연도별 파일의 2026년까지입니다. 이 인자 이름은 확인하지 않았습니다(UNVERIFIED). 기존 함수는 이 인자를 보내지 않으므로, 그날 이후에는 도구 안의 새 호출이 필요합니다.
  - 받은 응답에 2027-01-01 이후 날짜의 행이 하나라도 있으면, 무엇이든 쓰기 전에 거부합니다. 원자료 바이트를 잘라 저장하지 않습니다. 자른 바이트는 더 이상 원자료가 아니기 때문입니다.

### 9.2 공급사별 수신 경로

| `--provider` | 호출 | 비고 |
|---|---|---|
| `fmp` | `core.quant.history.fmp_history("SPY", days=N)` | 요청 시작일이 `today − (N × 1.6 + 10)`일이고(`core/quant/history.py:130`), 결과는 마지막 N행으로 잘립니다(`:182`). 2004-11-01부터 남기려면 N이 그 뒤 세션 수(약 5,500)보다 커야 합니다. 약 5,600을 제안합니다. `adjustment == "total"`이 아니면 거부(`:186`) |
| `kis` | `data.kis_markets.KISMarkets().overseas_daily("AMS", "SPY", days=N, adjusted=True)` | 분할만 조정(`data/kis_markets.py:459-473`). N은 구간의 세션 수보다 크게 둡니다. `load_history`를 거치지 않습니다. KIS 클라이언트는 접근 토큰을 `~/.nextgen/kis_token.json`에서 읽고, 새로 받으면 그 파일에 씁니다(`data/krx/kis_client.py:21`, `:54`, `:179`, `:188-191`). 앱과 같이 쓰는 파일이고, `.env` 키가 아니라 만료가 있는 토큰입니다 |
| `yahoo_now` | `core.ficc.data._yf_fetch(["SPY"], period)` | vintage |
| `coinbase` | 새 수신 함수(도구 안). `GET https://api.exchange.coinbase.com/products/BTC-USD/candles`, granularity 86400 | 엔드포인트는 공급사 감사 `:341`. 1회 300개, 응답 형식은 UNVERIFIED |
| `bitstamp` | 새 수신 함수(선택) | 엔드포인트 UNVERIFIED |
| `h15` | 새 수신 함수(선택). 연준 H.15 Data Download Program | 엔드포인트와 형식 UNVERIFIED |
| `binance` | `data.crypto.crypto_client.BinancePublic().daily("BTCUSDT", days=N)` | diagnostic |
| `treasury` | 새 수신 함수. 연도별 일별 par yield curve, "3 Mo" 열 | 공급사 감사 `:343`의 XML 경로. 형식 UNVERIFIED |
| `fred_now` | `config.FRED_BASE_URL`(`config.py:277`)의 fredgraph CSV를 직접 받음 | `_fred_fetch`는 '.' 관측을 버리므로(`core/ficc/data.py:167-169`) 공백 비교에는 직접 받습니다 |

- `load_history`와 `_cached`는 쓰지 않습니다. `auto`는 설정이 없으면 합성으로 바뀌고(3.4), `_cached`는 FICC 캐시 디렉터리에 씁니다(`core/quant/history.py:402`, `:451-452`).
- 저장소 코드 가운데 `fetch`가 `--out` 밖에 쓰는 곳은 `kis`의 토큰 파일 하나입니다. yfinance 같은 외부 라이브러리가 자체 캐시를 쓰는지는 확인하지 않았습니다(UNVERIFIED). 소유자 PC에서 HOME(Windows에서는 `USERPROFILE`)을 바꾸지 않습니다. 바꾸면 토큰을 새로 받아야 하기 때문입니다. 이 쓰기는 `~/.nextgen/macro/ledgers`를 건드리지 않습니다. 이 사실은 7절, 부록 A, 부록 B의 10.4 행에 적습니다.
- 수신 결과는 원자료 바이트, 정규화 CSV(`date,value`, UTF-8, LF), 메타데이터 JSON으로 남깁니다. 메타데이터에는 공급사, 엔드포인트, 키를 뺀 요청 인자, 수신 UTC 시각, 원자료 sha256, 규약(`total`, `split`, `none`, `rate_pct`), 호가 통화, 날짜 라벨 규칙이 들어갑니다.

### 9.3 키

- 별도 클론에는 `.env`가 없습니다. `config.py`는 `load_dotenv()`로 `.env`를 읽습니다(`config.py:25-29`). 그 파일을 찾는 위치는 UNVERIFIED입니다.
- 제안: `--env-file <연구 클론>\.env`를 받아 `FMP_API_KEY`, `KIS_APP_KEY`, `KIS_APP_SECRET`, `KIS_BASE_URL`만 읽습니다. 값은 출력하거나 기록하지 않습니다. `.env`를 복사하지 않습니다. 셸에 키를 직접 쳐서 PowerShell 기록에 남기지도 않습니다.

### 9.4 출력과 종료 코드

- `summary.json`, `detail.json`은 먼저 문자열로 만든 뒤, 새 폴더에 `open(..., "x", encoding="utf-8", newline="\n")`으로 씁니다(원형 `:672-680`).
- 종료 코드: 0 PASS, 1 FAIL, 3 WITHHELD, 2 거부(아무것도 쓰지 않음), 4 오류(그 밖의 예외. 종류만 출력하고 아무것도 쓰지 않음). 파이썬은 잡히지 않은 예외에도 1을 돌려주므로, 1을 FAIL로 읽으려면 4가 따로 있어야 합니다(원형 `run`, `:685-688`).
- 소유자는 결과를 종료 코드만이 아니라 마지막 줄 `PARITY <series> <판정> ...`으로 판단합니다(6.4).
- 거부 사유: md5 불일치, `--owner-run` 없는 보호 경로, 이미 있는 출력 폴더, git 작업 트리 안의 출력 폴더, 헤더가 `date,value`가 아닌 공급사 파일, 날짜가 늘지 않는 파일, 읽기 오류(예외 종류만 출력), 지도에 없는 공급사, 두 번 적은 공급사, 이유 목록에 없는 이유, 대조도 `--unavailable`도 아닌 필수 공급사, 2027-01-01 규칙 위반(`fetch`).

## 10. 합성 데이터 시험 계획

원형에 있는 사례는 26개입니다(`test_parity_check.py`). 정식 도구는 수신 부분에 가짜 전송 계층 사례를 더합니다.

| 묶음 | 사례 | 기대 | 원형 |
|---|---|---|---|
| SPY | 깨끗한 총수익 짝과 분할만 짝 | PASS. 7개 전년도 모두 배당일 4일 | 있음 |
| SPY | 가격 수익 파일을 총수익이라고 넣음 | `returns_same_convention` FAIL | 있음 |
| SPY | A에서 한 세션이 빠짐 | `calendar` FAIL, `only_b`에 그 날짜 | 있음 |
| SPY | B의 하루 값이 2% 틀림 | `n_over_tol` 2, `<=1e-01`, FAIL | 있음 |
| SPY | 한 해에 배당 조정 두 번 누락 | `adjustment_convention` FAIL | 있음 |
| SPY | 구간 밖 줄에 숫자가 아닌 값 | 파싱하지 않음, PASS | 있음 |
| SPY | 구간 안 칸이 숫자가 아님 | 거부. 출력에 그 값이 없음 | 있음 |
| SPY | vintage 짝만 있음 | WITHHELD | 있음 |
| 거부 | md5 불일치, 보호 경로, 작업 트리 안 출력 | 종료 2, 아무것도 쓰지 않음 | 있음 |
| 누출 | A에 표식값 4321.123457을 심음 | 요약에 표식이 없음. `thresholds` 밖에 소수 문자열이 없음. A와 B의 값 600개 어느 것도 요약에 없음 | 있음 |
| 누출 | 검증기에 실수, 날짜, 문자열 속 소수, 잘못된 정수를 넣음 | 모두 거부 | 있음 |
| 공급사 지도 | SPY에 `coinbase`, 필수 공급사 누락, 같은 공급사 두 번, 목록에 없는 이유 | 모두 종료 2, 아무것도 쓰지 않음. `--unavailable yahoo_now fetch_failed`면 PASS이고 `withheld_reasons`와 `providers`에 그대로 남음 | 있음 |
| BTC | 0.1% 거래소 잡음 | PASS, `lag` 0, `lag0_strictly_fewest` true | 있음 |
| BTC | B가 하루씩 밀린 라벨 | `day_boundary` FAIL, `lag` 1 | 있음 |
| BTC | A에서 7일 / 2일 빠짐 | FAIL / WARN, 날짜 목록 | 있음 |
| BTC | 뒤 구간 3%의 날에 3% 괴리 | `levels_and_returns` FAIL, 앞 구간은 안 | 있음 |
| BTC | B가 120일 늦게 시작 / 500일 늦게 시작 | PASS, `n_a_outside_b_span`과 `n_a_outside_evidence_spans` 120 / 상한 471 초과로 WITHHELD | 있음 |
| BTC | diagnostic 짝(`binance`)만 있음 | 검사는 WARN, 시계열 WITHHELD | 있음 |
| rf | 퍼센트, 휴일 공백 | PASS | 있음 |
| rf | 비율 단위 | `units` FAIL | 있음 |
| rf | 하루 1bp 차이 | `values` FAIL, 1건 | 있음 |
| rf | A 공백에 B가 값을 냄 | `blanks` WARN, 날짜 목록 | 있음 |
| 도구 | 요약 검증에서 값을 인용하는 예외가 남 | 종료 4, 마지막 줄 `PARITY spy ERROR exit=4 summary=-`, 출력에 값이 없음, 폴더가 생기지 않음 | 있음 |
| 도구 | SPY, BTC, rf 실행에서 나온 검사 ID | `COMPUTES`의 키와 같음. 코드에 상관·공분산·평균·표준편차·분산 호출이 없음 | 있음 |
| 계획 | SPY 공급사가 한국 날짜 라벨을 씀 | `calendar` FAIL | 없음 |
| 계획 | 2025~2026년 서명 NYSE 달력과 대조 | 서명 달력 밖 날짜는 FAIL | 없음 |
| 계획 | `fetch`가 `SYNTHETIC` History를 받음 | 거부 | 없음 |
| 계획 | 가짜 전송으로 각 수신 함수(FMP, KIS, Coinbase, Treasury, fredgraph) | 정규화 CSV와 메타데이터가 맞음. 키가 어떤 출력에도 없음 | 없음 |
| 계획 | `--env-file`의 키가 콘솔, 요약, 상세, 메타데이터에 없음 | 키 문자열 0건 | 없음 |
| 계획 | 수신 날짜가 2027-01-01 이후이고 끝 날짜를 명시하지 않는 호출 / 응답에 2027년 행이 있음 | 둘 다 거부, 아무것도 쓰지 않음 | 없음 |
| 계획 | `kis` 수신이 쓰는 경로 | `--out`과 `~/.nextgen/kis_token.json` 말고는 없음(가짜 전송과 임시 HOME으로) | 없음 |

- 합성 SPY는 평일 달력, 2자리 원가격, 분기 배당, Yahoo식 역방향 조정 계수(1 − D / 전일 종가)로 만듭니다(`test_parity_check.py`의 `spy_like`). 실제 SPY의 휴일이나 배당일은 쓰지 않습니다.
- 모든 사례는 시스템 임시 폴더 아래 새 폴더에서 돌고, 저장소의 파일은 원형 두 개 말고 읽지 않습니다.

## 11. 원형 실행 결과

### 11.1 자체 시험

- 파일(개정 1 뒤): `docs/nautilus_bridge/provider_parity_prototype/parity_check.py`(700줄, sha256 `4eed8fa579de9867cf7d40cf2acdc3b50b029c312cec71e8ed661d7f64819d44`), `test_parity_check.py`(517줄, sha256 `6bafad25e0664af11e9f4721bb17aaa34af54cdc17159a7a27715ebb05683f85`). 둘 다 ASCII, LF입니다. 개정 전은 614줄과 444줄이었습니다.
- 명령: 스크래치의 `mvenv/bin/python -I -B docs/nautilus_bridge/provider_parity_prototype/test_parity_check.py`. HOME과 TMPDIR은 스크래치 아래 새 폴더이고, HOME은 TMPDIR 안에 있지 않습니다.
- 결과: `SELFTEST PASS 26 cases`(개정 전 22개에 공급사 지도, BTC 늦은 시작, 오류 종료 4, 계산 목록 사례 4개를 더함). 클론의 `git status --short`는 이 문서와 `?? docs/nautilus_bridge/provider_parity_prototype/`만 보였습니다.
- 깨끗한 SPY 사례의 요약(발췌, `yahoo_now`는 `fetch_failed`로 적음): 시계열 PASS, `n_a_outside_evidence_spans` 0, `withheld_reasons`는 `yahoo_now not compared: fetch_failed` 하나. `returns_same_convention`은 `n_over_tol` 0, `max_abs_bucket` `<=1e-06`. `adjustment_convention`은 `n_full_years` 7, `n_years_expected_ex_days` 7, `yield_band_ok` true.
- 깨끗한 BTC 사례의 요약(발췌): 시계열 PASS, `day_boundary`는 `lag` 0, `lag0_strictly_fewest` true.

### 11.2 스캐너 패턴 재현

- `docs/**/*.py`를 재귀로 스캔하는 세 테스트의 패턴을 원형 두 파일에만 다시 돌렸습니다(개정 1 뒤에 다시 돌림). 테스트 자체를 돌린 것은 아닙니다.
  - `tests/macro_m6_context.py:506`의 문자열 검색: 0건.
  - `tests/macro_m7_ledger.py:328`의 `gate_ledger.scan_forbidden` 패턴(`core/quant/gate_ledger.py:851-865`, 독스트링 제거 뒤): 0건.
  - `tests/macro_tf_gov.py:262-280`의 0.4 배수 패턴: 0건.
- 원형 파일에는 T-RO-01의 금지 문자열(`tests/macro_m0_harness.py:29-36`)이 없습니다. `docs/` 하위 폴더는 T-RO-01 스캔 대상이 아닙니다(S-11).

### 11.3 원형이 하지 않는 것

- 수신(`fetch`)과 2027-01-01 규칙, 표 읽기(`--table`), 서명 달력 대조, 키 처리는 없습니다. 공급사 지도, 계산 목록, 오류 종료 4, B 구간 기준 덮는 비율은 원형에 있습니다.
- 실제 파일과 Windows에서는 돌리지 않았습니다.

## 12. 소유자 결정

| # | 결정할 것 | 선택지 | Claude 권고 | 정하지 않으면 |
|---|---|---|---|---|
| D-1 | 순서 선택지 | A, A', B, C(8.2). D와 E는 권하지 않음. A와 A'의 차이: A는 7A.2를 미루지 않지만 자료 교체 때 Step 7A 전체를 다시 하고, A'는 7A.2를 도구 완성과 대조까지 미루지만 교체를 7A.2 전에 흡수합니다(5.4, 8.3) | **A** | ⑤-2 도구 작성을 시작하지 않습니다. ⑥-1은 로드맵상 ⑤-2를 기다립니다 |
| D-2 | 이 초안과 원형의 커밋 위치 | (가) 별도 브랜치 (나) 7A.2 시작 전 연구 브랜치, "끼어든 변경" 승인 문장과 함께 (다) 커밋하지 않음 | **(가)** | 파일이 세션 클론에만 남습니다 |
| D-3 | 스펙 예외와 관문 문장(부록 A) | 승인 / 수정 / 거부. 승인 시 넣는 시점: A면 7A.4 검토 커밋 안 또는 바로 뒤, A'면 7A.2 시작 전 | **승인, 검토 커밋 바로 뒤 따로**(A일 때) | 등록 전 구간 계산이 3.9에 걸리므로 BTC 대조를 할 수 없습니다 |
| D-4 | 공급사, 키, 권리 처리 | SPY: FMP(키, 플랜 깊이), KIS(계좌), Yahoo 재수신. BTC: Coinbase, Bitstamp(선택), Binance(진단). rf: Treasury, FRED 재수신. 원자료는 PC에만, 요약만 커밋 | 3절 표 그대로. `--env-file` 방식 | 독립 짝이 없어 WITHHELD가 됩니다 |
| D-5 | 허용치, 공급사 지도, 재실행 규칙, 늦게 시작한 공급사 | 5.1과 5.5 승인 / 수정. 늦게 시작한 공급사: (가) 덮는 비율은 B의 구간 안에서 재고, 구간 밖 A 날짜는 따로 세어 상한(SPY·rf 5, BTC 471)을 둠 (나) 2014-09-17부터 Coinbase의 첫날까지를 덮는 두 번째 USD 거래소(Bitstamp)를 필수로 함 | **5.1과 5.5 승인, (가).** 어떤 결과든 보기 전에 정해야 합니다. (나)는 엔드포인트도 시작일도 확인하지 않은 공급사에 판정을 묶습니다 | 판정 기준이 없습니다. 같은 공급사를 역할을 바꿔 다시 돌리는 일을 막지 못합니다 |
| D-6 | 관문 규칙 | 5.3(절차 관문) / 참고만 | **5.3** | ⑤-2가 파일럿을 막지 못합니다 |
| D-7 | Claude 출력 허용 목록과 `detail.json` | 6.2 승인 / 더 좁힘. `detail.json`을 Step 10 뒤 커밋할지 | **6.2 승인. `detail.json`은 Step 10 뒤에 따로 정함** | 요약에 무엇을 넣을지 정해지지 않습니다 |
| D-8 | BTC 대조 시점 | ⑥-1 전에 세 시계열 모두(로드맵 그대로) / 소유자 실행(⑤-2/d)을 둘로 나눠 ⑤-2/d1(SPY, rf)은 ⑥-1 전, ⑤-2/d2(BTC)는 ⑥-2 전 | **⑥-1 전에 모두.** 한 번에 돌리는 편이 단순합니다 | 로드맵 그대로 ⑥-1 전에 모두 |
| D-9 | 파일럿 기간의 소유자 판정 기록 위치 | 별도 브랜치 `results/RULINGS.md` → Step 10에 실행 기록과 스펙 Status / `OWNER_RULINGS_LOG.md`(Step 10 허용 경로 밖이라 병합 뒤 `main`에서) | **앞의 것** | Step 10 diff 규칙에 걸릴 수 있습니다 |

- 하위 ID 제안: ⑤-2/a 이 설계 초안, ⑤-2/b 도구와 시험(별도 브랜치), ⑤-2/c 스펙 문장, ⑤-2/d 소유자 실행과 요약, ⑤-2/e Claude 검토와 Step 10 기록. D-8에서 나누기를 고르면 ⑤-2/d만 ⑤-2/d1(SPY, rf)과 ⑤-2/d2(BTC)로 나눕니다.
- 한 하위 ID는 한 가지 일만 뜻합니다. 인계 장부(LEDGER.md)에 적힌 ID는 끝난 일이고 다시 하지 않기 때문입니다(`CLAUDE.md`의 인계 규칙). 예를 들어 ⑤-2/a(이 초안)를 장부에 적어도 SPY와 rf의 대조는 ⑤-2/d 또는 ⑤-2/d1로 남습니다.

### 12.1 소유자 결정 (2026-11-04)

- 출처: Geon Koh가 2026-11-04 Claude Code 채팅(세션 `session_016uB1jgeiPdP8gPkAez3Wrx`)에 붙여 넣은 결정표 2차 답입니다. 첫 줄 원문은 `[QUANTGEN 소유자 결정 2026-11-04 · 2차] 아래는 Geon Koh의 결정입니다. (U6 승인과 A2 확인은 이미 기록됨)`입니다.
- 번호 대응: 결정표의 U5는 이 문서의 D-1입니다. P-D2~P-D9는 D-2~D-9입니다.
- 원문은 결정표 답 그대로입니다. 메모도 그대로 옮겼습니다. 아홉 건 모두 Claude 권고안입니다.
- **D-1 순서 (U5).** 원문: `U5 = (가) A: 7A 끝난 뒤 별도 클론에서 대조, 연구 브랜치에는 스펙만 바꾸는 커밋 하나 [권고]`
  - 반영: 순서는 A입니다. Step 7A는 끝났습니다. 연구 브랜치는 `83ee469`(7A.4 검토 커밋)이고, 소유자가 그 커밋에서 7A.5를 확인했습니다.
- **D-2 이 초안과 원형의 커밋 위치 (P-D2).** 원문: `P-D2 = (가) 별도 브랜치(claude/provider-parity-design-20261104)에 둠 [권고]`
  - 반영: 이 문서와 원형은 `claude/provider-parity-design-20261104`에 둡니다. 연구 브랜치에는 넣지 않습니다.
- **D-3 스펙 예외와 관문 문장, 부록 A (P-D3).** 원문: `P-D3 = (가) 승인. 7A.4 검토 커밋 바로 뒤에 따로 넣음 [권고] | 메모: 7A 전체가 마무리 된 것 감안하여 최대한 빨리 (금방 넣기)`
  - 반영: 부록 A를 승인합니다. 스펙만 바꾸는 커밋으로, 7A.4 검토 커밋 `83ee469` 바로 뒤에 따로 넣습니다. 메모대로 최대한 빨리 넣습니다.
  - 이 문서는 그 커밋을 7A.5 pull 전에 넣는다고 적었습니다(0절, 8.3, 8.4 2단계). 7A.5는 이미 `83ee469`에서 끝났습니다. 그래서 이 커밋은 7A.5 HEAD 뒤에 들어갑니다. S-5(파일럿은 7A.5 HEAD에 묶임)와 어떻게 맞출지는 이 결정에 적혀 있지 않습니다.
  - 이 기록을 적을 때 원격 연구 브랜치의 끝은 `83ee469`였습니다.
- **D-4 공급사, 키, 권리 처리 (P-D4).** 원문: `P-D4 = (가) 초안 3절 표 그대로 [권고]`
- **D-5 허용치, 재실행 규칙, 늦게 시작한 공급사 (P-D5).** 원문: `P-D5 = (가) 5.1·5.5 승인. 늦게 시작한 공급사는 그 공급사 구간 안에서 비율 계산 [권고]`
  - 반영: 5.1과 5.5를 승인합니다. 늦게 시작한 공급사는 D-5의 (가)입니다. 덮는 비율은 그 공급사(B)의 구간 안에서 잽니다.
- **D-6 관문 규칙 (P-D6).** 원문: `P-D6 = (가) 절차 관문(5.3): 통과하지 않으면 파일럿을 보류하거나 주석을 달고 진행 [권고]`
- **D-7 Claude 출력 허용 목록과 `detail.json` (P-D7).** 원문: `P-D7 = (가) 6.2 목록 승인. detail.json 처리는 Step 10 뒤에 정함 [권고]`
- **D-8 BTC 대조 시점 (P-D8).** 원문: `P-D8 = (가) Pilot 1 전에 세 시계열 모두 [권고]`
  - 반영: ⑤-2/d를 나누지 않습니다. 세 시계열 모두 Pilot 1(⑥-1) 전에 대조합니다.
- **D-9 파일럿 기간의 판정 기록 위치 (P-D9).** 원문: `P-D9 = (가) 별도 브랜치의 results/RULINGS.md → Step 10에 반영 [권고]`

## 13. UNVERIFIED

**공급사 사실**
- FMP: SPY 2004년까지의 이력이 소유자 플랜에 있는지. `adjClose`의 조정 방식.
- KIS: SPY의 거래소 코드가 `AMS`인지. 해외 일봉의 이력 깊이. `xymd`가 현지 날짜인지.
- Coinbase: `BTC-USD` 일봉의 시작일, 라벨이 버킷 시작 시각인지, 호출 한도와 응답 형식. 시작일이 2016-01-01보다 늦으면 BTC의 독립 짝은 `edge_uncovered_max`에 걸려 WITHHELD입니다(5.1).
- Bitstamp: 일봉 엔드포인트와 시작일. 연준 H.15 Data Download Program의 경로와 형식.
- 끝 날짜 인자: FMP `to`, fredgraph `coed`, Coinbase `end`, yfinance `end`의 이름과 동작(9.1).
- FRED DTB3가 할인율 기준이라는 것의 1차 출처. 저장소 문서(`QUANTGEN_MACRO_INTEGRATION.md:1440`)만 확인했습니다(3.4).
- US Treasury: 일별 par yield curve 경로와 형식. DGS3MO가 재무부 3개월 고정만기 수익률과 같은 값인지.
- Yahoo: BTC-USD의 출처(여러 거래소를 모은 가격인지)와 하루 경계. SPY `auto_adjust=True`의 조정 공식.
- SPY: 분할한 적이 없는지. 2005~2025년 해마다 배당일이 4일인지. 분기 배당이 가격의 0.3~0.6%인지. 하루 변동이 25%를 넘은 적이 없는지.
- 모든 권리 상태. 권리 표는 공급사 단위 검토이고 데이터셋별 권리는 미확인이라고 스스로 적습니다(권리 표 `:4-5`, `:66`). 공급사 감사의 원문 미확인 항목(`suppliers_ficc_btc.md:435`, `:437`)도 그대로입니다.

**설계와 규칙 해석**
- 5.1의 허용치는 실제 자료로 보정하지 않았습니다. 거짓 FAIL의 비율을 모릅니다.
- 스펙만 바꾸는 커밋을 7A.4 검토 커밋 뒤, 7A.5 pull 전에 따로 넣는 것이 S-4와 S-5의 뜻에 맞는지.
- A'에서 7A.2 전에 넣는 스펙 커밋에 대해, 소유자의 부록 A 승인 문장이 7A.4가 확인할 "승인 범위"가 되는지.
- `day_boundary`의 차이 개수 판정이 실제 거래소 잡음에서도 0일 이동을 가장 적게 고르는지. 합성 0.1% 잡음에서만 확인했습니다. 5.1의 잡음 0.3~1%, 변동성 4%도 가정입니다.
- `config.py`의 `load_dotenv()`가 `.env`를 찾는 위치.

**실행**
- 원형은 Linux의 합성 자료로만 돌렸습니다. Windows, 실제 파일, 수신 부분은 확인하지 않았습니다.
- 11.2는 스캐너 패턴의 재현이고, 테스트 스위트를 돌린 것이 아닙니다.
- 러너가 `runs/` 아래 미추적 파일을 면제한다는 것(S-7)은 코드를 읽어 확인했고, 실행해 보지는 않았습니다.
- 8.4 2단계의 장부를 열지 않는 `code_sha256` 명령은 돌려 보지 않았습니다. 허용 인터프리터가 러너의 import를 모두 풀 수 있는지도 확인하지 않았습니다.
- 저장소 코드의 수신 경로가 `--out` 말고는 KIS 토큰 파일에만 쓴다는 것(9.2)은 코드 읽기로만 확인했습니다. 외부 라이브러리의 자체 캐시는 확인하지 않았습니다(`core/ficc/data.py:284-285`는 `_cache_put` 안, `core/quant/history.py:451-452`는 `_cached` 안이라 도구가 거치지 않음).

## 부록 A. 스펙 문장 초안(영문, 소유자 승인 전)

스펙은 영문이므로 영문으로 적습니다. Status 블록에 한 항목, 10절에 10.5를 더합니다.

> **Status bullet.** "**<date> owner addendum (⑤-2 provider parity; spec-only).** <owner sentence verbatim>. It adds 10.5 and changes no code: `code_sha256` and every `owner_confirmed` stay valid. The ⑤-2 rows of 10.4 are written at Step 10."

> **10.5 Provider parity (⑤-2).**
> - *Tool.* `tools/provider_parity/parity_check.py` on branch `claude/provider-parity-5-2` at commit `<40 hex>`, sha256 `<64 hex>`, outside this branch and outside `code_sha256`. A run with other tool bytes counts under this section only by an owner ruling recorded with the earlier result.
> - *When and where.* Before Step 8, the owner runs it from a separate clone on his machine, from that clone's root, as `python -B -m tools.provider_parity.parity_check`. It reads each table's `prices_file` and `rf_file` read-only, checks their md5 against the table, and compares them with other providers' series fetched on the same machine. No observation dated on or after 2027-01-01 is requested, stored or compared.
> - *Exception to 3.9, narrow.* On the owner's machine only, on the pilot windows and before registration, the tool may compute: calendar membership of each provider's dates; the day-by-day differences between two providers' closes, simple or log returns and rates, including the differences of daily returns at lags -1, 0 and +1 for the BTC-USD day boundary; and counts, extremes, percentiles, ranges and per-year sums of those differences. Of one provider's series alone it computes only range and gap checks: no one-day move above a split-shaped threshold, missing days, rate units within range, a rate observation before the window start. It computes no correlation, no signal, no strategy return, and no mean, volatility, Sharpe or drawdown of any series. The tool's `COMPUTES` table names these kinds check by check, and its self-test holds the two together.
> - *Providers.* Each provider has the role and convention of 10.5.1, and the tool refuses any other provider or role. Every required provider is compared or recorded as unavailable with a reason; the summary lists both.
> - *Thresholds.* Those of 10.5.1.
> - *Outputs.* Only `summary.json` leaves the owner's machine, with the fields of 10.5.2. `detail.json` stays there until Step 10, and its later commit is the owner's decision. Claude reads only `summary.json`.
> - *Runs of record.* Every summary produced is committed under `results/` on the tool's branch. Per series, the first run that ends PASS, FAIL or WITHHELD is the run of record; a REFUSED or ERROR run writes nothing and is not a run. A later run, on new fetches or the same files, counts only after an owner ruling recorded next to the earlier result, which stays. A change to 10.5.1 after any summary exists is recorded with the earlier result in the same way.
> - *Gate.* Step 8 starts only when the SPY and DGS3MO runs of record say PASS, or the owner has written a ruling for each that does not; Step 9 likewise for BTC-USD, in addition to R-11's pilot-1 condition.
> - *Writes.* Nothing the tool writes enters this clone, `docs/asset_expansion/` or a ledger. The `kis` fetch reads, and may rewrite, the app's KIS access token `~/.nextgen/kis_token.json`; it writes nothing else under `~/.nextgen`.
> - *Step 10.* The summaries of record are copied to `docs/nautilus_bridge/runs/PP-<UTC>-<series>/provider_parity_summary.json`, and the execution record states their sha256, the tool's commit and sha256, and each outcome.
>
> **10.5.1 Providers and thresholds (fixed before any summary exists).**
>
> | Series | Providers: role, convention (required unless optional) | Thresholds |
> |---|---|---|
> | SPY (`yf_SPY.csv`, total return) | `fmp`: independent, total; `kis`: cross, split; `yahoo_now`: vintage, total | `coverage_min` 0.99; `edge_uncovered_max` 5; `ret_diff_tol` 2e-4; `ret_diff_max` 2e-3; `ret_diff_share_max` 0.005; `ret_diff_floor_days` 5; `drift_range_max` 5e-3; `jump_abs_max` 0.25; `ex_gap_min` 5e-4; `ex_gap_max` 2e-2; `ex_days_per_year` 4 (3 or 5 is WARN); `yield_band` [0.005, 0.04] |
> | BTC-USD (`yf_BTC-USD.csv`) | `coinbase`: independent, none; `bitstamp`: independent, none, optional; `binance`: diagnostic, none | `coverage_min` 0.95; `edge_uncovered_max` 471; `late_from` 2017-01-01; `level_p50_max` 0.003; `level_p99_max` 0.015; `level_max` 0.05; `early_level_p99_max` 0.03 and `early_level_max` 0.10 (WARN only); `missing_days_warn_max` 5; `jump_log_abs_max` 0.7; `ret_diff_big` 0.02 (also the day-boundary tolerance); `ret_diff_share_max` 0.005 |
> | DGS3MO (`fred_DGS3MO.csv`) | `treasury`: independent, rate_pct; `h15`: independent, rate_pct, optional; `fred_now`: vintage, rate_pct | `coverage_min` 0.99; `edge_uncovered_max` 5; `value_tol_pct` 0.005; `range_pct` [-1, 20]; `unit_max_at_least_pct` 1.0; `seed_lookback_days` 31 |
>
> Coverage is measured over A's dates inside the provider's first-to-last span; A's dates outside it are counted against `edge_uncovered_max`. Unavailable reasons: `no_key`, `plan_or_access`, `fetch_failed`, `short_history`. A vintage or diagnostic pair reports FAIL as WARN. A series is FAIL when A's integrity check or any independent or cross pair fails, WITHHELD when no independent or cross pair was evaluated in full, and PASS otherwise. Exit codes: 0 PASS, 1 FAIL, 3 WITHHELD, 2 refused, 4 error; the result is the last console line `PARITY <series> <outcome> ...`.
>
> **10.5.2 Summary fields.** Identifiers and hashes (`schema`, `run_id`, `created_utc`, `tool.sha256`, `pinned.md5`, `md5_ok`, `file_sha256`); the window, the thresholds and the provider map; integers under keys `n_*`; `lag` in {-1, 0, 1}; calendar dates under `first_date`, `last_date`, `only_a`, `only_b`, `missing_a`, `blank_a_value_b` and `value_a_absent_b`, at most 100 each; decade buckets such as `<=1e-04`; booleans; outcomes and `withheld_reasons`. Nothing else: no price, return, rate, per-date difference, exact extreme or its date, per-lag count, yearly gap sum or level ratio. The tool refuses to write a summary that breaks this rule.

- 개정 1에서 바꾼 점. 앞 초안의 10.5는 허용치와 허용 목록을 이 설계 초안의 절 번호로 인용했습니다. 그런데 이 초안은 별도 브랜치에만 커밋하므로(D-2), 연구 브랜치와 병합 뒤 `main`의 스펙이 그 브랜치에 없는 파일을 가리키게 됩니다. 그래서 허용치(10.5.1)와 출력 허용 목록(10.5.2)을 스펙 본문에 그대로 넣고, 도구는 커밋 sha와 sha256으로 고정합니다. 이 커밋은 스펙만 바꾸므로 S-4와 맞습니다.
- `<40 hex>`와 `<64 hex>`는 8.4 1단계가 끝나야 정해집니다. 그래서 2단계(스펙 커밋)는 1단계 뒤입니다.

## 부록 B. 스펙 10.4 행 초안(영문)

| When | Who | Data | What was computed | Ledger rows |
|---|---|---|---|---|
| 2026-11-04 | Claude, ⑤-2 design draft and prototype | synthetic series only; no price file, no price cache, no `fred_DGS3MO.csv`; code and docs read | prototype self-test (22 cases; 26 after revision 1), scanner-pattern replica | none |
| <run date> | owner's machine, provider-parity tool ⑤-2 (commit <…>, sha256 <…>) | `yf_SPY.csv` 2004-12-01 to 2026-09-25 and `fred_DGS3MO.csv` (both md5-pinned), against <providers>; `yf_BTC-USD.csv` whole file against <providers>; providers recorded unavailable: <…>. No observation dated on or after 2027-01-01. The `kis` fetch read, and may have rewritten, `~/.nextgen/kis_token.json` (an access token, not an `.env` key); no other `~/.nextgen` path | calendar membership; day-by-day differences between providers' closes, returns and rates, with their counts, extremes, percentiles, ranges and per-year sums; day-boundary lag from difference counts at lags -1, 0 and +1. No correlation, signal or strategy return; of one series only range and gap checks | none |
| <review date> | Claude | the ⑤-2 `summary.json` files only: counts, outcomes, decade buckets, calendar dates; no price, return, rate value or per-date difference | review and recommendation | none |
