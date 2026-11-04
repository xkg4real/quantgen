# 08. 외부 SDK·데이터 제공자 점검대장

- 문서 ID: QG-C08
- 버전: 1.5
- 기준일: 2026-11-04
- 상태: review-required
- 관리 주체: (주)넥스트제너레이션
- 문의: {{operator.support_email}}

## 적용 범위와 현재 상태

사진의 8번 ‘외부 SDK를 점검’에 대응한다. QUANTGEN의 직접 의존성, 외부 API, 인증정보, 제공 데이터의 이용권을 함께 관리한다. 패키지의 오픈소스 라이선스와 해당 패키지가 접속하는 서비스의 데이터·상업 이용 계약은 서로 다른 검토 대상이다.

현재 브라우저 앱은 Flet, 선택 데스크톱 앱은 PyQt6를 사용한다. 시장 데이터와 선택 AI 해설은 외부 요청을 수행한다. 제공자가 받는 요청에는 아래 명시한 필드 외에 접속 IP·요청 시각·HTTP 헤더 등 통신 메타데이터가 포함될 수 있다. 설치형에서는 이용자 기기가, 서버형에서는 운영 서버가 요청의 출발점이므로 실제 배포 구조를 확정해야 한다. 키가 없다는 사실은 개인정보 처리·쿠키·상업 이용 제한이 없다는 뜻이 아니다.

아래는 코드에서 확인한 목록이며, 실제 배포 시 설치되는 전이 의존성이나 호스팅 사업자 전체를 인증한 목록은 아니다. 저장소에서 제공자별 계약, 국외 이전의 구체적 국가·보유기간, 상업 재배포 허락을 일괄 확인하지 못했다. 현재 판정은 `NOT_VERIFIED`이며 ‘무료 API이므로 상업 이용 가능’으로 바꾸지 않는다.

### 2026-10-31 앱 UI 변경 검토

Babel 지역 형식 의존성과 출처·해시가 고정된 과거 환율 자료를 추가했습니다. Babel의 로컬 포맷팅은 번역 API 호출이 아닙니다. 교육 예제 열람은 동봉 파일을 읽고 Signals는 기존에 읽은 시계열을 사용합니다. 실제 시장 API의 기존 요청·인증·계약 의무는 유지합니다.

검토 범위와 코드 근거는 [코드 사실 기록](FACTS.md)의 앱 UI 변경 절을 참조합니다. 소스·문서의 정합성 검토이며 상태는 `review-required`를 유지합니다.

### 2026-11-02 KIS 전송·의존성 추가

기존 OAuth Bearer 인증·시세 GET에 REST 시세 경로 6개와 `POST client.base_url + /oauth2/Approval`(기본 REST 주소 HTTPS), 시세 WebSocket 구독/해제를 추가했습니다. 시세 GET 허용목록과 별도 승인 발급 POST가 있으므로 “모든 KIS 요청은 시세 GET뿐”이라고 설명하지 않습니다. 앱 키·시크릿은 승인키 발급에 사용하며 브라우저로 내보내지 않습니다. 승인키·선택 종목/TR은 `ws://ops.koreainvestment.com:21000`(실전)/`:31000`(모의)으로 전송됩니다. 계좌·주문 통보 TR은 구독하지 않습니다. 메모리 캐시의 23시간 재사용 기준은 즉시 파기·전송 암호화·다중 사용자 분리의 인증이 아닙니다.

`websockets>=15,<17`이 새 필수 의존성입니다. 통합 검토의 지정 개발 인터프리터는 16.0/BSD-3-Clause를 확인했고 PR #57은 별도 환경에서 당시 16.1.1/BSD-3-Clause를 확인했다고 기록합니다. 두 기록은 각각의 환경·시점에 한정하며 현재 전체 설치 버전이 같다는 뜻이 아닙니다. 현재 별도 환경에서 발견된 17.3은 선언 범위 밖이므로 이 통합의 의존성 충족 증거로 사용하지 않습니다. [권리대장](19-licenses.md)에서 라이선스 원문·실제 배포 버전/고지 검증을 구분합니다. 실제 전송 보호·로그·계약·제공자 국가·상업 시세 재배포권은 미검증이며 `NOT_VERIFIED`를 유지합니다. [정확한 처리·보관 범위](FACTS.md#kis-market-integration-2026-11-02)를 참조합니다.

이 절은 양쪽 소스·문서 검토를 통합한 사실 기록이며 `review-required`와 운영 증빙의 미확정 상태를 유지합니다. 법률 검토·공개 승인·실제 배포 검증이 아닙니다.

### 2026-11-02 Home 시세·Q-SCORE 후속 검토

