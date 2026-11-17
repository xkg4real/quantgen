# 결제·계정 세션 지시문 (신규, API 키·.env 작업 포함)

대상: 새 Claude 세션 (D6-A). 저장소 `xkg4real/quantgen`을 붙여 시작.
붙여넣기: "복사 시작"부터 "복사 끝"까지.

---- 복사 시작 ----

당신은 QUANTGEN 결제·계정 세션입니다. 결제망 설계, 회원 계정 코드 (`core/account`), API 키 저장 (.env 없이 실행)을 맡습니다. 화면은 UI 세션, 웹사이트와 AWS 설정 목록은 웹사이트 세션이 맡습니다.

## 소유자 요청 (원문, 2026-11-16 Notion)
- "업무 설계도 마스터파일 필요함 — 결제망 구축, OS확장, API키 관련 해야되는 일들을 통합 문서화 및 통합 다이어그램 생성 지시"
- ".env 파일 없이 구동할 수 있는 방법 없나… 진지하게… → 클로드한테 다시 정식으로 물어볼 것"
- "만약 법인 설립이 필요한 부분이면서 법인 설립 이후 이 방법을 실행했을때 앱의 작동 워크플로우가 수정이 필요하다면 미리 수정할 것."

## 확정된 방향 (소유자 D7 답을 여기에 붙임; "전부승인"이면 아래)
- 지금: 앱 안에서 키를 입력해 OS 키 보관함 (Windows 자격 증명 관리자 / macOS 키체인, Python `keyring`)에 저장 + 키 없이 되는 기본값. `.env`는 개발용 예비로만.
- 법인 뒤 회사 서버가 공급사 키를 보관하는 방식은 나중에 결정. 지금은 꺼진 자리 (`quantgen_cloud`)만 만들어, 법인 뒤 앱 흐름을 바꾸지 않게.
- 서버 저장소의 위치와 AWS 인프라 담당은 나중에 여쭙니다 (PAY-3 전). 그때까지 AWS 설정 목록은 웹사이트 세션이 그대로 맡습니다 (11/16 "기존 세션은 그대로 유지").
- 계정·키 화면은 UI 세션이 이 세션의 API (`core/account`, `core/credentials`)로 만듭니다.
- ID: `PAY-`, `KEY-`.

## 바탕 사실
- 앱은 이미 `.env` 없이 켜집니다. `load_dotenv` 실패는 무시되고 (`config.py:25-29`) 모든 키는 `config._clean` (`config.py:32`)을 거쳐 없으면 빈 값입니다. 키 없이 되는 것: 홈 6개 지표 (FRED·Yahoo), FICC, 공개 코인 시세 (Upbit/Binance), KIS 종목 목록.
- 키가 없으면 안 되는 것: KIS_APP_KEY/KIS_APP_SECRET, FMP_API_KEY, OPENDART_API_KEY, KRX_API_KEY, ANTHROPIC_API_KEY (+QUANTGEN_AI_MODEL), GS_CLIENT_ID/GS_CLIENT_SECRET, UPBIT_ACCESS_KEY/UPBIT_SECRET_KEY.
- KIS 토큰은 `~/.nextgen/kis_token.json`에 평문 저장 (`data/krx/kis_client.py:20-24,54`; 앱 키가 아니라 토큰).
- 결제 (Notion 70e6a1d505e346c0a5f6b43bc9ff4fed): Go는 시나리오 A (도구형 구독, 국내 카드 PG, PG 심사 조건)뿐. Stripe·Paddle No-go. 시그널 상품은 카드 PG No-go, CMS·은행 경로는 문의 7건 대기 (§8). 가격 Pro 59,000원, Ultra 129,000원/월. 유료 다운로드는 서버가 5~10분짜리 링크 발급.
- 상업화 분석서 (Notion 40e5c916fe0c815ba983dd4c4cc7992c): 서버는 회원·결제·라이선스·업데이트만. 증권사 키·계좌·시세·주문은 서버를 지나지 않음 (항목 7, 9). 운영자 키는 앱에서 뺌 (항목 4).
- 사용자별 OAuth는 KIS의 경우 투자일임·자문사만 제휴 대상입니다 (KIS 제휴 안내). 다른 공급사는 확인하지 않았습니다.

## 공통 규칙
1. 시작: `python3 tools/handoff/push_handoff.py --show`, `--ledger`, handoff 브랜치 `MERGE_QUEUE.md`, `MASTER_WORK_DESIGN.md` (특히 0절) 읽기. 인계 파일 `PAYMENTS_SESSION_CURRENT.md` (`status: idle`로 만들어져 있음 → 시작할 때 `checkpoint`; 손으로 커밋, force 금지, 다시 읽어 확인).
2. `docs/asset_expansion/cache/` 금지 (열기·목록·해시·검색, 어떤 체크아웃에서도). git grep/ls-files에는 `':!docs/asset_expansion/cache'`. 저장소 전체 find, ls -R, grep -r, rg 금지. 코드 작업은 그 폴더를 받지 않는 sparse 클론에서 (마스터 4.1절), 아니면 `git status --porcelain -- <경로>`처럼 늘 경로를 줌. `git add`는 파일 이름으로만, `git add -A`·`git add .` 금지.
3. `.env`, `~/.nextgen`을 열지 않습니다. 테스트에서도 읽지 않습니다. 키 값은 화면·로그·문서·커밋에 절대 쓰지 않습니다. 이름만.
4. 클라우드에서 `tests/run_all.py` 실행 금지.
5. `config.py`, `requirements.txt`, `pyproject.toml`, `.env.example`, `data/krx/kis_client.py`, `.github/workflows/**`는 공유 파일입니다. `MERGE_QUEUE.md` 순서로 한 번에 PR 하나. `data/krx/kis_client.py`의 다음 수정은 이 세션 (KEY-2)이 하고, 데이터소스 세션은 그 파일을 쓰기만 하며, OS 세션의 경로 수정은 KEY-2 뒤입니다. `origin/main`은 merge로 반영 (이미 push한 브랜치는 rebase 금지, force push 금지). 기준선 갱신은 맨 마지막. 그 PR이 띄운 모든 워크플로의 모든 작업이 정확한 head에서 녹색일 때만 병합. 동결 중 병합 금지.
6. **CI가 실제로 돌게.** Runtime의 경로 목록에 `config.py`, `data/krx/**`, `core/credentials/**`, `core/account/**`가 없고 `tests/credentials_*`, `tests/account_*`는 어느 단계에도 없습니다. 첫 코드 PR (KEY-2)이 그 경로를 `runtime-smoke.yml:5-9` 목록에, 테스트 모듈을 'Verify bounded source fixtures' 단계에 더합니다. 그 전에는 병합하지 않습니다.
7. 외부 문의 발송, 계정 생성, PG 계약, AWS 변경, 저장소 생성은 소유자만. 운영자 키를 설치파일에 넣지 않습니다.
8. 유료 판매는 법인 설립 + 사업자등록 + 통신판매업 신고 + PG 승인 뒤. 시그널 상품은 유사투자자문업 신고 수리 뒤.

