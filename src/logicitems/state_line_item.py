#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Item that provides animated lines of logic states.
'''

from PySide import QtGui, QtCore

from .itembase import ItemBase

class StateLineItem(ItemBase):
    def __init__(self, parent=None):
        super().__init__(parent)

        # contains last logic states with entries (sim_time, value)
        self._logic_states = []

        # timer for updating
        self._update_paint = QtCore.QTimer()
        self._update_paint.timeout.connect(self.do_update_paint)
        self._update_paint.setInterval(40)
        self._update_paint.setSingleShot(True)

    def set_logic_state(self, state):
        if self.scene() is not None:
            self._logic_states.append(((self.scene().registry().clock()),
                                        state))
        # TODO: update

    def get_last_logic_state(self):
        """Returns most recent logic state."""
        if len(self._logic_states) > 0:
            return self._logic_states[-1][1]
        else:
            return False

    def iter_state_line_segments_helper(self, origin, destination, delay,
                                        clock, is_vertical, parent_delay=0,
                                        parent_index=None, parent_state=None):
        """
        Iterator over line segments with specific state for given line.

        The function uses the current history of logic states to annotate
        the given line into segments of its logic values, considering
        its delay and possible parent item.

        :param origin: start of line as tuple (x, y) of float
        :param destination: end of line as tuple (x, y) of float
        :param delay: delay of line as float
        :param clock: clock used for segmentation as float
        :param is_vertical: is the given line vertical as bool
        :param parent_delay: delay of possible parent as float
        :param parent_index: index of possible parent, see return
        :param parent_state: state of possible parent, see return
        :return: (next_index, next_state). These return values can be used
            to animate child lines (lines attached at this line) by providing
            these values when segmenting each child.
        """
        if len(self._logic_states) == 0:
            yield (QtCore.QLineF(QtCore.QPointF(*origin),
                                 QtCore.QPointF(*destination)),
                   self.get_last_logic_state())
            current_index = parent_index
            current_state = parent_state
        else:
            if parent_index is None:
                parent_index = len(self._logic_states) - 1
            if parent_state is None:
                parent_state = self.get_last_logic_state()

            start = origin
            j = is_vertical
            current_index = parent_index
            current_state = parent_state
            while True:
                if current_index >= 0:
                    state_clock, state = self._logic_states[current_index]
                    delta = clock - state_clock - parent_delay
                else:
                    state = current_state
                    delta = delay

                if delta > 0:  # it has finite length --> visible
                    end = list(destination)
                    if delta < delay:
                        end[j] = (origin[j] + delta / delay *
                                  (destination[j] - origin[j]))
                    yield QtCore.QLineF(QtCore.QPointF(*start),
                                        QtCore.QPointF(*end)), state

                    start = end

                if delta >= delay:  # we are at the end of line
                    break

                current_state = state
                current_index -= 1
        return current_index, current_state

    def iter_state_line_segments(self):
        """
        Iterator over all line segments with specific state.

        Implement this function by using iter_state_line_segments_helper.
        """
        raise NotImplementedError

    def do_update_paint(self):
        # redraw
        QtGui.QGraphicsItem.update(self)

    # @timeit
    def paint(self, painter, option, widget=None):
        for line, state in self.iter_state_line_segments():
            color = QtCore.Qt.red if state else QtCore.Qt.black
            painter.setPen(QtGui.QPen(color))
            painter.drawLine(line)
        # TODO: delete old logic states

        # TODO: stop drawing on steady state
        self._update_paint.start()
