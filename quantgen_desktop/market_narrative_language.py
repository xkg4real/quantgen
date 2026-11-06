"""Display-only Korean for authored market prose; evidence stays canonical.

Only a narrative identical to the current local authoring function is replaced.
Provider notes, historical verdicts, model identifiers and unknown prose are raw.
"""
import math
from .market_diagnostics_language import decay_korean, funding_korean, coverage_korean
from core.research.sleeve_disclosure import conventions_korean, sharpe_note_korean, sharpe_text


def display_sharpe_note_korean(sleeves):
    """Use the approved term in freshly authored display text; keep source reports intact."""
    note = sharpe_note_korean(sleeves)
    return note.replace('의 샤프비율은 계산 불가입니다:', '의 샤프 지수는 계산 불가입니다:') if note else note


def display_conventions_korean(conventions):
    note = conventions_korean(conventions)
    return note.replace('각 샤프비율은 준비 구간', '각 샤프 지수는 준비 구간', 1)


def letf_korean(lt):
    assumptions = lt.get('assumptions') or {}
    if assumptions.get('mode') == 'EXPLICIT_SCENARIO':
        convention = ('가격수익률 비교로, beta에 가정 배당수익률을 곱한 값을 더합니다'
                      if assumptions['benchmark'] == 'price_return' else
                      '총수익률 비교로, 분배금이 이미 포함되어 추가 배당 항을 더하지 않습니다')
        dividend = (f", 배당수익률={assumptions['dividend_yield']:.2%}"
                    if assumptions['dividend_yield'] is not None else '')
        carry = (f"사용자 시나리오: {convention}. 연속복리 연율 입력: 조달금리={assumptions['funding_rate']:.2%}, "
                 f"보수={assumptions['annual_fee']:.2%}{dividend}; 시간=거래일/252. "
                 '펀딩·보수·배당 기여분을 각각 표시합니다. 펀딩 기여분은 (1-beta)*r*T이며 '
                 '인버스 펀드의 모형 상대 수익률을 높일 수 있습니다. 이 입력은 가정이며 관측된 펀드 비용이나 '
                 '검증된 분배금이 아닙니다. ZERO_RATE_REFERENCE는 기존 고정 보수와 배당 생략을 사용하는 '
                 '별도 비교 기준으로 유지합니다. ')
    else:
        carry = (f"현재 가정: 금리=0, 연간 보수={lt['fee']:.2%}, 배당 생략. "
                 'ZERO_RATE_REFERENCE는 비교 기준이며 고정 보수는 검증된 현재 펀드 비용이 아닙니다. ')
    return ("AZ 분산 대용값: 직전 63개 관측의 분산을 공식에 대입합니다. "
            "관측된 펀드/지수의 실현 드래그나 연구의 직전 분기 실현 드래그 벤치마크가 아닙니다. "
            "저장된 M_E4 연구는 과거 122630에 관한 것으로, 이 펀드·표본·분산 대용값을 검증하지 않습니다. "
            f"지수 입력: {lt['index_source']}. " + carry +
            "선택한 지수는 분산 입력이며 펀드의 실현 선물 벤치마크가 아닙니다. "
            "펀딩·배당 항과 실제 시장 검증은 별도의 한계로 남습니다. "
            "이 대용값을 펀드 괴리 예측이나 보유 권고로 사용하지 마세요.")


def letf_unavailable_korean(lt):
    # These two errors are authored by etf_workflow. Unknown provider text is raw.
    errors = {
        'Required index history or exact code mapping unavailable; no substitute index used.':
            '필요한 지수 이력 또는 정확한 코드 매핑을 사용할 수 없어 대체 지수를 사용하지 않았습니다.',
        'Index model calculation failed.': '지수 모델 계산에 실패했습니다.',
    }
    return (f"LETF 계산 NOT_RUN · 필요한 지수: {lt['underlying_index']}. "
            f"{errors.get(lt['error'], lt['error'])} 다른 ETF 결과는 계속 사용할 수 있습니다. "
            "합성 지수 데이터는 명시적으로 합성 시연 모드를 선택할 때만 사용합니다.")


