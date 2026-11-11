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
import hashlib
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
    # part 3 (2026-11-11, owner rulings 5 and 6)
    "macro_m1_calendars.py::test_regime01_full_range_expected_values_file",
    "macro_m8_forward.py::test_g_ref_01_s1_goldens_refdata",
)
LA02_REMAINING = {                              # not converted yet; a later part moves each up, so the list only shrinks
    "macro_m1_pit.py::test_fix_01_regeneration_at_level_1_tolerance_refdata":
        "T-FIX-01: council archive outside the repo; held by the owner (ruling 6 of 2026-11-11)",
    "macro_m7_cardp.py::test_i05_full_sample_lag_audit_over_compliant_goldens_refdata":
        "I-05: LA-07 and LA-30 first; the LA-30 vintages come with the reference data (ruling 12 of 2026-11-11)",
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
    # part 3 (2026-11-11, owner rulings 5 and 6)
    "macro_m1_calendars.py::test_regime01_full_range_expected_values_file",
    "macro_m8_forward.py::test_g_ref_01_s1_goldens_refdata",
})
LA02_FLOOR_SIZE = 15                            # the floor's size after part 3; a later part raises it, never lowers it
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
# YYYY-MM-DDTHH:MM:SSZ. F01, F13 and F16 hold one row per date and F27 one per code and date, in date order (F27: the
# dates of each code; a file grouped by code is in order too, review of PR #101, R2). One reader,
# tests.macro_m1_calendars.read_close_layout, reads the four files here and in the other part 2 bodies. A price is
# compared as owner ruling 4 of 2026-11-11 sets it (tests.macro_m1_calendars.price_as_compared; an owner-approved
# exception to spec L5735, Level 1 `price` "prices exact"): the Yahoo vendor closes of F13 and F16 rounded to two
# decimals, the KRX official closes of F01 and F27 exactly. F20
# (results/QX_DLA_postpatch.csv, the result table the rows were printed from) is gated with the others because
# goldens.csv lists it for kospi_close_2oct; its layout is not declared and the body does not read it (T-FIX-01
# regenerates it).
GPOST_READ = ("F01", "F13", "F16", "F27")
GPOST_COLUMNS = ("close", "series_id", "obs_date", "session_date", "obs_utc", "available_at_utc", "available_at_source",
                 "value_status")
GPOST_F27_CODES = ("005930", "000660")     # REFERENCE_FILES F27; G-POST-01/samsung_close_2oct and hynix_close_2oct
# The file each M1 price row of G-POST-01 is read from, which sets how it is compared (owner ruling 4 of 2026-11-11):
# the ^KS11 close (F13) and the KRW=X last row (F16) are Yahoo vendor prices, the two won closes (F27) KRX official.
GPOST_PRICE_FILES = {"kospi_close_2oct": "F13", "samsung_close_2oct": "F27", "hynix_close_2oct": "F27",
                     "krwx_last_row": "F16"}
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


def _gpost_rows(fid: str, text: str) -> list[dict]:
    """One G-POST-01 fixture in its declared layout as {date, close, series_id, obs_utc, available_at_utc[, code]} rows,
    read by the one reader of the declared close layout, tests.macro_m1_calendars.read_close_layout (shared with
    tests/macro_m1_pit.py, tests/macro_m2_risk.py and tests/macro_m3_estimators.py): AssertionError naming the file and
    line on any departure, a blank or "." close, a repeated date (F27: date and code) and a row available before its
    own obs_utc included."""
    from tests.macro_m1_calendars import read_close_layout
    return read_close_layout(fid, text)


def check_gpost01_rows(ks: list[dict], fx: list[dict], samsung: float, hynix: float, label: str) -> dict:
    """The eight G-POST-01 M1 rows (goldens.csv, runs_from M1), one helper for both G-POST-01 sites (this module's
    point-in-time replay and tests/macro_m1_pit.py's data rows). `ks` holds the KS11 rows the decision reads, in date
    order and ending with the 2-Oct close (the caller has checked that row and the previous session's), `fx` the KRW=X
    rows it reads, and `samsung` / `hynix` the 2-Oct KRX closes; `label` says how the caller read them. Asserts 200
    closes for close_over_200d and 21 KRW=X rows for the 20-observation dlog, KRW=X's last row on 1 Oct (the
    provisional 2-Oct row dropped), that the computed rows are exactly goldens.csv's M1 rows, every row at Level 1
    (`G.assert_golden`), and the peak, 9,114.55 on 22 Jun 2026. A price (kind `price`) is compared as
    tests.macro_m1_calendars.price_as_compared reads it, owner ruling 4 of 2026-11-11: the Yahoo vendor prices (the
    ^KS11 close, the peak and the KRW=X last row) rounded to two decimals, the KRX won prices of Samsung and SK hynix
    exactly (spec L5735). Returns the values as read, unrounded, and the peak."""
    from tests.macro_m1_calendars import price_as_compared
    assert len(ks) >= GPOST_SMA_N, f"G-POST-01: {len(ks)} KS11 rows {label}, fewer than the {GPOST_SMA_N} of close_over_200d"
    assert fx and fx[-1]["date"] == GPOST_KRWX_LAST, (
        f"G-POST-01: the last KRW=X row {label} is {fx[-1]['date'] if fx else None}, not {GPOST_KRWX_LAST} (the "
        "provisional 2-Oct row is dropped; G-POST-01/krwx_last_row)")
    assert len(fx) > GPOST_DLOG_N, f"G-POST-01: {len(fx)} KRW=X rows {label}, too few for a {GPOST_DLOG_N}-observation dlog"
    close, peak = ks[-1]["close"], max(ks, key=lambda r: r["close"])
    window = [r["close"] for r in ks[-GPOST_SMA_N:]]
    got = {"kospi_close_2oct": close,
           "kospi_return_2oct": close / ks[-2]["close"] - 1.0,
           "drawdown_from_peak": close / peak["close"] - 1.0,
           "close_over_200d": close / (sum(window) / len(window)),
           "samsung_close_2oct": samsung,
           "hynix_close_2oct": hynix,
           "krwx_last_row": fx[-1]["close"],
           "krwx_dlog20": math.log(fx[-1]["close"] / fx[-1 - GPOST_DLOG_N]["close"])}
    m1_rows = [r for r in G.golden("G-POST-01").rows if r.runs_from == "M1"]
    m1 = {r.sub_id for r in m1_rows}
    assert set(got) == m1, f"G-POST-01: goldens.csv M1 rows {sorted(m1)} != the computed rows {sorted(got)}"
    prices = {r.sub_id for r in m1_rows if r.kind == "price"}
    assert prices == set(GPOST_PRICE_FILES), (f"G-POST-01: goldens.csv M1 price rows {sorted(prices)} != the rows with "
                                              f"a price rule {sorted(GPOST_PRICE_FILES)}")
    print(f"PRINTED G-POST-01 M1 rows on {GPOST_DAY} ({label}): " + ", ".join(f"{k} {v:.6g}" for k, v in got.items())
          + f"; peak {peak['close']} on {peak['date']}")
    # Owner ruling 4 of 2026-11-11, an owner-approved exception to spec L5735 (Level 1 `price`: "prices exact"), for
    # vendor prices only: the Yahoo ^KS11 close, its peak and the KRW=X last row are compared after rounding to two
    # decimals (their goldens are printed at two decimals; a vendor file may carry float artefacts such as
    # 7003.740234375). The KRX official won prices of Samsung and SK hynix stay exact.
    G.assert_golden("G-POST-01", {k: price_as_compared(GPOST_PRICE_FILES[k], v) if k in GPOST_PRICE_FILES else v
                                  for k, v in got.items()})
    peak_price = price_as_compared("F13", peak["close"])
    assert peak["date"] == GPOST_PEAK[0] and G.within("price", peak_price, GPOST_PEAK[1]), (
        f"G-POST-01: the peak of the KS11 closes {label} is {peak['close']} on {peak['date']}, not {GPOST_PEAK[1]} on "
        f"{GPOST_PEAK[0]} (G-POST-01/drawdown_from_peak; a Yahoo vendor price, compared at two decimals: owner ruling "
        "4 of 2026-11-11, an exception to L5735)")
    return {**got, "peak": (peak["date"], peak["close"])}


def _check_g_post_01(f01: list[dict], f13: list[dict], f16: list[dict], f27: list[dict], cal) -> dict:
    """G-POST-01's M1 rows on the 2-Oct decision, read point in time (this site; tests/macro_m1_pit.py reads the same
    rows by date and does not read the instants). Each file is read as of 06:30:30Z: a row whose available_at_utc is
    later is not visible (spec L539), and a visible row dated after 2 Oct is a look-ahead stamp, a FAIL. The 2-Oct KOSPI
    rows of F13 and F01 and the 2-Oct Samsung and SK hynix rows of F27 are each the one visible row of that day, stamped
    at the scheduled close 06:30:00Z: an intraday print is not a close (the pre-patch 6,943.66 came from a file written
    at 10:56 KST, L6286). The previous visible KS11 row is dated the previous KRX session of the signed calendar `cal`
    (`clocks.prev_session`). Then `check_gpost01_rows` on the visible KS11 and KRW=X rows and the two stock closes, and
    F01's official close against kospi_close_2oct at Level 1: a KRX official price, compared exactly (spec L5735; owner
    ruling 4 of 2026-11-11 rounds vendor prices only). Returns the values."""
    from core.calendars import clocks
    from tests.macro_m1_calendars import price_as_compared
    label = f"visible at the {GPOST_DAY} decision"

    def visible(rows):
        return [r for r in rows if r["available_at_utc"] <= GPOST_DECISION_UTC]

    def close_of(rows, what):
        on_day = [r for r in visible(rows) if r["date"] == GPOST_DAY]
        assert len(on_day) == 1, (f"G-POST-01: {len(on_day)} {what} rows of {GPOST_DAY} visible at "
                                  f"{GPOST_DECISION_UTC:%H:%M:%S}Z; exactly one close is read (spec L539)")
        assert on_day[0]["obs_utc"] == GPOST_CLOSE_UTC, (
            f"G-POST-01: the {what} row of {GPOST_DAY} is not the close: obs_utc {on_day[0]['obs_utc']:%H:%M:%S}Z != "
            "the scheduled close 06:30:00Z (spec L1289; the pre-patch 6,943.66 was an intraday print, L6286)")
        return on_day[0]["close"]

    for what, rows in (("KOSPI_OFFICIAL_CLOSE", f01), ("KS11", f13), ("KRWX", f16), ("005930 / 000660", f27)):
        late = [r["date"] for r in visible(rows) if r["date"] > GPOST_DAY]
        assert not late, f"G-POST-01: a {what} row of {late[0]} is visible at the {GPOST_DAY} decision (look-ahead; L539)"
    close_of(f13, "KS11")
    ks = visible(f13)                                      # ends on 2 Oct: one visible row that day and none after it
    prev_day = clocks.prev_session("KR", GPOST_DAY, cal=cal)
    assert len(ks) > 1 and ks[-2]["date"] == prev_day, (
        f"G-POST-01: the previous visible KS11 row is dated {ks[-2]['date'] if len(ks) > 1 else None}, not the previous "
        f"KRX session {prev_day} (G-POST-01/kospi_return_2oct is the return on the previous close)")
    samsung, hynix = (close_of([r for r in f27 if r["code"] == c], c) for c in GPOST_F27_CODES)
    got = check_gpost01_rows(ks, visible(f16), samsung, hynix, label)
    official = close_of(f01, "KOSPI_OFFICIAL_CLOSE")
    print(f"PRINTED G-POST-01 F01 official close on {GPOST_DAY}: {official}")
    try:
        G.assert_golden("G-POST-01", {"kospi_close_2oct": price_as_compared("F01", official)})   # official: exact
    except AssertionError as exc:
        raise AssertionError(f"G-POST-01 on the F01 official close: {exc}") from None
    return {**got, "kospi_official_close_2oct": official}


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
    """(date, close, obs_utc, available_at_utc[, code]) rows written in the declared layout of `fid`, in memory
    (tests.macro_m1_calendars.close_layout_text; a close given as a string is written verbatim)."""
    from tests.macro_m1_calendars import close_layout_text
    return close_layout_text(fid, rows)


def _gpost_fails(fn, needle: str) -> str:
    try:
        fn()
    except AssertionError as exc:
        assert needle in str(exc), f"expected {needle!r} in: {exc}"
        return str(exc)
    raise AssertionError(f"expected an AssertionError naming {needle!r}")


