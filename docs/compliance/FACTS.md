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
| AI 해설 | Anthropic으로 계산 요약과 질문을 전송한다. 구조화된 private 필드 제거는 자유 입력 개인정보의 탐지·삭제를 보장하지 않는다. | [분석 전송](../../core/quant/insights.py) `deep_analysis`, [필드 필터](../../core/research/ai_payload.py) |
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

| 항목 | 사실 | 근거 |
| --- | --- | --- |
| 화면 | 시장 탭을 자산별 9개로 바꾸고 별도 “KIS chart” 탭을 없앰. 차트는 국내증권·해외증권·국내파생상품·해외파생상품·채권 탭 안에서 하나의 차트가 자산에 맞춰 이동. 시장 화면의 데이터 출처·곡선 출처 선택 상자를 숨기고 첫(자동) 값을 유지. Macro v2의 선택은 공급사가 아니라 기록 묶음이라 “기록 묶음”으로 표시 | [앱](../../quantgen_desktop/app.py), [도구 화면](../../quantgen_desktop/tools.py) |
| 공급사 선택 | KIS를 먼저 단독 조회. 실패·미설정·쓸 수 없는 자료(봉 2개 미만, 다른 종목, 순서·가격 오류)면 준비된 대체 공급사에 동시에 요청하고 첫 유효 응답을 표시. 합성 자료는 참여하지 않음. 마감 12초 뒤 늦은 응답은 버림(데몬 스레드) | [자동 선택](../../core/market/routing.py) |
| 대체 범위 | Yahoo Finance: 국내주식(.KS→.KQ), 미국(NAS/NYS/AMS)·홍콩·일본·중국 주식의 일·주·월봉, 수정 전 OHLC, 지연 시세. 선물·옵션·채권·분봉·틱·초봉은 KIS만 | [자동 선택](../../core/market/routing.py) |
| 표시 | 대체 응답은 출처·시도한 공급사(상태·예외 종류·미설정 변수 이름)를 표시하고 KIS 체결 스트림·5초 반복 조회·Q-SCORE에 쓰지 않음 | [차트 화면](../../quantgen_desktop/market_chart.py) |
| 범위 밖 | 시장지표 표(UI-7)·해외 종목명 검색·휠 확대(UI-16)는 후속 PR. 분석 도구의 기존 자동 경로(FRED·yfinance 실패 시 합성 표시)는 바꾸지 않음. Yahoo 표시 권리는 `rights_replace` 그대로 | [이용 조건 검토](../product/MARKET_DISPLAY_RIGHTS_2026-10-31.md) |

## 해외 종목명 검색·휠 확대·출처 두 줄 — 2026-11-03

| 항목 | 사실 | 근거 |
| --- | --- | --- |
| 종목 검색 | 해외증권은 이름·코드로 검색(한영·한글 초성). 목록은 앱에 포함된 126개 선별 종목(나스닥·NYSE·NYSE Arca/American·홍콩·도쿄)이며 시장 전체 목록이 아님. 검색은 로컬이며 고른 뒤에만 조회 | [검색](../../core/market/symbols.py), [목록](../../core/market/data/overseas_symbols.json) |
| 입력 정리 | 거래소·조회 봉 수·표시 봉 수 입력 제거. 거래소는 검색 결과로 정해지고, 국내파생상품만 시장 구분 선택을 보임. 기본 240봉 조회·120봉 표시 | [차트 화면](../../quantgen_desktop/market_chart.py) |
| 확대 | 차트 위 휠과 `+`/`-` 키로 표시 봉 수를 20봉~받은 봉 수 사이에서 바꿈. 다시 조회하지 않음 | [차트 화면](../../quantgen_desktop/market_chart.py) |
| 출처 표시 | 출처·지연 한 줄, 조회·체결 시각(한국시간) 한 줄, 같은 글자 크기. 긴 공급자 설명은 “데이터 설명” 펼침과 tooltip으로 이동 | [차트 화면](../../quantgen_desktop/market_chart.py) |

## 시장 지표 차트 4개 — 2026-11-03

| 항목 | 사실 | 근거 |
| --- | --- | --- |
| 화면 | 시장 화면의 7열 시장지표 표·새로고침 버튼·단위 안내를 지표 선 차트 4개(코스피, S&P 500, 원/달러 환율, 미국 10년 국채금리)로 교체. 개별 종목 없음(종목은 Home 목록·Q-SCORE에 그대로). 넓으면 2×2, 700px 미만이면 한 줄 | [보드](../../quantgen_desktop/market_board.py) |
| 공급사 | 카드마다 KIS 먼저(코스피 지수·S&P 500 해외지수·원/달러), 실패·미설정이면 Yahoo·FRED 동시 요청·첫 유효 응답. 미국 10년은 FRED. 합성 자료 없음 | [보드 자료](../../core/research/market_board.py), [자동 선택](../../core/market/routing.py) |
| 갱신 | 시장 화면이 보일 때만, KIS 카드 3분·지연 공급사 15분 간격, 실패 카드는 1·2·5·15분 간격 재시도. 자체 작업 큐라 분석 도구를 막지 않음. 실패한 갱신은 마지막 정상 값을 유지 | [보드](../../quantgen_desktop/market_board.py) |
| 표시 | 값·등락(%, 금리는 bp)·선 차트·출처/지연 한 줄·관측일/갱신 시각 한 줄. 7일 넘은 관측은 “오래된 관측” | [카드 차트](../../core/market/presentation.py) |

