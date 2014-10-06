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

from PySide import QtGui, QtCore
from docks.history_dock_widget import HistoryDockWidget

#import item_list_widget
import schematics

class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent = None):
        super().__init__(parent)
        # schematic view
        self._view = schematics.EditSchematicView(self)
        self.setCentralWidget(self._view)

        # item list view
        #        self._list = item_list_widget.ItemListView(self)
        #        self._main_layout.addWidget(self._list, 7)
        # symbol view
#        self._symbol = schematics.EditSymbolView(self)
#        self._main_layout.addWidget(self._symbol, 2)
        # set frame size
        #self.resize(400, 400)

        self._history_dock = HistoryDockWidget(self._view.scene().actions, self)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self._history_dock)
        self._history_dock.setFloating(True)
    
    def view(self):
        return self._view
