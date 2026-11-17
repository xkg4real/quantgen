# 나머지 7개 화면 새 배치 적용 (2026-11-17, Claude UI 세션)

## 소유자 요청 원문

> 시안 7개 전부 승인, 앱에 적용 진행하세요

> 끝나면 png로 보내주세요 실행cmd도 안내부탁 (skymi)

> 끝나면 실행 cmd를 skymi랑 whydi 둘 다 제공해주세요

앞선 요청(시안 작성 근거)은 [시장 메인 화면·지표 결론부 문서](UI_MARKET_HUB_CONCLUSIONS_2026-11-17.md)에 원문 그대로 있습니다.
시안 PNG: `docs/product/ui_drafts_2026-11-17/draft_01_home.png` … `draft_07_system.png`.

기준: 작업 브랜치 `claude/friendly-bardeen-r6xe8f` (main `e01e152` 위). PR은 소유자가 요청하면 만듭니다.

## 한 일

공통 틀 `quantgen_desktop/page_kit.py`: 상세 차트와 같은 배치(도구줄 · 왼쪽 결과 화면 · 오른쪽 설정 열 316~360px · 맨 아래 실행 버튼 고정 · 한 줄 핵심 수치 · 16px 둥근 카드). 기존 탭·패널·계산·요청·저장·내보내기는 그대로 두고 배치만 옮겼습니다(`bind_tabs`, `dock_form`, `dock_into`).

| ID | 화면 | 내용 | 주요 파일 |
|---|---|---|---|
| ⑬-2/page-redesign/quant | 설계/검증 | 몬테카를로 \| 전략 실험실 전환, 오른쪽 설정 열, 결과 위 한 줄 수치(시작·중앙값·하위/상위 5%·손실 확률·95% VaR) | `app.py`(make_quant), `page_kit.py`, `tools.py`, `form_layout.py` |
| ⑬-2/page-redesign/home | 연구 홈 | 지수 타일(작은 선) · 큰 일별 종가 차트 · 오른쪽 관심종목/최근 연구/작은 분포 | `home_view.py`, `app.py`(make_home) |
| ⑬-2/page-redesign/tools | 분석 도구 | 10개 도구 알약 탭, 채권: 가격·수익률 곡선(볼록성 음영·±100bp)·시나리오·선물 헤지 카드 | `bonds.py`, `tools.py`, `app.py`(make_tools) |
| ⑬-2/page-redesign/guide | 기술지표 가이드 | 차트 카드 + 날짜 슬라이더 + 빗나간 신호, 오른쪽 지표 \| 해석(결론부 카드), 투자 용어 모드 | `indicator_guide.py`, `app.py` |
| ⑬-2/page-redesign/risk | 분석 | 포트폴리오: 효율적 프런티어(자본시장선) · 비중·위험 기여 · 4가지 목적함수 비교, 기술적 분석, 모의투자(긴급 정지 맨 위) | `portfolio.py`, `charts.py`, `paper.py`, `risk_page.py` |
| ⑬-2/page-redesign/library | 연구 보관함 | 실행 목록(필터·검색) · 결과 미리보기 · 오른쪽 실행 정보/재현성/AI 해설 | `library_view.py`, `commentary.py`, `app.py` |
| ⑬-2/page-redesign/system | 시스템 | 공급처 목록(설정 이름·설정 여부·접속 검사, 키 값 표시 안 함), 언어·화면·연결 확인 | `connections.py`, `app.py` |

### 독립 검토에서 고친 것 (검토자 8명, 20건)

- 실행 중에도 오른쪽 열 실행 버튼이 눌리던 문제(설계/검증·분석 도구·기술적 분석·시스템) → 실행 중 비활성.
- 전략 실험실의 단계 안내가 어디에도 안 보이던 문제 → 탭을 따라 읽는 법으로 이동.
- 연구 홈이 특정 창 높이(예: 1440×781)에서 크기 조정을 끝없이 반복하던 문제 → 차트 높이 하한에 여유.
- 모의투자 엔진 버튼(긴급 정지 포함)이 버튼 모양·포커스 표시를 잃던 문제 → 복구.
- 1000px 창에서 오른쪽 열이 잘리던 곳(매크로 v2, 채권 영어, 전략 실험실, AI 해설 영어, 모의투자, 규칙 탭) → 줄바꿈·말줄임·열 폭 316px.
- 시스템 화면에서 Tab 키가 멈추던 문제, 보관함 AI 요청 중 목록 갱신이 결과를 엉키게 하던 문제, 언어 전환 후 모델 이름·배지가 이전 언어로 남던 문제 등.

