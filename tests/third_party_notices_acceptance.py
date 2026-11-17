"""tools/packaging/third_party_notices.py and packaging/selfcheck.py helpers (OS-P0-b/3). Offline."""
import hashlib
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "packaging"))

from tools.packaging import third_party_notices as notices  # noqa: E402
import selfcheck  # noqa: E402


class NoticesTests(unittest.TestCase):
    def test_lists_the_distribution_of_a_collected_module_with_its_licence(self):
        text, names = notices.notices_text(["yaml"])
        self.assertIn("pyyaml", names)
        self.assertRegex(text, r"- PyYAML [0-9.]+: MIT")

    def test_no_qt_section_without_qt_for_python(self):
        text, _ = notices.notices_text(["yaml"])
        self.assertNotIn("GNU LESSER GENERAL PUBLIC LICENSE", text)

    def test_unknown_and_own_modules_are_skipped(self):
        _, names = notices.notices_text(["no_such_module_qg", "core", "quantgen_desktop"])
        self.assertEqual(names, [])

    def test_bundled_licence_texts_are_the_fsf_versions(self):
        for name, first in (("LGPL-3.0.txt", "GNU LESSER GENERAL PUBLIC LICENSE"),
                            ("GPL-3.0.txt", "GNU GENERAL PUBLIC LICENSE")):
            text = (ROOT / "packaging" / "licenses" / name).read_text(encoding="utf-8")
            self.assertEqual(text.strip().splitlines()[0].strip(), first)
            self.assertIn("Version 3, 29 June 2007", text)


class SelfcheckHelperTests(unittest.TestCase):
    def test_expected_hash_matches_provenance_in_a_checkout(self):
        from core.research.provenance import code_evidence
        self.assertEqual(selfcheck.expected_calculation_sha256(ROOT / "core" / "quant"),
                         code_evidence()["calculation_sha256"])

    def test_binding_names_survive_the_port_tool(self):
        from tools.qt_port.pyqt6_to_pyside6 import rewrite
        source = (ROOT / "packaging" / "selfcheck.py").read_text(encoding="utf-8")
        text, changes = rewrite(source)
        self.assertEqual((text, changes), (source, []))


if __name__ == "__main__":
    unittest.main()
