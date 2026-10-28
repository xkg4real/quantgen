"""Build the proposed v1.0.0 kr_regime_tags file (audit report docs/audit/2026-10-27/08_kr_regime_tags.md).

Reads the v0.1.0 draft as committed before the audits (git DRAFT_REF), applies the audited change list below and
writes proposed/ plus proposed.diff. It never touches core/calendars/data/ and never writes a signature.

    python docs/audit/2026-10-27/calendar_batch4/build_proposed.py
"""
from __future__ import annotations

import difflib
import subprocess
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
OUT = HERE / "proposed"
DRAFT_REF = "1f63f91"
AUDIT_UTC = "2026-10-28T12:30:00Z"
REPORT = "docs/audit/2026-10-27/08_kr_regime_tags.md"
VERSION = "1.0.0"

# --------------------------------------------------------------------------- #
# Sources (search-engine excerpts on 2026-10-28)
# --------------------------------------------------------------------------- #
PL_WIKI = "https://ko.wikipedia.org/wiki/%EA%B0%80%EA%B2%A9%EC%A0%9C%ED%95%9C%ED%8F%AD"
PL_MIRAE = "https://securities.miraeasset.com/bbs/download/2034052.pdf?attachmentId=2034052"
HERALD_HOURS = "https://biz.heraldcorp.com/article/967855"
HK_1998_SAT = "https://www.hankookilbo.com/news/article/199812010033710380"
HK_1998_HOURS = "https://www.hankookilbo.com/news/article/199812240073584153"
HK_2000_LUNCH = "https://www.hankookilbo.com/news/article/200005130027413996"
CALL_PAPER = "http://www.korfin.org/korfin_file/forum/28-4-02.pdf"            # 2001-09-03 이전 14:50~15:00 종가 동시호가
RANDOM_END = "https://dic.hankyung.com/economy/view/?seq=9817"               # 2005년 도입
RANDOM_END_DAY = "https://www.sedaily.com/article/10339893"                  # "지난 1월26일 도입한 임의종료"
FX_1990 = "https://www.seoul.co.kr/news/1990/02/21/19900221007009"
FX_1997 = "https://www.imaeil.com/page/view/1997121615414071950"
FX_PAPER = "https://koreascience.kr/article/JAKO201022442401805.pub?lang=ko"
SS_KCMI = "https://www.kcmi.re.kr/common/downloadw.php?fid=25847&fgu=002002&fty=004003"
SS_ZDNET = "https://zdnet.co.kr/view/?no=20190807140948"
SS_FIN_2013 = "https://www.etoday.co.kr/news/view/821115"
TAX_2025 = "https://www.mt.co.kr/economy/2025/12/01/2025120108471236062"
TAX_2026 = "https://taxtimes.co.kr/news/article.html?no=272624"
TICK_2023 = "https://news.mtn.co.kr/news-detail/2022110114103274390"
LETF_2026 = "https://www.heraldk.com/article/2026012917335613316"
LETF_LAUNCH = "https://core.asiae.co.kr/article/2026051518184211131"
FX_2024 = "https://www.etoday.co.kr/news/view/2370025"


def _row(tag, lo, hi, value, src, evidence, unit=None):
    r = {"effective_from": lo, "effective_to": hi, "source_url": src, "retrieved_at_utc": AUDIT_UTC,
         "signed_off_by": None, "tag": tag, "value": value}
    if unit:
        r["unit"] = unit
    r["evidence"] = evidence
    return r


