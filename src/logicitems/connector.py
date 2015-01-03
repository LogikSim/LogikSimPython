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

from PySide import QtCore

from .state_line_item import StateLineItem


class ConnectorItem(StateLineItem):
    def __init__(self, parent, start, anchor, end, is_input, index):
        """
        anchor is the position, at which lines can connect to
        """
        super().__init__(parent)

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
        return True

    def connect(self, item):
        """
        Connect output to item.

        Only registred outputs can be connected, otherwise an Exception
        is thrown.
        """
        if not self.is_registered():
            raise Exception("Item not registered")

        # setup connection in backend
        self.scene().interface().connect(
            self.id(), self.index(), item.id(), 0, self.visual_delay())

    def disconnect(self):
        """Disconnect connected output."""
        if not self.is_registered():
            return

        # disconnect connection in backend
        self.scene().interface().disconnect(self.id(), self.index())

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
        drawing_end = self._end if self._is_connected else self._anchor
        delay = self._delay

        yield from self.iter_state_line_segments_helper(
            origin=self._start.toTuple(),
            destination=drawing_end.toTuple(),
            delay=delay,
            clock=self.scene().registry().clock(),
            is_vertical=False)
        return delay
