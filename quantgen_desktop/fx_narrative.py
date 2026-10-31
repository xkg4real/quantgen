"""Korean display prose for existing FX outputs; canonical evidence is untouched.

Use the existing narrative formatters so displayed precision/units agree with
the original English report. No pricing, calibration or validation is performed.
"""
from core.ficc.common import BP, tenor_label
from core.ficc.insights import _pair, _px, _pct, _bp


def sabr_korean(d):
    bounds = ('미보고' if d['active_bounds'] is None else
              ', '.join(d['active_bounds']) or '보고된 활성 경계 없음')
    residual = ('호가 잔차 NOT_RUN' if d['rmse_vol_points'] is None else
                f"호가 RMSE {d['rmse_vol_points']:.6f} / 최대 절대 잔차 "
                f"{d['max_abs_residual_vol_points']:.6f} 변동성 포인트")
    parameters = '; '.join(f"{p['name']}={p['value']:.9g} [{p['lower']:g}, {p['upper']:g}]"
                           for p in d['parameter_bounds'])
    return (f"SABR 수치 해법 {d['solver_status']}; 활성 경계: {bounds}; {residual}. "
            f"모수 / 보정 경계: {parameters}. "
            f"보정 호가 {d['quote_count']}개 / 자유 모수 {d['free_parameter_count']}개 "
            f"(beta는 {d['fixed_beta']:g}로 고정). 가격 산출 행사가격: {d['pricing_strike_scope']}. "
            "수치 해법의 수렴과 작은 보정 잔차는 호가 지점 밖의 적합 품질을 입증하지 않습니다. "
            "독립 검증: NOT_RUN; 차익거래 검증: NOT_RUN. "
            "Hagan 근사: 행사가격 양쪽의 먼 영역과 장기 만기는 검증되지 않았습니다.")


def fx_korean(out):
    """Translate supported authored prose; return None for untranslated tools."""
    d, q = out.data, out.request
    if q.tool == 'forward':
        pair = _pair(d['pair']); base, quote = pair[:3], pair[4:]
        spot, forward, carry, basis = d['S'], d['forward'], d['carry'], d['basis']
        lines = [
            f"{pair} 현물 {_px(spot)} 대비 CIP 선물환 {_px(forward)}, "
            f"{d['points']:+.1f} 포인트 ({(forward/spot-1)*100:+.2f}%).",
            f"{base} 매수 포지션은 연 {_pct(abs(carry))}의 캐리를 "
            f"{'얻습니다' if carry >= 0 else '지급합니다'} "
            f"({base} 금리에서 {quote} 금리를 뺀 값). 선물환은 이를 일대일로 상쇄합니다. "
            "선물환은 금리 차이를 반영하며 환율 예측값이 아닙니다.",
        ]
        if basis is not None:
            lines.append(f"시장 선물환이 내포한 통화 간 베이시스는 커버드 금리평가 대비 연 {_bp(basis)}이며, "
                         + ("잡음 범위 안입니다." if abs(basis) < 5*BP else
                            f"{base if basis < 0 else quote}의 실제 자금조달 프리미엄을 나타냅니다."))
        return ' '.join(lines)
    if q.tool != 'option':
        return None
    r = d['report']
    lines = [
        f"만기 {tenor_label(r.expiry)} {'콜' if r.call else '풋'}, 행사가격 {_px(r.strike)}, "
        f"현물 {_px(r.spot)} (선물환 {_px(r.forward)}), 변동성 {r.vol*100:.1f}%의 가치는 "
        f"기준 통화 단위당 {r.price:.5f}, 현물의 {r.price_pct_spot*100:.2f}%입니다.",
        f"현물 델타 {r.delta_spot:+.3f} (선물환 델타 {r.delta_fwd:+.3f}), "
        f"현물 1% 변동당 감마 {r.gamma_1pct:+.4f}, 변동성 포인트당 베가 {r.vega:.5f}, "
        f"일별 세타 {r.theta_1d:+.6f}; 상대 / 기준 통화 금리 bp당 로 "
        f"{r.rho_dom*BP:+.6f} / {r.rho_for*BP:+.6f}.",
    ]
    points = d.get('points') or ()
    pts = {p.label: p for p in points}
    put, call = pts.get('25d put'), pts.get('25d call')
    if put and call:
        skew = (call.vol-put.vol)*100
        lines.append('스마일: ' + ', '.join(f"{p.label} {p.vol*100:.2f}% / 행사가격 {_px(p.strike)}" for p in points)
                     + f"; 25d 리스크 리버설은 {skew:+.2f} 변동성 포인트로, "
                     f"시장은 {'콜' if skew > 0 else '풋'}에 더 높은 가격을 지불합니다.")
    if d.get('sabr_diagnostics') is not None:
        lines.append(sabr_korean(d['sabr_diagnostics']))
    return ' '.join(lines)
