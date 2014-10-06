#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
from PySide import QtGui, QtCore
from actions.history_window import HistoryWindow

class HistoryDockWidget(QtGui.QDockWidget):
    def __init__(self, action_stack_model, parent = None):
        super().__init__(parent)

        self._history_widget = HistoryWindow(action_stack_model, self)
        self.setWidget(self._history_widget)

        self.setWindowTitle(self._history_widget.windowTitle())
