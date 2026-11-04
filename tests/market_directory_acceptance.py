"""Unified symbol directory: code or name search over domestic and overseas stocks.

Network is blocked throughout; KIS stock masters are synthetic text in the KIS
fixed-width layout (core/market/directory.py marks that layout UNVERIFIED).
"""
from __future__ import annotations

import ast
import importlib.util
import io
import os
from pathlib import Path
import random
import re
import subprocess
import sys
import threading
import time
import unittest
from unittest.mock import patch
import zipfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import dotenv
with patch.object(dotenv, "load_dotenv", return_value=False):
    from data import kis_markets as km

from core.market import directory, symbols
from core.market.directory import Listing, SymbolDirectory, default_directory
from core.market.models import Instrument
from core.research.watchlist import KR_STOCK_SPECS

ROOT = Path(__file__).resolve().parents[1]
HAS_QT = importlib.util.find_spec("PyQt6") is not None
HANGUL = re.compile("[\u1100-\u11ff\u3130-\u318f\ua960-\ua97f\uac00-\ud7a3\ud7b0-\ud7ff]")
TAIL = {"kospi": 227, "kosdaq": 221}     # fixed-width fields without the line break


def master_line(code, name, group="ST", *, market="kospi", width=None, isin=None):
    """One master line: short code (9), standard code (12), name, fixed-width tail."""
    width = TAIL[market] if width is None else width
    isin = isin or ("KR7" + (code + "000000")[:6] + "003")
    tail = (group + "2" + "0" * width)[:width]
    return code.ljust(9) + isin + name.ljust(20) + tail


def master_text(rows, *, market="kospi", width=None):
    return "\n".join(master_line(*row, market=market, width=width) for row in rows) + "\n"


def loader_for(kospi_rows=(), kosdaq_rows=(), *, kospi=None, kosdaq=None):
    texts = {"kospi_code": kospi if kospi is not None else master_text(kospi_rows),
             "kosdaq_code": kosdaq if kosdaq is not None else master_text(kosdaq_rows, market="kosdaq")}
    calls = []

    def load(name):
        calls.append(name)
        return texts[name]
    load.calls = calls
    return load


def loaded(kospi_rows=(), kosdaq_rows=(("900100", "코스닥기본"),)):
    d = SymbolDirectory(master_loader=loader_for(kospi_rows, kosdaq_rows))
    d.load_domestic()
    assert d.domestic_loaded and d.error is None, d.error
    return d


def codes(results):
    return [listing.code for listing in results]


class Network(unittest.TestCase):
    def setUp(self):
        deny = patch("requests.sessions.Session.request", side_effect=AssertionError("Network forbidden"))
        deny.start()
        self.addCleanup(deny.stop)


