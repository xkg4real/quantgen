"""Native Strategy Lab. Existing costs, trials and gate decisions stay distinct."""
from core.research.strategy_analysis import StrategyRequest
from core.research.strategy_workflow import FAMILIES, narrative, payload
from core.research.strategy_exposure import EXPOSURE_HELP, exposure_lines
from .tools import ToolPane, number, fmt


class StrategyPane(ToolPane):
    def __init__(self):
        tools = [('run', '전략 검증 실행'), ('cards', '저장된 연구카드 읽기')]
        super().__init__('Strategy Lab', tools,
            [(s, s) for s in ('synthetic', 'auto', 'kis', 'fmp', 'yfinance', 'crypto')],
            {'run': [('family', 'Strategy family', [(k, v[0]) for k, v in FAMILIES.items()]),
                     ('symbols', 'Symbols · pairs는 y, x 순서', 'SPY, QQQ, TLT, GLD'),
                     ('cost', 'Cost bp/side · blank = table', ''), ('days', 'Sessions', 1500)],
             'cards': []})
        from .app import label
        self.input_box.layout().addWidget(label('실데이터 실행은 기존 연구 원장에 시행을 기록합니다. 합성 실행은 기록하지 않습니다. '
            '현재 Lab의 DSR 시행 수는 이번 그리드 수입니다. 누적 원장 기반 전환은 별도 작업입니다.', 'caption'))
        self.input_box.layout().addWidget(label(EXPOSURE_HELP, 'caption'))

    def make_request(self):
        if self.tool.currentData() == 'cards':
            return StrategyRequest(tool='cards')
        v = self.values()
        return StrategyRequest(v['family'], tuple(s.strip().upper() for s in v['symbols'].split(',') if s.strip()),
            self.source.currentData(), number(v['cost'], optional=True), number(v['days'], integer=True))

    def show_result(self, out):
        self.clear_result()
        d = out.data
        if out.request.tool == 'cards':
            cards = d['cards']
            self.result_table('Study scorecard', ['Card', 'Kind', 'Decision', 'Reason'],
                [[c['card_id'], c['kind'], c['decision'], c['decision_reason']] for c in cards])
            for c in cards:
                self.text(f"{c['card_id']} · {c['decision']}\n{c['hypothesis']}\n{c['decision_reason']}\n"
                          + '\n'.join(c.get('lines', [])) + '\nSources: ' + '; '.join(c.get('citations', [])))
            self.finished('저장된 연구 기록입니다. 조회는 카드를 재실행하거나 판정을 바꾸지 않습니다.' if cards else 'NOT_LOADED · 저장된 연구카드가 없습니다.')
            return
        sc, wf = d['score'], d['wf']
        safe = payload(d)
        self.text(f"{d['label']} · {', '.join(d['symbols'])}\n"
                  f"sources={', '.join(d['sources'])} · {len(d['panel'])} shared sessions · {d['cost_bps']:g} bp/side")
        if 'SYNTHETIC' in d['sources']:
            self.text('SYNTHETIC · 아래 점수는 합성 시연입니다. 공식 연구카드 판정이 아닙니다.')
        for line in exposure_lines(d.get('exposure')):
            self.text(line)
        self.text(f"Decision: {safe['decision']} · {safe['reason']}")
        self.text(f"Grid/DSR trials {len(d['grid'])}/{sc.n_trials} · cumulative ledger configurations {d['ledger_n']}\n"
                  f"Walk-forward: {wf.note} · last in-sample winner: {d['chosen']}")
        if d.get('convention'): self.text(d['convention'])
        self.result_table('Validation statistics', ['Metric', 'Value'], [
            ('OOS Sharpe', fmt(sc.sr_oos)), ('90% interval', str(sc.ci90)), ('Deflated Sharpe', fmt(sc.dsr)),
            ('PBO', fmt(sc.pbo)), ('OOS / IS', fmt(sc.oos_is)), ('2× cost Sharpe', fmt(sc.sr_stress)),
            ('Positive years', fmt(sc.years_positive, 'pct')), ('Plateau', fmt(sc.plateau, 'pct')),
            ('Plateau edge', str(sc.edge)), ('Trades', sc.n_trades), ('Max drawdown', fmt(sc.max_drawdown, 'pct')),
            ('Benchmark Sharpe', fmt(sc.bench_sr)), ('Benchmark difference', fmt(sc.bench_diff)),
            ('Benchmark p', fmt(sc.bench_p)), ('Haircut Sharpe', fmt(sc.haircut_sr))])
        series = [('Strategy', d['equity'])]
        if d['bench_equity'] is not None: series.append(('Benchmark', d['bench_equity']))
        self.line('Walk-forward equity', range(len(d['equity'])), series, 'OOS observations', 'Equity')
        self.text(' · '.join(d['notes']))
        self.finished(narrative(d))
