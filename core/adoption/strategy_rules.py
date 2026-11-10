"""Strategy adoption checks S-2, S-3, S-4 and S-7 (roadmap ⑨-4/2/a, the first unit of core/adoption, ruling M-21).

Source of every rule: `docs/nautilus_bridge/MODEL_ADOPTION_CRITERIA_DRAFT_2026-11-04.md` ("the criteria"),
owner-approved on 2026-11-10 and merged to main in PR #92, with the owner's answers M-1 to M-22 in its section 9
and in `docs/nautilus_bridge/OWNER_RULINGS_LOG.md`. Sections used: 4.0 (common rules), 4.2.2 (S-2, S-3, S-4, S-7
and add versus replace), 6.2 (borderline zones), 6.4 (N12: a NaN DSR does not meet S-2), 3.3 (the 2027-01-01
locked holdout) and 8.2 (the L1 note).

What this module does. It computes, on caller-supplied daily OOS P&L arrays, what the gate does not compute:
the deflated Sharpe ratio at the grid size G and at the family N_raw (S-2), the Ledoit-Wolf studentized paired
delta-Sharpe test against the incumbent (S-3) and against every registered baseline (S-4), the MDE80 power line
(S-7), the borderline zones and the holdout guard. Every number comes from an existing function:
`validate.deflated_sharpe`, `validate._col_sharpe` (the gate's own dispersion term), `gate_stats.pw_block_psi`,
`gate_stats.lw_studentized_boot`, `gate_stats.p_numeric` and `gate_stats.lw_hac_se`. Thresholds that exist are
read from `validate.GATE` and `gate_stats` and never redefined; the only new constants are the ruled alpha 0.10
(M-2), the borderline bounds 0.20 and 0.90 (M-11), the last session 2026-12-31 (M-14), the L1 note (M-20) and the
cash-baseline marker (criteria 2.3, M-4).

What it does not do. It assigns no outcome (ADOPT, KEEP, REVISE, REJECT, INSUFFICIENT_DATA): the outcome
assembly waits for owner questions (the gate passing at G with a second DSR below 0.90 is mapped by neither KEEP
nor REJECT in criteria 6.1, and whether S-7 converts S-3 into INSUFFICIENT_DATA was not answered by M-6). It never
re-decides the gate (S-1 is the caller's precondition), reads no file, ledger, clock, environment or network, and
imports only `core.quant.validate` and `core.quant.gate_stats` (never `core.quant.strategies`, `history` or
`config`). S-5 and S-6 (tf_gov SPA and break-even), the baselines' own P&L and the forecast, risk and data rules
are later units.

Provisional (M-3). The second DSR is labelled provisional until the ⑨-3c report and ⑨-3d. The meaning of the
ledger N_raw was not decided by the owner's answer of 2026-11-10; owner ruling 7 of 2026-11-11 decided it
(roadmap ⑨-4/2/b): R-FAM, the R3 run-registry count, is the N_raw reading of record (`N_RAW_READING_OF_RECORD`).
Until the R3 recorder exists no count comes from the registry itself, so N_raw stays a caller input under one or
both named readings (`N_RAW_READINGS`), both readings are still displayed (L-FAM for comparison) and the second
DSR stays provisional. Naming the reading of record changes no threshold, status or gate rule: every line is
computed and classified as before.

The DSR at N = G is the gate's own DSR and always uses the gate's dispersion term (`sr_sd_grid`); criteria 6.2
keys the second DSR's borderline on it. The dispersion term paired with N_raw is a criterion reserved for ⑨-3d
(R3 design 4.4; 10.2 B Q1), so it is a separate, explicit, labelled caller input used only for the N_raw lines;
N_raw below G is printed, not refused (R3 design 10.2 B Q4). The L1 note (M-20) is printed on the collected
`strategy_lines` result.
"""
from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from types import MappingProxyType
from typing import Optional, Union

import numpy as np

from core.quant import gate_stats as GS
from core.quant import validate as V

UNIT = "⑨-4/2/a"
CRITERIA_DOC = "docs/nautilus_bridge/MODEL_ADOPTION_CRITERIA_DRAFT_2026-11-04.md"
RULINGS_LOG = "docs/nautilus_bridge/OWNER_RULINGS_LOG.md"

ALPHA_ONE_SIDED = 0.10                    # M-2: every adoption comparison is one-sided at 0.10
BORDERLINE_P_MAX = 0.20                   # M-11, criteria 6.2: outside-gate one-sided p in (0.10, 0.20]
DSR_BORDERLINE_MIN = 0.90                 # M-11, criteria 6.2: second DSR in [0.90, dsr_min) while the gate's passes
HOLDOUT_LAST_SESSION = date(2026, 12, 31)   # M-14, criteria 3.3 (rule ⑧-2): a sample may end on this day at most
L1_NOTE = "L1 미적용(브리지 미지원)"          # M-20, criteria 8.2: printed on the collected strategy_lines result
KINDS = ("replace", "add")                # M-19, criteria 3.2 item 12
CASH_BASELINE = "CASH_BASELINE"          # M-4, criteria 2.3: a declared cash baseline (pairs E8, S6)