def etf_korean(a):
    parts = []
    q = a.get('quote')
    if q:
        parts.append(f"{a['code']}의 가격은 {q['price']:,.0f}, NAV는 {q['nav']:,.2f}, "
                     f"프리미엄은 {q['premium_pct']:+.2f} %, 추적 오차는 {q['tracking_error_pct']:.2f} %, "
                     f"설정 단위당 주식 수는 {q['cu_units']:,.0f}, LP 보유 비율은 {q['lp_holding_pct']:.1f} %입니다.")
    ps = a.get('premium_stats')
    if ps:
        parts.append(f"{len(a['dates'])}개 거래일 동안 평균 프리미엄은 {ps['mean']:+.2f} % "
                     f"(|프리미엄| {ps['abs_mean']:.2f} %)이며, 오늘 값은 평균에서 "
                     f"{ps['z']:+.1f} 표준편차 떨어져 있습니다. ADF p = {ps['adf_p']:.3f}. "
                     + decay_korean(ps.get('decay')))
    sl = a.get('sleeves')
    if sl:
        # §10 NEW-M6-04 / NEW-M6-05, in the same places as the English narrative.
        t, b, v = (sharpe_text(sl[k]) or '계산 불가' for k in ('trend', 'buy_hold', 'vol_target'))
        note = display_sharpe_note_korean(sl)
        parts.append(f"이 펀드의 자체 이력에서 10개월 추세 전환의 샤프 지수는 {t} "
                     f"(최대 낙폭 {sl['trend']['max_drawdown']:.0%}, 투자 비중 {sl['exposure_trend']:.0%})이며, "
                     f"매수 후 보유는 {b} ({sl['buy_hold']['max_drawdown']:.0%}), "
                     f"12 % 변동성 목표는 {v}입니다. 이는 표본 내 기술통계입니다. "
                     f"이 계열의 검증 연구 판정은 추세: {a['verdicts']['trend']}, 변동성 목표: {a['verdicts']['vol']}입니다. "
                     f"이 전략별 수치의 가격 기준: {a.get('sleeve_basis', a.get('data_source'))}."
                     + (' ' + note if note else '')
                     + (' ' + display_conventions_korean(sl['conventions']) if sl.get('conventions') else ''))
    lt = a.get('letf')
    if lt and 'rows' in lt:
        r63 = next(r for r in lt['rows'] if r['sessions'] == 63)
        parts.append(f"{lt['name']} ({lt['beta']:+.0f}×): 직전 분기 분산 AZ 대용값은 "
                     f"63개 관측에 걸쳐 {lt['last_quarter_drag_bp']:+.0f} bp, GARCH 분산 대용값은 "
                     f"63개 관측에 걸쳐 {r63['drag_bp']:+.0f} bp입니다. " + letf_korean(lt))
    elif lt:
        parts.append(letf_unavailable_korean(lt))
    if a.get('data_source') == 'SYNTHETIC':
        parts.append('시계열은 SYNTHETIC이며 위 수치는 시장 데이터가 아닙니다.')
    return ' '.join(parts) or '이력을 불러오지 못했습니다.'


def crypto_korean(a):
    from core.research.crypto_workflow import z_short_window, z_text
    kp, fc, g = a['kimchi'], a['funding'], a['garch']
    parts = [
        f"한국 비트코인 가격은 세계 가격 대비 {kp.last_pct:+.2f} % "
        + ((f"(1년이 안 되는 직전 {w}개 관측 평균에서 {z} 표준편차, " if (w := z_short_window(kp))
            else f"(일년 평균에서 {z} 표준편차, ")
           if (z := z_text(kp.last_z))
           else '(z는 계산할 수 없습니다: 관측이 91개 미만이거나 기간 내 변동이 없습니다, ')
        + f"{kp.dates[0]} 이후 평균 "
        f"{kp.mean_pct:+.2f} %, 최고 {kp.max_pct:.1f} %)입니다. "
        f"{decay_korean(getattr(kp, 'decay', None))} (ADF p = {kp.adf_p:.3f}). "
        '신호이지 거래가 아닙니다. 송금 한도, 트래블룰과 2027년 세금이 차익거래를 제약합니다'
        + (f". 다음 주 수익률의 예측 기울기는 {kp.pred_slope:+.4f} (t {kp.pred_t:+.1f})입니다."
           if math.isfinite(kp.pred_t) else '.'),
    ]
    if fc:
        parts.append(f"무기한 선물 펀딩은 7개 관측 평균 기준 연 {fc.last_ann_pct:+.1f} %이며, "
                     f"역사적 백분위 {fc.percentile:.0%} ({fc.flag})입니다. " + funding_korean(fc))
    parts.append(f"BTCUSDT {g['n']}일에 적합한 GARCH(1,1)-t: ν {g['nu']:.1f}, 지속성 "
                 f"{g['persistence']:.3f} (반감기 {g['half_life']:.0f}일), 365일 기준 조건부 변동성 "
                 f"{g['cond_vol_365']:.0%}"
                 + ('' if g['converged'] else '; 계산기가 수렴하지 않았습니다')
                 + ('; 경계 도달: ' + ', '.join(g['at_bound']) if g['at_bound'] else '')
                 + f". 비트코인에서 이 분포 범위의 검증 연구 판정은 {a['verdicts']['D_C2_garch_btc']}입니다.")
    parts.append(f"ln(ETH/BTC): {a['ethbtc']['verdict']} (ADF p {a['ethbtc']['adf_p']:.3f}). "
                 + decay_korean(a['ethbtc'].get('decay')))
    if a['source'] == 'SYNTHETIC': parts.append('모든 시계열은 SYNTHETIC입니다.')
    return ' '.join(parts)


