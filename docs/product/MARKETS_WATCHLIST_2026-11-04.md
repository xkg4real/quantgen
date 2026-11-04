# 시장 개편: 관심종목 차트·한 종목 화면·글자·좌측 메뉴·선택 상자

기록일: 2026-11-04 한국시간. 작성: Claude Code. 브랜치 `claude/ui-markets-watchlist-20261104`, 코드 기준 `44ba1c7`(main `f455710`에 이 개편을 더한 것). 네이티브 PyQt6 앱만 바꿨습니다. Flet 브라우저 화면과 웹사이트는 바꾸지 않았습니다.

이 기록은 코드가 하는 일만 적습니다. 실제 Windows 화면과 실제 KIS 응답은 확인하지 않았습니다(미검증).

## 1. 소유자 요청 (원문, 2026-11-04)

> (1) 현재 APP 글자 폰트가, 아무런 생기가 없고 글자 폰트가 깨지는 느낌이 드는 부분들도 많다. 글자 폰트를 필요한 부분들에 조금더 입체적으로 수정바란다. 또한 실시간 지표들을 보여주는 모든 부분에서, '공급자'와 '관측일'칸 자체가 필요가 없다. 또한 모든 차트를 검색할 때에, 종목 코드만이 아닌, 종목 코드와 해당 주식의 이름으로도 검색할 수 있게 수정돼야하고, 현재 시장 에서 KIS CHART, 채권 금리 등 해당 요소들을 스크롤을 통해 선택할수잇는데, 이 기능은 불편하기만 한다. 삭제 필요 또한 '시장' UI에서 주요지표들의 실시간 차트를 제공할 필요가 없다. 해당 화면은 사용자의 선호에 따라 자신이 관심종목으로 추가해놓은 차트들을 확인할 수 있어야하고, 구체적으로 하나의 종목을 검색하였을 때 해당 종목의 모든것들을 한 화면에서 제시해줘야한다. 바로 수정해보고 어플 실행방법 안내바란다.
>
> (2) ㅇㅇ 7A 끝나면 자동으로 메인병합해줘
>
> (3) 그리고 어플의 메인화면이 전체적으로 너무 좁다. 좌측의 ui공간을 조금 얇고 줄여서 메인화면을 탁 트이게 보일 수 있게 수정해야함. 단, 좌측이 답답해지면 안됨. 지금은 너무 널널해
>
> (4) 저 주식 챙권 이런거 종목고르는 옆에있는 화살표있지. 저것도 좀 세련되게 바꿔라 뭐냐 저게 윈도우 xp냐;;
>
> (5) 인터벌 화살표도 마찬가지. 저 화살표와 네모박스는 어디에서도 보고싶지않다.

## 2. 요청별로 바뀐 것

