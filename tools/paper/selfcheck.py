"""Self-checks of the research-paper pipeline (spec 5.5). Run by tests/run_all.py as the "papers" suite.

    python -m tools.paper.selfcheck            # run every check
    python -m tools.paper.selfcheck --warm     # build the sample once WITH network to fill the Tectonic cache

The compile checks build a throwaway paper around the real templates with `--only-cached`; they are NOT_RUN
only when the Tectonic binary is absent or its cache lacks a file. A TeX, font or BibTeX error is a FAIL.
The suite never needs the network. `tests()` collects every module-level `test_*` function; later blocks are
inserted above the `if __name__ == "__main__":` block, which stays last.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

import yaml

from tests.notrun import NotRun
from tools.paper import build as B

HERE = Path(__file__).resolve().parent

SAMPLE_NUMBERS = (r"\expandafter\def\csname qg@num@sharpe_12m\endcsname{0.84}" "\n"
                  r"\expandafter\def\csname qg@num@n_obs\endcsname{1{,}250}" "\n")
SAMPLE_MODEL = r"""\begin{equation}\label{eq:mv}
  w^{*} = \frac{1}{\gamma}\,\Sigma^{-1}\mu .
\end{equation}
"""
SAMPLE_BIB = """@article{markowitz1952,
  author = {Markowitz, Harry},
  title = {Portfolio Selection},
  journal = {The Journal of Finance},
  year = {1952},
  volume = {7},
  number = {1},
  pages = {77--91},
  doi = {10.1111/j.1540-6261.1952.tb01525.x}
}
"""

# Lines from real Tectonic 0.17.0 runs (2026-10-23); the natbib and Missing character lines are cut at 79 characters
# exactly as TeX wrote them. The 3.5pt overfull and the underfull lines are typed in to cover the warning branch.
LOG_FIXTURE = r"""LaTeX Warning: Reference `sec:nowhere' on page 1 undefined on input line 5.

Package natbib Warning: Citation `nobody2020' on page 1 undefined on input line
 5.

Missing character: There is no 가 (U+AC00) in font [lmroman10-regular]:mapping=t
ex-text;!

Overfull \hbox (194.92253pt too wide) detected at line 8
\TU/lmr/m/n/10.95 Averyveryveryveryveryverylongwordthatcannotbreak
 []

Overfull \hbox (3.5pt too wide) in paragraph at lines 12--13
 []

Underfull \hbox (badness 10000) in paragraph at lines 14--15
 []

LaTeX Font Warning: Font shape `TU/HANBatang(0)/m/it' undefined
(Font)              using `TU/HANBatang(0)/m/n' instead on input line 62.

! Package qgpaper Error: Undefined number key `nokey'.

LaTeX Warning: There were undefined references.
"""
BLG_FIXTURE = """This is BibTeX, Version 0.99d
The style file: plainnat.bst
Database file #1: ../refs.bib
I was expecting a `,' or a `}'---line 13 of file ../refs.bib
 :
 :   title = {Missing comma},