def test_g_post_01_body_passes_and_fails_on_invented_rows():
    """LA-02 part 2: the G-POST-01 M1 body can PASS and can FAIL. Invented rows in the declared layouts (no KRX, Yahoo
    or QX data) built to the goldens.csv values pass. It fails, naming the clause, when: a 2-Oct row is not visible at
    06:30:30Z or is an intraday print (F13, F01, F27); a later row is visible; the KS11 close (by a cent), the F01
    official close (also by a float32 artefact: a KRX official price is exact), the previous close, the peak (beyond and
    within the drawdown tolerance, by a cent, or on another day), the flat level, a stock close (also by less than a
    cent), KRW=X's last close (by a cent) or its row 20 observations back is off; the previous visible KS11 row is not 1
    Oct (that row missing with 30 Sep at its level, or available only at 07:00Z); the provisional 2-Oct KRW=X row is
    visible; there are too few KS11 or KRW=X rows; and, at the layout (the shared reader), a declared column is absent,
    a row is not of its file's series and status, rows are out of order, a row is available before its obs_utc, a close
    is blank, ".", 0 or negative, a date repeats (F16; F27 date and code), obs_date is not session_date or not written
    YYYY-MM-DD, an instant is not written zero-padded YYYY-MM-DDTHH:MM:SSZ (unpadded, or with fractional seconds), or
    the file holds no row. The row 201 closes back is outside the 200-close window (its level does not move the ratio)
    and the row 200 back inside it. tests/macro_m1_pit.py's G-POST-01 body returns the same eight rows on the same
    files. A KRW=X row dated 2026-10-05, after F16's last day, stamped available on 1 Oct (a look-ahead stamp) FAILs
    here while the by-date body returns the same eight rows (it does not read the row); stamped on 5 Oct, it is visible
    at neither and both pass. A float32 artefact of the Yahoo files on the KS11 close, on the peak or on KRW=X's last
    row passes: a vendor price is compared at two decimals (owner ruling 4 of 2026-11-11, an owner-approved exception to
    spec L5735). The calendar is the calendars module's synthetic signed set, through the owner gate. While a fixture is
    absent, the real test's REFDATA reason names it."""
    from tests.macro_m1_calendars import (F01_COLUMNS, VENDOR_PRICE_FILES, _official_calendar, _official_calendar_on,
                                          close_layout_file, drafts_set, fixture_set, price_as_compared)
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
        (dict(F13=at(GPOST_PEAK[0], close=9200.0)),
         "the peak of the KS11 closes visible at the 2026-10-02 decision is 9200.0 on 2026-06-22"),
        (dict(F13=lambda rows: at(date(2026, 6, 23), close=GPOST_PEAK[1])(at(GPOST_PEAK[0], close=flat)(rows))),
         "the peak of the KS11 closes visible at the 2026-10-02 decision is 9114.55 on 2026-06-23"),
        (dict(F13=lambda rows: rows[-150:]), "150 KS11 rows visible at the 2026-10-02 decision, fewer than the 200"),
        (dict(F16=lambda rows: rows[-15:]), "15 KRW=X rows visible at the 2026-10-02 decision, too few for a 20-observation"),
        # owner ruling 4 of 2026-11-11: a vendor price a cent away at two decimals is off (7,003.7451 rounds to
        # 7,003.75; the peak 9,114.56 is inside the drawdown tolerance and fails the peak clause)
        (dict(F13=at(oct2, close=7003.7451)), "G-POST-01 deviations: kospi_close_2oct: got 7003.75, want 7003.74"),
        (dict(F13=at(GPOST_PEAK[0], close=9114.56)),
         "the peak of the KS11 closes visible at the 2026-10-02 decision is 9114.56 on 2026-06-22"),
        # ... and a KRX official price stays exact (spec L5735): the won closes of F27 and F01's official KOSPI close
        # fail on less than a cent, F01 also on the float32 artefact that F13 may carry
        (dict(F27=at(oct2, "005930", close=276000.004)), "G-POST-01 deviations: samsung_close_2oct: got 276000.004"),
        (dict(F27=at(oct2, "000660", close=1841000.004)), "G-POST-01 deviations: hynix_close_2oct: got 1841000.004"),
        (dict(F01=at(oct2, close=7003.740234375)),
         "G-POST-01 on the F01 official close: G-POST-01 deviations: kospi_close_2oct: got 7003.740234375"),
    )
    for edits, needle in cases:
        _gpost_fails(lambda: run(**edits), needle)
    # Owner ruling 4 of 2026-11-11, an owner-approved exception to spec L5735 ("prices exact") for vendor prices only: a
    # Yahoo price is compared after rounding to two decimals, so a float32 artefact of the vendor file passes, on the
    # 2-Oct KS11 close, on KRW=X's last row and on the peak, and so does 7,003.7449 (it rounds to 7,003.74). The rows
    # are returned as read. The goldens of the vendor rows are printed at two decimals, so the rounding loses nothing.
    for edits, key, as_read in ((dict(F13=at(oct2, close=7003.740234375)), "kospi_close_2oct", 7003.740234375),
                                (dict(F13=at(oct2, close=7003.7449)), "kospi_close_2oct", 7003.7449),
                                (dict(F16=at(GPOST_KRWX_LAST, close=1356.8399658203125)), "krwx_last_row",
                                 1356.8399658203125)):
        assert run(**edits)[key] == as_read, key
    assert run(F13=at(GPOST_PEAK[0], close=9114.5498046875))["peak"] == (GPOST_PEAK[0], 9114.5498046875)
    assert VENDOR_PRICE_FILES == ("F13", "F16") and GPOST_PRICE_FILES == {
        "kospi_close_2oct": "F13", "samsung_close_2oct": "F27", "hynix_close_2oct": "F27", "krwx_last_row": "F16"}
    assert [close_layout_file(f)[2] for f in ("F13", "F16", "F27", "F01")] == ["vendor_close", "vendor_close",
                                                                               "official_close", "official_close"]
    assert all(round(g.want(k), 2) == g.want(k) for k in ("kospi_close_2oct", "krwx_last_row"))
    assert round(GPOST_PEAK[1], 2) == GPOST_PEAK[1]
    assert price_as_compared("F13", 7003.740234375) == 7003.74
    assert price_as_compared("F16", 1356.8399658203125) == 1356.84
    assert price_as_compared("F27", 276000.004) == 276000.004           # a KRX official price is not rounded
    assert price_as_compared("F01", 7003.740234375) == 7003.740234375
    _gpost_fails(lambda: price_as_compared("F14", 5000.0), "F14: no price comparison rule for a vendor_close file")
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
    # one rule for every file of the layout: a close that is blank or "." (each used to escape as a ValueError), 0 or
    # negative is refused naming the file and line, and so is a repeated date, here a repeated F27 date and code
    for cell in (".", "", "0", "-5"):
        blank = [(d, cell if i == 9 else c, o, a) for i, (d, c, o, a) in enumerate(inv["F13"])]
        _gpost_fails(lambda: _gpost_rows("F13", _gpost_csv("F13", blank)),
                     f"yahoo_KS11_1996-12_2026-10-02.csv line 11: close {cell!r} is not a finite number > 0")
    _gpost_fails(lambda: _gpost_rows("F27", _gpost_csv("F27", inv["F27"] + inv["F27"][-1:])),
                 f"krx_005930_000660_closes_mcap.csv line {len(inv['F27']) + 2}: rows out of date order or repeated")
    _gpost_fails(lambda: _gpost_rows("F16", _gpost_csv("F16", inv["F16"][:5] + inv["F16"][4:])),
                 "yahoo_KRWX_2004_2026-10-01.csv line 7: rows out of date order or repeated")
    # obs_date is session_date, both written YYYY-MM-DD; obs_utc and available_at_utc are written zero-padded
    # YYYY-MM-DDTHH:MM:SSZ, as docs/macro_fixtures.py writes them (strptime alone takes "2026-10-2T6:30:0Z"); a file
    # holds a row. Each departure is refused naming the file and line (`cell_at`: one cell of one line of the F13 text)
    f13_lines = texts["F13"].split("\n")

    def cell_at(line: int, **cells) -> str:
        cols, row = f13_lines[0].split(","), f13_lines[line - 1].split(",")
        for col, value in cells.items():
            row[cols.index(col)] = value
        return "\n".join(f13_lines[:line - 1] + [",".join(row)] + f13_lines[line:])
    day11, oct2_line = inv["F13"][9][0], len(inv["F13"]) + 1         # file line 11; the 2-Oct row's line (261)
    assert f13_lines[oct2_line - 1].startswith("2026-10-02,"), f13_lines[oct2_line - 1]
    for obs_date, session_date in (((day11 - timedelta(days=1)).isoformat(), day11.isoformat()),
                                   (day11.strftime("%Y%m%d"), day11.strftime("%Y%m%d"))):
        _gpost_fails(lambda: _gpost_rows("F13", cell_at(11, obs_date=obs_date, session_date=session_date)),
                     "yahoo_KS11_1996-12_2026-10-02.csv line 11: obs_date != session_date or not written YYYY-MM-DD "
                     f"({obs_date!r}, {session_date!r})")
    for col, instant in (("obs_utc", "2026-10-2T6:30:0Z"), ("available_at_utc", "2026-10-02T06:30:30.000Z")):
        _gpost_fails(lambda: _gpost_rows("F13", cell_at(oct2_line, **{col: instant})),
                     f"yahoo_KS11_1996-12_2026-10-02.csv line {oct2_line}: instant {instant!r} is not written "
                     "YYYY-MM-DDTHH:MM:SSZ")
    _gpost_fails(lambda: _gpost_rows("F13", f13_lines[0] + "\n"), "yahoo_KS11_1996-12_2026-10-02.csv: no rows")
    # the two G-POST-01 sites share the reader and `check_gpost01_rows`: tests/macro_m1_pit.py's data-row body returns
    # the same eight rows on the same files (it reads them by date, not by instant)
    from tests.macro_m1_pit import _check_gpost01_m1
    pit_rows = _check_gpost01_m1(*(_gpost_rows(fid, texts[fid]) for fid in ("F13", "F16", "F27")), cal)
    assert {k: pit_rows[k] for k in m1} == {k: got[k] for k in m1}, (pit_rows, got)
    # a KRW=X row dated 2026-10-05, after F16's last day (its name ends 2026-10-01): stamped available on 1 Oct, a
    # look-ahead stamp, it is visible at the decision and FAILs here (L539), while the by-date site does not read it and
    # returns the same eight rows; stamped on its own day it is visible at neither, and both pass
    oct5 = date(2026, 10, 5)
    for avail in (utc(date(2026, 10, 1), 21, 0), utc(oct5, 21, 0)):
        fx_late = {**{fid: _gpost_rows(fid, texts[fid]) for fid in GPOST_READ},
                   "F16": _gpost_rows("F16", _gpost_csv("F16", inv["F16"] + [(oct5, 1349.0, avail, avail)]))}
        by_date = _check_gpost01_m1(fx_late["F13"], fx_late["F16"], fx_late["F27"], cal)
        assert {k: by_date[k] for k in m1} == {k: got[k] for k in m1}, (avail, by_date)
        if avail <= GPOST_DECISION_UTC:
            _gpost_fails(lambda: _check_g_post_01(fx_late["F01"], fx_late["F13"], fx_late["F16"], fx_late["F27"], cal),
                         "G-POST-01: a KRWX row of 2026-10-05 is visible at the 2026-10-02 decision (look-ahead; L539)")
        else:
            assert _check_g_post_01(fx_late["F01"], fx_late["F13"], fx_late["F16"], fx_late["F27"], cal) == got, avail
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
        if "code" in MF.CLOSE_LAYOUT.get(fid, ()):         # F27, long form: one row per code and day (owner ruling 1)
            p.write_text("date,code,close\n" + "".join(f"{d},{code},{100 + i + k}\n" for d in ("2026-09-30", "2026-10-01")
                                                       for k, code in enumerate(series.split(";"))), encoding="utf-8")
        elif status:
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
# The reference close files F13, F14, F16 and F27 (owner rulings 1 and 2 of 2026-11-11,
# docs/nautilus_bridge/OWNER_RULINGS_LOG.md): one layout for the generator and its readers, and the instants of their
# unregistered series from the market calendar. Invented rows only: no Yahoo or KRX data.
# --------------------------------------------------------------------------- #
REFERENCE_CLOSE_FILES = ("F13", "F14", "F16", "F27")
REFERENCE_RETRIEVED = datetime(2026, 10, 2, 9, 0, tzinfo=timezone.utc)


def _reference_row(fid: str) -> tuple:
    rows = [r for r in MF.REFERENCE_FILES if r[0] == fid]
    assert len(rows) == 1, (fid, len(rows))
    return rows[0]


def _invented_reference(fid: str, days) -> str:
    """An invented reference file (no Yahoo or KRX data) in the declared layout of `fid`: a `date` column, then
    MF.CLOSE_LAYOUT[fid]; F27 holds one row per code and day."""
    codes = _reference_row(fid)[2].split(";") if "code" in MF.CLOSE_LAYOUT[fid] else [None]
    buf = io.StringIO()
    out = csv.writer(buf, lineterminator="\n")
    out.writerow(("date",) + MF.CLOSE_LAYOUT[fid])
    for i, d in enumerate(days):
        for k, code in enumerate(codes):
            close = f"{1000.0 * (k + 1) + 37.0 * math.sin(i) + 0.5 * i:.2f}"
            out.writerow((d.isoformat(), close) if code is None else (d.isoformat(), code, close))
    return buf.getvalue()


def _refused(fn, exc_type, *needles):
    """`fn` raises `exc_type` with every needle in its message; returns the exception."""
    try:
        fn()
    except exc_type as exc:
        text = exc.args[0] if exc.args and isinstance(exc.args[0], str) else str(exc)
        missing = [n for n in needles if n not in text]
        assert not missing, f"expected {missing} in: {text}"
        return exc
    raise AssertionError(f"expected {exc_type.__name__} naming {needles}")