| 요청 | 바뀐 것 | 근거 |
|---|---|---|
| (1) 글자 | 동봉 QG Interface의 400/500/600 굵기만 씁니다(700은 가짜 굵게라 거부). 제목 30/600, 소제목 18/600과 3px 강조 막대, 본문 14, 캡션·표 머리 12, 큰 수치 32/600, 카드 제목·가격 15/600. 패널은 세로 그라데이션과 2px 아래 테두리. 등락은 한국식 상승 빨강·하락 파랑 알약. SVG 차트 글자는 등록 글꼴 `QG Interface`만 지정하고 12px 이상(전에는 9–11px, 쉼표 목록이라 QtSvg가 없는 글꼴로 읽음). 칩 제거 버튼 `✕`(동봉 글꼴에 없음)를 `×`로 바꿈 | [글자·스타일](../../quantgen_desktop/typography.py), [SVG](../../core/market/presentation.py), [가이드](../../quantgen_desktop/indicator_guide.py) |
| (1) 공급자·관측일 칸 | 차트의 출처·시각 두 줄, Home 상세 창의 공급처·관측일 행, 매크로 표의 출처·관측일 열, 외환 캐리 표의 금리 관측일·오래된 관측 열, KRX의 공급자 줄(KIS일 때)과 `source`·`as_of` 행, ETF의 `as_of` 행을 화면에서 뺐습니다. 남는 곳은 화면마다 다릅니다. 시장 카드·공유 가격 차트·종목 정보·Home 상세 창에는 보고서 내보내기가 없어 tooltip에만 있습니다. 매크로·외환 캐리 표는 열만 숨기므로 내보내기에 그 열이 남습니다(도구 내보내기는 화면에 넣은 행으로 만듦, tools.py:226, :271). KRX·ETF 시세 표도 행을 화면에서만 숨기므로(market_tools.py:16 `hide_rows`, :113, :240) 내보내기에는 KRX `source`·`as_of`와 ETF `as_of` 행이 남습니다. KIS로 받은 KRX 결과의 공급자와 `as_of`는 화면·tooltip에는 없고 내보내기에만 있습니다. 공급자·날짜 글자가 그대로 남은 도구는 6절 7번에 적었습니다 | [차트](../../quantgen_desktop/market_chart.py), [Home 상세](../../quantgen_desktop/watchlist.py), [매크로](../../quantgen_desktop/macro.py), [외환](../../quantgen_desktop/fx.py), [ETF·KRX](../../quantgen_desktop/market_tools.py) |
| (1) 코드·이름 검색 | 시장 검색창과 Build & Test, 포트폴리오, Signals, Strategy Lab, ETF, KRX의 종목 칸에서 코드·한글 이름·영어 이름·한글 초성으로 찾습니다. 고르면 코드가 들어갑니다. 영어 이름은 Home 6종목과 동봉 해외 126종목에만 있습니다. KIS 종목 마스터에는 영어 이름이 없어(directory.py:67, :164) 그 밖의 국내 종목은 영어 이름으로 찾지 못하고 영어 화면에서는 코드로 보입니다(:76-85). 모의매매 규칙 편집기의 종목 칸(paper.py:164)에는 검색이 없습니다. 선물·채권은 시장 검색 막대에서 코드로만 엽니다 | [검색](../../core/market/directory.py), [시장 화면](../../quantgen_desktop/markets_view.py) `SymbolCompleter`, [앱](../../quantgen_desktop/app.py) `attach_symbol_searches` |
| (1) 스크롤 선택 삭제 | 시장의 자산별 탭 9개와 안쪽 탭(스크롤 화살표가 생기던 줄)을 없앴습니다. 10개 분석 도구는 새 왼쪽 메뉴 “분석 도구”에서 5열 2행 버튼으로 고릅니다. System 화면의 “데스크톱 이전 상태” 글도 분석 도구 10개를 적습니다(app.py:674) | app.py `TOOL_PANES`·`make_tools` |
| (1) 시장 = 관심종목 차트 + 한 종목 화면 | 지표 차트 4개(UI-7)를 없애고, 이용자가 고른 관심종목의 차트 카드를 보입니다. 카드나 검색 결과를 고르면 그 종목의 가격 차트와 종목 정보를 한 화면에 보입니다 | markets_view.py `WatchlistGrid`·`StockView`, [종목 정보](../../core/research/stock_profile.py) |
| (1) 실행 방법 안내 | 아래 10절 | |
| (2) 7A 뒤 자동 병합 | 해당 없음이 됐습니다. 소유자가 같은 날 U4-나로 main 병합 동결을 풀었으므로 이 브랜치는 평소대로 PR과 CI 통과 뒤 병합합니다([소유자 결정 기록](../nautilus_bridge/OWNER_RULINGS_LOG.md)) | |
| (3) 좌측 메뉴 | 고정 222px 대신 가장 긴 메뉴 이름(14px/600)에 여백을 더해 폭을 정하고 168–208px로 제한합니다. 오프스크린 측정은 영어 182px, 한국어 176px입니다. “PERSONAL RESEARCH”와 미리보기 두 줄을 뺐습니다(미리보기 안내는 System 화면에 있음). 영어 메뉴 이름 “Technical indicator guide”는 “Indicator guide”로 줄였습니다 | app.py `fit_sidebar`, typography.py `SIDEBAR_WIDTH_RANGE` |
| (4) 종목 고르는 선택 상자 화살표 | 선택 상자의 네모 칸과 기본 화살표를 없애고 얇은 꺾쇠 SVG를 그립니다(열리면 위쪽). 목록은 둥근 모서리입니다 | typography.py `controls_stylesheet`, [꺾쇠](../../assets/ui/chevron-down-light.svg) |
| (5) 인터벌 화살표·네모박스 | 같은 규칙을 창 전체에 적용합니다: 주기 선택을 포함한 모든 선택 상자, 숫자 상자의 위아래 버튼, 넘치는 탭 줄의 넘김 버튼은 상자 없는 꺾쇠, 스크롤 막대는 화살표 버튼 없이 얇게, 카드의 `×` 버튼은 상자 없음 | 같은 파일 |

