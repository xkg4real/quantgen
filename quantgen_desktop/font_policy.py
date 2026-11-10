"""Native fonts by role (owner decisions UI-D4, UI-D5) with an offline symbol fallback.

Owner, 2026-11-11 (font mockups, plan A): text in IBM Plex Sans KR, numbers kept in the current face
("일단 A로 바꾸고 숫자는 지금 폰트 유지해줘"). So:
  * INTERFACE_FAMILY "IBM Plex Sans KR" (unmodified Google Fonts files, SIL OFL 1.1, Reserved Font
    Name "Plex"; 400/500/600, all 11,172 Hangul syllables) is the application font for all text;
  * NUMBER_FAMILY "QG Interface" (the Pretendard 1.3.9-derived OTF set, 400/500/600, tabular
    figures) draws figures: number/price/delta labels, numeric table cells, chart ticks and the
    watchlist's prices (`number_font`), and is the first fallback for glyphs Plex lacks (μ, σ);
  * "QG Symbols" is the last fallback.
The hinted Gothic A1 TTFs (family name QG Interface) stay in assets/fonts unused, for rollback only.
"""
from pathlib import Path
import logging
from PyQt6.QtCore import QChar
from PyQt6.QtGui import QFont,QFontDatabase
INTERFACE_FAMILY='IBM Plex Sans KR'
NUMBER_FAMILY='QG Interface'
SYMBOL_FAMILY='QG Symbols'
INTERFACE_FILES=('IBMPlexSansKR-Regular.ttf','IBMPlexSansKR-Medium.ttf','IBMPlexSansKR-SemiBold.ttf')
NUMBER_FILES=('qg-interface.otf','qg-interface-medium.otf','qg-interface-semibold.otf')
SYMBOL_FILES=('qg-symbols.otf','qg-symbols-medium.otf','qg-symbols-semibold.otf')
_EXPECTED={**{f:INTERFACE_FAMILY for f in INTERFACE_FILES},**{f:NUMBER_FAMILY for f in NUMBER_FILES},
           **{f:SYMBOL_FAMILY for f in SYMBOL_FILES}}


def _has_family(families,expected):
    # A platform may list a weight under its legacy name ("IBM Plex Sans KR Medium").
    return any(f==expected or f.startswith(expected+' ') for f in families)


def number_font(base):
    """A copy of `base` (size, weight, features kept) that draws figures in NUMBER_FAMILY."""
    font=QFont(base)
    font.setFamilies([NUMBER_FAMILY,INTERFACE_FAMILY,SYMBOL_FAMILY])
    font.setFeature(QFont.Tag.fromString('tnum'),1)
    return font


def configure_interface_font(app,font_directory,*,logger=None):
    logger=logger or logging.getLogger(__name__)
    registered=[];complete=True
    for filename in INTERFACE_FILES+NUMBER_FILES+SYMBOL_FILES:
        path=Path(font_directory)/filename
        fid=QFontDatabase.addApplicationFont(str(path))
        families=QFontDatabase.applicationFontFamilies(fid) if fid>=0 else []
        if fid>=0:registered.append(fid)
        if not _has_family(families,_EXPECTED[filename]):
            complete=False;logger.warning('QUANTGEN interface font did not load: %s',path)
    if not complete:
        for fid in registered:QFontDatabase.removeApplicationFont(fid)
        logger.warning('QUANTGEN interface font bundle incomplete; using the platform font');return None
    for script in (QChar.Script.Script_Common,QChar.Script.Script_Greek,QChar.Script.Script_Hangul):
        for family in (NUMBER_FAMILY,SYMBOL_FAMILY):
            if family not in QFontDatabase.applicationFallbackFontFamilies(script):
                QFontDatabase.addApplicationFallbackFontFamily(script,family)
    font=QFont(INTERFACE_FAMILY);font.setFamilies([INTERFACE_FAMILY,NUMBER_FAMILY,SYMBOL_FAMILY])
    font.setPixelSize(14);font.setWeight(QFont.Weight.Normal)
    font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    font.setFeature(QFont.Tag.fromString('tnum'),1);app.setFont(font)
    return INTERFACE_FAMILY
