#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Edge indicators mark crossing and connected lines in a line tree.
'''

from PySide import QtGui, QtCore

from .itembase import ItemBase


class LineEdgeIndicator(ItemBase):
    """Mark crossing and connected lines."""

    def __init__(self, parent, position):
        super().__init__(parent)

        self.setFlag(QtGui.QGraphicsItem.ItemIgnoresTransformations)

        width = 4
        self._rect = QtCore.QRectF(-width / 2, -width / 2, width, width)
        self.setPos(position)

    def boundingRect(self):
        return self._rect

    def paint(self, painter, options, widget):
        painter.setBrush(QtCore.Qt.black)
        painter.setPen(QtCore.Qt.black)
        painter.drawRect(self._rect)
