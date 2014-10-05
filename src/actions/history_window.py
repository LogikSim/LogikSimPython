#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
from PySide import QtGui, QtCore
from actions.action_stack_view import ActionStackView

class HistoryWindow(QtGui.QWidget):
    def __init__(self, action_stack_model, parent = None):
        super().__init__(parent, QtCore.Qt.Tool)

        layout = QtGui.QVBoxLayout()
        history = ActionStackView(self)
        history.setModel(action_stack_model)
        layout.addWidget(history)
        self.setLayout(layout)

        self.setWindowTitle(self.tr("History"))
