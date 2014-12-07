#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Selection Items are boxes and anchors drawn for item selections.
'''

from PySide import QtGui, QtCore

from .itembase import ItemBase


class SelectionItem(ItemBase):
    _selection_color = QtGui.QColor(40, 125, 210)
    
    def __init__(self):
        super().__init__()
        
        self.setZValue(1)
        self._rect = QtCore.QRectF(0, 0, 0, 0)
        self._initial_positions = {}
        self._start_position = None
        
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtGui.QGraphicsItem.ItemSendsGeometryChanges)
        
    def _update_state(self):
        self.prepareGeometryChange()
        sel_items = self.scene().selectedItems()
        # get bounding rect
        self._rect = QtCore.QRectF(0, 0, 0, 0)
        for item in sel_items:
            scene_poly = item.mapToScene(item.boundingRect())
            self._rect = self._rect.united(scene_poly.boundingRect())
        # store initial positions
        self._initial_positions = {item: item.pos() for item in sel_items}
        # set position
        pos = self._rect.topLeft()
        self._start_position = pos
        self._rect.translate(-pos)
        self.setPos(pos)
    
    def _move_to(self, pos):
        for item, init_pos in self._initial_positions.items():
            item.setPos(init_pos - self._start_position + pos)
        self._update_state()

    def boundingRect(self):
        return self._rect
    
    def itemChange(self, change, value):
        if self.scene() is not None:
            #
            # round position to grid point
            if change == QtGui.QGraphicsItem.ItemPositionChange:
                return value #self.scene().roundToGrid(value)
            elif change == QtGui.QGraphicsItem.ItemPositionHasChanged:
                self._move_to(value)
        return super().itemChange(change, value)

    def paint(self, painter, options, widget):
        """
        When overwriting this function, call this partent at the end.
        """
        # item selection box
        rect = self.boundingRect()
        painter.setBrush(QtCore.Qt.NoBrush)
        #painter.setPen(QtCore.Qt.white)
        #painter.drawRect(rect)
        painter.setPen(QtGui.QPen(self._selection_color, 0,
                                  QtCore.Qt.DashLine))
        painter.drawRect(rect)
    
    @QtCore.Slot()
    def onSelectionChanged(self):
        self._update_state()
