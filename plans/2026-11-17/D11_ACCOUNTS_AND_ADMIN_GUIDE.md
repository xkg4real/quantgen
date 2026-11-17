# D11 — 정식 회원 계정: 지금 할 일과 관리자 안내서 (2026-11-17)

소유자 지시 (원문): "D11 : 권장과 반대로 진행, 즉 정식 계정 생성까지 진행할 것. 이에 따라 웹사이트에서도 수정할 부분이 있을 예정. 이때, 정식 계정 생성 후 관리자가 어떻게 관리/감독할 수 있는지(구체적으로, 예. 어떤 버튼을 누른다 등)를 기능별로 정리해서 정돈된 문서 형태로 전달할 것."

**읽는 법**
- **확인**: AWS 문서·법령 해설을 검색으로 확인한 내용입니다. 출처는 8장에 날짜와 함께 적었습니다.
- **미검증**: 확인하지 못한 내용입니다. 콘솔 화면에서 직접 확인해 주세요.
- **제안**: 제가 고른 값입니다. 바꾸셔도 됩니다.
- 이 세션은 `docs.aws.amazon.com`에 직접 접속할 수 없었습니다 (세션 네트워크 허용 목록 밖). AWS 내용은 모두 2026-11-17 웹 검색 결과의 요약으로 확인했습니다. 원문을 직접 확인하려면 세션 네트워크 설정에서 `docs.aws.amazon.com`을 허용해야 합니다.

> **법률 고지.** 이 문서의 법률 내용은 법률 자문이 아닙니다. 조문 원문(국가법령정보센터)을 이 세션에서 열지 못했고, 해설 자료와 검색 요약으로 정리했습니다. 공개 전에 변호사 또는 개인정보 침해 신고센터(국번 없이 118) 상담으로 한 번 확인하시기를 권합니다.

---

## 0. 결론 (먼저)

| 질문 | 답 |
|---|---|
| 법인 설립 전, 개인 명의로 지금 정식 계정을 열 수 있나 | **예, 조건부로 가능합니다 (법률 자문 아님).** 개인도 개인정보처리자가 될 수 있습니다. 대신 아래 "먼저 고칠 것 3가지"를 끝낸 뒤 엽니다. |
| 먼저 고칠 것 3가지 | ① 공개 문서의 운영자 표기 **"(주)넥스트제너레이션" → 개인 운영자 이름**. 법인이 아직 없다는 전제에서, 회사가 아닌데 상호에 회사 표시를 쓰면 상법 제20조 위반이고 200만 원 이하 과태료 대상입니다 (제28조; 해설 자료 기준, 법률 자문 아님). ② 개인정보 처리방침의 빈칸 채우기, 그리고 **회원 정보를 호주 시드니 AWS에 보관한다는 사실(국외 이전) 공개**. ③ 열람·삭제 요청을 실제로 받을 **메일함**이 작동할 것. |
| AWS에서 무엇을 만드나 | 시드니(ap-southeast-2)에 **새 운영용 사용자 풀 `quantgen-prod`** 하나. 이메일로 로그인, 이메일 인증은 이미 인증된 SES 도메인(`quantgeneration.com`)에서 보냄, 웹사이트용 앱 클라이언트 1개, 관리자 그룹 1개, 관리자 작업 기록(CloudTrail) 1년 보관, 비용 알림. **API Gateway·Lambda 없이도 됩니다** (웹사이트가 Cognito에 바로 연결). |
| 기존 개발 풀 `quantgen-dev`를 쓰면 안 되나 | 권하지 않습니다. 로그인 방식과 필수 항목은 풀을 만든 뒤에는 바꿀 수 없는데(**확인**), 개발 풀의 설정을 아직 아무도 확인하지 않았습니다. 개발 풀은 시험용으로 남깁니다. |
| 웹사이트에서 바뀌는 것 | 가입·인증 코드·로그인·비밀번호 찾기·계정 페이지(이메일 변경, 비밀번호 변경, MFA, 광고 메일 끄기, **회원 탈퇴**, 내 정보 내려받기). 웹사이트 세션에 보낼 요청은 4장. |
| 관리자는 어디서 관리하나 | **AWS 콘솔** (Cognito, CloudTrail, CloudWatch, SES, Billing). 웹 안에 관리자 화면은 지금 만들지 않습니다. 기능별 클릭 순서는 5장. |
| 비용 | Cognito는 월 활동 회원 1만 명까지 무료 (Essentials 요금제, 계정 전체 합산) — 검색 요약으로만 확인, 가격 페이지 직접 확인 필요. 그 위로는 회원 1명당 월 $0.015. 메일·기록 비용은 소액 (3.7절). |
| 제가 할 수 없는 것 | AWS 설정 변경, 저장소 수정. AWS는 소유자께서, 정책 문서는 메인 세션이, 웹 화면은 웹사이트 세션이 합니다. |
| 법인 설립 뒤 | 회원 정보를 법인으로 옮길 때 **미리 회원에게 알려야** 합니다 (개인정보 보호법 제27조, 2.9절). 풀은 그대로 쓰고 문서의 운영자 이름만 바뀝니다. |

**진행 순서 (요약)**

| 순서 | 누가 | 무엇을 | 끝난 기준 |
|---|---|---|---|
| 1 | 소유자 | 운영자 표기(개인 이름), 문의·개인정보 메일 주소, 만 14세 기준 승인 | 이 문서 2.1~2.4에 답 |
| 2 | 메인 세션 | 정책 문서 PR (01, 02, 06, 07, 08, 16, 17, 18, 20, `release-profile.json`) | PR 병합 (뜻이 바뀌므로 소유자 승인 뒤) |
| 3 | 소유자 (AWS) | 3.6절 순서로 `quantgen-prod` 풀·앱 클라이언트·그룹·SES·CloudTrail·예산 만들기 | 풀 ID와 앱 클라이언트 ID를 웹사이트 세션에 전달 (둘 다 비밀값 아님) |
| 4 | 웹사이트 세션 | 4장 요청 구현, 플래그 꺼진 상태로 배포 | CI 녹색, 플래그 꺼짐 |
| 5 | 소유자 | 본인 이메일로 처음부터 끝까지 시험 + 5장 관리 연습 (정지·해제·삭제) | 6.1절 체크 전부 통과 |
| 6 | 소유자 | 법률 확인 한 번 (118 또는 변호사) | 메모 한 줄 |
| 7 | 웹사이트 세션 | 플래그 켜기 = 공개 | 공개 주소에서 가입 성공 |

---

## 1. 지금 상태 (확인한 것)

| 항목 | 지금 상태 | 근거 |
|---|---|---|
| AWS 리전 | 웹·메일·Cognito 모두 **시드니 (ap-southeast-2)**. 서울(ap-northeast-2)은 SES 조회가 조직 정책(SCP)에 막혀 상태를 모름 | handoff `WEBSITE_AWS_SESSION_CURRENT.md` 88~115행 |
| AWS 계정 형태 | AWS가 관리하는 조직 정책(SCP) 아래에 있음. 선택 리전 밖을 막는 `RegionFloor` 정책일 가능성 (미검증) | 같은 문서 90~93행, AWS "SCPs and RCPs for projects" 검색 결과 |
| Cognito | 개발 풀 **`quantgen-dev` (ID `ap-southeast-2_fV38AjJFg`)** 존재. 앱 클라이언트, SES 연결, 실제 가입 성공은 **확인 안 됨** | 같은 문서 117~123행 |
| SES (메일 발송) | 시드니: 운영 모드(샌드박스 해제) 켜짐, 발송 켜짐, `quantgeneration.com` 도메인 인증·DKIM 성공. 실제 발송 시험은 안 함 | 같은 문서 99~115행 |
| Amplify (웹 호스팅) | GitHub `xkg4real/website` main → Amplify 자동 배포. `quantgeneration.com`, `www`, 기본 주소 모두 같은 HTML (SHA `1dbd9ded…`) | 같은 문서 1~43행 |
| API Gateway | 시드니에 REST·HTTP API 모두 **없음** | 같은 문서 126~133행 |
| 웹 로그인·가입 화면 | 머리글에 Login·Sign Up 버튼은 있으나 **백엔드 미연결**. 지금 공개 사이트의 정확한 문구는 이 세션에서 보지 못함 (미검증) | `WEBSITE_AWS_SESSION_CURRENT.md` 248행, `WEBSITE_AWS_HANDOFF.md`, Notion 11/16 메모 |
| 메일함 | Microsoft 365는 구매·설정 전. 문의는 기존 Gmail 경로 | `WEBSITE_AWS_SESSION_CURRENT.md` 167~194행 |
| 개인정보 처리방침 (main) | `01-privacy-policy.md` v1.10, `review-required`. 운영자를 "(주)넥스트제너레이션"으로 적음. 책임자·연락처·보유기간·국외 이전 칸은 `{{…}}` 빈칸. 웹 접속·회원가입 처리는 "찾지 못함"으로 적혀 있음 | main `docs/compliance/01-privacy-policy.md` 105~173행 |
| 사업자 정보 (main) | `release-profile.json`: 상호 "(주)넥스트제너레이션", 사업자등록번호·문의 메일·전화 **null** | main `docs/compliance/release-profile.json` 5~15행 |
| 삭제 절차 (main) | `20-deletion.md`는 앱(PC) 자료 위주. "계정 삭제 엔드포인트·삭제 티켓 시스템 없음"으로 적혀 있음 | main `docs/compliance/20-deletion.md` 12~14행 |
| 연령 정책 (main) | `17-children.md`: 최소 연령 미정 `{{age.minimum_age}}` | main `docs/compliance/17-children.md` |

---

## 2. 개인 운영자로서 필요한 것 (법·정책)

> 법률 자문이 아닙니다. 조문 원문 미확인, 해설·검색 요약 기준입니다.

### 2.1 운영자 표기

