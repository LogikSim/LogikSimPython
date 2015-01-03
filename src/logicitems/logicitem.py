#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Logic items are all items a logic behavior based on inputs and outputs.
'''

from PySide import QtGui, QtCore

from .insertable_item import InsertableItem


class LogicItem(InsertableItem, QtGui.QGraphicsLayoutItem):
    """
    Defines logic item base class.

    All children must implement the methods: ownBoundingRect, paint
    """

    def __init__(self, parent=None, metadata={}):
        # stores bounding rect
        self._bounding_rect_valid = False
        self._bounding_rect = None

        # store inputs and outputs connectors
        self._inputs = []
        self._outputs = []

        InsertableItem.__init__(self, parent, metadata)
        QtGui.QGraphicsLayoutItem.__init__(self, parent)

    def apply_update(self, metadata):
        # TODO: updates on input
#        input_states = metadata.get('input-states', None)
#        if input_states is not None:
#            for input_con, state in zip(self._inputs, input_states):
#                input_con.set_logic_state(state)

        output_states = metadata.get('output-states', None)
        if output_states is not None:
            for output_con, state in zip(self._outputs, output_states):
                output_con.set_logic_state(state)

    def setGeometry(self, rect):
        scene_offset = self.mapToScene(self.selectionRect().topLeft()) - \
            self.mapToScene(QtCore.QPointF(0, 0))
        self.setPos(rect.topLeft() - scene_offset)

    def sizeHint(self, which, constraint):
        return self.mapToScene(self.selectionRect()).boundingRect().size()

    def _invalidate_bounding_rect(self):
        self.prepareGeometryChange()
        self._bounding_rect_valid = False

    def ownBoundingRect(self):
        """ bounding rect of LogicItem without considering children """
        raise NotImplementedError

    def selectionRect(self):
        """
        Implements selectionRect

        By default returns own combined with child bounding rects.
        """
        return self.boundingRect().united(self.childrenBoundingRect())

    def itemChange(self, change, value):
        if change in (QtGui.QGraphicsItem.ItemChildAddedChange,
                      QtGui.QGraphicsItem.ItemChildRemovedChange):
            self._invalidate_bounding_rect()
        return super().itemChange(change, value)

    def boundingRect(self):
        if not self._bounding_rect_valid:
            self._bounding_rect = self.ownBoundingRect()
            self._bounding_rect_valid = True
        return self._bounding_rect
