# 법인 설립 때 바꿀 것 (소유자 요청 2026-11-19)

**누가 읽나:** 어느 Claude 세션이든, 소유자가 **"법인 설립 완료되었습니다."** (또는 "법인 설립 완료: <법인 등기상 이름>")라고 보내면 이 파일을 읽고 아래 표를 그대로 소유자에게 안내합니다. 법인 등기상 이름·사업자등록번호·법인 이메일·주소가 아직 없으면 먼저 물어봅니다.

**소유자 요청 원문 (2026-11-19):** "15번 화면을 지금 그대로 저장했고, 나중에 법인 설립 시 즉시 수정할 수 있도록 메모리 등에 저장해주시고, 추후 클로드한테 "법인 설립 완료되었습니다." 이렇게 보내면 위 부분을 포함한 수정해야되는 부분을 메모리 파일로부터 참고해서 알려주세요"

작성: PAYMENTS_ACCOUNT_KEYS 세션. 근거 문서 (main 병합 뒤 경로): `docs/commercial/accounts/ACCOUNT_SETUP.md` 0.1절·P8·P10·P12, `docs/commercial/accounts/OWNER_STEPS.md` 5절, `docs/commercial/accounts/ADMIN_GUIDE.md` 부록 B·6.1절, `docs/commercial/GATEWAY_DESIGN.md` 8절. 법률 관련 줄은 **법률 자문이 아닙니다** (근거를 줄마다 적음).

## 먼저 물어볼 것
1. 법인 등기상 이름, 사업자등록번호, 통신판매업 신고번호 (유료를 열 때), 법인 이메일 주소, 법인 주소·대표 전화.
2. **이미 회원이 있는지** (Cognito 운영 풀 `quantgen-prod` = `ap-southeast-2_…`, Golden Hour Code 계정의 사용자 수). 0명이면 아래 C는 필요 없음.
3. *(2026-11-20 추가)* 법인 **영문** 등기명·영문 주소·대표 전화. D-U-N-S, Apple, Google이 이 값으로 법인을 확인하므로 철자가 등기와 같아야 함 (F1·F2).
4. *(2026-11-20 추가)* 대표이사가 누구인지, 공동창업자·지분 관계가 있는지 (H1 권리 이전, F2 Apple의 서명 권한, G4 대표자 교육 대상).
5. *(2026-11-20 추가)* 법인 명의 은행 계좌를 열었는지 (G2), 공개할 사업장 주소를 정했는지. 2026-11-19 결정으로 공개 문서에서 주소를 뺐지만, 유료 판매 때는 사이트에 주소를 표시해야 하므로 다시 정함 (A7). 〔근거: `docs/compliance/FACTS.md` 답 2 "주소는 유료 판매 전에 다시 정합니다", 전자상거래법 제10조 제1항 제2호〕

## 0. 등기 직후 순서 *(2026-11-20 추가)*
기한이 있거나 다른 일의 선행인 것부터. 각 줄의 상세는 아래 표.
1. **사업자등록** (법인설립신고 함께): 사업 개시일부터 20일 이내, 법인은 실무상 설립등기일 기준. 늦으면 미등록 가산세 (G1). 〔근거: 부가가치세법 제8조 제1항〕
2. **법인 계좌** 개설 → **D-U-N-S** 조회·신청 (무료, 최대 5영업일, Apple 반영 최대 2영업일) (G2, F1).
3. 문서·표기 교체 A1~A7 (회원이 있으면 C 먼저), AWS·Cloudflare·Microsoft 365 명의 B1~B8.
4. 개인 → 법인 **권리 이전** (코드·로고·도메인), NEXTGEN 판매 중지 (H).
5. 결제 문의·PG 가맹 → 통신판매업 신고 → 유료 판매 (G3, E5). 유사투자자문업 신고는 시그널 상품을 팔 때만 (G4).
6. D-U-N-S가 나오면 Apple·Google 조직 계정 → 서명 인증서·키 → 서명한 빌드 배포 (F).
7. 데이터 계약 (E1, E6) → `routes.json` `commercial`·회사 서버 (E2~E4).
〔근거: 프로젝트 문서 `claude/cross-platform-expansion-2026-11-11.md` 6절 "법인 등기 직후의 순서", Notion "QUANTGEN 상업화 (GPT 버젼)"의 설립 순서 (등기 → 법인설립신고·사업자등록 → 법인계좌·회계·권리 이전 → 신고·데이터 계약·PG 심사)〕

