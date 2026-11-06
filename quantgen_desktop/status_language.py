"""Explicit, display-only status captions; source codes remain available."""
from PyQt6.QtCore import Qt

STATUS_ROLE = Qt.ItemDataRole.UserRole + 803

_LABELS = {
    'execution': {'RUNNING': '실행 중', 'COMPLETED': '완료', 'FAILED': '실패'},
    'official': {'NOT_RUN': '미실행', 'PARTIAL': '부분', 'PASS': '통과',
                 'FAIL': '실패', 'BLOCKED': '차단', 'SYNTHETIC': '합성 데이터',
                 'NOT_APPLIED': '미적용', 'NOT_VERIFIED': '미검증'},
    'connection': {'CONFIGURED': '설정 있음', 'NOT_CONFIGURED': '설정 없음',
                   'REACHABLE': '응답 확인', 'UNAVAILABLE': '이용 불가'},
}


def status_text(widget, value, context):
    raw = str(value)
    if getattr(widget.window(), 'ui_language', 'en') != 'ko':
        return raw
    caption = _LABELS.get(context, {}).get(raw)
    if not caption:
        return raw
    return f'{caption}({raw})' if context == 'official' else caption


def mark_status_column(table, column, context):
    """Tag only authored status cells, never arbitrary provider/user strings."""
    contexts = dict(getattr(table, '_qg_status_columns', {}))
    contexts[column] = context
    table._qg_status_columns = contexts
    for row in range(table.rowCount()):
        item = table.item(row, column)
        if item is None:
            continue
        raw = item.data(STATUS_ROLE)
        if raw is None:
            raw = item.text()
            item.setData(STATUS_ROLE, raw)
        item.setToolTip(str(raw))
        item.setText(status_text(table, raw, context))
