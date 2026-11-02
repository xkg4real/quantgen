# Home 종목 정보·Q-SCORE·타이포그래피와 정책 20종 대조

검토일: 2026-11-02 한국시간. compact 작업 기준: `ead6e67`. 검토는 작업 체크포인트 `19c663c`에 main `f673f37`(PR54/58)을 통합한 뒤, PR61 구현 `6925bbdd`에 main `8b40104`(PR59)를 통합한 이력과, `5b52e3d` 이후 종목 정보·글꼴 확장 작업 트리를 구분합니다. 검토 주체: Codex `completion_audit`.

이 검토는 네이티브 Home 목록·Q-SCORE 소개·차트 접근 경로의 소스와 정책 정합성을 확인합니다. 실제 KIS 연결·예측력·공개 승인·접근성 인증·AWS 배포를 확인한 기록이 아닙니다. 모든 정책의 `review-required`와 공개 준비 `BLOCKED`를 유지합니다.

## 초기 compact 변경 사실과 보존한 근거

| 변경 | 소스에서 확인한 범위 | 바꾸지 않은 의미 |
|---|---|---|
| Home 밀도 | 행 높이64px→44px, 기존 동봉 글꼴의 크기·굵기 위계 정리 | 출처·시각·상태·시세·상세 수치 및 점수 유지. 새 글꼴 다운로드·새 데이터 수집 아님 |
| 중복 버튼 제거 | Home 위쪽의 별도 실시간 차트 바로가기를 제거 | 종목 행·상세→기존 차트 경로 유지. 차트 기능·명시적 연결을 제거하거나 자동 주문을 추가하지 않음 |
| 열 제목의 도움말 | Q-SCORE 헤더 안22px `?` 실제 버튼, hover 요약과 클릭·Enter/Space로 여는 스크롤 본문. 열 이동·가로 스크롤·포커스에 맞춘 위치 제어 | 마우스 tooltip만으로 의미를 전달하지 않음. 새 작은 제어의 실제 Windows DPI·스크린리더 검증은 별도 |
| 한영 소개 | 수정 이력·시각·가격 기준을 확인한 뒤 기술신호·위험분석으로 추세·모멘텀·변동성·하락 위험을 함께 살피고 유효 체결에 따라 갱신하는 의미 | 기존 엔진 두 경로를 실제 호출하는 범위. 모든 모델·기업가치·검증된 예측력·수익 보장을 주장하지 않음 |
| 화면의 수식 생략 | 사용자 요청에 따라 가중치·환산식·별 경계 숫자를 UI 소개에서 생략 | 실제 `compute_q_score`와 내부 방법론은 그대로. 실험적 지표·예측력 미검증·사용상 한계는 한영 유지 |

근거: [Home](../../quantgen_desktop/app.py), [표·헤더·소개](../../quantgen_desktop/watchlist.py), [Q-SCORE](../../core/research/qscore.py), [경로 회귀 검사](../../tests/desktop_market_layout_acceptance.py). 이 초기 단계는 당시 `assets/fonts/qg-interface.otf`를 사용했습니다. 아래 후속 단계의 Pretendard 교체와 별도이며, 이전 글꼴로 확인한 치수를 새 글꼴의 검증 결과로 재사용하지 않습니다.

프리뷰에서 긴 영문 종목명이 두 줄 높이를 필요로 하는데 한 줄 높이만 받아 잘리는 문제를 발견했습니다. 실제 동봉 글꼴에서는38px가 필요하므로 이름 라벨의 세로 확장과 padding 조정으로39px를 확보하고 실제 필요 높이를 비교하는 회귀 검사를 추가했습니다. 44px 행 전체를 키우거나 이름을 삭제하는 방식으로 처리하지 않았습니다. 중지된 영문 점수의 두 줄 표시도 동봉 글꼴과 실제 item 내용 높이를 대조하는 회귀 검사를 통과했습니다. 빈 관측의 한국어 상태는 실제 의미에 맞게 `자료 없음`으로 표시합니다.

내부 수치 산식·표본·보수적 거부 경계는 [앞선 방법론 기록](HOME_LIVE_QSCORE_REVIEW_20261102.md)과 [주장 근거 정책](../compliance/12-claims.md)에 보존합니다. 도움말을 간결하게 만든 사실이 내부 검토 근거를 삭제하거나 계산 성능을 개선했다는 의미는 아닙니다. 소스상 시간·가격 기준 검사가 엔진 계산보다 앞에 실행되므로 한영 소개의 단계 순서도 이에 맞춰 대조했습니다.

