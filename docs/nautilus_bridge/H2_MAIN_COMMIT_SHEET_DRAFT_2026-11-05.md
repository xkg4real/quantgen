# H2 판독 산출물 main 커밋 실행표 (⑧-1, H-D5)

- 대상: 소유자(Geon Koh). 모든 명령은 소유자 PC의 Windows PowerShell 5.1(일반 권한)에서 소유자가 실행합니다.
- 작성: 2026-11-05, Claude. 커밋하지 않은 작업 파일입니다. Claude는 이 표를 쓰며 아무것도 커밋하거나 push하지 않았습니다.
- 근거:
  - 준비 문서 `docs/nautilus_bridge/H2_READOUT_PREP_2026-11-04.md`(브랜치 `claude/h2-readout-prep-20261104`, 커밋 `201cf7f`). 특히 6.7(main에 넣는 것)과 8.1(결정 원문). 이하 "준비".
  - 판독 실행표 `H2_RUN_SHEET_2026-11-04.md`(커밋하지 않은 작업 파일). 11절(해시와 비공개 사본), 12절(짧은 기록 파일), 15절(판독 뒤의 일). 이하 "실행표".
  - 태그 `studies-of-record-2026-10-23`(커밋 `eacd57d`)의 코드. `paper_live/engine.py:132-152`(`MANIFEST.json` 형식), `paper_live/replay.py:147-230`(재생 산출물), `paper_live/verdict.py:172-181`(`verdict.json`과 판정 줄).
  - main(`origin/main`, 2026-11-05에 읽은 끝은 `a41fd7a`)의 코드와 문서. `tests/frozen_guard.py:55-63`, 분리 스펙 `docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:99-101, 369-373`, `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`(결정표 2차 원문, U4-나 절), `.github/workflows/*.yml`, `.gitattributes`.
- Claude는 어느 ref에서도 `paper_live/out*/` 안을 열거나 목록을 보지 않았습니다(예외 하나는 공개 기록 4번). 그래서 main에 `MANIFEST.json`과 `replay_holdout/`가 이미 있는지 모릅니다. 아래 스크립트와 점검이 소유자 화면에서 그것을 가립니다.
- 판독 사실(소유자 보고, 유효): 두 프로필 모두 `h2_state final`, 10세션 2026-10-21..2026-11-03, 스냅샷 `holdout_5m_60d_20261105`, yfinance 1.4.1, 2026-11-05 06:45:16Z..06:55:54Z. 태그 클론 `C:\Users\whydi\QUANTGEN-studies`, 비공개 사본 `C:\Users\whydi\QUANTGEN-h2-private`(`H2_READOUT_RECORD.txt` 포함).
- 이 표가 스스로 정할 수 없는 것은 맨 끝 "확인 필요"에 모았습니다. 걸린 곳에 `[확인 필요 #n]`을 붙였고, 명령은 권고대로 적었습니다.

## 0. 한눈에 보기

| 항목 | 내용 |
|---|---|
| 누가 | 소유자가 커밋하고 push하고 PR을 엽니다. **병합은 main 세션(Claude)이 CI 통과 뒤에 합니다.** 근거: `OWNER_RULINGS_LOG.md` U4-나 절("CI 통과 시 Claude 병합"을 다시 적용). 소유자는 병합 버튼을 누르지 않습니다 |
| 어디서 | **새 클론 `C:\Users\whydi\QUANTGEN-h2-main`** (GitHub `main`, OneDrive 밖). 메인 클론 `C:\Users\whydi\OneDrive\Desktop\QUANTGEN`은 연구 브랜치 `claude/amazing-gauss-tdiguu`(`8a8c247` 이후)에 그대로 두고 쓰지 않습니다. 태그 클론 `C:\Users\whydi\QUANTGEN-studies`는 읽기만 합니다 |
| 무엇을 | 13개 파일. `replay_holdout/` 8개와 `verdict.json` 2개는 바이트 그대로 복사, `MANIFEST.json` 2개는 스냅샷 행 하나씩 추가, 짧은 기록 파일 1개 |
| 넣지 않는 것 | 스냅샷 `holdout_5m_60d_20261105.csv.gz` 2개(H-D6), 기록(transcript) 원본(H-D11), `out*/`의 다른 파일 |
| 브랜치 | `owner/h2-readout-outputs-20261105` `[확인 필요 #2]` |
| 언제 | 지금 할 수 있습니다. ⑧-4(분리 스펙 Phase 2)가 이 커밋을 기다립니다(준비 1.4, 6.8). 이 표는 `paper_live`를 실행하지 않고 `~\.nextgen`도 열지 않으므로 ⑤-2, 파일럿, 테스트 스위트와 겹쳐도 됩니다 |
| 공개 시점 | **push하는 순간 결과가 공개됩니다**(공개 저장소, 준비 5.4, D-6). 이 표는 H-D7의 "결과는 main 커밋 때 공개"를 이 push로 읽습니다. push 전에는 결과 수치를 Claude에게 보내지 않습니다 |
| 도구 | git과 Python(표준 라이브러리만). 스크립트 두 개를 `C:\Users\whydi\QUANTGEN-h2-tools`에 만듭니다. 두 스크립트의 출력에는 결과 수치가 없어 Claude에게 보내도 됩니다 |
| 걸리는 시간 | 30~60분으로 추정합니다(클론 시간에 따라, UNVERIFIED) |

## 1. 이 표가 따르는 결정

### 1.1 원문

출처: main `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`, "2026-11-04, Claude Code 채팅 (Step 7A 세션): 소유자 결정표 2차 답 (원문)" 절(커밋 `b099ae1`).

- `H-D5 = (가) 동결 해제 뒤 별도 클론에서 PR. 7A.5부터 Step 10 병합까지는 main을 연구 브랜치에 합치지 않음 [권고]`
- `H-D6 = (가) 스냅샷은 비공개 보관, sha256·행 수 등 MANIFEST만 커밋 [권고]`
- `H-D7 = (가) 유효성 항목만. 결과는 main 커밋 때 공개 [권고]`
- `H-D11 = (가) 짧은 기록 파일을 새로 만듦(판정 줄, yfinance 버전, 시작·끝 시각; 컴퓨터 이름 제외) [권고]`
- `H-D13 = (가) 공개 기록으로 남기고, Claude 세션의 guard 스위트 실행은 계속 허용 [권고]`
- 먼저 정해진 결정: `U4 = (나) main 병합 동결을 지금 해제합니다.` (같은 파일의 U4-나 절)

### 1.2 이 표의 읽기

| 결정 | 이 표가 하는 일 |
|---|---|
| H-D5 "별도 클론" | GitHub `main`에서 **새로** 복제한 세 번째 폴더. 메인 클론과 태그 클론은 커밋에 쓰지 않습니다(준비 6.7 (가)) |
| H-D5 뒷부분 | 이 PR이 병합된 뒤에도 Step 10 병합까지 main을 연구 브랜치에 합치지 않습니다. 병합 뒤 연구 브랜치 세션에 알립니다(20절) |
| H-D6 "MANIFEST만" | 판독이 쓴 `holdout_5m_60d_20261105` 행 하나를 엔진이 쓴 필드 그대로 넣습니다(sha256, rows, first, last, tickers, saved_utc 등). `.csv.gz`는 넣지 않습니다 |
| H-D7 | push가 공개 시점입니다. 그 전에는 판정 줄, 평균, p, 날짜별 손익을 Claude에게 보내지 않습니다 |
| H-D11 | 비공개 사본의 `H2_READOUT_RECORD.txt`를 바이트 그대로, 이름만 바꿔 넣습니다(2.1) |
| H-D13 | 커밋 메시지와 PR 본문의 공개 기록 1번 |
| 준비 6.7 | 대상은 `out*/replay_holdout`, `verdict.json`, 판독 기록입니다(분리 스펙 `:99-101` "Their outputs are copied into the main line and committed as artifacts"). 그래서 `summary.json`(재생 요약)과 `verdict.json`도 넣습니다 |

## 2. 넣는 파일

| # | 저장소 경로 | 출처 | 방법 | 기대 git 상태 |
|---|---|---|---|---|
| 1-4 | `paper_live/out/replay_holdout/days.csv`, `fills.jsonl`, `summary.json`, `trades.jsonl` | 태그 클론의 같은 경로 | 바이트 그대로 복사. sha256 = 11.1 | `??`(새 파일) |
| 5-8 | `paper_live/out_krx/replay_holdout/` 같은 4개 | 같음 | 같음 | `??` |
| 9 | `paper_live/out/verdict.json` | 같음 | 같음 | ` M`(10-23의 main에서 두 `verdict.json`은 pending이었음, 분리 스펙 `:373`) |
| 10 | `paper_live/out_krx/verdict.json` | 같음 | 같음 | ` M` |
| 11 | `paper_live/out/data/MANIFEST.json` | main의 파일 + 판독이 쓴 행 | 스크립트로 행 하나 추가(2.2) | ` M`. main에 파일이 없으면 `??` |
| 12 | `paper_live/out_krx/data/MANIFEST.json` | 같음 | 같음 | 같음 |
| 13 | `paper_live/H2_READOUT_RECORD_2026-11-05.txt` | `C:\Users\whydi\QUANTGEN-h2-private\H2_READOUT_RECORD.txt` | 바이트 그대로 복사 | `??` |

### 2.1 짧은 기록 파일의 위치 (제안) `[확인 필요 #1]`

제안: `paper_live/H2_READOUT_RECORD_2026-11-05.txt`.

- 판독 산출물 옆에 둡니다. 분리 스펙은 판독 기록("the readouts")을 `out*/replay_holdout`, `verdict.json`과 함께 main에 넣는 산출물로 적습니다(`:99-101`).
- `out/`이나 `out_krx/` 한쪽에 넣지 않습니다. 한 파일이 두 프로필을 다룹니다.
- `out*/` 밖에 둡니다. Claude 세션들은 `paper_live/out*/` 안을 읽지 않는 규칙으로 일해 왔습니다. 공개 뒤 ⑧-4 스펙이 이 기록을 인용할 때 그 규칙과 부딪히지 않습니다. `tests/frozen_guard.py`도 이 파일을 보지 않습니다.
- CI는 이 파일을 읽지 않습니다. 두 워크플로의 sparse checkout이 `paper_live/`를 빼고(`.github/workflows/*.yml`), 준법 점검은 `paper_live`를 보관 폴더로 건너뜁니다(`tools/compliance/check.py`의 `ROOT_ARCHIVES`).
- 이름에 날짜를 붙여 나중의 GROKTEAM 판독 기록과 구별합니다. 내용은 바꾸지 않으므로 비공개 사본과 sha256이 같습니다.
- 다른 안: `docs/nautilus_bridge/H2_READOUT_RECORD_2026-11-05.txt`(⑧ 로드맵 문서 옆). 이 경우 11.1, 11.2, 13, 14절의 경로와 커밋 메시지, PR 본문의 경로를 바꿉니다.

