#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
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

    def __init__(self, pos):
        radius = 10
        rect = QtCore.QRectF(-radius / 2, -radius / 2, radius, radius)
        QtGui.QGraphicsEllipseItem.__init__(self, rect)
        self.setFlag(QtGui.QGraphicsItem.ItemIgnoresTransformations)
        self.setPos(pos)

        pen = QtGui.QPen(QtCore.Qt.darkGreen)
        pen.setWidthF(1.2)
        self.setPen(pen)

    def paint(self, painter, options, widget):
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        super().paint(painter, options, widget)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, False)
