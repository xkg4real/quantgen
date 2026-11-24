# 데스크톱 앱 로그인 설계 (PAY-1, 설계만)

- 판: v0.1 (2026-11-24, PAYMENTS_ACCOUNT_KEYS 세션, 메인 지시 P6)
- 상태: 설계와 시험 계획만. **코드는 웹 계정 화면이 공개된 뒤** 씁니다 (`core/account`는 아직 없음). 화면은 UI 세션 몫이라 10절에 요청 목록으로만 둡니다.
- 기준: main `de32ea1`의 `core/app_identity.py` (`COGNITO_REGION`, `COGNITO_USER_POOL_ID`, `COGNITO_DESKTOP_CLIENT_ID` 빈 값), `core/credentials` (KEY-2), [계정 설정 묶음](ACCOUNT_SETUP.md) 1.3 (데스크톱 클라이언트 자리), [관리자 안내서](ADMIN_GUIDE.md) 6.1·6.2.
- AWS 동작 중 문서로 확인한 것은 "확인", 나머지는 "미검증". 법률 관련 줄은 **법률 자문이 아닙니다**.

## 0. 한 장 요약

데스크톱 앱은 **시스템 브라우저**로 Cognito 로그인 화면을 열고, **Authorization Code + PKCE(S256)** 로 받은 코드를 **127.0.0.1 임의 포트**의 일회용 콜백으로 받아 토큰으로 바꿉니다. 같은 운영 풀 `quantgen-prod`의 새 공개 클라이언트 `quantgen-desktop`을 씁니다. 새로고침 토큰만 OS 키 보관함(`core.credentials`)에 두고, 액세스·ID 토큰은 메모리에만 둡니다.

```mermaid
sequenceDiagram
  participant App as QUANTGEN 앱
  participant Loop as 127.0.0.1:임의포트
  participant Br as 시스템 브라우저
  participant Cg as Cognito (관리형 로그인)
  App->>Loop: 일회용 콜백 서버 열기 (5분)
  App->>Br: /oauth2/authorize?client_id&code_challenge(S256)&state&nonce&redirect_uri=http://127.0.0.1:PORT/callback
  Br->>Cg: 이메일·비밀번호 (+MFA)
  Cg->>Br: 302 → redirect_uri?code&state
  Br->>Loop: GET /callback?code&state
  Loop->>App: code (state 확인)
  App->>Cg: POST /oauth2/token (code, code_verifier)
  Cg->>App: ID·액세스·새로고침 토큰
  App->>App: ID 토큰 검증 (JWKS, iss, aud, exp, nonce) → 새로고침 토큰만 키 보관함
```

## 1. 먼저 정할 것 (이 방식의 전제)

브라우저 로그인 + PKCE는 Cognito의 **도메인과 관리형 로그인(managed login)** 이 있어야 합니다 (`/oauth2/authorize`·`/oauth2/token` 끝점이 도메인에 붙음). 지금 운영 풀은 **도메인을 만들지 않았습니다** ([계정 설정](ACCOUNT_SETUP.md) P17 "만들지 않음 (웹은 자체 화면)").

| # | 결정 | 선택지 | 이 세션의 제안 |
|---|---|---|---|
| D-1 | 로그인 방식 | (가) 시스템 브라우저 + 관리형 로그인 + PKCE (이 문서의 기본) / (나) 앱 안 입력 칸에서 SRP 로그인 (`ALLOW_USER_SRP_AUTH`, 도메인 불필요, 비밀번호가 앱을 지남) / (다) 웹사이트 자체 화면이 앱용 코드를 넘기는 맞춤 흐름 (웹 쪽 작업 큼) | (가). 비밀번호가 앱을 지나지 않고, MFA·비밀번호 찾기 화면을 Cognito가 그림 |
| D-2 | 도메인 | Cognito 접두 도메인 (`<접두>.auth.ap-southeast-2.amazoncognito.com`) / 맞춤 도메인 (`auth.quantgeneration.com`, 인증서·Cloudflare DNS 필요) | 처음엔 접두 도메인, 공개 판매 전 맞춤 도메인 검토 |
| D-3 | 관리형 로그인의 **가입 화면** | 운영 풀은 스스로 가입이 켜져 있어 관리형 로그인에도 가입 링크가 보일 수 있음 (미검증). 그 화면은 웹 가입 화면의 동의 체크(약관·14세·소식 메일)와 동의 기록 속성 6개를 받지 않음 | 앱에서는 가입을 웹사이트로 보냄. 관리형 로그인에서 가입 링크를 숨길 수 있는지 확인하고, 못 숨기면 D-1 (나) 재검토 또는 사전 가입 Lambda로 동의 속성 없는 가입을 거절 (미검증) |
| D-4 | 새로고침 토큰 수명·회전 | 수명 7~30일, 회전 켬/끔 | 30일, 회전 켬 (8절 위협 표) |

