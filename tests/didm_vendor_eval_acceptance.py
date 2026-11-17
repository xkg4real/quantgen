"""DS-1: the vendor evaluation keeps the owner's Excel values and agrees with them.

Network-free. The Excel values are the copy inside tools/didm/check_vendor_eval.py.
"""
from __future__ import annotations

import unittest

from tools.didm import check_vendor_eval as cve

EXCEL_SNIPPET = (
    "기준 | 세부 | 공통 | 차이 |  | 뉴스 기사 수집\n"
    "Ravenpack | 감성 | x | y | RAVENPACK 등 | " + " | ".join(cve.EXCEL_RAVENPACK) + " | \n"
    " | 관련성 |  | y | 대안책 | " + " | ".join(cve.EXCEL_ALTERNATIVES) + " | \n"
)


class VendorEvalDocument(unittest.TestCase):
    def setUp(self):
        self.doc = cve.DEFAULT_DOC.read_text(encoding="utf-8")

    def test_document_passes(self):
        self.assertEqual(cve.check(self.doc, EXCEL_SNIPPET), [])

    def test_matrix_shape(self):
        rows = cve.parse_matrix(self.doc)
        self.assertEqual([r["col"] for r in rows], cve.COLUMNS)
        self.assertTrue(all(len(r["cells"]) == 9 for r in rows))

    def test_legal_disclaimer_present(self):
        self.assertIn("법률 자문이 아닙니다", self.doc)

    def test_no_key_values(self):
        # Key names only; no '=' assignment after a key name.
        for name in ("FRED_API_KEY", "ALPHAVANTAGE_API_KEY", "TIINGO_API_KEY",
                     "CRYPTOPANIC_API_KEY", "TRADINGECONOMICS_API_KEY"):
            self.assertIn(name, self.doc)
            self.assertNotIn(name + "=", self.doc)


class CheckerRejects(unittest.TestCase):
    def setUp(self):
        self.doc = cve.DEFAULT_DOC.read_text(encoding="utf-8")

    def _row_line(self, col):
        matrix = self.doc.split(cve.BEGIN, 1)[1].split(cve.END, 1)[0]
        for line in matrix.splitlines():
            if line.startswith(f"| {col} |"):
                return line
        raise AssertionError(col)

    def test_changed_excel_value(self):
        line = self._row_line("N")
        bad = line.replace("| O | X |", "| O | O |", 1)
        self.assertTrue(any("changed" in p for p in cve.check(self.doc.replace(line, bad))))

    def test_contradiction_with_excel_x(self):
        line = self._row_line("P")
        bad = line.replace("X·P4", "O·P4", 1)
        self.assertTrue(any("Excel X" in p for p in cve.check(self.doc.replace(line, bad))))

    def test_question_without_handling(self):
        line = self._row_line("O")
        cells = line.split("|")
        cells[-2] = " — "
        self.assertTrue(any("without handling" in p
                            for p in cve.check(self.doc.replace(line, "|".join(cells)))))

    def test_cell_without_source(self):
        line = self._row_line("L")
        bad = line.replace("O·L4", "O", 1)
        self.assertTrue(any("bad cell" in p for p in cve.check(self.doc.replace(line, bad))))

    def test_excel_copy_mismatch(self):
        alt = list(cve.EXCEL_ALTERNATIVES)
        alt[0] = "X"
        snippet = EXCEL_SNIPPET.replace(" | ".join(cve.EXCEL_ALTERNATIVES), " | ".join(alt))
        self.assertTrue(cve.check(self.doc, snippet))


if __name__ == "__main__":
    unittest.main()
