"""Korean display text for the owner UI port, area: report (the stock screen's export, owner UI-D14, 2026-11-12).

Owner, verbatim: "그리고 기술지표들 우리 사이트 내에서 판단한걸 묶어서 pdf나 이런걸로 내보내기 하는 기능도 되면 좋겠다
상세차트에서". R-D14-1: an "내보내기" action on the stock screen saves one report of what the engine judged; PDF first,
also a PNG of the chart and JSON/CSV of the same readings, through a save dialog with a sensible default name.

`PAIRS` joins the window catalogue and is empty: the stock screen renders its texts itself (`qg_literal` widgets).
`TEXT` is read only by quantgen_desktop.stock_report: key -> (English, Korean); templates use {name} fields in both
languages. The report's own words (headings, Q-SCORE reasons, disclaimer) live in core.market.stock_report.TEXT so the
JSON/CSV/PDF can be built and tested without Qt. Wording: 해요체, no '봉', no buy/sell advice.
"""

PAIRS = {}

TEXT = {
    # Toolbar action and the ⋯ menu entry
    'export': ('Export', '내보내기'),
    'export_tip': ("Save this chart's readings as a PDF report, a chart picture (PNG) or data (JSON, CSV)",
                   '이 차트의 판단을 PDF 리포트, 차트 그림(PNG), 자료(JSON·CSV)로 저장해요'),
    # Save dialog
    'dialog_title': ('Export the report', '리포트 내보내기'),
    'filter_pdf': ('PDF report (*.pdf)', 'PDF 리포트 (*.pdf)'),
    'filter_pdf_all': ('PDF report with every available indicator (*.pdf)', 'PDF 리포트 · 볼 수 있는 지표 모두 (*.pdf)'),
    'filter_png': ('Chart picture (*.png)', '차트 그림 (*.png)'),
    'filter_json': ('Readings as data, JSON (*.json)', '판단 자료 JSON (*.json)'),
    'filter_csv': ('Indicator table, CSV (*.csv)', '지표 표 CSV (*.csv)'),
    # Results
    'saved': ('Saved · {file}', '저장했어요 · {file}'),
    'failed_title': ('Export', '내보내기'),
    'failed': ('Could not save the file ({reason}). Check the folder and the file name, then try again.',
               '파일을 저장하지 못했어요 ({reason}). 폴더와 파일 이름을 확인한 뒤 다시 해 보세요.'),
    'failed_protected': ('This folder is kept for app data. Choose another folder.',
                         '앱 자료를 두는 폴더예요. 다른 폴더를 골라 주세요.'),
    'no_chart': ('Open a chart first, then export it.', '차트가 열린 뒤에 내보낼 수 있어요.'),
    # Price box labels the card does not print itself
    'range_low': ('Low', '최저'),
    'range_high': ('High', '최고'),
}
