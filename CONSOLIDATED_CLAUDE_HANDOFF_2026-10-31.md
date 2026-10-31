# QUANTGEN 통합 Claude 인수인계 — 2026-10-31
수집 기준: 2026-10-31 19:54 KST. 이후 추가 자료는 해당 문서의 새 SHA를 대조해 보충해야 한다.

## 0. 최신 지시와 운영 상태
사용자는 모든 세션의 결과를 이 메인 세션에서 취합해 대표 인수인계를 진행하고, 그 외 모든 작업을 중지하라고 지시했다. 이 문서는 **완료·미완료를 함께 반환하는 인계**이며 전체 제품 완료 선언이 아니다. 개발, 추가 검사 실행, PR 병합, 배포, 새 예약은 이번 통합 작업에서 수행하지 않았다. 추가로 들어온 자료는 아래 출처를 대조해 반영했다.

- 개발은 사용자 중지 상태다. 기존 QUANTGEN Codex 인수인계 예약은 disabled, next_run_time=null을 재확인했다. 자동 재개하지 않는다.
- UI 세션은 PR47 완료 후 새 작업을 시작하지 않는다고 기록했다. 웹사이트 세션 배포 영수증도 owner_stop=true다. 다른 채팅 프로세스를 직접 정지·조회했다는 뜻은 아니다.
- 본 메인은 다른 채팅의 원문 전체나 메시지 발송 도구를 갖고 있지 않다. 공유 GitHub 인계, PR·CI, 접근 가능한 로컬 기록과 지정 Notion을 취합했다. 메인이 자료를 읽은 것은 확인됐지만 **Claude의 열람·실행 영수증은 없다**.
- 계정 토큰 잔량은 unknown이다. 사용자가 인계를 요청했다는 사실로만 기록하고 소진량을 추정하지 않는다.
- 이 최신 중지 지시가 과거의 “계속 진행”, “CI 후 병합”, “매시간 자동 개발”보다 우선한다. 인계가 returned가 되어도 개발 재개 허가로 해석하지 않는다.

## 1. 확보한 세션과 증거
| 구분 | 확보한 자료 | 이번 통합에서 확인한 수준 |
|---|---|---|
| 메인 제품·연구 후속 | CURRENT/LEDGER, 로컬 STATE·단위별 evidence, 주간 보고서 | 기존 50개 완료 하위 ID가 LEDGER에 모두 있음; 제품 체크아웃 clean. 새로운 제품 완료 ID를 만들지 않음 |
| 별도 UI | UI_SESSION_CURRENT.md 최종본 | PR47 최종 source·main 병합·CI 3개 환경과 문서 CI를 직접 GitHub 재조회 |
| 웹사이트/AWS | WEBSITE_AWS_HANDOFF.md, WEBSITE_AWS_SESSION_CURRENT.md, website-ui/2026-10-31.1/deployment-receipt.json, rebuild_ui.py | 새 배포 영수증과 변경 재구성 소스를 수신·보존. 실제 사이트 응답은 해당 세션의 기록이며 이번 메인이 다시 접속/배포하지 않음 |
| 정책·양식 문서 | PR34, docs/compliance/README.md·RELEASE_GAPS.md, CI41175726660 | 병합·정확한 source의 성공 CI 확인. 법률·공개 준비 완료로 확대하지 않음 |
| 진행표 | 승인된 sapientia 계정의 REMAINING WORK | 기존 완료 하위 취소선·미완료 부모 유지. 이전 상단 기록의 오래된 상태는 최신 원격 사실과 구분 |

모든 공유 출처는 저장소 xkg4real/quantgen이다. UI 최종본과 최초 웹 영수증 ref는 a9cb8744ad2fad652290e528306dd70fd8b6f2fc이며, 추가 AWS 최종 회신/중지 색인 ref883dd444891024757299b24a683b46d74c09fc20도 수신했다. 그 이후 자료가 오면 파일명·SHA·증거를 추가 확인하고 기존 내용을 조용히 덮어쓰지 않는다.

## 2. 최종 저장 위치와 충돌 방지
| 대상 | 기준 |
|---|---|
| 제품 main | 8c0fb632add442fd1f4d79baea239c21255324d1 — 별도 UI 세션 PR47 병합 |
| 메인 마지막 코드 작업 | gpt/market-diagnostics-website-record-20261031 / 6a47cc8692a18b505fecf549013252ce61e94e68 — PR52, 이후 제품main은 위 UI 병합까지 진전 |
| UI 마지막 소스 | gpt/chart-c-theme-20261031 / 74ae598b8beea50c52221f5934bcd9a298b123f8 — PR47 병합 완료 |
| 연구 브랜치 | claude/amazing-gauss-tdiguu / 0510719995e0ec3dfda8f113f826f43ca1821c6b — PR21 병합, 제품main과 별개 |
| 연구 수정 소스 | gpt/approved-research-followups-20261030 / 36df786cb7b1395cd08bc5db2d1ad9b6244e66f3 |
| 열려 있는 PR | #4 연구 누적 브랜치→main, #12 이전 누적 인수 브랜치→main. 이번 인계가 이 둘의 병합 허가는 아님 |
| 통합 실행 | f725a222-54c1-4b11-9336-ccedc319c1ed; handoff-only. 이전 0a573fe3 실행의 task/handoff/branch/source/CURRENT blob와 잠금 해제 기록을 대조한 뒤 CAS/read-back으로 인수 |

본 메인 작업트리는 /workspace/work/quantgen-ui-main-20261029에서 clean으로 확인했다. UI 세션이 적은 /workspace/work/quantgen-ui-guide-20261031 및 화면 캡처 폴더는 이 환경에는 없다. 원격 소스와 CI는 확보했으며 해당 화면 파일을 여기서 재검토했다고 주장하지 않는다. .env·보호 캐시·실제 원장 등은 읽거나 해시하지 않았다.

