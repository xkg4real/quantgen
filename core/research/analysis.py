"""UI-independent adapter to the existing Quant Lab calculation and evidence contract.

No Qt/Flet dependency, order engine or historical trial-ledger access. Providers
are lazy and injectable so offline verification never needs credentials or caches.
"""
from dataclasses import dataclass
import math

from .runs import completed, utc_now


@dataclass(frozen=True)
class AnalysisRequest:
    symbol: str = "AAPL"
    source_requested: str = "auto"
    model: str = "garch_t"
    horizon_days: int = 126
    n_paths: int = 5000
    target: float | None = None
    drift: str = "premium"
    erp: float = 0.04
    seed: int = 7

    def parameters(self):
        if not self.symbol.strip() or len(self.symbol.strip()) > 120:
            raise ValueError("Enter a symbol of 1–120 characters")
        if self.source_requested not in {"auto", "fmp", "kis", "synthetic"}:
            raise ValueError("Unknown data source")
        if self.model not in {"garch_t", "gbm", "jump", "bootstrap"}:
            raise ValueError("Unknown model")
        if self.drift not in {"premium", "zero", "rf", "sample"}:
            raise ValueError("Unknown drift")
        for name, lo, hi in (("horizon_days", 5, 1260), ("n_paths", 200, 100000), ("seed", 0, 2147483647)):
            value = getattr(self, name)
            if type(value) is not int or not lo <= value <= hi:
                raise ValueError(f"{name} must be an integer between {lo} and {hi}")
        if not math.isfinite(self.erp):
            raise ValueError("ERP must be finite")
        if self.target is not None and (not math.isfinite(self.target) or self.target <= 0):
            raise ValueError("Target must be a positive finite price")
        return dict(symbol=self.symbol.strip(), source_requested=self.source_requested,
                    model=self.model, horizon_days=self.horizon_days, n_paths=self.n_paths,
                    target=self.target, drift=self.drift, erp=self.erp, seed=self.seed)


@dataclass(frozen=True)
class AnalysisOutput:
    run: dict
    result: object
    history: object
    funding_note: str


def funding_rate(symbol, *, series_loader=None, short_rate_loader=None):
    """Same currency choice and explicit 3% fallback as the existing Flet Lab."""
    from core.quant.history import _looks_krx
    if series_loader is None or short_rate_loader is None:
        from core.ficc.data import load_series, load_short_rate
        series_loader = series_loader or load_series
        short_rate_loader = short_rate_loader or load_short_rate
    try:
        if _looks_krx(symbol):
            series = short_rate_loader("KRW", source="auto")
            if series.source == "FRED":
                return series.last, f"rf {series.last:.2%} · KRW 3m · FRED {series.last_date} · monthly"
        else:
            series = series_loader("DGS3MO", source="auto", days=30)
            if series.source == "FRED":
                rate = series.last / 100.0
                return rate, f"rf {rate:.2%} · FRED DGS3MO {series.last_date}"
    except Exception:
        pass
    return 0.03, "rf 3.00% assumed · FRED unavailable"


def execute_analysis(request, run, *, history_loader=None, rate_reader=None, engine=None):
    """Return existing engine results; never turn calculation completion into PASS."""
    params = request.parameters()
    if run["parameters"] != params or run["execution_status"] != "RUNNING":
        raise ValueError("Run does not match the captured request")
    if history_loader is None:
        from core.quant.history import load_history
        history_loader = load_history
    if engine is None:
        from core.quant.montecarlo import run_monte_carlo
        engine = run_monte_carlo
    rate, note = (0.0, "Funding rate not applied for this drift")
    if request.drift in {"premium", "rf"}:
        rate, note = (rate_reader or funding_rate)(params["symbol"])
    history = history_loader(params["symbol"], source=request.source_requested)
    loaded_at = utc_now()
    result = engine(history, model=request.model, horizon_days=request.horizon_days,
                    n_paths=request.n_paths, target=request.target, drift=request.drift,
                    rf_rate=rate, erp=request.erp if request.drift == "premium" else 0.0,
                    seed=request.seed)
    record = completed(run, history, result, loaded_at=loaded_at)
    return AnalysisOutput(record, result, history, note)
