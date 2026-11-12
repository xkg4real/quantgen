# Claude → GPT 인계 (사용량 소진) — 2026-11-12 16:55 KST · UI 세션

이 문서는 UI 세션(네이티브 PyQt 앱)의 인계서입니다. 같은 브랜치의 `CURRENT.md`는 다른 작업(`claude-resume-20261103`, work_branch
`claude/adoption-outcome-20261112`)이 쓰고 있으므로 건드리지 않았습니다. UI 작업의 기준 문서는 `UI_SESSION_CURRENT.md`, 끝난 일은
`LEDGER.md`(`⑬-2/` ID)입니다. 이 파일만 읽어도 이어서 할 수 있게 썼습니다.

- status: handoff
- reason: Claude 주간 사용량 소진. 소유자 원문: "아 근데 너 토큰없네. 일단 GPT한테 내가 ㅈ마지막으로 명령한거까지 인계해서 정확하게 넘겨줘",
  이어서 "브랜치 올리고 끝나자마자 GPT 인계자료 및 인수인계용 .md 파일을 지난주처럼 만들어줘. 지금 사용량 다 찼다"
- from: claude (세션 c958d211) → to: GPT
- work_branch: `claude/friendly-bardeen-r6xe8f` · work_commit: `7402a43` (원격에 푸시됨, main `0786200` 위 6커밋)
- main: `0786200` (PR https://github.com/xkg4real/quantgen/pull/109 병합, 2026-11-12 15:13 KST). 후속 작업 PR은 아직 없음 — **소유자가 요청할 때만** 만들 것.
- 필독: `UI_SESSION_CURRENT.md` 맨 위 소유자 결정(UI-D1~D6)과 R-D9~R-D10 규칙, `LEDGER.md`의 `⑬-2/` 행.

## 0. 소유자 답 — 인계 직후 (2026-11-12 약 16:57 KST) · 아래 모든 절보다 우선

Claude가 물은 4개(6절)에 대한 답, 원문 그대로:
> 1. 그냥 커서를 '차트위'로 올려두면
> 2. ofcourse
> 3. 이것도 당연하지 병신아
> 4. 일단 공개하는데, 상용화시에는 삭제도 검토. 우선 공개버전으로 개발

확정 해석(구속력 있음):
- **A1 (R-D12 손 모양 커서)**: 마우스가 차트 위에 있으면 언제나 손 모양(펼친 손), 끄는 중엔 쥔 손. "움직일 수 있을 때만" 조건은 두지 않음. 차트 밖(오른쪽 칸·도구줄)에서는 보통 화살표.
- **A2 (Q-SCORE 범위)**: 미국 주식까지 넓힘. 상세 화면 카드(R-D13-1)와 시장 순위(R-D15) 모두 국내 + 미국. 자료 경로는 **이미 허용된 것만**: 미국 일별은 앱이 이미 쓰는 경로(KIS 해외 일별이 허용 32개 안에 있으면 그것, 아니면 지금 미국 차트가 쓰는 Yahoo 일별)를 쓰고, 새 KIS 경로·새 호스트는 추가하지 않음(필요하면 소유자 승인부터). 방법론이 바뀌므로 `core/research/qscore.py`를 Q-SCORE v0.2로 올리고(국내 v0.1 결과는 그대로 재현), 미국용 입력(수정주가 여부, 200거래일 기준)과 출처를 카드·보고서·규정 문서에 밝힘.
- **A3 (시장 메뉴)**: "코인→크립토로 바꾸고 ETF 추가" 해석이 맞음. 840ae95 그대로 유지.
- **A4 (R-D15 Q-SCORE 순위 공개)**: **공개 버전으로 개발** — 3절 R-D15의 "기본으로 꺼 두기" 권고는 폐기, 기본으로 보임. 다만 상용화 때 삭제를 검토하므로 한 곳(설정 플래그 또는 상수 하나)에서 끌 수 있게 만들고, 규정 문서 12-claims에 "소유자 결정 2026-11-12: 공개 버전으로 개발, 상용화 시 삭제 검토, 법률 검토(자본시장법 투자자문/유사투자자문) 미완료"를 기록. 문구 제한(매수·추천·유망·사야 할·Top Pick 금지, "실험적 지표 · 투자 권유 아님" 표시)은 그대로.

## 1. 끝나서 work_branch에 올라간 것

| 커밋 | 내용 | 확인 |
|---|---|---|
| `c508a0d`, `793a321`, `5916c36` | R-D12-1/2: 상세 차트 Ctrl+휠 확대(커서 기준), +/− 키·버튼 제거, 좌클릭 끌기로 좌우 이동(←/→ 유지), 키 안내 "← → · 끌기 이동 · Ctrl+휠 확대·축소". 규정 문서 15-keyboard 날짜 메모, FACTS 앵커 `chart-zoom-drag-2026-11-12`, 기준선 갱신 | 상세 차트 시험 통과, compliance --check PASS |
| `36d23b8` | 소유자 PC 캡처 버그: 상세 화면 오른쪽 "종목" 칸이 7자리 가격(SK하이닉스 1,255,000)에서 좌우로 잘림 → 가격·등락이 한 줄에 안 들어가면 위아래로 쌓음, 카드 최소폭 축소, 칸의 가로 스크롤을 0에 고정. 회귀 시험 `test_the_right_column_never_moves_sideways_with_seven_digit_prices`(1440x900·1280x800·1000x700) | `tests.desktop_stock_detail_acceptance` + `tests.desktop_home_markets_markets_acceptance` 78개 OK(608초). 고치기 전엔 시험 실패(334 > 324) |
| `840ae95` (원래 `f4ac417`을 체리픽) | UI-D11 본체: 레일 "시장" = 지수·주식·크립토·선물·외환·국채·회사채·ETF·월드 이코노미 큰 범주 + 마우스 올리면 3단 하위 메뉴(`quantgen_desktop/rail_menu.py` 신규), 국내·미국 ETF 목록(각 약 20종, 주식과 같은 시세 경로, 시가총액 기준 없음), "코인"→"크립토" | 워크트리에서 레일·시장·순위 시험 통과 후 커밋. 합친 브랜치(`7402a43`)에서 `market_rankings`·`desktop_home_markets_shell`·`desktop_home_markets_markets`·`kis_workspace` 128개 OK(413초, 인계 직후 완료 — KIS 허용 경로 시험 포함) |
| `7402a43` | 규정 기준선 갱신(UI-D11) | compliance --check consistency PASS, publication BLOCKED(이전과 같음) |

## 2. 소유자 원문 — 이번 주 마지막 지시까지 (순서대로, 그대로)

1. (트레이딩뷰식 메뉴 그림: 지수 › 주식 › 크립토 › 선물 › 외환 › 국채 › 회사채 › ETF › 월드 이코노미 ›)
   > 좋은데 시장 하위 유아이를 저렇게 두지 말고 이런식으로 큰 범주로 묶고 저기 뭐 주식 하부 유야이다 그러면 거기 마우스 휠 올려놓으면 더 하부로 국내, 미국, 글로벌 뭐 이런 식으로 볼수있고 거기서 국내에 마우스 올려놓으면 다시 거래대금 거래량 급상승 급하락 이렇게 누를수있게. 누르면 지금 ui랑 똑같이 저 화면으로 바로 넘어갈수잇게 그니까 바꾸라는게 아니야. 지금 시장 안의 ui는 괜찮다. 새꺄 그리고 코인이 뭐야 ETF라해야지
2. > 아 그리고 차트 확대를 +-로 하지말고 컨트롤 + 마우스 휠 이렇게 하자
3. > 그리고 화살표 말고 차트 화면 좌클릭해서 좌우로 끌면 좌우도 움직일수잇게 !! 화살표도 유지하고
4. > 아 그리고 상세차트 들어가면 Q-SCORE 도 같이 볼수있게 하자. !!
5. > 그리고 기술지표들 우리 사이트 내에서 판단한걸 묶어서 pdf나 이런걸로 내보내기 하는 기능도 되면 좋겠다 상세차트에서
6. > q스코어도같이
7. (오른쪽 종목 칸이 잘린 캡처) > 그리고 여기 이렇게 잘리는 버그잇어. 이거 금방 다 끝낼수잇나?
8. > 그리고 시장에서 거래대금 거래량 등등 목록에서 마지막에 Q-SCORE 해서 이거 높은 것들만 모아서 보여줘도 괜찮긴 하겠다. 다만 법령검토가 필요하긴 함 !! 일단 구현해봐
9. > 그리고 우리가 명시적으로 보여주진 않을거지만, Q-SCORE 높을수록 사실상 매수해야하는 종목인거야. 알고있지?
10. > 아 근데 너 토큰없네. 일단 GPT한테 내가 ㅈ마지막으로 명령한거까지 인계해서 정확하게 넘겨줘
11. > 브랜치 올리고 끝나자마자 GPT 인계자료 및 인수인계용 .md 파일을 지난주처럼 만들어줘. 지금 사용량 다 찼다

상태: 1(본체)·2·3·7 완료. 1의 리뷰 수정, 4·6(Q-SCORE 카드), 5·6(내보내기), 8(Q-SCORE 순위)은 4절.

## 3. 해석 규칙 (Claude가 정하고 소유자 지시로 구속력 있음 — 그대로 지킬 것)

**R-D11 (시장 메뉴)**
- R-D11-1. 레일의 시장 하위 메뉴 = 그림의 큰 범주, 그 순서: 지수, 주식, 크립토, 선물, 외환, 국채, 회사채, ETF, 월드 이코노미. 각 줄에 "›". "코인"이라는 글자는 어디에도 쓰지 않음(코인 시장 = "크립토").
- R-D11-2. 범주에 마우스를 올리면(키보드 Enter / →) 오른쪽에 하위 시장 메뉴, 하위 시장에 올리면 다음 메뉴에 순위 기준(거래대금 · 거래량 · 급상승 · 급하락 · 시가총액). 잎을 누르면 지금의 시장 화면으로 그 시장·기준이 선택된 채 바로 이동. 데스크톱 메뉴바식 연쇄 메뉴(QMenu 연쇄 가능), 앱 모양(옅은 선, 넉넉한 줄, Pretendard, N3).
- R-D11-3. 시장 화면 자체는 바꾸지 않음("바꾸라는게 아니야. 지금 시장 안의 ui는 괜찮다").
- R-D11-4. 데이터가 있는 것만: 주식 › 국내/미국(글로벌은 경로가 없으면 빼고, 빈 메뉴 금지). 크립토 › 순위 기준 바로. ETF › 국내/미국(주식과 같은 경로: KIS inquire-price / 해외 시세, 없으면 Yahoo 일별). 지수 › 홈 카드의 지수. 선물·외환·국채·회사채·월드 이코노미 → 이미 있는 분석 화면(파생/선물, FX, 금리/채권, 거시). 새 호스트·새 KIS 경로 금지.
- 소유자에게 아직 묻지 않은 해석 하나: "코인이 뭐야 ETF라해야지"를 "코인 → 크립토로 바꾸고 ETF도 추가"로 구현함. 소유자가 "코인 자리에 ETF"만 원한 것인지는 확인 안 됨.

**R-D12 (차트 조작)** — 완료. Ctrl+휠(위=확대, 커서 아래 봉 기준), +/−·=/_ 키와 −/+ 버튼 제거, 휠만은 아무 일 없음(페이지도 안 움직임), 오른쪽 칸 위 Ctrl+휠은 차트 확대 안 함. 좌클릭 끌기 = 커서 아래 봉이 마우스를 따라감, 손 모양 커서(끄는 중 쥔 손), 클릭만 하면 봉 선택, 끝에서 멈춤. 미해결 질문: 손 모양 커서를 "움직일 수 있을 때만" vs "항상".

**R-D13-1 (상세 화면 Q-SCORE)** — 상세 화면 오른쪽 "종목" 탭 위쪽에 Q-SCORE 카드: 점수 0~100, 별, 짧은 해요체 한 줄, 엔진이 이미 주는 세 부분(기술 신호 70 %, 최대 낙폭 15 %, 꼬리 손실 15 %)을 쉬운 이름의 작은 막대로, 기준 시각, "실험적 지표 · 투자 권유 아님". 머리/띠 영역에 작은 Q-SCORE 배지(차트를 가리지 않음, R-D9-1). 화면이 이미 불러온 일별 자료로 직접 계산(`core.research.qscore.compute_q_score`, UI 스레드 밖, 과도 호출 방지). 방법론 그대로(Q-SCORE v0.1: 국내 주식, KIS 수정 일별, 200거래일 이상). 계산 못 하면 "산정 불가"만 쓰지 말고 이유와 조건을 쉬운 말로(예: "국내 주식만 · KIS 연결과 200거래일 이상 일별 자료가 있어야 계산돼요").

**R-D14-1 (내보내기)** — 상세 화면 "내보내기" 동작 하나로 이 종목에 대해 앱 엔진이 판단한 것을 보고서로 저장: 머리(이름, 코드, 시장, 간격·기간, 자료 출처·기준 시각, 내보낸 시각), 화면 그대로의 차트 그림, 가격 요약, 켜 둔 지표의 값 + 짧은 해요체 해설(가이드 카드와 같은 문장, 선택 시 전체 지표), "지금 이 차트" 요약, Q-SCORE(있으면 점수·부분, 없으면 이유) — 소유자 "q스코어도같이", 면책 문구("교육용 해설 · 투자 권유 아님"). PDF가 주 형식(번들 글꼴로 한글 내장, A4, 앱 같은 깔끔한 배치), 그 외 차트 PNG, 같은 판독의 JSON/CSV. 저장 대화상자, 기본 이름 `QUANTGEN_<code>_<YYYYMMDD>.pdf`, 사용자가 경로를 고르기 전엔 아무것도 쓰지 않음, 네트워크 없음, 화면에 없는 자료 없음.

**R-D15 (시장 목록 Q-SCORE 순위, 소유자 8·9번)** — 아직 Claude가 해석을 확정하지 못했으므로 아래는 권고안. 소유자에게 확인 후 진행할 것:
- 국내 주식 시장 화면의 순위 기준 마지막에 "Q-SCORE"(높은 순) 추가. Q-SCORE v0.1은 국내 주식만 되므로 미국 주식·크립토·ETF에는 넣지 않음(또는 넣고 "국내 주식만 계산돼요"라고 비활성).
- 계산: 목록 후보(예: 거래대금 상위 N종목) 각각에 KIS 수정 일별 200거래일 이상이 필요 → 이미 허용된 KIS 일별 경로만, 새 경로·호스트 금지, 요청 수 제한·캐시(하루 1회 등), UI 스레드 밖. 계산 못 한 종목은 목록에서 빼지 말고 "계산 안 됨"으로 아래에.
- 문구: "Q-SCORE 높은 순", "실험적 지표 · 투자 권유 아님"만. **"매수", "추천", "유망", "사야 할", "Top Pick" 같은 말 금지.**
- 법령: 소유자가 "법령검토가 필요하긴 함"이라고 했음. 자체 점수로 종목을 줄 세워 보여주는 것은 자본시장법상 투자자문업/유사투자자문업(불특정 다수에게 투자 판단 정보 제공) 해당 여부 검토가 필요. `docs/compliance/12-claims*`(주장 문서)에 이 기능과 "법률 검토 전 공개 금지"를 기록하고, 공개 상태는 지금처럼 BLOCKED 유지. 소유자 확인 없이는 기본으로 꺼 두는(설정 플래그) 것을 권고.
- **소유자 9번 발언 처리**: "Q-SCORE 높을수록 사실상 매수해야하는 종목"은 소유자 의도로 이 문서에만 기록. 앱 문구·코드 주석·문서·광고 문구에 넣지 말 것. 근거: `core/research/qscore.py` 모듈 설명이 "전략도 수익 예측기도 아님"이라고 밝히고 있고, 높은 점수가 이후 수익과 관련 있다는 검증(백테스트·표본 외 검증)이 저장소에 없음. 이 의도로 순위를 공개하면 사실상 매수 권유가 되어 위 법령 문제가 더 커짐 → 소유자에게 이 점을 알리고 결정을 받을 것(Claude는 이 답을 아직 소유자에게 하지 못함).

## 4. 끝나지 않은 일 — 다음 단계(명령과 완료 기준)

시작 전: `git fetch origin && git checkout -B ui-followup origin/claude/friendly-bardeen-r6xe8f` (또는 같은 브랜치에서 계속). 모든 시험은 `QT_QPA_PLATFORM=offscreen`.

1. **합친 브랜치 확인** (D11 관련 128개는 이미 OK — 1절. 상세 차트까지 함께 한 번 더 돌려 기준을 잡을 것)
   `QT_QPA_PLATFORM=offscreen python -m unittest tests.market_rankings_acceptance tests.desktop_home_markets_shell_acceptance tests.desktop_home_markets_markets_acceptance tests.kis_workspace_acceptance tests.desktop_stock_detail_acceptance`
   완료 기준: 모두 OK. 실패하면 D11(840ae95)과 36d23b8/R-D12의 충돌부터 볼 것.

2. **UI-D11 리뷰 수정** — patch `UI_WIP/ui-d11-review-fixes_base-840ae95.patch` (이 브랜치에 있음, 6파일: app.py, localization.py, rail_menu.py, shell_rail.py, tools.py, typography.py; **시험 안 됨, 중간 상태**). 적용: `git show origin/handoff:UI_WIP/ui-d11-review-fixes_base-840ae95.patch > /tmp/d11.patch && git apply -3 /tmp/d11.patch`.
   리뷰가 찾은 항목(제목만 남음, 각각 직접 재현·확인할 것): 정확성 — 시장 전환 중 남은 대기 요청(stale pending), 전환 중 화면을 떠날 때, 언어 처리 중복 호출; 소유자 눈높이 — 메뉴 안내 문구, 줄이 모두 보이는지, 메모, 도구 상태, 클릭 동작, 메뉴 간격, 그림자 영역 클릭, 줄 높이, ETF 이름, 크립토 자리 표시.
   완료 기준: 위 1번 시험 + 레일 메뉴 캡처(ko/en, light/dark, 1440x900·1000x700)에서 메뉴가 잘리지 않고 잎 클릭이 맞는 시장·기준으로 감. 그다음 규정 문서: FACTS에 `rail-categories-2026-11-12` 같은 앵커와 UI-D10 때처럼 관련 문서(01, 06, 07, 08, 09, 10, 12, 13, 14, 15, 19, 20)에 날짜 메모 → `python -m tools.compliance.check --refresh-baseline --reviewed-by "<이름>" --review-note "<12자 이상>"` → `--check` PASS.

3. **UI-D13 Q-SCORE 카드·배지** (R-D13-1) — patch `UI_WIP/ui-d13-qscore-card_base-5916c36.patch` (6파일: 신규 `quantgen_desktop/stock_qscore.py` 649줄, stock_detail.py, stock_detail_side.py, stock_detail_style.py, market_chart.py, owner_ui_language/stock.py; **빌드 중간 상태, 시험·캡처 없음**). `git apply -3`로 적용(stock_detail_side.py는 36d23b8과 겹칠 수 있음 — 오른쪽 칸 가로 스크롤 0 고정과 숫자 줄 쌓기는 반드시 유지).
   완료 기준: 국내 종목(예: 005930)에서 카드에 점수·별·세 부분·기준 시각·면책이 보이고, 미국 종목/자료 부족 시 이유 문장이 보임; 계산이 UI 스레드를 막지 않음; 새 시험(`tests/desktop_stock_detail_acceptance.py`에 추가) 통과; 1440x900·1000x700 캡처에서 차트를 가리지 않음; 오른쪽 칸 7자리 가격 시험 계속 통과; 규정 기준선 갱신.

4. **UI-D14 내보내기** (R-D14-1) — patch `UI_WIP/ui-d14-export_base-5916c36.patch` (3파일: 신규 `core/market/stock_report.py` 502줄 보고서 모델, `quantgen_desktop/owner_ui_language/report.py`, `owner_ui_language/__init__.py`). **아직 없음**: `quantgen_desktop/stock_report.py`(PDF/PNG/JSON/CSV 작성기 + 저장 대화상자 + 문구 목록), 상단 도구줄 "내보내기" 동작 하나, 시험, 표본 파일. Claude는 QPdfWriter로 Pretendard(QG Interface OTF)를 PDF에 넣을 때 숫자·자간 글꼴 기능(tnum/kern/liga)에 따른 차이를 보던 중이었음(결론 미기록) → PDF의 한글·숫자가 깨지지 않는지 직접 열어서 확인할 것. Q-SCORE는 3번이 계산한 값을 보고서에 넣을 것("q스코어도같이").
   완료 기준: 대화상자에서 고른 경로에만 파일 생성, PDF(A4, 한글 내장)·PNG·JSON·CSV 생성, JSON/CSV와 PDF의 판독이 같음, 네트워크 호출 없음, 시험 추가·통과, 규정 기준선 갱신.

5. **R-D15 시장 목록 Q-SCORE 순위** — 3절 R-D15를 소유자에게 확인한 뒤 구현. 완료 기준: 국내 주식 순위 기준 마지막 "Q-SCORE"(높은 순), 문구 금지어 없음, 새 KIS 경로/호스트 없음(`tests.kis_workspace_acceptance` 통과), 12-claims에 법률 검토 항목 기록, 시험 추가.

6. 소유자에게 물어본 것 — **0절에서 모두 답함**: ① 손 모양 커서를 움직일 수 있을 때만/항상 ② Q-SCORE를 미국 주식까지 넓힐지 ③ "코인→크립토 + ETF 추가" 해석이 맞는지 ④ R-D15 공개 여부·법률 검토 방식과 9번 발언의 위험.

7. 끝날 때마다: 작업 브랜치 푸시 → `LEDGER.md`에 `⑬-2/` 행 추가(형식은 기존 행과 같게) → `UI_SESSION_CURRENT.md` 갱신. 새 PR은 소유자가 요청할 때만.

## 5. 시험·CI 참고

- 상세 차트: `tests.desktop_stock_detail_acceptance` (약 10분). 시장/레일: `tests.desktop_home_markets_markets_acceptance`, `tests.desktop_home_markets_shell_acceptance`, `tests.market_rankings_acceptance`.
- CI: `.github/workflows/runtime-smoke.yml` (installed 작업: ubuntu 3.12, windows 3.11/3.12/3.14, 제한 120분). 새 시험 파일을 만들면 CI 단계에도 추가.
- 새 창은 Fusion 스타일·번들 글꼴 기준(`quantgen_desktop.use_fusion_style()`, `use_interface_fonts()`). Windows CI는 이 둘이 없으면 폭이 달라져 실패함.
- 규정: 소스가 바뀌면 `python -m tools.compliance.check --check`가 FAIL → 문서 메모 + 기준선 갱신 필요. publication BLOCKED는 원래 상태.

## 6. 금지·제약 (그대로 유지)

`.env`(변수 이름만 언급, 값 금지), `docs/asset_expansion/cache/`(열기·검색·해시 금지), `~/.nextgen`, 고정 하니스, research 브랜치, `tools/nautilus/**` 손대지 않음. 실제 Anthropic API 호출 금지. Vercel 상태 무시·댓글 금지. 웹사이트 HTML 수정·업로드 금지. KIS 허용 경로는 소유자가 승인한 price-detail 포함 32개로 고정, 새 네트워크 호스트 금지. 소유자 결정 UI-D1~D6(네이티브 기준, Pretendard + N3) 되돌리지 않기. "봉"이라는 낱말 금지(분/일/주/월/년). 차트 영역은 어떤 패널도 가리지 않음(R-D9-1). 소유자에게는 한국어로.

## 7. 증거 경계

컨테이너 로컬 워크트리(`.claude/worktrees/rail-d11`, `qscore-d13`, `report-d14`)와 Claude 스크래치(캡처 `d11_shots/` 등)는 세션과 함께 사라짐 — 남는 것은 work_branch 커밋과 이 브랜치의 `UI_WIP/*.patch`뿐. patch 셋은 시험되지 않은 중간 상태이며 완료 증거가 아님. 1절 840ae95의 합친 상태 시험은 인계 직후 128개 OK로 끝남(LEDGER ⑬-2/ui-d11-rail/a 행의 "미확인"은 이 결과로 해소).