| 항목 | 지금 | 바꿀 값 (제안) | 이유 |
|---|---|---|---|
| 운영자 (개인정보처리자) | (주)넥스트제너레이션 | **소유자 본인 성명 (개인), 서비스명 QUANTGEN** | 회사가 아니면 상호에 회사 표시 문자를 쓸 수 없음 (상법 제20조), 위반 시 200만 원 이하 과태료 (제28조) — **확인** (해설 자료) |
| 개인정보 보호책임자 | 빈칸 | 소유자 본인 | 사업주·대표자를 책임자로 지정할 수 있음 (시행령 제32조, 해설 기준). 1인 운영이면 본인이 맞습니다 |
| 책임자 연락처 | 빈칸 | 개인정보 전용 메일 (예: `privacy@quantgeneration.com`) **실제로 받는 메일함** | 처리방침에 책임자 연락처가 필요 (제30조, 시행령 제31조). 전화번호가 꼭 필요한지는 미검증 |
| 주소 | 서울특별시 성북구 안암로 145 | 무료 회원만이면 처리방침에는 넣지 않아도 됨 (미검증). 유료 판매 때 사업자 정보로 다시 정함 | 개인 주소를 굳이 공개하지 않기 위함 |
| 책임자 지정 신고 | — | **해당 없음** | 2026-09-11 시행 개정의 책임자 신고·이사회 의결 의무는 매출 1,800억 원 초과 등 대규모 처리자만 해당 (언론·로펌 자료, 시행령 원문 미확인) |

메일함 주의: 지금 Microsoft 365가 없습니다. 개인정보 요청 주소가 실제로 받아지는지 시험한 뒤에 처리방침에 적습니다. 방법은 웹사이트 세션의 메일 작업과 맞춰 정합니다 (예: Cloudflare 메일 전달 → 소유자 메일함, 미검증).

### 2.2 처리방침에 채울 칸 (메인 세션이 01번 문서에서 수정)

| 칸 | 값 (제안) |
|---|---|
| 적용 범위 `{{service.covered_urls_and_apps}}` | `https://quantgeneration.com` 회원 계정, (나중에) QUANTGEN 데스크톱 앱 로그인 |
| 서비스 계약·제공: 항목 | 필수: 이메일 주소, 비밀번호(운영자도 볼 수 없는 형태로 AWS가 보관), 계정 고유번호, 가입·수정 시각, 계정 상태, 약관·처리방침 버전과 동의 시각, 만 14세 이상 확인. 선택: 2단계 인증 설정 여부 |
| 서비스 계약·제공: 근거 | 계약 체결·이행에 필요 (개인정보 보호법 제15조 제1항 제4호, 원문 미확인) |
| 서비스 계약·제공: 보유 | **회원 탈퇴(계정 삭제) 즉시 삭제**. 이메일 인증을 마치지 않은 계정은 7일 뒤 삭제 (제안, 2.6절) |
| 광고성 소식 메일 | 선택. 항목: 이메일, 수신 동의 여부·시각. 근거: 동의. 보유: 동의 철회 또는 탈퇴 시까지 |
| 서비스 보안 기록 | 관리자 작업 기록과 계정 관련 요청 기록(요청 시각, 접속 IP, 요청 종류, 계정 고유번호). 보유 **1년** (제안, 2.6절) |
| 처리위탁 | 수탁자: Amazon Web Services (계약 법인명은 청구서의 판매자 표기로 확인, 미검증). 업무: 회원 계정 보관·인증(Cognito), 인증 메일 발송(SES), 웹 호스팅(Amplify), 보안 기록 보관(CloudTrail·S3) |
| 국외 이전 | 2.8절 표 |
| 권리 행사 창구 | `privacy@…` 메일, 그리고 웹 계정 페이지(직접 열람·수정·탈퇴) |
| 안전성 확보 조치 | 실제로 한 것만: 관리자 콘솔 2단계 인증, 관리자 작업 기록 1년 보관, 비밀번호는 운영자가 볼 수 없음, 전송 구간 HTTPS, 최소 수집 |
| 쿠키·저장장치 | 로그인 유지용 토큰을 브라우저 저장소에 둠 (웹사이트 세션이 실제 저장 위치를 확정해 04번 문서에 반영) |

### 2.3 가입 화면 동의 항목 (제안)

계약에 꼭 필요한 정보(이메일·비밀번호)는 "동의"가 아니라 "안내"로 처리하고, 선택 항목만 따로 체크받는 구성입니다. main `06-form-consent.md` 105~110행의 원칙(계약 이행·법정 의무·동의를 구분, 선택 항목은 기본 해제)과 같습니다. "[필수] 개인정보 수집·이용 동의" 체크박스를 따로 둘지는 법률 확인 대상입니다 (미검증).

| 항목 | 종류 | 한국어 | English |
|---|---|---|---|
| 약관 | 필수 체크 | [필수] 이용약관에 동의합니다. (보기) | [Required] I agree to the Terms of Service. (View) |
| 연령 | 필수 체크 | [필수] 만 14세 이상입니다. | [Required] I am 14 or older. |
| 개인정보 안내 | 체크 없음, 문장 | 가입하시면 계정 제공을 위해 이메일 주소와 비밀번호를 처리합니다. 정보는 호주 시드니에 있는 AWS 서버에 보관됩니다. 자세한 내용은 개인정보 처리방침에서 확인하실 수 있습니다. | When you sign up, we process your email address and password to provide your account. Your data is stored on AWS servers in Sydney, Australia. See our Privacy Policy for details. |
| 소식 메일 | **선택 체크, 기본 해제** | [선택] QUANTGEN 소식·혜택 이메일(광고)을 받겠습니다. 언제든 끌 수 있습니다. | [Optional] Send me QUANTGEN news and offers by email (advertising). You can turn this off any time. |

- 인증 코드·비밀번호 재설정·정책 변경 안내 메일은 광고가 아니므로 수신 동의가 필요 없다고 봅니다 (일반 해석, 미검증). 여기에 홍보 문구를 섞지 않습니다 (main `18-marketing-email.md` 15행).
- 동의 기록: 어떤 버전의 약관·처리방침에, 언제, 만 14세 확인, 광고 수신 여부. 3.2절의 사용자 정의 속성에 저장합니다.

### 2.4 최소 연령

| 대상 | 기준 (제안) | 이유 |
|---|---|---|
| 무료 계정 | **만 14세 이상** (스스로 확인하는 체크) | 만 14세 미만의 개인정보를 동의로 처리하려면 법정대리인 동의가 필요 (제22조의2, 원문 미확인). 우리는 그 절차를 만들지 않음 |
| 유료 계정 (나중) | 만 19세 이상 | 미성년자가 법정대리인 동의 없이 맺은 계약은 취소될 수 있음 (민법 제5조) |
| 만 14세 미만으로 밝혀지면 | 계정 정지 → 확인 → 삭제 | main `17-children.md` F17-03 절차 |

체크박스는 실제 나이 확인이 아닙니다. 처리방침과 약관에도 "확인"이 아니라 "본인 진술"이라고 씁니다 (main `17-children.md` 원칙).

### 2.5 수집 항목 최소 세트

| 항목 | 받나 | 어디에 | 이유 |
|---|---|---|---|
| 이메일 | 필수 | Cognito | 로그인 아이디, 인증 코드, 비밀번호 찾기 |
| 비밀번호 | 필수 | Cognito (운영자도 볼 수 없음, 미검증 표현 — 관리자 콘솔에 비밀번호 보기 기능은 없음) | 로그인 |
| 계정 고유번호 (sub), 가입·수정 시각, 상태 | 자동 | Cognito | 계정 관리 |
| 약관·처리방침 버전, 동의 시각, 만 14세 확인, 광고 수신 여부·시각 | 필수/선택 | Cognito 사용자 정의 속성 | 동의 기록 |
| 2단계 인증(OTP 앱) 등록 정보 | 선택 | Cognito | 계정 보호 |
| 이름, 생년월일, 전화번호, 주소 | **받지 않음** | — | 지금 쓸 데가 없음. 전화번호는 문자 비용도 생김 |
| 주민등록번호 | **절대 받지 않음** | — | 법령 근거 없이 처리 금지 (제24조의2, 원문 미확인) |
| 증권 계좌, 증권사 API 키 | **웹에서 받지 않음** | — | 키는 데스크톱 앱의 OS 키 보관함에만 (D7) |
| 표시 이름(닉네임) | 지금은 받지 않음 | — | Discussion 기능이 생길 때 추가. Cognito 표준 속성은 나중에 써도 됨 |

### 2.6 보유·파기 (제안)

| 자료 | 보유 | 파기 방법 |
|---|---|---|
| 회원 계정 | 탈퇴 시까지 | 회원이 계정 페이지에서 탈퇴 → 즉시 삭제. 또는 관리자 "Delete user" (5.5절) |
| 이메일 인증을 안 마친 계정 | 7일 | 관리자가 주 1회 목록 확인 후 삭제 (Cognito가 자동으로 지우는지는 미검증 → 자동 삭제 없다고 보고 운영) |
| 장기 미이용 계정 | 지금은 따로 정하지 않음 | 1년 미이용 파기 의무(유효기간제)는 2023-09-15 폐지됨 (**확인**, 해설 자료). 마지막 로그인 시각을 기록하려면 Lambda가 필요해 지금은 하지 않음 |
| 광고 수신 동의 | 철회 또는 탈퇴 시까지 | 계정 페이지에서 끄기 |
| 관리자 작업·보안 기록 (CloudTrail) | **1년 이상** (S3에 400일 뒤 자동 삭제, 제안) | S3 수명 주기 규칙 |
| 관리자가 만든 내보내기 파일 | 처리 끝나면 즉시 | 5.12절 |
| 권리 요청 처리 기록 | 3년 (제안) | 개인정보는 최소만 (요청 종류·날짜·결과·계정 고유번호) |

관리자 기록 1년: 개인정보처리시스템에 접속한 사람(정보주체 제외)의 접속기록을 1년 이상 보관해야 합니다 (개인정보의 안전성 확보조치 기준 제8조, 2023-9-22 시행 — **확인**, 해설 자료). 5만 명 이상이거나 민감·고유식별정보를 처리하면 2년입니다. 점검 주기는 2023년 개정으로 "월 1회"가 아니라 스스로 정하게 바뀌었습니다 (**확인**, 해설 자료). 우리는 6장에서 "월 1회"로 정합니다.

### 2.7 유출·사고 대응

| 단계 | 기준 | 근거 |
|---|---|---|
| 정보주체 통지 | 유출 등을 **알게 된 때부터 72시간 안**. 1명이라도 해당 | 개인정보 보호법 제34조 (**확인**, 해설 자료) |
| 기관 신고 | 72시간 안. ① 1천 명 이상, ② 민감·고유식별정보, ③ **외부의 불법 접근(해킹)으로 유출** — 셋 중 하나면 인원과 무관. 신고처: 개인정보보호위원회 또는 한국인터넷진흥원(KISA) | 시행령 제40조 (**확인**, 해설 자료) |
| 2026-09-11 개정 | 유출이 확정되지 않아도 "유출 가능성"을 알리는 제도와, 위조·변조·훼손까지 대상 확대가 보도됨 | 언론·로펌 자료 (**미검증**, 원문 확인 필요) |
| 통지 내용 | 유출 항목, 시점·경위, 피해 줄이는 방법, 우리의 대응, 문의처 | 제34조 (원문 미확인) |

