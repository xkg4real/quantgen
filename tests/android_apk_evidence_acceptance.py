"""Acceptance checks for evidence produced by the manual Android build."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch


SCRIPT = Path(__file__).resolve().parents[1] / "tools/packaging/android_apk_evidence.py"
CERT_SHA256 = "a2" * 32


class AndroidApkEvidenceAcceptance(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        # Resolved: on macOS the temporary folder sits below /var -> /private/var (OSPAY-7 test case below).
        root = Path(temporary.name).resolve()
        self.root = root
        self.apks = root / "apk"
        self.apks.mkdir()
        self.tools = root / "build-tools"
        self.tools.mkdir()
        self.signer = self.tools / ("apksigner.bat" if os.name == "nt" else "apksigner")
        self.signer.touch()
        self.signer.chmod(0o700)
        self.output = root / "evidence.json"

    def invoke(self, runner, *extra_args):
        argv = [str(SCRIPT), "--apk-dir", str(self.apks), "--build-tools", str(self.tools),
                "--output", str(self.output), *map(str, extra_args)]
        self.stderr = io.StringIO()
        with patch.object(sys, "argv", argv), patch.object(subprocess, "run", runner), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(self.stderr):
            try:
                runpy.run_path(str(SCRIPT), run_name="__main__")
            except SystemExit as exit_status:
                return exit_status.code or 0
        return 0

    def receipt(self):
        return json.loads(self.output.read_text(encoding="utf-8"))

    def signed(self, command, **kwargs):
        return subprocess.CompletedProcess(command, 0, f"Signer #1 certificate SHA-256 digest: {CERT_SHA256}\n", "")

    def symlink_or_skip(self, link, target, directory=False):
        try:
            os.symlink(target, link, target_is_directory=directory)
        except (OSError, NotImplementedError):
            self.skipTest("symbolic links are not available here")

    def test_empty_output_directory_fails_without_verifier(self):
        runner = Mock()
        self.assertNotEqual(self.invoke(runner), 0)
        runner.assert_not_called()
        self.assertNotEqual(json.loads(self.output.read_text(encoding="utf-8"))["status"], "PASS")

    def test_each_apk_has_its_own_digest_size_and_verified_certificate(self):
        packages = {"app-arm64-v8a-release.apk": b"fixture 1",
                    "app-x86_64-release.apk": b"second fixture"}
        fingerprints = {name: hashlib.sha256(name.encode()).hexdigest() for name in packages}
        checked = []
        for name, payload in packages.items():
            (self.apks / name).write_bytes(payload)

        def verify(command, **kwargs):
            self.assertFalse(kwargs.get("shell", False))
            self.assertEqual(kwargs["env"]["JAVA_HOME"], "synthetic-jdk")
            self.assertEqual(kwargs["env"]["PATH"], "synthetic-path")
            self.assertNotIn("SYNTHETIC_UNRELATED", kwargs["env"])
            self.assertEqual(Path(command[0]), self.signer)
            self.assertEqual(command[1:-1], ["verify", "--verbose", "--print-certs"])
            name = Path(command[-1]).name
            checked.append(name)
            stdout = (f"Signer #1 certificate DN: CN=PRIVATE_TEST_MARKER\n"
                      f"Signer #1 certificate SHA-256 digest: {fingerprints[name]}\n")
            return subprocess.CompletedProcess(command, 0, stdout, "")

        environment = {"JAVA_HOME": "synthetic-jdk", "PATH": "synthetic-path",
                       "SYNTHETIC_UNRELATED": "PRIVATE_TEST_MARKER"}
        with patch.dict(os.environ, environment):
            self.assertEqual(self.invoke(verify), 0)
        self.assertCountEqual(checked, packages)
        raw = self.output.read_text(encoding="utf-8")
        self.assertNotIn("PRIVATE_TEST_MARKER", raw)
        result = json.loads(raw)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["build_mode"], "NOT_OBSERVED")
        self.assertEqual(result["device_validation"], "NOT_PERFORMED")
        self.assertEqual(result["dependencies"]["status"], "NOT_OBSERVED")
        self.assertCountEqual([item["file"] for item in result["artifacts"]], packages)
        for item in result["artifacts"]:
            name = item["file"]
            self.assertEqual(item["bytes"], len(packages[name]))
            self.assertEqual(item["sha256"], hashlib.sha256(packages[name]).hexdigest())
            self.assertEqual(item["signature"]["status"], "VERIFIED")
            self.assertEqual(item["signature"]["certificate_sha256"], [fingerprints[name]])
            self.assertEqual(item["signature"]["expected_key_identity"], "NOT_VERIFIED")

    def test_one_rejected_apk_fails_the_batch_and_all_are_checked(self):
        (self.apks / "a.apk").write_bytes(b"unsigned fixture")
        (self.apks / "b.apk").write_bytes(b"second fixture")
        checked = []

        def verify(command, **kwargs):
            name = Path(command[-1]).name
            checked.append(name)
            code = 1 if name == "a.apk" else 0
            return subprocess.CompletedProcess(
                command, code, f"Signer #1 certificate SHA-256 digest: {CERT_SHA256}\n",
                "PRIVATE_TEST_MARKER")

        self.assertNotEqual(self.invoke(verify), 0)
        self.assertCountEqual(checked, ["a.apk", "b.apk"])
        raw = self.output.read_text(encoding="utf-8")
        self.assertNotIn("PRIVATE_TEST_MARKER", raw)
        result = json.loads(raw)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual({item["file"]: item["signature"]["status"] for item in result["artifacts"]},
                         {"a.apk": "VERIFICATION_FAILED", "b.apk": "VERIFIED"})

    def test_other_sha256_lines_cannot_substitute_for_signer_certificate(self):
        (self.apks / "app.apk").write_bytes(b"no signer digest fixture")
        output = f"Signer #1 public key SHA-256 digest: {CERT_SHA256}\n"
        runner = Mock(return_value=subprocess.CompletedProcess([], 0, output, ""))
        self.assertNotEqual(self.invoke(runner), 0)
        runner.assert_called_once()
        self.assertNotEqual(json.loads(self.output.read_text(encoding="utf-8"))["status"], "PASS")

    def distribution(self, directory, name, version):
        info = directory / f"{name}-{version}.dist-info"
        info.mkdir(parents=True)
        (info / "METADATA").write_text(
            f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n"
            f"Description: {'x' * 8193}\n", encoding="utf-8")

    def test_six_packages_are_read_per_android_abi_folder(self):
        # OSPAY-4: serious_python installs into build/site-packages/<abi>/ (arm64-v8a, armeabi-v7a, x86_64).
        (self.apks / "app.apk").write_bytes(b"synthetic")
        version_by_name = {"flet": "1.2.1", "PyYAML": "5.1", "Babel": "2.3",
                           "requests": "2.4", "numpy": "1.5", "pandas": "2.6"}
        target = self.apks.parent / "build/site-packages"
        for abi in ("arm64-v8a", "armeabi-v7a", "x86_64"):
            for name, version in version_by_name.items():
                self.distribution(target / abi, name, version)
            self.distribution(target / abi, "PrivateMarker", "10.0")
        self.distribution(target / "not-an-abi", "numpy", "9.0.9")
        self.assertEqual(self.invoke(self.signed, "--target-site-packages", target), 0)
        raw = self.output.read_text(encoding="utf-8")
        dependencies = json.loads(raw)["dependencies"]
        expected = {name.lower(): [version] for name, version in version_by_name.items()}
        self.assertEqual(dependencies["status"], "OBSERVED_METADATA")
        self.assertEqual(dependencies["abi"], ["arm64-v8a", "armeabi-v7a", "x86_64"])
        self.assertEqual(dependencies["nested_layout"], "INSPECTED_ABI_FOLDERS")
        self.assertEqual(dependencies["packages"], expected)
        self.assertEqual(dependencies["abi_packages"], {abi: expected for abi in ("arm64-v8a", "armeabi-v7a", "x86_64")})
        self.assertEqual((dependencies["conflicting_versions"], dependencies["abi_disagreements"]), ([], []))
        self.assertEqual(dependencies["complete_target_resolution"], "NOT_ESTABLISHED")
        self.assertNotIn("privatemarker", raw.lower())
        self.assertNotIn("9.0.9", raw)

    def test_abis_with_different_versions_are_flagged(self):
        (self.apks / "app.apk").write_bytes(b"synthetic")
        target = self.apks.parent / "build/site-packages"
        self.distribution(target / "arm64-v8a", "numpy", "2.3.5")
        self.distribution(target / "x86_64", "numpy", "2.3.4")
        self.distribution(target / "x86_64", "pandas", "2.2.0")
        self.assertEqual(self.invoke(self.signed, "--target-site-packages", target), 0)
        dependencies = self.receipt()["dependencies"]
        self.assertEqual(dependencies["status"], "CONFLICTING_METADATA")
        self.assertEqual(dependencies["abi_disagreements"], ["numpy"])   # pandas only in one ABI: not a disagreement
        self.assertEqual(dependencies["conflicting_versions"], [])
        self.assertEqual(dependencies["packages"]["numpy"], ["2.3.4", "2.3.5"])

    def test_direct_entries_still_count_and_no_abi_folder_is_reported(self):
        (self.apks / "app.apk").write_bytes(b"synthetic")
        target = self.apks.parent / "build/site-packages"
        self.distribution(target, "numpy", "1.5")
        self.assertEqual(self.invoke(self.signed, "--target-site-packages", target), 0)
        dependencies = self.receipt()["dependencies"]
        self.assertEqual((dependencies["status"], dependencies["abi"], dependencies["nested_layout"]),
                         ("PARTIAL_METADATA", "NOT_OBSERVED", "NO_ABI_FOLDERS"))
        self.assertEqual(dependencies["packages"]["numpy"], ["1.5"])

    def test_conflicting_direct_versions_are_separate_from_apk_status(self):
        (self.apks / "app.apk").write_bytes(b"fixture")
        target = self.apks.parent / "build/site-packages"
        for version in ("2.0", "2.1"):
            info = target / f"numpy-{version}.dist-info"
            info.mkdir(parents=True)
            (info / "METADATA").write_text(f"Name: numpy\nVersion: {version}\n", encoding="utf-8")
        signer_output = f"Signer #1 certificate SHA-256 digest: {CERT_SHA256}\n"
        runner = Mock(return_value=subprocess.CompletedProcess([], 0, signer_output, ""))
        self.assertEqual(self.invoke(runner, "--target-site-packages", target), 0)
        result = json.loads(self.output.read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["status_scope"], "APK_ARTIFACT_CHECKS_ONLY")
        self.assertEqual(result["artifacts"][0]["signature"]["status"], "VERIFIED")
        self.assertEqual(result["dependencies"]["status"], "CONFLICTING_METADATA")
        self.assertEqual(result["dependencies"]["conflicting_versions"], ["numpy"])
        self.assertEqual(result["dependencies"]["packages"]["numpy"], ["2.0", "2.1"])

    def test_parent_path_component_is_rejected_before_signer(self):
        (self.apks / "app.apk").write_bytes(b"fixture")
        self.apks = self.apks / ".." / "apk"
        runner = Mock()
        self.assertEqual(self.invoke(runner), 1)
        runner.assert_not_called()
        result = json.loads(self.output.read_text(encoding="utf-8"))
        self.assertEqual(result["error"], "parent_traversal_path")
        self.assertEqual(result["artifacts"], [])

    def test_existing_receipt_is_not_replaced_or_reported_as_new_success(self):
        (self.apks / "app.apk").write_bytes(b"new fixture")
        previous = b'{"status":"PASS","run":"older"}\n'
        self.output.write_bytes(previous)
        runner = Mock()
        self.assertEqual(self.invoke(runner), 2)
        runner.assert_not_called()
        self.assertEqual(self.output.read_bytes(), previous)

    # -- OSPAY-6: fail-closed and path-safety branches ---------------------------------------------------------
    def assert_failed(self, code, *, exit_code=1, where="artifact"):
        self.assertEqual(self.invoke_result, exit_code)
        result = self.receipt()
        self.assertEqual(result["status"], "FAIL")
        if where == "artifact":
            item = result["artifacts"][0]
            got = item.get("error") or item.get("signature", {}).get("error")
            self.assertEqual(got, code)
        else:
            self.assertEqual(result["error"], code)
        self.assertIn(code, self.stderr.getvalue())        # OSPAY-3: the reason reaches the CI log

    def test_signer_timeout_is_not_verified(self):
        (self.apks / "app.apk").write_bytes(b"fixture")
        def runner(command, **kwargs):
            raise subprocess.TimeoutExpired(command, 30)
        self.invoke_result = self.invoke(runner)
        self.assert_failed("signature_tool_timeout")
        self.assertEqual(self.receipt()["artifacts"][0]["signature"]["status"], "NOT_VERIFIED")

    def test_signer_that_cannot_run_is_not_verified(self):
        (self.apks / "app.apk").write_bytes(b"fixture")
        def runner(command, **kwargs):
            raise OSError("exec format error")
        self.invoke_result = self.invoke(runner)
        self.assert_failed("signature_tool_unavailable")
        self.assertEqual(self.receipt()["artifacts"][0]["signature"]["status"], "NOT_VERIFIED")

    def test_malformed_signer_digest_line_is_not_verified(self):
        (self.apks / "app.apk").write_bytes(b"fixture")
        # A valid first signer must not hide a second signer line the parser cannot read.
        out = f"Signer #1 certificate SHA-256 digest: {CERT_SHA256}\nSigner #2 certificate SHA-256 digest: zz\n"
        self.invoke_result = self.invoke(Mock(return_value=subprocess.CompletedProcess([], 0, out, "")))
        self.assert_failed("signer_digest_not_observed")

    def test_missing_signer_fails_before_any_verification(self):
        (self.apks / "app.apk").write_bytes(b"fixture")
        self.signer.unlink()
        runner = Mock()
        self.invoke_result = self.invoke(runner)
        runner.assert_not_called()
        self.assert_failed("signature_tool_missing", where="report")

    def test_empty_apk_fails_before_signer(self):
        (self.apks / "app.apk").write_bytes(b"")
        runner = Mock()
        self.invoke_result = self.invoke(runner)
        runner.assert_not_called()
        self.assert_failed("empty_apk")

    def test_directory_named_apk_fails(self):
        (self.apks / "app.apk").mkdir()
        runner = Mock()
        self.invoke_result = self.invoke(runner)
        runner.assert_not_called()
        self.assert_failed("not_regular_apk")

    def test_apk_changed_during_inspection_fails(self):
        apk = self.apks / "app.apk"
        apk.write_bytes(b"original fixture")
        def runner(command, **kwargs):
            apk.write_bytes(b"replaced while the signer ran")
            return self.signed(command)
        self.invoke_result = self.invoke(runner)
        self.assert_failed("apk_changed_during_inspection")

    def test_symlinked_apk_is_refused(self):
        real = self.root / "elsewhere.apk"
        real.write_bytes(b"fixture outside the folder")
        self.symlink_or_skip(self.apks / "app.apk", real)
        runner = Mock()
        self.invoke_result = self.invoke(runner)
        runner.assert_not_called()
        self.assert_failed("symlink_path")

    def test_protected_name_in_a_path_is_refused(self):
        protected = self.root / ".nextgen" / "apk"
        protected.mkdir(parents=True)
        (protected / "app.apk").write_bytes(b"fixture")
        self.apks = protected
        runner = Mock()
        self.invoke_result = self.invoke(runner)
        runner.assert_not_called()
        self.assert_failed("protected_path", where="report")

    def test_root_below_a_symlinked_folder_is_allowed(self):
        # OSPAY-7: macOS keeps temporary folders below /var -> /private/var.
        (self.root / "private").mkdir()
        self.symlink_or_skip(self.root / "var", self.root / "private", directory=True)
        for name in ("apk", "build-tools"):
            (self.root / "private" / name).mkdir()
        (self.root / "private" / "apk" / "app.apk").write_bytes(b"fixture")
        signer = self.root / "private" / "build-tools" / self.signer.name
        signer.touch()
        self.apks, self.tools = self.root / "var" / "apk", self.root / "var" / "build-tools"
        self.output = self.root / "var" / "evidence.json"
        self.assertEqual(self.invoke(self.signed), 0)
        self.assertEqual(self.receipt()["status"], "PASS")

    def test_receipt_schema_and_scope_are_fixed(self):
        (self.apks / "app.apk").write_bytes(b"fixture")
        self.assertEqual(self.invoke(self.signed), 0)
        result = self.receipt()
        self.assertEqual(result["schema"], "quantgen.android-apk-evidence.v1")
        self.assertEqual(result["status_scope"], "APK_ARTIFACT_CHECKS_ONLY")
        self.assertEqual(self.stderr.getvalue(), "")

    def test_cache_folder_in_a_path_is_refused(self):
        cached = self.root / "docs" / "asset_expansion" / "cache" / "apk"
        cached.mkdir(parents=True)
        (cached / "app.apk").write_bytes(b"fixture")
        self.apks = cached
        runner = Mock()
        self.invoke_result = self.invoke(runner)
        runner.assert_not_called()
        self.assert_failed("protected_path", where="report")

    def tool(self):
        spec = importlib.util.spec_from_file_location("apk_evidence_under_test", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_receipt_appearing_while_writing_is_not_replaced(self):
        # Another writer creates the receipt after the first check: the exclusive link refuses, nothing is replaced.
        module = self.tool()
        real_mkstemp = tempfile.mkstemp
        def racing_mkstemp(*args, **kwargs):
            result = real_mkstemp(*args, **kwargs)
            self.output.write_bytes(b"other writer")
            return result
        with patch.object(module.tempfile, "mkstemp", racing_mkstemp), \
                self.assertRaisesRegex(module.EvidenceError, "output_exists"):
            module._write_new_report(str(self.output), {"status": "PASS"})
        self.assertEqual(self.output.read_bytes(), b"other writer")
        self.assertEqual([p.name for p in self.root.iterdir() if p.name.startswith(".android-apk-evidence-")], [])

    def dependency_error(self, target):
        (self.apks / "app.apk").write_bytes(b"synthetic")
        self.assertEqual(self.invoke(self.signed, "--target-site-packages", target), 0)
        dependencies = self.receipt()["dependencies"]
        self.assertEqual(dependencies["status"], "ERROR")
        return dependencies["error"]

    def metadata(self, folder, text):
        folder.mkdir(parents=True)
        (folder / "METADATA").write_text(text, encoding="utf-8")

    def test_site_packages_outside_a_flet_build_is_refused(self):
        other = self.root / "elsewhere" / "site-packages"
        other.mkdir(parents=True)
        self.assertEqual(self.dependency_error(other), "not_flet_target_site_packages")

    def test_oversized_metadata_header_is_refused(self):
        target = self.root / "build" / "site-packages"
        self.metadata(target / "arm64-v8a" / "numpy-1.0.dist-info", "X-Long: " + "y" * 9000 + "\nName: numpy\nVersion: 1.0\n")
        self.assertEqual(self.dependency_error(target), "metadata_header_too_large")

    def test_duplicate_name_header_is_refused(self):
        target = self.root / "build" / "site-packages"
        self.metadata(target / "arm64-v8a" / "numpy-1.0.dist-info", "Name: numpy\nName: pandas\nVersion: 1.0\n")
        self.assertEqual(self.dependency_error(target), "duplicate_metadata_header")

    def test_version_that_is_not_a_version_is_refused(self):
        target = self.root / "build" / "site-packages"
        self.metadata(target / "arm64-v8a" / "numpy-1.0.dist-info", "Name: numpy\nVersion: ../../etc\n")
        self.assertEqual(self.dependency_error(target), "invalid_package_metadata")

    def test_metadata_naming_another_package_is_refused(self):
        target = self.root / "build" / "site-packages"
        self.metadata(target / "arm64-v8a" / "numpy-1.0.dist-info", "Name: pandas\nVersion: 1.0\n")
        self.assertEqual(self.dependency_error(target), "package_metadata_name_mismatch")


if __name__ == "__main__":
    unittest.main()
