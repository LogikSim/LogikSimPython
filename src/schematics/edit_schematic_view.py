#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can 
# be found in the LICENSE.txt file.
#
'''
Defines the schematic view used to create and visualize logic circuits.
'''

from . import mouse_modes
from . import grid_scene

from PySide import QtCore


class EditSchematicView(
            mouse_modes.SelectItemsMode, 
            mouse_modes.InsertItemMode,
            mouse_modes.InsertLineMode,
            mouse_modes.InsertConnectorMode):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        self.setScene(grid_scene.GridScene(self))
        self.setMouseMode(mouse_modes.SelectItemsMode)
        
        self.scene().actions.aboutToUndo.connect(self.onAboutToUndoRedo)
        self.scene().actions.aboutToRedo.connect(self.onAboutToUndoRedo)

    @QtCore.Slot()
    def onAboutToUndoRedo(self):
        self.abort_line_inserting()
    
#    @timeit
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.abort_line_inserting()
        else:
            super().keyPressEvent(event)