### 2.2 `MANIFEST.json` 행 합치기 설계 (코드에서)

- 형식(태그 `paper_live/engine.py:137-151`, `save_bars`):
  - 파일은 스냅샷 이름을 키로 하는 JSON 객체 하나입니다. 행 필드는 `file`, `sha256`(`.csv.gz`의 sha256, 소문자), `tickers`(정렬), `rows`, `first`, `last`, `saved_utc`, `source`, `interval`, `period`, `start`, `end` 순서입니다.
  - 새 스냅샷은 기존 파일을 읽어 키 하나를 맨 끝에 더한 뒤 `json.dumps(man, indent=1, default=str)`로 통째로 다시 씁니다. 끝 줄바꿈은 없습니다.
  - `Path.write_text`로 쓰므로 Windows에서는 줄바꿈이 CRLF입니다. 저장소의 `.gitattributes`가 `* -text`라 git은 바이트를 바꾸지 않습니다.
  - 스냅샷은 모든 종목을 받았을 때만 저장됩니다(`engine.py:181-182`). 그래서 행의 `tickers`는 base 27개, krx 21개 전부여야 합니다(태그 `config.py`의 `UNIVERSE` + `INVERSE_ETFS`).
- 왜 태그 클론의 `MANIFEST.json`을 통째로 복사하지 않나: 판독이 쓴 파일은 "태그의 행 + 새 행"입니다. 태그 뒤 main에 다른 행이 더해졌다면 통째 복사는 그 행을 지웁니다. 그래서 **main의 파일에 그 행 하나만 더합니다.** main의 행이 태그와 같고 줄바꿈도 같으면 결과는 판독이 쓴 파일과 바이트까지 같아집니다(11.1 해시와 일치).
- 스크립트 `h2_manifest_merge.py`가 하는 점검(하나라도 어긋나면 `STOP`, 아무것도 쓰지 않음):
  1. 11.1 해시 목록이 기대한 14개 경로를 담고, 태그 클론 HEAD가 `eacd57d…`이고, 태그 클론의 14개 파일이 11.1 해시와 같습니다.
  2. main 클론이 `main`이 아닌 새 브랜치에 있고 HEAD가 `origin/main`과 같습니다(커밋 전).
  3. 판독의 `MANIFEST.json`이 엔진 형식 그대로이고, 새 행이 맨 끝에 있고, 그 행이 판독이 쓰는 모양(파일 이름, 종목 전부, yfinance, 5m, 60d, 저장 날짜 2026-11-05)이며, 행의 sha256이 11.1의 `.csv.gz` 해시와 같습니다.
  4. 판독이 태그의 다른 행을 하나도 바꾸지 않았습니다(태그 커밋의 파일과 비교).
  5. main HEAD의 `MANIFEST.json`이 엔진 형식이고 그 행이 아직 없습니다. 합친 뒤 main의 행은 그대로이고 순서도 같으며, 새 행은 맨 끝에 있고 판독의 행과 같습니다.
  6. 차이의 모양이 "행 하나 추가"뿐입니다(지운 줄 0개, 더한 줄 base 42개, krx 36개).
- 순서: dry run(아무것도 쓰지 않음, 차이를 화면에 보임) → 소유자가 차이를 봄 → `--write`. `--write`도 같은 점검을 처음부터 다시 하고, 모두 통과할 때만 씁니다. 같은 내용이 이미 써져 있으면 다시 쓰지 않습니다.
- 경우별 동작:

| main의 상태 | 스크립트 | 결과 |
|---|---|---|
| main 파일 = 태그 파일 | 행 추가 | 판독 파일과 바이트까지 같음. 12절에서 `OK` |
| main에 태그 뒤 행이 더 있거나 줄바꿈이 다름 | 행 추가, main의 줄바꿈 유지 | 바이트는 다름. 12절에서 `MERGED`(정상) |
| main과 태그 모두 파일을 추적하지 않음 | 판독 파일을 그대로 씀(그 행만 들어 있음) | 새 파일 `??`. 더한 줄 base 44개, krx 38개 |
| main에 이미 그 행이 있음 / main 파일이 엔진 형식이 아님 / 태그는 추적하는데 main에 없음 | `STOP` | 멈추고 보고. Claude가 다른 방법을 설계합니다 |

### 2.3 `verdict.json`의 `frozen_file` `[확인 필요 #6]`

- `verdict.json`에는 `frozen_file` 필드가 있고, 값은 판독 때의 절대 경로입니다(`verdict.py:172`, `str(E.OUT / FROZEN_FILE)`). 즉 `C:\Users\whydi\QUANTGEN-studies\paper_live\out\HYPOTHESES_frozen.json` 꼴로 Windows 사용자 폴더 이름이 들어 있습니다. 컴퓨터 이름은 없습니다.
- 이 표는 바이트 그대로 넣습니다. 바이트 대조(11.1)가 증거이기 때문입니다. 같은 사용자 폴더 이름은 main 문서에 이미 공개돼 있습니다(예: `docs/ARCHITECTURE_REVIEW.md:4`).

## 3. 멈춤 규칙 (시작 전에 읽기)

- 멈추면 그 단계의 출력에서 기대와 다른 줄 원문만 Claude에게 보냅니다. push 전에는 판정 줄, 평균, p, 날짜별 손익을 넣지 않습니다(H-D7). 두 스크립트의 출력은 그대로 보내도 됩니다.
- 멈춘 뒤 혼자 고치지 않습니다. 파일을 손으로 고치거나, 지우거나, `git reset`·`git checkout`·`git clean`으로 되돌리지 않습니다. push 전이면 아무것도 공개되지 않았습니다.

| 단계 | 신호 | 할 일 |
|---|---|---|
| 어디서든 | 기대와 다른 출력, `Traceback`, `fatal:`, `error:` | 멈춤. 그 줄을 보냄 |
| 4.1, 6.1 | 만들 폴더가 이미 있음(`True`) | 멈춤. 지우거나 덮어쓰지 않음 |
| 4.2, 5 | `paths:`가 14가 아님, `DIFF`, `MISSING` | 멈춤. 태그 클론과 비공개 사본의 파일을 고치지 않음 |
| 5 | 태그 클론 HEAD가 `eacd57d…`가 아님, `git status`에 `paper_live/out/`·`paper_live/out_krx/` 밖의 경로 | 멈춤 |
| 6.2 | 브랜치가 `main`이 아님, HEAD ≠ `origin/main`, 트리가 깨끗하지 않음, `* -text` 없음, 태그 커밋이 조상이 아님 | 멈춤 |
| 6.3 | git 신원이 비어 있지 않은데 `563db54`의 신원과 다름 | 멈춤. 어느 신원으로 커밋할지 정한 뒤 진행 |
| 7 | `git ls-remote`가 무엇이든 출력함 | 멈춤. 같은 이름의 브랜치가 GitHub에 이미 있음 |
| 8.3 | 해시 앞 16자리가 다름 | 그 블록을 다시 붙여 넣고 다시 확인. 두 번째도 다르면 멈춤 |
| 10.1, 10.3 | `RESULT: STOP`, `exit code: 1` | 멈춤. `STOP` 줄을 보냄. `--write`를 돌리지 않음. `MANIFEST.json`을 손으로 고치지 않음 |
| 10.2 | 차이에 `-` 줄이 있음, 새 행 밖의 `+` 줄이 있음 | 멈춤(스크립트가 먼저 `STOP`을 내야 하지만 눈으로도 봄) |
| 11.2 | `RESULT: STOP` | 멈춤. 기록 파일을 고치지 않음 |
| 12 | `DIFF`, `STOP` | 멈춤 |
| 13 | 13줄이 아님, `replay_holdout` 파일이 ` M` | 멈춤. ` M`은 main에 홀드아웃 재생 산출물이 이미 있었다는 뜻입니다. main은 판독을 돌리지 않습니다(분리 스펙 3.1 3번) |
| 14, 15.3 | 13개 밖의 경로, `.csv.gz` | 멈춤. `git add -A`나 `git add .`를 쓰지 않음 |
| 17 | `rejected`, `non-fast-forward`, 인증 실패 | 멈춤. `--force` 금지 |
| 18 | PR에 충돌 표시, 파일 수가 13이 아님, CI 실패 | PR을 고치지 않고 main 세션에 알림 |

## 4. Step 0. 준비

### 4.1 도구 폴더

```powershell
Test-Path C:\Users\whydi\QUANTGEN-h2-tools
```

- 기대: `False`. `True`이면 멈춥니다(이전 시도의 폴더일 수 있음).

```powershell
New-Item -ItemType Directory -Path C:\Users\whydi\QUANTGEN-h2-tools | Out-Null
Test-Path C:\Users\whydi\QUANTGEN-h2-tools -PathType Container
```

- 기대: `True`.
- 이 폴더는 저장소 밖입니다. 스크립트, 해시 목록, 커밋 메시지 파일만 둡니다.

### 4.2 11.1 해시 목록

실행표 11.1에서 보관한 14줄(`<해시 64자>  <상대 경로>`)을 `C:\Users\whydi\QUANTGEN-h2-tools\hashes_11_1.txt`로 저장합니다.

- 텍스트 파일로 보관했으면 그 파일을 이 이름으로 복사합니다(`Copy-Item <보관 파일> C:\Users\whydi\QUANTGEN-h2-tools\hashes_11_1.txt`).
- 아니면 메모장으로 만듭니다. 아래 명령에서 "새 파일을 만드시겠습니까?"에 "예"를 누르고, 14줄을 붙여 넣고, 저장합니다(인코딩 "UTF-8").

```powershell
notepad C:\Users\whydi\QUANTGEN-h2-tools\hashes_11_1.txt
```

- 기대: 메모장이 열립니다. 저장하고 닫습니다.

목록 점검:

```powershell
$tag = "C:\Users\whydi\QUANTGEN-studies"
$want = @{}
Get-Content -LiteralPath C:\Users\whydi\QUANTGEN-h2-tools\hashes_11_1.txt | ForEach-Object {
  if ($_ -match '^\s*([0-9A-Fa-f]{64})\s+(\S.*?)\s*$') {
    $rel = $matches[2]
    if ($rel.StartsWith("$tag\", [System.StringComparison]::OrdinalIgnoreCase)) { $rel = $rel.Substring($tag.Length + 1) }
    $want[$rel] = $matches[1].ToUpper()
  }
}
"paths: $($want.Count)"
$want.Keys | Sort-Object
```

- 기대: `paths: 14`, 그리고 아래 14개 경로(순서는 다를 수 있음).
  - `paper_live\out\replay_holdout\days.csv`, `fills.jsonl`, `summary.json`, `trades.jsonl`
  - `paper_live\out_krx\replay_holdout\days.csv`, `fills.jsonl`, `summary.json`, `trades.jsonl`
  - `paper_live\out\verdict.json`, `paper_live\out_krx\verdict.json`
  - `paper_live\out\data\MANIFEST.json`, `paper_live\out_krx\data\MANIFEST.json`
  - `paper_live\out\data\holdout_5m_60d_20261105.csv.gz`, `paper_live\out_krx\data\holdout_5m_60d_20261105.csv.gz`
