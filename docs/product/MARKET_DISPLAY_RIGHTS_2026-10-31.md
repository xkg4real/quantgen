# Market display rights review — 2026-10-31

The System → Market data usage conditions view inventories six Home observations
and all 73 registered series in `DATA_READINESS_2026-10-29.json`. These are metadata
reads; no protected cache, customer contract, credential or live market request
was used. Home observations are daily, not a real-time licensed feed.

`core/research/display_rights.json` records every item, provider, frequency,
classification and provider policy in Korean/English. Policies cover free/paid
display, commercial use, live/delayed conditions, storage, redistribution/export,
derived commentary, attribution, agreements/costs and primary evidence URLs.

| Classification | Home (6) | Registered (73) |
| --- | ---: | ---: |
| Usable | 0 | 0 |
| Conditional | 3 | 31 |
| Replacement needed | 3 | 6 |
| Further verification | 0 | 36 |

These counts are **review classifications, not publication authorization**.
Conditional does not mean that a contract or acknowledgement was obtained.
Unavailable contracts, tariff amounts and legal conclusions remain unverified.

<a id="kis-chart-scope-2026-11-02"></a>
## Additional KIS chart scope — 2026-11-02

PR #56, integrated at `147afc0`, adds user-selected KIS quotes, OHLCV charts
and supported trade subscriptions in the native and Flet workspaces. These
dynamic instruments, exchanges and subscriptions are **not all covered by the
six Home observations or 73 registered-series counts above**. Those historical
inventory counts and classifications are preserved; this paragraph does not
add approved datasets or mark any live feed usable.

The [implemented coverage](KIS_MARKET_CHARTS_2026-11-02.md) distinguishes
domestic stock/ETF, overseas stock, domestic derivative and bond streams from
REST-only overseas futures and other unsupported combinations. Its US free
Nasdaq feed notice (0-minute delay, limited market-center coverage) and Asian
15-minute delay are product-specific source statements, not a blanket
consolidated real-time entitlement. Generic 20-minute-delayed examples in the
existing provider policy must not override these actual feed distinctions.
Live-account connectivity and the applicable entitlement have not been tested.

KIS/provider and exchange agreements must cover the actual audience, personal
or commercial app use, server-to-browser display, concurrent users, raw and
derived data, retention, redistribution and any export. Overseas futures also
require the applicable CME/SGX market-data entitlement. Free access, an API key,
temporary memory processing or calculating indicators grants none of these
permissions by itself. The existing `kis_krx` provider-level conditional
classification remains insufficient as dataset-specific or service-specific
approval. Contract terms, fees and legal conclusions remain **NOT_VERIFIED**;
`publication_authorization: false` and `legal_opinion: false` remain unchanged.

The new software dependency `websockets>=15,<17` has separate package-license
obligations recorded in [policy 19](../compliance/19-licenses.md). Its BSD license
does not grant KIS or exchange data rights. New authentication/transport and
in-memory approval-key handling are recorded in [FACTS](../compliance/FACTS.md#kis-market-integration-2026-11-02);
the `ws://` connection must not be described as TLS-protected.

## Home review

| Item / current route | Classification | Required next evidence |
| --- | --- | --- |
| S&P 500 `^GSPC`, KOSPI `^KS11`, BTC-USD via Yahoo/yfinance | Replacement needed for public commercial service | Appropriate licensed provider/display agreement; do not infer redistribution rights from installed client or free access |
| USD/KRW `DEXKOUS`, US 10-year `DGS10` via FRED/Board | Conditional | Verify exact Board-origin series notice, cite source/observation date and satisfy FRED delivery/API terms |
| VIX `VIXCLS` via FRED/Cboe | Conditional | Cboe/index display and redistribution permissions for the actual service; FRED delivery is not a rights grant |

## Primary sources and decision boundaries

- [Board disclaimer](https://www.federalreserve.gov/disclaimer.htm): distinguish
  Board-origin public-domain material from separately owned material and cite it.
- [FRED API terms](https://fred.stlouisfed.org/docs/api/terms_of_use.html) and
  series notices for [DEXKOUS](https://fred.stlouisfed.org/series/DEXKOUS),
  [DGS10](https://fred.stlouisfed.org/series/DGS10),
  [VIXCLS](https://fred.stlouisfed.org/series/VIXCLS): inspect source-specific rights.
- [yfinance usage notice](https://ranaroussi.github.io/yfinance/) and
  [Yahoo exchange/data information](https://help.yahoo.com/kb/SLN2310.html): do not
  treat a personal-use client or delayed feed as public redistribution clearance.
- [KIS Open API](https://apiportal.koreainvestment.com/about-open-api),
  [provider information](https://apiportal.koreainvestment.com/provider), and
  [KRX API conditions](https://openapi.krx.co.kr/contents/OPP/DATA/OPPDATA003.jsp):
  personal access, corporate display and redistribution have different conditions;
  obtain the applicable exchange/Koscom/provider agreement.
- [FMP terms](https://site.financialmodelingprep.com/terms-of-service): a public or
  client-facing service requires plan/display/distribution review, including free
  public use. Derived displays do not automatically remove restrictions.
- [Cboe data agreements](https://www.cboe.com/data/market-data-services/document-library):
  verify the actual product, audience, display method and redistribution rights.
- ECOS, KOSIS, Treasury, French library, Upbit, Binance and derived series retain
  their individually linked verification requirements. Derived records inherit
  every input's unresolved restrictions. Access alone is not a blanket grant.

The bundled educational FX sample is separately documented and attributed in its
provenance file; it does not license any live feed. Its original Board series is
[DEXUSEU](https://fred.stlouisfed.org/series/DEXUSEU); the
[2018-01-08 H.10 release](https://www.federalreserve.gov/releases/h10/20180108/)
also cross-checks the mirror's reciprocal orientation.

## Analysis/commentary legal scope

The [FSC's 2024-08-14 announcement](https://www.fsc.go.kr/no010101/82887) is a
starting point for evaluating paid interaction, individualized advice and
performance representations against the actual product and business model.
Education, generic commentary and personalized advice must be assessed separately;
a disclaimer alone does not decide the legal category. Current applicable law,
cross-border provision, privacy and the actual agreements need qualified review
before public-service approval. This record is not a legal opinion and sets
`publication_authorization: false` and `legal_opinion: false` explicitly.