## 2. 앱 클라이언트 `quantgen-desktop` (같은 풀)

| 항목 | 값 | 확인 상태 |
|---|---|---|
| 종류 | 공개 클라이언트 (비밀값 없음) | 제안 |
| OAuth 흐름 | Authorization code grant만. Implicit 끔. PKCE는 앱이 항상 `S256`으로 보냄 | Cognito가 공개 클라이언트에 PKCE를 권함 (확인) |
| 인증 흐름 | `ALLOW_REFRESH_TOKEN_AUTH`만 (D-1 (나)를 고르면 `ALLOW_USER_SRP_AUTH` 추가) | 제안 |
| 범위(scope) | `openid`, `email` (`profile`은 받을 것이 없어 뺌, 최소 수집) | 제안 |
| 콜백 URL | `http://127.0.0.1/callback`, `http://localhost/callback`. Cognito는 루프백 주소(localhost, 127.0.0.1, [::1])에 한해 등록한 포트와 다른 포트도 받고, 이때만 `http`를 허용 | 확인 (AWS 문서, 2026-11-24 검색) — 실제 콘솔 등록 시 다시 확인 |
| 로그아웃 URL | `http://127.0.0.1/signed-out` | 제안 |
| 토큰 | ID·액세스 60분, 새로고침 30일 (D-4) | 제안 |
| 새로고침 토큰 회전 | 켬 (유예 최대 60초). 회전을 켜면 `REFRESH_TOKEN_AUTH` 대신 `GetTokensFromRefreshToken` 또는 토큰 끝점을 씀 | 확인 (AWS 문서) |
| 토큰 폐기 | 켬 (웹 클라이언트와 같음, 운영 풀 16단계) | 확인 |
| 계정 존재 숨김 | 켬 | 제안 |
| 읽기 권한 | email, email_verified, 동의 속성 6개 | 제안 |
| 쓰기 권한 | 없음 (동의·소식 메일 변경은 웹 계정 페이지) | 제안 |

앱 쪽 설정값 (`core/app_identity.py`, OS 세션): `COGNITO_REGION = "ap-southeast-2"`, `COGNITO_USER_POOL_ID`, `COGNITO_DESKTOP_CLIENT_ID`, 그리고 **새 값 `COGNITO_DOMAIN`** (지금 없음 — OS 세션에 추가 요청). 모두 비밀값이 아닙니다.

## 3. 로그인 순서

