"""Ranked stock lists for the native Markets page (owner request 2026-11-11, point 5).

Owner: "시장 UI에는 토스증권처럼 실시간 차트를 다양한 분류기준으로 조회할수있게 변경해봐" — ranked lists by
trading value, volume, top gainers, top losers and market cap, for all of Korea, KOSPI, KOSDAQ or the US.

KIS has ranking endpoints, but the quotation allowlist (`config.KIS_QUOTATION_ALLOWLIST`) is frozen without
them. So this module ranks a curated universe of large caps instead, from per-stock quotes the existing
allowed sources already return:

* KIS ``inquire-price`` (domestic) and the overseas ``price`` quote: price, change, volume and the session's
  accumulated trading value. These are REST quotes polled every `POLL_SECONDS` during the session, never
  received trades, so the list's state says "KIS 조회 · 45초마다", not "실시간" (12-claims QG-CLAIM-KIS-20261102).
* domestic market cap (`parse_kis_domestic_cap`), from the same ``inquire-price`` answer: KIS's stated
  ``hts_avls`` read as 100 million won (`KIS_DOMESTIC_CAP_UNIT`, a unit KIS does not state) only when it agrees
  within `KIS_CAP_TOLERANCE` with listed shares ``lstn_stcn`` x price ``stck_prpr`` (basis 'provider', source
  KIS); without ``hts_avls``, listed shares x price (basis 'computed'); otherwise none, and why.
* the Yahoo daily path: the last daily bar's close, change against the previous close and volume. Trading
  value is then close x volume, an estimate, and the rows are labelled delayed/daily. Yahoo has no market cap.
* US market cap (owner 2026-11-11, "아니 미국 시총 자료 찾으세요"; KIS route approved the same day, "승인."):
  first KIS's overseas ``price-detail`` (``tomv``, checked against ``shar`` x ``last``; basis 'provider',
  source KIS) inside the KIS batch; then `core.market.market_cap`: FMP's stated figure (basis 'provider')
  or the Yahoo share count x the row's price (basis 'computed'). A stock whose figure could not be read
  keeps none.

The lists are therefore "the N major stocks below, ranked", never a whole-market ranking; the screen says so.

Pure: no Qt, no network, nothing read on import. Universe as of 2026-11 (listing market per stock as curated
here; a KIS quote that names its representative market, or a Yahoo answer under the other suffix, overrides it).
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime, timezone
import math

from core.market.models import Instrument

__all__ = ("CATEGORIES", "CATEGORY_KEYS", "MARKETS", "MARKET_KEYS", "SECTORS", "STATES", "POLL_SECONDS", "COLUMNS",
           "Member",
           "DOMESTIC", "US", "QuoteRecord", "Batch", "RankedRow", "group_of", "universe", "members_of", "member_for",
           "sectors_in", "rank", "ranking_value", "value_unit", "parse_kis_domestic", "parse_kis_overseas",
           "record_from_bars", "drop_stale", "compact", "price_text", "change_text", "source_state",
           "session_open", "text", "STALE_GAP_DAYS", "CAP_LABELS", "CAP_REASONS", "ADR_CODES", "with_cap",
           "computed_cap", "without_cap", "cap_label", "parse_kis_overseas_detail", "with_kis_detail",
           "KIS_CAP_TOLERANCE", "KIS_DOMESTIC_CAP_UNIT", "parse_kis_domestic_cap")

# (key, English, Korean). The interface contract between the native UI areas pins CATEGORIES exactly.
CATEGORIES = (("value", "Trading value", "거래대금"), ("volume", "Volume", "거래량"),
              ("gainers", "Top gainers", "급상승"), ("losers", "Top losers", "급하락"), ("cap", "Market cap", "시가총액"))
CATEGORY_KEYS = tuple(key for key, _en, _ko in CATEGORIES)
MARKETS = (("kr", "All Korea", "국내 전체"), ("kospi", "KOSPI", "코스피"), ("kosdaq", "KOSDAQ", "코스닥"),
           ("us", "US", "미국"))
MARKET_KEYS = tuple(key for key, _en, _ko in MARKETS)
SECTORS = (("semis", "Semiconductors", "반도체"), ("battery", "Batteries", "2차전지"), ("auto", "Autos", "자동차"),
           ("bio", "Bio & healthcare", "바이오·헬스케어"), ("finance", "Financials", "금융"),
           ("tech", "Tech & electronics", "IT·전자"), ("internet", "Internet & games", "인터넷·게임"),
           ("industrials", "Industrials", "산업재·조선·방산"), ("materials", "Energy & materials", "에너지·소재"),
           ("consumer", "Consumer & media", "소비재·엔터"), ("telecom", "Telecom & utilities", "통신·유틸리티"))
# Data source state shown beside the list. The KIS quotes are REST requests repeated every POLL_SECONDS during
# the session: polling, never "real-time"/"실시간", a word kept for received trades (the stock detail view's
# WebSocket state; 12-claims QG-CLAIM-KIS-20261102). The wording follows that view's "5초 조회"/"조회 시점",
# and US KIS quotes are the free feed there ("무료 시세"). Outside the session a KIS quote is the last price.
POLL_SECONDS = 45      # KIS quotes while the market is open (market_rankings.LIVE_REFRESH_SECONDS)
STATES = (("polled", f"KIS · polled every {POLL_SECONDS} s", f"KIS 조회 · {POLL_SECONDS}초마다"),
          ("polled_us", f"KIS free US feed · polled every {POLL_SECONDS} s", f"KIS 무료 시세 · {POLL_SECONDS}초마다 조회"),
          ("closed", "KIS · market closed", "KIS · 장 마감"),
          ("stale", "KIS · not current", "KIS · 갱신 지연"), ("daily", "Delayed · daily", "지연·일별"),
          ("none", "No data", "자료 없음"))
# Column captions of the list.
COLUMNS = (("rank", "Rank", "순위"), ("stock", "Stock", "종목"), ("price", "Price", "현재가"),
           ("change", "Change", "등락률"))
STALE_GAP_DAYS = 5     # a daily bar this much older than the newest one in its batch is a halted/stale quote
# Market-cap basis: a provider's stated figure, or shares outstanding x the row's price. The column heading
# says which ('시가총액(계산값)' whenever a computed figure is shown).
CAP_LABELS = (("provider", "Market cap", "시가총액"), ("computed", "Market cap (computed)", "시가총액(계산값)"))
# Why a US batch has no market cap at all (`Batch.cap_reasons`, in the order tried). The board words them.
CAP_REASONS = ("kis_off", "kis_none", "fmp_no_key", "fmp_plan", "fmp_failed", "yahoo_missing", "yahoo_unreachable",
               "yahoo_empty", "yahoo_timeout")
# US members quoted as ADRs. A share count need not be stated per ADR (TSMC: ordinary shares, five to an ADR),
# so shares x the ADR price, or a cap that only agrees with it, could overstate the cap five-fold; ADRs take
# FMP's stated figure or none.
ADR_CODES = frozenset({"TSM"})
KIS_CAP_TOLERANCE = 0.25   # KIS 'tomv' ('hts_avls') must lie within 25% of 'shar' x 'last' ('lstn_stcn' x
                           # 'stck_prpr') of the same answer to be used
KIS_DOMESTIC_CAP_UNIT = 1e8  # 'hts_avls' read as 100 million won; KIS states no unit, so every answer is checked

_EXCHANGE_NAMES = {"NAS": ("NASDAQ", "나스닥"), "NYS": ("NYSE", "뉴욕"), "AMS": ("NYSE American", "아멕스")}


def text(table, key, language):
    """The display text of `key` in one of the (key, English, Korean) tables above."""
    for k, en, ko in table:
        if k == key:
            return ko if language == "ko" else en
    raise KeyError(key)


@dataclass(frozen=True)
class Member:
    code: str
    market: str          # 'KOSPI', 'KOSDAQ' or 'US'
    sector: str          # a SECTORS key
    name_ko: str
    name_en: str
    exchange: str = ""   # KIS overseas exchange code for US members ('NAS', 'NYS')

    @property
    def group(self):
        return "us" if self.market == "US" else "kr"

    @property
    def instrument(self):
        if self.market == "US":
            return Instrument("overseas_stock", self.code, self.exchange)
        return Instrument("domestic_stock", self.code)

    @property
    def currency(self):
        return "USD" if self.market == "US" else "KRW"

    def label(self, language):
        return self.name_ko if language == "ko" else self.name_en

    def place(self, language, market=None):
        """'KOSPI'/'코스피' for a domestic member (its observed market when known), the exchange for a US one."""
        if self.market == "US":
            names = _EXCHANGE_NAMES.get(self.exchange, (self.exchange, self.exchange))
            return names[1] if language == "ko" else names[0]
        return text(MARKETS, (market or self.market).lower(), language)


def _kr(rows, market):
    return tuple(Member(code, market, sector, ko, en) for code, sector, ko, en in rows)


# Domestic large caps, KOSPI. (code, sector, Korean short name, English name)
_KOSPI = (
    ("005930", "semis", "삼성전자", "Samsung Electronics"), ("000660", "semis", "SK하이닉스", "SK hynix"),
    ("042700", "semis", "한미반도체", "Hanmi Semiconductor"),
    ("373220", "battery", "LG에너지솔루션", "LG Energy Solution"), ("006400", "battery", "삼성SDI", "Samsung SDI"),
    ("003670", "battery", "포스코퓨처엠", "POSCO Future M"),
    ("005380", "auto", "현대차", "Hyundai Motor"), ("000270", "auto", "기아", "Kia"),
    ("012330", "auto", "현대모비스", "Hyundai Mobis"),
    ("207940", "bio", "삼성바이오로직스", "Samsung Biologics"), ("068270", "bio", "셀트리온", "Celltrion"),
    ("000100", "bio", "유한양행", "Yuhan"), ("128940", "bio", "한미약품", "Hanmi Pharmaceutical"),
    ("105560", "finance", "KB금융", "KB Financial"), ("055550", "finance", "신한지주", "Shinhan Financial Group"),
    ("086790", "finance", "하나금융지주", "Hana Financial Group"),
    ("316140", "finance", "우리금융지주", "Woori Financial Group"),
    ("138040", "finance", "메리츠금융지주", "Meritz Financial Group"),
    ("032830", "finance", "삼성생명", "Samsung Life Insurance"),
    ("000810", "finance", "삼성화재", "Samsung Fire & Marine Insurance"),
    ("024110", "finance", "기업은행", "Industrial Bank of Korea"),
    ("006800", "finance", "미래에셋증권", "Mirae Asset Securities"), ("323410", "finance", "카카오뱅크", "KakaoBank"),
    ("066570", "tech", "LG전자", "LG Electronics"), ("009150", "tech", "삼성전기", "Samsung Electro-Mechanics"),
    ("011070", "tech", "LG이노텍", "LG Innotek"), ("018260", "tech", "삼성에스디에스", "Samsung SDS"),
    ("035420", "internet", "NAVER", "NAVER"), ("035720", "internet", "카카오", "Kakao"),
    ("259960", "internet", "크래프톤", "Krafton"), ("036570", "internet", "엔씨소프트", "NCSoft"),
    ("012450", "industrials", "한화에어로스페이스", "Hanwha Aerospace"),
    ("329180", "industrials", "HD현대중공업", "HD Hyundai Heavy Industries"),
    ("009540", "industrials", "HD한국조선해양", "HD Korea Shipbuilding & Offshore Engineering"),
    ("042660", "industrials", "한화오션", "Hanwha Ocean"),
    ("010140", "industrials", "삼성중공업", "Samsung Heavy Industries"),
    ("034020", "industrials", "두산에너빌리티", "Doosan Enerbility"),
    ("267260", "industrials", "HD현대일렉트릭", "HD Hyundai Electric"),
    ("010120", "industrials", "LS ELECTRIC", "LS Electric"), ("064350", "industrials", "현대로템", "Hyundai Rotem"),
    ("047810", "industrials", "한국항공우주", "Korea Aerospace Industries"),
    ("028260", "industrials", "삼성물산", "Samsung C&T"), ("011200", "industrials", "HMM", "HMM"),
    ("086280", "industrials", "현대글로비스", "Hyundai Glovis"), ("003490", "industrials", "대한항공", "Korean Air"),
    ("005490", "materials", "POSCO홀딩스", "POSCO Holdings"), ("051910", "materials", "LG화학", "LG Chem"),
    ("096770", "materials", "SK이노베이션", "SK Innovation"), ("010950", "materials", "S-Oil", "S-Oil"),
    ("010130", "materials", "고려아연", "Korea Zinc"),
    ("033780", "consumer", "KT&G", "KT&G"), ("090430", "consumer", "아모레퍼시픽", "Amorepacific"),
    ("097950", "consumer", "CJ제일제당", "CJ CheilJedang"), ("352820", "consumer", "하이브", "HYBE"),
    ("015760", "telecom", "한국전력", "KEPCO"), ("017670", "telecom", "SK텔레콤", "SK Telecom"),
    ("030200", "telecom", "KT", "KT"),
)
# Domestic large caps, KOSDAQ.
_KOSDAQ = (
    ("058470", "semis", "리노공업", "Leeno Industrial"), ("039030", "semis", "이오테크닉스", "EO Technics"),
    ("240810", "semis", "원익IPS", "Wonik IPS"), ("403870", "semis", "HPSP", "HPSP"),
    ("357780", "semis", "솔브레인", "Soulbrain"), ("036930", "semis", "주성엔지니어링", "Jusung Engineering"),
    ("247540", "battery", "에코프로비엠", "EcoPro BM"), ("086520", "battery", "에코프로", "EcoPro"),
    ("348370", "battery", "엔켐", "Enchem"),
    ("196170", "bio", "알테오젠", "Alteogen"), ("028300", "bio", "HLB", "HLB"),
    ("141080", "bio", "리가켐바이오", "LigaChem Biosciences"), ("145020", "bio", "휴젤", "Hugel"),
    ("214150", "bio", "클래시스", "Classys"), ("328130", "bio", "루닛", "Lunit"),
    ("068760", "bio", "셀트리온제약", "Celltrion Pharm"), ("298380", "bio", "에이비엘바이오", "ABL Bio"),
    ("087010", "bio", "펩트론", "Peptron"), ("000250", "bio", "삼천당제약", "Sam Chun Dang Pharm"),
    ("263750", "internet", "펄어비스", "Pearl Abyss"), ("293490", "internet", "카카오게임즈", "Kakao Games"),
    ("277810", "industrials", "레인보우로보틱스", "Rainbow Robotics"),
    ("035900", "consumer", "JYP Ent.", "JYP Entertainment"), ("041510", "consumer", "에스엠", "SM Entertainment"),
)
DOMESTIC = _kr(_KOSPI, "KOSPI") + _kr(_KOSDAQ, "KOSDAQ")

# US large caps; exchange codes as in core/market/data/overseas_symbols.json. (exchange, code, sector, ko, en)
_US = (
    ("NAS", "AAPL", "tech", "애플", "Apple"), ("NAS", "MSFT", "tech", "마이크로소프트", "Microsoft"),
    ("NAS", "NVDA", "semis", "엔비디아", "NVIDIA"), ("NAS", "AMZN", "internet", "아마존", "Amazon.com"),
    ("NAS", "GOOGL", "internet", "알파벳 A", "Alphabet Class A"), ("NAS", "META", "internet", "메타", "Meta Platforms"),
    ("NAS", "TSLA", "auto", "테슬라", "Tesla"), ("NAS", "AVGO", "semis", "브로드컴", "Broadcom"),
    ("NAS", "NFLX", "internet", "넷플릭스", "Netflix"), ("NAS", "AMD", "semis", "AMD", "Advanced Micro Devices"),
    ("NAS", "INTC", "semis", "인텔", "Intel"), ("NAS", "QCOM", "semis", "퀄컴", "Qualcomm"),
    ("NAS", "MU", "semis", "마이크론", "Micron Technology"), ("NAS", "AMAT", "semis", "어플라이드 머티리얼즈", "Applied Materials"),
    ("NAS", "TXN", "semis", "텍사스 인스트루먼트", "Texas Instruments"), ("NAS", "ADBE", "tech", "어도비", "Adobe"),
    ("NAS", "CSCO", "tech", "시스코", "Cisco Systems"), ("NAS", "PLTR", "tech", "팔란티어", "Palantir Technologies"),
    ("NAS", "CRWD", "tech", "크라우드스트라이크", "CrowdStrike"), ("NAS", "COST", "consumer", "코스트코", "Costco Wholesale"),
    ("NAS", "PEP", "consumer", "펩시코", "PepsiCo"), ("NAS", "SBUX", "consumer", "스타벅스", "Starbucks"),
    ("NAS", "ISRG", "bio", "인튜이티브 서지컬", "Intuitive Surgical"), ("NAS", "AMGN", "bio", "암젠", "Amgen"),
    ("NAS", "PYPL", "finance", "페이팔", "PayPal"), ("NAS", "COIN", "finance", "코인베이스", "Coinbase"),
    ("NAS", "TMUS", "telecom", "티모바일", "T-Mobile US"), ("NAS", "ABNB", "internet", "에어비앤비", "Airbnb"),
    ("NAS", "HON", "industrials", "하니웰", "Honeywell"),
    ("NYS", "JPM", "finance", "JP모건", "JPMorgan Chase"), ("NYS", "V", "finance", "비자", "Visa"),
    ("NYS", "MA", "finance", "마스터카드", "Mastercard"), ("NYS", "BAC", "finance", "뱅크오브아메리카", "Bank of America"),
    ("NYS", "GS", "finance", "골드만삭스", "Goldman Sachs"), ("NYS", "JNJ", "bio", "존슨앤드존슨", "Johnson & Johnson"),
    ("NYS", "LLY", "bio", "일라이 릴리", "Eli Lilly"), ("NYS", "UNH", "bio", "유나이티드헬스", "UnitedHealth Group"),
    ("NYS", "MRK", "bio", "머크", "Merck"), ("NYS", "PG", "consumer", "P&G", "Procter & Gamble"),
    ("NYS", "KO", "consumer", "코카콜라", "Coca-Cola"), ("NYS", "HD", "consumer", "홈디포", "Home Depot"),
    ("NYS", "MCD", "consumer", "맥도날드", "McDonald's"), ("NYS", "DIS", "consumer", "디즈니", "Walt Disney"),
    ("NYS", "XOM", "materials", "엑슨모빌", "Exxon Mobil"), ("NYS", "CVX", "materials", "셰브론", "Chevron"),
    ("NYS", "ORCL", "tech", "오라클", "Oracle"), ("NYS", "CRM", "tech", "세일즈포스", "Salesforce"),
    ("NYS", "UBER", "internet", "우버", "Uber Technologies"), ("NYS", "TSM", "semis", "TSMC", "TSMC ADR"),
    ("NYS", "BA", "industrials", "보잉", "Boeing"), ("NYS", "CAT", "industrials", "캐터필러", "Caterpillar"),
    ("NYS", "GE", "industrials", "GE 에어로스페이스", "GE Aerospace"), ("NYS", "T", "telecom", "AT&T", "AT&T"),
    ("NYS", "F", "auto", "포드", "Ford Motor"),
)
US = tuple(Member(code, "US", sector, ko, en, exchange) for exchange, code, sector, ko, en in _US)
_BY_KEY = {(m.instrument.asset, m.code, m.exchange): m for m in DOMESTIC + US}


def group_of(market):
    """'kr' for the domestic list keys (one fetch serves all three), 'us' for the US one."""
    if market not in MARKET_KEYS:
        raise ValueError(f"Unknown market {market!r}")
    return "us" if market == "us" else "kr"


def members_of(group):
    return US if group == "us" else DOMESTIC


def universe(market, sector=""):
    """Members listed for a market key (curated listing market), optionally one sector."""
    group = group_of(market)
    rows = members_of(group)
    if market in ("kospi", "kosdaq"):
        rows = tuple(m for m in rows if m.market == market.upper())
    return tuple(m for m in rows if not sector or m.sector == sector)


def member_for(instrument):
    """The curated member for an instrument, or None."""
    return _BY_KEY.get((instrument.asset, instrument.code, instrument.exchange))


def sectors_in(market):
    """Sector keys present in a market's universe, in SECTORS order."""
    present = {m.sector for m in universe(market)}
    return tuple(key for key, _en, _ko in SECTORS if key in present)


