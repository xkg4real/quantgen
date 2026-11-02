"""Disclosure of existing curve descriptors; no pricing or convention conversion."""

FIVE_YEAR_SIMPLE_LABEL = '5y5y · five-year simple-compounded forward'
FIVE_YEAR_SIMPLE_LABEL_KO = '5y5y · 5년 단리 선도금리'
FIVE_YEAR_SIMPLE_NOTE = (
    '5y5y: (DF(5y) / DF(10y) - 1) / 5y. One simple accrual over five years; '
    'not a forward par swap rate or a semiannually compounded rate.')
FIVE_YEAR_SIMPLE_NOTE_KO = (
    '5y5y: (DF(5y) / DF(10y) - 1) / 5y. 오 년 전체 구간에 단리를 한 번 적용합니다. '
    '선도 파 스왑금리나 반기 복리 금리가 아닙니다.')


def curve_descriptor_conventions():
    """Additive metadata: original descriptor keys and decimal values stay intact."""
    return {'5y5y': {
        'label': FIVE_YEAR_SIMPLE_LABEL,
        'compounding': 'simple_over_full_accrual_period',
        'formula': '(DF(5y) / DF(10y) - 1) / 5y',
        'unit': 'annualized_decimal',
        'start_years': 5, 'end_years': 10, 'accrual_years': 5,
        'is_forward_par_swap_rate': False,
        'note': FIVE_YEAR_SIMPLE_NOTE,
    }}
