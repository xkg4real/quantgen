"""One symbol directory for every chart and symbol search: type a code or a name.

Domestic and overseas stock listings are searched together by code, Korean name,
English name or Korean initial consonants (초성). Nothing is read, built or
downloaded when this module is imported:

* Overseas: the 126 bundled rows of ``core/market/data/overseas_symbols.json``
  (through ``core.market.symbols``, whose own API is unchanged).
* Domestic seed, always available offline: the six Home stocks of
  ``core.research.watchlist.KR_STOCK_SPECS`` with the English names the native
  Home table shows (``quantgen_desktop/watchlist.py`` ``_NAMES``).
* Domestic full list, only when a caller runs ``load_domestic()``: the keyless KIS
  stock masters ``kospi_code.mst.zip`` and ``kosdaq_code.mst.zip`` fetched by
  ``data.kis_markets.load_master`` from the same host as the other KIS masters.
  They are parsed and kept in process memory only; no file is written.

``search()`` never touches the network. ``load_domestic()`` is the only blocking
call; run it on a worker thread. It swaps the new rows in with one assignment of
an immutable index, so ``search()`` on the UI thread always sees either the old
or the new list, never half of one.
"""
from __future__ import annotations

from bisect import bisect_left, bisect_right
from dataclasses import dataclass
import heapq
import re
import threading
import unicodedata

from core.search_text import initials, is_initials, normal

__all__ = ("Listing", "SymbolDirectory", "default_directory")

ASSETS = ("domestic_stock", "overseas_stock")
KINDS = ("stock", "etf", "etn", "reit", "other")
DOMESTIC_MASTERS = ("kospi_code", "kosdaq_code")

# English names as the native Home table shows them (quantgen_desktop/watchlist.py
# _NAMES). That module imports Qt, so the six names are repeated here and a test
# keeps the two tables equal.
_SEED_EN = {
    "005930": "Samsung Electronics",
    "000660": "SK hynix",
    "005380": "Hyundai Motor",
    "105560": "KB Financial",
    "373220": "LG Energy Solution",
    "207940": "Samsung Biologics",
}

# Bundled overseas rows carry no security type. ETFs are the names with an "ETF"
# word; these two are not named that way.
_OVERSEAS_KINDS = {("AMS", "GLD"): "etf", ("NYS", "O"): "reit"}

_HANGUL = re.compile(r"[\u1100-\u11ff\u3130-\u318f\ua960-\ua97f\uac00-\ud7a3\ud7b0-\ud7ff]")
_DOMESTIC_CODE = re.compile(r"A?(\d{1,6})(?:\.(?:KS|KQ))?")
_SEP = "\x00"           # field separator inside the search haystack; removed from queries
_MAX_QUERY = 100


@dataclass(frozen=True)
class Listing:
    asset: str          # 'domestic_stock' or 'overseas_stock'
    code: str           # domestic: 6-digit code like '005930'; overseas: e.g. 'AAPL'
    exchange: str       # '' for domestic; 'NAS','NYS','AMS','HKS','TSE' for overseas
    name_ko: str
    name_en: str        # may be '' (the KIS stock master has no English names)
    kind: str           # 'stock','etf','etn','reit','other'

    def __post_init__(self):
        if self.asset not in ASSETS:
            raise ValueError("Unsupported listing asset")
        if self.kind not in KINDS:
            raise ValueError("Unsupported listing kind")

    def label(self, lang: str) -> str:
        """Korean name for 'ko' (else English, else code); English name or code otherwise.

        Any language other than Korean gets no Hangul: an English name that holds
        Hangul falls back to the code.
        """
        if str(lang or "").lower().startswith("ko"):
            return self.name_ko or self.name_en or self.code
        name = self.name_en
        return name if name and not _HANGUL.search(name) else self.code


