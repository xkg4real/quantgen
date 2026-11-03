"""Shared funding inference wording for browser, desktop, AI and export."""
FUNDING_CARD_NOTE = ("Stored funding card is historical and unchanged; its IID bootstrap result "
                     "is not valid confirmation. This analysis does not revalidate that card.")


def funding_text(fc):
    d = getattr(fc, 'diagnostic', {}) or {}
    horizon = d.get('forward_observations', 30)
    p = d.get('p_lower')
    result = (f"Exploratory circular-phase lower-tail p={p:.4g} ({d['cyclic_shifts']} shifts). "
              if p is not None else "Circular-phase diagnostic unavailable: " + d.get('reason', 'not estimated') + ". ")
    return (f"Retrospective full-sample deciles: following {horizon} aligned observations, "
            f"mean log return top={fc.top_decile_fwd30:+.1%}, bottom={fc.bottom_decile_fwd30:+.1%}. "
            f"Event counts top={d.get('top_count', 'unknown')}, bottom={d.get('bottom_count', 'unknown')}; "
            "overlapping windows are not independent samples. IID bootstrap p retired. " + result +
            "Relative cyclic phase must be equiprobable under independence; this assumption is unverified for market data. "
            "Wraparound and structural breaks limit inference. No predictive signal or official validation. " + FUNDING_CARD_NOTE)
