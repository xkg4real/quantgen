"""Market pages and their search criteria for the native Markets page (owner ruling UI-D10, 2026-11-11).

Owner: "저거 시장 있지. 시장에서 그냥 국장 미장 코인 이런걸 하부ui로 두고, 너가 지금 하부ui로 깔아놓은건 해당 시장의
하부ui 선택하고 차후에 검색기준으로 저걸 쓸수있게 구현하면 좋을 거 같은데, 공간 잘써서 센스있게해봐".

So the rail lists markets (`PAGES`: 국내 주식, 미국 주식, 코인) and each market's page ranks its own list by one of
`rankings.CATEGORIES`, the old sub-menu. The categories double as search criteria: a `Screen` is one market's
list as the user narrowed it, combining

* the ranking category (how the list is ordered: trading value, volume, top gainers, top losers, market cap),
* a sub-market (`SUBS`: 코스피/코스닥 for 국내, the exchange for 미국; none for coins),
* a sector (`rankings.SECTORS`, where the market's universe has them; none for coins),
* typed text (`matches_text`: name in either language, code, initial consonants, the sector's name, and a
  member's other names), so "반도체" with 급상승 lists that market's semiconductor names ranked by their rise,
* beginner conditions (`CONDITIONS`): 등락률 range, 거래대금 at least, 시가총액 at least.

Criteria are data: a new condition is one more `Condition` in `CONDITIONS` (its figure, kind, unit, the pages
that have the figure and, for a minimum, the thresholds offered); the page builds its controls from that
table, so adding one needs no UI rewrite. A category a market cannot rank (`category_note`) says why instead
of ranking nothing silently: coins have no unit count worth comparing and no market cap in any source the app
uses (`rankings` module docstring).

A stock whose figure is missing never passes a condition on that figure (unknown is not "at least").
Pure: no Qt, no network, nothing read on import.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
import math

from core.market import rankings as R
from core.search_text import best_score, normal

__all__ = ("PAGES", "PAGE_KEYS", "SUBS", "CONDITIONS", "CONDITION_KEYS", "Condition", "Screen", "condition",
           "category_note", "page_text", "sub_text", "matches_text", "threshold_text", "CATEGORY_NOTES")

# (key, English, Korean): the rail's Markets sub-items, in this order (owner ruling R-D10-1).
PAGES = (("kr", "Korean stocks", "국내 주식"), ("us", "US stocks", "미국 주식"), ("crypto", "Crypto", "코인"))
PAGE_KEYS = tuple(key for key, _en, _ko in PAGES)
# Sub-market filter of each page: '' is the whole market. US exchanges are the KIS codes the universe carries.
SUBS = {"kr": (("", "All", "전체"), ("kospi", "KOSPI", "코스피"), ("kosdaq", "KOSDAQ", "코스닥")),
        "us": (("", "All", "전체"), ("NAS", "NASDAQ", "나스닥"), ("NYS", "NYSE", "NYSE")),
        "crypto": ()}
# Why a market cannot rank by a category (English; the Korean is in quantgen_desktop/owner_ui_language/market.py).
# The page disables that chip and gives this as its tooltip.
CATEGORY_NOTES = {
    ("crypto", "volume"): "Coins are not ranked by units traded: one coin is worth very different amounts from "
                          "another. See trading value.",
    ("crypto", "cap"): "No source this app uses states coin market cap, so coins are not ranked by it.",
}


def page_text(page, language):
    return R.text(PAGES, page, language)


def sub_text(page, sub, language):
    return R.text(SUBS[page], sub, language)


def category_note(page, category):
    """Why `page` cannot rank by `category` (English source text), or '' when it can."""
    return CATEGORY_NOTES.get((page, category), "")


def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def threshold_text(value, unit, page, language):
    """'1,000억', '10조', '$1B', '+3%': a condition's bound as a person reads it."""
    if unit == "pct":
        if value == 0:
            return "0%"
        return f"{value:+g}%".replace("-", "−")
    v = float(value)
    if unit == "money" and page == "kr":
        if language == "ko":
            return f"{v / 1e12:g}조" if v >= 1e12 else f"{v / 1e8:,.0f}억"
        return f"₩{v / 1e12:g}T" if v >= 1e12 else f"₩{v / 1e9:g}B"
    for step, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M")):
        if v >= step:
            return f"${v / step:g}{suffix}"
    return f"${v:,.0f}"


@dataclass(frozen=True)
class Condition:
    """One beginner filter on a record's figure.

    kind 'range': a low and/or high bound, typed by the user (등락률 −3% ~ +5%); kind 'min': at least one of
    `steps[page]` (거래대금 1,000억 이상). `pages` are the markets whose records carry the figure.
    """
    key: str
    en: str
    ko: str
    kind: str
    unit: str
    figure: object
    pages: tuple = PAGE_KEYS
    steps: dict = field(default_factory=dict)

    def label(self, language):
        return self.ko if language == "ko" else self.en

    def available(self, page):
        return page in self.pages

    def value(self, record):
        value = self.figure(record)
        return float(value) if _finite(value) else None

    def holds(self, record, low=None, high=None):
        value = self.value(record)
        if value is None:
            return False
        return (low is None or value >= low) and (high is None or value <= high)


