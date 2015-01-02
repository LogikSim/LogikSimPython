#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Connectors of Logic Items where lines be attached.
'''

from PySide import QtGui, QtCore

from .itembase import ItemBase


class ConnectorItem(ItemBase):
    def __init__(self, parent, start, anchor, is_input, index):
        """
        anchor is the position, at which lines can connect to
        """
        super().__init__(parent)

        self._line = QtCore.QLineF(start, anchor)
        self._is_input = is_input
        self._index = index

        self._logic_state = False

        self._bounding_rect_valid = False
        self._bounding_rect = None

    def _invalidate_bounding_rect(self):
        self.prepareGeometryChange()
        self._bounding_rect_valid = False

    def toggle(self):
        """Toggle input signal."""
        if not self.is_input():
            raise Exception("Can only toggle inputs.")
        self.scene().interface().schedule_edge(self.id(), self.index(),
                                               not self.logic_state(), 0)

    def is_input(self):
        """Returns True if connector is an input."""
        return self._is_input

    def index(self):
        """Returns index of connector port."""
        return self._index

    def id(self):
        """Returns backend id of connector."""
        return self.parentItem().id()

    def is_registered(self):
        """Returns true if connector is registered in backend."""
        return self.parentItem().is_registered()

    def is_valid(self):
        """Returns True if connector has valid shape."""
        if self.scene() is None:
            return False
        return self._line.length() == self.scene().get_grid_spacing()

    def connect(self, linetree):
        """
        Connect output to linetree.

        Only registred outputs can be connected, otherwise an Exception
        is thrown.
        """
        if not self.is_registered():
            raise Exception("Item not registered")

        # setup connection in backend
        self.scene().interface().connect(
            self.id(), self.index(), linetree.id(), 0)

    def disconnect(self):
        """Disconnect connected output to linetree."""
        if not self.is_registered():
            return

        # disconect connection in backend
        self.scene().interface().disconnect(self.id(), self.index())

    def set_logic_state(self, state):
        if state != self._logic_state:
            self._logic_state = state
            self.update()

    def logic_state(self):
        return self._logic_state

    def anchorPoint(self):
        """Returns position where lines can connect to."""
        return self.mapToScene(self._line.p2())

    def setLine(self, start, anchor):
        self._invalidate_bounding_rect()
        self._line = QtCore.QLineF(start, anchor)

    def boundingRect(self):
        if not self._bounding_rect_valid:
            self._bounding_rect = self._line_to_col_rect(self._line)
            self._bounding_rect_valid = True
        return self._bounding_rect

    def paint(self, painter, option, widget=None):
        # draw line
        if self.is_valid():
            if self.logic_state():
                painter.setPen(QtGui.QPen(QtCore.Qt.red))
            else:
                painter.setPen(QtGui.QPen(QtCore.Qt.black))
        else:
            painter.setPen(QtGui.QPen(QtCore.Qt.lightGray))
        painter.drawLine(self._line)