class RankingTests(Network):
    def test_categories_rank_in_the_documented_order(self):
        # Listed in reverse so list order cannot explain the result.
        d = loaded([("900003", "테크1234"), ("123456", "베타"), ("900002", "1234테크"),
                    ("900001", "1234"), ("001234", "알파")])
        self.assertEqual(codes(d.search("1234")), ["001234", "900001", "900002", "123456", "900003"])
        # exact name < substring < 초성 prefix < 초성 substring for a 초성 query.
        d = loaded([("900013", "마가나다"), ("900012", "가나다라"), ("900011", "마ㄱㄴㄷ"), ("900010", "ㄱㄴㄷ")])
        self.assertEqual(codes(d.search("ㄱㄴㄷ")), ["900010", "900011", "900012", "900013"])

    def test_one_character_queries_match_prefixes_only(self):
        d = loaded([("900021", "나가"), ("900020", "가나")])
        self.assertEqual(codes(d.search("가")), ["900020"])
        self.assertEqual(codes(d.search("ㄱ", assets="domestic_stock")), ["900020"])

    def test_ties_go_to_kind_then_script_then_list_order(self):
        d = loaded([("900035", "오메가기타", "BC"), ("900031", "오메가ETF", "EF"), ("900032", "오메가리츠", "RT"),
                    ("900033", "오메가ETN", "EN"), ("900034", "오메가전자", "ST"), ("900036", "오메가전자2", "ST")])
        self.assertEqual(codes(d.search("오메가")),
                         ["900034", "900036", "900031", "900033", "900032", "900035"])
        kinds = {listing.code: listing.kind for listing in d.search("오메가")}
        self.assertEqual(kinds, {"900031": "etf", "900032": "reit", "900033": "etn",
                                 "900034": "stock", "900035": "other", "900036": "stock"})
        # Code prefixes from both assets merge in tie order.
        d = loaded([("720002", "칠이공ETF", "EF"), ("720001", "칠이공")])
        self.assertEqual([(x.exchange, x.code) for x in d.search("720")],
                         [("TSE", "7203"), ("", "720001"), ("", "720002")])
        self.assertEqual(codes(d.search("720", assets="domestic_stock")), ["720001", "720002"])
        self.assertEqual(codes(d.search("720", limit=1, assets=["domestic_stock"])), ["720001"])
        # Same bucket and kind: Hangul query puts domestic first, Latin query overseas first.
        d = loaded([("900040", "애플"), ("900041", "APPLE")])
        self.assertEqual([(x.asset, x.code) for x in d.search("애플")[:2]],
                         [("domestic_stock", "900040"), ("overseas_stock", "AAPL")])
        self.assertEqual([(x.asset, x.code) for x in d.search("apple")[:2]],
                         [("overseas_stock", "AAPL"), ("domestic_stock", "900041")])

    def test_a_word_of_a_domestic_name_is_not_an_exact_name(self):
        # KIS names ETNs '<issuer> <product> ETN'; the issuer word must not outrank the issuer's stock.
        d = loaded([("005930", "삼성전자"), ("530036", "삼성 레버리지 WTI원유 선물 ETN", "EN")])
        self.assertEqual(d.search("삼성")[0].code, "005930")
        self.assertEqual(codes(d.search("삼성")), ["005930", "207940", "530036"])
        self.assertIsNone(d.resolve("삼성"))
        products = ("레버리지 WTI원유 선물", "인버스 2X WTI원유 선물", "레버리지 구리 선물", "KRX 금현물",
                    "레버리지 천연가스 선물", "인버스 천연가스 선물", "레버리지 은 선물", "인버스 은 선물", "레버리지 금 선물")
        etns = [(f"5300{i:02d}", f"삼성 {product} ETN", "EN") for i, product in enumerate(products)]
        d = loaded(etns + [("580001", "KB 레버리지 금 선물 ETN", "EN"), ("500001", "신한 레버리지 WTI원유 선물 ETN", "EN"),
                           ("006400", "삼성SDI"), ("055550", "신한지주")])
        found = d.search("삼성")
        self.assertEqual(len(found), 8)
        self.assertEqual(codes(found)[:3], ["005930", "207940", "006400"])
        self.assertEqual([x.kind for x in found], ["stock"] * 3 + ["etn"] * 5)
        self.assertEqual(codes(d.search("KB")), ["105560", "580001"])
        self.assertEqual(codes(d.search("신한")), ["055550", "500001"])
        # A word inside a domestic name is still found, as a substring.
        self.assertIn("530000", codes(d.search("레버리지", limit=20)))
        self.assertIn("530000", codes(d.search("ㄹㅂㄹㅈ", limit=20)))
        # Name prefix outranks substring whatever the kind: the ETF's name starts with the query.
        d = loaded([("900091", "알파 베타"), ("900090", "베타플러스", "EF")])
        self.assertEqual(codes(d.search("베타", assets="domestic_stock")), ["900090", "900091"])
        self.assertEqual(codes(d.search("ㅂㅌ", assets="domestic_stock")), ["900090", "900091"])

    def test_words_of_bundled_overseas_names_still_count_as_name_prefixes(self):
        # The bundled overseas Korean names list alternative names ('알파벳 A 구글', '메타 페이스북').
        d = loaded([("011780", "금호석유")])
        self.assertEqual(codes(d.search("구글")), ["GOOGL", "GOOG"])
        self.assertEqual(codes(d.search("페이스북"))[:1], ["META"])
        self.assertEqual(codes(d.search("ㄱㄱ", assets="overseas_stock"))[:2], ["GOOGL", "GOOG"])
        self.assertIsNone(d.resolve("구글"))
        # ...but never as exact names: a stock's name prefix ranks before the ETF's word '금'.
        self.assertEqual(codes(d.search("금")), ["011780", "GLD"])

    def test_domestic_code_forms_normalise(self):
        d = SymbolDirectory(master_loader=loader_for())
        for text in ("005930", "A005930", "a005930", "005930.KS", "005930.KQ", "005930.ks", "5930", " 005930 "):
            with self.subTest(text=text):
                self.assertEqual(d.search(text)[0].code, "005930")
                self.assertEqual(d.resolve(text).code, "005930")
        self.assertEqual(d.lookup("domestic_stock", "5930").name_ko, "삼성전자")
        self.assertEqual(d.lookup("domestic_stock", "A005930").code, "005930")
        self.assertIsNone(d.lookup("domestic_stock", "AAPL"))
        self.assertEqual(d.lookup("overseas_stock", "aapl").exchange, "NAS")
        self.assertEqual(d.lookup("overseas_stock", "AAPL", "NAS").code, "AAPL")
        self.assertIsNone(d.lookup("overseas_stock", "AAPL", "NYS"))
        self.assertIsNone(d.lookup("overseas_stock", "005930"))
        # A code typed as written beats its zero-padded domestic reading.
        d = loaded([("000700", "패딩테스트")])
        self.assertEqual((d.search("00700")[0].exchange, d.resolve("00700").exchange), ("HKS", "HKS"))
        self.assertEqual(d.resolve("700").code, "000700")

    def test_resolve_needs_one_exact_match(self):
        d = loaded([("900050", "동명"), ("900051", "동명"), ("900052", "단독이름")])
        self.assertEqual(codes(d.search("동명")), ["900050", "900051"])
        self.assertIsNone(d.resolve("동명"))
        self.assertEqual(d.resolve("단독이름").code, "900052")
        self.assertEqual(d.resolve("단독 이름").code, "900052")    # separators are ignored
        self.assertIsNone(d.resolve("단독"))                       # a prefix is not a name
        self.assertIsNone(d.resolve(""))
        self.assertIsNone(d.resolve("a"))                          # one word of 'Alphabet A' is not a name
        self.assertEqual(d.resolve("Apple").code, "AAPL")
        self.assertEqual(d.resolve("애플", assets=("overseas_stock",)).code, "AAPL")
        self.assertIsNone(d.resolve("애플", assets=("domestic_stock",)))
        self.assertEqual(d.resolve("900050").name_ko, "동명")       # the code is never ambiguous

    def test_overseas_expectations_of_the_bundled_search_still_hold(self):
        d = SymbolDirectory(master_loader=loader_for())
        expected = {"apple": ("AAPL", "NAS"), "애플": ("AAPL", "NAS"), "AAPL": ("AAPL", "NAS"),
                    "aapl": ("AAPL", "NAS"), "tsm": ("TSM", "NYS"), "tsmc": ("TSM", "NYS"),
                    "엔비": ("NVDA", "NAS"), "ㅌㅅㄹ": ("TSLA", "NAS"), "spy": ("SPY", "AMS"),
                    "텐센트": ("00700", "HKS"), "7203": ("7203", "TSE"), "microsoft": ("MSFT", "NAS")}
        for query, listing in expected.items():
            with self.subTest(query=query):
                first = d.search(query)[0]
                self.assertEqual((first.code, first.exchange), listing)
                self.assertEqual(first.asset, "overseas_stock")
        self.assertEqual(symbols.search("애플")[0].code, "AAPL")   # tools/packaging/smoke_installed.py
        kinds = {(x.exchange, x.code): x.kind for x in d.search("etf", limit=50, assets="overseas_stock")}
        self.assertEqual(kinds[("AMS", "SPY")], "etf")
        self.assertEqual(d.lookup("overseas_stock", "GLD").kind, "etf")
        self.assertEqual(d.lookup("overseas_stock", "O").kind, "reit")
        self.assertEqual(d.lookup("overseas_stock", "AAPL").kind, "stock")

    def test_limits_assets_and_odd_input(self):
        d = SymbolDirectory(master_loader=loader_for())
        self.assertEqual(d.search(""), [])
        self.assertEqual(d.search("   "), [])
        self.assertEqual(d.search(None), [])
        self.assertEqual(d.search("zzzz"), [])
        self.assertEqual(d.search("a", limit=0), [])
        self.assertEqual(d.search("a", limit=-3), [])
        self.assertEqual(d.search("a", limit="x"), [])
        self.assertEqual(len(d.search("a", limit=3)), 3)
        self.assertEqual(len(d.search("a")), 8)
        self.assertIsInstance(d.search("a"), list)
        self.assertEqual(d.search("삼성", assets=("overseas_stock",)), [])
        self.assertEqual({x.asset for x in d.search("s", limit=50, assets="domestic_stock")}, {"domestic_stock"})
        self.assertEqual(d.search("삼성", assets=("bond",)), [])
        self.assertEqual(d.search("삼\x00성"), d.search("삼성"))