# Quote records ------------------------------------------------------------------------------
@dataclass(frozen=True)
class QuoteRecord:
    member: Member
    price: float
    change: float | None
    change_pct: float | None
    volume: float | None
    trading_value: float | None
    market_cap: float | None
    source: str                   # provider name, kept for the tooltip ('KIS', 'Yahoo Finance')
    mode: str                     # 'kis' (current quote) or 'daily' (last daily bar, delayed)
    as_of: str                    # 'daily': the bar's date; 'kis': when the quote was received (UTC ISO)
    estimated_value: bool = False  # trading value = close x volume
    closes: tuple = ()            # recent daily closes when the answer carried them (sparkline)
    market: str = ""              # observed listing market when the answer named it
    cap_basis: str = ""           # '' none, 'provider' (stated, checked where a share count came with it) or
                                  # 'computed' (shares x price)
    cap_source: str = ""          # who stated the cap ('KIS', 'FMP') or the share count ('Yahoo Finance', 'KIS')
    cap_as_of: str = ""           # provider: when the figure was stated/received (UTC ISO); computed: share-count
                                  # date (US) or when the KIS answer holding the share count was received (UTC ISO)
    shares: float | None = None   # the share count used (computed) or stated with the cap (KIS)
    cap_missing: str = ""         # sought but not found: 'adr', 'no_shares', 'error', 'timeout' (US); KIS domestic:
                                  # 'mismatch' (hts_avls disagrees with shares x price), 'unverified' (hts_avls
                                  # without a share count to check it), 'absent' (neither in the answer)

    @property
    def listing(self):
        return self.market or self.member.market


