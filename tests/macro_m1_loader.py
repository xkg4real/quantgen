"""Calendar loader edge cases on synthetic temporary files only (T-CAL-01)."""
from __future__ import annotations

import tempfile
from pathlib import Path

import yaml

from core.calendars import store
from tests.macro_m1_calendars import SIGNED_UTC, _doc, _row, _write_set, _raises
from tools import sign_calendars


def _small_doc(**fields):
    return _doc("holidays_NYSE", ("2025-01-01", "2027-12-31"), "NYSE",
                [_row(date="2025-07-03", kind="early_close", **fields)])


def test_cal01_sexagesimal_refused_before_load_or_sign():
    """YAML numeric coercion is refused even with matching fixture fingerprints; signing writes nothing."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        path = root / "holidays_NYSE.yaml"
        for key, literal in (("close_local", "13:00"), ("value", "15:30"), ("value", "13:00:30.5")):
            numeric = yaml.safe_load(f"value: {literal}")["value"]
            assert isinstance(numeric, (int, float))
            _write_set(root, {"holidays_NYSE": _small_doc(**{key: numeric})})
            raw = path.read_text(encoding="utf-8")
            raw = raw.replace(f"{key}: {numeric}", f"{key}: {literal}")
            path.write_text(raw, encoding="utf-8")
            # A fingerprint based on the old coercion is valid: refusal must happen while parsing.
            assert store.content_md5(yaml.safe_load(raw)) == yaml.safe_load(raw)["md5"]
            err = _raises(lambda: store.CalendarSet(root).file("holidays_NYSE"), store.CalendarUnsigned)
            assert "time" in str(err) and "line" in str(err)

        for raw, want in (("value: '13:00'\n", "13:00"), ("value: 09:30\n", "09:30"),
                          ("value: 780\n", 780), ("value: 1.25\n", 1.25)):
            path.write_text(raw, encoding="utf-8")
            assert store.read_yaml(path)["value"] == want
        assert yaml.safe_load("value: 13:00")["value"] == 780  # global PyYAML behavior unchanged

        # A valid draft precedes the malformed draft: preflight must refuse before any file is written.
        bad = _small_doc(close_local="13:00")
        good = _small_doc(close_local="14:00")
        good["file_id"] = "holidays_SIFMA"
        for doc in (bad, good):
            doc["signed_off_by"] = doc["signed_utc"] = doc["md5"] = None
        _write_set(root, {"holidays_NYSE": bad, "holidays_SIFMA": good})
        path.write_bytes(path.read_bytes().replace(b"'13:00'", b"13:00").replace(b"\n", b"\r\n"))
        before = {p.name: p.read_bytes() for p in root.glob("*.yaml")}
        err = _raises(lambda: sign_calendars.sign(["holidays_SIFMA", "holidays_NYSE"],
                                                "owner:test", data_dir=root), sign_calendars.SignRefused)
        assert "time" in str(err)
        assert {p.name: p.read_bytes() for p in root.glob("*.yaml")} == before


test_cal01_sexagesimal_refused_before_load_or_sign.test_ids = ["T-CAL-01"]


def test_cal01_signature_time_is_an_iso_utc_instant():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for stamp in ("10/30/2026", "2026-10-30", "2026-10-30T09:00:00+09:00",
                      "2026-10-30T09:00:00", "2026-10-30 09:00:00Z", "2026-02-30T09:00:00Z",
                      "2026-10-30T09:00:00-00:00"):
            doc = _small_doc(close_local="13:00")
            doc["signed_utc"] = stamp
            _write_set(root, {"holidays_NYSE": doc})
            err = _raises(lambda: store.CalendarSet(root).file("holidays_NYSE"), store.CalendarUnsigned)
            assert "signed_utc" in str(err)
        for stamp in (SIGNED_UTC, "2026-10-30T09:00:00+00:00", "2026-10-30T09:00:00.123Z"):
            doc = _small_doc(close_local="13:00")
            doc["signed_utc"] = stamp
            _write_set(root, {"holidays_NYSE": doc})
            assert store.CalendarSet(root).file("holidays_NYSE").signed_utc == stamp


test_cal01_signature_time_is_an_iso_utc_instant.test_ids = ["T-CAL-01"]
