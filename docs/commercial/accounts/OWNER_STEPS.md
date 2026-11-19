# 소유자 실행 순서: AWS → 전달 → 시험 → 공개 전

- 판: v1.2 (2026-11-19, 6절을 메인 세션 확인대로 고침: 지금 하지 않음, 보통 앱 Python, 브랜치+PR). v1.1 6절 추가, v1 2026-11-18. 작성: PAYMENTS_ACCOUNT_KEYS 세션. 소유자 요청 (원문): "위 항목 중에서 시험, 전달, AWS, 공개 전 4단계를 수행하기 위해서 해야되는 일들을 구체화하여 .md 파일로 만들어 여기서 다운로드하고 볼 수 있도록 해주세요"
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

### 1-0. 시작 전 (5분)

- [ ] `contact@quantgeneration.com` 으로 다른 주소에서 메일을 한 통 보내, 실제로 받는지 확인. 안 오면 여기서 멈추고 웹사이트 세션의 메일 작업을 먼저 끝냅니다 (가입 메일의 회신 주소이자 개인정보 문의 창구라 꼭 받아야 함).
- [ ] AWS 콘솔 로그인 계정에 MFA가 켜져 있는지: 오른쪽 위 계정 이름 → **Security credentials** → MFA 구역 *(미검증)*. 없으면 먼저 등록.
- [ ] 메모장 하나를 엽니다. 아래 "적어 둘 것"을 여기에 모읍니다 (PC에만 보관).

### 1-1. 25단계

`ACCOUNT_SETUP.md` 2부와 같은 순서입니다. 넣을 값을 그대로 옮겼습니다.

**A. 사용자 풀 (약 20분)**

| # | 할 일 | 넣을 값 | 확인 |
|---|---|---|---|
| 1 | 콘솔 로그인 → 오른쪽 위 리전 | **Asia Pacific (Sydney) ap-southeast-2** | [ ] |
| 2 | 검색창 `Cognito` → **User pools** → **Create user pool** *(미검증)* | — | [ ] |
| 3 | 앱 종류와 이름 | **Single-page application (SPA)**, 이름 `quantgen-web` | [ ] |
| 4 | 로그인 아이디 | **Email** 만 체크 (Username·Phone 체크 안 함) | [ ] |
| 5 | 자가 가입 켬, 필수 속성 | 필수 속성 **email** 만 (name·phone 등 추가하지 않음) | [ ] |
| 6 | Return URL | 비워 둠. 필수라고 나오면 `https://quantgeneration.com` → 저에게 알려 주세요 | [ ] |
| 7 | 만들기 → 풀 이름 | `quantgen-prod`. 이름을 정하는 칸이 없거나 자동 이름이면 그대로 두고 알려 주세요 | [ ] |
| 8 | 풀 → **Sign-up** → **Required attributes** | email만 있는지 확인 | [ ] |
| 9 | **Sign-up** → **Custom attributes** → **Add custom attributes** *(미검증)* | 6개, 모두 **String**, 최대 길이 64: `terms_ver`, `privacy_ver`, `age14`, `consent_at`, `mkt_opt`, `mkt_at` (화면이 앞에 `custom:`을 붙여 주면 뒷부분만 입력). **철자를 한 글자도 틀리지 않게** (나중에 못 바꿈) | [ ] |

**B. 메일 (약 15분)**

| # | 할 일 | 넣을 값 | 확인 |
|---|---|---|---|
| 10 | **Authentication methods** → Email 구역 → **Edit** *(미검증)* | — | [ ] |
| 11 | 메일 발송 방식 | **Send email with Amazon SES** *(미검증)*, SES 리전 시드니, FROM `no-reply@quantgeneration.com`, FROM 이름 `QUANTGEN`, Reply-to `contact@quantgeneration.com` → **Save changes** | [ ] |
| 12 | **Message templates** → **Verification message** | 제목: `[QUANTGEN] 이메일 인증 코드 / Email verification code` · 본문: 아래 상자 그대로 | [ ] |

