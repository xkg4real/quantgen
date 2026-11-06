"""Exclude known private structured fields from optional AI commentary.

Market calculations and official verdicts are preserved. This is a field-name
boundary, not a claim to detect private details in arbitrary free-form text.
"""
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import asdict, dataclass, is_dataclass
import datetime as _dt
import json
import math

PRIVATE_WORDS = ("account", "balance", "holding", "credential", "secret",
                 "api_key", "token", "authorization", "owner_decision")


def private_field(name):
    name = str(name).lower().replace("-", "_")
    return any(word in name for word in PRIVATE_WORDS)


def filter_analysis_fields(value):
    if is_dataclass(value) and not isinstance(value, type):
        value = asdict(value)
    if isinstance(value, Mapping):
        return {key: filter_analysis_fields(item) for key, item in value.items()
                if not private_field(key)}
    if isinstance(value, (list, tuple)):
        return [filter_analysis_fields(item) for item in value]
    return deepcopy(value)


# --------------------------------------------------------------------------- #
# One serialiser for every AI commentary request (NEW-M6-12, NEW-M6-19 (b))
# --------------------------------------------------------------------------- #
# The Native preview measures the same UTF-8 JSON (ensure_ascii=False) with the
# same '>' comparison, so a payload the user consented to is never refused later.
AI_PAYLOAD_MAX_BYTES = 180_000

NAN_MARKER = "NaN: not available or not defined"
POS_INF_MARKER = "+inf: not a finite number; read the status or note fields beside it"
NEG_INF_MARKER = "-inf: not a finite number; read the status or note fields beside it"
_NU = "+inf: normal innovations (the fitted Student-t degrees of freedom are at the normal limit, eta = 0)"
_NU_UPPER = ("+inf: the upper end of this interval reaches the normal limit (eta = 0); "
             "normal innovations are not excluded")
_GARCH_HALF_LIFE = "+inf: persistence at or above 1, so a variance shock does not halve"
_GARCH_HALF_LIFE_END = "+inf: this end of the interval reaches persistence 1, where a variance shock does not halve"
_UNCOND = "undefined, because persistence is at or above 1 (no unconditional variance)"
_AR1_HALF_LIFE = "+inf: no decaying AR(1) fit (missing or non-decaying); not slow mean reversion; read the decay status"
_ADF = "NaN: not available; the ADF test could not be computed"
# (enclosing dict key, field key, kind) -> marker; for list elements the list's key
# is the field key. Meanings: core/quant/garch.py:103, :107-108, :142-156, :267-271,
# :473-476; core/quant/strategies.py:284-299; core/research/crypto_workflow.py:58-61;
# core/research/etf_workflow.py:75-77, :152; core/crypto/analytics.py:119, :200-201;
# ui/quant_lab_page.py:381-397. Markers carry no digit other than 0 and 1.
NONFINITE_MEANINGS = {
    ("garch", "nu", "+inf"): _NU,
    ("letf", "nu", "+inf"): _NU,
    ("garch", "nu_interval_95", "+inf"): _NU_UPPER,
    ("garch", "half_life", "+inf"): _GARCH_HALF_LIFE,
    ("garch", "half_life_sessions", "+inf"): _GARCH_HALF_LIFE,
    ("garch", "half_life_interval_95", "+inf"): _GARCH_HALF_LIFE_END,
    ("garch", "uncond_vol_365", "NaN"): "NaN: " + _UNCOND,
    ("garch", "uncond_vol_annual", "NaN"): "NaN: " + _UNCOND,
    ("letf", "uncond_vol", "NaN"): "NaN: " + _UNCOND,
    ("garch", "uncond_vol_annual", "+inf"): "+inf: " + _UNCOND,
    ("kimchi", "half_life_days", "+inf"): _AR1_HALF_LIFE,
    ("ethbtc", "half_life_days", "+inf"): _AR1_HALF_LIFE,
    ("premium_stats", "half_life", "+inf"): _AR1_HALF_LIFE,
    ("kimchi", "adf_p", "NaN"): _ADF,
    ("ethbtc", "adf_p", "NaN"): _ADF,
    ("premium_stats", "adf_p", "NaN"): _ADF,
}
_GENERIC = {"NaN": NAN_MARKER, "+inf": POS_INF_MARKER, "-inf": NEG_INF_MARKER}
MARKER_PREFIXES = ("NaN:", "+inf:", "-inf:")

