# H2 홀드아웃 판독 준비 (⑧-1)

- **상태: 초안, 소유자 검토 대기**
- **작업 규칙 이탈 공개(소유자 확인 대기):** 이 초안을 쓰는 동안 Claude가 `tests/frozen_guard.py` 검사 (b)를 직접 불렀습니다.
  이 검사는 git으로 태그의 `paper_live/out/frozen_rule/`과 `paper_live/out_krx/frozen_rule/`의 `engine.py`, `config.py`
  4개 blob을 읽어 바이트를 비교합니다(`tests/frozen_guard.py:35, 75-76`). 이 blob은 동결 시점의 **코드 사본**이고, 홀드아웃
  결과(`replay_holdout/`, `verdict.json`, 스냅샷)가 아닙니다. 내용은 화면에 나오지 않았고 비교 결과(통과)만 나왔습니다.
  - 이 세션은 `paper_live/out*/` 아래를 아예 읽지 않는다는, 프로젝트 규칙보다 엄격한 작업 규칙을 두었고 이를 어겼습니다.
    같은 세션의 Linux 전체 검사(2026-11-04)도 guard 스위트를 돌려 같은 blob을 읽었습니다(`guard/test_b` PASS).
  - guard 스위트는 이전 클라우드 전체 실행(③-6 등)에서도 돌았습니다. 프로젝트 문서에서 이를 금지하는 규칙은 찾지 못했습니다.
  - 이 결과는 이 문서의 근거로 쓰지 않습니다(2.4). 실행 조건과 경위는 9.3에 적습니다.
  - 소유자가 정할 것: 이 기록을 그대로 둘지, Claude 세션의 guard 스위트 실행을 따로 제한할지(D-13).
- 작성: 2026-11-04, Claude (Step 7A 세션). 기준 커밋 `bb35b3b`(`main`, 병합 동결 시작점). 작업 브랜치 `claude/h2-readout-prep-20261104`.
  같은 날 검토 의견을 반영해 고쳤습니다.
- 로드맵 항목: ⑧-1 "H2 홀드아웃(11-03 종료) 판독. 태그 클론에서 실행", 기한 약 2026-12-19
  (`docs/nautilus_bridge/REMAINING_WORK_2026-10-27.md:118`, `docs/nautilus_bridge/ROADMAP_REVIEW_2026-10-27.md:149`).
- 이 문서는 준비 문서입니다. 판독은 소유자 PC에서 소유자만 실행합니다. Claude는 판독을 실행하지 않았고 홀드아웃
  산출물(`replay_holdout/`, `verdict.json`, 스냅샷)을 읽지 않았습니다. 다만 위 사고에서 `out*/frozen_rule/`의 코드 사본
  4개를 git으로 읽었습니다(9.3). `frozen_rule/`은 `freeze()`가 `out*/` 안에 쓴 폴더입니다(`paper_live/verdict.py:60-63`).
- 근거 표기: `파일:줄`은 기준 커밋 `bb35b3b`의 줄입니다. 다른 커밋의 파일은 `커밋:파일:줄`로 적습니다.
  - 태그 `studies-of-record-2026-10-23`(태그 객체 `6e7c1f7`, 커밋 `eacd57d`)의 파일은 `tag:파일:줄`로 적습니다.
  - 연구 브랜치 `claude/amazing-gauss-tdiguu`의 최신 커밋은 `fe37e82`(Step 7A 인계 보고서)입니다.
- 소유자가 정할 것은 8절에 D-1~D-13으로 모았습니다.

## 0. 한눈에 보기

| 항목 | 내용 | 근거 |
|---|---|---|
| 하는 일 | 태그로 만든 **별도 클론**에서 프로필(base, krx)마다 홀드아웃 재생 1번, 판정 1번을 실행합니다 | 분리 스펙 `docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md:82-97` |
| 판정 대상 | H2 비용 게이트. `LAZYOWEN-NAIVE-G2` 손익에서 `LAZYOWEN-NAIVE` 손익을 뺀 값, 홀드아웃 10세션, 단측 대응 t검정, α 0.10 | `paper_live/config.py:187, 199-211`, `paper_live/verdict.py:120-144` |
| 홀드아웃 세션 | 두 프로필 모두 2026-10-21 ~ 2026-11-03, 10세션. 태그 코드로 계산했습니다(2.1) | `paper_live/verdict.py:68-80` |
| 언제 | 지금 실행할 수 있습니다. **가능한 한 빨리** 하기를 제안합니다. Yahoo가 60일을 요청 시각부터 센다면 12-12(토) 요청까지는 통과합니다. 12-13(일) 요청은 시각과 시장에 따라 실패할 수 있고, 12-14(월)부터는 반드시 실패합니다. 마지막 평일은 12-11(금)입니다. 문서의 12-19보다 이릅니다(2.3, Yahoo 경계는 UNVERIFIED) | `paper_live/replay.py:157, 161-163` |
| 어디서 | 메인 클론이 아닌 새 폴더의 태그 클론. 제안 위치는 `C:\Users\whydi\QUANTGEN-studies`(OneDrive 밖, D-3) | 분리 스펙 `:82-88, 106` |
| 같이 돌리면 안 되는 것 | Step 7A PowerShell 블록, 파일럿, 테스트 스위트. QUANTGEN 앱은 제안입니다(근거 문서 없음). 스위트와 판독을 같이 돌리지 않는 것은 T-HERM-02에서 끌어낸 추정입니다(6.3) | Nautilus 스펙 `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md:193-196`(파일럿과 판독), `fe37e82:docs/nautilus_bridge/RUNBOOK_windows.md:32`(Step 7A 동안), `tests/macro_acceptance.py:113-138` |
| 네트워크와 키 | Yahoo(yfinance)만 씁니다. API 키는 필요 없습니다. 집 네트워크로 충분합니다(6.4) | `paper_live/engine.py:166-186` |
| 걸리는 시간 | 점검 포함 1~2시간으로 추정합니다. 계산은 프로필당 수 분~수십 분으로 추정합니다(UNVERIFIED, 3.0) | — |
| 산출물 | 태그 클론 안의 `paper_live/out*/data/holdout_5m_60d_<UTC날짜>.csv.gz`, `MANIFEST.json`, `replay_holdout/`의 4개 파일, `verdict.json` | `paper_live/replay.py:147, 199-203, 229`, `paper_live/verdict.py:174` |
| 끝나면 Claude에게 | 유효성 항목만 보냅니다(5.4 양식). 결과 수치는 소유자가 정하기 전에는 보내지 않습니다(제안, D-7) | 이 문서 5.4 |
| 가장 큰 위험 | ① 기한(2.3). ② 전역 Python에 `nautilus_trader`가 설치돼 있다는 7A 기록. 고정 버전이 바뀌었을 수 있습니다(6.5) | `fe37e82:docs/nautilus_bridge/handoff/win_amd64.json:96-101` |

## 1. H2가 무엇이고 판독이 무엇을 정하나

### 1.1 가설 H2 (사전 등록, 2026-10-20 동결)

| 항목 | 값 | 근거 |
|---|---|---|
| 주장 | "the 2x cost gate loses less than the same rule without it" | `paper_live/config.py:200` |
| 지표 | 세션 순손익 `LAZYOWEN-NAIVE-G2` − `LAZYOWEN-NAIVE`, `frozen` 뒤 세션의 재생 | `paper_live/config.py:201`, `paper_live/verdict.py:31, 139` |
| 검정 | 단측 대응 t > 0, 자유도 n−1. Newey-West(lag 5)는 보고만 하고 판정에 쓰지 않습니다 | `paper_live/config.py:202-203`, `paper_live/verdict.py:140-144` |
| 유의수준 | 단측 α 0.10, 검정력 0.80 | `paper_live/config.py:187-188` |
| 표본 | `frozen`(2026-10-20) 뒤 기준 시장의 첫 10세션, 정확히. 빠진 세션이 있으면 미완료이고 표본을 옮기지 않습니다 | `paper_live/config.py:186, 204-206` |
| 단위 | 프로필별 별도 주장. base와 krx를 따로 보고합니다 | `paper_live/config.py:207` |
| 규칙 | p ≤ α이면 confirmed. 표본이 생기기 전에는 pending | `paper_live/config.py:208` |
| 동결 대상 | 두 계정의 규칙 다이제스트, 게이트가 쓰는 live 시그마, `out*/frozen_rule`의 `engine.py`·`config.py` 사본. 마지막 홀드아웃 재생 전에 바뀌면 H2는 무효 | `paper_live/config.py:209-211` |
| 동결 시각 | base `2026-10-20T01:11:07Z`, krx `2026-10-20T01:11:09Z` | 태그 메시지(`git show studies-of-record-2026-10-23`) |

### 1.2 두 프로필

| 항목 | base | krx | 근거 |
|---|---|---|---|
| 설정 | `PAPER_PROFILE` 없음 | `PAPER_PROFILE=krx` | `paper_live/config.py:228, 233` |
| 출력 폴더 | `paper_live/out/` | `paper_live/out_krx/` | `paper_live/engine.py:31` |
| 기준 종목(첫 종목) | `ES=F`(CME) | `069500.KS`(KRX) | `paper_live/config.py:46, 244`, `paper_live/replay.py:27` |
| 세션을 세는 달력 | US(`CME`는 `MARKET_FOR_VENUE`에 없어 기본값 US) | KRX | `paper_live/verdict.py:72-73`, `paper_live/config.py:30` |
| 하루 창(UTC) | 11:42~16:42 (KST 20:42~01:42) | 01:20~06:20 (KST 10:20~15:20) | `paper_live/config.py:13-14, 234-235` |
| 비교 계정 | `LAZYOWEN-NAIVE`, `LAZYOWEN-NAIVE-G2` (재생은 6개 계정 모두 돌립니다) | 같음 | `paper_live/config.py:170-177`, `paper_live/replay.py:188-195` |

### 1.3 `verdict.json`의 H2 상태

| 상태 | 언제 | Phase 2 선행 조건을 채우나 | 근거 |
|---|---|---|---|
| `pending` | 예정 세션 일부가 `replay_holdout/days.csv`에 없고, 오늘이 마지막 예정 세션 이전 | 아니요 | `paper_live/verdict.py:127-132`, 분리 스펙 `:369-373` |
| `incomplete` | 같은 경우인데 오늘이 마지막 예정 세션 뒤 | 아니요 | 같음 |
| `invalid: ...` | 재생이 쓴 규칙 다이제스트가 동결본과 다름 | 아니요 | `paper_live/verdict.py:134-137` |
| `confirmed` | 10세션이 모두 있고 p ≤ 0.10 | 예 | `paper_live/verdict.py:138-142` |
| `not confirmed` | 10세션이 모두 있고 p > 0.10 | **예.** 유효한 "확인 안 됨"도 자격이 됩니다 | 같음, 분리 스펙 `:370-372` |

- 위 표의 "예"는 판독 부분만 채운다는 뜻입니다. Phase 2 선행 조건에는 보관된 증거도 들어 있습니다(분리 스펙 `:370-371`, 1.4).
- 판정 모듈은 시작 전에 세 가지를 확인하고 하나라도 어긋나면 멈춥니다(`paper_live/verdict.py:164-171`).
  - `out*/HYPOTHESES_frozen.json`이 있어야 합니다.
  - 그 파일의 `frozen_utc` 날짜가 `frozen`(2026-10-20)보다 늦으면 안 됩니다.
  - 지금의 `config.HYPOTHESES`가 동결본과 같아야 합니다.
- 최종 상태일 때 H2 칸에는 `status`, `sessions`, `days`, `mean_diff`, `t`, `p_one_sided`, `t_nw5_reported`, `gated_won`, `snapshot`이 들어갑니다(`paper_live/verdict.py:142-144`).
- `verdict.json`에는 H1(실거래와 같은 날 재생의 차이)과 H3(검정력 선만)도 같이 들어갑니다(`paper_live/verdict.py:172-173`). ⑧-1이 정하는 것은 H2입니다.

### 1.4 판독이 정하는 것과 정하지 않는 것

