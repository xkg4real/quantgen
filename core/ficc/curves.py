"""Yield curves: construction methods, shifts, descriptors, PCA.

One object, `YieldCurve`, carries continuously-compounded zero rates at a set of
knot tenors and answers every discounting question the rest of the FICC core
asks (DF, zero, forward, annuity, par rate). Builders turn a par-yield snapshot
into a curve; `analyze_curve` turns a history of par curves into the numbers
the rates page and the narrative state (slopes, flies, forwards, shape, the
20-session regime); `curve_pca` gives level/slope/curvature.

Construction methods (`CURVE_METHODS`, chosen by `curve_from_snapshot`):

  exact (reprice every input par yield)
    bootstrap        sequential bootstrap, log-linear discount factors between quotes
    cubic_spline     natural cubic spline through the bond par yields (from 1y), read
                     at every half-year and bootstrapped (the classic swap-desk recipe)
    pchip            the same with a shape-preserving monotone cubic (Fritsch &
                     Carlson 1980, SIAM J. Numer. Anal. 17(2)); no overshoot
    monotone_convex  Hagan & West (2006, Applied Mathematical Finance 13(2)):
                     continuous, positive forwards, solved jointly with the bonds
    smith_wilson     Smith & Wilson (2001) as specified by EIOPA for Solvency II:
                     kernel fit through the cash flows, extrapolated to an
                     ultimate forward rate (UFR and alpha are stated assumptions)
  smooth (least squares; the fit error is reported in the note)
    nelson_siegel    Nelson & Siegel (1987), four parameters
    diebold_li       Nelson-Siegel with lambda fixed at 0.0609 per month (Diebold
                     & Li 2006, J. Econometrics 130), betas by OLS
    svensson         Svensson (1994), six parameters
    bjork_christensen  Björk & Christensen (1999, Mathematical Finance 9(4)):
                     Nelson-Siegel plus a second slope term, five parameters

The exact non-bootstrap methods are evaluated on a dense grid (every month and
every coupon date) and stored as knots of the same log-linear `YieldCurve`, so
shifts, key-rate bumps and pricing work unchanged; `pillars` keeps the input
tenors for tables. Parametric fits are evaluated on KEY_TENORS ∪ input tenors
and bootstrapped, as Nelson-Siegel always was here.

Simplifications, on purpose:

  * ACT/365F simple year fractions; tenors are plain floats in years.
  * Interpolation is log-linear in discount factors (linear in z·t) between
    knots, flat in the zero rate beyond both ends. The bootstrap uses the SAME
    interpolation for coupon dates that fall between knots, so `par_rate` of a
    bootstrapped curve reproduces its inputs exactly.
  * Tenors under one year are money-market instruments: DF = 1/(1 + y·t).
    From one year on, par yields are coupon bonds paying `freq` times a year.
  * Coupon dates are t_i = T − k/freq for k = 0..n−1, dropping t ≤ start; a
    short first stub still carries a full 1/freq weight in the annuity.
  * Single-curve: the same curve projects forwards and discounts.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

import numpy as np
from scipy.interpolate import CubicSpline, PchipInterpolator
from scipy.optimize import brentq, least_squares, root

from core.ficc.common import BP, KEY_TENORS, FICCError, tenor_label

if TYPE_CHECKING:                                    # data.py owns these shapes
    from core.ficc.data import CurvePanel, CurveSnapshot

_FD_H = 1e-4                                          # finite-difference step (years)
_TABLE_KEYS = ("tenor", "label", "zero", "df", "par", "fwd_1y")

# Every method `curve_from_snapshot` accepts, exact ones first.
CURVE_METHODS: tuple[str, ...] = ("bootstrap", "cubic_spline", "pchip", "monotone_convex",
                                  "smith_wilson", "nelson_siegel", "diebold_li", "svensson",
                                  "bjork_christensen")
EXACT_METHODS = frozenset(CURVE_METHODS[:5])          # reprice every input par yield
PARAMETRIC_METHODS = frozenset(CURVE_METHODS[5:])     # least-squares fits, rmse reported
METHOD_NAMES: dict[str, str] = {                      # English display names (UIs translate them)
    "bootstrap": "Bootstrap", "cubic_spline": "Natural cubic spline",
    "pchip": "Monotone cubic (PCHIP)", "monotone_convex": "Monotone convex (Hagan-West)",
    "smith_wilson": "Smith-Wilson", "nelson_siegel": "Nelson-Siegel", "diebold_li": "Diebold-Li",
    "svensson": "Svensson", "bjork_christensen": "Björk-Christensen"}

DIEBOLD_LI_LAMBDA = 0.0609 * 12.0   # Diebold & Li (2006): 0.0609 per month -> per year
SW_UFR = 0.033                      # Smith-Wilson ultimate forward rate (annual compounding): an
                                    # ASSUMPTION, the euro UFR EIOPA set for 2024
SW_ALPHA = 0.10                     # Smith-Wilson convergence speed: an ASSUMPTION (the QIS5 value;
                                    # EIOPA now calibrates alpha >= 0.05 per currency, not done here)
SW_HORIZON = 60.0                   # Smith-Wilson extrapolation is sampled to 60y, flat zero beyond


def coupon_times(maturity: float, freq: int = 2, start: float = 0.0) -> np.ndarray:
    """Cashflow times T − k/freq for k = 0..n−1 that lie in (start, T], ascending."""
    if maturity <= start:
        raise ValueError(f"maturity {maturity} must exceed start {start}.")
    if freq < 1:
        raise ValueError(f"freq must be >= 1, got {freq}.")
    n = int(math.ceil((maturity - start) * freq - 1e-9))
    return np.sort(maturity - np.arange(n) / freq)


# --------------------------------------------------------------------------- #
# The curve
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class YieldCurve:
    date: str
    source: str
    tenors: tuple[float, ...]
    zeros: tuple[float, ...]          # continuously compounded, decimals
    method: str = "bootstrap"         # one of CURVE_METHODS | flat | shifted
    note: str = ""
    params: tuple[float, ...] = ()    # fitted parameters (parametric methods); (ufr, alpha) for Smith-Wilson
    pillars: tuple[float, ...] = ()   # input tenors to report when the knots are a dense grid

    def __post_init__(self) -> None:
        ts = tuple(float(t) for t in self.tenors)
        zs = tuple(float(z) for z in self.zeros)
        if not ts or len(ts) != len(zs):
            raise ValueError("tenors and zeros must be non-empty and the same length.")
        if ts[0] <= 0 or any(b <= a for a, b in zip(ts, ts[1:])):
            raise ValueError("tenors must be positive and strictly ascending.")
        if not all(math.isfinite(z) for z in zs):
            raise ValueError("zeros must be finite.")
        object.__setattr__(self, "tenors", ts)
        object.__setattr__(self, "zeros", zs)
        object.__setattr__(self, "pillars", tuple(float(p) for p in self.pillars))

    # -- discounting ------------------------------------------------------- #
    def _log_df(self, t) -> np.ndarray:
        t = np.asarray(t, dtype=float)
        if np.any(t < 0):
            raise ValueError("t must be >= 0.")
        ts, zs = np.asarray(self.tenors), np.asarray(self.zeros)
        zt = np.interp(t, ts, ts * zs)                 # linear in z·t between knots
        zt = np.where(t < ts[0], zs[0] * t, zt)        # flat zero beyond the ends
        zt = np.where(t > ts[-1], zs[-1] * t, zt)
        return -zt

    def df(self, t) -> float | np.ndarray:
        out = np.exp(self._log_df(t))
        return float(out) if out.ndim == 0 else out

    def zero(self, t) -> float | np.ndarray:
        t = np.asarray(t, dtype=float)
        with np.errstate(divide="ignore", invalid="ignore"):
            z = np.where(t > 0, -self._log_df(t) / np.where(t > 0, t, 1.0), self.zeros[0])
        return float(z) if z.ndim == 0 else z

    def fwd(self, t1: float, t2: float) -> float:
        """Simple-compounded forward between t1 and t2: (DF1/DF2 − 1)/(t2 − t1)."""
        if t2 <= t1:
            raise ValueError(f"t2 ({t2}) must exceed t1 ({t1}).")
        return (self.df(t1) / self.df(t2) - 1.0) / (t2 - t1)

    def inst_fwd(self, t: float) -> float:
        """−d ln DF/dt by central finite difference (one-sided at t < h)."""
        h = _FD_H
        if t < h:
            return float(-(self._log_df(t + h) - self._log_df(t)) / h)
        return float(-(self._log_df(t + h) - self._log_df(t - h)) / (2 * h))

    def annuity(self, maturity: float, freq: int = 2, start: float = 0.0) -> float:
        """Σ DF(t_i)/freq over coupon dates in (start, T]."""
        return float(np.sum(self.df(coupon_times(maturity, freq, start))) / freq)

    def par_rate(self, maturity: float, freq: int = 2, start: float = 0.0) -> float:
        """(DF(start) − DF(T)) / annuity(start, T, freq)."""
        return (self.df(start) - self.df(maturity)) / self.annuity(maturity, freq, start)

    # -- bumps ------------------------------------------------------------- #
    def shifted(self, bp: float) -> YieldCurve:
        """Parallel shift of every zero by `bp` basis points."""
        zs = tuple(z + bp * BP for z in self.zeros)
        return replace(self, zeros=zs, method="shifted",
                       note=f"{self.note} parallel {bp:+.1f}bp".strip())

    def key_rate_shifted(self, tenor: float, bp: float, *,
                         key_tenors: tuple[float, ...] = KEY_TENORS) -> YieldCurve:
        """Triangular bump of `bp` centred at `tenor`, falling to zero at the
        adjacent key tenors and flat beyond the first/last key tenor. The bump
        tenor and its neighbours are added as knots (at their interpolated
        zeros, which leaves the curve unchanged) so the bump always bites."""
        lower = max((k for k in key_tenors if k < tenor), default=None)
        upper = min((k for k in key_tenors if k > tenor), default=None)
        xp = [k for k in (lower, tenor, upper) if k is not None]
        fp = [0.0 if k != tenor else 1.0 for k in xp]
        knots = sorted(set(self.tenors) | set(xp))
        zs = np.asarray(self.zero(np.asarray(knots)), dtype=float)
        zs = zs + np.interp(knots, xp, fp) * bp * BP
        return replace(self, tenors=tuple(knots), zeros=tuple(float(z) for z in zs),
                       method="shifted",
                       note=f"{self.note} {tenor_label(tenor)} {bp:+.1f}bp".strip())

    # -- presentation ------------------------------------------------------ #
    def table(self) -> list[dict]:
        """Rows {tenor, label, zero, df, par, fwd_1y} at the pillars (the knots
        when there are none). `par` is the semi-annual par rate from 1y on and the
        money-market simple yield below 1y, matching the bootstrap convention so a
        bootstrapped curve's table echoes its inputs."""
        rows = []
        for t in self.pillars or self.tenors:
            d = self.df(t)
            par = self.par_rate(t, 2) if t >= 1.0 else (1.0 / d - 1.0) / t
            rows.append(dict(zip(_TABLE_KEYS, (t, tenor_label(t), self.zero(t), d, par,
                                               self.fwd(t, t + 1.0)))))
        return rows


