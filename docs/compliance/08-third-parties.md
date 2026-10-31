# 08. 외부 SDK·데이터 제공자 점검대장

- 문서 ID: QG-C08
- 버전: 1.0
- 기준일: 2026-10-31
- 상태: review-required
- 관리 주체: (주)넥스트제너레이션
- 문의: {{operator.support_email}}

## 적용 범위와 현재 상태

사진의 8번 ‘외부 SDK를 점검’에 대응한다. QUANTGEN의 직접 의존성, 외부 API, 인증정보, 제공 데이터의 이용권을 함께 관리한다. 패키지의 오픈소스 라이선스와 해당 패키지가 접속하는 서비스의 데이터·상업 이용 계약은 서로 다른 검토 대상이다.

현재 브라우저 앱은 Flet, 선택 데스크톱 앱은 PyQt6를 사용한다. 시장 데이터와 선택 AI 해설은 외부 요청을 수행한다. 제공자가 받는 요청에는 아래 명시한 필드 외에 접속 IP·요청 시각·HTTP 헤더 등 통신 메타데이터가 포함될 수 있다. 설치형에서는 이용자 기기가, 서버형에서는 운영 서버가 요청의 출발점이므로 실제 배포 구조를 확정해야 한다. 키가 없다는 사실은 개인정보 처리·쿠키·상업 이용 제한이 없다는 뜻이 아니다.

아래는 코드에서 확인한 목록이며, 실제 배포 시 설치되는 전이 의존성이나 호스팅 사업자 전체를 인증한 목록은 아니다. 저장소에서 제공자별 계약, 국외 이전의 구체적 국가·보유기간, 상업 재배포 허락을 일괄 확인하지 못했다. 현재 판정은 `NOT_VERIFIED`이며 ‘무료 API이므로 상업 이용 가능’으로 바꾸지 않는다.

## 정책 또는 구현 기준

### 외부 서비스 인벤토리