네이티브 Home은 기존 FRED/yfinance 일별 6계열을 유지하고 KIS 국내주식 6개 REST 시세를 조회합니다. 기본 자동 갱신 시 키가 있으면 이 REST 요청이 실행될 수 있습니다. 별도의 실시간 목록 연결은 KIS 수정 일별 이력을 먼저 읽고 한 소켓에 목록 종목별 시세 구독을 추가합니다. 별도 국내주식 차트도 명시적 조회 이후 점수용 수정 일별 이력을 같은 KIS 제공자에서 추가 조회합니다. 계좌·주문 endpoint나 새 AI 제공자는 추가하지 않으며, 조회·이력·구독 시점과 종목·기간·인증 항목을 실제 배포 대장에 구분합니다.

Q-SCORE 계산은 이미 사용하는 NumPy와 QUANTGEN 기술신호·위험 계산을 재사용합니다. 점수 계산 자체에는 네트워크·파일 저장·새 패키지가 없습니다. 제공자의 API 호출 제한, 동시 구독 한도, 공개 표시·상업 이용·파생값 전달 권리와 기존 승인키의 프로토콜·보관 한계는 여전히 별도 검토 대상입니다. 6종목을 한 소켓으로 구독할 수 있다는 구현이 계약 또는 모든 계정에서의 실제 수신을 입증하지 않습니다.

소스·문서 정합성 검토이며 기존 `review-required`와 공개 준비 `BLOCKED`를 유지합니다. 법률 의견·공개 승인·실제 계정 연결·Windows 수동 검증이 아닙니다.

### 2026-11-02 종목 정보·글꼴 확장 후속

