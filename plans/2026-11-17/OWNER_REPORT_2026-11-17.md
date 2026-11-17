# 11/16 업무 지시 정리 — 소유자 보고 (2026-11-17)

> **2026-11-17 소유자 답 이후 우선순위 (메인 세션):** 이 문서는 소유자 답 전의 초안입니다. 소유자 답(handoff `CURRENT.md`, "소유자 답: 11-16 결정 D1~D14" 절)과 같은 폴더의 보고서 `D5_GITHUB_PRO_AND_PRIVATE.md`, `D7_ENV_STRUCTURE.md`(D7-A 거부·D7-G 권장, 소유자 확인 중), `D9_PYSIDE6_ESTIMATE.md`(나안), `D11_ACCOUNTS_AND_ADMIN_GUIDE.md`(정식 계정 지금), `D14_RAVENPACK_ALTERNATIVES.md`(엑셀 대안 9개, Bigdata.com 시험·DS-2 없음)와 `sessions/04_OS_EXPANSION.md`·`05_PAYMENTS_ACCOUNT_KEYS.md`·`06_DATA_SOURCE_DIDM.md`가 이 문서와 다르면 **그쪽이 우선**합니다. `*_NEW.md` 세 지시문은 위 세 파일로 대체되어 지웠습니다(이력은 커밋 `8a66956`). 병합 순서와 동결은 handoff 루트 `MERGE_QUEUE.md`.


이번에는 읽기만 했습니다. 저장소·Notion·GitHub 설정은 바꾸지 않았습니다. 자세한 내용과 근거는 마스터 파일에 있습니다 (4절).

## 0. 지금 상황 (세 줄)

1. **main 자동 검사(CI)가 PR119 이후 계속 빨간불입니다.** 알려진 실패는 '봉' 문구 1개와 옛 화면 기준의 테스트 3개입니다. 테스트 3개는 GPT의 PR121이 이미 고쳤고, '봉' 때문에 PR121·122가 멈춰 있습니다.
2. **GPT가 넘긴 결과는 git으로 다시 계산해 맞았습니다** (파일럿 1·2, Windows 검사 964행 중 844 통과·0 실패). 새로 하나 찾았습니다: 파일럿 2가 Python 3.13.17로 돌았습니다 (D3). 연구 브랜치 마감(Step 10)은 판정 P2·결정 10대로 이 메인 세션이 합니다.
3. **오늘 UI 세션이 따로 받은 요청(시장 메인 화면, 지표 결론부)은 브랜치에서 끝났고 소유자 PNG 확인을 기다립니다** (인계 `c73ff11`, main 미병합). '봉' 줄도 그 브랜치에서 이미 고쳤습니다. 메인은 그 일과 겹치지 않게 순서를 맞춥니다 (D1·D2). 11/16의 마이페이지·홈 지표 화면은 UI 세션의 시안 승인 흐름에 넣습니다.

## 1. 결정해 주실 것

**"전부승인"** = 모든 ★권장안. 일부만 바꾸려면 "전부승인, 단 D5-B"처럼, 번호별로는 "D1-A, D2-B …"처럼 쓰시면 됩니다.
용어: P3 = main을 연구 브랜치에 합쳐 전체 검사하는 단계. F(F1~F21) = 그 뒤 소유자 PC 최종 검사와 병합. P3부터 F21까지 main 병합은 멈춥니다.