class SeedTests(Network):
    def test_seed_is_searchable_offline_without_any_loader_call(self):
        load = loader_for()
        d = SymbolDirectory(master_loader=load)
        self.assertFalse(d.domestic_loaded)
        self.assertIsNone(d.error)
        expected = {"삼성": "005930", "ㅅㅅㅈㅈ": "005930", "samsung": "005930", "하이닉스": "000660",
                    "hynix": "000660", "현대차": "005380", "kb financial": "105560",
                    "kb financial group": "105560", "엘지에너지": None, "LG에너지": "373220",
                    "바이오로직스": "207940"}
        for query, code in expected.items():
            with self.subTest(query=query):
                found = d.search(query, assets="domestic_stock")
                self.assertEqual(found[0].code if found else None, code)
        self.assertEqual(load.calls, [])

    def test_seed_names_match_the_home_tables(self):
        d = SymbolDirectory(master_loader=loader_for())
        tree = ast.parse((ROOT / "quantgen_desktop/watchlist.py").read_text(encoding="utf-8"))
        names = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                     and any(getattr(t, "id", "") == "_NAMES" for t in node.targets))
        for name_ko, code, _english in KR_STOCK_SPECS:
            listing = d.lookup("domestic_stock", code)
            self.assertEqual((listing.name_ko, listing.name_en, listing.kind), (name_ko, names[code][1], "stock"))
            self.assertEqual(names[code][0], name_ko)
        self.assertEqual(len(d.search("", assets="domestic_stock")), 0)

    def test_import_and_singleton_load_nothing(self):
        probe = ("import sys\nimport core.market.directory as d\nfrom core.market import symbols\n"
                 "heavy = sorted(m for m in sys.modules if m.split('.')[0] in "
                 "('PyQt6', 'data', 'config', 'requests', 'numpy', 'pandas', 'dotenv'))\n"
                 "print(heavy, symbols.entries.cache_info().currsize, d._DEFAULT is None)\n")
        out = subprocess.run([sys.executable, "-B", "-c", probe], cwd=ROOT, capture_output=True,
                             text=True, timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout.strip(), "[] 0 True")
        with patch.object(directory, "_DEFAULT", None), \
                patch.object(directory, "_kis_master_text", side_effect=AssertionError("download")):
            first = default_directory()
            self.assertIs(first, default_directory())
            self.assertFalse(first.domestic_loaded)
            self.assertEqual(first.search("삼성전자")[0].code, "005930")