def test_macro_fixtures_stamps_reference_series_from_the_market_calendar():
    """Owner ruling 2 (2026-11-11): the series of the reference close files are not registered, and the generator
    stamps each from the market calendar its REFERENCE_FILES row names. On invented rows over the synthetic signed
    calendars, F13 (KS11, KR), F14 (GSPC, US) and F27 (005930 / 000660, KR) come out observed at the scheduled close
    and available at the close-print bound of their session (`clocks.close_stamp`, calendar_bound), values unchanged,
    in the layout the shared reader accepts, and they pass the post-close check: retrieved at the bound + 10 min is
    accepted and one second earlier is refused (spec L1493 rule 5). A row of F27, the long form, is stamped with its
    own code as its series_id, so both 005930 and 000660 are stamped. F16 (KRWX) names FX, which no signed calendar
    carries: since owner ruling A-1 (2026-11-11) it is stamped at the New York 17:00 FX day close
    (test_macro_fixtures_stamps_krwx_at_the_new_york_fx_close; until then it was refused). A non-session and a date
    outside signed coverage raise from the clocks, so nothing is inferred. An id that is neither registered nor declared is refused with the error it
    always had, a declared series is stamped only as its row's value_status, and the registry knows none of the five
    ids."""
    from core.calendars import clocks as K
    from core.calendars.adapter import CalendarClocks
    from core.calendars.store import CalendarCoverageError, NotASession
    from core.ficc import contracts, pit
    from tests.macro_m1_calendars import fixture_set, read_close_layout
    registry, cal = contracts.default_registry(), fixture_set()
    clk = CalendarClocks(registry, cal=cal)
    available_at, check = MF.calendar_available_at(registry, clk), MF.calendar_check_fixture(registry, clk)
    # the declaration: the five ids the ruling names, each on the market and status of its REFERENCE_FILES row
    assert set(MF.REFERENCE_SERIES) == {"KS11", "GSPC", "KRWX", "005930", "000660"}
    assert MF.REFERENCE_SERIES == {sid: (_reference_row(fid)[5], _reference_row(fid)[3])
                                   for fid in REFERENCE_CLOSE_FILES for sid in _reference_row(fid)[2].split(";")}
    assert not any(registry.is_series(sid) for sid in MF.REFERENCE_SERIES)              # nothing is registered
    # only a close stamped calendar_bound on a named market can be declared: not a result table, not a published series
    _refused(lambda: MF._reference_series(("F20",)), ValueError, "F20 results/QX_DLA_postpatch.csv: a reference close")
    _refused(lambda: MF._reference_series(("F02",)), ValueError, "F02 ecos_bok_call_rate_1997_2026-10.csv: a reference")
    # KRX: scheduled close 06:30:00Z, close-print bound 06:30:30Z (spec L1289); the registered official close of the
    # same session is stamped the same. NYSE in EDT: 20:00:00Z, bound + 30 s (spec L1290, L1310)
    for sid, status in (("KS11", "vendor_close"), ("005930", "official_close"), ("000660", "official_close")):
        assert available_at(sid, GPOST_DAY, status) == (GPOST_CLOSE_UTC, GPOST_DECISION_UTC), sid
    assert available_at("KOSPI_OFFICIAL_CLOSE", GPOST_DAY, "official_close") == (GPOST_CLOSE_UTC, GPOST_DECISION_UTC)
    us_close = datetime(2026, 10, 1, 20, 0, tzinfo=timezone.utc)
    assert available_at("GSPC", date(2026, 10, 1), "vendor_close") == (us_close, us_close + timedelta(seconds=30))
    spans = {"F13": (date(2026, 9, 14), GPOST_DAY), "F14": (date(2026, 9, 14), date(2026, 10, 1)),
             "F27": (date(2026, 9, 28), GPOST_DAY)}
    quarantine = timedelta(minutes=pit.QUARANTINE_MINUTES)
    with tempfile.TemporaryDirectory() as tmp:
        for fid, (lo, hi) in spans.items():
            _fid, rel, series, status, source, market, _tests = _reference_row(fid)
            ids = series.split(";")
            days = K.sessions_between(market, lo, hi, cal=cal)
            src, dst = Path(tmp) / f"reference_{Path(rel).name}", Path(tmp) / Path(rel).name
            src.write_text(_invented_reference(fid, days), encoding="utf-8")

            def stamped(retrieved):
                return MF.fixture_rows(src, series_id=ids[0], value_status=status, available_at_source=source,
                                       retrieved_at_utc=retrieved, available_at=available_at,
                                       columns=MF.CLOSE_LAYOUT[fid], series=tuple(ids))
            fields, rows = stamped(REFERENCE_RETRIEVED)
            text = MF.fixture_text(fields, rows)
            assert "\r" not in text and text.count("\n") == len(rows) + 1, fid          # LF lines, as `generate` writes
            got = read_close_layout(fid, text)
            assert len(days) > 3 and [r["date"] for r in got] == [d for d in days for _ in ids], fid
            for r in got:
                stamp = K.close_stamp(market, r["date"], cal=cal)
                assert (r["obs_utc"], r["available_at_utc"]) == (stamp.obs_utc, stamp.available_at_utc), (fid, r)
                assert stamp.available_at_source == source == "calendar_bound", fid
            reference = list(csv.DictReader(io.StringIO(src.read_text(encoding="utf-8"))))
            assert [{c: r[c] for c in reference[0]} for r in rows] == reference, fid    # values copied unchanged
            # a long-form row carries its own code; every other file's rows carry the file's id
            assert [r["series_id"] for r in rows] == [r.get("code", ids[0]) for r in rows], fid
            assert {r["series_id"] for r in rows} == set(ids), fid
            bound = clk.close_print_bound_utc(market, days[-1])
            dst.write_text(MF.fixture_text(*stamped(bound + quarantine)), encoding="utf-8")
            assert check(dst) == len(rows), fid
            _refused(lambda: pit.check_fixture(dst, registry=registry, clocks=clk), KeyError, ids[0])
            dst.write_text(MF.fixture_text(*stamped(bound + quarantine - timedelta(seconds=1))), encoding="utf-8")
            _refused(lambda: check(dst), pit.FixtureRefused, "close + 10 min")
        # the post-close check reads a registered series through the registry, as before, and an id that is neither
        # registered nor declared (F08's SOX, stamped here by the stub) raises as the registry raises
        src, dst = Path(tmp) / f"reference_{FILE_OF['F13']}", Path(tmp) / "other.csv"

        def other(sid, status, stamp):
            fields, rows = MF.fixture_rows(src, series_id=sid, value_status=status, available_at_source="calendar_bound",
                                           retrieved_at_utc=REFERENCE_RETRIEVED, available_at=stamp)
            dst.write_text(MF.fixture_text(fields, rows), encoding="utf-8")
            return len(rows)
        n = other("KOSPI_OFFICIAL_CLOSE", "official_close", available_at)
        assert n > 3 and check(dst) == pit.check_fixture(dst, registry=registry, clocks=clk) == n
        other("SOX", "vendor_close", _available_at)
        assert _refused(lambda: check(dst), KeyError).args == ("SOX",)
        assert _refused(lambda: pit.check_fixture(dst, registry=registry, clocks=clk), KeyError).args == ("SOX",)
        view = MF._ReferenceMarkets(registry)                       # the registry as the check reads it: nothing added
        assert [view.is_series(sid) for sid in ("KS11", "KOSPI_OFFICIAL_CLOSE")] == [False, True]
        assert (view.market("KS11"), view.market("KOSPI_OFFICIAL_CLOSE"), view.schedule("DGS10")) == (
            "KR", registry.market("KOSPI_OFFICIAL_CLOSE"), registry.schedule("DGS10"))
        # F16: REFERENCE_FILES names FX. The spec's market clocks are KRX, NYSE and CRYPTO (L1289-1291) and
        # core.calendars has no FX clock; owner ruling A-1 stamps KRW=X at the New York 17:00 FX day close
        _fid, rel, series, status, source, market, _tests = _reference_row("F16")
        assert (series, market) == ("KRWX", "FX") and market not in K.M1_MARKETS
        _refused(lambda: clk.decision_time_utc(market, GPOST_KRWX_LAST), KeyError, "not an M1 market")   # still none
        src = Path(tmp) / f"reference_{Path(rel).name}"
        fx_days = _gpost_weekdays(GPOST_KRWX_LAST, 5)
        src.write_text(_invented_reference("F16", fx_days), encoding="utf-8")
        _fields, fx_rows = MF.fixture_rows(src, series_id=series, value_status=status, available_at_source=source,
                                           retrieved_at_utc=REFERENCE_RETRIEVED, available_at=available_at,
                                           columns=MF.CLOSE_LAYOUT["F16"])
        assert [(r["obs_utc"], r["available_at_utc"]) for r in fx_rows] == [
            (f"{d}T21:00:00Z", f"{d}T21:00:00Z") for d in fx_days]                    # 17:00 EDT, before November
        # a long-form file is stamped by code, so it is refused without the ids its codes may name
        f27 = Path(tmp) / f"reference_{FILE_OF['F27']}"
        _refused(lambda: MF.fixture_rows(f27, series_id="005930", value_status="official_close",
                                         available_at_source="calendar_bound", retrieved_at_utc=REFERENCE_RETRIEVED,
                                         available_at=available_at, columns=MF.CLOSE_LAYOUT["F27"]), ValueError,
                 f"reference_{FILE_OF['F27']}: a long-form file (declared column `code`) is stamped by code")
    for sid in ("SOX", "KODEX200_PRICE", "NOT_A_SERIES"):          # F08's series, F03's series, and no series at all
        exc = _refused(lambda: available_at(sid, GPOST_KRWX_LAST, "vendor_close"), KeyError)
        assert exc.args == (f"{sid}: not a registered series id (every fixture series is named)",), exc.args
    _refused(lambda: available_at("KS11", GPOST_DAY, "official_close"), ValueError,
             "KS11: a reference series is stamped as its REFERENCE_FILES row declares it (vendor_close)")
    # a Saturday is never rolled to a session, and the synthetic NYSE file starts in 2006
    _refused(lambda: available_at("KS11", date(2026, 10, 3), "vendor_close"), NotASession)
    _refused(lambda: available_at("GSPC", date(2005, 12, 30), "vendor_close"), CalendarCoverageError)


def test_macro_fixtures_stamps_krwx_at_the_new_york_fx_close():
    """Owner ruling A-1 (2026-11-11, docs/nautilus_bridge/OWNER_RULINGS_LOG.md): the generator stamps KRW=X (F16,
    whose REFERENCE_FILES row names the market FX) at the New York 17:00 FX day close. No signed calendar carries FX
    and none is added; KRWX stays unregistered. A row dated d is observed at 17:00 America/New_York on d, in UTC by the
    zone's own rules, and available at that same instant (no ruling names a print delay): 22:00Z in standard time and
    21:00Z in daylight time, on both sides of both 2026 changes (8 Mar, 1 Nov) and of the 2006 ones (2 Apr, 29 Oct),
    where today's month rule would give the wrong hour on 13 Mar and 30 Oct 2006. A weekday is stamped without a
    holiday list (none is signed for FX), 25 Dec included. A Saturday or a Sunday has no FX day close (the week closes
    on Friday at 17:00 and reopens on Sunday at 17:00): refused by the instant function and by the post-close check,
    and in a reference file with the file and line named, writing nothing. At the KRX decision of 2 Oct 2026
    (06:30:30Z) the 1-Oct row is visible and the 2-Oct row is not, as the ruling's note says. T-FIX-01 on an F16
    fixture: retrieved at its last close + 10 min it is written and accepted, one second earlier it is refused and
    nothing is written; the shared reader accepts the file; a fixture the generator did not write that holds a
    Saturday row is refused by the check, naming the fixture file and the date (it was a bare NoFXDayClose naming
    neither). The clocks of every other market are read unchanged."""
    from core.calendars import clocks as K
    from core.calendars.adapter import CalendarClocks
    from core.ficc import contracts, pit
    from tests.macro_m1_calendars import fixture_set, read_close_layout
    registry, cal = contracts.default_registry(), fixture_set()
    clk = CalendarClocks(registry, cal=cal)
    available_at, check = MF.calendar_available_at(registry, clk), MF.calendar_check_fixture(registry, clk)
    _fid, rel, series, status, source, market, _tests = _reference_row("F16")
    assert (series, status, source, market) == ("KRWX", "vendor_close", "calendar_bound", MF.FX_MARKET) and (
        MF.FX_MARKET == "FX")
    assert MF.REFERENCE_SERIES["KRWX"] == (MF.FX_MARKET, "vendor_close") and not registry.is_series("KRWX")
    assert MF.FX_MARKET not in K.M1_MARKETS and (MF.FX_CLOSE_LOCAL.hour, MF.FX_CLOSE_LOCAL.minute, MF.FX_CLOSE_TZ,
                                                 MF.FX_PRINT_BOUND_S) == (17, 0, "America/New_York", 0)

    def utc(d, hour):
        return datetime(d.year, d.month, d.day, hour, tzinfo=timezone.utc)
    stamps = {date(2026, 3, 6): 22, date(2026, 3, 9): 21,        # Fri before and Mon after Sun 8 Mar 2026 (EST -> EDT)
              date(2026, 10, 30): 21, date(2026, 11, 2): 22,     # Fri before and Mon after Sun 1 Nov 2026 (EDT -> EST)
              date(2006, 3, 13): 22, date(2006, 4, 3): 21,       # 2006: EDT from 2 Apr, not from the 2nd Sunday of March
              date(2006, 10, 27): 21, date(2006, 10, 30): 22,    # ... to 29 Oct, not to the 1st Sunday of November
              date(2026, 10, 1): 21, date(2026, 10, 2): 21,      # a Thursday and a Friday
              date(2026, 12, 25): 22}                             # a weekday holiday: no FX holiday list is signed
    for d, hour in stamps.items():
        assert MF.fx_close_utc(d) == utc(d, hour) and available_at("KRWX", d, status) == (utc(d, hour),) * 2, d
    reference_clocks = MF._ReferenceClocks(clk)
    for m, d in (("KR", GPOST_DAY), ("US", date(2026, 10, 1))):
        assert (reference_clocks.decision_time_utc(m, d), reference_clocks.close_print_bound_utc(m, d)) == (
            clk.decision_time_utc(m, d), clk.close_print_bound_utc(m, d)), m
    assert reference_clocks.is_session("KR", GPOST_DAY) and reference_clocks.cal is clk.cal
    # the ruling's note: at the KRX close of 2 Oct only the value dated the day before is visible
    assert available_at("KRWX", GPOST_KRWX_LAST, status)[1] <= GPOST_DECISION_UTC < available_at("KRWX", GPOST_DAY,
                                                                                                    status)[1]
    for d in (date(2026, 3, 7), date(2026, 3, 8), date(2026, 10, 3), date(2026, 10, 4), date(2026, 10, 31),
              date(2026, 11, 1)):
        _refused(lambda: available_at("KRWX", d, status), MF.NoFXDayClose, f"KRWX: FX {d} is a {d:%A}", "no day close")
        _refused(lambda: reference_clocks.close_print_bound_utc("FX", d), MF.NoFXDayClose, f"FX {d} is a {d:%A}")
    _refused(lambda: MF.fx_close_utc(datetime(2026, 10, 2, 12)), TypeError, "must be a datetime.date")
    _refused(lambda: available_at("KRWX", GPOST_DAY, "official_close"), ValueError,
             "KRWX: a reference series is stamped as its REFERENCE_FILES row declares it (vendor_close)")
    days, name = _gpost_weekdays(GPOST_KRWX_LAST, 10), FILE_OF["F16"]
    quarantine = timedelta(minutes=pit.QUARANTINE_MINUTES)
    with tempfile.TemporaryDirectory() as tmp:
        ref, out = Path(tmp) / "ref", Path(tmp) / "out"
        ref.mkdir()
        (ref / "CATALOG.md").write_text("invented catalog\n", encoding="utf-8")
        f16 = ref / rel

        def generate(retrieved):
            return MF.generate(ref, out, retrieved_at_utc=retrieved, licence="test licence", owner="package D",
                               available_at=available_at, check_fixture=check, only=("F16",))
        for weekend in (date(2026, 9, 19), date(2026, 9, 20)):                  # a Saturday, a Sunday, on line 3
            f16.write_text(_invented_reference("F16", days[:1] + [weekend] + days[1:]), encoding="utf-8")
            _refused(lambda: generate(REFERENCE_RETRIEVED), MF.NoFXDayClose,
                     f"{name} line 3: KRWX: FX {weekend} is a {weekend:%A}", "no fixture is written")
            assert not out.exists()
        f16.write_text(_invented_reference("F16", days), encoding="utf-8")
        bound = available_at("KRWX", days[-1], status)[1]
        assert bound == utc(days[-1], 21)
        _refused(lambda: generate(bound + quarantine - timedelta(seconds=1)), pit.FixtureRefused,
                 f"{name}:{len(days)}: KRWX {days[-1]}", "close + 10 min")
        assert not out.exists()
        rows = generate(bound + quarantine)
        assert [(r["file"], r["span"]) for r in rows] == [(name, f"{days[0]}..{days[-1]}")]
        got = read_close_layout("F16", (out / name).read_text(encoding="utf-8"))
        assert [(r["date"], r["obs_utc"], r["available_at_utc"]) for r in got] == [(d, utc(d, 21), utc(d, 21))
                                                                                   for d in days]
        assert check(out / name) == len(days)
        _refused(lambda: pit.check_fixture(out / name, registry=registry, clocks=clk), KeyError, "KRWX")
        # a fixture the generator did not write (archived, hand-made) with a Saturday row: T-FIX-01 has no bound for
        # it, and the refusal names the fixture file and the row's date
        lines = (out / name).read_text(encoding="utf-8").rstrip("\n").split("\n")
        saturday = date(2026, 10, 3)
        hand_made = Path(tmp) / "hand_made_krwx.csv"
        hand_made.write_text("\n".join(lines + [lines[-1].replace(days[-1].isoformat(), saturday.isoformat())]) + "\n",
                             encoding="utf-8")
        _refused(lambda: check(hand_made), MF.NoFXDayClose, f"hand_made_krwx.csv: FX {saturday} is a Saturday",
                 "no close-print bound for T-FIX-01")


