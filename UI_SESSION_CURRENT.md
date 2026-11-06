# 최종 상태 — 2026-11-07 KST

**PR89 main 병합 완료**: https://github.com/xkg4real/quantgen/pull/89
Merge `6a09d3fd367cfc14fd62378deed8c441001c6e1b`, source `2f336a363210176b9309fed6aaa3e571630ab4b7`. 아래 이전 중간기록의 main미병합/검사미완료 안내보다 이 최종상태가 우선합니다.

- 글꼴/compactUI/수정된regression19검사 PASS(83.537s). 패키징/정책50 PASS(3.777s). 기존31검사 중29통과와2수정재검사 결과를 중복합산하지 않습니다.
- 한글11172실제힌트/400500600, 전체UI문자coverage, KO/EN/light/dark/1000·1360·1920px 및100·125·150% offscreen9화면 검증 PASS. Preview /workspace/shared/quantgen-ui-preview/.
- 문서20종/소스622정합성PASS, 기존공개준비BLOCKED 유지. RemoteCompliance42245900905 success. **Runtime42245900881은 현재진행중**; 후속담당자가 성공/실패를확인하고 실제실패만수정할것. Windows전체CI/실기기표시완료라고말하지말것.
- AWS앱영향큐 docs/product/ui_website_updates/PR-89.json, 송신도구없어queued. 웹HTML/실배포변경없음. UI/AWS보충인수인계만저장, 메인CURRENT/LEDGER미수정.
- 앱을닫고 기존QUANTGEN CMD에서 origin main을pull한뒤 `.venv\Scripts\python.exe -X utf8 -m quantgen_desktop` 실행. 기존.env/KIS키 유지. 사용자요청에따라 실행법전달후작업중지.

---
이전 중간기록 (이하 미병합 상태는 과거 기록)

# QUANTGEN UI 인수인계 — 2026-11-07 KST

## 현재 상태

이번 글꼴·밀도 개선은 **작업 브랜치에 저장됨, main 미병합, 최종 검증 미완료**입니다. 사용자가 인수인계 .md부터 신속히 요청했으므로 중간 상태를 명시합니다. 앱 전체 완료/웹 배포 완료로 말하지 마세요.

- 저장소: https://github.com/xkg4real/quantgen
- 작업 브랜치: `gpt/compact-ui-final-20261107`
- 원격 확인한 최신 커밋: `0222dbad65fdbbadfa83b9a70d37e6207f87a1ae`
- 글꼴 커밋: `4fb61255c0bd579471589e49d2e09f9643d29006`
- 기준 main: `cd4019c2dfd6747594c75fdf417fd465fc66eb7e`
- 현재 경로: `/workspace/quantgen-ui`, Python `/workspace/.venvs/quantgen/bin/python`
- 이전 환경의 `/workspace/work/quantgen-compact-workspace-20261106`과 미push 커밋 `3bafe23`은 환경 교체로 없어졌습니다. 현재 원격 브랜치가 복원본입니다. 이전 검사/이미지를 현재 커밋의 검증으로 혼동하지 마세요.

## 사용자 요구와 권한

- 차트 안내문 등 한글 획 흐림/울퉁불퉁함 개선, 실제 글꼴 교체 허용.
- 분석 도구/설계·검증/분석 등의 지나치게 넓은 메뉴·입력폼·표를 내용에 맞게 압축. TradingView 참고 이미지 같은 밀도, 모든 기능/데이터 보존.
- GitHub에는 앱 관련 코드만. 웹 HTML은 업로드하지 않음. AWS 로그인/키 재요청 금지.
- 수정은 별도 컨펌 없이 진행하고 완료 보고. 최종 보고에 ‘북딱북딱’ 한 번 자연스럽게 포함.
- 완료 직후 CMD 업데이트/실행법 안내. 키 설정은 이미 성공했으므로 `.env`를 초기화하지 않음.
- 메인/Claude 인수인계는 `handoff`의 `UI_SESSION_CURRENT.md`로 보존. 메인 `CURRENT.md`, `LEDGER.md`, `AUTO_STATE*`는 수정하지 않음.

## 반영한 파일과 동작

1. `assets/fonts/`, `quantgen_desktop/font_policy.py`, `app.py`
   - Gothic A1의 실제400/500/600 hinted TTF를 QG Interface로 이름 변경하여 동봉.
   - 원본 Google Fonts 고정 ref `38411257417e616c5d4daa1b9e91a3dbcebe1c2e`, ofl/gothica1.
   - 한글 전체11172자와 실제 힌트 구성요소를 보존. 없는 기호는 기존 Pretendard에서 QG Symbols 별도 보충.
   - 완전한6파일을 등록하며 부분 실패 시 플랫폼 글꼴 유지/로그. 브라우저 Flet 기존OTF 유지. 런타임 다운로드 없음.
   - `README.txt`, `OFL-GothicA1.txt` 출처/해시/라이선스. `tools/ui/build_hinted_fonts.py` 재생성. pyproject/stage.py에TTF포함.
