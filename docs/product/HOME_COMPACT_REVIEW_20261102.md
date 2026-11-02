# Home compact 변경과 정책 20종 대조

검토일: 2026-11-02 한국시간. compact 작업 기준: `ead6e67`. 최종 검토는 작업 체크포인트 `19c663c`에 main `f673f37`(PR54/58)을 통합한 뒤, PR61 구현 `6925bbdd`에 최신 main `8b40104`(PR59)를 추가 통합한 작업 트리를 포함합니다. 검토 주체: Codex `completion_audit`.

이 검토는 네이티브 Home 목록·Q-SCORE 소개·차트 접근 경로의 소스와 정책 정합성을 확인합니다. 실제 KIS 연결·예측력·공개 승인·접근성 인증·AWS 배포를 확인한 기록이 아닙니다. 모든 정책의 `review-required`와 공개 준비 `BLOCKED`를 유지합니다.

## 변경 사실과 보존한 근거

| 변경 | 소스에서 확인한 범위 | 바꾸지 않은 의미 |
|---|---|---|
| Home 밀도 | 행 높이64px→44px, 기존 동봉 글꼴의 크기·굵기 위계 정리 | 출처·시각·상태·시세·상세 수치 및 점수 유지. 새 글꼴 다운로드·새 데이터 수집 아님 |
| 중복 버튼 제거 | Home 위쪽의 별도 실시간 차트 바로가기를 제거 | 종목 행·상세→기존 차트 경로 유지. 차트 기능·명시적 연결을 제거하거나 자동 주문을 추가하지 않음 |
| 열 제목의 도움말 | Q-SCORE 헤더 안22px `?` 실제 버튼, hover 요약과 클릭·Enter/Space로 여는 스크롤 본문. 열 이동·가로 스크롤·포커스에 맞춘 위치 제어 | 마우스 tooltip만으로 의미를 전달하지 않음. 새 작은 제어의 실제 Windows DPI·스크린리더 검증은 별도 |
| 한영 소개 | 수정 이력·시각·가격 기준을 확인한 뒤 기술신호·위험분석으로 추세·모멘텀·변동성·하락 위험을 함께 살피고 유효 체결에 따라 갱신하는 의미 | 기존 엔진 두 경로를 실제 호출하는 범위. 모든 모델·기업가치·검증된 예측력·수익 보장을 주장하지 않음 |
| 화면의 수식 생략 | 사용자 요청에 따라 가중치·환산식·별 경계 숫자를 UI 소개에서 생략 | 실제 `compute_q_score`와 내부 방법론은 그대로. 실험적 지표·예측력 미검증·사용상 한계는 한영 유지 |

근거: [Home](../../quantgen_desktop/app.py), [표·헤더·소개](../../quantgen_desktop/watchlist.py), [Q-SCORE](../../core/research/qscore.py), [경로 회귀 검사](../../tests/desktop_market_layout_acceptance.py). 앱은 기존 `assets/fonts/qg-interface.otf`를 로드하며 이번 변경에 새 글꼴 자산이나 라이선스를 추가하지 않습니다.

프리뷰에서 긴 영문 종목명이 두 줄 높이를 필요로 하는데 한 줄 높이만 받아 잘리는 문제를 발견했습니다. 실제 동봉 글꼴에서는38px가 필요하므로 이름 라벨의 세로 확장과 padding 조정으로39px를 확보하고 실제 필요 높이를 비교하는 회귀 검사를 추가했습니다. 44px 행 전체를 키우거나 이름을 삭제하는 방식으로 처리하지 않았습니다. 중지된 영문 점수의 두 줄 표시도 동봉 글꼴과 실제 item 내용 높이를 대조하는 회귀 검사를 통과했습니다. 빈 관측의 한국어 상태는 실제 의미에 맞게 `자료 없음`으로 표시합니다.

