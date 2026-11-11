"""Korean display text for the owner UI port, area: market. See the package docstring.

Markets tools (Derivatives, ETF, KRX, Crypto): result headings, chart legends and axes, row and column
names, and the codes shown in their tables (owner issues 03, 14; 2026-11-10). Codes keep the code beside
their Korean meaning, as the native status captions do ('미실행(NOT_RUN)'). Wording follows the reviewed
Flet catalogue (core/ui_page_messages/ficc_pages.py) where it has the term.
"""

PAIRS = {
    # Derivatives: headings, legends, axes, check names, codes
    'Futures & volatility': '선물·변동성',
    'Implied volatility smile': '내재 변동성 스마일',
    'Risk-neutral density': '위험중립 확률밀도',
    'Hedge simulation': '헤지 시뮬레이션',
    'Static arbitrage checks': '정적 차익거래 점검',
    'Black-76 IV %': 'Black-76 내재 변동성 %',
    'SVI IV %': 'SVI 내재 변동성 %',
    'Q density': '위험중립 밀도',
    'Index points': '지수 포인트',
    'Density': '밀도',
    'call_vertical': '콜 수직 스프레드',
    'call_butterfly': '콜 버터플라이',
    'put_vertical': '풋 수직 스프레드',
    'put_butterfly': '풋 버터플라이',
    'COMPUTED': '계산 완료(COMPUTED)',
    'NOT_RUN': '미실행(NOT_RUN)',
    'UNAVAILABLE': '산출 불가(UNAVAILABLE)',
    'NOT_LOADED': '불러오지 않음(NOT_LOADED)',
    'NOT_APPLICABLE': '해당 없음(NOT_APPLICABLE)',
    'True': '예',
    'False': '아니오',
    # ETF
    'ETF price / NAV': 'ETF 가격 / NAV',
    'Price / NAV': '가격 / NAV',
    'NAV premium': 'NAV 괴리율',
    'Premium %': '프리미엄 %',
    'Premium · %': '프리미엄 · %',
    'Premium statistics': '괴리율 통계',
    'Last premium %': '최근 괴리율 %',
    'Mean premium %': '평균 괴리율 %',
    'Premium SD %': '괴리율 표준편차 %',
    'Mean |premium| %': '평균 |괴리율| %',
    'Descriptive sleeve backtests': '전략별 백테스트 · 표본 내 기술통계',
    'Trend switch vs buy & hold': '추세 전환 vs 매수 후 보유',
    'Trend': '추세 전환',
    'Trend switch': '추세 전환',
    'Vol target': '변동성 목표',
    'Constituents': '구성종목',
    'Weight %': '비중 %',
    'Tracking error %': '추적오차 %',
    'Shares outstanding': '유통 주식 수',
    'LP holding %': 'LP 보유 비중 %',
    'Target index': '기초 지수',
    'Dividend cycle': '분배 주기',
    'Type': '유형',
    # Crypto
    'Premium / volatility': '프리미엄 / 변동성',
    'Perpetual funding': '무기한 선물 펀딩비',
    '7-day mean annualized %': '7일 평균 연율 %',
    'Annualized · %': '연율 · %',
    'USDT per BTC': 'BTC당 USDT',
    'Weekday observations': '요일별 관측',
    'Observations (n)': '관측 수',
    'Last ETH/BTC ratio': '최근 ETH/BTC 비율',
    'ADF p-value': 'ADF p값',
    '2-year z-score': '2년 z 점수',
    'Unit-root test': '단위근 검정',
    'no rejection of a unit root (the expected null)': '단위근을 기각하지 못함(예상된 귀무가설)',
    'mean-reverting at 5 %': '5% 수준에서 평균회귀',
    'AR(1) amplitude half-life · observations': 'AR(1) 진폭 반감기 · 관측 단위',
    '{half_life} · monotone': '{half_life} · 단조 감쇠',
    '{half_life} · oscillating': '{half_life} · 부호 진동',
    'Not estimated': '추정 불가',
    'Not decaying': '감쇠 없음',
    'Mon': '월', 'Tue': '화', 'Wed': '수', 'Thu': '목', 'Fri': '금', 'Sat': '토', 'Sun': '일',
    'Upbit holdings · read only': 'Upbit 보유 자산 · 조회 전용',
    'Total quantity': '보유 수량',
    'Average buy price': '평균 매수가',
    'KRW value': '원화 평가액',
    # KRX and quote fields (raw keys are shown by these English labels; the export keeps the keys)
    'Quote': '현재가',
    'Last price': '현재가',
    'Open': '시가',
    'High': '고가',
    'Low': '저가',
    'Sector': '업종',
    'Listed shares': '상장 주식 수',
    'As of': '기준 시각',
    'Turnover': '거래대금',
    'Level': '지수',
    'Filer': '제출인',
    'Receipt': '접수번호',
    'Company': '회사명',
    'Statement': '재무제표',
    'Account': '계정과목',
    'This term': '당기',
    'Prev term': '전기',
    # Markets real-time ranked lists (owner 2026-11-11, point 5; quantgen_desktop/market_rankings.py).
    # Short labels (categories, markets, sectors, source states, columns) are the (key, English, Korean)
    # tables of core/market/rankings.py, so that 'KOSPI' or 'Volume' elsewhere in the window is untouched.
    'Real-time charts': '실시간 차트',
    'All sectors': '전체 업종',
    'Refresh the ranked list': '순위 목록 새로고침',
    'Loading quotes…': '시세를 불러오는 중…',
    'Loading… {done}/{total}': '불러오는 중… {done}/{total}',
    'Request failed ({code})': '조회 실패 ({code})',
    'Updated just now': '방금 갱신',
    'Updated {seconds}s ago': '{seconds}초 전 갱신',
    'Updated {minutes} min ago': '{minutes}분 전 갱신',
    'Updated {hours} h ago': '{hours}시간 전 갱신',
    'Not loaded yet. Press Refresh to load the list.': '아직 불러오지 않았습니다. 새로고침을 누르면 목록을 불러옵니다.',
    'Could not load quotes. Trying again shortly.': '시세를 불러오지 못했습니다. 잠시 뒤 다시 시도합니다.',
    'Market cap comes with KIS quotes of domestic stocks only; the data shown has none.':
        '시가총액은 KIS 국내 주식 현재가에만 있습니다. 지금 자료에는 시가총액이 없습니다.',
    'No stock in this list is up.': '이 목록에서 오른 종목이 없습니다.',
    'No stock in this list is down.': '이 목록에서 내린 종목이 없습니다.',
    'No stocks match these filters.': '조건에 맞는 종목이 없습니다.',
    'Ranked among {count} major stocks, not the whole market. Open a row for its chart.':
        '주요 종목 {count}개 안에서 매긴 순위이며 전체 시장 순위가 아닙니다. 종목을 누르면 차트와 정보를 봅니다.',
    'Delayed · daily: the last daily bar; trading value is close × volume, estimated.':
        '지연·일별: 마지막 일봉 기준이며 거래대금은 종가×거래량 추정치입니다.',
    'Could not load {count} of these stocks.': '{count}개 종목은 불러오지 못했습니다.',
    'Left out for old data: {count}.': '오래된 자료라서 뺀 종목 {count}개.',
    '{source} daily bars, last bar {day}; trading value estimated as close × volume.':
        '{source} 일봉 · 마지막 봉 {day} · 거래대금은 종가×거래량 추정',
    # Source state (2026-11-11 compliance follow-up): KIS REST quotes are polled, never called 실시간, in the
    # stock detail view's words ("5초 조회", "조회 시점", US "무료 시세"; owner_ui_language/stock.py).
    '{source} current quotes polled every {seconds} s (REST requests, not a trade stream); last received {when} KST.':
        '{source} 현재가 · {seconds}초마다 조회(REST 요청이며 체결 수신이 아닙니다) · 마지막 수신 {when} (한국 시간)',
    # A round is timed from its start (market_rankings.RankingBoard.due); one that ran longer says so.
    'The last round of requests took {took} s, longer than {seconds} s, so each stock was asked less often than that.':
        '마지막 조회 한 회차가 {took}초 걸려 {seconds}초보다 길었으므로 종목마다 그보다 드물게 조회했습니다.',
    "US quotes are KIS's free feed and can differ from paid consolidated quotes.":
        '미국 시세는 KIS 무료 시세이며 유료 통합 시세와 다를 수 있습니다.',
    # US market cap in the ranked list (owner 2026-11-11, "아니 미국 시총 자료 찾으세요";
    # core/market/market_cap.py). The column heading is core/market/rankings.py CAP_LABELS.
    'Could not read US market cap.': '미국 시가총액을 읽지 못했습니다.',
    'KIS is not connected.': 'KIS가 연결되어 있지 않습니다.',
    'KIS returned no usable market cap.': 'KIS에서 쓸 수 있는 시가총액을 받지 못했습니다.',
    'FMP_API_KEY is not set.': 'FMP_API_KEY가 설정되어 있지 않습니다.',
    'The FMP plan does not include batch quotes.': 'FMP 요금제에 여러 종목 일괄 시세 조회가 포함되어 있지 않습니다.',
    'FMP did not answer.': 'FMP가 응답하지 않았습니다.',
    'yfinance is not installed.': 'yfinance가 설치되어 있지 않습니다.',
    'Yahoo Finance could not be reached.': 'Yahoo Finance에 연결하지 못했습니다.',
    'Yahoo Finance returned no share counts.': 'Yahoo Finance에서 상장주식수를 받지 못했습니다.',
    'Yahoo Finance did not answer in time.': 'Yahoo Finance가 제때 응답하지 않았습니다.',
    'No stock in this list has a market cap.': '이 목록에는 시가총액을 읽은 종목이 없습니다.',
    'These quotes came without market cap.': '이 시세에는 시가총액이 없습니다.',
    'Market cap (computed) = shares outstanding × the price shown; share counts are refreshed daily.':
        '시가총액(계산값) = 상장주식수 × 표시 가격이며, 상장주식수는 하루 한 번 갱신합니다.',
    'No market cap for {count} of these stocks; listed last without a rank.':
        '{count}개 종목은 시가총액을 읽지 못해 순위 없이 맨 아래에 둡니다.',
    'Shares outstanding {shares} ({source}, {day}) × price {price} = {cap}.':
        '상장주식수 {shares} ({source}, {day}) × 가격 {price} = {cap}',
    '{source} market cap, stated {when} KST.': '{source} 제공 시가총액 · {when} (한국 시간) 기준',
    'ADR: the share count is not per ADR, so no market cap is computed.':
        'ADR은 상장주식수가 ADR 단위가 아니어서 시가총액을 계산하지 않습니다.',
    'The share count could not be read.': '상장주식수를 읽지 못했습니다.',
    'Computed: shares outstanding × the price in the row; share counts from {source}, kept for a day.':
        '계산값: 상장주식수 × 행의 가격 · 상장주식수 출처 {source}, 하루 보관',
    'Stated by {source}.': '{source} 제공 수치',
    # Domestic market cap (2026-11-11 compliance follow-up; core/market/rankings.py parse_kis_domestic_cap):
    # KIS's hts_avls only when it agrees with listed shares x price of the same answer, else computed or none.
    'Could not use domestic market cap.': '국내 시가총액을 쓰지 못했습니다.',
    "KIS's market cap differs by more than 25% from listed shares × price of the same answer, so it is not used.":
        'KIS 시가총액이 같은 응답의 상장주식수 × 현재가와 25% 넘게 달라 쓰지 않습니다.',
    # A field KIS sent that is not a usable number is refused with its own reason, never read as absent.
    "KIS's market cap is not a positive number, so it is not used.":
        'KIS 시가총액이 0보다 큰 수가 아니어서 쓰지 않습니다.',
    "KIS's listed share count is not a positive whole number, so the market cap could not be checked or computed.":
        'KIS 상장주식수가 0보다 큰 정수가 아니어서 시가총액을 확인하거나 계산할 수 없습니다.',
    'KIS gave no listed share count, so its market cap could not be checked and is not used.':
        'KIS 응답에 상장주식수가 없어 시가총액을 확인할 수 없으므로 쓰지 않습니다.',
    'KIS gave neither a market cap nor a listed share count.': 'KIS 응답에 시가총액과 상장주식수가 모두 없습니다.',
    'KIS market cap (hts_avls read as 100 million won), stated {when} KST; it agrees within 25% with listed '
    'shares {shares} × price {price} = {computed} of the same KIS answer.':
        'KIS 제공 시가총액(hts_avls를 1억 원 단위로 읽음) · {when} (한국 시간) 기준 · 같은 KIS 응답의 '
        '상장주식수 {shares} × 현재가 {price} = {computed}와 25% 안에서 맞음',
    'Stated by KIS (hts_avls, read as 100 million won) and used only when it agrees within 25% with listed '
    'shares × price of the same KIS answer.':
        'KIS 제공 수치(hts_avls를 1억 원 단위로 읽음)이며, 같은 KIS 응답의 상장주식수 × 현재가와 25% 안에서 맞을 '
        '때만 씁니다.',
    'Computed: listed shares × price, both from the same KIS answer.':
        '계산값: 같은 KIS 응답의 상장주식수 × 현재가',
    "Market cap is KIS's figure, used only where it agrees with listed shares × price of the same answer.":
        '시가총액은 KIS 제공 값이며, 같은 응답의 상장주식수 × 현재가와 맞는 종목에만 씁니다.',
    'Market cap (computed) = listed shares × price, both from the KIS answer.':
        '시가총액(계산값) = KIS 응답의 상장주식수 × 현재가입니다.',
    "No usable market cap for {count} of these stocks; listed last without a rank (each row's tooltip says why).":
        '{count}개 종목은 쓸 수 있는 시가총액이 없어 순위 없이 맨 아래에 둡니다(이유는 각 값의 설명에 있습니다).',
    # Market pages (owner ruling UI-D10, 2026-11-11: 국내 주식 / 미국 주식 / 코인 in the rail; the ranking categories as
    # each market's criteria; quantgen_desktop/market_rankings.py, market_summary.py, core/market/screen.py).
    # Whole sentences only here: short or generic templates ('Open {name}', '{count} results') would rewrite
    # unrelated text anywhere in the window, so they are in PAGE_TEXT below, used by the market page alone.
    "Coins are not ranked by units traded: one coin is worth very different amounts from another. See trading value.":
        '코인은 종류마다 1개의 값이 크게 달라 거래 개수로는 순위를 매기지 않습니다. 거래대금을 보세요.',
    'No source this app uses states coin market cap, so coins are not ranked by it.':
        '이 앱이 쓰는 자료에는 코인 시가총액이 없어 시가총액 순위를 매기지 않습니다.',
    'Find in {market}: name, code, sector': '{market}에서 찾기 · 이름, 코드, 업종',
    'Find coins: name or symbol': '코인 찾기 · 이름이나 기호',
    'Search within {market}': '{market} 안에서 찾기',
    'Conditions: {count} set': '조건 {count}개 적용 중',
    'Narrow this list by change, trading value or market cap.': '등락률, 거래대금, 시가총액으로 목록을 좁힙니다.',
    'The lower bound is above the upper bound.': '최소가 최대보다 큽니다. 두 값을 맞추면 적용합니다.',
    'Clear conditions': '조건 지우기',
    'Remove this filter': '이 조건 지우기',
    'Remove filter: {name}': '조건 지우기: {name}',
    'Outside this list:': '목록 밖에서 찾은 종목',
    'Nothing in this list matches ‘{text}’.': '이 목록에는 ‘{text}’에 맞는 종목이 없습니다.',
    'Coins have no stock screen yet, so this row opens nothing.':
        '코인은 아직 종목 화면이 없어 눌러도 열리지 않습니다.',
    'Ranked among {count} major coins, not the whole market. Prices in US dollars.':
        '주요 코인 {count}개 안에서 매긴 순위이며 전체 시장 순위가 아닙니다. 가격은 미국 달러입니다.',
    "Delayed · daily: Yahoo Finance daily bars by UTC day, today's still moving; trading value is Yahoo's daily "
    "dollar volume.":
        '지연·일별: Yahoo Finance 일별 값(UTC 날짜 기준, 오늘 값은 아직 움직이는 중)이며 거래대금은 Yahoo가 주는 '
        '하루 달러 거래대금입니다.',
    '{source} daily bars by UTC day, last bar {day} (still moving today); prices and trading value in US dollars as '
    'Yahoo states them.':
        '{source} 일별 값 · UTC 날짜 기준 · 마지막 {day} (오늘 값은 아직 움직이는 중) · 가격과 거래대금은 Yahoo가 '
        '주는 미국 달러 값',
    # The index strip (market_summary.py).
    '{source} daily close, last {day}; during the session the last value can still be moving.':
        '{source} 일별 종가 · 마지막 {day} · 장중에는 마지막 값이 아직 움직이는 중일 수 있습니다.',
    "US dollars; a coin's day is the UTC calendar day.": '미국 달러 · 코인의 하루는 UTC 날짜 기준입니다.',
    'Could not load this index ({code}).': '이 지수를 불러오지 못했습니다 ({code}).',
    'Index and coin figures are Yahoo Finance daily closes, read with a delay; not live.':
        '지수와 코인 값은 Yahoo Finance 일별 종가를 늦게 받아 온 것이며 실시간이 아닙니다.',
}

