"""Local display translations; canonical macro results and exports stay untouched."""
import re

PAIRS = {
    'Macro · Market observations and local commentary': '매크로 · 시장 관측과 해설',
    'Macro sheet': '매크로 지표', 'Daily commentary': '일일 시장 해설',
    'Weekly rates & FX': '주간 금리·외환',
    'This tab is a descriptive macro sheet. See Analysis tools → Macro v2 for the v2 Overlay, Model cards and Research register.':
    '이 탭은 현재 상태를 설명하는 매크로 지표입니다. v2 오버레이·모형 카드·연구 등록부는 분석 도구의 매크로 v2에서 확인합니다.',
    'descriptive read — not a regime model (P19)': '설명용 관측 — 국면 모형이 아님 (P19)',
    'Descriptive read': '설명용 관측', 'Curve': '수익률곡선', 'Risk': '위험',
    'Dollar': '달러', 'Breakevens': '기대 인플레이션', 'Real yields': '실질금리',
    # The Flet chart title (owner issue 02, PR #98).
    '1y z-scores · descriptive only': '주요 거시 지표: 1년 평균 대비 현재 위치 (z-점수)',
    'Macro indicators': '매크로 지표', 'Group': '분류', 'Last': '최근값',
    '1y z-score': '1년 z점수', '1y percentile': '1년 백분위', 'Observed date': '관측일',
    'rates': '금리', 'credit': '신용', 'fx': '외환', 'risk': '위험',
    'bull steepener': '금리 하락·곡선 가팔라짐', 'bear steepener': '금리 상승·곡선 가팔라짐',
    'bull flattener': '금리 하락·곡선 평탄화', 'bear flattener': '금리 상승·곡선 평탄화',
    'parallel up': '평행 상승', 'parallel down': '평행 하락', 'unchanged': '변화 없음',
    'risk-on': '위험 선호', 'risk-off': '위험 회피', 'neutral': '중립',
    'strong': '강세', 'weak': '약세', 'range': '횡보',
    'rising': '상승', 'falling': '하락', 'stable': '안정',
    'UST 2y': '미국채 2년', 'UST 10y': '미국채 10년', 'UST 30y': '미국채 30년',
    '10y real (TIPS)': '10년 실질금리 (TIPS)', '10y breakeven': '10년 기대 인플레이션',
    'Fed funds': '연방기금금리', 'Broad USD': '광의 USD 지수',
    '10y note future': '10년 미국채 선물', 'Gold': '금',
    'Rate and spread changes are in bp; other changes use their original units. These descriptions do not change validation gates or positions.':
    '금리·스프레드의 변화는 bp, 다른 지표의 변화는 원 단위입니다. 분류는 설명용이며 검증 게이트나 포지션을 바꾸지 않습니다.',
}


def word(value):
    return PAIRS.get(value, value)


