#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Copyright 2014 The LogikSim Authors. All rights reserved.
Use of this source code is governed by the GNU GPL license that can 
be found in the LICENSE.txt file.
'''

from PySide import QtGui

import item_list_widget
import schematic_widget
import symbol_widget

class MainWindow(QtGui.QWidget):
    def __init__(self, *args, **kargs):
        QtGui.QWidget.__init__(self, *args, **kargs)
        # main layout
        self._main_layout = QtGui.QBoxLayout(QtGui.QBoxLayout.LeftToRight, self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._main_layout)
        # item list view
 #       self._list = item_list_widget.ItemListView(self)
 #       self._main_layout.addWidget(self._list, 7)
        # schematic view
        self._view = schematic_widget.SchematicView(self)
        self._main_layout.addWidget(self._view, 2)
        # symbol view
#        self._symbol = symbol_widget.SymbolView(self)
#        self._main_layout.addWidget(self._symbol, 2)
        # set frame size
        #self.resize(400, 400)
    
    def view(self):
        return self._view