12단계 본문 (그대로 붙여 넣기):
```
QUANTGEN 이메일 인증 코드: {####}
이 코드를 가입 화면에 입력해 주세요. 본인이 요청하지 않았다면 이 메일을 무시하셔도 됩니다.

Your QUANTGEN verification code is {####}
Enter this code on the sign-up screen. If you did not request it, you can ignore this email.
```
광고 문구는 넣지 않습니다.

**C. 로그인 보안 (약 10분)**

| # | 할 일 | 넣을 값 | 확인 |
|---|---|---|---|
| 13 | **Authentication methods** → **Password policy** → **Edit** *(미검증)* | Custom, 최소 **10자**, 숫자·소문자·대문자 요구 (특수문자는 요구 안 함), 임시 비밀번호 **7일**, 재사용 금지 **5** (칸이 없으면 건너뜀) | [ ] |
| 14 | **Sign-in** → **Multi-factor authentication** → **Edit** | MFA enforcement **Optional MFA**, 방법 **Authenticator apps** + **Email message** (SMS는 끔) → 저장 | [ ] |
| 15 | **Sign-in** → **User account recovery** *(미검증)* | 이메일만 | [ ] |

**D. 앱 클라이언트 (약 10분)**

| # | 할 일 | 넣을 값 | 확인 |
|---|---|---|---|
| 16 | **App clients** → `quantgen-web` → **Edit** *(미검증)* | 인증 흐름 **ALLOW_USER_SRP_AUTH**, **ALLOW_REFRESH_TOKEN_AUTH** 만 · ID·액세스 토큰 60분, 새로고침 토큰 7일 · 토큰 폐기(token revocation) 켬 · 계정 존재 숨김("Prevent user existence errors") 켬 · 속성 읽기: email, email_verified, custom 6개 · 쓰기: email, custom 6개 | [ ] |
| 17 | **Overview** *(미검증)* | **User pool ID** (예: `ap-southeast-2_xxxxxxxxx` 꼴), **Client ID** 를 메모장에 | [ ] |

**E. 관리자 그룹 (5분)**

| # | 할 일 | 넣을 값 | 확인 |
|---|---|---|---|
| 18 | **Groups** → **Create group** | 이름 `qg-admins`, Precedence `0` → **Create group** | [ ] |
| 19 | 소유자 본인 회원 계정 | **지금은 하지 않음.** 공개 직전에 웹에서 직접 가입한 뒤 그룹에 추가 (관리자 안내서 9절) | — |

**F. 삭제 보호와 관리자 기록 (약 15분)**

| # | 할 일 | 넣을 값 | 확인 |
|---|---|---|---|
| 20 | 풀 설정(Settings) 화면 → **Deletion protection** | **Active** 인지 확인, 아니면 **Activate** | [ ] |
| 21 | 검색 `CloudTrail` → **Trails** → **Create trail** *(미검증)* | 이름 `qg-audit`, **새 S3 버킷** (이름은 콘솔이 주는 대로), 로그 파일 KMS 암호화 **끔**, 관리 이벤트 **Read + Write** → 만들기 | [ ] |
| 22 | 검색 `S3` → 21번 버킷 → **Management** → **Lifecycle rules** → **Create lifecycle rule** *(미검증)* | 규칙 이름 `expire-400d`, 버킷 전체, **현재 버전 400일 뒤 만료** | [ ] |

**G. 경보와 예산 (약 15분)**