class MasterParseTests(Network):
    def test_synthetic_kospi_and_kosdaq_masters_parse(self):
        kospi = [("005930", "삼성전자"), ("005380", "현대자동차"), ("005935", "삼성전자우"), ("069500", "KODEX 200", "EF"),
                 ("530036", "삼성 레버리지 WTI원유 선물 ETN", "EN"), ("088980", "맥쿼리인프라", "IF"),
                 ("330590", "롯데리츠", "RT"), ("0072R0", "알파벳코드ETF", "EF"),
                 ("Q500001", "큐코드ETN", "EN")]
        kosdaq = [("247540", "에코프로비엠"), ("091990", "셀트리온헬스케어"), ("035720", "중복카카오")]
        kosdaq_text = master_text(kosdaq, market="kosdaq") + master_line("005930", "중복삼성", market="kosdaq")
        bad = "\n".join(["", "   ", "short line", "005930   KR7005930003",
                         "삼성전자 ".ljust(9) + "KR7005930003" + "깨진행".ljust(20) + "ST" + "0" * 225,
                         "123456   KR7123456003" + "제어\x01문자".ljust(20) + "ST" + "0" * 225,
                         "123457   KR7123457003" + "깨짐\ufffd".ljust(20) + "ST" + "0" * 225,
                         "123458   KR7123458003" + "한글꼬리".ljust(20) + "ST" + "가" * 225,
                         "123459   KR7123459003" + "숫자그룹".ljust(20) + "12" + "0" * 225])
        load = loader_for(kospi=master_text(kospi) + bad + "\n", kosdaq=kosdaq_text)
        d = SymbolDirectory(master_loader=load)
        added = d.load_domestic()
        self.assertEqual(load.calls, ["kospi_code", "kosdaq_code"])
        self.assertTrue(d.domestic_loaded)
        self.assertIsNone(d.error)
        got = {code: (d.lookup("domestic_stock", code).name_ko, d.lookup("domestic_stock", code).kind)
               for code in ("005930", "005935", "069500", "530036", "088980", "330590", "247540", "091990")}
        self.assertEqual(got, {"005930": ("삼성전자", "stock"), "005935": ("삼성전자우", "stock"),
                               "069500": ("KODEX 200", "etf"), "530036": ("삼성 레버리지 WTI원유 선물 ETN", "etn"),
                               "088980": ("맥쿼리인프라", "other"), "330590": ("롯데리츠", "reit"),
                               "247540": ("에코프로비엠", "stock"), "091990": ("셀트리온헬스케어", "stock")})
        for code in ("0072R0", "Q500001", "123456", "123457", "123458", "123459"):
            self.assertIsNone(d.lookup("domestic_stock", code), code)
        self.assertEqual(d.lookup("domestic_stock", "005930").name_en, "Samsung Electronics")  # seed merged
        # A seed stock keeps the name Home shows; a different master name still finds it.
        self.assertEqual(d.lookup("domestic_stock", "005380").name_ko, "현대차")
        self.assertEqual(d.search("현대자동차")[0].code, "005380")
        self.assertEqual(d.resolve("현대차").code, "005380")
        self.assertEqual(d.search("중복삼성"), [])            # a code seen in KOSPI is not taken twice
        self.assertEqual(d._counts["kospi_code"]["non_numeric_code"], 2)
        self.assertEqual(d._counts["kospi_code"]["malformed"], 7)
        self.assertEqual(d._counts["kosdaq_code"]["duplicate"], 1)
        # 7 KOSPI + 3 KOSDAQ listings, minus Samsung and Hyundai (already seed rows).
        self.assertEqual(added, 8)
        self.assertEqual(d.search("ㅋㄷㅅ200")[:1], [])        # mixed 초성/Latin is not an initials query
        self.assertEqual(d.search("에코프로")[0].code, "247540")
        self.assertEqual(d.search("ㅇㅋㅍㄹ")[0].code, "247540")
        self.assertEqual(d.search("kodex")[0].kind, "etf")
        for row in d._index.rows:
            listing = row.listing
            Instrument(listing.asset, listing.code, listing.exchange)   # raises on an invalid code
        self.assertEqual(d.load_domestic(), 0)                 # a reload adds nothing new
        self.assertTrue(d.domestic_loaded)

    def test_both_tail_widths_parse(self):
        # The KIS samples count the line break in the 228/222 widths; accept either reading.
        for extra in (0, 1):
            with self.subTest(extra=extra):
                kospi = master_text([("111110", "넓이시험", "EF")], width=TAIL["kospi"] + extra)
                kosdaq = master_text([("222220", "코스닥넓이")], market="kosdaq", width=TAIL["kosdaq"] + extra)
                d = SymbolDirectory(master_loader=loader_for(kospi=kospi, kosdaq=kosdaq))
                self.assertEqual(d.load_domestic(), 2)
                self.assertEqual((d.lookup("domestic_stock", "111110").name_ko,
                                  d.lookup("domestic_stock", "111110").kind), ("넓이시험", "etf"))
                self.assertEqual(d.lookup("domestic_stock", "222220").name_ko, "코스닥넓이")

    def test_default_loader_is_the_keyless_kis_master_kept_in_memory(self):
        def archive(name, text):
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w") as zf:
                zf.writestr(name + ".mst", text.encode("cp949"))
            return buffer.getvalue()

        bodies = {"kospi_code": archive("kospi_code", master_text([("000270", "기아")])),
                  "kosdaq_code": archive("kosdaq_code", master_text([("196170", "알테오젠")], market="kosdaq"))}
        urls = []

        class Response:
            def __init__(self, content):
                self.status_code, self.content = 200, content

        class Transport:
            def get(self, url, timeout):
                urls.append(url)
                return Response(bodies[url.rsplit("/", 1)[1].split(".")[0]])

        for name in directory.DOMESTIC_MASTERS:
            self.addCleanup(km._MASTER_CACHE.pop, name, None)
            km._MASTER_CACHE.pop(name, None)
        d = SymbolDirectory()
        refuse = AssertionError("no file may be opened")
        with patch.object(km, "_requests", Transport()), patch("builtins.open", side_effect=refuse), \
                patch("io.open", side_effect=refuse), patch("os.open", side_effect=refuse):
            added = d.load_domestic()
        self.assertIsNone(d.error)
        self.assertEqual(added, 2)
        self.assertEqual(urls, [km.MASTER_URL + "kospi_code.mst.zip", km.MASTER_URL + "kosdaq_code.mst.zip"])
        self.assertEqual(km.MASTER_URL, "https://new.real.download.dws.co.kr/common/master/")
        self.assertEqual(d.search("기아")[0].code, "000270")
        self.assertEqual(d.resolve("알테오젠").code, "196170")
        source = (ROOT / "core/market/directory.py").read_text(encoding="utf-8")
        self.assertNotRegex(source, r"\bopen\(|write_text|write_bytes|\.write\(|mkdir|tempfile|pickle|sqlite|shelve")