| 서비스·연결 | 기능과 요청 시점 | 전송·수신 항목 및 인증 | 로컬 처리·검토 항목 |
|---|---|---|---|
| Financial Modeling Prep | 시세·가격 이력 조회 | 종목, 조회기간, `FMP_API_KEY`; 키가 쿼리 문자열에 포함됨 | 가격 이력 캐시. 예외·프록시 로그의 키 노출 방지, 계약의 상업 표시·파생지표·재배포 범위 확인 |
| 한국투자증권 KIS | 시세 조회와 OAuth 토큰 발급 | 앱 키·시크릿으로 토큰 발급, 이후 토큰·종목·조회 조건 전송 | `~/.nextgen/kis_token.json`에 토큰 저장. 읽기 전용 허용목록과 토큰 파일 접근권한·삭제 절차 확인 |
| KIS 종목 마스터 다운로드 | 종목 식별용 마스터 파일 다운로드 | 요청한 마스터 파일명; 다운로드 호스트 별도 | `new.real.download.dws.co.kr`도 연결 목록에 포함. 종목 데이터의 배포권 확인 |
| 금융감독원 OpenDART | 공시·재무·법인코드 조회 | 공시 조회 조건과 `crtfc_key` 쿼리 | 법인코드 JSON 캐시. 공개 공시의 이용 조건 및 키 로그 제거 확인 |
| 한국거래소 KRX | Open API 시장 데이터; 레거시 CSV 코드 존재 | `AUTH_KEY` 헤더와 조회 조건; 레거시 OTP·다운로드 요청 | 현 코드의 레거시 URL은 HTTP이며 접근 거절 처리 존재. 배포에서 사용할 경로를 확정하고 전송 보호·계약 확인 |
| FRED / pandas-datareader | 금리·거시 시계열 조회 | 시계열 ID와 기간; 현재 경로는 API 키 불필요 | 시계열별 원권리자가 다를 수 있음. FRED 접근권을 모든 시계열 상업 이용권으로 간주하지 않음 |
| Yahoo Finance / yfinance | 주가·환율·선물·지수 이력 | 티커와 기간; 앱이 별도 계좌 키를 요구하지 않음 | 라이브러리 내부 세션·쿠키·보관 위치는 설치 버전과 실제 실행으로 확인. 서비스 약관·데이터 이용권 별도 검토 |
| Goldman Sachs Marquee / gs-quant | 로컬 계산 및 선택 세션·가격 조회 | 로컬 분석은 네트워크가 필요하지 않음. 선택 연결은 `GS_CLIENT_ID`·`GS_CLIENT_SECRET`와 `run_analytics` 범위 사용 | 오프라인 함수와 원격 세션 구분. 호출별 상품 파라미터·제공 데이터 이용 조건 확인 |
| Upbit 공개 API | 가상자산 시세·일봉 | 종목·기간·조회 조건, API 키 불필요 | 공개 데이터 이용약관·호출 제한·상업 표시 및 재배포 범위 확인 |
| Upbit 계좌 API | 선택 잔액 조회 `GET /v1/accounts` | 접근 키로 만든 JWT 전송; 통화·기준통화·잔액·잠금 수량·평균 매수가 수신, 총수량·원화평가액 계산 | 보유 통화의 종목을 Upbit 공개 시세 API에 추가 전송하여 평가. 계좌정보는 개인정보 처리 목록에 포함. 자산조회 권한만 사용. Flet는 키 설정 후 Refresh에서 조회하고, 네이티브는 기본 OFF 선택 사용 |
| Binance 공개 API | 가격·펀딩·미결제약정 조회 | 종목·기간; 현재 코드에 계좌 인증 없음 | `data-api.binance.vision`, `api.binance.com`, `fapi.binance.com` 각각 확인. 접속 가능성과 국내 제공·상업 데이터 이용권을 구분 |
| CoinGecko 공개 API | 가상자산 목록·시가총액 조회 함수 | 통화·정렬·페이지 조건; 코드 경로에서 키 불필요 | 연결 코드 존재와 실제 화면 호출 여부 구분. 무료 플랜의 표시·귀속 조건 확인 |
| Anthropic Claude API | 이용자가 선택한 AI 해설 | 계산 결과, 질문, 모델명, 인증 헤더. 알려진 계좌·잔액·키 필드명은 제외 | 자유 입력 질문의 개인정보 자동 제거는 보장하지 않음. 수신 법인·국가·보존·모델 학습 사용·하위처리자·삭제 방법은 계약으로 확인 |
| Cloudflare — 운영자가 지정한 호스팅 업체 | 대한민국에서 서비스를 운영할 예정이라는 사용자 제공 정보. 실제 연결 구조는 별도 확인 | Workers·Pages·R2 등 제품, 계약 법인, 원본 서버, 처리 항목·보유기간·국가 미확정 | CDN·엣지·로그·백업·하위처리자와 국외 접근을 조사. 대한민국 운영을 모든 자료의 국내 보관으로 해석하지 않음 |
| 기타 CDN·메일·결제·오류 수집 | 실제 운영 구성을 아직 확정하지 못함 | 서비스가 추가될 경우 별도 입력 | 저장소에서 회원·결제·광고메일·추적 SDK 흐름을 확인하지 못했어도 배포 인프라가 없다고 단정하지 않음 |

### 직접 의존성 인벤토리

| 분류 | 선언된 패키지 | 운영 점검 기준 |
|---|---|---|
| 웹·UI | `flet[all]==0.85.2`, `fastapi==0.141.1`, `starlette==1.6.0` | 실제 설치되는 런타임·전이 의존성·쿠키·정적 자원 요청·서버 로그 조사 |
| 네이티브 UI | 선택 의존성 `PyQt6==6.12.0` | 선택한 배포 방식의 PyQt·Qt 라이선스와 의무 확인. 소스 공개·상업 라이선스 필요 여부를 설치 가능성으로 판단하지 않음 |
| HTTP·설정 | `requests>=2.31`, `python-dotenv>=1.0`, `pyyaml>=6.0`, Windows용 `tzdata>=2024.1` | TLS 검증, URL 내 키, 환경파일 보호, 파서 사용 및 전이 의존성 확인 |
| 수치·도표 | `numpy>=1.26`, `pandas>=2.1`, `scipy>=1.11`, `statsmodels>=0.14.2`, `matplotlib>=3.8` | 라이선스·귀속, 공급망·취약점 및 실제 로드 버전 기록. `statsmodels`는 `pyproject.toml` 선언에 존재 |
| 금융 SDK | `gs-quant>=1.0`, `yfinance>=0.2`, `pandas-datareader>=0.10` | 패키지 라이선스와 원격 서비스 약관을 별도 확인 |
| 개발 전용 | `exchange_calendars>=4.13`, `reportlab>=4.0`, `pypdf>=4.0`, `pypdfium2>=4.0` | `requirements-dev.txt` 선언. 문서 생성·달력 작업 환경과 최종 배포물 포함 여부 확인 |
| 빌드 | `setuptools>=68` | 빌드 시점 버전·출처·생성 아티팩트 해시 기록 |

