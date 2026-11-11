# 공급사 대조(⑤-2) 다시 실행 안내: SPY 두 번째 실행과 BTC-USD 진단

작성 2026-11-11(KST) · 대상: QUANTGEN 소유자, Windows 11 · 작성: Claude Code

- 근거: 2026-11-11 소유자 판정 "SPY-가-승인, BTC-나-승인". 원문과 Claude가 받은 뜻은 [`results/RULINGS.md`](../../results/RULINGS.md)와 [결정 기록](../nautilus_bridge/OWNER_RULINGS_LOG.md)에 있습니다. 규칙은 연구 브랜치 `claude/amazing-gauss-tdiguu`의 스펙 10.5입니다. 이 문서와 스펙이 다르면 스펙을 따릅니다.
- 앞 문서: [첫 실행 안내](PROVIDER_PARITY_OWNER_RUN_2026-11-11.md). 이 문서는 그 안내로 첫 실행을 마친 PC에서 이어서 하는 일만 적습니다.
- 도구: 대조 도구 [`parity_check.py`](../../tools/provider_parity/parity_check.py), 진단 스크립트 [`btc_diagnose.py`](../../tools/provider_parity/btc_diagnose.py). 영문 설명은 [도구 안내서](../../tools/provider_parity/README.md)에 있습니다.

> **시작하는 때.** Claude가 "실행 브랜치에 새 도구를 올렸습니다"라고 알린 뒤에 시작합니다. 그 전에는 4단계가 `Already up to date.`로 끝나고 7단계에서 멈추게 됩니다.

## 1. 무엇을 하는지

첫 실행(2026-11-11)의 결과는 SPY WITHHELD(판정 보류), DGS3MO PASS, BTC-USD FAIL이었습니다. 이 문서는 그 뒤 소유자 판정에 따른 두 가지 일을 적습니다.

| 구역 | 하는 일 | 왜 하는지 | 언제 하는지 |
| --- | --- | --- | --- |
| A. SPY 두 번째 실행 | fmp만 새 폴더에 다시 받고, SPY 대조를 한 번 더 돌려 요약을 올립니다. | 첫 실행에서 fmp가 최근 5,000행만 주었는데 도구가 그것을 전체 이력으로 받아들였습니다. 그래서 표의 시작(2004-12-01)까지 덮는 독립 공급사가 없어 판정이 보류됐습니다. 고친 도구는 앞 기간을 이어서 요청합니다. | 파일럿 1(Step 8)이 이 결과를 기다립니다. |
| B. BTC-USD 진단 | 한 줄을 실행하고, 화면에 나온 글자를 전부 채팅에 붙입니다. | BTC-USD가 왜 FAIL이었는지 봅니다. 가격이 아닌 통계만 나옵니다. 무엇이 나오는지는 18단계에 모두 적었습니다. | 준비(1~9단계)를 마친 뒤 언제든 됩니다. A보다 먼저 해도 됩니다. 파일럿 2(Step 9) 전에 필요합니다. |

- 다시 하지 않는 것: DGS3MO(이미 PASS), BTC-USD 대조(기록 실행은 FAIL로 남습니다), kis와 yahoo_now 수신(첫 실행 때 받은 파일을 그대로 씁니다).
- 첫 실행의 요약 세 개와 `fetch1-...`, `compare1-...` 폴더는 그대로 둡니다. 지우거나 고치지 않습니다.
- 두 번째 SPY 실행은 판정 "SPY-가-승인"에 따라 파일럿 1 관문에 인정됩니다. 첫 실행(WITHHELD)의 요약도 기록으로 남습니다.

## 2. 시작 전에 필요한 것

| 필요한 것 | 내용 |
| --- | --- |
| 첫 실행의 결과물 | 도구 클론 `%LOCALAPPDATA%\quantgen\pp_clone`과, `%LOCALAPPDATA%\quantgen\provider_parity` 아래의 `fetch1-...`, `compare1-...` 폴더가 그대로 있어야 합니다. |
| 새 고정값 | 5~6단계에 채워져 있습니다. 도구 커밋 `1be43ec191ce73bc4fbc7357a4b3438aca0e4bb1`, 도구 파일 sha256 `78dd1f508c713f9be138466bf69f5dd92d8bfdcc3afacfa37b21fc4bf28ca80c`. 판정 SPY-가에 따라 fmp 수신만 고친 두 번째 고정 버전입니다. 첫 실행 때 확인한 값과 다른 것이 정상입니다. 8단계에서 `sha256 DIFFERENT`가 나오면 멈추고 Claude에게 알려 주십시오. |
| 진단 스크립트 | `tools/provider_parity/btc_diagnose.py`, 진단 스크립트 sha256 `1e44f3a791dd8c13a667bf46cda2933c7bb0810ac6f7bcaae884a16cc71bc6ea`. 18단계 출력의 첫 줄에 이 값이 찍힙니다. 대조는 붙여 주신 출력에서 Claude가 합니다. |
| 연구 클론 | 첫 실행 때와 같은 폴더, 같은 브랜치(`claude/amazing-gauss-tdiguu`)입니다. 도구와 진단 스크립트는 이 폴더를 읽기만 합니다. |
| `.env` 변수 이름 | 10단계(fmp 수신)에 `FMP_API_KEY`가 필요합니다. 값은 이 문서, 채팅, PowerShell 창 어디에도 적지 않습니다. B 구역은 키를 쓰지 않습니다. |
| 파이썬 | 첫 실행 때 쓴 그 `python`입니다. 가상환경을 켜지 않습니다. |
| 인터넷 | 4단계와 16단계(GitHub), 10단계(FMP)만 인터넷을 씁니다. 16단계가 `rejected`로 끝났을 때 쓰는 두 줄(`git pull --rebase`, `git push`)도 GitHub에 닿습니다. 11단계의 대조와 B 구역은 인터넷을 쓰지 않습니다. |
| 함께 돌리지 않는 것 | 파일럿, 전체 시험(`python tests/run_all.py`), 동결 연구 판독이 도는 동안에는 실행하지 않습니다. |
| 걸리는 시간 | 준비 2~3분, A 구역 3~5분, B 구역 1분 안팎입니다. 모두 추정입니다. |

