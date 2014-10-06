#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can 
# be found in the LICENSE.txt file.
#
'''
Define the main window of the LogikSim GUI.
'''

from PySide import QtGui, QtCore, QtUiTools
import logicitems

#import item_list_widget
import schematics
from ui_main_window import Ui_MainWindow

class MainWindow(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.setupUi(self)

        #FIXME: Only a test setup, replace it by proper circuit instance handling
        self._view = schematics.EditSchematicView(self)
        self.tab_widget.addTab(self._view, self.tr("New circuit"))
        self.tab_widget.tabBar().hide() # For now we only have one so hide
        self.tool_bar.hide() # For now we have no tools

        scene = self._view.scene()
        self.add_items(scene)

        actions = scene.actions
        #TODO: Wrap QUndoStack::createRedo(Undo)Action and use it instead
        self.action_stack_view.setModel(actions)
        self.action_undo.triggered.connect(actions.undo)
        actions.canUndoChanged.connect(self.action_undo.setEnabled)
        self.action_redo.triggered.connect(actions.redo)
        actions.canRedoChanged.connect(self.action_redo.setEnabled)

        self.menu_view.addAction(self.history_dock_widget.toggleViewAction())



    def showEvent(self, event):
        #FIXME: Temporary workaround, should be part of circuit instance management
        self._view.fitInView(self._view.scene().itemsBoundingRect().adjusted(-2000,-2000,2000,2000), QtCore.Qt.KeepAspectRatio)

    def add_items(self, scene):
        #TODO: Get rid of this and replace with proper toolbox implementation
        def add_simple_item(pos):
            item = logicitems.LogicItem()
            for i in range(1, 6):
                con1 = logicitems.ConnectorItem(
                    QtCore.QLineF(0, 100 * i, -100, 100 * i))
                con1.setParentItem(item)
                con2 = logicitems.ConnectorItem(
                    QtCore.QLineF(300, 100 * i, 400, 100 * i))
                con2.setParentItem(item)
            item.setPos(pos)
            scene.addItem(item)

        add_simple_item(QtCore.QPointF(81000, 50500))
        add_simple_item(QtCore.QPointF(82000, 50500))

        for text, pos in [("Modes:", (80000, 49000)),
                          ("F1 - Selection", (80000, 49200)),
                          ("F2 - Insert Logic Items", (80000, 49400)),
                          ("F3 - Insert Connectors", (80000, 49600)),
                          ("F4 - Insert Lines", (80000, 49800)),
                          ("F5 - Undo", (80000, 50000)),
                          ("F6 - Redo", (80000, 50200))]:
            item = QtGui.QGraphicsTextItem(text)
            item.setPos(*pos)
            item.setDefaultTextColor(QtCore.Qt.red)
            #item.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
            font = item.font()
            font.setPointSizeF(100)
            item.setFont(font)
            scene.addItem(item)

    
    def view(self):
        return self._view
