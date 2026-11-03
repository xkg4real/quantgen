"""Display variants for authored bond/portfolio prose; no pricing or re-solving.

Provider notes, symbols, scenario IDs and unrecognized text remain verbatim.
Canonical narratives and exported result records are kept by the caller.
"""
import re
from core.ficc.common import tenor_label
from core.ficc.insights import _pct, _bp, _money, _top, narrate_bond
from core.quant.insights import narrate_portfolio
from core.quant.history import convention_warning
from core.research.portfolio_disclosure import cap_label


_FLAT = "No curve supplied: flat curve at the bond's own yield; z-spread is trivially 0."
_NOTE_PARTS = (
    (re.compile(re.escape("Weights equalize each asset's contribution to portfolio risk.")),
     lambda m: '각 자산이 포트폴리오 위험에 기여하는 비중을 같게 맞춥니다.'),
    (re.compile(re.escape('No asset has positive estimated excess return over the risk-free rate. '
                         'Maximizing a non-positive Sharpe can favor higher volatility; these '
                         'weights are not evidence of an attractive or low-risk allocation.')),
     lambda m: '무위험금리보다 높은 추정 수익률을 가진 자산이 없습니다. '
               '양수가 아닌 샤프비율을 최대화하면 더 높은 변동성을 선호할 수 있습니다. '
               '이 비중은 매력적이거나 위험이 낮은 배분이라는 근거가 아닙니다.'),
    (re.compile(r'Requested per-asset cap (?P<requested>\d+\.\d{10}%) was adjusted to '
                r'(?P<effective>\d+\.\d{10}%) by the existing fully-invested feasibility bound '
                r'\(1/N \+ 1e-9, at most 1\)\.'),
     lambda m: f"요청한 종목당 상한 {m['requested']}를 기존 완전투자 가능 범위 "
               f"(1/N + 1e-9, 최대 1)에 따라 {m['effective']}로 조정했습니다."),
    (re.compile(re.escape('Solver did not report convergence; treat weights as approximate.')),
     lambda m: '최적화 계산기가 수렴을 보고하지 않았으므로 비중은 근삿값으로 보세요.'),
)


def model_note_korean(note):
    """Translate only an entire known engine note, never substrings of raw notes."""
    if note == _FLAT:
        return '곡선이 제공되지 않아 채권 자체 수익률의 평탄 곡선을 사용합니다. z-스프레드는 자명하게 0입니다.'
    remaining, parts = note, []
    while remaining:
        for pattern, render in _NOTE_PARTS:
            match = pattern.match(remaining)
            if match and (match.end() == len(remaining) or remaining[match.end()] == ' '):
                parts.append(render(match))
                remaining = remaining[match.end():].lstrip(' ')
                break
        else:
            return note
    return ' '.join(parts)


def bond_korean(a, scenarios=()):
    b, cr = a.bond, a.carry_roll
    name = b.name or f'{_pct(b.coupon)} {tenor_label(b.maturity)} 채권'
    lines = [
        f'{name}은 연 {b.freq}회 쿠폰을 지급하며 액면 {b.face:g}당 가격 {a.price:.3f}, '
        f'수익률 {_pct(a.ytm,3)}입니다. 매콜리 듀레이션 {a.macaulay:.2f}y, '
        f'수정 듀레이션 {a.modified:.2f}, 볼록성 {a.convexity:.1f}입니다.',
        f'명목금액 {_money(b.notional)}의 DV01은 bp당 {_money(a.dv01)}입니다. '
        f'+100bp 평행 상승 시 볼록성을 반영하기 전 대략 {_money(a.dv01*100)}의 손실이 발생합니다.',
    ]
    if a.krd:
        t,v = _top(a.krd)
        share = v/sum(a.krd.values()) if sum(a.krd.values()) else 0.0
        lines.append(f'주요 만기 금리위험은 {tenor_label(t)}에 집중됩니다 '
                     f'(bp당 {_money(v)}, 전체의 {share*100:.0f}%).')
    lines.append(f'곡선 대비 z-스프레드는 {_bp(a.z_spread)}이며 곡선 가격은 {a.curve_price:.3f}입니다.')
    be = (f'손실이 나기 전 금리가 {cr.breakeven_bp:.1f}bp까지 상승할 수 있습니다'
          if cr.total >= 0 else
          f'캐리와 롤다운의 합이 음수이므로 손익분기를 위해서는 해당 기간 금리가 '
          f'{abs(cr.breakeven_bp):.1f}bp 하락해야 합니다')
    lines.append(f'{tenor_label(cr.horizon)} 기간의 액면 {b.face:g}당 캐리는 {cr.carry:+.3f}, '
                 f'롤다운은 {cr.rolldown:+.3f}, 합계는 {cr.total:+.3f}입니다. 따라서 {be}.')
    lines.append('펀딩에는 price * (1 / DF(h) - 1)을 사용하며 h는 만기로 제한합니다. '
                 '곡선 기반 펀딩 대용값이며 체결 가능한 레포 호가가 아닙니다.')
    if scenarios:
        worst,best = min(scenarios,key=lambda r:r.pnl),max(scenarios,key=lambda r:r.pnl)
        lines.append(f"{len(scenarios)}개 시나리오 중 최악은 '{worst.name}': "
                     f"{_money(worst.pnl,signed=True)} ({worst.pnl_pct*100:+.2f}%), "
                     f"최선은 '{best.name}': {_money(best.pnl,signed=True)} ({best.pnl_pct*100:+.2f}%)입니다.")
    if a.note: lines.append(model_note_korean(a.note))
    return ' '.join(lines)


