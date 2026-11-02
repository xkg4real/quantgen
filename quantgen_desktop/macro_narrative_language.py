"""Local display translations; canonical macro results and exports stay untouched."""
import re

PAIRS = {
    'Macro · Market observations and local commentary': 'Macro · 시장 관측과 로컬 해설',
    'Macro sheet': '거시 지표표', 'Daily commentary': '일일 시장 해설',
    'Weekly rates & FX': '주간 금리·외환',
    'This tab is a descriptive macro sheet. See Markets → Macro v2 for the v2 Overlay, Model cards and Research register.':
    '이 탭은 descriptive macro sheet입니다. v2 Overlay·Model cards·Research register는 Markets의 Macro v2 탭에서 확인합니다.',
    'descriptive read — not a regime model (P19)': '설명용 관측 — 국면 모형이 아님 (P19)',
    'Descriptive read': '설명용 관측', 'Curve': '수익률곡선', 'Risk': '위험',
    'Dollar': '달러', 'Breakevens': '기대 인플레이션', 'Real yields': '실질금리',
    '1y z-scores · descriptive only': '1년 z점수 · 설명용',
    'Macro indicators': '거시 지표', 'Group': '분류', 'Last': '최근값',
    '1y z-score': '1년 z점수', '1y percentile': '1년 백분위', 'Observed date': '관측일',
    'rates': '금리', 'credit': '신용', 'fx': '외환', 'risk': '위험',
    'bull steepener': '금리 하락·곡선 가팔라짐', 'bear steepener': '금리 상승·곡선 가팔라짐',
    'bull flattener': '금리 하락·곡선 평탄화', 'bear flattener': '금리 상승·곡선 평탄화',
    'parallel up': '평행 상승', 'parallel down': '평행 하락', 'unchanged': '변화 없음',
    'risk-on': '위험 선호', 'risk-off': '위험 회피', 'neutral': '중립',
    'strong': '강세', 'weak': '약세', 'range': '횡보',
    'rising': '상승', 'falling': '하락', 'stable': '안정',
    'Rate and spread changes are in bp; other changes use their original units. These descriptions do not change validation gates or positions.':
    '금리·스프레드의 변화는 bp, 다른 지표의 변화는 원 단위입니다. 분류는 설명용이며 검증 게이트나 포지션을 바꾸지 않습니다.',
}


def word(value):
    return PAIRS.get(value, value)


def summary_korean(text):
    # Strict full shape: never substitute inside provider or historical prose.
    pattern = (r'\[descriptive read — not a regime model \(P19\)\] Curve (.+?) '
               r'\(10y ([+-]\d+)bp, 2s10s ([+-]\d+)bp over 20 sessions\); (.+?) '
               r'\(VIX/HY z ([+-]\d+\.\d+)\); dollar (.+?) \(([+-]\d+\.\d+)% 1m\); '
               r'breakevens (.+?), real yields (.+?) \(1m ([+-]\d+)bp / ([+-]\d+)bp\)\.')
    m = re.fullmatch(pattern, text)
    if not m:
        return text
    c, ten, slope, risk, z, usd, pct, be, real, bc, rc = m.groups()
    from core.ficc.macro import CURVE_REGIMES, RISK_REGIMES, DOLLAR_REGIMES, TREND_REGIMES
    if any(value not in allowed for value, allowed in zip(
            (c, risk, usd, be, real),
            (CURVE_REGIMES, RISK_REGIMES, DOLLAR_REGIMES, TREND_REGIMES, TREND_REGIMES))):
        return text
    return (f'[설명용 관측 — 국면 모형이 아님 (P19)] 수익률곡선 {word(c)} '
            f'(20거래일: 10y {ten}bp, 2s10s {slope}bp); {word(risk)} '
            f'(VIX/HY z {z}); 달러 {word(usd)} (1m {pct}%); '
            f'기대 인플레이션 {word(be)}, 실질금리 {word(real)} (1m {bc}bp / {rc}bp).')


def sheet_note_korean(text):
    pattern = (r'(?:(\d+)/(\d+) indicators are SYNTHETIC: ([A-Za-z0-9_=, .-]+)\.)?'
               r'(?: ?Shortest series has (\d+) obs; z/percentile use fewer than 252\.)?')
    m = re.fullmatch(pattern, text)
    if not m:
        return text
    count, total, ids, short = m.groups()
    parts = []
    if count:
        parts.append(f'{total}개 중 {count}개 지표가 합성(SYNTHETIC)입니다: {ids}.')
    if short:
        parts.append(f'가장 짧은 시계열은 {short}개 관측값이며 z점수·백분위는 252개 미만을 사용합니다.')
    return ' '.join(parts)