# --------------------------------------------------------------------------- #
# Builders
# --------------------------------------------------------------------------- #
def flat_curve(rate: float, *, tenors: tuple[float, ...] = KEY_TENORS, date: str = "",
               source: str = "FLAT") -> YieldCurve:
    return YieldCurve(date=date, source=source, tenors=tuple(tenors),
                      zeros=tuple(float(rate) for _ in tenors), method="flat")


def bootstrap_par_curve(tenors, par_yields, *, freq: int = 2, date: str = "", source: str = "",
                        note: str = "") -> YieldCurve:
    """Sequential bootstrap. Tenors < 1y are money-market: DF = 1/(1 + y·t). From
    1y on, each knot's zero solves 1 = y/freq·Σ DF(t_i) + DF(T) with brentq, where
    DFs on coupon dates between knots come from the curve's own interpolation
    over the knots solved so far plus the candidate. Works with any subset of
    tenors (a grid missing 1m or 6m simply extrapolates flat below its first knot)."""
    pairs = sorted((float(t), float(y)) for t, y in zip(tenors, par_yields))
    if len(pairs) != len(par_yields) or not pairs:
        raise ValueError("tenors and par_yields must be non-empty and the same length.")
    if pairs[0][0] <= 0 or any(b[0] <= a[0] for a, b in zip(pairs, pairs[1:])):
        raise ValueError("tenors must be positive and unique.")
    if not all(math.isfinite(y) for _, y in pairs):
        raise ValueError("par yields must be finite.")
    kt: list[float] = []
    kz: list[float] = []
    for t, y in pairs:
        if t < 1.0:
            if 1.0 + y * t <= 0:
                raise FICCError(f"Money-market yield {y} at {tenor_label(t)} is not positive.")
            z = math.log1p(y * t) / t
        else:
            times = coupon_times(t, freq)

            def gap(cand: float) -> float:
                c = YieldCurve(date, source, tuple(kt) + (t,), tuple(kz) + (cand,))
                return y / freq * float(np.sum(c.df(times))) + c.df(t) - 1.0

            lo, hi = -0.2, 1.0
            if gap(lo) * gap(hi) > 0:
                raise FICCError(f"Bootstrap cannot bracket a zero rate at {tenor_label(t)} "
                                f"for par yield {y:.4%}.")
            z = float(brentq(gap, lo, hi, xtol=1e-14, rtol=1e-14, maxiter=200))
        kt.append(t)
        kz.append(z)
    return YieldCurve(date=date, source=source, tenors=tuple(kt), zeros=tuple(kz),
                      method="bootstrap", note=note)