class LoadFailureTests(Network):
    def test_loader_errors_keep_the_seed_and_set_a_short_reason(self):
        cases = {"raise": RuntimeError("master kospi_code: HTTP 403 https://secret.example/?k=v"),
                 "empty": "", "garbage": "nothing like a master\n" * 3, "type": None}
        for label, outcome in cases.items():
            with self.subTest(case=label):
                def load(name, outcome=outcome):
                    if isinstance(outcome, Exception):
                        raise outcome
                    return outcome
                d = SymbolDirectory(master_loader=load)
                self.assertEqual(d.load_domestic(), 0)
                self.assertFalse(d.domestic_loaded)
                self.assertTrue(d.error and d.error.startswith("kospi_code: ") and len(d.error) <= 80, d.error)
                self.assertNotIn("secret", d.error)
                self.assertEqual(d.search("삼성전자")[0].code, "005930")
                self.assertEqual(d.search("apple")[0].code, "AAPL")
        d = SymbolDirectory(master_loader=load)
        self.assertEqual(d.error, None)
        d = SymbolDirectory(master_loader=lambda name: (_ for _ in ()).throw(RuntimeError("HTTP 403")))
        d.load_domestic()
        self.assertEqual(d.error, "kospi_code: RuntimeError HTTP 403")

    def test_kosdaq_failure_discards_kospi_and_a_later_success_clears_the_error(self):
        state = {"fail": True}

        def load(name):
            if name == "kosdaq_code" and state["fail"]:
                raise OSError("timed out")
            return master_text([("900060", "부분로드")] if name == "kospi_code" else [("900061", "코스닥로드")],
                               market="kospi" if name == "kospi_code" else "kosdaq")
        d = SymbolDirectory(master_loader=load)
        self.assertEqual(d.load_domestic(), 0)
        self.assertEqual(d.error, "kosdaq_code: OSError")
        self.assertEqual(d.search("부분로드"), [])
        state["fail"] = False
        self.assertEqual(d.load_domestic(), 2)
        self.assertIsNone(d.error)
        self.assertTrue(d.domestic_loaded)
        # A failed refresh keeps the loaded list.
        state["fail"] = True
        self.assertEqual(d.load_domestic(), 0)
        self.assertTrue(d.domestic_loaded and d.error == "kosdaq_code: OSError")
        self.assertEqual(d.search("부분로드")[0].code, "900060")


