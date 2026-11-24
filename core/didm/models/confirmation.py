"""DIDM-8 market confirmation: the registered rule of PREREG_V0 section 4 as code.

    expected reaction : r_i = alpha + beta * r_m fitted on trading days [-125, -6] before the event (120 days)
    event window      : firm [0, +1] trading days; macro [0, +60 minutes] with intraday data, else [0, +1] days
    ALREADY_PRICED    : |CAR[-5, -1]| > 2 * sigma * sqrt(5) in the predicted direction   (decided first)
    CONFIRMED         : window move in the predicted direction and |AR| > 2 * sigma (sigma scaled by sqrt(n))
    CONTRADICTED      : window move against the predicted direction and |AR| > 2 * sigma
    PENDING           : window not finished, or none of the above

sigma is the residual standard deviation of the estimation window. The caller supplies the returns
(this module reads no price source, no clock and no network) and says how far the data reaches at
decision time, so a window that has not finished can never be scored from later data.

"A market reaction that disagrees is not turned into a buy signal": the result is a label on the
score record (market_confirmation) and nothing here sizes or places anything.

Readings made here (DIDM_DEV, 2026-11-24; listed in docs/didm/MARKET_CONFIRMATION_V0.md):
ALREADY_PRICED is decided from the five days before the event alone, even while the event window is
still open; a neutral prediction (direction 0) is never confirmed or contradicted; too little history
for the 120-day window gives PENDING with a reason, not an estimate from fewer days.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np

from core.didm.llm.schema import MarketConfirmation

# --- registered values (PREREG_V0 4; not tunable) ---
ESTIMATION_FIRST, ESTIMATION_LAST = -125, -6        # 120 trading days, ending before the pre-event window
ESTIMATION_DAYS = ESTIMATION_LAST - ESTIMATION_FIRST + 1
EVENT_FIRST, EVENT_LAST = 0, 1                      # [0, +1] trading days
PRE_FIRST, PRE_LAST = -5, -1                        # CAR[-5, -1]
SIGMA_MULTIPLE = 2.0
INTRADAY_WINDOW_MINUTES = 60


class ConfirmationError(ValueError):
    pass


@dataclass(frozen=True)
class ConfirmationConfig:
    """Readings of the registered rule that are a choice (docs/didm/PREREG_V0_1_PROPOSAL_2026-11-24.md,
    section 10). The registered numbers above are not part of this.

    already_priced = "pre_window_alone": ALREADY_PRICED is decided from the five days before the event as
    soon as they are known, even while the event window is still open ("먼저 판정" read as first in time too).
    already_priced = "after_event_window": the same check, but nothing is decided until the event window has
    finished; until then the status is PENDING.
    """
    already_priced: str = "pre_window_alone"

    def __post_init__(self) -> None:
        if self.already_priced not in ("pre_window_alone", "after_event_window"):
            raise ConfirmationError("already_priced is pre_window_alone or after_event_window")


DEFAULT_CONFIG = ConfirmationConfig()


@dataclass(frozen=True)
class MarketModel:
    alpha: float
    beta: float
    sigma: float            # residual standard deviation per period
    n: int


@dataclass(frozen=True)
class Confirmation:
    status: MarketConfirmation
    reason: str
    window_move: float | None = None      # cumulative abnormal move over the event window
    window_threshold: float | None = None
    pre_move: float | None = None         # cumulative abnormal move over [-5, -1]
    pre_threshold: float | None = None
    sigma: float | None = None


def _series(values: Sequence[float], name: str) -> np.ndarray:
    out = np.asarray(values, dtype=float)
    if out.ndim != 1:
        raise ConfirmationError(f"{name} must be a one-dimensional series of returns")
    return out


def _direction(value: int) -> int:
    if isinstance(value, bool) or value not in (-1, 0, 1):
        raise ConfirmationError("predicted_direction must be +1, -1 or 0")
    return int(value)


def fit_market_model(asset: Sequence[float], market: Sequence[float]) -> MarketModel:
    """OLS of asset returns on market returns; sigma uses n - 2 degrees of freedom."""
    y, x = _series(asset, "asset"), _series(market, "market")
    if len(y) != len(x) or len(y) < 3 or not (np.isfinite(y).all() and np.isfinite(x).all()):
        raise ConfirmationError("the estimation window needs two equal-length finite series")
    xc = x - x.mean()
    denom = float(xc @ xc)
    if denom <= 0.0:
        raise ConfirmationError("the market return does not vary in the estimation window")
    beta = float(xc @ (y - y.mean())) / denom
    alpha = float(y.mean() - beta * x.mean())
    resid = y - alpha - beta * x
    return MarketModel(alpha, beta, math.sqrt(float(resid @ resid) / (len(y) - 2)), len(y))


def decide(*, predicted_direction: int, sigma: float, pre_move: float | None, pre_periods: int,
           window_move: float | None, window_periods: int,
           config: ConfirmationConfig = DEFAULT_CONFIG) -> Confirmation:
    """The registered decision from already-computed abnormal moves. ``window_move`` is None while the
    event window is unfinished; ``pre_move`` is None when the pre-event window is not available."""
    direction = _direction(predicted_direction)
    if not (isinstance(sigma, (int, float)) and math.isfinite(sigma) and sigma > 0):
        raise ConfirmationError("sigma must be a positive finite number")
    if pre_periods < 1 or window_periods < 1:
        raise ConfirmationError("window lengths must be at least one period")
    pre_threshold = SIGMA_MULTIPLE * sigma * math.sqrt(pre_periods)
    window_threshold = SIGMA_MULTIPLE * sigma * math.sqrt(window_periods)
    common = dict(pre_move=pre_move, pre_threshold=pre_threshold, window_threshold=window_threshold, sigma=sigma)
    if direction == 0:
        return Confirmation(MarketConfirmation.PENDING, "neutral prediction: nothing to confirm",
                            window_move=window_move, **common)
    if config.already_priced == "after_event_window" and window_move is None:
        return Confirmation(MarketConfirmation.PENDING, "event window not finished", **common)
    if pre_move is not None and abs(pre_move) > pre_threshold and pre_move * direction > 0:
        return Confirmation(MarketConfirmation.ALREADY_PRICED, "the move came in the five periods before the event",
                            window_move=window_move, **common)
    if window_move is None:
        return Confirmation(MarketConfirmation.PENDING, "event window not finished", **common)
    if abs(window_move) > window_threshold:
        if window_move * direction > 0:
            return Confirmation(MarketConfirmation.CONFIRMED, "abnormal move in the predicted direction",
                                window_move=window_move, **common)
        return Confirmation(MarketConfirmation.CONTRADICTED, "abnormal move against the predicted direction",
                            window_move=window_move, **common)
    return Confirmation(MarketConfirmation.PENDING, "no abnormal move in the event window", window_move=window_move,
                        **common)


def confirm_daily(asset: Sequence[float], market: Sequence[float], *, event_index: int, last_known_index: int,
                  predicted_direction: int, config: ConfirmationConfig = DEFAULT_CONFIG) -> Confirmation:
    """Firm (or macro without intraday data): daily returns of the asset and its index, aligned by trading day.

    ``event_index`` is the position of day 0. ``last_known_index`` is the last position whose return is
    known at decision time; nothing after it is read, whatever the arrays contain.
    """
    y, x = _series(asset, "asset"), _series(market, "market")
    if len(y) != len(x):
        raise ConfirmationError("asset and market series must be aligned")
    for name, value in (("event_index", event_index), ("last_known_index", last_known_index)):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ConfirmationError(f"{name} must be an integer position")
    if not 0 <= event_index < len(y) or last_known_index >= len(y):
        raise ConfirmationError("event_index or last_known_index is outside the series")
    direction = _direction(predicted_direction)
    known = last_known_index
    first, last = event_index + ESTIMATION_FIRST, event_index + ESTIMATION_LAST
    if first < 0 or known < last:
        return Confirmation(MarketConfirmation.PENDING, f"fewer than {ESTIMATION_DAYS} estimation days available")
    est_y, est_x = y[first: last + 1], x[first: last + 1]
    if not (np.isfinite(est_y).all() and np.isfinite(est_x).all()):
        return Confirmation(MarketConfirmation.PENDING, "missing returns in the estimation window")
    model = fit_market_model(est_y, est_x)
    if model.sigma <= 0.0:
        return Confirmation(MarketConfirmation.PENDING, "no residual variation in the estimation window")

    def abnormal(lo: int, hi: int) -> float | None:
        a, b = event_index + lo, event_index + hi
        if b > known:
            return None
        seg_y, seg_x = y[a: b + 1], x[a: b + 1]
        if not (np.isfinite(seg_y).all() and np.isfinite(seg_x).all()):
            return None
        return float((seg_y - model.alpha - model.beta * seg_x).sum())

    return decide(predicted_direction=direction, sigma=model.sigma,
                  pre_move=abnormal(PRE_FIRST, PRE_LAST), pre_periods=PRE_LAST - PRE_FIRST + 1,
                  window_move=abnormal(EVENT_FIRST, EVENT_LAST), window_periods=EVENT_LAST - EVENT_FIRST + 1,
                  config=config)


def window_sigma(past_window_moves: Sequence[float]) -> float:
    """Standard deviation of past same-length window moves (for the macro intraday rule): e.g. the
    60-minute moves at the same time of day on the 120 estimation days."""
    moves = _series(past_window_moves, "past_window_moves")
    if len(moves) < 20 or not np.isfinite(moves).all():
        raise ConfirmationError("need at least 20 finite past window moves")
    return float(moves.std(ddof=1))


def confirm_intraday(*, window_move: float | None, past_window_moves: Sequence[float], pre_daily_move: float | None,
                     daily_sigma: float | None, predicted_direction: int,
                     config: ConfirmationConfig = DEFAULT_CONFIG) -> Confirmation:
    """Macro event with intraday data: the [0, +60 minutes] move against the spread of past 60-minute moves.

    The pre-event check still uses the five trading days before (daily sigma); pass None for both when
    daily data is not available and only the window is judged.
    """
    sigma = window_sigma(past_window_moves)
    direction = _direction(predicted_direction)
    if config.already_priced == "after_event_window" and window_move is None:
        return decide(predicted_direction=direction, sigma=sigma, pre_move=None, pre_periods=1, window_move=None,
                      window_periods=1, config=config)
    if direction != 0 and pre_daily_move is not None and daily_sigma is not None:
        pre = decide(predicted_direction=direction, sigma=daily_sigma, pre_move=pre_daily_move,
                     pre_periods=PRE_LAST - PRE_FIRST + 1, window_move=None, window_periods=1)
        if pre.status is MarketConfirmation.ALREADY_PRICED:
            return pre
    return decide(predicted_direction=direction, sigma=sigma, pre_move=None, pre_periods=1,
                  window_move=window_move, window_periods=1)
