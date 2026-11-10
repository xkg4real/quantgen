"""Replica of core/skills/macro_daily.py:470-489 (pit_snapshot key/binding bookkeeping) and :542-544 (lag_audit roles),
on the shipped registry, without reading any data: which binding ends up stored per (sid, consumer) key."""
import sys
R = sys.argv[1]; sys.path.insert(0, R)
from core.ficc import contracts as C
reg = C.load_registry()
def consumer_for(b):   # macro_daily.py:207-209
    return b.consumer or {"acting_exposure": "nav", "risk_model": "hedge_state", "forward_sim": "R-28_R-29",
                          "context": "display", "history": "R-22"}[b.role]
for mkt in ("KR", "US"):
    bindings, reads = {}, {}
    for sid in reg.series_ids():
        market = reg.market(sid)
        for b in reg.bindings(sid):
            if b.role == "history": continue
            if b.role == "acting_exposure" and market not in (None, mkt): continue
            key = (sid, b.consumer)
            consumer = consumer_for(b)
            resolved = reg.resolve_binding(sid, consumer)
            if resolved.role == "acting_exposure" and market not in (None, mkt): continue
            if key in bindings:
                print(f"{mkt}: key {key} overwritten: {bindings[key].role} -> {b.role} (read as {resolved.role})")
            bindings[key] = b; reads[key] = resolved.role
    roles = {}
    for (sid, _), b in bindings.items():
        roles.setdefault(sid, set()).add(b.role)
    for sid in ("KRX_069500_OFFICIAL_CLOSE", "SPX_OFFICIAL_CLOSE"):
        print(f"{mkt}: roles[{sid}] = {sorted(roles.get(sid, ()))}; reads = {sorted((k[1], v) for k, v in reads.items() if k[0] == sid)}")
