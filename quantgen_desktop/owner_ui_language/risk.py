"""Korean display text for the owner UI port, area: risk. See the package docstring.

Portfolio, Signals, Quant Lab's Monte Carlo panel, the risk table and the home summary (owner issues 13,
04/12, 14, 11). Wording follows Claude's Flet fix (core/ui_page_messages/build_pages.py) where Flet has
the same text; English display names that Flet already translates (Max Sharpe, Minimum volatility, ...)
are left to that reviewed catalogue.
"""

PAIRS = {
    # Portfolio: objective id in the frontier legend, same name as the Flet page and narrative terms.
    "risk_parity": "리스크 패리티(위험 균등)",
    # Yes/no cells (portfolio convergence, signals "Beat benchmark").
    "Yes": "예",
    "No": "아니오",
    # Per-asset cap / scope cells: the specific form first, it must win over '{cap} · selected'.
    "{requested} requested → {effective} effective · selected": "{requested} 요청 → {effective} 적용 · 선택",
    "{requested} requested → {effective} effective · comparison": "{requested} 요청 → {effective} 적용 · 비교용",
    "{cap} · selected": "{cap} · 선택",
    "{cap} · comparison": "{cap} · 비교용",
    "Calculation complete · no official investment verdict": "계산 완료 · 공식 투자 판정 없음",
    "Calculation complete · the solver did not report convergence; treat the weights as approximate · "
    "no official investment verdict":
        "계산 완료 · 최적화 계산이 수렴했다고 보고하지 않았으므로 비중은 근사치로만 보세요 · 공식 투자 판정 없음",
    "Enter symbols separated by commas, pick an objective and press [Run portfolio analysis]. All four "
    "objectives are computed and marked on the frontier, so their trade-offs are visible side by side.":
        "종목을 쉼표로 나눠 입력하고 목적함수를 고른 뒤 [포트폴리오 분석 실행]을 누르세요. 네 가지 목적함수를 "
        "모두 계산해 효율적 프런티어 위에 함께 표시하므로, 서로의 장단점을 직접 비교할 수 있습니다.",
    "Historical-sample optimization, not a future return guarantee or official gate verdict. All results are "
    "long-only and fully invested; equal weight fixes each weight at 1/N.":
        "과거 표본에 대한 최적화이며 미래 수익 보장이나 공식 게이트 판정이 아닙니다. 모든 결과는 롱온리·"
        "완전투자이며 동일 비중은 각 비중을 1/N로 고정합니다.",
    # Signals: backtest parameters as words.
    "Fast {fast} · slow {slow}": "단기 {fast} · 장기 {slow}",
    "Lookback {lookback} sessions": "관찰 기간 {lookback}거래일",
    "RSI period {period} · buy below {buy_below} · exit above {exit_above}":
        "RSI 기간 {period} · {buy_below} 아래에서 매수 · {exit_above} 위에서 청산",
    # Paper trading before a session is open.
    "No paper session is open yet. Press [Open paper session] to show venue states, simulated orders and "
    "the decision log here.":
        "아직 모의 세션을 읽지 않았습니다. [모의 세션 읽기]를 누르면 거래소 상태, 모의 주문, 판단 기록이 "
        "여기에 표시됩니다.",
    # Monte Carlo panel and the risk table.
    "Jump diffusion": "점프 확산",
    "Block bootstrap": "블록 부트스트랩",
    "Paths / horizon / seed": "경로 수 / 기간(거래일) / 시드",
    "No Monte Carlo run in this session yet. Run one under Build & Test → Monte Carlo; each completed run "
    "adds a row here.":
        "이번 세션에 실행한 몬테카를로 분석이 아직 없습니다. 설계/검증 → 몬테카를로에서 분석을 실행하면 "
        "완료된 실행마다 여기에 한 줄씩 추가됩니다.",
}