(Error may have been on previous line)
I'm skipping whatever remains of this entry
I couldn't open database file ../nowhere.bib
---line 4 of file paper_en.aux
Warning--I didn't find a database entry for "nobody2020"
Warning--empty journal in broken1999
(There were 2 error messages)
"""
CLEAN_LOG = """LaTeX2e <2021-11-15> patch level 1
Package: infwarerr 2019/12/03 v1.5 Providing info/warning/error messages (HO)
Package hyperref Info: Hyper figures OFF on input line 4.
"""
CLEAN_BLG = """This is BibTeX, Version 0.99d
The style file: plainnat.bst
Database file #1: ../refs.bib
"""


def _sample_paper(root: Path) -> Path:
    """A throwaway paper dir around the real templates: two numbers, one shared equation, one reference."""
    for sub in ("en", "ko", "study", "common"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    shutil.copyfile(HERE / "template_en.tex", root / "en" / "paper_en.tex")
    shutil.copyfile(HERE / "template_ko.tex", root / "ko" / "paper_ko.tex")
    (root / "study" / "numbers.tex").write_text(SAMPLE_NUMBERS, encoding="utf-8")
    (root / "common" / "model.tex").write_text(SAMPLE_MODEL, encoding="utf-8")
    (root / "refs.bib").write_text(SAMPLE_BIB, encoding="utf-8")
    return root


def _compile(tex: Path) -> B.BuildResult:
    try:
        return B.compile_tex(tex, only_cached=True)
    except B.TectonicMissing as exc:
        raise NotRun(f"OWNER: tectonic binary absent ({exc})") from exc
    except B.CacheMiss as exc:
        raise NotRun(f"REFDATA: Tectonic cache lacks {exc}; run python -m tools.paper.selfcheck --warm") from exc


def _pdf_fonts_and_text(pdf: Path) -> tuple[set[str], str]:
    from pypdf import PdfReader
    reader = PdfReader(str(pdf))
    fonts = {str(f.get_object()["/BaseFont"]).split("+")[-1]
             for page in reader.pages for f in page["/Resources"]["/Font"].values()}
    return fonts, "".join(page.extract_text() for page in reader.pages)


def test_parse_log_sorts_errors_from_warnings():
    errors, warnings = B.parse_log(LOG_FIXTURE, BLG_FIXTURE)
    text = "\n".join(errors)
    for needle in ("Reference `sec:nowhere' on page 1 undefined",
                   "Citation `nobody2020' on page 1 undefined on input line 5.",     # rejoined across the cut
                   "There is no 가 (U+AC00) in font [lmroman10-regular]:mapping=tex-text;!",
                   "Overfull \\hbox (194.92253pt too wide)",
                   "! Package qgpaper Error: Undefined number key `nokey'.",
                   "There were undefined references.",
                   "BibTeX: I was expecting a `,' or a `}'---line 13 of file ../refs.bib",
                   "BibTeX: I couldn't open database file ../nowhere.bib ---line 4 of file paper_en.aux",
                   "BibTeX: (There were 2 error messages)"):
        assert needle in text, (needle, errors)
    assert not any("3.5pt" in e or "Underfull" in e or "Font Warning" in e or "Warning--" in e for e in errors), errors
    joined = "\n".join(warnings)
    for needle in ("Overfull \\hbox (3.5pt too wide)", "Underfull \\hbox (badness 10000)",
                   "LaTeX Font Warning: Font shape `TU/HANBatang(0)/m/it' undefined",
                   'BibTeX: Warning--I didn\'t find a database entry for "nobody2020"'):
        assert needle in joined, (needle, warnings)


def test_parse_log_clean_log_has_no_errors():
    assert B.parse_log(CLEAN_LOG, CLEAN_BLG) == ([], [])
    assert B.parse_log("") == ([], [])


def test_overfull_limit_is_ten_points():
    errors, warnings = B.parse_log("Overfull \\hbox (10.0pt too wide) in paragraph at lines 1--2\n"
                                   "Overfull \\vbox (10.01pt too high) has occurred while \\output is active\n")
    assert len(warnings) == 1 and "(10.0pt too wide)" in warnings[0], warnings
    assert len(errors) == 1 and "(10.01pt too high)" in errors[0], errors


def test_cache_miss_only_for_bare_bundle_files():
    # NOT_RUN for a bundle file the cache lacks; a paper's own missing input, a database or a font stays a FAIL
    for miss in ("! ! LaTeX Error: File `geometry.sty' not found..", "I couldn't open style file apalike.bst",
                 'error: failed to open input file "tectonic-format-latex.tex"'):
        assert B._CACHE_MISS.search(miss), miss
    for real in ("! ! LaTeX Error: File `../study/numbers.tex' not found..",
                 "\\@missingfileerror ...or: File `#1.#2' not found.}",
                 "I couldn't open database file ../refs.bib",
                 '! Package fontspec Error: The font "HANBatang" cannot be found.'):
        assert not B._CACHE_MISS.search(real), real


def test_glossary_seed_has_forty_terms():
    path = HERE / "glossary_ko.yaml"
    glossary = yaml.safe_load(path.read_text(encoding="utf-8"))
    entries = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")]
    assert len(glossary) == len(entries) >= 40, "duplicate or missing glossary keys"
    assert all(isinstance(k, str) and isinstance(v, str) and v.strip() for k, v in glossary.items())
    assert all(re.search(r"[\uac00-\ud7a3]", v) for v in glossary.values()), "every Korean term has Hangul"


def test_compile_template_en():
    with tempfile.TemporaryDirectory(prefix="qgpaper_") as tmp:
        result = _compile(_sample_paper(Path(tmp)) / "en" / "paper_en.tex")
        assert result.ok and not result.errors, result.errors
        assert result.fonts == {}, result.fonts                       # the English edition names no Korean font
        fonts, text = _pdf_fonts_and_text(result.pdf)
        assert "Markowitz (1952)" in text and "0.84" in text and "1,250" in text, text[:400]
        assert {"LMRoman10-Regular-Identity-H", "LMMono10-Regular-Identity-H"} <= fonts, fonts


def test_compile_template_ko():
    with tempfile.TemporaryDirectory(prefix="qgpaper_") as tmp:
        tex = _sample_paper(Path(tmp)) / "ko" / "paper_ko.tex"
        result = _compile(tex)
        assert result.ok and not result.errors, result.errors
        assert set(result.fonts) == set(B.FONT_FILES), result.fonts
        assert all(re.fullmatch(r"[0-9a-f]{64}", h) for h in result.fonts.values()), result.fonts
        fonts, text = _pdf_fonts_and_text(result.pdf)
        # HCRBatang-Bold is the real bold face (\section, \textbf); MalgunGothic is the sans face (\paperstatus)
        assert {"HCRBatang", "HCRBatang-Bold", "MalgunGothic"} <= fonts, fonts
        assert "결과" in text and "참고 문헌" in text and "0.84를" in text, text[:400]
        record = json.loads(B.write_build_record(tex, result).read_text(encoding="utf-8"))
        assert record["fonts"] == {n: {"path": B.FONT_FILES[n], "sha256": h} for n, h in result.fonts.items()}, record
        assert record["tectonic"] == B.TECTONIC_VERSION and record["bundle_url"] == B.BUNDLE_URL, record
        assert record["pdf_sha256"] == hashlib.sha256(result.pdf.read_bytes()).hexdigest(), record


def test_compile_undefined_number_key_is_a_failure():
    with tempfile.TemporaryDirectory(prefix="qgpaper_") as tmp:
        tex = Path(tmp) / "bad.tex"
        tex.write_text("\\documentclass[11pt,a4paper]{article}\n\\usepackage{qgpaper}\n"
                       "\\begin{document}\nx \\qnum{no_such_key} y\n\\end{document}\n", encoding="utf-8")
        result = _compile(tex)
        assert not result.ok and any("Undefined number key `no_such_key'" in e for e in result.errors), result.errors


def tests():
    return sorted((n, v) for n, v in globals().items() if n.startswith("test_") and callable(v))


def warm() -> int:
    """Fill the Tectonic cache: build both sample editions once without --only-cached (needs the network)."""
    root = _sample_paper(Path(tempfile.mkdtemp(prefix="qgpaper_warm_")))
    return B.main([str(root)])


# --------------------------------------------------------------------------- #
# Task 2: numbers.py, consistency.py, approval.py
# --------------------------------------------------------------------------- #
import json as _json              # noqa: E402  (this block's own imports, so it needs nothing from the header)
import re as _re                  # noqa: E402
import subprocess as _subprocess  # noqa: E402
import sys as _sys                # noqa: E402
import tempfile as _tempfile      # noqa: E402
from pathlib import Path as _Path  # noqa: E402

_ROOT = _Path(__file__).resolve().parents[2]


def _num(value, fmt):
    return dict(value=value, fmt=fmt, source="study/runs/r1/results.json:x", selection="all", units="ratio")


def test_numbers_digit_keys_roundtrip():
    """\\qnum keys with digits and underscores round-trip: entries -> numbers.tex and numbers.json -> same text."""
    from tools.paper import numbers as N
    tmp = _Path(_tempfile.mkdtemp(prefix="qgnum_"))
    entries = {"sharpe_2y": _num(0.8123, "{:.2f}"), "r2_10y": _num(0.04567, "{:.3f}"),
               "hit_rate_5d": _num(0.5312, "{:.1%}"), "beta_1m": _num(-0.5, "{:.2f}"), "n_obs": _num(1234, "{:,d}")}
    N.write_numbers(entries, tmp / "study" / "numbers.json", tmp / "study" / "numbers.tex")
    tex = (tmp / "study" / "numbers.tex").read_bytes().decode("utf-8")
    assert "\r" not in tex, "numbers.tex must be written with LF line ends"
    defs = dict(_re.findall(r"(?m)^\\expandafter\\def\\csname qg@num@([a-z0-9_]+)\\endcsname\{(.*)\}$", tex))
    assert defs == {"sharpe_2y": "0.81", "r2_10y": "0.046", "hit_rate_5d": r"53.1\%", "beta_1m": r"\ensuremath{-}0.50",
                    "n_obs": "1,234"}, defs
    rows = N.load_numbers(tmp / "study" / "numbers.json")
    assert set(rows) == set(entries), rows
    for key, entry in entries.items():
        assert {k: rows[key][k] for k in entry} == entry, (key, rows[key])
    assert rows["hit_rate_5d"]["text"] == "53.1%" and rows["beta_1m"]["text"] == "-0.50"


def test_numbers_refuses_bad_keys_missing_fields_and_nonfinite_values():
    from tools.paper import numbers as N
    tmp = _Path(_tempfile.mkdtemp(prefix="qgnum_"))
    bad = [{"Sharpe_2y": _num(1.0, "{:.2f}")}, {"sharpe-2y": _num(1.0, "{:.2f}")}, {"sharpe 2y": _num(1.0, "{:.2f}")},
           {"sharpe_2y\n": _num(1.0, "{:.2f}")}, {"": _num(1.0, "{:.2f}")},
           {"ok_1": {"value": 1.0, "fmt": "{:.2f}"}},
           {"ok_1": _num(float("nan"), "{:.2f}")}, {"ok_1": _num(float("inf"), "{:.2f}")}]
    for entries in bad:
        try:
            N.write_numbers(entries, tmp / "n.json", tmp / "n.tex")
        except ValueError:
            continue
        raise AssertionError(f"accepted {entries}")
    assert not (tmp / "n.json").exists() and not (tmp / "n.tex").exists(), "a refused entry must write nothing"


_EN_TEX = r"""\documentclass[11pt,a4paper]{article}
\usepackage{qgpaper}
\input{../study/numbers.tex}
\begin{document}
\begin{abstract}
% id: abstract-1
Twelve-month carry earns a Sharpe ratio of \qnum{sharpe_2y}.
\end{abstract}