## 3. 메인 제품 작업 — 완료와 범위
- PyQt6 독립 Windows 앱은 PR17로 네이티브 6개 워크스페이스와 분석·Strategy·Macro·Rules·모의 Trading·선택 AI 연결을 main에 반영했다. Flet 브라우저는 유지한다. PR16 초기 슬라이스는 PR17에 흡수된 이력이며 별도 완료량으로 더하지 않는다.
- PR13/14/15는 패키징·설치 CI, Monte Carlo ResearchRun 관측/출처/저장/내보내기, Home와 일별 지표, F1 favicon 자산·브라우저 시작 호환성을 반영했다. 전체 모델 ResearchRun·이력·canonical identity, 실제 설치본 검수까지 끝난 것은 아니다.
- 언어 문제는 Windows 독립 앱 대상이다. PR39 공통 언어 선택·재시작 유지, PR40 FX, PR43 캐리, PR44 Rates, PR49 Bonds/Portfolio, PR51 AR1·펀딩·호가 검사 고지를 한국어/영어 표시로 연결했다. 원본 보고서·숫자·모형 ID·사용자/공급자 원문과 미실시 상태는 보존했다. **13-8 부모, 기타 모델/LETF/인라인 문구, Flet 동등성, 실제 Windows 수동/DPI 인수는 미완료**다.
- Claude API 오류 PR46은 인증·권한·모델·크레딧·사용량·네트워크 오류를 안전하게 구분하고 양 UI에 안내한다. 키/원시 오류를 노출하지 않도록 회귀검사했다. **실제 사용자 키를 읽거나 변경하지 않았고 실제 연결 복구 13-9/b는 NOT_RUN**이다.
- NautilusTrader는 연구/백테스트 엔진과 어댑터이며 FMP·기타 원천데이터 공급사를 자동 대체하는 데이터 서비스가 아니다. PR46에 그 역할 구분을 문서화했다. 실제 공급자 제거/새 데이터 구독 완료로 읽지 않는다.
- §10 오류 정리는 기록 기준 67그룹 중 15그룹 구현·main 반영, 52그룹 미완료다. 14관찰 행·15모호 ID 매핑이 남는다. 다른 문서의 13관찰 그룹/13매핑과는 단위를 먼저 대조해야 한다. 전체 연구 검증률로 환산하지 않는다.
- PR29 NEW-M6-02/a는 잘못된 IID p값 제거와 조건부 탐색 위상진단까지만 완료했다. 실제시장 가정·역사 카드·부모 결함은 미완료다. M4-N3 금리/배당 규약은 분석 메모만 있고 구현하지 않았다.

### 메인 작업의 상세 검증 기록
M4-N1 기초지수 연결
PR https://github.com/xkg4real/quantgen/pull/31
source 55dae2fd7e6deeefa4a0a41f67f6b19d2d35e146; main merge d4670f3bb738147a48a5dafe34dad7628e3fe3e4
CI https://github.com/xkg4real/quantgen/actions/runs/41172791664 — success
22개 검사, 3펀드 27결과필드 동일. 공식 master live조회 CONNECT403; 실제 공급자 검수 NOT_RUN.

M4-N12 옵션 호가 검사수
PR https://github.com/xkg4real/quantgen/pull/32
source e5a09e5beea84f48cf037f1b2d715f4904f3f341; main merge 118041443385cdd05fae0929172cf8eccd4b86a3
CI https://github.com/xkg4real/quantgen/actions/runs/41173538906 — success
19개 검사, 기존3579값/배열 동일. 미실행·부분검사·실제 위반0 구분.

2-1/b 설치 의존성
PR https://github.com/xkg4real/quantgen/pull/33
source b20f9b1749b483e5430b5280a8e65a0d87f3854e; main merge e1ce7469511c6e128e6725b4d11ae28bfbbb908e
CI https://github.com/xkg4real/quantgen/actions/runs/41173902523 — success
15개 runtime 선언 일치; 합성OLS/ADF 스모크. 동결 연구환경 변경 없음.

M3-N04 스왑션 보조 환산
PR https://github.com/xkg4real/quantgen/pull/35
source 4e84e992f68cf02208c2e4fff121de883dd5c99c; main merge 94659fdd528efb34598a72b7017eda74f7d221ff
CI https://github.com/xkg4real/quantgen/actions/runs/41174151348 — success
11개 집중/UI/경계검사 + 기존3개 가격검증. 정상24사례 기존필드 동일; 보조환산 불가만 분리.

M4-N8 SABR 진단
PR https://github.com/xkg4real/quantgen/pull/38
source 743521d6d2660fd4b8ee1ef357ede1073fc8fe7a; main merge 579aadb8fd219a25b543ea8c9a2c803d3a2cbece
CI https://github.com/xkg4real/quantgen/actions/runs/41175905734 — success
집중7+기존desktop22+FX3검사;기존904필드 동일. 독립/차익/실제Windows 검증 NOT_RUN.

13-8/a Windows 언어 설정
PR https://github.com/xkg4real/quantgen/pull/39
source 6a82337de447279372a351185bda855b581c3c51; main merge f24463f4bf9fa637318dd1f1683c375d5387eef4
CI https://github.com/xkg4real/quantgen/actions/runs/41177249869 — success
언어7+desktop22+chart4=로컬33검사;언어전환·재시작·입력/원문 보존. 부모 및 긴 해설은 미완료.

