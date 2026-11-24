"""Measurement metrics for DIDM Stage 1 (PREREG_V0 3, Stage 1 row) and for any scorer's evaluation set.

Plain functions over Python sequences, standard library only, so the same code can score the
in-house model's news-type evaluation set and the DIDM gold set. Nothing here reads a clock,
a file or the network. Every function refuses empty or mismatched input instead of returning
a number that looks like a result.
"""
from __future__ import annotations

import math
import random
from collections import Counter
from dataclasses import dataclass
from typing import Hashable, Mapping, Sequence


class MetricError(ValueError):
    pass


def _paired(a: Sequence, b: Sequence, what: str) -> int:
    if len(a) != len(b):
        raise MetricError(f"{what}: the two sequences differ in length")
    if not a:
        raise MetricError(f"{what}: no items")
    return len(a)


def cohen_kappa(labels_a: Sequence[Hashable], labels_b: Sequence[Hashable]) -> float:
    """Cohen's kappa for two annotators over the same items (unweighted).

    If both annotators used one and the same single label for every item, chance agreement is 1
    and kappa is undefined; that case raises instead of reporting perfect agreement.
    """
    n = _paired(labels_a, labels_b, "kappa")
    observed = sum(x == y for x, y in zip(labels_a, labels_b)) / n
    count_a, count_b = Counter(labels_a), Counter(labels_b)
    expected = sum(count_a[k] * count_b.get(k, 0) for k in count_a) / (n * n)
    if expected >= 1.0:
        raise MetricError("kappa is undefined: both annotators used a single label throughout")
    return (observed - expected) / (1.0 - expected)


@dataclass(frozen=True)
class ClassScore:
    label: str
    precision: float
    recall: float
    f1: float
    support: int        # gold items with this label
    predicted: int


def per_class(gold: Sequence[Hashable], pred: Sequence[Hashable], labels: Sequence[Hashable]) -> list[ClassScore]:
    _paired(gold, pred, "classification")
    known = set(labels)
    if len(known) != len(labels):
        raise MetricError("labels must be distinct")
    stray = {x for x in (*gold, *pred) if x not in known}
    if stray:
        raise MetricError("a gold or predicted label is outside the label list")
    out = []
    for label in labels:
        tp = sum(g == label and p == label for g, p in zip(gold, pred))
        n_gold, n_pred = sum(g == label for g in gold), sum(p == label for p in pred)
        precision = tp / n_pred if n_pred else 0.0
        recall = tp / n_gold if n_gold else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        out.append(ClassScore(str(label), precision, recall, f1, n_gold, n_pred))
    return out


def macro_f1(gold: Sequence[Hashable], pred: Sequence[Hashable], labels: Sequence[Hashable]) -> float:
    """Unweighted mean F1 over the labels that occur in the gold set.

    A label with no gold item has no recall to measure, so it is left out of the mean; predicting
    it still costs precision on other labels' items. A label with gold items and no correct
    prediction counts as F1 = 0.
    """
    scored = [c for c in per_class(gold, pred, labels) if c.support > 0]
    return sum(c.f1 for c in scored) / len(scored)


def accuracy(gold: Sequence[Hashable], pred: Sequence[Hashable]) -> float:
    n = _paired(gold, pred, "accuracy")
    return sum(g == p for g, p in zip(gold, pred)) / n


@dataclass(frozen=True)
class LinkScore:
    precision: float
    recall: float
    true_links: int
    predicted_links: int
    gold_links: int


def linking_scores(gold_links: set[tuple[str, str]], predicted_links: set[tuple[str, str]]) -> LinkScore:
    """Entity-linking precision and recall over (article_id, entity_id) pairs."""
    if not isinstance(gold_links, (set, frozenset)) or not isinstance(predicted_links, (set, frozenset)):
        raise MetricError("links must be sets of (article_id, entity_id)")
    if not gold_links:
        raise MetricError("linking: the gold set has no links")
    if not predicted_links:
        raise MetricError("linking: no predicted links, so precision is undefined")
    hit = len(gold_links & predicted_links)
    return LinkScore(hit / len(predicted_links), hit / len(gold_links), hit, len(predicted_links), len(gold_links))


def _check_probs(probs: Sequence[Mapping[Hashable, float]], labels: Sequence[Hashable]) -> None:
    for row in probs:
        if set(row) != set(labels):
            raise MetricError("each probability row must have exactly the label list as keys")
        total = 0.0
        for value in row.values():
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0.0 <= value <= 1.0:
                raise MetricError("probabilities must be numbers in [0, 1]")
            total += value
        if abs(total - 1.0) > 1e-6:
            raise MetricError("each probability row must sum to 1")


def brier(probs: Sequence[Mapping[Hashable, float]], outcomes: Sequence[Hashable], labels: Sequence[Hashable]) -> float:
    """Multi-class Brier score: mean over items of sum over labels of (p - 1[outcome])^2. Lower is better."""
    n = _paired(probs, outcomes, "brier")
    _check_probs(probs, labels)
    if any(o not in set(labels) for o in outcomes):
        raise MetricError("an outcome is outside the label list")
    return sum(sum((row[k] - (1.0 if k == o else 0.0)) ** 2 for k in labels) for row, o in zip(probs, outcomes)) / n


