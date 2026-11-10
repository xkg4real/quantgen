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


_CHECK_KO = {'call_vertical': '콜 수직 스프레드', 'call_butterfly': '콜 버터플라이',
             'put_vertical': '풋 수직 스프레드', 'put_butterfly': '풋 버터플라이'}
_SCOPE_KO = {'Quoted-mid quality checks only; not proof of tradable arbitrage or an official study verdict':
             '호가 중간값의 품질 점검일 뿐이며, 체결 가능한 차익거래의 증거나 공식 연구 판정이 아닙니다'}


def quote_coverage_text_ko(coverage):
    """Korean twin of `quote_coverage_text`: the same counts and fraction, nothing recomputed; a check
    that was not performed still reads NOT_RUN, never as a pass."""
    parity = coverage['parity']
    text = (f"풋–콜 패리티: 적격 행사가격 {parity['tests']}개 중 {parity['within_fraction']:.0%}가 "
            "양쪽 호가 스프레드 합의 절반 이내입니다. " if parity['tests'] else
            '풋–콜 패리티 미실행 (NOT_RUN): 양방향 호가가 있는 적격 검사가 없습니다. ')
    for key, check in coverage['static'].items():
        name = _CHECK_KO.get(key, key)
        text += (f"{name}: 위반 {check['violations']}건 / 검사 {check['tests']}회. " if check['tests'] else
                 f"{name}: 미실행 (NOT_RUN, 호가가 있는 적격 행사가격 부족). ")
    return text + _SCOPE_KO.get(coverage['scope'], coverage['scope']) + '.'
