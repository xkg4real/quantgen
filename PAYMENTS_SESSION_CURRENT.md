---
status: checkpoint
reason: milestone
from: claude
task: payments-account-keys
cycle: 2026-11-17
done_ids: KEY-2, KEY-2/b
next_ids: PAY-A1, PAY-A2, KEY-1, KEY-3/design, KEY-3, PAY-0, PAY-2
updated_at: 2026-11-19T15:30:00+09:00
stale_after_hours: 3
waiting_on: none
work_branch: claude/payments-key3-prep-20261119
work_commit: 8a2886b
uncommitted_changes: no
pr: none
usage_weekly_pct: unknown
usage_5h_pct: unknown
usage_resets_at: 2026-11-24T17:00:00+09:00
session: https://claude.ai/code/session_016uB1jfZfzo935a4uucyT2S
---

# 인수인계: QUANTGEN/MAIN -> PAYMENTS_ACCOUNT_KEYS

운영 기준: [자동감시 취소·수동 인계](OWNER_HANDOFF_POLICY_2026-11-13.md).

## 0. 한 줄 요약

**2026-11-19 15:30 갱신 — 소유자 답 (원문):**
> 1. owner confirmed 완료
> 2. Key-3 승인
> 3. 더해주세요

- 1: GitHub 확인 결과 main 두 표는 여전히 `code f995600b36c75523`이고 `owner/nautilus-confirm-*` 브랜치·PR 없음 (15:2x KST). 메인 지침은 "지금 하지 않음, 다음 기록 실행 직전"이라 소유자에게 그대로 알림. 메인에 전달함.
- 2: `GATEWAY_DESIGN.md` v0.1 소유자 승인 → 문서에 기록. KEY-3/design은 그 문서가 main에 들어가면 (KEY-3 PR) LEDGER 요청.
- 3: `core/credentials/names.py`에 `RESEARCH` 9개 (DIDM 연구용: FRED, ECOS, SEC_EDGAR_USER_AGENT, Alpha Vantage, Tiingo, Cryptopanic, CME FedWatch 2개, Trading Economics), 종류 `research`. 시험 52 OK. 브랜치 `claude/payments-key3-prep-20261119` @ `8a2886b`. 데이터소스 세션이 연결 코드를 `core.credentials.get`으로 바꾸는 일은 그쪽 몫 (소유자 경유 전달).
- 다음: KEY-3 코드 (`core/gateway/**`, 시험 3개) 같은 브랜치.


**2026-11-19 12:40 갱신:** PR #129 병합 (main `ca5da08`, 메인이 LEDGER에 KEY-2/b 기록 `4adc965`). KEY-3 준비 브랜치 `claude/payments-key3-prep-20261119`에 main merge (`a5c0841`) 뒤 설계 문서 `docs/commercial/GATEWAY_DESIGN.md` v0.1 (`1734cda`): 부품, routes.json 스키마·검증, 규칙 6개와 시험, 공급원 id·길, 회사 서버 약속(꺼짐), 직접 호출 30개 파일 69곳 (D7은 72; 경계 시험이 기준). 30개 파일 중 Nautilus 지문 입력은 없음. **소유자 설계 확인 대기** (코드는 승인된 D7-G 범위라 병행 가능). 다음: KEY-3 코드 `core/gateway/**`, `tests/gateway_*` (같은 브랜치), 그 PR에 0c3d0d5의 5건 포함.


**2026-11-19 11:50 갱신:** 메인이 PR #129 (`ad124d1`)를 검증함: 1·2·3·4·6 확인, CI 녹색이면 병합 (push 금지). KEY-3 PR에 넣을 5건을 미리 고쳐 **PR 없는 브랜치** `claude/payments-key3-prep-20261119` @ `0c3d0d5`에 둠: 링크인 토큰 파일은 대상만 바꿈, POSIX O_NOFOLLOW + fchmod로 읽기, key_id는 발급에 쓴 키로, 심어 둔 `.tmp` 링크 시험, ENV_NAMES 19·109행과 20-deletion key_id 범위. credentials 50 OK; 새 시험은 main의 옛 kis_client에서 실패함 (8개). kis_stream 6 오류는 main 코드에서도 같은 환경 오류. **다음:** #129 병합 뒤 KEY-3 설계 문서 → KEY-3 코드 (이 prep 커밋을 포함).