@dataclass(frozen=True)
class Batch:
    """One fetch of one group ('kr' or 'us')."""
    group: str
    records: tuple
    mode: str                     # 'kis', 'daily' or 'none'
    fetched_at: str               # UTC ISO
    failures: tuple = ()          # (code, error class name) per member that returned nothing usable
    stale: tuple = ()             # codes left out because their daily bar is older than the batch's
    fallback: bool = False        # KIS was configured but no quote came back; the daily path answered
    caps: str = ""                # US market cap: '' not sought, 'ok' some rows have one, 'none' none read
    cap_reasons: tuple = ()       # CAP_REASONS keys when caps == 'none' (or a provider was passed over)


@dataclass(frozen=True)
class RankedRow:
    rank: int
    record: QuoteRecord
    value: float | None           # the figure the list is ranked by (change % for gainers/losers)


def ranking_value(record, category):
    if category == "value":
        return record.trading_value
    if category == "volume":
        return record.volume
    if category in ("gainers", "losers"):
        return record.change_pct
    if category == "cap":
        return record.market_cap
    raise ValueError(f"Unknown category {category!r}")


def value_unit(category, group):
    """What the right-hand column shows: ('trading value' | 'volume' | 'market cap', unit for `compact`)."""
    money = "usd" if group == "us" else "krw"
    if category == "volume":
        return "volume", "shares"
    if category == "cap":
        return "cap", money
    return "value", money


