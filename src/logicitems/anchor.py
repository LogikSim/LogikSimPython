#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can 
# be found in the LICENSE.txt file.
#
'''
Anchor indicator indicate where lines can be attached to.

They are shown during drawing new lines to snap to interesting anchors.
'''

from PySide import QtGui, QtCore


class LineAnchorIndicator(QtGui.QGraphicsEllipseItem):
    """ visual effect for line anchors while adding lines """
    def __init__(self, *args, **kargs):
        QtGui.QGraphicsEllipseItem.__init__(self, *args, **kargs)
        self.setPen(QtGui.QPen(QtCore.Qt.darkGreen))
    
    def setWidthF(self, width):
        if width != self.widthF():
            pen = self.pen()
            pen.setWidthF(width)
            self.setPen(pen)
    
    def widthF(self):
        return self.pen().widthF()
    
    def paint(self, painter, options, widget):
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        QtGui.QGraphicsEllipseItem.paint(self, painter, options, widget)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, False)