13-8/b1 FX 해설 번역
PR https://github.com/xkg4real/quantgen/pull/40
source ae768dc607a961bf71a8d4c57c6cd629ec78ba71; main merge bea069f14722b55466d21ad7a5924c4a42bbd312
CI https://github.com/xkg4real/quantgen/actions/runs/41177922111 — success
FX번역6+언어7+SABR1+desktop22=로컬36검사;모든 표시숫자·분기·NOT_RUN·원문보고서 보존. 다른 해설 미완료.

13-8/b2/a 캐리바스켓 해설
PR https://github.com/xkg4real/quantgen/pull/43
source df7ccd8f21815933ff48e105d8e6bac77937b4cf; main merge 9d55e2ba350054759055c2f85b4332993a047e8d
CI https://github.com/xkg4real/quantgen/actions/runs/41179628495 — success
로컬41검사;모든 표시숫자·비용/지연금리경고·포지션·원문보고서/표값/equity보존.

13-8/b2/b 금리 결과 해설
PR https://github.com/xkg4real/quantgen/pull/44
source 32d80824432bb28373c3c1aa17b14af60aa92cb5; main merge 8c9b2fc090285dfcb5a1b019685052949ced8f44
CI https://github.com/xkg4real/quantgen/actions/runs/41179930472 — success
로컬38검사;curve/PCA·swap·swaption/cap/floor·3시뮬레이션모형/조건부PV·원문보고서보존. 모형/provider원문 주석은 그대로.

13-9/a Claude 연결 오류 및9-2/c Nautilus 역할 설명
PR https://github.com/xkg4real/quantgen/pull/46
source c47f6c0a116cad919b403568d377408452cdab69; main merge 13d16ae551cea65b6ac20a02a04e812de7745838
CI https://github.com/xkg4real/quantgen/actions/runs/41181892399 — success
로컬24개 API/privacy/양UI·언어 검사 및47개 문서경계 검사. 실제 사용자 API/Windows 연결 NOT_RUN; 키를 읽거나 변경하지 않음.

13-8/b2/c/a Bonds/Portfolio 해설
PR https://github.com/xkg4real/quantgen/pull/49
source 22f52dc9adaeb27e44028b0cadee3c4f76d48b0b; main merge 4c51ab96e1f61a101fa8a76d024689830bf5d099
CI https://github.com/xkg4real/quantgen/actions/runs/41183600974 — success
로컬57검사 및문서47검사;이전11사례 report입력/sections/원문exact동일. 언어전환/조건부경고/수치/원문보존. 기타모델·inline·Flet parity·실제Windows/DPI는별도.

13-8/b2/c/b/a 시장 진단 고지 번역
PR https://github.com/xkg4real/quantgen/pull/51
source c3e69ccc058b5c0c59c147d2fa65ba5ea3b52372; main merge ccf6654b7da1221e2b6bf09e019ecb6223c1e966
CI https://github.com/xkg4real/quantgen/actions/runs/41191720514 — success
로컬33·문서47검사PASS;이전4사례 parameters/raw sections/report sections exact동일. AR1·펀딩·호가검사 범위/미실시/원문 보존. 실제Windows·나머지본문·Flet 동등성은 미완료.


## 4. 별도 UI 세션 — 최종 수신 완료
PR36 눈금·범례·각주 수정, PR37 UI→웹 인계 규칙, PR42 기술지표 가이드·언어/지역·자료 이용권 목록·런타임 아이콘, PR47 C형 차트·다크모드를 함께 인계한다.

PR47은 2026-10-31 19:43:36 KST에 main 8c0fb632로 병합됐다. 최종 source 74ae598b이며 Runtime 41193496809의 Windows Python3.12·3.14/Ubuntu3.12 세 작업과 Document41193496681이 모두 success인 것을 메인이 재조회했다. 메인이 PR을 병합한 것은 아니다.

- 넓은 창은 차트/데이터 왼쪽, 해설 오른쪽 2:1; 좁은 창은 순서대로 쌓는다. 네이티브 Home·교육 가이드·Quant/Portfolio/Bonds·공통 ToolPane 및 Flet 28개 차트 생성기에 연결했다.
- 기존 차트 유형·관측값·축·연구 기록을 유지한다. 관측되지 않은 OHLCV를 만들지 않는다.
- Qt Light/Dark는 ui/theme에 저장·복원한다. Flet는 캐시된 그림을 다시 칠하며 분석·공급자 조회를 다시 실행하지 않는다.
- 한글 SVG 글꼴, Home 갱신 후 언어 되돌림, Windows guide가 viewport보다 넓어지는 문제를 수정했다.
- UI 세션 로컬 증거는 230/16/29/38/17/13/10 검사 묶음과 문서47검사다. 중복되는 회귀 묶음이므로 합산하여 새 연구 실적으로 세지 않는다. 최종 소스 CI가 우선 증거다.
- 교육 표본은 2018–2022 USD/EUR 기준환율 1,247개이며 실제 OHLCV/실시간 데이터가 아니다. 한국어·영어 번역과 714개 CLDR 지역 형식을 구분한다.
- 아이콘 연결은 구현됐지만 설치된 EXE·고정 바로가기·작업표시줄의 실제 Windows 인수는 남는다.
- 실제 Windows 표시/DPI/입력·키보드/스크린리더·서명 설치물·추가 언어팩은 별도다. C형 구현 완료가 앱 전체 현장 검수 완료는 아니다.

주요 경로: docs/product/CHART_C_DESIGN_2026-10-31.md, INDICATOR_GUIDE_DESIGN.md, UI_LOCALIZATION.md, MARKET_DISPLAY_RIGHTS_2026-10-31.md; core/theme.py, core/education/chart.py, ui/chart_study.py, ui/theme_controller.py, quantgen_desktop/chart_study.py 및 각 화면 연결. 전체 상세는 [UI_SESSION_CURRENT.md](UI_SESSION_CURRENT.md).