# --------------------------------------------------------------------------- #
# Exact methods beyond the bootstrap: smooth interpolation through every quote
# --------------------------------------------------------------------------- #
_SNAP = 1e-9                                          # grid points closer than this are one point


def _inputs(tenors, par_yields, *, need: int, what: str) -> tuple[np.ndarray, np.ndarray]:
    """Sorted, validated (tenors, par yields) as arrays, the bootstrap's rules."""
    pairs = sorted((float(t), float(y)) for t, y in zip(tenors, par_yields))
    if len(pairs) != len(par_yields) or not pairs:
        raise ValueError("tenors and par_yields must be non-empty and the same length.")
    if pairs[0][0] <= 0 or any(b[0] <= a[0] for a, b in zip(pairs, pairs[1:])):
        raise ValueError("tenors must be positive and unique.")
    if not all(math.isfinite(y) for _, y in pairs):
        raise ValueError("par yields must be finite.")
    if len(pairs) < need:
        raise FICCError(f"Need at least {need} points for {what}, got {len(pairs)}.")
    return (np.array([p[0] for p in pairs]), np.array([p[1] for p in pairs]))


def _merge(exact: np.ndarray, extra) -> np.ndarray:
    """Sorted union of `exact` (input tenors, kept bit-for-bit) and `extra`; a point
    within 1e-9 of another collapses onto it, an input tenor winning."""
    keep = {float(x) for x in exact}
    out: list[float] = []
    for p in sorted(keep | {float(x) for x in extra}):
        if out and p - out[-1] < _SNAP:
            if p in keep:
                out[-1] = p
            continue
        out.append(p)
    return np.asarray(out)


def _pillars(t: np.ndarray) -> tuple[float, ...]:
    """The rows a table reports: the input tenors and the KEY_TENORS between them
    (no rows that would only show the flat extrapolation)."""
    return tuple(_merge(t, [k for k in KEY_TENORS if t[0] <= k <= t[-1]]))


def _dense_grid(t: np.ndarray, freq: int, end: float | None = None) -> np.ndarray:
    """Every month from the first input tenor to `end` (default the last), every input
    tenor, every coupon date of an input bond and the KEY_TENORS in range. A cash flow
    of an input instrument therefore always sits on a knot, so the stored curve
    reprices the inputs with the method's own discount factors."""
    lo, hi = float(t[0]), float(t[-1] if end is None else max(end, t[-1]))
    months = np.arange(1, int(math.floor(hi * 12 + 1e-9)) + 1) / 12.0
    extra = [m for m in months if lo - _SNAP <= m <= hi + _SNAP]
    for T in t:
        if T >= 1.0:
            extra.extend(coupon_times(float(T), freq))
    extra.extend(k for k in KEY_TENORS if lo <= k <= hi)
    return _merge(t, extra)


def _sampled(log_df: np.ndarray, grid: np.ndarray, *, method: str, t: np.ndarray, date: str,
             source: str, note: str, params: tuple[float, ...] = ()) -> YieldCurve:
    zeros = -np.asarray(log_df, dtype=float) / grid
    if not np.all(np.isfinite(zeros)):
        raise FICCError(f"{method} produced a non-finite discount factor.")
    return YieldCurve(date=date, source=source, tenors=tuple(float(g) for g in grid),
                      zeros=tuple(float(z) for z in zeros), method=method, note=note,
                      params=params, pillars=_pillars(t))


def par_spline_curve(tenors, par_yields, *, kind: str = "cubic_spline", freq: int = 2,
                     date: str = "", source: str = "", note: str = "") -> YieldCurve:
    """Interpolate the PAR yields, then bootstrap them at every half-year.

    kind="cubic_spline": natural cubic spline (second derivative zero at both ends).
    kind="pchip": monotone piecewise cubic Hermite interpolation (Fritsch & Carlson
    1980, as in scipy's PchipInterpolator) — between two quotes it never leaves
    their range, so it cannot invent bumps the quotes do not show.

    The spline runs through the bond par yields (tenors from 1y; at least three)
    and is read at every half-year from the first to the last of them (no
    first-coupon stubs). Money-market quotes below 1y use a different yield
    convention, so they are not splined with the bonds: they are bootstrapped as
    given, log-linear between them as in the bootstrap. The input quotes are kept
    exactly and the grid is bootstrapped, so every input par yield is repriced
    exactly; between bond quotes the curve follows the spline instead of the
    bootstrap's flat forwards. No extrapolation: flat zero below the first and
    beyond the last quote, as for the bootstrap."""
    if kind not in ("cubic_spline", "pchip"):
        raise FICCError(f"Unknown par-spline kind {kind!r}.")
    t, y = _inputs(tenors, par_yields, need=1, what="a par-yield spline")
    bonds = t >= 1.0
    if int(bonds.sum()) < 3:
        raise FICCError(f"Need at least 3 par yields from 1y for a par-yield spline, "
                        f"got {int(bonds.sum())}.")
    spline = (CubicSpline(t[bonds], y[bonds], bc_type="natural") if kind == "cubic_spline"
              else PchipInterpolator(t[bonds], y[bonds]))
    first, hi = float(t[bonds][0]), float(t[-1])
    halves = [first + k / freq for k in range(int(math.floor((hi - first) * freq + 1e-9)) + 1)]
    grid = _merge(t, [h for h in halves if h <= hi])
    quoted = dict(zip(t.tolist(), y.tolist()))
    values = [quoted.get(float(g), float(spline(g))) for g in grid]
    base = bootstrap_par_curve(grid, values, freq=freq, date=date, source=source)
    name = "natural cubic spline" if kind == "cubic_spline" else "monotone cubic (PCHIP)"
    text = f"{note} {name} on par yields, bootstrapped at {grid.size} points".strip()
    return replace(base, method=kind, note=text, pillars=_pillars(t))


