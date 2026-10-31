"""Verify a generated download folder or a native GitHub artifact ZIP, offline.

Uses only the standard library and never extracts an archive or executes source.
The embedded manifest records integrity, not legal/publication approval.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import xml.etree.ElementTree as ET
import zipfile


ARCHIVE = "QUANTGEN_Compliance_20_Documents.zip"
SCOPE = "review drafts and reusable forms; not publication/legal approval"
MAX_FILE_BYTES = 32 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024
PRIVATE_PARTS = frozenset((".git", ".aws", ".codex", ".agents", ".claude", "secrets", "credentials", "tokens", "user_data", "userdata", "paper_live", "grokteam", "_backup"))
WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
POLICY_HEADINGS = ("적용 범위와 현재 상태", "정책 또는 구현 기준", "양식", "검증과 변경 시 재검토", "근거")


class VerificationError(ValueError):
    pass


def _safe_name(name: str) -> str:
    path = PurePosixPath(name)
    if (not name or path.is_absolute() or name != path.as_posix()
            or any(part in (".", "..") for part in path.parts)
            or "\\" in name or ":" in name or any(ord(c) < 32 for c in name)
            or any(part.lower() in PRIVATE_PARTS or part.lower().startswith(".env") for part in path.parts)):
        raise VerificationError("unsafe or private package path")
    return name


def _json(raw: bytes) -> dict:
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise VerificationError("duplicate JSON key in package")
            value[key] = item
        return value
    try:
        value = json.loads(raw, object_pairs_hook=unique)
    except (ValueError, UnicodeError) as exc:
        raise VerificationError("invalid package JSON") from exc
    if not isinstance(value, dict):
        raise VerificationError("package JSON must be an object")
    return value


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _zip_files(source) -> dict[str, bytes]:
    try:
        with zipfile.ZipFile(source) as archive:
            infos = archive.infolist()
            files, seen, total = {}, set(), 0
            for info in infos:
                name = _safe_name(info.filename.removesuffix("/") if info.is_dir() else info.filename)
                if name in seen or stat.S_ISLNK(info.external_attr >> 16):
                    raise VerificationError("duplicate or symlink archive entry")
                seen.add(name)
                if info.flag_bits & 1:
                    raise VerificationError("encrypted package entries are not supported")
                total += info.file_size
                if info.file_size > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES:
                    raise VerificationError("package exceeds verification size limit")
            if archive.testzip() is not None:
                raise VerificationError("archive CRC verification failed")
            for info in infos:
                if not info.is_dir():
                    files[info.filename] = archive.read(info)
            return files
    except (zipfile.BadZipFile, RuntimeError, OSError) as exc:
        raise VerificationError("archive is corrupt or unreadable") from exc


def _word(raw: bytes) -> list[str]:
    files = _zip_files(io.BytesIO(raw))
    if "word/document.xml" not in files or "[Content_Types].xml" not in files:
        raise VerificationError("Word document is missing required OpenXML parts")
    try:
        document = ET.fromstring(files["word/document.xml"])
    except ET.ParseError as exc:
        raise VerificationError("Word document XML is invalid") from exc
    if document.tag != f"{{{WORD_NS}}}document" or not any(
            (node.text or "").strip() for node in document.iter(f"{{{WORD_NS}}}t")):
        raise VerificationError("Word document has no text content")
    # Join runs within paragraphs, not across paragraph/cell boundaries. This
    # accepts font/run/layout changes while keeping the source text observable.
    return ["".join(node.text or "" for node in paragraph.iter(f"{{{WORD_NS}}}t"))
            for paragraph in document.iter(f"{{{WORD_NS}}}p")]


def _semantic_tokens(markdown: str) -> list[str]:
    """Read literal words in Markdown order, independent of display layout.

    Formatting delimiters and list numbering are not source prose. Link labels
    and their destination words remain included; no renderer is called here.
    """
    lines, fenced = [], False
    for line in markdown.splitlines():
        if line.startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            line = re.sub(r"^\s*(?:#{1,6}\s+|>\s*|[-*]\s+|\d+\.\s+)", "", line)
            line = line.replace("**", "").replace("`", "")
        lines.append(line)
    return re.findall(r"\w+", "\n".join(lines), re.UNICODE)


def _form_source(source: str) -> str:
    sections = list(re.finditer(r"^##[ \t]+([^\r\n]+?)[ \t]*$", source, re.M))
    found = [i for i, section in enumerate(sections) if section.group(1) == "양식"]
    if len(found) != 1:
        raise VerificationError("policy source must contain one form section")
    index = found[0]
    end = sections[index + 1].start() if index + 1 < len(sections) else len(source)
    return source[sections[index].end():end].strip()


def _correspondence(row: dict, source_raw: bytes, policy_raw: bytes, form_raw: bytes, form_md_raw: bytes) -> None:
    try:
        source = source_raw.decode("utf-8").replace("\r\n", "\n")
        form_markdown = form_md_raw.decode("utf-8").replace("\r\n", "\n")
    except UnicodeError as exc:
        raise VerificationError("policy/form source is not UTF-8") from exc
    title = source.splitlines()[0]
    if not title.startswith("# ") or not isinstance(row.get("title"), str) or not row["title"].strip():
        raise VerificationError("policy/form title is missing")
    policy = _word(policy_raw)
    text = "\n".join(policy)
    if (not policy or re.findall(r"\w+", policy[0]) != re.findall(r"\w+", title)
            or f"QG-C{row['id']:02d}" not in text or any(heading not in text for heading in POLICY_HEADINGS)):
        raise VerificationError("Word policy identity or required sections do not match its source")
    for field in re.findall(r"\{\{[^{}]+\}\}", source):
        if re.sub(r"\s+", "", field) not in re.sub(r"\s+", "", text):
            raise VerificationError("Word policy lost a source template field")
    if _semantic_tokens(source) != re.findall(r"\w+", text, re.UNICODE):
        raise VerificationError("Word policy text does not correspond to its source")

    form_source = _form_source(source)
    preamble = form_markdown.split("\n\n", 2)
    expected_title = row["title"] + " 양식"
    if (len(preamble) != 3 or preamble[0] != "# " + expected_title or not preamble[1].strip()
            or preamble[2].strip() != form_source):
        raise VerificationError("Markdown form body does not match the source form section")
    form = _word(form_raw)
    expected_tokens = _semantic_tokens(form_source)
    form_tokens = re.findall(r"\w+", "\n".join(form), re.UNICODE)
    if (not form or _semantic_tokens(form[0]) != _semantic_tokens(expected_title)
            or not expected_tokens or form_tokens[-len(expected_tokens):] != expected_tokens):
        raise VerificationError("Word form identity or fields do not correspond to its source form")
    for field in re.findall(r"\{\{[^{}]+\}\}", form_source):
        if re.sub(r"\s+", "", field) not in re.sub(r"\s+", "", "\n".join(form)):
            raise VerificationError("Word form lost a source template field")


def _payload(files: dict[str, bytes]) -> dict:
    if "MANIFEST.json" not in files:
        raise VerificationError("package manifest is missing")
    manifest = _json(files["MANIFEST.json"])
    if (manifest.get("schema_version") != 1 or manifest.get("scope") != SCOPE
            or any(type(manifest.get(key)) is not int or manifest[key] != 20
                   for key in ("document_count", "word_document_count", "separate_form_count"))):
        raise VerificationError("manifest scope or document counts are invalid")
    hashes = manifest.get("files")
    if not isinstance(hashes, dict) or set(files) != set(hashes) | {"MANIFEST.json"}:
        raise VerificationError("package files differ from the manifest")
    for name, expected in hashes.items():
        _safe_name(name)
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected) or _sha(files[name]) != expected:
            raise VerificationError("package file hash mismatch")
    required = {"source/docs/compliance/registry.json", "QUANTGEN_20_DOCUMENTS.html", "FIELD_INDEX.csv", "verification/report.json", "verification/report.md"}
    if not required.issubset(files):
        raise VerificationError("download package is missing required supporting files")
    registry = _json(files["source/docs/compliance/registry.json"])
    rows = registry.get("documents")
    if (registry.get("schema_version") != 1 or not isinstance(rows, list) or len(rows) != 20
            or any(not isinstance(row, dict) or type(row.get("id")) is not int for row in rows)
            or sorted(row["id"] for row in rows) != list(range(1, 21))):
        raise VerificationError("embedded registry must cover document IDs 1..20")
    expected_words, expected_forms, source_paths = set(), set(), set()
    for row in rows:
        name = row.get("path")
        if not isinstance(name, str) or not re.fullmatch(rf"docs/compliance/{row['id']:02d}-[a-z0-9-]+\.md", name):
            raise VerificationError("embedded registry has an invalid policy path")
        stem = PurePosixPath(name).stem
        expected_words.update((f"documents/{stem}.docx", f"forms/{stem}-form.docx"))
        expected_forms.add(f"forms/{stem}-form.md")
        source_paths.add(name)
    actual_words = {name for name in files if name.endswith(".docx")}
    actual_forms = {name for name in files if name.startswith("forms/") and name.endswith(".md")}
    if actual_words != expected_words or actual_forms != expected_forms:
        raise VerificationError("package must contain exactly 20 Word policies and 20 corresponding Word/Markdown forms")
    sources = manifest.get("source_sha256")
    if not isinstance(sources, dict) or set(sources) != source_paths:
        raise VerificationError("source policy digest inventory is invalid")
    for name, expected in sources.items():
        content = files.get("source/" + name)
        if (not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected)
                or content is None or _sha(content.replace(b"\r\n", b"\n")) != expected):
            raise VerificationError("embedded policy source hash mismatch")
    for row in rows:
        stem = PurePosixPath(row["path"]).stem
        _correspondence(row, files["source/" + row["path"]], files[f"documents/{stem}.docx"],
                        files[f"forms/{stem}-form.docx"], files[f"forms/{stem}-form.md"])
    report = _json(files["verification/report.json"])
    if report.get("consistency_status") != "PASS" or report.get("publication_status") not in ("BLOCKED", "REVIEW_RECORDED"):
        raise VerificationError("package has no successful source/document consistency report")
    return {"verification_status": "PASS", "documents": 20, "separate_forms": 20,
            "word_files": 40, "files": len(files), "publication_status": report["publication_status"],
            "scope": "download integrity only; not publication/legal approval"}


def verify_archive(path: Path) -> dict:
    if path.is_symlink():
        raise VerificationError("archive symlinks are not accepted")
    return _payload(_zip_files(path))


def verify_directory(path: Path) -> dict:
    path = path.absolute()
    if any(parent.is_symlink() for parent in (path, *path.parents)) or not path.is_dir():
        raise VerificationError("download directory must be a real directory without symlink parents")
    files, total = {}, 0
    for here, dirs, names in os.walk(path, followlinks=False):
        for directory in dirs:
            if (Path(here) / directory).is_symlink():
                raise VerificationError("download directory contains a symlink")
        for name in names:
            file = Path(here) / name
            relative = _safe_name(file.relative_to(path).as_posix())
            if file.is_symlink() or not file.is_file():
                raise VerificationError("download package contains a nonregular file")
            if relative == ARCHIVE:
                continue
            total += file.stat().st_size
            if file.stat().st_size > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES:
                raise VerificationError("package exceeds verification size limit")
            files[relative] = file.read_bytes()
    result = _payload(files)
    archived = _zip_files(path / ARCHIVE)
    if set(archived) != set(files) or any(_sha(archived[name]) != _sha(data) for name, data in files.items()):
        raise VerificationError("download ZIP bytes differ from the generated folder")
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--directory", type=Path)
    source.add_argument("--archive", type=Path)
    args = parser.parse_args(argv)
    try:
        result = verify_directory(args.directory) if args.directory else verify_archive(args.archive)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (VerificationError, OSError, ValueError) as exc:
        print("Download verification failed: " + str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