def _finite(value):
    return value is not None and isinstance(value, (int, float)) and math.isfinite(value)


def rank(records, category, *, market="kr", sector="", limit=30, missing="omit"):
    """Ranked rows for one category, market key and optional sector.

    Trading value, volume and market cap: largest first, rows without the figure (or with zero) left out.
    Top gainers: rising stocks only, largest rise first; top losers: falling stocks only, largest fall first.
    Ties keep a stable order by code.

    `missing="last"` (trading value, volume, market cap): rows without the figure follow the ranked ones,
    unranked (rank 0, value None), so a stock whose figure could not be read is shown as '—' rather than
    silently dropped. Only when at least one row is ranked; otherwise the list is empty and says why.
    """
    if category not in CATEGORY_KEYS:
        raise ValueError(f"Unknown category {category!r}")
    if missing not in ("omit", "last"):
        raise ValueError(f"Unknown missing rule {missing!r}")
    group = group_of(market)
    pool = [r for r in records if r.member.group == group
            and (market in ("kr", "us") or r.listing == market.upper())
            and (not sector or r.member.sector == sector)]
    keyed = [(ranking_value(r, category), r) for r in pool]
    if category == "gainers":
        keyed = [(v, r) for v, r in keyed if _finite(v) and v > 0]
        keyed.sort(key=lambda item: (-item[0], item[1].member.code))
    elif category == "losers":
        keyed = [(v, r) for v, r in keyed if _finite(v) and v < 0]
        keyed.sort(key=lambda item: (item[0], item[1].member.code))
    else:
        keyed = [(v, r) for v, r in keyed if _finite(v) and v > 0]
        keyed.sort(key=lambda item: (-item[0], item[1].member.code))
    rows = [RankedRow(index + 1, record, value) for index, (value, record) in enumerate(keyed[:max(0, int(limit))])]
    if missing == "last" and rows and category not in ("gainers", "losers"):
        ranked = {id(r) for _v, r in keyed}
        rows += [RankedRow(0, r, None) for r in pool if id(r) not in ranked]
    return rows