## A. 문서·정책 (세션이 함)
| # | 누가 | 할 일 |
|---|---|---|
| A1 | PAYMENTS 세션 | `ACCOUNT_SETUP.md` 0.1절 "운영자 표기"를 개인 → 법인명으로, `ADMIN_GUIDE.md` 새 판. 메인에 값 목록 전달 |
| A2 | 메인 세션 | 정책 PR: `docs/compliance/release-profile.json`의 필드 (main에서 확인한 이름 그대로) `operator.legal_name`, `operator.representative`, `operator.business_registration`, `operator.ecommerce_registration`, `operator.support_phone`, `operator.address`, `deployment.contracting_entity` (같은 블록의 `operator.support_email`·`operator.privacy_contact`·`operator.refund_contact`도 법인 메일로 바꿀지 확인), 그리고 `01`·`02`·`16`의 운영자·책임자·계약 주체 |
| A3 | 웹사이트 세션 | 정책 원문 다시 생성 (메인 PR 병합 뒤). 인증 메일 하단 "QUANTGEN · Contact" 줄에 법인명을 넣을지 소유자에게 물음 (아래 B5) |
| A4 | 모두 | 법인 등기 **뒤에만** "(주)" 등 회사 표시. 〔근거: 상법 제20조·제28조〕 |
| A5 | 메인 세션 | *(2026-11-20 추가)* A2보다 범위가 넓음: `docs/compliance/FACTS.md` "운영자 개인 표기·문의 메일·이용연령" 절의 **"바꾼 위치" 표 전체** (01·02·03·04·05·06·08·10·16·17·18·20의 `QUANTGEN(운영자 고건)`, `release-profile.json` `operator.legal_name`). 찾기: `grep -rn "운영자 고건" docs/compliance`. README.md 7행·RELEASE_GAPS.md 7행은 단순 치환하지 말고 새 날짜 기록으로 고쳐 씀. "이력 보존" 줄은 옛 문장을 두고 날짜 줄을 더함. 01 176행 개인정보 보호책임자 `고건(운영자 본인)` 검토. 16 F16-01의 사업자등록번호·통신판매업 신고번호 칸 (지금 "해당 없음 (무료 서비스, 사업자 미등록)", `ACCOUNT_SETUP.md` 233행)을 실제 번호로, 공개 전 오타 대조 (16 C16-05). 바꾼 문서의 버전·기준일·현재 상태 줄 갱신 |
| A6 | OS 세션 | *(2026-11-20 추가)* `core/app_identity.py`: `PUBLISHER_DISPLAY_NAME`을 법인명으로 바꿀지 소유자에게 물음 (서명 인증서의 주체와 맞추는 것이 자연스러움). **`ORGANIZATION_NAME`·`APPLICATION_NAME`은 그대로** (QSettings 이름이라 바꾸면 사용자 설정이 사라짐, 같은 파일 15행 주석). 번들 ID `com.quantgeneration.quantgen` 소유자 확인 뒤 `BUNDLE_ID_CONFIRMED = True`. 같은 PR에서 `tests/app_identity_acceptance.py`의 `test_no_company_suffix_before_incorporation` (회사 표시 금지)와 `BUNDLE_ID_CONFIRMED` 단언을 법인 뒤 기준으로 고침 |
| A7 | 웹사이트 세션 | *(2026-11-20 추가, 유료 판매를 열 때)* 사이트 초기 화면(푸터)에 사업자 신원 표시: 상호·대표자, 사업장 주소, 전화·이메일, 사업자등록번호, 이용약관, 호스팅 제공자 상호 + 공정위 사업자정보 공개페이지 연결 + 통신판매업 신고번호·신고기관. 약관·환불·개인정보 초안에 남은 판매자 "(주)넥스트제너레이션"이 실제 등기명과 한 글자도 다르지 않은지 대조. 〔근거: 전자상거래법 제10조 제1항, 제13조; 공정위 의결 (사업자정보 공개페이지 미연결 시정명령); 프로젝트 문서 `claude/quantgeneration-site-review-2026-11-10.md`; 16번 문서 F16-01 양식〕 |

