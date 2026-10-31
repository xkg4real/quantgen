# LETF underlying-index identity (M4-N1 / NEW-M6-06)

Previously all five funds requested KIS index `2001` (KOSPI200), including
233740 and 251340, which require KOSDAQ150 as their variance input. Without
KIS, even a real fund history could silently receive a synthetic KOSPI200 input.

The shared workflow now maps 122630/252670/114800 to KOSPI200 and
233740/251340 to KOSDAQ150. KOSPI200 keeps its existing probed code. KOSDAQ150
is resolved from the official KIS index master by one exact normalized name
(`KOSDAQ150` or `코스닥150`); broad KOSDAQ, leveraged and futures index names
are not substitutes. Missing, ambiguous or malformed matches do not produce a
calculation. No KOSDAQ150 code is guessed or hard-coded.

The index response must have the requested identity, positive finite prices,
ordered unique dates and at least 63 returns. Mapping/provider failures leave
the fund's other results visible with a distinct LETF `NOT_RUN` notice. Both
Flet and PyQt6, narrative/AI payloads and JSON/HTML exports retain the required
index, actual code, source/mapping basis and calculation status. Only explicit
Synthetic demo mode uses a synthetic series named for the mapped index.

## Source evidence

Research source: `MODEL_LIMITS_REGISTER_2026-10-28.md`, Model95, at
`2da6469d8b3d45eab61d682555ff630ce1f564f7`.

Official KIS repository inspected at
`3a9be59a3ed8745720dc3aa9d584bdf3b7830362`:

- [Index master layout](https://github.com/koreainvestment/open-trading-api/blob/3a9be59a3ed8745720dc3aa9d584bdf3b7830362/stocks_info/%EC%97%85%EC%A2%85%EC%BD%94%EB%93%9C%EC%A0%95%EB%B3%B4.h): one market byte, four code bytes, forty name bytes.
- [Master download example](https://github.com/koreainvestment/open-trading-api/blob/3a9be59a3ed8745720dc3aa9d584bdf3b7830362/stocks_info/sector_code.py): `idxcode.mst.zip`, CP949. The implementation follows the header's byte layout and preserves TLS verification; the example's insecure SSL override is not copied.
- [Daily index endpoint](https://github.com/koreainvestment/open-trading-api/blob/3a9be59a3ed8745720dc3aa9d584bdf3b7830362/examples_llm/domestic_stock/inquire_daily_indexchartprice/inquire_daily_indexchartprice.py): market U, exact master code, FHKUP03500100.

The live master download was denied by the execution network (CONNECT403).
There was no bypass. Runtime lookup is implemented and tested with injected
fixed-width records; no live KOSDAQ150 code, entitlement or successful market
request is claimed. If the master is inaccessible in the user's environment,
the explicit unavailable result applies until access is available.

## Validation and limits

22 focused/regression tests passed, including both UIs and exports. Tests
exercise exact-name/CP949 parsing, wrong/ambiguous/short master records, all five
funds through the real index request adapter with injected transport, independent
AZ variance arithmetic, invalid histories and failure without substitution.
The test identifier 9876 is invented, not a claimed provider code.

Three KOSPI200 funds retain all nine existing numerical result fields (27 field
comparisons, including rows) exactly against main `8e4c593`. GARCH, strategy
and AZ engine sources are unchanged. CI includes the new checks on Windows
and Linux; its actual outcome is recorded with the PR.

M4-N1's incorrect input routing is corrected. This does not close M4-N3
(rate/dividend assumptions), M4-N10 (historical study proxy), funding inference,
manual Windows/live-provider validation, or the full §10 list. A spot index
variance input is not a claim about the fund's realised futures benchmark.
