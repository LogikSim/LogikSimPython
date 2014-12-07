#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Connectors of Logic Items where lines be attached.
'''

from PySide import QtGui, QtCore

from .itembase import ItemBase


class ConnectorItem(ItemBase):
    def __init__(self, start, anchor):
        """
        anchor is the position, at which lines can connect to
        """
        super().__init__()
        
        self._line = QtCore.QLineF(start, anchor)
        
        self._bounding_rect_valid = False
        self._bounding_rect = None

    def _invalidate_bounding_rect(self):
        self.prepareGeometryChange()
        self._bounding_rect_valid = False
    
    def is_valid(self):
        """
        returns weather the given connector has valid shape.
        """
        if self.scene() is None:
            return False
        return self._line.length() == self.scene().get_grid_spacing()

    def anchorPoint(self):
        """
        returns position where lines can connect to
        """
        return self._line.p2()

    def setLine(self, start, anchor):
        self._invalidate_bounding_rect()
        self._line = QtCore.QLineF(start, anchor)

    def boundingRect(self):
        if not self._bounding_rect_valid:
            self._bounding_rect = self._line_to_rect(self._line)
            self._bounding_rect_valid = True
        return self._bounding_rect
    
    def paint(self, painter, option, widget=None):
        # draw line
        if self.is_valid():
            painter.setPen(QtGui.QPen(QtCore.Qt.black))
        else:
            painter.setPen(QtGui.QPen(QtCore.Qt.lightGray))
        painter.drawLine(self._line)
