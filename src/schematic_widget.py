#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can 
# be found in the LICENSE.txt file.
#
'''
Defines the schematic widged used to create and visualize the logic circuits.
'''

from PySide import QtGui, QtCore

from helper.timeit_mod import timeit
import base_graphics_framework
from actions.ActionStack import ActionStack

class SchematicScene(base_graphics_framework.BasicGridScene):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        # set scene size
        height = 100 * 1000 # golden ratio
        self.setSceneRect(0, 0, height * (1+5**0.5)/2, height)

        self.actions =  ActionStack(self)

class SchematicView(
            base_graphics_framework.SelectItemsMode, 
            base_graphics_framework.InsertItemMode,
            base_graphics_framework.InsertLineMode,
            base_graphics_framework.InsertConnectorMode, 
            base_graphics_framework.BasicGridView):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        self.setScene(SchematicScene(self))
        self.setMouseMode(base_graphics_framework.SelectItemsMode)
    
#    @timeit
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
    
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_F1:
            print('selection mode')
            self.setMouseMode(base_graphics_framework.SelectItemsMode)
        elif event.key() == QtCore.Qt.Key_F2:
            print('insert logic element')
            self.setMouseMode(base_graphics_framework.InsertItemMode)
        elif event.key() == QtCore.Qt.Key_F3:
            print('insert connector')
            self.setMouseMode(base_graphics_framework.InsertConnectorMode)
        elif event.key() == QtCore.Qt.Key_F4:
            print('insert lines')
            self.setMouseMode(base_graphics_framework.InsertLineMode)
        elif event.key() == QtCore.Qt.Key_F5:
            actions = self.scene().actions

            if actions.canUndo():
                print('undo')
                self.scene().actions.undo()
            else:
                print("can't undo")

        elif event.key() == QtCore.Qt.Key_F6:
            actions = self.scene().actions

            if actions.canRedo():
                print('redo')
                self.scene().actions.redo()
            else:
                print("can't redo")
        elif event.key() == QtCore.Qt.Key_Escape:
            self.abort_line_inserting()
        else:
            super().keyPressEvent(event)


def main():
    import sys
    app = QtGui.QApplication(sys.argv)
    view = SchematicView()
    view.show()
    app.exec_()
 
if __name__ == '__main__':
    main()
