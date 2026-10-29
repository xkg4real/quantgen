"""Build the proposed v1.0.0 holidays_JPX, holidays_SSE, holidays_HKEX, holidays_TWSE, holidays_CME and market_closes
files (audit report docs/audit/2026-10-27/14_calendar_batch6.md).

The five holiday drafts ship with no rows and market_closes with three unsourced rows. The rows below come from the
exchanges' own notices (grade A), government holiday lists the exchanges follow (grade B) or the statutory rules where
the 2027 notice is not out yet (grade C). The session's network policy blocked the official sites, so every source
was read through search-engine excerpts; the cross-check against exchange_calendars 4.13.2 and
pandas_market_calendars 5.5.0 is in cross_check.py. Nothing under core/calendars/data/ is written and no signature
is set.

    python docs/audit/2026-10-27/calendar_batch6/build_proposed.py
"""
from __future__ import annotations

import difflib
import subprocess
import sys
from datetime import date
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
OUT = HERE / "proposed"
DRAFT_REF = "eacd57d"                       # the six drafts are unchanged since the baseline commit
AUDIT_UTC = "2026-10-28T18:10:00Z"          # when the search excerpts below were read
REPORT = "docs/audit/2026-10-27/14_calendar_batch6.md"
VERSION = "1.0.0"
COVERS = {"from": "2025-01-01", "to": "2027-12-31"}

# --------------------------------------------------------------------------- #
# Sources
# --------------------------------------------------------------------------- #
JPX_CAL = "https://www.jpx.co.jp/corporate/about-jpx/calendar/index.html"
JPX_HT = "https://www.jpx.co.jp/derivatives/rules/holidaytrading/"          # holiday trading runs only on market holidays
JPX_N = "https://www.jpx.co.jp/news/2040/"
JPX_EN = "https://www.jpx.co.jp/english/news/2040/"
JPX_2025 = {
    "2025-01-01": "https://www.jpx.co.jp/corporate/news/news-releases/0061/20241202-01.html",
    "2025-01-02": JPX_N + "20241230-01.html", "2025-01-03": JPX_N + "20241230-01.html",
    "2025-01-13": JPX_EN + "20250110-01.html", "2025-02-11": JPX_N + "20250210-01.html",
    "2025-02-24": JPX_EN + "20250224-01.html", "2025-03-20": JPX_EN + "20250319-01.html",
    "2025-04-29": JPX_EN + "20250428-01.html", "2025-05-05": JPX_EN + "20250502-01.html",
    "2025-05-06": JPX_EN + "20250502-01.html", "2025-07-21": JPX_EN + "20250718-01.html",
    "2025-08-11": JPX_EN + "20250808-01.html", "2025-09-15": JPX_N + "20250912-01.html",
    "2025-09-23": JPX_EN + "20250922-02.html", "2025-10-13": JPX_N + "20251010-02.html",
    "2025-11-03": JPX_EN + "20251031-01.html", "2025-11-24": JPX_N + "20251121-01.html",
    "2025-12-31": JPX_N + "20251230-01.html",
}
JPX_2025_COUNT = "https://www.jpx.co.jp/english/corporate/news/news-releases/0063/vk0khi000000kxv3-att/reference(tse)_2025.pdf"
NAOJ_2027 = "https://eco.mtk.nao.ac.jp/koyomi/yoko/2027/rekiyou271.html"
NIPPON_2027 = "https://www.nippon.com/ja/japan-data/h02794/"

SSE_2025 = "https://www.sse.com.cn/disclosure/announcement/general/c/c_20241223_10767108.shtml"
SSE_2025_REPOST = "https://www.sina.cn/news/detail/5114865242607279.html"
SSE_2025_NATL = "https://www.sse.com.cn/disclosure/announcement/general/c/c_20250925_10792976.shtml"
SSE_2026 = "https://www.sse.com.cn/disclosure/announcement/general/c/c_20251222_10802507.shtml"
SSE_2026_MIDAUT = "https://www.sse.com.cn/disclosure/announcement/general/c/c_20260915_10832273.shtml"
SC_2025 = "https://www.news.cn/politics/20241112/46dcf0de740844dd824ff54b5be5af2e/c.html"
SC_2026 = "https://www.news.cn/politics/20251104/88bcffd88ae249e58c699b8772548e3d/c.html"
SC_RULES = "https://www.news.cn/politics/20241112/53da215f46c546a480f0a01d339dafa2/c.html"   # holiday rules, from 2025
SSE_CLOSE_AUCTION = "https://finance.ifeng.com/a/20180806/16431578_0.shtml"

HK_CT_2025 = ("https://www.hkex.com.hk/-/media/HKEX-Market/Services/Circulars-and-Notices/Participant-and-Members-"
              "Circulars/SEHK/2024/ce_SEHK_CT_063_2024.pdf")
HK_CT_2026 = ("https://www.hkex.com.hk/Services/Circulars-and-Notices/Participant-and-Members-Circulars/SEHK/2025/"
              "SEHK_CT_075_2025?sc_lang=en")
HK_CT_2027 = ("https://www.hkex.com.hk/Services/Circulars-and-Notices/Participant-and-Members-Circulars/SEHK/2026/"
              "SEHK_CT_077_2026Jun01162846?sc_lang=en")
HK_CT_EVES = ("https://www.hkex.com.hk/Services/Circulars-and-Notices/Participant-and-Members-Circulars/SEHK/2025/"
              "SEHK_CT_166_2025Dec01164633?sc_lang=en")
HK_GOV = "https://www.gov.hk/en/about/abouthk/holiday/{y}.htm"
HK_HOURS = ("https://www.hkex.com.hk/Services/Trading-hours-and-Severe-Weather-Arrangements/Trading-Hours/"
            "Securities-Market?sc_lang=en")
HK_CAS_LAUNCH = "https://www.hkex.com.hk/News/Market-Communications/2016/160720news"
HK_CAS_PDF = ("https://www.HKEX.com.hk/-/media/HKEX-Market/Services/Trading/Securities/Overview/Trading-Mechanism/"
              "Trading-Mechanism-of-CAS-in-the-Securities-Market.pdf")