| # | 할 일 | 넣을 값 | 확인 |
|---|---|---|---|
| 23a | `CloudWatch` → **Alarms** → **Create alarm** *(미검증)* | 지표 `AWS/Cognito` → 풀 `quantgen-prod` → `SignUpSuccesses`, 통계 Sum, 기간 1시간, 조건 > 50 → 알림: 새 SNS 주제 `qg-alerts`, 메일 `contact@quantgeneration.com` → 경보 이름 `qg-signup-spike` | [ ] |
| 23b | 같은 방식 | `SignUpThrottles`, Sum, 5분, ≥ 1 → 같은 주제 `qg-alerts` → 이름 `qg-signup-throttle` | [ ] |
| 23c | **메일함 확인** | AWS가 보낸 "AWS Notification - Subscription Confirmation" 메일의 **Confirm subscription** 을 누름. **이걸 안 누르면 경보 메일이 오지 않습니다** | [ ] |
| 24a | `Billing and Cost Management` → **Budgets** → **Create budget** → **Use a template (simplified)** → **Zero spend budget** | 받는 메일 `contact@quantgeneration.com` → 만들기 | [ ] |
| 24b | 다시 **Create budget** → **Monthly cost budget** | 금액 $20, 같은 메일 | [ ] |
| 25 | 메모장에 한 줄씩 | "2026-11-xx quantgen-prod 생성, 그룹 qg-admins, trail qg-audit, 경보 2개, 예산 2개" (관리자 안내서 16.2절 변경 기록) | [ ] |

### 1-2. 적어 둘 것 → 저에게 보내 주실 것

| 항목 | 보내도 되나 | 쓰는 곳 |
|---|---|---|
| User pool ID | 예 (비밀값 아님) | 웹사이트 요청 (2단계), 데스크톱 로그인 (나중) |
| `quantgen-web` Client ID | 예 (비밀값 아님) | 같음 |
| CloudTrail S3 버킷 이름 | 예 | 관리자 안내서 13절 |
| 화면 문구가 달랐던 단계 번호와 실제 문구 | 예 | 문서 수정 |
| AWS 로그인 비밀번호·액세스 키 | **아니요, 절대** | — |

---

## 2단계. 전달 (웹사이트 세션에 붙여 넣기)

이 세션은 웹사이트 저장소를 직접 고치지 않습니다. 아래를 웹사이트 세션 대화창에 붙여 넣어 주세요.

1. `ACCOUNT_SETUP.md` 3부 "복사용" 상자 안의 글 전체 (ACC-1~ACC-10)를 복사합니다.
2. 그 아래에 다음 메시지를 이어 붙입니다 (`< >` 두 곳만 1단계 값으로 바꿈):