내부 수치 산식·표본·보수적 거부 경계는 [앞선 방법론 기록](HOME_LIVE_QSCORE_REVIEW_20261102.md)과 [주장 근거 정책](../compliance/12-claims.md)에 보존합니다. 도움말을 간결하게 만든 사실이 내부 검토 근거를 삭제하거나 계산 성능을 개선했다는 의미는 아닙니다. 소스상 시간·가격 기준 검사가 엔진 계산보다 앞에 실행되므로 한영 소개의 단계 순서도 이에 맞춰 대조했습니다.

`core/research/qscore.py`를 기준 커밋과 AST로 비교하여 `q_score_help`를 제외한 코드가 같은 것을 확인했습니다. 문구 변경을 새 분석 엔진 구현·가중치 보정·예측 성능 개선으로 설명하지 않습니다.

## 시장자료 실패의 표시

`core/research/markets.py`는 기존에 묶어서 표시하던 실패를 허용된 코드로 분류하고 `watchlist.py`가 그대로 전달합니다. 확인 가능한 예외 클래스·HTTP 상태·관측 수만 근거로 삼습니다. 원문 예외 텍스트는 최대1500자를 실행 중에만 살펴보고 UI용 데이터에는 코드만 보냅니다. 새 로그 파일·외부 진단 전송·공급자·캐시·조회 횟수나 폴백을 추가하지 않습니다.

분류는 패키지 누락/호환 문제, 미설정, 호출 제한, timeout/연결/인증서 오류, 접근 거부, 자료 없음/부족, 잘못된 응답, 미확인 공급자 실패입니다. Yahoo가 빈 프레임을 반환한 경우는 `no_observations`로 표시하며, 그 사실만으로 호출 제한·KIS 인증·사용자 PC 네트워크 문제를 확정하지 않습니다. 설치된 yfinance의 예외가 빈 응답으로 소실될 수 있다는 소스 설명과 실제 사용자 환경의 원인 진단은 별개입니다.

KIS 필수 가격이 없으면 자료 없음으로 유지하고 선택 OHLC·거래량 등 빈 항목만으로 유효한 가격을 버리지 않습니다. 관측은 유한해도 변화율 계산이 무한대이면 `invalid_response`로 처리합니다. 자료 부재를 0·합성 값·다른 제공자 자료로 채우지 않습니다. 근거: [분류와 관측 검사](../../core/research/markets.py), [Home 목록 조회](../../core/research/watchlist.py), [주입 회귀 검사](../../tests/home_watchlist_acceptance.py).

## 정책 20종을 대조한 결과

compact 작업 시작 때의20종 원문·양식은 직전 [Home 검토](HOME_LIVE_QSCORE_REVIEW_20261102.md)에서 읽은 파일과 모두 바이트 단위로 같음을 확인했습니다. 이후 main 통합으로 정책 본문·근거가 추가 보완되었으므로 이 초기 동일성 확인을 최종 파일 전체가 같다는 주장으로 사용하지 않습니다. 아래 표는 각 정책에 대한 **compact 변경의 추가 영향**이며, main의 별도 전송·보관·권리·접근성 보완은 다음 절에서 함께 대조합니다. 가격·VAT·자동 갱신·인원·환불·사업자 정보는 이 compact 변경으로 수정하지 않았습니다.

