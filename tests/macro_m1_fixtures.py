"""M1 package D — fixture tooling, golden registry, acquisition register, owner scripts (TASK-M1-01, TASK-M1-21,
TASK-M1-22; G-POST-01 data rows; G-DSR-01 / T-DSR-01; the T-PBO-01 noise control; T-RO-02 record clause).

Hermetic: no network (the macro guard is armed around every test), tempfile only, module globals restored in
`finally`. A clause that needs absent reference data raises NotRun("REFDATA: <file>") naming each missing file; one
that needs the owner raises NotRun("OWNER: ...").
"""
from __future__ import annotations

import ast
import contextlib
import csv
import fnmatch
import io
import json
import math
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import scipy.stats as sps

from core.quant import validate as V
from docs import kis_quote_check as KQ
from docs import macro_fixtures as MF
from tests import golden_tools as G
from tests.acceptance import _code_only
from tests.notrun import FIXTURES, MANIFEST, NotRun, load_manifest, require_fixture

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "tests" / "macro_registry.csv"
ACQUISITION = FIXTURES / "ACQUISITION.csv"
ACQ_COLUMNS = ("series", "source", "depth", "needed_by", "licence", "owner", "md5", "fixture")
SPEC_ACQ_ROWS = ("KRX official KOSPI daily closes, Saturday sessions included", "KODEX 200 PDF history",
                 "French daily Mkt-RF and RF", "The ECOS code of BOK_CALL_RATE", "USD_LIVE_PROXY (named, default DX-Y.NYB)",
                 "The 16:00 ET VIX / VIX3M snapshot source", "The hyperscaler list",
                 "JPX, SSE, HKEX, TWSE, CME and Cboe calendars")                                    # L6026-6033 verbatim
FILE_OF = {fid: Path(rel).name for fid, rel, *_ in MF.REFERENCE_FILES}                           # F13 -> yahoo_KS11_...


def _registry_ids(prefix: str) -> list[str]:
    with REGISTRY.open(encoding="utf-8", newline="") as fh:
        return [r["test_id"] for r in csv.DictReader(fh) if r["test_id"].startswith(prefix)]


def _refdata(fids) -> None:
    """NotRun("REFDATA: ...") naming every absent fixture among `fids`; returns when all are present."""
    missing = []
    for fid in fids:
        name = FILE_OF.get(fid, fid)
        try:
            require_fixture(name)
        except NotRun as exc:
            missing.append(f"{fid} {name} ({exc.reason.split(': ', 1)[1]})")
    if missing:
        raise NotRun("REFDATA: " + "; ".join(missing))


# --------------------------------------------------------------------------- #
# Tolerance table and helpers (L5734-5738)
# --------------------------------------------------------------------------- #
def test_tolerance_table_self_test():
    """LEVEL1 / LEVEL2 verbatim; p-kind by value; Level 2 refuses kinds it has no tolerance for."""
    assert G.LEVEL1 == {"sharpe": 0.01, "mdd": 0.01, "window_return": 0.01, "weight": 0.02, "share": 0.03,
                        "exceedance": 0.003, "p_hi": 0.01,
                        "p_lo": 0.005, "z": 0.05, "es_pp": 0.002, "count_exact": 0, "count_boot": 1, "percentile": 5,
                        "qlike_ratio": 0.005, "se": 0.005, "vol_level": 0.001, "ratio": 0.01, "price": 0}
    assert G.LEVEL2 == {"sharpe": 0.03, "window_return": 0.02, "mdd": 0.02, "p": 0.02}
    assert G.tol("sharpe") == 0.01 and G.tol("sharpe", 2) == 0.03 and G.tol("p_lo", 2) == 0.02 and G.tol("price") == 0
    assert G.p_kind(0.05) == "p_hi" and G.p_kind(0.049) == "p_lo"
    assert G.within("sharpe", 0.641, 0.6505) and not G.within("sharpe", 0.641, 0.652)
    assert G.within("count_exact", 132, 132) and not G.within("count_exact", 133, 132) and G.within("count_boot", 72, 71)
    assert G.within("price", 7003.74, 7003.74) and not G.within("price", 7003.75, 7003.74)
    assert not G.within("sharpe", float("nan"), 0.6)
    for kind in ("weight", "share", "count_exact", "z", "es_pp"):
        try:
            G.tol(kind, 2)
            raise AssertionError(f"Level 2 must not assert {kind}")
        except ValueError:
            pass
    for bad in (("nope", 1), ("sharpe", 3)):
        try:
            G.tol(*bad)
            raise AssertionError(bad)
        except (KeyError, ValueError):
            pass
    G.assert_close(0.6723, 0.6723 + 0.0099, "sharpe", label="G-DSR-02/sr")
    try:
        G.assert_close(0.60, 0.6723, "sharpe", label="G-DSR-02/sr")
        raise AssertionError("assert_close must raise")
    except AssertionError as exc:
        assert "G-DSR-02/sr" in str(exc) and "0.6723" in str(exc)


def test_golden_helpers_class_and_floor():
    """Near a threshold a verdict is a class (G-KR-L10: p_ni 0.103 vs 0.10), away from it the point holds; p = 0 is '<1/B'."""
    assert G.near_threshold(0.103, 0.10, "p_hi") and not G.near_threshold(0.146, 0.10, "p_hi")
    G.assert_class(0.103, 0.10, "p_hi", "PASS", {"PASS", "INSUFFICIENT_DATA"}, point="PASS")
    G.assert_class(0.103, 0.10, "p_hi", "INSUFFICIENT_DATA", {"PASS", "INSUFFICIENT_DATA"}, point="PASS")
    G.assert_class(0.146, 0.10, "p_hi", "REJECT", {"REJECT", "INSUFFICIENT_DATA"}, point="REJECT")
    # the fallback raise sits in `else:`, outside the try, so a helper that accepts everything fails here
    for stat, verdict, needle in ((0.103, "REJECT", "not in"), (0.146, "INSUFFICIENT_DATA", "although")):
        try:
            G.assert_class(stat, 0.10, "p_hi", verdict, {"PASS", "INSUFFICIENT_DATA"}, point="PASS")
        except AssertionError as exc:
            assert verdict in str(exc) and needle in str(exc), str(exc)
        else:
            raise AssertionError(f"assert_class accepted {verdict} at stat {stat}")
    G.assert_p_floor(0.0, 2000)
    G.assert_p_floor(0.0004, 2000)
    try:
        G.assert_p_floor(0.0005, 2000)
    except AssertionError as exc:
        assert "1/B" in str(exc), str(exc)
    else:
        raise AssertionError("assert_p_floor accepted p = 1/B")


# --------------------------------------------------------------------------- #
# goldens.csv and ACQUISITION.csv integrity
# --------------------------------------------------------------------------- #
def test_goldens_csv_integrity():
    """Every registry G-* id has rows; enums valid; pending rows carry no value and a section 9.4 note; loader semantics."""
    table = G.load_goldens()
    missing = [g for g in _registry_ids("G-") if g not in table]
    assert not missing, f"registry golden ids without goldens.csv rows: {missing}"
    rows = [r for g in table.values() for r in g.rows]
    assert len(rows) > 1000 and len(table) >= 78
    pending = [r for r in rows if r.status == "pending"]
    assert {r.golden_id for r in pending} >= {f"P94-{n:02d}" for n in range(1, 18)}, "the 17 section 9.4 items (L5996-6014)"
    for r in pending:
        assert r.value is None and r.note.startswith("§9.4 item "), r
    pre = [r for r in rows if r.status == "pre_patch_pending"]
    assert {r.golden_id for r in pre} == {"G-KR-06", "G-KR-02b"} and all("§9.4 item 2" in r.note for r in pre), pre
    assert all(r.status == "reference" for r in table["G-MOM-07"].rows + table["G-LAD-01"].rows)
    for r in rows:
        if r.kind in ("verdict", "text"):
            assert r.value is None or isinstance(r.value, str), r
        elif isinstance(r.value, str):
            assert r.kind == "p_lo" and r.value.startswith("<"), r          # a p floor ("<1/B", "<0.001"), T-PZERO-01
        elif r.value is not None and not isinstance(r.value, float):
            raise AssertionError(r)
        if r.kind == "p_lo" and isinstance(r.value, float):
            assert r.value < 0.05, r
        if r.kind == "p_hi" and isinstance(r.value, float):
            assert 0.05 <= r.value <= 1.0, r
        if r.kind == "verdict" and r.value not in ("PASS", "FAIL", "outside"):
            assert set(r.value.split("|")) <= {"PASS", "REVISE", "REJECT", "INSUFFICIENT_DATA"}, r   # schema enum, L4007
        # +/- 0.03 is for bootstrap shares only (L5734): an exceedance rate or band is `exceedance` (+/- 0.3 pp, L5642),
        # a deterministic fraction (staleness, days on, years positive, plateau, max share) is a `ratio` (+/- 0.01)
        q = r.quantity.lower()
        if any(s in q for s in ("exceedance", "band lower", "band upper")):
            assert r.kind == "exceedance", r
        elif r.kind == "share":
            assert r.golden_id not in ("G-STALE-01", "G-YRS-01", "G-R08-01") and not any(
                s in q for s in ("days", "years positive", "plateau", "max share", "implied share", "vol-of-vol")), r
    g = G.golden("G-POST-01")
    assert g.want("kospi_close_2oct") == 7003.74 and g.row("rv20_2oct").runs_from == "M2" and "F13" in g.fixtures
    for gid, sub in (("G-KR-06", "sharpe"), ("G-KR-02b", "x2_70bp_dsr_2016_26"), ("G-LAD-04", "halts_with_stop"), ("P94-11", "value")):
        try:
            G.golden(gid).want(sub)
            raise AssertionError(f"{gid}/{sub} must raise NotRun")
        except NotRun as exc:
            assert exc.reason.startswith("PENDING: §9.4 item "), exc.reason
    assert G.golden("G-MOM-08").want("p_pw251") == G.P_FLOOR
    report = G.assert_golden("G-DSR-02", {"sr": 0.6723, "dsr_vs_unscaled": 0.2729, "T": 9233})
    assert len(report) == 3 and report[0][4] == 0.0
    try:
        G.assert_golden("G-DSR-02", {"sr": 0.70, "T": 9233})
        raise AssertionError("deviation must raise")
    except AssertionError as exc:
        assert "sr: got 0.7" in str(exc) and "T:" not in str(exc)
    assert G.assert_golden("G-MOM-08", {"p_pw251": (0.0, 2000), "years_positive": 0.71})
    try:
        G.golden("G-NOPE-99")
        raise AssertionError
    except KeyError:
        pass


