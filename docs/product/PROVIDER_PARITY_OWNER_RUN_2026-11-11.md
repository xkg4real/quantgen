# 공급사 대조(⑤-2) 소유자 실행 안내

작성 2026-11-11(KST) · 대상: QUANTGEN 소유자, Windows 11 · 작성: Claude Code

- 근거: 연구 브랜치 `claude/amazing-gauss-tdiguu`의 스펙 `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md` 10.5·10.5.1·10.5.2와 소유자 결정 U5·P-D2~P-D9(2026-11-04). 이 문서와 스펙이 다르면 스펙을 따릅니다.
- 도구: [`tools/provider_parity/parity_check.py`](../../tools/provider_parity/parity_check.py). 영문 상세 설명은 [도구 안내서](../../tools/provider_parity/README.md)에 있습니다.
- 순서에서의 자리: Step 7A(2026-11-04 완료) → **이 단계** → Step 8 파일럿 1 → Step 9 파일럿 2 → Step 10 마감 → 병합.

> **아직 시작하지 마십시오.** 스펙 10.5는 도구의 커밋과 sha256을 소유자 판정으로 고정한 뒤에 첫 실행을 하도록 정합니다. 2026-11-11 현재 그 판정이 없고, 스펙이 이름 붙인 브랜치 `claude/provider-parity-5-2`에는 2026-11-05의 미완성본(`777fc5b`)이 있습니다. Claude가 5~7단계에 넣을 세 줄(도구 브랜치, 도구 커밋, 도구 sha256)을 값이 채워진 채로 보내 드리면 그때 시작합니다.

## 1. 이 단계가 하는 일

파일럿이 읽는 고정 파일 세 개(SPY 가격, DGS3MO 금리, BTC-USD 가격)를 다른 공급사 아홉 곳에서 새로 받은 같은 시계열과 소유자 PC에서 대조합니다. 시계열마다 나오는 판정(PASS, FAIL, WITHHELD)이 파일럿 1(Step 8)과 파일럿 2(Step 9)를 시작해도 되는지 정하는 관문입니다.

## 2. 시작 전에 필요한 것

| 필요한 것 | 내용 |
| --- | --- |
| 선행 단계 | Step 7A가 7A.5까지 끝나 있어야 합니다(2026-11-04 완료). |
| Claude가 보낸 세 줄 | `$branch = "..."`, `$fixed = "..."`, `$sha = "..."`. 소유자 판정으로 고정된 도구 브랜치, 도구 커밋(40자), 도구 파일 sha256(64자)입니다. 2026-11-11에 검토를 마친 도구 파일의 sha256은 `d651795e4b4776d096601a43989c7f45c375ae120b75a64179432f469d2daca1`입니다. Claude가 보낸 값이 이와 다르면 그 뒤에 도구가 바뀐 것이니, 12단계는 Claude가 보낸 값으로 맞추고 바뀐 이유를 물어보십시오. |
| 연구 클론 | Step 7A를 실행한 QUANTGEN 폴더입니다. 브랜치는 `claude/amazing-gauss-tdiguu` 그대로 둡니다. 도구는 이 폴더를 읽기만 합니다. 이 폴더에 대해서는 상태를 읽는 git 줄(2, 3, 8, 34단계)만 실행하고, 그 밖에는 아무것도 실행하지 않습니다. |
| 도구 클론 | 9단계가 `%LOCALAPPDATA%\quantgen\pp_clone`에 새로 만듭니다. 7A의 `py313`, `ntvenv`가 있는 그 폴더 옆입니다. 내려받는 양은 100MB 안팎으로 예상합니다. |
| 출력 폴더 | 도구가 `%LOCALAPPDATA%\quantgen\provider_parity` 아래에 만듭니다. 미리 만들지 않습니다. OneDrive 안이나 git 폴더 안은 도구가 거부합니다. |
| `.env` 변수 이름 | 연구 클론의 `.env`에 `FMP_API_KEY`(SPY의 fmp), `KIS_APP_KEY`와 `KIS_APP_SECRET`(SPY의 kis)가 있어야 합니다. `KIS_BASE_URL`은 있으면 읽고, 없어도 됩니다. 나머지 일곱 공급사는 키가 없습니다. 값은 이 문서, 채팅, PowerShell 창 어디에도 적지 않습니다. `.env`를 복사하지도 않습니다. |
| 파이썬 | 7A에서 `python -B -m tools.nautilus.runner --check-env`와 `python tests/run_all.py`를 실행한 그 `python`입니다. 가상환경을 켜지 않습니다. `py313`이나 `ntvenv`의 파이썬은 쓰지 않습니다(7A의 방화벽 규칙이 그 파이썬의 외부 연결을 막습니다). |
| 인터넷 | 공급사 아홉 곳으로 나가는 연결이 필요합니다. |
| 함께 돌리지 않는 것 | 파일럿, 전체 시험(`python tests/run_all.py`), 동결 연구 판독이 도는 동안에는 실행하지 않습니다. |
| 걸리는 시간 | 오류가 없으면 15~20분입니다. 구역별 시간은 3절에 있습니다. |

`kis` 수신은 앱의 KIS 클라이언트를 쓰므로 `~/.nextgen/kis_token.json`(KIS 접근 토큰)을 읽고, 토큰이 새로 발급되면 그 파일을 다시 씁니다. `~/.nextgen`의 다른 파일은 건드리지 않습니다.

