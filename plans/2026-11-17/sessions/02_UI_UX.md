# UI/UX 세션 지시문 (기존 세션 유지)

대상: 기존 UI/UX 세션. 오늘(2026-11-17) `claude/friendly-bardeen-r6xe8f` (`da0ea20`)에서 소유자의 11-17 요청을 끝내고 PNG 확인을 기다리는 Claude UI 세션 (session_016uB1jf8m3p5GW1qzQVJe7k; handoff `c73ff11`의 Claude-Session 줄로 확인). GPT UI 후임도 같은 규칙.
이 세션은 이미 일하는 중이므로 통째로 붙이지 말고, 소유자 보고서 2절 3번의 한 줄을 먼저 전달한 뒤 필요할 때 아래를 붙입니다. 결정 답이 오기 전에는 해당 작업을 시작하지 않습니다.

---- 복사 시작 ----

당신은 QUANTGEN UI/UX 세션입니다. 데스크톱 앱(PyQt6, `quantgen_desktop/`) 화면을 맡습니다. Flet(`main.py`, `ui/`)은 유지만 합니다 (`AGENTS.md` §6). **소유자의 11-17 요청 (`docs/product/UI_MARKET_HUB_CONCLUSIONS_2026-11-17.md`, PNG 확인 대기)과 그 피드백이 먼저입니다.** 아래 11-16 항목은 그 흐름 안에 넣습니다.

## 소유자 요청 (원문, 2026-11-16 Notion)
- "커넥션 테스트 페이지 없앨 것 (설정 창) → 여기에"
- "메인화면 아직도 리서치 홈에서 지표가 안뜨는데, 이거 고칠 것. 주요 지표 6개를 그래프와 함께 구현하도록(앱 키자마자 실시간) 해야함."
- "시스템에서 프로젝트 상태 → 마이페이지 (영문도 동일) 이름 바꾸고 시장 데이터 이용 조건, 기록된 프로젝트 상태 등 현재뿐만 아니라 상업화가 됐을때를 상정하여 필요 없는 부분은 표시 안되게 항목 삭제할 것."
- "이와 동일하게 사용자 목적에 맞지 않는 부분들은 삭제할 것"

## 소유자 결정 (보고서 D1, D2, D8, D9)
여기에 답을 붙입니다. "전부승인"이면:
- D1-A: 메인 세션이 PR121에 `core/education/reading_cues.py` 45행을 **이 브랜치와 같은 문장**으로 넣어 main CI를 고칩니다. 이 브랜치의 45행은 바꾸지 않습니다. 동의하면 `UI_SESSION_CURRENT.md`에 한 줄 적습니다.
- D2-A: 소유자가 PR122 병합 전까지 시장 메인·범주 화면 PNG와 지표 결론부 문구를 승인하면 이 브랜치의 PR이 P3 바로 전 자리에 들어갑니다. 아니면 F21 뒤. 화면 7개 시안은 이 PR과 무관합니다.
- D8-A: 홈 지표 6개 유지 (S&P 500, KOSPI, 원/달러, 미국 10년, VIX, BTC). '실시간' 표시는 BTC와 KOSPI(사용자 KIS 키가 있을 때)만, 나머지는 '일별(지연)'. 본인용 앱 기준이며, 공개·판매 전에는 표시권 정리가 필요합니다.
- D9-A: PySide6 전환일(OS-F1, F 뒤)에 OS 세션의 변환 도구를 **이 세션이** 실행합니다.

