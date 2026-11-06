"""Natural-width categories that wrap without hiding destinations."""
from PyQt6.QtCore import QRect,QSize,Qt
from PyQt6.QtWidgets import QLayout
class CategoryFlow(QLayout):
    def __init__(self,parent=None):
        super().__init__(parent);self.items=[];self.setContentsMargins(0,0,0,0);self.setSpacing(6)
    def addItem(self,item):self.items.append(item)
    def count(self):return len(self.items)
    def itemAt(self,index):return self.items[index] if 0<=index<len(self.items) else None
    def takeAt(self,index):return self.items.pop(index) if 0<=index<len(self.items) else None
    def expandingDirections(self):return Qt.Orientation(0)
    def hasHeightForWidth(self):return True
    def heightForWidth(self,width):return self._arrange(QRect(0,0,width,0),True)
    def minimumSize(self):
        size=QSize()
        for item in self.items:size=size.expandedTo(item.minimumSize())
        return size
    def sizeHint(self):return QSize(sum(i.sizeHint().width() for i in self.items)+max(0,len(self.items)-1)*self.spacing(),max((i.sizeHint().height() for i in self.items),default=0))
    def setGeometry(self,rect):super().setGeometry(rect);self._arrange(rect,False)
    def _arrange(self,rect,measure):
        x,y,height=rect.x(),rect.y(),0
        for item in self.items:
            size=item.sizeHint()
            if x>rect.x() and x+size.width()>rect.x()+rect.width():x,y,height=rect.x(),y+height+self.spacing(),0
            if not measure:item.setGeometry(QRect(x,y,size.width(),size.height()))
            x+=size.width()+self.spacing();height=max(height,size.height())
        return y+height-rect.y()