## 3. 순서

- 창은 Step 7A의 7A.2와 같은 일반 PowerShell 창입니다(관리자 권한 아님). 명령 프롬프트(CMD)가 아닙니다. 시작 메뉴에서 "PowerShell"을 찾아 "Windows PowerShell"을 엽니다.
- 회색 상자의 줄을 한 번에 한 줄씩 복사해 붙여넣고 Enter를 누릅니다. 줄이 길어 화면에서 접혀 보여도 한 줄입니다.
- 직접 고치는 곳은 1단계의 `<...>` 한 곳뿐입니다. 5~7단계는 Claude가 보낸 세 줄로 대신합니다.
- 각 단계의 "화면"과 다르게 나오면 다음 단계로 가지 않고 6절을 봅니다.
- 키 값을 창에 치지 않습니다. 도구가 `.env`에서 이름으로 읽습니다.
- 창을 닫으면 `$rc`와 `$q`가 사라집니다. 다시 열었을 때는 7절을 봅니다.

### 가. 준비 (1~14단계, 약 5~8분)

**1.** 연구 클론 폴더를 변수에 넣습니다. 따옴표 안의 `<...>`를 연구 클론 폴더의 전체 경로로 바꿉니다. 파일 탐색기에서 그 폴더를 열고 주소 표시줄을 누르면 경로가 보입니다.

```powershell
$rc = "<연구 클론 폴더의 전체 경로>"
```

화면: 아무것도 나오지 않습니다. 시간: 바로.

**2.** 연구 클론의 브랜치를 확인합니다.

```powershell
git -C $rc branch --show-current
```

화면: `claude/amazing-gauss-tdiguu` 한 줄. 시간: 1초 안.

**3.** 연구 클론에 바뀐 파일이 없는지 봅니다.

```powershell
git -C $rc status --porcelain
```

화면: 아무 줄도 나오지 않습니다. 줄이 나오면 그대로 복사해 두고 계속합니다. 34단계에서 같은 줄이 나와야 하고, 그 줄들을 Claude에게도 보냅니다. 시간: 1~5초.

**4.** 7A.2에서 쓴 `quantgen` 폴더를 변수에 넣습니다(7A.2와 같은 줄입니다).

```powershell
$q = Join-Path $env:LOCALAPPDATA "quantgen"
```

화면: 아무것도 나오지 않습니다. 시간: 바로.

**5.** Claude가 보낸 도구 브랜치 줄을 붙여넣습니다.

```powershell
$branch = "<Claude가 보낸 도구 브랜치 이름>"
```

화면: 아무것도 나오지 않습니다. 시간: 바로.

**6.** Claude가 보낸 도구 커밋 줄을 붙여넣습니다.

```powershell
$fixed = "<Claude가 보낸 도구 커밋 40자>"
```

화면: 아무것도 나오지 않습니다. 시간: 바로.

**7.** Claude가 보낸 도구 sha256 줄을 붙여넣습니다.

```powershell
$sha = "<Claude가 보낸 도구 sha256 64자>"
```

화면: 아무것도 나오지 않습니다. 시간: 바로.

**8.** 연구 클론이 쓰는 GitHub 주소를 읽습니다.

```powershell
$origin = git -C $rc remote get-url origin
```

화면: 아무것도 나오지 않습니다. 시간: 1초 안.

**9.** 도구 브랜치만 새 폴더에 내려받습니다.

```powershell
git clone --branch $branch --single-branch $origin "$q\pp_clone"
```

화면: `Cloning into '...\quantgen\pp_clone'...`로 시작하는 진행 줄들이 나오고 프롬프트가 돌아옵니다. `fatal:`로 시작하는 줄이 없어야 합니다. GitHub 로그인 창이 뜨면 7A.3에서 올릴 때 쓴 계정으로 로그인합니다. 시간: 1~3분(인터넷 속도에 따라 다릅니다).

**10.** 도구 클론 폴더로 들어갑니다. 여기부터 33단계까지 모든 줄을 이 폴더에서 실행합니다.

```powershell
cd "$q\pp_clone"
```

화면: 프롬프트가 `...\quantgen\pp_clone>`로 끝납니다. 시간: 바로.

**11.** 판정이 고정한 커밋이 이 클론에 들어 있는지 봅니다.

```powershell
git branch --contains $fixed
```

화면: `* `로 시작하고 도구 브랜치 이름이 적힌 한 줄. `error:`로 시작하는 줄이 나오거나 아무 줄도 없으면 멈춥니다. 시간: 1초 안.

**12.** 도구 파일이 판정이 고정한 바이트 그대로인지 봅니다.

```powershell
python -B -c "import hashlib,sys; h=hashlib.sha256(open('tools/provider_parity/parity_check.py','rb').read()).hexdigest(); print(h); print('sha256 ok' if h==sys.argv[1] else 'sha256 DIFFERENT')" $sha
```

화면: 64자 한 줄과 `sha256 ok` 한 줄. `sha256 DIFFERENT`가 나오면 멈추고 두 줄을 Claude에게 보냅니다. 시간: 1초 안.

**13.** 이 `python`이 앱이 쓰는 파이썬인지, 필요한 패키지가 있는지 봅니다.