실제 행동 순서는 5.17절 사고 대응에 있습니다.

### 2.8 그 밖의 법 포인트

| 주제 | 해야 할 것 | 근거·상태 |
|---|---|---|
| 국외 이전 (시드니 보관) | 계약 이행을 위한 처리위탁·보관이면, 처리방침에 공개하는 방식으로 이전할 수 있음. 공개 항목: 이전 항목, 국가, 시기·방법, 받는 자 이름·연락처, 목적·보유기간, 거부 방법·절차·효과 | 제28조의8 제1항 제3호, 제2항 (조문 원문 미확인. main 01번 문서 140~142행의 표가 같은 칸 구성) |
| 국외 이전 표 값 (제안) | 받는 자: Amazon Web Services (계약 법인 확인 필요) / 국가: 호주 / 시기·방법: 가입 시와 이용 중 수시, 네트워크 전송 / 항목: 2.5절 필수·선택 항목 / 목적: 회원 계정 보관·인증·인증 메일 발송 / 보유: 2.6절과 같음 / 거부: 가입하지 않거나 탈퇴. 거부하면 계정 서비스를 쓸 수 없음 (데스크톱 앱의 무료 기능은 계정 없이 사용 가능) | 제안 |
| 서울 리전으로 옮기면 | 국외 이전 공개가 필요 없어짐. 그러나 지금 계정은 서울 리전 호출이 조직 정책에 막힘 (SES 조회 사례) | 1장 |
| 광고 메일 | 사전 동의(선택), 제목 앞 "(광고)", 쉬운 무료 수신 거부, 동의받은 날부터 **2년마다 수신 동의 사실 안내** | 정보통신망법 제50조 (**확인**, 해설 자료). 야간(21~08시) 전송 별도 동의가 이메일에도 적용되는지는 미검증 |
| 권리 행사 쉽게 | 동의 철회·처리정지·탈퇴 방법을 가입보다 어렵게 만들지 않음 → 웹 계정 페이지에 탈퇴 버튼 | 제38조 (원문 미확인) |
| 권리 요청 처리 기한 | 열람·정정·삭제·처리정지 요청은 10일 안에 처리 또는 사유 통지 | 시행령 제41조·제43조·제44조 (원문 미확인) |
| 관리 계획 | 관리자 권한 부여·변경·회수 기록, 접속기록 점검 주기, 사고 대응 절차를 한 장으로 정해 둠 (6장이 그 초안) | 안전성 확보조치 기준 (소규모 처리자의 내부관리계획 면제 범위는 미검증) |
| 부가통신사업 신고 | 소규모(자본금 1억 원 이하) 부가통신사업자는 신고한 것으로 본다는 규정이 있다고 알고 있음 | 전기통신사업법 제22조 (**미검증**) |
| 개인정보 전송요구권 | 대규모 처리자 대상으로 알고 있음 → 지금은 해당 없음으로 봄 | 제35조의2 (**미검증**) |

### 2.9 법인 설립 뒤 바뀌는 것

| 항목 | 할 일 |
|---|---|
| 회원 정보 이전 | 개인 → 법인으로 넘기기 **전에 미리** 회원에게: ① 이전 사실, ② 받는 법인의 이름·주소·전화번호·연락처, ③ 이전을 원하지 않을 때의 방법 (제27조, 해설 기준. ③은 원문 미확인). 원칙은 서면 등(이메일 포함 여부 미검증), 어려우면 홈페이지에 30일 이상 게시 (시행령 제29조, 해설 기준) |
| 처리방침·약관 | 운영자 이름을 법인으로 바꾸고 새 버전 게시 |
| AWS | 풀은 그대로. AWS 계정 명의·결제 주체를 법인으로 바꾸는 일은 별도 (D7과 같은 원칙: 구조 변경 없음, 값만 바뀜) |
| 유료 | 사업자등록, 통신판매업 신고, PG, 만 19세 기준 |

---

## 3. AWS 구성 (소유자가 적용)

### 3.1 풀을 새로 만드는 이유

| 선택 | 장점 | 단점 | 권장 |
|---|---|---|---|
| A. 새 풀 `quantgen-prod` | 설정을 처음부터 맞춤. 시험 계정과 실제 회원이 섞이지 않음 | 만드는 데 30분 정도 | ★ |
| B. `quantgen-dev` 그대로 | 이미 있음 | 로그인 방식·필수 항목을 모름. 나중에 못 바꿈 (바꾸려면 새 풀 + 회원 이전) | — |

로그인 방식(이메일)과 필수 속성은 풀을 만든 뒤 바꿀 수 없습니다. 바꾸려면 새 풀을 만들고 회원을 옮겨야 합니다 (**확인**, AWS 문서 검색 요약). 사용자 정의 속성은 나중에 추가할 수 있지만 필수로 만들 수 없고, 삭제·이름 변경도 안 됩니다 (추가 가능·필수 불가는 **확인**, 삭제 불가는 미검증).

### 3.2 사용자 풀 설정표

| 설정 | 값 (제안) | 나중에 바꿀 수 있나 | 비고 |
|---|---|---|---|
| 리전 | ap-southeast-2 (시드니) | 아니요 (새 풀) | SES·Amplify와 같은 리전 |
| 풀 이름 | `quantgen-prod` | 미검증 | |
| 요금제 (feature plan) | **Essentials** (새 풀의 기본값) | 예, 언제든 | 월 1만 명 무료는 Lite·Essentials, Plus는 무료 없음 (**확인**, 검색 요약) |
| 로그인 아이디 | **이메일만** (대소문자 구분 안 함) | **아니요** | 사용자 이름 따로 안 받음 |
| 필수 속성 | **email 하나만** | **아니요** | 이름·전화번호 필수로 하지 말 것 |
| 스스로 가입 | 켬 | 예 | 대량 가입 때 잠깐 끔 (5.17절) |
| 가입 확인 | Cognito가 이메일로 코드 보내 확인 (자동 확인 켬) | 예 | 승인제를 원하면 5.3절 |
| 계정 복구 | 이메일만 | 예 | 문자(SMS) 쓰지 않음 |
| 메일 발송 | **Amazon SES 사용**, 보내는 주소 `no-reply@quantgeneration.com`, 보내는 이름 `QUANTGEN`, 회신 주소 `support@…` (실제 받는 메일함) | 예 | 기본 Cognito 메일은 하루 발송 한도가 낮아 운영에 맞지 않음 (**확인**. 한도 숫자 50통은 미검증). SES 신원은 풀과 같은 리전 권장 (**확인**) |
| 비밀번호 정책 | 최소 **10자**, 숫자·소문자·대문자 포함, 임시 비밀번호 7일 | 예 | 최소 6자까지 허용, 임시 7일이 기본 (**확인**, API 문서 요약). 10자는 제안 |
| 비밀번호 재사용 금지 | 최근 5개 | 예 | Lite에서는 못 씀, Essentials는 미검증 |
| MFA | **선택(Optional)**, 방법: **인증 앱(OTP)** + 이메일 | 예 | 이메일 MFA는 Essentials 이상 + 자체 SES 필요 (**확인**). 문자는 끔 |
| 이메일 변경 시 | 새 주소 인증 전까지 기존 주소 유지 | 예 | 콘솔 문구 "Keep original attribute value active when an update is pending" (미검증) |
| 사용자 정의 속성 | `custom:terms_ver`, `custom:privacy_ver`, `custom:age14`, `custom:consent_at`, `custom:mkt_opt`, `custom:mkt_at` (모두 문자열, 최대 64자) | 추가만 가능, 삭제·이름 변경 불가 (미검증) | 이름을 신중히. 검색 불가 (**확인**: 사용자 정의 속성은 검색 안 됨) |
| 삭제 보호 (deletion protection) | 켬 | 예 | 콘솔로 만든 풀은 기본 켜짐 (**확인**) |
| 위협 보호 (threat protection) | 지금 끔 | 예 | Plus 요금제 기능. 회원별 로그인 기록·위험 점수가 필요해지면 검토 (**확인**) |
| 관리형 로그인(AWS 화면) 도메인 | 지금 안 만듦 | 예 | 웹은 "우리의 UI". 데스크톱 앱이 브라우저 로그인을 쓰게 되면 그때 |

### 3.3 앱 클라이언트

| 항목 | 웹사이트 `quantgen-web` (지금) | 데스크톱 `quantgen-desktop` (나중) |
|---|---|---|
| 종류 | Single-page application (SPA), **공개 클라이언트(비밀값 없음)** | 공개 클라이언트(비밀값 없음). 종류는 결제·계정 세션과 정함 |
| 인증 흐름 | `ALLOW_USER_SRP_AUTH`, `ALLOW_REFRESH_TOKEN_AUTH`만 | 같은 흐름, 또는 브라우저 로그인 + PKCE |
| 토큰 유효 | ID·액세스 60분, 새로고침 7일 (제안) | 정할 것 |
| 토큰 폐기 (token revocation) | 켬 | 켬 |
| 계정 존재 여부 숨김 ("Prevent user existence errors") | 켬 (콘솔 문구 미검증) | 켬 |
| 읽기 권한 | email, email_verified, 위 사용자 정의 속성 6개 | 같음 |
| 쓰기 권한 | email, 위 사용자 정의 속성 6개 | 같음 |

- SPA 종류는 비밀값을 만들지 않습니다 (**확인**, 검색 요약). 풀 ID와 앱 클라이언트 ID는 비밀이 아니라서 웹 소스에 들어가도 됩니다.
- 한 풀에 클라이언트 두 개 → **한 계정으로 웹과 데스크톱에 모두 로그인**합니다. 클라이언트 ID는 운영 전에 웹사이트 세션과 결제·계정 세션이 합의합니다 (마스터 설계 `sessions/03`, `05`).
- 동의 기록은 회원 브라우저가 써 넣는 값입니다. 더 강한 증거가 필요하면 나중에 "가입 전(Pre sign-up) Lambda"로 서버 시각을 찍습니다 (지금은 안 함).

