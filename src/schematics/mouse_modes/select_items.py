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

from PySide import QtGui

from .modes_base import GridViewMouseModeBase


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
