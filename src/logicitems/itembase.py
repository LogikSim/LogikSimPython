#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
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

    # collision margin added to all bounding boxes and shapes
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

    def _line_to_rect(self, line, radius=None):
        """
        Converts QLineF to its collision area.

        :param radius: Collision radius of the line, using collision margin
            as default value.
        """
        if radius is None:
            radius = self.collision_margin
        rect = QtCore.QRectF(line.p1(), line.p2()).normalized()
        return rect.normalized().adjusted(-radius, -radius, radius, radius)

    def itemChange(self, change, value):
        if change is not ItemBase.ItemSingleSelectionHasChanged:
            # QGraphicsItem only supports changes defined in Qt
            return super().itemChange(change, value)