## 공통 규칙
1. 시작: `python3 tools/handoff/push_handoff.py --show`, `--ledger`, 그리고 handoff 브랜치 `MERGE_QUEUE.md`와 `MASTER_WORK_DESIGN.md`를 읽습니다.
2. `docs/asset_expansion/cache/`는 어떤 ref·어떤 체크아웃에서도 열기·목록·해시·검색 금지. git grep/ls-files에는 `':!docs/asset_expansion/cache'`. 저장소 전체 find, ls -R, grep -r, rg 금지. 코드 작업은 그 폴더를 받지 않는 sparse 클론에서 (마스터 4.1절), 아니면 `git status --porcelain -- <경로>`처럼 늘 경로를 줌. `git add`는 파일 이름으로만, `git add -A`·`git add .` 금지.
3. `.env`, `~/.nextgen` 열지 않음. 화면에 키 값·환경변수 이름을 보여주지 않음.
4. 클라우드에서 `tests/run_all.py` 실행 금지. 검사는 `QT_QPA_PLATFORM=offscreen python -m unittest tests.<모듈>`.
5. 기준선 갱신은 최신 main을 merge한 뒤 맨 마지막: `python -m tools.compliance.check --refresh-baseline --reviewed-by "<이름>" --review-note "<12자 이상>"` → `--check`. 파일 추가·삭제는 PR 설명에 적음.
6. 병합: `MERGE_QUEUE.md` 순서대로. `origin/main`은 merge로 반영 (이미 push한 브랜치는 rebase 금지, force push 금지). 그 PR이 띄운 모든 워크플로의 모든 작업이 정확한 head에서 녹색일 때만. 어떤 실행이든 도는 중에는 병합 금지. `freeze: P3`나 `freeze: F` 동안, 그리고 OS-F1 당일에는 다른 화면 PR을 병합하지 않습니다. 브랜치 작업은 계속 해도 됩니다.
7. LEDGER ID는 `⑬-2/…` 규칙. 11-16 항목은 새 ID를 만들지 않고 이미 정한 `⑬-2/page-redesign/<route>`에 넣습니다. 병합 뒤 기록.

## 맡는 경로
`quantgen_desktop/**` 전부 (계정 화면, API 키 화면, OS-F1 변환 실행, `app_identity` 화면 연결 포함), `ui/**` (유지만), `assets/**`, `core/education/**`, `core/ui_*messages*.py`, `core/ui_page_messages/**`, `tests/desktop_*`, `docs/product/UI_*.md`, `docs/product/ui_website_updates/*.json`.
손대지 않음: `core/research/markets.py` 등 데이터 계층 (데이터소스 세션), `config.py`, `core/credentials/**`·`core/account/**` (결제·계정 세션; 화면은 그 API를 씀), 연구 브랜치, 웹사이트 저장소.

## 작업

**UI-0 체크포인트 (끝남, handoff `c73ff11`).** `UI_SESSION_CURRENT.md` 맨 위에 11-17 요청 원문, `da0ea20`, 끝낸 4 ID, 소유자 확인 대기 3가지가 있고, LEDGER에 4 ID가 (병합 전) 기록되어 있습니다. 남은 것: D1 동의 줄을 같은 절에 더함 (손으로 커밋, force 금지, 다시 읽어 확인).

**UI-1 시안에 11-16 항목 넣기 (지금, 시안만).**
- `draft_07_system` (→ `⑬-2/page-redesign/system`): 이름을 `My Page|마이페이지`로 (메뉴, 번역 키, 화면 제목·부제 예: "My Page" / "계정·언어·설정"). 사용자 화면에서 지울 것: 연결(Connections) 탭 (`quantgen_desktop/connections.py`의 `ConnectionsPane`과 그 연결), 시장 데이터 이용 조건 탭, 홈의 데이터 권리 버튼과 `open_data_rights`, '프로젝트 상태' 패널, '데스크톱 이전 상태' 패널. 남길 것: `core/research/connections.py`와 그 어댑터 테스트, `core/recorded_status_display.py`, `tools/status` (CI·README가 씀). 자리만 (기능 없음): 계정 (웹사이트 로그인 뒤), API 키 (UI-4), 데이터 출처와 고지 (FRED 인용, VIX의 Cboe 저작권, Yahoo 개인용), 앱 버전. 규칙(Rules) 탭은 모의투자 화면으로 옮기는 안을 시안에 제안. 내부 용어 (NOT_RUN, PARTIAL, NOT_APPLIED, ResearchRun, 동결 연구, 원장, 미리보기, Flet)를 쉬운 말로. "계산 결과는 투자 권유가 아닙니다" 같은 안전 문구는 남김. 연결 테스트 대신 나중에 API 키 옆 '연결 확인' 버튼 하나.
- `draft_01_home` (→ `⑬-2/page-redesign/home`): 카드 6개마다 값, 변화, 약 1개월 작은 그래프 (`market_summary.py`의 타일 방식). 라벨은 D8대로. 원/달러(DEXKOUS)는 주 1회 갱신이라 최대 약 1주 늦다는 표시.
- 줄 번호 대신 이름으로 찾습니다 (이 브랜치에서 `app.py`가 이미 바뀜).
완료 조건: PNG를 소유자에게 보내고 승인·피드백을 `UI_SESSION_CURRENT.md`에 기록.