```text
[소유자 → 웹사이트 세션] 정식 회원 계정 (D11) 추가 정보 (2026-11-xx)

- 운영 사용자 풀: 시드니 ap-southeast-2
  - User pool ID: <1단계 17번의 User pool ID>
  - Web client ID (quantgen-web, 비밀값 없는 SPA): <1단계 17번의 Client ID>
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

준비: 시험용 메일 별칭 (예: `내아이디+qgtest1@gmail.com`), 시험용 비밀번호 1개 (10자 이상, 대·소문자·숫자. **실제로 쓰는 비밀번호와 다르게**, 시험 뒤 버림).

| # | 할 일 | 정확한 방법 | 기대 결과 | 결과 |
|---|---|---|---|---|
| T1 | 시험 계정 가입 | 콘솔 위 `>_` (CloudShell) → 아래 명령 ① | 시험 메일함에 6자리 코드 메일 도착 (발신 `no-reply@quantgeneration.com`, 회신 주소 `contact@`) | |
| T2 | 가입 확인 | 명령 ② (코드 넣기) | 오류 없음. 콘솔 **Users** 에서 상태 **Confirmed** | |
| T3 | 회원 목록·검색 (관리자 안내서 1절) | **Users** → 검색 칸 속성 **email** → `내아이디+qgtest` 입력 | 시험 계정 1개 보임 | |
| T4 | 회원 상세 (2절) | 회원 이름 클릭 | email, sub, custom 속성이 보임. 비밀번호는 어디에도 없음 | |
| T5 | 정지 전 삭제 버튼 (부록 C7) | **Actions** 를 열어 **Delete user** 가 눌리는지만 보고, **누르지 않음** | 정지 전에는 막혀 있음 (확인할 것) | |
| T6 | 정지 (4절, 부록 C1) | **Actions** → **Disable user access** → **Disable** | **Enabled** 열이 Disabled | |
| T7 | 해제 (부록 C3) | **Actions** → **Enable user access** → **Enable** | Enabled로 돌아옴 | |
| T8 | 비밀번호 재설정 (6절, 부록 C4) | **Actions** → **Reset password** → 확인 | 상태 **Reset required**, 시험 메일함에 코드 메일 | |
| T9 | 새 비밀번호 정하기 (부록 C5 대신) | 명령 ③ (메일의 코드 + 새 시험 비밀번호) | 상태 **Confirmed** 로 돌아옴 | |
| T10 | 인증 메일 재발송 버튼이 있는지 (0.3표 7번) | 상태가 Unconfirmed인 계정이 없으면 건너뛰고, 있으면 **Actions** 메뉴에 재발송 항목이 있는지만 봄 | 있음/없음 | |
| T11 | 그룹 넣기·빼기 (9절, 0.3표 6번) | **Groups** → `qg-admins` → **Add user to group** → 시험 계정 → 추가 → 같은 화면에서 빼기 버튼 문구 확인 → 빼기 | 넣기·빼기 모두 됨, 빼기 버튼 실제 문구 | |
| T12 | 속성 편집 화면 (8절, 0.3표 2·3번) | 회원 상세 → **User attributes** 편집 버튼 → 화면만 보고 **아무것도 바꾸지 않고 취소** | 편집 버튼 문구, "Mark email address as verified" 비슷한 체크의 실제 문구 | |
| T13 | 삭제 (5절, 부록 C6) | **Actions** → **Disable user access** → **Disable** → **Actions** → **Delete user** → 확인 창 (이름 입력을 요구하는지 보기) | 목록에서 사라짐 | |
| T14 | 관리자 기록 (부록 A 6번) | 10~15분 뒤 `CloudTrail` → **Event history** → 필터 Event source = `cognito-idp.amazonaws.com` | `AdminDisableUser`, `AdminEnableUser`, `AdminResetUserPassword`, `AdminDeleteUser` 가 보임. `SignUp`, `ConfirmSignUp`, `ConfirmForgotPassword` (회원 쪽 요청)도 보이는지와 IP가 남는지 **적어 주세요** (미검증 항목) | |
| T15 | 정리 | CloudShell에서 `history -c` | — | |

CloudShell 명령 (`< >` 만 바꿈, 비밀번호는 작은따옴표 안에):

```bash
# ① 시험 계정 가입 (웹 가입 화면과 같은 API)
aws cognito-idp sign-up --region ap-southeast-2 \
  --client-id <Client ID> \
  --username <시험 이메일> \
  --password '<시험용 비밀번호>' \
  --user-attributes Name=email,Value=<시험 이메일> Name=custom:terms_ver,Value=test Name=custom:age14,Value=Y Name=custom:mkt_opt,Value=N

# ② 가입 확인 (메일로 온 6자리)
aws cognito-idp confirm-sign-up --region ap-southeast-2 \
  --client-id <Client ID> --username <시험 이메일> --confirmation-code <6자리>

# ③ 재설정 뒤 새 비밀번호 (T8 메일의 코드)
aws cognito-idp confirm-forgot-password --region ap-southeast-2 \
  --client-id <Client ID> --username <시험 이메일> \
  --confirmation-code <코드> --password '<새 시험용 비밀번호>'

# 끝나면
history -c
```

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
| 5 | 관리자 기능 | 3단계 T5~T13 + W2~W3 결과 | 모두 "그대로 됨" (다른 곳은 문서 수정 뒤 다시) | |
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