def macro_korean(output):
    """Return a variant only for a current, exact locally generated narrative."""
    from core.ficc import insights as i
    generators = {'sheet': i.narrate_macro, 'daily': i.narrate_daily_brief,
                  'weekly': i.narrate_weekly_strategy}
    s = output.sheet
    generate = generators.get(output.request.tool)
    if generate is None or output.narrative != generate(s):
        return None
    r = s.row
    level, chg = i._level, i._chg

    def where(row):
        return f'z {row.z_1y:+.1f}, 연간 백분위 {row.pct_1y * 100:.0f}'

    def sd(z):
        return f'직전 252거래일 평균보다 {abs(z):.1f} 표준편차 {"위" if z >= 0 else "아래"}'

    if output.request.tool == 'sheet':
        lines = [
            f'{s.as_of} 기준: UST 2y {level(r("DGS2"))}, 10y {level(r("DGS10"))}, '
            f'30y {level(r("DGS30"))}, 2s10s {level(r("T10Y2Y"))}; '
            f'10y 실질금리 {level(r("DFII10"))}, 기대 인플레이션 {level(r("T10YIE"))}; SOFR {level(r("SOFR"))}.',
            f'신용: IG OAS {level(r("BAMLC0A0CM"))}, HY OAS {level(r("BAMLH0A0HYM2"))}. '
            f'달러지수 {level(r("DTWEXBGS"))}, VIX {level(r("VIXCLS"))}, WTI {level(r("DCOILWTICO"))}.',
            summary_korean(s.regime.summary),
        ]
        if s.rows:
            row = max(s.rows, key=lambda x: abs(x.z_1y))
            lines.append(f'가장 크게 이탈한 지표는 {row.label}: {level(row)} ({where(row)})입니다.')
        if s.synthetic_ids:
            ids = ', '.join(s.synthetic_ids[:6]) + (', ...' if len(s.synthetic_ids) > 6 else '')
            lines.append(f'전체 {len(s.rows)}개 중 {len(s.synthetic_ids)}개 행이 합성(SYNTHETIC)입니다 '
                         f'({ids}): 시장 데이터가 아닌 모의 자료입니다.')
    elif output.request.tool == 'daily':
        rows = list(s.rows)
        by_z = sorted(rows, key=lambda x: abs(x.z_1y), reverse=True)[:3]
        by_day = sorted((x for x in rows if x.chg_1d is not None),
                        key=lambda x: abs(x.chg_1d / (x.last - x.chg_1d)) if x.last != x.chg_1d else 0.,
                        reverse=True)[:3]
        lines = [
            f'{s.as_of} 일일 관측. 금리: 2y {level(r("DGS2"))} (하루 {chg(r("DGS2"))}, '
            f'한 주 {chg(r("DGS2"), "chg_1w")}), 10y {level(r("DGS10"))} '
            f'({chg(r("DGS10"))}, {chg(r("DGS10"), "chg_1w")}), 2s10s {level(r("T10Y2Y"))} '
            f'({chg(r("T10Y2Y"))}); 20거래일 수익률곡선 관측(설명용, 국면 모형 아님, P19)은 {word(s.regime.curve)}입니다.',
            f'위험 관측은 {word(s.regime.risk)}: VIX {level(r("VIXCLS"))} ({chg(r("VIXCLS"))}), '
            f'HY OAS {level(r("BAMLH0A0HYM2"))} ({chg(r("BAMLH0A0HYM2"))}); '
            f'달러는 {word(s.regime.dollar)}, {level(r("DTWEXBGS"))} (한 달 {chg(r("DTWEXBGS"), "chg_1m")}); '
            f'기대 인플레이션은 {word(s.regime.inflation)}, 실질금리는 {word(s.regime.real_rates)}입니다.',
        ]
        if by_day:
            lines.append('하루 변동이 가장 큰 지표: ' + '; '.join(
                f'{x.label} {chg(x)}, 최근값 {level(x)}' for x in by_day) + '.')
        if by_z:
            lines.append('직전 연간 분포에서 가장 크게 이탈한 지표: ' + '; '.join(
                f'{x.label} ({where(x)})' for x in by_z) + '.')
        if s.synthetic_ids:
            lines.append(f'주의: {len(s.synthetic_ids)}개 시계열은 합성(SYNTHETIC)입니다.')
    else:
        ten, slope, usd = r('DGS10'), r('T10Y2Y'), r('DTWEXBGS')
        lines = [f'주간 금리·외환 관측, {s.as_of}까지의 자료. {summary_korean(s.regime.summary)}']
        if ten is not None:
            lines.append(f'듀레이션: 미국 10년 국채금리는 {level(ten)}, {sd(ten.z_1y)}이며 '
                         f'한 주(5거래일) 동안 {chg(ten, "chg_1w")} 변했습니다.')
        if slope is not None:
            lines.append(f'곡선: 미국 국채곡선의 기울기인 2s10s(10y 빼기 2y)는 {slope.last / i.BP:+.0f}bp, '
                         f'21거래일 변화는 {chg(slope, "chg_1m")}입니다. 2s10s 분류는 '
                         f'20거래일 동안 {word(s.regime.curve)}입니다 '
                         '(금리 하락·상승에 따른 bull·bear, 2s10s 확대·축소에 따른 가팔라짐·평탄화, 각각 5bp 초과).')
        if usd is not None:
            lines.append(f'외환: 광의 무역가중 달러지수는 {level(usd)}, 21거래일 변화 {chg(usd, "chg_1m")}, '
                         f'{sd(usd.z_1y)}입니다. 분류는 {word(s.regime.dollar)}입니다 '
                         '(21거래일 변화가 어느 방향이든 1.5%를 넘으면 강세·약세, 그 외 횡보).')
        if s.synthetic_ids:
            lines.append(f'자료 주의: 입력 {len(s.synthetic_ids)}개는 합성(SYNTHETIC)이므로 위 수치는 시장이 아닌 생성기를 설명합니다.')
        lines.append('이 해설은 관측을 설명하며 투자 권고를 하지 않습니다.')
    return ' '.join(lines)