**UI-2 병합 차례가 오면 (D1·D2).**
- `origin/main`을 이 브랜치에 merge합니다. `tests/desktop_home_markets_markets_acceptance.py`의 두 블록 충돌은 **이 브랜치 판**으로 풉니다 (이 브랜치가 범주 아래 행을 없앴으므로 ea3d596의 국가 행 기대는 낡음). `reading_cues.py` 45행은 같은 문장이라 충돌이 없어야 합니다. `docs/compliance/FACTS.md`도 충돌합니다 (양쪽이 끝에 절 하나씩): 두 절을 모두 남깁니다. `source-review.json`은 기준선을 다시 만듭니다. `runtime-smoke.yml`은 이 브랜치 107~108행과 PR122의 9·93행이 다른 줄이라 자동으로 합쳐지는지 확인.
- D1-B를 고르셨다면 이 PR이 먼저입니다: ea3d596의 `tests/desktop_owner_ui_risk_acceptance.py` 수정도 가져와야 녹색이 됩니다.
- 모든 작업 녹색 → 대기열 순서로 병합 → 이미 LEDGER에 있는 4 ID는 다시 `--done` 하지 않고 병합 커밋을 `UI_SESSION_CURRENT.md`에 적음 (PNG 피드백으로 생긴 `⑬-2/market-hub/2` 같은 새 ID만 LEDGER에) → `docs/product/ui_website_updates/`에 JSON 한 개.

**UI-3 `⑬-2/page-redesign/system` 구현 (시안 승인 뒤, 한 PR).** UI-1의 내용. 고칠 테스트: `tests/desktop_a1_status_acceptance.py` (ConnectionsPane), `tests/desktop_market_acceptance.py`의 연결·상태 부분, `tests/status_display_acceptance.py`. PR 설명과 LEDGER에 "⑫-1/display-owner-decision (`LEDGER.md:168`)의 표시 부분을 되돌림"이라고 적음. main 병합은 F21 뒤 (대기열 10번).

**UI-4 `⑬-2/page-redesign/home` 구현 (시안 승인 + DS-H 병합 뒤).**
- 데이터소스 세션의 `load_home_indicators()`를 씁니다 (직접 공급사를 부르지 않음). DS-H 전에는 테스트에 주입한 가짜 로더로 만들고, 병합은 DS-H 뒤.
- 앱을 켜면 6개 기록을 한 작업으로 미리 읽고, 큰 그래프는 그 캐시를 읽음. 시장 갱신 작업을 지표 작업과 KIS 종목 시세 작업으로 나눠 지표가 먼저 그려지게.
- 가짜(합성) 값 금지, 실패 사유 코드 표시는 유지.
- 완료 조건: 오프스크린 테스트 (주입한 가짜 로더만, 네트워크 없음), 녹색, 병합.

**UI-5 `⑬-2/page-redesign/system/2` API 키 화면 (KEY-2 병합 뒤).** 공급사별 가린 입력칸, 저장, 삭제, 상태 '입력됨/입력 필요'. `core/credentials`만 사용. '연결 확인' 버튼 하나는 `core/research/connections.py`의 해당 검사를 재사용. 값은 화면·로그에 절대 표시하지 않음.

**UI-6 계정 화면 (PAY-1 병합 뒤).** 결제·계정 세션의 `core/account` API로 만듭니다. 서버·인증 코드는 쓰지 않습니다.

**UI-7 OS-F1 전환일 (F 뒤, 소유자 "OS go").** OS 세션이 준 `tools/qt_port/pyqt6_to_pyside6.py --apply`를 `quantgen_desktop/**`·`tests/desktop_*`에 실행하고, 알려진 동작 차이 3개를 고치고, OS 세션이 준 화면 밖 수정 목록 (pyproject, 실행 스크립트, Qt 설치 줄, 문서 표현)과 함께 PR 하나. 그날 다른 화면 PR은 열지 않음. 그 뒤 `core/app_identity.py`를 앱의 QSettings 이름과 `windows_branding.py`에 연결.

**UI-8 남은 '봉' 문구 점검.** `reading_cues.py` 19행·35행 (아직 '봉'), `core/market/presentation.py`, `market_chart.py`, `glossary.py` 등이 주식 화면에 나오는지 확인 (미검증). 나오면 규칙 R-D9-2에 맞게 이 세션의 브랜치에서 고침.

## 보고할 것
PR 번호, CI run 번호와 결과, 바꾼 화면 전후 캡처 (가능하면), 남은 질문. `UI_SESSION_CURRENT.md`에 기록.

---- 복사 끝 ----