## B. AWS (소유자가 콘솔에서)
| # | 할 일 |
|---|---|
| B1 | AWS 계정 **두 개 모두** (프로젝트 계정 Golden Hour Code 끝 8543, 관리 계정 끝 3710): 각 계정의 **루트**로 로그인 → 오른쪽 위 계정 → **Account** → 루트 로그인 이메일을 **법인 이메일**로, Contact information (이름·회사명·우편 주소·전화)을 법인 것으로 → Edit/Update *(문구 미검증)*. 2026-11-19 소유자 개인 이메일로 유료 플랜을 올렸기 때문 |
| B2 | 결제 수단·청구 주체를 법인으로 (AWS 결제 설정). 계정·사용자 풀은 새로 만들지 않음 (풀·회원 그대로) |
| B3 | 예산 알림 받는 메일 (24a·24b: `contact@quantgeneration.com`)은 그대로 둘지 법인 메일로 바꿀지 확인 |
| B4 | IAM Identity Center 사용자 (관리 계정)의 이름·이메일을 법인 담당자로 바꿀지 확인. 관리자를 늘리면 사람마다 따로 로그인 + MFA (`ADMIN_GUIDE.md` 9절) |
| B5 | Cognito 인증 메일 (Message templates → Verification message): 하단 문구에 법인명 표기를 넣을지. 로고 주소 `https://quantgeneration.com/quantgen-logo-white.png` 유지 |
| B6 | *(2026-11-20 추가)* **Cloudflare** (도메인 등록·이메일 설정): 계정 소유 이메일과 `quantgeneration.com` 등록자(Registrant) 연락처를 법인으로. Apple 조직 가입은 웹사이트 도메인이 조직과 연관돼야 하고 업무 메일이 그 도메인이어야 함 (F2). 〔근거: `docs/compliance/FACTS.md` 114행 (도메인 등록·이메일 설정은 Cloudflare), Apple Developer 가입 안내〕 |
| B7 | *(2026-11-20 추가)* 결제 주체를 바꾼 뒤 AWS 청구서의 판매자(계약 법인)를 확인해, 처리방침 처리위탁·국외이전 표의 "계약 법인명 확인 필요" 칸을 채움 → 메인 세션 정책 PR (A2·A5와 같은 PR). 〔근거: `ACCOUNT_SETUP.md` 249·260행 (미검증 표시)〕 |
| B8 | *(2026-11-20 추가)* **Microsoft 365** (문의 메일을 Gmail에서 옮기는 계획, 2026-11-13 기준 구매 전): 아직 안 샀으면 법인 명의·법인 결제로 구매, 이미 샀으면 조직 정보·결제 주체를 법인으로. 구매 뒤 실제 테넌트 위치·계약 법인을 확인해 정책 01·07·08·16·20 후보 문구에 반영 (웹사이트 세션). 〔근거: handoff `WEBSITE_AWS_SESSION_CURRENT.md` W1·W2〕 |

## C. 회원이 이미 있으면 (법 절차, 바로 안 될 수 있음)
| # | 할 일 |
|---|---|
| C1 | 회원 정보를 개인 → 법인으로 넘기기 **전에** 회원에게 미리 알림: 이전 사실, 받는 법인의 이름·주소·전화·연락처, 이전을 원하지 않을 때의 방법. 어려우면 홈페이지 30일 이상 게시. 공개 문서의 이름이 실제로 바뀌는 날은 알림 뒤. 〔근거: 개인정보 보호법 제27조, 시행령 제29조〕 |
| C2 | 알림 발송: `ADMIN_GUIDE.md` 12절 명령으로 Confirmed 회원 이메일 목록 → SES 안내 메일 (광고 문구 없음). 발송 날짜 기록 |