def _hw_forwards(tau: np.ndarray, Z: np.ndarray, positivity: bool) -> tuple[np.ndarray, np.ndarray]:
    """Hagan & West (2006) steps 1-3: discrete forwards fd_i on (tau_{i-1}, tau_i] and
    instantaneous forwards f_i at the knots, f_0 at t = 0. With `positivity` (used
    when every discrete forward is positive) f_i is collared into [0, 2·min(fd)]."""
    dt = np.diff(tau)
    fd = np.diff(Z) / dt
    n = fd.size
    f = np.empty(n + 1)
    if n == 1:
        f[:] = fd[0]
    else:
        f[1:n] = (dt[:-1] * fd[1:] + dt[1:] * fd[:-1]) / (dt[:-1] + dt[1:])
        f[0] = fd[0] - 0.5 * (f[1] - fd[0])
        f[n] = fd[n - 1] - 0.5 * (f[n - 1] - fd[n - 1])
    if positivity:
        f[0] = min(max(f[0], 0.0), 2.0 * fd[0])
        f[1:n] = np.clip(f[1:n], 0.0, 2.0 * np.minimum(fd[:-1], fd[1:]))
        f[n] = min(max(f[n], 0.0), 2.0 * fd[n - 1])
    return fd, f


def _hw_g_integral(g0: float, g1: float, x: float) -> float:
    """∫_0^x g(s) ds for Hagan-West's g on [0, 1], g(0) = g0, g(1) = g1, ∫_0^1 g = 0.
    The four sectors and their formulas are Hagan & West (2006) section 5."""
    if g0 == 0.0 and g1 == 0.0:
        return 0.0
    if (g0 < 0 and -0.5 * g0 <= g1 <= -2.0 * g0) or (g0 > 0 and -0.5 * g0 >= g1 >= -2.0 * g0):
        # (i) g = g0(1 - 4x + 3x²) + g1(-2x + 3x²)
        return g0 * (x - 2.0 * x * x + x ** 3) + g1 * (x ** 3 - x * x)
    if (g0 < 0 and g1 > -2.0 * g0) or (g0 > 0 and g1 < -2.0 * g0):
        # (ii) flat g0 up to eta, then a quadratic to g1
        eta = (g1 + 2.0 * g0) / (g1 - g0)
        tail = (g1 - g0) * (x - eta) ** 3 / (3.0 * (1.0 - eta) ** 2) if x > eta else 0.0
        return g0 * x + tail
    if (g0 > 0 and 0 > g1 > -0.5 * g0) or (g0 < 0 and 0 < g1 < -0.5 * g0):
        # (iii) a quadratic from g0 to g1 reached at eta, then flat g1
        eta = 3.0 * g1 / (g1 - g0)
        if x < eta:
            return g1 * x + (g0 - g1) * (eta ** 3 - (eta - x) ** 3) / (3.0 * eta * eta)
        return g1 * x + (g0 - g1) * eta / 3.0
    # (iv) g0 and g1 of the same sign: two quadratics meeting at their extremum A at eta
    eta = g1 / (g1 + g0)
    a = -g0 * g1 / (g0 + g1)
    if x < eta:
        return a * x + (g0 - a) * (eta ** 3 - (eta - x) ** 3) / (3.0 * eta * eta)
    tail = (g1 - a) * (x - eta) ** 3 / (3.0 * (1.0 - eta) ** 2) if x > eta else 0.0
    return a * x + (g0 - a) * eta / 3.0 + tail


def _hw_log_df(t_knots: np.ndarray, zeros: np.ndarray, at: np.ndarray) -> np.ndarray:
    """ln DF at `at` (0 <= at <= last knot) under monotone-convex interpolation of the
    knot zeros: ∫_0^t f = Z_{i-1} + fd_i·(t - tau_{i-1}) + Δ_i·∫_0^x g."""
    tau = np.concatenate([[0.0], t_knots])
    big_z = np.concatenate([[0.0], zeros * t_knots])
    fd = np.diff(big_z) / np.diff(tau)
    fd, f = _hw_forwards(tau, big_z, positivity=bool(np.all(fd > 0)))
    n = fd.size
    out = np.empty(len(at))
    for k, s in enumerate(np.asarray(at, dtype=float)):
        if s > tau[-1] + _SNAP:
            raise ValueError("monotone convex is evaluated only up to the last knot.")
        i = min(max(int(np.searchsorted(tau, s, side="left")), 1), n)
        a, d = tau[i - 1], tau[i] - tau[i - 1]
        x = min(max((s - a) / d, 0.0), 1.0)
        g0, g1 = f[i - 1] - fd[i - 1], f[i] - fd[i - 1]
        out[k] = -(big_z[i - 1] + fd[i - 1] * (s - a) + d * _hw_g_integral(g0, g1, x))
    return out


def monotone_convex_curve(tenors, par_yields, *, freq: int = 2, date: str = "",
                          source: str = "", note: str = "") -> YieldCurve:
    """Monotone convex interpolation, Hagan & West (2006) "Interpolation methods for
    curve construction", Applied Mathematical Finance 13(2), 89-129.

    The instantaneous forward is interpolated so that (a) it integrates exactly to
    the knot zero rates, (b) it is continuous, (c) it stays positive when every
    discrete forward is positive (their positivity collar), and (d) a quote moves
    the curve only locally. Because coupon dates fall between knots, the knot
    zeros are solved JOINTLY so that every input par yield (money-market below 1y,
    semi-annual coupon bond from 1y) is repriced under this interpolation; the
    log-linear bootstrap is the starting point. The curve is then sampled on a
    monthly grid that holds every coupon date. Flat zero beyond the last quote."""
    t, y = _inputs(tenors, par_yields, need=2, what="monotone convex")
    start = np.asarray(bootstrap_par_curve(t, y, freq=freq).zeros)
    times = [coupon_times(float(T), freq) if T >= 1.0 else None for T in t]

    def residuals(z: np.ndarray) -> np.ndarray:
        r = np.empty(t.size)
        for i, T in enumerate(t):
            if times[i] is None:                      # money market: DF = 1/(1 + y·t)
                r[i] = math.expm1(z[i] * T) / T - y[i]
            else:
                d = np.exp(_hw_log_df(t, z, times[i]))
                r[i] = (1.0 - d[-1]) / (np.sum(d) / freq) - y[i]
        return r

    sol = root(residuals, start, method="hybr", options={"xtol": 1e-14})
    worst = float(np.max(np.abs(residuals(sol.x))))
    if not np.all(np.isfinite(sol.x)) or worst > 1e-10:
        raise FICCError(f"Monotone convex could not reprice the par curve (worst miss "
                        f"{worst / BP:.2e}bp).")
    grid = _dense_grid(t, freq)
    text = (f"{note} monotone convex (Hagan-West) forwards, solved jointly with the par "
            f"bonds, worst miss {worst / BP:.1e}bp").strip()
    return _sampled(_hw_log_df(t, sol.x, grid), grid, method="monotone_convex", t=t,
                    date=date, source=source, note=text)


