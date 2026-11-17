import sys, yaml
from pathlib import Path
R = Path(sys.argv[1])
doc = yaml.safe_load((R/"data/macro/series_registry.yaml").read_text(encoding="utf-8"))
series = doc["series"]; groups = doc.get("groups") or {}; gb = doc.get("group_bindings") or {}
def roles(sid):
    raw = list(series[sid].get("bindings") or [])
    for g, m in groups.items():
        if sid in m: raw += list(gb.get(g) or [])
    return raw
for sid, s in series.items():
    rs = roles(sid)
    rstr = ";".join(f"{b['role']}" + (f"@{b.get('consumer')}" if b.get('consumer') else "") + (f"[{','.join(b.get('books') or [])}]" if 'books' in b else "") for b in rs)
    print(f"{sid}|{s.get('obs_kind')}|{s.get('schedule')}|{s.get('market')}|{s.get('timing_class')}|{s.get('frequency')}|{rstr}")