def test_macro_fixtures_close_layout_is_one_layout_for_three_readers():
    """Owner ruling 1 (2026-11-11): F13, F14 and F16 carry their value in `close`, and F27 is long form with `code`,
    `series_id` and `close`, the series_id of a row being its own code. The generator's declaration (MF.CLOSE_LAYOUT),
    the shared test reader's and the product reader's (docs/vol_backtest.FIXTURE_COLUMNS) name the same columns. On an
    invented reference set `generate` writes the four files as `date`, the declared columns and the section 4.1
    provenance columns, and the shared reader accepts each. From F13 the product reader `fixture_closes` reads the
    dates and closes the test reader reads, and `fixture_lines`, given a manifest that lists the file, returns the B5
    harness lines on them. `generate` refuses a reference file whose header lacks a declared column (Yahoo's own
    `Close`; F27 without `code`). The product reader refuses the old `value` column, a blank, "." or negative close, a
    repeated or badly written date and a one-row file, and `fixture_lines` raises on a listed file in the old layout:
    it does not report NOT_RUN."""
    from docs import vol_backtest as VB
    from tests.macro_m1_calendars import CLOSE_LAYOUT_FILES, CLOSE_LAYOUT_KEYS, F01_COLUMNS, read_close_layout
    from tests.notrun import md5_of
    assert MF.CLOSE_LAYOUT == {"F13": ("close",), "F14": ("close",), "F16": ("close",), "F27": ("code", "close")}
    assert tuple(MF.CLOSE_LAYOUT) == REFERENCE_CLOSE_FILES
    for fid, cols in MF.CLOSE_LAYOUT.items():
        key = CLOSE_LAYOUT_KEYS.get(fid)
        assert fid in CLOSE_LAYOUT_FILES and cols == ((key,) if key else ()) + ("close",), (fid, cols)
    assert F01_COLUMNS[0] == "close" and set(F01_COLUMNS[1:]) <= set(MF.PROVENANCE_FIELDS)
    assert VB.FIXTURE_COLUMNS == ("obs_date", "close") and set(VB.FIXTURE_COLUMNS) <= set(F01_COLUMNS)
    name = FILE_OF["F13"]
    with tempfile.TemporaryDirectory() as tmp:
        ref, out = Path(tmp) / "ref", Path(tmp) / "out"
        ref.mkdir()
        _fake_reference(ref)
        f13_ref, f27_ref = ref / _reference_row("F13")[1], ref / _reference_row("F27")[1]
        f13_ref.write_text(_invented_reference("F13", _gpost_weekdays(GPOST_DAY, 80)), encoding="utf-8")

        def generate():
            return MF.generate(ref, out, retrieved_at_utc=REFERENCE_RETRIEVED, licence="test licence",
                               owner="package D", available_at=_available_at)
        rows = generate()
        read = {}
        for fid in REFERENCE_CLOSE_FILES:
            text = (out / FILE_OF[fid]).read_bytes().decode("utf-8")
            assert "\r" not in text and text.endswith("\n"), fid
            assert text.split("\n", 1)[0].split(",") == ["date", *MF.CLOSE_LAYOUT[fid], *MF.PROVENANCE_FIELDS], fid
            read[fid] = read_close_layout(fid, text)
        assert [len(read[fid]) for fid in REFERENCE_CLOSE_FILES] == [80, 2, 2, 4]
        # F27, long form: `code` is the row's stock and `series_id` is that same code, so a 000660 row is not labelled
        # 005930 (the shared reader accepts either id of the file; the generator writes the row's own)
        codes = _reference_row("F27")[2].split(";")
        assert [(r["code"], r["series_id"]) for r in read["F27"]] == [(c, c) for _ in range(2) for c in codes]
        # the product reader on the generator's F13
        dates, closes = [r["date"].isoformat() for r in read["F13"]], [r["close"] for r in read["F13"]]
        got_dates, got_closes = VB.fixture_closes(out / name)
        assert got_dates == dates and got_closes.tolist() == closes
        manifest = out / "MANIFEST.csv"
        assert MF.freeze(manifest, [r for r in rows if r["file"] == name]) == 1
        lines = VB.fixture_lines(manifest=manifest)
        want = [dict(x, label=f"FIXTURE G-B5-01: {name}")
                for x in VB.spec_form(dates, np.asarray(closes, dtype=float), "KR", "G-B5-01")]
        assert len(want) == 4 and repr([x for x in lines if x["symbol"] == "G-B5-01"]) == repr(want)
        assert want[0]["sample"] == f"{VB.ORIGINS_FROM}..{dates[-1]} (pool from {dates[1]})", want[0]["sample"]
        rest = [x for x in lines if x["symbol"] != "G-B5-01"]              # SPY and the U1 alias are not listed
        assert [x["symbol"] for x in rest] == ["G-B5-02", "G-B5-03"]
        assert all(x["b5_status"] == "NOT_RUN" and x["label"].startswith("REFDATA: ") for x in rest), rest
        # the generator refuses a reference header without a declared column, and renames none
        good13, good27 = f13_ref.read_text(encoding="utf-8"), f27_ref.read_text(encoding="utf-8")
        f13_ref.write_text(good13.replace("date,close", "Date,Close", 1), encoding="utf-8")
        _refused(generate, ValueError,
                 f"{name}: declared columns ['close'] absent from the reference header ['Date', 'Close']")
        f13_ref.write_text(good13, encoding="utf-8")
        f27_ref.write_text("date,close\n2026-09-30,1\n2026-10-01,2\n", encoding="utf-8")
        _refused(generate, ValueError, f"{FILE_OF['F27']}: declared columns ['code'] absent")
        f27_ref.write_text(good27, encoding="utf-8")
        assert [r["md5"] for r in generate()] == [r["md5"] for r in rows]
        # the product reader refuses what the shared reader refuses in the columns it reads
        text = (out / name).read_text(encoding="utf-8")
        head, *body = text.rstrip("\n").split("\n")
        i_close, i_obs = head.split(",").index("close"), head.split(",").index("obs_date")
        old_layout = text.replace(",close,", ",value,", 1)
        assert old_layout.split("\n", 1)[0].split(",")[1] == "value"

        def edited(line: int, col: int, cell: str) -> str:
            cells = body[line].split(",")
            cells[col] = cell
            return "\n".join([head, *body[:line], ",".join(cells), *body[line + 1:]]) + "\n"
        bad = Path(tmp) / name
        for broken, needle in (
                (old_layout, f"{name}: declared columns ['close'] absent"),
                (edited(4, i_close, "."), f"{name} line 6: close '.' is not a finite number > 0"),
                (edited(4, i_close, ""), f"{name} line 6: close '' is not a finite number > 0"),
                (edited(4, i_close, "-5"), f"{name} line 6: close '-5' is not a finite number > 0"),
                (edited(5, i_obs, dates[4]), f"{name} line 7: rows out of date order or repeated"),
                (edited(4, i_obs, dates[4].replace("-", "")), f"{name} line 6: obs_date '{dates[4].replace('-', '')}'"),
                ("\n".join([head, body[0]]) + "\n", f"{name}: 1 rows; a return needs two closes")):
            bad.write_text(broken, encoding="utf-8")
            _refused(lambda: VB.fixture_closes(bad), ValueError, needle)
        old = Path(tmp) / "old"
        old.mkdir()
        (old / name).write_text(old_layout, encoding="utf-8")
        listed = dict(next(r for r in rows if r["file"] == name), md5=md5_of(old / name))
        assert MF.freeze(old / "MANIFEST.csv", [listed]) == 1
        _refused(lambda: VB.fixture_lines(manifest=old / "MANIFEST.csv"), ValueError,
                 f"{name}: declared columns ['close'] absent")


def test_macro_fixtures_refuses_close_rows_no_reader_accepts():
    """The generator holds a close file to its readers' rules before it writes anything (review of LA-02 part 3: it
    checked column names only, so it wrote, and `freeze` would have md5-listed, close files that both readers then
    refuse). MF.CLOSE_FILES is every file a reader reads in the close layout: the four of owner ruling 1, plus F01 and
    F15, which the same readers read and no ruling names; they declare no reference series. MF.CLOSE_MIN_ROWS is the
    two files the product reader reads. On invented rows over the synthetic signed calendars, through
    `generate(only=...)` with the real calendar function and the post-close check: a blank, "null", ".", zero,
    negative, nan or inf close, a repeated date, newest-first dates, a one-row F13 and a header with no rows are each
    refused naming the reference file and line, and so are an F27 code that is not one of the file's ids, a repeated
    date and code pair and F27 rows out of date order, and a blank close or a repeated date in F01. Each refused run
    leaves no output directory. For every case the same rows, stamped as the generator stamped them before (no row
    rule), are refused by a reader: the shared test reader, or for the one-row file the product reader. A good F13, a
    one-row F14 and a good F27 are written and both readers accept them. F15's rows are held to the same rules, and
    its SPY is still refused when stamped: it is neither registered nor declared."""
    from core.calendars import clocks as K
    from core.calendars.adapter import CalendarClocks
    from core.ficc import contracts
    from docs import vol_backtest as VB
    from tests.macro_m1_calendars import CLOSE_LAYOUT_FILES, fixture_set, read_close_layout
    registry, cal = contracts.default_registry(), fixture_set()
    clk = CalendarClocks(registry, cal=cal)
    available_at, check = MF.calendar_available_at(registry, clk), MF.calendar_check_fixture(registry, clk)
    # the declarations
    assert MF.CLOSE_FILES == {"F01": ("close",), "F15": ("close",), **MF.CLOSE_LAYOUT}
    assert set(MF.CLOSE_FILES) == set(CLOSE_LAYOUT_FILES) | {"F15"}
    product_names = {name for name, _market in VB.FIXTURES.values()}
    product = {fid for fid, rel, *_rest in MF.REFERENCE_FILES if Path(rel).name in product_names}
    assert product == {"F13", "F15"} == set(MF.CLOSE_MIN_ROWS) and set(MF.CLOSE_MIN_ROWS.values()) == {2}
    assert set(MF.REFERENCE_SERIES) == {"KS11", "GSPC", "KRWX", "005930", "000660"}     # F01 and F15 declare none
    assert registry.is_series("KOSPI_OFFICIAL_CLOSE") and not registry.is_series("SPY")
    kr = K.sessions_between("KR", date(2026, 9, 21), GPOST_DAY, cal=cal)
    us = K.sessions_between("US", date(2026, 9, 21), date(2026, 10, 1), cal=cal)
    assert len(kr) >= 5 and len(us) >= 5
    with tempfile.TemporaryDirectory() as tmp:
        ref, out = Path(tmp) / "ref", Path(tmp) / "out"
        ref.mkdir()
        (ref / "CATALOG.md").write_text("invented catalog\n", encoding="utf-8")

        def generate(fid, text, stamp=available_at):
            (ref / _reference_row(fid)[1]).write_text(text, encoding="utf-8")
            return MF.generate(ref, out, retrieved_at_utc=REFERENCE_RETRIEVED, licence="test licence",
                               owner="package D", available_at=stamp, check_fixture=check, only=(fid,))

        def unruled(fid, text) -> str:
            """The fixture the generator wrote before the row rules: the same rows, every one stamped with the file's
            first id (through the stub for F15, whose SPY the calendar function refuses)."""
            src = Path(tmp) / "unruled.csv"
            src.write_text(text, encoding="utf-8")
            _f, _rel, series, status, source, *_rest = _reference_row(fid)
            return MF.fixture_text(*MF.fixture_rows(
                src, series_id=series.split(";")[0], value_status=status, available_at_source=source,
                retrieved_at_utc=REFERENCE_RETRIEVED, available_at=_available_at if fid == "F15" else available_at))

        def cell(lines, i, close) -> str:
            cells = lines[i].split(",")
            return "\n".join(lines[:i] + [",".join(cells[:-1] + [close])] + lines[i + 1:]) + "\n"

        good = {fid: _invented_reference(fid, kr[-3:] if fid == "F27" else us if fid == "F14" else kr)
                for fid in REFERENCE_CLOSE_FILES}
        l13, l27 = good["F13"].rstrip("\n").split("\n"), good["F27"].rstrip("\n").split("\n")
        n13, n27, n01, n14, n15 = (FILE_OF[f] for f in ("F13", "F27", "F01", "F14", "F15"))
        not_a_close = "is not a finite number > 0"
        cases = [("F13", cell(l13, 3, bad), f"{n13} line 4: close {bad!r} {not_a_close}", f"{n13} line 4: close {bad!r}")
                 for bad in ("", "null", ".", "0", "-5", "nan", "inf")]
        cases += [
            ("F13", "\n".join(l13[:4] + [l13[3]] + l13[4:]) + "\n", f"{n13} line 5: rows out of date order or repeated",
             f"{n13} line 5: rows out of date order or repeated"),
            ("F13", "\n".join([l13[0]] + l13[:0:-1]) + "\n", f"{n13} line 3: rows out of date order or repeated",
             f"{n13} line 3: rows out of date order or repeated"),
            ("F13", l13[0] + "\n", f"{n13}: 0 row(s); its readers need at least 2", f"{n13}: no rows"),
            ("F14", good["F14"].split("\n", 1)[0] + "\n", f"{n14}: 0 row(s); its readers need at least 1",
             f"{n14}: no rows"),
            ("F27", good["F27"].replace(",000660,", ",005935,", 1),
             f"{n27} line 3: code '005935' is not one of the file's series ('005930', '000660')",
             f"{n27} line 3: code '005935' not in ('005930', '000660')"),
            ("F27", good["F27"].replace(",005930,", ",5930,", 1),
             f"{n27} line 2: code '5930' is not one of the file's series", f"{n27} line 2: code '5930' not in"),
            ("F27", "\n".join(l27[:3] + [l27[1]] + l27[3:]) + "\n", f"{n27} line 4: rows out of date order or repeated",
             f"{n27} line 4: rows out of date order or repeated"),
            ("F27", "\n".join([l27[0]] + l27[:0:-1]) + "\n", f"{n27} line 4: rows out of date order or repeated",
             f"{n27} line 4: rows out of date order or repeated"),
            ("F27", cell(l27, 2, ""), f"{n27} line 3: close '' {not_a_close}", f"{n27} line 3: close ''"),
            ("F01", cell(l13, 2, "."), f"{n01} line 3: close '.' {not_a_close}", f"{n01} line 3: close '.'"),
            ("F01", "\n".join(l13[:3] + [l13[2]] + l13[3:]) + "\n", f"{n01} line 4: rows out of date order or repeated",
             f"{n01} line 4: rows out of date order or repeated"),
        ]
        assert len(cases) == 18
        for fid, text, needle, reader_needle in cases:
            _refused(lambda: generate(fid, text), ValueError, needle)
            assert not out.exists(), (fid, needle)                              # a refused run writes nothing
            before = unruled(fid, text)                                         # ... and a reader refuses the same rows
            _refused(lambda: read_close_layout(fid, before), AssertionError, reader_needle)
        # a one-row F13: the shared reader takes it, the product reader does not (a return needs two closes)
        one = "\n".join(l13[:2]) + "\n"
        _refused(lambda: generate("F13", one), ValueError, f"{n13}: 1 row(s); its readers need at least 2")
        assert not out.exists() and len(read_close_layout("F13", unruled("F13", one))) == 1
        bad = Path(tmp) / n13
        bad.write_text(unruled("F13", one), encoding="utf-8")
        _refused(lambda: VB.fixture_closes(bad), ValueError, f"{n13}: 1 rows; a return needs two closes")
        # F15 (SPY, the product reader's other file): the same rules; stamping SPY is refused as it always was
        f15 = good["F14"].rstrip("\n").split("\n")
        _refused(lambda: generate("F15", "\n".join(f15[:2]) + "\n", _available_at), ValueError,
                 f"{n15}: 1 row(s); its readers need at least 2")
        _refused(lambda: generate("F15", cell(f15, 2, ""), _available_at), ValueError,
                 f"{n15} line 3: close '' {not_a_close}")
        exc = _refused(lambda: generate("F15", good["F14"]), KeyError)
        assert exc.args == ("SPY: not a registered series id (every fixture series is named)",) and not out.exists()
        # what the readers accept is written: a good F13, a one-row F14, a good F27 (each row stamped with its own code)
        assert [r["file"] for r in generate("F13", good["F13"])] == [n13]
        got = read_close_layout("F13", (out / n13).read_text(encoding="utf-8"))
        assert [r["date"] for r in got] == kr and VB.fixture_closes(out / n13)[0] == [d.isoformat() for d in kr]
        assert [r["span"] for r in generate("F14", "\n".join(f15[:2]) + "\n")] == [f"{us[0]}..{us[0]}"]
        assert len(read_close_layout("F14", (out / n14).read_text(encoding="utf-8"))) == 1
        assert [r["file"] for r in generate("F27", good["F27"])] == [n27]
        f27 = read_close_layout("F27", (out / n27).read_text(encoding="utf-8"))
        assert [(r["date"], r["code"], r["series_id"]) for r in f27] == [
            (d, c, c) for d in kr[-3:] for c in ("005930", "000660")]
        assert sorted(p.name for p in out.iterdir()) == sorted((n13, n14, n27))


