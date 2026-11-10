"""Korean display text for the owner UI port, area: strategy. See the package docstring.

Strategy Lab (Build & Test → 전략 실험실), owner issues 01, 04/12, 06, 07, 09, 10, 11, 14. Where the Flet
page already had reviewed Korean (core/ui_page_messages/strategy_lab.py) it is reused word for word, so
both apps say the same thing. Sentences built from numbers are authored in both languages in
core/research/strategy_display.py; `quantgen_desktop.strategy_view.ui` reads the fixed captions here.
"""
from core.research.strategy_exposure import EXPOSURE_HELP
from core.ui_page_messages.strategy_lab import EN_TO_KO as _FLET

MACRO_NOTE = ("v2 macro model cards (CARD-O / CARD-P) are under Macro → Model cards; this scorecard lists the "
              "asset-expansion study cards only.")
NO_CARDS = "No cards yet: run python docs/asset_expansion_study.py"

PAIRS = {
    # Run form (ToolPane captions, combo items, placeholder and tooltips): the Flet page's wording.
    **{key: _FLET[key] for key in (
        "Strategy family", "Trend switch (Faber SMA / MOP sign)", "Volatility target (per-asset cap)",
        "Cross-sectional momentum (long top third)", "Time-series momentum (MOP, long/short)",
        "Crypto short-horizon trend (per-asset 0/1)", "Risk parity across sleeves",
        "Pairs (Engle–Granger spread, y then x)", "Symbols (comma-separated)", "Cost per side (bp)", "table rate",
        "Blank charges QUANTGEN's table rate. A lower cost runs as a sensitivity with no verdict.",
        "How many recent trading days to load for each symbol.", MACRO_NOTE, NO_CARDS, EXPOSURE_HELP)},
    "Examples: US SPY, QQQ · Korean ETF 069500 · crypto BTC-USD, KRW-BTC · pairs take two symbols (y then x). "
    "A blank cost charges QUANTGEN's table rate.":
        "예: 미국 SPY, QQQ · 국내 ETF 069500 · 가상자산 BTC-USD, KRW-BTC · 페어 전략은 두 종목(y, x 순서). "
        "거래비용을 비워 두면 QUANTGEN 기준 비용을 씁니다.",
    "Volatility target and crypto trend: up to N× exposure with N assets":
        "변동성 목표·가상자산 추세: 자산이 N개면 총 노출 최대 N배",
    "Choose a tool and press Run. The app fetches prices from a suitable provider itself; the result names it.":
        "도구를 고른 뒤 실행하세요. 가격 자료는 앱이 알맞은 제공처에서 자동으로 가져오고, 결과에 어디서 가져왔는지 "
        "표시합니다.",

    # Study cards (tool "cards")
    "Validation summary": "검증 결과 요약",
    "How the strategies and models of the validation study were judged, at a glance.":
        "연구에서 검증한 전략과 모형이 어떤 판정을 받았는지 한눈에 봅니다.",
    "{count} study cards · the verdicts as the study recorded them":
        "검증 카드 {count}개 · 연구 보고서의 판정을 그대로 보여 줍니다",
    "Result per card": "카드별 결과",
    "What each card tested and why it got its verdict, in plain words. Click a row for the details below.":
        "카드마다 무엇을 검증했고, 왜 그 판정이 나왔는지 쉬운 말로 정리했습니다. 줄을 누르면 아래에서 자세히 볼 수 "
        "있습니다.",
    "Card details": "선택한 카드 자세히 보기",
    "Choose a validation card": "검증 카드 선택",
    "Card": "카드",
    "Kind": "종류",
    "Verdict": "판정",
    "Why": "이유",
    "Key numbers": "핵심 수치",
    "What was tested": "무엇을 검증했나",
    "Verdict and why": "결과와 이유",
    "Next step": "다음 단계",
    "Next step: {step}": "다음 단계: {step}",
    "Sources": "출처",
    "Recorded evidence ({count} lines)": "검증 기록 원문 보기 (영문 {count}줄)",
    "{count} study cards: {counts}": "검증 카드 {count}개: {counts}",
    "What each verdict means": "판정의 뜻",
    "Reading the scorecard": "읽는 법",
    "Every record states the number, the threshold and the sample behind it; pick a card to read its recorded "
    "evidence.": "모든 기록에는 수치, 기준, 표본이 함께 적혀 있습니다. 카드를 고르면 검증 기록 원문을 볼 수 있습니다.",

    # Run result (tool "run")
    "Result per criterion": "검증 항목별 결과",
    "Criterion": "검증 항목",
    "Result": "결과",
    "Threshold": "기준",
    "Meaning": "뜻",
    "Full gate lines": "검증 기록 원문 보기 (영문)",
    "Four headline numbers; all {count} criteria are under 'Result per criterion' below.":
        "핵심 지표 4개입니다. 검증 항목 {count}개 전체는 아래 '검증 항목별 결과'에 있습니다.",
    "Out-of-sample growth of 1: strategy and benchmark (equal-weight hold)":
        "처음 보는 구간(표본 외)의 누적 수익: 전략과 벤치마크(동일 비중 보유)",
    "Out-of-sample growth of 1": "처음 보는 구간(표본 외)의 누적 수익",
    "Out-of-sample sessions · growth of 1": "표본 외 거래일 순서 · 누적 자산(시작 = 1)",
    "Benchmark (equal-weight hold)": "벤치마크(동일 비중 보유)",
    "Data: {data} · walk-forward: {walk}": "데이터: {data} · 워크포워드: {walk}",
    "{family} ledger: {count} configurations": "{family} 계열 누적 설정 {count}개",
    "Provider notes (original text): {notes}": "제공처 메모(원문): {notes}",
}