`core/research/qscore.py`를 기준 커밋과 AST로 비교하여 `q_score_help`를 제외한 코드가 같은 것을 확인했습니다. 문구 변경을 새 분석 엔진 구현·가중치 보정·예측 성능 개선으로 설명하지 않습니다.

## 시장자료 실패의 표시

`core/research/markets.py`는 기존에 묶어서 표시하던 실패를 허용된 코드로 분류하고 `watchlist.py`가 그대로 전달합니다. 확인 가능한 예외 클래스·HTTP 상태·관측 수만 근거로 삼습니다. 원문 예외 텍스트는 최대1500자를 실행 중에만 살펴보고 UI용 데이터에는 코드만 보냅니다. 새 로그 파일·외부 진단 전송·공급자·캐시·조회 횟수나 폴백을 추가하지 않습니다.

분류는 패키지 누락/호환 문제, 미설정, 호출 제한, timeout/연결/인증서 오류, 접근 거부, 자료 없음/부족, 잘못된 응답, 미확인 공급자 실패입니다. Yahoo가 빈 프레임을 반환한 경우는 `no_observations`로 표시하며, 그 사실만으로 호출 제한·KIS 인증·사용자 PC 네트워크 문제를 확정하지 않습니다. 설치된 yfinance의 예외가 빈 응답으로 소실될 수 있다는 소스 설명과 실제 사용자 환경의 원인 진단은 별개입니다.

KIS 필수 가격이 없으면 자료 없음으로 유지하고 선택 OHLC·거래량 등 빈 항목만으로 유효한 가격을 버리지 않습니다. 관측은 유한해도 변화율 계산이 무한대이면 `invalid_response`로 처리합니다. 자료 부재를 0·합성 값·다른 제공자 자료로 채우지 않습니다. 근거: [분류와 관측 검사](../../core/research/markets.py), [Home 목록 조회](../../core/research/watchlist.py), [주입 회귀 검사](../../tests/home_watchlist_acceptance.py).

## 초기 compact 정책 20종 대조

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

main이 추가한 정책 문장들을 통합 파일에 대조했습니다. compact 요구로 명시적으로 바꾼09번의 수식 전시 약속과 버전 metadata를 제외하고 새 main 정책 문장이 유지됩니다. 이 단계의 버전은09번1.4, 12번1.6, 13/14/15번1.5였으며 아래 종목 정보·글꼴 확장에서 해당 문서와07/08/19번을 추가 갱신합니다. 모두 `review-required`입니다. main에서 `core.quant.signals`·`core.quant.risk` 변경은 없으며 compact Q-SCORE의 실제 산식·입력 경계 보존과 충돌하지 않습니다.

### PR59 금리 재평가 입력 일관성 추가 통합

최신 main `8b40104`의 [금리 재평가 검토](RATES_REVALUATION_PARAMS_2026-11-02.md), `core/ficc/ratesim.py`·`core/research/rates_analysis.py`·Flet 호출 및 회귀검사·CI 변경을 대조했습니다. 기간말 재평가에 전달한 model·kappa·theta·sigma·r0가 실제 `sim.params`와 정확히 다르면 가격 계산 전에 필드명을 명시해 거부하며 note만의 차이는 허용합니다. Hull–White의 기존 r0 정규화 이후 값을 넘기도록 호출부를 맞췄고, 정상 입력 수치·규약을 새로 정의하거나 다른 파라미터로 기존 경로를 재평가하는 기능을 추가하지 않습니다.

자동 병합된06번 입력·동의 구분, 12번 불일치 거부/검증 한계와 주장 대장, FACTS의 M3-N08 절을 compact 내용과 함께 보존했습니다. 20종 정책 범위와 다시 대조한 결과 새 개인정보·전송처·선택적 AI 범위·권리·요금·운영자·저장·삭제·접근성 계약 변경은 없으며 기존 미확정 상태를 유지합니다. main 문서에 기록된 합성10개 검사·이전 버전 수치 일치 기록은 기존 검토 증거이며 이 정책 검토자가 새로 실행했다고 표시하지 않습니다. 이번 단계에서도 최신 main baseline을 출발점으로 전체 통합 지문을 갱신합니다.

## 실제 환경 증거와 검증 범위