## 시안과 다른 점 (엔진이 계산하지 않는 값은 넣지 않음)

- 분석 도구: 한 번 실행에 한 도구만 계산하므로 시나리오·헤지 카드가 나란히 나오지 않습니다. ±50bp 행 없음(엔진은 ±25/±100bp).
- 분석: 최대 낙폭 없음(최적화기가 계산하지 않음, 대신 최적화 수렴). 종목은 칩이 아니라 입력칸.
- 연구 홈: 작은 선은 이미 불러온 종가로만 그립니다(추가 조회 없음). 1360px에서는 타일 3개.
- 연구 보관함: 진행률 막대 없음(기록하지 않음), 회사 이름 대신 데이터 출처.
- 시스템: "설정 다시 읽기" 없음(.env는 앱 시작 때 한 번 읽음). 접속 검사 전에는 "접속 검사 전".
- 기술지표 가이드: 기본 예시는 기존 USD/EUR 참조 환율(선 차트). 종목을 본 뒤 사례에서 "최근 조회한 시장 차트"를 고르면 캔들 차트.

## 소유자 확인 필요

- 투자 용어 목록의 "캔들 차트 · 봉" 항목(`core/education/glossary.py`)에 금지어 '봉'이 있습니다. 이름을 바꿀지 결정해 주세요.

## 검증

- 오프라인 픽스처 · Linux offscreen. UI 테스트 107개 모듈(1,100여 개) 실행, 화면별 1000/1360/1440/2000px · 한/영 · 밝게/어둡게 배치 점검.
- 소유자 Windows 화면·실제 시세·실계정은 확인하지 않았습니다.
- compliance: [FACTS](../compliance/FACTS.md#page-redesign-2026-11-17)·12-claims 기록, publication BLOCKED 유지.

## 실행 (Windows CMD)

이 작업은 아직 main에 합치지 않았으므로 작업 브랜치를 받아 실행합니다. 앱을 먼저 닫고, 터미널 앞에 `PS`가 있으면 `cmd`를 한 번 입력한 뒤 아래 블록을 붙여 넣습니다.

skymi PC:

```bat
cd /d "C:\Users\skymi\OneDrive\문서\GitHub\quantgen"
set "QG_GIT=git"
for /d %G in ("%LOCALAPPDATA%\GitHubDesktop\app-*") do @if exist "%G\resources\app\git\cmd\git.exe" set "QG_GIT=%G\resources\app\git\cmd\git.exe"
"%QG_GIT%" fetch origin claude/friendly-bardeen-r6xe8f && "%QG_GIT%" switch claude/friendly-bardeen-r6xe8f && "%QG_GIT%" --no-pager pull --ff-only origin claude/friendly-bardeen-r6xe8f && "%QG_GIT%" --no-pager log -1 --oneline && call Start-QUANTGEN-Desktop.cmd
```

whydi PC:

```bat
cd /d "C:\Users\whydi\OneDrive\Desktop\QUANTGEN"
set "QG_GIT=git"
for /d %G in ("%LOCALAPPDATA%\GitHubDesktop\app-*") do @if exist "%G\resources\app\git\cmd\git.exe" set "QG_GIT=%G\resources\app\git\cmd\git.exe"
"%QG_GIT%" fetch origin claude/friendly-bardeen-r6xe8f && "%QG_GIT%" switch claude/friendly-bardeen-r6xe8f && "%QG_GIT%" --no-pager pull --ff-only origin claude/friendly-bardeen-r6xe8f && "%QG_GIT%" --no-pager log -1 --oneline && call Start-QUANTGEN-Desktop.cmd
```

main으로 되돌아가기(두 PC 공통, 위의 `cd`·`set`·`for` 세 줄 다음에):

```bat
"%QG_GIT%" switch main && call Start-QUANTGEN-Desktop.cmd
```

`.env`·`.venv`는 그대로 둡니다. `switch`나 `pull`이 오류로 멈추면(로컬에 고친 파일이 있을 때 등) 앱을 실행하지 않고 멈추며, 파일을 덮어쓰거나 지우는 명령은 없습니다.
