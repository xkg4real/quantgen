# 2026-11-13 웹사이트 작업 재개 — 인계 대조 완료 / 최신 소스 대기

사용자의 재개 요청과 첨부 `QUANTGEN_WEBSITE_GPT_HANDOFF_2026-11-12.md`를 기준으로 워크플로우를 수립했습니다. 이번 인계의 핵심은 **Gmail 문의 메일 경로를 Microsoft 365로 전환하고 웹 정책 한영 문구를 정렬하는 작업**입니다.

## W1 완료: 인계·출시 계획·현재 환경 대조
- main `9e00bf326acbfd512d6479026946358967dfc078`, handoff 조회 head `7e2d40d5cfc6b2c641d77c51920de205f8792ba2`. 웹 공통 인계 최신은 11/7, 이 파일의 이전 최신은 11/2였습니다.
- Notion [launch plan](https://app.notion.com/p/68c577d259f847798171caad8a546c1d), [REMAINING WORK](https://app.notion.com/p/4065c916fe0c80d2af08c0e7f68817fa), [DEPLOY_EN](https://app.notion.com/p/55b5c916fe0c83319a24817a27c21bad)을 대조했습니다. 11/10 배포 안내/HTML 해시 기록은 실제 공개 URL 검증 완료로 간주하지 않습니다.
- 현재 환경에 11/11 privacy HTML, `_build/`, 11/3 motion 기준 HTML이 없습니다. GitHub main/handoff 전체 tree 및 Releases에도 없어 사용자에게 최신 ZIP을 요청했습니다. 11/2 파일을 최신 원본으로 대체하지 않습니다.
- 첨부 인계의 Gmail 초안 예상값: 8,619,355 bytes / SHA256 `de434d3a19fd9648009b978dc841d566dde46addbc49bce60349b33b5b5685c8`. 아직 실물 검증 전이며 첨부에 따르면 미배포입니다.
- 사용자 확인: Microsoft 365 구매·설정 전. 설정과 송수신 검증 전 Microsoft 처리방침을 운영에 게시하지 않습니다.
- AWS CLI2.39.2 존재, 기존 quantgen STS는 session expired. MCP endpoint TLS/HTTP405 도달은 확인했지만 인증된 MCP 성공은 미확인. 운영 도메인의 환경 프록시 CONNECT403은 사이트 장애 증거가 아닙니다.
- Sydney `ap-southeast-2` 유지. Launch plan의 Seoul/이전 support 메일 및 결제 계획은 최신 실제 리소스·사용자 결정과 재대조해야 합니다.
- 앱 UI PR112는 별도 GPT UI 세션 작업(조회 당시 OPEN/head `c45adc8dca1682069d9c88956c844f5c33b7d827`). 이번 웹 작업에서 인수·병합하지 않았습니다.
- [karpathy-guidelines](https://github.com/multica-ai/andrej-karpathy-skills/blob/main/skills/karpathy-guidelines/SKILL.md) blob `6a62d0441753157ca6ca50479e490c2948033adb`를 읽고 최소 변경·명시적 가정·검증 기준을 반영했습니다.

## 다음 작업과 의존성
1. W2: 공식 Microsoft/Cloudflare 자료로 설정 가이드와 KO/EN 정책 변경 초안 검토.
2. W3–W6: 최신 ZIP 확보·해시 대조 → 정책 수정 → 기존 3개 검사/모바일 표/한영/테마 회귀 → 단일 HTML·SHA·변경내역·현 운영본 기준 업로드/복구 안내.
3. W7: 웹 기록만 GitHub handoff에 누적하고 Notion 기존 REMAINING WORK에 완료/대기를 분리하여 갱신.
4. W8: 실제 Microsoft 설정·메일 경로·미확정 공개 조건 해결 후 운영 적용. 현재 미착수.
5. Notion Track A의 추가 개발 연결(Cognito/SES/API)은 별도 클릭 질문으로 범위 확인 중. 신규 과금 리소스와 공개 출시 승인을 추정하지 않습니다.

로컬 작업표: `/workspace/work/quantgen-web-20261113/WORKFLOW.md`, `TASK_LOG.md`.
**현재 완료는 인계 대조·작업 흐름 수립입니다. 새 HTML 구현/프리뷰/운영 배포/공개 가입 검증은 완료되지 않았습니다.** 웹 소스/HTML·비밀값은 GitHub 비게시. 메인 CURRENT/LEDGER/AUTO_STATE와 타 세션 checkpoint는 보존했습니다.

---

# 2026-11-02 AWS 웹 HTML 갱신 완료 — 사용자 수동 적용 대기

원본 ZIP을 사용자 첨부로 확보하고 인계 HTML SHA256 ce48aea0… 일치를 확인했습니다. 소개 화면·Docs20종 KO/EN을 현재 main `8b4010430a9ece2a4e1b05b234abe81d3796771f` 기준으로 갱신하고 최종 단일 HTML 검증을 완료했습니다. **운영 배포 및 공개 URL의 새 버전 확인은 아직 실행하지 않았습니다.**

- 최종 HTML: `QUANTGEN-website-ready-2026-11-02.html`, 8,462,984 bytes.
- SHA256: `b6664cd4889da06a3b47aed62ea26c61f9584bd913ff3faf80e56d25c7890656`.
- 전달 폴더: `/workspace/outputs/quantgen-20261102`.
- 사용자 업로드 ZIP: `QUANTGEN-AWS-upload-2026-11-02.zip` (HTML/manifest/manual_aws_upload.py/AWS_UPLOAD_KO.md).
- 편집용 보관 ZIP: `QUANTGEN-updated-source-2026-11-02.zip`. 웹 HTML/소스는 GitHub에 올리지 않았습니다. 별도 환경에서는 사용자가 전달받은 ZIP으로 복구해야 합니다.
- 편집 폴더: `/workspace/work/quantgen-web-redesign-20261102/QUANTGEN-website-2026-11-02`; 전체 수정 내역과 범위는 로컬 `FINAL_DELIVERY.md`에 있습니다.

## 완료 및 검증

정책20종/40번역의 원문·번역 hash/revision .3 갱신, main 대조 PASS. 실제 원문 변경 주입에서 양쪽 번역의 재검토 요구 PASS. 모든 정책은 preview/review-required 상태를 유지합니다. 현재 웹 Free/Pro/Ultra 초안과 이전 Research/Pro/Team Pilot 조건을 혼합하지 않았습니다.

Docs40본문·표 전체 렌더링, 320px 긴 본문/표, 같은 문서 언어 전환·직접 URL·새로고침·하단5링크·키보드·없는 번역/미지원 언어 안내 PASS. 한영/테마/6폭의 168 경로, 차트64조합, 삽입자산66개의 UTF-8 바이트 일치 및 SVG 글자 영역 검사가 PASS입니다. 기존 연구8경로·seed 변경 재계산·입력/언어/테마 유지도 PASS; 검사 중 브라우저 예외·외부 자산 요청 0입니다.

기존 #lab/#gate/#strategies 등은 원문을 보존한 영어 교육 연구 데모로 열립니다. 원본 source SHA d3dcc4f48dd2355fc7e748f30b75135992043a0e9933dc13f40d7355d624ca02를 별도 iframe에 보존했고 계산 엔진은 바꾸지 않았습니다. 프레임은 scripts/forms만 허용하고 same-origin과 외부 연결/폼 전송은 막습니다. 한글 차트 인코딩, 중첩 HTML의 script 문법, 모바일 긴 문자열, 테마 변경 시 스크롤·Auto 유지 문제를 수정했습니다. 기존 브랜드/글꼴/차트69자산은 ZIP과 같습니다.

마지막 조회한 PR61은 OPEN/head `4e17087b1de5dfc01e5f03485088c316f22b0710`입니다. 작업 중 추가된 종목 재무표·Pretendard 변경도 확인했으나 대응 웹 Q-SCORE 목록이 없어 실시간 표를 만들지 않았고 기존 웹 글꼴을 보존했습니다. 정책은 현재 main 기준이며 미병합 PR을 적용 완료로 표시하지 않습니다. main이 바뀌면 원문/번역 재검토 검사를 다시 실행해야 합니다.

## 운영 반영과 남은 범위

AWS_UPLOAD_KO.md: AWS Console 로그인 → Sydney CloudShell → ZIP 업로드/해시 검증 → stage → 공개 미리보기 확인 → apply(백업/원자 교체) → 공개 URL 확인 → 필요시 rollback 순서입니다. 실제 AWS 호출0회; 수동도구의 로컬 안전검사8개 PASS입니다.

기존 quantgen 인증은 만료 상태이며 최신 origin 소스 재조회는 미완료입니다. apply는 검토한 기존 원본 SHA와 현재 index가 다르거나 staging 이후 바뀌면 거부합니다. 운영본 백업은 /var/backups/quantgen-manual/<전송 ID>/index.html, 대상은 /usr/share/nginx/html/index.html입니다. 새 버킷·IAM·액세스 키 없이 기존 SSM을 사용합니다.

확인 예정 URL: https://quantgeneration.com/?lang=ko#/ , https://quantgeneration.com/?lang=en#/docs/privacy-policy , https://quantgeneration.com/#lab . 아직 이 최종 HTML의 공개 배포 확인 URL로 집계하지 않습니다.

Login/Sign Up·문의·결제 백엔드는 미연결이며, 회원 인증 후 실제 웹 연구 서비스를 제공하는 단계는 별도 미완료입니다. 공개 정책 프리뷰는 법률/시행 승인이 아닙니다.

공유 인계 기록만 갱신했습니다. 메인 CURRENT/LEDGER/AUTO_STATE 소유권과 앱 저장소는 변경하지 않았습니다.


<details>
<summary>이전 사전 점검 및 역사 기록</summary>

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

</details>
