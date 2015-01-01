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

    class ItemSingleSelectionHasChanged:
        """
        QGraphicsItem.itemChange() notification

        The item single selection state changed. It notifies whenever the item
        has become or has stopped being the only selected item in the scene.
        The return value is ignored.
        """
        pass

    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)

        self._is_temp = False  # is temporary

    def set_temporary(self, temp):
        """Set item to temporary status."""
        self._is_temp = temp

    def is_temporary(self):
        """
        Is item temporary.

        Temporary items are not considered in collision detection.
        """
        return self._is_temp

    def _line_to_col_rect(self, line, radius=None):
        """
        Converts QLineF to its collision area.

        :param radius: Collision radius of the line, using collision margin
            as default value.
        """
        return self._to_col_rect(QtCore.QRectF(line.p1(), line.p2()), radius)

    def _to_col_rect(self, rect, radius=None):
        """
        Converts QRectF to its collision area.

        :param radius: Collision radius of the line, using collision margin
            as default value.
        """
        if radius is None:
            radius = self.collision_margin
        return rect.normalized().adjusted(-radius, -radius, radius, radius)

    def itemChange(self, change, value):
        # QGraphicsItem only supports changes defined in Qt
        if isinstance(change, QtGui.QGraphicsItem.GraphicsItemChange):
            return super().itemChange(change, value)