- **정하는 것**
  - 프로필별 H2 상태(1.3).
  - 분리 스펙 Phase 2(⑧-4, LAZYOWEN 이관)의 선행 조건 일부. 두 프로필 모두 완료되고 유효해야 합니다(분리 스펙 `:369-373`, `docs/nautilus_bridge/REMAINING_WORK_2026-10-27.md:136`).
  - 선행 조건에는 "보관된 증거(archived evidence)"도 들어 있습니다(분리 스펙 `:370-371`). 분리 스펙은 산출물을 main에 복사해 커밋한다고 적습니다(`:99-101`). 그래서 ⑧-4는 판독만으로 풀리지 않고 D-5의 산출물 커밋도 기다립니다. 비공개 보관으로 이 조건을 채울지는 D-6입니다.
  - `tests/frozen_guard.py` 조항 (d)의 H2 부분. 두 프로필의 `verdict.json`이 main에서 최종 상태가 되면 H2는 대기 목록에서 빠집니다(`tests/frozen_guard.py:55-63`). GROKTEAM look이 2027-02-01 뒤에 커밋될 때까지 (d)는 계속 살아 있습니다.
- **정하지 않는 것**
  - 엣지 여부. H3는 검정력 선만 보고합니다(`paper_live/config.py:213-218`).
  - 실거래 승격. 승격 기준은 따로 정합니다(`docs/nautilus_bridge/ROADMAP_REVIEW_2026-10-27.md:55`, E2).
  - GROKTEAM-BOOK. 별도 연구이고 look은 2027-02-01 01:00 UTC 이후 단 한 번입니다(분리 스펙 `:57`, ⑧-3).

## 2. 선행 조건과 기한

### 2.1 홀드아웃 세션 (코드와 설정으로만 계산)

| 프로필 | 기준 달력 | 세션 (10개) |
|---|---|---|
| base | US | 2026-10-21, 10-22, 10-23, 10-26, 10-27, 10-28, 10-29, 10-30, 11-02, 11-03 |
| krx | KRX | 2026-10-21, 10-22, 10-23, 10-26, 10-27, 10-28, 10-29, 10-30, 11-02, 11-03 |

- 계산 방법:
  - 태그의 `core/`, `data/calendars/`, `paper_live/{__init__,config,verdict,power}.py`만 `git archive`로 스크래치 폴더에 풀었습니다. `paper_live/out*/`는 풀지 않았습니다.
  - 고정 버전 인터프리터(Python 3.13.18, numpy 2.3.5, pandas 2.3.3, scipy 1.18.0)로 `verdict.holdout_sessions({"hypotheses": _norm(config.HYPOTHESES)})`를 프로필마다 불렀습니다. 함수 호출은 허용된 방식입니다(분리 스펙 `:124`). 판정 모듈의 `main()`은 부르지 않았습니다.
- 판정은 동결 파일의 `hypotheses`를 씁니다. 저는 `config.HYPOTHESES`를 썼습니다. 둘이 다르면 판정이 멈추므로(`paper_live/verdict.py:170-171`) 결과는 같아야 합니다. 소유자가 태그 클론에서 동결 파일로 한 번 더 확인합니다(3.5).
- 달력은 태그, `bb35b3b`, `fe37e82`에서 같습니다. `core/calendars/__init__.py`의 sha256 앞 16자리는 세 커밋 모두 `39018920ce891312`입니다. `data/calendars`의 git 트리는 세 커밋 모두 `b2584dd9d5d3`입니다(`git rev-parse <커밋>:data/calendars`). 두 달력의 범위는 2026-01-01~2027-12-31입니다.
- 결과는 분리 스펙 5A의 기록(10-23 계산, 11-03 종료)과 같습니다(분리 스펙 `:626-628`).

### 2.2 가장 이른 실행 시점

- 재생은 지연된 막대가 모두 나온 세션만 셉니다. 세션 날짜 + 창 끝 + 30분이 데이터 저장 시각보다 이르거나 같아야 합니다(`paper_live/replay.py:164-166`).
- 마지막 세션 11-03의 기준 시각:
  - base: 16:42 + 30분 = 2026-11-03 17:12 UTC (KST 11-04 02:12).
  - krx: 06:20 + 30분 = 2026-11-03 06:50 UTC (KST 11-03 15:50).
- 둘 다 지났습니다. **지금 실행할 수 있습니다.**

### 2.3 기한: 문서의 "약 12-19"와 코드가 정하는 더 이른 날

- 5분봉은 Yahoo가 약 60일만 보관합니다(`paper_live/engine.py:54-55`). 재생은 `period="60d", interval="5m"`로 받습니다(`paper_live/replay.py:41`).
- 문서는 12-19와 "60일 보관"만 적습니다(분리 스펙 `:64-66, 375-376`, `docs/superpowers/specs/2026-10-23-review/round1_claude.md:137`). 추정: 10-20 + 60일 = 12-19. 문서에는 계산 근거가 없습니다. round1이 인용한 줄은 `paper_live/replay.py:41, 147`입니다.
- 그런데 재생은 받은 데이터의 시작일을 따로 검사합니다(`paper_live/replay.py:161-163`).
  - 모든 종목의 첫 막대 날짜 중 가장 늦은 날(`first`, `:157`)이 `frozen − 6일` = **2026-10-14**보다 늦으면 멈춥니다. 첫 세션 10-21에 6일 치 과거 데이터가 필요해서입니다.
  - pandas 2.3.3에서 `date(2026,10,20) - pd.Timedelta(days=6)`이 `2026-10-14`이고, 시작일 10-14는 통과, 10-15는 거부됨을 확인했습니다(9.3).
- 그래서 모든 종목의 데이터가 10-14 이전이나 그날에 시작해야 합니다. 10-14 + 60일 = **2026-12-13**입니다.
- Yahoo의 60일이 요청 시각부터 정확히 60×24시간을 거꾸로 센 것이라면:
  - **12-12(토)** 요청은 10-13 같은 시각부터 받습니다. 10-13과 10-14는 KRX, US, LSE 모두 거래일입니다(태그의 `core.calendars.is_trading_day`로 확인, 9.3). 그래서 모든 종목의 첫 막대가 10-13이나 10-14에 있고 통과합니다.
  - **12-13(일)** 요청은 10-14 같은 시각부터 받습니다. 그 시각에 10-14 세션이 이미 끝난 종목은 첫 막대가 10-15가 되어 실패합니다. 두 프로필 모두 해당합니다. krx는 KRX 종목(10-14 06:30 UTC경 마감)이, base는 LSE·US 종목(`paper_live/config.py:59-71`, 10-14 16:30·20:00 UTC경 마감)이 걸릴 수 있습니다.
  - **12-14(월)부터는** 모든 종목의 첫 막대가 10-15 이후이므로 반드시 실패합니다.
  - 마지막 평일은 **12-11 금요일**입니다.
- Yahoo가 "60d"를 정확히 어떻게 자르는지는 UNVERIFIED입니다. 데이터 공급사에 접속하지 않는 규칙 때문에 Claude는 확인하지 않았습니다. 그래서 아래의 보수적인 내부 기한을 유지합니다.
- 기한을 넘기면 회복할 수 없습니다.
  - 재생은 계산 전에 멈추고 `replay_holdout/days.csv`를 만들지 않습니다(`paper_live/replay.py:161-163`).
  - 판정은 11-03 뒤이므로 `incomplete`가 됩니다(`paper_live/verdict.py:128-129`).
  - Phase 2 선행 조건을 영영 채우지 못합니다(분리 스펙 `:369-373`).
- 늦게 돌릴수록 홀드아웃 밖 세션도 더 많이 보게 됩니다.
  - 재생은 10-20 뒤의 모든 세션을 받은 날까지 돌리고(`paper_live/replay.py:159, 166`) 날짜별 손익을 화면에 찍습니다(`:197`).
  - 판정은 10세션만 씁니다(`paper_live/verdict.py:138`). 나머지는 이미 본 데이터가 되어, 이후 사전 등록에 쓸 수 없습니다(`paper_live/config.py:219-220`).
- **제안(D-1):** 이번 주 안에 실행합니다. 늦어도 2026-11-30을 내부 기한으로 둡니다. 5A의 12-05 경고 알림은 코드상 마지막 날보다 1주쯤 앞설 뿐입니다(6.6).

### 2.4 그 밖의 선행 조건

| 조건 | 상태 | 근거 |
|---|---|---|
| 태그가 GitHub에 있음 | 확인. `git ls-remote --tags origin`: 태그 객체 `6e7c1f739e31db4c65240496bb0d87f48bf790a7`, 가리키는 커밋 `eacd57d2b0821ad796ab9b66d2d2c96a3d71081f`. 태그 시각 유닉스 `1792729571`, 작성자 Geon Koh | 9.3, `docs/nautilus_bridge/OWNER_GUIDE_1-3_1-5_2026-10-27.md:76-91` |
| 판독 경로 파일이 태그·`bb35b3b`·`fe37e82`에서 같음 | 확인(아래 표) | 9.3 |
| 줄바꿈 변환 없음 | 태그의 `.gitattributes`가 `* -text`. Windows의 `core.autocrlf`와 상관없이 바이트가 그대로입니다 | `tag:.gitattributes:1-2` |
| 고정 라이브러리 버전 | numpy 2.3.5, scipy 1.18.0, pandas 2.3.3, Python 3.13. 소유자 PC의 현재 값은 UNVERIFIED(6.5) | 태그 메시지, 분리 스펙 `:58-60, 92-94`, `tests/frozen_guard.py:85-91` |
| 태그에 `out*/HYPOTHESES_frozen.json`이 있음 | 태그 메시지가 "git-tracked tree"에서 측정했다고 적습니다 | 태그 메시지 |
| 태그에 `out*/frozen_rule/{engine,config}.py`가 있고 규칙 파일과 같음 | 태그 메시지가 "Both out*/frozen_rule copies equal the live files"라고 적고 두 파일의 sha256을 줍니다. 소유자가 3.3의 sha256 검사로 직접 확인합니다. Claude의 `frozen_guard` (b) 실행 결과는 근거로 쓰지 않습니다(머리말의 사고) | `git cat-file -p studies-of-record-2026-10-23`, 이 문서 3.3 |
| 태그에 `out*/model_train_only.json`, `out*/calibration.json`이 있음 | **UNVERIFIED.** 재생이 읽습니다. Claude는 `out*/` 목록을 보지 않았습니다. 소유자가 3.3에서 확인합니다 | `paper_live/replay.py:152-154` |
| 원장 위치 | `QUANTGEN_MACRO_DIR`가 없으면 `~/.nextgen/macro/ledgers`. 소유자 점검 P-5에서 이 변수는 모든 범위와 `.env`에 없습니다 | `paper_live/engine.py:96-104`, `tag:config.py:275-277`, `fe37e82:docs/nautilus_bridge/OWNER_RULINGS_LOG.md:686` |
| 원장 체인이 온전함 | UNVERIFIED. 재생은 계산 전에 세 원장(`QG-TACTICAL`, `QG-CORE`, `LAZYOWEN`)의 체인을 검사하고 깨져 있으면 멈춥니다. 이 검사는 데이터를 받은 뒤에 합니다 | `paper_live/replay.py:148, 172`, `paper_live/engine.py:96-113`, `core/quant/gate_ledger.py:337-355` |

판독 경로 파일의 sha256 앞 16자리:

| 파일 | 태그 | `bb35b3b` | `fe37e82` |
|---|---|---|---|
| `paper_live/engine.py` | `642fc67b10399887` | 같음 | 같음 |
| `paper_live/config.py` | `dc712a9d167e6fb5` | 같음 | 같음 |
| `paper_live/replay.py` | `e83d86f77bd413dc` | 같음 | 같음 |
| `paper_live/verdict.py` | `769ab357be740a9e` | 같음 | 같음 |
| `paper_live/power.py` | `5bcf782fd04397a0` | 같음 | 같음 |
| `core/quant/gate_ledger.py` | `018eaa960b2411dc` | 같음 | 같음 |
| `core/calendars/__init__.py` | `39018920ce891312` | 같음 | 같음 |

