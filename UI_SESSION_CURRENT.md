# QUANTGEN UI 완료 — 메인 / Claude 통합 인수인계

상태: **앱 UI 구현·검증 완료, PR47 main 병합 완료.**
메인 세션의 CURRENT 소유권·실행 ID·연구 원장을 변경하지 않는 보충 인계입니다.

## 사용자 명령과 전달 상태

- C형 차트를 선택했고 사이트 색상 무드에 맞춘 공통 차트·앱 다크모드를 요청했습니다. 이전 A 기본안은 폐기합니다.
- 앱 UI는 이 세션, quantgeneration.com 웹 UI는 기존 **웹사이트 작업공간(AWS)**에서 처리합니다. 이 UI 세션에서 AWS 로그인을 다시 요청하지 않습니다.
- 완료 시 QUANTGEN 메인세션에 알리고 Claude 통합 인수인계에 포함하라는 명령을 유지합니다.
- “토큰 다 쓰기 전에 만약에 다못끝내면 일단 중지하고 메인세션에 너가 지금까지 한거 쭉 알려줘” 명령에 따라 소진 전 체크포인트를 먼저 저장했습니다. 이후 크레딧 추가 후에도 같은 명령을 유지하라는 요청을 받았습니다.
- 지금은 앱 구현과 CI가 모두 끝났으므로 새 작업을 시작하지 않습니다. 미완료 구현을 숨기거나 크레딧을 끝까지 사용하며 범위를 늘리지 않습니다.

**메인 세션 직접 알림: queued / 전송 영수증 없음.** 도구 목록을 다시 확인했으나 기존 세션에 메시지를 보내거나 깨우는 기능이 없습니다. 이 공유 GitHub 기록은 저장된 인계 자료이며 실제 채팅 수신 확인이 아닙니다.
메인 참조 ID: 01a183c6-632a-70cc-a0e6-32e764f43087.
Claude 통합 인계에는 이 파일과 WEBSITE_AWS_HANDOFF.md를 포함하세요.

## 확정된 최종 소스와 검사

- PR47: https://github.com/xkg4real/quantgen/pull/47 — MERGED.
- main 병합: **8c0fb632add442fd1f4d79baea239c21255324d1**.
- 검증한 source head: **74ae598b8beea50c52221f5934bcd9a298b123f8**.
- 브랜치: gpt/chart-c-theme-20261031.
- 병합 전 main PR52 d7896914ee5b363ee745ef327f1ff295028edb5e까지 통합했습니다. PR46 Claude 오류 진단, PR49 채권/포트폴리오 번역, PR51 시장 진단 번역과 웹 인계 기록을 보존합니다.
- Runtime CI https://github.com/xkg4real/quantgen/actions/runs/41193496809 — **Windows Python 3.12, Windows Python 3.14, Ubuntu Python 3.12 모두 SUCCESS**. 설치 wheel·소스·네이티브·차트·교육/언어 검사를 포함합니다.
- Document CI https://github.com/xkg4real/quantgen/actions/runs/41193496681 — **SUCCESS**. 정합성 PASS와 공개 준비 BLOCKED를 구분합니다.
- 로컬: 초기 bounded 회귀 230개, Home/theme 16개, PR46 통합 29개, 네이티브/C/가이드/그리기 38개, 최종 폭 제약 17개, PR49 통합 13개, PR52 통합 10개 통과. 서로 겹치는 검사 묶음이며 연구 원장 누적 실적으로 합산하지 않습니다. 문서/내보내기 검사 47개도 통과했습니다.
- 28개 Flet 차트 생성기의 테마 전환을 확인했습니다. C wheel을 체크아웃 밖에 설치해 앱/네이티브/새 모듈 smoke도 통과했고 최종 CI는 최종 소스로 다시 빌드했습니다.
- 실제 로컬 Chromium/Flet 1600×1100·390×1000, Qt C 라이트/다크 1600×1050·좁은 창 1000×1100을 확인했습니다. 마지막 좁은 창의 content/viewport는 764/764px, 차트는 658×672px였습니다.

## 완료한 C형·다크모드 변경

1. 넓으면 차트/데이터 왼쪽 + 해설 오른쪽 2:1, 좁으면 차트 다음 해설로 쌓습니다. 네이티브 Home 팬·가이드·Quant·Portfolio·Bonds·공통 ToolPane, Flet 가이드/Signals와 28개 equity/FICC/extended 생성기에 공통 구성을 연결했습니다.
2. 기존 팬·선·막대·산점·히트맵 종류, 관측값·축 범위·계산·정규 연구 기록을 보존합니다. 없는 OHLCV를 만들어 캔들로 표시하지 않습니다.
3. 앱 라이트 #F7F5F0 / #FFFEFB / #194C40, 다크 #101915 / #17231D / #91C5AC의 QUANTGEN 아이보리/숲색 팔레트입니다. 실제 사이트 CSS 직접 조회는 403으로 막혀 정확한 토큰 대조는 AWS 후속입니다.
4. 네이티브 Light/Dark는 QSettings ui/theme에 저장·복원합니다. Flet는 page 세션의 테마를 바꾸며 캐시된 그림/제어를 다시 칠합니다. 금융 입력·결과·선택·커서를 유지하고 분석/공급자 조회를 재실행하지 않습니다.
5. 복수 지표는 같은 종목·기간·시간축을 유지합니다. 상세 해설은 Qt 탭/Flet 선택기로 읽으며 선택일 해석·네 단계 설명·실패 사례를 유지합니다.
6. Flutter SVG 한글 글꼴 참조를 단일 등록 가족 QG Interface로 수정했습니다. Home 소개 중복과 비동기 Home 갱신 후 언어가 돌아가는 문제도 수정했습니다.
7. Windows에서 viewport 764px인데 guide/study가 969px로 고정되는 문제를 재현했습니다. 차트 내부와 바깥 가이드 모두 기본 너비 힌트가 화면 폭을 강제하지 않도록 수정했습니다. 수동 지정 최소폭은 유지합니다. 966px 힌트를 넣는 내부/외부 회귀검사와 전체 창 검사 조건을 유지했고 최종 Windows CI가 통과했습니다.

