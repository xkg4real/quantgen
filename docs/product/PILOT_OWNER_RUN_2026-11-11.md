# 파일럿 1·2, Windows 전체 검사, main 병합 소유자 실행표 (Step 8·9·10)

작성 2026-11-11(KST) · 대상: QUANTGEN 소유자, Windows 11, PowerShell · 작성: Claude Code

- 다루는 범위: ⑤-2 공급사 대조가 끝난 **뒤** 소유자 PC에서 하는 일입니다. 파일럿 1(Step 8), 파일럿 2(Step 9), Windows 전체 검사(Step 10 앞부분), main 병합입니다.
- ⑤-2 공급사 대조는 안내서가 따로 있습니다: `docs/product/PROVIDER_PARITY_OWNER_RUN_2026-11-11.md`(PR #102로 main에 들어왔습니다). 이 문서는 그 내용을 되풀이하지 않습니다.
- 근거: 연구 브랜치 `claude/amazing-gauss-tdiguu`(끝 커밋 `8a8c247`)의 스펙, 런북, 러너 코드와 소유자 판정입니다. 줄 번호는 J절에 있습니다. 이 문서와 스펙이 다르면 스펙을 따릅니다.
- "미검증"은 근거 줄을 찾지 못했거나 Windows에서 실행해 보지 못했다는 뜻입니다. 모아 둔 목록은 L절에 있습니다.

> **아직 시작하지 않습니다.** 처음 앉는 때는 ⑤-2 대조 요약 세 개(SPY, DGS3MO, BTC-USD)가 모두 올라가고, Claude가 "SPY와 DGS3MO 관문을 통과했습니다"라고 알린 뒤입니다.

> **2026-11-11 공급사 대조 때 소유자 PC에서 본 상태 (소유자가 붙여 준 화면 줄).** 첫 파일럿 전에 정리할 것이 있습니다.
>
> - 연구 클론 폴더(`C:\Users\<사용자>\OneDrive\Desktop\QUANTGEN`)가 UI 브랜치 `claude/friendly-bardeen-r6xe8f`에 있었고, 소유자가 `git switch`로 연구 브랜치로 바꿨습니다. 앱을 쓰려고 다시 UI 브랜치로 돌려놓았다면 A3이 멈춥니다. 그때는 직접 바꾸지 말고 Claude에게 알립니다.
> - 로컬 연구 브랜치는 `83ee469`로, 원격의 `8a8c247`보다 커밋 하나가 뒤입니다. 그 커밋은 스펙 문서만 바꿉니다. A4의 `git pull --ff-only`가 받아 옵니다.
> - 추적되지 않는 폴더 `.agents/`와 `quantgen/`이 있습니다. 이 둘이 있는 동안 A5에 줄이 나오고 러너는 R-01로 거부합니다. 지우지 않습니다. 무엇이 들어 있는지 확인한 뒤 Claude가 클론 밖으로 옮기는 줄을 써 드립니다(아직 정하지 않았습니다).
> - `python`은 Microsoft Store의 Python 3.13.14였습니다.

## 세 줄 요약

1. 소유자는 네 번 앉습니다. 파일럿 1, 파일럿 2, Windows 전체 검사, main 병합입니다. 사이마다 Claude의 답을 기다립니다.
2. 앉을 때마다 A절의 준비 점검을 먼저 합니다. 그다음 명령을 한 줄씩 실행하고, 화면의 마지막 줄을 Claude에게 붙여 넣습니다.
3. 결과가 기대와 달라도 다시 돌리지 않습니다. 표, 원장, 고정 파일은 고치지 않습니다. 모르는 줄이 나오면 멈추고 그 줄을 보냅니다. 화면의 `remedy:` 줄은 Claude에게 보내는 줄이고, 그대로 따라 하지 않습니다.

되돌릴 수 없는 줄은 세 개입니다: B2(파일럿 1 실행), D2(파일럿 2 실행), F12(main을 GitHub에 올리기). 그 앞에는 굵은 글씨로 다시 적어 두었습니다.

## 앉는 횟수

| 앉는 횟수 | 무엇을 | 예상 시간(추정) | 시작 조건 |
| --- | --- | --- | --- |
| 그 전 | ⑤-2 공급사 대조 | 그 안내서에 있습니다. | 그 안내서에 있습니다. |
| 1 | A 준비 점검, B 파일럿 1 | 30~45분. 러너가 도는 시간은 그중 2~10분. | 세 시계열(SPY, DGS3MO, BTC-USD)의 대조 요약이 모두 올라가 있습니다(판정 P-D8). 그리고 Claude가 SPY와 DGS3MO 관문 통과를 알렸습니다. 관문 통과는 두 시계열의 기록 실행이 PASS이거나, PASS가 아닌 시계열마다 "진행한다"는 소유자 판정이 `results/RULINGS.md`에 적혀 있다는 뜻입니다. 판정이 "보류"이면 시작하지 않습니다. |
| 기다림 | C Claude의 파일럿 1 판독 | Claude 한 세션 안. | B의 push. |
| 2 | A 준비 점검, D 파일럿 2 | 20~30분. 러너가 도는 시간은 그중 1~5분. | Claude가 한 문장으로 두 가지를 알림: 파일럿 1이 `hard_pass True`이고, BTC-USD 관문을 통과했다는 것. 둘 가운데 하나만 적혀 있으면 시작하지 않고 되묻습니다. |
| 기다림 | Claude의 파일럿 2 판독 | Claude 한 세션 안. | D의 push. |
| 3 | A 준비 점검(일부), E Windows 전체 검사 | 30~40분. 검사가 도는 시간은 그중 약 16분. | 두 파일럿의 run 폴더가 올라가 있고, Claude가 시작해도 된다고 알림. |
| 기다림 | Claude의 마감 기록, main을 연구 브랜치에 합치기, 캐시 없는 전체 검사(판정 P3) | Claude 한두 세션. | E의 push. |
| 4 | F 받아서 확인, main 병합 네 줄 | 15~30분. | Claude가 "병합해도 됩니다"와 연구 브랜치 끝 커밋 번호를 알림. K절 2번과 3번에 소유자 판정이 나 있음. Claude가 알린 때부터 F12가 끝날 때까지 main에 다른 PR(변경 요청)을 병합하지 않고, 다른 세션에도 시키지 않음. |

시간은 모두 추정입니다. 근거는 아래 측정값과 계산입니다.

- 2026-11-04 소유자 PC의 `--timing` 기록: 5,600봉 합성 실행 12번에 35.1초(한 번에 2.5~3.8초).
- 같은 날 전체 검사 기록: 964행의 소요 시간 합이 958초(약 16분). 그 안에서 러너를 처음부터 끝까지 도는 합성 연습 두 건이 26.9초와 32.0초였습니다.
- 파일럿 1은 약 5,488봉을 24번 실행합니다(스펙의 행 수를 더한 값). 파일럿 2는 4,392일을 10번 실행합니다(날짜로 계산한 값). 고정 파일은 열지 않았습니다.
- 실제 자료에서 채점에 걸리는 시간은 잰 적이 없습니다(미검증). 준비 점검과 커밋에 드는 시간은 Claude의 어림입니다.

## 말 풀이

| 말 | 뜻 |
| --- | --- |
| 연구 클론 | Step 7A를 실행한 QUANTGEN 폴더입니다. 브랜치는 `claude/amazing-gauss-tdiguu`입니다. |
| 브랜치, 커밋, push, pull | 작업 갈래, 변경 묶음의 기록, GitHub에 올리기, GitHub에서 받기입니다. |
| HEAD | 지금 폴더가 가리키는 커밋입니다. |
| 러너 | 파일럿을 실행하는 프로그램 `tools/nautilus/runner.py`입니다. |
| 표 | 파일럿 설정을 적어 둔 등록표 파일입니다. `docs/nautilus_bridge/registration/` 아래에 두 개 있습니다. |
| 원장 | 시험한 설정을 한 줄씩 쌓는 기록 파일입니다(`E1.jsonl`, `C3.jsonl`). 덧붙이기만 하고, 한 번 쓴 줄은 지우지 않습니다. |
| 사슬 | 원장의 각 줄에는 바로 앞줄의 지문이 들어 있습니다. 줄을 고치거나 지우면 이 이어짐이 깨집니다. |
| 기록 실행 | 실제 원장에 남는, 정식으로 세는 실행입니다. 한 번 끝나면 그것이 기록이고, 다시 돌린 것은 소유자 판정 없이는 세지 않습니다. |
| 관문 | 파일럿을 시작해도 되는 조건입니다. ⑤-2 공급사 대조 결과로 정합니다. |
| 패리티 | QUANTGEN 계산과 Nautilus 계산이 같은지 보는 검사입니다. |
| hard 검사 | 하나라도 실패하면 판정을 보류하는 패리티 검사입니다. 화면의 `hard_pass`가 모두 통과했는지를 말합니다. |
| 카드 | 판정 결과를 적은 파일입니다. |
| 기준 카드 | 파일럿 2가 견주어 보는, 저장되어 있는 예전 결과 파일입니다. |
| 시행 수 | 판정이 "몇 번 시도해 본 것인지"로 세는 수입니다. 화면에는 다섯 값으로 나옵니다: `len_grid`(이번 설정 수), `family_n_raw`(원장의 줄 수), `market_n_raw`(그 가운데 같은 시장의 줄 수), `U`(예전 연구에서 썼지만 원장에 없는 설정 수), `n_trials`(`family_n_raw`와 `U`의 합). |
| 코드 지문 | 러너와 판정 코드 파일들의 내용으로 계산한 값입니다(`code_sha256`). 파일이 한 글자라도 바뀌면 달라집니다. |
| 실행 승인 문구 | 표의 `owner_confirmed`입니다. 소유자가 7A.3에서 적었습니다. 표 지문과 코드 지문의 앞 16자가 들어 있습니다. |
| 기준점 | 원장 줄에 적히는 git 커밋 번호입니다. 러너는 이것이 HEAD와 같아야 실행합니다. |
| run 폴더 | 러너가 실행 기록을 남기는 폴더입니다. `docs/nautilus_bridge/runs/NB-...` 꼴입니다. |
| 전용 파이썬 | 7A에서 Nautilus용으로 따로 만든 파이썬입니다(`ntvenv`). 러너가 안에서 부릅니다. 소유자가 직접 실행하지 않습니다. |
| 종료 코드 | 프로그램이 끝나며 남기는 숫자입니다. PowerShell에서 `$LASTEXITCODE`로 봅니다. |
| bp | 0.01%입니다. 10bp는 0.1%입니다. |
| worktree | 같은 클론에 딸린 둘째 작업 폴더입니다. 이 문서에서는 만들지 않습니다. |
| 캐시 | `docs/asset_expansion/cache` 폴더입니다. 가격과 금리 고정 파일이 들어 있습니다. Claude는 이 폴더를 열지 않습니다. |

## 공통 규칙

- 창은 Step 7A의 7A.2와 같은 일반 PowerShell 창입니다(관리자 권한 아님). 명령 프롬프트(CMD)가 아닙니다. 시작 메뉴에서 "PowerShell"을 찾아 "Windows PowerShell"을 엽니다.
- 회색 상자의 줄을 한 번에 한 줄씩 붙여 넣고 Enter를 누릅니다. 줄이 길어 접혀 보여도 한 줄입니다.
- 직접 고치는 곳은 `<...>` 자리뿐입니다.
- 각 단계의 "화면"과 다르게 나오면 다음 단계로 가지 않고 G절을 봅니다.
- 화면에 `remedy:`로 시작하는 줄이 나와도 그대로 따라 하지 않습니다. 그 줄은 Claude가 읽으라고 러너가 찍는 줄이고, 이 문서가 금지한 일(파일 지우기, 표 고치기, 다시 돌리기)을 시키는 것도 있습니다. G절 표의 "어떻게 하나" 칸만 따릅니다.
- 키 값과 `.env`의 내용은 창에 치지 않고 누구에게도 보내지 않습니다.
- 명령의 `python`은 7A에서 쓴 그 `python`입니다. 가상환경을 켜지 않습니다. `py313`이나 `ntvenv`의 파이썬으로 바꾸지 않습니다.
- 시간을 따로 적지 않은 단계는 몇 초 안에 끝납니다.
- B2, D2, E2의 마지막 줄들은 나오자마자 복사해 메모장에 붙여 둡니다. 창이 닫히면 다시 볼 수 없습니다.
- 창을 닫으면 `$rc`와 `$run`이 사라집니다. 창이 닫혔거나 PC가 꺼졌을 때는 G절 끝의 "창이 닫혔거나 PC가 꺼졌을 때"를 봅니다.

## A. 준비 점검 (앉을 때마다)

앉는 일에 따라 하는 단계가 다릅니다.

| 단계 | 파일럿 1, 2 (B, D) | 전체 검사 (E) | 병합 (F) |
| --- | --- | --- | --- |
| A1~A5 폴더, 브랜치, 받기, 바뀐 파일 | 합니다 | 합니다 | 합니다 |
| A6 기준점 | 합니다 | 안 해도 됩니다 | 안 해도 됩니다 |
| A7 지문 | 합니다 | 안 합니다 | 안 합니다 |
| A8 네트워크 | 합니다 | 권합니다 | 안 합니다 |
| A9 방화벽 규칙 | 합니다 | 합니다 | 안 합니다 |
| A10 전원, 업데이트, 다른 프로그램 | 합니다 | 합니다 | 전원만 |

**A1.** 연구 클론 폴더를 변수에 넣습니다. `<...>`를 연구 클론 폴더의 전체 경로로 바꿉니다. 파일 탐색기에서 그 폴더를 열고 주소 표시줄을 누르면 경로가 보입니다.

```powershell
$rc = "<연구 클론 폴더의 전체 경로>"
```

화면: 아무것도 나오지 않습니다.

**A2.** 그 폴더로 들어갑니다. 이 문서의 모든 줄은 이 폴더에서 실행합니다.

```powershell
cd $rc
```

화면: 프롬프트가 연구 클론 폴더 이름으로 끝납니다.

**A3.** 브랜치를 확인합니다.

```powershell
git branch --show-current
```

화면: `claude/amazing-gauss-tdiguu` 한 줄. 다르면 멈춥니다. 브랜치를 직접 바꾸지 않습니다.

**A4.** GitHub에서 받습니다. Claude가 올린 문서 커밋이 있으면 들어옵니다.

```powershell
git pull --ff-only
```

화면: `Already up to date.` 또는 `Fast-forward`가 들어 있는 줄들. `fatal:`이나 `error:`로 시작하는 줄이 있으면 멈추고 줄을 보냅니다. GitHub 로그인 창이 뜨면 7A.3에서 올릴 때 쓴 계정으로 로그인합니다. 시간: 5~20초.

**A5.** 바뀐 파일이나 새 파일이 없는지 봅니다.

```powershell
git status --porcelain --untracked-files=all
```

화면: 아무 줄도 나오지 않습니다. 러너는 `?? docs/nautilus_bridge/runs/`로 시작하는 줄만 받아 줍니다(아직 커밋하지 않은 run 폴더). 그 밖의 줄이 하나라도 있으면 러너가 R-01로 거부하므로, 멈추고 그 줄들을 보냅니다.

**A6.** 기준점이 HEAD와 같은지 봅니다.

```powershell
python -B -c "import subprocess; from core.quant import gate_ledger as g; a=g.repo_anchor(); h=subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True).stdout.strip(); print(a); print('anchor ok' if a=='git:'+h else 'anchor DIFFERENT')"
```

화면: `git:<40자>` 한 줄과 `anchor ok` 한 줄. 파일럿 기록에는 이 40자가 남습니다. 파일럿 1 때는, Claude가 새 커밋을 따로 알리지 않았다면 `git:8a8c2475b1a1480c7c6596a9d89619c755ab1e2a`입니다.

- 첫 줄이 `UNVERSIONED`이면 git이 브랜치 기록을 묶음 파일로 옮겨 둔 것일 수 있습니다. G절 R-02의 두 줄을 **한 번만** 실행하고 A5부터 다시 합니다. 그 두 줄은 빈 커밋 하나를 만들어 올리므로 HEAD의 40자가 바뀝니다. 새로 나온 A6의 두 줄을 Claude에게 보낼 때 그 사실을 함께 알립니다.
- 두 줄을 한 번 실행한 뒤에도 첫 줄이 `UNVERSIONED`이면 더 실행하지 않습니다. 멈추고 A6의 두 줄을 보냅니다. 이 한 줄 명령은 원인이 묶음 파일인지 다른 것(예: worktree)인지 가리지 못합니다.
- 첫 줄이 `git:`으로 시작하는데 둘째 줄이 `anchor DIFFERENT`이면 멈추고 두 줄을 보냅니다.
- 이 줄은 런북에 없습니다. 러너가 쓰는 함수 `repo_anchor()`를 그대로 불러 보는 줄로 Claude가 만들었고, Linux에서만 실행해 보았습니다.

**A7.** 실행 승인 문구가 지금 코드와 표에 맞는지 봅니다. 읽기만 하는 명령이며 아무것도 쓰지 않습니다. 파일럿 1 전에는 아래 줄을 씁니다.

```powershell
python -B -m tools.nautilus.runner --fingerprint --table docs\nautilus_bridge\registration\pilot1_E1_spy.json
```

화면(다섯 줄):

```text
table_sha256 d76d2d7301ffe92ca5198404ba1cbe07fd11890489c227e20cced8c4c4e07347
code_sha256 f995600b36c75523fe6079ab5209e60d94c2b5d0ac44437673fe4bc71c055620
host_fingerprint 4931117f(뒤 56자 생략)
owner_confirmed form: <name>, <YYYY-MM-DD>, table d76d2d7301ffe92c, code f995600b36c75523
STATUS OK exit=0 record=-
```

파일럿 2 전에는 표 이름만 바꿉니다.

```powershell
python -B -m tools.nautilus.runner --fingerprint --table docs\nautilus_bridge\registration\pilot2_C3_btcusd.json
```

화면: 첫 줄이 `table_sha256 e2ec073c309cbfc75ff476c03dda96337c45b46ce3f18129df96fb4d74462aba`, 둘째 줄은 위와 같고, 셋째 줄이 `host_fingerprint a4e80092`로 시작하고, 넷째 줄 끝이 `table e2ec073c309cbfc7, code f995600b36c75523`입니다.

- 볼 곳은 세 군데입니다. 넷째 줄 끝의 `table <16자>`, 같은 줄의 `code <16자>`, 셋째 줄 `host_fingerprint`의 앞 8자입니다. 셋 다 위와 같으면 실행 승인 문구가 유효합니다.
- 셋 가운데 하나라도 다르거나, 셋째 줄이 `host_fingerprint null (...)`로 나오거나, 다섯 줄이 아니면 멈추고 나온 줄을 모두 보냅니다. 표를 고치지 않습니다. 이 상태로 파일럿을 실행하면 러너가 거부합니다(R-11 또는 R-15).
- 다를 때의 뜻입니다. `code`가 다르면 A4에서 코드가 바뀐 커밋을 받은 것입니다. `table`이 다르면 표 파일이 바뀐 것입니다. `host_fingerprint`가 다르거나 `null`이면 원장이나 컴퓨터 이름이 7A 때와 다른 것입니다.
- 위의 64자 값은 Claude가 연구 브랜치 `8a8c247`의 파일로 Linux에서 다시 계산한 값입니다. Windows의 같은 커밋에서도 같아야 합니다(저장소는 줄바꿈을 바꾸지 않게 설정되어 있습니다). `host_fingerprint`의 앞 8자는 표에 적힌 값에서 읽었습니다.

**어떤 pull이 실행 승인을 그대로 두는가.** 코드 지문은 아래 27개 파일만으로 계산합니다. 이 파일들과 표 두 개가 그대로면, 다른 커밋을 받아도 승인은 유효합니다.

| 코드 지문에 들어가는 파일 | 개수 |
| --- | --- |
| `tools/nautilus/` 아래의 모든 `.py` | 7 |
| `tools/nautilus/golden/*.json` | 6 |
| `requirements-nautilus.txt` | 1 |
| 판정 코드: `core/quant/`의 `gate_stats.py`, `gate_ledger.py`, `cardp.py`, `cards.py`, `card_lines.py`, `instruments.py`, `costed.py`, `validate.py`, `strategies.py`, `gjr.py`와 `docs/macro_overlay_study.py` | 11 |
| `docs/asset_expansion_study.py`, `config.py` | 2 |

- 승인이 유지되는 pull: 스펙, 런북, 실행 기록 문서, `README.md`, `docs/nautilus_bridge/runs/`, `qa/acceptance_results.json`만 바뀐 커밋. 7A.3 커밋(`563db54`) 뒤로 연구 브랜치에서 바뀐 파일은 스펙 하나뿐입니다.
- 승인이 무효가 되는 pull: 위 27개 파일이나 표의 내용이 바뀐 커밋. 그때는 Windows 검증을 다시 하고 소유자가 `owner_confirmed`를 새로 적어야 합니다. Claude는 이 칸을 쓰지 않습니다.

**A8.** 이 네트워크가 1.1.1.1:443에 닿는지 봅니다. 러너는 전용 파이썬의 외부 연결이 막혀 있는지 시험하는데, 그 시험은 이 주소에 닿는 네트워크에서만 "방화벽 규칙 때문에 막혔다"를 가려낼 수 있습니다.

```powershell
python -B -c "import socket; socket.create_connection(('1.1.1.1',443),timeout=3).close(); print('reach ok')"
```

화면: `reach ok` 한 줄. `TimeoutError`나 `OSError`로 끝나는 여러 줄이 나오면 이 네트워크는 그 주소를 막고 있습니다. 다른 네트워크(예: 휴대폰 핫스팟)로 바꾸고 이 단계를 다시 합니다. 이 줄은 런북에 없고, 러너가 7A에서 쓴 연결 확인을 한 줄로 옮긴 것입니다(미검증).

**A9.** 방화벽 규칙이 그대로 있는지 봅니다.

```powershell
Get-NetFirewallRule -DisplayName QUANTGEN-nautilus-block-out | Format-List DisplayName, Enabled, Direction, Action, Profile
```

화면(11-04 인계 보고서에 남은 모양):

```text
DisplayName : QUANTGEN-nautilus-block-out
Enabled     : True
Direction   : Outbound
Action      : Block
Profile     : Any
```

규칙을 찾지 못했다는 빨간 오류가 나오거나, 아무것도 나오지 않거나, `Enabled`가 `False`이면 멈추고 화면을 보냅니다(G절 R-14). 규칙을 스스로 다시 만들지 않습니다. 규칙이 없을 때 이 줄이 어떤 화면을 내는지는 Windows에서 확인하지 못했습니다(미검증).

**A10.** 명령 없이 확인합니다.

- 전원 어댑터가 꽂혀 있습니다.
- Windows 업데이트를 일시 중지했습니다. 설정 화면에서 합니다. 명령은 없습니다(스펙도 미검증으로 적었습니다. 메뉴 이름도 미검증입니다).
- 이 PowerShell 창을 실행이 끝날 때까지 닫지 않습니다. 러너는 도는 동안 PC가 잠들지 않게 스스로 요청합니다.
- 실행 중에는 창 안을 마우스로 누르지 않기를 권합니다. Windows 콘솔은 글자를 선택하는 동안 프로그램의 출력을 멈춰 둘 수 있습니다(이 표의 권고. 이 PC에서는 미검증).
- 함께 돌리지 않습니다: 전체 검사(`python tests/run_all.py`), 동결 연구 판독(H2), 다른 러너, 공급사 대조 도구.
- **QUANTGEN 앱을 닫습니다.** 파일럿(B, D)과 전체 검사(E) 모두에서 지켜야 하는 규칙입니다.
  - 전체 검사(E): 검사 하나(T-HERM-02)가 검사 묶음이 시작할 때 찍어 둔 홈 폴더 원장 자리(`~/.nextgen/macro`)의 파일 크기와 수정 시각을 끝날 때의 것과 견줍니다. 그 사이에 앱이 그 자리에 쓰면 기록용 실행에 FAIL이 남습니다. 분리 스펙도 "검사가 도는 동안 앱을 실행하지 않는다"고 적었습니다.
  - 파일럿(B, D): 등록 뒤에 원장이 바뀌면 러너가 카드를 쓰지 않고 판정을 보류합니다(G-05). 그 기록이 기록 실행으로 남고, 다시 돌리려면 소유자 판정이 필요합니다.
  - 앱이 언제 원장에 쓰는지는 확인하지 못했습니다(미검증). 그래서 닫아 두는 것입니다.
- 방금 원장에 쓰는 작업(판독, 다른 파일럿)을 했다면 10분 기다립니다. 러너는 원장이 바뀐 지 600초가 안 되면 거부합니다.

## B. 파일럿 1 (Step 8, SPY, 12개 설정)

시작 조건은 "앉는 횟수" 표의 1번입니다. 러너는 ⑤-2 관문을 검사하지 않습니다. 순서를 지키는 것은 절차입니다.

**B1.** A1~A10을 합니다(A7은 파일럿 1의 표로).

**B2.** 파일럿 1을 실행합니다.

**이 줄은 한 번만 실행합니다. 되돌릴 수 없습니다.** 등록까지 간 실행은 그대로 기록 실행이 됩니다. 원장에 쓰인 줄은 지울 수 없습니다. 같은 표로 두 번째 실행을 하려면 소유자 판정과 사유 문장이 필요하고, 그것 없이는 러너가 거부합니다(R-17). 결과가 마음에 들지 않아도 다시 돌리지 않습니다.

```powershell
python -B -m tools.nautilus.runner --table docs/nautilus_bridge/registration/pilot1_E1_spy.json --of-record
```

러너가 하는 일은 이 순서입니다.

1. 같은 표의 다른 실행이 없는지, 원장이 최근 600초 안에 바뀌지 않았는지, 앞선 실행 기록이 있는지 봅니다.
2. 표, 실행 승인 문구, 원장, 이 PC의 지문을 확인합니다.
3. git 상태와 기준점을 확인합니다(A5, A6과 같은 검사).
4. 전용 파이썬 환경과 외부 연결 차단을 확인합니다.
5. 가격 파일과 금리 파일의 md5(파일 지문), 입력 값, 비용, 판정 기준, 원장 사슬을 확인합니다.
6. 여기까지 하나라도 어긋나면 **저장소(git)와 원장에 아무것도 쓰지 않고** 멈춥니다(종료 코드 2). 실행으로 세지 않습니다. git이 무시하는 잠금 파일 하나(`runs/.locks/` 아래)는 맨 처음에 생기며 그대로 둡니다.
7. 원장 E1에 12개 설정을 등록합니다. 이미 있는 설정은 그대로 둡니다. run 폴더는 이때 생깁니다.
8. 12개 설정을 비용 1배와 2배로 한 번씩, 모두 24번 실행합니다.
9. 패리티를 보고, 양쪽 계산을 채점하고, 둘이 일치하면 카드를 씁니다.

화면: 실행하는 동안에는 아무 줄도 나오지 않는 것이 정상입니다(러너 코드에 진행 줄이 없습니다). 끝나면 아래 네 줄이 나옵니다. 그 앞에 다른 프로그램의 경고 줄이 섞여 나올 수 있습니다(미검증).

```text
parity: hard_pass True; worst corr <숫자> (bar 0.9999, owner 0.99); worst abs dSR <숫자> (bar 0.01, owner 0.05)
trial counts: len_grid 12, family_n_raw <수>, market_n_raw <수>, U <수>, n_trials <수>
decisions: quantgen <판정>, nautilus <판정>
STATUS CARD_WRITTEN exit=0 record=<연구 클론>\docs\nautilus_bridge\runs\NB-<날짜와 시각>Z-d76d2d73\run.json
```

- 첫 줄의 `worst corr`는 두 계산의 일별 수익 상관 가운데 가장 낮은 값이고 0.9999 이상이어야 합니다. `worst abs dSR`는 샤프 비율(위험에 견준 수익을 재는 값) 차이 가운데 가장 큰 값이고 0.01 이하여야 합니다. `owner` 뒤의 숫자는 소유자가 처음 정한 기준입니다.
- `<판정>`은 `PASS`, `REVISE`, `REJECT`, `INSUFFICIENT_DATA` 가운데 하나입니다. **파일럿 1은 PASS가 아닐 것으로 미리 적어 두었습니다**(`INSUFFICIENT_DATA` 또는 `REJECT`). 이것은 규칙에 대한 결과이고 러너의 실패가 아닙니다. 마지막 줄이 `STATUS CARD_WRITTEN exit=0`이면 이 단계는 끝난 것입니다.
- `trial counts`는 시행 수입니다. 런북이 11-04 등록 줄에 기대한 값은 `len_grid 12, family_n_raw 12, market_n_raw 12, U 24, n_trials 36`입니다. 소유자가 그때 보고한 것은 "E1 원장 12줄"까지이고, `U 24`와 `n_trials 36`은 12줄에서 계산으로 따라 나오는 값입니다. E1 원장에 다른 줄이 더해지지 않았다면 같은 수가 나올 것으로 봅니다(그 화면을 본 기록이 없고 원장은 Claude가 볼 수 없어 미검증).
- 마지막 줄이 `STATUS WITHHELD exit=1 record=...`이면 판정 보류입니다. 그 앞에 `reason: ...` 줄들이 이유를 적습니다. 어느 경우든 **다시 돌리지 않고** B3으로 갑니다.
  - `hard_pass False`이면 `trial counts` 줄은 없고 `decisions: quantgen None, nautilus None`이 나옵니다. 걸린 검사가 `reason:` 줄에 적혀 있으면 스펙은 이것도 Step 8의 끝으로 인정합니다.
  - `hard_pass True`인데 보류이면, 스펙이 Step 8의 끝으로 인정하는 사유는 `decision mismatch`(두 계산의 판정이 다름) 하나입니다. 다른 사유(`benchmark test dropped`, `G-03`, `G-05`)는 스펙이 끝으로 적지 않았습니다. Claude가 읽고 보고한 뒤 소유자가 정합니다(K절 9번).
- 마지막 줄이 `STATUS REFUSED exit=2 record=-`이면 등록 전에 거부된 것입니다. G절을 봅니다.

끝의 네 줄과 `reason:` 줄은 나오자마자 복사해 메모장에 붙여 둡니다.

시간: 2~10분(추정). 30분이 지나도 `STATUS` 줄이 없으면 창을 닫지 말고 Ctrl+C도 누르지 말고 Claude에게 알립니다(이 표의 권고).

**B3.** 종료 코드를 봅니다.

```powershell
$LASTEXITCODE
```

화면: `0`(카드 작성) 또는 `1`(판정 보류). `2`, `3`, `4`, `5`이면 B4~B11을 하지 않고 G절을 봅니다.

**B4.** 새로 생긴 파일을 봅니다.

```powershell
git status --porcelain --untracked-files=all
```

화면(카드가 쓰였을 때 두 줄, 판정 보류였으면 `run.json` 한 줄):

```text
?? docs/nautilus_bridge/runs/NB-<날짜와 시각>Z-d76d2d73/NB_E1_trend_spy.json
?? docs/nautilus_bridge/runs/NB-<날짜와 시각>Z-d76d2d73/run.json
```

다른 모양의 줄이 하나라도 있으면 멈추고 줄들을 보냅니다.

**B5.** run 폴더 경로를 변수에 넣습니다. `<...>`를 B4에 나온 `NB-`로 시작하는 폴더 이름으로 바꿉니다.

```powershell
$run = "docs/nautilus_bridge/runs/<NB-로 시작하는 폴더 이름>"
```

화면: 아무것도 나오지 않습니다.

**B6.** 실행 기록을 커밋 대상에 담습니다.

```powershell
git add "$run/run.json"
```

화면: 아무것도 나오지 않습니다.

**B7.** 카드를 담습니다. B4에 카드 줄이 있었을 때만 실행합니다.

```powershell
git add "$run/NB_E1_trend_spy.json"
```

화면: 아무것도 나오지 않습니다.

**B8.** 담긴 것을 확인합니다.

```powershell
git status --short
```

화면: 모든 줄이 `A  docs/nautilus_bridge/runs/NB-`로 시작하고 폴더 이름이 `-d76d2d73`으로 끝납니다. 한 줄 또는 두 줄입니다. 다른 줄이 있으면 멈추고 줄들을 보냅니다.

**B9.** 커밋합니다.

```powershell
git commit -m "nautilus: Step 8 pilot 1 run folder (E1-SPY)"
```

화면: `file changed` 또는 `files changed`가 들어 있는 줄(파일이 하나면 `1 file changed`)과 `create mode 100644 docs/nautilus_bridge/runs/NB-...` 줄들. 다르면 멈추고 줄을 보냅니다.

**B10.** GitHub에 올립니다.

```powershell
git push
```

화면: 끝에서 두 번째 줄이 `To `로 시작하고, 마지막 줄이 `<옛 커밋>..<새 커밋>  claude/amazing-gauss-tdiguu -> claude/amazing-gauss-tdiguu` 모양입니다. `rejected`나 `fatal:`이 있으면 멈추고 줄을 보냅니다. GitHub 로그인 창이 뜨면 7A.3에서 올릴 때 쓴 계정으로 로그인합니다. 시간: 5~30초.

**B11.** 남은 것이 없는지 봅니다.

```powershell
git status --porcelain --untracked-files=all
```

화면: 아무 줄도 나오지 않습니다.

런북에는 B4~B11의 줄이 없습니다. 스펙의 "소유자가 run 폴더를 커밋하고 push한다"와 7A.3의 규칙(경로를 하나씩 적고 `git add -A`는 쓰지 않음)에서 Claude가 끌어낸 줄입니다. 스크래치 git 저장소에서 화면 모양을 확인했습니다.

## C. Claude의 판독을 기다립니다

Claude는 올라온 run 폴더를 읽고 채팅으로 아래를 알려 드립니다. 같은 내용이 Step 10 마감 기록에 들어갑니다.

1. 상태(`CARD_WRITTEN` 또는 `WITHHELD`)와 보류 사유.
2. `hard_pass` 값, 그리고 12개 설정과 비용 두 단계 각각의 hard 검사 결과(P0b, P1, P2, P3, P4, P7, P12, P13).
3. 경고(P5, P6, P8, P9, P10). 경고는 판정을 보류시키지 않습니다.
4. 시행 수 다섯 값.
5. 양쪽 계산의 판정과 일치 여부, 카드의 판정.
6. 다음에 할 일: "파일럿 1이 `hard_pass True`이고 BTC-USD 관문을 통과했으므로 파일럿 2를 시작해도 됩니다" 또는 "소유자 판정이 필요합니다". 앞의 문장에는 두 가지가 모두 들어 있어야 합니다. BTC-USD 관문이 빠져 있으면 파일럿 2를 시작하지 않고 되묻습니다.

결과에 따라 소유자가 정할 것은 아래와 같습니다.

| 결과 | 뜻 | 소유자가 정할 것 |
| --- | --- | --- |
| `CARD_WRITTEN`, 카드 판정이 PASS가 아님 | 규칙에 대한 결과입니다. 파일럿 1에서는 예상한 결과입니다. | 없습니다. 결과를 본 뒤 설정을 바꾸면 새 시행이 되므로 표를 고치지 않습니다. 파일럿 2로 갑니다. |
| `WITHHELD`인데 `hard_pass True` | 패리티는 통과했고 카드는 없습니다. 사유의 예: `decision mismatch`(두 계산의 판정이 다름), `benchmark test dropped`, `ledger moved after registration`(실행 중 원장이 바뀜), 채점 계산의 오류. | 러너는 파일럿 2를 막지 않습니다. 스펙이 Step 8의 끝으로 인정하는 것은 `decision mismatch`뿐입니다. 다른 사유일 때 Step 8을 끝난 것으로 볼지, 원인을 더 볼지, 다시 돌릴지는 Claude가 정리해 드린 뒤 정하십니다(K절 9번). 다시 돌리려면 사유 문장이 필요합니다. |
| `WITHHELD`이고 `hard_pass False` | hard 검사가 실패했거나 실행이 무효였습니다. 러너가 파일럿 2를 R-11로 막습니다. | 무엇을 고쳐 어떻게 다시 갈지, 파일럿 2 없이 마감할지는 문서에 정해진 절차가 없습니다(K절 1번). 스펙은 사유가 모두 `C-06`(실행 프로그램이 죽었거나 시간 초과)이면 같은 명령을 다시 받아 준다고 적었습니다. 그런데 코드를 읽어 보면 그 경우에도 `P13:`으로 시작하는 사유 줄이 함께 붙어서, 러너가 재실행 플래그와 사유 문장을 요구할 것으로 보입니다(실제 실행으로는 미검증). 어느 쪽이든 Claude 답을 먼저 기다립니다. |
| 종료 코드 3, 4, 5 | G절에 있습니다. | G절에 있습니다. |

## D. 파일럿 2 (Step 9, BTC-USD, 5개 설정)

시작 조건은 "앉는 횟수" 표의 2번입니다. 러너가 직접 확인하는 조건은 아래 셋입니다. 하나라도 어긋나면 등록 전에 거부합니다(R-11, R-15, R-09).

- `docs/nautilus_bridge/runs/` 안에 파일럿 1의 기록이 있고, 그 기록의 `hard_pass`가 참이고, 등록 행이 12개이고, 코드 지문이 지금과 같습니다. 그래서 파일럿 1의 run 폴더를 지우거나 옮기면 안 됩니다.
- 표가 가리키는 기준 카드 파일의 md5가 표에 적힌 값과 같습니다.
- 원장 C3가 있고, 줄이 있고, 사슬이 맞고, 이 PC의 지문이 표와 같습니다.

BTC-USD 대조 관문은 러너가 검사하지 않습니다. 순서를 지키는 것은 절차입니다.

**D1.** A1~A10을 합니다(A7은 파일럿 2의 표로).

**D2.** 파일럿 2를 실행합니다.

**이 줄은 한 번만 실행합니다. 되돌릴 수 없습니다.** 등록까지 간 실행은 그대로 기록 실행이 됩니다. 원장 C3에 5개 설정이 등록되고, 원장에 없던 설정은 새 줄로 영구히 남습니다(많아야 5줄). 원장에 쓰인 줄은 지울 수 없습니다. 같은 표로 두 번째 실행을 하려면 소유자 판정과 사유 문장이 필요하고, 그것 없이는 러너가 거부합니다(R-17).

```powershell
python -B -m tools.nautilus.runner --table docs/nautilus_bridge/registration/pilot2_C3_btcusd.json --of-record
```

스펙의 Step 9 줄에는 이 명령이 글자로 적혀 있지 않습니다. 러너의 사용법 줄과 런북이 쓰는 표 경로에서 끌어낸 명령입니다. 러너는 B2와 같은 순서로 확인한 뒤 원장 C3에 5개 설정을 등록하고, 비용 10bp와 20bp로 한 번씩, 모두 10번 실행합니다. 금리 파일은 쓰지 않습니다.

화면(끝의 네 줄):

```text
parity: hard_pass True; worst corr <숫자> (bar 0.9999, owner 0.99); worst abs dSR <숫자> (bar 0.01, owner 0.05)
trial counts: len_grid 5, family_n_raw <수>, market_n_raw <수>, U <수>, n_trials <수>
decisions: quantgen <판정>, nautilus <판정>
STATUS CARD_WRITTEN exit=0 record=<연구 클론>\docs\nautilus_bridge\runs\NB-<날짜와 시각>Z-e2ec073c\run.json
```

- 패리티가 통과하고 저장된 카드가 다시 만들어지면 기대 판정은 `PASS`입니다. `U`는 많아야 11입니다.
- `STATUS WITHHELD exit=1`에 `reason: G-08: reference drift: ...`가 나오면 QUANTGEN 쪽 점수가 저장된 카드와 달랐다는 뜻입니다. 이것도 Step 9의 끝으로 인정됩니다. 다시 돌리지 않습니다.
- 그 밖의 `STATUS WITHHELD exit=1`은 B2에 적은 것과 같습니다. 어느 경우든 다시 돌리지 않고 D3으로 갑니다.
- `R-11: of-record C3-BTCUSD needs an of-record E1-SPY record ...`가 나오면 파일럿 1의 통과 기록을 찾지 못한 것입니다. 멈추고 줄을 보냅니다.

끝의 네 줄과 `reason:` 줄은 나오자마자 복사해 메모장에 붙여 둡니다.

시간: 1~5분(추정). 30분이 지나도 `STATUS` 줄이 없으면 창을 닫지 말고 Ctrl+C도 누르지 말고 Claude에게 알립니다(이 표의 권고).

**D3.** 종료 코드를 봅니다.

```powershell
$LASTEXITCODE
```

화면: `0`(카드 작성) 또는 `1`(판정 보류). `2`, `3`, `4`, `5`이면 D4~D11을 하지 않고 G절을 봅니다.

**D4.** 새로 생긴 파일을 봅니다.

```powershell
git status --porcelain --untracked-files=all
```

화면(카드가 쓰였을 때 두 줄, 판정 보류였으면 `run.json` 한 줄):

```text
?? docs/nautilus_bridge/runs/NB-<날짜와 시각>Z-e2ec073c/NB_C3_crypto_trend_btcusd.json
?? docs/nautilus_bridge/runs/NB-<날짜와 시각>Z-e2ec073c/run.json
```

다른 모양의 줄이 하나라도 있으면 멈추고 줄들을 보냅니다. 폴더 이름이 `-d76d2d73`으로 끝나면 파일럿 1의 폴더입니다. 그것은 B에서 이미 올렸어야 하므로, 여기에 나오면 멈춥니다.

**D5.** run 폴더 경로를 변수에 넣습니다. `<...>`를 D4에 나온, `-e2ec073c`로 끝나는 폴더 이름으로 바꿉니다. 같은 창을 계속 쓰고 있다면 `$run`에는 아직 파일럿 1의 폴더가 들어 있으니, 이 단계를 건너뛰지 않습니다.

```powershell
$run = "docs/nautilus_bridge/runs/<NB-로 시작하는 폴더 이름>"
```

화면: 아무것도 나오지 않습니다.

**D6.** 실행 기록을 담습니다.

```powershell
git add "$run/run.json"
```

화면: 아무것도 나오지 않습니다.

**D7.** 카드를 담습니다. D4에 카드 줄이 있었을 때만 실행합니다.

```powershell
git add "$run/NB_C3_crypto_trend_btcusd.json"
```

화면: 아무것도 나오지 않습니다.

**D8.** 담긴 것을 확인합니다.

```powershell
git status --short
```

화면: 모든 줄이 `A  docs/nautilus_bridge/runs/NB-`로 시작하고 폴더 이름이 `-e2ec073c`로 끝납니다. 한 줄 또는 두 줄입니다. 다른 줄이 있으면 멈추고 줄들을 보냅니다.

**D9.** 커밋합니다.

```powershell
git commit -m "nautilus: Step 9 pilot 2 run folder (C3-BTCUSD)"
```

화면: `file changed` 또는 `files changed`가 들어 있는 줄과 `create mode 100644 docs/nautilus_bridge/runs/NB-...` 줄들. 다르면 멈추고 줄을 보냅니다.

**D10.** GitHub에 올립니다.

```powershell
git push
```

화면: 끝에서 두 번째 줄이 `To `로 시작하고, 마지막 줄이 `<옛 커밋>..<새 커밋>  claude/amazing-gauss-tdiguu -> claude/amazing-gauss-tdiguu` 모양입니다. `rejected`나 `fatal:`이 있으면 멈추고 줄을 보냅니다. 시간: 5~30초.

**D11.** 남은 것이 없는지 봅니다.

```powershell
git status --porcelain --untracked-files=all
```

화면: 아무 줄도 나오지 않습니다.

그다음 Claude의 판독을 기다립니다. 내용은 C절과 같고, 저장된 카드와 비교한 결과가 더해집니다.

## E. Windows 전체 검사 (Step 10 앞부분)

시작 조건은 "앉는 횟수" 표의 3번입니다. 전체 검사는 파일럿과 겹치면 안 됩니다. 검사가 도는 동안 원장 폴더의 상태를 찍어 두기 때문입니다.

**E1.** A1~A5, A9, A10을 합니다. A8도 권합니다.

**E2.** 전체 검사를 실행합니다. 뒤에 아무것도 붙이지 않습니다.

```powershell
python tests/run_all.py
```

화면: 검사마다 `PASS <이름>`, `NOT_RUN <이름> <이유>`, `FAIL <이름> <내용>` 가운데 한 줄씩 나오고, 마지막 줄이 아래 모양입니다.

```text
<통과 수>/<전체 수> passed, <실패 수> failed, <미실행 수> not run; <연구 클론>\qa\acceptance_results.json
```

- 필요한 것은 `0 failed`입니다.
- 11-04에는 `844/964 passed, 0 failed, 120 not run`이었습니다. 그 뒤 연구 브랜치의 코드는 바뀌지 않았으므로 같은 964행을 예상합니다. 다만 파일럿으로 원장과 run 폴더가 늘어난 뒤의 전체 검사는 이번이 처음이라 결과는 미검증입니다.
- `--suite`나 `--milestone`을 붙이면 결과 파일이 그 묶음의 행만으로 덮어써집니다. 기록용 실행에는 붙이지 않습니다.

마지막 줄은 나오자마자 복사해 메모장에 붙여 둡니다.

시간: 약 16분(11-04 기록의 소요 시간 합 958초. 벽시계 시간은 기록에 없습니다).

**E3.** 종료 코드를 봅니다.

```powershell
$LASTEXITCODE
```

화면: `0`. `1`이면 FAIL이 있다는 뜻입니다. `1`이어도 E4와 E5는 실행합니다(읽기만 하는 줄입니다). 커밋은 하지 않습니다.

**E4.** 결과 파일을 세 줄로 요약합니다.

```powershell
python -B -c "import json, collections; rows=json.load(open('qa/acceptance_results.json', encoding='utf-8')); print(len(rows), dict(collections.Counter(r['status'] for r in rows))); print('nautilus', dict(collections.Counter(r['status'] for r in rows if r['test'].startswith('nautilus/')))); print('guard', dict(collections.Counter(r['status'] for r in rows if r['test'].startswith('guard/'))))"
```

화면(11-04 결과로 실행했을 때의 모양):

```text
964 {'PASS': 844, 'NOT_RUN': 120}
nautilus {'PASS': 57}
guard {'PASS': 5}
```

아래 넷이 모두 맞을 때만 E6(커밋)으로 갑니다. 중괄호 안의 순서는 달라도 됩니다. 숫자와 낱말을 봅니다.

1. 첫 줄에 `'FAIL'`이 없습니다.
2. 첫 줄의 맨 앞 숫자가 `964`입니다.
3. `nautilus` 줄에 `'NOT_RUN'`이 없습니다. `'NOT_RUN': 1`이면 E5에서 그 이름을 봅니다.
4. `guard` 줄이 `{'PASS': 5}`입니다.

하나라도 어긋나면 E5를 실행합니다. 넷이 모두 맞으면 E5를 건너뛰고 E6으로 갑니다.

- 까닭: Step 10은 "FAIL 0, nautilus 묶음이 집계에 들어감, 동결 연구 보호 검사(guard)의 (a), (b), (d) 통과"를 요구합니다. FAIL이 없어도 nautilus나 guard 검사가 실행되지 않았다면(NOT_RUN) 그 조건을 채우지 못합니다.
- 행 수가 964가 아니면 실패는 아닐 수 있지만 예상과 다릅니다. Claude가 까닭을 본 뒤 커밋해도 되는지 답합니다.

**E5.** E4의 넷 가운데 어긋난 것이 있을 때만 실행합니다. FAIL 줄과, `nautilus`와 `guard`에서 PASS가 아닌 줄을 뽑습니다. 읽기만 합니다.

```powershell
python -B -c "import json; rows=json.load(open('qa/acceptance_results.json', encoding='utf-8')); bad=[r for r in rows if r['status']=='FAIL' or (r['test'].startswith(('nautilus/','guard/')) and r['status']!='PASS')]; [print(r['status'], r['test'], (r.get('detail') or r.get('reason') or '')[:200]) for r in bad]; print('listed', len(bad))"
```

화면: `<상태> <이름> <내용>` 줄들과 마지막 줄 `listed <줄 수>`.

- 나온 줄이 `NOT_RUN nautilus/test_l2_05b_input_linked_to_env_refused ...` 한 줄뿐이고(`listed 1`) E4의 1, 2, 4번이 맞으면 E6으로 갑니다. 이 한 건은 7A에서 허용한 것입니다(Windows 개발자 모드가 꺼져 있으면 실행되지 않는 검사).
- 그 밖에는 **여기서 멈춥니다.** 커밋하지 않고, 파일을 되돌리지도 않습니다. E2의 마지막 줄, E4의 세 줄, 이 줄들을 Claude에게 보냅니다. 내용 칸에 `.env`의 변수 이름이 나올 수 있습니다. 이름은 보내도 되고, 값은 나오지 않습니다.

**E6.** 바뀐 파일을 봅니다.

```powershell
git status --porcelain --untracked-files=all
```

화면: ` M qa/acceptance_results.json` 한 줄. 다른 줄이 있으면 멈추고 줄들을 보냅니다. 아무 줄도 없으면 결과 파일이 11-04의 것과 글자 하나까지 같다는 뜻인데, 실행 시간이 매번 달라 그럴 수 없으므로 이때도 멈춥니다.

**E7.** 결과 파일을 담습니다.

```powershell
git add qa/acceptance_results.json
```

화면: 아무것도 나오지 않습니다.

**E8.** 담긴 것을 확인합니다.

```powershell
git status --short
```

화면: `M  qa/acceptance_results.json` 한 줄. 다른 줄이 있으면 멈추고 줄들을 보냅니다.

**E9.** 커밋합니다.

```powershell
git commit -m "nautilus: Step 10 Windows full run (win_amd64)"
```

화면: `1 file changed`가 들어 있는 줄. 다르면 멈추고 줄을 보냅니다.

**E10.** GitHub에 올립니다.

```powershell
git push
```

화면: 끝에서 두 번째 줄이 `To `로 시작하고, 마지막 줄이 `<옛 커밋>..<새 커밋>  claude/amazing-gauss-tdiguu -> claude/amazing-gauss-tdiguu` 모양입니다. `rejected`나 `fatal:`이 있으면 멈추고 줄을 보냅니다. 시간: 5~30초.

**E11.** 남은 것이 없는지 봅니다.

```powershell
git status --porcelain --untracked-files=all
```

화면: 아무 줄도 나오지 않습니다.

- `qa/acceptance_results.json`은 소유자의 Windows 전체 실행에서만 커밋합니다. Claude는 이 파일을 쓰지 않습니다.
- `README.md`의 검사 개수와 Total 줄은 이 표에서 소유자가 고치지 않습니다. 누가 고치는지는 문서끼리 달라 아직 정해지지 않았습니다(K절 5번).
- E6~E10의 커밋 줄도 런북에 없고, 7A.3의 같은 파일 커밋에서 끌어낸 것입니다. E4와 E5의 요약 줄은 Claude가 만들었습니다.

## F. Claude의 마감 기록과 합치기가 끝난 뒤: 받아서 확인하고 main에 병합

Claude가 먼저 하는 일입니다(판정 P2, P3).

1. 마감 기록, 스펙의 자료 접근 이력, ⑤-2 요약 사본을 연구 브랜치에 커밋합니다. 범위는 P2가 정한 네 가지입니다(마감 기록, 스펙, `README.md`, 실행 기록 폴더).
2. Step 10의 확인을 합니다. 파일럿 기록에 남은 가장 이른 HEAD와 비교해, 바뀐 경로가 허용된 것뿐인지 봅니다.
3. 그 확인 뒤에 main을 연구 브랜치에 합쳐 충돌을 풀고, 캐시 폴더를 받지 않은 사본에서 전체 검사를 돌립니다. 그 전에는 main을 연구 브랜치에 합치지 않습니다(판정 H-D5).
4. "병합해도 됩니다"와 연구 브랜치 끝 커밋 번호(40자)를 알려 드립니다.

시작 조건을 다시 적습니다.

- Claude가 "병합해도 됩니다"와 40자를 알렸습니다.
- K절 2번(합친 뒤 Windows 전체 검사를 다시 할지)과 3번(11-04 서명 문장이 합친 뒤의 상태에도 적용되는지)에 소유자 판정이 나 있습니다. 2번을 "다시 한다"로 정하셨다면 F를 시작하지 않습니다. Claude가 순서를 다시 적어 드립니다.
- Claude가 알린 때부터 F12가 끝날 때까지 main에 다른 PR을 병합하지 않습니다. 다른 Claude나 GPT 세션에도 시키지 않습니다. 그 사이에 main이 움직이면 F4나 F8에서 멈추게 됩니다.

소유자가 하는 일입니다.

**F1.** A1~A5를 합니다. A4에서 Claude의 커밋들이 `Fast-forward`로 들어옵니다. A5는 아무 줄도 없어야 합니다.

**F2.** 받은 끝 커밋이 Claude가 알려 준 것과 같은지 봅니다.

```powershell
git rev-parse HEAD
```

화면: Claude가 알려 준 40자와 같은 한 줄. 다르면 멈춥니다(올리지 않은 커밋이 이 PC에 있거나 덜 받은 것입니다). 이 40자를 메모장에 적어 둡니다. F11에서 다시 씁니다.

**F3.** GitHub의 최신 상태를 받습니다(런북 7A.2의 첫 줄과 같습니다).

```powershell
git fetch origin; if ($LASTEXITCODE) { throw "fetch" }
```

화면: 아무것도 나오지 않거나 받은 내용 몇 줄. 빨간 글씨로 `fetch`가 나오면 멈추고 줄을 보냅니다. 시간: 5~20초.

**F4.** main이 연구 브랜치에 모두 들어 있는지 봅니다(런북 7A.2의 둘째 줄).

```powershell
git merge-base --is-ancestor origin/main origin/claude/amazing-gauss-tdiguu; if ($LASTEXITCODE) { throw "main has moved: ask Claude to merge origin/main into the branch first" }
```

화면: 아무것도 나오지 않습니다. 빨간 글씨로 `main has moved`가 나오면 Claude가 합친 뒤 main이 또 움직인 것입니다. 멈추고 알립니다.

**F5.** 이 PC의 main에 올리지 않은 커밋이 없는지 봅니다(런북 7A.2의 셋째 줄).

```powershell
git merge-base --is-ancestor main origin/claude/amazing-gauss-tdiguu; if ($LASTEXITCODE) { throw "local main has unpushed commits: push them, then ask Claude to merge origin/main" }
```

화면: 아무것도 나오지 않습니다. 빨간 글씨가 나오면 멈추고 알립니다. 빨간 글씨에 적힌 대로 스스로 push하지 않습니다.

여기부터가 런북의 병합 네 줄입니다(F6, F7, F10, F12). F8, F9, F11, F13은 Claude가 더한 확인 줄이고 읽기만 합니다.

main에 있는 동안(F6부터 F10까지) 지킬 것입니다.

- `git add`를 실행하지 않습니다.
- `git status`를 실행하면 `?? docs/nautilus_bridge/runs/.locks/...`나 `?? docs/nautilus_bridge/runs/A2-E1-...` 줄이 보일 수 있습니다. 이 파일들을 가려 주는 설정 파일이 연구 브랜치에만 있고 main에는 아직 없어서입니다. 담지도 지우지도 않습니다. 병합이 끝나면 다시 보이지 않습니다.

**F6.** main으로 옮깁니다.

```powershell
git switch main
```

화면: `Switched to branch 'main'`. 그 아래에 main이 뒤처져 있다는 안내가 나올 수 있습니다. `error:`나 `fatal:`로 시작하는 줄이 있으면 멈추고 줄을 보냅니다.

**F7.** main을 최신으로 받습니다.

```powershell
git pull --ff-only
```

화면: `Fast-forward`가 들어 있는 줄들 또는 `Already up to date.` `fatal:`이나 `error:`로 시작하는 줄이 있으면 멈추고 줄을 보냅니다. 시간: 5~30초.

**F8.** 받은 main이 연구 브랜치에 모두 들어 있는지 한 번 더 봅니다.

```powershell
git merge-base --is-ancestor main claude/amazing-gauss-tdiguu; if ($LASTEXITCODE) { throw "main moved after Claude's merge: stop and ask Claude" }
```

화면: 아무것도 나오지 않습니다. 빨간 글씨가 나오면 병합하지 않습니다. `git switch claude/amazing-gauss-tdiguu`로 돌아가고 Claude에게 알립니다.

**F9.** 병합 때 어떤 편집기가 뜨는지 미리 봅니다. 읽기만 하는 줄입니다.

```powershell
git var GIT_EDITOR
```

화면: 편집기 이름이나 경로 한 줄. 이 줄을 보고 F10에서 할 일을 아래 표에서 찾아 둡니다. F10의 병합 줄은 메시지를 `-m`으로 주지 않으므로, git이 병합 메시지를 보여 주는 편집기를 엽니다. 지금까지의 커밋은 모두 `-m`을 썼기 때문에 이 PC에서 이 편집기가 뜨는 것은 처음일 수 있습니다.

| F9에 나온 줄 | F10에서 뜨는 것 | 할 일 |
| --- | --- | --- |
| `vi` 또는 `vim`이 들어 있음 | PowerShell 창 안의 화면이 바뀌고, 맨 위에 `Merge branch 'claude/amazing-gauss-tdiguu'`, 그 아래에 `#`로 시작하는 줄들이 보입니다. | 아무것도 고치지 않습니다. Esc를 한 번 누르고, `:wq`를 치고(쌍점, w, q), Enter를 누릅니다. |
| `notepad`가 들어 있음 | 메모장 창이 따로 뜹니다. | 아무것도 고치지 않고 그 창을 닫습니다. |
| `code`가 들어 있음 | VS Code에 `MERGE_MSG` 탭이 뜹니다. | 아무것도 고치지 않고 그 탭을 닫습니다. |
| 그 밖의 줄 | 알 수 없습니다. | F10을 실행하지 않습니다. F9의 줄을 Claude에게 보내고 기다립니다. |

- 어떤 편집기가 뜨는지, 위의 키가 이 PC에서 그대로 통하는지는 확인하지 못했습니다(미검증). Git for Windows의 기본 편집기는 보통 Vim입니다.
- 편집기에서 어떻게 할지 모르겠으면 **PowerShell 창을 닫지 않습니다.** 창을 닫으면 main이 병합 도중의 상태로 남습니다. 그 창만 사진으로 찍어 Claude에게 보내고 기다립니다.
- 편집기가 아예 뜨지 않게 하는 방법(`--no-edit`)이 있지만 런북의 줄과 글자가 달라집니다. 쓸지는 K절 8번에서 정하십니다. 정하시기 전에는 런북의 줄 그대로 씁니다.

**F10.** 병합 커밋을 만듭니다.

```powershell
git merge --no-ff claude/amazing-gauss-tdiguu
```

화면: 편집기가 뜨면 F9의 표대로 합니다. 편집기가 닫힌 뒤 출력의 **첫 줄**이 `Merge made by the 'ort' strategy.`입니다(따옴표 안의 낱말은 git 버전에 따라 다를 수 있습니다. 미검증). 그 아래로 바뀐 파일 목록이 수백 줄 이어지고, 마지막 줄들은 ` create mode 100644 ...`로 시작합니다. 첫 줄은 화면 위로 밀려 올라가 보이지 않을 수 있습니다. 찾지 않아도 됩니다. F11이 확인해 줍니다.

- `CONFLICT`가 들어 있는 줄이 나오면 **아무것도 더 실행하지 않고** 화면의 줄을 Claude에게 보냅니다. 되돌리는 방법은 문서에 정해져 있지 않아, Claude가 그때 상태를 보고 안내합니다.
- `Already up to date.`가 나오면 병합할 것이 없다는 뜻입니다. 예상과 다르므로 멈추고 줄을 보냅니다.

**F11.** 만든 병합 커밋을 확인합니다. 아직 올리지 않았으므로 여기까지는 이 PC 안의 일입니다.

```powershell
git log -1 --format="%H %P"
```

화면: 40자 세 개가 한 줄에 나옵니다(병합 커밋, main 쪽 부모, 연구 브랜치 쪽 부모). **셋째 40자가 F2에서 적어 둔 40자와 같아야 합니다.**

- 40자가 두 개만 나오면 병합 커밋이 아닙니다. F12를 하지 않고 줄을 보냅니다.
- 셋째 40자가 F2의 것과 다르면 F12를 하지 않고 줄을 보냅니다.

**F12.** main을 GitHub에 올립니다.

**F11까지는 이 PC 안의 일입니다. 이 줄은 GitHub의 main을 바꾸며 되돌릴 수 없습니다.** F11의 두 조건이 맞을 때만 실행합니다.

```powershell
git push origin main
```

화면: 마지막 줄이 `<옛 커밋>..<새 커밋>  main -> main` 모양입니다. `rejected`가 나오면 멈추고 줄을 보냅니다. main에 직접 올리는 것이 저장소 설정으로 막혀 있는지는 확인하지 못했습니다(미검증). 시간: 10~60초.

**F13.** 남은 것이 없는지 봅니다.

```powershell
git status --porcelain --untracked-files=all
```

화면: 아무 줄도 나오지 않습니다. 줄이 나오면 담지도 지우지도 말고 줄들을 보냅니다.

올린 뒤입니다.

- GitHub에 빨간 X 표시가 뜨거나 실패 메일이 올 수 있습니다. 연습 병합에서는 준법 문서 점검(바뀐 파일을 준법 문서와 다시 맞춰 봤는지 확인하는 자동 검사)이 검토 기록을 새로 고치기 전에는 실패했습니다. 그 정리를 Claude의 합치기 안에 미리 넣을지는 K절 10번입니다. 넣지 않았다면 병합 뒤에 Claude가 따로 올립니다. 실제 GitHub에서 어떻게 보이는지는 미검증입니다.
- 빨간 표시가 떠도 아무것도 되돌리지 않습니다. Claude에게 알립니다.
- 이 PC의 폴더는 main에 그대로 둡니다. 브랜치를 다시 바꾸지 않습니다(이 표의 권고).

main에서 하지 않는 것입니다.

- squash 병합(여러 커밋을 하나로 뭉치는 병합)과 rebase(커밋을 다시 쓰는 방식)를 하지 않습니다. 소유자가 직접 만드는 병합 커밋이어야 합니다.
- 연구 브랜치를 지우지 않습니다. PC에서도 GitHub에서도 그대로 둡니다. 원장 줄에 적힌 기준점 커밋에 계속 닿을 수 있어야 하기 때문입니다.
- GitHub 화면의 병합 단추는 런북에 없습니다. 이 표는 런북의 네 줄만 씁니다.
- `git push --force`, `git add -A`, 폴더 전체 `checkout`, `reset`, `stash`, `clean`을 쓰지 않습니다.

참고입니다.

- 오늘(origin/main `83046c1`, 2026-11-11 13:53 KST) 기준으로 main은 코드 지문에 들어가는 27개 파일을 하나도 바꾸지 않았습니다. 그 목록을 정하는 `core/quant/gate_package.py`와 `qa/acceptance_results.json`도 바꾸지 않았고, `tools/nautilus/` 아래에 파일을 더하지도 않았습니다(두 브랜치가 갈라진 커밋 `bb35b3b`부터 비교). 그래서 Claude가 main을 합친 뒤에도 코드 지문은 그대로일 것으로 봅니다. main은 이 문서를 쓰는 동안에도 두 번 움직였으므로(`96cca1f`에서 `9fc3817`로, 다시 `83046c1`로), 합치는 날의 main으로 다시 확인해야 합니다(미검증).
- Claude가 미리 해 본 연습 병합의 기록은 `docs/product/STEP10_MERGE_REHEARSAL_2026-11-11.md`에 있습니다. 충돌 다섯 개와 소유자가 정해 주실 화면 선택이 거기에 적혀 있습니다.

## G. 거부 코드와 종료 코드

러너의 마지막 줄은 `STATUS <상태> exit=<숫자> record=<경로 또는 ->`입니다. 플래그 철자가 틀렸을 때만 이 줄이 없습니다. 거부될 때는 그 위에 이유 줄과 `remedy:` 줄이 나옵니다. 예:

```text
R-16: C:\Users\...\.nextgen\macro\ledgers\C3.jsonl was modified less than 600 s ago; wait 412 s
remedy: wait the printed seconds, or end the runner holding the printed lock
STATUS REFUSED exit=2 record=-
```

**`remedy:` 줄은 따라 하지 않습니다.** 러너가 Claude에게 읽으라고 찍는 줄입니다. 이 문서가 금지한 일을 시키는 것도 있습니다. 예를 들어 R-01의 `remedy:`는 "경로를 커밋하거나 지우라"이고, R-11은 "표의 칸을 고치라", R-17은 "재실행 플래그를 붙이라", R-03은 `pip uninstall` 줄입니다. 화면의 `remedy:`와 아래 표가 다르면 **표의 "어떻게 하나" 칸을 따릅니다.** 표가 소유자 스스로 하라고 적은 것은 둘뿐입니다. R-16(기다린 뒤 같은 줄을 다시 붙여 넣기)과, R-02에서 메시지에 `packed`가 있을 때의 두 줄입니다.

**종료 코드**

| 마지막 줄 | 종료 코드 | 무슨 뜻 | 어떻게 하나 |
| --- | --- | --- | --- |
| `STATUS CARD_WRITTEN exit=0 record=...\run.json` | 0 | 패리티가 통과했고 양쪽 판정이 일치해 카드가 쓰였습니다. | run 폴더를 커밋하고 올립니다. |
| `STATUS OK exit=0 record=-` | 0 | `--fingerprint`가 끝났습니다. | 다음 단계로 갑니다. |
| `STATUS WITHHELD exit=1 record=...\run.json` | 1 | 판정 보류입니다. 카드는 없습니다. 등록한 줄은 원장에 남습니다. | 다시 돌리지 않습니다. run 폴더를 커밋하고 올린 뒤 줄을 보냅니다. |
| `R-`로 시작하는 줄, `remedy:` 줄, `STATUS REFUSED exit=2 record=-` | 2 | 등록 전에 거부했습니다. 저장소(git)와 원장에 아무것도 쓰지 않았고 실행으로 세지 않습니다. git이 무시하는 잠금 파일 하나만 남습니다. | 아래 R 표를 봅니다. "기다립니다"나 "다시 붙여 넣습니다"로 적힌 것만 스스로 다시 실행합니다. |
| `R-`로 시작하는 줄 없이, 파이썬 오류 글자 여러 줄(`File "...", line ...` 같은 줄)에 이어 `STATUS REFUSED exit=2 record=-` | 2 | 등록 전에 예기치 않은 오류가 났습니다. 저장소와 원장에는 아무것도 쓰지 않았습니다. | 다시 실행하지 않습니다. `STATUS` 줄과 그 위의 20줄을 보냅니다. |
| `usage: ...`에 이어 `STATUS REFUSED exit=2 record=-` | 2 | 플래그 조합이 맞지 않습니다. | 이 문서의 줄을 다시 복사해 붙여 넣습니다. |
| `usage: ...`에 이어 `error: unrecognized arguments ...`(STATUS 줄 없음) | 2 | 플래그 철자가 틀렸습니다. | 같습니다. |
| `R-12: register_trial raised ...` 줄에 이어 `STATUS REFUSED_REGISTRATION exit=3 record=...` | 3 | 원장에 등록하다 오류가 났습니다(R-12). 그때까지 등록된 줄은 남습니다. | 멈춥니다. 다시 실행하려면 재실행 플래그가 필요합니다. 줄을 보냅니다. |
| `G-06: ...` 줄에 이어 `STATUS ERROR exit=4 record=...` | 4 | 등록 뒤 예기치 않은 오류입니다(G-06). | 멈춥니다. `STATUS` 줄과 그 위의 20줄을 보냅니다. |
| `reason: G-04: ...` 줄에 이어 `STATUS ERROR exit=4 record=...` | 4 | 판정 기준이 실행 중 바뀌었습니다(G-04). | 멈춥니다. 끝의 줄들을 보냅니다. |
| `G-07: ...` 줄에 이어 `STATUS ABORTED exit=5 record=...` | 5 | 등록 뒤 Ctrl+C 같은 것으로 중단되었습니다(G-07). | 멈춥니다. 줄을 보냅니다. |

- 종료 코드 3, 4, 5로 끝난 run 폴더는 지우지 않고 그대로 둡니다. 커밋할지는 Claude 답을 기다립니다(K절 4번). 커밋하지 않은 run 폴더가 남아 있어도 러너는 거부하지 않습니다.
- `record=` 뒤가 `run.final.<숫자>.json`이면 기록 파일을 제자리에 쓰지 못해 옆에 쓴 것입니다. 먼저 그 줄을 보냅니다. 러너는 `run.json`만 읽습니다. 그대로 두면 파일럿 1이 통과했더라도 파일럿 2가 R-11로 거부되고, 재실행 규칙도 그 폴더를 잘못 읽습니다. Claude가 파일 이름을 바로잡는 한 줄을 적어 드립니다. 그 한 줄이 H절 9번(run 폴더를 고치지 않는다)의 하나뿐인 예외입니다. 그 줄을 받기 전에는 파일럿 2도 재실행도 하지 않고, 파일 이름을 스스로 바꾸지도 않습니다.
- B3, D3의 숫자를 못 봤다면 `STATUS` 줄의 `exit=` 뒤 숫자가 같은 값입니다.
- 전체 검사(`python tests/run_all.py`)의 종료 코드는 FAIL이 없으면 0, 있으면 1입니다.

**러너의 플래그(명령 뒤에 붙이는 선택 글자)**

| 플래그 | 이 문서에서 쓰는 곳 |
| --- | --- |
| `--table <표>`와 `--of-record` | B2, D2. 실제 원장에 남는 기록 실행입니다. |
| `--fingerprint`와 `--table <표>` | A7. 읽기만 합니다. |
| `--rerun-of <실행 이름>`과 `--reason "<사유>"` | 재실행 때만 씁니다. 둘을 함께 써야 하고 사유는 비울 수 없습니다. 소유자가 정한 뒤에만 씁니다. |
| `--check-env`, `--egress-record`, `--fixtures`, `--record-baseline`, `--timing`, `--handoff-report` | 7A에서 쓴 것입니다. 이 문서에서는 쓰지 않습니다. |
| `--write-goldens` | Linux에서만 쓰는 것입니다. 이 PC에서는 러너가 거부합니다. 쓰지 않습니다. |
| `--rehearsal`, `--ledger-dir`, `--out-dir`, `--child-cmd` | 연습 실행용입니다. 기록 실행에 붙이면 러너가 거부합니다. |

**등록 전 거부 (모두 종료 코드 2, 저장소와 원장에 아무것도 쓰지 않음)**

| 코드 | 무슨 뜻 | 어떻게 하나 |
| --- | --- | --- |
| R-01 | 추적되는 파일이 바뀌었거나, `docs/nautilus_bridge/runs/` 밖에 새 파일이 있습니다. 화면에 그 경로가 나옵니다. | 지우거나 되돌리지 말고 줄을 보냅니다. Claude가 경로마다 커밋할지 치울지 알려 드립니다. |
| R-02 | git을 찾지 못했거나, 기준점이 HEAD와 다릅니다. 메시지에 `the branch ref is packed`가 있으면 git이 브랜치 기록을 묶음 파일로 옮겨 둔 것입니다(A6에서는 첫 줄 `UNVERSIONED`로 보입니다). | `packed`일 때는 아래 두 줄을 차례로 **한 번만** 실행한 뒤 A5부터 다시 합니다. `worktree`가 나오면 연구 클론 폴더에서 실행한 것이 아닙니다. 그 밖에는 줄을 보냅니다. |
| R-03 | 전용 파이썬 환경이 고정값과 다르거나, `.env`의 `QUANTGEN_NAUTILUS_PYTHON`이 비었거나, 일반 파이썬에 nautilus-trader가 설치되어 있습니다. | 아무것도 설치하거나 지우지 말고 줄을 보냅니다. |
| R-04 | 가격 파일이 없거나 md5가 표와 다릅니다. | 파일을 고치거나 다시 받지 않습니다. 줄을 보냅니다. 새 파일을 쓰려면 소유자 판정이 필요합니다. |
| R-05 | 가격 자료가 300행보다 적거나, 날짜 순서나 중복에 문제가 있거나, 소수 9자리 반올림 확인이 실패했습니다. | R-04와 같습니다. |
| R-06 | 금리 파일(DGS3MO)이 없거나 md5가 다르거나 빈 값이 남았습니다. 파일럿 1에만 해당합니다. | R-04와 같습니다. |
| R-07 | 표의 비용이 정해진 최소 비용보다 낮습니다. | 표를 고치지 않습니다. 줄을 보냅니다. |
| R-08 | 판정 기준의 부트스트랩 횟수가 2000이 아닙니다. | 줄을 보냅니다. |
| R-09 | 원장의 사슬이 깨졌습니다. | 멈춥니다. 원장을 고치지 않습니다. 소유자 판정 사안입니다. |
| R-10 | 연습 실행에만 있는 거부입니다. | 이 문서의 명령에서는 나오지 않습니다. 나오면 줄을 보냅니다. |
| R-11 | 표가 규격과 다르거나, 실행 승인 문구가 지금의 표와 코드 지문을 가리키지 않거나, 파일럿 2인데 파일럿 1의 통과 기록이 없습니다. | 표를 고치지 않습니다. 줄을 보냅니다. |
| R-13 | 러너가 읽은 날짜, 종가, 금리가 연구 스크립트가 읽는 값과 다릅니다. | 멈춥니다. 소유자 판정 사안입니다. |
| R-14 | 전용 파이썬의 외부 연결이 막혀 있음을 확인하지 못했습니다. 방화벽 규칙이 없거나 꺼졌거나, 7A의 기록과 지금 환경이 다릅니다. | A9와 A8을 다시 하고 그 화면과 러너의 줄을 보냅니다. 규칙을 다시 만드는 관리자 창 두 줄과 `--egress-record`는 Claude 답 뒤에 합니다. |
| R-15 | 원장이 없거나 비었거나, 이 PC의 지문이 표와 다릅니다(다른 PC, 컴퓨터 이름 변경). | 줄을 보냅니다. |
| R-16 | 다른 러너가 같은 표를 잡고 있거나, 원장이 600초 안에 바뀌었습니다. | 화면에 나온 초만큼 기다린 뒤 같은 줄을 다시 붙여 넣습니다. 다른 러너 창이 있으면 그것이 끝난 뒤에 합니다. |
| R-17 | 같은 표로 끝난 실행 기록이 이미 있는데 재실행 플래그가 없습니다. | 다시 돌리지 않습니다. 줄을 보냅니다. 재실행은 소유자가 사유를 정한 뒤에만 합니다. |

R-02에서 메시지가 `packed`일 때만, 한 번만:

```powershell
git commit --allow-empty -m "nautilus: re-anchor"
```

화면: `[claude/amazing-gauss-tdiguu <7자>] nautilus: re-anchor` 한 줄. 파일을 바꾸지 않는 빈 커밋이라 코드 지문은 그대로입니다. 그다음:

```powershell
git push
```

화면: B10과 같습니다. 이 두 줄을 실행했다는 것을 Claude에게 알립니다(HEAD의 40자가 바뀝니다).

**등록 뒤에 나오는 줄**

`STATUS` 줄 바로 위에 그대로 나오는 줄입니다. 앞에 `reason:`이 붙지 않습니다.

| 줄의 시작 | 상태, 종료 코드 | 무슨 뜻 | 어떻게 하나 |
| --- | --- | --- | --- |
| `R-12: register_trial raised` | `REFUSED_REGISTRATION`, 3 | 원장 등록 중 오류입니다. | 위 종료 코드 표의 3과 같습니다. |
| `G-06:` | `ERROR`, 4 | 예기치 않은 오류입니다. | 멈추고 `STATUS` 줄과 그 위의 20줄을 보냅니다. |
| `G-07:` | `ABORTED`, 5 | 실행 중 중단되었습니다. | 멈추고 줄을 보냅니다. |

`reason:`으로 시작하는 줄입니다. 한 번의 실행에 여러 줄이 나올 수 있습니다.

| `reason:` 뒤의 시작 | 상태, 종료 코드 | 무슨 뜻 | 어떻게 하나 |
| --- | --- | --- | --- |
| `C-01:` ~ `C-15:` (끝에 `(column <번호> (...), <1 또는 2>x)`) | `WITHHELD`, 1 | 24번(또는 10번) 가운데 그 실행이 무효였습니다. 예: `C-06`은 실행 프로그램이 죽었거나 시간 초과(한 번에 900초), `C-08`은 불러온 모듈 목록이 기준과 다름. 같은 실행에 대해 `P13:` 줄이 함께 나옵니다. | 다시 돌리지 않고 커밋한 뒤 줄을 보냅니다. |
| `P13:` | `WITHHELD`, 1 | 그 실행이 무효여서 비교하지 못했습니다. | 같습니다. |
| `P1:`, `P2:`, `P3:`, `P4:`, `P7:` (뒤에 `column <번호> (...), <1 또는 2>x:`) | `WITHHELD`, 1 | 그 설정과 비용 단계에서 hard 검사가 실패했습니다. 스펙의 표에서는 G-01입니다. 화면에는 `G-01`이라는 글자가 나오지 않습니다. | 같습니다. |
| `P0b:` | `WITHHELD`, 1 | 기준 수익(사서 그대로 들고 있었을 때의 수익) 계산이 연구 스크립트의 것과 다릅니다. hard 검사입니다(G-01). | 같습니다. |
| `P12: 1x:` 또는 `P12: 2x:` | `WITHHELD`, 1 | 설정을 골라 이어 붙인 수익 줄에서 상관이나 샤프 차이가 기준을 넘었습니다. hard 검사입니다(G-01). | 같습니다. |
| `G-02: decision mismatch` | `WITHHELD`, 1 | 두 계산의 판정이나 판정 조건이 다릅니다. | 같습니다. |
| `G-02: benchmark test dropped` | `WITHHELD`, 1 | 기준 수익과의 비교가 빠졌습니다. | 같습니다. |
| `G-03:` | `WITHHELD`, 1 | 채점 계산이 오류를 냈습니다. | 같습니다. |
| `G-04:` | `ERROR`, 4 | 판정 기준이 채점 뒤에 달라져 있었습니다. | 멈추고 줄을 보냅니다. |
| `G-05: ledger moved after registration` | `WITHHELD`, 1 | 등록 뒤에 원장이 바뀌었습니다(다른 프로그램이 원장에 씀). | 커밋한 뒤 줄을 보냅니다. |
| `G-08: reference drift` | `WITHHELD`, 1 | 파일럿 2에서 QUANTGEN 쪽 점수가 저장된 카드와 다릅니다. | 커밋한 뒤 줄을 보냅니다. |

**git 줄에서 나올 수 있는 것**

| 화면 | 무슨 뜻 | 어떻게 하나 |
| --- | --- | --- |
| A4, F7 `fatal: Not possible to fast-forward` | 이 PC에 GitHub에 없는 커밋이 있습니다. | 멈추고 줄을 보냅니다. |
| A4, F6, F7 `error: Your local changes ...` | 바뀐 파일이 있어 git이 받거나 옮기지 못했습니다. | 멈추고 줄을 보냅니다. 파일을 되돌리지 않습니다. |
| B6, B7, D6, D7 `fatal: pathspec '...' did not match any files` | `$run`에 넣은 폴더 이름이 틀렸습니다. | B5(또는 D5)를 B4(또는 D4)에 나온 폴더 이름으로 다시 하고, 그 단계부터 이어서 합니다. |
| B10, D10, E10 `! [rejected]` | 그 사이 같은 브랜치에 다른 커밋이 올라갔습니다. | 멈추고 줄을 보냅니다. 연구 클론에서 이것을 푸는 방법은 문서에 정해져 있지 않습니다. |
| B9, D9, E9 `Please tell me who you are` | 이 클론에 git 이름과 메일이 없습니다. | 줄을 보냅니다. |
| F10 `CONFLICT` | 병합이 충돌했습니다. | 아무것도 더 실행하지 않고 줄을 보냅니다. |
| `Error while finding module specification for 'tools.nautilus.runner'` | 연구 클론 폴더가 아닌 곳에서 실행했습니다. | A1, A2를 다시 합니다. |

**창이 닫혔거나 PC가 꺼졌을 때**

1. 새 PowerShell 창을 엽니다. A1과 A2를 합니다.
2. 아래 두 줄을 실행합니다. 둘 다 읽기만 합니다.

```powershell
git branch --show-current
```

```powershell
git status --porcelain --untracked-files=all
```

3. 나온 줄들과, 어느 단계에서 끊겼는지를 Claude에게 보내고 기다립니다.

- **파일럿 줄(B2, D2)을 다시 실행하지 않습니다.** 등록 뒤에 끊겼다면 run 폴더의 기록이 "진행 중"(`IN_PROGRESS`)으로 남고 `STATUS` 줄은 나오지 않습니다. 이때는 러너가 같은 줄을 거부하지 않고 다시 받아 줍니다. 그래서 막아 주는 것은 이 문서뿐입니다. 원장에는 이미 줄이 쓰였으므로, 다시 돌릴지는 Claude가 기록을 읽은 뒤 소유자가 정합니다.
- 전체 검사(E2) 도중에 끊겼다면 결과 파일은 바뀌지 않았을 것입니다(검사가 모두 끝난 뒤에 한 번 씁니다). 다시 돌려도 되는지 Claude 답을 기다립니다.
- 병합(F6~F12) 도중에 끊겼다면 위 두 줄 말고는 아무 git 줄도 실행하지 않습니다.
- B2, D2, E2가 끝난 뒤 커밋 단계에서 끊겼다면, 메모장에 붙여 둔 마지막 줄들도 함께 보냅니다.

## H. 하면 안 되는 것

| 번호 | 하면 안 되는 것 | 까닭 | 근거 |
| --- | --- | --- | --- |
| 1 | `git add -A`, `git add .` | 경로를 하나씩 적는 것이 규칙입니다. 다른 파일이 함께 올라갑니다. | 런북:188, 스펙:1597 |
| 2 | 연구 클론에서 폴더 전체 `checkout`, `reset`, `stash`, `clean`, 그리고 worktree 만들기 | 폴더 전체 명령은 고정 파일의 수정 시각을 바꾸는데, 검사 하나가 그 시각에 기대고 있습니다. worktree에서는 기준점이 `UNVERSIONED`가 됩니다. | 런북:58-59, 스펙:1548-1551, `docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md`:85-91 |
| 3 | 끝난 파일럿을 다시 돌리기. 재실행 플래그(`--rerun-of <실행 이름> --reason "<사유>"`)를 스스로 붙이기 | 같은 표의 끝난 기록이 있으면 러너가 R-17로 거부합니다. 재실행은 사유를 남기는 소유자 결정입니다. | 스펙:851-854, 1279, 러너:253-254, 290-293 |
| 4 | 표 고치기(설정, 비용, 날짜, `owner_confirmed`, `host_fingerprint`) | 실행 뒤 표의 값을 바꾸면 새 시행입니다. 승인 문구가 맞지 않으면 R-11입니다. | 스펙:1638-1639, 1273, 1608-1609 |
| 5 | 다른 실행이 도는 동안 시작하기(전체 검사, 판독, 다른 러너). QUANTGEN 앱을 켜 둔 채 파일럿이나 전체 검사 시작하기 | 파일럿과 전체 검사, 판독은 겹치지 않는 것이 규칙입니다. 전체 검사가 도는 동안에는 앱도 실행하지 않습니다. 파일럿 도중 원장이 바뀌면 판정이 보류됩니다(G-05). | 스펙:231-241, 1278, 1299, 런북:32, `docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md`:143-144, `tests/macro_acceptance.py`:113-138 |
| 6 | 원장 파일(`E1.jsonl`, `C3.jsonl`)을 열어 고치거나 지우기 | 원장은 덧붙이기만 합니다. 사슬이 깨지면 R-09입니다. | 스펙:259-263, 1271, 런북:140 |
| 7 | 가격 파일과 금리 파일을 바꾸거나 다시 받기 | md5가 달라지면 R-04, R-06입니다. 새 파일은 소유자 판정이 필요합니다. | 스펙:1266, 1268 |
| 8 | 실행 중 창 닫기, Ctrl+C | 등록 뒤에 끊기면 `ABORTED`로 남습니다. | 스펙:1631, 1301 |
| 9 | run 폴더를 지우거나 고치거나 옮기기. 예외는 하나: `STATUS` 줄이 `run.final.<숫자>.json`을 가리켰을 때 Claude가 적어 준 이름 바꾸기 한 줄(G절) | 러너가 앞선 기록을 읽어 재실행 규칙을 적용하고, 파일럿 2는 파일럿 1의 기록을 읽습니다. 러너는 `run.json`이라는 이름만 읽습니다. | 스펙:842-843, 러너:246, 413-424, 실행 기록:183, 스펙:1633(끌어낸 규칙) |
| 10 | 기록용 전체 검사에 `--suite`, `--milestone` 붙이기 | 결과 파일이 일부 행만으로 덮어써집니다. | `tests/run_all.py`:148-154 |
| 11 | `qa/acceptance_results.json`을 손으로 고치거나, Windows 전체 실행이 아닌 결과를 커밋하기 | 이 파일은 소유자의 Windows 전체 실행에서만 커밋합니다. | 스펙:1633 |
| 12 | Step 10 확인 전에 main을 연구 브랜치에 합치기 | 판정 H-D5와 P3입니다. | main의 `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`:508, 판정 P3 |
| 13 | 병합을 squash나 rebase로 하기, 연구 브랜치 지우기 | 원장 줄의 기준점 커밋에 계속 닿을 수 있어야 합니다. | 런북:213-214, 스펙:1615-1617 |
| 14 | 명령의 `python`을 `py313`이나 `ntvenv`의 파이썬으로 바꾸기, 일반 파이썬에 nautilus-trader 설치하기 | 러너와 검사는 일반 파이썬에서 돕니다. 설치하면 R-03입니다. | 러너:1, 스펙:164, 1265 |
| 15 | 방화벽 규칙 `QUANTGEN-nautilus-block-out`을 끄거나 지우기 | 외부 연결 차단을 확인하지 못하면 R-14입니다. | 스펙:1276, 339-342 |
| 16 | ⑤-2 관문 전에 파일럿 시작하기 | 러너는 이 관문을 검사하지 않습니다. 지키는 것은 절차입니다. | 스펙:1743-1747 |
| 17 | 키 값이나 `.env` 내용을 창이나 채팅에 적기 | 변수 이름만 적고 값은 적지 않는 것이 규칙입니다. | 공급사 대조 안내서 2절의 `.env` 줄, 저장소 `CLAUDE.md`의 마지막 항목(인계 문서 규칙) |
| 18 | 화면의 `remedy:` 줄을 그대로 따라 하기 | 그 줄에는 파일을 지우라, 표를 고치라, 재실행 플래그를 붙이라, `pip uninstall`을 하라는 것이 있습니다. 모두 이 표의 3, 4, 14번과 G절이 금지한 일입니다. | 러너:96-118, 실행 계약 코드:51-54 |
| 19 | 병합(F10) 도중 PowerShell 창 닫기 | main이 병합 도중의 상태로 남고, 이 표의 2번 때문에 폴더 전체를 되돌리는 명령도 쓸 수 없습니다. | 런북:58, 218 |
| 20 | Claude가 "병합해도 됩니다"를 알린 뒤 F12 전에 main에 다른 PR 병합하기 | main이 움직이면 Claude가 합쳐 확인한 상태와 달라져 F4나 F8에서 멈춥니다. | 런북:85, F4·F8의 확인 줄 |

## I. Claude에게 붙여 넣을 것

글자로 복사해 채팅에 붙입니다. run 폴더와 결과 파일은 push로 전달되므로 붙이지 않습니다.

**1번 앉기 (파일럿 1)**

1. A6의 두 줄.
2. A7의 다섯 줄.
3. B2의 끝 네 줄(`parity:`부터 `STATUS`까지). `reason:` 줄이 있으면 모두.
4. B3의 숫자.
5. B8의 줄들과 B10 출력의 마지막 두 줄.
6. 거부되었으면 `R-`로 시작하는 줄, `remedy:` 줄, `STATUS` 줄. `R-`로 시작하는 줄이 없으면 `STATUS` 줄과 그 위의 20줄.
7. A6에서 R-02의 두 줄을 실행했다면 그 사실.

**2번 앉기 (파일럿 2)**

1. A6의 두 줄, A7의 다섯 줄(파일럿 2의 표).
2. D2의 끝 네 줄과 `reason:` 줄.
3. D3의 숫자.
4. D8의 줄들과 D10 출력의 마지막 두 줄.
5. 거부되었으면 1번 앉기의 6번과 같습니다.

**3번 앉기 (전체 검사)**

1. E2의 마지막 줄.
2. E3의 숫자.
3. E4의 세 줄.
4. E5를 실행했으면 그 줄들. 멈춘 경우에는 커밋하지 않습니다.
5. 커밋했으면 E8의 줄과 E10 출력의 마지막 두 줄.

**4번 앉기 (병합)**

1. F2의 한 줄.
2. F3, F4, F5, F8에서 빨간 글씨가 나왔으면 그 줄.
3. F9의 한 줄.
4. F11의 한 줄(40자 세 개). F10의 출력은 보내지 않아도 됩니다. 첫 줄 `Merge made by ...`가 화면에 남아 있으면 그 한 줄만 함께 보냅니다.
5. F12 출력의 마지막 두 줄.
6. F13에서 줄이 나왔으면 그 줄들.
7. GitHub에서 빨간 표시나 실패 메일을 받았으면 그 제목.

**보내지 않는 것**

- `.env`의 내용과 키 값.
- 원장 파일(`E1.jsonl`, `C3.jsonl`)과 가격·금리 파일의 내용.
- 화면 전체를 찍은 그림. 다른 창의 내용이 함께 찍힐 수 있으니 위 줄만 글자로 보냅니다. 예외는 F10에서 편집기에 막혔을 때 하나입니다. 그때는 그 PowerShell 창만 찍어 보냅니다.

## J. 근거 표

Claude가 직접 읽은 줄입니다. 따로 적지 않은 것은 모두 연구 브랜치 `claude/amazing-gauss-tdiguu`의 `8a8c247`에 있는 파일입니다. 파일 이름은 아래처럼 줄여 적습니다.

- 스펙: `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md`
- 런북: `docs/nautilus_bridge/RUNBOOK_windows.md`
- 러너: `tools/nautilus/runner.py`
- 패리티 코드: `tools/nautilus/parity.py`
- 실행 계약 코드: `tools/nautilus/launch.py`
- 표 1, 표 2: `docs/nautilus_bridge/registration/pilot1_E1_spy.json`, `pilot2_C3_btcusd.json`
- 인계 보고서: `docs/nautilus_bridge/handoff/win_amd64.json`
- 검사 결과: `qa/acceptance_results.json`(7A.3 커밋 `563db54`의 것)

| 쓰인 곳 | 항목 | 근거 |
| --- | --- | --- |
| 머리말 | Step 8, 9, 10의 내용과 완료 기준 | 스펙:1631, 1632, 1633 |
| 앉는 횟수 | 관문: SPY와 DGS3MO가 PASS이거나 판정이 기록됨. BTC-USD도 같음. 러너는 검사하지 않음. 판정은 보류이거나 진행 | 스펙:1743-1747 |
| 앉는 횟수 | 파일럿 1 전에 세 시계열 모두 대조(P-D8) | 스펙:1720-1721, main의 `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`:521 |
| 앉는 횟수 | 시계열마다 첫 PASS, FAIL, WITHHELD 실행이 기록 실행 | 스펙:1738-1742 |
| 시간 | 5,600봉 12번 35.138초, 불러오기 1.94초 | 인계 보고서:3489-3521, 스펙:2097-2098 |
| 시간 | 964행, 소요 시간 합 958.3초. 합성 연습 26.9초, 32.0초 | 검사 결과(직접 집계), 같은 파일:5829-5831, 5859-5861 |
| 시간 | 약 5,488봉(777 + 4,711) | 스펙:1653 |
| 시간 | 4,392일(2014-09-17부터 2026-09-25까지 날짜 계산) | 표 2:12-13 |
| 시간 | 24번, 10번 | 러너:1439-1443, 표 1:17-30, 표 2:17-23 |
| 공통 | 일반 PowerShell 창(7A.2의 조건. 파일럿에 대해 따로 적은 줄은 없음) | 런북:51 |
| 공통 | 창 여는 방법, 폴더 경로 찾는 방법, 로그인 창 문장 | 공급사 대조 안내서:34, 43, 113(그 안내서도 Windows에서는 미검증으로 적음) |
| 공통, G | `remedy:` 줄의 문구 | 러너:96-118, 실행 계약 코드:46-54 |
| 공통 | 러너는 일반 파이썬에서 돈다 | 러너:1, 스펙:164 |
| A3 | 병합 전까지 연구 브랜치에 머무름 | 런북:221, 스펙:1618 |
| A4 | `git pull --ff-only`. 파일럿마다 다시 받고 두 점검을 되풀이 | 런북:205-209, 스펙:1610-1614, 스펙:12-13 |
| A5 | 러너의 git 검사 `status --porcelain=v1 -z --untracked-files=all`, `runs/` 아래 새 파일만 예외 | 러너:485, 494, 스펙:779, 1263 |
| A6 | 기준점은 `git:<HEAD>`여야 함. 함수 `repo_anchor()` | `core/quant/gate_ledger.py`:122-131, 러너:500-506, 스펙:1613-1614 |
| A6 | 한 줄 명령 자체 | 런북에 없음. 위 함수에서 끌어냄. Linux의 로컬 클론에서 `anchor ok` 확인 |
| A6 | `UNVERSIONED`는 묶음 파일일 때와 worktree일 때 같은 값 | `core/quant/gate_ledger.py`:122-131, 러너:500-504 |
| A6 | 연구 브랜치의 지금 끝 커밋 40자 | `git rev-parse origin/claude/amazing-gauss-tdiguu`(직접 실행, 2026-11-11) |
| A7 | `--fingerprint --table <표>` 명령과 표 경로 | 런북:114-115, 러너:1983 |
| A7 | 출력 다섯 줄의 모양. 읽기 전용. `host_fingerprint null (...)` 줄 | 러너:1750-1778, 런북:129, 155-156 |
| A7 | 표 지문과 코드 지문의 앞 16자, PC 지문 | 표 1:70-71, 표 2:50-51, 스펙:2194-2196 |
| A7 | 64자 전체 값 | Claude가 `8a8c247`의 git 파일 내용으로 러너:176-200의 계산을 다시 함(두 번, 따로 짠 스크립트로. 27개 파일) |
| A7 | 코드 지문에 들어가는 파일 | 러너:183-190, 스펙:1199-1204, `core/quant/gate_package.py`:36-38 |
| A7 | 표 지문은 두 소유자 칸을 빼고 계산 | 러너:176-180 |
| A7 | 승인 문구 확인과 거부. PC 지문이 다르면 R-15 | 러너:430-433, 447-449, 스펙:1273, 1277 |
| A7 | 코드나 표가 바뀌면 새 `owner_confirmed` | 스펙:1608-1609, 런북:199-200 |
| A7 | 7A.3 뒤 바뀐 파일은 스펙뿐 | `git diff --name-only 563db54 8a8c247`(직접 실행) |
| A7 | 줄바꿈을 바꾸지 않는 설정 | `.gitattributes`:2, 스펙:1205 |
| A8 | 1.1.1.1:443 조건, 핫스팟, 파일럿마다 적용 | 런북:143-149, 208-209 |
| A8 | 연결 확인의 모양 | 러너:606-612, `tools/nautilus/egress_probe.py`:11-17 |
| A8 | 한 줄 명령 자체 | 런북에 없음. 끌어냄. 문법만 확인(실행하지 않음) |
| A9 | 규칙 확인 명령과 11-04의 출력 | 러너:1742-1744, 인계 보고서:67-77 |
| A9 | 규칙이 없을 때의 화면 | 런북:66, 97-98은 `-ErrorAction SilentlyContinue`를 붙인 줄에 대해 "빈 출력"이라고 적음. A9의 줄에는 그것이 없어 빨간 오류가 날 것으로 봄(미검증) |
| A10 | 전원, 업데이트 일시 중지(명령 없음), 창 유지 | 스펙:1631, 런북:33 |
| A10 | 러너가 PC를 깨워 둠 | 러너:1287-1290, 스펙:845-848 |
| A10 | 겹치지 않는 실행 | 스펙:231-241, 런북:32 |
| A10 | 전체 검사 동안 앱을 실행하지 않음. 홈 폴더 상태를 견주는 검사 | `docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md`:143-144, `tests/macro_acceptance.py`:113-150, 198 |
| A10 | 등록 뒤 원장이 바뀌면 보류(G-05) | 패리티 코드:420-422, 512-514, 스펙:1299 |
| A10 | A2 등록 때 "다른 QUANTGEN 프로그램을 모두 닫고" | 런북:136-137 |
| A10 | 600초 | 러너:65, 284-288, 스펙:1278 |
| B2 | 파일럿 1 명령 | 스펙:1631, 러너:4, 1970-1972 |
| B2 | 러너의 순서 | 스펙:777-792, 러너:1385-1391, 1488-1510 |
| B2 | 등록 전 거부는 저장소와 원장에 아무것도 쓰지 않음 | 러너:11-13, 1535-1540, 스펙:857-858 |
| B2 | 잠금 파일은 맨 처음에 생김. git이 무시 | 러너:267-270, `docs/nautilus_bridge/.gitignore`:1 |
| B2, D2 | 되돌릴 수 없음: 원장은 덧붙이기만, 등록은 이 한 줄 안에서, 끝난 기록이 있으면 R-17 | 스펙:259-262, 851-854, 런북:138, 러너:253-254, 290-291, 1402-1405 |
| B2 | 원장 위치와 run 폴더 위치 | 러너:1256, `config.py`:182-184 |
| B2 | 실행 중 출력이 없음 | 러너의 run 경로에 있는 `print`는 1286, 1466, 1470, 1482, 1484, 1514-1517뿐 |
| B2 | 끝의 `parity:`, `trial counts:`, `decisions:`, `reason:` 줄 | 패리티 코드:458-473 |
| B2 | `STATUS` 줄 | 러너:1484, 스펙:855-856 |
| B2 | 기준 0.9999, 0.01과 소유자 기준 0.99, 0.05 | 패리티 코드:26-28, 스펙:874-875 |
| B2 | 판정 이름 네 가지 | `core/quant/validate.py`:50 |
| B2 | 파일럿 1의 예상 판정 | 스펙:1672-1680 |
| B2 | 등록 줄에 런북이 기대한 시행 수(본 기록은 아님) | 런북:136-138 |
| B2 | 소유자가 보고한 것은 E1 12줄까지 | 스펙:2140-2143 |
| B2 | 12줄에서 `U 24`, `n_trials 36`이 따라 나오는 계산 | 패리티 코드:246-252, 표 1:42-67 |
| B2 | `hard_pass False`일 때의 줄 | 패리티 코드:467-471, 482-487 |
| B2 | 스펙이 Step 8의 끝으로 인정하는 WITHHELD는 두 가지: 걸린 검사를 적은 기록, 패리티 통과 뒤의 `decision mismatch` | 스펙:1631 |
| B2 | `hard_pass True`인 보류의 다른 사유 | 패리티 코드:277, 422, 430, 514 |
| B2 | run 폴더 이름 `NB-<UTC>-<표 지문 앞 8자>` | 러너:211-213, 스펙:825-827 |
| B2 | 한 번의 제한 시간 900초 | 실행 계약 코드:39 |
| B3 | `$LASTEXITCODE` | 런북:84-116(같은 변수를 씀) |
| B4 | 카드 파일 이름 | 패리티 코드:517, 표 1:41 |
| B4 | `.locks`와 A2 영수증은 git이 무시 | `docs/nautilus_bridge/.gitignore`:1-4 |
| B4~B11 | 커밋 줄 | 런북에 없음. 스펙:1631과 런북:163-188에서 끌어냄. 스크래치 저장소에서 모양 확인 |
| C | Claude는 push 뒤에 읽음 | 스펙:1631 |
| C | 실행 기록의 항목 | 스펙:1139-1146 |
| C | hard 검사와 경고의 목록 | 스펙:872-885, 1304, 패리티 코드:29-30 |
| C | 결과를 본 뒤 설정을 바꾸면 새 시행 | 스펙:1680 |
| C | 재실행 규칙, `C-06`만일 때의 예외 | 스펙:851-854, 러너:253-254, 290-293, 1244-1245 |
| C | 무효 실행에는 `P13:` 사유 줄이 함께 붙음(코드를 읽은 것. 실제 실행으로는 미검증) | 패리티 코드:29, 151-154, 375-377 |
| C | 일치 검사의 사유 문구 | 패리티 코드:274-279, 514, 스펙:1140 |
| D | 러너가 확인하는 파일럿 2의 조건 | 러너:413-424, 434-438, 스펙:1273, 1665 |
| D | 기준 카드 md5 | 러너:400-410, 표 2:48-49 |
| D | 원장 C3와 PC 지문 | 러너:439-449, 스펙:1664 |
| D2 | Step 9 줄에 명령이 없음 | 스펙:1632 |
| D2 | 명령 | 러너:4의 사용법과 런북:115의 표 경로에서 끌어냄 |
| D2 | 5개 설정, 10bp와 20bp, 금리 없음 | 표 2:14-24, 스펙:1632, 1662 |
| D2 | 이미 있는 설정은 새 줄이 되지 않음 | 스펙:261-262, 1631("appended or already present") |
| D2 | 예상 판정 PASS, `U`는 많아야 11 | 스펙:1682-1689, 1664 |
| D2 | `reference drift`도 끝으로 인정 | 스펙:1632, 1302, 패리티 코드:502 |
| D2 | R-11 문구 | 러너:436-438 |
| D4 | 카드 파일 이름, 폴더 끝 8자 | 표 2:34, 러너:211-213 |
| E | 전체 검사와 파일럿은 겹치지 않음 | 스펙:233-235 |
| E2 | 명령 | 런북:113, 스펙:1633 |
| E2 | 줄마다의 출력, 마지막 줄, 종료 코드 | `tests/run_all.py`:141, 158-159 |
| E2 | `--suite`가 결과 파일을 덮어씀 | `tests/run_all.py`:148-154 |
| E2 | 11-04의 결과 | 스펙:2101-2105, 검사 결과(직접 집계) |
| E4 | 허용되는 `nautilus` NOT_RUN 한 건 | 런북:153-154, 스펙:1624-1625 |
| E4 | 커밋 전 조건: FAIL 0, nautilus 집계, guard (a)(b)(d) | 스펙:1633 |
| E4 | 11-04의 `nautilus` 57 PASS, `guard` 5 PASS, 964행 | 검사 결과(직접 집계), 스펙:2101-2105 |
| E4, E5 | 요약 줄 두 개 | 문서에 없음. Claude가 만듦. 11-04 검사 결과의 사본과, 일부러 고친 사본으로 Linux에서 실행 |
| E6 | 결과 파일은 검사가 모두 끝난 뒤 한 번 쓰이고 행마다 소요 시간이 들어감 | `tests/run_all.py`:139, 152-154 |
| E6 | 7A 때 전체 검사 뒤의 상태 줄 | 인계 보고서:3104-3109 |
| E7~E10 | 결과 파일 커밋 규칙 | 스펙:1633, 런북:184-188 |
| F | Step 10의 경로 확인 규칙 | 스펙:1633 |
| F3~F5 | 점검 세 줄 | 런북:84-86 |
| F6, F7, F10, F12 | 병합 네 줄과 금지 | 런북:211-221, 스펙:1615-1619 |
| F6~F10 | main에는 `docs/nautilus_bridge/.gitignore`가 없어 잠금 파일과 A2 영수증이 새 파일로 보임 | `git ls-tree origin/main docs/nautilus_bridge/.gitignore`(빈 출력), 연구 브랜치의 같은 파일:1-4. 스크래치 저장소에서 병합 전후 모양 확인 |
| F8 | 더한 확인 줄 | 런북에 없음. 런북:86의 꼴에서 끌어냄. 스크래치 저장소에서 종료 코드 확인 |
| F9 | 편집기 확인 줄, 편집기별 키 | 런북에 없음. git의 표준 명령. Linux에서 한 줄이 나오는 것만 확인. 편집기와 키는 미검증 |
| F10 | 병합 줄에 `-m`도 `--no-edit`도 없음. 앞선 소유자 커밋은 모두 `-m` | 런북:218, 168, 185 |
| F10 | 출력의 첫 줄이 `Merge made by the 'ort' strategy.`이고 끝은 `create mode` 줄 | 스크래치 저장소(git 2.43.0)에서 확인. 소유자 PC의 git 버전은 미검증 |
| F10 | 연구 브랜치 쪽에서 바뀐 파일 269개, 그중 새 파일 247개 | `git diff --name-status bb35b3b 8a8c247`(캐시 폴더 제외, 개수만 셈) |
| F11 | 병합 커밋의 부모 순서(main 쪽, 연구 브랜치 쪽) | 스크래치 저장소에서 확인 |
| F12 뒤 | 준법 문서 점검은 main에 올릴 때마다 돎. 연습 병합에서는 실패 | main의 `.github/workflows/compliance-review.yml`:3-6, 55, 연습 병합 기록 4절 |
| F | 서명 문장이 푸는 두 가지 | 스펙:17-25 |
| F | main이 지문 대상 파일, `core/quant/gate_package.py`, 표, 검사 결과 파일을 바꾸지 않음 | `git diff --name-only bb35b3b 83046c1`을 그 경로들로 한정해 직접 실행(빈 출력). `git ls-tree origin/main tools/nautilus/`도 빈 출력 |
| F | 코드 지문의 파일 목록이 정해지는 곳 | 러너:186-189 |
| G | R-01 ~ R-17 | 스펙:1263-1279, 러너:96-118 |
| G | C-01 ~ C-15 | 스펙:1280-1294 |
| G | G-01 ~ G-08 | 스펙:1295-1302 |
| G | 종료 코드 여섯 가지 | 러너:11-13, 스펙:855-859 |
| G | 등록 뒤 상태별 종료 코드 | 러너:1488-1510, 패리티 코드:509, 522-523 |
| G | `R-12`, `G-06`, `G-07`은 `reason:` 없이 나옴 | 러너:1465-1466, 1493-1508 |
| G | `reason:` 줄의 시작 글자. `G-01`은 화면에 나오지 않음 | 패리티 코드:375-381, 393, 398, 403, 422, 430, 472-473, 499, 502, 508, 514 |
| G | 등록 전 예기치 않은 오류는 `R-` 줄 없이 오류 글자 끝 2000자와 `STATUS` 줄 | 러너:1537-1540, 스펙:856-857 |
| G | `--write-goldens`는 Linux 전용 | 러너:1652-1653, 런북:107-116 |
| G | 러너에 있는 플래그 전부 | 러너:1970-1985 |
| G | 플래그 조합 거부 | 러너:1986-1994 |
| G | 재실행 플래그 두 개는 함께. 기록 실행은 연습용 플래그와 폴더 지정을 받지 않음 | 러너:1244-1254 |
| G | 철자가 틀린 플래그 | 파이썬 표준 동작. 스크래치에서 종료 코드 2 확인 |
| G | 거부 줄의 모양 | 러너:1513-1518, 실행 계약 코드:57-62 |
| G | R-16의 문구 | 러너:281, 288 |
| G | R-02의 `packed` 문구와 두 줄 | 러너:500-504, 98, 스펙:1264 |
| G | `run.final.<숫자>.json` | 러너:1477, 스펙:840-841 |
| G | 러너는 `run.json`만 읽음. 소유자가 이름을 바꾼다 | 러너:246, 416, 실행 기록:183 |
| G | 끊긴 실행의 기록은 `IN_PROGRESS`로 남고 러너가 다시 받아 줌 | 러너:253, 1414, 1426 |
| G | 커밋하지 않은 run 폴더는 거부되지 않음 | 러너:494 |
| H | 폴더 전체 명령과 worktree를 금지하는 까닭 | `docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md`:85-91 |
| H | 나머지 금지 항목 | H절 표의 근거 칸에 줄마다 적음 |
| 판정 | P1(대조 도구 버전을 main 쪽에 고정) | main(`83046c1`)의 `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`:675-695, `results/RULINGS.md`:17-39 |
| 판정 | P2, P3, P4(2026-11-11 "전부승인") | main(`83046c1`)의 `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`:697-764. 권장 문구는 705-707, 소유자 답은 748, 반영 내용은 757-759 |
| 판정 | H-D5, U5, P-D3, P-D6 ~ P-D9 | main의 `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`:505, 508, 516, 519-522 |
| 판정 | ⑥-1, ⑥-2, ⑦-1, ⑦-2의 몫 나누기 | main의 `docs/nautilus_bridge/REMAINING_WORK_2026-10-27.md`:117, 133-135 |
| 근거 파일 | 실행 기록 | `docs/superpowers/plans/2026-10-28-nautilus-execution-record.md`(연구 브랜치) |

## K. 아직 정해지지 않은 것

> 2026-11-11(KST) 소유자가 이 절의 10개 항목을 모두 정했습니다("전부승인합노."). 결정표는
> `docs/product/DECISIONS_PILOT_CLOSE_MERGE_2026-11-11.md`이고, 각 행이 이 절의 항목을 `K<번호>`로 적었습니다. 무엇이
> 정해졌는지는 `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`의 같은 날 "파일럿·마감·병합 결정 27건에 대한 답" 절에 있습니다.
> 2번은 "다시 한다"(합친 상태를 F의 첫머리에서 검사)로 정해졌으므로, F의 줄은 그 순서로 Claude가 다시 적어 드립니다.
> 다시 적은 줄을 받기 전에는 F를 시작하지 않습니다. 아래 글은 정하기 전의 질문 그대로 둡니다.

이 문서는 아래를 정하지 않았습니다. 소유자 판정이 필요합니다. 2번과 3번은 F를 시작하기 전에 정해져 있어야 합니다.

1. **파일럿 1이 `hard_pass False`로 끝났을 때의 다음 걸음.** 스펙은 걸린 검사를 적은 보류 기록을 Step 8의 끝으로 인정하지만, 무엇을 고쳐 다시 갈지와 파일럿 2 없이 마감과 병합을 해도 되는지는 적지 않았습니다. 코드를 고치면 코드 지문이 바뀌어 Windows 검증과 실행 승인 문구를 다시 해야 합니다.
2. **Claude가 main을 연구 브랜치에 합친 뒤 Windows 전체 검사를 다시 해야 하는지.** E에서 커밋하는 결과는 합치기 전 상태의 결과입니다.
3. **2026-11-04 서명 문장이 합친 뒤의 상태에도 적용되는지.** 7A.1 때는 main을 먼저 합치고 문장을 기록했습니다. 이번에는 문장이 먼저입니다.
4. **종료 코드 3, 4, 5로 끝난 실행의 run 폴더도 커밋하는지.** 스펙 Step 10은 "run 폴더를 커밋한다"고만 적었습니다.
5. **`README.md`의 검사 개수를 누가 고치는지.** 스펙 Step 10 줄은 소유자가 고친다고 적었습니다. 남은 일 문서(⑦-1 줄)는 Claude의 몫으로 적었고, 판정 P2는 Claude가 연구 브랜치에서 커밋할 수 있는 파일에 `README.md`를 넣었습니다. P2는 누가 숫자를 고치는지까지는 말하지 않습니다. Claude의 제안은 "Claude가 E의 결과 숫자로 두 줄을 고친다"입니다. 정하시기 전까지 이 표는 소유자가 고치지 않는 것으로만 적었습니다.
6. **Claude가 연구 브랜치에 올릴 때마다 승인을 받을지.** 7A.1에서는 push 전에 승인을 받았습니다. P2는 커밋 범위만 정했습니다.
7. **파일럿 2 뒤 Claude 판독을 기다리지 않고 전체 검사로 가도 되는지.** 스펙은 순서만 정합니다. 이 표는 기다리는 쪽으로 썼습니다.
8. **F10의 병합 줄에 `--no-edit`를 붙여도 되는지.** 붙이면 편집기가 뜨지 않고, git이 만든 기본 메시지로 같은 병합 커밋이 만들어집니다. 런북의 줄과 글자가 달라지는 것은 이 낱말 하나입니다. 정하시기 전까지 이 표는 런북의 줄 그대로 쓰고 F9에서 편집기를 미리 확인합니다.
9. **파일럿이 `hard_pass True`인데 `decision mismatch`나 `reference drift`가 아닌 사유로 보류됐을 때 그 Step을 끝난 것으로 볼지.** 사유는 `benchmark test dropped`, 채점 오류(G-03), 실행 중 원장이 바뀜(G-05)입니다. 스펙은 이 경우를 끝으로 적지 않았습니다.
10. **Claude의 합치기(P3)에 충돌 풀이 말고 무엇까지 넣을지.** 연습 병합에서 나온 것은 Bonds 화면 검사를 맞추는 수정 3개, 상태 요약 파일 다시 만들기, 준법 문서 검토 기록 갱신, Bonds 화면에서 고른 방식 일곱 가지입니다. 내용은 `docs/product/STEP10_MERGE_REHEARSAL_2026-11-11.md`에 있습니다.

## L. 확인하지 못한 것

- **PowerShell 자체.** Linux에는 PowerShell이 없습니다. 변수 줄(`$rc`, `$run`), 따옴표가 든 긴 `python -B -c` 줄, `$LASTEXITCODE`, `if (...) { throw ... }` 줄이 PowerShell에서 그대로 전달되는지는 실행해 보지 못했습니다. `git`과 `python` 부분은 bash로 옮겨 확인했습니다.
- **러너의 기록 실행.** Claude는 기록 실행(`--of-record`)을 한 번도 하지 않았고 하지 않는 것이 규칙입니다(스펙:770). B2와 D2의 화면 줄은 코드에서 읽은 것입니다. 합성 자료 연습 실행은 11-04 Windows 전체 검사에서 통과했습니다.
- **실제 자료의 패리티.** 파일럿 구간의 패리티 숫자는 일부러 계산한 적이 없습니다(스펙:927-929). `hard_pass`가 참으로 나올지는 실행해야 압니다.
- **화면에 섞여 나오는 줄.** 채점 계산이나 연구 스크립트가 경고 줄을 찍는지는 확인하지 못했습니다.
- **소유자 PC의 상태.** 연구 클론이 `8a8c247`을 받았는지, 원장 E1에 12줄이 있는지, C3의 줄 수, 방화벽 규칙이 지금도 있는지는 Claude가 볼 수 없습니다. E1의 12줄은 11-04 소유자 보고와 표의 PC 지문이 채워져 있다는 점에서 추정한 것입니다.
- **시간.** 모두 추정입니다. 근거 측정값은 맨 위에 적었습니다.
- **Windows 화면 조작.** 시작 메뉴에서 PowerShell 창을 여는 방법, 탐색기에서 폴더 경로를 보는 방법, GitHub 로그인 창이 뜨는지, 업데이트 일시 중지 메뉴의 이름, 콘솔 창을 마우스로 누르면 출력이 멈추는지는 확인하지 못했습니다.
- **병합 때의 편집기.** F9의 줄이 이 PC에서 무엇을 내는지, F10에서 어떤 편집기가 뜨는지, 적어 둔 키(`:wq`, 창 닫기, 탭 닫기)가 그대로 통하는지는 확인하지 못했습니다. `Merge made by the 'ort' strategy.`의 따옴표 안 낱말은 git 버전에 따라 다를 수 있습니다.
- **방화벽 규칙이 없을 때 A9의 화면.** 빨간 오류일 것으로 보지만 실행해 보지 못했습니다.
- **`C-06`만으로 보류된 실행의 재실행.** 스펙은 플래그 없이 다시 돌릴 수 있다고 적었습니다. 코드를 읽으면 `P13:` 사유 줄이 함께 붙어 러너가 R-17로 거부할 것으로 보입니다. 실제 러너로 실행해 확인하지는 않았습니다.
- **QUANTGEN 앱이 원장 자리에 언제 쓰는지.** 확인하지 못했습니다. 그래서 A10에서 닫도록 했습니다.
- **GitHub 쪽.** main에 직접 push가 막혀 있는지, 병합이 올라간 뒤 자동 검사가 어떻게 나오는지는 확인하지 못했습니다. 준법 문서 점검이 실패할 것이라는 예상은 Linux의 연습 병합에서 같은 점검 명령을 돌려 본 결과입니다.
- **파일럿 뒤의 전체 검사.** 원장과 run 폴더가 늘어난 상태의 전체 검사는 이번이 처음입니다.
- **커밋 줄과 커밋 메시지.** B4~B11, D4~D11, E6~E11, F8, F9, F11, F13은 규칙에서 끌어낸 줄입니다. 스크래치 git 저장소와 가짜 원격 저장소에서 화면 모양과 종료 코드만 확인했습니다. GitHub에는 아무것도 올리지 않았습니다.
- **합치는 날의 main.** 이 문서의 main 쪽 사실은 `83046c1`(2026-11-11 13:53 KST) 기준입니다. main이 더 움직이면 코드 지문 대상 파일 비교와 연습 병합을 다시 해야 합니다.
- **push가 `rejected`일 때 연구 클론에서의 처리.** 문서에 정해진 줄이 없어 "멈추고 보냅니다"로만 적었습니다.
- **`run.final.<숫자>.json`을 `run.json`으로 바꾸는 PowerShell 줄.** 미리 적어 두지 않았습니다. 그 일이 생기면 Claude가 그때의 폴더 상태를 보고 적습니다.
- **창이 닫혔을 때의 절차.** G절 끝의 절차는 러너 코드에서 끌어낸 것이고 Windows에서 해 보지 않았습니다.