이는 선언 기준 목록이다. 하한 버전은 실제 설치 버전이 아니므로 릴리스 환경에서 고정된 해결 결과·패키지 해시·전이 의존성 목록을 별도 보관한다. 현재 SBOM·취약점 스캔이 완료되었다고 표시하지 않는다.

새 SDK나 API를 추가하는 담당자는 목적, 최소 전송 필드, 기본 활성화 여부, 이용자 선택, 계약과 종료 시 삭제 방법을 변경 PR에 기록한다. 단순 시세 조회에서도 개인 API 키·검색 패턴과 IP가 결합될 수 있다. 개인정보 처리위탁·제3자 제공·국외 이전 중 어느 유형인지는 실제 계약과 데이터 흐름에 따라 정하고, 1번 개인정보처리방침 및 6번 동의 양식과 일치시킨다. 모든 연결을 일률적으로 ‘위탁’ 또는 ‘제3자 제공’으로 선언하지 않는다.

검증되지 않은 데이터의 상업 표시·배포를 승인 처리하지 않는다. 승인 단위는 서비스 이름만이 아니라 데이터셋, 사용 지역, 사용자 수, 표시·파생·다운로드·AI 전송·재배포 방식이다. 개인 키를 고객 다수에게 공유하는 운영도 별도 허용 근거가 있어야 한다.

## 양식

### F08-01 제공자·SDK 신규 도입 및 변경 검토서

| 필드 | 기입 내용 |
|---|---|
| 검토 ID / 코드 버전 / 담당·검토일 | {{third_party.review_id}} / {{release.commit}} / {{third_party.owner}} / {{third_party.reviewed_at}} |
| 서비스 법인·패키지 / 실제 버전·해시 | {{third_party.legal_entity}} / {{third_party.package_version_hash}} |
| 기능 / 호출 파일·함수 / 기본 활성화 | {{third_party.purpose}} / {{third_party.callsite}} / {{third_party.default_state}} |
| 요청 목적지·프로토콜 / 응답 데이터 | {{third_party.endpoints}} / {{third_party.response_fields}} |
| 전송 필드 / 인증정보 전달 방식 | {{third_party.request_fields}} / {{third_party.authentication}} |
| 접속 주체 / 수탁·제공 관계 / 계약 근거 | {{third_party.request_origin}} / {{third_party.processing_role}} / {{third_party.contract_ref}} |
| 이전받는 자·국가·시기·방법·연락처 | {{third_party.transfer_details}} |
| 목적·보유기간·재이전·학습 이용 / 삭제 | {{third_party.retention_training_deletion}} |
| 이용자 고지·법적 근거 / 거부 결과·대체 기능 | {{third_party.notice_basis}} / {{third_party.refusal_alternative}} |
| 오픈소스 라이선스·의무·고지 파일 | {{third_party.oss_license_evidence}} |
| 상업 표시·파생·다운로드·AI 전송·재배포 허락 | {{third_party.data_rights_evidence}} |
| 비용·쿼터·장애 대안·계약 종료 | {{third_party.cost_and_exit}} |
| 보안·쿠키·로그·전이 의존성 시험 | {{third_party.test_evidence}} |
| 판정 / 미확정 사항 / 승인 범위·만료일 | {{third_party.decision}} / {{third_party.open_items}} / {{third_party.approved_scope_expiry}} |

판정은 `NOT_VERIFIED`, `CHANGES_REQUIRED`, `APPROVED_FOR_SCOPE`, `REJECTED` 중 하나로 기록한다. 빈 칸·추정·단순 가입 화면은 허락 증거를 대신하지 않는다. 계약 원문·연락처·보안 자료는 접근 제한 저장소에 보관하고 Git에는 문서 식별자와 비식별 판정만 남긴다.

### F08-02 릴리스 재고 확인표

- 릴리스: {{release.commit}} / 배포형태: {{deployment.mode}} / 대상국가: {{deployment.jurisdictions}}
- 직접·전이 패키지 목록과 해시 증거: {{third_party.sbom_evidence}}
- 실제 네트워크 목적지·쿠키·스토리지 조사 증거: {{third_party.runtime_evidence}}
- 신규·삭제·버전 변경·요청 필드 변경: {{third_party.change_summary}}
- 미검증 권리와 비활성화한 범위: {{third_party.unverified_scope}}
- 방침·동의·가격표·삭제 절차에 반영한 문서 버전: {{third_party.linked_policy_versions}}
- 검토자·승인자·승인일: {{third_party.reviewer_approval}}

