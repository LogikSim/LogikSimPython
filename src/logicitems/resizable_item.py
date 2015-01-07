#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Resizable logic item with variable number of inputs.
'''

from PySide import QtGui, QtCore

import logicitems
from actions.resize_action import ResizeAction
from .insertable_item import disabled_undo


class ResizableItem(logicitems.LogicItem):
    # item overlap above first and below last input connector in
    # in grid gap fraction
    _overlap = 0.37

    def __init__(self, parent, metadata):
        metadata.setdefault('#inputs', 2)

        # internal state
        self._input_count = None
        self._show_handles = False
        self._body_rect = QtCore.QRectF(0, 0, 0, 0)
        self._handles = {}
        self._delay = None

        super().__init__(parent=parent, metadata=metadata)
        self.setFlag(QtGui.QGraphicsItem.ItemSendsScenePositionChanges)

    def apply_update_frontend(self, metadata):
        super().apply_update_frontend(metadata)

        input_count = metadata.get('#inputs')
        if input_count is not None and input_count != self.get_input_count():
            self.set_input_count_and_pos(input_count)

    def update_backend(self, backend_metadata):
        super().update_backend(backend_metadata)

        metadata = {}
        if self._input_count != backend_metadata.get('#inputs'):
            metadata['#inputs'] = self._input_count
        if self._delay != backend_metadata.get('delay'):
            metadata['delay'] = self._delay
        self.notify_backend(metadata)

    def get_input_count(self):
        return self._input_count

    def set_input_count(self, new_input_count):
        self.set_input_count_and_pos(new_input_count)

    def set_input_count_and_pos(self, new_input_count, new_pos=None):
        # create undo event
        if self.scene() is not None:
            action = ResizeAction(self.scene().getUndoGroupId(), self,
                                  self.get_input_count(), self.pos(),
                                  new_input_count, new_pos)
            self._register_undo_action(action)

        def apply_change():
            # update input count
            self._input_count = new_input_count
            self._update_state()

            # update position
            if new_pos is not None:
                with disabled_undo(self):
                    self.setPos(new_pos)

        # notify surrounding
        self._change_and_notify_surrounding(apply_change,
                                            condition_function=lambda: True,
                                            notify_surrounding=True)

    def _set_show_handles(self, value):
        if value != self._show_handles:
            self._show_handles = value
            self._update_resize_tool_handles()

    def _update_state(self):
        if self.scene() is None:
            return

        self._invalidate_bounding_rect()
        scale = self.scene().get_grid_spacing()
        # update body
        self._body_rect = self._to_col_rect(QtCore.QRectF(
            0, -scale * self._overlap, scale * 2,
            scale * (self._input_count - 1 + 2 * self._overlap)))

        # update connectors
        for con in self._inputs + self._outputs:
            con.setParentItem(None)
        self._inputs = []
        self._outputs = []
        # inputs
        for i in range(self._input_count):
            con = logicitems.ConnectorItem(
                parent=self,
                start=QtCore.QPointF(0, scale * i),
                anchor=QtCore.QPointF(-0.5 * scale, scale * i),
                end=QtCore.QPointF(-scale, scale * i),
                is_input=True,
                port=i)
            self._inputs.append(con)
        # output
        mid_point = int((self._input_count - 1) / 2)
        con = logicitems.ConnectorItem(
            parent=self,
            start=QtCore.QPointF(2 * scale, scale * mid_point),
            anchor=QtCore.QPointF(2.5 * scale, scale * mid_point),
            end=QtCore.QPointF(3 * scale, scale * mid_point),
            is_input=False,
            port=0)
        self._outputs.append(con)

        # setup delay based on #inputs
        self._delay = (2 + self._input_count // 2) * self._delay_per_gridpoint

        # notify change
        self.register_change_during_inactivity()

    def _update_resize_tool_handles(self):
        show_handles = self.isSelected() and self._show_handles
        if not show_handles:
            for handle in self._handles.values():
                handle.scene().removeItem(handle)
            self._handles = {}
        else:
            scale = self.scene().get_grid_spacing()
            if not self._handles:
                ht = logicitems.ResizeHandle(
                    horizontal=False, resize_callback=self.on_handle_resize)
                self.scene().addItem(ht)
                hb = logicitems.ResizeHandle(
                    horizontal=False, resize_callback=self.on_handle_resize)
                self.scene().addItem(hb)
                self._handles = {'top': ht, 'bottom': hb}
            self._handles['top'].setPos(self.mapToScene(scale, -scale *
                                                        self._overlap))
            self._handles['bottom'].setPos(
                self.mapToScene(scale, (self._input_count - 1 +
                                        self._overlap) * scale))

    def on_handle_resize(self, handle, delta):
        sign = (-1 if handle is self._handles['top'] else 1)
        round_delta = self.scene().roundToGrid(delta)
        input_delta = sign * self.scene().to_grid(round_delta)[1]  # y delta
        new_input_count = max(2, self._input_count + input_delta)
        if new_input_count != self._input_count:
            eff_pos_delta = self.scene().to_scene_point(
                (0, (new_input_count - self._input_count)))
            # calc new position
            if handle is self._handles['top']:
                new_pos = self.pos() - eff_pos_delta
            else:
                new_pos = None
            # update item
            self.set_input_count_and_pos(new_input_count, new_pos)
            # update handle position
            self._update_resize_tool_handles()
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
        elif change == logicitems.ItemBase.ItemScenePositionHasChanged:
            self._update_resize_tool_handles()
        return super().itemChange(change, value)

    def ownBoundingRect(self):
        return self._body_rect

    def selectionRect(self):
        rect = self.ownBoundingRect()
        for con in self._inputs + self._outputs:
            rect = rect.united(con.boundingRect())
        return rect

    def paint(self, painter, options, widget):
        painter.setBrush(QtGui.QColor(255, 255, 128))
        painter.setPen(QtCore.Qt.black)
        painter.drawRect(self._body_rect)
