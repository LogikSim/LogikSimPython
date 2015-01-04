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

from PySide import QtCore, QtGui

from .state_line_item import StateLineItem


class ConnectorItem(StateLineItem):
    def __init__(self, parent, start, anchor, end, is_input, index):
        """
        anchor is the position, at which lines can connect to
        """
        super().__init__(parent)

        self.setFlag(QtGui.QGraphicsItem.ItemSendsScenePositionChanges)

        self._start = start
        self._anchor = anchor
        self._end = end
        self._is_input = is_input
        self._index = index

        self._is_connected = False
        self.set_animate_lines(False)

        self._bounding_rect_valid = False
        self._bounding_rect = None

        # delay of connector given by backend
        self._delay = 0

    def update_metadata_state(self, state):
        """
        Called by parent item to propagate metadata updates.

        Instead of the full metadata only the logic state of
        the specific connector is propagated.
        """
        self.set_logic_state(state)

    def update_metadata_connection(self, connection_data):
        """
        Called by parent item to propagate metadata updates.

        Instead of the full metadata only the connection data
        of the specific connector is propagated.
        """
        if self.is_input():
            dst_id, _ = connection_data
            con_delay = self.visual_delay()
        else:
            dst_id, _, con_delay = connection_data

        self._is_connected = dst_id is not None
        self._delay = con_delay
        self.set_animate_lines(self._is_connected)
        self.request_paint()

    def _update_connection(self):
        from .linetree import LineTree

        if self.scene() is not None:
            found_con = False
            for item in self.scene().items(self.endPoint()):
                if isinstance(item, LineTree):
                    if item.is_registered() and self.is_registered():
                        item.connect(self)
                    found_con = True
            if self.is_temporary():
                self.set_anchored(found_con)

    def set_anchored(self, value):
        """If value is True, visualizes the object as being connected."""
        self.set_animate_lines(True if value else self.is_connected())
        # use direct update here for immediate feedback
        QtGui.QGraphicsItem.update(self)

    def visual_delay(self):
        """Get delay based on visual extend of the connector."""
        if self.scene() is None:
            return 0
        return abs((self._end - self._start).manhattanLength() *
                   self._delay_per_gridpoint / self.scene().get_grid_spacing())

    def _invalidate_bounding_rect(self):
        self.prepareGeometryChange()
        self._bounding_rect_valid = False

    def toggle(self):
        """Toggle input signal."""
        if not self.is_input():
            raise Exception("Can only toggle inputs.")
        if not self._is_connected:
            new_state = not self.get_last_logic_state()
            self.scene().interface().schedule_edge(
                self.id(), self.index(), new_state, 0)

    def is_input(self):
        """Returns True if connector is an input."""
        return self._is_input

    def is_output(self):
        """Returns True if connector is an output."""
        return not self._is_input

    def index(self):
        """Returns index of connector port."""
        return self._index

    def id(self):
        """Returns backend id of connector."""
        return self.parentItem().id()

    def is_registered(self):
        """Returns True if connector is registered in backend."""
        return self.parentItem() is not None and \
            self.parentItem().is_registered()

    def is_temporary(self):
        """Return True if connector is temporary."""
        return self.parentItem() is not None and \
            self.parentItem().is_temporary()

    def connect(self, item):
        """Setup connection with given item."""
        if not self.is_registered():
            raise Exception("Item not registered")

        if self.is_input():
            item.connect(self)
        else:
            # setup connection in backend
            self.scene().interface().connect(
                self.id(), self.index(), item.id(), 0, self.visual_delay())

    def is_connected(self):
        return self._is_connected

    def anchorPoint(self):
        """Returns where AnchorItems should be drawn at."""
        return self.mapToScene(self._anchor)

    def endPoint(self):
        """Returns position where lines can connect to."""
        return self.mapToScene(self._end)

    def boundingRect(self):
        if not self._bounding_rect_valid:
            line = QtCore.QLineF(self._start, self._end)
            self._bounding_rect = self._line_to_col_rect(line)
            self._bounding_rect_valid = True
        return self._bounding_rect

    def iter_state_line_segments(self):
        """
        Returns iterator of line segments with state information.

        :return: iterator with items of (QLineF, state)
        """
        start = self._start
        drawing_end = (self._end if self.animate_lines() else self._anchor)
        delay = self._delay

        yield from self.iter_state_line_segments_helper(
            origin=(drawing_end if self.is_input() else start).toTuple(),
            destination=(start if self.is_input() else drawing_end).toTuple(),
            delay=delay,
            clock=self.scene().registry().clock(),
            is_vertical=False)
        return delay

    def on_registration_status_changed(self):
        """Called when registration status of parent is changed."""
        self._update_connection()

    def itemChange(self, change, value):
        if change == QtGui.QGraphicsItem.ItemParentHasChanged or \
                change == QtGui.QGraphicsItem.ItemSceneHasChanged or \
                change == QtGui.QGraphicsItem.ItemScenePositionHasChanged:
            self._update_connection()

        return super().itemChange(change, value)
