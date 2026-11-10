"""Plain-language display catalogue for the Strategy Lab (owner UI review, 2026-11-10).

Presentation only: nothing here computes a statistic, changes a threshold or decides
a verdict. It turns what the validation gate already recorded (card fields, Score
fields, `validate.GATE`) into Korean and English sentences a non-specialist can read.

Every text helper returns a `(ko, en)` pair; `pick(pair, language)` chooses one.
A card or reason this catalogue does not know falls back to the recorded wording,
so a future card still shows, just less polished.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional

from core.quant import validate as V

Pair = tuple[str, str]


def pick(pair: Pair, language: str) -> str:
    return pair[0] if language == "ko" else pair[1]


def _num(x) -> Optional[float]:
    if isinstance(x, bool):
        return float(x)
    if isinstance(x, (int, float)) and math.isfinite(float(x)):
        return float(x)
    return None


def _f2(x) -> str:
    v = _num(x)
    return "—" if v is None else f"{v:.2f}"


def _pct(x, digits: int = 0) -> str:
    v = _num(x)
    return "—" if v is None else f"{v * 100:.{digits}f}%"


def _p(x) -> str:
    v = _num(x)
    if v is None:
        return "—"
    return "< 0.001" if v < 0.001 else f"{v:.3f}"


# --------------------------------------------------------------------------- #
# Vocabulary shared by the scorecard and the run result
# --------------------------------------------------------------------------- #
KIND: dict[str, Pair] = {
    "model": ("모형", "Model"),
    "strategy": ("전략", "Strategy"),
    "distribution": ("분포 예측", "Distribution forecast"),
}

VERDICT: dict[str, Pair] = {
    "PASS": ("통과", "Passed"),
    "REVISE": ("보완 필요", "Needs revision"),
    "REJECT": ("기각", "Rejected"),
    "INSUFFICIENT_DATA": ("자료 부족", "Insufficient data"),
    "UNKNOWN": ("판정 없음", "No verdict"),
}

VERDICT_TOKEN = {"PASS": "success", "REVISE": "accent", "REJECT": "error", "INSUFFICIENT_DATA": "muted",
                 "UNKNOWN": "muted", "WITHHELD": "muted"}

# What each verdict means for the person reading the scorecard (the study's offer policy).
VERDICT_MEANING: dict[str, Pair] = {
    "PASS": ("모든 검증 기준을 충족해 앱에서 기본으로 제공합니다.",
             "Met every validation criterion; offered by default."),
    "REVISE": ("일부 기준을 넘지 못했습니다. 고칠 점과 함께 제공합니다.",
               "Missed some criteria; offered with what must be fixed."),
    "REJECT": ("근거가 부족해 제공하지 않습니다. 이유를 볼 수 있게 남겨 둡니다.",
               "Not enough evidence to use it; listed so the refusal is visible."),
    "INSUFFICIENT_DATA": ("자료가 부족해 아직 판단할 수 없습니다. 이유를 볼 수 있게 남겨 둡니다.",
                          "Too little data to decide yet; listed so the refusal is visible."),
    "UNKNOWN": ("이 화면의 자산 확장 검증 카드 형식이 아닙니다 (v2 매크로 카드는 매크로 → 모델 카드).",
                "Not an asset-expansion study card (v2 macro cards: Macro → Model cards)."),
}

STATUS: dict[str, Pair] = {"pass": ("통과", "Pass"), "fail": ("미달", "Fail"), "info": ("참고", "Info"),
                           "na": ("해당 없음", "n/a")}
STATUS_TOKEN = {"pass": "success", "fail": "error", "info": "text", "na": "muted"}


def verdict_label(decision: str) -> Pair:
    """'기각 · REJECT' / 'REJECT': the code always stays visible (repository policy)."""
    code = decision if decision in VERDICT else "UNKNOWN"
    shown = decision or "UNKNOWN"
    return (f"{VERDICT[code][0]} · {shown}", shown)


SOURCE: dict[str, Pair] = {
    "YFINANCE": ("Yahoo", "Yahoo"), "FMP": ("FMP", "FMP"), "KIS": ("한국투자증권(KIS)", "KIS"),
    "UPBIT": ("업비트", "Upbit"), "BINANCE": ("바이낸스", "Binance"), "CRYPTO": ("암호화폐 거래소", "crypto exchange"),
    "SYNTHETIC": ("합성 데이터", "synthetic"),
}


def source_label(source: str) -> Pair:
    return SOURCE.get(str(source).upper(), (str(source), str(source)))


# --------------------------------------------------------------------------- #
# The 34 asset-expansion study cards: name and one-line plain explanation
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CardText:
    name: Pair
    what: Pair


_ASSET = {"btc": ("비트코인(BTC-USD)", "Bitcoin (BTC-USD)"), "kodex200": ("KODEX 200", "KODEX 200"),
          "spy": ("S&P 500 ETF(SPY)", "S&P 500 ETF (SPY)")}
_MODEL = {"garch": ("GARCH-t", "GARCH-t"), "gjr": ("GJR-GARCH-t", "GJR-GARCH-t"),
          "skewt": ("GJR-GARCH 비대칭 t", "GJR-GARCH skew-t")}


def _dist(asset: str, model: str) -> CardText:
    a, m = _ASSET[asset], _MODEL[model]
    return CardText(
        (f"{a[0]} 하루 손실 범위 예측 ({m[0]})", f"{a[1]} one-day risk range ({m[1]})"),
        (f"{m[0]} 모형이 예측한 {a[0]}의 하루 손실 범위(VaR)가 실제로 그 빈도만큼 맞았는지, "
         f"단순 EWMA 변동성보다 나은지 검정했습니다.",
         f"Checks whether the {m[1]} one-day loss range (VaR) for {a[1]} was breached as often as it said, "
         f"and whether it beats a simple EWMA volatility."))


def _trend(where: Pair) -> CardText:
    return CardText((f"{where[0]} 추세 전환", f"{where[1]} trend switch"),
                    (f"이동평균·모멘텀 신호에 따라 {where[0]}를 보유하거나 현금으로 바꾸는 전략이 "
                     "동일 비중 단순 보유보다 나은지 검정했습니다.",
                     f"Tests whether switching {where[1]} between holding and cash on moving-average or momentum "
                     "signals beats equal-weight buy-and-hold."))


def _voltarget(where: Pair) -> CardText:
    return CardText((f"{where[0]} 변동성 목표 투자", f"{where[1]} volatility targeting"),
                    (f"변동성이 높을 때 {where[0]} 비중을 줄이는 전략이 단순 보유보다 샤프 지수를 높이고 "
                     "낙폭을 줄이는지 검정했습니다.",
                     f"Tests whether cutting {where[1]} exposure when volatility is high raises the Sharpe ratio "
                     "and cuts drawdown versus buy-and-hold."))


def _pair(where: Pair) -> CardText:
    return CardText((f"{where[0]} 페어 거래", f"{where[1]} pair trade"),
                    (f"{where[0]}의 가격 차이가 벌어졌다 다시 좁혀지는 움직임을 2σ 규칙으로 거래해 "
                     "비용을 내고도 수익이 나는지 검정했습니다.",
                     f"Tests whether trading the {where[1]} spread at 2σ, as it widens and narrows again, "
                     "makes money after costs."))


def _crypto_trend(where: Pair) -> CardText:
    return CardText((f"비트코인 단기 추세 추종 ({where[0]})", f"Bitcoin short-term trend ({where[1]})"),
                    ("단기 추세 신호가 맞을 때만 비트코인을 보유하고 아니면 현금으로 빠지는 전략이 단순 보유보다 "
                     "샤프 지수가 높고 낙폭이 작은지 검정했습니다.",
                     "Tests whether holding bitcoin only while short-term trend signals agree (otherwise cash) "
                     "beats buy-and-hold on Sharpe with a smaller drawdown."))


CARDS: dict[str, CardText] = {
    "D_C2_garch_btc": _dist("btc", "garch"),
    "D_C2_gjr_btc": _dist("btc", "gjr"),
    "D_C2_skewt_btc": _dist("btc", "skewt"),
    "D_Q_garch_kodex200": _dist("kodex200", "garch"),
    "D_Q_garch_spy": _dist("spy", "garch"),
    "D_Q_gjr_kodex200": _dist("kodex200", "gjr"),
    "D_Q_gjr_spy": _dist("spy", "gjr"),
    "D_Q_skewt_kodex200": _dist("kodex200", "skewt"),
    "D_Q_skewt_spy": _dist("spy", "skewt"),
    "M_B1_dns": CardText(
        ("미국 국채 금리 12개월 예측 (Diebold–Li)", "US Treasury 12-month yield forecast (Diebold–Li)"),
        ("Diebold–Li 3요인 모형의 12개월 뒤 국채 금리 예측이 '지금 금리 그대로'(랜덤워크)보다 정확한지 "
         "5개 만기에서 검정했습니다.",
         "Tests whether Diebold–Li factor forecasts of Treasury yields 12 months ahead beat assuming today's "
         "yields stay put (random walk) at five maturities.")),
    "M_C1_kimchi": CardText(
        ("김치 프리미엄 신호", "Kimchi premium signal"),
        ("국내 거래소 비트코인 웃돈(김치 프리미엄)이 빨리 평균으로 돌아오는지, 웃돈이 클 때 다음 주 비트코인 "
         "수익률이 약해지는지 검정했습니다.",
         "Tests whether the Korean bitcoin premium reverts quickly and whether a high premium predicts weaker "
         "bitcoin returns over the next week.")),
    "M_C4_funding": CardText(
        ("BTC 무기한선물 펀딩비 신호", "BTC perpetual funding signal"),
        ("무기한선물 펀딩비가 높을 때(매수 쏠림) 이후 30일 비트코인 수익률이 낮아지는지 검정했습니다.",
         "Tests whether high perpetual-futures funding (crowded longs) is followed by weaker 30-day bitcoin "
         "returns.")),
    "M_C7_weekday": CardText(
        ("암호화폐 요일 효과와 주말 유동성", "Crypto weekday effect and weekend liquidity"),
        ("요일별 수익률에 지속적인 차이가 없는지(예상된 결론), 주말 거래량이 적어 거래비용을 더 잡아야 "
         "하는지 확인했습니다.",
         "Checks that weekday returns carry no persistent effect (the expected result) and that thinner "
         "weekend volume calls for a higher cost input.")),
    "M_C8_ethbtc": CardText(
        ("ETH/BTC 비율 평균회귀", "ETH/BTC ratio mean reversion"),
        ("이더리움/비트코인 가격 비율이 일정한 수준으로 되돌아오는지(평균회귀) 검정했습니다. "
         "되돌아오지 않는 것이 예상된 결론입니다.",
         "Tests whether the ETH/BTC price ratio reverts to a stable level; no reversion is the expected "
         "result.")),
    "M_E4_letf_drag": CardText(
        ("레버리지 ETF 괴리(드래그) 예측", "Leveraged ETF drag forecast"),
        ("KODEX 레버리지가 KOSPI200 2배 수익률보다 분기마다 얼마나 뒤처지는지 GARCH 변동성으로 미리 "
         "예측할 수 있는지 검정했습니다.",
         "Tests whether a GARCH-based variance forecast predicts how far KODEX Leverage falls short of "
         "2× KOSPI200 each quarter.")),
    "M_O1_board_today": CardText(
        ("KOSPI200 옵션 호가판 대조", "KOSPI200 option board reconciliation"),
        ("앱의 내재변동성 계산(Black-76, SVI, MFIV)이 실제 KOSPI200 옵션 호가판과 맞는지 그날 "
         "스냅숏으로 대조했습니다.",
         "Reconciles the app's implied-volatility calculations (Black-76, SVI, MFIV) with that day's live "
         "KOSPI200 option board.")),
    "M_O2_basis_today": CardText(
        ("KOSPI200 선물 베이시스 대조", "KOSPI200 futures basis reconciliation"),
        ("앱이 계산한 선물 이론가(보유비용 모형)가 배당을 맞춘 뒤 한국투자증권(KIS) 이론가와 같은지 "
         "대조했습니다.",
         "Checks that the app's cost-of-carry fair value matches KIS's theoretical price once dividend points "
         "are aligned.")),
    "S_B2_pca_fly": CardText(
        ("미국 국채 2-5-10년 버터플라이", "US Treasury 2-5-10 butterfly"),
        ("금리 수준·기울기 위험을 뺀(PCA 중립) 2-5-10년 버터플라이가 평균으로 되돌아오고, 2σ 매매 규칙이 "
         "거래비용의 두 배 넘게 버는지 검정했습니다.",
         "Tests whether the PCA-neutral 2-5-10 butterfly mean-reverts and its 2σ rule earns more than twice "
         "its trading cost.")),
    "S_B3_tsmom_futures": CardText(
        ("선물 10종 시계열 모멘텀", "Time-series momentum on ten futures"),
        ("각 선물의 지난 12개월 방향을 따라 사거나 파는 모멘텀 전략이 2009년 이후 비용을 빼고도 수익을 "
         "내는지 검정했습니다 (Yahoo 연속 선물의 롤 방식은 공개되지 않음).",
         "Tests whether following each future's 12-month direction (long or short) earns a positive net "
         "Sharpe after 2009 (Yahoo's roll treatment is undocumented).")),
    "S_C3_crypto_trend_btcusd": _crypto_trend(("달러 BTC-USD", "BTC-USD")),
    "S_C3_crypto_trend_krwbtc": _crypto_trend(("원화 KRW-BTC", "KRW-BTC")),
    "S_E1_trend_krx": _trend(("국내 ETF", "Korean ETF")),
    "S_E1_trend_us": _trend(("미국 ETF", "US ETF")),
    "S_E2_voltarget_kodex200": _voltarget(("KODEX 200", "KODEX 200")),
    "S_E2_voltarget_spy": _voltarget(("S&P 500(SPY)", "S&P 500 (SPY)")),
    "S_E3_riskparity_us": CardText(
        ("미국 자산 리스크 패리티", "US risk parity"),
        ("자산마다 위험 기여도를 같게 맞추는 배분이 동일 비중 배분보다 샤프 지수가 높은지 검정했습니다 "
         "(레버리지 없음).",
         "Tests whether equal-risk-contribution allocation beats equal weight on Sharpe (unlevered).")),
    "S_E5_xsmom_sectors": CardText(
        ("미국 섹터 ETF 상대 모멘텀", "US sector ETF momentum"),
        ("9개 섹터 ETF 가운데 최근 12개월 성과 상위 1/3만 보유하는 전략이 섹터 동일 비중 보유보다 "
         "나은지 검정했습니다.",
         "Tests whether holding the top third of the nine sector ETFs by 12-month momentum beats the "
         "equal-weight sector basket.")),
    "S_E8_pairs_gld_iau": _pair(("금 ETF(GLD·IAU)", "Gold ETF (GLD/IAU)")),
    "S_E8_pairs_kodex_tiger": _pair(("KOSPI200 ETF(KODEX·TIGER)", "KOSPI200 ETF (KODEX/TIGER)")),
    "S_S6_pairs_hyundai_kia": _pair(("현대차·기아", "Hyundai/Kia")),
    "S_S6_pairs_samsung_pref": _pair(("삼성전자 우선주·보통주", "Samsung Electronics preferred/common")),
    "S_V1_vix_rolldown": CardText(
        ("VIX 롤다운 (변동성 매도)", "VIX roll-down (short volatility)"),
        ("VIX 선물이 콘탱고일 때 VIX ETP를 매도하고 SPY로 헤지하는 전략이 헤지 없는 매도보다 작은 낙폭으로 "
         "롤다운 수익을 얻는지 검정했습니다.",
         "Tests whether shorting the VIX ETP in contango, hedged with SPY, earns the roll-down with a smaller "
         "drawdown than the unhedged short.")),
    "S_V3_fx_momentum": CardText(
        ("통화 상대 모멘텀 (G10·원화)", "Currency momentum (G10 and KRW)"),
        ("최근 1~3개월 강했던 통화를 사고 약했던 통화를 파는 전략이 2010년 이후 비용을 빼고도 의미 있는 "
         "수익을 내는지 검정했습니다.",
         "Tests whether buying the strongest and selling the weakest currencies over the last one to three "
         "months earns a meaningful net return after 2010.")),
    "S_V4_dollar_carry": CardText(
        ("달러 캐리", "Dollar carry"),
        ("해외 금리가 평균적으로 더 높을 때 해외 통화 바스켓을 보유하는 전략이 처음 보는 구간(표본 외)에서도 "
         "수익을 내는지 검정했습니다.",
         "Tests whether holding the foreign-currency basket when foreign rates are higher on average earns a "
         "positive out-of-sample Sharpe.")),
}


def card_text(card: Mapping) -> CardText:
    """Name and plain explanation; an unknown card shows its id and its recorded hypothesis."""
    cid = str(card.get("card_id") or "")
    if cid in CARDS:
        return CARDS[cid]
    hypothesis = str(card.get("hypothesis") or card.get("claim") or "")
    return CardText((cid, cid), (hypothesis, hypothesis))


def kind_label(kind: str) -> Pair:
    return KIND.get(str(kind), (str(kind), str(kind)))


# --------------------------------------------------------------------------- #
# Decision reasons and revise targets, in plain words
# --------------------------------------------------------------------------- #
CHECK_NAMES: dict[str, Pair] = {
    # strategy gate (validate._decide_strategy)
    "over-search": ("과최적화 점검(표본 외/표본 내 성과 비율)", "over-search (out-of-sample vs in-sample)"),
    "execution": ("거래비용 2배 점검", "2× cost check"),
    "regime": ("연도별 일관성", "consistency across years"),
    "plateau": ("설정 안정성", "parameter stability"),
    "sample": ("거래 횟수", "number of trades"),
    "interval": ("수익 신뢰구간", "Sharpe interval"),
    # distribution gate (validate.score_distribution)
    "tails": ("손실 한도 초과 빈도(95% VaR)", "tail frequency (95 % VaR)"),
    "clustering": ("손실 몰림(군집)", "loss clustering"),
    "coverage": ("90% 범위 적중률", "90 % band coverage"),
    "pit": ("분포 모양(PIT)", "distribution shape (PIT)"),
    "light": ("바젤 신호등", "Basel traffic light"),
}
# Strategy check each failed gate name corresponds to (see strategy_checks below).
_TARGET_CHECK = {"over-search": "oos_is", "execution": "stress", "regime": "years", "plateau": "plateau",
                 "sample": "trades", "interval": "interval"}

_EXACT_REASONS: dict[str, tuple[Pair, Optional[str]]] = {
    "every gate criterion met": (("모든 검증 기준을 충족했습니다.", "Met every validation criterion."), None),
    "deflated Sharpe below 0.95": (
        ("시험한 설정 수를 감안하면 성과가 운일 수 있습니다 (보정 샤프 0.95 미달).",
         "Allowing for how many setups were tried, the result could be luck (deflated Sharpe below 0.95)."),
        "dsr"),
    "PBO above 0.20 and the in-sample winner loses out of sample": (
        ("과최적화 가능성이 큽니다: 과거 최적 설정이 처음 보는 구간에서 졌습니다 (PBO 0.20 초과).",
         "Likely overfitted: the in-sample winner lost out of sample (PBO above 0.20)."), "pbo"),
    "loses money at 2× costs and the Sharpe interval includes zero": (
        ("거래비용이 두 배면 손실이 나고, 수익이 0보다 크다고 확신할 수 없습니다.",
         "Loses money at 2× costs, and the return could be zero."), "stress"),
    "every calibration test met": (("모든 보정(캘리브레이션) 검정을 통과했습니다.", "Met every calibration test."), None),
    "exceedance at twice the target": (
        ("예측한 손실 한도를 넘은 날이 목표의 두 배 이상입니다.", "Losses beyond the forecast limit happened at twice "
                                                    "the target rate."), None),
    "red traffic light": (("최근 1년 99% 손실 한도 초과가 너무 많습니다 (바젤 신호등 빨강).",
                           "Too many 99 % breaches over the last year (red Basel traffic light)."), None),
    "PIT fails at the 1 % level": (
        ("예측 분포의 모양이 실제 수익률과 맞지 않습니다 (PIT 검정 1% 수준에서 실패).",
         "The forecast distribution does not match realised returns (PIT fails at the 1 % level)."), None),
    "non-convergence above 5 % of origins": (
        ("모형 추정이 5%가 넘는 시점에서 수렴하지 않았습니다.", "The model failed to converge at more than 5 % of "
                                                  "origins."), None),
    "BIS sign confirmed": (
        ("펀딩비가 높으면 이후 수익률이 낮다는 BIS 연구의 방향이 확인됐습니다.",
         "Confirmed the BIS finding: high funding is followed by weaker returns."), None),
    "cost input set": (
        ("요일 효과는 없었고(예상대로), 주말 거래량이 적어 주말 거래비용을 2배로 반영했습니다.",
         "No weekday effect (as expected); thinner weekend volume is now a 2× weekend cost input."), None),
    "within the dividend band": (
        ("앱 이론가와 KIS 이론가의 차이가 배당 차이로 설명되는 범위 안에 있습니다.",
         "The app's fair value and KIS's agree within the dividend band."), None),
    "descriptive tile only: the predictive test did not pass": (
        ("참고 지표로만 씁니다: 수익률 예측력 검정을 통과하지 못했습니다.",
         "Kept as a descriptive tile only: the predictive test did not pass."), None),
    "no rejection of a unit root (the expected null)": (
        ("평균으로 되돌아온다는 근거가 없습니다 (예상했던 결론).",
         "No evidence of mean reversion (the expected result)."), None),
}

_PATTERNS: list[tuple[re.Pattern, Any]] = []


def _pattern(regex: str):
    def register(fn):
        _PATTERNS.append((re.compile(regex), fn))
        return fn
    return register


@_pattern(r"does not beat its benchmark \(Sharpe difference ([+-]?[\d.]+|nan), p ([\d.]+|nan)\)")
def _bench(m):
    d, p = m.group(1), m.group(2)
    lim = V.GATE["bench_p_max"]
    return (f"단순 보유(벤치마크)보다 낫다는 근거가 없습니다 (샤프 지수 차이 {d}, p {p}; 기준 p ≤ {lim}).",
            f"No evidence it beats simply holding the benchmark (Sharpe difference {d}, p {p}; needs p ≤ {lim})."
            ), "bench"


@_pattern(r"([\w-]+) check failed \((.*)\)")
def _check_failed(m):
    target, failed = m.group(1), m.group(2)
    names = [x.strip() for x in failed.split(";")] if failed != "interval includes zero" else ["interval"]
    ko = ", ".join(CHECK_NAMES.get(n, (n, n))[0] for n in names)
    en = ", ".join(CHECK_NAMES.get(n, (n, n))[1] for n in names)
    return (f"통과하지 못한 점검: {ko}.", f"Failed checks: {en}."), _TARGET_CHECK.get(target)


@_pattern(r"(\d+) trades over (\d+) full OOS years \(([\d,]+) sessions\); the gate needs ≥ (\d+) trades and "
          r"≥ (\d+) full years of ≥ ([\d,]+) sessions")
def _insufficient(m):
    n, y, s, nt, ny, ns = m.groups()
    return (f"판단하기에 자료가 부족합니다: 표본 외 거래 {n}회, {y}년({s}거래일). 최소 {nt}회, {ny}년({ns}거래일)이 "
            f"필요합니다.",
            f"Not enough data to judge: {n} trades over {y} out-of-sample years ({s} sessions); needs ≥ {nt} "
            f"trades and ≥ {ny} full years ({ns} sessions)."), "trades"


@_pattern(r"the Sharpe interval includes zero but DSR and PBO pass; a Sharpe of ([+-]?[\d.]+) needs about "
          r"([\d,]+) sessions to certify and ([\d,]+) were available")
def _short_record(m):
    sr, need, have = m.groups()
    return (f"보정 샤프와 과최적화 점검은 통과했지만, 샤프 {sr}를 확신하려면 약 {need}거래일이 필요한데 "
            f"{have}거래일뿐입니다.",
            f"Deflated Sharpe and PBO pass, but a Sharpe of {sr} needs about {need} sessions to certify and only "
            f"{have} were available."), "interval"


@_pattern(r"((?:tails|clustering|coverage|pit|light)(?:, (?:tails|clustering|coverage|pit|light))*) failed")
def _dist_failed(m):
    names = [x.strip() for x in m.group(1).split(",")]
    return (f"통과하지 못한 검정: {', '.join(CHECK_NAMES[n][0] for n in names)}.",
            f"Failed tests: {', '.join(CHECK_NAMES[n][1] for n in names)}."), None


@_pattern(r"(\d+) origins; the 95 % tests need ≥ (\d+)")
def _few_origins(m):
    n, need = m.groups()
    return (f"예측 시점이 {n}개뿐입니다 (95% 검정에는 {need}개 이상 필요).",
            f"Only {n} forecast origins; the 95 % tests need ≥ {need}."), None


@_pattern(r"(\d+)/(\d+) maturities beaten, (\d+)/(\d+) significant")
def _maturities(m):
    b, n, s, n2 = m.groups()
    return (f"'금리 그대로' 예측보다 나은 만기가 {n}개 중 {b}개, 의미 있게 나은 만기가 {s}개였습니다.",
            f"Beat the no-change forecast at {b} of {n} maturities, significantly at {s} of {n2}."), None


@_pattern(r"market closed at capture: last prints of (\S+) only; run during a session \((.*)\)")
def _closed(m):
    day, hours = m.groups()
    return (f"장 마감 후 수집된 자료({day} 마지막 체결가)라 제대로 대조할 수 없었습니다. 장중({hours})에 다시 "
            f"실행해야 합니다.",
            f"Captured with the market closed (last prints of {day}); run again during the session ({hours})."
            ), None


def _see_lines(card: Mapping) -> Optional[Pair]:
    """'see lines' cards: the plain reason from the card's own numbers."""
    st = card.get("stats") or {}
    cid = card.get("card_id")
    if cid == "M_E4_letf_drag" and _num(st.get("mae_garch_bp")) is not None:
        return ("GARCH 기반 괴리 예측이 단순한 예측보다 충분히 정확하지 않았고, 실제 괴리와의 관계도 약했습니다.",
                "The GARCH-based drag forecast was not clearly more accurate than simple forecasts and tracked "
                "the realised drag weakly.")
    if cid == "S_B2_pca_fly" and _num(st.get("mean_pnl_per_trade_bp")) is not None:
        return ("버터플라이는 평균으로 되돌아오지만, 2σ 매매 규칙이 거래비용 이상을 벌지 못했습니다.",
                "The butterfly does mean-revert, but the 2σ trading rule did not earn more than its costs.")
    return None


