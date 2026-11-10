"""Yield-curve construction methods (owner UI review 2026-11-10, issue 08: "only three methods?").

Every method in `core.ficc.curves.CURVE_METHODS` is checked on hand-made normal, inverted and
humped U.S. Treasury-style par curves and on the synthetic panel:

  * finite zeros; discount factors positive and strictly decreasing on 0-30y; finite forwards
  * exact methods reprice every input par yield within 0.1bp (in practice ~1e-6bp)
  * parametric methods stay within a stated RMSE of the input par yields (RMSE_BOUND_BP)
  * deterministic; an unknown method still raises FICCError
  * bootstrap / Nelson-Siegel / Svensson are bit-identical to the code before the new methods
    (an in-test copy of the old builder) and match values recorded before the change

plus method-specific properties (Hagan-West sector integrals, linear-forward reproduction and
continuity; Smith-Wilson kernel and UFR convergence; PCHIP no-overshoot; Diebold-Li lambda;
Björk-Christensen nesting Nelson-Siegel) and the Rates page / request wiring.
"""
from __future__ import annotations

import math
import unittest
from dataclasses import replace
from types import SimpleNamespace

import numpy as np

from core.ficc import curves as C
from core.ficc.common import BP, KEY_TENORS, UST_TENORS, FICCError
from core.ficc.data import CurveSnapshot, synthetic_curve_panel

CURVES = {
    "normal":   (0.0350, 0.0360, 0.0370, 0.0380, 0.0395, 0.0405, 0.0420, 0.0432, 0.0445, 0.0465, 0.0470),
    "inverted": (0.0545, 0.0540, 0.0530, 0.0510, 0.0480, 0.0460, 0.0440, 0.0430, 0.0420, 0.0425, 0.0410),
    "humped":   (0.0300, 0.0320, 0.0345, 0.0380, 0.0420, 0.0440, 0.0450, 0.0445, 0.0430, 0.0410, 0.0400),
}
# Stated fit quality of the parametric methods on these curves (root mean square miss of the
# par yields, bp). Observed: NS <= 3.4, Diebold-Li <= 6.1, Svensson <= 1.8, B-C <= 3.1.
RMSE_BOUND_BP = {"nelson_siegel": 5.0, "diebold_li": 10.0, "svensson": 5.0, "bjork_christensen": 5.0}
LEGACY_METHODS = ("bootstrap", "nelson_siegel", "svensson")


def snapshots() -> dict[str, CurveSnapshot]:
    out = {name: CurveSnapshot("2026-11-06", "TEST", tuple(UST_TENORS), ys) for name, ys in CURVES.items()}
    out["synthetic"] = synthetic_curve_panel(days=200, seed=11).latest()
    return out


def quoted(curve: C.YieldCurve, t: float) -> float:
    """The input convention: money-market simple yield below 1y, semi-annual par from 1y."""
    return curve.par_rate(t) if t >= 1.0 else (1.0 / curve.df(t) - 1.0) / t


def misses(curve: C.YieldCurve, snap: CurveSnapshot) -> np.ndarray:
    return np.array([quoted(curve, t) - y for t, y in zip(snap.tenors, snap.par_yields)])