## 3. 순서

- 창은 첫 실행 때와 같은 일반 PowerShell 창("Windows PowerShell")입니다. 관리자 권한이 아닙니다.
- 회색 상자의 줄을 한 번에 한 줄씩 복사해 붙여넣고 Enter를 누릅니다. 줄이 길어 화면에서 접혀 보여도 한 줄입니다. 두 줄을 한 줄로 잇지 않습니다.
- 직접 고치는 곳은 1단계의 `<...>` 한 곳뿐입니다. 5~6단계의 값은 이미 채워져 있으니 그대로 붙여넣습니다.
- 각 단계의 "화면"과 다르게 나오면 다음 단계로 가지 않고 5절을 봅니다.
- 키 값을 창에 치지 않습니다. 도구가 `.env`에서 이름으로 읽습니다.

### 준비 (1~9단계, 약 2~3분)

**1.** 연구 클론 폴더를 변수에 넣습니다. 첫 실행의 1단계와 같은 줄입니다. 따옴표 안의 `<...>`를 연구 클론 폴더의 전체 경로로 바꿉니다.

```powershell
$rc = "<연구 클론 폴더의 전체 경로>"
```

화면: 아무것도 나오지 않습니다. 시간: 바로.

**2.** `quantgen` 폴더를 변수에 넣습니다(첫 실행의 4단계와 같은 줄입니다).

```powershell
$q = Join-Path $env:LOCALAPPDATA "quantgen"
```

화면: 아무것도 나오지 않습니다. 시간: 바로.

**3.** 도구 클론 폴더로 들어갑니다. 여기부터 18단계까지 모든 줄을 이 폴더에서 실행합니다.

```powershell
cd "$q\pp_clone"
```

화면: 프롬프트가 `...\quantgen\pp_clone>`로 끝납니다. 시간: 바로.

**4.** 도구 클론을 최신으로 맞춥니다. 고친 도구와 진단 스크립트가 이 줄로 들어옵니다.

```powershell
git pull --ff-only
```

화면: `Updating`으로 시작하는 줄, `Fast-forward` 한 줄, 바뀐 파일 목록이 나오고 프롬프트가 돌아옵니다. `Updating` 앞에 `From`으로 시작하는 줄과 브랜치 이름이 든 줄이 먼저 나올 수 있고, 파일 목록 뒤에는 바뀐 파일 수를 적은 줄과 `create mode`로 시작하는 줄들이 붙습니다. 파일 목록은 길어도 정상입니다(그동안 main에 들어간 다른 변경이 함께 옵니다). `Already up to date.`만 나오면 Claude가 아직 올리지 않은 것이니 멈춥니다. `fatal:`이나 `error:`로 시작하는 줄이 있으면 5절을 봅니다. 시간: 5~20초.

**5.** 판정이 고정한 새 도구 커밋을 변수에 넣습니다(그대로 붙여넣습니다).

```powershell
$fixed = "1be43ec191ce73bc4fbc7357a4b3438aca0e4bb1"
```

화면: 아무것도 나오지 않습니다. 시간: 바로.

**6.** 판정이 고정한 새 도구 파일 sha256을 변수에 넣습니다(그대로 붙여넣습니다).

```powershell
$sha = "78dd1f508c713f9be138466bf69f5dd92d8bfdcc3afacfa37b21fc4bf28ca80c"
```

화면: 아무것도 나오지 않습니다. 시간: 바로.

**7.** 새 도구 커밋이 이 클론에 들어 있는지 봅니다.

```powershell
git branch --contains $fixed
```

화면: `* claude/provider-parity-runs-20261111` 한 줄. `error:`로 시작하는 줄이 나오거나 아무 줄도 없으면 멈춥니다. 시간: 1초 안.

**8.** 도구 파일이 판정이 고정한 바이트 그대로인지 봅니다.

```powershell
python -B -c "import hashlib,sys; h=hashlib.sha256(open('tools/provider_parity/parity_check.py','rb').read()).hexdigest(); print(h); print('sha256 ok' if h==sys.argv[1] else 'sha256 DIFFERENT')" $sha
```

화면: 64자 한 줄과 `sha256 ok` 한 줄. `sha256 DIFFERENT`가 나오면 멈추고 두 줄을 Claude에게 보냅니다. 시간: 1초 안.

**9.** 도구 자체 점검을 돌립니다. 인터넷을 쓰지 않고 파일도 쓰지 않습니다.