```powershell
python -B -c "import sys, numpy, pandas, requests, yfinance; print(sys.version.split()[0], sys.executable)"
```

화면: `3.13.x`와 파이썬 경로가 적힌 한 줄. 경로에 `quantgen\py313`이나 `ntvenv`가 들어 있으면 안 됩니다. `ModuleNotFoundError`가 나오면 멈춥니다. 시간: 2~5초.

**14.** 도구 자체 점검을 돌립니다. 인터넷을 쓰지 않고 파일도 쓰지 않습니다.

```powershell
python -B -m tools.provider_parity.parity_check selftest
```

화면: 마지막 줄이 `SELFTEST PASS checks=11 failures=0`. 시간: 1~3초.

### 나. 수신 (15~23단계, 약 3~6분)

공급사마다 한 번씩, 모두 아홉 번 받습니다. 수신은 판정이 아니므로 실패해도 기록 실행으로 세지 않습니다. 실패한 수신은 아무 폴더도 남기지 않아서, 원인을 고친 뒤 같은 줄을 그대로 다시 실행할 수 있습니다.

성공하면 마지막 두 줄이 아래 모양입니다(`<...>` 자리에는 실제 행 수와 날짜가 나옵니다).

```text
rows <행 수>, first <첫 날짜>, last <끝 날짜>, weekend dates 0
FETCH spy fmp OK exit=0 csv=C:\Users\...\AppData\Local\quantgen\provider_parity\fetch1-spy-fmp\spy_fmp.csv
```

BTC-USD 세 번은 첫 줄의 끝이 `weekend dates <수>` 대신 `missing days <수>`입니다.

**15.** SPY, 공급사 fmp(키 `FMP_API_KEY`).

```powershell
python -B -m tools.provider_parity.parity_check fetch --series spy --provider fmp --start 2004-12-01 --end 2026-09-25 --out "$q\provider_parity\fetch1-spy-fmp" --env-file "$rc\.env"
```

화면: 마지막 줄 `FETCH spy fmp OK exit=0 csv=...`. 시간: 5~30초(요청 1번).

**16.** SPY, 공급사 kis(키 `KIS_APP_KEY`, `KIS_APP_SECRET`).

```powershell
python -B -m tools.provider_parity.parity_check fetch --series spy --provider kis --start 2004-12-01 --end 2026-09-25 --out "$q\provider_parity\fetch1-spy-kis" --env-file "$rc\.env"
```

화면: 마지막 줄 `FETCH spy kis OK exit=0 csv=...`. 시간: 20초~1분(한 번에 100거래일씩 약 56~58번 요청).

**17.** SPY, 공급사 yahoo_now(키 없음).

```powershell
python -B -m tools.provider_parity.parity_check fetch --series spy --provider yahoo_now --start 2004-12-01 --end 2026-09-25 --out "$q\provider_parity\fetch1-spy-yahoo_now"
```

화면: 마지막 줄 `FETCH spy yahoo_now OK exit=0 csv=...`. 시간: 5~30초.

**18.** DGS3MO(도구에서는 `rf`), 공급사 treasury.

```powershell
python -B -m tools.provider_parity.parity_check fetch --series rf --provider treasury --start 2004-12-01 --end 2026-09-25 --out "$q\provider_parity\fetch1-rf-treasury"
```

화면: 마지막 줄 `FETCH rf treasury OK exit=0 csv=...`. 시간: 15초~1분(연도별 파일 23번 요청, 요청 사이 0.35초 대기).

**19.** DGS3MO, 공급사 h15(선택 공급사).

```powershell
python -B -m tools.provider_parity.parity_check fetch --series rf --provider h15 --start 2004-12-01 --end 2026-09-25 --out "$q\provider_parity\fetch1-rf-h15"
```

화면: 마지막 줄 `FETCH rf h15 OK exit=0 csv=...`. 시간: 5~30초.

**20.** DGS3MO, 공급사 fred_now.

```powershell
python -B -m tools.provider_parity.parity_check fetch --series rf --provider fred_now --start 2004-12-01 --end 2026-09-25 --out "$q\provider_parity\fetch1-rf-fred_now"
```

화면: 마지막 줄 `FETCH rf fred_now OK exit=0 csv=...`. 시간: 5~30초.

**21.** BTC-USD(도구에서는 `btc`), 공급사 coinbase.

```powershell
python -B -m tools.provider_parity.parity_check fetch --series btc --provider coinbase --start 2014-09-17 --end 2026-09-25 --out "$q\provider_parity\fetch1-btc-coinbase"
```

화면: 마지막 줄 `FETCH btc coinbase OK exit=0 csv=...`. 시간: 10~40초(300일씩 15번 요청).

**22.** BTC-USD, 공급사 bitstamp(선택 공급사).

```powershell
python -B -m tools.provider_parity.parity_check fetch --series btc --provider bitstamp --start 2014-09-17 --end 2026-09-25 --out "$q\provider_parity\fetch1-btc-bitstamp"
```

화면: 마지막 줄 `FETCH btc bitstamp OK exit=0 csv=...`. 시간: 5~30초(1000일씩 5번 요청).

**23.** BTC-USD, 공급사 binance(진단용).

```powershell
python -B -m tools.provider_parity.parity_check fetch --series btc --provider binance --start 2014-09-17 --end 2026-09-25 --out "$q\provider_parity\fetch1-btc-binance"
```