### 3.4 그룹

| 그룹 | 우선순위 | 용도 |
|---|---|---|
| `qg-admins` | 0 | 소유자 본인 회원 계정. 나중에 웹 안 관리자 기능의 표시 |
| `qg-beta` (선택) | 10 | 미리 보기 기능을 열어 줄 회원 |

그룹은 로그인 토큰의 `cognito:groups` 값으로만 전달됩니다. 지금은 서버가 없어서 **그룹에 넣어도 실제 권한은 생기지 않습니다.** AWS 콘솔 관리 권한(IAM)과 다른 것입니다 (5.9절). 그룹은 중첩이 안 되고, 그룹 안에서 회원 검색도 안 됩니다 (**확인**).

### 3.5 기록·감시·비용 알림

| 항목 | 값 (제안) | 이유 |
|---|---|---|
| CloudTrail "추적(trail)" | 이름 `qg-audit`, 관리 이벤트(읽기+쓰기), S3 버킷 `qg-audit-<임의값>`, 400일 뒤 자동 삭제 | 이벤트 기록(Event history)은 90일만 보관 (**확인**). 접속기록 1년 보관 의무 (2.6절) |
| CloudTrail 암호화 | SSE-S3 (S3 기본 암호화). 콘솔이 KMS 새 키를 기본으로 고르면 키당 월 약 $1 (미검증) | 비용 최소 |
| CloudWatch 경보 1 | `SignUpSuccesses` 합계 1시간 50건 초과 → 메일 | 대량 가입 감지. 지표 이름 **확인** (`AWS/Cognito`) |
| CloudWatch 경보 2 | `SignUpThrottles` 1건 이상 → 메일 | 가입 요청 폭주 (**확인**) |
| SES 경보 | 반송률 2% 초과, 신고율 0.05% 초과 → 메일 | 반송률 5% 넘으면 AWS 검토, 10% 넘으면 발송 중지 (**확인**). 신고율 한도는 자료마다 다름 (0.1% 등, 미검증) → 보수적으로 |
| 예산 1 | "Zero spend budget" (무료 범위 넘으면 메일) | (**확인**, 템플릿 이름) |
| 예산 2 | "Monthly cost budget" 월 $20, 85%·100%·예측 100%에 메일 | (**확인**, 템플릿 이름. 알림 비율은 제3자 자료) |

### 3.6 만드는 순서 (소유자, 약 1~2시간)

콘솔 문구는 지금(2026) 콘솔을 기준으로 정리했습니다. 확인 못 한 문구는 *(미검증)* 으로 표시했습니다. 화면 이름이 조금 달라도 같은 메뉴를 찾으시면 됩니다.

**A. 사용자 풀**
1. AWS 콘솔 로그인 → 오른쪽 위 리전을 **Asia Pacific (Sydney) ap-southeast-2**로 바꿈.
2. 검색창에 `Cognito` → **User pools** → **Create user pool** *(버튼 문구 미검증)*.
3. "Define your application" 화면 *(미검증)*: 종류 **Single-page application (SPA)**, 이름 `quantgen-web`.
4. 로그인 아이디 *(Options for sign-in identifiers, 미검증)*: **Email**만 체크.
5. **Self-registration** 켬 *(미검증)*. 가입 필수 속성 *(Required attributes)*: **email**만.
6. Return URL은 비워 둠 (관리형 로그인 안 씀) *(미검증: 필수 입력인지)*.
7. 만들기. 만든 뒤 풀 이름을 `quantgen-prod`로 *(이름 바꾸기 가능 여부 미검증. 안 되면 만들 때 지정 화면을 찾아 입력)*.
8. 풀 화면 → **Sign-up** 메뉴 → 필수 속성이 email뿐인지 확인 (**확인**: Sign-up 메뉴의 Required attributes 구역).
9. **Sign-up** 메뉴 → **Custom attributes** → **Add custom attributes** *(미검증)* → 3.2절 6개 추가.

**B. 메일 (SES)**
10. 풀 화면 → **Authentication methods** 메뉴 → **Email** → **Edit** *(Authentication methods 메뉴는 확인, Email 구역 위치·Edit는 미검증. 예전 콘솔은 "Messaging" 탭)*.
11. **Send email with Amazon SES** 선택 *(미검증)* → SES 리전 시드니 → FROM `no-reply@quantgeneration.com` → FROM 이름 `QUANTGEN` → Reply-to `support@…` → **Save changes**.
12. **Message templates** 메뉴 (**확인**) → **Verification message** → 제목 "[QUANTGEN] 이메일 인증 코드 / Email verification code", 본문에 한국어·영어 함께 + `{####}`. 광고 문구 넣지 않음.

**C. 로그인 보안**
13. **Authentication methods** → **Password policy** → **Edit** *(미검증)* → Custom, 최소 10자, 숫자·소문자·대문자, 임시 7일, 재사용 금지 5.
14. **Sign-in** 메뉴 → **Multi-factor authentication** → Edit → MFA enforcement **Optional MFA** → 방법 **Authenticator apps** + **Email message** → 저장 (**확인**: Sign-in 메뉴, Multi-factor authentication, MFA enforcement).
15. 계정 복구는 이메일만 *(Sign-in 메뉴 "User account recovery", 미검증)*.

**D. 앱 클라이언트**
16. **App clients** 메뉴 (**확인**) → `quantgen-web` → **Edit** *(미검증)* → 3.3절 표대로 인증 흐름·토큰 시간·속성 읽기/쓰기 권한·토큰 폐기·존재 여부 숨김.
17. **Overview** *(미검증)* 에서 **User pool ID**와 앱 클라이언트 **Client ID**를 적어 웹사이트 세션에 전달.

**E. 그룹과 소유자 계정**
18. **Groups** 메뉴 → **Create group** (**확인**) → `qg-admins`, Precedence 0 → **Create group**.
19. 웹 가입 화면이 열리기 전 시험은 개발 풀에서. 운영 풀의 소유자 계정은 공개 직전 웹에서 직접 가입 → 5.9절로 `qg-admins`에 추가.

**F. 삭제 보호와 기록**
20. 삭제 보호 켜짐 확인 *(새 콘솔의 위치 미검증. 예전 콘솔은 "User pool settings" 탭의 Deletion protection)*.
21. 콘솔 검색 `CloudTrail` → **Trails** → **Create trail** *(미검증)* → 이름 `qg-audit`, 새 S3 버킷, 로그 파일 KMS 암호화는 끔(선택), 관리 이벤트 Read+Write → 만들기.
22. 콘솔 검색 `S3` → 위 버킷 → **Management** → **Lifecycle rules** → **Create lifecycle rule** *(미검증)* → 현재 버전 400일 뒤 만료.

**G. 경보·예산**
23. `CloudWatch` → **Alarms** → **Create alarm** *(미검증)* → 지표 `AWS/Cognito` → User pool `quantgen-prod` → `SignUpSuccesses` (Sum, 1시간, > 50) → 알림 메일 → 같은 방식으로 `SignUpThrottles` (> 0).
24. `Billing and Cost Management` → **Budgets** → **Create budget** → **Use a template (simplified)** → **Zero spend budget** → 메일 주소 → 만들기. 다시 **Monthly cost budget** $20 (**확인**: Budgets, Create budget, 두 템플릿 이름).
25. 기록: 언제 무엇을 만들었는지 한 줄씩 메모 (권한·설정 변경 기록, 6장).

### 3.7 비용 (추정)

| 항목 | 예상 | 상태 |
|---|---|---|
| Cognito Essentials | 월 활동 회원 1만 명까지 $0, 넘으면 1명당 $0.015 (us-east-1 기준) | 검색 요약 (AWS 블로그·제3자). 가격 페이지 직접 확인 필요. 무료 범위는 계정 또는 조직 단위 — 우리 계정이 AWS 관리 조직 아래라 어떻게 세는지 **미검증** |
| Cognito Plus (쓰지 않음) | 1명당 $0.02, 무료 없음 | 검색 요약 |
| SES 메일 | 1천 통당 약 $0.10 | **미검증** |
| CloudTrail 추적 1개 + S3 | 관리 이벤트 첫 사본 무료로 알고 있음, S3 저장 몇 센트 | **미검증** |
| CloudWatch 경보 2개 | 무료 범위 안 또는 월 $1 미만 | **미검증** |
| AWS WAF (대량 가입 방어, 필요할 때만) | 월 $5 이상 + 규칙·요청당 | **미검증** |

---

## 4. 웹사이트 세션에 보낼 요청 (복사용)

> 아래는 웹사이트 세션(`xkg4real/website`)에 그대로 붙여 넣을 요청입니다. 마스터 설계의 WEB-3(출시 알림)·WEB-4(로그인 UI)는 D11 변경으로 이 요청이 대신합니다. 정책 문서의 **뜻**이 바뀌는 수정은 먼저 quantgen `docs/compliance`를 메인 세션이 고친 뒤 사이트에서 다시 생성합니다 (해시 검사 우회 금지). AWS 설정은 소유자가 3장대로 합니다.

---- 복사 시작 ----

D11 변경: 소유자가 "정식 계정 생성까지 진행"을 지시했습니다. 출시 알림 폼(WEB-3) 대신 정식 회원 계정을 엽니다. 운영 사용자 풀은 시드니 `quantgen-prod` (소유자가 만들고 풀 ID·클라이언트 ID를 전달). 공개 전까지 플래그 `AUTH_UI_ENABLED=false`.

**ACC-1 가입 화면.** 이메일, 비밀번호, 비밀번호 확인. 체크: [필수] 이용약관, [필수] 만 14세 이상, [선택·기본 해제] 소식 이메일(광고). 체크 없는 개인정보 안내 문장(시드니 보관 포함) + 처리방침 링크. 한/영 문구는 D11 문서 2.3절. `SignUp` 호출 때 사용자 정의 속성 `custom:terms_ver`, `custom:privacy_ver`, `custom:age14=Y`, `custom:consent_at`(ISO 시각), `custom:mkt_opt`(Y/N), `custom:mkt_at` 기록. 비밀번호 규칙(10자, 숫자·소문자·대문자)을 입력 중에 보여 줌.
완료 조건: 필수 체크 없이 가입 불가, 선택 체크 기본 해제, 한/영·밝음/어두움·320px.

