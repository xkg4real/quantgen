# A1 terminology and display roles

The owner approved the proposed glossary, existing G1 panels, local reading help,
limited A1/A3 parallel implementation and A1-first merge on 2026-11-06. This A1
change starts at main `e79ef2c1160242ddf86d5b381e1005f2ad627e16` after AI PR #75.
It changes authored display text and explicitly marked columns. A3 layout and
reading help are a separate implementation branch and acceptance step.

## Approved vocabulary

| Source | Korean display |
| --- | --- |
| Build & Test / Portfolio & Risk | 설계/검증 / 분석 |
| Signals / Paper Trading | 기술적 분석 / 모의투자 |
| Metric / Field / Metrics | 항목 / 항목 / 주요 지표 |
| Sharpe ratio | 샤프 지수 |
| Convexity | 컨벡시티; explanatory first mention 컨벡시티(볼록성) |
| Macaulay duration | 맥컬리 듀레이션 |
| Zero rate / Provider | 무이표 금리 / 제공처 |
| Monte Carlo / Horizon in sessions | 몬테카를로 / 분석 기간(거래일) |
| Macro sheet / Macro v2 | 매크로 지표 / 매크로 v2 |

Model names retain Vasicek, Hull-White, Nelson-Siegel and other proper names.
Model data keys and selected values stay canonical. The separate Analysis tools
menu remains 분석 도구. Monte Carlo convexity correction keeps its existing meaning.

## Preserved contracts

- Existing English and older Korean source captions remain available for locale
  switching. Exact display aliases do not rewrite report text or data identifiers.
- Native metric/header metadata marks authored captions. Explicit status roles
  distinguish execution, connection and official verdict cells. Official Korean
  captions include their original codes, and status tooltips retain the raw code.
  Unknown status codes remain visible. A connection setting being present is not
  labelled a successful provider call.
- OBSERVED is shown as 정상 관측; its daily-observation scope remains in the
  explanatory text. STALE, missing values, failures and their warnings remain.
- Native ETF Korean display notes use a presentation adapter. Original shared
  disclosure functions, report sections, English source, calculation values and
  AI payloads are unchanged.
- Specified Flet Bonds, Structuring, KRX, Macro, Rates and FX table headers use
  authored header metadata where a context is ambiguous. Provider/user/result
  cell text remains literal, including text equal to a known header word.
- New A3 section-title translations are available, but their presence does not
  mean that A3 layout or the local reading panel has been implemented here.

No calculation, precision, source data, report schema, export, AI request,
official validation rule, order path or frozen research behavior is changed.
This is not complete Flet translation or a claim of Windows manual acceptance.

## Validation and completion evidence

Validation is limited to synthetic fixtures, fake HTTP and temporary mutable
state, with protected caches, actual ledgers, dotenv and live networking excluded.
The focused status/watchlist run passed 24 tests. Its first five-test run had one
test assertion aimed at the status label instead of the preserved report section;
the assertion was corrected and the full focused run passed.

Final integrated validation passed 167 tests across 20 modules (exit 0): native
A1 terms/status, selected Flet headers, language round trips, raw report/payload
preservation, watchlist/ETF/glossary/indicator guide, typography and Flet routes.
Independent implementation review found a Korean particle typo and it was fixed
before this final run. All 20 source policies were reviewed; policies 09/12/15
and supporting facts were minimally revised without clearing publication gates.
PR, exact-head Windows/Ubuntu CI and merge/LEDGER receipts remain required before
completion. A prior focused ETF test falsely recognized a hex commit suffix as
scientific notation; the numeric-token test was corrected and rerun successfully.
Actual user Windows/DPI/keyboard/screen-reader checks, provider/API calls, legal,
license, pilot and frozen-research evidence remain separate. Optional additional
GPT/Gemini specification review remains NOT_PERFORMED.