def reason_text(reason: str, card: Optional[Mapping] = None) -> tuple[Pair, Optional[str]]:
    """Plain (ko, en) wording of a recorded decision reason, and the strategy check it points at (or None).
    Unknown wording comes back unchanged in both languages."""
    reason = str(reason or "").strip()
    if reason in _EXACT_REASONS:
        return _EXACT_REASONS[reason]
    for rx, fn in _PATTERNS:
        m = rx.fullmatch(reason)
        if m:
            return fn(m)
    if reason == "see lines" and card is not None:
        plain = _see_lines(card)
        if plain:
            return plain, None
    if reason == "see lines":
        return ("세부 근거를 확인하세요.", "See the evidence lines."), None
    return (reason, reason), None


REVISE_TARGET: dict[str, Pair] = {
    "coarsen the grid or fix a parameter at the plateau centre; lengthen the IS window":
        ("설정 후보를 줄이거나 안정 구간 가운데 값으로 고정하고, 학습 구간을 늘리세요.",
         "Coarsen the grid or fix a parameter at the plateau centre; lengthen the in-sample window."),
    "lengthen the holding period or add a hysteresis band; never lower the cost assumption":
        ("보유 기간을 늘리거나 매매 완충 구간을 두세요. 비용 가정은 낮추지 않습니다.",
         "Lengthen the holding period or add a hysteresis band; never lower the cost assumption."),
    "only a pre-registered regime condition may be tightened; otherwise this is a new hypothesis":
        ("사전에 등록한 국면 조건만 조일 수 있습니다. 그 밖의 변경은 새 가설로 다시 검증해야 합니다.",
         "Only a pre-registered regime condition may be tightened; anything else is a new hypothesis."),
    "widen the grid (edge) or move to the plateau centre and re-run":
        ("설정 범위를 넓히거나 안정 구간 가운데로 옮겨 다시 실행하세요.",
         "Widen the grid (edge) or move to the plateau centre and re-run."),
    "extend history or lengthen the sample": ("더 긴 기간의 자료로 다시 검증하세요.",
                                              "Extend the history or lengthen the sample."),
    "the Sharpe interval includes zero: extend history": ("수익 신뢰구간이 0을 포함합니다: 더 긴 자료가 필요합니다.",
                                                          "The Sharpe interval includes zero: extend the history."),
    "the sleeve set or the cost model, not the rule: the benchmark is as good":
        ("규칙이 아니라 자산 구성이나 비용 모형을 바꿔야 합니다: 단순 보유도 이만큼 좋습니다.",
         "Change the sleeve set or the cost model, not the rule: the benchmark is as good."),
    "extend history": ("더 긴 기간의 자료가 필요합니다.", "Extend the history."),
    "extend history (pykrx / Yahoo .KS), do not touch the rules":
        ("규칙은 그대로 두고 더 긴 자료(pykrx / Yahoo .KS)로 다시 검증하세요.",
         "Extend the history (pykrx / Yahoo .KS); do not touch the rules."),
    "tails too thin: t innovations, a lower ν floor, or the GJR leverage term":
        ("꼬리 위험을 과소평가합니다: t 분포 충격, 더 낮은 ν 하한, GJR 비대칭 항을 검토하세요.",
         "Tails too thin: t innovations, a lower ν floor, or the GJR leverage term."),
    "fan too wide: shorter window, or the bounded-innovation variance gap":
        ("예측 범위가 너무 넓습니다: 추정 창을 줄이거나 분산 차이를 점검하세요.",
         "Fan too wide: a shorter window, or the bounded-innovation variance gap."),
    "volatility dynamics missing: GBM → GARCH → GJR, or a longer half-life":
        ("변동성 변화가 반영되지 않았습니다: GBM → GARCH → GJR 또는 더 긴 반감기를 검토하세요.",
         "Volatility dynamics missing: GBM → GARCH → GJR, or a longer half-life."),
    "band width: the horizon aggregation or the ½σ²_t correction":
        ("범위 폭 문제: 기간 합산 방식이나 ½σ²_t 보정을 점검하세요.",
         "Band width: the horizon aggregation or the ½σ²_t correction."),
    "centring: drift mode or dividend / FX-rate conventions":
        ("중심 위치 문제: 드리프트 방식이나 배당·환율 관례를 점검하세요.",
         "Centring: drift mode or dividend / FX-rate conventions."),
    "shape: see the histogram diagnosis": ("분포 모양 문제: 히스토그램 진단을 확인하세요.",
                                           "Shape: see the histogram diagnosis."),
    "recent 99 % exceptions: re-examine the last year's fits": (
        "최근 99% 한도 초과: 지난 1년의 추정을 다시 확인하세요.", "Recent 99 % exceptions: re-examine the last year's fits."),
    "no claim at h = 1; use h = 12 only": ("1개월 예측은 주장하지 않고 12개월 예측만 씁니다.",
                                           "No claim at one month; use the 12-month horizon only."),
    "keep as a monitor; never feed the composite": ("관찰 지표로만 두고 종합 점수에는 넣지 않습니다.",
                                                    "Keep as a monitor; never feed the composite."),
    "closed: the ratio has trended for years": ("종결: 비율이 수년째 한 방향으로 움직였습니다.",
                                                "Closed: the ratio has trended for years."),
    "re-run during the session": ("장중에 다시 실행하세요.", "Re-run during the session."),
}