def test_acquisition_csv_integrity():
    """The 8 section 9.5 rows verbatim plus every absent D.1 fixture; licence / owner / md5 blank; none is in the manifest."""
    with ACQUISITION.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        assert tuple(reader.fieldnames or ()) == ACQ_COLUMNS, reader.fieldnames
        rows = list(reader)
    series = [r["series"] for r in rows]
    assert series[:8] == list(SPEC_ACQ_ROWS), series[:8]
    fids = {tok for r in rows for tok in r["fixture"].split() if tok.startswith(("F", "U")) and tok[1:3].isdigit()}
    expected = {"F01", "F02", "F03", "F04-F06", "F07", "F08", "F09", "F10", "F11", "F12", "F13", "F14", "F15", "F16", "F17",
                "F18", "F19", "F20", "F21", "F22", "F23", "F24", "F25", "F27", "F28", "F29", "U1"}
    assert expected <= fids, sorted(expected - fids)
    listed = load_manifest()
    for r in rows:
        assert r["series"] and r["source"] and r["needed_by"], r
        assert not (r["licence"] or r["owner"] or r["md5"]), f"an open row with licence/owner/md5: {r}"
        for name in r["fixture"].split(" ", 1)[-1].split(";"):
            assert Path(name).name not in listed, f"{name} is both open in ACQUISITION.csv and listed in MANIFEST.csv"
    # every absent reference file the generator expects is an open row (by F-id)
    for fid in {f for f, *_ in MF.REFERENCE_FILES}:
        assert any(fid in tok or (fid in ("F04", "F05", "F06") and "F04-F06" in tok) for tok in fids), f"{fid} not registered"


