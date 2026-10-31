"""Native Korean display variants of existing rates results, without repricing.

Original model/provider notes and unknown identifiers remain source evidence.
The English narrative and exported report are never rewritten.
"""
import math
from core.ficc.common import BP, tenor_label
from core.ficc.insights import _bp, _pct, _money, _top


SHAPES = {'normal': '정상 우상향', 'inverted': '역전', 'humped': '중간 만기 돌출', 'flat': '평탄'}
REGIMES = {'bull steepener': '금리 하락·기울기 확대', 'bull flattener': '금리 하락·기울기 축소',
           'bear steepener': '금리 상승·기울기 확대', 'bear flattener': '금리 상승·기울기 축소',
           'parallel up': '평행 상승', 'parallel down': '평행 하락', 'unchanged': '변화 없음'}
COMPONENTS = {'level': '수준', 'slope': '기울기', 'curvature': '곡률'}


def curve_korean(r, pca=None):
    d, c, snap = r.descriptors, r.changes, r.snapshot
    lines = [
        f"{snap.date}의 {snap.source} 파 수익률 곡선은 {SHAPES.get(r.shape,r.shape)}입니다: "
        f"2s10s {_bp(d['2s10s'])}, 5s30s {_bp(d['5s30s'])}, 3m10y {_bp(d['3m10y'])}, "
        f"2s5s10s 버터플라이 {_bp(d['2s5s10s_fly'])}, 2y/5y/10y 평균 수준 {_pct(d['level'])}.",
        f"최근 {r.lookback}개 거래일 변화는 {REGIMES.get(r.regime,r.regime)}입니다: "
        f"2y {_bp(c.get('2y'))}, 10y {_bp(c.get('10y'))}, 2s10s {_bp(c.get('2s10s'))}.",
        f"선도금리는 1y1y {_pct(d['1y1y'])}, 2y1y {_pct(d['2y1y'])}, 5y5y {_pct(d['5y5y'])}입니다. "
        f"1y 금리는 향후 일 년간 {_bp(d['1y_fwd_1y_ahead'])} 변화를 가격에 반영합니다.",
        f"{r.ns.method.replace('_','-')} 적합의 파 수익률 오차는 RMS {r.ns.rmse/BP:.1f}bp입니다 "
        f"(가격 산출에는 {r.curve.method} 제로금리 사용).",
    ]
    if pca is not None:
        parts = ', '.join(f'{COMPONENTS.get(lbl,lbl)} {float(e)*100:.0f}%'
                          for lbl,e in zip(pca.labels,pca.explained))
        lines.append(f'일별 변화의 PCA 설명 분산: {parts}'
                     + (f'; 최근 일자의 수준 점수 {float(pca.latest_scores[0]):+.1f}bp, '
                        f'기울기 점수 {float(pca.latest_scores[1]):+.1f}bp.'
                        if len(pca.latest_scores) >= 2 else '.'))
    if 'SYNTHETIC' in str(snap.source).upper():
        lines.append('곡선은 SYNTHETIC (모의) 데이터이므로 이 수치는 시장이 아닌 생성기를 설명합니다.')
    return ' '.join(lines)


def swap_korean(r):
    s = r.swap
    k = r.par_rate if s.fixed_rate is None else s.fixed_rate
    lines = [
        f"{s.label}은 명목금액 {_money(s.notional)}에 고정금리 {_pct(k,3)}를 "
        f"{'지급' if s.pay_fixed else '수취'}합니다. 파 스왑금리 {_pct(r.par_rate,3)} 대비 "
        f"현재 가치 {_money(r.pv,signed=True)} (연금계수 {r.annuity:.3f})입니다.",
        f"+1bp 평행 이동에 대한 DV01은 bp당 {_money(r.dv01,signed=True)}입니다"
        + (f", {tenor_label(_top(r.krd)[0])}에 집중 "
           f"(bp당 {_money(_top(r.krd)[1],signed=True)})." if r.krd else '.'),
        f"곡선이 실현되면 첫 기간 캐리 {_money(r.carry_1y,signed=True)}, "
        f"일 년 롤다운 {_money(r.rolldown_1y,signed=True)}가 발생합니다.",
        '선도 스왑금리: ' + ', '.join(f'{n} {_pct(v,3)}' for n,v in r.fwd_rates.items()) + '.',
    ]
    return ' '.join(lines)


