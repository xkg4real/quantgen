"""Korean display text for the owner UI port, area: macro. See the package docstring.

Owner issue 14 (2026-11-10, "Korean and English mixed on the same screen"): the Macro sheet table's change
columns read 1일/1주/1개월/3개월 as on the Flet Macro page (ui/macro_page.py `_HEADERS_KO`), and the
Macro v2 notes say 실제 실행 / 북 instead of "Live" / "book" / "refusal" inside Korean sentences. Codes such
as NOT_LOADED, FORWARD-SIM and PASS stay as they are.
"""

PAIRS = {
    "1d": "1일",
    "1w": "1주",
    "1m": "1개월",
    "3m": "3개월",
    "Records are read explicitly. Live execution requires existing signed-calendar and connection conditions.":
        "기록은 직접 눌러야 읽습니다. 실제 실행은 서명된 거래 달력과 연결 조건이 갖춰져야 합니다.",
    "Verified source records displayed. Reading does not change official verdicts or recommended books.":
        "검증된 원문 기록을 표시했습니다. 조회가 공식 판정이나 권장 북을 바꾸지 않습니다.",
    "Research register · display only. Design weights are not sent as exposure, rule or book inputs.":
        "연구 등록부 · 표시 전용. 설계 가중치를 노출·규칙·북 입력으로 보내지 않습니다.",
    "Recorded settings displayed. Exposure is not recalculated in the UI. FORWARD-SIM/refusal are not recommendations.":
        "기록된 구성 값을 표시했습니다. 화면에서 노출을 재계산하지 않습니다. FORWARD-SIM·거절 북은 권장이 아닙니다.",
}
