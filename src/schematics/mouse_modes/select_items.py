#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Defines functionality when selecting items.
'''

from PySide import QtGui, QtCore

from .modes_base import GridViewMouseModeBase, mouse_mode_filtered


class SelectItemsMode(GridViewMouseModeBase):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)

    def mouse_enter(self):
        super().mouse_enter()
        self.setDragMode(QtGui.QGraphicsView.RubberBandDrag)
        self.scene().setSelectionAllowed(True)

    def mouse_leave(self):
        super().mouse_leave()
        self.setDragMode(QtGui.QGraphicsView.NoDrag)
        self.scene().setSelectionAllowed(False)

    @mouse_mode_filtered
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            for item in self.scene().selectedItems():
                self.scene().removeItem(item)
        else:
            super().keyPressEvent(event)