2. `category_picker.py`, `app.py`, `typography.py`
   - 분석 도구 버튼을 글자폭으로 배치하고 좁으면 줄바꿈. 선택/키보드/기존 연결 유지.
   - 패널16px 여백, 페이지24px, 버튼/입력/탭 여백 축소. 표14px.
3. `form_layout.py`, `tools.py`, `bonds.py`, `portfolio.py`, `app.py`
   - 공통/Portfolio/Monte Carlo3열, Bonds4열 기준224px 입력폭, 좁으면 재배치.
   - 실제폭에 맞춘 패널 최소높이 재계산으로 긴 설명 잘림 방지. 실행버튼은 내용폭/좌측.
4. `table_layout.py`, `result_layout.py`
   - 표 전체Stretch 제거, 내용폭/숫자정렬/최소34px행, 긴내용 자동확장.
   - 좁은2~3열표 줄바꿈, 넓은표 내부스크롤. 쌍 결과패널 최대960px.
   - 분석 계산/요청/보고서 값·KIS·권한·주문 기능은 변경하지 않음.

## 검증 상태 — 미완료를 유지

현재 `/tmp/qg-layout.log`에서 Markets 탭11검사, A3 결과/요청보존8검사 등 통과 출력을 확인했지만 **전체 프로세스 최종 종료코드/총합은 아직 확인하지 않았습니다**.

기존 responsive test의 ‘일부러 잘못된 native width hint를 주면 전체페이지 overflow’ 사전 조건은 새 최대폭 정책으로 성립하지 않아 실패했습니다. 원격0222dba에서는 ‘주입한 hint 자체가 viewport보다 크다’를 검사하도록 조정했고 값/선택/언어보존 검사는 유지했습니다. 실행 중인 오래된 테스트 프로세스가 수정 전 파일을 로드했을 수 있어 해당 검사 재실행이 필요합니다. 실패를 숨기거나 전부PASS로 기록하지 마세요.

남은 일:
- 최종 레이아웃/글꼴/기존 조작 검사 실행 및 실제 실패 수정.
- 현재 TTF+기호의 전체UI문자/11172한글/실제굵기/힌트/패키지 검사. 기존 typography 테스트는 새TTF+기호coverage로 변경됨; 신규 실제hint 검사는 추가해야 함.
- KO/EN, light/dark,1000/1360/1920폭,125/150% 배율 화면 확인. Linux offscreen으로 사용자 Windows 획 선명도를 전부 보장하지 않음.
- `docs/compliance/19-licenses.md` 현재서체 설명과13/14/15/FACTS/source-review 갱신. 이전 환경에서만 했던 이 문서수정은 현 원격에는 아직 없음. 기존 공개준비BLOCKED/운영 검증 조건 유지.
- 앱PR 생성/검사/병합, `docs/product/ui_website_updates/PR-N.json`, UI/AWS보충인수인계. 직접 채팅 송신 도구가 없으므로 큐저장과 송신/배포 구분.

## 다음 담당자 명령

```bash
cd /workspace/quantgen-ui
git fetch origin main handoff
git status --short
QT_QPA_PLATFORM=offscreen XDG_CACHE_HOME=/tmp/qg-cache MPLCONFIGDIR=/tmp/qg-mpl /workspace/.venvs/quantgen/bin/python -m unittest tests.desktop_a3_layout_acceptance tests.desktop_responsive_tools_acceptance tests.desktop_operation_fixes_acceptance tests.desktop_typography_acceptance -v
```

네트워크 자격증명 값을 출력하지 마세요. 현재 환경에서는 일반 `git push origin HEAD`가 실제 성공했습니다. 기존 환경의 GitHub대형blob 우회 작업은 필요 없습니다.

## 사용자 CMD 안내 — main 병합 후 제공

앱을 닫고 CMD에 아래3줄 전부 순서대로 입력합니다. PowerShell용 아님. 경로 앞의 프롬프트나 `.claude` 문자열을 복사하지 않습니다. 아직 이번 브랜치 main병합 전이므로 이 명령만으로 미병합 UI가 적용된다고 말하지 마세요.

```bat
cd /d "C:\Users\skymi\OneDrive\문서\GitHub\quantgen"
for /d %G in ("%LOCALAPPDATA%\GitHubDesktop\app-*") do @if exist "%G\resources\app\git\cmd\git.exe" set "QG_GIT=%G\resources\app\git\cmd\git.exe"
"%QG_GIT%" --no-pager pull --ff-only origin main && .venv\Scripts\python.exe -X utf8 -m quantgen_desktop
```

사용자는 크레딧/시간에 매우 민감합니다. 새 범위를 추가하거나 이미통과한 변동없는검사를 무작정 반복하지 말고 남은 오류와 배포 연결을 끝내세요.
