#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Defines functionality when triggering edges on input connectors.
'''

from PySide import QtCore

from .modes_base import GridViewMouseModeBase, mouse_mode_filtered
from logicitems import ConnectorItem


class TriggerEdgeMode(GridViewMouseModeBase):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)

        self._mouse_press_pos = None

    @mouse_mode_filtered
    def mousePressEvent(self, event):
        super().mousePressEvent(event)

        # left button
        if event.button() is QtCore.Qt.LeftButton:
            self._mouse_press_pos = self.mapToSceneGrid(event.pos())

    @mouse_mode_filtered
    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)

        # left button
        if event.button() is QtCore.Qt.LeftButton:
            self._mouse_press_pos = self.mapToSceneGrid(event.pos())

    @mouse_mode_filtered
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

        # left button -> trigger edge on input
        if event.button() is QtCore.Qt.LeftButton:
            gpos = self.mapToSceneGrid(event.pos())
            if self._mouse_press_pos == gpos:
                for item in self.scene().items(gpos):
                    if isinstance(item, ConnectorItem) and \
                            item.is_input():
                        item.toggle()
            self._mouse_press_pos = None

    def mouse_leave(self):
        super().mouse_leave()
        # cleanup
        self._mouse_press_pos = None
