#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
And logic item with variable number of inputs.
'''

from PySide import QtCore

from logicitems import ResizableItem
from backend.simple_element import SimpleElementGuiItem


class AndItem(ResizableItem, SimpleElementGuiItem):
    def __init__(self, parent=None, metadata={}):
        ResizableItem.__init__(self, metadata.get('#inputs', 2), parent=parent)
        SimpleElementGuiItem.__init__(self, metadata)

        self.setPos(metadata.get('x', 0), metadata.get('y', 0))

    def update(self, metadata):
        SimpleElementGuiItem.update(self, metadata)

        x = metadata.get('x')
        if x is not None:
            self.setX(x)

        y = metadata.get('y')
        if y is not None:
            self.setY(y)

    def paint(self, painter, options, widget):
        super().paint(painter, options, widget)

        font = painter.font()
        font.setPointSizeF(self.scene().get_grid_spacing() * 0.8)
        painter.setFont(font)
        painter.drawText(self.boundingRect(), QtCore.Qt.AlignCenter, '&')
