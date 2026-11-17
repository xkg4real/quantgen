"""Korean reading of the data-status notes the app itself writes (owner issue 14, 2026-11-11).

The owner found English sentences in the Korean window. Most were notes the app writes about its own
data: synthetic fallbacks ("Simulated series (...) — no market data provider was used."), missing keys
and the keyless Yahoo fallback. Those sentences have fixed shapes, written by core.ficc.data and
core.quant.history; `note_korean` reads exactly those shapes, line by line.

Anything else — a provider's own message, an error string, a user's note — stays exactly as written:
the rules match only whole fixed phrases and never translate words inside other text. Numbers, ticker
symbols and the provider text inside parentheses are kept as they are. Display only: exports keep the
English notes.
"""
from __future__ import annotations

import re
from typing import Optional

_NO_PROVIDER = "시장 데이터 제공처를 쓰지 않았습니다"
_FREQ = {"daily": "일별", "weekly": "주별", "monthly": "월별", "quarterly": "분기별", "annual": "연간"}

_RULES = (
    (re.compile(r"Simulated Treasury par curve \(Nelson-Siegel random walk\) — no market data provider was used\."),
     f"넬슨-시겔 랜덤워크로 만든 합성 미국채 파 금리 곡선이며 {_NO_PROVIDER}."),
    (re.compile(r"Simulated series \(GBM, μ=([^,()]+), σ=([^()]+)\) — no market data provider was used\."),
     rf"GBM(μ=\1, σ=\2)으로 만든 합성 시계열이며 {_NO_PROVIDER}."),
    (re.compile(r"Simulated series \(GBM price, vol ([^()]+)\) — no market data provider was used\."),
     rf"GBM 가격 경로(변동성 \1)로 만든 합성 시계열이며 {_NO_PROVIDER}."),
    (re.compile(r"Simulated series \(OU rate, mean ([^()]+)\) — no market data provider was used\."),
     rf"OU 금리 과정(평균 \1)으로 만든 합성 시계열이며 {_NO_PROVIDER}."),
    (re.compile(r"Simulated series \(random-walk level\) — no market data provider was used\."),
     f"랜덤워크 수준으로 만든 합성 시계열이며 {_NO_PROVIDER}."),
    (re.compile(r"Simulated spot \(GBM, vol ([^()]+)\) — no market data provider was used\."),
     rf"GBM(변동성 \1)으로 만든 합성 현물환이며 {_NO_PROVIDER}."),
    (re.compile(r"KIS credentials are not configured; "), "KIS 인증 정보가 설정되지 않음: "),
    (re.compile(r"FMP_API_KEY is not configured; "), "FMP_API_KEY가 설정되지 않음: "),
    (re.compile(r" ?Yahoo Finance also failed \((.*)\)\.$"), r" Yahoo Finance도 쓸 수 있는 자료를 주지 않았습니다(\1)."),
    (re.compile(r"; Yahoo used because (KIS credentials are not configured|FMP_API_KEY is not configured)"),
     lambda m: "; " + ("KIS 인증 정보" if m[1].startswith("KIS") else "FMP_API_KEY") + "가 없어 Yahoo를 사용"),
    (re.compile(r"^FRED failed: (.*); simulated curve panel\. "), r"FRED 응답 실패(\1)로 합성 곡선을 씁니다. "),
    (re.compile(r"^(FRED|Yahoo|Yahoo Finance) failed: (.*); simulated series\. "), r"\1 응답 실패(\2)로 합성 시계열을 씁니다. "),
    (re.compile(r"^(daily|weekly|monthly|quarterly|annual); "), lambda m: _FREQ[m[1]] + "; "),
)


def note_korean(text: Optional[str]) -> Optional[str]:
    """The Korean window's reading of an app-written data note; other text is returned unchanged."""
    if not isinstance(text, str) or not text:
        return text
    lines = []
    for line in text.split("\n"):
        for pattern, replacement in _RULES:
            line = pattern.sub(replacement, line)
        lines.append(line)
    return "\n".join(lines)


def method_korean(method: str) -> str:
    """A curve method id (core.ficc.curves) by its Korean display name; unknown ids stay as written."""
    try:
        from core.ficc.curves import METHOD_NAMES
        from .translations import translate
    except ImportError:  # pragma: no cover - the native app always has both
        return method
    name = METHOD_NAMES.get(method)
    return translate(name, "ko") if name else method