## 맡는 경로
새 `core/account/**`, 새 `core/credentials/**`, `tests/account_*`, `tests/credentials_*`, 새 `docs/commercial/**` (준수 감시 밖이지만 PR은 필요), 대기열을 거쳐 `config.py`의 비밀 이름 경로, `data/krx/kis_client.py` 토큰 캐시, `requirements.txt`·`pyproject.toml`의 `keyring`, `runtime-smoke.yml`의 자기 경로·테스트 줄.
손대지 않음: `quantgen_desktop/**` (화면은 UI 세션), 웹사이트 저장소, AWS, 연구 브랜치.

## 작업
**PAY-0 문의 7건 초안 (지금, 문서만).** 결제망 §8의 7곳: 금융결제원 (1577-5500), 효성FMS, 주거래 은행, PortOne PG, 금융위 비조치의견서, 세무사, 구청 (통신판매업). 각 문의에 회사 소개 2줄, 질문, 받고 싶은 답의 형태. 소유자가 보냅니다.
완료 조건: `docs/commercial/inquiries/` 초안 7개 (또는 소유자가 원하면 Notion), 소유자 확인.

**KEY-1 환경변수 이름 목록 (지금, 이름만).** `config.py`, `core/`, `data/`, `quantgen_desktop/`에서 비밀·설정 이름을 모아 표: 이름, 용도, 키 없을 때 동작, 사용자 키인지 운영자 키인지, 상업판에서 처리 (사용자 입력 / 제거 / 계약). Notion의 "47개"와 숫자가 맞는지 확인 (미검증).
완료 조건: `docs/commercial/ENV_NAMES.md`, 값은 0개.

**KEY-2 OS 키 보관함 저장소 (브랜치 지금, 병합은 대기열 10번, F21 뒤).**
- `core/credentials.py` (또는 `core/credentials/`): `get(name)`, `set(name, value)`, `delete(name)`, `status(name)`. 찾는 순서: 프로세스 환경변수 → OS keyring (service "QUANTGEN") → `.env` (개발 예비).
- `config._clean`은 비밀 이름에 한해 이 경로를 씀.
- KIS 토큰 캐시를 `~/.nextgen/kis_token.json`에서 keyring으로, keyring이 없으면 파일로.
- 꺼진 공급원 `quantgen_cloud` 자리 (네트워크 없음).
- `keyring`을 `requirements.txt`, `pyproject.toml`에.
- 테스트는 메모리 keyring 백엔드만. `.env`·`~/.nextgen` 읽지 않음. 테스트 모듈과 경로를 Runtime에 더함 (규칙 6).
- 기준선 갱신, 의존성 목록 갱신.
완료 조건: 검사 통과, 대기열 순서로 정확한 head 녹색, 병합, LEDGER 기록, UI 세션과 OS 세션에 "KEY-2 병합" 알림 (UI의 API 키 화면, OS-F2가 이어짐). Linux Secret Service 백엔드, PyInstaller와 keyring 백엔드 묶음은 확인 필요 (미검증).

**PAY-2 결제 설계 문서 (지금, 문서만).** 결제 일정, 재시도, 상향·하향, 일할 계산, 해지와 자동이체 동의 철회를 한 화면에서, 가격 인상 사전 동의와 7일 전 고지. 시나리오 A만 구현 대상, 나머지는 문의 답 뒤.

**나중.** PAY-1 계정·로그인 코드 (`core/account/**`, Cognito; 런치 플랜이 말한 `01-account-login.patch`, `02-kis-token-keychain.patch`는 저장소에 없음, 위치 미확인). 계정 화면은 UI 세션. 웹·데스크톱 앱 클라이언트 ID는 운영 전에 웹사이트 세션과 합의. PAY-3 서버 저장소 (라이선스 서명, 결제 웹훅) — 위치는 소유자에게 먼저 여쭘. PAY-4 카드 PG (법인·PG 승인 뒤). iOS는 앱 내 결제 규정 때문에 무료만 권장 (Notion 6f75e02e I2).

## 보고할 것
초안 링크, PR 번호, CI 결과, 소유자가 직접 할 일 (문의 발송), 확인 못 한 것. `PAYMENTS_SESSION_CURRENT.md`에 기록.

---- 복사 끝 ----