HSI_GUIDE = "https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/methodologies/index_operation_guide_e.pdf"
HK_SWT = "https://www.hkex.com.hk/News/Market-Communications/2024/240618news?sc_lang=en"

# --------------------------------------------------------------------------- #
# Rows: (date, kind, name, evidence, source[, close_local])
# --------------------------------------------------------------------------- #
JPX_A = "A: JPX notice (holiday trading runs only on cash-market holidays) or JPX holiday list"
JPX_B27 = ("B: National Holidays Act date, listed by NAOJ's 2027 calendar (gazette 2026-02-02); JPX's 2027 list exists "
           "but this row was not in the search excerpt")
JPX = [
    ("2025-01-01", "closed", "New Year's Day (元日)", JPX_A, JPX_2025["2025-01-01"]),
    ("2025-01-02", "closed", "Market holiday, New Year (休業日)", JPX_A, JPX_2025["2025-01-02"]),
    ("2025-01-03", "closed", "Market holiday, New Year (休業日)", JPX_A, JPX_2025["2025-01-03"]),
    ("2025-01-13", "closed", "Coming of Age Day (成人の日)", JPX_A, JPX_2025["2025-01-13"]),
    ("2025-02-11", "closed", "National Foundation Day (建国記念の日)", JPX_A, JPX_2025["2025-02-11"]),
    ("2025-02-24", "closed", "Substitute holiday, Emperor's Birthday (振替休日)", JPX_A, JPX_2025["2025-02-24"]),
    ("2025-03-20", "closed", "Vernal Equinox Day (春分の日)", JPX_A, JPX_2025["2025-03-20"]),
    ("2025-04-29", "closed", "Showa Day (昭和の日)", JPX_A, JPX_2025["2025-04-29"]),
    ("2025-05-05", "closed", "Children's Day (こどもの日)", JPX_A, JPX_2025["2025-05-05"]),
    ("2025-05-06", "closed", "Substitute holiday, Greenery Day (振替休日)", JPX_A, JPX_2025["2025-05-06"]),
    ("2025-07-21", "closed", "Marine Day (海の日)", JPX_A, JPX_2025["2025-07-21"]),
    ("2025-08-11", "closed", "Mountain Day (山の日)", JPX_A, JPX_2025["2025-08-11"]),
    ("2025-09-15", "closed", "Respect for the Aged Day (敬老の日)", JPX_A, JPX_2025["2025-09-15"]),
    ("2025-09-23", "closed", "Autumnal Equinox Day (秋分の日)", JPX_A, JPX_2025["2025-09-23"]),
    ("2025-10-13", "closed", "Sports Day (スポーツの日)", JPX_A, JPX_2025["2025-10-13"]),
    ("2025-11-03", "closed", "Culture Day (文化の日)", JPX_A, JPX_2025["2025-11-03"]),
    ("2025-11-24", "closed", "Substitute holiday, Labor Thanksgiving Day (振替休日)", JPX_A, JPX_2025["2025-11-24"]),
    ("2025-12-31", "closed", "Market holiday, year end (休業日)", JPX_A, JPX_2025["2025-12-31"]),
    ("2026-01-01", "closed", "New Year's Day (元日)", JPX_A, JPX_CAL),
    ("2026-01-02", "closed", "Market holiday, New Year (休業日)", JPX_A, JPX_CAL + " ; " + JPX_N + "20251230-01.html"),
    ("2026-01-12", "closed", "Coming of Age Day (成人の日)", JPX_A, JPX_CAL),
    ("2026-02-11", "closed", "National Foundation Day (建国記念の日)", JPX_A, JPX_CAL),
    ("2026-02-23", "closed", "Emperor's Birthday (天皇誕生日)", JPX_A, JPX_CAL),
    ("2026-03-20", "closed", "Vernal Equinox Day (春分の日)", JPX_A, JPX_CAL),
    ("2026-04-29", "closed", "Showa Day (昭和の日)", JPX_A, JPX_CAL),
    ("2026-05-04", "closed", "Greenery Day (みどりの日)", JPX_A, JPX_CAL + " ; " + JPX_N + "20260501-01.html"),
    ("2026-05-05", "closed", "Children's Day (こどもの日)", JPX_A, JPX_CAL + " ; " + JPX_N + "20260501-01.html"),
    ("2026-05-06", "closed", "Substitute holiday, Constitution Day (振替休日)", JPX_A, JPX_CAL + " ; " + JPX_N + "20260501-01.html"),
    ("2026-07-20", "closed", "Marine Day (海の日)", JPX_A, JPX_CAL),
    ("2026-08-11", "closed", "Mountain Day (山の日)", JPX_A, JPX_CAL),
    ("2026-09-21", "closed", "Respect for the Aged Day (敬老の日)", JPX_A, JPX_CAL + " ; " + JPX_EN + "20260918-01.html"),
    ("2026-09-22", "closed", "Citizens' holiday (国民の休日, 祝日法第3条第3項)", JPX_A, JPX_CAL + " ; " + JPX_EN + "20260918-01.html"),
    ("2026-09-23", "closed", "Autumnal Equinox Day (秋分の日)", JPX_A, JPX_CAL + " ; " + JPX_EN + "20260918-01.html"),
    ("2026-10-12", "closed", "Sports Day (スポーツの日)", JPX_A, JPX_CAL),
    ("2026-11-03", "closed", "Culture Day (文化の日)", JPX_A, JPX_CAL),
    ("2026-11-23", "closed", "Labor Thanksgiving Day (勤労感謝の日)", JPX_A, JPX_CAL),
    ("2026-12-31", "closed", "Market holiday, year end (休業日)", JPX_A, JPX_CAL),
    ("2027-01-01", "closed", "New Year's Day (元日)", JPX_A, JPX_CAL),
    ("2027-01-11", "closed", "Coming of Age Day (成人の日)", JPX_A, JPX_CAL),
    ("2027-02-11", "closed", "National Foundation Day (建国記念の日)", JPX_A, JPX_CAL),
    ("2027-02-23", "closed", "Emperor's Birthday (天皇誕生日)", JPX_A, JPX_CAL),
    ("2027-03-22", "closed", "Substitute holiday, Vernal Equinox Day (振替休日)", JPX_A, JPX_CAL + " ; " + JPX_HT + " ; " + NAOJ_2027),
    ("2027-04-29", "closed", "Showa Day (昭和の日)", JPX_B27, NAOJ_2027 + " ; " + NIPPON_2027),
    ("2027-05-03", "closed", "Constitution Memorial Day (憲法記念日)", JPX_B27, NAOJ_2027 + " ; " + NIPPON_2027),
    ("2027-05-04", "closed", "Greenery Day (みどりの日)", JPX_B27, NAOJ_2027 + " ; " + NIPPON_2027),
    ("2027-05-05", "closed", "Children's Day (こどもの日)", JPX_B27, NAOJ_2027 + " ; " + NIPPON_2027),
    ("2027-07-19", "closed", "Marine Day (海の日)", JPX_B27, NAOJ_2027 + " ; " + NIPPON_2027),
    ("2027-08-11", "closed", "Mountain Day (山の日)", JPX_B27, NAOJ_2027 + " ; " + NIPPON_2027),
    ("2027-09-20", "closed", "Respect for the Aged Day (敬老の日)", JPX_A, JPX_HT),
    ("2027-09-23", "closed", "Autumnal Equinox Day (秋分の日)", JPX_A, JPX_HT + " ; " + NAOJ_2027),
    ("2027-10-11", "closed", "Sports Day (スポーツの日)", JPX_A, JPX_CAL),
    ("2027-11-03", "closed", "Culture Day (文化の日)", JPX_B27, NAOJ_2027 + " ; " + NIPPON_2027),
    ("2027-11-23", "closed", "Labor Thanksgiving Day (勤労感謝の日)", JPX_A, JPX_CAL),
    ("2027-12-31", "closed", "Market holiday, year end (休業日)", JPX_A, JPX_HT + " ; " + JPX_CAL),
]