N_RAW_READINGS = MappingProxyType({
    "L-FAM": "family ledger row count (gate_ledger.FamilyLedger.n_raw, the number of ledger rows), "
             "read on the owner PC",
    "R-FAM": "R3 registry literal family-wide count (R3 design 3.13: |K| + |L minus cfg(K)|)",
})
# Owner ruling 7 of 2026-11-11 (M-3, roadmap ⑨-4/2/b): the R3 run-registry count is the N_raw reading of record.
# Until the R3 recorder exists both readings are still shown and the second DSR stays provisional.
N_RAW_READING_OF_RECORD = "R-FAM"

DSR_STATUSES = ("pass", "borderline", "below", "nan", "not_supplied")
COMPARISON_STATUSES = ("win", "borderline", "not_won", "not_run", "replaced")   # "replaced": cash, S-4 only

_PROVISIONAL_NOTE = ("provisional (M-3): the second DSR stands until the ⑨-3c report and is reviewed at ⑨-3d; "
                     f"{N_RAW_READING_OF_RECORD}, the R3 run-registry count, is the N_raw reading of record "
                     "(owner ruling 7 of 2026-11-11); until the R3 recorder exists both readings are shown")
_OF_RECORD_ROLE = "reading of record (owner ruling 7, 2026-11-11)"
_COMPARISON_ROLE = "shown for comparison"
_RECORD_MISSING = ("the reading of record was not supplied, so this result has no second DSR of record and "
                   "stays provisional")
_PAIRING_NOTE = ("the DSR at N = G uses the gate's own dispersion term; the term paired with N_raw is a criterion "
                 "reserved for ⑨-3d (R3 design 4.4, 10.2 B Q1), so the N_raw lines use the caller's labelled term")
_BELOW_GRID_NOTE = ("N_raw below G is printed only: whether a ledger-based N may fall below G is R3 design "
                    "10.2 B Q4, reserved for ⑨-3d")
_NO_OUTCOME_NOTE = ("no outcome label: the outcome assembly (criteria 6.1) waits for the owner's answers on a "
                    "second DSR below 0.90 and on S-7")
_CASH_NOTE = ("criteria 2.3 (M-4): the cash baseline is replaced by the gate's check that the Sharpe interval "
              "excludes 0 (S-1, the caller's precondition); no LW test is run")
_CASH_HINT = "; a cash baseline is declared with CASH_BASELINE (criteria 2.3), not as a constant series"
_NUMERIC_KINDS = "iuf"                     # integer, unsigned or float dtypes; strings, bools and objects are refused
_ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


class AdoptionInputError(ValueError):
    """A caller input outside the rules: misaligned sessions, a bad count, a missing registration field."""


# --------------------------------------------------------------------------- #
# Input checks
# --------------------------------------------------------------------------- #
def _count(value, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
        raise AdoptionInputError(f"{name} must be an integer count, got {type(value).__name__}")
    if int(value) < 1:
        raise AdoptionInputError(f"{name} must be >= 1, got {int(value)}")
    return int(value)


def _real(value, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, np.integer, np.floating)):
        raise AdoptionInputError(f"{name} must be a real number, got {type(value).__name__}")
    out = float(value)
    if not math.isfinite(out):
        raise AdoptionInputError(f"{name} must be finite, got {out}")
    return out


