#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Defines functionality when selecting items.
'''

import json

from PySide import QtGui, QtCore

from .modes_base import GridViewMouseModeBase, mouse_mode_filtered


class SelectItemsMode(GridViewMouseModeBase):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)

        self._undo_group_scene = None
        self._drag_start_pos = None

    def mouse_enter(self):
        super().mouse_enter()
        self.setDragMode(QtGui.QGraphicsView.RubberBandDrag)
        self.scene().setSelectionAllowed(True)

    def mouse_leave(self):
        super().mouse_leave()

        self.setDragMode(QtGui.QGraphicsView.NoDrag)
        self.scene().setSelectionAllowed(False)

        if self._undo_group_scene is not None:
            self._undo_group_scene.endUndoRedoGroup()
            self._undo_group_scene = None

    def _mask_drag_mode(self, func, mouse_event):
        """
        disables rubber band mode when the left mouse button is not pressed,
        then calls func(mouse_event)
        """
        drag_mode = self.dragMode()
        try:
            if drag_mode is QtGui.QGraphicsView.RubberBandDrag and \
                    not mouse_event.button() & QtCore.Qt.LeftButton:
                # disable rubber band drag
                self.setDragMode(QtGui.QGraphicsView.NoDrag)
            return func(mouse_event)
        finally:
            # restore old drag mode
            self.setDragMode(drag_mode)

    @mouse_mode_filtered
    def mousePressEvent(self, event):
        # call parent with masked drag mode
        self._mask_drag_mode(super().mousePressEvent, event)

        if event.button() == QtCore.Qt.LeftButton:
            self._undo_group_scene = self.scene()
            self._undo_group_scene.beginUndoGroup()

            self._drag_start_pos = event.pos()

    @mouse_mode_filtered
    def mouseMoveEvent(self, event):
        # TODO: merge code with the one in library_view

        is_draged = False

        if event.buttons() & QtCore.Qt.LeftButton and \
                (event.pos() - self._drag_start_pos).manhattanLength() >= \
                QtGui.QApplication.startDragDistance():

            # get selected items & start drag&drop
            gpos = self.mapToScene(self._drag_start_pos)
            # TODO: create method instead of accessing _selection_item
            gpos_items = self.scene().items(gpos)
            sel_items = self.scene().selectedItems()
            if len(sel_items) > 0 and \
                    self.scene()._selection_item in gpos_items:

                drag_pos = self.mapToScene(self._drag_start_pos)
                data = {'drag_pos': drag_pos.toTuple(),
                        'items': [item.metadata() for item in sel_items]}

                mimeData = QtCore.QMimeData()
                mimeData.setData('application/x-components',
                                 json.dumps(data))

                drag = QtGui.QDrag(self)
                drag.setMimeData(mimeData)

                # set items temporary
                for item in sel_items:
                    item.set_temporary(True)


                drop_action = drag.exec_(QtCore.Qt.CopyAction |
                                         QtCore.Qt.MoveAction)

                if drop_action == QtCore.Qt.MoveAction:
                    # delete all items
                    for item in sel_items:
                        self.scene().removeItem(item)
                    is_draged = True

                if drop_action == QtCore.Qt.CopyAction:
                    # unset temporary
                    for item in sel_items:
                        item.set_temporary(False)
                    is_draged = True

                if is_draged:
                    # TODO: refactor
                    self._undo_group_scene.endUndoGroup()
                    self._undo_group_scene = None
                    self._drag_start_pos = None

        if not is_draged:
            super().mouseMoveEvent(event)

    @mouse_mode_filtered
    def mouseDoubleClickEvent(self, event):
        self.mousePressEvent(event)

    @mouse_mode_filtered
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

        if event.button() == QtCore.Qt.LeftButton and \
                self._undo_group_scene is not None:
            self._undo_group_scene.endUndoGroup()
            self._undo_group_scene = None

    @mouse_mode_filtered
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            self._remove_selected_items()
        else:
            super().keyPressEvent(event)

    def _remove_selected_items(self):
        sel_items = list(self.scene().selectedItems())
        scene = self.scene()

        # selection should not be restored
        for item in sel_items:
            item.setSelected(False)

        def do():
            for item in sel_items:
                scene.removeItem(item)

        def undo():
            for item in sel_items:
                scene.addItem(item)

        self.scene().actions.execute(
            do, undo, "remove logic item"
        )
