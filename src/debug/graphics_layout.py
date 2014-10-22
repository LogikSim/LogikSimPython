#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Copyright 2014 The LogikSim Authors. All rights reserved.
Use of this source code is governed by the GNU GPL license that can 
be found in the LICENSE.txt file.
"""

import sys

from PySide import QtGui, QtCore


#class TestRect(QtGui.QGraphicsItem, QtGui.QGraphicsLayoutItem):
#    def __init__(self, *args, **kargs):
#        QtGui.QGraphicsLayoutItem.__init__(self, *args, **kargs)
#        QtGui.QGraphicsItem.__init__(self, *args, **kargs)
#        #super(TestRect, self).__init__(*args, **kargs)
#        
#        self._pen = QtGui.QPen(QtCore.Qt.black)
#        self._pen.setWidthF(1)
#        self._size = QtCore.QSizeF(200, 100)
#    
#    def boundingRect(self):
#        width = self._pen.width()
#        return QtCore.QRectF(QtCore.QPointF(width/2, width/2), self._size + 
#                QtCore.QSizeF(width, width))
#    
#    def paint(self, painter, option, widget):
#        painter.setPen(self._pen)
#        painter.drawRoundedRect(QtCore.QRectF(QtCore.QPointF(0, 0), 
#                self._size), 10, 10)
#    
#    def setGeometry(self, rect):
#        self.setPos(rect.topLeft())
#        self._size = rect.size()
#    
#    def sizeHint(self, *args):
#        return self._size




class TestRect(QtGui.QGraphicsRectItem, QtGui.QGraphicsLayoutItem):
    def __init__(self, *args, **kargs):
        QtGui.QGraphicsRectItem.__init__(self, *args, **kargs)
        QtGui.QGraphicsLayoutItem.__init__(self, *args, **kargs)
        self.setRect(0, 0, 200, 100)
    
    def setGeometry(self, rect):
        self.setRect(rect)
    
    def sizeHint(self, *args):
        return self.rect().size()


def add_rect_with_layout(scene):
    item1 = TestRect()
    print(item1)
    item2 = TestRect()
    scene.addItem(item1)
    scene.addItem(item2)
    
    layout = QtGui.QGraphicsGridLayout()
    layout.addItem(item1, 0, 0)
    layout.addItem(item2, 0, 1)
    
    form = QtGui.QGraphicsWidget()
    form.setLayout(layout)
    scene.addItem(form)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    scene = QtGui.QGraphicsScene()
    
    add_rect_with_layout(scene)
    
    view = QtGui.QGraphicsView()
    view.setScene(scene)
    view.show()
    app.exec_()
