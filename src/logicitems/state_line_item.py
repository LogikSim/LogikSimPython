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
    _update_paint = QtCore.QTimer()
    _update_paint.setInterval(40)

    def __init__(self, parent=None):
        super().__init__(parent)

        # contains last logic states with entries (sim_time, value)
        self._logic_states = []
        self._animate_lines = True

        # start timer
        self._update_paint.start()
        self._update_paint_connected = False

    def set_animate_lines(self, on):
        """
        If on is True, this item will animate its line.

        Animation is based on logic states provided. If it is off,
        everything is drawn in with the last logic state.

        It is enabled by default.
        """
        self._animate_lines = on
        self.request_paint()

    def animate_lines(self):
        """
        Return True, if this item will animate its line.

        see set_animate_lines.
        """
        return self._animate_lines

    def set_logic_state(self, state, clock=None):
        """Set new logic state with clock information."""
        if self.scene() is not None:
            self._logic_states.append((self.scene().registry().clock(), state))
            self.request_paint()

    def get_last_logic_state(self):
        """Returns most recent logic state or False."""
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
        current_state = self.get_last_logic_state() if parent_state is None \
            else parent_state
        current_index = len(self._logic_states) - 1 if parent_index is None \
            else parent_index

        if not self._animate_lines or delay == 0 \
                or len(self._logic_states) == 0:
            yield (QtCore.QLineF(QtCore.QPointF(*origin),
                                 QtCore.QPointF(*destination)), current_state)
        else:
            start = origin
            j = is_vertical
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
        Based on the returned longest delay old logic states are discarded.

        :return: Iterator with line segments. Iterator return: longest delay
        """
        raise NotImplementedError

    def request_paint(self):
        if not self._update_paint_connected:
            self._update_paint.timeout.connect(self.do_update_paint)
            self._update_paint_connected = True

    def do_update_paint(self):
        # redraw
        self._update_paint.timeout.disconnect(self.do_update_paint)
        self._update_paint_connected = False
        QtGui.QGraphicsItem.update(self)

    def paint(self, painter, option, widget=None):
        # extract longest delay from generator
        def helper():
            nonlocal longest_delay
            longest_delay = yield from self.iter_state_line_segments()
        longest_delay = 0

        # draw line segments
        for line, state in helper():
            color = QtCore.Qt.red if state else QtCore.Qt.black
            painter.setPen(QtGui.QPen(color))
            painter.drawLine(line)

        # delete old logic states
        clock = self.scene().registry().clock()
        i = 0
        for i, (state_clock, state) in enumerate(self._logic_states):
            delta = clock - state_clock
            if delta < longest_delay:
                break
        i -= 1  # keep one more
        if i > 0:
            self._logic_states = self._logic_states[i:]

        # connect to timer, if there are still relevant states
        if self._animate_lines and len(self._logic_states) > 1 and \
                (clock - self._logic_states[-1][0]) < longest_delay:
            # self._update_paint.start()
            self.request_paint()