def revise_target_text(target) -> Optional[Pair]:
    if not target:
        return None
    t = str(target).strip()
    return REVISE_TARGET.get(t, (t, t))


# --------------------------------------------------------------------------- #
# Labelled key numbers (no raw field names)
# --------------------------------------------------------------------------- #
# key -> (ko label, en label, format)
_LABELLED: dict[str, tuple[str, str, str]] = {
    "bootstrap_p": ("부트스트랩 p", "bootstrap p", "p"),
    "top_decile_fwd30": ("펀딩 상위 10% 후 30일 수익", "30-day return after top-decile funding", "pct1"),
    "bottom_decile_fwd30": ("하위 10% 후", "after bottom decile", "pct1"),
    "return_p_bonferroni": ("요일 효과 p(본페로니)", "weekday-effect p (Bonferroni)", "p"),
    "weekend_volume_ratio": ("주말 거래량 비율", "weekend volume ratio", "pct0"),
    "theo_gap_pts": ("KIS 이론가와 차이", "gap to KIS theoretical", "pts"),
    "mispricing_bp": ("배당 미반영 괴리", "mispricing before dividends", "bp"),
    "adf_p": ("단위근 검정(ADF) p", "unit-root test (ADF) p", "p"),
    "half_life_days": ("반감기", "half-life", "days"),
    "pred_t": ("예측력 t값", "predictive t-stat", "t"),
    "mae_garch_bp": ("예측 오차(MAE)", "forecast error (MAE)", "bp"),
    "mae_zero_bp": ("0 예측 오차", "zero-forecast error", "bp"),
    "mae_last_bp": ("직전 분기값 예측 오차", "last-quarter forecast error", "bp"),
    "r2": ("설명력 R²", "R²", "f2"),
    "iv_median_gap": ("내재변동성 차이 중앙값", "median implied-vol gap", "volpts"),
    "iv_p90_gap": ("90분위 차이", "90th-percentile gap", "volpts"),
    "beats_rw_12m": ("랜덤워크보다 나은 만기", "maturities beating the random walk", "of5"),
    "n_trades": ("거래", "trades", "count"),
    "hit_rate": ("적중률", "hit rate", "pct0"),
    "mean_pnl_per_trade_bp": ("거래당 손익", "P&L per trade", "bp"),
}