# --------------------------------------------------------------------------- #
# KIS stock master (kospi_code.mst / kosdaq_code.mst)
# --------------------------------------------------------------------------- #
# UNVERIFIED LAYOUT. The real files could not be downloaded where this was
# written (the proxy answers 403 for the KIS download host). The layout follows
# KIS's published sample readers (open-trading-api stocks_info
# kis_kospi_code_mst.py / kis_kosdaq_code_mst.py) as remembered: CP949 text, one
# issue per line; the samples read each line with its line break and split off
# ``row[-228:]`` (KOSPI) or ``row[-222:]`` (KOSDAQ) as fixed-width fields whose
# first 2 characters are the group code (ST stock, EF ETF, EN ETN, RT REIT, ...).
# The leading part is the short code (9 characters, stripped), the standard code
# (12 characters) and the Korean name (the rest, stripped).
#
# Because the samples count the line break, the tail of a line without it is one
# character shorter. The parser accepts both widths and picks the one whose
# first two characters are a known KIS group code, so it does not depend on
# which reading is right. Malformed lines are skipped and counted; nothing raises.
_TAIL = {"kospi_code": 228, "kosdaq_code": 222}
_GROUP_KINDS = {"ST": "stock", "EF": "etf", "EN": "etn", "RT": "reit"}
_KNOWN_GROUPS = frozenset(("ST", "MF", "RT", "SC", "IF", "DR", "EW", "EF", "SW", "SR",
                           "BC", "FE", "FS", "EN"))
_FRONT = 21             # short code (9) + standard code (12)


def _tail_start(line: str, tail: int):
    """Index where the fixed-width fields start, or None when no width fits."""
    picked = None
    for width in (tail - 1, tail):
        start = len(line) - width
        if start <= _FRONT:
            continue
        group = line[start:start + 2]
        if not (group.isascii() and group.isalpha() and group.isupper()):
            continue
        if not line[start:].isascii():
            continue
        if group in _KNOWN_GROUPS:
            return start
        if picked is None:
            picked = start
    return picked


def _parse_stock_master(text, tail: int):
    """(listings, counts) from one decoded master; skips and counts bad lines."""
    counts = {"lines": 0, "listings": 0, "malformed": 0, "non_numeric_code": 0, "duplicate": 0}
    if isinstance(text, (list, tuple)):
        text = "\n".join(str(line) for line in text)
    if not isinstance(text, str):
        return [], counts
    listings, seen = [], set()
    for line in text.splitlines():
        if not line.strip():
            continue
        counts["lines"] += 1
        start = _tail_start(line, tail)
        if start is None:
            counts["malformed"] += 1
            continue
        short, standard = line[0:9].strip(), line[9:_FRONT].strip()
        name = re.sub(r"\s+", " ", unicodedata.normalize("NFC", line[_FRONT:start])).strip()
        if not name or chr(0xFFFD) in name or not name.isprintable():  # a CP949 decoding failure
            counts["malformed"] += 1
            continue
        if not (short.isascii() and short.isalnum() and standard.isascii() and standard.isalnum()):
            counts["malformed"] += 1
            continue
        if not (len(short) == 6 and short.isdigit()):
            # e.g. letter-containing short codes; core/market/models.py:34 takes digits only.
            counts["non_numeric_code"] += 1
            continue
        if short in seen:
            counts["duplicate"] += 1
            continue
        seen.add(short)
        kind = _GROUP_KINDS.get(line[start:start + 2], "other")
        listings.append(Listing("domestic_stock", short, "", name, "", kind))
    counts["listings"] = len(listings)
    return listings, counts


def _kis_master_text(name: str) -> str:
    """Default loader: the existing keyless KIS master download, held in memory."""
    from data import kis_markets          # imported here so importing this module loads nothing
    return "\n".join(kis_markets.load_master(name))


def _reason(name: str, exc: BaseException) -> str:
    detail = type(exc).__name__
    status = re.search(r"HTTP (\d{3})", str(exc))
    if status:
        detail += f" HTTP {status.group(1)}"
    return f"{name}: {detail}"[:80]


# --------------------------------------------------------------------------- #
# Search index
# --------------------------------------------------------------------------- #
class _Row:
    __slots__ = ("listing", "code", "names", "inits", "full", "kind_rank", "domestic")

    def __init__(self, listing: Listing, aliases=()):
        def norm(text):
            return normal(text).replace(_SEP, "")

        self.listing = listing
        self.code = norm(listing.code)
        self.domestic = listing.asset == "domestic_stock"
        self.kind_rank = KINDS.index(listing.kind)
        full = []
        for text in (listing.name_ko, listing.name_en, *aliases):
            value = norm(text)
            if value and value not in full:
                full.append(value)
        self.full = tuple(full)             # whole names: the exact-name rank and resolve()
        names = list(full)
        if not self.domestic:
            # The bundled overseas Korean names are lists of alternative names
            # ('알파벳 A 구글', '메타 페이스북'), so each word also counts for the
            # prefix ranks, as core.market.symbols.search treats them. A word of a
            # KIS name ('삼성' in '삼성 레버리지 WTI원유 선물 ETN') is not a name of
            # that issue: it matches as a substring only.
            for word in listing.name_ko.split():
                value = norm(word)
                if value and value not in names:
                    names.append(value)
        inits = []
        for value in names:
            jamo = initials(value)
            if jamo != value and jamo not in inits:
                inits.append(jamo)
        # Every field starts with _SEP, so _SEP + query finds prefixes.
        self.names = _SEP + _SEP.join(names) + _SEP if names else ""
        self.inits = _SEP + _SEP.join(inits) + _SEP if inits else ""


