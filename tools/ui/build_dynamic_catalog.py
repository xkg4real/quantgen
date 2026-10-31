"""Extract presentation templates; never scan data stores, environment or ledgers."""
import ast
from pathlib import Path
import pprint
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from core.ui_legacy_messages import KO_TO_EN


def atoms(node):
    if isinstance(node,ast.Constant) and isinstance(node.value,str):return [node.value]
    if isinstance(node,ast.JoinedStr):
        return [v.value if isinstance(v,ast.Constant) else None for v in node.values]
    if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Add):return atoms(node.left)+atoms(node.right)
    return [None]


def templates():
    result=set()
    for directory in ('ui','quantgen_desktop'):
        for path in sorted((ROOT/directory).glob('*.py')):
            if path.name in {'indicator_guide.py','data_rights.py','localization.py'}:continue
            for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
                if not isinstance(node,(ast.JoinedStr,ast.BinOp)):continue
                parts=atoms(node)
                if None not in parts or not any(isinstance(s,str) and any('\uac00'<=c<='\ud7a3' for c in s) for s in parts):continue
                chunks=['']
                for part in parts:
                    if part is None:chunks.append('')
                    else:chunks[-1]+=part
                result.add(tuple(chunks))
    return sorted(result,key=lambda row:(-sum(map(len,row)),row))


if __name__=='__main__':
    rows=templates()
    target=ROOT/'core/ui_dynamic_messages.py'
    target.write_text('"""Generated UI templates; rebuild with tools/ui/build_dynamic_catalog.py."""\nTEMPLATES = '+pprint.pformat(rows,width=110,sort_dicts=False)+'\n',encoding='utf-8')
    missing=sorted({part for row in rows for part in row if any('\uac00'<=c<='\ud7a3' for c in part) and part not in KO_TO_EN})
    print('Templates',len(rows),'untranslated literal chunks',len(missing))
    for part in missing:print(repr(part))
