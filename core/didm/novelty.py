"""DIDM novelty (and relevance) models, V0 -- owner decision P2, 2026-11-18.

Owner (verbatim): "시간만을 더미변수로 간주하고 점수로 매기기보다, 가능한 모든 요소(변수화)를
고려한 데이터과학/계량경제학적 모형(다중회귀든 time series든 상관 없음)을 세우고(이때의 y변수는
신규성이 되는 것도 하나 세울 것), 이때 기존 cutoff(0.75)에서 test를 했을 때 기대되는 accuracy가
0.9 이상이 되도록 하여 신규성을 평가할 것."

So novelty is not a time-decay score. It is P(new event | features) from a
pre-registered model (PREREG_V0 4.1):

* y = ``is_new_event`` from the Stage 1 gold set (a second model uses y = ``is_subject``
  for relevance, same machinery).
* X = every point-in-time feature we can compute from metadata (FEATURES below);
  the 24-hour window and rank decay are features, not the score.
* Logistic regression (IRLS, small ridge penalty), deterministic.
* Test = time-ordered hold-out (last 30% by received_at; no shuffling, so the
  test is out-of-sample in time). Pass = accuracy >= 0.90 at cutoff 0.75.
  Reported next to it: majority-class accuracy, balanced accuracy, precision,
  recall (a 0.90 accuracy can be trivial when 90% of articles are new).

Features use only articles received strictly before the article itself, so adding
later articles never changes an earlier article's features. No network; numpy only.
The similarity function is injected (MinHash, embeddings, ... decided outside).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Sequence

import numpy as np

from core.didm.llm.schema import EventType

CUTOFF = 0.75
TARGET_ACCURACY = 0.90
TEST_FRACTION = 0.30
SIM_THRESHOLD = 0.80          # "similar" for the count features (PREREG_V0 4.1)
WINDOW = timedelta(hours=24)
ENTITY_WINDOW = timedelta(days=7)
RIDGE = 1e-3
_TYPES = [e for e in EventType if e is not EventType.NONE]

FEATURES = (
    ["intercept", "max_sim_24h", "n_sim_24h_log", "hours_since_sim_log", "n_sources_sim_24h_log",
     "cluster_decay", "entity_count_7d_log", "entity_type_count_24h_log",
     "tier1", "tier3", "hour_sin", "hour_cos", "weekend"]
    + [f"type_{t.value}" for t in _TYPES]
)


@dataclass(frozen=True)
class Article:
    article_id: str
    received_at: datetime
    entity_id: str | None
    event_type: EventType
    source_id: str
    source_tier: int          # 1 official/wire, 2 major outlet, 3 social/other


class NoveltyError(ValueError):
    pass


def _numeric_array(value, name: str, ndim: int) -> np.ndarray:
    try:
        out = np.asarray(value)
    except (TypeError, ValueError):
        raise NoveltyError(f"{name} must be a {ndim}D numeric array") from None
    if out.ndim != ndim or out.dtype.kind not in "biuf" or not out.size:
        raise NoveltyError(f"{name} must be a non-empty {ndim}D numeric array")
    with np.errstate(over="ignore", invalid="ignore"):
        out = out.astype(float)
    if not np.isfinite(out).all():
        raise NoveltyError(f"{name} must contain only finite values")
    return out


def _binary_labels(value) -> np.ndarray:
    # Validate before integer conversion: 0.9 is not a negative-class label.
    y = _numeric_array(value, "y", 1)
    if not np.isin(y, (0.0, 1.0)).all():
        raise NoveltyError("y must be 0/1")
    return y


def _probability_threshold(value, name: str, *, endpoints: bool) -> float:
    try:
        number = np.asarray(value)
    except (TypeError, ValueError):
        raise NoveltyError(f"{name} must be a finite numeric scalar") from None
    if number.ndim != 0 or number.dtype.kind not in "iuf":
        raise NoveltyError(f"{name} must be a finite numeric scalar")
    number = float(number)
    valid = 0.0 <= number <= 1.0 if endpoints else 0.0 < number < 1.0
    if not math.isfinite(number) or not valid:
        interval = "[0, 1]" if endpoints else "(0, 1)"
        raise NoveltyError(f"{name} must be in {interval}")
    return number


def _utc_received(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise NoveltyError("received_at must be timezone-aware")
    return value.astimezone(timezone.utc)


def build_features(articles: Sequence[Article],
                   similarity: Callable[[Article, Article], float]) -> np.ndarray:
    """One feature row per article, in the input order, from strictly earlier articles only."""
    received = [_utc_received(a.received_at) for a in articles]
    order = sorted(range(len(articles)), key=lambda i: (received[i], articles[i].article_id))
    rows = np.zeros((len(articles), len(FEATURES)))
    seen: list[tuple[Article, datetime]] = []
    for i in order:
        a = articles[i]
        received_utc = received[i]
        prior = [(b, bt) for b, bt in seen if bt < received_utc]
        win = [(b, bt) for b, bt in prior if received_utc - bt <= WINDOW
               and a.entity_id is not None and b.entity_id == a.entity_id
               and b.event_type == a.event_type]
        # Keep the caller's Article objects intact for the similarity callback.
        sims = [(b, bt, float(similarity(a, b))) for b, bt in win]
        similar = [(b, bt, s) for b, bt, s in sims if s >= SIM_THRESHOLD]
        max_sim = max((s for _, _, s in sims), default=0.0)
        if similar:
            last = max(bt for _, bt, _ in similar)
            hours = (received_utc - last).total_seconds() / 3600
        else:
            hours = WINDOW.total_seconds() / 3600 * 7  # none: cap at a week
        n_sim = len(similar)
        ent7 = sum(1 for b, bt in prior if b.entity_id == a.entity_id and a.entity_id is not None
                   and received_utc - bt <= ENTITY_WINDOW)
        et24 = sum(1 for b, bt in prior if a.entity_id is not None and b.entity_id == a.entity_id
                   and b.event_type == a.event_type and received_utc - bt <= WINDOW)
        hour = received_utc.hour + received_utc.minute / 60
        row = {
            "intercept": 1.0,
            "max_sim_24h": max_sim,
            "n_sim_24h_log": math.log1p(n_sim),
            "hours_since_sim_log": math.log1p(hours),
            "n_sources_sim_24h_log": math.log1p(len({b.source_id for b, _, _ in similar})),
            "cluster_decay": 0.5 ** n_sim,
            "entity_count_7d_log": math.log1p(ent7),
            "entity_type_count_24h_log": math.log1p(et24),
            "tier1": float(a.source_tier == 1),
            "tier3": float(a.source_tier == 3),
            "hour_sin": math.sin(2 * math.pi * hour / 24),
            "hour_cos": math.cos(2 * math.pi * hour / 24),
            "weekend": float(received_utc.weekday() >= 5),
        }
        for t in _TYPES:
            row[f"type_{t.value}"] = float(a.event_type is t)
        rows[i] = [row[f] for f in FEATURES]
        seen.append((a, received_utc))
    return rows


def fit_logistic(X: np.ndarray, y: np.ndarray, ridge: float = RIDGE, iters: int = 100) -> np.ndarray:
    """Ridge-penalised logistic regression by IRLS (intercept = column 0, not penalised)."""
    X = _numeric_array(X, "X", 2)
    y = _binary_labels(y)
    if X.shape[0] != len(y):
        raise NoveltyError("X and y differ in length")
    beta = np.zeros(X.shape[1])
    pen = np.full(X.shape[1], ridge)
    pen[0] = 0.0
    for _ in range(iters):
        p = predict_proba(X, beta)
        w = np.clip(p * (1 - p), 1e-9, None)
        grad = X.T @ (y - p) - pen * beta
        hess = (X * w[:, None]).T @ X + np.diag(pen) + 1e-9 * np.eye(X.shape[1])
        step = np.linalg.solve(hess, grad)
        beta = beta + step
        if np.max(np.abs(step)) < 1e-8:
            break
    return beta


def predict_proba(X: np.ndarray, beta: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(X @ beta, -35, 35)))


@dataclass(frozen=True)
class Report:
    n_train: int
    n_test: int
    cutoff: float
    accuracy: float
    majority_accuracy: float
    balanced_accuracy: float
    precision: float
    recall: float
    passes: bool                 # accuracy >= TARGET_ACCURACY (owner criterion)
    beats_majority: bool         # supplementary, reported
    coefficients: dict


def evaluate(y: np.ndarray, p: np.ndarray, cutoff: float = CUTOFF) -> dict:
    y = _binary_labels(y)
    p = _numeric_array(p, "p", 1)
    if len(y) != len(p):
        raise NoveltyError("y and p differ in length")
    if ((p < 0.0) | (p > 1.0)).any():
        raise NoveltyError("p must be in [0, 1]")
    cutoff = _probability_threshold(cutoff, "cutoff", endpoints=True)
    yhat = (p >= cutoff).astype(int)
    tp = int(((yhat == 1) & (y == 1)).sum()); tn = int(((yhat == 0) & (y == 0)).sum())
    fp = int(((yhat == 1) & (y == 0)).sum()); fn = int(((yhat == 0) & (y == 1)).sum())
    n = len(y)
    tpr = tp / (tp + fn) if tp + fn else float("nan")
    tnr = tn / (tn + fp) if tn + fp else float("nan")
    return {
        "accuracy": (tp + tn) / n if n else float("nan"),
        "majority_accuracy": max(y.mean(), 1 - y.mean()) if n else float("nan"),
        "balanced_accuracy": (tpr + tnr) / 2,
        "precision": tp / (tp + fp) if tp + fp else float("nan"),
        "recall": tpr,
    }


def time_split(received: Sequence[datetime], test_fraction: float = TEST_FRACTION) -> tuple[np.ndarray, np.ndarray]:
    test_fraction = _probability_threshold(test_fraction, "test_fraction", endpoints=False)
    received_utc = [_utc_received(value) for value in received]
    order = np.array(sorted(range(len(received_utc)), key=lambda i: received_utc[i]))
    cut = int(round(len(order) * (1 - test_fraction)))
    if cut < 1 or cut >= len(order):
        raise NoveltyError("not enough articles for a time split")
    if received_utc[order[cut - 1]] == received_utc[order[cut]]:
        raise NoveltyError("time split boundary must have distinct received_at values")
    return order[:cut], order[cut:]


def fit_and_test(articles: Sequence[Article], y: Sequence[int],
                 similarity: Callable[[Article, Article], float]) -> Report:
    """The pre-registered test: time-ordered split, fit on the past, score the future at 0.75."""
    y = _binary_labels(y)
    if len(articles) != len(y):
        raise NoveltyError("articles and labels differ in length")
    X = build_features(articles, similarity)
    train, test = time_split([a.received_at for a in articles])
    beta = fit_logistic(X[train], y[train])
    m = evaluate(y[test], predict_proba(X[test], beta))
    return Report(
        n_train=len(train), n_test=len(test), cutoff=CUTOFF,
        accuracy=m["accuracy"], majority_accuracy=m["majority_accuracy"],
        balanced_accuracy=m["balanced_accuracy"], precision=m["precision"], recall=m["recall"],
        passes=m["accuracy"] >= TARGET_ACCURACY,
        beats_majority=m["accuracy"] > m["majority_accuracy"],
        coefficients=dict(zip(FEATURES, (round(float(b), 6) for b in beta))),
    )