SSE_A25 = "A: SSE 2025 holiday notice (上证公告〔2024〕38号); weekend make-up workdays are 周末休市, not sessions"
SSE_A26 = "A: SSE 2026 holiday notice (上证公告〔2025〕45号) and the SSE per-holiday notice"
SSE_C27 = ("C: 2027 not announced (State Council notice usually November, SSE notice December); statutory holiday "
           "on a weekday under the rules in force from 2025 (Spring Festival Eve and May 2 added)")
SSE_C27_OWED = ("C: 2027 not announced; a weekday off owed for a statutory holiday falling on a weekend "
                "(放假办法 补假), date inferred")
SSE_C27_PATTERN = ("C: 2027 not announced; inferred from the 2025-2026 arrangements (Spring Festival 8-9 days, "
                   "Labour Day May 1-5, National Day Oct 1-7); a wrong guess only delays or blanks a Shanghai close")
SSE = [
    ("2025-01-01", "closed", "New Year's Day (元旦)", SSE_A25, SSE_2025 + " ; " + SSE_2025_REPOST),
    *[(d, "closed", "Spring Festival (春节)" + (", Eve (除夕)" if d == "2025-01-28" else ""), SSE_A25,
       SSE_2025 + " ; " + SSE_2025_REPOST + " ; " + SC_2025)
      for d in ("2025-01-28", "2025-01-29", "2025-01-30", "2025-01-31", "2025-02-03", "2025-02-04")],
    ("2025-04-04", "closed", "Qingming Festival (清明节)", SSE_A25, SSE_2025),
    *[(d, "closed", "Labour Day (劳动节)", SSE_A25, SSE_2025 + " ; " + SC_2025)
      for d in ("2025-05-01", "2025-05-02", "2025-05-05")],
    ("2025-06-02", "closed", "Dragon Boat Festival (端午节)", SSE_A25, SSE_2025 + " ; " + SC_2025),
    *[(d, "closed", "National Day and Mid-Autumn Festival (国庆节、中秋节)", SSE_A25, SSE_2025_NATL + " ; " + SSE_2025)
      for d in ("2025-10-01", "2025-10-02", "2025-10-03", "2025-10-06", "2025-10-07", "2025-10-08")],
    *[(d, "closed", "New Year's Day (元旦)", SSE_A26, SSE_2026 + " ; " + SC_2026) for d in ("2026-01-01", "2026-01-02")],
    *[(d, "closed", "Spring Festival (春节)" + (", Eve (除夕)" if d == "2026-02-16" else ""), SSE_A26,
       SSE_2026 + " ; " + SC_2026)
      for d in ("2026-02-16", "2026-02-17", "2026-02-18", "2026-02-19", "2026-02-20", "2026-02-23")],
    ("2026-04-06", "closed", "Qingming Festival (清明节)", SSE_A26, SSE_2026 + " ; " + SC_2026),
    *[(d, "closed", "Labour Day (劳动节)", SSE_A26, SSE_2026 + " ; " + SC_2026)
      for d in ("2026-05-01", "2026-05-04", "2026-05-05")],
    ("2026-06-19", "closed", "Dragon Boat Festival (端午节)", SSE_A26, SSE_2026 + " ; " + SC_2026),
    ("2026-09-25", "closed", "Mid-Autumn Festival (中秋节)", SSE_A26, SSE_2026_MIDAUT + " ; " + SSE_2026),
    *[(d, "closed", "National Day (国庆节)", SSE_A26, SSE_2026_MIDAUT + " ; " + SC_2026)
      for d in ("2026-10-01", "2026-10-02", "2026-10-05", "2026-10-06", "2026-10-07")],
    ("2027-01-01", "closed", "New Year's Day (元旦)", SSE_C27, SC_RULES),
    ("2027-02-05", "closed", "Spring Festival Eve (除夕)", SSE_C27, SC_RULES + " ; " + HK_GOV.format(y=2027)),
    ("2027-02-08", "closed", "Spring Festival, third day (春节初三)", SSE_C27, SC_RULES + " ; " + HK_GOV.format(y=2027)),
    ("2027-02-09", "closed", "Spring Festival (春节)", SSE_C27_OWED, SC_RULES),
    ("2027-02-10", "closed", "Spring Festival (春节)", SSE_C27_OWED, SC_RULES),
    ("2027-02-11", "closed", "Spring Festival (春节)", SSE_C27_PATTERN, SC_2025 + " ; " + SC_2026),
    ("2027-02-12", "closed", "Spring Festival (春节)", SSE_C27_PATTERN, SC_2025 + " ; " + SC_2026),
    ("2027-04-05", "closed", "Qingming Festival (清明节)", SSE_C27, SC_RULES + " ; " + HK_GOV.format(y=2027)),
    ("2027-05-03", "closed", "Labour Day (劳动节)", SSE_C27_OWED, SC_RULES),
    ("2027-05-04", "closed", "Labour Day (劳动节)", SSE_C27_OWED, SC_RULES),
    ("2027-05-05", "closed", "Labour Day (劳动节)", SSE_C27_PATTERN, SC_2025 + " ; " + SC_2026),
    ("2027-06-09", "closed", "Dragon Boat Festival (端午节)", SSE_C27, SC_RULES + " ; " + HK_GOV.format(y=2027)),
    ("2027-09-15", "closed", "Mid-Autumn Festival (中秋节)", SSE_C27, SC_RULES),
    ("2027-10-01", "closed", "National Day (国庆节)", SSE_C27, SC_RULES),
    ("2027-10-04", "closed", "National Day (国庆节)", SSE_C27_OWED, SC_RULES),
    ("2027-10-05", "closed", "National Day (国庆节)", SSE_C27_OWED, SC_RULES),
    ("2027-10-06", "closed", "National Day (国庆节)", SSE_C27_PATTERN, SC_2025 + " ; " + SC_2026),
    ("2027-10-07", "closed", "National Day (国庆节)", SSE_C27_PATTERN, SC_2025 + " ; " + SC_2026),
]