1. `core.app_identity.accounts_configured()`가 거짓이면 (도메인 값이 생기면 그것도 조건에 포함) 로그인 단추를 숨기고 "계정 기능 준비 중"만 보임.
2. `code_verifier` (43~128자 무작위), `code_challenge = BASE64URL(SHA256(verifier))`, `state`·`nonce` (각 32바이트 무작위).
3. `127.0.0.1`의 임의 빈 포트에 HTTP 서버를 엶 (바깥 주소에 열지 않음). 5분 지나면 닫힘.
4. `webbrowser.open(<도메인>/oauth2/authorize?response_type=code&client_id&redirect_uri&scope=openid+email&state&nonce&code_challenge&code_challenge_method=S256)`.
5. `/callback`에서 `state`가 다르면 버리고 오류. `error=` 가 오면 그 코드만 화면에 (설명 글은 보이지 않음).
6. 브라우저에는 "QUANTGEN으로 돌아가세요" 한 줄 (토큰·코드 표시 없음, 외부 자원 없음).
7. `POST <도메인>/oauth2/token` (`grant_type=authorization_code`, `code`, `redirect_uri`, `client_id`, `code_verifier`).
8. ID 토큰 검증: JWKS 서명, `iss = https://cognito-idp.ap-southeast-2.amazonaws.com/<풀 ID>`, `aud = 데스크톱 클라이언트 ID`, `exp`, `nonce`, `token_use = id`.
9. 새로고침 토큰 → 키 보관함 (4절). 액세스·ID 토큰 → 메모리. 화면에는 이메일만 표시.
10. 액세스 토큰은 회사 데이터 서버(PAY-3)에 `Authorization: Bearer`로 쓰임 (`core/gateway/remote.py` `token_getter`).

## 4. 토큰 보관

| 토큰 | 위치 | 이유 |
|---|---|---|
| 새로고침 | `core.credentials.set_token("account_refresh", …)` — `names.TOKENS`에 이름 하나 추가 (종류 `token`). OS 자격 증명 저장소만 (환경변수·`.env`에서 읽지 않음, 기존 규칙) | 다시 로그인하지 않게 |
| 액세스·ID | 프로세스 메모리 | 60분짜리, 파일에 두지 않음 |
| OS 저장소가 없을 때 | 저장하지 않음 (실행할 때마다 로그인). 평문 파일로 대신하지 않음 (`kis_token`의 파일 예외를 따라 하지 않음) | KEY-2 원칙: 평문 저장 금지 |

- **Windows 자격 증명 크기 한도 위험 (미검증):** Windows 자격 증명 관리자의 비밀 크기 한도(약 2.5KB)와 Cognito 새로고침 토큰 길이(수 KB일 수 있음)에 따라 저장이 실패할 수 있습니다. 시험 9절 T-W1로 먼저 확인하고, 실패하면 토큰을 조각으로 나눠 여러 항목에 저장 (`account_refresh.1`, `.2`, …).
- **OA-41 (`set_backend(None)` 가·나 안, 소유자 답 없음, GPT가 가 안으로 진행):** 어느 안이든 "OS 저장소가 없으면 저장하지 않음"과 맞습니다. 시험은 메모리 백엔드(`set_backend(<가짜>)`)만 쓰고 실제 저장소를 건드리지 않습니다.

## 5. 로그아웃·계정 삭제 뒤

1. `POST <도메인>/oauth2/revoke` (새로고침 토큰, `client_id`) — 그 토큰과 그것으로 받은 액세스 토큰이 폐기됨 (확인). 실패해도 4번까지 진행.
2. 키 보관함에서 `account_refresh` 지움, 메모리 토큰 지움.
3. 관리형 로그인의 세션 쿠키(1시간)는 남으므로 `<도메인>/logout?client_id&logout_uri`를 브라우저로 열지 선택 (확인: 쿠키는 토큰과 별개).
4. 폐기된 토큰도 서명·만료 검사는 통과할 수 있으므로 (확인) 회사 서버는 필요하면 Cognito에 다시 묻는 경로를 둡니다 (PAY-3 2절).
5. 웹에서 탈퇴했거나 관리자가 삭제·정지했으면 다음 새로고침이 실패 → 앱은 토큰을 지우고 "로그인 필요"로 돌아감.

## 6. 오프라인과 계정 없는 사용

- 무료 기능은 계정 없이 그대로 씁니다 (처리방침: "데스크톱 앱의 무료 기능은 계정 없이 사용").
- 오프라인이거나 새로고침이 실패하면 계정이 필요한 기능(회사 데이터 길, 유료 기능)만 "오프라인 — 다시 연결되면 로그인 상태를 확인합니다"로 멈추고, 다른 기능은 영향 없음.
- 액세스 토큰이 만료되고 새로고침이 안 되면 회사 길은 꺼진 것으로 보고 `gateway.status()`에 이유를 표시 (값을 지어내지 않음).

