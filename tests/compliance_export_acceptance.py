"""Synthetic download-integrity tests; no optional GUI or Word dependencies."""
from pathlib import Path
import contextlib
import hashlib
import io
import json
import struct
import tempfile
import unittest
import zipfile
from xml.sax.saxutils import escape

from tools.compliance.verify import ARCHIVE, SCOPE, VerificationError, main, verify_archive, verify_directory


def sha(data):
    return hashlib.sha256(data).hexdigest()


def word(text="Synthetic policy text"):
    paragraphs = [text] if isinstance(text, str) else text
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("word/document.xml", '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>' + ''.join('<w:p><w:r><w:t>' + escape(p) + '</w:t></w:r></w:p>' for p in paragraphs) + '</w:body></w:document>')
    return data.getvalue()


class ExportIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "download"
        self.root.mkdir()
        self.rows, self.sources, self.policy_text, self.form_text = [], {}, {}, {}
        for i in range(1, 21):
            stem = f"{i:02d}-fixture"
            path = f"docs/compliance/{stem}.md"
            title = f"{i:02d} Synthetic policy"
            form_source = f"### Request form {i:02d}\n\n| Field | Value |\n|---|---|\n| Request label {i:02d} | {{{{request_{i:02d}.id}}}} |"
            source = f"# {title}\n\n문서 ID: QG-C{i:02d}\n\n## 적용 범위와 현재 상태\n\nSynthetic scope {i:02d}\n\n## 정책 또는 구현 기준\n\nSynthetic rule {i:02d}\n\n## 양식\n\n{form_source}\n\n## 검증과 변경 시 재검토\n\nSynthetic validation {i:02d}\n\n## 근거\n\nSynthetic evidence {i:02d}\n"
            raw = source.replace("\n", "\r\n").encode()
            self.put("source/" + path, raw)
            self.sources[path] = sha(raw.replace(b"\r\n", b"\n"))
            self.rows.append({"id": i, "path": path, "title": f"Policy {i}"})
            self.policy_text[i] = [title, f"문서 ID: QG-C{i:02d}", "적용 범위와 현재 상태", f"Synthetic scope {i:02d}",
                                   "정책 또는 구현 기준", f"Synthetic rule {i:02d}", "양식", f"Request form {i:02d}",
                                   "Field", "Value", f"Request label {i:02d}", f"{{{{request_{i:02d}.id}}}}",
                                   "검증과 변경 시 재검토", f"Synthetic validation {i:02d}", "근거", f"Synthetic evidence {i:02d}"]
            self.form_text[i] = [f"Policy {i} 양식", "Synthetic safety notice.", f"Request form {i:02d}",
                                 "Field", "Value", f"Request label {i:02d}", f"{{{{request_{i:02d}.id}}}}"]
            self.put(f"documents/{stem}.docx", word(self.policy_text[i]))
            self.put(f"forms/{stem}-form.docx", word(self.form_text[i]))
            self.put(f"forms/{stem}-form.md", (f"# Policy {i} 양식\n\nSynthetic safety notice.\n\n" + form_source + "\n").encode())
        self.put("source/docs/compliance/registry.json", json.dumps({"schema_version": 1, "documents": self.rows}).encode())
        self.put("QUANTGEN_20_DOCUMENTS.html", b"<!doctype html><title>Package</title>")
        self.put("FIELD_INDEX.csv", b"field,value\n")
        self.put("verification/report.md", b"Consistency PASS; publication BLOCKED\n")
        self.put("verification/report.json", b'{"consistency_status":"PASS","publication_status":"BLOCKED"}')
        self.bundle()

    def put(self, name, raw):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    def bundle(self, **overrides):
        hashes = {f.relative_to(self.root).as_posix(): sha(f.read_bytes()) for f in self.root.rglob("*")
                  if f.is_file() and f.name not in (ARCHIVE, "MANIFEST.json")}
        manifest = {"schema_version": 1, "scope": SCOPE, "document_count": 20, "word_document_count": 20,
                    "separate_form_count": 20, "source_sha256": self.sources, "files": hashes, **overrides}
        self.put("MANIFEST.json", json.dumps(manifest).encode())
        with zipfile.ZipFile(self.root / ARCHIVE, "w", zipfile.ZIP_DEFLATED) as z:
            for f in self.root.rglob("*"):
                if f.is_file() and f.name != ARCHIVE:
                    z.write(f, f.relative_to(self.root))

    def test_generated_directory_and_native_artifact_zip_verify_without_live_checkout(self):
        self.assertEqual(verify_directory(self.root)["word_files"], 40)
        native = Path(self.temp.name) / "native-artifact.zip"
        native.write_bytes((self.root / ARCHIVE).read_bytes())
        self.assertEqual(verify_archive(native)["separate_forms"], 20)
        self.assertEqual(verify_archive(native)["publication_status"], "BLOCKED")

    def test_missing_policy_word_is_rejected(self):
        (self.root / "documents/01-fixture.docx").unlink()
        with self.assertRaises(VerificationError):
            verify_directory(self.root)

    def test_source_tampering_fails_even_with_regenerated_file_hashes(self):
        self.put("source/docs/compliance/01-fixture.md", b"Changed source\n")
        self.bundle()
        with self.assertRaisesRegex(VerificationError, "source hash"):
            verify_directory(self.root)

    def test_folder_hash_tampering_is_rejected(self):
        self.put("FIELD_INDEX.csv", b"tampered\n")
        with self.assertRaisesRegex(VerificationError, "hash mismatch"):
            verify_directory(self.root)

    def test_corrupt_archive_and_cli_failure_are_rejected(self):
        self.put(ARCHIVE, b"not an archive")
        with self.assertRaisesRegex(VerificationError, "corrupt"):
            verify_directory(self.root)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--archive", str(self.root / ARCHIVE)]), 1)

    def test_changed_stored_member_is_rejected_by_crc(self):
        payload = self.read_zip()
        with zipfile.ZipFile(self.root / ARCHIVE, "w", zipfile.ZIP_STORED) as z:
            for name, data in payload.items():
                z.writestr(name, data)
        with zipfile.ZipFile(self.root / ARCHIVE) as z:
            offset = z.getinfo("FIELD_INDEX.csv").header_offset
        data = bytearray((self.root / ARCHIVE).read_bytes())
        name_length, extra_length = struct.unpack_from("<HH", data, offset + 26)
        data[offset + 30 + name_length + extra_length] ^= 1
        self.put(ARCHIVE, data)
        with self.assertRaisesRegex(VerificationError, "CRC"):
            verify_archive(self.root / ARCHIVE)

    def test_archive_traversal_private_entry_and_extra_member_are_rejected(self):
        for name in ("../escape.txt", ".env", "extra.txt"):
            self.bundle()
            with zipfile.ZipFile(self.root / ARCHIVE, "a") as z:
                z.writestr(name, b"fixture")
            with self.assertRaises(VerificationError):
                verify_archive(self.root / ARCHIVE)

    def test_symlink_file_is_refused_without_following_target(self):
        target = Path(self.temp.name) / "outside"
        target.write_bytes(b"unrelated")
        file = self.root / "documents/01-fixture.docx"
        file.unlink()
        try:
            file.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable on this test host")
        with self.assertRaisesRegex(VerificationError, "nonregular"):
            verify_directory(self.root)
        self.assertEqual(target.read_bytes(), b"unrelated")

    def test_archive_symlink_entry_is_refused(self):
        payload = self.read_zip()
        with zipfile.ZipFile(self.root / ARCHIVE, "w", zipfile.ZIP_DEFLATED) as z:
            for name, data in payload.items():
                if name == "documents/01-fixture.docx":
                    info = zipfile.ZipInfo(name)
                    info.create_system = 3
                    info.external_attr = 0o120777 << 16
                    z.writestr(info, "../unrelated")
                else:
                    z.writestr(name, data)
        with self.assertRaisesRegex(VerificationError, "symlink"):
            verify_archive(self.root / ARCHIVE)

    def test_wrong_counts_and_duplicate_registry_ids_are_rejected(self):
        self.bundle(document_count=19)
        with self.assertRaisesRegex(VerificationError, "counts"):
            verify_directory(self.root)
        self.bundle(scope="approved for production")
        with self.assertRaisesRegex(VerificationError, "scope"):
            verify_directory(self.root)
        self.rows[-1]["id"] = 1
        self.put("source/docs/compliance/registry.json", json.dumps({"schema_version": 1, "documents": self.rows}).encode())
        self.bundle()
        with self.assertRaisesRegex(VerificationError, "IDs"):
            verify_directory(self.root)

    def test_invalid_word_xml_is_rejected_after_manifest_and_zip_refresh(self):
        self.put("forms/01-fixture-form.docx", word(""))
        self.bundle()
        with self.assertRaisesRegex(VerificationError, "no text"):
            verify_directory(self.root)

    def test_archive_bytes_must_match_folder_even_when_zip_crc_is_valid(self):
        payload = {name: data for name, data in self.read_zip().items()}
        payload["FIELD_INDEX.csv"] = b"other valid CRC payload"
        with zipfile.ZipFile(self.root / ARCHIVE, "w", zipfile.ZIP_DEFLATED) as z:
            for name, data in payload.items():
                z.writestr(name, data)
        with self.assertRaisesRegex(VerificationError, "differ"):
            verify_directory(self.root)

    def test_swapped_policy_words_fail_even_with_refreshed_manifest_and_crc(self):
        first = (self.root / "documents/01-fixture.docx").read_bytes()
        second = (self.root / "documents/02-fixture.docx").read_bytes()
        self.put("documents/01-fixture.docx", second)
        self.put("documents/02-fixture.docx", first)
        self.bundle()
        with self.assertRaisesRegex(VerificationError, "identity"):
            verify_directory(self.root)

    def test_swapped_form_words_fail_even_with_refreshed_manifest_and_crc(self):
        first = (self.root / "forms/01-fixture-form.docx").read_bytes()
        second = (self.root / "forms/02-fixture-form.docx").read_bytes()
        self.put("forms/01-fixture-form.docx", second)
        self.put("forms/02-fixture-form.docx", first)
        self.bundle()
        with self.assertRaisesRegex(VerificationError, "Word form"):
            verify_directory(self.root)

    def test_dropped_policy_and_form_fields_fail_after_manifest_and_crc_refresh(self):
        self.put("documents/01-fixture.docx", word([p for p in self.policy_text[1] if p != "{{request_01.id}}"] ))
        self.bundle()
        with self.assertRaisesRegex(VerificationError, "field"):
            verify_directory(self.root)
        self.put("documents/01-fixture.docx", word(self.policy_text[1]))
        self.put("forms/01-fixture-form.docx", word([p for p in self.form_text[1] if p != "{{request_01.id}}"] ))
        self.bundle()
        with self.assertRaisesRegex(VerificationError, "Word form"):
            verify_directory(self.root)

    def test_changed_form_body_fails_after_manifest_and_crc_refresh(self):
        self.put("forms/01-fixture-form.md", b"# Policy 1 \xec\x96\x91\xec\x8b\x9d\n\nSynthetic notice.\n\nUnrelated nonempty form text.\n")
        self.bundle()
        with self.assertRaisesRegex(VerificationError, "Markdown form"):
            verify_directory(self.root)

    def read_zip(self):
        with zipfile.ZipFile(self.root / ARCHIVE) as z:
            return {name: z.read(name) for name in z.namelist()}


if __name__ == "__main__":
    unittest.main()
