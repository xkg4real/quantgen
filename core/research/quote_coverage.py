"""Describe performed quote checks without turning absent coverage into a pass."""


def quote_coverage(arbitrage, parity):
    checks = {}
    for side in ('call', 'put'):
        n = arbitrage['n_' + side + 's']
        for kind, required in (('vertical', 2), ('butterfly', 3)):
            key = side + '_' + kind
            tests = max(n - required + 1, 0)
            checks[key] = {'tests': tests, 'violations': arbitrage[key] if tests else None,
                           'status': 'COMPUTED' if tests else 'NOT_RUN'}
    eligible = [row['within'] for row in parity if row['within'] is not None]
    return {'scope': 'Quoted-mid quality checks only; not proof of tradable arbitrage or an official study verdict',
            'static': checks,
            'parity': {'tests': len(eligible), 'within': sum(eligible) if eligible else None,
                       'within_fraction': sum(eligible) / len(eligible) if eligible else None,
                       'status': 'COMPUTED' if eligible else 'NOT_RUN'}}


def butterfly_display(coverage):
    checks = [coverage['static'][side + '_butterfly'] for side in ('call', 'put')]
    performed = [c for c in checks if c['tests']]
    if not performed:
        return 'NOT_RUN', 'muted'
    total = sum(c['violations'] for c in performed)
    partial = len(performed) != len(checks)
    return str(total) + (' · PARTIAL' if partial else ''), ('error' if total else 'muted' if partial else 'text')


def quote_coverage_text(coverage):
    parity = coverage['parity']
    text = (f"Put–call parity: {parity['within_fraction']:.0%} within half the summed spread "
            f"on {parity['tests']} eligible strikes. " if parity['tests'] else
            'Put–call parity NOT_RUN: no eligible two-sided spread tests. ')
    for key, check in coverage['static'].items():
        text += (f"{key}: {check['violations']} violations / {check['tests']} tests. " if check['tests'] else
                 f'{key}: NOT_RUN (insufficient eligible quoted strikes). ')
    return text + coverage['scope'] + '.'


def static_payload(arbitrage, coverage):
    """Keep existing count names, using null when that inequality was not tested."""
    return {**{key: check['violations'] for key, check in coverage['static'].items()},
            'n_calls': arbitrage['n_calls'], 'n_puts': arbitrage['n_puts'],
            'checks': coverage['static'], 'scope': coverage['scope']}