def swaption_korean(r):
    s = r.swaption
    model = 'Bachelier' if r.model == 'bachelier' else 'Black-76'
    vol = f'{r.vol/BP:.0f}bp 정규 변동성' if r.model == 'bachelier' else f'{r.vol*100:.1f}% Black 변동성'
    lines = [
        f"{tenor_label(s.expiry)}x{tenor_label(s.tenor)} "
        f"{'고정금리 지급' if s.payer else '고정금리 수취'} 스왑션은 행사가 {_pct(r.strike,3)}, "
        f"선도금리 {_pct(r.forward,3)} (ATM 대비 {(r.strike-r.forward)/BP:+.0f}bp)입니다. "
        f"{model}, {vol}에서 명목금액 {_money(s.notional)}에 프리미엄 {_money(r.premium)} "
        f"(명목금액의 {r.premium_bp:.1f}bp)입니다.",
        f"선도금리 bp당 델타 {_money(r.delta,signed=True)}, bp 제곱당 감마 {_money(r.gamma,signed=True)}, "
        f"베가 {_money(r.vega)} {r.vega_unit}, 하루 가치 감소 {_money(-r.theta_1d)}입니다.",
    ]
    if math.isfinite(r.other_model_vol):
        other = (f'{r.other_model_vol*100:.1f}% Black' if r.model == 'bachelier'
                 else f'{r.other_model_vol/BP:.0f}bp 정규')
        lines.append(f'같은 프리미엄을 다른 모형으로 환산한 변동성은 {other}입니다.')
    if r.note:
        lines.append(r.note)
    return ' '.join(lines)


def cap_floor_korean(r):
    what = '캡' if r.cap else '플로어'
    model = 'Bachelier' if r.model == 'bachelier' else 'Black-76'
    vol = f'{r.vol/BP:.0f}bp 정규' if r.model == 'bachelier' else f'{r.vol*100:.1f}% Black'
    lines = [f'{what} 행사가 {_pct(r.strike,3)} (ATM {_pct(r.atm_strike,3)}, '
             f'{(r.strike-r.atm_strike)/BP:+.0f}bp)의 프리미엄은 명목금액 {_money(r.notional)}에 '
             f'{_money(r.premium)}, 명목금액의 {r.premium_bp:.1f}bp입니다. '
             f'{model} 모형, {vol} 변동성, {len(r.caplets)}개 {what}렛을 반영합니다.']
    if r.caplets:
        t0,t1,fwd,prem = max(r.caplets,key=lambda c:c[3])
        lines.append(f'가장 비싼 {what}렛의 구간은 {tenor_label(t0)}-{tenor_label(t1)}, '
                     f'선도금리 {_pct(fwd,3)}, 프리미엄 {_money(prem)}입니다. '
                     f'전체 선도금리 범위는 {_pct(r.caplets[0][2],3)}~{_pct(r.caplets[-1][2],3)}입니다.')
    if r.note:
        lines.append(r.note)
    return ' '.join(lines)


def simulation_korean(sim, horizon_pv=None):
    p = sim.params
    name = {'vasicek':'Vasicek','cir':'CIR','hull_white':'Hull-White'}.get(sim.model,sim.model)
    sigma = f'sigma {p.sigma:.4f} × sqrt(r)' if sim.model == 'cir' else f'연 sigma {p.sigma/BP:.0f}bp'
    lines = [
        f'{name} 보정: kappa {p.kappa:.2f} (반감기 {math.log(2)/p.kappa:.1f}y), '
        f'장기 평균 {_pct(p.theta)}, {sigma}, 초기 r0 {_pct(p.r0)}.',
        f'{tenor_label(sim.horizon)} 동안 {sim.n_paths:,}개 경로에서 단기금리 평균은 '
        f'{_pct(sim.mean_terminal)}, 90% 구간은 {_pct(sim.p05)}~{_pct(sim.p95)}입니다.',
    ]
    if sim.prob_above is not None and sim.threshold is not None:
        lines.append(f'모형상 종료 금리가 {_pct(sim.threshold)}를 초과할 확률은 {sim.prob_above*100:.0f}%입니다.')
    if sim.model_curve_at_horizon:
        (t0,z0),(t1,z1) = sim.model_curve_at_horizon[0],sim.model_curve_at_horizon[-1]
        lines.append(f'중앙 경로의 종료 시점 곡선은 {tenor_label(t0)}의 {_pct(z0)}에서 '
                     f'{tenor_label(t1)}의 {_pct(z1)}까지입니다.')
    if horizon_pv is not None:
        h = horizon_pv
        lines.append(f'이 경로들로 재평가한 상품 가치는 평균 {_money(h.mean)} '
                     f'({_money(h.p05)}~{_money(h.p95)}), 종료 시점 95% VaR {_money(h.var95)}, '
                     f'기대 초과손실 {_money(h.cvar95)}입니다.')
    for note in (p.note,sim.note):
        if note:
            lines.append(note + ('.' if not note.endswith('.') else ''))
    return ' '.join(lines)


def rates_korean(out):
    q,r = out.request,out.report
    if q.tool == 'curve': return curve_korean(r,out.pca)
    if q.tool == 'swap': return swap_korean(r)
    if q.tool == 'option': return swaption_korean(r) if q.kind == 'swaption' else cap_floor_korean(r)
    if q.tool == 'sim': return simulation_korean(r,out.horizon_pv)
    return None
