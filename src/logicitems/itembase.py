#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Base class for all graphics items used
'''

from PySide import QtGui, QtCore


class ItemBase(QtGui.QGraphicsItem):
    # selection colors
    _selection_color_fill = QtGui.QColor(80, 151, 222)
    _selection_color_line = QtGui.QColor(40, 125, 210)

    # collision margin added to all bounding boxes and collision shapes
    # (make sure this is fully representable as double, otherwise we get
    # rounding errors, check with (number).hex() how many digits are taken)
    collision_margin = 2 ** -10

    # Standard delay of signals on the grid
    _delay_per_gridpoint = 1

    class ItemSingleSelectionHasChanged:
        """
        ItemBase.itemChange() notification

        The item single selection state changed. It notifies whenever the item
        has become or has stopped being the only selected item in the scene.
        The return value is ignored.
        """

    class ItemSceneActivatedChange:
        """
        ItemBase.itemChange() notification

        The scene is about to become active, but is not yet active.

        See ItemSceneActivatedHasChanged
        """

    class ItemSceneActivatedHasChanged:
        """
        ItemBase.itemChange() notification

        The scene has become active again. The item is only notified
        if it has registered for this event by calling
            self.scene().register_change_during_inactivity(self)
        during the time the scene was inactive. This has to be
        repeated in each inactivity.
        """

    class ItemTemporaryHasChanged:
        """
        ItemBase.itemChange() notification

        The item temporary state has changed.
        """

    def __init__(self, parent=None):
        super().__init__(parent)

        self._is_temp = False  # is temporary

    def set_temporary(self, temp):
        """Set item to temporary status."""
        if temp != self._is_temp:
            self._is_temp = temp
            self.itemChange(ItemBase.ItemTemporaryHasChanged, temp)

    def is_temporary(self):
        """
        Is item temporary.

        Temporary items are not considered in collision detection.
        """
        return self._is_temp

    def is_inactive(self):
        """
        Returns True, if the item is inactive.

        See GridScene.set_active
        """
        return self.scene() is not None and self.scene().is_inactive()

    # TODO: remove underscore of name
    @classmethod
    def _line_to_col_rect(cls, line, radius=None):
        """
        Converts QLineF to its collision area.

        :param radius: Collision radius of the line, using collision margin
            as default value.
        """
        return cls._to_col_rect(QtCore.QRectF(line.p1(), line.p2()), radius)

    # TODO: remove underscore of name
    @classmethod
    def _to_col_rect(cls, rect, radius=None):
        """
        Converts QRectF to its collision area.

        :param radius: Collision radius of the line, using collision margin
            as default value.
        """
        if radius is None:
            radius = cls.collision_margin
        return rect.normalized().adjusted(-radius, -radius, radius, radius)

    def itemChange(self, change, value):
        # QGraphicsItem only supports changes defined in Qt
        if isinstance(change, QtGui.QGraphicsItem.GraphicsItemChange):
            return super().itemChange(change, value)
