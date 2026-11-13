"""Export a frozen stock-screen reading. No provider calls; write only after a save choice."""
from __future__ import annotations

from dataclasses import replace
from html import escape
from pathlib import Path

from PyQt6.QtCore import QIODevice, QSaveFile, QUrl
from PyQt6.QtGui import QPageSize, QPdfWriter, QTextDocument, QFont
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from core.market import stock_report as R
from .owner_ui_language.report import TEXT


def text(lang, key, **fields):
    return TEXT[key][1 if lang == 'ko' else 0].format(**fields)


def capture(view, *, include_all=False):
    """Read values, explanations and chart pixels in one GUI turn, before opening a modal dialog."""
    from core.education import indicators as engine
    from core.education.study_guide import availability_text, line_readout
    from .indicator_picker import guide_parts, state_word, state_tone
    from .stock_detail_style import polite
    lang = view.ctx.language
    pane, instrument = view.chart, view.instrument
    snapshot = pane.snapshot
    if instrument is None or snapshot is None or not snapshot.candles:
        raise ValueError('no_chart')
    bars = view.engine_bars()
    rows = []
    keys = tuple(view.studies)
    if include_all:
        keys += tuple(k for k in engine.study_keys() if k not in keys)
    for key in keys:
        spec = engine.study(key)
        why = engine.availability(key, asset=instrument.asset, interval=snapshot.request.interval,
                                  supply=pane.supply, has_volume=any(v == v for v in bars.volume))
        note, reading, code, detail, values = '', '', '', '', ()
        if why:
            note = polite(availability_text(why, lang), lang)
        else:
            reading, code, _, _, paragraphs = guide_parts(key, bars, language=lang,
                                                         interval=snapshot.request.interval, supply=pane.supply)
            detail = ' '.join(paragraphs[:1])
            readout = line_readout(key, bars, -1, language=lang, supply=pane.supply)
            values = tuple((name, view.study_value(key, line, len(bars) - 1, value))
                           for line, (name, value) in zip(spec.lines, readout))
        rows.append(R.indicator_row(key, spec.name(lang), values=values, state=code,
                                   state_word=state_word(key, code, lang) if code else '',
                                   tone=state_tone(code), reading=reading, detail=detail,
                                   on_chart=key in view.studies, note=note))
    view._refresh_side(force=True)
    card, now = view.side.card, view.side.now
    last = snapshot.candles[-1]
    price = R.PriceBox(price=card.price.text(), change=card.change.text(), state=card.state.text(),
                       volume=card.volume.text(), volume_ratio=card.volume_ratio.text(),
                       range_title=card.range_title.text(),
                       range_text=card.range_low.text() + ' – ' + card.range_high.text(),
                       range_from=card.range_from.text(),
                       latest=tuple((R.text(lang, k), view.volume_text(getattr(last, k)) if k == 'volume'
                                     else view.price_text(getattr(last, k)))
                                    for k in ('open', 'high', 'low', 'close', 'volume')),
                       numbers={k: getattr(last, k) for k in ('open', 'high', 'low', 'close', 'volume')})
    start, stop = pane.window()
    shown = snapshot.candles[start:stop]
    qscore, _ = view.qscore_shown()
    from .stock_detail import text as stock_text
    report = R.build_report(language=lang, name=view.name.text(), code=instrument.code,
        asset=instrument.asset, exchange=instrument.exchange, interval=snapshot.request.interval,
        interval_name=view.interval_name(snapshot.request.interval), period=view.period or '',
        period_name=stock_text(lang, 'period_' + view.period) if view.period else '',
        first=R.bar_time(shown[0].timestamp, snapshot.request.interval) if shown else '',
        last=R.bar_time(shown[-1].timestamp, snapshot.request.interval) if shown else '',
        bars_shown=len(shown), count_text=view._unit(snapshot.request.interval, len(shown)), price=price,
        indicators=rows, now_title=now.title.text(), now_caption=now.caption.text(),
        now=[(r.topic.text(), r.sentence.text() + ' ' + r.detail.text()) for r in now.rows if not r.isHidden()],
        qscore=qscore, source=snapshot.source, as_of=last.timestamp, fetched_at=snapshot.fetched_at,
        notes=tuple(v for v in pane.feed_facts().values() if isinstance(v, str)), include_all=include_all)
    return report, pane.chart.grab().toImage()


