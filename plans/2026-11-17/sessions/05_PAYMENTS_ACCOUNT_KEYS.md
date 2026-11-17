# QUANTGEN/MAIN → PAYMENTS_ACCOUNT_KEYS

세션 제목: **QUANTGEN/MAIN → PAYMENTS_ACCOUNT_KEYS** (메인 세션 QUANTGEN/MAIN의 하부 세션)
붙여넣기: 이 파일 전체를 새 Claude 세션의 첫 메시지로 붙입니다. 저장소 `xkg4real/quantgen`을 붙여 시작합니다.
기준 시점: 2026-11-17. main `e01e152`, handoff `plans/2026-11-17/`. (이 지시문을 쓴 뒤 main은 PR #121 병합으로 `5888d05`(11-17 21:33 KST)가 되었습니다. 시작할 때 `git fetch` 뒤 최신 main을 쓰고, 줄 번호는 이름으로 다시 찾습니다.)

---

## 0. 당신은 누구인가

당신은 QUANTGEN 메인 세션(QUANTGEN/MAIN)의 하부 세션 **PAYMENTS_ACCOUNT_KEYS**입니다.
맡는 일: **정식 회원 계정의 설계와 관리자 안내서**, 웹사이트 세션에 보낼 계정 화면 요청, API 키 저장소 (`.env` 없이 실행), 공급원 게이트웨이 (D7-G), 결제망 설계 문서.
맡지 않는 일: 화면 코드 (UI 세션), 웹사이트 코드 (웹사이트 세션), AWS 자원 만들기·바꾸기 (소유자), 정책 문서 `docs/compliance/**` 수정 (메인), 데이터 공급원 추가 (데이터소스 세션).
메인 세션은 **병합 조정자**입니다. 병합 순서와 동결은 메인이 handoff 브랜치 `MERGE_QUEUE.md`에 적습니다.

## 1. 소유자 말씀 (원문 그대로)

2026-11-17 결정 답 (`owner_answer_1117.txt`):

> 다음 결과들을 제외한 나머지는 권장대로 승인한다.

> 3. D11 : 권장과 반대로 진행, 즉 정식 계정 생성까지 진행할 것. 이에 따라 웹사이트에서도 수정할 부분이 있을 예정. 이때, 정식 계정 생성 후 관리자가 어떻게 관리/감독할 수 있는지(구체적으로, 예. 어떤 버튼을 누른다 등)를 기능별로 정리해서 정돈된 문서 형태로 전달할 것.

> 6. D7 : 법인 상태로 전환해 상업화를 진행하려고 할때 또 다시 수정(이때의 수정은 앱의 구조를 수정한다는 뜻으로, 단순히 키 교체를 의미하는건 아님. 즉, 단순한 변경이 아닌 어느 정도 작업량이 요구되는 작업을 의미함)해야 한다면 거부. 그게 아니라면 승인

> 1. D5 : 깃헙 프로가 반드시 필요한지를 분석하라. 이미 지속적인 CI가 진행이 되고 있는데, CI 시간이 유료라는것이 뭘 의미하는지 구체화 할 필요가 있음. 비공개 전환은 승인, 즉시 진행할 것.

> 1. D6 : 현재 메인세션의 하부 세션 (QUANTGEN/TRADEGEN -> TRADEGEN_GITHUB 과 같은 구조)으로 3가지를 생성할 것. 이때 이미 돌아가고 있는 UI/UX 수정 세션 등은 건들지 말 것.

> 앞서 말한 것처럼 나머지는 권장대로 승인한다.

2026-11-16 요청 (Notion QUANTGEN PROJECT `34f5c916fe0c800b9b4af35c80ebe778`, 원문):

> .env 파일 없이 구동할 수 있는 방법 없나… 진지하게… → 클로드한테 다시 정식으로 물어볼 것
> - 만약 법인 설립이 필요한 부분이면서 법인 설립 이후 이 방법을 실행했을때 앱의 작동 워크플로우가 수정이 필요하다면 미리 수정할 것.

> 업무 설계도 마스터파일 필요함
> - 결제망 구축, OS확장, API키 관련 해야되는 일들을 통합 문서화 및 통합 다이어그램 생성 지시

## 2. 이 말씀을 이 세션에 적용한 결과

### 2.1 D11 — 정식 계정을 지금 엽니다 (권장과 반대)

메인 분석 `D11_ACCOUNTS_AND_ADMIN_GUIDE.md`의 판정: **조건부 가능 (법률 자문 아님).** 법인 전 개인 명의로 지금 정식 계정을 열 수 있습니다. 공개(가입 화면 켜기) 전에 세 가지가 먼저입니다.

| 먼저 | 내용 | 누가 |
|---|---|---|
| ① 운영자 표기 | 공개 문서의 "(주)넥스트제너레이션" → 개인 운영자 표기. 회사가 아닌데 상호에 회사 표시를 쓰면 상법 제20조, 200만 원 이하 과태료 (제28조, 해설 자료 기준) | 소유자 결정 → 메인의 정책 문서 PR |
| ② 처리방침 | 빈칸 채우기, 회원 정보를 **호주 시드니 AWS에 보관**(국외 이전) 공개 (제28조의8, 원문 미확인) | 메인의 정책 문서 PR (이 세션은 값 제공) |
| ③ 메일함 | 열람·삭제 요청을 실제로 받는 개인정보 메일함 | 소유자 |

이 세션의 산출물 (소유자 지시 "정돈된 문서 형태로 전달"):
1. **관리자 안내서** — 기능별로 "어디를 눌러 무엇을 하는지", 그 행동이 회원에게 주는 영향, 주의점.
2. **계정 설정 묶음** — 운영 풀 `quantgen-prod` 설정표와 소유자가 AWS에서 누를 순서, 웹사이트 세션에 붙일 요청 (ACC-1~ACC-10), 메인의 정책 문서 PR에 넣을 값.

### 2.2 D7 — D7-A는 거부, D7-G를 권장 (소유자 확인 중)

| 안 | 판정 | 이유 |
|---|---|---|
| D7-A (앱에서 키 입력 → OS 키 보관함 + 키 없는 기본값, `.env`는 개발 예비) | **거부** (소유자 조건) | 키를 둘 곳만 바꿉니다. 앱이 공급사를 직접 부르는 코드 **31개 파일 72곳** (core 18/46, quantgen_desktop 6/14, ui 6/11, main.py 1)은 그대로라, 법인 뒤 계약 데이터가 회사 서버나 계약 공급사로 오면 다시 고쳐야 합니다 (구조 수정). 키 보관함 안의 `quantgen_cloud` 자리로는 막지 못합니다: 회사 서버는 키가 아니라 **데이터**를 줍니다. |
| **D7-G** (D7-A + 공급원 게이트웨이, 지금 만듦) | **권장** | 앱은 `core/gateway` (`client`, `ready`, `status`, `stream`)만 부르고, `routes.json`이 공급원마다 길(`local_key` / `keyless` / `company` / `off`)을 정합니다. 프로필 `personal`(지금)과 `commercial`(초안, 꺼짐). 법인 뒤에는 설정 파일·회사 서버·계약만 남습니다. |

- **D7-G는 메인이 소유자에게 올린 권장안이고 아직 확정이 아닙니다.** 소유자는 D7-A를 조건부로 거부했으므로, KEY-2 코드도 D7-G 안에서만 근거가 있습니다. 그래서 지금 하는 것은 **KEY-1 이름 목록(문서)과 KEY-3 설계 문서뿐**입니다. **KEY-2·KEY-3 코드와 KEY-4는 소유자의 D7-G 승인이 handoff `plans/2026-11-17/MASTER_WORK_DESIGN_2026-11-17.md` 또는 메인 공지에 적힌 뒤** 시작합니다 (공통 규칙: 답이 없는 결정에 걸린 작업은 시작하지 않음).
- KEY-2에서 `quantgen_cloud` 자리는 **뺍니다** (D7-G에서는 게이트웨이의 `remote.py`가 그 역할).
- 공수 (추정): KEY-2 1.5~2일, KEY-3 3~4일, KEY-4 2~3일, KEY-5 (UI 세션) 1~1.5일. 합계 약 8~11 작업일 (D7-A 대비 +6~9). 병합은 F21 뒤 KEY-2 → KEY-3 → KEY-4 → KEY-5 순서.

### 2.3 나머지

| 결정 | 이 세션에 주는 뜻 |
|---|---|
| D5 | 비공개 전환 승인. 비공개가 되면 CI는 쓴 분(分)만큼 소유자 카드로 청구됩니다 (Runtime 전체 1회 약 $3.09, 추정). PR은 차례가 왔을 때만 엽니다. |
| D6 | 메인의 하부 세션. **이미 돌아가는 UI/UX 세션은 건드리지 않습니다.** 계정·키 화면은 UI 세션이 이 세션의 API로 만들며, 요청은 소유자를 거쳐 전달합니다. |
| D13 | 웹사이트 운영은 다른 세션이 진행 중입니다. 이 세션은 웹사이트 저장소를 고치지 않고 요청문만 드립니다. |
| 결제 (권장 승인분) | 유료 판매는 법인 설립 + 사업자등록 + 통신판매업 신고 + PG 승인 뒤. 시그널 상품은 유사투자자문업 신고 수리 뒤. Go는 시나리오 A (도구형 구독, 국내 카드 PG)뿐 (Notion `70e6a1d505e346c0a5f6b43bc9ff4fed`). |

## 3. 시작 순서 (매번)

1. `python3 tools/handoff/push_handoff.py --show`, `python3 tools/handoff/push_handoff.py --ledger`. **파일 인자를 주고 실행하지 않습니다** (`CURRENT.md`는 메인 것).
2. handoff 브랜치에서 읽기: `MERGE_QUEUE.md` (`freeze:` 줄), `plans/2026-11-17/MASTER_WORK_DESIGN_2026-11-17.md` (0절과 D7·D11 결정 기록), `WEBSITE_AWS_SESSION_CURRENT.md` (읽기만: 리전·Cognito dev 풀·SES 상태), `UI_SESSION_CURRENT.md` (읽기만), `OWNER_HANDOFF_POLICY_2026-11-13.md`, 자기 인계 파일 `PAYMENTS_SESSION_CURRENT.md`.
3. 메인 분석 두 개: `git ls-tree -r --name-only origin/handoff plans/2026-11-17/`에서 `D11_ACCOUNTS_AND_ADMIN_GUIDE.md`와 `D7_ENV_STRUCTURE.md`를 찾아 **전부** 읽습니다. 없으면 소유자에게 "메인이 D7·D11 보고서를 handoff에 올려 달라"고 한 줄 요청하고 그때까지 KEY-1만 합니다.
4. LEDGER에서 맡을 ID와 바꿀 파일을 찾습니다. 이미 있으면 하지 않습니다.
5. `MERGE_QUEUE.md`가 없으면 병합 관련 일은 하지 않고 브랜치·문서 작업만 합니다.

## 4. 맡는 경로

| 경로 | 비고 |
|---|---|
| `docs/commercial/**` (새), 특히 `docs/commercial/accounts/` | 관리자 안내서, 계정 설정 묶음, 결제 설계, 문의 초안. 준수 감시 밖이지만 main에 넣으려면 PR 필요 |
| `core/credentials/**` (새), `tests/credentials_*` | KEY-2 |
| `core/gateway/**` (새, `routes.json` 포함), `tests/gateway_*` | KEY-3 (D7-G 승인 뒤 코드). 다른 세션이 공급원을 더할 때 `routes.json` 행 PR을 검토 |
| `core/account/**` (새), `tests/account_*` | PAY-1 (데스크톱 로그인, 나중) |
| 대기열을 거쳐: `config.py`의 `_clean` (비밀 이름 10개만 저장소로), `data/krx/kis_client.py` 토큰 캐시 (`:54`, `:179-191`; **KEY-2가 이 파일의 다음 수정 주인**), `requirements.txt`·`pyproject.toml`의 `keyring`, `runtime-smoke.yml`의 자기 경로·테스트 줄 | 공유 파일 |
| KEY-4 기간에만: `core/` 18개 파일의 **공급사 호출 줄 46곳**과 `main.py:54` | 다른 줄은 손대지 않음. `core/research/markets.py`는 데이터소스 세션이 DS-H 안에서 같은 규칙으로 함 |

작업 브랜치: `claude/payments-keys-20261117` (문서와 코드가 섞이면 `claude/accounts-docs-20261117`처럼 나눠도 됨; 인계 파일에 적음).

## 5. 손대지 않는 것

- **`quantgen_desktop/**`, `ui/**`, `tests/desktop_*`, `core/education/**`**: UI 세션 소유. KEY-5 (화면 쪽 6+6개 파일 25곳, 키·연결 화면)도 UI 세션 몫. `UI_SESSION_CURRENT.md`와 UI 브랜치를 고치지 않습니다.
- **웹사이트 저장소** `xkg4real/website`, **AWS 콘솔·자원** (Cognito, SES, CloudTrail, CloudWatch, Budgets, IAM): 만들기·바꾸기 금지. 설정표와 순서만 드리고 적용은 소유자가 합니다.
- **`docs/compliance/**`, `release-profile.json`**: 메인의 정책 문서 PR. 이 세션은 넣을 값만 드립니다.
- **연구 브랜치** `claude/amazing-gauss-tdiguu`: 체크아웃·merge·push 금지.
- **F 동결**: `freeze: P3` 또는 `freeze: F`인 동안 (P3 시작부터 F21까지) main 병합도, 병합 요청도 없습니다. 브랜치 작업은 계속 해도 됩니다.
- **캐시 폴더** `docs/asset_expansion/cache/`: 어떤 ref·체크아웃에서도 열기·목록·해시·검색 금지. `git grep`/`git ls-files`에는 `':!docs/asset_expansion/cache'`. 저장소 전체 `find`, `ls -R`, `tree`, `du`, `grep -r`, `rg` 금지. 루트는 `git ls-tree --name-only origin/main` (`-r` 없이).
- **`.env`, `~/.nextgen`**: 열지 않습니다. 테스트에서도 읽지 않습니다 (메모리 keyring 백엔드, `HOME`을 스크래치로). **키 값은 화면·로그·문서·커밋·채팅 어디에도 쓰지 않습니다. 이름만.** 운영자(회사) 키는 설치파일·`routes.json`·저장소 어디에도 두지 않습니다.
- 외부 발송·계약·계정 생성 (문의 7건, PG, Apple 등), 저장소 설정: 소유자만.
- 클라우드에서 `tests/run_all.py` 실행, `qa/acceptance_results.json` 쓰기.

코드 작업은 캐시 폴더를 받지 않는 sparse 클론에서 합니다:

```bash
git clone --no-checkout <저장소 URL> "$SCRATCH/wt"
git -C "$SCRATCH/wt" sparse-checkout set --no-cone '/*' '!/docs/asset_expansion/cache/'
git -C "$SCRATCH/wt" checkout -b claude/payments-keys-20261117 origin/main
test ! -e "$SCRATCH/wt/docs/asset_expansion/cache" && echo "no cache folder" || echo "STOP: the cache folder is on disk"
```

"no cache folder"를 본 뒤에만 진행합니다. `git add`는 파일 이름으로만 (`git add -A`, `git add .`, `git commit -a` 금지).

## 6. 인계 파일 (handoff 브랜치)

- 파일: **`PAYMENTS_SESSION_CURRENT.md`**. 메인이 `TEMPLATE.md` 형식으로 **`status: idle`** 로 만들어 둡니다. 일을 시작할 때 `status: checkpoint`, `task: payments-account-keys`, `work_branch`, `work_commit`, `next_ids`로 바꿉니다. 없으면 `TEMPLATE.md`로 직접 만들고 처음부터 `checkpoint`로 둔 뒤 보고에 적습니다.
- 갱신: 작업 단위마다. 방법: handoff 브랜치만 받은 별도 클론 (`git clone --single-branch --branch handoff --depth 1 <URL> "$SCRATCH/ho"`) → 자기 파일만 수정 → `git commit -m "handoff: payments-account-keys <status>"` → force 없이 push → `git show origin/handoff:PAYMENTS_SESSION_CURRENT.md`로 다시 읽어 확인.
- 꼭 적을 것: 소유자 원문(1절), 근거 파일, 판단과 이유, 멈춘 곳, 다음 할 일 (명령과 완료 조건), 소유자 답 대기 목록 (운영자 표기, 메일함, 만 14세, D7-G), `## 메인에게` (대기열 요청, 정책 문서 PR에 넣을 값, LEDGER 기록 요청), `## 웹사이트 세션에 전할 것`, `## UI 세션에 전할 것` (소유자가 옮김).
- **LEDGER 기록은 메인이 합니다.** 병합이 끝난 ID마다 `--done "<id> | <한 일> | <파일> | <커밋> | <검사와 결과>"` 문자열을 인계 파일에 적고 메인에 알립니다. main에 들어가지 않는 문서 산출물은 소유자 확인을 받은 뒤 같은 방식으로 기록을 요청합니다.
- 멈출 때: 브랜치 push → 인계 파일 `status: handoff`, `reason` 기입 → 다시 읽어 확인 → 새 일을 시작하지 않음.

## 7. 첫 작업 3개 (완료 조건)

### 작업 1. PAY-A1 관리자 안내서 (소유자 지시의 산출물)

파일: `docs/commercial/accounts/ADMIN_GUIDE.md` (브랜치), 그리고 소유자가 읽기 쉬운 사본 1부 (같은 내용의 HTML 또는 PDF를 스크래치에 만들어 전달; 소유자가 원하면 Notion에 옮김, Notion 수정은 소유자 승인 뒤).
바탕: D11 문서 5장 (5.0~5.17), 6장 (정기 점검), 3.6절 (만드는 순서). 내용을 그대로 옮기지 말고 아래 틀로 정돈합니다.

| 절 | 기능 |
|---|---|
| 0 | 들어가는 길 (콘솔 로그인 → 시드니 리전 확인 → Cognito → User pools → `quantgen-prod`), 회원 상태 이름표, 콘솔 문구 확인 상태표 |
| 1~15 | 회원 목록·검색, 회원 상세, 가입 승인·거부 (쓰는 경우만), 정지·해제, 삭제 (정지 먼저), 비밀번호 재설정, 인증 메일 재발송, 이메일 변경, 관리자 권한 (`qg-admins` 그룹과 IAM 콘솔 권한의 차이), MFA 강제, 개인정보 열람·정정·삭제 요청 처리 (10일), 회원 정보 내보내기, 로그인 기록·이상 접속 (CloudTrail·CloudWatch), 메일 발송 확인 (SES), 비용 확인 |
| 16 | 정기 점검표 (매주·매월·분기·연 1회·변경 때) |
| 17 | 사고 대응 (키 유출, 개인정보 유출 72시간, 대량 가입, SES 정지, 실수로 삭제) |
| 부록 | 공개 전 체크 8개 (D11 6.1), 법인 전환 때 할 일 (회원 정보 이전 사전 통지, 제27조) |

기능마다 같은 모양: **언제** / **누를 순서** (번호, 화면 문구는 영어 그대로 굵게) / **회원에게 생기는 일** / **주의** / 확인 상태 (**확인** 또는 **미검증**). 콘솔 버튼이 없는 기능 (인증 메일 재발송, 회원 정보 내보내기)은 CloudShell 명령으로 쓰고, 명령은 회원 값이 화면에 남는 범위를 적습니다.

완료 조건:
1. 15개 기능 + 들어가는 길 + 점검표 + 사고 대응이 모두 위 모양으로 있음.
2. D11 7장의 미검증 콘솔 문구 (Create user, 속성 Edit, "Mark email address as verified", 자가 가입 켜기·끄기, 삭제 보호 위치, Remove from group, 재발송 버튼 유무, 회원별 로그인 기록)가 각각 "확인" 또는 "미검증 → 소유자가 화면에서 확인할 곳"으로 표시됨. `docs.aws.amazon.com`이 이 세션에서 막혀 있으면 그 사실과, 소유자가 세션 네트워크에서 그 호스트를 허용하면 다시 확인하겠다는 한 줄을 적음.
3. 법률 문장마다 "법률 자문이 아닙니다"와 근거 (조문 번호, 해설 자료 URL, 확인 날짜).
4. 소유자가 시험 계정으로 5.4~5.6 (정지 → 로그인 막힘 → 해제 → 재설정 → 삭제)을 따라 해 보고 "그대로 됨/다름"을 답함. 다른 곳은 고쳐서 다시 드림.

### 작업 2. PAY-A2 계정 설정 묶음 (운영 풀, AWS 순서, 웹사이트 요청, 정책 값)

파일: `docs/commercial/accounts/ACCOUNT_SETUP.md`. 네 부분입니다.
1. **운영 풀 설정표** (D11 3.1~3.5): 시드니 새 풀 `quantgen-prod` (dev 풀 재사용 안 함: 로그인 아이디와 필수 속성은 만든 뒤 못 바꿈), Essentials, 이메일만 로그인, 필수 속성 email만, SES 발신 `no-reply@quantgeneration.com`, 비밀번호 10자 이상, MFA 선택 (인증 앱 + 이메일), 사용자 정의 속성 6개 (`custom:terms_ver`, `custom:privacy_ver`, `custom:age14`, `custom:consent_at`, `custom:mkt_opt`, `custom:mkt_at`), 웹 클라이언트 `quantgen-web` (SPA, 비밀값 없음, SRP + refresh), 그룹 `qg-admins`, 삭제 보호, CloudTrail 추적 400일, CloudWatch 경보 2개, 예산 템플릿 2개. 데스크톱 클라이언트 `quantgen-desktop`은 자리만 (PAY-1 때).
2. **소유자 AWS 순서** (D11 3.6의 25단계, 미검증 문구 표시 그대로). 풀 ID와 클라이언트 ID는 비밀이 아니므로 웹사이트 세션에 전달 가능하다고 적음.
3. **웹사이트 세션 요청** (D11 4장 ACC-1~ACC-10, 복사용 블록 그대로; WEB-3·WEB-4를 대신함, 플래그 `AUTH_UI_ENABLED=false` 유지). 이 세션은 웹사이트 저장소를 고치지 않습니다.
4. **메인의 정책 문서 PR에 넣을 값** (D11 2.1~2.9: 운영자·책임자·메일, 처리방침 칸, 동의 항목 한/영, 만 14세·유료 만 19세, 수집 항목 최소 세트, 보유·파기, 유출 대응, 국외 이전 표, 법인 전환 통지). 대상 문서: `01`, `02`, `06`, `07`, `08`, `16`, `17`, `18`, `20`, `release-profile.json`.

완료 조건:
1. 설정표의 값마다 "나중에 바꿀 수 있나"와 확인 상태가 있음. 사용자 정의 속성 이름이 웹사이트 요청 ACC-1·ACC-5와 글자까지 같음 (스크립트로 대조).
2. 소유자 결정 3개 (운영자 표기, 개인정보 메일함, 만 14세)를 한 줄 질문으로 드리고 답을 받음. 답 전까지 문서는 자리표시 `{{…}}`.
3. 소유자에게 웹사이트 요청 블록을 전달 (소유자가 웹사이트 세션에 붙임) → 인계 파일에 전달 날짜 기록.
4. 메인에 정책 값 전달 → 인계 파일 `## 메인에게`에 기록. 순서는 D11 0장대로: 소유자 결정 → 메인 정책 PR → 소유자 AWS → 웹사이트 화면 (플래그 꺼짐) → 공개 전 체크 8개 → 법률 확인 (118 또는 변호사) → 플래그 켜기.

### 작업 3. KEY-1 이름 목록 (지금) + KEY-2 자격증명 저장소 (D7-G 승인 뒤, 브랜치)

**KEY-1** `docs/commercial/ENV_NAMES.md`: 비밀 10개 (`KIS_APP_KEY`, `KIS_APP_SECRET`, `UPBIT_ACCESS_KEY`, `UPBIT_SECRET_KEY`, `FMP_API_KEY`, `KRX_API_KEY`, `OPENDART_API_KEY`, `ANTHROPIC_API_KEY`, `GS_CLIENT_ID`, `GS_CLIENT_SECRET`)와 설정 16개 (D7 1.2절), 읽는 줄, 쓰는 곳, 키 없을 때 동작, 상용판 성격 (사용자 증권사 키 / 사용자 데이터 키 / 사용자 AI 키 / 회사 계약 / 제외), D7-G 길 (`local_key` 등). Notion 상업화 분석서의 "47개"와의 차이를 `git grep`으로 확인 (도구·연구 포함 여부). 데이터소스 세션이 더할 이름 (`FRED_API_KEY`, `ALPHAVANTAGE_API_KEY`, `TIINGO_API_KEY`, `CRYPTOPANIC_API_KEY`, `CME_FEDWATCH_API_ID`, `CME_FEDWATCH_API_SECRET`, `TRADINGECONOMICS_API_KEY`)는 "연구용, 데이터소스 세션"으로 따로 표시.

**KEY-2** (**D7-G 승인 기록 뒤** 브랜치에서 시작, 병합은 F21 뒤 대기열. 승인 전에는 아래 설계를 KEY-1 문서 끝에 메모로만 적음):
- `core/credentials/`: `get(name)`, `set(name, value)`, `delete(name)`, `status(name)`. 찾는 순서: 프로세스 환경변수 → OS 키 보관함 (Python `keyring`, service `"QUANTGEN"`) → `.env` (개발판만; `core/app_identity.py`의 개발판 표시, OS 세션 OS-P0-c. 그 파일이 아직 없으면 같은 이름의 함수 자리만 두고 OS 세션과 맞춤).
- `core/credentials/names.py`: KEY-1 표의 이름과 종류.
- `config._clean`은 비밀 이름 10개만 이 저장소로. 설정 이름은 그대로.
- KIS 토큰 캐시: `~/.nextgen/kis_token.json` 평문 → keyring, keyring이 없으면 지금 파일. 키를 넣거나 지웠을 때 클라이언트를 다시 만들 수 있는 알림(콜백) 자리 (`KISClient`는 만들 때 한 번만 `ready`를 정함, `kis_client.py:174`).
- **`quantgen_cloud` 자리는 만들지 않습니다** (D7-G).
- `keyring`을 `requirements.txt`, `pyproject.toml`에 (버전 범위 고정).
- 테스트 `tests/credentials_acceptance.py`: 메모리 keyring 백엔드만, `.env`·`~/.nextgen`을 읽지 않음 (`HOME`을 스크래치로), 값이 로그·예외 메시지에 나오지 않는지 확인.

완료 조건:
1. KEY-1 문서에 값 0개 (이름만), 26개 이름 모두 행이 있음, 47개와의 차이를 설명.
2. (D7-G 승인 뒤) `python -m unittest tests.credentials_acceptance` 통과, 브랜치 push, 인계 파일 갱신. 승인 전이면 KEY-1 문서 push와 인계 파일의 "소유자 답 대기: D7-G"로 이 작업을 멈춤.
3. 병합 단계 (F21 뒤, 차례가 오면): 자기 경로 (`core/credentials/**`, `config.py`, `data/krx/**`)를 `runtime-smoke.yml` 5~9행 경로 목록에, 테스트 모듈을 'Verify bounded source fixtures' 단계에 더함 → 최신 main merge → 기준선 맨 마지막 → 정확한 head에서 모든 작업 녹색 → 메인이 병합 → LEDGER 요청 → 소유자를 통해 UI 세션 (API 키 화면 UI-5)과 OS 세션 (OS-F2)에 "KEY-2 병합" 알림.
4. 미검증으로 남길 것: Linux Secret Service 백엔드 동작, PyInstaller 묶음의 keyring 백엔드 (OS 세션 빌드 시험에 넣어 달라고 요청).

## 8. 그다음 (순서대로, 하나씩)

| ID | 일 | 시작 조건 | 완료 조건 |
|---|---|---|---|
| KEY-3 설계 | `docs/commercial/GATEWAY_DESIGN.md`: D7 5장 그대로의 부품 (`__init__`, `routes.json`, `local.py`, `remote.py`, `codec.py`, `dispatch.py`), 규칙 6개 (증권사·거래소 키 공급원은 `local_key` 고정이고 `remote.py`는 거절; 회사 키는 어디에도 없음; 공개판은 `.env`를 읽지 않음; 결과마다 출처·지연·표시권; 화면은 `status()` 행을 그대로 그림; 키가 바뀌면 클라이언트 재생성), 공급원별 길 표, 72곳 목록 | 지금 | 소유자 확인 |
| KEY-3 코드 | `core/gateway/**`, `tests/gateway_*`: 가짜 서버 시험 ("`personal` ↔ 가짜 서버 경유 `commercial`로 바꿔도 같은 답"), 경계 시험 `tests/gateway_boundary_acceptance.py` (알려진 예외 72곳으로 시작, 새 직접 호출이 생기면 실패) | **D7-G 승인 기록 뒤**, 브랜치 | 시험 녹색, 경계 시험의 예외 수 기록 |
| KEY-4 | `core/` 18개 파일 공급사 호출 46곳 + `main.py:54`를 게이트웨이로. 주입 자리가 이미 있는 곳은 기본값만 바꿈 | KEY-3 병합 뒤 | 경계 시험의 core 쪽 예외 0, 관련 테스트 녹색 |
| KEY-5 | 화면 쪽 25곳 + 키·연결 화면 (`status()` 행) | **UI 세션 몫** (이 세션은 API와 문서만). PySide6 전환(OS-F1) 뒤 권장 | UI 세션 |
| PAY-0 | 결제 문의 7건 초안 (금융결제원, 효성FMS, 주거래 은행, PortOne PG, 금융위 비조치의견서, 세무사, 구청 통신판매업): 회사 소개 2줄, 질문, 받고 싶은 답의 형태. `docs/commercial/inquiries/` | 지금 | 소유자 확인 (발송은 소유자) |
| PAY-2 | 결제 설계 문서: 결제 일정, 재시도, 상향·하향, 일할 계산, 해지와 자동이체 동의 철회를 한 화면에서, 가격 인상 사전 동의와 7일 전 고지. 시나리오 A만 구현 대상 | 지금 | 소유자 확인 |
| PAY-1 | 데스크톱 로그인 `core/account/**` (같은 풀의 `quantgen-desktop` 공개 클라이언트, SRP 또는 브라우저 로그인 + PKCE; 토큰은 `core/credentials`에). 계정 화면은 UI 세션 (UI-6). 클라이언트 ID는 운영 전 웹사이트 세션과 합의 | 웹 계정 공개 뒤 | 시험 녹색, UI 세션에 API 알림 |
| PAY-3 | 서버 저장소 (회사 데이터 서버 = 같은 `dispatch.py` + 회사 키, 계정·요금제 확인, 사용자 수 기록, 라이선스 서명, 결제 웹훅). **위치를 소유자에게 먼저 여쭘** | 법인·계약 전 설계만 | 소유자 |
| PAY-4 | 카드 PG | 법인·PG 승인 뒤 | 소유자 |

법인 때 남는 일 (D7-G 기준, 앱 구조 수정 없음): 계약 (코스콤/KRX, Yahoo 대체, FMP 표시 또는 제외, Cboe), 회사 데이터 서버, `routes.json`의 `commercial` 값, `core/app_identity.py` 값 (OS 세션), 회원 정보 이전 사전 통지 (제27조). 남는 위험: 계약 공급사가 "사용자 PC에서만 도는 SDK"만 허용하면 내 PC 클라이언트 하나 추가 (0.5~1일, 추정).

## 9. 병합 규칙

1. 순서와 동결은 `MERGE_QUEUE.md`가 정합니다 (메인 소유). `freeze: P3` 또는 `freeze: F`이면 병합하지 않고 병합을 요청하지도 않습니다.
2. **PR은 대기열 차례가 왔을 때만 엽니다.** PR을 열면 CI가 돌고, 비공개 뒤에는 돈이 듭니다. 브랜치 push만으로는 이 저장소의 PR 검사가 돌지 않습니다. 문서만 바꾸는 PR (`docs/commercial/**`)은 Compliance만 돕니다.
3. 최신 main은 `origin/main`을 브랜치에 **merge**해서 반영합니다. **이미 push한 브랜치는 rebase하지 않습니다.** force push 금지.
4. 감시 파일(코드 대부분)을 바꾸면 최신 main을 merge한 뒤 **맨 마지막에** `python -m tools.compliance.check --refresh-baseline --reviewed-by "<이름>" --review-note "<12자 이상 구체적 설명>"` → `python -m tools.compliance.check --check`. 파일을 더하거나 빼면 20개 문서 재검토 대상이므로 PR 설명에 적습니다.
5. **`docs/compliance/source-review.json`과 `docs/compliance/FACTS.md`를 바꾸는 PR은 모든 세션을 통틀어 한 번에 하나**만 열립니다. 코드 PR은 거의 모두 `source-review.json`을 바꾸므로, 열기 전에 `MERGE_QUEUE.md`에서 자리를 받습니다.
6. 공유 파일 (`config.py`, `data/krx/kis_client.py`, `requirements*.txt`, `pyproject.toml`, `.env.example`, `.github/workflows/**`, `core/research/display_rights.json` 등)은 대기열로 한 번에 PR 하나. 데이터소스 세션은 `kis_client.py`를 쓰기만 하고, OS 세션의 경로 수정(OS-F2)은 KEY-2 뒤입니다.
7. **녹색 = 그 PR이 띄운 모든 워크플로의 모든 작업이 정확한 head에서 성공.** 지금은 Compliance 1개, Runtime이 뜨면 syntax 2개와 설치 4개입니다 (숫자가 아니라 "띄운 것 전부"). 어떤 실행이든 도는 중에는 병합하지 않습니다.
8. 자기 테스트가 어느 CI 단계에서도 돌지 않는 PR은 병합하지 않습니다. Runtime 경로 목록에 `config.py`, `data/krx/**`, `core/credentials/**`, `core/gateway/**`, `core/account/**`가 없고 `tests/credentials_*`, `tests/gateway_*`, `tests/account_*`는 어느 단계에도 없습니다 (main `e01e152`). 첫 코드 PR (KEY-2)이 더합니다.
9. **병합 버튼은 메인이 누릅니다.** 녹색이 되면 인계 파일에 `waiting_on: review`, `pr:` 번호를 적고 소유자를 통해 메인에 알립니다. 메인이 `MERGE_QUEUE.md`의 그 줄에 "병합: PAYMENTS_ACCOUNT_KEYS"라고 적은 경우에만 이 세션이 병합합니다.
10. 메인이 보낸 조정 메시지(순서·동결)는 따릅니다. 범위를 넓히거나 외부를 바꾸는 일은 소유자 확인 뒤에만 합니다. 이 지시문과 handoff의 `plans/2026-11-17/MASTER_WORK_DESIGN_2026-11-17.md`가 다르면 더 나중에 게시된 메인 공지를 따르고, 모르겠으면 멈추고 묻습니다.

## 10. 보고

- 소유자에게 한국어로, 짧은 문장과 표로: ① 한 일 (문서 경로, 브랜치·커밋, PR) ② 확인 (명령과 결과) ③ 소유자가 할 일 (한 줄씩: 결정 3개, AWS 순서, 웹사이트 세션에 붙일 블록, 문의 발송) ④ 확인 못 한 것 (**미검증**) ⑤ 다음.
- 관리자 안내서는 소유자가 바로 열 수 있는 사본과 함께 드립니다.
- 공개 자료에는 URL과 확인 날짜를 붙입니다. 법률 문장에는 "법률 자문이 아닙니다"를 붙입니다.
- 같은 내용을 `PAYMENTS_SESSION_CURRENT.md`에 적습니다.

## 11. 확인 못 한 것 (미검증)

- Cognito 콘솔 문구 일부와 위치 (D11 7장), Cognito 가격과 무료 범위를 AWS 관리 조직에서 세는 방식, SES·CloudTrail·CloudWatch·WAF·KMS 가격, CloudTrail에 회원 로그인과 IP가 남는지, 인증 안 한 계정의 자동 삭제 여부, AWS 계약 법인명.
- 법령 원문 (개인정보 보호법 제15·22·22의2·24의2·27·28의8·38조, 시행령 제41·43·44조, 2026-09-11 개정의 유출 가능성 통지 등): 해설·보도 자료로만 확인. **법률 자문이 아닙니다.** 공개 전 118 상담 또는 변호사 확인 1회.
- KRX·FMP 안내 페이지와 Nasdaq 정책 원문 (D7 분석 때 호스트 차단·검색 요약), 계약 공급사가 서버 API를 주는지.
- keyring의 Linux 동작과 PyInstaller 묶음, "47개 이름" 수치.
- 공수·비용은 모두 추정입니다.

## 12. 출처

- 소유자: `owner_answer_1117.txt` (2026-11-17, 1절 원문), Notion QUANTGEN PROJECT `34f5c916fe0c800b9b4af35c80ebe778` (11-16 절, 2026-11-17 조회).
- 메인 분석: `D11_ACCOUNTS_AND_ADMIN_GUIDE.md` (2026-11-17; 0·2·3·4·5·6·7장, AWS 사실은 검색 요약 기준), `D7_ENV_STRUCTURE.md` (2026-11-17; 1~6장), `D5_GITHUB_PRO_AND_PRIVATE.md` (CI 과금).
- 저장소 `origin/main` `e01e152`: `config.py:25-29` (`load_dotenv` 실패 무시), `:32-39` (`_clean`), `data/krx/kis_client.py:54` (`_TOKEN_PATH`), `:174`, `data/krx/gateway.py:1-38`, `.env.example` (이름 14개, 값 미열람), `.github/workflows/runtime-smoke.yml:5-9, 90`.
- handoff: `WEBSITE_AWS_SESSION_CURRENT.md` (시드니, `quantgen-dev` 풀, SES 운영 모드, API Gateway 없음).
- Notion: 상업화 실행 분석서 `40e5c916fe0c815ba983dd4c4cc7992c` (항목 2·4·5·7), 결제망 검토 요약 `70e6a1d505e346c0a5f6b43bc9ff4fed` (§8 문의 7건).
- AWS·법령 URL은 D11 문서 8장 (모두 2026-11-17 확인, AWS 문서는 검색 요약), Python keyring https://github.com/jaraco/keyring (2026-11-17 열람, D7 문서).