CARD_NUMBERS: dict[str, tuple[str, ...]] = {
    "M_B1_dns": ("beats_rw_12m",),
    "M_C1_kimchi": ("adf_p", "half_life_days", "pred_t"),
    "M_C4_funding": ("bootstrap_p", "top_decile_fwd30", "bottom_decile_fwd30"),
    "M_C7_weekday": ("return_p_bonferroni", "weekend_volume_ratio"),
    "M_C8_ethbtc": ("adf_p", "half_life_days"),
    "M_E4_letf_drag": ("mae_garch_bp", "mae_last_bp", "r2"),
    "M_O1_board_today": ("iv_median_gap", "iv_p90_gap"),
    "M_O2_basis_today": ("theo_gap_pts",),
    "S_B2_pca_fly": ("adf_p", "n_trades", "hit_rate", "mean_pnl_per_trade_bp"),
}


def _fmt(value, kind: str, language: str) -> str:
    v = _num(value)
    if v is None:
        return "—"
    if kind == "p":
        return _p(v)
    if kind == "pct0":
        return f"{v * 100:.0f}%"
    if kind == "pct1":
        return f"{v * 100:+.1f}%"
    if kind == "bp":
        return f"{v:+.1f}bp" if v < 0 else f"{v:.0f}bp"
    if kind == "pts":
        return f"{v:.2f}pt"
    if kind == "volpts":
        return f"{v:.2f}%p" if language == "ko" else f"{v:.2f} vol pts"
    if kind == "days":
        return f"{v:.0f}일" if language == "ko" else f"{v:.0f} days"
    if kind == "of5":
        return f"{v:.0f}/5"
    if kind == "count":
        return f"{v:,.0f}" + ("회" if language == "ko" else "")
    if kind == "t":
        return f"{v:+.2f}"
    return f"{v:.2f}"