## 5. 웹사이트/AWS 세션 — 초기 수정 배포와 후속 미완료 구분
새로 들어온 [배포 영수증](website-ui/2026-10-31.1/deployment-receipt.json)은 revision2026-10-31.1의 초기 소개사이트 UI 수정이 16:26:02 KST 배포됐고 16:27:19 KST 공개 응답 HTTP200·revision·스타일/inline script 일치를 확인했다고 기록한다. 메인은 영수증 자체를 원격으로 읽고 보존했다. 현재 실제 사이트를 재접속해 검증하거나 배포를 실행하지 않았다.

- 이전 HTML SHA256: eb392040377722562ee5d5ca175629c2156186c5bd55a3aec9792dce8b2a643f.
- 배포 HTML SHA256: d3dcc4f48dd2355fc7e748f30b75135992043a0e9933dc13f40d7355d624ca02.
- AWS 세션의 local review commit: 5cd022145bf34d993fbcc7f92242895b57cf2598. AWS 작업공간의 독립 사이트 저장소 커밋이며 제품 main의 PR/커밋이 아니다.
- 수정 내용은 저장된 장식/카드/grade 중복, 모바일 grid 잔여 열, 큰 가격 축 여백·라벨 겹침, DPR 선명도, 누락된 saved-page 분석자산 참조다.
- 영수증의 검증: responsive7, motion/theme4, large-price4; 데이터 checksum 및 study engine/gates/font 불변; units34/mini34/grades9.
- 배율 검증은 CSS viewport/device-scale 모사이며 실제 브라우저 수동 줌이 아니다. 숨겨진 복사 버튼·활성 없는 외부 링크/다운로드는 검사하지 않았다.
- **C형 사이트 전체 차트 통일, PR42/47 기능 이식, 인증된 웹앱 구현은 이 배포 범위 밖이며 미완료**다.
- rebuild_ui.py는 특정 원본 해시에서 위 배포물을 재구성하고 일치 여부를 확인하는 스크립트다. 원본을 덮어쓰지 않고 배포도 하지 않는다. 이번 인계에서 실행하지 않았다.
- 이전 WEBSITE_AWS_HANDOFF.md의 “사이트 수정/배포 미확인”은 UI 세션 관점의 과거 기록이다. AWS가 최신 문서를 중지 색인으로 바꾸고 원문을 고정 링크에 보존했다. 초기 배포 영수증과 후속 C형 미완료를 구분한다.
- 기존 AWS 프로필 quantgen/리전 ap-southeast-2 이력만 전달한다. 현재 로그인/호스팅 계정 접근을 이 메인에서 새로 검증하지 않았으며 인증/설정/배포를 변경하지 않았다. 영수증은 owner_stop=true다.

본 메인의 기존 산출물은 public-site/QUANTGEN_A_F1.html과 전달 ZIP이다. 초기 문구·숫자·동작 보존 검증(29링크/71컨트롤/4스크립트, seeded출력/16전략 카드 일치 등)은 과거 완료 근거다. 최신 공개 파일은 웹 세션 영수증과 구분한다. UI웹검토 큐의 queued/no receipt를 자동으로 “전체 사이트 적용”으로 바꾸지 않는다.

### 추가 수신한 AWS 최종 회신
[WEBSITE_AWS_SESSION_CURRENT.md](WEBSITE_AWS_SESSION_CURRENT.md)를 19:54 KST에 직접 읽었다. 호스팅·복구·사용자 결정·미구현 범위를 다음과 같이 보충한다. 이 값들은 AWS 세션의 검증 기록이며 본 메인이 클라우드에 접속해 다시 확인한 것은 아니다.

- 실제 호스팅: Cloudflare → AWS EC2 nginx, 원본 /usr/share/nginx/html/index.html. Workers/Pages가 아니다. CLI2.39.2·24개 AWS 스킬·MCP/STS/SSM 검증 이력이 있다. 현재 인증 유효성은 재확인하지 않았다.
- 서버 원본 백업: /var/backups/quantgen-ui/2026-10-31-eb3920403777/index.html. 복구는 후속 배포 여부·원래 소유권/권한을 먼저 확인한 뒤 별도 승인 범위에서만 수행한다. 이번 인계는 복구하지 않았다.
- 전체 원본/스크린샷/SSM 증거는 AWS 작업공간 /workspace/.cloud-setup/aws-toolkit/website-review/에 있다. 메인에서 동일 경로로 접근 가능하다고 가정하지 않는다. 공유 영수증/재구성 스크립트만 현재 패키지에 포함했다.
- 사이트 실측 light #F7F5F0/#FFFEFB/#194C40은 앱 light와 일치한다. 사이트 dark #121A16/#1A241E/#A4CFB6와 앱 dark #101915/#17231D/#91C5AC는 다르다. 통합·색상 변경은 미진행이며 현재 재개하지 않는다.
- 새 웹 확장 요청: 소개·문서·로그인 후 웹 연구 기능. 사용자 확정은 핵심 연구 기능부터(차트/지표·Quant Lab·Strategy Lab·개인 연구 저장), 누구나 가입→이메일 인증→로그인 후 자동 이용이다.
- **실시간 데이터 범위와 월 운영비는 미결정**이다. 월5만원/샘플·CSV 우선은 제안일 뿐 승인으로 기록하지 않는다. 문서 사이트·인증 리소스·회원 DB/API·웹앱은 미구현/미배포·중지 상태다.
- Strategy Lab의 공용 ledger·전역 gate를 공개 웹으로 옮기려면 사용자별 격리와 작업 프로세스 분리 검토가 필요하다. 공급사 권리 검토는 공개 시세 게시 허가가 아니다. 후속 범위·승인 없이 구현하지 않는다.
- AWS는 원본 카드68→34/성적표18→9,320px에서372→320px 가로폭, seed checksum fc3b15b2 보존을 기록했다. 과거34가설/5PASS와 연구원장·주문·앱 소스는 변경하지 않았다. 제목 반복은 접근성 텍스트/aria-hidden 표시 조합으로 판단해 유지했다.
- AWS의 패널 링크 연결 queued와 별개로 **이 메인은 해당 공유 회신을 읽었다**. Claude가 열람했다는 영수증은 여전히 없다.