def derivatives_korean(s):
    from core.research.option_disclosure import box_korean, hedge_korean, mfiv_korean, mfiv_strip
    fq, b, fit, sim = s['futures'], s['basis'], s['svi'], s['hedge']
    mv = s['mfiv']
    txt = [
        f"{s['expiry']} 옵션판 (만기 {s['expiry_date']}, {s['T'] * 365:.0f}일), "
        f"행사가 {s['n_quotes']}개: 패리티 내재 선도는 {s['F']:.2f}, "
        f"{fq.get('name', 'front future')}는 {fq['price']:.2f}, 지수는 {fq['underlying_level']:.2f}입니다.",
        f"최근월 선물은 현물 대비 {b.basis_pts:+.2f}포인트이며, 금리 {s['rate']:.2%} "
        f"({s['rate_source']})에서 보유비용 공정가치는 {b.fair:.2f}입니다. 따라서 "
        f"현물의 {abs(b.mispricing_bp):.0f} bp만큼 {'고평가' if b.rich else '저평가'}되어 있습니다 "
        f"(내재 단리 펀딩 {b.implied_rate:.2%})"
        + (f". KIS 자체 이론가격 {fq['theo']:.2f}와의 차이는 {b.theo_gap_pts:+.2f}포인트이며 배당 포인트 규약입니다."
           if b.theo_gap_pts is not None else '.'),
        f"앱의 Black-76 역산 ATM 내재 변동성은 {s['atm'].iv:.1%}입니다. "
        f"호가 행사가 {s['reconcile']['n']}개에서 거래소 IV와의 중앙 차이는 "
        f"{s['reconcile']['median_volpts']:.2f} 변동성 포인트입니다"
        + (' (0.5포인트 게이트 이내). ' if s['reconcile']['ok'] else ' (0.5포인트 게이트 밖: 규약 확인 필요). ')
        + f"SVI 스마일 적합 RMSE는 {fit.rmse_volpts:.2f} 변동성 포인트, 왜도 ρ는 {fit.rho:+.2f}이며"
        + (' 차익거래가 없습니다.' if fit.arbitrage_free else ' 버터플라이 차익거래 구간이 있습니다.'),
        (f"모형 비의존 내재 변동성은 {mv['n_strikes']}개 행사가에서 {mv['vol']:.1%}입니다 (VKOSPI 방식 스트립). "
         + mfiv_korean(mfiv_strip(s)) if mv.get('n_strikes') else f"모형 비의존 분산 미계산: {mv.get('error', '')}"),
        coverage_korean(s['quote_coverage']),
        box_korean(s),
        f"헤지 시뮬레이션 ({sim.engine}, {sim.n_paths:,}개 경로, {sim.horizon}개 거래일): "
        f"σ_h = {sim.sigma_hedge:.1%}에서 ATM 옵션을 매도하고 매일 델타 헤지하면 모의 평균 손익은 "
        f"명목금액의 {sim.mean_pnl_bp:+.0f} bp (SE {sim.se_bp:.0f} bp), CVaR95 {sim.cvar95_bp:+.0f} bp이며, "
        f"손익분기 실현 변동성은 {sim.breakeven_vol:.1%}입니다. "
        f"항등식 ½Σe^{{r(T−t)}}ΓS²(σ_h² − r²/Δ)Δ는 기울기 {sim.identity_slope:.2f}, "
        f"R² {sim.identity_r2:.2f}로 손익을 설명합니다.",
    ]
    hedge_note = hedge_korean(s)
    if hedge_note:
        txt.append(hedge_note)
    if s.get('garch') is not None:
        g = s['garch']
        txt.append(f"지수 GARCH-t: ν {g.nu:.1f}, 지속성 {g.persistence:.3f}, 조건부 변동성 "
                   f"{g.cond_vol_last:.1%} (보호 조건: {', '.join(g.at_bound) or '이상 없음'}"
                   + ('' if g.converged else '; 계산기 미수렴') + ').')
    return ' '.join(txt)


def market_variants(out, kind):
    from importlib import import_module
    author = import_module('core.research.' + kind + '_workflow').narrative
    if out.narrative != author(out.data): return None
    render = {'etf': etf_korean, 'crypto': crypto_korean, 'derivatives': derivatives_korean}[kind]
    return {'en': out.narrative, 'ko': render(out.data)}