def _fixture_gates():
    """(module path, test function, require_fixture call, module-level literal constants) for every test module."""
    for path in sorted((ROOT / "tests").glob("macro_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        consts = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                with contextlib.suppress(ValueError, SyntaxError):
                    consts[node.targets[0].id] = ast.literal_eval(node.value)
        for fn in tree.body:
            if isinstance(fn, ast.FunctionDef):
                for call in ast.walk(fn):
                    if isinstance(call, ast.Call) and getattr(call.func, "id", "") == "require_fixture" and call.args:
                        yield path, fn, call, consts


def test_every_required_fixture_is_generated_or_registered():
    """A `require_fixture` name is a D.1 generator output, an ACQUISITION.csv fixture or a manifest row; any other
    spelling stays NOT_RUN forever after `generate` + `freeze`, whatever data arrives."""
    with ACQUISITION.open(encoding="utf-8", newline="") as fh:
        acq = {Path(n).name for r in csv.DictReader(fh) for n in r["fixture"].split(" ", 1)[-1].split(";") if n}
    known = {Path(rel).name for _, rel, *_ in MF.REFERENCE_FILES} | set(load_manifest())
    bad, checked = [], 0
    for path, fn, call, consts in _fixture_gates():
        if any(k.arg == "manifest" for k in call.keywords):
            continue                                                  # the loader's own tests on a temp manifest
        loops = {n.target.id: n.iter for n in ast.walk(fn) if isinstance(n, ast.For) and isinstance(n.target, ast.Name)}
        arg = call.args[0]
        expr = loops.get(arg.id, arg) if isinstance(arg, ast.Name) else arg
        try:
            val = eval(compile(ast.Expression(expr), path.name, "eval"), {"__builtins__": {}}, dict(consts))
        except Exception:
            continue                                                  # a runtime name (FILE_OF lookup, manifest loop)
        for name in [val] if isinstance(val, str) else val:
            checked += 1
            if Path(name).name not in known and not any(fnmatch.fnmatch(Path(name).name, a) for a in acq):
                bad.append(f"{path.name}:{call.lineno} {name}")
    assert checked >= 30 and not bad, f"names no generator, ACQUISITION or manifest row produces ({checked} checked): {bad}"


test_every_required_fixture_is_generated_or_registered.test_ids = ["T-HERM-01"]


def test_no_golden_test_passes_on_its_fixture_gate_alone():
    """A test whose last statement is its `require_fixture` gate PASSES with nothing asserted once the file is listed.
    After the gate a test asserts, raises NotRun naming the input still missing, or fails as not implemented."""
    def gate_only(stmt):
        if isinstance(stmt, ast.For):
            return all(gate_only(s) for s in stmt.body)
        call = stmt.value if isinstance(stmt, ast.Expr) else None
        return isinstance(call, ast.Call) and getattr(call.func, "id", "") == "require_fixture"
    bare = sorted({f"{path.name}::{fn.name}" for path, fn, _call, _c in _fixture_gates()
                   if path.stem != "macro_m0_harness" and gate_only(fn.body[-1])})   # m0_harness tests the gate itself
    assert not bare, f"tests that pass on the fixture gate alone: {bare}"


test_no_golden_test_passes_on_its_fixture_gate_alone.test_ids = ["T-HERM-01"]


# --------------------------------------------------------------------------- #
# Look-ahead audit LA-02 ratchet (docs/nautilus_bridge/LOOKAHEAD_AUDIT_2026-11-04.md at 7749450, LA-02): the named
# REFDATA / OWNER point-in-time bodies, not whole modules (the rule above still lets other golden tests fail as not
# implemented after their gate)
# --------------------------------------------------------------------------- #
LA02_CONVERTED = (                              # each runs a real body once its fixture or calendar input arrives
    "macro_m1_calendars.py::test_print01_real_kospi_close_2026_03_09",
    "macro_m1_calendars.py::test_sat01_real_kospi_completeness_and_variance_ratio",
    "macro_m1_pit.py::test_avail_01_official_calendars_are_owner_signed",
    "macro_m7_cardp.py::test_placebo_01_positive_control_fixture_refdata",
    # part 2 (2026-11-10)
    "macro_m1_pit.py::test_g_post_01_m1_data_rows_refdata",
    "macro_m1_pit.py::test_print_01_real_kospi_close_refdata",
    "macro_m1_pit.py::test_stale_01_g_stale_01_reference_table_refdata",
    "macro_m1_pit.py::test_miss_01_cpi_yoy_3_353_refdata",
    "macro_m1_calendars.py::test_close02_on_the_real_signed_files_is_owner_input",
    "macro_m1_fixtures.py::test_g_post_01_m1_data_rows_refdata",
    "macro_m2_risk.py::test_vt_01_rv20_28_82_and_vt_0_694_on_2_oct_refdata",
    "macro_m2_risk.py::test_label_01_kospi_elevated_stressed_and_us_normal_refdata",
    "macro_m3_estimators.py::test_t_b5_01_kospi_golden_refdata",
)
LA02_REMAINING = {                              # not converted yet; a later part moves each up, so the list only shrinks
    "macro_m1_pit.py::test_fix_01_regeneration_at_level_1_tolerance_refdata": "T-FIX-01: council archive outside the repo",
    "macro_m1_calendars.py::test_regime01_full_range_expected_values_file": "T-REGIME-01: no ACQUISITION row for the file",
    "macro_m7_cardp.py::test_i05_full_sample_lag_audit_over_compliant_goldens_refdata": "I-05: LA-07 and LA-30 first",
    "macro_m8_forward.py::test_g_ref_01_s1_goldens_refdata": "G-REF-01: no product R-11 replay; owner inputs from 1997",
}
# Frozen at part 1 (2026-11-10); a part never edits LA02_SITES. LA02_CONVERTED_FLOOR holds every conversion made so
# far: a later part that converts a site moves it from LA02_REMAINING to LA02_CONVERTED, adds it here and raises
# LA02_FLOOR_SIZE to the floor's new size; nothing leaves the floor. So LA02_REMAINING only shrinks and LA02_CONVERTED
# only grows.
LA02_SITES = frozenset({
    "macro_m1_calendars.py::test_print01_real_kospi_close_2026_03_09",
    "macro_m1_calendars.py::test_sat01_real_kospi_completeness_and_variance_ratio",
    "macro_m1_pit.py::test_avail_01_official_calendars_are_owner_signed",
    "macro_m7_cardp.py::test_placebo_01_positive_control_fixture_refdata",
    "macro_m1_pit.py::test_fix_01_regeneration_at_level_1_tolerance_refdata",
    "macro_m1_pit.py::test_g_post_01_m1_data_rows_refdata",
    "macro_m1_pit.py::test_print_01_real_kospi_close_refdata",
    "macro_m1_pit.py::test_stale_01_g_stale_01_reference_table_refdata",
    "macro_m1_pit.py::test_miss_01_cpi_yoy_3_353_refdata",
    "macro_m1_calendars.py::test_close02_on_the_real_signed_files_is_owner_input",
    "macro_m1_calendars.py::test_regime01_full_range_expected_values_file",
    "macro_m1_fixtures.py::test_g_post_01_m1_data_rows_refdata",
    "macro_m2_risk.py::test_vt_01_rv20_28_82_and_vt_0_694_on_2_oct_refdata",
    "macro_m2_risk.py::test_label_01_kospi_elevated_stressed_and_us_normal_refdata",
    "macro_m3_estimators.py::test_t_b5_01_kospi_golden_refdata",
    "macro_m7_cardp.py::test_i05_full_sample_lag_audit_over_compliant_goldens_refdata",
    "macro_m8_forward.py::test_g_ref_01_s1_goldens_refdata",
})
LA02_CONVERTED_FLOOR = frozenset({
    "macro_m1_calendars.py::test_print01_real_kospi_close_2026_03_09",
    "macro_m1_calendars.py::test_sat01_real_kospi_completeness_and_variance_ratio",
    "macro_m1_pit.py::test_avail_01_official_calendars_are_owner_signed",
    "macro_m7_cardp.py::test_placebo_01_positive_control_fixture_refdata",
    # part 2 (2026-11-10)
    "macro_m1_pit.py::test_g_post_01_m1_data_rows_refdata",
    "macro_m1_pit.py::test_print_01_real_kospi_close_refdata",
    "macro_m1_pit.py::test_stale_01_g_stale_01_reference_table_refdata",
    "macro_m1_pit.py::test_miss_01_cpi_yoy_3_353_refdata",
    "macro_m1_calendars.py::test_close02_on_the_real_signed_files_is_owner_input",
    "macro_m1_fixtures.py::test_g_post_01_m1_data_rows_refdata",
    "macro_m2_risk.py::test_vt_01_rv20_28_82_and_vt_0_694_on_2_oct_refdata",
    "macro_m2_risk.py::test_label_01_kospi_elevated_stressed_and_us_normal_refdata",
    "macro_m3_estimators.py::test_t_b5_01_kospi_golden_refdata",
})
LA02_FLOOR_SIZE = 13                            # the floor's size after part 2; a later part raises it, never lowers it
_GATES = ("require_fixture", "_refdata")
_LA02_WORDS = ("unreachable", "not implemented")
_CONST_NODES = (ast.Constant, ast.BoolOp, ast.UnaryOp, ast.BinOp, ast.Compare, ast.Tuple, ast.List, ast.expr_context,
                ast.boolop, ast.unaryop, ast.operator, ast.cmpop)


def _la02_list_defects(converted, remaining) -> list[str]:
    """The two lists against the frozen sites and floor: they partition LA02_SITES, and LA02_CONVERTED holds the floor."""
    out = []
    conv, rem = set(converted), set(remaining)
    if conv & rem:
        out.append(f"listed as both converted and remaining: {sorted(conv & rem)}")
    if conv | rem != LA02_SITES:
        out.append(f"the lists differ from the 17 frozen sites: extra {sorted((conv | rem) - LA02_SITES)}, "
                   f"missing {sorted(LA02_SITES - conv - rem)}")
    if (not LA02_CONVERTED_FLOOR <= conv or len(conv) < len(LA02_CONVERTED_FLOOR)
            or len(LA02_CONVERTED_FLOOR) < LA02_FLOOR_SIZE):
        out.append(f"converted sites left LA02_CONVERTED: {sorted(LA02_CONVERTED_FLOOR - conv)} (the list only grows)")
    return out


def _exc_name(exc) -> str:
    target = exc.func if isinstance(exc, ast.Call) else exc
    return target.id if isinstance(target, ast.Name) else getattr(target, "attr", "")


def _constant_truth(test: ast.expr):
    """True / False for a test built from constants only (`if True:`, `if 1 == 1:`, `assert 0`), else None."""
    if not all(isinstance(n, _CONST_NODES) for n in ast.walk(test)):
        return None
    try:
        return bool(eval(compile(ast.Expression(test), "<la02>", "eval"), {"__builtins__": {}}, {}))
    except Exception:                                   # noqa: BLE001
        return None


def _always_run(stmts):
    """The statements that run whenever `stmts` runs: each one, and recursively the bodies of `with`, the `try` body and
    `finally`, and the live branch of an `if` / `while` whose test is a constant."""
    for st in stmts:
        yield st
        if isinstance(st, (ast.With, ast.AsyncWith)):
            yield from _always_run(st.body)
        elif isinstance(st, ast.Try):
            yield from _always_run(st.body)
            yield from _always_run(st.finalbody)
        elif isinstance(st, (ast.If, ast.While)):
            truth = _constant_truth(st.test)
            if truth is True:
                yield from _always_run(st.body)
            elif truth is False:
                yield from _always_run(st.orelse)


def _parking_defects(fn: ast.FunctionDef) -> list[str]:
    """A NotRun that runs whatever the inputs (at the top level, or under a constant `if`), an exception whose message
    says unreachable / not implemented (any exception class, any letter case), NotImplementedError, a constant-false
    assert."""
    out = []
    for st in _always_run(fn.body):
        if isinstance(st, ast.Raise) and st.exc is not None and _exc_name(st.exc) in ("NotRun", "require_owner"):
            out.append(f"line {st.lineno}: unconditional NotRun")
    for node in ast.walk(fn):
        if isinstance(node, ast.Raise) and node.exc is not None:
            text = " ".join(c.value for c in ast.walk(node.exc) if isinstance(c, ast.Constant) and isinstance(c.value, str))
            if _exc_name(node.exc) == "NotImplementedError" or any(w in text.lower() for w in _LA02_WORDS):
                out.append(f"line {node.lineno}: fails as unreachable / not implemented")
        if isinstance(node, ast.Assert) and _constant_truth(node.test) is False:
            out.append(f"line {node.lineno}: assert False")
    return out


def _la02_defects(fn: ast.FunctionDef, defs: dict) -> list[str]:
    """Why `fn` is not a convertible body: a parking form (`_parking_defects`) in it or in a module function it calls
    (followed through the module's own functions, so a gate helper such as `_official_calendar` is covered), or no
    `_check_*` body that asserts."""
    out = list(_parking_defects(fn))
    seen, todo = {fn.name}, [fn]
    while todo:
        for n in ast.walk(todo.pop()):
            name = n.func.id if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) else None
            if name in defs and name not in seen:
                seen.add(name)
                todo.append(defs[name])
                out += [f"helper {name}: {d}" for d in _parking_defects(defs[name])]
    checks = sorted({n.func.id for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                     and n.func.id.startswith("_check_")})
    if not checks:
        out.append("calls no _check_* body")
    for name in checks:
        if name not in defs or not any(isinstance(n, ast.Assert) for n in ast.walk(defs[name])):
            out.append(f"{name} is not a module function that asserts")
    return out


def test_la02_converted_pit_bodies_stay_convertible():
    """LA-02 ratchet (look-ahead audit 2026-11-04): a converted REFDATA / OWNER point-in-time test opens with its
    fixture gate or a computed owner check, never raises NotRun whatever the inputs (also not under a constant `if`,
    and not in a module helper it calls), never fails as unreachable or not implemented (any exception, any case), and
    runs a module `_check_*` body that asserts; each body is also shown to PASS and to FAIL on invented data next to it.
    The lists partition the 17 frozen sites (LA02_SITES), LA02_CONVERTED holds LA02_CONVERTED_FLOOR, and every remaining
    site must still be unconverted, so LA02_REMAINING only shrinks. 17 sites: the 18 the ⑨-1/2 scoping cited for LA-02,
    less macro_m1_fixtures.py::test_kis_quote_check_owner_record (T-RO-02, an owner live-quote record, not a PIT golden);
    the audit's own count of 19 is not reproduced."""
    defs_of: dict[str, dict] = {}

    def lookup(ref: str):
        module, name = ref.split("::")
        if module not in defs_of:
            tree = ast.parse((ROOT / "tests" / module).read_text(encoding="utf-8"))
            defs_of[module] = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
        return defs_of[module].get(name), defs_of[module]

    bad = _la02_list_defects(LA02_CONVERTED, LA02_REMAINING)
    for ref in LA02_CONVERTED:
        fn, defs = lookup(ref)
        if fn is None:
            bad.append(f"{ref}: missing")
            continue
        bad += [f"{ref}: {d}" for d in _la02_defects(fn, defs)]
        first_gate = next((n.lineno for n in ast.walk(fn) if isinstance(n, ast.Call)
                           and getattr(n.func, "id", "") in _GATES), None)
        notrun_lines = [n.lineno for n in ast.walk(fn) if isinstance(n, ast.Raise)
                        and getattr(getattr(n.exc, "func", n.exc), "id", "") == "NotRun"]
        if first_gate is not None and any(line < first_gate for line in notrun_lines):
            bad.append(f"{ref}: NotRun before its fixture gate")
    for ref in LA02_REMAINING:
        fn, defs = lookup(ref)
        if fn is None:
            bad.append(f"{ref}: listed as remaining but missing")
        elif not _la02_defects(fn, defs):
            bad.append(f"{ref}: converted; move it to LA02_CONVERTED and LA02_CONVERTED_FLOOR")
    assert not bad, bad


def test_la02_ratchet_refuses_the_old_forms():
    """The ratchet's rule on the forms LA-02 found and on the review's evasions (invented sources, parsed only): the
    gate followed by an 'unreachable' assertion (any exception class, any case), an unconditional NotRun (also under a
    constant `if`, or in a gate helper), a gate with nothing after it are refused; a gated `_check_*` body with a
    computed owner check passes. The lists: a converted site moved back to LA02_REMAINING, or a new remaining site, is
    refused."""
    def defects(src: str) -> list[str]:
        tree = ast.parse(src)
        defs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
        return _la02_defects(defs["test_x"], defs)
    gated = 'def test_x():\n    text = require_fixture("a.csv").read_text()\n    _check_x(text)\n{}\n' \
            'def _check_x(v):\n    assert v\n'
    assert defects('def test_x():\n    require_fixture("a.csv")\n    raise AssertionError("unreachable")\n')
    assert defects('def test_x():\n    require_fixture("a.csv")\n    raise AssertionError(f"{A} listed: golden assertion '
                   'not implemented")\n')
    assert defects('def test_x():\n    raise NotRun("REFDATA: a.csv absent")\n')
    assert defects('def test_x():\n    _refdata(["F13"])\n    raise NotRun("REFDATA: present but not wired")\n')
    assert defects('def test_x():\n    require_fixture("a.csv")\n    _check_x(1)\n\ndef _check_x(v):\n    return v\n')
    for tail in ('    if True:\n        raise NotRun("OWNER: parked")', '    if 1 == 1:\n        raise NotRun("OWNER: x")',
                 '    raise RuntimeError("unreachable")', '    raise AssertionError("Unreachable")',
                 '    raise ValueError("Not Implemented yet")', '    raise NotImplementedError', '    assert 0, "x"',
                 '    with open("f"):\n        raise NotRun("OWNER: x")'):
        assert defects(gated.format(tail)), tail
    helper = ('def test_x():\n    text = require_fixture("a.csv").read_text()\n    _check_x(text, _gate())\n\n'
              'def _gate():\n    waiting = []\n    if {}:\n        raise NotRun("OWNER: " + "; ".join(waiting))\n    return 1\n\n'
              'def _check_x(v, cal):\n    assert v\n')
    assert defects(helper.format("True")) == ["helper _gate: line 8: unconditional NotRun"], defects(helper.format("True"))
    assert defects(helper.format("waiting")) == [], defects(helper.format("waiting"))
    ok = ('def test_x():\n    text = require_fixture("a.csv").read_text()\n    if not text:\n'
          '        raise NotRun("OWNER: computed")\n    _check_x(text)\n\ndef _check_x(v):\n    assert v\n')
    assert defects(ok) == [], defects(ok)
    assert _la02_list_defects(LA02_CONVERTED, LA02_REMAINING) == []
    sat = "macro_m1_calendars.py::test_sat01_real_kospi_completeness_and_variance_ratio"
    back = _la02_list_defects([c for c in LA02_CONVERTED if c != sat], {**LA02_REMAINING, sat: "parked again"})
    assert back and "left LA02_CONVERTED" in back[0] and sat in back[0], back
    grown = _la02_list_defects(LA02_CONVERTED, {**LA02_REMAINING, "macro_m9_lab.py::test_new_refdata": "new"})
    assert grown and "extra ['macro_m9_lab.py::test_new_refdata']" in grown[0], grown


# --------------------------------------------------------------------------- #
# The first two real golden checks (SYNTH; reproduce on core/quant/validate.py)
# --------------------------------------------------------------------------- #
def test_g_dsr_01_reproduces_bldp():
    """BLdP worked example with the L2522 mapping: 0.9505 at N 46, 0.9004 at N 100 (paper inputs frozen in F30)."""
    fx = json.loads(require_fixture("bldp_dsr_example.json").read_text(encoding="utf-8"))
    m = fx["mapping"]
    sr = m["sr_annual"] / math.sqrt(m["periods_per_year"])
    se_obs = math.sqrt((1 - m["skew"] * sr + (m["kurtosis"] - 1) / 4 * sr ** 2) / (m["T"] - 1))
    assert abs(se_obs - math.sqrt((1 + 3 * sr + 9 / 4 * sr ** 2) / (m["T"] - 1))) < 1e-15     # the L2522 form
    sd_null = math.sqrt(m["sr_trials_variance_annual"] / m["periods_per_year"])
    got = {}
    for n, want in fx["expected"].items():
        hurdle = V.expected_max_sharpe(int(n), sd_null)                   # sd * e(N), validate.py L168
        got[n] = float(sps.norm.cdf((sr - hurdle) / se_obs))
        assert abs(got[n] - want) <= 5e-5, (n, got[n], want)              # printed precision, tighter than kind p_hi
    g = G.golden("G-DSR-01")
    assert round(got["46"], 4) == g.want("dsr_n46") and round(got["100"], 4) == g.want("dsr_n100")
    G.assert_golden("G-DSR-01", {"dsr_n46": got["46"], "dsr_n100": got["100"]})


test_g_dsr_01_reproduces_bldp.test_ids = ["G-DSR-01", "T-DSR-01"]


def test_t_pbo_01_noise_control_reproduces():
    """QF3's recipe exactly (L2632): first draw of default_rng(11), normal(0, 0.01, (2600, 10)), 2,592 rows, 16 blocks,
    Sharpe ddof 1 -> PBO 0.536 +/- 0.001. The 200-panel calibration and the KOSPI grid PBO 0.28 are freeze tier (M7)."""
    panel = np.random.default_rng(11).normal(0.0, 0.01, size=(2600, 10))[:2592]
    pbo = V.pbo_cscv(panel, S=16)
    assert pbo["n_splits"] == 12870 and abs(pbo["pbo"] - 0.536) <= 0.001, pbo
    assert abs(pbo["pbo"] - 0.5359) <= 1e-4, pbo["pbo"]


test_t_pbo_01_noise_control_reproduces.test_ids = ["T-PBO-01"]


# --------------------------------------------------------------------------- #
# G-POST-01 data rows (REFDATA) and the arithmetic identities (SYNTH)
# --------------------------------------------------------------------------- #
# G-POST-01's M1 rows on the 2-Oct decision (look-ahead audit LA-02, part 2). docs/macro_fixtures.py writes each file as
# the reference file's own columns followed by the section 4.1 provenance columns. ACQUISITION.csv and the spec name no
# reference column, so the layout the body reads is declared here, an input contract the owner confirms at ⑨-2:
#   F01 krx_kospi_official_close_1997-01-03_2026-10-02.csv  the T-PRINT-01 / T-SAT-01 layout of part 1
#                                                           (tests/macro_m1_calendars.py F01_COLUMNS): `close`
#   F13 yahoo_KS11_1996-12_2026-10-02.csv                    `close`
#   F16 yahoo_KRWX_2004_2026-10-01.csv                       `close`
#   F27 krx_005930_000660_closes_mcap.csv                    long form: `code` (005930 or 000660) and its `close`; the
#                                                           other columns (the market caps) are not read
# Every row carries the series_id, value_status and available_at_source that docs/macro_fixtures.REFERENCE_FILES gives
# its file (F27: either of its two series ids), obs_date = session_date (ISO), and obs_utc / available_at_utc written
# YYYY-MM-DDTHH:MM:SSZ. F01, F13 and F16 hold one row per date and F27 one per code and date, in date order. F20
# (results/QX_DLA_postpatch.csv, the result table the rows were printed from) is gated with the others because
# goldens.csv lists it for kospi_close_2oct; its layout is not declared and the body does not read it (T-FIX-01
# regenerates it).
GPOST_READ = ("F01", "F13", "F16", "F27")
GPOST_COLUMNS = ("close", "series_id", "obs_date", "session_date", "obs_utc", "available_at_utc", "available_at_source",
                 "value_status")
GPOST_F27_CODES = ("005930", "000660")     # REFERENCE_FILES F27; G-POST-01/samsung_close_2oct and hynix_close_2oct
_GPOST_PROVENANCE = {fid: (tuple(series.split(";")), status, source)
                     for fid, _rel, series, status, source, *_rest in MF.REFERENCE_FILES}
# The decision: the KRX close of 2 Oct 2026 (goldens.csv G-POST-01 quantities "... 2 Oct 2026"), scheduled at 06:30:00Z
# (spec L1289) and stamped 06:30:30Z, close_print_bound_utc('KR', 2026-10-02) (L2096, L6278). A datum enters it only if
# its available_at_utc is at or before that instant (L539); goldens.csv times every M1 row COMPLIANT.
GPOST_DAY = date(2026, 10, 2)
GPOST_CLOSE_UTC = datetime(2026, 10, 2, 6, 30, tzinfo=timezone.utc)
GPOST_DECISION_UTC = datetime(2026, 10, 2, 6, 30, 30, tzinfo=timezone.utc)
GPOST_KRWX_LAST = date(2026, 10, 1)     # G-POST-01/krwx_last_row "KRW=X last row (1 Oct 2026)": the provisional 2-Oct
                                        # row is dropped (spec L5834, L6291)
GPOST_PEAK = (date(2026, 6, 22), 9114.55)   # G-POST-01/drawdown_from_peak "drawdown from the 9,114.55 peak (22 Jun
                                            # 2026)"; spec L5821
GPOST_SMA_N = 200                       # G-POST-01/close_over_200d note: "mean of last 200 closes incl. 2 Oct"
GPOST_DLOG_N = 20                       # G-POST-01/krwx_dlog20 "KRW=X 20-observation dlog" (spec L5834)
# The previous visible KS11 row must be the previous KRX session of 2 Oct (G-POST-01/kospi_return_2oct note "7,003.74 /
# prev close - 1") on the signed KRX clock files, read on the fortnight to 2 Oct through the part-1 owner gate
# tests.macro_m1_calendars._official_calendar (as tests/macro_m1_pit.py reads it; the shipped holidays_KRX covers 2026).
GPOST_CAL_SPAN = (GPOST_DAY - timedelta(days=14), GPOST_DAY)


def _gpost_utc(name: str, text: str) -> datetime:
    if not text.endswith("Z"):
        raise AssertionError(f"{name}: instant {text!r} is not written YYYY-MM-DDTHH:MM:SSZ")
    return datetime.fromisoformat(text[:-1]).replace(tzinfo=timezone.utc)


def _gpost_rows(fid: str, text: str) -> list[dict]:
    """One G-POST-01 fixture in its declared layout as {date, close, obs_utc, available_at_utc[, code]} rows;
    AssertionError on any departure from it (also a row available before its own observation instant)."""
    name, (series, status, source) = FILE_OF[fid], _GPOST_PROVENANCE[fid]
    reader = csv.DictReader(io.StringIO(text))
    missing = [c for c in GPOST_COLUMNS + (("code",) if fid == "F27" else ()) if c not in (reader.fieldnames or ())]
    assert not missing, f"{name}: declared columns {missing} absent (header {reader.fieldnames})"
    rows: list[dict] = []
    for line, raw in enumerate(reader, start=2):
        where = f"{name} line {line}"
        assert raw["series_id"] in series and (raw["value_status"], raw["available_at_source"]) == (status, source), (
            f"{where}: not a {'/'.join(series)} / {status} / {source} row")
        d = date.fromisoformat(raw["session_date"])
        assert date.fromisoformat(raw["obs_date"]) == d, f"{where}: obs_date != session_date"
        close = float(raw["close"])
        assert math.isfinite(close) and close > 0, f"{where}: close {raw['close']!r}"
        row = {"date": d, "close": close, "obs_utc": _gpost_utc(name, raw["obs_utc"]),
               "available_at_utc": _gpost_utc(name, raw["available_at_utc"])}
        assert row["available_at_utc"] >= row["obs_utc"], (
            f"{where}: available_at_utc {raw['available_at_utc']} before obs_utc {raw['obs_utc']}")
        if fid == "F27":
            assert raw["code"] in GPOST_F27_CODES, f"{where}: code {raw['code']!r} not in {GPOST_F27_CODES}"
            row["code"] = raw["code"]
            key, prev = (d, raw["code"]), [(r["date"], r["code"]) for r in rows[-2:]]
            assert not rows or (rows[-1]["date"] <= d and key not in prev), f"{where}: rows out of date order or repeated"
        else:
            assert not rows or rows[-1]["date"] < d, f"{where}: rows out of date order or repeated"
        rows.append(row)
    assert rows, f"{name}: no rows"
    return rows


def _check_g_post_01(f01: list[dict], f13: list[dict], f16: list[dict], f27: list[dict], cal) -> dict:
    """G-POST-01's M1 rows (goldens.csv, runs_from M1) on the 2-Oct decision. Each file is read as of 06:30:30Z: a row
    whose available_at_utc is later is not visible (spec L539), and no visible row may be dated after 2 Oct. The 2-Oct
    KOSPI rows of F13 and F01 and the 2-Oct Samsung and SK hynix rows of F27 are each the one visible row of that day,
    stamped at the scheduled close 06:30:00Z: an intraday print is not a close (the pre-patch 6,943.66 came from a file
    written at 10:56 KST, L6286). The previous visible KS11 row is dated the previous KRX session of the signed calendar
    `cal` (`clocks.prev_session`). KRW=X's last visible row is 1 Oct. Then every M1 row at Level 1 against goldens.csv:
    the close (F13, and F01's official close), the return on the previous visible close, the drawdown from the highest
    visible close, the close over the mean of the last 200 visible closes, the two stock closes, KRW=X's last close and
    its log change over 20 observations; and the peak is 9,114.55 on 22 Jun 2026. Returns the values."""
    from core.calendars import clocks
    def visible(rows):
        return [r for r in rows if r["available_at_utc"] <= GPOST_DECISION_UTC]

    def close_of(rows, label):
        on_day = [r for r in visible(rows) if r["date"] == GPOST_DAY]
        assert len(on_day) == 1, (f"G-POST-01: {len(on_day)} {label} rows of {GPOST_DAY} visible at "
                                  f"{GPOST_DECISION_UTC:%H:%M:%S}Z; exactly one close is read (spec L539)")
        assert on_day[0]["obs_utc"] == GPOST_CLOSE_UTC, (
            f"G-POST-01: the {label} row of {GPOST_DAY} is not the close: obs_utc {on_day[0]['obs_utc']:%H:%M:%S}Z != "
            "the scheduled close 06:30:00Z (spec L1289; the pre-patch 6,943.66 was an intraday print, L6286)")
        return on_day[0]["close"]

    for label, rows in (("KOSPI_OFFICIAL_CLOSE", f01), ("KS11", f13), ("KRWX", f16), ("005930 / 000660", f27)):
        late = [r["date"] for r in visible(rows) if r["date"] > GPOST_DAY]
        assert not late, f"G-POST-01: a {label} row of {late[0]} is visible at the {GPOST_DAY} decision (look-ahead; L539)"
    close = close_of(f13, "KS11")
    ks = visible(f13)                                      # ends on 2 Oct: one visible row that day and none after it
    assert len(ks) >= GPOST_SMA_N, f"G-POST-01: {len(ks)} visible KS11 rows, fewer than the {GPOST_SMA_N} of close_over_200d"
    prev_day = clocks.prev_session("KR", GPOST_DAY, cal=cal)
    assert ks[-2]["date"] == prev_day, (
        f"G-POST-01: the previous visible KS11 row is dated {ks[-2]['date']}, not the previous KRX session {prev_day} "
        "(G-POST-01/kospi_return_2oct is the return on the previous close)")
    peak = max(ks, key=lambda r: r["close"])
    kx = visible(f16)
    assert kx and kx[-1]["date"] == GPOST_KRWX_LAST, (
        f"G-POST-01: the last KRW=X row visible at the {GPOST_DAY} decision is {kx[-1]['date'] if kx else None}, not "
        f"{GPOST_KRWX_LAST} (the provisional 2-Oct row is dropped; G-POST-01/krwx_last_row)")
    assert len(kx) > GPOST_DLOG_N, f"G-POST-01: {len(kx)} visible KRW=X rows, too few for a {GPOST_DLOG_N}-observation dlog"
    window = [r["close"] for r in ks[-GPOST_SMA_N:]]
    got = {"kospi_close_2oct": close,
           "kospi_return_2oct": close / ks[-2]["close"] - 1.0,
           "drawdown_from_peak": close / peak["close"] - 1.0,
           "close_over_200d": close / (sum(window) / len(window)),
           "samsung_close_2oct": close_of([r for r in f27 if r["code"] == "005930"], "005930"),
           "hynix_close_2oct": close_of([r for r in f27 if r["code"] == "000660"], "000660"),
           "krwx_last_row": kx[-1]["close"],
           "krwx_dlog20": math.log(kx[-1]["close"] / kx[-1 - GPOST_DLOG_N]["close"])}
    m1 = {r.sub_id for r in G.golden("G-POST-01").rows if r.runs_from == "M1"}
    assert set(got) == m1, f"G-POST-01: goldens.csv M1 rows {sorted(m1)} != the replayed rows {sorted(got)}"
    official = close_of(f01, "KOSPI_OFFICIAL_CLOSE")
    print(f"PRINTED G-POST-01 M1 rows on {GPOST_DAY}: " + ", ".join(f"{k} {v:.6g}" for k, v in got.items())
          + f"; F01 official close {official}; peak {peak['close']} on {peak['date']}")
    G.assert_golden("G-POST-01", got)
    try:
        G.assert_golden("G-POST-01", {"kospi_close_2oct": official})
    except AssertionError as exc:
        raise AssertionError(f"G-POST-01 on the F01 official close: {exc}") from None
    assert (peak["date"], peak["close"]) == GPOST_PEAK, (
        f"G-POST-01: the peak of the visible KS11 closes is {peak['close']} on {peak['date']}, not 9114.55 on 2026-06-22 "
        "(G-POST-01/drawdown_from_peak)")
    return {**got, "kospi_official_close_2oct": official, "peak": (peak["date"], peak["close"])}


def test_g_post_01_m1_data_rows_refdata():
    """The M1 rows (close, return, drawdown, 200-day ratio, Samsung / SK hynix closes, KRW=X) need F01/F13/F16/F20/F27:
    NotRun naming each absent file; once all are listed, F01, F13, F16 and F27 are read in their declared layouts, NotRun
    (OWNER) while the signed KRX clock files do not cover the fortnight to 2 Oct (computed from the files by
    tests.macro_m1_calendars._official_calendar), and `_check_g_post_01` replays the rows on the 2-Oct decision at Level
    1 against goldens.csv (look-ahead audit LA-02, part 2: the body used to raise NotRun after the gate whatever the
    files held)."""
    from tests.macro_m1_calendars import _official_calendar
    g = G.golden("G-POST-01")
    m1 = [r for r in g.rows if r.runs_from == "M1"]
    assert {r.sub_id for r in m1} >= {"kospi_close_2oct", "kospi_return_2oct", "close_over_200d", "samsung_close_2oct",
                                      "hynix_close_2oct", "krwx_last_row", "krwx_dlog20"}
    fids = sorted({f for r in m1 for f in r.fixtures})
    assert fids == ["F01", "F13", "F16", "F20", "F27"], fids
    _refdata(fids)
    rows = {fid: _gpost_rows(fid, require_fixture(FILE_OF[fid]).read_text(encoding="utf-8")) for fid in GPOST_READ}
    _check_g_post_01(rows["F01"], rows["F13"], rows["F16"], rows["F27"], _official_calendar(*GPOST_CAL_SPAN))


test_g_post_01_m1_data_rows_refdata.test_ids = ["G-POST-01"]


def _gpost_weekdays(end: date, n: int) -> list[date]:
    out, d = [], end
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d -= timedelta(days=1)
    return out[::-1]


def _gpost_invented() -> dict[str, list[tuple]]:
    """Invented rows (no KRX, Yahoo or QX data) on which every M1 row of G-POST-01 lands on its goldens.csv value:
    260 weekday KS11 closes to 2 Oct 2026, flat but for the 9,114.55 peak on 22 Jun 2026, the previous close set from
    kospi_return_2oct and the flat level from close_over_200d; F01's last five of them; 40 weekday KRW=X closes to
    1 Oct, flat at krwx_dlog20 above the last one; the stock closes of 1 and 2 Oct. KRX rows are stamped at the KRX close
    (06:30:00Z / 06:30:30Z), KRW=X rows at 21:00Z of their day."""
    g = G.golden("G-POST-01")
    close, prev = g.want("kospi_close_2oct"), round(g.want("kospi_close_2oct") / (1.0 + g.want("kospi_return_2oct")), 2)
    flat = round((GPOST_SMA_N * close / g.want("close_over_200d") - GPOST_PEAK[1] - prev - close) / (GPOST_SMA_N - 3), 2)
    days = _gpost_weekdays(GPOST_DAY, 260)
    level = {**{d: flat for d in days}, GPOST_PEAK[0]: GPOST_PEAK[1], days[-2]: prev, GPOST_DAY: close}

    def kr(d):
        return datetime(d.year, d.month, d.day, 6, 30, tzinfo=timezone.utc), datetime(d.year, d.month, d.day, 6, 30, 30,
                                                                                     tzinfo=timezone.utc)
    last = g.want("krwx_last_row")
    fx_flat = round(last / math.exp(g.want("krwx_dlog20")), 2)
    fx = [(d, last if d == GPOST_KRWX_LAST else fx_flat) for d in _gpost_weekdays(GPOST_KRWX_LAST, 40)]
    stock = {(GPOST_DAY, "005930"): g.want("samsung_close_2oct"), (GPOST_DAY, "000660"): g.want("hynix_close_2oct")}
    return {"F01": [(d, level[d], *kr(d)) for d in days[-5:]],
            "F13": [(d, level[d], *kr(d)) for d in days],
            "F16": [(d, c, datetime(d.year, d.month, d.day, 21, tzinfo=timezone.utc),
                     datetime(d.year, d.month, d.day, 21, tzinfo=timezone.utc)) for d, c in fx],
            "F27": [(d, stock.get((d, code), base), *kr(d), code) for d in days[-2:]
                    for code, base in (("005930", 275000.0), ("000660", 1830000.0))]}


def _gpost_csv(fid: str, rows) -> str:
    """(date, close, obs_utc, available_at_utc[, code]) rows written in the declared layout of `fid`, in memory."""
    series, status, source = _GPOST_PROVENANCE[fid]
    buf = io.StringIO()
    out = csv.writer(buf, lineterminator="\n")
    out.writerow(("date",) + (("code",) if fid == "F27" else ()) + GPOST_COLUMNS)
    for d, close, obs, avail, *code in rows:
        sid = series[GPOST_F27_CODES.index(code[0])] if code else series[0]
        out.writerow((d.isoformat(), *code, repr(close), sid, d.isoformat(), d.isoformat(),
                      obs.strftime("%Y-%m-%dT%H:%M:%SZ"), avail.strftime("%Y-%m-%dT%H:%M:%SZ"), source, status))
    return buf.getvalue()


def _gpost_fails(fn, needle: str) -> str:
    try:
        fn()
    except AssertionError as exc:
        assert needle in str(exc), f"expected {needle!r} in: {exc}"
        return str(exc)
    raise AssertionError(f"expected an AssertionError naming {needle!r}")


def test_g_post_01_body_passes_and_fails_on_invented_rows():
    """LA-02 part 2: the G-POST-01 M1 body can PASS and can FAIL. Invented rows in the declared layouts (no KRX, Yahoo or
    QX data) built to the goldens.csv values pass. It fails, naming the clause, when: a 2-Oct row is not visible at
    06:30:30Z or is an intraday print (F13, F01, F27); a later row is visible; the KS11 close, the F01 official close,
    the previous close, the peak (beyond and within the drawdown tolerance, or on another day), the flat level, a stock
    close, KRW=X's last close or its row 20 observations back is off; the previous visible KS11 row is not 1 Oct (that
    row missing with 30 Sep at its level, or available only at 07:00Z); the provisional 2-Oct KRW=X row is visible;
    there are too few KS11 or KRW=X rows; and, at the layout, a declared column is absent, a row is not of its file's
    series and status, rows are out of order, or a row is available before its obs_utc. The row 201 closes back is
    outside the 200-close window (its level does not move the ratio) and the row 200 back inside it. The calendar is
    the calendars module's synthetic signed set, through the owner gate. While a fixture is absent, the real test's
    REFDATA reason names it."""
    from tests.macro_m1_calendars import F01_COLUMNS, _official_calendar, _official_calendar_on, drafts_set, fixture_set
    assert GPOST_COLUMNS == F01_COLUMNS                     # one declared F01 layout (part 1)
    inv = _gpost_invented()
    texts = {fid: _gpost_csv(fid, inv[fid]) for fid in GPOST_READ}
    cal = _official_calendar_on(*GPOST_CAL_SPAN, fixture_set())
    try:
        _official_calendar(*GPOST_CAL_SPAN, live=drafts_set())
    except NotRun as exc:
        assert exc.reason.startswith("OWNER: the signed KRX clock files must cover 2026-09-18..2026-10-02"), exc.reason
    else:
        raise AssertionError("_official_calendar passed the unsigned set")

    def run(**edits):
        rows = {fid: _gpost_rows(fid, texts[fid]) for fid in GPOST_READ}
        for fid, edit in edits.items():
            rows[fid] = edit(rows[fid])
        return _check_g_post_01(rows["F01"], rows["F13"], rows["F16"], rows["F27"], cal)

    def at(day, code=None, **kw):
        return lambda rows: [{**r, **kw} if r["date"] == day and code in (None, r.get("code")) else r for r in rows]

    def utc(d, hh, mm, ss=0):
        return datetime(d.year, d.month, d.day, hh, mm, ss, tzinfo=timezone.utc)

    got = run()
    g = G.golden("G-POST-01")
    assert got["kospi_close_2oct"] == got["kospi_official_close_2oct"] == 7003.74 and got["peak"] == GPOST_PEAK, got
    m1 = [r.sub_id for r in g.rows if r.runs_from == "M1"]
    assert len(m1) == 8 and all(G.within(g.row(k).kind, got[k], g.want(k)) for k in m1), got
    flat, oct2 = inv["F13"][0][1], GPOST_DAY
    # the 200-close window (G-POST-01/close_over_200d note "mean of last 200 closes incl. 2 Oct"; the count is typed
    # here, not read from GPOST_SMA_N): the row 201 closes back is outside it, the row 200 back inside it (levels far
    # from the window mean, below the 9,114.55 peak; one row moves the mean by (level - flat) / 200)
    day200, day201 = inv["F13"][-200][0], inv["F13"][-201][0]
    assert run(F13=at(day201, close=3000.0))["close_over_200d"] == got["close_over_200d"]
    moved = run(F13=at(day200, close=9000.0))["close_over_200d"]
    close = got["kospi_close_2oct"]
    assert abs(moved - close / (close / got["close_over_200d"] + (9000.0 - flat) / 200)) < 1e-9, moved
    print_1056 = dict(close=6943.66, obs_utc=utc(oct2, 1, 56), available_at_utc=utc(oct2, 1, 56))   # 10:56 KST, L6286
    cases = (
        (dict(F13=at(oct2, available_at_utc=utc(oct2, 6, 31))), "G-POST-01: 0 KS11 rows of 2026-10-02 visible at 06:30:30Z"),
        (dict(F13=at(oct2, **print_1056)), "the KS11 row of 2026-10-02 is not the close: obs_utc 01:56:00Z"),
        (dict(F01=at(oct2, **print_1056)), "the KOSPI_OFFICIAL_CLOSE row of 2026-10-02 is not the close"),
        (dict(F27=at(oct2, "005930", available_at_utc=utc(oct2, 6, 45))), "0 005930 rows of 2026-10-02 visible"),
        (dict(F27=at(oct2, "000660", obs_utc=utc(oct2, 5, 0))), "the 000660 row of 2026-10-02 is not the close"),
        (dict(F13=lambda rows: rows + [{**rows[-1], "date": date(2026, 10, 5)}]),
         "a KS11 row of 2026-10-05 is visible at the 2026-10-02 decision (look-ahead"),
        (dict(F13=at(oct2, close=7003.75)), "G-POST-01 deviations: kospi_close_2oct: got 7003.75"),
        (dict(F01=at(oct2, close=6943.66)),
         "G-POST-01 on the F01 official close: G-POST-01 deviations: kospi_close_2oct: got 6943.66"),
        (dict(F13=at(date(2026, 10, 1), close=6800.0)), "G-POST-01 deviations: kospi_return_2oct: got 0.0299"),
        (dict(F13=lambda rows: at(date(2026, 9, 30), close=[r for r in rows if r["date"] == date(2026, 10, 1)][0]["close"])(
            [r for r in rows if r["date"] != date(2026, 10, 1)])),
         "G-POST-01: the previous visible KS11 row is dated 2026-09-30, not the previous KRX session 2026-10-01"),
        (dict(F13=at(date(2026, 10, 1), available_at_utc=utc(oct2, 7, 0))),
         "G-POST-01: the previous visible KS11 row is dated 2026-09-30, not the previous KRX session 2026-10-01"),
        (dict(F13=at(GPOST_PEAK[0], close=9300.0)), "G-POST-01 deviations: drawdown_from_peak: got -0.246"),
        (dict(F13=lambda rows: [{**r, "close": r["close"] + 200.0} if r["close"] == flat else r for r in rows]),
         "G-POST-01 deviations: close_over_200d: got 1.07"),
        (dict(F27=at(oct2, "005930", close=276001.0)), "G-POST-01 deviations: samsung_close_2oct: got 276001.0"),
        (dict(F27=at(oct2, "000660", close=1840000.0)), "G-POST-01 deviations: hynix_close_2oct: got 1840000.0"),
        (dict(F16=at(GPOST_KRWX_LAST, close=1356.85)), "G-POST-01 deviations: krwx_last_row: got 1356.85"),
        (dict(F16=lambda rows: rows[:-21] + [{**rows[-21], "close": 1400.0}] + rows[-20:]),
         "G-POST-01 deviations: krwx_dlog20: got -0.031"),
        (dict(F16=lambda rows: rows + [{"date": oct2, "close": 1360.63, "obs_utc": utc(oct2, 6, 0),       # L6291
                                        "available_at_utc": utc(oct2, 6, 0)}]),
         "the last KRW=X row visible at the 2026-10-02 decision is 2026-10-02, not 2026-10-01"),
        (dict(F13=at(GPOST_PEAK[0], close=9200.0)), "the peak of the visible KS11 closes is 9200.0 on 2026-06-22"),
        (dict(F13=lambda rows: at(date(2026, 6, 23), close=GPOST_PEAK[1])(at(GPOST_PEAK[0], close=flat)(rows))),
         "the peak of the visible KS11 closes is 9114.55 on 2026-06-23"),
        (dict(F13=lambda rows: rows[-150:]), "150 visible KS11 rows, fewer than the 200"),
        (dict(F16=lambda rows: rows[-15:]), "15 visible KRW=X rows, too few for a 20-observation dlog"),
    )
    for edits, needle in cases:
        _gpost_fails(lambda: run(**edits), needle)
    # the layout
    _gpost_fails(lambda: _gpost_rows("F13", texts["F13"].replace(",close,", ",Close,", 1)),
                 "yahoo_KS11_1996-12_2026-10-02.csv: declared columns ['close'] absent")
    _gpost_fails(lambda: _gpost_rows("F27", texts["F27"].replace("date,code,", "date,ticker,", 1)),
                 "krx_005930_000660_closes_mcap.csv: declared columns ['code'] absent")
    _gpost_fails(lambda: _gpost_rows("F13", texts["F13"].replace(",vendor_close\n", ",provisional_intraday\n", 1)),
                 "yahoo_KS11_1996-12_2026-10-02.csv line 2: not a KS11 / vendor_close / calendar_bound row")
    head, first, second, *rest = texts["F16"].split("\n")
    _gpost_fails(lambda: _gpost_rows("F16", "\n".join([head, second, first, *rest])),
                 "yahoo_KRWX_2004_2026-10-01.csv line 3: rows out of date order or repeated")
    early = [(d, c, o, utc(oct2, 6, 0) if d == oct2 else a) for d, c, o, a in inv["F13"]]   # before its own close
    _gpost_fails(lambda: _gpost_rows("F13", _gpost_csv("F13", early)),
                 f"yahoo_KS11_1996-12_2026-10-02.csv line {len(early) + 1}: available_at_utc 2026-10-02T06:00:00Z before "
                 "obs_utc 2026-10-02T06:30:00Z")
    # while a fixture is absent the real test is NOT_RUN (REFDATA) and names it
    listed = load_manifest()
    absent = [fid for fid in ("F01", "F13", "F16", "F20", "F27") if FILE_OF[fid] not in listed]
    if absent:
        try:
            test_g_post_01_m1_data_rows_refdata()
        except NotRun as exc:
            assert exc.reason.startswith("REFDATA: ") and all(f"{fid} {FILE_OF[fid]} (" in exc.reason for fid in absent), exc
        else:
            raise AssertionError("test_g_post_01_m1_data_rows_refdata ran with absent fixtures")


def test_g_post_01_arithmetic_identities():
    """Identities between printed numbers (brief D.3 ARITH): drawdown -23.16% from 7,003.74 / 9,114.55; vt = min(1, 0.20/0.2882) = 0.694."""
    g = G.golden("G-POST-01")
    close = g.want("kospi_close_2oct")
    assert close == 7003.74
    G.assert_close(close / 9114.55 - 1.0, g.want("drawdown_from_peak"), "mdd", label="G-POST-01/drawdown_from_peak")
    assert abs(close / 9114.55 - 1.0 - (-0.2316)) < 5e-5
    rv20 = g.want("rv20_2oct")
    G.assert_close(min(1.0, 0.20 / rv20), g.want("vt_2oct"), "weight", label="G-POST-01/vt_2oct")
    assert abs(min(1.0, 0.20 / 0.2882) - 0.694) < 5e-4
    k4 = G.golden("G-KR-04")
    G.assert_close(min(1.0, 0.20 / k4.want("rv20_2oct2026")), k4.want("w_decided_2oct2026"), "weight")
    assert abs(g.want("samsung_share") + g.want("hynix_share") - g.want("pair_implied_share")) < 1e-9


test_g_post_01_arithmetic_identities.test_ids = ["G-POST-01"]


def test_synth_b5_bands_and_concentration_bounds():
    """B5 exceedance bands 0.05 +/- 2*sqrt(0.05*0.95/n) (L5642; brief B.4) and the section 11 concentration bounds."""
    def band(n):
        h = 2.0 * math.sqrt(0.05 * 0.95 / n)
        return 0.05 - h, 0.05 + h
    for gid, sub, n in (("G-B5-01", "sample", 2594), ("G-B5-01", "subsample", 371), ("G-B5-01", "garch_fhs", 2123),
                        ("G-B5-02", "sample", 2663), ("G-B5-03", "sample", 8961)):
        g = G.golden(gid)
        assert g.want(f"{sub}_origins") == n
        lo, hi = band(n)
        assert abs(lo - g.want(f"{sub}_band_lo")) < 5e-5 and abs(hi - g.want(f"{sub}_band_hi")) < 5e-5, (gid, sub, lo, hi)
    assert band(2594) == (band(2594)[0], band(2594)[1]) and abs(band(2594)[0] - 0.0414) < 5e-5 and abs(band(2594)[1] - 0.0586) < 5e-5
    s11 = G.golden("S11")
    G.assert_close(22.5 / 29.8, s11.want("conc_bound_abs"), "ratio")
    G.assert_close(0.05 / (0.298 - 0.225), s11.want("conc_bound_single"), "ratio")
    G.assert_close(min(0.694, 22.5 / 29.8, 0.05 / (0.298 - 0.225)), s11.want("gross_2oct"), "weight")


# --------------------------------------------------------------------------- #
# docs/macro_fixtures.py (TASK-M1-22)
# --------------------------------------------------------------------------- #
def test_macro_fixtures_refuses_when_reference_dir_absent():
    """An absent or empty reference directory: clear refusal listing every missing file; nothing written; exit 2."""
    with tempfile.TemporaryDirectory() as tmp:
        absent, empty, out = Path(tmp) / "nope", Path(tmp) / "ref", Path(tmp) / "out"
        empty.mkdir()
        for ref in (absent, empty):
            missing = MF.missing_files(ref)
            assert missing[0] == "CATALOG.md" and len(missing) == 1 + len(MF.REFERENCE_FILES)
            try:
                MF.generate(ref, out, retrieved_at_utc=datetime(2026, 10, 2, 9, tzinfo=timezone.utc), licence="x", owner="y")
                raise AssertionError("generate must refuse")
            except MF.ReferenceMissing as exc:
                msg = str(exc)
                assert exc.missing == missing and "refused" in msg and "yahoo_KS11_1996-12_2026-10-02.csv" in msg
                assert ("absent" in msg) == (ref is absent)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = MF.main(["--reference", str(ref), "--out", str(out)])
            assert rc == 2 and "refused" in buf.getvalue() and "fred_snapshot_2026-10-02/DGS10.csv" in buf.getvalue()
            assert not out.exists()
        # a partial directory names only what is missing
        (empty / "CATALOG.md").write_text("catalog\n", encoding="utf-8")
        (empty / "sox_daily.csv").write_text("date,close\n2026-10-01,1\n", encoding="utf-8")
        missing = MF.missing_files(empty)
        assert "CATALOG.md" not in missing and "sox_daily.csv" not in missing and len(missing) == len(MF.REFERENCE_FILES) - 1


def _fake_reference(ref: Path) -> None:
    (ref / "CATALOG.md").write_text("fake catalog\n", encoding="utf-8")
    for i, (fid, rel, series, status, *_rest) in enumerate(MF.REFERENCE_FILES):
        p = ref / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if status:
            p.write_text(f"date,close\n2026-09-30,{100 + i}\n2026-10-01,{101 + i}.5\n", encoding="utf-8")
        else:
            p.write_text(f"item,value\n{fid},{i}\n", encoding="utf-8")


def _available_at(series_id, obs, value_status):
    close = datetime(obs.year, obs.month, obs.day, 6, 30, tzinfo=timezone.utc)      # stub: KRX 15:30 KST
    return close, close + timedelta(seconds=30)


def test_macro_fixtures_generates_provenance_and_freezes_md5():
    """On a complete reference set: values unchanged, the section 4.1 provenance fields appended, md5 per file, manifest
    rows appended once; a regeneration reproduces the md5s; a changed reference file is refused by `freeze`."""
    with tempfile.TemporaryDirectory() as tmp:
        ref, out, manifest = Path(tmp) / "ref", Path(tmp) / "out", Path(tmp) / "MANIFEST.csv"
        ref.mkdir()
        _fake_reference(ref)
        retrieved = datetime(2026, 10, 2, 9, 0, tzinfo=timezone.utc)
        checked = []
        rows = MF.generate(ref, out, retrieved_at_utc=retrieved, licence="test licence", owner="package D",
                           available_at=_available_at, check_fixture=checked.append)
        assert len(rows) == len(MF.REFERENCE_FILES) and all(r["md5"] and r["licence"] and r["owner"] for r in rows)
        assert len(checked) == sum(1 for *_, st, _s, _m, _t in MF.REFERENCE_FILES if st in ("official_close", "vendor_close", "live_snapshot"))
        with (out / "yahoo_KS11_1996-12_2026-10-02.csv").open(encoding="utf-8", newline="") as fh:
            data = list(csv.DictReader(fh))
        assert tuple(data[0]) == ("date", "close") + MF.PROVENANCE_FIELDS
        assert [d["close"] for d in data] == ["114", "115.5"] and data[0]["obs_date"] == "2026-09-30"
        assert data[0]["available_at_utc"] == "2026-09-30T06:30:30Z" and data[0]["obs_utc"] == "2026-09-30T06:30:00Z"
        assert data[0]["value_status"] == "vendor_close" and data[0]["available_at_source"] == "calendar_bound"
        assert data[0]["retrieved_at_utc"] == "2026-10-02T09:00:00Z" and data[0]["vintage"] == "2026-10-02" and len(data[0]["content_hash"]) == 32
        ks11 = next(r for r in rows if r["file"] == "yahoo_KS11_1996-12_2026-10-02.csv")
        assert ks11["span"] == "2026-09-30..2026-10-01" and ks11["value_status_rule"] == "vendor_close; available_at_source = calendar_bound"
        assert (out / "QX_DLA_postpatch.csv").read_text(encoding="utf-8") == (ref / "results/QX_DLA_postpatch.csv").read_text(encoding="utf-8")
        assert MF.freeze(manifest, rows) == len(rows)
        listed = load_manifest(manifest)
        assert set(listed) == {r["file"] for r in rows} and listed[ks11["file"]]["md5"] == ks11["md5"]
        again = MF.generate(ref, out, retrieved_at_utc=retrieved, licence="test licence", owner="package D", available_at=_available_at)
        assert [r["md5"] for r in again] == [r["md5"] for r in rows] and MF.freeze(manifest, again) == 0
        assert load_manifest(manifest) == listed
        (ref / "sox_daily.csv").write_text("date,close\n2026-09-30,1\n2026-10-01,2\n", encoding="utf-8")
        changed = MF.generate(ref, out, retrieved_at_utc=retrieved, licence="test licence", owner="package D", available_at=_available_at)
        try:
            MF.freeze(manifest, changed)
            raise AssertionError("a changed md5 must be refused")
        except MF.FixtureChanged as exc:
            assert "sox_daily.csv" in str(exc) and "L5492" in str(exc)
        assert load_manifest(manifest) == listed
        try:
            MF.generate(ref, out, retrieved_at_utc=retrieved, licence="", owner="package D", available_at=_available_at)
            raise AssertionError("licence required")
        except ValueError as exc:
            assert "not a fixture" in str(exc)
        try:
            MF.generate(ref, out, retrieved_at_utc=retrieved, licence="l", owner="o")       # no calendar injected
            raise AssertionError("must not infer instants from retrieval")
        except RuntimeError as exc:
            assert "inferred" in str(exc)


# --------------------------------------------------------------------------- #
# docs/kis_quote_check.py (TASK-M1-01; T-RO-02 record clause)
# --------------------------------------------------------------------------- #
def test_kis_quote_check_refuses_without_credentials():
    """Import-safe, quotation-only; without credentials it prints the not-run line, records status 'not run' and exits 2."""
    code = _code_only(ROOT / "docs" / "kis_quote_check.py")
    tree = ast.parse(code)
    uapi = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.startswith("/uapi/")]
    assert uapi and all("/quotations/" in p for p in uapi), uapi
    assert set(KQ.PATHS.values()) == set(uapi) and not any(w in code.lower() for w in ("/trading/", "order_cash", "cano", "tttc"))
    assert "data.krx.kis_client" not in {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.col_offset == 0}
    assert KQ.NOT_RUN_MESSAGE == "not run: owner must run this with KIS credentials over ~20 live sessions"
    import config
    original = config.kis_ready
    config.kis_ready = lambda: False
    try:
        with tempfile.TemporaryDirectory() as tmp:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = KQ.main(["--out", tmp, "--session", "2026-10-06"], clock=lambda: datetime(2026, 10, 6, 6, 19, 59, tzinfo=timezone.utc))
            assert rc == 2 and buf.getvalue().startswith(KQ.NOT_RUN_MESSAGE)
            rec = json.loads((Path(tmp) / "2026-10-06.json").read_text(encoding="utf-8"))
            assert rec["status"] == "not run" and rec["reason"] == KQ.NOT_RUN_MESSAGE and rec["read_only"] is True
            assert rec["app_key_can_trade"] == "unknown" and rec["sessions"] == [] and rec["official_close"]["market_div_code"] is None
            assert set(rec["dependent_features"]) == {"R-27 snapshots", "R-08 spread snapshots", "R-26 stress-line calibration"}
            assert set(rec["dependent_features"].values()) == {"UNVERIFIED"} and rec["codes"] == ["069500", "005930"]
    finally:
        config.kis_ready = original


test_kis_quote_check_refuses_without_credentials.test_ids = ["T-RO-02"]


def test_kis_quote_check_owner_record():
    """T-RO-02 record clause: a 'run' record from the owner's live sessions; until then OWNER."""
    runs = [p for p in sorted(KQ.OUT_DIR.glob("*.json")) if json.loads(p.read_text(encoding="utf-8")).get("status") == "run"]
    if not runs:
        raise NotRun("OWNER: KIS quote-field check not run; run docs/kis_quote_check.py with KIS credentials at 15:19:59 KST "
                     "over ~20 live sessions and record app_key_can_trade (docs/kis_quote_check/<session>.json)")
    for p in runs:
        rec = json.loads(p.read_text(encoding="utf-8"))
        assert rec["read_only"] is True and all("/quotations/" in x for x in rec["paths"])
        assert rec["app_key_can_trade"] in ("yes", "no", "unknown") and rec["sessions"], p.name


test_kis_quote_check_owner_record.test_ids = ["T-RO-02"]


if __name__ == "__main__":
    from tests.macro_acceptance import run_module
    raise SystemExit(run_module(globals()))