## D. 회원 로그인·MFA 재검토 (2026-11-19 결정, "15번" 포함)
| # | 지금 (2026-11-19) | 법인·유료 단계에서 다시 정할 것 |
|---|---|---|
| D1 | 회원 MFA: **Optional**, 방법 **인증 앱 + 이메일**, **SMS 끔** (전화번호를 받지 않음). `ACCOUNT_SETUP.md` P12 | 유료 가입 때 본인인증(휴대폰·PASS)으로 전화번호를 받게 되면 SMS MFA를 켤지 (문자 요금, SMS 제한 해제 신청, SMS 펌핑 방어 필요) |
| D2 | 계정 복구 (15번): Self-service 켬, **Email if available, otherwise SMS** (이메일 MFA를 켜서 "Email only"는 Cognito가 막음). `ACCOUNT_SETUP.md` P8 | 전화번호를 받으면 이메일 MFA 회원도 문자로 스스로 비밀번호를 찾을 수 있게 됨 → 15번을 다시 설정. 또는 이메일 MFA를 끄고 "Email only" |
| D3 | 이메일 MFA 회원이 비밀번호를 잊으면 **관리자 임시 비밀번호** (`ADMIN_GUIDE.md` 6.1, 7일 만료) | D2가 바뀌면 6.1 절차를 없애거나 줄임 |
| D4 | 비밀번호: 10자 이상, 숫자·소문자·대문자·**특수문자** (13번) | 그대로 (바꿀 이유 없음) |
| D5 | 받는 개인정보: 이메일·비밀번호·동의 기록 (이름·생년월일·전화번호 받지 않음) | 유료: 결제는 PG가 받음 (카드번호 저장 안 함), 만 19세 확인은 본인확인기관 경유 (주민등록번호 받지 않음 〔근거: 개인정보 보호법 제24조의2, 정보통신망법 제23조의2, 원문 미확인〕), 거래 기록 보관 (계약·결제 5년, 불만·분쟁 3년 〔근거: 전자상거래법 시행령 제6조, 현행 원문 재확인 필요〕). 처리방침 개정 (PAY-2) |

## E. 상업화 (법인 뒤, 앱 구조 수정 없음; `GATEWAY_DESIGN.md` 8절)
| # | 할 일 |
|---|---|
| E1 | 공급사 계약: 코스콤/KRX, Yahoo 대체, FMP 표시 또는 제외, Cboe (VIX) |
| E2 | `core/gateway/routes.json` `commercial` 값 확정, `display_rights.json` 갱신 (PAYMENTS + 데이터소스 세션) |
| E3 | `core/app_identity.py`: `DATA_API_BASE`, Cognito ID, `GATEWAY_PROFILE = "commercial"` (OS 세션) |
| E4 | 회사 데이터 서버 (PAY-3; 위치는 소유자에게 먼저 물음) |
| E5 | 유료: 사업자등록, 통신판매업 신고, PG 승인, 유료 만 19세 기준 (PAY-1·PAY-2). 받은 번호·주소는 A2의 `release-profile.json` 필드 (`operator.business_registration`, `operator.ecommerce_registration`, `operator.address`, `operator.support_phone`, `deployment.contracting_entity`)로 메인 정책 PR에 넘김 |
| E6 | *(2026-11-20 추가)* DIDM·연구용 키 (`core/credentials/names.py` `RESEARCH` 9개): 공급사 데이터를 화면에 보이지 않으면 구조 변경 없이 **키만 사업자 요금제로** (예: Tiingo 개인 $30 → 사업자 $50). 화면 표시·재배포는 별도 계약 (Tiingo·Trading Economics·Cryptopanic Enterprise 등). RavenPack 계약은 DIDM 3단계 뒤. 공급사 상업 약관은 공급사별 확인. 〔근거: handoff `plans/2026-11-17/D14_RAVENPACK_ALTERNATIVES.md` 7.1절·8절, 미검증 표시 포함〕 |

