r"""Do the English and Korean editions say the same thing? (spec 5.3 step 11)

    python -m tools.paper.consistency papers/<paper_id>     # one line per problem; exit 1 when there is any

Checks between en/paper_en.tex and ko/paper_ko.tex:
  * the same ordered list of `% id:` paragraph ids, none repeated;
  * per section (a \section and everything up to the next one, named by its first \label{sec:...}):
    the same multiset of \qnum keys and the same set of cite keys;
  * the same \label and \ref sets;
  * in either edition, no bare digit run in the prose of sec:results / sec:robustness or in any tabular body.
    Math, comments and the arguments of \qnum, \cite*, \ref*, \label and layout commands are not prose.
Every \input or \include of a file inside the paper folder (tables/<name>, ../common/<name>) is inlined first, so
generated tables and shared equations are checked where they appear; study/ (numbers.tex) is left out.
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

EDITIONS = {"en": "en/paper_en.tex", "ko": "ko/paper_ko.tex"}
NO_BARE_DIGITS = ("sec:results", "sec:robustness")

ID_RE = re.compile(r"(?m)^[ \t]*%[ \t]*id:[ \t]*(\S+)")
COMMENT_RE = re.compile(r"(?<!\\)%.*")
INPUT_RE = re.compile(r"\\(?:input|include)\s*\{([^}]*)\}")
SECTION_RE = re.compile(r"\\section\*?\s*[\[{]")
SEC_LABEL_RE = re.compile(r"\\label\{(sec:[^}]*)\}")
QNUM_RE = re.compile(r"\\qnum\{([^}]*)\}")
CITE_RE = re.compile(r"\\[Cc]ite[a-zA-Z]*\*?(?:\[[^\]]*\])*\{([^}]*)\}")
LABEL_RE = re.compile(r"\\label\{([^}]*)\}")
REF_RE = re.compile(r"\\(?:ref|eqref|autoref|pageref|nameref|cref|Cref)\*?\{([^}]*)\}")
TABULAR_RE = re.compile(r"\\begin\{(tabular\*?|tabularx|longtable)\}.*?\\end\{\1\}", re.S)
DIGITS_RE = re.compile(r"\d+")

ARG = r"\{(?:[^{}]|\{[^{}]*\})*\}"                    # one brace group, one level of nesting inside
NOT_PROSE = [                                          # applied in this order
    re.compile(r"\\\\\*?\[[^\]]*\]"),                  # \\[2pt] (before math, or its "\[" would open display math)
    re.compile(r"\\begin\{(equation|align|gather|multline|eqnarray|math|displaymath)(\*?)\}.*?\\end\{\1\2\}", re.S),
    re.compile(r"\$\$.*?\$\$|(?<!\\)\$.*?(?<!\\)\$|\\\(.*?\\\)|\\\[.*?\\\]", re.S),
    re.compile(r"\\cmidrule(?:\([^)]*\))?\{[^}]*\}"),
    re.compile(r"\\(?:href|multicolumn" + ARG + r"|multirow" + ARG + r")" + ARG),   # keeps the text argument
    re.compile(r"\\(?:qnum|[Cc]ite[a-zA-Z]*|ref|eqref|autoref|pageref|nameref|cref|Cref|label|input|include"
               r"|includegraphics|url|hspace|vspace|rule|setlength|addlinespace|cline|specialrule|begin|end"
               r"|bibliography|bibliographystyle)(?![a-zA-Z])\*?(?:\[[^\]]*\]|" + ARG + r")*"),
    re.compile(r"\\[a-zA-Z@]+\*?\[[^\]]*\]"),          # the optional argument of any other command
]


def strip_comments(tex: str) -> str:
    return "\n".join(COMMENT_RE.sub("", line) for line in tex.splitlines())


def inline_inputs(tex: str, base: Path, paper_dir: Path, _depth: int = 0) -> str:
    r"""Replace each \input/\include of a file inside paper_dir (study/ excepted) with that file's text, comments
    removed, recursively; `base` is the folder the including file sits in. Other targets stay as they are."""
    paper = Path(paper_dir).resolve()

    def text(m: re.Match) -> str:
        target = (Path(base) / m.group(1).strip()).resolve()
        if target.suffix != ".tex":
            target = target.with_name(target.name + ".tex")
        if (_depth >= 8 or paper not in target.parents or paper / "study" in target.parents
                or not target.is_file()):
            return m.group(0)
        return inline_inputs(strip_comments(target.read_text(encoding="utf-8")), target.parent, paper, _depth + 1)

    return INPUT_RE.sub(text, tex)


def _body(tex: str, base: Path, paper_dir: Path) -> str:
    """The document body with comments removed and the paper's own input files inlined."""
    tex = inline_inputs(strip_comments(tex), base, paper_dir)
    start, end = tex.find(r"\begin{document}"), tex.find(r"\end{document}")
    return tex[max(start, 0): end if end >= 0 else len(tex)]


