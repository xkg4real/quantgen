"""Native Strategy Lab. Existing costs, trials and gate decisions stay distinct.

Owner UI review 2026-11-10 (port of Claude's Flet fixes, PR #98): the result leads with a plain verdict
(good or bad strategy, why, what next), four headline tiles, the equity chart and every gate criterion in
readable words; study cards show by name with a verdict summary; the commentary is headed bullets in the
window language; and there is no data-source selector (the app asks load_history(source="best") and the
result names the provider that answered). The display lives in strategy_view.py; the export sections
below are recorded exactly as before, so reports do not depend on the screen or its language.
"""
from core.research.presentation import safe_detail
from core.research.strategy_analysis import StrategyRequest
from core.research.strategy_workflow import FAMILIES, narrative, narrative_sections, payload
from core.research.strategy_exposure import EXPOSURE_HELP, exposure_lines
from .tools import ToolPane, number, fmt
from .model_narrative_language import strategy_variants

LEDGER_NOTE = ("Real-data execution records a trial in the existing research ledger. Synthetic execution does "
               "not. Lab DSR currently uses this grid's trial count; cumulative ledger counts are separate work.")
EXAMPLES = ("Examples: US SPY, QQQ · Korean ETF 069500 · crypto BTC-USD, KRW-BTC · pairs take two symbols "
            "(y then x). A blank cost charges QUANTGEN's table rate.")
STORED = '저장된 연구 기록입니다. 조회는 카드를 재실행하거나 판정을 바꾸지 않습니다.'