## 6. 정책·양식 문서 세션
PR34 source c63ca999b686d36787c7b013e66f53bb2199c97d → main d1c56a847e975228a93aae539c8a303c467b1a5e를 수집했다. CI41175726660은 정확한 소스에서 success다.

- docs/compliance/01~20 정책·구현 기준·작성 양식·검증 기준과 정합성/문서 export 파이프라인을 반영했다.
- 기존 로컬 정합성31+다운로드16=47검사 기록, Word 본문20+양식20=40개 및 업로드101파일 검증 기록이 있다.
- [다운로드 artifact](https://github.com/xkg4real/quantgen/actions/runs/41175726660/artifacts/13032559787) SHA256181b2578f352eadd53a2b25dbd7752a58ff38c425679d08efc3be5d18b87a05d; 30일 보관 정책. 현재 다운로드 가능 여부를 이 인계에서 다시 시험하지 않았다.
- 문서 정합성 PASS와 **공개 준비 BLOCKED**를 구분한다. 결제·동의·삭제 구현, 계약/권리, 서비스 접근성 인증을 완료한 것으로 기록하지 않는다.
- 최신 RELEASE_GAPS.md의 연락처/등록정보·보유/삭제·저장보호·외부전송·요금/해지·접근성·권리 등 미확정 사항은 그대로 남는다. 비공개 사업자/계약 원문은 통합 문서에 복제하지 않는다.
- UI/번역 후속 PR에서 FACTS/source-review를 갱신한 것은 최신 코드와 문서의 정합성 반영이며 법률 승인이 아니다.

## 7. Nautilus 연구 브리지와 승인 경계
PR21은 source36df786 → 연구 브랜치 merge0510719로 병합됐다. 제품main 전체 Nautilus 통합·파일럿 완료가 아니다. 기존 O11 A2 구현을 보존했다.

- O8 추가 GPT/Gemini 심사는 **선택 사항·NOT_PERFORMED**다. 기존 Claude 심사와 AppendixB 면제 기록을 사용한다. 미실시만으로 Windows 인계를 차단하지 않는다.
- 일반 수정·검사는 승인 범위에서 포괄 승인됐지만 현재 사용자 STOP이 우선이다. 연구 판정 기준 변경, 정식 원장, 외부 공개는 별도 승인 경계를 유지한다.
- 가격 읽기 전12개 설정 등록, n_trials=12+U, U≤24를 유지한다.
- 과거 임시 저장소20검사와 CI41032685371 Windows/Ubuntu3.13 통과 기록이 있다. 실제 원장으로 실행한 증거가 아니다.
- 실제 Windows 등록/Step7A, 파일럿 공급사 대조, SPY/BTC 파일럿, 최신 실제 실행용 owner_confirmed는 미완료다. 이 통합 작업은 어떤 승인도 새로 부여하지 않았다.
- PR4 연구 누적 브랜치를 제품 main에 통째로 합치거나 PR12의 과거 누적 작업을 재병합하지 않는다.
- AUTO_STATE는 10월29일 periodic·다른 연구 브랜치 스냅샷이다. 현재 제품 재개 patch로 사용하지 않았고 수동 수정하지 않았다.

## 8. 남은 일 — 재개 지시를 받은 다음에만
| 우선 검토 범위 | 정확한 미완료/다음 안전 시작점 |
|---|---|
| 13-8/b2/c/b/b | 기타 모델·LETF·모형 주석·인라인 표시. private NATIVE_LANGUAGE_NEXT_AFTER_PR51.json의48 callsite는 후보 목록이며 완료가 아니다. 공급자/사용자/역사 원문을 일괄 번역하지 말고 원본 report·수치 회귀를 보존 |
| 13-9/b | 사용자의 실제 Windows 설치본 Claude 요청 성공 확인. 키 값 요구/출력 금지. 상태코드·모델/워크스페이스 권한·결제 오류를 안전하게 구분한 뒤 사용자 쪽 실제 인수 |
| Windows 제품 인수 | 설치/업데이트·100/125/150%DPI·키보드/스크린리더·파일dialog·작업표시줄/고정아이콘·실공급자. CI 성공으로 대체하지 않음 |
| M4-N3 / NEW-M6-02 | 금리/배당규약과 실제시장/역사카드의 근거. M4_N3_NEXT_SCOPE.json은 읽기 분석뿐. 공식판정/역사원장 변경 금지 |
| §10 / 9-1 | 나머지52그룹과 미래정보 누출 감사, 관찰행/모호매핑 대조. 완료ID를 다시 수행하지 않음 |
| ResearchRun / 제품 후속 | 모든 모델·이력·canonical identity와 offline viewer 전체 인수. 준비 산출물과 제품완료 구분 |
| 연구⑤~⑦ | Windows Step7A·공급사 대조·실제 파일럿·마감; 선행/실행승인 유지 |
| 웹사이트 | 초기 배포와 별개인 전체 C형/다크색상 통합/모바일·키보드 및 로그인 웹 연구 공간. 가입+이메일 인증은 사용자 확정; 실시간 데이터·월 예산은 미결정. 회원 DB/API/웹앱 미구현. 새 지시 없이 시작하지 않음 |
| 권리·운영 | 실제 데이터 취득/라이선스, 전문법률/운영증빙, 공개준비. 준비 문서만으로 통과 처리하지 않음 |
| TRADEGEN | read-only 브리프만 완료. 실제 연동 구현·주문 경로 변경은 하지 않음 |

Notion은 지정 sapientia 계정의 REMAINING WORK만 사용한다. 13-8·13-9 등 부모는 미완료다. PR21을 draft/미병합이라고 적은 과거 상단 이력은 연구 branch 병합 사실과 구분하고, 이번 통합은 실제 미완료 자식 범위를 완료로 바꾸지 않는다.

## 9. Claude에게 넘기는 첫 지시
1. CURRENT.md의 returned와 본 통합 인계를 읽고 사용자 STOP을 유지한다. 자료를 읽는 것과 개발 재개는 별개다. 새 재개 지시가 없다면 구현·검사 실행·병합·배포·예약 재활성화를 하지 않는다.
2. 재개가 승인되면 실제 clock, STATE transition, 같은 게시환경/private 접근, OS RUN.lock과 직전 execution/task/handoff/branch/source를 확인한다. 최신 같은 ref의 CURRENT/README/TEMPLATE/AGENTS/LEDGER/AUTO_STATE 및 UI_SESSION_CURRENT/WEBSITE_AWS_HANDOFF/WEBSITE_AWS_SESSION_CURRENT 보조 문서를 읽는다.
3. 이미 완료한 50개 하위 ID와 UI PR36/37/42/47, 정책PR34를 중복 수행하지 않는다. 최신 CURRENT blob CAS/고유 execution ID/read-back 없이 소유권을 가져오지 않는다.
4. 제품 변경은 검증된 최신 main을 기준으로 새 gpt 작업 브랜치에서 시작한다. 별도 연구 브랜치·다른 세션·실제 사이트 배포 소유권을 선점하지 않는다.
5. 전체 요청 미완료를 유지하고 각 하위 범위만 검사·커밋·CI·Notion에 기록한다. 작업 단위마다 안전 저장한다. 예약 성공·Claude 수신·실제 API/Windows 성공을 문서 저장만으로 주장하지 않는다.

## 10. 검사 재현 정보와 원자료
아래는 **재개 후 검토용 명령**이다. 이번 통합에서는 테스트를 새로 실행하지 않았다. 보호 파일/실제 원장/네트워크를 읽지 않는 합성·주입 fixture와 격리 저장소에서만 사용한다. 명령 묶음의 검사 수를 위 개수 전체와 동일하다고 가정하지 않는다.

```bash
QT_QPA_PLATFORM=offscreen python -B -m unittest tests.desktop_language_acceptance tests.desktop_fx_language_acceptance tests.desktop_carry_language_acceptance tests.desktop_rates_language_acceptance tests.desktop_bonds_portfolio_language_acceptance tests.desktop_market_diagnostics_language_acceptance -v
QT_QPA_PLATFORM=offscreen python -B -m unittest tests.letf_index_acceptance tests.desktop_letf_index_acceptance -v
QT_QPA_PLATFORM=offscreen python -B -m unittest tests.quote_coverage_acceptance tests.desktop_quote_coverage_acceptance -v
QT_QPA_PLATFORM=offscreen python -B -m unittest tests.swaption_conversion_acceptance tests.desktop_swaption_conversion_acceptance tests.ficc_boundary_acceptance -v
```

UI 최종 전체 설치 검사는 PR47 source74ae598b의 .github/workflows/runtime-smoke.yml/CI41193496809, 문서는 compliance-review.yml/CI41193496681의 정확한 명령을 따른다. O8/O11은 연구branch CI41032685371 범위를 별도로 읽는다.

private reports/2026-10-31의 CONSOLIDATION_INPUT_SNAPSHOT.json, CONSOLIDATION_INCOMING_SESSIONS.json, CONSOLIDATION_REMOTE_EVIDENCE.json, 각 단위 *_EVIDENCE.json, 과거 주간TXT·NEXT_SAFE_START를 보존했다. 비공개 원문·키·계좌·보호 캐시를 공개 인계에 올리지 않는다.

## 부록 A. 이번 주 제품/연구 PR 저장 이력
다음은 이번 통합에서 GitHub closed PR 목록으로 재조회한 원격 상태다. 행 수는 기능/테스트 완료 수가 아니다. PR16은 PR17에 흡수됐으며 PR18은 미병합 종료다. 이전 달력/서명 등 주간 선행 작업은 LEDGER 전체 이력을 유지한다.

| PR | 변경 | 대상/상태 | source → merge |
|---|---|---|---|
| [#11](https://github.com/xkg4real/quantgen/pull/11) | Gpt/UI apply main 20261029 | main / merged | e46f81fca513ca39983d31ac5131e5f6e67b0543 → 3023af3656b0b9296379d5e8ec3ef160704824cd |
| [#13](https://github.com/xkg4real/quantgen/pull/13) | Connect Research Home to analysis results and add runtime packaging CI | main / merged | fadec1c2e66b78773a3d24463d00794038891638 → 00e0488fd9f7cf7be01b3bcc51de1a5f72727cc7 |
| [#14](https://github.com/xkg4real/quantgen/pull/14) | Save ResearchRun exports to the selected desktop file | main / merged | 94121deed56993ae07b1f4e1c10eb0fb99e5a1f8 → 22ac580bb249e2b42c1d2bfae91d4e47ebc8f743 |
| [#15](https://github.com/xkg4real/quantgen/pull/15) | Use F1 browser icons and preserve Flet web startup compatibility | main / merged | 459bed0f9344350a178d61cf331f98fa07e16255 → ebb6d61fa8ee7813cca9dbd8df58cea96b80dc05 |
| [#16](https://github.com/xkg4real/quantgen/pull/16) | Add native PyQt6 research workflows while retaining Flet browser | main / merged | c401e0d581d7439cba7580aa6b5d19b0ac6a9beb → c401e0d581d7439cba7580aa6b5d19b0ac6a9beb |
| [#17](https://github.com/xkg4real/quantgen/pull/17) | Add native PyQt6 research desktop while retaining Flet browser | main / merged | e1df541b35b320bf8360e80305503f72a6043ab0 → a1adf008568aa7475a9db5ff7a5c97b41b0a12fb |
| [#18](https://github.com/xkg4real/quantgen/pull/18) | Fix BS-21 bond funding to match discount-factor accumulation | main / closed, NOT_MERGED | e8efbf7188161521711343ceb7e21215b32a255c → none |
| [#19](https://github.com/xkg4real/quantgen/pull/19) | Correct BS-21 bond funding to discount-implied repayment | main / merged | 941455aa5a0b41d0941325846dab89a05d80b5e1 → 0cc30c3ed1a7e25f1d06215a858d57bc199e9be6 |
| [#20](https://github.com/xkg4real/quantgen/pull/20) | Correct kimchi regression HAC t-statistic and record initial section10 triage | main / merged | 0e7dd782c01707b0bd3cff78c4c7deb837f761eb → ce12459eae1258e03270702092c839758cde91fa |
| [#21](https://github.com/xkg4real/quantgen/pull/21) | Add O11 registration-only initialization and apply approved O8 review scope | claude/amazing-gauss-tdiguu / merged | 36df786cb7b1395cd08bc5db2d1ad9b6244e66f3 → 0510719995e0ec3dfda8f113f826f43ca1821c6b |
| [#22](https://github.com/xkg4real/quantgen/pull/22) | Keep account holdings out of browser AI commentary | main / merged | ed521b1a8b8d0ec1ceb6715a35c03a6d7c0f9585 → 450fa00eb7739651717c8b6f118076f0a901e469 |
| [#23](https://github.com/xkg4real/quantgen/pull/23) | Correct Fama HAC uncertainty and refuse empty caplet schedules | main / merged | 468d53e97fa31574c6c2261c5044a1f2886d5c77 → ff421ea7c24e53a6e588336199c518f098690561 |
| [#24](https://github.com/xkg4real/quantgen/pull/24) | Show portfolio negative-Sharpe warnings and actual cap scope | main / merged | 71b0c9c179987f20762bb5ab01a8d6c9b813e381 → ec98cbef49f0fca90083dbbe5beca0667d382282 |
| [#25](https://github.com/xkg4real/quantgen/pull/25) | Clarify target probability as a terminal-price event | main / merged | 501bce2555e1a09873d28be8474fde621ba4e5ac → 8ebf75d4434cd119a32828607b376662eb1d6cfd |
| [#26](https://github.com/xkg4real/quantgen/pull/26) | Name sample and forecast volatility separately in both interfaces | main / merged | e55018716b3580ecc81684378d082e9c75cb6304 → 6bd4a208020998379a49acaeb1ee4a6fff3c49b3 |
| [#27](https://github.com/xkg4real/quantgen/pull/27) | Clarify strategy exposure and fix Flet equity-date alignment | main / merged | 437ca29c7439b4e27030cca3e86de39abd5538ab → 93f31a3158c4b49a348d9e91f2842e3640605fdc |
| [#28](https://github.com/xkg4real/quantgen/pull/28) | Correct negative AR(1) half-life and ETF/Crypto interpretation | main / merged | 696ee3cb9eaf5190db649be58d46754d865dc5c5 → c9a03ce9a71bf1ab81b733fd4dc40ffa6c2c1117 |
| [#29](https://github.com/xkg4real/quantgen/pull/29) | Retire invalid funding IID inference and label exploratory phase diagnostic | main / merged | 414ce3e440de0dbe977a6b3856c95f2ea8b57f70 → 39d92efb84389f6d7ae40c5502e629d52562d2bf |
| [#30](https://github.com/xkg4real/quantgen/pull/30) | Distinguish LETF variance proxies from historical realised-drag evidence | main / merged | f72b14745ff223ffab7a80afdd32f35d753ad632 → 8e4c593616a77ad5dc2911ab212b1c615d9673af |
| [#31](https://github.com/xkg4real/quantgen/pull/31) | Use the correct underlying index for leveraged ETF variance | main / merged | 55dae2fd7e6deeefa4a0a41f67f6b19d2d35e146 → d4670f3bb738147a48a5dafe34dad7628e3fe3e4 |
| [#32](https://github.com/xkg4real/quantgen/pull/32) | Report NOT_RUN and partial coverage for option quote checks | main / merged | e5a09e5beea84f48cf037f1b2d715f4904f3f341 → 118041443385cdd05fae0929172cf8eccd4b86a3 |
| [#33](https://github.com/xkg4real/quantgen/pull/33) | Include statsmodels in direct requirements installation | main / merged | b20f9b1749b483e5430b5280a8e65a0d87f3854e → e1ce7469511c6e128e6725b4d11ae28bfbbb908e |
| [#34](https://github.com/xkg4real/quantgen/pull/34) | QUANTGEN 운영 정책·양식 20종과 점검·다운로드 파이프라인 추가 | main / merged | c63ca999b686d36787c7b013e66f53bb2199c97d → d1c56a847e975228a93aae539c8a303c467b1a5e |
| [#35](https://github.com/xkg4real/quantgen/pull/35) | Preserve swaption results when comparison volatility cannot be inverted | main / merged | 4e84e992f68cf02208c2e4fff121de883dd5c99c → 94659fdd528efb34598a72b7017eda74f7d221ff |
| [#36](https://github.com/xkg4real/quantgen/pull/36) | Fix clipped price ticks and overlapping desktop chart legends | main / merged | 6d8477144dfc60c62880c131e67c3a66da7b0220 → 73131c9e74b9ec61fca88845cbdad1525ebceef9 |
| [#37](https://github.com/xkg4real/quantgen/pull/37) | Record immediate UI handoff to the website workspace | main / merged | 7a44f162a24a187146c1f5cfece260fa7556df1b → 2999296cae297da69b0198c4a72a9b49fe33ae95 |
| [#38](https://github.com/xkg4real/quantgen/pull/38) | Separate SABR solver convergence from fit diagnostics | main / merged | 743521d6d2660fd4b8ee1ef357ede1073fc8fe7a → 579aadb8fd219a25b543ea8c9a2c803d3a2cbece |
| [#39](https://github.com/xkg4real/quantgen/pull/39) | Add persistent English/Korean language switching to native desktop | main / merged | 6a82337de447279372a351185bda855b581c3c51 → f24463f4bf9fa637318dd1f1683c375d5387eef4 |
| [#40](https://github.com/xkg4real/quantgen/pull/40) | Translate native FX forward, option and SABR narratives | main / merged | ae768dc607a961bf71a8d4c57c6cd629ec78ba71 → bea069f14722b55466d21ad7a5924c4a42bbd312 |
| [#41](https://github.com/xkg4real/quantgen/pull/41) | Record verified PR40 UI change for website review | main / merged | ed51d9d8d23b068c2ced3a77ed88bd74b72d32e0 → 712e5e9770e33144e11157380f99f830d8da8fe5 |
| [#42](https://github.com/xkg4real/quantgen/pull/42) | Add aligned indicator education, source-rights review and regional UI settings | main / merged | 13308a63113743f9b4f8d6a4cf1473a9f7e7e166 → d77d99660132f71b50c19b42cc6d76dc4b5f9a79 |
| [#43](https://github.com/xkg4real/quantgen/pull/43) | Localize native carry basket summaries and disclosures | main / merged | df7ccd8f21815933ff48e105d8e6bac77937b4cf → 9d55e2ba350054759055c2f85b4332993a047e8d |
| [#44](https://github.com/xkg4real/quantgen/pull/44) | Translate native Rates result paragraphs into Korean | main / merged | 32d80824432bb28373c3c1aa17b14af60aa92cb5 → 8c9b2fc090285dfcb5a1b019685052949ced8f44 |
| [#45](https://github.com/xkg4real/quantgen/pull/45) | Record carry and Rates language changes for website review | main / merged | 7759137873917fd003413f409f85638d1f00b3a1 → c3a0613eaa6d26620d871b28f28e5ba349ff1ac9 |
| [#46](https://github.com/xkg4real/quantgen/pull/46) | Explain Claude API failures safely and clarify Nautilus/provider roles | main / merged | c47f6c0a116cad919b403568d377408452cdab69 → 13d16ae551cea65b6ac20a02a04e812de7745838 |
| [#47](https://github.com/xkg4real/quantgen/pull/47) | Apply C chart layout and QUANTGEN light/dark themes across the app | main / merged | 74ae598b8beea50c52221f5934bcd9a298b123f8 → 8c0fb632add442fd1f4d79baea239c21255324d1 |
| [#48](https://github.com/xkg4real/quantgen/pull/48) | Record PR46 website review scope and verified CI | main / merged | f369559c94a43f193e6afd5fe37f9f5f86e29bc8 → 91f6a588389282332a05b26f017eb2c84f86af47 |
| [#49](https://github.com/xkg4real/quantgen/pull/49) | Localize native Bonds and Portfolio result narratives | main / merged | 22f52dc9adaeb27e44028b0cadee3c4f76d48b0b → 4c51ab96e1f61a101fa8a76d024689830bf5d099 |
| [#50](https://github.com/xkg4real/quantgen/pull/50) | Record PR49 language changes for website review | main / merged | 5e3c0606a13daace4e490adaddf5ca43a0ea2d0b → ab6f79455da994d19d0e3b0a4415d5e32a4f4b04 |
| [#51](https://github.com/xkg4real/quantgen/pull/51) | Localize native AR1, funding and quote coverage notices | main / merged | c3e69ccc058b5c0c59c147d2fa65ba5ea3b52372 → ccf6654b7da1221e2b6bf09e019ecb6223c1e966 |
| [#52](https://github.com/xkg4real/quantgen/pull/52) | Record PR51 diagnostic language changes for website review | main / merged | 6a47cc8692a18b505fecf549013252ce61e94e68 → d7896914ee5b363ee745ef327f1ff295028edb5e |

## 부록 B. 상태 충돌을 정리한 기준
- PyQt6 전환 보류/Flet-only라는 옛 해석은 사용자 정정으로 폐기됐다. Windows=PyQt6, browser=Flet이다.
- 차트 A 기본안은 사용자 선택 C로 대체됐다. 기존 QUANTGEN 로고를 보존한다.
- PR47 open/CI대기라는 옛 체크포인트는 최신 main 병합과 CI success로 대체됐다. 실제 Windows 수동 검수는 여전히 미완료다.
- 소개사이트 “미배포”라는 UI측 문서는 초기 UI 수정 배포 영수증과 AWS 최종 회신으로 보완된다. 후속 C형 사이트·회원가입/로그인/웹 연구 작업은 완료되지 않았다.
- Notion의 초기 O11 draft/미병합 서술과 PR21 최신 연구branch 병합을 구분한다. 제품main/파일럿 완료로 확대하지 않는다.
- 문서 검사 PASS와 공개준비 BLOCKED를 동시에 유지한다.
- 과거 returned 후 자동개발 허용, 주간 창, hourly 유지 문구는 현재 사용자 STOP을 해제하지 않는다. 전체 인계의 반환은 완료 하위 작업을 보존하고 미완료를 넘기는 행위다.

