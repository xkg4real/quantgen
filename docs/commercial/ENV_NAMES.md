# QUANTGEN 환경변수 이름 목록 (KEY-1)

- 판: v0.1 (2026-11-17). 작성: PAYMENTS_ACCOUNT_KEYS 세션. ID `KEY-1`. 고침 2026-11-19 (KEY-4): 4절 "main에는 아직 없습니다"의 대상, 5절 `names.py` 행 (연구용 9개·토큰·종류 이름) — 메인 세션 KEY-3 검토 잔여 8번.
- 기준: `origin/main` `5888d05` (2026-11-17 21:33 KST). `git grep`으로만 셌습니다 (`docs/asset_expansion/cache` 제외).
- **이 문서에는 이름만 있고 값은 0개입니다.** `.env`, `~/.nextgen`은 열지 않았습니다. `.env.example`은 줄 앞의 이름만 뽑았습니다.
- 바탕: handoff `plans/2026-11-17/D7_ENV_STRUCTURE.md` 1장·5장.
- D7-G (공급원 게이트웨이)는 소유자가 2026-11-18에 승인했습니다 (5절). "D7-G 길" 열의 `commercial` 값은 아직 설계 값입니다. KEY-2 코드는 PR #128 (5절).

## 0. 요약

| 묶음 | 수 | 어디 |
|---|---|---|
| 앱 비밀 키 | **10** | 1절 |
| 앱 설정 (비밀 아님) | **16** (`NEXTGEN_MAX_AGE_<코드>` 하나로 셈) | 2절 |
| 앱 실행에 쓰는 이름 합계 | **26** | `config.py`, `core/markets.py`의 두 곳에서만 읽음 |
| 저장소 전체 (도구·연구·테스트·CI 포함) | **49** (아래 3절 셈) | Notion 상업화 분석서의 "47개"와 2개 차이 |
| 데이터소스 세션의 연구용 이름 (DIDM) | 12 | 4절. `core/credentials/names.py`의 `RESEARCH` (main `9f76b07`, KEY-3; Alpaca 2개·Massive 1개 2026-11-24 더함) |

