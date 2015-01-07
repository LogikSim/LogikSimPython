#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Implements interactive view for GridScene supporting dragging and zooming.

It can further support additional mouse_modes.
'''

import json

from PySide import QtGui, QtCore

from . import grid_view


class InteractiveGridView(grid_view.GridView):
    """
    The basic view of all mouse modes.

    The class itself implements:
        - zooming scene with the mouse
        - dragging and scrolling scene with mouse
    """
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)

        # used to store last position while dragging the view with the
        # middle mouse button
        self._mouse_mid_last_pos = None

        self.setTransformationAnchor(QtGui.QGraphicsView.AnchorUnderMouse)
        # self.setResizeAnchor(QtGui.QGraphicsView.AnchorViewCenter)
        # self.setOptimizationFlags(QtGui.QGraphicsView.DontSavePainterState)

        self.setAcceptDrops(True)
        self._drop_items = None  # list of (items, initial pos)
        self._drag_pos = None  # as QPointF in scene pos

        self.scale(0.12, 0.12)

    def mapToSceneGrid(self, pos, y=None):
        """Rounds mouse position to scene grid."""
        if y is not None:
            pos = QtCore.QPoint(pos, y)
        return self.scene().roundToGrid(self.mapToScene(pos))

    def wheelEvent(self, event):
        super().wheelEvent(event)
        # TODO: zoom with STRG and add modifier to scroll horizontally

        if event.orientation() is QtCore.Qt.Horizontal or \
                event.modifiers() != QtCore.Qt.NoModifier:
            # scroll
            fake_evt = QtGui.QWheelEvent(
                event.pos(), event.globalPos(), event.delta(), event.buttons(),
                event.modifiers() & ~(QtCore.Qt.ControlModifier),
                event.orientation())
            QtGui.QAbstractScrollArea.wheelEvent(self, fake_evt)
        else:
            # scale
            factor = 1.1 ** (event.delta() / 60)
            new_scale = self.getAbsoluteScale() * factor
            if 0.0075 < new_scale < 5:
                self.scale(factor, factor)

        # generate mouse move event
        # workaround to update AnchorUnderMouse
        move_event = QtGui.QMouseEvent(QtCore.QEvent.MouseMove, event.pos(),
                                       event.globalPos(), QtCore.Qt.NoButton,
                                       event.buttons(),
                                       event.modifiers())
        self.mouseMoveEvent(move_event)

    # TODO: Move selection with arrow keys

    def mousePressEvent(self, event):
        super().mousePressEvent(event)

        # drag mode
        if event.button() is QtCore.Qt.MidButton or \
                event.button() is QtCore.Qt.MiddleButton:
            self._mouse_mid_last_pos = self.mapToScene(event.pos())
            self.setCursor(QtCore.Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

        # mid mouse pressed -> drag grid
        if event.buttons() & QtCore.Qt.MidButton or \
                event.buttons() & QtCore.Qt.MiddleButton:
            curr_pos = self.mapToScene(event.pos())
            delta = curr_pos - self._mouse_mid_last_pos
            top_left = QtCore.QPointF(self.horizontalScrollBar().value(),
                                      self.verticalScrollBar().value())
            desired_slider_pos = top_left - delta * self.getAbsoluteScale()
            self.horizontalScrollBar().setSliderPosition(
                desired_slider_pos.x())
            self.verticalScrollBar().setSliderPosition(desired_slider_pos.y())

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

        if event.button() is QtCore.Qt.MidButton or \
                event.button() is QtCore.Qt.MiddleButton:
            self._mouse_mid_last_pos = None
            self.unsetCursor()

    def _move_dropped_items_to(self, view_pos):
        for item, item_drop_pos in self._drop_items:
            new_pos = self.scene().roundToGrid(
                item_drop_pos + self.mapToScene(view_pos) - self._drag_pos)
            item.setPos(new_pos, notify_surrounding=True)

    def dragEnterEvent(self, event):
        if not self.scene().insertItemAllowed():
            return

        if event.mimeData().hasFormat('application/x-components'):
            self.scene().clearSelection()

            # geta data
            data = json.loads(str(event.mimeData().data(
                'application/x-components')))

            # calculate translation pos
            self._drag_pos = QtCore.QPointF(*data['drag_pos'])

            # create item
            self._drop_items = []
            for item_metadata in data['items']:
                item = self.scene().registry().instantiate_frontend_item(
                    backend_guid=item_metadata['GUID'],
                    additional_metadata=item_metadata)
                item.set_temporary(True)
                item.setZValue(0.5)
                self.scene().addItem(item)
                item.setSelected(True)
                self._drop_items.append((item, item.pos()))

            # move items
            self._move_dropped_items_to(event.pos())

            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        # move items
        self._move_dropped_items_to(event.pos())

        event.acceptProposedAction()

    def _abort_drop(self):
        # delete item
        for item, _ in self._drop_items:
            item.setSelected(False)
            self.scene().removeItem(item)
        self._drop_items = None

    def dragLeaveEvent(self, event):
        self._abort_drop()

    def dropEvent(self, event):
        if not self.scene().insertItemAllowed():
            self._abort_drop()
            return

        scene = self.scene()
        items = self._drop_items

        # move to final position
        self._move_dropped_items_to(event.pos())

        # mark as persistent
        for item, _ in self._drop_items:
            item.set_temporary(False)
            item.setZValue(0)
        self._drop_items = None

        # TODO: create undo action
        def do():
            for item, _ in items:
                scene.addItem(item)

        def undo():
            for item, _ in items:
                scene.removeItem(item)

        self.scene().actions.executed(
            do, undo, "Insert {} item".format(items[0][0].name())
        )

        event.acceptProposedAction()

    @QtCore.Slot()
    def cut(self):
        """Copies the selected items to the clipboard and deletes them."""
        self.copy()
        self.delete()

    @QtCore.Slot()
    def paste(self):
        """
        Pastes items from the clipboard into the scene.

        The inserted position is the current cursor position.
        """
        clipboard = QtGui.QApplication.clipboard()

        # TODO: move items?

        data = json.loads(clipboard.text())
        paste_items = []
        for item_metadata in data.get('items', []):
            item = self.scene().registry().instantiate_frontend_item(
                backend_guid=item_metadata['GUID'],
                additional_metadata=item_metadata)
            self.scene().addItem(item)
            item.setSelected(True)
            paste_items.append(item)

        # undo creation
        scene = self.scene()

        def do():
            for item in paste_items:
                scene.addItem(item)

        def undo():
            for item in paste_items:
                item.setSelected(False)
                scene.removeItem(item)

        self.scene().actions.executed(
            do, undo, "pasted logic item"
        )

    @QtCore.Slot()
    def copy(self):
        """Copies any selected items to the clipboard."""
        clipboard = QtGui.QApplication.clipboard()

        sel_items = self.scene().selectedItems()
        data = {'items': [item.metadata() for item in sel_items]}
        # TODO: use mime type 'application/x-components'
        # TODO: store mime type in variable
        clipboard.setText(json.dumps(data))

    @QtCore.Slot()
    def delete(self):
        """Delete all selected items."""
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

    @QtCore.Slot()
    def selectAll(self):
        """Select all items in the scene."""
        for item in self.scene().items():
            item.setSelected(True)