# Parsing provider answers -----------------------------------------------------------------------
def _number(value):
    try:
        number = float(str(value).strip().replace(",", ""))
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _signed(value, sign):
    """KIS signs: 1 upper limit, 2 up, 3 unchanged, 4 lower limit, 5 down."""
    number = _number(value)
    if number is None:
        return None
    return -abs(number) if str(sign).strip() in ("4", "5") else number


def _market_name(value):
    name = str(value or "").upper()
    if "KOSDAQ" in name or "KSQ" in name:
        return "KOSDAQ"
    if "KOSPI" in name:
        return "KOSPI"
    return ""


def _utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _listed_shares(value):
    """A positive whole share count (as `data.krx.kis_client._listed_shares`), or None; never rescaled."""
    number = _number(value)
    if number is None or not 0 < number <= 2 ** 53 - 1 or not number.is_integer():
        return None
    return number


def parse_kis_domestic_cap(output, price):
    """(market cap, basis, listed shares, missing reason) from a KIS domestic ``inquire-price`` answer.

    KIS names ``hts_avls`` HTS 시가총액 without a unit. It is read as `KIS_DOMESTIC_CAP_UNIT` (100 million won)
    and used (basis 'provider') only when it agrees within `KIS_CAP_TOLERANCE` with listed shares ``lstn_stcn``
    x ``price`` (``stck_prpr``) of the same answer, the check the US path makes on ``tomv``; a disagreement is
    refused, never rescaled ('mismatch'), and a figure with no share count to check it is not used
    ('unverified'). Without ``hts_avls``, listed shares x price is the figure (basis 'computed'). Neither:
    'absent'.
    """
    if not isinstance(output, dict) or not _finite(price) or price <= 0:
        return None, "", None, "absent"
    stated = _number(output.get("hts_avls"))
    stated = stated * KIS_DOMESTIC_CAP_UNIT if stated is not None and stated > 0 else None
    shares = _listed_shares(output.get("lstn_stcn"))
    if shares is None:
        return None, "", None, "unverified" if stated is not None else "absent"
    computed = shares * float(price)
    if stated is None:
        return computed, "computed", shares, ""
    if abs(stated / computed - 1) > KIS_CAP_TOLERANCE:
        return None, "", None, "mismatch"
    return stated, "provider", shares, ""


