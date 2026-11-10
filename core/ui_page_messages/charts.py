"""Chart frames and reading panels (ui/chart_study.py, ui/fcharts.py, ui/xcharts.py, ui/qcharts.py) and the Macro page (ui/macro_page.py)."""

EN_TO_KO: dict[str, str] = {
    # Macro page chrome
    "Refresh": "새로고침",
    "Open Settings": "설정 열기",
    "View": "보기",
    "Overlay state": "오버레이 상태",
    "Model cards": "모형 카드",
    "Research register": "연구 등록부",
    "Cross-asset sheet (descriptive read), the v2 overlay state, model cards, the research register, "
    "and the daily / weekly rates-FX report inputs.":
        "주요 거시 지표의 현재 위치와 규칙 기반 시장 요약, v2 오버레이 상태, 모형 카드, 연구 등록부, "
        "일간·주간 금리·외환 보고서를 봅니다.",
    "Press Refresh to load the macro sheet": "새로고침을 눌러 거시 지표를 불러오세요",
    "Treasuries, real and breakeven yields, policy rates, IG/HY spreads, the dollar, VIX, WTI, the 10y future "
    "and gold - FRED and Yahoo are keyless; without them the sheet runs on clearly labeled synthetic series.":
        "미 국채 금리, 실질금리·기대인플레이션, 정책금리, 투자등급·하이일드 스프레드, 달러, VIX, WTI, "
        "10년 국채선물, 금을 불러옵니다. FRED와 Yahoo는 키 없이 쓸 수 있고, 가져오지 못한 지표는 "
        "합성 시계열로 대체한 뒤 분명히 표시합니다.",
    "Data is fetched automatically (FRED and Yahoo, no key needed).":
        "데이터는 자동으로 가져옵니다 (FRED·Yahoo, 키 불필요).",
    "Keyless. Treasury curve, SOFR, OECD short rates, credit OAS, macro.":
        "키 불필요. 미 국채 곡선, SOFR, OECD 단기금리, 신용 스프레드, 거시 지표.",
    "Keyless. FX spot, futures and index levels.": "키 불필요. 환율, 선물, 지수 수준.",
    "Auto (FRED + Yahoo, synthetic fallback)": "자동 (FRED·Yahoo, 실패 시 합성 데이터)",
    "Live only (FRED + Yahoo, no fallback)": "실데이터만 (FRED·Yahoo, 대체 없음)",
    "Synthetic demo": "합성 데이터 시연",
    "Data": "데이터",
    "Market summary": "시장 요약",
    "Key levels": "주요 지표 수준",
    "All indicators": "전체 지표",
    "Reports": "보고서",
    "Descriptive read — not a regime model (P19)": "현재 상태를 설명하는 해석 — 국면 모형 아님 (P19)",
    "1y z-scores · descriptive read — not a regime model (P19)":
        "1년 z-점수 · 현재 상태를 설명하는 해석 — 국면 모형 아님 (P19)",
    "Yield curve (20 sessions)": "금리 곡선 (20거래일)",
    "Risk appetite": "위험선호",
    "Dollar": "달러",
    "Inflation expectations (1 month)": "기대인플레이션 (1개월)",
    "Real yields (1 month)": "실질금리 (1개월)",
    "Rule calculation (original summary)": "규칙 계산 근거 (원문)",
    "Daily market commentary": "일간 시장 코멘트",
    "Weekly rates and FX note": "주간 금리·외환 노트",
    "Deep-analysis format (instructions sent with a deep analysis)":
        "심층 분석 형식 (심층 분석에 함께 보내는 지시문)",

    # Macro -> Overlay state (ui/macro_state_panel.py): chrome only; artifact values stay verbatim.
    "Market": "시장",
    "Artifacts": "산출물",
    "Live (macro dir)": "실제 (macro 폴더)",
    "Dry run (macro dir/dry_run)": "모의 실행 (macro 폴더/dry_run)",
    "Run macro_daily": "macro_daily 실행",
    "Run": "실행",
    "Dry run (local vendor data)": "모의 실행 (로컬 공급사 데이터)",
    "Live (needs KIS, signed calendars)": "실제 실행 (KIS·서명된 거래 달력 필요)",
    "Running… (hermetic, local data)": "실행 중… (외부 연결 없이 로컬 데이터 사용)",
    "Running one live decision…": "실제 결정 1건 실행 중…",
    "Busy: wait for the current run": "진행 중: 지금 실행이 끝날 때까지 기다리세요",
    "Reading artifacts…": "산출물을 읽는 중…",
    "Acknowledging…": "확인 처리 중…",
    "Runs one live decision of the selected market": "선택한 시장의 실제 결정 1건을 실행합니다",
    "No macro_state artifact for this market: nothing is shown (fail closed, no numbers).":
        "이 시장의 macro_state 기록이 없어 숫자를 표시하지 않습니다 (안전 차단).",
    "No macro state yet": "아직 매크로 상태 기록이 없습니다",
    "Run macro_daily (dry run on local vendor data) to see the pipeline end to end; books stay DISARMED until "
    "official closes and signed calendars exist.":
        "macro_daily를 모의 실행(로컬 공급사 데이터)하면 전체 과정을 처음부터 끝까지 볼 수 있습니다. 공식 종가와 "
        "서명된 거래 달력이 생기기 전까지 모든 북은 DISARMED(비활성) 상태입니다.",
    "VENDOR DATA · DRY RUN · not an official close · not a card run":
        "공급사 데이터 · 모의 실행 · 공식 종가 아님 · 카드 실행 아님",
    "volatility labels (display only)": "변동성 라벨 (표시 전용)",
    "Acknowledge": "확인",
    "Alerts": "알림",
    "No open alerts.": "처리할 알림이 없습니다.",
    "Page alerts persist until acknowledged; Acknowledge records ack_utc in the alert store.":
        "긴급(PAGE) 알림은 확인할 때까지 남습니다. 확인을 누르면 알림 저장소에 ack_utc가 기록됩니다.",
    "Open owner actions and decisions": "소유자 확인이 필요한 항목과 결정",
    "Read-only: the owner rules through the rules store.": "읽기 전용: 소유자는 규칙 저장소에서 결정합니다.",
    "Tech-fund XS / OQ items: none changes an acting parameter.":
        "테크 펀드 XS / OQ 항목: 어느 것도 실행 파라미터를 바꾸지 않습니다.",
    "Inputs": "입력 데이터",
    "Recorded inputs, then the acting inputs that failed closed.": "기록된 입력과, 안전 차단된 실행 입력입니다.",
    "No inputs recorded.": "기록된 입력이 없습니다.",
    "None listed.": "해당 항목이 없습니다.",
    "Volatility target": "변동성 목표",
    "Overlays": "오버레이",
    "One overlay_decision per family; composition by min(), floor 0.5, cap 1.0.":
        "계열마다 overlay_decision 하나, min()으로 합성, 하한 0.5, 상한 1.0.",
    "Display-only books — not a recommendation": "표시 전용 북 — 권유 아님",
    "FORWARD-SIM and refusal books never enter a weight book's min() and never share its stat strip.":
        "FORWARD-SIM 북과 거절 북은 비중 북의 min()에 들어가지 않고 같은 지표 줄에도 표시하지 않습니다.",
    "No overlay_decision artifacts for this decision's effective session.":
        "이 결정의 적용 세션에 해당하는 overlay_decision 기록이 없습니다.",
    "Context log": "맥락 기록",
    "Context only — never acts, feeds no book (R-13).": "맥락 정보일 뿐 — 실행하지 않고 어떤 북에도 들어가지 않습니다 (R-13).",
    "No context_log artifact for this decision.": "이 결정의 context_log 기록이 없습니다.",
    "Event calendar": "이벤트 달력",
    "No event_calendar artifact yet (a macro_daily run writes one).":
        "아직 event_calendar 기록이 없습니다 (macro_daily를 실행하면 생깁니다).",
    "No items.": "항목이 없습니다.",
    "No events.": "이벤트가 없습니다.",
    "Canonical key": "설정 키",
    "Decision": "결정",
    "Title": "제목",
    "Severity": "심각도",
    "Code": "코드",
    "Series": "시계열",
    "Role": "역할",
    "Dispute": "이의 제기",
    "Event": "이벤트",
    "Region": "지역",
    "Disposition": "처분",
    "First seen (UTC)": "처음 발생 (UTC)",
    "Obs date": "관측일",
    "Value status": "값 상태",
    "Stale deadline (UTC)": "갱신 기한 (UTC)",
    "Scheduled (UTC)": "예정 시각 (UTC)",
    "KR gap session": "한국 갭 세션",
    "Would apply to": "적용 대상",

    # Macro -> Model cards (ui/macro_cards_view.py)
    "Macro model cards": "매크로 모형 카드",
    "CARD-O / CARD-P registry. Nothing here reaches the recommended book until it PASSes under a frozen gate package.":
        "CARD-O / CARD-P 등록부. 동결된 게이트 패키지에서 PASS하기 전에는 어떤 항목도 권장 북에 들어가지 않습니다.",
    "Registered REJECT — a fact about the instrument": "등록된 REJECT — 해당 상품에 대한 사실 기록",
    "Registered card: never re-run, never rebuilt.": "등록된 카드: 다시 실행하거나 다시 만들지 않습니다.",
    "FORWARD-SIM books — not a recommendation": "FORWARD-SIM 북 — 권유 아님",
    "Display only: a FORWARD-SIM multiplier never reaches the recommended book, and a forward record never validates.":
        "표시 전용: FORWARD-SIM 배수는 권장 북에 들어가지 않으며, 이후 기록이 검증을 대신하지 않습니다.",
    "Refusal books — not a recommendation": "거절 북 — 권유 아님",
    "Retired legs kept as labelled REJECTs (archived council records); display only.":
        "퇴역한 구성요소를 REJECT 표시와 함께 보관한 기록(위원회 기록), 표시 전용.",
    "Reading… (local files, read-only)": "읽는 중… (로컬 파일, 읽기 전용)",
    "Read-only records. A verdict chip shows only a gate result; BUILD-AS-INSURANCE, FORWARD-SIM and refusal are "
    "dispositions, shown beside it. Labels are printed verbatim.":
        "읽기 전용 기록입니다. 판정 칩은 게이트 결과만 보여 주며, BUILD-AS-INSURANCE·FORWARD-SIM·거절은 처분으로 "
        "옆에 따로 표시합니다. 라벨은 원문 그대로 표시합니다.",
    "No macro card runs before the freeze: every card stays NOT RUN until the package is frozen and its formal run "
    "is recorded (P11).":
        "동결 전에는 매크로 카드를 실행하지 않습니다. 패키지가 동결되고 정식 실행이 기록될 때까지 모든 카드는 NOT RUN"
        "입니다 (P11).",
    "Model cards not shown: the card registry, verdict chain or gate status is missing or invalid (fail closed).":
        "모형 카드를 표시하지 않습니다: 카드 등록부, 판정 기록 또는 게이트 상태가 없거나 올바르지 않습니다 (안전 차단).",
    "Gate package": "게이트 패키지",
    "Tech-fund card drafts — not run, not a recommendation": "테크 펀드 카드 초안 — 미실행, 권유 아님",
    "Proposals pending owner confirmation; Council v2.0 governs on conflict.":
        "소유자 확인을 기다리는 제안입니다. 충돌하면 Council v2.0을 따릅니다.",
    "CRY-1 control results (crypto card C3)": "CRY-1 대조 결과 (암호화폐 카드 C3)",
    "Vendor data, labelled trials, not formal card runs; the stored C3 verdict is not rewritten.":
        "공급사 데이터로 표시한 시험이며 정식 카드 실행이 아닙니다. 저장된 C3 판정은 바뀌지 않습니다.",
    "No tech-fund card drafts found under docs/techfund.": "docs/techfund에서 테크 펀드 카드 초안을 찾지 못했습니다.",
    "No CRY-1 results found under docs/techfund.": "docs/techfund에서 CRY-1 결과를 찾지 못했습니다.",
}
