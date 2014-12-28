#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Logic items are all items a logic behavior based on inputs and outputs.
'''

from PySide import QtGui, QtCore

from .itembase import ItemBase
from actions.move_action import MoveAction


class LogicItem(ItemBase, QtGui.QGraphicsLayoutItem):
    """
    Defines logic item base class.

    All children must implement the methods: ownBoundingRect, paint
    """
    def __init__(self, *args, **kargs):
        ItemBase.__init__(self, *args, **kargs)
        QtGui.QGraphicsLayoutItem.__init__(self, *args, **kargs)

        # self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
        self.setFlag(QtGui.QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

        # contains last valid position for self.itemChange(...)
        self._last_position = None
        # stores bounding rect
        self._bounding_rect_valid = False
        self._bounding_rect = None

    def setGeometry(self, rect):
        scene_offset = self.mapToScene(self.selectionRect().topLeft()) - \
            self.mapToScene(QtCore.QPointF(0, 0))
        self.setPos(rect.topLeft() - scene_offset)

    def sizeHint(self, which, constraint):
        return self.mapToScene(self.selectionRect()).boundingRect().size()

    def __repr__(self):
        return "<{} {} at {}>".format(
            type(self).__name__, id(self), (self.pos().x(), self.pos().y()))

    def _invalidate_bounding_rect(self):
        self.prepareGeometryChange()
        self._bounding_rect_valid = False

    def _is_current_position_valid(self):
        pass

    def ownBoundingRect(self):
        """ bounding rect of LogicItem without considering children """
        raise NotImplementedError

    def selectionRect(self):
        """
        return rect used for selection.

        By default returns own combined with child bounding rects.
        """
        return self.boundingRect().united(self.childrenBoundingRect())

    def itemChange(self, change, value):
        if self.scene() is not None:
            #
            # round position to grid point
            if change == QtGui.QGraphicsItem.ItemPositionChange:
                if self._is_current_position_valid():
                    self._last_position = self.pos()
                else:
                    self._last_position = None
                return self.scene().roundToGrid(value)
            elif change == QtGui.QGraphicsItem.ItemPositionHasChanged:
                if self._is_current_position_valid():
                    if self.isSelected():
                        self.scene().selectedItemPosChanged.emit()
                    # create undo/redo action
                    if not self.is_temporary():
                        action = MoveAction(self.scene().getUndoRedoGroupId(),
                                            self, self._last_position,
                                            self.pos())
                        self.scene().actions.push(action)
                else:
                    if self._last_position is not None:
                        self.setPos(self._last_position)

            #
            # only selectable when allowed by scene
            elif change == QtGui.QGraphicsItem.ItemSelectedChange:
                return value and self.scene().selectionAllowed()
            #
            # only movable when selected
            elif change == QtGui.QGraphicsItem.ItemSelectedHasChanged:
                self.setFlag(QtGui.QGraphicsItem.ItemIsMovable, value)
        if change in (QtGui.QGraphicsItem.ItemChildAddedChange,
                      QtGui.QGraphicsItem.ItemChildRemovedChange):
            self._invalidate_bounding_rect()
        return super().itemChange(change, value)

    def hoverMoveEvent(self, event):
        super().hoverMoveEvent(event)
        self.setCursor(QtCore.Qt.SizeAllCursor if self.isSelected() else
                       QtCore.Qt.ArrowCursor)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self.setCursor(QtCore.Qt.SizeAllCursor if self.isSelected() else
                       QtCore.Qt.ArrowCursor)

    def boundingRect(self):
        if not self._bounding_rect_valid:
            self._bounding_rect = self.ownBoundingRect()
            self._bounding_rect_valid = True
        return self._bounding_rect

    def mouseReleaseEvent(self, event):
        """
        default implementation of QGraphicsItem selects the current item
        if any mouse button is released, limit this behaviour to the
        left mouse button.
        """
        if not event.button() is QtCore.Qt.LeftButton:
            # default implementation changes selection when following is true:
            # event->scenePos() == event->buttonDownScenePos(Qt::LeftButton)
            event.setButtonDownScenePos(
                QtCore.Qt.LeftButton, event.scenePos() + QtCore.QPointF(1, 1))
        return QtGui.QGraphicsItem.mouseReleaseEvent(self, event)