## 3. Claude가 정한 것과 이유

1. **10개 분석 도구는 지우지 않고 “분석 도구 / Analysis tools” 화면으로 옮겼습니다.** 요청은 스크롤로 고르는 방식을 지우라는 것이었고 도구 자체를 지우라는 말은 없었습니다. 도구는 보이는 버튼 격자로 고릅니다.
2. **선물·채권은 시장 검색 막대의 종류 선택(국내 파생·해외 파생·채권)으로 코드를 입력합니다.** 이름 목록은 주식만 있고, 선물·채권 코드는 자산 구분이 있어야 해석됩니다.
3. **공급자·관측일 칸과 줄을 빼고, 지연·오래된 자료·실패 상태는 화면 글자로 남겼습니다.** 공급자와 시각이 남는 곳은 화면마다 다릅니다(2절 표). 대체(Yahoo) 자료는 차트의 “KIS 대신 Yahoo Finance 자료입니다(지연·수정 전 가격)”(market_chart.py:1074)와 종목 정보 섹션 노트의 “Yahoo Finance 일별 종가 (수정 전·지연)”(stock_profile.py:785)로 글자에 남습니다. 관심종목 카드는 출처가 KIS(`KIS`·`KIS REST`, markets_view.py:42)가 아니면 “지연 시세”만 보이고 Yahoo 이름은 tooltip에만 있습니다(markets_view.py:459-466). 근거: [09번](../compliance/09-dark-patterns.md)의 “화면을 간결하게 만드는 변경이 오래된 값·불완전 자료·자료 이용권의 은폐가 되어서는 안 됩니다”, [12번](../compliance/12-claims.md)의 지연 안내, [08번](../compliance/08-third-parties.md)의 “대체 응답은 출처를 ‘Yahoo Finance’로 표시”(차트에 관한 2026-11-03 문장), [권리 목록](../../core/research/display_rights.json)의 공급자·관측일·지연 표시 조건.
4. **KIS 종목 마스터는 자동 갱신이 켜진 창에서만 키 없이 백그라운드로 받고, 프로세스 메모리에만 두며 디스크에 쓰지 않습니다.** 근거: [07번](../compliance/07-data-minimization.md)의 “종목 마스터는 프로세스 메모리”, [FACTS](../compliance/FACTS.md)의 “종목 master도 메모리”. 저장소에 스냅숏을 넣으면 `kis_krx` 저장·재배포 조건에 걸립니다.
5. **관심종목은 QSettings 키 `markets/watchlist`에 자산 구분·코드·거래소만 저장합니다(최대 20개, 기본은 Home의 국내주식 6개).** 이름·가격은 저장하지 않으므로 오래된 이름이나 시세가 남지 않습니다.
6. **Home의 고정 종목 목록(6종목)과 열 구성은 바꾸지 않았습니다.** 요청 (1)의 글자와 공급자·관측일 부분은 Home에도 적용했습니다. 변동 열은 한국식 상승 빨강·하락 파랑(watchlist.py:934-936), 열 머리는 12/600(:812), 종목 코드 알약은 12px(:815)입니다. 상세 창에서 공급처·관측일 행을 뺐고(:540-563), 오래된 관측은 안내문에 날짜를 적습니다(:355-359).
7. **Flet 브라우저 화면은 바꾸지 않았습니다.** 요청한 화면 구조(자산별 탭, 지표 차트 4개, 좌측 메뉴)는 네이티브 앱의 것이고, 웹사이트는 2026-11-03 소유자 결정에 따라 수정하지 않습니다. 다만 공유 SVG의 글꼴 이름·글자 크기 변경은 Flet 차트에도 적용됩니다.

## 4. 한 종목 화면

**보이는 것:** 코드·거래소, 이름, 가격, 등락. ☆ 관심종목 추가 / ★ 해제. 가격 차트(기존 차트 그대로: 주기, 지표 5개, 체결 갱신, 확대). 종목 정보 섹션:

