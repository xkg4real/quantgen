# KEY-5/a 메인 독립 검토 결과 (dc936d4)

작성: 메인 세션 QUANTGEN/MAIN, 2026-11-20 05:50 KST. 대상: `claude/payments-key5a-20261120` @ `dc936d4` (main 8445187 기준, MERGE_QUEUE 4h).
방법: workflow wf_56720449-739, 5개 관점(게이트웨이 핵심, feed·main.py, 시험 품질, 보안·개인정보, 문서) + 지적마다 반박 검증 2회. **주간 사용량 98%로 반박 검증 도중 중단** → 아래 "주요"는 서로 다른 관점 3~4개가 각각 따로 찾은 것이라 신뢰도가 높지만, "작은 것"은 일부만 검증됨(미검증 표시). 메인이 직접 확인한 것: 동결 엔진 4파일 바이트 같음, main.py CRLF, code_sha256 10c27010 그대로, 게이트웨이 시험 5종 71 OK.

## 주요 (PR 전에 고칠 것)

| # | 파일 | 결함 | 왜 문제인가 | 고칠 방향 |
|---|---|---|---|---|
| M1 | core/gateway/feed.py 44–58 (`look_again`) | 엔진 feed가 **이미 만든 FMP 클라이언트를 계속 씀**: 키를 지우거나 reload로 FMP가 off·company가 되어도 `self._fmp`가 None이 아니면 그대로 둠. docstring "게이트웨이의 키 변경 hook이 이미 새로 고침"은 틀림 (FMPQuoteClient는 만들 때 한 번 키를 읽고 reload_credentials가 없음, provider()로 만들어 LOCAL.held()에도 없음) | 지운 키가 계속 FMP로 감, `blocked('fmp')=='off'`인데 FMP에 닿음 → KEY-4의 막힘 원칙 위반 (보안) | look_again이 매번 `blocked('fmp')`를 다시 보고, 막혔거나 키가 바뀌었으면 `_fmp=None`으로 버리고 다시 만듦. 시험: 키 저장→feed→키 삭제→FMP 호출 0회, reload off→호출 0회 |
| M2 | core/gateway/__init__.py 486–490 (`_refresh_krx`) | 같은 객체를 두 단계로 다시 만듦: `base.__init__(gateway)`가 진짜 KRXMarketClient·OpenDARTClient를 먼저 넣고, 그 뒤 `_gate_krx`가 OffClient로 바꿈. 잠금 없음 | 그 사이 다른 스레드(화면·엔진 feed)가 막혀야 할 공급처에 닿을 수 있음(fail-open). `_KRX_BUILT`도 잠금 없이 `list()` → 다른 스레드의 krx_gateway()와 겹치면 RuntimeError 가능 | 새 하위 클라이언트를 지역 변수로 다 만들고 막힘을 먼저 적용한 뒤 한 번에 바꿔 끼움(+ 모듈 잠금). `_KRX_BUILT` 접근도 같은 잠금 |

## 작은 것 (같은 PR에서 함께 권장, 일부 미검증)

- S1 core/gateway/remote.py 117 (F5): 허용 목록이 이 저장소 공급처가 실제로 보내는 코드(예: OpenDART `DARTUnavailable`, dispatch.py가 보내는 코드)를 `bad_answer`로 바꿈 → 8445187 대비 동작 변화. dispatch.py의 실제 코드 전부를 허용 목록에 넣거나 시험으로 고정.
- S2 remote.py 133 (F6): `requests.exceptions.ProxyError`(requests의 ConnectionError 하위)가 `transport_connection`이 아니라 `transport_error`로 감. 유일한 실제 전송(http_transport)은 requests 예외를 냄 → requests 예외로 시험.
- S3 feed.py 58: provider_status의 fmp_blocked 사유를 읽는 곳이 시험 밖에 없음(ui/·quantgen_desktop/·main.py는 config.*_provider_status만 부름). 엔진 last_error에 개발자용 글(`fmp is served by the company route in profile X ...`)이 그대로 나감 → 사용자용 문장으로.
- S4 시험 빈틈: A1R3-1 "원래 사유 유지 + OffClient 사유" (assertIn은 교체여도 통과), F5 약어 5자 규칙, A1R3-5 OpenDART·KIS 키 변경(지금은 KRX_API_KEY만), on_change에서 실패한 listener가 다른 listener를 막지 않음, F2 3회 반복이 필요한 별칭 경우.
- S5 tests/gateway_boundary_acceptance.py 285: F2 별칭은 단순 이름 대입만 셈(튜플·속성 대입 등은 못 셈) — 범위를 문서에 적거나 넓힘.
- S6 문서 GATEWAY_DESIGN.md: 266(사유 대체 범위가 코드와 다름: 코드는 market_snapshot·filings·financials만 대체, quote·indices는 덧붙임), 191·202(QuoteFeed가 아직 main.py에 있다고 씀), 201(F2 별칭 셈 미기재), 263 vs 266–269(규칙 6 범위 서로 어긋남), 174(transport_* 꼴 빠짐). feed.py 1–11 docstring(paper.py가 아직 안 씀 — KEY-5 몫).
- S7 compliance: dc936d4에서 `--check` FAIL(806, 새 파일 core/gateway/feed.py) — 예상된 것. PR 때 최신 main 합친 뒤 기준선 마지막에 갱신.

## 다음 (PAYMENTS 또는 이어받는 쪽)

1. M1, M2 고침 + 각각 실패하는 시험 먼저(고치기 전 코드에서 실패 확인).
2. S1–S6 같은 브랜치에서.
3. 4h 차례("병합: PAYMENTS_ACCOUNT_KEYS")가 적힌 뒤 최신 main 합침 → 기준선 마지막 → `--check` PASS → PR.