def portfolio_korean(p):
    top = sorted(zip(p.symbols,p.weights),key=lambda x:-x[1])[:3]
    top_text = ', '.join(f'{s} {w*100:.0f}%' for s,w in top)
    lines = [f'{p.objective.replace("_","-")} 포트폴리오의 주요 비중은 {top_text}입니다. '
             f'추정 연율 수익률 {p.ann_return*100:+.1f}%, 변동성 {p.ann_vol*100:.1f}%, '
             f'샤프비율 {p.sharpe:.2f}입니다.']
    if p.risk_contrib is not None:
        symbol,rc = sorted(zip(p.symbols,p.risk_contrib),key=lambda x:-x[1])[0]
        lines.append(f'{symbol}은 포트폴리오 전체 위험의 {rc*100:.0f}%를 기여합니다. '
                     '투자 비중과 위험 기여도는 같지 않습니다.')
    if not p.converged:
        lines.append('최적화 계산기가 수렴하지 않았으므로 이 비중은 근삿값으로 보세요.')
    if p.note: lines.append(model_note_korean(p.note))
    lines.append('기대 수익률은 표본 기간에서 추정하며 여기서 가장 불안정한 입력입니다. '
                 '수익률 예측보다 변동성 구조가 더 신뢰할 만합니다.')
    return ' '.join(lines)


def portfolio_scope_korean(portfolios, objective):
    p = portfolios[objective]
    cap = (f'{p.requested_max_weight:.2%} 요청 → {p.effective_max_weight:.8%} 유효'
           if p.requested_max_weight != p.effective_max_weight else cap_label(p))
    return (f'선택 목적 {objective}: 종목당 상한 {cap}. 요청한 상한은 선택한 목적에만 적용합니다. '
            '다른 목적의 행, 효율적 투자선과 무작위 구름은 종목당 상한 100%를 사용합니다. '
            '모두 롱온리·완전투자이며 equal_weight는 각 비중을 1/N로 고정합니다. '
            '상한이 다르면 동일 조건의 효율적 투자선 비교가 아닙니다.')


def convention_korean(out):
    if not out.convention_warning or out.convention_warning != convention_warning(out.histories):
        return out.convention_warning
    total = ', '.join(h.symbol for h in out.histories if h.adjustment=='total')
    split = ', '.join(h.symbol for h in out.histories if h.adjustment=='split')
    return (f'수익률 규약 혼합: {total}에는 배당 재투자가 포함되고 {split}는 가격만 반영합니다 '
            '(배당 미포함). 배당수익률만큼 수익률이 달라 비중과 비교가 첫 번째 그룹 쪽으로 기울어집니다. '
            '동일 조건 비교를 위해 모든 종목에 같은 규약을 사용하세요. 총수익률은 Yahoo '
            '(KRX 코드는 005930.KS), 가격수익률은 KIS (미국 티커는 NAS:AAPL)를 사용합니다.')


def bond_notes(out, language):
    ko = language == 'ko'
    narrative = out.narrative
    if ko and narrative == narrate_bond(out.analytics,list(out.scenarios) if out.scenarios else None):
        narrative = bond_korean(out.analytics,out.scenarios)
    source = out.panel.source
    if source == 'SYNTHETIC':
        source = '합성 곡선 · 현재 시장 데이터 아님' if ko else 'Synthetic curve · not current market data'
    return '\n'.join(n for n in [source,
        f'{out.curve.source} · {out.curve.date} · {out.curve.method} · {len(out.panel)} '
        + ('거래일' if ko else 'sessions'),
        out.panel.note,out.curve.note,
        model_note_korean(out.analytics.note) if ko else out.analytics.note,narrative] if n)


def hedge_text(hedge, language):
    if not hedge: return ''
    pos,ctd,cf,n = hedge
    if language == 'ko':
        return (f'선물 매도 {n:,.2f}계약 · 반올림 {round(n):,}\n'
                f'포지션 DV01 {pos:,.2f} × 전환계수 {cf:.4f} / CTD DV01 {ctd:,.2f}\n'
                f'반올림 후 잔여 DV01 {pos-round(n)*ctd/cf:+,.2f} / bp · 실제 주문 없음')
    return (f'Sell futures {n:,.2f} contracts · rounded {round(n):,}\n'
            f'Position DV01 {pos:,.2f} × CF {cf:.4f} / CTD DV01 {ctd:,.2f}\n'
            f'Residual DV01 after rounding {pos-round(n)*ctd/cf:+,.2f} per bp · no real orders')


def portfolio_notes(out, language, disclosure):
    ko = language == 'ko'
    chosen = out.portfolios[out.request.objective]
    narrative = out.narrative
    if ko and narrative == narrate_portfolio(chosen): narrative = portfolio_korean(chosen)
    sources = [f'{h.symbol}: {h.source} · {h.first_date} → {h.last_date} · {h.note}' for h in out.histories]
    notes = [f'공통 {out.stats.sessions}개 거래일' if ko else f'Common {out.stats.sessions} sessions',
             *sources,convention_korean(out) if ko else out.convention_warning,
             *[f'{name}: {model_note_korean(p.note) if ko else p.note}'
               for name,p in out.portfolios.items() if p.note],narrative,
             portfolio_scope_korean(out.portfolios,out.request.objective) if ko else disclosure['summary']]
    synthetic = [h.symbol for h in out.histories if h.source=='SYNTHETIC']
    if synthetic:
        notes.insert(0,('합성 데이터: ' if ko else 'Synthetic data: ') + ', '.join(synthetic)
                     + (' · 투자 배분이 아닌 계산 시연입니다.' if ko else ' · calculation demonstration, not an investment allocation.'))
    return '\n'.join(n for n in notes if n)


def display_variants(label, en, ko):
    """Leave source_text/export evidence intact while switching display variants."""
    label.localized_text = {'en': en, 'ko': ko}
    label.retranslate()