화면: 마지막 줄 `FETCH btc binance OK exit=0 csv=...`. `first`가 2017-08-17 무렵이어도 정상입니다(바이낸스의 BTCUSDT가 그때 시작합니다). 시간: 5~30초(1000일씩 5번 요청).

**멈춤 지점.** 아홉 번이 모두 아래 네 가지를 만족하면 바로 다 구역으로 갑니다. 하나라도 아니면 여기서 멈추고, 아홉 번의 마지막 두 줄씩(18줄)을 Claude에게 보낸 뒤 답을 기다립니다. 그때는 Claude가 상황에 맞는 대조 줄을 다시 써 드립니다. 대조는 시계열마다 첫 실행이 기록으로 남으므로, 수신이 정리되기 전에 대조를 돌리지 않습니다.

- 마지막 줄이 `FETCH ... OK exit=0`입니다.
- SPY와 rf 여섯 번은 `weekend dates 0`입니다. 0이 아니면 그 공급사가 날짜를 다르게 붙인 것입니다.
- `first`: SPY 세 번은 2004-12-01이거나 그 전, rf 세 번은 2004-11-05이거나 그 전, coinbase와 bitstamp는 2016-01-01이거나 그 전입니다. binance는 따지지 않습니다.
- `last`: 아홉 번 모두 2026-09-25이거나 그 뒤입니다.

BTC-USD의 `missing days`는 0이 아니어도 계속합니다(대조가 그 날짜들을 경고로 적습니다).

### 다. 대조와 요약 복사 (24~29단계, 약 1~2분)

대조는 인터넷을 쓰지 않습니다. 시계열마다 **한 번만** 돌립니다. PASS, FAIL, WITHHELD로 끝난 첫 실행이 그 시계열의 기록 실행이고, 다시 돌린 결과는 소유자 판정을 `results/RULINGS.md`에 적은 뒤에만 인정됩니다. REFUSED나 ERROR로 끝난 대조는 아무것도 쓰지 않으며 실행으로 세지 않으므로, 원인을 고친 뒤 같은 줄을 다시 실행할 수 있습니다.

**24.** SPY를 대조합니다.

```powershell
python -B -m tools.provider_parity.parity_check compare --series spy --table "$rc\docs\nautilus_bridge\registration\pilot1_E1_spy.json" --repo $rc --pair fmp "$q\provider_parity\fetch1-spy-fmp\spy_fmp.csv" --pair kis "$q\provider_parity\fetch1-spy-kis\spy_kis.csv" --pair yahoo_now "$q\provider_parity\fetch1-spy-yahoo_now\spy_yahoo_now.csv" --out "$q\provider_parity\compare1-spy" --owner-run
```

화면: 마지막 줄 `PARITY spy PASS exit=0 summary=...\compare1-spy\summary.json`. PASS 자리에 FAIL이나 WITHHELD가 나와도 25단계로 갑니다(4절). 시간: 2~10초.

**25.** SPY 요약을 도구 클론의 `results` 폴더로 복사합니다. 24단계가 PASS, FAIL, WITHHELD 가운데 하나로 끝났을 때만 실행합니다.

```powershell
python -B -c "import json,pathlib,shutil,sys; s=pathlib.Path(sys.argv[1]); d=pathlib.Path('results',json.loads(s.read_text(encoding='utf-8'))['run_id']); d.mkdir(parents=True); shutil.copyfile(s,d/'summary.json'); print((d/'summary.json').as_posix())" "$q\provider_parity\compare1-spy\summary.json"
```

화면: `results/PP-<날짜와 시각>Z-spy/summary.json` 한 줄. 시간: 1초 안.

**26.** DGS3MO를 대조합니다(SPY와 같은 표를 씁니다).

```powershell
python -B -m tools.provider_parity.parity_check compare --series rf --table "$rc\docs\nautilus_bridge\registration\pilot1_E1_spy.json" --repo $rc --pair treasury "$q\provider_parity\fetch1-rf-treasury\rf_treasury.csv" --pair fred_now "$q\provider_parity\fetch1-rf-fred_now\rf_fred_now.csv" --pair h15 "$q\provider_parity\fetch1-rf-h15\rf_h15.csv" --out "$q\provider_parity\compare1-rf" --owner-run
```

화면: 마지막 줄 `PARITY rf PASS exit=0 summary=...\compare1-rf\summary.json`. 시간: 2~10초.

**27.** DGS3MO 요약을 복사합니다. 26단계가 PASS, FAIL, WITHHELD 가운데 하나로 끝났을 때만 실행합니다.

```powershell
python -B -c "import json,pathlib,shutil,sys; s=pathlib.Path(sys.argv[1]); d=pathlib.Path('results',json.loads(s.read_text(encoding='utf-8'))['run_id']); d.mkdir(parents=True); shutil.copyfile(s,d/'summary.json'); print((d/'summary.json').as_posix())" "$q\provider_parity\compare1-rf\summary.json"
```

화면: `results/PP-<날짜와 시각>Z-rf/summary.json` 한 줄. 시간: 1초 안.

**28.** BTC-USD를 대조합니다.