def _sections(body: str) -> dict[str, str]:
    r"""\section regions keyed by their first sec: label; "front" before the first, "section<k>" if unlabelled."""
    starts = [m.start() for m in SECTION_RE.finditer(body)]
    out: dict[str, str] = {}
    for k, (a, b) in enumerate(zip([0] + starts, starts + [len(body)])):
        chunk = body[a:b]
        label = SEC_LABEL_RE.search(chunk)
        name = "front" if k == 0 else (label.group(1) if label else f"section{k}")
        out[name] = out.get(name, "") + chunk
    return out


def _keys(rx: re.Pattern, text: str) -> set[str]:
    return {k.strip() for group in rx.findall(text) for k in group.split(",") if k.strip()}


def _bare_digits(text: str) -> list[str]:
    """Context of every digit run left once math and markup arguments are removed."""
    for rx in NOT_PROSE:
        text = rx.sub(" ", text)
    return [" ".join(text[max(m.start() - 30, 0): m.end() + 30].split()) for m in DIGITS_RE.finditer(text)]


def check(paper_dir: Path) -> list[str]:
    paper_dir = Path(paper_dir)
    missing = [rel for rel in EDITIONS.values() if not (paper_dir / rel).is_file()]
    if missing:
        return [f"{rel} missing" for rel in missing]
    raw = {ed: (paper_dir / rel).read_text(encoding="utf-8") for ed, rel in EDITIONS.items()}
    problems = []

    ids = {ed: ID_RE.findall(text) for ed, text in raw.items()}
    for ed, seq in ids.items():
        repeated = sorted(k for k, n in Counter(seq).items() if n > 1)
        if repeated:
            problems.append(f"ids: {ed} repeats paragraph ids {repeated}")
    if ids["en"] != ids["ko"]:
        lacks = [i for i in ids["en"] if i not in ids["ko"]]
        extra = [i for i in ids["ko"] if i not in ids["en"]]
        if lacks:
            problems.append(f"ids: ko lacks paragraph ids {lacks}")
        if extra:
            problems.append(f"ids: ko has paragraph ids not in en {extra}")
        if not lacks and not extra:
            problems.append("ids: ko has the paragraph ids in a different order")

    body = {ed: _body(raw[ed], (paper_dir / rel).parent, paper_dir) for ed, rel in EDITIONS.items()}
    sections = {ed: _sections(text) for ed, text in body.items()}
    for name in dict.fromkeys([*sections["en"], *sections["ko"]]):
        en, ko = sections["en"].get(name, ""), sections["ko"].get(name, "")
        qe, qk = Counter(QNUM_RE.findall(en)), Counter(QNUM_RE.findall(ko))
        drift = {k: (qe[k], qk[k]) for k in sorted(qe | qk) if qe[k] != qk[k]}
        if drift:
            problems.append(f"qnum {name}: count differs en/ko {drift}")
        ce, ck = _keys(CITE_RE, en), _keys(CITE_RE, ko)
        if ce != ck:
            problems.append(f"cite {name}: only in en {sorted(ce - ck)}, only in ko {sorted(ck - ce)}")
    for what, rx in (("label", LABEL_RE), ("ref", REF_RE)):
        le, lk = _keys(rx, body["en"]), _keys(rx, body["ko"])
        if le != lk:
            problems.append(f"{what}: only in en {sorted(le - lk)}, only in ko {sorted(lk - le)}")

    for ed in EDITIONS:
        for name in NO_BARE_DIGITS:
            problems += [f"bare number {ed} {name}: ...{c}..." for c in _bare_digits(sections[ed].get(name, ""))]
        for table in TABULAR_RE.finditer(body[ed]):
            problems += [f"bare number {ed} tabular: ...{c}..." for c in _bare_digits(table.group(0))]
    return problems


def main(argv=None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: python -m tools.paper.consistency <paper_dir>", file=sys.stderr)
        return 2
    problems = check(Path(args[0]))
    for problem in problems:
        print(problem)
    print(f"consistency: {len(problems)} problem(s)" if problems else "consistency: OK")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