HK_A = "A: HKEX holiday-schedule circular lists the date"
HK_B = ("B: HK general holiday (gazette); HKEX's circular for the year says it follows the gazette but this row was "
        "not in the search excerpt")
HK_HALF = ("A: HKEX half-day trading day (no afternoon session); the closing auction runs 12:00 to a random close "
           "12:08-12:10, so the official close is set by 12:10")
HK = [
    ("2025-01-01", "closed", "New Year's Day", HK_B, HK_GOV.format(y=2025) + " ; " + HK_CT_2025),
    ("2025-01-28", "early_close", "Lunar New Year's Eve (half day)", HK_HALF, HK_CT_2025 + " ; " + HK_HOURS, "12:10"),
    *[(d, "closed", n, HK_B, HK_GOV.format(y=2025) + " ; " + HK_CT_2025) for d, n in (
        ("2025-01-29", "Lunar New Year's Day"), ("2025-01-30", "The second day of Lunar New Year"),
        ("2025-01-31", "The third day of Lunar New Year"))],
    *[(d, "closed", n, HK_A, HK_CT_2025 + " ; " + HK_GOV.format(y=2025)) for d, n in (
        ("2025-04-04", "Ching Ming Festival"), ("2025-04-18", "Good Friday"), ("2025-04-21", "Easter Monday"),
        ("2025-05-01", "Labour Day"), ("2025-05-05", "The Birthday of the Buddha"))],
    ("2025-07-01", "closed", "HKSAR Establishment Day", HK_B, HK_GOV.format(y=2025) + " ; " + HK_CT_2025),
    ("2025-10-01", "closed", "National Day", HK_B, HK_GOV.format(y=2025) + " ; " + HK_CT_2025),
    ("2025-10-07", "closed", "The day following the Chinese Mid-Autumn Festival", HK_A, HK_CT_2025 + " ; " + HK_GOV.format(y=2025)),
    ("2025-10-29", "closed", "Chung Yeung Festival", HK_A, HK_CT_2025 + " ; " + HK_GOV.format(y=2025)),
    ("2025-12-24", "early_close", "Christmas Eve (half day)", HK_HALF, HK_CT_2025 + " ; " + HK_CT_EVES, "12:10"),
    ("2025-12-25", "closed", "Christmas Day", HK_B, HK_GOV.format(y=2025) + " ; " + HK_CT_2025),
    ("2025-12-26", "closed", "The first weekday after Christmas Day", HK_B, HK_GOV.format(y=2025) + " ; " + HK_CT_2025),
    ("2025-12-31", "early_close", "New Year's Eve (half day)", HK_HALF, HK_CT_2025 + " ; " + HK_CT_EVES, "12:10"),
    ("2026-01-01", "closed", "New Year's Day", HK_A, HK_CT_2026),
    ("2026-02-16", "early_close", "Lunar New Year's Eve (half day)", HK_HALF, HK_CT_EVES + " ; " + HK_CT_2026, "12:10"),
    *[(d, "closed", n, HK_A, HK_CT_2026 + " ; " + HK_GOV.format(y=2026)) for d, n in (
        ("2026-02-17", "Lunar New Year's Day"), ("2026-02-18", "The second day of Lunar New Year"),
        ("2026-02-19", "The third day of Lunar New Year"), ("2026-04-03", "Good Friday"),
        ("2026-04-06", "The day following Ching Ming Festival"), ("2026-04-07", "The day following Easter Monday"),
        ("2026-05-01", "Labour Day"), ("2026-05-25", "The day following the Birthday of the Buddha"),
        ("2026-06-19", "Tuen Ng Festival"), ("2026-07-01", "HKSAR Establishment Day"), ("2026-10-01", "National Day"),
        ("2026-10-19", "The day following Chung Yeung Festival"))],
    ("2026-12-24", "early_close", "Christmas Eve (half day)", HK_HALF, HK_CT_2026, "12:10"),
    ("2026-12-25", "closed", "Christmas Day", HK_A, HK_CT_2026 + " ; " + HK_GOV.format(y=2026)),
    ("2026-12-31", "early_close", "New Year's Eve (half day)", HK_HALF, HK_CT_2026, "12:10"),
    ("2027-01-01", "closed", "New Year's Day", HK_A, HK_CT_2027 + " ; " + HK_GOV.format(y=2027)),
    ("2027-02-05", "early_close", "Lunar New Year's Eve (half day)", HK_HALF, HK_CT_2027, "12:10"),
    *[(d, "closed", n, HK_B, HK_GOV.format(y=2027) + " ; " + HK_CT_2027) for d, n in (
        ("2027-02-08", "The third day of Lunar New Year"),
        ("2027-02-09", "The fourth day of Lunar New Year (the second day is a Sunday)"),
        ("2027-03-26", "Good Friday"), ("2027-03-29", "Easter Monday"), ("2027-04-05", "Ching Ming Festival"),
        ("2027-05-13", "The Birthday of the Buddha"), ("2027-06-09", "Tuen Ng Festival"),
        ("2027-07-01", "HKSAR Establishment Day"), ("2027-09-16", "The day following the Chinese Mid-Autumn Festival"),
        ("2027-10-01", "National Day"), ("2027-10-08", "Chung Yeung Festival"))],
    ("2027-12-24", "early_close", "Christmas Eve (half day)", HK_HALF, HK_CT_2027, "12:10"),
    ("2027-12-27", "closed", "The first weekday after Christmas Day", HK_B, HK_GOV.format(y=2027) + " ; " + HK_CT_2027),
    ("2027-12-31", "early_close", "New Year's Eve (half day)", HK_HALF, HK_CT_2027, "12:10"),
]

