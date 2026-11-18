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
from datetime import datetime, timedelta
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


def build_features(articles: Sequence[Article],
                   similarity: Callable[[Article, Article], float]) -> np.ndarray:
    """One feature row per article, in the input order, from strictly earlier articles only."""
    for a in articles:
        if a.received_at.tzinfo is None:
            raise NoveltyError(f"{a.article_id}: received_at must be timezone-aware")
    order = sorted(range(len(articles)), key=lambda i: (articles[i].received_at, articles[i].article_id))
    rows = np.zeros((len(articles), len(FEATURES)))
    seen: list[Article] = []
    for i in order:
        a = articles[i]
        prior = [b for b in seen if b.received_at < a.received_at]
        win = [b for b in prior if a.received_at - b.received_at <= WINDOW
               and (b.entity_id == a.entity_id or b.event_type == a.event_type)]
        sims = [(b, float(similarity(a, b))) for b in win]
        similar = [(b, s) for b, s in sims if s >= SIM_THRESHOLD]
        max_sim = max((s for _, s in sims), default=0.0)
        if similar:
            last = max(b.received_at for b, _ in similar)
            hours = (a.received_at - last).total_seconds() / 3600
        else:
            hours = WINDOW.total_seconds() / 3600 * 7  # none: cap at a week
        n_sim = len(similar)
        ent7 = sum(1 for b in prior if b.entity_id == a.entity_id and a.entity_id is not None
                   and a.received_at - b.received_at <= ENTITY_WINDOW)
        et24 = sum(1 for b in prior if b.entity_id == a.entity_id and b.event_type == a.event_type
                   and a.received_at - b.received_at <= WINDOW)
        hour = a.received_at.hour + a.received_at.minute / 60
        row = {
            "intercept": 1.0,
            "max_sim_24h": max_sim,
            "n_sim_24h_log": math.log1p(n_sim),
            "hours_since_sim_log": math.log1p(hours),
            "n_sources_sim_24h_log": math.log1p(len({b.source_id for b, _ in similar})),
            "cluster_decay": 0.5 ** n_sim,
            "entity_count_7d_log": math.log1p(ent7),
            "entity_type_count_24h_log": math.log1p(et24),
            "tier1": float(a.source_tier == 1),
            "tier3": float(a.source_tier == 3),
            "hour_sin": math.sin(2 * math.pi * hour / 24),
            "hour_cos": math.cos(2 * math.pi * hour / 24),
            "weekend": float(a.received_at.weekday() >= 5),
        }
        for t in _TYPES:
            row[f"type_{t.value}"] = float(a.event_type is t)
        rows[i] = [row[f] for f in FEATURES]
        seen.append(a)
    return rows


def fit_logistic(X: np.ndarray, y: np.ndarray, ridge: float = RIDGE, iters: int = 100) -> np.ndarray:
    """Ridge-penalised logistic regression by IRLS (intercept = column 0, not penalised)."""
    y = np.asarray(y, dtype=float)
    if set(np.unique(y)) - {0.0, 1.0}:
        raise NoveltyError("y must be 0/1")
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
    y = np.asarray(y, dtype=int)
    yhat = (np.asarray(p) >= cutoff).astype(int)
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
    order = np.array(sorted(range(len(received)), key=lambda i: received[i]))
    cut = int(round(len(order) * (1 - test_fraction)))
    if cut < 1 or cut >= len(order):
        raise NoveltyError("not enough articles for a time split")
    return order[:cut], order[cut:]


def fit_and_test(articles: Sequence[Article], y: Sequence[int],
                 similarity: Callable[[Article, Article], float]) -> Report:
    """The pre-registered test: time-ordered split, fit on the past, score the future at 0.75."""
    if len(articles) != len(y):
        raise NoveltyError("articles and labels differ in length")
    X = build_features(articles, similarity)
    y = np.asarray(y, dtype=float)
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
