# 시장 메뉴·지표 가이드·첫 시세 표시·작업표시줄 로고

**2026-11-13 main 반영 완료:** [PR115](https://github.com/xkg4real/quantgen/pull/115),
병합 `1006b5ee80067fae4b61c26b322794d6906a05bb`. 앱/테스트/자산/Runtime 설정이 같은
`5d98193`의 [Runtime 43419701530](https://github.com/xkg4real/quantgen/actions/runs/43419701530)
6개 작업(Windows3.11·3.12·3.14, Linux3.12, 문법3.10·3.11)이 통과했다. 이후 문서만 통합한
`d743695`의 [Compliance 43429242181](https://github.com/xkg4real/quantgen/actions/runs/43429242181)도 통과했다.
문서 통합 때 자동 재시작된 Runtime43429242177의 완료와 혼동하지 않는다.
웹 후속은 [PR-115 큐](ui_website_updates/PR-115.json)를 따른다.

사용자의 2026-11-13 정정이 과거 UI-D11의 상시 메뉴와 우측 플라이아웃 요구를 대체한다.
바탕화면 바로가기는 만들지 않는다. 대상 앱은 `python -m quantgen_desktop` 네이티브 앱이다.

## 변경

- 시장 메뉴는 처음 숨김. 호버/클릭/키보드로 열고 하위 항목은 레일 안에서 아래로 펼친다.
  지수·외환·채권·매크로 목적지도 시장에 남는다. 지수 전용 화면은 실제 일별 관측을 표시한다.
  자산별 도구는 기존 엔진을 쓰되 분석 도구 화면과 입력·결과 상태를 따로 유지한다.
- 가이드는 시장 차트와 같은 27종을 분류별 짧은 복수 선택 버튼으로 제공한다. 종가만 있는
  역사 표본에서는 OHLC/거래량/수급 자료가 필요한 지표의 부족 이유를 설명한다. 최근 조회한
  실제 시장 차트를 선택하면 같은 OHLCV·시간축·계산·렌더러로 학습한다. 예제와 실측을 섞지 않는다.
- 분석 도구/가이드의 선택 버튼·패널·설명을 종목 상세 화면의 색·간격·선 굵기에 맞춘다.
  승인된 Pretendard OTF/N3 글꼴은 유지한다. 한영·다크 모드와 좁은 화면을 지원한다.
- 시장 목록 첫 진입은 전체 종목과 시가총액을 기다리지 않고 받은 시세부터 표시한다.
  미국 시세는 선택적 시가총액 상세보다 먼저 조회한다. 부분 목록은 조회 중이며 순위 미확정,
  Q-SCORE 후보 계산도 완성된 목록에서 시작한다. 재조회 중에는 마지막 완성 목록을 유지한다.
  시장 전환 시 이전 요청 묶음의 남은 요청을 중단한다. 새 공급자/호스트/요청 한도는 추가하지 않는다.
- Windows는 앱 생성 전 QUANTGEN AppUserModelID를 설정하고, 생성된 실제 창에 작은/큰 로고
  아이콘을 지정한다. 아이콘 핸들은 창이 살아 있는 동안 유지하고 종료 시 해제한다.
  CMD/Windows Terminal 자체의 아이콘은 운영체제 것이며 QUANTGEN 앱 창과 구분된다.
- 시장 상세 차트는 테마/중첩 화면 배치가 뒤늦게 바뀌어도 새 위치를 측정해 화면 상단에 고정한다.
  창 크기가 바뀌지 않는 재배치도 처리하며, 예약 작업은 화면이 닫히면 취소한다.

## 검증과 한계

로컬 오프라인 검사는 실제 앱의 클릭/호버/키보드, 모든 시장 목적지, 지표 선택/해제/언어/내보내기,
창 파괴 시 예약 취소, 27종 계산의 자료 요구 조건, 동일 타임스탬프 틱 보존을 확인한다.
후속 원격 Runtime 결과와 main 병합 SHA는 PR 및 shared handoff의 최신 절에서 확인한다.
Windows 아이콘 검사는 별도 실제 Windows Qt 프로세스에서 AppUserModelID와 WM_GETICON을 읽는다.
Linux에서는 해당 검사를 건너뛴다. 사용자 PC의 Explorer 캐시·DPI·보조기술은 직접 검증하지 못했다.

시세 응답성 검사는 마지막 응답을 차단한 동안 첫 행의 표시/상세 열기와 순위 미확정을 확인한다.
실제 계정/네트워크 지연 시간의 개선율은 측정하지 않았다. 공개 정책 20종의 일관성 검토는 공개
승인이 아니며 기존 BLOCKED 상태를 유지한다. 웹 HTML·AWS 배포를 완료한 것으로 표시하지 않는다.

## whydi PC 실행

앱을 종료한다. 터미널 앞에 `PS`가 있으면 `cmd`를 한 번 입력한 뒤 아래 CMD 블록을 실행한다.
명령 블록에 `C:\...>` 프롬프트나 코드 펜스를 함께 붙이지 않는다.

```bat
cd /d "C:\Users\whydi\OneDrive\Desktop\QUANTGEN"
set "QG_GIT=git"
for /d %G in ("%LOCALAPPDATA%\GitHubDesktop\app-*") do @if exist "%G\resources\app\git\cmd\git.exe" set "QG_GIT=%G\resources\app\git\cmd\git.exe"
"%QG_GIT%" switch main && "%QG_GIT%" --no-pager pull --ff-only origin main && "%QG_GIT%" --no-pager log -1 --oneline && .venv\Scripts\python.exe -X utf8 -m quantgen_desktop
```

`.env`/KIS 키나 가상환경을 다시 만들 필요는 없다. `pull`이 오류로 멈추면 앱을 실행하기 전에
그 오류를 확인한다. 기존 변경 파일을 강제로 덮거나 삭제하는 명령은 포함하지 않는다.