def test_macro_fixtures_writes_nothing_when_refused_and_only_the_selected_files():
    """A refused run writes nothing, and `only` selects the files a run writes (review of LA-02 part 3). `generate`
    wrote each file as it went: on a whole invented reference set the real calendar function refuses F02
    (BOK_CALL_RATE has no scheduled publication instant), and by then F01's fixture was in the output directory with
    no manifest row; in tests/fixtures/macro, the default, an unlisted file fails T-HERM-01. It also wrote the whole
    set or nothing, so F13, F14 and F27, which owner rulings 1 and 2 made writable, could not be written from the
    command line. Now every file is built and checked in a temporary directory first: the refused run leaves no
    output directory, and a refused regeneration leaves an earlier generation byte for byte as it was. With
    `only=("F13", "F14", "F27")` a reference directory holding CATALOG.md and those three files is enough: the three
    fixtures are written in REFERENCE_FILES order, pass the post-close check and are frozen; without `only` the same
    directory is refused, listing the other files. An unknown id and an empty selection are refused; a selected file
    that is absent is the only one listed; a selection whose F16 holds a Saturday row (no FX day close, owner ruling
    A-1; before that ruling any F16 was refused) or a file retrieved one second before its bound + 10 min writes none
    of the selected files. The command line takes `--only` and
    writes the same three files and manifest rows, on the calendars it is given."""
    from core.calendars import clocks as K
    from core.calendars.adapter import CalendarClocks
    from core.ficc import contracts, pit
    from tests.macro_m1_calendars import fixture_set, read_close_layout
    from tests.notrun import md5_of
    registry, cal = contracts.default_registry(), fixture_set()
    clk = CalendarClocks(registry, cal=cal)
    available_at, check = MF.calendar_available_at(registry, clk), MF.calendar_check_fixture(registry, clk)
    kwargs = {"licence": "test licence", "owner": "package D"}
    three = ("F13", "F14", "F27")
    names = [FILE_OF[fid] for fid in three]
    # the selection
    assert MF.selected_files() is MF.REFERENCE_FILES and MF.selected_files(None) is MF.REFERENCE_FILES
    assert [r[0] for r in MF.selected_files(("F27", "F13", "F14", "F13"))] == list(three)      # REFERENCE_FILES order
    assert len(MF.selected_files(("F18",))) == len(MF.FRED_IDS) == 17 and len(MF.selected_files(("F10", "F23"))) == 10
    _refused(lambda: MF.selected_files(("F13", "F12")), ValueError, "--only names ['F12']; the fixture ids are F01, F02")
    _refused(lambda: MF.selected_files(()), ValueError, "--only names no fixture id")
    with tempfile.TemporaryDirectory() as tmp:
        # 1. a whole invented set, the real calendar function: refused at F02, and nothing is left behind
        ref, out = Path(tmp) / "ref", Path(tmp) / "out"
        ref.mkdir()
        _fake_reference(ref)
        f01 = ref / _reference_row("F01")[1]
        assert MF.REFERENCE_FILES[0][0] == "F01" and MF.REFERENCE_FILES[1][:3] == (
            "F02", "ecos_bok_call_rate_1997_2026-10.csv", "BOK_CALL_RATE")
        assert len(MF.fixture_rows(f01, series_id="KOSPI_OFFICIAL_CLOSE", value_status="official_close",
                                   available_at_source="calendar_bound", retrieved_at_utc=REFERENCE_RETRIEVED,
                                   available_at=available_at)[1]) == 2                   # F01 itself stamps

        def whole(stamp):
            return MF.generate(ref, out, retrieved_at_utc=REFERENCE_RETRIEVED, available_at=stamp,
                               check_fixture=check if stamp is available_at else None, **kwargs)
        _refused(lambda: whole(available_at), ValueError, "BOK_CALL_RATE: no scheduled publication instant")
        assert not out.exists()
        # 2. an earlier generation (the stub stamps every row) is left byte for byte as it was by a refused regeneration
        rows = whole(_available_at)
        frozen = {p.name: md5_of(p) for p in out.iterdir()}
        assert frozen == {r["file"]: r["md5"] for r in rows} and len(frozen) == len(MF.REFERENCE_FILES)
        f01.write_text("date,close\n2026-09-30,555\n2026-10-01,556\n", encoding="utf-8")   # F01 would change first
        _refused(lambda: whole(available_at), ValueError, "BOK_CALL_RATE: no scheduled publication instant")
        assert {p.name: md5_of(p) for p in out.iterdir()} == frozen
        changed = {r["file"]: r["md5"] for r in whole(_available_at)}                        # the same edit, not refused
        assert [n for n in frozen if changed[n] != frozen[n]] == [FILE_OF["F01"]]
        # 3. `only`: a reference directory holding CATALOG.md and three files
        ref3, out3, manifest = Path(tmp) / "ref3", Path(tmp) / "out3", Path(tmp) / "MANIFEST.csv"
        ref3.mkdir()
        (ref3 / "CATALOG.md").write_text("invented catalog\n", encoding="utf-8")
        kr = K.sessions_between("KR", date(2026, 9, 21), GPOST_DAY, cal=cal)
        us = K.sessions_between("US", date(2026, 9, 21), date(2026, 10, 1), cal=cal)
        for fid in three:
            (ref3 / _reference_row(fid)[1]).write_text(_invented_reference(fid, us if fid == "F14" else kr),
                                                       encoding="utf-8")

        def some(only, retrieved=REFERENCE_RETRIEVED, target=out3):
            return MF.generate(ref3, target, retrieved_at_utc=retrieved, available_at=available_at, check_fixture=check,
                               only=only, **kwargs)
        assert MF.missing_files(ref3, three) == [] and len(MF.missing_files(ref3)) == len(MF.REFERENCE_FILES) - 3
        exc = _refused(lambda: some(None), MF.ReferenceMissing, "incomplete", "sox_daily.csv")
        assert len(exc.missing) == len(MF.REFERENCE_FILES) - 3 and not out3.exists()
        exc = _refused(lambda: some(("F13", "F15")), MF.ReferenceMissing, "1 file(s) missing")
        assert exc.missing == [_reference_row("F15")[1]] and not out3.exists()
        _refused(lambda: some(("F13", "F12")), ValueError, "--only names ['F12']")
        _refused(lambda: some(()), ValueError, "--only names no fixture id")
        # a selection the generator refuses part-way writes none of it: an F16 row dated on a Saturday has no FX day
        # close (owner ruling A-1); a file retrieved one second before its close-print bound + 10 min fails the
        # post-close check on the staged file
        saturday = date(2026, 10, 3)
        (ref3 / _reference_row("F16")[1]).write_text(_invented_reference("F16", us + [saturday]), encoding="utf-8")
        _refused(lambda: some(("F13", "F16")), MF.NoFXDayClose,
                 f"{FILE_OF['F16']} line {len(us) + 2}: KRWX: FX {saturday} is a Saturday")
        early = clk.close_print_bound_utc("KR", GPOST_DAY) + timedelta(minutes=pit.QUARANTINE_MINUTES, seconds=-1)
        _refused(lambda: some(three, retrieved=early), pit.FixtureRefused, "close + 10 min")
        assert not out3.exists()
        got = some(("F27", "F13", "F14", "F13"))
        assert [r["file"] for r in got] == names and sorted(p.name for p in out3.iterdir()) == sorted(names)
        assert [r["md5"] for r in got] == [md5_of(out3 / n) for n in names]
        assert [len(read_close_layout(fid, (out3 / FILE_OF[fid]).read_text(encoding="utf-8"))) for fid in three] == [
            len(kr), len(us), 2 * len(kr)]
        assert MF.freeze(manifest, got) == 3 and set(load_manifest(manifest)) == set(names)
        assert [r["md5"] for r in some(three)] == [r["md5"] for r in got] and MF.freeze(manifest, some(three)) == 0
        # 4. the command line
        out4, manifest4 = Path(tmp) / "out4", Path(tmp) / "MANIFEST4.csv"
        argv = ["--reference", str(ref3), "--out", str(out4), "--manifest", str(manifest4),
                "--retrieved-at-utc", "2026-10-02T09:00:00Z", "--licence", "test licence", "--owner", "package D"]

        class Given:                                 # the clocks handed to the command line, counting their use
            used = 0

            def __getattr__(self, name):
                Given.used += 1
                return getattr(clk, name)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = MF.main(argv + ["--only", *three], clocks=Given())
        assert rc == 0 and buf.getvalue().startswith("3 fixtures written under "), buf.getvalue()
        assert Given.used > 0                        # stamped on the calendars it was given, not on the shipped set
        assert {n: md5_of(out4 / n) for n in names} == {r["file"]: r["md5"] for r in got}
        assert {n: r["md5"] for n, r in load_manifest(manifest4).items()} == {r["file"]: r["md5"] for r in got}
        for extra, needle in ((["--only", "F12"], "--only names ['F12']"), (["--only"], "expected at least one")):
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                try:
                    MF.main(argv + extra, clocks=clk)
                    raise AssertionError(f"{extra}: argparse must refuse")
                except SystemExit as stop:
                    assert stop.code == 2 and needle in err.getvalue(), (extra, err.getvalue())
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = MF.main(argv + ["--only", "F01", "F13"], clocks=clk)
        assert rc == 2 and "1 file(s) missing" in buf.getvalue() and FILE_OF["F01"] in buf.getvalue(), buf.getvalue()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = MF.main(argv, clocks=clk)                                # no --only: the whole set, as before
        assert rc == 2 and f"{len(MF.REFERENCE_FILES) - 4} file(s) missing" in buf.getvalue(), buf.getvalue()
        assert sorted(p.name for p in out4.iterdir()) == sorted(names) and len(load_manifest(manifest4)) == 3


# --------------------------------------------------------------------------- #
# Code review of PR #101 (96cca1f), findings R1 to R5 (⑨-1/2/d/2). Each test below failed on that commit.
# --------------------------------------------------------------------------- #
def _calendar_generator(only, ref: Path, out: Path, **kw):
    """`generate` over the synthetic signed calendars with the real calendar function and the post-close check."""
    from core.calendars.adapter import CalendarClocks
    from core.ficc import contracts
    from tests.macro_m1_calendars import fixture_set
    registry = contracts.default_registry()
    clk = CalendarClocks(registry, cal=fixture_set())
    return MF.generate(ref, out, retrieved_at_utc=kw.pop("retrieved_at_utc", REFERENCE_RETRIEVED), licence="test licence",
                       owner="package D", available_at=MF.calendar_available_at(registry, clk),
                       check_fixture=MF.calendar_check_fixture(registry, clk), only=only, **kw)


