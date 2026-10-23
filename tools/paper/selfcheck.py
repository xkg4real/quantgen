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


def test_approval_detects_changed_scope_file():
    """The write workflow's deterministic refusal: a scope file changed, removed or added after approval."""
    from tools.paper import approval as A
    tmp = _Path(_tempfile.mkdtemp(prefix="qgappr_"))
    (tmp / "scope").mkdir()
    for name in ("questions.md", "protocol.md", "prereg.json"):
        (tmp / "scope" / name).write_text(f"{name}\n", encoding="utf-8")
    assert A.check(tmp) == ["scope/approval.json missing: the owner has not approved this scope"]
    for words in ("", "   "):
        try:
            A.approve(tmp, words, "2026-10-23T00:00:00Z")
        except ValueError:
            continue
        raise AssertionError(f"approved with owner words {words!r}")
    record = A.approve(tmp, "I approve this scope as written", "2026-10-23T00:00:00Z")
    assert record == tmp / "scope" / "approval.json" and A.check(tmp) == []
    saved = _json.loads(record.read_text(encoding="utf-8"))
    assert sorted(saved["files"]) == ["scope/prereg.json", "scope/protocol.md", "scope/questions.md"], saved
    assert saved["owner_words"] == "I approve this scope as written" and saved["approved_utc"] == "2026-10-23T00:00:00Z"

    def cli() -> int:
        return _subprocess.run([_sys.executable, "-m", "tools.paper.approval", "check", str(tmp)], cwd=_ROOT,
                               capture_output=True, text=True, encoding="utf-8").returncode

    assert cli() == 0
    (tmp / "scope" / "protocol.md").write_text("protocol.md\none more variant\n", encoding="utf-8")
    assert A.check(tmp) == ["scope/protocol.md changed after approval"], A.check(tmp)
    assert cli() == 1
    (tmp / "scope" / "protocol.md").write_text("protocol.md\n", encoding="utf-8")
    assert A.check(tmp) == []                                   # restored byte for byte
    (tmp / "scope" / "questions.md").unlink()
    (tmp / "scope" / "extra.md").write_text("x\n", encoding="utf-8")
    assert A.check(tmp) == ["scope/questions.md removed after approval", "scope/extra.md added after approval"]


# --------------------------------------------------------------------------- #
# Task 3: refs.yaml verification, the claims gate and study runs (offline)
# --------------------------------------------------------------------------- #
import tempfile                    # noqa: E402
from pathlib import Path           # noqa: E402

import yaml                        # noqa: E402

_REFS_NOW = "2026-10-23T00:00:00Z"
_REFS_KCARRY = {"key": "koijen2018carry", "type": "article",
                "authors": ["Koijen, Ralph S. J.", "Moskowitz, Tobias J.", "Pedersen, Lasse Heje", "Vrugt, Evert B."],
                "year": 2018, "title": "Carry", "venue": "Journal of Financial Economics", "volume": 127,
                "pages": "197-225", "doi": "10.1016/j.jfineco.2017.11.002", "class": "published"}
_REFS_KCARRY_URL = "https://api.crossref.org/works/10.1016/j.jfineco.2017.11.002"
_REFS_CROSSREF = {"status": "ok", "message": {"DOI": "10.1016/j.jfineco.2017.11.002", "title": ["Carry"]}}
_REFS_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2101.00001v2</id>
    <title>An Offline
      Fixture Title</title>
  </entry>