class StrategyPane(ToolPane):
    # The data source is chosen by the app (owner issues 04/12): 'best' is first and hide_source() keeps
    # it. The other providers stay in the hidden combo so scripts and tests can still ask for one.
    SOURCES = ('best', 'auto', 'kis', 'fmp', 'yfinance', 'crypto', 'synthetic')

    def __init__(self):
        tools = [('run', '전략 검증 실행'), ('cards', '저장된 연구카드 읽기')]
        super().__init__('Strategy Lab', tools, [(s, s) for s in self.SOURCES],
            {'run': [('family', 'Strategy family', [(k, v[0]) for k, v in FAMILIES.items()]),
                     ('symbols', 'Symbols (comma-separated)', 'SPY, QQQ, TLT, GLD'),
                     ('cost', 'Cost per side (bp)', ''), ('days', 'Sessions', 1500)],
             'cards': []})
        self.hide_source()
        run = self.fields['run']
        run['cost'].setPlaceholderText('table rate')
        run['cost'].setToolTip("Blank charges QUANTGEN's table rate. A lower cost runs as a sensitivity with no verdict.")
        run['days'].setToolTip('How many recent trading days to load for each symbol.')
        self.status.setText('Choose a tool and press Run. The app fetches prices from a suitable provider itself; '
                            'the result names it.')
        from .app import label
        from .strategy_view import Fold, ui
        self.run_notes = [label(EXAMPLES, 'caption'), label(LEDGER_NOTE, 'caption'),
                          Fold(ui('Volatility target and crypto trend: up to N× exposure with N assets'),
                               [label(EXPOSURE_HELP, 'caption')])]
        for widget in self.run_notes:
            self.input_box.layout().addWidget(widget)
        self.tool.currentIndexChanged.connect(self._show_run_notes)

    def _show_run_notes(self, index=None):
        for widget in self.run_notes:
            widget.setVisible(self.tool.currentData() == 'run')

    def make_request(self):
        if self.tool.currentData() == 'cards':
            return StrategyRequest(tool='cards')
        v = self.values()
        return StrategyRequest(v['family'], tuple(s.strip().upper() for s in v['symbols'].split(',') if s.strip()),
            self.source.currentData(), number(v['cost'], optional=True), number(v['days'], integer=True))

    # Export sections: the same entries in the same order as before the display rewrite.
    def _record_text(self, text):
        self.sections.append({'type': 'text', 'text': safe_detail(text, limit=None)})

    def _record_table(self, name, headers, rows):
        self.sections.append({'type': 'table', 'name': name, 'headers': headers, 'rows': rows})

    def _record_line(self, name, x, series, x_label, y_label):
        x, series = list(x), [(n, list(v)) for n, v in series]
        self.sections.append({'type': 'line', 'name': name, 'x': x, 'series': series,
                              'x_label': x_label, 'y_label': y_label})
        return x, series

    def _add_view(self, view):
        from .strategy_view import sync_language
        view.setProperty('reading_help_keep_visible', False)
        self.result_layout.addWidget(view)
        sync_language(view)

    def show_result(self, out):
        self.clear_result()
        if out.request.tool == 'cards':
            self._show_cards(out.data['cards'])
        else:
            self._show_run(out.data)

    def _show_cards(self, cards):
        from .strategy_view import CardsView, cards_sections
        from .translations import translate
        self._record_table('Study scorecard', ['Card', 'Kind', 'Decision', 'Reason'],
            [[c['card_id'], c['kind'], c['decision'], c['decision_reason']] for c in cards])
        for c in cards:
            self._record_text(f"{c['card_id']} · {c['decision']}\n{c['hypothesis']}\n{c['decision_reason']}\n"
                              + '\n'.join(c.get('lines', [])) + '\nSources: ' + '; '.join(c.get('citations', [])))
        view = CardsView(cards)
        if view.table is not None:
            self.tables['Study scorecard'] = view.table
        self._add_view(view)
        summary = STORED if cards else 'NOT_LOADED · 저장된 연구카드가 없습니다.'
        self.finished(summary, localized={'ko': summary, 'en': translate(summary, 'en')},
                      sections=cards_sections(cards))

    def _show_run(self, d):
        from .strategy_view import RunView
        sc, wf = d['score'], d['wf']
        safe = payload(d)
        self._record_text(f"{d['label']} · {', '.join(d['symbols'])}\n"
                          f"sources={', '.join(d['sources'])} · {len(d['panel'])} shared sessions · {d['cost_bps']:g} bp/side")
        if 'SYNTHETIC' in d['sources']:
            self._record_text('SYNTHETIC · 아래 점수는 합성 시연입니다. 공식 연구카드 판정이 아닙니다.')
        for line in exposure_lines(d.get('exposure')):
            self._record_text(line)
        self._record_text(f"Decision: {safe['decision']} · {safe['reason']}")
        self._record_text(f"Grid/DSR trials {len(d['grid'])}/{sc.n_trials} · cumulative ledger configurations {d['ledger_n']}\n"
                          f"Walk-forward: {wf.note} · last in-sample winner: {d['chosen']}")
        if d.get('convention'):
            self._record_text(d['convention'])
        self._record_table('Validation statistics', ['Metric', 'Value'], [
            ('OOS Sharpe', fmt(sc.sr_oos)), ('90% interval', str(sc.ci90)), ('Deflated Sharpe', fmt(sc.dsr)),
            ('PBO', fmt(sc.pbo)), ('OOS / IS', fmt(sc.oos_is)), ('2× cost Sharpe', fmt(sc.sr_stress)),
            ('Positive years', fmt(sc.years_positive, 'pct')), ('Plateau', fmt(sc.plateau, 'pct')),
            ('Plateau edge', str(sc.edge)), ('Trades', sc.n_trades), ('Max drawdown', fmt(sc.max_drawdown, 'pct')),
            ('Benchmark Sharpe', fmt(sc.bench_sr)), ('Benchmark difference', fmt(sc.bench_diff)),
            ('Benchmark p', fmt(sc.bench_p)), ('Haircut Sharpe', fmt(sc.haircut_sr))])
        series = [('Strategy', d['equity'])]
        if d['bench_equity'] is not None: series.append(('Benchmark', d['bench_equity']))
        x, series = self._record_line('Walk-forward equity', range(len(d['equity'])), series, 'OOS observations', 'Equity')
        self._record_text(' · '.join(d['notes']))
        view = RunView(d, x, series, colors=getattr(self.window(), 'colors', None))
        self.charts['Walk-forward equity'] = view.chart
        self.tables['Result per criterion'] = view.checklist
        self._add_view(view)
        self.finished(narrative(d), localized=strategy_variants(d),
                      sections={language: narrative_sections(d, language, include_results=False)
                                for language in ('ko', 'en')})
