"""Searchable rights inventory. Selecting rows never requests market data."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget,QVBoxLayout,QLineEdit,QTreeWidget,QTreeWidgetItem,QHeaderView
from core.i18n import LocaleContext
from core.research.display_rights import display_rights,policy_detail


class DataRightsPane(QWidget):
    def __init__(self,ctx=None):
        super().__init__()
        from .app import label
        self.ctx=ctx or LocaleContext();self.record=display_rights()
        layout=QVBoxLayout(self)
        self.intro=label('');layout.addWidget(self.intro)
        self.search=QLineEdit();self.search.textChanged.connect(self.filter);layout.addWidget(self.search)
        self.tree=QTreeWidget();self.tree.setColumnCount(4);self.tree.setMinimumHeight(300)
        self.tree.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.tree.setStyleSheet('QTreeWidget::item { padding: 4px 8px; }')
        for column in range(3):self.tree.header().setSectionResizeMode(column,QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(3,QHeaderView.ResizeMode.Stretch)
        self.tree.header().setMinimumSectionSize(130)
        self.tree.setRootIsDecorated(True);self.tree.itemSelectionChanged.connect(self.choose);layout.addWidget(self.tree)
        self.detail=label('');layout.addWidget(self.detail)
        self.legal=label('','caption');layout.addWidget(self.legal)
        self.set_locale(self.ctx)

    def set_locale(self,ctx):
        self.ctx=ctx
        self.intro.setText(ctx.t('rights_intro')+'\n'+ctx.t('rights_scope'))
        self.search.setPlaceholderText(ctx.t('rights_search'))
        self.tree.setHeaderLabels([ctx.t('symbol'),ctx.t('provider'),ctx.t('frequency'),ctx.t('status')])
        self.tree.clear()
        for key,label in (('home',ctx.t('rights_home')),('registered_series',ctx.t('rights_registry'))):
            group=QTreeWidgetItem([label]);self.tree.addTopLevelItem(group)
            for row in self.record[key]:
                item=QTreeWidgetItem([row['series_id'],row['source'],ctx.t('daily') if row['frequency']=='daily' else ctx.text(row['frequency']),ctx.t(row['outcome'])])
                for column in range(4):item.setToolTip(column,item.text(column))
                item.setData(0,Qt.ItemDataRole.UserRole,row);group.addChild(item)
            group.setExpanded(key=='home')
        for column in range(4):self.tree.resizeColumnToContents(column)
        self.legal.setText(self.record['legal_review']['scope_'+ctx.language]+'\n'+'\n'.join(self.record['legal_review']['sources']))
        self.detail.setText('');self.filter()

    def filter(self,*args):
        needle=self.search.text().casefold().strip()
        for g in range(self.tree.topLevelItemCount()):
            group=self.tree.topLevelItem(g);visible=False
            for index in range(group.childCount()):
                item=group.child(index);matches=needle in ' '.join(item.text(c) for c in range(4)).casefold()
                item.setHidden(not matches);visible=visible or matches
            group.setHidden(not visible)
            if needle and visible:group.setExpanded(True)

    def choose(self):
        items=self.tree.selectedItems()
        row=items[0].data(0,Qt.ItemDataRole.UserRole) if items else None
        if not row:return
        lines=[row['series_id']+' · '+self.ctx.t(row['outcome'])]
        lines += [title+'\n'+value for title,value in policy_detail(self.record,row,self.ctx)]
        self.detail.setText('\n\n'.join(lines))
