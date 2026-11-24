"""DIDM Stage 1 (measurement validity): the registered pass rules as code (PREREG_V0 3, Stage 1 row).

    Go     : human kappa >= 0.6, event-type macro-F1 >= 0.75, linking precision >= 0.95 and
             recall >= 0.80, ECE <= 0.05 after calibration, Brier skill > 0, LLM beats the
             Loughran-McDonald dictionary and FinBERT
    Revise : kappa 0.4-0.6 (lower K), or any other Go condition missed
    No-Go  : kappa < 0.4, or LLM <= FinBERT

How the row is read here (decided before any gold set exists; interpretation by DIDM_DEV):

* kappa is Cohen's kappa of the two annotators on ``event_type`` (the Revise rule "lower K" is
  about event types). Kappa on direction, is_subject and is_new_event is reported, not gated.
* ECE and Brier skill are measured on the later 30% of the gold set by received_at, after an
  isotonic map fitted on the earlier 70%; both the direction and the event-type probabilities
  must pass. The Brier reference is the class frequencies of the earlier 70%.
* "LLM beats LM and FinBERT" is compared on direction macro-F1 over the whole gold set, the one
  judgement all three scorers make. Strictly greater passes; LLM <= FinBERT is No-Go.
* A gold item a scorer returned no valid judgement for counts as a wrong answer for that scorer.
* Every scorer must be eligible for every gold article under the cutoff rule
  (core/didm/llm/cutoffs.py); otherwise the run is not a Stage 1 result at all (verdict INVALID).
* The gold set must have 1,000-1,500 articles covering EN and KR; otherwise INVALID.

Nothing here calls a model or reads a file, a clock or the network: the caller supplies labels and
judgements. No gold set exists yet, so Stage 1 has not been run.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from core.didm.calibration import isotonic
from core.didm.eval import metrics
from core.didm.eval.sampling import MARKETS, TARGET_MAX, TARGET_MIN
from core.didm.llm import cutoffs
from core.didm.llm.judgement import Judgement
from core.didm.llm.schema import EventType, GoldLabel

# --- registered thresholds (PREREG_V0 3; not tunable) ---
KAPPA_GO, KAPPA_NO_GO = 0.6, 0.4
MACRO_F1_MIN = 0.75
LINK_PRECISION_MIN, LINK_RECALL_MIN = 0.95, 0.80
ECE_MAX = 0.05
BRIER_SKILL_MIN = 0.0            # strictly greater

TYPE_LABELS = tuple(e.value for e in EventType)
DIRECTION_LABELS = ("+1", "-1", "0")       # the order of direction_probs
MISSING = "__no_valid_judgement__"
LM_KEY, FINBERT_KEY = "loughran-mcdonald", "ProsusAI/finbert"

Key = tuple[str, str | None]               # (article_id, entity_id)


class Stage1Error(ValueError):
    pass


@dataclass(frozen=True)
class ScorerRun:
    model_version: str
    judgements: Mapping[Key, Judgement]


@dataclass(frozen=True)
class Criterion:
    name: str
    value: float | None
    rule: str
    passed: bool


@dataclass(frozen=True)
class Stage1Report:
    verdict: str                              # GO | REVISE | NO-GO | INVALID
    criteria: tuple[Criterion, ...]
    notes: tuple[str, ...]
    info: dict = field(default_factory=dict)  # reported, not gated

    @property
    def line(self) -> str:
        return f"STAGE1: {self.verdict}"


def _key(label: GoldLabel) -> Key:
    return (label.article_id, label.entity_id)


def _index(labels: list[GoldLabel], what: str) -> dict[Key, GoldLabel]:
    out: dict[Key, GoldLabel] = {}
    for label in labels:
        if not isinstance(label, GoldLabel):
            raise Stage1Error(f"{what} must be validated GoldLabel objects")
        if _key(label) in out:
            raise Stage1Error(f"{what}: an article and target appears twice")
        out[_key(label)] = label
    return out


def _direction_row(j: Judgement) -> dict[str, float]:
    return dict(zip(DIRECTION_LABELS, j.direction_probs))


def _direction_pick(j: Judgement | None) -> str:
    if j is None:
        return MISSING
    row = _direction_row(j)
    return max(DIRECTION_LABELS, key=lambda k: (row[k], -DIRECTION_LABELS.index(k)))


def _macro_f1_with_missing(gold: list[str], pred: list[str], labels: tuple[str, ...]) -> float:
    return metrics.macro_f1(gold, pred, (*labels, MISSING))


def _calibrated(field_name: str, labels: tuple[str, ...], rows: list[dict], outcomes: list[str],
                fit: list[int], test: list[int]) -> tuple[float, float, str]:
    """(ECE, Brier skill, map version) on the test items after an isotonic map fitted on the fit items."""
    cal = isotonic.fit_map(field_name, labels, [rows[i] for i in fit], [outcomes[i] for i in fit])
    test_rows = [cal.apply(rows[i]) for i in test]
    test_out = [outcomes[i] for i in test]
    reference = metrics.base_rates([outcomes[i] for i in fit], labels)
    return (metrics.top_label_ece(test_rows, test_out, labels),
            metrics.brier_skill(test_rows, test_out, labels, reference), cal.version)


def evaluate(*, annotator_a: list[GoldLabel], annotator_b: list[GoldLabel], gold: list[GoldLabel],
             llm: ScorerRun, baselines: Mapping[str, ScorerRun], predicted_links: set[tuple[str, str]],
             registry: cutoffs.Registry = cutoffs.REGISTRY, bootstrap_seed: int = 0,
             bootstrap_resamples: int = 2000) -> Stage1Report:
    a, b, g = _index(annotator_a, "annotator A"), _index(annotator_b, "annotator B"), _index(gold, "gold")
    notes: list[str] = []
    invalid: list[str] = []

    if set(a) != set(b):
        raise Stage1Error("the two annotators must label the same articles and targets")
    if set(g) != set(a):
        raise Stage1Error("the adjudicated gold set must cover exactly the double-labelled items")
    if LM_KEY not in baselines or FINBERT_KEY not in baselines:
        raise Stage1Error(f"baselines must include {LM_KEY} and {FINBERT_KEY}")

    keys = sorted(g, key=lambda k: (g[k].received_at, k[0], k[1] or ""))
    articles = {k[0] for k in keys}
    if not TARGET_MIN <= len(articles) <= TARGET_MAX:
        invalid.append(f"gold set has {len(articles)} articles; the registered size is {TARGET_MIN}-{TARGET_MAX}")
    if {g[k].market for k in keys} != set(MARKETS):
        invalid.append("gold set must cover both EN and KR")

    runs = {"llm": llm, **{f"baseline:{name}": run for name, run in baselines.items()}}
    for name, run in runs.items():
        stray = set(run.judgements) - set(g)
        if stray:
            raise Stage1Error(f"{name}: a judgement is for an item outside the gold set")
        bad = sum(not registry.eligibility(run.model_version, published_at=g[k].published_at,
                                           received_at=g[k].received_at).eligible for k in keys)
        if bad:
            invalid.append(f"{name} ({run.model_version}): {bad} gold items fail the training-cutoff rule")

    criteria: list[Criterion] = []
    info: dict = {"n_items": len(keys), "n_articles": len(articles)}

    # 1. human agreement
    kappa = metrics.cohen_kappa([a[k].event_type.value for k in keys], [b[k].event_type.value for k in keys])
    criteria.append(Criterion("human kappa (event type)", kappa, f">= {KAPPA_GO}", kappa >= KAPPA_GO))
    for name, pick in (("direction", lambda x: x.direction.value), ("is_subject", lambda x: x.is_subject),
                       ("is_new_event", lambda x: x.is_new_event)):
        try:
            info[f"kappa_{name}"] = metrics.cohen_kappa([pick(a[k]) for k in keys], [pick(b[k]) for k in keys])
        except metrics.MetricError:
            info[f"kappa_{name}"] = None

    # 2. event-type macro-F1 (a missing judgement is a wrong answer)
    gold_type = [g[k].event_type.value for k in keys]
    llm_type = [llm.judgements[k].event_type.value if k in llm.judgements else MISSING for k in keys]
    f1 = _macro_f1_with_missing(gold_type, llm_type, TYPE_LABELS)
    criteria.append(Criterion("event-type macro-F1", f1, f">= {MACRO_F1_MIN}", f1 >= MACRO_F1_MIN))
    info["llm_coverage"] = sum(k in llm.judgements for k in keys) / len(keys)

    # 3. entity linking
    gold_links = {(k[0], k[1]) for k in keys if k[1] is not None and g[k].is_subject}
    link = metrics.linking_scores(gold_links, set(predicted_links))
    criteria.append(Criterion("linking precision", link.precision, f">= {LINK_PRECISION_MIN}",
                              link.precision >= LINK_PRECISION_MIN))
    criteria.append(Criterion("linking recall", link.recall, f">= {LINK_RECALL_MIN}", link.recall >= LINK_RECALL_MIN))

    # 4. calibration on the later 30%, map fitted on the earlier 70% (judged items only)
    judged = [k for k in keys if k in llm.judgements]
    if len(judged) < 2 * isotonic.MIN_ITEMS:
        raise Stage1Error("too few judged items to fit and test a calibration map")
    fit, test = isotonic.time_split([g[k].received_at for k in judged])
    for field_name, labels, rows, outcomes in (
            ("direction", DIRECTION_LABELS, [_direction_row(llm.judgements[k]) for k in judged],
             [g[k].direction.value for k in judged]),
            ("event_type", TYPE_LABELS, [dict(llm.judgements[k].event_type_probs) for k in judged],
             [g[k].event_type.value for k in judged])):
        ece, skill, version = _calibrated(field_name, labels, rows, outcomes, fit, test)
        criteria.append(Criterion(f"ECE after calibration ({field_name})", ece, f"<= {ECE_MAX}", ece <= ECE_MAX))
        criteria.append(Criterion(f"Brier skill ({field_name})", skill, f"> {BRIER_SKILL_MIN}",
                                  skill > BRIER_SKILL_MIN))
        info[f"calibration_version_{field_name}"] = version
    info["n_calibration_fit"], info["n_calibration_test"] = len(fit), len(test)

    # 5. LLM against the baselines, on direction
    gold_dir = [g[k].direction.value for k in keys]
    picks = {name: [_direction_pick(run.judgements.get(k)) for k in keys] for name, run in runs.items()}
    score = {name: _macro_f1_with_missing(gold_dir, p, DIRECTION_LABELS) for name, p in picks.items()}
    info["direction_macro_f1"] = dict(score)
    llm_le_finbert = score["llm"] <= score[f"baseline:{FINBERT_KEY}"]
    for name in (LM_KEY, FINBERT_KEY):
        base = f"baseline:{name}"
        criteria.append(Criterion(f"LLM direction macro-F1 minus {name}", score["llm"] - score[base], "> 0",
                                  score["llm"] > score[base]))
        diff = metrics.paired_bootstrap(
            gold_dir, picks["llm"], picks[base],
            lambda gg, pp: _macro_f1_with_missing(list(gg), list(pp), DIRECTION_LABELS), seed=bootstrap_seed,
            resamples=bootstrap_resamples)
        info[f"bootstrap90_vs_{name}"] = (diff.lower, diff.upper)

    # verdict
    if invalid:
        return Stage1Report("INVALID", tuple(criteria), tuple(invalid), info)
    if kappa < KAPPA_NO_GO:
        notes.append(f"human kappa below {KAPPA_NO_GO}")
    if llm_le_finbert:
        notes.append("LLM does not beat FinBERT on direction macro-F1")
    if notes:
        return Stage1Report("NO-GO", tuple(criteria), tuple(notes), info)
    failed = [c.name for c in criteria if not c.passed]
    if not failed:
        return Stage1Report("GO", tuple(criteria), (), info)
    if kappa < KAPPA_GO:
        notes.append(f"human kappa between {KAPPA_NO_GO} and {KAPPA_GO}: lower the number of event types")
    notes += [f"not met: {name}" for name in failed]
    return Stage1Report("REVISE", tuple(criteria), tuple(notes), info)


def render(report: Stage1Report) -> str:
    lines = ["| criterion | value | rule | result |", "|---|---|---|---|"]
    for c in report.criteria:
        value = "n/a" if c.value is None else f"{c.value:.4f}"
        lines.append(f"| {c.name} | {value} | {c.rule} | {'pass' if c.passed else 'FAIL'} |")
    lines += ["", *[f"- {note}" for note in report.notes], "", report.line]
    return "\n".join(lines) + "\n"
