# QUANTGEN 웹사이트 AWS 재개 점검 — 2026-11-02

확인 시각: 2026-11-02T13:37:00+09:00
현재 범위: 사용자가 승인한 기존 소개 화면·Docs 갱신, 검증 후 사용자가 직접 반영할 단일 HTML 제공.
상태: 원본 산출물 확보 대기. 새 HTML 구현·프리뷰·배포 완료가 아님.

## 이번 AWS 세션에서 확인한 내용

- 공유 WEBSITE_AWS_HANDOFF.md / UI_SESSION_CURRENT.md 최신 섹션 및 앱 변경 큐 PR54/58/59/60을 읽었다. PR61은 조회 당시 OPEN, head `5b52e3dd041b39c020b4e862f807c4a1a322eb82`, main은 `8b4010430a9ece2a4e1b05b234abe81d3796771f`였다. PR61을 병합 완료로 취급하지 않는다.
- 해당 main의 registry·정책 20종 및 관련 사실/큐 기록을 별도 로컬 snapshot으로 확보했다. 32개 파일의 Git blob SHA를 대조하여 원격과 바이트 일치를 확인했다. HTML 기존 기준 `cac727e2` 이후 정책 14종(01/02/04/06/07/08/09/11/12/13/14/15/19/20)이 변경됐다. 정책 20종은 모두 review-required다. 이는 공개 번역 정합성 통과가 아니다.
- 지정된 `/workspace/work/quantgen-web-redesign-20261102` 및 해당 HTML/ZIP은 이 AWS 환경에 없다. /workspace, /home/agent, /tmp의 파일명 검색과 Library/shared 경로에서도 발견되지 않았다. 지원 앱 도구의 다른 UI 스레드 조회는 빈 결과 또는 연결 종료로 실패했다. 원본을 새 디자인으로 대체하지 않았다.
- 사용자에게 기존 `QUANTGEN-source-and-handoff-2026-11-02.zip`의 접근 가능한 다운로드 링크를 요청한 상태다. 원본 HTML 예상값은 5,506,989 bytes / SHA256 `ce48aea091f482ad834fdf836ae71528731e92ddbd90b1d5b2bc372fd8fcc609`이며 아직 로컬 검증하지 못했다.
- AWS setup-state와 CLI 설치 ZIP 존재, CLI 2.39.2, 설치 AWS 스킬 24개를 확인했다. 최신 환경의 aws-mcp.us-east-1.api.aws 허용 설정과 실제 TLS 검증된 HTTP 405 응답을 확인했다. 인증된 MCP API 성공을 뜻하지 않는다.
- 기존 quantgen 프로필의 STS 호출은 “Your session has expired”로 실패했다. 새 로그인·비밀번호·액세스 키를 요청하지 않았으며 운영 서버의 현재 소스/라우팅 재조회는 미완료다. HTML 편집 자체에 새 AWS 인증이 필요한 것은 아니다.
- 보존된 10월31일 운영 소스는 `/workspace/.cloud-setup/aws-toolkit/website-review/site/index.html`, SHA256 `d3dcc4f48dd2355fc7e748f30b75135992043a0e9933dc13f40d7355d624ca02`다. 연구 설명/브라우저 시뮬레이션, #lab/#gate/#strategies 등 기존 앵커와 qg-theme 저장을 확인했다. 이 snapshot에는 Q-SCORE 연구 목록이 없다. 11월2일 실제 origin의 최신 바이트로 단정하지 않는다.
- 공개 웹 조회의 캐시 화면도 기존 Record/Rules/Quant Lab/Gate/Strategy Lab/Desk/Reproduce/Contribute 구성을 보여준다. 캐시 조회를 새 배포 검증으로 취급하지 않는다.
- 앱 저장소 /workspace/quantgen, /workspace/tradegen은 git status 기준 변경 없음. 웹 HTML/소스는 GitHub에 게시하지 않았다. CURRENT/LEDGER/AUTO_STATE 소유권·파일은 변경하지 않았다.