- 사용자 실행에서 `KIS_SETTINGS_FOUND=True`를 확인했습니다. 이는 설정 발견이며 실제 거래시간대의 KIS 시세 인증·구독·체결 수신 성공 증거가 아닙니다.
- Yahoo의 S&P 500·KOSPI·Bitcoin 일별 자료는 KIS 인증과 독립입니다. 이 세 행의 실패를 KIS 설정 문제라고 단정하지 않으며 실제 사용자 PC의 공급자 실패 원인은 추가 증거 없이 확정하지 않습니다.
- 새 UI의 Qt offscreen·주입 키·레이아웃 검사는 실제 Windows DPI·전 화면 Tab·스크린리더·모바일 웹이나 AWS 배포 검증과 구분합니다.
- 최종 코드 고정 전에는 `source-review.json`을 갱신하지 않았습니다. 긴 영문 이름·자료 없음 문구를 포함한 최종 소스를 대조하고 주 작업자의 코드 고정 통지 이후 20종 기준선을 갱신합니다. 정책 정합성·회귀 검사 결과는 실행한 모듈과 범위별로 기록하며 서로 겹치는 실행 수를 합산하지 않습니다.

## 초기 compact 검증 기록 — 새 종목 정보·글꼴 변경 전

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

## 후속 종목 정보·글꼴 확장: 실제 계약

이 절은 PR61의 `5b52e3d` 이후 변경에 대한 추가 검토입니다. 별도 작업 트리에서 진행하는 차트 시간봉·실시간 UX 작업은 이 검토나 PR61 완료 범위에 포함하지 않습니다.

| 항목 | 확인한 소스·의미와 경계 |
|---|---|
| 10열 표 | 종목·가격·변동·거래량·시가총액·PER·EPS·업종·상세·Q-SCORE.44px 행을 유지하고 마지막 열에 점수/소개를 둠. 출처·관측/체결·수신 시각·상태·안전 오류 코드는 가격 hover/접근성 설명과 상세 버튼·행 Enter·더블클릭 본문으로 옮김 |
| 기존 KIS 응답 | `per`, `eps`, `bstp_kor_isnm`, `lstn_stcn`을 같은 `inquire-price` 응답에서 읽음. 필드가 없거나 잘못되면 해당 값만 비우고 유효 가격은 유지. 추가 endpoint·HTTP 호출·계좌·재무 파일·새 공급자·원격 번역·AI 입력 없음 |
| 시가총액 | 같은 응답의 KRW 가격×유효한 양의 정수 상장주수로 산출. `price_x_listed_shares` 기준을 표시. 원시 `hts_avls`의 단위는 여전히 `UNVERIFIED`이며 환산하거나 화면 수치로 사용하지 않음 |
| 산출값의 시각 | REST 가격의 실제 관측 시각이 없으므로 최초 cap 기준 시각은 미제공. 상장주수 수신일과 같은 KST 날짜의 유효 체결만 cap 재계산에 사용하며 그 체결 시각을 기록. 다른 날짜에는 이전 cap/기준 시각을 보존. 이는 상장주수 실시간 재검증·기업행위 보정 보장이 아님 |
| PER/EPS | 공급자 제공 유한0·음수는 보존하고 결측/잘못된 값은 `—`. TTM·연결/별도·희석·EPS 통화/주당 단위를 확인하지 못했으므로 단정하지 않음. `fundamentals_received_at`은 REST 수신이며 `fundamentals_as_of`는 미제공. 가격 tick으로 재무 시각을 바꾸지 않음 |
| 업종 | KIS 분류 원문. GICS나 새 분류 모델이 아님. 준비된 정확한 한영 대응 외에는 `Untranslated`와 상세 원문을 제공 |
| 표시·분석 경계 | Q-SCORE 계산식·실험 상태는 그대로. 종목 정보와 글꼴 변경을 새 AI 분석·가격 예측력·수익 성과·거래 권고로 설명하지 않음 |

