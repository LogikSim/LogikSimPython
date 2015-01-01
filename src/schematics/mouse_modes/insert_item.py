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

from PySide import QtCore

from .modes_base import GridViewMouseModeBase, mouse_mode_filtered
from logicitems.itembase import ItemBase
from backend.components import And


class InsertItemMode(GridViewMouseModeBase):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        # class used to insert new items
        self._insert_item_guid = And.GUID()
        # reference to currently inserted item (used to move it
        # while the mouse button is still pressed)
        self._inserted_item = None
        self._inserted_id = None

    def mouse_enter(self):
        super().mouse_enter()

    @QtCore.Slot(ItemBase)
    def _instantiated(self, instance):
        if instance.id() != self._inserted_id:
            return

        self._inserted_item = instance

    @mouse_mode_filtered
    def mousePressEvent(self, event):
        super().mousePressEvent(event)

        # left button
        if event.button() is QtCore.Qt.LeftButton:
            item = self.scene().registry().instantiate_frontend_item(
                self._insert_item_guid)
            item.set_temporary(True)
            item.setPos(self.mapToSceneGrid(event.pos()))
            self.scene().addItem(item)
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

        # left button -> insert item
        if event.button() is QtCore.Qt.LeftButton and \
                self._inserted_item is not None:
            scene = self.scene()
            item = self._inserted_item

            # prevent item from being deleted when switching modes
            self._inserted_item = None
            item.set_temporary(False)

            def do():
                scene.addItem(item)

            def undo():
                scene.removeItem(item)

            self.scene().actions.executed(
                do, undo, "insert logic item"
            )

    def mouse_leave(self):
        super().mouse_leave()
        # cleanup InsertItem
        if self._inserted_item is not None:
            self.scene().removeItem(self._inserted_item)
            self._inserted_item = None
