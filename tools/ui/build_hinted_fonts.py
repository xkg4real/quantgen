from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools import subset
import hashlib,shutil
root=Path('assets/fonts'); lines=[]
for style,suffix in [('Regular',''),('Medium','-medium'),('SemiBold','-semibold')]:
 src=Path('/tmp/qg-fonts')/f'GothicA1-{style}.ttf'
 for source,family,output,remove in [(src,'QG Interface',root/f'qg-interface{suffix}.ttf',None),(root/f'qg-interface{suffix}.otf','QG Symbols',root/f'qg-symbols{suffix}.otf',src)]:
  f=TTFont(source,recalcTimestamp=False); opts=subset.Options();opts.name_IDs=['*'];opts.name_languages=['*'];opts.name_legacy=True;opts.layout_features=['*'];opts.hinting=True;opts.recalc_timestamp=False
  chars=set(f.getBestCmap())
  if remove: chars-=set(TTFont(remove).getBestCmap())
  else: chars={c for c in chars if c<0x2700 or 0x3000<=c<0x3190 or 0xAC00<=c<0xD7A4}
  ss=subset.Subsetter(options=opts);ss.populate(unicodes=chars);ss.subset(f)
  ps=family.replace(' ','');names={1:family if style=='Regular' else f'{family} {style}',2:'Regular',3:f'{ps}-{style}-3',4:f'{family} {style}',6:f'{ps}-{style}',16:family,17:style}
  for r in f['name'].names:
   if r.nameID in names:r.string=names[r.nameID].encode(r.getEncoding())
  if 'CFF ' in f:
   t=f['CFF '].cff.topDictIndex[0];t.FamilyName=family;t.FullName=f'{family} {style}';f['CFF '].cff.fontNames=[f'{ps}-{style}']
  f.save(output)
  lines.append(f'{source.name} source SHA256 {hashlib.sha256(source.read_bytes()).hexdigest()}\n{output.name} SHA256 {hashlib.sha256(output.read_bytes()).hexdigest()}')
shutil.copyfile('/tmp/qg-fonts/OFL.txt',root/'OFL-GothicA1.txt')
old=(root/'README.txt').read_text()
(root/'README.txt').write_text('''Native desktop fonts: hinted Gothic A1, renamed QG Interface (400/500/600).
Pinned Google Fonts ref38411257417e616c5d4daa1b9e91a3dbcebe1c2e:
https://github.com/google/fonts/tree/38411257417e616c5d4daa1b9e91a3dbcebe1c2e/ofl/gothica1
Copyright HanYang I&C Co., Ltd.; SIL OFL1.1 in OFL-GothicA1.txt.
Actual TrueType glyph hints and all11172Hangul syllables are preserved.
Missing symbols use the separate QG Symbols family derived from the existing
Pretendard OTF; its OFL.txt and original license name records are preserved.
No runtime download or OS font installation. Browser/Flet OTF stays unchanged.
Rebuild: download GothicA1-{Regular,Medium,SemiBold}.ttf and OFL.txt at the pinned
ref into /tmp/qg-fonts, then run python tools/ui/build_hinted_fonts.py from repo root.
The script requires fontTools at build time only. Linux offscreen checks cannot
prove rendering on every Windows display or display scale.

'''+ '\n'.join(lines)+'\n\nLEGACY FLET FONT PROVENANCE (unchanged OTFs)\n'+old)
