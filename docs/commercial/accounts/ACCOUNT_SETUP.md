# QUANTGEN 회원 계정 설정 묶음

- 판: v0.3.3 (2026-11-20, 소유자 결정 OA-44 "2로 권장합니다": P8 두 번째 확인을 할 수 없으면 동의 뒤 계정 삭제·같은 이메일 재가입 (`ADMIN_GUIDE.md` 6.2), 3부 ACC-4 거절 안내 문구와 ACC-9 재가입 시험). v0.3.2 (2026-11-20, 계정 문서 고침 KEY-4/a: P8 두 번째 확인 방법 (메일함에서 읽을 수 없는 것; 로그인 IP 대조는 회원 식별 확인 뒤), 3부 ACC-4 거절 종류를 오류 이름으로·ACC-9 새 두 경로 시험, L1 실제 버킷, 4.2 보안 기록 칸의 회원 식별 미검증 (소유자 시험 T14)). v0.3.1 (2026-11-20, PR #133 3차 검토 A4·A5·B3: 3부 ACC-3 새 비밀번호 단계·ACC-4 거절 안내, P8 두 번째 확인 (소유자 결정 2026-11-20), 2부 1·15단계, 0.1 5번 두 계정, 4.6). v0.3 (2026-11-19, 소유자 결정: P10 비밀번호 특수문자 요구, 12번 HTML 인증 메일; 3부 ACC-1 비밀번호 규칙 문구도 바뀌어 D11 4장 원문과 그 한 곳이 다름 — 4.6 참고). v0.2 (2026-11-18, 소유자 답 Q1~Q3 반영). v0.1 2026-11-17. 작성: PAYMENTS_ACCOUNT_KEYS 세션. ID `PAY-A2`.
- 바탕: handoff `plans/2026-11-17/D11_ACCOUNTS_AND_ADMIN_GUIDE.md` 2·3·4장. 관리 방법은 `docs/commercial/accounts/ADMIN_GUIDE.md`.
- 네 부분: **1부** 운영 풀 설정표 · **2부** 소유자 AWS 순서 (25단계) · **3부** 웹사이트 세션 요청 (복사용) · **4부** 메인 정책 문서 PR에 넣을 값.
- 소유자 결정 3개(0절)는 2026-11-18에 답을 받아 채웠습니다. 운영자 이름은 0.1절 한 곳에서만 정합니다.
- 확인 상태 표시: **확인** (AWS 문서·법령 해설, 검색 요약 2026-11-17) / **부분 확인** / **미검증** / **제안** (이 세션이 고른 값). AWS 문서 사이트(`docs.aws.amazon.com`)는 이 세션 네트워크에서 막혀 있어 직접 열지 못했습니다.
- 법률 내용은 **법률 자문이 아닙니다**. 근거는 문장 뒤 〔 〕.

## 0. 진행 순서와 소유자 결정 3개

D11 0장 순서 그대로입니다. 앞 단계가 끝나야 다음으로 갑니다.

| # | 누가 | 무엇 | 끝난 기준 |
|---|---|---|---|
| 1 | 소유자 | 아래 결정 3개 답 | **끝남 (2026-11-18)** |
| 2 | 메인 세션 | 정책 문서 PR (4부 값) | PR 병합 |
| 3 | 소유자 | AWS 2부 순서 (실행 안내: `OWNER_STEPS.md`) | 풀 ID·클라이언트 ID를 웹사이트 세션에 전달 |
| 4 | 웹사이트 세션 | 3부 요청 구현, 플래그 꺼짐 (`AUTH_UI_ENABLED=false`) | CI 녹색, 플래그 꺼짐 |
| 5 | 소유자 | 관리자 안내서 부록 A 공개 전 체크 8개 | 전부 통과 |
| 6 | 소유자 | 법률 확인 1회 (118 또는 변호사) | 메모 한 줄 |
| 7 | 웹사이트 세션 | 플래그 켜기 = 공개 | 공개 주소에서 가입 성공 |

**소유자 결정 3개 (한 줄 질문)**

| # | 질문 | 권장 답 | 자리표시 |
|---|---|---|---|
| Q1 운영자 표기 | 공개 문서의 운영자를 "(주)넥스트제너레이션"에서 **소유자 개인 성명 + 서비스명 QUANTGEN**으로 바꿀까요? 〔법률 자문이 아닙니다. 근거: 상법 제20조·제28조 (회사 아닌 자의 상호에 회사 표시 금지, 200만 원 이하 과태료) · https://korea.legal/wiki/상법-제20조/ · https://korea.legal/wiki/상법-제28조/ · 2026-11-17 메인 D11 확인〕 | **답 (2026-11-18): 예.** "다만 제가 법인 설립 설립이 완료되었다고 여기에 말하는 순간 바로 해당 법인 명으로 수정 가능하도록 해주세요" → 0.1절 | 0.1절 **운영자 표기** |
| Q2 개인정보 메일함 | 열람·삭제 요청을 실제로 받을 주소를 무엇으로 할까요? (예: `privacy@quantgeneration.com` → 소유자 메일함 전달. Microsoft 365 없음, 전달 방식은 웹사이트 세션 메일 작업과 맞춤) | **답 (2026-11-18): `contact@quantgeneration.com`** ("현재 웹사이트의 구조도 이렇게 되어있습니다"). 개인정보 요청과 일반 문의를 한 주소로 받음 | `contact@quantgeneration.com` |
| Q3 최소 연령 | 무료 회원 최소 연령을 **만 14세 이상 (본인 진술 체크)**, 유료는 나중에 만 19세로 할까요? 〔법률 자문이 아닙니다. 근거: 개인정보 보호법 제22조의2 (만 14세 미만은 법정대리인 동의, 원문 미확인), 민법 제5조 (미성년자 계약 취소) · 해설 URL 미확보 → https://www.law.go.kr 확인 필요 · 2026-11-17 메인 D11 2.4절〕 | **답 (2026-11-18): 예** (무료 만 14세, 유료 만 19세) | 14 |

### 0.1 운영자 표기 (한 곳에서 정함)

이 문서와 관리자 안내서의 "**운영자 표기**"는 아래 값 하나를 뜻합니다.

| 시기 | 운영자 표기 | 상호의 회사 표시 |
|---|---|---|
| **지금 (개인 운영)** | 소유자 개인 성명 + 서비스명 QUANTGEN. 성명은 main `docs/compliance/release-profile.json`의 `operator.representative`와 같은 사람 (이 문서에는 이름을 다시 적지 않음) | 쓰지 않음 ("(주)" 없음) |
| **법인 설립 뒤** | 소유자가 알려 주는 법인 등기상 이름 | 등기된 이름 그대로 |

**법인 전환 절차 (소유자가 "법인 설립 완료: <법인명>"이라고 말하면)**

| # | 누가 | 할 일 | 걸리는 시간 |
|---|---|---|---|
| 1 | 이 세션 | 위 표의 "지금" 행을 법인명으로 바꾸고, `ACCOUNT_SETUP.md`·`ADMIN_GUIDE.md`를 새 판으로 push. 메인에게 바꿀 값 목록 전달 (아래 2번의 칸) | 같은 날 |
| 2 | 메인 세션 | 정책 문서 PR: `release-profile.json` `operator.legal_name`, `01`·`02`·`16`의 운영자·책임자·계약 주체, 사업자등록번호·통신판매업 신고번호 (받은 뒤) | PR 1개 |
| 3 | 웹사이트 세션 | 정책 원문 다시 생성 (직접 문구를 만들지 않음) | 메인 PR 병합 뒤 |
| 4 | 소유자 | **회원이 이미 있으면**: 회원 정보를 법인으로 넘기기 **전에** 회원에게 알림 (관리자 안내서 부록 B). 알림 없이 이름만 바꾸면 안 됨 | 알림 뒤 (홈페이지 게시라면 30일 이상) |
| 5 | 소유자 | AWS 계정 **두 개 모두** (프로젝트 계정 Golden Hour Code, 관리 계정) 명의·결제 주체를 법인으로 (별도 절차, handoff `INCORPORATION_CHECKLIST.md` B1·B2). 사용자 풀은 그대로 | AWS 안내대로 |

- 1~3은 문서 값만 바꾸면 되어 바로 할 수 있습니다. 앱이나 AWS 구조는 바꾸지 않습니다.
- 4는 법 절차라 "바로"가 안 될 수 있습니다. 공개 전(회원 0명)에 법인이 생기면 4는 필요 없습니다. 〔법률 자문이 아닙니다. 근거: 개인정보 보호법 제27조, 시행령 제29조 · https://itwiki.kr/w/개인정보_보호법_제27조 · 2026-11-17 메인 D11 확인〕
- 법인 등기 전에는 "(주)" 등 회사 표시를 쓰지 않습니다. 〔법률 자문이 아닙니다. 근거: 상법 제20조·제28조 · https://korea.legal/wiki/상법-제20조/ · 2026-11-17 메인 D11 확인〕

---

## 1부. 운영 풀 `quantgen-prod` 설정표

새 풀을 만듭니다. 개발 풀 `quantgen-dev` (ID `ap-southeast-2_fV38AjJFg`)은 시험용으로 남기고 다시 쓰지 않습니다. 로그인 아이디와 필수 속성은 풀을 만든 뒤 바꿀 수 없는데, 개발 풀의 그 설정을 아무도 확인하지 않았기 때문입니다 (**확인**: 변경 불가).

### 1.1 사용자 풀

| # | 설정 | 값 | 나중에 바꿀 수 있나 | 확인 상태 |
|---|---|---|---|---|
| P1 | 리전 | `ap-southeast-2` (시드니). SES·Amplify와 같은 리전 | 아니요 (새 풀 필요) | 확인 (리전 고정은 일반 사실) |
| P2 | 풀 이름 | `quantgen-prod` | 미검증 (만들 때 정확히 입력) | 미검증 |
| P3 | 요금제 | **Essentials** (새 풀 기본값). 월 활동 회원 1만 명까지 무료, 넘으면 1명당 약 $0.015 | 예, 언제든 | 확인 (무료 범위·기본값은 검색 요약, 조직 단위 집계 방식 미검증) |
| P4 | 로그인 아이디 | **이메일만** (대소문자 구분 안 함). 사용자 이름 따로 안 받음 | **아니요** | 확인 |
| P5 | 필수 속성 | **email 하나만** | **아니요** | 확인 |
| P6 | 스스로 가입 | 켬 (**Enable self-registration**) | 예 | 확인 (토글 경로 확인) |
| P7 | 가입 확인 | Cognito가 이메일 코드로 확인 (자동 확인 켬) | 예 | 부분 확인 (문구 미검증) |
| P8 | 계정 복구 | Self-service 켬, **Email if available, otherwise SMS** (전화번호를 받지 않으므로 실제로는 이메일). 이메일 MFA를 켜면 Cognito가 "Email only"를 막음 (MFA 코드와 복구 코드는 다른 통로여야 함). 그래서 **이메일 MFA를 켠 회원은 비밀번호 찾기가 막히고, 관리자가 임시 비밀번호를 발급** (`ADMIN_GUIDE.md` 6.1절). 소유자 결정 2026-11-19: 이메일 MFA 유지. **맞교환:** 임시 비밀번호도 그 회원의 메일함으로 가므로 이메일 MFA 회원은 메일함이 유일한 인증 수단이 됨 → 발급 전 **두 번째 확인** (① 메일함에서 읽을 수 없는 정보, 또는 ② 최근 로그인 IP·지역 대조 — ②는 CloudTrail에서 회원이 식별되는 것이 확인될 때까지 사용 불가 (소유자 시험 T14, 2026-11-20); 비밀번호·MFA 코드는 절대 묻지 않음; 방법은 `ADMIN_GUIDE.md` 6.1이 정함), 확인이 틀리면 발급하지 않음, 강제 변경 뒤 인증 앱으로 바꾸기를 권함 (근거: 소유자 결정 2026-11-20 "권장으로 가겠습니다"). 두 번째 확인을 **할 수 없으면** (지금 대부분) 회원 동의를 받아 옛 계정을 지우고 같은 이메일로 다시 가입하게 함 — 옛 정보는 사라지고, 메일함만 가진 사람은 빈 새 계정만 얻음 (`ADMIN_GUIDE.md` 6.2; 근거: 소유자 결정 2026-11-20 "2로 권장합니다" (OWNER_RULINGS_LOG 기록 예정)) | 예 | 확인 (AWS 문서: 같은 통로 금지; 콘솔에서 Email only 비활성 확인) |
| P9 | 메일 발송 | **Amazon SES 사용**. FROM `no-reply@quantgeneration.com`, FROM 이름 `QUANTGEN`, Reply-to `contact@quantgeneration.com` (실제 받는 메일함). 기본 Cognito 메일은 하루 한도가 낮아 운영에 맞지 않음 | 예 | 확인 (한도 숫자 50통은 미검증) |
| P10 | 비밀번호 정책 | 최소 **10자**, 숫자·소문자·대문자·**특수문자** (소유자 결정 2026-11-19), 임시 비밀번호 7일. 웹 가입 화면은 "특수문자 1개 이상"을 입력 중에 보여 줌 (ACC-1). 특수문자로 인정되는 기호는 Cognito가 정함: `` ^ $ * . [ ] { } ( ) ? " ! @ # % & / \ , > < ' : ; \| _ ~ ` = + - `` (AWS 문서 확인 2026-11-19) | 예 | 제안 (최소 6자 허용·임시 7일 기본은 확인) |
| P11 | 비밀번호 재사용 금지 | 최근 5개 | 예 | 미검증 (Essentials에서 되는지) |
| P12 | MFA | **Optional MFA**, 방법 **Authenticator apps** + **Email message** (소유자 결정 2026-11-19: 이메일 MFA 유지, P8의 결과 감수). SMS 끔 (전화번호를 받지 않음; 유료 단계에서 본인인증으로 번호를 받게 되면 재검토, PAY-2) | 예 | 확인 (이메일 MFA는 Essentials + 자체 SES) |
| P13 | 이메일 변경 대기 | 새 주소 인증 전까지 기존 주소 유지 ("Keep original attribute value active when an update is pending") | 예 | 미검증 (문구) |
| P14 | 사용자 정의 속성 | 아래 1.2표 6개, 모두 String, 최대 64자 | 추가만 가능. 필수로 만들 수 없음. 삭제·이름 변경 불가 | 추가 가능·필수 불가 확인, 삭제 불가 미검증 |
| P15 | 삭제 보호 | 켬 (콘솔로 만든 풀은 기본 켜짐) | 예 | 확인 (기본값), 위치 부분 확인 |
| P16 | 위협 보호 | 끔 (Plus 기능) | 예 | 확인 |
| P17 | 관리형 로그인 도메인 | 만들지 않음 (웹은 자체 화면) | 예 | 제안 |

### 1.2 사용자 정의 속성 (이름은 웹사이트 요청 ACC-1·ACC-5와 글자까지 같아야 함)

<!-- custom-attrs:start -->
| 속성 이름 | 값 | 쓰는 곳 |
|---|---|---|
| `custom:terms_ver` | 동의한 이용약관 버전 문자열 | 가입 (ACC-1) |
| `custom:privacy_ver` | 확인한 처리방침 버전 문자열 | 가입 (ACC-1) |
| `custom:age14` | `Y` (만 14세 이상 본인 진술) | 가입 (ACC-1) |
| `custom:consent_at` | 가입 동의 시각 (ISO 8601) | 가입 (ACC-1) |
| `custom:mkt_opt` | `Y` / `N` (광고성 소식 메일) | 가입 (ACC-1), 계정 페이지 (ACC-5) |
| `custom:mkt_at` | `mkt_opt`를 정하거나 바꾼 시각 (ISO 8601) | 가입 (ACC-1), 계정 페이지 (ACC-5) |
<!-- custom-attrs:end -->

- 이 속성들은 서버 검색이 안 됩니다 (**확인**). 이메일·이름 같은 개인정보를 넣지 않습니다 (CloudTrail이 가리지 않음, **확인**).
- Q3 답이 "예"(만 14세)라 `custom:age14` 이름 그대로 씁니다. 이름은 나중에 못 바꿉니다.

### 1.3 앱 클라이언트

| # | 항목 | 웹 `quantgen-web` (지금) | 데스크톱 `quantgen-desktop` (자리만, PAY-1 때) | 나중에 바꿀 수 있나 | 확인 상태 |
|---|---|---|---|---|---|
| C1 | 종류 | Single-page application (SPA), **공개 클라이언트 (비밀값 없음)** | 공개 클라이언트. 종류는 PAY-1에서 정함 | 비밀값 유무는 아니요 (새 클라이언트) | 확인 (SPA는 비밀값 없음) |
| C2 | 인증 흐름 | `ALLOW_USER_SRP_AUTH`, `ALLOW_REFRESH_TOKEN_AUTH` 만 | 같은 흐름 또는 브라우저 로그인 + PKCE | 예 | 확인 (흐름 이름) |
| C3 | 토큰 유효 | ID·액세스 60분, 새로고침 7일 | 정할 것 | 예 | 제안 |
| C4 | 토큰 폐기 | 켬 | 켬 | 예 | 확인 |
| C5 | 계정 존재 숨김 | 켬 ("Prevent user existence errors") | 켬 | 예 | 문구 미검증 |
| C6 | 읽기 권한 | email, email_verified, 1.2표 6개 | 같음 | 예 | 제안 |
| C7 | 쓰기 권한 | email, 1.2표 6개 | 같음 | 예 | 제안 |

- **풀 ID와 앱 클라이언트 ID는 비밀값이 아닙니다.** 웹 소스에 들어가도 되고, 소유자가 웹사이트 세션에 그대로 전달해도 됩니다 (**확인**: SPA 공개 클라이언트). 비밀값은 AWS 로그인과 액세스 키뿐입니다.
- 한 풀에 클라이언트 두 개 → 한 계정으로 웹과 데스크톱에 모두 로그인. 데스크톱 클라이언트 ID는 운영 전에 웹사이트 세션과 합의합니다.

### 1.4 그룹

| 그룹 | 우선순위 | 용도 | 나중에 바꿀 수 있나 | 확인 상태 |
|---|---|---|---|---|
| `qg-admins` | 0 | 소유자 본인 회원 계정. 지금은 실제 권한 없음 (서버 없음) | 예 | 확인 (그룹 동작) |
| `qg-beta` | 10 | (선택) 미리 보기 기능 대상 | 예 | 제안 |

### 1.5 기록·감시·비용

| # | 항목 | 값 | 나중에 바꿀 수 있나 | 확인 상태 |
|---|---|---|---|---|
| L1 | CloudTrail 추적 | 이름 `qg-audit`, 관리 이벤트 Read+Write, 새 S3 버킷 (2026-11-20 Quick trail create가 만든 `aws-cloudtrail-logs-<계정 번호>-0bcc59a3`, 400일 만료) | 예 | 확인 (Event history 90일이라 추적 필요) |
| L2 | 보관 | S3 수명 주기: 현재 버전 400일 뒤 만료 (접속기록 1년 이상) 〔법률 자문이 아닙니다. 근거: 개인정보의 안전성 확보조치 기준 제8조 · https://itwiki.kr/w/개인정보의_안전성_확보조치_기준_제8조 · 2026-11-17 메인 D11 확인〕 | 예 | 제안 (400일) |
| L3 | 암호화 | SSE-S3 (KMS 새 키는 월 약 $1) | 예 | KMS 요금 미검증 |
| L4 | CloudWatch 경보 1 | `AWS/Cognito` `SignUpSuccesses` Sum 1시간 > 50 → 메일 | 예 | 지표 이름 확인, 기준값 제안 |
| L5 | CloudWatch 경보 2 | `SignUpThrottles` ≥ 1 → 메일 | 예 | 확인 |
| L6 | SES 경보 | 반송률 > 2%, 신고율 > 0.05% → 메일 | 예 | 반송 5%/10% 기준 확인, 신고율 한도 미검증 |
| L7 | 예산 1 | **Zero spend budget** | 예 | 확인 (템플릿 이름) |
| L8 | 예산 2 | **Monthly cost budget** 월 $20, 85%·100%·예측 100% 알림 | 예 | 템플릿 확인, 알림 비율 제3자 자료 |

비용 (추정): Cognito $0 (1만 명 미만), SES 1천 통당 약 $0.10, CloudTrail·S3 몇 센트, CloudWatch 경보 $1 미만, WAF는 필요할 때만 월 $5 이상. 모두 **미검증** 또는 검색 요약.

---

## 2부. 소유자 AWS 순서 (25단계, 약 1~2시간)

이 세션은 AWS를 바꾸지 않습니다. 소유자가 순서대로 누릅니다. *(미검증)* 은 화면 문구를 확인하지 못한 곳입니다. 화면이 다르면 해당 단계 번호와 실제 문구를 알려 주세요.

**시작 전**: Reply-to로 쓸 메일함 `contact@quantgeneration.com`이 실제로 받는지 확인 (다른 주소에서 한 통 보내 보기).

**A. 사용자 풀**
1. AWS 콘솔 로그인 (MFA) → 오른쪽 위 계정이 **Golden Hour Code** (프로젝트 계정)인지 확인 (관리 계정 아님) → 리전을 **Asia Pacific (Sydney) ap-southeast-2** 로.
2. 검색창 `Cognito` → **User pools** → **Create user pool** *(미검증)*.
3. "Define your application" 화면 *(미검증)*: 종류 **Single-page application (SPA)**, 이름 `quantgen-web`.
4. 로그인 아이디 *(Options for sign-in identifiers, 미검증)*: **Email** 만 체크.
5. 자가 가입 켬 *(만드는 화면의 문구 미검증; 만든 뒤 위치는 **Sign-up** → **Self-service sign-up** 로 **확인**)*. 가입 필수 속성 *(Required attributes)*: **email** 만.
6. Return URL은 비워 둠 *(필수 입력인지 미검증; 필수면 `https://quantgeneration.com` 을 넣고 웹사이트 세션에 알림)*.
7. 만들기. 풀 이름이 `quantgen-prod` 인지 확인 *(만드는 화면에서 풀 이름을 정하는지, 나중에 바꿀 수 있는지 미검증; 자동 이름이면 Overview에서 이름 변경을 찾고, 없으면 그대로 두고 풀 ID로 구분한 뒤 알려 주세요)*.
8. 풀 → **Sign-up** → **Required attributes** 가 email뿐인지 확인 (**확인**).
9. **Sign-up** → **Custom attributes** → **Add custom attributes** *(미검증)* → 1.2표 6개 (String, 최대 64). 이름은 표에서 복사해 붙입니다 (`custom:` 접두어는 콘솔이 자동으로 붙이는지 미검증 → 붙이면 뒷부분만 입력).

**B. 메일 (SES)**
10. 풀 → **Authentication methods** → Email 구역 → **Edit** *(Authentication methods 메뉴는 확인, Email 구역 위치·Edit 미검증)*.
11. **Send email with Amazon SES** *(미검증)* → SES 리전 시드니 → FROM `no-reply@quantgeneration.com` → FROM 이름 `QUANTGEN` → Reply-to `contact@quantgeneration.com` → **Save changes**.
12. 왼쪽 메뉴 **Message templates** (**확인**) → **Verification message** → 제목 "[QUANTGEN] Email verification code / 이메일 인증 코드", 본문은 `OWNER_STEPS.md` 12번의 HTML (로고 배너, `{####}` 코드 상자, 영어·한국어; 소유자 결정 2026-11-19). 광고 문구 없음.

**C. 로그인 보안**
13. **Authentication methods** → **Password policy** → **Edit** *(미검증)* → Custom, 최소 10자, 숫자·소문자·대문자·특수문자, 임시 7일, 재사용 금지 5.
14. **Sign-in** → **Multi-factor authentication** → **Edit** → **MFA enforcement** = **Optional MFA** → **Authenticator apps** + **Email message** → 저장 (**확인**).
15. **Sign-in** → **User account recovery** *(미검증)* → Self-service 켬, **Email if available, otherwise SMS** (14번에서 이메일 MFA를 켜면 "Email only"는 Cognito가 막음; P8, `OWNER_STEPS.md` 15번과 같음).

**D. 앱 클라이언트**
16. **App clients** (**확인**) → `quantgen-web` → **Edit** *(미검증)* → 1.3표 C2~C7.
17. **Overview** *(미검증)* 에서 **User pool ID** 와 **Client ID** 를 적어 웹사이트 세션에 전달 (비밀값 아님).

**E. 그룹과 소유자 계정**
18. **Groups** → **Create group** (**확인**) → `qg-admins`, Precedence 0 → **Create group**.
19. 운영 풀의 소유자 계정은 공개 직전 웹에서 직접 가입 → 관리자 안내서 9절로 `qg-admins` 에 추가. 그 전 시험은 개발 풀에서.

**F. 삭제 보호와 기록**
20. 삭제 보호 켜짐 확인: 풀 설정(Settings) 화면의 **Deletion protection** 구역 → 꺼져 있으면 **Activate** (**부분 확인**: 구역과 버튼, 탭 이름은 콘솔 판마다 다름).
21. 검색 `CloudTrail` → **Trails** → **Create trail** *(미검증)* → 이름 `qg-audit`, 새 S3 버킷, 로그 파일 KMS 암호화 끔 (선택), 관리 이벤트 Read + Write → 만들기.
22. 검색 `S3` → 위 버킷 → **Management** → **Lifecycle rules** → **Create lifecycle rule** *(미검증)* → 현재 버전 400일 뒤 만료.

**G. 경보·예산**
23. `CloudWatch` → **Alarms** → **Create alarm** *(미검증)* → `AWS/Cognito` → 풀 `quantgen-prod` → `SignUpSuccesses` (Sum, 1시간, > 50) → 알림 메일. 같은 방식으로 `SignUpThrottles` (> 0).
24. `Billing and Cost Management` → **Budgets** → **Create budget** → **Use a template (simplified)** → **Zero spend budget** → 메일 → 만들기. 다시 **Monthly cost budget** $20 (**확인**).
25. 언제 무엇을 만들었는지 관리자 안내서 16.2절 변경 기록에 한 줄씩.

---

## 3부. 웹사이트 세션 요청 (복사용)

- 이 세션은 웹사이트 저장소(`xkg4real/website`)를 고치지 않습니다. 아래 블록을 소유자가 웹사이트 세션에 붙여 넣습니다.
- 이 요청이 마스터 설계의 WEB-3 (출시 알림)·WEB-4 (로그인 UI)를 대신합니다. 공개 전까지 플래그 `AUTH_UI_ENABLED=false`.
- 블록은 D11 4장과 글자까지 같고, 다른 곳은 소유자 결정으로 바뀐 ACC-1 비밀번호 규칙 한 곳과 ACC-3·ACC-4의 이메일 MFA 회원 처리 (2026-11-20, 3차 검토 A4·A5), ACC-4 거절 종류·ACC-9 시험 (2026-11-20, KEY-4/a)입니다 (4.6절).
- 블록 안의 "만 14세"는 Q3 답(예)과 같습니다. 개인정보 문의 메일은 `contact@quantgeneration.com` (ACC-8).

<!-- website-block:start -->
```text
D11 변경: 소유자가 "정식 계정 생성까지 진행"을 지시했습니다. 출시 알림 폼(WEB-3) 대신 정식 회원 계정을 엽니다. 운영 사용자 풀은 시드니 `quantgen-prod` (소유자가 만들고 풀 ID·클라이언트 ID를 전달). 공개 전까지 플래그 `AUTH_UI_ENABLED=false`.

**ACC-1 가입 화면.** 이메일, 비밀번호, 비밀번호 확인. 체크: [필수] 이용약관, [필수] 만 14세 이상, [선택·기본 해제] 소식 이메일(광고). 체크 없는 개인정보 안내 문장(시드니 보관 포함) + 처리방침 링크. 한/영 문구는 D11 문서 2.3절. `SignUp` 호출 때 사용자 정의 속성 `custom:terms_ver`, `custom:privacy_ver`, `custom:age14=Y`, `custom:consent_at`(ISO 시각), `custom:mkt_opt`(Y/N), `custom:mkt_at` 기록. 비밀번호 규칙(10자, 숫자·소문자·대문자·특수문자)을 입력 중에 보여 줌.
완료 조건: 필수 체크 없이 가입 불가, 선택 체크 기본 해제, 한/영·밝음/어두움·320px.

**ACC-2 이메일 인증 화면.** 6자리 코드 입력, **"코드 다시 받기"** (`ResendConfirmationCode`) 버튼. 관리자 콘솔에는 자가 가입 회원에게 코드를 다시 보내는 버튼이 없다고 봅니다 (미검증) → 화면에 꼭 필요.
완료 조건: 잘못된 코드·만료 코드 안내, 다시 받기 횟수 제한 안내.

**ACC-3 로그인.** SRP 로그인(`USER_SRP_AUTH`), MFA 코드 단계(인증 앱·이메일), "로그인 유지" 없음(새로고침 토큰 7일). 오류 문구는 계정 존재 여부를 드러내지 않음 ("이메일 또는 비밀번호가 맞지 않습니다"). **새 비밀번호 단계:** 관리자가 임시 비밀번호를 준 회원(FORCE_CHANGE_PASSWORD)은 로그인 응답이 `NEW_PASSWORD_REQUIRED` → 새 비밀번호 화면(ACC-1과 같은 규칙: 10자, 숫자·소문자·대문자·특수문자, 입력 중 표시) → `RespondToAuthChallenge`. 임시 비밀번호는 7일 뒤 만료. 이 화면에 "이메일 MFA 대신 인증 앱(OTP)으로 바꾸기를 권합니다" 한 줄과 계정 페이지(ACC-5) 링크.
**ACC-4 비밀번호 찾기·새 비밀번호.** `ForgotPassword` → `ConfirmForgotPassword`. 관리자가 재설정을 건 회원(RESET_REQUIRED)도 이 화면으로 옴. **이메일 MFA를 켠 회원은 Cognito가 비밀번호 찾기를 거절함**(복구와 MFA가 같은 메일 통로): 그 거절이면 "이 계정은 스스로 비밀번호를 찾을 수 없습니다. 가입한 이메일로 contact@quantgeneration.com에 문의하시면 본인 확인 뒤 임시 비밀번호를 드리거나, 계정을 삭제한 뒤 같은 이메일로 다시 가입하도록 도와드립니다 (삭제하면 저장된 정보는 사라집니다)"를 보여 줌 (관리자 처리: `ADMIN_GUIDE.md` 6.1·6.2). 거절 종류: `ForgotPassword`의 오류 이름(`__type`)과 메시지로 구별 — 정확한 이름은 소유자 시험 T17에서 확정해 전달 (미검증; 확정 전에는 이 안내를 다른 오류에 붙이지 않음). `UserNotFoundException`·`LimitExceededException`·`CodeDeliveryFailureException` 등 다른 오류는 계정 존재 여부를 드러내지 않는 기존 문구 그대로.
**ACC-5 계정 페이지.** 내 이메일 보기·변경(`UpdateUserAttributes` → 새 주소 코드 확인), 비밀번호 변경, 2단계 인증 켜기·끄기(OTP 앱 QR 등록), 소식 이메일 켜기·끄기(`custom:mkt_opt`·`custom:mkt_at` 갱신), 모든 기기에서 로그아웃(`GlobalSignOut`), **내 정보 내려받기**(`GetUser` 결과를 JSON 파일로), **회원 탈퇴**(`DeleteUser`, 확인 문구 입력 후 즉시 삭제, 결과 화면). 탈퇴는 가입보다 어렵지 않게.
**ACC-6 머리글·문구.** Log in / Sign up 버튼을 위 화면에 연결(플래그 뒤). 플래그 꺼진 동안은 기존 안내 문장 유지. "(주)넥스트제너레이션" 표기는 메인 세션 정책 PR 병합 뒤 사이트 전체에서 개인 운영자 표기로 바뀜(직접 문구를 만들지 말고 원문 재생성).
**ACC-7 보안.** Cognito 라이브러리 버전 고정·빌드에 묶기(런타임 CDN 금지), CSP `connect-src`에 `https://cognito-idp.ap-southeast-2.amazonaws.com`만 추가, 토큰은 메모리 또는 sessionStorage(로그 금지), 인증 화면에 분석·추적 스크립트 없음, 비밀번호 입력란 자동완성 `new-password`/`current-password`.
**ACC-8 하단.** "개인정보 처리방침" 링크를 다른 링크보다 눈에 띄게(굵게). 개인정보 문의 메일 표시(소유자가 받는 메일함 확인 뒤).
**ACC-9 시험.** 개발 풀로 끝에서 끝까지(가입 → 코드 → 로그인 → MFA → 이메일 변경 → 비밀번호 찾기 → 내려받기 → 탈퇴) 자동 시험 + 소유자 이메일로 운영 풀 수동 시험 1회. 새 두 경로도 시험: ① 관리자가 임시 비밀번호를 준 회원(FORCE_CHANGE_PASSWORD) 로그인 → `NEW_PASSWORD_REQUIRED` → 새 비밀번호 화면(규칙 표시, 인증 앱 권장 줄) → 로그인됨, 7일 지난 임시 비밀번호는 거절 (ACC-3); ② 이메일 MFA 회원의 비밀번호 찾기 → 거절 → contact@ 문의 안내 (임시 비밀번호 또는 삭제 뒤 같은 이메일 재가입 문구), 다른 오류는 기존 문구 (ACC-4); ③ 관리자가 지운 계정의 이메일로 다시 가입 → 새 계정으로 가입·코드 확인·로그인 됨 (`ADMIN_GUIDE.md` 6.2). 결과를 `WEBSITE_AWS_SESSION_CURRENT.md`에 기록.
**ACC-10 소유자에게 줄 것.** 앱 클라이언트 설정 확인표(3.3절과 대조), 플래그 켜기 전 체크리스트. 웹 안 관리자 화면은 만들지 않음(관리는 AWS 콘솔).
```
<!-- website-block:end -->

---

## 4부. 메인 정책 문서 PR에 넣을 값

- 이 세션은 `docs/compliance/**`와 `release-profile.json`을 고치지 않습니다. 메인 세션이 정책 문서 PR에서 아래 값을 넣습니다. 뜻이 바뀌는 수정이므로 Q1~Q3 답과 소유자 승인 뒤입니다.
- 칸 이름은 main `5888d05`의 실제 자리표시 이름입니다. 문서에 그 칸이 없으면 "새 문장"으로 적었습니다.
- 모든 값은 **제안**이고, 법률 내용은 **법률 자문이 아닙니다**.

### 4.1 운영자·책임자·연락처 (`release-profile.json`, `01`, `02`, `16`)

| 대상 | 칸 | 값 |
|---|---|---|
| `release-profile.json` | `operator.legal_name` | `**운영자 표기** (0.1절)` (개인. "(주)" 없음) 〔법률 자문이 아닙니다. 근거: 상법 제20조·제28조 · https://korea.legal/wiki/상법-제20조/ · 2026-11-17 메인 D11 확인〕 |
| `release-profile.json` | `operator.privacy_contact` | `contact@quantgeneration.com` |
| `release-profile.json` | `operator.support_email` | `contact@quantgeneration.com` |
| `release-profile.json` | `operator.address` | 무료 회원만이면 처리방침에 공개하지 않는 안 (미검증). 유료 판매 때 사업자 정보로 다시 정함 |
| `01` | `{{privacy.owner}}`, `{{privacy.officer_or_department}}` | `**운영자 표기** (0.1절)` (개인정보 보호책임자 = 운영자 본인) 〔법률 자문이 아닙니다. 근거: 개인정보 보호법 시행령 제32조 (사업주·대표자 지정 가능, 해설 기준) · 해설 URL 미확보 · 2026-11-17 메인 D11 2.1절〕 |
| `01` | `{{privacy.contact_email}}` | `contact@quantgeneration.com` (실제 수신 시험 뒤) |
| `01` | `{{privacy.contact_phone}}` | 비움 또는 "이메일로 문의" (전화번호 필수 여부 미검증) |
| `01`, `02` | `{{operator.support_email}}` | `contact@quantgeneration.com` |
| `16` | 상호·대표자 | `**운영자 표기** (0.1절)`. 사업자등록번호·통신판매업 신고번호는 "해당 없음 (무료 서비스, 사업자 미등록)" — 유료 판매 전까지 |
| `01` | 책임자 지정 신고 | 해당 없음 (대규모 처리자만) 〔법률 자문이 아닙니다. 근거: 2026-09-11 시행 개정 보도 · https://www.lawtimes.co.kr/news/articleViewAmp.html?idxno=226414 · 2026-11-17 메인 D11 확인, 시행령 원문 미확인〕 |

### 4.2 처리방침 칸 (`01-privacy-policy.md`)

| 칸 | 값 |
|---|---|
| `{{service.covered_urls_and_apps}}` | `https://quantgeneration.com` 회원 계정, (나중에) QUANTGEN 데스크톱 앱 로그인 |
| `{{privacy.service_fields}}` | 필수: 이메일 주소, 비밀번호 (운영자도 볼 수 없는 형태로 AWS가 보관), 계정 고유번호, 가입·수정 시각, 계정 상태, 약관·처리방침 버전과 동의 시각, 만 14세 이상 본인 진술. 선택: 2단계 인증 설정 여부 |
| `{{privacy.service_collection_and_location}}` | 회원이 웹 가입 화면에 직접 입력. 호주 시드니의 AWS (Amazon Cognito)에 보관 |
| `{{privacy.service_basis}}` | 계약 체결·이행에 필요 〔법률 자문이 아닙니다. 근거: 개인정보 보호법 제15조 제1항 제4호 (원문 미확인) · 해설 URL 미확보 · 2026-11-17 메인 D11 2.2절〕 |
| `{{privacy.service_retention}}` | 회원 탈퇴(계정 삭제) 즉시 삭제. 이메일 인증을 마치지 않은 계정은 7일 뒤 삭제 |
| 광고 메일 (새 행 또는 `{{privacy.marketing_basis}}`, 06번 문서) | 선택. 항목: 이메일, 수신 동의 여부·시각. 근거: 동의. 보유: 동의 철회 또는 탈퇴 시까지 |
| `{{privacy.security_log_route}}` | 관리자 작업 기록과 계정 관련 요청 기록 (요청 시각, 접속 IP, 요청 종류, 계정 고유번호). AWS CloudTrail → 시드니 S3. *주의 (소유자 시험 T14, 2026-11-20): 회원 쪽 요청 (가입·로그인·비밀번호 찾기)은 시각·접속 IP·요청 종류가 기록되지만 Event history CSV에는 계정 고유번호가 비어 있었음 → 이벤트 원문에 남는지 확인 전까지 "계정 고유번호"는 관리자 작업 기록에만 확실 (미검증)* |
| `{{privacy.security_log_basis}}` | 안전성 확보 의무 〔법률 자문이 아닙니다. 근거: 개인정보의 안전성 확보조치 기준 제8조 · https://itwiki.kr/w/개인정보의_안전성_확보조치_기준_제8조 · 2026-11-17 메인 D11 확인〕 |
| `{{privacy.security_log_retention}}` | 1년 (400일 뒤 자동 삭제) |
| 처리위탁 (`{{privacy.recipient_*}}` 또는 위탁 표) | 수탁자: Amazon Web Services (계약 법인명은 청구서 판매자 표기로 확인, **미검증**). 업무: 회원 계정 보관·인증 (Cognito), 인증 메일 발송 (SES), 웹 호스팅 (Amplify), 보안 기록 보관 (CloudTrail·S3) |
| `{{privacy.rights_request_url}}` | 웹 계정 페이지 주소 (웹사이트 세션이 정함) + `contact@quantgeneration.com` |
| `{{privacy.implemented_safeguards}}` | 실제로 한 것만: 관리자 콘솔 2단계 인증, 관리자 작업 기록 1년 보관, 비밀번호는 운영자가 볼 수 없음, 전송 구간 HTTPS, 최소 수집 |
| `04` 쿠키·저장장치 | 로그인 유지용 토큰을 브라우저 저장소(메모리 또는 sessionStorage)에 둠. 실제 위치는 웹사이트 세션이 확정 |

### 4.3 국외 이전 표 (`01`의 `{{privacy.transfer_*}}`)

〔법률 자문이 아닙니다. 근거: 개인정보 보호법 제28조의8 제1항 제3호·제2항 (계약 이행을 위한 위탁·보관은 처리방침 공개로 이전 가능, 원문 미확인) · https://itwiki.kr/w/개인정보_보호법_제28조의8 · 2026-11-17 메인 D11 확인〕

| 칸 | 값 |
|---|---|
| `{{privacy.transfer_recipient}}` | Amazon Web Services (계약 법인명 확인 필요, 연락처: AWS 개인정보 문의 창구 — 주소 미확보) |
| `{{privacy.transfer_countries}}` | 호주 (시드니, ap-southeast-2) |
| `{{privacy.transfer_time_method}}` | 가입 시와 이용 중 수시, 네트워크 전송 |
| `{{privacy.transfer_fields}}` | 4.2의 필수·선택 항목, 보안 기록 |
| `{{privacy.transfer_purpose}}` | 회원 계정 보관·인증, 인증 메일 발송, 보안 기록 보관 |
| `{{privacy.transfer_retention}}` | 4.2와 같음 |
| `{{privacy.transfer_basis}}` | 제28조의8 제1항 제3호 (계약 이행을 위한 처리위탁·보관, 처리방침 공개) |
| `{{privacy.transfer_refusal}}` | 가입하지 않거나 탈퇴. 거부하면 회원 계정 서비스를 쓸 수 없음. 데스크톱 앱의 무료 기능은 계정 없이 사용 가능 |

### 4.4 문서별 넣을 것 (`06`, `07`, `08`, `17`, `18`, `20`)

| 문서 | 넣을 것 |
|---|---|
| `06-form-consent.md` | 가입 화면 동의 항목 (아래 표). 계약에 필요한 정보는 "동의"가 아니라 "안내", 선택 항목만 체크, 선택은 기본 해제. "[필수] 개인정보 수집·이용 동의" 체크를 따로 둘지는 법률 확인 대상 (**미검증**) |
| `07-data-minimization.md` | 받는 것: 이메일, 비밀번호, 자동 항목, 동의 기록 6개, MFA 등록 정보. **받지 않는 것**: 이름, 생년월일, 전화번호, 주소, 주민등록번호, 증권 계좌·증권사 API 키 (웹에서 받지 않음; 키는 데스크톱 앱 OS 키 보관함에만), 닉네임 (나중에) |
| `08-third-parties.md` | AWS (Cognito, SES, Amplify, CloudTrail, S3), 리전 시드니. 웹 인증 화면에는 분석·추적 스크립트 없음 (ACC-7) |
| `17-children.md` | `{{age.minimum_age}}` = 14 (본인 진술 체크, 실제 나이 확인 아님). 유료 계정 만 19세. 만 14세 미만으로 밝혀지면 정지 → 확인 → 삭제 (F17-03) |
| `18-marketing-email.md` | 선택 동의 기본 해제, 제목 앞 "(광고)", 쉬운 무료 수신 거부 (계정 페이지), 동의일부터 2년마다 수신 동의 사실 안내. 인증·재설정·정책 안내 메일에는 홍보 문구를 섞지 않음 〔법률 자문이 아닙니다. 근거: 정보통신망법 제50조 · https://www.itwiki.kr/w/정보통신망법_제50조 · 2026-11-17 메인 D11 확인. 야간 전송 별도 동의의 이메일 적용 여부 미검증〕 |
| `20-deletion.md` | "계정 삭제 엔드포인트 없음" → 웹 계정 페이지 **회원 탈퇴** (Cognito `DeleteUser`, 즉시 삭제), 관리자 대리 삭제 (관리자 안내서 5절), 인증 안 한 계정 7일 뒤 삭제, 보안 기록의 계정 고유번호는 1년 보관 후 자동 삭제. 권리 요청 10일 〔법률 자문이 아닙니다. 근거: 개인정보 보호법 시행령 제41·43·44조 (원문 미확인, 해설 URL 미확보) · 2026-11-17 메인 D11 2.8절〕 |
| `02-terms-of-service.md` | `{{service.age_and_minor_contract_policy}}` = 무료 만 14세 이상 본인 진술, 유료 만 19세 이상. `{{operator.contract_owner}}` = `**운영자 표기** (0.1절)` |

가입 화면 동의 항목 (06번, D11 2.3절 그대로):

| 항목 | 종류 | 한국어 | English |
|---|---|---|---|
| 약관 | 필수 체크 | [필수] 이용약관에 동의합니다. (보기) | [Required] I agree to the Terms of Service. (View) |
| 연령 | 필수 체크 | [필수] 만 14세 이상입니다. | [Required] I am 14 or older. |
| 개인정보 안내 | 체크 없음, 문장 | 가입하시면 계정 제공을 위해 이메일 주소와 비밀번호를 처리합니다. 정보는 호주 시드니에 있는 AWS 서버에 보관됩니다. 자세한 내용은 개인정보 처리방침에서 확인하실 수 있습니다. | When you sign up, we process your email address and password to provide your account. Your data is stored on AWS servers in Sydney, Australia. See our Privacy Policy for details. |
| 소식 메일 | 선택 체크, 기본 해제 | [선택] QUANTGEN 소식·혜택 이메일(광고)을 받겠습니다. 언제든 끌 수 있습니다. | [Optional] Send me QUANTGEN news and offers by email (advertising). You can turn this off any time. |

### 4.5 유출 대응·법인 전환 (`01`, `20`)

| 주제 | 넣을 것 |
|---|---|
| 유출 통지 | 알게 된 때부터 72시간 안 회원 통지, 1천 명 이상·민감정보·외부 불법 접근이면 개인정보보호위원회 또는 KISA 신고 〔법률 자문이 아닙니다. 근거: 개인정보 보호법 제34조, 시행령 제40조 · https://www.kisa.or.kr/1030402 · https://itwiki.kr/w/개인정보_보호법_시행령_제40조 · 2026-11-17 메인 D11 확인〕 |
| 법인 전환 통지 | 개인 → 법인 이전 전에 이전 사실, 받는 법인 이름·주소·전화·연락처, 원하지 않을 때의 방법을 미리 알림 (서면 등, 어려우면 홈페이지 30일 이상 게시) 〔법률 자문이 아닙니다. 근거: 개인정보 보호법 제27조, 시행령 제29조 · https://itwiki.kr/w/개인정보_보호법_제27조 · 2026-11-17 메인 D11 확인〕 |

### 4.6 대조 결과 (이 세션의 스크립트)

`tools`에 넣지 않은 일회용 스크립트로 확인했습니다 (스크래치에 보관, 인계 파일에 명령 기록).

1. 1.2표의 속성 이름 6개가 3부 블록의 ACC-1에 모두 있고, ACC-5에는 `custom:mkt_opt`·`custom:mkt_at`이 있음.
2. 3부 블록이 D11 4장 "복사 시작"~"복사 끝" 사이와 바이트 단위로 같음.
3. 결과: 아래 줄에 기록.

2026-11-19 소유자 결정 (특수문자 요구)으로 3부 ACC-1의 "비밀번호 규칙(10자, 숫자·소문자·대문자·특수문자)" 한 곳이 D11 4장 원문과 달라졌습니다. 2026-11-20 (PR #133 3차 검토 A4·A5, 소유자 결정 "권장으로 가겠습니다")에 ACC-3의 새 비밀번호 단계와 ACC-4의 이메일 MFA 회원 거절 안내가 더해졌고, 같은 날 계정 문서 고침 (KEY-4/a)에서 ACC-4의 거절 종류와 ACC-9의 새 두 경로 시험이 더해졌습니다. 그래서 2번 바이트 대조는 이 날부터 이 네 곳 (ACC-1, ACC-3, ACC-4, ACC-9)을 뺀 대조입니다. 웹사이트 세션에는 이 문서의 3부 블록을 넘깁니다.

결과 (2026-11-17): 속성 표 6개 ['custom:age14', 'custom:consent_at', 'custom:mkt_at', 'custom:mkt_opt', 'custom:privacy_ver', 'custom:terms_ver']; ACC-1 ['custom:age14', 'custom:consent_at', 'custom:mkt_at', 'custom:mkt_opt', 'custom:privacy_ver', 'custom:terms_ver'] 일치=True; ACC-5 ['custom:mkt_at', 'custom:mkt_opt'] 표 안에 포함=True; 3부 블록 = D11 4장 원문 3667바이트 일치=True