def key_numbers(card: Mapping, language: str) -> str:
    """'샤프 지수 1.19 · 보정 샤프 1.00 · 과최적화 확률(PBO) 0.19' — labelled, never a raw field name."""
    stats = card.get("stats") or {}
    tests = card.get("tests") or {}
    ko = language == "ko"
    if _num(stats.get("sr_oos")) is not None:
        parts = [("샤프 지수" if ko else "Sharpe") + f" {_f2(stats.get('sr_oos'))}",
                 ("보정 샤프" if ko else "deflated Sharpe") + f" {_f2(stats.get('dsr'))}",
                 ("과최적화 확률(PBO)" if ko else "overfitting probability (PBO)") + f" {_f2(stats.get('pbo'))}"]
        return " · ".join(parts)
    if _num(stats.get("exceed95")) is not None:
        parts = [(f"95% 한도 초과 {_pct(stats.get('exceed95'), 1)} (목표 5%)" if ko else
                  f"95 % limit breached {_pct(stats.get('exceed95'), 1)} of days (target 5 %)"),
                 (f"90% 범위 적중 {_pct(stats.get('coverage90'), 1)}" if ko else
                  f"90 % band hit {_pct(stats.get('coverage90'), 1)}"),
                 (f"초과 빈도 검정 p {_p(tests.get('kupiec95_p'))}" if ko else
                  f"breach-rate test p {_p(tests.get('kupiec95_p'))}")]
        return " · ".join(parts)
    keys = CARD_NUMBERS.get(str(card.get("card_id")), tuple(k for k in _LABELLED if k in stats or k in tests))
    parts = []
    for k in keys:
        if k not in _LABELLED:
            continue
        value = stats.get(k, tests.get(k))
        if _num(value) is None:
            continue
        lab_ko, lab_en, kind = _LABELLED[k]
        parts.append(f"{lab_ko if ko else lab_en} {_fmt(value, kind, language)}")
    return " · ".join(parts) if parts else "—"


