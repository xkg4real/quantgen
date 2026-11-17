"""Live quotes and chart page (ui/market_chart_page.py).

The page authors its own Korean and English captions; this catalogue holds the
Korean reading of the provider caveat sentences that `data.kis_workspace` and
`core.market.live` append to a snapshot note (one entry per sentence, exact text).
The coverage sentences of `availability_note` are shown by the page's own
Korean coverage line and are not repeated here.
"""

EN_TO_KO: dict[str, str] = {
    # data.kis_workspace.MarketDataService.load: tick/second bars
    "Received executions only: tick/second bars begin when the stream connects.":
        "수신한 체결만 사용합니다. 틱·초봉은 실시간 연결 시점부터 만들어집니다.",
    "Historical tick/second bars are unavailable; gaps are not filled.":
        "과거 틱·초봉은 제공되지 않으며, 빈 구간은 채우지 않습니다.",
    "The first/current bar can be partial; volume is received trade volume, not session volume.":
        "첫 봉과 현재 봉은 일부만 반영될 수 있습니다. 거래량은 세션 전체가 아니라 수신한 체결의 거래량입니다.",
    "Current quote unavailable; waiting for a valid streaming execution.":
        "현재가를 받지 못했습니다. 유효한 실시간 체결을 기다립니다.",
    # data.kis_workspace.MarketDataService.load: REST history
    "Clock-aligned aggregation of observed one-minute bars; first/latest bars can be partial.":
        "관측된 1분봉을 시각 기준으로 묶었습니다. 첫 봉과 마지막 봉은 일부만 반영될 수 있습니다.",
    "Adjusted historical prices; live raw-price candle updates must remain disabled.":
        "수정주가 기준 과거 가격입니다. 원주가 기준 실시간 봉 갱신은 꺼 두어야 합니다.",
    "Current quote unavailable; historical bars retained.":
        "현재가를 받지 못해 과거 봉만 표시합니다.",
    # data.kis_workspace.MarketDataService.quote
    "REST snapshot; quote timestamp convention unverified.":
        "REST 스냅샷입니다. 시세 시각의 기준은 검증되지 않았습니다.",
    "REST snapshot; market timestamp not provided.":
        "REST 스냅샷입니다. 거래소 시세 시각은 제공되지 않습니다.",
    # core.market.live: stream gaps
    "Live gap: some executions were not received; affected bars are partial.":
        "실시간 수신 공백: 일부 체결을 받지 못해 해당 봉은 불완전합니다.",
    "No missing trades are reconstructed.":
        "누락된 체결은 복원하지 않습니다.",
    "Live gap: missing trades may affect OHLC and minute-bar volume.":
        "실시간 수신 공백: 누락된 체결이 시가·고가·저가·종가와 분봉 거래량에 영향을 줄 수 있습니다.",
    "Reload history to reconcile.":
        "차트를 다시 조회해 맞추세요.",
}