def rows() -> list[dict]:
    out = []
    add = lambda *a, **k: out.append(_row(*a, **k))
    # price_limit: every step confirmed (A); pre-1995-04 was a 17-step fixed-amount band schedule, no single fraction
    add("price_limit", "1995-01-01", "1995-03-31", None, PL_WIKI,
        "A: 1995-04-01 이전 17단계 정액제(평균 약 4.6%), 단일 비율 없음 -> null 유지", unit="fraction")
    for lo, hi, v in (("1995-04-01", "1996-11-24", 0.06), ("1996-11-25", "1998-03-01", 0.08),
                      ("1998-03-02", "1998-12-06", 0.12), ("1998-12-07", "2015-06-14", 0.15)):
        add("price_limit", lo, hi, v, f"{PL_WIKI}; {PL_MIRAE}", "A: 유가증권시장 가격제한폭 변천표와 일치", unit="fraction")
    add("price_limit", "2015-06-15", None, 0.3, f"{PL_WIKI}; spec L2038", "A: 2015-06-15 ±30%", unit="fraction")
    # saturday_session (consistent with the signed kr_sessions v1.0.0 and T-SAT-01)
    add("saturday_session", "1995-01-01", "1998-12-11", True, HK_1998_SAT, "A: 1998-12-12부터 토요 휴장")
    add("saturday_session", "1998-12-12", None, False, HK_1998_SAT, "A: 토요 휴장")
    add("close_time_kst", "1995-01-01", "2016-07-31", "15:00", f"{HERALD_HOURS}; spec L2010", "A: 장 마감 15:00")
    add("close_time_kst", "2016-08-01", None, "15:30", f"{HERALD_HOURS}; spec L2010", "A: 2016-08-01 30분 연장")
    add("closing_call", "1995-01-01", "2016-07-31", "14:50-15:00", f"{CALL_PAPER}; spec L2011",
        "B: 2001-09-03 이전에도 종가 14:50~15:00 동시호가(논문); 1995~2000 구간은 같은 시간대로 추정")
    add("closing_call", "2016-08-01", None, "15:20-15:30", f"{HERALD_HOURS}; spec L2011", "A: 종가 단일가 15:20~15:30")
    # random_end: CHANGE RT-03 - conditional random end was introduced in 2005, not in force from 1995
    add("random_end", "1995-01-01", "2005-01-25", "none", f"{RANDOM_END}; {RANDOM_END_DAY}",
        "B: 랜덤엔드(임의종료)는 2005년 도입; 그 전에는 없음")
    add("random_end", "2005-01-26", "2015-06-14", "conditional", f"{RANDOM_END}; {RANDOM_END_DAY}; spec L2012",
        "B: '2005년 도입'(용어사전)과 '1월 26일 도입'(서울경제) 결합; 예상체결가 급변 종목만 최대 5분 연장")
    add("random_end", "2015-06-15", None, "unconditional_le_30s", "spec L2012",
        "A: 2015-06-15 모든 단일가매매에 30초 이내 랜덤엔드")
    # lunch_break: CHANGE RT-01 - 11:30-13:00 until 1998-12-06 (same fix as kr_sessions KS-02)
    add("lunch_break", "1995-01-01", "1998-12-06", "11:30-13:00", f"{HERALD_HOURS}; {HK_1998_HOURS}",
        "A: 오전장 09:30~11:30, 오후장 13:00~15:00 (kr_sessions v1.0.0과 일치)")
    add("lunch_break", "1998-12-07", "2000-05-21", "12:00-13:00", f"{HK_1998_HOURS}; {HK_2000_LUNCH}",
        "A: 1998-12-07 점심 30분 단축; 2000-05-22 폐지")
    add("lunch_break", "2000-05-22", None, "none", HK_2000_LUNCH, "A: 2000-05-22 점심 휴장 폐지")
    # fx_regime: CHANGE RT-04 - name the regimes around the spec's peg_1997 window instead of null
    add("fx_regime", "1995-01-01", "1997-09-21", "market_average_rate", f"{FX_1990}; {FX_PAPER}",
        "A: 1990-03 시장평균환율제 (일일 변동폭 제한)")
    add("fx_regime", "1997-09-22", "1997-10-17", "peg_1997", "spec L2041",
        "B: 스펙이 정한 구간 이름(T-REGIME-01: 1997-10-01 = peg_1997); 제도상으로는 시장평균환율제 기간")
    add("fx_regime", "1997-10-18", "1997-12-15", "market_average_rate", f"{FX_1997}; {FX_PAPER}",
        "A: 시장평균환율제 (1997-11-20 변동폭 확대 포함)")
    add("fx_regime", "1997-12-16", None, "free_float", f"{FX_1997}; {FX_PAPER}",
        "B: 1997-12-16 변동폭 폐지·자유변동환율제 (논문은 12-15로 표기)")
    add("etf_available", "1995-01-01", "2002-10-13", False, "spec L2042", "A: KODEX 200 2002-10-14 상장 전")
    add("etf_available", "2002-10-14", None, True, "spec L2042", "A: 2002-10-14 국내 첫 ETF 상장")
    # short selling: CHANGE RT-02 - 2011 ban from 08-10; financials banned 2008-10-01 .. 2013-11-13
    ban = [("1995-01-01", "2008-09-30", False, "none", "A: 금지 없음"),
           ("2008-10-01", "2009-05-31", True, "full_ban", "A: 2008-10-01 전 종목 금지"),
           ("2009-06-01", "2011-08-09", False, "partial_ban_financials",
            "A: 2009-06-01 비금융주 재개, 금융주는 계속 금지(2013-11-14 재개)"),
           ("2011-08-10", "2011-11-09", True, "full_ban", "A: 2011-08-10부터 3개월 전 종목 금지"),
           ("2011-11-10", "2013-11-13", False, "partial_ban_financials",
            "A: 2011-11-10 비금융주 재개, 금융주는 2013-11-13까지 금지"),
           ("2013-11-14", "2020-03-15", False, "none", "A: 2013-11-14 금융주 공매도 재개"),
           ("2020-03-16", "2021-05-02", True, "full_ban", "A: 2020-03-16 전 종목 금지"),
           ("2021-05-03", "2023-11-05", False, "partial_ban_non_index", "A: 2021-05-03 코스피200·코스닥150만 재개"),
           ("2023-11-06", "2025-03-30", True, "full_ban", "A: 2023-11-06 전 종목 금지"),
           ("2025-03-31", None, False, "none", "A: 2025-03-31 전면 재개")]
    for lo, hi, b, regime, ev in ban:
        src = f"{SS_KCMI}; {SS_ZDNET}; {SS_FIN_2013}" if lo < "2014" else "spec L2043 (GV-210/216/217)"
        add("short_sale_ban", lo, hi, b, src, ev + " (부분 금지 기간은 false, short_sale_regime이 구분)")
        add("short_sale_regime", lo, hi, regime, src, ev)
    # sell_tax_pct (KOSPI: securities transaction tax + rural special tax, percent)
    add("sell_tax_pct", "1995-01-01", "2019-05-29", 0.3, "spec L2044 anchor (2019)",
        "B: 2019년 0.30%(거래세 0.15+농특세 0.15) 기준값; 1995~1996년 단계는 법령 연혁으로 확인하지 못함", unit="percent")
    for lo, hi, v in (("2019-05-30", "2020-12-31", 0.25), ("2021-01-01", "2022-12-31", 0.23),
                      ("2023-01-01", "2023-12-31", 0.2), ("2024-01-01", "2024-12-31", 0.18),
                      ("2025-01-01", "2025-12-31", 0.15)):
        add("sell_tax_pct", lo, hi, v, f"{TAX_2025}; spec L2044", "A: 거래세 단계 인하 + 농특세 0.15", unit="percent")
    add("sell_tax_pct", "2026-01-01", None, 0.2, f"{TAX_2026}; spec L2044",
        "A: 2026-01-01 거래세 0.05 + 농특세 0.15 (ETF 면제)", unit="percent")
    add("tick_regime", "1995-01-01", "2023-01-24", "pre_2023_reform", TICK_2023, "A: 2023-01-25 개편 전")
    add("tick_regime", "2023-01-25", "2023-12-10", "stocks_reformed_2023_01_25", f"{TICK_2023}; spec L2045",
        "A: 주식 호가단위 개편·시장 간 통일")
    add("tick_regime", "2023-12-11", None, "stocks_reformed_etf_w1_tick_below_w2000", "spec L2045",
        "B: ETF 2,000원 미만 1원 호가 시행일은 스펙 값(검색으로 확인 못 함)")
    add("letf_rules", "1995-01-01", "2026-05-26", "none", "spec L2046", "A: 단일종목 레버리지 상품 없음")
    add("letf_rules", "2026-05-27", "2026-07-15", "single_stock_letf_rule_2026_05_27", f"{LETF_2026}; {LETF_LAUNCH}; spec L2046",
        "A: 단일종목 레버리지 ETF 2026-05-27 출시")
    add("letf_rules", "2026-07-16", None, "single_stock_letf_rule_2026_07_16", "spec L2046",
        "B: 2026-07-16 규칙 변경은 스펙 값(검색으로 확인 못 함)")
    add("usdkrw_onshore_hours", "1995-01-01", "2016-07-31", "close_15:00", "spec L2047", "A: 마감 15:00")
    add("usdkrw_onshore_hours", "2016-08-01", "2024-06-30", "close_15:30", f"{FX_2024}; spec L2047", "A: 마감 15:30")
    add("usdkrw_onshore_hours", "2024-07-01", "2026-07-05", "close_02:00_next_day", FX_2024,
        "A: 서울외환시장운영협의회 의결, 2024-07-01부터 익일 02:00")
    add("usdkrw_onshore_hours", "2026-07-06", None, "24h", "spec L2047 / L1305",
        "B: 2026-07-06 24시간 거래는 스펙 값(검색으로 확인 못 함)")
    add("value_up", "1995-01-01", "2024-02-25", "pre_value_up", "spec (GV-218)", "A: 밸류업 발표 전")
    add("value_up", "2024-02-26", None, "post_value_up_2024_02_26", "spec (GV-218)", "A: 2024-02-26 밸류업 프로그램 발표")
    return out