**ACC-2 이메일 인증 화면.** 6자리 코드 입력, **"코드 다시 받기"** (`ResendConfirmationCode`) 버튼. 관리자 콘솔에는 자가 가입 회원에게 코드를 다시 보내는 버튼이 없다고 봅니다 (미검증) → 화면에 꼭 필요.
완료 조건: 잘못된 코드·만료 코드 안내, 다시 받기 횟수 제한 안내.

**ACC-3 로그인.** SRP 로그인(`USER_SRP_AUTH`), MFA 코드 단계(인증 앱·이메일), "로그인 유지" 없음(새로고침 토큰 7일). 오류 문구는 계정 존재 여부를 드러내지 않음 ("이메일 또는 비밀번호가 맞지 않습니다").
**ACC-4 비밀번호 찾기·새 비밀번호.** `ForgotPassword` → `ConfirmForgotPassword`. 관리자가 재설정을 건 회원(RESET_REQUIRED)도 이 화면으로 옴.
**ACC-5 계정 페이지.** 내 이메일 보기·변경(`UpdateUserAttributes` → 새 주소 코드 확인), 비밀번호 변경, 2단계 인증 켜기·끄기(OTP 앱 QR 등록), 소식 이메일 켜기·끄기(`custom:mkt_opt`·`custom:mkt_at` 갱신), 모든 기기에서 로그아웃(`GlobalSignOut`), **내 정보 내려받기**(`GetUser` 결과를 JSON 파일로), **회원 탈퇴**(`DeleteUser`, 확인 문구 입력 후 즉시 삭제, 결과 화면). 탈퇴는 가입보다 어렵지 않게.
**ACC-6 머리글·문구.** Log in / Sign up 버튼을 위 화면에 연결(플래그 뒤). 플래그 꺼진 동안은 기존 안내 문장 유지. "(주)넥스트제너레이션" 표기는 메인 세션 정책 PR 병합 뒤 사이트 전체에서 개인 운영자 표기로 바뀜(직접 문구를 만들지 말고 원문 재생성).
**ACC-7 보안.** Cognito 라이브러리 버전 고정·빌드에 묶기(런타임 CDN 금지), CSP `connect-src`에 `https://cognito-idp.ap-southeast-2.amazonaws.com`만 추가, 토큰은 메모리 또는 sessionStorage(로그 금지), 인증 화면에 분석·추적 스크립트 없음, 비밀번호 입력란 자동완성 `new-password`/`current-password`.
**ACC-8 하단.** "개인정보 처리방침" 링크를 다른 링크보다 눈에 띄게(굵게). 개인정보 문의 메일 표시(소유자가 받는 메일함 확인 뒤).
**ACC-9 시험.** 개발 풀로 끝에서 끝까지(가입 → 코드 → 로그인 → MFA → 이메일 변경 → 비밀번호 찾기 → 내려받기 → 탈퇴) 자동 시험 + 소유자 이메일로 운영 풀 수동 시험 1회. 결과를 `WEBSITE_AWS_SESSION_CURRENT.md`에 기록.
**ACC-10 소유자에게 줄 것.** 앱 클라이언트 설정 확인표(3.3절과 대조), 플래그 켜기 전 체크리스트. 웹 안 관리자 화면은 만들지 않음(관리는 AWS 콘솔).

---- 복사 끝 ----

---

## 5. 관리자 안내서 (기능별)

### 5.0 공통: 들어가는 길과 표시

**들어가는 길 (모든 기능 공통)**
1. AWS 콘솔에 로그인합니다 (2단계 인증 켠 계정으로).
2. 오른쪽 위 리전이 **Asia Pacific (Sydney)** 인지 확인합니다. 다른 리전이면 풀이 안 보입니다.
3. 위쪽 검색창에 `Cognito` → **Amazon Cognito** → 왼쪽 **User pools** → **`quantgen-prod`** 를 누릅니다.

이 안에서 왼쪽 메뉴 이름(새 콘솔): **Overview, Applications(App clients), User management(Users, Groups), Authentication(Authentication methods, Sign-in, Sign-up), Security(Threat protection), Branding(Message templates)** 등입니다. 확인한 것: Users, Groups, App clients, Authentication methods, Sign-in, Sign-up, Message templates. 나머지 이름과 묶음 구성은 미검증입니다.

**콘솔 문구 확인 상태 (요약)**

| 문구 | 상태 |
|---|---|
| User pools, Users, Groups, Create group | 확인 (AWS 문서 검색 요약) |
| 회원 화면의 Actions → Reset password / Disable user access / Enable user access / Delete user | 확인 |
| Actions → Confirm account | 부분 확인 (AWS re:Post 지식 센터 "Confirm Account") |
| Add user to group | 부분 확인 (제3자 문서) |
| Sign-in → Multi-factor authentication → MFA enforcement | 확인 |
| Sign-up → Required attributes | 확인 |
| Authentication methods (SMS 설정 위치) | 확인. 이메일·비밀번호 정책 위치는 미검증 |
| Message templates, App clients | 확인 |
| Create user, 속성 Edit, "Mark email address as verified", 자가 가입 켜기/끄기 문구, 삭제 보호 위치 | 미검증 |
| CloudTrail Event history (90일) | 확인 |
| Billing → Budgets → Create budget → Zero spend / Monthly cost budget | 확인 |
| SES Account dashboard → Suppression list, Reputation dashboard | 확인 |

**회원 상태 이름 (목록의 Status 열)**

| 상태 | 뜻 |
|---|---|
| Unconfirmed (UNCONFIRMED) | 가입했지만 이메일 코드를 아직 넣지 않음 |
| Confirmed (CONFIRMED) | 정상 |
| Reset required (RESET_REQUIRED) | 관리자가 비밀번호 재설정을 걸어 둠 |
| Force change password (FORCE_CHANGE_PASSWORD) | 관리자가 만든 계정, 첫 로그인 전 |
| Enabled 열 = Disabled | 정지된 계정 (상태와 별개) |

---

### 5.1 회원 목록 보기·검색

**언제**: 특정 회원을 찾을 때, 주간 점검 때.

1. 공통 경로 → 왼쪽 **Users**.
2. 목록 위 검색 칸에서 **찾을 속성**을 고르고(예: 이메일) 값을 넣습니다. 검색은 **앞부분 일치**입니다 (예: `kim`으로 시작하는 이메일).
3. 이메일로 로그인하는 풀이라 "User name" 열은 긴 영숫자(UUID)로 보입니다. 이메일 열을 보세요.

| 검색 가능한 속성 | 비고 |
|---|---|
| username, email, phone_number, name, given_name, family_name, preferred_username, sub | **확인** |
| Status (`cognito:user_status`), Enabled (`status`) | 콘솔에서는 Status, Enabled로 보임 (**확인**) |
| 사용자 정의 속성 (`custom:…`) | **검색 안 됨** (**확인**) → 광고 수신자 목록은 5.12절 내보내기로 |

- 한 번에 속성 하나로만 거를 수 있습니다 (**확인**).
- 그룹 안에서 검색은 안 됩니다. 그룹 화면의 회원 목록을 보세요 (**확인**).
- **주의**: 화면을 캡처해 채팅·Notion·GitHub에 올리지 마세요. 이메일이 개인정보입니다.

### 5.2 회원 상세 보기

1. **Users** → 회원의 User name(파란 글자)을 누릅니다 (**확인**: 목록에서 회원을 골라 상세 화면).
2. 보이는 것: 상태, 사용 여부(Enabled), 가입·수정 시각, MFA 설정, **User attributes**(email, email_verified, sub, 사용자 정의 속성), **Group memberships**.
3. Plus 요금제라면 로그인 기록(**User event history**)도 보입니다. Essentials에는 없습니다 (미검증 문구, Plus 기능임은 **확인**).

- 비밀번호는 어디에도 보이지 않습니다. 관리자가 볼 수도, 알 수도 없습니다.
- **주의**: 상세 화면을 여는 것도 관리자 접속기록(CloudTrail)에 남습니다. 필요할 때만 엽니다.

### 5.3 가입 승인·거부 (쓰는 경우만)

**권장: 쓰지 않습니다.** 이메일 인증만으로 가입이 끝나게 둡니다. 승인제가 필요하면 아래 두 방법 중 하나입니다.

| 방법 | 설정 | 승인 | 거부 | 단점 |
|---|---|---|---|---|
| 수동 확인 | Sign-up 설정에서 Cognito의 자동 확인(Cognito-assisted verification and confirmation, 문구 미검증)을 끔 | **Users** → 회원 → **Actions** → **Confirm account** | **Actions** → **Disable user access** → **Delete user** | 이메일이 자동 인증되지 않아 비밀번호 찾기가 안 될 수 있음 (미검증). 관리자 일이 많아짐 |
| 허용 목록 | 가입 전(Pre sign-up) Lambda가 허용 목록만 통과 | 목록에 추가 | 목록에 없음 | Lambda와 코드 필요 |

- **Confirm account를 누르면** 회원이 바로 로그인할 수 있습니다. 이메일 주인이 맞는지 다른 방법으로 확인하기 전에는 누르지 마세요.

### 5.4 계정 정지·해제

**정지 (Disable)**
1. **Users** → 회원 → 오른쪽 위 **Actions** → **Disable user access**.
2. 확인 창에서 **Disable** (**확인**).

회원에게 생기는 일: 모든 로그인 세션이 끊기고, 로그인할 수 없으며, 액세스·새로고침 토큰이 폐기됩니다 (**확인**). 회원에게 자동 알림은 가지 않습니다 (미검증) → 필요하면 직접 메일.

**해제 (Enable)**
1. **Users** → 회원 → **Actions** → **Enable user access** → 확인 창 **Enable** (**확인**).

회원에게 생기는 일: 바로 다시 로그인할 수 있습니다 (**확인**).

- **언제 정지**: 부정 이용 의심, 만 14세 미만으로 밝혀짐, 처리정지 요청, 탈퇴 요청을 확인하는 동안.
- **주의**: 정지는 삭제가 아닙니다. 정보는 그대로 남습니다. 정지 이유와 날짜를 처리 기록(6장)에 남기세요.

### 5.5 계정 삭제

1. **Users** → 회원 → **Actions** → **Disable user access** → **Disable** (먼저 정지).
2. 다시 **Actions** → **Delete user** → 확인 창에서 **Delete**.

콘솔은 정지하지 않은 회원의 삭제 버튼을 막아 둡니다 (AWS re:Post 답변 기준, 공식 영문 페이지에서 순서 문구는 미검증).