- `engine.py`와 `config.py`의 전체 sha256은 태그 메시지의 값과 같습니다: `642fc67b103998870b55c4c9f12c0c0f9189163ee482bdfe029ea2079f418199`, `dc712a9d167e6fb59e162aaf33a0fb65d817fd572e18cb4df018bdaf4cd26ee2`.
- 판독은 어차피 태그 클론의 파일로 돌므로, 이 표는 "main이나 연구 브랜치가 판독 코드를 바꾸지 않았다"는 참고 사실입니다.

## 3. 소유자 PC에서의 실행 절차

### 3.0 준비와 시간

| 단계 | 내용 | 예상 시간 |
|---|---|---|
| 1 | 실행 창 확보, Step 7A 세션에 알림 | 5분 |
| 2 | 태그 클론 만들기 | 수 분 (저장소 크기에 따라, UNVERIFIED) |
| 3~5 | 클론, 인터프리터, 세션 점검 | 10분 |
| 6 | base 재생과 판정 | 수 분~수십 분 (UNVERIFIED) |
| 7 | krx 재생과 판정 | 수 분~수십 분 (UNVERIFIED) |
| 8 | 사후 점검, 보관, 보고 | 15분 |

- 계산 시간의 참고값: 이전 창 전 재생의 실제 시간이 태그 클론의 `paper_live/out/replay/summary.json`의 `seconds`에 있습니다(`paper_live/replay.py:205`). 홀드아웃 결과가 아니므로 소유자가 미리 봐도 됩니다. Claude는 이 값을 보지 않았습니다.
- 전원을 연결하고 절전 모드를 끕니다. 창을 닫지 않습니다. 환경 변수와 기록(transcript)이 창에 묶여 있습니다.
- **UTC 날짜 하나 안에서 끝냅니다.** 스냅샷 이름은 UTC 날짜입니다(`paper_live/replay.py:147`). KST로는 오전 09:00부터 다음 날 오전 08:59까지가 같은 UTC 날짜입니다. 같은 UTC 날짜에 다시 돌리면 새로 받지 않고 저장된 스냅샷을 그대로 읽어 사용합니다(`paper_live/engine.py:170-175`). 스냅샷은 모든 종목이 온 경우에만 저장됩니다(`:181-182`). 날짜가 바뀌면 새로 받습니다. 그래서 **KST 09:30 이후에 시작**하기를 제안합니다.
- PowerShell(일반 권한)에서 실행합니다. 아래 명령은 PowerShell 기준입니다.

### 3.1 Step 1. 실행 창 확보

1. 아래가 하나도 돌고 있지 않은지 확인합니다.
   - Step 7A 7A.2 PowerShell 블록, 파일럿(Step 8, 9), `tests/run_all.py`(어떤 형태든), QUANTGEN 앱.
2. Step 7A 세션에 "지금부터 H2 판독, 끝나면 알림"이라고 한 줄 남깁니다. Step 7A 세션이 그동안 파일럿 실행을 안내하지 않게 하려는 것입니다.
3. 근거:
   - 파일럿과 판독: Nautilus 스펙 `:193-196`(GOVERNANCE-9), `fe37e82:docs/nautilus_bridge/RUNBOOK_windows.md:221`.
   - Step 7A 동안 스위트, 동결 연구 판독, 파일럿을 돌리지 않음: `fe37e82:docs/nautilus_bridge/RUNBOOK_windows.md:32`.
   - 스위트와 판독: 문서 규칙이 아니라 추정입니다. 스위트의 T-HERM-02가 `~/.nextgen/macro` 아래 파일 목록을 전후로 비교합니다(`tests/macro_acceptance.py:113-138`). 분리 스펙 `:143-144`는 스위트와 앱만 다룹니다.
   - QUANTGEN 앱과 판독: 근거 문서가 없는 제안입니다.

### 3.2 Step 2. 태그 클론 만들기

```powershell
cd $env:USERPROFILE
git clone --branch studies-of-record-2026-10-23 "$env:USERPROFILE\OneDrive\Desktop\QUANTGEN" QUANTGEN-studies
cd "$env:USERPROFILE\QUANTGEN-studies"
```

- `git worktree`가 아니라 `git clone`입니다(분리 스펙 `:85-88`).
- 메인 클론에서는 객체만 읽습니다. 메인 클론의 작업 트리, 브랜치, 캐시 파일은 바뀌지 않습니다.
- 출력에 `detached HEAD` 안내가 나오는 것이 정상입니다.
- GitHub에서 받아도 같은 태그 객체입니다(2.4). 그때는 원본 경로 대신 `https://github.com/xkg4real/quantgen.git`을 씁니다.
- 위치는 D-3입니다. 스펙의 예시처럼 메인 클론 옆(`OneDrive\Desktop\QUANTGEN-studies`)도 가능합니다.

### 3.3 Step 3. 클론 점검

```powershell
git rev-parse HEAD
git rev-parse studies-of-record-2026-10-23
git cat-file -t studies-of-record-2026-10-23
git status --porcelain
Test-Path .git -PathType Container
Get-Content .gitattributes
```

| 줄 | 기대값 | 다르면 |
|---|---|---|
| 1 | `eacd57d2b0821ad796ab9b66d2d2c96a3d71081f` | 멈추고 보고 |
| 2 | `6e7c1f739e31db4c65240496bb0d87f48bf790a7` | 멈추고 보고 |
| 3 | `tag` | 멈추고 보고 |
| 4 | 아무것도 출력되지 않음 | 멈추고 보고 |
| 5 | `True` (worktree가 아님) | 멈춤. worktree는 원장 행을 UNVERSIONED로 씁니다(`core/quant/gate_ledger.py:122-131`) |
| 6 | `* -text`가 들어 있음 | 멈추고 보고 |

규칙 파일과 동결 사본의 sha256 (6줄 모두 `OK`여야 합니다):

```powershell
$want = @{ "engine.py" = "642FC67B103998870B55C4C9F12C0C0F9189163EE482BDFE029EA2079F418199";
           "config.py" = "DC712A9D167E6FB59E162AAF33A0FB65D817FD572E18CB4DF018BDAF4CD26EE2" }
foreach ($f in $want.Keys) {
  foreach ($p in "paper_live\$f", "paper_live\out\frozen_rule\$f", "paper_live\out_krx\frozen_rule\$f") {
    $h = (Get-FileHash -Algorithm SHA256 $p).Hash
    "{0}  {1}  {2}" -f $(if ($h -eq $want[$f]) { "OK  " } else { "DIFF" }), $h.Substring(0, 16), $p
  }
}
```

재생과 판정이 읽는 파일 (앞 3개는 `True`, 마지막 줄은 `False`여야 합니다):

```powershell
foreach ($d in "paper_live\out", "paper_live\out_krx") {
  foreach ($f in "HYPOTHESES_frozen.json", "model_train_only.json", "calibration.json") {
    "{0}  {1}" -f (Test-Path "$d\$f"), "$d\$f"
  }
  "{0}  {1}  (기대: False)" -f (Test-Path "$d\replay_holdout"), "$d\replay_holdout"
}
```

- `False`가 하나라도 나오면(앞 3개) 멈추고 보고합니다. 메인 클론에서 복사해 오지 않습니다(D-8).
- `replay_holdout`이 이미 있으면 멈추고 보고합니다. 기한 때문에 소유자가 빨리 정합니다.
  - 기대값 `False`는 추정입니다. 스펙 인용이 아닙니다. 분리 스펙은 10-23에 두 `verdict.json`이 pending이었다고만 적습니다(`:372-373`). 일부 세션만 담긴 이른 홀드아웃 재생도 pending을 냅니다(`paper_live/verdict.py:124-132`).
  - git은 빈 폴더를 담지 않습니다. 새 클론에 이 폴더가 보이면 태그가 그 안의 파일을 추적한다는 뜻입니다.
  - 태그 시각(2026-10-23 04:26 UTC)에는 두 프로필 모두 10-21, 10-22 두 세션만 끝나 있었습니다(2.2의 규칙). 그 전에 홀드아웃 재생이 있었다면 그 세션의 결과를 미리 본 것입니다. 이것은 절차 문제입니다.
  - 폴더가 있어도 새 재생의 숫자는 무효가 되지 않습니다. 재생이 `days.csv`, `trades.jsonl`, `fills.jsonl`, `summary.json` 4개를 모두 새로 씁니다(`paper_live/replay.py:199-203, 229`).

### 3.4 Step 4. 인터프리터 점검

```powershell
python -B -c "import sys; print(sys.executable)"
python -B -c "import sys, numpy, scipy, pandas, yfinance; print(sys.version.split()[0], numpy.__version__, scipy.__version__, pandas.__version__, yfinance.__version__)"
python -B -c "import importlib.util as u; print('nautilus_trader importable:', u.find_spec('nautilus_trader') is not None)"
"QUANTGEN_MACRO_DIR=[$env:QUANTGEN_MACRO_DIR] PAPER_PROFILE=[$env:PAPER_PROFILE] REPLAY_HOLDOUT=[$env:REPLAY_HOLDOUT] REPLAY_LAST=[$env:REPLAY_LAST]"
```

| 줄 | 기대값 | 다르면 |
|---|---|---|
| 1 | 평소 QUANTGEN을 돌리는 전역 Python. 7A 인계 보고서의 `sys_executable` 값 `C:\Users\whydi\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\python.exe`와 같아야 합니다(`fe37e82:docs/nautilus_bridge/handoff/win_amd64.json:100`) | `%LOCALAPPDATA%\quantgen\py313` 또는 `ntvenv`이면 멈춤(4절 N11). D-2 (i)로 정한 전용 venv가 아닌 다른 경로면 멈추고 경로를 보고 |
| 2 | `3.13.x 2.3.5 1.18.0 2.3.3 <yfinance 버전>` | numpy·scipy·pandas가 다르면 **멈춤**(D-2) |
| 3 | `False`가 바람직 | `True`여도 2번 줄이 맞으면 H2는 진행할 수 있습니다. 이 사실은 Step 7A 세션에 따로 알립니다(6.5) |
| 4 | 네 칸 모두 `[]` | 값이 있으면 그 변수를 지우고 다시 확인합니다 |

- 1번 줄은 `(Get-Command python).Source`가 아니라 `sys.executable`을 씁니다. 7A 기록이 `sys.executable` 값이고, Store Python에서 `Get-Command`는 보통 `%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe` 별칭을 돌려주기 때문입니다(소유자 PC에서는 UNVERIFIED).
- yfinance 버전은 고정돼 있지 않습니다(`tag:requirements.txt`의 `yfinance>=0.2`). 보고 양식에 적어 둡니다.
- 7A 인계 보고서의 전역 Python은 3.13.14입니다(`fe37e82:docs/nautilus_bridge/handoff/win_amd64.json:101`). 동결 때 기록된 패치와 같습니다(`fe37e82:docs/nautilus_bridge/RUNBOOK_windows.md:7-10`).

### 3.5 Step 5. 홀드아웃 세션 재확인 (함수 호출만)

```powershell
python -B -c "import json; from paper_live import verdict as V; print(V.holdout_sessions(json.load(open(r'paper_live\out\HYPOTHESES_frozen.json'))))"
$env:PAPER_PROFILE = "krx"
python -B -c "import json; from paper_live import verdict as V; print(V.holdout_sessions(json.load(open(r'paper_live\out_krx\HYPOTHESES_frozen.json'))))"
Remove-Item Env:PAPER_PROFILE
```

- 두 줄 모두 `['2026-10-21', '2026-10-22', '2026-10-23', '2026-10-26', '2026-10-27', '2026-10-28', '2026-10-29', '2026-10-30', '2026-11-02', '2026-11-03']`여야 합니다.
- 다르면 멈추고 보고합니다.
- 이 명령은 함수만 부르고 아무 파일도 쓰지 않습니다(`paper_live/verdict.py:68-80`). `python -m paper_live.verdict`와 다릅니다(분리 스펙 `:124-126`).

### 3.6 Step 6. base 판독

