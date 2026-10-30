"""Describe the constraints actually used; never re-solve or adjust weights."""


def cap_label(portfolio):
    requested, effective = portfolio.requested_max_weight, portfolio.effective_max_weight
    if requested != effective:
        return f"{requested:.2%} requested → {effective:.8%} effective"
    return f"{effective:.2%}"


def portfolio_disclosure(portfolios, selected_objective):
    chosen = portfolios[selected_objective]
    summary = (
        f"Selected {selected_objective}: per-asset cap {cap_label(chosen)}. "
        "Only the selected objective uses the requested cap. Other objective rows, "
        "the frontier curve and random cloud use a 100% per-asset bound. "
        "All are long-only and fully invested; equal_weight fixes each weight at 1/N. "
        "With different caps, this is not a like-for-like frontier comparison."
    )
    return {
        "selected_objective": selected_objective,
        "long_only": True,
        "fully_invested": True,
        "objectives": {
            name: {
                "role": "selected" if name == selected_objective else "comparison",
                "requested_max_weight": p.requested_max_weight,
                "effective_max_weight": p.effective_max_weight,
                "cap_adjusted": p.requested_max_weight != p.effective_max_weight,
                "fixed_equal_weights": name == "equal_weight",
                "note": p.note,
                "converged": p.converged,
            } for name, p in portfolios.items()
        },
        "frontier": {"effective_max_weight": 1.0, "uses_selected_cap": False},
        "random_cloud": {"effective_max_weight": 1.0, "uses_selected_cap": False},
        "summary": summary,
    }