```powershell
python -B -m tools.provider_parity.parity_check compare --series btc --table "$rc\docs\nautilus_bridge\registration\pilot2_C3_btcusd.json" --repo $rc --pair coinbase "$q\provider_parity\fetch1-btc-coinbase\btc_coinbase.csv" --pair binance "$q\provider_parity\fetch1-btc-binance\btc_binance.csv" --pair bitstamp "$q\provider_parity\fetch1-btc-bitstamp\btc_bitstamp.csv" --out "$q\provider_parity\compare1-btc" --owner-run
```

화면: 마지막 줄 `PARITY btc PASS exit=0 summary=...\compare1-btc\summary.json`. binance 짝은 늦게 시작해서 요약 안에서 WITHHELD로 적히는 것이 정상이고, 진단용이라 시계열 판정에 영향을 주지 않습니다. 시간: 2~10초.

**29.** BTC-USD 요약을 복사합니다. 28단계가 PASS, FAIL, WITHHELD 가운데 하나로 끝났을 때만 실행합니다.

```powershell
python -B -c "import json,pathlib,shutil,sys; s=pathlib.Path(sys.argv[1]); d=pathlib.Path('results',json.loads(s.read_text(encoding='utf-8'))['run_id']); d.mkdir(parents=True); shutil.copyfile(s,d/'summary.json'); print((d/'summary.json').as_posix())" "$q\provider_parity\compare1-btc\summary.json"
```

화면: `results/PP-<날짜와 시각>Z-btc/summary.json` 한 줄. 시간: 1초 안.

### 라. 기록 (30~34단계, 약 1~2분)

판정이 무엇이든 요약은 모두 올립니다. `detail.json`, 수신 폴더, CSV는 올리지 않습니다. 아래 30단계의 줄은 이름이 `summary.json`인 파일만 담습니다.

**30.** 복사한 요약만 커밋 대상에 담습니다.

```powershell
git add "results/*/summary.json"
```

화면: 아무것도 나오지 않습니다. 시간: 1초 안.

**31.** 담긴 것을 확인합니다.

```powershell
git status --short
```

화면: 복사한 요약 수만큼의 줄. 모든 줄이 `A  results/PP-`로 시작하고 `/summary.json`으로 끝납니다. 다른 모양의 줄이 하나라도 있으면 멈추고 그 줄들을 Claude에게 보냅니다. 시간: 1초 안.

**32.** 커밋합니다.

```powershell
git commit -m "5-2: provider parity summaries"
```

화면: `files changed`가 들어 있는 줄과 `create mode 100644 results/PP-.../summary.json` 줄들. 시간: 1초 안.

**33.** GitHub에 올립니다.

```powershell
git push
```

화면: 끝에서 두 번째 줄이 `To `로 시작하고(뒤는 GitHub 주소), 마지막 줄이 `<옛 커밋>..<새 커밋>  <도구 브랜치> -> <도구 브랜치>` 모양입니다. `rejected`나 `fatal:`이 있으면 6절의 표를 봅니다. 시간: 5~20초.

**34.** 연구 클론이 그대로인지 다시 봅니다.

```powershell
git -C $rc status --porcelain
```

화면: 3단계와 같습니다(3단계에서 아무 줄도 없었으면 여기서도 없습니다). 시간: 1~5초.

`%LOCALAPPDATA%\quantgen\provider_parity` 폴더와 그 안의 파일은 지우지 않고 그대로 둡니다. `detail.json`을 어떻게 할지는 Step 10 뒤에 소유자가 정합니다(P-D7).

## 4. 통과와 실패

| 화면의 마지막 줄 | 뜻 | 할 일 |
| --- | --- | --- |
| `FETCH <시계열> <공급사> OK exit=0 csv=...` | 그 공급사에서 받았습니다. | 계속합니다. |
| `FETCH ... UNAVAILABLE <이유> exit=4 csv=-` | 받지 못했습니다. 아무것도 쓰지 않았습니다. 이유는 `no_key`, `plan_or_access`, `fetch_failed` 가운데 하나입니다. | 6절. 대조로 넘어가지 않습니다. |
| `FETCH ... REFUSED exit=2 csv=-` 또는 `FETCH ... ERROR exit=4 csv=-` | 도구가 입력이나 쓸 곳을 받아들이지 않았거나 예기치 않은 오류입니다. 아무것도 쓰지 않았습니다. | 6절. |
| `PARITY <시계열> PASS exit=0 summary=...` | 통과입니다. 이 실행이 기록 실행입니다. | 요약을 복사하고 라 구역에서 올립니다. |
| `PARITY <시계열> FAIL exit=1 summary=...` | 고정 파일 자체 검사나 독립·교차 공급사와의 대조가 허용치를 넘었습니다. 이 실행이 기록 실행입니다. | 다시 돌리지 않습니다. 요약을 복사하고 올린 뒤 Claude에게 알립니다. |
| `PARITY <시계열> WITHHELD exit=3 summary=...` | 끝까지 평가된 독립·교차 공급사가 없어 판정을 보류했습니다. 이 실행이 기록 실행입니다. | FAIL과 같습니다. |
| `PARITY <시계열> REFUSED exit=2 summary=-` | 입력을 읽지 않았습니다. 실행으로 세지 않고 아무것도 쓰지 않았습니다. | 윗줄의 이유를 고치고 같은 줄을 다시 실행합니다. 모르겠으면 두 줄을 Claude에게 보냅니다. |
| `PARITY <시계열> ERROR exit=4 summary=-` | 예기치 않은 오류입니다. 실행으로 세지 않습니다. | 마지막 두 줄을 Claude에게 보내고 기다립니다. |