TW_2025 = "https://dsp.twse.com.tw/public/static/downloads/announcement/official/J-11300220221-2.doc"
TW_2025_LNY = ("https://tw.stock.yahoo.com/news/%E8%AD%89%E4%BA%A4%E6%89%80-%E5%8F%B0%E8%82%A1%E6%98%A5%E7%AF%801-27"
               "%E8%B5%B7%E4%BC%91%E5%B8%825%E5%A4%A9-2-8%E8%A3%9C%E7%8F%AD%E6%97%A5%E4%B8%8D%E4%BA%A4%E6%98%93-083656114.html")
TW_2025_0929 = "https://money.udn.com/money/story/5607/9026549"
TW_2025_ADDED = ("https://tw.stock.yahoo.com/news/%E8%AD%89%E4%BA%A4%E6%89%80%E6%96%B0%E5%A2%9Eq3%E5%8F%B0%E8%82%A1%E4%BC%91"
                 "%E5%B8%82%E6%97%A5-10-24-12-25%E8%82%A1%E5%B8%82%E4%B8%8D%E4%BA%A4%E6%98%93-134242218.html")
TW_TAIFEX_2025 = ("https://www.taifex.com.tw/file/taifex/CHINESE/11/attach/%E5%8F%B0%E6%9C%9F%E4%BA%A4%E5%AD%97%E7%AC%AC"
                  "1140001929%E8%99%9F%E5%87%BD.pdf")
TW_2026 = "https://www.twse.com.tw/holidaySchedule/holidaySchedule?response=html"
TW_2026_LNY = "https://www.twse.com.tw/staticFiles/news/news/tsecnews/8a8216d69bde495d019c0d7f8f0100e2.pdf"
TW_BAVI = "https://ctee.com.tw/news/20260710700623-430301"
TW_CHAMPI = "https://money.udn.com/money/story/5607/9832133"
TW_DGPA_2027 = "https://focustaiwan.tw/society/202605210014 ; https://www.ettoday.net/news/20260521/3169805.htm"
TW_LAW_2025 = "https://insightplus.bakermckenzie.com/bm/employment-compensation/taiwan-new-public-holidays-take-effect-28-may-2025"
TW_CLOSE = ("https://www.twse.com.tw/downloads/zh/trading/introduce/introduce4-5.pdf ; "
            "https://www.twse.com.tw/staticFiles/product/publication/twse60/html/201/")

TW_A25 = "A: TWSE 2025 market calendar (中華民國114年有價證券集中交易市場開(休)市日期表)"
TW_AP = "A: TWSE announcement, read through press reports of it"
TW_A26 = "A: TWSE 2026 market calendar (115年市場開休市日期)"
TW_B27 = ("B: DGPA 2027 government office calendar (approved 2026-05-21; 121 days off, no make-up workdays); the TWSE "
          "2027 calendar was not out as of the audit date")
TW_SETTLE = "no trading, settlement only (市場無交易，僅辦理結算交割作業): no close is printed"
TW_C27_SETTLE = ("C: inferred; in 2025 and 2026 the two business days before the Lunar New Year block were settlement-only "
                 "days; the TWSE 2027 calendar will fix them")
