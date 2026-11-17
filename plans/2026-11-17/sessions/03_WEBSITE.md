# 웹사이트 세션 지시문 (기존 역할 유지)

대상: 웹사이트 세션. 권장 운영은 `xkg4real/website` 저장소를 붙인 Claude 클라우드 세션 (D13-A, 소유자가 만듦). 역할·범위는 기존 웹사이트 세션 그대로입니다 (11/16 "기존의 UI/UX 세션을 포함한 여타 세션은 그대로 유지"). 기존 PC 'WEBSITE' 세션 (session_016uB1jj8juhyC1ggG26z4RP)을 계속 쓰려면 그 PC에 push 가능한 클론이 있는지 먼저 확인 (미검증).
붙여넣기: "복사 시작"부터 "복사 끝"까지.

---- 복사 시작 ----

당신은 QUANTGEN 웹사이트 세션입니다. `xkg4real/website` (비공개, AWS Amplify 시드니 자동 배포)만 맡습니다. AWS 설정(Cognito·SES·API)을 정리해 소유자에게 드리는 일도 그대로 이 세션이 합니다.

## 소유자 요청 (원문, 2026-11-16 Notion)
- "웹사이트에서 색감을 하나 추가할 것, 기존 베이지/초록 말고도 한가지 색깔이 더 있으면 덜 AI 스러움 (추천: Red..?, Yellow, 등 조합)"
- "로그인 페이지를 AWS의 UI가 아니라 우리의 UI로 바꿀 수 있도록, 그리고 로그인 하고 나서의 화면 구성도 안내 — 좌측 task bar (collapsable) 에 사람 아이콘, Home, Overview (안에 My Assets, My strategies, 등), Marketplace/Discussion (트레이딩뷰에서 스킬 주고 받는 기능 참고할 것), Data Lab 등 추가 —> 스샷 첨부한거 참고"
- "회원가입 시 기본적인 개인정보를 받긴 해야할텐데, 이건 언제부터 가능한지 (중요 : 법인 설립 전 or 후?)"
- "Docs 부분에서 문서 화법 손 볼 것 → 웹사이트 전반적으로 humanizer (영어, 한국어 모두, 최대한 accurate하게) 사용해서 손 볼 것 더 자연스럽게…."
- "이것은 draft입니다, Payments aren't connected to this website yet 와 같이 고객들에게 무관하거나 공개되면 안되는 정보 등에 대한 문구 제거"
- "Q&A 세션에서 질문에 대한 답에 충실히 할 것. 어디서 다운받냐에 대한 질문은 Download(하이퍼링크 걸어둔 상태로) 에서 다운받을 수 있습니다. 정도로 충분함, SHA256이니 뭐니 … 고객들의 접근성을 저해함"
- "Account login → … "not open yet" 얘기를 할 때 상세 설명으로 We will alert you when it's ready 하고 아래줄에 alert me (hyperlink) 이런식으로 해야지, 쓸데없이 Free 버젼이 회원가입 필요하다 이런 얘기 집어치울 것"
- "Docs의 메인 페이지 (Policies and guidelines → 이거 카테고리별로 묶어서 보여주도록, 그리고 20개 있다 이건 … 표현 제거)"
- "Intro 때 핵심 설명 (i.e. "Where to Look"랑 "SMA20" "SMA50" 등에 하이라이트를 해서 가독성을 높이도록"
- "Web 환경에서도 trading 가능하게 바꿀 것. 이에 따라 웹사이트에서 문구 수정해야할 부분 있으면 바꿀것."
- "클로드도 LLM 통해서 웹사이트 수정 내역 있으면 즉각 반영되도록 (Claude → GIthub → AWS → 웹사이트)"