```powershell
python -B -m tools.provider_parity.parity_check selftest
```

화면: 마지막 줄이 `SELFTEST PASS checks=11 failures=0`. 다른 줄로 끝나면 멈추고 마지막 몇 줄을 Claude에게 보냅니다. 시간: 1~3초.

### A. SPY 두 번째 실행 (10~17단계, 약 3~5분)

**10.** SPY를 fmp에서 새 폴더(`fetch2-spy-fmp`)로 다시 받습니다. 날짜는 첫 실행 때와 같은 표의 기간입니다.

```powershell
python -B -m tools.provider_parity.parity_check fetch --series spy --provider fmp --start 2004-12-01 --end 2026-09-25 --out "$q\provider_parity\fetch2-spy-fmp" --env-file "$rc\.env"
```

화면: 마지막 두 줄이 아래 모양입니다(`<...>` 자리에는 실제 행 수와 날짜가 나옵니다). 시간: 10초~1분(요청 2번 이상).

```text
rows <행 수>, first <첫 날짜>, last <끝 날짜>, weekend dates 0
FETCH spy fmp OK exit=0 csv=C:\Users\...\AppData\Local\quantgen\provider_parity\fetch2-spy-fmp\spy_fmp.csv
```

**멈춤 지점.** 아래 다섯 가지를 모두 만족하면 11단계로 갑니다. 하나라도 아니면 **대조(11단계)를 돌리지 않고** 이 두 줄을 Claude에게 보낸 뒤 답을 기다립니다. 수신은 판정이 아니므로 여기서 멈춰도 기록 실행으로 세지 않습니다.

- 마지막 줄이 `FETCH spy fmp OK exit=0`입니다.
- 첫 줄의 `first`가 2004-12-01이거나 그 전입니다. FMP가 2004년 자료를 주면 2004-11-01이 나옵니다(추정).
- 첫 줄의 `last`가 2026-09-25이거나 그 뒤이고, `weekend dates 0`입니다.
- 첫 줄에 `fmp paging stopped at`이 없습니다.
- 첫 줄의 `rows`가 5515입니다. `first`가 2004-11-01이고 `last`가 2026-10-02일 때 빠진 거래일이 없으면 나오는 수입니다. 이 수는 첫 실행 요약의 수(fmp가 준 표 기간 안의 4,995일과 그 앞에 남았던 494일)에 달력으로 센 2004년 11월의 거래일 21일과 표가 끝난 뒤의 5일을 더한 것입니다. `first`나 `last`가 그 날짜가 아니거나 `rows`가 5515가 아니면, 틀렸다는 뜻은 아니지만 대조 전에 한 번 봐야 하므로 멈추고 두 줄을 보냅니다.

`first`가 여전히 2006-11-15처럼 늦거나, 첫 줄 끝에 `; fmp paging stopped at <날짜>, after the first requested date 2004-10-31: <이유>`가 붙어 있으면 FMP에서 그 앞 자료를 받지 못한 것입니다. 이유는 둘 중 하나입니다. `an answer brought no earlier date`는 FMP가 더 앞 날짜를 주지 않았다는 뜻이고, `the budget of 12 requests ran out`은 한 번에 온 행이 너무 적어 요청 횟수 12번을 다 썼다는 뜻입니다. 수신 자체는 `OK`로 끝나지만 파일이 그 날짜에서 시작하므로, 이대로 대조하면 다시 WITHHELD가 됩니다. 그래서 대조하지 않고 두 줄을 보냅니다.

여기서 멈추면 두 번째 실행은 하지 않은 것입니다. SPY의 기록 실행은 첫 실행(WITHHELD) 그대로 남고 파일럿 1은 보류됩니다. 그 뒤에 도구를 또 고치거나 대조를 돌리는 것은 새 소유자 판정이 있어야 인정됩니다(스펙 10.5). Claude가 받은 줄을 보고 선택지를 정리해 드립니다.

**11.** SPY를 대조합니다. fmp는 10단계에서 새로 받은 파일을, kis와 yahoo_now는 첫 실행 때 받은 파일을 씁니다. 이 줄은 **한 번만** 실행합니다.

```powershell
python -B -m tools.provider_parity.parity_check compare --series spy --table "$rc\docs\nautilus_bridge\registration\pilot1_E1_spy.json" --repo $rc --pair fmp "$q\provider_parity\fetch2-spy-fmp\spy_fmp.csv" --pair kis "$q\provider_parity\fetch1-spy-kis\spy_kis.csv" --pair yahoo_now "$q\provider_parity\fetch1-spy-yahoo_now\spy_yahoo_now.csv" --out "$q\provider_parity\compare2-spy" --owner-run
```

화면: 마지막 줄 `PARITY spy PASS exit=0 summary=...\compare2-spy\summary.json`. PASS 자리에 FAIL이나 WITHHELD가 나와도 12단계로 갑니다. 시간: 2~10초.

- kis 짝은 요약 안에서 WITHHELD로 적히는 것이 정상입니다. KIS에는 2007-08-21 이전 자료가 없습니다. SPY 판정은 fmp 짝이 끝까지 평가되면 납니다.
- 첫 실행 때 받은 두 파일을 새 도구가 그대로 받아들입니다. 각 파일 옆의 수신 기록(`meta.json`)은 파일 내용, 공급사, 시계열, 받은 기간을 확인할 뿐 도구 버전은 따지지 않기 때문입니다(도구 코드에서 확인했고 합성 검사로도 확인했습니다).