**2026-11-19 11:20 갱신:** PR #128 병합됨 (main `3249af7`, 메인이 LEDGER에 KEY-2 기록, handoff `11467ff`). KEY-2/b: 작업 브랜치에 main `3249af7` merge → `cc1cfa3` merge → 기준선 갱신 `ad124d1` (PASS) → **PR #129**. credentials 47 OK, 회귀 실패 집합 main과 같음, 코드 지문 10c27010 그대로. 메인이 CI 녹색이면 병합. 소유자에게 owner_confirmed 안내 (KEY-2 병합으로 이제 필요).


**2026-11-19 10:10 갱신:** 메인 재검증: 6916f8d에서 8건 중 7건 확인, CI 진행 중이라 PR #128에는 push 금지 → 녹색이면 메인이 병합. 후속 KEY-2/b (메인 지적 6건)를 미리 만들어 **PR 없는 별도 브랜치** `claude/payments-keys-key2b-20261119` @ `cc1cfa3`에 둠 (credentials 시험 47 OK, 회귀 실패 집합 main과 같음). 단, 5번 중 `tools/provider_parity/parity_check.py` 주석은 고치지 않음: 그 파일 sha256(`78dd1f50…`)이 `results/RULINGS.md` 92행에 고정돼 있고 `tests.provider_parity_acceptance`가 확인함. **PR #128 병합 뒤 할 일:** 작업 브랜치에 최신 main merge → `cc1cfa3` merge → 기준선 갱신 (맨 마지막) → `--check` → 메인이 "병합: PAYMENTS_ACCOUNT_KEYS"(KEY-2/b) 적으면 PR. 그리고 LEDGER 문자열을 메인에 전달.