| 섹션 | 내용 |
|---|---|
| 주요 지표 | 시가·고가·저가·거래량, 시가총액(계산값: 가격 × 상장 주식 수), PER, EPS, 업종, 상장 주식 수 |
| 52주 범위 | 52주 최고·최저, 범위 내 위치, 최고·최저 대비 |
| 기간 수익률 | 1주·1개월·3개월·6개월·1년(가격 기준, 배당 제외) |
| 위험 지표 | 과거 일별 수익률로 계산. “과거 자료이며 예측이 아님” |
| 기술적 신호 | 기존 신호 계산(`compute_signals`)과 Signals 화면 문구. “매수·매도 추천이 아닙니다” |
| 기술 지표 | SMA 20, EMA 12·26, RSI 14, MACD(12/26)와 시그널(9), 볼린저 상단·하단 |
| 투자자별 순매수 | 외국인·기관·개인, 최근 5·20거래일 합계(주). 보고된 날이 모자라면 tooltip에 “M거래일 중 N일만 보고됨” |
| 공매도 | 최근·20거래일 평균 공매도 수량과 비중. 평균에 빠진 날이 있으면 tooltip에 보고된 날 수 |
| 제공되지 않는 정보 | 뉴스, 애널리스트 의견·목표주가, 배당, 호가, 해외 종목 재무 지표. 대체 자료일 때 “실시간 체결: KIS 자료에서만 제공”. 못 받은 섹션과 그 이유 |

**보이지 않는 것:** 공급자 칸과 관측일 칸. 공급자 이름과 기간·조회 시각은 각 행의 tooltip에 있습니다. 이 화면에는 보고서 내보내기가 없습니다. 대체(Yahoo Finance) 자료와 오래된 자료는 섹션 노트에 글자로 적습니다. 공매도 섹션 노트는 비중의 정의로 “KIS가 제공하는 공매도 거래량 비중”이라고 적습니다. 주식이 아닌 종류(선물·채권)는 차트만 보이고 “종목 정보는 주식에만 제공합니다”라고 적습니다.

## 5. 자료원과 요청

| 무엇 | 언제 | 요청 |
|---|---|---|
| 관심종목 카드 | 자동 갱신이 켜진 창에서 시장 화면이 보일 때. 15초마다 차례 확인, `KIS`로 판정된 카드 3분·그 밖 15분, 실패 1·2·5·15분 | 카드마다 일별 120봉(수정주가): KIS 먼저(현재가 포함), 주식은 KIS가 응답하지 못하면 Yahoo Finance |
| 종목 정보 | 종목을 열 때(자동 갱신 켬) | 일별 260봉(수정주가): KIS 먼저, 주식은 Yahoo Finance 대체. 국내주식만 KIS `inquire-price`, `investor-trade-by-stock-daily`(20일), `daily-short-sale`(20일). 모두 기존 허용목록 경로 |
| 가격 차트 | 종목을 열 때(자동 갱신 켬) | 기존 차트 경로 그대로: 이력 조회 뒤 지원되는 체결 연결 |
| 종목 마스터 | 자동 갱신이 켜진 창에서 종목 검색 칸에 처음 포커스가 갈 때. 실패하면 10분 뒤 다음 포커스에서 다시 | `kospi_code.mst.zip`, `kosdaq_code.mst.zip`(키 없음, 파일 이름만) |

없어진 요청: 지표 차트 4개가 하던 KIS 지수·환율, Yahoo `^KS11`·`^GSPC`·`KRW=X`, FRED `DEXKOUS`·`DGS10`. Home의 기존 조회는 그대로입니다. 합성 자료는 시장 화면에 쓰지 않습니다.

