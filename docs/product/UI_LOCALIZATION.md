# Interface language and regional formatting

The native window owns a `LocaleContext`; the Flet application owns one per page.
There is no process-global user language. Native language/locale preferences use
QSettings and survive restart. Existing English/Korean shortcuts and the main
session's source-preserving FX/SABR translations remain supported.

The System language/region selector lists 714 CLDR regional formats from Babel.
**Only Korean and English interface catalogues ship in this change.** Other
selections explicitly display English fallback copy with the selected region's
dates, numbers, percentages and currencies. Regional formatting is not currency
conversion. The locale count is not a translated-language count.

## Terminology and fallback

New educational and rights copy uses stable keys in `core/ui_messages.py`.
SMA, EMA, RSI, MACD, BB, canonical symbols, source IDs and research verdict codes
remain stable; Korean expands the term alongside its abbreviation. Chart values,
legends, tooltips, explanations and educational reports use the same catalogue.

Existing native authored copy remains in `quantgen_desktop/translations.py`.
The source-preserving controller covers late-created controls and results; it
keeps `UiLabel.source_text` and explicitly localized narratives for reversible
switching. Financial input values and user/provider identifiers are not translated.
The shared catalogue supplements older copy without replacing these contracts.

An unsupported locale uses English text and an explicit fallback notice. Missing
new-catalogue keys raise an error in development; a missing translation in a
future partial catalogue falls back to the English entry. Unknown external
narratives remain in their source language. Technical source URLs are not
translated. Existing analysis sections that lack a translation say that the
original source language is retained.

## Adding and reviewing a language

1. Supply every catalogue key and preserve each named placeholder exactly.
2. Review indicator definitions, units, thresholds, sample limitations, source
   rights classifications and educational-versus-research meaning with a fluent
   reviewer familiar with financial terminology.
3. Check fonts, longer text, number/date/currency examples and both themes on the
   supported window widths. For an RTL pack, verify direction at layout level,
   while preserving chronological chart direction and unambiguous symbols.
4. Exercise selection, deselection, tooltips, empty/error states, reports and
   restart persistence. Verify inputs, requests, canonical exports and verdicts
   before and after language changes.
5. Add the language to the shipped catalogue only after these checks. Record
   the review scope and reviewer; automated placeholder tests alone do not
   establish professional translation review.

Legacy generated model narratives beyond the main session's completed FX scope
are still being localized there. This change does not claim universal translation
or completed language review for all existing models. The same extension rules
apply when those translations are added.
