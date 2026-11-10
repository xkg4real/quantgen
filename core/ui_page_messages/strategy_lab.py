"""Strategy Lab page (ui/strategy_lab_page.py) and the shared analysis panel (ui/ai_panel.py).

Sentences with numbers in them are authored in both languages in
core/research/strategy_display.py; this catalogue covers the fixed captions.
"""
from core.research.strategy_exposure import EXPOSURE_HELP

EN_TO_KO: dict[str, str] = {
    # page header and notes
    "See which strategies and models passed validation and why, then test a strategy yourself against the same "
    "criteria.": "연구에서 검증한 전략과 모형이 통과했는지, 왜 그런 판정이 나왔는지 확인하고 같은 기준으로 직접 "
                 "전략을 검증해 볼 수 있습니다.",
    "v2 macro model cards (CARD-O / CARD-P) are under Macro → Model cards; this scorecard lists the "
    "asset-expansion study cards only.": "v2 매크로 모델 카드(CARD-O / CARD-P)는 매크로 → 모델 카드에 있습니다. "
                                         "이 목록은 자산 확장 연구의 검증 카드만 보여 줍니다.",
    "No cards yet: run python docs/asset_expansion_study.py":
        "아직 검증 카드가 없습니다. python docs/asset_expansion_study.py를 실행하세요.",
    # run form
    "Strategy family": "전략 종류",
    "Trend switch (Faber SMA / MOP sign)": "추세 전환 (Faber 이동평균 / MOP 부호)",
    "Volatility target (per-asset cap)": "변동성 목표 (자산별 상한)",
    "Cross-sectional momentum (long top third)": "상대 모멘텀 (상위 1/3 매수)",
    "Time-series momentum (MOP, long/short)": "시계열 모멘텀 (MOP, 매수·매도)",
    "Crypto short-horizon trend (per-asset 0/1)": "암호화폐 단기 추세 (보유 또는 현금)",
    "Risk parity across sleeves": "리스크 패리티 (자산별 위험 균등)",
    "Pairs (Engle–Granger spread, y then x)": "페어 거래 (Engle–Granger, y 다음 x)",
    "Symbols (comma-separated)": "종목 (쉼표로 구분)",
    "Cost per side (bp)": "편도 거래비용 (bp)",
    "table rate": "기준 비용",
    "Blank charges QUANTGEN's table rate. A lower cost runs as a sensitivity with no verdict.":
        "비워 두면 QUANTGEN 기준 비용을 적용합니다. 기준보다 낮은 비용은 판정 없이 민감도 실험으로만 실행됩니다.",
    "How many recent trading days to load for each symbol.": "종목마다 불러올 최근 거래일 수입니다.",
    "Run": "실행",
    "Pick a family and symbols, then press Run": "전략 종류와 종목을 고른 뒤 실행을 누르세요",
    "The same gate as the study: purged walk-forward (train 756 / test 126 sessions), a block-bootstrap Sharpe "
    "interval, deflated Sharpe, PBO, 2× costs, parameter plateau and a benchmark test.":
        "연구와 같은 검증 절차를 거칩니다: 워크포워드(학습 756일 / 검증 126일), 블록 부트스트랩 샤프 신뢰구간, "
        "보정 샤프, 과최적화 확률(PBO), 거래비용 2배, 설정 안정성, 벤치마크 비교.",
    # run result
    "Synthetic data in the panel: the verdict below is a toy.":
        "합성(가상) 데이터가 섞여 있습니다. 아래 판정은 연습용이며 실제 시장 결과가 아닙니다.",
    EXPOSURE_HELP: "변동성 목표와 암호화폐 추세 전략은 자산마다 따로 비중을 정합니다. 상한은 자산별 상한이지 "
                   "포트폴리오 전체 상한이 아니어서, 자산이 N개면 총 노출이 N배까지 될 수 있습니다. 자산별 규칙이며 "
                   "포트폴리오 변동성 목표나 1배 바스켓이 아닙니다. 여러 자산을 넣은 결과는 정규화하지 않은 자산별 "
                   "합계입니다.",
    # shared analysis panel (ui/ai_panel.py)
    "engine: local": "로컬 해설",
    "Ask the analyst something specific (optional)": "AI 분석가에게 물어볼 질문 (선택)",
    "e.g. how sensitive is this to the drift assumption?": "예: 기대수익률(드리프트) 가정에 결과가 얼마나 민감한가요?",
    "Deep analysis": "심층 분석",
    "Set ANTHROPIC_API_KEY to enable Claude deep analysis.": "ANTHROPIC_API_KEY를 설정하면 Claude 심층 분석을 쓸 수 있습니다.",
    "Deep analysis needs ANTHROPIC_API_KEY in .env; the local read above works without it.":
        "심층 분석에는 .env의 ANTHROPIC_API_KEY가 필요합니다. 위의 로컬 해설은 키 없이도 볼 수 있습니다.",
}
