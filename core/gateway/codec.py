"""Results to and from JSON for the company route (KEY-3; GATEWAY_DESIGN.md section 1).

Only registered result types cross the wire. Anything else raises CodecError, so a new client cannot leak an
unexpected object (or a credential inside one) to the company server or back."""
from __future__ import annotations

import dataclasses
import datetime as _dt
import importlib
from typing import Any

# kind -> "module:Class" of a dataclass result
REGISTERED = {
    "kis.Quote": "data.krx.kis_client:Quote",
    "fmp.Quote": "data.fmp.quote_client:FMPQuote",
    "market.Candle": "core.market.models:Candle",
    "market.MarketSnapshot": "core.market.models:MarketSnapshot",
    "krx.Answer": "data.krx.gateway:Answer",
}


class CodecError(ValueError):
    pass


def _cls(spec: str):
    module, _, attr = spec.partition(":")
    return getattr(importlib.import_module(module), attr)


def _kind_of(obj: Any) -> str | None:
    for kind, spec in REGISTERED.items():
        module, _, attr = spec.partition(":")
        if type(obj).__module__ == module and type(obj).__name__ == attr:
            return kind
    return None


def encode(obj: Any) -> Any:
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, (list, tuple)):
        return [encode(v) for v in obj]
    if isinstance(obj, dict):
        if not all(isinstance(k, str) for k in obj):
            raise CodecError("only string keys cross the wire")
        return {k: encode(v) for k, v in obj.items()}
    if isinstance(obj, _dt.datetime):
        return {"__kind__": "datetime", "value": obj.isoformat()}
    if isinstance(obj, _dt.date):
        return {"__kind__": "date", "value": obj.isoformat()}
    kind = _kind_of(obj)
    if kind and dataclasses.is_dataclass(obj):
        return {"__kind__": kind,
                "fields": {f.name: encode(getattr(obj, f.name)) for f in dataclasses.fields(obj)}}
    try:
        import pandas as pd
    except Exception:
        pd = None
    if pd is not None and isinstance(obj, pd.DataFrame):
        frame = obj.copy()
        frame.index = [encode(i) if not isinstance(i, (str, int, float)) else i for i in frame.index]
        return {"__kind__": "pandas.DataFrame", "split": encode(frame.to_dict(orient="split"))}
    raise CodecError(f"type not allowed on the wire: {type(obj).__name__}")


def decode(payload: Any) -> Any:
    if isinstance(payload, list):
        return [decode(v) for v in payload]
    if not isinstance(payload, dict):
        return payload
    kind = payload.get("__kind__")
    if kind is None:
        return {k: decode(v) for k, v in payload.items()}
    if kind == "datetime":
        return _dt.datetime.fromisoformat(payload["value"])
    if kind == "date":
        return _dt.date.fromisoformat(payload["value"])
    if kind == "pandas.DataFrame":
        import pandas as pd
        split = decode(payload["split"])
        return pd.DataFrame(split["data"], index=split["index"], columns=split["columns"])
    if kind in REGISTERED:
        cls = _cls(REGISTERED[kind])
        return cls(**{k: decode(v) for k, v in payload["fields"].items()})
    raise CodecError(f"unknown kind on the wire: {kind}")
