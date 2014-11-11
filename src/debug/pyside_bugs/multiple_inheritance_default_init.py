#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright 2014 The LogikSim Authors. All rights reserved.
Use of this source code is governed by the GNU GPL license that can
be found in the LICENSE.txt file.

Default constructor in the case of multiple inheritance not supported:

Run the script as it is and you will observe the following issues:

 - item1 and item2 are not recognized as valid QGraphicsLayoutItems
   while trying to add them to a layout. The following error is printed:

        QGraphicsGridLayout::addItem: cannot add null item
        QGraphicsGridLayout::addItem: cannot add null item

 -> The two rects are drawn on top of each other instead of being side
    by side due to broken layout

Workaround for this example:

Uncomment the constructor of TestRect:

    def __init__(self, *args, **kargs):
        QtGui.QGraphicsRectItem.__init__(self, *args, **kargs)
        QtGui.QGraphicsLayoutItem.__init__(self, *args, **kargs)

"""

import sys

from PySide import QtGui


class TestRect(QtGui.QGraphicsRectItem, QtGui.QGraphicsLayoutItem):
    # def __init__(self, *args, **kargs):
    # QtGui.QGraphicsRectItem.__init__(self, *args, **kargs)
    #    QtGui.QGraphicsLayoutItem.__init__(self, *args, **kargs)

    def setGeometry(self, rect):
        self.setRect(rect)

    def sizeHint(self, *args):
        return self.rect().size()


def add_rect_with_layout(scene):
    item1 = TestRect()
    item1.setRect(0, 0, 200, 100)
    item2 = TestRect()
    item2.setRect(0, 0, 200, 100)
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
