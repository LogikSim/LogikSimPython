#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Insertable items are items that are backed by a backend instance.
'''

from PySide import QtGui, QtCore

from .itembase import ItemBase
from actions.move_action import MoveAction


class InsertableRegistry(type(ItemBase)):
    """Keeps track of all derived classes of InsertableItem."""
    _insertable_classes = []

    def __init__(self, *args, **kargs):
        type(ItemBase).__init__(self, *args, **kargs)

        # register types that implement GUI_GUID
        try:
            self.GUI_GUID()
        except NotImplementedError:
            pass
        else:
            InsertableRegistry._insertable_classes.append(self)

    @classmethod
    def get_insertable_classes(self):
        """Returns all insertable classes with defined GUI_GUID."""
        return InsertableRegistry._insertable_classes


class InsertableItem(ItemBase, metaclass=InsertableRegistry):
    """
    Insertable items have a position and are backed by a backend instance.
    """
    def __init__(self, parent=None, metadata={}):
        super().__init__(parent)

        # self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
        self.setFlag(QtGui.QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

        # set position
        self.setX(metadata.get('x', 0))
        self.setY(metadata.get('y', 0))

        self._cached_metadata = metadata
        self._registered_scene = None

        # contains last valid position
        self._last_position = None

    def selectionRect(self):
        """Return rect used for selection."""
        raise NotImplementedError

    @classmethod
    def GUI_GUID(cls):
        """Return GUI_GUID of this class."""
        raise NotImplementedError

    def GUID(self):
        """Return GUID of this instance."""
        return self._cached_metadata['GUID']

    def id(self):
        """Return id, used to communicate with backend."""
        return self._cached_metadata['id']

    def name(self):
        """Return name."""
        return self._cached_metadata.get('name', '<name>')

    def metadata(self):
        """Return the complete metadata."""
        return self._cached_metadata

    def update(self, metadata):
        self._cached_metadata.update(metadata)

        x = metadata.get('x')
        if x is not None and x != self.x():
            self.setX(x)

        y = metadata.get('y')
        if y is not None and y != self.y():
            self.setY(y)

    def set_temporary(self, temp):
        """
        Overrides set_temporary.

        Temporary insertable items have no instance in the backend.
        """
        ItemBase.set_temporary(self, temp)

        if temp:
            self._unregister()
        else:
            self._register()

    def _unregister(self):
        """Delete backend instance."""
        if self._registered_scene is not None:
            self._registered_scene.interface().delete_element(self.id())
            self._registered_scene = None

    def _register(self):
        """Create new backend instance."""
        scene = self.scene()
        if scene is not None and not self.is_temporary():
            scene.interface().create_element(
                guid=self.GUID(),
                parent=None,
                additional_metadata=self.metadata())
            self._registered_scene = scene

    def _on_item_position_has_changed(self, new_pos):
        """Notification from scene that position has changed."""
        if new_pos == self._last_position:
            return

        # notify selection change
        if self.isSelected():
            self.scene().selectedItemPosChanged.emit()

        if not self.is_temporary():
            # create undo/redo action
            action = MoveAction(self.scene().getUndoRedoGroupId(),
                                self, self._last_position, new_pos)
            self.scene().actions.push(action)
            # notify backend
            # self.scene().interface().update_element(
            #     self.id(), {'x': new_pos.x(), 'y': new_pos.y()})

    def itemChange(self, change, value):
        # re-register on scene change
        if change is QtGui.QGraphicsItem.ItemSceneHasChanged:
            self._unregister()
            self._register()

        if self.scene() is not None:
            # round position to grid point
            if change == QtGui.QGraphicsItem.ItemPositionChange:
                self._last_position = self.pos()
                return self.scene().roundToGrid(value)
            # handle position changes
            elif change == QtGui.QGraphicsItem.ItemPositionHasChanged:
                self._on_item_position_has_changed(value)
            # only selectable when allowed by scene
            elif change == QtGui.QGraphicsItem.ItemSelectedChange:
                return value and self.scene().selectionAllowed()
            # only movable when selected
            elif change == QtGui.QGraphicsItem.ItemSelectedHasChanged:
                self.setFlag(QtGui.QGraphicsItem.ItemIsMovable, value)

        return super().itemChange(change, value)

    def hoverMoveEvent(self, event):
        super().hoverMoveEvent(event)
        self.setCursor(QtCore.Qt.SizeAllCursor if self.isSelected() else
                       QtCore.Qt.ArrowCursor)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self.setCursor(QtCore.Qt.SizeAllCursor if self.isSelected() else
                       QtCore.Qt.ArrowCursor)

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
