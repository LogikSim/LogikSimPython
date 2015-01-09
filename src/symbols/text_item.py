#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Resizable item with text label.
'''

from PySide import QtCore

from logicitems import ResizableItem


class TextItem(ResizableItem):
    """
    Resizable item with text label.

    The label can be set via metadata['text'].
    """
    def paint(self, painter, options, widget):
        super().paint(painter, options, widget)

        label = self.metadata().get("text", "--")
        font = painter.font()
        font.setPointSizeF(self.scene().get_grid_spacing() * 0.8)
        painter.setFont(font)
        painter.setPen(QtCore.Qt.black)
        painter.drawText(self.boundingRect(), QtCore.Qt.AlignCenter, label)

    @classmethod
    def GUI_GUID(cls):
        return "3BFA39F9-C6A8-46AA-8D03-3B951B4D5FB2"
