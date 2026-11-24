"""Inspect already built Android artifacts without running their application code.

This records APK bytes and SDK signature verification, not phone startup,
Flutter build mode, a release/debug key identity, or Android wheel compatibility.
Optional dependency observations are limited to six distribution metadata headers
in Flet's build/site-packages directory: entries directly in it and in its Android
ABI folders (arm64-v8a, armeabi-v7a, x86_64, x86). The per-ABI layout is taken from
reading serious_python's packaging source; no real Flet build has confirmed it yet.
They are not a lock file or proof of complete target dependency resolution. No key
store is read.

Paths: each path given on the command line (--apk-dir, --build-tools,
--target-site-packages, and the folder of --output) is a root. A root must not itself
be a symbolic link, but its ancestors may be (macOS keeps temporary folders under
/var -> /private/var); the root is resolved once and must not contain a protected name
as written or once resolved. Entries found inside a root (APKs, apksigner, ABI
folders, dist-info folders, METADATA) and the output file itself must not be symbolic
links. A non-PASS result prints its fixed error codes on stderr, each APK named only
with the characters A-Z a-z 0-9 . _ - (others become _).

Receipt schema quantgen.android-apk-evidence.v2 (2026-11-24): v1 had dependencies with
'abi' and 'nested_layout' always NOT_OBSERVED / NOT_INSPECTED and only direct entries.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile


PACKAGES = ("flet", "pyyaml", "babel", "requests", "numpy", "pandas")
_DIGEST = re.compile(r"Signer #([1-9][0-9]*) certificate SHA-256 digest: ([0-9a-fA-F]{64})", re.ASCII)
_VERSION = re.compile(r"[0-9][A-Za-z0-9.!+_-]{0,127}", re.ASCII)
_PROTECTED = {".aws", ".codex", ".agents", ".nextgen", "paper_live", "grokteam", "_backup", "holdout", "frozen"}
ABIS = ("arm64-v8a", "armeabi-v7a", "x86_64", "x86")


class EvidenceError(Exception):
    """A fixed public error code, never external tool output or private input."""


def _check_names(p: Path) -> None:
    parts = tuple(x.lower() for x in p.parts)
    if any(x.startswith(".env") or x in _PROTECTED for x in parts):
        raise EvidenceError("protected_path")
    if any(parts[i:i + 3] == ("docs", "asset_expansion", "cache") for i in range(len(parts))):
        raise EvidenceError("protected_path")


def _root(value: str | Path) -> Path:
    """A path given on the command line: no '..', no protected name as written or once resolved."""
    raw = Path(value)
    if ".." in raw.parts:
        raise EvidenceError("parent_traversal_path")
    _check_names(raw.absolute())
    if raw.absolute().is_symlink():
        raise EvidenceError("symlink_path")
    try:
        resolved = raw.absolute().resolve()
    except (RuntimeError, OSError):
        # Python 3.11/3.12 raise RuntimeError on a symlink loop; never let a path reach stderr in a traceback.
        raise EvidenceError("symlink_path") from None
    _check_names(resolved)
    return resolved


def _child(parent: Path, name: str) -> Path:
    """An entry inside a resolved root: never a symbolic link, never a protected name."""
    if name in ("", ".", "..") or "/" in name or "\\" in name:
        raise EvidenceError("parent_traversal_path")
    entry = parent / name
    _check_names(entry)
    # Do not follow an alias out of the inspected folder into unrelated user storage.
    if entry.is_symlink():
        raise EvidenceError("symlink_path")
    return entry


def _sha256(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    count = 0
    with path.open("rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise EvidenceError("not_regular_file")
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            count += len(chunk)
            digest.update(chunk)
    return count, digest.hexdigest()


def _signature(apk: Path, signer: Path) -> dict:
    result = {"status": "NOT_VERIFIED", "certificate_sha256": [], "expected_key_identity": "NOT_VERIFIED"}
    # Preserve only the runner's Java/tool lookup, never signing credentials.
    environment = {"PATH": os.defpath, "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}
    for name in ("PATH", "JAVA_HOME", "SYSTEMROOT", "WINDIR"):
        if name in os.environ:
            environment[name] = os.environ[name]
    try:
        completed = subprocess.run(
            [str(signer), "verify", "--verbose", "--print-certs", str(apk)],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            encoding="utf-8", errors="replace", timeout=30, check=False,
            env=environment,
        )
    except subprocess.TimeoutExpired:
        return dict(result, error="signature_tool_timeout")
    except OSError:
        return dict(result, error="signature_tool_unavailable")
    if completed.returncode != 0:
        return dict(result, status="VERIFICATION_FAILED", error="signature_verification_failed")
    signers = []
    for line in completed.stdout.splitlines():
        match = _DIGEST.fullmatch(line.strip())
        if match:
            signers.append((int(match[1]), match[2].lower()))
        elif line.strip().startswith("Signer #") and " certificate SHA-256 digest:" in line:
            return dict(result, error="signer_digest_not_observed")
    numbers = [n for n, _ in signers]
    if not numbers or len(numbers) != len(set(numbers)) or sorted(numbers) != list(range(1, len(numbers) + 1)):
        return dict(result, error="signer_digest_not_observed")
    return dict(result, status="VERIFIED", certificate_sha256=[value for _, value in sorted(signers)])


def _artifact(apk: Path, signer: Path) -> dict:
    item = {"file": apk.name, "status": "FAIL"}
    try:
        apk = _child(apk.parent, apk.name)
        if not apk.is_file():
            raise EvidenceError("not_regular_apk")
        size, digest = _sha256(apk)
        item.update(bytes=size, sha256=digest)
        if not size:
            raise EvidenceError("empty_apk")
        item["signature"] = _signature(apk, signer)
        if _sha256(apk) != (size, digest):
            raise EvidenceError("apk_changed_during_inspection")
        if item["signature"]["status"] == "VERIFIED":
            item["status"] = "PASS"
    except EvidenceError as exc:
        item["error"] = str(exc)
    except OSError:
        item["error"] = "apk_read_failed"
    return item


def _distribution_header(metadata: Path) -> tuple[str, str]:
    name = version = None
    consumed = 0
    with metadata.open("r", encoding="utf-8", errors="strict") as stream:
        while True:
            line = stream.readline(8193)
            if not line or line in ("\n", "\r\n"):
                break
            consumed += len(line)
            if len(line) > 8192 or consumed > 65536:
                raise EvidenceError("metadata_header_too_large")
            key, sep, value = line.partition(":")
            if sep and key.lower() in ("name", "version"):
                value = value.strip()
                if key.lower() == "name":
                    if name is not None:
                        raise EvidenceError("duplicate_metadata_header")
                    name = re.sub(r"[-_.]+", "-", value).lower()
                else:
                    if version is not None:
                        raise EvidenceError("duplicate_metadata_header")
                    version = value
            if name is not None and version is not None:
                break
    if name not in PACKAGES or version is None or not _VERSION.fullmatch(version):
        raise EvidenceError("invalid_package_metadata")
    return name, version


def _read_location(directory: Path) -> dict:
    """{package: [versions]} from *.dist-info entries directly in one folder."""
    found = {name: [] for name in PACKAGES}
    for entry in sorted(directory.iterdir()):
        if not entry.name.endswith(".dist-info"):
            continue
        expected = re.sub(r"[-_.]+", "-", entry.name[:-10].split("-", 1)[0]).lower()
        if expected not in PACKAGES:
            continue
        info = _child(directory, entry.name)
        metadata = _child(info, "METADATA") if info.is_dir() else None
        if metadata is None or not metadata.is_file():
            raise EvidenceError("package_metadata_missing")
        name, version = _distribution_header(metadata)
        if name != expected:
            raise EvidenceError("package_metadata_name_mismatch")
        found[name].append(version)
    return {name: sorted(set(versions)) for name, versions in found.items()}


def _dependencies(value: str | None) -> dict:
    result = {
        "status": "NOT_OBSERVED",
        "scope": "build/site-packages distribution metadata only: direct entries and Android ABI folders",
        "abi": "NOT_OBSERVED", "complete_target_resolution": "NOT_ESTABLISHED",
        "nested_layout": "NOT_OBSERVED", "conflicting_versions": [], "abi_disagreements": [],
        "abi_missing": {}, "direct_abi_disagreements": [],
        "packages": {name: [] for name in PACKAGES}, "abi_packages": {},
    }
    if value is None:
        return result
    try:
        root = _root(value)
        if root.name != "site-packages" or root.parent.name != "build":
            raise EvidenceError("not_flet_target_site_packages")
        if not root.exists():
            return result
        if not root.is_dir():
            raise EvidenceError("not_target_metadata_directory")
        locations = {"": _read_location(root)}
        for abi in ABIS:
            folder = root / abi
            if folder.is_symlink():
                raise EvidenceError("symlink_path")
            if folder.is_dir():
                locations[abi] = _read_location(_child(root, abi))
        abis = [abi for abi in ABIS if abi in locations]
        result["abi"] = abis or "NOT_OBSERVED"
        result["nested_layout"] = "INSPECTED_ABI_FOLDERS" if abis else "NO_ABI_FOLDERS"
        result["abi_packages"] = {abi: locations[abi] for abi in abis}
        # Within one location two versions of a package conflict; across ABIs a different version disagrees.
        result["conflicting_versions"] = sorted({name for found in locations.values()
                                                 for name, versions in found.items() if len(versions) > 1})
        result["abi_disagreements"] = sorted(
            name for name in PACKAGES
            if len({tuple(locations[abi][name]) for abi in abis if locations[abi][name]}) > 1)
        # A package seen in some ABI folders but not in others, and a direct entry whose version differs from the
        # version in the ABI folders, are reported too: both are missing or conflicting evidence.
        seen_in_abi = {name for abi in abis for name in PACKAGES if locations[abi][name]}
        result["abi_missing"] = {abi: [name for name in PACKAGES if name in seen_in_abi and not locations[abi][name]]
                                 for abi in abis}
        result["abi_missing"] = {abi: names for abi, names in result["abi_missing"].items() if names}
        result["direct_abi_disagreements"] = sorted(
            name for name in PACKAGES
            if locations[""][name] and any(locations[abi][name] and locations[abi][name] != locations[""][name]
                                           for abi in abis))
        result["packages"] = {name: sorted({v for found in locations.values() for v in found[name]})
                              for name in PACKAGES}
        observed = sum(bool(versions) for versions in result["packages"].values())
        result["status"] = "OBSERVED_METADATA" if observed == len(PACKAGES) else ("PARTIAL_METADATA" if observed else "NOT_OBSERVED")
        if result["status"] == "OBSERVED_METADATA" and result["abi_missing"]:
            result["status"] = "PARTIAL_METADATA"
        if result["conflicting_versions"] or result["abi_disagreements"] or result["direct_abi_disagreements"]:
            result["status"] = "CONFLICTING_METADATA"
    except EvidenceError as exc:
        result.update(status="ERROR", error=str(exc))
    except (OSError, UnicodeError):
        result.update(status="ERROR", error="metadata_read_failed")
    return result


def inspect(apk_dir: str, build_tools: str, target_site_packages: str | None = None) -> dict:
    report = {
        "schema": "quantgen.android-apk-evidence.v2", "status": "FAIL", "status_scope": "APK_ARTIFACT_CHECKS_ONLY", "artifacts": [],
        "build_mode": "NOT_OBSERVED", "device_validation": "NOT_PERFORMED",
        "dependencies": _dependencies(target_site_packages),
        "limits": "Signature evidence does not establish signer key identity, build mode, target imports or device startup.",
    }
    try:
        directory = _root(apk_dir)
        tools = _root(build_tools)
        if not directory.is_dir():
            raise EvidenceError("apk_directory_missing")
        if not tools.is_dir():
            raise EvidenceError("signature_tool_missing")
        signer = _child(tools, "apksigner.bat" if os.name == "nt" else "apksigner")
        if not signer.is_file():
            raise EvidenceError("signature_tool_missing")
        apks = sorted(p for p in directory.iterdir() if p.suffix.lower() == ".apk")
        if not apks:
            raise EvidenceError("no_apk_observed")
        report["artifacts"] = [_artifact(apk, signer) for apk in apks]
        if all(item["status"] == "PASS" for item in report["artifacts"]):
            report["status"] = "PASS"
    except EvidenceError as exc:
        report["error"] = str(exc)
    except OSError:
        report["error"] = "artifact_directory_read_failed"
    return report


def _output(value: str) -> Path:
    raw = Path(value)
    if ".." in raw.parts:
        raise EvidenceError("parent_traversal_path")
    return _child(_root(raw.absolute().parent), raw.name)


def _write_new_report(output: str, report: dict) -> None:
    target = _output(output)
    if target.exists():
        raise EvidenceError("output_exists")
    if not target.parent.is_dir():
        raise EvidenceError("output_parent_missing")
    temporary = None
    try:
        descriptor, name = tempfile.mkstemp(prefix=".android-apk-evidence-", suffix=".tmp", dir=target.parent)
        temporary = Path(name)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(report, stream, ensure_ascii=True, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        # Exclusive publication: an earlier receipt is never truncated or replaced.
        os.link(temporary, target)
    except FileExistsError:
        raise EvidenceError("output_exists") from None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apk-dir", required=True)
    parser.add_argument("--build-tools", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--target-site-packages")
    options = parser.parse_args(argv)
    try:
        target = _output(options.output)
        if target.exists():
            raise EvidenceError("output_exists")
        if not target.parent.is_dir():
            raise EvidenceError("output_parent_missing")    # before any signer run: no receipt could be written
        report = inspect(options.apk_dir, options.build_tools, options.target_site_packages)
        _write_new_report(options.output, report)
    except EvidenceError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except OSError:
        print("receipt_write_failed", file=sys.stderr)
        return 2
    print(report["status"])
    if report["status"] != "PASS":
        # APK file names (unsafe characters replaced) and fixed codes only, never tool output or paths,
        # so a failed CI run shows why without letting a crafted name write its own log line.
        print(" ".join(error_codes(report)) or "no_error_code", file=sys.stderr)
    return 0 if report["status"] == "PASS" else 1


def _safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", name) or "_"


def error_codes(report: dict) -> list[str]:
    codes = []
    if report.get("error"):
        codes.append(f"report:{report['error']}")
    for item in report.get("artifacts", []):
        if item.get("error"):
            codes.append(f"{_safe_name(item['file'])}:{item['error']}")
        signature = item.get("signature") or {}
        if signature.get("error"):
            codes.append(f"{_safe_name(item['file'])}:signature:{signature['error']}")
    dependencies = report.get("dependencies") or {}
    if dependencies.get("error"):
        codes.append(f"dependencies:{dependencies['error']}")
    return codes


if __name__ == "__main__":
    raise SystemExit(main())