## 가격 정책 충돌과 다음 적용 기준

main의 02/03/10 문서는 Research 월29,000원 / Pro 월59,000원 / Team Pilot 월290,000원 및 VAT 포함·월 자동 갱신·Team Pilot 최대5인을 기재한다. 이번 사용자 웹 지시는 Free / Pro 월59,000원 / Ultra 월129,000원과 승인된 기능 초안이다. 최신 사용자 지시를 웹 초안 기준으로 삼되, 기존 Research/Team Pilot의 세금·갱신·인원 조건을 Free/Ultra로 임의 이식하거나 두 상품 구성을 하나의 현재 계약으로 혼합하면 안 된다. KO/EN 공개 본문에 같은 해석을 적용하고 출처 대비 차이를 버전 기록에 남겨야 한다. 법정 권리와 협의 중인 추가 환불 혜택도 구분한다.

## 작업 상태와 다음 순서

| 구분 | 상태 |
|---|---|
| 원문/기존 환경 사전 확인 | 위 범위 완료 |
| 기존 redesign 원본 확보·해시 검증 | 미완료 |
| 공개 KO/EN 40본문 개정 | 미완료 |
| HTML 묶음/모바일·테마·키보드·Docs 회귀 검사 | 미실행 |
| 최신 HTML 다운로드 파일·최종 SHA256 | 아직 없음 |
| 운영 반영·배포 후 URL 검증 | 미실행; 이번 사용자 직접 업로드 방식 유지 |

1. 기존 ZIP을 복구하고 최초 HTML 크기/해시부터 대조한다. site, public-docs, tools, 기존 디자인 스킬/규칙을 읽고 수정한다.
2. 재개 시 최신 main/PR61 상태를 다시 읽는다. 현재 main 원문과 공개 번역 차이, 위 상품 조건 충돌을 정리한다. 내부 운영표/승인서 양식은 공개 본문에 복사하지 않는다.
3. 기존 연구 경로·테마 키를 보존하는 연결을 검사하고, review-required 표시와 같은 문서 언어 전환·직접 URL·footer 경로를 검증한다. 실제 웹에 Q-SCORE 목록이 없다면 실시간 표를 새로 만들지 않는다.
4. 실제 제공된 스크립트 옵션을 확인한 뒤 build/check/source-root/bundle/browser 검사를 수행한다. 기존 보고서를 이번 파일의 검사 통과로 재사용하지 않는다.
5. 새 단일 HTML, SHA256, 사용자 업로드 안내를 전달한다. 이전에 확인한 서버 파일 경로는 /usr/share/nginx/html/index.html이고 복구본은 /var/backups/quantgen-ui/2026-10-31-eb3920403777/index.html이다. 현재 서버 상태 대조 없이 덮어쓰기하지 않는다.

로컬 준비 자료: `/workspace/work/quantgen-web-resume-20261102`
- `source-main/docs/compliance/`: main 고정 ref의 원문 snapshot
- `evidence/verified-source-manifest.json`: 원문 Git blob 및 SHA256
- `evidence/policy-preflight.json`: 20종 버전/상태·14종 변경 목록
- `evidence/retained-website-inventory.json`: 보존된 10월31일 웹 source 구조
- `evidence/PR61.json`, `evidence/compare-cac727e2-to-main.json`

---

<details>
<summary>이전 2026-10-31 중단·배포 인계 기록 (역사 기록)</summary>

# QUANTGEN 웹사이트(AWS) → QUANTGEN 메인세션 인계

작성일: 2026-10-31  
발신 세션: QUANTGEN 웹사이트 (AWS)  
수신 세션: QUANTGEN 메인세션 (`01a183c6-632a-70cc-a0e6-32e764f43087`)  
상태: **사용자 지시로 개발·추가 배포 중단. 완료 결과 보존 및 통합 인계만 진행.**