저장: `markets/watchlist`만 새로 저장합니다. 종목 마스터, 카드 시세, 종목 정보는 프로세스 메모리에만 둡니다. 자세한 정책 대조는 [FACTS](../compliance/FACTS.md#markets-watchlist-2026-11-04)와 01·04·06·07·08·09·13·14·15·19·20번 문서의 2026-11-04 절에 있습니다.

## 6. 이 기록 시점에 알려진 문제

1. **(고침) 실제 KIS 카드가 “지연 시세”로 표시되고 15분 간격으로 조회되던 문제.** 카드는 출처 문자열이 `KIS`와 같은지로 판정했는데, 실제 KIS 일별 응답의 출처는 `KIS REST`입니다(data/kis_workspace.py:229). 이제 `KIS`·`KIS REST`를 KIS로 봅니다(markets_view.py:42, :464, :608. Q-SCORE의 qscore.py:113과 같은 집합). 시험 `test_kis_rest_cards_are_live_and_the_search_popup_follows_the_theme`은 출처 `KIS REST`인 가짜 응답을 씁니다. 실제 KIS 응답으로는 미검증입니다.
2. **(고침) 검색 목록에서 종목을 고른 뒤 검색창에 그 코드가 다시 들어가던 문제.** 고를 때 코드를 다음 이벤트에 한 번 더 쓰는데, 종목을 여는 쪽이 검색창을 먼저 비워서(markets_view.py:1059) 비운 칸에 코드가 다시 들어갔습니다. 이제 다음 이벤트의 재기록은 칸이 아직 고른 글자나 그 코드를 담고 있을 때만 합니다(markets_view.py:323-330). 시험 `test_choosing_a_search_row_opens_the_stock_and_leaves_the_search_empty`(오프스크린).
3. **공급자 이름을 화면에서 키보드로 읽을 경로가 없습니다.** tooltip은 마우스 hover에서만 보이고, Home 상세 창에서도 공급처 행을 뺐습니다(예외: Yahoo 대체 안내 글자, 매크로·외환 캐리의 보고서 내보내기, 7번의 남은 글자). 보조기술 경로는 일부 있습니다. Home 표의 각 셀은 tooltip을 접근성 설명으로도 두고(watchlist.py:930-931), 가격 셀의 tooltip에는 공급자 이름(YFINANCE·FRED·KIS)과 시각 줄이 있습니다(:285-309). 표는 키보드로 셀을 옮겨 다니고 Enter로 상세 창을 엽니다(:367-375). 가격 차트 그림은 포커스를 받고 접근성 이름이 “캔들 차트 · {공급자}”입니다(market_chart.py:50, :1148). 관심종목 카드와 종목 정보 행은 접근성 이름·설명에 공급자가 없고 tooltip에만 있습니다. Windows 스크린리더가 이 설명과 이름을 읽는지, Qt가 카드·글자 행의 tooltip을 설명으로 넘기는지는 미검증입니다.
4. **외환 캐리 표의 오래된 금리 칸 색 `#B26B00`은 두 테마 모두 4.5:1 미만입니다**(LIGHT 4.17·3.73, DARK 3.86·3.43). `⚠`를 함께 둡니다. 얇은 스크롤 막대 손잡이도 배경과 3:1 미만입니다([14번](../compliance/14-contrast.md)).
5. **매크로 표의 행별 관측일은 tooltip에만 있습니다.** 행별 오래된 표시 규칙은 원래 없었습니다.
6. **(고침) 종목 검색 목록이 창의 색을 따르지 않던 문제.** QCompleter 목록은 부모 없는 별도 창이라 주 창의 스타일시트가 닿지 않습니다. 이제 테마를 정하거나 바꿀 때마다 모든 종목 칸의 목록에 직접 스타일을 줍니다(typography.py:138 `popup_stylesheet`, markets_view.py:270 `SymbolCompleter.set_theme`, app.py:1040-1041). 닿지 않던 창 스타일시트의 `QListView#symbolPopup` 규칙은 지웠습니다. 소스 색 대비는 글자/바탕 LIGHT 14.99:1·DARK 14.10:1, 선택·hover 행 LIGHT 12.76:1·DARK 9.26:1입니다([14번](../compliance/14-contrast.md)). 목록 안쪽 여백을 없애 두 줄 결과에 스크롤 막대가 생기지 않게 했습니다(오프스크린 캡처). Windows 스타일에서의 모습은 미검증입니다.
7. **공급자·날짜 글자가 그대로 남은 도구가 있습니다.** 요청은 “모든 부분에서” 공급자·관측일 칸을 없애는 것이었지만 이 기록의 변경은 다음 글자를 바꾸지 않았습니다. 외환: 모든 결과의 “Data sources” 표(Series·Provider·First·Last·Note, fx.py:38-39)와 차트 축 이름의 기간(:63, :79). 매크로: “As of {기준일} · {공급자: 개수}” 줄(macro.py:44-46). 금리(rates.py:59-60)·채권(bonds.py:99-100)·구조화 상품(structuring.py:40)·파생상품(market_tools.py:41)·ETF(:104)·가상자산(:164): 결과 머리의 공급자와 날짜. KRX: 실패이거나 KIS가 아닌 출처일 때 “Provider:” 줄(:228-229).
8. **(기록함) UI 변경 기록.** 2026-11-03 소유자 결정은 UI 변경마다 `docs/product/ui_website_updates/` 기록을 요구합니다([소유자 결정 기록](../nautilus_bridge/OWNER_RULINGS_LOG.md) 326행). 이 브랜치의 PR #71을 연 뒤 [PR-71.json](ui_website_updates/PR-71.json)을 썼습니다. 웹사이트 반영은 별도 세션 담당이며 이 기록은 수신을 뜻하지 않습니다.

## 7. 미검증

- 실제 Windows 화면: 글꼴 렌더링, DPI 125·150%, 꺾쇠·스크롤 막대 모양, 좌측 메뉴 폭.
- KIS 종목 마스터의 고정폭 형식(이 환경에서 받지 못함), 6자리가 아닌 단축코드로 빠지는 종목 수, 마스터 이름(한자 등)의 글꼴 지원.
- 실제 KIS 응답: 투자자별 매매·공매도 필드, 260봉에 필요한 페이지 수, 호출 한도.
- 설치물(wheel)에서 꺾쇠 SVG가 그려지는지. Linux에서 만든 설치물에 8개 파일이 `share/quantgen/assets/ui`로 들어가고 설치 환경의 `application_root()`가 그 폴더를 가리키는 것까지는 확인했습니다(2026-11-04, 파일 존재만).
- 실제 Windows Tab 순서, IME 조합 입력, 스크린리더 발화.
- 공급자 계약상 출처 표시 의무. 저장소에는 검토 조건만 있습니다([표시권 검토](MARKET_DISPLAY_RIGHTS_2026-10-31.md)).

## 8. 확인 방법

모든 시험은 오프라인입니다. 공급자는 가짜이고 HTTP·Yahoo 요청은 시험을 실패시킵니다. Qt는 offscreen입니다.

| 시험 | 확인하는 것 |
|---|---|
| [tests/desktop_markets_watchlist_acceptance.py](../../tests/desktop_markets_watchlist_acceptance.py) | 관심종목 저장·기본값·잘못된 항목·20개 제한, 카드에 공급자·날짜 글자가 없고 지연·오래된 자료는 보임, 실패 뒤 마지막 차트 유지, 카드·검색으로 한 종목 화면 열기, 추측하지 않는 검색, ☆·× 추가·삭제, 모든 종목 칸의 코드·이름 검색, 영어 모드에 한글 없음, 자동 갱신이 꺼지면 조회·다운로드 없음, 출처 `KIS REST` 카드는 지연 표시 없이 3분 간격, 두 테마에서 모든 종목 칸의 검색 목록 색, 검색 목록에서 고른 뒤 시장 검색창이 빈 채로 남음, KRX 시세 표는 `source`·`as_of` 행을 화면에서 숨기고 내보내기 자료에 남김 |
| [tests/market_directory_acceptance.py](../../tests/market_directory_acceptance.py) | 코드·이름·초성 검색 순위, 코드 형식, 마스터 분석, 실패 처리, 파일 쓰기 없음, 동봉 글꼴로 모든 이름 표시 |
| [tests/stock_profile_acceptance.py](../../tests/stock_profile_acceptance.py) | 섹션 계산(손 계산과 대조), 허용목록 경로와 호출 횟수, 대체 자료 표시, 합성 자료 미사용, 공급자·관측일 칸 없음, 영어에 한글 없음, 새 endpoint 없음 |
| [tests/desktop_typography_acceptance.py](../../tests/desktop_typography_acceptance.py) | 400/500/600 굵기만 사용, SVG 글자 12px 이상과 등록 글꼴, 한국식 등락 색의 AA 대비, 패널 안 알약 색, 좌측 메뉴 폭과 두 언어의 메뉴 이름, 소제목 막대 높이, 화면 글자의 동봉 글꼴 지원, 글꼴 파일이 없을 때 경고 |
| [tests/desktop_market_tabs_acceptance.py](../../tests/desktop_market_tabs_acceptance.py) | 시장 화면에 탭 줄·지표 차트 없음, 두 언어에서 도구마다 버튼 한 번으로 도달, 도구 화면에 출처 선택 상자 없음, Home 상세가 그 종목 화면을 엶, 차트의 대체 자료 안내 |

꺾쇠, 상자 없는 `×` 버튼, 얇은 스크롤 막대를 확인하는 시험은 없습니다.

이 문서 커밋에서 실행한 결과는 아래 9절에 적습니다. 카드 Enter·Space, 카드에서 `×`로 Tab, 검색 목록 방향키·Enter·Esc, 도구 버튼 Space·방향키는 일회성 오프스크린 확인이며 시험 파일에 없습니다.

## 9. 실행 결과 (이 문서 커밋)

2026-11-04, Linux, Python 3.13, PyQt6 offscreen, `.env` 읽기 끔, 네트워크 차단(시험 자체가 HTTP·Yahoo 요청을 실패로 처리). 코드 기준은 이 문서 커밋의 작업 트리입니다(6절 1·2·6번 수정과 KRX·ETF 행 숨김 포함).

| 모듈 | 시험 수 | 결과 |
|---|---:|---|
| `tests.desktop_markets_watchlist_acceptance` | 12 | 통과 |
| `tests.desktop_typography_acceptance` | 14 | 통과 |
| `tests.market_directory_acceptance` | 21 | 통과 |
| `tests.stock_profile_acceptance` | 34 | 통과 |
| `tests.desktop_market_tabs_acceptance` | 11 | 통과 |
| `tests.desktop_language_acceptance` | 7 | 통과 |
| `tests.desktop_acceptance` | 22 | 통과 |
| `tests.desktop_market_acceptance` | 12 | 통과 |
| `tests.desktop_market_chart_acceptance` | 26 | 통과 |
| `tests.desktop_watchlist_acceptance` | 19 | 통과 |
| `tests.desktop_qscore_acceptance` | 11 | 통과 |
| `tests.desktop_market_layout_acceptance` | 4 | 통과 |
| `tests.desktop_operation_fixes_acceptance` | 7 | 통과 |
| `tests.desktop_responsive_tools_acceptance` | 5 | 통과 |
| `tests.desktop_indicator_guide_acceptance` | 8 | 통과 |
| `tests.desktop_macro_language_acceptance` | 10 | 통과 |
| `tests.desktop_authored_prose_language_acceptance` | 9 | 통과 |
| `tests.desktop_home_live_acceptance` | 3 | 통과 |

설치물 확인: `tools/packaging/stage.py`로 허용 파일만 모아 만든 wheel을 새 가상환경에 설치하고 저장소 밖에서 `tools/packaging/smoke_desktop.py`를 실행해 `PASS`를 받았습니다(실제 공급자·모의투자 엔진·공식 원장은 `NOT_RUN`). 새 시험 셋은 수정 전 코드로 되돌리면 실패하는 것을 확인했습니다. `tests/run_all.py` 전체 실행과 Windows CI는 이 기록에 포함하지 않았습니다(미검증).

## 10. 실행 방법 (Windows)

1. 저장소 폴더에서 브랜치를 받습니다: `git fetch` 다음 `git switch claude/ui-markets-watchlist-20261104` (main에 병합된 뒤에는 `git switch main`과 `git pull`).
2. 처음 한 번만: `py -m venv .venv` 다음 `.venv\Scripts\python.exe -m pip install ".[desktop]"`.
3. `Start-QUANTGEN-Desktop.cmd`를 두 번 누릅니다. 이 파일은 저장소 폴더로 이동한 뒤 `.venv`의 Python으로 `python -m quantgen_desktop`을 실행하므로 받은 코드가 실행됩니다.
4. 실행한 코드가 맞는지 `git log -1 --oneline`으로 확인합니다. 설치된 `quantgen-desktop` 명령이나 다른 폴더에서 실행한 `python -m quantgen_desktop`은 마지막으로 `pip install`한 사본을 실행할 수 있습니다.
5. KIS 키가 없어도 인터넷 연결이 있으면 시장 화면의 종목 이름 검색과 주식 카드·가격 이력이 동작합니다(자동 갱신은 기본으로 켜져 있음, app.py:186). 국내 전체 종목 이름 목록은 키 없이 받습니다(data/kis_markets.py:657-671). KIS 키가 없으면 카드와 한 종목 화면의 가격 이력과 가격으로 계산하는 섹션은 주식(국내, 미국·홍콩·일본·중국)에 한해 Yahoo Finance 일·주·월봉으로 받습니다(지연·수정 전 가격, core/market/routing.py `default_chart_router`). `.env`의 KIS 설정(`KIS_APP_KEY`, `KIS_APP_SECRET`)이 있어야 하는 것: 국내주식의 PER·EPS·업종·상장 주식 수와 그것으로 계산하는 시가총액, 투자자별 순매수, 공매도, 실시간 체결 갱신, 분·틱봉, 선물·채권 차트(app.py:75-85). 실제 KIS·Yahoo 응답은 미검증입니다.