# Values computed by the code BEFORE the new methods were added (2026-11-10, commit 55bcba9):
# (knots, zeros, params, note) per (curve, method).
LEGACY = {
    ('normal', 'bootstrap'): ((0.08333333333333333, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0, 30.0),
        (0.034949057364419556, 0.035838965485887615, 0.036661913369446915, 0.03765283596699353, 0.03914922125636442, 0.04015952306474894, 0.04170230026885997, 0.04297895520778132, 0.04441027990443138, 0.04676089754929981, 0.04735150204184085),
        (), ''),
    ('normal', 'nelson_siegel'): ((0.08333333333333333, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0, 30.0),
        (0.03565949454961588, 0.03591602845716307, 0.03626794211688119, 0.03721251362022783, 0.038810740482063434, 0.0401015455917909, 0.042008139237289556, 0.04331335941032997, 0.04459479463301787, 0.04646310091243686, 0.04720703343638514),
        (0.048023959096387105, -0.012499654225211772, 5.555150914627993e-07, 2.739267980956649), 'nelson_siegel fit, rmse 3.4bp'),
    ('normal', 'svensson'): ((0.08333333333333333, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0, 30.0),
        (0.03503869751878831, 0.035758100827019336, 0.0365439974349379, 0.037800446621226245, 0.03916521768808274, 0.04008624488341578, 0.04167916235177902, 0.043017149015654635, 0.04446892094271732, 0.04663124568840767, 0.04747738586937491),
        (0.04833245850190095, -0.013728282580103545, -6.519050275467955e-09, -0.016986687547072127, 0.625464966746946, 1.7607547661994882), 'svensson fit, rmse 0.8bp'),
    ('inverted', 'bootstrap'): ((0.08333333333333333, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0, 30.0),
        (0.05437661303060601, 0.0536387476396707, 0.05230991495370242, 0.05033575567406584, 0.04735038523213654, 0.045334210884644725, 0.043305451660959164, 0.04228008420735425, 0.04122589169812227, 0.04200972529324624, 0.03971626848482601),
        (), ''),
    ('inverted', 'nelson_siegel'): ((0.08333333333333333, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0, 30.0),
        (0.054617045847805135, 0.05356942971009956, 0.05212640471199048, 0.05023044771420574, 0.04739664457875559, 0.045473368463895526, 0.04326977127782143, 0.04221666026577269, 0.04152906165071854, 0.040995979475410435, 0.04086081548247523),
        (0.04126671478481307, 0.013902057857602115, -0.010074906928752597, 2.298665225349614), 'nelson_siegel fit, rmse 3.2bp'),
    ('inverted', 'svensson'): ((0.08333333333333333, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0, 30.0),
        (0.054510658841614844, 0.05353207296515826, 0.0521657607313418, 0.050353226972300796, 0.047509789432139356, 0.04547641363821241, 0.04307760801823337, 0.04202363628105842, 0.04163258216871906, 0.041821220242434044, 0.039790162937081174),
        (0.01675123242381401, 0.03827044967659252, -9.529686666851206e-06, 0.07052561669544259, 2.6789961577952712, 14.476021364252155), 'svensson fit, rmse 1.7bp'),
    ('humped', 'bootstrap'): ((0.08333333333333333, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0, 30.0),
        (0.029962562383046384, 0.0318726785967075, 0.034205815799324565, 0.03767619517905639, 0.04166657940308885, 0.043682724597625816, 0.04466905549912794, 0.04407151927869038, 0.042337518492044854, 0.040005097151752884, 0.038696376671964225),
        (), ''),
    ('humped', 'nelson_siegel'): ((0.08333333333333333, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0, 30.0),
        (0.030191916497241622, 0.03184455367016246, 0.03396764658524313, 0.03752193590057811, 0.041838354465731455, 0.04384181116825848, 0.04461925035149106, 0.04388149017862176, 0.042456837904625046, 0.03986792997784382, 0.038872925987764914),
        (0.0384990198344825, -0.00921176538905976, 0.03460838199524766, 1.8866330842455132), 'nelson_siegel fit, rmse 1.5bp'),
    ('humped', 'svensson'): ((0.08333333333333333, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0, 30.0),
        (0.03002838706659328, 0.03184725530339211, 0.03410190223309795, 0.03768656211291842, 0.041802741026833304, 0.043681951270647466, 0.04453094197422762, 0.04395402917792913, 0.04262788739017394, 0.03986198635502604, 0.03872465802469393),
        (0.03820481921798071, -0.00919599209894318, -8.944929279412289e-06, 0.02682746796519866, 0.643335597072324, 2.23911255312427), 'svensson fit, rmse 1.1bp'),
    ('synthetic', 'bootstrap'): ((0.08333333333333333, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0, 30.0),
        (0.06738487535856563, 0.06599713509523708, 0.06406375848118824, 0.06154218138216308, 0.057500848367669485, 0.054458306952076055, 0.05037206388282611, 0.047875171582039, 0.04566593756475562, 0.042817130022380946, 0.04178766024693492),
        (), 'Simulated Treasury par curve (Nelson-Siegel random walk) — no market data provider was used.'),
    ('synthetic', 'nelson_siegel'): ((0.08333333333333333, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0, 30.0),
        (0.06738487874155927, 0.06599713709064453, 0.06406375883822016, 0.06154217958258252, 0.05750084500065043, 0.0544583037392486, 0.05037206192982359, 0.04787517022160622, 0.04566593579892691, 0.04281712550877228, 0.041787654330906525),
        (0.04167598600715637, 0.02643483218257759, 0.00033208260831230936, 2.0001454356987467), 'Simulated Treasury par curve (Nelson-Siegel random walk) — no market data provider was used. nelson_siegel fit, rmse 0.0bp'),
    ('synthetic', 'svensson'): ((0.08333333333333333, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0, 30.0),
        (0.06738488057093492, 0.06599713724245113, 0.06406375750930783, 0.06154217780448766, 0.057500847416524864, 0.05445831163355265, 0.05037207534577066, 0.04787518157207658, 0.04566593859999178, 0.04281711637876799, 0.041787658622919985),
        (0.04167605011984483, 0.02643477098962911, 0.0003227602475961951, -2.8280290305819213e-07, 2.0008557856143865, 8.67959014992704), 'Simulated Treasury par curve (Nelson-Siegel random walk) — no market data provider was used. svensson fit, rmse 0.0bp'),
}


