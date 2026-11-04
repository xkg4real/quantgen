"""Advisory number check for AI commentary, and its 'not verified' label.

§10 NEW-M6-12, NEW-M6-19 (limitations a and d). Pure: re, math and dataclasses
only, no I/O and no application imports. The check never changes the commentary text, an error
code, the payload or a verdict, and it never blocks display.

A cited number counts as found when it occurs somewhere in the JSON payload that
was sent (numeric leaves, whole formatted-number strings, and numbers inside
other free-text strings), allowing rounding to the printed decimals and %/bp
scaling. The sign, the measure a number is attached to, and verdict words are
not compared, so a match is not verification. Numbers that appear only in the
question text (the operator's question or the report-format instructions) are
reported separately, never as data.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass

COARSE_SIGNIFICANT_DIGITS = 2
MAX_LISTED = 10
_MARKER_PREFIXES = ("NaN:", "+inf:", "-inf:")      # the payload's non-finite markers

AI_LABEL = {
    "en": ("AI commentary · not verified. Claude wrote this from the data sent; QUANTGEN does not check its "
           "reasoning, and the same request can give different text. It does not change any official verdict."),
    "ko": ("AI 해설 · 검증 안 됨. Claude가 전송한 데이터로 쓴 글이며 QUANTGEN은 그 논리를 확인하지 않습니다. "
           "같은 요청에도 다른 글이 나올 수 있습니다. 공식 판정은 바뀌지 않습니다."),
}


@dataclass(frozen=True)
class NumberCheck:
    checked: int                 # numbers compared (skipped tokens excluded)
    not_found: tuple             # cited as printed, in text order
    question_only: tuple         # found only in the question text, not in the data sent
    found: int                   # data matches with three or more significant digits
    coarse_found: int            # data matches with two significant digits or fewer
    skipped: int                 # dates, tenors, windows, scale words, ranges, identifiers


# --------------------------------------------------------------------------- #
# Tokens in the AI text
# --------------------------------------------------------------------------- #
_NUMBER = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?")
_WORD = re.compile(r"[A-Za-z0-9_]")
_MONTHS = ("January|February|March|April|May|June|July|August|September|October|November|December|"
           "Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept|Sep|Oct|Nov|Dec")
_ISO_DATE = r"\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?)?"
_MASKS = tuple(re.compile(p) for p in (
    _ISO_DATE,
    r"\d{4}/\d{1,2}/\d{1,2}",
    r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
    r"\d{4}\.\s?\d{1,2}\.\s?\d{1,2}\.?",
    r"\b\d{1,2}:\d{2}(?::\d{2})?\b",
    r"\d{4}년\s*\d{1,2}월(?:\s*\d{1,2}일)?",
    r"\d{1,2}월(?:\s*\d{1,2}일)?",
    rf"\b(?:{_MONTHS})\.?\s+\d{{1,2}}(?!\d)(?:,\s*\d{{4}})?",
    rf"\b(?:{_MONTHS})\.?\s+\d{{4}}\b",
    rf"\b\d{{1,2}}\s+(?:{_MONTHS})\b",
))
# Longest first; each maps to the scale family used for matching.
_UNITS = (("percentage points", "%"), ("percentage point", "%"), ("퍼센트포인트", "%"),
          ("베이시스포인트", "bp"), ("basis points", "bp"), ("basis point", "bp"), ("per cent", "%"),
          ("percent", "%"), ("퍼센트", "%"), ("bps", "bp"), ("%p", "%"), ("pp", "%"), ("bp", "bp"),
          ("%", "%"), ("×", "x"), ("x", "x"), ("배", "x"))
_INDEX_BEFORE = re.compile(r"(?:S&P|KOSPI|KOSDAQ|Nasdaq|NASDAQ|FTSE|Nikkei|Russell|Stoxx|STOXX|DAX|CAC) $")
_CONFIDENCE_AFTER = re.compile(r"\s?(?:VaR|CVaR|ES\b|expected shortfall|confidence|CI\b|interval|신뢰|구간)")
_SCALE_WORD_AFTER = re.compile(r"\s?(?:thousand|million|billion|trillion|mn|bn|tn)\b", re.I)
_KO_SPAN = ("년", "개월", "달", "주", "거래일", "영업일", "일", "세션", "분기", "시간", "번째", "차")
_KO_SPAN_NOT = ("달러", "차이", "주식")
_KO_SCALE = ("만", "억", "조", "천")
_SCALES = {"%": (1, 100), "bp": (1, 100, 10_000), "x": (1,), None: (1,)}


@dataclass(frozen=True)
class _Cited:
    raw: str
    value: float
    decimals: int
    unit: str | None
    significant: int


def _mask(text: str) -> str:
    for pattern in _MASKS:
        text = pattern.sub(lambda m: " " * len(m.group(0)), text)
    return text


def _cited_numbers(text: str) -> tuple[list[_Cited], int]:
    src = _mask(text)
    cited, skipped = [], 0
    for m in _NUMBER.finditer(src):
        start, end, number = m.start(), m.end(), m.group(0)
        prev = src[start - 1] if start else ""
        if prev and (_WORD.match(prev) or prev in ".,"):
            skipped += 1; continue                       # A12, x1.5, 1.2.3
        if prev in ("-", "–", "/") and start >= 2 and _WORD.match(src[start - 2]):
            skipped += 1; continue                       # M6-19, 2y/5y, the second end of 15-20%
        if _INDEX_BEFORE.search(src[max(0, start - 12):start]):
            skipped += 1; continue                       # S&P 500, KOSPI 200
        unit, stop = None, end
        rest = src[end:]
        gap = 1 if rest[:1] == " " else 0
        for word, family in _UNITS:
            if rest[gap:gap + len(word)].lower() == word:
                after = rest[gap + len(word):gap + len(word) + 1]
                if not (after and _WORD.match(after)) or word in ("%", "%p"):
                    unit, stop = family, end + gap + len(word)
                    break
        following = src[stop:stop + 1]
        tail = src[stop:]
        plain = number.replace(",", "")
        decimals = len(plain.split(".")[1]) if "." in plain else 0
        if following and _WORD.match(following):
            skipped += 1; continue                       # 10y, 5th, 3M, 1e5
        if unit is None and following in ("-", "–") and _WORD.match(src[stop + 1:stop + 2] or " "):
            skipped += 1; continue                       # 10-year, 1-week, 252-session, ranges
        if unit == "%" and _CONFIDENCE_AFTER.match(tail):
            skipped += 1; continue                       # 95% VaR, 99% 신뢰구간
        if unit is None and _SCALE_WORD_AFTER.match(tail):
            skipped += 1; continue                       # 1.2 billion
        if (unit is None and decimals == 0 and tail.startswith(_KO_SPAN)
                and not tail.startswith(_KO_SPAN_NOT)):
            skipped += 1; continue                       # 52주, 3개월, 252거래일, 10년
        if unit is None and tail.startswith(_KO_SCALE) and not tail.startswith("만큼"):
            skipped += 1; continue                       # 3억, 1.2조
        if (unit is None and decimals == 0 and "," not in number and len(plain) == 4
                and 1900 <= int(plain) <= 2100):
            skipped += 1; continue                       # a year (integer prices in that range too)
        digits = plain.replace(".", "")
        significant = len(digits.lstrip("0").rstrip("0")) if decimals == 0 else len(digits.lstrip("0"))
        cited.append(_Cited(src[start:stop].strip(), float(plain), decimals, unit, max(significant, 1)))
    return cited, skipped


# --------------------------------------------------------------------------- #
# References
# --------------------------------------------------------------------------- #
_FORMATTED = re.compile(r"^\s*[+\-−]?(\d{1,3}(,\d{3})+|\d+)(\.\d+)?\s*(%|bp)?\s*$")
_ISO_ONLY = re.compile(rf"\s*{_ISO_DATE}\s*")


def _data_references(obj) -> list[float]:
    values = []

    def walk(o):
        if isinstance(o, dict):
            for item in o.values():
                walk(item)
        elif isinstance(o, list):
            for item in o:
                walk(item)
        elif isinstance(o, bool) or o is None:
            return
        elif isinstance(o, (int, float)):
            if math.isfinite(o):
                values.append(abs(float(o)))
        elif isinstance(o, str):
            whole = _FORMATTED.match(o)
            if whole:
                values.append(float((whole.group(1) + (whole.group(3) or "")).replace(",", "")))
            elif not o.startswith(_MARKER_PREFIXES) and not _ISO_ONLY.fullmatch(o):
                for m in _NUMBER.finditer(_mask(o)):
                    values.append(float(m.group(0).replace(",", "")))

    walk(obj)
    return values


def _question_references(question: str) -> list[float]:
    return [float(m.group(0).replace(",", "")) for m in _NUMBER.finditer(question or "")]


def _first_at_least(values, x):
    """Index of the first sorted value >= x (a plain binary search)."""
    lo, hi = 0, len(values)
    while lo < hi:
        mid = (lo + hi) // 2
        if values[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo


class _Index:
    """Sorted absolute reference values; each scale searches only its window."""
    def __init__(self, values):
        self.values = sorted(values)

    def match(self, c: _Cited) -> bool:
        step = 10.0 ** -c.decimals
        eps = 1e-9 * max(1.0, c.value)
        for scale in _SCALES[c.unit]:
            # A match needs |v|*scale in [c - step/2, c + step) (rounding or truncation).
            lo = _first_at_least(self.values, (c.value - 0.5 * step - eps) / scale)
            hi = _first_at_least(self.values, (c.value + step + eps) / scale)
            for v in self.values[lo:hi + 1]:
                x = v * scale
                if abs(x - c.value) <= 0.5 * step + eps:
                    return True
                if abs(math.floor(x / step + 1e-9) * step - c.value) <= eps:
                    return True                          # printed by truncation
        return False


def number_check(text: str, sent_payload, question: str = "") -> NumberCheck:
    """Compare the numbers cited in `text` with the JSON payload object that was sent."""
    cited, skipped = _cited_numbers(text or "")
    data = _Index(_data_references(sent_payload))
    asked = _Index(_question_references((question or "").strip()))
    not_found, question_only, found, coarse = [], [], 0, 0
    for c in cited:
        if data.match(c):
            if c.significant <= COARSE_SIGNIFICANT_DIGITS:
                coarse += 1
            else:
                found += 1
        elif asked.match(c):
            question_only.append(c.raw)
        else:
            not_found.append(c.raw)
    return NumberCheck(len(cited), tuple(not_found), tuple(question_only), found, coarse, skipped)


# --------------------------------------------------------------------------- #
# Display
# --------------------------------------------------------------------------- #
def _listed(items, ko: bool) -> str:
    head = ", ".join(items[:MAX_LISTED])
    more = len(items) - MAX_LISTED
    if more > 0:
        head += f" 외 {more}개" if ko else f" and {more} more"
    return head


def check_line(check: NumberCheck | None, language: str) -> str:
    ko = language == "ko"
    if check is None:
        return "숫자 대조: 실행하지 않음." if ko else "Number check: not run."
    if check.checked == 0:
        return ("숫자 대조: 해설에 대조할 숫자가 없습니다." if ko
                else "Number check: the commentary cites no numbers to compare.")
    if ko:
        line = (f"숫자 대조(확인한 숫자 {check.checked}개): 전송한 내용에서 찾지 못한 숫자: "
                f"{_listed(check.not_found, True) if check.not_found else '없음'}.")
        if check.not_found:
            line += " 찾지 못한 숫자는 틀린 값이 아니라 차이나 비율처럼 계산해 낸 값일 수도 있습니다."
        if check.question_only:
            line += (" 계산 데이터가 아니라 질문 문장(사용자 질문 또는 보고서 형식 지침)에만 있는 숫자: "
                     f"{_listed(check.question_only, True)}.")
        if check.coarse_found:
            line += f" 일치한 숫자 중 {check.coarse_found}개는 유효숫자가 두 자리 이하라 우연히 일치했을 수 있습니다."
        return line + (" 일치는 그 숫자가 전송한 데이터 어딘가에 있다는 뜻일 뿐입니다(반올림과 %·bp 환산 허용). "
                       "부호, 숫자가 가리키는 항목, 판정 단어는 확인하지 않습니다.")
    line = (f"Number check ({check.checked} checked): not found in anything sent: "
            f"{_listed(check.not_found, False) if check.not_found else 'none'}.")
    if check.not_found:
        line += " A number that was not found may be derived (a difference or a ratio) rather than wrong."
    if check.question_only:
        line += (" Only in the question text (your question or the report-format instructions), "
                 f"not in the calculation data: {_listed(check.question_only, False)}.")
    if check.coarse_found:
        line += f" {check.coarse_found} of the matches have two significant digits or fewer and could match by chance."
    return line + (" A match means only that the number occurs somewhere in the data sent, allowing rounding "
                   "and %/bp scaling; its sign, the measure it refers to, and verdict words are not checked.")