# Model-facing (English), appended to the user message only when the payload
# carries a marker or a JSON null. _SYSTEM itself is unchanged.
VALUE_NOTE = (
    'Value conventions in the computed results: a string starting "NaN:" marks a value that is not '
    'available or not defined; a string starting "+inf:" or "-inf:" marks an unbounded or limiting '
    'value, not a measurement. The text after the colon gives the meaning (for example "+inf: normal '
    'innovations" for a Student-t degrees-of-freedom parameter). JSON null means the value was missing '
    'or not a finite number in the source. Describe these values by that meaning; never quote them as '
    'numbers or estimate them.')


@dataclass(frozen=True)
class PayloadText:
    text: str          # strict JSON, UTF-8 characters kept (ensure_ascii=False)
    marked: int        # non-finite numbers replaced by a meaning-bearing marker
    nulls: int         # JSON nulls in the text


def _key_text(key):
    """A mapping key as json.dumps would write it."""
    if hasattr(key, "item") and type(key).__module__ == "numpy":
        key = key.item()
    if isinstance(key, str):
        return key
    if isinstance(key, bool):
        return "true" if key else "false"
    if key is None:
        return "null"
    if isinstance(key, int):
        return str(int(key))
    if isinstance(key, float):
        return float.__repr__(key)
    return str(key)


class _Converter:
    def __init__(self):
        self.marked = 0
        self.nulls = 0

    def marker(self, x, parent, field):
        kind = "NaN" if math.isnan(x) else ("+inf" if x > 0 else "-inf")
        self.marked += 1
        return NONFINITE_MEANINGS.get((parent, field, kind)) or _GENERIC[kind]

    def mapping(self, items, field):
        out = {}
        for key, item in items:
            text = _key_text(key)
            if private_field(text):
                continue
            out[text] = self.value(item, field, text)
        return out

    def value(self, o, parent=None, field=None):
        if is_dataclass(o) and not isinstance(o, type):
            o = asdict(o)
        if isinstance(o, Mapping):
            return self.mapping(o.items(), field)
        if isinstance(o, (list, tuple)):
            return [self.value(item, parent, field) for item in o]
        if o is None:
            self.nulls += 1
            return None
        if isinstance(o, (bool, str)):
            return o
        if isinstance(o, (_dt.date, _dt.datetime, _dt.time)):
            return str(o)                               # pd.Timestamp included, as before
        if type(o).__module__.split(".")[0] == "pandas":
            frame = self.pandas(o, parent, field)
            if frame is not None:
                return frame
        kind = getattr(getattr(o, "dtype", None), "kind", "")
        if kind and kind in "mM":                       # numpy datetime64 / timedelta64
            return [str(x) for x in o] if getattr(o, "ndim", 0) else str(o)
        if hasattr(o, "tolist") and not isinstance(o, (int, float)):
            return self.value(o.tolist(), parent, field)    # full length, never cut
        if isinstance(o, int):
            return int(o)
        if isinstance(o, float):
            x = float(o)
            return x if math.isfinite(x) else self.marker(x, parent, field)
        return str(o)

    def pandas(self, o, parent, field):
        import pandas as pd
        if isinstance(o, pd.DataFrame):
            keep_cols = [not private_field(_key_text(c)) for c in o.columns]
            keep_rows = [not private_field(_key_text(i)) for i in o.index]
            split = o.loc[keep_rows, keep_cols].to_dict(orient="split")
            return {"index": self.value(list(split["index"]), field, "index"),
                    "columns": self.value(list(split["columns"]), field, "columns"),
                    "data": self.value(list(split["data"]), parent, field)}
        if isinstance(o, pd.Series):
            keep = [not private_field(_key_text(i)) for i in o.index]
            s = o[keep]
            return {"index": self.value(s.index.tolist(), field, "index"),
                    "values": self.value(s.tolist(), parent, field)}
        return None


def ai_payload_json(payload) -> PayloadText:
    """The exact JSON text sent for AI commentary.

    Field-name privacy boundary first (filter_analysis_fields, unchanged), then a
    strict conversion: arrays and pandas objects in full, numpy scalars as JSON
    numbers or booleans, keys as json.dumps writes them (private ones dropped,
    including keys that only appear after conversion), and NaN / +inf / -inf as
    marker strings that carry the field's meaning. allow_nan=False makes a missed
    non-finite value raise here instead of being sent as a bare token.
    """
    converter = _Converter()
    obj = converter.value(filter_analysis_fields(payload))
    text = json.dumps(obj, ensure_ascii=False, allow_nan=False)
    return PayloadText(text, converter.marked, converter.nulls)