CONDITIONS = (
    Condition("change", "Change", "등락률", "range", "pct", lambda r: r.change_pct),
    Condition("value", "Trading value", "거래대금", "min", "money", lambda r: r.trading_value,
              steps={"kr": (1e10, 5e10, 1e11, 5e11), "us": (1e8, 5e8, 1e9, 5e9), "crypto": (1e8, 1e9, 1e10)}),
    Condition("cap", "Market cap", "시가총액", "min", "money", lambda r: r.market_cap, pages=("kr", "us"),
              steps={"kr": (1e12, 1e13, 5e13, 1e14), "us": (1e10, 1e11, 5e11, 1e12)}),
)
CONDITION_KEYS = tuple(c.key for c in CONDITIONS)


def condition(key):
    for item in CONDITIONS:
        if item.key == key:
            return item
    raise KeyError(key)


def matches_text(member, text):
    """Whether typed text names the member: its name in either language, code, initial consonants, its sector's
    name ('반도체') or another name it is known by."""
    wanted = normal(text)
    if not wanted:
        return True
    candidates = [member.name_ko, member.name_en, member.code, *member.aliases]
    if member.sector:
        candidates += [R.text(R.SECTORS, member.sector, "ko"), R.text(R.SECTORS, member.sector, "en")]
    return best_score(wanted, candidates) is not None


@dataclass(frozen=True)
class Screen:
    """One market's list as the user narrowed it; `apply` ranks a batch's records by it.

    `limits` holds (condition key, low, high) in `CONDITIONS` order, one per condition.
    """
    page: str = "kr"
    category: str = "value"
    sub: str = ""
    sector: str = ""
    text: str = ""
    limits: tuple = ()

    def __post_init__(self):
        if self.page not in PAGE_KEYS:
            raise ValueError(f"Unknown market page {self.page!r}")
        if self.category not in R.CATEGORY_KEYS:
            raise ValueError(f"Unknown ranking category {self.category!r}")
        if self.sub not in {key for key, _en, _ko in SUBS[self.page]} | {""}:
            raise ValueError(f"Sub-market {self.sub!r} is not in {self.page!r}")
        if self.sector and self.sector not in R.sectors_in(self.page):
            raise ValueError(f"Sector {self.sector!r} is not in {self.page!r}")
        order = []
        for key, low, high in self.limits:
            item = condition(key)
            if not item.available(self.page):
                raise ValueError(f"{key!r} is not a condition of {self.page!r}")
            if low is None and high is None:
                raise ValueError("A condition needs a bound")
            if low is not None and high is not None and low > high:
                raise ValueError("The low bound is above the high bound")
            order.append(CONDITION_KEYS.index(key))
        if order != sorted(set(order)):
            raise ValueError("One limit per condition, in CONDITIONS order")

    # Changes ----------------------------------------------------------------------------------
    def with_limit(self, key, low=None, high=None):
        """This screen with condition `key` set to [low, high]; no bound at all clears it."""
        kept = {k: (lo, hi) for k, lo, hi in self.limits if k != key}
        if low is not None or high is not None:
            kept[key] = (None if low is None else float(low), None if high is None else float(high))
        return replace(self, limits=tuple((k, *kept[k]) for k in CONDITION_KEYS if k in kept))

    def without(self, key):
        return self.with_limit(key)

    def cleared(self):
        """No conditions (the category, sub-market, sector and text stay)."""
        return replace(self, limits=())

    def limit(self, key):
        """(low, high) of a condition, or (None, None) when it is not set."""
        return next(((lo, hi) for k, lo, hi in self.limits if k == key), (None, None))

    def active(self):
        """(Condition, low, high) for each condition set, in table order."""
        return tuple((condition(k), lo, hi) for k, lo, hi in self.limits)

    def conditions(self):
        """The conditions this market's records can be filtered by."""
        return tuple(item for item in CONDITIONS if item.available(self.page))

    # Matching ---------------------------------------------------------------------------------
    def matches(self, record, *, text=True):
        member = record.member
        if member.group != R.group_of(self.page):
            return False
        if self.sub and self.page == "kr" and record.listing != self.sub.upper():
            return False
        if self.sub and self.page == "us" and member.exchange != self.sub:
            return False
        if self.sector and member.sector != self.sector:
            return False
        if text and self.text and not matches_text(member, self.text):
            return False
        return all(condition(k).holds(record, lo, hi) for k, lo, hi in self.limits)

    def members(self, *, text=True):
        """The universe members the sub-market, sector and text admit (before any quote is read)."""
        market = self.sub if self.page == "kr" and self.sub else self.page
        rows = R.universe(market, self.sector)
        if self.page == "us" and self.sub:
            rows = tuple(m for m in rows if m.exchange == self.sub)
        return tuple(m for m in rows if not text or matches_text(m, self.text))

    def apply(self, records, *, limit=30, missing="omit"):
        """Ranked rows: the records this screen admits, ranked by its category (rank 1 is the first admitted)."""
        if CATEGORY_NOTES.get((self.page, self.category)):
            return []
        pool = [r for r in records if self.matches(r)]
        return R.rank(pool, self.category, market=self.page, limit=limit, missing=missing)
