# 소유자 실행 순서: AWS → 전달 → 시험 → 공개 전

- 판: v1.8 (2026-11-20, 계정 문서 고침 KEY-4/a: 소유자 3-A 시험 결과 T3~T9·T13~T15 (실제 화면 문구, T5 삭제 창, T9 CloudShell 값 사라짐, T13 이름 입력 없음, T14 CloudTrail 결과), 값 줄에 풀 ID·시험 계정 2와 명령 ①~⑥을 값으로 (F6), T17a 이메일 MFA 회원 Reset password (F3), T18 표 고침 (F2), T19 두 번째 확인을 메일함에서 읽을 수 없는 것으로 (F1), 1-2 표 고침 (F4), 2단계 자리표시 (F5), 11월 비용 서비스별). v1.7 (2026-11-20, 소유자 요청 "T3 ~ T8까지 절차를 구체화해서 QUANTGEN_OWNER_STEPS.md를 수정해주세요": 3-A T3~T8 단계별 누를 곳·기대 결과와 CloudShell 값 세 줄; 소유자 진행 결과와 PR #133 3차 검토: 1단계 1~23c·25 끝남 (24는 기존 예산 사용), 23a·23b를 CloudShell 명령으로 (새 풀은 가입 전이라 콘솔 지표 목록에 없음), 21번 Quick trail create, 24번 기존 예산 규칙과 크레딧 메모, 1-2에 기록한 값, 1-3을 일반 "풀 지우기" 두 경우로 (B2), 15번·2단계·3단계에 이메일 MFA 회원 비밀번호 분실 처리 (A4·A5, 소유자 결정 2026-11-20 "권장으로 가겠습니다")). v1.6 (2026-11-19, 소유자 결정: 이메일 MFA 유지, 15번 복구 방법). v1.5 (2026-11-19, 메인 PR #133 2차 검토 B3·C5: 계정 둘 구분 — MFA는 액세스 포털/관리 계정 경로, 결제 접근은 Budgets가 거부될 때만 Golden Hour Code 루트, 5-2a는 두 계정 모두; 1-3 잘못 만든 풀 지우기와 삭제 보호 끄기; 풀 ID 리전 확인을 7·17번으로). v1.4 (2026-11-19, 소유자 결정: 13번 비밀번호에 특수문자 반영, 12번 HTML 인증 메일·영어 먼저·Message templates 위치). v1.3.2 (2026-11-19, 소유자 진행 중 확인: 1-0 둘째 항목으로 프로젝트 계정 Golden Hour Code 확인, 1번에 풀 ID 리전 확인 — v1.5에서 7·17번으로 옮김). v1.3.1 (2026-11-19, 메인 PR #133 검토 B10: 1-0의 따로 만드는 예산 줄을 지우고 24a·24b로 모음, 결제 화면 접근 켜기 추가, IAM Identity Center 로그인 확인 반영, 5-2a 법인 이메일·연락처로 명확히, 1-0 소요 15~20분). v1.3 (2026-11-19, 소유자 질문 반영: 1-0 MFA 찾는 길과 로그인 계정, 5절 AWS 계정 이메일). v1.2 (2026-11-19, 6절을 메인 세션 확인대로 고침: 지금 하지 않음, 보통 앱 Python, 브랜치+PR). v1.1 6절 추가, v1 2026-11-18. 작성: PAYMENTS_ACCOUNT_KEYS 세션. 소유자 요청 (원문): "위 항목 중에서 시험, 전달, AWS, 공개 전 4단계를 수행하기 위해서 해야되는 일들을 구체화하여 .md 파일로 만들어 여기서 다운로드하고 볼 수 있도록 해주세요"
- 반영한 소유자 답 (2026-11-18): Q1 운영자 = 개인 (법인 설립을 알려 주시면 바로 법인명으로 바꿈), Q2 메일 = `contact@quantgeneration.com`, Q3 최소 연령 = 무료 만 14세 / 유료 만 19세.
- 함께 보는 문서 (브랜치 `claude/payments-keys-20261117`): `docs/commercial/accounts/ACCOUNT_SETUP.md` (설정값, 25단계, 웹사이트 요청 블록), `docs/commercial/accounts/ADMIN_GUIDE.md` (관리자 안내서).
- *(미검증)* 은 AWS 화면 문구를 확인하지 못한 곳입니다. 화면이 다르면 "단계 번호 + 실제 문구"를 알려 주세요. 문서를 고쳐 드립니다.

---

## 0. 한눈에 보기

| 순서 | 단계 | 누가 | 미리 필요한 것 | 걸리는 시간 (추정) | 끝나면 저에게 알려 줄 것 |
|---|---|---|---|---|---|
| 1 | **AWS**: 운영 풀 `quantgen-prod`와 기록·경보·예산 만들기 | 소유자 | AWS 콘솔 로그인 (MFA), `contact@` 수신 확인 | 1~2시간 | 풀 ID, 웹 클라이언트 ID (둘 다 비밀값 아님), 화면 문구가 달랐던 단계 |
| 2 | **전달**: 웹사이트 세션에 요청 블록 + ID 붙여 넣기 | 소유자 | 1단계의 ID 2개 | 10분 | 붙여 넣은 날짜 |
| 3 | **시험**: 관리자 기능을 시험 계정으로 따라 하기 | 소유자 | 1단계 끝. 3-B는 웹사이트 화면이 나온 뒤 | 3-A 30분, 3-B 30분 | 부록 C 표의 "그대로 됨/다름" |
| 4 | **공개 전**: 체크 8개 + 법률 확인 1회 | 소유자 | 메인 세션의 정책 문서 PR 병합, 웹사이트 화면 배포 (플래그 꺼짐) | 반나절 + 상담 | 8개 결과 |

- 1단계(AWS)는 메인 세션의 정책 문서 PR과 **동시에** 해도 됩니다. 풀을 만들어도 웹사이트 가입 화면은 플래그가 꺼져 있어 아무도 가입할 수 없습니다.
- 4단계의 1·2번은 메인 세션 정책 PR이 main에 들어간 뒤에만 통과할 수 있습니다.

**어디서나 지킬 것**
- 화면 캡처를 채팅·Notion·GitHub에 올리지 않습니다 (회원 이메일이 개인정보).
- 비밀번호, AWS 액세스 키, 인증 코드는 채팅에 쓰지 않습니다. 풀 ID와 클라이언트 ID는 비밀값이 아니라 보내셔도 됩니다.
- 시험 계정은 본인 메일의 별칭을 씁니다. Gmail이면 `내아이디+qgtest1@gmail.com` 처럼 `+` 뒤에 글자를 붙이면 같은 메일함으로 오고, AWS에는 다른 주소로 보입니다.
- CloudShell 명령을 쓴 뒤에는 마지막에 `history -c` 를 실행해 명령 기록(시험 이메일·비밀번호 포함)을 지웁니다.

---

## 1단계. AWS (운영 풀 만들기)

### 1-0. 시작 전 (15~20분)

- [ ] `contact@quantgeneration.com` 으로 다른 주소에서 메일을 한 통 보내, 실제로 받는지 확인. 안 오면 여기서 멈추고 웹사이트 세션의 메일 작업을 먼저 끝냅니다 (가입 메일의 회신 주소이자 개인정보 문의 창구라 꼭 받아야 함).
- [ ] **어느 계정인가 (AWS 작업 전 가장 먼저):** 운영 풀은 **프로젝트 계정 "Golden Hour Code"** (계정 번호 끝 `8543`)에 만듭니다. 시드니 SES의 `quantgeneration.com` 도메인 인증(DKIM SUCCESS)·샌드박스 해제와 개발 풀 `quantgen-dev`가 이 계정에 있기 때문입니다 (웹사이트 세션 기록 2026-11-13). 이름에 "Management Account"가 붙은 관리 계정에 만들면 11번 FROM 칸에 아무것도 나오지 않습니다 (2026-11-19 실제로 겪음). 확인: 오른쪽 위 계정 이름이 Golden Hour Code, Cognito → User pools에 `quantgen-dev`가 보임.
- [ ] 어느 로그인으로 하나: 위 계정 (2026-11-19 소유자가 유료 플랜으로 올림). 소유자 화면 확인 (2026-11-19): 이 계정은 **IAM Identity Center** 로그인 (오른쪽 위 `AccountFullAccessRole/…`)으로 들어오며, 그래서 IAM의 Users 목록이 비어 있는 것이 정상입니다. **IAM 사용자는 만들지 않습니다.** 1-1 이후도 같은 로그인으로 합니다.
- [ ] 그 로그인에 MFA: 본인이 하는 길은 **액세스 포털**(로그인 때 계정을 고르는 화면) 오른쪽 위 이름 → **MFA devices**. 관리자 경로는 **관리 계정**(…3710, IAM Identity Center가 있는 계정)의 IAM Identity Center 콘솔 → **Users** → 본인 사용자 **이름** → **MFA devices** 탭 (프로젝트 계정 Golden Hour Code에는 이 콘솔이 없음). 장치가 있으면 끝, 없으면 **Register MFA device** (인증 앱의 QR → 6자리 입력). 2023-11 뒤에 만든 Identity Center는 MFA가 기본으로 켜져 있어 처음 로그인 때 이미 등록했을 수 있습니다. 로그인마다 묻는지는 **Settings** → **Authentication** → Multi-factor authentication **Configure**에서 확인. 〔AWS 문서로 확인: Register an MFA device for users, Configure MFA in IAM Identity Center, 2023-11 MFA 기본값 공지 · 2026-11-19〕
- [ ] 결제 화면 접근 (필요할 때만): 먼저 Identity Center 로그인(Golden Hour Code 계정)으로 **Budgets** 화면을 열어 봅니다. 열리면 이 줄은 끝입니다. **접근 거부될 때만**: **Golden Hour Code 계정의 루트**(관리 계정의 루트가 아님)로 한 번 로그인 → 오른쪽 위 계정 → **Account** → **IAM user and role access to Billing information** → **Edit** → **Activate IAM Access** → **Update**. 이 계정을 Organizations로 만들어 루트 비밀번호를 정한 적이 없으면 루트 로그인 화면의 비밀번호 찾기(루트 이메일로 재설정)부터 합니다 *(문구 미검증)*. 이 설정은 루트만 바꿀 수 있습니다. 〔AWS 문서로 확인: Overview of managing access permissions (Billing) · 2026-11-19〕 예산 자체는 24a·24b에서 만듭니다 (받는 메일 `contact@quantgeneration.com`); 여기서 따로 만들지 않습니다.
- [ ] 메모장 하나를 엽니다. 아래 "적어 둘 것"을 여기에 모읍니다 (PC에만 보관).

### 1-1. 25단계

`ACCOUNT_SETUP.md` 2부와 같은 순서입니다. 넣을 값을 그대로 옮겼습니다.

**진행 상태 (2026-11-20):** 소유자가 1~23c와 25를 마침 (Golden Hour Code 계정, 시드니). 24는 이미 있던 예산으로 대신함 (24번 칸). 기록한 값은 1-2절.

**A. 사용자 풀 (약 20분)**

| # | 할 일 | 넣을 값 | 확인 |
|---|---|---|---|
| 1 | 콘솔 로그인 (Golden Hour Code 계정) → 오른쪽 위 리전 | **Asia Pacific (Sydney) ap-southeast-2** | [ ] |
| 2 | 검색창 `Cognito` → **User pools** → **Create user pool** *(미검증)* | — | [ ] |
| 3 | 앱 종류와 이름 | **Single-page application (SPA)**, 이름 `quantgen-web` | [ ] |
| 4 | 로그인 아이디 | **Email** 만 체크 (Username·Phone 체크 안 함) | [ ] |
| 5 | 자가 가입 켬, 필수 속성 | 필수 속성 **email** 만 (name·phone 등 추가하지 않음) | [ ] |
| 6 | Return URL | 비워 둠. 필수라고 나오면 `https://quantgeneration.com` → 저에게 알려 주세요 | [ ] |
| 7 | 만들기 → 풀 이름 | Overview의 **User pool ID**가 `ap-southeast-2_`로 시작하는지 먼저 확인 (`us-east-1_` 등이면 리전이 틀린 것: 시드니에 다시 만들고 틀린 풀은 1-3절 **경우 2**대로 지움; 리전은 옮길 수 없음). 그다음 **Rename** → `quantgen-prod` | [ ] |
| 8 | 풀 → **Sign-up** → **Required attributes** | email만 있는지 확인 | [ ] |
| 9 | **Sign-up** → **Custom attributes** → **Add custom attributes** *(미검증)* | 6개, 모두 **String**, 최대 길이 64: `terms_ver`, `privacy_ver`, `age14`, `consent_at`, `mkt_opt`, `mkt_at` (화면이 앞에 `custom:`을 붙여 주면 뒷부분만 입력). **철자를 한 글자도 틀리지 않게** (나중에 못 바꿈) | [ ] |

**B. 메일 (약 15분)**

| # | 할 일 | 넣을 값 | 확인 |
|---|---|---|---|
| 10 | **Authentication methods** → Email 구역 → **Edit** *(미검증)* | — | [ ] |
| 11 | 메일 발송 방식 | **Send email with Amazon SES** *(미검증)*, SES 리전 시드니, FROM `no-reply@quantgeneration.com`, FROM 이름 `QUANTGEN`, Reply-to `contact@quantgeneration.com` → **Save changes** | [ ] |
| 12 | 왼쪽 메뉴 **Message templates** (Authentication methods 안이 아님) → **Verification message** → **Edit** | Verification type **Code**, 제목: `[QUANTGEN] Email verification code / 이메일 인증 코드` · 본문: 아래 HTML 상자 그대로 (소유자 결정 2026-11-19: 로고 배너·코드 상자, 영어 먼저) | [ ] |

12단계 본문 (그대로 붙여 넣기; 2026-11-19 소유자가 이 내용으로 저장함):
```
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F4F6F9;padding:24px 0;">
<tr><td align="center">
<table role="presentation" width="480" cellpadding="0" cellspacing="0" style="max-width:480px;width:100%;background:#FFFFFF;border-radius:10px;overflow:hidden;font-family:Arial,Helvetica,sans-serif;color:#111111;">
<tr><td style="background:#0B1F3A;padding:18px 24px;text-align:center;">
<img src="https://quantgeneration.com/quantgen-logo-white.png" alt="QUANTGEN" width="155" height="32" style="display:inline-block;width:155px;height:32px;border:0;color:#FFFFFF;font-size:22px;font-weight:bold;letter-spacing:4px;">
</td></tr>
<tr><td style="padding:28px 24px 8px 24px;">
<p style="margin:0 0 6px 0;font-size:17px;font-weight:bold;">Email verification code</p>
<p style="margin:0;font-size:14px;color:#555555;">이메일 인증 코드</p>
</td></tr>
<tr><td align="center" style="padding:20px 24px;">
<span style="display:inline-block;padding:14px 24px;border:2px solid #0B1F3A;border-radius:8px;background:#F4F6F9;font-family:'Courier New',Courier,monospace;font-size:32px;font-weight:bold;letter-spacing:10px;color:#0B1F3A;">{####}</span>
</td></tr>
<tr><td style="padding:8px 24px 28px 24px;font-size:13px;line-height:1.6;color:#555555;">
Enter this code on the sign-up screen. If you did not request it, you can ignore this email.<br><br>
이 코드를 가입 화면에 입력해 주세요. 본인이 요청하지 않았다면 이 메일을 무시하셔도 됩니다.
</td></tr>
<tr><td style="padding:14px 24px;border-top:1px solid #E5E7EB;font-size:11px;color:#999999;text-align:center;">
QUANTGEN · Contact / 문의: contact@quantgeneration.com
</td></tr>
</table>
</td></tr>
</table>
```
로고 `https://quantgeneration.com/quantgen-logo-white.png` (투명 바탕 RGBA 309×64, 웹사이트 세션 확인). 이미지를 막는 메일 프로그램에서는 `alt` 글자 "QUANTGEN"이 남색 배너 위에 보임. Cognito 본문은 HTML 허용, `{####}` 필수, 최대 20,000자 (AWS 문서 확인). 숫자 6칸 따로는 불가 (`{####}`가 통째로 바뀜). 광고 문구는 넣지 않습니다.

**C. 로그인 보안 (약 10분)**

| # | 할 일 | 넣을 값 | 확인 |
|---|---|---|---|
| 13 | **Authentication methods** → **Password policy** → **Edit** *(미검증)* | Custom, 최소 **10자**, 숫자·소문자·대문자·**특수문자** 요구 (소유자 결정 2026-11-19: 특수문자 반영), 임시 비밀번호 **7일**, 재사용 금지 **5** (칸이 없으면 건너뜀) | [ ] |
| 14 | **Sign-in** → **Multi-factor authentication** → **Edit** | MFA enforcement **Optional MFA**, 방법 **Authenticator apps** + **Email message** (SMS는 끔) → 저장 | [ ] |
| 15 | **Sign-in** → **User account recovery** → **Edit** | **Enable self-service account recovery** 체크, 전달 방법 **Email if available, otherwise SMS** (14번에서 Email message MFA를 켜서 "Email only"는 회색으로 막힘; 전화번호를 받지 않으므로 실제로는 이메일). 소유자 결정 2026-11-19: 이메일 MFA 유지 → 이메일 MFA 회원의 비밀번호 분실은 관리자 임시 비밀번호 (`ADMIN_GUIDE.md` 6.1절). 발급 전 **두 번째 확인** (회원만 아는 정보 또는 최근 로그인 IP·지역; 실패하면 발급 안 함), 강제 변경 뒤 인증 앱 권장 — 소유자 결정 2026-11-20 (OWNER_RULINGS_LOG 기록 예정) | [ ] |

**D. 앱 클라이언트 (약 10분)**

| # | 할 일 | 넣을 값 | 확인 |
|---|---|---|---|
| 16 | **App clients** → `quantgen-web` → **Edit** *(미검증)* | 인증 흐름 **ALLOW_USER_SRP_AUTH**, **ALLOW_REFRESH_TOKEN_AUTH** 만 · ID·액세스 토큰 60분, 새로고침 토큰 7일 · 토큰 폐기(token revocation) 켬 · 계정 존재 숨김("Prevent user existence errors") 켬 · 속성 읽기: email, email_verified, custom 6개 · 쓰기: email, custom 6개 | [ ] |
| 17 | **Overview** *(미검증)* | **User pool ID** (`ap-southeast-2_`로 시작하는지 다시 확인), **Client ID** 를 메모장에. 오른쪽 위 계정이 Golden Hour Code인지도 확인 | [ ] |

**E. 관리자 그룹 (5분)**

| # | 할 일 | 넣을 값 | 확인 |
|---|---|---|---|
| 18 | **Groups** → **Create group** | 이름 `qg-admins`, Precedence `0` → **Create group** | [ ] |
| 19 | 소유자 본인 회원 계정 | **지금은 하지 않음.** 공개 직전에 웹에서 직접 가입한 뒤 그룹에 추가 (관리자 안내서 9절) | — |

**F. 삭제 보호와 관리자 기록 (약 15분)**

| # | 할 일 | 넣을 값 | 확인 |
|---|---|---|---|
| 20 | 풀 설정(Settings) 화면 → **Deletion protection** | **Active** 인지 확인, 아니면 **Activate** | [ ] |
| 21 | 검색 `CloudTrail` → **Trails** → **Create trail** *(미검증)* | 이름 `qg-audit`, **새 S3 버킷** (이름은 콘솔이 주는 대로), 로그 파일 KMS 암호화 **끔**, 관리 이벤트 **Read + Write** → 만들기. **Quick trail create** 화면이 나와도 그대로 됨 (2026-11-20 소유자 화면: 이름, 버킷 자동 생성 `aws-cloudtrail-logs-<계정 번호>-…`, 여러 리전 trail, 관리 이벤트 기록; KMS 칸 없음) | [x] |
| 22 | 검색 `S3` → 21번 버킷 → **Management** → **Lifecycle rules** → **Create lifecycle rule** *(미검증)* | 규칙 이름 `expire-400d`, 버킷 전체, **현재 버전 400일 뒤 만료** | [x] |

**G. 경보와 예산 (약 15분)**

| # | 할 일 | 넣을 값 | 확인 |
|---|---|---|---|
| 23a·23b | 콘솔 아래 왼쪽 **CloudShell** (Golden Hour Code 계정, 시드니) → 아래 명령 상자를 통째로 붙여 넣기 | SNS 주제 `qg-alerts` + 메일 구독 `contact@quantgeneration.com`, 경보 `qg-signup-spike` (`SignUpSuccesses`, Sum, 1시간, > 50), `qg-signup-throttle` (`SignUpThrottles`, Sum, 5분, ≥ 1). 마지막 표에 두 경보가 `INSUFFICIENT_DATA` 또는 `OK`로 보이면 됨 | [x] |
| 23c | **메일함 확인** | AWS가 보낸 "AWS Notification - Subscription Confirmation" 메일의 **Confirm subscription** 을 누름. **이걸 안 누르면 경보 메일이 오지 않습니다** | [x] |
| 24 | `Billing and Cost Management` → **Budgets** 목록부터 봄 | **예산이 이미 있으면 그것을 씀** (2026-11-20 Golden Hour Code에는 `My Monthly Cost Budget` $100이 있어 24a·24b를 만들지 않음): 그 예산의 알림 받는 메일만 확인 (2026-09-30 뒤 새로 넣은 주소는 확인 메일을 눌러야 알림이 옴 — 화면 안내). 없을 때만: **Create budget** → **Use a template (simplified)** → **Monthly cost budget**, 받는 메일 `contact@quantgeneration.com`. **월 금액은 이번 달 이미 쓴 금액보다 크게** (작으면 만들자마자 울림). Zero spend budget은 건너뜀 | [x] |
| 25 | 메모장에 한 줄씩 | "2026-11-20 quantgen-prod 생성, 그룹 qg-admins, 삭제 보호 Active, trail qg-audit (400일 만료), 경보 2개 → SNS qg-alerts (구독 확인), 예산: 기존 월 예산 사용" (관리자 안내서 16.2절 변경 기록) | [x] |

23a·23b 명령 (2026-11-20 소유자가 실행함). **왜 콘솔이 아니라 명령인가:** 가입이 한 번도 없는 새 풀은 CloudWatch에 Cognito 지표가 아직 없어서, 경보 만들기의 **Select metric** 목록에 운영 풀이 나오지 않습니다 (2026-11-20 소유자 화면: `quantgen-dev`만 보임; 지표가 활동 뒤에 생긴다는 것은 화면으로 확인, AWS 문서 문장은 못 찾음). 명령으로는 아직 데이터가 없는 지표에도 경보를 걸 수 있습니다. 지표 이름과 구분값 (`UserPool` + `UserPoolClient`)은 AWS 문서 "User pool metrics in CloudWatch"로 확인. 웹 가입 화면은 `quantgen-web` 클라이언트로 가입하므로 그 클라이언트 값으로 겁니다 (관리자가 만든 계정은 클라이언트 이름 "Admin"으로 따로 집계됨).

```bash
R=ap-southeast-2
POOL=ap-southeast-2_pQEsrAvvb          # 운영 풀 quantgen-prod (1-2절)
CLIENT=77qi9vi90i118rck1ppisbca7r      # quantgen-web (1-2절)
TOPIC=$(aws sns create-topic --region $R --name qg-alerts --query TopicArn --output text)
aws sns subscribe --region $R --topic-arn "$TOPIC" --protocol email --notification-endpoint contact@quantgeneration.com
aws cloudwatch put-metric-alarm --region $R --alarm-name qg-signup-spike \
  --namespace AWS/Cognito --metric-name SignUpSuccesses \
  --dimensions Name=UserPool,Value=$POOL Name=UserPoolClient,Value=$CLIENT \
  --statistic Sum --period 3600 --evaluation-periods 1 \
  --threshold 50 --comparison-operator GreaterThanThreshold \
  --treat-missing-data notBreaching --alarm-actions "$TOPIC"
aws cloudwatch put-metric-alarm --region $R --alarm-name qg-signup-throttle \
  --namespace AWS/Cognito --metric-name SignUpThrottles \
  --dimensions Name=UserPool,Value=$POOL Name=UserPoolClient,Value=$CLIENT \
  --statistic Sum --period 300 --evaluation-periods 1 \
  --threshold 1 --comparison-operator GreaterThanOrEqualToThreshold \
  --treat-missing-data notBreaching --alarm-actions "$TOPIC"
aws cloudwatch describe-alarms --region $R --alarm-names qg-signup-spike qg-signup-throttle \
  --query 'MetricAlarms[].[AlarmName,MetricName,StateValue]' --output table
```

- `--treat-missing-data notBreaching`: 가입이 없는 시간을 "문제 없음"으로 봅니다 (없으면 회원이 없는 동안 경보가 계속 애매한 상태로 남음).
- **비용 메모 (2026-11-20, 24번 확인 중):** Cost Explorer에서 **Charge type → Credit 제외**로 보니, 크레딧 적용 전 사용액이 10월 $13.73, 11월 $48.71이었고 대부분 **EC2-Instances·EC2-Other·VPC**였습니다 (Cognito·CloudTrail·SES·CloudShell은 $0.00). 지금은 크레딧이 내고 있습니다. 예산은 크레딧 적용 전 사용액을 세고, Cost Explorer 기본 화면은 크레딧을 뺀 값을 보여 주는 것으로 보입니다 *(추론, 미검증: 두 화면 숫자 $48.71 일치로 뒷받침)*. 11월 서비스별 (크레딧 적용 전, 소유자가 메인 세션에 보낸 화면): EC2-Other $39.47, EC2-Instances $5.55, VPC $2.11, Amplify $1.57 (합 $48.71). 출처는 아직 모름 (메인이 소유자와 OA-43으로 확인 중). 이 EC2 자원은 이 문서의 작업이 만든 것이 아닙니다. **소유자가 무엇인지 (EC2 Global View: 리전·이름·유형·만든 날짜) 확인하기 전에는 끄거나 지우지 않습니다** (웹사이트 세션 등 다른 작업의 것일 수 있음; Terminate는 되돌릴 수 없음).

### 1-2. 적어 둘 것 → 저에게 보내 주실 것

| 항목 | 보내도 되나 | 쓰는 곳 |
|---|---|---|
| User pool ID | 예 (비밀값 아님) | 웹사이트 요청 (2단계), 데스크톱 로그인 (나중) |
| `quantgen-web` Client ID | 예 (비밀값 아님) | 같음 |
| CloudTrail S3 버킷 이름 | 예 | 관리자 안내서 13절 |
| 화면 문구가 달랐던 단계 번호와 실제 문구 | 예 | 문서 수정 |
| AWS 로그인 비밀번호·액세스 키 | **아니요, 절대** | — |

**기록한 값 (2026-11-20, 소유자 화면에서 확인; 비밀값 아님):** 운영 풀 `quantgen-prod` = `ap-southeast-2_pQEsrAvvb` (Golden Hour Code, 시드니; 같은 계정의 `quantgen-dev` `ap-southeast-2_fV38AjJFg`는 개발용이라 그대로 둠), `quantgen-web` Client ID = `77qi9vi90i118rck1ppisbca7r`, CloudTrail 버킷 `aws-cloudtrail-logs-<Golden Hour Code 계정 번호>-0bcc59a3`, SES 신원 `no-reply@quantgeneration.com` Verified (도메인 인증으로 바로 됨, Cloudflare 설정 불필요), custom 속성 6개 있음.

---

### 1-3. 잘못 만든 풀 지우기

지울 풀은 두 경우뿐입니다. **2단계에서 웹사이트 세션에 보낸 풀 (운영 풀 `quantgen-prod`, `ap-southeast-2_pQEsrAvvb`)과 개발 풀 `quantgen-dev`는 절대 지우지 않습니다.**

| 경우 | 어느 계정 | 어떤 풀 (리전 + 이름으로 식별) |
|---|---|---|
| 1. 관리 계정의 시험 풀 (2026-11-19 생김) | **관리 계정** (…3710, Golden Hour Code가 아님) | 버지니아 (us-east-1)의 `User pool - hoa9ag`, 시드니의 `ap-southeast-2_hvH4JqdOu`. 이 두 ID는 웹사이트 세션에 보내지 않습니다 |
| 2. Golden Hour Code의 잘못된 리전 풀 (7번에서 `ap-southeast-2_`가 아니었던 풀) | **Golden Hour Code** | 시드니가 **아닌** 리전에 있는 풀 (그 리전의 User pools 목록에서 이름·ID 확인) |

순서 (두 경우 같음; 운영 풀이 다 된 뒤에):
1. 오른쪽 위 계정이 위 표의 계정인지, 지울 풀의 **리전과 이름·ID**가 위 표와 맞는지 확인합니다. 운영 풀·개발 풀을 지우지 않게 이 확인을 꼭 합니다.
2. 리전을 그 풀의 리전으로 맞춥니다.
3. 풀 → **Settings** 화면의 **Deletion protection** 구역 → **Deactivate** (콘솔로 만든 풀은 삭제 보호가 기본으로 켜져 있음, `ACCOUNT_SETUP.md` P15) *(구역·버튼 이름 부분 확인)*.
4. 풀 오른쪽 위 **Delete user pool** → 확인 글자 입력 → **Delete**.
5. 메모장의 변경 기록에 "날짜 | <계정> <리전> <풀 이름> 삭제 | 회원 0명" 한 줄.

## 2단계. 전달 (웹사이트 세션에 붙여 넣기)

이 세션은 웹사이트 저장소를 직접 고치지 않습니다. 아래를 웹사이트 세션 대화창에 붙여 넣어 주세요.

1. `ACCOUNT_SETUP.md` 3부 "복사용" 상자 안의 글 전체 (ACC-1~ACC-10)를 복사합니다.
2. 그 아래에 다음 메시지를 이어 붙입니다 (풀 ID·클라이언트 ID는 이미 채워 둠; 첫 줄의 `2026-11-xx`만 붙여 넣는 날로 바꿈):

```text
[소유자 → 웹사이트 세션] 정식 회원 계정 (D11) 추가 정보 (2026-11-xx)

- 운영 사용자 풀: 시드니 ap-southeast-2
  - User pool ID: ap-southeast-2_pQEsrAvvb (1단계 17번, 2026-11-20 기록)
  - Web client ID (quantgen-web, 비밀값 없는 SPA): 77qi9vi90i118rck1ppisbca7r
- 이메일 MFA 회원의 비밀번호 분실 (소유자 결정 2026-11-19·2026-11-20): Cognito가 그 회원의 비밀번호 찾기를 거절하므로
  관리자가 두 번째 확인 뒤 임시 비밀번호를 줍니다. 그래서
  - ACC-3: 로그인 응답이 NEW_PASSWORD_REQUIRED면 새 비밀번호 화면 (ACC-1과 같은 규칙: 10자, 숫자·소문자·대문자·특수문자) →
    RespondToAuthChallenge. 이 화면에 "이메일 MFA 대신 인증 앱(OTP)으로 바꾸기를 권합니다" 한 줄 + 계정 페이지 링크.
  - ACC-4: 비밀번호 찾기가 그 이유로 거절되면 "이 계정은 스스로 비밀번호를 찾을 수 없습니다. 가입한 이메일로
    contact@quantgeneration.com에 문의해 주세요" 표시 (다른 오류 문구는 계정 존재를 드러내지 않게 그대로).
- 소유자 결정 (2026-11-18): 운영자는 개인 (회사 표시 "(주)" 쓰지 않음, 문구는 메인 세션 정책 PR 병합 뒤 원문 재생성),
  문의·개인정보 메일 contact@quantgeneration.com (ACC-8), 최소 연령 무료 만 14세 (ACC-1 그대로) / 유료 만 19세 (나중).
- 공개 전까지 AUTH_UI_ENABLED=false 유지.
- 공개 전 소유자 시험용으로, 플래그를 켠 미리보기 주소 (공개 주소가 아닌 곳) 하나가 필요합니다. 준비되면 주소를 알려 주세요.
- 결과는 WEBSITE_AWS_SESSION_CURRENT.md에 기록해 주세요.
```

3. 붙여 넣은 날짜를 저에게 알려 주세요 (인계 파일에 기록합니다).

---

## 3단계. 시험 (관리자 기능 따라 하기)

두 번에 나눠 합니다. 3-A는 1단계 직후 콘솔과 CloudShell만으로 됩니다. 3-B는 웹사이트 화면(미리보기)이 나온 뒤입니다.

### 3-A. 콘솔만으로 (1단계 직후, 약 30분)

준비: 시험용 메일 별칭 (예: `내아이디+qgtest1@gmail.com`), 시험용 비밀번호 1개 (10자 이상, 대·소문자·숫자·특수문자. **실제로 쓰는 비밀번호와 다르게**, 시험 뒤 버림. **작은따옴표(`'`)는 쓰지 않음**: 명령에서 비밀번호를 작은따옴표로 감싸므로 명령이 깨짐).

CloudShell을 열면 먼저 아래 값 줄을 붙여 넣어 둡니다 (`내아이디`만 본인 Gmail 아이디로 바꿈; 이 문서에는 실제 주소를 적지 않음). 아래 명령 ①~⑥은 이 값을 그대로 씁니다. 메일로 온 코드는 예시 `123456`(가입 확인)·`654321`(재설정) 자리에 실제 6자리를 넣습니다.

**CloudShell이 다시 연결되면 (창을 새로 열었거나 한동안 쉬었을 때) 이 값이 사라집니다.** 명령 전에 값 줄을 다시 붙여 넣고 마지막 `echo` 줄로 값이 보이는지 확인합니다 (2026-11-20 T9에서 값이 빠져 `argument --region: expected one argument` 오류).

```bash
R=ap-southeast-2
POOL=ap-southeast-2_pQEsrAvvb              # 운영 풀 quantgen-prod (1-2절)
CLIENT=77qi9vi90i118rck1ppisbca7r          # quantgen-web (1-2절)
TESTMAIL='내아이디+qgtest1@gmail.com'      # 시험 계정 1 (T1~T13)
TESTMAIL2='내아이디+qgtest2@gmail.com'     # 시험 계정 2: 이메일 MFA 회원 (T16~T19, W9~W10)
echo "$R $POOL $CLIENT $TESTMAIL $TESTMAIL2"
```

**T3~T8 공통 시작 (콘솔):** 오른쪽 위 계정 **Golden Hour Code**, 리전 **Asia Pacific (Sydney)** 확인 → 위 검색창 `Cognito` → **User pools** → `quantgen-prod` (ID `ap-southeast-2_pQEsrAvvb`) → 왼쪽 **User management** → **Users**. 아래 버튼 이름은 AWS 문서로 확인했지만 문서가 약 1년 전 것이라 화면 문구가 다를 수 있습니다 (문서 확인, 화면 문구 다를 수 있음). 다르면 실제 문구를 결과 칸에 적어 주세요. 〔AWS 문서: [Managing and searching for user accounts](https://docs.aws.amazon.com/cognito/latest/developerguide/how-to-manage-user-accounts.html), [Managing users in your user pool](https://docs.aws.amazon.com/cognito/latest/developerguide/managing-users.html)〕

| # | 할 일 | 정확한 방법 | 기대 결과 | 결과 |
|---|---|---|---|---|
| T1 | 시험 계정 가입 | 콘솔 위 `>_` (CloudShell) → 아래 명령 ① | 시험 메일함에 6자리 코드 메일 도착 (발신 `no-reply@quantgeneration.com`, 회신 주소 `contact@`) | |
| T2 | 가입 확인 | 명령 ② (코드 넣기) | 오류 없음. 콘솔 **Users** 에서 상태 **Confirmed** | |
| T3 | 회원 목록·검색 (관리자 안내서 1절) | 1. 공통 시작으로 **Users** 화면. 2. 목록 위 **Property:** 드롭다운 (처음 값 **User name**)을 **Email**로 바꿈. 3. 오른쪽 **Search users by attribute** 칸에 `내아이디+qgtest` 입력 → Enter. 콘솔 검색은 언제나 **앞부분 일치** ("~로 시작")이고 이메일은 대소문자를 가리지 않으므로 주소 앞부분만 넣어도 됩니다. 4. 목록 열: User name / Email address / Email verified / Confirmation status / Status. **User name** 열은 이메일이 아니라 `c99ec458-…` 같은 UUID(sub)입니다 (이메일로 로그인하는 풀이라 정상). 5. 목록이 안 나오면 CloudShell로 같은 검색: `aws cognito-idp list-users --region $R --user-pool-id $POOL --filter 'email ^= "내아이디+qgtest"'` | 시험 계정 **1개**, Email verified **Yes**, Confirmation status **Confirmed**, Status **Enabled** | 그대로 됨 (2026-11-20 소유자 화면: Property: / Search users by attribute, 목록 위 버튼 **Delete user**·**Create user**) |
| T4 | 회원 상세 (2절) | 1. T3 목록에서 그 회원의 **User name** 링크 (UUID)를 누름 (이메일 칸이 아니라 이 링크). 2. 화면 제목 **User: <sub>**, 오른쪽 위 **Actions**. 3. **User information** 구역: User ID (Sub), Account status (Enabled), Created time, Alias attributes used to sign in (Email), Confirmation status (Confirmed), Last updated time, MFA setting (**MFA inactive**: 회원 MFA가 선택이라 정상), MFA methods. 4. **User attributes (5)** 구역 (오른쪽 **Edit**): 값이 있는 속성만 보임 — `custom:age14` = Y, `custom:mkt_opt` = N, `custom:terms_ver` = test, `email` (**Verified** 표시), `sub`. 명령 ①에서 넣지 않은 custom 속성 3개는 값이 없어 안 보임 (정상). 5. 화면 어디에도 비밀번호가 없는지 봄. **아무것도 바꾸지 않음** | 위 값이 보이고 비밀번호는 없음 | 그대로 됨 (2026-11-20 소유자 화면) |
| T5 | 정지 전 삭제 (부록 C7) | 1. **Users** 목록으로 돌아가 시험 회원 줄 왼쪽의 **선택 단추(라디오)**를 누름. 2. 목록 위 **Delete user**를 누름. 3. 열린 창 **Delete user "<sub>"?** 를 읽기만 함: "You must disable sign-in access for the user … before you delete the user profile." 문장, 창 안의 검은 **Disable user access** 단추, 회색(눌리지 않는) **Delete**. 4. **Cancel**만 누름. **창 안의 Disable user access는 누르지 않음** (누르면 이 창에서 정지되고 Delete가 열릴 수 있음; 정지는 T6에서 Actions로 따로 함) | 정지 전에는 **Delete가 막혀 있음**. Cancel 뒤 회원은 그대로 **Enabled** | 그대로 됨 (2026-11-20 소유자 화면) |
| T6 | 정지 (4절, 부록 C1) | 1. T4처럼 회원 상세로 들어감. 2. 오른쪽 위 **Actions** → **Disable user access**. 3. 확인 창에서 **Disable** | 문서상 효과: 그 회원의 모든 세션 로그아웃, 액세스·새로고침 토큰 폐기, 로그인 막힘. 상세의 **Account status**와 목록의 **Status**가 **Disabled** | 그대로 됨 (2026-11-20) |
| T7 | 해제 (부록 C3) | 1. 같은 회원 상세 → **Actions** → **Enable user access**. 2. 확인 창에서 확인 (**Enable**) | 상태가 **Enabled**로 돌아옴 | 그대로 됨 (2026-11-20) |
| T8 | 비밀번호 재설정 (6절, 부록 C4) | 1. 같은 회원 상세 → **Actions** → **Reset password**. 2. 확인 창에서 확인. 3. 시험 메일함 (Gmail; 안 보이면 스팸함)에서 `no-reply@quantgeneration.com`이 보낸 재설정 코드 메일을 엶. **코드는 1시간 유효** → 1시간 안에 T9 (명령 ③) | 확인 상태 **Reset required** (화면에 `RESET_REQUIRED`로 보일 수 있음), 코드 메일 도착 | 코드 메일 도착 (2026-11-20) |
| T9 | 새 비밀번호 정하기 (부록 C5 대신) | CloudShell이 다시 연결됐으면 **먼저 값 줄 (`R=`·`POOL=`·`CLIENT=`·`TESTMAIL=`·`TESTMAIL2=`)을 다시 붙여 넣고** `echo "$R $CLIENT $TESTMAIL"`로 세 값이 보이는지 확인 → 명령 ③ (메일의 코드 + 새 시험 비밀번호). 값이 빠지면 `argument --region: expected one argument` 오류가 남 (2026-11-20 실제로 겪음) | **아무것도 출력되지 않고** 프롬프트로 돌아오면 성공. 콘솔에서 상태 **Confirmed**. `ExpiredCodeException`이면 1시간이 지난 것 → T8 **Reset password**를 다시 하고 새 코드로. `InvalidPasswordException`이면 13번 규칙 (10자, 숫자·소문자·대문자·특수문자) | 그대로 됨 (2026-11-20, 값 줄 다시 넣은 뒤) |
| T10 | 인증 메일 재발송 버튼이 있는지 (0.3표 7번) | 상태가 Unconfirmed인 계정이 없으면 건너뛰고, 있으면 **Actions** 메뉴에 재발송 항목이 있는지만 봄 | 있음/없음 | |
| T11 | 그룹 넣기·빼기 (9절, 0.3표 6번) | **Groups** → `qg-admins` → **Add user to group** → 시험 계정 → 추가 → 같은 화면에서 빼기 버튼 문구 확인 → 빼기 | 넣기·빼기 모두 됨, 빼기 버튼 실제 문구 | |
| T12 | 속성 편집 화면 (8절, 0.3표 2·3번) | 회원 상세 → **User attributes** 편집 버튼 → 화면만 보고 **아무것도 바꾸지 않고 취소** | 편집 버튼 문구, "Mark email address as verified" 비슷한 체크의 실제 문구 | |
| T13 | 삭제 (5절, 부록 C6) | **Actions** → **Disable user access** → **Disable** → **Actions** → **Delete user** (또는 목록에서 선택 → **Delete user**) → 확인 창 **Delete** | 목록에서 사라짐. 확인 창은 이름 입력을 **요구하지 않음** | 그대로 됨 (2026-11-20; 이름 입력 없음) |
| T14 | 관리자 기록 (부록 A 6번) | **정해진 대기 시간 없음**: T13 직후 `CloudTrail` → **Event history** → 필터 **Event source** = `cognito-idp.amazonaws.com` → 빠진 것이 있으면 몇 분 뒤 새로고침 (15분이 지나도 빠지면 알림). 이 목록은 **계정 전체**라 개발 풀 `quantgen-dev`의 기록도 섞임 → 시험한 시간대로 좁히거나, 이벤트를 열어 **View event**의 `userPoolId`가 운영 풀인지 봄. 추가 확인 1회: `ConfirmForgotPassword` 또는 `InitiateAuth` 이벤트 하나를 열어 **View event** (이벤트 원문 JSON)의 `requestParameters`·`additionalEventData`에 회원의 `username`이나 `sub`가 있는지 봄 (관리자 안내서 6.1 (나)②에 씀) | 관리자 쪽: `AdminDisableUser` 2개 (T6·T13), `AdminEnableUser`, `AdminResetUserPassword`, `AdminDeleteUser`. 회원 쪽: `SignUp`, `ConfirmSignUp`, `ForgotPassword`, `ConfirmForgotPassword`, `InitiateAuth` | 그대로 됨 (2026-11-20 소유자 CSV 내보내기): 관리자 4종 모두 (User name = Identity Center 역할 세션, Source IP = 관리자 IP), 1~2분 안에 보임. 회원 쪽 요청도 Source IP (여기서는 CloudShell의 AWS IP)·User agent와 함께 기록되지만 CSV의 **User name 칸이 비고 Resources가 []** → CSV만으로는 어느 회원인지 모름. View event 확인은 **미검증** (소유자 확인 대기) |
| T16 | 이메일 MFA 회원 준비 (6.1절) | 두 번째 시험 별칭 (`내아이디+qgtest2@…`)으로 명령 ①·② → 명령 ④ (그 회원에게 이메일 MFA 켜기) | 오류 없음 | |
| T17 | 이메일 MFA 회원의 비밀번호 찾기 | 명령 ⑤ | **거절됨** (오류 이름과 메시지를 그대로 적어 주세요; 미검증 — 웹사이트 ACC-4가 이 이름에 안내를 붙임). 웹은 이때 contact@ 문의 안내 (ACC-4, W10) | |
| T17a | 이메일 MFA 회원에게 관리자 **Reset password** (관리자 안내서 6절·6.1, 3차 검토 F3) | 콘솔 → 시험 계정 2의 회원 상세 → **Actions** → **Reset password** → 확인 | 막히는지 (오류 문구), 아니면 코드 메일이 오는지와 확인 상태 (**Reset required**인지)를 적기 (**미검증**). 막히면 관리자 안내서 6절·17-A대로 이메일 MFA 회원에게는 Reset password 대신 6.1. 메일이 오고 Reset required가 되면 그 회원은 웹 비밀번호 찾기 화면에서 그 코드를 쓸 수 있는지까지 (W10과 함께) | |
| T18 | 두 번째 확인 실패 → 발급 안 함 (6.1절 1번 (나)) | 명령을 실행하지 않음. 거절 답장 문구와 변경 기록 한 줄만 메모장에 써 봄: `날짜 \| 거절 \| 처리한 사람 \| 회원 sub \| (가) 맞음 (나) 맞지 않음` | 발급 없음, 기록 한 줄 | |
| T19 | 두 번째 확인 통과 → 임시 비밀번호 (6.1절 1~3번) | (가) 시험 메일 주소에서 contact@로 요청 메일 → (나) ① **메일함에서 읽을 수 없는 것** 하나를 시험 삼아 정해 대조 (예: 시험 시작 때 메모장에만 적어 둔 낱말; 가입 시각·인증 메일 내용처럼 메일함에서 알 수 있는 것은 쓰지 않음). ②(최근 로그인 IP·지역)는 T14의 View event 확인이 끝나기 전에는 쓰지 않음 → 명령 ⑥ (작은따옴표 없는 임시 비밀번호) → `history -c` | 상태 **Force change password**. 로그인·강제 변경은 3-B의 W9 | |
| T15 | 정리 (T16~T19 뒤 마지막) | 두 번째 시험 계정은 W9·W10 뒤 T13처럼 지움. CloudShell에서 `history -c` | — | 첫 시험 계정은 T13에서 지움 (2026-11-20). 두 번째 계정은 아직 만들지 않음 |

CloudShell 명령 (위 값 줄을 먼저; 비밀번호와 코드만 바꿈, 비밀번호는 작은따옴표 안에, 비밀번호에 작은따옴표를 넣지 않음):

```bash
# ① 시험 계정 가입 (T1; 웹 가입 화면과 같은 API)
aws cognito-idp sign-up --region $R \
  --client-id $CLIENT \
  --username $TESTMAIL \
  --password '<시험용 비밀번호>' \
  --user-attributes Name=email,Value=$TESTMAIL Name=custom:terms_ver,Value=test Name=custom:age14,Value=Y Name=custom:mkt_opt,Value=N

# ② 가입 확인 (T2; 메일로 온 6자리를 123456 자리에)
aws cognito-idp confirm-sign-up --region $R \
  --client-id $CLIENT --username $TESTMAIL --confirmation-code 123456

# ③ 재설정 뒤 새 비밀번호 (T9; T8 메일의 코드를 654321 자리에. 성공하면 아무것도 출력하지 않음)
echo "$R $CLIENT $TESTMAIL"            # 세 값이 보이는지 먼저 확인 (비면 값 줄을 다시)
aws cognito-idp confirm-forgot-password --region $R \
  --client-id $CLIENT --username $TESTMAIL \
  --confirmation-code 654321 --password '<새 시험용 비밀번호>'

# ④ 시험 계정 2 가입·확인 뒤 이메일 MFA 켜기 (T16; ①·②를 $TESTMAIL2로 한 번 더 한 뒤)
aws cognito-idp admin-set-user-mfa-preference --region $R \
  --user-pool-id $POOL --username $TESTMAIL2 \
  --email-mfa-settings Enabled=true,PreferredMfa=true

# ⑤ 이메일 MFA 회원의 비밀번호 찾기 (T17, 거절이 기대 결과; 오류 이름을 적음)
aws cognito-idp forgot-password --region $R \
  --client-id $CLIENT --username $TESTMAIL2

# ⑥ 임시 비밀번호 (T19, 관리자 안내서 6.1절 3번; 작은따옴표를 넣지 않은 비밀번호)
aws cognito-idp admin-set-user-password --region $R \
  --user-pool-id $POOL --username $TESTMAIL2 \
  --password '<임시 비밀번호>' --no-permanent

# 끝나면
history -c
```

- 출처 (T3~T8): AWS 문서 [Managing and searching for user accounts](https://docs.aws.amazon.com/cognito/latest/developerguide/how-to-manage-user-accounts.html) (검색은 앞부분 일치, 정지·해제·재설정·삭제), [Managing users in your user pool](https://docs.aws.amazon.com/cognito/latest/developerguide/managing-users.html). 메인 세션 확인 2026-11-20; 문서가 약 1년 전 것이라 버튼 문구는 화면과 다를 수 있음.
- 화면에 남는 값: 시험 이메일 1개와 시험 비밀번호 (내 시험 계정이라 개인정보 문제는 없지만, `history -c` 로 지움).
- ① 에서 `NotAuthorizedException` 이 나오면 자가 가입이 꺼진 것입니다 → **Sign-up** → **Self-service sign-up** → **Edit** → **Enable self-registration** 체크. `InvalidParameterException ... custom:` 이 나오면 9단계 속성 이름이나 16단계 쓰기 권한을 확인하세요.
- **로그인이 막히는지 (부록 C2)** 는 명령줄로 보기 어렵습니다 (우리 클라이언트는 SRP 로그인만 허용). 3-B에서 웹 화면으로 확인합니다.

### 3-B. 웹 미리보기가 나온 뒤 (약 30분)

웹사이트 세션이 플래그를 켠 미리보기 주소를 주면:

| # | 할 일 | 기대 결과 | 결과 |
|---|---|---|---|
| W1 | 새 시험 별칭으로 웹 가입 → 코드 → 로그인 | 됨. 필수 체크 2개 없이는 가입 안 됨, 광고 체크는 처음에 꺼져 있음 | |
| W2 | 콘솔에서 그 계정 정지 (4절) → 웹에서 로그인 | **로그인 막힘** (부록 C2) | |
| W3 | 해제 → 웹 로그인 | 됨 | |
| W4 | 콘솔에서 재설정 (6절) → 웹 "비밀번호 찾기"로 새 비밀번호 | 됨 (부록 C5) | |
| W5 | 웹 계정 페이지: 2단계 인증 켜기 (인증 앱) → 로그아웃 → 로그인 | 인증 앱 코드 단계가 나옴 | |
| W6 | 웹 계정 페이지: 이메일 변경 → 새 주소 코드 | 바뀜. 코드 넣기 전에는 옛 주소로 로그인됨 | |
| W7 | 웹 계정 페이지: 내 정보 내려받기 | JSON 파일. 비밀번호 없음 | |
| W8 | 웹 계정 페이지: 회원 탈퇴 | 콘솔 Users에서 사라짐 | |
| W9 | T19의 시험 계정 2로 웹 로그인 (임시 비밀번호) → 이메일 MFA 코드 | **새 비밀번호 화면** (규칙 표시, "인증 앱으로 바꾸기를 권합니다" 한 줄) → 새 비밀번호로 들어감 (ACC-3). 7일 지난 임시 비밀번호는 안 됨 | |
| W10 | 시험 계정 2로 웹 "비밀번호 찾기" | 거절 + "contact@quantgeneration.com으로 문의" 안내 (ACC-4) | |

결과는 관리자 안내서 **부록 C** 표 (C1~C8)와 위 표에 "그대로 됨/다름: 실제 문구"로 적어 저에게 보내 주세요.

---

## 4단계. 공개 전 (체크 8개 + 법률 확인)

**시작 조건**: 메인 세션의 정책 문서 PR이 main에 병합됨, 웹사이트 세션이 화면을 플래그 꺼진 채 배포함, 3단계 끝남.

| # | 확인 | 정확한 방법 | 통과 기준 | 결과 |
|---|---|---|---|---|
| 1 | 운영자 표기 | 공개 사이트의 처리방침·약관 페이지에서 Ctrl+F `(주)` 와 `넥스트제너레이션` | 0건. 운영자 = 개인 성명 + QUANTGEN, 책임자 = 같은 사람, 메일 = `contact@quantgeneration.com` | |
| 2 | 국외 이전·처리위탁 | 처리방침에서 "호주" 또는 "시드니", "Amazon Web Services" 검색 | 국외 이전 표 (받는 자, 국가, 시기·방법, 항목, 목적, 보유, 거부 방법)와 위탁 표가 채워져 있음 | |
| 3 | 메일 수신 | 다른 주소 (예: 휴대폰 메일)에서 `contact@quantgeneration.com` 으로 "수신 시험" 메일 | 받음. 받은 시각 메모 | |
| 4 | 회원 쪽 전체 흐름 | 3-B의 W1, W4~W8을 **운영 풀**에서 본인 실제 이메일로 한 번 더 (가입 → 코드 → 로그인 → MFA → 이메일 변경 → 비밀번호 찾기 → 내려받기 → 탈퇴) | 모두 성공 | |
| 5 | 관리자 기능 | 3단계 T5~T13, T16~T19 + W2~W3, W9~W10 결과 | 모두 "그대로 됨" (다른 곳은 문서 수정 뒤 다시) | |
| 6 | 관리자 기록 | 3단계 T14 | 관리자 작업이 Event history에 보임 | |
| 7 | 경보·예산 메일 | CloudShell: `aws cloudwatch set-alarm-state --region ap-southeast-2 --alarm-name qg-signup-spike --state-value ALARM --state-reason "test"` → 몇 분 안에 `contact@` 로 경보 메일. 예산은 메일 주소 등록만 확인 (일부러 울릴 수 없음) | 경보 메일 받음 (경보는 다음 평가 때 저절로 OK로 돌아옴) | |
| 8 | 법률 확인 | 아래 "118 상담에서 물을 것" | 답을 한 줄씩 메모 | |

**118 상담에서 물을 것** (개인정보 침해 신고센터, 국번 없이 118. 무료)

1. 법인 없이 개인이 무료 회원 서비스를 운영할 때, 처리방침의 운영자·개인정보 보호책임자를 개인 성명으로 적고 문의 창구를 이메일 하나(`contact@`)로 두면 충분한가요? 전화번호도 꼭 적어야 하나요?
2. 회원 정보를 호주 시드니의 AWS에 보관합니다. 처리방침에 국외 이전 표를 공개하는 것으로 충분한가요, 아니면 가입 때 별도 동의를 받아야 하나요?
3. 이메일·비밀번호만 받는 가입에서 "[필수] 개인정보 수집·이용 동의" 체크박스 없이 안내 문장만 두어도 되나요?
4. 만 14세 이상 여부를 "본인 진술 체크"로만 확인해도 되나요?
5. 1인 운영 소규모 서비스도 내부 관리계획을 문서로 만들어야 하나요?

**모두 통과하면**: 저에게 "공개 전 8개 통과"라고 알려 주세요. 소유자 본인 계정을 웹에서 가입해 `qg-admins` 에 넣고 (관리자 안내서 9절), 웹사이트 세션에 플래그 `AUTH_UI_ENABLED` 를 켜 달라고 전달합니다 (= 공개).

---

## 5. 법인 설립을 알려 주시면

"법인 설립 완료: <법인 등기상 이름>" 이라고만 말씀해 주세요. 그날 바로:
1. 이 세션이 계정 문서의 운영자 표기를 법인명으로 바꾸고 (`ACCOUNT_SETUP.md` 0.1절), 메인 세션에 정책 문서 값을 넘깁니다.
2. 메인 세션 정책 PR → 웹사이트 원문 재생성.
2a. AWS 계정 **두 개 모두** (프로젝트 계정 Golden Hour Code …8543, 관리 계정 …3710): 각 계정의 루트 로그인 이메일을 법인 이메일 주소로, 연락처(Contact information: 이름·회사명·우편 주소·전화)를 법인 것으로. 각 계정의 루트로 로그인해서: 오른쪽 위 계정 → **Account** → Account details / Contact information → **Edit** *(문구 미검증)*. 계정은 새로 만들지 않습니다 (풀·회원 그대로). 소유자가 2026-11-19 개인 이메일로 계정을 올렸으므로 이 단계가 필요합니다.
3. **이미 회원이 있다면**, 회원 정보를 법인으로 넘기기 **전에** 회원에게 미리 알려야 합니다 (홈페이지 게시라면 30일 이상). 그래서 공개 문서의 이름이 실제로 바뀌는 날은 알림 뒤가 될 수 있습니다. 공개 전(회원 0명)이면 이 절차가 필요 없습니다. 〔법률 자문이 아닙니다. 근거: 개인정보 보호법 제27조, 시행령 제29조 · https://itwiki.kr/w/개인정보_보호법_제27조 · 2026-11-17 확인〕


---

## 6. 기타 할 일: Nautilus 표의 owner_confirmed 두 줄 새로 쓰기

회원 계정과는 별개입니다. 소유자 요청(2026-11-19)으로 여기에 함께 적습니다.

**근거 (main `6e077dc`에서 확인, 2026-11-19)**
- 절차: `docs/nautilus_bridge/RUNBOOK_windows.md` 7A.3절 2번. 러너 규칙 R-11: 표나 코드가 바뀌면 `--fingerprint`로 다시 재고 owner_confirmed를 새로 씀 (`tools/nautilus/runner.py`).
- 결정: `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`의 2026-11-18 절. 소유자 답 "1번 : (가) 승인" = P3-가. 메인 세션은 이렇게 기록했습니다: "두 표의 owner_confirmed 두 줄은 다음 기록 실행 전에 소유자가 새로 적으셔야 합니다(`--fingerprint`). Claude는 그 줄을 쓰지 않습니다."
- Claude는 이 줄을 쓰지 않습니다. 소유자 승인 줄이기 때문입니다.

**왜 해야 하나**

Nautilus 브리지는 코드 파일 27개의 지문(code_sha256)을 잽니다. 표의 owner_confirmed에 적힌 지문이 지금 코드와 다르면, 기록 실행을 거부합니다(R-11).

| 시점 | 코드 지문 (앞 16자리) | 두 표에 지금 적힌 값 |
|---|---|---|
| 2026-11-04 서명 때 | `f995600b36c75523` | 이 값 (E1, C3 둘 다) |
| P3-가 뒤 (11-18) | `ec72fab3c2ab8f05` | — |
| 지금 main (KEY-2 `3249af7` 뒤) | `10c27010176ad477` | 맞지 않음. 다만 OS-F2가 `config.py`를 또 바꿀 예정이라 지금은 쓰지 않음 |

`10c27010…`은 이 세션이 계산한 값이고, main `3249af7`의 실제 값과 같습니다. 그날 쓸 값은 그날 `--fingerprint`가 출력한 값입니다 (그 사이에 OS-F2 등으로 바뀝니다).

**언제 하나 (2026-11-19 메인 세션 확인)**
- **지금은 하지 않습니다.** 다음 Nautilus 기록 실행 **직전에 한 번만** 합니다. 지금 예정된 기록 실행은 없습니다.
- 앞으로 OS 세션 작업(OS-F2)이 `config.py`를 한 번 더 바꿀 예정이라 지문이 또 움직입니다. 지금 쓰면 두 번 쓰게 됩니다.
- **다음 기록 실행을 하실 때 메인 세션이 그날 순서를 드립니다.** 아래는 그날 할 일의 모양입니다.

**어떻게 하나 (그날, 소유자 Windows PC, QUANTGEN 폴더의 PowerShell)**

1. 최신 main으로 맞춥니다 (작업 중인 변경이 없는 상태에서):
   ```powershell
   git switch main
   git pull --ff-only
   ```
2. 두 표의 지문을 잽니다. **보통 앱 Python**으로 실행합니다. `tests/run_all.py`를 돌리시는 그 Python이고, Nautilus용 환경(ntvenv)이 아닙니다. 읽기만 하는 명령입니다:
   ```powershell
   python -B -m tools.nautilus.runner --fingerprint --table docs\nautilus_bridge\registration\pilot1_E1_spy.json; if ($LASTEXITCODE) { throw "fingerprint" }
   python -B -m tools.nautilus.runner --fingerprint --table docs\nautilus_bridge\registration\pilot2_C3_btcusd.json; if ($LASTEXITCODE) { throw "fingerprint" }
   ```
   각 줄이 `owner_confirmed form:`으로 시작하는 한 줄을 출력합니다.
3. 메모장으로 두 파일을 엽니다:
   - `docs\nautilus_bridge\registration\pilot1_E1_spy.json`
   - `docs\nautilus_bridge\registration\pilot2_C3_btcusd.json`

   각 파일의 `"owner_confirmed": "..."` **한 줄만** 고칩니다. 값은 2번에서 **그 표의** `owner_confirmed form:` 줄에 나온 그대로입니다 (꼴: `"<이름>, <날짜>, table <16자리>, code <16자리>"`).
4. `host_fingerprint` 줄은 2번이 같은 값을 출력하면 그대로 둡니다. **다르면 멈추고 메인 세션에 2번 출력을 보내세요.**
5. 저장할 때 인코딩은 **"UTF-8"** 입니다 ("UTF-8 (BOM 있음)"이 아님). BOM이 있으면 이후 검사(L1-36)가 실패합니다.
6. 2번을 다시 실행해 두 표 모두 오류가 없는지 봅니다.
7. **main에 바로 push하지 않습니다.** 브랜치를 만들어 PR로 올립니다 (`<YYYYMMDD>`는 오늘 날짜, `<16자리>`는 2번의 code 값):
   ```powershell
   git switch -c owner/nautilus-confirm-<YYYYMMDD>
   git add docs/nautilus_bridge/registration/pilot1_E1_spy.json docs/nautilus_bridge/registration/pilot2_C3_btcusd.json
   git commit -m "nautilus: owner_confirmed for code <16자리>"
   git push -u origin owner/nautilus-confirm-<YYYYMMDD>
   ```
   그다음 GitHub 저장소 화면에 뜨는 **Compare & pull request**를 누릅니다.
8. 메인 세션이 Linux에서 code_sha256을 다시 계산해 두 줄과 맞는지 확인합니다 (RUNBOOK 7A.4와 같은 검토). CI가 녹색이면 메인이 병합합니다. 그날 `MERGE_QUEUE.md`에 자리를 따로 둡니다.

**하지 말 것**
- `--record-baseline` 등 다른 러너 명령 출력의 지문을 옮겨 적지 않습니다. 7A.3은 위 2번의 두 줄만 씁니다.
- 원장(ledger) 파일을 고치거나 지우지 않습니다.
- 값을 맞추려고 코드를 되돌리지 않습니다.

이 문서의 법률 내용은 법률 자문이 아닙니다.