| 문서 | compact 추가 조치와 이유 |
|---|---|
| [01 개인정보](../compliance/01-privacy-policy.md) | 유지: compact 표시·로컬 소개에 새 개인 항목·수신자·계좌·전송·파일 쓰기 없음 |
| [02 약관](../compliance/02-terms-of-service.md) | 유지: 기존 연구·표·가이드·실험 점수 범위와 권리·계약을 바꾸지 않음 |
| [03 환불](../compliance/03-refund-policy.md) | 유지: 결제·해지·환불 처리나 법정 권리·기존 가격 조건 변경 없음 |
| [04 쿠키](../compliance/04-cookie-policy.md) | 유지: 새 방문자 쿠키·웹 추적·저장기술 없음. 공급사 세션과 브라우저 저장의 기존 구분 유지 |
| [05 쿠키 동의](../compliance/05-cookie-consent.md) | 유지: 배너·선택 저장·철회 경로 변경 없음 |
| [06 폼 동의](../compliance/06-form-consent.md) | 유지: 도움말은 로컬 설명. 기존 Home 자동 REST·명시적 실시간·별도 차트 조회 범위 유지 |
| [07 최소화](../compliance/07-data-minimization.md) | 유지: 고정 목록·시장 이력·메모리 점수 범위와 캐시 한도를 변경하지 않음 |
| [08 외부 SDK](../compliance/08-third-parties.md) | 유지: 같은 KIS/FRED/yfinance·Qt·NumPy 사용. 새 공급자·의존성·상업 이용권 추가 없음 |
| [09 선택권](../compliance/09-dark-patterns.md) | 갱신: UI 도움말에 공식·가중치 전체를 표시한다는 이전 계약을 실제 기능 소개로 수정. 내부 근거·해석 한계 보존 |
| [10 요금](../compliance/10-pricing.md) | 유지: 서비스 요금·외부 데이터 비용 포함 범위·갱신 조건 변경 없음 |
| [11 후기](../compliance/11-testimonials.md) | 유지: 계산 별점은 여전히 고객 평가·추천·실현 성과가 아님. 후기 수집 없음 |
| [12 주장](../compliance/12-claims.md) | 갱신: 실제 엔진·검사 단계에 근거한 한영 소개, 수식의 내부 보존, KIS 설정 발견과 실제 수신의 구별. 빈 자료·알려진 오류와 미확인 장애 원인을 구분 |
| [13 대체 정보](../compliance/13-alternative-text.md) | 갱신: 헤더의 실제 버튼·짧은 hover·키보드 소개 본문과 작은 행의 텍스트·상세 경로 |
| [14 대비](../compliance/14-contrast.md) | 갱신: 행·글꼴 크기·작은 도움말 제어 변경의 대비·확대 검증 범위. 기존 팔레트 재사용을 인증으로 확대하지 않음 |
| [15 키보드](../compliance/15-keyboard.md) | 갱신: 헤더 도움말 포커스·가로 스크롤·Enter/Space와 종목 상세→차트 여정 |
| [16 사업자](../compliance/16-business-information.md) | 유지: 사업자·번호·연락처·호스팅 조건 새 확정 없음 |
| [17 아동](../compliance/17-children.md) | 유지: 연령·보호자·미성년 계약 처리 변경 없음 |
| [18 광고메일](../compliance/18-marketing-email.md) | 유지: 광고 동의·주소 수집·발송·수신거부 처리 변경 없음 |
| [19 권리](../compliance/19-licenses.md) | 유지: 기존 브랜드·동봉 글꼴·SDK·데이터 제공자 재사용. 권리 확인 완료로 승격하지 않음 |
| [20 삭제](../compliance/20-deletion.md) | 유지: 추가 저장·삭제·철회·보유기간 변경 없음. 연결 중지와 전체 삭제의 기존 구분 유지 |

09/12/13/14/15의 버전을 갱신하고 [FACTS](../compliance/FACTS.md)에 후속 사실을 반영했습니다. 원본 버전 변경을 별도 웹 Docs HTML의 번역 완료나 배포로 처리하지 않습니다.

## 최신 main 통합의 추가 대조

main `f673f37`의 정책01/06/07/08/12/13/14/15/19/20, FACTS, RELEASE_GAPS 및 근거 문서를 읽고 compact 절과 함께 보존했습니다. 기존 baseline을 과거 compact 기준으로 되돌리지 않고 main의 `source-review.json`을 충돌 해소의 출발점으로 사용합니다. 아래는 main의 이미 기록된 검토를 통합 확인한 범위이며 새 시장 실험이나 법률 검토를 수행했다는 뜻이 아닙니다.