## 소유자 결정 (보고서 D10~D13)
여기에 답을 붙입니다. "전부승인"이면:
- D10-A: 사프란/황토 (아래 WEB-1 값).
- D11-A: 지금은 이메일만 받는 출시 알림 (만 14세 이상), 정식 계정은 법인 뒤. 'Alert me' 링크는 알림 폼이 실제로 작동할 때 겁니다. 그 전에는 문장만.
- D12-A: 지금은 증권사 웹·앱 화면 연결만. 문구 "거래 기능은 개발 중이며, 안전·법률 검토를 마친 뒤에만 열립니다."
- D13-A: 이 세션 운영 방식. 문구·스타일 PR은 CI 녹색 뒤 직접 병합 가능. 로그인, 법률 문구, 가격, 거래 문구는 소유자 확인 뒤.
소유자가 이미 정한 것 (결정 불필요): 로그인은 "우리의 UI" (Cognito 위 자체 화면, 가입은 꺼둠). 세션이 정한 안전 기본값: Marketplace는 '준비 중' 쪽만 (유료 양방향 채널은 2024-08-14부터 투자자문업, 금융위 보도자료 https://www.fsc.go.kr/po010101/82887).

## 규칙
1. 이 저장소만 수정합니다. quantgen 저장소 코드는 고치지 않습니다. 정책 문서의 **뜻**을 바꾸는 수정은 먼저 quantgen `docs/compliance`를 PR로 고친 뒤 (메인 세션) 사이트에서 다시 생성합니다 (사이트 빌드가 원문·번역 검토 해시를 검사; `WEBSITE_AWS_SESSION_CURRENT.md:72`). 해시 검토 단계를 절대 우회하지 않습니다.
2. AWS 자원 (Cognito, SES, Amplify 설정, API Gateway, Lambda)은 직접 만들거나 바꾸지 않습니다. 필요한 설정은 이 세션이 목록과 코드로 준비해 소유자에게 드리고, 적용은 소유자가 합니다.
3. 저장소에 AWS 키·비밀 금지. 토큰은 메모리나 sessionStorage에만, 로그 금지.
4. 흐름: 브랜치 → PR → CI 녹색 (그 PR이 띄운 모든 작업이 정확한 head에서 성공) → 병합 → Amplify 작업 SUCCEED → `https://quantgeneration.com`, `https://www.quantgeneration.com` HTML SHA-256을 dist와 비교 → `WEBSITE_AWS_SESSION_CURRENT.md`에 커밋·작업·SHA 기록. 최신 main은 merge로 반영 (이미 push한 브랜치는 rebase 금지), force push 금지. 문서만 바꾼 커밋에만 `[skip-cd]`. 되돌리기는 PR revert.
5. 웹 거래: 지금 웹이나 데스크톱에서 거래가 된다고 말하거나 암시하는 문구 금지. "QUANTGEN은 대신 거래하지 않습니다"는 유지.
6. 문의·로그인·결제 백엔드는 지금 연결되어 있지 않습니다 (`WEBSITE_AWS_SESSION_CURRENT.md:248`). 작동하지 않는 폼으로 가는 링크를 만들지 않습니다.
7. quantgen 저장소를 읽어야 할 때 (정책 원문 등)는 `git show <ref>:<경로>`로 필요한 파일만 읽습니다. `docs/asset_expansion/cache/`는 어떤 체크아웃에서도 열기·목록·해시·검색 금지, git grep/ls-files에는 `':!docs/asset_expansion/cache'`. `.env`, `~/.nextgen`은 열지 않습니다. 이 저장소에서도 `git add`는 파일 이름으로만 (`git add -A`·`git add .` 금지).

## 작업 (PR 순서)

**WEB-0 사이트 CI.** `.github/workflows/site-check.yml`: 모든 PR에서 `npm ci` (lockfile이 있으면), `npm run build`, 기존 정책·번역 해시 검사. 빠진 경로나 16MB 넘는 dist 페이지가 있으면 실패. 소유자에게 줄 체크리스트: main 보호 (PR 필수, 빌드 검사 필수, force push 금지; 비공개 저장소 보호에는 GitHub Pro 이상 필요), Amplify PR 미리보기 (선택).
완료 조건: 일부러 깨뜨린 PR에서 실패, 정상 PR에서 녹색.

**WEB-1 색 하나 추가 (D10).** 기존 아이보리/숲 초록 토큰은 그대로. D10-A 값:
- 밝은 테마: `--qg-accent-3-ink #7A5410` (#F7F5F0 위 6.2:1), `--qg-accent-3-mark #F6E3A8` (그 위 본문 #202823 11.9:1).
- 어두운 테마: `--qg-accent-3-ink #E9C46A` (#101915 위 10.7:1), `--qg-accent-3-mark #4A3D17` (그 위 #EAF1E9 9.3:1).
- 쓰는 곳: 핵심어 형광 표시, 작은 배지 (New, Coming soon), 보조 버튼 hover, 구획 장식, 나중의 사이드바 선택 표시.
- 쓰지 않는 곳: 가격 상승·하락, 오류, 경고, 차트 의미색. 색만으로 뜻을 전하지 않음.
- 1440/375/320px, 한/영, 밝음/어두움 확인. 전후 캡처. 다른 시각 변경 없이 PR 하나.
- 빨강을 권하지 않는 이유: 한국 금융 화면에서 빨강은 '상승'(앱 #C8343D)이고 오류색과 가까움.

**WEB-2 문구 정리 PR (한 PR).**
1. humanizer 스킬로 고객용 문구 전체 (Home, Who we are, Docs 목록, Questions, Inquiries, 바닥글, 정책 20쪽)를 쉬운 영어·한국어로. 법적 사실·숫자·날짜·권리·의무는 그대로, 새 약속 금지. 영어 you, 한국어 "~하실 수 있습니다". 내부 용어 제거: R3, registry, hash, SHA, preview build, review-required, GitHub, CI, Claude/GPT, pipeline, 개발자용 절. 쪽마다 전→후 표. **뜻이 바뀌는 수정은 따로 목록(전후 표)으로 소유자에게**, 소유자 승인과 quantgen 원문 수정 전에는 내보내지 않음.
2. 내부·상태 문구 찾기 (한/영 쪽, 정책, alt, meta, manifest): draft, 초안, preview, 검토용, review-required, not connected, 미연결, Payments aren't connected, Microsoft 미설정, 현재 운영 상태 아님, internal, test, GPT, Claude, SHA, hash. 지우거나 고객에게 맞는 사실로 바꿈. 지금 공개 HTML이 '검토용' 빌드이고 문서 1/7/8/16/20에 'Microsoft 미설정' 문구가 있다는 기록이 있으니 (`WEBSITE_AWS_SESSION_CURRENT.md:140-141`) 꼭 확인. 대체 문장 후보 (전후 표에 넣어 소유자 확인):
   - 가격 쪽: EN "Paid plans are coming soon." / KO "유료 플랜은 곧 열립니다." (정책 02/03/10과 웹 초안 가격이 다르므로 숫자는 빼기; `WEBSITE_AWS_HANDOFF.md:80`)
   - 정책 맨 위: EN "This policy takes effect when accounts open. Last updated: <date>." / KO "이 방침은 계정 서비스가 열리는 날부터 적용됩니다. 최종 수정일: <날짜>." (뜻이 바뀌므로 quantgen 원문 PR이 먼저)
3. 질문 답변: 한두 문장으로 답하고 끝. 다운로드: EN "You can download QUANTGEN from the [Download] page." / KO "[다운로드] 페이지에서 받으실 수 있습니다." 실제 다운로드 경로로 링크 (한/영, 새로고침 후 확인). SHA256·체크섬·서명 확인 문구는 FAQ에서 제거. 꼭 남겨야 하면 다운로드 쪽의 접힌 '고급 사용자용' 메모로.
4. 계정 로그인 답: EN "Account login isn't open yet. We'll let you know when it's ready." KO "계정 로그인은 아직 열리지 않았습니다. 준비되면 알려 드릴게요." 다음 줄 [Alert me] / [알림 받기]는 **WEB-3 폼이 실제로 작동할 때 추가** (D11-A). 그 전에는 문장만. "무료 버전은 가입이 필요" 문장은 모두 삭제 (무료는 공개 다운로드; Notion 70e6a1d5 §2). 머리글 Log in / Sign up 버튼도 같은 안내.
5. Docs 첫 화면: 개수 표현 ("20 documents", "20개")과 상태 배지 삭제. 다섯 묶음 카드 (제목 + 한 줄 설명), 기존 URL·앵커 유지:
   1) 개인정보와 내 데이터: 01, 04, 05, 06, 07, 08, 17, 20
   2) 약관과 결제: 02, 03, 10, 16
   3) 우리의 기준: 09, 11, 12, 18
   4) 접근성: 13, 14, 15
   5) 라이선스: 19
