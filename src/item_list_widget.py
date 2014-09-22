#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can 
# be found in the LICENSE.txt file.
#
'''
The item list view is used to show all available logic elements.
'''

from PySide import QtGui, QtCore

import schematics

class TestRect(QtGui.QGraphicsRectItem, QtGui.QGraphicsLayoutItem):
    def __init__(self, *args, **kargs):
        super(TestRect, self).__init__(*args, **kargs)
        self.setRect(0, 0, 100, 100)
        self.setPen(QtGui.QPen(QtCore.Qt.black))
        self.setBrush(QtCore.Qt.white)

class ItemListScene(schematics.GridScene):
    def __init__(self, *args, **kargs):
        super(ItemListScene, self).__init__(*args, **kargs)
        # top level widget is needed to layout all other items
        self._top_widget = QtGui.QGraphicsWidget()
        self._layout = QtGui.QGraphicsGridLayout()
        self._top_widget.setLayout(self._layout)
        self.addItem(self._top_widget)
#        self._top_widget.setGeometry(0, 0, 250, 250)
#        self.setSceneRect(0, 0, 500, 500)
        # how many cols should be visible?
        self._col_count = None
        # tuple for next inserted item: row, col
        self._next_index = 0, 0
        
        
#        layout = QtGui.QGraphicsGridLayout()
#        form = QtGui.QGraphicsWidget()
#        form.setLayout(layout)
#        self.addItem(form)
#        
#        textEdit = self.addWidget(QtGui.QTextEdit())
#        pushButton = self.addWidget(QtGui.QPushButton())
#        
#        layout.addItem(textEdit, 0, 0)
#        layout.addItem(pushButton, 0, 1)
        
    
    def get_col_count(self, cols):
        return self._col_count
    
    def set_col_count(self, cols):
        assert isinstance(cols, int) and cols > 0
        self._col_count = cols
    
    def add_item(self, item_class):
        item = self.addItem(item_class())
        row, col = self._next_index
        self._layout.addItem(item, row, col) #QtCore.Qt.AlignCenter)
        col += 1
        self._next_index = row + col // self._col_count, col % self._col_count
#        self._top_widget.setLayout(self._layout)


class ItemListView(schematics.GridView):
    def __init__(self, *args, **kargs):
        super(ItemListView, self).__init__(*args, **kargs)
        self.setScene(ItemListScene(self))
        
        # set number of cols
        self.scene().set_col_count(2)
        
        for _ in range(10):
            self.scene().add_item(TestRect)
        return
        
        import simulation_model
        for item in simulation_model.JsonMeta.get_all_json_classes():
            if issubclass(item, simulation_model.Primitive):
                self.scene().add_item(item)
    
    def update_scale(self, cols):
        width = 100
        
        self.scene().setSceneRect(0, 0, 1000, 1000)
        self.setSceneRect(0, 0, 1000, 1000)

