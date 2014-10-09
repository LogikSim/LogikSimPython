#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can 
# be found in the LICENSE.txt file.
#
'''
Defines functionality when inserting logic items.
'''

from .modes_base import GridViewMouseModeBase, mouse_mode_filtered
import logicitems

from PySide import QtCore


class InsertItemMode(GridViewMouseModeBase):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        # class used to insert new items
        self._insert_item_class = logicitems.LogicItem
        # reference to currently inserted item (used to move it 
        # while the mouse button is still pressed)
        self._inserted_item = None
    
    def mouse_enter(self):
        super().mouse_enter()

    def insert_item(self, gpos):
        item = self._insert_item_class()
        item.setPos(gpos)
        self.scene().addItem(item)

        return item

    @mouse_mode_filtered
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        
        # left button
        if event.button() is QtCore.Qt.LeftButton:
            gpos = self.mapToSceneGrid(event.pos())
            item = self.insert_item(gpos)
            self._inserted_item = item
    
    @mouse_mode_filtered
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        
        # left button
        if event.buttons() & QtCore.Qt.LeftButton:
            gpos = self.mapToSceneGrid(event.pos())
            # move new item
            if self._inserted_item is not None:
                self._inserted_item.setPos(gpos)
    
    @mouse_mode_filtered
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        
        # left button
        if event.button() is QtCore.Qt.LeftButton and self._inserted_item is not None:
            # Add undo/redo action
            scene = self.scene()
            gpos = self._inserted_item.pos()
            item = self._inserted_item

            def do():
                nonlocal item
                item = self.insert_item(gpos)

            def undo():
                nonlocal item
                scene.removeItem(item)

            self.scene().actions.executed(
                do, undo, "insert logic item"
            )

            # prevent item from being deleted when switching modes
            self._inserted_item = None
    
    def mouse_leave(self):
        super().mouse_leave()
        # cleanup InsertItem
        if self._inserted_item is not None:
            self.scene().removeItem(self._inserted_item)
            self._inserted_item = None

