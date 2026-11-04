"""Installed native navigation, synthetic calculation and export, outside checkout.

Uses only a temporary preference/export directory and injected synthetic history.
Never starts a provider, paper engine, research pilot or official ledger.
"""
from datetime import date, timedelta
import json
import math
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import Mock, patch
from zipfile import ZipFile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def guard(event,args):
    if event == 'socket.connect': raise AssertionError('Desktop smoke is offline')
    if event == 'open' and isinstance(args[0],(str,bytes,os.PathLike)):
        parts=Path(os.fsdecode(args[0])).parts
        if any(p.startswith('.env') or p in ('holdout','frozen','paper_live','grokteam','.nextgen','_backup') for p in parts):
            raise AssertionError('Protected path refused')
        if ('asset_expansion' in parts and 'cache' in parts) or str(args[0]).endswith('.jsonl'):
            raise AssertionError('Protected cache/ledger refused')


sys.addaudithook(guard)
import dotenv
with patch.object(dotenv,'load_dotenv',return_value=False):
    import quantgen_desktop.app as desktop
    from core.quant.history import History
    from core.research.analysis import execute_analysis
    from core.research.runs import read_export
    from quantgen_desktop.market_chart import MarketChartPane
from PyQt6.QtCore import QSettings
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QMessageBox
if 'site-packages' not in Path(desktop.__file__).parts:
    raise AssertionError('Imported checkout instead of installed wheel')
app=QApplication([])
assert desktop.load_interface_fonts(app)=='QG Interface'
history=History('FIXTURE','SYNTHETIC',
    tuple((date(2026,1,1)+timedelta(days=i)).isoformat() for i in range(120)),
    tuple(100+.08*i+math.sin(i*.7) for i in range(120)),note='Installed runtime fixture')


def fixture_runner(request, run):
    return execute_analysis(request,run,history_loader=lambda *a,**kw:history,
        rate_reader=lambda symbol:(.03,'assumed fixture rate'))


chart_service=Mock()
chart_service.load.side_effect=AssertionError('Installed navigation must not query KIS')
with tempfile.TemporaryDirectory(prefix='quantgen-installed-smoke-') as folder, \
     patch('data.kis_workspace.MarketDataService',return_value=chart_service) as chart_factory, \
     patch('data.kis_stream.KISStream',side_effect=AssertionError('No KIS stream')) as chart_stream, \
     patch('config.kis_credentials',side_effect=AssertionError('No real KIS credentials')):
    root=Path(folder)
    settings=QSettings(str(root/'preferences.ini'),QSettings.Format.IniFormat)
    # A malformed stored value must leave the UI usable for preference repair.
    settings.setValue('ui/locale',42)
    window=desktop.ResearchWindow(auto_refresh=False,analysis_runner=fixture_runner,
        locale=settings.value('ui/locale'),language_store=settings)
    try:
        window.show();app.processEvents()
        assert window.stack.count()==8  # Seven research workspaces (Analysis tools since 2026-11-04) plus the guide.
        assert 'guide' in window.nav
        assert window.home_markets.rowCount()==12
        assert window.home_markets.horizontalHeaderItem(window.home_markets.columnCount()-1).text()=='Q-SCORE'
        assert not window.windowIcon().isNull()
        assert not window.grab().isNull()
        assert window.locale_picker.currentData()=='en_US'
        for route in window.route_indices:
            window.navigate(route)
            assert window.nav[route].isChecked()
        assert isinstance(window.market_chart,MarketChartPane)
        window.navigate('markets');window.show_market_pane(window.market_chart)
        assert window.current_market_pane() is window.market_chart,'Installed chart must be reachable from Markets'
        assert window.tool_host.count()==10 and window.market_chart.asset.currentData()=='domestic_stock'
        assert window.markets_view.showing_stock() and len(window.markets_view.grid.cards)==6
        app.processEvents()
        assert window.market_chart.snapshot is None
        assert not window.market_chart.jobs.busy
        assert not window.market_chart.poll_button.isChecked()
        assert not window.market_chart.poll_timer.isActive()
        assert window.market_chart._stream is None
        assert window.market_chart.request().instrument.code=='005930'
        # Chart, Home feed and the two independent Q-SCORE controllers each
        # construct a service. Construction must still perform no live work.
        assert chart_factory.call_count==4
        assert all(not call.args and not call.kwargs for call in chart_factory.call_args_list)
        assert not window.home_feed.active and not window.home_feed.busy
        assert window.home_feed._stream is None
        assert not window.home_feed.age_timer.isActive()
        for scores in (window.q_scores,window.chart_scores):
            assert not scores.jobs.busy and not scores.timer.isActive()
            assert scores.scores()=={}
        chart_service.load.assert_not_called();chart_stream.assert_not_called()
        window.symbol.setText('FIXTURE')
        window.source.setCurrentIndex(window.source.findData('synthetic'))
        window.model.setCurrentIndex(window.model.findData('gbm'))
        window.drift.setCurrentIndex(window.drift.findData('zero'))
        window.paths.setValue(200);window.horizon.setValue(5)
        window.run_button.click()
        for _ in range(1500):
            app.processEvents()
            if not window.jobs.busy:break
            QTest.qWait(10)
        assert not window.jobs.busy,'Synthetic worker did not finish within 15 seconds'
        run=window.session.runs()[0]
        assert run['execution_status']=='COMPLETED'
        assert run['verdict']=='NOT_RUN' and run['data']['synthetic']
        window.set_language('ko');window.theme.setCurrentIndex(1)
        window.navigate('library');window.run_table.selectRow(0)
        assert window.session.runs()[0]==run
        for bundle in (False,True):
            destination=root/('fixture.zip' if bundle else 'fixture.json')
            with patch.object(desktop.QFileDialog,'getSaveFileName',return_value=(str(destination),'')):
                window.export_selected(bundle)
            if bundle:
                with ZipFile(destination) as archive:
                    assert archive.testzip() is None
                    assert read_export(archive.read('research-run.json'))==run
            else:assert read_export(destination.read_bytes())==run
        settings.sync()
        assert QSettings(str(root/'preferences.ini'),QSettings.Format.IniFormat).value('ui/locale')=='ko_KR'
        assert window.market_chart.ctx.language=='ko'
        assert window.market_chart.snapshot is None
        assert not window.home_feed.active and not window.home_feed.busy
        for scores in (window.q_scores,window.chart_scores):
            assert not scores.jobs.busy and not scores.timer.isActive()
        chart_service.load.assert_not_called();chart_stream.assert_not_called()
        assert window.paper_session.runtime is None
    finally:
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Yes):
            window.close()
        window.deleteLater();app.processEvents()
print(json.dumps({'status':'PASS','platform':sys.platform,
    'scope':'installed native shell, six workspaces plus independent guide, 12-row Q-SCORE watchlist, reachable idle KIS chart, synthetic worker, locale/theme, preference repair and JSON/ZIP exports',
    'live_providers':'NOT_RUN','paper_engine':'NOT_RUN','research_pilot':'NOT_RUN','official_ledger':'NOT_RUN'}))