## F. 앱 서명·배포·스토어 (D-U-N-S 뒤; OS 세션 + 소유자) *(2026-11-20 추가)*
지금은 서명 없는 설치파일 공개 배포 금지, Apple 개인 명의 가입 안 함 (서명 주체가 실명으로 보임). 아래가 끝나야 공개 배포.

| # | 할 일 |
|---|---|
| F1 | **D-U-N-S** 조회 → 없으면 신청 (무료, 최대 5영업일, Apple 반영 최대 2영업일). Apple은 이 번호로 법인의 실재·법인격·주소를 확인하므로 영문명·주소·전화가 등기와 같아야 함. 〔근거: `claude/cross-platform-expansion-2026-11-11.md` 6절, Apple Developer 가입 안내〕 |
| F2 | **Apple Developer Program 조직 가입** (연 99달러): 법인격, D-U-N-S, 서명 권한, 공개된 웹사이트(조직 도메인), 그 도메인의 업무 메일 (Gmail 불가). 앱 판매자명 = 법인 등기명. → Developer ID Application 인증서 → 공증 → 서명한 dmg 배포 (OS-M5~M7). 〔근거: Apple Developer 가입 안내, `docs/platform/LICENSE_COMPLIANCE_PREP.md` 42행〕 |
| F3 | **Windows OV 코드서명 인증서** 법인 명의 (유효기간 최대 460일, 연 약 $150~300: 둘 다 **미검증**). Azure Artifact Signing은 한국 법인이 못 쓴다는 Q&A 답만 봄 (공식 문서 미확인). 받기 전까지 서명 없는 설치파일 공개 배포 금지 유지. 〔근거: `docs/platform/PLATFORM_EXPANSION_2026-11-17.md` 1절·4절, handoff 마스터 8절〕 |
| F4 | **Google**: Play 조직 계정 + Android 개발자 인증 (D-U-N-S, Search Console 웹사이트 인증, 조직 서류) → 배포용 업로드 키 생성 (키 지문은 법인 계정에 한 번만 등록) → apk·Play 배포 (OS-A6·A7). 그 전에는 디버그 APK와 한정 배포 (기기 50대, 비상업)만. Play의 조직 계정 요건은 **추론**. 〔근거: `claude/cross-platform-expansion-2026-11-11.md` 7.3절, `mobile/README.md`〕 |
| F5 | **App Store** (I3~I5): App Store Connect의 대한민국 규정 준수 정보 (회사 이름·이메일·전화·사업자등록번호), 제출 전 I2 결정 (결제 범위 a/b/c, "무료도 로그인 필수"와 심사지침 5.1.1(v) 충돌), 심사 메모에 "주문 기능 없음" 표준 답변. 〔근거: `claude/cross-platform-expansion-2026-11-11.md` 7.4절〕 |
| F6 | 서명본이 나오면 `releases.json`의 `signed` 값과 다운로드 페이지 상태 (준비 중 → 비공개 베타 → 정식)를 웹사이트 세션이 바꿈. 〔근거: `claude/quantgeneration-site-review-2026-11-10.md`〕 |

