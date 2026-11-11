"""Korean display text for the owner UI port, area: common (shared narrative chrome). See the package docstring."""

PAIRS = {
    "Full narrative paragraph": "해설 전체 문단 보기",
    "Choose a tool, then run.": "도구를 고른 뒤 실행하세요.",
    # Left rail (owner 2026-11-11, UI-D7 points 2-3): hide/show toggle and the Markets sub-menu.
    "Hide menu": "메뉴 숨기기",
    "Hide menu (Ctrl+B)": "메뉴 숨기기 (Ctrl+B)",
    "Show menu": "메뉴 펼치기",
    "Show menu (Ctrl+B)": "메뉴 펼치기 (Ctrl+B)",
    "Markets sections": "시장 하위 메뉴",
    # The Markets sub-items are the markets since owner ruling UI-D10 (2026-11-11): 국내 주식, 미국 주식, 코인. Their
    # text comes from core.market.screen.PAGES, set in the window language by app.retitle_market_sections, because
    # the English "Crypto" already reads 가상자산 for the analysis tool. The pairs below are the five ranking
    # category names the sub-menu showed until then (UI-D7); other screens still show them in English source.
    "Korean stocks": "국내 주식",
    "US stocks": "미국 주식",
    "Trading value": "거래대금",
    "Volume": "거래량",
    "Top gainers": "급상승",
    "Top losers": "급하락",
    "Market cap": "시가총액",
    "Stock search": "종목 검색",
}
