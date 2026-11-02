QG Interface — Korean / Latin interface family, Regular / Medium / SemiBold.

Current source: Pretendard 1.3.9 (orioncactus/pretendard), pinned source ref
5c41199ea0024a9e0b2cb31735265056e5472d76.
https://github.com/orioncactus/pretendard/tree/5c41199ea0024a9e0b2cb31735265056e5472d76

These are modified, subset fonts. Primary family, style-group and PostScript
names are renamed to QG Interface; the reserved name Pretendard is not used as
the derivative's family name. Existing embedded copyright, author and license
records are retained. OS/2 weights 400, 500 and 600 come from the real upstream
faces; desktop headings and controls no longer depend on synthetic bolding.

License: SIL Open Font License 1.1. OFL.txt is the exact upstream LICENSE,
Copyright (c) 2021, Kil Hyung-jin, with Reserved Font Name Pretendard.
The source font's embedded copyright says Copyright 2023 Kil Hyung-jin; it is
preserved. Distribution must retain the copyright, license and reserved-name
conditions; font files must not be sold on their own.

Upstream attribution (from packages/pretendard/README.md at the same ref):
Inter — Rasmus Andersson.
Source Han Sans — Adobe, Google, Sandoll Communications; Jang Soo-young,
Kang Ju-yeon.
M PLUS 1p — UNDERFOREST DESIGN; Coji Morishita.
Redesign and production — Kil Hyung-jin.
These acknowledgements do not imply endorsement of QUANTGEN.

Coverage: the existing Latin, Greek, Hangul Jamo/compatibility Jamo, modern
Hangul syllables, punctuation and symbol ranges are retained where present in
the source. All 11,172 modern Hangul syllables are included. OpenType layout
features, including tabular numerals, are preserved.

Rebuild (fontTools is a build-time tool only; no new runtime dependency):
  python tools/ui/subset_font.py /path/to/Pretendard-Regular.otf
  python tools/ui/subset_font.py /path/to/Pretendard-Medium.otf --style Medium
  python tools/ui/subset_font.py /path/to/Pretendard-SemiBold.otf --style SemiBold

No runtime download or system-font installation is used. PyQt registers all
three bundled faces and enables tabular numerals. The shared Regular filename
also changes the Flet font asset; registering Medium/SemiBold is a native Qt
change, not a claim that the external AWS website has been updated.

Historical source, superseded by this update: Noto Sans CJK KR Regular,
Debian NotoSansCJK-Regular.ttc SHA256
b76b0433203017ca80401b2ee0dd69350349871c4b19d504c34dbdd80541690a.
OFL-Noto-legacy.txt preserves that earlier original notice; it is not the
provenance or license attribution for the current Pretendard-derived files.

Regular / weight 400
  Upstream: packages/pretendard/dist/public/static/Pretendard-Regular.otf
  Upstream SHA256: 3ffbacde6ab8411f1d2db54bb9b1f0b3ee2a738932033722cf0388c06aed1c93
  Bundled: qg-interface.otf
  Bundled SHA256: 90aded599c3206a647c88f6a81bc5df670fdec6ff2d9c9f241de2d0bf64b6b31
  Bundled bytes: 1411584

Medium / weight 500
  Upstream: packages/pretendard/dist/public/static/Pretendard-Medium.otf
  Upstream SHA256: d39e50e4bb52b4993b6a4eeb821a171254745bd824446af01e1f616b89fface0
  Bundled: qg-interface-medium.otf
  Bundled SHA256: f52aa3022d241b4cd03eb71f64a9389fc298760e057a317305312e24bb44fbbc
  Bundled bytes: 1420644

SemiBold / weight 600
  Upstream: packages/pretendard/dist/public/static/Pretendard-SemiBold.otf
  Upstream SHA256: c89bc43027dc7cde5726e96223376f8eec09302b2fc1f8147fd5b57cfc376118
  Bundled: qg-interface-semibold.otf
  Bundled SHA256: 97c53221c1d3fadc48d692fab9bf5a545159be95a5c0228dc3b8cc24db4ec8dd
  Bundled bytes: 1420648