TWSE = [
    ("2025-01-01", "closed", "Founding Day / New Year (開國紀念日)", TW_A25, TW_2025),
    ("2025-01-23", "closed", "Pre-Lunar New Year, " + TW_SETTLE, TW_A25, TW_2025),
    ("2025-01-24", "closed", "Pre-Lunar New Year, " + TW_SETTLE, TW_A25, TW_2025),
    ("2025-01-27", "closed", "Lunar New Year bridge day (調整放假; made up on Sat 2025-02-08, no trading then)", TW_AP, TW_2025_LNY),
    ("2025-01-28", "closed", "Lunar New Year's Eve (農曆除夕)", TW_AP, TW_2025_LNY + " ; " + TW_2025),
    ("2025-01-29", "closed", "Lunar New Year (春節)", TW_AP, TW_2025_LNY + " ; " + TW_2025),
    ("2025-01-30", "closed", "Lunar New Year (春節)", TW_AP, TW_2025_LNY + " ; " + TW_2025),
    ("2025-01-31", "closed", "Lunar New Year (春節)", TW_AP, TW_2025_LNY + " ; " + TW_2025),
    ("2025-02-28", "closed", "Peace Memorial Day (和平紀念日)", TW_A25, TW_2025),
    ("2025-04-03", "closed", "Children's Day, observed (兒童節)", TW_A25, TW_2025),
    ("2025-04-04", "closed", "Tomb-Sweeping Day (民族掃墓節)", TW_A25, TW_2025),
    ("2025-05-01", "closed", "Labour Day (勞動節)", TW_A25, TW_2025),
    ("2025-05-30", "closed", "Dragon Boat Festival, observed (端午節)", TW_A25, TW_2025),
    ("2025-09-29", "closed", "Teacher's Day, observed (教師節補假; holiday added by the 2025 act)", TW_AP,
     TW_2025_0929 + " ; " + TW_TAIFEX_2025 + " ; " + TW_LAW_2025),
    ("2025-10-06", "closed", "Mid-Autumn Festival (中秋節)", TW_A25, TW_2025 + " ; " + TW_2025_0929),
    ("2025-10-10", "closed", "National Day (國慶日)", TW_A25, TW_2025),
    ("2025-10-24", "closed", "Retrocession Day, observed (臺灣光復紀念日補假; added by the 2025 act)", TW_AP,
     TW_2025_ADDED + " ; " + TW_LAW_2025),
    ("2025-12-25", "closed", "Constitution Day (行憲紀念日; added by the 2025 act)", TW_AP, TW_2025_ADDED + " ; " + TW_LAW_2025),
    ("2026-01-01", "closed", "Founding Day / New Year (開國紀念日)", TW_A26, TW_2026),
    ("2026-02-12", "closed", "Pre-Lunar New Year, " + TW_SETTLE, TW_A26, TW_2026),
    ("2026-02-13", "closed", "Pre-Lunar New Year, " + TW_SETTLE, TW_A26, TW_2026),
    ("2026-02-16", "closed", "Lunar New Year's Eve (農曆除夕)", TW_A26, TW_2026_LNY + " ; " + TW_2026),
    ("2026-02-17", "closed", "Lunar New Year (春節)", TW_A26, TW_2026_LNY),
    ("2026-02-18", "closed", "Lunar New Year (春節)", TW_A26, TW_2026_LNY),
    ("2026-02-19", "closed", "Lunar New Year (春節)", TW_A26, TW_2026_LNY),
    ("2026-02-20", "closed", "Day before Lunar New Year's Eve, observed (小年夜補假)", TW_A26, TW_2026_LNY + " ; " + TW_2026),
    ("2026-02-27", "closed", "Peace Memorial Day, observed (和平紀念日補假)", TW_A26, TW_2026),
    ("2026-04-03", "closed", "Children's Day, observed (兒童節補假)", TW_A26, TW_2026),
    ("2026-04-06", "closed", "Tomb-Sweeping Day, observed (民族掃墓節補假)", TW_A26, TW_2026),
    ("2026-05-01", "closed", "Labour Day (勞動節)", TW_A26, TW_2026),
    ("2026-06-19", "closed", "Dragon Boat Festival (端午節)", TW_A26, TW_2026),
    ("2026-07-10", "closed", "Typhoon Bavi: Taipei work suspension, market closed all day (颱風停止交易)", TW_AP, TW_BAVI),
    ("2026-09-25", "closed", "Mid-Autumn Festival (中秋節)", TW_A26, TW_2026),
    ("2026-09-28", "closed", "Teacher's Day (教師節)", TW_A26, TW_2026),
    ("2026-10-09", "closed", "National Day, observed (國慶日補假)", TW_A26, TW_2026),
    ("2026-10-23", "closed", "Typhoon Champi: Taipei work suspension, market closed all day (颱風停止交易)", TW_AP, TW_CHAMPI),
    ("2026-10-26", "closed", "Retrocession Day, observed (臺灣光復紀念日補假)", TW_A26, TW_2026),
    ("2026-12-25", "closed", "Constitution Day (行憲紀念日)", TW_A26, TW_2026),
    ("2027-01-01", "closed", "Founding Day / New Year (開國紀念日)", TW_B27, TW_DGPA_2027),
    ("2027-02-02", "closed", "Pre-Lunar New Year, " + TW_SETTLE, TW_C27_SETTLE, TW_2025 + " ; " + TW_2026),
    ("2027-02-03", "closed", "Pre-Lunar New Year, " + TW_SETTLE, TW_C27_SETTLE, TW_2025 + " ; " + TW_2026),
    ("2027-02-04", "closed", "Day before Lunar New Year's Eve (小年夜)", TW_B27, TW_DGPA_2027),
    ("2027-02-05", "closed", "Lunar New Year's Eve (農曆除夕)", TW_B27, TW_DGPA_2027),
    ("2027-02-08", "closed", "Lunar New Year (春節)", TW_B27, TW_DGPA_2027),
    ("2027-02-09", "closed", "Lunar New Year, observed (春節補假)", TW_B27, TW_DGPA_2027),
    ("2027-02-10", "closed", "Lunar New Year, observed (春節補假)", TW_B27, TW_DGPA_2027),
    ("2027-03-01", "closed", "Peace Memorial Day, observed (和平紀念日補假)", TW_B27, TW_DGPA_2027),
    ("2027-04-05", "closed", "Tomb-Sweeping Day (民族掃墓節)", TW_B27, TW_DGPA_2027),
    ("2027-04-06", "closed", "Children's Day, observed (兒童節補假)", TW_B27, TW_DGPA_2027),
    ("2027-04-30", "closed", "Labour Day, observed (勞動節補假)", TW_B27, TW_DGPA_2027),
    ("2027-06-09", "closed", "Dragon Boat Festival (端午節)", TW_B27, TW_DGPA_2027),
    ("2027-09-15", "closed", "Mid-Autumn Festival (中秋節)", TW_B27, TW_DGPA_2027),
    ("2027-09-28", "closed", "Teacher's Day (教師節)", TW_B27, TW_DGPA_2027),
    ("2027-10-11", "closed", "National Day, observed (國慶日補假)", TW_B27, TW_DGPA_2027),
    ("2027-10-25", "closed", "Retrocession Day (臺灣光復紀念日)", TW_B27 + "; date derived from the calendar's long-weekend list", TW_DGPA_2027),
    ("2027-12-24", "closed", "Constitution Day, observed (行憲紀念日補假)", TW_B27 + "; date derived from the calendar's long-weekend list", TW_DGPA_2027),
    ("2027-12-31", "closed", "Founding Day 2028, observed (開國紀念日補假)", TW_B27, TW_DGPA_2027),
]