- 환경을 읽는 곳 (KEY-2 전, main `5888d05` 기준; 지금은 아래 5절): `config.py:34` (`_clean(name)` → `os.getenv`), `core/markets.py:222` (`NEXTGEN_MAX_AGE_<코드>`). `.env`는 `load_dotenv()`가 읽었습니다. KEY-2 (PR #128) 뒤에는 `config._clean`이 `core.credentials.read_setting`을 부르고, `.env`는 개발판에서만 `core.credentials.load_dotenv_for_development()`가 읽습니다. 어느 쪽이든 `.env`가 없어도 앱은 켜집니다 (키가 필요한 기능만 꺼짐).
- `.env.example`에 있는 이름: 14개 (`FMP_API_KEY`, `KIS_APP_KEY`, `KIS_APP_SECRET`, `OPENDART_API_KEY`, `KRX_API_KEY`, `ANTHROPIC_API_KEY`, `QUANTGEN_AI_MODEL`, `GS_CLIENT_ID`, `GS_CLIENT_SECRET`, `UPBIT_ACCESS_KEY`, `UPBIT_SECRET_KEY`, `NEXTGEN_FICC_CACHE`, `NEXTGEN_FICC_CACHE_TTL`, `NEXTGEN_NO_DATA_GRACE`).

## 1. 앱 비밀 키 (10개)

"상용판 성격"은 D7 분석의 분류입니다: **사용자 증권사 키** / **사용자 데이터 키** / **사용자 AI 키** / **회사 계약** / **제외**. "D7-G 길"은 `routes.json`의 `personal`(지금) → `commercial`(법인 뒤, 예시) 값입니다.

| # | 이름 | 읽는 줄 (`config.py`) | 읽는 함수 | 쓰는 곳 (main `5888d05`) | 키가 없으면 | 상용판 성격 | D7-G 길 |
|---|---|---|---|---|---|---|---|
| 1 | `KIS_APP_KEY` | :81 | `kis_credentials()`, `kis_ready()` | `data/krx/kis_client.py:206,237`, `data/kis_stream.py:223` (실시간 승인키). 준비 확인 `kis_ready()`: `core/quant/history.py` 5곳, `core/research/derivatives_workflow.py:34`, `core/research/etf_workflow.py:48`, `data/kis_markets.py:827`, `data/krx/kis_client.py:174,366`, `quantgen_desktop/market_tools.py:125`, `ui/derivatives_page.py:53`, `ui/macro_state_panel.py:653` | 국내·해외 시세, 차트, 순위, 실시간이 꺼짐 | 사용자 증권사 키 | `local_key` → 미정 (코스콤 답에 따라 `local_key` 또는 `company`) |
| 2 | `KIS_APP_SECRET` | :81 | 같음 | 같음 | 같음 | 사용자 증권사 키 | 같음 |
| 3 | `UPBIT_ACCESS_KEY` | :265 | `upbit_keys()`, `upbit_ready()` | `data/crypto/crypto_client.py:339` (보유 자산). 준비 확인: `core/research/crypto_workflow.py:65`, `data/crypto/crypto_client.py:334,360`, `ui/crypto_page.py:163` | 보유 자산만 꺼짐. 공개 시세는 됨 | 사용자 증권사 키 (거래소) | `local_key` 고정 → `local_key` 고정 |
| 4 | `UPBIT_SECRET_KEY` | :265 | 같음 | 같음 | 같음 | 사용자 증권사 키 (거래소) | 같음 |
| 5 | `FMP_API_KEY` | :53 | `fmp_key()`, `fmp_ready()` | `data/fmp/quote_client.py:115`, `core/quant/history.py:126,356,509`, `core/market/market_cap.py:210`, (`core/engine/feed.py`는 클라이언트 경유) | 미국 일봉·시세가 꺼짐 | 회사 계약 (표시 라이선스) 또는 제외 | `local_key` → `company` 또는 `off` |
| 6 | `KRX_API_KEY` | :141 | `krx_key()`, `krx_ready()` | `data/krx/krx_market_client.py:77,84` | 전체 시장 스냅샷이 꺼짐 | 사용자 데이터 키 또는 회사 계약 (약관 **미검증**) | `local_key` → `local_key` 또는 `company` |
| 7 | `OPENDART_API_KEY` | :133 | `opendart_key()`, `opendart_ready()` | `data/krx/opendart_client.py:67,72,210` | 공시·재무가 꺼짐 | 사용자 데이터 키 (1인 1키로 알려짐, 2차 출처) | `local_key` → `local_key` |
| 8 | `ANTHROPIC_API_KEY` | :219 | `anthropic_key()`, `ai_ready()` | `core/quant/insights.py:57,59,321`, `core/ficc/insights.py:25` | AI 해설만 꺼짐 | 사용자 AI 키 (나중에 회사 중계 선택) | `local_key` (기본 꺼짐) → `local_key` |
| 9 | `GS_CLIENT_ID` | :231 | `gs_client_id()` | `core/quant/gsq.py:54,75` | 선택 기능만 꺼짐 | 제외 후보 | `local_key` → `off` 후보 |
| 10 | `GS_CLIENT_SECRET` | :235 | `gs_client_secret()` | `core/quant/gsq.py:54,75` | 같음 | 제외 후보 | 같음 |

- `config.py` 밖에서 이 10개 이름을 직접 읽는 앱 코드는 없습니다. 예외는 연구 도구 `tools/provider_parity/parity_check.py:175-176` (`FMP_API_KEY`, `KIS_APP_KEY`, `KIS_APP_SECRET`, `KIS_BASE_URL`; 앱 실행과 무관)와 그 사본들 (`grokteam/out/frozen_book/...`, 보관 사본).
- 키 값은 화면에 나오지 않습니다. 설정·연결 화면은 "있음/없음"과 이름만 봅니다 (`config.py:157`, `:238`, `:268`의 `*_provider_status()`).
- 디스크의 자격 정보 (KEY-2 전, main `5888d05`): KIS 접근 토큰이 `~/.nextgen/kis_token.json`에 평문이었습니다. KEY-2 (PR #128)부터는 OS 키 보관함이 먼저이고, 파일은 대체 수단 (0600, TRADEGEN과 공유라 지우지 않음)입니다. 자세한 것은 5절 "KIS 토큰 캐시" 행.

## 2. 앱 설정 (비밀 아님, 16개)

| # | 이름 | 읽는 줄 | 용도 | 기본값 있음 | 상용판 |
|---|---|---|---|---|---|
| 1 | `FMP_BASE_URL` | `config.py:62` | FMP 주소 | 예 | 공개판에서 고정 (환경에서 읽지 않음, KEY-2 제안) |
| 2 | `NEXTGEN_FMP_MIN_INTERVAL` | :68 | 같은 종목 재조회 간격 | 예 | 개발 전용 |
| 3 | `KIS_BASE_URL` | :84 | KIS 주소 (실전/모의) | 예 | 사용자 설정 (실전/모의 선택) 후보 |
| 4 | `OPENDART_BASE_URL` | :136 | OpenDART 주소 | 예 | 고정 |
| 5 | `KRX_BASE_URL` | :150 | KRX Open API 주소 | 예 | 고정 |
| 6 | `NEXTGEN_HTTP_TIMEOUT` | :154 | 요청 시간 제한 | 예 | 개발 전용 |
| 7 | `NEXTGEN_TRADING_DIR` | :179 | 로컬 거래 기록 폴더 | 예 | 사용자 설정 후보 |
| 8 | `QUANTGEN_MACRO_DIR` | :186 | 매크로 자료 폴더 | 예 | 사용자 설정 후보 |
| 9 | `NEXTGEN_QUOTE_MAX_AGE` | :191 | 규칙 엔진 시세 유효시간 | 예 | 개발 전용 |
| 10 | `NEXTGEN_ENGINE_TICK` | :194 | 규칙 엔진 주기 | 예 | 개발 전용 |
| 11 | `NEXTGEN_NO_DATA_GRACE` | :203 | 허용 누락 횟수 | 예 | 개발 전용 |
| 12 | `QUANTGEN_AI_MODEL` | :227 | AI 해설 모델 이름 | 예 | 앱 설정 |
| 13 | `FRED_BASE_URL` | :280 | FRED 주소 | 예 | 고정 |
| 14 | `NEXTGEN_FICC_CACHE_TTL` | :283 | FICC 캐시 유효시간 | 예 | 개발 전용 |
| 15 | `NEXTGEN_FICC_CACHE` | :287 | FICC 캐시 폴더 | 예 | 사용자 설정 후보 |
| 16 | `NEXTGEN_MAX_AGE_<코드>` | `core/markets.py:222` | 시장별 시세 유효시간 (코드마다 하나) | 예 | 개발 전용 |

- 16개 모두 기본값이 있어 `.env` 없이 동작합니다. KEY-2는 이 이름들을 **건드리지 않습니다** (`_clean`은 비밀 10개만 저장소로 보냄).
- "상용판" 열은 제안입니다. 공개판에서 환경변수 읽기를 끄는 범위는 OS 세션의 `core/app_identity.py` "개발판" 표시와 함께 정합니다.

## 3. "47개"와의 차이

Notion "QUANTGEN 상업화 실행 분석서" (`40e5c916fe0c815ba983dd4c4cc7992c`)는 "소스상 환경변수 이름 47개"라고 적었습니다. 셈 방식이 적혀 있지 않아 같은 숫자를 다시 만들 수는 없었습니다 (**미검증**). 같은 기준(저장소 전체)으로 다시 센 결과입니다.

| 묶음 | 수 | 이름 |
|---|---|---|
| 앱 실행 (1·2절) | 26 | 위 표 |
| 연구·실험 도구 | 11 | `GROKTEAM_DATA`, `GROKTEAM_LEDGER_DIR` (`grokteam/book.py`), `ANALYSIS_DIR` (`paper_live/analyze.py` 등), `PAPER_PROFILE` (`paper_live/config.py`), `REPLAY_HOLDOUT`, `REPLAY_LAST` (`paper_live/replay.py`, 백업 사본), `PRIMER_END_DATE`, `PRIMER_OFFLINE` (`docs/build_models_primer.py`), `QUANTGEN_AGY` (`tools/debate.py`), `QUANTGEN_TECTONIC` (`tools/paper/build.py`), `PORT` (`.claude/run_web.py`) |
| OneDrive 감지 (연구 도구) | 3 | `OneDrive`, `OneDriveConsumer`, `OneDriveCommercial` (`tools/provider_parity/parity_check.py:243`) |
| 테스트·OS | 4 | `QT_QPA_PLATFORM` (화면 시험), `HOME`, `USERPROFILE`, `SYSTEMROOT` (시험 격리) |
| CI 워크플로 | 5 | `COMPLIANCE_ARTIFACT_URL`, `COMPLIANCE_EXPORT_REF`, `GITHUB_STEP_SUMMARY`, `GITHUB_WORKSPACE`, `RUNNER_TEMP` |
| **합계** | **49** | |

- 셈 명령 (재현용): `git grep -hoE "(getenv|environ\.get|environ\[|_clean|setdefault|environ\.pop)\(?\s*[\"'][A-Z][A-Z0-9_]{2,}[\"']" -- '*.py' ':!docs/asset_expansion/cache'` → 39개, 여기에 `NEXTGEN_MAX_AGE_<코드>` (f-문자열), OneDrive 3개 (튜플 상수), `SYSTEMROOT`, 워크플로의 `${...}` 5개를 더함.
- 해석: 47과 49의 차이 2개는 OS·CI가 주는 이름 (`HOME`/`USERPROFILE`/`SYSTEMROOT`, `GITHUB_*`/`RUNNER_TEMP`)을 어디까지 넣었는지, 또는 분석서 작성일(2026-11-04) 뒤에 더해진 연구 도구 이름 때문으로 보입니다 (추정). **앱 실행에 쓰는 이름은 26개이고, 그중 키 보관함 대상은 비밀 10개뿐**이라는 판단에는 영향이 없습니다.

## 4. 데이터소스 세션이 더할 이름 (연구용, 따로 표시)

이 이름을 쓰는 연구 도구 코드 (`tools/didm`, `data/didm`)는 데이터소스 세션 브랜치 (`claude/data-source-didm-20261117`)에 있고 main에는 아직 없습니다. 이름 목록 자체는 main에 있습니다 (`core/credentials/names.py`의 `RESEARCH`, KEY-3 `9f76b07`). **연구 도구 전용**입니다. 소유자 답 (2026-11-19, "더해주세요")으로 자격 증명 저장소가 이 이름들도 받습니다 (`core/credentials/names.py`의 `RESEARCH`, 종류 `research`). 그래서 OS 키 보관함에 둘 수 있습니다. 연구 도구가 `os.environ` 대신 `core.credentials.get(이름)`으로 읽도록 바꾸는 일은 데이터소스 세션 몫입니다. `ECOS_API_KEY`, `SEC_EDGAR_USER_AGENT`도 같은 묶음입니다. 앱이 실행 중에 부르게 되면 그때 `routes.json` 행과 함께 1절 표로 옮깁니다 (D7 5.5절 "새 공급원 규칙").

| 이름 | 종류 | 담당 | 상용판 |
|---|---|---|---|
| `FRED_API_KEY` | 비밀 | 데이터소스 세션 (연구용) | 미정 |
| `ALPHAVANTAGE_API_KEY` | 비밀 | 데이터소스 세션 (연구용) | 미정 |
| `TIINGO_API_KEY` | 비밀 | 데이터소스 세션 (연구용) | 미정 |
| `CRYPTOPANIC_API_KEY` | 비밀 | 데이터소스 세션 (연구용) | 미정 |
| `CME_FEDWATCH_API_ID` | 비밀 | 데이터소스 세션 (연구용) | 미정 |
| `CME_FEDWATCH_API_SECRET` | 비밀 | 데이터소스 세션 (연구용) | 미정 |
| `TRADINGECONOMICS_API_KEY` | 비밀 | 데이터소스 세션 (연구용) | 미정 |
| `ECOS_API_KEY` | 비밀 | 데이터소스 세션 (연구용, 한국은행 ECOS) | 미정 |
| `SEC_EDGAR_USER_AGENT` | 연락처 문자열 (키 아님) | 데이터소스 세션 (연구용, SEC EDGAR) | 미정 |
| `ALPACA_API_KEY_ID` | 비밀 (키 ID) | 데이터소스 세션 (연구용, Alpaca) | 미정 |
| `ALPACA_API_SECRET_KEY` | 비밀 | 데이터소스 세션 (연구용, Alpaca) | 미정 |
| `MASSIVE_API_KEY` | 비밀 | 데이터소스 세션 (연구용, Massive) | 미정 |

- Alpaca·Massive 3개는 소유자 N0 승인 (2026-11-24 18:41 KST, 데이터소스 세션 원문 "N0 승인, Alpaca·Massive부터 진행하세요")으로 더했습니다. EODHD는 N1 답 전이라 넣지 않았습니다. 데이터소스 세션이 연구 도구의 `ENV_ONLY_KEYS`에서 `RESEARCH_KEYS`로 옮깁니다.

## 5. KEY-2 자격증명 저장소 설계

2026-11-17에 D7-G 승인 전 메모로 썼습니다. 소유자가 2026-11-18 14:15 KST에 D7-G를 승인했습니다 (원문 "그러면 D7-G의 방식대로 진행하겠습니다", handoff `MERGE_QUEUE.md`·`MASTER_WORK_DESIGN_2026-11-17.md` 맨 앞, 커밋 `762150c`). 이 설계대로 같은 브랜치에 구현했습니다 (`core/credentials/**`, `config.py`, `data/krx/kis_client.py`, `tests/credentials_acceptance.py`). 병합은 F21 뒤 대기열 (KEY-2 → KEY-3 → KEY-4 → KEY-5).

구현에서 정한 것 (PR #128): `config.py`는 3줄만 바꿉니다 (Nautilus 브리지 코드 지문의 입력이라서). `.env` 로딩은 `core.credentials.load_dotenv_for_development()`가 하고, 이 함수는 `core.app_identity.may_read_dotenv()` (OS 세션, PR #127로 main에 들어감)가 허용할 때만 `dotenv.load_dotenv`를 부릅니다. 시험 20여 개가 그 `dotenv.load_dotenv`를 막아 `.env`를 차단하는 방식은 그대로 통합니다. 그 호출이 더한 이름을 기록해 `.env` 값이 키 보관함보다 뒤에 옵니다. 설정 16개는 `core.credentials.read_setting()`이 환경변수에서 읽습니다. 키 보관함은 운영체제 기본 저장소 (Windows, macOS, SecretService, kwallet, libsecret)만 받고, `keyrings.alt` 같은 평문 백엔드는 거절합니다.

| 부품 | 내용 |
|---|---|
| `core/credentials/__init__.py` | `get(name)`, `set(name, value)`, `delete(name)`, `status(name)`, `read_setting(name)`, `load_dotenv_for_development()`. 찾는 순서: ① 프로세스 환경변수 → ② OS 키 보관함 (Python `keyring`, service `"QUANTGEN"`, OS 기본 저장소만) → ③ `.env` (개발판만). 개발판 판정은 `core/app_identity.may_read_dotenv()` (OS 세션, PR #127로 main에 있음) |
| `status(name)` | 값 대신 `{"name", "present", "source": "env"|"keyring"|"dotenv"|None}`만 돌려줌. 값은 어떤 반환·예외·로그에도 넣지 않음 |
| `core/credentials/names.py` | 1절의 비밀 10개 (`SECRETS`), 4절의 연구용 12개 (`RESEARCH`), 앱이 받아 두는 토큰 1개 (`TOKENS`: `kis_token`)와 종류 (`user_broker_key` 사용자 증권사 키 / `user_data_key` 사용자 데이터 키 / `user_ai_key` 사용자 AI 키 / `dev_only` 개발 전용 / `token` 토큰 / `research` 연구용). 이름 목록에 없는 이름은 `set` 거절 |
| `config._clean` | `core.credentials.read_setting(name)` 한 줄: 비밀 10개는 위 순서로, 설정 16개는 환경변수에서 (`.env`는 개발판에서 `load_dotenv_for_development()`가 미리 환경에 넣음) |
| KIS 토큰 캐시 | 키 보관함 `QUANTGEN`/`kis_token`을 먼저 읽고, 없거나 만료·깨졌으면 `~/.nextgen/kis_token.json`. 새 토큰은 키 보관함에 쓰고, 쓰기가 거절되면 키 보관함의 낡은 값을 지운 뒤 파일에 씀 (0600, 새로 만드는 폴더는 0700). **파일은 지우지 않음**: TRADEGEN이 같은 KIS 키로 같은 파일을 씀 (research_notes "QUANTGEN TRADEGEN split map"). 영향: QUANTGEN이 키 보관함에 새 토큰을 받으면 TRADEGEN 파일은 갱신되지 않아 TRADEGEN이 따로 토큰을 받을 수 있음 (하루 발급이 최대 2배). 앱에서 KIS 키를 바꾸면 키 보관함 토큰을 지우고 그 실행 동안 파일 토큰을 쓰지 않음. 다시 시작한 뒤에도 옛 키 토큰을 믿지 않도록, QUANTGEN이 쓰는 토큰에는 `key_id` (앱 키와 서버 주소의 SHA-256 앞 16자리, 키 값은 저장하지 않음)를 함께 적고 다르면 버림 (KEY-2/b). `key_id`가 없는 토큰 (TRADEGEN, 옛 QUANTGEN)은 전처럼 받음: 그런 파일이 옛 키로 받은 것이면 재시작 뒤 만료(약 24시간)까지 쓰일 수 있음. `key_id`는 앱 키와 서버 주소만 봄: 시크릿만 바꾸면 해당 없음 (그때는 KIS가 토큰을 거절하면 새로 받음). `key_id`는 발급에 쓴 키로 계산함. 파일 권한 맞추기는 링크를 따라가지 않고 (POSIX O_NOFOLLOW로 열어 같은 파일에 fchmod), 실패해도 읽기는 계속함. 임시 파일은 무작위 이름 (mkstemp). 토큰 파일이 링크면 링크는 두고 대상 파일을 바꿈. `KISClient.reload_credentials()`로 `ready`를 다시 읽음 (`ready`는 `KISClient.__init__`에서 한 번 정해짐) |
| `quantgen_cloud` 자리 | **만들지 않음** (D7-G에서는 게이트웨이 `remote.py`가 그 역할) |
| 의존성 | `keyring`을 `requirements.txt`, `pyproject.toml`에 버전 범위 고정 (공유 파일, 대기열 경유) |
| 시험 `tests/credentials_acceptance.py` | 메모리 keyring 백엔드만. `.env`·`~/.nextgen`을 읽지 않음 (`HOME`·`USERPROFILE`을 임시 폴더로). 값이 로그·예외 메시지·`status()`·`repr`에 나오지 않는지 확인. 찾는 순서 3단계, 공개판에서 `.env`를 읽지 않음, 이름 목록 밖 거절, keyring 없음 → 파일 대체 |
| CI | 첫 코드 PR이 `runtime-smoke.yml` 경로 목록에 `config.py`, `data/krx/**`, `core/credentials/**`를, 'Verify bounded source fixtures' 단계에 시험 모듈을 더함 |
| 미검증으로 남길 것 | Linux Secret Service 백엔드 동작, PyInstaller 묶음의 keyring 백엔드 (OS 세션 빌드 시험에 넣어 달라고 요청) |
| 공수 (추정) | 1.5~2 작업일 |

## 6. 출처

- 저장소 `origin/main` `5888d05`: `config.py:25-34, 52-287`, `core/markets.py:222`, `data/krx/kis_client.py:54, 174, 179-191, 206, 237`, `data/kis_stream.py:223`, `tools/provider_parity/parity_check.py:175-176, 243`, `.env.example` (이름만), `.github/workflows/*` (`${...}` 이름만).
- handoff `plans/2026-11-17/D7_ENV_STRUCTURE.md` (2026-11-17), `plans/2026-11-17/sessions/05_PAYMENTS_ACCOUNT_KEYS.md` 7절 작업 3.
- Notion "QUANTGEN 상업화 실행 분석서" `40e5c916fe0c815ba983dd4c4cc7992c` (D7 문서 인용, 이 세션에서 다시 열지 않음).
- Python keyring https://github.com/jaraco/keyring (D7 문서 2026-11-17 열람).
