"""refs.yaml: the single source of bibliography truth, its verification records and refs.bib.

Spec 5.2 step 3 and section 7 (reference verification). refs.yaml is a list of entries
{key, type, authors, year, title, venue, volume, pages, doi?, arxiv?, url?, class, verified?}.
`verify_entry` checks one entry against Crossref (DOI) or the arXiv API and returns its
`verified` record {method, url, retrieved_utc, fetched_title, ok}. An entry with neither a DOI
nor an arXiv id is `manual`: an agent opens its url and is the only one who sets `ok` on it, and
re-verification keeps that record. A DOI or arXiv id that cannot be fetched stays ok: false.
The tool rewrites refs.yaml, so that file carries no comments.

CLI (exit 1 while any entry lacks an ok record):
    python -m tools.paper.refs verify <paper_dir>   network; rewrites refs.yaml, writes refs.bib
    python -m tools.paper.refs bib <paper_dir>      offline; writes refs.bib
"""
from __future__ import annotations

import html
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.parse import quote

import yaml

CLASSES = ("published", "working_paper", "book", "local_note")
REQUIRED = ("key", "type", "authors", "year", "title", "class")
KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_:-]*$")
VENUE_FIELD = {"article": "journal", "book": "publisher", "techreport": "institution",
               "inproceedings": "booktitle", "incollection": "booktitle", "phdthesis": "school",
               "misc": "howpublished"}
CROSSREF = "https://api.crossref.org/works/"
ARXIV = "http://export.arxiv.org/api/query?id_list="
_ATOM = "{http://www.w3.org/2005/Atom}"

Fetch = Callable[[str], "dict | None"]


def load_refs(path) -> list[dict]:
    """Entries of refs.yaml; ValueError naming every schema problem."""
    refs = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or []
    if not isinstance(refs, list):
        raise ValueError(f"{path}: refs.yaml must be a list of entries")
    bad, seen = [], set()
    for i, e in enumerate(refs):
        if not isinstance(e, dict):
            bad.append(f"entry {i}: not a mapping")
            continue
        key = e.get("key", f"#{i}")
        missing = [f for f in REQUIRED if not e.get(f)]
        if missing:
            bad.append(f"{key}: missing {missing}")
        if not KEY_RE.match(str(key)):
            bad.append(f"{key}: bad key")
        if key in seen:
            bad.append(f"{key}: duplicate key")
        seen.add(key)
        if e.get("class") not in CLASSES:
            bad.append(f"{key}: class {e.get('class')!r} not in {CLASSES}")
        if not isinstance(e.get("authors"), list):
            bad.append(f"{key}: authors must be a list")
    if bad:
        raise ValueError(f"{path}: " + "; ".join(bad))
    return refs


def _norm(title: str) -> str:
    """Entity-, case-, markup- and punctuation-free form used to compare titles (keeps Hangul)."""
    return re.sub(r"[\W_]+", "", re.sub(r"<[^>]+>", "", html.unescape(title or "")).casefold())


def _tex(text) -> str:
    return re.sub(r"(?<!\\)([&%#_])", r"\\\1", str(text))


def write_bib(refs, out_bib: Path) -> None:
    """refs.bib for natbib/plainnat, in refs.yaml order. Titles are double-braced to keep case."""
    blocks = []
    for e in refs:
        fields = [("author", " and ".join(_tex(a) for a in e["authors"])), ("year", e["year"]),
                  ("title", "{" + _tex(e["title"]) + "}")]
        if e.get("venue"):
            fields.append((VENUE_FIELD.get(e["type"], "note"), _tex(e["venue"])))
        if e.get("volume"):
            fields.append(("volume", e["volume"]))
        if e.get("pages"):
            fields.append(("pages", re.sub(r"\s*-+\s*", "--", str(e["pages"]))))
        if e.get("doi"):
            fields.append(("doi", e["doi"]))
        if e.get("arxiv"):
            fields += [("eprint", e["arxiv"]), ("archivePrefix", "arXiv")]
        if e.get("url"):
            fields.append(("url", e["url"]))
        body = "".join(f"  {k} = {{{v}}},\n" for k, v in fields)
        blocks.append(f"@{e['type']}{{{e['key']},\n{body}}}\n")
    Path(out_bib).write_text("\n".join(blocks), encoding="utf-8", newline="\n")


