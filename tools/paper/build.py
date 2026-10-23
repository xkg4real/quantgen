"""Build a QUANTGEN paper with Tectonic and fail on what a journal would reject (spec 5.3 step 12).

`compile_tex` copies `qgpaper.sty` beside the .tex, runs `tectonic -X compile --keep-logs` against the pinned
bundle, and `parse_log` sorts the .log/.blg into errors (TeX errors, undefined references or citations,
`Missing character`, BibTeX error messages, overfull boxes over 10 pt) and warnings (every other warning,
underfull boxes, small overfull boxes). It records the sha256 of every Korean font file the source names;
`write_build_record` keeps them, with the Tectonic version, the bundle and the sha256 of the .tex and the PDF, in
build.json. Tectonic writes a PDF even for a build this module rejects, so `compile_tex` deletes the old build.json
first: a PDF counts only beside the record of its own successful build (tools.paper.index.release checks the hashes).

    python -m tools.paper.build <paper_dir>     # en/paper_en.tex and ko/paper_ko.tex; exit 1 on any error
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

STY = Path(__file__).resolve().parent / "qgpaper.sty"
TECTONIC_VERSION = "0.17.0"
BUNDLE_URL = "https://relay.fullyjustified.net/default_bundle_v33.tar"
FONT_FILES = {"HANBatang": "C:/Windows/Fonts/HANBatang.ttf", "HANBatangB": "C:/Windows/Fonts/HANBatangB.ttf",
              "malgun": "C:/Windows/Fonts/malgun.ttf", "malgunbd": "C:/Windows/Fonts/malgunbd.ttf"}
OVERFULL_LIMIT_PT = 10.0
LOG_WIDTH = 79                       # TeX's max_print_line: longer log lines are cut at 79 characters
COMPILE_TIMEOUT_S = 600              # a stalled build (for example a network wait) becomes an error, not a hang

_UNDEFINED = re.compile(r"(?:Reference|Citation) `[^']*' on page \S+ undefined"
                        r"|There were undefined (?:references|citations)")
_OVERFULL = re.compile(r"Overfull \\[hv]box \(([\d.]+)pt too (?:wide|high)\)")
_BIBTEX_ERRORS = re.compile(r"\(There (?:was|were) \d+ error messages?\)")
# ponytail: with --only-cached a bundle file absent from the cache looks exactly like an unknown package, so any
# bare missing name counts as a cache miss; the warm-up build (no --only-cached) turns a real typo into an error.
_CACHE_MISS = re.compile(r"File `([^'/#]+)' not found|I couldn't open style file (\S+)"
                         r"|failed to open input file \"([^\"/]+)\"")


class TectonicMissing(Exception):
    """No tectonic binary: not in QUANTGEN_TECTONIC, on PATH or at ~/.local/bin/tectonic.exe."""


class CacheMiss(Exception):
    """--only-cached, and a resource file is not in the local Tectonic cache."""


@dataclass
class BuildResult:
    ok: bool
    pdf: Path | None
    errors: list[str]
    warnings: list[str]
    fonts: dict[str, str]
    log: Path | None


def find_tectonic() -> Path | None:
    for cand in (os.environ.get("QUANTGEN_TECTONIC"), shutil.which("tectonic"),
                 str(Path.home() / ".local" / "bin" / "tectonic.exe")):
        if cand and Path(cand).is_file():
            return Path(cand)
    return None


def tectonic_version(exe: Path) -> str:
    """The version word `tectonic --version` prints ("" if it prints nothing)."""
    words = subprocess.run([str(exe), "--version"], capture_output=True, text=True, timeout=60).stdout.split()
    return words[-1] if words else ""


def _unwrap(text: str) -> list[str]:
    """Rejoin log lines TeX cut at LOG_WIDTH characters."""
    out, buf = [], ""
    for line in text.splitlines():
        buf += line
        if len(line) != LOG_WIDTH:
            out.append(buf)
            buf = ""
    return out + [buf] if buf else out


def parse_log(log_text: str, blg_text: str = "") -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for line in _unwrap(log_text):
        box = _OVERFULL.search(line)
        if line.startswith("!") or _UNDEFINED.search(line) or "Missing character:" in line:
            errors.append(line)
        elif box:
            (errors if float(box.group(1)) > OVERFULL_LIMIT_PT else warnings).append(line)
        elif "Warning:" in line or "Underfull \\" in line:
            warnings.append(line)
    blg = blg_text.splitlines()
    for i, line in enumerate(blg):
        if line.startswith("Warning--"):
            warnings.append(f"BibTeX: {line}")
        elif line.startswith("---") and i:
            errors.append(f"BibTeX: {blg[i - 1]} {line}")
        elif "---" in line or _BIBTEX_ERRORS.search(line):
            errors.append(f"BibTeX: {line}")
    return list(dict.fromkeys(errors)), list(dict.fromkeys(warnings))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def compile_tex(tex: Path, *, only_cached: bool = False) -> BuildResult:
    exe = find_tectonic()
    if exe is None:
        raise TectonicMissing("tectonic not found (QUANTGEN_TECTONIC, PATH, ~/.local/bin/tectonic.exe)")
    tex = Path(tex).resolve()
    if not tex.is_file():
        return BuildResult(ok=False, pdf=None, errors=[f"no such file: {tex}"], warnings=[], fonts={}, log=None)
    shutil.copyfile(STY, tex.parent / STY.name)
    log, blg, pdf = (tex.with_suffix(s) for s in (".log", ".blg", ".pdf"))
    for stale in (log, blg, pdf, tex.parent / "build.json"):
        stale.unlink(missing_ok=True)
    cmd = [str(exe), "-X", "compile", "--keep-logs", "-b", BUNDLE_URL, tex.name]
    if only_cached:
        cmd.insert(3, "--only-cached")
    try:
        proc = subprocess.run(cmd, cwd=tex.parent, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=COMPILE_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return BuildResult(ok=False, pdf=None, errors=[f"tectonic timed out after {COMPILE_TIMEOUT_S} s: {tex.name}"],
                           warnings=[], fonts={}, log=log if log.is_file() else None)
    log_text, blg_text = _read(log), _read(blg)
    if only_cached and (miss := _CACHE_MISS.search(log_text + "\n" + blg_text + "\n" + proc.stderr)):
        raise CacheMiss(next(g for g in miss.groups() if g))
    errors, warnings = parse_log(log_text, blg_text)
    if proc.returncode:
        tail = proc.stderr.strip().splitlines()[-1:] or ["no stderr"]
        errors.append(f"tectonic exited {proc.returncode}: {tail[0]}")
    version = tectonic_version(exe)
    if version != TECTONIC_VERSION:
        warnings.append(f"tectonic {version or '(no version)'} is not the pinned {TECTONIC_VERSION}")
    source, fonts = tex.read_text(encoding="utf-8"), {}
    for name, path in FONT_FILES.items():
        if name in source:
            if Path(path).is_file():
                fonts[name] = _sha256(Path(path))
            else:
                errors.append(f"font file missing: {path}")
    return BuildResult(ok=not errors and pdf.is_file(), pdf=pdf if pdf.is_file() else None, errors=errors,
                       warnings=warnings, fonts=fonts, log=log if log.is_file() else None)


def write_build_record(tex: Path, result: BuildResult) -> Path:
    """<tex dir>/build.json for a successful build: Tectonic version, bundle, font files, .tex and PDF sha256."""
    exe = find_tectonic()
    record = {"tex": Path(tex).name, "tectonic": tectonic_version(exe) if exe else "", "bundle_url": BUNDLE_URL,
              "fonts": {n: {"path": FONT_FILES[n], "sha256": h} for n, h in result.fonts.items()},
              "tex_sha256": _sha256(Path(tex)), "pdf_sha256": _sha256(result.pdf) if result.pdf else None}
    out = Path(tex).parent / "build.json"
    out.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return out


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Build both editions of a QUANTGEN paper with Tectonic.")
    parser.add_argument("paper_dir", type=Path)
    paper = parser.parse_args(argv).paper_dir
    failed = False
    for tex in (paper / "en" / "paper_en.tex", paper / "ko" / "paper_ko.tex"):
        result = compile_tex(tex)
        for line in result.errors:
            print(f"ERROR {tex.name}: {line}")
        for line in result.warnings:
            print(f"warning {tex.name}: {line}")
        print(f"{'OK' if result.ok else 'FAIL'} {tex} -> {result.pdf}; fonts {result.fonts}")
        if result.ok:
            print(f"record {write_build_record(tex, result)}")
        failed |= not result.ok
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
