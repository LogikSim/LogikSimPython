#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Copyright 2014 The LogikSim Authors. All rights reserved.
Use of this source code is governed by the GNU GPL license that can
be found in the LICENSE.txt file.

http://blog.rburchell.com/2010/02/pyside-tutorial-custom-widget-painting.html
'''

import sys

from PySide import QtCore, QtGui


class CustomWidget(QtGui.QWidget):
    def __init__(self, parent, anumber):
        QtGui.QWidget.__init__(self, parent)
        self._number = anumber

    def paintEvent(self, ev):
        p = QtGui.QPainter(self)
        p.fillRect(self.rect(), QtGui.QBrush(QtCore.Qt.red, 
                                             QtCore.Qt.Dense2Pattern))
        p.drawText(self.rect(), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                   str(self._number))
        p.setPen(QtGui.QColor(220, 220, 220))
        p.drawText(self.rect(), QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter,
                   str(self._number * 2))


class MyMainWindow(QtGui.QMainWindow):
    def __init__(self, parent):
        QtGui.QMainWindow.__init__(self, parent)
        # Add content
        central = CustomWidget(self, 666)
        self.setCentralWidget(central)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    sw = MyMainWindow(None)
    sw.show()
    app.exec_()
    sys.exit()
