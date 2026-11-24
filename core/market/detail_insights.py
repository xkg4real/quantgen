"""Stock-detail display contracts. Pure functions: no providers, credentials or I/O.

KIS field names follow official open-trading-api74b0a082. A documented field is
not evidence of a live response, a realtime feed, or permission to redistribute.
Financial ratios retain the provider basis; no ROE/PSR or peer data is invented.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
import math
import re
from statistics import mean as exact_mean

from core.market.models import Instrument

GROUPS = ("individual", "foreign", "institution")


def number(value, *, nonnegative=False, positive=False):
    if isinstance(value, bool):
        return None
    try:
        out = float(str(value).strip().replace(",", ""))
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(out) or (nonnegative and out < 0) or (positive and out <= 0):
        return None
    return out


def _map(value):
    return value if isinstance(value, Mapping) else {}


def _text(value, limit=120):
    if not isinstance(value, str):
        return ""
    value = value.strip()
    return value if len(value) <= limit and all(ord(c) >= 32 and c not in "<>" for c in value) else ""


def _day(value):
    try:
        return date.fromisoformat(str(value)).isoformat()
    except (ValueError, TypeError):
        return ""


def _received(value):
    text = _text(value, 40)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return text if parsed.tzinfo is not None else ""
    except ValueError:
        return ""


def _clock(value):
    # Preserve a clock only, never supply a missing market date or timezone.
    text = str(value or "").strip()
    if not re.fullmatch(r"\d{6}", text):
        return ""
    return text if int(text[:2]) < 24 and int(text[2:4]) < 60 and int(text[4:]) < 60 else ""


def normalize_orderbook(payload, *, received_at=""):
    """Validate up to10 paired depth levels; keep expected trades separate.

    Accept the provider response or our own normalized contract (for a supplied
    profile). Zero quantity is observed empty depth; a blank quantity is missing.
    """
    payload = _map(payload)
    normalized = payload.get("format") == "quantgen.stock-depth/1"
    raw = payload if normalized else _map(payload.get("output1"))
    levels = []
    supplied = payload.get("levels", ()) if normalized else ()
    supplied = supplied if isinstance(supplied, (tuple, list)) else ()
    for i in range(1, 11):
        row = _map(supplied[i - 1]) if normalized and i <= len(supplied) else {}
        level = {"level": i}
        for side, price_key, qty_key in (("ask", "askp", "askp_rsqn"), ("bid", "bidp", "bidp_rsqn")):
            price = number(row.get(side + "_price") if normalized else raw.get(price_key + str(i)), positive=True)
            qty = number(row.get(side + "_qty") if normalized else raw.get(qty_key + str(i)), nonnegative=True)
            # A price without its corresponding size is not an executable level.
            level[side + "_price"], level[side + "_qty"] = (price, qty) if price is not None and qty is not None else (None, None)
        levels.append(level)
    if not any(r["ask_price"] is not None or r["bid_price"] is not None for r in levels):
        return None
    expected = _map(payload.get("expected") if normalized else payload.get("output2"))
    return {
        "format": "quantgen.stock-depth/1", "source": "KIS", "kind": "REST snapshot",
        "levels": tuple(levels), "price_unit": "KRW", "quantity_unit": "shares",
        "total_ask_qty": number(raw.get("total_ask_qty" if normalized else "total_askp_rsqn"), nonnegative=True),
        "total_bid_qty": number(raw.get("total_bid_qty" if normalized else "total_bidp_rsqn"), nonnegative=True),
        "provider_time": _clock(raw.get("provider_time" if normalized else "aspr_acpt_hour")),
        "market_date": "", "received_at": _received(received_at or payload.get("received_at")),
        "expected": {"price": number(expected.get("price" if normalized else "antc_cnpr"), positive=True),
                     "volume": number(expected.get("volume" if normalized else "antc_vol"), nonnegative=True)},
    }


def normalize_executions(payload, *, received_at=""):
    """REST observations, preserving response order; no 'latest' or strength formula assumption."""
    payload = _map(payload)
    normalized = payload.get("format") == "quantgen.stock-executions/1"
    raw = payload.get("rows" if normalized else "output")
    if not isinstance(raw, (tuple, list)):
        return None
    rows = []
    for item in raw[:256]:
        row = _map(item)
        price = number(row.get("price" if normalized else "stck_prpr"), positive=True)
        volume = number(row.get("volume" if normalized else "cntg_vol"), nonnegative=True)
        strength = number(row.get("strength" if normalized else "tday_rltv"), nonnegative=True)
        if price is None or volume is None:
            continue
        rows.append({"price": price, "volume": volume, "strength": strength,
                     "provider_time": _clock(row.get("provider_time" if normalized else "stck_cntg_hour"))})
    if not rows:
        return None
    return {"format": "quantgen.stock-executions/1", "source": "KIS", "kind": "REST snapshot",
            "price_unit": "KRW", "quantity_unit": "shares", "strength_unit": "provider value",
            "market_date": "", "received_at": _received(received_at or payload.get("received_at")), "rows": tuple(rows)}


def peer_comparison(comparison):
    """An explicit, metadata-matched injected peer set only; never collect or infer membership."""
    value = _map(comparison)
    membership = _map(value.get("membership"))
    missing = {"status": "unavailable", "reason": "verified_peer_data_missing", "mean": None,
               "method": "arithmetic mean", "included": 0, "total": 0, "excluded": ()}
    members = membership.get("members")
    if (membership.get("verified") is not True or membership.get("kind") not in ("theme", "sector")
            or not all(_text(membership.get(k)) for k in ("id", "source", "proof"))
            or not _day(membership.get("as_of")) or not isinstance(members, (list, tuple))
            or not members or any(not _text(x, 40) for x in members) or len(set(members)) != len(members)):
        return missing
    metric = value.get("metric")
    if metric not in ("per", "pbr", "roe", "psr") or not all(_text(value.get(k)) for k in ("unit", "period", "basis")) or not _day(value.get("as_of")):
        return dict(missing, reason="comparison_basis_missing", total=len(members))
    if _day(membership["as_of"]) > _day(value["as_of"]):
        return dict(missing, reason="future_membership", total=len(members))
    rows = value.get("observations")
    if not isinstance(rows, (list, tuple)):
        return dict(missing, total=len(members))
    indexed = {}
    for row in rows:
        row = _map(row)
        member = row.get("member")
        if isinstance(member, str) and member in indexed:
            return dict(missing, reason="duplicate_peer", total=len(members))
        if isinstance(member, str):
            indexed[member] = row
    good, excluded = [], []
    for member in members:
        row = indexed.get(member, {})
        matched = all(row.get(k) == value.get(k) for k in ("metric", "unit", "period", "basis", "as_of"))
        n = number(row.get("value"))
        reason = "basis_mismatch" if not matched else "missing_value" if n is None else "nonpositive_multiple" if metric in ("per", "pbr", "psr") and n <= 0 else ""
        if not _text(row.get("source")):
            reason = "source_missing"
        if reason:
            excluded.append((member, reason))
        else:
            good.append(n)
    try:
        mean = math.fsum(n / len(good) for n in good) if good else None
    except OverflowError:
        # At the float limit each divided term may round up; the true mean is still finite.
        mean = exact_mean(good)
    available = len(good) >= 2 and mean is not None and math.isfinite(mean)
    return {"status": "available" if available else "unavailable", "reason": "" if available else "insufficient_comparable_peers",
            "mean": mean if available else None, "method": "arithmetic mean", "metric": metric,
            "unit": value["unit"], "period": value["period"], "basis": value["basis"], "as_of": value["as_of"],
            "kind": membership["kind"], "group_id": membership["id"], "membership_as_of": membership["as_of"],
            "source": membership["source"], "included": len(good), "total": len(members), "excluded": tuple(excluded)}


@dataclass(frozen=True)
class StockPeerComparisons:
    subject: Instrument
    as_of: str
    averages: tuple[dict, ...]


def _member_symbol(subject, symbol):
    """Require the same asset and an explicit venue for overseas stock identifiers."""
    if not isinstance(symbol, str):
        return False
    exchange, _, code = symbol.rpartition(":")
    if subject.asset == "domestic_stock" and exchange != subject.exchange:
        return False
    try:
        return Instrument(subject.asset, code, exchange).symbol == symbol
    except ValueError:
        return False


def stock_peer_comparisons(subject, today, snapshots):
    """Bind supplied averages to one instrument and one dated membership list.

    Each entry has the peer_comparison fields plus a subject Instrument. A missing
    ratio can leave other ratios available. Mixing groups, dates or duplicate
    ratio entries makes the supplied set ambiguous.
    """
    if (not isinstance(subject, Instrument) or subject.asset not in ("domestic_stock", "overseas_stock")
            or not _day(today) or not isinstance(snapshots, (list, tuple)) or not 1 <= len(snapshots) <= 4):
        return None
    scope, seen, averages = None, set(), []
    for raw in snapshots:
        entry = _map(raw)
        membership = _map(entry.get("membership"))
        members = membership.get("members")
        metric = entry.get("metric")
        as_of = _day(entry.get("as_of"))
        if (entry.get("subject") != subject or metric not in ("per", "pbr", "roe", "psr") or metric in seen
                or not as_of or as_of > _day(today) or _day(membership.get("as_of")) != as_of
                or not isinstance(members, (tuple, list)) or subject.symbol not in members
                or any(not _member_symbol(subject, member) for member in members)):
            return None
        seen.add(metric)
        member_set = frozenset(members)
        if len(member_set) != len(members):
            return None
        group = (membership.get("kind"), membership.get("id"), membership.get("source"),
                 membership.get("proof"), as_of, member_set)
        if scope is not None and group != scope:
            return None
        scope = group
        rows = entry.get("observations")
        if not isinstance(rows, (tuple, list)) or entry.get("unit") != ("%" if metric == "roe" else "x"):
            continue
        # Do not pool rows from a different universe, reporting basis or snapshot.
        if any(not isinstance(row, Mapping) or not isinstance(row.get("member"), str)
               or row["member"] not in member_set
               or any(row.get(key) != entry.get(key) for key in ("metric", "unit", "period", "basis", "as_of"))
               for row in rows):
            continue
        average = peer_comparison(entry)
        if average["status"] == "available":
            averages.append(average)
    return StockPeerComparisons(subject, as_of, tuple(averages)) if averages else None


def _flow_window(window, length, source, received):
    window = _map(window)
    start, end = _day(window.get("first_date")), _day(window.get("last_date"))
    rows = []
    for group in GROUPS:
        gross = _map(_map(window.get("gross")).get(group))
        buy, sell = number(gross.get("buy"), nonnegative=True), number(gross.get("sell"), nonnegative=True)
        count = gross.get("reported_pairs", 0)
        count = count if isinstance(count, int) and not isinstance(count, bool) and 0 <= count <= length else 0
        reported = _map(window.get("reported")).get(group, 0)
        reported = reported if isinstance(reported, int) and not isinstance(reported, bool) and 0 <= reported <= length else 0
        total = buy + sell if buy is not None and sell is not None else None
        paired = bool(start and end and start <= end and count > 0 and total is not None and math.isfinite(total) and total > 0)
        rows.append({"group": group, "net_qty": number(window.get(group)), "net_reported": reported,
                     "buy_qty": buy, "sell_qty": sell,
                     "buy_fraction": buy / total if paired else None, "sell_fraction": sell / total if paired else None,
                     "reported_pairs": count, "sessions": length, "first_date": start, "last_date": end,
                     "source": _text(source), "received_at": _received(received),
                     "reason": "" if paired else "gross_pair_or_denominator_missing"})
    return tuple(rows)


def _flow_daily(daily, length):
    """The profile's own daily net rows, (date, foreign, institution, individual), oldest first.

    Only the most recent `length` sessions (the longest summed window) are kept, so the
    daily bars and the window sums describe the same days. A blank value stays None;
    a row without a valid date is dropped rather than guessed.
    """
    if not isinstance(daily, (tuple, list)) or length <= 0:
        return ()
    rows = []
    for row in daily:
        if not isinstance(row, (tuple, list)) or len(row) != 1 + len(GROUPS_DAILY):
            continue
        day = _day(row[0])
        if not day:
            continue
        rows.append({"date": day, **{group: number(value)
                                     for group, value in zip(GROUPS_DAILY, row[1:])}})
    rows = rows[-length:]
    if not any(row[group] is not None for row in rows for group in GROUPS_DAILY):
        return ()
    return tuple(rows)


# The column order of stock_profile._flows "daily" rows.
GROUPS_DAILY = ("foreign", "institution", "individual")


def build_insights(profile, *, comparison=None):
    """Read the already-loaded profile only. Rendering this model cannot issue requests."""
    values = _map(getattr(profile, "values", None))
    reasons = _map(getattr(profile, "reasons", None))
    sources = _map(getattr(profile, "sources", None))
    fetched = _map(getattr(profile, "fetched", None))
    figures = _map(values.get("key_figures"))
    metrics = []
    for key in ("per", "pbr", "roe", "psr"):
        n = number(figures.get(key)) if key in ("per", "pbr") else None
        metrics.append({"key": key, "value": n, "unit": "x" if key in ("per", "pbr") else "",
                        "status": "available" if n is not None else "unavailable",
                        "reason": "" if n is not None else "not_connected" if key in ("roe", "psr") else reasons.get("fundamentals", "not_provided"),
                        "source": _text(sources.get("quote")), "received_at": _received(fetched.get("quote")),
                        "basis": "provider accounting/reference basis unconfirmed"})
    flow_data = _map(values.get("flows"))
    windows = _map(flow_data.get("windows"))
    lengths = [k for k in windows if isinstance(k, int) and not isinstance(k, bool) and k > 0]
    flow_windows = {length: _flow_window(windows[length], length, sources.get("flows"), fetched.get("flows"))
                    for length in sorted(lengths)}
    flows = flow_windows[max(lengths)] if lengths else _flow_window({}, 0, sources.get("flows"), fetched.get("flows"))
    flow_daily = _flow_daily(flow_data.get("daily"), max(lengths) if lengths else 0)
    short = _map(values.get("short_selling"))
    latest, average = _map(short.get("latest")), _map(short.get("average"))
    average = dict(average)
    average["short_qty"] = number(average.get("short_qty"), nonnegative=True)
    average["short_ratio_pct"] = number(average.get("short_ratio_pct"), nonnegative=True)
    if average["short_ratio_pct"] is not None and average["short_ratio_pct"] > 100:
        average["short_ratio_pct"] = None
    ratio = number(latest.get("short_ratio_pct"), nonnegative=True)
    ratio = ratio if ratio is not None and ratio <= 100 else None
    shorts = {"date": _day(latest.get("date")), "ratio_pct": ratio,
              "qty": number(latest.get("short_qty"), nonnegative=True), "average": dict(average),
              "source": _text(sources.get("short_selling")), "received_at": _received(fetched.get("short_selling"))}
    instrument, today = getattr(profile, "instrument", None), getattr(profile, "today", None)
    peers = (stock_peer_comparisons(instrument, today, (comparison,)) if comparison is not None
             else getattr(profile, "peer_comparisons", None))
    comparisons = {}
    if isinstance(peers, StockPeerComparisons) and peers.subject == instrument and peers.as_of <= _day(today):
        comparisons = {item["metric"]: dict(item) for item in peers.averages}
    last_price = number(getattr(profile, "last_price", None), positive=True)
    return {"metrics": tuple(metrics), "flows": tuple(flows), "flow_windows": flow_windows,
            "flow_daily": flow_daily, "last_price": last_price, "shorts": shorts,
            "orderbook": normalize_orderbook(values.get("orderbook")),
            "executions": normalize_executions(values.get("executions")),
            "comparisons": comparisons, "comparison": next(iter(comparisons.values())) if len(comparisons) == 1 else peer_comparison(None),
            "reasons": dict(reasons), "snapshot": True}
