# GPT UI 진행 체크포인트 — 2026-11-13 (최신)

- status: taken
- owner: GPT UI 세션; 메인 엔진 CURRENT.md는 변경하지 않음.
- work_branch: gpt/ui-d11-d15-20261113
- work_commit: 5b7f7dd3369b14e4497e90b76b62f08265fb1144
- PR: https://github.com/xkg4real/quantgen/pull/112 (Windows CI 대기, main 미병합)
- 사용자 요청: "클로드가 ui작업 ... 변경된 버전 ... 인계문서에 잇으니 확인해서 진행 ... 실행법"

## 완료한 구현 및 로컬 확인

Claude 7402a43 위에 main 9e00bf3를 병합하고 UI_WIP D11/D13/D14 패치를 복구했다.
Pretendard OTF/N3, 네이티브 기준, 기존 승인 차트 모양을 유지한다.
- D11 메뉴 리뷰: 항목 상시 표시로 클릭 위치 이동 방지, 직접 클릭/호버/키보드 분리, 언어/그림자 처리.
- D12 A1: 차트 전체에서 열린 손, 끄는 중 쥔 손. Ctrl+휠/화살표/7자리 가격 수정 유지.
- D13 A2: 상세 Q-SCORE 카드/배지, 국내·미국 v0.2, KIS 수정 일별 200거래일, 미국 뉴욕 거래일.
  기존 국내 v0.1 점수/부분 점수 일치(71.57/50.34/63.59); 자료 부족 이유 표시. 프로필 자료 재사용,
  작업 스레드 계산과 5초 재계산 간격, 다른 종목/오래된 결과 폐기.
- D14: 동결된 화면의 PDF/PNG/JSON/CSV; 취소 시 파일 없음, 원자적 저장, 형식 변경 시 기존 파일
  덮어쓰기 재확인. 한글 내장 확인(pdffonts), 숫자 검색을 위해 PDF 문서에서만 tnum/liga/kern=0 및 PreferNoShaping. 한글·숫자·음수 부호 복사 검사 추가, 후속 9개 재통과.
- D15 A4: 국내·미국 Q-SCORE 높은 순, 최대 20개 거래대금 후보, 순차 KIS 수정 일별 조회,
  날짜별 메모리 캐시/실패 5분 제한/이탈 중단. 미산정 아래에 유지. ENABLED 한 곳으로 숨김.
- 사용자 지정 면책 "실험적 지표 · 투자 권유 아님"은 이전 해요체 검사에서 이 정확한 문구만 예외.
- 메뉴/순위 64 OK, Q-SCORE/KIS/export 33 OK, 통합/정책 58 OK, 수정 화면 4 OK, 최종 후속 9 OK.
  초기 시장 90 중 3개, 상세 34 중 2개 실패는 새 UI 기대값 차이였고 해당 검사들을 재통과했다.
- 메뉴 ko/en×light/dark×1440x900/1000x700 8개 패널 경계 확인; 상세 큰/작은 창 캡처 확인.
- compliance consistency PASS, publication BLOCKED 유지. 법률·데이터 이용권 승인 주장 없음.

## 다음 단계 (GPT 계속 진행 중)

1. PR112 최신 head 5b7f7dd의 Runtime Windows 3.11/3.12/3.14 + Ubuntu 3.12와 compliance 결과 확인.
2. 실패 시 실제 실패를 수정하고 해당 검사를 다시 확인. CI 진행 중에 병합하지 않는다(PR89 교훈).
3. 검증 통과 후 사용자 기존 main 병합 지시에 따라 PR ready/main merge. attach_artifact 이미 완료.
4. 이 문서와 LEDGER 완료 기록에 병합 SHA/검증 결과 추가, 사용자에게 최종 CMD/버전 표시 안내.

## AWS / 증거 경계

소스 큐: docs/product/ui_website_updates/PR-112.json. 웹사이트 작업공간(AWS)에 보낼 자료는 queued.
지원되는 대화 간 발송 도구가 없어 실제 발송/웹 HTML 변경/배포는 하지 않았다. 사용자 KIS 실계정과
Windows DPI는 검증하지 않았다. 화면 캡처는 오프라인 합성 시세이며 실제 시세의 증거가 아니다.
로컬 /workspace/shared/ui-20261113/에 캡처/PDF가 있으나 환경 종료 후 사라질 수 있다.

---

# GPT UI 인수 체크포인트 — 2026-11-13

- 사용자 요청: 클로드 변경본 확인, 인계된 미완성 UI 작업 계속, 같은 버전을 확인할 CMD 실행법 제공.
- 확인한 main9e00bf3(PR109 UI 포함), UI작업원격 claude/friendly-bardeen-r6xe8f7402a43ec9fed7279967e5c71eea848e8207206a. UI-D11/D12 후속은 main미병합. UI-D13/D14 패치는시험되지않은중간작업, D15는구현전.
- 새 작업브랜치 gpt/ui-d11-d15-20261113, /workspace/quantgen-ui-20261113. 클로드7402a43에서 시작. 사용자에게현재main9e00bf3 확인CMD를 먼저 안내함.
- UI-D1..D6(PretendardOTF+N3), Fusion, R-D9차트비침범, 최신A1~A4(차트항상손커서·미국Qscore·크립토+ETF·기본표시순위/중앙off설정)를 그대로따름. 이전GPT글꼴로되돌리지않음.
- 다음: 최신main통합, D11리뷰patch점검/시험, D13카드+Qscorev0.2/미국, D14PDFPNGJSONCSV, D15순위. 새호스트/KIS경로추가없음. 완료단위만⑬-2원장기록. CURRENT/다른엔진작업은건드리지않음.
- 실제API/키/웹HTML/배포는범위밖. 사용자기존main업데이트선호와병합권한을유지하되, 이전PR89처럼원격Windows검사가진행중인상태를완료로넘기지않음.

---

# 소유자 결정 — 2026-11-11 05:40 KST (UI 앱 통일) · 모든 에이전트(Claude·GPT) 필독

소유자 원문(2026-11-11, Claude Code 채팅):
> 네이티브로 통일하는데, 글꼴은 너가 쓴거 그대로 쓰면 되고 + 오늘 변경한 부분들도 너가 썼던 걸로 진행하면돼. gpt한테 전달 똑바로하고, 대신 나머지 부분은 gpt가 수정한 ui사용해야해

앞선 선택(같은 날 AskUserQuestion): 주력 앱 = **네이티브 앱으로 통일**, 글꼴 = **Flet 화면 글꼴(Pretendard 기반)**.