## 7. MFA·비밀번호 찾기·가입

| 상황 | 데스크톱에서 | 근거 |
|---|---|---|
| 인증 앱 MFA | 관리형 로그인이 코드 입력 화면을 그림 | 관리형 로그인 기능 목록 (확인) |
| 이메일 MFA | 관리형 로그인이 이메일 코드 화면을 그림 (Essentials + 자체 SES) | 확인 |
| 비밀번호 찾기 (MFA 없음 또는 인증 앱) | 관리형 로그인의 "비밀번호 찾기" | 미검증 (화면) |
| 비밀번호 찾기 (이메일 MFA 회원) | Cognito가 막음 → 웹과 같은 안내: "contact@quantgeneration.com으로 문의" → 관리자 안내서 6.1 (두 번째 확인 뒤 임시 비밀번호) 또는 6.2 (1회용 코드 동의 뒤 삭제·재가입) | [계정 설정](ACCOUNT_SETUP.md) P8, 소유자 결정 2026-11-20 |
| 임시 비밀번호로 첫 로그인 | 관리형 로그인이 새 비밀번호 화면 (`NEW_PASSWORD_REQUIRED`) | 미검증 (화면) |
| 가입 | 앱은 웹 가입 화면(`https://quantgeneration.com`)으로 보냄. 관리형 로그인 가입은 쓰지 않음 (D-3) | 동의 기록은 웹 가입 화면에서만 받음 |

## 8. 위협과 대책

| 위협 | 대책 |
|---|---|
| 다른 프로그램이 콜백 포트로 코드를 가로챔 | PKCE S256 (코드만으로는 토큰을 못 받음), `state` 확인, 127.0.0.1에만 열고 5분 뒤 닫음 |
| 가짜 로그인 페이지 | 시스템 브라우저 주소창으로 도메인 확인 가능 (앱 내장 브라우저 쓰지 않음). 맞춤 도메인이면 더 알아보기 쉬움 (D-2) |
| 키 보관함의 새로고침 토큰 도난 | 30일 수명 + 회전 (도난된 토큰은 한 번 쓰이면 원래 앱의 다음 새로고침이 실패해 드러남), 로그아웃·관리자 정지 때 폐기 |
| 토큰이 기록에 남음 | 토큰·코드·verifier를 로그·오류 글·화면에 쓰지 않음 (게이트웨이 `RemoteFailed` 원칙과 같음) |
| 관리형 로그인 가입으로 동의 없이 계정 생김 | D-3 |
| 비밀번호가 앱을 지남 | (가) 방식에서는 지나지 않음 |

## 9. 시험 계획

**자동 시험 (오프라인, 코드와 함께, 실제 Cognito·키 보관함·네트워크 없음):**

| # | 시험 | 기대 |
|---|---|---|
| T-1 | 가짜 IdP (로컬 HTTP: authorize·token·revoke·JWKS) 로 전체 로그인 | 새로고침 토큰이 가짜 키 보관함에, 액세스·ID는 메모리에만 |
| T-2 | `state` 다름 / `error=` 응답 / 5분 시간 초과 | 토큰 요청 없이 실패, 콜백 서버 닫힘 |
| T-3 | ID 토큰의 `aud`·`iss`·`nonce`·`exp`·서명 하나씩 틀림 | 거절, 아무것도 저장 안 함 |
| T-4 | PKCE: verifier 길이·문자, challenge = SHA256 | 규격대로 |
| T-5 | 새로고침 회전: 새 토큰 저장, 옛 토큰 재사용 시 실패 처리 | 키 보관함 갱신, 실패 시 로그아웃 상태 |
| T-6 | 로그아웃: revoke 실패해도 로컬 지움 | 키 보관함 비어 있음 |
| T-7 | OS 저장소 없음 (`set_backend(None)`) | 저장하지 않고 로그인은 이번 실행만 유지, 평문 파일 없음 |
| T-8 | 토큰·코드가 로그·예외 글에 없음 | 문자열 검사 |
| T-9 | 계정 설정 빈 값 | 로그인 단추 없음, 다른 기능 정상 |
| T-W1 | 긴 토큰(4KB) 저장·읽기 (Windows 저장소 조각 저장) | 같은 값 복원 (Windows CI에서) |

