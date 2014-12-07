#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
And logic item with variable number of inputs.
'''

from PySide import QtGui, QtCore

import logicitems


class AndItem(logicitems.LogicItem):
    
    def __init__(self, input_count = 3):
        super().__init__()
        self._input_count = input_count
        
        self.setAcceptHoverEvents(True)
        
        # internal state
        self._body_rect = None
    
    def _update_state(self):
        assert self.scene() is not None
        self._invalidate_bounding_rect()
        scale = self.scene().get_grid_spacing()
        # update body
        self._body_rect = QtCore.QRectF(0, -scale/2, scale * 2, 
                                        scale * (self._input_count))
        # update connectors
        for i in range(self._input_count):
            # inputs
            logicitems.ConnectorItem(
                self, QtCore.QPointF(0, scale * (i)),
                QtCore.QPointF(-scale, scale * (i)))
        # output
        mid_point = int(self._input_count / 2)
        logicitems.ConnectorItem(
            self, QtCore.QPointF(2 * scale, scale * (mid_point)),
            QtCore.QPointF(3 * scale, scale * (mid_point)))
    
    def itemChange(self, change, value):
        if change is QtGui.QGraphicsItem.ItemSceneHasChanged:
            if value is not None:
                self._update_state()
        return super().itemChange(change, value)
    
    def ownBoundingRect(self):
        assert self._body_rect is not None
        return self._body_rect
    
    def paint(self, painter, options, widget):
        painter.setBrush(QtGui.QColor(255, 255, 128))
        painter.setPen(QtCore.Qt.black)
        painter.drawRect(self._body_rect)
    
    def hoverMoveEvent(self, event):
        self.unsetCursor()
        super().hoverMoveEvent(event)
        if self.isSelected() and \
                QtCore.QRectF(0, 0, 100, 100).contains(event.pos()):
            self.setCursor(QtCore.Qt.SizeVerCursor)