PER·EPS·업종·상장주수는 이미 호출하는 KIS `inquire-price` 응답의 `per`·`eps`·`bstp_kor_isnm`·`lstn_stcn`을 재사용합니다. [공식 고정 버전 필드 목록](https://github.com/koreainvestment/open-trading-api/blob/3a9be59a3ed8745720dc3aa9d584bdf3b7830362/examples_llm/domestic_stock/inquire_price/chk_inquire_price.py)은 이름을 확인하는 근거이며 기간·희석·회계기준·원시 시가총액 단위나 상업 표시권의 근거로 확대하지 않습니다. 새 공급자·HTTP 호출·원격 번역·외부 AI 요청은 추가하지 않습니다.

새 로컬 글꼴 자산은 [19번 권리 대장](19-licenses.md)에 출처·서브셋/이름 변경·OFL을 기록합니다. 폰트 제작 도구는 빌드 용도이며 런타임 폰트 다운로드나 사용자 시스템 글꼴 설치를 추가하지 않습니다. Qt의 실제 굵기 등록과 웹·AWS 적용 상태는 구분합니다.

소스·문서 정합성 검토이며 `review-required`와 공개 준비 `BLOCKED`를 유지합니다. [최종 범위와 검증 기록](../product/HOME_COMPACT_REVIEW_20261102.md)을 참조합니다.

### 2026-11-03 시장 자산별 탭·공급사 자동 선택

시장 화면의 차트는 KIS를 먼저 조회하고, KIS 키가 없거나 조회가 실패하거나 쓸 수 없는 자료를 돌려주면 국내주식(`.KS`, `.KQ`)과 미국·홍콩·일본·중국 주식의 일·주·월봉에 한해 Yahoo Finance(yfinance)에 같은 시점에 요청합니다([자동 선택](../../core/market/routing.py)). 전송 내용은 기존 인벤토리와 같은 티커·주기·기간이며 계좌·키·사용자 입력 외 정보는 보내지 않습니다. 대체 응답은 출처를 “Yahoo Finance”로 표시하고 KIS 실시간 체결·Q-SCORE에 쓰지 않으며 5초 반복 조회도 하지 않습니다. 선물·옵션·채권·분봉·틱봉은 대체 공급사가 없습니다. 분석 도구(금리·외환·매크로 등)는 기존 자동 경로를 그대로 쓰고 선택 상자만 숨깁니다. Yahoo 표시 권리는 기존 [이용 조건 검토](../product/MARKET_DISPLAY_RIGHTS_2026-10-31.md)의 `rights_replace` 상태 그대로이며 이 변경이 상업 표시 권리를 확정하지 않습니다.

### 2026-11-03 시장 지표 차트 4개

시장 화면의 시장지표 표를 지표 차트 4개(코스피, S&P 500, 원/달러 환율, 미국 10년 국채금리)로 바꿨습니다([보드](../../core/research/market_board.py)). 코스피·원/달러는 KIS 지수·환율 일별 시세를 먼저, S&P 500은 KIS 해외지수를 먼저 조회하고, 응답하지 못하면 Yahoo Finance(`^KS11`, `^GSPC`, `KRW=X`)에 요청합니다. 원/달러는 Yahoo가 실패할 때만 FRED `DEXKOUS`(주간 공표 지연)를, 미국 10년은 FRED `DGS10`을 씁니다. 전송 내용은 지수·환율·금리 코드와 기간뿐이며 개별 종목·계좌·사용자 입력은 보내지 않습니다. 화면이 보일 때만 갱신하며(KIS 3분, 지연 공급자 15분, 실패 시 1·2·5·15분 간격으로 재시도) 자동 갱신을 끈 창에서는 새로고침 버튼으로만 조회합니다. 표시 권리는 기존 검토 상태 그대로입니다.

### 2026-11-04 시장 개편: 종목 마스터·관심종목 카드·한 종목 화면

- **KIS 종목 마스터:** `kospi_code.mst.zip`, `kosdaq_code.mst.zip`을 기존 KIS 마스터 호스트 `https://new.real.download.dws.co.kr/common/master/`에서 받습니다([마스터](../../data/kis_markets.py) `_MASTERS`, `load_master`). 앱 키·토큰·계좌 없이 파일 이름만 요청하며 호스트는 IP 주소 등 통신 정보를 받습니다. 자동 갱신이 켜진 창에서 종목 검색 칸에 처음 포커스가 갈 때 백그라운드로 받습니다. 성공하면 같은 실행 중 다시 받지 않고, 실패하면 10분이 지난 뒤 다음 포커스에서 다시 시도합니다. 내용은 프로세스 메모리에만 두고 파일로 쓰지 않습니다. 화면의 종목 이름은 KIS/KRX 자료이며 표시 권리는 [권리 목록](../../core/research/display_rights.json)의 `kis_krx` `rights_conditional` 그대로입니다. 고정폭 파일 형식은 미검증입니다.
- **관심종목 카드:** 카드마다 `ChartRequest(종목, "1d", 120, adjusted=True)`를 KIS에 먼저 요청하고, KIS가 응답하지 못하면 주식은 Yahoo Finance(yfinance)에 요청합니다([자동 선택](../../core/market/routing.py) `default_chart_router`). KIS 일별 조회는 현재가도 함께 읽습니다. 카드는 자체 `MarketDataService`를 씁니다. 자동 갱신이 켜진 창에서 시장 화면이 보일 때만 조회합니다(출처가 `KIS`로 판정된 카드 3분, 그 밖 15분, 실패 시 1·2·5·15분. 실제 KIS 일별 응답의 출처 문자열과 이 판정의 차이는 [변경 사실](FACTS.md#markets-watchlist-2026-11-04)의 범위 밖 행 참조). 전송 내용은 종목 코드·주기·기간이며 관심종목 목록 자체는 보내지 않습니다. 같은 종목을 주기적으로 요청하므로 공급자는 요청 기록에서 관심종목을 짐작할 수 있습니다.
- **한 종목 화면:** 일별 이력 260봉(KIS 먼저, 주식은 Yahoo Finance 대체)을 읽고, 국내주식만 KIS `inquire-price`, `investor-trade-by-stock-daily`(FHPTJ04160001, 20일), `daily-short-sale`(FHPST04830000, 20일)를 부릅니다([종목 정보](../../core/research/stock_profile.py) `load_profile`). 세 경로 모두 이미 [허용목록](../../config.py)에 있던 것이며, 투자자별 매매와 공매도를 앱 화면에 보이는 것은 이번이 처음입니다. 전송 내용은 종목 코드와 날짜뿐입니다. 이 두 자료도 `kis_krx` 정책을 따르며 `registered_series`에는 넣지 않았습니다. 가격 차트는 기존 차트 경로(조회 뒤 지원 체결 연결)를 그대로 씁니다. 해외주식은 이력만 읽습니다.
- **없어진 요청:** 시장 화면의 지표 차트 4개가 하던 KIS 지수·환율, Yahoo Finance `^KS11`·`^GSPC`·`KRW=X`, FRED `DEXKOUS`·`DGS10` 요청은 더 이상 하지 않습니다. [보드 자료](../../core/research/market_board.py)는 남아 있지만 앱 화면이 부르지 않습니다. Home의 기존 FRED/yfinance 6계열과 KIS 6종목 조회는 그대로입니다.
- **Yahoo 대체 표시:** 카드는 “지연 시세”를 보이고 출처 이름은 tooltip에 둡니다. 차트는 “KIS 대신 Yahoo Finance 자료입니다(지연·수정 전 가격)”를, 종목 정보 섹션은 “Yahoo Finance 일별 종가 (수정 전·지연)”을 보입니다. 대체 자료는 실시간 체결·Q-SCORE에 쓰지 않습니다. 공급자 칸을 없앤 다른 화면에서도 출처는 tooltip과 보고서 내보내기에 남습니다.
- **새 의존성 없음:** 꺾쇠 SVG 8개(`assets/ui/`)는 저장소에서 만든 파일이며 외부 SDK·글꼴·다운로드를 더하지 않았습니다.

실제 KIS 응답(투자자별 매매·공매도 포함)·호출 한도·상업 표시권은 미검증이며 `NOT_VERIFIED`를 유지합니다. [변경 사실](FACTS.md#markets-watchlist-2026-11-04)을 따릅니다.

## 정책 또는 구현 기준

### 외부 서비스 인벤토리

| 서비스·연결 | 기능과 요청 시점 | 전송·수신 항목 및 인증 | 로컬 처리·검토 항목 |
|---|---|---|---|
| Financial Modeling Prep | 시세·가격 이력 조회 | 종목, 조회기간, `FMP_API_KEY`; 키가 쿼리 문자열에 포함됨 | 가격 이력 캐시. 예외·프록시 로그의 키 노출 방지, 계약의 상업 표시·파생지표·재배포 범위 확인 |
| 한국투자증권 KIS | 시세 조회와 OAuth 토큰 발급 | 앱 키·시크릿으로 토큰 발급, 이후 토큰·종목·조회 조건 전송 | `~/.nextgen/kis_token.json`에 토큰 저장. 읽기 전용 허용목록과 토큰 파일 접근권한·삭제 절차 확인 |
| KIS 실시간 시세 구독 | 사용자가 실시간 연결 선택 시 REST 이력 조회 후 승인 발급·WebSocket 구독 | `/oauth2/Approval`에 앱 키·시크릿, `ws://ops.koreainvestment.com:21000`/`:31000`에 승인키·종목/TR. 가격·거래량·시각 수신 | 비TLS 전송 보호 미검증. 승인키 전역 메모리 23시간 재사용은 삭제 기간이 아님. 계좌/주문 통보 구독 없음. 개인 접근·상업 표시·브라우저 전달권을 구분 |
| KIS 종목 마스터 다운로드 | 종목 식별용 마스터 파일 다운로드. 2026-11-04부터 종목 이름 검색용 KOSPI·KOSDAQ 마스터 포함(자동 갱신이 켜진 창에서 검색 칸 첫 포커스 때) | 요청한 마스터 파일명; 다운로드 호스트 별도, 키 없음 | `new.real.download.dws.co.kr`도 연결 목록에 포함. 내용은 프로세스 메모리에만 둠. 종목 데이터의 배포권 확인 |
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
| 시세 WebSocket 전송 | `websockets>=15,<17` | 지정 개발 환경 16.0/BSD-3-Clause를 확인하고 PR #57의 별도 환경 16.1.1 검토는 당시 기록으로 구분. 현재 별도 환경의 17.3은 선언 범위 밖. 실제 릴리스 버전·고지·로그·프로토콜 별도 검토; `ws://`를 SDK 사용만으로 TLS 보호라 표시하지 않음 |
| 지역 형식 | `Babel>=2.17,<3` | 로컬 CLDR 숫자·날짜·통화 형식. 확인한 2.18.0 배포본은 BSD-3-Clause와 포함 Unicode-3.0 고지가 있으며 설치물에서도 고지 보존 확인 |
| 수치·도표 | `numpy>=1.26`, `pandas>=2.1`, `scipy>=1.11`, `statsmodels>=0.14.2`, `matplotlib>=3.8` | 라이선스·귀속, 공급망·취약점 및 실제 로드 버전 기록. `statsmodels`는 `pyproject.toml`과 `requirements.txt` 양쪽에 선언 |
| 금융 SDK | `gs-quant>=1.0`, `yfinance>=0.2`, `pandas-datareader>=0.10` | 패키지 라이선스와 원격 서비스 약관을 별도 확인 |
| 개발 전용 | `exchange_calendars>=4.13`, `reportlab>=4.0`, `pypdf>=4.0`, `pypdfium2>=4.0`; 다운로드 문서 생성용 `python-docx==1.2.0` | 앞 네 패키지는 `requirements-dev.txt` 선언. `python-docx`는 문서 패키지 생성 workflow에서 별도 설치. 문서 생성·달력 작업 환경과 전이 의존성·최종 배포물 포함 여부 확인 |
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