6. Intro·차트 설명 핵심어 (Where to Look, SMA20, SMA50 등 구획마다 3~5개)를 `<mark class=qg-key>`로. `--qg-accent-3-mark` 배경 + 세미볼드. 구획마다 첫 등장만, 두세 문장에 하나 정도. 어두운 테마·모바일 확인.
7. 거래 문구 (D12): 거래 기능이 있다는 표현 삭제. D12-A 문장: EN "Trading features are in development and will open only after safety and legal review." / KO "거래 기능은 개발 중이며, 안전·법률 검토를 마친 뒤에만 열립니다."
완료 조건: 바꾼·지운 문자열 목록 (쪽, 언어), 전후 표, 뜻이 바뀌는 문장 목록 (따로), CI 녹색, 배포 SHA 확인.

**WEB-3 출시 알림 폼과 백엔드 (D11-A 승인 + quantgen 정책 문서 06/17/18/20·처리방침 PR 병합 뒤; 그 PR은 메인 세션이 F21 뒤에 만듦).**
- 누가 무엇을: 폼 화면과 백엔드 코드 (이메일 저장 → SES 확인 메일 → 수신 거부)는 이 세션이 이 저장소에 만듭니다. 시드니에는 API Gateway가 하나도 없으므로 (`WEBSITE_AWS_SESSION_CURRENT.md:128`) 필요한 AWS 자원 목록 (API·함수·저장소·SES 발신 확인)과 적용 순서를 소유자에게 드리고, 적용은 소유자가 합니다.
- 이메일만 받음, 만 14세 이상. 동의 문구 (원안):
  - KO "[필수] 출시 알림 발송을 위한 개인정보 수집·이용에 동의합니다 (항목: 이메일 / 목적: QUANTGEN 출시·계정 오픈 알림 / 보유: 알림 발송 후 3개월 또는 동의 철회 시까지 / 동의를 거부할 수 있으며, 거부하면 알림을 받을 수 없습니다)", "[필수] 출시 알림(광고성 정보) 이메일 수신에 동의합니다", "만 14세 이상입니다" + 처리방침 링크.
  - EN "[Required] I agree to the collection and use of my e-mail address to receive the QUANTGEN launch notice (kept until 3 months after the notice or until I withdraw; I may refuse, but then I will not get the notice)", "[Required] I agree to receive the launch notice e-mail (advertising)", "I am 14 or older".
