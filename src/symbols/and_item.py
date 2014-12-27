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


class AndItem(ResizableItem):
    def __init__(self, input_count=3):
        super().__init__(input_count)

    def paint(self, painter, options, widget):
        super().paint(painter, options, widget)

        font = painter.font()
        font.setPointSizeF(self.scene().get_grid_spacing() * 0.8)
        painter.setFont(font)
        painter.drawText(self.boundingRect(), QtCore.Qt.AlignCenter, '&')
