"""DIDM daily collector (DS-4a). Runs on the owner's PC, not in CI or the cloud.

    python -m tools.didm.collect_daily --data-dir <folder outside the repository> [--finbert]
    python -m tools.didm.collect_daily --data-dir <folder> --alfred CPIAUCSL PAYEMS
    python -I -m tools.didm.collect_daily --data-dir <folder> --alfred-file CPIAUCSL=<downloaded .xlsx>
    python -m tools.didm.collect_daily --data-dir <folder> --no-gdelt --edgar 320193 --opendart 20261117 20261118 \
        --ecos "722Y001,M,202401,202610,0101000" --kalshi KXFED

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
from datetime import datetime, timezone
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
             "ALPHAVANTAGE_API_KEY", "TIINGO_API_KEY", "CRYPTOPANIC_API_KEY",
             "ALPACA_API_KEY_ID", "ALPACA_API_SECRET_KEY", "MASSIVE_API_KEY")


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


def collect_alpaca_news(store: PointInTimeStore, symbols: list[str], start: str | None, end: str | None,
                        max_pages: int, fetch=None) -> dict:
    """DS-5b: Alpaca News pages oldest first, until no next token or ``max_pages``. Receipt = after each page."""
    from core.didm.ingest import alpaca_news
    from core.didm.ingest import news_store
    if fetch is None:
        from data.didm import alpaca_news as alpaca_http
        fetch = alpaca_http.fetch_page
    token, seen, pages, articles, added, first, last = None, (), 0, 0, 0, None, None
    while pages < max_pages:
        payload = fetch(symbols or None, start=start, end=end, limit=50, page_token=token)
        page = alpaca_news.parse_page(payload, _now(), limit=50, current_token=token, seen_tokens=seen)
        rows = news_store.alpaca_rows(page.articles)
        added += store.append_many(rows)
        pages, articles = pages + 1, articles + len(rows)
        for r in rows:
            d = r["published_at"].date().isoformat()
            first, last = min(first or d, d), max(last or d, d)
        if page.next_page_token is None:
            token = None
            break
        seen = seen + ((token,) if token is not None else ())
        token = page.next_page_token
    complete = token is None
    print(f"Alpaca news {','.join(symbols) or 'all'}: pages {pages} (complete {complete}), articles {articles}, "
          f"first {first or '-'}, last {last or '-'}, new {added}")
    return {"pages": pages, "articles": articles, "added": added, "first": first, "last": last}


def collect_massive_news(store: PointInTimeStore, ticker: str | None, start: str | None, max_pages: int,
                         fetch=None) -> dict:
    """DS-5c: Massive ticker news, oldest first, following next_url cursors (free plan: spaced 12.5 s)."""
    from core.didm.ingest import news_store
    from data.didm import massive_news
    fetch = fetch or massive_news.fetch_page
    cursor, seen, pages, articles, added, insights, first, last = None, [], 0, 0, 0, 0, None, None
    while pages < max_pages:
        payload = fetch(ticker, published_gte=start, cursor=cursor)
        page = massive_news.parse_page(payload, _now(), seen_cursors=seen)
        rows = news_store.massive_rows(page.articles)
        added += store.append_many(rows)
        pages, articles = pages + 1, articles + len(rows)
        insights += sum(1 for r in rows if r["payload"]["has_insights"])
        for r in rows:
            d = r["published_at"].date().isoformat()
            first, last = min(first or d, d), max(last or d, d)
        if page.next_cursor is None:
            cursor = None
            break
        if cursor is not None:
            seen.append(cursor)
        cursor = page.next_cursor
    complete = cursor is None
    print(f"Massive news {ticker or 'all'}: pages {pages} (complete {complete}), articles {articles}, "
          f"with insights {insights}, first {first or '-'}, last {last or '-'}, new {added}")
    return {"pages": pages, "articles": articles, "added": added, "insights": insights}


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
    ap.add_argument("--opendart", nargs=2, metavar=("BGN_YYYYMMDD", "END_YYYYMMDD"))
    ap.add_argument("--ecos", action="append", default=[], metavar="STAT,CYCLE,START,END[,ITEM...]")
    ap.add_argument("--kalshi", nargs="*", default=[], metavar="SERIES")
    ap.add_argument("--alphavantage", nargs="*", metavar="TICKER",
                    help="paid NEWS_SENTIMENT endpoint; held by the current data plan")
    ap.add_argument("--tiingo", nargs="*", metavar="TICKER", help="paid news access; held by the current data plan")
    ap.add_argument("--cryptopanic", nargs="*", metavar="CODE", help="paid API; held by the current data plan")
    ap.add_argument("--alpaca-news", nargs="*", metavar="SYMBOL", help="DS-5b Alpaca News (key id + secret)")
    ap.add_argument("--massive-news", nargs="*", metavar="TICKER", help="DS-5c Massive ticker news (free: 5/min)")
    ap.add_argument("--news-start", metavar="YYYY-MM-DD", help="oldest article date for --alpaca-news/--massive-news")
    ap.add_argument("--news-end", metavar="YYYY-MM-DD", help="newest article date for --alpaca-news")
    ap.add_argument("--news-max-pages", type=int, default=5, help="page cap per source/ticker (default 5)")
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
        if args.alpaca_news is not None:
            _run("Alpaca news", lambda: collect_alpaca_news(store, args.alpaca_news, args.news_start, args.news_end,
                                                            args.news_max_pages))
        if args.massive_news is not None:
            for ticker in args.massive_news or [None]:
                _run("Massive news", lambda ticker=ticker: collect_massive_news(store, ticker, args.news_start,
                                                                                args.news_max_pages))
        for series in args.kalshi:
            _run("Kalshi", lambda series=series: collect_kalshi(store, series))
    print(gdelt_ingest.ATTRIBUTION)
    return 0


if __name__ == "__main__":
    sys.exit(main())