## G. 사업자·세무·신고 (소유자; 법률·세무 자문 아님) *(2026-11-20 추가)*
| # | 할 일 |
|---|---|
| G1 | **사업자등록** (법인설립신고 함께, 홈택스 또는 관할 세무서): 20일 기한. 업종은 정해 둔 응용 소프트웨어 개발 및 공급업 (722000). 유사투자자문업 신고 전에 업종 추가가 필요한지는 세무사·행정사에게 확인 (자료가 엇갈림). 〔근거: 부가가치세법 제8조 제1항, `claude/payment-network-review-2026-11-11.md` 2절·8장 6번〕 |
| G2 | **법인 계좌**: PG 정산 계좌. 주거래은행 기업영업점에 CMS 이용계약·직계약 가상계좌·펌뱅킹을 이 업종에 열어 주는지 함께 문의 (결제망 문의 3번). 기장·부가세 체계와 계좌 출금 매출의 현금영수증 발급 방식은 세무사 (문의 6번) |
| G3 | **결제 문의 7건**을 법인 명의로 발송 (금융결제원 CMS, 효성CMS, 주거래은행, 카드 PG, 금융규제민원포털, 세무사·행정사, 관할 구청). 초안 PAY-0은 아직 없음 (PAYMENTS 세션 `next_ids`). 권고 순서: 시나리오 A (도구형만 카드 PG)로 출시 → PG 가맹 → 통신판매업 신고 (구매안전서비스 이용확인증). 신고 서류 전에 회신을 받아 "신고는 했는데 결제 경로가 없는" 상태를 피함. 〔근거: `claude/payment-network-review-2026-11-11.md` 7·8장〕 |
| G4 | **유사투자자문업 신고** (관문 G2, 시그널 상품을 팔 때만): 대표자 사전교육 8시간 (신고일 전 1년 이내), 사무실 계약 서류, 심사 2~6개월 (자료마다 다름), 유효기간 5년. 신고 전에 금융규제민원포털 비조치의견서로 도구형 범위 확인. 신고하면 카드 PG가 막힐 수 있음 (포트원 입점불가 업종). 〔근거: `claude/QUANTGEN-license-audit-2026-11-04.md`, `claude/payment-network-review-2026-11-11.md` 3·4장〕 |
| G5 | **법률 확인** (관문 L, D-14): Q-SCORE 등 기본 탑재 여부의 최종 판단 (소유자 2026-11-17: 법인 설립 때 법무사 도움 뒤 결정), `claude/quantgen-vision-first-step-2026-11-17.md` "법률 질의" 6건, PySide6 LGPL로 소스를 닫고 팔 때의 조건 (macOS 공증·iOS 정적 링크) |

## H. 개인 → 법인 권리·자산 이전 (소유자) *(2026-11-20 추가)*
| # | 할 일 |
|---|---|
| H1 | 자산 장부를 만들고 법인으로 넘김: 코드 (`xkg4real/quantgen`, website 저장소), 로고·F1 심볼·아이콘, 글꼴 (QG Interface, OFL), 도메인 (B6), 사이트. 공동 기여자가 있으면 기여분 권리 관계를 먼저 정리. 양도 대가와 세금 처리는 세무사·변호사. 〔근거: Notion "QUANTGEN 상업화 (GPT 버젼)" C2 (법인 이전 대상 장부), Notion "QUANTGEN 상업화 실행 분석서" (코드 저작권 귀속)〕 |
| H2 | F1 심볼·아이콘: ChatGPT로 만든 계정의 주인 확인 → 권리 이전 → 비슷한 상표 조회 → QUANTGEN 상표·로고 출원을 법인 명의로 (출원 여부는 소유자 결정). 〔근거: `claude/QUANTGEN-license-audit-2026-11-04.md` "라이선스 주의 항목"〕 |
| H3 | NEXTGEN (크몽 판매) 일시 중지: 소유자가 밝힌 계획 (QUANTGEN 법인을 등록하면 NEXTGEN 판매를 잠시 멈춤). 크몽 상품 판매 중지와 진행 중 주문 처리 확인 |

## 보강 기록
- 2026-11-20 (claude.ai 채팅, 소유자 요청 "추가해야 될 부분 있으면 바로바로 넣어주세요"): 먼저 물어볼 것 3~5, 0절, A5~A7, B6~B8, E6, F·G·H절 추가. 기존 줄은 바꾸지 않음. 근거는 줄마다 적음: main `9f76b07`, handoff `e831256`, claude.ai 프로젝트 "QUANTGEN_런칭준비" 문서, 소유자 Notion. 법령 줄은 검색으로 확인한 조문 번호이며 **법률 자문이 아닙니다**.
- 원본: GitHub `xkg4real/quantgen` `handoff` 브랜치 `INCORPORATION_CHECKLIST.md`. 사본: claude.ai 프로젝트 "QUANTGEN_런칭준비" 문서 `claude/incorporation-checklist.md`, Notion Documents "법인 설립 체크리스트 (QUANTGEN)". 고칠 때는 원본을 먼저 고치고 사본을 맞춤.
