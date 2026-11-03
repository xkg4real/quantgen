"""Build the renamed QG Interface font assets without runtime font downloads.

fontTools is a build tool, not a runtime dependency. See assets/fonts/README.txt
for pinned Pretendard sources, their original hashes and the SIL OFL notices.

python tools/ui/subset_font.py /path/to/Pretendard-Regular.otf
python tools/ui/subset_font.py /path/to/Pretendard-Medium.otf --style Medium
python tools/ui/subset_font.py /path/to/Pretendard-SemiBold.otf --style SemiBold

The earlier NotoSansCJK-Regular.ttc rebuild remains supported for provenance.
"""
import argparse
from pathlib import Path
from fontTools import subset
from fontTools.ttLib import TTFont


WEIGHTS = {'Regular': 400, 'Medium': 500, 'SemiBold': 600}


def build(source: str, destination: Path, *, style: str = 'Regular'):
    if style not in WEIGHTS:
        raise ValueError('Unsupported QG Interface style')
    collection = Path(source).suffix.lower() in {'.ttc', '.otc'}
    font = TTFont(source, fontNumber=1 if collection else -1, recalcTimestamp=False)
    family = font['name'].getDebugName(16) or font['name'].getDebugName(1)
    if family not in {'Pretendard', 'Noto Sans CJK KR'}:
        raise ValueError('Expected the documented Pretendard or Korean Noto source')
    if font['OS/2'].usWeightClass != WEIGHTS[style]:
        raise ValueError('Source weight does not match the requested style')
    options = subset.Options()
    options.name_IDs = ['*']; options.name_legacy = True; options.name_languages = ['*']
    options.layout_features = ['*']  # Retain tabular numerals and language shaping.
    options.recalc_timestamp = False
    chars = set()
    for start, stop in ((0x20,0x0250),(0x0370,0x0400),(0x1100,0x1200),(0x2000,0x2700),
                        (0x3000,0x3040),(0x3130,0x3190),(0xAC00,0xD7A4)):
        chars.update(range(start,stop))
    worker = subset.Subsetter(options=options); worker.populate(unicodes=chars); worker.subset(font)
    # Retain copyright/license records, but rename the derivative's family and
    # PostScript identities as required by Pretendard's reserved font name.
    legacy_family = 'QG Interface' if style == 'Regular' else f'QG Interface {style}'
    names = {1:legacy_family,2:'Regular',3:f'QGInterface-{style}-2',4:f'QG Interface {style}',
             6:f'QGInterface-{style}',16:'QG Interface',17:style}
    for record in font['name'].names:
        if record.nameID in names:
            record.string = names[record.nameID].encode(record.getEncoding())
    top = font['CFF '].cff.topDictIndex[0]
    top.FamilyName='QG Interface'; top.FullName=f'QG Interface {style}'
    font['CFF '].cff.fontNames=[f'QGInterface-{style}']
    destination.parent.mkdir(parents=True,exist_ok=True); font.save(destination)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('--style', choices=WEIGHTS, default='Regular')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    suffix = '' if args.style == 'Regular' else '-' + args.style.lower()
    destination = args.output or Path(__file__).resolve().parents[2] / f'assets/fonts/qg-interface{suffix}.otf'
    build(args.source, destination, style=args.style)
