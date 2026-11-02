"""Selected-language views of local Signals/Structuring authored explanations.

The original report remains authoritative. No price, signal, hedge or verdict is
recomputed; unknown/user/provider text is left intact.
"""
from .translations import translate

SIGNAL_STANCES = frozenset(('strong bullish', 'bullish', 'neutral', 'bearish', 'strong bearish'))


def localize_columns(table, columns):
    """Tag only caller-selected authored text cells; never all result values."""
    from .localization import CAPTION_ROLE
    columns = sorted(set(table.property('localized_columns') or ()) | set(columns))
    table.setProperty('localized_columns', columns)
    for column in columns:
        for row in range(table.rowCount()):
            item = table.item(row, column)
            if item is not None and item.data(CAPTION_ROLE) is None:
                item.setData(CAPTION_ROLE, item.text())


def localize_cell(table, row, column):
    """Tag one authored value without translating neighboring provider values."""
    from .localization import CAPTION_ROLE
    table.setProperty('localized_columns', sorted(set(table.property('localized_columns') or ()) | {column}))
    item = table.item(row, column)
    if item is not None: item.setData(CAPTION_ROLE, item.text())


def signals_korean(s, b):
    from core.quant.insights import _pct
    agree = [c for c in s.components if c.score * s.composite > 0]
    dissent = [c for c in s.components if c.score * s.composite < 0 and abs(c.score) > 20]
    # Only the display label changes; the original enum and report stay intact.
    stance = translate(s.stance, 'ko') if s.stance in SIGNAL_STANCES else s.stance
    lines = [f'{s.symbol}의 종합 기술적 관측은 {s.composite:+.0f} — {stance}입니다.']
    if agree:
        c = max(agree, key=lambda c: abs(c.score))
        lines.append(f"가장 강하게 지지하는 구성요소는 {translate(c.label, 'ko')} "
                     f"({c.score:+.0f})입니다: {translate(c.reason, 'ko')}")
    if dissent:
        c = max(dissent, key=lambda c: abs(c.score))
        lines.append(f"반대 방향 구성요소: {translate(c.label, 'ko')} "
                     f"({c.score:+.0f}) — {translate(c.reason, 'ko')}")
    else:
        lines.append('종합 관측에 뚜렷하게 반대하는 구성요소는 없습니다.')
    lines += [
        f'{b.symbol}의 {b.strategy} 전략은 {b.sessions}개 거래일 동안 {_pct(b.total_return)}의 수익률로 '
        f'매수 후 보유 ({_pct(b.bench_return)})보다 ' + ('높았습니다.' if b.beat_benchmark else '낮았습니다.'),
        f'시장 노출 기간은 {b.exposure * 100:.0f}%, 거래 횟수는 {b.n_trades}회, 편도 비용은 '
        f'{b.cost_bps:.0f} bps이며 최대 낙폭은 {b.max_drawdown * 100:.1f}%, '
        f'벤치마크의 최대 낙폭은 {b.bench_max_drawdown * 100:.1f}%입니다.',
    ]
    if b.win_rate is not None: lines.append(f'청산 거래 승률: {b.win_rate * 100:.0f}%.')
    if not b.beat_benchmark and b.max_drawdown > b.bench_max_drawdown:
        lines.append('수익률은 낮았지만 낙폭은 더 작았습니다. 수익률을 포기해 보호를 얻는 전략입니다. '
                     '그 교환이 가치 있는지는 백테스트가 아니라 사용자의 위험 감내 수준에 달려 있습니다.')
    elif not b.beat_benchmark:
        lines.append('낙폭을 줄이지 못하면서 수익률이 낮았습니다. 이 설정의 복잡성에 대한 보상이 없습니다.')
    lines.append('하나의 백테스트 기간은 하나의 표본입니다. 이 수치는 예측이 아닌 과거에 대한 설명으로 보세요.')
    return ' '.join(lines)


