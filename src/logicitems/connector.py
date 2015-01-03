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

        self._logic_state = False
        self._is_connected = False

        self._bounding_rect_valid = False
        self._bounding_rect = None

        # contains last logic states with entries (sim_time, value)
        self._input_state = False
        self._logic_states = []
        self._delay = self._get_delay(end)
        self._anchor_delay = self._get_delay(anchor)

        # timer for updating
        self._update_paint = QtCore.QTimer()
        self._update_paint.timeout.connect(self.do_update_paint)
        self._update_paint.setInterval(40)
        self._update_paint.setSingleShot(True)

    def _get_delay(self, pos):
        return abs((pos - self._start).manhattanLength() * \
            self._delay_per_gridpoint / self.scene().get_grid_spacing())

    def _invalidate_bounding_rect(self):
        self.prepareGeometryChange()
        self._bounding_rect_valid = False

    def toggle(self):
        """Toggle input signal."""
        if not self.is_input():
            raise Exception("Can only toggle inputs.")
        if not self._is_connected:
            self._input_state = not self._input_state
            self.scene().interface().schedule_edge(self.id(), self.index(),
                                                   self._input_state, 0)
            print(self._input_state)
            # TODO: update


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

    def delay(self):
        return self._delay

    def connect(self, linetree):
        """
        Connect output to linetree.

        Only registred outputs can be connected, otherwise an Exception
        is thrown.
        """
        assert not self._is_connected
        if not self.is_registered():
            raise Exception("Item not registered")

        # setup connection in backend
        self.scene().interface().connect(
            self.id(), self.index(), linetree.id(), 0, self.delay())
        self._is_connected = True
        self.update()

    def disconnect(self):
        """Disconnect connected output to linetree."""
        assert self._is_connected
        if not self.is_registered():
            return

        # disconect connection in backend
        self.scene().interface().disconnect(self.id(), self.index())
        self._is_connected = False
        self.update()

    def set_logic_state(self, state):
        if self.scene() is not None:
            self._logic_states.append(((self.scene().registry().clock()),
                                        state))

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

    def _iter_state_line_segments(self):
        """
        Returns iterator of line segments with state information.

        :return: iterator with items of (QLineF, state)
        """
        if self._is_connected:
            drawing_end = self._end
            delay = self._delay
        else:
            drawing_end = self._anchor
            delay = self._anchor_delay

        if len(self._logic_states) == 0 or self._is_input:
            yield (QtCore.QLineF(self._start, drawing_end), self._input_state)
            return

        clock = self.scene().registry().clock()
        origin = self._start.toTuple()
        destination = drawing_end.toTuple()

        next_index = len(self._logic_states) - 1
        current_state = self._logic_states[next_index][1]

        start = origin
        while True:
            if next_index >= 0:
                state_clock, state = self._logic_states[next_index]
                delta = clock - state_clock
            else:
                state = current_state
                delta = delay

            if delta > 0:  # it has finite length --> visible
                end = list(destination)
                if delta < delay:
                    end[0] = (origin[0] + delta / delay *
                              (destination[0] - origin[0]))
                yield QtCore.QLineF(QtCore.QPointF(*start),
                                    QtCore.QPointF(*end)), state

                start = end

            if delta >= delay:  # we are at the end of line
                break

            current_state = state
            next_index -= 1

    def do_update_paint(self):
        # redraw
        QtGui.QGraphicsItem.update(self)

    def paint(self, painter, option, widget=None):
        # TODO: merge paint logic of Connector and LineTree in new class

        for line, state in self._iter_state_line_segments():
            color = QtCore.Qt.red if state else QtCore.Qt.black
            painter.setPen(QtGui.QPen(color))
            painter.drawLine(line)
        # TODO: delete old logic states

        # TODO: stop drawing on steady state
        self._update_paint.start()