- 파일럿 1(Step 8)은 SPY와 rf(DGS3MO)의 기록 실행이 둘 다 PASS일 때 시작합니다. 파일럿 2(Step 9)는 BTC-USD의 기록 실행이 PASS일 때 시작합니다(파일럿 1 통과라는 기존 조건은 그대로입니다).
- PASS가 아닌 시계열이 있으면 Claude가 올라온 요약을 읽고 선택지를 정리해 드립니다. 그 시계열의 파일럿은 소유자가 판정 문장을 `results/RULINGS.md`에 남긴 뒤에만 시작합니다. 러너는 이 관문을 검사하지 않으므로 순서를 지키는 것은 절차입니다.
- FAIL이나 WITHHELD를 PASS로 바꾸려고 다시 받거나 다시 대조하지 않습니다.

## 5. Claude에게 보낼 것

글자로 복사해 채팅에 붙입니다.

1. 수신 아홉 번(15~23단계) 각각의 마지막 두 줄, 모두 18줄.
2. 대조 세 번(24, 26, 28단계) 각각의 마지막 줄(`PARITY`로 시작하는 줄). REFUSED나 ERROR였으면 그 윗줄도 함께.
3. 31단계 `git status --short`의 줄들과 33단계 `git push` 출력의 마지막 두 줄.
4. 3단계나 34단계에서 줄이 나왔으면 그 줄들.

`summary.json`은 33단계의 push로 전달됩니다. 채팅에 붙이지 않아도 됩니다. Claude는 올라온 요약만 읽습니다.

**보내지 않는 것**

- `.env`의 내용과 키 값. 일부만 잘라서도 보내지 않습니다. 위 줄들에는 키가 들어 있지 않습니다. 도구는 키를 화면이나 파일에 쓰지 않습니다.
- `detail.json`, `fetch1-...` 폴더의 CSV와 `raw` 폴더(가격과 금리 값이 들어 있습니다), `meta.json`(값은 없지만 요약이 아닙니다). 스펙에 따라 이 PC 밖으로 나가는 파일은 `summary.json`뿐입니다.
- 화면 전체를 찍은 그림. 다른 창의 내용이 함께 찍힐 수 있으니 위 줄만 글자로 보냅니다.

## 6. 오류가 났을 때

도구가 실제 공급사를 부르는 것은 이번이 처음입니다(도구를 만드는 동안 실제 호출은 0건이었습니다). 수신에서 오류가 나면 소유자 PC의 문제가 아니라 도구의 문제일 수 있으므로, 고쳐 보려고 애쓰지 말고 줄을 보내 주십시오.

### 가장 나기 쉬운 세 가지

**(1) `REFUSED: ...: the output folder must be new`**

```text
REFUSED: C:\Users\...\quantgen\provider_parity\fetch1-spy-fmp: the output folder must be new
FETCH spy fmp REFUSED exit=2 csv=-
```

같은 줄을 두 번 실행했습니다. 그 폴더는 앞선 실행이 이미 만들었습니다.

- 수신(15~23단계)이면 이미 받은 것이므로 다시 받지 않고 다음 단계로 갑니다.
- 대조(24, 26, 28단계)이면 그 시계열은 이미 기록 실행이 있습니다. 다시 돌리지 않고 복사 단계로 갑니다.
- 폴더를 지우거나 이름을 바꿔 다시 실행하지 않습니다. 다시 받아야 할 이유가 있으면 Claude에게 먼저 알립니다.

**(2) `UNAVAILABLE: FMP_API_KEY is not set (--env-file or the environment)`**

```text
UNAVAILABLE: FMP_API_KEY is not set (--env-file or the environment)
FETCH spy fmp UNAVAILABLE no_key exit=4 csv=-
```

연구 클론의 `.env`에 그 이름의 줄이 없거나, 값이 비었거나, `<...>` 모양의 자리표시자가 그대로입니다. kis는 `KIS_APP_KEY`나 `KIS_APP_SECRET` 이름으로 같은 줄이 나옵니다.

- 키를 갖고 있는데 `.env`에 없었던 것이면, 연구 클론의 `.env`를 메모장으로 열어 `이름=값` 한 줄을 넣고 저장한 뒤 같은 단계를 다시 실행합니다. `.env`는 git이 추적하지 않는 파일이라 3단계와 34단계의 결과가 달라지지 않습니다. 값은 창에 치지 않고 누구에게도 보내지 않습니다.
- 그 공급사의 키가 원래 없으면 고치지 않습니다. 두 줄을 Claude에게 보내면, 대조에서 그 공급사를 "받지 못함(`no_key`)"으로 적는 줄을 Claude가 써 드립니다.

**(3) `UNAVAILABLE: ...`에 이어 `fetch_failed`나 `plan_or_access`, 또는 `ERROR: ...`**

```text
UNAVAILABLE: coinbase: HTTP 503, the answer starts: {"message":"..."}
FETCH btc coinbase UNAVAILABLE fetch_failed exit=4 csv=-
```