## 메인 세션이 우선 반영할 상태

- https://quantgeneration.com/ 의 **초기 소개사이트 UI 버그 수정은 실제 배포 완료**입니다. 버전 `2026-10-31.1`, 배포 시각 2026-10-31 07:26:02 UTC.
- **후속 C형 전체 차트 통일, PR42/47 앱 기능의 웹 이식, documentation·회원가입·로그인·웹 연구 공간은 미구현/미배포**입니다. 초기 UI 배포를 이 후속 작업의 완료로 집계하면 안 됩니다.
- 중단 이후 이 AWS 세션에서 새 기능 구현·클라우드 설정 변경·추가 사이트 배포를 하지 않았습니다. 인계 자료 보존만 수행합니다.
- 메인 세션의 CURRENT 소유권·execution ID·연구 원장·자동 예약은 이 회신에서 변경하지 않았습니다. 별도 사용자 재개 지시 없이 개발을 재개하지 마세요.

## 실제 완료한 UI 수정

1. 저장된 HTML 위에 JavaScript가 카드를 다시 추가하던 문제: 모델 카드/축약 카드 각각 68→34, 성적표 행 18→9. 첫 카드 클릭과 방향키 이동 복구.
2. 저장된 내비게이션·테마·필터 장식의 중복 생성 및 오래된 좌표 제거.
3. 모바일에서 12열 그리드의 간격이 남아 발생한 가로 넘침 수정. 320px 화면의 페이지 폭 372→320; 390px/150% 배율 모사 조건은 372→260.
4. Canvas DPR 2 제한 제거, 실제 DPR 대응. 큰 가격 축 여백을 글자 폭으로 계산하고 좁은 차트 설명의 잘림·겹침 보완.
5. 존재하지 않는 saved-page 분석 스크립트 참조 제거. Cloudflare가 실제로 주입하는 분석 스크립트는 유지.

기존 로고·글꼴 정의·색상, 과거 34개 가설/5 PASS 및 날짜, study JSON·시드 계산 엔진·gate 검사는 보존했습니다. 연구 원장·주문 경로·앱 소스는 변경하지 않았습니다. 제목 반복은 접근성 텍스트와 aria-hidden 시각 단어의 조합으로 확인되어 변경하지 않았습니다.

## 검증과 배포 증거

- PC 1600/1366, 모바일 390/320 및 125/150% 배율 모사 포함 7조건 통과. 수동 브라우저 확대 검수라는 주장은 아닙니다.
- 애니메이션 활성·라이트/다크·메뉴·필터·앵커 4조건, 큰 가격 숫자 4조건 통과. 카드 클릭·키보드 이동·시드 재실행 검증.
- 실행 예외/콘솔 오류/누락된 애플리케이션 자원 없음. 원래 비활성인 복사·다운로드·외부 링크는 동작 검수 완료로 집계하지 않았습니다.
- 동일 시드 checksum `fc3b15b2` 및 표시 수치 일치. study/engine/gate/font의 원본 해시 불변.
- 브라우저 검수는 운영 원본의 정확한 로컬 사본에서 수행. 실제 공개 HTTPS는 별도로 HTTP 200, 버전 표식, CSS 2블록 및 인라인 script 3블록 일치를 확인했습니다. Cloudflare 상태 DYNAMIC.
- 공개 HTML은 Cloudflare 분석 스크립트 주입 때문에 원본과 전체 바이트 해시가 다르며, 앱 JS/CSS 일치로 배포 확인했습니다.
- [기계 판독 배포·검증 기록](website-ui/2026-10-31.1/deployment-receipt.json)
- [완료 코드 재구성 스크립트](website-ui/2026-10-31.1/rebuild_ui.py): 원본 SHA와 결과 SHA를 모두 검사하며 입력을 덮어쓰지 않고 지정 출력만 생성합니다. **배포하거나 새 UI를 개발하는 도구가 아닙니다.**

