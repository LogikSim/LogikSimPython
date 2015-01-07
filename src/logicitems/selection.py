#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Selection Items are boxes and anchors drawn for item selections.
'''

from PySide import QtGui, QtCore

from .itembase import ItemBase
from .connectable_item import ConnectableItem


class SelectionItem(ItemBase):
    def __init__(self):
        super().__init__()

        self.setZValue(1)
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtGui.QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.setCursor(QtCore.Qt.SizeAllCursor)

        self._rect = QtCore.QRectF(0, 0, 0, 0)
        self._bounding_rect = QtCore.QRectF(0, 0, 0, 0)

        # use timer to only process most recent update event
        self._update_state_timer = QtCore.QTimer()
        self._update_state_timer.timeout.connect(self._do_update_state)
        self._update_state_timer.setSingleShot(True)

    def _invalidate_state(self):
        """
        Makes sure that we group update events.

        This makes sure that _do_update_state is called only once,
        if many items are moved.
        """
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
            scene_poly = self.mapFromItem(item, item.selectionRect())
            self._rect = self._rect.united(scene_poly.boundingRect())
        if len(sel_items) > 1:
            offset = self.scene().get_grid_spacing() / 2
            self._rect.adjust(-offset, -offset, offset, offset)
        # make bounding rect a little bit wider (prevent drawing artefacts)
        self._bounding_rect = self._to_col_rect(
            self._rect, radius=self.scene().get_grid_spacing())

    def boundingRect(self):
        return self._bounding_rect

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        event.accept()

    def hoverMoveEvent(self, event):
        super().hoverMoveEvent(event)
        self.setCursor(QtCore.Qt.SizeAllCursor)

    def mouseMoveEvent(self, event):
        self.setCursor(QtCore.Qt.SizeAllCursor)
        # store old positions
        sel_items = self.scene().selectedItems()
        chanded_items_set = set(sel_items)
        for item in sel_items:
            chanded_items_set.update(item.items_at_connections())
        old_positions = {item: item.pos() for item in sel_items}
        # this moves all selected items
        super().mouseMoveEvent(event)
        # has any position changed?
        if any(item.pos() != old_pos
               for item, old_pos in old_positions.items()):
            for item in sel_items:
                chanded_items_set.update(item.items_at_connections())
            # notify to items that surrounding has changed
            for item in chanded_items_set:
                item.itemChange(
                    ConnectableItem.ItemConnectableSurroundingHasChanged, True)

    def itemChange(self, change, value):
        if self.scene() is not None:
            if change == QtGui.QGraphicsItem.ItemPositionHasChanged:
                self._do_update_state()
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
        for item in sel_items:
            poly = self.mapFromItem(item, item.selectionRect())
            painter.drawRect(poly.boundingRect())

        # combined selection box
        if len(sel_items) > 1:
            painter.setPen(self._selection_color_line)
            painter.drawRect(self._rect)

    @QtCore.Slot()
    def onSelectionChanged(self):
        """Selection in the scene changed."""
        self._invalidate_state()

    @QtCore.Slot()
    def onSelectedItemPosChanged(self):
        """The position of a selected item in the scene changed."""
        self._invalidate_state()