**12.** SPY 요약을 도구 클론의 `results` 폴더로 복사합니다. 11단계가 PASS, FAIL, WITHHELD 가운데 하나로 끝났을 때만 실행합니다.

```powershell
python -B -c "import json,pathlib,shutil,sys; s=pathlib.Path(sys.argv[1]); d=pathlib.Path('results',json.loads(s.read_text(encoding='utf-8'))['run_id']); d.mkdir(parents=True); shutil.copyfile(s,d/'summary.json'); print((d/'summary.json').as_posix())" "$q\provider_parity\compare2-spy\summary.json"
```

화면: `results/PP-<날짜와 시각>Z-spy/summary.json` 한 줄. 첫 실행의 SPY 폴더(`results/PP-20261111T051909Z-spy`)와 이름이 다릅니다. 시간: 1초 안.

**13.** 복사한 요약만 커밋 대상에 담습니다.

```powershell
git add "results/*/summary.json"
```

화면: 아무것도 나오지 않습니다. 시간: 1초 안.

**14.** 담긴 것을 확인합니다.

```powershell
git status --short
```

화면: 한 줄. `A  results/PP-`로 시작하고 `Z-spy/summary.json`으로 끝납니다. 줄이 둘 이상이거나 다른 모양이면 멈추고 그 줄들을 Claude에게 보냅니다. 시간: 1초 안.

**15.** 커밋합니다.

```powershell
git commit -m "5-2: provider parity SPY second run summary"
```

화면: `1 file changed`가 들어 있는 줄과 `create mode 100644 results/PP-.../summary.json` 한 줄. 시간: 1초 안.

**16.** GitHub에 올립니다.

```powershell
git push
```

화면: 끝에서 두 번째 줄이 `To `로 시작하고(뒤는 GitHub 주소), 마지막 줄이 `<옛 커밋>..<새 커밋>  claude/provider-parity-runs-20261111 -> claude/provider-parity-runs-20261111` 모양입니다. `rejected`나 `fatal:`이 있으면 5절의 표를 봅니다. 시간: 5~20초.

**17.** 연구 클론이 그대로인지 봅니다.

```powershell
git -C $rc status --porcelain
```

화면: 첫 실행의 3단계, 34단계와 같습니다(그때 아무 줄도 없었으면 여기서도 없습니다). 시간: 1~5초.

**A 구역 결과의 뜻**

| 11단계의 마지막 줄 | 뜻 | 할 일 |
| --- | --- | --- |
| `PARITY spy PASS exit=0 summary=...` | SPY가 통과했습니다. DGS3MO는 이미 PASS이므로, Claude가 올라온 요약을 확인하면 파일럿 1(Step 8)의 대조 관문이 열립니다. | 12~17단계를 하고 줄을 보냅니다. |
| `PARITY spy FAIL exit=1 summary=...` | 새로 받은 fmp와 고정 파일의 차이가 허용치를 넘었습니다. | 다시 돌리지 않습니다. 12~17단계를 하고 줄을 보냅니다. Claude가 요약을 읽고 선택지를 정리해 드립니다. |
| `PARITY spy WITHHELD exit=3 summary=...` | 이번에도 끝까지 평가된 독립·교차 공급사가 없습니다. | FAIL과 같습니다. |
| `PARITY spy REFUSED exit=2 summary=-` 또는 `PARITY spy ERROR exit=4 summary=-` | 실행으로 세지 않습니다. 아무것도 쓰지 않았습니다. | 마지막 두 줄을 Claude에게 보내고 기다립니다. |

FAIL이나 WITHHELD로 끝난 두 번째 실행의 요약도 첫 실행의 요약 옆에 기록으로 남습니다. 그 뒤에 도구를 또 고치거나 SPY를 한 번 더 대조하는 것은 새 소유자 판정이 있어야 인정됩니다(스펙 10.5). 그때는 Claude가 요약을 읽고 선택지를 정리해 드리며, 그 전까지 파일럿 1은 보류입니다.

### B. BTC-USD 진단 (18단계, 약 1분)

**18.** 진단 스크립트를 실행합니다. 첫 실행 때 받은 coinbase와 bitstamp 파일, 그리고 고정 파일을 읽습니다. 파일을 쓰지 않고 인터넷을 쓰지 않으므로, 다시 실행해도 됩니다.

```powershell
python -B -m tools.provider_parity.btc_diagnose --table "$rc\docs\nautilus_bridge\registration\pilot2_C3_btcusd.json" --repo $rc --pair coinbase "$q\provider_parity\fetch1-btc-coinbase\btc_coinbase.csv" --pair bitstamp "$q\provider_parity\fetch1-btc-bitstamp\btc_bitstamp.csv" --owner-run
```

화면: 84줄입니다. 첫 줄은 `BTCDIAG 1 tool_sha256=<64자> script_sha256=<64자>`, 마지막 줄은 `BTCDIAG OK exit=0`입니다. 사이의 줄은 `window`, `file`, `common`, `returns`, `levels`, `split`, `venues` 가운데 하나로 시작합니다. 시간: 2~10초.