def base_rates(outcomes: Sequence[Hashable], labels: Sequence[Hashable]) -> dict[Hashable, float]:
    if not outcomes:
        raise MetricError("base rates: no items")
    counts = Counter(outcomes)
    return {k: counts.get(k, 0) / len(outcomes) for k in labels}


def brier_skill(probs: Sequence[Mapping[Hashable, float]], outcomes: Sequence[Hashable], labels: Sequence[Hashable],
                reference: Mapping[Hashable, float]) -> float:
    """1 - Brier(model) / Brier(reference), the reference being one fixed probability row for every item.

    Pass the class frequencies of an EARLIER set (the calibration split) as the reference: using the
    test set's own frequencies would hand the reference information the model does not have.
    """
    ref = brier([dict(reference)] * len(outcomes), outcomes, labels)
    if ref == 0.0:
        raise MetricError("the reference forecast is perfect, so skill is undefined")
    return 1.0 - brier(probs, outcomes, labels) / ref


@dataclass(frozen=True)
class ReliabilityBin:
    lower: float
    upper: float
    count: int
    mean_confidence: float
    accuracy: float


def reliability(confidences: Sequence[float], correct: Sequence[bool], n_bins: int = 10) -> list[ReliabilityBin]:
    """Equal-width bins on [0, 1]; the last bin includes 1."""
    n = _paired(confidences, correct, "reliability")
    if isinstance(n_bins, bool) or not isinstance(n_bins, int) or n_bins < 2:
        raise MetricError("n_bins must be an integer of at least 2")
    for c in confidences:
        if isinstance(c, bool) or not isinstance(c, (int, float)) or not 0.0 <= c <= 1.0:
            raise MetricError("confidences must be numbers in [0, 1]")
    sums = [[0, 0.0, 0] for _ in range(n_bins)]
    for c, ok in zip(confidences, correct):
        i = min(int(c * n_bins), n_bins - 1)
        sums[i][0] += 1
        sums[i][1] += c
        sums[i][2] += bool(ok)
    return [ReliabilityBin(i / n_bins, (i + 1) / n_bins, cnt, conf / cnt if cnt else 0.0, hit / cnt if cnt else 0.0)
            for i, (cnt, conf, hit) in enumerate(sums)]


def ece(confidences: Sequence[float], correct: Sequence[bool], n_bins: int = 10) -> float:
    """Expected calibration error: sum over bins of (bin share) * |accuracy - mean confidence|."""
    bins = reliability(confidences, correct, n_bins)
    n = len(confidences)
    return sum(b.count / n * abs(b.accuracy - b.mean_confidence) for b in bins)


def top_label(probs: Sequence[Mapping[Hashable, float]], labels: Sequence[Hashable]) -> tuple[list, list[float]]:
    """The most probable label of each row (first in label order on a tie) and its probability."""
    _check_probs(probs, labels)
    picks, confs = [], []
    for row in probs:
        best = max(labels, key=lambda k: (row[k], -list(labels).index(k)))
        picks.append(best)
        confs.append(float(row[best]))
    return picks, confs


def top_label_ece(probs: Sequence[Mapping[Hashable, float]], outcomes: Sequence[Hashable],
                  labels: Sequence[Hashable], n_bins: int = 10) -> float:
    _paired(probs, outcomes, "ece")
    picks, confs = top_label(probs, labels)
    return ece(confs, [p == o for p, o in zip(picks, outcomes)], n_bins)


@dataclass(frozen=True)
class PairedDifference:
    difference: float          # metric(a) - metric(b) on the full set
    lower: float               # percentile bootstrap interval of the difference
    upper: float
    level: float
    resamples: int


def paired_bootstrap(gold: Sequence, pred_a: Sequence, pred_b: Sequence, metric, *, seed: int,
                     resamples: int = 2000, level: float = 0.90) -> PairedDifference:
    """Percentile bootstrap of metric(gold, a) - metric(gold, b), resampling items with replacement.

    ``metric(gold, pred)`` returns a float. A resample on which the metric is undefined is skipped
    and not replaced; more than 5% skipped raises.
    """
    n = _paired(gold, pred_a, "bootstrap")
    _paired(gold, pred_b, "bootstrap")
    if not 0.5 < level < 1.0 or resamples < 100:
        raise MetricError("level must be in (0.5, 1) and resamples at least 100")
    rng = random.Random(seed)
    full = metric(gold, pred_a) - metric(gold, pred_b)
    draws = []
    for _ in range(resamples):
        idx = [rng.randrange(n) for _ in range(n)]
        g, a, b = [gold[i] for i in idx], [pred_a[i] for i in idx], [pred_b[i] for i in idx]
        try:
            draws.append(metric(g, a) - metric(g, b))
        except (MetricError, ZeroDivisionError):
            continue
    if len(draws) < 0.95 * resamples:
        raise MetricError("the metric was undefined on too many resamples")
    draws.sort()
    tail = (1.0 - level) / 2.0
    lo = draws[int(math.floor(tail * (len(draws) - 1)))]
    hi = draws[int(math.ceil((1.0 - tail) * (len(draws) - 1)))]
    return PairedDifference(full, lo, hi, level, len(draws))