def main() -> int:
    OUT.mkdir(exist_ok=True)
    name = "kr_regime_tags.yaml"
    old_text = subprocess.run(["git", "show", f"{DRAFT_REF}:core/calendars/data/{name}"], cwd=REPO, check=True,
                              capture_output=True, text=True, encoding="utf-8").stdout
    doc = yaml.safe_load(old_text)
    n_old = len(doc["rows"])
    doc["rows"] = rows()
    doc["version"] = VERSION
    doc["status"] = (f"AUDITED, UNSIGNED - proposed v{VERSION} ({REPORT}); refused at load until the owner signs "
                     "(R-20 rule 6, T-CAL-01)")
    doc["unverified"] = [
        "price_limit before 1995-04-01 stays null (a 17-step fixed-amount schedule, no single fraction)",
        "sell_tax_pct 1995-2019: one 0.30% row; the 1990s steps were not confirmed from the statute history",
        "random_end conditional start 2005-01-26 combines two sources (year and day)",
        "spec values not confirmed by search: ETF 1-won tick 2023-12-11, letf rule 2026-07-16, 24h FX 2026-07-06, "
        "the peg_1997 window",
        "new short_sale_regime value partial_ban_financials (financial stocks only, 2009-06-01..2013-11-13)",
        "T-REGIME-01 expected-values file (full-range clause) is still an owner deliverable",
    ]
    for k in ("signed_off_by", "signed_utc", "md5"):
        assert doc[k] is None, k
    new_text = yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120)
    (OUT / name).write_text(new_text, encoding="utf-8")
    (HERE / "proposed.diff").write_text("".join(difflib.unified_diff(
        old_text.splitlines(keepends=True), new_text.splitlines(keepends=True),
        f"a/core/calendars/data/{name}", f"b/core/calendars/data/{name}")), encoding="utf-8")
    print(f"{name}: {n_old} -> {len(doc['rows'])} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