**소유자 수동 시험 (웹 계정 화면 공개 뒤, 시험 계정 `내아이디+qgtest…`):**

1. 콘솔에서 `quantgen-desktop` 클라이언트와 도메인 만들기 (그때 `OWNER_STEPS`에 단계 추가).
2. 앱에서 로그인 → 브라우저 → 돌아옴 → 이메일 표시.
3. 인증 앱 MFA 회원, 이메일 MFA 회원 각각 로그인.
4. 이메일 MFA 회원 비밀번호 찾기 → 거절 안내가 contact@를 가리키는지.
5. 앱 다시 시작 → 로그인 유지. 로그아웃 → 다시 시작 → 로그아웃 상태.
6. 웹에서 탈퇴 → 앱이 다음 새로고침에서 로그아웃 상태로.
7. CloudTrail에 데스크톱 로그인 이벤트가 남는지 (관리자 안내서 13절).

## 10. UI 세션 요청 목록 (화면은 UI 세션 몫)

1. 계정 단추 (상단 또는 설정): 로그아웃 상태 "로그인", 로그인 상태 이메일 + "로그아웃".
2. 로그인 중 화면: "브라우저에서 로그인을 마치세요" + 취소 단추 + 5분 남은 시간. 브라우저가 안 열리면 주소 복사 단추.
3. 오류 표시: 시간 초과, 취소, 서버 오류 코드 (설명 글 없이 코드와 다시 시도).
4. 오프라인·만료 상태 줄: 계정이 필요한 기능 옆에만.
5. "계정 만들기" → 웹 가입 화면 열기. "비밀번호를 잊었나요" → 관리형 로그인 링크 + 이메일 MFA 회원 안내 (contact@).
6. 키·연결 화면(`gateway.status()`)의 회사 길 행에 "로그인 필요"를 "키 없음"과 구분해 표시 (KEY-5 요청문 v2와 같은 원칙).

## 11. 결정·확인 목록

| # | 내용 | 누가 |
|---|---|---|
| D-1 | 로그인 방식 (가)/(나)/(다) | 소유자 (제안: 가) |
| D-2 | 도메인 종류 | 소유자 |
| D-3 | 관리형 로그인 가입 화면 처리 | 이 세션 확인 → 소유자 |
| D-4 | 새로고침 토큰 30일·회전 | 소유자 |
| D-5 | 처리방침: 데스크톱 로그인의 처리 항목(새로고침 토큰을 사용자 PC 키 보관함에 둠, 로그인 기록) 추가 | 메인 (정책 PR, 코드 때) |
| D-6 | `COGNITO_DOMAIN` 설정값 추가 | OS 세션 |
| 미검증 | 관리형 로그인의 가입 링크 숨김, 비밀번호 찾기·새 비밀번호 화면, Windows 저장 한도와 토큰 길이, 루프백 콜백의 콘솔 등록 형식 | 코드 착수 전 확인 |

## 출처 (AWS 문서, 2026-11-24 검색)

- 루프백 콜백·포트: https://docs.aws.amazon.com/cognito/latest/developerguide/authorization-endpoint.html , https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_UserPoolClientType.html
- 토큰 끝점·PKCE: https://docs.aws.amazon.com/cognito/latest/developerguide/token-endpoint.html
- 새로고침 토큰 회전: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-refresh-token.html
- 토큰 폐기: https://docs.aws.amazon.com/cognito/latest/developerguide/revocation-endpoint.html , https://docs.aws.amazon.com/cognito/latest/developerguide/token-revocation.html
- 관리형 로그인: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-managed-login.html
