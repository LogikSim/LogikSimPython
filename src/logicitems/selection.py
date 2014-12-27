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
    def __init__(self):
        super().__init__()

        self.setZValue(-1)
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtGui.QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.setCursor(QtCore.Qt.SizeAllCursor)

        self._rect = QtCore.QRectF(0, 0, 0, 0)
        self._initial_positions = {}
        self._start_position = None

        # use timer to only process most recent update event
        self._update_state_timer = QtCore.QTimer()
        self._update_state_timer.timeout.connect(self._do_update_state)
        self._update_state_timer.setSingleShot(True)

    def _invalidate_state(self):
        self._update_state_timer.start()

    def _do_update_state(self):
        """
        Updates all internal state.

        Call _invalidate_state instead of calling this method directly.
        """
        self.prepareGeometryChange()
        sel_items = self.scene().selectedItems()
        # get combined bounding rect
        self._rect = QtCore.QRectF(0, 0, 0, 0)
        for item in sel_items:
            scene_poly = item.mapToScene(item.selectionRect())
            self._rect = self._rect.united(scene_poly.boundingRect())
        if len(sel_items) > 1:
            offset = self.scene().get_grid_spacing() / 2
            self._rect.adjust(-offset, -offset, offset, offset)
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
        self._invalidate_state()

    def boundingRect(self):
        return self._rect

    def hoverMoveEvent(self, event):
        super().hoverMoveEvent(event)
        self.setCursor(QtCore.Qt.SizeAllCursor)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self.setCursor(QtCore.Qt.SizeAllCursor)

    def itemChange(self, change, value):
        if self.scene() is not None:
            if change == QtGui.QGraphicsItem.ItemPositionHasChanged:
                self._move_to(value)
        return super().itemChange(change, value)

    def paint(self, painter, options, widget):
        """
        When overwriting this function, call this partent at the end.
        """
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.setPen(QtGui.QPen(self._selection_color_line, 0,
                                  QtCore.Qt.DashLine))
        # detailed selection
        sel_items = self.scene().selectedItems()
        if len(sel_items) > 1:
            for item in sel_items:
                poly = self.mapFromItem(item, item.selectionRect())
                painter.drawRect(poly.boundingRect())

        # combined selection box
        painter.drawRect(self.boundingRect())

    @QtCore.Slot()
    def onSelectionChanged(self):
        """Selection in the scene changed."""
        self._invalidate_state()

    @QtCore.Slot()
    def onSelectedItemPosChanged(self):
        """The position of a selected item in the scene changed."""
        self._invalidate_state()
