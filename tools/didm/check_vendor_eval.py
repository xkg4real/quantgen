"""Check docs/didm/VENDOR_EVAL_2026-11.md against the owner's Excel text copy.

The owner's Excel (``ravenpack_alt.xlsx``) has two O/X/? rows over 19 information
types (columns F..X): "RAVENPACK 등" and "대안책". The evaluation document must
copy both rows unchanged and its per-alternative matrix must agree with them:

* Excel O  -> at least one alternative is O
* Excel X  -> no alternative is O or ?
* Excel ?  -> no alternative is O, at least one is ?

Every per-alternative cell is ``<O|X|?>·<source code>`` and every ``?`` names one
handling method. Network-free; run with no arguments to check only the document,
or with ``--excel <path to OWNER_EXCEL_RAVENPACK_ALTERNATIVES.txt>`` to also
compare against the Excel text copy (kept on the handoff branch, not in main).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

COLUMNS = list("FGHIJKLMNOPQRSTUVWX")
ALTERNATIVES = [
    "CME", "FRED", "Polymarket", "Trad. Econ", "GDELT",
    "Alpha Vantage", "Tiingo", "Cryptopanic", "자체 NLP",
]
METHODS = ("무료 키 1회 호출로 확인", "공급사 문의", "공급사 무응답")
# Excel values as published in OWNER_EXCEL_RAVENPACK_ALTERNATIVES.txt (2026-11-17).
EXCEL_RAVENPACK = "O O O O O O O O O O O X X X X X X ? ?".split()
EXCEL_ALTERNATIVES = "O O O O O O O O X ? X O O O O O O X O".split()
DEFAULT_DOC = Path(__file__).resolve().parents[2] / "docs" / "didm" / "VENDOR_EVAL_2026-11.md"
BEGIN, END = "<!-- matrix:begin -->", "<!-- matrix:end -->"
CELL = re.compile(r"^([OX?])·(\S+)$")


def read_excel_rows(text: str) -> tuple[list[str], list[str]]:
    """Return (RAVENPACK 등, 대안책) values F..X from the Excel text copy."""
    rp = alt = None
    for line in text.splitlines():
        fields = [f.strip() for f in line.split("|")]
        if len(fields) < 24:
            continue
        if fields[4] == "RAVENPACK 등":
            rp = fields[5:24]
        elif fields[4] == "대안책":
            alt = fields[5:24]
    if rp is None or alt is None:
        raise ValueError("Excel text copy: rows 'RAVENPACK 등' and '대안책' not found")
    return rp, alt


def parse_matrix(doc: str) -> list[dict]:
    if BEGIN not in doc or END not in doc:
        raise ValueError("matrix markers not found")
    body = doc.split(BEGIN, 1)[1].split(END, 1)[0]
    rows = []
    for line in body.strip().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cells or cells[0] not in COLUMNS:
            continue
        if len(cells) != 5 + len(ALTERNATIVES):
            raise ValueError(f"column {cells[0]}: {len(cells)} cells")
        rows.append({
            "col": cells[0], "rp": cells[2], "alt": cells[3],
            "cells": dict(zip(ALTERNATIVES, cells[4:13])), "handling": cells[13],
        })
    return rows


def check(doc: str, excel_text: str | None = None) -> list[str]:
    problems: list[str] = []
    rows = parse_matrix(doc)
    if [r["col"] for r in rows] != COLUMNS:
        problems.append("matrix columns are not exactly F..X in order")
        return problems
    rp_ref, alt_ref = EXCEL_RAVENPACK, EXCEL_ALTERNATIVES
    if excel_text is not None:
        rp_x, alt_x = read_excel_rows(excel_text)
        if (rp_x, alt_x) != (rp_ref, alt_ref):
            problems.append("Excel text copy differs from the values this checker was written for")
        rp_ref, alt_ref = rp_x, alt_x
    for row, rp, alt in zip(rows, rp_ref, alt_ref):
        col = row["col"]
        if row["rp"] != rp:
            problems.append(f"{col}: RAVENPACK 등 changed {rp} -> {row['rp']}")
        if row["alt"] != alt:
            problems.append(f"{col}: 대안책 changed {alt} -> {row['alt']}")
        values = []
        for name, cell in row["cells"].items():
            m = CELL.match(cell)
            if not m:
                problems.append(f"{col}/{name}: bad cell {cell!r}")
                continue
            values.append(m.group(1))
            if m.group(1) == "?" and f"{name}: " not in row["handling"]:
                problems.append(f"{col}/{name}: '?' without handling")
        for part in [p.strip() for p in row["handling"].split(";") if p.strip() != "—"]:
            if not any(method in part for method in METHODS):
                problems.append(f"{col}: handling {part!r} names no allowed method")
        if row["rp"] == "?" and "RAVENPACK 등: " not in row["handling"]:
            problems.append(f"{col}: RAVENPACK 등 '?' without handling")
        if alt == "O" and "O" not in values:
            problems.append(f"{col}: Excel O but no alternative is O")
        if alt == "X" and ("O" in values or "?" in values):
            problems.append(f"{col}: Excel X but an alternative is O or ?")
        if alt == "?" and ("O" in values or "?" not in values):
            problems.append(f"{col}: Excel ? needs no O and at least one ?")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    ap.add_argument("--excel", type=Path, help="OWNER_EXCEL_RAVENPACK_ALTERNATIVES.txt")
    args = ap.parse_args(argv)
    excel = args.excel.read_text(encoding="utf-8") if args.excel else None
    problems = check(args.doc.read_text(encoding="utf-8"), excel)
    rows = parse_matrix(args.doc.read_text(encoding="utf-8"))
    cells = sum(len(r["cells"]) for r in rows)
    unknown = sum(1 for r in rows for c in r["cells"].values() if c.startswith("?"))
    print(f"columns {len(rows)}, alternative cells {cells}, '?' cells {unknown}, "
          f"excel compared: {'yes' if excel else 'no (built-in copy)'}")
    print(f"excel cells changed: {sum(1 for p in problems if 'changed' in p)}")
    for p in problems:
        print("PROBLEM", p)
    print("OK" if not problems else f"FAIL ({len(problems)})")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