class _Hay:
    """One string holding a field of every row, for C-speed substring search."""
    __slots__ = ("text", "starts", "ids")

    def __init__(self, parts):
        texts, starts, ids, offset = [], [], [], 0
        for i, segment in parts:
            if segment:
                starts.append(offset)
                ids.append(i)
                texts.append(segment)
                offset += len(segment)
        self.text, self.starts, self.ids = "".join(texts), starts, ids

    def find(self, needle: str) -> list:
        """Row ids whose segment contains ``needle`` (which never holds _SEP)."""
        text, starts, ids = self.text, self.starts, self.ids
        last, out = len(starts) - 1, []
        pos = text.find(needle)
        while pos >= 0:
            j = bisect_right(starts, pos) - 1
            out.append(ids[j])
            pos = text.find(needle, starts[j + 1]) if j < last else -1
        return out


_ID_BITS = 40
_ID_MASK = (1 << _ID_BITS) - 1


class _Index:
    """Immutable search tables; a load builds a new one and swaps it in whole."""
    __slots__ = ("rows", "keys_latin", "keys_hangul", "by_code", "by_name",
                 "codes", "names", "code_text", "inits", "domestic_count")

    def __init__(self, rows):
        self.rows = tuple(rows)
        keys_latin, keys_hangul = [], []
        by_code, by_name = {}, {}
        per_asset = {asset: [] for asset in ASSETS}
        for i, row in enumerate(self.rows):
            # Tie order as one integer: kind, then asset (by query script), then list order.
            kind = row.kind_rank << (_ID_BITS + 1)
            keys_hangul.append(kind | ((0 if row.domestic else 1) << _ID_BITS) | i)
            keys_latin.append(kind | ((1 if row.domestic else 0) << _ID_BITS) | i)
            by_code.setdefault(row.code, []).append(i)
            for name in row.full:
                by_name.setdefault(name, []).append(i)
            per_asset[row.listing.asset].append((row.code, i))
        self.keys_latin, self.keys_hangul = keys_latin, keys_hangul
        self.by_code = {key: tuple(value) for key, value in by_code.items()}
        self.by_name = {key: tuple(value) for key, value in by_name.items()}
        # Codes sorted per asset, with tie keys aligned, so a code prefix is one bisect.
        self.codes = {}
        for asset, pairs in per_asset.items():
            pairs.sort()
            self.codes[asset] = (tuple(code for code, _ in pairs),
                                 tuple(keys_latin[i] for _, i in pairs),
                                 tuple(keys_hangul[i] for _, i in pairs))
        self.names = _Hay((i, row.names) for i, row in enumerate(self.rows))
        self.code_text = _Hay((i, _SEP + row.code) for i, row in enumerate(self.rows))
        self.inits = _Hay((i, row.inits) for i, row in enumerate(self.rows))
        self.domestic_count = sum(1 for row in self.rows if row.domestic)


class _Query:
    __slots__ = ("wanted", "padded", "jamo", "hangul")

    def __init__(self, text):
        text = unicodedata.normalize("NFC", "" if text is None else str(text))[:_MAX_QUERY]
        self.wanted = normal(text).replace(_SEP, "")
        compact = re.sub(r"\s+", "", text).upper()
        match = _DOMESTIC_CODE.fullmatch(compact)
        self.padded = match.group(1).zfill(6) if match else None
        self.jamo = is_initials(self.wanted)
        self.hangul = bool(_HANGUL.search(text))


def _allowed(assets):
    if assets is None:
        return None
    if isinstance(assets, str):
        return frozenset((assets,))
    try:
        return frozenset(str(asset) for asset in assets)
    except TypeError:
        return frozenset()


