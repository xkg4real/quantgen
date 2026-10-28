"""Owner sign-off for core/calendars/data files (R-20 rule 6; T-CAL-01, T-CAL-02).

Run by the owner only: the library and the build never sign (spec L2100). For every named file this records the
owner's signature the way the loader checks it, in this order: signed_off_by on every row and on the file, signed_utc
(now, UTC), md5 = content md5 of the signed document, then the matching MANIFEST.yaml row (version, md5, signer). It
then loads each file through CalendarSet and restores every file it touched if any of them is still refused.

    python -m tools.sign_calendars --signer "<signed_off_by>" holidays_KRX holidays_NYSE holidays_FED holidays_SIFMA

The draft fingerprints printed before the prompt are the content md5 of the unsigned files; compare them with the
signing form (docs/audit/2026-10-27/02_signing_form_T-CAL-02.md) or pass --expect FILE=MD5 to enforce them.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

import yaml

from core.calendars import store

PLACEHOLDERS = ("TEST-FIXTURE", "SIMULATION")
CAL02_FILES = ("holidays_KRX", "holidays_NYSE", "holidays_FED", "holidays_SIFMA")
CAL02_DEADLINE = datetime(2026, 11, 1, tzinfo=timezone.utc)


class SignRefused(Exception):
    """The signature was not written (bad signer, unknown or already-signed file, fingerprint mismatch)."""


def _dump(doc: dict) -> str:
    return yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120)


def fingerprints(file_ids: Iterable[str], *, data_dir: Path = store.DATA_DIR) -> dict[str, str]:
    """Content md5 of each unsigned file as it stands (what the owner reviewed)."""
    return {fid: store.content_md5(store.read_yaml(Path(data_dir) / f"{fid}.yaml")) for fid in file_ids}


def sign(file_ids: Iterable[str], signer: str, *, data_dir: Path = store.DATA_DIR,
         now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
         expect: dict[str, str] | None = None) -> list[dict]:
    """Sign the named unsigned files; returns one {file, version, md5, signed_utc} per file."""
    file_ids, data_dir = list(dict.fromkeys(file_ids)), Path(data_dir)
    if not isinstance(signer, str) or not signer.strip():
        raise SignRefused("signer is empty")
    if any(tag in signer.upper() for tag in PLACEHOLDERS):
        raise SignRefused(f"{signer!r} is a test or simulation placeholder, not an owner signature")
    if not file_ids:
        raise SignRefused("no file named")
    current = store.CalendarSet(data_dir)
    for fid in file_ids:
        if not (data_dir / f"{fid}.yaml").is_file():
            raise SignRefused(f"{fid}.yaml: no such file in {data_dir}")
        if current.refusal(fid) is None:
            raise SignRefused(f"{fid}.yaml is already signed; a change is a new version with a new signature")
    if expect:
        got = fingerprints(expect, data_dir=data_dir)
        wrong = {fid: (want, got[fid]) for fid, want in expect.items() if got[fid] != want}
        if wrong:
            raise SignRefused(f"draft fingerprint mismatch (expected, found): {wrong}")

    signed_utc = now().astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest_path = data_dir / store.MANIFEST
    originals = {p: p.read_text(encoding="utf-8") for p in [manifest_path] + [data_dir / f"{f}.yaml" for f in file_ids]}
    manifest = store.read_yaml(manifest_path)
    rows = {r["file"]: r for r in manifest["rows"]}
    out = []
    try:
        for fid in file_ids:
            path = data_dir / f"{fid}.yaml"
            doc = store.read_yaml(path)
            for row in doc["rows"]:
                row["signed_off_by"] = signer
            doc["signed_off_by"], doc["signed_utc"] = signer, signed_utc
            doc["md5"] = store.content_md5(doc)
            path.write_text(_dump(doc), encoding="utf-8")
            entry = rows.get(path.name)
            if entry is None:
                raise SignRefused(f"{path.name}: no {store.MANIFEST} row")
            entry.update(version=doc["version"], md5=doc["md5"], signed_off_by=signer)
            out.append({"file": path.name, "version": doc["version"], "md5": doc["md5"], "signed_utc": signed_utc})
        manifest_path.write_text(_dump(manifest), encoding="utf-8")
        check = store.CalendarSet(data_dir)
        refused = {fid: check.refusal(fid) for fid in file_ids if check.refusal(fid) is not None}
        if refused:
            raise SignRefused(f"still refused after signing: {refused}")
    except Exception:
        for p, text in originals.items():
            p.write_text(text, encoding="utf-8")
        raise
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Owner sign-off for core/calendars/data files (owner only).")
    ap.add_argument("files", nargs="+", help="file ids, e.g. holidays_KRX (with or without .yaml)")
    ap.add_argument("--signer", required=True, help="the signed_off_by value, e.g. the owner's name")
    ap.add_argument("--expect", action="append", default=[], metavar="FILE=MD5", help="required draft fingerprint")
    ap.add_argument("--yes", action="store_true", help="skip the typed confirmation")
    ap.add_argument("--governance-log", type=Path, help="append one calendar_change event per signed file here")
    args = ap.parse_args(argv)
    file_ids = [f[:-5] if f.endswith(".yaml") else f for f in args.files]
    expect = dict(e.split("=", 1) for e in args.expect)

    current = store.CalendarSet()
    print(f"signer: {args.signer}\ndata:   {store.DATA_DIR}")
    for fid in file_ids:
        doc = store.read_yaml(store.DATA_DIR / f"{fid}.yaml")
        print(f"  {fid + '.yaml':24} v{doc.get('version')}  rows={len(doc.get('rows') or [])}  covers={doc.get('covers')}"
              f"  draft fingerprint={store.content_md5(doc)}  {'unsigned' if current.refusal(fid) else 'ALREADY SIGNED'}")
    if not args.yes and input("Type SIGN to record this signature: ").strip() != "SIGN":
        print("not signed")
        return 1
    try:
        done = sign(file_ids, args.signer, expect=expect)
    except SignRefused as exc:
        print(f"REFUSED: {exc}")
        return 1
    for row in done:
        print(f"signed   {row['file']:24} v{row['version']}  md5={row['md5']}  signed_utc={row['signed_utc']}")
    late = [r["file"] for r in done if r["file"][:-5] in CAL02_FILES
            and datetime.fromisoformat(r["signed_utc"].replace("Z", "+00:00")) >= CAL02_DEADLINE]
    if late:
        print(f"WARNING: {', '.join(late)} signed on or after 2026-11-01 UTC; test_cal02 (spec L2101) will fail")
    if args.governance_log:
        store.record_calendar_changes(args.governance_log, file_ids, lambda: datetime.now(timezone.utc),
                                      cal=store.CalendarSet(), actor="owner")
        print(f"governance: calendar_change events appended to {args.governance_log}")
    print("next: python -m tests.macro_m1_calendars  (test_cal02 runs once all four 2027 files are signed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