# --------------------------------------------------------------------------- #
# Strategy gate checklist: pass / fail from Score fields and validate.GATE
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Check:
    key: str
    label: Pair
    value: str            # the headline number, language neutral
    detail: Pair          # extra numbers next to it ("" when none)
    threshold: Pair
    status: str           # pass | fail | info | na
    help: Pair
    gated: bool


def _getter(score):
    if isinstance(score, Mapping):
        return lambda k, d=None: score.get(k, d)
    return lambda k, d=None: getattr(score, k, d)


def _status(ok, *values) -> str:
    if any(_num(v) is None for v in values):
        return "na"
    return "pass" if ok else "fail"


def strategy_checks(score) -> list[Check]:
    """One row per strategy-gate criterion, judged with validate.GATE on the Score's own fields
    (a `StrategyScore` or a card's stats mapping, whose `ci90` may come from its tests)."""
    g = V.GATE
    get = _getter(score)
    sr = _num(get("sr_oos"))
    ci = get("ci90")
    lo, hi = (_num(ci[0]), _num(ci[1])) if isinstance(ci, (list, tuple)) and len(ci) == 2 else (None, None)
    dsr, pbo, pl = _num(get("dsr")), _num(get("pbo")), _num(get("prob_loss_oos"))
    n_cfg = _num(get("n_configs"))
    oos_is, yp, st = _num(get("oos_is")), _num(get("years_positive")), _num(get("sr_stress"))
    plateau, edge, trades = _num(get("plateau")), bool(get("edge")), _num(get("n_trades"))
    bp, bdiff, bsr = _num(get("bench_p")), _num(get("bench_diff")), _num(get("bench_sr"))
    mdd, bmdd, haircut = _num(get("max_drawdown")), _num(get("bench_mdd")), _num(get("haircut_sr"))
    out: list[Check] = []

    out.append(Check(
        "interval", ("표본 외 샤프 지수", "Out-of-sample Sharpe"), _f2(sr),
        (f"90% 구간 {_f2(lo)} ~ {_f2(hi)}", f"90 % interval {_f2(lo)} to {_f2(hi)}"),
        ("90% 구간 하단 > 0", "interval lower bound > 0"),
        _status(lo is not None and lo > 0, sr, lo),
        ("처음 보는 구간(표본 외)에서 낸 위험 대비 수익입니다. 1 이상이면 좋은 편이며, 90% 신뢰구간의 아래쪽 "
         "끝이 0보다 커야 수익이 우연이 아니라고 봅니다.",
         "Return per unit of risk on data the rule never saw. Above 1 is good; the lower end of the 90 % "
         "interval must be above zero for the return not to be luck."), True))
    out.append(Check(
        "dsr", ("보정 샤프 (DSR)", "Deflated Sharpe (DSR)"), _f2(dsr), ("", ""),
        (f"≥ {g['dsr_min']}", f"≥ {g['dsr_min']}"), _status(dsr is not None and dsr >= g["dsr_min"], dsr),
        ("설정을 여러 번 바꿔 시험하면 우연히 좋은 결과가 나오기 쉽습니다. 시험 횟수를 감안해 성과가 진짜일 "
         f"확률을 계산한 값으로, {g['dsr_min']} 이상이어야 합니다.",
         "Trying many setups makes a lucky result likely. This is the probability the result is real after "
         f"allowing for the number of trials; it must be at least {g['dsr_min']}."), True))
    meaningful = n_cfg is not None and n_cfg >= g["pbo_min_configs"]
    n_txt = "—" if n_cfg is None else f"{n_cfg:.0f}"
    flat = pl is not None and pl <= g["prob_loss_max"]
    if meaningful:
        out.append(Check(
            "pbo", ("과최적화 확률 (PBO)", "Overfitting probability (PBO)"), _f2(pbo),
            (f"최적 설정 패배율 {_pct(pl)}", f"in-sample winner lost in {_pct(pl)} of splits"),
            (f"≤ {g['pbo_max']} (또는 최적 설정 패배율 ≤ {g['prob_loss_max']:.0%})",
             f"≤ {g['pbo_max']}, or losing splits ≤ {g['prob_loss_max']:.0%}"),
            _status((pbo is not None and pbo <= g["pbo_max"]) or flat, pbo, pl),
            ("과거 구간에서 가장 좋았던 설정이 처음 보는 구간에서 하위권으로 떨어질 확률입니다. 낮을수록 "
             "좋습니다. 비슷한 설정만 있으면 0.5가 나오기 쉬워, 과거 최적 설정이 처음 보는 구간에서 실제로 진 "
             "비율(최적 설정 패배율)도 함께 봅니다.",
             "The chance that the best in-sample setup ends up in the bottom half out of sample; lower is "
             "better. Near-identical setups push it to 0.5, so the share of splits the winner actually lost "
             "is read with it."), True))
    else:
        out.append(Check(
            "pbo", ("과최적화 점검 (최적 설정 패배율)", "Over-search check (in-sample winner lost)"), _pct(pl),
            (f"PBO {_f2(pbo)} 참고용 · 설정 {n_txt}개 < {g['pbo_min_configs']}개",
             f"PBO {_f2(pbo)} reported only · {n_txt} setups < {g['pbo_min_configs']}"),
            (f"≤ {g['prob_loss_max']:.0%}", f"≤ {g['prob_loss_max']:.0%}"), _status(flat, pl),
            ("과거 구간에서 가장 좋았던 설정이 처음 보는 구간에서 진 비율입니다. 설정 후보가 8개 미만이면 "
             "PBO 순위가 너무 거칠어 이 비율로 판단합니다.",
             "The share of splits where the best in-sample setup lost out of sample. With fewer than eight "
             "setups the PBO rank is too coarse, so this share decides."), True))
    out.append(Check(
        "oos_is", ("표본 외 / 표본 내 성과 비율", "Out-of-sample / in-sample Sharpe"), _f2(oos_is), ("", ""),
        (f"≥ {g['oos_is_min']}", f"≥ {g['oos_is_min']}"),
        _status(oos_is is not None and oos_is >= g["oos_is_min"], oos_is),
        ("학습 구간 성과 대비 처음 보는 구간 성과의 비율입니다. 0.5보다 작으면 과거에만 잘 맞춘 설정일 "
         "가능성이 큽니다.",
         "Out-of-sample Sharpe as a share of the in-sample Sharpe. Below 0.5 the setup probably only fitted "
         "the past."), True))
    if bp is not None:
        out.append(Check(
            "bench", ("벤치마크 대비 샤프 차이", "Sharpe difference vs benchmark"),
            "—" if bdiff is None else f"{bdiff:+.2f}",
            (f"p {_f2(bp)} · 벤치마크 샤프 {_f2(bsr)}", f"p {_f2(bp)} · benchmark Sharpe {_f2(bsr)}"),
            (f"p ≤ {g['bench_p_max']}", f"p ≤ {g['bench_p_max']}"), _status(bp <= g["bench_p_max"], bp),
            ("같은 자산을 동일 비중으로 그냥 보유했을 때와 샤프 지수를 비교합니다. p가 "
             f"{g['bench_p_max']} 이하여야 '벤치마크보다 낫다'고 말할 수 있습니다.",
             "Compares the Sharpe ratio with simply holding the same assets in equal weights. The claim "
             f"'beats the benchmark' needs p ≤ {g['bench_p_max']}."), True))
    out.append(Check(
        "years", ("수익 낸 해의 비율", "Share of positive years"), _pct(yp), ("", ""),
        (f"≥ {g['years_pos_min']:.0%}", f"≥ {g['years_pos_min']:.0%}"),
        _status(yp is not None and yp >= g["years_pos_min"], yp),
        ("한 해 단위로 수익을 낸 비율입니다. 몇몇 해에만 기대는 전략인지 봅니다.",
         "The share of calendar years with a profit: does the result rely on a few lucky years?"), True))
    out.append(Check(
        "stress", ("거래비용 2배일 때 샤프", "Sharpe at 2× costs"), _f2(st), ("", ""),
        ("> 0", "> 0"), _status(st is not None and st > 0, st),
        ("거래비용을 두 배로 잡아도 수익이 남는지 봅니다.", "Does a profit remain if trading costs double?"), True))
    out.append(Check(
        "plateau", ("설정 안정성", "Parameter stability"), _pct(plateau),
        ("설정 범위 가장자리", "on a grid edge") if edge else ("", ""),
        (f"≥ {g['plateau_min']:.0%}, 가장자리 아님", f"≥ {g['plateau_min']:.0%}, not on an edge"),
        _status(plateau is not None and plateau >= g["plateau_min"] and not edge, plateau),
        ("설정을 조금 바꿔도 성과의 절반 이상이 유지되는 이웃 설정의 비율입니다. 최적 설정이 범위 가장자리에 "
         "있으면 더 넓게 시험해야 합니다.",
         "The share of neighbouring setups that keep at least half the Sharpe. A best setup on the edge of the "
         "grid needs a wider grid."), True))
    out.append(Check(
        "trades", ("표본 외 거래 횟수", "Trades out of sample"), "—" if trades is None else f"{trades:,.0f}",
        ("", ""), (f"≥ {g['trades_min']}", f"≥ {g['trades_min']}"),
        _status(trades is not None and trades >= g["trades_min"], trades),
        ("처음 보는 구간에서 포지션을 바꾼 횟수입니다. 너무 적으면 통계로 판단하기 어렵습니다.",
         "How often the position changed out of sample; too few changes cannot be judged statistically."),
        True))
    out.append(Check(
        "mdd", ("최대 낙폭", "Maximum drawdown"), _pct(mdd),
        (f"벤치마크 {_pct(bmdd)}", f"benchmark {_pct(bmdd)}") if bmdd is not None else ("", ""),
        ("판정에 쓰지 않음", "reported, not gated"), "info" if mdd is not None else "na",
        ("고점에서 가장 크게 떨어졌던 폭입니다. 판정에는 쓰지 않고 참고로 보여 줍니다.",
         "The largest fall from a peak. Shown for reference; it does not decide the verdict."), False))
    out.append(Check(
        "haircut", ("예상 실전 샤프 (할인 후)", "Expected live Sharpe (haircut)"), _f2(haircut), ("", ""),
        (f"참고: 표본 외 샤프 × {g['haircut']}", f"reference: OOS Sharpe × {g['haircut']}"),
        "info" if haircut is not None else "na",
        ("발표된 전략은 실전에서 성과가 26~58% 줄어든다는 연구(McLean–Pontiff)를 반영해 표본 외 샤프에 "
         f"{g['haircut']}을 곱한 예상치입니다.",
         "Published strategies lose 26–58 % of their performance live (McLean–Pontiff); this is the "
         f"out-of-sample Sharpe × {g['haircut']}."), False))
    return out