def structured_korean(p):
    from core.ficc.common import BP, tenor_label
    from core.ficc.insights import _money, _pct
    tr = lambda value: translate(value, 'ko')
    cms = str(getattr(p, 'underlying', '')).startswith('CMS')
    ux = (lambda x: f'{x / BP:+.0f}bp') if cms else (lambda x: f'{x:g}')
    lines = [f'{tr(p.product)}, 명목금액 {_money(p.notional)} {p.currency}, 만기 {tenor_label(p.maturity)}: '
             f'100당 공정가치 {p.fair_value:.2f}, 발행가격 {p.issue_price:.2f}, '
             f'발행자 마진 {p.margin:+.2f}포인트입니다.']
    if p.legs:
        lines.append('구성: ' + '; '.join(f'{tr(l.name)} ({l.kind}) {l.value:+.2f}' for l in p.legs) + '.')
    if getattr(p, 'participation', None) is not None:
        lines.append(f'쿠폰 레버리지는 10y-2y 스프레드의 {p.participation:g}x입니다.' if cms else
                     f'상승분의 {p.participation * 100:.0f}%에 참여합니다.')
    if getattr(p, 'coupon', None) is not None:
        lines.append(
            f'첫 기간 예상 쿠폰은 연율 {_pct(p.coupon)}입니다. '
            '이후 쿠폰은 CMS 쿠폰 구성요소의 기간별 선도 곡선 일정을 따르며, '
            '첫 기간 수치만으로 모든 기간의 쿠폰이 고정되거나 지급이 보장된다고 볼 수 없습니다.'
            if cms else f'연간 쿠폰은 {_pct(p.coupon)}입니다.')
    g = dict(getattr(p, 'greeks', {}) or {})
    if g:
        lines.append('상품 전체 위험: ' + ', '.join(
            f'{k} {_money(v, signed=True)}' if k == 'dv01' else f'{k} {v:+.4g}' for k, v in g.items()) + '.')
    if getattr(p, 'payoff_grid', ()):
        lo, hi = p.payoff_grid[0], p.payoff_grid[-1]
        lines.append(f'만기 지급액은 기초자산 {ux(lo[0])}에서 100당 {lo[1]:.2f}, '
                     f'{ux(hi[0])}에서 {hi[1]:.2f}입니다.')
    if getattr(p, 'hedge', ()):
        lines.append('헤지: ' + '; '.join(f'{h.quantity:,.2f} {tr(h.unit)} {tr(h.instrument)}' for h in p.hedge) + '.')
    if getattr(p, 'note', ''): lines.append(tr(p.note))
    return ' '.join(lines)


def signals_variants(out):
    from core.quant.insights import narrate_signals, narrate_backtest
    original = narrate_signals(out.report) + ' ' + narrate_backtest(out.backtest)
    if original != out.narrative: return None
    return {'en': original, 'ko': signals_korean(out.report, out.backtest)}


def structured_variants(out):
    from core.ficc.insights import narrate_structured
    if out.narrative != narrate_structured(out.report): return None
    return {'en': out.narrative, 'ko': structured_korean(out.report)}


def strategy_variants(data):
    from core.research.strategy_workflow import narrative
    from core.research.strategy_exposure import exposure_lines
    score = data['score']
    decision = (f"판정 보류 — {data['withheld']} " if data.get('withheld') else
                f'판정 {score.decision} — {score.reason}. ')
    head = (f"{data['label']} · {', '.join(data['symbols'])} (공통 거래일 {len(data['panel'])}개, "
            f"편도 {data['cost_bps']:.0f} bp, 설정 {len(data['grid'])}개 = 시행 {score.n_trials}회): "
            + decision + f"마지막 표본 내 최적 설정은 {data['chosen']}입니다.")
    # Score reasons/lines are recorded technical evidence. Translate only the
    # surrounding authored workflow explanation, never turn a withheld result
    # into an apparent decision or alter the cumulative-trials description.
    prose = [translate(line, 'ko') for line in exposure_lines(data.get('exposure'))]
    return {'en': narrative(data), 'ko': head + ' ' + ' '.join(prose + list(score.lines))}
