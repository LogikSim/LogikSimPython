#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright 2014 The LogikSim Authors. All rights reserved.
Use of this source code is governed by the GNU GPL license that can 
be found in the LICENSE.txt file.

Invalid return value in TestRect.sizeHint leads to event handling Problems.

Run the script as it is and you will observe the following issues:

- Frame cannot be closed kindly only by killing the process

- Resizing the Program leads to strange error messages:
     QPainter::begin: Paint device returned engine == 0, type: 0

  Since the problem is related to sizeHint this is a secondary error to the 
  initial problem.


How to fix this example:

Change:
    
    def sizeHint(self, *args):
        return self.rect()

To:

    def sizeHint(self, *args):
        return self.rect().size()

"""

import sys

from PySide import QtGui


class TestRect(QtGui.QGraphicsRectItem, QtGui.QGraphicsLayoutItem):
    def __init__(self, *args, **kargs):
        QtGui.QGraphicsRectItem.__init__(self, *args, **kargs)
        QtGui.QGraphicsLayoutItem.__init__(self, *args, **kargs)
        self.setRect(0, 0, 200, 100)
    
    def setGeometry(self, rect):
        self.setRect(rect)
    
    def sizeHint(self, *args):
        return self.rect()#.size()


def add_rect_with_layout(scene):
    item = TestRect()
    scene.addItem(item)
    
    layout = QtGui.QGraphicsGridLayout()
    layout.addItem(item, 0, 0)
    
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