def _html(report):
    esc = lambda value: escape(str(value or '').replace('−', '-').replace('–', '-'))
    sections = []
    def heading(value):
        sections.append('<h2>' + esc(value) + '</h2>')
    def paragraph(value):
        if value:
            sections.append('<p>' + esc(value).replace('\n', '<br>') + '</p>')
    sections.append('<h1>QUANTGEN</h1>')
    paragraph(report.word('title') + ' · ' + report.name + ' · ' + report.code)
    paragraph(report.market + ' · ' + report.window_text)
    sections.append('<img src="qg:chart" width="675">')
    heading(report.word('section_price'))
    for value in (report.price.price + ' ' + report.price.change, report.price.state,
                  report.price.volume + ' · ' + report.price.volume_ratio, report.price.range_text):
        paragraph(value)
    for title, rows in (('section_indicators', report.on_chart), ('section_more', report.others)):
        if not rows and title == 'section_more':
            continue
        heading(report.word(title))
        if not rows:
            paragraph(report.word('none_on'))
        for row in rows:
            sections.append('<h3>' + esc(row.name + ' · ' + row.value_text()) + '</h3>')
            paragraph(' · '.join(v for v in (row.state_word, row.reading, row.note) if v))
    heading(report.now_title)
    paragraph(report.now_caption)
    for row in report.now:
        paragraph(row.topic + ' · ' + row.text)
    heading('Q-SCORE')
    q = report.qscore
    if q.ready:
        paragraph(f'{q.score:.2f} / 100 · ' + '★' * q.stars)
        paragraph(q.reading)
        for _, name, _, value in q.parts:
            paragraph(f'{name} · {value:.0f}')
        paragraph(q.as_of)
    else:
        paragraph(q.reason)
    paragraph(q.note)
    heading(report.word('section_notes'))
    for label, value in (('source', report.source), ('as_of', report.as_of), ('exported', report.exported_text)):
        paragraph(report.word(label) + ' · ' + value)
    for value in (*report.notes, report.word('network'), report.disclaimer, report.tagline):
        paragraph(value)
    return ('<html><head><style>body{font-family:"QG Interface";font-size:10pt;color:#193d34;}'
            'h1{font-size:24pt;font-weight:600;}h2{font-size:14pt;font-weight:500;margin-top:20px;}'
            'h3{font-size:11pt;font-weight:500;}p{margin:7px 0;line-height:145%;}</style></head><body>'
            + ''.join(sections) + '</body></html>')


def write_report(path, report, chart, extension=None):
    """Atomic replace of the selected file; a failed PDF/PNG never leaves a half-written destination."""
    path = Path(path)
    extension = extension or path.suffix.lstrip('.').lower()
    if extension not in R.EXTENSIONS:
        raise ValueError('format')
    output = QSaveFile(str(path))
    if not output.open(QIODevice.OpenModeFlag.WriteOnly):
        raise OSError('open')
    try:
        if extension == 'pdf':
            from . import use_interface_fonts
            use_interface_fonts()
            writer = QPdfWriter(output)
            writer.setResolution(96)
            writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            writer.setTitle(report.word('title') + ' · ' + report.name)
            writer.setCreator('QUANTGEN')
            document = QTextDocument()
            # Qt PDF ToUnicode loses tnum alternate digit mappings: keep base glyphs in searchable text.
            font = QFont("QG Interface", 10)
            for feature in ("tnum", "liga", "kern"):
                font.setFeature(QFont.Tag.fromString(feature), 0)
            document.setDefaultFont(font)
            document.addResource(QTextDocument.ResourceType.ImageResource, QUrl('qg:chart'), chart)
            document.setHtml(_html(report))
            document.print(writer)
            del writer
        elif extension == 'png':
            if not chart.save(output, 'PNG'):
                raise OSError('image')
        else:
            content = R.report_json(report) if extension == 'json' else R.indicator_csv(report)
            if output.write(content) != len(content):
                raise OSError('write')
        if not output.commit():
            raise OSError('commit')
    except BaseException:
        output.cancelWriting()
        raise


def export_dialog(view):
    lang = view.ctx.language
    try:
        report, chart = capture(view, include_all=True)
    except ValueError:
        QMessageBox.information(view, text(lang, 'export'), text(lang, 'no_chart'))
        return False
    choices = [(text(lang, key), extension, all_studies) for key, extension, all_studies in (
        ('filter_pdf', 'pdf', False), ('filter_pdf_all', 'pdf', True), ('filter_png', 'png', False),
        ('filter_json', 'json', False), ('filter_csv', 'csv', False))]
    path, selected = QFileDialog.getSaveFileName(view, text(lang, 'dialog_title'),
        R.file_name(report.code, 'pdf', report.exported_at), ';;'.join(c[0] for c in choices))
    if not path:
        return False
    _, extension, include_all = next((c for c in choices if c[0] == selected), choices[0])
    path = Path(path)
    if not path.suffix:
        path = path.with_suffix('.' + extension)
        if path.exists() and QMessageBox.question(view, text(lang, 'export'),
                ('이미 있는 파일을 덮어쓸까요?' if lang == 'ko' else 'Replace the existing file?')) != QMessageBox.StandardButton.Yes:
            return False
    if not include_all:
        report = replace(report, indicators=report.on_chart, include_all=False)
    try:
        write_report(path, report, chart, extension)
    except (OSError, ValueError) as exc:
        QMessageBox.warning(view, text(lang, 'failed_title'), text(lang, 'failed', reason=type(exc).__name__))
        return False
    QMessageBox.information(view, text(lang, 'export'), text(lang, 'saved', file=path.name))
    return True