def parse_kis_domestic(member, output, *, received_at=None):
    """A record from the ``output`` of KIS domestic ``inquire-price`` (FHKST01010100); market cap as
    `parse_kis_domestic_cap` decides (source KIS, as of the answer's receipt)."""
    if not isinstance(output, dict):
        raise ValueError("KIS answer has no output")
    price = _number(output.get("stck_prpr"))
    if price is None or price <= 0:
        raise ValueError("KIS answer has no valid price")
    sign = output.get("prdy_vrss_sign")
    volume, value = _number(output.get("acml_vol")), _number(output.get("acml_tr_pbmn"))
    received = received_at or _utc_now()
    cap, basis, shares, missing = parse_kis_domestic_cap(output, price)
    return QuoteRecord(member, price, _signed(output.get("prdy_vrss"), sign), _signed(output.get("prdy_ctrt"), sign),
                       volume if volume is not None and volume >= 0 else None,
                       value if value is not None and value >= 0 else None,
                       cap, "KIS", "kis", received, market=_market_name(output.get("rprs_mrkt_kor_name")),
                       cap_basis=basis, cap_source="KIS" if basis else "", cap_as_of=received if basis else "",
                       shares=shares, cap_missing=missing)


def parse_kis_overseas(member, output, *, received_at=None):
    """A record from the ``output`` of the KIS overseas ``price`` quote (HHDFS00000300); no market cap there."""
    if not isinstance(output, dict):
        raise ValueError("KIS answer has no output")
    price = _number(output.get("last"))
    if price is None or price <= 0:
        raise ValueError("KIS answer has no valid price")
    sign = output.get("sign")
    change = _signed(output.get("diff"), sign)
    base = _number(output.get("base"))
    if change is None and base:
        change = price - base
    pct = _signed(output.get("rate"), sign)
    if pct is None and change is not None and base:
        pct = change / base * 100
    volume, value = _number(output.get("tvol")), _number(output.get("tamt"))
    return QuoteRecord(member, price, change, pct, volume if volume is not None and volume >= 0 else None,
                       value if value is not None and value >= 0 else None, None, "KIS", "kis",
                       received_at or _utc_now())