def check_line(c: Check, language: str) -> str:
    """'보정 샤프 (DSR) 0.77 — 기준 ≥ 0.95: 미달'"""
    detail = pick(c.detail, language)
    value = c.value + (f" ({detail})" if detail else "")
    if not c.gated:                        # reported, not judged: no pass/fail word
        return f"{pick(c.label, language)} {value} — {pick(c.threshold, language)}"
    if language == "ko":
        return f"{c.label[0]} {value} — 기준 {c.threshold[0]}: {STATUS[c.status][0]}"
    return f"{c.label[1]} {value} — needs {c.threshold[1]}: {STATUS[c.status][1].lower()}"


# --------------------------------------------------------------------------- #
# Run result: the verdict a layperson reads first
# --------------------------------------------------------------------------- #
VERDICT_TITLE: dict[str, Pair] = {
    "PASS": ("검증 통과: 이 설정은 모든 검증 기준을 통과했습니다", "Passed: this setup met every validation criterion"),
    "REVISE": ("보완 필요: 일부 기준을 통과하지 못해 고칠 점이 있습니다",
               "Needs revision: some criteria failed and must be fixed first"),
    "REJECT": ("기각: 이 전략은 채택 근거가 부족합니다", "Rejected: the evidence does not support using this strategy"),
    "INSUFFICIENT_DATA": ("판단 보류: 자료가 부족해 결론을 낼 수 없습니다",
                          "Undecided: there is not enough data to reach a verdict"),
    "WITHHELD": ("판정 없음: 이번 실행은 비용 민감도 실험입니다", "No verdict: this run is a cost sensitivity"),
}


def withheld_text(r: Mapping) -> Pair:
    """Korean wording of run_family's withheld sentence; the English is the recorded sentence itself."""
    en = str(r.get("withheld") or "")
    floor, cost = r.get("cost_floor"), r.get("cost_bps")
    if floor is None:
        ko = ("QUANTGEN 비용표에 없는 종목이 있어 이번 실행은 판정(PASS / REJECT)이 아닌 비용 민감도 실험입니다.")
    else:
        ko = (f"입력한 편도 비용 {cost:g}bp가 이 종목들의 기준 비용 {floor:g}bp보다 낮아, 이번 실행은 판정"
              "(PASS / REJECT)이 아닌 비용 민감도 실험입니다.")
    return ko, en


def run_verdict(r: Mapping) -> dict:
    """Title, colour token, 1-3 decisive reasons and the next step for a Lab run result."""
    sc = r["score"]
    checks = strategy_checks(sc)
    if r.get("withheld"):
        return {"code": "NO VERDICT", "decision": "WITHHELD", "token": "muted", "title": VERDICT_TITLE["WITHHELD"],
                "reasons": [withheld_text(r)], "next": None, "checks": checks}
    decision = sc.decision if sc.decision in VERDICT_TITLE else "INSUFFICIENT_DATA"
    (primary, linked) = reason_text(sc.reason)
    reasons: list[Pair] = [primary]
    if decision == "PASS":
        haircut = next((c for c in checks if c.key == "haircut"), None)
        reasons.append((f"과거 자료로 한 검증입니다. 실전 성과는 더 낮을 수 있습니다 (할인 후 예상 샤프 "
                        f"{haircut.value if haircut else '—'}).",
                        f"This is a test on past data; live results can be weaker (expected live Sharpe after the "
                        f"haircut {haircut.value if haircut else '—'})."))
    else:
        failed = [c for c in checks if c.gated and c.status == "fail" and c.key != linked]
        for c in failed[:2]:
            detail = c.detail
            reasons.append((f"{c.label[0]} {c.value}" + (f" ({detail[0]})" if detail[0] else "") +
                            f" — 기준 {c.threshold[0]}",
                            f"{c.label[1]} {c.value}" + (f" ({detail[1]})" if detail[1] else "") +
                            f" — needs {c.threshold[1]}"))
    return {"code": sc.decision, "decision": decision, "token": VERDICT_TOKEN.get(decision, "muted"),
            "title": VERDICT_TITLE[decision], "reasons": reasons, "next": revise_target_text(sc.revise_target),
            "checks": checks}


