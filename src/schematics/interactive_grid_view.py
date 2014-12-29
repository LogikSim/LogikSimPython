#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
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
        self._drop_item = None

        self.scale(0.12, 0.12)

    def mapToSceneGrid(self, pos, y=None):
        """Rounds mouse position to scene grid."""
        if y is not None:
            pos = QtCore.QPoint(pos, y)
        return self.scene().roundToGrid(self.mapToScene(pos))

    def wheelEvent(self, event):
        super().wheelEvent(event)

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

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat('application/x-components'):
            self.scene().clearSelection()

            # create item
            metadata = json.loads(str(event.mimeData().data(
                'application/x-components')))


            # delete positions in metadata
            try:
                del metadata['x']
            except KeyError:
                pass
            try:
                del metadata['y']
            except KeyError:
                pass

            # create item
            item = self.scene().registry().instantiate_frontend_item(
                backend_guid=metadata['GUID'],
                additional_metadata=metadata)
            item.set_temporary(True)
            item.setPos(self.mapToSceneGrid(event.pos()))
            self.scene().addItem(item)
            self._drop_item = item

            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        # move item
        gpos = self.mapToSceneGrid(event.pos())
        self._drop_item.setPos(gpos)

        event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        # delete item
        self.scene().removeItem(self._drop_item)
        self._drop_item = None

    def dropEvent(self, event):
        scene = self.scene()
        item = self._drop_item

        # mark as persistent
        self._drop_item.set_temporary(False)
        self._drop_item = None

        # create UndoRedo action
        def do():
            scene.addItem(item)

        def undo():
            scene.removeItem(item)

        self.scene().actions.executed(
            do, undo, "Insert {} item".format(item.name())
        )

        event.acceptProposedAction()