## 검증과 변경 시 재검토

| 검사 ID | 검증 방법 | 수용 기준 |
|---|---|---|
| C08-01 | 배포 환경의 패키지 목록과 선언 파일·SBOM 대조 | 직접·전이 의존성이 누락되지 않고 실제 버전·출처·귀속 증거가 있음 |
| C08-02 | 가짜 인증값·합성 입력으로 각 호출 전송 캡처 | 목적지·필드·권한이 검토서와 일치. 실제 키·사용자 정보가 시험 보고서에 없음 |
| C08-03 | AI에 중첩 `account`, `balance`, `holding`, `secret`, `api_key`, `token` 필드 삽입 | 전송 payload에서 해당 구조 필드 제외. 자유 텍스트 제거까지 통과한 것으로 기록하지 않음 |
| C08-04 | 네이티브 AI 미동의와 미리보기 변경 / Flet AI 동작 확인 | 네이티브 미동의 전송 0건. Flet의 체크박스 미구현은 미해결로 기록하고 양쪽 구현을 동일하다고 표시하지 않음 |
| C08-05 | 네이티브 계좌조회 기본값과 Flet Crypto Refresh 확인 | 네이티브 OFF에서 계좌 요청 0건. Flet의 키 설정 시 조회를 방침·선택 설계와 대조하여 기록 |
| C08-06 | 합성 키로 예외·재시도·프록시 로그 확인 | 키·Bearer 토큰·계좌 원문을 로그나 Git에 남기지 않음. 토큰 파일 저장 사실과 접근 제어를 별도 확인 |
| C08-07 | 제공자별 사용권·이전·보존 근거 대조 | 허락 범위가 실제 상업 서비스와 일치. 미확정이면 해당 범위를 승인 처리하지 않음 |

의존성 선언·잠금 파일, 목적지 URL, 인증권한, 전송 필드, 호출 기본값, 호스팅·SDK 버전·계약·과금·제공자 하위처리자 변경 시 재검토한다. 정적 점검 결과만으로 실제 요청·라이선스·국외 이전 적법성을 자동 승인하지 않는다.

## 근거

- 구현: [`pyproject.toml`](../../pyproject.toml), [`requirements.txt`](../../requirements.txt), [`requirements-dev.txt`](../../requirements-dev.txt).
- 인증·설정: [`config.py`](../../config.py), [`KISClient`](../../data/krx/kis_client.py) 146–184행, [`OpenDARTClient`](../../data/krx/opendart_client.py) 44·74–79행, [`KRXMarketClient`](../../data/krx/krx_market_client.py) 81–129행.
- API와 SDK: [`crypto_client.py`](../../data/crypto/crypto_client.py) 51–54·308–326행, [`kis_markets.py`](../../data/kis_markets.py) 47·664행, [`gsq.py`](../../core/quant/gsq.py) 70–85행, [`ficc/data.py`](../../core/ficc/data.py) 163–200행, [`quant/history.py`](../../core/quant/history.py) 123–137행.
- AI: [`ai_payload.py`](../../core/research/ai_payload.py), [`quant/insights.py`](../../core/quant/insights.py) 300–320행, [`ui/ai_panel.py`](../../ui/ai_panel.py) 35–77행, [`commentary.py`](../../quantgen_desktop/commentary.py) 49–91행.
- 공식 확인 창구: [개인정보 보호법](https://www.law.go.kr/법령/개인정보보호법), [FRED 이용 조건](https://fred.stlouisfed.org/legal/), [KIS 개발자센터](https://apiportal.koreainvestment.com/), [OpenDART](https://opendart.fss.or.kr/), [KRX 정보데이터시스템](https://data.krx.co.kr/), [Anthropic 개인정보 안내](https://www.anthropic.com/legal/privacy), [Qt 라이선스 안내](https://www.qt.io/licensing/), [PyQt 라이선스 안내](https://www.riverbankcomputing.com/commercial/license-faq).
- 법령·외부 계약의 최신 시행·계약 범위 확인 기록은 [출처 대장](SOURCES.md)에 남긴다. 위 링크는 현재 계약 또는 허락을 획득했다는 증거가 아니다.