윗줄은 `<공급사>: HTTP <번호>`, `request failed (URLError)`, `request failed (TimeoutError)`, `... answered with a message instead of ...`, `kis request failed (KISError; HTTP 500, msg_cd ...)`, `yfinance failed (...)` 같은 모양입니다. `ERROR: <종류> at parity_check.py lines ...`로 나올 수도 있습니다.

- 같은 줄을 한 번만 더 실행합니다(잠깐의 연결 문제일 수 있습니다).
- 같은 결과면 마지막 두 줄을 Claude에게 보내고 기다립니다. 나머지 수신은 계속해도 되지만 대조(다 구역)는 시작하지 않습니다.
- 키가 없는 공급사의 `HTTP 403`은 대개 공급사 요금제가 아니라 회사·공유기의 프록시나 방화벽입니다. 다른 네트워크(예: 휴대폰 핫스팟)에서 한 번 더 해 볼 수 있습니다.
- 두 줄에는 키가 없습니다. 공급사 답의 앞부분이 인용될 때는 소수가 `#.#`으로 가려져 나옵니다.

### 그 밖의 줄

| 화면 | 원인 | 할 일 |
| --- | --- | --- |
| 2, 3단계 `fatal: cannot change to '...'` | 1단계의 경로가 틀렸습니다. | 1단계를 올바른 경로로 다시 실행합니다. |
| `Error while finding module specification for 'tools.provider_parity.parity_check'` | 도구 클론 폴더가 아닌 곳에서 실행했습니다. | 10단계를 다시 실행합니다. |
| `usage: ...`에 이어 `error: argument ...: expected one argument` | 창을 다시 열어 `$rc`나 `$q`가 비었습니다. | 7절. |
| `REFUSED: --env-file cannot be read (FileNotFoundError)` | `$rc`가 연구 클론이 아니거나 그 폴더에 `.env`가 없습니다. | 1단계의 경로를 확인합니다. |
| `REFUSED: ...: cannot be read as a pilot table (FileNotFoundError)` | `$rc`가 틀렸거나 연구 클론이 다른 브랜치에 있습니다. | 1, 2단계를 확인합니다. 연구 클론의 브랜치를 직접 바꾸지 말고 Claude에게 알립니다. |
| `REFUSED: ...: cannot be read as a pilot table (JSONDecodeError)` | 표 파일이 BOM과 함께 저장되어 있습니다. | 표를 고치지 않습니다(고치면 `owner_confirmed`에 영향이 있습니다). 줄을 Claude에게 보냅니다. |
| `REFUSED: yf_SPY.csv: md5 ... differs from the table's ...` | 고정 파일이 표에 적힌 것과 다릅니다. | 아무것도 고치지 않고 두 줄을 Claude에게 보냅니다. md5는 값이 아니므로 보내도 됩니다. |
| `REFUSED: --repo holds this tool ...` | `$rc`가 도구 클론을 가리킵니다. | 1단계를 연구 클론 경로로 다시 실행합니다. |
| `REFUSED: ... must lie outside every git work tree` 또는 `... must not lie in a OneDrive folder ...` | 출력 폴더가 git 폴더나 OneDrive 안입니다. | 4단계를 다시 실행하고 줄을 고치지 않은 채 다시 붙여넣습니다. |
| `REFUSED: spy_fmp.csv: cannot be read (FileNotFoundError)` | 그 수신이 OK로 끝나지 않아 파일이 없습니다. | 멈춤 지점으로 돌아갑니다. |
| `UNAVAILABLE: yfinance failed (ModuleNotFoundError)` | 이 `python`에 yfinance가 없습니다. | 13단계를 다시 보고, 설치하지 말고 Claude에게 알립니다. |
| `weekend dates`가 0이 아님 | 공급사가 날짜를 하루 밀어 붙였을 수 있습니다. | 그 파일로 대조하지 않습니다. 두 줄을 Claude에게 보냅니다. |
| `LEFT BEHIND: <폴더> ...`에 이어 `ERROR: ...` | 쓰다가 실패했고 폴더를 지우지 못했습니다(백신이나 동기화 프로그램이 파일을 잡고 있었습니다). | 결과가 아닙니다. 그 폴더를 직접 지우고 줄을 Claude에게 보냅니다. |
| 9단계 `fatal: destination path ... already exists and is not an empty directory.` | 도구 클론이 이미 있습니다. | 7절. |
| 9단계 `fatal: Remote branch ... not found in upstream origin` | 도구 브랜치 이름이 다르거나 아직 올라오지 않았습니다. | 5단계의 줄을 확인하고 Claude에게 알립니다. |
| 32단계 `Please tell me who you are` | 이 클론에 git 이름과 메일이 없습니다. | 줄을 Claude에게 보냅니다. |
| 33단계 `! [rejected]` | 그 사이 Claude가 같은 브랜치에 커밋을 올렸습니다. | 아래 두 줄을 차례로 실행합니다. |

33단계가 `rejected`였을 때만:

```powershell
git pull --rebase
```

화면: 마지막 줄이 `Successfully rebased and updated refs/heads/<도구 브랜치>.` 그다음:

```powershell
git push
```

화면: 33단계와 같습니다. 이번에도 `rejected`나 `CONFLICT`가 나오면 멈추고 줄을 Claude에게 보냅니다.

## 7. 창을 닫았다가 다시 할 때