def synthetic_rows(count, seed=7):
    rnd = random.Random(seed)
    syllables = "가나다라마바사아자차카타파하삼성전자현대기아엘지에스케이한화롯데신세계셀트리온카카오네이버포스코두산"
    suffixes = ("", "전자", "홀딩스", "바이오", "제약", "건설", "화학", "증권", "우", "", "", "")
    rows = []
    for i in range(count):
        name = "".join(rnd.choice(syllables) for _ in range(rnd.randint(2, 4))) + rnd.choice(suffixes)
        if i % 9 == 0:
            name = rnd.choice(("KODEX ", "TIGER ", "ACE ", "SOL ")) + name
        group = "EF" if i % 9 == 0 else ("EN" if i % 97 == 0 else "ST")
        rows.append((f"{100000 + i:06d}", name, group))
    return rows


class ConcurrencyAndScaleTests(Network):
    def test_search_during_a_load_sees_the_old_or_the_new_list(self):
        rows = synthetic_rows(12000)
        texts = {"kospi_code": master_text(rows[:7000] + [("900070", "스레드시험")]),
                 "kosdaq_code": master_text(rows[7000:], market="kosdaq")}
        gate = threading.Event()

        def load(name):
            gate.wait(10)
            return texts[name]
        d = SymbolDirectory(master_loader=load)
        failures, searches = [], 0
        worker = threading.Thread(target=lambda: failures.append(d.load_domestic() <= 0), daemon=True)
        worker.start()
        gate.set()
        deadline = time.monotonic() + 30
        while worker.is_alive() and time.monotonic() < deadline:
            first = d.search("삼성전자")[0]
            found = codes(d.search("스레드시험"))
            if first.code != "005930" or found not in ([], ["900070"]):
                failures.append((first, found))
            searches += 1
        worker.join(10)
        self.assertFalse(worker.is_alive())
        self.assertEqual(failures, [False])
        self.assertGreater(searches, 0)
        self.assertTrue(d.domestic_loaded)
        self.assertEqual(codes(d.search("스레드시험")), ["900070"])

    def test_queries_take_at_most_15_ms_on_15000_rows(self):
        rows = synthetic_rows(15000 - 126)
        d = SymbolDirectory(master_loader=loader_for(kospi=master_text(rows[:9000]),
                                                      kosdaq=master_text(rows[9000:], market="kosdaq")))
        d.load_domestic()
        self.assertIsNone(d.error)
        self.assertGreaterEqual(len(d._index.rows), 15000)
        worst = {}
        for query in ("삼성", "삼성전자", "005930", "5930", "A005930", "ㅅ", "ㅅㅅ", "ㅅㅅㅈㅈ", "가", "전자",
                      "samsung", "a", "kodex", "1", "10", "1000", "하이닉스", "apple", "zzzz", "바이오", "ㅎㄷ"):
            best = min(self._timed(d, query) for _ in range(3))
            worst[query] = best
        self.assertLessEqual(max(worst.values()), 0.015, {k: round(v * 1000, 2) for k, v in worst.items()})

    @staticmethod
    def _timed(d, query):
        start = time.perf_counter()
        d.search(query)
        return time.perf_counter() - start


