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
from backend.simple_element import SimpleElementGuiItem


class AndItem(logicitems.LogicItem, SimpleElementGuiItem):
    def __init__(self, parent=None, metadata={}):
        super().__init__(parent)
        self._input_count = metadata['#inputs']
        self.setPos(metadata.get('x', 0), metadata.get('y', 0))

        self.setAcceptHoverEvents(True)

        # internal state
        self._show_handles = False
        self._body_rect = None
        self._connectors = []
        self._handles = {}

    def _set_show_handles(self, value):
        if value != self._show_handles:
            self._show_handles = value
            self._update_resize_tool_handles()

    def _update_state(self):
        assert self.scene() is not None
        self._invalidate_bounding_rect()
        scale = self.scene().get_grid_spacing()
        # update body
        self._body_rect = QtCore.QRectF(0, -scale/2, scale * 2,
                                        scale * (self._input_count))
        # update connectors
        for con in self._connectors:
            con.setParentItem(None)
        self._connectors = []
        for i in range(self._input_count):
            # inputs
            con = logicitems.ConnectorItem(
                self, QtCore.QPointF(0, scale * (i)),
                QtCore.QPointF(-scale, scale * (i)))
            self._connectors.append(con)
        # output
        mid_point = int((self._input_count - 1) / 2)
        con = logicitems.ConnectorItem(
            self, QtCore.QPointF(2 * scale, scale * (mid_point)),
            QtCore.QPointF(3 * scale, scale * (mid_point)))
        self._connectors.append(con)

    def _update_resize_tool_handles(self):
        for handle in self._handles.values():
            handle.setParentItem(None)
        self._handles = {}
        if self.isSelected() and self._show_handles:
            scale = self.scene().get_grid_spacing()
            ht = logicitems.ResizeHandle(self, horizontal=False,
                                         resize_callback=self.on_handle_resize)
            ht.setPos(scale, -scale/2)
            hb = logicitems.ResizeHandle(self, horizontal=False,
                                         resize_callback=self.on_handle_resize)
            hb.setPos(scale, (self._input_count - 0.5) * scale)
            self._handles = {'top': ht, 'bottom': hb}

    def on_handle_resize(self, handle, delta):
        sign = (-1 if handle is self._handles['top'] else 1)
        round_delta = self.scene().roundToGrid(delta)
        input_delta = sign * self.scene().to_grid(round_delta.y())
        new_input_count = max(2, self._input_count + input_delta)
        if new_input_count != self._input_count:
            eff_pos_delta = self.scene().to_scene_point(
                (0, (new_input_count - self._input_count)))
            # update input count
            self._input_count = new_input_count
            self._update_state()
            # move item
            if handle is self._handles['top']:
                self.setPos(self.pos() - eff_pos_delta)
            # update handle position
            self._handles['bottom'].setPos(self._handles['bottom'].pos() +
                                           eff_pos_delta)
            # notify scene of change
            self.scene().selectedItemPosChanged.emit()

    def itemChange(self, change, value):
        if change is QtGui.QGraphicsItem.ItemSceneHasChanged:
            if value is not None:
                self._update_state()
        elif change is QtGui.QGraphicsItem.ItemSelectedHasChanged:
            self._update_resize_tool_handles()
        elif change == logicitems.ItemBase.ItemSingleSelectionHasChanged:
            self._set_show_handles(value)
        return super().itemChange(change, value)

    def ownBoundingRect(self):
        assert self._body_rect is not None
        return self._body_rect

    def selectionRect(self):
        rect = self.ownBoundingRect()
        for con in self._connectors:
            rect = rect.united(con.boundingRect())
        return rect

    def paint(self, painter, options, widget):
        painter.setBrush(QtGui.QColor(255, 255, 128))
        painter.setPen(QtCore.Qt.black)
        painter.drawRect(self._body_rect)