회원에게 생기는 일: 계정과 모든 속성이 **즉시, 되돌릴 수 없이** 지워집니다. 같은 이메일로 새로 가입할 수는 있습니다 (새 계정 고유번호).

- **언제**: 회원이 탈퇴를 요청했는데 스스로 못 할 때, 인증 안 한 지 7일 지난 계정, 만 14세 미만 확인.
- **주의**: ① 삭제 전 본인 요청인지 확인 (5.11절). ② CloudTrail 기록에는 계정 고유번호(sub)가 남습니다. 1년 보관 기록이라 지우지 않습니다. ③ 내보내기 파일에 그 회원이 있으면 그 파일도 지웁니다.
- 여러 계정 정리(인증 안 한 계정): 5.12절 명령으로 목록을 먼저 만들고, 하나씩 확인하며 지웁니다. 한꺼번에 지우는 스크립트는 쓰지 않습니다.

### 5.6 비밀번호 재설정

1. **Users** → 회원 → **Actions** → **Reset password** → 확인 창에서 재설정 (**확인**).

회원에게 생기는 일: 지금 비밀번호가 **바로 막히고**(상태 RESET_REQUIRED), 이메일로 확인 코드가 갑니다. 코드는 **1시간** 유효합니다 (**확인**). 회원은 웹의 "비밀번호 찾기"(ACC-4)에서 새 비밀번호를 정합니다.

- **언제**: 회원이 해킹이 의심된다고 알려 왔을 때, 비밀번호 유출이 확인됐을 때.
- 그냥 비밀번호를 잊은 회원은 관리자가 할 일이 없습니다. 웹의 "비밀번호 찾기"를 안내하세요.
- **주의**: 관리자가 직접 비밀번호를 정해 주는 명령(`admin-set-user-password`)도 있지만 쓰지 마세요. 관리자가 회원 비밀번호를 알게 됩니다.

### 5.7 이메일 인증 재발송

| 회원 상태 | 방법 |
|---|---|
| 스스로 가입, 코드 미입력 (Unconfirmed) | 웹 인증 화면의 **"코드 다시 받기"** 를 안내 (ACC-2). 콘솔에 재발송 버튼은 찾지 못했습니다 (미검증) |
| 같은 경우, 관리자가 대신 | CloudShell(콘솔 위쪽 `>_` 아이콘)에서: `aws cognito-idp resend-confirmation-code --client-id <웹 앱 클라이언트 ID> --username <회원 이메일> --region ap-southeast-2` → 회원 메일로 새 코드 발송 |
| 관리자가 만든 계정 (Force change password) | `aws cognito-idp admin-create-user --user-pool-id <풀 ID> --username <회원 이메일> --message-action RESEND --region ap-southeast-2` → 새 임시 비밀번호로 초대 메일 재발송 (**확인**: RESEND 동작) |
| 이미 Confirmed | 재발송 불가 (**확인**) |

- **주의**: 코드가 안 온다는 문의가 많으면 SES 문제일 수 있습니다 → 5.14절에서 반송·차단 목록 확인.
- 확인 버튼(Confirm account)으로 대신 확인해 주는 것은 이메일 주인 확인이 끝난 경우만.

### 5.8 이메일 변경

**기본: 회원이 직접** (웹 계정 페이지 ACC-5). 새 주소로 코드가 가고, 코드를 넣기 전까지 기존 주소로 계속 로그인됩니다 (3.2절 설정, 문구 미검증).

**관리자가 대신 바꾸는 경우** (회원이 예전 메일함을 잃었을 때만)
1. 본인 확인을 먼저 합니다 (5.11절. 예: 가입 시각, 마지막 이용 시기, 계정 페이지에서 내려받은 정보 등 회원만 아는 것).
2. **Users** → 회원 → **User attributes** 구역의 **Edit** *(미검증)*.
3. `email` 값을 새 주소로 바꿉니다. "이메일을 인증된 것으로 표시"(Mark email address as verified, 문구 미검증)는 **켜지 않습니다**.
4. 저장 → 회원에게 웹에서 새 주소 인증을 하도록 안내합니다.

- **주의**: 이메일이 로그인 아이디입니다. 잘못 바꾸면 남이 그 계정을 가져갑니다. 인증된 것으로 표시하는 체크는 본인 확인이 확실할 때만.

### 5.9 관리자 권한 부여

"관리자"는 두 가지입니다. 헷갈리지 않게 나눕니다.

| 종류 | 무엇 | 어디서 |
|---|---|---|
| ① 웹 안의 관리자 표시 | 회원 계정에 `qg-admins` 그룹 | Cognito Groups |
| ② AWS 콘솔 관리 권한 | 회원 정보를 보고 바꿀 수 있는 사람 | AWS IAM (회원 계정과 무관) |

**① 그룹에 넣기**
1. 공통 경로 → **Groups** → `qg-admins` → **Add user to group** *(제3자 문서로만 확인)* → 회원 선택 → 추가.
2. 회원이 **다시 로그인해야** 새 토큰에 그룹이 들어갑니다.
3. 빼기: 같은 화면에서 회원 선택 → **Remove** *(미검증)*.

지금은 서버가 없어 그룹이 실제 권한을 주지 않습니다 (3.4절).

**② AWS 콘솔 권한 (지금은 하지 않기를 권함)**
- 1인 운영이라 다른 사람에게 콘솔 권한을 주지 않는 것이 가장 안전합니다.
- 꼭 필요하면: 그 사람만의 로그인(공유 금지), 2단계 인증 필수, 권한은 Cognito 사용자 조회·정지 정도로 최소화, **부여·변경·회수 날짜와 범위를 기록** (안전성 확보조치 기준의 접근권한 기록. 보관 기간 3년으로 알고 있으나 미검증).
- 이 계정은 AWS가 관리하는 조직 정책 아래라, IAM 사용자·역할 생성이 막혀 있을 수 있습니다 (미검증).

### 5.10 MFA 강제

| 대상 | 방법 | 주의 |
|---|---|---|
| 관리자 본인 (AWS 콘솔 로그인) | **가장 중요.** AWS 콘솔 로그인 계정에 2단계 인증이 켜져 있는지 확인 (계정 메뉴 → Security credentials, 미검증) | 콘솔이 뚫리면 모든 회원 정보가 위험 |
| 회원 전체 | 공통 경로 → **Sign-in** → **Multi-factor authentication** → **Edit** → MFA enforcement **Require MFA** → 방법 선택 → 저장 (**확인**) | 켜는 순간 **모든 회원**이 다음 로그인 때 MFA를 설정해야 함. 웹 화면(ACC-3·5)이 MFA 설정 단계를 지원하기 전에 켜면 회원이 로그인을 못 함. 지금은 **Optional** 유지 권장 |
| 특정 회원만 | 콘솔에서 한 사람만 강제하는 방법은 찾지 못함 (미검증). 회원이 계정 페이지에서 켜도록 안내 | Plus의 적응형 인증은 위험한 로그인에만 MFA 요구 (나중) |
| 이메일 MFA | Essentials 이상 + 자체 SES 필요 (**확인**). 우리 설정은 충족 | 메일함이 뚫리면 같이 뚫림 → 인증 앱 권장 |

### 5.11 개인정보 열람·정정·삭제 요청 처리

**기본 원칙**: 회원이 웹 계정 페이지에서 **직접** 할 수 있게 만들어 둡니다 (열람 = 내 정보 내려받기, 정정 = 이메일 변경, 삭제 = 탈퇴, 동의 철회 = 소식 메일 끄기). 관리자는 직접 못 하는 경우만 처리합니다.

| 단계 | 할 일 |
|---|---|
| 1 접수 | `privacy@…` 메일로 받음. 접수일 기록. **10일 안** 처리 또는 사유 통지 (2.8절, 원문 미확인) |
| 2 본인 확인 | **가입한 그 이메일 주소에서 온 요청**인지 확인. 다른 주소에서 왔으면, 가입 주소로 확인 메일을 보내 회신받음. 신분증·주민번호는 요구하지 않음 (main `20-deletion.md` 원칙) |
| 3 찾기 | 5.1절로 이메일 검색 |
| 4a 열람 | 5.2절 화면의 속성을 정리해 **가입 이메일로만** 회신. 또는 CloudShell `aws cognito-idp admin-get-user --user-pool-id <풀 ID> --username <회원 이메일> --region ap-southeast-2` 결과에서 필요한 값만 옮김 |
| 4b 정정 | 5.8절 |
| 4c 삭제 | 5.5절 |
| 4d 처리정지 | 5.4절 정지 |
| 4e 광고 동의 철회 | 회원 상세 → User attributes → Edit *(미검증)* → `custom:mkt_opt` = `N`, `custom:mkt_at` = 오늘 시각 |
| 5 회신 | 무엇을 했는지, 남은 것(예: 1년 보관 보안 기록에 계정 고유번호가 남음)과 이의 제기 방법 |
| 6 기록 | 접수 번호, 요청 종류, 접수·완료 날짜, 결과, 처리자. **이메일·요청 원문은 기록에 넣지 않음** |

- **주의**: 회신 메일에 다른 회원 정보가 섞이지 않게. 요청 원문을 GitHub 이슈·Notion에 올리지 않습니다.

### 5.12 회원 정보 내보내기

콘솔에 회원 목록을 파일로 내보내는 버튼은 찾지 못했습니다 (미검증). CloudShell 명령으로 합니다.

1. 콘솔 위쪽 `>_` (CloudShell) → 리전 시드니 확인.
2. 필요한 칸만 화면에 보기 (파일 안 만듦):
   ```
   aws cognito-idp list-users --user-pool-id <풀 ID> --region ap-southeast-2 \
     --query "Users[].{email: Attributes[?Name=='email']|[0].Value, status: UserStatus, enabled: Enabled, created: UserCreateDate}" \
     --output table
   ```
3. 인증 안 한 계정만: 위 명령에 `--filter "cognito:user_status = \"UNCONFIRMED\""` 를 붙입니다 (필터 문법 **확인**: 속성 하나, `=` 또는 `^=`).
4. 파일이 꼭 필요하면 `--output json > users.json` → **Actions → Download file** *(CloudShell 메뉴 문구 미검증)* → 일이 끝나면 내 PC와 CloudShell 양쪽에서 지웁니다 (`rm users.json`).