주요 파일: core/theme.py, core/education/chart.py, main.py, ui/chart_study.py, ui/theme_controller.py, ui/indicator_guide.py, ui/research_home.py, quantgen_desktop/chart_study.py, indicator_guide.py, app.py, tools.py, bonds.py, portfolio.py.
설계: docs/product/CHART_C_DESIGN_2026-10-31.md.
웹 변경 큐: docs/product/ui_website_updates/PR-47.json. 확정 merge/CI는 이 기록과 PR에서 확인합니다.

## 앞서 완료한 작업도 함께 인계

- PR36 main 73131c9e74b9ec61fca88845cbdad1525ebceef9: 큰 가격 눈금 잘림, 범례 겹침, 각주 수정. 로컬 39개 및 Windows/Ubuntu CI 통과.
- PR37 main 2999296cae297da69b0198c4a72a9b49fe33ae95: UI→웹사이트 변경 큐·인계 규칙.
- PR42 main d77d99660132f71b50c19b42cc6d76dc4b5f9a79: 기술지표 가이드, 지역/언어·보고서 구조, 데이터 표시 이용권 목록, QUANTGEN 런타임 아이콘. Source 13308a63113743f9b4f8d6a4cf1473a9f7e7e166. Runtime 41181029682 / documents 41181029690 통과.
- Home SMA/EMA/RSI/MACD/BB 가이드와 Signals의 실제 History 재사용. 교육 자료는 출처·해시가 고정된 2018–2022 USD/EUR 기준환율 1,247개이며 역수/네 자리 반올림을 명시합니다. 실시간 OHLCV가 아닙니다.
- Home 6개 + 등록 73개 계열 / 13개 제공 정책의 이용권 검토는 게시/법률 승인이 아닙니다.
- 한국어·영어 문구 묶음과 714개 CLDR 지역 형식을 구분합니다. 714개 언어를 번역 완료했다고 표시하지 않습니다.
- 기존 QUANTGEN ICO/PNG를 Flet Windows 창, Qt 기본 아이콘과 Windows 앱 식별자에 연결했습니다. 설치본/고정 바로가기는 업데이트·재실행 및 실제 Windows 수용 확인이 필요합니다.
- A/B/C/D 시안 중 C를 선택했습니다. 다른 시안은 구현 완료 화면이 아닙니다.

## 완료 범위 밖 후속

- **AWS:** quantgeneration.com 실제 소스·색상 확인, 모든 사이트 차트 C 통일, Auto/Light/Dark 유지, 모바일/배율/키보드 검사, 실제 적용·배포 증거. WEBSITE_AWS_HANDOFF.md 및 PR-42/PR-47 큐를 읽으세요. 앱 병합은 사이트 배포 증거가 아닙니다.
- 실제 Windows 표시/DPI/키보드/작업표시줄/설치물 및 전체 스크린리더 검수, 전문 검수한 추가 번역팩, 메인 세션의 나머지 모델/인라인 번역.
- 운영·법률·계약·데이터 권리·공개 승인. 모든 review-required/BLOCKED 상태와 연구 게이트는 보존했습니다.
- 메인/AWS 채팅 직접 전달 영수증이 없으므로 수신 완료로 처리하지 않습니다.

PR47에 남은 앱 구현·CI·병합 작업은 없습니다. 다른 작업공간에서는 main을 fetch하고 8c0fb632 병합을 확인하면 됩니다. PR36/37/42/47을 다시 수행하거나 실제 원장·보호 캐시·holdout/frozen·주문 경로를 실행하지 마세요.

## 화면 근거

UI 작업공간 /workspace/artifacts/quantgen-ui에 chart-design-studies-ABCD.png, chart-c-light.png, chart-c-dark.png, chart-c-native-narrow.png, chart-c-browser-light/dark/mobile.png가 있습니다. 다른 환경에서 파일이 없으면 소스/CI 링크를 사용하세요.
최초 브라우저 fixture가 Home 자동 갱신 요청을 시도해 차단된 적이 있어 중지하고 공급자 stub/요청 차단으로 교체했습니다. 그 시도를 실시간 데이터·사이트 검증 증거로 쓰지 않습니다.