def legacy_curve_from_snapshot(snap, *, method="bootstrap"):
    """`curve_from_snapshot` exactly as it was before the new methods (copied verbatim)."""
    if method == "bootstrap":
        return C.bootstrap_par_curve(snap.tenors, snap.par_yields, date=snap.date,
                                     source=snap.source, note=snap.note)
    if method not in ("nelson_siegel", "svensson"):
        raise FICCError(f"Unknown curve method {method!r}.")
    fit = C.fit_nelson_siegel(snap.tenors, snap.par_yields, svensson=method == "svensson")
    grid = np.array(sorted(set(KEY_TENORS) | set(float(t) for t in snap.tenors)))
    fn = C.svensson if method == "svensson" else C.nelson_siegel
    curve = C.bootstrap_par_curve(grid, fn(grid, *fit.params), date=snap.date, source=snap.source)
    note = f"{snap.note} {fit.method} fit, rmse {fit.rmse / BP:.1f}bp".strip()
    return replace(curve, method=method, params=fit.params, note=note)


def hw_g(g0: float, g1: float, x: float) -> float:
    """Hagan & West's g on [0, 1], written out independently of the module's integral."""
    if g0 == 0 and g1 == 0:
        return 0.0
    if (g0 < 0 and -0.5 * g0 <= g1 <= -2 * g0) or (g0 > 0 and -0.5 * g0 >= g1 >= -2 * g0):
        return g0 * (1 - 4 * x + 3 * x * x) + g1 * (-2 * x + 3 * x * x)
    if (g0 < 0 and g1 > -2 * g0) or (g0 > 0 and g1 < -2 * g0):
        eta = (g1 + 2 * g0) / (g1 - g0)
        return g0 if x <= eta else g0 + (g1 - g0) * ((x - eta) / (1 - eta)) ** 2
    if (g0 > 0 and 0 > g1 > -0.5 * g0) or (g0 < 0 and 0 < g1 < -0.5 * g0):
        eta = 3 * g1 / (g1 - g0)
        return g1 + (g0 - g1) * ((eta - x) / eta) ** 2 if x < eta else g1
    eta = g1 / (g1 + g0)
    a = -g0 * g1 / (g0 + g1)
    if x <= eta:
        return a + (g0 - a) * ((eta - x) / eta) ** 2
    return a + (g1 - a) * ((x - eta) / (1 - eta)) ** 2


class CurveMethodAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snaps = snapshots()
        cls.built = {(name, m): C.curve_from_snapshot(snap, method=m)
                     for name, snap in cls.snaps.items() for m in C.CURVE_METHODS}

    # -- catalogue -------------------------------------------------------------- #
    def test_catalogue_offers_nine_named_methods_in_two_kinds(self):
        self.assertEqual(len(set(C.CURVE_METHODS)), 9)
        self.assertGreaterEqual(len(set(C.CURVE_METHODS) - set(LEGACY_METHODS)), 4)
        self.assertEqual(C.EXACT_METHODS | C.PARAMETRIC_METHODS, set(C.CURVE_METHODS))
        self.assertFalse(C.EXACT_METHODS & C.PARAMETRIC_METHODS)
        self.assertEqual(set(C.METHOD_NAMES), set(C.CURVE_METHODS))
        self.assertEqual(C.CURVE_METHODS[0], "bootstrap")           # the default stays first

    # -- every method on every curve -------------------------------------------- #
    def test_every_method_gives_a_well_formed_curve(self):
        grid = np.linspace(0.0, 30.0, 1201)
        for (name, m), curve in self.built.items():
            with self.subTest(curve=name, method=m):
                self.assertEqual(curve.method, m)
                if m != "bootstrap":                                   # the bootstrap keeps the input note
                    self.assertTrue(curve.note)
                self.assertTrue(np.all(np.isfinite(curve.zeros)))
                df = curve.df(grid)
                self.assertEqual(df[0], 1.0)
                self.assertTrue(np.all(df > 0))
                self.assertTrue(np.all(np.diff(df) < 0), "discount factors must fall with maturity")
                fwd = np.array([curve.fwd(t, t + 1.0) for t in np.linspace(0.0, 30.0, 121)])
                inst = np.array([curve.inst_fwd(t) for t in np.linspace(0.01, 30.0, 300)])
                self.assertTrue(np.all(np.isfinite(fwd)) and np.all(np.isfinite(inst)))
                rows = curve.table()
                expected = sorted(set(KEY_TENORS) | set(self.snaps[name].tenors))
                self.assertEqual([r["tenor"] for r in rows], expected)
                for r in rows:
                    self.assertTrue(all(math.isfinite(r[k]) for k in ("zero", "df", "par", "fwd_1y")))

    def test_exact_methods_reprice_every_input_within_a_tenth_of_a_bp(self):
        for (name, m), curve in self.built.items():
            if m in C.EXACT_METHODS:
                with self.subTest(curve=name, method=m):
                    worst = float(np.max(np.abs(misses(curve, self.snaps[name]))))
                    self.assertLess(worst, 0.1 * BP)
                    self.assertLess(worst, 1e-6 * BP)           # in practice: solver precision

    def test_parametric_methods_stay_within_the_stated_rmse(self):
        for (name, m), curve in self.built.items():
            if m in C.PARAMETRIC_METHODS:
                with self.subTest(curve=name, method=m):
                    snap = self.snaps[name]
                    fit = C.fit_parametric(m, snap.tenors, snap.par_yields)
                    self.assertLess(fit.rmse / BP, RMSE_BOUND_BP[m])
                    self.assertIn(f"rmse {fit.rmse / BP:.1f}bp", curve.note)
                    self.assertEqual(curve.params, fit.params)
                    rms = float(np.sqrt(np.mean(misses(curve, snap) ** 2)))
                    self.assertLess(rms / BP, RMSE_BOUND_BP[m])
                    self.assertEqual(curve.tenors, tuple(sorted(set(KEY_TENORS) | set(snap.tenors))))

    def test_results_are_deterministic(self):
        for (name, m), curve in self.built.items():
            with self.subTest(curve=name, method=m):
                again = C.curve_from_snapshot(self.snaps[name], method=m)
                self.assertEqual((again.tenors, again.zeros, again.params, again.note, again.pillars),
                                 (curve.tenors, curve.zeros, curve.params, curve.note, curve.pillars))

    def test_unknown_method_still_raises(self):
        snap = self.snaps["normal"]
        for bad in ("cubic", "", "NELSON_SIEGEL", "flat", "shifted", None):
            with self.subTest(method=bad), self.assertRaises(FICCError):
                C.curve_from_snapshot(snap, method=bad)
        with self.assertRaises(FICCError):
            C.parametric_function("bootstrap")

    def test_too_few_points_fail_clearly(self):
        two = CurveSnapshot("d", "T", (2.0, 10.0), (0.04, 0.045))
        for m in ("cubic_spline", "pchip", "nelson_siegel", "diebold_li", "svensson",
                  "bjork_christensen"):
            with self.subTest(method=m), self.assertRaises(FICCError):
                C.curve_from_snapshot(two, method=m)
        for m in ("bootstrap", "monotone_convex", "smith_wilson"):     # two quotes are enough
            self.assertLess(float(np.max(np.abs(misses(C.curve_from_snapshot(two, method=m), two)))),
                            1e-6 * BP)

    def test_sparse_grid_without_money_market_tenors(self):
        snap = CurveSnapshot("d", "T", (1.0, 2.0, 5.0, 10.0, 30.0), (0.047, 0.044, 0.042, 0.044, 0.046))
        for m in C.CURVE_METHODS:
            if m == "svensson":                                       # needs six points
                continue
            with self.subTest(method=m):
                curve = C.curve_from_snapshot(snap, method=m)
                self.assertTrue(np.all(np.diff(curve.df(np.linspace(0, 30, 301))) < 0))
                if m in C.EXACT_METHODS:
                    self.assertLess(float(np.max(np.abs(misses(curve, snap)))), 1e-6 * BP)
                    self.assertEqual(curve.table()[0]["tenor"], 1.0)  # no extrapolated rows

    def test_analyze_curve_runs_every_method(self):
        panel = synthetic_curve_panel(days=200, seed=11)
        for m in C.CURVE_METHODS:
            with self.subTest(method=m):
                rep = C.analyze_curve(panel, lookback=20, method=m)
                self.assertEqual(rep.curve.method, m)
                self.assertTrue(all(math.isfinite(v) for v in rep.descriptors.values()))
                self.assertEqual(rep.ns.method, m if m in C.PARAMETRIC_METHODS else "nelson_siegel")
                self.assertEqual(len(C.parametric_function(rep.ns.method)(np.array([1.0]), *rep.ns.params)), 1)

    def test_scenario_shifts_still_work_on_dense_curves(self):
        curve = self.built[("normal", "monotone_convex")]
        up = curve.shifted(10.0)
        self.assertEqual(up.pillars, curve.pillars)
        self.assertAlmostEqual(up.zero(7.3) - curve.zero(7.3), 10 * BP, places=12)
        kr = curve.key_rate_shifted(5.0, 10.0)
        self.assertAlmostEqual(kr.zero(5.0) - curve.zero(5.0), 10 * BP, places=12)
        self.assertAlmostEqual(kr.zero(10.0) - curve.zero(10.0), 0.0, places=12)

    # -- legacy results unchanged ----------------------------------------------- #
    def test_legacy_methods_are_bit_identical_to_the_previous_builder(self):
        for name, snap in self.snaps.items():
            for m in LEGACY_METHODS:
                with self.subTest(curve=name, method=m):
                    new, old = self.built[(name, m)], legacy_curve_from_snapshot(snap, method=m)
                    self.assertEqual(new, old)                         # every field, bit for bit
                    self.assertEqual(new.pillars, ())
                    rep_new = C.analyze_curve(synthetic_curve_panel(days=60, seed=7), method=m)
                    fit_old = C.fit_nelson_siegel(snap.tenors, snap.par_yields,
                                                  svensson=m == "svensson")
                    fit_new = C.fit_parametric("svensson" if m == "svensson" else "nelson_siegel",
                                               snap.tenors, snap.par_yields)
                    self.assertEqual((fit_new.params, fit_new.rmse, fit_new.method),
                                     (fit_old.params, fit_old.rmse, fit_old.method))
                    self.assertEqual(rep_new.ns.method, "svensson" if m == "svensson" else "nelson_siegel")

    def test_legacy_methods_match_values_recorded_before_the_change(self):
        for (name, m), (knots, zeros, params, note) in LEGACY.items():
            with self.subTest(curve=name, method=m):
                curve = self.built[(name, m)]
                self.assertEqual(curve.tenors, knots)
                self.assertEqual(curve.note, note)
                # Exact on the recording platform; a few ulps of slack for other BLAS/libm builds.
                np.testing.assert_allclose(curve.zeros, zeros, rtol=0, atol=1e-12 if m == "bootstrap" else 1e-9)
                np.testing.assert_allclose(curve.params, params, rtol=1e-7, atol=1e-9)

    # -- method-specific properties --------------------------------------------- #
    def test_hagan_west_sector_integrals(self):
        cases = [(-1.0, 1.0), (1.0, -1.0), (-1.0, 3.0), (2.0, -5.0), (2.0, -0.3), (-2.0, 0.3),
                 (1.0, 2.0), (-1.0, -0.5), (0.0, 1.0), (1.0, 0.0), (0.0, 0.0), (-0.4, 0.2)]
        h = 1e-6
        for g0, g1 in cases:
            with self.subTest(g0=g0, g1=g1):
                self.assertAlmostEqual(C._hw_g_integral(g0, g1, 1.0), 0.0, places=14)
                self.assertEqual(C._hw_g_integral(g0, g1, 0.0), 0.0)
                for x in np.linspace(0.01, 0.99, 37):
                    slope = (C._hw_g_integral(g0, g1, x + h) - C._hw_g_integral(g0, g1, x - h)) / (2 * h)
                    self.assertAlmostEqual(slope, hw_g(g0, g1, x), places=6)

    def test_monotone_convex_reproduces_a_linear_forward_curve(self):
        knots = np.array([0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0])
        zeros = 0.02 + 0.001 * knots                                     # f(t) = 2% + 0.2%·t
        h = 1e-6
        for a, b in zip(knots[:-2], knots[1:-1]):                          # interior intervals
            for s in np.linspace(a + 0.01, b - 0.01, 9):
                ld = C._hw_log_df(knots, zeros, np.array([s - h, s + h]))
                self.assertAlmostEqual(-(ld[1] - ld[0]) / (2 * h), 0.02 + 0.002 * s, places=8)
        self.assertTrue(np.allclose(C._hw_log_df(knots, zeros, knots), -zeros * knots, atol=1e-15))

    def test_monotone_convex_forwards_are_continuous_and_positive(self):
        knots = np.array([0.1, 1.0, 4.0, 9.0, 20.0, 30.0])                # a deliberately jagged
        zeros = np.array([0.081, 0.07, 0.044, 0.07, 0.04, 0.03])          # zero curve
        h = 1e-7

        def fwd(s):
            ld = C._hw_log_df(knots, zeros, np.array([s - h, s + h]))
            return -(ld[1] - ld[0]) / (2 * h)

        for k in knots[:-1]:
            self.assertLess(abs(fwd(k - 1e-5) - fwd(k + 1e-5)), 1e-5)     # no jump at a knot
        grid = np.linspace(1e-4, 30.0, 6000)
        self.assertGreaterEqual(float(np.min(-np.diff(C._hw_log_df(knots, zeros, grid)))), 0.0)
        curve = self.built[("humped", "monotone_convex")]
        self.assertGreater(len(curve.tenors), 300)                        # sampled monthly
        self.assertIn("Hagan-West", curve.note)

    def test_smith_wilson_kernel_assumptions_and_ufr_convergence(self):
        u = np.array([0.5, 1.0, 7.0, 30.0])
        w = C._sw_kernel(u, u, 0.1, math.log1p(0.033))
        self.assertTrue(np.allclose(w, w.T, rtol=0, atol=1e-18))
        self.assertTrue(np.all(np.linalg.eigvalsh(w) > 0))
        self.assertTrue(np.allclose(C._sw_kernel(np.array([0.0]), u, 0.1, 0.03), 0.0))
        curve = self.built[("normal", "smith_wilson")]
        self.assertEqual(curve.params, (C.SW_UFR, C.SW_ALPHA))
        self.assertEqual((C.SW_UFR, C.SW_ALPHA), (0.033, 0.10))
        self.assertIn("UFR 3.30% and alpha 0.1 assumed", curve.note)
        omega = math.log1p(C.SW_UFR)
        self.assertEqual(curve.tenors[-1], C.SW_HORIZON)
        gap30, gap59 = abs(curve.inst_fwd(30.5) - omega), abs(curve.inst_fwd(59.5) - omega)
        self.assertLess(gap59, gap30 / 5)                                 # bends toward the UFR
        self.assertLess(gap59, 10 * BP)
        other = C.smith_wilson_curve(UST_TENORS, CURVES["normal"], ufr=0.045, alpha=0.2)
        snap = self.snaps["normal"]
        self.assertLess(float(np.max(np.abs(misses(other, snap)))), 1e-6 * BP)
        self.assertGreater(other.zero(55.0), curve.zero(55.0))            # a higher UFR lifts the tail
        for bad in ({"alpha": 0.0}, {"ufr": float("nan")}):
            with self.assertRaises(FICCError):
                C.smith_wilson_curve(UST_TENORS, CURVES["normal"], **bad)

    def test_par_splines_follow_their_interpolants(self):
        from scipy.interpolate import CubicSpline
        t, y = np.array(UST_TENORS), np.array(CURVES["humped"])
        bonds = t >= 1.0                       # money-market quotes are not splined with the bonds
        natural = CubicSpline(t[bonds], y[bonds], bc_type="natural")
        spline, pchip = self.built[("humped", "cubic_spline")], self.built[("humped", "pchip")]
        for s in np.arange(1.0, 30.01, 0.5):
            self.assertAlmostEqual(spline.par_rate(s), float(natural(s)), places=11)
        for lo, hi, ylo, yhi in zip(t[3:-1], t[4:], y[3:-1], y[4:]):       # no overshoot (PCHIP)
            for s in np.arange(lo, hi + 1e-9, 0.5):
                self.assertGreaterEqual(pchip.par_rate(s), min(ylo, yhi) - 1e-12)
                self.assertLessEqual(pchip.par_rate(s), max(ylo, yhi) + 1e-12)
        kinked = (0.052, 0.051, 0.050, 0.047, 0.044, 0.043, 0.042, 0.043, 0.044, 0.047, 0.046)
        pc = C.par_spline_curve(UST_TENORS, kinked, kind="pchip")
        self.assertLessEqual(pc.par_rate(25.0), 0.047 + 1e-12)            # stays inside 20y-30y quotes
        with self.assertRaises(FICCError):
            C.par_spline_curve(UST_TENORS, kinked, kind="akima")

    def test_diebold_li_fixed_lambda_and_ols(self):
        from core.ficc.curve_models import DL_LAMBDA_YEARLY
        self.assertEqual(C.DIEBOLD_LI_LAMBDA, DL_LAMBDA_YEARLY)
        self.assertAlmostEqual(C.DIEBOLD_LI_LAMBDA, 0.7308, places=12)
        tau = 1.0 / C.DIEBOLD_LI_LAMBDA
        exact = C.nelson_siegel(np.array(UST_TENORS), 0.045, -0.012, 0.02, tau)
        fit = C.fit_diebold_li(UST_TENORS, exact)
        self.assertLess(fit.rmse, 1e-12)
        np.testing.assert_allclose(fit.params, (0.045, -0.012, 0.02, tau), atol=1e-10)
        self.assertEqual(fit.method, "diebold_li")

    def test_bjork_christensen_nests_and_never_loses_to_nelson_siegel(self):
        t = np.array(UST_TENORS)
        exact = C.bjork_christensen(t, 0.045, -0.02, 0.01, 0.008, 2.5)
        self.assertLess(C.fit_bjork_christensen(t, exact).rmse, 0.05 * BP)
        self.assertTrue(np.allclose(C.bjork_christensen(t, 0.04, -0.01, 0.02, 0.0, 2.0),
                                    C.nelson_siegel(t, 0.04, -0.01, 0.02, 2.0)))
        for name, snap in self.snaps.items():
            with self.subTest(curve=name):
                bc = C.fit_bjork_christensen(snap.tenors, snap.par_yields)
                ns = C.fit_nelson_siegel(snap.tenors, snap.par_yields)
                self.assertLessEqual(bc.rmse, ns.rmse + 1e-15)

    # -- wiring ------------------------------------------------------------------ #
    def test_rates_request_accepts_every_method_and_rejects_others(self):
        from core.research.rates_analysis import RatesRequest
        for m in C.CURVE_METHODS:
            RatesRequest(method=m).validate()
        with self.assertRaises(ValueError):
            RatesRequest(method="cubic").validate()

    def test_rates_page_lists_and_explains_every_method_in_korean(self):
        from core.i18n import LocaleContext
        from ui import rates_page
        ko = LocaleContext("ko_KR")
        self.assertEqual([k for k, _ in rates_page._METHODS], list(C.CURVE_METHODS))
        self.assertEqual(set(rates_page._METHOD_TEXT), set(C.CURVE_METHODS))
        for text in [n for _, n in rates_page._METHODS] + list(rates_page._METHOD_TEXT.values()):
            if text not in ("Smith-Wilson", "Nelson-Siegel", "Svensson", "Björk-Christensen"):
                self.assertNotEqual(ko.text(text), text, text)              # a Korean caption exists
        for text in rates_page._KIND_TEXT.values():
            self.assertNotEqual(ko.text(text), text)

    def test_rates_page_hides_the_source_and_explains_the_chosen_method(self):
        from core.i18n import LocaleContext
        from ui import rates_page
        from ui.localization import translate_controls

        class Page:
            qg_locale = LocaleContext("ko_KR")
            def update(self): pass
            def run_thread(self, fn): fn()

        view = rates_page.build_rates_page(Page())
        translate_controls(view, Page.qg_locale)
        tool, source, run = view.controls[1].controls[:3]
        self.assertFalse(source.visible)                                  # issue 12: no source selector
        self.assertEqual(source.value, "auto")
        self.assertIn("auto", [o.key for o in source.options])
        self.assertEqual(run.content, "실행")
        method = view.controls[2].controls[0].controls[0]
        info = view.controls[2].controls[1]
        texts = lambda: [c.value for c in (info.content.controls[0].controls[0], info.content.controls[1])]
        self.assertEqual(texts()[0], "부트스트랩")
        method.value = "smith_wilson"
        method.on_select(SimpleNamespace(control=method))
        self.assertEqual(texts()[0], "Smith-Wilson")
        self.assertIn("3.30%", texts()[1])
        self.assertIn("가정", texts()[1])                                  # the UFR is an assumption
        for block in view.controls[2:6]:                                  # no helper lines: one baseline
            for field in block.controls[0].controls:
                self.assertIsNone(getattr(field, "helper", None))
                self.assertFalse(getattr(field, "expand", False))
        source.value = "synthetic"
        view.controls[2].controls[0].controls[1].value = "abc"
        run.on_click(None)
        host = view.controls[-1].controls[0]
        self.assertIn("숫자로 읽을 수 없습니다", host.controls[0].content.controls[1].value)

    def test_korean_shape_and_regime_words_match_the_native_app(self):
        from quantgen_desktop.rates_narrative import REGIMES, SHAPES
        from ui import rates_page
        self.assertEqual(rates_page._SHAPES_KO, SHAPES)
        self.assertEqual(rates_page._REGIMES_KO, REGIMES)


if __name__ == "__main__":
    unittest.main()