def _label(value, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AdoptionInputError(f"{name} must be a non-empty label")
    return value.strip()


def _numeric(values, name: str) -> np.ndarray:
    """A float copy of an integer or float array; numeric strings, booleans and object arrays are refused."""
    try:
        raw = np.asarray(values)
    except (TypeError, ValueError):
        raise AdoptionInputError(f"{name} must be numeric daily P&L") from None
    if raw.dtype.kind not in _NUMERIC_KINDS:
        raise AdoptionInputError(f"{name} must be numeric daily P&L (integer or float), got dtype {raw.dtype}")
    return raw.astype(float)


def _series(values, name: str) -> np.ndarray:
    arr = _numeric(values, name)
    if arr.ndim != 1:
        raise AdoptionInputError(f"{name} must be one-dimensional daily P&L, got shape {arr.shape}")
    if not np.all(np.isfinite(arr)):
        raise AdoptionInputError(f"{name} has non-finite values")
    return arr.copy()


def _session(value, name: str) -> date:
    if isinstance(value, datetime):
        raise AdoptionInputError(f"{name}: a session is a calendar date, not a datetime")
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            if not _ISO_DATE.fullmatch(value):        # the same YYYY-MM-DD form on every Python version
                raise ValueError(value)
            return date.fromisoformat(value)
        except ValueError:
            raise AdoptionInputError(f"{name}: {value!r} is not an ISO date (YYYY-MM-DD)") from None
    raise AdoptionInputError(f"{name}: a session must be a date or an ISO date string, got {type(value).__name__}")


def _sessions(values: Sequence, name: str) -> tuple:
    if isinstance(values, (str, bytes)):
        raise AdoptionInputError(f"{name} must be a sequence of sessions")
    out = tuple(_session(v, name) for v in values)
    for i in range(1, len(out)):
        if out[i] <= out[i - 1]:
            raise AdoptionInputError(f"{name} is not strictly increasing at index {i}: {out[i - 1]} then {out[i]}")
    return out


def _aligned(x_a, x_b, dates_a, dates_b, name_a: str, name_b: str):
    """Both books on the same OOS sessions (S-3: '같은 OOS 세션'); refused otherwise, never trimmed."""
    a, b = _series(x_a, name_a), _series(x_b, name_b)
    da, db = _sessions(dates_a, f"{name_a} sessions"), _sessions(dates_b, f"{name_b} sessions")
    if a.size != len(da):
        raise AdoptionInputError(f"{name_a}: {a.size} values but {len(da)} sessions")
    if b.size != len(db):
        raise AdoptionInputError(f"{name_b}: {b.size} values but {len(db)} sessions")
    if len(da) != len(db):
        raise AdoptionInputError(f"unequal sessions: {name_a} has {len(da)}, {name_b} has {len(db)}")
    for i, (sa, sb) in enumerate(zip(da, db)):
        if sa != sb:
            raise AdoptionInputError(f"misaligned sessions at index {i}: {name_a} {sa}, {name_b} {sb}")
    if not da:
        raise AdoptionInputError("no sessions to compare")
    return a, b, da


def _fmt(x) -> str:
    return "nan" if x is None or (isinstance(x, float) and not math.isfinite(x)) else f"{x:.4f}"


# --------------------------------------------------------------------------- #
# Holdout guard (criteria 3.3 and 4.0 rule 6; M-14)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class SampleEnd:
    last_session: date
    holdout_last_session: date
    holdout_touched: bool
    adopt_allowed: bool
    rule: str = "4.0 rule 6, M-14"

    def line(self) -> str:
        if self.holdout_touched:
            return (f"holdout (M-14): sample ends {self.last_session} after {self.holdout_last_session}: "
                    "HOLDOUT_TOUCHED, this run cannot be adopted")
        return f"holdout (M-14): sample ends {self.last_session}, on or before {self.holdout_last_session}"


def check_sample_end(last_session) -> SampleEnd:
    """Criteria 4.0 rule 6 and 3.3, ruling M-14 (가): before decision 14 the evaluation sample ends on or before
    2026-12-31, and a HOLDOUT_TOUCHED run (a sample ending on or after 2027-01-01, R3 design 4.2 row 16) cannot be
    adopted. `last_session` is a `datetime.date` or an ISO date string; a `datetime` is refused."""
    last = _session(last_session, "last_session")
    touched = last > HOLDOUT_LAST_SESSION
    return SampleEnd(last_session=last, holdout_last_session=HOLDOUT_LAST_SESSION, holdout_touched=touched,
                     adopt_allowed=not touched)


# --------------------------------------------------------------------------- #
# S-2: DSR at G and at N_raw (M-3, provisional)
# --------------------------------------------------------------------------- #
def classify_dsr(value: float, *, grid_status: Optional[str] = None) -> str:
    """S-2 line status (criteria 4.2.2 S-2, 6.2, 6.4; rulings M-3, M-11). With `grid_status=None` this is the
    DSR at N = G: "pass" at `GATE['dsr_min']` or above, else "below" (gate territory, the gate decides). For a
    DSR at N_raw, pass the grid line's status: "borderline" is [0.90, dsr_min) only while the grid DSR passes
    (6.2); a NaN DSR is "nan" and does not meet S-2 (6.4, N12)."""
    v = float(value)
    if not math.isfinite(v):
        return "nan"
    if v >= V.GATE["dsr_min"]:
        return "pass"
    if grid_status == "pass" and v >= DSR_BORDERLINE_MIN:
        return "borderline"
    return "below"


def gate_sr_sd_daily(full_pnl) -> float:
    """S-2 helper (criteria 4.2.2 S-2, M-3): the gate's own trial-dispersion term, the population SD of the
    full-sample per-period Sharpe ratios of the T x G grid columns, formed exactly as `validate.score_strategy`
    forms it (`validate.py:503-506`), with the same `validate._col_sharpe` (validate.py is a frozen harness source).
    This is the term `dsr_two_n` needs as `sr_sd_grid` for the DSR at N = G.

    The value is the gate's, not a repaired one. A column that is constant up to floating noise and not zero (a
    configuration that stays in cash and earns the Lab's cash rate) has a sample SD at floating-noise level, so its
    Sharpe and the gate's term are enormous (about 1e13 to 1e14 in a T 1400 synthetic probe); an exactly zero
    column gives Sharpe 0. The public `validate.sharpe` computes that noise differently, which is why it is not
    used here. Pairing this term with N_raw is one reading only (reserved for ⑨-3d)."""
    M = _numeric(full_pnl, "full_pnl")
    if M.ndim != 2 or M.shape[0] < 2 or M.shape[1] < 1:
        raise AdoptionInputError(f"full_pnl must be a T x G matrix with T >= 2, got shape {M.shape}")
    if not np.all(np.isfinite(M)):
        raise AdoptionInputError("full_pnl has non-finite values")
    full_sr = V._col_sharpe(M) / math.sqrt(V.TRADING_DAYS)
    return float(np.nanstd(full_sr)) if full_sr.size > 1 else 0.0


@dataclass(frozen=True)
class RawReading:
    reading: str              # a key of N_RAW_READINGS
    meaning: str
    n_raw: Optional[int]      # None: the caller did not supply this reading
    dsr: float
    status: str               # pass / borderline / below / nan / not_supplied
    below_grid: bool          # N_raw < G, printed only
    of_record: bool           # True for N_RAW_READING_OF_RECORD (ruling 7); the other reading is for comparison

    def role(self) -> str:
        return _OF_RECORD_ROLE if self.of_record else _COMPARISON_ROLE


@dataclass(frozen=True)
class DsrTwoN:
    n_grid: int
    dsr_grid: float
    status_grid: str
    readings: tuple
    sr_sd_grid: float         # the gate's own dispersion term, used for the DSR at N = G only
    sr_sd_daily: float        # the caller's labelled term, used for the N_raw lines only (pairing reserved, ⑨-3d)
    sr_sd_label: str
    dsr_min: float
    borderline_min: float
    n_sessions: int
    notes: tuple
    rule: str = "S-2"
    provisional: bool = True  # stays True until the R3 recorder exists, with or without the reading of record
    reading_of_record: str = N_RAW_READING_OF_RECORD

    def lines(self) -> tuple:
        out = [f"S-2 [provisional] DSR at N = G = {self.n_grid}: {_fmt(self.dsr_grid)} ({self.status_grid}); "
               f"dispersion term {self.sr_sd_grid:.6g} per period [the gate's own term]"]
        for r in self.readings:
            if r.n_raw is None:
                missing = f"; {_RECORD_MISSING}" if r.of_record else ""
                out.append(f"S-2 [provisional] N_raw {r.reading} ({r.meaning}) [{r.role()}]: not supplied{missing}")
                continue
            tail = f"; N_raw {r.n_raw} < G {self.n_grid}: printed only" if r.below_grid else ""
            out.append(f"S-2 [provisional] DSR at N_raw {r.reading} = {r.n_raw} [{r.role()}]: {_fmt(r.dsr)} "
                       f"({r.status}); dispersion term {self.sr_sd_daily:.6g} per period [{self.sr_sd_label}]{tail}")
        return tuple(out) + tuple(self.notes)


def _dispersion(value, name: str) -> float:
    out = _real(value, name)
    if out < 0:
        raise AdoptionInputError(f"{name} must be >= 0, got {out}")
    return out


def dsr_two_n(oos_daily, *, n_grid, sr_sd_grid, n_raw: Mapping, sr_sd_daily, sr_sd_label: str) -> DsrTwoN:
    """S-2 (criteria 4.2.2 S-2, 6.2; rulings M-3 (나), M-11): `validate.deflated_sharpe` of the OOS daily P&L at
    N = G and at N = N_raw, each against `GATE['dsr_min']`, labelled provisional.

    The two lines take separate dispersion terms. The DSR at N = G is the gate's DSR, so it uses `sr_sd_grid`, the
    gate's own term (`gate_sr_sd_daily(full_pnl)` on the same T x G matrix the gate saw); with the gate's OOS P&L
    and N = G it equals `validate.score_strategy(...).dsr`. Each N_raw line uses `sr_sd_daily` with its required
    `sr_sd_label`, because the term paired with N_raw is reserved for ⑨-3d (R3 design 4.4, 10.2 B Q1); the caller
    may pass the gate's term there too, under its own label. The N_raw statuses are keyed on the N = G line's
    status, so "borderline" ([0.90, dsr_min)) needs the gate's DSR to pass, as criteria 6.2 says.

    `n_raw` maps one or both readings of `N_RAW_READINGS` ("L-FAM", "R-FAM") to an integer count supplied by the
    caller (read on the owner PC; this module opens no ledger). Both readings are always displayed; an absent one
    shows as "not_supplied". R-FAM is the reading of record (`N_RAW_READING_OF_RECORD`, owner ruling 7 of
    2026-11-11) and its line says so; the L-FAM line says it is shown for comparison. When R-FAM is not supplied
    its line says that the reading of record is missing. The result is provisional in every case until the R3
    recorder exists, and each reading is computed and classified exactly as before the ruling. N_raw < G is a
    printed status, not a refusal. Counts must be integers >= 1; a NaN DSR is status "nan" (6.4, N12)."""
    daily = _series(oos_daily, "oos_daily")
    g = _count(n_grid, "n_grid")
    sd_grid = _dispersion(sr_sd_grid, "sr_sd_grid")
    sd = _dispersion(sr_sd_daily, "sr_sd_daily")
    label = _label(sr_sd_label, "sr_sd_label")
    if not isinstance(n_raw, Mapping) or not n_raw:
        raise AdoptionInputError("n_raw must map at least one of " + ", ".join(N_RAW_READINGS) + " to a count")
    unknown = sorted(str(k) for k in n_raw if k not in N_RAW_READINGS)
    if unknown:
        raise AdoptionInputError(f"unknown N_raw reading(s) {unknown}; known: {list(N_RAW_READINGS)}")
    counts = {k: _count(v, f"n_raw[{k!r}]") for k, v in n_raw.items()}
    dsr_grid = float(V.deflated_sharpe(daily, n_trials=g, sr_sd_daily=sd_grid))
    status_grid = classify_dsr(dsr_grid)
    readings, notes = [], [_PROVISIONAL_NOTE, _PAIRING_NOTE]
    for key, meaning in N_RAW_READINGS.items():
        of_record = key == N_RAW_READING_OF_RECORD
        if key not in counts:
            readings.append(RawReading(key, meaning, None, float("nan"), "not_supplied", False, of_record))
            continue
        value = float(V.deflated_sharpe(daily, n_trials=counts[key], sr_sd_daily=sd))
        readings.append(RawReading(key, meaning, counts[key], value, classify_dsr(value, grid_status=status_grid),
                                   counts[key] < g, of_record))
    if any(r.below_grid for r in readings):
        notes.append(_BELOW_GRID_NOTE)
    if status_grid == "nan" or any(r.status == "nan" for r in readings):
        notes.append("a NaN DSR does not meet S-2 (criteria 6.4, N12)")
    return DsrTwoN(n_grid=g, dsr_grid=dsr_grid, status_grid=status_grid, readings=tuple(readings),
                   sr_sd_grid=sd_grid, sr_sd_daily=sd, sr_sd_label=label, dsr_min=float(V.GATE["dsr_min"]),
                   borderline_min=DSR_BORDERLINE_MIN, n_sessions=int(daily.size), notes=tuple(notes))


# --------------------------------------------------------------------------- #
# S-3 / S-4: Ledoit-Wolf studentized paired delta-Sharpe (M-2, M-6, M-11)
# --------------------------------------------------------------------------- #
def classify_comparison(d_sr: float, p: float) -> str:
    """S-3 / S-4 line status (criteria 4.0 rule 2, 4.2.2 S-3 and S-4, 6.2; rulings M-2, M-6, M-11). A win needs
    the point estimate in the registered direction (dSR > 0) AND one-sided p <= 0.10. Borderline is one-sided p
    in (0.10, 0.20] with dSR > 0 (reading: the zone of 6.2 is the near-miss of a win, so the direction rule of
    4.0 applies to it too). Anything else is "not_won". A borderline result is never adopted (M-11)."""
    d, pv = float(d_sr), float(p)
    if not math.isfinite(d) or not math.isfinite(pv) or not 0.0 <= pv <= 1.0:
        raise AdoptionInputError(f"classify_comparison needs a finite dSR and 0 <= p <= 1, got {d}, {pv}")
    if d <= 0.0:
        return "not_won"
    if pv <= ALPHA_ONE_SIDED:
        return "win"
    if pv <= BORDERLINE_P_MAX:
        return "borderline"
    return "not_won"


@dataclass(frozen=True)
class Comparison:
    rule: str                 # "S-3" (incumbent) or "S-4" (a registered baseline)
    other: str                # the incumbent's or baseline's label
    status: str               # win / borderline / not_won / not_run
    counts: bool              # False: printed only (an addition's incumbent comparison, M-19)
    d_sr: float
    se: float
    t_obs: float
    p_lw: Optional[Union[float, str]]   # as gate_stats prints it ("< 1/B" at a resample count of 0)
    p: float                  # its comparison value, gate_stats.p_numeric
    p_hac: float
    count: Optional[int]
    block: int
    block_events: tuple       # (event, block, reason) from pw_block_psi's fallback log
    B: int
    seed: int
    n_sessions: int
    first_session: date
    last_session: date
    conforms_to_registration: bool = True   # False: B or seed differs from criteria 3.2 item 11 (GATE B, seed 11)
    reason: str = ""
    alpha: float = ALPHA_ONE_SIDED
    borderline_max: float = BORDERLINE_P_MAX

    def line(self) -> str:
        role = "" if self.counts else " [printed only, addition (M-19)]"
        if not self.conforms_to_registration:
            role += (f" [OFF-REGISTRATION: B {self.B}, seed {self.seed}; criteria 3.2 item 11 fixes "
                     f"B {int(V.GATE['bootstrap_B'])} and seed {int(GS.SEED_STUDY)}]")
        if self.status == "not_run":
            return f"{self.rule} vs {self.other}{role}: NOT_RUN ({self.reason})"
        return (f"{self.rule} vs {self.other}{role}: dSR {self.d_sr:+.4f}, LW p {self.p_lw} (one-sided, block "
                f"{self.block}, B {self.B}, seed {self.seed}; HAC p {self.p_hac:.4g}) -> {self.status} "
                f"(win: dSR > 0 and p <= {self.alpha:.2f}; borderline: p in ({self.alpha:.2f}, "
                f"{self.borderline_max:.2f}])")


def lw_compare(challenger, other, challenger_dates: Sequence, other_dates: Sequence, *, rule: str,
               other_label: str, counts: bool = True, B: Optional[int] = None,
               seed: Optional[int] = None) -> Comparison:
    """S-3 (incumbent, replacement) and S-4 (each registered baseline) of criteria 4.2.2; rulings M-2, M-6 (가),
    M-11, M-19. `gate_stats.lw_studentized_boot(challenger, other)` on the same OOS sessions with
    block = `gate_stats.pw_block_psi` (max(21, PW(psi)); its 250-session fallback is kept in `block_events`),
    B = `GATE['bootstrap_B']` and seed = `gate_stats.SEED_STUDY` unless given. The one-sided p is
    `gate_stats.p_numeric(p_lw, B)`; "< 1/B" compares as 1/B. The gate's `bench_p` (a lower-tail share of
    `validate.sharpe_diff_bootstrap`) is not used. Another B or seed is for tests only: the result is marked
    `conforms_to_registration=False` and its line says OFF-REGISTRATION (criteria 3.2 item 11, 6.4: B 2,000, seed
    11). A cash baseline is not a series here: `strategy_lines` takes it as `CASH_BASELINE` (criteria 2.3).

    Unequal or misaligned sessions are refused (`AdoptionInputError`), never trimmed. When the statistic is
    undefined (zero HAC SE, a block longer than the sample, fewer than 30 sessions) the line is "not_run" with
    the reason. `counts=False` marks an addition's incumbent comparison, printed only (M-19)."""
    rule = _label(rule, "rule")
    if rule not in ("S-3", "S-4"):
        raise AdoptionInputError(f"rule must be 'S-3' or 'S-4', got {rule!r}")
    other_label = _label(other_label, "other_label")
    B = int(V.GATE["bootstrap_B"]) if B is None else _count(B, "B")
    if seed is None:
        seed = int(GS.SEED_STUDY)
    elif isinstance(seed, bool) or not isinstance(seed, (int, np.integer)) or int(seed) < 0:
        raise AdoptionInputError(f"seed must be a non-negative integer, got {seed!r}")
    a, b, sessions = _aligned(challenger, other, challenger_dates, other_dates, "challenger", other_label)
    events: list = []
    block = int(GS.pw_block_psi(a, b, log=events))
    event_rows = tuple((str(e.get("event", "")), int(e.get("block", 0)), str(e.get("reason", ""))) for e in events)
    conforms = B == int(V.GATE["bootstrap_B"]) and int(seed) == int(GS.SEED_STUDY)
    common = dict(rule=rule, other=other_label, counts=bool(counts), block=block, block_events=event_rows, B=B,
                  seed=int(seed), n_sessions=int(a.size), first_session=sessions[0], last_session=sessions[-1],
                  conforms_to_registration=conforms)
    nan = float("nan")
    try:
        res = GS.lw_studentized_boot(a, b, block, B=B, seed=int(seed))
    except ValueError as exc:
        hint = _CASH_HINT if np.all(b == b[0]) else ""
        return Comparison(status="not_run", d_sr=nan, se=nan, t_obs=nan, p_lw=None, p=nan, p_hac=nan, count=None,
                          reason=f"lw_studentized_boot refused: {exc}{hint}", **common)
    d_sr, se, t_obs = float(res["dSR"]), float(res["se"]), float(res["t_obs"])
    if not (math.isfinite(d_sr) and math.isfinite(se) and se > 0 and math.isfinite(t_obs)):
        return Comparison(status="not_run", d_sr=d_sr, se=se, t_obs=t_obs, p_lw=None, p=nan, p_hac=nan,
                          count=None, reason="non-finite dSR, HAC SE or t statistic", **common)
    p = float(GS.p_numeric(res["p_lw"], res["B"]))
    return Comparison(status=classify_comparison(d_sr, p), d_sr=d_sr, se=se, t_obs=t_obs, p_lw=res["p_lw"], p=p,
                      p_hac=float(res["p_hac"]), count=int(res["count"]), **common)


@dataclass(frozen=True)
class CashBaseline:
    """S-4 line for a declared cash baseline (criteria 2.3, M-4): pairs (E8, S6) take cash as their baseline and
    criteria 2.3 replaces that comparison with the gate's existing check that the Sharpe interval excludes 0, which
    is part of S-1 (the caller's precondition). No LW test is run and no number is claimed here."""
    other: str
    rule: str = "S-4"
    status: str = "replaced"
    counts: bool = True
    replaced_by: str = "S-1"
    reason: str = _CASH_NOTE

    def line(self) -> str:
        return f"{self.rule} vs {self.other}: REPLACED ({self.reason})"


# --------------------------------------------------------------------------- #
# S-7: power line (printed only)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class PowerS7:
    other: str
    status: str               # "printed" or "not_run"
    se: float                 # gate_stats.lw_hac_se(...).se, annualised
    se_nw10: float
    mde80: float              # gate_stats.MDE_FACTOR * se
    expected_dsr: float       # the registered expected delta-Sharpe (criteria 3.2 item 8)
    underpowered_vs_expected: bool
    n_sessions: int
    reason: str = ""
    rule: str = "S-7"
    printed_only: bool = True

    def line(self) -> str:
        if self.status == "not_run":
            return f"S-7 vs {self.other}: NOT_RUN ({self.reason})"
        flag = "MDE80 above the expected dSR" if self.underpowered_vs_expected else "MDE80 within the expected dSR"
        return (f"S-7 vs {self.other} [printed only]: SE(dSR) {self.se:.4f} (NW10 {self.se_nw10:.4f}), MDE80 "
                f"{self.mde80:.4f} vs registered expected dSR {self.expected_dsr:.4f}: {flag}")


def power_line_s7(challenger, incumbent, challenger_dates: Sequence, incumbent_dates: Sequence, *,
                  expected_dsr, other_label: str = "incumbent") -> PowerS7:
    """S-7 (criteria 4.2.2 S-7, 3.2 item 8, 5.3; ruling M-6): MDE80 = `gate_stats.MDE_FACTOR` x SE(dSR) with
    SE = `gate_stats.lw_hac_se(challenger, incumbent).se`, compared with the registered expected dSR (> 0, annual
    Sharpe units). The flag `underpowered_vs_expected` is printed only: M-6 did not answer whether it turns S-3
    into INSUFFICIENT_DATA (criteria section 9, decision 6). `gate_stats.power_line` is not used: it takes the
    macro cards' SE plateau and only CARD-O / CARD-P. Sessions must align as in `lw_compare`."""
    other_label = _label(other_label, "other_label")
    expected = _real(expected_dsr, "expected_dsr")
    if expected <= 0:
        raise AdoptionInputError(f"expected_dsr must be > 0, got {expected}")
    a, b, _ = _aligned(challenger, incumbent, challenger_dates, incumbent_dates, "challenger", other_label)
    nan = float("nan")
    try:
        hac = GS.lw_hac_se(a, b)
    except ValueError as exc:
        return PowerS7(other=other_label, status="not_run", se=nan, se_nw10=nan, mde80=nan, expected_dsr=expected,
                       underpowered_vs_expected=False, n_sessions=int(a.size), reason=f"lw_hac_se refused: {exc}")
    se = float(hac.se)
    if not (math.isfinite(se) and se > 0):
        return PowerS7(other=other_label, status="not_run", se=se, se_nw10=float(hac.se_nw10), mde80=nan,
                       expected_dsr=expected, underpowered_vs_expected=False, n_sessions=int(a.size),
                       reason="HAC SE is zero or non-finite")
    mde80 = float(GS.MDE_FACTOR) * se
    return PowerS7(other=other_label, status="printed", se=se, se_nw10=float(hac.se_nw10), mde80=mde80,
                   expected_dsr=expected, underpowered_vs_expected=bool(mde80 > expected), n_sessions=int(a.size))


# --------------------------------------------------------------------------- #
# The collected strategy lines (no outcome)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class StrategyLines:
    kind: str                 # "replace" or "add" (M-19)
    s2: DsrTwoN
    s3: Optional[Comparison]
    s4: tuple                 # one Comparison (or CashBaseline) per registered baseline, in the caller's order
    s7: Optional[PowerS7]
    sample_end: SampleEnd
    notes: tuple
    unit: str = UNIT
    l1_note: str = L1_NOTE
    provisional: bool = True

    def lines(self) -> tuple:
        out = [f"{self.unit} strategy lines ({self.kind}); {self.l1_note}", self.sample_end.line()]
        out += list(self.s2.lines())
        if self.s3 is not None:
            out.append(self.s3.line())
        out += [c.line() for c in self.s4]
        if self.s7 is not None:
            out.append(self.s7.line())
        return tuple(out) + tuple(self.notes)


def strategy_lines(*, kind: str, challenger, challenger_dates: Sequence, n_grid, sr_sd_grid, n_raw: Mapping,
                   sr_sd_daily, sr_sd_label: str, baselines: Mapping, incumbent=None,
                   incumbent_dates: Optional[Sequence] = None, incumbent_label: str = "incumbent",
                   expected_dsr=None) -> StrategyLines:
    """Collect S-2, S-3 and S-4 (and S-7) for one registration (criteria 4.2.2; rulings M-3, M-4, M-6, M-11,
    M-14, M-19, M-20). The gate (S-1) is the caller's precondition and is not re-run here.

    `kind` is "replace" or "add" (M-19, criteria 3.2 item 12). A replacement needs the incumbent and the registered
    expected dSR: S-3 counts and S-7 is printed. An addition is judged by S-2 and S-4; an incumbent comparison,
    if supplied, is printed only and claims nothing. An expected dSR, whenever supplied, must be finite and > 0.
    `sr_sd_grid` is the gate's dispersion term and `sr_sd_daily` / `sr_sd_label` the N_raw term (`dsr_two_n`).
    `baselines` maps each registered baseline's label to `(daily_pnl, sessions)` or to `CASH_BASELINE` (M-4: at
    least one; criteria 2.3: cash is replaced by the gate's Sharpe-interval check); each series is an S-4 line on
    the challenger's sessions. B and seed are the registration's (criteria 3.2 item 11) and cannot be changed
    here. The holdout guard reads the challenger's last session (M-14). The collected result carries the L1 note
    (M-20) and no outcome. PCA butterfly (B2) has no gate daily P&L column (criteria 2.3) and is outside this unit."""
    kind = _label(kind, "kind")
    if kind not in KINDS:
        raise AdoptionInputError(f"kind must be one of {KINDS}, got {kind!r}")
    sessions = _sessions(challenger_dates, "challenger sessions")
    if not sessions:
        raise AdoptionInputError("challenger has no sessions")
    if _series(challenger, "challenger").size != len(sessions):
        raise AdoptionInputError("challenger: the number of values and sessions differ")
    if not isinstance(baselines, Mapping) or not baselines:
        raise AdoptionInputError("at least one registered baseline is required (S-4, M-4)")
    if kind == "replace" and (incumbent is None or incumbent_dates is None):
        raise AdoptionInputError("a replacement needs the incumbent's P&L and sessions (S-3, M-19)")
    if kind == "replace" and expected_dsr is None:
        raise AdoptionInputError("a replacement needs the registered expected dSR (S-7, criteria 3.2 item 8)")
    if (incumbent is None) != (incumbent_dates is None):
        raise AdoptionInputError("incumbent and incumbent_dates go together")
    if expected_dsr is not None:
        expected_dsr = _real(expected_dsr, "expected_dsr")
        if expected_dsr <= 0:
            raise AdoptionInputError(f"expected_dsr must be > 0, got {expected_dsr}")
    s2 = dsr_two_n(challenger, n_grid=n_grid, sr_sd_grid=sr_sd_grid, n_raw=n_raw, sr_sd_daily=sr_sd_daily,
                   sr_sd_label=sr_sd_label)
    s3 = s7 = None
    notes = [_NO_OUTCOME_NOTE]
    if incumbent is not None:
        s3 = lw_compare(challenger, incumbent, sessions, incumbent_dates, rule="S-3", other_label=incumbent_label,
                        counts=(kind == "replace"))
        if expected_dsr is not None:
            s7 = power_line_s7(challenger, incumbent, sessions, incumbent_dates, expected_dsr=expected_dsr,
                               other_label=incumbent_label)
    elif expected_dsr is not None:
        notes.append("an expected dSR was registered but no incumbent was supplied, so no S-7 line is printed")
    s4 = []
    for label, pair in baselines.items():
        name = _label(label, "baseline")
        if isinstance(pair, str) and pair == CASH_BASELINE:
            s4.append(CashBaseline(other=name))
            continue
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise AdoptionInputError(f"baseline {label!r} must be (daily_pnl, sessions) or CASH_BASELINE")
        s4.append(lw_compare(challenger, pair[0], sessions, pair[1], rule="S-4", other_label=name))
    return StrategyLines(kind=kind, s2=s2, s3=s3, s4=tuple(s4), s7=s7, sample_end=check_sample_end(sessions[-1]),
                         notes=tuple(notes))
