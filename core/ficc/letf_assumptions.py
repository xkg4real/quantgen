"""Explicit LETF model scenarios; never infer observed funding or dividends."""
import math


def resolve_letf_assumptions(*, funding_rate=None, annual_fee=None,
                             benchmark="zero_rate_reference", dividend_yield=None,
                             reference_fee=0.0064):
    """Rates are annual continuous decimal inputs; time is sessions/252.

    A price-return comparison adds beta*q*T. A total-return comparison already
    includes distributions, so adding q again would double count them. Neither
    convention identifies a real fund's benchmark or validates its financing.
    """
    if benchmark not in {"zero_rate_reference", "total_return", "price_return"}:
        raise ValueError("Choose zero-rate reference, total-return or price-return comparison.")

    def number(name, value, nonnegative=False):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"{name} must be an explicit finite annual decimal rate.")
        if nonnegative and value < 0:
            raise ValueError(f"{name} must be nonnegative.")
        return float(value)

    if benchmark == "zero_rate_reference":
        if any(v is not None for v in (funding_rate, annual_fee, dividend_yield)):
            raise ValueError("Choose a return comparison to apply funding, fee or dividend inputs.")
        return {"mode": "ZERO_RATE_REFERENCE", "benchmark": benchmark, "funding_rate": 0.0,
                "annual_fee": number("Reference fee", reference_fee, True), "dividend_yield": None,
                "funding_source": "REFERENCE_ZERO_NOT_MARKET_DATA",
                "fee_source": "LEGACY_FIXED_ASSUMPTION_NOT_VERIFIED_FUND_FEE", "dividends": "OMITTED",
                "rate_convention": "CONTINUOUS_ANNUAL_DECIMAL", "time_convention": "SESSIONS/252"}
    rate = number("Funding rate", funding_rate)
    fee = number("Annual fee", annual_fee, True)
    if benchmark == "price_return":
        q = number("Dividend yield for the price-return comparison", dividend_yield, True)
    else:
        if dividend_yield is not None:
            raise ValueError("Total-return comparison already includes dividends; do not add a dividend yield.")
        q = None
    return {"mode": "EXPLICIT_SCENARIO", "benchmark": benchmark, "funding_rate": rate,
            "annual_fee": fee, "dividend_yield": q,
            "funding_source": "USER_ASSUMPTION_NOT_MARKET_DATA", "fee_source": "USER_ASSUMPTION_NOT_VERIFIED_FUND_FEE",
            "dividends": "USER_ASSUMPTION" if q is not None else "ALREADY_IN_TOTAL_RETURN_COMPARISON",
            "rate_convention": "CONTINUOUS_ANNUAL_DECIMAL", "time_convention": "SESSIONS/252"}
