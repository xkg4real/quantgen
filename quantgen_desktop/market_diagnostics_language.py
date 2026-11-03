"""Native display variants for existing diagnostics; never recalculate evidence."""


def decay_korean(info):
    status = (info or {}).get('status', 'NOT_ESTIMATED')
    if status == 'NOT_ESTIMATED':
        return ('AR(1) 반감기 추정 불가: 관측 부족, 유한하지 않은 값 또는 식별할 수 없는 변동입니다. '
                '느린 평균회귀의 근거가 아닙니다.')
    phi = info['phi']
    if status == 'NON_DECAYING':
        return (f'AR(1) phi={phi:.4f}: 적합 충격의 진폭이 감쇠하지 않습니다 (|phi| ≥ 1). '
                '유한한 반감기가 없으며 느린 평균회귀를 입증하지 않습니다.')
    if status == 'NO_MEMORY':
        return 'AR(1) phi=0: 한 관측 이후 시계열 기억이 없습니다 (반감기 0은 지속성이 없는 극한입니다).'
    if status not in ('OSCILLATING', 'MONOTONE'):
        # Preserve future/unknown diagnostics instead of inventing an explanation.
        from core.research.decay_disclosure import decay_text
        return decay_text(info)
    motion = '부호가 진동하며' if status == 'OSCILLATING' else '단조롭게 감쇠하며'
    return (f"AR(1) phi={phi:.4f}: 적합 충격은 {motion} 진폭은 "
            f"{info['half_life']:.2f} 관측 후 절반이 됩니다. "
            '이 기술적 추정은 정상성 검정이나 진입 시점 신호가 아닙니다.')


def funding_korean(fc):
    d = getattr(fc, 'diagnostic', {}) or {}
    horizon = d.get('forward_observations', 30)
    p = d.get('p_lower')
    if p is not None:
        result = f"탐색적 순환 위상 하측 p={p:.4g} ({d['cyclic_shifts']}회 이동). "
    else:
        # Diagnostic reasons are evidence: keep supplied text verbatim.
        result = '순환 위상 진단 불가: ' + d.get('reason', 'not estimated') + '. '
    return (f"전체 표본을 사후적으로 나눈 십분위: 정렬된 다음 {horizon}개 관측의 "
            f"평균 로그수익률은 상위={fc.top_decile_fwd30:+.1%}, 하위={fc.bottom_decile_fwd30:+.1%}. "
            f"사건 수 상위={d.get('top_count', 'unknown')}, 하위={d.get('bottom_count', 'unknown')}; "
            '서로 겹치는 구간은 독립 표본이 아닙니다. IID 부트스트랩 p는 폐기했습니다. ' + result +
            '독립성 아래 상대 순환 위상들이 같은 확률로 발생해야 하며, 시장 데이터에서 이 가정은 검증되지 않았습니다. '
            '끝과 처음을 연결하는 처리와 구조 변화는 추론을 제한합니다. 예측 신호나 공식 검증이 아닙니다. '
            '저장된 펀딩 카드는 변경하지 않은 과거 기록이며, 그 IID 부트스트랩 결과는 유효한 확인 근거가 아닙니다. '
            '이 분석은 해당 카드를 재검증하지 않습니다.')


def coverage_korean(coverage):
    parity = coverage['parity']
    text = (f"풋–콜 패리티: 적격 행사가 {parity['tests']}개에서 "
            f"{parity['within_fraction']:.0%}가 양쪽 스프레드 합의 절반 이내입니다. "
            if parity['tests'] else
            '풋–콜 패리티 NOT_RUN: 적격 양방향 스프레드 검사가 없습니다. ')
    for key, check in coverage['static'].items():
        text += (f"{key}: 위반 {check['violations']}건 / 검사 {check['tests']}회. "
                 if check['tests'] else f'{key}: NOT_RUN (적격 호가 행사가 부족). ')
    scope = coverage['scope']
    if scope == 'Quoted-mid quality checks only; not proof of tradable arbitrage or an official study verdict':
        scope = '호가 중간값의 품질 검사만 수행하며, 체결 가능한 차익거래나 공식 연구 판정의 근거가 아닙니다'
    return text + scope + '.'