def parse_kis_overseas_detail(output):
    """(market cap, listed shares) from the ``output`` of the KIS overseas ``price-detail`` quote
    (HHDFS76200200), or (None, None) when it cannot be trusted.

    Unit assumption, checked on every answer: KIS names ``tomv`` 시가총액 and ``shar`` 상장주수 without a unit.
    ``tomv`` is taken to be in the quote currency ``curr`` (USD on NAS/NYS/AMS), the unit of ``last`` that
    `parse_kis_overseas` already reads as dollars; the won conversions are the separate ``t_x*``/``p_x*``
    fields (``t_xprc`` = last x ``t_rate``), not used here. ``tomv`` must agree with ``shar`` x ``last``
    within `KIS_CAP_TOLERANCE`, else neither figure is used: a thousand-fold unit (or won) shows up as a
    mismatch and is refused, never rescaled. A currency other than USD is refused.
    """
    if not isinstance(output, dict):
        return None, None
    currency = str(output.get("curr") or "").strip().upper()
    if currency and currency != "USD":
        return None, None
    cap, shares, last = _number(output.get("tomv")), _number(output.get("shar")), _number(output.get("last"))
    if not all(value is not None and value > 0 for value in (cap, shares, last)):
        return None, None
    if abs(cap / (shares * last) - 1) > KIS_CAP_TOLERANCE:
        return None, None
    return cap, shares


def with_kis_detail(record, output, *, received_at=""):
    """`record` with KIS's stated market cap (basis 'provider', source 'KIS') when the price-detail answer
    passes `parse_kis_overseas_detail`; unchanged otherwise, and always for an ADR."""
    if record.member.code in ADR_CODES:
        return record
    cap, shares = parse_kis_overseas_detail(output)
    if cap is None:
        return record
    return with_cap(record, cap, basis="provider", source="KIS", as_of=received_at, shares=shares)


def record_from_bars(member, bars, *, source="Yahoo Finance", market="", sparkline=20):
    """A delayed record from daily bars ``(date, open, high, low, close, volume)``, oldest first.

    The change is the last close against the previous one; trading value is close x volume (estimated).
    """
    rows = []
    for bar in bars:
        try:
            day, close, volume = str(bar[0])[:10], _number(bar[4]), _number(bar[5]) if len(bar) > 5 else None
        except (TypeError, IndexError):
            continue
        if close is None or close <= 0:
            continue
        rows.append((day, close, volume if volume is not None and volume >= 0 else None))
    rows.sort(key=lambda row: row[0])
    if len(rows) < 2:
        raise ValueError("Fewer than two usable daily bars")
    (day, close, volume), previous = rows[-1], rows[-2][1]
    change = close - previous
    value = close * volume if volume else None
    return QuoteRecord(member, close, change, change / previous * 100, volume, value, None, source, "daily", day,
                       estimated_value=value is not None,
                       closes=tuple(row[1] for row in rows[-max(2, int(sparkline)):]), market=market)


