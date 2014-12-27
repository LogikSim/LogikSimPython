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

    @mouse_mode_filtered
    def mousePressEvent(self, event):
        super().mousePressEvent(event)

    @mouse_mode_filtered
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

    @mouse_mode_filtered
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            self._remove_selected_items()
        else:
            super().keyPressEvent(event)

    def _remove_selected_items(self):
        sel_items = list(self.scene().selectedItems())
        scene = self.scene()

        # selection should not be restored
        for item in sel_items:
            item.setSelected(False)

        def do():
            for item in sel_items:
                scene.removeItem(item)

        def undo():
            for item in sel_items:
                scene.addItem(item)

        self.scene().actions.execute(
            do, undo, "remove logic item"
        )

    def mouse_enter(self):
        super().mouse_enter()
        self.setDragMode(QtGui.QGraphicsView.RubberBandDrag)
        self.scene().setSelectionAllowed(True)

    def mouse_leave(self):
        super().mouse_leave()
        self.setDragMode(QtGui.QGraphicsView.NoDrag)
        self.scene().setSelectionAllowed(False)
