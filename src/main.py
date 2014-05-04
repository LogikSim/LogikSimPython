#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Copyright 2014 The LogikSim Authors. All rights reserved.
Use of this source code is governed by the GNU GPL license that can 
be found in the LICENSE.txt file.
'''

import sys

from PySide import QtGui, QtCore

import main_window
import logic_item
import symbols

def add_items(scene):
    def add_simple_item(pos):
        item = logic_item.LogicItem()
        for i in range(1, 6):
            con1 = logic_item.ConnectorItem(
                    QtCore.QLineF(0, 100 * i, -100, 100 * i))
            con1.setParentItem(item)
            con2 = logic_item.ConnectorItem(
                    QtCore.QLineF(300, 100 * i, 400, 100 * i))
            con2.setParentItem(item)
        item.setPos(pos)
        scene.addItem(item)
    
    add_simple_item(QtCore.QPointF(81000, 50500))
    add_simple_item(QtCore.QPointF(82000, 50500))
    
    item = QtGui.QGraphicsTextItem("Text Item")
    item.setPos(80000, 50000)
    item.setDefaultTextColor(QtCore.Qt.red)
    item.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
    font = item.font()
    font.setPointSizeF(100)
    item.setFont(font)
    scene.addItem(item)
    

def main():
    symbols.load_all_symbols()
    
    app = QtGui.QApplication(sys.argv)
    frame = main_window.MainWindow()
    frame.show()
    add_items(frame.view().scene())
    app.exec_()

if __name__ == '__main__':
    main()