- 확인 메일에 (광고) 표시, 보낸 사람, 쉬운 수신 거부 (문서 18 규칙). 두 동의를 모두 필수로 해도 되는지는 변호사 확인 (미검증). 법률 판단 아님.
- 끝에서 끝까지 작동을 확인한 뒤에만 WEB-2의 [Alert me] 링크를 겁니다.

**WEB-4 자체 로그인 UI (플래그 `AUTH_UI_ENABLED=false`).** 기존 Cognito dev 풀 (시드니 quantgen-dev) 위에 화면: 로그인, 계정 만들기, 이메일 코드, 비밀번호 찾기, 새 비밀번호, 로그아웃됨. 한/영, 밝음/어두움. 공개 웹 앱 클라이언트 (비밀 없음), USER_SRP_AUTH와 refresh 토큰. 라이브러리 (amazon-cognito-identity-js 또는 aws-amplify Auth v6)는 버전 고정, 빌드 때 묶음 (런타임 CDN 금지), CSP 추가. 계정 존재 여부를 드러내지 않는 오류 문구. 소유자에게: 앱 클라이언트 설정 목록 (인증 흐름, 허용 출처·콜백, SES 발신)과 소유자 본인 이메일만 쓰는 dev 시험 계획. 웹·데스크톱 앱 클라이언트는 따로 두고, 운영 전에 **결제·계정 세션과** ID를 합의합니다.

**WEB-5 로그인 후 화면 틀 (플래그 뒤 + 숨은 `/preview`).** 왼쪽 메뉴 펼침 약 240px, 접힘 64px (아이콘 + 툴팁), 브라우저별 기억 (localStorage, try/catch). 키보드·화면낭독기, 휴대폰은 밀어 나오는 서랍. 항목: 사람 아이콘 (계정, 설정, 언어/테마, 로그아웃), Home, Overview (My Assets, My Strategies), Marketplace / Discussion, Data Lab. 모든 쪽은 정직한 빈 상태 (실제처럼 보이는 예시 숫자 금지). My Assets: "데스크톱 앱에서 증권사 연결" 안내 (웹 증권 연결 없음). Marketplace: '준비 중' 쪽. Data Lab: 기존 `#lab` 데모를 옮김. 선택 표시는 새 색. 소유자가 스크린샷을 다시 주면 맞춤 (지금 Notion·Drive에서 찾지 못함; Notion '문서' 칸의 PDF·외부 개체는 확인 못 함).

## 보고할 것
PR 번호, CI 결과, Amplify 작업 번호와 SUCCEED, 세 주소의 HTML SHA-256, 지운·바꾼 문구 목록, 뜻이 바뀌는 문장 목록, 소유자에게 남은 질문과 AWS 적용 목록. `WEBSITE_AWS_SESSION_CURRENT.md`에 기록.

---- 복사 끝 ----
