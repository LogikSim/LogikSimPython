#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright 2014 The LogikSim Authors. All rights reserved.
Use of this source code is governed by the GNU GPL license that can
be found in the LICENSE.txt file.

Nonimplemented virtual methods can lead to event handling Problems.

Run the script as it is and you will observe the following issues:

- Frame cannot be closed kindly only by killing the process

- Resizing the Program leads to strange error messages:
     QPainter::begin: Paint device returned engine == 0, type: 0


Proposed changes:

    - Detect unresolvable virtual methods and print appropriate error message


Workaround for this example:

Uncomment:

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

        # def sizeHint(self, *args):
        # return self.rect().size()


def add_rect_with_layout(scene):
    item1 = TestRect()
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
