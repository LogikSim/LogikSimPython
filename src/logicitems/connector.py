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
    def __init__(self, parent, start, anchor, end,
                 is_input, port):
        """
        anchor is the position, at which lines can connect to
        """
        super().__init__(parent)

        self.setFlag(QtGui.QGraphicsItem.ItemStacksBehindParent)

        self._start = start
        self._anchor = anchor
        self._end = end
        self._is_input = is_input
        self._port = port

        self.set_animate_lines(False)

        self._bounding_rect_valid = False
        self._bounding_rect = None

    def apply_update_frontend(self, metadata):
        """Apply changes from metadata to this item."""
        # extract state
        states = metadata.get(
            'input-states' if self._is_input else 'output-states', None)
        if states is not None:
            self.set_logic_state(states[self.port()])

        # connection change
        if 'inputs' in metadata or 'outputs' in metadata:
            self.set_animate_lines(self.is_connected())
            # use immediate update
            self.update()

    def items_at_connection(self):
        """Return set of all items in the scene located at the connections."""
        from .linetree import LineTree

        con_items = set()
        if self.scene() is not None:
            for item in self.scene().items(self.endPoint()):
                if item is not self:
                    if isinstance(item, LineTree):
                        con_items.add(item)
                    elif isinstance(item, ConnectorItem):
                        con_items.add(item.parentItem())
        return con_items

    def connect(self, item):
        """Connection output to other item."""
        assert self.is_output(), "Can only connect outputs."
        assert self.is_registered()

        # setup connection in backend
        from .linetree import LineTree
        if isinstance(item, LineTree):
            port = 0
        elif isinstance(item, ConnectorItem):
            port = item.port()
        else:
            raise Exception("Unknown item")
        self.parentItem().notify_backend_connect(
            self.port(), item.id(), port, self.visual_delay())

    def set_anchored(self, value):
        """If value is True, visualizes the object as being connected."""
        self.set_animate_lines(True if value else self.is_connected())
        # use direct update here for immediate feedback
        QtGui.QGraphicsItem.update(self)

    def update_anticipation(self):
        """
        Update the anticipation of connections.

        Anticipated connections are visualized just as real connections,
        but reported to the backend.

        Called by parent whenever the connectable surrounding changes.
        """
        self.set_animate_lines(self.is_connected())

    def delay(self):
        if self.is_input():
            return self.visual_delay()
        else:
            return self.parentItem().output_delay(self.port()) or 0

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
        if not self.is_connected():
            new_state = not self.get_last_logic_state()
            self.scene().interface().schedule_edge(
                self.id(), self.port(), new_state, 0)

    def is_input(self):
        """Returns True if connector is an input."""
        return self._is_input

    def is_output(self):
        """Returns True if connector is an output."""
        return not self._is_input

    def port(self):
        """Returns connector port."""
        return self._port

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

    def is_connected(self):
        if self.is_inactive():
            return len(self.items_at_connection()) > 0
        else:
            return self.parentItem() is not None and \
                self.parentItem().is_connected(self.is_input(), self.port())

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
        if self.animate_lines():
            drawing_end = self._end
        else:
            drawing_end = self._anchor
        delay = self.delay()

        yield from self.iter_state_line_segments_helper(
            origin=(drawing_end if self.is_input() else start).toTuple(),
            destination=(start if self.is_input() else drawing_end).toTuple(),
            delay=delay,
            clock=self.scene().registry().clock(),
            is_vertical=False)
        return delay