| D | 질문 | ★ 권장 | 다른 선택 | 근거 (한 줄) |
|---|---|---|---|---|
| D1 | main CI를 누가 어떤 순서로 고치나 | ★A UI 세션이 동의하면, 메인이 PR121에 '봉' 한 줄을 UI 세션 문장 그대로 넣음 → PR121 병합 → PR122가 새 main을 합쳐 다시 검사 → 병합 | B UI 세션의 PR을 먼저 병합 (시장 메인 PNG 승인이 먼저 필요, 그동안 main은 계속 빨간불) | 고칠 것이 모두 PR121에 모여 검사 한 번(약 95분)이 줄고, '봉' 줄은 문장이 같아 충돌하지 않습니다 (시장 테스트 충돌 한 번은 어느 안이든 생기며 UI 판으로 풂) |
| D2 | UI 세션 PR(시장 메인 화면 등)을 언제 main에 넣나 | ★A 시장 메인 화면 PNG와 지표 결론부 문구를 PR122 병합 전까지 승인하시면 P3 바로 전에 하나 넣음. 아니면 F21 뒤 | B 무조건 F21 뒤 | 빨리 앱에서 보실 수 있음. 대신 F가 검사 한 번(약 95분)만큼 늦어집니다 |
| D3 | 파일럿 2의 Python 3.13.17 | ★A 차이로 기록하고 파일럿 2를 그대로 인정 | B 3.13.14로 파일럿 2 다시 실행 (한 번 더 앉으셔야 함) | 10/10 일치, 주요 패키지 버전 같음. 원인은 미확인 |
| D4 | 스펙 10.5 '도구' 단락 | ★A 본문은 그대로, 지금 도구 위치·커밋·지문을 Status와 마감 기록에 적음 | B 단락 본문을 고침 | 11-11 결정표가 남긴 질문. 여러 문서가 줄 번호로 인용. GPT도 같은 안 |
| D5 | 저장소 비공개와 비용 | ★A quantgen·tradegen을 지금 비공개 + GitHub Pro + 결제수단 + 예산은 '알림만'. CI 줄이는 작업(GH-1)은 F21 뒤 | B quantgen은 GH-1을 P3 전에 넣고 그 뒤 비공개 (F가 늦어짐) / C 무료·결제수단 없음 (약 $12 뒤 CI 멈춤) | 걱정하신 노출을 바로 막고 F도 늦추지 않음. F까지 전체 검사 2~3번, 번당 약 $3.09 (추정) |
| D6 | 세션 구성 | ★A 새 Claude 세션 3개 (OS 확장 / 결제·계정·API 키 / 데이터소스+DIDM), 메인 = 병합 관리자, 병합 규칙은 마스터 4절 | B 데이터소스만 지금, 나머지는 F21 뒤 / C 일부 GPT | 지금 할 일은 브랜치·문서뿐이라 main과 안 겹침. Claude 주간 사용량을 함께 쓰므로, 70%를 넘었다고 알려 주시면 메인이 OS·결제 세션부터 멈추자고 권함 |
| D7 | .env 없이 실행 | ★A 앱에서 키를 입력해 PC의 키 보관함(Windows 자격 증명 관리자)에 저장 + 키 없이 되는 기본값. `.env`는 개발용 예비 | B 지금은 그대로 | 앱은 이미 `.env` 없이 켜집니다. 법인 없이 가능하고, 법인 뒤에도 흐름이 같습니다 |
| D8 | 홈 지표 6개와 '실시간' | ★A 지금 6개 유지 (S&P 500, KOSPI, 원/달러, 미국 10년, VIX, BTC), 본인용 앱에만. 실시간 표시는 BTC·KOSPI(본인 KIS 키)만, 나머지는 '일별(지연)'. 공개·판매 전에 공급원 교체 | B 다른 6개 지정 | 6개 모두 연결됨. 다만 Yahoo 3개(S&P 500·KOSPI·BTC)는 개인용, 나머지 3개(FRED, VIX는 Cboe)도 조건부라 6개 모두 공개 표시 허가가 아직 없음 (`display_rights.json`). 10/31에 법률 확인을 요청하셨음 |
| D9 | 앱 화면 기술 (PySide6 질문) | ★A 계산 로직은 UI 없는 공통 Python. 데스크톱(Windows·macOS) 화면만 F 뒤 PyQt6→PySide6. 모바일은 Flet(Android 먼저). 지금은 변환 도구·빌드 초안만 브랜치에 | B PyQt6 유지 (판매하려면 유료 라이선스, 가격 미공개) / C 모바일도 PySide6 (iOS에서 numpy를 못 써 막힘) | "전 플랫폼 PySide6 기반이 맞나"의 답은 "아니오". PySide6는 LGPLv3 (판매 조건은 변호사 확인 필요) |
| D10 | 웹사이트 추가 색 | ★A 사프란/황토 (글자 #7A5410, 형광 #F6E3A8) | B 벽돌색 #A8432E / C 직접 지정 | 빨강은 한국 금융 화면에서 '상승'이고 오류색과 비슷합니다 |
| D11 | 회원가입은 언제부터 (Notion 빈칸) | ★A 지금은 이메일만 받는 출시 알림 (만 14세 이상), 정식 계정은 법인 뒤 (유료는 만 19세 이상). 'Alert me' 링크는 알림 폼이 실제로 작동할 때 검 | B 법인 전에는 아무것도 받지 않음 / C 지금 개인 명의로 정식 가입 | 개인도 개인정보처리자라 법인 전에도 가능 (법률 자문 아님, 변호사 확인 전). 처리방침의 운영자 정보가 비어 있고 문의 폼도 미연결 |
| D12 | 웹에서 거래 | ★A 지금은 증권사 웹·앱 화면 연결만 + 문구 "거래 기능은 개발 중이며, 안전·법률 검토를 마친 뒤에만 열립니다." 설계 메모는 메인이 연구 병합(⑦-2) 뒤에 씀 | B 웹 화면 + 내 PC 앱이 직접 주문 (변호사 의견 뒤) / C 우리 서버가 주문 중계 (면허 없이 불가) | 네이버페이 사례에서 금감원이 투자중개업으로 봄. 주문 기능은 변호사 의견서(D-14) 뒤로 이미 정하셨음 |
| D13 | 웹사이트 운영 세션 | ★A website 저장소를 붙인 Claude 클라우드 세션 (역할은 기존 웹사이트 세션 그대로) | B 기존 PC 'WEBSITE' 세션 (push 가능 여부 미확인) | GitHub→AWS 자동 배포는 이미 작동. 빠진 것은 Claude→GitHub 연결 |
| D14 | DIDM 데이터 소스 하나 | ★A Bigdata.com Pro 2주 시험 (월 약 $40, 미검증) + 중단 조건 4개. 시험 스크립트는 소유자 PC에서 실행, 출력만 붙여넣기 (키는 PC에만). RavenPack 계약은 DIDM 3단계 뒤 | B RavenPack 견적 지금 / C 무료 소스만 | RavenPack과 같은 회사·같은 종목 ID라 나중에 옮기기 쉬움. 다만 "3단계 전 유료 $0" 규칙을 깨므로 승인 필요 |

나중에 여쭐 것 (2주 안에 필요 없음): Mac 없이 macOS 방법, 번들 ID·Apple 가입·Windows 서명 인증서, 서버 저장소 위치, Marketplace 범위, 정책 문구 전후 표 (웹사이트 세션이 따로), 오래된 PR #12 닫기, 연구 클론의 `.agents` 옮기기 (P3 공지 때 줄을 드림), '서명 작업'의 정확한 뜻 (지금 작업에 영향 없음).

## 2. 직접 해 주셔야 할 것 (지금)

1. **앱 업데이트와 홈 지표 2분 진단.** 기다리실 서명 작업은 없습니다. 앱을 닫고, **skymi PC의 GitHub\quantgen 폴더**에서 CMD로 실행하세요. (whydi PC의 `Desktop\QUANTGEN`은 연구 클론이라 F가 끝날 때까지 브랜치를 바꾸지 마세요. 그 폴더에서 앱을 켜면 옛 연구 홈이 보입니다.)
   ```bat
   cd /d "C:\Users\skymi\OneDrive\문서\GitHub\quantgen"
   set "QG_GIT=git"
   for /d %G in ("%LOCALAPPDATA%\GitHubDesktop\app-*") do @if exist "%G\resources\app\git\cmd\git.exe" set "QG_GIT=%G\resources\app\git\cmd\git.exe"
   "%QG_GIT%" branch --show-current
   "%QG_GIT%" --no-pager log -1 --oneline
   "%QG_GIT%" switch main && "%QG_GIT%" --no-pager pull --ff-only origin main && "%QG_GIT%" --no-pager log -1 --oneline
   .venv\Scripts\python.exe -X utf8 -c "from core.research.markets import load_markets; [print(r['symbol'], r['status'], r['reason_code'], r['observation_date']) for r in load_markets()]"
   .venv\Scripts\python.exe -m pip show yfinance curl_cffi requests
   call Start-QUANTGEN-Desktop.cmd
   ```
   출력을 붙여 주세요 (키·값은 나오지 않습니다). pull이 실패하면 멈추고 오류를 붙여 주세요 (파일을 지우거나 강제로 되돌리지 마세요). `.venv`가 없으면 `%LOCALAPPDATA%\QUANTGEN\venv\Scripts\python.exe`로 바꾸세요. 평소 whydi PC에서 앱을 켜셨다면, 그 폴더에서는 `git branch --show-current`와 `git log -1 --oneline` 두 줄만 실행해 함께 붙여 주세요.
2. **비공개 전환 (D5-A).** ① quantgen·tradegen 각각 Security → Secret scanning에서 알림이 있었는지 확인 (있으면 그 키 재발급). ② tradegen의 Actions 탭에서 자동 실행 워크플로가 있는지 확인 (있으면 메인에 알려 주세요). ③ 계정 Settings → Billing: Pro 가입, 결제수단, Actions 예산 약 $250/월에 75·90·100% 알림, **'한도에서 사용 중지'는 끔**. ④ 각 저장소 Settings → General → Danger Zone → Change visibility → Make private. ⑤ 두 PC의 GitHub Desktop이 본인 계정으로 로그인됐는지 확인하고, 각 클론에서 `git fetch origin`이 오류 없이 끝나는지 보세요.
3. **UI 세션에 한 줄 전달 (D1-A).** UI 세션 채팅에 붙여 주세요: "메인 세션이 PR121에 `core/education/reading_cues.py` 45행을 이 브랜치와 같은 문장으로 넣어 main CI를 고칩니다. 그 줄은 바꾸지 마세요. PR121·122가 병합되면 main을 이 브랜치에 merge하고 `tests/desktop_home_markets_markets_acceptance.py` 충돌은 이 브랜치 판으로 푸세요. 동의하면 `UI_SESSION_CURRENT.md`에 적어 주세요." 같은 곳에서 시장 메인 화면 PNG·지표 결론부 문구(D2)와 화면 7개 시안을 검토해 주세요.
4. **새 세션 열기 (D6·D13).** Claude 세션 3개에 `xkg4real/quantgen`을 붙이고 지시문 04·05·06을 붙입니다. 웹사이트용 Claude 클라우드 세션에는 `xkg4real/website`를 붙이고 지시문 03을 붙입니다. 그다음 website 저장소 Settings → Branches에서 main 보호 (Pro 필요). 원하시면 승인 때 "세션 생성 위임"이라고 쓰시면 메인이 만듭니다.
5. **문의에 한 줄 추가 (D12).** 상업화 분석서의 KIS 제휴 문의(작업 4)에 "웹 화면에서 고객이 본인 KIS 계좌로 주문하는 구조가 제3자 서비스 제휴 대상인지"를 더하고, 변호사 질문 목록(D-14)에 웹 채널을 넣어 주세요.
6. **로그인 후 화면 참고 스크린샷.** Notion 11/16 절과 Drive에서 찾지 못했습니다. Notion '문서' 칸의 PDF와 외부 개체 2개는 열어 보지 못했으니, 그 안에 있으면 어느 것인지 알려 주시거나 다시 첨부해 주세요.
7. **(D14-A면) Bigdata.com 계정.** 키는 내 PC에만 `BIGDATA_API_KEY` 이름으로 두세요. 채팅에 붙이지 마세요.
8. **"노트북 파일"의 뜻.** 저장소에는 `.ipynb`가 없고 앱과 무관한 것은 `test_npu.py`뿐입니다 (메인이 지웁니다). PC 안 파일을 뜻하셨다면 마스터 부록 H의 목록 명령 출력을 붙여 주세요.

## 3. 세션 배치

| 세션 | 11/16 목록에서 맡는 일 | 시작 |
|---|---|---|
| 메인 (Claude, 이 세션) | Remaining Work (Step 10 마감, PR121·122, P3, F), main 병합 관리, 마스터 파일·다이어그램, 저장소 정리 (test_npu.py 등)·비공개용 CI 축소 (F21 뒤), 웹 거래 설계 메모, 회원가입 정책 문서 (F21 뒤) | 승인 즉시 |
| UI/UX (기존 Claude UI 세션, GPT UI 포함) | 연결 테스트 삭제, 시스템→마이페이지, 불필요 항목 삭제, 홈 지표 6개 화면 → 이미 그린 '시스템'·'연구 홈' 시안 안에서 | 지금 (구현은 시안 승인 뒤, main 병합은 F21 뒤: 아래 시간표) |
| 웹사이트 (기존 역할, 클라우드 세션) | 색 추가, 우리 로그인 화면 (꺼둔 채), 로그인 후 화면 틀, 문구·humanizer, Docs 묶음, Q&A, Intro 강조, 거래 문구, Claude→GitHub→AWS | 세션을 여는 즉시 |
| OS 확장 (신규 Claude) | 플랫폼 문서 수정, 파이프라인 미리 구축, PySide6 질문, 기기 없이 할 수 있는 것, 법인 전/후 차이 | 지금 (브랜치만), main 병합은 F21 뒤 |
| 결제·계정·API 키 (신규 Claude) | 결제망 문서, .env 없이 실행, 법인 뒤 흐름 미리 수정 | 지금 (문서·브랜치), main 병합은 F21 뒤 |
| 데이터소스+DIDM (신규 Claude) | RavenPack·Bigdata.com 비교표, 하나 선택, 점수 방식, 보완 소스 연결, 홈 지표 데이터 쪽 | 지금. 홈 지표는 2절 1번 출력 뒤 |
| TRADEGEN (기존) | 비공개 전 자기 워크플로 점검 | 비공개 전 |

자체 LLM은 Notion 항목이 비어 있어 이번 지시가 없습니다. **시간표:** 11/16의 앱 항목(마이페이지, 홈 지표, API 키 화면)은 F21 뒤에 main에 들어갑니다. F21 날짜는 소유자 Windows 실행에 달려 있습니다. 더 빨리 원하시면 P3 바로 전 자리 하나를 쓸 수 있습니다 (D2와 같은 자리, F가 약 95분 늦어짐).

## 4. 자세한 내용

설계도·근거·출처·법률 메모·부록은 `MASTER_WORK_DESIGN_2026-11-17.md`, 세션별 지시문은 `sessions/00`~`07`에 있습니다.
