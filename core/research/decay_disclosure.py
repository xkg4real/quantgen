"""Plain-language AR(1) diagnostic status shared by ETF and Crypto views."""
def decay_value(info):
    status = (info or {}).get('status', 'NOT_ESTIMATED')
    value = (info or {}).get('half_life')
    if value is None:
        return 'Not decaying' if status == 'NON_DECAYING' else 'Not estimated'
    return f"{value:.2f} · {status.lower()}"


def decay_text(info):
    status = (info or {}).get('status', 'NOT_ESTIMATED')
    if status == 'NOT_ESTIMATED':
        return 'AR(1) half-life not estimated: insufficient, non-finite or unidentified variation. This is not evidence of slow reversion.'
    phi = info['phi']
    if status == 'NON_DECAYING':
        return f'AR(1) phi={phi:.4f}: fitted impulse amplitude does not decay (|phi| ≥ 1); no finite half-life. This does not establish slow mean reversion.'
    if status == 'NO_MEMORY':
        return 'AR(1) phi=0: no serial memory after one observation (half-life 0 is the zero-persistence limit).'
    motion = 'oscillates in sign' if status == 'OSCILLATING' else 'decays monotonically'
    return (f"AR(1) phi={phi:.4f}: the fitted impulse {motion}; its amplitude halves in "
            f"{info['half_life']:.2f} observations. This descriptive estimate is not a stationarity test or an entry-timing signal.")