직접 대조한 소스는 [KIS 현재가 파서](../../data/krx/kis_client.py), [Home 조회](../../core/research/watchlist.py), [표·상세·tick cap 갱신](../../quantgen_desktop/watchlist.py)입니다. [공식 KIS 예제의 고정 버전](https://github.com/koreainvestment/open-trading-api/blob/3a9be59a3ed8745720dc3aa9d584bdf3b7830362/examples_llm/domestic_stock/inquire_price/chk_inquire_price.py)의26·33·63·64·65·69행은 업종·현재가·상장주수·원시 시총·PER·EPS 필드 이름의 근거입니다. 이 목록에서 확인되지 않는 단위·회계기간·표시권을 추정하지 않습니다. API 호출 검사는 주입 응답이며 실제 사용자 계정이나 금융자료 기준일을 확인한 기록이 아닙니다.

### 글꼴 출처와 배포 경계

[글꼴 README](../../assets/fonts/README.txt), [현재 OFL](../../assets/fonts/OFL.txt), [이전 Noto 고지](../../assets/fonts/OFL-Noto-legacy.txt), [서브셋 도구](../../tools/ui/subset_font.py), [Qt 등록과 계층](../../quantgen_desktop/app.py)을 읽고 실제3개 파일과 대조했습니다. 현재 원본은 Pretendard1.3.9, 고정 commit `5c41199ea0024a9e0b2cb31735265056e5472d76`입니다. 라이선스의 Copyright2021 Kil Hyung-jin과 Reserved Font Name Pretendard를 보존하며, 수정본의 주 표시/typographic 가족·PostScript 이름은 QG Interface로 바꿉니다. 포함된 Copyright2023 메타데이터도 유지합니다. 실제 배포물에는 OFL·저작권·이름 조건을 포함해야 하며 독립 폰트 판매·권리자 보증 주장을 허용하지 않습니다.

| 동봉 파일 | 실제 굵기·바이트 | 직접 확인한 SHA256 |
|---|---|---|
| `qg-interface.otf` | 400 · 1,411,584 | `90aded599c3206a647c88f6a81bc5df670fdec6ff2d9c9f241de2d0bf64b6b31` |
| `qg-interface-medium.otf` | 500 · 1,420,644 | `f52aa3022d241b4cd03eb71f64a9389fc298760e057a317305312e24bb44fbbc` |
| `qg-interface-semibold.otf` | 600 · 1,420,648 | `97c53221c1d3fadc48d692fab9bf5a545159be95a5c0228dc3b8cc24db4ec8dd` |

각 파일은 한글11,172개와 `tnum` OpenType 기능을 포함합니다. Qt가3개 실제 굵기를 등록하고 제목28px/600·소제목17px/600·수치30px/500·본문13px/400·작은 설명12px로 조정합니다. 폰트 담당자의 QRawFont 대조는 실제 선택한 각 face의 CFF 바이트가 해당 파일과 같으며 `11111`/`88888` 폭39.921875px, regular 재생성 해시 일치, 런타임 HTTP0을 보고했습니다. 근거는 작업공간 `evidence/native-typography-20261102/typography-proof.json`이며 이 정책 검토자가 해당 렌더링 실행을 새로 수행한 것으로 기록하지 않습니다.

정책 검토자는 위3개 해시·크기·OS/2 굵기·이름·한글 문자 수·`tnum`을 별도로 직접 읽었습니다. `fontTools`는 빌드 도구이며 새 런타임 패키지·폰트 다운로드·시스템 설치를 추가하지 않습니다. 공유 Regular 파일 변경은 Flet 자산에도 해당하지만 Qt의 실제500/600 등록을 Flet·AWS 화면 배포로 확대하지 않습니다. `OFL.txt`22행의 끝 공백은 원본과 정확히 같은 라이선스를 보존하기 위한 기록이며 전체 저장소의 공백 검사 규칙을 완화하지 않습니다.

### 확장 후 정책 20종 재대조

기존에 읽은20종과 최신 main PR54/58/59 통합 원문을 기준으로 전체 변경 영향을 재대조했습니다. 이 확장에서 아래 유지12종은 `5b52e3d`와 바이트 단위로 같음을 직접 확인했고8종만 내용을 보강했습니다. 새 폰트 자산이 registry의 공통 재검토를 일으키므로 유지 문서도 검토에서 제외하지 않습니다.

| 문서 | 확장 후 조치와 근거 |
|---|---|
| 01 개인정보 | 유지: 시장 응답 재사용·로컬 글꼴 변경으로 개인 항목·수신자·계좌·고객 프로필 추가 없음 |
| 02 약관 | 유지: 기능 표시 변경이며 계약·사용권·투자서비스 보장·인원 변경 없음 |
| 03 환불 | 유지: 결제·해지·청약철회·환불 조건 변경 없음 |
| 04 쿠키 | 유지: 새 쿠키·브라우저 저장·방문자 추적 없음 |
| 05 쿠키 동의 | 유지: 배너·허용/거절·철회 처리 변경 없음 |
| 06 폼 동의 | 유지: 기존 시작 REST·명시적 연결 흐름과 금리 입력 일관성 절 보존. 새 동의·자동 연결 없음 |
| 07 최소화 | 1.5: 동일 응답 추가 항목·파생 cap·별도 시각·저장하지 않는 범위 |
| 08 제삼자 | 1.4: 공식 필드 근거와 한계·같은 공급자/호출·로컬 폰트 빌드 구분 |
| 09 선택권 | 1.5: 상태/출처/시각을 숨기지 않는 상세 경로·결측/미번역/오래된 재무 구분 |
| 10 요금 | 유지: 가격·VAT·자동 갱신·외부 데이터 비용 계약 변경 없음 |
| 11 후기 | 유지: Q-SCORE·재무항목을 후기나 검증된 성과로 사용하지 않음 |
| 12 주장 | 1.7: cap 산출·raw 단위 미검증·재무시각/회계 기준·업종·분석 성능 경계 |
| 13 대체 정보 | 1.6: 10열과 가격 hover 외 키보드 상세·미제공/미번역 텍스트 경로 |
| 14 대비 | 1.6: 이전 Noto와 새 Pretendard 치수 검사를 구분. 새 굵기·44px 행을 별도 확인 |
| 15 키보드 | 1.6: 변경한 열 인덱스·마지막 Q-SCORE 도움말·상세→기존 차트 접근 검사 |
| 16 사업자 | 유지: 운영자·주소·연락처·호스팅 정보 새 확정 없음 |
| 17 아동 | 유지: 연령·보호자·미성년 계약 범위 변경 없음 |
| 18 광고메일 | 유지: 주소 수집·광고 발송·동의·수신거부 변경 없음 |
| 19 권리 | 1.5: Pretendard 고정 출처·3개 실제 굵기·이름 변경·OFL·이전 Noto 구분. 시장 표시권 승인과 별개 |
| 20 삭제 | 유지: 추가 저장·보유기간·삭제 수단 없음. 기존 프로세스 상태/토큰 캐시 경계 보존 |

이전 main의 KIS 전송·선택·보관·FX/CMS/Signals·LETF·금리 재평가 절과 내부 Q-SCORE 수식은 유지합니다. 새 정책 버전은 별도 웹 Docs 번역·HTML 반영·AWS 배포를 자동 완료하지 않습니다. 실제 Windows DPI·스크린리더·장중 KIS 체결, 시장자료 상업 이용권 및 공개 승인도 별도입니다.20종 `review-required`와 공개 준비 `BLOCKED`를 유지합니다.

### 확장 검증 기록

최종 표/새 글꼴 프리뷰 고정 통지를 받은 뒤 기준선을 갱신합니다. 위 초기 compact의47개/523소스 및 이전 PR head CI를 이 확장의 최종 결과로 재사용하지 않습니다. 서로 겹치는 실행 수는 합산하지 않습니다.

| 주체·명령/범위 | 이 확장의 확인 결과 |
|---|---|
| 데이터 담당자: `python -m unittest tests.home_watchlist_acceptance tests.kis_workspace_acceptance tests.kis_stream_acceptance -v` | 44개,1.666초 통과 보고. 같은 응답의 재무·상장주수 파싱/결측·유효 가격 유지·기존 KIS 이력/스트림 계약. 실제 API 요청 아님 |
| UI 담당자: `MPLCONFIGDIR=/tmp/quantgen-mpl QT_QPA_PLATFORM=offscreen /workspace/quantgen-compat-venv/bin/python -m unittest -q tests.desktop_watchlist_acceptance` | 새 Pretendard3개 face로19개,6.754초 통과 보고.44px·긴 영문/중지 점수 두 줄·PER100.50·10열·상세/도움말·상태 시각 포함 |
| UI 담당자: 새 글꼴과 주입 시세 프리뷰 | 1360px 화면의 표1064px에서 가로 넘침0,1000px 화면의 표704px에서 내부 가로 스크롤360px. `/tmp/quantgen-comparison-FINAL-fixture-{ko-light-1360,en-dark-1360,en-dark-1000-right}.png`. 실제 공급자 시세 아님 |
| 주 작업자: 메트릭·KIS·패키징/웹브랜딩 | 48개 통과 보고. 설치 smoke는 실제 `load_interface_fonts(app)`와 QG Interface 확인을 추가했으며 최종 설치/CI 결과는 주 작업자 기록을 따름 |
| 정책 검토자: `/workspace/.venvs/quantgen/bin/python -m unittest tests.compliance_acceptance tests.compliance_export_acceptance` | 47개,7.615초 통과. 문서 로컬 링크·수정 문서 공백 검사도 통과 |

최종 기준선/정합성 명령은 `python -m tools.compliance.check --refresh-baseline --reviewed-by 'Codex UI session 2026-11-02' --review-note '…HOME_COMPACT_REVIEW_20261102.md…'`와 `python -m tools.compliance.check --check --report-dir /tmp/qg-compact-compliance`입니다. 결과의 소스 수·PASS 및 공개 준비 `BLOCKED`는 해당 보고서와 PR/인수인계 기록을 기준으로 확인합니다. 배포물 검사·실제 Windows/KIS·새 PR head CI를 이 문서의 소스 검토나 fixture 프리뷰만으로 통과 처리하지 않습니다.