def indicator_caption(row):
    """Localize only the exact caption paired with a registered indicator ID."""
    from core.ficc.macro import INDICATORS
    known = {item.id: item.label for item in INDICATORS}
    return word(row.label) if known.get(row.id) == row.label else row.label


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
            f'(20거래일: 10년 {ten}bp, 2년·10년 금리차 {slope}bp); {word(risk)} '
            f'(VIX/HY z {z}); 달러 {word(usd)} (1개월 {pct}%); '
            f'기대 인플레이션 {word(be)}, 실질금리 {word(real)} (1개월 {bc}bp / {rc}bp).')


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
            f'{s.as_of} 기준: 미국채 2년 {level(r("DGS2"))}, 10년 {level(r("DGS10"))}, '
            f'30년 {level(r("DGS30"))}, 2년·10년 금리차 {level(r("T10Y2Y"))}; '
            f'10년 실질금리 {level(r("DFII10"))}, 기대 인플레이션 {level(r("T10YIE"))}; SOFR {level(r("SOFR"))}.',
            f'신용: IG OAS {level(r("BAMLC0A0CM"))}, HY OAS {level(r("BAMLH0A0HYM2"))}. '
            f'달러지수 {level(r("DTWEXBGS"))}, VIX {level(r("VIXCLS"))}, WTI {level(r("DCOILWTICO"))}.',
            summary_korean(s.regime.summary),
        ]
        if s.rows:
            row = max(s.rows, key=lambda x: abs(x.z_1y))
            lines.append(f'가장 크게 이탈한 지표는 {indicator_caption(row)}: {level(row)} ({where(row)})입니다.')
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
            f'{s.as_of} 일일 관측. 금리: 2년 {level(r("DGS2"))} (하루 {chg(r("DGS2"))}, '
            f'한 주 {chg(r("DGS2"), "chg_1w")}), 10년 {level(r("DGS10"))} '
            f'({chg(r("DGS10"))}, {chg(r("DGS10"), "chg_1w")}), 2s10s {level(r("T10Y2Y"))} '
            f'({chg(r("T10Y2Y"))}); 20거래일 수익률곡선 관측(설명용, 국면 모형 아님, P19)은 {word(s.regime.curve)}입니다.',
            f'위험 관측은 {word(s.regime.risk)}: VIX {level(r("VIXCLS"))} ({chg(r("VIXCLS"))}), '
            f'HY OAS {level(r("BAMLH0A0HYM2"))} ({chg(r("BAMLH0A0HYM2"))}); '
            f'달러는 {word(s.regime.dollar)}, {level(r("DTWEXBGS"))} (한 달 {chg(r("DTWEXBGS"), "chg_1m")}); '
            f'기대 인플레이션은 {word(s.regime.inflation)}, 실질금리는 {word(s.regime.real_rates)}입니다.',
        ]
        if by_day:
            lines.append('하루 변동이 가장 큰 지표: ' + '; '.join(
                f'{indicator_caption(x)} {chg(x)}, 최근값 {level(x)}' for x in by_day) + '.')
        if by_z:
            lines.append('직전 연간 분포에서 가장 크게 이탈한 지표: ' + '; '.join(
                f'{indicator_caption(x)} ({where(x)})' for x in by_z) + '.')
        if s.synthetic_ids:
            lines.append(f'주의: {len(s.synthetic_ids)}개 시계열은 합성(SYNTHETIC)입니다.')
    else:
        ten, slope, usd = r('DGS10'), r('T10Y2Y'), r('DTWEXBGS')
        lines = [f'주간 금리·외환 관측, {s.as_of}까지의 자료. {summary_korean(s.regime.summary)}']
        if ten is not None:
            lines.append(f'듀레이션: 미국 10년 국채금리는 {level(ten)}, {sd(ten.z_1y)}이며 '
                         f'한 주(5거래일) 동안 {chg(ten, "chg_1w")} 변했습니다.')
        if slope is not None:
            lines.append(f'곡선: 미국 국채곡선의 기울기인 2년·10년 금리차(10년 빼기 2년)는 {slope.last / i.BP:+.0f}bp, '
                         f'21거래일 변화는 {chg(slope, "chg_1m")}입니다. 2년·10년 금리차 분류는 '
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


# --------------------------------------------------------------------------- #
# Macro sheet screen wording (owner issues 02 and 14, 2026-11-10)
# --------------------------------------------------------------------------- #
# The Flet Macro page fixed "people can't read it" with plain-language names and meanings
# (ui/charts_terms.py, PR #98). The same reviewed wording, Flet-free, for the native sheet. Display only:
# nothing here computes a value; `regime_evidence` re-reads the numbers the core printed in
# `Regime.summary`, and the export keeps the core's own text.

# Indicator id -> Korean chart name with the provider code in brackets (the chart rows).
CHART_NAMES_KO = {
    'DGS2': '미 국채 2년 금리 (UST 2y)', 'DGS10': '미 국채 10년 금리 (UST 10y)',
    'DGS30': '미 국채 30년 금리 (UST 30y)', 'T10Y2Y': '장단기 금리차 10년−2년 (2s10s)',
    'DFII10': '10년 실질금리 (TIPS)', 'T10YIE': '10년 기대인플레이션 (BEI)',
    'SOFR': '담보부 익일물 금리 (SOFR)', 'DFF': '미 연방기금금리 (Fed funds)',
    'BAMLC0A0CM': '투자등급 회사채 스프레드 (IG OAS)', 'BAMLH0A0HYM2': '하이일드 스프레드 (HY OAS)',
    'DTWEXBGS': '달러 지수 (Broad USD)', 'DEXUSEU': '유로/달러 환율 (EUR/USD)',
    'DEXJPUS': '달러/엔 환율 (USD/JPY)', 'DEXKOUS': '달러/원 환율 (USD/KRW)',
    'VIXCLS': '미국 주식 변동성 지수 (VIX)', 'DCOILWTICO': '서부텍사스유 가격 (WTI)',
    'ZN=F': '미 10년 국채선물 (ZN)', 'GC=F': '금 선물 가격 (Gold)',
}

# Indicator group -> chart legend name.
GROUP_NAMES = {
    'rates': {'ko': '금리', 'en': 'Rates'}, 'credit': {'ko': '신용', 'en': 'Credit'},
    'fx': {'ko': '외환', 'en': 'FX'}, 'risk': {'ko': '위험선호', 'en': 'Risk appetite'},
}

# Captions the z-score chart draws.
Z_CHART_TEXTS = {
    'band': {'ko': '평소 범위 (±1)', 'en': 'Usual range (±1)'},
    'unusual': {'ko': '이례적', 'en': 'Unusual'},
    'axis': {'ko': '1년 z-점수 (0 = 1년 평균, ±2 = 이례적)', 'en': '1-year z-score (0 = 1-year average, ±2 = unusual)'},
    'synthetic': {'ko': '합성 데이터 · 실제 관측 아님', 'en': 'Synthetic data · not observed'},
}

# Regime field -> {core word: (Korean meaning, English meaning)}; the Korean words are PAIRS above.
# The rules are those of core/ficc/macro.py, as ui/charts_terms.py states them.
REGIME_MEANINGS = {
    'curve': {
        'bull steepener': ('금리가 내리는 가운데 단기 금리가 더 많이 내려 장단기 금리차가 벌어졌습니다.',
                           'Yields fell and the short end fell more, so the 10y-2y gap widened.'),
        'bear steepener': ('금리가 오르는 가운데 장기 금리가 더 많이 올라 장단기 금리차가 벌어졌습니다.',
                           'Yields rose and the long end rose more, so the 10y-2y gap widened.'),
        'bull flattener': ('금리가 내리는 가운데 장기 금리가 더 많이 내려 장단기 금리차가 줄었습니다.',
                           'Yields fell and the long end fell more, so the 10y-2y gap narrowed.'),
        'bear flattener': ('금리가 오르는 가운데 단기 금리가 더 많이 올라 장단기 금리차가 줄었습니다.',
                           'Yields rose and the short end rose more, so the 10y-2y gap narrowed.'),
        'parallel up': ('장단기 금리가 비슷한 폭으로 올랐습니다.', 'Short and long yields rose by similar amounts.'),
        'parallel down': ('장단기 금리가 비슷한 폭으로 내렸습니다.', 'Short and long yields fell by similar amounts.'),
        'unchanged': ('20거래일 동안 10년 금리와 장단기 금리차가 5bp 미만으로 움직였습니다.',
                      'The 10y yield and the 10y-2y gap moved less than 5bp over 20 sessions.'),
    },
    'risk': {
        'risk-on': ('VIX와 하이일드 스프레드의 1년 z-점수 평균이 -0.5보다 낮습니다(위험을 감수하는 쪽).',
                    'The average of the VIX and high-yield spread 1-year z-scores is below -0.5 (leaning toward '
                    'taking risk).'),
        'risk-off': ('VIX와 하이일드 스프레드의 1년 z-점수 평균이 +0.75보다 높습니다(위험을 피하는 쪽).',
                     'The average of the VIX and high-yield spread 1-year z-scores is above +0.75 (leaning toward '
                     'avoiding risk).'),
        'neutral': ('VIX와 하이일드 스프레드의 1년 z-점수 평균이 -0.5와 +0.75 사이입니다(어느 쪽으로도 뚜렷하게 '
                    '기울지 않음).',
                    'The average of the VIX and high-yield spread 1-year z-scores is between -0.5 and +0.75 (no clear '
                    'lean).'),
    },
    'dollar': {
        'strong': ('달러 지수가 한 달 동안 1.5% 넘게 올랐습니다.', 'The broad dollar rose more than 1.5% in a month.'),
        'weak': ('달러 지수가 한 달 동안 1.5% 넘게 내렸습니다.', 'The broad dollar fell more than 1.5% in a month.'),
        'range': ('달러 지수의 한 달 변화가 ±1.5% 안에 머물렀습니다.', 'The broad dollar stayed within ±1.5% over a month.'),
    },
    'inflation': {
        'rising': ('시장이 예상하는 10년 물가상승률이 한 달 동안 0.10%p 넘게 올랐습니다.',
                   'Market-implied 10-year inflation rose more than 10bp in a month.'),
        'falling': ('시장이 예상하는 10년 물가상승률이 한 달 동안 0.10%p 넘게 내렸습니다.',
                    'Market-implied 10-year inflation fell more than 10bp in a month.'),
        'stable': ('시장이 예상하는 10년 물가상승률의 한 달 변화가 0.10%p 미만입니다.',
                   'Market-implied 10-year inflation moved less than 10bp in a month.'),
    },
    'real_rates': {
        'rising': ('물가를 뺀 10년 실질금리가 한 달 동안 0.15%p 넘게 올랐습니다.',
                   'The 10-year real yield rose more than 15bp in a month.'),
        'falling': ('물가를 뺀 10년 실질금리가 한 달 동안 0.15%p 넘게 내렸습니다.',
                    'The 10-year real yield fell more than 15bp in a month.'),
        'stable': ('물가를 뺀 10년 실질금리의 한 달 변화가 0.15%p 미만입니다.',
                   'The 10-year real yield moved less than 15bp in a month.'),
    },
}

_EVIDENCE = re.compile(
    r'\(10y (?P<d10>[+-]\d+)bp, 2s10s (?P<slope>[+-]\d+)bp over (?P<n>\d+) sessions\).*?'
    r'\(VIX/HY z (?P<risk>[+-][\d.]+)\).*?\((?P<usd>[+-][\d.]+)% 1m\).*?'
    r'\(1m (?P<bei>[+-]\d+)bp / (?P<real>[+-]\d+)bp\)', re.DOTALL)


def regime_evidence(summary):
    """The numbers the core printed in `Regime.summary` as {field: (Korean, English)}; {} for another format."""
    m = _EVIDENCE.search(summary or '')
    if not m:
        return {}
    g = m.groupdict()
    return {
        'curve': (f"{g['n']}거래일: 10년 금리 {g['d10']}bp, 장단기 금리차 {g['slope']}bp",
                  f"{g['n']} sessions: 10y {g['d10']}bp, 2s10s {g['slope']}bp"),
        'risk': (f"VIX·하이일드 평균 z-점수 {g['risk']}", f"VIX/HY average z {g['risk']}"),
        'dollar': (f"1개월 변화 {g['usd']}%", f"1-month change {g['usd']}%"),
        'inflation': (f"1개월 변화 {g['bei']}bp", f"1-month change {g['bei']}bp"),
        'real_rates': (f"1개월 변화 {g['real']}bp", f"1-month change {g['real']}bp"),
    }


_READ_HEADERS = (('curve', 'Curve'), ('risk', 'Risk'), ('dollar', 'Dollar'), ('inflation', 'Breakevens'),
                 ('real_rates', 'Real yields'))


def descriptive_read_lines(regime):
    """Each word of the descriptive read with its meaning and the summary's own numbers, one line per
    field, as {'ko': text, 'en': text}; None when the summary is not the core's format or a word is unknown
    (the caller then shows the summary as before)."""
    evidence = regime_evidence(regime.summary)
    if not evidence:
        return None
    ko, en = [], []
    for field, header in _READ_HEADERS:
        value = getattr(regime, field)
        meaning = REGIME_MEANINGS[field].get(value)
        if meaning is None:
            return None
        ko.append(f'{PAIRS[header]} · {word(value)} — {meaning[0]} ({evidence[field][0]})')
        en.append(f'{header} · {value} — {meaning[1]} ({evidence[field][1]})')
    return {'ko': '\n'.join(ko), 'en': '\n'.join(en)}


def chart_caption_korean(row):
    """Korean chart row name for a registered indicator (id and caption must both match); else the label."""
    from core.ficc.macro import INDICATORS
    known = {item.id: item.label for item in INDICATORS}
    if known.get(row.id) == row.label and row.id in CHART_NAMES_KO:
        return CHART_NAMES_KO[row.id]
    return row.label


def synthetic_notice(sheet):
    """The one synthetic-data notice of the sheet as {'ko', 'en'} (Flet `_synthetic_notice`, PR #98), or
    None when the sheet note is not the core's format (then the note is shown as before)."""
    note = sheet.note or ''
    if not sheet.synthetic_ids or sheet_note_korean(note) == note:
        return None
    ids = ', '.join(sheet.synthetic_ids)
    ko = (f'합성 데이터 사용 중: 지표 {len(sheet.rows)}개 중 {len(sheet.synthetic_ids)}개가 실제 관측이 아닌 '
          f'합성 시계열입니다 ({ids}). 차트에서는 빗금 막대로 표시됩니다.')
    short = re.search(r'Shortest series has (\d+) obs', note)
    if short:
        ko += f' 가장 짧은 시계열이 {short.group(1)}개 관측이라 z-점수·백분위는 252개보다 적은 관측으로 계산했습니다.'
    return {'ko': ko, 'en': 'Synthetic data: ' + note + ' The chart hatches these bars.'}