# --------------------------------------------------------------------------- #
# Small recorded sentences rendered in Korean
# --------------------------------------------------------------------------- #
def exposure_lines_ko(info: Optional[Mapping]) -> list[str]:
    """Korean wording of strategy_exposure.exposure_lines, line for line, from the same numbers."""
    if info is None:
        return []
    cap = f"{info['per_asset_cap_min']:g}–{info['per_asset_cap_max']:g}배"
    if info["per_asset_cap_min"] == info["per_asset_cap_max"]:
        cap = f"{info['per_asset_cap_max']:g}배"
    return [
        f"자산별 비중 상한 {cap}, 독립적으로 운용하는 자산 {info['asset_count']}개, 포트폴리오 전체 상한 없음. "
        f"이론상 총 노출 상한 {info['theoretical_gross_upper_bound']:g}배. 자산별 규칙이라 여러 자산을 넣으면 "
        "비중이 정규화되지 않고 그대로 더해집니다(포트폴리오 변동성 목표가 아님).",
        f"표본 외 실제 총 노출: 평균 {info['gross_mean']:.2f}배, 최대 {info['gross_max']:.2f}배 "
        f"({info['observations']}개 관측). 워크포워드 시점마다 선택된 설정 기준이며, 마지막 최적 설정을 전 기간에 "
        "적용한 값이 아닙니다.",
        f"표본 외 최대 차입 {info['borrowing_max']:.2f}배(자본 대비). 현금 = 1 − 비중 합계이며, 음수 현금은 "
        f"거래일당 {info['cash_rate_per_session']:.8f}로 빌린 것으로 계산합니다(실험실 가정: 연 3% / 252). "
        "1배 동일 비중 일간 수익률 벤치마크는 노출을 맞춘 비교가 아닙니다.",
    ]


def walk_forward_text(note: str) -> Pair:
    m = re.fullmatch(r"IS (\d+) / OOS (\d+) / embargo (\d+); (\d+) origins; (\d+) configs", str(note or ""))
    if not m:
        return str(note), str(note)
    w_is, w_oos, emb, n_o, n_c = m.groups()
    return (f"학습 {w_is}일 · 검증 {w_oos}일 · 간격 {emb}일 · 재선정 {n_o}회 · 설정 후보 {n_c}개",
            f"train {w_is} · test {w_oos} · gap {emb} sessions · {n_o} re-selections · {n_c} setups")


def convention_text(text: str) -> Pair:
    m = re.match(r"Mixed return conventions: (.*) include reinvested dividends, (.*) are price-only", str(text or ""))
    if not m:
        return str(text), str(text)
    return (f"수익률 기준이 섞여 있습니다: {m.group(1)}은(는) 배당 재투자 포함, {m.group(2)}은(는) 가격만(배당 제외)입니다. "
            "두 묶음의 수익률은 배당수익률만큼 달라 비교가 앞 묶음 쪽으로 기웁니다. 모든 종목을 한 기준으로 맞추세요: "
            "총수익은 Yahoo(국내 코드는 005930.KS), 가격 수익은 KIS(미국 종목은 NAS:AAPL).", str(text))


# Strategy parameter names of the Lab families (strategy_workflow.FAMILIES grids).
PARAM: dict[str, Pair] = {
    "rule": ("규칙", "rule"), "lookback": ("관측 기간", "lookback"), "step": ("재조정 간격", "step"),
    "target": ("목표 변동성", "target"), "window": ("추정 기간", "window"), "skip": ("제외 기간", "skip"),
    "top": ("상위 비율", "top"), "long_only": ("매수만", "long only"), "vol_target_ann": ("연 목표 변동성", "vol target"),
    "cap": ("상한", "cap"), "hysteresis": ("완충 폭", "hysteresis"), "formation": ("형성 기간", "formation"),
    "trading": ("거래 기간", "trading"), "entry": ("진입 z", "entry z"), "exit": ("청산 z", "exit z"),
}


def _korean(text: str) -> str:
    """The reviewed Korean caption of a fixed English label (core.ui_page_messages), else the label."""
    from core.ui_legacy_messages import static_text
    return static_text(text, "ko")


def run_sections(r: Mapping, language: str) -> list[tuple[str, list[str]]]:
    """Structured local commentary for a Lab run: conclusion, data and setup, results, risks."""
    ko = language == "ko"
    v = run_verdict(r)
    sc = r["score"]
    conclusion = [f"{pick(v['title'], language)} ({v['code']})"] + [pick(x, language) for x in v["reasons"]]
    if v["next"]:
        conclusion.append(("다음 단계: " if ko else "Next step: ") + pick(v["next"], language))
    panel = r["panel"]
    dates = list(getattr(panel, "dates", []) or [])
    srcs = ", ".join(f"{s} {pick(source_label(src), language)}" for s, src in zip(r["symbols"], r["sources"]))
    chosen = ", ".join(f"{pick(PARAM.get(k, (k, k)), language)} {v_}"
                       for k, v_ in dict(r.get("chosen") or {}).items()) or "—"
    data = [
        (f"전략: {_korean(r['label'])} · 종목: {', '.join(r['symbols'])}" if ko else
         f"Strategy: {r['label']} · symbols: {', '.join(r['symbols'])}"),
        (f"데이터: {srcs}" if ko else f"Data: {srcs}"),
        (f"기간: {dates[0]} ~ {dates[-1]} (공통 거래일 {len(panel):,}일)" if ko and dates else
         f"Period: {dates[0]} to {dates[-1]} ({len(panel):,} shared sessions)" if dates else ""),
        (f"편도 거래비용 {r['cost_bps']:g}bp · 시험한 설정 {len(r['grid'])}개 = 시험 횟수 {sc.n_trials}회" if ko else
         f"Cost {r['cost_bps']:g} bp per side · {len(r['grid'])} setups tried = {sc.n_trials} trials"),
        ("워크포워드: " if ko else "Walk-forward: ") + pick(walk_forward_text(r["wf"].note), language),
        (f"마지막 학습 구간의 최적 설정: {chosen}" if ko else f"Last in-sample winner: {chosen}"),
    ]
    results = [check_line(c, language) for c in v["checks"] if c.gated]
    risks = [check_line(c, language) for c in v["checks"] if not c.gated]
    if sc.regime:
        rg = sc.regime
        risks.append((f"국면별 샤프: 고변동 {_f2(rg.get('high_vol'))} / 저변동 {_f2(rg.get('low_vol'))}, "
                      f"상승장 {_f2(rg.get('up_market'))} / 하락장 {_f2(rg.get('down_market'))}") if ko else
                     (f"Regime Sharpe: high-vol {_f2(rg.get('high_vol'))} / low-vol {_f2(rg.get('low_vol'))}, "
                      f"up {_f2(rg.get('up_market'))} / down {_f2(rg.get('down_market'))}"))
    from core.research.strategy_exposure import exposure_lines
    risks += exposure_lines_ko(r.get("exposure")) if ko else exposure_lines(r.get("exposure"))
    if "SYNTHETIC" in r["sources"]:
        risks.append("합성(가상) 데이터가 섞여 있어 이 판정은 연습용입니다." if ko else
                     "Synthetic data in the panel: the verdict is a toy.")
    risks.append("과거 자료에 대한 검증이며 미래 수익을 보장하지 않습니다." if ko else
                 "A test on past data; it does not promise future returns.")
    heads = (("결론", "데이터와 설정", "검증 결과", "위험과 참고") if ko else
             ("Conclusion", "Data and setup", "Validation results", "Risks and notes"))
    return [(heads[0], conclusion), (heads[1], [x for x in data if x]), (heads[2], results), (heads[3], risks)]


def iter_display_texts(card: Mapping) -> Iterable[str]:
    """Every catalogue string the scorecard shows for a card (both languages), for the acceptance test."""
    t = card_text(card)
    (reason, _) = reason_text(card.get("decision_reason", ""), card)
    target = revise_target_text(card.get("revise_target"))
    yield from (*t.name, *t.what, *reason, *kind_label(card.get("kind", "")))
    yield key_numbers(card, "ko")
    yield key_numbers(card, "en")
    if target:
        yield from target