def test_macro_fixtures_long_form_date_order_is_per_code():
    """R2: the long form (F27) is in date order code by code. The generator refused a file grouped by code (every row
    of 005930, then every row of 000660) at its first 000660 row, and so did the reader (tests/macro_m1_calendars
    .test_close_layout_long_form_date_order_is_per_code). No consumer of F27 rows reads them by position: both
    G-POST-01 sites pick a row by code and date. The one thing that did was the manifest `span`, taken from the first
    and last row. Now F27 in date order and grouped by code are both written, row for row in the reference order, and
    the reader takes either with the same rows per code; the span is the file's first and last observation, also when
    the codes end on different days. Still refused, naming the file and line, with the last good generation left as
    it was: a code's dates out of order, a repeated date and code pair, a code that is not one of the file's ids."""
    from core.calendars import clocks as K
    from tests.macro_m1_calendars import fixture_set, read_close_layout
    days = K.sessions_between("KR", date(2026, 9, 21), GPOST_DAY, cal=fixture_set())
    codes = tuple(_reference_row("F27")[2].split(";"))
    name, n = FILE_OF["F27"], len(days)
    with tempfile.TemporaryDirectory() as tmp:
        ref, out = Path(tmp) / "ref", Path(tmp) / "out"
        ref.mkdir()
        (ref / "CATALOG.md").write_text("invented catalog\n", encoding="utf-8")

        def generate(pairs):
            (ref / _reference_row("F27")[1]).write_text("date,code,close\n" + "".join(
                f"{d},{c},{1000 + 10 * days.index(d) + (c == codes[1])}\n" for d, c in pairs), encoding="utf-8")
            return _calendar_generator(("F27",), ref, out)
        by_date = [(d, c) for d in days for c in codes]
        by_code = [(d, c) for c in codes for d in days]
        read = {}
        for label, pairs in (("by date", by_date), ("by code", by_code)):
            rows = generate(pairs)
            assert [r["span"] for r in rows] == [f"{days[0]}..{days[-1]}"], (label, rows)
            got = read_close_layout("F27", (out / name).read_text(encoding="utf-8"))
            assert [(r["date"], r["code"], r["series_id"]) for r in got] == [(d, c, c) for d, c in pairs], label
            read[label] = sorted((r["code"], r["date"], r["close"], r["obs_utc"], r["available_at_utc"]) for r in got)
        assert read["by date"] == read["by code"] and len(read["by code"]) == 2 * n
        short = [(d, codes[0]) for d in days] + [(d, codes[1]) for d in days[:-2]]      # 000660 ends two sessions early
        assert [r["span"] for r in generate(short)] == [f"{days[0]}..{days[-1]}"]
        before = (out / name).read_bytes()
        for pairs, needle in (
                (by_code[:n + 2] + [by_code[n + 3], by_code[n + 2]] + by_code[n + 4:],
                 f"{name} line {n + 5}: rows out of date order or repeated"),
                (by_code[:n + 1] + [by_code[n]] + by_code[n + 1:], f"{name} line {n + 3}: rows out of date order or repeated"),
                ([(d, "005935" if i == n else c) for i, (d, c) in enumerate(by_code)],
                 f"{name} line {n + 2}: code '005935' is not one of the file's series ('005930', '000660')")):
            _refused(lambda: generate(pairs), ValueError, needle)
            assert (out / name).read_bytes() == before


def test_macro_fixtures_finds_the_date_column_by_name():
    """R3: the observation date was read from the first column whatever its name, and parsed unguarded, so F27 with
    `code` before `date`, or a malformed or blank date, ended in a bare "Invalid isoformat string" with no file or
    line. Now the date column is the header cell named `date` in any letter case, or FRED's `observation_date` (the
    names core/ficc/data.py reads FRED rows by), wherever it stands, and `date` when both are present. F27 with `code`
    first is written with its columns unchanged and in their order, stamped as the same rows with `date` first. A
    date that is not ISO (2026/10/02, blank) and a header with two date columns are refused naming the reference file
    (and the line), and nothing is written. Follow-up of the independent check: the first ten characters were taken,
    so 2026-09-301 became 2026-09-30 and 2026-W40-3 was read without a word; these are now refused with the file and
    line. A leading byte order mark is dropped when the file is read, so F27 with `code` first saved as Excel's
    "CSV UTF-8" is no longer refused as lacking `code`. A row with fewer or more cells than the header is refused with
    the file and line (it ended in a bare TypeError or "dict contains fields not in fieldnames"). Review of PR #107,
    F1: R3 also refused what the generator read before it, a header with no date name (it read the first column) and
    a cell written YYYYMMDD (date.fromisoformat takes it on Python 3.11 and later). Now such a header falls back to
    its first column, so `code,day,close` is refused at its first row naming `code` as the first column, and a cell
    of exactly eight digits YYYYMMDD is read as that date; every other shape above stays refused
    (test_macro_fixtures_reads_the_first_column_and_basic_dates_as_before_r3 covers the fallback). Since the fallback,
    a date name the lookup failed to recognise would pass unseen where it stands first, so `observation_date` and
    ` Date ` (blanks around the name) are also tested where they are not first; and a YYYYMMDD cell written in
    full-width digits is refused (only ASCII digits are read)."""
    from core.calendars import clocks as K
    from tests.macro_m1_calendars import fixture_set, read_close_layout
    days = K.sessions_between("KR", date(2026, 9, 28), GPOST_DAY, cal=fixture_set())
    codes = tuple(_reference_row("F27")[2].split(";"))
    name = FILE_OF["F27"]
    with tempfile.TemporaryDirectory() as tmp:
        ref = Path(tmp) / "ref"
        ref.mkdir()
        (ref / "CATALOG.md").write_text("invented catalog\n", encoding="utf-8")

        def generate(text, out):
            (ref / _reference_row("F27")[1]).write_text(text, encoding="utf-8")
            return _calendar_generator(("F27",), ref, out)
        pairs = [(d, c) for d in days for c in codes]
        code_first = "code,date,close\n" + "".join(f"{c},{d},{1000 + i}\n" for i, (d, c) in enumerate(pairs))
        date_first = "date,code,close\n" + "".join(f"{d},{c},{1000 + i}\n" for i, (d, c) in enumerate(pairs))
        out_cd, out_dc = Path(tmp) / "out_cd", Path(tmp) / "out_dc"
        generate(code_first, out_cd)
        generate(date_first, out_dc)
        text_cd, text_dc = ((o / name).read_text(encoding="utf-8") for o in (out_cd, out_dc))
        assert text_cd.split("\n", 1)[0].split(",")[:3] == ["code", "date", "close"]    # columns unchanged, in order
        got_cd, got_dc = read_close_layout("F27", text_cd), read_close_layout("F27", text_dc)
        assert [(r["date"], r["code"]) for r in got_cd] == pairs and got_cd == got_dc
        # refusals name the file and the line; nothing is written
        out = Path(tmp) / "out"
        lines = code_first.rstrip("\n").split("\n")
        n = len(lines)
        for text, needle in (
                (code_first.replace(f",{days[2]},", f",{days[2].strftime('%Y/%m/%d')},", 1),
                 f"{name} line 6: date '{days[2].strftime('%Y/%m/%d')}' in column 'date' is not an ISO date"),
                ("\n".join(lines[:3] + [lines[3].replace(f",{days[1]},", ",,")] + lines[4:]) + "\n",
                 f"{name} line 4: date '' in column 'date' is not an ISO date"),
                (code_first + "005930\n", f"{name} line {n + 1}: 1 cell(s), the header has 3"),
                (code_first.replace(f",{days[2]},", f",{days[2]}1,", 1),           # a typed extra digit
                 f"{name} line 6: date '{days[2]}1' in column 'date' is not an ISO date"),
                (code_first.replace("code,date,close", "code,day,close", 1),            # F1: the first column
                 f"{name} line 2: date '{codes[0]}' in column 'code' (the first column: no header cell is named date "
                 "or observation_date) is not an ISO date"),
                (code_first.replace("code,date,close", "code,date,close,Date", 1),
                 f"{name}: more than one date column ['date', 'Date']")):
            _refused(lambda: generate(text, out), ValueError, needle)
            assert not out.exists(), needle
        # F27 with `code` first saved with a byte order mark (Excel's "CSV UTF-8"): the mark hides no declared column,
        # and the fixture is the one written from the same file without the mark
        out_bom = Path(tmp) / "out_bom"
        generate("\ufeff" + code_first, out_bom)
        assert (out_bom / name).read_bytes() == (out_cd / name).read_bytes()
        # an undeclared file: Yahoo's `Date`, FRED's `DATE` and `observation_date` (first, and last, where the first
        # column cannot stand in for it), a byte order mark, the date last, the name with blanks around it; with both
        # `date` and `observation_date` the date is read from `date`
        src = Path(tmp) / "plain.csv"

        def obs_dates(text):
            src.write_text(text, encoding="utf-8")
            _fields, rows = MF.fixture_rows(src, series_id="DGS10", value_status="first_release",
                                            available_at_source="calendar_bound", retrieved_at_utc=REFERENCE_RETRIEVED,
                                            available_at=_available_at)
            return [r["obs_date"] for r in rows]
        for head, body in (("Date,Close", "{d},4.1"), ("DATE,DGS10", "{d},4.1"), ("observation_date,DGS10", "{d},4.1"),
                           ("DGS10,observation_date", "4.1,{d}"), ("\ufeffdate,value", "{d},4.1"),
                           ("value,Date", "4.1,{d}"), ("value, Date ", "4.1,{d}"),
                           ("observation_date,date,value", "2026-01-02,{d},4.1")):
            assert obs_dates(head + "\n" + "".join(body.format(d=d) + "\n" for d in days[:2])) == [
                d.isoformat() for d in days[:2]], head
        # a date cell is YYYY-MM-DD, alone or followed by 'T' or a space and a time (as pandas writes a timestamp), or
        # exactly eight ASCII digits YYYYMMDD (F1): the date as written. Anything else is refused with the file and
        # line, the week date Python's own ISO parser also takes (2026-W40-3) and full-width digits (which the regular
        # expression class \d would take) included; so are the week dates and the times after the date that the
        # generator before R3 read through its first ten characters (2026W404, 2026-10-01T16, ... EST, T24:00)
        for cell in ("2026-10-01 00:00:00", "2026-10-01T00:00:00Z", "2026-10-01 00:00:00+09:00", " 2026-10-01 ",
                     "2026-10-01T23:59:59.5-04:00", "20261001", " 20261001 "):
            assert obs_dates(f"DATE,DGS10\n2026-09-30,4.1\n{cell},4.2\n") == ["2026-09-30", "2026-10-01"], cell
        wide = "".join(chr(0xFF10 + int(c)) for c in "20261001")             # 20261001 in full-width digits
        for cell in ("not-a-date", "2026-10-011", "2026-W40-4", "2026-10-01Tjunk", "2026-10-01 25:00", "2026-13-01",
                     "2026-10-01x", "2026-10-01xyz", "2026/10/01", "", "202610011", "2026101", "202610", "20261301",
                     "20261032", "20261001T00:00", "20261001 00:00:00", "2026-1001", "+20261001", wide,
                     f"{wide[:4]}-{wide[4:6]}-{wide[6:]}", "2026W404", "2026-10-01T16", "2026-10-01 16:00:00 EST",
                     "2026-10-01T24:00", "20261001T1600"):
            _refused(lambda: obs_dates(f"DATE,DGS10\n2026-09-30,4.1\n{cell},4.2\n"), ValueError,
                     f"plain.csv line 3: date '{cell}' in column 'DATE' is not an ISO date written YYYY-MM-DD "
                     "(a time may follow after 'T' or a space) or YYYYMMDD")
        # a row with fewer or more cells than the header, in a file without the close rules: named with its line
        for text, needle in (("DATE,DGS10\n2026-09-30,4.1\n2026-10-01\n", "plain.csv line 3: 1 cell(s), the header has 2"),
                             ("DATE,DGS10\n2026-09-30,4.1\n2026-10-01,4.2,9\n",
                              "plain.csv line 3: 3 cell(s), the header has 2")):
            _refused(lambda: obs_dates(text), ValueError, needle)


