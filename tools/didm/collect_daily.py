"""DIDM daily collector (DS-4a). Runs on the owner's PC, not in CI or the cloud.

    python -m tools.didm.collect_daily --data-dir <folder outside the repository> [--finbert]
    python -m tools.didm.collect_daily --data-dir <folder> --alfred CPIAUCSL PAYEMS
    python -I -m tools.didm.collect_daily --data-dir <folder> --alfred-file CPIAUCSL=<downloaded .xlsx>
    python -m tools.didm.collect_daily --data-dir <folder> --no-gdelt --edgar 320193 --opendart 20261117 20261118 \
        --ecos 722Y001,M,202401,202612,0101000 --kalshi KXFED

Keys / settings by name only: FRED_API_KEY, OPENDART_API_KEY (existing), ECOS_API_KEY,
SEC_EDGAR_USER_AGENT (generic contact). Kalshi and GDELT need none.

Steps: GDELT 2.0 newest 15-minute events + GKG files -> point-in-time store
(<data-dir>/didm_store.sqlite). Optional: FinBERT baseline polarity on GKG page
titles (local model, needs `transformers` and `torch`; skipped with a reason if
absent -- never a made-up score). Optional: ALFRED vintages via FRED_API_KEY, or from
a manual "Observations by Real-Time Period" download (needs openpyxl).

Prints counts and reason codes only: no keys, no URLs with keys, no article text.
Collected data is never written inside the repository.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

import config  # noqa: F401 - loads the project .env into the environment, like the app

from core.didm.ingest import alfred as alfred_ingest
from core.didm.ingest import ecos as ecos_ingest
from core.didm.ingest import filings as filings_ingest
from core.didm.ingest import gdelt as gdelt_ingest
from core.didm.ingest import kalshi as kalshi_ingest
from core.didm.llm.schema import ess_like
from core.didm.store import PointInTimeStore

REPO = Path(__file__).resolve().parents[2]
KEY_NAMES = ("FRED_API_KEY", "OPENDART_API_KEY", "ECOS_API_KEY", "SEC_EDGAR_USER_AGENT")


def key_status(env: Mapping[str, str] | None = None) -> dict[str, bool]:
    """Which settings are present (names and True/False only; values are never returned)."""
    env = os.environ if env is None else env
    return {name: bool(str(env.get(name, "")).strip()) for name in KEY_NAMES}
FINBERT_MODEL = "ProsusAI/finbert"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _data_dir(path: str) -> Path:
    d = Path(path).expanduser().resolve()
    if d == REPO or REPO in d.parents:
        raise SystemExit("--data-dir must be outside the repository (collected data is not committed)")
    d.mkdir(parents=True, exist_ok=True)
    return d


def collect_gdelt(store: PointInTimeStore) -> tuple[int, list[dict]]:
    from data.didm import gdelt as gdelt_http
    rows, refs = gdelt_ingest.ingest_latest(
        gdelt_http.fetch_text, gdelt_http.fetch_bytes, gdelt_http.LASTUPDATE_URL, _now())
    added = store.append_many(rows)
    print(f"GDELT files {len(refs)} ({', '.join(r.stamp + ':' + r.kind for r in refs)}), "
          f"rows {len(rows)}, new {added}")
    return added, rows


def finbert_baseline(store: PointInTimeStore, rows: list[dict]) -> str:
    try:
        from transformers import pipeline  # optional, owner PC only
    except Exception:  # noqa: BLE001 - any import failure means "not installed"
        return "finbert_unavailable"
    titled = [r for r in rows if r["kind"] == "gdelt_gkg" and r["payload"].get("page_title")]
    if not titled:
        return "no_titles"
    clf = pipeline("text-classification", model=FINBERT_MODEL, top_k=None)
    received = _now()
    n = 0
    for r in titled:
        scores = {d["label"].lower(): float(d["score"]) for d in clf(r["payload"]["page_title"][:512])[0]}
        p_pos, p_neg = scores.get("positive", 0.0), scores.get("negative", 0.0)
        n += store.append(
            source_id="finbert-baseline", item_id=r["item_id"], kind="finbert_baseline",
            published_at=r["published_at"], received_at=received, valid_at=r["valid_at"],
            payload={"model": FINBERT_MODEL, "p_positive": p_pos, "p_negative": p_neg,
                     "p_neutral": scores.get("neutral", 0.0), "ess_like_0_100": ess_like(p_pos, p_neg),
                     "input": "gkg_page_title"})
    return f"scored {n}"


def collect_alfred_api(store: PointInTimeStore, series: list[str]) -> None:
    from data.didm import alfred as alfred_http
    if not alfred_http.has_key():
        print(f"ALFRED skipped: {alfred_http.KEY_NAME} not set (use --alfred-file)")
        return
    for sid in series:
        rows = alfred_ingest.rows_from_api(sid, alfred_http.fetch_vintages(sid), _now())
        print(f"ALFRED {sid}: vintage rows {len(rows)}, new {store.append_many(rows)}")


def collect_alfred_file(store: PointInTimeStore, spec: str) -> None:
    import openpyxl  # owner PC; untrusted input, run with python -I
    sid, _, path = spec.partition("=")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheet = wb["Obs. By Real-Time Period"]
    rows = alfred_ingest.rows_from_manual(sid, list(sheet.iter_rows(values_only=True))[1:], _now())
    print(f"ALFRED file {sid}: vintage rows {len(rows)}, new {store.append_many(rows)}")


def _run(label: str, fn) -> None:
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 - one source failing must not stop the others
        print(f"{label} failed: {type(exc).__name__}")


def collect_edgar(store: PointInTimeStore, ciks: list[str]) -> None:
    from data.didm import edgar
    for cik in ciks:
        rows = filings_ingest.edgar_rows(edgar.fetch_submissions(int(cik)), _now())
        print(f"EDGAR CIK {int(cik)}: filings {len(rows)}, new {store.append_many(rows)}")


def collect_opendart(store: PointInTimeStore, bgn: str, end: str) -> None:
    from data.didm import opendart
    pages = opendart.fetch_listing(bgn, end)
    received = _now()
    rows = [r for p in pages for r in filings_ingest.opendart_rows(p, received)]
    print(f"OpenDART {bgn}-{end}: pages {len(pages)}, filings {len(rows)}, new {store.append_many(rows)}")


def collect_ecos(store: PointInTimeStore, spec: str) -> None:
    from data.didm import ecos
    stat, cycle, start, end, *items = spec.split(",")
    rows = ecos_ingest.rows(ecos.fetch_series(stat, cycle, start, end, *items), _now())
    print(f"ECOS {stat}: observations {len(rows)}, new {store.append_many(rows)}")


def collect_kalshi(store: PointInTimeStore, series: str) -> None:
    from data.didm import kalshi
    rows = kalshi_ingest.market_snapshot_rows(kalshi.fetch_markets(series), _now())
    liquid = sum(1 for r in rows if r["payload"]["liquid"])
    print(f"Kalshi {series}: markets {len(rows)} (liquid {liquid}), new {store.append_many(rows)}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="DIDM daily collector (owner PC)")
    ap.add_argument("--check-keys", action="store_true",
                    help="print which key names are set (True/False only) and exit")
    ap.add_argument("--data-dir")
    ap.add_argument("--no-gdelt", action="store_true")
    ap.add_argument("--finbert", action="store_true")
    ap.add_argument("--alfred", nargs="*", default=[])
    ap.add_argument("--alfred-file", action="append", default=[], metavar="SERIES=PATH")
    ap.add_argument("--edgar", nargs="*", default=[], metavar="CIK")
    ap.add_argument("--opendart", nargs=2, metavar=("BGN_YYYYMMDD", "END_YYYYMMDD"))
    ap.add_argument("--ecos", action="append", default=[], metavar="STAT,CYCLE,START,END[,ITEM...]")
    ap.add_argument("--kalshi", nargs="*", default=[], metavar="SERIES")
    args = ap.parse_args(argv)
    if args.check_keys:
        for name, present in key_status().items():
            print(f"{name}: {present}")
        return 0
    if not args.data_dir:
        ap.error("--data-dir is required")
    with PointInTimeStore(_data_dir(args.data_dir) / "didm_store.sqlite") as store:
        rows: list[dict] = []
        if not args.no_gdelt:
            try:
                _, rows = collect_gdelt(store)
            except Exception as exc:  # noqa: BLE001 - report a reason code, keep going
                print(f"GDELT failed: {type(exc).__name__}")
        if args.finbert:
            print(f"FinBERT baseline: {finbert_baseline(store, rows)}")
        if args.alfred:
            collect_alfred_api(store, args.alfred)
        for spec in args.alfred_file:
            collect_alfred_file(store, spec)
        if args.edgar:
            _run("EDGAR", lambda: collect_edgar(store, args.edgar))
        if args.opendart:
            _run("OpenDART", lambda: collect_opendart(store, *args.opendart))
        for spec in args.ecos:
            _run("ECOS", lambda spec=spec: collect_ecos(store, spec))
        for series in args.kalshi:
            _run("Kalshi", lambda series=series: collect_kalshi(store, series))
    print(gdelt_ingest.ATTRIBUTION)
    return 0


if __name__ == "__main__":
    sys.exit(main())
