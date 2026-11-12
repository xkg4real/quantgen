Owner decision UI-D6 (2026-11-11, second font mockup round, plan N3): the native desktop app
uses the Pretendard-derived QG Interface OTFs described under LEGACY FLET FONT PROVENANCE below for
text and figures, with tighter tracking and one-step-lighter text weights set in
quantgen_desktop/typography.py. The Flet app and its chart PNGs (ui/qcharts.py) use the same OTFs.
Plan A (IBM Plex Sans KR, UI-D5) was applied and dropped the same day; its files were removed. The
hinted Gothic A1 TTFs below keep the family name QG Interface and stay unused, for rollback only.

Earlier native desktop fonts (2026-11-07, now unused): hinted Gothic A1, renamed QG Interface (400/500/600).
Pinned Google Fonts ref38411257417e616c5d4daa1b9e91a3dbcebe1c2e:
https://github.com/google/fonts/tree/38411257417e616c5d4daa1b9e91a3dbcebe1c2e/ofl/gothica1
Copyright HanYang I&C Co., Ltd.; SIL OFL1.1 in OFL-GothicA1.txt.
Actual TrueType glyph hints and all11172Hangul syllables are preserved.
Registered with matplotlib (ui/qcharts.py) on 2026-11-10 to draw Flet chart PNGs; since
2026-11-11 the charts use the OTFs instead. Only rendered pixels reach the browser.
Missing symbols use the separate QG Symbols family derived from the existing
Pretendard OTF; its OFL.txt and original license name records are preserved.
No runtime download or OS font installation. Browser/Flet OTF stays unchanged.
Rebuild: download GothicA1-{Regular,Medium,SemiBold}.ttf and OFL.txt at the pinned
ref into /tmp/qg-fonts, then run python tools/ui/build_hinted_fonts.py from repo root.
The script requires fontTools at build time only. Linux offscreen checks cannot
prove rendering on every Windows display or display scale.

GothicA1-Regular.ttf source SHA256 211151bea98098c579610ab1114bb1bfe909057207db561f357b896d076c21ac
qg-interface.ttf SHA256 98c3a0825398ab5f2f7f90a7ce66911d47d5fed526855917f4e6278262922c7d
qg-interface.otf source SHA256 90aded599c3206a647c88f6a81bc5df670fdec6ff2d9c9f241de2d0bf64b6b31
qg-symbols.otf SHA256 292089940ba00a4284b8b2d6cef096f96f2f493e9b15955d93c72d02d241195f
GothicA1-Medium.ttf source SHA256 c8a0eb56fa6b13448688fed0799d503fe536a8c6b7acfafdfd580edb9c4c2192
qg-interface-medium.ttf SHA256 853a07f6eb4b756882c43ce6033305963e8be873a4895532272d48951c39beec
qg-interface-medium.otf source SHA256 f52aa3022d241b4cd03eb71f64a9389fc298760e057a317305312e24bb44fbbc
qg-symbols-medium.otf SHA256 78afc4d4d23a930455bfc86a4d1fba4e1b689c1ed742823e280e567a0a2211df
GothicA1-SemiBold.ttf source SHA256 7ee3063f2d626936d8a59dfa21525e7ed19b4e89e8fbb0ea5a924cad9b0cc1f4
qg-interface-semibold.ttf SHA256 40d3b08308d03a86beea77330cc9b29152aafc444dd6886153458456410d51a9
qg-interface-semibold.otf source SHA256 97c53221c1d3fadc48d692fab9bf5a545159be95a5c0228dc3b8cc24db4ec8dd
qg-symbols-semibold.otf SHA256 6446af4f101fcdfddc4e21f74af11622e4a685ffc9142500154390d6cff651f3

LEGACY FLET FONT PROVENANCE (unchanged OTFs)
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
