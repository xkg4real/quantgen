"""Apply the owner's signature to the four audited holiday files (T-CAL-02; report section 7, steps 1-4 and 6).

Copies proposed/holidays_{KRX,NYSE,FED,SIFMA}.yaml into the data directory, writes the owner's signer on every row
and at file level with `signed_utc`, sets `md5` to the content md5 and updates the four MANIFEST.yaml rows (version,
md5, signer, test id T-CAL-02). It then reloads the directory with the real loader and checks the audited dates.

The signer and the time come from the owner's signature sentence, never from this script. The proposed files must be
the ones the owner reviewed: their content md5 is pinned in REVIEWED_MD5 and a changed file is refused. With
`--cal14 exclude` the three inferred Board closures (CAL-14) are dropped before signing.

    python docs/audit/2026-10-27/calendar_T-CAL-02/apply_signature.py --signer "<value>" \
        --signed-utc 2026-10-29T01:23:45Z --cal14 include [--data-dir DIR] [--governance-log PATH]

`--data-dir` defaults to core/calendars/data/; point it at a copy for a dry run.
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO))

from core.calendars import store  # noqa: E402

REPORT = "docs/audit/2026-10-27/01_calendar_T-CAL-02.md"
VERSION = "1.0.0"
DEADLINE_UTC = "2026-11-01T00:00:00Z"           # spec L2101: signed off before 2026-11-01
COVERS_TO_MIN = date(2027, 12, 31)
TEST_ID = "T-CAL-02"
# Content md5 (store.content_md5) of proposed/ as committed in 0849ca9 and reviewed by the owner.
REVIEWED_MD5 = {
    "holidays_KRX": "9c67594f0717fd8aad8161bc5db87609",
    "holidays_NYSE": "acb21e1c20b929648fd0085a456ad5e1",
    "holidays_FED": "f9be6eeb2e8580c6756e64cf752be686",
    "holidays_SIFMA": "43e5bdc9cbf9ca3ed04f0aa462e5e7b2",
}
CAL14 = ("2018-12-24", "2019-12-24", "2020-12-24")
CAL14_NOTE_IN = "class C rows (2018-12-24, 2019-12-24, 2020-12-24)"
CAL14_NOTE_OUT = ("2018-12-24, 2019-12-24 and 2020-12-24 (CAL-14) are left out by the owner's choice; if the Board was "
                  "closed on them, H.15 and H.10 are used one day early on those three dates")
# The audited dates (report sections 3 and 5), checked on the signed files after writing.
CLOSED = {
    "KRX": ("2026-06-03", "2026-07-17", "2027-05-03", "2027-07-19", "2027-02-09", "2027-12-31"),
    "NYSE": ("2027-03-26", "2027-06-18", "2027-12-24"),
    "FED": ("2027-12-31", "2025-01-09", "2025-12-24", "2025-12-26", "2021-06-18", "2027-07-05"),
    "SIFMA": ("2027-03-26",),
}
NOT_CLOSED = {"KRX": ("2026-06-04", "2027-05-04", "2027-07-20", "2027-12-30"), "NYSE": ("2027-12-31",),
              "FED": ("2027-12-30",), "SIFMA": ("2026-04-03",)}
EARLY = {"SIFMA": {"2026-04-03": "12:00", "2027-03-25": "14:00", "2027-05-28": "14:00", "2027-07-02": "14:00",
                   "2027-12-23": "14:00", "2025-01-09": "14:00"}}
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
PLACEHOLDER_SIGNERS = ("SIMULATION", "DRY RUN", "TEST-FIXTURE")     # refused on the shipped directory (dry runs only)


def dump(doc: dict) -> str:
    return yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120)


def load_reviewed(fid: str) -> dict:
    doc = store.read_yaml(HERE / "proposed" / f"{fid}.yaml")
    if any(doc.get(k) is not None for k in store.SIGNATURE_FIELDS) or any(r.get("signed_off_by") for r in doc["rows"]):
        raise SystemExit(f"{fid}: proposed file already carries a signature field")
    got = store.content_md5(doc)
    if got != REVIEWED_MD5[fid]:
        raise SystemExit(f"{fid}: proposed content md5 {got} != reviewed {REVIEWED_MD5[fid]}; the file changed after "
                         "the owner's review, so it needs a new review before signing")
    return doc


def drop_cal14(doc: dict) -> dict:
    kept = [r for r in doc["rows"] if r["date"] not in CAL14]
    gone = sorted(r["date"] for r in doc["rows"] if r["date"] in CAL14)
    if gone != list(CAL14) or not all(str(r.get("evidence", "")).startswith("C") for r in doc["rows"] if r["date"] in CAL14):
        raise SystemExit(f"holidays_FED: CAL-14 rows are {gone}, expected the three class C rows {CAL14}")
    doc["rows"] = kept
    doc["unverified"] = [CAL14_NOTE_OUT if CAL14_NOTE_IN in u else u for u in doc["unverified"]]
    return doc


def sign(doc: dict, signer: str, signed_utc: str, cal14: str) -> dict:
    for row in doc["rows"]:
        row["signed_off_by"] = signer
    note = f"; CAL-14 {cal14}d" if doc["file_id"] == "holidays_FED" else ""
    doc["status"] = f"SIGNED v{VERSION} by {signer} at {signed_utc} after the T-CAL-02 audit ({REPORT}){note}"
    doc["signed_off_by"], doc["signed_utc"] = signer, signed_utc
    doc["md5"] = store.content_md5(doc)
    return doc


def update_manifest(data_dir: Path, signed: dict[str, dict], signed_utc: str) -> None:
    path = data_dir / store.MANIFEST
    manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
    rows = {r["file"]: r for r in manifest["rows"]}
    for fid, doc in signed.items():
        row = rows[f"{fid}.yaml"]
        row.update(version=doc["version"], md5=doc["md5"], signed_off_by=doc["signed_off_by"])
        if TEST_ID not in row["test_ids"]:
            row["test_ids"].append(TEST_ID)
    manifest["status"] = (f"PARTIALLY SIGNED: {', '.join(signed)} v{VERSION} signed at {signed_utc} (T-CAL-02); "
                          "every other row is an unsigned draft and the loader refuses it")
    path.write_text(dump(manifest), encoding="utf-8")


def verify(data_dir: Path, signed: dict[str, dict], others_before: dict[str, str | None], cal14: str) -> list[str]:
    cal = store.CalendarSet(data_dir)
    bad = []
    for fid, doc in signed.items():
        reason = cal.refusal(fid)
        if reason:
            bad.append(f"{fid} refused: {reason}")
            continue
        f = cal.file(fid)
        if (f.version, f.md5, f.signed_utc) != (VERSION, doc["md5"], doc["signed_utc"]) or f.covers_to < COVERS_TO_MIN:
            bad.append(f"{fid}: loaded v{f.version} md5 {f.md5} signed {f.signed_utc} covers_to {f.covers_to}")
        set_id = fid.split("_", 1)[1]
        closed, early, _ = cal.holiday_set(set_id)
        want_closed = CLOSED.get(set_id, ()) + (CAL14 if set_id == "FED" and cal14 == "include" else ())
        want_open = NOT_CLOSED.get(set_id, ()) + (CAL14 if set_id == "FED" and cal14 == "exclude" else ())
        bad += [f"{fid}: {d} should be closed" for d in want_closed if date.fromisoformat(d) not in closed]
        bad += [f"{fid}: {d} should not be closed" for d in want_open if date.fromisoformat(d) in closed]
        bad += [f"{fid}: {d} early close {early.get(date.fromisoformat(d))!r} != {t!r}"
                for d, t in EARLY.get(set_id, {}).items() if early.get(date.fromisoformat(d)) != t]
    after = {fid: cal.refusal(fid) for fid in others_before}
    bad += [f"{fid}: load state changed ({others_before[fid]!r} -> {after[fid]!r})" for fid in others_before
            if (others_before[fid] is None) != (after[fid] is None)]
    return bad


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--signer", required=True, help="the signed_off_by value from the owner's signature sentence")
    ap.add_argument("--signed-utc", required=True, help="the time of the owner's signature message, YYYY-MM-DDTHH:MM:SSZ")
    ap.add_argument("--cal14", required=True, choices=("include", "exclude"), help="the owner's CAL-14 decision")
    ap.add_argument("--data-dir", type=Path, default=store.DATA_DIR)
    ap.add_argument("--governance-log", type=Path, help="append one calendar_change event per signed file")
    ap.add_argument("--allow-late", action="store_true", help="sign at or after the T-CAL-02 deadline")
    a = ap.parse_args(argv)

    signer = a.signer.strip()
    data_dir = a.data_dir.resolve()
    placeholder = any(tag in signer.upper() for tag in PLACEHOLDER_SIGNERS)
    if not signer or (placeholder and data_dir == store.DATA_DIR.resolve()):
        raise SystemExit("--signer must be the owner's signed_off_by value (placeholders only sign a --data-dir copy)")
    if not UTC_RE.match(a.signed_utc):
        raise SystemExit("--signed-utc must look like 2026-10-29T01:23:45Z")
    when = datetime.strptime(a.signed_utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    if when > datetime.now(timezone.utc):
        raise SystemExit(f"--signed-utc {a.signed_utc} is in the future; use the time of the owner's message")
    if a.signed_utc >= DEADLINE_UTC and not a.allow_late:
        raise SystemExit(f"--signed-utc {a.signed_utc} is not before {DEADLINE_UTC} (T-CAL-02 deadline clause); "
                         "pass --allow-late only on the owner's say-so")

    current = {fid: store.read_yaml(data_dir / f"{fid}.yaml") for fid in REVIEWED_MD5}
    already = [fid for fid, doc in current.items() if doc.get("signed_off_by") is not None]
    if already:
        raise SystemExit(f"{already} already signed in {data_dir}; a change is a new version with a new review")
    probe = store.CalendarSet(data_dir)
    others_before = {fid: probe.refusal(fid) for fid in probe.file_ids() if fid not in REVIEWED_MD5}

    signed = {}
    for fid in REVIEWED_MD5:
        doc = load_reviewed(fid)
        if fid == "holidays_FED" and a.cal14 == "exclude":
            doc = drop_cal14(doc)
        signed[fid] = sign(doc, signer, a.signed_utc, a.cal14)
        (data_dir / f"{fid}.yaml").write_text(dump(signed[fid]), encoding="utf-8")
    update_manifest(data_dir, signed, a.signed_utc)

    problems = verify(data_dir, signed, others_before, a.cal14)
    for fid, doc in signed.items():
        print(f"{fid:16} v{doc['version']} rows {len(doc['rows']):3} md5 {doc['md5']} signed_off_by {doc['signed_off_by']!r} "
              f"signed_utc {doc['signed_utc']}")
    if problems:
        print("\nVERIFY FAILED:\n  " + "\n  ".join(problems))
        return 1
    print(f"\nverified: the four files load from {data_dir}; audited dates match; other files unchanged")
    if a.governance_log:
        rows = store.record_calendar_changes(a.governance_log, tuple(signed), lambda: datetime.now(timezone.utc),
                                             cal=store.CalendarSet(data_dir))
        print(f"governance: {len(rows)} calendar_change event(s) appended to {a.governance_log}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
