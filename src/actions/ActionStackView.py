#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
from PySide import QtGui, QtCore

class ActionStackView(QtGui.QListView):
    def __init__(self, parent = None):
        super().__init__(parent)

    def setModel(self, model):
        model.currentModelIndexChanged.connect(self.currentModelIndexChanged)
        super().setModel(model)

    @QtCore.Slot(QtCore.QModelIndex)
    def currentModelIndexChanged(self, modelIndex):
        if modelIndex != self.currentIndex():
            self.setCurrentIndex(modelIndex)

    def currentChanged(self, current, previous):
        """
        React to user changing current selected item
        """
        if current != previous:
            self.model().undoRedoToIndex(current)

        super().currentChanged(current, previous)