</feed>
"""


def _refs_fetcher(table: dict):
    """Offline stand-in for refs.default_fetch: answers from `table`, records every URL asked."""
    calls = []

    def fetch(url):
        calls.append(url)
        return table.get(url)

    fetch.calls = calls
    return fetch


def test_refs_crossref_record_ok_and_mismatch():
    from tools.paper import refs as R
    fetch = _refs_fetcher({_REFS_KCARRY_URL: _REFS_CROSSREF})
    rec = R.verify_entry(dict(_REFS_KCARRY), fetch=fetch, now_utc=_REFS_NOW)
    assert fetch.calls == [_REFS_KCARRY_URL], fetch.calls
    assert rec == {"method": "doi", "url": _REFS_KCARRY_URL, "retrieved_utc": _REFS_NOW, "fetched_title": "Carry",
                   "ok": True}, rec
    wrong = dict(_REFS_KCARRY, title="Carry Trades Everywhere")
    assert R.verify_entry(wrong, fetch=fetch, now_utc=_REFS_NOW)["ok"] is False
    gone = R.verify_entry(dict(_REFS_KCARRY), fetch=_refs_fetcher({}), now_utc=_REFS_NOW)   # unreachable or 404
    assert gone["ok"] is False and gone["fetched_title"] == "", gone
    # Crossref escapes HTML entities and keeps markup in titles; neither makes a correct DOI entry fail
    amp = {"status": "ok", "message": {"title": ["Carry &amp; <i>Value</i>"]}}
    rec = R.verify_entry(dict(_REFS_KCARRY, title="Carry & Value"), fetch=_refs_fetcher({_REFS_KCARRY_URL: amp}),
                         now_utc=_REFS_NOW)
    assert rec["ok"] is True and rec["fetched_title"] == "Carry & <i>Value</i>", rec


def test_refs_arxiv_atom_fixture():
    from tools.paper import refs as R
    parsed = R.parse_arxiv_atom(_REFS_ATOM)
    assert parsed == {"entries": [{"id": "http://arxiv.org/abs/2101.00001v2",
                                   "title": "An Offline Fixture Title"}]}, parsed
    url = "http://export.arxiv.org/api/query?id_list=2101.00001"
    entry = {"key": "fixture2021", "type": "misc", "authors": ["Doe, Jane"], "year": 2021,
             "title": "An offline fixture title", "arxiv": "2101.00001", "class": "working_paper"}
    rec = R.verify_entry(entry, fetch=_refs_fetcher({url: parsed}), now_utc=_REFS_NOW)
    assert rec["method"] == "arxiv" and rec["url"] == url and rec["ok"] is True, rec
    other = dict(entry, arxiv="2101.00002")          # the feed answers for a different id
    rec = R.verify_entry(other, fetch=_refs_fetcher({"http://export.arxiv.org/api/query?id_list=2101.00002": parsed}),
                         now_utc=_REFS_NOW)
    assert rec["ok"] is False, rec


def test_refs_verify_file_records_manual_and_problems():
    from tools.paper import refs as R
    book = {"key": "hamilton1994", "type": "book", "authors": ["Hamilton, James D."], "year": 1994,
            "title": "Time Series Analysis", "venue": "Princeton University Press",
            "url": "https://press.princeton.edu/", "class": "book"}
    fetch = _refs_fetcher({_REFS_KCARRY_URL: _REFS_CROSSREF})
    with tempfile.TemporaryDirectory(prefix="qgrefs_") as d:
        path = Path(d) / "refs.yaml"
        path.write_text(yaml.safe_dump([dict(_REFS_KCARRY), book], allow_unicode=True, sort_keys=False),
                        encoding="utf-8")
        problems = R.verify_file(path, fetch=fetch, now_utc=_REFS_NOW)
        assert problems == ["hamilton1994: not verified (manual: fetched '')"], problems
        assert b"\r\n" not in path.read_bytes(), "refs.yaml is rewritten with LF line ends"
        saved = R.load_refs(path)
        assert saved[0]["verified"]["ok"] is True and saved[1]["verified"]["method"] == "manual", saved
        saved[1]["verified"].update(ok=True, fetched_title="Time Series Analysis")     # the agent's manual check
        path.write_text(yaml.safe_dump(saved, allow_unicode=True, sort_keys=False), encoding="utf-8")
        assert R.verify_file(path, fetch=fetch, now_utc="2026-10-24T00:00:00Z") == []
        kept = R.load_refs(path)[1]["verified"]
        assert kept["ok"] is True and kept["retrieved_utc"] == _REFS_NOW, kept
        assert R.ref_problems([dict(book)]) == ["hamilton1994: no verified record"]


def test_refs_write_bib_and_schema_refusals():
    from tools.paper import refs as R
    with tempfile.TemporaryDirectory(prefix="qgrefs_") as d:
        bib = Path(d) / "refs.bib"
        R.write_bib([dict(_REFS_KCARRY, title="Carry & Value_Spread")], bib)
        assert bib.read_bytes().decode("utf-8") == (
            "@article{koijen2018carry,\n"
            "  author = {Koijen, Ralph S. J. and Moskowitz, Tobias J. and Pedersen, Lasse Heje and Vrugt, Evert B.},\n"
            "  year = {2018},\n"
            "  title = {{Carry \\& Value\\_Spread}},\n"
            "  journal = {Journal of Financial Economics},\n"
            "  volume = {127},\n"
            "  pages = {197--225},\n"
            "  doi = {10.1016/j.jfineco.2017.11.002},\n"
            "}\n"), bib.read_bytes()
        path = Path(d) / "refs.yaml"
        for bad, needle in (([_REFS_KCARRY, dict(_REFS_KCARRY)], "duplicate key"),
                            ([dict(_REFS_KCARRY, **{"class": "slides"})], "class 'slides'"),
                            ([dict(_REFS_KCARRY, authors=[])], "missing ['authors']")):
            path.write_text(yaml.safe_dump(bad, sort_keys=False), encoding="utf-8")
            try:
                R.load_refs(path)
            except ValueError as exc:
                assert needle in str(exc), exc
            else:
                raise AssertionError(f"load_refs accepted an entry with {needle}")


_CLAIMS_TEX = r"""\documentclass{article}
\begin{document}
\section{Introduction}\label{sec:intro}
% id: intro-1
Carry is introduced by \citet{koijen2018carry}.

