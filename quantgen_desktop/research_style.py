"""Research workspaces share the stock detail's quiet surfaces and controls."""
from .stock_detail_style import sheet as detail_sheet, line_color


def sheet(p,dark):
    line=line_color(p)
    return detail_sheet(p,dark)+f'''
      QWidget {{ font-family: "QG Interface"; }}
      QLabel[role='title'] {{ font-size: 23px; font-weight: 600; letter-spacing: -0.9px; }}
      QFrame#panel {{ border: 1px solid {line}; border-radius: 12px; background: {p.surface}; }}
      QLabel[role='heading'] {{ border: 0; padding: 0; font-size: 16px; font-weight: 500;
                              letter-spacing: -0.36px; color: {p.text}; }}
      QFrame#workspaceGuide {{ background: transparent; border: 0; border-bottom: 1px solid {line}; border-radius: 0; }}
      QLabel[role='workflowTitle'] {{ font-size: 16px; font-weight: 500; color: {p.text}; }}
      QFrame#workspaceGuide QLabel[role='workflowNumber'] {{ background: {p.surface_2}; color: {p.muted}; border-radius: 10px; }}
      QFrame#workspaceGuide QLabel[role='caption'] {{ color: {p.muted}; }}
      QPushButton[tool='true'] {{ padding: 5px 10px; border: 0; border-radius: 8px;
                                font-size: 13px; background: transparent; color: {p.muted}; }}
      QPushButton[tool='true']:checked {{ background: {p.accent_soft}; color: {p.accent}; font-weight: 600; }}
      QPushButton[studyChoice='true'] {{ padding: 5px 11px; min-height: 20px; border-radius: 8px;
                                       font-size: 13px; font-weight: 400; }}
      QPushButton[studyChoice='true']:checked {{ background: {p.accent_soft}; color: {p.accent}; font-weight: 600; }}
      QPushButton[chip='true'] {{ padding: 4px 9px; border: 0; border-radius: 7px;
                                font-size: 12px; background: {p.surface_2}; color: {p.text}; }}
      QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{ border-color: {line}; border-radius: 8px; }}
      QTabWidget::pane {{ border: 0; background: transparent; }}
      QTabBar::tab {{ background: transparent; border: 0; border-radius: 8px;
                       color: {p.muted}; padding: 7px 14px; margin: 0 5px 8px 0; }}
      QTabBar::tab:selected {{ background: {p.accent_soft}; color: {p.accent}; font-weight: 600; }}
      QTabBar::tab:hover {{ background: {p.surface_2}; color: {p.text}; }}
    '''


def apply(widget,colors,dark):
    widget.setStyleSheet(sheet(colors,dark))


def prepare_page(layout):
    """Bound prose and forms together; long results still scroll vertically."""
    page = layout.parentWidget()
    page.setObjectName('researchWorkspace')
    page.setMaximumWidth(1200)
    layout.setContentsMargins(24, 22, 24, 28)
    layout.setSpacing(16)
    return page
