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

from .connectable_item import ConnectableItem
from .linetree import LineTree
from .connector import ConnectorItem


class LogicItem(ConnectableItem, QtGui.QGraphicsLayoutItem):
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

        ConnectableItem.__init__(self, parent, metadata)
        QtGui.QGraphicsLayoutItem.__init__(self, parent)

    def apply_update_frontend(self, metadata):
        super().apply_update_frontend(metadata)

        # feed input/output connectors with metadata update
        for con_item in self._inputs + self._outputs:
            con_item.apply_update_frontend(metadata)

    def setGeometry(self, rect):
        scene_offset = self.mapToScene(self.selectionRect().topLeft()) - \
            self.mapToScene(QtCore.QPointF(0, 0))
        self.setPos(rect.topLeft() - scene_offset)

    def sizeHint(self, which, constraint):
        return self.mapToScene(self.selectionRect()).boundingRect().size()

    def items_at_connections(self):
        """Overrides items_at_connections"""
        items_set = set()
        for con_item in self._inputs + self._outputs:
            items_set.update(con_item.items_at_connection())
        return items_set

    def connect_all_outputs(self):
        """Overrides connect_all_outputs."""
        for con_item in self._outputs:
            for item in self.scene().items(con_item.endPoint()):
                if isinstance(item, LineTree) or \
                        (isinstance(item, ConnectorItem) and item.is_input()):
                    con_item.connect(item)

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
        # invalidate bounding rect when child added or removed
        if change in (QtGui.QGraphicsItem.ItemChildAddedChange,
                      QtGui.QGraphicsItem.ItemChildRemovedChange):
            self._invalidate_bounding_rect()
        # update line connectors when connectable surrounding changed
        elif change == ConnectableItem.ItemConnectableSurroundingHasChanged:
            for con_item in self._inputs + self._outputs:
                con_item.update_anticipation()
        return super().itemChange(change, value)

    def boundingRect(self):
        if not self._bounding_rect_valid:
            self._bounding_rect = self.ownBoundingRect()
            self._bounding_rect_valid = True
        return self._bounding_rect
