"""DS-9: filing -> event type hints. Synthetic rows only (fake filer ids). Offline."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

from core.didm.ingest import event_rules as er
from core.didm.llm.schema import EventType as E

DOC = Path(__file__).resolve().parents[1] / "docs" / "didm" / "EVENT_RULES_V0.md"


def block(name: str) -> str:
    text = DOC.read_text(encoding="utf-8")
    m = re.search(rf"<!-- {name}:start -->(.*?)<!-- {name}:end -->", text, re.S)
    assert m, name
    return m.group(1)


def table(name: str) -> dict:
    return {m.group(1): m.group(2) for m in re.finditer(r"^\| `([^`]+)` \| ([a-z_]+) \|", block(name), re.M)}


class DocumentMatchesCode(unittest.TestCase):
    def test_edgar_table(self):
        self.assertEqual(table("edgar-items"), {k: v.value for k, v in er.EDGAR_ITEMS.items()})
        self.assertEqual(re.findall(r"`([^`]+)`", block("edgar-none")), list(er.EDGAR_NONE_ITEMS))
        self.assertFalse(set(er.EDGAR_NONE_ITEMS) & set(er.EDGAR_ITEMS))

    def test_opendart_table(self):
        self.assertEqual(table("opendart-names"), {k: v.value for k, v in er.OPENDART_NAMES.items()})
        self.assertEqual(re.findall(r"`([^`]+)`", block("opendart-amend")), list(er.OPENDART_AMENDMENT))

    def test_only_known_types(self):
        for t in list(er.EDGAR_ITEMS.values()) + list(er.OPENDART_NAMES.values()):
            self.assertIn(t, er.PRIORITY)
        self.assertNotIn(E.NONE, er.PRIORITY)


class Edgar(unittest.TestCase):
    def test_single_and_multiple_items(self):
        self.assertEqual(er.edgar_hint("8-K", "2.02,9.01").types, (E.EARNINGS,))
        h = er.edgar_hint("8-K", "5.02,2.02,9.01")
        self.assertEqual((h.types, h.primary, h.matched), ((E.EARNINGS, E.MANAGEMENT), E.EARNINGS, ("5.02", "2.02")))
        self.assertEqual(er.edgar_hint("8-K", "2.02,4.02").types, (E.EARNINGS,))        # no repeats

    def test_none_items(self):
        for items in ("7.01", "8.01,9.01", "1.01", "", "5.07"):
            with self.subTest(items=items):
                self.assertEqual(er.edgar_hint("8-K", items).types, (E.NONE,))
        self.assertEqual(er.edgar_hint("8-K", "7.01,5.02").types, (E.MANAGEMENT,))    # none never beside a type

    def test_amendment_and_other_forms(self):
        h = er.edgar_hint("8-K/A", "2.02")
        self.assertEqual((h.types, h.amendment), ((E.EARNINGS,), True))
        self.assertFalse(er.edgar_hint("8-K", "2.02").amendment)
        self.assertEqual(er.edgar_hint("10-Q", "").types, (E.NONE,))

    def test_bad_items_refused(self):
        for items in ("2.2", "Item 2.02", "2.02;5.02"):
            with self.subTest(items=items), self.assertRaises(er.EventRuleError):
                er.edgar_hint("8-K", items)


class OpenDart(unittest.TestCase):
    def test_names(self):
        self.assertEqual(er.opendart_hint("연결재무제표기준영업(잠정)실적(공정공시)").types, (E.EARNINGS,))
        self.assertEqual(er.opendart_hint("영업잠정실적(공정공시)").types, (E.EARNINGS,))
        self.assertEqual(er.opendart_hint("주요사항보고서(회사합병결정)").types, (E.MERGERS_ACQUISITIONS,))
        self.assertEqual(er.opendart_hint("대표이사 변경").types, (E.MANAGEMENT,))      # spaces ignored
        self.assertEqual(er.opendart_hint("단일판매ㆍ공급계약체결").types, (E.SUPPLY_CHAIN,))
        self.assertEqual(er.opendart_hint("주식분할결정").types, (E.NONE,))
        self.assertEqual(er.opendart_hint("임원ㆍ주요주주특정증권등소유상황보고서").types, (E.NONE,))

    def test_multiple_and_amendment(self):
        h = er.opendart_hint("[기재정정]소송등의제기ㆍ신청(합병관련)")
        self.assertEqual((h.types, h.amendment), ((E.MERGERS_ACQUISITIONS, E.REGULATION_LITIGATION), True))
        self.assertFalse(er.opendart_hint("소송등의제기").amendment)


class Rows(unittest.TestCase):
    def test_store_rows(self):
        edgar = {"source_id": "sec-edgar", "payload": {"cik": "999", "form": "8-K", "items": "2.01,9.01"}}
        dart = {"source_id": "opendart", "payload": {"corp_code": "00000001", "report_nm": "회사분할결정"}}
        self.assertEqual(er.hint_for_row(edgar).primary, E.MERGERS_ACQUISITIONS)
        self.assertEqual(er.hint_for_row(dart).primary, E.MERGERS_ACQUISITIONS)
        self.assertIsNone(er.hint_for_row({"source_id": "gdelt-gkg2", "payload": {}}))


if __name__ == "__main__":
    unittest.main()