# Short words and templates of the market pages (UI-D10), (English, Korean) by key. Not merged into the window's
# catalogue: as global pairs they would also rewrite unrelated text ('Any', 'Open Interest').
PAGE_TEXT = {
    "conditions": ("Conditions", "조건"),
    "loading": ("Loading…", "불러오는 중…"),
    "coin": ("Coin", "코인"),
    "min": ("min", "최소"),
    "max": ("max", "최대"),
    "any": ("Any", "제한 없음"),
    "or_more": ("{value} or more", "{value} 이상"),
    "between": ("{name} {low} to {high}", "{name} {low} ~ {high}"),
    "at_least": ("{name} at least {value}", "{name} {value} 이상"),
    "at_most": ("{name} at most {value}", "{name} {value} 이하"),
    "results": ("{count} results", "{count}개 종목"),
    "coin_results": ("{count} coins", "코인 {count}개"),
    "clear_all": ("Clear all", "모두 지우기"),
    "open": ("Open {name}", "{name} 열기"),
    "no_coin": ("No coin in this list matches '{text}'.", "이 목록에는 '{text}'에 맞는 코인이 없습니다."),
    "not_found": ("No stock matches '{text}'. Check the name or enter its code.",
                  "'{text}'에 맞는 종목을 찾지 못했습니다. 이름을 고치거나 종목 코드를 입력하세요."),
}

# The market pages' index strip (market_summary.py): Yahoo symbol -> (English, Korean).
INDEX_NAMES = {"^KS11": ("KOSPI", "코스피"), "^KQ11": ("KOSDAQ", "코스닥"), "^GSPC": ("S&P 500", "S&P 500"),
               "^IXIC": ("Nasdaq Composite", "나스닥 종합"), "BTC-USD": ("Bitcoin", "비트코인"),
               "ETH-USD": ("Ethereum", "이더리움")}