| ID | 결정 | 구체적 의미 |
|---|---|---|
| UI-D1 | 주력 앱은 네이티브 PyQt (`python -m quantgen_desktop`, `Start-QUANTGEN-Desktop.cmd`) | 앞으로의 UI 수정은 네이티브 기준. Flet(`main.py`)은 유지하되 기준 앱이 아님 |
| UI-D2 | 2026-11-10 소유자 지적 14건의 해결은 **Claude 버전**(PR #98, Flet에 구현된 것)을 네이티브로 옮김 | 전략 실험실 판정 배너·요약 타일·카드 이름(`core/research/strategy_display.py`), 분석 요약 정리, 차트 읽는 법, 천 단위 콤마, 출처 선택기 제거·`source="best"`, 실시간 시세 정렬, 곡선 방법 9개, 한국어 통일 등 |
| UI-D3 | 그 밖의 화면·구조는 **GPT 버전**(PR #89 네이티브 압축 UI: 내용폭 메뉴, `form_layout`·`table_layout`·`category_picker`·`result_layout`, 여백·표 밀도) 유지 | 14건과 무관한 네이티브 화면을 Flet 모양으로 바꾸지 않음. 14건을 옮길 때도 GPT의 배치 도구를 그대로 사용 |
| UI-D6 (2026-11-11, UI-D5를 대체) | 네이티브 글자·숫자 = 원래 Pretendard(QG Interface OTF) + 2차 시안 N3 설정. 소유자 원문: A안 적용 후 "하.. 좃구린데 ... PRETENDARD 저거랑 비슷한 글꼴인데 좀더 깔끔해보이는거 위주로 다시 찾아서 시안 던져볼래?" → 2차 시안 16종 중 "N3 진행해줘" | `quantgen_desktop/typography.py` `window_stylesheet` 맨 끝 N3 규칙: 자간(제목 -0.9px, 소제목 -0.36px, 본문 -0.2px, 설명 -0.14px, 표·버튼 -0.1px, 가격·등락 0), 소제목·카드 제목 500, 설명 400, 버튼·메뉴·탭 400(선택 메뉴·도구 600), 기본 버튼 500, 표 머리글 500. Plex 파일 제거. 커밋 `d90dda7`, `9a322d3` |
| UI-D5 (2026-11-11, UI-D4의 네이티브 글자 부분을 대체) | 네이티브 글자 = IBM Plex Sans KR, 숫자 = 지금 글꼴(QG Interface, Pretendard OTF). 소유자 원문: "일단 A로 바꾸고 숫자는 지금 폰트 유지해줘" (글꼴 시안 14종 중 A) | `quantgen_desktop/font_policy.py`: 앱 글꼴 Plex, `number_font()`로 숫자(지표·가격·등락·숫자 표 칸·관심종목 숫자 열·차트 눈금)는 QG Interface. Flet·Flet 차트는 QG Interface 그대로. 파일 `assets/fonts/IBMPlexSansKR-*.ttf` + `OFL-IBMPlexSansKR.txt` |
| UI-D4 | 글꼴 = Flet 화면 글꼴 `assets/fonts/qg-interface*.otf`(Pretendard 1.3.9 기반, 한글 11172자) + `QG Symbols` | 네이티브 `font_policy.py`가 Gothic A1 TTF 대신 이 OTF를 등록. Flet·네이티브 차트 글자도 같은 글꼴. Gothic A1 TTF 파일은 저장소에 남겨 두되 사용하지 않음(되돌릴 때 대비) |

GPT 인수 시 금지: 위 14건 화면을 GPT 이전 버전으로 되돌리기, 글꼴을 Gothic A1로 되돌리거나 UI-D6(Pretendard + N3 자간·굵기)을 바꾸기, 14건과 무관한 GPT 압축 UI를 Flet 모양으로 바꾸기.

---

# ⚠ 인계 상태 — 2026-11-12 16:55 KST (Claude → GPT, 사용량 소진) · 이 절이 아래 내용보다 우선

- status: handoff · reason: Claude 주간 사용량 소진(소유자: "아 근데 너 토큰없네. 일단 GPT한테 내가 ㅈ마지막으로 명령한거까지 인계해서 정확하게 넘겨줘")
- work_branch: `claude/friendly-bardeen-r6xe8f` · work_commit: `7402a43` (main `0786200` 위: R-D12 c508a0d·793a321·5916c36, 오른쪽 칸 잘림 수정 36d23b8, UI-D11 본체 840ae95, 기준선 7402a43)
- **전체 인계서: [WEEKLY_HANDOFF_2026-11-12_ui-d11-d14_c958d211.md](WEEKLY_HANDOFF_2026-11-12_ui-d11-d14_c958d211.md)** — 소유자 원문 11개(마지막 지시까지), 해석 규칙 R-D11·R-D12·R-D13·R-D14·R-D15, 남은 일 명령·완료 기준, 법령 주의
- **이번 주 요청 26건 요약표: [UI_WEEKLY_REQUESTS_2026-11-10_12.md](UI_WEEKLY_REQUESTS_2026-11-10_12.md)** (상태·커밋·작업 방식 요청·확정 답·고정 규칙)
- 중간 작업 patch(시험 안 됨): `UI_WIP/ui-d11-review-fixes_base-840ae95.patch`, `UI_WIP/ui-d13-qscore-card_base-5916c36.patch`, `UI_WIP/ui-d14-export_base-5916c36.patch`
- 소유자 답(16:57 KST, 원문은 인계서 0절): ① 손 모양 커서 = 차트 위면 항상 ② Q-SCORE 미국 주식까지 확대(허용된 경로만, v0.2) ③ 코인→크립토 + ETF 추가 맞음 ④ Q-SCORE 순위는 공개 버전으로 개발(기본 표시, 상용화 시 삭제 검토 → 한 곳에서 끌 수 있게)
- 남은 일: UI-D11 리뷰 수정·규정 문서, UI-D13 상세 화면 Q-SCORE 카드·배지, UI-D14 PDF/PNG/JSON/CSV 내보내기(Q-SCORE 포함), R-D15 시장 목록 Q-SCORE 순위(법령 검토 필요 — 매수·추천 문구 금지)

---

# 종목 상세 차트(UI-D8·UI-D9)·미국 시가총액·시장 화면 개편(UI-D10) 완료 — 2026-11-12 04:10 KST (Claude) · GPT 필독

- status: PR https://github.com/xkg4real/quantgen/pull/109 소유자가 main에 병합(2026-11-12 15:13 KST, main `0786200`). 작업 브랜치 `claude/friendly-bardeen-r6xe8f`는 main `0786200`으로 다시 맞춤.
- 진행 중(후속, 새 PR은 소유자 요청 시): UI-D11 레일 "시장" 큰 범주(지수·주식·크립토·선물·외환·국채·회사채·ETF·월드 이코노미) + 마우스 올리면 하위 메뉴가 3단으로 펼쳐짐 + 국내/미국 ETF 시장, "코인"→"크립토"(컨테이너 로컬 브랜치 `ui-rail-d11`); R-D12-1/2 상세 차트 Ctrl+휠 확대(+/− 키·버튼 제거), 좌클릭 끌기로 좌우 이동(화살표 유지)(`ui-zoom-d12`). 소유자 원문은 아래 "UI-D11·R-D12" 절.
- PR CI에서 찾아 고친 것(GPT 필독): ① 앱이 Qt 스타일을 정하지 않아 Windows에서 windows11 스타일로 그려짐 → `quantgen_desktop.use_fusion_style()`로 모든 OS에서 Fusion(`a2e4daf`) ② `main()` 밖에서 만든 창(시험·캡처)이 번들 글꼴을 등록하지 않아 OS 기본 글꼴로 측정 → `use_interface_fonts()`(`c5286ec`) ③ `LanguageController`가 레이아웃 변화마다 창 전체 글자(약 2만 개)를 다시 번역해 크기 조절이 1초씩 멈춤 → 같은 언어·로캘로 이미 그린 글자는 건너뜀, 1440→1000px 1.1초→0.37초(`27c3a10`) ④ 관심종목 Q-SCORE 칸 폭 맞춤(`0235319`) ⑤ CI installed 작업 제한 45→120분(`4e743e3`). 새 화면을 만들 때 Fusion·번들 글꼴 기준으로 확인할 것.
- work_branch: `claude/friendly-bardeen-r6xe8f` (main 미병합, PR은 소유자 요청 시)
- 소유자 확정 규칙 원문·해석(R-D9-1~4, R-D10-1~3)은 아래 절. 상세 차트·시장 화면을 고치기 전에 반드시 읽을 것.

## UI-D11·R-D12 소유자 원문 (2026-11-12, 트레이딩뷰식 시장 메뉴 그림과 함께)
> 좋은데 시장 하위 유아이를 저렇게 두지 말고 이런식으로 큰 범주로 묶고 저기 뭐 주식 하부 유야이다 그러면 거기 마우스 휠 올려놓으면 더 하부로 국내, 미국, 글로벌 뭐 이런 식으로 볼수있고 거기서 국내에 마우스 올려놓으면 다시 거래대금 거래량 급상승 급하락 이렇게 누를수있게. 누르면 지금 ui랑 똑같이 저 화면으로 바로 넘어갈수잇게 그니까 바꾸라는게 아니야. 지금 시장 안의 ui는 괜찮다. 새꺄 그리고 코인이 뭐야 ETF라해야지
> 아 그리고 차트 확대를 +-로 하지말고 컨트롤 + 마우스 휠 이렇게 하자
> 그리고 화살표 말고 차트 화면 좌클릭해서 좌우로 끌면 좌우도 움직일수잇게 !! 화살표도 유지하고

해석: 그림의 범주·순서 그대로, 데이터가 있는 하위만(빈 메뉴 금지), 잎을 누르면 지금 시장 화면으로 그 시장·기준 선택; 시장 화면 자체는 그대로; "코인" 대신 "크립토"(그림 표기), ETF 추가(국내·미국 각 약 20종, 주식과 같은 시세 경로, 시가총액 기준 없음). 차트: Ctrl+휠 확대(커서 기준), +/− 제거, 좌클릭 끌기 이동, 화살표 유지, 휠만으로는 아무 일 없음.

## UI-D9 소유자 원문 (2026-11-11~12, 상세 차트 캡처를 보고)
> 야 ㅅㅂ 우측 가이드가 차트를 가리면 어떡해 차트영역은 절대 침범하면안돼 가이드를 다른위치에 좀 센스있게 넣어봐. 그리고 그 봉간격도 좀 일봉 ㅇㅈㄹ하지말고 몇분, 일, 주 월, 년 이렇게해야지 누가 봉을쓰냐 18련아
> 그리고 저거 알려주는 방식도 무엇인가요, 어떻게 보나요, 주의, 아 이게 뭔가 너무 이상한데 좀 더 센스있게 못하나? 지금 글밥이 너무 많아보이잖아. 여백도 똑바로 못쓰고잇고 존나읽기싫어
> 그리고 차트 가로넓이 살짝만 더넓혀보자

| 규칙 | 내용 | 구현(파일) |
|---|---|---|
| R-D9-1 | 어떤 창 크기에서도 차트 영역(가격·거래량·보조 패널·축)을 덮는 것 없음. 오른쪽 열은 항상 차트 옆에 붙고 차트가 줄어듦. 좁은 창은 이 화면에서만 왼쪽 레일 자동 접기(소유자 저장값은 안 바꿈, 나가면 복원) | `stock_detail.py`(오버레이 모드 삭제, 기하 시험 1000×700~1920×1080) |
| R-D9-2 | 간격 이름 = 1분·3분·5분·15분·30분·60분 / 일·주·월·년(년 추가, 월봉을 접어 만듦, 진행 중인 해 표시). 한국어 화면 어디에도 "봉" 없음(간격에 맞춘 말: 최근 14일/14주…) | `core/market/models.py`, `detail_model.py`, `study_guide.py`, `stock_detail.py`; 모든 글자를 훑는 "봉" 금지 시험 |
| R-D9-3 | 해설은 "무엇인가요/어떻게 보나요/주의/지금 읽기/설정" 나열 금지. 카드 = 상태 알약 + 지금 읽기 한 문장 + 작은 눈금 그림 + 회색 한 줄 + 단서 칩 2~3개 + 주의 한 줄, 긴 글은 "자세히 ›" 뒤. 여백 16·간격 10·줄높이 150% | `study_guide.short_guide`(27종 짧은 글 한/영, 길이 제한 시험), `GuideCard` |
| R-D9-4 | 차트 폭 살짝 넓힘: 오른쪽 열 360/350/335/320(이전 380/360/340/320), 화면 좌우 여백 16(이전 24) → 1440×900에서 차트 829→855px | `stock_detail.py` `6206daf` |
| 이전(UI-D8) | 왼쪽 큰 차트 고정, 휠은 오른쪽 열만, ←/→는 차트를 바로 이동(Shift 10칸, Home/End), 지표 분류 접기, 주린이 해설, 매수·매도 조언 금지 | `92bb4d7`·`016d7a8`·`eee4206` |

## 미국 시가총액·규정 후속 (소유자 승인 "승인.", 2026-11-11)
- KIS 해외 상세시세 `/uapi/overseas-price/v1/quotations/price-detail`(HHDFS76200200)을 읽기 전용 허용 목록에 추가(31→32개). 순서: KIS `tomv`(USD, 상장주식수×가격과 25% 안일 때만) → FMP batch-quote(키 있을 때) → Yahoo 상장주식수×가격("시가총액(계산값)"). TSM(ADR)은 FMP만. 캐시 `config.ficc_cache_dir()/SHARES_YFINANCE_<SYMBOL>.json` 24시간. `aceeb52`
- 순위 목록 상태 표시 "KIS 실시간" → "KIS 조회 · 45초마다"(REST 반복은 실시간이라 부르지 않는 2026-11-02 주장 규칙). 국내 시가총액은 `hts_avls`×1e8이 `lstn_stcn`×현재가와 25% 안일 때만, 없으면 계산값, 안 맞으면 순위 없이 "—". 시장 버튼·홈 접기 버튼 포커스 표시. `8a323a2`·`179d85a`
- 규정 문서 01·04·06·07·08·09·10·12·13·14·15·19·20·FACTS(앵커 `ui-d7-d8-uscap-2026-11-11`, `ui-d10-markets-2026-11-11`) 갱신 + 독립 검사 반영(`06ed39f`·`38e7dbd`·`5dcbdb8`). 소스 검토 기준선 갱신 `a6d780b`: `--check` consistency PASS, publication BLOCKED(변경 없음), 701 소스.
- 차트 시험 자정 오류 수정(`cab19e1`): 자정 직후 KST에 체결 날짜가 전날이 되어 실패하던 시험을 고정 시계로 결정적으로.

## UI-D10 시장 화면 (완료 `486e002`·`972ed28`·`5dcbdb8`) — 소유자 원문
> 저거 시장 있지. 시장에서 그냥 국장 미장 코인 이런걸 하부ui로 두고, 너가 지금 하부ui로 깔아놓은건 해당 시장의 하부ui 선택하고 차후에 검색기준으로 저걸 쓸수있게 구현하면 좋을 거 같은데, 공간 잘써서 센스있게해봐

해석(R-D10): 레일 "시장" 하위 = 국내 주식 / 미국 주식 / 코인. 각 시장 화면 안에서 거래대금·거래량·급상승·급하락·시가총액이 그 시장의 순위 기준이자 검색 기준(검색어 + 기준 + 조건 필터: 등락률 범위·거래대금·시가총액 하한·업종, 나중에 기준 추가 가능한 구조). 코스피/코스닥 등은 화면 안 필터. 큰 제목·설명 문단·별도 검색 카드 없이 한 줄 머리 + 기준 줄 + 넓은 목록, 얇은 지수 띠. 코인은 앱이 이미 쓰는 Yahoo 일별만(새 호스트·KIS 엔드포인트 없음), "지연·일별" 표시. 구현: 레일 하위 = `core.market.screen.PAGES`(국내 주식/미국 주식/코인), `MarketsWorkspace.show_market(key)`·`market_changed`·`focus_search()`(옛 `show_category`는 호환 유지), 기준·조건은 데이터(`core/market/screen.py` `Condition`·`CONDITIONS`, 기준 하나 = 표 한 줄), 머리 고정(스크롤해도 이름·정렬 기준·검색·열 제목 유지), 지수 띠 `quantgen_desktop/market_summary.py`(홈 로더 재사용, 보일 때만·자동 갱신 켰을 때만), 코인 15종 `rankings.CRYPTO`(Yahoo `<CODE>-USD` 일별, 달러, 거래대금은 Yahoo 달러 거래량 그대로, 시가총액·거래량 기준은 비활성+이유, 행은 열지 않음+이유). 새 호스트·KIS 엔드포인트 없음. 검토 2명 22건 전부 반영. 병합 후 시장·홈·상세·규정 시험 233개 통과.

---

# 연구 홈·시장·레일 재설계 완료(UI-D7) + 상세 차트 진행 중(UI-D8) — 2026-11-11 KST (Claude) · GPT 필독

- status: UI-D7 완료·푸시(`b9bd84b`), UI-D8(종목 상세 차트) 진행 중 · waiting_on: none · updated_at: 2026-11-11 16:40 KST
- UI-D7 병합 결과: 레일 `7bf3c92`, 시장 순위 `9786dea`·`9ab7591`·`c12de90`, 연구 홈 `fcccc85`, 연결 수정 `d1563c3`·`b0a6e4c`·`0152880`, 연한 구획선·여백 `b9bd84b`
  - 연한 구획선(소유자: "모든 화면들의 구획 선을 연하게 가자. 한칸한칸 공간을 넓게해서 구획선이 연해도 괜찮게"): `typography.py` 선 색 = `mix(border, bg, 0.5)`, 패널 2px 아래 선 제거·1px·반경 16, 페이지 여백 32/28·블록 간격 24, 패널 22/20, 도구 화면 26/22.
  - 연구 홈 기본 선택 카드 = 코스피(소유자 트레이딩뷰 참고).
- UI-D8(종목 상세 차트) 소유자 원문과 확정 규칙: 스크래치가 아니라 이 문서 아래 "UI-D8" 절 참고(완료 시 갱신).
- work_branch: `claude/friendly-bardeen-r6xe8f` (시작 `ce857a9`), 영역 3개 병렬(컨테이너 로컬 브랜치 → 통합 후 병합)

## 소유자 요청 (원문, 2026-11-11, 스크린샷 2장: 우리 관심종목 카드, 트레이딩뷰 "지수 >" 화면)
> 여전히 여기 그 주식 가격들있지 여기 숫자가 너무 위아래로 납작해, 그리고 시장 누르면 하위 UI로 종목 고를수있게 바꿔주고, 왼쪽 UI화면들 숨기는 기능도 필요해. 공간이슈때문에 , 그리고 연구 홈 화면을 표대신 이렇게 심플하고 세련되게 화살표로 휙휙 넘길수잇게 하자 (트레이딩뷰 화면 참고) 표에 종목 너무많이 때려박는거 자체의 구조적 문제인거같아. 세로로 넓게 넓게 공간 쓰고, 연구 홈에 주요차트 뿐만이 아니라 우리는 연구분석과 같은 UI들이 들어가는데, 얘들이 들어갈 공간은 스크롤 상하 범위를 넓혀서 해결해보자. 그리고 연구 홈에서 '관심종목' 차트를 직관적으로 볼수있게 유아이를 저기로 옮기고, 시장 UI에는 토스증권처럼 실시간 차트를 다양한 분류기준으로 조회할수있게 변경해봐

## UI-D8 종목 상세 차트 (진행 중) — 소유자 원문
> 그리고 검색해서 차트를 확인하는 경우엔, 그 차트의 가독성과 들어있는 데이터들을 우리 기술엔진 가이드와 함께 최대한 구체적이고 이해할수있게 제시해줘야해. 그러니까 사용자가 검색해서 한 차트를 구체적으로 볼때에는, 해당 차트로 화면을 거의 가득채워도 가능해. 정보전달과 가독성에 신경쓰고 공간 넉넉하게써줘
> 그리고 시장에서 차트검색해서 들어갈때, 지금 스크롤로 차트좌우이동이 가능한데, 이거 그냥 막아버리고 pc기준 좌우화살표로 차트 좌우 확인할수있게 변경해줘
> (기술지표 확대 승인) ㅇㅇ 그걸넣고, 그러면 상세차트로 들어갈 때에 기술지표 목록들의 ui도 저렇게 뜨면 안되겠지, 수가 늘어날 테니. 트레이딩뷰 상세차트 목록 ui인데, 이런식으로 큼직큼직하게 하고 지표같은건 화살표로 접고펴고 할수잇게 해야하고, 우리는 이 ui를 기본으로 주린이들이 읽기 쉽게 하는 가이드를 화면에 잘 녹여야해
> 그리고 우리 상세차트 밑에잇는 ui들인데.. 딱봐도 ㅈㄴ조잡하지?그냥 좌측에 존나큰차트 존나크게, 이런 공간 부족해서 스크롤이 필요한 메뉴들은 오른쪽으로 빼서 간소화. 이 틀로 진행해줘
> 오른쪽의 스크롤 필요한 메뉴들은 움직이는거고, 차트쪽은 스크롤로 위아래 이동이 안되는거야. 오른쪽만 움직이는거지 스크롤이

확정 규칙: 왼쪽 큰 차트(창 대부분), 차트 아래 카드 묶음 없음, 오른쪽 열 하나만 스크롤(페이지 스크롤 없음), 차트 위 휠은 무반응, ←/→ 이동·+/− 확대, 지표 목록은 분류별 ▸/▾ 접기·큰 행, 주린이 해설(커서 위치 값의 쉬운 말, 매수·매도 조언 금지), 오른쪽 묶음은 핵심 숫자 3~4개만 보이고 접힘. 지표 엔진 27종(`dcf12ff`: `core/education/indicators.py`, `core/education/study_guide.py`, `core/market/presentation.chart_svg(end=, price_height=, supply=)`) — 수급(외국인·기관·개인 순매수, 공매도)은 이미 허용된 KIS 조회만 사용.

## 결정 UI-D7 (Claude의 해석, 소유자에게 보고함)
| 영역 | 내용 | 파일 |
|---|---|---|
| 카드 비율 | 관심종목 카드 차트 150→210px (`ce857a9`) | `markets_view.py` |
| S 레일 | 왼쪽 레일 접기(버튼·Ctrl+B, 상태 저장), "시장" 하위 메뉴(거래대금·거래량·급상승·급하락·시가총액·종목 검색) | `app.py`(make_home/make_markets 제외), `typography.py` |
| H 연구 홈 | 큰 시세 표 대신 트레이딩뷰식 지수 카드 줄(‹ › 넘김) + 선택 카드의 큰 차트 + 관심종목 카드(시장에서 이동) + 연구 영역(세로 여유). 기존 시세 표는 맨 아래 접힌 "전체 시세 표" | `home_view.py`(새), `app.make_home` |
| M 시장 | 토스식 "실시간 차트": 분류(거래대금·거래량·급상승·급하락·시가총액) × 시장(국내 전체·코스피·코스닥·미국) 순위 목록, 행 클릭 → 종목 화면 | `markets_view.py`, `core/market/rankings.py`(새), `market_rankings.py`(새) |

데이터 제약: KIS 허용 목록(`config.KIS_QUOTATION_ALLOWLIST`, 읽기 전용·고정)에 순위 API가 없어 **시장 전체 순위가 아니라 주요 종목군(국내 대형주·업종 대표·미국 대형주)의 시세로 순위**를 매김. 시장 전체 순위가 필요하면 허용 목록 확장은 소유자 승인 사항.

인터페이스 약속: `markets_view.RANKING_CATEGORIES`, `MarketsWorkspace.show_category(key)`, `WatchlistGrid`는 이름·생성자 유지(홈이 사용), `window.watchlist`(시세 표)는 창 속성으로 유지.

---

# 네이티브 이식 완료 — 2026-11-11 KST (Claude, ⑬-2/owner-14-native) · GPT 필독

- status: 완료(작업 브랜치 푸시됨, PR은 소유자 요청 시) · waiting_on: owner(PR 여부) · updated_at: 2026-11-11 10:55 KST
- session: https://claude.ai/code/session_016uB1jf8m3p5GW1qzQVJe7k
- work_branch: `claude/friendly-bardeen-r6xe8f` = main `1a8b29f` + 커밋 `9a322d3` (main에 아직 병합 안 됨)
- LEDGER: ⑬-2/owner-14-native (이 브랜치), 앞서 ⑬-2/owner-14-flet(PR #98), ⑬-2/ui-base-owner-decision

## 무엇이 바뀌었나 (네이티브 `quantgen_desktop/`)
| 이슈 | 네이티브 결과 | 파일 |
|---|---|---|
| 01·06·07·09·10 전략 실험실 | 판정 배너 → 핵심 지표 타일 → 누적 수익 차트 → 검증 항목 표(한국어·결과·기준·판정·뜻) → 제공처 메모. 카드 보기: 판정별 개수 타일, 카드 34종 이름, 카드 선택 상세. 출처 상자 숨김(`best`) | `strategy.py`, `strategy_view.py`(새), `core/research/strategy_analysis.py` |
| 02 차트 | 정수·반올림 눈금, 한국어 축·범례(`charts.chart_text`), 도구 차트 24개 "이 차트 읽는 법", Macro z-점수 막대 Flet식 | `charts.py`, `chart_study.py`, `macro.py`, `macro_records.py` |
| 03·08 숫자·금리 | 천 단위 구분, DV01 이름표, 곡선 방법 설명 상자(9개) | `bonds.py`, `rates.py`, `structuring.py`, `fx.py` |
| 04·12 출처 선택 | Portfolio·Signals·Monte Carlo·Strategy Lab 숨김+`best`, ETF 이력 `best`, Derivatives 자동(KIS/합성) | `portfolio.py`, `signals.py`, `app.py`, `core/research/{analysis,portfolio_analysis,signals_analysis,market_analysis}.py` |
| 05 시세 표 | 머리글·값 같은 여백, 숫자 오른쪽 끝 맞춤, 단위 고정 칸, 본문 13px | `watchlist.py` |
| 11 해설 | 모든 도구 해설 = 소제목+글머리표, 전체 문단 접힘 | `narrative_view.py`(새), `tools.py` `finished` |
| 13 포트폴리오 | 결론 요약 카드, 목적함수 이름, 표 크기 맞춤, 실행 전 안내 | `portfolio.py`, `risk_display.py`(새) |
| 14 한국어 | 영역별 문구 `owner_ui_language/*.py`, 앱 자료 메모 한국어(`source_notes.py`) | — |
| 글꼴(UI-D6) | 원래 Pretendard(QG Interface) + N3 자간·굵기. Plex(UI-D5)는 같은 날 철회·파일 제거. Gothic A1 TTF는 미사용 보관 | `font_policy.py`, `typography.py` |
| 비율(소유자 추가 지시) | 관심종목 카드 4열·차트 150px, 모든 차트 높이=폭/2(최대 440), 폭 최대 920 | `markets_view.py`, `charts.py` |

## GPT가 지켜야 할 것
- UI 기준 앱은 네이티브 하나(`AGENTS.md` 6절). 위 화면을 이전 모양으로 되돌리지 말 것, 글꼴을 Gothic A1로 되돌리지 말 것, 14건과 무관한 GPT 압축 UI를 Flet 모양으로 바꾸지 말 것.
- 표시만 바꾸는 규칙: 계산값·판정 코드·내보내기(`pane.sections`/`report`)는 언어와 무관하게 같아야 함. 한국어 문구는 `owner_ui_language/<영역>.py`에 추가(같은 영어에 다른 한국어를 주면 import 시 오류).
- 해설 줄(`narrative_view.NarrativeLine`)은 UiLabel이 아님. 시험·내보내기는 UiLabel.source_text로 원문을 찾음.
- 차트 문구는 `owner_ui_language/charts.CHART_TERMS`(차트 전용 뜻)와 `READINGS`(읽는 법). 새 도구 차트는 READINGS 항목이 없으면 시험 실패.
- 숨긴 출처 상자는 지우지 말 것(시험이 `findData('synthetic')`으로 고름).

## 남은 일
1. 글꼴: A안(`cf55a5d`) → 소유자 거절 → 2차 시안 N3 적용(`d90dda7`, `9a322d3`). 다시 바꿀 때는 OFL/Apache만, 시안 승인 후. 시안 도구는 컨테이너 임시 폴더(세션 종료 시 사라짐).
2. PR 생성·main 병합(소유자 요청 시). 다른 Claude 세션의 PR #102와 `docs/compliance/FACTS.md`·`source-review.json`·`runtime-smoke.yml`이 겹침 — 나중에 병합하는 쪽이 main을 합치고 기준선 갱신.
3. 실제 Windows 화면 확인(글꼴 선명도·DPI), 실제 제공처 응답 확인.

## 검증
- GitHub CI `runtime-smoke.yml`의 unittest 단계를 그대로 나눠 컨테이너에서 실행(offscreen): 13묶음 1,256개 전부 통과.
- 새 시험: `tests/desktop_owner_ui_{integration,strategy,ficc,market,risk,charts}_acceptance.py` (CI 단계 "Verify the owner's 14 UI issues on the native app"에 등록).
- 컴플라이언스: `python -m tools.compliance.check --check` → consistency PASS, publication BLOCKED(변화 없음), FACTS `owner-ui-native-2026-11-11`.
- 수정 전후 캡처는 컨테이너 임시 폴더라 세션 종료 시 사라짐. 다시 만들려면 시험 픽스처로 `ResearchWindow`를 띄워 `grab()`(오프스크린).

---

# 네이티브 이식 진행 기록(이전) — 2026-11-11 KST (Claude, 위 UI-D1~D4 실행)

- status: checkpoint · waiting_on: none · updated_at: 2026-11-11 07:30 KST · LEDGER ID: ⑬-2/owner-14-native (진행 중)
- session: https://claude.ai/code/session_016uB1jf8m3p5GW1qzQVJe7k
- work_branch: `claude/friendly-bardeen-r6xe8f` = main `1a8b29f` + 기반 커밋 `66470f4` (푸시됨). PR 없음(소유자 요청 시 생성).
- 메인 `CURRENT.md`·`LEDGER.md`는 다른 Claude 세션(task claude-resume-20261103) 것이라 건드리지 않음.

## 끝난 것 — 기반 커밋 `66470f4`
1. 글꼴(UI-D4): `quantgen_desktop/font_policy.py`가 `qg-interface*.otf`(Pretendard 파생, 가족 이름 동일 `QG Interface`)를 등록. `ui/qcharts.py`(Flet 차트 PNG)도 같은 OTF. Gothic A1 TTF는 `assets/fonts`에 남기고 사용하지 않음. 글꼴로 폭을 재는 시험 4개도 OTF로.
2. 이슈 11(분석 해설 한 덩어리): `quantgen_desktop/narrative_view.py` `NarrativeView` — 해설을 창 언어로 소제목+글머리표로 보여 주고 전체 문단은 아래 접기(`FullTextFold`). `ToolPane.finished(..., sections=)`가 모든 분석 도구에 적용. 내보내기 문장은 그대로. 문장 분할기는 Flet 없는 `ui/narrative_sections.py`로 옮김(`ui/ai_panel.py`가 재수출).
3. `quantgen_desktop/owner_ui_language/<영역>.py`: 영역별 한국어 표시 문구(`PAIRS`), `translations.py`가 기존 카탈로그 뒤에 병합. 같은 영어에 영역마다 다른 한국어를 주면 거부.

## 두 에이전트가 다른 앱을 고친 이유와 재발 방지 (2026-11-11, 소유자 지적)

소유자: "gpt와의 인계를 정확히 진행해라. 둘이 다른 기반으로 앱개발 하고있던게 말이되냐"

- 원인: 2026-10-30(⑬-2/d) 이후 화면 작업은 Claude·GPT 모두 네이티브(`quantgen_desktop/`)에서 했는데, 2026-11-10 소유자
  스크린샷이 Flet 화면이어서 Claude UI 세션이 Flet(`ui/*.py`)을 고쳤습니다(PR #98). 시작 전에 `LEDGER.md`의 `⑬-2/` 기록으로
  기준 앱을 확인하지 않았고, 끝낸 일을 `LEDGER.md`에 적지 않고 GPT가 읽지 않는 이 문서에만 적었습니다.
- 조치: (1) 소유자 결정 UI-D1~D4 — UI 기준 앱은 네이티브 하나. (2) `AGENTS.md` 6절과 2절 2단계, `README.md` 파일 표에 이
  문서를 GPT 필독으로 연결. (3) `LEDGER.md`에 ⑬-2/owner-14-flet(PR #98), ⑬-2/ui-base-owner-decision 기록. (4) 레포 루트
  `AGENTS.md`·`CLAUDE.md`에도 같은 규칙(작업 브랜치 `claude/friendly-bardeen-r6xe8f`, main 병합 시 적용). (5) 메인
  `CURRENT.md`를 쓰는 Claude 세션(task claude-resume-20261103, next_ids에 ⑬-2/a3·⑬-2/k)에 같은 내용을 전달.
- 네이티브 이식 진행: 영역 5개 중 4개(market `fc2d8e3`, strategy `b278ad9`, ficc `dc1dc78`, risk `12b6ad5`) 병합·푸시,
  charts_macro 진행 중. 그 뒤 전체 CI 단계 재실행 → 독립 검토 → 컴플라이언스 → 이 문서 `완료`, `LEDGER.md`에 ⑬-2/owner-14-native.

## 진행 중 — 영역 5개 병렬 (각자 브랜치 `owner-ui-native-<영역>`, 컨테이너 로컬 → 통합 후 work_branch로 병합)
| 영역 | 파일 | 이슈 |
|---|---|---|
| strategy | `quantgen_desktop/strategy.py`(+`strategy_view.py`), `core/research/strategy_analysis.py`(source "best") | 01·06·07·09·10·11·14·04 |
| charts_macro | `charts.py`, `chart_study.py`, `macro.py`, `macro_records.py`, `macro_narrative_language.py` | 02·11·14 |
| ficc | `bonds.py`, `rates.py`, `structuring.py`, `fx.py` 및 해설 모듈 | 03·08·11·14·04 |
| market | `watchlist*.py`, `qscore.py`, `market_tools.py`, `markets_view.py`, `market_chart.py` | 05·04·14·03·11 |
| risk | `app.py`(몬테카를로·셸), `portfolio.py`, `signals.py`, `core/research/{analysis,portfolio_analysis,signals_analysis}.py`(source "best") | 13·04/12·14·11 |

규칙(모든 영역): 표시만 바꿈 — 계산값·판정 코드·내보내기 보고서 불변, 영어/한국어 실행 중 전환 유지, GPT의 배치 도구(`form_layout`·`table_layout`·`result_layout`·`category_picker`·`typography` 역할) 사용, 줄바꿈 바이트 그대로.

## 다음 (Claude가 이어서)
1. 영역 브랜치 병합 → CI와 같은 단계별 unittest(`runtime-smoke.yml`의 unittest 줄을 한 줄씩, `QT_QPA_PLATFORM=offscreen`) → 수정 전후 캡처 비교.
2. 독립 검토(정확성·소유자 14건 화면·한국어·GPT UI 보존) → 반영.
3. 컴플라이언스 13/14/19·FACTS 갱신, `python -m tools.compliance.check --refresh-baseline ...` → `--check` PASS.
4. work_branch 푸시, 이 문서를 `status: 완료`로 갱신.

## 세션이 끊겨 GPT가 이어받는 경우
- 컨테이너의 영역 브랜치는 사라짐. work_branch `66470f4`에서 위 표의 영역별로 다시 진행. 각 이슈의 Claude 해결 방식은 `git diff 7ddb568^1 7ddb568 -- ui/<해당 페이지>.py`와 아래 2026-11-10 기록이 기준.
- 금지(위 소유자 결정 그대로): 14건 화면을 이전으로 되돌리기, 글꼴을 Gothic A1로 되돌리기, 14건과 무관한 GPT 네이티브 UI를 Flet 모양으로 바꾸기.

---

# UI 세션 진행 중 — 2026-11-10 KST (Claude, 소유자 UI/UX 검토 14건)

- status: 완료 · main 병합됨 (UI 세션 전용 기록. 메인 `CURRENT.md`·`LEDGER.md`는 다른 Claude 세션
  session_01H6RrzMUzF8vwK8xkX977mB가 쓰는 중이라 건드리지 않음)
- session: https://claude.ai/code/session_016uB1jf8m3p5GW1qzQVJe7k
- work_branch: `claude/friendly-bardeen-r6xe8f` (main `9d1eacd`에서 시작), [PR #98](https://github.com/xkg4real/quantgen/pull/98) main 병합 완료 — merge `7ddb568` (head `6941e6d`, main PR 97·99 포함). GitHub CI 전부 통과(Ubuntu 3.12, Windows 3.11/3.12/3.14, 구문 3.10/3.11, 문서 정합성), Vercel은 소유자 규칙으로 무시
- updated_at: 2026-11-11 03:12 KST, waiting_on: none

## 소유자 요청 (원문)

> @"C:\Users\whydi\Downloads\QUANTGEN_인계_1107.zip" 다음 파일을 바탕으로 앱 내부 UI/UX을 수정해주세요. 제목을 보면 뭘 수정해야할지를 어느정도 알 수 있도록 써놓았기 때문에 잘 보시고 수정해주세요
>
> /ui-ux-pro-max /karpathy-guidelines 등을 적극적으로 사용해주시되, UI/UX의 기본적인 mood나 틀에서 크게 벗어나지 않도록 주의해주세요

zip = Flet 앱(main.py, ui/*.py) 스크린샷 14장. 파일 제목이 곧 지시입니다. 요지:
01 검증 요약 칩이 너무 작음 · 02 매크로 z-점수 차트와 해설 패널을 아무도 못 읽음 · 03 숫자 천 단위 콤마(명목금액), DV01 라벨 줄바꿈 ·
04/12 데이터 출처 선택기 삭제(앱이 알아서 가져올 것), 자동/auto 불일치 · 05 실시간 시세 화면 행·열 정렬과 글자 크기 ·
06 전략 결과에 좋은/나쁜 전략 판정이 없음 · 07 카드 ID(M_C4_funding) 노출 · 08 금리 곡선 방법이 3개뿐 · 09 검증 표가 외계어 ·
10 전략 실험실 전체 정리 · 11 분석 패널이 한 덩어리 문단 · 13 포트폴리오 회색 화면 · 14 한국어/영어 섞임.

## 결정과 이유

| 결정 | 이유 |
|---|---|
| 대상은 Flet 화면(ui/*.py). 네이티브 PyQt는 공유 core와 금리 방법 목록만 | 스크린샷이 Flet(Flutter 회색 오류 상자, '5초마다 조회' 문구 등)임을 코드로 확인 |
| 13 원인: `expand=True` 입력칸이 `Row(wrap=True)` 안에 있어 Flutter가 회색 상자를 그림 | 컨테이너에서 Flet 웹+Playwright로 재현하고, 폭 고정 시 정상 렌더 확인 |
| 출처 선택기는 숨기고(visible=False) 값은 유지, `core.quant.history`에 `source="best"` 추가 | UI-8 선례(2026-11-03). 기존 `auto`는 FMP 키가 없으면 합성으로 떨어지고 그 불변식이 테스트로 고정돼 있어, 화면용으로 키 없는 Yahoo를 먼저 묻는 경로를 따로 둠 |
| 번역은 페이지 묶음별 `core/ui_page_messages/*.py`(setdefault 병합) + `LocalText` | 병렬 작업 충돌 방지, 기존 검토된 번역 우선 |
| 판정 코드 PASS/REVISE/REJECT는 그대로 두고 한국어 뜻을 옆에 | `core/ui_messages.py` 정책: 판정 코드는 바꾸지 않음 |

## 진행 상황

- [x] 기반 커밋 `ae8a313`, `55bcba9` (공용 헬퍼, source="best").
- [x] 영역 브랜치 8개 구현·병합(a–h), 독립 검토 4관점(정확성·소유자 14건 화면·한국어·주장/고지) → 검토 반영 브랜치 4개(s/q/f/m) 병합.
- [x] 통합 정리: 페이지 문구가 검토된 메시지 키(price→기준값 등)를 가리지 않게 함, 그릭스 지수 표기 제거(영문·한국어 공용 `_greek`), 매크로 한국어 만기 표기, CRLF 복구, CI 경로 필터·새 시험 6종.
- [x] 컴플라이언스 07/08/12/13/14/15/19/20·FACTS 갱신, `--refresh-baseline` → consistency PASS, publication BLOCKED(변화 없음), 소스 641.
- [x] CI 단계별 재현: unittest 14묶음 1,069개 중 1,067개 통과. 실패 2개는 main에서도 동일: A3 MC 콤보(다른 세션 PR #90), `desktop_market_chart_acceptance` 오래된 시각 표시(KST 자정 직후 날짜 경계 시간 의존). 스크립트형 시험 전부 통과.
- [x] 수정 후 캡처(ko 1360/1000, en): 컨테이너 `/tmp/claude-0/qgshots/final/` (세션 종료 시 사라짐).

## 남은 일 (소유자 결정 또는 후속)

1. 병합 후 CI 조정: 곡선 기존 방법 기록값 비교는 NS/NSS의 적합 곡선(0.05bp)과 RMSE로(매개변수는 플랫폼마다 다름), installed 작업 제한 45분. 실제 Windows 화면·실제 제공처(Yahoo/FRED/KIS) 응답은 미확인.
2. 알려진 한계: 네이티브 PyQt 화면은 공유 core 외 미변경. 실시간 차트 SVG 머리글 '1d'와 구분 기호(core/market/presentation.py, 네이티브 공유), 금리 결과표 만기 1m/1y(flet_a1_headers 시험이 언어 간 셀 동일성을 요구), '오 년 단리'(forward_convention 시험이 문자열 고정), 일부 네이티브 한국어 해설 안의 영문 조각(ETF 제공처 원문, ETH/BTC ADF 문장).
3. 시간 의존 시험 `test_old_market_timestamp_is_labelled_stale_despite_fresh_transport` 고정 시계 적용 제안.

---
이전 기록 (2026-11-07 GPT UI 세션)

# 최종 상태 — 2026-11-07 KST

**PR89 main 병합 완료**: https://github.com/xkg4real/quantgen/pull/89
Merge `6a09d3fd367cfc14fd62378deed8c441001c6e1b`, source `2f336a363210176b9309fed6aaa3e571630ab4b7`. 아래 이전 중간기록의 main미병합/검사미완료 안내보다 이 최종상태가 우선합니다.

- 글꼴/compactUI/수정된regression19검사 PASS(83.537s). 패키징/정책50 PASS(3.777s). 기존31검사 중29통과와2수정재검사 결과를 중복합산하지 않습니다.
- 한글11172실제힌트/400500600, 전체UI문자coverage, KO/EN/light/dark/1000·1360·1920px 및100·125·150% offscreen9화면 검증 PASS. Preview /workspace/shared/quantgen-ui-preview/.
- 문서20종/소스622정합성PASS, 기존공개준비BLOCKED 유지. RemoteCompliance42245900905 success. **Runtime42245900881은 현재진행중**; 후속담당자가 성공/실패를확인하고 실제실패만수정할것. Windows전체CI/실기기표시완료라고말하지말것.
- AWS앱영향큐 docs/product/ui_website_updates/PR-89.json, 송신도구없어queued. 웹HTML/실배포변경없음. UI/AWS보충인수인계만저장, 메인CURRENT/LEDGER미수정.
- 앱을닫고 기존QUANTGEN CMD에서 origin main을pull한뒤 `.venv\Scripts\python.exe -X utf8 -m quantgen_desktop` 실행. 기존.env/KIS키 유지. 사용자요청에따라 실행법전달후작업중지.

---
이전 중간기록 (이하 미병합 상태는 과거 기록)

# QUANTGEN UI 인수인계 — 2026-11-07 KST

## 현재 상태

이번 글꼴·밀도 개선은 **작업 브랜치에 저장됨, main 미병합, 최종 검증 미완료**입니다. 사용자가 인수인계 .md부터 신속히 요청했으므로 중간 상태를 명시합니다. 앱 전체 완료/웹 배포 완료로 말하지 마세요.

- 저장소: https://github.com/xkg4real/quantgen
- 작업 브랜치: `gpt/compact-ui-final-20261107`
- 원격 확인한 최신 커밋: `0222dbad65fdbbadfa83b9a70d37e6207f87a1ae`
- 글꼴 커밋: `4fb61255c0bd579471589e49d2e09f9643d29006`
- 기준 main: `cd4019c2dfd6747594c75fdf417fd465fc66eb7e`
- 현재 경로: `/workspace/quantgen-ui`, Python `/workspace/.venvs/quantgen/bin/python`
- 이전 환경의 `/workspace/work/quantgen-compact-workspace-20261106`과 미push 커밋 `3bafe23`은 환경 교체로 없어졌습니다. 현재 원격 브랜치가 복원본입니다. 이전 검사/이미지를 현재 커밋의 검증으로 혼동하지 마세요.

## 사용자 요구와 권한

- 차트 안내문 등 한글 획 흐림/울퉁불퉁함 개선, 실제 글꼴 교체 허용.
- 분석 도구/설계·검증/분석 등의 지나치게 넓은 메뉴·입력폼·표를 내용에 맞게 압축. TradingView 참고 이미지 같은 밀도, 모든 기능/데이터 보존.
- GitHub에는 앱 관련 코드만. 웹 HTML은 업로드하지 않음. AWS 로그인/키 재요청 금지.
- 수정은 별도 컨펌 없이 진행하고 완료 보고. 최종 보고에 ‘북딱북딱’ 한 번 자연스럽게 포함.
- 완료 직후 CMD 업데이트/실행법 안내. 키 설정은 이미 성공했으므로 `.env`를 초기화하지 않음.
- 메인/Claude 인수인계는 `handoff`의 `UI_SESSION_CURRENT.md`로 보존. 메인 `CURRENT.md`, `LEDGER.md`, `AUTO_STATE*`는 수정하지 않음.

## 반영한 파일과 동작

1. `assets/fonts/`, `quantgen_desktop/font_policy.py`, `app.py`
   - Gothic A1의 실제400/500/600 hinted TTF를 QG Interface로 이름 변경하여 동봉.
   - 원본 Google Fonts 고정 ref `38411257417e616c5d4daa1b9e91a3dbcebe1c2e`, ofl/gothica1.
   - 한글 전체11172자와 실제 힌트 구성요소를 보존. 없는 기호는 기존 Pretendard에서 QG Symbols 별도 보충.
   - 완전한6파일을 등록하며 부분 실패 시 플랫폼 글꼴 유지/로그. 브라우저 Flet 기존OTF 유지. 런타임 다운로드 없음.
   - `README.txt`, `OFL-GothicA1.txt` 출처/해시/라이선스. `tools/ui/build_hinted_fonts.py` 재생성. pyproject/stage.py에TTF포함.
2. `category_picker.py`, `app.py`, `typography.py`
   - 분석 도구 버튼을 글자폭으로 배치하고 좁으면 줄바꿈. 선택/키보드/기존 연결 유지.
   - 패널16px 여백, 페이지24px, 버튼/입력/탭 여백 축소. 표14px.
3. `form_layout.py`, `tools.py`, `bonds.py`, `portfolio.py`, `app.py`
   - 공통/Portfolio/Monte Carlo3열, Bonds4열 기준224px 입력폭, 좁으면 재배치.
   - 실제폭에 맞춘 패널 최소높이 재계산으로 긴 설명 잘림 방지. 실행버튼은 내용폭/좌측.
4. `table_layout.py`, `result_layout.py`
   - 표 전체Stretch 제거, 내용폭/숫자정렬/최소34px행, 긴내용 자동확장.
   - 좁은2~3열표 줄바꿈, 넓은표 내부스크롤. 쌍 결과패널 최대960px.
   - 분석 계산/요청/보고서 값·KIS·권한·주문 기능은 변경하지 않음.

## 검증 상태 — 미완료를 유지

현재 `/tmp/qg-layout.log`에서 Markets 탭11검사, A3 결과/요청보존8검사 등 통과 출력을 확인했지만 **전체 프로세스 최종 종료코드/총합은 아직 확인하지 않았습니다**.

기존 responsive test의 ‘일부러 잘못된 native width hint를 주면 전체페이지 overflow’ 사전 조건은 새 최대폭 정책으로 성립하지 않아 실패했습니다. 원격0222dba에서는 ‘주입한 hint 자체가 viewport보다 크다’를 검사하도록 조정했고 값/선택/언어보존 검사는 유지했습니다. 실행 중인 오래된 테스트 프로세스가 수정 전 파일을 로드했을 수 있어 해당 검사 재실행이 필요합니다. 실패를 숨기거나 전부PASS로 기록하지 마세요.

남은 일:
- 최종 레이아웃/글꼴/기존 조작 검사 실행 및 실제 실패 수정.
- 현재 TTF+기호의 전체UI문자/11172한글/실제굵기/힌트/패키지 검사. 기존 typography 테스트는 새TTF+기호coverage로 변경됨; 신규 실제hint 검사는 추가해야 함.
- KO/EN, light/dark,1000/1360/1920폭,125/150% 배율 화면 확인. Linux offscreen으로 사용자 Windows 획 선명도를 전부 보장하지 않음.
- `docs/compliance/19-licenses.md` 현재서체 설명과13/14/15/FACTS/source-review 갱신. 이전 환경에서만 했던 이 문서수정은 현 원격에는 아직 없음. 기존 공개준비BLOCKED/운영 검증 조건 유지.
- 앱PR 생성/검사/병합, `docs/product/ui_website_updates/PR-N.json`, UI/AWS보충인수인계. 직접 채팅 송신 도구가 없으므로 큐저장과 송신/배포 구분.

## 다음 담당자 명령

```bash
cd /workspace/quantgen-ui
git fetch origin main handoff
git status --short
QT_QPA_PLATFORM=offscreen XDG_CACHE_HOME=/tmp/qg-cache MPLCONFIGDIR=/tmp/qg-mpl /workspace/.venvs/quantgen/bin/python -m unittest tests.desktop_a3_layout_acceptance tests.desktop_responsive_tools_acceptance tests.desktop_operation_fixes_acceptance tests.desktop_typography_acceptance -v
```

네트워크 자격증명 값을 출력하지 마세요. 현재 환경에서는 일반 `git push origin HEAD`가 실제 성공했습니다. 기존 환경의 GitHub대형blob 우회 작업은 필요 없습니다.

## 사용자 CMD 안내 — main 병합 후 제공

앱을 닫고 CMD에 아래3줄 전부 순서대로 입력합니다. PowerShell용 아님. 경로 앞의 프롬프트나 `.claude` 문자열을 복사하지 않습니다. 아직 이번 브랜치 main병합 전이므로 이 명령만으로 미병합 UI가 적용된다고 말하지 마세요.

```bat
cd /d "C:\Users\skymi\OneDrive\문서\GitHub\quantgen"
for /d %G in ("%LOCALAPPDATA%\GitHubDesktop\app-*") do @if exist "%G\resources\app\git\cmd\git.exe" set "QG_GIT=%G\resources\app\git\cmd\git.exe"
"%QG_GIT%" --no-pager pull --ff-only origin main && .venv\Scripts\python.exe -X utf8 -m quantgen_desktop
```

사용자는 크레딧/시간에 매우 민감합니다. 새 범위를 추가하거나 이미통과한 변동없는검사를 무작정 반복하지 말고 남은 오류와 배포 연결을 끝내세요.
