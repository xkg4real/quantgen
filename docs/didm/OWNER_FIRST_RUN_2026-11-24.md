# 소유자 PC 첫 실행 안내 (D10, 2026-11-24)

- 작성: DATA_SOURCE 세션 (메인 지시 D10). **통합 PR ② 병합 뒤 main 기준**입니다 (DS-5b/5c Alpaca·Massive, D4 수집 현황, D6 EDGAR 과거 목록, D7 Kalshi 과거 일봉). FedWatch 파일 읽기 (D9)는 그 브랜치가 병합된 뒤 9단계를 씁니다.
- 모두 PowerShell, `QUANTGEN_didm` 폴더에서 실행합니다. 원래 `QUANTGEN` 폴더는 쓰지 않습니다 (커밋하지 않은 `qa/acceptance_results.json`이 있음).
- 키 값은 이 문서, 채팅, 화면 출력 어디에도 적지 않습니다. 명령은 키 **이름**만 씁니다. 돈이 드는 가입·결제는 하지 않습니다.
- 수집 자료는 `%LOCALAPPDATA%\QUANTGEN\didm\didm_store.sqlite`에만 쌓이고 저장소에 올라가지 않습니다.

## 한눈에

| 단계 | 할 일 | 걸리는 시간 | 실패해도 다음 단계 |
|---|---|---|---|
| 0 | main 받기 | 1분 | 안 됨 (먼저 해결) |
| 1 | Alpaca 무료 키 발급 | 5분 | 됨 (4단계 Alpaca 줄만 실패) |
| 2 | Massive 무료 키 발급 | 5분 | 됨 |
| 3 | 키 등록·확인 | 2분 | 됨 |
| 4 | 뉴스 수집 1회 | 1~2분 | 됨 |
| 5 | EDGAR 2015~2024 | 1분 안팎 | 됨 |
| 6 | Kalshi 과거 일봉 | 1~3분 | 됨 |
| 7 | 수집 현황 확인 | 수 초 | — |
| 8 | 결과 전달 | — | — |
| 9 | (선택, D9 병합 뒤) FedWatch 파일 | 수 초 | 됨 |

## 0. main 받기

```
cd <QUANTGEN_didm 폴더>
git fetch origin
git switch --detach origin/main
git log --oneline -1
```

- 기대: 마지막 줄이 메인이 알려 준 병합 커밋.
- 실패 때: `git switch`가 "would be overwritten"으로 멈추면 그 폴더에 고친 파일이 있다는 뜻입니다. 지우지 말고 파일 이름을 알려 주세요.

## 1. Alpaca 무료 키

1. alpaca.markets에서 무료 가입 (이메일 확인). 결제 정보는 넣지 않습니다.
2. 대시보드에서 **Paper** 계정을 고른 뒤 API Keys 메뉴에서 키를 만듭니다 (화면 이름은 바뀔 수 있음).
3. Key ID와 Secret 두 값이 나옵니다. Secret은 이때 한 번만 보이니 바로 3단계로.

## 2. Massive 무료 키

1. massive.com (옛 Polygon.io)에서 무료 (Basic) 가입.
2. 대시보드의 API Keys에서 키를 복사합니다.

## 3. 키 등록·확인

```
setx ALPACA_API_KEY_ID "<Key ID>"
setx ALPACA_API_SECRET_KEY "<Secret>"
setx MASSIVE_API_KEY "<Massive key>"
```

**새 PowerShell 창**을 열고 (setx는 열려 있던 창에 반영되지 않음) `QUANTGEN_didm`으로 가서:

```
python -m tools.didm.collect_daily --check-keys
```

- 기대: `ALPACA_API_KEY_ID: True`, `ALPACA_API_SECRET_KEY: True`, `MASSIVE_API_KEY: True`, `SEC_EDGAR_USER_AGENT: True` (값은 나오지 않음).
- 실패 때: False면 새 창을 열었는지, `setx` 이름 철자를 확인. 따옴표 안에 키 앞뒤 공백이 있어도 지워서 읽습니다.

## 4. 뉴스 수집 1회 (DS-5b/5c)

```
python -m tools.didm.collect_daily --data-dir "$env:LOCALAPPDATA\QUANTGEN\didm" --no-gdelt --alpaca-news AAPL --massive-news AAPL --news-start 2026-11-01 --news-max-pages 2
```

- 기대 (숫자는 다름):
  - `Alpaca news AAPL: pages 1 (complete True), articles 37, first 2026-11-01..., last 2026-11-24..., new 37`
  - `Massive news AAPL: pages 2 (complete False), articles 200, with insights 180, first ..., last ..., new 200`
- Massive는 무료 한도 (분당 5회) 때문에 쪽마다 12.5초씩 기다립니다. 멈춘 것이 아닙니다.
- `complete False` = 쪽 상한 (2쪽)에 걸림. 오류 아님.
- 실패 때 (한 줄로 나옴, 키 값은 가려짐):

