"""DIDM daily collector (DS-4a). Runs on the owner's PC, not in CI or the cloud.

    python -m tools.didm.collect_daily --data-dir <folder outside the repository> [--finbert]
    python -m tools.didm.collect_daily --data-dir <folder> --alfred CPIAUCSL PAYEMS
    python -I -m tools.didm.collect_daily --data-dir <folder> --alfred-file CPIAUCSL=<downloaded .xlsx>
    python -m tools.didm.collect_daily --data-dir <folder> --no-gdelt --edgar-history 320193 --edgar-from 2015-01-01 --edgar-to 2024-12-31
    python -m tools.didm.collect_daily --data-dir <folder> --no-gdelt --edgar 320193 --opendart 20261117 20261118 \
        --ecos "722Y001,M,202401,202610,0101000" --kalshi KXFED
    python -m tools.didm.collect_daily --data-dir <folder> --no-gdelt --kalshi-history KXFED --kalshi-from 2021-07-01 --kalshi-to 2024-12-31

In PowerShell, quote every comma-separated value (--ecos "..."): unquoted, PowerShell
reads it as an array and turns 0101000 into 101000 (owner run 2026-11-18).

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
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Mapping

import config  # noqa: F401 - loads the project .env into the environment, like the app

from core.didm.ingest import alfred as alfred_ingest
from core.didm.ingest import ecos as ecos_ingest
from core.didm.ingest import filings as filings_ingest
from core.didm.ingest import gdelt as gdelt_ingest
from core.didm.ingest import kalshi as kalshi_ingest
from core.didm.ingest import news as news_ingest
from core.didm.llm.schema import ess_like
from core.didm.store import PointInTimeStore

REPO = Path(__file__).resolve().parents[2]
KEY_NAMES = ("FRED_API_KEY", "OPENDART_API_KEY", "ECOS_API_KEY", "SEC_EDGAR_USER_AGENT",
             "ALPHAVANTAGE_API_KEY", "TIINGO_API_KEY", "CRYPTOPANIC_API_KEY")


def load_env_file(path: str) -> None:
    """Load KEY=VALUE lines from another .env into this process only (no override, no output)."""
    from dotenv import load_dotenv
    env = Path(path).expanduser()
    if not env.is_file():
        raise SystemExit(f"--env-file: no file at {env}")
    load_dotenv(env, override=False)


def key_status(env: Mapping[str, str] | None = None) -> dict[str, bool]:
    """Which settings are present (names and True/False only; values are never returned)."""
    if env is None:
        from data.didm import keys as didm_keys
        return {name: didm_keys.key_status(name)["present"] for name in KEY_NAMES}
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


_SAFE_MODULES = ("core.didm.", "data.didm.")


def _http_reason(exc: Exception) -> str:
    """Exception name, HTTP status, and the message only for DIDM's own exceptions (written to hold no
    key or key-bearing URL). Library exceptions (requests etc.) can carry URLs with keys: name only."""
    name = type(exc).__name__
    if type(exc).__module__.startswith(_SAFE_MODULES) and str(exc):
        return f"{name}: {exc}"
    resp = getattr(exc, "response", None)
    code = getattr(resp, "status_code", None)
    return name + (f" HTTP {code}" if code is not None else "")


def _stamp_completed_batch(rows: list[dict]) -> None:
    """Use batch completion as a conservative availability time after fetching and parsing.

    The ingest functions accept one timestamp before invoking their fetchers. That
    initial time must not enter the store as if the downloads had already finished.
    """
    received = _now()
    for row in rows:
        row["received_at"] = received


def collect_gdelt(store: PointInTimeStore) -> tuple[int, list[dict]]:
    from data.didm import gdelt as gdelt_http
    stage = ["lastupdate"]

    def text(url):
        stage[0] = "lastupdate"
        return gdelt_http.fetch_text(url)

    def blob(url):
        stage[0] = url.rsplit("/", 1)[-1]  # public file name, e.g. 20261118011500.gkg.csv.zip
        return gdelt_http.fetch_bytes(url)

    try:
        rows, refs = gdelt_ingest.ingest_latest(text, blob, gdelt_http.LASTUPDATE_URL, _now())
    except Exception as exc:  # noqa: BLE001
        print(f"GDELT failed at {stage[0]}: {_http_reason(exc)}")
        code = getattr(getattr(exc, "response", None), "status_code", None)
        if code == 404 and stage[0][:14].isdigit():
            # The newest file in lastupdate is not published yet: take the two slots before it.
            first = gdelt_ingest.previous_stamp(stage[0][:14])
            stamps = [gdelt_ingest.previous_stamp(first), first]
            rows, fetched, missing = gdelt_ingest.ingest_stamps(
                gdelt_http.fetch_bytes_optional, stamps, _now(), kinds=("events", "gkg"))
            _stamp_completed_batch(rows)
            added = store.append_many(rows)
            print(f"GDELT fallback {stamps[0]}..{stamps[-1]}: files {len(fetched)}, missing {len(missing)}, "
                  f"rows {len(rows)}, new {added} (zip CRC checked, md5 not published for these)")
            return added, rows
        return 0, []
    _stamp_completed_batch(rows)
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
    n = 0
    for r in titled:
        scores = {d["label"].lower(): float(d["score"]) for d in clf(r["payload"]["page_title"][:512])[0]}
        p_pos, p_neg = scores.get("positive", 0.0), scores.get("negative", 0.0)
        n += store.append(
            source_id="finbert-baseline", item_id=r["item_id"], kind="finbert_baseline",
            published_at=r["published_at"], received_at=_now(), valid_at=r["valid_at"],
            payload={"model": FINBERT_MODEL, "p_positive": p_pos, "p_negative": p_neg,
                     "p_neutral": scores.get("neutral", 0.0), "ess_like_0_100": ess_like(p_pos, p_neg),
                     "input": "gkg_page_title"})
    return f"scored {n}"


def collect_gdelt_day(store: PointInTimeStore, day: str, with_gkg: bool) -> None:
    from datetime import date as _date
    from data.didm import gdelt as gdelt_http
    d = _date(int(day[:4]), int(day[4:6]), int(day[6:8]))
    kinds = ("events", "gkg") if with_gkg else ("events",)
    rows, fetched, missing = gdelt_ingest.ingest_stamps(
        gdelt_http.fetch_bytes_optional, gdelt_ingest.stamps_for_day(d), _now(), kinds=kinds)
    _stamp_completed_batch(rows)
    print(f"GDELT day {day} UTC ({'+'.join(kinds)}): files {len(fetched)}, missing {len(missing)}, "
          f"rows {len(rows)}, new {store.append_many(rows)}")


def probe_ecos(spec: str) -> None:
    """Try a few request variants for one series; print masked paths and counts. Stores nothing."""
    from data.didm import ecos
    stat, cycle, start, end, items = ecos_spec(spec)
    variants = [
        ("as collected", dict(rows=1000), items),
        ("rows 100", dict(rows=100), items),
        ("no item code", dict(rows=1000), []),
        ("trailing slash", dict(rows=1000, trailing_slash=True), items),
    ]
    for label, kw, its in variants:
        try:
            payload = ecos.fetch_series(stat, cycle, start, end, *its, **kw)
        except Exception as exc:  # noqa: BLE001
            print(f"ECOS probe [{label}] {ecos.masked_path(stat, cycle, start, end, *its, **kw)}: {_http_reason(exc)}")
            continue
        body = payload.get("StatisticSearch") or {}
        result = payload.get("RESULT") or {}
        print(f"ECOS probe [{label}] {ecos.masked_path(stat, cycle, start, end, *its, **kw)}: "
              f"rows {len(body.get('row') or [])}, total {body.get('list_total_count')}, "
              f"result {result.get('CODE')} {result.get('MESSAGE') or ''}".rstrip())


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
        print(f"{label} failed: {_http_reason(exc)}")


def collect_edgar(store: PointInTimeStore, ciks: list[str]) -> None:
    from data.didm import edgar
    for cik in ciks:
        rows = filings_ingest.edgar_rows(edgar.fetch_submissions(int(cik)), _now())
        print(f"EDGAR CIK {int(cik)}: filings {len(rows)}, new {store.append_many(rows)}")


def collect_edgar_history(store: PointInTimeStore, ciks: list[str], start: str | None, end: str | None,
                          max_files: int, fetch_submissions=None, fetch_file=None) -> list[dict]:
    """D6: filings between start and end (filing dates, inclusive) from filings.recent plus the older
    submissions files that overlap the range. Same User-Agent and spacing as --edgar."""
    if fetch_submissions is None or fetch_file is None:
        from data.didm import edgar
        fetch_submissions = fetch_submissions or edgar.fetch_submissions
        fetch_file = fetch_file or edgar.fetch_history_file
    lo = date.fromisoformat(start) if start else None
    hi = date.fromisoformat(end) if end else None
    if lo and hi and lo > hi:
        raise SystemExit("--edgar-from must not be after --edgar-to")

    def in_range(row: dict) -> bool:
        d = date.fromisoformat(row["payload"]["filing_date"])
        return (lo is None or d >= lo) and (hi is None or d <= hi)

    results = []
    for cik in ciks:
        subs = fetch_submissions(int(cik))
        received = _now()
        rows = [r for r in filings_ingest.edgar_rows(subs, received) if in_range(r)]
        files = filings_ingest.edgar_history_files(subs, lo, hi)
        read = 0
        for entry in files[:max_files]:
            payload = fetch_file(entry["name"])
            rows += [r for r in filings_ingest.edgar_history_rows(subs, entry, payload, _now()) if in_range(r)]
            read += 1
        dates = sorted(r["payload"]["filing_date"] for r in rows)
        added = store.append_many(rows)
        complete = read == len(files)
        print(f"EDGAR history CIK {int(cik)} {start or '-'}..{end or '-'}: files {read}/{len(files)} "
              f"(complete {complete}), filings {len(rows)}, first {dates[0] if dates else '-'}, "
              f"last {dates[-1] if dates else '-'}, new {added}")
        results.append({"cik": int(cik), "files": len(files), "read": read, "filings": len(rows), "added": added})
    return results


def collect_opendart(store: PointInTimeStore, bgn: str, end: str) -> None:
    from data.didm import opendart
    pages = opendart.fetch_listing(bgn, end)
    received = _now()
    rows = [r for p in pages for r in filings_ingest.opendart_rows(p, received)]
    print(f"OpenDART {bgn}-{end}: pages {len(pages)}, filings {len(rows)}, new {store.append_many(rows)}")


def ecos_spec(spec: str) -> tuple[str, str, str, str, list[str]]:
    """Split STAT,CYCLE,START,END[,ITEM...]; refuse item codes that lost a leading zero.

    ECOS item codes used here are 7 digits, so a 6-digit numeric code is almost
    certainly PowerShell's number conversion of an unquoted argument.
    """
    stat, cycle, start, end, *items = [p.strip() for p in spec.split(",")]
    for item in items:
        if item.isdigit() and len(item) < 7:
            raise SystemExit(f"ECOS item code {item!r} looks like it lost a leading zero; "
                             f'put the whole --ecos value in quotes, e.g. --ecos "{stat},{cycle},{start},{end},0{item}"')
    return stat, cycle, start, end, items


def collect_ecos(store: PointInTimeStore, spec: str) -> None:
    from data.didm import ecos
    stat, cycle, start, end, items = ecos_spec(spec)
    payload = ecos.fetch_series(stat, cycle, start, end, *items)
    rows = ecos_ingest.rows(payload, _now())
    result = payload.get("RESULT") or {}
    note = f" (ECOS {result.get('CODE')}: {result.get('MESSAGE')})" if result else ""
    print(f"ECOS {stat} {cycle} {start}-{end}: observations {len(rows)}, new {store.append_many(rows)}{note}")


def collect_alphavantage(store: PointInTimeStore, tickers: list[str]) -> None:
    from data.didm import alphavantage
    rows = news_ingest.alphavantage_rows(alphavantage.fetch_news(tickers=tickers or None), _now())
    rel = sum(1 for r in rows if r["payload"]["has_relevance_field"])
    print(f"Alpha Vantage news {','.join(tickers) or 'all'}: articles {len(rows)}, "
          f"with ticker relevance_score {rel}, new {store.append_many(rows)}")


def collect_tiingo(store: PointInTimeStore, tickers: list[str]) -> None:
    from data.didm import tiingo
    rows = news_ingest.tiingo_rows(tiingo.fetch_news(tickers=tickers or None), _now())
    tags = sum(1 for r in rows if r["payload"]["has_tags_field"])
    back = sum(1 for r in rows if r["payload"]["backfilled"])
    print(f"Tiingo news {','.join(tickers) or 'all'}: articles {len(rows)}, with tags field {tags}, "
          f"backfilled (>24h) {back}, new {store.append_many(rows)}")


def collect_cryptopanic(store: PointInTimeStore, codes: list[str]) -> None:
    from data.didm import cryptopanic
    payload, path = cryptopanic.fetch_posts(codes or None)
    rows = news_ingest.cryptopanic_rows(payload, _now())
    voted = sum(1 for r in rows if r["payload"]["votes"] is not None)
    tagged = sum(1 for r in rows if r["payload"]["currencies"])
    print(f"CryptoPanic {','.join(codes) or 'all'} (api {path}): posts {len(rows)}, with votes {voted}, "
          f"with currency tags {tagged}, new {store.append_many(rows)}")
    if rows and voted == 0:
        first = sorted((payload.get("results") or [{}])[0].keys())
        print(f"CryptoPanic field names (first post): {', '.join(first)}")


def show_ecos_items(stat: str) -> None:
    """Public table metadata only: item code, name, cycle, first and last period."""
    from data.didm import ecos
    payload = ecos.fetch_item_list(stat)
    body = payload.get("StatisticItemList") or {}
    rows = body.get("row") or []
    if not rows:
        result = payload.get("RESULT") or {}
        print(f"ECOS items {stat}: none (ECOS {result.get('CODE')}: {result.get('MESSAGE')})")
    for r in rows[:40]:
        print(f"ECOS items {stat}: {r.get('ITEM_CODE')} {r.get('ITEM_NAME')} cycle {r.get('CYCLE')} "
              f"{r.get('START_TIME')}-{r.get('END_TIME')}")


def _epoch(day: str, end_of_day: bool = False) -> int:
    d = datetime.combine(date.fromisoformat(day), datetime.min.time(), tzinfo=timezone.utc)
    return int(d.timestamp()) + (86_399 if end_of_day else 0)


def _market_ts(market: dict, key: str) -> int | None:
    raw = market.get(key)
    if not raw:
        return None
    try:
        t = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None
    return int((t if t.tzinfo else t.replace(tzinfo=timezone.utc)).timestamp())


def collect_kalshi_history(store: PointInTimeStore, series_list: list[str], start: str, end: str | None,
                           statuses: list[str], max_markets: int, max_pages: int = 20,
                           list_markets=None, fetch_candles=None, window_days: int = 365) -> list[dict]:
    """D7: daily candles (period 1440) of markets in a series that were alive between start and end,
    closed and settled ones included. Market lists use the cursor checks of fetch_all_markets;
    candle requests are split into windows of at most window_days."""
    if list_markets is None or fetch_candles is None:
        from data.didm import kalshi
        list_markets = list_markets or kalshi.fetch_all_markets
        fetch_candles = fetch_candles or kalshi.fetch_candlesticks
    lo = _epoch(start)
    hi = _epoch(end, end_of_day=True) if end else int(_now().timestamp())
    if lo > hi:
        raise SystemExit("--kalshi-from must not be after --kalshi-to")
    results = []
    for series in series_list:
        markets, pages, complete = {}, 0, True
        for status in statuses:
            got = list_markets(series, status, max_pages, min_close_ts=lo)
            pages += got["pages"]
            complete = complete and got["complete"]
            for m in got["markets"]:
                opened = _market_ts(m, "open_time")
                if m.get("ticker") and (opened is None or opened <= hi):
                    markets.setdefault(m["ticker"], m)
        tickers = sorted(markets)[:max_markets]
        candles = added = with_candles = 0
        first = last = None
        for ticker in tickers:
            m = markets[ticker]
            a = max(lo, _market_ts(m, "open_time") or lo)
            b = min(hi, _market_ts(m, "close_time") or hi)
            rows = []
            while a <= b:
                w_end = min(b, a + window_days * 86_400 - 1)
                rows += kalshi_ingest.candlestick_rows(ticker, fetch_candles(series, ticker, a, w_end, 1440), _now())
                a = w_end + 1
            if rows:
                with_candles += 1
                days = sorted(r["valid_at"].date().isoformat() for r in rows)
                first = min(first or days[0], days[0])
                last = max(last or days[-1], days[-1])
            candles += len(rows)
            added += store.append_many(rows)
        capped = len(markets) > len(tickers)
        print(f"Kalshi history {series} {start}..{end or 'now'}: markets {len(markets)} (pages {pages}, "
              f"complete {complete}{', capped at ' + str(max_markets) if capped else ''}), "
              f"with candles {with_candles}, candles {candles}, first {first or '-'}, last {last or '-'}, new {added}")
        results.append({"series": series, "markets": len(markets), "read": len(tickers), "complete": complete,
                        "candles": candles, "added": added})
    return results


def collect_kalshi(store: PointInTimeStore, series: str) -> None:
    from data.didm import kalshi
    got = kalshi.fetch_all_markets(series)
    rows = kalshi_ingest.market_snapshot_rows(got, _now())
    liquid = sum(1 for r in rows if r["payload"]["liquid"])
    priced = sum(1 for r in rows if r["payload"]["p_yes"] is not None)
    no_volume = sum(1 for r in rows if r["payload"]["volume"] is None)
    first = sorted((got.get("markets") or [{}])[0].keys())
    print(f"Kalshi {series}: pages {got['pages']} (complete {got['complete']}), markets {len(rows)}, "
          f"priced {priced}, volume missing {no_volume}, liquid {liquid}, new {store.append_many(rows)}")
    if rows and (priced == 0 or no_volume == len(rows)):
        print(f"Kalshi field names (first market): {', '.join(first)}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="DIDM daily collector (owner PC)")
    ap.add_argument("--env-file", metavar="PATH",
                    help="also read keys from this .env (e.g. the app folder's), never printed; "
                         "values already set in the environment win")
    ap.add_argument("--check-keys", action="store_true",
                    help="print which key names are set (True/False only) and exit")
    ap.add_argument("--data-dir")
    ap.add_argument("--no-gdelt", action="store_true")
    ap.add_argument("--finbert", action="store_true")
    ap.add_argument("--alfred", nargs="*", default=[])
    ap.add_argument("--alfred-file", action="append", default=[], metavar="SERIES=PATH")
    ap.add_argument("--edgar", nargs="*", default=[], metavar="CIK")
    ap.add_argument("--edgar-history", nargs="*", default=[], metavar="CIK",
                    help="D6: older filings too (filings.files), limited by --edgar-from/--edgar-to")
    ap.add_argument("--edgar-from", metavar="YYYY-MM-DD", help="earliest filing date for --edgar-history")
    ap.add_argument("--edgar-to", metavar="YYYY-MM-DD", help="latest filing date for --edgar-history")
    ap.add_argument("--edgar-max-files", type=int, default=10, help="older files per company (default 10)")
    ap.add_argument("--opendart", nargs=2, metavar=("BGN_YYYYMMDD", "END_YYYYMMDD"))
    ap.add_argument("--ecos", action="append", default=[], metavar="STAT,CYCLE,START,END[,ITEM...]")
    ap.add_argument("--kalshi", nargs="*", default=[], metavar="SERIES")
    ap.add_argument("--kalshi-history", nargs="*", default=[], metavar="SERIES",
                    help="D7: daily candles of open, closed and settled markets from --kalshi-from")
    ap.add_argument("--kalshi-from", metavar="YYYY-MM-DD", help="first day for --kalshi-history (required)")
    ap.add_argument("--kalshi-to", metavar="YYYY-MM-DD", help="last day for --kalshi-history (default now)")
    ap.add_argument("--kalshi-status", nargs="+", default=["settled", "closed", "open"],
                    choices=["open", "closed", "settled"])
    ap.add_argument("--kalshi-max-markets", type=int, default=200, help="markets per series (default 200)")
    ap.add_argument("--alphavantage", nargs="*", metavar="TICKER",
                    help="paid NEWS_SENTIMENT endpoint; held by the current data plan")
    ap.add_argument("--tiingo", nargs="*", metavar="TICKER", help="paid news access; held by the current data plan")
    ap.add_argument("--cryptopanic", nargs="*", metavar="CODE", help="paid API; held by the current data plan")
    ap.add_argument("--gdelt-day", metavar="YYYYMMDD", help="fetch all 96 fifteen-minute files of a UTC day")
    ap.add_argument("--gdelt-gkg", action="store_true", help="with --gdelt-day, also GKG files (large)")
    ap.add_argument("--ecos-probe", action="append", default=[], metavar="STAT,CYCLE,START,END[,ITEM]")
    ap.add_argument("--ecos-items", nargs="*", default=[], metavar="STAT_CODE",
                    help="list an ECOS table's item codes and cycles (no data stored)")
    args = ap.parse_args(argv)
    if args.env_file:
        load_env_file(args.env_file)
    if args.check_keys:
        for name, present in key_status().items():
            print(f"{name}: {present}")
        return 0
    if not args.data_dir:
        ap.error("--data-dir is required")
    with PointInTimeStore(_data_dir(args.data_dir) / "didm_store.sqlite") as store:
        rows: list[dict] = []
        if not args.no_gdelt:
            _, rows = collect_gdelt(store)
        if args.finbert:
            print(f"FinBERT baseline: {finbert_baseline(store, rows)}")
        if args.alfred:
            _run("ALFRED", lambda: collect_alfred_api(store, args.alfred))
        for spec in args.alfred_file:
            collect_alfred_file(store, spec)
        if args.edgar:
            _run("EDGAR", lambda: collect_edgar(store, args.edgar))
        if args.edgar_history:
            _run("EDGAR history", lambda: collect_edgar_history(store, args.edgar_history, args.edgar_from,
                                                                args.edgar_to, args.edgar_max_files))
        if args.opendart:
            _run("OpenDART", lambda: collect_opendart(store, *args.opendart))
        for spec in args.ecos:
            _run("ECOS", lambda spec=spec: collect_ecos(store, spec))
        if args.alphavantage is not None:
            _run("Alpha Vantage", lambda: collect_alphavantage(store, args.alphavantage))
        if args.tiingo is not None:
            _run("Tiingo", lambda: collect_tiingo(store, args.tiingo))
        if args.cryptopanic is not None:
            _run("CryptoPanic", lambda: collect_cryptopanic(store, args.cryptopanic))
        if args.gdelt_day:
            _run("GDELT day", lambda: collect_gdelt_day(store, args.gdelt_day, args.gdelt_gkg))
        for spec in args.ecos_probe:
            _run("ECOS probe", lambda spec=spec: probe_ecos(spec))
        for stat in args.ecos_items:
            _run("ECOS items", lambda stat=stat: show_ecos_items(stat))
        for series in args.kalshi:
            _run("Kalshi", lambda series=series: collect_kalshi(store, series))
        if args.kalshi_history:
            if not args.kalshi_from:
                ap.error("--kalshi-history needs --kalshi-from")
            _run("Kalshi history", lambda: collect_kalshi_history(
                store, args.kalshi_history, args.kalshi_from, args.kalshi_to, args.kalshi_status,
                args.kalshi_max_markets))
    print(gdelt_ingest.ATTRIBUTION)
    return 0


if __name__ == "__main__":
    sys.exit(main())
