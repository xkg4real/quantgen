"""Optional asset rebuild; fontTools is a build tool, not a runtime dependency.

python tools/ui/subset_font.py /path/to/NotoSansCJK-Regular.ttc
Source: notofonts/noto-cjk, SIL OFL 1.1. Retain the adjacent license.
"""
from pathlib import Path
import sys
from fontTools import subset
from fontTools.ttLib import TTFont


def build(source: str, destination: Path):
    font = TTFont(source, fontNumber=1)  # Noto Sans CJK KR
    if font['name'].getDebugName(1) != 'Noto Sans CJK KR':
        raise ValueError('Expected Korean Noto Sans CJK collection face')
    options = subset.Options()
    options.name_IDs = ['*']; options.name_legacy = True; options.name_languages = ['*']
    chars = set()
    for start, stop in ((0x20,0x0250),(0x0370,0x0400),(0x1100,0x1200),(0x2000,0x2700),
                        (0x3000,0x3040),(0x3130,0x3190),(0xAC00,0xD7A4)):
        chars.update(range(start,stop))
    worker = subset.Subsetter(options=options); worker.populate(unicodes=chars); worker.subset(font)
    names = {1:'QG Interface',2:'Regular',3:'QGInterface-Regular-1',4:'QG Interface Regular',
             6:'QGInterface-Regular',16:'QG Interface',17:'Regular'}
    for record in font['name'].names:
        if record.nameID in names:
            record.string = names[record.nameID].encode(record.getEncoding())
    top = font['CFF '].cff.topDictIndex[0]
    top.FamilyName='QG Interface'; top.FullName='QG Interface Regular'
    font['CFF '].cff.fontNames=['QGInterface-Regular']
    destination.parent.mkdir(parents=True,exist_ok=True); font.save(destination)


if __name__ == '__main__':
    build(sys.argv[1], Path(__file__).resolve().parents[2] / 'assets/fonts/qg-interface.otf')
