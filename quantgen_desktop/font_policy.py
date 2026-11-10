"""Native interface font: the Flet screen font (owner UI-D4, 2026-11-11) with an offline symbol fallback.

QG Interface is the Pretendard 1.3.9-derived OTF set the Flet app uses (400/500/600, all 11,172 Hangul
syllables). The hinted Gothic A1 TTFs (same family name) stay in assets/fonts unused, for rollback only.
"""
from pathlib import Path
import logging
from PyQt6.QtCore import QChar
from PyQt6.QtGui import QFont,QFontDatabase
INTERFACE_FILES=('qg-interface.otf','qg-interface-medium.otf','qg-interface-semibold.otf')
SYMBOL_FILES=('qg-symbols.otf','qg-symbols-medium.otf','qg-symbols-semibold.otf')
def configure_interface_font(app,font_directory,*,logger=None):
    logger=logger or logging.getLogger(__name__)
    registered=[];complete=True
    for filename in INTERFACE_FILES+SYMBOL_FILES:
        path=Path(font_directory)/filename
        fid=QFontDatabase.addApplicationFont(str(path))
        families=QFontDatabase.applicationFontFamilies(fid) if fid>=0 else []
        expected='QG Symbols' if filename in SYMBOL_FILES else 'QG Interface'
        if fid>=0:registered.append(fid)
        if expected not in families:
            complete=False;logger.warning('QUANTGEN interface font did not load: %s',path)
    if not complete:
        for fid in registered:QFontDatabase.removeApplicationFont(fid)
        logger.warning('QUANTGEN interface font bundle incomplete; using the platform font');return None
    for script in (QChar.Script.Script_Common,QChar.Script.Script_Greek,QChar.Script.Script_Hangul):
        if 'QG Symbols' not in QFontDatabase.applicationFallbackFontFamilies(script):
            QFontDatabase.addApplicationFallbackFontFamily(script,'QG Symbols')
    font=QFont('QG Interface');font.setFamilies(['QG Interface','QG Symbols'])
    font.setPixelSize(14);font.setWeight(QFont.Weight.Normal)
    font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    font.setFeature(QFont.Tag.fromString('tnum'),1);app.setFont(font)
    return 'QG Interface'