- 새 PowerShell 창에서 1단계, 4단계, 10단계를 다시 실행하고, 멈춘 단계부터 이어서 합니다. 5~9단계와 11~14단계는 다시 하지 않아도 됩니다.
- 이미 `OK`로 끝난 수신과 이미 PASS, FAIL, WITHHELD로 끝난 대조는 다시 실행하지 않습니다.
- 도구 클론이 이미 있는데 Claude가 "도구 클론을 최신으로 맞춰 달라"고 한 경우에만, 10단계 뒤에 아래 줄을 실행하고 11~14단계를 다시 합니다.

```powershell
git pull --ff-only
```

화면: `Already up to date.` 또는 `Fast-forward`가 들어 있는 줄들. 시간: 5~20초.

## 8. 확인하지 못한 것

이 안내의 줄은 Claude가 Linux에서 합성 자료와 가짜 공급사로 처음부터 끝까지 따라 해 본 것입니다. 연구 클론, 표 두 개, 고정 파일 세 개, `.env`는 모두 스크래치 폴더에 만든 합성본이고, 실제 값, 실제 키, 실제 공급사는 쓰지 않았습니다. 6절의 오류 줄도 같은 환경에서 일부러 일으켜 문구를 맞춰 보았습니다. `LEFT BEHIND` 줄 하나만은 일으키지 못해 도구 코드와 합성 검사에서 문구를 읽었습니다. 아래는 그렇게 해서는 확인할 수 없었던 것입니다.

- **PowerShell 자체.** Linux에는 PowerShell이 없어서, 같은 `git`·`python` 명령을 bash로 옮겨 실행했습니다(변수는 bash 변수로, `\`는 `/`로). 그래서 PowerShell의 변수 줄(1, 4~8단계), `$env:LOCALAPPDATA`, `Join-Path`, `"$q\..."` 꼴의 경로, 10단계의 `cd`, 12·25·27·29단계의 긴 따옴표 줄이 PowerShell에서 그대로 전달되는지는 실행해 보지 못했습니다. 시작 메뉴에서 창을 여는 방법과 탐색기에서 경로를 보는 방법도 확인하지 못한 화면 조작입니다.
- **Windows에서의 도구 실행.** 도구는 Windows에서 돈 적이 없습니다. 화면에 찍히는 경로 모양(`C:\Users\...`), cp949 콘솔, OneDrive 거부, 지워지지 않는 폴더는 Linux에서 흉내 낸 시험으로만 확인했습니다.
- **실제 공급사.** 아홉 공급사 가운데 어느 곳도 실제로 부르지 않았습니다. 주소와 응답 형식(특히 Coinbase, Bitstamp, 재무부 XML, H.15), KIS의 SPY 거래소 코드 `AMS`, FMP 요금제의 이력 깊이, 실제로 걸리는 시간은 첫 실행에서 처음 확인됩니다. 가짜 공급사는 `urllib`의 연결 함수, `yfinance` 모듈, 앱의 KIS 클라이언트 모듈을 대역으로 바꿔 끼운 것입니다. 그래서 앱의 실제 KIS 클라이언트와 `~/.nextgen/kis_token.json`을 거치는 경로, 실제 yfinance는 이번에 실행하지 않았습니다.
- **시간.** 3절의 시간은 추정입니다. 잰 값은 Linux에서 가짜 공급사로 잰 것뿐입니다: 자체 점검 0.5초, 수신 한 번에 0.5~8.2초(재무부 8.2초와 Coinbase 5.3초는 대부분 요청 사이 대기 시간), 대조 한 번에 0.5~0.7초. 실제 인터넷 왕복과 Windows의 파이썬 시작 시간은 들어 있지 않습니다.
- **9단계의 클론.** 가짜 원격 저장소에서 같은 줄에 `--no-checkout`을 붙이고 `docs/asset_expansion/`을 뺀 채로 실행했습니다(스크래치 폴더에 고정 캐시 폴더의 파일이 풀리지 않게 하기 위해서입니다). 실제 GitHub에서의 내려받는 양과 시간, 로그인 창이 뜨는지는 확인하지 못했습니다.
- **33단계의 push와 `git pull --rebase`.** 스크래치 폴더의 가짜 원격 저장소에만 실행했습니다. GitHub에는 아무것도 올리지 않았습니다. 33단계의 `To ...` 줄과 6절의 `rejected` 줄은 가짜 원격(`To file://...`)에서 본 모양을 적은 것입니다.
- **도구 브랜치, 커밋, sha256.** 2026-11-11 현재 고정되지 않았습니다. 완성본은 아직 GitHub에 올라가지 않았고, 5~7단계의 세 값은 소유자 판정 뒤에 정해집니다. 따라 해 볼 때는 현재 완성본의 브랜치와 커밋, sha256 `d651795e...`를 넣었습니다.
- **연구 클론의 실제 상태.** 표 두 개는 연구 브랜치에 올라와 있는 것(7A.3 커밋 `563db54`)을 git으로 읽어 BOM이 없고 도구가 읽는 필드가 있음을 확인했습니다. 소유자 PC의 고정 파일 세 개, `.env`, 3단계의 출력은 Claude가 볼 수 없습니다.
- **허용치.** 스펙 10.5.1의 허용치는 실제 자료 없이 정한 것이라, 실제 시계열에서 잘못된 FAIL이 얼마나 나올지는 알 수 없습니다.