**읽는 것.** 판정 때의 선택지는 "PC에 남은 상세 파일에서" 읽는다고 적었습니다. 그런데 상세 파일(`detail.json`)에는 수준 차이가 가장 큰 100일만 있고 날짜별 수익률 차이가 없어서, 연도별 불일치 일수를 거기서 읽을 수 없습니다. 그래서 스크립트는 대조 때 읽은 파일 셋(고정 파일, coinbase 파일, bitstamp 파일)을 대조 도구의 읽기 함수로 다시 읽어 계산합니다. 상세 파일은 열지 않습니다. 이것은 선택지의 문구보다 넓은 Claude의 해석입니다.

**찍는 것.** 모두 가격이 아닌 통계입니다. 선택지가 이름 붙인 것은 아래의 (가)와 (나) 두 가지이고, 나머지는 Claude가 "가격이 아닌 통계"로 읽어 함께 찍는 것입니다. 나머지가 PC 밖으로 나가는 것을 원하지 않으시면 출력을 붙이지 말고 그렇게 알려 주십시오. 그러면 Claude가 스크립트를 두 가지만 찍도록 줄입니다.

- (가) 연도별 "불일치 일수"(`returns`의 `over`). 불일치 일수는 하루 수익률이 두 시계열 사이에서 2% 넘게 다른 날의 수입니다. 고정 파일과 coinbase, 고정 파일과 bitstamp 두 짝을 각각 셉니다.
- (나) 구간별 "수준 차이"의 상위 1% 값과 최댓값(`levels`의 `p99_pct`, `max_pct`). 수준 차이는 같은 날 두 가격이 서로 몇 % 떨어져 있는지입니다(두 가격의 비율에 로그를 취해 100을 곱한 값으로, 몇 % 안쪽에서는 보통의 % 차이와 거의 같습니다). 상위 1% 값은, 그보다 차이가 큰 날이 전체의 1%뿐인 값입니다(99번째 백분위수). 구간은 2017-01-01 앞과 뒤 둘입니다. 소수 첫째 자리까지만 찍고, 100일이 안 되는 구간은 `n/a`로 찍습니다.
- 도구 파일과 진단 스크립트의 sha256, 표의 기간, 도구가 쓰는 허용치 세 개.
- 읽은 coinbase 파일과 bitstamp 파일의 sha256, 그리고 각 파일 옆에 수신 기록이 있었는지(`file`). 이 sha256은 첫 실행 때 올린 요약에 이미 들어 있는 값입니다.
- 두 시계열에 함께 있는 날 수(`common`)와 연도별로 비교한 날 수(`returns`의 `days`).
- 수준 차이가 1.5%, 5%를 넘은 날 수(`levels`의 `over_p99_max`, `over_max`)와, 그 가운데 그 거래소만 따로 떨어진 날 수(`only_p99_max`, `only_max`: 고정 파일은 다른 거래소와 그 한도 안에서 맞고 두 거래소끼리는 그 한도보다 더 벌어진 날).
- 불일치한 날의 갈래(`split`). 두 거래소 모두와 불일치한 날(`both`), 한 거래소와만 불일치하고 두 거래소끼리도 서로 다른 날(`..._only`: 그 거래소가 따로 떨어진 날), 한 거래소와만 불일치하지만 두 거래소끼리는 맞는 날(`..._edge`: 어느 쪽이 따로 떨어졌는지 가를 수 없는 날), 짝을 지을 수 없는 날(`..._unpaired`)로 나눕니다.
- 두 거래소 모두와 불일치한 날에 두 거래소끼리는 서로 맞는지(`venues`).
- coinbase와 bitstamp를 서로 견준 같은 줄들(`returns`, `levels`). 고정 파일의 자료가 들어가지 않습니다.

**찍지 않는 것.** 가격, 수익률 값, 날짜를 알 수 있는 어느 한 날의 차이, 연도보다 자세한 날짜. 예외는 표의 시작·끝 날짜와 허용치에 들어 있는 날짜 2017-01-01뿐이며, 둘 다 자료의 날짜가 아닙니다. 스크립트는 찍을 줄 전체를 정해진 모양과 대조한 뒤에만 첫 줄을 찍습니다. 모양이 다른 줄이 하나라도 있으면 통계는 한 줄도 찍지 않고 `ERROR: ...`와 `BTCDIAG ERROR exit=4` 두 줄만 찍습니다.

**최댓값에 대해 알아 두실 것.** 최댓값(`max_pct`)은 어느 하루의 수준 차이입니다. 날짜는 찍지 않습니다. 다만 coinbase와 bitstamp의 종가는 누구나 볼 수 있는 값이라서, 그 하루가 언제인지 찾아낸 사람은 그날의 고정 파일 종가를 반올림 오차(0.05% 안팎) 안에서 되짚을 수 있습니다. 선택지가 최댓값을 이름 붙였기 때문에 찍습니다.

**보낼 것.** 첫 줄부터 마지막 줄까지 84줄 전체를 글자로 복사해 채팅에 붙입니다. 긴 줄이 화면에서 접혀 보여도 그대로 복사하면 됩니다. 마지막 줄이 `BTCDIAG REFUSED exit=2`나 `BTCDIAG ERROR exit=4`이면 통계는 한 줄도 찍히지 않은 것입니다. 그때는 나온 두 줄을 보냅니다. `REFUSED` 줄에는 폴더 경로가 들어갈 수 있습니다. 경로 가운데 Windows 계정 이름 부분은 지우고 보내도 됩니다.