```powershell
Start-Transcript -Path "$env:USERPROFILE\h2_readout_transcript_$(Get-Date -Format yyyyMMdd_HHmm).txt"
Remove-Item Env:PAPER_PROFILE, Env:REPLAY_LAST -ErrorAction SilentlyContinue
$env:REPLAY_HOLDOUT = "1"
python -m paper_live.replay
```

- 정상 끝: 마지막에 JSON 요약이 찍히고 그 안에 `"holdout": true`와 `"snapshot": "holdout_5m_60d_<UTC날짜>"`가 있습니다(`paper_live/replay.py:204-207, 230`).
- 화면에 날짜별 손익(`:197`)과 검정력 문장(`:227-228`)이 찍힙니다. **이것을 보고 멈추거나 다시 돌리지 않습니다**(4절 N8).
- **`WARNING: Yahoo returned no bars`로 시작하는 줄이 나오면 바로 Ctrl+C를 누릅니다.** 날짜로 시작하는 줄(`2026-10-21 {...}`)이 하나라도 나오기 전이어야 합니다.
  - 이 경고는 오류가 아닙니다. 경고 뒤에도 재생은 받은 종목만으로 계속 돕니다. 날짜별 손익, 검정력 문장, 요약 JSON을 찍고 `replay_holdout/`을 씁니다(`paper_live/engine.py:183-186`, `paper_live/replay.py:172, 197-203, 227-230`). 빠진 종목이 기준 종목이면 `KeyError`로 멈출 수도 있습니다(`paper_live/replay.py:155`).
  - 경고 줄은 데이터를 받는 단계(`paper_live/replay.py:148`)에서 나오므로 첫 날짜 줄보다 앞섭니다. 둘 사이의 시간은 UNVERIFIED입니다. 화면을 지켜봅니다.
  - 판정은 돌리지 않습니다. 그다음은 D-4 ①과 3.9를 따릅니다.

정상으로 끝났으면 판정을 돌립니다.

```powershell
Remove-Item Env:REPLAY_HOLDOUT
python -m paper_live.verdict
```

- `H1 fidelity: ...`, `H2 cost gate (base): <상태> ...`, `H3 edge: ...` 줄이 나옵니다(`paper_live/verdict.py:175-184`).
- `--freeze`를 붙이지 않습니다.

### 3.7 Step 7. krx 판독

```powershell
$env:PAPER_PROFILE = "krx"
$env:REPLAY_HOLDOUT = "1"
python -m paper_live.replay
```

정상으로 끝났으면:

```powershell
Remove-Item Env:REPLAY_HOLDOUT
python -m paper_live.verdict
Remove-Item Env:PAPER_PROFILE
Stop-Transcript
```

- 판정 줄은 `H2 cost gate (krx): ...`입니다.
- krx는 출력이 `paper_live/out_krx/`로 갑니다(`paper_live/engine.py:31`).
- 3.6의 WARNING 규칙(바로 Ctrl+C)이 krx에도 똑같이 적용됩니다.

### 3.8 Step 8. 사후 점검, 보관, 보고

5.2, 5.3, 5.4를 차례로 합니다. 끝나면 Step 7A 세션에 "H2 판독 끝"을 알립니다.

### 3.9 멈춰야 하는 신호와 대응

| 신호 | 뜻 | 할 일 | 근거 |
|---|---|---|---|
| `this pull starts <날짜>: it lacks the 6-day lookback ...` | 적어도 한 종목의 데이터가 2026-10-14 뒤에 시작합니다. 기한이 지났거나, 그 종목의 Yahoo 기록이 짧습니다 | 멈춤. 판정 금지. 같은 UTC 날짜에 다시 돌리지 않습니다. 스냅샷이 검사 전에 저장돼 있어 다시 읽으면 같은 결과가 나옵니다. 메시지 원문을 그대로 보고 | `paper_live/replay.py:148, 157, 161-163`, `paper_live/engine.py:170-175, 181-182` |
| `[...] differ from the frozen rule; restore ...` | 규칙 파일이 동결본과 다릅니다 | 멈춤. 파일을 고치지 않고 보고 | `paper_live/replay.py:142-146` |
| `no ...HYPOTHESES_frozen.json: ...` | 동결 기록이 없습니다 | 멈춤. 보고(D-8) | `paper_live/replay.py:138-140` |
| `REPLAY_LAST would drop holdout sessions; ...` | 환경 변수가 남아 있습니다 | `Remove-Item Env:REPLAY_LAST` 뒤 같은 UTC 날짜 안에 재생만 다시 | `paper_live/replay.py:136-137` |
| `WARNING: Yahoo returned no bars for [...]` | 일부 종목이 빠져 스냅샷이 저장되지 않았습니다. 재생은 멈추지 않고 결과를 찍습니다 | 바로 Ctrl+C. 판정 금지. 날짜 줄이 나오기 전에 멈췄으면 D-4 ①에 따라 같은 UTC 날짜 안에서 재생만 다시. 날짜 줄이 이미 나왔으면 본 것으로 칩니다. 다시 돌리지 않고 멈추고 보고 | `paper_live/engine.py:183-186`, `paper_live/replay.py:148-230` |
| `no sessions to replay after 2026-10-20` | 재생할 세션이 없습니다 | 멈춤. 보고 | `paper_live/replay.py:169-171` |
| 원장 관련 `LedgerRefused` 또는 `chain broken` | 원장 체인 문제 | 멈춤. 원장 파일을 열지 않고 보고. 같은 UTC 날짜에 다시 돌리지 않습니다. 스냅샷이 이미 저장돼 있고 원장도 그대로라 같은 오류가 납니다 | `paper_live/engine.py:96-100`, `paper_live/replay.py:148, 172` |
| 그 밖의 `Traceback` | 예상하지 못한 오류 | 멈춤. 오류 줄 원문만 보고 | — |
| 판정이 `freeze the hypotheses first`, `not a pre-registration`, `config.HYPOTHESES has changed` 중 하나로 멈춤 | 사전 등록 검사 실패 | 멈춤. 보고. `--freeze` 금지 | `paper_live/verdict.py:164-171` |
| H2가 `pending` 또는 `incomplete` | 예정 세션이 빠졌습니다 | 멈춤. `missing` 목록을 보고(D-4) | `paper_live/verdict.py:127-132` |
| H2가 `invalid: ...` | 다른 규칙으로 재생됐습니다 | 멈춤. 보고 | `paper_live/verdict.py:134-137` |

## 4. 하면 안 되는 일

| # | 하지 말 것 | 이유 | 근거 |
|---|---|---|---|
| N1 | 메인 클론에서 판독 | main은 판독을 돌리지 않습니다. 메인 클론은 Step 7A~10 동안 연구 브랜치에 있습니다 | 분리 스펙 `:106`, `fe37e82:docs/nautilus_bridge/RUNBOOK_windows.md:221` |
| N2 | `git worktree`로 태그 폴더 만들기 | `.git`이 파일이 되어 원장 행이 UNVERSIONED가 됩니다 | 분리 스펙 `:85-87`, `core/quant/gate_ledger.py:122-131` |
| N3 | 메인 클론에서 트리 전체 `checkout`, `reset`, `stash`, `clean` | 캐시 파일의 수정 시각이 바뀝니다 | 분리 스펙 `:89-91`, `fe37e82:docs/nautilus_bridge/RUNBOOK_windows.md:58` |
| N4 | 재생 전에 `python -m paper_live.verdict` 실행, 언제든 `--freeze` | 판정이 `verdict.json`을 씁니다. 동결 기록은 다시 쓰지 않습니다 | 분리 스펙 `:124-126`, `paper_live/verdict.py:39-58, 174` |
| N5 | `REPLAY_LAST` 설정 | 사전 등록 표본은 고정입니다 | `paper_live/replay.py:136-137` |
| N6 | 태그 클론의 `paper_live/engine.py`, `config.py`, `out*/frozen_rule/`, `HYPOTHESES_frozen.json`, `model_train_only.json`, `calibration.json` 편집 | H2가 무효가 되거나 재생이 멈춥니다 | `paper_live/config.py:209-211`, `paper_live/replay.py:142-146`, `paper_live/verdict.py:134-137, 168-171` |
| N7 | 태그 클론에서 `paper_live.calibrate`, `grid`, `sameday`, `run_live`, `power` 실행 | `calibrate`는 재생이 읽는 모델 파일을 덮어씁니다. 나머지는 판독 절차 밖입니다 | `paper_live/calibrate.py:107-109`, `paper_live/replay.py:152-154`, 분리 스펙 `:95-96` |
| N8 | 화면의 날짜별 손익을 보고 멈추거나, 날짜 줄을 본 뒤 다시 돌리기(같은 날이든 다른 날이든) | 표본을 결과에 맞춰 고르는 것이 됩니다. 다른 UTC 날짜는 새 스냅샷입니다. WARNING 실행은 스냅샷이 저장되지 않아 같은 날 다시 돌려도 새로 받습니다 | `paper_live/config.py:205-206, 219-220`, `paper_live/replay.py:147, 197`, `paper_live/engine.py:181-186` |
| N9 | Step 7A 블록, 파일럿, 테스트 스위트, 앱과 동시 실행 | 파일럿과 판독: 문서 규칙. Step 7A 동안: 런북 규칙. 스위트와 판독: T-HERM-02가 홈 폴더 파일 목록을 비교하므로 피한다는 추정. 앱: 근거 없는 제안 | Nautilus 스펙 `:193-196`, `fe37e82:docs/nautilus_bridge/RUNBOOK_windows.md:32, 221`, `tests/macro_acceptance.py:113-138` |
| N10 | Step 7A~10 동안 메인 클론에서 `python tests/run_all.py --suite guard` | `--suite`도 `qa/acceptance_results.json`을 덮어써 작업 트리를 더럽힙니다. Step 7A 소유자 모드는 깨끗한 트리를 요구하고, 이 파일은 소유자 Windows 전체 실행에서만 커밋합니다 | `tests/run_all.py:54, 136-137`, `fe37e82:docs/nautilus_bridge/RUNBOOK_windows.md:22`, Nautilus 스펙 `:1580` |
| N11 | Nautilus 전용 인터프리터(`%LOCALAPPDATA%\quantgen\py313`, `ntvenv`)로 판독 | `py313`은 방화벽 규칙이 바깥 연결을 막습니다. 고정 버전은 전역 인터프리터 기준입니다 | `fe37e82:docs/nautilus_bridge/handoff/win_amd64.json:33-39`, 분리 스펙 `:92-94` |
| N12 | 판독 산출물을 연구 브랜치에 커밋 | Step 10 완료 조건은 7A.5 HEAD 이후 `paper_live/` 변경이 없어야 합니다 | Nautilus 스펙 `:1580` |
| N13 | 동결 기간에 main 병합 | 7A.3 커밋까지 main 병합 동결. 어느 커밋이 동결을 끝내는지는 D-12 | `docs/nautilus_bridge/OWNER_RULINGS_LOG.md:396-399` |
| N14 | `.env`를 태그 클론에 복사, `QUANTGEN_MACRO_DIR` 설정 | 키가 필요 없습니다. 원장 위치가 main과 달라집니다 | `paper_live/engine.py:96-104`, `tag:config.py:275-277` |
| N15 | 판독 뒤 태그 클론 삭제, 산출물 이동·편집 | main에 커밋할 원본입니다 | 분리 스펙 `:99-101` |
| N16 | 태그 클론에서 `python -m grokteam.book` | GROKTEAM의 단 한 번의 look은 2027-02-01 01:00 UTC 이후입니다 | 분리 스펙 `:57, 97-98` |
| N17 | 원장 파일(`~\.nextgen\macro\ledgers\*.jsonl`)을 열어 편집 | 한 글자만 바뀌어도 체인이 영구히 깨집니다 | `core/quant/gate_ledger.py:284-309` |
| N18 | D-7 결정 전에 결과 수치나 기록 파일을 Claude 대화에 붙여 넣기 | Claude는 홀드아웃 산출물을 읽지 않는 규칙으로 일합니다 | 이 문서 5.4(제안) |

## 5. 점검과 보고