**2026-11-19 09:30 갱신:** 메인의 병합 전 검토(PR #128, CI 녹색이지만 보류)의 8건을 반영해 `6916f8d` push. 핵심: (2) 시험이 CI 순서에서 실제 `~/.nextgen/kis_token.json`을 지우던 문제를 재현하고 고침, (4) 그 파일은 TRADEGEN과 공유라 이제 지우지 않음, (1) 준법 문서 01·08·20·FACTS·RELEASE_GAPS를 먼저 고치고 기준선 갱신 (PASS). credentials 시험 40 OK. 코드 지문 10c27010 그대로. 메인 재검토와 CI를 기다림.


**2026-11-19 05:40 갱신:** 메인이 "병합: PAYMENTS_ACCOUNT_KEYS" (MERGE_QUEUE, 05:14 KST). main `c28b1d7` merge (runtime-smoke.yml 충돌 2곳: main 줄 유지 + 내 경로 4개·시험 모듈 1개 추가) → `029be27`; app_identity 연결 시험 2개 추가 (총 31 OK); 회귀 실패 집합 main 코드와 동일; 준수 기준선 갱신 `606f33f` (consistency PASS, 20 문서, 793 소스) → **PR #128**. 본문에 코드 지문 ec72fab3 → 10c27010과 owner_confirmed 재작성 필요를 적음. 병합은 메인 (CI 전부 녹색, Windows 최대 약 2시간). 병합 뒤: LEDGER 요청 `KEY-2 | ...`, 소유자에게 owner_confirmed 안내 (OWNER_STEPS 6절), UI·OS 세션에 "KEY-2 병합" 알림 (소유자 경유).


**2026-11-19 01:40 갱신:** freeze OFF (`MERGE_QUEUE.md` `82fac0c`). KEY-2는 대기열 3번 (1 메인 ⑦-2/a → 2 OS 작은 PR → 3 KEY-2). 메인이 "병합: PAYMENTS_ACCOUNT_KEYS"라고 적으면: 최신 main merge (그때 OS PR의 `core/app_identity.py`가 들어와 있으므로 `may_read_dotenv` 연결을 시험으로 확인) → 기준선 갱신 → `--check` → PR (본문: 코드 지문 ec72fab3 → 10c27010 예상, owner_confirmed 재작성 필요). 그 사이 브랜치에 소유자 안내서 6절 (owner_confirmed 절차) 추가 `7626723`.


**2026-11-19 00:45 갱신:** 소유자가 이 세션에 "F22까지 마무리했습니다"라고 알림. main `6e077dc`(연구 브랜치 병합)을 작업 브랜치에 merge함 (`31b724f`, 충돌 없음, 브랜치만의 파일 12개). `tests.credentials_acceptance` 29 OK (keyring 있음/없음). Nautilus code_sha256: main `ec72fab3…` → KEY-2 브랜치 `10c27010…` (config.py 3줄 변경 때문; PR 본문에 적을 것). `MERGE_QUEUE.md`는 아직 `freeze: ON`이고 KEY-2 차례가 적혀 있지 않아 PR은 열지 않음. 메인이 동결 해제와 순서를 적으면: 최신 main merge → 준수 기준선 갱신 → PR.


**2026-11-18 16:30 갱신 — 소유자 답 Q1~Q3 (원문):**
> Q1 답변 : 예, 다만 제가 법인 설립 설립이 완료되었다고 여기에 말하는 순간 바로 해당 법인 명으로 수정 가능하도록 해주세요
> Q2 답변 : 일단 contact@quantgeneration.com으로 하겠습니다. 현재 웹사이트의 구조도 이렇게 되어있습니다.
> Q3 답변 : 예
> 위 항목 중에서 시험, 전달, AWS, 공개 전 4단계를 수행하기 위해서 해야되는 일들을 구체화하여 .md 파일로 만들어 여기서 다운로드하고 볼 수 있도록 해주세요

반영: `ACCOUNT_SETUP.md`·`ADMIN_GUIDE.md` v0.2 (빈칸 0개, 운영자 표기는 `ACCOUNT_SETUP.md` 0.1절 한 곳 + 법인 전환 절차), 새 `docs/commercial/accounts/OWNER_STEPS.md` (AWS 25단계 값·확인 칸, 웹사이트 전달 메시지, 시험 3-A/3-B, 공개 전 8개와 118 질문). 커밋 `687bf65`. 소유자에게 .md로 전달함. 이제 소유자의 AWS 실행 결과(풀 ID·클라이언트 ID·다른 문구)를 기다리고, 이 세션은 KEY-3 설계로 갑니다. **소유자가 "법인 설립 완료: <이름>"이라고 하면** 0.1절 절차 1번부터 즉시.


**2026-11-18 갱신:** 소유자가 D7-G를 승인했습니다 (원문 "그러면 D7-G의 방식대로 진행하겠습니다", 2026-11-18 14:15 KST; handoff `MERGE_QUEUE.md` 21행, 커밋 `762150c`에서 확인). 그래서 KEY-2 자격 증명 저장소를 브랜치에 구현했습니다 (`178c51e`, main `7c33955`을 merge한 뒤). main 병합은 F21 뒤 대기열 차례에만 하고, PR은 아직 열지 않았습니다. Q1~Q3 답은 아직 없습니다. 다음 일: KEY-3 설계 문서 → KEY-3 코드.

(11-17 요약)

첫 작업 3개의 문서 초안을 브랜치에 push했습니다 (`fed3820`, main `5888d05` 위 3커밋, PR 없음). PAY-A1 관리자 안내서, PAY-A2 계정 설정 묶음, KEY-1 이름 목록입니다. 이제 소유자 답을 기다립니다: 결정 3개 (운영자 표기, 개인정보 메일함, 만 14세), D7-G 승인, 관리자 안내서 4~6절 시험 결과. 세 문서는 소유자 확인 전이라 아직 done이 아닙니다.

## 1. 목표와 완료 조건

- **소유자 원문 (2026-11-17, `owner_answer_1117.txt`):**
  > 3. D11 : 권장과 반대로 진행, 즉 정식 계정 생성까지 진행할 것. 이에 따라 웹사이트에서도 수정할 부분이 있을 예정. 이때, 정식 계정 생성 후 관리자가 어떻게 관리/감독할 수 있는지(구체적으로, 예. 어떤 버튼을 누른다 등)를 기능별로 정리해서 정돈된 문서 형태로 전달할 것.

  > 6. D7 : 법인 상태로 전환해 상업화를 진행하려고 할때 또 다시 수정(이때의 수정은 앱의 구조를 수정한다는 뜻으로, 단순히 키 교체를 의미하는건 아님. 즉, 단순한 변경이 아닌 어느 정도 작업량이 요구되는 작업을 의미함)해야 한다면 거부. 그게 아니라면 승인
- **소유자 원문 (2026-11-16, Notion `34f5c916fe0c800b9b4af35c80ebe778`):**
  > .env 파일 없이 구동할 수 있는 방법 없나… 진지하게… → 클로드한테 다시 정식으로 물어볼 것
  > - 만약 법인 설립이 필요한 부분이면서 법인 설립 이후 이 방법을 실행했을때 앱의 작동 워크플로우가 수정이 필요하다면 미리 수정할 것.
- **완료 조건:** 지시문 `plans/2026-11-17/sessions/05_PAYMENTS_ACCOUNT_KEYS.md` 7절 작업 1~3. 범위 밖: 화면 코드, 웹사이트 코드, AWS 변경, `docs/compliance/**`, D7-G 승인 전 KEY 코드.

## 2. 근거

| 종류 | 위치 | 쓰는 부분 |
|---|---|---|
| 지시문 | handoff `plans/2026-11-17/sessions/05_PAYMENTS_ACCOUNT_KEYS.md` | 전체 |
| 메인 분석 | handoff `plans/2026-11-17/D11_ACCOUNTS_AND_ADMIN_GUIDE.md` | 2~7장 |
| 메인 분석 | handoff `plans/2026-11-17/D7_ENV_STRUCTURE.md` | 1·5장 |
| 병합 순서 | handoff `MERGE_QUEUE.md` (2026-11-17T21:56, freeze: none) | KEY-2~5는 F21 뒤, D7-G 승인 뒤 |
| 저장소 | `origin/main` `5888d05` | `config.py`, `core/markets.py:222`, `.env.example` (이름만) |
| 외부 | AWS 문서는 검색 요약 (2026-11-17). `docs.aws.amazon.com`·`docs.aws.eu`·`repost.aws`는 이 세션 프록시가 거절 | 콘솔 문구 |

## 3. 판단 기록

| 결정 | 이유 | 버린 대안 |
|---|---|---|
| D7-G 승인 전 코드 없음, KEY-2 설계는 `ENV_NAMES.md` 5절 메모로만 | 지시문 2.2, 공통 규칙 11 | KEY-2 브랜치 선행 작업 |
| 콘솔 문구 8개 상태를 검색 요약으로 다시 확인 | 문서 사이트가 막힘 | 전부 미검증으로 둠. 결과: 자가 가입 토글·User event history는 확인, 속성 Edit·이메일 인증 표시·삭제 보호 위치는 부분 확인, Create user·그룹 빼기 버튼·재발송 버튼은 미검증 (CLI 대안은 확인) |
| 소유자 결정은 `{{operator_name}}`, `{{privacy_mailbox}}`, `{{support_mailbox}}`, `{{min_age}}` 자리표시 | 지시문 작업 2 완료 조건 2 | 권장값 미리 채우기 |
| 문서 브랜치 하나 (`claude/payments-keys-20261117`) | 지금은 문서만이라 섞이지 않음 | `claude/accounts-docs-20261117` 분리 (코드 시작 때 다시 판단) |
| 소유자용 사본은 HTML (스크래치 `out/QUANTGEN_ADMIN_GUIDE.html`, `out/QUANTGEN_ACCOUNT_SETUP.html`, 채팅으로 전달) | 지시문 작업 1 | Notion 사본 (소유자 승인 뒤에만) |

## 4. 진행 상황

- [x] PAY-A1 `docs/commercial/accounts/ADMIN_GUIDE.md` v0.1 — 커밋 `8e8a17f`. 0절 (들어가는 길, 상태 이름표, 문구 확인표 17행) + 1~15절 기능 (언제 / 누를 순서 / 회원에게 생기는 일 / 주의 / 확인 상태) + 16 점검표 + 17 사고 대응 + 부록 A~D. 법률 문장 12곳 모두 "법률 자문이 아닙니다" + 조문 + URL 또는 "URL 미확보" + 날짜. **소유자 시험 대기 (부록 C)**.
- [x] PAY-A2 `docs/commercial/accounts/ACCOUNT_SETUP.md` v0.1 — 커밋 `bbb7c8c`. 1부 설정표 (값마다 변경 가능 여부·확인 상태), 2부 25단계, 3부 웹사이트 블록 (D11 4장과 3667바이트 일치), 4부 정책 값 (main 실제 자리표시 이름에 맞춤). **소유자 결정 3개 대기**.
- [x] KEY-1 `docs/commercial/ENV_NAMES.md` v0.1 — 커밋 `fed3820`. 26개 이름 모두 행, 값 0개, 저장소 전체 49개 (47과 2개 차이 설명), 연구용 7개 따로, 5절 KEY-2 설계 메모. **소유자 확인 대기**.
- [x] KEY-2 자격 증명 저장소 (브랜치, 미병합) — 커밋 `178c51e`. 새 파일 `core/credentials/__init__.py`·`names.py`, `tests/credentials_acceptance.py`. 바꾼 파일 `config.py` (`.env` 로딩은 개발판에서만, 비밀 10개만 저장소 경유), `data/krx/kis_client.py` (토큰을 keyring에 두고 파일은 대체 수단, 키가 바뀌면 토큰 삭제, `reload_credentials()`), `requirements.txt`·`pyproject.toml` (`keyring>=25.6,<26`), `runtime-smoke.yml` (경로 4개, 시험 모듈 1개). `quantgen_cloud` 자리 없음.
- [ ] KEY-3/design `docs/commercial/GATEWAY_DESIGN.md` ← **다음**.
- [ ] KEY-3 코드 `core/gateway/**`, `tests/gateway_*`.
- [ ] PAY-0 문의 7건 초안, PAY-2 결제 설계 — 아직 시작 안 함.

**마지막으로 통과한 검증:**

```
KEY-2 (2026-11-18, 커밋 178c51e):
HOME=<임시> python3 -m unittest tests.credentials_acceptance            -> 29 OK (skipped=2, keyring 없음)
HOME=<임시> PYTHONPATH=<keyring 25.7.0> python3 -m unittest tests.credentials_acceptance -> 29 OK
회귀: runtime-smoke.yml 93행 모듈 + kis_stream + kis_workspace 를 바꾸기 전/후 같은 환경에서 실행 -> 실패 집합 동일
  (이 컨테이너에 scipy·flet이 없어 생기는 실패만 있음. 두 환경: 기본 / keyring+scipy 추가)
python -m tools.compliance.check --check -> consistency FAIL (새 소스 파일 때문에 20개 문서 재검토 필요; 기준선 갱신은 PR 때 최신 main merge 뒤 맨 마지막에 함)

python3 -I <scratch>/tools/check_account_setup.py <D11 문서> docs/commercial/accounts/ACCOUNT_SETUP.md
속성 표 6개 = ACC-1 6개 일치=True; ACC-5 (mkt_opt, mkt_at) 표 안에 포함=True; 3부 블록 = D11 4장 원문 3667바이트 일치=True
ENV_NAMES.md: 26개 이름 모두 표 행에 있음=True, NAME=값 꼴 0건
```

## 5. 중단 지점

커밋 안 한 변경 없음. 대조 스크립트와 HTML 변환 스크립트는 스크래치 `tools/` (저장소 밖). 다른 세션은 D11 문서와 이 브랜치의 ACCOUNT_SETUP.md만으로 같은 대조를 다시 할 수 있음 (속성 이름 6개, 4부 "복사 시작~끝").

## 6. 다음 할 일 (순서대로)

1. 소유자 답 Q1~Q3 → `ACCOUNT_SETUP.md`·`ADMIN_GUIDE.md`의 `{{…}}` 채움 → push → `## 메인에게` 정책 값 전달 표시. 완료 기준: 자리표시 0개 (`grep -c "{{" docs/commercial/accounts/*.md` 가 0, 단 4부의 main 자리표시 이름 인용은 제외).
2. 소유자 부록 C 결과 → 다른 곳 고쳐 v0.2. 완료 기준: C1~C8 "그대로 됨/다름" 기록.
3. KEY-3/design `docs/commercial/GATEWAY_DESIGN.md` (지시문 8절). 완료 기준: 소유자 확인.
4. PAY-0 (`docs/commercial/inquiries/`), PAY-2 결제 설계. 완료 기준: 소유자 확인.
5. KEY-3/design → KEY-3 코드 (지시문 8절, D7 5장). 완료 기준: 가짜 서버 시험 ("personal ↔ 가짜 서버 경유 commercial 같은 답"), 경계 시험의 예외 수 기록.
5a. KEY-2 병합 (F21 뒤, 대기열 차례). **PR 본문에 꼭 적을 것 (메인 요청 2026-11-18):** "config.py 변경 → Nautilus 브리지 code_sha256 바뀜 (`config.py`는 연구 브랜치 `tools/nautilus/runner.py` `code_paths`의 입력) → 다음 기록 실행 전 소유자가 owner_confirmed 두 줄을 새로 씀". config.py 변경은 3줄로 줄였음 (`.env` 로딩·설정 읽기를 `core/credentials`의 `load_dotenv_for_development`·`read_setting`으로 옮김). 순서: 최신 main merge → `python -m tools.compliance.check --refresh-baseline --reviewed-by "<이름>" --review-note "<12자 이상>"` → `--check` → PR (파일 추가가 있으니 20개 문서 재검토를 PR 설명에 씀) → 모든 작업 녹색 → 메인이 병합.
6. 세 문서는 소유자 확인 뒤 메인에 LEDGER 기록 요청 (main에 넣는 PR은 대기열 차례가 올 때만; 문서 PR은 Compliance만 돎).

## 7. 주의사항

- `docs/asset_expansion/cache/` 열기·목록·검색 금지 (작업은 sparse 클론 `<scratch>/wt`). `.env`, `~/.nextgen` 열지 않음. 값은 어디에도 쓰지 않음.
- AWS·웹사이트·Notion 변경 금지 (소유자만). UI·웹사이트 세션 파일 수정 금지. `CURRENT.md`에 `push_handoff.py`를 파일 인자로 실행하지 않음.

## 소유자 답 대기

(2026-11-18: Q1~Q3 답 받음 → 아래 표의 Q1~Q3는 끝남. D7-G도 승인됨. 남은 것: AWS 실행 결과, 시험 부록 C, 웹사이트 전달 날짜, 공개 전 8개)

| # | 질문 | 권장 |
|---|---|---|
| Q1 | 공개 문서 운영자를 "(주)넥스트제너레이션" → 소유자 개인 성명 + 서비스명 QUANTGEN으로 바꿀까요? | 예 |
| Q2 | 개인정보 요청을 받을 메일 주소는? (지원 메일 `support@`도 함께) | `privacy@quantgeneration.com` (수신 시험 뒤) |
| Q3 | 무료 회원 최소 연령 만 14세 (본인 진술), 유료 만 19세로 할까요? | 예 |
| D7-G | 공급원 게이트웨이 안 (D7_ENV_STRUCTURE.md 5장) 승인 | 메인이 올린 권장안 |
| 시험 | 관리자 안내서 부록 C (정지 → 로그인 막힘 → 해제 → 재설정 → 삭제) "그대로 됨/다름" | — |
| 네트워크 (선택) | 세션 네트워크에 `docs.aws.amazon.com` 허용 시 미검증 문구 재확인 | — |

## 메인에게

- **2026-11-18 정책 값 확정 (Q1~Q3):** 운영자 = 개인 (소유자 성명, `release-profile.json` `operator.representative`와 같은 사람, "(주)" 없음), 개인정보 보호책임자 = 같은 사람, `operator.privacy_contact`·`operator.support_email`·`{{privacy.contact_email}}`·`{{operator.support_email}}` = `contact@quantgeneration.com`, `{{age.minimum_age}}` = 14 (유료 19). 전체 값: 브랜치 `ACCOUNT_SETUP.md` 4부 (`687bf65`). 소유자가 법인 설립을 알리면 같은 칸을 법인명으로 바꾸는 PR을 다시 요청함 (0.1절).

- **2026-11-18 KEY-2 (브랜치 `178c51e`, 미병합):** 정책 문서에 넣을 새 의존성: `keyring>=25.6,<26`. 이 세션에서 설치한 25.7.0의 METADATA는 `License-Expression: MIT`이고, 의존성 `jaraco.classes`, `jaraco.functools`, `jaraco.context`, Windows `pywin32-ctypes`, Linux `SecretStorage`·`jeepney`, 3.12 미만 `importlib_metadata`. 19-licenses·08-third-parties 행은 메인 몫 (LICENSE 원문은 대조하지 않음, 미검증). 처리방침 쪽 사실: API 키와 KIS 토큰은 사용자 PC의 OS 자격 증명 저장소 (Windows 자격 증명 관리자)에 저장되고, 키 보관함이 없을 때만 KIS 토큰이 `~/.nextgen/kis_token.json`에 남음.
- 주의 (KEY-5 전에 정할 것): 앱 화면에서 키를 keyring에 저장한 PC (소유자 PC)에서 테스트를 돌리면, 환경을 비우는 테스트가 keyring의 실제 키를 "있음"으로 볼 수 있음. 지금은 keyring에 저장하는 화면이 없어 해당 없음. KEY-5 전에 시험 묶음이 `credentials.set_backend(None)`을 쓰도록 하는 방안을 제안 예정.

- 정책 문서 PR에 넣을 값: 브랜치 `claude/payments-keys-20261117`의 `docs/commercial/accounts/ACCOUNT_SETUP.md` 4부 (4.1~4.5). Q1~Q3 답 전에는 자리표시. 대상 문서 `01`, `02`, `04`, `06`, `07`, `08`, `16`, `17`, `18`, `20`, `release-profile.json`.
- 대기열 요청: 지금은 없음 (문서만, PR 안 엶). KEY-2는 D7-G 승인 뒤 F21 뒤 자리.
- LEDGER 기록 요청: 아직 없음 (소유자 확인 뒤 PAY-A1, PAY-A2, KEY-1 요청 예정).

## 웹사이트 세션에 전할 것

- `ACCOUNT_SETUP.md` 3부 블록 (ACC-1~ACC-10, D11 4장과 같음). 소유자에게 전달함 2026-11-17 (채팅 보고). 소유자가 웹사이트 세션에 붙인 날짜: 미기록.
- 풀 ID·클라이언트 ID는 소유자가 AWS 2부 17단계 뒤 전달 (비밀값 아님).

## 데이터소스 세션에 전할 것 (소유자 경유)

- 2026-11-19: KEY-3 PR이 main에 들어가면 `core/credentials`가 DIDM 키 이름 9개를 받습니다 (`names.RESEARCH`). `data/didm/*.py`가 `os.environ.get(KEY_NAME)` 대신 `core.credentials.get(KEY_NAME)`을 쓰면 키를 OS 키 보관함에 둘 수 있습니다 (찾는 순서: 환경변수 → 키 보관함 → `.env` 개발판).

## UI 세션에 전할 것

- 아직 없음. KEY-5 (키·연결 화면은 `gateway.status()` 행을 그대로 그림)는 D7-G 승인 뒤 소유자를 거쳐 전달.
