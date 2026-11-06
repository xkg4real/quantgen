# QUANTGEN 정책 작성의 코드 근거

2026-10-31 추가 표시 검토: 네이티브 ETF/Crypto/Derivatives의 AR(1)·펀딩·호가 검사 안내에 로컬 한영 문구를 연결했습니다. 원본 보고서·수치·미실시 상태·외부 진단 원문 및 기존 전송/저장 경로는 보존합니다. `quantgen_desktop/market_diagnostics_language.py`, `market_tools.py`와 `docs/product/MARKET_DIAGNOSTICS_LANGUAGE_2026-10-31.md`가 근거입니다. 실제 Windows 시각/DPI·Flet 동등성·외부 서비스 검증 또는 공개 승인은 별도입니다.

- 기준일: 2026-11-02 한국시간
- 코드 기준: 기존 `5074322` 기능 검토 이력을 보존하고 `853de90`과 PR #57 `cac727e2`의 통합 작업 트리를 대조. 검토 fingerprint는 `source-review.json` 참조 · 이후 main PR60 `1e67b04`/기록 `ead6e67`의 Home 목록·Q-SCORE·7페이지 변경도 통합 대조. M3-N08 `7e8d7442` 재평가 입력 일관성 변경도 보존·대조.
- 범위: 실행 진입점, `core/`, `data/`, `ui/`, `quantgen_desktop/`, 의존성·자산 선언과 관련 문서. 실제 운영 서버·사업자 계약·판매 사이트는 이 소스 검사로 확인되지 않는다.

<a id="kis-market-integration-2026-11-02"></a>
## KIS 시세·차트 통합 — 2026-11-02 소스·문서 정합성

PR #55/#56이 포함된 `69a2559`의 통합 `147afc0`, 후속 `853de90`과 PR #57 `cac727e2`를 통합한 작업 트리를 기준으로 검토했습니다. [20개 문서별 검토표](../product/KIS_SOURCE_DOCUMENT_REVIEW_2026-11-02.md)의 원검토 이력과 현재 통합 검증을 구분합니다. 이전 UI 번역·FX/CMS 설명 수정에 관한 “외부 전송 변화 없음” 기록은 그 변경에 한정하며 아래 KIS 신규 연결에는 적용하지 않습니다. 비밀값·실제 계정·시세 API·고객 자료를 읽거나 요청하지 않은 소스 검토입니다.

| 추가·변경 사실 | 확인된 범위와 남은 확인 |
|---|---|
| 시세 GET | 기존 KIS 허용목록에 국내주식 과거 분봉, 국내파생 분봉, 해외주식 분봉, 해외선물 주봉·월봉·현재가의 6개 시세 경로 추가. [설정](../../config.py), [조회 어댑터](../../data/kis_workspace.py). 계좌·주문 API를 추가하지 않음 |
| 승인키 발급·구독 | [스트림](../../data/kis_stream.py)은 기존 앱 키·시크릿을 `client.base_url + /oauth2/Approval`에 POST함(기본 REST 주소는 HTTPS). 승인키·선택 종목/TR을 `ws://ops.koreainvestment.com:21000`(실전), `:31000`(모의)에 전달. 이 WebSocket은 비TLS이며 전송 보호 검토 완료가 아님. 암호화 계좌·주문 통보는 구독/해독하지 않음 |
| 승인키 메모리 | 프로세스 전역 캐시가 base URL과 인증정보 지문별로 승인키를 23시간 재사용. 기한은 재사용 기준이며 자동 삭제·안전한 메모리 소거·원격 철회가 아님. 정지 시 전역 캐시를 지우지 않으며 기존 Bearer 토큰 평문 JSON 저장과 별개. 새 스트림 모듈의 승인키 파일 저장은 없음 |
| 실행 선택·종료 | 조회·기본 OFF인 5초 REST 반복 조회·별도 WebSocket 연결을 사용자가 선택. 새 연결 전 REST 이력 재조회, 화면 이탈/종료 후 자동 재개 없음. Flet 실시간 중지는 WebSocket 수신만 중지하며 REST 반복 조회는 별도 스위치 OFF로 중지. 이미 전송된 요청의 취소·제공자 로그 삭제·법적 동의 충족은 보장하지 않음. [Qt](../../quantgen_desktop/market_chart.py), [Flet](../../ui/market_chart_page.py) |
| 시세·체결 처리 | 선택 종목/거래소/기간·주기와 OHLCV·시장/수신 시각을 처리. snapshot·체결 대기·해외선물 배율 자료는 실행 프로세스 메모리에서 사용. 기존 마스터 다운로드 경로 `new.real.download.dws.co.kr`도 사용. 화면을 닫는 것이 모든 처리 자료 삭제를 뜻하지 않음 |
| 브라우저 경계 | Flet 서버가 공급자 요청을 수행하고 브라우저에는 차트·시세 표시 데이터 전달. 새 화면이 앱 키·시크릿·승인키를 표시 데이터로 넘기거나 AI 해설로 보내는 경로는 없음. 운영 서버의 이용자 분리·인증정보 접근·통신 보호·제공자 로그/처리 국가·보유기간은 미검증 |
| 지원·단위 | PyQt6/Flet가 공통 OHLCV·지표·SVG를 사용. 국내/해외주식·국내파생 차트와 채권 일봉, master 계산 배율을 확인한 해외선물 일·주·월봉을 제공하고 해외옵션·야간 WebSocket 등은 미지원. 파생 계약별 시세 단위·채권 액면 1만원 기준을 구분. 기존 Upbit 계좌·AI 흐름은 별개 |
| 표시와 주장 | `SUBSCRIBED`와 유효 체결 수신 `LIVE`를 구분. heartbeat는 새 시세 증거가 아님. 미국 무료 Nasdaq 범위와 아시아 15분 지연, 부분 이력·형성 중 봉·미확정 거래량·공백 후 OHLC 불완전·일부 체결의 수신일 추정을 유지. [공개 구현 범위](../product/KIS_MARKET_CHARTS_2026-11-02.md)의 지원 제한을 전체 자산 실시간 보장으로 확대하지 않음 |
| 대체 정보·대비 | 선택 봉 OHLCV 텍스트·Flet 이미지 이름/tooltip·Qt 설명·커서/슬라이더·Qt 방향키를 제공. 시장 SVG는 일반 title만 있고 desc·전체 동등 표는 없으며 지표값은 최신 봉 기준. PR #57 네 범례쌍 검토와 최종 17개 합성 검사의 범위는 [14번](14-contrast.md)에 구분. 실제 전체 상태·보조기술·Windows/브라우저 수용은 미완료 |
| 새 패키지·데이터 권리 | 필수 `websockets>=15,<17`. 현재 지정 개발 환경 16.0의 BSD-3-Clause 원문 확인과 PR #57 당시 별도 환경 16.1.1 확인 기록을 [19번](19-licenses.md)에 구분. 현재 별도 환경의 17.3은 선언 범위 밖이며 이 통합 검증의 의존성 충족 근거로 사용하지 않음. 새 동적 시세는 기존 Home 6개/등록 계열 73개 목록과 범위가 다름. [별도 표시권 검토](../product/MARKET_DISPLAY_RIGHTS_2026-10-31.md#kis-chart-scope-2026-11-02)는 KIS/거래소 상업 표시·재배포·파생지표·서버→브라우저 제공권을 미확정으로 유지 |

정책 01/06/07/08/20의 전송·선택·보관, 12–15의 주장·대체 정보·대비·키보드, 19의 패키지·데이터 권리에 해당 사실을 반영했습니다. PR #57의 02/04/09/10 기능 범위·메모리/쿠키 구분·선택권·추가 시세 비용 안내도 보존했습니다. 밝은 테마 범례의 기존 대비 미달과 후속 합성 검증은 [14번 수정 이력](14-contrast.md)에 구분합니다. 02/03/04/05/09/10/11/16/17/18의 상품·가격/환불·쿠키·후기·사업자·연령·메일 운영 조건은 이 변경으로 해결되지 않습니다. 모든 정책 `review-required`, 공개 준비 `BLOCKED`, 실제 KIS 계정/이용권·Windows/브라우저 수동 수용·AWS 배포·법률 검토의 미완료 상태를 유지합니다. 최종 소스 fingerprint 갱신은 별도 작업이며 이 문단 자체가 배포 승인이나 수동 검증 결과가 아닙니다.

## M3-N08 금리 재평가 파라미터 일관성 — 2026-11-02

`7e8d7442`의 [재평가 API](../../core/ficc/ratesim.py)는 외부에서 전달한 `params`를 무시하지 않고 `sim.params`의 `model`·`kappa`·`theta`·`sigma`·`r0`와 정확히 비교합니다. 불일치는 곡선·경로 재평가 전에 `ValueError`로 거부하고 다른 필드명을 알립니다. 설명용 `note`는 제외하며, 새 계산 설정은 기존 경로의 대체 재평가가 아니라 시뮬레이션 재생성을 요구합니다. [네이티브 서비스](../../core/research/rates_analysis.py)·[Flet](../../ui/rates_page.py)는 Hull–White의 기존 곡선 기반 `r0` 정규화를 반영한 최종 `sim.params`를 전달합니다.

이 변경은 정상 일치 입력의 수치·모형·경로 선택·손실 기준·분위수/CVaR·0 하한·금리 및 현금흐름 규약을 유지합니다. 새 입력 항목·개인정보·키·제공자·요청/AI 전송·동의·저장·삭제·의존성·색상/차트 조작·실제 주문은 추가하지 않습니다. 기존 데이터 조회와 선택적 AI 경로의 미확정 사항을 해결한 변경이 아닙니다. 저장된 과거 보고서·공식 판정·연구 기준·실행 승인·원장·동결/홀드아웃을 변경하지 않습니다.

기존 registry는 `core/**`·`ui/**`와 제품 문서를 폭넓게 연결하므로 01–20의 영향 범위를 대조했습니다. 실질적 보강은 [06 입력·동의](06-form-consent.md)의 기술적 입력 일관성과 법적 동의 구분, [12 주장](12-claims.md)의 거부 조건·검증 범위입니다. 나머지 정책의 개인정보·제공자 계약·권리·요금·운영자·접근성·삭제 미완료 조건은 그대로입니다. [제품 검증 기록](../product/RATES_REVALUATION_PARAMS_2026-11-02.md)은 합성 검사 10개 및 이전 `0169c98` 대비 terminal 배열 12개·PV 배열 24개·요약 값/설명 144개 정확 일치를 보고합니다. 이 문서 검토가 검사를 새로 실행한 기록은 아니며 실제 시장·수동 Windows·전체 접근성·공식 연구 게이트·사이트 배포·법률 검토를 대체하지 않습니다. 20개 `review-required`·공개 준비 `BLOCKED`를 유지하고 최종 source fingerprint 갱신은 별도로 수행합니다.

## 기능과 정보 흐름

