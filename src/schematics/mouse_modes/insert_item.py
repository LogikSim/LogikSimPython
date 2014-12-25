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

    def mouse_enter(self):
        super().mouse_enter()

    @QtCore.Slot(int, ItemBase)
    def _instantiated(self, _, instance):
        if instance.pos() != self._insertion_pos:
            # TODO: Consider a stronger check
            return

        self._inserted_item = instance

    def insert_item(self, gpos):
        interface = self.scene().get_interface()
        registry = self.scene().get_registry()

        # FIXME: This function isn't robust nor pretty.

        self._inserted_item = None
        self._insertion_pos = gpos

        registry.instantiated.connect(self._instantiated)
        interface.create_element(guid=self._insert_item_guid,
                                 additional_metadata={'x': gpos.x(),
                                                      'y': gpos.y()})

        while not self._inserted_item:
            QtCore.QCoreApplication.processEvents()

        registry.instantiated.disconnect(self._instantiated)

        self.scene().addItem(self._inserted_item)

        return self._inserted_item

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
        if event.button() is QtCore.Qt.LeftButton and \
                self._inserted_item is not None:
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
