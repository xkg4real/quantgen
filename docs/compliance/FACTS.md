# QUANTGEN 정책 작성의 코드 근거

- 기준일: 2026-10-31 한국시간
- 코드 기준: `d4670f3bb738147a48a5dafe34dad7628e3fe3e4`
- 범위: 실행 진입점, `core/`, `data/`, `ui/`, `quantgen_desktop/`, 의존성·자산 선언과 관련 문서. 실제 운영 서버·사업자 계약·판매 사이트는 이 소스 검사로 확인되지 않는다.

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
| 차트 | 공통 Flet 차트 이미지에 결과별 대체 설명이 없다. 네이티브 차트 접근성 이름은 실제 수치·변화 설명의 충분성을 보장하지 않는다. | [Flet 차트 생성기](../../ui/qcharts.py), [네이티브 차트](../../quantgen_desktop/charts.py) |
| 대비 | 대표 텍스트 색상쌍은 충분한 대비를 보이지만 입력 테두리 등 전체 상태·화면의 적합성은 확인되지 않았다. | [팔레트](../../core/theme.py), [검사 양식](14-contrast.md) |
| 키보드 | 직접 메서드를 호출하는 이동 테스트는 실제 Tab·스크린리더 검증이 아니다. Windows·DPI·포커스 수동 검증이 남아 있다. | [데스크톱 검증](../../tests/desktop_acceptance.py), [남은 검증](../DESKTOP_MIGRATION_2026-10-30.md) |
| 권리 | Noto CJK 파생 폰트와 OFL 고지가 있다. PyQt6 배포 방식, 개별 이미지 제작·허락, 시장데이터 상업 이용·재배포·AI 전송권은 별도 증빙이 필요하다. | [폰트 기록](../../assets/fonts/README.txt), [OFL](../../assets/fonts/OFL.txt), [의존성](../../pyproject.toml), [권리대장](19-licenses.md) |

## 기존 설명의 충돌

[최신 README](../../README.md)의 상업화 결정은 과거 개인용 배포 정책을 대체한다고 명시한다. 그러나 [2026-10-29 배포 검토](../product/DISTRIBUTION_REVIEW_2026-10-29.md), [데스크톱 이행 문서](../DESKTOP_MIGRATION_2026-10-30.md), 일부 실행 코드의 개인용 표현과 공개 배포 미승인 표시는 남아 있다. 이 문서 묶음은 현재 기능과 최신 사업 의도를 구분하고, 과거 개인용 제한을 현행 정책으로 복제하지 않는다. 기존 표시를 일괄 정정하려면 데이터 권리·배포 승인 상태를 함께 확인해야 하며, 문구 삭제만으로 권리가 확보되지는 않는다.

## 이 기록으로 확정할 수 없는 사실

법적 사업자·대표자·등록번호·운영 주소와 연락처, 실제 요금·갱신·환불 채널, 운영 국가·호스팅·로그·백업, 실제 보유기간, 제공자별 개인정보 역할·국외이전 국가·계약, 허용 이용 연령, 계약별 데이터 권리, 운영 사이트 접근성은 운영자가 증빙해야 한다. 이 파일은 이용자 개인정보나 비밀키를 저장하는 장소가 아니다.