### 5.1 실행 전 점검 (요약)

| 점검 | 어디서 | 기대 |
|---|---|---|
| 동시 실행 없음 | 3.1 | Step 7A 블록, 파일럿, 스위트, 앱 모두 멈춤 |
| 태그 클론 정체 | 3.3 | HEAD `eacd57d…`, 태그 객체 `6e7c1f7…`, 깨끗함, `.git` 폴더 |
| 동결 사본 | 3.3 | 6줄 모두 `OK` |
| 읽을 파일 | 3.3 | 6개 `True`, `replay_holdout` 2개 `False` |
| 인터프리터 | 3.4 | `sys.executable`이 7A 기록과 같음(또는 D-2 (i)의 venv), 3.13.x, 2.3.5, 1.18.0, 2.3.3 |
| 홀드아웃 세션 | 3.5 | 두 프로필 모두 10-21~11-03 |
| 시각 | 3.0 | KST 09:30 이후 시작, 같은 UTC 날짜 안에 끝 |

- 선택 사항(소유자만): `frozen_guard`를 메인 클론에서 돌리고 싶으면 `tests/run_all.py`가 아닌 아래 형태로 돌립니다. 작업 트리에는 파일을 쓰지 않습니다(`-B`는 `.pyc`도 쓰지 않습니다). 다만 (d)의 두 번째 검사가 임시 폴더(`%TEMP%`)에 파일을 잠깐 쓰고 지웁니다(`tests/frozen_guard.py:94-105`). 5줄이 모두 `PASS`여야 합니다. Step 7A 블록이 돌지 않을 때만 합니다. Claude 세션은 이 검사를 돌리지 않습니다(머리말의 사고).

```powershell
cd "$env:USERPROFILE\OneDrive\Desktop\QUANTGEN"
python -B -c "import tests.frozen_guard as g; [print('PASS', n) for n, f in g.tests() if f() is None]"
```

- 실패하면 그 줄에서 `AssertionError`가 나고 멈춥니다. 조항 (d)는 전역 인터프리터의 버전을 봅니다(`tests/frozen_guard.py:85-91`).

### 5.2 실행 후 점검 (태그 클론에서)

1. 바뀐 파일이 `paper_live/out/`과 `paper_live/out_krx/` 아래뿐인지 봅니다.

```powershell
git status --porcelain --untracked-files=all
```

- 기대: 모든 경로가 `paper_live/out/` 또는 `paper_live/out_krx/`로 시작합니다. 예상 경로는 `data/holdout_5m_60d_<날짜>.csv.gz`, `data/MANIFEST.json`, `replay_holdout/{days.csv,summary.json,trades.jsonl,fills.jsonl}`, `verdict.json`입니다(`paper_live/engine.py:137-152`, `paper_live/replay.py:199-203, 229`, `paper_live/verdict.py:174`). 어느 것이 `M`이고 어느 것이 `??`인지는 태그에 무엇이 추적돼 있는지에 달려 UNVERIFIED입니다.
- 다른 경로가 있으면 경로만 보고합니다.

2. 규칙 파일이 그대로인지 3.3의 sha256 블록을 다시 돌립니다. 6줄 모두 `OK`여야 합니다.

3. 원장에 새 행이 생겼는지는 보통 확인하지 않아도 됩니다.
   - 재생은 6개 계정을 `QG-TACTICAL`, `QG-CORE`, `LAZYOWEN` 원장에 등록합니다(`paper_live/replay.py:172`, `paper_live/engine.py:69, 106-112`, `tests/paper_live_acceptance.py:240-243`).
   - 같은 설정이 이미 있으면 아무것도 덧붙이지 않습니다(`core/quant/gate_ledger.py:60-61, 342-346`). 이전 재생이 같은 설정을 등록했을 것이므로 새 행은 0개로 예상합니다(UNVERIFIED).
   - 행이 생기면 그 행의 `run_utc_anchor`는 `git:eacd57d…`입니다(분리 스펙 `:88, 101`).

### 5.3 보관

- 태그 클론은 산출물을 main에 커밋할 때까지 지우지 않습니다(N15).
- 해시를 기록합니다. 나중에 커밋한 파일이 같은 바이트인지 확인하는 데 씁니다.

```powershell
Get-ChildItem paper_live\out\replay_holdout, paper_live\out_krx\replay_holdout -File | Get-FileHash -Algorithm SHA256 | Format-Table Hash, Path -AutoSize
Get-FileHash -Algorithm SHA256 paper_live\out\verdict.json, paper_live\out_krx\verdict.json, paper_live\out\data\MANIFEST.json, paper_live\out_krx\data\MANIFEST.json | Format-Table Hash, Path -AutoSize
Get-ChildItem paper_live\out\data\holdout_5m_60d_*.csv.gz, paper_live\out_krx\data\holdout_5m_60d_*.csv.gz | Get-FileHash -Algorithm SHA256 | Format-Table Hash, Path -AutoSize
```

- 제안: 위 파일들의 사본을 OneDrive 밖 다른 곳(외장 디스크 등)에도 둡니다. 원본을 옮기지는 않습니다.

### 5.4 Claude에게 보고하는 법 (개인정보와 결과 보호)

- **제안(D-7):** 기본 보고에는 유효성 항목만 넣습니다. H2가 확인됐는지, 평균 차이, t, p 같은 결과는 넣지 않습니다.
  - 이유 1: 이번 작업에서 Claude는 판독을 돌리지 않고 홀드아웃 산출물을 읽지 않는 규칙으로 일합니다.
  - 이유 2: Phase 2의 선행 조건은 "모든 예정 세션, 동결 다이제스트 일치, 보관된 증거"이지 결과의 방향이 아닙니다(분리 스펙 `:369-373`). Claude의 다음 일(⑧-4 스펙)에는 유효성 항목과 증거 보관이 필요합니다. 그래서 ⑧-4는 이 보고만으로 시작하지 않고 D-5의 산출물 커밋도 기다립니다(1.4).
  - 결과는 산출물이 main에 커밋되면 공개됩니다(6.7). 그 전에 Claude에게 보낼지는 소유자가 정합니다.
- 기록 파일(`h2_readout_transcript_*.txt`)에는 날짜별 손익과 판정 줄이 들어 있습니다. D-7 결정 전에는 붙여 넣지 않습니다.
- 기록 파일의 머리말에는 보통 사용자 이름, 컴퓨터 이름, 호스트 프로그램, 프로세스 번호가 들어갑니다(소유자 PC의 PowerShell 버전에서는 UNVERIFIED). Nautilus 설계는 컴퓨터 이름을 해시로만 공개합니다(Nautilus 스펙 `:1154`, `host_fingerprint`). 그래서 이 파일을 그대로 공개 저장소에 커밋하지 않습니다. 어떤 판독 기록을 커밋할지는 D-11입니다.
- 유효성 항목만 뽑는 명령입니다. `confirmed`와 `not confirmed`는 모두 `final`로 바꿔 보여 줍니다.

```powershell
foreach ($d in "paper_live\out", "paper_live\out_krx") {
  $v = Get-Content "$d\verdict.json" -Raw | ConvertFrom-Json
  $s = Get-Content "$d\replay_holdout\summary.json" -Raw | ConvertFrom-Json
  $m = (Get-Content "$d\data\MANIFEST.json" -Raw | ConvertFrom-Json).($s.snapshot)
  $st = $v.H2.status
  if (@("confirmed", "not confirmed") -contains $st) { $st = "final" }
  [pscustomobject]@{
    folder = $d; profile = $v.profile; h2_state = $st
    sessions = $v.H2.sessions; planned = $v.H2.planned; missing = ($v.H2.missing -join ",")
    days = ($v.H2.days -join ".."); snapshot = $s.snapshot; holdout = $s.holdout
    n_days = $s.n_days; replay_first = $s.first; replay_last = $s.last; seconds = $s.seconds; config_sha = $s.sha
    digest_naive = $s.rule_digest."LAZYOWEN-NAIVE"; digest_g2 = $s.rule_digest."LAZYOWEN-NAIVE-G2"
    manifest_sha256 = $m.sha256; saved_utc = $m.saved_utc; bars_first = $m.first; bars_last = $m.last
    rows = $m.rows; tickers = @($m.tickers).Count
  } | Format-List
}
```

- 이 명령이 읽는 필드는 모두 결과가 아닌 과정 정보입니다(`paper_live/verdict.py:129-132, 142-144`, `paper_live/replay.py:204-207`, `paper_live/engine.py:141-147`).
- `missing`이 비어 있지 않거나 `h2_state`가 `final`이 아니면 그 값을 그대로 보냅니다. 그것은 결과가 아니라 실패의 이유입니다.

보고 양식:

```
[⑧-1 H2 판독 보고 - 유효성만]
실행 시각(KST 시작~끝):
태그 클론: 경로=  HEAD=  태그 객체=  실행 전 git status 깨끗함(예/아니요)
인터프리터: 경로=  python=  numpy=  scipy=  pandas=  yfinance=  nautilus_trader importable(True/False)
3.3 sha256 6줄: 모두 OK(예/아니요)   3.5 세션 두 줄: 기대와 같음(예/아니요)
base: 재생 정상 끝(예/아니요)  WARNING 줄(있음/없음, 있으면 Ctrl+C가 날짜 줄 전/후)  재시도 횟수  + 5.4 명령 출력
krx:  재생 정상 끝(예/아니요)  WARNING 줄(있음/없음, 있으면 Ctrl+C가 날짜 줄 전/후)  재시도 횟수  + 5.4 명령 출력
실행 후 git status: 경로 목록만
5.3 해시 표: 붙여 넣기
멈춘 경우: 오류 줄 원문(손익 숫자 줄은 빼고)
```

## 6. 현재 상태와의 관계

### 6.1 main 병합 동결 (Step 7A.3까지)