**Claude가 출력을 받으면 하는 일.** 읽는 규칙은 출력을 보기 전에 미리 적어 두었습니다([`results/RULINGS.md`](../../results/RULINGS.md)의 BTC-USD 항목, Claude의 규칙).

1. 먼저 기록 실행의 파일을 읽은 출력인지 봅니다. sha256 넷, 공통 일수(4086, 4392), 도구의 불일치 일수와 허용 일수(43과 20, 47과 21)가 첫 실행의 요약과 같아야 합니다. 다르면 읽지 않고 여쭙니다.
2. 한 거래소만 따로 떨어진 날(고정 파일은 다른 거래소와 맞는 날)을 빼면 고정 파일의 불일치 일수가 허용 일수 안에 들고 2017년 이후의 수준 한도 안에도 들면, FAIL은 고정 파일이 아니라 각 거래소 자신의 종가에서 나온 것입니다. 두 거래소 모두에 대해 그럴 때만 원인이 밝혀진 것으로 봅니다. 이때는 판정의 둘째 줄에 따라 BTC-USD 관문을 통과한 것으로 처리하고 알려 드립니다.
3. 두 거래소끼리는 맞는데 고정 파일만 두 거래소 모두와 다른 날이 허용 일수보다 많으면 "고정 파일이 따로 떨어진 것"입니다. 이 출력은 어느 해에 얼마나 다른지는 말해 주지만 왜 다른지는 말해 주지 않습니다. 원인은 미검증으로 두고, 관문을 자동으로 통과시키지 않습니다. 수치를 보고하고 여쭙니다.
4. 그 밖의 경우에도 원인은 미검증입니다. 보고하고 여쭙니다.

## 4. Claude에게 보낼 것

글자로 복사해 채팅에 붙입니다.

1. 10단계의 마지막 두 줄.
2. 11단계의 마지막 줄(`PARITY`로 시작하는 줄). REFUSED나 ERROR였으면 그 윗줄도 함께.
3. 14단계 `git status --short`의 줄과 16단계 `git push` 출력의 마지막 두 줄.
4. 17단계에서 줄이 나왔으면 그 줄들.
5. 18단계의 출력 전체(84줄).

새 요약(`summary.json`)은 16단계의 push로 전달됩니다. 채팅에 붙이지 않아도 됩니다.

**보내지 않는 것**

- `.env`의 내용과 키 값. 일부만 잘라서도 보내지 않습니다.
- `detail.json`, `fetch1-...`·`fetch2-...` 폴더의 CSV와 `raw` 폴더(가격 값이 들어 있습니다), `meta.json`.
- 화면 전체를 찍은 그림. 위 줄만 글자로 보냅니다.

## 5. 다르게 나왔을 때

고쳐 보려고 애쓰지 말고 줄을 보내 주십시오. 실패한 수신과 REFUSED·ERROR로 끝난 대조는 아무 폴더도 남기지 않습니다.