def drop_stale(records, gap_days=STALE_GAP_DAYS):
    """Daily records whose bar is `gap_days` older than the newest bar of the batch are left out.

    Returns (kept, stale codes). A halted stock's old move must not rank beside today's.
    """
    days = {}
    for record in records:
        if record.mode == "daily":
            try:
                days[record.member.code] = date.fromisoformat(record.as_of[:10])
            except ValueError:
                pass
    if not days:
        return tuple(records), ()
    newest = max(days.values())
    stale = tuple(code for code, day in days.items() if (newest - day).days >= gap_days)
    return tuple(r for r in records if r.member.code not in stale), stale


# Market cap -----------------------------------------------------------------------------------
def with_cap(record, cap, *, basis, source, as_of="", shares=None):
    """`record` with a market cap and where it came from; a missing or non-positive figure is refused."""
    if basis not in ("provider", "computed"):
        raise ValueError(f"Unknown market-cap basis {basis!r}")
    if not _finite(cap) or cap <= 0:
        raise ValueError("Market cap must be a positive number")
    return replace(record, market_cap=float(cap), cap_basis=basis, cap_source=str(source), cap_as_of=str(as_of),
                   shares=float(shares) if shares is not None else None, cap_missing="")


def computed_cap(record, shares, *, source, as_of):
    """Shares outstanding x the record's own price (KIS last or the daily close); never for an ADR."""
    if record.member.code in ADR_CODES:
        raise ValueError("A share count is not per ADR")
    if not _finite(shares) or shares <= 0:
        raise ValueError("Share count must be a positive number")
    return with_cap(record, float(shares) * record.price, basis="computed", source=source, as_of=as_of,
                    shares=shares)


def without_cap(record, reason):
    """`record` with no market cap, and why ('adr', 'no_shares', 'error', 'timeout')."""
    return replace(record, market_cap=None, cap_basis="", cap_source="", cap_as_of="", shares=None,
                   cap_missing=str(reason))


def cap_label(rows, language):
    """The heading of the market-cap column: '시가총액(계산값)' when any row shown is computed."""
    computed = any(getattr(row, "record", row).cap_basis == "computed" for row in rows)
    return text(CAP_LABELS, "computed" if computed else "provider", language)


# Display ------------------------------------------------------------------------------------
def compact(value, unit, language):
    """Compact figures: '1.2조', '3,456억', '2,130만주' in Korean; '₩1.2T', '$12.3B', '21.3M' in English."""
    if not _finite(value):
        return "—"
    sign, v = ("-" if value < 0 else ""), abs(float(value))
    if language == "ko" and unit == "krw":
        if v >= 1e12:
            return f"{sign}{v / 1e12:,.1f}조"
        if v >= 1e8:
            return f"{sign}{v / 1e8:,.0f}억"
        if v >= 1e4:
            return f"{sign}{v / 1e4:,.0f}만"
        return f"{sign}{v:,.0f}"
    if language == "ko" and unit == "shares":
        if v >= 1e8:
            return f"{sign}{v / 1e8:,.1f}억주"
        if v >= 1e4:
            return f"{sign}{v / 1e4:,.0f}만주"
        return f"{sign}{v:,.0f}주"
    prefix = {"krw": "₩", "usd": "$"}.get(unit, "")
    for step, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if v >= step:
            return f"{sign}{prefix}{v / step:,.1f}{suffix}"
    return f"{sign}{prefix}{v:,.0f}"


def price_text(value, currency):
    if not _finite(value):
        return "—"
    return f"${value:,.2f}" if currency == "USD" else f"{value:,.0f}"


def change_text(pct):
    """('+1.24%', 'up'); Korean market tones: up is red, down is blue (typography.TONE_COLORS)."""
    if not _finite(pct):
        return "", "flat"
    if pct == 0:
        return "0.00%", "flat"
    return f"{pct:+.2f}%", "up" if pct > 0 else "down"


def session_open(group, moment=None):
    """Whether the group's market is in its regular session now (holiday calendars included)."""
    from core.markets import is_open
    moment = moment or datetime.now(timezone.utc)
    return bool(is_open("US" if group == "us" else "KRX", moment))


def source_state(batch, *, open_now, age_seconds=0.0, live_limit=None):
    """'polled' (KIS REST quotes during the session; 'polled_us' for the US group, KIS's free US feed),
    'stale' (KIS during the session but older than `live_limit` seconds, e.g. refreshes keep failing),
    'closed' (KIS outside it), 'daily' (delayed daily bars) or 'none'. Never 'live': nothing here is a
    received trade."""
    if batch is None or not batch.records:
        return "none"
    if batch.mode == "kis":
        if not open_now:
            return "closed"
        if live_limit is not None and age_seconds > live_limit:
            return "stale"
        return "polled_us" if batch.group == "us" else "polled"
    return "daily"