def _sw_kernel(t: np.ndarray, u: np.ndarray, alpha: float, omega: float) -> np.ndarray:
    """Smith-Wilson W(t, u) = e^{-ω(t+u)}·(α·min(t,u) − e^{-α·max(t,u)}·sinh(α·min(t,u)))."""
    tt, uu = np.asarray(t, dtype=float)[:, None], np.asarray(u, dtype=float)[None, :]
    lo, hi = np.minimum(tt, uu), np.maximum(tt, uu)
    return np.exp(-omega * (tt + uu)) * (alpha * lo - np.exp(-alpha * hi) * np.sinh(alpha * lo))


def smith_wilson_curve(tenors, par_yields, *, ufr: float = SW_UFR, alpha: float = SW_ALPHA,
                       freq: int = 2, horizon: float = SW_HORIZON, date: str = "",
                       source: str = "", note: str = "") -> YieldCurve:
    """Smith & Wilson (2001), "Fitting yield curves with long term constraints",
    in the form EIOPA specifies for the Solvency II risk-free curve (EIOPA-BoS
    technical documentation of the RFR methodology, section on Smith-Wilson).

    P(t) = e^{-ωt} + Σ_j ζ_j·W(t, u_j) with ω = ln(1 + UFR) and the Wilson kernel
    `_sw_kernel`. Each input is an instrument priced at 1: a money-market deposit
    paying 1 + y·t below 1y, a par bond with coupons y/freq from 1y. With cash-flow
    matrix C (instruments × cash-flow dates u), ζ solves (C W Cᵀ) ζ = 1 − C·e^{-ωu},
    so every input is repriced exactly. Beyond the last quote the forward rate
    converges to the UFR at a speed set by alpha.

    `ufr` (annually compounded) and `alpha` are ASSUMPTIONS, not estimates: the
    defaults are 3.30% (the euro UFR EIOPA set for 2024) and 0.10 (the QIS5
    value); EIOPA calibrates alpha per currency, which is not done here. Sampled
    monthly up to `horizon` years, flat zero beyond."""
    if not (math.isfinite(ufr) and ufr > -1.0 and math.isfinite(alpha) and alpha > 0):
        raise FICCError(f"Smith-Wilson needs ufr > -100% and alpha > 0, got {ufr}, {alpha}.")
    t, y = _inputs(tenors, par_yields, need=2, what="Smith-Wilson")
    flows: list[dict[float, float]] = []
    for T, yy in zip(t.tolist(), y.tolist()):
        if T < 1.0:
            flows.append({T: 1.0 + yy * T})
        else:
            cf = {float(s): yy / freq for s in coupon_times(T, freq)}
            cf[T] = cf.get(T, 0.0) + 1.0
            flows.append(cf)
    u = np.array(sorted(set().union(*flows)))
    col = {float(v): j for j, v in enumerate(u)}
    c = np.zeros((t.size, u.size))
    for i, cf in enumerate(flows):
        for s, amount in cf.items():
            c[i, col[s]] = amount
    omega = math.log1p(ufr)
    mu = np.exp(-omega * u)
    zeta = np.linalg.solve(c @ _sw_kernel(u, u, alpha, omega) @ c.T, 1.0 - c @ mu)
    weights = c.T @ zeta
    grid = _dense_grid(t, freq, end=horizon)
    df = np.exp(-omega * grid) + _sw_kernel(grid, u, alpha, omega) @ weights
    if not np.all(df > 0):
        raise FICCError("Smith-Wilson produced a non-positive discount factor.")
    text = (f"{note} Smith-Wilson, UFR {ufr:.2%} and alpha {alpha:g} assumed, "
            f"extrapolated to {grid[-1]:g}y").strip()
    return _sampled(np.log(df), grid, method="smith_wilson", t=t, date=date, source=source,
                    note=text, params=(float(ufr), float(alpha)))


# --------------------------------------------------------------------------- #
# Nelson-Siegel / Svensson
# --------------------------------------------------------------------------- #
def _loading(t: np.ndarray, tau: float) -> tuple[np.ndarray, np.ndarray]:
    """Slope and curvature loadings with the t→0 limit handled."""
    x = t / tau
    safe = np.where(x > 1e-12, x, 1.0)
    slope = np.where(x > 1e-12, (1.0 - np.exp(-safe)) / safe, 1.0)
    return slope, slope - np.exp(-x)


def nelson_siegel(t, beta0: float, beta1: float, beta2: float, tau: float):
    t = np.asarray(t, dtype=float)
    s, c = _loading(t, tau)
    return beta0 + beta1 * s + beta2 * c


def svensson(t, b0: float, b1: float, b2: float, b3: float, tau1: float, tau2: float):
    t = np.asarray(t, dtype=float)
    s, c1 = _loading(t, tau1)
    _, c2 = _loading(t, tau2)
    return b0 + b1 * s + b2 * c1 + b3 * c2


@dataclass(frozen=True)
class NSFit:
    params: tuple[float, ...]
    fitted: np.ndarray = field(repr=False)
    rmse: float = 0.0
    method: str = "nelson_siegel"