| main 보완 | 확인·보존한 근거와 경계 |
|---|---|
| KIS 전송·선택·보관 | [KIS20종 통합 검토](KIS_SOURCE_DOCUMENT_REVIEW_2026-11-02.md), FACTS의 승인 발급 POST·비TLS WS·23시간 재사용·Flet 별도 REST 중지·전역 캐시와 삭제 구분, 정책01/06/07/08/20의 표·양식 보강 |
| KIS 표현·접근성·권리 | 정책12–15의 구독 승인과 실제 체결 구분·부분 이력·최신 지표·대체 정보 한계·최종 SVG 대비 수치·실제 보조기술 미검증, 정책19의 지정 환경 websockets16.0·과거16.1.1 기록·선언 밖17.3 구분·상업 표시권 미확정 |
| 금융 결과 해석 | [FX CIP 차이](FX_CIP_DISCREPANCY_2026-11-02.md), [CMS 첫 기간 쿠폰](CMS_COUPON_DISCLOSURE_2026-11-02.md), [5y5y 단리 규약](FORWARD_CONVENTION_2026-11-02.md), [Signals 체결 횟수](SIGNALS_TRADE_COUNTS_2026-11-02.md)의 조건·기간·gross/실행 의미와 기존 NOT_RUN·연구 원장 경계 |
| LETF 가정 | [명시적 가정](LETF_ASSUMPTIONS_2026-11-02.md)의 사용자 가정·기존 ZERO_RATE_REFERENCE·비교기준·자금/보수/배당 기여도·선택적 기존 AI/보고서 metadata, 새 전송처·원장·실제시장 검증 없음 |
| 앱 구동·언어·배치 | [앱 구동 검증](APP_ACCEPTANCE_2026-11-02.md)의 잘못된 locale 복구·기존 QSettings·원문/수치 보존·현재 탭 기준 높이·주입 Flet/설치 wheel 범위. 자동 CI와 실제 Windows 실기기 수용 구분 |

main이 추가한 정책 문장들을 통합 파일에 대조했습니다. compact 요구로 명시적으로 바꾼09번의 수식 전시 약속과 버전 metadata를 제외하고 새 main 정책 문장이 유지됩니다. compact 대상 버전은09번1.4, 12번1.6, 13/14/15번1.5이며 나머지는 최신 main 버전을 유지합니다. 모두 `review-required`입니다. main에서 `core.quant.signals`·`core.quant.risk` 변경은 없으며 compact Q-SCORE의 실제 산식·입력 경계 보존과 충돌하지 않습니다.

### PR59 금리 재평가 입력 일관성 추가 통합

최신 main `8b40104`의 [금리 재평가 검토](RATES_REVALUATION_PARAMS_2026-11-02.md), `core/ficc/ratesim.py`·`core/research/rates_analysis.py`·Flet 호출 및 회귀검사·CI 변경을 대조했습니다. 기간말 재평가에 전달한 model·kappa·theta·sigma·r0가 실제 `sim.params`와 정확히 다르면 가격 계산 전에 필드명을 명시해 거부하며 note만의 차이는 허용합니다. Hull–White의 기존 r0 정규화 이후 값을 넘기도록 호출부를 맞췄고, 정상 입력 수치·규약을 새로 정의하거나 다른 파라미터로 기존 경로를 재평가하는 기능을 추가하지 않습니다.

자동 병합된06번 입력·동의 구분, 12번 불일치 거부/검증 한계와 주장 대장, FACTS의 M3-N08 절을 compact 내용과 함께 보존했습니다. 20종 정책 범위와 다시 대조한 결과 새 개인정보·전송처·선택적 AI 범위·권리·요금·운영자·저장·삭제·접근성 계약 변경은 없으며 기존 미확정 상태를 유지합니다. main 문서에 기록된 합성10개 검사·이전 버전 수치 일치 기록은 기존 검토 증거이며 이 정책 검토자가 새로 실행했다고 표시하지 않습니다. 이번 단계에서도 최신 main baseline을 출발점으로 전체 통합 지문을 갱신합니다.

## 실제 환경 증거와 검증 범위