\section{Introduction}\label{sec:intro}
% id: intro-1
Carry trades earn a risk premium \citep{lustig2011}; Section~\ref{sec:results} reports its size.

\section{Data}\label{sec:data}
% id: data-1
The sample spans \qnum{n_months} months.
\begin{tabular}{@{}lr@{}}
\toprule
Statistic & Value \\ \midrule
Months & \qnum{n_months} \\[2pt]
\bottomrule
\end{tabular}

\section{Results}\label{sec:results}
% id: results-1
The Sharpe ratio is \qnum{sharpe_2y} \citep{lustig2011,fama1984}, with $t = 2.1$ and an $R^2$ of \qnum{r2_10y} (Table~\ref{tab:res1}).

% id: results-2
Standard errors follow \citet[p.~1035]{hansen1982}.
\begin{table}[t]\centering
\caption{Main estimates}\label{tab:res1}
\begin{tabular}{@{}lr@{}}
\toprule
Horizon & Sharpe ratio \\ \cmidrule(lr){1-2}
Long & \qnum{sharpe_2y} \\
\bottomrule
\end{tabular}
\end{table}
\includegraphics[width=0.8\linewidth]{figures/fig_1}

\section{Robustness}\label{sec:robustness}
% id: robustness-1
The model is
\begin{equation}\label{eq:carry1}
r_{t+1} = \alpha + 2\beta x_t + \varepsilon_{t+1},
\end{equation}
and \eqref{eq:carry1} holds with \[ \hat\beta_{10} > 0. \]
\end{document}
"""

_KO_TEX = r"""\documentclass[11pt,a4paper]{article}
\usepackage{kotex}
\usepackage{qgpaper}
\input{../study/numbers.tex}
\begin{document}
\begin{abstract}
% id: abstract-1
열두 달 캐리 전략의 샤프 비율은 \qnum{sharpe_2y}이다.
\end{abstract}

