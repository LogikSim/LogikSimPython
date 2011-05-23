#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Apr 26, 2011

@author: Christian
'''

from PySide import QtGui

import schematic_widget

class MainWindow(QtGui.QWidget):
    def __init__(self, *args, **kargs):
        QtGui.QWidget.__init__(self, *args, **kargs)
        # main layout
        self._main_layout = QtGui.QBoxLayout(QtGui.QBoxLayout.LeftToRight, self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._main_layout)
        # schematic view
        self._view = schematic_widget.SchematicView(self)
        self._main_layout.addWidget(self._view, 1)
        # set frame size
        #self.resize(400, 400)
    
    def view(self):
        return self._view
