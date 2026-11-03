"""Offline document/source consistency and a separate publication-readiness gate.

Python >=3.11; standard library only. Source bytes are hashed, never executed or
copied into reports. Private stores, credentials and research ledgers are excluded.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
import fnmatch
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import tomllib
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
DOC_DIR = "docs/compliance"
REGISTRY = f"{DOC_DIR}/registry.json"
PROFILE = f"{DOC_DIR}/release-profile.json"
BASELINE = f"{DOC_DIR}/source-review.json"
PUBLICATION = f"{DOC_DIR}/publication-review.json"
KST = timezone(timedelta(hours=9))
SUPPLEMENTAL = frozenset(f"{DOC_DIR}/{name}.md" for name in ("README", "FACTS", "SOURCES", "RELEASE_GAPS", "PIPELINE"))
HEADINGS = ("적용 범위와 현재 상태", "정책 또는 구현 기준", "양식", "검증과 변경 시 재검토", "근거")
SOURCE_SUFFIXES = frozenset((".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".scss", ".qss", ".qml", ".vue", ".toml", ".yaml", ".yml", ".ini", ".cfg", ".cmd", ".bat", ".ps1", ".sh", ".lock"))
BINARY_ASSETS = frozenset((".png", ".jpg", ".jpeg", ".ico", ".gif", ".webp", ".ttf", ".otf", ".woff", ".woff2"))
ALWAYS_EXCLUDED = frozenset((".git", ".aws", ".codex", ".agents", ".claude", ".venv", ".venvs", "venv", "__pycache__", ".pytest_cache", ".cache", "node_modules", "build", "dist"))
ROOT_ARCHIVES = frozenset(("paper_live", "grokteam", "_backup", "_legacy", "research_notes", "research", "reports", "scratch", "quantgen_quant_council_2026-10-03", "quantgen_techfund_research_bundle"))
PRIVATE_PARTS = frozenset(("cache", "caches", "logs", "secrets", "credentials", "tokens", "user_data", "userdata", "accounts", "holdout", "frozen"))
SOURCE_ROOTS = frozenset(("core", "data", "ui", "quantgen_desktop", "tools", "tests", "pkg_tools"))
CODE_SUFFIXES = frozenset((".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".scss", ".qss", ".qml", ".vue"))
DEPENDENCY_MANIFESTS = frozenset(("package.json", "package-lock.json", "npm-shrinkwrap.json", "composer.json", "composer.lock", "bower.json", "deno.json", "deno.jsonc", "deno.lock", "bun.lock", "bun.lockb"))
PLACEHOLDER = re.compile(r"\{\{[^{}]+\}\}|\b(?:TODO|TBD|UNKNOWN|UNVERIFIED|PENDING|EXAMPLE|PLACEHOLDER|NOT_CONFIGURED)\b|미정|확인\s*필요|입력\s*필요", re.I)
REQUIREMENTS = ("privacy_review", "retention_schedule", "third_party_contracts", "international_transfer", "cookie_audit", "consent_ui", "data_minimization", "pricing_and_refunds", "business_disclosure", "child_scope", "marketing_email", "deletion", "accessibility", "asset_licenses", "dependency_licenses", "data_licenses", "financial_regulatory_review", "claims_and_testimonials")
OPERATOR_FIELDS = ("legal_name", "representative", "address", "business_registration", "ecommerce_registration", "support_email", "support_phone", "privacy_contact", "refund_contact")
KNOWN_FINDINGS = ("kis-token-plaintext", "flet-upbit-implicit-read", "ai-free-text-transfer", "flet-ai-consent-gap", "deletion-not-implemented", "accessibility-not-validated", "licensing-not-confirmed", "commercial-policy-conflicts")


class CheckError(ValueError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_path(root: Path, relative: str) -> Path:
    """Never follow symlinks or accept absolute/traversing evidence paths."""
    p = PurePosixPath(relative)
    if (not relative or p.is_absolute() or ".." in p.parts or "\\" in relative
            or any(ord(ch) < 32 for ch in relative)):
        raise CheckError("unsafe path in configuration")
    path = root / relative
    if any(parent.is_symlink() for parent in (path, *path.parents) if parent != root.parent):
        raise CheckError(f"symlink is not accepted: {relative}")
    if not path.resolve().is_relative_to(root.resolve()):
        raise CheckError("path escapes repository")
    return path


def normalized_bytes(root: Path, name: str) -> bytes:
    path = safe_path(root, name)
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise CheckError(f"required source/config file missing or unreadable: {name}") from exc
    return data if PurePosixPath(name).suffix.lower() in BINARY_ASSETS else data.replace(b"\r\n", b"\n")


def read_json(root: Path, name: str) -> dict:
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise CheckError(f"duplicate JSON key: {name}")
            value[key] = item
        return value
    try:
        value = json.loads(normalized_bytes(root, name), object_pairs_hook=unique)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise CheckError(f"invalid JSON: {name}") from exc
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise CheckError(f"unsupported schema: {name}")
    return value


def monitored(name: str) -> bool:
    p = PurePosixPath(name)
    parts = tuple(s.lower() for s in p.parts)
    if (not parts or parts[0] in ROOT_ARCHIVES
            or any(part in ALWAYS_EXCLUDED or part.startswith(".env") for part in parts)
            or any(part.startswith(".compliance-report") for part in parts)):
        return False
    if any(part in PRIVATE_PARTS for part in parts):
        # A source package called core/accounts or core/research is still code.
        # Never open account/log/token/cache payloads while inspecting its modules.
        if parts[0] not in SOURCE_ROOTS or p.suffix.lower() not in CODE_SUFFIXES:
            return False
    if parts[0] == "docs":
        # Explicit public distribution evidence, not archived studies or datasets.
        return (name.startswith("docs/product/") and p.suffix == ".md"
                or name == "docs/DESKTOP_MIGRATION_2026-10-30.md" or name in SUPPLEMENTAL)
    if parts[0] == "assets":
        return p.suffix.lower() in BINARY_ASSETS | {".svg", ".txt", ".json"}
    if name in ("README.md", "LICENSE", "LICENSE.txt", "LICENSE.md", "NOTICE", "NOTICE.txt"):
        return True
    if p.name.startswith("requirements") and p.suffix == ".txt":
        return True
    if p.name.lower() in DEPENDENCY_MANIFESTS:
        return True
    if p.suffix.lower() == ".json":
        return ("schemas" in parts or name.startswith("data/calendars/")
                or name == "data/macro/rules_v2.0.0.json")
    return p.suffix.lower() in SOURCE_SUFFIXES


def source_inventory(root: Path) -> dict[str, str]:
    """Use a bounded filesystem walk so newly added source is detected before git add.

    Excluded directories are pruned before traversing. Only eligible public code,
    dependency declarations and shipped assets are opened, never arbitrary data.
    """
    result = {}
    for here, dirs, files in os.walk(root, followlinks=False):
        rel_dir = Path(here).relative_to(root)
        dirs[:] = sorted(d for d in dirs if d.lower() not in ALWAYS_EXCLUDED
                         and not d.lower().startswith(".env")
                         and not d.lower().startswith(".compliance-report"))
        if not rel_dir.parts:
            dirs[:] = [d for d in dirs if d.lower() not in ROOT_ARCHIVES]
        if not rel_dir.parts or rel_dir.parts[0].lower() not in SOURCE_ROOTS:
            dirs[:] = [d for d in dirs if d.lower() not in PRIVATE_PARTS]
        if rel_dir.parts and rel_dir.parts[0] == "docs":
            # Avoid traversing any research-document subtree.
            if rel_dir == Path("docs"):
                dirs[:] = [d for d in dirs if d in ("product", "compliance")]
            elif rel_dir.parts[1] == "compliance":
                dirs[:] = []
            elif rel_dir.parts[1] != "product":
                dirs[:] = []
        if any((Path(here) / d).is_symlink() for d in dirs):
            raise CheckError("source directory symlink requires explicit inspection; not followed")
        for file in sorted(files):
            name = (rel_dir / file).as_posix()
            if monitored(name):
                result[name] = digest(normalized_bytes(root, name))
    return dict(sorted(result.items()))


def registry(root: Path) -> list[dict]:
    value = read_json(root, REGISTRY)
    rows = value.get("documents")
    if not isinstance(rows, list) or len(rows) != 20:
        raise CheckError("registry must contain exactly 20 documents")
    if any(not isinstance(r, dict) for r in rows):
        raise CheckError("invalid document registry entry")
    if sorted(r.get("id", -1) for r in rows) != list(range(1, 21)):
        raise CheckError("document IDs must be unique and cover 1..20")
    paths = set()
    for row in rows:
        name = row.get("path", "")
        if (not isinstance(name, str)
                or not re.fullmatch(rf"docs/compliance/{row['id']:02d}-[a-z0-9-]+\.md", name)
                or name in paths or not isinstance(row.get("title"), str) or not row["title"].strip()):
            raise CheckError("invalid/duplicate document path or title")
        patterns = row.get("source_patterns")
        if not isinstance(patterns, list) or not patterns or any(not isinstance(x, str) or not x or ".." in x or x.startswith("/") for x in patterns):
            raise CheckError("source_patterns must be nonempty safe glob strings")
        safe_path(root, name)
        paths.add(name)
    return sorted(rows, key=lambda r: r["id"])


def documents(root: Path, rows: list[dict]) -> tuple[dict, list[str]]:
    result, errors = {}, []
    expected = {r["path"] for r in rows}
    extras = {p.relative_to(root).as_posix() for p in (root / DOC_DIR).glob("[0-9][0-9]-*.md")} - expected
    if extras:
        errors.append("unexpected numbered documents: " + ", ".join(sorted(extras)))
    for row in rows:
        name = row["path"]
        try:
            raw = normalized_bytes(root, name)
            text = raw.decode("utf-8")
        except (OSError, UnicodeError, CheckError):
            errors.append(f"document missing, unreadable or unsafe: {name}")
            continue
        sections = {}
        if not text.startswith("# "):
            errors.append(f"document title missing: {name}")
        preamble = text.split("\n## ", 1)[0]
        metadata = {}
        for key, pattern in {
            "id": r"문서\s*ID:\s*(QG-C\d{2})",
            "version": r"버전:\s*(\d+\.\d+(?:\.\d+)?)",
            "reviewed_on": r"(?:검토일|기준일):\s*(\d{4}-\d{2}-\d{2})",
            "status": r"상태:\s*([a-z-]+)",
            "approved_by": r"승인자:\s*([^·\r\n]+)",
            "approval_evidence": r"승인\s*근거:\s*([^·\r\n]+)",
            "approval_reason": r"승인\s*사유:\s*([^·\r\n]+)",
        }.items():
            match = re.search(pattern, preamble)
            metadata[key] = match.group(1).strip() if match else None
        if metadata["id"] != f"QG-C{row['id']:02d}" or not metadata["version"]:
            errors.append(f"document ID/version metadata missing or mismatched: {name}")
        if metadata["status"] not in ("review-required", "approved", "not-applicable"):
            errors.append(f"invalid/missing document status metadata: {name}")
        try:
            if date.fromisoformat(metadata["reviewed_on"]) > datetime.now(KST).date():
                raise ValueError("future review")
        except (TypeError, ValueError):
            errors.append(f"valid document review/reference date missing: {name}")
        for heading in HEADINGS:
            marker = f"## {heading}"
            hits = list(re.finditer(rf"^{re.escape(marker)}\s*$", text, re.M))
            if len(hits) != 1:
                errors.append(f"required heading missing/duplicate ({heading}): {name}")
            else:
                sections[heading] = re.split(r"^## ", text[hits[0].end():], maxsplit=1, flags=re.M)[0].strip()
                if len(sections[heading]) < 20:
                    errors.append(f"substantive section missing ({heading}): {name}")
        if "양식" in sections and not any(token in sections["양식"] for token in ("|", "```", "- ", "[ ]")):
            errors.append(f"copyable form missing: {name}")
        result[str(row["id"])] = {"path": name, "sha256": digest(raw),
            "template_fields": sorted(set(re.findall(r"\{\{([^{}]+)\}\}", text))),
            "publication_placeholders": bool(PLACEHOLDER.search(sections.get("정책 또는 구현 기준", ""))),
            "metadata": metadata}
    return result, errors


def local_link_errors(root: Path, names: list[str]) -> list[str]:
    """Check repository-local Markdown destinations, without opening destinations."""
    errors = []
    for name in names:
        if not (root / name).exists():
            continue
        try:
            text = normalized_bytes(root, name).decode("utf-8")
        except (UnicodeError, OSError, CheckError):
            errors.append(f"linked document unreadable: {name}")
            continue
        # Examples in fenced forms are not actual document links.
        text = re.sub(r"```.*?```", "", text, flags=re.S)
        for match in re.finditer(r"!?\[[^\]\n]*\]\((<[^>]+>|[^)\n]+)\)", text):
            raw = match.group(1).strip()
            if raw.startswith("<"):
                raw = raw[1:-1]
            else:
                raw = re.split(r'\s+[\'\"]', raw, maxsplit=1)[0]
            if "{{" in raw or raw.startswith("#"):
                continue
            parts = urlsplit(raw)
            if parts.scheme or parts.netloc:
                continue
            target = unquote(parts.path)
            if not target:
                continue
            local = (root / name).parent / target
            if not local.resolve().is_relative_to(root.resolve()):
                errors.append(f"local document link escapes repository: {name}")
            elif not local.exists():
                # Only the local path is emitted, never source or document payload.
                errors.append(f"broken local link in {name}: {target}")
    return errors


def affected_documents(name: str, rows: list[dict]) -> list[int]:
    found = [r["id"] for r in rows if any(fnmatch.fnmatchcase(name, pattern) for pattern in r["source_patterns"])]
    return found or [r["id"] for r in rows]


def source_digests(sources: dict, rows: list[dict]) -> dict[str, str]:
    # Every source addition/deletion/rename requires classifying the new surface.
    # Content-only changes preserve the more useful targeted path mapping.
    inventory = digest(json.dumps(sorted(sources)).encode())
    per_doc = {str(r["id"]): {"__monitored_path_inventory__": inventory} for r in rows}
    for name, sha in sources.items():
        for doc in affected_documents(name, rows):
            per_doc[str(doc)][name] = sha
    return {key: digest(json.dumps(value, sort_keys=True).encode()) for key, value in per_doc.items()}


def dependencies(root: Path) -> list[str]:
    name = "pyproject.toml"
    if not (root / name).exists():
        raise CheckError("pyproject.toml missing")
    try:
        project = tomllib.loads(normalized_bytes(root, name).decode())["project"]
        declared = project.get("dependencies", [])
        optional = project.get("optional-dependencies", {})
        if (not isinstance(declared, list) or not isinstance(optional, dict)
                or any(not isinstance(x, str) for x in declared)
                or any(not isinstance(v, list) or any(not isinstance(x, str) for x in v) for v in optional.values())):
            raise ValueError("invalid dependency declarations")
        # Never expose userinfo/tokens from a direct-reference dependency URL.
        def safe_declaration(dep):
            match = re.match(r"[A-Za-z0-9][A-Za-z0-9_.-]*(?:\[[A-Za-z0-9_, .-]+\])?", dep)
            name = match.group(0) if match else "[name unavailable]"
            if "@" in dep:
                return name + " @ [direct reference redacted]"
            return dep if re.fullmatch(r"[A-Za-z0-9_.\[\], <>!=~*;()'\"-]+", dep) else name + " [declaration redacted]"
        return sorted([safe_declaration(x) for x in declared]
                      + [f"{safe_declaration(group)}: {safe_declaration(dep)}" for group, deps in optional.items() for dep in deps])
    except (ValueError, KeyError, UnicodeError, TypeError) as exc:
        raise CheckError("invalid static project dependencies") from exc


def meaningful(value) -> bool:
    return isinstance(value, str) and len(value.strip()) >= 2 and not PLACEHOLDER.search(value)


def profile_blockers(root: Path) -> list[str]:
    p = read_json(root, PROFILE)
    if p.get("jurisdiction") != "KR" or not isinstance(p.get("operator"), dict):
        raise CheckError("release profile requires jurisdiction KR and operator object")
    blockers = [f"operator.{key}: operator must supply/verify this field" for key in OPERATOR_FIELDS if not meaningful(p["operator"].get(key))]
    requirements = p.get("requirements")
    findings = p.get("known_findings")
    if not isinstance(requirements, dict) or set(requirements) != set(REQUIREMENTS):
        raise CheckError("release profile requirements missing or unknown")
    if not isinstance(findings, dict) or set(findings) != set(KNOWN_FINDINGS):
        raise CheckError("release profile known findings missing or unknown")
    for key, item in {**requirements, **findings}.items():
        if not isinstance(item, dict) or item.get("status") not in ("unverified", "verified", "not_applicable"):
            raise CheckError(f"invalid review status: {key}")
        if item["status"] == "unverified":
            blockers.append(f"{key}: review/evidence required")
            continue
        if (not meaningful(item.get("evidence")) or not meaningful(item.get("reviewed_by"))
                or not meaningful(item.get("rationale"))):
            blockers.append(f"{key}: evidence, reviewer and reason required")
        try:
            when = date.fromisoformat(item.get("reviewed_on", ""))
            if when > datetime.now(KST).date():
                raise ValueError("future review")
        except (ValueError, TypeError):
            blockers.append(f"{key}: valid completed review date required")
    return blockers


def publication_scope(current: dict) -> str:
    scope = {"sources": current["sources"],
             "documents": {key: doc["sha256"] for key, doc in current["documents"].items()},
             "registry_sha256": current["registry_sha256"], "profile_sha256": current["profile_sha256"]}
    return digest(json.dumps(scope, sort_keys=True).encode())


def document_publication_blockers(root: Path, current: dict) -> list[str]:
    release = profile_blockers(root)
    for key, doc in current["documents"].items():
        meta = doc["metadata"]
        if meta["status"] == "review-required":
            release.append(f"document {key}: review-required draft; publication approval not recorded")
        elif not meaningful(meta["approved_by"]) or not meaningful(meta["approval_evidence"]):
            release.append(f"document {key}: publication status requires approver and evidence in preamble")
        if meta["status"] == "not-applicable" and not meaningful(meta["approval_reason"]):
            release.append(f"document {key}: non-applicability requires a recorded reason in preamble")
        if meta["status"] != "not-applicable" and doc["publication_placeholders"]:
            release.append(f"document {key}: unresolved policy-section template fields or review markers")
    return release


def publication_snapshot_blockers(root: Path, current: dict) -> list[str]:
    if not (root / PUBLICATION).exists():
        return ["publication snapshot absent: a separate publication review has not been recorded"]
    try:
        snapshot = read_json(root, PUBLICATION)
    except (CheckError, OSError):
        return ["publication snapshot invalid or unsafe: separate publication review required"]
    blockers = []
    if snapshot.get("scope_sha256") != publication_scope(current):
        blockers.append("publication snapshot stale: source, document, mapping or operator/evidence profile changed; ordinary baseline refresh cannot re-approve it")
    if (not meaningful(snapshot.get("reviewed_by")) or not meaningful(snapshot.get("review_note"))
            or not meaningful(snapshot.get("review_evidence"))):
        blockers.append("publication snapshot requires a named reviewer, reason and approval evidence")
    try:
        reviewed = datetime.fromisoformat(snapshot.get("reviewed_at", ""))
        if reviewed.tzinfo is None or reviewed > datetime.now(timezone.utc):
            raise ValueError("invalid review time")
    except (ValueError, TypeError):
        blockers.append("publication snapshot requires a valid completed review timestamp")
    return blockers


def record_publication(root: Path, reviewer: str, note: str, evidence: str) -> dict:
    if not meaningful(reviewer) or not meaningful(note) or len(note.strip()) < 12 or not meaningful(evidence):
        raise CheckError("publication review requires a named reviewer, a specific review note and approval evidence")
    report = check(root)
    current = collect(root)
    if report["errors"] or document_publication_blockers(root, current):
        raise CheckError("publication review cannot be recorded while structure/source review, document approvals or operating evidence remain unresolved")
    snapshot = {"schema_version": 1, "scope_sha256": publication_scope(current),
                "reviewed_by": reviewer.strip(), "review_note": note.strip(), "review_evidence": evidence.strip(),
                "reviewed_at": datetime.now(timezone.utc).isoformat(), "source_commit": commit(root),
                "scope": "explicit recorded publication-evidence review for these fingerprints; not independent legal or operational certification"}
    atomic_text(safe_path(root, PUBLICATION), json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n")
    return snapshot


def commit(root: Path) -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True,
                              capture_output=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def collect(root: Path) -> dict:
    rows = registry(root)
    docs, errors = documents(root, rows)
    errors.extend(local_link_errors(root, [r["path"] for r in rows] + sorted(SUPPLEMENTAL)))
    sources = source_inventory(root)
    if not sources:
        errors.append("source inventory is empty")
    return {"schema_version": 1, "sources": sources, "documents": docs,
            "source_digests": source_digests(sources, rows),
            "registry_sha256": digest(normalized_bytes(root, REGISTRY)),
            "profile_sha256": digest(normalized_bytes(root, PROFILE)),
            "dependency_declarations": dependencies(root), "errors": errors}


def refresh(root: Path, reviewer: str, note: str, selected: list[int] | None = None) -> dict:
    if not meaningful(reviewer) or not meaningful(note) or len(note.strip()) < 12:
        raise CheckError("baseline refresh requires a named reviewer and a specific review note (12+ characters)")
    current = collect(root)
    # Validate the profile even for a source-only review; unknown is valid, malformed is not.
    profile_blockers(root)
    if current["errors"]:
        raise CheckError("fix document structure before recording a review: " + "; ".join(current["errors"]))
    if selected is not None and (not selected or any(x not in range(1, 21) for x in selected)):
        raise CheckError("selected document IDs must be 1..20")
    old = read_json(root, BASELINE) if selected is not None and (root / BASELINE).exists() else None
    if selected is not None and old is None:
        raise CheckError("first review must cover all 20 documents")
    if old and (old.get("registry_sha256") != current["registry_sha256"]
                or old.get("profile_sha256") != current["profile_sha256"]):
        raise CheckError("registry/profile changes require reviewing all 20 documents")
    reviews = dict(old.get("reviews", {})) if old else {}
    for key, doc in current["documents"].items():
        if selected is None or int(key) in selected:
            reviews[key] = {"document_sha256": doc["sha256"], "source_digest": current["source_digests"][key],
                            "reviewed_by": reviewer.strip(), "review_note": note.strip(),
                            "reviewed_at": datetime.now(timezone.utc).isoformat(), "source_commit": commit(root)}
    inventory_reviewed = all(r.get("source_digest") == current["source_digests"][key] for key, r in reviews.items())
    result = {"schema_version": 1, "normalization": "UTF-8 text CRLF to LF; binary assets raw bytes",
              "scope": "named source/document consistency review; not legal or operational certification",
              "source_state": "HEAD commit identifier plus observed working-tree fingerprints; not a clean-checkout attestation",
              "registry_sha256": current["registry_sha256"], "profile_sha256": current["profile_sha256"],
              "sources": current["sources"] if inventory_reviewed else old["sources"], "reviews": reviews}
    atomic_text(safe_path(root, BASELINE), json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


def check(root: Path) -> dict:
    current = collect(root)
    baseline = read_json(root, BASELINE)
    errors = current["errors"]
    rows = registry(root)
    if baseline.get("registry_sha256") != current["registry_sha256"]:
        errors.append("registry changed: review mappings and all documents")
    if baseline.get("profile_sha256") != current["profile_sha256"]:
        errors.append("release profile changed: review facts and documents")
    old_sources = baseline.get("sources")
    reviews = baseline.get("reviews")
    if not isinstance(old_sources, dict) or not isinstance(reviews, dict) or set(reviews) != {str(i) for i in range(1, 21)}:
        raise CheckError("review baseline must contain a source inventory and all 20 review records")
    changed = []
    for name in sorted(set(current["sources"]) | set(old_sources)):
        before, after = old_sources.get(name), current["sources"].get(name)
        if before != after:
            change = "added" if before is None else "deleted" if after is None else "modified"
            changed.append({"path": name, "change": change,
                            "documents": list(range(1, 21)) if change in ("added", "deleted") else affected_documents(name, rows)})
    stale = []
    for key, doc in current["documents"].items():
        review = reviews.get(key, {})
        reasons = []
        if not isinstance(review, dict):
            review = {}
        if review.get("document_sha256") != doc["sha256"]:
            reasons.append("document changed since review")
        if review.get("source_digest") != current["source_digests"][key]:
            reasons.append("related source changed since review")
        if not meaningful(review.get("reviewed_by")) or not meaningful(review.get("review_note")):
            reasons.append("review attribution missing")
        if reasons:
            stale.append({"id": int(key), "path": doc["path"], "reasons": reasons})
    # The per-document digests keep selective refresh from hiding unreviewed source
    # changes even though the global inventory advances on every refresh.
    if stale:
        errors.append("documents need review: " + ", ".join(str(x["id"]) for x in stale))
    release = document_publication_blockers(root, current) + publication_snapshot_blockers(root, current)
    return {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_commit": commit(root), "consistency_status": "FAIL" if errors else "PASS",
            "publication_status": "BLOCKED" if release or errors else "REVIEW_RECORDED",
            "scope": "offline source/document consistency and recorded evidence only; not a deployment, legal opinion or complete accessibility/security audit",
            "errors": errors, "changed_sources": changed, "documents_needing_review": stale,
            "publication_blockers": release, "document_count": len(current["documents"]),
            "source_file_count": len(current["sources"]),
            "dependency_declarations": current["dependency_declarations"],
            "template_fields": {key: doc["template_fields"] for key, doc in current["documents"].items()}}


def atomic_text(path: Path, text: str) -> None:
    if path.is_symlink():
        raise CheckError("output file symlink refused")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, prefix=".compliance-write-", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(text)
        # Replacing a race-created symlink replaces the link itself, not its target.
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def write_reports(directory: Path, report: dict) -> None:
    absolute = directory.absolute()
    if any(path.is_symlink() for path in (absolute, *absolute.parents)):
        raise CheckError("report directory symlink refused")
    output = directory.resolve()
    # Reports are separate artifacts; do not overwrite runtime or authored documents.
    protected = ("docs", "tools", "core", "data", "ui", "quantgen_desktop", "assets", ".github", ".aws", ".codex", ".agents")
    if output == ROOT or any(output.is_relative_to(ROOT / item) for item in protected):
        raise CheckError("report directory must be a separate output directory")
    output.mkdir(parents=True, exist_ok=True)
    if any((output / name).is_symlink() for name in ("report.json", "report.md")):
        raise CheckError("report output file symlink refused")
    atomic_text(output / "report.json", json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    atomic_text(output / "report.md", markdown(report))


def markdown(report: dict) -> str:
    def clean(s):
        return str(s).replace("|", "\\|").replace("`", "'").replace("\n", " ").replace("\r", " ")
    lines = ["# QUANTGEN 문서 자체 점검 결과", "", f"- 문서 정합성: **{report['consistency_status']}**",
             f"- 공개 준비 증빙: **{report['publication_status']}**", f"- 점검 시각 UTC: {report['generated_at']}",
             f"- 문서 {report['document_count']}개, 공개 소스·자산 {report['source_file_count']}개", "", report["scope"], "",
             "## 정합성 오류", ""]
    lines += [f"- {clean(x)}" for x in report["errors"]] or ["없음"]
    lines += ["", "## 소스 변경과 재검토 문서", "", "| 경로 | 변경 | 문서 번호 |", "|---|---|---|"]
    lines += [f"| {clean(x['path'])} | {x['change']} | {', '.join(map(str,x['documents']))} |" for x in report["changed_sources"]]
    lines += ["", "## 재검토가 필요한 문서", ""]
    lines += [f"- {x['id']:02d} {clean(x['path'])}: {clean('; '.join(x['reasons']))}" for x in report["documents_needing_review"]] or ["없음"]
    lines += ["", "## 공개 전 확인할 사항", ""]
    lines += [f"- {clean(x)}" for x in report["publication_blockers"]] or ["기록상 미해결 항목 없음. 실사·승인·배포는 별도 절차입니다."]
    lines += ["", "변경 내용을 읽고 해당 문서와 양식을 수정한 뒤 명시적인 검토자·검토 내용을 남겨 기준을 갱신합니다. 기준 갱신은 공개 준비 증빙을 승인하지 않습니다.", ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--refresh-baseline", action="store_true")
    mode.add_argument("--record-publication-review", action="store_true")
    parser.add_argument("--release", action="store_true", help="also fail for unresolved publication evidence")
    parser.add_argument("--reviewed-by")
    parser.add_argument("--review-note")
    parser.add_argument("--review-evidence")
    parser.add_argument("--documents", type=int, nargs="+")
    parser.add_argument("--report-dir", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.refresh_baseline:
            if args.release or args.review_evidence:
                raise CheckError("release checks and publication evidence are separate from a baseline review")
            refresh(ROOT, args.reviewed_by, args.review_note, args.documents)
        elif args.record_publication_review:
            if args.documents or args.release:
                raise CheckError("publication review covers the complete current scope, separate from check mode")
            record_publication(ROOT, args.reviewed_by, args.review_note, args.review_evidence)
        elif args.documents or args.reviewed_by or args.review_note or args.review_evidence:
            raise CheckError("review arguments require an explicit review-recording mode")
        result = check(ROOT)
        if args.report_dir:
            write_reports(args.report_dir, result)
        print(json.dumps({key: result[key] for key in ("consistency_status", "publication_status", "document_count", "source_file_count")}, ensure_ascii=False))
        for item in result["errors"]:
            print(item, file=sys.stderr)
        if args.release:
            for item in result["publication_blockers"]:
                print(item, file=sys.stderr)
        return 1 if result["errors"] or args.release and result["publication_blockers"] else 0
    except (CheckError, OSError, ValueError, TypeError, KeyError) as exc:
        # No exception payloads from source/dependency contents are emitted.
        reason = str(exc) if isinstance(exc, CheckError) else f"{type(exc).__name__}: required files or configuration could not be processed"
        print(f"Compliance check failed: {reason}", file=sys.stderr)
        if args.report_dir:
            failure = {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
                       "source_commit": commit(ROOT), "consistency_status": "FAIL", "publication_status": "BLOCKED",
                       "scope": "incomplete check; no complete source/document or publication verdict",
                       "errors": [reason], "changed_sources": [], "documents_needing_review": [],
                       "publication_blockers": ["Complete the failed configuration/structure check before publication review."],
                       "document_count": 0, "source_file_count": 0, "dependency_declarations": [], "template_fields": {}}
            try:
                write_reports(args.report_dir, failure)
            except (CheckError, OSError):
                print("Failure report destination unavailable or protected.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
