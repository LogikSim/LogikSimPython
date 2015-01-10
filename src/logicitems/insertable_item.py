#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Insertable items are backed by a backend instance.

They also support undo action creation.
'''

import contextlib
from logging import getLogger

from PySide import QtGui, QtCore

from .itembase import ItemBase
from actions.move_action import MoveAction


class InsertableRegistry(type(ItemBase)):
    """Keeps track of all derived types of InsertableItem."""
    _insertable_types = []

    def __init__(self, *args, **kargs):
        type(ItemBase).__init__(self, *args, **kargs)

        # register types that implement GUI_GUID
        try:
            self.GUI_GUID()
        except NotImplementedError:
            pass
        else:
            InsertableRegistry._insertable_types.append(self)

    @classmethod
    def get_insertable_types(self):
        """Returns all insertable types with valid GUI_GUID."""
        return InsertableRegistry._insertable_types


@contextlib.contextmanager
def disabled_undo(insertable_item):
    """Put insertable item in context where it creates no undo actions."""
    old_state = insertable_item.item_creates_undo_actions()
    insertable_item.set_item_creates_undo_actions(False)
    try:
        yield
    finally:
        insertable_item.set_item_creates_undo_actions(old_state)


class InsertableItem(ItemBase, metaclass=InsertableRegistry):
    """
    Insertable items have a position and are backed by a backend instance.

    They also support undo action creation.
    """

    _position_invalid_color_line = QtGui.QColor(255, 0, 0, 0)
    _position_invalid_color_fill = QtGui.QColor(255, 0, 0, 150)
    _position_invalid_opacity = 0.6
    _position_invalid_zvalue_increase = 5

    class ItemRegistrationChange:
        """
        InsertableItem.itemChange() notification

        The item is being registered / unregistered in the backend
        """

    class ItemRegistrationHasChanged:
        """
        InsertableItem.itemChange() notification

        The item has been registered / unregistered in the backend
        """

    class ItemPositionValidHasChanged:
        """
        InsertableItem.itemChange() notification

        The item position has become valid / invalid.
        """

    def __init__(self, parent, metadata):
        super().__init__(parent)
        metadata.setdefault('x', 0)
        metadata.setdefault('y', 0)

        self.log = getLogger(type(self).__name__)

        # self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
        self.setFlag(QtGui.QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.setZValue(self.default_zvalue())

        self._cached_metadata = {}
        self._registered_scene = None

        # contains last valid position
        self._last_position = None
        # set during item changes of a metadata update
        self._in_metadata_update = False
        # is item creating undo actions
        self._item_creates_undo_actions = True
        # additional items to notify surrounding change when scene is changing
        self._additional_notify_items = None
        # true if position is valid
        self._is_position_valid = None

        self.update_frontend(metadata)

    def default_zvalue(self):
        """Return default z-value for this component."""
        return 0

    def calculate_is_position_valid(self):
        """Calculate if the current position is valid and return result"""
        raise NotImplementedError

    def _invalidate_position_is_valid(self):
        """Invalidate and recompute position valid state."""
        is_valid = self.calculate_is_position_valid()
        if is_valid != self._is_position_valid:
            self._is_position_valid = is_valid
            self.setOpacity(1 if is_valid else self._position_invalid_opacity)
            self.setZValue(self.default_zvalue() + (0 if is_valid else
                           self._position_invalid_zvalue_increase))
            self.itemChange(InsertableItem.ItemPositionValidHasChanged,
                            is_valid)

    def is_position_valid(self):
        """Returns True, if position is valid."""
        return self._is_position_valid

    def register_change_during_inactivity(self):
        """Call this function on all changes during inactivity"""
        if self.scene() is not None:
            self.scene().register_change_during_inactivity(self)

    def update_frontend(self, metadata):
        """
        Update incoming metadata changes from the backend.

        Note: Do NOT update states within this function override
            apply_update_frontend instead.
        """
        self.log.info("Update {} with {}".format(self.id(), metadata))
        self._cached_metadata.update(metadata)

        self._in_metadata_update = True
        try:
            self.apply_update_frontend(metadata)
        finally:
            self._in_metadata_update = False

    def apply_update_frontend(self, metadata):
        """
        Apply changes from metadata to this item.
        """
        # apply position
        if 'x' in metadata or 'y' in metadata:
            self.setPos(metadata.get('x', self.x()),
                        metadata.get('y', self.y()))

    def update_backend(self, backend_metadata):
        """
        Notify backend on all changed to the item.

        Use the given backend metadata to look for changes and report
        them via
        """
        # update position
        metadata = {}
        if self.x() != backend_metadata.get('x'):
            metadata['x'] = self.x()
        if self.y() != backend_metadata.get('y'):
            metadata['y'] = self.y()
        self.notify_backend(metadata)

    def set_item_creates_undo_actions(self, value):
        """Set whether item should generate undo actions."""
        self._item_creates_undo_actions = value

    def item_creates_undo_actions(self):
        return self._item_creates_undo_actions

    def _register_undo_action(self, action):
        """
        Register undo action.

        You can register actions at any times. If the item
        is not temporary the action will be forwarded to the scene,
        otherwise it will be discarded.
        """
        if self.scene() is not None and \
                self._item_creates_undo_actions and \
                not self._in_metadata_update and \
                not self.is_temporary():
            self.scene().actions.push(action)

    def _unregister(self):
        """Delete backend instance."""
        if self._registered_scene is not None:
            self.itemChange(InsertableItem.ItemRegistrationChange, False)
            self._registered_scene.interface().delete_element(self.id())
            self._registered_scene = None
            self.itemChange(InsertableItem.ItemRegistrationHasChanged, False)

    def _register(self):
        """Create new backend instance."""
        scene = self.scene()
        if scene is not None and not self.is_temporary():
            self.itemChange(InsertableItem.ItemRegistrationChange, True)
            scene.registry().instantiated_frontend_item(self)
            scene.interface().create_element(
                guid=self.GUID(),
                parent=None,
                additional_metadata=self.metadata())
            self._registered_scene = scene
            self.itemChange(InsertableItem.ItemRegistrationHasChanged, True)

    def is_registered(self):
        return self._registered_scene is not None

    def notify_backend(self, metadata):
        """Notify backend on metadata change."""
        if not metadata:
            return
        if not self.is_registered():
            self._cached_metadata.update(metadata)
        else:
            assert not self.is_inactive(), "notify only allowed while active"
            # notify backend
            self.scene().interface().update_element(self.id(), metadata)

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
        return self._cached_metadata.get('id')

    def name(self):
        """Return name."""
        return self._cached_metadata.get('name', '<name>')

    def __repr__(self):
        return "<{} 0x{:x} at {}>".format(
            type(self).__name__, id(self),
            (self.pos().x(), self.pos().y()))

    def metadata(self):
        """Return the complete metadata."""
        return self._cached_metadata

    def setPos(self, pos, y=None, notify_surrounding=False):
        """
        :param notify_surrounding: If True, surrounding is notified that the
            connectable surrounding has been changed.
        """
        if y is not None:
            pos = QtCore.QPointF(pos, y)

        # change position and notify surrounding
        setPos = super().setPos
        self._pos_change_helper(lambda: setPos(pos), notify_surrounding)

        self._on_item_position_has_changed(self.pos())

    def setX(self, x):
        self.setPos(x, self.y())

    def setY(self, y):
        self.setPos(self.x(), y)

    def moveBy(self, dx, dy):
        self.setPos(self.x() + dx, self.y() + dy)

    def _on_item_position_has_changed(self, new_pos):
        """Notification that position has changed."""
        if new_pos == self._last_position:
            return

        # notify selection change
        if self.isSelected():
            self.scene().selectedItemPosChanged.emit()

        # create undo action
        if self.scene() is not None:
            action = MoveAction(self.scene().getUndoGroupId(),
                                self, self._last_position, new_pos)
            self._register_undo_action(action)

        self._last_position = new_pos

        # notify change
        self.register_change_during_inactivity()

        # update position valid
        self._invalidate_position_is_valid()

    def itemChange(self, change, value):
        if change is QtGui.QGraphicsItem.ItemSceneChange:
            self._additional_notify_items = self.items_at_connections()
        # on scene change
        elif change is QtGui.QGraphicsItem.ItemSceneHasChanged:
            # re-register
            self._unregister()
            self._register()
            # notify surrounding
            self.notify_surrounding(self._additional_notify_items)
            self._additional_notify_items = None
            # update position valid state
            self._invalidate_position_is_valid()
        # Register, unregister and notify surrounding on temporary state change
        elif change is ItemBase.ItemTemporaryHasChanged:
            if value:
                self._unregister()
            else:
                self._register()
                self.notify_surrounding()

        if self.scene() is not None:
            # round position to grid point
            if change == QtGui.QGraphicsItem.ItemPositionChange:
                return self.scene().roundToGrid(value)
            # handle position changes
            elif change == QtGui.QGraphicsItem.ItemPositionHasChanged:
                self._on_item_position_has_changed(value)
            # only selectable when allowed by scene
            elif change == QtGui.QGraphicsItem.ItemSelectedChange:
                return value and self.scene().selectionAllowed()
            # after becoming active update metadata for backend
            elif change == ItemBase.ItemSceneActivatedHasChanged and value:
                self.update_backend(self._cached_metadata)
            # before becoming registered update metadata for backend
            elif change == InsertableItem.ItemRegistrationChange and value:
                self.update_backend(self._cached_metadata)
            # only movable when selected
            elif change == QtGui.QGraphicsItem.ItemSelectedHasChanged:
                self.setFlag(QtGui.QGraphicsItem.ItemIsMovable, value)
            # update surroudning when position valid changed
            elif change == InsertableItem.ItemPositionValidHasChanged:
                self.notify_surrounding()

        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        event.accept()

    def hoverMoveEvent(self, event):
        super().hoverMoveEvent(event)
        self.setCursor(QtCore.Qt.SizeAllCursor if self.isSelected() else
                       QtCore.Qt.ArrowCursor)

    def mouseMoveEvent(self, event):
        """Moves the item and creates surrounding changed notifications"""
        self.setCursor(QtCore.Qt.SizeAllCursor if self.isSelected() else
                       QtCore.Qt.ArrowCursor)

        # move item and notify surrounding
        mouseMoveEvent = super().mouseMoveEvent
        self._pos_change_helper(lambda: mouseMoveEvent(event), True)

    def _pos_change_helper(self, update_pos_function, notify_surrounding):
        """
        Changes position with given function and notifies surrounding.

        :param function: function to do position change
        :param notify_surrounding: If True, surrounding is notified.
        """
        old_pos = self.pos()
        self._change_and_notify_surrounding(
            update_pos_function,
            lambda: self.pos() != old_pos,
            notify_surrounding)

    def _change_and_notify_surrounding(
            self, change_function, condition_function, notify_surrounding):
        """
        Applies changes and notifies the surrounding if condition is True.

        :param change_function: function called to apply changes
        :param condition_function: if condition is fulfilled after
            applying the changes the surrounding is notified
        :param notify_surrounding: if this parameter is False,
            no notifications are made.
        """
        if notify_surrounding:
            # store old surrounding
            assert self.scene() is None or \
                len(self.scene().selectedItems()) <= 1
            chanded_items_set = self.items_at_connections()
        # change position
        change_function()
        # notify items that surrounding has changed
        if notify_surrounding and condition_function():
            self.notify_surrounding(chanded_items_set)

    def notify_surrounding(self, addition_items=None):
        """
        Notify items that connectable surrounding has changed.

        By default only items in the connectable surrounding are notified.

        :param addition_items: further items to notify
        """
        from .connectable_item import ConnectableItem

        chanded_items_set = set()
        if addition_items is not None:
            chanded_items_set.update(addition_items)
        chanded_items_set.update(self.items_at_connections())
        chanded_items_set.add(self)
        for item in chanded_items_set:
            item.itemChange(
                ConnectableItem.ItemConnectableSurroundingHasChanged, True)

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
        QtGui.QGraphicsItem.mouseReleaseEvent(self, event)