# CME equity index futures (ES / MES): a business day is a day with a regular daily settlement. On every 2025-2026
# date CME equity followed the NYSE list: no settlement on NYSE holidays (a short Globex session's trades go to the
# next trade date), a 12:15 CT halt with a 12:00 CT settlement on NYSE 13:00 ET early closes. 2027 follows the signed
# holidays_NYSE v1.0.0 until CME publishes its 2027 schedule.
CME_F = "https://www.cmegroup.com/tools-information/holiday-calendar/files/"
CME_HOL = "https://www.cmegroup.com/tools-information/holiday-calendar.html"
CME_NOTICE = {
    "2025-01-01": CME_F + "2025-new-years-advisory.pdf",
    "2025-01-09": ("https://www.cmegroup.com/content/dam/cmegroup/notices/ser/2025/01/ser-9499r.pdf ; "
                   "https://www.cmegroup.com/notices/clearing/2025/01/25-012.html"),
    "2025-01-20": CME_F + "2025/mlk-day-holiday-settlement-times-2025.pdf",
    "2025-02-17": CME_F + "2025/presidents-day-holiday-settlement-times-2025.pdf",
    "2025-04-18": CME_F + "2025/2025-good-friday-clearing-advisory.pdf",
    "2025-05-26": CME_F + "2025/memorial-day-holiday-settlement-times-2025.pdf",
    "2025-06-19": CME_F + "2025/juneteenth-day-settlement-times-2025.pdf",
    "2025-07-03": CME_HOL + " ; " + CME_F + "us-independence-day-settlement-times-2024.pdf",
    "2025-07-04": CME_HOL,
    "2025-09-01": CME_F + "2025/labor-day-holiday-settlement-times-2025.pdf",
    "2025-11-27": CME_F + "2025/thanksgiving-holiday-settlement-times-2025.pdf",
    "2025-11-28": CME_F + "2025/thanksgiving-holiday-settlement-times-2025.pdf",
    "2025-12-24": CME_F + "2025/christmas-holiday-settlement-times-2025.pdf",
    "2025-12-25": CME_F + "2025/christmas-holiday-settlement-times-2025.pdf",
    "2026-01-01": CME_F + "2025/new-years-eve-holiday-settlement-times-2026.pdf",
    "2026-01-19": CME_F + "2026/mlk-day-holiday-settlement-times-2026.pdf",
    "2026-02-16": CME_F + "2026/presidents-day-holiday-settlement-times-2026.pdf",
    "2026-04-03": CME_F + "2026/2026-good-friday-clearing-advisory.pdf",
    "2026-05-25": "https://iqhelp.dtn.com/memorial-day-holiday-service-hours-2026/",
    "2026-06-19": CME_F + "2026/juneteenth-day-settlement-times-2026.pdf",
    "2026-07-03": CME_F + "2026/us-independence-day-settlement-times-2026.pdf",
    "2026-09-07": "https://support.tradovate.com/s/article/2026-Holiday-Trading-Hours-Tradovate?language=en_US",
    "2026-11-26": CME_F + "2026/thanksgiving-holiday-settlement-times-2026.pdf",
    "2026-11-27": CME_F + "2026/thanksgiving-holiday-settlement-times-2026.pdf",
    "2026-12-24": CME_F + "2026/christmas-holiday-settlement-times-2026.pdf",
    "2026-12-25": CME_F + "2026/christmas-holiday-settlement-times-2026.pdf",
    "2027-01-01": CME_F + "2026/new-years-eve-holiday-settlement-times-2027.pdf",
}
CME_SPECIAL = {
    "2025-01-09": ("A: CME SER-9499R and clearing advisory 25-012: equity open only to 08:30 CT (NYSE closed for the "
                   "National Day of Mourning) and settlement prices copied forward from 2025-01-08; no new settlement"),
    "2026-04-03": ("A: CME Good Friday clearing advisory: equities open for an abbreviated session (to about 08:15 CT, "
                   "jobs-report day) but not settled; the 2026-04-02 settlement is rolled forward"),
    "2025-11-28": ("A: CME settlement notice, equity settles 12:00 CT; B: halt 12:15 CT (brokers); Globex was down from "
                   "20:40 CT on 11-27 to about 07:30 CT for a data-centre outage, the session then traded"),
    "2026-05-25": "B: no settlement (DTN: the Tuesday 2026-05-26 trade date opens Sunday); CME's own notice not seen",
    "2026-09-07": "B: no settlement (Tradovate: equity halt 12:00 CT, resume 17:00 CT); CME's own notice not seen",
    "2026-12-25": "B: Christmas full close (third-party calendars); CME's 2026 notice excerpt covered only 12-24",
    "2025-07-03": ("B: trade date per CME's 2025 holiday page; halt 12:15 CT (brokers) and 12:00 CT settlement as in "
                   "CME's 2023 and 2024 notices"),
}
CME_CLOSED_A = "A: CME notice: no settlement prices derived for that date (a holiday Globex session's trades go to the next trade date)"
CME_EARLY_A = ("A: CME notice, equity settles 12:00 CT; the 12:15 CT trading halt is from brokers and CME's earlier "
               "schedules (B), not from CME's own 2025-2026 text")
CME_C27 = ("C: CME's 2027 schedule is not out; CME equity matched the NYSE list on every 2025-2026 date, so this row "
           "follows the signed holidays_NYSE v1.0.0")


def _cme_rows() -> list:
    nyse = yaml.safe_load((REPO / "core" / "calendars" / "data" / "holidays_NYSE.yaml").read_text(encoding="utf-8"))
    assert nyse.get("signed_off_by"), "holidays_NYSE must be owner-signed before CME is derived from it"
    out = []
    for r in nyse["rows"]:
        d, kind = r["date"], r["kind"]
        if not COVERS["from"] <= d <= COVERS["to"]:
            continue
        evidence = CME_SPECIAL.get(d) or (CME_C27 if d >= "2027-01-02" else CME_CLOSED_A if kind == "closed" else CME_EARLY_A)
        source = CME_NOTICE.get(d, CME_HOL + " ; " + r["source_url"])
        name = r["name"] + (" (CME equity: halt 12:15 CT, settlement 12:00 CT)" if kind == "early_close" else "")
        out.append((d, kind, name, evidence, source, "12:15") if kind == "early_close" else (d, kind, name, evidence, source))
    return out


CME = _cme_rows()