\section{Literature}
\label{sec:literature}
\subsection{Canonical treatment}\label{sec:literature-canon}
% id: literature-1
Carry is defined by \citet{koijen2018carry}; curve factors follow \citep[p.~55]{litterman1991common}.
% A commented \cite{ghost2020} is not a citation.

\section{Results}\label{sec:results}
% id: results-1
\Citet{koijen2018carry} define the carry ranking used here.
\end{document}
"""
_CLAIM_ROWS = [
    {"id": "c1", "paragraph_id": "literature-1", "source_key": "koijen2018carry", "locator": "p. 197, eq. (1)",
     "support": "Carry is the futures return when the spot price stays unchanged.", "status": "supported"},
    {"id": "c2", "paragraph_id": "literature-1", "source_key": "litterman1991common", "locator": "p. 55",
     "support": "Level, steepness and curvature explain most bond-return variance.", "status": "supported"},
    {"id": "c3", "paragraph_id": "results-1", "source_key": "koijen2018carry", "locator": "section 2",
     "support": "The carry definition used for the ranking.", "status": "supported"},
]


def _claims_paper(d: Path, rows, *, litterman_ok: bool = True) -> Path:
    """A paper dir with en/paper_en.tex, refs.yaml (verified records) and claims.yaml."""
    paper = d / "paper"
    (paper / "en").mkdir(parents=True)
    (paper / "en" / "paper_en.tex").write_text(_CLAIMS_TEX, encoding="utf-8")
    rec = {"method": "doi", "url": _REFS_KCARRY_URL, "retrieved_utc": _REFS_NOW, "fetched_title": "Carry", "ok": True}
    litterman = {"key": "litterman1991common", "type": "article", "authors": ["Litterman, Robert",
                 "Scheinkman, Jose"], "year": 1991, "title": "Common Factors Affecting Bond Returns",
                 "venue": "Journal of Fixed Income", "volume": 1, "pages": "54-61",
                 "doi": "10.3905/jfi.1991.692347", "class": "published", "verified": dict(rec, ok=litterman_ok)}
    refs = [dict(_REFS_KCARRY, verified=rec), litterman]
    (paper / "refs.yaml").write_text(yaml.safe_dump(refs, sort_keys=False), encoding="utf-8")
    (paper / "claims.yaml").write_text(yaml.safe_dump(rows, sort_keys=False), encoding="utf-8")
    return paper


def test_claims_gate_passes_on_a_supported_paper():
    from tools.paper import claims as C
    paras = C.paragraphs(_CLAIMS_TEX)
    assert [(s, p) for s, p, _ in paras] == [("intro", "intro-1"), ("literature", "literature-1"),
                                             ("results", "results-1")], paras
    assert C.cite_keys(paras[1][2]) == ["koijen2018carry", "litterman1991common"], paras[1][2]
    assert C.cite_keys(paras[2][2]) == ["koijen2018carry"], paras[2][2]               # \Citet is a citation too
    with tempfile.TemporaryDirectory(prefix="qgclaims_") as d:
        assert C.check(_claims_paper(Path(d), _CLAIM_ROWS)) == []     # intro-1 is not a gated section


def test_claims_gate_fails_on_unread_unsupported_missing_and_unverified():
    from tools.paper import claims as C
    c1, c2, c3 = _CLAIM_ROWS
    cases = [
        ([dict(c1, status="unread", support=""), c2, c3], True, "claim c1: status unread blocks release"),
        ([dict(c1, status="unread", support=""), c2, c3], True,
         "literature-1: \\cite{koijen2018carry} has no supported claims.yaml row"),
        ([c1, dict(c2, status="unsupported"), c3], True, "claim c2: status unsupported blocks release"),
        ([c1, c2], True, "results-1: \\cite{koijen2018carry} has no supported claims.yaml row"),
        (_CLAIM_ROWS, False, "claim c2: source litterman1991common is not verified ok"),
        ([c1, c2, c3, dict(c3, id="c4", source_key="ghost2020")], True,
         "claim c4: source 'ghost2020' not in refs.yaml"),
        ([c1, c2, c3, dict(c3, id="c5", paragraph_id="results-9")], True, "claim c5: paragraph 'results-9' not in"),
        ([c1, c2, dict(c3, locator="")], True, "claim c3: missing ['locator']"),
    ]
    with tempfile.TemporaryDirectory(prefix="qgclaims_") as d:
        for i, (rows, ok, needle) in enumerate(cases):
            problems = C.check(_claims_paper(Path(d) / str(i), rows, litterman_ok=ok))
            assert any(needle in p for p in problems), (needle, problems)
        # a citation inside an \input file belongs to the paragraph that inputs it
        paper = _claims_paper(Path(d) / "input", _CLAIM_ROWS)
        (paper / "en" / "tables").mkdir()
        (paper / "en" / "tables" / "cites.tex").write_text("Curve factors \\citep{litterman1991common}.\n",
                                                           encoding="utf-8")
        tex = paper / "en" / "paper_en.tex"
        tex.write_text(tex.read_text(encoding="utf-8").replace("used here.", "used here.\n\\input{tables/cites}"),
                       encoding="utf-8")
        assert C.check(paper) == ["results-1: \\cite{litterman1991common} has no supported claims.yaml row"], \
            C.check(paper)
        assert C.check(Path(d) / "nowhere") == ["missing en/paper_en.tex", "missing claims.yaml", "missing refs.yaml"]

        def variant(name, rows, *edits):
            p = _claims_paper(Path(d) / name, rows)
            t = p / "en" / "paper_en.tex"
            text = t.read_text(encoding="utf-8")
            for old, new in edits:
                assert old in text, old
                text = text.replace(old, new)
            t.write_text(text, encoding="utf-8")
            return C.check(p)

        # a section is named by the first \label{sec:..} anywhere in its \section chunk, never by the section before it
        assert [(s, p) for s, p, _ in C.paragraphs(
            "\\section{A}\\label{sec:intro}\n% id: intro-1\nx\n\\section{Results}\n% id: results-1\ny \\citet{ghost}")
        ] == [("intro", "intro-1"), ("", "results-1")]
        assert [(s, p) for s, p, _ in C.paragraphs(
            "\\section{Results}\n% id: results-1\ny \\citet{ghost}\n\\label{sec:results}")] == [("results", "results-1")]
        unlabelled = "\\section{Results} has no \\label{sec:...}; the claims gate cannot tell which section it is"
        assert variant("nolabel", _CLAIM_ROWS, ("\\section{Results}\\label{sec:results}", "\\section{Results}")) \
            == [unlabelled]
        assert variant("lateid", [c1, c2], ("\\section{Results}\\label{sec:results}\n", "\\section{Results}\n"),
                       ("ranking used here.", "ranking used here.\n\\label{sec:results}")) \
            == ["results-1: \\cite{koijen2018carry} has no supported claims.yaml row"]
        # labels that match no gated section leave the gate with nothing to check, which is a problem in itself
        assert variant("renamed", _CLAIM_ROWS, ("{sec:literature}", "{sec:related}"), ("{sec:results}", "{sec:method}")) \
            == ["no `% id:` paragraph falls in a gated section (sec:literature, sec:model, sec:results)"]
        # a cite in a gated section but outside every `% id:` paragraph cannot have a claims row
        assert variant("loose", _CLAIM_ROWS, ("% id: results-1\n", "\\Citet{ghost2020} opens the section.\n% id: results-1\n")) \
            == ["sec:results: \\cite{ghost2020} outside an id'd paragraph"]
        noids = variant("noids", _CLAIM_ROWS, ("% id: results-1\n", ""))
        assert "sec:results: \\cite{koijen2018carry} outside an id'd paragraph" in noids, noids
        assert "claim c3: paragraph 'results-1' not in en/paper_en.tex" in noids, noids
        # every refs.yaml entry needs an ok record naming a url, whether or not a claims row uses it
        paper = _claims_paper(Path(d) / "unused", _CLAIM_ROWS)
        refs = yaml.safe_load((paper / "refs.yaml").read_text(encoding="utf-8"))
        refs.append({"key": "unused2020", "type": "misc", "authors": ["Doe, Jane"], "year": 2020,
                     "title": "Never cited", "class": "working_paper"})
        (paper / "refs.yaml").write_text(yaml.safe_dump(refs, sort_keys=False), encoding="utf-8")
        assert C.check(paper) == ["unused2020: no verified record"], C.check(paper)


import contextlib                  # noqa: E402
import os                          # noqa: E402
import subprocess                  # noqa: E402

_STUDY_RUN_PY = b"SEED = 7\n"


def _study_git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True,
                          encoding="utf-8").stdout.strip()


def _study_commit(root: Path, message: str) -> None:
    _study_git(root, "add", "-A")
    _study_git(root, "commit", "-q", "-m", message)


@contextlib.contextmanager
def _study_sandbox():
    """(repo root, paper dir) in a throwaway git repo under %TEMP%; never the real repo.
    Restores NEXTGEN_FICC_CACHE, which start_run() sets."""
    if shutil.which("git") is None:
        raise NotRun("OWNER: git is not on PATH")
    saved = os.environ.get("NEXTGEN_FICC_CACHE")
    try:
        with tempfile.TemporaryDirectory(prefix="qgstudy_", ignore_cleanup_errors=True) as d:
            root = Path(d).resolve()
            _study_git(root, "init", "-q")
            _study_git(root, "config", "user.name", "selfcheck")
            _study_git(root, "config", "user.email", "selfcheck@example.invalid")
            _study_git(root, "config", "core.autocrlf", "false")
            paper = root / "papers" / "2026-10-23-demo"
            (paper / "scope").mkdir(parents=True)
            (paper / "study").mkdir()
            (paper / "study" / "run.py").write_bytes(_STUDY_RUN_PY)
            _study_commit(root, "paper skeleton")
            yield root, paper
    finally:
        if saved is None:
            os.environ.pop("NEXTGEN_FICC_CACHE", None)
        else:
            os.environ["NEXTGEN_FICC_CACHE"] = saved


def _study_prereg(root: Path, paper: Path, pinned: dict | None = None, *, key: str = "pinned_code") -> None:
    """scope/prereg.json in the shape the research workflow writes, committed."""
    prereg = {"paper_id": paper.name, "created_utc": "2026-10-23T00:00:00Z", "run_kind": "confirmatory", "seed": 7,
              "protocol_sha256": "0" * 64, "claims": [], "variants": [], "holdout": None, key: pinned or {},
              "new_code": [], "ledger_family": f"PAPER-{paper.name}"}
    (paper / "scope" / "prereg.json").write_text(json.dumps(prereg) + "\n", encoding="utf-8")
    _study_commit(root, "prereg")


def _study_refused(S, paper: Path, kind: str, needle: str, now: str = "2026-10-23T02:00:00Z") -> None:
    try:
        S.start_run(paper, kind=kind, seed=1, command="selfcheck", now_utc=now)
    except S.StudyRefused as exc:
        assert needle in str(exc), exc
    else:
        raise AssertionError(f"start_run(kind={kind}) was not refused ({needle})")


def test_study_refuses_without_a_committed_unmodified_prereg():
    from tools.paper import study as S
    with _study_sandbox() as (root, paper):
        _study_refused(S, paper, "exploratory", "is not committed at HEAD")                 # no prereg at all
        (paper / "scope" / "prereg.json").write_text('{"pinned_code": {}}\n', encoding="utf-8")
        _study_refused(S, paper, "exploratory", "is not committed at HEAD")                 # present, untracked
        _study_git(root, "add", "-A")
        _study_refused(S, paper, "exploratory", "is not committed at HEAD")                 # staged, not committed
        _study_git(root, "commit", "-q", "-m", "prereg")
        ctx = S.start_run(paper, kind="exploratory", seed=1, command="selfcheck", now_utc="2026-10-23T01:00:00Z")
        assert ctx.run_dir.is_dir() and ctx.clean is True, ctx
        (paper / "scope" / "prereg.json").write_text('{"pinned_code": {"x": "y"}}\n', encoding="utf-8")
        _study_refused(S, paper, "exploratory", "differs from HEAD")


def test_study_refuses_when_a_pinned_file_changed():
    from tools.paper import study as S
    with _study_sandbox() as (root, paper):
        _study_prereg(root, paper, key="pinned")                     # a misnamed key is refused, never ignored
        _study_refused(S, paper, "exploratory", "lacks pinned_code")
        _study_prereg(root, paper, {"papers/2026-10-23-demo/study/run.py": hashlib.sha256(_STUDY_RUN_PY).hexdigest()})
        S.start_run(paper, kind="confirmatory", seed=1, command="selfcheck", now_utc="2026-10-23T01:00:00Z")
        (paper / "study" / "run.py").write_bytes(b"SEED = 8\n")
        _study_commit(root, "edit the pinned study code")
        _study_refused(S, paper, "exploratory", "pinned papers/2026-10-23-demo/study/run.py")


def test_study_refuses_a_dirty_tree_for_prespecified_and_confirmatory_runs():
    from tools.paper import study as S
    with _study_sandbox() as (root, paper):
        _study_prereg(root, paper)
        (root / "notes.txt").write_text("uncommitted\n", encoding="utf-8")
        for kind in ("prespecified", "confirmatory"):
            _study_refused(S, paper, kind, "working tree is dirty")
        ctx = S.start_run(paper, kind="exploratory", seed=1, command="selfcheck", now_utc="2026-10-23T03:00:00Z")
        assert ctx.clean is False, ctx
        _study_commit(root, "notes")
        ctx = S.start_run(paper, kind="confirmatory", seed=1, command="selfcheck", now_utc="2026-10-23T04:00:00Z")
        assert ctx.clean is True and ctx.kind == "confirmatory", ctx
        _study_refused(S, paper, "replication", "kind 'replication' not in")


def test_study_run_dir_is_never_overwritten_and_manifest_is_complete():
    from tools.paper import study as S
    with _study_sandbox() as (root, paper):
        _study_prereg(root, paper)
        head = _study_git(root, "rev-parse", "HEAD")
        ctx = S.start_run(paper, kind="prespecified", seed=11, command="python study/run.py",
                          now_utc="2026-10-23T05:06:07Z")
        assert ctx.run_id == f"20261023T050607Z-{head[:7]}", ctx.run_id
        assert ctx.run_dir == paper / "study" / "runs" / ctx.run_id, ctx.run_dir
        assert os.environ["NEXTGEN_FICC_CACHE"] == str(paper / "study" / "cache")
        assert S.paper_ledger_dir(paper) == paper / "study" / "ledgers"
        raw = b"date,value\n2026-10-22,4.31\n"
        assert S.freeze_input(ctx, "dgs10.csv", raw, vintage="FRED as of 2026-10-23").read_bytes() == raw
        for name, data, needle in (("dgs10.csv", b"date,value\n", "already frozen"),
                                   ("../escape.csv", raw, "plain file name")):
            try:
                S.freeze_input(ctx, name, data)
            except S.StudyRefused as exc:
                assert needle in str(exc), exc
            else:
                raise AssertionError(f"freeze_input accepted {name}")
        try:
            S.finish(ctx, {"beta": 0.5}, qualification="significant")
        except S.StudyRefused as exc:
            assert "qualification" in str(exc), exc
        else:
            raise AssertionError("finish accepted an unknown qualification")
        try:
            S.finish(ctx, {"beta": 0.5}, qualification="qualified", config={"cache": paper})    # a Path is not JSON
        except TypeError:
            pass
        else:
            raise AssertionError("finish accepted a config that is not JSON")
        assert list(ctx.run_dir.iterdir()) == [], "a failed finish leaves no file behind, so the run can be finished"
        manifest_path = S.finish(ctx, {"beta": 0.5, "n": 250}, qualification="qualified", config={"calendar": "NYSE"})
        assert b"\r\n" not in manifest_path.read_bytes(), "MANIFEST.json is written with LF line ends"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for key in ("run_id", "kind", "seed", "command", "started_utc", "qualification", "inputs", "vintages",
                    "git", "prereg_sha256", "study_code", "python", "packages", "timezone", "config",
                    "ficc_cache", "results_sha256"):
            assert key in manifest, key
        assert manifest["inputs"] == {"dgs10.csv": hashlib.sha256(raw).hexdigest()}, manifest["inputs"]
        assert manifest["vintages"] == {"dgs10.csv": "FRED as of 2026-10-23"}, manifest["vintages"]
        assert manifest["git"] == {"commit": head, "clean": True}, manifest["git"]
        assert manifest["study_code"] == {"run.py": hashlib.sha256(_STUDY_RUN_PY).hexdigest()}, manifest["study_code"]
        assert set(manifest["packages"]) == {"numpy", "scipy", "pandas"}, manifest["packages"]
        assert (manifest["seed"], manifest["kind"], manifest["qualification"]) == (11, "prespecified", "qualified")
        body = (ctx.run_dir / "results.json").read_bytes()
        assert manifest["results_sha256"] == hashlib.sha256(body).hexdigest()
        try:
            S.finish(ctx, {"beta": 0.6}, qualification="qualified")
        except S.StudyRefused as exc:
            assert "already finished" in str(exc), exc
        else:
            raise AssertionError("a finished run was written twice")
        assert json.loads((ctx.run_dir / "results.json").read_text(encoding="utf-8")) == {"beta": 0.5, "n": 250}
        _study_refused(S, paper, "exploratory", "runs are never overwritten", now="2026-10-23T05:06:07Z")


def test_study_compare_runs_within_and_beyond_tolerance():
    from tools.paper import study as S
    with tempfile.TemporaryDirectory(prefix="qgcmp_") as d:
        def run(name, results, inputs):
            p = Path(d) / name
            p.mkdir()
            (p / "results.json").write_text(json.dumps(results), encoding="utf-8")
            (p / "MANIFEST.json").write_text(json.dumps({"inputs": inputs}), encoding="utf-8")
            return p
        a = run("a", {"beta": 0.5, "rows": [1.0, 2.0], "label": "carry"}, {"x.csv": "aa"})
        b = run("b", {"beta": 0.5 * (1 + 1e-12), "rows": [1.0, 2.0], "label": "carry"}, {"x.csv": "aa"})
        assert S.compare_runs(a, b) == []
        c = run("c", {"beta": 0.5001, "rows": [1.0], "label": "value", "extra": 1}, {"x.csv": "bb"})
        problems = S.compare_runs(a, c)
        for needle in ("inputs differ", "results.beta: 0.5 != 0.5001", "results.rows: length 2 != 1",
                       "results.extra: present in one run only", "results.label: 'carry' != 'value'"):
            assert any(needle in p for p in problems), (needle, problems)
        assert S.compare_runs(a, c, rtol=1e-3) != []          # the input and shape differences remain


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