| 주제 | 코드에서 확인한 사실 | 근거 |
|---|---|---|
| 서비스 성격 | 최신 README는 상업 출시 의도를 명시한다. 연구·분석·모의거래 기능이며 실거래 주문 경로는 없다고 설명한다. 정부·KOFIA의 승인을 뜻하지 않는다. | [README 시작 부분](../../README.md), 같은 파일 `Regulatory note` |
| 화면 | 브라우저는 Flet, 선택 네이티브 화면은 PyQt6이다. 화면별 구현 수준이 다르다. | [main.py](../../main.py), [pyproject.toml](../../pyproject.toml), [네이티브 구현 범위](../DESKTOP_MIGRATION_2026-10-30.md) |
| 키 입력과 전송 | 키는 환경변수 또는 `.env`에서 읽는다. 설정 화면은 존재 여부를 보여준다. KIS 인증 때 앱 키·시크릿이 발급 서버에 전송된다. | [config.py](../../config.py), [KIS 클라이언트](../../data/krx/kis_client.py) `token` |
| 인증정보 저장 | KIS Bearer 토큰은 기본 `~/.nextgen/kis_token.json`에 평문 JSON으로 저장된다. “인증정보를 전혀 저장하지 않는다”는 고지는 부정확하다. | [KIS 클라이언트](../../data/krx/kis_client.py) `_TOKEN_PATH`, `_store_token` |
| 계좌 조회 | 통화·기준통화·잔액·잠금금액·평균매수가·총수량과 파생 원화평가액을 처리한다. 평가를 위해 보유 통화 종목으로 Upbit 공개 시세를 추가 요청한다. Flet Crypto Refresh는 키가 있으면 기본 잔액 조회를 포함하며 네이티브는 기본 해제다. | [계좌 API](../../data/crypto/crypto_client.py) `balances`, [Flet 흐름](../../core/research/crypto_workflow.py) `analyze`, [네이티브 화면](../../quantgen_desktop/market_tools.py), [시장 분석](../../core/research/market_analysis.py) |
| AI 해설 | Anthropic으로 계산 결과·질문·분석 종류·고정 작성 지시문과 해당 시 값 표기 설명을 전송한다. 구조화된 private 필드 제거는 자유 입력 개인정보의 탐지·삭제를 보장하지 않는다. | [분석 전송](../../core/quant/insights.py) `deep_analysis`, [필드 필터](../../core/research/ai_payload.py), [2026-11-06 범위](#ai-commentary-guards-2026-11-06) |
| AI 선택 | 네이티브는 전송 미리보기·기본 해제 체크박스가 있다. Flet는 안내와 전송 버튼이 있고 동일한 체크박스 절차는 없다. 이 차이만으로 동의의 법적 충족 여부를 단정하지 않는다. | [네이티브 AI](../../quantgen_desktop/commentary.py), [Flet AI](../../ui/ai_panel.py) |
| 로컬 기록 | 규칙 이름·메모·개정 이력, 모의거래 상태·주문·판정이 파일로 저장된다. 이름과 메모에는 이용자가 개인정보를 넣을 수 있다. | [규칙 저장](../../core/rules/store.py), [엔진 저장](../../core/engine/runtime.py) |
| 캐시 | FICC·시세 캐시 등이 로컬에 존재한다. 6시간 TTL은 읽을 때의 신선도 기준이며 보관기간이나 자동 파기 기능이 아니다. | [config.py](../../config.py) `ficc_cache_dir`, [FICC 캐시](../../core/ficc/data.py), [시세 캐시](../../core/quant/history.py) |
| 내보내기 | ResearchRun은 메모리 내 기록과 이용자 선택에 따른 내보내기를 제공한다. 저장한 파일·사용자 백업의 위치는 별도 관리 대상이다. | [연구 실행 기록](../../core/research/runs.py), [내보내기](../../core/research/tool_export.py) |
| 전체 삭제 | 모의투자 초기화는 모의 장부와 판정 기록을 초기화한다. 개인정보 전체 삭제, 외부 제공자 삭제, 백업 삭제의 증거가 아니다. | [엔진](../../core/engine/runtime.py) `reset_practice`, [삭제 절차](20-deletion.md) |
| 미확인 서비스 기능 | 검토한 실행 코드에서 회원가입·서비스 결제·환불 처리·광고메일 발송·연령 확인·일반 개인정보 삭제 요청 흐름을 찾지 못했다. 운영 사이트에 같은 기능이 없다고 단정할 수는 없다. | 실행 코드 검색 범위 위와 같음. [알림 sink](../../core/skills/alerts.py)는 이메일을 unavailable로 취급 |
| 쿠키 | 앱 자체의 쿠키·브라우저 저장 제어 호출을 찾지 못했다. Flet 서버·프록시·배포 인프라·yfinance 세션의 쿠키 여부는 각각 별도 확인이 필요하다. | [의존성](../../pyproject.toml), [쿠키 조사 양식](04-cookie-policy.md) |

## 접근성과 권리

| 주제 | 관찰과 한계 | 근거 |
|---|---|---|
| 차트 | 공통 Flet 차트 이미지는 C형 읽기 영역에 제목·축·범례·한계를 제공한다. 이는 전체 관측값의 동등한 대체 표나 스크린리더 검증이 아니다. 네이티브 차트 접근성 이름은 실제 수치·변화 설명의 충분성을 보장하지 않는다. | [Flet 차트 생성기](../../ui/qcharts.py), [네이티브 차트](../../quantgen_desktop/charts.py) |
| 대비 | 대표 텍스트 색상쌍은 충분한 대비를 보이지만 입력 테두리 등 전체 상태·화면의 적합성은 확인되지 않았다. | [팔레트](../../core/theme.py), [검사 양식](14-contrast.md) |
| 키보드 | 직접 메서드를 호출하는 이동 테스트는 실제 Tab·스크린리더 검증이 아니다. Windows·DPI·포커스 수동 검증이 남아 있다. | [데스크톱 검증](../../tests/desktop_acceptance.py), [남은 검증](../DESKTOP_MIGRATION_2026-10-30.md) |
| 네이티브 차트 표시 | 글꼴 치수에 따른 축 여백·범례/각주 줄바꿈·눈금 밀도로 텍스트 잘림과 겹침을 개선했다. 긴 범례의 전체 이름은 툴팁에 제공한다. 화면 표시 개선이 키보드·스크린리더 동등 접근을 입증하지는 않는다. | [차트 구현](../../quantgen_desktop/charts.py), [합성 렌더링 검사와 남은 실제 환경 검증](../product/UI_RENDERING_2026-10-31.md) |
| 옵션 검사 상태 | 검사를 수행할 표본이 없으면 `NOT_RUN`·null, 한쪽만 검사하면 `PARTIAL`을 표시하고 실제 검사 분모를 함께 전달한다. 이는 quoted-mid 품질 검사이며 실거래 차익 검증이나 공식 연구 판정이 아니다. | [검사 범위 표현](../../core/research/quote_coverage.py), [연구 흐름](../../core/research/derivatives_workflow.py), [변경 근거](../product/QUOTE_COVERAGE_2026-10-31.md) |
| 스왑션 비교 결과 | 주모델 가격·Greeks가 유효해도 보조 모델 간 변동성 환산은 `UNAVAILABLE`일 수 있다. 내부 NaN·내보내기 null 및 이유를 전달하며 0이나 주가격 전체 실패로 표시하지 않는다. | [스왑션 계산](../../core/ficc/swaps.py), [변경 근거](../product/SWAPTION_CONVERSION_2026-10-31.md) |
| 권리 | Noto CJK 파생 폰트와 OFL 고지가 있다. PyQt6 배포 방식, 개별 이미지 제작·허락, 시장데이터 상업 이용·재배포·AI 전송권은 별도 증빙이 필요하다. | [폰트 기록](../../assets/fonts/README.txt), [OFL](../../assets/fonts/OFL.txt), [의존성](../../pyproject.toml), [권리대장](19-licenses.md) |

## 기존 설명의 충돌

### 2026-10-31 Claude 연결 진단 변경 검토

[연결 진단](../../core/research/ai_connection.py)과 [전송 경계](../../core/quant/insights.py)는
인증·권한·모델·크레딧·사용량·통신 실패를 구분하고 원문 오류/예외를 표시하지 않습니다.
키 값·계정 자료를 새로 수집하거나 보관하지 않으며 기존 전송 내용·제공자·명시적 실행을 유지합니다.
Flet와 네이티브의 기존 동의 절차 차이, 자유 질문의 개인정보 필터 한계는 해소된 것으로 표시하지 않습니다.
양 UI의 오류 언어 전환은 요청을 다시 보내지 않고, 실패는 성공 보고서나 연구 통과 판정을 만들지 않습니다.

[Nautilus 역할 설명](../product/NAUTILUS_AND_DATA_SOURCES_2026-10-31.md)은 데이터 공급자와
독립 연구 백테스트 엔진의 범위를 구분합니다. 데이터 권리·연구 main 통합·실제 실행 승인을 부여하지 않습니다.
이번 변경은 결제/환불·쿠키/동의 배너·사업자 정보·아동·광고·후기·삭제·라이선스나 화면 접근성의
미검증 항목을 완료로 바꾸지 않습니다. 로컬 합성/주입 검사는 오류 분류·원문 비노출·언어 표시 범위이며,
실제 Windows/브라우저·스크린리더·사용자 API 연결은 별도입니다. 20개 문서와 소스의 정합성만 검토하며
각 문서의 `review-required` 및 외부 공개의 별도 증거 조건을 유지합니다.

[최신 README](../../README.md)의 상업화 결정은 과거 개인용 배포 정책을 대체한다고 명시한다. [2026-10-29 배포 검토](../product/DISTRIBUTION_REVIEW_2026-10-29.md)는 2026-11-02 정정으로 현행 소유자 결정과 과거 개인용 이력을 구분했다. [데스크톱 이행 문서](../DESKTOP_MIGRATION_2026-10-30.md)와 일부 실행 코드의 개인용 표현·공개 준비 미확정 표시는 별도 검토 대상으로 남아 있다. 이 문서 묶음은 현재 기능과 최신 사업 의도를 구분하고, 과거 개인용 제한을 현행 정책으로 복제하지 않는다. 기존 표시를 일괄 정정하려면 데이터 권리·배포 승인 상태를 함께 확인해야 하며, 문구 삭제만으로 권리가 확보되지는 않는다.

## 이 기록으로 확정할 수 없는 사실

2026-11-02 M4-N6/M4-N11: FX의 기존 수치를 입력 금리 기준 부호 있는 연환산 CIP 차이로 설명하고 5bp 경계의 잡음/실제 조달 프리미엄 단정과 오류 색을 제거했다. 호가 시점·만기·규약 정합성은 미검증이다. CMS의 기존 coupon은 첫 기간 예상 연율 쿠폰으로 명시하고 이후 기간은 기존 일정으로 구분하며 지급 보장으로 해석하지 않는다. Flet의 `implied_basis_note`·`coupon_interpretation` 및 native 보고서·기존 선택적 AI 전달의 해석 정보를 보강했다. 수치·가격·Greeks·계산식·기존 저장 보고서·연구 판정은 유지하며 새 전송처·개인정보/키·동의·저장·삭제 경로는 추가하지 않았다. [FX 근거](../product/FX_CIP_DISCREPANCY_2026-11-02.md)와 [CMS 근거](../product/CMS_COUPON_DISCLOSURE_2026-11-02.md)를 01–20 문서와 대조했다. 합성 검증은 실시장·실제 Windows·접근성·법률·공개 승인 증거가 아니며 `review-required`와 `BLOCKED`는 유지한다.

2026-11-02 M4-N3: ETF 화면에 LETF 비교기준과 연속 연율 금리·보수·배당 가정을 명시 입력하는 시나리오를 추가했다. 이는 사용자 가정이며 관측 금리·검증된 펀드 비용·분배금이 아니다. 기존 영금리 계산은 `ZERO_RATE_REFERENCE`로 별도 보존하며 분산·펀딩·보수·배당 기여도를 구분한다. 입력 가정과 계산 결과는 사용자가 명시적으로 만든 보고서 및 기존 선택적 AI 해설 payload에 포함될 수 있다. 새 키·계좌정보 필드, 외부 목적지, 기본 조회, 주문 경로, 저장 위치·보유기간은 추가하지 않았다. 기존 native 미리보기·미선택 동의와 Flet 전송 버튼의 차이, 자유 입력 개인정보·자료 이용권·국외이전의 미확정 사항은 유지한다. 역사적 연구·공식 판정·원장을 바꾸지 않으며 현 시나리오의 시장 대조 검증은 `NOT_RUN`이다. 합성 수학·표시 검사는 실제 Windows 접근성 또는 시장 대조 증빙이 아니다. [가정 계산](../../core/ficc/letf_assumptions.py), [ETF 흐름](../../core/research/etf_workflow.py), [공시](../../core/research/letf_disclosure.py), [Flet 입력](../../ui/etf_page.py), [Qt 입력](../../quantgen_desktop/market_tools.py), [검증 범위](../product/LETF_ASSUMPTIONS_2026-11-02.md)를 01–20 문서의 현재 조건과 대조했으며 `review-required`와 공개 준비 `BLOCKED`는 유지한다.
2026-11-02 표시 후속: Markets/Risk의 선택한 탭만 크기를 결정하고 실제 폭에 맞춰 긴 해설 높이를 계산하여 좁은 Signals 잘림과 Macro의 과도한 입력 공백을 수정했다. Macro의 코드에 정의된 지표명과 등록된 차트 설명, 종료 실패 안내에 표시 언어를 적용한다. 공급자 원문·수치·원본 보고서·실행/저장/전송 조건은 유지하며 새 정보 수집·추적·자격증명·배포 경로는 없다. 접근성 문서 13–15를 포함한 기존 20개 문서의 조건과 대조했으며 합성 offscreen 결과는 실제 Windows/DPI·키보드·스크린리더 증빙을 대신하지 않는다. 공개 준비 BLOCKED 및 review-required는 유지한다.

2026-11-02 앱 구동·언어 표시 후속: 저장된 locale 타입이 잘못돼도 기존 영어 대체 표시로 설정 화면을 열고 사용자가 지역 설정을 고칠 수 있게 했다. 기존 QSettings 경로와 저장 항목을 유지한다. 네이티브 모델·매크로 해설과 명시한 표 셀은 현재 로컬 생성 문구일 때만 표시 언어를 바꾸며 원문 보고서·식별자·수치·연구 판정은 유지한다. 외부 번역 API, 새 개인정보·키 수집, 새로운 계좌·주문·서비스 과금 경로는 추가하지 않았다. 합성 입력을 사용한 실제 Flet 화면 생성·이동과 설치 wheel의 PyQt6 작업·내보내기 검사를 확대했다([구동 검증 범위](../product/APP_ACCEPTANCE_2026-11-02.md)). 01–20 문서의 기능·전송·저장·공개 조건과 대조했으며 `review-required`, 외부 계약·운영 증빙의 미확정값과 공개 준비 `BLOCKED`는 유지한다. 이 검토는 실제 Windows 실기기·스크린리더·실제 API·Windows 연구 검증이나 법률 의견을 대신하지 않는다.

사업자 등록·신고 증빙과 연락처, 실제 요금·갱신·환불 채널, 호스팅 제품·로그·백업·처리 국가, 실제 보유기간, 제공자별 개인정보 역할·국외이전 국가·계약, 허용 이용 연령, 계약별 데이터 권리, 운영 사이트 접근성은 별도 증빙이 필요하다. 이 파일은 이용자 개인정보나 비밀키를 저장하는 장소가 아니다.

## 운영자가 제공한 정보

2026-10-31 이 작업의 사용자 답변을 반영한다. 사업자등록 증명, 호스팅 계약과 실제 인프라 조사로 확인한 정보와 구분한다.

| 항목 | 제공된 정보와 남은 확인 |
|---|---|
| 사업자명 | (주)넥스트제너레이션 |
| 대표자 | 고건 |
| 주소 | 서울특별시 성북구 안암로 145. 추후 변경 가능하므로 공개·판매 전 현재 주소를 재확인 |
| 사업자등록번호 | 미정 |
| 고객센터·개인정보 연락처 | 미정 |
| 판매 요금·구독 | 사용자가 텍스트로 제공: Research 월 29,000원, Pro 월 59,000원, Team Pilot 월 290,000원. 모두 VAT 포함·월 자동 갱신, Team Pilot 최대 5인. 최초 언급한 22페이지 원문은 열람하지 않았으며 직접 제공한 요금 설명을 근거로 반영 |
| 추가 환불 정책 | 운영자와 협의 필요. 법정 청약철회·하자·환급 권리는 미정으로 유보하거나 축소하지 않음. 상품별 기능·체험·청구일·해지 경로 등은 아직 제공되지 않음 |
| 서비스 운영 국가 | 대한민국 |
| 호스팅 업체 | Cloudflare. Workers·Pages·R2 등 제품, 계약 법인, 원본 서버·로그·백업·국외 접근 및 처리 국가·보유기간은 미확정. 대한민국에서 운영한다는 정보만으로 모든 데이터가 국내에 보관된다고 표시하지 않음 |

## 앱 UI 변경 — 2026-10-31 소스·문서 정합성 검토

PR42와 통합된 메인 변경(PR39/40/43/44, SABR 진단)의 공개 소스 차이를 검토했다. 01–20 문서의 현재 상태·영향 항목을 대조했으며 요금·사업자·계약·보유기간·연령·운영 배포의 미확정값은 그대로 둔다. 이 기록은 법률 검토나 출시 승인, 실제 사이트·스크린리더 검사 결과가 아니다.

| 확인한 변화 | 근거와 범위 |
|---|---|
| 교육 가이드 | [교육 모듈](../../core/education/indicators.py), [차트·ZIP](../../core/education/chart.py). 동봉한 공개 과거 자료를 로컬에서 읽고 계산. 고정 종목·기간을 공유하며 실패 사례는 이후 5개 관측을 이용한 사후 설명. 거래·연구 판정 생성 없음 |
| 자료 출처 | [provenance](../../core/education/samples/usdeur_provenance.json)의 Board H.10/FRED DEXUSEU, 고정 mirror와 해시. 역수·네 자리 반올림된 참조 환율이며 거래소 종가·OHLCV가 아님. CSV·provenance JSON은 기본 소스 fingerprint 대상이 아니므로 별도 데이터 해시/packaging 검사와 연결 |
| 설정 저장 | [앱](../../quantgen_desktop/app.py)의 QSettings QUANTGEN/QUANTGEN에 ui/language·ui/locale. [Flet](../../ui/localization.py)의 언어는 page 세션 상태. 외부 번역 API·광고/분석 추적·새 계좌/인증 요청 추가 없음 |
| 번역 범위 | [다국어 기준](../product/UI_LOCALIZATION.md). 한국어·영어 2개 문구 묶음, Babel 2.18의 714개 지역 형식. 그 외 언어는 영어 대체 표시를 고지. 미번역 모델·외부 서술과 실제 OS 대화상자는 별도 범위 |
| 내보내기 | [현지화 보고서](../../core/research/localized_report.py), [내보내기](../../core/research/tool_export.py). 읽기용 HTML을 별도 추가하고 정규 JSON 식별자·수치·판정은 유지. 교육 ZIP은 HTML·메타데이터·해시 manifest이며 verdict NOT_RUN. 사용자가 저장한 사본은 별도 관리 |
| 시장자료 표시 | [검토 문서](../product/MARKET_DISPLAY_RIGHTS_2026-10-31.md)와 [목록](../../core/research/display_rights.json). Home 6개와 등록 73개, 제공 정책 13개. 조건/대체/추가 확인을 구분하며 publication_authorization·legal_opinion은 false |
| 차트·접근성 | [디자인/검증 범위](../product/INDICATOR_GUIDE_DESIGN.md). SVG title·desc, 날짜 커서·값·해석, 문자·체크·선종류 구분. 배경·큰 화면 좌표·범례 및 지역 축 표시 수정. 기존 차트 전부의 대체 설명·대비나 실제 브라우저/Windows/스크린리더 완료가 아님 |
| 통합한 메인 변경 | [SABR 근거](../product/SABR_DIAGNOSTICS_2026-10-31.md), [FX](../product/FX_LANGUAGE_2026-10-31.md), [캐리](../product/CARRY_LANGUAGE_2026-10-31.md), [금리](../product/RATES_LANGUAGE_2026-10-31.md). 진단은 수렴·잔차·경계·외삽과 독립/차익 검증 NOT_RUN을 구별. 번역은 화면 표현이며 정규 기록과 연구 게이트를 변경하지 않음 |

추가 SDK인 Babel의 BSD-3-Clause·Unicode-3.0 고지는 실제 설치한 2.18.0 배포본에서 확인했으며 [권리대장](19-licenses.md)에 조건을 남겼다. 전체 전이 의존성·시장자료 상업 표시·소개사이트 적용을 승인한 것으로 확대하지 않는다. 공개 소스 검사에서 새 회원가입·서비스 청구·광고메일·연령확인·전체 삭제 서비스가 추가되지 않았음을 확인한 범위만 기록한다.

앱 아이콘 후속: Flet Windows 창의 런타임 icon, Qt 애플리케이션 기본 아이콘 및 Windows 앱 식별자를 기존 QUANTGEN 자산으로 지정했다. 새 이미지·브랜드 권리를 만들거나 기존 사용권 상태를 변경하지 않는다. 외부 전송·지속 사용자 데이터·계약 변화는 없으며 실제 Windows 작업표시줄/고정 바로가기의 수동 검증은 남아 있다.

## C형 차트·테마 후속 검토 — 2026-10-31

기준은 병합된 PR42 d77d996과 C형 작업 트리의 차이입니다. 새 UI 모듈과 색상·배치·설정 저장·글꼴 변경을 01–20의 현재 상태 및 정책·양식과 대조했습니다. 관련 문서 01/04/07/12–15/19/20에 후속 사실을 추가했습니다. 나머지 문서의 가격·사업자·동의·회원가입·환불·연령·메일·운영 증빙에는 이 소스 차이로 변경할 근거가 없습니다. 공개 준비의 BLOCKED 및 문서 review-required를 유지합니다.

- [공통 C형 구성](../product/CHART_C_DESIGN_2026-10-31.md)은 Qt 공통 분석 도구·Quant·Portfolio·Bonds·가이드와 Flet의 28개 차트 생성기를 연결합니다. 기존 팬·선·막대·산점·히트맵 종류, 계산·축 범위·정규 기록을 유지합니다.
- [Qt 설정](../../quantgen_desktop/app.py)에 ui/theme을 추가합니다. Flet는 page.qg_theme 세션 상태입니다. [재도색](../../ui/theme_controller.py)은 캐시된 제어와 [Matplotlib 그림](../../ui/chart_study.py)을 유지하며 데이터 조회·모델 재실행을 호출하지 않습니다.
- 교육 SVG는 등록된 QG Interface 단일 글꼴 가족을 사용합니다. 새 글꼴·이미지·라이선스·앱 배포 의존성은 없습니다. 다크 팔레트 대비를 14번에 갱신했습니다.
- Qt offscreen, Linux 로컬 Chromium/Flet 1600×1100 및 390×1000에서 C형·다크·한글 표시를 확인했습니다. 브라우저 fixture는 실제 계좌·엔진·시장 공급자 조회를 차단한 로컬 검증입니다. 초기 fixture의 자동 Home 갱신은 차단된 공급자 요청을 시도하여 이후 명시적 stub으로 교체했습니다. 실제 서비스 데이터·사이트 배포 검증으로 사용하지 않습니다.
- quantgeneration.com 텍스트는 확인했으나 배포 CSS 토큰은 직접 요청이 403으로 막혀 대조하지 못했습니다. 앱은 기존 아이보리/숲색 브랜드를 적용하며 실제 사이트 토큰·전체 차트 적용은 AWS 작업공간의 확인 항목입니다.

C형 통합 시 main PR46(13d16ae)의 안전한 Claude 오류 분류·한국어 표시와 Nautilus 역할 문서를 함께 보존했습니다. 원문 오류/키 비노출, 명시적 기존 전송, 언어 변경 시 추가 요청 없음의 경계를 대조했으며 이 절 앞의 연결 진단 검토와 일치합니다. 정합성 기준선은 두 변경이 결합된 작업 파일을 대상으로 갱신합니다.

C형 Windows CI 후속: 긴 플랫폼 글꼴의 가로 최소폭 합계가 스크롤 영역을 넓게 고정하여 세로 배치 전환을 막는 현상을 재현했습니다. ChartStudy가 한 열의 최소폭을 보고하도록 수정하고 1200→700→1200 폭에서 가로/세로 전환과 스크롤 영역의 실제 폭을 검사합니다. 데이터·저장·전송·정책 상태 변화는 없습니다.

같은 C형 프레임을 Home의 기존 팬 차트와 요약에도 적용했습니다. 원래 관측·계산·요약을 이동한 배치 변경입니다. 네이티브 회귀검사는 Windows에서 창→스크롤→자식의 크기 이벤트가 처리되도록 실제 Qt 이벤트 루프를 150ms 진행한 뒤 동일한 좁은 배치 조건을 검사합니다. 조건을 완화하거나 Windows 검사를 제외하지 않습니다.

Windows 후속 수치: 1000px 창의 viewport는 764px인데 guide/study는 969px, study 최소 힌트는 966px였습니다. 이벤트 대기만으로는 해결되지 않았습니다. C형 컨테이너의 이미지·텍스트 폭 힌트를 실제 최소폭으로 강제하지 않고, 수동 지정한 최소폭은 유지하도록 수정했습니다. 966px 해설 힌트/764px viewport를 별도 회귀 fixture로 고정합니다. 데이터·저장·전송 및 정책 상태 변화는 없습니다.

최종 가이드 경계 보완: study 최소 힌트를 0으로 줄여도 Windows에서 상위 guide 최소 힌트 969px가 페이지 폭을 유지했습니다. 가이드 컨테이너에도 화면 폭에 맞게 줄어드는 정책을 적용하고 자동 레이아웃 최소폭을 해제합니다. 전체 창 시험에 966px 기본 너비의 줄바꿈 설명을 가이드 바깥쪽 내용으로 추가하여 guide와 설명이 viewport 안에 들어오는지 함께 검사합니다.

### Native Bonds/Portfolio language follow-up

[Bonds/Portfolio result text](../product/BONDS_PORTFOLIO_LANGUAGE_2026-10-31.md)
now has explicit English/Korean display variants, including funding-proxy,
non-positive Sharpe, convergence and differing-cap warnings. Existing computed
numbers, canonical report sections, symbols and unknown provider text stay
intact. This source delta adds no data collection, external translation request,
SDK, persistent setting, billing, marketing or deletion behavior. It changes no
operator facts, price terms, research approvals or data rights. The twenty
policy scopes were compared with this bounded display change; their
`review-required` status and actual Windows/accessibility/website limitations
remain. Source/document consistency is not publication approval.

C형 최종 통합 시 main PR48/49(4c51ab9)의 인계 기록과 채권·포트폴리오 한/영 결과 표현을 보존했습니다. display_variants는 원본 source_text·내보내기·수치·경고를 유지하고 C형의 기존 notes 위젯을 재사용합니다. 이 한정된 소스 차이를 20개 문서와 대조했으며 저장·전송·거래·정책 공개 상태 변화는 없습니다.

C형 병합 직전 통합: main PR50–52(d789691)의 웹 인계 기록과 시장 진단 한영 표시를 함께 보존했습니다. ToolPane의 기존 text(localized=...) 경로를 사용하며 AR(1)·펀딩·호가 수치, 원문 경고와 NOT_RUN·정규 보고서가 유지됩니다. 20개 정책 범위와 대조했고 신규 저장·요청·승인 상태 변화는 없습니다.


### Signals count and forward-convention disclosure — 2026-11-02

The [Signals correction](../product/SIGNALS_TRADE_COUNTS_2026-11-02.md) aligns
executed order-side counts and completed round trips with the existing executable
return/cost window. Final-bar pending transitions do not count as fills. Win rates
remain gross price comparisons, and legacy or unknown statistics versions remain
unverified. Existing equity, return and risk arrays are unchanged. This is product
backtest result labeling/statistics, not an actual trade ledger or research verdict.

The [curve disclosure](../product/FORWARD_CONVENTION_2026-11-02.md) identifies
5y5y as a five-year simple-compounded annualized forward and distinguishes it from
semiannual and forward par swap rates. Descriptor values, curve/bootstrap and swap
engines remain unchanged. Optional AI payloads and user-initiated exports include
additive scope/convention metadata; existing privacy filters and consent paths remain.

All twenty policy scopes were checked for these bounded changes. They introduce no
new provider, collection, storage path, SDK, billing, marketing or deletion behavior.
Existing KIS integration transmission/retention facts remain independently applicable.
Actual Windows/accessibility/provider checks, commercial/data rights, legal/operator
facts and publication approval remain unresolved; review-required/BLOCKED is retained.

## KIS 시세·차트 후속 — 2026-11-02

01–20 문서를 새 시세 소스·화면·의존성과 대조했습니다. [20개 문서별 검토표](../product/KIS_SOURCE_DOCUMENT_REVIEW_2026-11-02.md)는 사실 갱신과 변경 없는 정책을 구분합니다. 이는 fingerprint 갱신에 앞선 소스·문서 정합성 기록이며 `review-required`·공개 준비 `BLOCKED`, 운영자 제공 사실과 미확정 계약·보유기간·연령·호스팅 조건을 유지합니다. 법률 의견·게시 승인·데이터 재배포 허가·실서비스 검증이 아닙니다.

| 주제 | 새로 확인한 사실과 한계 | 근거 |
|---|---|---|
| 시세 범위 | PyQt6/Flet가 공통 OHLCV·지표·SVG를 사용. REST 단일/5초 폴링과 WS 체결을 구분. KIS 계좌·주문 경로 추가 없음; 기존 Upbit 계좌·AI 흐름은 별개 | [기능 범위](../product/KIS_MARKET_CHARTS_2026-11-02.md), [시세 adapter](../../data/kis_workspace.py), [공통 모델](../../core/market/models.py) |
| 지원·단위·지연 | 국내/해외주식·국내파생 차트와 채권 일봉. 해외선물은 master 계산 배율이 확인된 일·주·월봉만. 해외옵션·야간 WS 등 미지원. 미국 무료 Nasdaq 범위/아시아15분 지연, 계약별 시세 단위/채권 액면1만원 기준, 부분 이력·미확인 거래량·잠정 봉을 표시 | 같은 기능 문서, [시세 처리](../../data/kis_workspace.py), [체결 집계](../../core/market/live.py) |
| 인증·프로토콜 | HTTPS `/oauth2/Approval`에 appkey·secretkey를 전송. 승인키·종목·채널을 실전 `ws://ops.koreainvestment.com:21000` / 모의 `:31000` 구독에 사용. 키를 브라우저에 넣지 않는 Python 측 경계이며 해당 WS 구간의 암호화 보장이 아님 | [승인키·연결](../../data/kis_stream.py) `_approval_key`, `subscription_message`, `_run` |
| 보관·중지 | 기존 평문 Bearer 토큰 파일은 유지. 승인키는 서버 주소·인증정보 지문별 프로세스 전역 메모리 캐시이며 23시간은 재사용 기준. 시세 snapshot·대기 tick·종목 master도 메모리. 연결 중지·브라우저 종료가 전역 캐시 삭제·원격 철회를 보장하지 않음 | 같은 파일 `_APPROVAL_CACHE`, `stop`; [master](../../data/kis_markets.py) `load_master`; [삭제 지도](20-deletion.md) |
| 입력·생명주기 | 별도 KIS 차트 화면 최초 진입은 요청 없음. 조회·폴링·체결 연결을 명시적으로 선택하고 화면 이탈/중지 후 자동 재개하지 않음. 새 체결 연결은 REST 새 조회 후 시작. 이 선택은 개인정보·국외이전·광고의 법적 동의를 대체하지 않음. Home 시작 시 조회는 아래 후속 절 참조 | [Flet](../../ui/market_chart_page.py), [Qt](../../quantgen_desktop/market_chart.py), [라우팅](../../main.py) |
| 접근성 | 선택 봉 OHLCV 텍스트·이미지 이름/Qt 설명, 커서·슬라이더/Qt 방향키 제공. 시장 SVG는 일반 title만 있고 desc·전체 동등 표 없음. 지표는 최신 봉 값. 14번의 네 범례 대비 측정만 확인하며 실제 보조기술·전체 상태 검증은 미완료 | [표시](../../core/market/presentation.py), [대체 정보](13-alternative-text.md), [대비](14-contrast.md), [키보드](15-keyboard.md) |
| 의존성·권리 | `websockets>=15,<17` 추가. 이 작업의 프로젝트 가상환경 16.1.1/BSD-3-Clause 메타데이터·LICENSE 원문 확인. 전체 선언 버전·전이 의존성·최종 설치물·KIS 자료 상업 표시/재배포권을 확인한 결과가 아님 | [선언](../../pyproject.toml), [외부 대장](08-third-parties.md), [권리 대장](19-licenses.md) |

가격·환불 기능·사업자 번호/연락처·후기·연령 확인·광고메일·쿠키 동의·전체 삭제 기능을 새로 구현하거나 운영 사실로 확정한 변경은 없습니다. 합성·주입 테스트와 메타데이터 검사는 실제 사용자 키 연결, 웹사이트 반영·배포, 공유 서버의 사용자별 분리·로그/백업 조사 및 금융 서비스 분류 검토를 대신하지 않습니다.

## Home 목록·Q-SCORE·레이아웃 후속 — 2026-11-02

20개 정책의 본문·양식과 새 모듈·변경 소스를 대조했습니다. [20종 검토 기록](../product/HOME_LIVE_QSCORE_REVIEW_20261102.md)은 변경한 14종과 유지한 6종의 이유, 산식과 검증 한계를 구분합니다. 새로운 소스 파일 추가에 따른 전체 정책 재검토이며 공개 준비 `BLOCKED`·각 문서 `review-required`를 유지합니다.

| 주제 | 코드에서 확인한 변경과 한계 | 근거 |
|---|---|---|
| Home 구성 | 기존 시장지표 6개와 고정 국내주식 6개를 목록·상세로 표시. 기술지표 가이드는 독립 왼쪽 메뉴로 이동하며 기존 교육 내용을 재사용. Home의 실시간 차트 바로가기는 기존 KIS 차트에 연결 | [Home](../../quantgen_desktop/app.py), [목록·상세](../../quantgen_desktop/watchlist.py), [기존 가이드](../../quantgen_desktop/indicator_guide.py) |
| 시작 시 요청 | 기존 `auto_refresh=True`의 일별 시장지표 조회에, 키가 준비된 경우 고정 국내주식 6개의 KIS REST 단일 현재가 조회가 추가됨. 최초 Home 자동 갱신에는 점수용 일봉 조회나 WS 연결 없음. 별도 차트 화면의 최초 무요청과 구분 | [snapshot 조회](../../core/research/watchlist.py), [Home 초기화](../../quantgen_desktop/app.py) |
| 명시적 실시간 요청 | Home 실시간 목록 연결에서 종목별 수정 일봉 최대252개를 백그라운드에서 조회한 뒤 단일 KIS WS에 최대6종을 구독. 국내주식 차트를 명시적으로 조회해도 별도 점수용 수정 일봉을 조회. 모두 계좌·잔고·실주문·출금 요청 추가 없음 | [Home 수신 제어](../../quantgen_desktop/watchlist_live.py), [WS](../../data/kis_stream.py), [점수 제어](../../quantgen_desktop/qscore.py) |
| 표시·수신 상태 | 일별 관측, REST snapshot 수신 시각, 실제 거래 시각을 구분. Home은 신선한 실제 체결을 받은 뒤에만 수신 상태를 표시하고 중복·역순·오래된 tick을 거부. 표는200ms마다 변경 행을 모아 표시하며 종목별15초 초과 수신 공백을 stale로 표시. 수신 공백·재연결은 정상 연속 시세로 위장하지 않으며 Home 이탈·중지 후 자동 재개하지 않음 | 위 수신 제어, [Home](../../quantgen_desktop/app.py), [목록](../../quantgen_desktop/watchlist.py) |
| Q-SCORE v0.1 | 기존 기술신호70%·최대낙폭15%·95% CVaR15%의 새 실험적 표시 점수. 최소200개 수정 일봉에서 계산하고 실제 체결을 당일 잠정 종가로 반영. 1초 주기로 최신 tick을 모아 계산하며 원시 차트 봉·정규 연구 게이트를 변경하지 않음. 초기 비중·별 경계의 예측력 검증 없음 | [순수 계산](../../core/research/qscore.py), [점수 제어](../../quantgen_desktop/qscore.py) |
| 처리·저장 경계 | 시세·수정 이력·파생 점수는 프로세스 상태. 새 고객 프로필·연구 원장·점수 파일·외부 AI 요청 없음. Q-SCORE 제어기별 수정 이력 캐시는 최대16종. 중지는 늦은 콜백을 무시하지만 진행 중 REST가 공급자 timeout 전 즉시 종료되거나 기존 Bearer 파일·승인키 캐시가 삭제됨을 보장하지 않음 | 위 계산·제어, [삭제 범위](20-deletion.md) |
| 접근성·검증 | 표·상세 수치, 상태 텍스트, 점수 도움말·Enter/Return 상세 열기 제공. 빈 ToolPane가 세로 공간을 과점유하던 배치 수정. 소스·주입/offscreen 검증과 실제 Windows DPI·키보드·스크린리더·KIS 계정 연결 검증은 별개 | [대체 정보](13-alternative-text.md), [대비](14-contrast.md), [키보드](15-keyboard.md), [검토 기록](../product/HOME_LIVE_QSCORE_REVIEW_20261102.md) |

변경은 네이티브 앱 범위이며 Flet·소개사이트에 같은 Home이나 점수가 배포되었다고 기록하지 않습니다. 기존 외부 SDK·NumPy·브랜드 자산을 재사용했으며, 권리 목록에 항목을 추가하거나 계산식을 설명한 사실만으로 시장자료의 상업 표시·저장·파생·재배포 권리, 금융서비스 분류, 예측 성능 또는 사용자 후기의 근거를 확보한 것으로 취급하지 않습니다.

네이티브 실행 진입점은 `python -m quantgen_desktop`이며 기존 `python main.py`의 Flet과 구분합니다. 빈 차트에서도 사용자가 연결을 누르면 초기 이력 조회 뒤 구독을 시작합니다. `KISUnavailable`에는 `.env`의 KIS 키 설정·재시작·시스템 연결 확인 안내를 제공합니다. 사용자가 업데이트 후 기존 KIS 차트 화면을 표시한 증거와 실제 체결 연결 성공·이번 통합 UI의 전체 Windows 검증은 별개입니다.

## Home compact 후속 — 2026-11-02

기준 `ead6e67`의 compact 변경과 이후 main `f673f37`(PR54/58)·`8b40104`(PR59) 통합 작업 트리를 [20종 검토 기록](../product/HOME_COMPACT_REVIEW_20261102.md)에 대조했습니다. 위 KIS 통합·FX/CMS·Signals/금리 규약·LETF 가정·구동 검토의 기존 범위와 compact 사실을 함께 보존합니다. 앞 절의 Home 별도 차트 바로가기 버튼은 제거하고 종목 상세→기존 차트 경로를 유지합니다. 표 행은64px에서44px로 줄이고 Q-SCORE 소개 버튼은 해당 열 제목 옆에 둡니다. 실제 버튼의 hover·클릭·Enter/Space, 가로 스크롤/헤더 변경에 따른 위치·포커스 처리를 구분합니다. 이 초기 compact 단계는 당시 `assets/fonts/qg-interface.otf`를 재사용했으며, 아래 종목 정보·글꼴 확장 단계의 자산 교체와 구분합니다.

Q-SCORE 한영 소개는 실제 기술신호·위험분석 엔진, 입력 이력·시각·가격 기준 점검, 가격 추세·과거 손실 분석과 체결에 따른 재계산의 의미를 설명합니다. 사용자 화면에서 가중치·환산식·별점 경계 숫자를 생략하지만 순수 계산·표본 요구·결과·실험 상태를 바꾸지 않았습니다. 내부 방법론은 [12번 주장 근거](12-claims.md)와 [기존 산식 기록](../product/HOME_LIVE_QSCORE_REVIEW_20261102.md)에 보존합니다. 코드에 없는 AI 분석·기업가치 판단·모든 엔진 실행·예측력·실현 성과를 추가하지 않습니다.

사용자 Windows 실행에서 `KIS_SETTINGS_FOUND=True`로 설정 발견을 확인한 범위와 실제 KIS 체결 수신·상업 이용권 확인을 구분합니다. Yahoo의 S&P 500·KOSPI·Bitcoin 일별 자료는 KIS 인증과 다른 경로이며 KIS 설정 성공만으로 해당 자료 공급 성공이 입증되지 않습니다. 실제 사용자 환경의 공급자 장애 원인·실시간 연결·새 compact 화면의 DPI/보조기술 검증·웹사이트 배포는 별도입니다. 문서 상태·가격·환불·운영자 사실·공개 준비 상태를 변경하지 않습니다.

[Home 시장 조회](../../core/research/markets.py)는 기존 예외·상태·관측 수를 허용된 `reason_code`로 분류하고 [목록 조회](../../core/research/watchlist.py)가 이를 보존합니다. 예외 텍스트는 최대1500자를 실행 중 분류에만 사용하고 원문·URL·키를 UI 진단으로 반환하거나 새 파일에 저장하지 않습니다. 빈 Yahoo 응답은 `no_observations`이며 원인을 추정하지 않습니다. 새 외부 요청·데이터 공급자·폴백·캐시 경로는 없고, 원래의 KIS/FRED/yfinance 흐름을 유지합니다. 유한한 입력에서도 변화율이 무한대로 계산되면 정상 관측으로 표시하지 않습니다.

### Home 종목 정보·글꼴 확장 — 2026-11-02

PR61의 `5b52e3d` 이후 작업 트리는 같은 Home을 종목·가격·변동·거래량·시가총액·PER·EPS·업종·상세·Q-SCORE의10열로 정리합니다. 출처·관측/체결·앱 수신 시각·연결 상태·안전한 오류 안내는 가격 hover/접근성 설명과 상세 버튼·행 Enter로 여는 본문에서 유지합니다. 표시 열을 줄인 사실을 출처나 오래된 자료 상태의 삭제로 기록하지 않습니다.

KIS 기존 현재가 응답의 `per`·`eps`·`bstp_kor_isnm`·`lstn_stcn`을 읽으며 새 endpoint·HTTP 횟수·개인 항목·계좌·재무 파일·원격 번역·AI 요청을 추가하지 않습니다. 표시 시가총액은 같은 응답의 원화 가격×유효한 양의 정수 상장주수로 계산한 값입니다. 원시 `hts_avls`는 별도 미확인 단위로 남기며 환산하지 않습니다. 같은 KST 날짜에 수신한 상장주수와 유효 체결 가격으로만 산출값을 갱신하고 날짜가 다르면 이전 기준 시각을 보존합니다. 이는 상장주수를 매 tick 검증했다는 뜻이 아닙니다.

재무항목의 REST 수신 시각과 실제 가격 체결 시각은 다릅니다. 공급자가 재무 기준일을 제공하지 않아 `fundamentals_as_of`는 비워 둡니다. PER/EPS의 TTM·회계 범위·EPS 단위·희석 기준을 추정하지 않으며, 유한한0·음수와 없는/잘못된 값을 구분합니다. 업종은 공급자 분류이며 GICS라고 주장하지 않습니다. 준비된 정확한 영어 대응 외에는 `Untranslated`와 상세 원문을 제공하고 미번역을 숨기지 않습니다. 공식 필드 근거와 한계는 [08번](08-third-parties.md), [12번](12-claims.md), [20종 재검토](../product/HOME_COMPACT_REVIEW_20261102.md)에 기록합니다.

현재 QG Interface는 Pretendard1.3.9의 이름을 바꾼 Regular400·Medium500·SemiBold600 서브셋으로 교체합니다. [README](../../assets/fonts/README.txt)에 고정 원본·SHA256·재생성 절차, [OFL](../../assets/fonts/OFL.txt)에 원본 고지, [이전 Noto 고지](../../assets/fonts/OFL-Noto-legacy.txt)에 과거 출처를 구분합니다. 실제3개 파일의 해시·굵기·한글11,172자·tabular numeral 기능을 대조했습니다. 네이티브 Qt는3개 실제 굵기를 등록하고 제목·본문·수치·설명의 위계를 조정합니다. 공유 Regular 파일 교체는 Flet 자산에도 영향을 주지만 실제 Medium/SemiBold 등록·전체 웹사이트 화면 반영·AWS 배포까지 입증하지 않습니다. 런타임 폰트 다운로드·시스템 설치·새 런타임 의존성은 추가하지 않습니다.

이 확장에 따라 정책07/08/09/12/13/14/15/19의 버전을 갱신하고 나머지12종의 계약·권리·개인정보·동의·보유/삭제 범위도 대조합니다. 이전 main PR54/58/59의 절·양식은 보존합니다. 실제 KIS 체결 수신·Windows 전체 화면 수용·시장자료 상업 표시권·본문 번역/사이트 배포·정책 공개 승인은 별도이며20종 `review-required`와 공개 준비 `BLOCKED`를 유지합니다.


<a id="received-chart-update-2026-11-02"></a>
## 네이티브 수신 체결봉·자동 갱신·선택 지표 — 2026-11-02

PR61의 main `707cdc7`을 기준으로 기존 정책과 실제 복구 소스를 대조합니다. 이전 실행 환경의 미게시 수정/테스트 결과는 현재 복구본의 통과 근거로 사용하지 않습니다. [지원·20종 영향 검토](../product/CHART_RECEIVED_BARS_REVIEW_20261102.md)를 유지합니다.

- 네이티브의 명시적 조회/Enter는 이력 또는 빈 수신봉 기준과 선택적 현재가를 조회한 뒤 지원 WS를 구독합니다. 미지원 구독 자산은 지원 이력을 5초 REST로 갱신합니다. 최초 탐색만으로 조회하지 않습니다.
- 활성 입력 변경은450ms 후 새 조회/구독이며 중지·이탈은 예약도 해제합니다. 재연결 구독이 돌아오면 명시적 조회당 한 번 새 기준을 조회하고, 반복 공백에는 수동 조회를 요구합니다. 이미 전송한 요청·기존 캐시/로그 삭제와 다릅니다.
- 1/10/100틱·1/5/10/30초는 실제 수신한 유효 체결만 모읍니다. 누적량으로 중복·역순·누락을 구분하고 같은 초의 별개 봉에 실제 시각과 순서/수신 개수를 보존합니다. 과거/누락 자료·시간 해상도를 만들어내지 않습니다. 최대500봉이며 첫/현재·공백 영향 봉은 불완전할 수 있습니다.
- 다섯 선택 지표는 SMA20·EMA12/26·볼린저20/2σ·RSI14·MACD12/26/9입니다. 기본 SMA 하나, 조회 전/중/실시간 선택 유지, 같은 커서 봉의 OHLCV/지표 읽기와 한영 초보 설명을 제공합니다. 필요 봉 전에는 값을 만들지 않습니다.
- 공통 SVG/읽기 문자열은 한영 언어를 받지만 Flet의 기존9개 주기/지표 선택/별도연결을 새 네이티브 기능과 동일하다고 설명하지 않습니다. 복수 지표 높이 변경 시 `MarketChartSvg`가 상위 레이아웃 무효화/크기 갱신을 다음 이벤트로 전달하여 하단 읽기 겹침을 수정했습니다. 빠른 전체 선택·8개 언어/테마/폭 전환·해제 후 축소 회귀를 확인했으며 공통 CurrentPageTabs는 변경하지 않았습니다.
- 새 endpoint·계좌/주문·개인 프로필·AI 전송·차트 파일 저장·라이선스 변경은 없습니다. 원래 해외 지연·시장센터 범위·모의/자산 제한, 시장자료 권리·정책 미확정과 공개 BLOCKED를 유지합니다.

## 네이티브 가이드 검색·용어 사전 — 2026-11-03

| 항목 | 사실 | 근거 |
| --- | --- | --- |
| 화면 | 네이티브 기술지표 가이드의 A–E 버튼을 검색창·추천 목록(최대 8개)·자주 찾는 항목·차트 표시 칩으로 바꿈. 제목 “Search what you want to explore” / “궁금한 내용을 검색해 보세요”. 고른 항목의 설명을 검색창 바로 아래에 표시. 기술지표는 고르면 기존 공통 표본 차트에도 표시되고 표본 선택 규칙(SMA/EMA 단독 2022, 그 밖 2020)은 그대로 | [Qt 가이드](../../quantgen_desktop/indicator_guide.py) |
| 사전 | 기술지표 5개(기존 검토 문구 재사용)와 시장·위험·금리·파생·외환·QUANTGEN 용어 27개, 한국어·영어. 이름·약어·별칭·한글 초성·정의 순으로 일치 | [검색 사전](../../core/education/glossary.py), [문구](../../core/ui_messages.py) |
| 데이터 처리 | 검색어는 화면 안에서만 로컬로 비교하며 저장·내보내기·네트워크 전송·AI 전송·공급사 조회를 하지 않음. 가이드 보고서 ZIP의 내용과 형식은 바뀌지 않음 | [Qt 가이드](../../quantgen_desktop/indicator_guide.py), [시험](../../tests/desktop_indicator_guide_acceptance.py) |
| 범위 | Flet 가이드와 웹사이트는 바꾸지 않음(2026-11-03 소유자 결정). 실제 Windows IME·Tab 순서·스크린리더는 미검증 | [소유자 결정 기록](../nautilus_bridge/OWNER_RULINGS_LOG.md) |

## 시장 자산별 탭·공급사 자동 선택 — 2026-11-03

> 2026-11-04 대체: 자산별 탭 줄과 안쪽 탭은 [시장 개편](#markets-watchlist-2026-11-04)으로 없어졌습니다. 분석 도구는 “분석 도구” 화면으로 옮겼습니다. 공급사 자동 선택(KIS 먼저, 주식은 Yahoo Finance 대체)과 숨긴 출처 선택 상자는 그대로입니다. 아래 표는 당시 기록입니다.

| 항목 | 사실 | 근거 |
| --- | --- | --- |
| 화면 | 시장 탭을 자산별 9개로 바꾸고 별도 “KIS chart” 탭을 없앰. 차트는 국내증권·해외증권·국내파생상품·해외파생상품·채권 탭 안에서 하나의 차트가 자산에 맞춰 이동. 시장 화면의 데이터 출처·곡선 출처 선택 상자를 숨기고 첫(자동) 값을 유지. Macro v2의 선택은 공급사가 아니라 기록 묶음이라 “기록 묶음”으로 표시 | [앱](../../quantgen_desktop/app.py), [도구 화면](../../quantgen_desktop/tools.py) |
| 공급사 선택 | KIS를 먼저 단독 조회. 실패·미설정·쓸 수 없는 자료(봉 2개 미만, 다른 종목, 순서·가격 오류)면 준비된 대체 공급사에 동시에 요청하고 첫 유효 응답을 표시. 합성 자료는 참여하지 않음. 마감 12초 뒤 늦은 응답은 버림(데몬 스레드) | [자동 선택](../../core/market/routing.py) |
| 대체 범위 | Yahoo Finance: 국내주식(.KS→.KQ), 미국(NAS/NYS/AMS)·홍콩·일본·중국 주식의 일·주·월봉, 수정 전 OHLC, 지연 시세. 선물·옵션·채권·분봉·틱·초봉은 KIS만 | [자동 선택](../../core/market/routing.py) |
| 표시 | 대체 응답은 출처·시도한 공급사(상태·예외 종류·미설정 변수 이름)를 표시하고 KIS 체결 스트림·5초 반복 조회·Q-SCORE에 쓰지 않음 | [차트 화면](../../quantgen_desktop/market_chart.py) |
| 범위 밖 | 시장지표 표(UI-7)·해외 종목명 검색·휠 확대(UI-16)는 후속 PR. 분석 도구의 기존 자동 경로(FRED·yfinance 실패 시 합성 표시)는 바꾸지 않음. Yahoo 표시 권리는 `rights_replace` 그대로 | [이용 조건 검토](../product/MARKET_DISPLAY_RIGHTS_2026-10-31.md) |

## 해외 종목명 검색·휠 확대·출처 두 줄 — 2026-11-03

> 2026-11-04 대체: “출처 표시” 행은 [시장 개편](#markets-watchlist-2026-11-04)으로 바뀌었습니다. 차트는 국내 실시간이 아닐 때 지연 안내 한 줄만 보이고 출처·조회/체결 시각은 가격 tooltip에 둡니다. “종목 검색” 행은 국내·해외 공통 코드·이름 검색으로 넓어졌습니다. “입력 정리”와 “확대” 행은 그대로입니다. 아래 표는 당시 기록입니다.

| 항목 | 사실 | 근거 |
| --- | --- | --- |
| 종목 검색 (2026-11-04 대체) | 해외증권은 이름·코드로 검색(한영·한글 초성). 목록은 앱에 포함된 126개 선별 종목(나스닥·NYSE·NYSE Arca/American·홍콩·도쿄)이며 시장 전체 목록이 아님. 검색은 로컬이며 고른 뒤에만 조회 | [검색](../../core/market/symbols.py), [목록](../../core/market/data/overseas_symbols.json) |
| 입력 정리 | 거래소·조회 봉 수·표시 봉 수 입력 제거. 거래소는 검색 결과로 정해지고, 국내파생상품만 시장 구분 선택을 보임. 기본 240봉 조회·120봉 표시 | [차트 화면](../../quantgen_desktop/market_chart.py) |
| 확대 | 차트 위 휠과 `+`/`-` 키로 표시 봉 수를 20봉~받은 봉 수 사이에서 바꿈. 다시 조회하지 않음 | [차트 화면](../../quantgen_desktop/market_chart.py) |
| 출처 표시 (2026-11-04 대체) | 출처·지연 한 줄, 조회·체결 시각(한국시간) 한 줄, 같은 글자 크기. 긴 공급자 설명은 “데이터 설명” 펼침과 tooltip으로 이동 | [차트 화면](../../quantgen_desktop/market_chart.py) |

## 시장 지표 차트 4개 — 2026-11-03

> 2026-11-04 대체: 지표 차트 4개는 [시장 개편](#markets-watchlist-2026-11-04)의 관심종목 차트로 바뀌었습니다. `quantgen_desktop/market_board.py`와 `tests/desktop_market_board_acceptance.py`는 `2927879`에서 삭제했습니다. [보드 자료](../../core/research/market_board.py)와 그 시험은 남아 있지만 앱 화면은 부르지 않습니다. 아래 표는 당시 기록입니다.

| 항목 | 사실 | 근거 |
| --- | --- | --- |
| 화면 | 시장 화면의 7열 시장지표 표·새로고침 버튼·단위 안내를 지표 선 차트 4개(코스피, S&P 500, 원/달러 환율, 미국 10년 국채금리)로 교체. 개별 종목 없음(종목은 Home 목록·Q-SCORE에 그대로). 넓으면 2×2, 700px 미만이면 한 줄 | 보드 `quantgen_desktop/market_board.py`(2026-11-04 삭제) |
| 공급사 | 카드마다 KIS 먼저(코스피 지수·S&P 500 해외지수·원/달러), 실패·미설정이면 Yahoo·FRED 동시 요청·첫 유효 응답. 미국 10년은 FRED. 합성 자료 없음 | [보드 자료](../../core/research/market_board.py), [자동 선택](../../core/market/routing.py) |
| 갱신 | 시장 화면이 보일 때만, KIS 카드 3분·지연 공급사 15분 간격, 실패 카드는 1·2·5·15분 간격 재시도. 자체 작업 큐라 분석 도구를 막지 않음. 실패한 갱신은 마지막 정상 값을 유지 | 보드 `quantgen_desktop/market_board.py`(2026-11-04 삭제) |
| 표시 | 값·등락(%, 금리는 bp)·선 차트·출처/지연 한 줄·관측일/갱신 시각 한 줄. 7일 넘은 관측은 “오래된 관측” | [카드 차트](../../core/market/presentation.py) |

## 조작 버그 수정(A2) — 2026-11-03

| 항목 | 사실 | 근거 |
| --- | --- | --- |
| 휠 | 선택 상자·숫자 상자는 휠로 포커스를 받지 않음(StrongFocus). 포커스 없는 상자와 탭의 휠은 그 방향으로 움직일 수 있는 가장 가까운 스크롤 영역으로 전달, 없으면 무시. 실제 Windows 휠은 미검증 | [휠 처리](../../quantgen_desktop/wheel_guard.py) |
| 채권 입력 | 금액 칸이 천 단위 구분기호로 표시(1,000,000). 계산 전 구분기호를 제거해 같은 값을 사용 | [채권 화면](../../quantgen_desktop/bonds.py) |
| 입력 잘림 | 분석 도구 입력 영역이 고정 높이 대신 현재 양식만 표시·측정(숨긴 양식은 자리를 차지하지 않음, 폭에 따른 높이 포함). 입력 패널 높이를 선호 폭 기준 크기 힌트로 제한하지 않아, 실제 폭에서 캡션이 더 줄바꿈되는 경우(Windows 글꼴)에도 마지막 줄이 잘리지 않음. Rates·KRX·ETF 잘림 해결. 실제 Windows 화면은 미검증, Windows CI로 확인 | [도구 화면](../../quantgen_desktop/tools.py) |
| 아이콘 | 창·앱 아이콘을 16–256px .ico와 PNG로 구성하고 Windows 앱 ID 설정 결과를 확인. 실제 Windows 작업표시줄 표시는 미검증 | [앱](../../quantgen_desktop/app.py) |
| AI 해설 버튼 | 항상 응답하며 미리보기·동의 단계를 안내. 동의 없이는 전송하지 않고, 동의 후 질문을 고치면 동의가 다시 꺼짐 | [AI 해설](../../quantgen_desktop/commentary.py) |

<a id="markets-watchlist-2026-11-04"></a>
## 시장 개편: 관심종목 차트·한 종목 화면·분석 도구 — 2026-11-04

소유자 요청 원문과 결정 이유는 [제품 기록](../product/MARKETS_WATCHLIST_2026-11-04.md)에 있습니다. 아래는 브랜치 `claude/ui-markets-watchlist-20261104`(코드 기준 `44ba1c7`)의 코드 사실입니다. 네이티브 PyQt6만 바꿨고 Flet 브라우저 화면과 Home 고정 목록은 그대로입니다.

| 항목 | 사실 | 근거 |
| --- | --- | --- |
| 화면 | 시장 화면은 검색 막대 아래에 관심종목 차트 카드 또는 한 종목 화면을 보임. UI-7 지표 차트 4개와 UI-8 자산별 탭 줄은 없음. 카드는 이름·코드·가격·등락·일별 종가 선 차트(120봉)와, 해당할 때만 상태 한 줄. 폭 1060px 이상 3열, 640px 이상 2열, 그 밖 1열. 카드를 누르거나 Enter·Space를 누르면 한 종목 화면. Home 상세의 차트 버튼도 그 종목 화면을 엶 | [시장 화면](../../quantgen_desktop/markets_view.py) `WatchlistGrid`·`WatchCard`·`StockView`, [앱](../../quantgen_desktop/app.py) `make_markets`·`open_stock_chart` |
| 조회 시점 | 자동 갱신이 켜진 창에서 시장 화면이 보일 때만 카드를 조회. 15초마다 차례를 확인하고 KIS 카드는 3분, 그 밖은 15분, 실패한 카드는 1·2·5·15분 뒤 다시 조회. 화면을 떠나면 멈춤. 실패해도 마지막 차트를 두고 “갱신 실패, 마지막 값 표시”. 종목을 열면 차트 조회·지원 체결 연결과 종목 정보 조회를 함께 시작. 자동 갱신이 꺼진 창(시험)은 카드의 새로고침·차트의 조회 버튼을 누르기 전에는 조회하지 않고 종목 마스터도 받지 않음 | markets_view.py `due`·`showEvent`·`show_instrument`, [시험](../../tests/desktop_markets_watchlist_acceptance.py) |
| 관심종목 저장 | QSettings `QUANTGEN/QUANTGEN`의 `markets/watchlist`. 값은 자산 구분·코드·거래소만 담은 JSON 목록이며 최대 20개. 키가 없으면 Home의 국내주식 6개로 시작하고, 이용자가 ☆·★·×로 추가·삭제할 때만 씀. 모두 지우면 빈 목록이 남음. 잘못된 항목은 건너뛰고 다른 코드로 고치지 않음. 이름·가격·조회 결과·검색어는 저장하지 않음 | markets_view.py `WatchlistStore`(107–169행) |
| 종목 검색 | 시장 검색창, Build & Test 종목, 포트폴리오 종목(쉼표 목록), Signals 종목, Strategy Lab 종목, ETF 코드(ETF만), KRX 코드에서 코드나 이름으로 찾음. 국내·해외 주식을 코드·한글 이름·영어 이름·한글 초성으로 찾고 결과는 최대 8개(“이름 코드 · 거래소”). 영어 이름은 Home 6종목과 동봉 해외 126종목에만 있음. KIS 마스터에는 영어 이름이 없어(directory.py 67·164행) 그 밖의 국내 종목은 영어 이름으로 찾지 못하고 영어 화면에서 코드로 보임(76–85행). 모의매매 규칙 편집기의 종목 칸(paper.py 164행)은 검색 없음. 고르면 칸에 코드만 들어가 각 화면의 조회 경로는 그대로. 거래소가 빠진 코드로 다른 종목을 부르지 않도록 시장 검색창 밖의 칸은 해외 종목 중 미국(NAS·NYS·AMS)만 보임(홍콩·도쿄 8종목 제외, markets_view.py `US_EXCHANGES`). 검색은 로컬이고 입력한 글자를 보내지 않음. 시장 검색 막대의 종류 선택(국내 파생·해외 파생·채권)에서는 코드를 직접 입력. 맞는 종목이 없으면 추측하지 않고 안내 | [검색](../../core/market/directory.py) `search`·`resolve`, markets_view.py `SymbolCompleter`·`submit`, app.py `attach_symbol_searches` |
| 종목 목록 내려받기 | 자동 갱신이 켜진 창에서 위 검색 칸 중 하나에 처음 포커스가 가면, KIS 키 없이 `kospi_code.mst.zip`·`kosdaq_code.mst.zip`을 기존 마스터 호스트 `new.real.download.dws.co.kr`에서 백그라운드로 받음. 요청에는 파일 이름만 있음. 원본 줄은 `_MASTER_CACHE`, 분석한 목록은 디렉터리의 메모리 색인에 두고 파일로 쓰지 않음. 성공하면 같은 실행 중 다시 받지 않고, 실패하면 10분이 지난 뒤 다음 포커스에서 다시 시도. 받기 전이나 실패 시 국내는 Home 6종목만 이름으로 찾고 그 밖은 6자리 코드로 엶. 실패하면 시장 화면에 “국내 종목 이름 목록을 불러오지 못했습니다. 국내 종목은 6자리 코드로 검색하세요.”를 보임. 해외는 동봉 126종목뿐. 6자리 숫자가 아닌 국내 단축코드는 건너뜀 | markets_view.py `DirectoryLoader`, directory.py `load_domestic`(465행)·155행, [마스터](../../data/kis_markets.py) `_MASTERS`(48행)·`load_master`(657행) |
| 한 종목 화면 | 머리글(코드·거래소, 이름, 가격, 등락), ☆ 관심종목 추가 / ★ 해제, 공유 가격 차트(주기·지표·체결 갱신은 기존 차트 그대로, 종목 입력칸은 숨김), 종목 정보 섹션. 섹션: 주요 지표(시가·고가·저가·거래량·시가총액(계산값)·PER·EPS·업종·상장 주식 수), 52주 범위, 기간 수익률(1주·1개월·3개월·6개월·1년), 위험 지표(“과거 자료이며 예측이 아님”), 기술적 신호(“매수·매도 추천이 아닙니다”), 기술 지표, 투자자별 순매수(외국인·기관·개인, 최근 5·20거래일), 공매도(최근·20거래일 평균 수량과 비중), 제공되지 않는 정보. 주식이 아닌 종류는 차트만 보이고 “종목 정보는 주식에만 제공합니다” | [종목 정보](../../core/research/stock_profile.py) `sections`, markets_view.py `StockView` |
| 한 종목 화면 자료원 | 일별 이력 `ChartRequest(종목, "1d", 260, adjusted=True)`: KIS 먼저, 주식은 KIS가 응답하지 못하면 Yahoo Finance. 국내주식만 KIS `inquire-price`, `investor-trade-by-stock-daily`(20일), `daily-short-sale`(20일). 셋 다 기존 허용목록 경로이며, 투자자별 매매와 공매도를 앱 화면에 보이는 것은 처음. 해외주식은 이력만. 합성 자료는 쓰지 않음. 오류는 정한 이유 코드와 예외 종류 이름만 보임 | stock_profile.py `load_profile`, app.py `_ProductionProfileLoader`, [허용목록](../../config.py) 91·98·99행 |
| 제공하지 않는 정보 | “제공되지 않는 정보” 섹션에 적음: 뉴스, 애널리스트 의견·목표주가, 배당(기간 수익률은 가격 기준), 호가, 해외 종목 재무 지표. 대체 자료일 때 “실시간 체결: KIS 자료에서만 제공”. 조회하지 못한 섹션은 이유와 함께 같은 섹션에 적음 | stock_profile.py `_ALWAYS_MISSING`·`_unavailable_rows` |
| 공급자·관측일 제거 | 칸·줄로 보이던 공급자·관측일을 없앰: 차트의 출처·시각 두 줄, Home 상세 창의 공급처·관측일 행, 매크로 표의 출처·관측일 열, 외환 캐리 표의 금리 관측일·오래된 관측 열, KRX의 공급자 줄(KIS일 때)과 시세 표의 `source`·`as_of` 행, ETF 시세 표의 `as_of` 행(요청일). 공급자와 시각은 tooltip(카드, 차트 가격, 섹션 행, 매크로 지표 이름, 캐리 금리)에 남음. 시장 카드·공유 가격 차트·종목 정보·Home 상세 창은 보고서 내보내기가 없음. 도구 내보내기는 화면에 넣은 행으로 만들므로(tools.py 226·271행) 매크로·외환 캐리 표의 숨긴 열은 내보내기 표에 그대로 있음. KRX `source`·`as_of`와 ETF `as_of` 행도 화면에서만 숨기므로(market_tools.py `hide_rows`) 내보내기에 남음. KIS로 받은 KRX 결과의 공급자·`as_of`는 화면·tooltip에 없고 내보내기에만 있음. KIS가 아닌 KRX 대체(직전 거래일 종가)는 공급자 줄과 `as_of` 행을 화면에 보임 | [차트](../../quantgen_desktop/market_chart.py), [Home 상세](../../quantgen_desktop/watchlist.py), [매크로](../../quantgen_desktop/macro.py), [외환](../../quantgen_desktop/fx.py), [ETF·KRX](../../quantgen_desktop/market_tools.py) |
| 남은 공급자·날짜 글자 | 이번 변경이 바꾸지 않아 화면 글자로 남은 것: 외환의 “Data sources” 표(Series·Provider·First·Last·Note, 모든 결과)와 차트 축 이름의 기간, 매크로의 “As of {기준일} · {공급자: 개수}” 줄, 금리·채권·구조화 상품·파생상품·ETF·가상자산 결과 머리의 공급자와 날짜, KRX의 실패·KIS 아닌 출처 “Provider:” 줄 | [외환](../../quantgen_desktop/fx.py) 38–39·63·79행, [매크로](../../quantgen_desktop/macro.py) 44–46행, [금리](../../quantgen_desktop/rates.py) 59–60행, [채권](../../quantgen_desktop/bonds.py) 99–100행, [구조화](../../quantgen_desktop/structuring.py) 40행, [도구](../../quantgen_desktop/market_tools.py) 41·104·164·228–229행 |
| 남긴 상태 표시 | 차트: 국내 실시간이 아닐 때 지연 안내 한 줄(예: “15분 지연”, “미국 무료 시세 · 지연 0분”, “지연 시세”), 대체 자료일 때 “KIS 대신 Yahoo Finance 자료입니다(지연·수정 전 가격)”, 상태 줄의 오래된 값·조회 실패. 카드: 출처가 `KIS`·`KIS REST`가 아니면 “지연 시세”(Yahoo 대체도 이 글자뿐이고 Yahoo 이름은 tooltip에만), 마지막 봉이 7일보다 오래되면 “오래된 자료”, “갱신 실패, 마지막 값 표시”. 종목 정보: 섹션 노트의 “Yahoo Finance 일별 종가 (수정 전·지연)”과 “마지막 일봉 …, 오래된 자료”. 외환 캐리 표: 오래된 금리 칸에 ⚠와 날짜 tooltip. Home 상세 창: 오래된 관측의 날짜를 안내문에 적음. 매크로: 합성 자료 줄과 기준일 줄. KRX: 실패이거나 KIS가 아닐 때 공급자 줄 | 같은 파일, markets_view.py `WatchCard.render` |
| 분석 도구 | 시장 탭에 있던 10개 도구(채권·금리·구조화 상품·외환·파생상품·ETF·KRX·가상자산·거시 지표표·매크로 v2)를 새 왼쪽 메뉴 “분석 도구 / Analysis tools”로 옮김. 5열 2행 버튼(Tab·Space로도 선택), 스크롤 탭 없음. 각 도구의 계산·조회·자동 경로·숨긴 출처 선택은 그대로. 매크로 안내문은 “분석 도구의 매크로 v2”를 가리킴 | app.py `TOOL_PANES`·`make_tools`·`show_tool`·`show_market_pane` |
| 글자·좌측 메뉴·선택 상자 | 동봉 QG Interface의 400/500/600 굵기만 씀(700은 거부). 제목 30/600, 소제목 18/600과 3px 강조 막대, 본문 14, 캡션·표 머리 12, 큰 수치 32/600. 패널은 세로 그라데이션과 2px 아래 테두리. 등락은 한국식(상승 빨강·하락 파랑) 알약. 좌측 메뉴 폭은 가장 긴 메뉴 이름으로 정하고 168–208px로 제한(오프스크린 측정 영어 182px, 한국어 176px, 이전 고정 222px). “PERSONAL RESEARCH”와 미리보기 두 줄은 뺐고 미리보기 안내는 System 화면에 있음. 선택 상자·숫자 상자·넘치는 탭 줄의 기본 화살표 상자를 상자 없는 얇은 꺾쇠 SVG로, 스크롤 막대는 화살표 버튼 없이 얇게. 카드의 × 버튼은 상자 없음. SVG 차트 글자는 등록 글꼴 `QG Interface`만 지정하고 12px 이상. 글꼴 파일을 읽지 못하면 Python logging 경고(파일 경로)를 남기며 로그 파일은 만들지 않음 | [글자·스타일](../../quantgen_desktop/typography.py), [꺾쇠](../../assets/ui/chevron-down-light.svg), [SVG](../../core/market/presentation.py), app.py `fit_sidebar`·`load_interface_fonts` |
| 범위 밖·미검증 | Flet 브라우저·웹사이트·Home 고정 종목 목록과 열 구성은 바꾸지 않음(공유 SVG의 글꼴 이름·크기 변경은 Flet 차트에도 적용). Home 표의 변동 색(한국식 상승 빨강·하락 파랑)·열 머리 12/600·종목 코드 알약 12px과 상세 창의 공급처·관측일 행 제거는 이번 변경(watchlist.py 812·815·936행, 540–563행). 종목 검색 목록(QCompleter)은 부모 없는 별도 창이라 주 창 스타일시트가 닿지 않으므로 테마마다 목록에 직접 스타일을 줌(typography.py `popup_stylesheet`, markets_view.py `SymbolCompleter.set_theme`). Windows 모습은 미검증. 웹사이트 변경 기록은 [PR-71.json](../product/ui_website_updates/PR-71.json). 실제 Windows 표시·DPI·글꼴 렌더링, KIS 종목 마스터의 고정폭 형식, 실제 KIS 응답(투자자별 매매·공매도 포함), 마스터 이름의 글꼴 지원(한자 등), 6자리가 아닌 단축코드로 빠지는 종목 수는 미검증. 실제 KIS 일별 응답의 출처 문자열은 `KIS REST`(data/kis_workspace.py:229)이며 카드는 `KIS`·`KIS REST`를 KIS로 판정함(markets_view.py:44). 실제 KIS 응답으로는 미검증. 종목 이름 표시 권리는 `kis_krx` `rights_conditional` 그대로 | [표시권 검토](../product/MARKET_DISPLAY_RIGHTS_2026-10-31.md), [권리 목록](../../core/research/display_rights.json) |

정책 01·04·06·07·08·09·13·14·15·19·20에 해당 사실을 반영했습니다. 02·03·05·10·11·12·16·17·18은 대조했고 거짓이 된 문장이 없어 본문을 바꾸지 않았습니다. 모든 정책의 `review-required`와 공개 준비 `BLOCKED`를 유지합니다. 법률 의견·공개 승인·실제 계정 연결·Windows 수동 검증이 아닙니다.

## Crypto 결측값(§10 NEW-M6-14·15·22) — 2026-11-04

| 항목 | 사실 | 근거 |
| --- | --- | --- |
| 보유 평가 | 원화 시세가 없는 통화는 평가액을 0이 아닌 빈 값으로 두고, 합계는 "부분 합계"로 표시하며 빠진 통화를 밝힘. 수량이 0이면 평가액 0. 평균 매수가에 통화 단위 표시. 빠진 통화를 밝히는 안내도 보유 내역처럼 AI 해설로 보내지 않음 | [Crypto 흐름](../../core/research/crypto_workflow.py) |
| 공개 시세 요청 | 보유 통화 목록을 한 번에 요청하고, Upbit가 목록을 거부하면(HTTP 400·404) 같은 종목을 하나씩 다시 요청. 시간 초과·요청 한도·서버 오류는 종목별로 하나씩 다시 묻지 않고 조회 실패로 표시함. 다만 공용 HTTP 세션은 연결 실패·시간 초과·HTTP 502·503·504일 때 같은 요청을 최대 2번 더 보냄(HTTP 429·500은 한 번만). 보내는 항목(종목 코드)은 같음. 실제 Upbit 응답은 미검증 | [Crypto 흐름](../../core/research/crypto_workflow.py) |
| 무기한 선물 괴리 | 마크·인덱스 가격 중 하나라도 없으면 0%·−100% 대신 "n/a" | [Crypto 공급사](../../data/crypto/crypto_client.py) |
| 김치 프리미엄 z | 관측 91개 미만이거나 변동이 없으면 z를 계산하지 않고 "n/a"·"—"로 표시. 기록이 1년(관측 365개)보다 짧으면 z가 실제로 쓴 관측 수를 Flet 화면·해설·AI 페이로드(`z_window`)에 밝힘. 종가가 없는 날은 −100% 대신 제외 | [Crypto 분석](../../core/crypto/analytics.py) |

## 옵션판 표시(§10 M4-N4·N7·N9) — 2026-11-04

| 항목 | 사실 | 근거 |
| --- | --- | --- |
| 박스 금리 | 인접 행사가(2.5포인트) 박스는 네 다리 모두 양방향 호가일 때만 산출하고, 0.01포인트당 민감도와 매수·매도호가 기준 범위를 함께 보이며 "조달금리 추정치가 아닌 호가 품질 점검"으로 표시 | [옵션 표시](../../core/research/option_disclosure.py) |
| 헤지 손익 | GBM 엔진은 σ_true = σ_h라 기대 평균 손익이 정의상 0. 부호를 색칠하지 않고 "모의 평균"으로 표시. GARCH-t는 기존과 같음 | [파생 흐름](../../core/research/derivatives_workflow.py) |
| MFIV | 스트립의 행사가 범위와 절단으로 인한 하향 편향을 표시. 기존 MFIV 값은 같음 | [Flet 화면](../../ui/derivatives_page.py) |

## 몬테카를로 부트스트랩·ETF 전략 표시(§10 N-M1-02/a·NEW-M6-04·NEW-M6-05) — 2026-11-04

| 항목 | 사실 | 근거 |
| --- | --- | --- |
| 부트스트랩 설명 | 몬테카를로 부트스트랩을 "5거래일 고정 길이 블록의 원형 재표본(블록 길이가 무작위인 정상 부트스트랩이 아님)"으로 Flet 화면·해설·AI 페이로드(`resampling_definition`)·Native 메모·README·모형 설명서 원본에 표시. 변동성 군집은 시차 1-4에서 일부만 남고 시차 5부터 사라지며, 팬 차트는 현재 변동성 수준에서 출발하지 않음. 엔진 함수와 모든 숫자는 같음(모듈 설명문만 수정). 블록 길이를 바꾸는 수학 수정은 소유자 결정 사항. 모형 설명서 PDF는 다시 만들지 않음. ResearchRun 내보내기에는 설명 문장이 없음 | [몬테카를로 표시](../../core/research/mc_disclosure.py), [엔진](../../core/quant/montecarlo.py) |
| ETF 샤프 계산 불가 | 일별 손익이 변하지 않는 전략(현금만 보유, 일부 평탄한 가격)의 샤프비율을 1e16이나 0.00 대신 "n/a"·"계산 불가"·페이로드 null(`sharpe_status`)로 표시. 표준편차(ddof=1)가 1e-10 × max(1, 최대 절댓값) 이하이면 변동 없음으로 봄. 정의되는 샤프비율과 다른 숫자는 같음 | [전략 표시](../../core/research/sleeve_disclosure.py), [ETF 흐름](../../core/research/etf_workflow.py) |
| ETF 계산 관례 | 추세 전환의 첫 210개 일별 수익률은 현금 준비 구간, 변동성 목표는 첫 23개. 현금은 연 3% 고정 가정. 샤프비율은 준비 구간을 포함한 전체 기간 기준이며 현금 초과 수익 기준이 아님. 매수 후 보유는 준비 구간·현금·비용이 없음. 변동성 목표 비중은 매 거래일 비용 없이 재조정(K-e). 연구 판정은 계열 카드. Flet 안내·툴팁, 해설(영·한), Native 문장과 내보내기 절(`sleeve_conventions`)에 표시. 한국어 내보내기 HTML에서는 기존 공개 문구처럼 영어로 남음 | [Flet 화면](../../ui/etf_page.py), [Native](../../quantgen_desktop/market_tools.py) |

<a id="ai-commentary-guards-2026-11-06"></a>
## AI 해설 전송·응답·참고용 숫자 대조 — 2026-11-06 소스 검토

Claude의 AI 변경(`7c31417`, `401fe33`, `54b52eb`)과 후속 수정 작업 트리의 사실을 대조했습니다. [원래 제품 기록](../product/AI_COMMENTARY_GUARDS_2026-11-04.md)의 당시 검증·설계 설명과 후속 상태를 구분합니다. 이 절은 코드·정책 정합성 기록이며 실제 API 호출·법률 검토·공개 승인 증거가 아닙니다.

| 항목 | 현재 확인한 범위와 한계 | 근거 |
| --- | --- | --- |
| 계산 JSON | 알려진 private 구조 필드를 제외한 뒤 배열·pandas 자료를 직렬화 단계에서 50개로 자르지 않고 보존. NaN·무한대는 의미 설명 문자열로 바꾸고 `allow_nan=False`의 JSON을 생성. 알려진 필드의 무한대 의미와 일반적인 미정/비유한 값을 구분 | [변환](../../core/research/ai_payload.py) `ai_payload_json`·`NONFINITE_MEANINGS` |
| 전송 범위·크기 | 계산 JSON·질문 외에 분석 종류, 고정 작성 지시문 `_SYSTEM`, marker/null이 있으면 설명 `VALUE_NOTE`도 전송. 계산 JSON이 UTF-8 **180,000바이트 초과**이면 POST 전 `PAYLOAD_TOO_LARGE`; 직렬화/UTF-8 인코딩 실패는 `PAYLOAD_INVALID`. 이 한도는 전체 요청·질문·토큰·요금 한도가 아님 | [요청](../../core/quant/insights.py) `deep_analysis`; 네이티브 질문에는 별도의 4,000자 제한 |
| 기존 변환의 한계 | full-array 보존은 호출자가 넘긴 자료에 한정. 네이티브 보고서 `plain()`의 비유한 값→null과 Crypto 표의 `nu=inf`→`—`가 먼저 적용된 의미를 복원하지 않음. 필드명 필터는 자유 질문·문자열의 개인정보를 모두 탐지하지 않으며 자료의 외부 AI 전송권도 입증하지 않음 | [보고서](../../core/research/tool_export.py) `plain`, [네이티브 payload](../../quantgen_desktop/commentary.py) `commentary_payload`, [Crypto 표시](../../quantgen_desktop/market_tools.py) |
| 응답 종료 | 유효한 비어 있지 않은 텍스트와 `end_turn`일 때만 성공. `max_tokens`·`refusal`·그 밖의 중단/잘못된 응답은 오류와 빈 텍스트로 처리하여 부분 응답을 화면·보고서에 싣지 않음. 요청은 한 번이며 자동 재시도 없음; 출력 예산 1,500은 실제 응답 길이나 사실성을 보장하지 않음 | [응답 분류](../../core/research/ai_connection.py) `reply_result`, `deep_analysis` |
| 숫자 대조 | 전송한 계산 JSON의 값 및 질문에서 찾은 숫자와 응답 숫자를 제한된 표현·반올림/단위 규칙으로 대조. 키 이름·고정 지시문·분석 종류·`VALUE_NOTE`는 비교 대상이 아님. 부호·지표 대응·추론·판정·진위는 검증하지 않고 우연 일치·파생값 누락 가능. 실패/미실행도 해설의 공식 판정으로 바꾸지 않음 | [참고용 대조](../../core/research/ai_output_check.py) `number_check`·`check_line` |
| 표시·내보내기 | Flet와 네이티브에 ‘AI 해설 · 검증 안 됨’과 대조 한계를 표시. 같은 입력의 다른 출력 가능성을 유지. 네이티브는 `safe_detail`로 응답 표시가 달라지면 원문 기준 대조를 화면·내보내기에서 보류하고 `number_check=None`, `WITHHELD_REDACTED_REPLY`와 원문 기준을 기록; 표시된 글을 다시 검사했다고 주장하지 않음. 보고서 `verification=NOT_VERIFIED`, `verdict=NOT_RUN` 유지 | [Flet](../../ui/ai_panel.py), [네이티브](../../quantgen_desktop/commentary.py) `finished` |
| 선택·운영 경계 | 네이티브 미동의 안내는 고정 작성 지시문도 보낸다고 한영으로 설명하고 크기/인코딩 오류를 현지화. 기존 기본 미선택·입력 변경 시 동의 해제를 유지. Flet도 한영 전송 안내에 분석 종류·고정 지시문·해당 시 값 표기 설명을 포함하나 동등한 체크박스 동의 절차가 구현된 것은 아님. 부분 응답 미표시·표시 마스킹·대조 보류는 메모리 보안 소거·제공자 삭제 증거가 아님 | [네이티브 화면](../../quantgen_desktop/commentary.py), [번역](../../quantgen_desktop/translations.py), [Flet 화면](../../ui/ai_panel.py) `_SendNotice` |

01–20 정책을 대조하고 전송 범위·최소화·가격 한계·AI 주장·키보드 검수·삭제에 직접 관련된 문구만 보강했습니다. 모든 정책 `review-required`와 공개 준비 `BLOCKED`를 유지합니다. 제공자 계약·처리 국가·보존/삭제·데이터/라이브러리 권리·운영자 정보·법적 동의·실제 Windows/보조기술·실제 API/파일럿·동결 연구 증거는 별도이며, GPT/Gemini 추가 spec 공개·심사는 선택적 `NOT_PERFORMED`입니다. 원래 기록의 chance-match 수치는 당시 규칙의 합성 관측으로만 읽고 후속 단위/표현 규칙의 정확도나 현재 검증률로 재사용하지 않습니다. 소스 fingerprint 갱신과 최종 합성 실행 결과는 통합 후 별도 기록합니다.

<a id="a1-terminology-2026-11-06"></a>
## A1 용어·상태·표 머리글 — 2026-11-06 소스 검토

기준 `e79ef2c1160242ddf86d5b381e1005f2ad627e16` 대비 승인된 A1 표시 변경입니다. [용어·범위 기록](../product/A1_TERMINOLOGY_2026-11-06.md)을 따르며 A3 배치·읽기 도움말은 별도 구현입니다.

| 항목 | 확인한 소스 동작과 한계 | 근거 |
| --- | --- | --- |
| 용어 | 설계/검증·분석·기술적 분석·모의투자·샤프 지수·컨벡시티·맥컬리 듀레이션·무이표 금리·제공처 등 작성된 표시 문구를 정리. 기존 한영 별칭과 모델의 정규 키·선택값을 보존하며 이름 변경으로 새 기능·계산·검증을 만들지 않음 | [공통 문구](../../core/ui_messages.py), [기존 별칭](../../core/ui_legacy_messages.py), [네이티브 번역](../../quantgen_desktop/translations.py), [용어 사전](../../core/education/glossary.py) |
| 상태 | 지정 셀의 실행·연결·공식 판정 역할을 구분. 한국어 공식 판정은 원래 코드 병기, 상태 tooltip에는 원래 코드 보존, 알 수 없는 코드는 그대로 표시. CONFIGURED 설정 있음과 REACHABLE 응답 확인은 별개이며 연결·연구 판단 규칙 자체는 바꾸지 않음 | [상태 표시](../../quantgen_desktop/status_language.py), [연결 화면](../../quantgen_desktop/connections.py), [표 갱신](../../quantgen_desktop/app.py), [언어 전환](../../quantgen_desktop/localization.py) |
| 관측 상태 | Home OBSERVED의 한국어를 정상 관측으로 바꾸고 일별 관측 설명·오래된 자료/실패 경고와 원래 코드를 유지. 정상 관측은 실시간 체결·자료 완전성·실제 공급사 대조 성공이 아님 | [Home 상태·설명](../../quantgen_desktop/watchlist.py) `_STATUS`, `_price_tooltip`, `_reason` |
| 표시와 원본 구분 | 네이티브 항목 열은 명시한 표시 역할로 번역. ETF의 한국어 표시 어댑터는 원래 공통 설명 함수·보고서 절·AI payload·계산값을 보존. Flet 지정 표는 머리글 메타데이터와 원문 셀을 구분하며 알려진 머리글과 같은 공급자/사용자/결과 문자열도 원문 유지. 전체 Flet 화면 번역 완료를 뜻하지 않음 | [ETF 표시 어댑터](../../quantgen_desktop/market_narrative_language.py), [보고서 절 보존](../../quantgen_desktop/market_tools.py), [Flet 메타데이터](../../ui/localization.py), [채권](../../ui/bonds_page.py), [구조화](../../ui/structuring_page.py), [KRX](../../ui/krx_page.py), [매크로](../../ui/macro_page.py), [금리](../../ui/rates_page.py), [외환](../../ui/fx_page.py) |
| 검증 한계 | 표시 메타데이터·원래 코드·tooltip은 실제 키보드 경로·스크린리더 읽기·Windows DPI·전 화면 대비 수용의 증거가 아님. 긴 번역·상태 표시와 기존 제어를 실제 환경에서 재검수해야 함. A3 제목 번역의 존재도 A3 도움말 구현 증거가 아님 | [주장](12-claims.md), [대체 정보](13-alternative-text.md), [대비](14-contrast.md), [키보드](15-keyboard.md) |

01–20 정책을 현재 A1 소스와 대조하고 선택권·주장·키보드 문구만 직접 보강했습니다. 기존 법률·운영자·제공자 계약·라이선스·전송 동의·실제 공개/배포 조건, `review-required`와 공개 준비 `BLOCKED`를 보존합니다. 실제 Windows/API/파일럿·동결 연구 증거는 추가되지 않았고 Flet AI 체크박스 흐름도 여전히 미구현입니다. 최종 합성 실행·CI·병합과 소스 fingerprint는 통합 후 실제 결과로 별도 기록합니다.


<a id="a3-reading-layout-2026-11-06"></a>
## A3 네이티브 결과 배치·로컬 알아보기 — 2026-11-06 소스 검토

A1 코드 `2715d9e` 이후 A3 통합 소스 `e33063b`의 범위입니다. A1 선행 병합, A3 최종 통합 검사·CI·병합과 실제 배포는 각각 확인해야 합니다. [A3 구현·실행 기록](../product/A3_READING_LAYOUT_2026-11-06.md)을 따릅니다.

| 항목 | 확인한 소스 동작과 한계 | 근거 |
| --- | --- | --- |
| 결과 배치 | MC 제목→차트/서술→기존 7행 또는 GARCH 8행 표 순서. Bonds 기존 12개 지표와 실제 key-rate DV01 행을 같은 폭 두 G1 패널에 배치하고 내용 폭 820px 미만에서 세로 배치. 작은 지정 표만 실제 머리글·행·프레임·가로 스크롤 높이로 맞추며 다른 표의 스크롤은 유지. 계산·수치 형식·차트·원래 서술·보고서·AI 입력·공식 판정은 바꾸지 않음 | [표 높이·두 패널](../../quantgen_desktop/result_layout.py), [MC/호스트](../../quantgen_desktop/app.py), [채권](../../quantgen_desktop/bonds.py) |
| 로컬 알아보기 | 창마다 한 제어기. F1 또는 표/선택한 라벨의 문맥 메뉴로 열고 기존 로컬 용어집의 후보를 명시적으로 선택해야 정의 표시. 선택 행의 보이는 셀과 선택 문구를 그대로 인용하며 3.000%·−0.00·— 같은 표시를 재계산/재형식화하지 않음. 새 정의·금융 해석·AI/네트워크 요청·파일/QSettings 저장 없음 | [도움말](../../quantgen_desktop/reading_panel.py) `TermPanel`, `ReadingHelp`, [기존 용어집](../../core/education/glossary.py), [한영 제어 문구](../../quantgen_desktop/reading_language.py) |
| 문맥·복사 | 닫기·페이지/도구 전환·결과 초기화·원본 삭제, 같은 행 값/같은 크기 선택 문구 교체 시 인용 무효화. 원래 위젯이 남아 있고 표시·활성 상태이면 포커스와 원래 셀 복귀. 복사는 이용자가 선택할 때 OS 클립보드에 기록하며 인용 지우기가 클립보드·후속 사본 삭제나 메모리 보안 소거를 뜻하지 않음 | 같은 파일 `_snapshot`, `_source_contents`, `_check_quote`, `close`, `eventFilter`; [삭제 범위](20-deletion.md) |
| 중요 안내·겹침 | 창 폭 1280px 이상은 340px 도킹, 좁으면 본문 폭을 유지하는 겹침 표시. 보이는 명시적 `reading_help_keep_visible` 영역을 피한 높이 260px 이상 구간만 사용하고 없으면 닫고 tooltip 안내. 일반 결과 행은 일시적으로 가려질 수 있음. 호스트는 동의/AI·연결/규칙/권리·프로젝트 상태·시장/관심종목·MC/Bonds/포트폴리오의 지정 안내를 보호. 태그/기하 검사와 실제 보조기술 검수는 별개 | [배치·회피](../../quantgen_desktop/reading_panel.py) `_overlay_rect`, `reflow`; [호스트 태그](../../quantgen_desktop/app.py), [Bonds 태그](../../quantgen_desktop/bonds.py), [포트폴리오 태그](../../quantgen_desktop/portfolio.py) |
| 명시적 상세 접기 | `ToolPane.text`/`result_table`의 `display_role='provenance'`만 처음 접힌 상세 정보로 이동. 실제 연결 지점은 Macro 기준일·출처 개수 줄뿐. 별도 합성 ID·기술통계용 안내·짧은 표본 경고, 기본/알 수 없는/혼합/가정/지연/실패 문구는 본문 유지. 역할 메타데이터는 보고서 sections·AI 입력에 넣지 않음 | [위젯 배치](../../quantgen_desktop/tools.py), [Macro 호출](../../quantgen_desktop/macro.py), [접기 제어](../../quantgen_desktop/reading_panel.py) `DetailsFold` |
| 검증 범위 | 지정 합성/offscreen 검사에는 F1/Esc·셀 복귀·언어/테마·폭 변경·정확 인용·실제 Macro 접기·기존 보고서/AI 입력 비교가 있음. 선행 실행의 통과 수를 합산하지 않으며 재현된 baseline 실패도 기록대로 유지. 실제 Windows/IME/DPI·스크린리더·전체 대비/캡처 행렬·Flet 동등 구현·실제 API/공개 배포 완료를 뜻하지 않음 | [레이아웃 검사](../../tests/desktop_a3_layout_acceptance.py), [읽기 검사](../../tests/desktop_a3_reading_acceptance.py), [실행 기록·한계](../product/A3_READING_LAYOUT_2026-11-06.md), [키보드 검수](15-keyboard.md) |

01–20 정책을 현재 A3 소스와 대조하고 로컬 인용/명시적 복사, 선택권·주장·키보드·삭제에 직접 관련된 문구만 보강했습니다. 기존 법률·운영자·제공자 계약·라이선스·전송 동의·실제 공개/배포 조건, `review-required`와 공개 준비 `BLOCKED`를 유지합니다. Flet AI 체크박스 흐름·실제 Windows/API/파일럿·동결 연구 증거는 미완료이며 선택적 GPT/Gemini 추가 심사는 `NOT_PERFORMED`입니다. 최종 실행·CI·병합과 소스 fingerprint는 통합 후 실제 결과로 별도 기록합니다.

<a id="recorded-status-display-2026-11-06"></a>
## 기록된 소유자 결정·준비 상태 표시 — 2026-11-06 소스 검토

기준 `67a883875ca0a8242e880246ea2a009e688978f4` 대비 ⑫-1의 한정된 표시 수정입니다. 기존 snapshot의 의미와 검증 규칙을 유지하며 [구현 범위](../product/RECORDED_STATUS_DISPLAY_2026-11-06.md)를 따릅니다.

| 항목 | 확인한 소스 동작과 한계 | 근거 |
| --- | --- | --- |
| 기록과 화면 일치 | 네이티브/Flet System의 고정 공개 배포 NOT_APPROVED를 없애고 기존 `verify()`가 반환한 기록을 공통 한영 표시 함수로 전달. 원래 dict·코드·날짜·집계는 바꾸지 않음. 기존 번역 카탈로그의 호환용 문구가 남아 있어도 이 새 상태 화면은 명시적 한영 문구를 사용 | [공통 표시](../../core/recorded_status_display.py), [네이티브 System](../../quantgen_desktop/app.py) `make_system`, [Flet System](../../ui/research_home.py) `recorded_status`, `RecordedStatusView` |
| 승인·준비·게시 구분 | COMMERCIAL·OWNER_APPROVED·2026-10-30은 기존 소유자 상업 출시 결정. 규제 승인·기술 준비 완료와 분리하고 실제 공개 배포는 이 기록만으로 확인되지 않는다고 설명. 데이터/공식 게이트/검증/동결 연구 상태는 각각 원래 코드 유지 | [기존 기록·검증](../../tools/status/snapshot.py), [README 결정](../../README.md#regulatory-note), [주장 기준](12-claims.md) |
| 검증 실패 | 원본/상태 파일 누락, stale/변조·불일치, JSON/YAML 파싱 등 처리 대상 실패에는 None을 표시 함수로 전달해 확인 필요 문구만 표시. YAMLError 처리는 두 UI 경계에 추가하며 snapshot 생성·스키마·검증·승인 규칙은 변경하지 않음. 표시 함수 자체가 새 검증기인 것은 아님 | 같은 두 UI 호출부와 [표시 함수](../../core/recorded_status_display.py) |
| 시간·증거 한계 | 기록된 검사 수는 새 실행이 아니고 실행 시각/commit은 원본 미기록. 달력은 서명 메타데이터이며 파일별 검증은 별도. generated_at은 상태 자료 생성 시각이며 실제 검사·게시 시각으로 사용하지 않음. A3 System 중요 안내 보호 태그 유지 | [합성 표시 검사](../../tests/status_display_acceptance.py), [기존 snapshot 검사](../../tests/status_snapshot_acceptance.py) |

01–20 정책을 이 변경과 대조하고 12번 주장 문구만 보강했습니다. 정책 `review-required`, 공개 준비 `BLOCKED`, 운영자·계약·권리·동의·실제 공개/배포 조건과 Windows/보조기술·실제 API/파일럿·동결 연구 미완료 상태는 유지합니다. 이 수정은 실제 게시 여부나 포괄적 ⑫-1 완료를 판정하지 않습니다. 최종 합성 실행·CI·병합·소스 fingerprint와 사이트 반영/전달은 별도 증거로 기록합니다. 선택적 GPT/Gemini 추가 spec 심사는 `NOT_PERFORMED`입니다.

<a id="a3-mc-tab-width-2026-11-06"></a>
## A3 Monte Carlo 비활성 탭 최소 폭 후속 — 2026-11-06

최초 PR #77 Windows CI는 `67a8838`의 GBM·GARCH-t MC 가로 스크롤 최대값이 286px여서 기존 0 조건에 실패했습니다. 앞서 통과한 Linux 131개 검사와 이 실패를 별도 증거로 보존합니다. Quant 탭을 일반 `QTabWidget`에서 이미 사용 중인 `CurrentPageTabs`로 바꿔 현재 선택한 페이지의 크기 힌트만 사용합니다. 비활성 Strategy Lab의 최소 폭이 MC를 넓히는 경로를 제거하되 Strategy가 선택되면 그 최소 폭을 그대로 존중합니다. [앱 적용](../../quantgen_desktop/app.py) `make_quant`와 [기존 탭 크기 처리](../../quantgen_desktop/chart_study.py) `CurrentPageTabs`가 근거이며 계산·문구·가정·판정·보호 태그·보고서·AI 입력은 바꾸지 않습니다.

새 합성 회귀는 비활성 Strategy에 최소 폭 1800px를 주어 수정 전 넘침 1057px를 재현했습니다. 이는 숨은 탭 크기 제약의 재현이며 Windows에서 관측한 286px나 실제 Windows 글꼴·자식 폭을 재현/측정한 것으로 설명하지 않습니다. 수정 후 A3 layout 5개+reading 12개, 17개 검사가 통과했고 viewport 경계 조건을 보강한 같은 회귀 1개도 통과했습니다. 1개는 앞 검사와 겹치므로 합산하지 않습니다. 기존 넘침 0 조건은 유지하고 차트/표가 실제 viewport 안에 있는지도 검사하여 잘림으로 대신하지 않습니다. 선택한 Strategy의 필요한 스크롤·MC 복귀, 값·실행 보고서·AI 입력 보존도 확인합니다. [회귀 검사](../../tests/desktop_a3_layout_acceptance.py)와 [최종 통합/CI 기록](../product/A3_READING_LAYOUT_2026-11-06.md)을 연결합니다.

01–20 정책을 이 한정된 변경에 재대조하고 15번에 실패 이력·검수 범위만 보강했습니다. 수정 후 정확한 커밋의 Windows CI는 별도로 확인하며 클라우드 합성 통과를 실제 사용자 Windows/DPI·키보드·스크린리더 수용으로 바꾸지 않습니다. 정책 `review-required`, 공개 준비 `BLOCKED`, 기존 법률·라이선스·동의·실제 API/파일럿·동결 연구·게시/배포 조건은 유지합니다.

<a id="rates-inline-language-2026-11-06"></a>
## 금리 결과의 인라인 한영 안내 — 2026-11-06 소스 검토

기준 `3726dd6` 대비 ⑬-8/b2/b/2의 한정된 표시 변경입니다. [이전 PR #44 범위](../product/RATES_LANGUAGE_2026-10-31.md)는 결과 서술 번역이고 당시 인라인 안내는 제외되어 있었습니다. 이번 변경은 [금리 결과 표시](../../quantgen_desktop/rates.py) `RatesPane.show_result`의 다섯 블록에 명시적 한영 문구를 추가합니다.

| 항목 | 확인한 소스 동작과 한계 |
| --- | --- |
| 작성된 표시 | 출처 요약의 합성 고지·관측 개수, 스왑의 명목금액·지급 빈도·단일 곡선, 옵션의 정규 변동성·명목금액, 스왑션의 고정금리 지급/수취 방향, 시뮬레이션의 합성 표시·시드 7·경로 개수. Black·ACT/365F 등 이름/규약, 원래 코드·날짜·숫자 형식·단위는 유지 |
| 원문과 증거 | 원래 다섯 문장 구성식을 canonical text로 유지하고 표시용 `localized`만 추가. 공급자/곡선/모델/시뮬레이션 설명과 카탈로그 문구처럼 보이는 원문도 번역하지 않으며 기존 `safe_detail` 처리는 유지. [공통 표시·보고서](../../quantgen_desktop/tools.py) `text`, `bind_output`과 [라벨](../../quantgen_desktop/localization.py) `UiLabel`에 따라 원본 sections·보고서·AI 입력과 표시 문구를 구분 |
| 안내 노출 | 합성 곡선의 “현재 시장 데이터 아님”을 한영 모두 표시. 다섯 혼합 안내 블록에 `provenance` 역할을 부여하지 않으므로 본문과 기존 `reading_help_keep_visible` 보호를 유지. 별도 PCA 미실행·보조 모델 환산 상태·기간말 PV 설명·결과 서술·공식 판정은 변경하지 않음 |
| 검증 범위 | [금리 언어 회귀](../../tests/desktop_rates_language_acceptance.py)에 주입된 원문 설명·알 수 없는 출처, 스왑 양방향, 옵션 세 종류/두 모델/양방향, 단기금리 세 모델을 추가. 언어 반복 전환 시 표시·숫자·원본 sections·직렬화 보고서·AI 입력과 재계산 없음, A3 보호 속성을 검사. 실행 결과·CI·병합은 실제 수신 기록으로 별도 확인 |

01–20 정책을 이 변경과 대조하고 12번 주장 문구만 보강했습니다. 새 계산·공급자/번역 API·저장/동의·권리/승인 규칙을 추가하지 않으며 실제 Windows/DPI·키보드·스크린리더·API/공급사대조·법률/라이선스·파일럿·동결 연구·웹사이트 반영/배포 증거는 추가하지 않습니다. 기존 A3/System 좁은 화면 한계와 공개 준비 `BLOCKED`, 모든 `review-required`·미확정 항목을 유지합니다. Flet AI 체크박스 흐름은 여전히 미구현이며 선택적 GPT/Gemini 추가 심사는 `NOT_PERFORMED`입니다.

<a id="a3-mc-form-width-2026-11-06"></a>
## A3 MC 입력 폼 최소 폭 추가 후속 — 2026-11-06

앞의 비활성 탭 수정 `af782be` 뒤 Windows CI에서도 MC 자체 최소 폭 1014px, viewport 782/792px, 가로 넘침 294/284px가 확인되었습니다. 해당 실행은 17개 검사 중 3개 실패이며 최초 `67a8838`의 286px 실패와 별도 이력입니다. 앞의 합성 1057px 재현·Linux 통과를 Windows 전체 원인 해결이나 수정 후 Windows 성공으로 바꾸지 않습니다.

[앱](../../quantgen_desktop/app.py) `make_quant`의 데이터 출처·모델·드리프트 세 콤보박스에 [기존 공통 도구 머리글](../../quantgen_desktop/tools.py)의 `AdjustToMinimumContentsLengthWithIcon`, 최소 내용 길이 12, 가변 가로 폭/고정 세로 크기 정책을 적용합니다. 전체 항목 문자열은 목록 모델과 현재 선택 tooltip에 유지하며 선택/모델 데이터 변경에 tooltip을 갱신합니다. 기존 언어 제어기의 재번역도 이 경로를 사용합니다. 선택의 내부 값·기본값·입력 범위·이름·실행 경로·보고서·AI 입력·수치·NOT_RUN 안내와 A3 보호 태그는 유지합니다.

[추가 회귀](../../tests/desktop_a3_layout_acceptance.py)는 긴 합성 선택 문구와 14px 스타일 갱신으로 내용 기반 크기 힌트 경로를 검사합니다. 수정 전 해당 조건의 넘침 2615px는 별도의 합성 재현이며 Windows에서 관측한 284/294px나 실제 Windows 글꼴 폭을 재현한 증거는 아닙니다. 콤보 크기 정책만 적용한 중간 소스는 18개 합성 검사 통과 뒤 독립 Linux 렌더의 18px·영문·1000px 조건에서 14px 넘침(MC 최소 폭 770px, 설정 752px, viewport 818px, 내용 832px)으로 실패했습니다. 중간 통과와 이 실패를 함께 보존합니다.

최종 소스의 [선택 적용 폼](../../quantgen_desktop/result_layout.py) `ResponsiveFieldGrid`는 각 라벨·컨트롤의 실제 명시적/권장 최소 폭과 간격의 합으로 가능한 최대 열 수 3·2·1을 선택합니다. 원래 아홉 위젯을 같은 읽기 순서로 옮기며 폭별 라벨 높이·컨트롤 높이를 계산하고 글꼴/스타일/배치/폭 변화에 갱신합니다. 위젯을 배치한 뒤 Tab 순서를 설정합니다. 고정 창폭 경계값이나 임의로 낮춘 컨트롤 최소 크기를 쓰지 않으며 한 컨트롤의 실제 최소 폭보다 좁으면 필요한 스크롤이 남을 수 있습니다.

최종 layout 8개+reading 12개, 20개 합성 검사는 넘침 0, 입력·차트·표의 viewport 안 배치와 실제 최소 크기, 전체 행·선택값·보고서·AI 입력·재계산 없음 조건을 유지합니다. 18px 실제 MC 위젯의 Qt Tab 이동과 별도 250px 최소 폭 위젯의 1→2→3→1 배치도 확인합니다. 독립 Linux offscreen 렌더는 기본/18px·한영·1000/1360px 8개와 Linux Qt의 Windows 스타일을 적용한 1000px·한영 2개, 총 10개 관측에서 같은 소스의 넘침 0·팝업 열기·선택 변경/복귀·원본 보존을 확인합니다. Linux에서 Qt 스타일을 바꾼 것이며 Windows 운영체제 실행이 아닙니다. 이 범위의 합성 렌더/키 입력·목록 모델/tooltip 문자열 확인은 실제 Windows/DPI·스크린리더 수용이나 모든 확대율의 보장이 아닙니다.

[CI 구성](../../.github/workflows/runtime-smoke.yml)은 같은 `PyQt6==6.12.0` 설치를 독립 단계로 옮기고 기존 두 A3 모듈을 긴 네이티브 묶음보다 먼저 실행합니다. 검사를 없애거나 판정 기준을 낮추지 않습니다. 수정 후 실행·정확한 커밋의 Windows CI·병합은 [제품 검증 기록](../product/A3_READING_LAYOUT_2026-11-06.md)의 실제 결과로 확인합니다. 01–20 정책을 재대조하고 15번 검수 범위만 보강했으며 공개 준비 `BLOCKED`, 모든 `review-required`·미확정 법률/운영자/라이선스/동의·실제 API/파일럿·동결 연구·게시/배포 조건과 기존 A3/System 좁은 화면 한계를 유지합니다.

<a id="a3-qt-fixture-cleanup-2026-11-06"></a>
## A3 후속 Qt 시험 위젯 정리·CI 실행 예산 — 2026-11-06

`f7b4a73`의 Windows 3.14 CI는 A3 20개 통과 뒤 별도 차트/텍스트 31개를 모두 `OK`로 출력했으나 프로세스 종료 코드가 1이므로 전체 성공이 아닙니다. 정확한 종료 실패 원인은 확정하지 않았습니다. Linux의 같은 네 모듈에서는 수정 전 종료 시 `ResearchWindow`와 `ReadingHelp`가 각각 12개 남는 것을 관측했으며, 이 관측을 Windows 원인 재현으로 바꾸지 않습니다.

[시험 전용 정리 함수](../../tests/qt_fixture_cleanup.py)는 이미 삭제된 소유 위젯에는 반환하고, 살아 있으면 `hide`·`deleteLater`·해당 위젯에만 `DeferredDelete` 전달 후 실제 Qt 삭제를 확인합니다. 네 테스트 모듈의 직접 소유 fixture에만 적용하며 프로덕션 코드·종료 callback·계산·보고서·AI 입력은 바꾸지 않습니다. 전체 위젯 삭제·예외 무시·강제 종료·검사 건너뛰기 없이 기존 31개 테스트 메서드와 152개 정적 assertion 구문, Linux 강제 넘침 전제조건을 보존합니다. Qt 객체 정리는 사용자 자료·클립보드·디스크·제공자 삭제 또는 보안 소거 기능이 아닙니다.

수정된 집중 검사 6개(기존 차트 5개와 별도 소유권/반복 정리 진단 1개)는 3.276초, 종료 코드 0으로 통과했습니다. 최종 원래 네 모듈은 83.636초에 31개 중 30개 통과·기존 Linux 전제조건 1개 실패, 오류 0·종료 코드 1입니다. 서로 겹치는 검사를 합산하거나 이 실행을 전체 통과로 기록하지 않습니다. 최종 종료 시 위 두 객체는 각각 0개였고, 별도 삭제 대기 위젯은 집중 진단에서 살아 있어 대상별 처리를 확인했습니다. 중간 중복 정리 오류 2건과 기존 실패 이력은 보존하며, 새 Windows CI와 실제 사용자 Windows/DPI·보조기술 검수는 별도입니다.

[CI 구성](../../.github/workflows/runtime-smoke.yml)은 같은 차트/텍스트 명령을 A3 바로 뒤로 옮기고 정리 helper 경로를 검사 대상으로 추가합니다. 모든 실행 명령은 유지하고 설치 포함 작업 예산만 20분에서 30분으로 늘리며 구문 검사는 5분을 유지합니다. 앞선 Windows 3.11/3.12 작업은 API 시각상 약 20분 5초에 취소되었고 로그는 검사 진행 중이었으나 취소 주석 원문을 읽지 못했으므로 확정된 시간초과 원인으로 표시하지 않습니다. 이 실행 예산 변경은 검사·금융·연구 판정 기준 변경이 아닙니다.

01–20 정책을 시험/CI 차이와 대조했고 기존 조항은 그대로 유지합니다. [제품 검증 기록](../product/A3_READING_LAYOUT_2026-11-06.md)에 결과와 한계를 연결하며 공개 준비 `BLOCKED`, `review-required`, 법률·운영자·라이선스·동의·실제 API/파일럿·동결 연구·공개/배포 조건은 해제하지 않습니다.

<a id="instrument-identity-detached-2026-11-06"></a>
## 분리된 종목 식별 resolver — 2026-11-06 소스 검토

기준 `f7b4a73`에 [명시적 메타데이터 resolver](../../core/research/instrument_identity.py)와 [합성 검사](../../tests/instrument_identity_acceptance.py)를 추가한 한정된 범위입니다. 기존 실행·주문·라우팅·비용 계산·연구 판정 흐름에 연결하지 않습니다.

| 항목 | 확인한 소스 동작과 한계 |
| --- | --- |
| 입력 근거 | 호출자가 전체 alias registry와 선택적 provider/요청 심볼에 결합된 메타데이터를 전달. registry version은 호출자의 표식이며 제공자 확인·진위·최신성의 증거가 아님. 기본 registry, 실제 공급자 조회·파일/환경 읽기·저장 없음 |
| 식별·원문 | 조회에서만 ASCII 대소문자와 양끝 공백을 정규화하고 원래 provider/심볼 문자열은 결과에 보존. 문자열이 아닌 요청값은 None. 심볼 접미사·영문 이름으로 거래소/자산을 추정하지 않음. 자산/비용 행은 실제 enum을 요구하되 통화·MIC의 실재성이나 ISO/공급자 목록을 검증하는 기능은 아님 |
| 거부 범위 | 잘못된 요청/registry/메타데이터·결합 불일치·근거 없음은 UNKNOWN, 같은 내용도 포함한 중복 alias와 서로 다른 근거는 AMBIGUOUS. None과 구체 값도 불일치로 취급. 미지원 비용 조합은 식별 정보는 남기되 비용 행을 비운 UNSUPPORTED_COST. 잘못된 registry는 관련 없는 항목의 오류도 포함하여 전체 거부 |
| 비용 행 이름 | 호출자가 지정한 기존 `us`·`krx_stock`·`krx_etf`·`crypto`·`fx`·`futures` 이름만 반환. 주식/ETF/선물에는 제한된 MIC·quote 조합을 적용하며 crypto/FX는 명시적 자산·행의 일치로 판단하고 거래소 지원을 주장하지 않음. FX 동일 통화는 ASCII 대소문자가 달라도 거부. 이 표는 구현 선택이며 공급사 정책·데이터 권리·실제 수수료·비용 산식 승인이나 production 비용 변경이 아님 |
| 실행·혼합 입력 | continuous 선물은 orderable=False, 다른 결과는 주문 가능성 증거가 없어 None. RESOLVED도 거래 허가·실행 종목 ID·검증된 공급사 식별을 뜻하지 않음. 혼합 목록은 순서·중복·각 거부를 보존하며 비용을 합산하지 않음. list/tuple이 아닌 목록 컨테이너는 TypeError |
| 검증 한계 | 과거 설계의 17개 요청을 주입한 합성 registry로 검사하며 설계의 required_evidence 문장을 실제 메타데이터로 사용하지 않음. 공급자별 결합·통화 구분·모호/미지원·원문 보존·불변 결과와 I/O 없는 해석을 검사. 수정 전 FX 대소문자 동등 self-pair의 두 실패와 수정 후 19개 합성 통과를 구분. 실제 공급사 대조·Windows·비용 계산·주문/라우팅·동결 연구 결과 검증은 수행하지 않음 |

01–20 정책을 이 분리된 소스와 대조했으며 기존 번호 문서의 처리·권리·비용/주장·승인·연구 한계가 그대로 적용되어 본 사실 기록만 추가합니다. 실제 registry 확보·공급사 검증·기존 비용/연구/주문 경로 연결은 별도 범위와 증거가 필요합니다. 모든 미확정 운영자/법률/계약/라이선스/동의·실제 API/파일럿·동결 연구·공개/배포 조건, `review-required`와 공개 준비 `BLOCKED`를 유지하며 선택적 GPT/Gemini 추가 심사는 `NOT_PERFORMED`입니다.

<a id="r3-event-envelope-codec-2026-11-06"></a>
## R3 이벤트 envelope 코덱·LAB ID의 분리된 일부 구현 — 2026-11-06

기준 `b79d56d`에 [순수 코덱](../../core/quant/run_registry_codec.py)과 [합성 검사](../../tests/run_registry_codec_acceptance.py)를 추가합니다. 호출자가 전달한 메모리 자료·바이트와 UTC 시각·토큰 공급 함수를 처리하는 범위이며 저장소·기록기·Lab 연결·공식 원장·동결 연구·판정/소유자 승인 효과를 구현하지 않습니다.

| 항목 | 확인한 소스 동작과 한계 |
| --- | --- |
| Envelope 범위 | `qg-run-registry/1`의 알려진 이벤트와 허용된 최상위 필드, 기본 ID/시각/작성자·chain 필드 형식을 검사. 이벤트별 내용 필드는 여기서는 선택적이며 중첩 통계/요청 의미·필수 payload 전체·이벤트 순서·중복 실행·수명주기를 검증하지 않음. 사람 이벤트의 `person` 필드 존재는 본인 확인·동의·owner ruling 유효성이나 승인 증거가 아님 |
| 바이트 형식 | 키 정렬·공백 없는 UTF-8 JSON과 한 개의 끝 LF를 사용. 입력 객체를 바꾸지 않고 분리된 JSON 자료를 반환. 중복 JSON 키·비정규 바이트·잘못된 UTF-8·지원하지 않는 JSON 값·순환 참조 등을 거부. 원래 문자열을 마스킹하는 기능이나 개인정보 최소화/전송 동의 구현은 아님 |
| 비유한 수치 | NaN·양/음 무한대를 `null`로 바꾸고 배열 인덱스와 `/`·`~` 이스케이프를 포함한 RFC 6901 위치를 정렬·중복 제거하여 기록. 세 값의 종류·부호·업무상 의미를 보존/복원하지 않음. 기존 위치 표시는 해당 null의 구조만 확인하며 실제 과거 변환 여부를 입증하지 않음 |
| MD5 연결 | `row_md5`는 두 chain 필드를 제외한 정규 JSON, `prev_row_md5`는 이전 줄의 LF까지 포함한 바이트의 MD5. 단일 줄 확인은 이전 줄과의 연결을 확인하지 않으며 별도 stream 검사가 전달된 줄과 선택적 직전 줄의 연결만 대조. MD5는 인증·위변조 방지 보장이 아니며 독립적인 끝 기준점이 없는 정상 접두부에서 완전한 뒤쪽 기록 삭제를 알아낼 수 없음 |
| ID | 호출자가 넘긴 UTC offset 0 시각과 한 번 호출한 공급 함수의 8자리 소문자 hex 토큰으로 LAB 형식 ID를 구성하고 달력·문자 형식을 검사. 시각은 초 단위로 표현. 실제 시계·난수원·충돌 예약/재시도·고유성/보안성 보장을 제공하지 않으며 주입한 공급 함수 내부의 부작용을 차단하는 기능도 아님 |
| Segment·연결 제외 | `SEGMENT_START` envelope만 지원하고 설계에 명시되지 않은 segment payload 필드명을 만들지 않음. 실제 segment 저장·잠금·append/fsync·복구·회전·완전성, key/fingerprint 생성, 사람 결정 조회·효과, Lab 실행/공식 원장/연구 연결은 미구현. 입력에 파일/원장/해시 이름이 있어도 해당 파일을 열거나 검증하지 않음 |
| 검증 범위 | 최종 17개 합성 검사는 정규 바이트·해시·줄 연결/손상·비유한 위치·거부 조건·주입 ID를 검사하여 0.010초, 종료 코드 0으로 통과. 앞선 16개 실행과 겹치므로 합산하지 않음. 전체 이벤트 의미·저장소·수명주기 및 전체 T-RUNREG-02/-09·상위 ⑨-3a 완료 증거가 아님 |

01–20 정책을 이 일부 구현과 대조했고 기존 번호 조항은 유지합니다. [제품 범위·검증 기록](../product/R3_DETACHED_CODEC_2026-11-06.md)과 함께 읽으며 실제 API/공급사·Windows 사용자 환경·법률/운영자/계약/라이선스/동의·파일럿·동결 연구·게시/배포 조건, `review-required`와 공개 준비 `BLOCKED`를 해제하지 않습니다. 기존 Identity·Rates·상태·A3의 범위와 실패/후속 검증 기록도 보존하며 선택적 GPT/Gemini 추가 심사는 `NOT_PERFORMED`입니다.

<a id="identity-a1-fixture-cleanup-2026-11-06"></a>
## Identity 통합의 A1 시험 위젯 정리 후속 — 2026-11-06

`b79d56d`의 Runtime `42191579626` Ubuntu 3.12 작업은 A1 세 모듈 18개 검사를 11.710초에 `OK`로 출력한 뒤 segmentation fault·종료 코드 139로 실패했습니다. 검사 문구를 프로세스 성공으로 대체하지 않습니다. 같은 세 모듈의 수정 전 Linux guarded 진단은 18개 통과·14.055초·종료 코드 0이었지만 종료 시 소유 `ResearchWindow` 4개·상태 host 5개와 `ReadingHelp` 4개가 살아 있었습니다. 로컬에서 충돌을 재현한 것은 아니며 CI 충돌의 정확한 원인은 미확정입니다.

[A1 용어 검사](../../tests/desktop_a1_terms_acceptance.py)와 [A1 상태 검사](../../tests/desktop_a1_status_acceptance.py)는 직접 소유한 창/host의 cleanup 등록을 이미 있는 [대상별 Qt 정리 함수](../../tests/qt_fixture_cleanup.py)로 바꿉니다. 두 import·두 cleanup 등록 외의 테스트 내용, 도우미·Flet 모듈·프로덕션 구현은 그대로입니다. 기존 18개 테스트 메서드와 82개 정적 assertion 구문, 값·코드·원문·보고서·AI 입력·언어 왕복 검사를 보존하며 종료 우회·예외 무시·전체 위젯 삭제·skip을 추가하지 않습니다.

수정 후 같은 18개 검사는 12.249초·종료 코드 0으로 통과하고 소유 Qt 위젯 9개 모두의 삭제 신호를 확인했습니다. `ResearchWindow`·상태 host·`ReadingHelp` 생존 수는 0이며 전체 Qt top-level은 24개가 남습니다. 일부 Python wrapper 참조는 남아 있어 전체 메모리/객체 소거라고 주장하지 않습니다. 전후 실행은 같은 검사이므로 합산하지 않고, 이 수명 관측을 실제 CI 원인 입증·새 head의 CI 성공·사용자 자료 삭제 기능으로 확대하지 않습니다.

[CI 구성](../../.github/workflows/runtime-smoke.yml)은 동일한 A1 명령을 차트/텍스트 검사 바로 뒤로 옮겨 조기에 결과를 확인합니다. 모든 기존 명령과 구문 5분/설치 포함 30분 예산을 유지합니다. [제품 검증 기록](../product/DETACHED_INSTRUMENT_IDENTITY_2026-11-06.md)에 실패·전후 측정과 새 CI 확인 필요를 남기며, 01–20 번호 정책·공개 준비 `BLOCKED`·`review-required`와 기존 법률/권리/동의·실제 Windows/API/파일럿·동결 연구·게시/배포 조건을 유지합니다.

<a id="rates-a1-fixture-cleanup-2026-11-06"></a>
## Rates 통합의 동일 A1 시험 정리 적용 — 2026-11-06

Rates `578d35d`의 Runtime `42191259285` Ubuntu 3.12 작업 `127803562205`는 A1 세 모듈 18개 검사를 19.066초에 `OK`로 출력한 뒤 segmentation fault·종료 코드 139로 실패했습니다. 기존 금리 언어 11개 합성 통과와 별도 결과이며 전체 Runtime 성공으로 기록하지 않습니다.

수정 전 두 네이티브 A1 파일은 Identity `b79d56d`와 같아 검토된 `e981ef7`의 동일한 두 import·두 cleanup 등록을 적용합니다. [A1 용어](../../tests/desktop_a1_terms_acceptance.py)·[상태 검사](../../tests/desktop_a1_status_acceptance.py)가 기존 대상별 Qt 삭제 도우미를 재사용하며 18개 테스트 메서드·82개 정적 assertion 구문과 프로덕션/Flet/도우미 코드는 유지합니다. 공유 Identity 진단의 전후 18개 통과·자연 종료 코드 0, 수정 후 12.249초 및 소유 Qt 위젯 9개 삭제는 동일 수정의 근거이며 Rates의 신규 로컬 실행으로 세지 않습니다. 로컬 충돌 재현과 기존 CI 실패의 정확한 원인 입증은 없으며 새 head의 전체 CI를 확인해야 합니다.

동일 A1 명령을 차트/텍스트 바로 뒤로 옮기고 모든 기존 명령·5분/30분 실행 예산을 유지합니다. [제품 검증 기록](../product/RATES_INLINE_LANGUAGE_2026-11-06.md)에 실제 Rates 실패와 공유 측정의 차이를 남기며 01–20 번호 정책·기존 사실·`review-required`·공개 준비 `BLOCKED`·법률/권리/동의·실제 Windows/API/파일럿·동결 연구·게시/배포 조건을 보존합니다. 검사 완화·skip·종료 우회·전체 객체/사용자 자료 소거 기능은 추가하지 않습니다.
<a id="r3-single-segment-store-2026-11-06"></a>
## R3 단일 활성 파일 저장의 분리된 일부 구현 — 2026-11-06

기준 `f3d6c5e`의 코덱 위에 [호출자 경로 저장 유틸리티](../../core/quant/run_registry_store.py)를 추가한 ⑨-3a/store/1 범위입니다. 앱·Lab·실제 원장·환경/설정 경로·공급자·소유자 결정 효과·연구 판정에는 연결하지 않습니다. 코덱의 문자열/비유한 위치·MD5 한계는 그대로 적용합니다.

| 항목 | 확인한 동작과 한계 |
| --- | --- |
| 파일·읽기 | 호출자가 이미 있는 신뢰할 수 있는 로컬 디렉터리의 절대 `.jsonl` 경로를 지정. 같은 기본 이름의 `.lock`을 사용하며 객체 생성과 없는 파일 읽기는 파일을 만들지 않음. 기존 데이터의 읽기에 sidecar가 없으면 거부. append는 후속 기록 거부 전에도 sidecar를 생성/초기화할 수 있어 모든 거부를 무변경이라고 주장하지 않음 |
| 협력 잠금 | 정규화한 경로의 프로세스 잠금과 OS sidecar 잠금으로 협력 작성자의 접근을 직렬화. 기본 2초·선택 0–10초는 두 잠금 획득의 합산 예산이며 파일 읽기·검증·쓰기·fsync 시간 제한이 아님. 최종 심볼릭 링크/특수 파일은 거부하지만 경로 보안 sandbox·하드링크 별칭·외부 교체·적대적 디렉터리 변경·동기화 폴더 지원을 보장하지 않음 |
| 허용 이벤트·검증 | STARTED·PROGRESS·FINGERPRINT·SHADOW·FINISHED만 지원하고 전체 기존 파일을 매번 검증. 같은 run ID의 STARTED 또는 FINISHED 중복을 잠금 안에서 거부. 전체 이벤트 순서·필수 payload 의미·사람 권한·연구 결과를 검증하는 것은 아니며 사람/segment 이벤트는 미지원. 전체 바이트 읽기와 MD5 연결 대조도 인증·완전한 과거 이력 증명이 아니며 유효 접두부 뒤의 완전한 기록 삭제는 독립 기준점 없이 알 수 없음 |
| 쓰기·불확실성 | 입력을 잠금 대기 전에 분리해 보존하고 정규 UTF-8 JSON+LF를 append한 뒤 flush/fsync. 쓰기 시도 후 오류에는 일부 또는 전체 바이트가 남을 수 있음을 `AppendOutcomeUncertain`으로 알리고 자동 재시도·잘라내기·복구를 하지 않음. 이후 정상 읽기는 현재 바이트를 확인할 뿐 실패 당시 fsync의 내구성을 입증하지 않음. 손상/불완전한 데이터는 거부 후 그대로 남음 |
| 크기·보존 | 32 MB를 32,000,000바이트로 정하고 append 전에 초과를 거부. 후속 append에서 회전하는 전체 설계보다 좁은 구현이며 회전·prefix cache·복구·보존기간·TTL·자동 삭제는 없음. 파일 상한과 잠금 해제는 보유/파기 정책이나 암호화·개인정보 필터가 아님 |
| 실제 검증 범위 | [합성 검사](../../tests/run_registry_store_acceptance.py) 16개와 기존 코덱 17개, 총 33개가 0.401초·종료 코드 0으로 통과. 임시 파일의 정규 바이트·전체 검증·중복 경쟁·5개 스레드의 각 10개 append·별도 실제 Linux 프로세스의 잠금·불확실한 쓰기 등을 검사. 독립 임시 검사 8개 통과는 겹치는 별도 근거이며 합산하지 않음. Windows `msvcrt` 동작·실제 사용자 파일/원장·전원 장애 내구성 수용을 이 Linux 결과로 완료 처리하지 않음 |

[제품 범위·검증 기록](../product/R3_SINGLE_SEGMENT_STORE_2026-11-06.md)을 따르며 전체 R3·T-RUNREG-02·기록기/key/Lab/사람 결정/회전/복구/연구 연결은 미완료입니다. 01–20 정책을 재대조하여 01·07·20의 처리/최소화/삭제 지도에 새 `.jsonl`·`.lock`만 추가했습니다. 기존 원장·보호 자료를 읽거나 실행한 증거가 아니며 모든 `review-required`·공개 준비 `BLOCKED`·운영자/법률/계약/라이선스/동의·실제 API/파일럿·동결 연구·게시/배포 조건과 선택적 추가 심사 `NOT_PERFORMED`를 유지합니다.

<a id="r3-detached-planned-keys-2026-11-06"></a>
## R3 계획 구성 키의 분리된 일부 구현 — 2026-11-06

기준 `b5cbf669`에서 [계획 키 함수](../../core/quant/run_registry_keys.py)를 추가한 ⑨-3a/keys/1 범위입니다. 호출자가 규칙 ID·pairs 여부·기호·grid·이미 결정한 int/float 비용을 제공하며 함수 자체는 파일/원장·설정·환경·시계·공급자·비용표·기존 Lab를 조회하거나 등록하지 않습니다. 반환은 grid 위치별 `{theta_index, config_id}`이며 중복 위치도 남겨 실제 등록 수·N_raw·판정·연구 증거로 해석하지 않습니다.

| 항목 | 확인한 동작과 한계 |
| --- | --- |
| 기존 키 조합 | 기존 writer처럼 기호의 앞뒤 공백 제거·대문자화 후 non-pairs만 정렬하며 pairs 순서·중복 기호를 보존. 명시한 기호/비용은 theta의 같은 이름을 대체. `default=str` JSON 왕복의 tuple/list 변환·객체 키 문자열 변환/충돌과 int/float 구분을 보존하며 새로운 의미상 동일성 규칙을 만들지 않음 |
| 직렬화·수치 | rule·params·고정 timing_class `COMPLIANT`·여섯 null 선택 필드의 9개 최상위 필드를 정렬·압축 UTF-8 JSON, 끝 LF 없이 MD5로 계산. MD5는 기존 키 호환용이며 인증/충돌 방지 보장이 아님. 미결정·bool·비유한 비용은 빈 grid에서도 거부하고 비유한 params도 거부. 비용표/최소 비용·적격성 검사가 아니며 `COMPLIANT`는 기존 조합의 상수로 실제 timing·법률 준수·연구/소유자 승인 증거가 아님 |
| 메타데이터·입력 한계 | 별도로 전달된 실행 날짜·공급자/source·시각·시장·script·anchor·결과를 자동으로 키에 넣지 않음. 호출자가 같은 이름을 theta 안에 넣으면 params에 남아 ID에 영향. 임의 객체의 문자열 변환 등 호출자 코드 부작용/불안정성을 막는 sandbox가 아니며 지원하는 입력 범위의 바이트 호환을 과학적 동등성·공급사 동일성·거래 가능성으로 확대하지 않음 |
| 과거 소스 대조 | `527cdf24`의 원래 writer와 현재 이동된 writer 함수는 끝 LF 포함 1,708바이트가 같음. 새 함수와 독립적으로 과거 소스에서 지금 생성한 고정 예제는 27사례·151개 예상 위치이며 7개 family의 전체 66위치를 비용 int/float로 각각 포함. 과거 실제 운영 기록이나 과거 원장 실행 증거가 아님 |
| 합성 검증 | [유지 검사](../../tests/run_registry_keys_acceptance.py) 최종 13개가 0.986초·종료 코드 0으로 통과. 변경하지 않은 현재 writer를 합성 입력의 26개 nonsynthetic-label 사례에서 명시한 새 임시 원장으로 실행했고 기본 경로는 거부·dotenv/네트워크/보호 자료 접근은 차단. 별도 SYNTHETIC 사례는 등록 없이 반환하며 파일을 만들지 않음. US 비용 50.0은 소스 상수만 대조하여 실제 비용 resolver/공급사 분류를 실행·검증하지 않음 |
| 별도 검토·미완료 | 독립 검사 7개·0.002초와 과거 예제 생성 1개·0.051초는 각각 종료 코드 0이며 13개와 합산하지 않음. 앞선 private 생성기의 grid 개수 가정과 표준 time import 허용 누락 실패는 보존하고 수정했으며 제품 함수 실패로 바꾸어 적지 않음. 로컬 Linux 결과이며 새 head의 CI·실제 Windows 사용자 환경·전체 T-RUNREG-01b·상위 R3·recorder/Lab/연구 연결 완료 근거가 아님 |

[제품 범위·검증 기록](../product/R3_DETACHED_KEYS_2026-11-06.md)에 따라 01–20 번호 정책은 유지합니다. 기존 codec/store·Identity·Rates·상태·A3의 사실과 한계, `review-required`·공개 준비 `BLOCKED`·운영자/법률/계약/라이선스/동의·실제 API/공급사/파일럿·동결 연구·게시/배포 조건 및 선택적 GPT/Gemini 추가 심사 `NOT_PERFORMED`를 해제하지 않습니다.

### 2026-11-06 기업 식별 마크·목록 가독성 후속

Home 표와 시장 관심종목 카드·검색·종목 제목에 로컬 문자 식별 마크를 추가합니다. 공식 기업 로고 파일을 내려받거나 추가 데이터 공급처에 접속하지 않습니다. 종목코드와 전체 이름이 식별 기준이며, Home의 긴 화면 이름은 한 줄 말줄임하되 전체 이름을 모델·접근성 이름·툴팁에 유지합니다. Home 44px 행, 오른쪽 숫자 정렬, Q-SCORE 마지막 열/도움말과 기존 상세·차트 경로를 유지합니다.

공통 본문 라벨은 15px, 설명 캡션은 실제 Medium 14px/500, Home 설명문은 14px/500입니다. 표 머리·차트 축에는 기존 별도 밀도를 유지합니다. 번들 글꼴 바이너리는 교체하지 않았으며 Windows 획 번짐 해소를 실측한 것은 아닙니다. Home 및 종목 상세의 거래량·시가총액은 한국어/영어 모두 K/M/B/T(10³/10⁶/10⁹/10¹²)로 축약하고 전체 값·통화·기존 시각/상태는 상세 또는 툴팁에 유지합니다. 가격 자체와 Q-SCORE 산식·자료 조회는 바꾸지 않습니다. 근거: [검토 기록](../product/COMPANY_MARKS_READABILITY_20261106.md).

<a id="r3-keys-ui82-integration-2026-11-06"></a>
## R3 계획 키와 별도 UI82 변경의 통합 — 2026-11-06

계획 키 head `246c9af2`에 main `e4ec6ef9`의 UI82 변경을 통합하며 양쪽 기존 사실을 보존합니다. [UI82 표시 범위](../product/COMPANY_MARKS_READABILITY_20261106.md)의 문자 마크·표/글꼴·K/M/B/T 표시와 [분리된 계획 키](../product/R3_DETACHED_KEYS_2026-11-06.md)는 별도 기능입니다. UI 코드/검사는 incoming main과, codec/store/keys 및 keys 검사·고정 예제는 이전 keys head와 같은 바이트입니다. 숫자 표시가 바뀌는 화면까지 원래 표시 문자열과 동일하다고 주장하지 않으며 키 산식·등록/연구·공급자 요청·승인 규칙의 변경은 없습니다.

기존 Linux의 고정 710px 가로 넘침 사전조건 실패는 당시 기록으로 유지합니다. UI82의 합성 검사는 고정값 대신 `max(710, 실제 viewport 폭 + 100)`으로 충분히 큰 입력을 만들고 기존 넘침 발생·정상 정책 복원 후 0·선택/요청/전체 문구 보존 검사를 유지합니다. 이는 과거 실패를 성공으로 바꾼 기록이나 실제 Windows 글꼴/접근성 검증이 아닙니다. 통합 후 임시·합성 guarded 검사 codec 17개·store 16개·keys 13개, 총 46개는 1.480초·종료 코드 0으로 통과했으며 기존 집중 검사와 겹쳐 합산하지 않습니다. `246c9af2`의 Runtime 42201679975 전체 6개 작업과 Compliance 42201680042 성공은 해당 이전 head의 근거이며, 본 통합 결과의 최종 head CI 성공은 별도로 확인해야 합니다.

01–20 정책을 통합 소스와 다시 대조하여 UI82의 13·14·19 추가 조항과 기존 17개 정책·RELEASE_GAPS·R3 보존/미완료 한계를 유지합니다. 웹 전달은 PR82 큐의 `queued`/영수증 없음이며 실제 적용·배포를 완료로 바꾸지 않습니다. `review-required`·공개 준비 `BLOCKED`, 법률/운영자/계약/라이선스/동의·실제 API/공급사/Windows 사용자 검증·파일럿·동결 연구·전체 R3 조건과 선택적 추가 심사 `NOT_PERFORMED`는 그대로입니다.

<a id="r3-detached-data-hash-2026-11-06"></a>
## R3 전달받은 panel 바이트의 분리된 data MD5 — 2026-11-06

기준 `a083f751`에 [순수 data hash 함수](../../core/quant/run_registry_data_hash.py)를 추가한 ⑨-3a/data-hash/1 범위입니다. 승인된 R3 rev2 §5.4의 지정 바이트 조합만 계산하며 기존 데이터 수집·정렬·Lab·codec/store/keys 호출·원장·소유자 결정·판정에는 연결하지 않습니다.

| 항목 | 확인한 동작과 한계 |
| --- | --- |
| 지정 조합 | 날짜 문자열을 LF로 연결한 UTF-8, NUL 1바이트, 기호 문자열을 LF로 연결한 UTF-8, NUL 1바이트, little-endian float64 행렬의 C 순서 바이트를 연결해 소문자 MD5 반환. 끝 LF·JSON·dtype/shape 머리말·시각·공급자 메타데이터를 추가하지 않음. shape는 길이와 대조하지만 해시 머리말로 넣지 않음 |
| 지원 입력 | 빈 축이 아닌 일반 list/tuple의 일반 문자열, 정확한 ASCII `YYYY-MM-DD` 유효 달력 날짜, 정확히 2차원인 일반 `numpy.ndarray` float64와 `(날짜 수, 기호 수)` shape만 지원. 빈 문자열·LF/NUL·UTF-8 인코딩 불가 문자열·잘못된 shape/타입을 거부. float32/정수/bool/복소/객체/구조체·배열 subclass/masked/memmap을 변환·채움 없이 거부. 이 범위는 API 입력 제한이며 새로운 연구 기준·거래일/세션/관측기간/홀드아웃 검증이 아님 |
| 원문·원시 비트 | 날짜/기호 순서·중복을 보존하고 기호 대소문자·공백·CR·Unicode를 정규화하지 않음. 양 endian·C/F 순서·음수/0/비연속 stride·읽기 전용 배열을 처리하며 정수 view로 byte order만 바꿔 signed zero·무한대·NaN payload/signalling 비트를 보존. 가격 반올림/복구·비유한 값의 null 변환·의미상 동일성 판정은 없음 |
| 효과·증거 한계 | 호출자 입력을 변경하지 않으며 안정된 입력을 전제로 함. 동시 수정 중 일관된 snapshot은 보장하지 않음. 함수 자체의 파일/시계/설정/환경/공급자 조회·저장·실행 등록·횟수 계산은 없음. MD5 일치는 인증·유효 가격·공급자 일치·조정 기준·자료 권리·연구 결과의 증거가 아님 |
| 합성 검증 | [유지 검사](../../tests/run_registry_data_hash_acceptance.py) 15개가 0.013초·종료 코드 0으로 통과. root의 data hash 15개+keys 13개+store 16개+codec 17개 통합 61개도 1.382초·종료 코드 0이며 앞선 검사와 겹쳐 합산하지 않음. 별도 독립 검사 10개·0.009초·종료 코드 0도 중복을 포함하는 별도 근거. 독립적인 표준 라이브러리 예제 준비 1개 통과는 새 함수/NumPy를 사용하지 않은 고정 바이트 기대값 근거. 모든 입력은 합성이며 memmap 거부 사례도 별도 임시 파일만 사용. 새 head의 전체 CI·실제 사용자 Windows/API 증거는 별도 확인 대상 |

[제품 범위·검증 기록](../product/R3_DETACHED_DATA_HASH_2026-11-06.md)에 따라 01–20 번호 정책은 유지합니다. series-store SHA-256 규칙·저장·recorder/Lab·전체 payload/수명주기·실제 원장·동결 연구·상위 R3 완료를 구현하거나 추정하지 않습니다. 기존 사실/실패 이력과 `review-required`·공개 준비 `BLOCKED`, 운영자/법률/계약/라이선스/동의·실제 API/공급사/Windows 사용자 검증·파일럿·게시/배포 조건 및 선택적 추가 심사 `NOT_PERFORMED`를 유지합니다.

<a id="r3-detached-source-hashes-2026-11-06"></a>
## R3 전달받은 소스 내용의 분리된 SHA-256 — 2026-11-06

기준 `6ddf5146`에서 [소스 해시 함수](../../core/quant/run_registry_source_hash.py)를 추가한 ⑨-3a/source-digests/1 범위입니다. 승인된 R3 §3.3 중 호출자가 이미 전달한 내용의 raw/LF 해시만 계산하며 실제 함수·파일·저장소 소스를 수집하거나 전체 코드 식별자·원장·Lab에 연결하지 않습니다.

| 항목 | 확인한 동작과 한계 |
| --- | --- |
| 지원 입력·반환 | 정확한 일반 `str`을 strict UTF-8로 인코딩하거나 정확한 일반 `bytes`를 그대로 받음. 빈 입력은 허용하고 surrogate 등 인코딩 불가 문자열·subclass·bytearray·memoryview·경로·스트림·변환 객체는 강제 변환 없이 거부. bytes는 잘못된 UTF-8·NUL도 불투명한 바이트로 처리. 매번 `lf`·`raw` 두 키와 소문자 64자리 SHA-256의 새 dict를 반환하며 입력은 변경하지 않음 |
| 원문·개행 | raw는 원래 바이트, lf는 원래 CRLF 쌍만 한 번 LF로 치환한 바이트의 해시. `CR CR LF`는 `CR LF`가 되며 다시 LF까지 치환하지 않으므로 일반적인 개행 정규화·멱등 변환이 아님. lone CR·BOM·들여쓰기·공백·Unicode 조합·끝 개행 유무를 보존하고 trim/dedent·파싱·AST/Unicode 정규화를 하지 않음 |
| 효과·증거 한계 | 함수 자체의 파일/네트워크/환경/설정/시계/git/소스 검사·로그·저장 없음. 큰 입력의 자원 한도는 호출자 책임이며 sandbox/스트리밍 수집기가 아님. SHA-256은 전달 내용의 지정 바이트 계산이며 출처·저작자·이용권·인증·완전한 전략 소스 범위·의미상 동등성을 입증하지 않음. 전송·공개 허락이나 개인정보 제거/안전한 삭제를 제공하지 않음 |
| 합성 검증 | [유지 검사](../../tests/run_registry_source_hash_acceptance.py) 8개·0.002초, 별도 독립 검사 10개·0.002초가 각각 종료 코드 0으로 통과. root의 source hash 8개+data hash 15개+keys 13개+store 16개+codec 17개 통합 69개도 1.524초·종료 코드 0이며 서로 겹쳐 합산하지 않음. 별도 표준 라이브러리 고정 바이트 예제 준비 1개 통과는 제품 수용 검사 수가 아님. CRCRLF 관련 제품 설명만 더 정확하게 고쳤고 소스/검사 변경이나 실패 실행은 없었음. 모두 로컬 Linux 합성 근거이며 새 최종 head의 전체 CI·실제 사용자 Windows/API 증거는 별도 확인 대상 |

[제품 범위·검증 기록](../product/R3_DETACHED_SOURCE_HASH_2026-11-06.md)에 따라 01–20 번호 정책은 유지합니다. 소스 수집·파일/git 메타데이터·전체 코드 식별·recorder/Lab·실제 원장·횟수/판정·소유자 승인·동결 연구·상위 R3 완료를 구현하거나 추정하지 않습니다. 기존 사실/실패 이력과 `review-required`·공개 준비 `BLOCKED`, 운영자/법률/계약/라이선스/동의·실제 API/공급사/Windows 사용자 검증·파일럿·게시/배포 조건 및 선택적 GPT/Gemini 추가 심사 `NOT_PERFORMED`를 유지합니다.

<a id="r3-detached-series-digest-2026-11-06"></a>
## R3 전달받은 배열의 분리된 series SHA-256 — 2026-11-06

기준 `9f623fd9`에서 [series digest 함수](../../core/quant/run_registry_series_hash.py)를 추가한 ⑨-3a/series-digest/1 범위입니다. 승인된 R3 §5.7의 dtype·shape·원시 배열 바이트를 해시하는 부분이며, 아래 바이트 framing은 이번에 명시한 새 v1 구현 규칙입니다. 설계 원문에 같은 framing이 이미 정해졌거나 과거 저장 파일·series_ref와 호환됨을 확인한 기록이 아닙니다.

| 항목 | 확인한 동작과 한계 |
| --- | --- |
| 새 v1 조합 | `quantgen.r3.series/1` + NUL + `<f8` + NUL의 25바이트 헤더, 행/열 크기 각각 unsigned little-endian 8바이트, little-endian float64의 논리 C 순서 바이트를 연결해 소문자 64자리 SHA-256 반환. 고정 framing은 41바이트이며 JSON·끝 LF·파일명·`.npy` 머리말·날짜/기호/시각/공급자 메타데이터를 추가하지 않음 |
| 지원 입력 | 정확히 2차원인 일반 `numpy.ndarray` float64와 dtype metadata 없음만 허용. 빈 metadata mapping도 거부. 다른 rank/dtype·list·coercion 객체·subclass/masked/memmap 객체는 변환하지 않고 거부. 0길이 축은 shape를 포함한 해시 입력으로만 허용하며 유효한 저장 series·완료 실행·연구 적격성을 뜻하지 않음. 날짜 열·설정 ID·PnL·가격·열 의미를 추정/검증하지 않음 |
| 원시 비트·입력 보존 | 양 endian·C/F·음수/비단위/0 stride·읽기 전용·유효한 비정렬 버퍼를 지원. 정수 word view/변환으로 byte order만 맞추며 signed zero·무한대·quiet/signalling NaN payload와 논리 행/열 순서를 보존. 입력 바이트·shape·dtype·stride·쓰기 가능 상태를 변경하지 않음. 호출자가 입력을 안정되게 유지해야 하며 정확한 ndarray 타입이 backing buffer 출처·동시 수정 snapshot·자원 한도·보안 sandbox를 보장하지 않음 |
| 효과·증거 한계 | 함수 자체의 파일/네트워크/설정/환경/시계 조회·저장 없음. SHA-256만으로 출처·저작자·이용권·소유자 승인·공급사/가격 정확성·날짜 순서·연구 유효성을 입증하지 않음. 이후 저장기/읽기기는 같은 framing 채택과 검증을 별도로 확정해야 하며 현재 파일·기존 data MD5/source hash/keys/codec/store를 변경·이전하지 않음 |
| 합성 검증 | [유지 검사](../../tests/run_registry_series_hash_acceptance.py) 15개·0.011초, 독립 검사 11개·0.008초가 각각 종료 코드 0으로 통과. root의 series 15개+source 8개+data 15개+keys 13개+store 16개+codec 17개 통합 84개도 1.469초·종료 코드 0이며 서로 겹쳐 합산하지 않음. NumPy/새 함수를 쓰지 않고 미리 준비한 15개 원시 바이트 예제는 제품 검사 15회가 아님. memmap 거부 사례는 새 임시 파일만 사용. 이 하위 작업의 실패 실행은 없었으며 모두 로컬 Linux 합성 근거로 새 최종 head 전체 CI·실제 사용자 Windows/API 검증을 대신하지 않음 |

[제품 범위·검증 기록](../product/R3_DETACHED_SERIES_HASH_2026-11-06.md)에 따라 01–20 번호 정책은 유지합니다. series 저장/읽기·pickle 거부·재해시·원자 쓰기·중복/손상 파일/재시도·series_ref·recorder/Lab·수명주기·횟수/판정·실제 원장·동결 연구·상위 R3 완료는 이 함수로 구현하거나 추정하지 않습니다. 기존 사실/실패 이력과 `review-required`·공개 준비 `BLOCKED`, 운영자/법률/계약/라이선스/동의·실제 API/공급사/Windows 사용자 검증·파일럿·게시/배포 조건 및 선택적 GPT/Gemini 추가 심사 `NOT_PERFORMED`를 유지합니다.