- 광고 수신자 목록: 사용자 정의 속성은 서버 검색이 안 되므로, 전체를 받아 `custom:mkt_opt`가 `Y`인 것만 고릅니다 (`--query`로 화면에서 거르기).
- **주의**: ① 내보낸 파일도 개인정보입니다. 저장소·Notion·Drive·채팅에 올리지 않습니다. ② CloudShell 저장 공간은 지우기 전까지 남습니다 (보관 기간 미검증). ③ 필요한 칸만 뽑습니다. ④ 언제, 왜 내보냈는지 기록합니다.

### 5.13 로그인 기록·이상 접속 확인 (CloudTrail·CloudWatch)

**무엇을 볼 수 있나 (Essentials 기준)**

| 보고 싶은 것 | 어디서 | 한계 |
|---|---|---|
| 하루·시간별 가입·로그인 수 | **CloudWatch** → 지표 → `AWS/Cognito` → User pool `quantgen-prod` → `SignUpSuccesses`, `SignInSuccesses`, `SignUpThrottles` (**확인**: 지표 이름) | 회원별이 아님. 실패 수는 Sample Count − Sum 계산 (**확인**) |
| 관리자(나)가 한 일 | **CloudTrail** → **Event history** → Event source `cognito-idp.amazonaws.com` (최근 90일, **확인**) / 1년 치는 S3 버킷 `qg-audit-…` | — |
| 특정 회원의 요청 | CloudTrail에는 회원 이메일이 아니라 **계정 고유번호(sub)** 가 남음 (**확인**) → 5.1절에서 `sub`로 검색해 누군지 찾음 | 로그인 같은 회원 쪽 요청이 모두 남는지, 접속 IP가 남는지는 **미검증** → 공개 전 시험 로그인 1번 하고 기록이 보이는지 확인 |
| 회원별 로그인 기록·위험 점수 | Plus 요금제 + 위협 보호 → 회원 상세의 로그인 기록, CloudWatch Logs·S3로 내보내기 (**확인**) | 1명당 월 $0.02, 무료 없음. 지금은 쓰지 않음 |

**점검 순서 (월 1회, 6장)**
1. **CloudTrail** → **Event history** → 필터 **Event source** = `cognito-idp.amazonaws.com` *(필터 문구 미검증)*.
2. 볼 것: `AdminDeleteUser`, `AdminDisableUser`, `AdminUpdateUserAttributes`, `AdminSetUserPassword`, `ListUsers`, `UpdateUserPool`, `UpdateUserPoolClient` 같은 **관리자 작업**이 내가 한 것인지. 처음 보는 IP·시간대가 있는지.
3. **CloudWatch** → `SignUpSuccesses`를 지난 30일 그래프로 → 갑자기 튄 날이 있는지.
4. 결과를 한 줄로 기록 ("2026-12-01 점검, 이상 없음").

- **주의**: CloudTrail 기록 일부 값은 AWS가 가리지만, 일반 칸에 넣은 개인정보까지 자동으로 가리지는 않습니다 (**확인**). 그래서 사용자 정의 속성에 이메일·이름 같은 값을 넣지 않습니다.

### 5.14 이메일 발송 설정 확인 (SES)

1. 콘솔 → `Amazon Simple Email Service` → 리전 **시드니**.
2. **Identities** *(미검증 문구)* → `quantgeneration.com` → 인증 상태 Verified, DKIM 성공인지.
3. **Account dashboard** → 운영 모드(Production access), 하루 발송 한도, 최근 발송량.
4. **Account dashboard** → **Suppression list** (**확인**) → 반송·신고로 막힌 주소. 회원이 "코드가 안 와요"라고 하면 여기에 그 주소가 있는지 봅니다. 있으면 주소가 맞는지 확인 후 목록에서 지웁니다 *(삭제 버튼 문구 미검증)*.
5. **Reputation dashboard** (**확인**) → 반송률 **5% 미만**(넘으면 AWS 검토, 10% 넘으면 발송 중지 — **확인**), 신고율은 낮게(한도 수치는 자료마다 달라 미검증).
6. Cognito 쪽: 공통 경로 → **Authentication methods** → Email 구역 *(미검증)* → SES 사용, FROM 주소가 `no-reply@quantgeneration.com`인지.
7. 시험: 본인 이메일로 개발 풀 또는 운영 풀에서 가입 코드 받기.

- 대시보드는 경보를 보내지 않습니다. 경보는 CloudWatch에서 따로 겁니다 (**확인**, 3.5절).
- **주의**: 서울 리전 SES 화면은 조직 정책에 막혀 있을 수 있습니다. 항상 시드니에서 봅니다.

### 5.15 비용 확인

1. 콘솔 → `Billing and Cost Management`.
2. **Bills** *(미검증)* → 이번 달 서비스별 금액 (Cognito, SES, CloudTrail, S3, CloudWatch).
3. **Cost Explorer** *(미검증)* → 서비스별로 묶어 지난 3개월 추이.
4. **Budgets** (**확인**) → 3.5절 두 예산의 상태.
5. **Free Tier** 화면 *(미검증)* → 무료 범위 사용량.

| 볼 숫자 | 정상 범위 (추정) | 이상하면 |
|---|---|---|
| Cognito | $0 (월 활동 회원 1만 명 미만) | 요금제가 Plus로 바뀌었는지 확인 (요금제 변경은 언제든 가능, **확인**) |
| SES | 거의 $0 | 대량 가입·발송 의심 → 5.17절 |
| CloudTrail·S3 | 몇 센트~$1 | KMS 키 요금($1/월) 확인 (미검증) |

### 5.16 정기 점검 연결

5.1~5.15의 정기 확인은 6장 점검표로 묶었습니다.

### 5.17 사고 대응

**A. 키·비밀값 유출**

| 무엇이 샜나 | 위험 | 바로 할 일 |
|---|---|---|
| 풀 ID, 앱 클라이언트 ID | **없음** (원래 공개값) | 할 일 없음 |
| AWS 콘솔 로그인 (비밀번호·MFA) | 매우 큼 | ① 비밀번호 변경, MFA 재등록 ② CloudTrail Event history에서 최근 작업 확인 ③ 모르는 사용자·키·리소스 삭제 ④ 회원 정보 조회(`ListUsers`, `AdminGetUser`)가 있었으면 **B. 개인정보 유출**로 |
| AWS 액세스 키 (CLI용) | 큼 | 콘솔 → IAM → 해당 사용자 → **Security credentials** → 액세스 키 → **Deactivate** → 새 키 발급 → 옛 키 **Delete** *(문구 미검증)* → CloudTrail에서 그 키로 한 일 확인. 키를 저장소·채팅에 붙인 적이 있으면 그 기록도 정리 |
| 회원 한 명의 비밀번호·토큰 | 그 회원 | 5.4 정지 → 5.6 재설정 → 회원에게 안내 → 해제 |
| GitHub 토큰 등 다른 키 | 서비스별 | 해당 서비스에서 폐기·재발급 (D5·D7 문서 원칙) |

**B. 개인정보 유출 (의심 포함)**

| 시간 | 할 일 |
|---|---|
| 즉시 | 원인 차단 (키 폐기, 계정 정지, 자가 가입 끄기). 증거 보존 (CloudTrail 기록 지우지 않음) |
| 24시간 안 | 범위 파악: 몇 명, 어떤 항목, 언제부터. `ListUsers`/`AdminGetUser`가 누구에 의해 몇 번 호출됐는지 |
| **72시간 안** | 해당 회원에게 통지 (항목, 시점·경위, 회원이 할 일, 우리의 조치, 문의처). 1천 명 이상·해킹 등 외부 불법 접근이면 개인정보보호위원회 또는 KISA에 **신고** (2.7절) |
| 이후 | 재발 방지, 처리 기록, 처리방침 갱신 필요 여부 |

법률 자문 아님. 실제 사고면 KISA(118)에 먼저 문의하세요. 신고 접수 화면의 위치는 미검증입니다.

**C. 대량 가입 (봇)**

신호: `SignUpSuccesses` 경보, SES 발송량 급증, 반송률 상승, 이상한 이메일 주소가 Unconfirmed로 쌓임.

1. **자가 가입 잠시 끄기**: 공통 경로 → **Sign-up** → 자가 가입 *(Self-service sign-up → Edit → Enable self-registration 해제, 문구 미검증)* → 저장. 기존 회원 로그인은 그대로 됩니다.
2. 웹사이트 세션에 알림: 가입 화면에 "잠시 가입을 멈췄습니다" 문구 (플래그).
3. 가짜 계정 찾기: 5.12절 3번 명령(UNCONFIRMED) + 가입 시각으로 범위 확정.
4. 하나씩 확인하며 정지 → 삭제 (5.5절). 진짜 회원이 섞였을 수 있으니 확인 후.
5. SES 확인 (5.14절): 반송률 5%에 가까우면 발송을 줄이는 것이 먼저입니다.
6. 재발 방지 (선택): 웹 가입 화면에 CAPTCHA, 또는 Cognito에 **AWS WAF** 웹 ACL 연결(속도 제한 규칙). WAF는 월 $5 이상 (미검증), 연결 메뉴 위치 미검증.
7. 정리되면 자가 가입 다시 켬. 기록 남김.

**D. SES 발송이 멈춤**

가입 코드·비밀번호 재설정 메일이 안 갑니다 → 신규 가입이 사실상 멈춤. SES **Account dashboard**에서 상태 확인 → 원인(반송·신고) 제거 → AWS 안내에 따라 재개 요청. 그동안 웹에 안내 문구.

**E. 관리자 실수 (회원을 잘못 지움)**

삭제는 되돌릴 수 없습니다. 회원에게 사실을 알리고 다시 가입을 안내합니다. 그래서 삭제 전 정지 단계를 꼭 거칩니다.

---

## 6. 정기 점검표 (내부 관리 기준 초안)

| 주기 | 할 일 | 절 |
|---|---|---|
| 매주 | Users에서 Status = Unconfirmed, 가입 7일 지난 계정 삭제 | 5.1, 5.5 |
| 매주 | `privacy@`·`support@` 메일함 확인, 요청은 10일 안 처리 | 5.11 |
| 매월 | CloudTrail 관리자 작업 점검 (접속기록 점검), 결과 한 줄 기록 | 5.13 |
| 매월 | CloudWatch 가입·로그인 추이, SES 반송·신고율, 비용·예산 | 5.13~5.15 |
| 매월 | `qg-admins` 그룹 구성원이 맞는지 | 5.9 |
| 분기 | 내보내기 파일이 남아 있지 않은지 (내 PC, CloudShell) | 5.12 |
| 연 1회 | 비밀번호 정책·MFA·요금제·처리방침 재검토, 광고 수신자에게 수신 동의 사실 안내 (2년 주기 의무 대비) | 3.2, 2.8 |
| 변경할 때마다 | 풀·앱 클라이언트·그룹·권한 변경을 날짜·내용·이유로 기록 | 3.6 |
| 사고 때 | 5.17절 | 5.17 |