def _overseas_listings():
    from core.market import symbols
    out = []
    for entry in symbols.entries():
        kind = _OVERSEAS_KINDS.get((entry.exchange, entry.code))
        if kind is None:
            words = f"{entry.name_en} {entry.name_ko}".upper().split()
            kind = "etf" if "ETF" in words else "stock"
        out.append(Listing("overseas_stock", entry.code, entry.exchange,
                           entry.name_ko, entry.name_en, kind))
    return out


def _seed():
    """[(listing, aliases)] for the six Home stocks, in Home order."""
    from core.research.watchlist import KR_STOCK_SPECS
    out = []
    for name_ko, code, english in KR_STOCK_SPECS:
        name_en = _SEED_EN.get(code, english)
        aliases = (english,) if english != name_en else ()
        out.append((Listing("domestic_stock", code, "", name_ko, name_en, "stock"), aliases))
    return out


class SymbolDirectory:
    """Code-or-name search over domestic and overseas stock listings.

    Ranking, after normalising the query (NFC, case-fold, separators removed;
    'A005930', '005930.KS', '005930.KQ' and '5930' all mean domestic '005930'):
    exact code, exact name (a whole Korean or English name, the same names
    ``resolve()`` takes), name prefix, code prefix, substring of 2+ characters,
    초성 prefix, 초성 substring. Prefixes are of whole names, except that each
    word of a bundled overseas Korean name (a list of alternative names such as
    '알파벳 A 구글') also counts as a name prefix and 초성 prefix; a word inside a
    domestic name matches as a substring only. Ties: stock < ETF < ETN < REIT < other, then domestic
    first when the query holds Hangul and overseas first otherwise, then list
    order (the six Home stocks first, then KOSPI and KOSDAQ master order; the
    bundled overseas order).
    """

    def __init__(self, *, master_loader=None):
        self._loader = master_loader or _kis_master_text
        self._load_lock = threading.Lock()
        self._seed_rows = tuple(_Row(listing, aliases) for listing, aliases in _seed())
        self._overseas_rows = tuple(_Row(listing) for listing in _overseas_listings())
        self._index = _Index(self._seed_rows + self._overseas_rows)
        self._domestic_loaded = False
        self._counts = {}
        self.error: str | None = None

    @property
    def domestic_loaded(self) -> bool:
        return self._domestic_loaded

    # ------------------------------------------------------------------ search
    def search(self, query: str, *, limit: int = 8, assets=None) -> list[Listing]:
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            return []
        q = _Query(query)
        if limit <= 0 or not q.wanted:
            return []
        index, allowed = self._index, _allowed(assets)
        rows, wanted = index.rows, q.wanted
        keys = index.keys_hangul if q.hangul else index.keys_latin
        results, seen = [], set()

        def take(ids):
            """Append one rank bucket in tie order; True once the limit is filled."""
            fresh = {i for i in ids if i not in seen
                     and (allowed is None or rows[i].listing.asset in allowed)}
            for i in sorted(fresh, key=keys.__getitem__)[:limit - len(results)]:
                results.append(rows[i].listing)
                seen.add(i)
            return len(results) >= limit

        def code_prefix():
            # At most len(seen) rows of a range were taken already, and
            # len(seen) + (limit - len(results)) == limit, so `limit` per asset is enough.
            best = []
            for asset, (codes, latin, hangul) in index.codes.items():
                if allowed is None or asset in allowed:
                    lo, hi = bisect_left(codes, wanted), bisect_left(codes, wanted + "\U0010ffff")
                    best.extend(heapq.nsmallest(limit, (hangul if q.hangul else latin)[lo:hi]))
            return [key & _ID_MASK for key in best]

        exact = list(index.by_code.get(wanted, ()))
        if q.padded is not None:
            exact.extend(i for i in index.by_code.get(q.padded, ()) if rows[i].domestic)
        long = len(wanted) >= 2
        stages = (
            lambda: exact,                                                       # exact code
            lambda: index.by_name.get(wanted, ()),                               # exact name
            lambda: index.names.find(_SEP + wanted),                             # name prefix
            code_prefix,                                                         # code prefix
            lambda: (index.names.find(wanted) + index.code_text.find(wanted)) if long else (),
                                                                                 # substring (2+)
            lambda: index.inits.find(_SEP + wanted) if q.jamo else (),           # 초성 prefix
            lambda: index.inits.find(wanted) if q.jamo and long else (),         # 초성 substring
        )
        for stage in stages:        # buckets in rank order; stop once the limit is filled
            if take(stage()):
                break
        return results

    def resolve(self, text: str, *, assets=None) -> Listing | None:
        """The one listing ``text`` names exactly, or None when none or several do.

        An exact normalised code wins (a code typed as written before a
        zero-padded domestic reading of it); otherwise exactly one listing must
        carry the whole Korean or English name. A single word of a name never
        resolves (it would turn 'A' into Alphabet Class A).
        """
        q = _Query(text)
        if not q.wanted:
            return None
        index, allowed = self._index, _allowed(assets)

        def pick(ids, domestic_only=False):
            return [index.rows[i] for i in ids
                    if (allowed is None or index.rows[i].listing.asset in allowed)
                    and (not domestic_only or index.rows[i].domestic)]

        for found in (pick(index.by_code.get(q.wanted, ())),
                      pick(index.by_code.get(q.padded, ()), True) if q.padded else []):
            if found:
                return found[0].listing if len(found) == 1 else None
        found = pick(index.by_name.get(q.wanted, ()))
        return found[0].listing if len(found) == 1 else None

    def lookup(self, asset: str, code: str, exchange: str = "") -> Listing | None:
        """The listing with this asset and code; the exchange narrows overseas codes.

        Domestic codes are normalised like queries ('5930' -> '005930'); a
        domestic exchange argument is ignored.
        """
        index = self._index
        if asset == "domestic_stock":
            match = _DOMESTIC_CODE.fullmatch(re.sub(r"\s+", "", str(code or "")).upper())
            key = match.group(1).zfill(6) if match else None
            wanted_exchange = ""
        else:
            key = normal(str(code or "")).replace(_SEP, "")
            wanted_exchange = str(exchange or "").strip().upper()
        for i in index.by_code.get(key, ()) if key else ():
            listing = index.rows[i].listing
            if listing.asset == asset and (not wanted_exchange or listing.exchange == wanted_exchange):
                return listing
        return None

    # ------------------------------------------------------------------ loading
    def load_domestic(self) -> int:
        """BLOCKING network: fetch, parse and swap in the KOSPI and KOSDAQ masters.

        Returns how many listings the swap added to the directory (the six seed
        stocks found in a master are merged, not added again); 0 on failure.
        Never raises: a failure sets ``error`` to a short reason (no URL, no
        provider text) and keeps the current listings, seed included. Both
        masters must load, or neither is used. Safe to call from a worker thread
        while ``search()`` runs on the UI thread.
        """
        with self._load_lock:
            try:
                return self._load()
            except Exception as exc:          # never raise into a worker thread
                self.error = _reason("directory", exc)
                return 0

    def _load(self) -> int:
        master, counts = [], {}
        seen = set()
        for name in DOMESTIC_MASTERS:
            try:
                text = self._loader(name)
            except Exception as exc:
                self.error = _reason(name, exc)
                return 0
            listings, counts[name] = _parse_stock_master(text, _TAIL[name])
            if not listings:
                self.error = f"{name}: no listings parsed"
                return 0
            for listing in listings:
                if listing.code in seen:
                    counts[name]["duplicate"] += 1
                    continue
                seen.add(listing.code)
                master.append(listing)
        # Seed stocks keep the names Home shows; the master adds its kind and, when it
        # differs, its own Korean name as a search alias.
        by_code = {listing.code: listing for listing in master}
        seed_codes, rows = set(), []
        for seed in self._seed_rows:
            listing = seed.listing
            seed_codes.add(listing.code)
            found = by_code.get(listing.code)
            if found is None:
                rows.append(seed)
                continue
            aliases = seed.full + ((found.name_ko,) if normal(found.name_ko) not in seed.full else ())
            rows.append(_Row(Listing("domestic_stock", listing.code, "", listing.name_ko,
                                     listing.name_en, found.kind), aliases))
        rows.extend(_Row(listing) for listing in master if listing.code not in seed_codes)
        before = self._index.domestic_count
        index = _Index(rows + list(self._overseas_rows))
        self._index = index                    # one assignment: readers see old or new
        self._counts = counts
        self._domestic_loaded = True
        self.error = None
        return max(0, index.domestic_count - before)


_DEFAULT: SymbolDirectory | None = None
_DEFAULT_LOCK = threading.Lock()


def default_directory() -> SymbolDirectory:
    """The process-wide directory (built on first call; masters load only on request)."""
    global _DEFAULT
    with _DEFAULT_LOCK:
        if _DEFAULT is None:
            _DEFAULT = SymbolDirectory()
        return _DEFAULT