def parse_arxiv_atom(text: str) -> dict:
    """arXiv API Atom feed -> {"entries": [{"id", "title"}]} with whitespace collapsed."""
    root = ET.fromstring(text)
    return {"entries": [{"id": (e.findtext(f"{_ATOM}id") or "").strip(),
                         "title": " ".join((e.findtext(f"{_ATOM}title") or "").split())}
                        for e in root.findall(f"{_ATOM}entry")]}


def default_fetch(url: str) -> dict | None:
    """GET: Crossref JSON, or the arXiv feed parsed by parse_arxiv_atom; None on any failure."""
    import requests
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": "QUANTGEN-paper-refs/1.0"})
        if r.status_code != 200:
            return None
        return parse_arxiv_atom(r.text) if url.startswith(ARXIV) else r.json()
    except Exception:          # network, JSON or XML failure: the entry stays unverified (ok: false)
        return None


def verify_entry(entry: dict, *, fetch: Fetch, now_utc: str) -> dict:
    """The entry's `verified` record. DOI wins over arXiv; neither means manual."""
    if entry.get("doi"):
        url = CROSSREF + quote(str(entry["doi"]), safe="/")
        msg = (fetch(url) or {}).get("message") or {}
        title = html.unescape(" ".join((msg.get("title") or [""])[:1] + (msg.get("subtitle") or [])[:1]))
        ok = bool(_norm(title)) and _norm(title) == _norm(entry["title"])
        return {"method": "doi", "url": url, "retrieved_utc": now_utc, "fetched_title": title, "ok": ok}
    if entry.get("arxiv"):
        url = ARXIV + str(entry["arxiv"])
        base = re.sub(r"v\d+$", "", str(entry["arxiv"]))
        hits = [x for x in (fetch(url) or {}).get("entries", []) if base in x.get("id", "")]
        title = hits[0]["title"] if hits else ""
        ok = bool(_norm(title)) and _norm(title) == _norm(entry["title"])
        return {"method": "arxiv", "url": url, "retrieved_utc": now_utc, "fetched_title": title, "ok": ok}
    prior = entry.get("verified") or {}
    if prior.get("method") == "manual":
        return dict(prior)
    return {"method": "manual", "url": entry.get("url", ""), "retrieved_utc": now_utc, "fetched_title": "",
            "ok": False}


def ref_problems(refs) -> list[str]:
    """One line per entry without an ok record that names a url, or whose DOI / arXiv record was fetched for another
    id or title than the entry now has (edited after verification, or copied from another entry)."""
    out = []
    for e in refs:
        v = e.get("verified") or {}
        if not v:
            out.append(f"{e['key']}: no verified record")
        elif v.get("ok") is not True:
            out.append(f"{e['key']}: not verified ({v.get('method')}: fetched {v.get('fetched_title', '')!r})")
        elif not v.get("url"):
            out.append(f"{e['key']}: verified record has no url")
        elif e.get("doi") or e.get("arxiv"):
            expected = (("doi", CROSSREF + quote(str(e["doi"]), safe="/")) if e.get("doi")
                        else ("arxiv", ARXIV + str(e["arxiv"])))
            if (v.get("method"), v.get("url")) != expected or _norm(v.get("fetched_title")) != _norm(e["title"]):
                out.append(f"{e['key']}: verified record does not match the entry; "
                           "rerun python -m tools.paper.refs verify")
    return out


def verify_file(path, *, fetch: Fetch, now_utc: str) -> list[str]:
    """Verify every entry, write the records back into refs.yaml, return the problems."""
    refs = load_refs(path)
    for e in refs:
        e["verified"] = verify_entry(e, fetch=fetch, now_utc=now_utc)
    Path(path).write_text(yaml.safe_dump(refs, allow_unicode=True, sort_keys=False, width=1000), encoding="utf-8",
                          newline="\n")
    return ref_problems(refs)


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2 or argv[0] not in ("verify", "bib"):
        print("usage: python -m tools.paper.refs verify|bib <paper_dir>", file=sys.stderr)
        return 2
    paper = Path(argv[1])
    if argv[0] == "verify":
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        verify_file(paper / "refs.yaml", fetch=default_fetch, now_utc=now)
    refs = load_refs(paper / "refs.yaml")
    write_bib(refs, paper / "refs.bib")
    problems = ref_problems(refs)
    for p in problems:
        print(p)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