- 경로가 `C:\Users\whydi\QUANTGEN-studies\`로 시작하는 줄(준비 5.3 양식)도 받아들입니다. 경로 끝이 `...`로 잘린 줄이 있으면 멈춥니다.

### 4.3 Python

```powershell
$py = "C:\Users\whydi\QUANTGEN-h2venv\Scripts\python.exe"; if (-not (Test-Path -LiteralPath $py)) { $py = (Get-Command python).Source }
$py
& $py -I -B -c "import sys; print(sys.version.split()[0])"
```

- 기대: 1줄은 `C:\Users\whydi\QUANTGEN-h2venv\Scripts\python.exe`(판독 venv). venv를 지웠으면 전역 Python 경로가 나옵니다. 2줄은 `3.13.x`. `python`을 찾지 못한다는 오류가 나면 멈춥니다.
- 두 스크립트는 표준 라이브러리만 씁니다. 어느 쪽이든 됩니다. `-I`는 현재 폴더의 파일을 모듈로 읽지 않게 하고, `-B`는 `.pyc`를 쓰지 않게 합니다.
- 아래 블록마다 첫 줄에서 `$py`를 다시 정합니다. 창을 새로 열어도 됩니다.

## 5. Step 1. 소스 점검 (태그 클론, 읽기만)

```powershell
Set-Location C:\Users\whydi\QUANTGEN-studies
git rev-parse HEAD
git status --porcelain --untracked-files=all
```

- 기대 1줄: `eacd57d2b0821ad796ab9b66d2d2c96a3d71081f`.
- 그다음 줄들: 실행표 10.1과 같은 목록. 모든 경로가 `paper_live/out/` 또는 `paper_live/out_krx/`로 시작합니다. 판독 뒤 새 경로가 생겼으면 멈춥니다.

```powershell
$tag = "C:\Users\whydi\QUANTGEN-studies"
$want = @{}
Get-Content -LiteralPath C:\Users\whydi\QUANTGEN-h2-tools\hashes_11_1.txt | ForEach-Object {
  if ($_ -match '^\s*([0-9A-Fa-f]{64})\s+(\S.*?)\s*$') {
    $rel = $matches[2]
    if ($rel.StartsWith("$tag\", [System.StringComparison]::OrdinalIgnoreCase)) { $rel = $rel.Substring($tag.Length + 1) }
    $want[$rel] = $matches[1].ToUpper()
  }
}
foreach ($rel in ($want.Keys | Sort-Object)) {
  $p = Join-Path $tag $rel
  if (-not (Test-Path -LiteralPath $p)) { "MISSING  $rel"; continue }
  $h = (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash
  "{0}  {1}" -f $(if ($h -eq $want[$rel]) { "OK  " } else { "DIFF" }), $rel
}
Test-Path -LiteralPath C:\Users\whydi\QUANTGEN-h2-private\H2_READOUT_RECORD.txt
```

- 기대: `OK  `로 시작하는 14줄, 마지막 줄 `True`.
- 판독 뒤 산출물이 한 바이트도 바뀌지 않았다는 확인입니다. 10절의 스크립트도 같은 점검을 다시 합니다.

## 6. Step 2. 새 main 클론

### 6.1 폴더가 비어 있는지

```powershell
Test-Path C:\Users\whydi\QUANTGEN-h2-main
```

- 기대: `False`. `True`이면 멈춥니다.

### 6.2 GitHub `main`에서 복제

```powershell
Set-Location C:\Users\whydi
git clone --branch main https://github.com/xkg4real/quantgen.git QUANTGEN-h2-main
```

- 기대: `Cloning into 'QUANTGEN-h2-main'...`, 진행 줄들(`Receiving objects: 100%`, `Resolving deltas: 100%`, `Updating files: 100%`). `detached HEAD` 안내는 나오지 않습니다.
- GitHub 로그인 창이 뜨면 평소 계정으로 로그인합니다.
- `Filename too long`이나 네트워크 오류가 나면 멈춥니다. 반쯤 만들어진 폴더는 그대로 둡니다.

```powershell
Set-Location C:\Users\whydi\QUANTGEN-h2-main
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD origin/main
git status --porcelain
Test-Path .git -PathType Container
Get-Content .gitattributes
git merge-base --is-ancestor eacd57d2b0821ad796ab9b66d2d2c96a3d71081f HEAD; "tag commit is an ancestor: $($LASTEXITCODE -eq 0)"
git log -1 --format="%h %ci %s" HEAD
```

- 기대:
  1. `main`
  2. 같은 40자 해시 두 줄(그때의 main 끝. Claude가 11-05에 읽은 끝은 `a41fd7a…`이고, 더 뒤의 커밋이어도 됩니다)
  3. 출력 없음
  4. `True`
  5. `# Byte-exact: frozen studies pin file sha256s, so never convert line endings.`와 `* -text`
  6. `tag commit is an ancestor: True`
  7. 한 줄. **앞의 짧은 해시를 적어 둡니다**(PR 본문의 "main 기준 커밋").

### 6.3 커밋 신원

```powershell
Set-Location C:\Users\whydi\QUANTGEN-h2-main
git config user.name
git config user.email
git log -1 --format="%an <%ae>" 563db54
```

- 기대: 1, 2줄이 3줄의 이름, 이메일과 같습니다. 3줄은 소유자가 커밋한 7A.3 기록 커밋 `563db54`의 신원입니다.
- 1, 2줄이 비어 있으면(전역 설정이 없으면) 아래로 **이 클론에만** 같은 신원을 설정하고 위 블록을 다시 돌립니다. 전역 설정은 바꾸지 않습니다.

```powershell
Set-Location C:\Users\whydi\QUANTGEN-h2-main
git config user.name "$(git log -1 --format=%an 563db54)"
git config user.email "$(git log -1 --format=%ae 563db54)"
```

- 기대: 출력 없음.
- 비어 있지 않은데 다르면 멈춥니다.

## 7. Step 3. 작업 브랜치 `[확인 필요 #2]`

```powershell
Set-Location C:\Users\whydi\QUANTGEN-h2-main
git ls-remote --heads origin owner/h2-readout-outputs-20261105
git switch -c owner/h2-readout-outputs-20261105
git rev-parse --abbrev-ref HEAD
```

- 기대: 1줄 명령은 출력 없음(GitHub에 같은 이름이 없음). `Switched to a new branch 'owner/h2-readout-outputs-20261105'`. 마지막 줄 `owner/h2-readout-outputs-20261105`.
- `git switch`를 모른다는 오류가 나면(git 2.23 이전) 같은 자리에서 `git checkout -b owner/h2-readout-outputs-20261105`를 씁니다.

## 8. Step 4. 스크립트 두 개 만들기

블록 하나를 통째로 복사해 붙여 넣습니다. `@'`부터 `'@`까지가 스크립트입니다. 마지막 `'@`는 줄의 맨 앞에 있어야 합니다. 붙여 넣는 동안 `>>`로 시작하는 줄이 이어지는 것은 정상입니다.

### 8.1 `h2_manifest_merge.py` (MANIFEST 행 합치기)

```powershell
$code = @'
"""H2 main commit (H-D5, H-D6): add the holdout snapshot's row to main's paper_live/out*/data/MANIFEST.json.

Reads only, unless --write: the tag clone (its outputs and git objects), the 11.1 hash list and the new main
clone. With --write it writes only <main>/paper_live/out/data/MANIFEST.json and .../out_krx/data/MANIFEST.json.
The format is paper_live/engine.py save_bars(): json.dumps(manifest, indent=1, default=str), no final newline,
the platform's line breaks; a new snapshot is a new key appended last.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

TAG_COMMIT = "eacd57d2b0821ad796ab9b66d2d2c96a3d71081f"
# every ticker of a complete pull, sorted as save_bars() stores them (the tag's config.py UNIVERSE + INVERSE_ETFS)
PROFILES = {
    "paper_live/out": ("AUDUSD=X AZN.L CL=F ES=F EURUSD=X GBPUSD=X GC=F GLD HSBA.L HYG IEF ISF.L IWM NQ=F PSQ QQQ "
                       "RTY=F RWM SH SHEL.L SPY TBF TLT USDJPY=X USO ZB=F ZN=F").split(),
    "paper_live/out_krx": ("000660.KS 005380.KS 005930.KS 069500.KS 105560.KS 114800.KS 132030.KS 148070.KS "
                           "229200.KS 251340.KS 261240.KS 261250.KS AUDUSD=X CL=F ES=F EURUSD=X GC=F KRW=X NQ=F "
                           "USDJPY=X ZN=F").split(),
}
REPLAY_FILES = ("days.csv", "fills.jsonl", "summary.json", "trades.jsonl")
problems, written = [], []


def stop(msg):
    problems.append(msg)
    print("  STOP  " + msg)


def ok(msg):
    print("  ok    " + msg)


def info(msg):
    print("  info  " + msg)


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def git(repo, *args):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", "replace").strip()


def blob(repo, rev, rel):
    if subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{rev}:{rel}"], capture_output=True).returncode:
        return None
    r = subprocess.run(["git", "-C", str(repo), "cat-file", "blob", f"{rev}:{rel}"], capture_output=True)
    if r.returncode:
        raise SystemExit(f"git cat-file blob {rev}:{rel} failed in {repo}")
    return r.stdout


def style(b):
    lf, crlf = b.count(b"\n"), b.count(b"\r\n")
    if lf == 0 and b"\r" not in b:
        return ""
    if crlf == lf and b.count(b"\r") == crlf:
        return "\r\n"
    if crlf == 0 and b"\r" not in b:
        return "\n"
    return "mixed"


def name(nl):
    return {"\r\n": "CRLF", "\n": "LF", "": "one line"}.get(nl, nl)


def rows(n):
    return f"{n} row" + ("" if n == 1 else "s")


def dump(d, nl):
    return json.dumps(d, indent=1, default=str).replace("\n", nl or "\n").encode("ascii")


def engine_format(b):
    """(dict, line style) if b is exactly what save_bars() writes, else (None, reason)."""
    nl = style(b)
    if nl == "mixed":
        return None, "mixed line breaks"
    try:
        d = json.loads(b.decode("ascii"))
    except (UnicodeDecodeError, ValueError) as e:
        return None, f"not ASCII JSON ({e.__class__.__name__})"
    if not isinstance(d, dict):
        return None, "not a JSON object"
    if dump(d, nl) != b:
        return None, "not in json.dumps(indent=1) form"
    return d, nl


def read_hashes(p, tag):
    """11.1 lines '<sha256>  <path>'; a path given from the tag clone's root down is made relative."""
    root = str(tag).replace("\\", "/").rstrip("/").lower() + "/"
    raw = Path(p).read_bytes()
    text = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8-sig", "replace")
    out = {}
    for line in text.splitlines():
        m = re.match(r"^\s*([0-9A-Fa-f]{64})\s+(\S.*?)\s*$", line)
        if m:
            rel = m.group(2).replace("\\", "/")
            out[rel[len(root):] if rel.lower().startswith(root) else rel] = m.group(1).upper()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--main", required=True)
    ap.add_argument("--hashes", required=True)
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    tag, mainc, snap = Path(a.tag), Path(a.main), a.snapshot
    print(f"mode: {'WRITE' if a.write else 'DRY RUN (writes nothing)'}")

    print("[sources]")
    want = read_hashes(a.hashes, tag)
    expected = set()
    for d in PROFILES:
        expected |= {f"{d}/replay_holdout/{f}" for f in REPLAY_FILES}
        expected |= {f"{d}/verdict.json", f"{d}/data/MANIFEST.json", f"{d}/data/{snap}.csv.gz"}
    if set(want) != expected:
        stop(f"11.1 hash list: {len(want)} lines; missing {sorted(expected - set(want))}, extra {sorted(set(want) - expected)}")
        return finish(a)
    ok("11.1 hash list: the 14 expected paths")
    code, head = git(tag, "rev-parse", "HEAD")
    if code or head != TAG_COMMIT:
        stop(f"tag clone HEAD is {head!r}, want {TAG_COMMIT}")
        return finish(a)
    ok(f"tag clone HEAD {TAG_COMMIT[:12]}")
    changed = [rel for rel in sorted(want) if not (tag / rel).is_file() or sha((tag / rel).read_bytes()) != want[rel]]
    if changed:
        stop(f"tag clone files differ from 11.1 or are missing: {changed}")
        return finish(a)
    ok("tag clone: all 14 files equal their 11.1 sha256")
    code, branch = git(mainc, "rev-parse", "--abbrev-ref", "HEAD")
    c1, mh = git(mainc, "rev-parse", "HEAD")
    c2, om = git(mainc, "rev-parse", "origin/main")
    if code or c1 or c2 or branch in ("HEAD", "main") or branch.startswith("claude/") or mh != om:
        stop(f"main clone: branch {branch!r}, HEAD {mh[:12]}, origin/main {om[:12]}; want a new branch at origin/main")
        return finish(a)
    ok(f"main clone: branch {branch}, HEAD = origin/main {om[:12]}")

    plans = []
    for d, tickers in PROFILES.items():
        n_tickers = len(tickers)
        rel = f"{d}/data/MANIFEST.json"
        print(f"[{d}]")
        src = (tag / rel).read_bytes()
        src_d, src_nl = engine_format(src)
        if src_d is None:
            stop(f"readout {rel}: {src_nl}")
            continue
        ok(f"readout MANIFEST.json: sha256 = 11.1, engine format ({name(src_nl)}), {rows(len(src_d))}")
        if list(src_d)[-1:] != [snap]:
            stop(f"readout MANIFEST.json: {snap} is not its last row")
            continue
        row = src_d[snap]
        checks = [row.get("file") == f"{snap}.csv.gz", row.get("tickers") == tickers,
                  row.get("source") == "yfinance", row.get("interval") == "5m", row.get("period") == "60d",
                  str(row.get("saved_utc", ""))[:10].replace("-", "") == snap[-8:]]
        if not all(checks):
            stop(f"row {snap}: file/tickers/source/interval/period/saved_utc not as the readout writes them: {checks}")
            continue
        ok(f"row {snap}: the {n_tickers} tickers of a complete pull, yfinance 5m 60d, saved {row['saved_utc']}, rows {row.get('rows')}")
        if str(row.get("sha256", "")).upper() != want[f"{d}/data/{snap}.csv.gz"]:
            stop(f"row {snap}: its sha256 is not the 11.1 hash of the snapshot .csv.gz")
            continue
        ok("row sha256 = 11.1 hash of the snapshot .csv.gz")
        old = blob(tag, "HEAD", rel)
        if old is None:
            tag_d = None
            if list(src_d) != [snap]:
                stop("the tag does not track MANIFEST.json, yet the readout's file has other rows")
                continue
            ok("the tag does not track MANIFEST.json; the readout's file holds only this row")
        else:
            tag_d, tag_nl = engine_format(old)
            if tag_d is None:
                stop(f"tag HEAD {rel}: {tag_nl}")
                continue
            rest = {k: v for k, v in src_d.items() if k != snap}
            if snap in tag_d or list(rest) != list(tag_d) or rest != tag_d:
                stop("the readout changed rows other than its own, or the tag already had this row")
                continue
            ok(f"the readout added this one row and changed none of the tag's {rows(len(tag_d))}")

        base = blob(mainc, "HEAD", rel)
        dst = mainc / rel
        if base is None:
            if tag_d is not None:
                stop(f"main does not track {rel}, but the tag does")
                continue
            new = src
            info("main does not track MANIFEST.json either: the new file is the readout's file, byte for byte")
            diff_from = []
        else:
            main_d, main_nl = engine_format(base)
            if main_d is None:
                stop(f"main HEAD {rel}: {main_nl}")
                continue
            if snap in main_d:
                stop(f"main HEAD {rel} already has a row {snap}")
                continue
            ok(f"main HEAD MANIFEST.json: {rows(len(main_d))}, engine format ({name(main_nl)}), no {snap} row")
            if tag_d is not None:
                only_main = [k for k in main_d if k not in tag_d]
                only_tag = [k for k in tag_d if k not in main_d]
                differ = [k for k in main_d if k in tag_d and main_d[k] != tag_d[k]]
                same_order = list(main_d) == list(tag_d)
                info(f"main vs tag rows: {len(only_main)} only in main, {len(only_tag)} only in the tag, "
                     f"{len(differ)} different, same order: {'yes' if same_order else 'no'}")
            new_d = dict(main_d)
            new_d[snap] = row
            new = dump(new_d, main_nl or src_nl)
            back = json.loads(new.decode("ascii"))
            if list(back) != list(main_d) + [snap] or any(back[k] != main_d[k] for k in main_d) or back[snap] != row:
                stop("merge self-check failed")
                continue
            ok(f"after merge: main's {rows(len(main_d))} unchanged and in order, this row added last, equal to the readout's")
            diff_from = base.decode("ascii").splitlines()
        a_lines = diff_from
        b_lines = new.decode("ascii").splitlines()
        pre = 0
        while pre < min(len(a_lines), len(b_lines)) and a_lines[pre] == b_lines[pre]:
            pre += 1
        suf = 0
        while (suf < min(len(a_lines), len(b_lines)) - pre
               and a_lines[len(a_lines) - 1 - suf] == b_lines[len(b_lines) - 1 - suf]):
            suf += 1
        removed = a_lines[pre:len(a_lines) - suf]
        added = b_lines[pre:len(b_lines) - suf]
        print(f"  ---- diff of {rel}: main HEAD -> after merge (lines {pre + 1}..) ----")
        for x in a_lines[max(pre - 1, 0):pre]:
            print("  |  " + x)
        for x in removed:
            print("  | -" + x)
        for x in added:
            print("  | +" + x)
        for x in a_lines[len(a_lines) - suf:][:2]:
            print("  |  " + x)
        print("  ---- end of diff ----")
        if not diff_from:
            shape = (len(removed), len(added)) == (0, n_tickers + 17)
        elif diff_from == ["{}"]:
            shape = (len(removed), len(added)) == (1, n_tickers + 17)
        else:
            shape = ((len(removed), len(added)) == (0, n_tickers + 15)
                     and added[:2] == [" },", f' "{snap}": {{'])
        if not shape:
            stop(f"diff shape: {len(removed)} removed, {len(added)} added; not the one-row append expected")
            continue
        ok(f"diff shape: {len(removed)} line(s) removed, {len(added)} added = the one-row append")
        eq = "equal" if sha(new) == want[rel] else "different (main's rows or line breaks differ from the tag's)"
        info(f"merged file sha256 {sha(new)[:16]}..., to the 11.1 MANIFEST.json hash: {eq}")
        cur = dst.read_bytes() if dst.is_file() else None
        if cur == new:
            state = "already written (identical)"
        elif cur == base:
            state = "not written yet"
        else:
            stop(f"{rel} in the main clone is neither main's HEAD version nor the merge result")
            continue
        info(f"state: {state}")
        plans.append((dst, new, state))

    if a.write and not problems:
        for dst, new, state in plans:
            if state == "not written yet":
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(new)
                if dst.read_bytes() != new:
                    stop(f"{dst}: read-back differs")
                else:
                    written.append(dst)
                    print(f"  WROTE {dst} sha256 {sha(new)}")
    return finish(a)


def finish(a):
    if problems:
        print(f"RESULT: STOP ({len(problems)} problem(s)); files written: {len(written)}. Send these STOP lines to Claude.")
        return 1
    print("RESULT: OK, " + (f"write mode, files written now: {len(written)}" if a.write else "dry run, nothing written"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'@
[System.IO.File]::WriteAllText("C:\Users\whydi\QUANTGEN-h2-tools\h2_manifest_merge.py", $code, (New-Object System.Text.UTF8Encoding($false)))
"written: $($code.Length) chars"
```

- 기대: `written: <숫자> chars`. 숫자는 줄바꿈 방식에 따라 다릅니다. 내용은 8.3에서 확인합니다.

### 8.2 `h2_record_check.py` (짧은 기록 점검)

```powershell
$code = @'
"""H2 main commit (H-D11): check the short record file against the copied verdict.json files.

Prints ok/STOP lines only, never the verdict lines themselves. Reads only.
argv: <main clone> <record in the main clone> <record in the private copy>
"""
import json
import os
import sys
from pathlib import Path

WANT = ["H2 holdout readout record (H-D11)", "yfinance: 1.4.1",
        "start_utc: 2026-11-05T06:45:16Z", "end_utc: 2026-11-05T06:55:54Z"]
SNAP = "holdout_5m_60d_20261105"
problems = []


def check(cond, msg):
    print(("  ok    " if cond else "  STOP  ") + msg)
    if not cond:
        problems.append(msg)


def gate_line(v):
    """paper_live/verdict.py main(), the H2 print, word for word."""
    h2 = v["H2"]
    return (f"H2 cost gate ({v['profile']}): {h2['status']}"
            + (f" ({h2['sessions']} of {h2['planned']} sessions)" if "planned" in h2 else "")
            + (f"; mean {h2['mean_diff']:+.2f} a session, p {h2['p_one_sided']:.3f}" if "p_one_sided" in h2 else ""))


def main():
    mainc, rec, private = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    raw = rec.read_bytes()
    check(raw == private.read_bytes(), "record file: same bytes as the private copy")
    if raw.startswith(b"\xef\xbb\xbf"):
        print("  info  record file starts with a UTF-8 byte-order mark (kept as is)")
        raw = raw[3:]
    text = raw.decode("utf-8", "replace")
    lines = text.splitlines()
    check(len(lines) == 6, f"record file: {len(lines)} lines (want 6)")
    for i, w in enumerate(WANT):
        check(i < len(lines) and lines[i] == w, f"record line {i + 1}: '{w}'")
    for i, d, prof in ((4, "paper_live/out", "base"), (5, "paper_live/out_krx", "krx")):
        v = json.loads((mainc / d / "verdict.json").read_text(encoding="utf-8"))
        h2 = v.get("H2", {})
        check(v.get("profile") == prof, f"{d}/verdict.json: profile {prof}")
        check(h2.get("status") in ("confirmed", "not confirmed"), f"{d}/verdict.json: H2 final")
        check(h2.get("sessions") == 10 and h2.get("days") == ["2026-10-21", "2026-11-03"],
              f"{d}/verdict.json: 10 sessions 2026-10-21..2026-11-03")
        check(h2.get("snapshot") == SNAP, f"{d}/verdict.json: snapshot {SNAP}")
        check(i < len(lines) and lines[i] == gate_line(v),
              f"record line {i + 1}: equals verdict.py's H2 line rebuilt from {d}/verdict.json")
        print(f"  info  {d}/verdict.json frozen_file: {v.get('frozen_file')}")
    for var in ("COMPUTERNAME", "USERDOMAIN", "USERNAME"):
        val = os.environ.get(var, "")
        check(not val or val.lower() not in text.lower(), f"record file: no {var}")
    if problems:
        print(f"RESULT: STOP ({len(problems)} problem(s)). Send these STOP lines to Claude.")
        return 1
    print("RESULT: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'@
[System.IO.File]::WriteAllText("C:\Users\whydi\QUANTGEN-h2-tools\h2_record_check.py", $code, (New-Object System.Text.UTF8Encoding($false)))
"written: $($code.Length) chars"
```

- 기대: `written: <숫자> chars`.

### 8.3 붙여 넣기가 온전한지

```powershell
$py = "C:\Users\whydi\QUANTGEN-h2venv\Scripts\python.exe"; if (-not (Test-Path -LiteralPath $py)) { $py = (Get-Command python).Source }
foreach ($f in "h2_manifest_merge.py", "h2_record_check.py") {
  & $py -I -B -c "import hashlib, sys; b = open(sys.argv[1], 'rb').read().replace(b'\r\n', b'\n').lstrip(b'\xef\xbb\xbf').rstrip(b'\n'); print(hashlib.sha256(b).hexdigest()[:16], sys.argv[1])" "C:\Users\whydi\QUANTGEN-h2-tools\$f"
}
```

- 기대 두 줄:
  - `0f6685cb36a0c7f1 C:\Users\whydi\QUANTGEN-h2-tools\h2_manifest_merge.py`
  - `c067d316fda5ee5f C:\Users\whydi\QUANTGEN-h2-tools\h2_record_check.py`
- 줄바꿈 방식과 BOM은 빼고 비교합니다. 다르면 그 스크립트의 블록을 다시 붙여 넣습니다.
- 메모장으로 만들어도 됩니다(스크립트 부분만 붙여 넣고 UTF-8로 저장). 그때도 이 점검을 합니다.

## 9. Step 5. 산출물 10개 복사 (태그 클론 → 새 main 클론)

```powershell
$tag = "C:\Users\whydi\QUANTGEN-studies"; $main = "C:\Users\whydi\QUANTGEN-h2-main"; $n = 0
foreach ($d in "paper_live\out", "paper_live\out_krx") {
  New-Item -ItemType Directory -Force -Path "$main\$d\replay_holdout" | Out-Null
  foreach ($f in "days.csv", "fills.jsonl", "summary.json", "trades.jsonl") {
    Copy-Item -LiteralPath "$tag\$d\replay_holdout\$f" -Destination "$main\$d\replay_holdout\$f"; $n++
  }
  Copy-Item -LiteralPath "$tag\$d\verdict.json" -Destination "$main\$d\verdict.json"; $n++
}
"copied $n"
```

- 기대: `copied 10`.
- 태그 클론에서는 읽기만 합니다(`Copy-Item`은 원본을 바꾸지 않음). `.csv.gz`와 `MANIFEST.json`은 복사하지 않습니다.

## 10. Step 6. `MANIFEST.json` 행 합치기

### 10.1 dry run (아무것도 쓰지 않음)

```powershell
$py = "C:\Users\whydi\QUANTGEN-h2venv\Scripts\python.exe"; if (-not (Test-Path -LiteralPath $py)) { $py = (Get-Command python).Source }
& $py -I -B C:\Users\whydi\QUANTGEN-h2-tools\h2_manifest_merge.py --tag C:\Users\whydi\QUANTGEN-studies --main C:\Users\whydi\QUANTGEN-h2-main --hashes C:\Users\whydi\QUANTGEN-h2-tools\hashes_11_1.txt --snapshot holdout_5m_60d_20261105
"exit code: $LASTEXITCODE"
```

- 기대(차례로):
  - `mode: DRY RUN (writes nothing)`
  - `[sources]` 아래 `ok` 4줄: 해시 목록 14개, 태그 클론 HEAD `eacd57d2b082`, 14개 파일 = 11.1, main 클론 `branch owner/h2-readout-outputs-20261105, HEAD = origin/main <해시>`
  - `[paper_live/out]` 아래:
    - `ok    readout MANIFEST.json: sha256 = 11.1, engine format (CRLF), <n> rows`
    - `ok    row holdout_5m_60d_20261105: the 27 tickers of a complete pull, yfinance 5m 60d, saved 2026-11-05T06:..., rows <n>`
    - `ok    row sha256 = 11.1 hash of the snapshot .csv.gz`
    - `ok    the readout added this one row and changed none of the tag's <n> rows`
    - `ok    main HEAD MANIFEST.json: <n> rows, engine format (CRLF), no holdout_5m_60d_20261105 row`
    - `info  main vs tag rows: ...`
    - `ok    after merge: ...`
    - 차이(10.2에서 봄)
    - `ok    diff shape: 0 line(s) removed, 42 added = the one-row append`
    - `info  merged file sha256 ..., to the 11.1 MANIFEST.json hash: equal` 또는 `different (...)`. **어느 쪽인지 적어 둡니다**(12절에서 씀)
    - `info  state: not written yet`
  - `[paper_live/out_krx]` 아래 같은 줄들. 종목 21개, 더한 줄 36개.
  - `RESULT: OK, dry run, nothing written`
  - `exit code: 0`
- main과 태그 모두 파일을 추적하지 않으면 `the tag does not track MANIFEST.json; ...`와 `info  main does not track MANIFEST.json either: ...`가 나오고, 더한 줄이 44개, 38개입니다. 정상입니다.
- `main HEAD MANIFEST.json` 줄에 `(LF)`가 나와도 정상입니다. 스크립트는 main 파일의 줄바꿈을 따릅니다.
- `STOP`이 하나라도 있으면 3절대로 멈춥니다.

### 10.2 차이 보기 (소유자가 눈으로)

프로필마다 `---- diff of ... ----`와 `---- end of diff ----` 사이를 봅니다. 스크립트는 줄 앞에 세로 막대와 빈칸을 붙여 찍습니다. 그 뒤의 첫 글자가 빈칸이면 바뀌지 않는 줄, `-`이면 지우는 줄, `+`이면 더하는 줄입니다.

- 맨 위: 바뀌지 않는 줄 하나(앞 행의 마지막 줄).
- `-` 줄: 없어야 합니다.
- 첫 두 `+` 줄: `+ },`와 `+ "holdout_5m_60d_20261105": {`.
- 그다음 `+` 줄: `"file": "holdout_5m_60d_20261105.csv.gz"`, `"sha256": "<소문자 64자>"`(11.1의 `.csv.gz` 해시를 소문자로 쓴 값), `"tickers": [`, 종목 줄(base 27개, krx 21개), `],`, `"rows"`, `"first"`, `"last"`, `"saved_utc"`, `"source": "yfinance"`, `"interval": "5m"`, `"period": "60d"`, `"start": null`, `"end": null`.
- 맨 아래: 바뀌지 않는 줄 두 개(` }`와 `}`).
- 행 밖의 줄이 바뀌거나 지워지면 멈춥니다.

### 10.3 쓰기

```powershell
$py = "C:\Users\whydi\QUANTGEN-h2venv\Scripts\python.exe"; if (-not (Test-Path -LiteralPath $py)) { $py = (Get-Command python).Source }
& $py -I -B C:\Users\whydi\QUANTGEN-h2-tools\h2_manifest_merge.py --tag C:\Users\whydi\QUANTGEN-studies --main C:\Users\whydi\QUANTGEN-h2-main --hashes C:\Users\whydi\QUANTGEN-h2-tools\hashes_11_1.txt --snapshot holdout_5m_60d_20261105 --write
"exit code: $LASTEXITCODE"
```

- 기대: 첫 줄 `mode: WRITE`, 10.1과 같은 점검 줄과 차이, 그리고
  - `  WROTE C:\Users\whydi\QUANTGEN-h2-main\paper_live\out\data\MANIFEST.json sha256 <64자>`
  - `  WROTE C:\Users\whydi\QUANTGEN-h2-main\paper_live\out_krx\data\MANIFEST.json sha256 <64자>`
  - `RESULT: OK, write mode, files written now: 2`
  - `exit code: 0`
- 한 번 더 돌리면 `state: already written (identical)`와 `files written now: 0`이 나옵니다. 정상입니다.

### 10.4 git이 보는 차이

```powershell
Set-Location C:\Users\whydi\QUANTGEN-h2-main
git diff --stat -- paper_live/out/data/MANIFEST.json paper_live/out_krx/data/MANIFEST.json
```

- 기대:
  - `paper_live/out/data/MANIFEST.json     | 42 ++++...`
  - `paper_live/out_krx/data/MANIFEST.json | 36 ++++...`
  - ` 2 files changed, 78 insertions(+)` (지운 줄 없음)
- main이 이 파일을 추적하지 않던 경우(10.1의 `main does not track`)는 출력이 없습니다. 13절에서 `??`로 보입니다.

## 11. Step 7. 짧은 기록 파일

### 11.1 복사

```powershell
Copy-Item -LiteralPath C:\Users\whydi\QUANTGEN-h2-private\H2_READOUT_RECORD.txt -Destination C:\Users\whydi\QUANTGEN-h2-main\paper_live\H2_READOUT_RECORD_2026-11-05.txt
Test-Path C:\Users\whydi\QUANTGEN-h2-main\paper_live\H2_READOUT_RECORD_2026-11-05.txt
```

- 기대: `True`.
- 비공개 사본의 원본은 그대로 둡니다.

### 11.2 점검

```powershell
$py = "C:\Users\whydi\QUANTGEN-h2venv\Scripts\python.exe"; if (-not (Test-Path -LiteralPath $py)) { $py = (Get-Command python).Source }
& $py -I -B C:\Users\whydi\QUANTGEN-h2-tools\h2_record_check.py C:\Users\whydi\QUANTGEN-h2-main C:\Users\whydi\QUANTGEN-h2-main\paper_live\H2_READOUT_RECORD_2026-11-05.txt C:\Users\whydi\QUANTGEN-h2-private\H2_READOUT_RECORD.txt
"exit code: $LASTEXITCODE"
```

- 기대: `ok` 19줄, `info` 2줄, `RESULT: OK`, `exit code: 0`.
  - `ok    record file: same bytes as the private copy`
  - `ok    record file: 6 lines (want 6)`
  - `ok    record line 1: 'H2 holdout readout record (H-D11)'`, line 2 `yfinance: 1.4.1`, line 3 `start_utc: 2026-11-05T06:45:16Z`, line 4 `end_utc: 2026-11-05T06:55:54Z`
  - 프로필마다: `profile`, `H2 final`, `10 sessions 2026-10-21..2026-11-03`, `snapshot holdout_5m_60d_20261105`, `record line 5`(또는 6)`: equals verdict.py's H2 line rebuilt from .../verdict.json`
  - `info  paper_live/out/verdict.json frozen_file: C:\Users\whydi\QUANTGEN-studies\paper_live\out\HYPOTHESES_frozen.json`(krx도 한 줄)
  - `ok    record file: no COMPUTERNAME`, `no USERDOMAIN`, `no USERNAME`
- 이 스크립트는 판정 줄 자체를 화면에 찍지 않습니다. 5, 6줄이 `verdict.json`에서 `verdict.py`의 출력 형식대로 다시 만든 줄과 글자까지 같은지만 봅니다(공개 기록 3번의 확인).
- 1~4줄의 기대값은 실행표 12절의 형식과 판독 사실입니다. 다르게 나오면 멈춥니다. 기록 파일을 고칠지는 Claude와 함께 정합니다.

## 12. Step 8. 11.1 해시와 바이트 대조 (새 main 클론)

```powershell
$tag = "C:\Users\whydi\QUANTGEN-studies"; $main = "C:\Users\whydi\QUANTGEN-h2-main"
$want = @{}
Get-Content -LiteralPath C:\Users\whydi\QUANTGEN-h2-tools\hashes_11_1.txt | ForEach-Object {
  if ($_ -match '^\s*([0-9A-Fa-f]{64})\s+(\S.*?)\s*$') {
    $rel = $matches[2]
    if ($rel.StartsWith("$tag\", [System.StringComparison]::OrdinalIgnoreCase)) { $rel = $rel.Substring($tag.Length + 1) }
    $want[$rel] = $matches[1].ToUpper()
  }
}
foreach ($rel in ($want.Keys | Sort-Object)) {
  $p = Join-Path $main $rel
  if ($rel -like "*.csv.gz") { "{0}  {1}" -f $(if (Test-Path -LiteralPath $p) { "STOP" } else { "ABSENT-OK" }), $rel; continue }
  $h = (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash
  if ($rel -like "*MANIFEST.json") { "{0}  {1}" -f $(if ($h -eq $want[$rel]) { "OK  " } else { "MERGED" }), $rel; continue }
  "{0}  {1}" -f $(if ($h -eq $want[$rel]) { "OK  " } else { "DIFF" }), $rel
}
```

- 기대 14줄:
  - `OK  ` 10줄: `replay_holdout` 8개와 `verdict.json` 2개. 태그 클론의 원본과 바이트가 같다는 확인입니다.
  - `ABSENT-OK` 2줄: 스냅샷 `.csv.gz`가 새 main 클론에 없습니다(H-D6).
  - `MANIFEST.json` 2줄: 10.1이 `equal`이라 한 프로필은 `OK  `, `different`라 한 프로필은 `MERGED`. 둘 다 정상입니다. `MERGED`이면 행 단위 확인은 10.1의 스크립트가 이미 했습니다(행 = 판독의 행, 행의 sha256 = `.csv.gz`의 11.1 해시).
- `DIFF`나 `STOP`이 있으면 멈춥니다.

## 13. Step 9. 바뀐 파일 목록

```powershell
Set-Location C:\Users\whydi\QUANTGEN-h2-main
git status --porcelain --untracked-files=all
```

- 기대: 정확히 13줄.

```
 M paper_live/out/data/MANIFEST.json
 M paper_live/out/verdict.json
 M paper_live/out_krx/data/MANIFEST.json
 M paper_live/out_krx/verdict.json
?? paper_live/H2_READOUT_RECORD_2026-11-05.txt
?? paper_live/out/replay_holdout/days.csv
?? paper_live/out/replay_holdout/fills.jsonl
?? paper_live/out/replay_holdout/summary.json
?? paper_live/out/replay_holdout/trades.jsonl
?? paper_live/out_krx/replay_holdout/days.csv
?? paper_live/out_krx/replay_holdout/fills.jsonl
?? paper_live/out_krx/replay_holdout/summary.json
?? paper_live/out_krx/replay_holdout/trades.jsonl
```

- 10.1에서 `main does not track MANIFEST.json`이 나왔으면 두 `MANIFEST.json`이 ` M` 대신 `??`로 아래쪽에 나옵니다.
- `replay_holdout` 파일이 ` M`이면 멈춥니다(3절). `.csv.gz`가 보이면 멈춥니다.

## 14. Step 10. 스테이징 (경로를 하나씩)

```powershell
Set-Location C:\Users\whydi\QUANTGEN-h2-main
git add -- paper_live/H2_READOUT_RECORD_2026-11-05.txt paper_live/out/verdict.json paper_live/out_krx/verdict.json paper_live/out/data/MANIFEST.json paper_live/out_krx/data/MANIFEST.json paper_live/out/replay_holdout/days.csv paper_live/out/replay_holdout/fills.jsonl paper_live/out/replay_holdout/summary.json paper_live/out/replay_holdout/trades.jsonl paper_live/out_krx/replay_holdout/days.csv paper_live/out_krx/replay_holdout/fills.jsonl paper_live/out_krx/replay_holdout/summary.json paper_live/out_krx/replay_holdout/trades.jsonl
git diff --cached --name-status
git status --porcelain --untracked-files=all
```

- 기대: `git add`는 출력 없음. 이어서 13줄:

```
A	paper_live/H2_READOUT_RECORD_2026-11-05.txt
M	paper_live/out/data/MANIFEST.json
A	paper_live/out/replay_holdout/days.csv
A	paper_live/out/replay_holdout/fills.jsonl
A	paper_live/out/replay_holdout/summary.json
A	paper_live/out/replay_holdout/trades.jsonl
M	paper_live/out/verdict.json
M	paper_live/out_krx/data/MANIFEST.json
A	paper_live/out_krx/replay_holdout/days.csv
A	paper_live/out_krx/replay_holdout/fills.jsonl
A	paper_live/out_krx/replay_holdout/summary.json
A	paper_live/out_krx/replay_holdout/trades.jsonl
M	paper_live/out_krx/verdict.json
```

- 그다음 `git status`도 13줄이고, 모든 줄의 첫 칸이 `A` 또는 `M`, 둘째 칸이 빈칸입니다(`A  ...`, `M  ...`). `??`나 ` M`이 남으면 멈춥니다.
- `MANIFEST.json`이 새 파일이었던 경우는 그 두 줄이 `A`입니다.

## 15. Step 11. 커밋

### 15.1 커밋 메시지 파일 `[확인 필요 #3, #4, #5]`

영문, ASCII만 씁니다(저장소의 커밋 메시지 관례, 7A.3 소유자 커밋 `fe37e82`, `563db54`의 형식). 공개 기록 문안은 16절의 PR 본문과 같은 내용입니다.

```powershell
$msg = @'
paper_live: H2 holdout readout outputs, both profiles (roadmap 8-1)

The owner ran the pre-registered H2 cost-gate readout once per profile
on 2026-11-05, 06:45:16Z to 06:55:54Z, in a git clone of the tag
studies-of-record-2026-10-23 (commit eacd57d), with a venv pinned to
numpy 2.3.5, scipy 1.18.0 and pandas 2.3.3, and yfinance 1.4.1 (U3).
Both profiles reached a final H2 verdict (confirmed or not confirmed)
on all 10 sessions 2026-10-21..2026-11-03, snapshot
holdout_5m_60d_20261105. The results are in the files below and are
public from this commit on (H-D7).

Copied byte for byte from the tag clone; each sha256 equals the hash
the owner recorded right after the run:
- paper_live/out/replay_holdout/: days.csv, summary.json,
  trades.jsonl, fills.jsonl
- paper_live/out_krx/replay_holdout/: the same four files
- paper_live/out/verdict.json, paper_live/out_krx/verdict.json; their
  frozen_file field keeps the tag clone's absolute path, which names
  the owner's Windows user folder
Added:
- paper_live/out/data/MANIFEST.json and
  paper_live/out_krx/data/MANIFEST.json: one row each,
  holdout_5m_60d_20261105, equal to the row the readout wrote; the
  row's sha256 is the snapshot's. The snapshot .csv.gz stays private
  with the owner (H-D6).
- paper_live/H2_READOUT_RECORD_2026-11-05.txt: the short record
  (H-D11): both H2 verdict lines, the yfinance version, start and end
  time, no machine name.

Disclosures for the public record:
1. H-D13. While drafting the readout preparation on 2026-11-04, a
   Claude session called check (b) of tests/frozen_guard.py directly.
   It reads through git the tag's four code copies
   paper_live/out*/frozen_rule/{engine,config}.py and compares bytes;
   only the pass result was shown. The same session's Linux full run
   that day ran the guard suite over the same blobs (guard/test_b
   PASS). These are code copies, not holdout outputs. Owner ruling
   H-D13: keep it as a public record; Claude sessions may keep running
   the guard suite.
2. Before this commit, the owner pasted the base profile's replay
   output (its date lines and summary JSON) into a Claude chat once.
   H-D7 had limited what Claude receives before the main commit to
   validity items.
3. Windows PowerShell 5.1's transcript did not capture the Python
   output, so the record file's two verdict lines were rebuilt from
   each profile's verdict.json in paper_live/verdict.py's own print
   format, not copied from the screen. A check before this commit
   confirmed that each line equals that rebuild.
4. While writing the run sheet for this commit on 2026-11-05, a Claude
   agent ran git grep on origin/main with the pathspecs
   'paper_live/*.py' and 'grokteam/*.py', which also cover .py files
   under paper_live/out*/ and grokteam/out/. Lines from paper_live/out*
   were filtered out before display; under grokteam/out/ only lines of
   the code copy in frozen_book/ were shown, none from book/. Only .py
   files were searched, so no holdout output file was among them.
'@
[System.IO.File]::WriteAllText("C:\Users\whydi\QUANTGEN-h2-tools\commit_msg.txt", $msg, (New-Object System.Text.UTF8Encoding($false)))
Get-Content C:\Users\whydi\QUANTGEN-h2-tools\commit_msg.txt -TotalCount 1
```

- 기대: `paper_live: H2 holdout readout outputs, both profiles (roadmap 8-1)`.

### 15.2 커밋

```powershell
Set-Location C:\Users\whydi\QUANTGEN-h2-main
git commit -F C:\Users\whydi\QUANTGEN-h2-tools\commit_msg.txt
```

- 기대:
  - `[owner/h2-readout-outputs-20261105 <짧은 해시>] paper_live: H2 holdout readout outputs, both profiles (roadmap 8-1)`
  - ` 13 files changed, <n> insertions(+), <m> deletions(-)`
  - `create mode 100644 ...` 9줄(기록 파일 1, `replay_holdout` 8). `MANIFEST.json`이 새 파일이었으면 11줄.

### 15.3 커밋 점검 (push 전)

```powershell
Set-Location C:\Users\whydi\QUANTGEN-h2-main
git log --oneline origin/main..HEAD
git diff --name-only origin/main HEAD
git diff --name-only origin/main HEAD | Select-String -SimpleMatch ".csv.gz"
git status --porcelain --untracked-files=all
git log -1 --format="%an <%ae>" HEAD
```

- 기대:
  1. 한 줄(방금 만든 커밋)
  2. 14절과 같은 13개 경로
  3. 출력 없음
  4. 출력 없음
  5. 6.3의 신원
- 커밋 뒤에는 10절의 스크립트를 다시 돌리지 않습니다. HEAD가 `origin/main`과 달라 `STOP`을 냅니다(무해하지만 혼동됩니다).

## 16. 공개 기록과 PR 본문

### 16.1 PR 제목

```
paper_live: H2 holdout readout outputs, both profiles (⑧-1)
```

### 16.2 PR 본문 `[확인 필요 #3, #4, #5]`

`<...>` 두 곳(6.2의 main 기준 커밋, 12절의 `OK`/`MERGED`)을 채워 붙여 넣습니다.

```
## 요약

⑧-1 H2 홀드아웃 판독의 산출물을 main에 넣습니다(H-D5: 동결 해제 뒤 별도 클론에서 PR).

- 판독: 소유자가 2026-11-05 06:45:16Z~06:55:54Z에 태그 `studies-of-record-2026-10-23`(커밋 `eacd57d`)의 클론에서 프로필(base, krx)마다 재생 1번, 판정 1번을 실행했습니다.
- 인터프리터: 고정 버전 전용 venv(numpy 2.3.5, scipy 1.18.0, pandas 2.3.3), yfinance 1.4.1(U3).
- 유효성: 두 프로필 모두 H2 최종 판정(confirmed 또는 not confirmed), 10세션 2026-10-21..2026-11-03, 스냅샷 `holdout_5m_60d_20261105`.
- 결과는 아래 파일에 있고 이 PR부터 공개입니다(H-D7).
- main 기준 커밋: `<6.2에서 적은 짧은 해시>`

## 파일 13개

| 경로 | 넣은 방법 |
|---|---|
| `paper_live/out/replay_holdout/`, `paper_live/out_krx/replay_holdout/`의 `days.csv`, `summary.json`, `trades.jsonl`, `fills.jsonl` (8개) | 태그 클론에서 바이트 그대로. sha256이 판독 직후 기록한 해시와 같습니다 |
| `paper_live/out/verdict.json`, `paper_live/out_krx/verdict.json` | 같음. `frozen_file`에는 태그 클론의 절대 경로(소유자의 Windows 사용자 폴더 이름 포함)가 그대로 있습니다 |
| `paper_live/out/data/MANIFEST.json`, `paper_live/out_krx/data/MANIFEST.json` | `holdout_5m_60d_20261105` 행 하나씩만 더했습니다. 판독이 쓴 행과 같고, 행의 sha256이 스냅샷의 해시입니다. 스냅샷 `.csv.gz`는 넣지 않고 소유자가 비공개로 보관합니다(H-D6) |
| `paper_live/H2_READOUT_RECORD_2026-11-05.txt` | 짧은 기록(H-D11): 판정 줄 2개, yfinance 버전, 시작·끝 시각. 컴퓨터 이름 없음. 비공개 사본과 같은 바이트 |

## 소유자 PC에서 한 점검

- 태그 클론의 산출물 14개(스냅샷 포함)의 sha256 = 판독 직후 기록한 해시.
- `MANIFEST.json` 합치기 스크립트: dry run과 write 모두 `RESULT: OK`. 행 하나 추가 말고는 바뀐 줄이 없습니다.
- 짧은 기록 점검: `RESULT: OK`. 판정 줄이 `verdict.json`에서 `verdict.py`의 형식대로 다시 만든 줄과 같습니다.
- 새 main 클론: 복사한 10개의 sha256 = 기록한 해시, 스냅샷 `.csv.gz` 없음, `MANIFEST.json` 2개 `<OK 또는 MERGED>`.
- 커밋 1개, 파일 13개.

## 공개 기록

1. **H-D13 (guard 스위트).** 2026-11-04 판독 준비 문서를 쓰던 Claude 세션이 `tests/frozen_guard.py`의 검사 (b)를 직접 불렀습니다. 이 검사는 git으로 태그의 코드 사본 4개 `paper_live/out*/frozen_rule/{engine,config}.py`를 읽어 바이트를 비교합니다. 화면에는 통과 결과만 나왔습니다. 같은 세션의 그날 Linux 전체 실행도 guard 스위트로 같은 blob을 읽었습니다(`guard/test_b` PASS). 이 파일들은 코드 사본이고 홀드아웃 산출물이 아닙니다. 소유자 결정 H-D13: 공개 기록으로 남기고, Claude 세션의 guard 스위트 실행은 계속 허용합니다. 경위는 브랜치 `claude/h2-readout-prep-20261104`의 `docs/nautilus_bridge/H2_READOUT_PREP_2026-11-04.md` 머리말과 9.3에 있습니다.
2. **결과 일부를 이르게 전달함.** 이 커밋 전에 소유자가 base 프로필의 재생 출력(날짜 줄과 요약 JSON)을 Claude 채팅에 한 번 붙여 넣었습니다. H-D7은 main 커밋 전에는 Claude에게 유효성 항목만 보내기로 했습니다.
3. **판정 줄을 다시 만든 경위.** Windows PowerShell 5.1의 기록(transcript)에 Python 출력이 담기지 않았습니다. 그래서 짧은 기록 파일의 판정 줄 두 개는 화면에서 옮긴 것이 아니라 각 프로필의 `verdict.json`에서 `paper_live/verdict.py`의 출력 형식 그대로 다시 만든 것입니다. 커밋 전 점검에서 두 줄이 그렇게 다시 만든 줄과 같음을 확인했습니다.
4. **이 PR의 실행표를 쓰며 생긴 작업 규칙 이탈.** 2026-11-05 Claude 에이전트가 `origin/main`에서 `git grep`을 pathspec `paper_live/*.py`, `grokteam/*.py`로 돌렸습니다. 이 pathspec은 `paper_live/out*/`와 `grokteam/out/` 아래의 `.py` 파일도 덮습니다. `paper_live/out*`의 줄은 화면에 나오기 전에 걸러냈고, `grokteam/out/` 아래에서는 `frozen_book/`의 코드 사본 줄만 나왔으며 `book/`의 줄은 없었습니다. 검색 대상이 `.py` 파일뿐이라 홀드아웃 산출물 파일은 들어 있지 않았습니다.

## 병합

- main 세션(Claude)이 CI(Compliance document review) 통과 뒤 병합합니다("CI 통과 시 Claude 병합"). 소유자는 병합하지 않습니다.
- H-D5: 7A.5부터 Step 10 병합까지 main을 연구 브랜치 `claude/amazing-gauss-tdiguu`에 합치지 않습니다.
- 이 PR은 `paper_live/` 아래만 바꿉니다. 두 CI 워크플로의 sparse checkout이 `paper_live/`를 빼므로 이 파일들을 읽는 CI 단계는 없고, `Runtime packaging smoke`는 경로 필터 때문에 돌지 않습니다.
```

- 원하면 `## 결과` 절을 더해 짧은 기록 파일의 판정 줄 두 개를 붙여도 됩니다. PR을 여는 때는 push 뒤라 이미 공개 상태입니다.

## 17. Step 12. push (결과 공개)

push하면 결과가 공개됩니다. 15.3까지 모두 기대대로였는지 한 번 더 봅니다.

```powershell
Set-Location C:\Users\whydi\QUANTGEN-h2-main
git push -u origin owner/h2-readout-outputs-20261105
git rev-parse HEAD origin/owner/h2-readout-outputs-20261105
```

- 기대(push):
  - `remote: Create a pull request for 'owner/h2-readout-outputs-20261105' on GitHub by visiting:`
  - `remote:      https://github.com/xkg4real/quantgen/pull/new/owner/h2-readout-outputs-20261105`
  - ` * [new branch]      owner/h2-readout-outputs-20261105 -> owner/h2-readout-outputs-20261105`
  - `branch 'owner/h2-readout-outputs-20261105' set up to track 'origin/owner/h2-readout-outputs-20261105'.`(git 버전에 따라 문구가 조금 다름)
- 기대(마지막 명령): 같은 40자 해시 두 줄.
- 거부되면 멈춥니다. `--force`를 쓰지 않습니다.

## 18. Step 13. PR 열기

1. 브라우저에서 엽니다: `https://github.com/xkg4real/quantgen/compare/main...owner/h2-readout-outputs-20261105?expand=1`
2. base가 `main`, compare가 `owner/h2-readout-outputs-20261105`인지 봅니다.
3. 제목에 16.1, 본문에 16.2(두 곳을 채운 것)를 붙여 넣습니다.
4. "Create pull request"를 누릅니다(초안 PR이 아님).

- 기대:
  - PR 번호(`#<번호>`)가 생깁니다. "Files changed"가 13입니다.
  - 충돌 표시가 없습니다("Able to merge" 또는 충돌 없음 안내).
  - 검사는 `Compliance document review / Document and source consistency` 하나가 돕니다. `Runtime packaging smoke`는 돌지 않습니다. 경로 필터에 `paper_live/`가 없기 때문입니다(`.github/workflows/runtime-smoke.yml:6`). 정상입니다.
- **병합 버튼을 누르지 않습니다.** 병합은 main 세션이 합니다.

## 19. Step 14. main 세션에 알리기 (병합은 main 세션)

main 세션(main에 PR을 병합하는 Claude 세션)에 아래를 보냅니다. push 뒤이므로 결과가 들어가도 되지만, 필요하지 않습니다.

```
[⑧-1 H2 산출물 main PR] PR #<번호> https://github.com/xkg4real/quantgen/pull/<번호>
브랜치 owner/h2-readout-outputs-20261105, 커밋 <15.2의 짧은 해시>, main 기준 <6.2의 짧은 해시>
파일 13개: replay_holdout 8, verdict.json 2(바이트 그대로), MANIFEST.json 2(행 하나씩 추가), paper_live/H2_READOUT_RECORD_2026-11-05.txt
점검: 5절 14개 OK / 10.1·10.3 RESULT OK(MANIFEST: <equal/different>) / 11.2 RESULT OK / 12절 OK 10, ABSENT-OK 2, MANIFEST <OK/MERGED> / 15.3 커밋 1개, 파일 13개, csv.gz 없음
요청: CI(Compliance document review)가 통과하면 병합해 주세요("CI 통과 시 Claude 병합").
H-D5: 병합 뒤에도 Step 10 병합까지 main을 연구 브랜치 claude/amazing-gauss-tdiguu에 합치지 않습니다.
```

- main 세션이 할 일(이 표의 권고):
  - CI 통과를 확인하고 병합합니다. 충돌이나 CI 실패면 소유자에게 알리고 PR 내용은 바꾸지 않습니다.
  - 인계 원장에 ⑧-1을 기록합니다(`--done`) `[확인 필요 #11]`.

## 20. 병합 뒤

- 소유자:
  - 연구 브랜치 Claude 세션에 한 줄 남깁니다: "H2 산출물 PR #<번호>가 main에 병합됨. H-D5에 따라 Step 10 병합 전까지 main을 연구 브랜치에 합치지 않음."
  - 실행표 14절(H-D9)의 12-05 경고 알림을 아직 끄지 않았으면 끕니다. 메인 클론은 연구 브랜치에 있어 그 클론의 `verdict.json`은 계속 pending으로 보입니다(준비 6.6, UNVERIFIED).
  - 지우지 않는 것: 태그 클론 `C:\Users\whydi\QUANTGEN-studies`, 비공개 사본 `C:\Users\whydi\QUANTGEN-h2-private`. 스냅샷 원본과 그 사본이 H-D6의 비공개 보관입니다. 같은 태그 클론을 ⑧-3에 쓸지는 그때 정합니다(준비 6.8).
  - 지워도 되는 것: `C:\Users\whydi\QUANTGEN-h2-main`, `C:\Users\whydi\QUANTGEN-h2-tools` `[확인 필요 #10]`.
- 바뀌는 것:
  - `tests/frozen_guard.py`의 대기 목록에서 H2 두 줄이 빠집니다(`:55-63`). GROKTEAM look이 남아 있으므로 조항 (d)(고정 버전 검사)는 그대로 살아 있습니다(준비 1.4).
  - ⑧-4(분리 스펙 Phase 2)의 판독 선행 조건이 채워집니다. "archived evidence"를 무엇으로 볼지는 `[확인 필요 #7]`.

## 21. 하지 말 것

| # | 하지 말 것 | 근거 |
|---|---|---|
| 1 | 메인 클론 `C:\Users\whydi\OneDrive\Desktop\QUANTGEN`에서 복사, `checkout`, 커밋 | 연구 브랜치에 있음(실행표 0절). N3, N12 |
| 2 | 태그 클론에서 `git add`, 커밋, 파일 이동·수정·삭제 | 산출물 원본(N15) |
| 3 | `.csv.gz` 커밋 | H-D6 |
| 4 | 기록(transcript) 원본 `h2_readout_transcript_*.txt` 커밋 | H-D11, 준비 5.4 |
| 5 | `git add -A`, `git add .` | 경로를 하나씩 넣음(14절) |
| 6 | `MANIFEST.json` 손 편집, dry run을 보기 전에 `--write` | 2.2 |
| 7 | push 전에 결과 수치를 Claude 채팅에 붙여 넣기 | H-D7 |
| 8 | PR을 직접 병합 | main 세션 몫("CI 통과 시 Claude 병합") |
| 9 | Step 10 병합 전에 main을 연구 브랜치에 합치기 | H-D5 |
| 10 | `git push --force` | 3절 |
| 11 | 새 클론에서 `python -m paper_live.*` 실행 | main은 판독을 돌리지 않음(분리 스펙 3.1 3번) |

## 22. 체크리스트

- [ ] 4: 도구 폴더를 새로 만들었다. 해시 목록 `paths: 14`. `$py`가 3.13.x.
- [ ] 5: 태그 클론 HEAD `eacd57d…`, `git status`가 `paper_live/out*/` 아래뿐, 14개 `OK`, 비공개 기록 파일 `True`.
- [ ] 6: `C:\Users\whydi\QUANTGEN-h2-main`을 GitHub `main`에서 새로 복제했다. `main`, HEAD = `origin/main`, 깨끗함, `.git` 폴더, `* -text`, 태그 커밋이 조상. main 기준 커밋을 적었다. 신원이 `563db54`와 같다.
- [ ] 7: 브랜치 `owner/h2-readout-outputs-20261105`(GitHub에 없던 이름).
- [ ] 8: 스크립트 두 개의 해시 앞 16자리가 기대와 같다.
- [ ] 9: `copied 10`.
- [ ] 10: dry run `RESULT: OK`, 차이가 행 하나 추가뿐(42/36, 또는 44/38). `equal`/`different`를 적었다. `--write` `RESULT: OK`. `git diff --stat`에 지운 줄 없음.
- [ ] 11: 기록 파일 복사, 점검 `RESULT: OK`.
- [ ] 12: `OK` 10, `ABSENT-OK` 2, MANIFEST 2줄이 10.1과 맞음.
- [ ] 13, 14: 정확히 13개 경로, 모두 스테이징.
- [ ] 15: 커밋 1개, 13개 파일, `.csv.gz` 없음, 트리 깨끗함.
- [ ] 17: push, 두 해시 같음.
- [ ] 18: PR을 열었다(13개 파일, 충돌 없음). 병합하지 않았다.
- [ ] 19: main 세션에 알렸다.
- [ ] 20: 병합 뒤 연구 브랜치 세션에 알렸다. 12-05 알림을 껐다. 태그 클론과 비공개 사본을 지우지 않았다.

## 확인 필요

이 표가 스스로 정하지 않은 것입니다. 명령과 문안은 아래 권고대로 적었습니다.

1. **짧은 기록 파일의 저장소 경로**(H-D11, 실행표 확인 필요 #4). 권고: `paper_live/H2_READOUT_RECORD_2026-11-05.txt`. 이유는 2.1. 다른 안은 `docs/nautilus_bridge/H2_READOUT_RECORD_2026-11-05.txt`이고, 그때는 11.1, 11.2, 13, 14절의 경로와 커밋 메시지, PR 본문의 경로를 바꿉니다.
2. **브랜치 이름** `owner/h2-readout-outputs-20261105`. 저장소의 브랜치는 `claude/…`, `gpt/…`뿐이고 소유자 브랜치 관례가 없습니다. 권고: 이 이름. 에이전트 브랜치(`claude/`, `gpt/`)와 한눈에 구별됩니다.
3. **Claude 작성 표시.** 커밋 메시지와 PR 본문의 초안은 Claude가 썼지만 커밋과 PR은 소유자의 것입니다. 권고: 7A.3 소유자 커밋(`fe37e82`, `563db54`, 문안은 RUNBOOK 7A.3)처럼 `Co-Authored-By` 줄과 PR 꼬리말을 넣지 않습니다. 넣기로 하면 커밋 메시지 끝에 빈 줄 하나와 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`, `Claude-Session: https://claude.ai/code/session_016uB1jgeiPdP8gPkAez3Wrx` 두 줄을 더합니다.
4. **공개 기록 4번**(이 표를 쓰며 생긴 작업 규칙 이탈). 권고: H-D13 선례대로 커밋 메시지와 PR 본문에 넣습니다. 빼기로 하면 두 문안에서 4번 단락을 지웁니다.
5. **공개 기록 2번의 채팅.** 문안은 "a Claude chat"(Claude 채팅)이라고만 적습니다. 권고: 소유자가 어느 세션인지 알면 그 세션 링크를 덧붙입니다. 모르면 지금 문구로 둡니다.
6. **`verdict.json`의 `frozen_file`**(2.3). 권고: 바이트 그대로 커밋합니다. 사용자 폴더 이름은 이미 공개돼 있고, 고치면 11.1 대조가 깨집니다.
7. **Phase 2의 "archived evidence"**(준비 D-6의 남은 부분, 실행표 확인 필요 #3). 권고: 이 커밋(산출물과 `MANIFEST.json` 행의 sha256)과 비공개 보관(태그 클론의 스냅샷 원본, `C:\Users\whydi\QUANTGEN-h2-private`)을 합쳐 채운다고 보고, ⑧-4 스펙을 시작할 때 소유자 판정으로 `OWNER_RULINGS_LOG.md`에 남깁니다.
8. **병합 뒤 Claude 세션이 커밋된 H2 산출물을 읽어도 되는지.** H-D7은 결과를 main 커밋 때 공개한다고 적지만, Claude 세션들은 `paper_live/out*/`를 읽지 않는 규칙으로 일해 왔습니다. 권고: 병합 뒤 ⑧-4 작업에 한해 허용한다고 소유자가 한 줄로 정합니다. 그 전까지 세션들은 지금 규칙을 지킵니다.
9. **준비 문서가 main에 없음.** H-D13 사고의 경위(준비 머리말과 9.3)는 브랜치 `claude/h2-readout-prep-20261104`에만 있습니다. 권고: 공개 기록 1번이 요지를 main 기록에 남기므로 이 PR은 그대로 두고, main 세션이 준비 문서를 별도 문서 PR로 넣을지 따로 정합니다.
10. **정리 시점.** 권고: `C:\Users\whydi\QUANTGEN-h2-main`과 `C:\Users\whydi\QUANTGEN-h2-tools`는 병합 뒤 지워도 됩니다. 판독 venv `C:\Users\whydi\QUANTGEN-h2venv`도 병합 뒤 지워도 됩니다(실행표 15절 3번은 main 커밋까지 두자고 했습니다). 태그 클론과 비공개 사본은 지우지 않습니다.
11. **⑧-1의 원장 기록.** 권고: main 세션이 병합 뒤 `--done "⑧-1 | H2 holdout readout, outputs on main | <13 paths> | <병합 커밋> | <CI와 이 표의 점검 결과>"`로 기록합니다. 판독(11-05)만으로 기록할지, main 병합까지 기다릴지는 main 세션이 정합니다.
12. **소유자 PC에서 확인되지 않은 것.** GitHub 로그인 필요 여부와 복제 시간, git 버전(`git switch`), 6.3의 전역 git 신원, 실행표 11.1 해시의 보관 형식(4.2가 두 형식을 받음), 저장소 공개 여부(준비 5.4와 D-6이 "공개 저장소"라고 적음). 다르게 나오면 그 단계에서 멈춥니다.