class LabelTests(Network):
    def test_english_labels_never_contain_hangul(self):
        d = loaded(synthetic_rows(300))
        listings = list(d._index.rows)
        self.assertGreater(len(listings), 400)
        for row in listings:
            listing = row.listing
            self.assertTrue(listing.label("ko"))
            english = listing.label("en")
            self.assertTrue(english)
            self.assertIsNone(HANGUL.search(english), listing)
            self.assertIsNone(HANGUL.search(listing.label("en_US")), listing)
        plain = Listing("domestic_stock", "123456", "", "한글이름", "", "stock")
        self.assertEqual((plain.label("ko"), plain.label("en")), ("한글이름", "123456"))
        mixed = Listing("domestic_stock", "123456", "", "", "한글 Mixed", "etf")
        self.assertEqual((mixed.label("ko"), mixed.label("en")), ("한글 Mixed", "123456"))
        self.assertEqual(Listing("overseas_stock", "AAPL", "NAS", "", "", "stock").label("ko"), "AAPL")
        with self.assertRaises(ValueError):
            Listing("bond", "1", "", "", "", "stock")
        with self.assertRaises(ValueError):
            Listing("domestic_stock", "123456", "", "", "", "fund")


@unittest.skipUnless(HAS_QT, "PyQt6 is not installed")
class BundledFontTests(Network):
    def test_every_bundled_and_seed_name_renders_with_the_bundled_font(self):
        from PyQt6.QtGui import QRawFont
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])   # keep a reference: QRawFont needs a live app
        self.assertIsNotNone(app)
        d = SymbolDirectory(master_loader=loader_for())
        names = {text for row in d._index.rows
                 for text in (row.listing.name_ko, row.listing.name_en, row.listing.code)}
        self.assertGreaterEqual(len(names), 3 * 120)
        for face in ("qg-interface.otf", "qg-interface-medium.otf", "qg-interface-semibold.otf"):
            raw = QRawFont(str(ROOT / "assets/fonts" / face), 16)
            self.assertTrue(raw.isValid(), face)
            missing = sorted({char for text in names for char in text
                              if not char.isspace() and not raw.supportsCharacter(ord(char))})
            self.assertEqual(missing, [], face)


if __name__ == "__main__":
    unittest.main()
