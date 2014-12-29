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


class TextItem(ResizableItem):
    def paint(self, painter, options, widget):
        super().paint(painter, options, widget)

        label = self.metadata().get("text", "--")
        font = painter.font()
        font.setPointSizeF(self.scene().get_grid_spacing() * 0.8)
        painter.setFont(font)
        painter.drawText(self.boundingRect(), QtCore.Qt.AlignCenter, label)

    @classmethod
    def GUI_GUID(cls):
        return "3BFA39F9-C6A8-46AA-8D03-3B951B4D5FB2"
