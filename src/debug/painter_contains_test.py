#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Copyright 2014 The LogikSim Authors. All rights reserved.
Use of this source code is governed by the GNU GPL license that can
be found in the LICENSE.txt file.
'''


import sys
import collections

from PySide import QtCore, QtGui


class CustomWidget(QtGui.QWidget):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)

        self.paths = collections.OrderedDict()

        #
        # WindingFill
        sp_win = QtGui.QPainterPath()
        sp_win.setFillRule(QtCore.Qt.WindingFill)
        sp_win.addRect(QtCore.QRectF(75, 75, 450, 50))
        sp_win.addRect(QtCore.QRectF(475, 75, 50, 250))
        sp_win.addRect(QtCore.QRectF(475, 275, 150, 50))
        sp_win.addRect(QtCore.QRectF(575, 75, 50, 250))
        sp_win.addRect(QtCore.QRectF(575, 75, 450, 50))
        sp_win.addRect(QtCore.QRectF(975, 75, 550, 50))
        self.paths['WindingFill'] = sp_win

        #
        # OddEvenFill
        sp_odd = QtGui.QPainterPath()
        sp_odd.setFillRule(QtCore.Qt.OddEvenFill)
        # lines
        sp_odd.addRect(QtCore.QRectF(125, 75, 350, 50))
        sp_odd.addRect(QtCore.QRectF(475, 125, 50, 150))
        sp_odd.addRect(QtCore.QRectF(525, 275, 50, 50))
        sp_odd.addRect(QtCore.QRectF(575, 125, 50, 150))
        sp_odd.addRect(QtCore.QRectF(625, 75, 350, 50))
        sp_odd.addRect(QtCore.QRectF(1025, 75, 450, 50))
        # corners
        sp_odd.addRect(QtCore.QRectF(75, 75, 50, 50))
        sp_odd.addRect(QtCore.QRectF(475, 75, 50, 50))
        sp_odd.addRect(QtCore.QRectF(475, 275, 50, 50))
        sp_odd.addRect(QtCore.QRectF(575, 275, 50, 50))
        sp_odd.addRect(QtCore.QRectF(575, 75, 50, 50))
        sp_odd.addRect(QtCore.QRectF(975, 75, 50, 50))
        self.paths['OddEvenFill'] = sp_odd

        #
        # UnitedPolygons
        sp_united = QtGui.QPainterPath()
        poly = QtGui.QPolygonF()
        # lines
        poly = poly.united(QtGui.QPolygonF(QtCore.QRectF(75, 75, 450, 50)))
        poly = poly.united(QtGui.QPolygonF(QtCore.QRectF(475, 275, 150, 50)))
        poly = poly.united(QtGui.QPolygonF(QtCore.QRectF(575, 75, 50, 250)))
        poly = poly.united(QtGui.QPolygonF(QtCore.QRectF(575, 75, 450, 50)))
        poly = poly.united(QtGui.QPolygonF(QtCore.QRectF(975, 75, 550, 50)))
        poly = poly.united(QtGui.QPolygonF(QtCore.QRectF(475, 75, 50, 250)))
        sp_united.addPolygon(poly)
        self.paths['UnitedPolygons'] = sp_united


        self._rect_gap = QtCore.QRectF(300, 90, 400, 20)
        self._rect_in = QtCore.QRectF(800, 90, 500, 20)


        for name, path in self.paths.items():
            print(name)
            print("Path contains first rect:", path.contains(self._rect_gap),
                  "(expected False)")
            print("Path contains second rect:", path.contains(self._rect_in),
                       "(expected True)")
            print()


    def paintEvent(self, ev):
        p = QtGui.QPainter(self)

        i = 0
        gap = 300
        for name, path in self.paths.items():
            font = p.font()
            font.setBold(False); p.setFont(font)
            p.drawText(50, 50 + i * gap, name)
            font.setBold(path.contains(self._rect_gap)); p.setFont(font)
            p.drawText(50, 150 + i * gap, "Path contains first rect: " +
                       str(path.contains(self._rect_gap)) +
                       " (expected False)")
            font.setBold(not path.contains(self._rect_in)); p.setFont(font)
            p.drawText(50, 175 + i * gap, "Path contains second rect: " +
                       str(path.contains(self._rect_in)) +
                       " (expected True)")

            p.fillRect(self._rect_gap.translated(QtCore.QPointF(0, i * gap)),
                       QtGui.QBrush(QtGui.QColor(0, 0, 255, 255)))
            p.fillRect(self._rect_in.translated(QtCore.QPointF(0, i * gap)),
                       QtGui.QBrush(QtGui.QColor(0, 0, 255, 255)))
            p.fillPath(path.translated(QtCore.QPointF(0, i * gap)),
                       QtGui.QBrush(QtGui.QColor(255, 0, 0, 128)))
            i += 1



class MyMainWindow(QtGui.QMainWindow):
    def __init__(self, parent):
        QtGui.QMainWindow.__init__(self, parent)
        # Add content
        central = CustomWidget(self)
        self.setCentralWidget(central)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    sw = MyMainWindow(None)
    sw.show()
    sys.exit(app.exec_())