def test_macro_fixtures_reads_the_first_column_and_basic_dates_as_before_r3():
    """Review of PR #107, F1: R3 found the date column only by its name and took only YYYY-MM-DD, so it refused files
    the generator read before (the first column, through date.fromisoformat): Ken French's raw daily layout (a blank
    first header cell, dates written YYYYMMDD), a first column with another name, a `date` column written YYYYMMDD.
    No real reference file has been checked against either rule. Now a header with no cell named date or
    observation_date falls back to its first column, and a cell of exactly eight digits is read as that calendar
    date, so these files come out with the observation dates the generator gave them before R3. The date cell is
    copied as written (the fixture keeps 19261103), and obs_date and session_date are written YYYY-MM-DD; the readers
    of the fixtures read those, so F13 dated YYYYMMDD goes through the real calendar function and the post-close check
    and is read by the shared reader and by docs/vol_backtest.fixture_closes exactly as F13 dated YYYY-MM-DD is. A
    first column that holds no dates is refused naming the file, the line and the column as the first column."""
    from core.calendars import clocks as K
    from docs import vol_backtest as VB
    from tests.macro_m1_calendars import fixture_set, read_close_layout
    days = K.sessions_between("KR", date(2026, 9, 21), GPOST_DAY, cal=fixture_set())
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "plain.csv"

        def stamped(text):
            src.write_text(text, encoding="utf-8")
            return MF.fixture_rows(src, series_id="FRENCH_MOM_D", value_status="vendor_derived",
                                   available_at_source="published", retrieved_at_utc=REFERENCE_RETRIEVED,
                                   available_at=_available_at)
        # Ken French's raw daily layout: the first header cell blank, the dates YYYYMMDD; the cell is copied as written
        fields, rows = stamped(",Mom   \n19261103,   0.56\n19261104,  -0.12\n")
        assert fields[:2] == ["", "Mom   "] and [(r[""], r["obs_date"], r["session_date"]) for r in rows] == [
            ("19261103", "1926-11-03", "1926-11-03"), ("19261104", "1926-11-04", "1926-11-04")]
        assert MF.fixture_text(fields, rows).split("\n")[1].startswith("19261103,   0.56,FRENCH_MOM_D,1926-11-03,")
        for head, cells in (("day,value", ("2026-09-30,4.1", "2026-10-01,4.2")),         # another first-column name
                            ("Day,value", ("20260930,4.1", "20261001,4.2")),
                            ("date,value", ("20260930,4.1", "20261001,4.2")),          # the named column, YYYYMMDD
                            ("\ufeff,Mom", ("20260930,0.5", "20261001,0.6")),           # a byte order mark before ""
                            ("value,DATE", ("4.1,20260930", "4.2,20261001"))):         # named, not first
            got = [r["obs_date"] for r in stamped(head + "\n" + "".join(c + "\n" for c in cells))[1]]
            assert got == ["2026-09-30", "2026-10-01"], head
        # the byte order mark is gone when the header is read (utf-8-sig), so `_date_column` strips none (F9)
        fields, _rows = stamped("\ufeffDate,value\n20260930,4.1\n")
        assert fields[:2] == ["Date", "value"] and MF._date_column(src, fields) == "Date"
        _refused(lambda: stamped("value,day\n4.1,2026-09-30\n"), ValueError,
                 "plain.csv line 2: date '4.1' in column 'value' (the first column: no header cell is named date or "
                 "observation_date) is not an ISO date")
        # F13 dated YYYYMMDD and dated YYYY-MM-DD: the same rows for both readers of the declared close layout
        ref = Path(tmp) / "ref"
        ref.mkdir()
        (ref / "CATALOG.md").write_text("invented catalog\n", encoding="utf-8")
        f13, name = ref / _reference_row("F13")[1], FILE_OF["F13"]
        iso = _invented_reference("F13", days)
        basic = iso.replace("-", "")
        assert iso.count("-") == 2 * len(days) and basic.split("\n")[1].startswith(days[0].strftime("%Y%m%d") + ",")
        read = {}
        for label, text in (("iso", iso), ("basic", basic)):
            f13.write_text(text, encoding="utf-8")
            out = Path(tmp) / label
            assert [r["span"] for r in _calendar_generator(("F13",), ref, out)] == [f"{days[0]}..{days[-1]}"], label
            fixture = (out / name).read_text(encoding="utf-8")
            assert fixture.split("\n")[1].split(",")[0] == text.split("\n")[1].split(",")[0], label   # as written
            read[label] = (read_close_layout("F13", fixture), VB.fixture_closes(out / name)[0])
        assert read["basic"] == read["iso"] and [r["date"] for r in read["basic"][0]] == days
        assert read["basic"][1] == [d.isoformat() for d in days]


def test_macro_fixtures_names_the_reference_row_of_every_calendar_refusal():
    """Review of PR #107, F4: of the refusals `available_at` raises for a reference row, only NoFXDayClose was
    re-raised with the reference file and line; a KS11 row on a day that is not a KRX session (NotASession), a date
    outside the calendar's coverage (CalendarCoverageError), an id neither registered nor declared (KeyError) and a
    value_status other than the declared one (ValueError) named only the series and the date. Now each reaches the
    caller with the type and str() `available_at` gave it, plus a note naming the reference file, the line, the date
    cell and the series, which the traceback prints under the message (Python 3.11 and later); `generate` writes
    nothing. NoFXDayClose keeps its own message with the file and line, and gets no note. A refusal raised from another
    error keeps that cause: KS11 on clocks that lack the KR market is the KeyError `available_at` raises from the
    clocks' own KeyError, which stays its __cause__ (the note is added and the same exception raised again)."""
    import sys
    import traceback
    from core.calendars.adapter import CalendarClocks
    from core.calendars.store import CalendarCoverageError, NotASession
    from core.ficc import contracts
    from tests.macro_m1_calendars import fixture_set
    registry = contracts.default_registry()
    clk = CalendarClocks(registry, cal=fixture_set())
    available_at = MF.calendar_available_at(registry, clk)
    good, saturday, early = date(2026, 10, 1), date(2026, 10, 3), date(1980, 1, 3)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "reference.csv"

        def stamped(sid, status, days):
            src.write_text("date,close\n" + "".join(f"{d},{100 + i}\n" for i, d in enumerate(days)), encoding="utf-8")
            return MF.fixture_rows(src, series_id=sid, value_status=status, available_at_source="calendar_bound",
                                   retrieved_at_utc=REFERENCE_RETRIEVED, available_at=available_at, columns=("close",))

        def direct(sid, status, day, exc_type):
            try:
                available_at(sid, day, status)
            except exc_type as exc:
                return str(exc)
            raise AssertionError(f"available_at({sid}, {day}) did not raise {exc_type.__name__}")
        for sid, status, days, exc_type in (("KS11", "vendor_close", (good, saturday), NotASession),
                                            ("KS11", "vendor_close", (early,), CalendarCoverageError),
                                            ("NOPE", "vendor_close", (good,), KeyError),
                                            ("KS11", "official_close", (good,), ValueError)):
            day, line = days[-1], len(days) + 1
            note = (f"reference row: reference.csv line {line}, date '{day}' in column 'date', series {sid}; no "
                    "fixture is written")
            try:
                stamped(sid, status, days)
                raise AssertionError(f"{sid} {day}: not refused")
            except exc_type as exc:
                assert type(exc) is exc_type and str(exc) == direct(sid, status, day, exc_type), (sid, day, exc)
                assert getattr(exc, "__notes__", None) == [note], (sid, day, getattr(exc, "__notes__", None))
                if sys.version_info >= (3, 11):
                    assert note in "".join(traceback.format_exception(exc)), (sid, day)
        # a refusal raised from another error keeps its cause: the clocks lack the KR market (as a calendar set
        # without it would), so KS11 is refused with the KeyError `available_at` raises from the clocks' KeyError

        class NoKR:
            def __getattr__(self, name):
                return getattr(clk, name)

            def decision_time_utc(self, market, day):
                if market == "KR":
                    raise KeyError("KR: no calendar in this set")
                return clk.decision_time_utc(market, day)
        src.write_text(f"date,close\n{good},100\n", encoding="utf-8")
        no_kr = MF.calendar_available_at(registry, NoKR())
        exc = _refused(lambda: MF.fixture_rows(src, series_id="KS11", value_status="vendor_close",
                                               available_at_source="calendar_bound",
                                               retrieved_at_utc=REFERENCE_RETRIEVED, available_at=no_kr,
                                               columns=("close",)),
                       KeyError, "KS11: no market calendar for its REFERENCE_FILES market 'KR'")
        assert type(exc.__cause__) is KeyError and exc.__cause__.args == ("KR: no calendar in this set",), exc.__cause__
        assert exc.__notes__ == [f"reference row: reference.csv line 2, date '{good}' in column 'date', series KS11; "
                                 "no fixture is written"]
        # NoFXDayClose: its message names the file and line as before, and no note repeats them
        exc = _refused(lambda: stamped("KRWX", "vendor_close", (good, saturday)), MF.NoFXDayClose,
                       f"reference.csv line 3: KRWX: FX {saturday} is a Saturday", "no fixture is written")
        assert getattr(exc, "__notes__", None) is None
        # through `generate` on the real calendar function: refused, the reference file and line named, nothing written
        ref, out = Path(tmp) / "ref", Path(tmp) / "out"
        ref.mkdir()
        (ref / "CATALOG.md").write_text("invented catalog\n", encoding="utf-8")
        (ref / _reference_row("F13")[1]).write_text(f"date,close\n2026-09-30,100\n{good},101\n{saturday},102\n",
                                                    encoding="utf-8")
        try:
            _calendar_generator(("F13",), ref, out)
            raise AssertionError("a KS11 row on a Saturday must be refused")
        except NotASession as exc:
            assert exc.__notes__ == [f"reference row: {FILE_OF['F13']} line 4, date '{saturday}' in column 'date', "
                                     "series KS11; no fixture is written"]
        assert not out.exists()


def test_macro_fixtures_copies_result_tables_byte_for_byte():
    """R5: a result table was read as text and written with LF line ends, so a CRLF table was not copied byte for
    byte although REFERENCE_FILES says it is, and a byte that is not UTF-8 stopped the run. Now the bytes are copied:
    CRLF, LF, no final line end, a byte that is not UTF-8 and a byte order mark all come out identical, the md5 listed
    is the md5 of the bytes on disk, `freeze` lists it and the fixture gate (`require_fixture`) accepts the file.
    Review of PR #107, F7: the table was also written to the staging directory, where nothing reads it (no check
    runs on a result table; the md5 and the final write use the bytes in memory); it is no longer staged, so the
    one write of it is the final one into the output directory."""
    from tests.notrun import md5_of, unlisted
    rel, name = _reference_row("F20")[1], FILE_OF["F20"]
    with tempfile.TemporaryDirectory() as tmp:
        ref, out = Path(tmp) / "ref", Path(tmp) / "out"
        (ref / "results").mkdir(parents=True)
        (ref / "CATALOG.md").write_text("invented catalog\n", encoding="utf-8")
        for label, data in (("CRLF", b"golden_id,sub_id,value\r\nG-POST-01,gkr05_share,0.42\r\n"),
                            ("LF", b"golden_id,sub_id,value\nG-POST-01,gkr05_share,0.42\n"),
                            ("no final line end", b"item,value\nF20,1"),
                            ("a byte that is not UTF-8", b"item,value\nF20,\xff\n"),
                            ("a byte order mark and CRLF", b"\xef\xbb\xbfitem,value\r\nF20,1\r\n")):
            (ref / rel).write_bytes(data)
            staged, real = [], MF._atomic_write
            MF._atomic_write = lambda path, data: (staged.append(Path(path)), real(path, data))[1]
            try:
                rows = MF.generate(ref, out, retrieved_at_utc=REFERENCE_RETRIEVED, licence="test licence",
                                   owner="package D", available_at=_available_at, only=("F20",))
            finally:
                MF._atomic_write = real
            assert staged == [], (label, staged)                       # F7: not staged; written once, by `_commit`
            assert (out / name).read_bytes() == data, label
            assert [r["md5"] for r in rows] == [hashlib.md5(data).hexdigest()] == [md5_of(out / name)], label
            assert rows[0]["span"] == "result table" and rows[0]["value_status_rule"].startswith("result table"), label
        manifest = out / "MANIFEST.csv"
        assert MF.freeze(manifest, rows) == 1 and load_manifest(manifest)[name]["md5"] == md5_of(out / name)
        assert b"\r" not in manifest.read_bytes()                       # the manifest itself is written with LF
        assert require_fixture(name, manifest=manifest) == out / name and unlisted(manifest) == []


def test_macro_fixtures_command_line_counts_the_appended_rows_once():
    """Review of PR #107, F8: the command line read the manifest a second time only to count the rows it appended,
    while `_manifest_bytes` had counted them for the final write and the count was dropped. Now `MF._generate`
    returns that count with the rows and `main` prints it, so the manifest is read once per run (not at all while it
    is absent) and the count is the one the final write used. The printed line keeps its wording: a first run
    appends 1 row, the same run again 0, a run adding a second file 1."""
    from core.calendars.adapter import CalendarClocks
    from core.ficc import contracts
    from tests.macro_m1_calendars import fixture_set
    clk = CalendarClocks(contracts.default_registry(), cal=fixture_set())
    with tempfile.TemporaryDirectory() as tmp:
        ref, out = Path(tmp) / "ref", Path(tmp) / "out"
        manifest = out / "MANIFEST.csv"
        (ref / "results").mkdir(parents=True)
        (ref / "CATALOG.md").write_text("invented catalog\n", encoding="utf-8")
        for fid in ("F20", "F21"):
            (ref / _reference_row(fid)[1]).write_bytes(f"item,value\n{fid},1\n".encode("utf-8"))
        reads, real = [], MF.load_manifest

        def run(*only):
            argv = ["--reference", str(ref), "--out", str(out), "--manifest", str(manifest), "--retrieved-at-utc",
                    "2026-10-02T09:00:00Z", "--licence", "test licence", "--owner", "package D", "--only", *only]
            reads.clear()
            printed = io.StringIO()
            MF.load_manifest = lambda path: (reads.append(Path(path)), real(path))[1]
            try:
                with contextlib.redirect_stdout(printed):
                    assert MF.main(argv, clocks=clk) == 0
            finally:
                MF.load_manifest = real
            return printed.getvalue(), len(reads)
        for only, written, appended, read in ((("F20",), 1, 1, 0), (("F20",), 1, 0, 1), (("F20", "F21"), 2, 1, 1)):
            assert run(*only) == (f"{written} fixtures written under {out}; {appended} manifest rows appended to "
                                  f"{manifest}\n", read), (only, appended, read)
        assert sorted(load_manifest(manifest)) == sorted(FILE_OF[f] for f in ("F20", "F21"))