def fit_nelson_siegel(tenors, yields, *, svensson: bool = False) -> NSFit:
    """Least squares on the par yields; betas bounded to ±0.5, tau to [0.1, 30].
    Deterministic start (β0 = long yield, β1 = short − long, β2 = 0, τ = 2y)."""
    t = np.asarray(tenors, dtype=float)
    y = np.asarray(yields, dtype=float)
    need = 6 if svensson else 4
    if t.size != y.size or t.size < need:
        raise FICCError(f"Need at least {need} points to fit "
                        f"{'Svensson' if svensson else 'Nelson-Siegel'}, got {t.size}.")
    if not np.all(np.isfinite(y)):
        raise ValueError("yields must be finite.")
    b = 0.5
    if svensson:
        fn, x0 = globals()["svensson"], [y[-1], y[0] - y[-1], 0.0, 0.0, 2.0, 8.0]
        bounds = ([-b, -b, -b, -b, 0.1, 0.1], [b, b, b, b, 30.0, 30.0])
    else:
        fn, x0 = nelson_siegel, [y[-1], y[0] - y[-1], 0.0, 2.0]
        bounds = ([-b, -b, -b, 0.1], [b, b, b, 30.0])
    x0 = np.clip(np.asarray(x0, dtype=float), bounds[0], bounds[1])
    res = least_squares(lambda p: fn(t, *p) - y, x0, bounds=bounds, method="trf")
    fitted = fn(t, *res.x)
    return NSFit(params=tuple(float(p) for p in res.x), fitted=fitted,
                 rmse=float(np.sqrt(np.mean((fitted - y) ** 2))),
                 method="svensson" if svensson else "nelson_siegel")


def fit_diebold_li(tenors, yields, *, lam: float = DIEBOLD_LI_LAMBDA) -> NSFit:
    """Diebold & Li (2006), "Forecasting the term structure of government bond
    yields", J. Econometrics 130, 337-364: Nelson-Siegel with the decay FIXED at
    λ = 0.0609 per month (0.7308 per year, curvature loading peaking near 30
    months), so (β0, β1, β2) come from ordinary least squares and are comparable
    from day to day. Diebold and Li fit zero yields; like every fit in this module
    it is applied to the par yields here. params = (β0, β1, β2, τ = 1/λ) for
    `nelson_siegel`."""
    t = np.asarray(tenors, dtype=float)
    y = np.asarray(yields, dtype=float)
    if t.size != y.size or t.size < 3:
        raise FICCError(f"Need at least 3 points to fit Diebold-Li, got {t.size}.")
    if not np.all(np.isfinite(y)):
        raise ValueError("yields must be finite.")
    if not (math.isfinite(lam) and lam > 0):
        raise FICCError(f"Diebold-Li lambda must be positive, got {lam}.")
    tau = 1.0 / lam
    s, c = _loading(t, tau)
    beta, *_ = np.linalg.lstsq(np.column_stack([np.ones_like(t), s, c]), y, rcond=None)
    params = (float(beta[0]), float(beta[1]), float(beta[2]), float(tau))
    fitted = nelson_siegel(t, *params)
    return NSFit(params=params, fitted=fitted, rmse=float(np.sqrt(np.mean((fitted - y) ** 2))),
                 method="diebold_li")


def bjork_christensen(t, b0: float, b1: float, b2: float, b3: float, tau: float):
    """Björk & Christensen (1999), "Interest rate dynamics and consistent forward
    rate curves", Mathematical Finance 9(4): forward f(m) = b0 + b1·e^{-m/τ} +
    b2·(m/τ)·e^{-m/τ} + b3·e^{-2m/τ}; the yield adds b3·(1 - e^{-2m/τ})/(2m/τ),
    a second slope term at half the decay, to Nelson-Siegel."""
    t = np.asarray(t, dtype=float)
    s, c = _loading(t, tau)
    s2, _ = _loading(t, tau / 2.0)
    return b0 + b1 * s + b2 * c + b3 * s2


def fit_bjork_christensen(tenors, yields) -> NSFit:
    """Least squares on the par yields, started from the Nelson-Siegel fit with
    b3 = 0 (deterministic, and never a worse fit than Nelson-Siegel); betas
    bounded to ±0.5 and τ to [0.1, 30] as for Nelson-Siegel."""
    t = np.asarray(tenors, dtype=float)
    y = np.asarray(yields, dtype=float)
    if t.size != y.size or t.size < 5:
        raise FICCError(f"Need at least 5 points to fit Björk-Christensen, got {t.size}.")
    ns = fit_nelson_siegel(t, y)
    b = 0.5
    bounds = ([-b, -b, -b, -b, 0.1], [b, b, b, b, 30.0])
    x0 = np.clip(np.array([*ns.params[:3], 0.0, ns.params[3]]), bounds[0], bounds[1])
    res = least_squares(lambda p: bjork_christensen(t, *p) - y, x0, bounds=bounds, method="trf")
    fitted = bjork_christensen(t, *res.x)
    return NSFit(params=tuple(float(p) for p in res.x), fitted=fitted,
                 rmse=float(np.sqrt(np.mean((fitted - y) ** 2))), method="bjork_christensen")


_PARAMETRIC_FN = {"nelson_siegel": nelson_siegel, "diebold_li": nelson_siegel,
                  "svensson": svensson, "bjork_christensen": bjork_christensen}


def parametric_function(method: str):
    """The yield function of a parametric method; NSFit.params unpack into it."""
    try:
        return _PARAMETRIC_FN[method]
    except KeyError:
        raise FICCError(f"{method!r} is not a parametric curve method.") from None


def fit_parametric(method: str, tenors, yields) -> NSFit:
    if method in ("nelson_siegel", "svensson"):
        return fit_nelson_siegel(tenors, yields, svensson=method == "svensson")
    if method == "diebold_li":
        return fit_diebold_li(tenors, yields)
    if method == "bjork_christensen":
        return fit_bjork_christensen(tenors, yields)
    raise FICCError(f"{method!r} is not a parametric curve method.")


def curve_from_snapshot(snap: CurveSnapshot, *, method: str = "bootstrap") -> YieldCurve:
    """bootstrap: the par yields as given. Parametric methods (nelson_siegel,
    diebold_li, svensson, bjork_christensen): fit the par curve, evaluate it on
    KEY_TENORS ∪ input tenors, then bootstrap that. cubic_spline / pchip /
    monotone_convex / smith_wilson: exact smooth curves, see their builders."""
    if method == "bootstrap":
        return bootstrap_par_curve(snap.tenors, snap.par_yields, date=snap.date,
                                   source=snap.source, note=snap.note)
    common = dict(date=snap.date, source=snap.source, note=snap.note)
    if method in ("cubic_spline", "pchip"):
        return par_spline_curve(snap.tenors, snap.par_yields, kind=method, **common)
    if method == "monotone_convex":
        return monotone_convex_curve(snap.tenors, snap.par_yields, **common)
    if method == "smith_wilson":
        return smith_wilson_curve(snap.tenors, snap.par_yields, **common)
    if method not in PARAMETRIC_METHODS:
        raise FICCError(f"Unknown curve method {method!r}.")
    fit = fit_parametric(method, snap.tenors, snap.par_yields)
    grid = np.array(sorted(set(KEY_TENORS) | set(float(t) for t in snap.tenors)))
    fn = parametric_function(method)
    curve = bootstrap_par_curve(grid, fn(grid, *fit.params), date=snap.date, source=snap.source)
    note = f"{snap.note} {fit.method} fit, rmse {fit.rmse / BP:.1f}bp".strip()
    return replace(curve, method=method, params=fit.params, note=note)