### 6.1 공개 전 체크 (소유자)

| # | 확인 | 통과 기준 |
|---|---|---|
| 1 | 처리방침·약관에 "(주)" 없음, 개인 운영자·책임자·메일 표기 | 공개 페이지 검색 |
| 2 | 국외 이전(시드니)·처리위탁(AWS) 표 채움 | 01번 문서 |
| 3 | `privacy@` 메일 실제 수신 | 외부 주소에서 보내 받기 |
| 4 | 본인 이메일로 가입 → 코드 → 로그인 → MFA → 이메일 변경 → 비밀번호 찾기 → 내려받기 → 탈퇴 | 전부 성공 |
| 5 | 시험 계정으로 관리자 기능: 정지 → 로그인 막힘 → 해제 → 재설정 → 삭제 | 5.4~5.6 대로 동작 |
| 6 | CloudTrail에 위 관리자 작업이 보임 | Event history |
| 7 | 경보·예산 메일 수신 확인 | 시험 경보 1회 |
| 8 | 법률 확인 1회 (118 또는 변호사) | 메모 |

---

## 7. 확인 못 한 것 (미검증 목록)

| 항목 | 왜 못 했나 | 어떻게 확인 |
|---|---|---|
| Cognito 콘솔 문구 일부 (Create user, 속성 Edit, Mark email address as verified, 자가 가입 토글, 삭제 보호 위치, Remove from group, 재발송 버튼 유무, 회원 로그인 기록 문구) | `docs.aws.amazon.com` 접속 불가, 검색 요약에 없음 | 콘솔에서 직접. 또는 세션 네트워크에 `docs.aws.amazon.com` 허용 |
| Cognito 기본 메일 하루 50통 | 검색 요약에 숫자 없음 | Cognito Quotas 문서 |
| Cognito 가격, 무료 범위를 조직 단위로 세는 방식 (AWS 관리 조직) | 가격 페이지 본문을 못 읽음 | `aws.amazon.com/cognito/pricing`, Billing의 Free Tier 화면 |
| SES·CloudTrail·CloudWatch·WAF·KMS 가격 | 확인 안 함 | 각 가격 페이지 |
| CloudTrail에 회원 쪽 요청(로그인 등)과 IP가 남는지 | 문서 요약이 엇갈림 | 시험 로그인 후 Event history |
| Cognito가 인증 안 한 계정을 자동 삭제하는지 | 확인 안 함 | 문서 또는 7일 관찰 |
| 사용자 정의 속성 삭제·이름 변경 불가, 최대 개수 | 요약에 없음 | 문서 |
| 이 계정에서 IAM 사용자 생성·서울 리전 사용 가능 여부 | 조직 SCP 본문 미확인 | 시도 또는 AWS 지원 |
| AWS 계약 법인명 (처리방침 수탁자·이전받는 자) | 확인 안 함 | 청구서의 판매자 표기 |
| 법령: 제15조·제22조·제22조의2·제24조의2·제27조 제1항 제3호·제28조의8 제2항·제38조·시행령 제41·43·44조 원문, 2026-09-11 개정의 유출 가능성 통지, 정보통신망법 야간 전송 규정의 이메일 적용, 전기통신사업법 제22조 소규모 신고 의제, 접근권한 기록 3년 | 국가법령정보센터 원문을 열지 못함 | law.go.kr 원문, 118 상담 |
| "[필수] 개인정보 수집·이용 동의"를 둘지 안내로 갈음할지 | 법률 판단 | 변호사·118 |
| 지금 공개 사이트의 로그인·가입 문구 | 사이트를 이 세션에서 못 엶 | 웹사이트 세션 |

---

## 8. 출처 (모두 2026-11-17 확인. AWS 문서는 검색 결과 요약으로 확인)

**저장소 (읽기 전용)**
- handoff `WEBSITE_AWS_SESSION_CURRENT.md` (리전, Cognito dev 풀, SES, API Gateway, Amplify, 로그인 미연결), `WEBSITE_AWS_HANDOFF.md`
- main `docs/compliance/01-privacy-policy.md`, `20-deletion.md`, `17-children.md`, `06-form-consent.md`, `18-marketing-email.md`, `16-business-information.md`, `release-profile.json`
- 마스터 초안 `MASTER_WORK_DESIGN_2026-11-17.md` 부록 A·E·F, `sessions/03_WEBSITE.md` (WEB-3·WEB-4), `sessions/05_PAYMENTS_ACCOUNT_KEYS_NEW.md`, `OWNER_REPORT_2026-11-17.md` D11

**AWS**
- 회원 관리 (Actions: Reset password, Disable/Enable user access, Delete user): https://docs.aws.amazon.com/cognito/latest/developerguide/how-to-manage-user-accounts.html (미러 https://docs.aws.eu/cognito/latest/developerguide/how-to-manage-user-accounts.html)
- Confirm account: https://repost.aws/knowledge-center/cognito-confirm-account
- 삭제 전 정지 필요 (커뮤니티 답변): https://repost.aws/questions/QUEt519E4kQeqwlJPUO8R1VQ/why-is-cognito-user-action-password-reset-confirm-account-and-delete-user-disabled-in-aws-console-ui
- 그룹: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-user-groups.html ; Add user to group (제3자): https://docs.cognite.com/cdf/access/aws/guides/create_groups_oidc_cognito
- 관리자가 만드는 계정·RESEND: https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_AdminCreateUser.html ; ResendConfirmationCode: https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/resend-confirmation-code.html
- 가입·확인: https://docs.aws.amazon.com/cognito/latest/developerguide/signing-up-users-in-your-app.html
- 속성 (필수 속성 변경 불가): https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-attributes.html ; https://repost.aws/knowledge-center/cognito-change-user-pool-attributes
- 메일 (SES): https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-email.html ; https://aws.amazon.com/premiumsupport/knowledge-center/cognito-user-pool-ses-integration/
- MFA: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-mfa.html ; 이메일 MFA (Essentials): https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pool-settings-advanced-security-email-mfa.html
- 비밀번호 정책 값: https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_PasswordPolicyType.html
- 요금제·가격: https://aws.amazon.com/cognito/pricing ; https://builder.aws.com/content/3KlTXfJhkIuYFkyPkM2P16amtXC/sign-in-for-10000-users-at-dollar0-with-amazon-cognito ; https://frontegg.com/guides/aws-cognito-pricing
- Plus·위협 보호·로그 내보내기: https://docs.aws.amazon.com/cognito/latest/developerguide/feature-plans-features-plus.html ; https://docs.aws.amazon.com/cognito/latest/developerguide/exporting-quotas-and-usage.html
- 검색 가능 속성 (ListUsers): https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_ListUsers.html
- 삭제 보호: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-deletion-protection.html
- 앱 클라이언트·토큰 폐기: https://docs.aws.amazon.com/cognito/latest/developerguide/token-revocation.html ; SPA 비밀값 없음: https://docs.cognite.com/cdf/access/aws/guides/register_custom_webapp_cognito
- 메시지 템플릿·Authentication methods 메뉴: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pool-settings-message-customizations.html
- CloudTrail (관리 이벤트, sub 기록, 90일): https://docs.aws.eu/cognito/latest/developerguide/logging-using-cloudtrail.html ; https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-info-in-cloudtrail.html
- CloudWatch 지표: https://docs.aws.amazon.com/cognito/latest/developerguide/metrics-for-cognito-user-pools.html
- 예산 템플릿: https://docs.aws.amazon.com/cost-management/latest/userguide/budget-templates.html ; https://docs.aws.amazon.com/cost-management/latest/userguide/create-cost-budget.html
- SES 차단 목록·평판: https://docs.aws.amazon.com/ses/latest/DeveloperGuide/sending-email-global-suppression-list.html ; https://aws.amazon.com/ru/premiumsupport/knowledge-center/ses-suppression-list-sending-quota/ ; https://repost.aws/knowledge-center/ses-high-bounce-rate ; https://repost.aws/knowledge-center/ses-reputation-dashboard-bounce-rate ; https://docs.aws.amazon.com/ses/latest/dg/reputation-dashboard-dg.md
- AWS 관리 조직 정책: https://docs.aws.amazon.com/accounts/latest/reference/scps-and-rcps-for-projects.html

**법령 (해설·보도 자료. 원문 미확인, 법률 자문 아님)**
- 상법 제20조·제28조: https://korea.legal/wiki/상법-제20조/ , https://korea.legal/wiki/상법-제28조/
- 유출 통지·신고 (제34조, 시행령 제40조): https://itwiki.kr/w/개인정보_보호법_시행령_제40조 , https://www.kisa.or.kr/1030402
- 안전성 확보조치 기준 제8조 (접속기록 1년·2년, 점검 주기 자율): https://itwiki.kr/w/개인정보의_안전성_확보조치_기준_제8조 , https://www.lawtimes.co.kr/news/articleViewAmp.html?idxno=213530
- 국외 이전 (제28조의8): https://itwiki.kr/w/개인정보_보호법_제28조의8 , https://www.nepla.ai/wiki/it-정보-방송통신/개인정보-위치정보-신용정보/개인정보의-국외이전-mo59y3rr81vj
- 영업양도 이전 (제27조, 시행령 제29조): https://itwiki.kr/w/개인정보_보호법_제27조 , https://itwiki.kr/w/개인정보_보호법_시행령_제29조
- 유효기간제 폐지 (2023-09-15): https://www.nepla.ai/wiki/it-정보-방송통신/개인정보-위치정보-신용정보/개인정보-유효기간제의-내용과-폐지-zr592wrov96k
- 광고성 정보 (정보통신망법 제50조, 2년 확인): https://www.itwiki.kr/w/정보통신망법_제50조
- 2026-09-11 시행 개정 (유출 가능성 통지, 책임자 신고 대상): https://www.lawtimes.co.kr/news/articleViewAmp.html?idxno=226414 , https://zdnet.co.kr/view?no=20260910211643
- 개인정보보호위원회: https://pipc.go.kr/np/default/page.do?mCode=D060040000
