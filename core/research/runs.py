"""Versioned observation contract. No provider, engine, ledger or order access."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
import re
from threading import RLock
from uuid import uuid4

SCHEMA = "quantgen.research-run/1"
MAX_EXPORT_BYTES = 1_000_000


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate(run):
    keys = {"schema", "run_id", "kind", "created_at", "finished_at", "execution_status",
            "verdict", "gate_version", "code", "data", "parameters", "metrics", "cost",
            "reproducibility", "error_code", "environment"}
    if not isinstance(run, dict) or set(run) != keys or run["schema"] != SCHEMA:
        raise ValueError("Unsupported ResearchRun shape")
    if run["kind"] != "monte_carlo" or run["execution_status"] not in {"RUNNING", "COMPLETED", "FAILED"}:
        raise ValueError("Unsupported run kind/status")
    if not re.fullmatch(r"[0-9a-f-]{36}", run["run_id"]):
        raise ValueError("Invalid run ID")
    # This adapter has no mandate to create formal investment judgments.
    if run["verdict"] != "NOT_RUN" or run["gate_version"] is not None:
        raise ValueError("This observation adapter cannot assert a gate verdict")
    if run["cost"] != {"status": "NOT_APPLIED", "reason": "price_distribution_not_strategy_backtest"}:
        raise ValueError("Unsupported cost declaration")
    if run["reproducibility"] != "PARTIAL":
        raise ValueError("Unverified provenance cannot assert full reproducibility")
    for field in ("created_at", "finished_at"):
        if run[field] is not None and datetime.fromisoformat(run[field]).tzinfo is None:
            raise ValueError("Run times require timezone")
    if run["created_at"] is None or (run["execution_status"] == "RUNNING") != (run["finished_at"] is None):
        raise ValueError("Inconsistent execution timestamps")
    if set(run["code"]) != {"commit", "working_tree", "calculation_sha256"} or run["code"]["working_tree"] != "NOT_VERIFIED":
        raise ValueError("Invalid code evidence")
    digest=run['code']['calculation_sha256']
    if digest is not None and not re.fullmatch(r'[0-9a-f]{64}',digest): raise ValueError('Invalid calculation hash')
    if set(run['environment']) != {'python','numpy','scipy','pandas','quantgen'}:
        raise ValueError('Missing runtime evidence')
    commit = run["code"]["commit"]
    if commit is not None and not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Invalid code revision")
    if set(run["parameters"]) - {"symbol", "source_requested", "model", "horizon_days", "n_paths", "target", "drift", "rf_rate", "erp", "seed"}:
        raise ValueError("Unknown parameter")
    for key, value in run["parameters"].items():
        if value is not None and not isinstance(value, (str, int, float)):
            raise ValueError("Parameters must be scalar")
        if isinstance(value, str) and len(value) > 120:
            raise ValueError("Parameter too long")
    if run["error_code"] is not None and not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,79}", run["error_code"]):
        raise ValueError("Invalid error category")
    if set(run["metrics"]) - {"spot", "p05", "p50", "p95", "prob_loss", "var_pct", "cvar_pct"}:
        raise ValueError("Unknown result field")
    if any(not _number(v) for v in run["metrics"].values()):
        raise ValueError("Non-finite metric")
    if run["data"] is not None:
        d = run["data"]
        if set(d) != {"symbol", "source", "first_observation", "last_observation", "observations",
                      "fingerprint_sha256", "loaded_at", "provider_retrieved_at", "vintage",
                      "adjustment", "timezone", "calendar", "license", "synthetic"}:
            raise ValueError("Unknown data evidence field")
        if not re.fullmatch(r"[0-9a-f]{64}", d["fingerprint_sha256"]):
            raise ValueError("Invalid input fingerprint")
        if d["license"] != "NOT_VERIFIED" or type(d["synthetic"]) is not bool:
            raise ValueError("Invalid license/synthetic evidence")
        if d["synthetic"] != (d["source"] == "SYNTHETIC"):
            raise ValueError("Contradictory synthetic evidence")
        if d["vintage"] != "NOT_VERIFIED" or d["provider_retrieved_at"] is not None:
            raise ValueError("Unsupported vintage claim")
    if run["execution_status"] == "COMPLETED":
        if run["data"] is None or set(run["metrics"]) != {"spot", "p05", "p50", "p95", "prob_loss", "var_pct", "cvar_pct"}:
            raise ValueError("Completed run lacks results")
        for key in ("horizon_days", "n_paths", "seed"):
            if type(run["parameters"].get(key)) is not int:
                raise ValueError("Completed run requires effective integer parameters")
        m = run["metrics"]
        if not m["p05"] <= m["p50"] <= m["p95"] or not 0 <= m["prob_loss"] <= 1:
            raise ValueError("Invalid distribution")
    canonical(run)  # also refuses NaN in nested parameters
    return run


def new_run(parameters, *, code=None, environment=None):
    run = dict(schema=SCHEMA, run_id=str(uuid4()), kind="monte_carlo", created_at=utc_now(),
               finished_at=None, execution_status="RUNNING", verdict="NOT_RUN", gate_version=None,
               code=code or {"commit": None, "working_tree": "NOT_VERIFIED", "calculation_sha256":None}, data=None,
               parameters=deepcopy(parameters), metrics={},
               cost={"status": "NOT_APPLIED", "reason": "price_distribution_not_strategy_backtest"},
               reproducibility="PARTIAL", error_code=None,
               environment=environment or {k:'NOT_RECORDED' for k in ('python','numpy','scipy','pandas','quantgen')})
    return validate(run)


def completed(run, history, result, *, loaded_at):
    dates, closes = list(history.dates), [float(v) for v in history.closes]
    if not dates or len(dates) != len(closes) or any(not _number(v) for v in closes):
        raise ValueError("Invalid history observations")
    if dates != sorted(set(dates)):
        raise ValueError("History dates must be unique and ascending")
    fingerprint = {"symbol": history.symbol, "source": history.source, "dates": dates,
                   "closes": closes, "adjustment": history.adjustment}
    out = deepcopy(run)
    out.update(execution_status="COMPLETED", finished_at=utc_now(),
        data=dict(symbol=history.symbol, source=history.source, first_observation=dates[0],
            last_observation=dates[-1], observations=len(dates),
            fingerprint_sha256=hashlib.sha256(canonical(fingerprint).encode()).hexdigest(),
            loaded_at=loaded_at, provider_retrieved_at=None, vintage="NOT_VERIFIED",
            adjustment=history.adjustment or "NOT_VERIFIED", timezone="NOT_VERIFIED",
            calendar="NOT_VERIFIED", license="NOT_VERIFIED", synthetic=history.source == "SYNTHETIC"),
        metrics={key: float(getattr(result, attr)) for key, attr in
                 [("spot", "spot"), ("p05", "p05"), ("p50", "median_terminal"), ("p95", "p95"),
                  ("prob_loss", "prob_loss"), ("var_pct", "var_pct"), ("cvar_pct", "cvar_pct")]})
    # Record the engine's effective clamped inputs, not just the UI request.
    out["parameters"].update(model=result.model, n_paths=result.n_paths, horizon_days=result.horizon_days,
                             drift=result.drift_mode, rf_rate=result.rf_rate, erp=result.erp)
    return validate(out)


def failed(run, error_code):
    out = deepcopy(run)
    out.update(execution_status="FAILED", finished_at=utc_now(), error_code=error_code)
    return validate(out)


def computation_fingerprint(run):
    """Stable calculation identity excludes run IDs/times; refuses unknown code."""
    validate(run)
    if run['execution_status'] != 'COMPLETED' or run['code']['calculation_sha256'] is None:
        raise ValueError('Incomplete calculation provenance')
    evidence={k:run[k] for k in ('parameters','metrics','cost','gate_version','verdict','environment')}
    evidence.update(code=run['code']['calculation_sha256'], data=run['data']['fingerprint_sha256'])
    return hashlib.sha256(canonical(evidence).encode()).hexdigest()


def export_bytes(run):
    payload = validate(deepcopy(run))
    # No raw prices, account data, credentials, order intents or filesystem paths.
    body = canonical(payload).encode("utf-8")
    envelope = {"format": "quantgen.read-only-export/1", "audience": "personal_research",
                "order_capable": False, "payload_json": body.decode("utf-8"), "payload_sha256": hashlib.sha256(body).hexdigest()}
    result = (canonical(envelope) + "\n").encode("utf-8")
    if len(result) > MAX_EXPORT_BYTES:
        raise ValueError("Export too large")
    return result


def read_export(raw):
    if len(raw) > MAX_EXPORT_BYTES:
        raise ValueError("Export too large")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result: raise ValueError("Duplicate JSON key")
            result[key] = value
        return result
    e = json.loads(raw, object_pairs_hook=unique)
    if set(e) != {"format", "audience", "order_capable", "payload_json", "payload_sha256"} or e["format"] != "quantgen.read-only-export/1":
        raise ValueError("Unsupported export")
    if e["audience"] != "personal_research" or e["order_capable"] is not False:
        raise ValueError("Not a read-only personal export")
    if not isinstance(e["payload_json"], str): raise ValueError("Payload must be canonical JSON text")
    run = validate(json.loads(e["payload_json"], object_pairs_hook=unique))
    if e["payload_json"] != canonical(run) or hashlib.sha256(e["payload_json"].encode()).hexdigest() != e["payload_sha256"]:
        raise ValueError("Export checksum mismatch")
    return run  # checksum is integrity, not a signature or proof of trusted origin


class SessionResearch:
    """One Flet session; never a replacement for historical trial ledgers."""
    def __init__(self):
        self._lock = RLock()
        self._runs = {}
        self._markets = []
        self.market_loading = False
        self.market_attempted = False

    def put(self, run):
        validate(run)
        with self._lock:
            self._runs[run["run_id"]] = deepcopy(run)

    def runs(self):
        with self._lock:
            return deepcopy(list(reversed(self._runs.values())))

    def start_market_refresh(self):
        with self._lock:
            if self.market_loading: return False
            self.market_loading = self.market_attempted = True
            return True

    def finish_market_refresh(self, rows):
        with self._lock:
            self._markets = deepcopy(rows)
            self.market_loading = False

    def markets(self):
        with self._lock:
            return deepcopy(self._markets)


def session_for(page):
    if not hasattr(page, "_quantgen_research_session"):
        page._quantgen_research_session = SessionResearch()
    return page._quantgen_research_session