# --------------------------------------------------------------------------- #
# Curve report
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CurveReport:
    curve: YieldCurve
    snapshot: CurveSnapshot
    descriptors: dict[str, float]
    shape: str                        # normal | flat | inverted | humped
    regime: str                       # bull/bear steepener/flattener, parallel up/down, unchanged
    changes: dict[str, float]         # Δ par yield over `lookback` per tenor label, plus 2s10s
    ns: NSFit                         # the method's own fit if parametric, else Nelson-Siegel
    lookback: int


def _par_at(snap, t: float) -> float:
    """Par yield at tenor t, linearly interpolated over the snapshot grid
    (clamped at the ends, so a grid ending at 20y reports its 20y as '30y')."""
    return float(np.interp(t, np.asarray(snap.tenors, dtype=float),
                           np.asarray(snap.par_yields, dtype=float)))


def _shape(snap) -> str:
    p2, p30 = _par_at(snap, 2.0), _par_at(snap, 30.0)
    s = _par_at(snap, 10.0) - p2
    if s > 25 * BP:
        return "normal"
    if s < -10 * BP:
        return "inverted"
    mids = [y for t, y in zip(snap.tenors, snap.par_yields) if 2.0 < t < 30.0]
    if any(m > p2 + 10 * BP and m > p30 + 10 * BP for m in mids):
        return "humped"
    return "flat"


def _regime(d10: float, d2: float, dslope: float) -> str:
    """bull/bear = 10y down/up ≥ 5bp. If the slope moved ≥ 5bp while the 10y
    stayed within 5bp, bull/bear follows the sign of the 2y-10y average move."""
    if abs(dslope) >= 5 * BP:
        move = d10 if abs(d10) >= 5 * BP else (d10 + d2) / 2
        tone = "bull" if move < 0 else "bear"
        return f"{tone} {'steepener' if dslope > 0 else 'flattener'}"
    if abs(d10) >= 5 * BP:
        return "parallel up" if d10 > 0 else "parallel down"
    return "unchanged"


def analyze_curve(panel: CurvePanel, *, lookback: int = 20,
                  method: str = "bootstrap") -> CurveReport:
    """Latest snapshot → curve + descriptors + shape; `lookback` sessions back →
    regime and per-tenor changes. Descriptors: 2s10s, 5s30s, 3m10y, 2s5s10s_fly
    (2·5y − 2y − 10y), level (mean of 2y/5y/10y) from par yields; 1y1y, 2y1y,
    5y5y are simple forwards off the curve; 1y_fwd_1y_ahead = 1y1y − 1y par,
    i.e. the move the curve prices into the 1y rate over the next year. `ns` is
    the method's own fit for a parametric method, the Nelson-Siegel reference
    fit otherwise."""
    if len(panel) < 2:
        raise FICCError("Need at least two curve dates to analyze.")
    lookback = max(1, min(int(lookback), len(panel) - 1))
    snap = panel.latest()
    prev = panel.at(len(panel) - 1 - lookback)
    curve = curve_from_snapshot(snap, method=method)
    ns = fit_parametric(method if method in PARAMETRIC_METHODS else "nelson_siegel",
                        snap.tenors, snap.par_yields)
    p = {t: _par_at(snap, t) for t in (0.25, 1.0, 2.0, 5.0, 10.0, 30.0)}
    descriptors = {
        "2s10s": p[10.0] - p[2.0],
        "5s30s": p[30.0] - p[5.0],
        "3m10y": p[10.0] - p[0.25],
        "2s5s10s_fly": 2 * p[5.0] - p[2.0] - p[10.0],
        "level": (p[2.0] + p[5.0] + p[10.0]) / 3,
        "1y1y": curve.fwd(1.0, 2.0),
        "2y1y": curve.fwd(2.0, 3.0),
        "5y5y": curve.fwd(5.0, 10.0),
        "1y_fwd_1y_ahead": curve.fwd(1.0, 2.0) - p[1.0],
    }
    changes = {tenor_label(t): float(y_now - y_then) for t, y_now, y_then
               in zip(snap.tenors, snap.par_yields, prev.par_yields)}
    d2 = p[2.0] - _par_at(prev, 2.0)
    d10 = p[10.0] - _par_at(prev, 10.0)
    changes["2s10s"] = d10 - d2
    return CurveReport(curve=curve, snapshot=snap, descriptors=descriptors, shape=_shape(snap),
                       regime=_regime(d10, d2, d10 - d2), changes=changes, ns=ns,
                       lookback=lookback)


# --------------------------------------------------------------------------- #
# PCA
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class PCAResult:
    tenors: tuple[float, ...]
    loadings: np.ndarray = field(repr=False)     # K x n
    explained: np.ndarray = field(repr=False)    # n, fractions of variance
    scores: np.ndarray = field(repr=False)       # T-1 x n (T x n on levels)
    latest_scores: np.ndarray = field(repr=False)
    labels: tuple[str, ...] = ("level", "slope", "curvature")


def curve_pca(panel: CurvePanel, *, n: int = 3, use_changes: bool = True) -> PCAResult:
    """SVD of demeaned daily changes (bp) — or demeaned levels in bp when
    use_changes=False. PC1 is signed so its loadings are positive, PC2 so the
    long end loads positive, later PCs so their largest loading is positive."""
    if len(panel) < 60:
        raise FICCError(f"Need at least 60 curve dates for PCA, got {len(panel)}.")
    y = np.asarray(panel.yields, dtype=float) / BP
    x = np.diff(y, axis=0) if use_changes else y
    x = x - x.mean(axis=0)
    n = max(1, min(int(n), x.shape[1]))
    _, s, vt = np.linalg.svd(x, full_matrices=False)
    loadings = vt[:n].T.copy()
    for j in range(n):
        pivot = (loadings[:, 0].mean() if j == 0 else loadings[-1, 1] if j == 1
                 else loadings[np.argmax(np.abs(loadings[:, j])), j])
        if pivot < 0:
            loadings[:, j] *= -1
    scores = x @ loadings
    explained = (s[:n] ** 2) / np.sum(s ** 2)
    names = ("level", "slope", "curvature")
    labels = tuple(names[j] if j < 3 else f"pc{j + 1}" for j in range(n))
    return PCAResult(tenors=tuple(float(t) for t in panel.tenors), loadings=loadings,
                     explained=explained, scores=scores, latest_scores=scores[-1].copy(),
                     labels=labels)