- 사용자 실행에서 `KIS_SETTINGS_FOUND=True`를 확인했습니다. 이는 설정 발견이며 실제 거래시간대의 KIS 시세 인증·구독·체결 수신 성공 증거가 아닙니다.
- Yahoo의 S&P 500·KOSPI·Bitcoin 일별 자료는 KIS 인증과 독립입니다. 이 세 행의 실패를 KIS 설정 문제라고 단정하지 않으며 실제 사용자 PC의 공급자 실패 원인은 추가 증거 없이 확정하지 않습니다.
- 새 UI의 Qt offscreen·주입 키·레이아웃 검사는 실제 Windows DPI·전 화면 Tab·스크린리더·모바일 웹이나 AWS 배포 검증과 구분합니다.
- 최종 코드 고정 전에는 `source-review.json`을 갱신하지 않았습니다. 긴 영문 이름·자료 없음 문구를 포함한 최종 소스를 대조하고 주 작업자의 코드 고정 통지 이후 20종 기준선을 갱신합니다. 정책 정합성·회귀 검사 결과는 실행한 모듈과 범위별로 기록하며 서로 겹치는 실행 수를 합산하지 않습니다.

## 검증 기록

| 실행 주체·명령 또는 범위 | 확인한 결과 |
|---|---|
| 검토자: `python -m unittest tests.compliance_acceptance tests.compliance_export_acceptance` | PR59까지의 main 통합·최종 UI 수정 후47개 통과, 6.076초. 실행기는 `/workspace/.venvs/quantgen/bin/python` |
| UI 담당자: `MPLCONFIGDIR=/tmp/quantgen-mpl QT_QPA_PLATFORM=offscreen /workspace/quantgen-compat-venv/bin/python -m unittest -q tests.desktop_watchlist_acceptance` | 최종15개 통과, 9.032초. 실제 동봉 글꼴의 긴 영문 이름·중지 점수 두 줄, 헤더 도움말·안전한 오류 표시 포함 |
| 주 작업자: `tests.qscore_acceptance` + `tests.desktop_market_layout_acceptance` | 12개 통과 보고. 한영 소개·기존 계산·종목 상세에서 차트 접근 범위 |
| 데이터 담당자: Home 목록15개와 기존 시장 계약2개 | 17개 통과 보고. Yahoo 빈/정상 MultiIndex 응답·패키지 누락·FRED 독립 유지·비밀 원문 비노출·KIS 선택 항목 빈값·무한 변화율 거부 |
| 주 작업자: Home 통합·점수 제어 검사 | 14개 통과 보고. 시세·점수의 기존 연결/중지 계약 |
| 검토자: 문서 링크·정책 상태·Q-SCORE AST 대조·diff 검사 | 깨진 로컬 링크 없음, 20종 모두 review-required, 도움말 이외 계산 코드 동일. compact diff 및 CRLF 허용 staged diff 공백 검사 통과 |
| 검토자: `python -m tools.compliance.check --check --report-dir /tmp/qg-compact-compliance` | 정합성 PASS, 문서20종·소스523개, 공개 준비 BLOCKED |

이는 코드·주입 자료·Qt offscreen 검증입니다. 실제 사용자 키·실시간 시세 복구·새 Windows 화면의 모든 접근성·소개사이트 배포를 통과로 보고하지 않습니다. 정책 정합성 검사 결과는 별도 `/tmp/qg-compact-compliance` 보고서에서 확인하며 정합성 통과가 공개 준비 `BLOCKED`를 해제하지 않습니다.

UI 담당자의 최종 스크린샷은 `/tmp/quantgen-compact-FINAL-fixture-ko-light-1360.png`와 `/tmp/quantgen-compact-FINAL-fixture-en-dark-1000-right.png`입니다. 결정적인 테스트 시세를 넣은 렌더링 증거이며 실제 사용자 시세로 소개하지 않습니다.

main에서 가져온 일부 기존 소스는 CRLF이므로 일반 staged `git diff --check`가 줄 끝 CR을 공백으로 표시했습니다. 무관한 소스를 재포맷하지 않고 `git -c core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol diff --cached --check`로 확인해 통과했습니다. 정책 점검기의 기존 줄바꿈 정규화 규칙을 바꾸지 않았습니다.
