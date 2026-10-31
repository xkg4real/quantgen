"""Translate presentation text in place without rebuilding views or input values."""
from PyQt6.QtCore import QLocale, Qt, QSignalBlocker
from PyQt6.QtWidgets import (QLabel,QPushButton,QComboBox,QLineEdit,QTabWidget,
                             QTableWidget,QTreeWidget,QWidget)
from core.i18n import numeric_presentation


class LocalizedLabel(QLabel):
    def setText(self,text):
        ctx=getattr(self.window(),'ctx',None)
        translated=ctx.text(text) if ctx else str(text)
        self._qg_translations={'text':(str(text),translated)}
        super().setText(translated)


class LocalizedButton(QPushButton):
    def setText(self,text):
        ctx=getattr(self.window(),'ctx',None)
        translated=ctx.text(text) if ctx else str(text)
        self._qg_translations={'text':(str(text),translated)}
        super().setText(translated)


class LanguageBinder:
    def __init__(self,window):
        self.window=window

    def value(self,widget,key,value,ctx,*,numeric=False):
        fields=getattr(widget,'_qg_translations',{})
        source,last=fields.get(key,(value,None))
        if value!=last:source=value
        translated=ctx.text(source)
        if numeric:translated=numeric_presentation(translated,ctx)
        fields[key]=(source,translated)
        widget._qg_translations=fields
        return translated

    def apply(self,ctx):
        window=self.window
        window.setLocale(QLocale(str(ctx.locale)))
        window.setLayoutDirection(Qt.LayoutDirection.RightToLeft if ctx.rtl else Qt.LayoutDirection.LeftToRight)
        for widget in window.findChildren(QLabel)+window.findChildren(QPushButton):
            widget.setText(self.value(widget,'text',widget.text(),ctx))
        for widget in window.findChildren(QLineEdit):
            widget.setPlaceholderText(self.value(widget,'placeholder',widget.placeholderText(),ctx))
        for widget in window.findChildren(QWidget):
            for key,getter,setter in (('tooltip',widget.toolTip,widget.setToolTip),
                    ('accessibleName',widget.accessibleName,widget.setAccessibleName),
                    ('accessibleDescription',widget.accessibleDescription,widget.setAccessibleDescription)):
                value=getter()
                if value:setter(self.value(widget,key,value,ctx))
        for widget in window.findChildren(QComboBox):
            if widget.property('localePicker'):continue
            blocker=QSignalBlocker(widget)
            for index in range(widget.count()):
                widget.setItemText(index,self.value(widget,('item',index),widget.itemText(index),ctx))
            del blocker
        for widget in window.findChildren(QTabWidget):
            for index in range(widget.count()):
                widget.setTabText(index,self.value(widget,('tab',index),widget.tabText(index),ctx))
        for table in window.findChildren(QTableWidget):
            blocker=QSignalBlocker(table)
            for column in range(table.columnCount()):
                item=table.horizontalHeaderItem(column)
                if item:item.setText(self.value(table,('header',column),item.text(),ctx))
            for row in range(table.rowCount()):
                for column in range(table.columnCount()):
                    item=table.item(row,column)
                    header=table.horizontalHeaderItem(column)
                    identity=header and header.text() in {'Symbol','Code','ID','Name','Venue','종목·통화쌍','이름','종목','시장 코드'}
                    if item:item.setText(self.value(item,'text',item.text(),ctx,numeric=not identity))
            del blocker
        for tree in window.findChildren(QTreeWidget):
            item=tree.headerItem()
            for column in range(tree.columnCount()):
                item.setText(column,self.value(tree,('header',column),item.text(column),ctx))


def locale_picker(ctx,parent=None):
    from core.i18n import locale_choices
    picker=QComboBox(parent)
    picker.setProperty('localePicker',True)
    picker.setEditable(True);picker.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
    picker.setMaxVisibleItems(14);picker.setMinimumWidth(180);picker.setMaximumWidth(480)
    picker.completer().setFilterMode(Qt.MatchFlag.MatchContains)
    picker.completer().setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    choices=list(locale_choices())
    priority=[('ko_KR','한국어 · 대한민국'),('en_US','English · United States')]
    for key,label in priority+[(k,n) for k,n in choices if k not in {'ko_KR','en_US'}]:picker.addItem(label,key)
    index=picker.findData(str(ctx.locale));picker.setCurrentIndex(max(0,index))
    return picker