# --------------------------------------------------------------------------- #
# Self-check
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    from core.ficc.common import UST_TENORS

    # Flat 5% semi-annual par curve → continuous zero 2·ln(1.025) from 1y on.
    flat = bootstrap_par_curve(UST_TENORS, [0.05] * len(UST_TENORS))
    z_cont = 2 * math.log1p(0.025)
    for t, z in zip(flat.tenors, flat.zeros):
        if t >= 1.0:
            assert abs(z - z_cont) < 1e-6, (t, z, z_cont)
        assert abs(flat.par_rate(t) - 0.05) < 1e-8 if t >= 1 else True
    assert flat.df(0.0) == 1.0
    grid = np.linspace(0.0, 40.0, 401)
    assert np.all(np.diff(flat.df(grid)) < 0), "DF must fall with tenor"

    # Round-trip on a sloped, kinked par curve; missing 1m/6m must still work.
    par = [0.052, 0.051, 0.050, 0.047, 0.044, 0.043, 0.042, 0.043, 0.044, 0.047, 0.046]
    c = bootstrap_par_curve(UST_TENORS, par, date="2026-09-04", source="TEST")
    for t, y in zip(UST_TENORS, par):
        got = c.par_rate(t) if t >= 1.0 else (1.0 / c.df(t) - 1.0) / t
        assert abs(got - y) < 1e-8, (t, got, y)
    sparse = bootstrap_par_curve([1.0, 2.0, 5.0, 10.0, 30.0], [0.047, 0.044, 0.042, 0.044, 0.046])
    assert abs(sparse.par_rate(30.0) - 0.046) < 1e-8
    assert all(k in c.table()[3] for k in _TABLE_KEYS)

    # Bumps: parallel moves every zero; a key-rate bump bites only near its tenor.
    up = c.shifted(10.0)
    assert all(abs((zu - z0) - 10 * BP) < 1e-12 for zu, z0 in zip(up.zeros, c.zeros))
    kr = c.key_rate_shifted(5.0, 10.0)
    assert abs(kr.zero(5.0) - c.zero(5.0) - 10 * BP) < 1e-12
    assert abs(kr.zero(10.0) - c.zero(10.0)) < 1e-12 and abs(kr.zero(3.0) - c.zero(3.0)) < 1e-12
    # between knots the bump interpolates in z·t: 10bp·5/(2·6) at 6y
    assert abs(kr.zero(6.0) - c.zero(6.0) - 10 * BP * 5 / 12) < 1e-12
    edge = c.key_rate_shifted(30.0, 10.0)
    assert abs(edge.zero(40.0) - c.zero(40.0) - 10 * BP) < 1e-12, "flat beyond the last key"
    assert abs(c.fwd(1.0, 2.0) - (c.df(1.0) / c.df(2.0) - 1.0)) < 1e-14
    assert abs(c.inst_fwd(4.0) - c.zero(4.0)) < 0.02

    # Nelson-Siegel reproduces its own shape; a fit on a panel is tight.
    ns_par = nelson_siegel(np.array(UST_TENORS), 0.045, -0.01, 0.02, 2.0)
    fit = fit_nelson_siegel(UST_TENORS, ns_par)
    assert fit.rmse < 1e-6, fit.rmse
    assert fit_nelson_siegel(UST_TENORS, ns_par, svensson=True).rmse < 1e-6

    try:
        from core.ficc.data import synthetic_curve_panel
        panel = synthetic_curve_panel(days=200)
    except ImportError:                              # data.py not built yet: local stand-in
        from types import SimpleNamespace as _NS
        rng = np.random.default_rng(7)
        b = np.array([0.045, -0.01, 0.01, 2.0])
        rows = []
        for _ in range(200):
            b = b + rng.normal(0, [0.0004, 0.0006, 0.0008, 0.0], 4)
            rows.append(nelson_siegel(np.array(UST_TENORS), *b) + rng.normal(0, 0.0002, 11))
        ys = np.array(rows)
        dates = tuple(f"D{i:03d}" for i in range(200))

        def _snap(i: int):
            return _NS(date=dates[i], source="SYNTHETIC", tenors=UST_TENORS,
                       par_yields=tuple(float(v) for v in ys[i]), note="stand-in")

        panel = _NS(source="SYNTHETIC", dates=dates, tenors=UST_TENORS, yields=ys, note="",
                    latest=lambda: _snap(199), at=_snap)
        panel.__class__.__len__ = lambda self: 200
    snap = panel.latest()
    assert fit_nelson_siegel(snap.tenors, snap.par_yields).rmse < 5 * BP
    for m in CURVE_METHODS:
        rep = analyze_curve(panel, lookback=20, method=m)
        assert rep.curve.method == m
        if m in EXACT_METHODS:                       # every quote repriced
            for t, y in zip(snap.tenors, snap.par_yields):
                got = rep.curve.par_rate(t) if t >= 1.0 else (1.0 / rep.curve.df(t) - 1.0) / t
                assert abs(got - y) < 1e-9, (m, t, got, y)
        assert [r["tenor"] for r in rep.curve.table()] == sorted(set(KEY_TENORS) | set(snap.tenors))
        assert rep.shape in ("normal", "flat", "inverted", "humped")
        assert rep.regime in ("bull steepener", "bear steepener", "bull flattener",
                              "bear flattener", "parallel up", "parallel down", "unchanged")
        assert set(rep.descriptors) >= {"2s10s", "5s30s", "3m10y", "2s5s10s_fly", "level",
                                        "1y1y", "2y1y", "5y5y", "1y_fwd_1y_ahead"}
        assert "2s10s" in rep.changes and "10y" in rep.changes
    assert _regime(-8 * BP, -20 * BP, 12 * BP) == "bull steepener"
    assert _regime(8 * BP, 0.0, 8 * BP) == "bear steepener"
    assert _regime(8 * BP, 0.0, 0.0) == "parallel up"
    assert _regime(1 * BP, 0.0, 0.0) == "unchanged"

    pca = curve_pca(panel)
    assert pca.explained[0] > 0.5 and np.all(pca.loadings[:, 0] > 0)
    assert pca.loadings[-1, 1] > 0 and pca.scores.shape == (len(panel) - 1, 3)
    assert abs(float(np.sum(pca.explained))) <= 1.0 + 1e-12
    print("ok")