## 호스팅·소스·복구

실제 배포는 Cloudflare → AWS EC2 nginx이며 원본은 `/usr/share/nginx/html/index.html`입니다. Workers/Pages 프로젝트가 아닙니다. AWS 프로필 `quantgen`, 리전 `ap-southeast-2`; CLI 2.39.2, AWS 스킬 24개, MCP·STS·SSM 원격 실행 검증 완료 기록이 있습니다. 자격증명은 공유하지 않습니다.

- 변경 전 SHA256: `eb392040377722562ee5d5ca175629c2156186c5bd55a3aec9792dce8b2a643f`
- 배포 SHA256: `d3dcc4f48dd2355fc7e748f30b75135992043a0e9933dc13f40d7355d624ca02`
- 배포 전 원본은 **서버** `/var/backups/quantgen-ui/2026-10-31-eb3920403777/index.html`에 보존되어 있습니다. 복구 시 후속 배포가 없는지 먼저 확인하고 원래 소유권·권한을 유지합니다.
- 로컬 검토 커밋 `5cd022145bf34d993fbcc7f92242895b57cf2598`은 AWS 작업공간의 독립 사이트 저장소에만 있습니다. 앱 main의 커밋/PR이 아닙니다.
- 전체 원본/스크린샷/SSM 증거는 **AWS 세션 작업공간** `/workspace/.cloud-setup/aws-toolkit/website-review/`에 있습니다. 메인 세션의 같은 경로에 존재한다고 가정하지 마세요. 이번에 재구성 코드와 배포 영수증을 공유 GitHub에 보존했습니다.
- 사이트 토큰: light bg `#F7F5F0`, surface `#FFFEFB`, accent `#194C40`; dark bg `#121A16`, surface `#1A241E`, accent `#A4CFB6`. 이 배포의 실제 CSS에서 확인한 값입니다. 앱 C형 테마와의 새 통합은 미진행입니다.

## 보류된 웹 확장 요구와 사용자 결정

사용자는 QuantConnect처럼 소개·문서·로그인 후 웹 기능을 같은 사이트에서 제공하고 기존 로고·글꼴을 유지하기를 원했습니다. 확정 답변은 다음 두 가지입니다.

- 첫 버전: 차트·지표 가이드, Quant Lab, Strategy Lab, 개인 연구 저장 등 **핵심 연구 기능부터**.
- 접근: **누구나 가입 → 이메일 인증 → 로그인 후 자동 이용**.

실시간 데이터 범위와 월 운영비 질문에는 확정 답변이 없었습니다. 월 5만원이나 샘플/CSV 우선은 제안일 뿐 사용자 승인으로 집계하지 마세요. 인증 리소스/회원 DB/API/웹앱은 아직 생성하지 않았습니다.

검토 과정에서 앱의 개발용 Flet ASGI 실행기와 UI 독립 Quant Lab/Strategy Lab 코어를 확인했습니다. Strategy Lab은 공용 ledger 경로와 전역 gate 설정을 사용하므로 공개 웹 이식 시 사용자별 격리와 작업 프로세스 분리가 필요합니다. 최신 공급사 이용권 검토는 공개 시세 게시 승인과 다릅니다. 이 항목들은 후속 구현 근거이며 지금 재개할 작업 지시가 아닙니다.

## 인계 방식

사용자가 지정한 QUANTGEN 메인세션을 실제 thread 목록에서 확인했고, 해당 세션이 읽고 있는 `handoff/WEBSITE_AWS_HANDOFF.md`에 이 회신 링크를 연결했습니다. 이 자료를 UI_SESSION_CURRENT.md와 함께 통합 인수인계에 포함하세요. 공유 GitHub 보존/패널 연결과 메인 에이전트의 열람 확인은 구분합니다.

</details>