- 시작점은 `bb35b3b`(PR #69 병합)입니다. 7A.3 커밋이 `claude/amazing-gauss-tdiguu`에 들어갈 때까지 main에는 아무것도 병합하지 않습니다(`docs/nautilus_bridge/OWNER_RULINGS_LOG.md:387, 396-399`).
- "7A.3 커밋"은 두 가지로 읽힙니다. 7A.3 3단계에서 소유자는 결과와 상관없이 인계 보고서를 커밋하고, 모든 줄이 통과했을 때만 기준선·이그레스 기록·두 표·`qa/acceptance_results.json`을 한 변경 묶음으로 커밋합니다(Nautilus 스펙 `:1544-1551`). `fe37e82`는 앞의 것입니다. 실패가 기록된 인계 보고서 한 파일만 바꿉니다(`git show --stat fe37e82`).
  - 이 문서는 동결이 **모든 줄이 통과한 뒤의 7A.3 변경 묶음**으로 끝난다고 읽습니다. `fe37e82`는 동결을 끝내지 않았다고 봅니다.
  - 이 읽기는 소유자와 Step 7A 세션이 D-5 (가)의 일정을 잡기 전에 확인합니다(D-12).
- 판독 자체는 main을 바꾸지 않습니다. 태그 클론 안에서만 파일이 생깁니다. 그래서 **판독은 동결과 상관없이 지금 할 수 있습니다.**
- 산출물을 main에 넣는 일만 동결이 풀린 뒤로 미룹니다(6.7, D-5).

### 6.2 메인 클론이 연구 브랜치에 있음 (Step 7A~10)

- 메인 클론은 7A.2 첫 블록에서 `claude/amazing-gauss-tdiguu`로 바뀌었고 Step 10 병합 뒤까지 그대로입니다(`fe37e82:docs/nautilus_bridge/RUNBOOK_windows.md:85-88, 211-221`). 7A 인계 보고서의 HEAD는 `0bc9595`입니다(`fe37e82:docs/nautilus_bridge/handoff/win_amd64.json:71-76`).
- 런북은 이 기간의 판독을 "기다리거나, 별도 클론에서, 파일럿 중이 아닐 때" 하라고 적습니다(`fe37e82:docs/nautilus_bridge/RUNBOOK_windows.md:221`). 이 문서의 절차가 그 "별도 클론"입니다.
- 태그 클론을 만들 때 메인 클론의 `.git`에서 객체를 읽기만 합니다. 작업 트리와 브랜치는 그대로이므로 Step 7A의 깨끗한 트리 조건에 영향이 없습니다(`fe37e82:docs/nautilus_bridge/RUNBOOK_windows.md:22`).

### 6.3 Step 7A·파일럿과의 동시 실행

- 문서 규칙:
  - 파일럿은 동결 연구 판독 중에 돌지 않습니다(GOVERNANCE-9, Nautilus 스펙 `:196`). 파일럿과 스위트도 겹치지 않습니다(`:193-195`).
  - Step 7A 동안에는 스위트, 동결 연구 판독, 파일럿이 돌지 않습니다(`fe37e82:docs/nautilus_bridge/RUNBOOK_windows.md:32`). 이 문서는 이것을 "7A 줄이 도는 동안"으로 읽습니다. 같은 런북이 Step 10까지 "별도 클론에서, 파일럿 중이 아닐 때"의 판독을 허용하기 때문입니다(`:221`). 이 읽기는 D-10에서 확인합니다.
  - 스위트가 도는 동안 앱은 돌지 않습니다(분리 스펙 `:143-144`). 이 줄은 판독을 말하지 않습니다.
- 추정: 스위트가 도는 동안 판독도 돌리지 않습니다. 근거는 아래의 T-HERM-02입니다.
- 겹치는 자원은 `~/.nextgen/macro/ledgers`입니다.
  - 판독은 `QG-TACTICAL`, `QG-CORE`, `LAZYOWEN` 원장과 그 `.lock` 파일을 엽니다(`core/quant/gate_ledger.py:243-262, 342`).
  - 스위트의 T-HERM-02는 `~/.nextgen/macro` 아래 모든 파일의 크기와 수정 시각을 전후로 비교합니다(`tests/macro_acceptance.py:113-138`). 판독이 `.lock` 파일을 새로 만들면 스위트가 실패할 수 있습니다.
- **Step 7A 세션 참고(기록만, 이 문서는 바꾸지 않음):** Nautilus 스펙 3.8은 "the H2 readout registers rows into C3 (`paper_live/replay.py:172`)"라고 적습니다(Nautilus 스펙 `:196-197`).
  - 코드상 재생은 `C.ACCOUNTS`만 등록하고, 여기에는 `trend` 규칙 계정이 없습니다(`paper_live/config.py:170-177`, `paper_live/engine.py:69`). C3 행은 `paper_live/grid.py:130`이 씁니다.
  - 그래서 러너의 R-16 검사(`C3.jsonl` 또는 해당 원장이 600초 안에 바뀌었으면 거부)는 H2 판독을 감지하지 못합니다. 새 행이 없으면 어떤 원장 파일도 바뀌지 않습니다.
  - 결론: 동시 실행 방지는 **소유자의 일정 관리**에 달려 있습니다. 3.1의 Step 7A 세션 알림이 그 장치입니다.

### 6.4 핫스팟 메모

- Step 7A의 3-8~3-13과 파일럿은 1.1.1.1:443에 닿는 네트워크(휴대폰 핫스팟)에서 돌립니다. 집 네트워크는 1.1.1.1:443만 막혀 있습니다(`fe37e82:docs/nautilus_bridge/OWNER_RULINGS_LOG.md:677-679`, `fe37e82:docs/nautilus_bridge/RUNBOOK_windows.md:145-149, 208-209`).
- H2 판독의 바깥 연결은 yfinance의 Yahoo 요청뿐입니다(`paper_live/engine.py:176-179`). 1.1.1.1을 쓰지 않습니다.
- 방화벽 규칙 `QUANTGEN-nautilus-block-out`은 `%LOCALAPPDATA%\quantgen\py313\python.exe`에만 걸려 있습니다(`fe37e82:docs/nautilus_bridge/handoff/win_amd64.json:33-39`). 전역 Python은 막지 않습니다.
- 그래서 **핫스팟은 H2와 무관합니다.** 집 네트워크에서 Yahoo에 닿는지는 UNVERIFIED입니다. QUANTGEN 앱이 같은 네트워크에서 yfinance를 써 왔다면 문제없을 것으로 봅니다.

### 6.5 전역 Python의 `nautilus_trader` (중요)

- 7A 인계 보고서(2026-11-04 01:57 UTC)는 전역 Python에 `nautilus-trader` 2.0.0rc7 배포판이 있다고 기록합니다(`fe37e82:docs/nautilus_bridge/handoff/win_amd64.json:96-103`). 이 값은 전역 인터프리터의 배포판 정보를 읽은 것입니다(`fe37e82:tools/nautilus/launch.py:237-242`).
- 규칙은 전역 Python에 설치하지 말라는 것입니다. 이유는 `frozen_guard` (d)가 numpy 2.3.5, scipy 1.18.0, pandas 2.3.3을 고정하기 때문입니다(`fe37e82:requirements-nautilus.txt:2-3`). `tests/nautilus_acceptance.py`의 L1-22도 이 상태에서 실패하고, 처방 세 줄(`pip uninstall -y nautilus-trader`, `pip check`, 버전 출력)을 냅니다(`fe37e82:tests/nautilus_acceptance.py:505-516`).
- H2에 대한 뜻: 설치 과정에서 numpy·scipy·pandas가 바뀌었다면 전역 Python으로는 판독할 수 없습니다. 분리 스펙은 그때 고정 버전 전용 venv로 판독하라고 이미 적습니다(`:92-94`). 바뀌었는지는 UNVERIFIED입니다. 3.4의 두 번째 줄이 답입니다.
- 버전이 그대로면 H2는 진행할 수 있습니다. `nautilus_trader` 제거는 Step 7A 세션의 일입니다.
- 버전이 바뀌었으면 D-2입니다. GROKTEAM look(2027-02-01 이후)도 같은 고정 버전이 필요합니다(`tests/frozen_guard.py:55-63, 85-91`). Step 7A 완료와 Step 10 완료도 (d) 통과를 요구합니다(Nautilus 스펙 `:1574, 1580`).
- (d)는 guard를 돌리는 인터프리터를 봅니다(`tests/frozen_guard.py:85-91`). 전용 venv로 판독해도 전역 인터프리터의 (d) 실패는 그대로 남습니다.

### 6.6 휴대폰 알림 (분리 스펙 5A)

- `h2-holdout-ready-alert`: 2026-11-04 09:00 KST 1회. 두 `out*/verdict.json`을 읽기만 하고 알림을 보냅니다(분리 스펙 `:626-632`). 오늘 왔는지는 UNVERIFIED입니다.
- `h2-readout-deadline-warning`: 2026-12-05 09:00 KST 1회. H2가 아직 pending이면 알립니다(분리 스펙 `:633-635`).
  - 이 알림은 메인 클론의 `verdict.json`을 볼 것으로 보입니다(UNVERIFIED, 작업 정의를 보지 않았습니다). 태그 클론에서 판독을 끝내도 main에 커밋하기 전에는 pending으로 남아 잘못 울릴 수 있습니다(D-9).
  - 반대로 판독을 아직 안 했다면 12-05는 코드상 마지막 날보다 1주쯤 앞설 뿐입니다. 요청 시각부터 센 60일이면 12-12(토)까지 통과하고, 12-13(일)은 시각에 따라 실패할 수 있고, 마지막 평일은 12-11(금)입니다(2.3).
- 알림은 Claude 앱이 열려 있을 때만 제때 돕니다(분리 스펙 `:637-640`).

### 6.7 산출물을 main에 넣는 시점 (D-5)

- 분리 스펙: 판독 산출물은 main에 복사해 커밋합니다. 대상은 `out*/replay_holdout`, `verdict.json`, 판독 기록입니다(분리 스펙 `:99-101`). 판독 기록으로 무엇을 커밋할지는 D-11입니다(5.4의 기록 파일 머리말 문제).
- 지금은 두 가지가 막습니다.
  - main 병합 동결(6.1).
  - 메인 클론이 연구 브랜치에 있습니다. 연구 브랜치에 커밋하면 Step 10 완료 조건을 깨뜨립니다(N12).
- 아래 선택지 (가)도 연구 브랜치를 묶습니다.
  - Step 10 완료 조건: 7A.5 HEAD 대비 `git diff --name-only`에 `paper_live/` 아래 경로가 없어야 합니다(Nautilus 스펙 `:1560-1561, 1580`).
  - H2 산출물이 main에 들어간 뒤 7A.5 HEAD와 Step 10 사이에 main을 연구 브랜치에 합치면 `paper_live/out*/` 경로가 그 diff에 들어가 Step 10이 실패합니다.
  - Step 7A 세션은 main을 연구 브랜치에 합쳐 왔습니다(`docs/nautilus_bridge/OWNER_RULINGS_LOG.md:412-413`, 커밋 `c95b3aa`).
  - 7A.1과 7A.2는 `origin/main`이 연구 브랜치의 조상이 아니면 멈추고 main 병합을 요구합니다. 재진입에는 새 승인 문장도 들어갑니다(`fe37e82:docs/nautilus_bridge/RUNBOOK_windows.md:41-42, 57, 85`). 7A 인계 보고서는 fixtures와 guard 부분이 실패했다고 적으므로(`fe37e82:docs/nautilus_bridge/handoff/win_amd64.json:66-68, 91-93`, "no venv python") 7A.2 재진입 가능성이 높습니다. (가)가 재진입보다 먼저 main에 들어가면 재진입이 main 병합을 강제합니다. 그 병합이 7A.5 HEAD보다 앞서면 Step 10 diff에는 들어가지 않지만, 연구 브랜치에 `paper_live/out*/` 변경이 들어갑니다.
- 선택지:

| 선택지 | 방법 | 장점 | 단점 |
|---|---|---|---|
| (가) 제안 | 동결이 풀린 뒤(D-12) GitHub `main`에서 세 번째 폴더를 클론하고 새 브랜치에 산출물을 복사해 커밋·push, PR, CI 뒤 병합. **전제:** H2 산출물이 main에 들어간 뒤에는 7A.5 HEAD와 Step 10 병합 사이에 main을 연구 브랜치에 합치지 않습니다. 또는 (가)를 7A.5 HEAD 전이나 Step 10 병합 뒤에만 넣습니다 | 메인 클론의 작업 트리와 브랜치를 건드리지 않습니다. 몇 주 안에 main에 들어갈 수 있어 ⑧-4의 증거 조건을 일찍 채웁니다 | 폴더가 하나 더 생깁니다. 위 전제가 연구 브랜치의 main 병합 시점을 묶습니다. 7A.2 재진입 전에 넣으면 재진입이 main 병합을 강제합니다 |
| (나) | Step 10 병합 뒤 메인 클론이 `main`으로 돌아오면 그때 커밋 | 폴더가 늘지 않습니다. 연구 브랜치와 엮이지 않습니다 | 수 주 늦어집니다. 그동안 태그 클론을 지켜야 하고 12-05 알림이 잘못 울립니다. ⑧-4도 그만큼 늦어집니다(1.4) |
| (다) | Claude가 커밋 | — | 지금 규칙으로는 불가. Claude는 `paper_live/out*/`를 읽거나 복사하지 않습니다 |

- (가)의 시점은 소유자가 Step 7A 세션과 함께 정합니다(D-5).

- 어느 쪽이든 복사는 H2 산출물만 합니다. `out*/` 폴더 전체를 덮어쓰지 않습니다. main의 `out*/data/MANIFEST.json`이 태그와 다를 수 있으므로 행을 합쳐야 할 수 있습니다(UNVERIFIED). 이 작업은 그때 따로 안내합니다.
- Yahoo 5분봉 스냅샷(`holdout_5m_60d_*.csv.gz`)을 공개 저장소에 넣을지는 D-6입니다.

### 6.8 다른 로드맵 항목과의 관계

| 항목 | 관계 | 근거 |
|---|---|---|
| ⑧-4 분리 스펙 Phase 2 | ⑧-1이 두 프로필 모두 유효하게 끝나고, 증거가 보관돼야 시작합니다. 산출물의 D-5 커밋(또는 D-6에서 소유자가 인정한 비공개 보관)을 기다립니다 | `docs/nautilus_bridge/REMAINING_WORK_2026-10-27.md:136`, 분리 스펙 `:99-101, 369-373` |
| ⑧-2 잠금 홀드아웃 | 2027-01-01 이후 데이터 규칙. H2 데이터는 그 전이라 해당하지 않습니다 | `docs/nautilus_bridge/REMAINING_WORK_2026-10-27.md:122` |
| ⑧-3 GROKTEAM look | 같은 태그를 쓰지만 별도 실행입니다. 같은 태그 클론을 써도 되는지는 그때 정합니다 | `docs/nautilus_bridge/REMAINING_WORK_2026-10-27.md:119` |
| ⑤-1 Step 7A, ⑥ 파일럿 | 동시 실행 금지(6.3). (가) 커밋은 연구 브랜치의 main 병합 시점을 묶습니다(6.7) | Nautilus 스펙 `:193-196, 1580`, `fe37e82:docs/nautilus_bridge/RUNBOOK_windows.md:32, 221` |

## 7. 소유자 체크리스트

- [ ] 8절 결정 가운데 D-1(시점), D-3(위치), D-4(재실행 규칙), D-7(보고 범위), D-10(실행 창)을 먼저 정했다.
- [ ] KST 09:30 이후, Step 7A 블록·파일럿·스위트·앱이 모두 멈춘 때에 시작했다. Step 7A 세션에 알렸다.
- [ ] `git clone --branch studies-of-record-2026-10-23 ... QUANTGEN-studies`로 새 폴더를 만들었다(worktree 아님).
- [ ] 3.3: HEAD `eacd57d…`, 태그 객체 `6e7c1f7…`, `tag`, 깨끗함, `.git` 폴더, `* -text`.
- [ ] 3.3: sha256 6줄 모두 `OK`. 읽을 파일 6개 `True`, `replay_holdout` 2개 `False`.
- [ ] 3.4: `sys.executable`이 7A 기록과 같음. `3.13.x 2.3.5 1.18.0 2.3.3`(다르면 D-2). 환경 변수 네 칸 비어 있음. Nautilus 인터프리터가 아님.
- [ ] 3.5: 두 프로필 모두 10-21~11-03, 10세션.
- [ ] 3.6 base: 재생 정상 끝, WARNING 없음(있었으면 날짜 줄 전에 Ctrl+C), 판정 실행. 화면 결과를 보고 멈추거나 다시 돌리지 않았다.
- [ ] 3.7 krx: 같음. `Stop-Transcript`.
- [ ] 5.2: `git status`가 `paper_live/out*/` 아래 경로뿐. sha256 6줄 다시 `OK`.
- [ ] 5.3: 해시 표 저장. 태그 클론은 지우지 않았다.
- [ ] 5.4: 유효성 보고 양식만 Claude에게 보냈다. Step 7A 세션에 "H2 판독 끝"을 알렸다.

## 8. 열린 질문과 소유자 결정

| # | 질문 | 왜 중요한가 | Claude 제안 | 소유자가 정할 것 |
|---|---|---|---|---|
| D-1 | 언제 실행하나 | Yahoo가 60일을 요청 시각부터 센다면 12-13(일) 요청부터 시각에 따라 실패할 수 있고 12-14(월)부터는 반드시 실패합니다. 마지막 평일은 12-11(금)입니다(2.3, Yahoo 경계 UNVERIFIED). 늦을수록 홀드아웃 밖 세션을 더 봅니다 | 이번 주. 내부 기한 2026-11-30 | 실행 날짜와 내부 기한 |
| D-2 | 3.4에서 numpy·scipy·pandas가 고정값과 다르면 | 고정 버전 없이는 판독할 수 없습니다. 분리 스펙은 그때 고정 버전 전용 venv로 판독하라고 이미 적습니다(`:92-94`). (d) 조항 고쳐 쓰기는 전역 인터프리터가 "움직여야 할 때"만 허용됩니다(`:116-119`). 규칙을 어긴 설치(`fe37e82:requirements-nautilus.txt:2-3`)는 필요한 이동이 아니고, 처방은 복구입니다(`fe37e82:tests/nautilus_acceptance.py:510-515`). 동결 중에는 guard 수정이 main에 들어갈 수도 없고, Step 7A와 Step 10은 (d) 통과가 필요합니다(Nautilus 스펙 `:1574, 1580`) | 세 결정으로 나눕니다. (i) 판독: 지금, 고정 버전 전용 venv에서 합니다. guard는 고치지 않습니다. (ii) 전역 인터프리터 복구: L1-22 처방으로, Step 7A 세션과 함께 합니다. 처방은 `nautilus-trader`를 지우고 버전을 출력할 뿐이라, 버전이 돌아오지 않으면 고정 버전을 다시 설치해야 합니다(절차 UNVERIFIED). (iii) (d) 조항 고쳐 쓰기: 소유자가 전역 인터프리터를 움직여야 한다고 판정할 때만, 동결이 끝난 뒤에만 | (i) 전용 venv 판독 승인(승인하면 Claude가 venv 절차를 따로 씁니다). (ii) 복구 시점. (iii) 전역 인터프리터를 움직일지 |
| D-3 | 태그 클론 위치 | OneDrive 동기화가 실행 중 파일을 잠그거나 올릴 수 있습니다(UNVERIFIED) | `C:\Users\whydi\QUANTGEN-studies`(OneDrive 밖) | 위치 |
| D-4 | 재실행 규칙을 미리 정해 두기 | 결과를 본 뒤 정하면 표본 선택이 됩니다(`paper_live/config.py:219-220`) | ① `WARNING: Yahoo returned no bars` 줄이 나오면 바로 Ctrl+C를 누릅니다. 날짜 줄이 하나도 나오기 전에 멈춘 실행에 한해, 같은 UTC 날짜 안에서 재생만 최대 2번 더 합니다. WARNING 없이 저장된 첫 스냅샷의 결과를 씁니다. 3번 모두 WARNING이면 멈추고 보고합니다. 날짜 줄이 이미 나왔으면 그 실행은 본 것으로 칩니다. 다시 돌리지 않고 멈추고 보고합니다(경고 뒤에도 재생은 결과를 찍습니다, `paper_live/engine.py:183-186`, `paper_live/replay.py:148-230`). 6일 조건 거부와 원장 오류는 같은 UTC 날짜에 다시 돌리지 않습니다. 저장된 스냅샷을 다시 읽어 같은 결과가 나옵니다(`paper_live/engine.py:170-175, 181-182`). `REPLAY_LAST` 거부는 데이터를 받기 전이라 변수를 지운 뒤 다시 돌려도 됩니다(`paper_live/replay.py:136-137`). ② 판정이 `pending`/`incomplete`/`invalid`이면 멈추고 보고합니다. 다른 날 다시 받는 것은 그때 소유자가 따로 판정합니다. ③ 정상 판정 뒤에는 다시 돌리지 않습니다 | 이 규칙을 승인하거나 고칠 것. 승인 문장은 `OWNER_RULINGS_LOG.md`에 원문으로 남깁니다 |
| D-5 | 산출물을 언제 어디에 커밋하나 | 동결 중이고 연구 브랜치는 쓸 수 없습니다. ⑧-4가 이 커밋을 기다립니다. (가)도 연구 브랜치의 main 병합 시점을 묶습니다(6.7) | (가) 동결 해제(D-12) 뒤 세 번째 클론에서 PR. 전제: H2 산출물이 main에 들어간 뒤 7A.5 HEAD와 Step 10 병합 사이에 main을 연구 브랜치에 합치지 않습니다. 또는 7A.5 HEAD 전이나 Step 10 병합 뒤에만 넣습니다. 7A.2 재진입 전에 넣으면 재진입이 main 병합을 강제합니다 | (가), (나) 중 선택. (가)라면 시점을 Step 7A 세션과 함께 정할 것 |
| D-6 | Yahoo 5분봉 스냅샷을 공개 저장소에 커밋하나 | 데이터 재배포 라이선스 문제(⑩-1). 커밋하지 않으면 재현은 해시로만 확인합니다. Phase 2 선행 조건에는 "보관된 증거"가 들어 있습니다(분리 스펙 `:370-371`) | 스냅샷 파일은 비공개로 보관하고, `MANIFEST.json` 행(sha256, 첫·끝 시각, 행 수)만 커밋합니다. 증거 기록은 두 가지입니다. 비공개 보관 위치(태그 클론의 `paper_live\out*\data\` 원본과 5.3의 OneDrive 밖 사본, 소유자가 경로를 정함)와, 커밋한 `MANIFEST.json`의 스냅샷 sha256입니다 | 커밋 여부. 비공개 보관 위치. 이 보관이 "archived evidence"를 채우는지 |
| D-7 | Claude에게 어디까지 보내나 | Claude는 이번 작업에서 홀드아웃 산출물을 읽지 않습니다. 다음 일(⑧-4)에는 유효성과 증거 보관이 필요하고 결과의 방향은 필요 없습니다 | 유효성만(5.4). 결과는 main 커밋 때 공개 | 유효성만 또는 결과 포함 |
| D-8 | 3.3에서 `HYPOTHESES_frozen.json`, `model_train_only.json`, `calibration.json` 중 하나가 태그에 없으면 | 재생이 그 파일을 읽습니다(`paper_live/replay.py:138-141, 152-154`). 메인 클론의 사본은 태그 뒤에 바뀌었을 수 있습니다 | 멈추고 보고. Claude가 git 기록으로 원본을 찾는 방법을 제안한 뒤 소유자가 판정 | 그때 판정 |
| D-9 | 12-05 경고 알림 | 판독 뒤에도 main 커밋 전에는 잘못 울릴 수 있고, 판독 전이라면 너무 늦을 수 있습니다(6.6) | 판독을 끝내면 끕니다. 판독이 늦어지면 11-25쯤으로 당긴 알림을 하나 더 둡니다 | 끄기·당기기 여부 |
| D-10 | Step 7A 일정과의 조율 | 판독과 7A 블록·파일럿은 겹치면 안 됩니다(6.3). R-16은 판독을 감지하지 못합니다. 런북 `:32`의 "meanwhile"을 Step 7A 기간 전체로 읽으면 7A가 끝날 때까지 판독을 못 하고, 기한(2.3)에 걸릴 수 있습니다 | 런북 `:32`를 "7A 줄이 도는 동안"으로 읽습니다(런북 `:221`, Nautilus 스펙 3.8). 다음 7A 블록이나 파일럿 전에 판독을 먼저 끝냅니다 | 실행 창. 런북 `:32`의 읽기를 Step 7A 세션과 확인 |
| D-11 | 어떤 판독 기록을 main에 커밋하나 | 분리 스펙은 "the readouts"를 커밋한다고만 적습니다(`:99-101`). 기록 파일 머리말에 컴퓨터 이름이 들어갈 수 있습니다(5.4, UNVERIFIED). Nautilus 설계는 컴퓨터 이름을 해시로만 공개합니다(Nautilus 스펙 `:1154`) | 기록 파일은 비공개로 둡니다. 대신 짧은 기록 파일을 새로 만듭니다. 내용은 5.4 명령의 출력, 판정의 `H2 cost gate (...)` 줄 원문, yfinance 버전, 시작·끝 시각입니다. 날짜별 손익 줄은 `days.csv`에 이미 있으므로 넣지 않습니다. 컴퓨터 이름은 넣지 않습니다 | 짧은 기록 파일, 머리말을 지운 기록 파일, 커밋 안 함 중 선택. 파일 이름과 위치 |
| D-12 | main 병합 동결은 어느 커밋으로 끝나나 | 결정 원문은 "7A.3 커밋"이라고만 적습니다(`docs/nautilus_bridge/OWNER_RULINGS_LOG.md:387`). 7A.3에는 실패해도 커밋하는 인계 보고서(`fe37e82`)와 모두 통과했을 때의 변경 묶음이 있습니다(Nautilus 스펙 `:1544-1551`). D-5 (가)의 시점이 이것에 달려 있습니다 | 동결은 모든 줄이 통과한 뒤의 7A.3 변경 묶음으로 끝나고, `fe37e82`는 동결을 끝내지 않았다고 읽습니다 | 이 읽기를 승인하거나 고칠 것. Step 7A 세션과 함께 확인 |
| D-13 | 초안 작성 중의 작업 규칙 이탈(머리말) | Claude가 이 세션의 엄격한 작업 규칙이 막은 `paper_live/out*/` 아래 코드 사본 4개를 git으로 읽었습니다(`tests/frozen_guard.py:35, 75-76`). 홀드아웃 결과는 아닙니다. 같은 세션의 Linux 전체 검사도 guard 스위트로 같은 blob을 읽었습니다 | `OWNER_RULINGS_LOG.md`에 공개 기록으로 남깁니다. 그 결과는 이 문서의 근거로 쓰지 않습니다(2.4) | 기록 방법. Claude 세션이 guard 스위트(`frozen_guard` (b) 포함)를 돌려도 되는지 |

UNVERIFIED로 남은 사실 (모두 소유자 PC에서만 확인할 수 있습니다):

| # | 사실 | 확인 방법 |
|---|---|---|
| U-1 | Yahoo "60d" 5분봉의 정확한 시작 경계 (2.3) | 확인하지 않습니다. 빨리 실행하면 무관해집니다 |
| U-2 | 태그에 `model_train_only.json`, `calibration.json`이 있는지 | 3.3 |
| U-3 | 전역 Python의 numpy·scipy·pandas 현재 버전 | 3.4 |
| U-4 | 계산 시간 | 3.0의 `seconds` 참고 |
| U-5 | 원장 체인이 온전하고 새 행이 0개인지 | 재생이 체인을 검사합니다. 새 행 수는 필요할 때 ①-5의 원장 집계 스크립트로 확인합니다 |
| U-6 | 5A 알림 작업이 무엇을 읽는지, 오늘 알림이 왔는지 | 소유자의 Claude 데스크톱 예약 작업 |
| U-7 | 실행 뒤 `git status`에서 어느 파일이 `M`이고 `??`인지 | 5.2 |
| U-8 | 기록 파일 머리말에 컴퓨터 이름 등이 들어가는지 | 기록 파일 첫 몇 줄을 소유자가 봅니다(D-11) |
| U-9 | WARNING 줄과 첫 날짜 줄 사이의 시간 | 3.6. WARNING이 나오면 바로 Ctrl+C로 대비합니다 |

## 9. 근거 목록

### 9.1 문서

| 문서 | 줄 | 내용 |
|---|---|---|
| `docs/nautilus_bridge/REMAINING_WORK_2026-10-27.md` | 118, 119, 122, 136, 160 | ⑧-1, ⑧-3, ⑧-2, ⑧-4, 고정 일정 |
| `docs/nautilus_bridge/ROADMAP_REVIEW_2026-10-27.md` | 34, 55, 149, 152, 166 | 기한, E2, ⑧-1 "5분봉 보존 기간 때문" |
| `docs/nautilus_bridge/OWNER_GUIDE_1-3_1-5_2026-10-27.md` | 57-59, 76-91 | 태그의 역할과 ⑧-1 언급, 태그 확인 명령 |
| `docs/nautilus_bridge/OWNER_RULINGS_LOG.md` | 365-413 | main 병합 동결(시작점 `bb35b3b`, 끝 387·396-399), Step 7A 세션의 main 병합(412-413) |
| `fe37e82:docs/nautilus_bridge/OWNER_RULINGS_LOG.md` | 677-679, 681, 686 | 핫스팟 결정, 메인 클론 경로, P-5 |
| `docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md` | 12-16, 49, 57-66, 73-126, 143-144, 369-376, 622-640, 744-765 | D9, 태그 판독 절차, guard, 동시 실행 금지, Phase 2 선행 조건, 기한, 5A 알림, Appendix C |
| `docs/superpowers/specs/2026-10-23-review/round1_claude.md` | 137 | 12-19 기한(계산 근거 없음, `replay.py:41, 147` 인용) |
| `docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md` | 191-199, 227-230, 1154, 1544-1561, 1574, 1580 | 3.8 동시 실행 금지(193-196), 3.11, `host_fingerprint`, 7A.3 두 커밋, 7A.5 HEAD, Step 7A·10 완료 조건 |
| `fe37e82:docs/nautilus_bridge/RUNBOOK_windows.md` | 7-10, 22, 32, 41-42, 57, 58, 85-88, 145-149, 208-209, 211-221 | 7A 동안 금지 사항, main 조상 검사와 재진입, 연구 브랜치 전환, 핫스팟, "별도 클론" |
| `fe37e82:docs/nautilus_bridge/handoff/win_amd64.json` | 33-39, 66-68, 71-76, 91-93, 96-103 | 방화벽 대상, fixtures·guard 실패, 메인 클론 HEAD, 전역 Python의 `nautilus_trader`와 `sys_executable` |
| 태그 메시지 `studies-of-record-2026-10-23`(`git cat-file -p`) | — | 고정 버전, 동결 시각, 규칙 파일 sha256, "Both out*/frozen_rule copies equal the live files" |
| 커밋 `fe37e82`, `c95b3aa` | `git show --stat` | 인계 보고서 한 파일, main(`bb35b3b`)을 연구 브랜치에 합친 병합 |

### 9.2 코드

| 파일 | 줄 | 내용 |
|---|---|---|
| `paper_live/config.py` | 13-14, 30, 46, 59-71, 170-177, 185-221, 228, 233-235, 244 | 창, base의 LSE·US 종목, 계정, HYPOTHESES, 프로필 |
| `paper_live/verdict.py` | 3-16, 31, 39-65, 68-80, 120-144, 157-184 | 동결(`frozen_rule` 사본 60-63), 홀드아웃 세션, H2 판정, 판정 모듈 |
| `paper_live/replay.py` | 24-27, 41, 124-172, 178-179, 188-207, 227-230 | 홀드아웃 재생, 6일 조건(157, 161-163), 원장 등록, 날짜 줄(197), 출력 |
| `paper_live/engine.py` | 31, 54-56, 63-69, 96-113, 137-152, 166-186 | 출력 폴더, 60일 보존 주석, 원장, 스냅샷 재사용(170-175)·저장(181-182)·WARNING(183-186) |
| `paper_live/calibrate.py` | 107-109 | 모델 파일 덮어쓰기 |
| `paper_live/grid.py` | 130 | C3 행을 쓰는 곳 |
| `core/quant/gate_ledger.py` | 60-61, 122-131, 168-171, 243-262, 284-309, 337-355 | 설정 ID, 앵커, 잠금, 체인, 중복 무시 |
| `tests/frozen_guard.py` | 31-39, 55-63, 72-77, 85-91, 94-105 | 태그 검사, 대기 판독, 버전 고정, 임시 폴더를 쓰는 검사 |
| `tests/macro_acceptance.py` | 113-138 | T-HERM-02 홈 목록 |
| `tests/run_all.py` | 54, 128-142 | `--suite`도 결과 파일을 씀 |
| `tests/paper_live_acceptance.py` | 240-243, 262-275 | 원장 가족 3개, 홀드아웃 표본 검사 |
| `tag:config.py` | 26-30, 275-277 | `.env` 읽기, `QUANTGEN_MACRO_DIR` |
| `tag:.gitattributes` | 1-2 | `* -text` |
| `tag:requirements.txt` | — | `yfinance>=0.2`(고정 아님) |
| `fe37e82:requirements-nautilus.txt` | 2-3 | 전역 Python 설치 금지 이유 |
| `fe37e82:tools/nautilus/launch.py` | 237-242 | 전역 `nautilus-trader` 버전 읽기 |
| `fe37e82:tests/nautilus_acceptance.py` | 505-516 | L1-22: 전역 설치 시 실패와 처방 세 줄 |

### 9.3 Claude가 이 문서를 쓰며 실행한 것과 하지 않은 것

- 실행한 것 (모두 이 세션의 스크래치 폴더나 git 객체에서):
  - `git show`, `git diff --stat`, `git ls-tree`로 태그, `bb35b3b`, `fe37e82`의 코드와 문서를 읽었습니다. `paper_live/out*/`, `grokteam/out/book/`, 보호 캐시 4개는 경로에서 뺐습니다.
  - `git archive`로 태그의 `core/`, `data/calendars/`, `paper_live/{__init__,config,verdict,power}.py`를 스크래치 폴더에 풀고, 고정 버전 인터프리터로 `holdout_sessions()`를 프로필마다 불렀습니다(2.1). HOME과 TMPDIR은 새 스크래치 폴더였습니다.
  - 같은 인터프리터로 pandas의 날짜 계산(`date − Timedelta(days=6)`)을 확인했습니다(2.3).
  - 판독 경로 파일 7개(2.4 표)의 sha256과 `data/calendars`의 git 트리를 세 커밋에서 계산했습니다(2.1, 2.4).
  - 검토 반영 때 같은 인터프리터로, 새 스크래치 HOME과 TMPDIR(HOME은 TMPDIR 밖)에서 태그 달력의 `is_trading_day`로 2026-10-13~10-15가 US, LSE, KRX 모두 거래일임을 확인했습니다(2.3).
  - `git fetch origin`과 `git ls-remote --tags origin`으로 GitHub의 태그를 확인했습니다. 데이터 공급사에는 접속하지 않았습니다.
  - `python3 tools/handoff/push_handoff.py --ledger`와 `--show`로 인계 원장을 읽기만 했습니다. ⑧-1 ID는 원장에 없습니다. 게시하지 않았습니다.
  - **작업 규칙 이탈(머리말, D-13):** 이 클론에서 `tests/frozen_guard.py`의 5개 검사를 `run_all.py` 없이 직접 불렀고 5개 모두 통과했습니다.
    - 검사 (b)는 git으로 태그의 `paper_live/out/frozen_rule/`과 `paper_live/out_krx/frozen_rule/`의 `engine.py`, `config.py` 4개 blob을 읽어 바이트를 비교합니다(`tests/frozen_guard.py:35, 72-77`). 내용은 화면에 나오지 않았고 비교 결과만 나왔습니다. 이 파일들은 코드 사본이고 홀드아웃 산출물이 아니지만, `paper_live/out*/` 아래를 열거나 읽거나 해시하지 않는다는 이번 작업 규칙을 어겼습니다. 이 결과는 근거로 쓰지 않습니다(2.4).
    - 검사 (c)와 (d)는 작업 트리에서 `grokteam/out/book/FORWARD_LOOK.json`과 `paper_live/out*/verdict.json`이 있는지 보고, 있으면 `verdict.json`을 읽습니다(`tests/frozen_guard.py:55-63, 80-82`). 이 클론의 스파스 설정은 지금 이 폴더들을 뺍니다(`git sparse-checkout list`). 실행 당시에도 같았다면 읽은 파일은 없습니다(당시 설정은 UNVERIFIED).
    - 그 실행의 인터프리터, HOME, TMPDIR은 기록이 남지 않아 UNVERIFIED입니다. 고정 버전 인터프리터와 새 스크래치 HOME·TMPDIR을 썼는지 확인할 수 없습니다. 클론에 `tests/__pycache__`가 없으므로 바이트코드는 쓰지 않았습니다. `test_d_pending_readouts_retire_only_when_all_three_are_in`은 TMPDIR 아래에 임시 파일을 쓰고 지웁니다(`tests/frozen_guard.py:94-105`).
    - 이 규칙이 유지되는 동안 Claude 세션은 `frozen_guard` (b)와 guard 스위트를 돌리지 않습니다.
- 하지 않은 것:
  - 판독(`paper_live.replay`, `paper_live.verdict`)과 그 밖의 `paper_live`·`grokteam` 모듈 실행.
  - `paper_live/out*/`의 목록 보기, 산출물 읽기(위 사고 제외), `~/.nextgen`, `.env`, 보호 캐시 4개 열기.
  - 추적 파일 수정, 커밋, push, 인계 문서 게시. 이 문서 파일 하나만 만들었습니다.
