"""Isotonic calibration maps (pipeline step 5, Notion DIDM 6.1: "isotonic/Platt per field").

One map per class: a non-decreasing step function from the raw probability of that class to the
observed frequency, fitted by pool-adjacent-violators on a calibration set. A multi-class map
applies each class's function and renormalises. Fitting uses only the items given, so the caller
decides the split; ``time_split`` gives the registered one (earlier 70% fits, later 30% tests,
by received_at, no shuffling: PREREG_V0 4.1).

A map has a version derived from its contents, which is what ``assemble_record`` takes as
``calibration_version`` (PREREG_V0 5.7: the calibration-map version travels with every record).

Standard library only; no network, no clock reads.
"""
from __future__ import annotations

import bisect
import hashlib
import json
from dataclasses import dataclass
from typing import Hashable, Mapping, Sequence

TEST_FRACTION = 0.30
MIN_ITEMS = 30               # a map fitted on fewer items is refused: it would mostly memorise them


class CalibrationError(ValueError):
    pass


@dataclass(frozen=True)
class Isotonic:
    """Right-continuous step function: value[i] applies from threshold[i] up to the next threshold."""
    thresholds: tuple[float, ...]
    values: tuple[float, ...]

    def __call__(self, p: float) -> float:
        if isinstance(p, bool) or not isinstance(p, (int, float)) or not 0.0 <= p <= 1.0:
            raise CalibrationError("probability must be a number in [0, 1]")
        i = bisect.bisect_right(self.thresholds, p) - 1
        return self.values[max(i, 0)]


def fit_isotonic(raw: Sequence[float], hit: Sequence[bool]) -> Isotonic:
    """Pool-adjacent-violators fit of P(hit) as a non-decreasing function of the raw probability."""
    if len(raw) != len(hit):
        raise CalibrationError("raw probabilities and outcomes differ in length")
    if len(raw) < MIN_ITEMS:
        raise CalibrationError(f"a calibration map needs at least {MIN_ITEMS} items")
    for p in raw:
        if isinstance(p, bool) or not isinstance(p, (int, float)) or not 0.0 <= p <= 1.0:
            raise CalibrationError("raw probabilities must be numbers in [0, 1]")
    # 1. one group per distinct raw value: [raw value, sum of outcomes, count]
    groups: list[list[float]] = []
    for p, y in sorted(zip((float(p) for p in raw), (1.0 if h else 0.0 for h in hit))):
        if groups and groups[-1][0] == p:
            groups[-1][1] += y
            groups[-1][2] += 1
        else:
            groups.append([p, y, 1.0])
    # 2. pool adjacent groups whose rates are not increasing (complete groups only)
    blocks: list[list[float]] = []
    for group in groups:
        blocks.append(list(group))
        while len(blocks) > 1 and blocks[-2][1] / blocks[-2][2] >= blocks[-1][1] / blocks[-1][2]:
            _, y2, n2 = blocks.pop()
            blocks[-1][1] += y2
            blocks[-1][2] += n2
    return Isotonic(tuple(b[0] for b in blocks), tuple(b[1] / b[2] for b in blocks))


@dataclass(frozen=True)
class CalibrationMap:
    field: str                                   # "direction" or "event_type"
    labels: tuple[str, ...]
    maps: tuple[Isotonic, ...]                   # one per label, in label order
    n_fit: int

    @property
    def version(self) -> str:
        payload = {"field": self.field, "labels": list(self.labels), "n_fit": self.n_fit,
                   "maps": [[list(m.thresholds), list(m.values)] for m in self.maps]}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        return f"iso-{self.field}-{digest[:16]}"

    def apply(self, probs: Mapping[Hashable, float]) -> dict[str, float]:
        if set(probs) != set(self.labels):
            raise CalibrationError("probabilities must have exactly the map's labels as keys")
        out = {k: m(probs[k]) for k, m in zip(self.labels, self.maps)}
        total = sum(out.values())
        if total <= 0.0:
            # every class mapped to 0 (none of these raw values ever came true in the fit set):
            # fall back to the raw probabilities rather than inventing a distribution
            return {k: float(probs[k]) for k in self.labels}
        return {k: v / total for k, v in out.items()}

    def apply_direction(self, probs: Sequence[float]) -> tuple[float, float, float]:
        """For assemble_record(calibrate_direction=...): [P(+1), P(-1), P(0)] in, same order out."""
        if self.labels != ("+1", "-1", "0") or len(probs) != 3:
            raise CalibrationError("apply_direction needs a direction map and three probabilities")
        out = self.apply(dict(zip(self.labels, probs)))
        return (out["+1"], out["-1"], out["0"])


def fit_map(field: str, labels: Sequence[str], probs: Sequence[Mapping[Hashable, float]],
            outcomes: Sequence[Hashable]) -> CalibrationMap:
    labels = tuple(labels)
    if len(probs) != len(outcomes):
        raise CalibrationError("probabilities and outcomes differ in length")
    if len(set(labels)) != len(labels) or not labels:
        raise CalibrationError("labels must be distinct and non-empty")
    for row in probs:
        if set(row) != set(labels):
            raise CalibrationError("each probability row must have exactly the label list as keys")
    if any(o not in set(labels) for o in outcomes):
        raise CalibrationError("an outcome is outside the label list")
    maps = tuple(fit_isotonic([row[k] for row in probs], [o == k for o in outcomes]) for k in labels)
    return CalibrationMap(field, labels, maps, len(outcomes))


def time_split(received_at: Sequence, test_fraction: float = TEST_FRACTION) -> tuple[list[int], list[int]]:
    """Indices of the earlier (fit) and later (test) items by received_at; ties stay on one side."""
    n = len(received_at)
    if n < 2 or not 0.0 < test_fraction < 1.0:
        raise CalibrationError("need at least two items and a test fraction in (0, 1)")
    order = sorted(range(n), key=lambda i: (received_at[i], i))
    cut = n - max(1, int(round(n * test_fraction)))
    while 0 < cut < n and received_at[order[cut - 1]] == received_at[order[cut]]:
        cut -= 1                                  # never split one timestamp across fit and test
    if cut <= 0:
        raise CalibrationError("the split leaves no earlier items (too many equal timestamps)")
    return order[:cut], order[cut:]