def test_macro_fixtures_compares_the_manifest_before_the_final_write():
    """R1: on the command line `generate` wrote the output directory and only then did `freeze` compare the md5s, so
    a regeneration refused with FixtureChanged had already overwritten the frozen file, which then no longer matched
    its manifest row. Now the built files are compared with the manifest before anything is written: the refused
    regeneration leaves every frozen byte and the manifest as they were, with a new file selected beside the changed
    one nothing is written either, and `generate(manifest=...)` refuses the same way. An unchanged regeneration
    rewrites the same bytes and adds no row, also when the manifest writes its md5 in upper case, and the manifest is
    written with LF line ends; once the reference is restored the new file is written and listed. The
    manifest is written in the same final write as the fixtures, last (R4): with MANIFEST.csv locked, a run that
    adds a file fails and leaves that file neither written nor unlisted (`freeze` used to write the manifest after
    the fixtures were in place, so the new file stayed in the folder with no manifest row)."""
    from core.calendars import clocks as K
    from core.calendars.adapter import CalendarClocks
    from core.ficc import contracts
    from tests.macro_m1_calendars import fixture_set
    from tests.notrun import unlisted
    cal = fixture_set()
    clk = CalendarClocks(contracts.default_registry(), cal=cal)
    kr = K.sessions_between("KR", date(2026, 9, 21), GPOST_DAY, cal=cal)
    us = K.sessions_between("US", date(2026, 9, 21), date(2026, 10, 1), cal=cal)
    n13, n14 = FILE_OF["F13"], FILE_OF["F14"]
    with tempfile.TemporaryDirectory() as tmp:
        ref, out = Path(tmp) / "ref", Path(tmp) / "out"
        manifest = out / "MANIFEST.csv"
        ref.mkdir()
        (ref / "CATALOG.md").write_text("invented catalog\n", encoding="utf-8")
        f13, f14 = ref / _reference_row("F13")[1], ref / _reference_row("F14")[1]
        good13 = _invented_reference("F13", kr)
        f13.write_text(good13, encoding="utf-8")
        f14.write_text(_invented_reference("F14", us), encoding="utf-8")

        def run(*only):
            argv = ["--reference", str(ref), "--out", str(out), "--manifest", str(manifest), "--retrieved-at-utc",
                    "2026-10-02T09:00:00Z", "--licence", "test licence", "--owner", "package D", "--only", *only]
            with contextlib.redirect_stdout(io.StringIO()):
                return MF.main(argv, clocks=clk)

        def state():
            return {p.name: p.read_bytes() for p in out.iterdir()}
        assert run("F13") == 0
        frozen = state()
        md5 = hashlib.md5(frozen[n13]).hexdigest()
        assert sorted(frozen) == sorted(["MANIFEST.csv", n13]) and unlisted(manifest) == []
        assert load_manifest(manifest)[n13]["md5"] == md5 and b"\r" not in frozen["MANIFEST.csv"]
        assert run("F13") == 0 and state() == frozen                     # the same reference: same bytes, no new row
        # an md5 the manifest writes in upper case is the same md5: the unchanged regeneration is not refused
        upper = frozen["MANIFEST.csv"].replace(md5.encode(), md5.upper().encode())
        assert upper != frozen["MANIFEST.csv"]
        manifest.write_bytes(upper)
        assert run("F13") == 0 and manifest.read_bytes() == upper
        manifest.write_bytes(frozen["MANIFEST.csv"])
        lines = good13.rstrip("\n").split("\n")
        f13.write_text("\n".join(lines[:-1] + [lines[-1].rsplit(",", 1)[0] + ",9999.00"]) + "\n", encoding="utf-8")
        _refused(lambda: run("F13"), MF.FixtureChanged, f"{n13}: {md5} -> ", "L5492")
        assert state() == frozen and unlisted(manifest) == []
        _refused(lambda: run("F13", "F14"), MF.FixtureChanged, f"{n13}: {md5} -> ")
        assert state() == frozen                                         # F14 is not written either
        _refused(lambda: _calendar_generator(("F13",), ref, out, manifest=manifest), MF.FixtureChanged, n13)
        assert state() == frozen
        f13.write_text(good13, encoding="utf-8")
        # R4 on the command line: the manifest is the last file of the same final write. With MANIFEST.csv locked (on
        # Windows, open in a spreadsheet) a run that adds F14 fails and leaves no F14 that the manifest does not list
        import os
        real = os.replace

        def locked(src, dst, *args, **kwargs):
            if Path(dst) == manifest:
                raise PermissionError(13, "simulated: MANIFEST.csv is open in another program", str(dst))
            return real(src, dst, *args, **kwargs)
        os.replace = locked
        try:
            _refused(lambda: run("F13", "F14"), PermissionError, "simulated: MANIFEST.csv")
        finally:
            os.replace = real
        assert state() == frozen and unlisted(manifest) == []
        assert run("F13", "F14") == 0
        after = state()
        assert after[n13] == frozen[n13] and sorted(after) == sorted(["MANIFEST.csv", n13, n14])
        assert sorted(load_manifest(manifest)) == sorted([n13, n14]) and unlisted(manifest) == []


def test_macro_fixtures_final_write_is_all_or_nothing():
    """R4: the final write renamed one file after another into the output directory, so a rename that failed part way
    (on Windows, a destination open in another program) left the earlier files new and the rest old, and on a first
    generation left files no manifest lists. Now (`MF._commit`) every file is written whole beside its destination and
    the bytes it replaces are read first, then the renames run, and a failure undoes the renames already made. With
    the second of three files locked: a regeneration leaves every byte as it was, a first generation leaves no output
    directory (nor the parent directories it created), and the error reaching the caller is the PermissionError
    itself; a Ctrl+C (KeyboardInterrupt) at the same rename is undone the same way. A destination that cannot be read
    (here a directory with a fixture's name) stops the run before any
    rename. If the undo itself fails, FinalWriteIncomplete names the file left with its new bytes, and that is the
    only file changed. No temporary file is left in any case. What a stopped process can leave is stated in
    `MF._commit` and is not demonstrated here."""
    import os
    from tests.notrun import md5_of
    three = ("F13", "F14", "F27")
    n13, n14, n27 = (FILE_OF[f] for f in three)
    with tempfile.TemporaryDirectory() as tmp:
        ref = Path(tmp) / "ref"
        ref.mkdir()
        (ref / "CATALOG.md").write_text("invented catalog\n", encoding="utf-8")

        def write_reference(base):
            for fid, b in (("F13", base), ("F14", base + 100)):
                (ref / _reference_row(fid)[1]).write_text(f"date,close\n2026-09-30,{b}\n2026-10-01,{b + 1}\n",
                                                          encoding="utf-8")
            (ref / _reference_row("F27")[1]).write_text(f"date,code,close\n2026-10-01,005930,{base}\n"
                                                        f"2026-10-01,000660,{base + 1}\n", encoding="utf-8")

        def generate(out):
            return MF.generate(ref, out, retrieved_at_utc=REFERENCE_RETRIEVED, licence="test licence",
                               owner="package D", available_at=_available_at, only=three)

        def state(out):
            return {p.name: p.read_bytes() if p.is_file() else "a directory" for p in out.iterdir()}
        real = os.replace

        def with_locked(out, fn, fail_restore_of=None, error=None):
            """Run `fn` with every rename onto out/F14 refused (with `error`, by default a PermissionError), and the
            second rename onto `fail_restore_of` too."""
            seen: dict = {}

            def replace(src, dst, *args, **kwargs):
                dst = Path(dst)
                if dst.parent == out:                                     # renames into `out` only, not the staging
                    seen[dst.name] = seen.get(dst.name, 0) + 1
                    if dst.name == n14 or (dst.name == fail_restore_of and seen[dst.name] > 1):
                        raise error or PermissionError(13, "simulated: the file is open in another program", str(dst))
                return real(src, dst, *args, **kwargs)
            os.replace = replace
            try:
                return fn()
            finally:
                os.replace = real
        write_reference(100)
        out = Path(tmp) / "out"
        rows = generate(out)
        frozen = state(out)
        assert sorted(frozen) == sorted([n13, n14, n27]) and {r["file"]: r["md5"] for r in rows} == {
            n: hashlib.md5(b).hexdigest() for n, b in frozen.items()}
        write_reference(500)                                              # every file would change
        _refused(lambda: with_locked(out, lambda: generate(out)), PermissionError, "simulated", n14)
        assert state(out) == frozen
        # Ctrl+C at the second rename (KeyboardInterrupt is not an Exception): undone the same way, then re-raised
        _refused(lambda: with_locked(out, lambda: generate(out), error=KeyboardInterrupt("simulated Ctrl+C")),
                 KeyboardInterrupt, "simulated Ctrl+C")
        assert state(out) == frozen
        fresh = Path(tmp) / "new" / "deeper" / "out"                      # a first generation, two parents created
        _refused(lambda: with_locked(fresh, lambda: generate(fresh)), PermissionError, "simulated")
        assert not (Path(tmp) / "new").exists()
        # a destination that cannot be read stops the run before any rename
        blocked = Path(tmp) / "blocked"
        generate(blocked)                                                 # the current reference, then one more change
        (blocked / n27).unlink()
        (blocked / n27).mkdir()
        before = state(blocked)
        write_reference(900)
        _refused(lambda: generate(blocked), OSError)
        assert state(blocked) == before and (blocked / n27).is_dir()
        # the undo fails for F13: named, and F13 is the only file changed
        write_reference(500)
        exc = _refused(lambda: with_locked(out, lambda: generate(out), fail_restore_of=n13), MF.FinalWriteIncomplete,
                       f"writing {n14} into {out} failed (PermissionError", f"{n13}: left with its new bytes")
        assert len(exc.left) == 1 and isinstance(exc.__cause__, PermissionError)
        now = state(out)
        assert sorted(now) == sorted(frozen) and now[n14] == frozen[n14] and now[n27] == frozen[n27]
        assert now[n13] != frozen[n13] and md5_of(out / n13) == next(
            r["md5"] for r in generate(Path(tmp) / "check") if r["file"] == n13)   # the new bytes, whole


def test_macro_fixtures_final_write_fsyncs_each_file_before_its_rename():
    """Review of PR #107, F2: `MF._commit` and `MF._atomic_write` renamed their temporary files with neither flush nor
    fsync, while the docstring promised whole files after a power loss. Now every temporary file is fsynced before it
    is renamed over its destination (watched by wrapping os.fsync and os.replace and matching files by inode); a
    failing file fsync fails the run and is undone like any other error. On POSIX each destination directory is then
    fsynced, best effort: a directory fsync that fails does not fail the run; on Windows (os.name 'nt') no directory
    is opened. What a power loss can still leave is stated in `MF._commit` and is not demonstrated here."""
    import os
    import stat
    events: list = []
    real_fsync, real_replace, real_open, real_name = os.fsync, os.replace, os.open, os.name

    def key(st):
        return st.st_dev, st.st_ino

    def fsync(fd):
        st = os.fstat(fd)
        events.append(("fsync", key(st), stat.S_ISDIR(st.st_mode)))
        return real_fsync(fd)

    def replace(src, dst, *args, **kwargs):
        events.append(("replace", key(os.stat(src)), Path(dst).name))
        return real_replace(src, dst, *args, **kwargs)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "new" / "out"
        os.fsync, os.replace = fsync, replace
        try:
            MF._commit([(out / "a.csv", b"a\n"), (out / "b.csv", b"b\n"), (out / "MANIFEST.csv", b"m\n")])
            MF._atomic_write(out / "c.csv", b"c\n")
        finally:
            os.fsync, os.replace = real_fsync, real_replace
        assert {p.name: p.read_bytes() for p in out.iterdir()} == {"a.csv": b"a\n", "b.csv": b"b\n",
                                                                   "MANIFEST.csv": b"m\n", "c.csv": b"c\n"}
        renames = [(i, k, name) for i, (kind, k, name) in enumerate(events) if kind == "replace"]
        assert [name for *_i, name in renames] == ["a.csv", "b.csv", "MANIFEST.csv", "c.csv"]
        for i, k, name in renames:
            assert ("fsync", k, False) in events[:i], f"{name}: renamed before its bytes were fsynced"
        if os.name != "nt":                                 # the directory after the final write's last rename
            assert ("fsync", key(os.stat(out)), True) in events[renames[2][0] + 1:renames[3][0]], events
        # a failing file fsync fails the run before any rename; a failing directory fsync does not fail it

        def failing(kind):
            def fn(fd):
                if stat.S_ISDIR(os.fstat(fd).st_mode) == (kind == "directory"):
                    raise OSError(5, f"simulated: the {kind} cannot be synced")
                return real_fsync(fd)
            return fn
        before = {p.name: p.read_bytes() for p in out.iterdir()}
        for kind in ("file", "directory"):
            os.fsync = failing(kind)
            try:
                if kind == "file":
                    _refused(lambda: MF._commit([(out / "a.csv", b"a2\n"), (out / "d.csv", b"d\n")]), OSError,
                             "simulated: the file cannot be synced")
                else:
                    MF._commit([(out / "a.csv", b"a3\n")])
            finally:
                os.fsync = real_fsync
            if kind == "file":
                assert {p.name: p.read_bytes() for p in out.iterdir()} == before
        assert (out / "a.csv").read_bytes() == b"a3\n"
        # Windows: no directory is opened for an fsync
        opened: list = []
        os.open = lambda *args, **kwargs: opened.append(args) or real_open(*args, **kwargs)
        os.name = "nt"
        try:
            MF._fsync_dir(out)
        finally:
            os.open, os.name = real_open, real_name
        assert opened == []


def test_macro_fixtures_final_write_refuses_a_destination_named_twice():
    """Review of PR #107, F5: `MF._commit` kept its temporary files in a table keyed by destination, so two items with
    one destination lost the first temporary file from the table: the first rename put the second item's bytes in
    place, the second rename ended in a KeyError, and the undo left the lost `.tmp` file and the directory behind
    (FinalWriteIncomplete). Now a destination named twice (also spelled another way, `sub/../a.csv`) is refused with
    a ValueError naming it before anything is written: no directory is made, an existing file keeps its bytes, and no
    temporary file is left."""
    with tempfile.TemporaryDirectory() as tmp:
        fresh, kept = Path(tmp) / "fresh", Path(tmp) / "kept"
        kept.mkdir()
        (kept / "a.csv").write_bytes(b"earlier\n")
        for folder in (fresh, kept):
            a = folder / "a.csv"
            for again in (a, folder / "sub" / ".." / "a.csv"):
                _refused(lambda: MF._commit([(a, b"one\n"), (folder / "b.csv", b"two\n"), (again, b"three\n")]),
                         ValueError, f"the final write names {a} more than once", "nothing is written")
        assert not fresh.exists() and [p.name for p in kept.iterdir()] == ["a.csv"]
        assert (kept / "a.csv").read_bytes() == b"earlier\n"


def test_macro_fixtures_final_write_removes_every_directory_it_made():
    """Review of PR #107, F6: `MF._commit` created the destination directories before its guarded block, so when a
    later one could not be created (no permission, a file holding the name) the error left the directories already
    created for the earlier destinations behind. Now each directory is created inside the guarded block and recorded
    as soon as it exists: with the second destination's directory refused (simulated by patching Path.mkdir), the
    error reaching the caller is that PermissionError and every directory the run created is removed, the existing
    ones kept. A file standing where a directory would go is refused the same way."""
    real = Path.mkdir
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "kept").mkdir()
        first, second = root / "new1" / "deep", root / "kept" / "new2" / "deeper"

        def mkdir(self, *args, **kwargs):
            if self == second:
                raise PermissionError(13, "simulated: the directory cannot be created", str(self))
            return real(self, *args, **kwargs)
        Path.mkdir = mkdir
        try:
            _refused(lambda: MF._commit([(first / "a.csv", b"a\n"), (second / "b.csv", b"b\n")]), PermissionError,
                     "simulated: the directory cannot be created")
        finally:
            Path.mkdir = real
        assert [p.name for p in root.iterdir()] == ["kept"] and list((root / "kept").iterdir()) == []
        (root / "blocker").write_bytes(b"a file\n")
        _refused(lambda: MF._commit([(first / "a.csv", b"a\n"), (root / "blocker" / "c.csv", b"c\n")]), OSError)
        assert sorted(p.name for p in root.iterdir()) == ["blocker", "kept"]
        assert (root / "blocker").read_bytes() == b"a file\n"


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
