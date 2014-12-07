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


class LogicItem(ItemBase):
    """
    Defines logic item base class.
    
    All children must implement the methods: ownBoundingRect, paint
    """
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        # self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
        self.setFlag(QtGui.QGraphicsItem.ItemSendsGeometryChanges)

        # contains last valid position for self.itemChange(...)
        self._last_position = None
        # stores bounding rect
        self._bounding_rect_valid = False
        self._bounding_rect = None

    def _invalidate_bounding_rect(self):
        self.prepareGeometryChange()
        self._bounding_rect_valid = False

    def _is_current_position_valid(self):
        origin = self.mapToScene(QtCore.QPointF(0, 0))
        bound_rect = self.boundingRect().translated(origin)
        return self.scene().sceneRect().contains(bound_rect)

    def ownBoundingRect(self):
        """ bounding rect of LogicItem without considering childs """
        raise NotImplementedError

    def itemChange(self, change, value):
        if self.scene() is not None:
            #
            # round position to grid point
            if change == QtGui.QGraphicsItem.ItemPositionChange:
                self._last_position = self.pos()
                return self.scene().roundToGrid(value)
            elif change == QtGui.QGraphicsItem.ItemPositionHasChanged:
                if not self._is_current_position_valid():
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

    def boundingRect(self):
        if not self._bounding_rect_valid:
            self._bounding_rect = self.ownBoundingRect().adjusted(-25, -25, 25, 25)
            #self._bounding_rect = self.ownBoundingRect().united(
            #    self.childrenBoundingRect()).adjusted(-25, -25, 25, 25)
            self._bounding_rect_valid = True
        return self._bounding_rect

    def paint(self, painter, options, widget):
        """
        When overwriting this function, call this partent at the end.
        """
        # item selection box
        if options.state & QtGui.QStyle.State_Selected:
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.setPen(QtCore.Qt.white)
            painter.drawRect(self.boundingRect())
            painter.setPen(QtGui.QPen(QtGui.QColor(40, 125, 210), 0,
                                      QtCore.Qt.DashLine))
            painter.drawRect(self.boundingRect())

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