# market_closes: effective-dated regular closes of CN, HK, TW (US and JP are in the rules store)
CLOSES = [
    {"effective_from": "2015-01-01", "effective_to": None, "market": "CN", "open_local": "09:30", "close_local": "15:00",
     "tz": "Asia/Shanghai", "source_url": SSE_CLOSE_AUCTION,
     "evidence": ("B: SSE trading rules: 09:30-11:30 and 13:00-15:00 CST; from 2018-08-20 the close is a 14:57-15:00 "
                  "call auction (before it, the last-minute VWAP), so the close is 15:00 throughout")},
    {"effective_from": "2015-01-01", "effective_to": "2016-07-24", "market": "HK", "open_local": "09:30",
     "close_local": "16:00", "tz": "Asia/Hong_Kong", "source_url": HK_CAS_PDF + " ; " + HK_CAS_LAUNCH,
     "evidence": "B: before the closing auction the HKEX close was set from the last minute of continuous trading, 16:00"},
    {"effective_from": "2016-07-25", "effective_to": None, "market": "HK", "open_local": "09:30", "close_local": "16:10",
     "tz": "Asia/Hong_Kong", "source_url": HK_HOURS + " ; " + HK_CAS_LAUNCH + " ; " + HSI_GUIDE,
     "evidence": ("A: closing auction session from 2016-07-25, 16:00 to a random close 16:08-16:10; the HSI closing "
                  "index uses the official closing prices, so the close is set by 16:10 (close_print_bound_s is 0)")},
    {"effective_from": "2015-01-01", "effective_to": None, "market": "TW", "open_local": "09:00", "close_local": "13:30",
     "tz": "Asia/Taipei", "source_url": TW_CLOSE,
     "evidence": ("B: TWSE trading system: trading 09:00-13:25 (continuous from 2020-03-23, periodic auctions before), "
                  "then a closing call 13:25-13:30 matched once at 13:30; the close is 13:30 throughout")},
]


def _rows(entries: list) -> list[dict]:
    rows = []
    for e in entries:
        d, kind, name, evidence, source = e[:5]
        row = {"effective_from": d, "effective_to": d, "source_url": source, "retrieved_at_utc": AUDIT_UTC,
               "signed_off_by": None, "date": d, "kind": kind, "name": name}
        if kind == "early_close":
            row["close_local"] = e[5]
        row["evidence"] = evidence
        assert date.fromisoformat(d).weekday() < 5, (d, name)
        rows.append(row)
    rows.sort(key=lambda r: r["date"])
    dates = [r["date"] for r in rows]
    assert len(dates) == len(set(dates)), "duplicate dates"
    return rows


def _closes(entries: list) -> list[dict]:
    return [{"effective_from": e["effective_from"], "effective_to": e["effective_to"], "source_url": e["source_url"],
             "retrieved_at_utc": AUDIT_UTC, "signed_off_by": None, "kind": "close", "market": e["market"],
             "open_local": e["open_local"], "close_local": e["close_local"], "tz": e["tz"], "evidence": e["evidence"]}
            for e in entries]


UNVERIFIED = {
    "holidays_JPX": [
        "rows before 2025 (the Korea-covariance span) are a later version",
        "2027 rows graded B: JPX's 2027 list exists but those rows were read from NAOJ and a secondary list",
        "a closure ordered after the audit date (a change to the National Holidays Act, an outage) is a new version",
    ],
    "holidays_SSE": [
        "rows before 2025 (the Korea-covariance span) are a later version",
        "all 2027 rows are grade C (not announced as of the audit date); replace them with the State Council and SSE "
        "2027 notices in a new version",
    ],
    "holidays_HKEX": [
        "rows before 2025 (the Korea-covariance span) are a later version",
        "half days close at 12:10 (end of the closing auction); severe-weather trading since 2024-09-23 means a "
        "typhoon no longer closes the market, but an 'exceptional situation' closure would be a new version",
    ],
    "holidays_TWSE": [
        "rows before 2025 (the Korea-covariance span) are a later version",
        "2027 rows are the DGPA office calendar (B) and two inferred pre-Lunar-New-Year settlement-only days (C); "
        "replace them with the TWSE 2027 calendar in a new version",
        "typhoon closures are recorded as they happen (the market closes when Taipei suspends work all day or in the "
        "morning); a closure after the audit date is a new version",
    ],
    "holidays_CME": [
        "the set is CME equity index futures (ES, MES): a business day has a regular daily settlement; other CME "
        "products (rates, energy) keep different holiday hours",
        "early_close times are the equity trading halt in America/Chicago (12:15 CT); the settlement is 12:00 CT",
        "2027 rows follow the signed NYSE list (C) until CME publishes its 2027 schedule",
        "rows before 2025 are a later version",
    ],
    "market_closes": ["open_local is informational; only close_local enters the decision clock"],
}
BUILDS = {"holidays_JPX": JPX, "holidays_SSE": SSE, "holidays_HKEX": HK, "holidays_TWSE": TWSE, "holidays_CME": CME}


def main() -> int:
    OUT.mkdir(exist_ok=True)
    diffs = []
    for fid in (*BUILDS, "market_closes"):
        name = f"{fid}.yaml"
        old_text = subprocess.run(["git", "show", f"{DRAFT_REF}:core/calendars/data/{name}"], cwd=REPO, check=True,
                                  capture_output=True, text=True, encoding="utf-8").stdout
        doc = yaml.safe_load(old_text)
        if fid == "market_closes":
            doc["rows"] = _closes(CLOSES)
        else:
            if not BUILDS[fid]:
                print(f"{name}: no rows yet, skipped")
                continue
            doc["covers"] = dict(COVERS)
            doc["rows"] = _rows(BUILDS[fid])
        doc["version"] = VERSION
        doc["status"] = (f"AUDITED, UNSIGNED - proposed v{VERSION} ({REPORT}); refused at load until the owner signs "
                         "(R-20 rule 6, T-CAL-01)")
        doc["unverified"] = UNVERIFIED[fid]
        for k in ("signed_off_by", "signed_utc", "md5"):
            assert doc[k] is None, (fid, k)
        assert all(r["signed_off_by"] is None for r in doc["rows"]), fid
        new_text = yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120)
        (OUT / name).write_text(new_text, encoding="utf-8")
        diffs += difflib.unified_diff(old_text.splitlines(keepends=True), new_text.splitlines(keepends=True),
                                      f"a/core/calendars/data/{name}", f"b/core/calendars/data/{name}")
        print(f"{name}: {len(yaml.safe_load(old_text)['rows'])} -> {len(doc['rows'])} rows, "
              f"covers {doc['covers']['from']}..{doc['covers']['to']}")
    (HERE / "proposed.diff").write_text("".join(diffs), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