| 출력 | 뜻 | 할 일 |
|---|---|---|
| `Alpaca news failed: SourceError: Alpaca news: HTTP 403 (... not permit ...)` | 무료 계정이 뉴스 조회를 막음 | 그 줄 그대로 전달 → 유료 단계 판단 근거로 기록 |
| `... HTTP 401` | 키가 틀림 | 1·3단계 다시 (Paper 키인지 확인) |
| `... failed: MissingKey: ... is not set` | 키 이름이 안 읽힘 | 3단계 새 창 확인 |
| `Massive news failed: SourceError: Massive news: HTTP 403 (...)` | 무료 플랜 범위 밖 | 그대로 전달 |
| `... HTTP 429` | 호출 한도 초과 | 1분 뒤 다시 |

## 5. EDGAR 2015~2024 (D6)

```
python -m tools.didm.collect_daily --data-dir "$env:LOCALAPPDATA\QUANTGEN\didm" --no-gdelt --edgar-history 320193 --edgar-from 2015-01-01 --edgar-to 2024-12-31
```

- 기대: `EDGAR history CIK 320193 2015-01-01..2024-12-31: files 1/1 (complete True), filings N, first 2015-..., last 2024-..., new N` (기본 서식 8-K·6-K·10-Q·10-K만).
- `complete False` = 과거 파일 상한 (10)에 걸림 → `--edgar-max-files 30`을 붙여 다시.
- 실패 때: `HTTP 403` = SEC가 User-Agent를 거부 (`SEC_EDGAR_USER_AGENT`가 "단체명 연락처" 형태인지). `FilingError: ... filings, index says ...` = SEC 파일 건수가 색인과 다름 → 그 줄 전달.

## 6. Kalshi 과거 일봉 (D7)

```
python -m tools.didm.collect_daily --data-dir "$env:LOCALAPPDATA\QUANTGEN\didm" --no-gdelt --kalshi-history KXFED --kalshi-from 2021-07-01 --kalshi-to 2024-12-31 --kalshi-max-markets 20
```

- 기대: `Kalshi history KXFED 2021-07-01..2024-12-31: markets N (pages P, complete True, capped at 20), with candles M, candles C, first ..., last ..., new C`.
- 이 단계는 **확인용**입니다: Kalshi가 오래된 시장의 일봉을 지금 API로 주는지, 마감 시각 필터를 받는지 아직 공식 문서로 확인하지 못했습니다.

| 출력 | 뜻 |
|---|---|
| `markets 0` | 그 기간에 마감한 시장을 API가 주지 않음 (오래된 시장은 별도 경로일 수 있음) → 전달 |
| `with candles 0` | 시장 목록은 오지만 일봉이 비어 있음 → 전달 |
| `Kalshi history failed: SourceError: Kalshi /markets: HTTP 400` | 필터 이름이 다름 → 전달 |
| `... repeated cursor` | 같은 쪽이 반복 → 전달 (멈춤 방지로 끊은 것) |

## 7. 수집 현황 확인 (D4)

```
python -m tools.didm.collection_status --data-dir "$env:LOCALAPPDATA\QUANTGEN\didm"
```

- 기대: 공급원·종류별 한 줄, 예 `sec-edgar / filing: items N (versions N), valid 2015-..2024-.., received 2026-11-..2026-11-.. on 1 days, missing 0 days, sample years with data 10/10`.
- 읽기만 합니다 (저장소를 바꾸지 않음). 본문·키는 나오지 않습니다.
- 실패 때: `no store at ...` = 4~6단계가 한 번도 저장하지 않음.

## 8. 결과 전달

4~7단계 출력 줄을 그대로 붙여 주세요 (키 값은 출력되지 않으므로 그대로 붙여도 됩니다). DATA_SOURCE가 `COLLECTION_STATUS_GUIDE_2026-11-24.md` 2절 표와 `NEW_SOURCES_PLAN_2026-11-24.md`를 실제 결과로 고칩니다.

## 9. (선택, D9 병합 뒤) FedWatch 파일

CME FedWatch 확률을 CSV로 옮겨 적은 파일이 있을 때만:

```
python -I -m tools.didm.collect_daily --data-dir "$env:LOCALAPPDATA\QUANTGEN\didm" --no-gdelt --fedwatch-file <CSV 경로>
```

- 열: `trade_date,meeting_date,lower_bp,upper_bp,probability` (+ 선택 `published_at,current_lower_bp,current_upper_bp`). 자세한 형식은 `DS4C_FEDWATCH_DESIGN_2026-11-24.md` 8절.
- 기대: `FedWatch file x.csv: trade days N (...), meeting rows M, refused days 0, new M`. 거부된 날은 `FedWatch refused <날짜>: <이유>`로 나옵니다.
- 가입·이력 저장 허용 여부 (OA-31)는 별도 질문입니다. 법률 자문이 아닙니다.
