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

    def _line_to_rect(self, line):
        """ converts QLineF to its collision area """
        radius = 10**-3
        rect = QtCore.QRectF(line.p1(), line.p2()).normalized()
        return rect.normalized().adjusted(-radius, -radius, radius, radius)

    def itemChange(self, change, value):
        if change is not ItemBase.ItemSingleSelectionHasChanged:
            # QGraphicsItem only supports changes defined in Qt
            return super().itemChange(change, value)