| 화면 | 원인 | 할 일 |
| --- | --- | --- |
| 3단계 뒤 프롬프트가 `...\quantgen\pp_clone>`로 끝나지 않고 빨간 오류 글이 나옴 | 2단계를 하지 않아 `$q`가 비었거나, 도구 클론 폴더가 없습니다. | 2단계와 3단계를 다시 실행합니다. 같은 결과면 그 글을 Claude에게 보냅니다. |
| 4단계 `Already up to date.` | Claude가 아직 실행 브랜치에 새 도구를 올리지 않았습니다. | 멈추고 Claude에게 알립니다. |
| 4단계 `fatal: Not possible to fast-forward, aborting.` | 이 클론에 올리지 않은 커밋이 있습니다. | 줄을 Claude에게 보냅니다. |
| 4단계 `error: Your local changes to the following files would be overwritten by merge` | 도구 클론의 파일이 바뀌어 있습니다. | 고치지 말고 그 줄들을 Claude에게 보냅니다. |
| 7단계에서 아무 줄도 없거나 `error: malformed object name` 또는 `error: no such commit` | 새 도구 커밋이 이 클론에 없습니다. | 4단계의 화면을 다시 보고 Claude에게 알립니다. |
| 8단계 `sha256 DIFFERENT` | 도구 파일이 고정값과 다릅니다. | 멈추고 두 줄을 Claude에게 보냅니다. |
| 9단계의 마지막 줄이 `SELFTEST PASS checks=11 failures=0`이 아님(`SELFTEST FAIL ...`이거나 빨간 오류 글) | 도구 자체 점검이 통과하지 못했습니다. | 멈추고 마지막 몇 줄을 Claude에게 보냅니다. |
| 10단계 `REFUSED: ...\fetch2-spy-fmp: the output folder must be new` | 10단계를 이미 한 번 실행했습니다. | 다시 받지 않습니다. 앞선 실행의 두 줄로 멈춤 지점을 확인합니다. 그 두 줄을 보지 못했으면 Claude에게 알립니다. |
| 10단계 `UNAVAILABLE: FMP_API_KEY is not set (--env-file or the environment)` | 연구 클론의 `.env`에 그 이름의 줄이 없습니다. | 첫 실행 안내 6절의 (2)와 같습니다. |
| 10단계 `UNAVAILABLE: fmp: HTTP <번호>`, `UNAVAILABLE: fmp answered with a message instead of rows` 또는 `UNAVAILABLE: fmp returned no rows` (줄 끝에 `request <수> of the page-back`가 없음) | 첫 요청이 실패했습니다. 아무 폴더도 남지 않았습니다. | 첫 실행 안내 6절의 (3)과 같습니다. 같은 줄을 한 번만 더 실행하고, 같은 결과면 마지막 두 줄을 Claude에게 보냅니다. |
| 10단계 `UNAVAILABLE: fmp: HTTP <번호>; request <수> of the page-back` 또는 `UNAVAILABLE: fmp answered with a message instead of rows; request <수> of the page-back` | 이어 받는 요청 가운데 하나가 실패했습니다(FMP의 요청 한도일 수 있습니다). 아무 폴더도 남지 않았습니다. | 1분쯤 뒤 같은 줄을 한 번만 더 실행합니다. 같은 결과면 마지막 두 줄을 Claude에게 보냅니다. |
| 10단계 `UNAVAILABLE: fmp gave one date two different values in two answers` | 이어 받은 두 답이 같은 날짜에 다른 값을 주었습니다. 도구는 두 답이 맞닿는 날을 일부러 두 번 받아 값을 견주며, 어느 쪽도 고르지 않습니다. 아무 폴더도 남지 않았고 실행으로 세지 않습니다. | 다시 실행하지 않고 마지막 두 줄을 Claude에게 보냅니다. |
| 11단계 `REFUSED: ...\compare2-spy: the output folder must be new` | 두 번째 대조를 이미 실행했습니다. | 다시 돌리지 않고 12단계로 갑니다. |
| 11단계 `REFUSED: spy_fmp.csv: cannot be read (FileNotFoundError)` | 10단계가 `OK`로 끝나지 않아 파일이 없습니다. | 멈춤 지점으로 돌아갑니다. |
| 11단계 `REFUSED: spy_kis.csv: cannot be read (FileNotFoundError)`(또는 `spy_yahoo_now.csv`) | 첫 실행의 수신 폴더가 없거나 이름이 다릅니다. | 줄을 Claude에게 보냅니다. |
| 12단계 `FileExistsError` | 12단계를 이미 한 번 실행했습니다. | 13단계로 갑니다. |
| 14단계에서 줄이 없음 | 12단계를 하지 않았거나 요약이 이미 커밋돼 있습니다. | 12단계의 화면을 확인하고, 모르겠으면 Claude에게 알립니다. |
| 16단계 `! [rejected]` | 그 사이 Claude가 같은 브랜치에 커밋을 올렸습니다. | 아래 두 줄을 차례로 실행합니다. |
| 18단계 `REFUSED: ...`에 이어 `BTCDIAG REFUSED exit=2` | 스크립트가 입력을 읽지 않았습니다. 통계는 찍히지 않았습니다. | 두 줄을 Claude에게 보냅니다. |
| 18단계 `ERROR: ...`에 이어 `BTCDIAG ERROR exit=4` | 예기치 않은 오류이거나, 스크립트의 수치가 도구 자체 검사와 맞지 않아 찍지 않은 것입니다. | 두 줄을 Claude에게 보냅니다. |
| 18단계 `No module named tools.provider_parity.btc_diagnose` | 4단계를 하지 않아 진단 스크립트가 이 클론에 아직 없습니다. | 4단계부터 다시 합니다. |
| `Error while finding module specification for 'tools.provider_parity.btc_diagnose'`(또는 `...parity_check'`) | 도구 클론 폴더가 아닌 곳에서 실행했습니다. | 3단계를 다시 실행합니다. |
| `usage: ...`에 이어 `error: argument --repo: expected one argument` | 창을 다시 열어 `$rc`가 비었습니다. | 6절. |

16단계가 `rejected`였을 때만:

```powershell
git pull --rebase
```

화면: 마지막 줄이 `Successfully rebased and updated refs/heads/claude/provider-parity-runs-20261111.` 그다음:

```powershell
git push
```

화면: 16단계와 같습니다. 이번에도 `rejected`나 `CONFLICT`가 나오면 멈추고 줄을 Claude에게 보냅니다.

## 6. 창을 닫았다가 다시 할 때

- 새 PowerShell 창에서 1, 2, 3단계를 다시 실행하고, 멈춘 단계부터 이어서 합니다. 4~9단계는 이미 통과했으면 다시 하지 않아도 됩니다.
- 이미 `OK`로 끝난 10단계와 이미 PASS, FAIL, WITHHELD로 끝난 11단계는 다시 실행하지 않습니다.
- 18단계는 아무것도 쓰지 않으므로 다시 실행해도 됩니다.

## 7. 확인하지 못한 것

