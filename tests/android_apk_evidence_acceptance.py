"""Acceptance checks for evidence produced by the manual Android build."""
import contextlib
import hashlib
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
        root = Path(temporary.name)
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
        with patch.object(sys, "argv", argv), patch.object(subprocess, "run", runner), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            try:
                runpy.run_path(str(SCRIPT), run_name="__main__")
            except SystemExit as exit_status:
                return exit_status.code or 0
        return 0

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

    def test_only_direct_target_metadata_for_six_packages_is_reported(self):
        (self.apks / "app.apk").write_bytes(b"synthetic")
        version_by_name = {"flet": "1.2.1", "PyYAML": "5.1", "Babel": "2.3",
                           "requests": "2.4", "numpy": "1.5", "pandas": "2.6"}
        target = self.apks.parent / "build/site-packages"

        def distribution(directory, name, version):
            info = directory / f"{name}-{version}.dist-info"
            info.mkdir(parents=True)
            (info / "METADATA").write_text(
                f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n"
                f"Description: {'x' * 8193}\n", encoding="utf-8")

        for name, version in version_by_name.items():
            distribution(target, name, version)
        distribution(target, "PrivateMarker", "10.0")
        distribution(target / "arm64-v8a", "numpy", "9.0.1")
        distribution(target / "x86_64", "numpy", "9.0.2")
        signer_output = f"Signer #1 certificate SHA-256 digest: {CERT_SHA256}\n"
        runner = Mock(return_value=subprocess.CompletedProcess([], 0, signer_output, ""))
        self.assertEqual(self.invoke(runner, "--target-site-packages", target), 0)
        raw = self.output.read_text(encoding="utf-8")
        dependencies = json.loads(raw)["dependencies"]
        self.assertEqual(dependencies["status"], "OBSERVED_METADATA")
        self.assertEqual(dependencies["packages"],
                         {name.lower(): [version] for name, version in version_by_name.items()})
        self.assertEqual(dependencies["abi"], "NOT_OBSERVED")
        self.assertEqual(dependencies["nested_layout"], "NOT_INSPECTED")
        self.assertEqual(dependencies["conflicting_versions"], [])
        self.assertEqual(dependencies["complete_target_resolution"], "NOT_ESTABLISHED")
        self.assertNotIn("privatemarker", raw.lower())
        self.assertNotIn("9.0.1", raw)
        self.assertNotIn("9.0.2", raw)

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


if __name__ == "__main__":
    unittest.main()
