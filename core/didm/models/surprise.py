"""DIDM-8 macro surprise and prediction-market liquidity: PREREG_V0 section 4, last two rows.

    surprise        : (released value - consensus) / historical standard deviation, when a consensus exists;
                      otherwise "unknown" plus the change in a FedWatch or prediction-market probability
    liquidity floor : a prediction market with fewer than 1,000 contracts traded is not liquid and is
                      left out of signals and shocks

Reading made here (DIDM_DEV, 2026-11-24): the "historical standard deviation" is that of past surprises
(released minus consensus) of the same indicator, released strictly before this one, at least 8 of them.
The caller supplies every number; nothing here reads a data source, a clock or the network.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

KALSHI_MIN_VOLUME = 1000          # contracts (PREREG_V0 4)
MIN_PAST_SURPRISES = 8
UNKNOWN = "unknown"               # "미상"
STANDARDISED = "standardised"


class SurpriseError(ValueError):
    pass


def _number(value, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise SurpriseError(f"{name} must be a finite number")
    return float(value)


def is_liquid(volume_contracts) -> bool:
    """True when at least 1,000 contracts traded. A missing or invalid volume is not liquid."""
    if isinstance(volume_contracts, bool) or not isinstance(volume_contracts, (int, float)):
        return False
    return math.isfinite(volume_contracts) and volume_contracts >= KALSHI_MIN_VOLUME


@dataclass(frozen=True)
class ProbabilityMove:
    change: float | None          # after - before, in probability points; None when the market is not usable
    liquid: bool
    reason: str


def probability_move(before, after, volume_contracts) -> ProbabilityMove:
    if not is_liquid(volume_contracts):
        return ProbabilityMove(None, False, f"volume below {KALSHI_MIN_VOLUME} contracts: left out")
    p0, p1 = _number(before, "probability before"), _number(after, "probability after")
    if not (0.0 <= p0 <= 1.0 and 0.0 <= p1 <= 1.0):
        raise SurpriseError("probabilities must be in [0, 1]")
    return ProbabilityMove(p1 - p0, True, "liquid market")


@dataclass(frozen=True)
class MacroSurprise:
    kind: str                     # "standardised" or "unknown"
    value: float | None           # standardised surprise, None when unknown
    probability: ProbabilityMove | None
    reason: str


def standardised_surprise(released, consensus, past_surprises: Sequence[float]) -> float:
    actual, expected = _number(released, "released value"), _number(consensus, "consensus")
    history = [_number(x, "past surprise") for x in past_surprises]
    if len(history) < MIN_PAST_SURPRISES:
        raise SurpriseError(f"need at least {MIN_PAST_SURPRISES} past surprises")
    mean = sum(history) / len(history)
    sd = math.sqrt(sum((x - mean) ** 2 for x in history) / (len(history) - 1))
    if sd <= 0.0:
        raise SurpriseError("past surprises do not vary")
    return (actual - expected) / sd


def macro_surprise(*, released, consensus=None, past_surprises: Sequence[float] = (),
                   probability: ProbabilityMove | None = None) -> MacroSurprise:
    """Standardised surprise when a consensus and enough history exist; otherwise "unknown", carrying the
    probability move of a liquid market if the caller has one. A missing consensus is never filled in."""
    _number(released, "released value")
    if probability is not None and not isinstance(probability, ProbabilityMove):
        raise SurpriseError("probability must be a ProbabilityMove")
    if consensus is None:
        return MacroSurprise(UNKNOWN, None, probability, "no consensus")
    if len(past_surprises) < MIN_PAST_SURPRISES:
        return MacroSurprise(UNKNOWN, None, probability, f"fewer than {MIN_PAST_SURPRISES} past surprises")
    return MacroSurprise(STANDARDISED, standardised_surprise(released, consensus, past_surprises), probability,
                         "consensus available")
