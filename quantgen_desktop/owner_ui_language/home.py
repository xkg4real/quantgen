"""Korean display text for the owner UI port, area: home. See the package docstring.

Research Home redesign (owner request 2026-11-11, decision UI-D7 point 4): market cards that page left and
right, the selected market's large chart, the watchlist chart cards, the research sections and the full
quotes table in a closed fold. Owner-approved page draft 2026-11-17: tiles, key figures and the chart on the
left, the watchlist rows and research in the right column; Korean prose in 해요체.

`PAIRS` joins the window catalogue (static chrome the LanguageController translates: section headings and
the fold title). `TEXT`, `MARKETS` and `UNITS` are read only by `quantgen_desktop.home_view`, which renders
its cards and chart captions in the window language itself; they stay out of the window catalogue so that
short words such as '1M' or 'Refresh' on other screens are never rewritten.
"""

PAIRS = {
    'My research': '내 연구',
    'All quotes table': '전체 시세 표',
    'Markets and Korean stocks, live connection and Q-SCORE': '주요 시장·국내 주요 종목 시세, 실시간 연결, Q-SCORE',
}

# key: (English, Korean). Templates use {name} fields in both languages.
TEXT = {
    'section': ('Major markets', '주요 시장'),
    'section_note': ('Daily observations · pick a tile to change the chart below', '일별 관측 · 타일을 누르면 아래 차트가 바뀌어요'),
    'refresh': ('Refresh', '새로고침'),
    'refresh_name': ('Refresh the markets, the chart and the watchlist', '주요 시장, 차트, 관심종목 새로고침'),
    'previous': ('Previous markets', '이전 시장'),
    'next': ('Next markets', '다음 시장'),
    'page': ('{first}–{last} of {total}', '{total}개 중 {first}–{last}'),
    'add': ('Add stocks', '종목 추가'),
    'add_tip': ('Search a stock on Markets and press ☆ to add it here.',
                '시장 화면에서 종목을 검색해 ☆를 누르면 여기에 추가돼요.'),
    'daily': ('Daily closes', '일별 종가'),
    'range_1m': ('1M', '1개월'),
    'range_3m': ('3M', '3개월'),
    'range_6m': ('6M', '6개월'),
    'range_1y': ('1Y', '1년'),
    'range_name': ('Show {range}', '{range} 보기'),
    'period': ('{range} change {change}', '{range} 변동 {change}'),
    'card_name': ('{name} {value} {change}', '{name} {value} {change}'),
    'not_loaded': ('Not loaded', '조회 전'),
    'chart_off': ('Not loaded yet. Automatic refresh is off: press Refresh to load the daily closes.',
                  '아직 불러오지 않았어요. 자동 새로고침이 꺼져 있어서 새로고침을 누르면 일별 종가를 불러와요.'),
    'chart_waiting': ('The daily closes load when Research Home is shown.', '연구 홈을 열면 일별 종가를 불러와요.'),
    'chart_loading': ('Loading the daily closes…', '일별 종가를 불러오는 중…'),
    'chart_failed': ('Could not load the daily closes ({reason}). Press Refresh to try again.',
                     '일별 종가를 불러오지 못했습니다 ({reason}). 새로고침을 눌러 다시 시도하세요.'),
    'chart_kept': ('Refresh failed ({reason}); the last chart is shown.', '갱신 실패 ({reason}), 마지막 차트를 보여 줘요.'),
    'chart_stale': ('The latest close is more than {days} days old.', '마지막 종가가 {days}일보다 오래됐어요.'),
    'chart_short': ('Too few daily closes in this range.', '이 기간의 일별 종가가 너무 적어요.'),
    'chart_name': ('{name} daily closes, {range}', '{name} 일별 종가, {range}'),
    'source': ('Source {source} · last close {date}', '출처 {source} · 마지막 종가 {date}'),
    'loading': ('Loading…', '불러오는 중…'),
    # The selected market's key figures and the chart card's legend (approved draft 2026-11-17).
    'fig_close': ('Close', '종가'),
    'fig_change': ('Day change', '전일 대비'),
    'fig_high': ('Range high', '기간 고가'),
    'fig_low': ('Range low', '기간 저가'),
    'legend_close': ('Daily close', '일별 종가'),
    'legend_base': ('First close of the range', '기간 첫 종가'),
}

# Home market cards: (English name, Korean name), keyed by the core.research.markets symbol.
MARKETS = {
    '^GSPC': ('S&P 500', 'S&P 500'),
    '^KS11': ('KOSPI Composite', '코스피 종합지수'),
    'DEXKOUS': ('US dollar / Korean won', '달러/원 환율'),
    'DGS10': ('US 10-year yield', '미국 10년 국채 금리'),
    'VIXCLS': ('Volatility index (VIX)', 'VIX 변동성 지수'),
    'BTC-USD': ('Bitcoin', '비트코인'),
}

# Card units, keyed by the core.research.markets unit: (English, Korean).
UNITS = {
    'pt': ('PTS', 'POINT'),
    'KRW/USD': ('KRW', 'KRW'),
    '%': ('%', '%'),
    'USD': ('USD', 'USD'),
}