\section{서론}\label{sec:intro}
% id: intro-1
캐리 트레이드는 위험 프리미엄을 얻는다 \citep{lustig2011}. 그 크기는 \ref{sec:results}절에서 보고한다.

\section{자료}\label{sec:data}
% id: data-1
표본은 \qnum{n_months}개월에 걸친다.
\begin{tabular}{@{}lr@{}}
\toprule
통계량 & 값 \\ \midrule
개월 수 & \qnum{n_months} \\[2pt]
\bottomrule
\end{tabular}

\section{결과}\label{sec:results}
% id: results-1
샤프 비율은 \qnum{sharpe_2y}이며 \citep{lustig2011,fama1984}, $t = 2.1$이고 $R^2$는 \qnum{r2_10y}이다(표~\ref{tab:res1}).

% id: results-2
표준오차는 \citet[p.~1035]{hansen1982}를 따른다.
\begin{table}[t]\centering
\caption{주요 추정치}\label{tab:res1}
\begin{tabular}{@{}lr@{}}
\toprule
기간 & 샤프 비율 \\ \cmidrule(lr){1-2}
장기 & \qnum{sharpe_2y} \\
\bottomrule
\end{tabular}
\end{table}
\includegraphics[width=0.8\linewidth]{figures/fig_1}

\section{강건성}\label{sec:robustness}
% id: robustness-1
모형은 다음과 같다.
\begin{equation}\label{eq:carry1}
r_{t+1} = \alpha + 2\beta x_t + \varepsilon_{t+1},
\end{equation}
그리고 \eqref{eq:carry1}은 \[ \hat\beta_{10} > 0 \]에서 성립한다.
\end{document}
"""
_TABLE_TEX = r"""\begin{tabular}{@{}lr@{}}
\specialrule{.8pt}{0pt}{0pt}
Horizon & Sharpe ratio \\ \cline{1-2}
Long & \qnum{sharpe_2y} \\
\bottomrule
\end{tabular}
"""


def _consistency(*ko_edits) -> list[str]:
    """check() on the fixture pair after applying (old, new) replacements to the Korean edition."""
    from tools.paper import consistency as C
    ko = _KO_TEX
    for old, new in ko_edits:
        assert ko.count(old) == 1, old
        ko = ko.replace(old, new)
    tmp = _Path(_tempfile.mkdtemp(prefix="qgcons_"))
    for ed, text in (("en", _EN_TEX), ("ko", ko)):
        (tmp / ed).mkdir()
        (tmp / ed / f"paper_{ed}.tex").write_text(text, encoding="utf-8")
    return C.check(tmp)


def test_consistency_clean_pair_passes():
    """Math, \\qnum, \\cite[p.~1035], \\ref, \\label, colspecs, \\cmidrule(lr){1-2}, \\\\[2pt] and graphics options
    are not bare numbers, and a faithful pair has no problem."""
    from tools.paper import consistency as C
    assert _consistency() == [], _consistency()
    assert C.check(_Path(_tempfile.mkdtemp(prefix="qgcons_"))) == ["en/paper_en.tex missing", "ko/paper_ko.tex missing"]


def test_consistency_bare_digit_in_results_and_tables():
    probs = _consistency(("$t = 2.1$이고", "t 값은 2.1이고"))
    assert probs and all(p.startswith("bare number ko sec:results: ") and "2.1" in p for p in probs), probs
    probs = _consistency((r"개월 수 & \qnum{n_months}", "개월 수 & 120"))
    assert any(p.startswith("bare number ko tabular: ") and "120" in p for p in probs), probs
    assert "qnum sec:data: count differs en/ko {'n_months': (2, 1)}" in probs, probs


def test_consistency_missing_cite_key_in_ko():
    probs = _consistency((r"\citep{lustig2011,fama1984}", r"\citep{lustig2011}"))
    assert probs == ["cite sec:results: only in en ['fama1984'], only in ko []"], probs


def test_consistency_per_section_qnum_count_drift():
    probs = _consistency((r"샤프 비율은 \qnum{sharpe_2y}이며", "샤프 비율은 높으며"))
    assert probs == ["qnum sec:results: count differs en/ko {'sharpe_2y': (2, 1)}"], probs
    # the same total, moved to another section, is still a drift in both sections
    probs = _consistency((r"$R^2$는 \qnum{r2_10y}이다", "$R^2$는 높다"),
                         (r"\qnum{n_months}개월에 걸친다.", r"\qnum{n_months}개월에 걸친다(\qnum{r2_10y})."))
    assert probs == ["qnum sec:data: count differs en/ko {'r2_10y': (0, 1)}",
                     "qnum sec:results: count differs en/ko {'r2_10y': (1, 0)}"], probs


def test_consistency_dropped_paragraph_id():
    probs = _consistency(("% id: results-2\n", ""))
    assert probs == ["ids: ko lacks paragraph ids ['results-2']"], probs


def test_consistency_follows_input_into_table_files():
    """A table \\input from <edition>/tables/ is checked where it appears; \\cline and \\specialrule are layout."""
    from tools.paper import consistency as C
    tmp = _Path(_tempfile.mkdtemp(prefix="qgcons_"))
    anchor = r"\includegraphics[width=0.8\linewidth]{figures/fig_1}"
    for ed, text in (("en", _EN_TEX), ("ko", _KO_TEX)):
        (tmp / ed / "tables").mkdir(parents=True)
        (tmp / ed / "tables" / "main.tex").write_text(_TABLE_TEX, encoding="utf-8")
        (tmp / ed / f"paper_{ed}.tex").write_text(text.replace(anchor, "\\input{tables/main}\n" + anchor),
                                                  encoding="utf-8")
    assert C.check(tmp) == [], C.check(tmp)
    (tmp / "ko" / "tables" / "main.tex").write_text(_TABLE_TEX.replace(r"\qnum{sharpe_2y}", "0.81"), encoding="utf-8")
    probs = C.check(tmp)
    assert any(p.startswith("bare number ko tabular: ") and "0.81" in p for p in probs), probs
    assert "qnum sec:results: count differs en/ko {'sharpe_2y': (3, 2)}" in probs, probs


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if sys.argv[1:] == ["--warm"]:
        raise SystemExit(warm())
    bad = 0
    for name, fn in tests():
        try:
            fn()
            print(f"PASS {name}")
        except NotRun as exc:
            print(f"NOT_RUN {name}: {exc.reason}")
        except Exception as exc:
            bad += 1
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    print(f"{len(tests()) - bad}/{len(tests())} passed or not run")
    raise SystemExit(1 if bad else 0)
