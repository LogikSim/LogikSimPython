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
    _selection_color_fill = QtGui.QColor(80, 151, 222)
    _selection_color_line = QtGui.QColor(40, 125, 210)

    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)

    def _line_to_rect(self, line):
        """ converts QLineF to its collision area """
        radius = 10**-3
        rect = QtCore.QRectF(line.p1(), line.p2()).normalized()
        return rect.normalized().adjusted(-radius, -radius, radius, radius)