이 안내의 줄은 Claude가 Linux에서 합성 자료와 가짜 공급사로 따라 해 본 것입니다. 18단계 가운데 16단계(`git push`)와 그 뒤의 `git pull --rebase` 두 줄만 실행하지 않았습니다. 5절의 오류 줄도 같은 환경에서 일부러 일으켜 문구를 맞췄습니다. 일으키지 못한 것은 셋입니다: 16단계의 `rejected`(push를 하지 않았습니다), 3단계에서 PowerShell이 내는 글, 18단계의 `BTCDIAG ERROR exit=4`(이 줄은 합성 검사에서 문구를 확인했습니다). 무엇을 어떻게 따라 했는지는 [검토 기록](../compliance/FACTS.md#provider-parity-2026-11-11)의 "다시 실행 안내 따라 하기" 행에 있습니다.

그렇게 따라 한 뒤에 검토가 있었고, 도구와 진단 스크립트를 한 번 더 고쳤습니다. 고친 뒤에는 처음부터 끝까지 다시 따라 하지 않았습니다. 다시 확인한 것은 둘입니다. 검사 묶음이 8·9·10·11·12·18단계의 줄을 이 안내서 파일에서 뽑아 그대로 실행하고, 9·10·11단계의 오류 줄을 일으켜 5절 표와 대조합니다. 그리고 4단계의 화면(`From` 줄, `Updating`, `Fast-forward`, 파일 목록, `create mode` 줄)을 스크래치 저장소에서 한 번 더 봤습니다. git만 부르는 나머지 줄(7, 13~15, 17단계)은 바뀌지 않았습니다. 아래는 이렇게 해서는 확인할 수 없었던 것입니다.

- **실제 FMP.** FMP를 실제로 부르지 않았습니다. 확인된 것은 첫 실행에서 FMP가 요청 한 번에 5,000행을 주었고 그 첫 날짜가 2006-11-15였다는 것뿐입니다. FMP가 `to` 날짜를 지켜 그 앞 기간을 주는지, 2004~2006년 자료를 갖고 있는지, 같은 날짜에 대해 두 요청에서 같은 값을 주는지, 자료가 없는 기간을 물으면 무엇으로 답하는지는 10단계에서 처음 확인됩니다. 자료를 주지 않으면 멈춤 지점에서 멈추게 됩니다. 두 요청의 값이 다르거나, 자료가 없는 기간에 빈 목록이 아닌 다른 것(안내 글이나 오류 번호)으로 답하면 10단계는 `UNAVAILABLE`로 끝나고 아무 폴더도 남지 않습니다(5절의 표).
- **멈춤 지점의 행 수 5515.** 첫 실행의 요약에서 읽은 수(4,995와 494)에, 규칙으로 만든 거래소 달력으로 센 수(2004년 11월의 21일, 표가 끝난 뒤의 5일)를 더한 것입니다. 그 달력은 첫 실행 SPY 요약의 수를 모두 맞게 냅니다. 실제 FMP 파일이나 소유자 PC의 yahoo_now 파일과 견줘 본 수는 아닙니다.
- **PowerShell과 Windows.** Linux에는 PowerShell이 없어서 같은 `git`·`python` 명령을 bash로 옮겨 실행했습니다(변수는 bash 변수로, `\`는 `/`로). 그래서 1~3단계와 5~6단계의 변수 줄, 따옴표가 든 긴 줄(8, 12단계)이 PowerShell에서 그대로 전달되는지, PowerShell이 내는 오류 글이 어떤 모양인지는 보지 못했습니다. 같은 모양의 줄은 첫 실행 안내에 있고, 소유자가 2026-11-11에 그 안내로 요약 세 개를 올렸습니다. 고친 도구와 진단 스크립트는 Windows에서 돈 적이 없습니다.
- **`.env`.** 10단계의 `--env-file "$rc\.env"` 자리에는 다른 이름의 합성 키 파일을 넣어 실행했습니다. 실제 `.env`는 열지 않았습니다.
- **실제 파일.** 진단 스크립트는 실제 고정 파일과 첫 실행의 실제 수신 파일을 읽은 적이 없습니다. 84줄이라는 수는 표의 기간(2014~2026년, 13개 연도)에서 나온 것이고, 같은 기간의 합성 파일로 실행해 84줄을 확인했습니다. 실제 파일에서 걸리는 시간은 재지 못했습니다.
- **출력을 읽는 규칙.** 18단계 끝에 적은 규칙은 합성 자료로만 시험했습니다. 실제 출력이 어느 경우에 드는지, 그 규칙으로 원인이 갈리는지는 출력을 받아야 압니다.
- **실행 브랜치.** 4단계가 받아 오는 커밋은 이 문서를 쓴 뒤에 Claude가 main을 실행 브랜치에 합쳐 올리는 것입니다. 따라 해 본 것은 스크래치 폴더에 만든 가짜 원격 저장소입니다. 첫 실행 뒤의 상태(첫 고정 버전의 도구와 요약 세 개의 자리)를 만들고, 거기에 새 파일이 들어온 커밋 하나를 더한 뒤 4단계를 실행했습니다. 실제 GitHub에서 4단계가 받아 오는 양과 시간은 확인하지 못했습니다.
- **16단계의 push.** 이번에는 실행하지 않았습니다. 화면 설명은 첫 실행 안내의 33단계와 같은 줄을 그때 가짜 원격 저장소에서 본 모양입니다.
- **BTC-USD의 원인.** 진단 출력을 받기 전이라 아직 모릅니다. 출력이 어느 경우에 드는지에 따라 파일럿 2를 바로 진행할 수 있는지, 소유자께 다시 여쭤야 하는지가 갈립니다(`results/RULINGS.md`의 BTC-USD 항목).
- **시간.** 모두 추정입니다.
